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
import { BEACON_PATH } from '../lib/agent-paths.mjs';
import { BEACON_MAX_BYTES, beaconPoint, ipLimitKey, parseBeacon } from '../lib/beacon.mjs';
import { logEdgeRequest } from '../lib/edge-log.mjs';

const NO_STORE = { 'cache-control': 'no-store' };
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

export default {
	async fetch(request, env, ctx) {
		const startedAt = Date.now();
		const url = new URL(request.url);
		if (url.pathname === BEACON_PATH) return handleBeacon(request, env, ctx, url, startedAt);
		const response = await env.ASSETS.fetch(request);
		const verdict = response.status >= 300 && response.status < 400 ? 'redirect' : 'asset';
		logEdgeRequest({ env, request, url, startedAt, status: response.status, cacheStatus: verdict, response });
		return response;
	},
};
