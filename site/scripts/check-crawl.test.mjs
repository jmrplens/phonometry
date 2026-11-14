// The page dates check-crawl.mjs holds the sitemap to, and the failure it
// reports for a number run into a word, on builds small enough to read.
//
// A page's modified date is written three times from one source: into the
// sitemap's <lastmod> by scripts/add-sitemap-lastmod.mjs, and into its
// structured data and its footer through the `lastUpdated` src/routeData.ts
// sets. The real build only ever hands the check pages whose three dates
// agree, so a check that stopped comparing them would stay green there for
// good. Each test here writes a build of a few pages that passes every other
// rule of the check, with the dates a case needs, runs the check on it the way
// CI does and reads the exit status and the lines it printed.
//
// The real build only ever hands the check pages that pass, so a check that
// stopped reading the text the way a crawler does would stay green there for
// good too. Those tests write the home alone, dated as every other rule asks,
// around a body of their own. What the reader counts as glue, case by case, is
// shared/crawler-text.test.mjs.
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

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-crawl.mjs');
const ORIGIN = `${siteUrl}${basePath}`;

/**
 * A built page at `route` with the head check-crawl.mjs asks of every page,
 * a graph node carrying `modified` and `published`, and a footer that shows
 * `footer` (the published day and the modified moment, as LastUpdated.astro
 * writes them). `node: false` leaves the structured data out, and `body` is
 * what the page shows between its heading and its footer.
 */
function page(
	route,
	{ modified, published = '2026-01-01', footer = [published, `${modified}T10:00:00.000Z`], node = true, body = '' } = {},
) {
	const lang = route.startsWith('/es/') || route === '/es/' ? 'es' : 'en';
	const slug = route.replace(/^\/|\/$/g, '');
	const english = `${ORIGIN}/${slug.replace(/^es(\/|$)/, '')}`.replace(/\/?$/, '/');
	const spanish = `${ORIGIN}/es${english.slice(ORIGIN.length)}`;
	const canonical = `${ORIGIN}${route}`;
	const id = slug === '' || slug === 'es' ? `${canonical}#webpage` : `${canonical}#article`;
	const graph = node
		? [{ '@type': 'TechArticle', '@id': id, datePublished: published, dateModified: modified }]
		: [];
	const title = `${lang === 'es' ? 'Página' : 'Page'} ${slug || 'home'} | phonometry`;
	return [
		`<!DOCTYPE html><html lang="${lang}"><head><meta charset="utf-8"><title>${title}</title>`,
		`<link rel="canonical" href="${canonical}">`,
		`<meta property="og:url" content="${canonical}">`,
		`<meta property="og:locale" content="${lang === 'es' ? 'es_ES' : 'en_US'}">`,
		`<meta property="og:locale:alternate" content="${lang === 'es' ? 'en_US' : 'es_ES'}">`,
		`<link rel="alternate" hreflang="en" href="${english}">`,
		`<link rel="alternate" hreflang="es" href="${spanish}">`,
		`<link rel="alternate" hreflang="x-default" href="${english}">`,
		`<script type="application/ld+json">${JSON.stringify({ '@context': 'https://schema.org', '@graph': graph })}</script>`,
		`</head><body><h1>${title}</h1>${body}<footer><p>`,
		footer.map((datetime) => `<time datetime="${datetime}">${datetime}</time>`).join(', '),
		'</p></footer></body></html>',
	].join('');
}

/**
 * Write a build of `pages` (route -> HTML) with a sitemap that lists every
 * route with its <lastmod> (`lastmod[route]`, or none), and any other files
 * named in `files`, run the check on it, and say how it ended.
 */
function check(t, pages, lastmod, files = {}) {
	const dist = mkdtempSync(join(tmpdir(), 'check-crawl-'));
	t.after(() => rmSync(dist, { recursive: true, force: true }));
	for (const [route, html] of Object.entries(pages)) {
		const file = join(dist, route, 'index.html');
		mkdirSync(dirname(file), { recursive: true });
		writeFileSync(file, html);
	}
	for (const [name, contents] of Object.entries(files)) writeFileSync(join(dist, name), contents);
	const urls = Object.keys(pages)
		.map((route) => `<url><loc>${ORIGIN}${route}</loc>${lastmod[route] ? `<lastmod>${lastmod[route]}</lastmod>` : ''}</url>`)
		.join('');
	writeFileSync(join(dist, 'sitemap-0.xml'), `<urlset>${urls}</urlset>`);
	writeFileSync(join(dist, 'sitemap-index.xml'), `<sitemapindex><sitemap><loc>${ORIGIN}/sitemap-0.xml</loc></sitemap></sitemapindex>`);
	const ran = spawnSync(process.execPath, [CHECK, dist], { encoding: 'utf8' });
	return { status: ran.status, out: ran.stdout, err: ran.stderr };
}

/** The four pages of a build whose dates agree, each with its <lastmod>. */
const agreeing = () => ({
	pages: {
		'/': page('/', { modified: '2026-03-01' }),
		'/es/': page('/es/', { modified: '2026-03-02' }),
		'/a/': page('/a/', { modified: '2026-03-03', published: '2026-03-03', footer: ['2026-03-03'] }),
		'/es/a/': page('/es/a/', { modified: '2026-03-04' }),
	},
	lastmod: { '/': '2026-03-01', '/es/': '2026-03-02', '/a/': '2026-03-03', '/es/a/': '2026-03-04' },
});

test('a build whose sitemap, structured data and footers give each page one date passes', (t) => {
	const { pages, lastmod } = agreeing();
	const ran = check(t, pages, lastmod);
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}the 4 pages of the sitemap give one modified date in its <lastmod>, their dateModified and their footer/);
	assert.match(ran.out, /\n0 failing check\(s\)\./);
});

test('a dateModified that is not the <lastmod> fails, as when Starlight sets its own date', (t) => {
	const { pages, lastmod } = agreeing();
	// What the structured data and the footer say when nothing overrides
	// Starlight's lastUpdated: the last commit that touched the file.
	pages['/a/'] = page('/a/', { modified: '2026-03-09', published: '2026-03-03' });
	const ran = check(t, pages, lastmod);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 1 page\(s\) whose dates disagree:\s+\S+\/a\/: <lastmod> 2026-03-03, dateModified 2026-03-09, footer 2026-03-09/);
});

test('a footer that is not the <lastmod> fails', (t) => {
	const { pages, lastmod } = agreeing();
	pages['/es/a/'] = page('/es/a/', { modified: '2026-03-04', footer: ['2026-01-01', '2026-03-05T23:30:00.000Z'] });
	const ran = check(t, pages, lastmod);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /\/es\/a\/: <lastmod> 2026-03-04, dateModified 2026-03-04, footer 2026-03-05/);
});

test('a sitemap URL with no <lastmod> fails, as when the stamp found no sitemap to write into', (t) => {
	const { pages, lastmod } = agreeing();
	const ran = check(t, pages, { ...lastmod, '/': undefined, '/es/': undefined });
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 2 page\(s\) whose dates disagree:\s+\S+\/: <lastmod> null, not a day/);
});

test('a page with no dateModified of its own fails', (t) => {
	const { pages, lastmod } = agreeing();
	pages['/a/'] = page('/a/', { modified: '2026-03-03', node: false });
	const ran = check(t, pages, lastmod);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /\/a\/: <lastmod> 2026-03-03, dateModified none, footer 2026-03-03/);
});

test('a page published after the day it last changed fails', (t) => {
	const { pages, lastmod } = agreeing();
	pages['/a/'] = page('/a/', { modified: '2026-03-03', published: '2026-03-04', footer: ['2026-03-04', '2026-03-03T23:30:00.000Z'] });
	const ran = check(t, pages, lastmod);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /\/a\/: datePublished 2026-03-04 is after dateModified 2026-03-03/);
});

// A number run into a word, on builds of the home alone.

/** The day the home of the builds below was last changed, in all three places. */
const DAY = '2026-03-01';

/**
 * Run the check on a build of the home alone, showing `body`, with any other
 * files named in `files`, and say how it ended.
 */
const home = (t, body, files = {}) => check(t, { '/': page('/', { modified: DAY, body }) }, { '/': DAY }, files);

const READOUT = (gap) =>
	`<section class="readout"><div class="readout-cell"><span class="readout-value">1897</span>${gap}<span class="readout-label"><a href="${basePath}/">conformance checks passing</a></span></div></section>`;

test('a home whose readout spaces each number from its label passes', (t) => {
	const ran = home(t, READOUT(' '));
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /read 1 pages/);
	assert.match(ran.out, /ok {3}no number runs into a word in the text a crawler reads/);
	assert.match(ran.out, /\n0 failing check\(s\)\./);
	assert.equal(ran.err, '');
});

test('a home whose readout writes a number against its label fails', (t) => {
	const ran = home(t, READOUT(''));
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL 1 place\(s\) where a number runs into a word in the text a crawler reads[^\n]*:\s+\/: "1897" runs into "conformance checks passing"/,
	);
	assert.match(ran.out, /\n1 failing check\(s\)\./);
});

test('a topic landing whose card writes a count against its label fails', (t) => {
	const ran = home(
		t,
		`<nav class="topic-sections"><ul><li><a href="${basePath}/"><span class="label">Theory</span><span class="count">7 pages</span></a></li></ul></nav>`,
	);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /\/: "Theory" runs into "7 pages"/);
});

test('every glued place is reported, with the page it is on', (t) => {
	const chips = ['ISO 717', 'ISO 3382', 'IEC 61260'].map((chip) => `<a class="page-chip">${chip}</a>`).join('');
	const ran = home(t, `<p class="page-chips">${chips}</p>`);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 2 place\(s\)/);
	assert.match(ran.err, /\/: "ISO 717" runs into "ISO 3382"/);
	assert.match(ran.err, /\/: "ISO 717ISO 3382" runs into "IEC 61260"/);
});

test('the error page is read for a number run into a word like any other page', (t) => {
	const error = [
		'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>404 | phonometry</title></head>',
		'<body><h1>Page not found</h1><p><span>404</span><span>Page not found</span></p></body></html>',
	].join('');
	const ran = home(t, READOUT(' '), { '404.html': error });
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 1 place\(s\) where a number runs into a word[^\n]*:\s+\/404\/: "404" runs into "Page not found"/);
	assert.match(ran.out, /\n1 failing check\(s\)\./);
});
