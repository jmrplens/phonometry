// The one path that runs the Worker: the beacon.
//
// Everything else (pages, _astro, media, images, PDFs, the search index, the
// Markdown copies, the llms files, the sitemaps, robots.txt) stays a plain
// asset that runs no code, so the Workers quota can never stop it and a fault
// in the Worker cannot take a file with it. The matcher is a copy of the one
// Static Assets runs, so these tests read the patterns exactly as Cloudflare
// does.
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { describe, test } from 'node:test';

import { BEACON_PATH, WORKER_PATHS, globRegExp, runsWorker } from '../lib/worker-paths.mjs';

/** The asset router miniflare bundles (pnpm keeps it under .pnpm, beside wrangler). */
const PNPM = new URL('../node_modules/.pnpm/', import.meta.url);
const miniflare = existsSync(PNPM) ? readdirSync(PNPM).find((name) => name.startsWith('miniflare@')) : undefined;
const ROUTER = miniflare ? new URL(`${miniflare}/node_modules/miniflare/dist/src/workers/assets/router.worker.js`, PNPM) : new URL('file:///nonexistent');

describe('WORKER_PATHS', () => {
	test('the beacon and nothing else', () => {
		assert.deepEqual(WORKER_PATHS, ['/_v']);
		assert.equal(BEACON_PATH, '/_v');
		assert.ok(Object.isFrozen(WORKER_PATHS));
	});
});

describe('the matcher reads a pattern as Static Assets does', () => {
	// The files agents read are files like any other: a spent quota, a
	// failed deploy of the code or a fault in it cannot answer them with
	// anything but the file.
	const cases = [
		['/_v', true],
		['/_v/', false],
		['/_vx', false],
		['/_V', false],
		['/index.md', false],
		['/signals/index.md', false],
		['/llms.txt', false],
		['/llms-full.txt', false],
		['/llms/llms-signals.txt', false],
		['/sitemap-index.xml', false],
		['/sitemap-0.xml', false],
		['/robots.txt', false],
		['/ai.txt', false],
		['/.well-known/security.txt', false],
		['/signals/', false],
		['/404.html', false],
		['/_astro/index.A1B2.css', false],
		['/media/clip.webm', false],
		['/pagefind/pagefind-entry.json', false],
		['/', false],
	];
	for (const [path, expected] of cases) {
		test(`${path} ${expected ? 'runs' : 'does not run'} the Worker`, () => assert.equal(runsWorker(path), expected));
	}

	test('the copy of generateGlobOnlyRuleRegExp is still the one wrangler ships', { skip: !existsSync(ROUTER) && 'wrangler is not installed' }, () => {
		const source = readFileSync(ROUTER, 'utf8');
		assert.match(source, /var ESCAPE_REGEX_CHARACTERS = \/\[-\/\\\\\^\$\*\+\?\.\(\)\|\[\\\]\{\}\]\/g, escapeRegex = \(str\) => str\.replace\(ESCAPE_REGEX_CHARACTERS, "\\\\\$&"\);/);
		assert.match(source, /var generateGlobOnlyRuleRegExp = \(rule\) => \(rule = rule\.split\("\*"\)\.map\(escapeRegex\)\.join\("\.\*"\), rule = "\^" \+ rule \+ "\$", RegExp\(rule\)\);/);
		assert.equal(String(globRegExp('/a*.b')), String(/^\/a.*\.b$/));
	});
});
