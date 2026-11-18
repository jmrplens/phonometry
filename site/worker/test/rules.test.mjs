// The zone rulesets of the preview: their exact expressions and targets.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { IMMUTABLE, redirectRules, responseHeaderRules, wildcardMatch } from '../lib/rules.mjs';
import { twinExclusions } from '../lib/twins.mjs';

const prefix = '/phonometry';
const options = {
	host: 'phonometry.dev',
	prefix,
	exclusions: twinExclusions(prefix),
	clipBase: 'https://docs.jmrp.io/phonometry/media/',
};

describe('redirectRules', () => {
	const rules = redirectRules(options);
	const byRef = Object.fromEntries(rules.map((rule) => [rule.ref, rule]));

	test('four rules in order, within the ten a Free zone takes', () => {
		assert.deepEqual(
			rules.map(({ ref }) => ref),
			['www-to-apex', 'root-to-base', 'clips-to-range-host', 'markdown-twin'],
		);
		for (const rule of rules) {
			assert.equal(rule.action, 'redirect');
			assert.equal(rule.enabled, true);
			assert.ok(rule.description.length > 0);
		}
	});

	test('www goes to the apex, path and query kept, permanently', () => {
		const { expression, action_parameters: p } = byRef['www-to-apex'];
		assert.equal(expression, 'http.host eq "www.phonometry.dev"');
		assert.deepEqual(p.from_value, {
			status_code: 301,
			target_url: { expression: 'concat("https://phonometry.dev", http.request.uri.path)' },
			preserve_query_string: true,
		});
	});

	test('the bare root goes to the base path while there is one', () => {
		const { expression, action_parameters: p } = byRef['root-to-base'];
		assert.equal(expression, 'http.host eq "phonometry.dev" and http.request.uri.path eq "/"');
		assert.deepEqual(p.from_value, {
			status_code: 302,
			target_url: { value: 'https://phonometry.dev/phonometry/' },
			preserve_query_string: true,
		});
		assert.equal(redirectRules({ ...options, prefix: '', exclusions: twinExclusions('') }).some(({ ref }) => ref === 'root-to-base'), false);
	});

	test('a clip goes to a host that answers byte ranges', () => {
		const { expression, action_parameters: p } = byRef['clips-to-range-host'];
		assert.equal(expression, 'http.host eq "phonometry.dev" and http.request.uri.path wildcard "/phonometry/media/*.webm"');
		assert.deepEqual(p.from_value, {
			status_code: 302,
			target_url: {
				expression:
					'wildcard_replace(http.request.uri.path, "/phonometry/media/*.webm", "https://docs.jmrp.io/phonometry/media/${1}.webm")',
			},
			preserve_query_string: false,
		});
	});

	test('the Markdown rule names the copy beside the page and excludes the pages without one', () => {
		const { expression, action_parameters: p } = byRef['markdown-twin'];
		assert.equal(
			expression,
			[
				'http.host eq "phonometry.dev"',
				'http.request.method in {"GET" "HEAD"}',
				'starts_with(http.request.uri.path, "/phonometry/")',
				'ends_with(http.request.uri.path, "/")',
				'any(http.request.headers["accept"][*] wildcard "*text/markdown*")',
				'not any(http.request.headers["accept"][*] wildcard "*text/html*text/markdown*")',
				'not any(http.request.headers["accept"][*] wildcard "*application/xhtml+xml*text/markdown*")',
				'not starts_with(http.request.uri.path, "/phonometry/es/reference/api/")',
			].join(' and '),
		);
		assert.deepEqual(p.from_value, {
			status_code: 302,
			target_url: { expression: 'concat(http.request.uri.path, "index.md")' },
			preserve_query_string: false,
		});
	});

	test('pages listed one by one are excluded by an in-set', () => {
		const rule = redirectRules({ ...options, exclusions: { pages: ['/phonometry/x/', '/phonometry/y/'], subtrees: [] } }).at(-1);
		assert.match(rule.expression, / and not http\.request\.uri\.path in \{"\/phonometry\/x\/" "\/phonometry\/y\/"\}$/);
	});

	test('the clip host moves to R2 by changing one argument', () => {
		const rule = redirectRules({ ...options, clipBase: 'https://media.phonometry.dev/' })[2];
		assert.match(rule.action_parameters.from_value.target_url.expression, /"https:\/\/media\.phonometry\.dev\/\$\{1\}\.webm"\)$/);
	});

	test('a quote in a host or path is refused, so no expression can be broken out of', () => {
		assert.throws(() => redirectRules({ ...options, host: 'a"b' }), /host/);
		assert.throws(() => redirectRules({ ...options, clipBase: 'https://x/"' }), /clip/);
	});
});

describe('responseHeaderRules', () => {
	const rules = responseHeaderRules({ host: 'phonometry.dev', prefix });
	const byRef = Object.fromEntries(rules.map((rule) => [rule.ref, rule]));

	test('three rules in order, all rewrites', () => {
		assert.deepEqual(
			rules.map(({ ref }) => ref),
			['markdown-twin-vary', 'not-found-plain', 'astro-immutable'],
		);
		for (const rule of rules) {
			assert.equal(rule.action, 'rewrite');
			assert.equal(rule.enabled, true);
			assert.ok(rule.description.length > 0);
		}
	});

	test('the 302 of the Markdown rule varies on Accept and is never stored', () => {
		const rule = byRef['markdown-twin-vary'];
		assert.equal(
			rule.expression,
			'http.host eq "phonometry.dev" and http.response.code eq 302 and ends_with(http.request.uri.path, "/") and any(http.request.headers["accept"][*] wildcard "*text/markdown*")',
		);
		assert.deepEqual(rule.action_parameters.headers, {
			Vary: { operation: 'set', value: 'Accept' },
			'Cache-Control': { operation: 'set', value: 'no-store' },
		});
	});

	test('a 404 names no copy and no canonical, is HTML and varies on encoding only', () => {
		const rule = byRef['not-found-plain'];
		assert.equal(rule.expression, 'http.host eq "phonometry.dev" and http.response.code eq 404');
		assert.deepEqual(rule.action_parameters.headers, {
			Link: { operation: 'remove' },
			Vary: { operation: 'set', value: 'Accept-Encoding' },
			'Content-Type': { operation: 'set', value: 'text/html; charset=utf-8' },
		});
	});

	test('a content-hashed file is immutable only when it was found', () => {
		const rule = byRef['astro-immutable'];
		assert.equal(
			rule.expression,
			'http.host eq "phonometry.dev" and http.response.code in {200 304} and starts_with(http.request.uri.path, "/phonometry/_astro/")',
		);
		assert.deepEqual(rule.action_parameters.headers, { 'Cache-Control': { operation: 'set', value: IMMUTABLE } });
		assert.equal(IMMUTABLE, 'public, max-age=31536000, immutable');
		const root = responseHeaderRules({ host: 'phonometry.dev', prefix: '' }).at(-1);
		assert.match(root.expression, /starts_with\(http\.request\.uri\.path, "\/_astro\/"\)$/);
	});
});

describe('wildcardMatch, the model of the wildcard operator', () => {
	test('matches the whole value, case-insensitively, * as any run including none', () => {
		assert.equal(wildcardMatch('Text/Markdown', '*text/markdown*'), true);
		assert.equal(wildcardMatch('text/markdown', 'text/markdown'), true);
		assert.equal(wildcardMatch('x text/markdown', 'text/markdown'), false);
		assert.equal(wildcardMatch('text/html, text/markdown', '*text/html*text/markdown*'), true);
		assert.equal(wildcardMatch('text/markdown, text/html', '*text/html*text/markdown*'), false);
		assert.equal(wildcardMatch('a.b+c', 'a.b+c'), true);
		assert.equal(wildcardMatch('aXb+c', 'a.b+c'), false);
	});
});
