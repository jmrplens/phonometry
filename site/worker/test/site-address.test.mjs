// The addresses the deploy checks read (scripts/site-address.mjs): the
// served host, the build's base path and canonical site, and the clip host,
// for the target of today's table and for the build at the root.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { DEFAULT_SITE, SITE_TARGETS, clipBase } from '../../src/data/site.mjs';
import { SERVED_ORIGIN } from '../lib/staging.mjs';
import { outputLines, siteAddress } from '../scripts/site-address.mjs';

const SCRIPT = join(dirname(fileURLToPath(import.meta.url)), '..', 'scripts', 'site-address.mjs');

test('the pages are checked on the served host, under the base path of the build', () => {
	const address = siteAddress({ siteUrl: 'https://docs.jmrp.io', basePath: '/phonometry', clipBase: 'https://docs.jmrp.io/phonometry/media/' }, 'https://phonometry.dev');
	assert.deepEqual(address, {
		origin: 'https://phonometry.dev',
		base: '/phonometry',
		canonical: 'https://docs.jmrp.io/phonometry',
		page_url: 'https://phonometry.dev/phonometry/',
		clip_base: 'https://docs.jmrp.io/phonometry/media/',
	});
});

test('at the root the base is empty and the home page is the host itself', () => {
	const address = siteAddress({ siteUrl: 'https://phonometry.dev', basePath: '', clipBase: 'https://media.phonometry.dev/' }, 'https://phonometry.dev');
	assert.equal(address.base, '');
	assert.equal(address.canonical, 'https://phonometry.dev');
	assert.equal(address.page_url, 'https://phonometry.dev/');
	assert.equal(outputLines(address).split('\n')[1], 'base=');
});

test('run as a script it prints the default target of site-targets.json, one line each', () => {
	const env = { ...process.env };
	delete env.PHONOMETRY_SITE;
	const printed = execFileSync(process.execPath, [SCRIPT], { env }).toString();
	// The child has PHONOMETRY_SITE unset, so it prints the default target
	// whatever this process was started with: the expected values are that
	// target's, not the ones site.mjs picked here.
	const { siteUrl, basePath } = SITE_TARGETS[DEFAULT_SITE];
	assert.equal(printed, outputLines(siteAddress({ siteUrl, basePath, clipBase }, SERVED_ORIGIN)));
	assert.match(printed, /^origin=https:\/\/phonometry\.dev\nbase=/);
	assert.equal(printed.split('\n').filter(Boolean).length, 5);
});

test('PHONOMETRY_SITE picks the target, as for the build and stage.mjs, and a wrong one stops it', () => {
	const printed = execFileSync(process.execPath, [SCRIPT], { env: { ...process.env, PHONOMETRY_SITE: 'phonometry.dev' } }).toString();
	assert.match(printed, /^canonical=https:\/\/phonometry\.dev/m);
	assert.throws(() => execFileSync(process.execPath, [SCRIPT], { env: { ...process.env, PHONOMETRY_SITE: 'nowhere.example' }, stdio: 'pipe' }));
});
