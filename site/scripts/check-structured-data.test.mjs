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
// runs the check on it the way CI does. The pages come from
// shared/structured-data-fixture.mjs, whole unless a test breaks them, so the
// checks the whole site answers for elsewhere pass on every build here.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
	ABOUT_FILES,
	ABOUT_TEXT,
	aboutPage,
	commitDay,
	FIRST_COMMIT,
	LIBRARY_MODIFIED,
	page,
	PLATFORMS,
	runCheck,
	siteNodes,
} from './shared/structured-data-fixture.mjs';

/**
 * Build `pages` pages, the first `dated` of them published on `published`, and run the check on them.
 *
 * The first two pages are the About page in English and in Spanish, which the
 * check asks every build for; the rest are plain articles. `platforms` gives
 * the software node's `operatingSystem` on each page, by its index; null leaves
 * the property out, and a page past its end names the default platforms.
 */
function check(t, pages, dated, published = '2026-07-01', platforms = []) {
	const files = {};
	for (let i = 0; i < pages; i += 1) {
		const options = {
			datePublished: i < dated ? published : '2026-10-01',
			dateModified: '2026-10-01',
			nodes: siteNodes({ operatingSystem: i < platforms.length ? platforms[i] : PLATFORMS }),
		};
		if (i === 0) files[ABOUT_FILES.en] = aboutPage('en', options);
		else if (i === 1) files[ABOUT_FILES.es] = aboutPage('es', options);
		else files[`page-${i}/index.html`] = page(`page-${i}`, options);
	}
	return runCheck(t, files);
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

// The software's history and the About page. Every page carries the same
// site-wide nodes, so a defect in them is one line with the number of pages it
// stands on; the About page is asked for once in each language, typed as the
// page about the maintainer, and every span of years it writes, in whatever
// form, has to be the years of a role the Person node dates.

/**
 * Build the two About pages and eight articles, nine of the ten edited since
 * they were first published, and run the check on them.
 *
 * `nodes` are the site-wide nodes of every page. `about` replaces an About
 * page by its language: HTML to write instead, or null to leave it out.
 */
function history(t, { nodes = siteNodes(), about = {} } = {}) {
	const options = { datePublished: '2026-07-01', dateModified: '2026-10-01', nodes };
	const files = {};
	for (const lang of ['en', 'es']) {
		const html = lang in about ? about[lang] : aboutPage(lang, options);
		if (html !== null) files[ABOUT_FILES[lang]] = html;
	}
	for (let i = 2; i < 10; i += 1) files[`page-${i}/index.html`] = page(`page-${i}`, options);
	return runCheck(t, files);
}

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
	const options = { datePublished: '2026-07-01', dateModified: '2026-10-01' };
	const files = { [ABOUT_FILES.en]: aboutPage('en', options), [ABOUT_FILES.es]: aboutPage('es', options) };
	for (let i = 2; i < 10; i += 1) files[`page-${i}/index.html`] = page(`page-${i}`, options);
	files['page-2/index.html'] = page('page-2', {
		...options,
		nodes: siteNodes().filter((node) => node['@type'] !== 'SoftwareSourceCode'),
	});
	const ran = runCheck(t, files);
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
	const plain = history(t, {
		about: { en: aboutPage('en', { types: 'TechArticle', datePublished: '2026-07-01' }) },
	});
	assert.equal(plain.status, 1);
	assert.match(plain.err, /FAIL \/start\/about\/: the About page's article node is not typed AboutPage/);
	assert.doesNotMatch(plain.out, typed);
});

test('two English About pages are not the English one and its Spanish twin', (t) => {
	// start/about.html is served at /start/about/ as well.
	const options = { datePublished: '2026-07-01', dateModified: '2026-10-01' };
	const files = { [ABOUT_FILES.en]: aboutPage('en', options), 'start/about.html': aboutPage('en', options) };
	for (let i = 2; i < 10; i += 1) files[`page-${i}/index.html`] = page(`page-${i}`, options);
	const ran = runCheck(t, files);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL found 2 About page\(s\) in English and 0 in Spanish/);
	assert.doesNotMatch(ran.out, /typed AboutPage$/m);
});

test('an About page that dates the research role otherwise than the Person node fails, in either language', (t) => {
	const ran = history(t, {
		about: {
			en: aboutPage('en', {
				datePublished: '2026-07-01',
				text: '<p>I worked as an acoustics researcher at the UPV from 2020 to 2023.</p>',
			}),
			es: aboutPage('es', {
				datePublished: '2026-07-01',
				text: '<p>Trabajé como investigador en acústica en la UPV de 2020 a 2023.</p>',
			}),
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
const saying = (t, { en = ABOUT_TEXT.en, es = ABOUT_TEXT.es } = {}) =>
	history(t, {
		about: {
			en: aboutPage('en', { datePublished: '2026-07-01', text: en }),
			es: aboutPage('es', { datePublished: '2026-07-01', text: es }),
		},
	});

/** The failure a wrong span of `route`'s About page prints, up to the years. */
const wrongSpan = (route, span) => new RegExp(`FAIL ${route}: the page says "${span}", and no role the Person node dates`);

test('a wrong span beside right ones fails in every form a page writes years in, in any case', (t) => {
	const ran = saying(t, {
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
	const ran = saying(t, {
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
	const ran = saying(t);
	assert.equal(ran.status, 0, ran.err);
	assert.match(
		ran.out,
		/ok {3}the About page in English writes 2 spans of years, each the years of a role the Person node dates; 1 of them only by its end year, the node giving that role no start/,
	);
	const moved = saying(t, { en: ABOUT_TEXT.en.replace('2018-2019', '2018-2020') });
	assert.equal(moved.status, 1);
	assert.match(
		moved.err,
		/FAIL \/start\/about\/: the page says "2018-2020", and no role the Person node dates runs from 2018 to 2020 or ends in 2020 with no start given/,
	);
});

test("a year inside an identifier, an ORCID iD or a standard's number, is no span", (t) => {
	const ran = saying(t, {
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
			en: aboutPage('en', {
				datePublished: '2026-07-01',
				text:
					'<p>I worked as an acoustics researcher at the UPV from 2019 to 2023.</p>' +
					'<p>Before that I was a sound technician.</p>',
			}),
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
		about: {
			en: aboutPage('en', {
				datePublished: '2026-07-01',
				text: '<p>I worked as an acoustics researcher at the UPV for four years after my master.</p>',
			}),
		},
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
