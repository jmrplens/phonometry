// Small builds for the tests of check-structured-data.mjs.
//
// The check reads a whole build, and some of what it asks is asked of the
// whole site at once: the software's history on every page, the About page in
// both languages, a share of pages edited since they were first published. A
// test that hands it a build of a few pages has to give it all of that, or
// every test fails on what it did not mean to test. So the pages are written
// here, once, whole by default, and every test file of the check builds on
// them: a check that adds a site-wide requirement adds it to this file, and
// each suite keeps testing only its own defect.
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
 * The date of the last commit `git log` lists with these arguments, as
 * `YYYY-MM-DD` in the committer's own time, the way the check reads it.
 *
 * @param {...string} args Arguments after `git -C <repository root> log`.
 * @returns {string} The date.
 */
const commitDate = (...args) =>
	execFileSync('git', ['-C', REPOSITORY_ROOT, 'log', '--format=%cI', ...args], { encoding: 'utf8' })
		.trim()
		.split('\n')
		.at(-1)
		.slice(0, 10);

/** The repository's first commit, which the software's `dateCreated` has to give. */
export const FIRST_COMMIT = commitDate('--max-parents=0', 'HEAD');
/** The last commit under src/, which the software's `dateModified` has to give. */
export const LIBRARY_MODIFIED = commitDate('-1', '--', 'src');

/** The platforms the software node names when a test does not say otherwise. */
export const PLATFORMS = ['Linux', 'macOS', 'Windows'];

const PERSON = 'https://jmrp.io/#person';
const WEBSITE = `${ORIGIN}/#website`;
const REPOSITORY = 'https://github.com/jmrplens/phonometry';
const SOFTWARE = `${REPOSITORY}#software`;

/** The years of the maintainer's research role, as the Person node dates it and the About page states it. */
export const RESEARCH = { start: '2019', end: '2023' };

/**
 * The four nodes astro.config.mjs puts on every page, whole: the software's
 * history the check reads from git, and the maintainer's dated roles as the
 * Person node jmrp.io publishes gives them, one the About page names and one
 * it does not.
 *
 * @param {object} [options]
 * @param {unknown} [options.operatingSystem] What the software node names; null leaves the property out.
 * @returns {object[]} Person, WebSite, SoftwareApplication and SoftwareSourceCode.
 */
export function siteNodes({ operatingSystem = PLATFORMS } = {}) {
	return [
		{
			'@type': 'Person',
			'@id': PERSON,
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
		{ '@type': 'WebSite', '@id': WEBSITE, name: 'phonometry', url: `${ORIGIN}/` },
		{
			'@type': 'SoftwareApplication',
			'@id': SOFTWARE,
			name: 'phonometry',
			alternateName: 'PyOctaveBand',
			codeRepository: REPOSITORY,
			releaseNotes: `${REPOSITORY}/releases`,
			softwareHelp: { '@id': WEBSITE },
			sameAs: ['https://pypi.org/project/phonometry/', 'https://pypi.org/project/PyOctaveBand/'],
			dateCreated: FIRST_COMMIT,
			dateModified: LIBRARY_MODIFIED,
			...(operatingSystem === null ? {} : { operatingSystem }),
		},
		{
			'@type': 'SoftwareSourceCode',
			'@id': `${REPOSITORY}#source-code`,
			codeRepository: REPOSITORY,
			dateCreated: FIRST_COMMIT,
			targetProduct: { '@id': SOFTWARE },
			archivedAt: `https://archive.softwareheritage.org/browse/origin/?origin_url=${REPOSITORY}`,
		},
	];
}

/**
 * The built HTML of one page whose structured data is whole.
 *
 * The page is English unless its route starts with `es/`. A page under a
 * topic names the topic's section, and a Spanish page points back at its
 * English original.
 *
 * @param {string} route The page's route without slashes at either end, `es/start/about` for one.
 * @param {object} [options]
 * @param {string} [options.datePublished] The article's first publication.
 * @param {string} [options.dateModified] The article's last edit.
 * @param {string|string[]} [options.types] The article node's `@type`.
 * @param {object[]} [options.nodes] The site-wide nodes, `siteNodes()` unless given.
 * @param {string} [options.text] What the page says, as the body of its HTML.
 * @returns {string} The page's HTML.
 */
export function page(
	route,
	{
		datePublished = '2026-10-01',
		dateModified = '2026-10-01',
		types = 'TechArticle',
		nodes = siteNodes(),
		text = '',
	} = {},
) {
	const lang = route.startsWith('es/') ? 'es' : 'en';
	const slug = route.replace(/^es\//, '');
	const url = `${ORIGIN}/${route}/`;
	const twin = `${ORIGIN}${lang === 'es' ? '' : '/es'}/${slug}/#article`;
	const topic = topicForSlug(slug);
	const graph = [
		...nodes,
		{
			'@type': types,
			'@id': `${url}#article`,
			url,
			inLanguage: lang,
			[lang === 'es' ? 'translationOfWork' : 'workTranslation']: { '@id': twin },
			...(topic ? { articleSection: topic.label[lang] } : {}),
			...Object.fromEntries(
				[
					'about',
					'author',
					'description',
					'headline',
					'image',
					'isPartOf',
					'mainEntityOfPage',
					'publisher',
					'speakable',
					'wordCount',
				].map((field) => [field, 'a value']),
			),
			datePublished,
			dateModified,
		},
		{
			'@type': 'BreadcrumbList',
			itemListElement: [
				{ position: 1, name: 'Home', item: `${ORIGIN}/` },
				{ position: 2, name: slug, item: url },
			],
		},
	];
	const block = JSON.stringify({ '@context': 'https://schema.org', '@graph': graph });
	return (
		`<!doctype html><html lang="${lang}"><head><script type="application/ld+json">${block}</script></head>` +
		`<body><main>${text}</main></body></html>`
	);
}

/** What each About page says of the research role, in its own language. */
export const ABOUT_TEXT = {
	en: `<p>I worked as an acoustics researcher at the UPV from ${RESEARCH.start} to ${RESEARCH.end}.</p>`,
	es: `<p>Trabajé como investigador en acústica en la UPV de ${RESEARCH.start} a ${RESEARCH.end}.</p>`,
};

/**
 * The About page of one language, typed and worded as the check asks.
 *
 * @param {'en'|'es'} lang The page's language.
 * @param {object} [options] As `page()` takes them; `types` and `text` default to the About page's own.
 * @returns {string} The page's HTML.
 */
export function aboutPage(lang, options = {}) {
	return page(lang === 'es' ? 'es/start/about' : 'start/about', {
		types: ['AboutPage', 'TechArticle'],
		text: ABOUT_TEXT[lang],
		...options,
	});
}

/** Where each About page is written in a build. */
export const ABOUT_FILES = { en: 'start/about/index.html', es: 'es/start/about/index.html' };

/**
 * Write a build of `files` into a directory of its own, run the check on it
 * the way CI does, and say how it ended.
 *
 * @param {import('node:test').TestContext} t The test, which removes the build when it ends.
 * @param {Record<string, string>} files Each page's HTML by its path in the build.
 * @returns {{status: number|null, out: string, err: string}} The check's exit status and what it printed.
 */
export function runCheck(t, files) {
	const dist = mkdtempSync(join(tmpdir(), 'check-structured-data-'));
	t.after(() => rmSync(dist, { recursive: true, force: true }));
	for (const [path, html] of Object.entries(files)) {
		mkdirSync(dirname(join(dist, path)), { recursive: true });
		writeFileSync(join(dist, path), html);
	}
	const ran = spawnSync(process.execPath, [CHECK, dist], { encoding: 'utf8' });
	return { status: ran.status, out: ran.stdout, err: ran.stderr };
}
