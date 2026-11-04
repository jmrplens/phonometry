// The failure of the first-publication dates that only the built site can show.
//
// Each page's `datePublished` falls back to its `dateModified` when
// src/lib/page-dates.mjs has no date for it, and a page added and never edited
// has the same two dates by right, so no single page can be judged. A whole build
// can: one failed read of the history, or a shallow checkout, leaves every field
// present and every page saying it was published on the day it was last edited.
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

/** The built HTML of one page that gives the check nothing else to report. */
function page(slug, datePublished, dateModified) {
	const url = `${ORIGIN}/${slug}/`;
	const graph = [
		...['Person', 'WebSite', 'SoftwareApplication', 'SoftwareSourceCode'].map((type) => ({ '@type': type })),
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

/** Build `pages` pages, the first `dated` of them with two different dates, and run the check on them. */
function check(t, pages, dated) {
	const dist = mkdtempSync(join(tmpdir(), 'check-structured-data-'));
	t.after(() => rmSync(dist, { recursive: true, force: true }));
	for (let i = 0; i < pages; i += 1) {
		const dir = join(dist, `page-${i}`);
		mkdirSync(dir);
		writeFileSync(join(dir, 'index.html'), page(`page-${i}`, i < dated ? '2026-07-01' : '2026-10-01', '2026-10-01'));
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

test('a tenth of the pages is the floor: one under it fails and one on it passes', (t) => {
	assert.equal(check(t, 11, 1).status, 1);
	assert.equal(check(t, 10, 1).status, 0);
});
