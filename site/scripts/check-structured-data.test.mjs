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
import { catalogues } from '../src/generated/catalogues.mjs';
import { knownSlugs } from '../src/lib/breadcrumbs.mjs';
import { variablesMeasured } from '../src/lib/catalogue-datasets.mjs';
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

// ---------------------------------------------------------------------------
// The catalogues as datasets
// ---------------------------------------------------------------------------

/** The catalogue page every dataset of the fixture sits on: one page may hold several. */
const CATALOGUE_PAGE = 'reference/catalogues/solids';

/**
 * A build whose every catalogue is a Dataset of a catalogue page in each
 * language, listed by that language's overview: the pages of `build()` and,
 * per language, the overview and one catalogue page that holds all the
 * datasets with a table for each.
 *
 * @param {{pageSlug?: string, overviewSlug?: string}} [at] Where the catalogue
 *   page and the overview sit, which a test moves to a route topics.mjs does
 *   not list.
 */
function catalogueBuild({ pageSlug = CATALOGUE_PAGE, overviewSlug = 'reference/catalogues' } = {}) {
	const built = build();
	for (const [lang, url] of [
		['en', EN],
		['es', ES],
	]) {
		const prefix = lang === 'es' ? '/es' : '';
		const twin = lang === 'es' ? '' : '/es';
		const pageUrl = `${ORIGIN}${prefix}/${pageSlug}/`;
		const overviewUrl = `${ORIGIN}${prefix}/${overviewSlug}/`;
		const datasets = Object.keys(catalogues).map((key) => ({
			'@type': 'Dataset',
			'@id': `${pageUrl}#dataset-${key}`,
			name: `Catalogue ${key}`,
			description: `The rows of ${key}.`,
			url: `${pageUrl}#catalogue-${key}`,
			inLanguage: lang,
			includedInDataCatalog: { '@type': 'DataCatalog', '@id': `${overviewUrl}#article`, name: 'Catalogues', url: overviewUrl },
			[lang === 'en' ? 'workTranslation' : 'translationOfWork']: {
				'@id': `${ORIGIN}${twin}/${pageSlug}/#dataset-${key}`,
			},
			variableMeasured: variablesMeasured(catalogues[key].columns, lang),
			isBasedOn: [stub(book(url))],
			// The day page() says the page was last edited.
			dateModified: '2026-10-01',
		}));
		const catalogue = page(pageSlug, lang, {
			mainEntity: datasets.map((node) => ({ '@id': node['@id'] })),
			citation: [stub(book(url))],
		});
		catalogue.nodes.push(...datasets);
		// The page shows what its datasets say: the first is named by its
		// title, every later one by the heading of its section, and each is
		// described by the paragraph above its table.
		catalogue.text =
			`<h1 id="_top">${datasets[0].name}</h1>` +
			datasets
				.map(
					(node, i) =>
						`${i > 0 ? `<h2 id="h-${i}">${node.name}</h2>` : ''}<p>${node.description}</p>` +
						`<section id="${node.url.split('#')[1]}"></section>`,
				)
				.join('');
		built[`${lang}/catalogue`] = catalogue;
		built[`${lang}/overview`] = page(overviewSlug, lang, {
			'@type': ['TechArticle', 'DataCatalog'],
			name: 'Catalogues',
			dataset: datasets.map((node) => ({ '@type': 'Dataset', '@id': node['@id'], name: node.name, url: node.url })),
		});
	}
	return built;
}

/** The dataset of `key` on the catalogue page of `lang`. */
const datasetOf = (built, lang, key) =>
	built[`${lang}/catalogue`].nodes.find((node) => node['@id']?.endsWith(`#dataset-${key}`));

test('a build whose every catalogue is a dataset of its page, listed by the overview, passes', (t) => {
	const ran = check(t, catalogueBuild());
	assert.equal(ran.status, 0, ran.err);
	const count = Object.keys(catalogues).length;
	assert.match(ran.out, new RegExp(`ok {3}each of the ${count} catalogues is a Dataset of one en catalogue page`));
	assert.match(ran.out, new RegExp(`the DataCatalog lists the ${count} datasets of its language`));
	assert.match(ran.out, new RegExp(`each of the ${count * 2} datasets names its twin in the other language`));
	assert.match(ran.out, new RegExp(`each of the ${count * 2} datasets is dated as the page that renders it`));
	assert.match(
		ran.out,
		new RegExp(`each of the ${count * 2} datasets is named by a heading of its page and described by a paragraph of it`),
	);
});

test('a catalogue page that publishes no Dataset fails, and so does the count', (t) => {
	const built = catalogueBuild();
	const catalogue = built['es/catalogue'];
	catalogue.nodes = catalogue.nodes.filter((node) => node['@type'] !== 'Dataset');
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/es\/reference\/catalogues\/solids\/: a catalogue page publishes no Dataset/);
	assert.match(ran.err, /FAIL the es catalogue pages publish 0 of the 24 catalogues as a Dataset; none is solids/);
});

test('a dataset that claims a licence or a download over the rows fails', (t) => {
	const built = catalogueBuild();
	datasetOf(built, 'en', 'carpets').license = 'https://creativecommons.org/licenses/by/4.0/';
	datasetOf(built, 'es', 'solids').contentUrl = 'https://example.org/solids.json';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /solids\/ carpets: the dataset claims license over rows other works printed/);
	assert.match(ran.err, /solids\/ solids: the dataset claims contentUrl over rows other works printed/);
});

test('a dataset whose source is a bare @id, or that names none, fails', (t) => {
	const built = catalogueBuild();
	datasetOf(built, 'en', 'gases').isBasedOn = [{ '@id': stub(book(EN))['@id'] }];
	delete datasetOf(built, 'en', 'fluids').isBasedOn;
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /gases: the dataset is based on \S+#doi-10-1000-book without naming it/);
	assert.match(ran.err, /fluids: the dataset names no work it is based on/);
});

test('a dataset that names its band columns by their band, or leaves a column out, fails', (t) => {
	const built = catalogueBuild();
	datasetOf(built, 'en', 'absorption').variableMeasured = catalogues.absorption.columns.map((column) => ({
		'@type': 'PropertyValue',
		name: column.heading,
	}));
	datasetOf(built, 'es', 'solids').variableMeasured.splice(0, 1);
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /absorption: the dataset's variableMeasured names no variable for Absorption coefficient/);
	assert.match(ran.err, /absorption: variables named by a band alone: 63 Hz, 125 Hz/);
	assert.match(ran.err, /solids: the dataset's variableMeasured names no variable for Densidad/);
});

test('a dataset with no date, or another date than its page, fails', (t) => {
	const built = catalogueBuild();
	delete datasetOf(built, 'en', 'gases').dateModified;
	// The rows changed after the page last did, and the page was never told.
	datasetOf(built, 'es', 'fluids').dateModified = '2026-10-29';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /solids\/ gases: the dataset's dateModified is undefined, not its page's "2026-10-01"/);
	assert.match(ran.err, /solids\/ fluids: the dataset's dateModified is "2026-10-29", not its page's "2026-10-01"/);
	assert.doesNotMatch(ran.out, /datasets is dated as the page that renders it/);
});

test('a dataset whose url points at no table on its page fails', (t) => {
	const built = catalogueBuild();
	const catalogue = built['en/catalogue'];
	catalogue.text = catalogue.text.replace('<section id="catalogue-plateau"></section>', '');
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /plateau: the dataset's url points at #catalogue-plateau, and the page holds no such table/);
});

test('an overview that is not a DataCatalog, or lists other datasets than the pages publish, fails', (t) => {
	const built = catalogueBuild();
	const english = built['en/overview'].article;
	english['@type'] = 'TechArticle';
	english.dataset.pop();
	built['es/overview'].article.dataset[0].name = 'Otro nombre';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /\/reference\/catalogues\/: the overview of the catalogues is typed "TechArticle", not a DataCatalog/);
	assert.match(ran.err, /\/reference\/catalogues\/: the DataCatalog leaves out 1, lists 0 no catalogue page publishes/);
	assert.match(ran.err, /\/es\/reference\/catalogues\/: the DataCatalog leaves out 0, lists 0 no catalogue page publishes and names 1/);
});

test("an article whose mainEntity is not its page's datasets fails", (t) => {
	const built = catalogueBuild();
	built['en/catalogue'].article.mainEntity.pop();
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /\/reference\/catalogues\/solids\/: the article's mainEntity is /);
});

test("a dataset that takes the page's description on a page of several catalogues fails", (t) => {
	const built = catalogueBuild();
	// The page's description speaks of every catalogue the page renders.
	datasetOf(built, 'en', 'absorption').description = built['en/catalogue'].article.description;
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/\/reference\/catalogues\/solids\/ absorption: the dataset takes the page's description, which speaks of all 24 catalogues it renders/,
	);
});

test('a dataset whose name is no heading of its page, or whose description no paragraph of it, fails', (t) => {
	const built = catalogueBuild();
	// What a reader of the page's source took for text, and the page shows otherwise.
	datasetOf(built, 'en', 'gases').description = 'The rows of \\*gases\\*.';
	datasetOf(built, 'es', 'fluids').name = 'Catalogue <abbr>fluids</abbr>';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/reference\/catalogues\/solids\/ gases: the dataset's description is no paragraph of its page: "The rows of \\\\\*gases\\\\\*\."/);
	assert.match(ran.err, /FAIL \/es\/reference\/catalogues\/solids\/ fluids: the dataset's name, "Catalogue <abbr>fluids<\/abbr>", is no heading of its page/);
	assert.doesNotMatch(ran.out, /datasets is named by a heading of its page/);
});

/** An aside as the site renders one, `:::note[title]` or `<Aside title>` alike, holding one paragraph. */
const renderedAside = (title, paragraph) =>
	`<aside aria-label="${title}" class="starlight-aside starlight-aside--note">` +
	`<p class="starlight-aside__title" aria-hidden="true">${title}</p>` +
	`<div class="starlight-aside__content"><p>${paragraph}</p></div></aside>`;

test('a dataset described by the lines of an admonition, its markers with them, fails', (t) => {
	const built = catalogueBuild();
	const catalogue = built['en/catalogue'];
	catalogue.text = catalogue.text.replace(
		'<p>The rows of gases.</p>',
		`<p>The rows of gases.</p>${renderedAside('Where the rows come from', 'The book prints them in three parts.')}`,
	);
	// What a reader makes of `:::note[...]`, its paragraph and `:::` when it
	// takes the lines of the admonition for a paragraph.
	datasetOf(built, 'en', 'gases').description = ':::note[Where the rows come from] The book prints them in three parts. :::';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/reference\/catalogues\/solids\/ gases: the dataset's description is no paragraph of its page: ":::note\[Where/);
});

test("a dataset described by the paragraph an aside holds passes: keeping it out is the page reader's part", (t) => {
	const built = catalogueBuild();
	const catalogue = built['en/catalogue'];
	catalogue.text = catalogue.text.replace(
		'<p>The rows of gases.</p>',
		`<p>The rows of gases.</p>${renderedAside('Where the rows come from', 'The book prints them in three parts.')}`,
	);
	// What a reader makes of `<Aside title="...">`, its paragraph and
	// `</Aside>`: the component's tags are markup it drops.
	datasetOf(built, 'en', 'gases').description = 'The book prints them in three parts.';
	const ran = check(t, built);
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /datasets is named by a heading of its page and described by a paragraph of it/);
});

test("a dataset's text is what its page shows, with the typographer's quotes and the page's character references read back", (t) => {
	const built = catalogueBuild();
	datasetOf(built, 'en', 'gases').description = 'The book\'s rows of gases & "air", in three parts...';
	const catalogue = built['en/catalogue'];
	catalogue.text = catalogue.text.replace(
		'<p>The rows of gases.</p>',
		'<p>The book\u2019s rows of\n<em>gases</em> &#x26; \u201cair\u201d, in three parts\u2026</p>',
	);
	const ran = check(t, built);
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /datasets is named by a heading of its page and described by a paragraph of it/);
});

test('catalogue pages and an overview at a route topics.mjs does not list fail, rather than leave nothing to check', (t) => {
	// The catalogue routes moved, and nothing told the check: every dataset
	// assertion above would read no page, and the count after them none.
	const ran = check(t, catalogueBuild({ pageSlug: 'reference/tables/solids', overviewSlug: 'reference/tables' }));
	assert.equal(ran.status, 1);
	const count = Object.keys(catalogues).length;
	for (const prefix of ['', '/es']) {
		assert.match(
			ran.err,
			new RegExp(
				`FAIL ${prefix}/reference/tables/solids/: publishes ${count} catalogue dataset\\(s\\) and holds ${count} catalogue ` +
					'table\\(s\\) .*and is not a catalogue page of catalogueSlugs',
			),
		);
		assert.match(ran.err, new RegExp(`FAIL ${prefix}/reference/tables/: publishes a DataCatalog, and is not the overview`));
	}
});

// ---------------------------------------------------------------------------
// The errata pages and the works they correct
// ---------------------------------------------------------------------------

/** The family page of the fixture, the one page under the errata index that corrects a work. */
const ERRATA_FAMILY = 'reference/errata/iso-1';

/** A page of the content tree as scripts/generate_site_reports.py writes it, with what it corrects. */
const errataSource = (title, corrects = []) =>
	`---\ntitle: "${title}"\n${corrects.length > 0 ? `corrects:\n${corrects.map((fragment) => `  - "${fragment}"\n`).join('')}` : ''}---\n\nThe page.\n`;

/** The `about` of an errata family page in `lang` naming `fragments` of its bibliography, as the build writes it. */
const aboutNaming = (built, lang, fragments) => {
	const url = lang === 'es' ? ES : EN;
	return [{ '@id': SITE.software }, ...fragments.map((fragment) => stub(nodeAt(built, `${lang}/bibliography`, `${url}#${fragment}`)))];
};

/**
 * A build with the errata registry in both languages: the pages of `build()`
 * and, per language, the registry's index, one family page whose `about` names
 * the standard it corrects beside the software, and the page of properties
 * that are not errata, which corrects nothing; and the content tree the three
 * are built from, the family page's `corrects` listing that standard.
 */
function errataBuild() {
	const built = build();
	built.content = {};
	for (const lang of ['en', 'es']) {
		const prefix = lang === 'es' ? 'es/' : '';
		for (const slug of ['reference/errata', ERRATA_FAMILY, 'reference/errata/not-errata']) {
			built[`${lang}/${slug}`] = page(slug, lang, {
				about: slug === ERRATA_FAMILY ? aboutNaming(built, lang, ['std-iso-1-2000']) : { '@id': SITE.software },
			});
		}
		built.content[`${prefix}reference/errata/index.mdx`] = errataSource('Errata');
		built.content[`${prefix}${ERRATA_FAMILY}.md`] = errataSource('Errata in ISO 1', ['std-iso-1-2000']);
		built.content[`${prefix}reference/errata/not-errata.md`] = errataSource('Not errata');
	}
	return built;
}

/** Take the errata pages of `lang` out of `built`, but those at `keep`. */
const unbuildErrata = (built, lang, keep = []) => {
	for (const key of Object.keys(built)) {
		const slug = key.slice(lang.length + 1);
		if (key.startsWith(`${lang}/reference/errata`) && !keep.includes(slug)) delete built[key];
	}
};

test('a build whose every errata family page names the work it corrects passes', (t) => {
	const ran = check(t, errataBuild());
	assert.equal(ran.status, 0, ran.err);
	assert.match(
		ran.out,
		/ok {3}each of the 2 errata family pages names in about, in order, the works its corrects lists, 2 in all/,
	);
});

test('an errata family page naming fewer works than its corrects lists fails', (t) => {
	// What a regression that keeps the first work of each page builds: every
	// page still names a work, and the six editions of ISO 12354 come to one.
	const built = errataBuild();
	built.content[`${ERRATA_FAMILY}.md`] = errataSource('Errata in ISO 1', ['std-iso-1-2000', 'std-iso-2-2010']);
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		new RegExp(
			'FAIL 1 errata page\\(s\\) name in about other works than their corrects lists, or in another order ' +
				`\\(first: /reference/errata/iso-1/ names 1 work\\(s\\) and its corrects lists 2; at position 2 it names nothing ` +
				`where corrects lists ${RegExp.escape(EN)}#std-iso-2-2010\\)`,
		),
	);
	assert.match(ran.err, /FAIL the en errata family pages name 1 work\(s\) in about, and their corrects list 2/);
});

test('an errata family page naming its works in another order, or one its corrects does not list, fails', (t) => {
	const built = errataBuild();
	built.content[`es/${ERRATA_FAMILY}.md`] = errataSource('Errata en ISO 1', ['std-iso-2-2010', 'std-iso-1-2000']);
	built[`es/${ERRATA_FAMILY}`].article.about = aboutNaming(built, 'es', ['std-iso-1-2000', 'std-iso-2-2010']);
	built[`en/${ERRATA_FAMILY}`].article.about = aboutNaming(built, 'en', ['std-iso-1-2000', 'std-iso-2-2010']);
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 2 errata page\(s\) name in about other works than their corrects lists, or in another order/);
	assert.match(
		ran.err,
		new RegExp(
			`/es/reference/errata/iso-1/ names 2 work\\(s\\) and its corrects lists 2; at position 1 it names ${RegExp.escape(ES)}#std-iso-1-2000 where corrects lists ${RegExp.escape(ES)}#std-iso-2-2010`,
		),
	);
	assert.match(
		ran.err,
		new RegExp(
			`/reference/errata/iso-1/ names 2 work\\(s\\) and its corrects lists 1; at position 2 it names ${RegExp.escape(EN)}#std-iso-2-2010 where corrects lists nothing`,
		),
	);
	assert.match(ran.err, /FAIL the en errata family pages name 2 work\(s\) in about, and their corrects list 1/);
});

test('an errata page of the content tree the build does not hold, or one built from no page, fails', (t) => {
	// A family page that stopped being built would leave every count above
	// agreeing with a build that has one page fewer.
	const built = errataBuild();
	built.content['reference/errata/iso-2.md'] = errataSource('Errata in ISO 2', ['std-iso-2-2010']);
	built['es/reference/errata/iso-3'] = page('reference/errata/iso-3', 'es', { about: aboutNaming(built, 'es', ['std-iso-2-2010']) });
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL the en build holds 2 of the 3 errata pages under .*reference\/errata \(first missing: iso-2\)/);
	assert.match(ran.err, /FAIL \/es\/reference\/errata\/iso-3\/: an errata page with no page under .*es\/reference\/errata to say what it corrects/);
});

test('an errata index of the content tree the build does not hold fails', (t) => {
	const built = errataBuild();
	unbuildErrata(built, 'es');
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL the es errata index is under .*es\/reference\/errata and the build does not hold it/);
	assert.match(ran.err, /FAIL the es build holds 0 of the 2 errata pages under .*es\/reference\/errata \(first missing: iso-1, not-errata\)/);
});

test('a corrects field written in a shape the check cannot read fails', (t) => {
	// Read as nothing, the field would let the page name no work at all.
	const built = errataBuild();
	built.content[`${ERRATA_FAMILY}.md`] = '---\ntitle: "Errata in ISO 1"\ncorrects: ["std-iso-1-2000"]\n---\n';
	built.content[`es/${ERRATA_FAMILY}.md`] = '---\ntitle: "Errata en ISO 1"\ncorrects:\n  - std-iso-1-2000\n---\n';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL .*reference\/errata\/iso-1\.md: corrects is written in a shape this check cannot read: corrects: \["std-iso-1-2000"\]/);
	assert.match(ran.err, /FAIL .*es\/reference\/errata\/iso-1\.md: a line of corrects this check cannot read: - std-iso-1-2000/);
});

test('an errata family page whose about names the software alone fails', (t) => {
	const built = errataBuild();
	built[`es/${ERRATA_FAMILY}`].article.about = { '@id': SITE.software };
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL 1 errata page\(s\) name no work they correct in about, only the software \(first: \/es\/reference\/errata\/iso-1\/\)/,
	);
});

test('the page of properties that are not errata fails when it names a work it corrects', (t) => {
	const built = errataBuild();
	built['en/reference/errata/not-errata'].article.about = [
		{ '@id': SITE.software },
		stub(nodeAt(built, 'en/bibliography', `${EN}#std-iso-2-2010`)),
	];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/reference\/errata\/not-errata\/: the page of properties that are not errata corrects nothing and names 1 work\(s\) in about/,
	);
});

test("an errata page that names a corrected work on the other language's bibliography fails", (t) => {
	const built = errataBuild();
	built[`es/${ERRATA_FAMILY}`].article.about = [
		{ '@id': SITE.software },
		stub(nodeAt(built, 'en/bibliography', `${EN}#std-iso-1-2000`)),
	];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/es\/reference\/errata\/iso-1\/: the errata page names 1 work\(s\) it corrects on another language's bibliography/,
	);
});

test("an errata page whose about opens with a work, or names what is not one, fails", (t) => {
	const built = errataBuild();
	const { article } = built[`en/${ERRATA_FAMILY}`];
	article.about = [article.about[1], { '@id': SITE.software }, { '@id': SITE.person }];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/reference\/errata\/iso-1\/: the errata page's about opens with .*#std-iso-1-2000, not the software/);
	assert.match(ran.err, /FAIL \/reference\/errata\/iso-1\/: the errata page's about names 2 thing\(s\) that are not a cited work/);
});

test('an errata index built without its family pages or the page of properties that are not errata fails', (t) => {
	// The routes moved under the check: every errata assertion would read
	// nothing, and the build pass.
	const built = errataBuild();
	unbuildErrata(built, 'es', ['reference/errata']);
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL the es errata index was built with no family page under it/);
	assert.match(ran.err, /FAIL the es errata index was built without reference\/errata\/not-errata, the page of properties that are not errata/);
});

test('an errata content tree checked out with CRLF line endings is read as the LF one', (t) => {
	// A checkout with core.autocrlf=true, or the generator run on Windows,
	// writes the errata pages with CRLF; the build reads them as it reads LF.
	const built = errataBuild();
	for (const [path, text] of Object.entries(built.content)) built.content[path] = text.replaceAll('\n', '\r\n');
	const ran = check(t, built);
	assert.equal(ran.status, 0, ran.err);
	assert.match(
		ran.out,
		/ok {3}each of the 2 errata family pages names in about, in order, the works its corrects lists, 2 in all/,
	);
});
