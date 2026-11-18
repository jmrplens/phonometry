// The `_redirects` file of the preview: the same pairs as docs.jmrp.io's
// Bulk Redirects list, and the limits Static Assets documents.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { cloudflareItems, copyOf, redirectPairs, retiredShards } from '../../scripts/cloudflare-redirects.mjs';
import { redirects } from '../../src/data/redirects.mjs';
import { basePath, siteUrl } from '../../src/data/site.mjs';
import {
	REDIRECT_LINE_LIMIT,
	REDIRECT_STATIC_LIMIT,
	parseRedirects,
	redirectProblems,
	redirectsFile,
} from '../lib/redirects.mjs';

describe('redirectsFile', () => {
	const pairs = redirectPairs();
	const text = redirectsFile(pairs);
	const lines = parseRedirects(text);

	test('one 301 line per source of the Bulk Redirects list, same targets, same order', () => {
		const items = cloudflareItems();
		const host = new URL(siteUrl).host;
		assert.equal(lines.length, items.length);
		lines.forEach((line, i) => {
			assert.equal(`${host}${line.from}`, items[i].redirect.source_url);
			assert.equal(`${siteUrl}${line.to}`, items[i].redirect.target_url);
			assert.equal(line.code, 301);
		});
	});

	test('every address of the map, with and without its slash', () => {
		const sources = new Set(lines.map(({ from }) => from));
		for (const from of Object.keys(redirects)) {
			assert.ok(sources.has(`${basePath}${from}`), from);
			if (from.endsWith('/')) assert.ok(sources.has(`${basePath}${from.slice(0, -1)}`), from);
		}
	});

	test('the Markdown copy of every retired page and every retired llms shard name, as on docs.jmrp.io', () => {
		const to = new Map(lines.map((line) => [line.from, line.to]));
		for (const [from, target] of Object.entries(redirects)) {
			if (from.endsWith('/') && target.endsWith('/')) assert.equal(to.get(`${basePath}${from}index.md`), copyOf(target), from);
		}
		for (const [from, name] of Object.entries(retiredShards())) {
			assert.equal(to.get(`${basePath}/llms/llms-${from}.txt`), `${basePath}/llms/llms-${name}.txt`, from);
		}
	});

	test('the real map passes every check against a tree that holds every target', () => {
		assert.deepEqual(redirectProblems(pairs, { exists: () => true }), []);
	});

	test('limits are the documented ones', () => {
		assert.equal(REDIRECT_STATIC_LIMIT, 2000);
		assert.equal(REDIRECT_LINE_LIMIT, 1000);
	});
});

describe('redirectProblems', () => {
	const ok = { exists: () => true };

	test('a repeated source', () => {
		const problems = redirectProblems([{ from: '/a/', to: '/b/' }, { from: '/a/', to: '/c/' }], ok);
		assert.match(problems.join('\n'), /listed twice: \/a\//);
	});

	test('a target the tree does not hold', () => {
		const problems = redirectProblems([{ from: '/a/', to: '/gone/' }], { exists: (to) => to !== '/gone/' });
		assert.match(problems.join('\n'), /no page at \/gone\//);
	});

	test('a target that is itself a source (two hops)', () => {
		const problems = redirectProblems([{ from: '/a/', to: '/b/' }, { from: '/b/', to: '/c/' }], ok);
		assert.match(problems.join('\n'), /\/a\/ -> \/b\/ is itself redirected/);
	});

	test('a source with a splat, a placeholder or a space would not be a static line', () => {
		for (const from of ['/a/*', '/a/:name/', '/a b/']) {
			assert.match(redirectProblems([{ from, to: '/b/' }], ok).join('\n'), /not a plain path/, from);
		}
	});

	test('more lines than the static limit', () => {
		const many = Array.from({ length: REDIRECT_STATIC_LIMIT + 1 }, (_, i) => ({ from: `/p${i}/`, to: '/t/' }));
		assert.match(redirectProblems(many, ok).join('\n'), /2001 redirects, over the 2000/);
	});

	test('a line over the character limit', () => {
		const long = `/${'x'.repeat(REDIRECT_LINE_LIMIT)}/`;
		assert.match(redirectProblems([{ from: long, to: '/t/' }], ok).join('\n'), /characters, over the 1000/);
	});
});
