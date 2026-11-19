// The edge list answers every retired address, its Markdown copy and every
// llms shard name retired before the generator kept them.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import { cloudflareItems, copyOf, legacyItems, legacyList, legacyPageItems, redirectPairs, retiredAddresses, retiredShards, sitemapPages } from './cloudflare-redirects.mjs';
import { basePath, siteUrl } from '../src/data/site.mjs';

// The site the fixtures are written for, named rather than read from the
// build, so they hold whatever site the build is made for.
const docs = { target: { siteUrl: 'https://docs.jmrp.io', basePath: '/phonometry' } };
const legacy = { siteUrl: 'https://docs.jmrp.io', basePath: '/phonometry' };
const root = { siteUrl: 'https://phonometry.dev', basePath: '' };

const record = (content) => {
	const file = join(mkdtempSync(join(tmpdir(), 'llms-shards-')), 'llms-shards.json');
	writeFileSync(file, typeof content === 'string' ? content : JSON.stringify(content));
	return file;
};

test('a retired page answers in both spellings, and its Markdown copy leads to the copy of the page it moved to', () => {
	const addresses = retiredAddresses({ '/guides/levels/': '/phonometry/signals/levels/levels/' }, {}, docs);
	assert.deepEqual(Object.fromEntries(addresses), {
		'docs.jmrp.io/phonometry/guides/levels/': 'https://docs.jmrp.io/phonometry/signals/levels/levels/',
		'docs.jmrp.io/phonometry/guides/levels': 'https://docs.jmrp.io/phonometry/signals/levels/levels/',
		'docs.jmrp.io/phonometry/guides/levels/index.md': 'https://docs.jmrp.io/phonometry/signals/levels/levels/index.md',
	});
});

test('a retired Spanish API page leads its copy to the English copy, the only one there is', () => {
	assert.equal(copyOf('/phonometry/es/reference/api/building/facade/', '/phonometry'), '/phonometry/reference/api/building/facade/index.md');
	assert.equal(copyOf('/phonometry/es/start/about/', '/phonometry'), '/phonometry/es/start/about/index.md');
	const addresses = retiredAddresses({ '/es/reference/api/building/fa/': '/phonometry/es/reference/api/building/facade/' }, {}, docs);
	assert.equal(
		addresses.get('docs.jmrp.io/phonometry/es/reference/api/building/fa/index.md'),
		'https://docs.jmrp.io/phonometry/reference/api/building/facade/index.md',
	);
});

test('a retired llms shard name answers with the file that now carries its first page', () => {
	const addresses = retiredAddresses({}, { simulation: 'simulation-1' }, docs);
	assert.deepEqual(Object.fromEntries(addresses), {
		'docs.jmrp.io/phonometry/llms/llms-simulation.txt': 'https://docs.jmrp.io/phonometry/llms/llms-simulation-1.txt',
	});
});

test('every item is a 301 that keeps the query and matches its source alone', () => {
	const items = cloudflareItems({ '/about/': '/phonometry/start/about/' }, { theory: 'theory-1' }, docs);
	assert.equal(items.length, 4);
	for (const { redirect } of items) {
		assert.equal(redirect.status_code, 301);
		assert.equal(redirect.preserve_query_string, true);
		assert.equal(redirect.subpath_matching, false);
		assert.equal(redirect.include_subdomains, false);
	}
});

test("the site's own list holds two items per address, one per copy and one per retired shard name", () => {
	const shards = retiredShards();
	assert.ok(Object.keys(shards).length >= 15);
	assert.equal(shards.simulation, 'simulation-1');
	assert.equal(shards.start, undefined, 'llms-start.txt is still written, as the list of its parts');
	const items = cloudflareItems();
	const copies = items.filter(({ redirect }) => redirect.source_url.endsWith('/index.md'));
	const llms = items.filter(({ redirect }) => redirect.source_url.includes('/llms/'));
	assert.equal(llms.length, Object.keys(shards).length);
	assert.equal(items.length - copies.length - llms.length, 2 * copies.length);
});

test('a record of shard names of another shape stops the list', () => {
	assert.throws(() => retiredShards(record({ published: [] })), /no "redirects" object/);
	assert.throws(() => retiredShards(record({ redirects: { 'a b': 'a-1' } })), /is no pair of shard names/);
	assert.throws(() => retiredShards(record('not json')), SyntaxError);
});

test('an address retired twice stops the list', () => {
	assert.throws(() => retiredAddresses({ '/a/': '/phonometry/b/', '/a': '/phonometry/c/' }, {}, docs), /is retired twice/);
});

test('an address the old site retired goes straight to its page on the current site, in one hop', () => {
	const items = legacyItems(legacy, { '/guides/levels/': '/signals/levels/levels/', '/es/reference/api/building/fa/': '/es/reference/api/building/facade/' }, { simulation: 'simulation-1' }, root);
	assert.deepEqual(
		Object.fromEntries(items.map(({ redirect }) => [redirect.source_url, redirect.target_url])),
		{
			'docs.jmrp.io/phonometry/guides/levels/': 'https://phonometry.dev/signals/levels/levels/',
			'docs.jmrp.io/phonometry/guides/levels': 'https://phonometry.dev/signals/levels/levels/',
			'docs.jmrp.io/phonometry/es/reference/api/building/fa/': 'https://phonometry.dev/es/reference/api/building/facade/',
			'docs.jmrp.io/phonometry/es/reference/api/building/fa': 'https://phonometry.dev/es/reference/api/building/facade/',
			'docs.jmrp.io/phonometry/guides/levels/index.md': 'https://phonometry.dev/signals/levels/levels/index.md',
			'docs.jmrp.io/phonometry/es/reference/api/building/fa/index.md': 'https://phonometry.dev/reference/api/building/facade/index.md',
			'docs.jmrp.io/phonometry/llms/llms-simulation.txt': 'https://phonometry.dev/llms/llms-simulation-1.txt',
		},
	);
	for (const { redirect } of items) {
		assert.equal(redirect.status_code, 301);
		assert.equal(redirect.preserve_query_string, true);
	}
});

test("the build's own list and _redirects pairs answer on the site the build is made for", () => {
	const host = new URL(siteUrl).host;
	const items = cloudflareItems();
	assert.ok(items.length > 0);
	for (const { redirect } of items) {
		assert.ok(redirect.source_url.startsWith(`${host}${basePath}/`), redirect.source_url);
		assert.ok(redirect.target_url.startsWith(`${siteUrl}${basePath}/`), redirect.target_url);
	}
	assert.deepEqual(
		redirectPairs().map(({ from, to }) => [`${host}${from}`, `${siteUrl}${to}`]),
		items.map(({ redirect }) => [redirect.source_url, redirect.target_url]),
	);
});

// --- The list docs.jmrp.io answers from once the site lives at the root -----

/** A dist/ with a sitemap index and one shard, as @astrojs/sitemap writes them. */
const distWith = (pages, origin = 'https://phonometry.dev') => {
	const dist = mkdtempSync(join(tmpdir(), 'legacy-dist-'));
	writeFileSync(join(dist, 'sitemap-index.xml'), `<?xml version="1.0"?><sitemapindex><sitemap><loc>${origin}/sitemap-0.xml</loc></sitemap></sitemapindex>`);
	writeFileSync(join(dist, 'sitemap-0.xml'), `<?xml version="1.0"?><urlset>${pages.map((page) => `<url><loc>${origin}${page}</loc><lastmod>2026-11-19</lastmod></url>`).join('')}</urlset>`);
	return dist;
};

test('the pages of the sitemap are read from the index and its shards, on the current site', () => {
	const dist = distWith(['/', '/signals/', '/es/signals/levels/']);
	assert.deepEqual(sitemapPages(dist, root), ['/', '/signals/', '/es/signals/levels/']);
	assert.throws(() => sitemapPages(distWith(['/signals/'], 'https://docs.jmrp.io'), root), /not on https:\/\/phonometry\.dev/);
	assert.throws(() => sitemapPages(distWith([]), root), /no page/);
	assert.throws(() => sitemapPages(distWith(['/signals']), root), /does not end in \//);
});

test('each page the old site served answers without its slash in one hop, straight to its page here', () => {
	const items = legacyPageItems(['/', '/signals/', '/es/signals/levels/'], legacy, root);
	assert.deepEqual(
		items.map(({ redirect }) => [redirect.source_url, redirect.target_url]),
		[
			['docs.jmrp.io/phonometry', 'https://phonometry.dev/'],
			['docs.jmrp.io/phonometry/signals', 'https://phonometry.dev/signals/'],
			['docs.jmrp.io/phonometry/es/signals/levels', 'https://phonometry.dev/es/signals/levels/'],
		],
	);
	for (const { redirect } of items) {
		assert.deepEqual({ ...redirect, source_url: undefined, target_url: undefined }, { source_url: undefined, target_url: undefined, status_code: 301, preserve_query_string: true, include_subdomains: false, subpath_matching: false, preserve_path_suffix: false });
	}
});

test('the list for the old host: every retired address and every page without its slash, none twice', () => {
	const map = { '/guides/levels/': '/signals/levels/levels/' };
	const items = legacyList(legacy, ['/', '/signals/levels/levels/'], map, { simulation: 'simulation-1' }, root);
	const sources = items.map(({ redirect }) => redirect.source_url);
	assert.equal(items.length, 4 + 2);
	assert.equal(new Set(sources).size, sources.length);
	assert.ok(sources.includes('docs.jmrp.io/phonometry/guides/levels'));
	assert.ok(sources.includes('docs.jmrp.io/phonometry/signals/levels/levels'));
	assert.ok(items.every(({ redirect }) => redirect.target_url.startsWith('https://phonometry.dev/')));
	assert.throws(() => legacyList(legacy, ['/guides/levels/'], map, {}, root), /retired twice/);
});

test('--legacy prints that list for the build in dist/, and refuses a dist with no sitemap', () => {
	const script = join(import.meta.dirname, 'cloudflare-redirects.mjs');
	const dist = distWith(['/', '/signals/']);
	const printed = JSON.parse(execFileSync(process.execPath, [script, '--legacy', '--dist', dist], { encoding: 'utf8' }));
	const sources = printed.map(({ redirect }) => redirect.source_url);
	assert.ok(sources.includes('docs.jmrp.io/phonometry'));
	assert.ok(sources.includes('docs.jmrp.io/phonometry/signals'));
	assert.equal(printed.length, cloudflareItems(undefined, undefined, { source: legacy }).length + 2);
	assert.ok(printed.every(({ redirect }) => redirect.source_url.startsWith('docs.jmrp.io/phonometry') && redirect.target_url.startsWith(`${siteUrl}${basePath}/`)));
	assert.throws(() => execFileSync(process.execPath, [script, '--legacy', '--dist', mkdtempSync(join(tmpdir(), 'empty-'))], { stdio: 'pipe' }));
});
