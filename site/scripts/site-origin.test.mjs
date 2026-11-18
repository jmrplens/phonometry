// The postbuild step that moves the hand-written files of public/ to the host
// the build was made for. The default build is left alone, byte for byte.
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';

import { CANONICAL_ORIGIN, ORIGIN_FILES, moveOrigin } from './site-origin.mjs';

function dist(files) {
	const root = mkdtempSync(join(tmpdir(), 'site-origin-'));
	mkdirSync(root, { recursive: true });
	for (const [name, body] of Object.entries(files)) writeFileSync(join(root, name), body);
	return root;
}

const robots = 'Sitemap: https://docs.jmrp.io/phonometry/sitemap-index.xml\n# https://docs.jmrp.io/robots.txt\n';
const sitemap = '<loc>https://docs.jmrp.io/phonometry/sitemap-0.xml</loc>\n';

test('the files it moves are the two hand-written ones that name the host', () => {
	assert.deepEqual(ORIGIN_FILES, ['robots.txt', 'sitemap.xml']);
	assert.equal(CANONICAL_ORIGIN, 'https://docs.jmrp.io');
});

test('the default build is not touched', (t) => {
	const root = dist({ 'robots.txt': robots, 'sitemap.xml': sitemap });
	t.after(() => rmSync(root, { recursive: true, force: true }));
	assert.deepEqual(moveOrigin(root, 'https://docs.jmrp.io'), []);
	assert.equal(readFileSync(join(root, 'robots.txt'), 'utf8'), robots);
	assert.equal(readFileSync(join(root, 'sitemap.xml'), 'utf8'), sitemap);
});

test('a phonometry.dev build names phonometry.dev in both', (t) => {
	const root = dist({ 'robots.txt': robots, 'sitemap.xml': sitemap });
	t.after(() => rmSync(root, { recursive: true, force: true }));
	assert.deepEqual(moveOrigin(root, 'https://phonometry.dev'), ['robots.txt', 'sitemap.xml']);
	assert.equal(
		readFileSync(join(root, 'robots.txt'), 'utf8'),
		'Sitemap: https://phonometry.dev/phonometry/sitemap-index.xml\n# https://phonometry.dev/robots.txt\n',
	);
	assert.equal(readFileSync(join(root, 'sitemap.xml'), 'utf8'), '<loc>https://phonometry.dev/phonometry/sitemap-0.xml</loc>\n');
});

test('a file that no longer names the host fails, so the list cannot go stale', (t) => {
	const root = dist({ 'robots.txt': robots, 'sitemap.xml': '<loc>/sitemap-0.xml</loc>\n' });
	t.after(() => rmSync(root, { recursive: true, force: true }));
	assert.throws(() => moveOrigin(root, 'https://phonometry.dev'), /sitemap\.xml names no https:\/\/docs\.jmrp\.io/);
});
