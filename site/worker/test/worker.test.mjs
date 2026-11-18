// The Worker's fetch handler with fake bindings: the beacon's answers, the
// one data point per request, and the agent files passed through untouched.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import worker, { assetVerdict } from '../src/index.mjs';

const ORIGIN = 'https://phonometry.dev';
const PAGE_UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36';

/** Fake bindings that record what the Worker does with them. */
function bindings({ limited = false, limiterThrows = false, assets = () => new Response('# copy', { headers: { 'content-type': 'text/markdown; charset=utf-8' } }) } = {}) {
	const points = [];
	const fetched = [];
	const keys = [];
	const env = {
		REQS: { writeDataPoint: (point) => points.push(point) },
		PER_IP: {
			limit: async ({ key }) => {
				keys.push(key);
				if (limiterThrows) throw new Error('limiter down');
				return { success: !limited };
			},
		},
		ASSETS: { fetch: async (request) => (fetched.push(request), assets(request)) },
	};
	const waits = [];
	const ctx = { waitUntil: (promise) => waits.push(promise), passThroughOnException() {} };
	return { env, ctx, points, fetched, keys, settle: () => Promise.all(waits) };
}

/** A beacon request as a page sends it. */
function beacon(body, { method = 'POST', origin = ORIGIN, site = 'same-origin', length } = {}) {
	const headers = { 'user-agent': PAGE_UA, 'cf-connecting-ip': '203.0.113.7', 'content-type': 'text/plain;charset=UTF-8' };
	if (origin !== null) headers.origin = origin;
	if (site !== null) headers['sec-fetch-site'] = site;
	if (length !== undefined) headers['content-length'] = String(length);
	return new Request(`${ORIGIN}/_v`, { method, headers, body: method === 'POST' ? body : undefined });
}

const VIEW = JSON.stringify({ p: '/phonometry/signals/', q: '', r: 'https://www.google.com/', n: 'navigate', t: 300, w: 1920, h: 1080, vw: 1280, vh: 720, dpr: 1, lg: 'en', tz: 'UTC', wd: 0, nf: 0 });

describe('the beacon', () => {
	test('a page view: 204 at once, one data point after, marked beacon', async () => {
		const b = bindings();
		const response = await worker.fetch(beacon(VIEW), b.env, b.ctx);
		assert.equal(response.status, 204);
		assert.equal(response.headers.get('cache-control'), 'no-store');
		await b.settle();
		assert.equal(b.points.length, 1);
		assert.equal(b.points[0].blobs[0], '/phonometry/signals/');
		assert.equal(b.points[0].blobs[11], 'beacon');
		assert.equal(b.points[0].doubles.length, 15);
		assert.deepEqual(b.keys, ['203.0.113.7']);
		assert.equal(b.fetched.length, 0, 'the beacon never reads an asset');
	});

	test('over the per-address limit: still 204, the point says beacon-limited', async () => {
		const b = bindings({ limited: true });
		assert.equal((await worker.fetch(beacon(VIEW), b.env, b.ctx)).status, 204);
		await b.settle();
		assert.equal(b.points[0].blobs[11], 'beacon-limited');
	});

	test('a limiter that fails counts as not over the limit', async () => {
		const b = bindings({ limiterThrows: true });
		assert.equal((await worker.fetch(beacon(VIEW), b.env, b.ctx)).status, 204);
		await b.settle();
		assert.equal(b.points[0].blobs[11], 'beacon');
	});

	const rejected = [
		['a GET', () => beacon(null, { method: 'GET' }), 405, 'method'],
		['another origin', () => beacon(VIEW, { origin: 'https://evil.example' }), 403, 'origin'],
		['no origin', () => beacon(VIEW, { origin: null }), 403, 'origin'],
		['a cross-site fetch', () => beacon(VIEW, { site: 'cross-site' }), 403, 'origin'],
		['a declared length over 2 KB', () => beacon(VIEW, { length: 4096 }), 413, 'size'],
		['a body over 2 KB', () => beacon(JSON.stringify({ p: '/x/', pad: 'x'.repeat(3000) })), 413, 'size'],
		['a body that is not a beacon', () => beacon('{"x":1}'), 400, 'body'],
	];
	for (const [what, make, status, reason] of rejected) {
		test(`${what}: ${status}, one point beacon-rejected-${reason}`, async () => {
			const b = bindings();
			const response = await worker.fetch(make(), b.env, b.ctx);
			assert.equal(response.status, status);
			assert.equal(response.headers.get('cache-control'), 'no-store');
			if (status === 405) assert.equal(response.headers.get('allow'), 'POST');
			await b.settle();
			assert.equal(b.points.length, 1);
			assert.equal(b.points[0].blobs[0], '/_v');
			assert.equal(b.points[0].blobs[10], String(status));
			assert.equal(b.points[0].blobs[11], `beacon-rejected-${reason}`);
			assert.equal(b.keys.length, 0, 'a refused beacon does not spend the limiter');
		});
	}

	test('the 404 page at an agent path: refused, the Worker logged that miss already', async () => {
		const b = bindings();
		const body = JSON.stringify({ ...JSON.parse(VIEW), p: '/phonometry/no-such-page/index.md', nf: 1 });
		const response = await worker.fetch(beacon(body), b.env, b.ctx);
		assert.equal(response.status, 400);
		await b.settle();
		assert.equal(b.points.length, 1);
		assert.equal(b.points[0].blobs[0], '/_v');
		assert.equal(b.points[0].blobs[11], 'beacon-rejected-agent-404');
	});

	test('the 404 page anywhere else is a page view with status 404', async () => {
		const b = bindings();
		const body = JSON.stringify({ ...JSON.parse(VIEW), p: '/phonometry/no-such-page/', nf: 1 });
		assert.equal((await worker.fetch(beacon(body), b.env, b.ctx)).status, 204);
		await b.settle();
		assert.equal(b.points[0].blobs[0], '/phonometry/no-such-page/');
		assert.equal(b.points[0].blobs[10], '404');
		assert.equal(b.points[0].blobs[11], 'beacon');
	});

	test('an agent-file path from an ordinary page is not refused (only the 404 page skips)', async () => {
		const b = bindings();
		const body = JSON.stringify({ ...JSON.parse(VIEW), p: '/phonometry/signals/index.md', nf: 0 });
		assert.equal((await worker.fetch(beacon(body), b.env, b.ctx)).status, 204);
	});

	test('a Sec-Fetch-Site the browser leaves out is accepted (older browsers)', async () => {
		const b = bindings();
		assert.equal((await worker.fetch(beacon(VIEW, { site: null }), b.env, b.ctx)).status, 204);
	});

	test('no dataset bound: the beacon still answers 204', async () => {
		const b = bindings();
		delete b.env.REQS;
		assert.equal((await worker.fetch(beacon(VIEW), b.env, b.ctx)).status, 204);
		await b.settle();
	});
});

describe('an agent file', () => {
	test('the binding answers, the response goes out as it came, one point', async () => {
		const sent = new Response('# signals', { status: 200, headers: { 'content-type': 'text/markdown; charset=utf-8', link: '<https://docs.jmrp.io/phonometry/signals/>; rel="canonical"' } });
		const b = bindings({ assets: () => sent });
		const request = new Request(`${ORIGIN}/phonometry/signals/index.md`, { headers: { 'user-agent': 'GPTBot/1.2', accept: 'text/markdown' } });
		const response = await worker.fetch(request, b.env, b.ctx);
		assert.equal(response, sent, 'the very object the binding returned');
		assert.equal(b.fetched[0], request, 'the very request the client sent');
		await b.settle();
		assert.equal(b.points.length, 1);
		assert.deepEqual(b.points[0].indexes, ['md-twin']);
		assert.equal(b.points[0].blobs[3], 'GPTBot');
		assert.equal(b.points[0].blobs[10], '200');
		assert.equal(b.points[0].blobs[11], 'asset');
		assert.equal(b.points[0].blobs[12], 'text/markdown');
		assert.equal(b.points[0].doubles.length, 9);
	});

	test('the binding sends no Content-Length: the bytes are counted after the answer, the response untouched', async () => {
		const text = '# signals\n\nAcoustic signals, \u00e9t\u00e9.\n'.repeat(500);
		const sent = new Response(text, { status: 200, headers: { 'content-type': 'text/markdown; charset=utf-8' } });
		const b = bindings({ assets: () => sent });
		const response = await worker.fetch(new Request(`${ORIGIN}/phonometry/signals/index.md`, { headers: { 'user-agent': 'ClaudeBot/1.0' } }), b.env, b.ctx);
		assert.equal(response, sent, 'the very object the binding returned');
		assert.equal(response.headers.get('content-length'), null, 'no header is added to what the client gets');
		assert.equal(await response.text(), text, 'the client reads the whole body');
		await b.settle();
		assert.equal(b.points.length, 1);
		assert.equal(b.points[0].doubles[4], Buffer.byteLength(text));
		assert.equal(b.points[0].blobs[10], '200');
	});

	test('a HEAD and a 304 count 0 bytes; the 304 is logged as not-modified, not as a redirect', async () => {
		for (const [method, status] of [['HEAD', 200], ['GET', 304]]) {
			const b = bindings({ assets: () => new Response(null, { status, headers: { etag: '"x"' } }) });
			const response = await worker.fetch(new Request(`${ORIGIN}/robots.txt`, { method, headers: { 'if-none-match': '"x"' } }), b.env, b.ctx);
			assert.equal(response.status, status);
			await b.settle();
			assert.equal(b.points.length, 1, `${method} ${status}`);
			assert.equal(b.points[0].doubles[4], 0);
			assert.equal(b.points[0].blobs[11], status === 304 ? 'not-modified' : 'asset');
		}
	});

	test('the verdict of each status the binding answers', () => {
		for (const status of [301, 302, 303, 307, 308]) assert.equal(assetVerdict(status), 'redirect', String(status));
		assert.equal(assetVerdict(304), 'not-modified');
		for (const status of [200, 206, 404, 300, 305]) assert.equal(assetVerdict(status), 'asset', String(status));
	});

	test('a retired copy: the 301 of _redirects, logged as redirect', async () => {
		const b = bindings({ assets: () => new Response(null, { status: 301, headers: { location: '/phonometry/start/about/index.md' } }) });
		const response = await worker.fetch(new Request(`${ORIGIN}/phonometry/about/index.md`), b.env, b.ctx);
		assert.equal(response.status, 301);
		await b.settle();
		assert.equal(b.points[0].blobs[10], '301');
		assert.equal(b.points[0].blobs[11], 'redirect');
	});

	test('a missing copy: the 404 page, logged with its status', async () => {
		const b = bindings({ assets: () => new Response('not found', { status: 404 }) });
		assert.equal((await worker.fetch(new Request(`${ORIGIN}/phonometry/nope/index.md`), b.env, b.ctx)).status, 404);
		await b.settle();
		assert.equal(b.points[0].blobs[10], '404');
		assert.equal(b.points[0].blobs[11], 'asset');
	});

	test('a dataset that throws never costs the file', async () => {
		const b = bindings();
		b.env.REQS.writeDataPoint = () => {
			throw new Error('write failed');
		};
		assert.equal((await worker.fetch(new Request(`${ORIGIN}/robots.txt`), b.env, b.ctx)).status, 200);
	});
});
