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
// The glossary's terms are each held to the entry of src/data/glossary.mjs
// they are built from, and the real build only ever hands the check a
// glossary that passes.
//
// The site-wide graph is one block on the pages of both languages, so its
// descriptions, feature list and keywords are held to carry each text in
// English and in Spanish, the feature list one entry per topic that teaches,
// and no placeholder or bare area name ("files") among the keywords; its
// requirements are held to pyproject.toml, whatever floors and markers the
// file gives (scripts/shared/requirement-defects.test.mjs holds the sentence
// to the lines that give each Python a floor of its own), and every API page
// to the release and the Python it documents.
//
// Each test here writes a build into a directory of its own: the two
// bibliographies and one guide in each language, every cited work named as the
// bibliography names it, and as many plain pages besides as a test asks for.
// Beside it go the conformance report and the pages' frontmatter the build was
// made from, which the check joins to say what the report's Dataset has to be
// based on. It puts one defect into that build, runs the check on it the way
// CI does, and reads the exit status and the lines it printed. The pages, the site-wide
// nodes and the writing of the build come from
// shared/structured-data-fixture.mjs, which every suite of the check shares.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

import { glossary } from '../src/data/glossary.mjs';
import { en as homeEn, es as homeEs } from '../src/data/home.ts';
import { dependencies, extras, softwareRequirements } from '../src/data/repo-stats.mjs';
import { featureLists, siteDescriptions, softwareDescriptions } from '../src/data/scope.mjs';
import { domainIds, topicForSlug, topics } from '../src/data/topics.mjs';
import { catalogues } from '../src/generated/catalogues.mjs';
import { knownSlugs } from '../src/lib/breadcrumbs.mjs';
import { variablesMeasured } from '../src/lib/catalogue-datasets.mjs';
import { glossaryTermSet } from '../src/lib/glossary-structured-data.mjs';
import {
	ABOUT_TEXT,
	aboutPage,
	apiPage,
	build as wholeBuild,
	check as checkBuild,
	commitDay,
	FIRST_COMMIT,
	LIBRARY_MODIFIED,
	ORIGIN,
	page,
	SITE,
	SITE_TYPES,
	siteNodes,
	SOFTWARE_DOI,
	TARGET_PLATFORM,
	VERSION,
} from './shared/structured-data-fixture.mjs';

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

/** The library the committed report was generated for, which the report's Dataset gives as its version. */
const LIBRARY = JSON.parse(readFileSync(new URL('../../docs/conformance.json', import.meta.url), 'utf8')).library;

/** The day the report's rows last changed, which its banner prints and its Dataset gives. */
const DATA_DAY = '2026-09-15';

/** The commit the report's rows are of, which its banner names and every repository address of its Dataset is at. */
const DATA_COMMIT = '0123456789abcdef0123456789abcdef01234567';

/** An address in the repository at the commit the report's rows are of. */
const atCommit = (path, host = 'raw') =>
	host === 'raw'
		? `https://raw.githubusercontent.com/jmrplens/phonometry/${DATA_COMMIT}/${path}`
		: `https://github.com/jmrplens/phonometry/blob/${DATA_COMMIT}/${path}`;

/** The banner line of the report page that names the commit and the day its rows are of (Conformance.astro). */
const provenance = (day) =>
	'<p class="banner-provenance" data-report-provenance>Generated for phonometry <b data-report-library>4.0.0</b>; ' +
	`its rows last changed in commit <a href="https://github.com/jmrplens/phonometry/commit/${DATA_COMMIT}"><code data-report-commit="${DATA_COMMIT}">${DATA_COMMIT.slice(0, 9)}</code></a>, ` +
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
		distribution: [
			{ '@type': 'DataDownload', encodingFormat: 'application/json', contentUrl: atCommit('docs/conformance.json') },
			{ '@type': 'DataDownload', encodingFormat: 'text/markdown', contentUrl: atCommit('docs/CONFORMANCE.md') },
		],
		isBasedOn: [atCommit('scripts/conformance_report.py', 'blob'), stub(work)],
	};
	report.text = provenance(DATA_DAY);
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
 * Run the check on `built`, made from what `from` gives: the conformance
 * report, and the frontmatter of the guide in each language, written into the
 * content tree the build carries beside any page of it a test wrote (JSON is
 * YAML, so the frontmatter is written as JSON).
 */
function check(t, built, from = sources()) {
	const frontmatter = `---\ntitle: A guide\nreferences: ${JSON.stringify(from.references)}\n---\n\nText.\n`;
	const content = { ...built.content, 'guide.mdx': frontmatter, 'es/guide.mdx': frontmatter };
	return checkBuild(t, { ...built, content, report: from.report });
}

/**
 * A build the check has nothing to report on: the two bibliographies, a
 * guide and the conformance report in each language, where every cited work
 * is named as the bibliography names it, then plain English pages up to
 * `pages` in all.
 *
 * The first `dated` pages, in that order, are published on `published` and the
 * rest on the day of their last edit, 2026-10-01. `platforms` gives the
 * software node's `operatingSystem` on each page by the same index; a page
 * past its end names the default platforms.
 */
function build({ pages = 4, base: extra = {}, ...options } = {}) {
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
		base[`${lang}/report`] = reportPage(lang, iso2);
	}
	return wholeBuild({ pages, ...options, base: { ...base, ...extra } });
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
	built['page/8'].blocks = ['{"@context": '];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/page-8\/: an ld\+json block is not valid JSON/);
	assert.match(ran.err, /FAIL 10 page\(s\): the software node's operatingSystem is "Windows, Linux, macOS"/);
});

test('a block that parses to no JSON-LD object is reported as one that does not parse', (t) => {
	// `null` parses, and reading its @context threw, so the check stopped before
	// it reported the page or tallied any software node.
	const built = build({ pages: 11, dated: 9, platforms: Array(11).fill('Windows, Linux, macOS') });
	built['page/8'].blocks = ['null'];
	built['page/9'].blocks = ['[]'];
	built['page/10'].blocks = ['5'];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	for (const page of [8, 9, 10]) {
		assert.match(ran.err, new RegExp(`FAIL /page-${page}/: an ld\\+json block is not a JSON-LD object`));
	}
	assert.match(ran.err, /FAIL 11 page\(s\): the software node's operatingSystem is "Windows, Linux, macOS"/);
	assert.doesNotMatch(ran.err, /TypeError/);
});

test('a malformed block on a page leaves two nodes of its valid blocks that share an @id reported', (t) => {
	const twin = { '@context': 'https://schema.org', '@type': 'Thing', '@id': `${ORIGIN}/#thing` };
	const built = build({ pages: 10, dated: 9 });
	built['page/8'].blocks = [twin, twin, '{'];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/page-8\/: an ld\+json block is not valid JSON/);
	assert.match(ran.err, /FAIL \/page-8\/: .*\/#thing defined more than once/);
});

// The software's history and the About page. Every page carries the same
// site-wide nodes, so a defect in them is one line with the number of pages it
// stands on; the About page is asked for once in each language, typed as the
// page about the maintainer, and every span of years it writes, in whatever
// form, has to be the years of a role the Person node dates.

/**
 * Build ten pages, the bibliographies and guides every build of this file
 * holds, the two About pages and plain articles, all edited since they were
 * first published, and run the check on them.
 *
 * `nodes`, when given, are the site-wide nodes of every page. `about` replaces
 * an About page by its language: another page to build instead, or null to
 * leave it out.
 */
function history(t, { nodes, about = {} } = {}) {
	const built = build({ pages: 10 });
	for (const [lang, entry] of Object.entries(about)) {
		if (entry === null) delete built[`${lang}/about`];
		else built[`${lang}/about`] = entry;
	}
	if (nodes) {
		for (const entry of Object.values(built)) {
			entry.nodes = [...structuredClone(nodes), ...entry.nodes.filter((node) => !SITE_TYPES.has(node['@type']))];
		}
	}
	return check(t, built);
}

/** The About page of `lang` saying `text`. */
const saying = (lang, text) => ({ ...aboutPage(lang), text });

/** The site-wide nodes with the one of `type` changed by `change`, which edits a copy. */
function changed(type, change) {
	return siteNodes().map((node) => {
		if (node['@type'] !== type) return node;
		const copy = structuredClone(node);
		change(copy);
		return copy;
	});
}

/** The day before `day`, as `YYYY-MM-DD`. */
const dayBefore = (day) => new Date(Date.parse(`${day}T00:00:00Z`) - 86_400_000).toISOString().slice(0, 10);

test('a build whose software nodes give the whole history passes, and says what it read', (t) => {
	const ran = history(t);
	assert.equal(ran.status, 0, ran.err);
	assert.match(
		ran.out,
		new RegExp(
			`ok {3}the software's nodes on all 10 pages give its history: created ${FIRST_COMMIT}, ` +
				`library last changed ${LIBRARY_MODIFIED}, release notes, help, its former package and its archive`,
		),
	);
	assert.match(ran.out, /ok {3}the About page in English and its Spanish twin are both typed AboutPage/);
	assert.equal(ran.err, '');
});

test("the software's creation date is the UTC day of the first commit, not the day the committer's clock wrote", (t) => {
	// The first commit was made at one in the morning two hours ahead of UTC,
	// so the two days differ; if history ever made them agree, this test
	// would prove nothing, and says so.
	const local = commitDay('%cI', '--max-parents=0', 'HEAD');
	assert.notEqual(local, FIRST_COMMIT, "the first commit's own day and its UTC day agree");
	const ran = history(t, {
		nodes: siteNodes().map((node) =>
			node['@type'] === 'SoftwareApplication' || node['@type'] === 'SoftwareSourceCode'
				? { ...node, dateCreated: local }
				: node,
		),
	});
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		new RegExp(
			`FAIL SoftwareApplication dateCreated is "${local}", not ${FIRST_COMMIT}, ` +
				"the UTC day of the repository's first commit \\(on 10 pages\\)",
		),
	);
});

test("a page without one of the software's nodes fails by name, and the history is not said of every page", (t) => {
	const built = build({ pages: 10 });
	built['page/8'].nodes = built['page/8'].nodes.filter((node) => node['@type'] !== 'SoftwareSourceCode');
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/page-8\/: no SoftwareSourceCode node/);
	assert.doesNotMatch(ran.out, /give its history/);
});

test('a software node with no creation date, or source code created on another day, fails by name', (t) => {
	const nodes = siteNodes();
	delete nodes.find((node) => node['@type'] === 'SoftwareApplication').dateCreated;
	nodes.find((node) => node['@type'] === 'SoftwareSourceCode').dateCreated = dayBefore(FIRST_COMMIT);
	const ran = history(t, { nodes });
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		new RegExp(
			`FAIL SoftwareApplication dateCreated is undefined, not ${FIRST_COMMIT}, ` +
				"the UTC day of the repository's first commit \\(on 10 pages\\)",
		),
	);
	assert.match(ran.err, new RegExp(`FAIL SoftwareSourceCode dateCreated is "${dayBefore(FIRST_COMMIT)}"`));
});

test('a software node dated by a commit that did not change the library fails', (t) => {
	const ran = history(t, {
		nodes: changed('SoftwareApplication', (node) => {
			node.dateModified = dayBefore(LIBRARY_MODIFIED);
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		new RegExp(
			`FAIL SoftwareApplication dateModified is "${dayBefore(LIBRARY_MODIFIED)}", ` +
				`not ${LIBRARY_MODIFIED}, the UTC day of the last commit under src/ \\(on 10 pages\\)`,
		),
	);
});

test('release notes that point at the latest release only, or no help, fail', (t) => {
	const ran = history(t, {
		nodes: changed('SoftwareApplication', (node) => {
			node.releaseNotes = `${node.codeRepository}/releases/latest`;
			delete node.softwareHelp;
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL SoftwareApplication releaseNotes is "https:\/\/github\.com\/jmrplens\/phonometry\/releases\/latest", not https:\/\/github\.com\/jmrplens\/phonometry\/releases/,
	);
	assert.match(ran.err, /FAIL SoftwareApplication softwareHelp is undefined, not the WebSite node /);
});

test('release notes cannot be held to a repository the software node does not name', (t) => {
	const ran = history(t, {
		nodes: changed('SoftwareApplication', (node) => {
			delete node.codeRepository;
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL SoftwareApplication names no codeRepository, so its releaseNotes cannot be held to the repository's releases/,
	);
});

test('a software node that leaves out the package of its former name, or the name, fails', (t) => {
	const left = history(t, {
		nodes: changed('SoftwareApplication', (node) => {
			node.sameAs = node.sameAs.filter((url) => !url.includes('PyOctaveBand'));
		}),
	});
	assert.equal(left.status, 1);
	assert.match(
		left.err,
		/FAIL SoftwareApplication sameAs leaves out https:\/\/pypi\.org\/project\/PyOctaveBand\/, the package of its former name/,
	);
	const unnamed = history(t, {
		nodes: changed('SoftwareApplication', (node) => {
			delete node.alternateName;
		}),
	});
	assert.equal(unnamed.status, 1);
	assert.match(
		unnamed.err,
		/FAIL SoftwareApplication names no alternateName, the former name its first releases carry/,
	);
});

test('source code that does not name the application it builds fails', (t) => {
	const ran = history(t, {
		nodes: changed('SoftwareSourceCode', (node) => {
			delete node.targetProduct;
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL SoftwareSourceCode targetProduct is undefined, not the SoftwareApplication https:\/\/github\.com\/jmrplens\/phonometry#software/,
	);
});

test('source code with no archive, or another archive than its repository at Software Heritage, fails', (t) => {
	const archive =
		'https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/jmrplens/phonometry';
	const none = history(t, {
		nodes: changed('SoftwareSourceCode', (node) => {
			delete node.archivedAt;
		}),
	});
	assert.equal(none.status, 1);
	assert.match(
		none.err,
		new RegExp(
			`FAIL SoftwareSourceCode archivedAt is undefined, not ${RegExp.escape(archive)}, ` +
				'the Software Heritage archive of its repository',
		),
	);
	const other = history(t, {
		nodes: changed('SoftwareSourceCode', (node) => {
			node.archivedAt = 'https://doi.org/10.5281/zenodo.21215280';
		}),
	});
	assert.equal(other.status, 1);
	assert.match(
		other.err,
		/FAIL SoftwareSourceCode archivedAt is "https:\/\/doi\.org\/10\.5281\/zenodo\.21215280", not /,
	);
	const unrepositoried = history(t, {
		nodes: changed('SoftwareSourceCode', (node) => {
			delete node.codeRepository;
		}),
	});
	assert.equal(unrepositoried.status, 1);
	assert.match(
		unrepositoried.err,
		/FAIL SoftwareSourceCode names no codeRepository, so its archivedAt cannot be held to the repository's archive/,
	);
});

test('a build without the Spanish About page fails, and so does an About page typed as a plain article', (t) => {
	const typed = /typed AboutPage$/m;
	const missing = history(t, { about: { es: null } });
	assert.equal(missing.status, 1);
	assert.match(missing.err, /FAIL found 1 About page\(s\) in English and 0 in Spanish, not the English one and its Spanish twin/);
	assert.doesNotMatch(missing.out, typed);
	const plain = history(t, { about: { en: aboutPage('en', { '@type': 'TechArticle' }) } });
	assert.equal(plain.status, 1);
	assert.match(plain.err, /FAIL \/start\/about\/: the About page's article node is not typed AboutPage/);
	assert.doesNotMatch(plain.out, typed);
});

test('two English About pages are not the English one and its Spanish twin', (t) => {
	// start/about.html is served at /start/about/ as well.
	const ran = history(t, { about: { es: { ...aboutPage('en'), path: 'start/about.html' } } });
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL found 2 About page\(s\) in English and 0 in Spanish/);
	assert.doesNotMatch(ran.out, /typed AboutPage$/m);
});

test('an About page that dates the research role otherwise than the Person node fails, in either language', (t) => {
	const ran = history(t, {
		about: {
			en: saying('en', '<p>I worked as an acoustics researcher at the UPV from 2020 to 2023.</p>'),
			es: saying('es', '<p>Trabajé como investigador en acústica en la UPV de 2020 a 2023.</p>'),
		},
	});
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/start\/about\/: the page says "from 2020 to 2023", and no role the Person node dates runs from 2020 to 2023/,
	);
	assert.match(
		ran.err,
		/FAIL \/es\/start\/about\/: the page says "de 2020 a 2023", and no role the Person node dates runs from 2020 to 2023/,
	);
});

test('a Person node whose role moved, with the About page left as it was, fails', (t) => {
	const ran = history(t, {
		nodes: changed('Person', (node) => {
			node.hasOccupation[0].startDate = '2018';
			node.alumniOf[0].startDate = '2018';
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/start\/about\/: the page says "from 2019 to 2023", and no role the Person node dates runs from 2019 to 2023 or ends in 2023 with no start given/,
	);
	assert.match(ran.err, /FAIL \/es\/start\/about\/: the page says "de 2019 a 2023"/);
});

/** Run the check on the About pages saying `en` and `es`, the fixture's own text where left out. */
const sayingBoth = (t, { en = ABOUT_TEXT.en, es = ABOUT_TEXT.es } = {}) =>
	history(t, { about: { en: saying('en', en), es: saying('es', es) } });

/** The failure a wrong span of `route`'s About page prints, up to the years. */
const wrongSpan = (route, span) => new RegExp(`FAIL ${route}: the page says "${span}", and no role the Person node dates`);

test('a wrong span beside right ones fails in every form a page writes years in, in any case', (t) => {
	const ran = sayingBoth(t, {
		en:
			`${ABOUT_TEXT.en}<p>I studied at the Universidad de Alicante (2012-2018).</p>` +
			'<p>From 2020 to 2021 I taught at the UPV, between 2012 and 2018 I mixed sound, ' +
			'and in 2012-18 I toured.</p><p>I worked as an acoustics researcher at the UPV (2020\u20132023).</p>',
		es:
			`${ABOUT_TEXT.es}<p>Fui técnico de sonido desde 2012 hasta 2018, entre 2012 y 2018 ` +
			'y del 2012 al 2018.</p>',
	});
	assert.equal(ran.status, 1);
	for (const span of ['2012-2018', 'From 2020 to 2021', 'between 2012 and 2018', '2012-18', '2020\u20132023']) {
		assert.match(ran.err, wrongSpan('/start/about/', span));
	}
	for (const span of ['desde 2012 hasta 2018', 'entre 2012 y 2018', 'del 2012 al 2018']) {
		assert.match(ran.err, wrongSpan('/es/start/about/', span));
	}
	assert.doesNotMatch(ran.err, /the page says "(?:2018-2019|from 2019 to 2023|de 2019 a 2023)"/);
});

test('research years moved into a parenthesis fail though another span of the page is right', (t) => {
	const ran = sayingBoth(t, {
		en:
			'<p>I worked as an acoustics researcher at the UPV (2020\u20132023).</p>' +
			'<p>I was a sound technician from 2011 to 2018.</p>',
	});
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/start\/about\/: the page says "2020\u20132023", and no role the Person node dates runs from 2020 to 2023 or ends in 2023 with no start given/,
	);
});

test('a span ending the year a role the node dates by its end alone passes on its end year, and says so', (t) => {
	const ran = sayingBoth(t);
	assert.equal(ran.status, 0, ran.err);
	assert.match(
		ran.out,
		/ok {3}the About page in English writes 2 spans of years, each the years of a role the Person node dates; 1 of them only by its end year, the node giving that role no start/,
	);
	const moved = sayingBoth(t, { en: ABOUT_TEXT.en.replace('2018-2019', '2018-2020') });
	assert.equal(moved.status, 1);
	assert.match(
		moved.err,
		/FAIL \/start\/about\/: the page says "2018-2020", and no role the Person node dates runs from 2018 to 2020 or ends in 2020 with no start given/,
	);
});

test("a year inside an identifier, an ORCID iD or a standard's number, is no span", (t) => {
	const ran = sayingBoth(t, {
		en:
			`${ABOUT_TEXT.en}<p>ORCID 0000-0003-1250-6212; IEC 61672-1:2013, ISO 1996-2:2017 ` +
			'and https://example.org/2011-2012/.</p>',
	});
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}the About page in English writes 2 spans of years/);
});

test('an About page that names a dated role without its years passes', (t) => {
	const ran = history(t, {
		about: {
			en: saying(
				'en',
				'<p>I worked as an acoustics researcher at the UPV from 2019 to 2023.</p>' +
					'<p>Before that I was a sound technician.</p>',
			),
		},
	});
	assert.equal(ran.status, 0, ran.err);
	assert.match(
		ran.out,
		/ok {3}the About page in English writes 1 span of years, each the years of a role the Person node dates/,
	);
});

test('an About page that writes the years of no dated role fails, so the years check cannot go quiet', (t) => {
	const ran = history(t, {
		about: { en: saying('en', '<p>I worked as an acoustics researcher at the UPV for four years after my master.</p>') },
	});
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/start\/about\/: the page writes the years of none of the 4 roles the Person node dates, so they cannot be held to it/,
	);
	assert.match(
		ran.out,
		/ok {3}the About page in Spanish writes 2 spans of years, each the years of a role the Person node dates/,
	);
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
	for (const key of ['en/report', 'es/report']) built[key].article.mainEntity.isBasedOn.pop();
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL no page names a cited work: the citation markup changed under this check/);
});

test('the site-wide block within its byte budget passes, and says its size and how much of it the Person is', (t) => {
	const ran = check(t, build());
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}the site-wide ld\+json block is \d+ bytes on 8 pages, within its budget of \d+; the Person is \d+ of them/);
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
		/FAIL 8 page\(s\): the site-wide ld\+json block is \d+ bytes, over its budget of \d+; the Person spliced from jmrp\.io is \d+ of them/,
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

// The glossary. The real build only ever hands the check a glossary that
// passes, so a check that stopped comparing a term's name with its quantity,
// or let a code keep its TeX, would stay green there for good. It did let six
// defects through when it only compared a term's name with its own code: a
// name that was the symbol with the code deleted, the other language's
// quantity, the quantity in lower case, a trailing space, terms with no code
// at all and a term with no guide.
//
// These builds add to the shared pages the two glossary pages, each carrying
// the DefinedTermSet src/lib/glossary-structured-data.mjs gives it in a block
// of its own, as the page writes it, and the page of every guide a term
// points at, in both languages. That build passes. Each defect is then made
// on it, the way it would reach a real build, and the check has to fail on it
// by name.

/** Every guide a glossary entry names. */
const GUIDES = [...new Set(glossary.flatMap((group) => group.terms).map((term) => term.guide))];

/**
 * The shared pages, with the two glossary pages and the page of every guide
 * their terms point at, in both languages, every page edited since it was
 * first published. `mutate` is given the two DefinedTermSets and the list of
 * guides to publish, to break first.
 */
function glossaryBuild(mutate = () => {}) {
	const sets = {
		en: glossaryTermSet('en', (slug) => `Guide ${slug}`),
		es: glossaryTermSet('es', (slug) => `Guía ${slug}`),
	};
	const guides = [...GUIDES];
	mutate(sets, guides);
	const base = {};
	for (const lang of ['en', 'es']) {
		base[`${lang}/glossary`] = { ...page('reference/glossary', lang), blocks: [sets[lang]] };
		for (const slug of guides) base[`${lang}/${slug}`] = page(slug, lang);
	}
	return build({ base, pages: 0, dated: Number.POSITIVE_INFINITY });
}

/** Run the check on the glossary build, broken first by `mutate`. */
const glossaryCheck = (t, mutate) => check(t, glossaryBuild(mutate));

/** The DefinedTerm of entry `id` in a set. */
const termOf = (set, id) => set.hasDefinedTerm.find((term) => term['@id'].endsWith(`#${id}`));

/** Assert the check failed, and on the glossary page of `lang` for `what`. */
function failsWith(ran, lang, what) {
	assert.equal(ran.status, 1, `the check passed:\n${ran.out}`);
	const route = lang === 'es' ? '/es/reference/glossary/' : '/reference/glossary/';
	const line = ran.err.split('\n').find((text) => text.startsWith(`FAIL ${route}:`) && what.test(text));
	assert.ok(line, `no FAIL line on ${route} matching ${what}:\n${ran.err}`);
	return line;
}

/** The line the check prints when the whole glossary passes. */
const GLOSSARY_OK = /ok {3}checked the \d+ DefinedTerms of the glossary in both languages/;

test('the glossary as the site publishes it passes, with every term joined to its guide', (t) => {
	const ran = glossaryCheck(t);
	assert.equal(ran.status, 0, ran.err);
	const terms = glossary.flatMap((group) => group.terms).length;
	assert.match(ran.out, new RegExp(`ok {3}checked the ${2 * terms} DefinedTerms of the glossary in both languages`));
	assert.match(ran.out, new RegExp(`which all ${2 * terms} resolve to in this build`));
	assert.equal(ran.err, '');
});

test('a term named by its symbol, with its code and alternate name gone, fails', (t) => {
	const ran = glossaryCheck(t, ({ en }) => {
		const term = termOf(en, 'l-aeq');
		term.name = 'LAeq';
		delete term.termCode;
		delete term.alternateName;
	});
	assert.match(failsWith(ran, 'en', /not named by the quantity/), /l-aeq \("LAeq", not "A-weighted equivalent/);
	assert.match(failsWith(ran, 'en', /have a symbol and no usable termCode/), /l-aeq \(undefined\)/);
});

test('terms named by their code, as every symbolised term used to be, fail by that name', (t) => {
	const ran = glossaryCheck(t, ({ en }) => {
		for (const term of en.hasDefinedTerm) if (term.termCode) term.name = term.termCode;
	});
	assert.match(failsWith(ran, 'en', /named by their termCode instead of the quantity/), /186 of 198/);
});

test('terms with no code and no alternate name at all fail', (t) => {
	const ran = glossaryCheck(t, ({ es }) => {
		for (const term of es.hasDefinedTerm) {
			delete term.termCode;
			delete term.alternateName;
		}
	});
	assert.match(failsWith(ran, 'es', /have a symbol and no usable termCode/), /186 of 198/);
	assert.match(failsWith(ran, 'es', /alternateName that is not the alias their entry declares/), /6 of 198 .*itu-r-468/);
});

test('a term with no guide fails', (t) => {
	const ran = glossaryCheck(t, ({ en }) => {
		delete termOf(en, 'l-aeq').subjectOf;
	});
	assert.match(failsWith(ran, 'en', /do not point at the guide that computes them/), /1 of 198 DefinedTerm\(s\).*: l-aeq$/);
});

test("the other language's quantity, the quantity in lower case and a trailing space all fail as names", (t) => {
	const ran = glossaryCheck(t, ({ en }) => {
		termOf(en, 'l-aeq').name = 'Nivel de presión acústica continuo equivalente ponderado A';
		termOf(en, 'l-eq').name = 'equivalent continuous sound pressure level';
		termOf(en, 'l-p').name = 'Sound pressure level ';
	});
	const line = failsWith(ran, 'en', /3 of 198 DefinedTerm\(s\) are not named by the quantity/);
	for (const id of ['l-aeq', 'l-eq', 'l-p']) assert.match(line, new RegExp(`${id} \\(`));
});

test('TeX left in a code, or a code that is not the alternate name, fails', (t) => {
	const ran = glossaryCheck(t, ({ en }) => {
		const tex = termOf(en, 'l-aeq');
		tex.termCode = 'L_\\mathrm{Aeq}';
		tex.alternateName = tex.termCode;
		termOf(en, 'l-eq').alternateName = 'Leq, the equivalent level';
	});
	assert.match(failsWith(ran, 'en', /carry TeX in their termCode/), /l-aeq/);
	assert.match(failsWith(ran, 'en', /alternateName that is not their termCode/), /l-eq/);
});

test('a named term with a code, or with its label for an alternate name, fails', (t) => {
	const ran = glossaryCheck(t, ({ en }) => {
		termOf(en, 'pml').termCode = 'PML';
		termOf(en, 'pml').alternateName = 'PML (perfectly matched layer)';
		termOf(en, 'cepstrum').alternateName = 'Cepstrum and quefrency';
	});
	assert.match(failsWith(ran, 'en', /named rather than symbolised and still carry a termCode/), /pml/);
	const line = failsWith(ran, 'en', /alternateName that is not the alias their entry declares/);
	assert.match(line, /pml \("PML \(perfectly matched layer\)" for "PML"\)/);
	assert.match(line, /cepstrum \("Cepstrum and quefrency" for undefined\)/);
});

test('a term with no entry, an entry with no term and a term published twice fail', (t) => {
	const ran = glossaryCheck(t, ({ en }) => {
		const extra = structuredClone(termOf(en, 'l-p'));
		extra['@id'] = extra['@id'].replace('#l-p', '#no-such-term');
		const twice = structuredClone(termOf(en, 'l-eq'));
		en.hasDefinedTerm = en.hasDefinedTerm.filter((term) => !term['@id'].endsWith('#l-aeq'));
		en.hasDefinedTerm.push(extra, twice);
	});
	assert.match(failsWith(ran, 'en', /have no entry in src\/data\/glossary\.mjs/), /no-such-term/);
	assert.match(failsWith(ran, 'en', /published more than once/), /l-eq/);
	assert.match(failsWith(ran, 'en', /entr\(y\/ies\) of src\/data\/glossary\.mjs have no DefinedTerm/), /l-aeq/);
});

test('a guide in the other language, or not its article node, fails, and so does one the build lacks', (t) => {
	const ran = glossaryCheck(t, ({ es }, guides) => {
		const english = `${ORIGIN}/signals/levels/levels/`;
		termOf(es, 'l-aeq').subjectOf = { ...termOf(es, 'l-aeq').subjectOf, url: english, '@id': `${english}#article` };
		const own = termOf(es, 'l-eq').subjectOf;
		termOf(es, 'l-eq').subjectOf = { ...own, '@id': own.url };
		guides.splice(guides.indexOf('signals/metrology/calibration'), 1);
	});
	const line = failsWith(ran, 'es', /point at another page than their entry's guide/);
	assert.match(line, /l-aeq/);
	assert.match(line, /l-eq/);
	assert.match(ran.err, /FAIL \d+ glossary term\(s\) point at an article node no page of the build defines/);
	assert.match(ran.err, /es\/signals\/metrology\/calibration\/#article/);
});

test('a hole or TeX left in a description fails', (t) => {
	const ran = glossaryCheck(t, ({ en }) => {
		termOf(en, 'k-2').description = termOf(en, 'k-2').description.replace('≤', '');
		termOf(en, 'tau').description = 'a $\\tau$ of 10-5 is a 50 dB partition.';
	});
	assert.match(failsWith(ran, 'en', /hole in their description/), /k-2 \("[^"]*K2A {2}4/);
	assert.match(failsWith(ran, 'en', /carry TeX in their description/), /tau/);
});

// What a step that writes maths as text loses on the way. The step the page
// used before dropped every command it did not know: of the 26 codes and the
// 17 descriptions in each language it misread, the check saw only the 12
// codes left blank or opening with a space and the 6 descriptions with two
// spaces in a row, and said every code had no TeX left and every description
// no hole. A code or a description that loses a Greek letter, a named
// function, a root or an exponent cleanly, or reads a thin space as a comma,
// is missing something its entry writes, and the check counts what the entry
// writes.

/** The code and alternate name of entry `id` in a set, written as `code`. */
function plantCode(set, id, code) {
	termOf(set, id).termCode = code;
	termOf(set, id).alternateName = code;
}

/** The description of entry `id` in a set, with `published` written as `misread`. */
function plantDescription(set, id, published, misread) {
	const term = termOf(set, id);
	assert.ok(term.description.includes(published), `${id}: "${published}" is not in "${term.description}"`);
	term.description = term.description.replace(published, misread);
}

test('a code that lost a Greek letter, has a hole, or reads a thin space as a comma fails by name', (t) => {
	const ran = glossaryCheck(t, ({ en }) => {
		plantCode(en, 'alpha-s', 's');
		plantCode(en, 'se', 'SE,  LSE');
		plantCode(en, 'l-p-a-s-4m', 'Lp,A,S,4,m');
	});
	const lost = failsWith(ran, 'en', /have a termCode that lost what their symbol writes/);
	assert.match(lost, /alpha-s \("s": 1 of its 1 Greek letter\(s\)\)/);
	assert.match(lost, /se \("SE, {2}LSE": 1 of its 1 Greek letter\(s\)\)/);
	assert.match(failsWith(ran, 'en', /have a hole in their termCode/), /se \("SE, {2}LSE"\)/);
	const commas = failsWith(ran, 'en', /termCode whose commas are not those of their symbol/);
	assert.match(commas, /l-p-a-s-4m \("Lp,A,S,4,m": 4, the symbol 3\)/);
	assert.doesNotMatch(ran.out, GLOSSARY_OK);
});

test('a description that lost a Greek letter, a function name or an exponent fails by name', (t) => {
	const ran = glossaryCheck(t, ({ es }) => {
		plantDescription(es, 'eta-tot', 'Ts = 2,2/(f ηtot)', 'Ts = 2,2/(f,tot)');
		plantDescription(es, 'k-1', '-10 log10(1 - 10^(-0,1ΔLp))', '-1010(1 - 10-0,1 Lp)');
	});
	const lost = failsWith(ran, 'es', /have a description that lost what their entry writes/);
	assert.match(lost, /eta-tot \(1 of its 1 Greek letter\(s\)\)/);
	assert.match(lost, /k-1 \(1 of its 1 Greek letter\(s\), \\log, 1 exponent\(s\)\)/);
	const commas = failsWith(ran, 'es', /description whose commas are not those of their entry/);
	assert.match(commas, /eta-tot \(\d+, the entry \d+\)/);
	assert.doesNotMatch(ran.out, GLOSSARY_OK);
});

/**
 * The step the page used to write its maths as text with: the argument of a
 * font command kept, every other command dropped, and the TeX characters
 * deleted.
 */
const droppingStep = (source) =>
	source
		.replace(/\\(?:text|mathrm|mathit|mathbf|operatorname)\{([^}]*)\}/g, '$1')
		.replace(/\\[a-zA-Z]+/g, '')
		.replace(/[$\\{}_^]/g, '');

test('every code and description the step that dropped commands wrote fails, in both languages', (t) => {
	const entries = new Map(glossary.flatMap((group) => group.terms).map((entry) => [entry.id, entry]));
	const ran = glossaryCheck(t, (sets) => {
		for (const [lang, set] of Object.entries(sets)) {
			for (const term of set.hasDefinedTerm) {
				const entry = entries.get(term['@id'].split('#').pop());
				if (entry.symbol) plantCode(set, entry.id, droppingStep(entry.symbol));
				// The definition the step misread, and the unit and the standard
				// after it as the page writes them.
				const definition = typeof entry.definition === 'string' ? entry.definition : entry.definition[lang];
				const end = term.description.indexOf(lang === 'es' ? ' Definida en: ' : ' Defined in: ');
				const unit = term.description.lastIndexOf(lang === 'es' ? ' Unidad: ' : ' Unit: ', end);
				term.description = `${droppingStep(definition)}${term.description.slice(unit < 0 ? end : unit)}`;
			}
		}
	});
	for (const lang of ['en', 'es']) {
		failsWith(ran, lang, /have a termCode that lost what their symbol writes/);
		failsWith(ran, lang, /termCode whose commas are not those of their symbol/);
		failsWith(ran, lang, /have a description that lost what their entry writes/);
	}
	assert.doesNotMatch(ran.out, GLOSSARY_OK);
});

// A count cannot tell a code from another that writes as many of each:
// "wrong" for $L_\mathrm{Aeq}$ writes no Greek letter, function, exponent or
// comma, and neither does the symbol, so it passed with the ok line, as did a
// code with a letter, a digit or a prime dropped and a Greek letter written as
// another. A code and a description are held to what they write as
// themselves, in order, read from the entry's own fields.

/** The ids planted below, each with the code it is given and what its symbol writes. */
const MISWRITTEN = {
	en: [
		['l-aeq', 'wrong', 'LAeq'],
		['l-eq', 'L', 'Leq'],
		['k-1', 'K', 'K1'],
		['alpha-s', 'βs', 'αs'],
		['thd-n', 'THDN', 'THD+N'],
	],
	es: [
		['r-2', 'R', "R'"],
		['l-nt', 'LnT', "L'nT"],
		['sigma', 'ρ', 'σ'],
	],
};

test('a code that writes other letters, digits, primes, Greek letters or signs than its symbol fails by name', (t) => {
	const ran = glossaryCheck(t, (sets) => {
		for (const [lang, planted] of Object.entries(MISWRITTEN)) {
			for (const [id, code] of planted) plantCode(sets[lang], id, code);
		}
	});
	for (const [lang, planted] of Object.entries(MISWRITTEN)) {
		const line = failsWith(ran, lang, /have a termCode that does not write what their symbol writes/);
		assert.match(line, new RegExp(`: ${planted.length} of \\d+ DefinedTerm`));
		for (const [id, code, written] of planted) {
			assert.ok(line.includes(`${id} (${JSON.stringify(code)}, the symbol ${JSON.stringify(written)})`), `${id} in ${line}`);
		}
	}
	assert.doesNotMatch(ran.out, GLOSSARY_OK);
});

// A field is read as TeX writes it, one control sequence at a time: a
// spacing command is the space it sets, or nothing for `\!`, and `\prime` is
// the prime, on its own or as a superscript. "$4\:\mathrm{m}$" writes what
// "$4\,\mathrm{m}$" does, "$L_{W\!A}$" what "$L_{WA}$" does and "$s^{\prime}$"
// what "$s'$" does. The check took the colon and the exclamation mark of the
// two spacing commands as written, dropped `\prime` and counted the caret
// before it as an exponent, so an entry that wrote any of them failed beside
// the codes and descriptions the page writes from it.

/** Entries written another way TeX allows: the id, the field, the text the site writes and the one planted. */
const TEX_FORMS = [
	['l-p-a-s-4m', 'symbol', '4\\,\\mathrm{m}', '4\\:\\mathrm{m}'],
	['l-wa', 'symbol', 'L_{WA}', 'L_{W\\!A}'],
	['n-2', 'symbol', "N'", 'N\\prime'],
	['s-2', 'symbol', "s'", 's^{\\prime}'],
	['courant-number', 'definition', 'c\\,\\Delta t', 'c\\:\\Delta t'],
	['nr-2', 'definition', 'L_{p1} - L_{p2}', 'L_{p1}\\! - L_{p2}'],
];

test('an entry written with a spacing command or with \\prime passes beside the codes and descriptions the page writes from it', (t) => {
	const groups = structuredClone(glossary);
	const entries = new Map(groups.flatMap((group) => group.terms).map((entry) => [entry.id, entry]));
	for (const [id, field, written, planted] of TEX_FORMS) {
		const edit = (text) => {
			assert.ok(text.includes(written), `${id}: "${written}" is not in "${text}"`);
			return text.replace(written, planted);
		};
		const value = entries.get(id)[field];
		entries.get(id)[field] =
			typeof value === 'string' ? edit(value) : Object.fromEntries(Object.entries(value).map(([lang, text]) => [lang, edit(text)]));
	}
	// The page writes `\prime` as the prime, where the site's "'" stays as typed.
	const built = glossaryBuild((sets) => {
		for (const set of Object.values(sets)) {
			plantCode(set, 'n-2', 'N′');
			plantCode(set, 's-2', 's′');
		}
	});
	const ran = check(t, { ...built, glossary: groups });
	assert.equal(ran.status, 0, `the check failed:\n${ran.err}`);
	assert.match(ran.out, GLOSSARY_OK);
});

test('a description that writes other text than its definition, or drops a sign or its unit, fails by name', (t) => {
	const ran = glossaryCheck(t, ({ en, es }) => {
		const lp = termOf(en, 'l-p');
		lp.description = `wrong.${lp.description.slice(lp.description.indexOf(' Unit: '))}`;
		plantDescription(en, 'l-cpeak', 'µPa', 'Pa');
		plantDescription(en, 'imd', ' Unit: %.', '');
		plantDescription(es, 'k-2', 'K2A ≤ 4', 'K2 ≤ 4');
	});
	const en = failsWith(ran, 'en', /have a description that does not write what their entry writes/);
	assert.match(en, /: 3 of \d+ DefinedTerm\(s\) .*: (?=.*\bl-p\b)(?=.*\bl-cpeak\b)(?=.*\bimd\b)/);
	assert.match(failsWith(ran, 'es', /have a description that does not write what their entry writes/), /: 1 of \d+ DefinedTerm\(s\) .*: k-2$/);
	assert.doesNotMatch(ran.out, GLOSSARY_OK);
});

/**
 * A step that drops a font command with its argument, so that "$L_\mathrm{Aeq}$"
 * comes out "L" and keeps every Greek letter, function, exponent and comma.
 */
const droppingArguments = (source) =>
	source
		.replace(/\\(?:text|mathrm|mathit|mathbf|operatorname)\{[^}]*\}/g, '')
		.replace(/\\[a-zA-Z]+/g, '')
		.replace(/[$\\{}_^]/g, '');

test('every code written as one word, and every code and description that dropped its font arguments, fails in both languages by count', (t) => {
	const entries = new Map(glossary.flatMap((group) => group.terms).map((entry) => [entry.id, entry]));
	const symbolised = { en: 0, es: 0 };
	const wrong = glossaryCheck(t, (sets) => {
		for (const [lang, set] of Object.entries(sets)) {
			for (const term of set.hasDefinedTerm) {
				const entry = entries.get(term['@id'].split('#').pop());
				if (entry.symbol) {
					plantCode(set, entry.id, 'wrong');
					symbolised[lang] += 1;
				}
			}
		}
	});
	for (const lang of ['en', 'es']) {
		const line = failsWith(wrong, lang, /have a termCode that does not write what their symbol writes/);
		assert.match(line, new RegExp(`: ${symbolised[lang]} of \\d+ DefinedTerm`));
	}
	const dropped = glossaryCheck(t, (sets) => {
		for (const [lang, set] of Object.entries(sets)) {
			for (const term of set.hasDefinedTerm) {
				const entry = entries.get(term['@id'].split('#').pop());
				if (entry.symbol) plantCode(set, entry.id, droppingArguments(entry.symbol));
				const definition = typeof entry.definition === 'string' ? entry.definition : entry.definition[lang];
				const end = term.description.indexOf(lang === 'es' ? ' Definida en: ' : ' Defined in: ');
				const unit = term.description.lastIndexOf(lang === 'es' ? ' Unidad: ' : ' Unit: ', end);
				term.description = `${droppingArguments(definition)}${term.description.slice(unit < 0 ? end : unit)}`;
			}
		}
	});
	for (const lang of ['en', 'es']) {
		failsWith(dropped, lang, /have a termCode that does not write what their symbol writes/);
		failsWith(dropped, lang, /have a description that does not write what their entry writes/);
	}
	assert.doesNotMatch(wrong.out, GLOSSARY_OK);
	assert.doesNotMatch(dropped.out, GLOSSARY_OK);
});

// The glossary is found by its route. Were the page to move, its checks would
// stop with nothing to say so; a build that publishes the guides its entries
// name has to publish it, once in each language, and a build of a few pages
// that publishes none of them, as every other suite here writes, has no
// glossary to answer for.

test('a build that publishes the guides without the Spanish glossary fails, and says no more of the glossary', (t) => {
	const built = glossaryBuild();
	delete built['es/glossary'];
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		new RegExp(
			'FAIL found 0 glossary pages in Spanish, not one, in a build that publishes ' +
				`${GUIDES.length} of the ${GUIDES.length} guides its entries name in that language`,
		),
	);
	assert.doesNotMatch(ran.out, GLOSSARY_OK);
});

test('two English glossary pages are not the English one and its Spanish twin', (t) => {
	// reference/glossary.html is served at /reference/glossary/ as well.
	const built = glossaryBuild();
	built['es/glossary'] = { ...built['en/glossary'], path: 'reference/glossary.html' };
	const ran = check(t, built);
	assert.equal(ran.status, 1, `the check passed:\n${ran.out}`);
	assert.match(ran.err, /FAIL found 2 glossary pages in English, not one/);
	assert.match(ran.err, /FAIL found 0 glossary pages in Spanish, not one/);
	assert.doesNotMatch(ran.out, GLOSSARY_OK);
});

test('one guide a glossary entry names is enough to ask for the glossary of its language', (t) => {
	const ran = check(t, build({ base: { guide: page(GUIDES[0], 'en') } }));
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		new RegExp(
			'FAIL found 0 glossary pages in English, not one, in a build that publishes ' +
				`1 of the ${GUIDES.length} guides its entries name in that language`,
		),
	);
	assert.doesNotMatch(ran.err, /glossary pages in Spanish/);
});

test('a build of a few pages that publishes none of the guides has no glossary to answer for', (t) => {
	const ran = check(t, build());
	assert.equal(ran.status, 0, ran.err);
	assert.doesNotMatch(`${ran.out}${ran.err}`, /glossary/i);
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

// The site-wide graph in both languages. Every page carries the same block, so
// each defect is one line with the number of pages it stands on; a Spanish page
// used to describe the software in English, list eleven of the thirteen
// topics, publish "no governing standard" as a standard and state two of the
// package's five optional extras.

/** The site-wide nodes with the one of each type in `changes` changed by its function, on a copy. */
function changedAll(changes) {
	return siteNodes().map((node) => {
		const change = changes[node['@type']];
		if (!change) return node;
		const copy = structuredClone(node);
		change(copy);
		return copy;
	});
}

/** A requirement as a failure line names it: pyproject.toml's text without spaces, its marker in brackets. */
const asWritten = ({ text }) => {
	const [requirement, marker] = text.split(';').map((part) => part.replace(/\s+/g, ''));
	return marker ? `${requirement} (${marker})` : requirement;
};

/** "a", "a and b", "a, b and c", as a failure line lists what it names. */
const listed = (items) => (items.length < 2 ? items.join('') : `${items.slice(0, -1).join(', ')} and ${items.at(-1)}`);

/** The label of each topic that teaches, in the order the navigation lists them, in `lang`. */
const topicLabels = (lang) => domainIds.map((id) => topics.find((topic) => topic.id === id).label[lang]);

test('a build whose site-wide nodes speak both languages passes, and says what it read', (t) => {
	const ran = history(t);
	assert.equal(ran.status, 0, ran.err);
	assert.match(
		ran.out,
		new RegExp(
			'ok {3}the site-wide nodes on all 10 pages describe the site and the software in English and in Spanish, ' +
				`list one feature for each of the ${domainIds.length} topics that teach in each language, ` +
				'publish no placeholder as a standard or a keyword, and state every requirement and extra of pyproject.toml',
		),
	);
	assert.equal(ran.err, '');
	// A build with no API page has no release to answer for.
	assert.doesNotMatch(ran.out, /name the release/);
});

test('descriptions in English alone, as every page published them, fail on both nodes', (t) => {
	const ran = history(t, {
		nodes: changedAll({
			WebSite: (node) => {
				node.description = siteDescriptions.en;
			},
			SoftwareApplication: (node) => {
				node.description = softwareDescriptions.en;
			},
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL WebSite description is not one text in English and one in Spanish, each tagged with its language: "Acoustic measurement toolkit/);
	assert.match(ran.err, /FAIL SoftwareApplication description is not one text in English and one in Spanish, each tagged with its language: "Acoustic measurement, analysis/);
	assert.match(ran.err, /\(on 10 pages\)/);
	assert.doesNotMatch(ran.out, /speak|in English and in Spanish, list/);
});

test('a Spanish description that is the English text, or any other than scope.mjs writes, fails', (t) => {
	const ran = history(t, {
		nodes: changedAll({
			SoftwareApplication: (node) => {
				node.description = [
					{ '@value': softwareDescriptions.en, '@language': 'en' },
					{ '@value': softwareDescriptions.en, '@language': 'es' },
				];
			},
			WebSite: (node) => {
				node.description[1]['@value'] = siteDescriptions.es.replace('Python', 'Phyton');
			},
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL SoftwareApplication description in Spanish is the English text: "Acoustic measurement, analysis/);
	assert.match(ran.err, /FAIL WebSite description in Spanish is not the Spanish text src\/data\/scope\.mjs writes: "Biblioteca de medición acústica en Phyton/);
});

test('a feature list in English alone and eleven areas long, as every page published it, fails', (t) => {
	const eleven = featureLists.en.filter((feature) => !/^(?:Fluids|Elastic solids):/.test(feature));
	const ran = history(t, {
		nodes: changedAll({
			SoftwareApplication: (node) => {
				node.featureList = eleven;
			},
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL SoftwareApplication featureList has 11 entries tagged with no language of the site/);
	assert.match(
		ran.err,
		new RegExp(`FAIL SoftwareApplication featureList in Spanish has 0 entries, not one for each of the ${domainIds.length} topics that teach`),
	);
});

test('a feature list that leaves out a topic in one language fails, naming the topic', (t) => {
	const [, fluids] = topicLabels('es');
	const ran = history(t, {
		nodes: changedAll({
			SoftwareApplication: (node) => {
				node.featureList = node.featureList.filter(
					(feature) => !(feature['@language'] === 'es' && feature['@value'].startsWith(`${fluids}:`)),
				);
			},
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		new RegExp(`FAIL SoftwareApplication featureList in Spanish has ${domainIds.length - 1} entries, not one for each of the ${domainIds.length} topics that teach`),
	);
	assert.match(ran.err, new RegExp(`entry 2 opens with "${topicLabels('es')[2]}", not with "${fluids}", the topic topics\\.mjs lists there`));
	assert.doesNotMatch(ran.err, /featureList in English/);
});

test('a feature in another order than the navigation, or another text than scope.mjs writes, fails', (t) => {
	const ran = history(t, {
		nodes: changedAll({
			SoftwareApplication: (node) => {
				const english = node.featureList.filter((feature) => feature['@language'] === 'en');
				[english[0], english[1]] = [english[1], english[0]];
				const spanish = node.featureList.filter((feature) => feature['@language'] === 'es');
				spanish[3] = { ...spanish[3], '@value': `${spanish[3]['@value']} Y más.` };
				node.featureList = [...english, ...spanish];
			},
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, new RegExp(`entry 1 opens with "${topicLabels('en')[1]}", not with "${topicLabels('en')[0]}"`));
	assert.match(
		ran.err,
		new RegExp(
			'FAIL SoftwareApplication featureList in Spanish is not the list src/data/scope\\.mjs builds from ' +
				`the landing page: entry 4 is "${topicLabels('es')[3]}: `,
		),
	);
});

test('a placeholder published as a standard or as a keyword fails, in either language', (t) => {
	const placeholder = homeEn.coverage.noStandard;
	const ran = history(t, {
		nodes: changedAll({
			SoftwareApplication: (node) => {
				const last = node.featureList.findIndex((feature) => feature['@language'] === 'es') - 1;
				node.featureList[last] = {
					...node.featureList[last],
					'@value': `${node.featureList[last]['@value']} Standards implemented: ${placeholder}.`,
				};
				node.keywords = [...node.keywords, { '@value': 'sin norma que la rija', '@language': 'es' }];
			},
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, new RegExp(`FAIL SoftwareApplication featureList states "${placeholder}" as a standard`));
	assert.match(ran.err, /FAIL SoftwareApplication keywords publish "sin norma que la rija" as a keyword/);
	// One text of keywords delimited by commas, as every page published them.
	const joined = history(t, {
		nodes: changedAll({
			SoftwareApplication: (node) => {
				node.keywords = `acoustics, Python, signal analysis, files, ISO 717-1, ${placeholder}`;
			},
		}),
	});
	assert.equal(joined.status, 1);
	assert.match(joined.err, new RegExp(`FAIL SoftwareApplication keywords publish "${placeholder}" as a keyword`));
	assert.match(joined.err, /FAIL SoftwareApplication keywords hold no keyword in Spanish/);
	assert.match(joined.err, /FAIL SoftwareApplication keywords publish "files", the name of an area that says nothing about acoustics on its own/);
});

test('the name of an area that says nothing about acoustics, published as a keyword, fails in either language', (t) => {
	const replaced = [homeEn, homeEs].flatMap(({ coverage }) => coverage.areas.filter((area) => area.keyword));
	assert.ok(replaced.length >= 2, 'no area of the landing pages gives a keyword of its own; update this test');
	const names = new Map(replaced.map((area) => [area.keyword, area.name.toLowerCase()]));
	const ran = history(t, {
		nodes: changedAll({
			SoftwareApplication: (node) => {
				node.keywords = node.keywords.map((keyword) =>
					names.has(keyword?.['@value']) ? { ...keyword, '@value': names.get(keyword['@value']) } : keyword,
				);
			},
		}),
	});
	assert.equal(ran.status, 1);
	for (const area of replaced) {
		assert.match(
			ran.err,
			new RegExp(
				`FAIL SoftwareApplication keywords publish "${RegExp.escape(area.name.toLowerCase())}", the name of an area ` +
					'that says nothing about acoustics on its own \\(on 10 pages\\)',
			),
		);
	}
	assert.match(ran.err, /keywords publish "files"/);
	assert.match(ran.err, /keywords publish "archivos"/);
	// The check names the Files topic itself, so a keywords list that names
	// it in either language fails whatever the landing page's rows declare.
	const bare = history(t, {
		nodes: changedAll({
			SoftwareApplication: (node) => {
				node.keywords = [...node.keywords, { '@value': 'Archivos', '@language': 'es' }];
			},
		}),
	});
	assert.equal(bare.status, 1);
	assert.match(bare.err, /FAIL SoftwareApplication keywords publish "archivos", the name of an area that says nothing about acoustics on its own/);
	assert.doesNotMatch(bare.err, /keywords publish "files"/);
});

test('requirements typed by hand, as every page published them, fail and name what they leave out', (t) => {
	const ran = history(t, {
		nodes: changedAll({
			SoftwareApplication: (node) => {
				node.softwareRequirements = 'Python >= 3.12 with NumPy and SciPy (matplotlib and numba optional).';
			},
		}),
	});
	assert.equal(ran.status, 1);
	// Every requirement and every extra pyproject.toml gives, read from it, so
	// the test holds whichever floors the file sets and whatever markers it
	// writes them behind.
	const named = [...dependencies.map(asWritten), ...extras.map((extra) => `the extra ${extra.name}`)];
	assert.ok(named.length > 2, 'pyproject.toml gives no requirement or no extra; update this test');
	assert.match(
		ran.err,
		new RegExp(
			`FAIL SoftwareApplication softwareRequirements leaves out ${RegExp.escape(listed(named))}, ` +
				'which pyproject\\.toml gives \\(on 10 pages\\)',
		),
	);
	const none = history(t, {
		nodes: changedAll({
			SoftwareApplication: (node) => {
				delete node.softwareRequirements;
			},
		}),
	});
	assert.equal(none.status, 1);
	assert.match(none.err, /FAIL SoftwareApplication softwareRequirements is undefined, not a text naming what pyproject\.toml requires/);
});

test('a requirement stated with a version longer than the one pyproject.toml gives fails, naming it', (t) => {
	const [first] = dependencies;
	const floor = ` ${first.clauses[0].version}`;
	assert.ok(softwareRequirements.includes(floor), softwareRequirements);
	const ran = history(t, {
		nodes: changedAll({
			SoftwareApplication: (node) => {
				node.softwareRequirements = softwareRequirements.replace(floor, `${floor}0`);
			},
		}),
	});
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		new RegExp(
			`FAIL SoftwareApplication softwareRequirements leaves out ${RegExp.escape(asWritten(first))}, ` +
				'which pyproject\\.toml gives \\(on 10 pages\\)',
		),
	);
});

test('every API page names the release and the Python it documents, and the check says so', (t) => {
	const ran = check(
		t,
		build({ base: { a: apiPage('signals/levels'), b: apiPage('filters/banks'), c: apiPage('room/acoustics') } }),
	);
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, new RegExp(`ok {3}all 3 API pages name the release ${RegExp.escape(VERSION)} and ${RegExp.escape(TARGET_PLATFORM)}`));
});

test('an API page that names no release, another release or another Python fails, with the pages it stands on', (t) => {
	const unnamed = apiPage('filters/banks');
	delete unnamed.article.assemblyVersion;
	delete unnamed.article.targetPlatform;
	const ran = check(
		t,
		build({
			base: {
				right: apiPage('signals/levels'),
				unnamed,
				old: apiPage('room/acoustics', { assemblyVersion: '3.3.0' }),
				python: apiPage('underwater/propagation', { targetPlatform: 'Python >= 3.11' }),
			},
		}),
	);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		new RegExp(
			'FAIL 1 API page\\(s\\) name the release undefined and the platform undefined, ' +
				`not ${RegExp.escape(VERSION)}, from VERSION, and ${RegExp.escape(TARGET_PLATFORM)}, from pyproject\\.toml`,
		),
	);
	assert.match(ran.err, /FAIL 1 API page\(s\) name the release "3\.3\.0" and the platform "Python >= 3\.12"/);
	assert.match(ran.err, /FAIL 1 API page\(s\) name the release "[^"]+" and the platform "Python >= 3\.11"/);
	assert.doesNotMatch(ran.out, /name the release/);
});

// ---------------------------------------------------------------------------
// The conformance report
// ---------------------------------------------------------------------------

test('a report whose Dataset is its main entity, versioned, dated by its data, based on named standards and written in each language passes', (t) => {
	const ran = check(t, build());
	assert.equal(ran.status, 0, ran.err);
	assert.match(
		ran.out,
		new RegExp(
			`ok {3}the conformance report's Dataset is the main entity of both report pages, versioned ${LIBRARY.replace(/\./g, '\\.')}, ` +
				'dated by the day its rows last changed, based on the 1 work the standards of its checks resolve to, named in each language, ' +
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
	built['en/report'].article.mainEntity.isBasedOn = [atCommit('scripts/conformance_report.py', 'blob')];
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

test('a report Dataset that leaves a text out, or leaves it empty, fails, and names it', (t) => {
	const built = build();
	const spanish = built['es/report'].article.mainEntity;
	delete spanish.variableMeasured[0].description;
	spanish.description = ' ';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/es\/reference\/conformance\/: the conformance report's Dataset writes no text for description, variableMeasured\[0\]\.description/,
	);
	assert.doesNotMatch(ran.err, /says in English/);
	assert.doesNotMatch(ran.err, /FAIL \/reference\/conformance\//);
});

test('a report Dataset with a column the other language does not describe fails, on both pages', (t) => {
	const built = build();
	const spanish = built['es/report'].article.mainEntity;
	spanish.variableMeasured.push({ '@type': 'PropertyValue', name: REPORT_TEXT.en.column[0], description: REPORT_TEXT.en.column[1] });
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL the conformance report's Dataset describes 1 column in English and 2 in Spanish/);
	assert.match(
		ran.err,
		/FAIL \/reference\/conformance\/: the conformance report's Dataset writes no text for variableMeasured\[1\]\.name, variableMeasured\[1\]\.description/,
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
	built['es/report'].text = '';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/es\/reference\/conformance\/: the conformance report's Dataset: the page prints no day its rows last changed \(\[data-report-provenance\] with a <time datetime>\)/,
	);
});

test("a report Dataset that hands out a file of another commit than the one its banner names fails, address by address", (t) => {
	const built = build();
	const english = built['en/report'].article.mainEntity;
	english.distribution[0].contentUrl = 'https://raw.githubusercontent.com/jmrplens/phonometry/main/docs/conformance.json';
	const spanish = built['es/report'].article.mainEntity;
	delete spanish.distribution;
	spanish.isBasedOn[0] = 'https://github.com/jmrplens/phonometry/blob/main/scripts/conformance_report.py';
	spanish.sameAs = 'https://github.com/jmrplens/phonometry/tree/main/docs';
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	const commit = RegExp.escape(DATA_COMMIT);
	assert.match(
		ran.err,
		new RegExp(
			"FAIL /reference/conformance/: the conformance report's Dataset: https://raw\\.githubusercontent\\.com/jmrplens/phonometry/main/docs/conformance\\.json " +
				`is of main, not of commit ${commit}, the one the page says its rows are of`,
		),
	);
	assert.match(ran.err, /FAIL \/es\/reference\/conformance\/: the conformance report's Dataset: it hands out no file of the report \(distribution\)/);
	assert.match(
		ran.err,
		new RegExp(
			"FAIL /es/reference/conformance/: the conformance report's Dataset: https://github\\.com/jmrplens/phonometry/blob/main/scripts/conformance_report\\.py " +
				`is of main, not of commit ${commit}`,
		),
	);
	assert.match(ran.err, /FAIL \/es\/reference\/conformance\/: the conformance report's Dataset: https:\/\/github\.com\/jmrplens\/phonometry\/tree\/main\/docs is of main/);
});

test('a report page that names no commit its rows are of fails', (t) => {
	const built = build();
	built['en/report'].text = built['en/report'].text.replace(/ data-report-commit="[^"]*"/, '');
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL \/reference\/conformance\/: the conformance report's Dataset: the page names no commit its rows are of \(\[data-report-provenance\] with a data-report-commit of 40 hexadecimal digits\)/,
	);
});
