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
// The glossary's terms are each held to the entry of src/data/glossary.mjs
// they are built from, and the real build only ever hands the check a
// glossary that passes.
//
// The site-wide graph is one block on the pages of both languages, so its
// descriptions, feature list and keywords are held to carry each text in
// English and in Spanish, the feature list one entry per topic that teaches,
// and no placeholder; its requirements are held to pyproject.toml, whatever floors and markers the
// file gives (scripts/shared/requirement-defects.test.mjs holds the sentence
// to the lines that give each Python a floor of its own), and every API page
// to the release and the Python it documents.
//
// Each test here writes a build of a few pages into a directory of its own and
// runs the check on it the way CI does. The pages come from
// shared/structured-data-fixture.mjs, whole unless a test breaks them, so the
// checks the whole site answers for elsewhere pass on every build here: a
// test takes a build, changes what it tests in place, and runs the check.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { glossary } from '../src/data/glossary.mjs';
import { glossaryTermSet } from '../src/lib/glossary-structured-data.mjs';
import { en as homeEn } from '../src/data/home.ts';
import { dependencies, extras, softwareRequirements } from '../src/data/repo-stats.mjs';
import { featureLists, siteDescriptions, softwareDescriptions } from '../src/data/scope.mjs';
import { domainIds, topics } from '../src/data/topics.mjs';
import {
	ABOUT_TEXT,
	aboutPage,
	apiPage,
	build,
	check,
	commitDay,
	FIRST_COMMIT,
	LIBRARY_MODIFIED,
	ORIGIN,
	page,
	SITE_TYPES,
	siteNodes,
	TARGET_PLATFORM,
	VERSION,
} from './shared/structured-data-fixture.mjs';

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

// The software's history and the About page. Every page carries the same
// site-wide nodes, so a defect in them is one line with the number of pages it
// stands on; the About page is asked for once in each language, typed as the
// page about the maintainer, and every span of years it writes, in whatever
// form, has to be the years of a role the Person node dates.

/**
 * Build the two About pages and eight articles, all ten edited since they
 * were first published, and run the check on them.
 *
 * `nodes`, when given, are the site-wide nodes of every page. `about` replaces
 * an About page by its language: another page to build instead, or null to
 * leave it out.
 */
function history(t, { nodes, about = {} } = {}) {
	const built = build();
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
	const built = build();
	built['page/2'].nodes = built['page/2'].nodes.filter((node) => node['@type'] !== 'SoftwareSourceCode');
	const ran = check(t, built);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL \/page-2\/: no SoftwareSourceCode node/);
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
