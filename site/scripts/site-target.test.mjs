// PHONOMETRY_SITE: which host the build is made for, with closed values.
//
// Unset, the build is the one docs.jmrp.io serves, byte for byte; the
// phonometry.dev preview builds with PHONOMETRY_SITE=phonometry.dev; anything
// else stops the build before it starts, so a typo cannot publish a site
// whose canonical URLs name a host nobody serves.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

import { SITE_TARGETS, basePath, siteTarget, siteUrl } from '../src/data/site.mjs';

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
