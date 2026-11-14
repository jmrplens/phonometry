// The structured data the site actually publishes.
//
// Every page carries a JSON-LD graph: the site-wide Person / WebSite /
// SoftwareApplication / SoftwareSourceCode nodes from astro.config.mjs, and a
// per-page article and breadcrumb trail from src/components/Head.astro. It is
// the only part of a page written for machines alone, and nothing in this
// repository read it. html-validate does not look inside a <script>, pa11y has
// no reason to, and the link checker sees no links there: a graph could stop
// being JSON, lose a required field or point at nothing at all and every check
// in the pipeline would stay green.
//
// It did. `Head.astro` resolved the section name from a map written out by
// hand beside the topic list, the signal chapter was renamed `signals` and
// only the list was swept, so all 54 pages of the signal analysis topic
// shipped with no `articleSection` for as long as nobody looked. The
// breadcrumb trail on those same pages named the section correctly throughout,
// because it reads src/data/topics.mjs.
//
// So this check reads topics.mjs too, and the built HTML, and nothing else: it
// derives what each page should say from its own URL and asserts it against
// what the page emits. A check that read Head.astro's idea of the answer would
// have agreed with the defect.
//
// The glossary's terms are held to src/data/glossary.mjs, the data the page
// is built from, field by field: a DefinedTerm is named by its entry's
// quantity, a symbol is its code and alternate name, a named entry's alternate
// name is the alias it declares, and the guide is the one the entry names.
// The code itself is not recomputed here: comparing it with what the page's
// own maths-to-text step produces would agree with that step's defects. It is
// held instead to the symbol it is written from, read from the symbol alone:
// it writes, in order, every Latin letter, digit, Greek letter, prime and sign
// the symbol writes as itself, a Greek letter's command being the letter, a
// function's its name, `\prime` the prime and a spacing command the space it
// sets, if any; and every Greek letter, named function, root and exponent the
// symbol writes is still in it, and so is every comma, less the thin spaces,
// which are spaces. A step that dropped every command it did not know wrote
// "s" for the absorption coefficient's "$\alpha_\mathrm{s}$" and "-1010" for
// "$-10\log_{10}$", and passed a check that only asked for no TeX and no
// blank; "wrong" for "$L_\mathrm{Aeq}$" passed one that only counted, since
// it writes no Greek letter, function, exponent or comma, and neither does
// the symbol. The description is held to the fields it is written from the
// same way: it writes what its definition writes, then what its unit writes,
// and ends on what its standard and clause write.
//
// Two things the built HTML cannot answer on its own are read from git: the
// SoftwareApplication's `dateCreated` is the UTC day of the repository's first
// commit, and its `dateModified` the UTC day of the last commit that changed
// the library under src/. The graph used to take the date of the commit at
// HEAD, so a dependency bump of the documentation site announced a library
// that had not moved.
//
// The site-wide graph is one block, the same on the pages of both languages,
// and every Spanish page used to publish it in English alone: the site's and
// the software's descriptions, a feature list of eleven of the thirteen topics
// that teach, and keywords that ended "no governing standard", the label the
// landing page shows where no standard governs an area. So each description
// has to be one text in English and one in Spanish, each tagged and each the
// text src/data/scope.mjs writes; the feature list has to give, in each
// language, one entry per topic in the order src/data/topics.mjs lists them,
// opening with the topic's own label there; no feature or keyword may
// publish the placeholder, and no keyword the bare name of an area that says
// nothing about acoustics on its own ("files"). The software's requirements
// are held to pyproject.toml, as src/data/repo-stats.mjs reads it: the Python
// it requires, every requirement as one phrase with its versions and the
// Python its marker limits it to, and every extra by name
// (scripts/shared/requirement-defects.mjs). Every API page has to name the
// release in VERSION and the Python pyproject.toml requires.
//
// The About page is held to the Person node it carries: every span of years
// the page writes, "(2011-2018)", "from 2019 to 2023", "de 2019 a 2023" or any
// other form `SPAN_FORMS` reads, has to be the years of a role that node
// dates, its start year included where the node gives one. The node comes from
// jmrp.io and the page is written here, and the two disagreed once, the page
// giving 2020 for a research role the node starts in 2019, with nothing to say
// so.
//
// The conformance report's Dataset is the one place the check reads more than
// the build: it joins docs/conformance.json with the pages' frontmatter
// (src/lib/conformance-evidence.mjs) to know which works the report's checks
// are based on, and holds the Dataset of each language to exactly those.
//
// Usage: node scripts/check-structured-data.mjs [dist-directory] [content-directory]
//          [--report=<conformance.json>] [--glossary=<glossary.mjs>]
//        (the content tree, the report and the glossary entries the build
//        was made from; by default the repository's)
import { execFileSync } from 'node:child_process';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { glossary } from '../src/data/glossary.mjs';
import { en as homeEn, es as homeEs } from '../src/data/home.ts';
import { dependencies, extras, requiresPython } from '../src/data/repo-stats.mjs';
import { featureLists, siteDescriptions, softwareDescriptions } from '../src/data/scope.mjs';
import { basePath, siteUrl } from '../src/data/site.mjs';
import { catalogueSlugs, domainIds, topicForSlug, topics, topicSections } from '../src/data/topics.mjs';
import { catalogues } from '../src/generated/catalogues.mjs';
import { knownSlugs } from '../src/lib/breadcrumbs.mjs';
import { isoDay } from '../src/lib/date-rules.mjs';
import { englishTwin, isApiRoute, isFallbackRoute } from '../src/lib/fallback-routes.mjs';
import { referenceId } from '../src/lib/citations.mjs';
import { SAME_WORKS, conformanceEvidence, governingDocuments } from '../src/lib/conformance-evidence.mjs';
import { readPageReferences } from '../src/lib/page-references.mjs';
import { requirementDefects } from './shared/requirement-defects.mjs';

import { decode, markupOf, markupText } from './shared/dist-pages.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
/** The value of `--name=value`, if given. */
const option = (name) => args.find((arg) => arg.startsWith(`--${name}=`))?.slice(name.length + 3);
const positional = args.filter((arg) => !arg.startsWith('--'));
// An explicit directory is for reproducing a defect against a build kept aside;
// with none, the check reads the build that is there.
const DIST = positional[0] ? resolve(positional[0]) : join(here, '..', 'dist');
// The pages whose frontmatter says what an errata page corrects and what
// each guide cites, and the conformance report: another directory and another
// report are for the tests of this check, which write pages of their own.
const CONTENT = positional[1] ? resolve(positional[1]) : join(here, '..', 'src', 'content', 'docs');
const REPORT_FILE = option('report') ? resolve(option('report')) : join(here, '..', '..', 'docs', 'conformance.json');
// The glossary entries the pages are held to, a module that exports `glossary`
// as src/data/glossary.mjs does; another module is for the tests of this
// check, which hold the pages to entries the site's own do not write.
const GLOSSARY_MODULE = option('glossary');
const GLOSSARY_GROUPS = GLOSSARY_MODULE ? (await import(pathToFileURL(resolve(GLOSSARY_MODULE)).href)).glossary : glossary;
const ORIGIN = `${siteUrl}${basePath}`;

const REPOSITORY_ROOT = join(here, '..', '..');

/**
 * The day in UTC of the last commit `git log` lists, as `YYYY-MM-DD`.
 *
 * The day is read from the commit's timestamp, not from the date the committer's
 * clock wrote: the site dates every page by the UTC day of its commit, and
 * astro.config.mjs dates the software the same way. The committer's own day
 * would date the repository's first commit, made at one in the morning two
 * hours ahead of UTC, a day after its UTC day, and a library change made
 * after midnight a day after the pages of the same commit.
 *
 * @param {string[]} args Arguments after `git -C <repository root> log`.
 * @param {string} what What the date is, for the error a missing history raises.
 * @returns {string} The day; a history that names no commit throws instead.
 */
const commitDay = (args, what) => {
	const printed = execFileSync('git', ['-C', REPOSITORY_ROOT, 'log', '--format=%ct', ...args], {
		encoding: 'utf8',
	})
		.trim()
		.split('\n')
		.at(-1);
	if (!/^\d+$/.test(printed ?? '')) {
		throw new Error(`git names no commit for ${what}: this check needs the repository history`);
	}
	return isoDay(new Date(Number(printed) * 1000));
};

// A shallow clone has a first commit of its own, the oldest one it fetched, and
// would hold the graph to that date instead of the repository's.
if (
	execFileSync('git', ['-C', REPOSITORY_ROOT, 'rev-parse', '--is-shallow-repository'], {
		encoding: 'utf8',
	}).trim() === 'true'
) {
	throw new Error('the repository is a shallow clone: this check needs its whole history (fetch-depth 0)');
}

/** The repository's first commit: the day the code was first published, as PyOctave. */
const FIRST_COMMIT = commitDay(['--max-parents=0', 'HEAD'], 'the first commit');
/** The last commit that changed the library itself, which is what the software's `dateModified` claims. */
const LIBRARY_MODIFIED = commitDay(['-1', '--', 'src'], 'the last change under src/');

/** The release the API pages document: the first line of VERSION, read here and not from the site's own reader. */
const VERSION = readFileSync(join(REPOSITORY_ROOT, 'VERSION'), 'utf8').trim();

/**
 * Whether `url` addresses a page of this site.
 *
 * The boundary matters: `basePath` is a path segment, not a prefix, so a
 * plain `startsWith(ORIGIN)` would also accept a sibling whose name merely
 * begins the same way, `/phonometry-old/` passing as `/phonometry/`. Nothing
 * emits such a URL today, but a check that accepts an address it was written
 * to reject reports success without having looked.
 *
 * @param {unknown} url The crumb's `item`, which may be absent or not a string.
 * @returns {boolean} True when the URL is this site's root or below it.
 */
const isOnThisSite = (url) => {
	const value = String(url ?? '');
	return value === ORIGIN || value.startsWith(`${ORIGIN}/`);
};

let failures = 0;
const fail = (message) => {
	console.error(`FAIL ${message}`);
	failures += 1;
};
const ok = (message) => console.log(`ok   ${message}`);

// The lookup the rest of this file rests on, pinned before it is used: a wrong
// answer here would not fail anything, it would make the check agree with
// whatever the site happens to emit.
//
// Every topic has to answer for its own landing page, which is what catches a
// prefix that shadows another, and the case that matters is the pair sharing a
// first segment: the API tree is its own topic and it lives inside the
// reference section's path, so `reference/api/...` must not fall through to
// Reference. Longest prefix first is what decides that, and it is the property
// the map this check replaced encoded as the order its keys were written in.
{
	let wrong = 0;
	for (const section of topicSections) {
		const got = topicForSlug(section.prefix)?.id;
		if (got !== section.id) {
			fail(`topics.mjs: the landing page of ${section.id} resolves to the topic ${got}`);
			wrong += 1;
		}
	}
	const NESTED = [
		['signals/filters/filter-banks', 'signals'],
		['reference/conformance', 'reference'],
		['reference/api/signals/levels', 'api'],
		['start/guides', 'start'],
		// Outside every topic: the home page and the error page.
		['', undefined],
		['404', undefined],
	];
	for (const [slug, id] of NESTED) {
		const got = topicForSlug(slug)?.id;
		if (got !== id) {
			fail(`topicForSlug(${JSON.stringify(slug)}) is ${got}, not ${id}`);
			wrong += 1;
		}
	}
	if (wrong === 0) {
		ok(`each of the ${topicSections.length} topics owns its own landing page, and reference/api resolves past reference`);
	}
}

/** Every .html file under `dir`, at any depth, as paths relative to DIST. */
function walk(dir, out = []) {
	for (const name of readdirSync(dir)) {
		const full = join(dir, name);
		if (statSync(full).isDirectory()) walk(full, out);
		else if (name.endsWith('.html')) out.push(relative(DIST, full).split(sep).join('/'));
	}
	return out;
}

/**
 * The route a built file is served at: `signals/levels/index.html` is
 * `/signals/levels/`, and the one page that is not an index, `404.html`, is
 * `/404/`. This is deliberately computed from the file tree rather than read
 * out of the page, so a page whose own `url` is wrong cannot hide it.
 */
function routeOf(file) {
	const withoutIndex = file.replace(/(^|\/)index\.html$/, '$1').replace(/\.html$/, '/');
	return `/${withoutIndex}`.replace(/\/{2,}/g, '/');
}

/** `@type` as an array, whichever of the two shapes a node uses. */
const typesOf = (node) => (Array.isArray(node['@type']) ? node['@type'] : [node['@type']]);

/** The one node of a page carrying `type`, or undefined. */
const nodeOfType = (nodes, type) => nodes.find((node) => typesOf(node).includes(type));

/** Fields every article node carries, whatever its type. */
const ARTICLE_FIELDS = [
	'about',
	'author',
	'dateModified',
	'datePublished',
	'description',
	'headline',
	'image',
	'inLanguage',
	'isPartOf',
	'mainEntityOfPage',
	'publisher',
	'speakable',
	'url',
	'wordCount',
];

/**
 * The share of articles that have to have been edited since they were first
 * published. A page added and never edited has the same two dates by right, so
 * no page can be judged alone, and about four in five differ in a good build. None
 * do where src/lib/page-dates.mjs had no history to read, because Head.astro falls
 * back to `dateModified`: every field is present, and every page claims it was
 * published on the day it was last edited.
 */
const EDITED_FLOOR = 0.1;

/** The nodes astro.config.mjs puts on every page for the per-page ones to join. */
const SITE_NODES = ['Person', 'WebSite', 'SoftwareApplication', 'SoftwareSourceCode'];

/**
 * The most bytes the site-wide ld+json block may take, the one astro.config.mjs
 * writes on every page around the Person it splices from jmrp.io verbatim.
 *
 * That Person is most of the block, and it changes when jmrp.io changes, with
 * no diff in this repository: four profile links added there grew every page
 * here by 132 bytes, and an earlier change there doubled the Person. The block
 * was 23,545 bytes on 2026-11-07, 16,320 of them the Person, and 30,804 once
 * it gave its descriptions, feature list and keywords in Spanish beside the
 * English and listed a feature for each topic that teaches. The budget leaves
 * room for a few more links or topics and none for a second copy of a list,
 * so a growth of that kind stops the build and is decided here, by raising the
 * budget or by trimming the source, instead of shipping on every page unseen.
 */
const SITE_BLOCK_BUDGET = 32_000;

/** `sameAs` as an array, whichever of the two shapes a node uses. */
const sameAsOf = (node) => (Array.isArray(node.sameAs) ? node.sameAs : [node.sameAs].filter(Boolean));

/**
 * What the software's own nodes get wrong about its history, one sentence per
 * defect, so the same defect on every page is reported once.
 *
 * Each expected value comes from somewhere other than astro.config.mjs: the
 * dates from git, the release notes and the archive from the node's own
 * repository, the help from the WebSite node the page defines, the old name's
 * package page from the node's own `alternateName`. A check that read the
 * config's idea of the answer would agree with whatever the config says.
 *
 * @param {object[]} nodes Every node of one page's graph.
 * @returns {string[]|undefined} The defects, empty when the history is whole;
 *   undefined when the page lacks one of the three nodes, which is reported as
 *   a missing node, so the page is not counted as read.
 */
function softwareDefects(nodes) {
	const app = nodeOfType(nodes, 'SoftwareApplication');
	const code = nodeOfType(nodes, 'SoftwareSourceCode');
	const site = nodeOfType(nodes, 'WebSite');
	if (!app || !code || !site) return undefined;
	const defects = [];
	if (app.dateCreated !== FIRST_COMMIT) {
		defects.push(
			`SoftwareApplication dateCreated is ${JSON.stringify(app.dateCreated)}, ` +
				`not ${FIRST_COMMIT}, the UTC day of the repository's first commit`,
		);
	}
	if (code.dateCreated !== FIRST_COMMIT) {
		defects.push(
			`SoftwareSourceCode dateCreated is ${JSON.stringify(code.dateCreated)}, ` +
				`not ${FIRST_COMMIT}, the UTC day of the repository's first commit`,
		);
	}
	if (app.dateModified !== LIBRARY_MODIFIED) {
		defects.push(
			`SoftwareApplication dateModified is ${JSON.stringify(app.dateModified)}, ` +
				`not ${LIBRARY_MODIFIED}, the UTC day of the last commit under src/`,
		);
	}
	if (typeof app.codeRepository !== 'string' || !app.codeRepository) {
		defects.push(
			"SoftwareApplication names no codeRepository, so its releaseNotes cannot be held to the repository's releases",
		);
	} else {
		const releases = `${app.codeRepository.replace(/\/$/, '')}/releases`;
		if (app.releaseNotes !== releases) {
			defects.push(`SoftwareApplication releaseNotes is ${JSON.stringify(app.releaseNotes)}, not ${releases}`);
		}
	}
	if (app.softwareHelp?.['@id'] !== site['@id']) {
		defects.push(
			`SoftwareApplication softwareHelp is ${JSON.stringify(app.softwareHelp)}, ` +
				`not the WebSite node ${site['@id']}`,
		);
	}
	if (typeof app.alternateName !== 'string' || !app.alternateName) {
		defects.push('SoftwareApplication names no alternateName, the former name its first releases carry');
	} else {
		const formerPackage = `https://pypi.org/project/${app.alternateName}/`;
		if (!sameAsOf(app).includes(formerPackage)) {
			defects.push(`SoftwareApplication sameAs leaves out ${formerPackage}, the package of its former name`);
		}
	}
	if (code.targetProduct?.['@id'] !== app['@id']) {
		defects.push(
			`SoftwareSourceCode targetProduct is ${JSON.stringify(code.targetProduct)}, ` +
				`not the SoftwareApplication ${app['@id']}`,
		);
	}
	if (typeof code.codeRepository !== 'string' || !code.codeRepository) {
		defects.push(
			"SoftwareSourceCode names no codeRepository, so its archivedAt cannot be held to the repository's archive",
		);
	} else {
		const archive = `${SOFTWARE_HERITAGE}${code.codeRepository}`;
		if (code.archivedAt !== archive) {
			defects.push(
				`SoftwareSourceCode archivedAt is ${JSON.stringify(code.archivedAt)}, not ${archive}, ` +
					'the Software Heritage archive of its repository',
			);
		}
	}
	return defects;
}

/**
 * Where Software Heritage shows the archive of a repository, given the
 * repository's URL after it. The archive keeps every visit of the origin under
 * this one address, so the link holds as new visits are made.
 */
const SOFTWARE_HERITAGE = 'https://archive.softwareheritage.org/browse/origin/?origin_url=';

/** The languages the site is written in, by the tag JSON-LD gives each. */
const LANGUAGES = ['en', 'es'];

/** What the landing page's standards cell says, in each language, of an area no standard governs. */
const PLACEHOLDERS = [homeEn.coverage.noStandard, homeEs.coverage.noStandard];

/**
 * The topics whose label says nothing about acoustics on its own: "Files" is
 * a word every program has. Named here, not read off the keyword the landing
 * page's row gives in its place, so that a row that loses its keyword fails
 * the check instead of taking the label off the list.
 */
const GENERIC_TOPICS = ['io'];

/**
 * The area names, in lower case and in both languages, that are not keywords
 * on their own: those of the topics above, and of every row of either landing
 * page that gives a keyword in its place. The site published "files" before.
 */
const BARE_LABELS = new Set([
	...GENERIC_TOPICS.flatMap((id) => LANGUAGES.map((lang) => topics.find((topic) => topic.id === id).label[lang].toLowerCase())),
	...[homeEn, homeEs].flatMap(({ coverage }) =>
		coverage.areas.filter((area) => area.keyword).map((area) => area.name.toLowerCase()),
	),
]);

/** The label of each topic that teaches, in the order the navigation lists them, by language. */
const TOPIC_LABELS = Object.fromEntries(
	LANGUAGES.map((lang) => [lang, domainIds.map((id) => topics.find((topic) => topic.id === id).label[lang])]),
);

/** A value cut to a length a failure line can carry. */
const shown = (value) => {
	const text = JSON.stringify(value);
	return text === undefined ? 'undefined' : text.length > 120 ? `${text.slice(0, 117)}...` : text;
};

/** Whether `value` is a text JSON-LD tags with one of the site's languages. */
const isTagged = (value) =>
	value !== null &&
	typeof value === 'object' &&
	typeof value['@value'] === 'string' &&
	value['@value'] !== '' &&
	LANGUAGES.includes(value['@language']);

/**
 * What a description gets wrong about the two languages: it has to be one
 * text in each, tagged, and the one src/data/scope.mjs writes there.
 *
 * @param {string} type The node's type, for the message.
 * @param {unknown} description The node's `description`.
 * @param {{en: string, es: string}} expected The text in each language.
 * @returns {string[]} The defects.
 */
function descriptionDefects(type, description, expected) {
	const literals = Array.isArray(description) ? description : [];
	const byLanguage = (lang) => literals.filter((literal) => isTagged(literal) && literal['@language'] === lang);
	if (literals.length !== 2 || !literals.every(isTagged) || LANGUAGES.some((lang) => byLanguage(lang).length !== 1)) {
		return [`${type} description is not one text in English and one in Spanish, each tagged with its language: ${shown(description)}`];
	}
	const [english, spanish] = LANGUAGES.map((lang) => byLanguage(lang)[0]['@value']);
	// Held apart from scope.mjs as well, which would agree with itself had it
	// handed the English text to both languages.
	if (english === spanish) return [`${type} description in Spanish is the English text: ${shown(spanish)}`];
	return LANGUAGES.filter((lang) => byLanguage(lang)[0]['@value'] !== expected[lang]).map(
		(lang) =>
			`${type} description in ${LANGUAGE[lang]} is not the ${LANGUAGE[lang]} text src/data/scope.mjs writes: ` +
			shown(byLanguage(lang)[0]['@value']),
	);
}

/**
 * What the software node's feature list gets wrong: in each language one
 * entry per topic that teaches, in the navigation's order and opening with
 * that topic's label, the list src/data/scope.mjs builds, and no placeholder
 * stated as a standard.
 *
 * @param {unknown} featureList The node's `featureList`.
 * @returns {string[]} The defects.
 */
function featureDefects(featureList) {
	const entries = Array.isArray(featureList) ? featureList : [featureList];
	const defects = [];
	const untagged = entries.filter((entry) => !isTagged(entry));
	if (untagged.length > 0) {
		defects.push(`SoftwareApplication featureList has ${untagged.length} entries tagged with no language of the site: ${shown(untagged[0])}`);
	}
	for (const lang of LANGUAGES) {
		const texts = entries.filter((entry) => isTagged(entry) && entry['@language'] === lang).map((entry) => entry['@value']);
		const labels = TOPIC_LABELS[lang];
		if (texts.length !== labels.length) {
			defects.push(
				`SoftwareApplication featureList in ${LANGUAGE[lang]} has ${texts.length} entries, ` +
					`not one for each of the ${labels.length} topics that teach`,
			);
		}
		const misplaced = labels.findIndex((label, i) => texts[i] !== undefined && !texts[i].startsWith(`${label}: `));
		if (misplaced >= 0) {
			defects.push(
				`SoftwareApplication featureList in ${LANGUAGE[lang]}, entry ${misplaced + 1} opens with ` +
					`${shown(texts[misplaced].split(':')[0])}, not with "${labels[misplaced]}", the topic topics.mjs lists there`,
			);
		}
		const differs = featureLists[lang].findIndex((feature, i) => texts[i] !== feature);
		if (texts.length > 0 && (differs >= 0 || texts.length !== featureLists[lang].length)) {
			const at = differs >= 0 ? differs : featureLists[lang].length;
			defects.push(
				`SoftwareApplication featureList in ${LANGUAGE[lang]} is not the list src/data/scope.mjs builds ` +
					`from the landing page: entry ${at + 1} is ${shown(texts[at])}`,
			);
		}
	}
	for (const placeholder of PLACEHOLDERS) {
		if (entries.some((entry) => String(entry?.['@value'] ?? entry).includes(placeholder))) {
			defects.push(`SoftwareApplication featureList states "${placeholder}" as a standard`);
		}
	}
	return defects;
}

/**
 * What the software node's keywords get wrong: each is a text, tagged with a
 * language of the site where it is written in words, none is the
 * placeholder an area with no governing standard shows, and none is the bare
 * name of an area that says nothing about acoustics on its own (BARE_LABELS).
 *
 * @param {unknown} keywords The node's `keywords`.
 * @returns {string[]} The defects.
 */
function keywordDefects(keywords) {
	const entries = Array.isArray(keywords) ? keywords : [keywords];
	const defects = [];
	const malformed = entries.filter((entry) => !(isTagged(entry) || (typeof entry === 'string' && entry !== '')));
	if (malformed.length > 0) defects.push(`SoftwareApplication keywords hold ${malformed.length} value(s) that are not a text: ${shown(malformed[0])}`);
	for (const lang of LANGUAGES) {
		if (!entries.some((entry) => isTagged(entry) && entry['@language'] === lang)) {
			defects.push(`SoftwareApplication keywords hold no keyword in ${LANGUAGE[lang]}`);
		}
	}
	// A keywords text is a list in itself, its entries delimited by commas, as
	// schema.org reads it: the site published one such text, ending in the
	// placeholder.
	const texts = entries.flatMap((entry) =>
		String(entry?.['@value'] ?? entry)
			.split(',')
			.map((text) => text.trim().toLowerCase()),
	);
	for (const placeholder of PLACEHOLDERS) {
		if (texts.includes(placeholder.toLowerCase())) defects.push(`SoftwareApplication keywords publish "${placeholder}" as a keyword`);
	}
	for (const label of BARE_LABELS) {
		if (texts.includes(label)) {
			defects.push(`SoftwareApplication keywords publish "${label}", the name of an area that says nothing about acoustics on its own`);
		}
	}
	return defects;
}

/**
 * What the site-wide nodes get wrong about the two languages and the package,
 * one sentence per defect, so the same defect on every page is reported once.
 *
 * @param {object[]} nodes Every node of one page's graph.
 * @returns {string[]|undefined} The defects; undefined when the page lacks the
 *   WebSite or the SoftwareApplication node, which is reported as a missing
 *   node, so the page is not counted as read.
 */
function languageDefects(nodes) {
	const site = nodeOfType(nodes, 'WebSite');
	const app = nodeOfType(nodes, 'SoftwareApplication');
	if (!site || !app) return undefined;
	return [
		...descriptionDefects('WebSite', site.description, siteDescriptions),
		...descriptionDefects('SoftwareApplication', app.description, softwareDescriptions),
		...featureDefects(app.featureList),
		...keywordDefects(app.keywords),
		...requirementDefects(app.softwareRequirements, { requiresPython, dependencies, extras }),
	];
}

/**
 * The years of every role a Person node dates with an end, wherever in the
 * node it sits: the schools it was at, the occupations it held, the bodies it
 * belonged to. A role dated by its end alone, a degree the node gives the
 * year it was awarded, has no start.
 *
 * @param {object} person The Person node.
 * @returns {{start: string|undefined, end: string}[]} The years of each dated role.
 */
function datedRoles(person) {
	const roles = [];
	const visit = (value) => {
		if (Array.isArray(value)) {
			value.forEach(visit);
			return;
		}
		if (!value || typeof value !== 'object') return;
		if (typesOf(value).some((type) => /Role$/.test(String(type))) && value.endDate) {
			roles.push({
				start: value.startDate ? String(value.startDate).slice(0, 4) : undefined,
				end: String(value.endDate).slice(0, 4),
			});
		}
		Object.values(value).forEach(visit);
	};
	visit(person);
	return roles;
}

/**
 * What a page says, as a reader reads it: the text of its main content (the
 * whole body when it has no `<main>`), without scripts, styles or markup, with
 * runs of white space as one space.
 */
const textOf = (html) => {
	const body =
		html.match(/<main\b[^>]*>([\s\S]*?)<\/main>/i)?.[1] ??
		html.match(/<body\b[^>]*>([\s\S]*)<\/body>/i)?.[1] ??
		html;
	return body
		.replace(/<(script|style|template)\b[\s\S]*?<\/\1>/gi, ' ')
		.replace(/<[^>]+>/g, ' ')
		.replace(/&nbsp;|&#160;|&#xa0;/gi, ' ')
		.replace(/&amp;/g, '&')
		.replace(/\s+/g, ' ');
};

/** A year of the last century or this one, which is every year the page can date a role by. */
const YEAR = String.raw`((?:19|20)\d{2})`;

/**
 * Every way a page writes the years a role ran, in either language and in any
 * case: two years joined by a dash, the second written whole or by its last
 * two digits ("2011-2018", "(2018–2019)", "2011-18"); "from 2019 to 2023"
 * (until, through); "between 2019 and 2023"; "de 2019 a 2023" ("del 2019 al
 * 2023"); "desde 2019 hasta 2023"; "entre 2019 y 2023". The dashes are every
 * one Unicode has between the hyphen and the horizontal bar, and the minus
 * sign. A year inside an identifier, an ORCID iD or a standard's number, is
 * not read: the dash form wants no letter, digit, dot, colon, slash or hyphen
 * on either side.
 */
const SPAN_FORMS = [
	new RegExp(String.raw`(?<![\w.:/-])${YEAR}\s*[-\u2010-\u2015\u2212]\s*(\d{4}|\d{2})(?![\w.:/-])`, 'giu'),
	new RegExp(String.raw`\bfrom\s+${YEAR}\s+(?:to|until|through)\s+${YEAR}\b`, 'giu'),
	new RegExp(String.raw`\bbetween\s+${YEAR}\s+and\s+${YEAR}\b`, 'giu'),
	new RegExp(String.raw`\bdel?\s+${YEAR}\s+al?\s+${YEAR}\b`, 'giu'),
	new RegExp(String.raw`\bdesde\s+${YEAR}\s+hasta\s+${YEAR}\b`, 'giu'),
	new RegExp(String.raw`\bentre\s+${YEAR}\s+y\s+${YEAR}\b`, 'giu'),
];

/**
 * Every span of years `text` writes, once each, as the page writes it and as
 * the two years it names. An end year written by its last two digits takes
 * the century of the start, and a "span" that would end before it starts is
 * not one.
 *
 * @param {string} text What the page says (`textOf`).
 * @returns {{span: string, start: string, end: string}[]} The spans, in the order the forms find them.
 */
function spansOf(text) {
	const spans = new Map();
	for (const form of SPAN_FORMS) {
		for (const [span, start, written] of text.matchAll(form)) {
			const end = written.length === 2 ? `${start.slice(0, 2)}${written}` : written;
			if (end < start) continue;
			spans.set(span.toLowerCase(), { span, start, end });
		}
	}
	return [...spans.values()];
}

/**
 * What the About page gets wrong about the years of the maintainer's roles,
 * against the Person node it carries.
 *
 * Every span of years the page writes, in any of the forms `SPAN_FORMS` reads,
 * has to be the years of a role the node dates: its end year a role's end
 * year, and its start year that role's start year where the node gives one.
 * Where the node dates a role by its end alone, a span ending that year is
 * held by its end year only, and the ok line says how many were. The page also
 * has to write at least one span: a page that dates no role leaves this check
 * nothing to hold. The page need not date every role it names; what it says
 * of today, it says without years.
 *
 * @param {object} person The Person node of the page.
 * @param {string} text What the page says (`textOf`).
 * @returns {{defects: string[], spans: number, endOnly: number}} The defects, how many distinct spans the
 *   page writes, and how many of them only a role's end year holds.
 */
function yearsDefects(person, text) {
	const roles = datedRoles(person);
	const defects = [];
	const spans = spansOf(text);
	let endOnly = 0;
	for (const { span, start, end } of spans) {
		const ending = roles.filter((role) => role.end === end);
		if (ending.some((role) => role.start === start)) continue;
		if (ending.some((role) => role.start === undefined)) {
			endOnly += 1;
			continue;
		}
		defects.push(
			`the page says "${span}", and no role the Person node dates runs from ${start} to ${end} ` +
				`or ends in ${end} with no start given`,
		);
	}
	if (spans.length === 0) {
		defects.push(
			`the page writes the years of none of the ${roles.length} roles the Person node dates, so they cannot be held to it`,
		);
	}
	return { defects, spans: spans.length, endOnly };
}

/** Each defect of the software's nodes, with the number of pages that carry it. */
const siteNodeDefects = new Map();

/** Every JSON-LD block of a document, whatever else the script tag carries. */
const LD_JSON = /<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g;

/**
 * Whether an `@id` is a work a page cites: a standard, book, paper, report or
 * web page defined on a bibliography page (src/lib/citations.mjs). The
 * bibliography's own article and the standards bodies hang off the same
 * address and are not works.
 */
const isCitedWork = (id) =>
	typeof id === 'string' && /\/reference\/bibliography\/#(?:std|doi|book|article|report|web)-/.test(id);

/**
 * The types src/lib/citations.mjs gives a cited work. A stub typed anything
 * else, an Organization say, is not naming a work, whatever its name says.
 */
const WORK_TYPES = new Set(['CreativeWork', 'Book', 'ScholarlyArticle', 'Report', 'WebPage']);

/** Whether a reference to a work says what the work is, not only where it is defined. */
const isNamed = (item) =>
	typeof item?.name === 'string' &&
	item.name.trim() !== '' &&
	item['@type'] !== undefined &&
	typesOf(item).every((type) => WORK_TYPES.has(type));

/**
 * The fields a page's stub shares with the bibliography's node for the same
 * work (src/lib/citations.mjs, `STUB_FIELDS`), compared value for value.
 * `sameAs` is compared apart: the Spanish bibliography adds the English node
 * to it, which a page's stub does not carry.
 */
const STUB_FIELDS = ['@type', 'name', 'identifier', 'reportNumber', 'url'];

/** A value as JSON with its keys in order, so two equal nodes compare equal. */
const canonical = (value) =>
	value === undefined
		? 'undefined'
		: JSON.stringify(value, (_, v) =>
				v && typeof v === 'object' && !Array.isArray(v)
					? Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b)))
					: v,
			);

/** Every object under `value` that refers to a cited work, in document order. */
function citedWorkReferences(value, out = []) {
	if (Array.isArray(value)) {
		for (const item of value) citedWorkReferences(item, out);
	} else if (value && typeof value === 'object') {
		if (isCitedWork(value['@id'])) out.push(value);
		for (const child of Object.values(value)) citedWorkReferences(child, out);
	}
	return out;
}

/**
 * Where every standards body is defined, once for both languages: the English
 * bibliography, whichever page names the body.
 */
const BODY_PREFIX = `${ORIGIN}/reference/bibliography/#org-`;
/** Where the English bibliography defines each standard. */
const ENGLISH_STANDARD_PREFIX = `${ORIGIN}/reference/bibliography/#std-`;
/**
 * The bodies that publish no texts of their own: the Spanish state issuers,
 * whose texts the Boletín Oficial del Estado prints and each of those
 * references links (src/lib/citations.mjs, STANDARDS_BODIES). Every other body
 * a standard names carries its official site.
 */
const BODIES_WITHOUT_SITE = new Set(
	['es-ministerio-de-la-presidencia', 'es-ministerio-de-fomento', 'es-jefatura-del-estado'].map(
		(id) => `${BODY_PREFIX}${id}`,
	),
);

/**
 * Words that tie a description to the catalogue page it was written on, in
 * either language: "this catalogue", "these catalogues", "este catálogo".
 */
const CATALOGUE_BOUND = /\b(?:this|these) catalogues?\b|\best(?:e|os) catálogos?(?![\p{L}])/iu;

/** The numbers of a designation, in order: what a translation of it leaves alone. */
const numbersOf = (designation) => (String(designation ?? '').match(/\d+/g) ?? []).join(' ');

/**
 * The catalogues the generator writes (src/generated/catalogues.mjs), each of
 * which a catalogue page of each language publishes as a Dataset.
 */
const CATALOGUE_KEYS = Object.keys(catalogues);

/**
 * The catalogue pages, by their route in either language: the list
 * src/data/topics.mjs keeps, which the sidebar, the finder and the build read
 * too. A route written here as a pattern would stay behind if they moved, and
 * every check of a dataset below would pass having read nothing.
 */
const CATALOGUE_PAGES = new Set(catalogueSlugs);

/**
 * The overview of the catalogues: the one page their sidebar group in
 * src/data/topics.mjs holds besides the catalogue pages themselves.
 *
 * @param {unknown[]} items A level of the navigation tree.
 * @returns {string | undefined} The overview's route, without the language.
 */
function catalogueOverviewIn(items) {
	for (const item of items) {
		if (!Array.isArray(item?.items)) continue;
		const slugs = item.items.map((entry) => (typeof entry === 'string' ? entry : entry?.slug));
		if (catalogueSlugs.every((slug) => slugs.includes(slug))) {
			const others = slugs.filter((slug) => slug !== undefined && !CATALOGUE_PAGES.has(slug));
			if (others.length !== 1) {
				throw new Error(
					`the sidebar group of the catalogue pages in src/data/topics.mjs holds ${others.length} other pages, ` +
						'and the overview of the catalogues is the one page it holds besides them',
				);
			}
			return others[0];
		}
		const found = catalogueOverviewIn(item.items);
		if (found !== undefined) return found;
	}
	return undefined;
}
const CATALOGUE_OVERVIEW = catalogueOverviewIn(topics);
if (CATALOGUE_OVERVIEW === undefined) {
	throw new Error('no sidebar group of src/data/topics.mjs lists the catalogue pages, so their overview is unknown');
}

/** The catalogue a node's `@id` names as `#dataset-<key>`, when it is one the generator writes. */
const datasetKeyOf = (id) => {
	const key = /#dataset-(\w+)$/.exec(String(id ?? ''))?.[1];
	return key !== undefined && key in catalogues ? key : undefined;
};

/** A heading that is a band and nothing else: `125 Hz`, `1,25 kHz`. */
const BAND_HEADING = /^\d+(?:[.,]\d+)? k?Hz$/;

/**
 * Fields a dataset of transcribed tables must not carry. The rows are read
 * off works that keep their own rights, so the site grants no licence over
 * them, and it serves them on the page and nowhere else.
 */
const DATASET_CLAIMS = ['license', 'contentUrl', 'distribution', 'encoding'];

/**
 * Text with what the site's typographer sets undone, its blanks one space:
 * remark-smartypants, which Astro runs on every page, curls the straight
 * quotes, sets three dots as an ellipsis and two hyphens as a dash. A dataset
 * says what the page's source says; the page sets it.
 */
const unset = (text) =>
	String(text)
		.replace(/[\u2018\u2019]/g, "'")
		.replace(/[\u201c\u201d]/g, '"')
		.replace(/\u2026/g, '...')
		.replace(/[\u2013\u2014]/g, '--')
		.replace(/[ \t\r\n]+/g, ' ')
		.trim();

/** The text a reader sees of an element's markup: its runs of text, its references decoded. */
const shownText = (inner) => unset(decode(markupText(inner)));

/**
 * What a page shows a dataset could be named or described by: the text of
 * its title and its `##` headings, and of its paragraphs.
 *
 * @param {string} html A built page.
 * @returns {{headings: Set<string>, paragraphs: Set<string>}}
 */
function pageTexts(html) {
	const markup = markupOf(html);
	return {
		headings: new Set([...markup.matchAll(/<h([12])\b[^>]*>([\s\S]*?)<\/h\1>/gi)].map(([, , inner]) => shownText(inner))),
		paragraphs: new Set([...markup.matchAll(/<p\b[^>]*>([\s\S]*?)<\/p>/gi)].map(([, inner]) => shownText(inner))),
	};
}

/** What each catalogue's columns call the variables a dataset of it measures, per language. */
const variableNames = (key, lang) =>
	new Set(
		catalogues[key].columns.map((column) =>
			lang === 'es' ? (column.quantityEs ?? column.headingEs) : (column.quantity ?? column.heading),
		),
	);

/**
 * The errata registry's index, and the one page under it that corrects no
 * work: the properties of the sources that look like misprints and are not
 * (NOT_ERRATA_SLUG in scripts/generate_site_reports.py). Every other page
 * under the index is the page of one document family.
 */
const ERRATA_INDEX = 'reference/errata';
const NOT_ERRATA = `${ERRATA_INDEX}/not-errata`;

/**
 * The fragments one errata page's frontmatter lists under `corrects`, in order.
 *
 * scripts/generate_site_reports.py writes the field one quoted fragment per
 * line, and nothing else writes it; a line under it in another shape, or the
 * field written on one line, is reported rather than read as nothing. The
 * page is read with its line endings normalised, as the build reads it: a
 * checkout with core.autocrlf=true, or the generator run on Windows, writes
 * it with CRLF.
 *
 * @param {string} file The page's path, for the report.
 * @returns {string[]} The fragments; none when the page has no `corrects`.
 */
function correctsOf(file) {
	const where = relative(join(here, '..'), file);
	const fence = /^---\n([\s\S]*?)\n---(?:\n|$)/.exec(readFileSync(file, 'utf8').replace(/\r\n?/g, '\n'));
	if (!fence) {
		fail(`${where}: an errata page with no frontmatter`);
		return [];
	}
	const lines = fence[1].split('\n');
	const at = lines.findIndex((line) => /^corrects\s*:/.test(line));
	if (at === -1) return [];
	if (lines[at] !== 'corrects:') fail(`${where}: corrects is written in a shape this check cannot read: ${lines[at]}`);
	const fragments = [];
	for (const line of lines.slice(at + 1)) {
		if (!/^\s/.test(line)) break;
		const item = /^ {2}- "([a-z0-9]+(?:-[a-z0-9]+)*)"$/.exec(line);
		if (item) fragments.push(item[1]);
		else fail(`${where}: a line of corrects this check cannot read: ${line.trim()}`);
	}
	return fragments;
}

/**
 * What the content tree holds under one language's errata index: whether the
 * index is there, and each page under it with the fragments it corrects.
 *
 * The build is held to it page for page: read from the build alone, a page
 * naming one of the six editions it corrects would pass as a page that names
 * a work, and a family page that stopped being built would pass as one that
 * was never written.
 *
 * @param {string} lang `en` or `es`.
 * @returns {{folder: string, index: boolean, pages: Map<string, string[]>}}
 */
function errataContent(lang) {
	const folder = join(CONTENT, ...(lang === 'es' ? ['es'] : []), ...ERRATA_INDEX.split('/'));
	const pages = new Map();
	let index = false;
	let names = [];
	try {
		names = readdirSync(folder).sort();
	} catch {
		// No errata folder in this language: nothing to hold the build to.
	}
	for (const name of names) {
		const page = /^(.+)\.mdx?$/.exec(name);
		if (!page) continue;
		if (page[1] === 'index') index = true;
		else pages.set(page[1], correctsOf(join(folder, name)));
	}
	return { folder: relative(join(here, '..'), folder), index, pages };
}
const errataPages = { en: errataContent('en'), es: errataContent('es') };

/** The route of the conformance report, without its locale. */
const REPORT = 'reference/conformance';

/**
 * The library the committed report was generated for: what the report's
 * Dataset has to give as its `version`. Read from the artefact, not from the
 * code that writes the Dataset.
 */
const CONFORMANCE = JSON.parse(readFileSync(REPORT_FILE, 'utf8'));
const REPORT_LIBRARY = CONFORMANCE.library;

/**
 * The day the report page prints as the one its rows last changed: the
 * `<time datetime>` of its `[data-report-provenance]` line, which
 * Conformance.astro writes from the last commit of docs/conformance.json.
 */
const provenanceLine = (html) => /<p\b[^>]*\bdata-report-provenance\b[^>]*>([\s\S]*?)<\/p>/.exec(html)?.[1];
const provenanceDay = (html) => {
	const line = provenanceLine(html);
	return line === undefined ? undefined : /<time\b[^>]*\bdatetime="(\d{4}-\d{2}-\d{2})"/.exec(line)?.[1];
};

/** The commit the report page names as the one its rows are of: the `data-report-commit` of the same line. */
const provenanceCommit = (html) => {
	const line = provenanceLine(html);
	return line === undefined ? undefined : /\bdata-report-commit="([0-9a-f]{40})"/.exec(line)?.[1];
};

/**
 * Every address into the repository a node holds, at any depth, with the ref
 * it is read at: the branch, tag or commit after `raw.githubusercontent.com/
 * <owner>/<repo>/` or after `github.com/<owner>/<repo>/{blob,tree,raw,commit}/`.
 */
const REPOSITORY_ADDRESS =
	/^https:\/\/(?:raw\.githubusercontent\.com\/jmrplens\/phonometry|github\.com\/jmrplens\/phonometry\/(?:blob|tree|raw|commit))\/([^/?#]+)/;
const repositoryAddresses = (node, found = []) => {
	if (typeof node === 'string') {
		const ref = REPOSITORY_ADDRESS.exec(node)?.[1];
		if (ref !== undefined) found.push([node, ref]);
	} else if (Array.isArray(node)) {
		for (const item of node) repositoryAddresses(item, found);
	} else if (node && typeof node === 'object') {
		for (const value of Object.values(node)) repositoryAddresses(value, found);
	}
	return found;
};

/** Every DOI a node gives as its `identifier`, whichever shape it uses. */
const doisOf = (node) =>
	[node?.identifier ?? []]
		.flat()
		.map((id) => (typeof id === 'object' ? id?.value : id))
		.filter((value) => typeof value === 'string' && /^10\.\S+$/.test(value));

/** The texts of the report's Dataset a reader of its language reads. */
const datasetTexts = (dataset) => ({
	name: dataset.name,
	description: dataset.description,
	measurementTechnique: dataset.measurementTechnique,
	...Object.fromEntries(
		[dataset.variableMeasured ?? []]
			.flat()
			.flatMap((variable, i) => [
				[`variableMeasured[${i}].name`, variable?.name],
				[`variableMeasured[${i}].description`, variable?.description],
			]),
	),
});

const files = walk(DIST).sort();
if (files.length === 0) throw new Error(`no HTML under ${DIST}: build the site first`);

// Tallies, so a check that silently stopped looking at anything says so.
const seen = {
	pages: 0,
	redirects: 0,
	blocks: 0,
	sections: 0,
	guides: 0,
	api: 0,
	fallbacks: 0,
	unlisted: 0,
	articles: 0,
	edited: 0,
	basedOn: 0,
	cited: 0,
	citing: 0,
	datasetBasis: 0,
	datasetDated: 0,
	datasetUndated: 0,
	datasetShown: 0,
	datasetUnshown: 0,
	corrected: 0,
	history: 0,
	languages: 0,
	definedTerms: 0,
	reports: 0,
};

/** The About pages found in each language, and how many of them are typed AboutPage. */
const about = { en: { found: 0, typed: 0 }, es: { found: 0, typed: 0 } };

/** Each distinct defect of the site-wide graph's languages and requirements, and the pages it stands on. */
const languageNodeDefects = new Map();
/** Each distinct release and platform an API page names, as JSON, and the pages that name it. */
const apiReleases = new Map();

/** Each language's name, as an ok line writes it. */
const LANGUAGE = { en: 'English', es: 'Spanish' };

/**
 * Every article node `@id` the build defines, whichever page defines it, so a
 * reference from another page can be resolved once every page has been read.
 */
const articleIds = new Set();

/** The glossary's references to the guides that compute each term, resolved after the walk. */
const glossarySubjects = [];
/** How many of the glossary's checks failed, so its summary line is only printed when none did. */
let glossaryDefects = 0;

/** Every glossary entry by its id: what each DefinedTerm of the built pages answers to. */
const GLOSSARY = new Map(GLOSSARY_GROUPS.flatMap((group) => group.terms).map((entry) => [entry.id, entry]));

/** The guides the glossary's entries name, each a route in either language. */
const GLOSSARY_GUIDES = new Set([...GLOSSARY.values()].map((entry) => entry.guide));

/**
 * The glossary pages found in each language, and how many of the guides its
 * entries name each language's pages publish.
 */
const glossaryPages = { en: { found: 0, guides: 0 }, es: { found: 0, guides: 0 } };

/** A field an entry stores once for both languages, or as `{ en, es }`, in `lang`. */
const fieldIn = (value, lang) =>
	value !== null && typeof value === 'object' && !Array.isArray(value) ? value[lang] : value;

/** The alternate name a named entry's declared aliases give in `lang`: none, one, or the list. */
const declaredAlias = (entry, lang) => {
	const aliases = [fieldIn(entry.alias, lang) ?? []].flat();
	return aliases.length > 1 ? aliases : aliases[0];
};

/** What is left of TeX in a string written for machines: a code has none of it. */
const TEX_IN_CODE = /[$\\{}^_]/;

/**
 * What is left of TeX in a description. A caret is not on the list: an
 * exponent with no superscript form is written `m/s^1.75`, on purpose.
 */
const TEX_IN_TEXT = /[$\\{}_]/;

/**
 * Where a dropped symbol leaves a hole: two spaces, a space before the
 * punctuation after it or after an opening bracket, or a text that starts
 * with a space, a punctuation mark or a prime.
 */
const HOLE = /\s{2}|\s[,.;:)]|\(\s|^[\s,.;:'′]/;

/**
 * The TeX commands for Greek letters, each with the letter it is. Each is a
 * letter of the Greek block in text, U+0370 to U+03FF, whatever the step that
 * writes it.
 */
const GREEK_LETTER_OF = Object.freeze({
	alpha: 'α', beta: 'β', gamma: 'γ', delta: 'δ', epsilon: 'ϵ', varepsilon: 'ε', zeta: 'ζ', eta: 'η', theta: 'θ',
	vartheta: 'ϑ', iota: 'ι', kappa: 'κ', lambda: 'λ', mu: 'μ', nu: 'ν', xi: 'ξ', pi: 'π', varpi: 'ϖ', rho: 'ρ',
	varrho: 'ϱ', sigma: 'σ', varsigma: 'ς', tau: 'τ', upsilon: 'υ', phi: 'ϕ', varphi: 'φ', chi: 'χ', psi: 'ψ',
	omega: 'ω', Gamma: 'Γ', Delta: 'Δ', Theta: 'Θ', Lambda: 'Λ', Xi: 'Ξ', Pi: 'Π', Sigma: 'Σ', Upsilon: 'Υ',
	Phi: 'Φ', Psi: 'Ψ', Omega: 'Ω',
});

/** The TeX commands for Greek letters. */
const GREEK_COMMANDS = Object.keys(GREEK_LETTER_OF);

/** A letter of the Greek block. */
const GREEK_LETTER = /[\u0370-\u03FF]/gu;

/** The named functions of TeX, each written as its name. */
const FUNCTION_COMMANDS = [
	'arccos', 'arcsin', 'arctan', 'arg', 'cos', 'cosh', 'cot', 'coth', 'csc', 'deg', 'det', 'dim', 'exp', 'gcd',
	'hom', 'inf', 'ker', 'lg', 'lim', 'liminf', 'limsup', 'ln', 'log', 'max', 'min', 'Pr', 'sec', 'sin', 'sinh',
	'sup', 'tan', 'tanh',
];

/** The characters a root, a relation or another symbol of TeX stands for, with the commands that write each. */
const SYMBOL_COMMANDS = new Map([
	['√', ['sqrt']],
	['∞', ['infty']],
	['∂', ['partial']],
	['≤', ['le', 'leq']],
	['≥', ['ge', 'geq']],
	['≠', ['ne', 'neq']],
	['≈', ['approx']],
	['±', ['pm']],
	['×', ['times']],
	['·', ['cdot']],
]);

/** A run of superscript characters, which is how a text writes an exponent that has them. */
const SUPERSCRIPT_RUN = /[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾]+/gu;

/** How many times `what`, a string or a global regular expression, occurs in `text`. */
const occurrences = (text, what) =>
	typeof what === 'string' ? text.split(what).length - 1 : (text.match(what) ?? []).length;

/** How many times the control word `\name` occurs in `source`, and not a longer one it begins. */
const commandCount = (source, name) => occurrences(source, new RegExp(`\\\\${name}(?![a-zA-Z])`, 'g'));

/** How many exponents a string writes: a caret each, or a run of superscript characters. */
const exponents = (text) => occurrences(text, /\^/g) + occurrences(text, SUPERSCRIPT_RUN);

/**
 * A superscript of primes alone, `^{\prime}` or `^\prime`, which TeX sets as
 * the prime: no exponent, and a text writes it as the prime.
 */
const PRIME_SUPERSCRIPT = /\^\s*(?:\{\s*(?:\\prime(?![a-zA-Z])\s*)+\}|\\prime(?![a-zA-Z]))/g;

/** The commas a text written from TeX keeps of its source: all of them, less the thin spaces `\,`. */
const keptCommas = (source) => occurrences(source, ',') - occurrences(source, '\\,');

/**
 * What a text lost of the fields it was written from, counted from those
 * fields alone: each Greek letter, named function, root or other symbol a
 * command stands for, and each exponent, is in the text at least as many
 * times as the fields write it, as a command or as the character itself. A
 * superscript of primes alone is the prime, and no exponent.
 *
 * @param {string} text The text the page publishes.
 * @param {string[]} sources The fields it is written from, with their inline maths.
 * @returns {string[]} What is missing, each said in a few words; empty when nothing is.
 */
function lostFrom(text, sources) {
	const source = sources.join('\n');
	// What of the source stands as written once its control words are taken out.
	const literal = source.replace(/\\[a-zA-Z]+/g, ' ');
	const lost = [];
	const greek =
		GREEK_COMMANDS.reduce((sum, name) => sum + commandCount(source, name), 0) + occurrences(literal, GREEK_LETTER);
	const greekWritten = occurrences(text, GREEK_LETTER);
	if (greekWritten < greek) lost.push(`${greek - greekWritten} of its ${greek} Greek letter(s)`);
	for (const name of FUNCTION_COMMANDS) {
		const commands = commandCount(source, name);
		if (commands > 0 && occurrences(text, name) < commands + occurrences(literal, name)) lost.push(`\\${name}`);
	}
	for (const [character, names] of SYMBOL_COMMANDS) {
		const commands = names.reduce((sum, name) => sum + commandCount(source, name), 0);
		if (commands > 0 && occurrences(text, character) < commands + occurrences(literal, character)) {
			lost.push(`the ${character} of \\${names[0]}`);
		}
	}
	const exponentsWanted = exponents(source) - occurrences(source, PRIME_SUPERSCRIPT);
	const exponentsWritten = exponents(text);
	if (exponentsWritten < exponentsWanted) lost.push(`${exponentsWanted - exponentsWritten} exponent(s)`);
	return lost;
}

/**
 * The two shapes of one letter, the superscript form of a digit or a sign, the
 * prime and the micro sign, each read as the one character a reader takes it
 * for.
 */
const SAME_CHARACTER = Object.freeze({
	'ϵ': 'ε', 'ϑ': 'θ', 'ϖ': 'π', 'ϱ': 'ρ', 'ς': 'σ', 'ϕ': 'φ', '−': '-', '⁻': '-', '⁺': '+', '⁼': '=',
	'⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '′': "'",
	'µ': 'μ',
});

/**
 * What a text writes as itself, in order: its Latin letters, digits, Greek
 * letters, primes and the marks + - = < > ! : ° %, each read as
 * SAME_CHARACTER reads it. These a step that writes maths as text copies from
 * its source. Spaces, brackets, slashes, carets, roots and dots are left out,
 * since the step writes them of its own for a fraction, a root, an exponent
 * or a product; a comma is held exactly by the comma count.
 */
const asItself = (text) =>
	(
		[...text]
			.map((character) => SAME_CHARACTER[character] ?? character)
			.join('')
			.match(/[\p{Script=Latin}\p{Nd}\u0370-\u03FF+\-=<>'!:°%]/gu) ?? []
	).join('');

/**
 * What a control word writes as itself: a Greek letter's command the letter,
 * a named function's its name, `\prime` the prime, and any other nothing.
 */
const controlWord = (name) => {
	if (Object.hasOwn(GREEK_LETTER_OF, name)) return GREEK_LETTER_OF[name];
	if (FUNCTION_COMMANDS.includes(name)) return ` ${name} `;
	return name === 'prime' ? '′' : ' ';
};

/**
 * What a control symbol, a backslash and the one character after it that is
 * no letter, writes as itself: `\,`, `\:`, `\>`, `\;` and a backslash before
 * a blank set a space, `\!` takes a thin space away and writes nothing, and
 * any other, `\%` or `\#`, is its character.
 */
const controlSymbol = (character) => (/^[\s,:>;]$/.test(character) ? ' ' : character === '!' ? '' : character);

/**
 * What a field of the entry writes as itself, read from the field alone and a
 * control sequence at a time, as TeX reads it: each control word and control
 * symbol as above, and everything else as written.
 */
const writtenAsItself = (source) =>
	asItself(
		source.replace(/\\(?:([a-zA-Z]+)|([^a-zA-Z]))/g, (_, name, character) =>
			name === undefined ? controlSymbol(character) : controlWord(name),
		),
	);

/** The first few items of a list, for a report line that stays one line. */
const sample = (list) => `${list.slice(0, 5).join(', ')}${list.length > 5 ? ', ...' : ''}`;

/**
 * Hold one glossary page's DefinedTerms to src/data/glossary.mjs, and fail
 * once for each kind of defect, with the terms it was found on.
 *
 * @param {string} route The page's route, which names it in the report.
 * @param {string} canonical The page's own address, every term's `@id` prefix.
 * @param {'en' | 'es'} lang The page's language.
 * @param {object[]} nodes Every node of the page's graph.
 */
function checkGlossary(route, canonical, lang, nodes) {
	/** What is wrong, said of some DefinedTerms, mapped to the terms it is wrong on. */
	const problems = new Map();
	const note = (what, where) => problems.set(what, [...(problems.get(what) ?? []), where]);
	const terms = nodeOfType(nodes, 'DefinedTermSet')?.hasDefinedTerm ?? [];
	seen.definedTerms += terms.length;
	if (terms.length === 0) {
		fail(`${route}: the glossary publishes no DefinedTerm`);
		glossaryDefects += 1;
		return;
	}
	const published = new Set();
	for (const term of terms) {
		const id = String(term['@id'] ?? '');
		const label = id.startsWith(`${canonical}#`) ? id.slice(canonical.length + 1) : `(${id || 'no @id'})`;
		const entry = GLOSSARY.get(label);
		if (!entry) {
			note('have no entry in src/data/glossary.mjs', label);
			continue;
		}
		if (published.has(label)) {
			note('are published more than once', label);
			continue;
		}
		published.add(label);

		// The name is the quantity, as the entry spells it in this language. The
		// one defect this check was written for, a term named by its symbol,
		// gets a message of its own because it is the one most likely to return.
		const quantity = entry.quantity[lang];
		if (term.name !== quantity) {
			const what =
				term.termCode !== undefined && term.name === term.termCode
					? 'are named by their termCode instead of the quantity'
					: 'are not named by the quantity their entry gives';
			note(what, `${label} (${JSON.stringify(term.name)}, not ${JSON.stringify(quantity)})`);
		}

		if (entry.symbol !== undefined) {
			// A symbol is the term's code and its alternate name, the same string,
			// read as a machine reads it: no TeX left, nothing blank, no hole,
			// nothing the symbol writes lost on the way, and the letters, digits,
			// Greek letters, primes and signs it writes those of the symbol, in
			// order.
			const code = term.termCode;
			const symbol = fieldIn(entry.symbol, lang);
			if (typeof code !== 'string' || code.trim() === '' || code !== code.trim()) {
				note('have a symbol and no usable termCode', `${label} (${JSON.stringify(code)})`);
			} else {
				if (TEX_IN_CODE.test(code)) note('carry TeX in their termCode', `${label} (${JSON.stringify(code)})`);
				if (HOLE.test(code)) {
					note('have a hole in their termCode where a symbol was dropped', `${label} (${JSON.stringify(code)})`);
				}
				const lost = lostFrom(code, [symbol]);
				if (lost.length > 0) {
					note(
						'have a termCode that lost what their symbol writes',
						`${label} (${JSON.stringify(code)}: ${lost.join(', ')})`,
					);
				}
				const commas = occurrences(code, ',');
				if (commas !== keptCommas(symbol)) {
					note(
						'have a termCode whose commas are not those of their symbol, a thin space read as one or a comma lost',
						`${label} (${JSON.stringify(code)}: ${commas}, the symbol ${keptCommas(symbol)})`,
					);
				}
				const written = writtenAsItself(symbol);
				if (asItself(code) !== written) {
					note(
						'have a termCode that does not write what their symbol writes',
						`${label} (${JSON.stringify(code)}, the symbol ${JSON.stringify(written)})`,
					);
				}
			}
			if (term.alternateName !== code) {
				note(
					'have an alternateName that is not their termCode',
					`${label} (${JSON.stringify(term.alternateName)} for ${JSON.stringify(code)})`,
				);
			}
		} else {
			if (term.termCode !== undefined) {
				note(
					'are named rather than symbolised and still carry a termCode',
					`${label} (${JSON.stringify(term.termCode)})`,
				);
			}
			const alias = declaredAlias(entry, lang);
			if (JSON.stringify(term.alternateName) !== JSON.stringify(alias)) {
				note(
					'carry an alternateName that is not the alias their entry declares',
					`${label} (${JSON.stringify(term.alternateName)} for ${JSON.stringify(alias)})`,
				);
			}
		}

		// A command the maths-to-text step does not know leaves a hole where it
		// stood, two spaces or a space before the punctuation after it, or the
		// TeX itself; and a symbol it drops cleanly, "-1010" for
		// "$-10\log_{10}$", is missing from the count of what the entry writes.
		// The description is the definition, the unit, then the standard and
		// the clause, these two joined by a comma: it opens on what the
		// definition writes as itself, ends on what the standard and the clause
		// write, and writes the unit's between them, read from the entry alone.
		const description = String(term.description ?? '');
		const fields = ['definition', 'unit', 'standard', 'clause'].map((field) => fieldIn(entry[field], lang) ?? '');
		const [, , standard, clause] = fields;
		const around = (at) => `${label} ("${description.slice(Math.max(0, at - 12), at + 8)}")`;
		if (description.trim() === '') note('have no description', label);
		else {
			const hole = HOLE.exec(description);
			if (hole) note('have a hole in their description where a symbol was dropped', around(hole.index));
			if (TEX_IN_TEXT.test(description)) note('carry TeX in their description', around(description.search(TEX_IN_TEXT)));
			const lost = lostFrom(description, fields);
			if (lost.length > 0) note('have a description that lost what their entry writes', `${label} (${lost.join(', ')})`);
			const commas = occurrences(description, ',');
			const kept = fields.reduce((sum, field) => sum + keptCommas(field), 0) + (standard && clause ? 1 : 0);
			if (commas !== kept) {
				note(
					'have a description whose commas are not those of their entry, a thin space read as one or a comma lost',
					`${label} (${commas}, the entry ${kept})`,
				);
			}
			const [definition, unit] = fields;
			const text = asItself(description);
			const opening = writtenAsItself(definition);
			const closing = writtenAsItself(standard) + writtenAsItself(clause);
			const between = text.length >= opening.length + closing.length ? text.slice(opening.length, text.length - closing.length) : undefined;
			if (!text.startsWith(opening) || !text.endsWith(closing) || between === undefined || !between.includes(writtenAsItself(unit))) {
				note('have a description that does not write what their entry writes', label);
			}
		}

		// The guide is the one the entry names, in the page's own language, and
		// the term points at the article node that page publishes.
		const url = `${ORIGIN}${lang === 'es' ? '/es' : ''}/${entry.guide}/`;
		const subject = term.subjectOf;
		if (subject === undefined) note('do not point at the guide that computes them', label);
		else if (subject.url !== url || subject['@id'] !== `${url}#article`) {
			note(
				"point at another page than their entry's guide, or not at its article node",
				`${label} (${JSON.stringify(subject['@id'])}, not ${url}#article)`,
			);
		} else if (typeof subject.name !== 'string' || subject.name.trim() === '') {
			note('point at their guide without naming it', label);
		} else {
			glossarySubjects.push({ route, term: label, target: subject['@id'] });
		}
	}
	for (const [what, where] of problems) {
		fail(`${route}: ${where.length} of ${terms.length} DefinedTerm(s) ${what}: ${sample(where)}`);
		glossaryDefects += 1;
	}
	const missing = [...GLOSSARY.keys()].filter((id) => !published.has(id));
	if (missing.length > 0) {
		fail(`${route}: ${missing.length} entr(y/ies) of src/data/glossary.mjs have no DefinedTerm: ${sample(missing)}`);
		glossaryDefects += 1;
	}
}

/** Every route the navigation tree lists (src/data/topics.mjs). */
const LISTED = new Set(knownSlugs());

/** The longest route above `slug` that the tree lists, or undefined. */
const listedParentOf = (slug) => {
	for (let route = slug; route.includes('/'); ) {
		route = route.slice(0, route.lastIndexOf('/'));
		if (LISTED.has(route)) return route;
	}
	return undefined;
};
const missingSection = [];
const wrongSection = [];
/** Each distinct `operatingSystem` of the software node, as JSON, and the pages that carry it. */
const platformLists = new Map();
/** Each distinct size of the site-wide block, in bytes, with the Person's share and the pages. */
const siteBlocks = new Map();
/** Pages whose `isBasedOn` points at a work without naming it, with the count. */
const unnamedBasis = [];
/** Pages that point at a cited work nothing on the page names, with the count. */
const unnamedCited = [];
/** Every reference to a cited work that says more than its `@id`, with its page. */
const stubs = [];
/** What each language's bibliography page defines, for the check across the two. */
const bibliographies = new Map();
/** Per language: each catalogue's dataset, by key, with the page that publishes it. */
const datasetsByLanguage = { en: new Map(), es: new Map() };
/** Per language: what the overview of the catalogues lists, by `@id`. */
const listedDatasets = { en: undefined, es: undefined };
/** Per language: how many catalogue pages the build holds. */
const cataloguePagesSeen = { en: 0, es: 0 };
/** Every dataset's link to its twin, checked once both languages are read. */
const datasetTwins = [];
/**
 * Per language: whether the errata index was built, every page built under
 * it, how many family pages and the works they name, the not-errata page.
 */
const errataSeen = {
	en: { index: false, built: new Set(), families: 0, corrected: 0, notErrata: false },
	es: { index: false, built: new Set(), families: 0, corrected: 0, notErrata: false },
};
/** Errata family pages whose `about` names no work they correct. */
const errataWithoutWorks = [];
/** Errata family pages whose `about` names other works than their `corrects`, with what differs. */
const errataMisnamed = [];
/** The Dataset each language's conformance report is about, for the check across the two. */
const reportDatasets = new Map();

for (const file of files) {
	const html = readFileSync(join(DIST, file), 'utf8');

	// The legacy redirect stubs are a <meta refresh> and nothing else. They
	// carry no graph on purpose and are not pages a reader lands on.
	if (/http-equiv="refresh"/.test(html)) {
		seen.redirects += 1;
		if (html.includes('application/ld+json')) {
			fail(`${file}: a redirect stub publishes structured data`);
		}
		continue;
	}
	seen.pages += 1;

	const route = routeOf(file);
	// A Spanish API page serves its English twin as fallback content and
	// publishes the English page's graph, naming the English address as its own
	// (src/lib/fallback-routes.mjs). That is the one way a page's graph may name
	// another address than its route, and it is checked as the twin's below.
	const own = isFallbackRoute(route) ? englishTwin(route) : route;
	if (own !== route) seen.fallbacks += 1;
	const lang = own.startsWith('/es/') ? 'es' : 'en';
	const slug = own.replace(/^\/(es\/)?/, '').replace(/\/$/, '');
	const canonical = `${ORIGIN}${own}`;
	const is404 = slug === '404';
	const isHome = slug === '';

	// Parsing is the whole point: a JSON-LD consumer reads each <script> as one
	// document, and a block that does not parse is not "mostly fine", it is a
	// page with no structured data at all.
	const blocks = [...html.matchAll(LD_JSON)];
	if (blocks.length === 0) {
		fail(`${route}: no application/ld+json block`);
		continue;
	}
	const nodes = [];
	let broken = false;
	for (const [, body] of blocks) {
		seen.blocks += 1;
		let doc;
		try {
			doc = JSON.parse(body);
		} catch (error) {
			fail(`${route}: an ld+json block is not valid JSON (${error.message})`);
			broken = true;
			continue;
		}
		// `null`, an array or a bare value parses and is still no JSON-LD
		// document, so it holds no node and is read as one that does not
		// parse: reading its @context would stop the whole check here.
		if (doc === null || typeof doc !== 'object' || Array.isArray(doc)) {
			fail(`${route}: an ld+json block is not a JSON-LD object`);
			broken = true;
			continue;
		}
		if (doc['@context'] !== 'https://schema.org') {
			fail(`${route}: an ld+json block declares @context ${JSON.stringify(doc['@context'])}`);
		}
		const graph = Array.isArray(doc['@graph']) ? doc['@graph'] : [doc];
		for (const node of graph) {
			if (!node || typeof node !== 'object' || !node['@type']) {
				fail(`${route}: a node in the graph has no @type`);
				continue;
			}
			nodes.push(node);
		}
		// The site-wide block is the one that carries the Person, measured as
		// published: the bytes every page pays before its own graph.
		const person = graph.find((node) => node && typeof node === 'object' && typesOf(node).includes('Person'));
		if (person) {
			const size = Buffer.byteLength(body, 'utf8');
			const entry = siteBlocks.get(size) ?? { person: Buffer.byteLength(JSON.stringify(person), 'utf8'), pages: 0 };
			entry.pages += 1;
			siteBlocks.set(size, entry);
		}
	}

	// What a page's valid blocks say holds whatever its other blocks do: a
	// consumer reads each block as a document of its own, so a malformed one
	// takes its own nodes out and leaves the others published. The two
	// readings below need nothing else, and they are made before a malformed
	// block ends the page. Everything after them asks for a node the page has
	// to carry, which the malformed block may have held.
	//
	// An `@id` names one thing. Two nodes sharing one on a page is a merge
	// conflict a consumer resolves by picking whichever it read last.
	const ids = nodes.map((node) => node['@id']).filter(Boolean);
	const duplicated = ids.filter((id, i) => ids.indexOf(id) !== i);
	if (duplicated.length > 0) {
		fail(`${route}: ${[...new Set(duplicated)].join(', ')} defined more than once`);
	}
	const software = nodeOfType(nodes, 'SoftwareApplication');
	if (software) {
		const platforms = JSON.stringify(software.operatingSystem ?? null);
		platformLists.set(platforms, (platformLists.get(platforms) ?? 0) + 1);
	}
	if (broken) continue;

	for (const type of SITE_NODES) {
		if (!nodeOfType(nodes, type)) fail(`${route}: no ${type} node`);
	}

	const history = softwareDefects(nodes);
	if (history) seen.history += 1;
	for (const defect of history ?? []) {
		siteNodeDefects.set(defect, (siteNodeDefects.get(defect) ?? 0) + 1);
	}
	const spoken = languageDefects(nodes);
	if (spoken) seen.languages += 1;
	for (const defect of spoken ?? []) {
		languageNodeDefects.set(defect, (languageNodeDefects.get(defect) ?? 0) + 1);
	}

	// The About page says who maintains the library and how its numbers are
	// made, and schema.org has a type for exactly that page.
	if (slug === 'start/about') {
		about[lang].found += 1;
		const typed = nodes.some(
			(node) => node['@id'] === `${canonical}#article` && typesOf(node).includes('AboutPage'),
		);
		if (typed) about[lang].typed += 1;
		else fail(`${route}: the About page's article node is not typed AboutPage`);
		const person = nodeOfType(nodes, 'Person');
		if (person) {
			const { defects, spans, endOnly } = yearsDefects(person, textOf(html));
			for (const defect of defects) fail(`${route}: ${defect}`);
			if (defects.length === 0) {
				const byEnd =
					endOnly === 0
						? ''
						: `; ${endOnly} of them only by its end year, the node giving ` +
							`${endOnly === 1 ? 'that role' : 'those roles'} no start`;
				ok(
					`the About page in ${LANGUAGE[lang]} writes ${spans} span${spans === 1 ? '' : 's'} ` +
						`of years, each the years of a role the Person node dates${byEnd}`,
				);
			}
		}
	}

	// The glossary publishes one DefinedTerm per entry, and each is quoted on
	// its own. It used to be named by its symbol alone, the same string as its
	// termCode, so the node for LAeq never said "A-weighted equivalent
	// continuous sound pressure level"; and the guide it points at named no
	// `@id`, so nothing joined it to the article that guide publishes.
	if (slug === 'reference/glossary') {
		glossaryPages[lang].found += 1;
		checkGlossary(route, canonical, lang, nodes);
	}
	if (GLOSSARY_GUIDES.has(slug)) glossaryPages[lang].guides += 1;

	// The error page is not an article and must not be indexed as one, which is
	// the whole reason Head.astro special-cases it.
	if (is404) {
		for (const type of ['TechArticle', 'APIReference', 'BreadcrumbList']) {
			if (nodeOfType(nodes, type)) fail(`${route}: the error page publishes a ${type} node`);
		}
		continue;
	}

	if (isHome) {
		const page = nodeOfType(nodes, 'WebPage');
		if (!page) fail(`${route}: the home page has no WebPage node`);
		else {
			if (page['@id'] !== `${canonical}#webpage`) {
				fail(`${route}: WebPage @id is ${page['@id']}, not ${canonical}#webpage`);
			}
			if (page.inLanguage !== lang) {
				fail(`${route}: WebPage inLanguage is ${JSON.stringify(page.inLanguage)}, not ${lang}`);
			}
			if (!page.speakable) fail(`${route}: the home page names no speakable selector`);
		}
		continue;
	}

	// Every other page is an article of some kind.
	const article = nodes.find((node) =>
		typesOf(node).some((type) => ['TechArticle', 'APIReference', 'CollectionPage'].includes(type)),
	);
	if (!article) {
		fail(`${route}: no TechArticle, APIReference or CollectionPage node`);
		continue;
	}
	for (const field of ARTICLE_FIELDS) {
		if (article[field] === undefined) fail(`${route}: the article node has no ${field}`);
	}
	seen.articles += 1;
	if (article.datePublished && article.dateModified && article.dateModified > article.datePublished) {
		seen.edited += 1;
	}
	if (article['@id'] !== `${canonical}#article`) {
		fail(`${route}: article @id is ${article['@id']}, not ${canonical}#article`);
	}
	if (article.url !== canonical) fail(`${route}: article url is ${article.url}, not ${canonical}`);
	articleIds.add(article['@id']);
	if (article.inLanguage !== lang) {
		fail(`${route}: article inLanguage is ${JSON.stringify(article.inLanguage)}, not ${lang}`);
	}

	// The per-page nodes join the site-wide ones by `@id`. A reference that
	// resolves to nothing on the page that makes it is the failure the single
	// `@graph` in Head.astro exists to prevent: a plain JSON-LD processor
	// expands each script as its own document, and there the target is a node
	// with no properties at all. (`about` goes on to name the works the page
	// implements, which the check of cited works below holds to the same.)
	const defined = new Set(ids);
	const joins = {
		author: article.author,
		publisher: article.publisher,
		isPartOf: article.isPartOf,
		about: Array.isArray(article.about) ? article.about[0] : article.about,
	};
	for (const [key, value] of Object.entries(joins)) {
		const target = value?.['@id'];
		if (target && !defined.has(target)) {
			fail(`${route}: article ${key} points at ${target}, which no node on the page defines`);
		}
	}

	// The works the page cites, named on the page. They used to be bare `@id`s
	// into the bibliography, which defines them on a page of its own: the
	// reader this markup is for takes one document at a time, and there the
	// standard a guide is based on was an address with nothing at it. The first
	// reference to a work in `isBasedOn` says what it is, with its type and
	// name; a later one may point back. Every other reference, in `about` and
	// `citation`, has to resolve to a work named somewhere on the same page.
	const references = citedWorkReferences(article);
	if (references.length > 0) seen.citing += 1;
	for (const item of references) {
		if (Object.keys(item).some((key) => key !== '@id')) stubs.push({ route, item });
	}
	const namedHere = new Set(references.filter(isNamed).map((item) => item['@id']));
	const firstInBasis = new Set();
	let bareBasis = 0;
	for (const item of [article.isBasedOn ?? []].flat()) {
		const id = item?.['@id'];
		if (!isCitedWork(id) || firstInBasis.has(id)) continue;
		firstInBasis.add(id);
		seen.basedOn += 1;
		if (!isNamed(item)) bareBasis += 1;
	}
	if (bareBasis > 0) unnamedBasis.push([route, bareBasis]);
	const works = new Set(references.map((item) => item['@id']));
	seen.cited += works.size;
	const unnamed = [...works].filter((id) => !namedHere.has(id));
	if (unnamed.length > 0) unnamedCited.push([route, unnamed.length]);

	// Every published catalogue is a Dataset of the page that renders it, and
	// the overview of the catalogues is the DataCatalog that lists them
	// (src/lib/catalogue-datasets.mjs). Read here off what was built: each
	// dataset is the article's main entity, points at its table on the page,
	// names the variables its columns hold and the works its rows were read
	// from, is dated as its page, and claims no licence over rows other works
	// printed. The count across the pages, every catalogue the generator
	// writes once in each language, is checked after the loop.
	if (CATALOGUE_PAGES.has(slug)) {
		cataloguePagesSeen[lang] += 1;
		/** What the page shows, read once a dataset needs it. */
		let pageText;
		const datasets = nodes.filter((node) => typesOf(node).includes('Dataset'));
		if (datasets.length === 0) fail(`${route}: a catalogue page publishes no Dataset`);
		const mainEntities = [article.mainEntity ?? []].flat().map((item) => item?.['@id']);
		const datasetIds = datasets.map((node) => node['@id']);
		if (JSON.stringify(mainEntities) !== JSON.stringify(datasetIds)) {
			fail(
				`${route}: the article's mainEntity is ${JSON.stringify(mainEntities)}, not the page's datasets ` +
					`${JSON.stringify(datasetIds)}`,
			);
		}
		for (const dataset of datasets) {
			const id = String(dataset['@id']);
			const key = id.startsWith(`${canonical}#dataset-`) ? id.slice(`${canonical}#dataset-`.length) : undefined;
			if (!key || !(key in catalogues)) {
				fail(`${route}: a Dataset's @id, ${dataset['@id']}, names no catalogue the generator writes`);
				continue;
			}
			const seenOn = datasetsByLanguage[lang].get(key);
			if (seenOn) fail(`${route}: the catalogue ${key} is a Dataset of ${seenOn.route} as well`);
			datasetsByLanguage[lang].set(key, { route, node: dataset });
			const at = `${route} ${key}`;
			if (dataset.url !== `${canonical}#catalogue-${key}`) {
				fail(`${at}: the dataset's url is ${dataset.url}, not its table, ${canonical}#catalogue-${key}`);
			} else if (!html.includes(`id="catalogue-${key}"`)) {
				fail(`${at}: the dataset's url points at #catalogue-${key}, and the page holds no such table`);
			}
			for (const field of ['name', 'description']) {
				if (typeof dataset[field] !== 'string' || dataset[field].trim() === '') {
					fail(`${at}: the dataset has no ${field}`);
				}
			}
			// What a dataset says is what its page shows: its name is the page's
			// title or the `##` heading of its section, and its description a
			// paragraph of the page, or the page's own description where the page
			// renders one catalogue alone. Read off the built page, so a reading of
			// the page's source that took markup for text, or the lines of an
			// admonition for a paragraph (its `:::` markers are no text the page
			// shows), fails here whatever the reader did. Any paragraph of the page
			// counts, one an aside holds too, written `:::note` or `<Aside>`, and one
			// of a list: the tags of an `<Aside>` are markup the reader drops, so
			// its lines read as the paragraph it holds. Keeping those out is the
			// reader's part, src/lib/catalogue-datasets.mjs and its tests.
			pageText ??= pageTexts(html);
			const nameShown = pageText.headings.has(unset(dataset.name ?? ''));
			const descriptionShown =
				pageText.paragraphs.has(unset(dataset.description ?? '')) ||
				(datasets.length === 1 && dataset.description === article.description);
			if (!nameShown) fail(`${at}: the dataset's name, ${JSON.stringify(dataset.name)}, is no heading of its page`);
			if (!descriptionShown) {
				fail(
					`${at}: the dataset's description is no paragraph of its page` +
						`${datasets.length === 1 ? ' and not its description' : ''}: ` +
						JSON.stringify(String(dataset.description ?? '').slice(0, 120)),
				);
			}
			seen[nameShown && descriptionShown ? 'datasetShown' : 'datasetUnshown'] += 1;
			// A page of several catalogues describes them all, so its description
			// says of one dataset what belongs to another.
			if (datasets.length > 1 && dataset.description === article.description) {
				fail(`${at}: the dataset takes the page's description, which speaks of all ${datasets.length} catalogues it renders`);
			}
			if (dataset.inLanguage !== lang) {
				fail(`${at}: the dataset's inLanguage is ${JSON.stringify(dataset.inLanguage)}, not ${lang}`);
			}
			const claims = DATASET_CLAIMS.filter((field) => dataset[field] !== undefined);
			if (claims.length > 0) {
				fail(`${at}: the dataset claims ${claims.join(', ')} over rows other works printed`);
			}
			const overview = `${ORIGIN}${lang === 'es' ? '/es' : ''}/${CATALOGUE_OVERVIEW}/#article`;
			if (dataset.includedInDataCatalog?.['@id'] !== overview) {
				fail(`${at}: the dataset is included in ${dataset.includedInDataCatalog?.['@id']}, not ${overview}`);
			}
			// A dataset is its page's text and the rows the page renders, so it
			// changed when its page did: it carries the article's dateModified.
			if (typeof dataset.dateModified !== 'string' || dataset.dateModified !== article.dateModified) {
				fail(
					`${at}: the dataset's dateModified is ${JSON.stringify(dataset.dateModified)}, not its page's ` +
						`${JSON.stringify(article.dateModified)}`,
				);
				seen.datasetUndated += 1;
			} else {
				seen.datasetDated += 1;
			}
			const twinKey = lang === 'en' ? 'workTranslation' : 'translationOfWork';
			datasetTwins.push({ at, lang, key, twin: dataset[twinKey]?.['@id'] });
			// The variables are the columns: every column names one, by its
			// quantity where the page heads it by its band alone, and a band is
			// never a variable's whole name.
			const variables = [dataset.variableMeasured ?? []].flat();
			const named = new Set(
				variables.filter((item) => typesOf(item ?? {}).includes('PropertyValue')).map((item) => item.name),
			);
			const missing = [...variableNames(key, lang)].filter((name) => !named.has(name));
			if (variables.length === 0 || missing.length > 0) {
				fail(
					`${at}: the dataset's variableMeasured names ${variables.length === 0 ? 'nothing' : `no variable for ${missing.join(', ')}`}`,
				);
			}
			const bands = [...named].filter((name) => BAND_HEADING.test(String(name)));
			if (bands.length > 0) fail(`${at}: variables named by a band alone: ${bands.join(', ')}`);
			// The works its rows were read from, each named where the dataset names
			// it, and held to what the bibliography says of it like any other stub.
			const basis = [dataset.isBasedOn ?? []].flat();
			if (basis.length === 0) fail(`${at}: the dataset names no work it is based on`);
			for (const item of basis) {
				if (!isCitedWork(item?.['@id']) || !isNamed(item)) {
					fail(`${at}: the dataset is based on ${item?.['@id'] ?? JSON.stringify(item)} without naming it`);
				} else {
					stubs.push({ route, item });
					seen.datasetBasis += 1;
				}
			}
		}
	} else {
		// Nowhere else does a catalogue's dataset or table appear: a catalogue
		// page that sits at a route topics.mjs does not list would leave every
		// check above with nothing to read, and the build green.
		const strayDatasets = nodes.filter((node) => typesOf(node).includes('Dataset') && datasetKeyOf(node['@id']));
		const strayTables = CATALOGUE_KEYS.filter((key) => html.includes(`id="catalogue-${key}"`));
		if (strayDatasets.length > 0 || strayTables.length > 0) {
			fail(
				`${route}: publishes ${strayDatasets.length} catalogue dataset(s) and holds ${strayTables.length} catalogue ` +
					`table(s) (first: ${[...strayDatasets.map((node) => node['@id']), ...strayTables].slice(0, 3).join(', ')}), ` +
					'and is not a catalogue page of catalogueSlugs in src/data/topics.mjs',
			);
		}
	}
	// An errata page is about the works its entries correct, and says so in
	// `about`, beside the software (src/lib/citations.mjs, correctedWorks).
	// Every one of them used to name the software alone, so to a search
	// engine 95 pages per language were about phonometry and about none of
	// the documents they correct. Each family page names the works its
	// `corrects` lists, those and no others, in that order, on its own
	// language's bibliography; the page of properties that are not errata
	// corrects nothing and names none. Whether each is named as the
	// bibliography describes it is the check of every stub, below.
	if (slug === ERRATA_INDEX) errataSeen[lang].index = true;
	if (slug.startsWith(`${ERRATA_INDEX}/`)) {
		const name = slug.slice(ERRATA_INDEX.length + 1);
		const corrects = errataPages[lang].pages.get(name);
		errataSeen[lang].built.add(name);
		if (corrects === undefined) {
			fail(`${route}: an errata page with no page under ${errataPages[lang].folder} to say what it corrects`);
		}
		const [software, ...rest] = [article.about ?? []].flat();
		const works = rest.filter((item) => isCitedWork(item?.['@id']));
		const ownBibliography = `${ORIGIN}${lang === 'es' ? '/es' : ''}/reference/bibliography/#`;
		const application = nodeOfType(nodes, 'SoftwareApplication')?.['@id'];
		if (software?.['@id'] !== application) {
			fail(`${route}: the errata page's about opens with ${software?.['@id']}, not the software, ${application}`);
		}
		if (rest.length !== works.length) {
			fail(`${route}: the errata page's about names ${rest.length - works.length} thing(s) that are not a cited work`);
		}
		if (slug === NOT_ERRATA) {
			errataSeen[lang].notErrata = true;
			if (works.length > 0) {
				fail(`${route}: the page of properties that are not errata corrects nothing and names ${works.length} work(s) in about`);
			}
		} else {
			errataSeen[lang].families += 1;
			errataSeen[lang].corrected += works.length;
			if (works.length === 0) errataWithoutWorks.push(route);
			seen.corrected += works.length;
			const named = works.map((item) => String(item['@id']));
			const listed = (corrects ?? []).map((fragment) => `${ownBibliography}${fragment}`);
			const at = named.findIndex((id, i) => id !== listed[i]);
			if (works.length > 0 && corrects !== undefined && (at !== -1 || named.length !== listed.length)) {
				const position = at === -1 ? Math.min(named.length, listed.length) : at;
				errataMisnamed.push(
					`${route} names ${named.length} work(s) and its corrects lists ${listed.length}; at position ` +
						`${position + 1} it names ${named[position] ?? 'nothing'} where corrects lists ${listed[position] ?? 'nothing'}`,
				);
			}
			const foreign = works.filter((item) => !String(item['@id']).startsWith(ownBibliography));
			if (foreign.length > 0) {
				fail(
					`${route}: the errata page names ${foreign.length} work(s) it corrects on another language's ` +
						`bibliography (first: ${foreign[0]['@id']})`,
				);
			}
		}
	}

	if (slug !== CATALOGUE_OVERVIEW && nodes.some((node) => typesOf(node).includes('DataCatalog'))) {
		fail(`${route}: publishes a DataCatalog, and is not the overview of the catalogues, ${CATALOGUE_OVERVIEW}`);
	}
	if (slug === CATALOGUE_OVERVIEW) {
		if (!typesOf(article).includes('DataCatalog')) {
			fail(`${route}: the overview of the catalogues is typed ${JSON.stringify(article['@type'])}, not a DataCatalog`);
		}
		const listed = new Map();
		for (const item of [article.dataset ?? []].flat()) {
			if (!typesOf(item ?? {}).includes('Dataset') || typeof item.name !== 'string' || item.name === '') {
				fail(`${route}: the DataCatalog lists ${item?.['@id'] ?? JSON.stringify(item)} without naming it as a Dataset`);
			}
			listed.set(item?.['@id'], item);
		}
		if (DATASET_CLAIMS.some((field) => article[field] !== undefined)) {
			fail(`${route}: the DataCatalog claims ${DATASET_CLAIMS.filter((field) => article[field] !== undefined).join(', ')}`);
		}
		listedDatasets[lang] = { route, listed };
	}

	// The conformance report is a Dataset, and the article that renders it is
	// about it. It used to be a block of its own in the page's frontmatter, in
	// English on both pages, with no version and no date, the software's DOI as
	// its identifier and the script that writes it as the one thing it was
	// based on. Now it is the article's main entity, says which library it was
	// generated for and the day its data last changed, which can be no later
	// than the page's own, and names the standards its values are quoted from,
	// each as a named work, so its licence is read as covering the report.
	if (slug === REPORT) {
		seen.reports += 1;
		const dataset = article.mainEntity;
		const problems = [];
		if (!dataset || typeof dataset !== 'object' || !typesOf(dataset).includes('Dataset')) {
			problems.push('the article has no Dataset as its mainEntity');
		} else {
			if (dataset['@id'] !== `${canonical}#dataset`) problems.push(`its @id is ${dataset['@id']}, not ${canonical}#dataset`);
			if (dataset.inLanguage !== lang) problems.push(`its inLanguage is ${JSON.stringify(dataset.inLanguage)}, not ${lang}`);
			if (dataset.version !== REPORT_LIBRARY) {
				problems.push(`its version is ${JSON.stringify(dataset.version)}, and docs/conformance.json was generated for ${REPORT_LIBRARY}`);
			}
			// Dated by its data: the day the page prints as the one its rows
			// last changed, not the page's own date, which a change to how the
			// rows are drawn or to the page's text moves as well.
			const dataDay = provenanceDay(html);
			if (!/^\d{4}-\d{2}-\d{2}$/.test(String(dataset.dateModified ?? ''))) {
				problems.push(`its dateModified is ${JSON.stringify(dataset.dateModified)}, not a day`);
			} else {
				if (article.dateModified && dataset.dateModified > article.dateModified) {
					problems.push(`its data changed on ${dataset.dateModified}, after the page's own last change, ${article.dateModified}`);
				}
				if (dataDay !== undefined && dataset.dateModified !== dataDay) {
					problems.push(`its dateModified is ${dataset.dateModified}, and the page says its rows last changed on ${dataDay}`);
				}
			}
			if (dataDay === undefined) {
				problems.push('the page prints no day its rows last changed ([data-report-provenance] with a <time datetime>)');
			}
			// Of the commit its rows are of: the files it hands out and the
			// script it names are read at the commit the banner prints, as the
			// version and the date are, and not at a branch that moves on
			// after the page is built, which would hand out a newer file than
			// the one the record describes with nothing in it to say so.
			const commit = provenanceCommit(html);
			if (commit === undefined) {
				problems.push('the page names no commit its rows are of ([data-report-provenance] with a data-report-commit of 40 hexadecimal digits)');
			}
			const downloads = [dataset.distribution ?? []].flat();
			if (downloads.length === 0) problems.push('it hands out no file of the report (distribution)');
			for (const download of downloads) {
				if (!REPOSITORY_ADDRESS.test(String(download?.contentUrl ?? ''))) {
					problems.push(`it hands out ${JSON.stringify(download?.contentUrl)}, which is no file of the repository read at a commit`);
				}
			}
			if (commit !== undefined) {
				for (const [address, ref] of repositoryAddresses(dataset)) {
					if (ref !== commit) problems.push(`${address} is of ${ref}, not of commit ${commit}, the one the page says its rows are of`);
				}
			}
			const software = nodeOfType(nodes, 'SoftwareApplication');
			const borrowed = doisOf(dataset).filter((doi) => doisOf(software).includes(doi));
			if (borrowed.length > 0) problems.push(`it gives the software's DOI ${borrowed.join(', ')} as its own identifier`);
			const basis = [dataset.isBasedOn ?? []].flat().filter((item) => typeof item === 'object');
			const works = basis.filter((item) => isCitedWork(item?.['@id']) && isNamed(item));
			if (works.length === 0) problems.push('it names no standard it is based on');
			const unnamed = basis.length - works.length;
			if (unnamed > 0) problems.push(`${unnamed} of what it is based on is not a work the bibliography defines, named`);
			const named = new Set(basis.map((item) => item?.['@id']).filter(isCitedWork));
			reportDatasets.set(lang, { route, dataset, works: works.length, named, problems });
		}
		// The block of its own the page used to carry, kept beside the main
		// entity, would describe the report twice, the second time with what the
		// first one no longer says.
		const loose = nodes.filter((node) => typesOf(node).includes('Dataset')).length;
		if (loose > 0) {
			problems.push(
				`${loose === 1 ? 'a Dataset' : `${loose} Datasets`} of its own beside the article, which says what the report is a second time`,
			);
		}
		// Reported once the works the checks are based on are known, below.
		if (!reportDatasets.has(lang)) for (const problem of problems) fail(`${route}: the conformance report's Dataset: ${problem}`);
	}

	// The bibliography page defines every work in full, and names each
	// standard's publisher by the one identity the body has on the English
	// bibliography, in both languages. A body written out as an anonymous
	// Organization in every node that named it was 146 unrelated ISOs on the
	// English page alone. The check across the two languages runs after the
	// loop, once both pages have been read.
	if (slug === 'reference/bibliography') {
		const byId = new Map(nodes.filter((node) => node['@id']).map((node) => [node['@id'], node]));
		const standards = nodes.filter((node) => node.genre === 'Technical standard');
		const anonymous = new Map();
		const siteless = new Set();
		for (const standard of standards) {
			const id = standard.publisher?.['@id'];
			const body = typeof id === 'string' ? byId.get(id) : undefined;
			const identified =
				typeof id === 'string' &&
				id.startsWith(BODY_PREFIX) &&
				body !== undefined &&
				typesOf(body).includes('Organization') &&
				typeof body.name === 'string' &&
				body.name !== '';
			if (!identified) {
				const name = standard.publisher?.name ?? id ?? '(no publisher)';
				anonymous.set(name, (anonymous.get(name) ?? 0) + 1);
			} else if (!BODIES_WITHOUT_SITE.has(id) && !/^https:\/\/\S+$/.test(String(body.url ?? ''))) {
				// One identity per body is half of it; the other half is where the
				// body lives, which is what tells two bodies of one name apart.
				siteless.add(id);
			}
		}
		if (anonymous.size > 0) {
			const count = [...anonymous.values()].reduce((sum, n) => sum + n, 0);
			fail(
				`${route}: ${count} of ${standards.length} standards name a publisher with no identity of its own ` +
					`under ${BODY_PREFIX}: ${[...anonymous].map(([name, n]) => `${name} (${n})`).join(', ')}`,
			);
		} else {
			ok(`${route}: each of the ${standards.length} standards names its publisher by the body's one identity`);
		}
		if (siteless.size > 0) {
			fail(
				`${route}: ${siteless.size} of the bodies its standards name carry no https url of their official ` +
					'site: ' +
					[...siteless].map((id) => id.slice(BODY_PREFIX.length)).join(', '),
			);
		} else if (standards.length > 0) {
			const bodies = new Set(standards.map((standard) => standard.publisher?.['@id']));
			ok(
				`${route}: each of the ${bodies.size} bodies its standards name carries its official site, save ` +
					'the Spanish state issuers whose texts the BOE prints',
			);
		}
		// A work's description is the note of one page that cites it
		// (src/lib/citations.mjs, citedWorks). A catalogue page's note speaks
		// of that page's own rows, and read on the bibliography "the rows of
		// this catalogue" points at no catalogue at all: four books were
		// described that way, by whichever catalogue page sorted first.
		const described = nodes.filter((node) => isCitedWork(node['@id']) && typeof node.description === 'string');
		const pageBound = described.filter((node) => CATALOGUE_BOUND.test(node.description));
		if (pageBound.length > 0) {
			fail(
				`${route}: ${pageBound.length} of the ${described.length} works it describes take the words of a ` +
					`catalogue page about its own rows: ` +
					pageBound.map((node) => node['@id'].slice(node['@id'].indexOf('#'))).join(', '),
			);
		} else if (described.length > 0) {
			ok(`${route}: none of the ${described.length} works it describes is described as one catalogue page's rows`);
		}
		bibliographies.set(lang, { route, defined, standards, byId });
	}

	// The two locales are one work. English pages point forward to their
	// translation, Spanish pages point back at the original; a page carrying
	// both, or neither, is claiming something else. The API reference has one
	// version, in English, and declares neither on either route.
	const pairing = lang === 'en' ? 'workTranslation' : 'translationOfWork';
	const opposite = lang === 'en' ? 'translationOfWork' : 'workTranslation';
	if (isApiRoute(slug)) {
		const declared = ['workTranslation', 'translationOfWork'].filter((key) => article[key] !== undefined);
		if (declared.length > 0) fail(`${route}: an API page declares ${declared.join(' and ')}`);
	} else if (article[pairing] === undefined || article[opposite] !== undefined) {
		const declared =
			['workTranslation', 'translationOfWork'].filter((key) => article[key] !== undefined).join(' and ') ||
			'neither';
		fail(`${route}: a ${lang} page has to declare ${pairing} alone, and declares ${declared}`);
	}

	// The generated API tree is documentation of modules, not a guide, and of
	// one release, on one range of Pythons: the graph is the same for every
	// module, so it is judged once per distinct release and platform below.
	if (slug.startsWith('reference/api/')) {
		seen.api += 1;
		if (!typesOf(article).includes('APIReference')) {
			fail(`${route}: an API page is typed ${JSON.stringify(article['@type'])}`);
		}
		const release = JSON.stringify([article.assemblyVersion ?? null, article.targetPlatform ?? null]);
		apiReleases.set(release, (apiReleases.get(release) ?? 0) + 1);
	}

	// The trail: contiguous positions from one, and the last crumb is the page
	// itself. A trail that ends anywhere else is describing another page.
	const crumbs = nodeOfType(nodes, 'BreadcrumbList');
	if (!crumbs) fail(`${route}: no BreadcrumbList node`);
	else {
		const items = crumbs.itemListElement ?? [];
		const positions = items.map((item) => item.position);
		const contiguous = positions.every((position, i) => position === i + 1);
		if (items.length < 2 || !contiguous) {
			fail(`${route}: breadcrumb positions are ${JSON.stringify(positions)}`);
		}
		const last = items[items.length - 1];
		if (last && last.item !== canonical) {
			fail(`${route}: the last crumb points at ${last.item}, not ${canonical}`);
		}
		const dangling = items.filter((item) => !isOnThisSite(item.item));
		if (dangling.length > 0) {
			fail(`${route}: ${dangling.length} crumb(s) point outside the site`);
		}

		// A page the tree does not list has no trail of its own there, and
		// takes the trail of the route its address sits under: an errata page,
		// /reference/errata/iso-3743/, is one of 96 the registry's index lists
		// and the sidebar does not. Its trail used to run from the root straight
		// to the page, skipping both the section and the index its address
		// names. The tree decides a listed page's trail, and that one differs
		// from the address on purpose in places (a URL prefix is often a
		// grouping, not a page), so only an unlisted page is held to this.
		const parent = LISTED.has(slug) ? undefined : listedParentOf(slug);
		if (parent !== undefined) {
			seen.unlisted += 1;
			const wanted = `${ORIGIN}${lang === 'es' ? '/es' : ''}/${parent}/`;
			if (!items.slice(0, -1).some((item) => item.item === wanted)) {
				fail(
					`${route}: the navigation tree does not list this page, and its trail skips ${wanted}, ` +
						`the listed route it sits under (${items.map((item) => item.name).join(' > ')})`,
				);
			}
		}
	}

	// The section, which is what this check exists for. The name comes from
	// src/data/topics.mjs, in the page's own language, and every page a topic
	// owns has to carry it.
	const topic = topicForSlug(slug);
	if (topic) {
		const wanted = topic.label[lang];
		if (article.articleSection === undefined) missingSection.push(route);
		else if (article.articleSection !== wanted) {
			wrongSection.push(`${route}: ${JSON.stringify(article.articleSection)} for ${JSON.stringify(wanted)}`);
		} else seen.sections += 1;

		// A topic that teaches publishes guides, and a guide is a learning
		// resource as well as an article.
		if (topic.isDomain) {
			seen.guides += 1;
			if (!typesOf(article).includes('LearningResource')) {
				fail(`${route}: a guide is typed ${JSON.stringify(article['@type'])} with no LearningResource`);
			}
			if (article.learningResourceType !== 'Guide') {
				fail(`${route}: a guide declares learningResourceType ${JSON.stringify(article.learningResourceType)}`);
			}
		}
	} else if (article.articleSection !== undefined) {
		fail(`${route}: belongs to no topic but claims the section ${JSON.stringify(article.articleSection)}`);
	}
}

// Reported per topic rather than per page: the defect that prompted this check
// took out an entire topic at once, and 54 identical lines would have buried
// the one fact worth reading.
const byTopic = (routes) => {
	const groups = new Map();
	for (const route of routes) {
		const slug = route.replace(/^\/(es\/)?/, '').replace(/\/$/, '');
		const id = topicForSlug(slug)?.id ?? '(none)';
		groups.set(id, (groups.get(id) ?? 0) + 1);
	}
	return [...groups].map(([id, n]) => `${id} (${n} pages)`).join(', ');
};

if (missingSection.length > 0) {
	fail(`${missingSection.length} page(s) under a topic publish no articleSection: ${byTopic(missingSection)}`);
	console.error(`     first: ${missingSection.slice(0, 3).join(', ')}`);
}
if (wrongSection.length > 0) {
	fail(`${wrongSection.length} page(s) name a section topics.mjs does not: ${wrongSection.slice(0, 3).join('; ')}`);
}
if (missingSection.length === 0 && wrongSection.length === 0) {
	ok(`every one of the ${seen.sections} pages under a topic names its section as topics.mjs does`);
}

// The software node's operating systems, one platform per entry. jmrp.io's
// projects page publishes the same `@id` with `operatingSystem` as a list of
// single names, and this site published one comma-joined string. That string
// was valid on its own, but a consumer merging the two documents by `@id` read
// four values for three platforms, one of them a list inside a string, and
// nothing on either side flagged it. The graph is the same on every page, so
// it is judged once per distinct value, with the pages that carry it.
for (const [platforms, pages] of platformLists) {
	const names = JSON.parse(platforms);
	const onePerEntry =
		Array.isArray(names) &&
		names.length > 0 &&
		names.every((name) => typeof name === 'string' && /^[^,\s](?:[^,]*[^,\s])?$/.test(name)) &&
		new Set(names).size === names.length;
	if (onePerEntry) {
		ok(`the software node names its ${names.length} operating systems one per entry on ${pages} pages`);
	} else {
		fail(
			`${pages} page(s): the software node's operatingSystem is ${platforms}; ` +
				'it has to list each platform once, one name per entry, as jmrp.io/projects/ does for the same @id',
		);
	}
}

// The site-wide block, judged once per distinct size: it is the same bytes on
// every page, so a growth shows as one size on every page at once.
if (siteBlocks.size === 0) {
	fail('no page carries the site-wide ld+json block with the Person: the site graph changed under this check');
}
for (const [size, { person, pages }] of [...siteBlocks].sort(([a], [b]) => b - a)) {
	if (size > SITE_BLOCK_BUDGET) {
		fail(
			`${pages} page(s): the site-wide ld+json block is ${size} bytes, over its budget of ${SITE_BLOCK_BUDGET}; ` +
				`the Person spliced from jmrp.io is ${person} of them. Trim the source, or raise SITE_BLOCK_BUDGET ` +
				'in scripts/check-structured-data.mjs if the growth is wanted',
		);
	} else {
		ok(
			`the site-wide ld+json block is ${size} bytes on ${pages} pages, within its budget of ` +
				`${SITE_BLOCK_BUDGET}; the Person is ${person} of them`,
		);
	}
}

const editedLine = `${seen.edited} of the ${seen.articles} articles were last edited after the day they were first published`;
if (seen.edited < seen.articles * EDITED_FLOOR) {
	fail(`${editedLine}: src/lib/page-dates.mjs read no history, from a shallow checkout or a failed git log`);
} else {
	ok(editedLine);
}

/** The first few routes of a list of [route, count] pairs, with the counts. */
const firstOf = (pairs) => pairs.slice(0, 3).map(([route, n]) => `${route} (${n})`).join(', ');
const total = (pairs) => pairs.reduce((sum, [, n]) => sum + n, 0);

if (unnamedBasis.length > 0) {
	fail(
		`${unnamedBasis.length} page(s) give ${total(unnamedBasis)} work(s) they are based on as a bare @id: ` +
			'the first reference to each work in isBasedOn has to carry its @type and name',
	);
	console.error(`     first: ${firstOf(unnamedBasis)}`);
} else if (seen.basedOn === 0) {
	// A check that found nothing to read would pass everything.
	fail('no page says what it is based on: the citation properties changed under this check');
} else {
	ok(`every one of the ${seen.basedOn} works pages are based on is named at its first reference in isBasedOn`);
}
if (unnamedCited.length > 0) {
	fail(
		`${unnamedCited.length} page(s) point at ${total(unnamedCited)} cited work(s) that nothing on the page names`,
	);
	console.error(`     first: ${firstOf(unnamedCited)}`);
} else {
	ok(`every one of the ${seen.cited} works ${seen.citing} pages cite is named on the page that cites it`);
}

// Every catalogue the generator writes is a Dataset once in each language,
// and the overview of the catalogues lists exactly those. A build that holds
// no catalogue page at all (the small builds the tests of this check write)
// has nothing to count. It is one that holds none anywhere: the routes are the
// ones topics.mjs lists, and a catalogue's dataset or table at any other
// route, or a DataCatalog anywhere but the overview, has failed above.
for (const lang of ['en', 'es']) {
	if (cataloguePagesSeen[lang] === 0 && listedDatasets[lang] === undefined) continue;
	const found = datasetsByLanguage[lang];
	const missing = CATALOGUE_KEYS.filter((key) => !found.has(key));
	if (missing.length > 0) {
		fail(
			`the ${lang} catalogue pages publish ${found.size} of the ${CATALOGUE_KEYS.length} catalogues as a Dataset; ` +
				`none is ${missing.join(', ')}`,
		);
	} else {
		ok(`each of the ${CATALOGUE_KEYS.length} catalogues is a Dataset of one ${lang} catalogue page, claiming no licence`);
	}
	const overview = listedDatasets[lang];
	if (!overview) {
		fail(`the ${lang} overview of the catalogues was not found: build the site first`);
		continue;
	}
	const ids = new Set([...found.values()].map(({ node }) => node['@id']));
	const unlisted = [...ids].filter((id) => !overview.listed.has(id));
	const stray = [...overview.listed.keys()].filter((id) => !ids.has(id));
	const misnamed = [...found.values()].filter(
		({ node }) => overview.listed.has(node['@id']) && overview.listed.get(node['@id']).name !== node.name,
	);
	if (unlisted.length > 0 || stray.length > 0 || misnamed.length > 0) {
		fail(
			`${overview.route}: the DataCatalog leaves out ${unlisted.length}, lists ${stray.length} no catalogue page ` +
				`publishes and names ${misnamed.length} otherwise than its page (first: ` +
				`${[...unlisted, ...stray, ...misnamed.map(({ node }) => node['@id'])].slice(0, 3).join(', ')})`,
		);
	} else {
		ok(`${overview.route}: the DataCatalog lists the ${ids.size} datasets of its language, each by its own name`);
	}
}
{
	const twinless = datasetTwins.filter(({ lang, key, twin }) => {
		const other = datasetsByLanguage[lang === 'en' ? 'es' : 'en'].get(key);
		return !other || other.node['@id'] !== twin;
	});
	if (twinless.length > 0) {
		fail(
			`${twinless.length} dataset(s) name as their translation a dataset the other language does not publish ` +
				`(first: ${twinless.slice(0, 3).map(({ at, twin }) => `${at} -> ${twin}`).join('; ')})`,
		);
	} else if (datasetTwins.length > 0) {
		ok(`each of the ${datasetTwins.length} datasets names its twin in the other language`);
	}
	if (seen.datasetDated > 0 && seen.datasetUndated === 0) {
		ok(`each of the ${seen.datasetDated} datasets is dated as the page that renders it`);
	}
	if (seen.datasetShown > 0 && seen.datasetUnshown === 0) {
		ok(
			`each of the ${seen.datasetShown} datasets is named by a heading of its page and described by a paragraph ` +
				'of it, or by the description of a page of one catalogue',
		);
	}
	if (seen.datasetBasis > 0) {
		ok(`the datasets name each of the ${seen.datasetBasis} works they are based on where they cite it`);
	}
}

// Every errata family page names the works it corrects. A build that holds no
// errata index in a language (the small builds the tests of this check write)
// has nothing to count; one that does holds its family pages and the page of
// properties that are not errata under it, or the routes moved under this
// check and every test above read nothing.
if (errataWithoutWorks.length > 0) {
	fail(
		`${errataWithoutWorks.length} errata page(s) name no work they correct in about, only the software ` +
			`(first: ${errataWithoutWorks.slice(0, 3).join(', ')})`,
	);
}
if (errataMisnamed.length > 0) {
	fail(
		`${errataMisnamed.length} errata page(s) name in about other works than their corrects lists, or in another ` +
			`order (first: ${errataMisnamed.slice(0, 3).join('; ')})`,
	);
}
// What the content tree holds under each errata index, the build holds, and
// the works its family pages name add up to what their `corrects` lists.
let errataAgree = errataWithoutWorks.length === 0 && errataMisnamed.length === 0;
for (const lang of ['en', 'es']) {
	const { index, built, families, corrected, notErrata } = errataSeen[lang];
	const content = errataPages[lang];
	if (content.index && !index) {
		fail(`the ${lang} errata index is under ${content.folder} and the build does not hold it`);
		errataAgree = false;
	}
	const unbuilt = [...content.pages.keys()].filter((name) => !built.has(name));
	if (unbuilt.length > 0) {
		fail(
			`the ${lang} build holds ${content.pages.size - unbuilt.length} of the ${content.pages.size} errata pages ` +
				`under ${content.folder} (first missing: ${unbuilt.slice(0, 3).join(', ')})`,
		);
		errataAgree = false;
	}
	if (!index) continue;
	if (families === 0) fail(`the ${lang} errata index was built with no family page under it`);
	if (!notErrata) {
		fail(
			`the ${lang} errata index was built without ${NOT_ERRATA}, the page of properties that are not errata ` +
				'(scripts/generate_site_reports.py, NOT_ERRATA_SLUG)',
		);
	}
	const listed = [...content.pages.values()].reduce((sum, fragments) => sum + fragments.length, 0);
	if (corrected !== listed) {
		fail(`the ${lang} errata family pages name ${corrected} work(s) in about, and their corrects list ${listed}`);
	}
	if (families === 0 || !notErrata || corrected !== listed) errataAgree = false;
}
if (errataAgree && seen.corrected > 0) {
	const families = errataSeen.en.families + errataSeen.es.families;
	ok(
		`each of the ${families} errata family pages names in about, in order, the works its corrects lists, ` +
			`${seen.corrected} in all`,
	);
}

// The two bibliographies define one set of works in two languages. A Spanish
// standard says which English node it is with `sameAs`, and that node has to
// exist: an edition note is translated with the page ("4.ª ed.", "4th ed."),
// so the two `@id`s are not always the locale apart, and a guessed address
// would point at nothing.
{
	const en = bibliographies.get('en');
	const es = bibliographies.get('es');
	if (!en || !es) {
		fail(`the bibliography page was not found in ${en ? 'Spanish' : 'English'}: build the site first`);
	} else if (en.standards.length === 0 || es.standards.length === 0) {
		fail(
			`the bibliography defines ${en.standards.length} standards in English and ${es.standards.length} in ` +
				'Spanish: the standard nodes changed under this check',
		);
	} else {
		const untied = [];
		const dangling = [];
		const mismatched = [];
		for (const standard of es.standards) {
			const targets = [standard.sameAs ?? []]
				.flat()
				.filter((url) => typeof url === 'string' && url.startsWith(ENGLISH_STANDARD_PREFIX));
			if (targets.length === 0) untied.push(standard.identifier);
			for (const url of targets) {
				const target = en.byId.get(url);
				if (!target) dangling.push(url);
				// The pairing is read off the built nodes, not off citations.mjs: a
				// translated designation keeps its numbers, in their order, and a
				// Spanish standard naming another English one does not.
				else if (numbersOf(target.identifier) !== numbersOf(standard.identifier)) {
					mismatched.push(`${standard.identifier} as ${target.identifier}`);
				}
			}
		}
		if (untied.length > 0) {
			fail(
				`${es.route}: ${untied.length} of ${es.standards.length} standards name no English node as the same ` +
					`work (first: ${untied.slice(0, 3).join('; ')})`,
			);
		}
		if (dangling.length > 0) {
			fail(
				`${es.route}: ${dangling.length} sameAs point at English standards ${en.route} does not define ` +
					`(first: ${dangling.slice(0, 3).join(', ')})`,
			);
		}
		if (mismatched.length > 0) {
			fail(
				`${es.route}: ${mismatched.length} standards name as the same work an English standard whose ` +
					`designation carries other numbers (first: ${mismatched.slice(0, 3).join('; ')})`,
			);
		}
		if (untied.length === 0 && dangling.length === 0 && mismatched.length === 0) {
			ok(
				`each of the ${es.standards.length} Spanish standards names the English node it is, among the ` +
					`${en.standards.length} the English bibliography defines, with the same numbers in its designation`,
			);
		}

		// A page names a work from its own references and the bibliography from
		// whichever page it read first, so the two could say different things
		// of one @id: two catalogue addresses for one standard, one paper's
		// title on another's identifier. citations.mjs refuses to build that;
		// this is the same promise read off what was built.
		const differing = new Map();
		const fieldCounts = new Map();
		const FIELD_ORDER = [...STUB_FIELDS, 'sameAs', '(defined on no bibliography)'];
		for (const { route, item } of stubs) {
			const lang = item['@id'].startsWith(`${ORIGIN}/es/`) ? 'es' : 'en';
			const node = bibliographies.get(lang).byId.get(item['@id']);
			const wrong = node
				? STUB_FIELDS.filter((field) => canonical(item[field]) !== canonical(node[field]))
				: ['(defined on no bibliography)'];
			const known = new Set([node?.sameAs ?? []].flat());
			if (node && [item.sameAs ?? []].flat().some((value) => !known.has(value))) wrong.push('sameAs');
			if (wrong.length === 0) continue;
			if (!differing.has(item['@id'])) differing.set(item['@id'], { routes: [], fields: new Set() });
			const entry = differing.get(item['@id']);
			entry.routes.push(route);
			for (const field of wrong) {
				if (!entry.fields.has(field)) fieldCounts.set(field, (fieldCounts.get(field) ?? 0) + 1);
				entry.fields.add(field);
			}
		}
		if (stubs.length === 0) {
			fail('no page names a cited work: the citation markup changed under this check');
		} else if (differing.size > 0) {
			const pages = new Set([...differing.values()].flatMap(({ routes }) => routes));
			fail(
				`${differing.size} work(s) are named on ${pages.size} page(s) other than as the bibliography ` +
					`defines them: ${[...fieldCounts]
						.sort(([a], [b]) => FIELD_ORDER.indexOf(a) - FIELD_ORDER.indexOf(b))
						.map(([field, n]) => `${field} on ${n}`)
						.join(', ')}`,
			);
			const first = [...differing]
				.slice(0, 3)
				.map(([id, { routes, fields }]) => `${routes[0]} ${id.slice(id.indexOf('#'))} (${[...fields].join(', ')})`);
			console.error(`     first: ${first.join('; ')}`);
		} else {
			ok(`each of the ${stubs.length} stubs that name a work on a page says what the bibliography says of it`);
		}
	}
}

// Every page carries the same site-wide nodes, so a defect in them is on every
// page at once: reported once, with the number of pages it was found on.
// A page that lacks one of the software's nodes has failed by name above and
// was not read here, so the summary speaks for every page only when it read
// every page.
for (const [defect, pages] of siteNodeDefects) fail(`${defect} (on ${pages} pages)`);
if (siteNodeDefects.size === 0 && seen.history === seen.pages) {
	ok(
		`the software's nodes on all ${seen.pages} pages give its history: created ${FIRST_COMMIT}, ` +
			`library last changed ${LIBRARY_MODIFIED}, release notes, help, its former package and its archive`,
	);
}

// The languages of the site-wide graph and the package's requirements, the
// same on every page, reported once with the pages each defect stands on. The
// summary speaks for every page only when every page carried the two nodes.
for (const [defect, pages] of languageNodeDefects) fail(`${defect} (on ${pages} pages)`);
if (languageNodeDefects.size === 0 && seen.languages === seen.pages) {
	ok(
		`the site-wide nodes on all ${seen.pages} pages describe the site and the software in English and in Spanish, ` +
			`list one feature for each of the ${domainIds.length} topics that teach in each language, ` +
			'publish no placeholder as a standard or a keyword, and state every requirement and extra of pyproject.toml',
	);
}

// The release and the Python each API page documents: VERSION, read above,
// and the requires-python of pyproject.toml, compared without the spaces the
// site writes between the operator and the version.
{
	const platform = `Python${requiresPython}`.replace(/\s+/g, '');
	let wrong = 0;
	for (const [release, pages] of apiReleases) {
		const [version, target] = JSON.parse(release);
		if (version === VERSION && typeof target === 'string' && target.replace(/\s+/g, '') === platform) continue;
		wrong += pages;
		fail(
			`${pages} API page(s) name the release ${shown(version ?? undefined)} and the platform ${shown(target ?? undefined)}, ` +
				`not ${VERSION}, from VERSION, and Python ${requiresPython.replace(/^(>=|<=|==|~=|!=|>|<)/, '$1 ')}, from pyproject.toml`,
		);
	}
	if (seen.api > 0 && wrong === 0) {
		const [, target] = JSON.parse([...apiReleases.keys()][0]);
		ok(`all ${seen.api} API pages name the release ${VERSION} and ${target}`);
	}
}

// One About page in each language, each typed AboutPage. A page that is not
// typed has failed by its route above; the summary is printed only when both
// pages are there and typed.
if (about.en.found !== 1 || about.es.found !== 1) {
	fail(
		`found ${about.en.found} About page(s) in English and ${about.es.found} in Spanish, ` +
			'not the English one and its Spanish twin',
	);
} else if (about.en.typed === 1 && about.es.typed === 1) {
	ok('the About page in English and its Spanish twin are both typed AboutPage');
}

// A glossary term's guide is another page, so its article node can only be
// looked for once every page has been read.
const unresolved = glossarySubjects.filter((subject) => !articleIds.has(subject.target));
if (unresolved.length > 0) {
	fail(`${unresolved.length} glossary term(s) point at an article node no page of the build defines:`);
	for (const subject of unresolved.slice(0, 5)) {
		console.error(`     ${subject.route}#${subject.term} -> ${subject.target}`);
	}
}
// The glossary indexes the quantities its guides compute, so a build that
// publishes one of those guides publishes the glossary in that language too,
// once. Its route is matched by name above: were the page to move, its checks
// would stop with nothing to say so, and this is what says so. A build of a
// few pages that publishes none of the guides, as the tests of the other
// checks write, has no glossary to answer for, and gets no line about one.
for (const [lang, { found, guides }] of Object.entries(glossaryPages)) {
	if (found > 1 || (found === 0 && guides > 0)) {
		fail(
			`found ${found} glossary pages in ${LANGUAGE[lang]}, not one, in a build that publishes ` +
				`${guides} of the ${GLOSSARY_GUIDES.size} guides its entries name in that language`,
		);
	}
}
if (
	glossaryPages.en.found === 1 &&
	glossaryPages.es.found === 1 &&
	glossaryDefects === 0 &&
	unresolved.length === 0
) {
	ok(
		`checked the ${seen.definedTerms} DefinedTerms of the glossary in both languages against ` +
			`src/data/glossary.mjs: one per entry, each named by its entry's quantity, a symbol as its ` +
			`termCode and alternateName with no TeX and no hole left that writes, in order, the letters, ` +
			`digits, Greek letters, primes and signs of the symbol and keeps every Greek letter, named ` +
			`function, root, exponent and comma of it, a named entry with no code and only its declared ` +
			`alias, a description with no hole and no TeX that writes, in order, what its definition, unit, ` +
			`standard and clause write and keeps the same of its entry, and its own ` +
			`guide's article node, which all ${glossarySubjects.length} resolve to in this build`,
	);
}

// The report's Dataset in the two languages: the Spanish page used to name
// it, describe its technique and its eight columns in English. Every text a
// reader reads has to be the page's own, so none is the same in both.
{
	const en = reportDatasets.get('en');
	const es = reportDatasets.get('es');
	// What each language's Dataset has to be based on: the works the join of
	// the report with that language's pages resolves the checks' standards
	// to, the join the build itself makes, read here from the report and the
	// frontmatter the build was made from, not from what the build wrote.
	let governing = new Map();
	if (reportDatasets.size > 0) {
		try {
			const pages = await readPageReferences(CONTENT);
			// The pairings the report's documents need; whether every entry is
			// still needed is the build's to say, and it does.
			const documents = governingDocuments(CONFORMANCE);
			const sameWorks = SAME_WORKS.filter((entry) => documents.has(entry.document));
			governing = new Map(
				[...reportDatasets.keys()].map((lang) => {
					const bibliography = `${ORIGIN}${lang === 'es' ? '/es' : ''}/reference/bibliography/`;
					const evidence = conformanceEvidence({
						report: CONFORMANCE,
						pages: pages.filter((page) => page.lang === lang),
						bibliographyUrl: bibliography,
						reportPath: `${basePath}/${REPORT}/`,
						sameWorks,
						lang,
					});
					return [lang, evidence.governing.map((ref) => referenceId(ref, bibliography))];
				}),
			);
		} catch (error) {
			fail(`the works the conformance report's checks are based on cannot be read from ${CONTENT}: ${error.message}`);
		}
	}
	const fragments = (ids) => ids.map((id) => id.slice(id.indexOf('#'))).join(', ');
	for (const [lang, { route, named, problems }] of reportDatasets) {
		const due = governing.get(lang);
		if (due) {
			const missing = due.filter((id) => !named.has(id));
			const extra = [...named].filter((id) => !due.includes(id));
			if (missing.length > 0) {
				problems.push(`it leaves out ${missing.length} of the ${due.length} works its checks are based on: ${fragments(missing.slice(0, 8))}${missing.length > 8 ? ', ...' : ''}`);
			}
			if (extra.length > 0) {
				problems.push(`it names ${extra.length} work${extra.length === 1 ? '' : 's'} no check is based on: ${fragments(extra.slice(0, 8))}${extra.length > 8 ? ', ...' : ''}`);
			}
		}
		for (const problem of problems) fail(`${route}: the conformance report's Dataset: ${problem}`);
	}
	if (seen.reports === 0) {
		fail(`no page at /${REPORT}/ was found: build the site first`);
	} else if (en && es) {
		const english = datasetTexts(en.dataset);
		const spanish = datasetTexts(es.dataset);
		// Both pages are held to every text either one writes, each a text
		// with words in it: a text one page leaves out, or leaves empty, is
		// not a translation of the other's, and a column one page describes
		// and the other does not is a column the other leaves out.
		const written = (value) => typeof value === 'string' && value.trim() !== '';
		const keys = [...new Set([...Object.keys(english), ...Object.keys(spanish)])];
		const unwritten = [];
		for (const [{ route }, texts] of [
			[en, english],
			[es, spanish],
		]) {
			const left = keys.filter((key) => !written(texts[key]));
			if (left.length > 0) {
				unwritten.push(route);
				fail(`${route}: the conformance report's Dataset writes no text for ${left.join(', ')}`);
			}
		}
		const columns = (dataset) => [dataset.variableMeasured ?? []].flat().length;
		const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
		const described = columns(en.dataset) === columns(es.dataset);
		if (!described) {
			fail(
				`the conformance report's Dataset describes ${plural(columns(en.dataset), 'column')} in English ` +
					`and ${columns(es.dataset)} in Spanish`,
			);
		}
		const same = keys.filter((key) => written(english[key]) && english[key] === spanish[key]);
		// The two pages render one report, so they name one set of works,
		// each in its own language's bibliography.
		const counted = en.named.size === es.named.size;
		if (!counted) fail(`the conformance report's Dataset names ${plural(en.named.size, 'work')} in English and ${es.named.size} in Spanish`);
		if (same.length > 0) {
			fail(`${es.route}: the conformance report's Dataset says in English what the English page says: ${same.join(', ')}`);
		} else if (counted && described && unwritten.length === 0 && en.problems.length === 0 && es.problems.length === 0) {
			ok(
				`the conformance report's Dataset is the main entity of both report pages, versioned ${REPORT_LIBRARY}, ` +
					`dated by the day its rows last changed, based on the ${en.named.size} work${en.named.size === 1 ? '' : 's'} ` +
					`the standards of its checks resolve to, named in each language, and written in each page's language ` +
					`(${keys.length} texts)`,
			);
		}
	}
}

ok(`parsed ${seen.blocks} ld+json blocks across ${seen.pages} pages (${seen.redirects} redirect stubs skipped)`);
ok(`checked ${seen.guides} guide pages for the learning-resource type and ${seen.api} API pages for APIReference`);
ok(`checked ${seen.fallbacks} Spanish API routes against their English twin's graph`);
ok(`checked ${seen.unlisted} pages the navigation tree does not list for the route they sit under in their trail`);

console.log(`\n${failures} failing check(s).`);
process.exit(failures ? 1 : 0);
