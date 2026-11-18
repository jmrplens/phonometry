// The paths that run the Worker: the beacon and the files agents read.
//
// Everything else (pages, _astro, media, images, PDFs, the search index)
// stays a plain asset that runs no code, so the Workers quota can never stop
// it. The matcher is a copy of the one Static Assets runs, so these tests
// read the patterns exactly as Cloudflare does.
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { describe, test } from 'node:test';

import { BEACON_PATH, agentPaths, globRegExp, runsWorker } from '../lib/agent-paths.mjs';

/** The asset router miniflare bundles (pnpm keeps it under .pnpm, beside wrangler). */
const PNPM = new URL('../node_modules/.pnpm/', import.meta.url);
const miniflare = existsSync(PNPM) ? readdirSync(PNPM).find((name) => name.startsWith('miniflare@')) : undefined;
const ROUTER = miniflare ? new URL(`${miniflare}/node_modules/miniflare/dist/src/workers/assets/router.worker.js`, PNPM) : new URL('file:///nonexistent');

describe('agentPaths', () => {
	test('the base path gives the beacon and the agent files, nothing else', () => {
		assert.deepEqual(agentPaths('/phonometry'), [
			'/_v',
			'/phonometry/index.md',
			'/phonometry/*/index.md',
			'/llms*.txt',
			'/phonometry/llms*.txt',
			'/robots.txt',
			'/phonometry/robots.txt',
			'/sitemap*.xml',
			'/phonometry/*.xml',
		]);
		assert.equal(BEACON_PATH, '/_v');
	});

	test('at the root the duplicates fold away', () => {
		assert.deepEqual(agentPaths(''), ['/_v', '/index.md', '/*/index.md', '/llms*.txt', '/robots.txt', '/sitemap*.xml', '/*.xml']);
	});

	test('Static Assets takes at most 100 patterns, each starting with /', () => {
		const patterns = agentPaths('/phonometry');
		assert.ok(patterns.length <= 100);
		for (const pattern of patterns) assert.match(pattern, /^\//);
	});
});

describe('the matcher reads a pattern as Static Assets does', () => {
	const patterns = agentPaths('/phonometry');
	const cases = [
		['/_v', true],
		['/_v/', false],
		['/_vx', false],
		['/phonometry/index.md', true],
		['/phonometry/signals/index.md', true],
		['/phonometry/es/reference/api/levels/index.md', true],
		['/phonometry/Signals/INDEX.md', false],
		['/llms.txt', true],
		['/phonometry/llms.txt', true],
		['/phonometry/llms-full.txt', true],
		['/phonometry/llms/llms-signals.txt', true],
		['/robots.txt', true],
		['/phonometry/robots.txt', true],
		['/sitemap.xml', true],
		['/sitemap-index.xml', true],
		['/phonometry/sitemap-index.xml', true],
		['/phonometry/sitemap-0.xml', true],
		['/phonometry/', false],
		['/phonometry/signals/', false],
		['/phonometry/404.html', false],
		['/phonometry/_astro/index.A1B2.css', false],
		['/phonometry/media/clip.webm', false],
		['/phonometry/pagefind/pagefind-entry.json', false],
		['/phonometry/favicon.svg', false],
		['/', false],
	];
	for (const [path, expected] of cases) {
		test(`${path} ${expected ? 'runs' : 'does not run'} the Worker`, () => assert.equal(runsWorker(path, patterns), expected));
	}

	test('the copy of generateGlobOnlyRuleRegExp is still the one wrangler ships', { skip: !existsSync(ROUTER) && 'wrangler is not installed' }, () => {
		const source = readFileSync(ROUTER, 'utf8');
		assert.match(source, /var ESCAPE_REGEX_CHARACTERS = \/\[-\/\\\\\^\$\*\+\?\.\(\)\|\[\\\]\{\}\]\/g, escapeRegex = \(str\) => str\.replace\(ESCAPE_REGEX_CHARACTERS, "\\\\\$&"\);/);
		assert.match(source, /var generateGlobOnlyRuleRegExp = \(rule\) => \(rule = rule\.split\("\*"\)\.map\(escapeRegex\)\.join\("\.\*"\), rule = "\^" \+ rule \+ "\$", RegExp\(rule\)\);/);
		assert.equal(String(globRegExp('/a*.b')), String(/^\/a.*\.b$/));
	});
});
