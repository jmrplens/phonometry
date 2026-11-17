// The edge list answers every retired address, its Markdown copy and every
// llms shard name retired before the generator kept them.
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import { cloudflareItems, copyOf, retiredAddresses, retiredShards } from './cloudflare-redirects.mjs';

const record = (content) => {
	const file = join(mkdtempSync(join(tmpdir(), 'llms-shards-')), 'llms-shards.json');
	writeFileSync(file, typeof content === 'string' ? content : JSON.stringify(content));
	return file;
};

test('a retired page answers in both spellings, and its Markdown copy leads to the copy of the page it moved to', () => {
	const addresses = retiredAddresses({ '/guides/levels/': '/phonometry/signals/levels/levels/' }, {});
	assert.deepEqual(Object.fromEntries(addresses), {
		'docs.jmrp.io/phonometry/guides/levels/': 'https://docs.jmrp.io/phonometry/signals/levels/levels/',
		'docs.jmrp.io/phonometry/guides/levels': 'https://docs.jmrp.io/phonometry/signals/levels/levels/',
		'docs.jmrp.io/phonometry/guides/levels/index.md': 'https://docs.jmrp.io/phonometry/signals/levels/levels/index.md',
	});
});

test('a retired Spanish API page leads its copy to the English copy, the only one there is', () => {
	assert.equal(copyOf('/phonometry/es/reference/api/building/facade/'), '/phonometry/reference/api/building/facade/index.md');
	assert.equal(copyOf('/phonometry/es/start/about/'), '/phonometry/es/start/about/index.md');
	const addresses = retiredAddresses({ '/es/reference/api/building/fa/': '/phonometry/es/reference/api/building/facade/' }, {});
	assert.equal(
		addresses.get('docs.jmrp.io/phonometry/es/reference/api/building/fa/index.md'),
		'https://docs.jmrp.io/phonometry/reference/api/building/facade/index.md',
	);
});

test('a retired llms shard name answers with the file that now carries its first page', () => {
	const addresses = retiredAddresses({}, { simulation: 'simulation-1' });
	assert.deepEqual(Object.fromEntries(addresses), {
		'docs.jmrp.io/phonometry/llms/llms-simulation.txt': 'https://docs.jmrp.io/phonometry/llms/llms-simulation-1.txt',
	});
});

test('every item is a 301 that keeps the query and matches its source alone', () => {
	const items = cloudflareItems({ '/about/': '/phonometry/start/about/' }, { theory: 'theory-1' });
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
	assert.throws(() => retiredAddresses({ '/a/': '/phonometry/b/', '/a': '/phonometry/c/' }, {}), /is retired twice/);
});
