// Small builds for the tests of check-structured-data.mjs.
//
// The check reads a whole build, and some of what it asks is asked of the
// whole site at once: the software node and its history on every page, the
// site-wide block under its byte budget, the About page in both languages, a
// share of pages edited since they were first published. A test that hands it
// a build of a few pages has to give it all of that, or every test fails on
// what it did not mean to test. So the pages are written here, once, whole by
// default, and every test file of the check builds on them: a check that adds
// a site-wide requirement adds it to this file, and each suite keeps testing
// only its own defect.
//
// A page is data until the build is written: its article node, every node of
// its graph and what it says, which a test changes in place before `check`
// writes the build. Each page carries two ld+json blocks, as the built site
// does: the site-wide nodes astro.config.mjs puts on every page, and the
// page's own graph from Head.astro. A page may carry further blocks, as the
// glossary writes its terms in one of its own; a test gives each whole, or as
// written when it means one not to parse.
//
// Nothing here is installed: the tests run before the site's dependencies are.
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../../src/data/site.mjs';
import { topicForSlug } from '../../src/data/topics.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const CHECK = join(here, '..', 'check-structured-data.mjs');
const REPOSITORY_ROOT = join(here, '..', '..', '..');

/** The site's own address, as every URL of a page starts. */
export const ORIGIN = `${siteUrl}${basePath}`;

/**
 * The day of the last commit `git log` lists with these arguments, as
 * `YYYY-MM-DD`: in UTC, from the commit's timestamp, the way the check reads
 * it, or as the committer's clock wrote it, which a test gives the check to
 * see it refused.
 *
 * @param {'%ct'|'%cI'} format `%ct` for the UTC day, `%cI` for the committer's.
 * @param {...string} args Arguments after `git -C <repository root> log`.
 * @returns {string} The day.
 */
export const commitDay = (format, ...args) => {
	const printed = execFileSync('git', ['-C', REPOSITORY_ROOT, 'log', `--format=${format}`, ...args], {
		encoding: 'utf8',
	})
		.trim()
		.split('\n')
		.at(-1);
	return format === '%ct' ? new Date(Number(printed) * 1000).toISOString().slice(0, 10) : printed.slice(0, 10);
};

/** The UTC day of the repository's first commit, which the software's `dateCreated` has to give. */
export const FIRST_COMMIT = commitDay('%ct', '--max-parents=0', 'HEAD');
/** The UTC day of the last commit under src/, which the software's `dateModified` has to give. */
export const LIBRARY_MODIFIED = commitDay('%ct', '-1', '--', 'src');

/** The platforms the software node names when a test does not say otherwise. */
export const PLATFORMS = ['Linux', 'macOS', 'Windows'];

const REPOSITORY = 'https://github.com/jmrplens/phonometry';

/** The `@id` of each node astro.config.mjs puts on every page, as the config writes it. */
export const SITE = {
	person: 'https://jmrp.io/#person',
	website: `${ORIGIN}/#website`,
	software: `${REPOSITORY}#software`,
	source: `${REPOSITORY}#source-code`,
};

/** The types of the nodes astro.config.mjs writes in a block of their own on every page. */
export const SITE_TYPES = new Set(['Person', 'WebSite', 'SoftwareApplication', 'SoftwareSourceCode']);

/** The years of the maintainer's research role, as the Person node dates it and the About page states it. */
export const RESEARCH = { start: '2019', end: '2023' };

/** The year the maintainer's master's degree was awarded, the one date the Person node gives it. */
export const MASTER_END = '2019';

/**
 * The four nodes astro.config.mjs puts on every page, whole: the software's
 * history the check reads from git, and the maintainer's dated roles as the
 * Person node jmrp.io publishes gives them: the research role and the sound
 * technician's, with a start and an end, and the master's degree, dated by
 * the year it was awarded alone, as the node dates every degree.
 *
 * @param {unknown} [operatingSystem] What the software node names; null leaves the property out.
 * @returns {object[]} Person, WebSite, SoftwareApplication and SoftwareSourceCode.
 */
export function siteNodes(operatingSystem = PLATFORMS) {
	return [
		{
			'@type': 'Person',
			'@id': SITE.person,
			name: 'The maintainer',
			alumniOf: [
				{
					'@type': 'OrganizationRole',
					alumniOf: {
						'@type': 'EducationalOrganization',
						name: 'Universitat Politècnica de València',
						alternateName: 'UPV',
					},
					startDate: RESEARCH.start,
					endDate: RESEARCH.end,
				},
				{
					'@type': 'OrganizationRole',
					roleName: "Master's degree in acoustical engineering",
					alumniOf: { '@type': 'EducationalOrganization', name: 'Universitat Politècnica de València' },
					endDate: MASTER_END,
				},
			],
			hasOccupation: [
				{
					'@type': 'Role',
					startDate: RESEARCH.start,
					endDate: RESEARCH.end,
					hasOccupation: {
						'@type': 'Occupation',
						name: [
							{ '@value': 'Acoustics researcher', '@language': 'en' },
							{ '@value': 'Investigador en acústica', '@language': 'es' },
						],
					},
				},
				{
					'@type': 'Role',
					startDate: '2011',
					endDate: '2018',
					hasOccupation: {
						'@type': 'Occupation',
						name: [
							{ '@value': 'Sound technician', '@language': 'en' },
							{ '@value': 'Técnico de sonido', '@language': 'es' },
						],
					},
				},
			],
		},
		{ '@type': 'WebSite', '@id': SITE.website, name: 'phonometry', url: `${ORIGIN}/` },
		{
			'@type': 'SoftwareApplication',
			'@id': SITE.software,
			name: 'phonometry',
			alternateName: 'PyOctaveBand',
			codeRepository: REPOSITORY,
			releaseNotes: `${REPOSITORY}/releases`,
			softwareHelp: { '@id': SITE.website },
			sameAs: ['https://pypi.org/project/phonometry/', 'https://pypi.org/project/PyOctaveBand/'],
			dateCreated: FIRST_COMMIT,
			dateModified: LIBRARY_MODIFIED,
			...(operatingSystem === null ? {} : { operatingSystem }),
		},
		{
			'@type': 'SoftwareSourceCode',
			'@id': SITE.source,
			name: 'phonometry',
			codeRepository: REPOSITORY,
			dateCreated: FIRST_COMMIT,
			targetProduct: { '@id': SITE.software },
			archivedAt: `https://archive.softwareheritage.org/browse/origin/?origin_url=${REPOSITORY}`,
		},
	];
}

/**
 * One page whose structured data is whole: its article node, the trail from
 * the home page down to it, and the site-wide nodes.
 *
 * A page under a topic names the topic's section, a guide is a learning
 * resource, and a Spanish page points back at its English original. Every
 * page is published on 2026-07-01 and last edited on 2026-10-01 unless a test
 * says otherwise.
 *
 * @param {string} slug The page's route without the language prefix or slashes at either end.
 * @param {'en'|'es'} lang The page's language.
 * @param {object} [extra] Fields of the article node, over its own.
 * @returns {{path: string, article: object, nodes: object[], text: string}} The page: where the
 *   build writes it, its article node, every node of its graph, and what it says.
 */
export function page(slug, lang, extra = {}) {
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
	return { path, article, nodes: [...siteNodes(), article, trail], text: '' };
}

/**
 * What each About page says of the master's degree and the research role, in
 * its own language and in the two forms the real page writes its years in.
 */
export const ABOUT_TEXT = {
	en:
		`<p>I took the master's degree at the UPV (2018-${MASTER_END}) and worked as an acoustics ` +
		`researcher there from ${RESEARCH.start} to ${RESEARCH.end}.</p>`,
	es:
		`<p>Cursé el máster en la UPV (2018-${MASTER_END}) y trabajé allí como investigador en acústica ` +
		`de ${RESEARCH.start} a ${RESEARCH.end}.</p>`,
};

/**
 * The About page of one language, typed and worded as the check asks.
 *
 * @param {'en'|'es'} lang The page's language.
 * @param {object} [extra] Fields of the article node, as `page()` takes them.
 * @returns {{path: string, article: object, nodes: object[], text: string}} The page.
 */
export function aboutPage(lang, extra = {}) {
	return { ...page('start/about', lang, { '@type': ['AboutPage', 'TechArticle'], ...extra }), text: ABOUT_TEXT[lang] };
}

/**
 * A build the check has nothing to report on: the pages in `base`, then the
 * About page in English and in Spanish, which the check asks of every build,
 * then plain English pages up to `pages` in all.
 *
 * The first `dated` pages, in that order, are published on `published` and
 * the rest on the day of their last edit, 2026-10-01. `platforms` gives the
 * software node's `operatingSystem` on each page by the same index; null
 * leaves the property out, and a page past its end names the default
 * platforms.
 *
 * @param {object} [options]
 * @param {Record<string, object>} [options.base] Pages a suite needs in every build of its own, by key.
 * @returns {Record<string, {path: string, article: object, nodes: object[], text: string}>} Each page by its key.
 */
export function build({ pages = 10, dated = pages, published = '2026-07-01', platforms = [], base = {} } = {}) {
	const built = { ...base, 'en/about': aboutPage('en'), 'es/about': aboutPage('es') };
	for (let i = Object.keys(built).length; i < pages; i += 1) built[`page/${i}`] = page(`page-${i}`, 'en');
	Object.values(built).forEach(({ article, nodes }, i) => {
		article.datePublished = i < dated ? published : '2026-10-01';
		if (i < platforms.length) {
			const software = nodes.find((node) => node['@type'] === 'SoftwareApplication');
			if (platforms[i] === null) delete software.operatingSystem;
			else software.operatingSystem = platforms[i];
		}
	});
	return built;
}

/**
 * Write `built` as HTML files into a directory of their own, and its
 * `content` (path to text) as the content tree in another, run the check on
 * the two the way CI does, and say how it ended. A build with no `content`
 * gets an empty tree, so the check holds it to no page of the site's; its
 * `glossary`, when it gives one, is the glossary entries it was made from, in
 * the shape src/data/glossary.mjs exports them.
 *
 * Each page carries two blocks, as the built site does: the site-wide nodes
 * astro.config.mjs puts on every page, and the page's own graph from
 * Head.astro; what it says is the text of its `<main>`. The further blocks in
 * a page's `blocks` follow, each in a block of its own: a document is written
 * as JSON, a string as it is, so a test can hand the check one that does not
 * parse.
 *
 * @param {import('node:test').TestContext} t The test, which removes the build when it ends.
 * @param {Record<string, {path: string, nodes: object[], text?: string, blocks?: (object|string)[]}>|object[]} built
 *   The pages, under `content` the pages of the content tree they are built from, and under
 *   `glossary` the glossary entries.
 * @returns {{status: number|null, out: string, err: string}} The check's exit status and what it printed.
 */
export function check(t, built) {
	const dist = mkdtempSync(join(tmpdir(), 'check-structured-data-'));
	const tree = mkdtempSync(join(tmpdir(), 'check-structured-data-content-'));
	t.after(() => {
		rmSync(dist, { recursive: true, force: true });
		rmSync(tree, { recursive: true, force: true });
	});
	const { content = {}, glossary, ...pages } = built;
	for (const [path, text] of Object.entries(content)) {
		mkdirSync(dirname(join(tree, path)), { recursive: true });
		writeFileSync(join(tree, path), text);
	}
	const block = (body) => `<script type="application/ld+json">${body}</script>`;
	const script = (nodes) => block(JSON.stringify({ '@context': 'https://schema.org', '@graph': nodes }));
	const further = (doc) => block(typeof doc === 'string' ? doc : JSON.stringify(doc));
	for (const { path, nodes, text = '', blocks = [] } of Object.values(pages)) {
		const site = nodes.filter((node) => SITE_TYPES.has(node['@type']));
		const own = nodes.filter((node) => !SITE_TYPES.has(node['@type']));
		mkdirSync(dirname(join(dist, path)), { recursive: true });
		writeFileSync(
			join(dist, path),
			`<!DOCTYPE html><html><head>${script(site)}${script(own)}</head>` +
				`<body><main>${text}</main>${blocks.map(further).join('')}</body></html>`,
		);
	}
	const args = [CHECK, dist, tree];
	if (glossary !== undefined) {
		const folder = mkdtempSync(join(tmpdir(), 'check-structured-data-glossary-'));
		t.after(() => rmSync(folder, { recursive: true, force: true }));
		const file = join(folder, 'glossary.mjs');
		writeFileSync(file, `export const glossary = ${JSON.stringify(glossary)};\n`);
		args.push(`--glossary=${file}`);
	}
	const ran = spawnSync(process.execPath, args, { encoding: 'utf8' });
	return { status: ran.status, out: ran.stdout, err: ran.stderr };
}
