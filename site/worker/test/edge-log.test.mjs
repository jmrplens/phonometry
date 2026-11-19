// The data point the Worker writes is docs-edge's, field for field.
//
// lib/edge-log.mjs carries docs-edge's logging block verbatim (NAMED_AGENTS
// through logEdgeRequest), so the local pipeline (ae-to-influx.mjs in the
// jmrp.io repository) reads phonometry.dev rows with the same column layout as
// docs.jmrp.io's. When that repository is on this machine the block is
// compared with its source text; the layout tests below run everywhere.
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { test } from 'node:test';

import { logEdgeRequest, requestClass } from '../lib/edge-log.mjs';

const DOCS_EDGE = '/var/www/jmrp.io/workers/docs-edge/worker.js';
const OURS = new URL('../lib/edge-log.mjs', import.meta.url);

/** The text from `const NAMED_AGENTS` to the closing brace of logEdgeRequest. */
function loggingBlock(source) {
	const start = source.indexOf('const NAMED_AGENTS = [');
	const head = source.indexOf('function logEdgeRequest(');
	assert.ok(start >= 0 && head > start, 'no logging block');
	const end = source.indexOf('\n}\n', head);
	assert.ok(end > head, 'logEdgeRequest has no end');
	return source.slice(start, end + 2).replaceAll(/^export /gm, '');
}

test('the block is docs-edge’s, verbatim', { skip: !existsSync(DOCS_EDGE) && 'the jmrp.io repository is not on this machine' }, () => {
	assert.equal(loggingBlock(readFileSync(OURS, 'utf8')), loggingBlock(readFileSync(DOCS_EDGE, 'utf8')));
});

/** A request as workerd hands it over, with request.cf. */
function fakeRequest(headers = {}, cf = {}) {
	return { method: 'GET', headers: new Headers(headers), cf };
}

test('20 blobs and 9 doubles in docs-edge’s order', () => {
	let point = null;
	const env = { REQS: { writeDataPoint: (p) => (point = p) } };
	const request = fakeRequest(
		{
			'user-agent': 'Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)',
			accept: 'text/markdown',
			'cf-connecting-ip': '2001:db8::1',
			referer: 'https://example.org/x',
			'accept-language': 'en',
			'cf-ray': 'abc123',
		},
		{ country: 'US', colo: 'IAD', city: 'Ashburn', asOrganization: 'Anthropic', httpProtocol: 'HTTP/2', tlsVersion: 'TLSv1.3', latitude: '39.0', longitude: '-77.4', asn: 399358, clientTcpRtt: 12 },
	);
	const url = new URL('https://phonometry.dev/phonometry/signals/index.md?x=1');
	const response = new Response('x', { headers: { 'content-type': 'text/markdown; charset=utf-8', 'content-length': '1' } });
	logEdgeRequest({ env, request, url, startedAt: 1700000000000, status: 200, cacheStatus: 'asset', response });
	assert.deepEqual(point.indexes, ['md-twin']);
	assert.equal(point.blobs.length, 20);
	assert.equal(point.doubles.length, 9);
	assert.deepEqual(point.blobs.slice(0, 19), [
		'/phonometry/signals/index.md',
		'bot',
		'US',
		'ClaudeBot',
		'example.org',
		'IAD',
		'Ashburn',
		'Anthropic',
		'HTTP/2',
		'TLSv1.3',
		'200',
		'asset',
		'text/markdown',
		'GET',
		'Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)',
		'2001:db8::1',
		'en',
		'https://example.org/x',
		'x=1',
	]);
	assert.equal(point.blobs[19].split('|').length, 14);
	assert.deepEqual(point.doubles.slice(0, 6), [39, -77.4, 399358, 12, 1, 0]);
	assert.equal(point.doubles[8], 1700000000000);
});

test('a failing write never throws into serving', () => {
	const env = { REQS: { writeDataPoint: () => { throw new Error('quota'); } } };
	assert.doesNotThrow(() => logEdgeRequest({ env, request: fakeRequest(), url: new URL('https://phonometry.dev/robots.txt'), startedAt: 0, status: 200, cacheStatus: 'asset', response: null }));
});

test('the request class strips the base path, as on docs.jmrp.io', () => {
	assert.equal(requestClass('/phonometry/llms.txt'), 'llms-txt');
	assert.equal(requestClass('/phonometry/sitemap-index.xml'), 'feed-xml');
	assert.equal(requestClass('/phonometry/signals/'), 'page');
	assert.equal(requestClass('/robots.txt'), 'other');
	assert.equal(requestClass('/llms.txt'), 'llms-txt');
});

test('at the root of phonometry.dev every path the Worker runs for keeps its class', () => {
	assert.equal(requestClass('/index.md'), 'md-twin');
	assert.equal(requestClass('/signals/index.md'), 'md-twin');
	assert.equal(requestClass('/es/signals/levels/levels/index.md'), 'md-twin');
	assert.equal(requestClass('/llms-full.txt'), 'llms-txt');
	assert.equal(requestClass('/llms/llms-signals.txt'), 'llms-txt');
	assert.equal(requestClass('/sitemap-index.xml'), 'feed-xml');
	assert.equal(requestClass('/sitemap-0.xml'), 'feed-xml');
	assert.equal(requestClass('/signals/levels/'), 'page');
	assert.equal(requestClass('/_v'), 'page');
});
