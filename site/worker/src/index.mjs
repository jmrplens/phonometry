// The phonometry.dev Worker: it runs only for the beacon and the files agents
// read (assets.run_worker_first in wrangler.jsonc, from lib/agent-paths.mjs),
// and writes one Analytics Engine data point for each. Pages, _astro, media
// and every other file are served by Static Assets without running this.
//
// An agent file is answered by the assets binding, which applies _redirects,
// _headers, html_handling and the 404 page exactly as an asset request gets
// them, and its response goes out as the binding returned it. Logging never
// stands between a client and a file: the write is fire-and-forget and a
// failure is swallowed (lib/edge-log.mjs). The beacon answers at once and
// writes its point in waitUntil.
import { BASE_PATH, BEACON_PATH, agentPaths, runsWorker } from '../lib/agent-paths.mjs';
import { BEACON_MAX_BYTES, beaconPoint, ipLimitKey, parseBeacon } from '../lib/beacon.mjs';
import { logEdgeRequest } from '../lib/edge-log.mjs';

const NO_STORE = { 'cache-control': 'no-store' };
/** The paths this Worker runs for (wrangler.jsonc's run_worker_first). */
const WORKER_PATHS = agentPaths(BASE_PATH);
const reply = (status, headers = {}) => new Response(null, { status, headers: { ...NO_STORE, ...headers } });

/**
 * The body, read up to `max` bytes. Null when it is longer: a body with no
 * Content-Length is not read whole to be thrown away.
 *
 * @param {Request} request The request.
 * @param {number} max The limit in bytes.
 * @returns {Promise<string | null>} The text, or null.
 */
async function readCapped(request, max) {
	if (!request.body) return '';
	const reader = request.body.getReader();
	const parts = [];
	let size = 0;
	for (;;) {
		const { done, value } = await reader.read();
		if (done) break;
		size += value.byteLength;
		if (size > max) {
			await reader.cancel();
			return null;
		}
		parts.push(value);
	}
	const all = new Uint8Array(size);
	let at = 0;
	for (const part of parts) {
		all.set(part, at);
		at += part.byteLength;
	}
	return new TextDecoder().decode(all);
}

/** Whether the per-address limit is spent. A limiter that is absent or fails counts as not spent. */
async function overLimit(env, ip) {
	if (!env.PER_IP) return false;
	try {
		return !(await env.PER_IP.limit({ key: ipLimitKey(ip) })).success;
	} catch {
		return false;
	}
}

/**
 * The beacon. 204 for a page view (also over the per-address limit, so a
 * shared connection sees no error and a flood learns nothing); 405, 403, 413
 * or 400 for what is not one. Every outcome writes exactly one data point, so
 * Analytics Engine writes never outnumber Worker invocations and its daily
 * allowance cannot run out before the Workers quota does.
 *
 * Origin and Sec-Fetch-Site are a filter, not a defence: curl can send both.
 * What keeps a flood from spending the quota are the zone's WAF and rate
 * rules (lib/rules.mjs), which run before any Worker.
 */
async function handleBeacon(request, env, ctx, url, startedAt) {
	const rejected = (status, reason, headers) => {
		logEdgeRequest({ env, request, url, startedAt, status, cacheStatus: `beacon-rejected-${reason}`, response: null });
		return reply(status, headers);
	};
	if (request.method !== 'POST') return rejected(405, 'method', { allow: 'POST' });
	const site = request.headers.get('sec-fetch-site');
	if (request.headers.get('origin') !== url.origin || (site !== null && site !== 'same-origin')) return rejected(403, 'origin');
	if (Number(request.headers.get('content-length') ?? 0) > BEACON_MAX_BYTES) return rejected(413, 'size');
	const body = await readCapped(request, BEACON_MAX_BYTES);
	if (body === null) return rejected(413, 'size');
	const beacon = parseBeacon(body);
	if (beacon === null) return rejected(400, 'body');
	// The 404 page at an agent path: that request ran this Worker and was
	// logged with its 404 already. The staged 404 page sends nothing there;
	// this keeps a page staged before it did from counting the miss twice.
	if (beacon.notFound === 1 && runsWorker(beacon.path, WORKER_PATHS)) return rejected(400, 'agent-404');
	ctx.waitUntil(
		(async () => {
			const limited = await overLimit(env, request.headers.get('cf-connecting-ip'));
			const point = beaconPoint({ request, beacon, host: url.hostname, startedAt, verdict: limited ? 'beacon-limited' : 'beacon' });
			if (point !== null) env.REQS?.writeDataPoint(point);
		})().catch(() => {
			// Analytics must never break serving.
		}),
	);
	return reply(204);
}

/** The statuses `_redirects` answers with. */
const REDIRECTS = new Set([301, 302, 303, 307, 308]);

/**
 * Blob 12 of an agent file: `redirect` for a `_redirects` answer,
 * `not-modified` for a conditional request answered 304, `asset` otherwise.
 *
 * @param {number} status The status the assets binding answered.
 * @returns {string} The verdict.
 */
export function assetVerdict(status) {
	if (REDIRECTS.has(status)) return 'redirect';
	return status === 304 ? 'not-modified' : 'asset';
}

/**
 * The bytes of a body, read to its end (what was read when it fails).
 *
 * @param {ReadableStream | null} body The body.
 * @returns {Promise<number>} The count.
 */
async function byteLength(body) {
	if (!body) return 0;
	let size = 0;
	const reader = body.getReader();
	try {
		for (;;) {
			const { done, value } = await reader.read();
			if (done) return size;
			size += value.byteLength;
		}
	} catch {
		return size;
	}
}

export default {
	async fetch(request, env, ctx) {
		const startedAt = Date.now();
		const url = new URL(request.url);
		if (url.pathname === BEACON_PATH) return handleBeacon(request, env, ctx, url, startedAt);
		const response = await env.ASSETS.fetch(request);
		const facts = { request, url, startedAt, status: response.status, cacheStatus: assetVerdict(response.status) };
		// The assets binding sends no Content-Length header (the client gets
		// one from the runtime), and double 5 is the response's length, as
		// docs-edge stores it. So when the header is absent the bytes are
		// counted from a clone, after the response has gone out: a HEAD and a
		// 304 have no body and count 0.
		if (response.headers.has('content-length') || !env.REQS) {
			logEdgeRequest({ ...facts, env, response });
			return response;
		}
		// Double 7 stays the time to the answer, not to the end of the count.
		const answeredIn = Date.now() - startedAt;
		const copy = response.clone();
		ctx.waitUntil(
			byteLength(copy.body).then((size) => {
				const headers = new Headers(response.headers);
				headers.set('content-length', String(size));
				const point = { REQS: { writeDataPoint: (p) => env.REQS.writeDataPoint({ ...p, doubles: p.doubles.with(6, answeredIn) }) } };
				logEdgeRequest({ ...facts, env: point, response: { headers } });
			}),
		);
		return response;
	},
};
