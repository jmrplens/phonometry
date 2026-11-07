// The failures of the structured data that only the built site can show, on
// builds small enough to read.
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
// The same block is held to a byte budget: most of it is the Person spliced
// from jmrp.io, which grows when jmrp.io changes and never in a diff here.
//
// The real build only ever hands the check the works the guides cite today,
// named the way citations.mjs names them today, so a branch of the check that
// stopped seeing a bare reference, an anonymous publisher, a Spanish standard
// paired with the wrong English one or a page naming a work otherwise than the
// bibliography would stay green there for good.
//
// Each test here writes a build into a directory of its own: the two
// bibliographies and one guide in each language, every cited work named as the
// bibliography names it, and as many plain pages besides as a test asks for.
// Beside it go the conformance report and the pages' frontmatter the build was
// made from, which the check joins to say what the report's Dataset has to be
// based on. It puts one defect into that build, runs the check on it the way
// CI does, and reads the exit status and the lines it printed.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';
import { topicForSlug } from '../src/data/topics.mjs';
import { knownSlugs } from '../src/lib/breadcrumbs.mjs';

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-structured-data.mjs');
const ORIGIN = `${siteUrl}${basePath}`;
const EN = `${ORIGIN}/reference/bibliography/`;
const ES = `${ORIGIN}/es/reference/bibliography/`;

/** A guide the navigation tree lists, so its trail and section are the tree's. */
const GUIDE = knownSlugs().find((slug) => topicForSlug(slug)?.isDomain && slug.split('/').length === 3);

/** The platforms the software node names when a test does not say otherwise. */
const PLATFORMS = ['Linux', 'macOS', 'Windows'];

/** The library the committed report was generated for, which the report's Dataset gives as its version. */
const LIBRARY = JSON.parse(
	readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', '..', 'docs', 'conformance.json'), 'utf8'),
).library;
/** The software's DOI, which names every version of the library and no report. */
const SOFTWARE_DOI = '10.5281/zenodo.0000001';

const SITE = {
	person: `${ORIGIN}/#person`,
	website: `${ORIGIN}/#website`,
	software: `${ORIGIN}/#software`,
	source: `${ORIGIN}/#source`,
};

/**
 * The nodes astro.config.mjs puts on every page. `operatingSystem` is what the
 * software node names; null leaves the property out.
 */
const siteNodes = (operatingSystem) => [
	{ '@type': 'Person', '@id': SITE.person, name: 'A maintainer' },
	{ '@type': 'WebSite', '@id': SITE.website, name: 'phonometry' },
	{
		'@type': 'SoftwareApplication',
		'@id': SITE.software,
		name: 'phonometry',
		identifier: { '@type': 'PropertyValue', propertyID: 'DOI', value: SOFTWARE_DOI },
		...(operatingSystem === null ? {} : { operatingSystem }),
	},
	{ '@type': 'SoftwareSourceCode', '@id': SITE.source, name: 'phonometry' },
];

/**
 * The article and trail every page carries, for `slug` in `lang`, with the
 * article's own fields in `extra`. Every page is published on 2026-07-01 and
 * last edited on 2026-10-01 unless a build says otherwise.
 */
function page(slug, lang, extra = {}) {
	const prefix = lang === 'es' ? '/es' : '';
	const canonical = `${ORIGIN}${prefix}/${slug}/`;
	const topic = topicForSlug(slug);
	const parts = slug.split('/');
	const crumbs = [`${ORIGIN}${prefix}/`, ...parts.map((_, i) => `${ORIGIN}${prefix}/${parts.slice(0, i + 1).join('/')}/`)];
	const article = {
		'@type': topic?.isDomain ? ['TechArticle', 'LearningResource'] : 'TechArticle',
		'@id': `${canonical}#article`,
		headline: slug,
		description: 'A page.',
		inLanguage: lang,
		url: canonical,
		mainEntityOfPage: canonical,
		image: `${ORIGIN}/og.png`,
		speakable: { '@type': 'SpeakableSpecification', cssSelector: ['h1'] },
		datePublished: '2026-07-01',
		dateModified: '2026-10-01',
		wordCount: 100,
		...(topic ? { articleSection: topic.label[lang] } : {}),
		...(topic?.isDomain ? { learningResourceType: 'Guide' } : {}),
		[lang === 'en' ? 'workTranslation' : 'translationOfWork']: {
			'@id': `${ORIGIN}${lang === 'en' ? '/es' : ''}/${slug}/#article`,
		},
		author: { '@id': SITE.person },
		publisher: { '@id': SITE.person },
		isPartOf: { '@id': SITE.website },
		about: { '@id': SITE.software },
		...extra,
	};
	const trail = {
		'@type': 'BreadcrumbList',
		'@id': `${canonical}#breadcrumbs`,
		itemListElement: crumbs.map((item, i) => ({ '@type': 'ListItem', position: i + 1, name: `crumb ${i}`, item })),
	};
	const path = `${prefix.slice(1)}${prefix ? '/' : ''}${slug}/index.html`;
	return { path, article, nodes: [...siteNodes(PLATFORMS), article, trail] };
}

const ISO = {
	'@type': 'Organization',
	'@id': `${EN}#org-iso`,
	name: 'International Organization for Standardization',
	alternateName: 'ISO',
	url: 'https://www.iso.org/',
};
const SPAIN = { '@type': 'Organization', '@id': `${EN}#org-es-jefatura-del-estado`, name: 'Jefatura del Estado' };

/** A standard's full node on the bibliography at `url`. */
const standard = (url, designation, catalogue) => ({
	'@id': `${url}#std-${designation.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
	'@type': 'CreativeWork',
	name: `Acoustics, ${designation}`,
	url: `https://www.iso.org/standard/${catalogue}.html`,
	alternateName: designation,
	identifier: designation,
	genre: 'Technical standard',
	publisher: { '@id': ISO['@id'] },
});
const book = (url) => ({
	'@id': `${url}#doi-10-1000-book`,
	'@type': 'Book',
	name: 'A book',
	identifier: { '@type': 'PropertyValue', propertyID: 'DOI', value: '10.1000/book' },
	sameAs: 'https://doi.org/10.1000/book',
	author: [{ '@type': 'Person', name: 'Roe, R.' }],
	publisher: { '@type': 'Organization', name: 'A Press' },
});
const law = (url) => ({
	'@id': `${url}#std-ley-37-2003`,
	'@type': 'CreativeWork',
	name: 'Ley del Ruido',
	url: 'https://www.boe.es/eli/es/l/2003/11/17/37/con',
	alternateName: 'Ley 37/2003',
	identifier: 'Ley 37/2003',
	genre: 'Technical standard',
	publisher: { '@id': SPAIN['@id'] },
});

/** What a page says of a work at its first reference (citations.mjs, `STUB_FIELDS`). */
const stub = (node) =>
	Object.fromEntries(
		['@id', '@type', 'name', 'identifier', 'reportNumber', 'url', 'sameAs']
			.filter((key) => node[key] !== undefined)
			.map((key) => [key, node[key]]),
	);

/** The day the report's rows last changed, which its banner prints and its Dataset gives. */
const DATA_DAY = '2026-09-15';

/** The banner line of the report page that names the commit and the day its rows are of (Conformance.astro). */
const provenance = (day) =>
	'<p class="banner-provenance" data-report-provenance>Generated for phonometry <b data-report-library>4.0.0</b>; ' +
	'its rows last changed in commit <a href="https://github.com/jmrplens/phonometry/commit/abc"><code data-report-commit="abc">abc</code></a>, ' +
	`on <time datetime="${day}">${day}</time>.</p>`;

/** What the report's Dataset says in each language. */
const REPORT_TEXT = {
	en: { name: 'The report', description: 'Checks.', technique: 'Comparison.', column: ['Standard', 'The standard'] },
	es: { name: 'El informe', description: 'Comprobaciones.', technique: 'Comparación.', column: ['Norma', 'La norma'] },
};

/**
 * The conformance report in `lang`: an article whose main entity is the
 * Dataset of the report, generated for the committed library, dated by its
 * data before the page, written in the page's language and based on the
 * script that writes it and on the standard `work`, named as the
 * bibliography names it.
 */
function reportPage(lang, work) {
	const text = REPORT_TEXT[lang];
	const report = page('reference/conformance', lang);
	report.article.mainEntity = {
		'@type': 'Dataset',
		'@id': `${report.article.url}#dataset`,
		name: text.name,
		description: text.description,
		inLanguage: lang,
		version: LIBRARY,
		dateModified: DATA_DAY,
		license: 'https://opensource.org/license/MIT',
		measurementTechnique: text.technique,
		variableMeasured: [{ '@type': 'PropertyValue', name: text.column[0], description: text.column[1] }],
		isBasedOn: ['https://github.com/jmrplens/phonometry/blob/main/scripts/conformance_report.py', stub(work)],
	};
	report.body = provenance(DATA_DAY);
	return report;
}

/** A standard as a guide's frontmatter cites it, the one the bibliography's `standard()` node defines. */
const cited = (designation, year) => ({
	type: 'standard',
	organization: 'International Organization for Standardization',
	year,
	title: `Acoustics, ${designation}`,
	designation,
});

/**
 * What the build was made from, as far as the report's Dataset goes: the
 * conformance report, whose checks are based on the standards `documents`
 * names (each `[designation, edition]`), and the frontmatter of the guide in
 * each language, which cites ISO 1:2000 and ISO 2:2010. By default the checks
 * are based on ISO 2:2010 alone, the one work the Dataset of `build()` names.
 */
const sources = (documents = [['ISO 2', '2010']]) => ({
	report: {
		library: LIBRARY,
		domains: [{ id: 'domain', title: 'A domain' }],
		checks: documents.map(([designation, edition], i) => ({
			id: `domain/${i}`,
			domain: 'domain',
			reference: { documents: [{ kind: 'standard', designation, edition }] },
		})),
	},
	references: [cited('ISO 1:2000', 2000), cited('ISO 2:2010', 2010)],
});

/**
 * A build the check has nothing to report on: the two bibliographies, a
 * guide and the conformance report in each language, where every cited work
 * is named as the bibliography names it, then plain English pages up to
 * `pages` in all.
 *
 * The first `dated` pages, in that order, are published on `published` and the
 * rest on the day of their last edit, 2026-10-01; all of them with no `dated`.
 * `platforms` gives the software node's `operatingSystem` on each page by the
 * same index; a page past its end names the default platforms.
 */
function build({ pages = 6, dated, published = '2026-07-01', platforms = [] } = {}) {
	const built = {};
	for (const [lang, url] of [
		['en', EN],
		['es', ES],
	]) {
		const iso1 = standard(url, 'ISO 1:2000', 1);
		const iso2 = standard(url, 'ISO 2:2010', 2);
		const works = [iso1, iso2, book(url), law(url)];
		if (lang === 'es') {
			for (const work of works.filter((node) => node.genre === 'Technical standard')) {
				work.sameAs = work['@id'].replace(ES, EN);
			}
		}
		const bibliography = page('reference/bibliography', lang);
		// Copies, so a test that takes a field off a body takes it off its own build only.
		bibliography.nodes.push({ ...ISO }, { ...SPAIN }, ...works);
		built[`${lang}/bibliography`] = bibliography;

		built[`${lang}/guide`] = page(GUIDE, lang, {
			isBasedOn: [stub(iso1)],
			citation: [{ '@id': iso1['@id'] }, stub(iso2), stub(book(url))],
			about: [{ '@id': SITE.software }, { '@id': iso1['@id'] }],
		});
		built[`${lang}/report`] = reportPage(lang, iso2);
	}
	for (let i = Object.keys(built).length; i < pages; i += 1) built[`page/${i}`] = page(`page-${i}`, 'en');
	Object.values(built).forEach(({ article, nodes }, i) => {
		if (dated !== undefined && i >= dated) article.datePublished = '2026-10-01';
		else article.datePublished = published;
		if (i < platforms.length) {
			const software = nodes.find((node) => node['@type'] === 'SoftwareApplication');
			if (platforms[i] === null) delete software.operatingSystem;
			else software.operatingSystem = platforms[i];
		}
	});
	return built;
}

/** The types of the nodes astro.config.mjs writes in a block of their own on every page. */
const SITE_TYPES = new Set(['Person', 'WebSite', 'SoftwareApplication', 'SoftwareSourceCode']);

/**
 * Write `built` as HTML files, run the check on it, and say how it ended.
 *
 * Each page carries two blocks, as the built site does: the site-wide nodes
 * astro.config.mjs puts on every page, and the page's own graph from
 * Head.astro.
 */
function check(t, built, from = sources()) {
	const root = mkdtempSync(join(tmpdir(), 'check-structured-data-'));
	t.after(() => rmSync(root, { recursive: true, force: true }));
	const dist = join(root, 'dist');
	const script = (nodes) =>
		`<script type="application/ld+json">${JSON.stringify({ '@context': 'https://schema.org', '@graph': nodes })}</script>`;
	for (const { path, nodes, body = '' } of Object.values(built)) {
		const site = nodes.filter((node) => SITE_TYPES.has(node['@type']));
		const own = nodes.filter((node) => !SITE_TYPES.has(node['@type']));
		mkdirSync(dirname(join(dist, path)), { recursive: true });
		writeFileSync(
			join(dist, path),
			`<!DOCTYPE html><html><head>${script(site)}${script(own)}</head><body>${body}</body></html>`,
		);
	}
	// The report and the pages the build was made from: JSON is YAML, so the
	// frontmatter is written as JSON.
	const report = join(root, 'conformance.json');
	writeFileSync(report, JSON.stringify(from.report));
	const content = join(root, 'content');
	for (const path of ['guide.mdx', 'es/guide.mdx']) {
		mkdirSync(dirname(join(content, path)), { recursive: true });
		writeFileSync(join(content, path), `---\ntitle: A guide\nreferences: ${JSON.stringify(from.references)}\n---\n\nText.\n`);
	}
	const ran = spawnSync(process.execPath, [CHECK, dist, `--report=${report}`, `--content=${content}`], { encoding: 'utf8' });
	return { status: ran.status, out: ran.stdout, err: ran.stderr };
}

/** The node with `id` among a built page's nodes. */
const nodeAt = (built, key, id) => built[key].nodes.find((node) => node['@id'] === id);

test('a build where most pages have been edited since they were added passes', (t) => {
	const ran = check(t, build({ pages: 10, dated: 9 }));
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}9 of the 10 articles were last edited after the day they were first published/);
	assert.equal(ran.err, '');
});

test('a build where no page has two different dates fails, and says where to look', (t) => {
	const ran = check(t, build({ pages: 10, dated: 0 }));
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 0 of the 10 articles were last edited after the day they were first published/);
	assert.match(ran.err, /page-dates\.mjs/);
});

test('a page published after its last edit does not count as edited', (t) => {
	const ran = check(t, build({ pages: 10, published: '2026-11-01' }));
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 0 of the 10 articles were last edited after the day they were first published/);
});

test('a tenth of the pages is the floor: one under it fails and one on it passes', (t) => {
	assert.equal(check(t, build({ pages: 11, dated: 1 })).status, 1);
	assert.equal(check(t, build({ pages: 10, dated: 1 })).status, 0);
});

test('a software node that names its operating systems one per entry passes, and says on how many pages', (t) => {
	const ran = check(t, build({ pages: 10, dated: 9 }));
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}the software node names its 3 operating systems one per entry on 10 pages/);
});

test('a software node that joins its operating systems into one string fails, and names the value', (t) => {
	const ran = check(t, build({ pages: 10, platforms: Array(10).fill('Windows, Linux, macOS') }));
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 10 page\(s\): the software node's operatingSystem is "Windows, Linux, macOS"/);
	assert.match(ran.err, /jmrp\.io/);
});

test('one entry that holds two platforms fails as the joined string does', (t) => {
	const ran = check(t, build({ pages: 10, platforms: Array(10).fill(['Linux', 'macOS, Windows']) }));
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 10 page\(s\): the software node's operatingSystem is \["Linux","macOS, Windows"\]/);
});

test('a software node that names no operating system, or one twice, fails', (t) => {
	const ran = check(t, build({ pages: 10, platforms: [null, [], ['Linux', 'Linux']] }));
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 1 page\(s\): the software node's operatingSystem is null/);
	assert.match(ran.err, /FAIL 1 page\(s\): the software node's operatingSystem is \[\]/);
	assert.match(ran.err, /FAIL 1 page\(s\): the software node's operatingSystem is \["Linux","Linux"\]/);
	assert.match(ran.out, /ok {3}the software node names its 3 operating systems one per entry on 7 pages/);
});

test('the fixture names a guide the navigation tree lists', () => {
	assert.ok(GUIDE, 'no three-segment guide under a domain topic in src/data/topics.mjs');
});

test('a build where every cited work is named, and named as the bibliography names it, passes', (t) => {
	const ran = check(t, build());
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}every one of the 2 works pages are based on is named at its first reference in isBasedOn/);
	assert.match(ran.out, /ok {3}each of the 8 stubs that name a work on a page says what the bibliography says of it/);
	assert.match(ran.out, /each of the 3 Spanish standards names the English node it is/);
	assert.match(ran.out, /\n0 failing check\(s\)\./);
});

test('a first reference in isBasedOn that is a bare @id fails', (t) => {
	const built = build();
	built['en/guide'].article.isBasedOn = [{ '@id': `${EN}#std-iso-1-2000` }];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 1 page\(s\) give 1 work\(s\) they are based on as a bare @id/);
});

test('a cited work that nothing on the page names fails', (t) => {
	const built = build();
	built['es/guide'].article.citation[2] = { '@id': `${ES}#doi-10-1000-book` };
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 1 page\(s\) point at 1 cited work\(s\) that nothing on the page names/);
});

test('a stub typed as something other than a work names nothing', (t) => {
	const built = build();
	built['en/guide'].article.citation[2]['@type'] = 'Organization';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 1 page\(s\) point at 1 cited work\(s\) that nothing on the page names/);
	assert.match(ran.err, /FAIL 1 work\(s\) are named on 1 page\(s\) other than as the bibliography defines them: @type on 1/);
});

test('a page that names a work otherwise than the bibliography fails, field by field', (t) => {
	const built = build();
	// Another catalogue address for the standard, and another book's title.
	built['en/guide'].article.isBasedOn[0].url = 'https://www.iso.org/standard/9.html';
	built['es/guide'].article.citation[2].name = 'Another book';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL 2 work\(s\) are named on 2 page\(s\) other than as the bibliography defines them: name on 1, url on 1/,
	);
});

test('a stub claiming a sameAs the bibliography does not give fails', (t) => {
	const built = build();
	built['en/guide'].article.citation[2].sameAs = 'https://doi.org/10.1000/another';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /other than as the bibliography defines them: sameAs on 1/);
});

test('a standard whose publisher has no identity of its own fails, anonymous or off the bibliography', (t) => {
	const anonymous = build();
	nodeAt(anonymous, 'en/bibliography', `${EN}#std-iso-2-2010`).publisher = {
		'@type': 'Organization',
		name: 'International Organization for Standardization',
	};
	let ran = check(t, anonymous);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/reference\/bibliography\/: 1 of 3 standards name a publisher with no identity of its own under .*#org-: International Organization for Standardization \(1\)/,
	);

	const elsewhere = build();
	nodeAt(elsewhere, 'es/bibliography', `${ES}#std-iso-2-2010`).publisher = { '@id': 'https://example.org/#iso' };
	ran = check(t, elsewhere);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/es\/reference\/bibliography\/: 1 of 3 standards name a publisher with no identity/);
});

test('a standards body without its official site fails, and only the Spanish state issuers go without', (t) => {
	const built = build();
	delete nodeAt(built, 'en/bibliography', ISO['@id']).url;
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/reference\/bibliography\/: 1 of the bodies its standards name carry no https url[^\n]*: iso/);
	// The Spanish state issuer carries no url in every build here, and passes.
	assert.doesNotMatch(ran.err, /es-jefatura-del-estado/);
});

test('a Spanish standard that names no English one, a missing one or another one fails', (t) => {
	const untied = build();
	delete nodeAt(untied, 'es/bibliography', `${ES}#std-iso-2-2010`).sameAs;
	let ran = check(t, untied);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/es\/reference\/bibliography\/: 1 of 3 standards name no English node as the same work \(first: ISO 2:2010\)/);

	const dangling = build();
	nodeAt(dangling, 'es/bibliography', `${ES}#std-iso-2-2010`).sameAs = `${EN}#std-iso-2-2099`;
	ran = check(t, dangling);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/es\/reference\/bibliography\/: 1 sameAs point at English standards \/reference\/bibliography\/ does not define/);

	// A real English node, but another standard: ISO 2:2010 is not ISO 1:2000.
	const wrong = build();
	nodeAt(wrong, 'es/bibliography', `${ES}#std-iso-2-2010`).sameAs = `${EN}#std-iso-1-2000`;
	ran = check(t, wrong);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/es\/reference\/bibliography\/: 1 standards name as the same work an English standard whose designation carries other numbers \(first: ISO 2:2010 as ISO 1:2000\)/,
	);
});

test('a build where no page says what it is based on fails rather than passing on nothing', (t) => {
	const built = build();
	for (const key of ['en/guide', 'es/guide']) {
		const { article } = built[key];
		article.citation[0] = article.isBasedOn[0];
		delete article.isBasedOn;
	}
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL no page says what it is based on: the citation properties changed under this check/);
});

test('a bibliography that defines no standard fails rather than passing on nothing', (t) => {
	const built = build();
	for (const node of built['es/bibliography'].nodes) delete node.genre;
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL the bibliography defines 3 standards in English and 0 in Spanish/);
});

test('a build where no page names a cited work fails rather than passing on nothing', (t) => {
	const built = build();
	for (const key of ['en/guide', 'es/guide']) {
		const { article } = built[key];
		delete article.isBasedOn;
		delete article.citation;
		article.about = { '@id': SITE.software };
	}
	for (const key of ['en/report', 'es/report']) built[key].article.mainEntity.isBasedOn.pop();
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL no page names a cited work: the citation markup changed under this check/);
});

test('the site-wide block within its byte budget passes, and says its size and how much of it the Person is', (t) => {
	const ran = check(t, build());
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}the site-wide ld\+json block is \d+ bytes on 6 pages, within its budget of \d+; the Person is \d+ of them/);
});

test('a site-wide block over its byte budget fails, and says how much of it the Person is', (t) => {
	// A Person spliced from jmrp.io with every link listed twice over: the
	// growth no page of this repository shows in a diff.
	const built = build();
	const links = Array.from({ length: 600 }, (_, i) => `https://example.org/profiles/maintainer-${i}`);
	for (const { nodes } of Object.values(built)) {
		nodes.find((node) => node['@type'] === 'Person').sameAs = links;
	}
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL 6 page\(s\): the site-wide ld\+json block is \d+ bytes, over its budget of \d+; the Person spliced from jmrp\.io is \d+ of them/,
	);
});

test('a build with no site-wide block fails rather than passing the budget on nothing', (t) => {
	const built = build();
	for (const entry of Object.values(built)) entry.nodes = entry.nodes.filter((node) => node['@type'] !== 'Person');
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL no page carries the site-wide ld\+json block/);
});

test('a report whose Dataset is its main entity, versioned, dated by its data, based on named standards and written in each language passes', (t) => {
	const ran = check(t, build());
	assert.equal(ran.status, 0, ran.err);
	assert.match(
		ran.out,
		new RegExp(
			`ok {3}the conformance report's Dataset is the main entity of both report pages, versioned ${LIBRARY.replace(/\./g, '\\.')}, ` +
				'dated by the day its rows last changed, based on the 1 work its checks are based on in each language, named, ' +
				'and written in each page\'s language \\(5 texts\\)',
		),
	);
});

test('a report whose Dataset is a block of its own, beside the article and not its main entity, fails', (t) => {
	const built = build();
	for (const key of ['en/report', 'es/report']) {
		const { article, nodes } = built[key];
		nodes.push(article.mainEntity);
		delete article.mainEntity;
	}
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/reference\/conformance\/: the conformance report's Dataset: the article has no Dataset as its mainEntity/);
	assert.match(ran.err, /FAIL \/es\/reference\/conformance\/: the conformance report's Dataset: the article has no Dataset as its mainEntity/);
});

test('a report that keeps a Dataset of its own beside the one that is its main entity fails', (t) => {
	const built = build();
	const { article, nodes } = built['es/report'];
	nodes.push({ ...article.mainEntity });
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/es\/reference\/conformance\/: the conformance report's Dataset: a Dataset of its own beside the article, which says what the report is a second time/,
	);
	assert.doesNotMatch(ran.err, /FAIL \/reference\/conformance\//);
});

test("a report Dataset that gives the software's DOI as its own identifier fails", (t) => {
	const built = build();
	built['en/report'].article.mainEntity.identifier = { '@type': 'PropertyValue', propertyID: 'DOI', value: SOFTWARE_DOI };
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, new RegExp(`FAIL /reference/conformance/: the conformance report's Dataset: it gives the software's DOI ${SOFTWARE_DOI.replace(/\./g, '\\.')} as its own identifier`));
});

test('a report Dataset with no version, another one, or no day its data changed fails', (t) => {
	const built = build();
	delete built['en/report'].article.mainEntity.version;
	built['es/report'].article.mainEntity.version = '0.0.1';
	delete built['es/report'].article.mainEntity.dateModified;
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/reference\/conformance\/: the conformance report's Dataset: its version is undefined, and docs\/conformance\.json was generated for /);
	assert.match(ran.err, /FAIL \/es\/reference\/conformance\/: the conformance report's Dataset: its version is "0\.0\.1"/);
	assert.match(ran.err, /FAIL \/es\/reference\/conformance\/: the conformance report's Dataset: its dateModified is undefined, not a day/);
});

test('a report Dataset whose data changed after the page did fails', (t) => {
	const built = build();
	built['en/report'].article.mainEntity.dateModified = '2026-10-02';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/reference\/conformance\/: the conformance report's Dataset: its data changed on 2026-10-02, after the page's own last change, 2026-10-01/);
});

test('a report Dataset based on its script alone, or on a work it does not name, fails', (t) => {
	const built = build();
	built['en/report'].article.mainEntity.isBasedOn = ['https://github.com/jmrplens/phonometry/blob/main/scripts/conformance_report.py'];
	built['es/report'].article.mainEntity.isBasedOn.push({ '@id': `${ES}#std-iso-1-2000` });
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/reference\/conformance\/: the conformance report's Dataset: it names no standard it is based on/);
	assert.match(ran.err, /FAIL \/es\/reference\/conformance\/: the conformance report's Dataset: 1 of what it is based on is not a work the bibliography defines, named/);
});

test('a Spanish report Dataset that says in English what the English one says fails, text by text', (t) => {
	const built = build();
	const spanish = built['es/report'].article.mainEntity;
	spanish.name = REPORT_TEXT.en.name;
	spanish.variableMeasured[0].description = REPORT_TEXT.en.column[1];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/es\/reference\/conformance\/: the conformance report's Dataset says in English what the English page says: name, variableMeasured\[0\]\.description/,
	);
});

test('a build with no conformance report fails rather than passing on nothing', (t) => {
	const built = build();
	delete built['en/report'];
	delete built['es/report'];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL no page at \/reference\/conformance\/ was found: build the site first/);
});

test('a report Dataset that leaves out a work its checks are based on fails, and names it', (t) => {
	// The checks are based on ISO 1:2000 and ISO 2:2010, and the Dataset of
	// either page names ISO 2:2010 alone.
	const ran = check(t, build(), sources([['ISO 1', '2000'], ['ISO 2', '2010']]));
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/reference\/conformance\/: the conformance report's Dataset: it leaves out 1 of the 2 works its checks are based on: #std-iso-1-2000/,
	);
	assert.match(ran.err, /FAIL \/es\/reference\/conformance\/: the conformance report's Dataset: it leaves out 1 of the 2 works/);
});

test('a report Dataset that names a work no check is based on fails, and names it', (t) => {
	const built = build();
	built['en/report'].article.mainEntity.isBasedOn.push(stub(standard(EN, 'ISO 1:2000', 1)));
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/reference\/conformance\/: the conformance report's Dataset: it names 1 work no check is based on: #std-iso-1-2000/,
	);
	assert.doesNotMatch(ran.err, /FAIL \/es\/reference\/conformance\//);
});

test('report Datasets that name a different number of works in the two languages fail', (t) => {
	const built = build();
	for (const [key, url] of [['en/report', EN], ['es/report', ES]]) {
		const iso1 = standard(url, 'ISO 1:2000', 1);
		if (key === 'es/report') iso1.sameAs = iso1['@id'].replace(ES, EN);
		if (key === 'en/report') built[key].article.mainEntity.isBasedOn.push(stub(iso1));
	}
	const ran = check(t, built, sources([['ISO 1', '2000'], ['ISO 2', '2010']]));
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL the conformance report's Dataset names 2 works in English and 1 in Spanish/);
});

test('a report Dataset dated by the page and not by the day its rows last changed fails', (t) => {
	const built = build();
	// The page's own date, 2026-10-01, the variant that would date the data by
	// a change to how the rows are drawn.
	built['en/report'].article.mainEntity.dateModified = '2026-10-01';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/reference\/conformance\/: the conformance report's Dataset: its dateModified is 2026-10-01, and the page says its rows last changed on 2026-09-15/,
	);
	assert.doesNotMatch(ran.err, /FAIL \/es\/reference\/conformance\//);
});

test('a report page that prints no day its rows last changed fails', (t) => {
	const built = build();
	built['es/report'].body = '';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/es\/reference\/conformance\/: the conformance report's Dataset: the page prints no day its rows last changed \(\[data-report-provenance\] with a <time datetime>\)/,
	);
});
