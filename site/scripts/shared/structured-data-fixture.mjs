// Small builds for the tests of check-structured-data.mjs.
//
// The check reads a whole build, and some of what it asks is asked of the
// whole site at once: the software node on every page, the site-wide block
// under its byte budget, a share of pages edited since they were first
// published. A test that hands it a build of a few pages has to give it all
// of that, or every test fails on what it did not mean to test. So the pages
// are written here, once, whole by default, and every test file of the check
// builds on them: a check that adds a site-wide requirement adds it to this
// file, and each suite keeps testing only its own defect.
//
// A page is data until the build is written: its article node, every node of
// its graph and what it says, which a test changes in place before `check`
// writes the build. Each page carries two ld+json blocks, as the built site
// does: the site-wide nodes astro.config.mjs puts on every page, and the
// page's own graph from Head.astro. A page may carry further blocks, which a
// test gives whole, or as written when it means one not to parse.
//
// Nothing here is installed: the tests run before the site's dependencies are.
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../../src/data/site.mjs';
import { topicForSlug } from '../../src/data/topics.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const CHECK = join(here, '..', 'check-structured-data.mjs');

/** The site's own address, as every URL of a page starts. */
export const ORIGIN = `${siteUrl}${basePath}`;

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

/**
 * The four nodes astro.config.mjs puts on every page.
 *
 * @param {unknown} [operatingSystem] What the software node names; null leaves the property out.
 * @returns {object[]} Person, WebSite, SoftwareApplication and SoftwareSourceCode.
 */
export function siteNodes(operatingSystem = PLATFORMS) {
	return [
		{ '@type': 'Person', '@id': SITE.person, name: 'The maintainer' },
		{ '@type': 'WebSite', '@id': SITE.website, name: 'phonometry', url: `${ORIGIN}/` },
		{
			'@type': 'SoftwareApplication',
			'@id': SITE.software,
			name: 'phonometry',
			...(operatingSystem === null ? {} : { operatingSystem }),
		},
		{ '@type': 'SoftwareSourceCode', '@id': SITE.source, name: 'phonometry' },
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
 * A build the check has nothing to report on: the pages in `base`, then
 * plain English pages up to `pages` in all.
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
	const built = { ...base };
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
 * gets an empty tree, so the check holds it to no page of the site's.
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
 *   The pages, and under `content` the pages of the content tree they are built from.
 * @returns {{status: number|null, out: string, err: string}} The check's exit status and what it printed.
 */
export function check(t, built) {
	const dist = mkdtempSync(join(tmpdir(), 'check-structured-data-'));
	const tree = mkdtempSync(join(tmpdir(), 'check-structured-data-content-'));
	t.after(() => {
		rmSync(dist, { recursive: true, force: true });
		rmSync(tree, { recursive: true, force: true });
	});
	const { content = {}, ...pages } = built;
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
	const ran = spawnSync(process.execPath, [CHECK, dist, tree], { encoding: 'utf8' });
	return { status: ran.status, out: ran.stdout, err: ran.stderr };
}
