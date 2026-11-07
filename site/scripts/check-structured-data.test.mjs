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
import {
	ABOUT_TEXT,
	aboutPage,
	build,
	check,
	commitDay,
	FIRST_COMMIT,
	LIBRARY_MODIFIED,
	ORIGIN,
	page,
	SITE_TYPES,
	siteNodes,
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
