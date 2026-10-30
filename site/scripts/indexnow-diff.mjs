// Works out which pages a deploy changed, so IndexNow is told about those.
//
// IndexNow is how this site tells the search engines that take part in it
// (Bing, Yandex, Seznam, Naver and others) that a URL was added, updated or
// deleted, so they come back for it. The deploy used to send every URL of the
// sitemap after every merge, the whole site for a typo on one page, which
// tells an engine nothing about which pages changed. It also read that
// sitemap from the live site a moment after the deploy, where the edge could
// still be serving the copy of the deploy before.
//
// Now the build publishes a manifest beside the sitemap,
// `indexnow-manifest.json`: every URL of the sitemap with a digest of what
// the page says. Before the next deploy the build fetches the manifest the
// live site carries, compares it with its own and hands the IndexNow job the
// URLs whose digest changed, the URLs that are new and the URLs that are gone.
// When there is no previous manifest to compare with (the first deploy, a
// manifest that cannot be read, or one written by another version of this
// script), the job sends every URL of the sitemap, as it did before.
//
// What a page says is read from the build, the way an engine reads it: its
// title, its meta description, the date the sitemap gives it (the last commit
// that changed its content or the data it is built from, as
// src/lib/content-dates.mjs dates it) and the text of its Markdown copy, the
// `index.md` beside it. The two landing pages have no Markdown copy and give
// the text of their <main> element instead. Nothing in the record depends on
// when the build ran, so two builds of the same tree publish the same
// manifest. The header lines of a copy that name the release (`Version:` and
// `Install:`, listed in src/lib/page-markdown.mjs) are left out, so stamping a
// release does not report every page as changed; the landing pages state the
// release in their text, and the sitemap dates them by it, so they are
// reported.
//
// A run that a newer push cancels after it deployed and before it submitted
// leaves its pages to the sitemap's <lastmod>: the next run compares with
// the manifest that run deployed.
//
// Usage:
//   node scripts/indexnow-diff.mjs manifest [dist]
//     writes <dist>/indexnow-manifest.json (package.json `postbuild`, last)
//   node scripts/indexnow-diff.mjs diff [--dist <dir>] (--live | --previous <file or URL>) [--out <file>]
//     checks the published manifest against the pages, compares it with the
//     previous one, prints the changed, new and removed URLs, and writes the
//     URLs to submit to <file> as JSON ({"urls": [...]} and the lists behind it)
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';
import { withoutReleaseLines } from '../src/lib/page-markdown.mjs';
import { decode, markupOf, tags } from './shared/dist-pages.mjs';

const here = dirname(fileURLToPath(import.meta.url));

/** The file the build publishes, at the root of the site. */
export const MANIFEST_NAME = 'indexnow-manifest.json';
/**
 * What a digest is made of. A manifest written under another number is not
 * compared with, because its digests mean something else; changing what a
 * record holds means changing this number, and the next deploy sends every URL
 * once.
 */
export const MANIFEST_FORMAT = 1;
/** Every URL of the site starts with this and a slash. */
export const ORIGIN = `${siteUrl}${basePath}`;
/** How long the fetch of the live manifest may take before the full list is sent instead. */
const FETCH_TIMEOUT_MS = 30_000;

/** A failure that stops the build, with what to do about it in the message. */
export class ManifestError extends Error {}

/** Every <url> of the sitemap the build wrote, as `{ loc, lastmod }`, read from the shards its index lists. */
export function sitemapEntries(dist) {
	const index = join(dist, 'sitemap-index.xml');
	if (!existsSync(index)) throw new ManifestError(`${index} does not exist: there is no sitemap to read the pages from.`);
	const shards = [...readFileSync(index, 'utf8').matchAll(/<loc>([^<]+)<\/loc>/g)].map(([, loc]) => {
		if (!loc.startsWith(`${ORIGIN}/`)) throw new ManifestError(`the sitemap index lists ${loc}, outside ${ORIGIN}/.`);
		const file = join(dist, loc.slice(ORIGIN.length + 1));
		if (!existsSync(file)) throw new ManifestError(`the sitemap index lists ${loc}, which the build did not write.`);
		return file;
	});
	if (shards.length === 0) throw new ManifestError(`${index} lists no sitemap.`);
	const entries = [];
	const seen = new Set();
	for (const shard of shards) {
		for (const [block] of readFileSync(shard, 'utf8').matchAll(/<url>[\s\S]*?<\/url>/g)) {
			const loc = /<loc>([^<]+)<\/loc>/.exec(block)?.[1];
			const lastmod = /<lastmod>([^<]+)<\/lastmod>/.exec(block)?.[1];
			if (!loc?.startsWith(`${ORIGIN}/`)) throw new ManifestError(`the sitemap lists ${loc}, outside ${ORIGIN}/.`);
			if (!lastmod) {
				throw new ManifestError(
					`the sitemap gives ${loc} no <lastmod>: the manifest is written after scripts/add-sitemap-lastmod.mjs has dated every URL.`,
				);
			}
			if (seen.has(loc)) throw new ManifestError(`the sitemap lists ${loc} twice.`);
			seen.add(loc);
			entries.push({ loc, lastmod });
		}
	}
	if (entries.length === 0) throw new ManifestError('the sitemap lists no URL.');
	return entries;
}

/** The text of a page's <main> element, with its tags, scripts and styles out and its spacing collapsed. */
export function mainText(html) {
	const main = /<main\b[^>]*>([\s\S]*)<\/main>/i.exec(markupOf(html));
	if (!main) return null;
	return decode(main[1].replace(/<[^>]*>/g, ' ')).replace(/\s+/g, ' ').trim();
}

/**
 * What one page says, as one string: its title, its meta description, its
 * date and its text. The text is the Markdown copy beside the page without its
 * release lines, or the text of <main> where the page has no copy.
 */
export function pageRecord(dist, { loc, lastmod }) {
	const dir = join(dist, ...loc.slice(ORIGIN.length + 1).split('/').filter(Boolean).map(decodeURIComponent));
	const htmlFile = join(dir, 'index.html');
	if (!existsSync(htmlFile)) throw new ManifestError(`the sitemap lists ${loc}, and the build wrote no ${htmlFile}.`);
	const html = readFileSync(htmlFile, 'utf8');
	const markup = markupOf(html);
	const title = decode(/<title>([\s\S]*?)<\/title>/i.exec(markup)?.[1] ?? '').trim();
	const description = (tags(markup, 'meta').find((meta) => meta.name === 'description')?.content ?? '').trim();
	const copy = join(dir, 'index.md');
	let text;
	if (existsSync(copy)) {
		text = withoutReleaseLines(readFileSync(copy, 'utf8'));
	} else {
		text = mainText(html);
		if (text === null) {
			throw new ManifestError(`${loc} has neither a Markdown copy (${copy}) nor a <main> element to read its text from.`);
		}
	}
	return [`Title: ${title}`, `Description: ${description}`, `Modified: ${lastmod}`, '', text].join('\n');
}

/** The sha256 of a record, in hex. */
export const digestOf = (record) => createHash('sha256').update(record, 'utf8').digest('hex');

/** The manifest of a build: every URL of its sitemap with the digest of its record, in URL order. */
export function buildManifest(dist) {
	const pages = {};
	for (const entry of sitemapEntries(dist).sort((a, b) => (a.loc < b.loc ? -1 : 1))) {
		pages[entry.loc] = digestOf(pageRecord(dist, entry));
	}
	return { format: MANIFEST_FORMAT, pages };
}

/** A manifest as the file holds it. */
export const serialize = (manifest) => `${JSON.stringify(manifest, null, 1)}\n`;

/**
 * The pages of a manifest read back, or the reason it cannot be compared with:
 * not JSON, another format, or an entry that is not a URL of this site with a
 * sha256.
 */
export function parseManifest(text) {
	let manifest;
	try {
		manifest = JSON.parse(text);
	} catch (error) {
		return { reason: `it is not JSON (${error.message})` };
	}
	if (manifest?.format !== MANIFEST_FORMAT) {
		return { reason: `it is format ${JSON.stringify(manifest?.format)}, and this script writes format ${MANIFEST_FORMAT}` };
	}
	const pages = manifest.pages;
	if (typeof pages !== 'object' || pages === null || Array.isArray(pages)) return { reason: 'it has no pages' };
	for (const [url, digest] of Object.entries(pages)) {
		if (!url.startsWith(`${ORIGIN}/`)) return { reason: `it lists ${url}, outside ${ORIGIN}/` };
		if (typeof digest !== 'string' || !/^[0-9a-f]{64}$/.test(digest)) return { reason: `its entry for ${url} is not a sha256` };
	}
	return { pages };
}

/**
 * The previous manifest, from a file or a URL: `{ pages, from }` when it can
 * be compared with, `{ reason, from }` when it cannot. Nothing here fails the
 * build: without a previous manifest the full list goes out, as it always did.
 */
export async function loadPrevious(source) {
	if (/^https?:\/\//.test(source)) {
		let response;
		try {
			response = await fetch(source, { signal: AbortSignal.timeout(FETCH_TIMEOUT_MS), redirect: 'follow' });
		} catch (error) {
			return { from: source, reason: `it could not be fetched (${error.cause?.code ?? error.message})` };
		}
		if (response.status === 404) return { from: source, reason: 'the live site has none yet (404)' };
		if (!response.ok) return { from: source, reason: `the live site answered ${response.status}` };
		return { from: source, ...parseManifest(await response.text()) };
	}
	if (!existsSync(source)) return { from: source, reason: 'there is no such file' };
	return { from: source, ...parseManifest(readFileSync(source, 'utf8')) };
}

/**
 * What to submit, given the current pages and the previous ones (or none):
 * the URLs whose digest changed, the new ones and the removed ones, each list
 * in URL order; with no previous pages, every current URL.
 */
export function urlsToSubmit(current, previous) {
	const urls = Object.keys(current).sort();
	if (!previous) return { full: true, changed: [], added: [], removed: [], urls };
	const changed = urls.filter((url) => Object.hasOwn(previous, url) && previous[url] !== current[url]);
	const added = urls.filter((url) => !Object.hasOwn(previous, url));
	const removed = Object.keys(previous)
		.filter((url) => !Object.hasOwn(current, url))
		.sort();
	return { full: false, changed, added, removed, urls: [...changed, ...added, ...removed].sort() };
}

/** The value of `--name` in an argument list, or undefined. */
function option(args, name) {
	const at = args.indexOf(name);
	return at === -1 ? undefined : args[at + 1];
}

/** `manifest [dist]`: write the manifest of a build into it. */
function writeManifest(args) {
	const dist = resolve(args[0] ?? join(here, '..', 'dist'));
	const manifest = buildManifest(dist);
	writeFileSync(join(dist, MANIFEST_NAME), serialize(manifest));
	console.log(`[indexnow] wrote ${MANIFEST_NAME} with the digests of ${Object.keys(manifest.pages).length} pages`);
}

/** `diff ...`: compare the build with the previous manifest and say what to submit. */
async function diff(args) {
	const dist = resolve(option(args, '--dist') ?? join(here, '..', 'dist'));
	const published = join(dist, MANIFEST_NAME);
	if (!existsSync(published)) {
		throw new ManifestError(`${published} does not exist: run \`node scripts/indexnow-diff.mjs manifest\` after the build.`);
	}
	const current = buildManifest(dist);
	if (readFileSync(published, 'utf8') !== serialize(current)) {
		throw new ManifestError(
			`${published} is not the manifest the built pages give: a step after it changed the pages or the sitemap, so it has to run last.`,
		);
	}
	const source = args.includes('--live')
		? `${ORIGIN}/${MANIFEST_NAME}?v=${process.env.GITHUB_SHA ?? Date.now()}`
		: option(args, '--previous');
	if (!source) throw new ManifestError('say where the previous manifest is: --live or --previous <file or URL>.');
	const previous = await loadPrevious(source);
	const result = urlsToSubmit(current.pages, previous.pages);
	const total = Object.keys(current.pages).length;
	if (result.full) {
		console.log(`[indexnow] no previous manifest to compare with from ${previous.from}: ${previous.reason}.`);
		console.log(`[indexnow] the full list goes out: ${result.urls.length} URLs.`);
	} else {
		console.log(`[indexnow] compared with ${previous.from} (${Object.keys(previous.pages).length} pages).`);
		console.log(
			`[indexnow] ${result.changed.length} changed, ${result.added.length} new and ${result.removed.length} removed ` +
				`of ${total} pages: ${result.urls.length} URLs to submit.`,
		);
		for (const [label, list] of [['changed', result.changed], ['new', result.added], ['removed', result.removed]]) {
			for (const url of list) console.log(`  ${label.padEnd(7)} ${url}`);
		}
	}
	const out = option(args, '--out');
	if (out) {
		mkdirSync(dirname(resolve(out)), { recursive: true });
		const reason = result.full ? previous.reason : null;
		writeFileSync(
			out,
			`${JSON.stringify({ previous: previous.from, reason, full: result.full, changed: result.changed, new: result.added, removed: result.removed, urls: result.urls }, null, 1)}\n`,
		);
	}
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
	const [command, ...args] = process.argv.slice(2);
	try {
		if (command === 'manifest') writeManifest(args);
		else if (command === 'diff') await diff(args);
		else throw new ManifestError(`unknown command ${JSON.stringify(command)}: use \`manifest\` or \`diff\`.`);
	} catch (error) {
		if (!(error instanceof ManifestError)) throw error;
		console.error(`[indexnow] FAIL ${error.message}`);
		process.exit(1);
	}
}
