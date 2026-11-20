// The `_headers` file of the preview: order, detaches, the homes and the
// Spanish API pages, the canonical of each Markdown copy, and the limits.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { HEADER_RULE_LIMIT, HEADER_LINE_LIMIT, headersFile, parseHeaders, SECURITY_HEADERS } from '../lib/headers.mjs';
import { clipBase, mediaOrigins } from '../../src/data/site.mjs';
import { twinExclusions } from '../lib/twins.mjs';

const prefix = '';
const options = {
	prefix,
	origin: 'https://phonometry.dev',
	exclusions: twinExclusions(prefix),
	indexable: false,
};

/** The headers a request path gets, applying the rules as Static Assets documents them. */
function headersFor(text, path) {
	const out = new Map();
	for (const { pattern, lines } of parseHeaders(text)) {
		const splat = matchPattern(pattern, path);
		if (splat === null) continue;
		for (const line of lines) {
			if (line.startsWith('! ')) {
				out.delete(line.slice(2).toLowerCase());
				continue;
			}
			const at = line.indexOf(':');
			const name = line.slice(0, at).toLowerCase();
			const value = line.slice(at + 1).trim().replaceAll(':splat', splat);
			out.set(name, out.has(name) ? `${out.get(name)}, ${value}` : value);
		}
	}
	return out;
}

/** The splat a pattern captures from a path, '' when it has none, or null when it does not match. */
function matchPattern(pattern, path) {
	const star = pattern.indexOf('*');
	if (star < 0) return pattern === path ? '' : null;
	const head = pattern.slice(0, star);
	const tail = pattern.slice(star + 1);
	if (!path.startsWith(head) || !path.endsWith(tail)) return null;
	if (path.length < head.length + tail.length) return null;
	return path.slice(head.length, path.length - tail.length);
}

describe('headersFile', () => {
	const text = headersFile(options);

	test('every response carries the security set and the noindex of a preview', () => {
		const got = headersFor(text, '/_astro/x.css');
		for (const [name, value] of SECURITY_HEADERS) assert.equal(got.get(name.toLowerCase()), value, name);
		assert.equal(got.get('x-robots-tag'), 'noindex');
	});

	test('the security set is docs.jmrp.io rule 1 plus nosniff', () => {
		const names = SECURITY_HEADERS.map(([name]) => name);
		assert.deepEqual(names, [
			'Access-Control-Allow-Origin',
			'Content-Security-Policy',
			'Permissions-Policy',
			'Referrer-Policy',
			'X-Frame-Options',
			'X-Content-Type-Options',
		]);
	});

	test('a page with a copy names it and varies on Accept', () => {
		const got = headersFor(text, '/signals/levels/levels/');
		assert.equal(got.get('link'), '</signals/levels/levels/index.md>; rel="alternate"; type="text/markdown"');
		assert.equal(got.get('vary'), 'Accept, Accept-Encoding');
	});

	test('the copy names its page as canonical, on the build origin', () => {
		const got = headersFor(text, '/signals/levels/levels/index.md');
		assert.equal(got.get('link'), '<https://phonometry.dev/signals/levels/levels/>; rel="canonical"');
		assert.equal(got.has('vary'), false);
	});

	test('the two homes name their copy too', () => {
		assert.equal(headersFor(text, '/').get('link'), '</index.md>; rel="alternate"; type="text/markdown"');
		assert.equal(headersFor(text, '/').get('vary'), 'Accept, Accept-Encoding');
		assert.equal(headersFor(text, '/es/').get('link'), '</es/index.md>; rel="alternate"; type="text/markdown"');
	});

	test('the Spanish API pages announce no copy', () => {
		for (const path of ['/es/reference/api/', '/es/reference/api/signals/levels/']) {
			const got = headersFor(text, path);
			assert.equal(got.has('link'), false, path);
			assert.equal(got.has('vary'), false, path);
			assert.equal(got.get('x-robots-tag'), 'noindex', path);
		}
	});

	test('the English API pages keep their copy', () => {
		assert.ok(headersFor(text, '/reference/api/signals/levels/').has('link'));
	});

	test('a detach comes after the rule that set the header (it removes only what came before)', () => {
		const rules = parseHeaders(text);
		const setAt = rules.findIndex(({ lines }) => lines.some((line) => line.startsWith('Link: <')));
		const detachAt = rules.findIndex(({ lines }) => lines.includes('! Link'));
		assert.ok(setAt >= 0 && detachAt > setAt, `set at ${setAt}, detached at ${detachAt}`);
	});

	test('the copies of the homes name the homes as canonical', () => {
		assert.equal(headersFor(text, '/index.md').get('link'), '<https://phonometry.dev/>; rel="canonical"');
		assert.equal(headersFor(text, '/es/index.md').get('link'), '<https://phonometry.dev/es/>; rel="canonical"');
	});

	test('no rule touches the cache lifetime: a pattern would match a 404 too', () => {
		assert.equal(headersFor(text, '/_astro/x.css').has('cache-control'), false);
		assert.equal(headersFor(text, '/signals/').has('cache-control'), false);
		assert.ok(!text.includes('Cache-Control'));
	});

	test('Markdown and text files say they are UTF-8, and only one Content-Type is left', () => {
		for (const path of ['/signals/index.md', '/index.md', '/es/reference/api/x/index.md']) {
			assert.equal(headersFor(text, path).get('content-type'), 'text/markdown; charset=utf-8', path);
		}
		for (const path of ['/llms.txt', '/llms-full.txt', '/llms/signals.txt', '/llms.txt', '/robots.txt']) {
			assert.equal(headersFor(text, path).get('content-type'), 'text/plain; charset=utf-8', path);
		}
		assert.equal(headersFor(text, '/signals/').has('content-type'), false);
		for (const { pattern, lines } of parseHeaders(text).filter(({ lines }) => lines.some((line) => line.startsWith('Content-Type:')))) {
			assert.equal(lines.indexOf('! Content-Type'), lines.findIndex((line) => line.startsWith('Content-Type:')) - 1, pattern);
		}
	});

	test('the clip hosts are allowed as media sources, the rest of docs.jmrp.io rule 1 is unchanged', () => {
		const csp = SECURITY_HEADERS.find(([name]) => name === 'Content-Security-Policy')[1];
		const media = csp.split('; ').find((part) => part.startsWith('media-src '));
		assert.deepEqual(media.split(' ').slice(1), ["'self'", ...mediaOrigins]);
		assert.ok(mediaOrigins.includes(new URL(clipBase).origin));
		const rest = csp.split('; ').filter((part) => !part.startsWith('media-src ')).join('; ');
		assert.equal(
			rest,
			"default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://img.shields.io https://cursor.com https://kiro.dev https://files.lmstudio.ai; font-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; report-uri https://jmrp.io/csp-report",
		);
	});

	test('indexable drops the noindex, except on the llms files', () => {
		const open = headersFile({ ...options, indexable: true });
		assert.equal(headersFor(open, '/signals/').has('x-robots-tag'), false);
		assert.equal(headersFor(open, '/llms.txt').get('x-robots-tag'), 'noindex');
		assert.equal(headersFor(open, '/llms/signals.txt').get('x-robots-tag'), 'noindex');
		// The staging step copies llms.txt to the host root as well.
		assert.equal(headersFor(open, '/llms.txt').get('x-robots-tag'), 'noindex');
		assert.equal(headersFor(open, '/robots.txt').has('x-robots-tag'), false);
		const root = headersFile({ ...options, prefix: '', origin: 'https://phonometry.dev', exclusions: twinExclusions(''), indexable: true });
		assert.equal(headersFor(root, '/llms.txt').get('x-robots-tag'), 'noindex');
		assert.equal(parseHeaders(root).filter(({ pattern }) => pattern === '/llms*').length, 1);
	});

	test('at the root the patterns lose the prefix', () => {
		const root = headersFile({ ...options, prefix: '', origin: 'https://phonometry.dev', exclusions: twinExclusions('') });
		assert.equal(headersFor(root, '/signals/').get('link'), '</signals/index.md>; rel="alternate"; type="text/markdown"');
		assert.equal(headersFor(root, '/signals/index.md').get('link'), '<https://phonometry.dev/signals/>; rel="canonical"');
		assert.equal(headersFor(root, '/').get('link'), '</index.md>; rel="alternate"; type="text/markdown"');
		assert.equal(headersFor(root, '/index.md').get('link'), '<https://phonometry.dev/>; rel="canonical"');
		assert.equal(headersFor(root, '/es/reference/api/x/').has('link'), false);
	});

	test('the file fits the documented limits', () => {
		const rules = parseHeaders(text);
		assert.ok(rules.length <= HEADER_RULE_LIMIT, `${rules.length} rules`);
		for (const line of text.split('\n')) assert.ok(line.length <= HEADER_LINE_LIMIT, line.slice(0, 40));
		assert.equal(HEADER_RULE_LIMIT, 100);
		assert.equal(HEADER_LINE_LIMIT, 2000);
	});

	test('a prefix with a trailing slash or no leading slash is refused', () => {
		assert.throws(() => headersFile({ ...options, prefix: '/docs/' }), /prefix/);
		assert.throws(() => headersFile({ ...options, prefix: 'phonometry' }), /prefix/);
		assert.throws(() => headersFile({ ...options, origin: 'https://phonometry.dev/' }), /origin/);
	});
});
