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
// the page says. Once the IndexNow job has submitted a deploy's pages, it
// keeps that deploy's manifest as an artifact of its run, the record of what
// the engines were last told. The next build finds the newest record, compares
// its own manifest with it and hands the IndexNow job the URLs whose digest
// changed, the URLs that are new and the URLs that are gone. When there is no
// record to compare with (the first deploy, a record that expired, one that
// cannot be read or one written by another version of this script), the job
// sends every URL of the sitemap, as it did before.
//
// The record is the IndexNow job's own, not the manifest the live site
// carries, because a deploy goes live before its pages are submitted. A run
// whose IndexNow job fails, or which a newer push cancels after it deployed
// and before it submitted, keeps no record, so the next run compares with the
// record before it and sends those pages along with its own.
//
// What a page says is read from the build, the way an engine reads it: its
// title, its meta description, the date the sitemap gives it (the last commit
// that changed its content or the data it is built from, as
// src/lib/content-dates.mjs dates it) and the text of its Markdown copy, the
// `index.md` beside it. The pages src/lib/page-markdown.mjs gives no Markdown
// copy, those that render their data through a component (the two landing
// pages and the catalogues among them), give the text of their <main> element
// instead, and a page it gives one that the build did not write fails the
// build. Nothing in the record depends on when the build ran, so two builds of
// the same tree publish the same manifest. The header lines of a copy that
// name the release (`Version:` and `Install:`, listed in
// src/lib/page-markdown.mjs) are left out, so stamping a release does not
// report every page as changed; the landing pages state the release in their
// text, and the sitemap dates them by it, so they are reported.
//
// Usage:
//   node scripts/indexnow-diff.mjs manifest [dist]
//     writes <dist>/indexnow-manifest.json (package.json `postbuild`, last)
//   node scripts/indexnow-diff.mjs last-submitted
//     asks the GitHub API (GITHUB_API_URL, GITHUB_REPOSITORY, GITHUB_TOKEN)
//     for the newest record an IndexNow job kept, and writes the id of its run
//     as `run-id` to $GITHUB_OUTPUT, for the workflow to download it from;
//     writes nothing when there is none
//   node scripts/indexnow-diff.mjs diff [--dist <dir>] --previous <file or URL> [--out <dir>]
//     checks the published manifest against the pages, compares it with the
//     previous one (a record, or a URL such as the live site's manifest, to
//     compare a local build with), prints the changed, new and removed URLs,
//     and writes into <dir> the URLs to submit (urls.json: {"urls": [...]}
//     and the lists behind it) and the manifest they were worked out from,
//     which the IndexNow job keeps once it has submitted them
import { createHash } from 'node:crypto';
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';
import { hasMarkdownCopy, withoutReleaseLines } from '../src/lib/page-markdown.mjs';
import { decode, markupOf, tags } from './shared/dist-pages.mjs';

const here = dirname(fileURLToPath(import.meta.url));

/** The file the build publishes, at the root of the site. */
export const MANIFEST_NAME = 'indexnow-manifest.json';
/** The file `diff --out` writes the URLs to submit to, beside a copy of the manifest. */
export const URLS_NAME = 'urls.json';
/**
 * What a digest is made of. A manifest written under another number is not
 * compared with, because its digests mean something else; changing what a
 * record holds means changing this number, and the next deploy sends every URL
 * once.
 */
export const MANIFEST_FORMAT = 1;
/** Every URL of the site starts with this and a slash. */
export const ORIGIN = `${siteUrl}${basePath}`;
/** How long a fetch from another server may take before the full list is sent instead. */
const FETCH_TIMEOUT_MS = 30_000;
/**
 * The artifact an IndexNow job keeps the manifest of the pages it submitted
 * in. .github/workflows/docs.yml uploads it once the submission has gone
 * through, and the next build compares with the newest one.
 */
export const SUBMITTED_ARTIFACT = 'indexnow-submitted';
/** The branch the site deploys from: the IndexNow jobs of its runs are the only ones that submit. */
export const DEPLOY_BRANCH = 'main';
/** The most artifacts the GitHub API lists on one page. */
const PER_PAGE = 100;
/** The most pages of artifacts read before giving up, far more than a record kept 90 days can fill. */
const MAX_PAGES = 50;

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

/** The route of a sitemap URL, as src/lib/page-markdown.mjs names routes: no base path and no slash at either end. */
export const routeOfUrl = (loc) => decodeURIComponent(loc.slice(ORIGIN.length + 1)).replace(/\/$/, '');

/**
 * What one page says, as one string: its title, its meta description, its
 * date and its text. The text is the Markdown copy beside the page without its
 * release lines, or, on a page src/lib/page-markdown.mjs gives no copy, the
 * text of its <main>. Which pages have a copy is that module's rule, not
 * whatever the build happens to hold: a copy the build should have written and
 * did not fails here, rather than the page being read another way and
 * reported as changed on this deploy and again on the one that restores it.
 */
export function pageRecord(dist, { loc, lastmod }) {
	const route = routeOfUrl(loc);
	const dir = join(dist, ...route.split('/').filter(Boolean));
	const htmlFile = join(dir, 'index.html');
	if (!existsSync(htmlFile)) throw new ManifestError(`the sitemap lists ${loc}, and the build wrote no ${htmlFile}.`);
	const html = readFileSync(htmlFile, 'utf8');
	const markup = markupOf(html);
	const title = decode(/<title>([\s\S]*?)<\/title>/i.exec(markup)?.[1] ?? '').trim();
	const description = (tags(markup, 'meta').find((meta) => meta.name === 'description')?.content ?? '').trim();
	let text;
	if (hasMarkdownCopy(route)) {
		const copy = join(dir, 'index.md');
		if (!existsSync(copy)) {
			throw new ManifestError(
				`${loc} has a Markdown copy by src/lib/page-markdown.mjs, and the build wrote no ${copy}: scripts/emit-page-markdown.mjs runs before the manifest.`,
			);
		}
		text = withoutReleaseLines(readFileSync(copy, 'utf8'));
	} else {
		text = mainText(html);
		if (text === null) {
			throw new ManifestError(`${loc} has no Markdown copy by src/lib/page-markdown.mjs and no <main> element to read its text from.`);
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

/**
 * The record to compare with, out of the artifacts the GitHub API lists: the
 * newest {@link SUBMITTED_ARTIFACT} that has not expired, kept by a run of this
 * repository's {@link DEPLOY_BRANCH}. A pull request, from a fork or not, can
 * upload an artifact of that name from a workflow it edits, and its run
 * submits nothing, so its artifact is never the record. The API does not say
 * in what order it lists artifacts, so the newest is the one created last,
 * and of two created in the same second the one with the larger id.
 *
 * @returns the artifact, or undefined when there is no record
 */
export function lastSubmitted(artifacts) {
	let newest;
	for (const artifact of artifacts) {
		const run = artifact.workflow_run;
		if (artifact.name !== SUBMITTED_ARTIFACT || artifact.expired !== false || !run) continue;
		if (run.head_branch !== DEPLOY_BRANCH || run.head_repository_id !== run.repository_id) continue;
		const later =
			newest === undefined ||
			artifact.created_at > newest.created_at ||
			(artifact.created_at === newest.created_at && artifact.id > newest.id);
		if (later) newest = artifact;
	}
	return newest;
}

/**
 * Every artifact named {@link SUBMITTED_ARTIFACT} of a repository, read from
 * the GitHub API a page at a time until it has listed as many as it counts.
 */
export async function submittedArtifacts({ api, repository, token }) {
	const artifacts = [];
	for (let page = 1; page <= MAX_PAGES; page += 1) {
		const url = `${api}/repos/${repository}/actions/artifacts?name=${SUBMITTED_ARTIFACT}&per_page=${PER_PAGE}&page=${page}`;
		const response = await fetch(url, {
			headers: { accept: 'application/vnd.github+json', authorization: `Bearer ${token}`, 'x-github-api-version': '2022-11-28' },
			signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
		});
		if (!response.ok) throw new Error(`the API answered ${response.status} to ${url}`);
		const listed = await response.json();
		if (!Array.isArray(listed?.artifacts) || !Number.isInteger(listed.total_count)) {
			throw new Error(`the API answered ${url} with no list of artifacts`);
		}
		artifacts.push(...listed.artifacts);
		if (listed.artifacts.length < PER_PAGE || artifacts.length >= listed.total_count) return artifacts;
	}
	throw new Error(`the API lists more than ${MAX_PAGES * PER_PAGE} artifacts named ${SUBMITTED_ARTIFACT}`);
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

/**
 * `last-submitted`: name the run whose IndexNow job kept the newest record, in
 * the step output `run-id`, for the workflow to download the record from. A
 * record that cannot be listed is not a reason to stop a deploy: with no
 * `run-id` the build compares with nothing and the full list goes out, as it
 * always did, with a warning on the run.
 */
async function findLastSubmitted() {
	const { GITHUB_API_URL: api = 'https://api.github.com', GITHUB_REPOSITORY: repository, GITHUB_TOKEN: token, GITHUB_OUTPUT: output } = process.env;
	if (!repository || !token || !output) {
		throw new ManifestError('last-submitted reads the GitHub API from a workflow step: it needs GITHUB_REPOSITORY, GITHUB_TOKEN and GITHUB_OUTPUT.');
	}
	let artifacts;
	try {
		artifacts = await submittedArtifacts({ api, repository, token });
	} catch (error) {
		console.log(`::warning::[indexnow] the records of the pages IndexNow was sent could not be listed (${error.cause?.code ?? error.message}): the full list goes out.`);
		return;
	}
	const record = lastSubmitted(artifacts);
	if (record === undefined) {
		console.log(
			`[indexnow] no IndexNow job of a run of ${DEPLOY_BRANCH} has kept a record that has not expired ` +
				`(${artifacts.length} artifacts named ${SUBMITTED_ARTIFACT} listed): the full list goes out.`,
		);
		return;
	}
	const run = record.workflow_run;
	console.log(`[indexnow] the pages were last submitted by run ${run.id}, of commit ${run.head_sha}, on ${record.created_at}.`);
	appendFileSync(output, `run-id=${run.id}\n`);
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
	const source = option(args, '--previous');
	if (!source) throw new ManifestError('say where the previous manifest is: --previous <file or URL>.');
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
		mkdirSync(out, { recursive: true });
		const reason = result.full ? previous.reason : null;
		writeFileSync(
			join(out, URLS_NAME),
			`${JSON.stringify({ previous: previous.from, reason, full: result.full, changed: result.changed, new: result.added, removed: result.removed, urls: result.urls }, null, 1)}\n`,
		);
		writeFileSync(join(out, MANIFEST_NAME), serialize(current));
	}
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
	const [command, ...args] = process.argv.slice(2);
	try {
		if (command === 'manifest') writeManifest(args);
		else if (command === 'last-submitted') await findLastSubmitted();
		else if (command === 'diff') await diff(args);
		else throw new ManifestError(`unknown command ${JSON.stringify(command)}: use \`manifest\`, \`last-submitted\` or \`diff\`.`);
	} catch (error) {
		if (!(error instanceof ManifestError)) throw error;
		console.error(`[indexnow] FAIL ${error.message}`);
		process.exit(1);
	}
}
