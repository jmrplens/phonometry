// The Worker's fetch handler with fake bindings: the beacon's answers and the
// one data point each writes. Nothing else runs it (lib/worker-paths.mjs).
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import worker from '../src/index.mjs';

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

const VIEW = JSON.stringify({ p: '/signals/', q: '', r: 'https://www.google.com/', n: 'navigate', t: 300, w: 1920, h: 1080, vw: 1280, vh: 720, dpr: 1, lg: 'en', tz: 'UTC', wd: 0, nf: 0 });

describe('the beacon', () => {
	test('a page view: 204 at once, one data point after, marked beacon', async () => {
		const b = bindings();
		const response = await worker.fetch(beacon(VIEW), b.env, b.ctx);
		assert.equal(response.status, 204);
		assert.equal(response.headers.get('cache-control'), 'no-store');
		await b.settle();
		assert.equal(b.points.length, 1);
		assert.equal(b.points[0].blobs[0], '/signals/');
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

	test('the 404 page is a page view with status 404', async () => {
		const b = bindings();
		const body = JSON.stringify({ ...JSON.parse(VIEW), p: '/no-such-page/', nf: 1 });
		assert.equal((await worker.fetch(beacon(body), b.env, b.ctx)).status, 204);
		await b.settle();
		assert.equal(b.points[0].blobs[0], '/no-such-page/');
		assert.equal(b.points[0].blobs[10], '404');
		assert.equal(b.points[0].blobs[11], 'beacon');
	});

	test('the 404 page at a missing copy is a page view too: no Worker logged that miss', async () => {
		const b = bindings();
		const body = JSON.stringify({ ...JSON.parse(VIEW), p: '/no-such-page/index.md', nf: 1 });
		assert.equal((await worker.fetch(beacon(body), b.env, b.ctx)).status, 204);
		await b.settle();
		assert.equal(b.points.length, 1);
		assert.equal(b.points[0].blobs[0], '/no-such-page/index.md');
		assert.equal(b.points[0].blobs[10], '404');
		assert.equal(b.points[0].blobs[11], 'beacon');
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

describe('any other request', () => {
	test('reaching the Worker by mistake, it gets the file as the assets answer it, and nothing is logged', async () => {
		const b = bindings();
		const request = new Request(`${ORIGIN}/signals/index.md`, { headers: { 'user-agent': 'GPTBot/1.2' } });
		const response = await worker.fetch(request, b.env, b.ctx);
		assert.equal(response.status, 200);
		assert.equal(await response.text(), '# copy');
		assert.equal(b.fetched.length, 1);
		assert.equal(b.fetched[0], request);
		await b.settle();
		assert.equal(b.points.length, 0);
	});
});
