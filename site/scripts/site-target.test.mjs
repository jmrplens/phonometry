// PHONOMETRY_SITE: which host the build is made for, with closed values,
// read from src/data/site-targets.json (scripts/site_target.py reads the same
// file for the Python generators, tests/test_site_target.py holds that side).
//
// There is one target, phonometry.dev at the root: unset, empty or naming it,
// the build is the same; anything else stops the build before it starts, so a
// typo cannot publish a site whose canonical URLs name a host nobody serves.
// The host the site was published on before is a legacy origin, read only by
// the redirect map (scripts/cloudflare-redirects.mjs --legacy).
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

test('unset or empty, the build is phonometry.dev at the root', () => {
	assert.deepEqual(readWith(undefined), ['https://phonometry.dev', '']);
	assert.deepEqual(readWith(''), ['https://phonometry.dev', '']);
	assert.equal(DEFAULT_SITE, 'phonometry.dev');
});

test('naming phonometry.dev gives the same build', () => {
	assert.deepEqual(readWith('phonometry.dev'), ['https://phonometry.dev', '']);
});

test('any other value is refused, by name, the old host among them', () => {
	for (const value of ['docs.jmrp.io', 'phonometry.org', 'https://phonometry.dev', 'PHONOMETRY.DEV', 'toString', '__proto__']) {
		// The message is matched as text, not as a pattern built from the
		// value: a host is no regular expression.
		assert.throws(() => siteTarget(value), (error) => error instanceof Error && error.message.includes(`PHONOMETRY_SITE=${value} is not one of`), value);
	}
	assert.throws(() => readWith('docs.jmrp.io'), /PHONOMETRY_SITE=docs\.jmrp\.io is not one of phonometry\.dev$/m);
});

test('the table is closed and frozen, and this process reads it like the others', () => {
	assert.deepEqual(Object.keys(SITE_TARGETS), ['phonometry.dev']);
	assert.ok(Object.isFrozen(SITE_TARGETS));
	for (const target of Object.values(SITE_TARGETS)) assert.ok(Object.isFrozen(target));
	assert.deepEqual([siteUrl, basePath], readWith(process.env.PHONOMETRY_SITE));
});

test('the site was published before on docs.jmrp.io under /phonometry, and nothing builds for it', () => {
	assert.deepEqual(LEGACY_ORIGINS, [{ siteUrl: 'https://docs.jmrp.io', basePath: '/phonometry' }]);
	for (const legacy of LEGACY_ORIGINS) {
		assert.ok(!Object.values(SITE_TARGETS).some((target) => target.siteUrl === legacy.siteUrl), `${legacy.siteUrl} is still a target`);
	}
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
