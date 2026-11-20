// PHONOMETRY_SITE: which host the build is made for, with closed values,
// read from src/data/site-targets.json (scripts/site_target.py reads the same
// file for the Python generators, tests/test_site_target.py holds that side).
//
// Unset, the build is the one docs.jmrp.io serves, byte for byte; the
// phonometry.dev preview builds with PHONOMETRY_SITE=phonometry.dev; anything
// else stops the build before it starts, so a typo cannot publish a site
// whose canonical URLs name a host nobody serves.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

import {
	DEFAULT_SITE,
	LEGACY_ORIGINS,
	SITE_TARGETS,
	basePath,
	checkedTarget,
	clipBase,
	mediaOrigins,
	siteTarget,
	siteUrl,
} from '../src/data/site.mjs';

const SITE = fileURLToPath(new URL('../src/data/site.mjs', import.meta.url));

/** The two exports as a fresh process with that environment reads them. */
function readWith(value) {
	const env = { ...process.env };
	if (value === undefined) delete env.PHONOMETRY_SITE;
	else env.PHONOMETRY_SITE = value;
	const script = `import(${JSON.stringify(SITE)}).then((m) => process.stdout.write(JSON.stringify([m.siteUrl, m.basePath])))`;
	return JSON.parse(execFileSync(process.execPath, ['--input-type=module', '-e', script], { env, encoding: 'utf8' }));
}

test('unset, the build is docs.jmrp.io under /phonometry, as it always was', () => {
	assert.deepEqual(readWith(undefined), ['https://docs.jmrp.io', '/phonometry']);
	assert.deepEqual(readWith(''), ['https://docs.jmrp.io', '/phonometry']);
});

test('naming docs.jmrp.io gives the same build', () => {
	assert.deepEqual(readWith('docs.jmrp.io'), ['https://docs.jmrp.io', '/phonometry']);
});

test('phonometry.dev moves the origin and keeps the base path for now', () => {
	assert.deepEqual(readWith('phonometry.dev'), ['https://phonometry.dev', '/phonometry']);
});

test('any other value is refused, by name', () => {
	for (const value of ['phonometry.org', 'https://phonometry.dev', 'PHONOMETRY.DEV', 'toString', '__proto__']) {
		assert.throws(() => siteTarget(value), new RegExp(`PHONOMETRY_SITE=${value.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')} is not one of`), value);
	}
	assert.throws(() => readWith('phonometry.org'), /PHONOMETRY_SITE=phonometry\.org is not one of docs\.jmrp\.io, phonometry\.dev/);
});

test('the table is closed and frozen, and this process reads it like the others', () => {
	assert.deepEqual(Object.keys(SITE_TARGETS), ['docs.jmrp.io', 'phonometry.dev']);
	assert.ok(Object.isFrozen(SITE_TARGETS));
	for (const target of Object.values(SITE_TARGETS)) assert.ok(Object.isFrozen(target));
	assert.deepEqual([siteUrl, basePath], readWith(process.env.PHONOMETRY_SITE));
});

test('every value comes from site-targets.json, the file the Python generators read too', () => {
	const file = JSON.parse(readFileSync(new URL('../src/data/site-targets.json', import.meta.url), 'utf8'));
	assert.deepEqual(SITE_TARGETS, file.targets);
	assert.equal(DEFAULT_SITE, file.default);
	assert.deepEqual(LEGACY_ORIGINS, file.legacy);
	assert.deepEqual(mediaOrigins, file.mediaOrigins);
	assert.equal(clipBase, file.clipBase);
	assert.ok(Object.isFrozen(LEGACY_ORIGINS) && LEGACY_ORIGINS.every(Object.isFrozen));
	assert.ok(Object.isFrozen(mediaOrigins));
});

test('the clip host is one the pages allow', () => {
	assert.ok(mediaOrigins.includes(new URL(clipBase).origin), `${clipBase} is not under ${mediaOrigins.join(', ')}`);
});

test('a target is an https origin and a base path every reader can append a route to', () => {
	assert.deepEqual(checkedTarget({ siteUrl: 'https://example.org', basePath: '' }, 't'), { siteUrl: 'https://example.org', basePath: '' });
	assert.deepEqual(checkedTarget({ siteUrl: 'https://example.org', basePath: '/a/b-c' }, 't'), { siteUrl: 'https://example.org', basePath: '/a/b-c' });
	assert.ok(Object.isFrozen(checkedTarget({ siteUrl: 'https://example.org', basePath: '' }, 't')));
	// A port is refused here and by scripts/site_target.py alike (its test
	// holds the same case): every reader joins a host and a path, and none
	// of them carries a port.
	for (const siteUrl of ['http://example.org', 'https://example.org/', 'https://example.org/docs', 'https://example.org:8443', 'example.org', 42]) {
		assert.throws(() => checkedTarget({ siteUrl, basePath: '' }, 't'), /the t siteUrl .* is not an https origin/, String(siteUrl));
	}
	for (const base of ['/', 'docs', '/docs/', '/Docs', undefined]) {
		assert.throws(() => checkedTarget({ siteUrl: 'https://example.org', basePath: base }, 't'), /the t basePath .* is neither empty nor \/segment/, String(base));
	}
});
