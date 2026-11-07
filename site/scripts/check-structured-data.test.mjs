// The failures of the structured data that only the built site can show.
//
// Each page's `datePublished` falls back to its `dateModified` when
// src/lib/page-dates.mjs has no date for it, and a page added and never edited
// has the same two dates by right, so no single page can be judged. A whole build
// can: one failed read of the history, or a shallow checkout, leaves every field
// present and every page saying it was published on the day it was last edited.
//
// The software node names its operating systems one per entry, as jmrp.io does
// for the same `@id`: the site-wide graph is the same on every page, so the
// check reads it once per distinct value and says on how many pages it stands.
//
// Each test here writes a build of a few pages into a directory of its own and
// runs the check on it the way CI does.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-structured-data.mjs');
const ORIGIN = `${siteUrl}${basePath}`;

/** The platforms the software node names when a test does not say otherwise. */
const PLATFORMS = ['Linux', 'macOS', 'Windows'];

/**
 * The built HTML of one page that gives the check nothing else to report.
 *
 * `operatingSystem` is what the software node names; null leaves the property out.
 */
function page(slug, datePublished, dateModified, operatingSystem = PLATFORMS) {
	const url = `${ORIGIN}/${slug}/`;
	const graph = [
		...['Person', 'WebSite', 'SoftwareSourceCode'].map((type) => ({ '@type': type })),
		{ '@type': 'SoftwareApplication', ...(operatingSystem === null ? {} : { operatingSystem }) },
		{
			'@type': 'TechArticle',
			'@id': `${url}#article`,
			url,
			inLanguage: 'en',
			workTranslation: { '@id': `${ORIGIN}/es/${slug}/#article` },
			...Object.fromEntries(
				[
					'about',
					'author',
					'description',
					'headline',
					'image',
					'isPartOf',
					'mainEntityOfPage',
					'publisher',
					'speakable',
					'wordCount',
				].map((field) => [field, 'a value']),
			),
			datePublished,
			dateModified,
		},
		{
			'@type': 'BreadcrumbList',
			itemListElement: [
				{ position: 1, name: 'Home', item: `${ORIGIN}/` },
				{ position: 2, name: slug, item: url },
			],
		},
	];
	const block = JSON.stringify({ '@context': 'https://schema.org', '@graph': graph });
	return `<!doctype html><html><head><script type="application/ld+json">${block}</script></head></html>`;
}

/**
 * Build `pages` pages, the first `dated` of them published on `published`, and run the check on them.
 *
 * `platforms` gives the software node's `operatingSystem` on each page, by its
 * index; a page past its end names the default platforms.
 */
function check(t, pages, dated, published = '2026-07-01', platforms = []) {
	const dist = mkdtempSync(join(tmpdir(), 'check-structured-data-'));
	t.after(() => rmSync(dist, { recursive: true, force: true }));
	for (let i = 0; i < pages; i += 1) {
		const dir = join(dist, `page-${i}`);
		mkdirSync(dir);
		const operatingSystem = i < platforms.length ? platforms[i] : PLATFORMS;
		writeFileSync(
			join(dir, 'index.html'),
			page(`page-${i}`, i < dated ? published : '2026-10-01', '2026-10-01', operatingSystem),
		);
	}
	const ran = spawnSync(process.execPath, [CHECK, dist], { encoding: 'utf8' });
	return { status: ran.status, out: ran.stdout, err: ran.stderr };
}

test('a build where most pages have been edited since they were added passes', (t) => {
	const ran = check(t, 10, 9);
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}9 of the 10 articles were last edited after the day they were first published/);
	assert.equal(ran.err, '');
});

test('a build where no page has two different dates fails, and says where to look', (t) => {
	const ran = check(t, 10, 0);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 0 of the 10 articles were last edited after the day they were first published/);
	assert.match(ran.err, /page-dates\.mjs/);
});

test('a page published after its last edit does not count as edited', (t) => {
	const ran = check(t, 10, 10, '2026-11-01');
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 0 of the 10 articles were last edited after the day they were first published/);
});

test('a tenth of the pages is the floor: one under it fails and one on it passes', (t) => {
	assert.equal(check(t, 11, 1).status, 1);
	assert.equal(check(t, 10, 1).status, 0);
});

test('a software node that names its operating systems one per entry passes, and says on how many pages', (t) => {
	const ran = check(t, 10, 9);
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}the software node names its 3 operating systems one per entry on 10 pages/);
});

test('a software node that joins its operating systems into one string fails, and names the value', (t) => {
	const ran = check(t, 10, 9, undefined, Array(10).fill('Windows, Linux, macOS'));
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 10 page\(s\): the software node's operatingSystem is "Windows, Linux, macOS"/);
	assert.match(ran.err, /jmrp\.io/);
});

test('one entry that holds two platforms fails as the joined string does', (t) => {
	const ran = check(t, 10, 9, undefined, Array(10).fill(['Linux', 'macOS, Windows']));
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 10 page\(s\): the software node's operatingSystem is \["Linux","macOS, Windows"\]/);
});

test('a software node that names no operating system, or one twice, fails', (t) => {
	const ran = check(t, 10, 9, undefined, [null, [], ['Linux', 'Linux']]);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 1 page\(s\): the software node's operatingSystem is null/);
	assert.match(ran.err, /FAIL 1 page\(s\): the software node's operatingSystem is \[\]/);
	assert.match(ran.err, /FAIL 1 page\(s\): the software node's operatingSystem is \["Linux","Linux"\]/);
	assert.match(ran.out, /ok {3}the software node names its 3 operating systems one per entry on 7 pages/);
});
