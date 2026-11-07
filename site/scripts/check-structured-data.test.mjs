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
// A malformed block takes out its own nodes and no others: the software node
// and the `@id`s of the page's valid blocks are still read, as a consumer reads
// them, so the count names every page that carries a value. A block that parses
// to `null`, an array or a bare value is read the same way, and does not stop
// the check.
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
// It puts one defect into that build, runs the check on it the way CI does, and
// reads the exit status and the lines it printed. The pages, the site-wide
// nodes and the writing of the build come from
// shared/structured-data-fixture.mjs, which every suite of the check shares.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { topicForSlug } from '../src/data/topics.mjs';
import { knownSlugs } from '../src/lib/breadcrumbs.mjs';
import { build as wholeBuild, check, ORIGIN, page, SITE } from './shared/structured-data-fixture.mjs';

const EN = `${ORIGIN}/reference/bibliography/`;
const ES = `${ORIGIN}/es/reference/bibliography/`;

/** A guide the navigation tree lists, so its trail and section are the tree's. */
const GUIDE = knownSlugs().find((slug) => topicForSlug(slug)?.isDomain && slug.split('/').length === 3);

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

/**
 * A build the check has nothing to report on: the two bibliographies and a
 * guide in each language, where every cited work is named as the bibliography
 * names it, then plain English pages up to `pages` in all.
 *
 * The first `dated` pages, in that order, are published on `published` and the
 * rest on the day of their last edit, 2026-10-01. `platforms` gives the
 * software node's `operatingSystem` on each page by the same index; a page
 * past its end names the default platforms.
 */
function build({ pages = 4, ...options } = {}) {
	const base = {};
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
		base[`${lang}/bibliography`] = bibliography;

		base[`${lang}/guide`] = page(GUIDE, lang, {
			isBasedOn: [stub(iso1)],
			citation: [{ '@id': iso1['@id'] }, stub(iso2), stub(book(url))],
			about: [{ '@id': SITE.software }, { '@id': iso1['@id'] }],
		});
	}
	return wholeBuild({ pages, ...options, base });
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

test('a malformed block on a page leaves the software node of its valid block counted', (t) => {
	const built = build({ pages: 10, dated: 9, platforms: Array(10).fill('Windows, Linux, macOS') });
	built['page/4'].blocks = ['{"@context": '];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/page-4\/: an ld\+json block is not valid JSON/);
	assert.match(ran.err, /FAIL 10 page\(s\): the software node's operatingSystem is "Windows, Linux, macOS"/);
});

test('a block that parses to no JSON-LD object is reported as one that does not parse', (t) => {
	// `null` parses, and reading its @context threw, so the check stopped before
	// it reported the page or tallied any software node.
	const built = build({ pages: 10, dated: 9, platforms: Array(10).fill('Windows, Linux, macOS') });
	built['page/4'].blocks = ['null'];
	built['page/5'].blocks = ['[]'];
	built['page/6'].blocks = ['5'];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	for (const page of [4, 5, 6]) {
		assert.match(ran.err, new RegExp(`FAIL /page-${page}/: an ld\\+json block is not a JSON-LD object`));
	}
	assert.match(ran.err, /FAIL 10 page\(s\): the software node's operatingSystem is "Windows, Linux, macOS"/);
	assert.doesNotMatch(ran.err, /TypeError/);
});

test('a malformed block on a page leaves two nodes of its valid blocks that share an @id reported', (t) => {
	const twin = { '@context': 'https://schema.org', '@type': 'Thing', '@id': `${ORIGIN}/#thing` };
	const built = build({ pages: 10, dated: 9 });
	built['page/4'].blocks = [twin, twin, '{'];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/page-4\/: an ld\+json block is not valid JSON/);
	assert.match(ran.err, /FAIL \/page-4\/: .*\/#thing defined more than once/);
});

test('the fixture names a guide the navigation tree lists', () => {
	assert.ok(GUIDE, 'no three-segment guide under a domain topic in src/data/topics.mjs');
});

test('a build where every cited work is named, and named as the bibliography names it, passes', (t) => {
	const ran = check(t, build());
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}every one of the 2 works pages are based on is named at its first reference in isBasedOn/);
	assert.match(ran.out, /ok {3}each of the 6 stubs that name a work on a page says what the bibliography says of it/);
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

test("a work described in a catalogue page's words about its own rows fails, in either language", (t) => {
	const built = build();
	const id = (url) => book(url)['@id'];
	nodeAt(built, 'en/bibliography', id(EN)).description = 'Table 4.1: the source of the rows of this catalogue that cite it.';
	nodeAt(built, 'es/bibliography', id(ES)).description = 'Tabla 4.1: fuente de las filas de este catálogo que la citan.';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	for (const route of ['/reference/bibliography/', '/es/reference/bibliography/']) {
		assert.match(
			ran.err,
			new RegExp(`FAIL ${route}: 1 of the 1 works it describes take the words of a catalogue page about its own rows: #doi-10-1000-book`),
		);
	}

	// Named, the catalogue is a fact about the work wherever it is read.
	const named = build();
	nodeAt(named, 'en/bibliography', id(EN)).description = 'Table 4.1: the source of the rows of the catalogue of solids that cite it.';
	nodeAt(named, 'es/bibliography', id(ES)).description = 'Tabla 4.1: fuente de las filas del catálogo de sólidos que la citan.';
	const passed = check(t, named);
	assert.equal(passed.status, 0, passed.err);
	assert.match(passed.out, /ok {3}\/es\/reference\/bibliography\/: none of the 1 works it describes is described as one catalogue page's rows/);
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
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL no page names a cited work: the citation markup changed under this check/);
});

test('the site-wide block within its byte budget passes, and says its size and how much of it the Person is', (t) => {
	const ran = check(t, build());
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}the site-wide ld\+json block is \d+ bytes on 4 pages, within its budget of \d+; the Person is \d+ of them/);
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
		/FAIL 4 page\(s\): the site-wide ld\+json block is \d+ bytes, over its budget of \d+; the Person spliced from jmrp\.io is \d+ of them/,
	);
});

test('a build with no site-wide block fails rather than passing the budget on nothing', (t) => {
	const built = build();
	for (const entry of Object.values(built)) entry.nodes = entry.nodes.filter((node) => node['@type'] !== 'Person');
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL no page carries the site-wide ld\+json block/);
});
