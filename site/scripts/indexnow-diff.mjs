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
// record to compare with (the first deploy, a record that expired or could
// not be downloaded, one that cannot be read or one written by another
// version of this script), the job sends every URL of the sitemap, as it did
// before, and the deploy goes on.
//
// The record is the IndexNow job's own, not the manifest the live site
// carries, because a deploy goes live before its pages are submitted. A run
// whose IndexNow job fails, or which a newer push cancels after it deployed
// and before it submitted, keeps no record, so the next run compares with the
// record before it and sends those pages along with its own. A record is kept
// only while no deploy has gone out after the one it describes, so the newest
// record is the one of the newest deploy that kept one, in whatever order
// failed jobs are re-run: a job re-run after a newer deploy keeps nothing, and
// the newer deploy's own job, re-run before or after it, keeps its record. A
// manifest older than a deploy that went out after it would otherwise be the
// newest record, and a page that deploy added and the next one removes would
// be in neither manifest the next build compares, so its removal would never
// be sent.
//
// A job can submit and still keep no record: the deployments cannot be
// listed, a newer push cancels the run between the submission and the record,
// the upload of the record fails, or the submission reaches IndexNow and the
// step fails after it. A page that deploy added and the next one removes is
// then in no record, and the record alone would never send its removal. So the
// build also reads the list the newest deploy after the record handed its
// IndexNow job (`indexnow-urls`, uploaded before the deploy, or on a deploy
// re-run by that job before it submits, and kept as long as a record is), and
// sends as removed every page that list or its manifest names and this build
// no longer has. The other way round, a page that list removed, gave other
// content or was to send, and this build has as the record has it, is sent
// too, as new or as changed: IndexNow was last told what the list said, or was
// never told it, and the record holds neither. The list a build hands on, like
// the one the job of a deploy re-run works out again and hands on, carries
// those removals and those pages in turn, until a job keeps a record, so a
// chain of deploys that kept no record loses none of them.
//
// A deploy job re-run after a newer deploy, as "Re-run failed jobs" runs it
// on a run whose deploy failed, puts its run's pages back on the site after
// that deploy, and the list its build handed on, worked out before it,
// against the record of the build's time, says nothing of the pages that
// deploy changed and this one puts back. When the deploy job ran in a later
// attempt than the build, the IndexNow job works the list out again: it
// compares the manifest the build handed on with the newest record and the
// newest list handed on after it, its own run's left out, as a build would,
// hands that list on in place of the build's and submits it. No later build
// reads the build's list, older than the newest record, so a job that
// submitted and kept no record would otherwise leave what it sent in no list.
// Its deploy is then the newest, so it keeps its record like any other, while
// no deploy has gone out after it.
//
// What a page says is read from the build, the way an engine reads it: its
// title, its meta description, the date the sitemap gives it (the last commit
// that changed its content or the data it is built from, as
// src/lib/content-dates.mjs dates it) and the text of its Markdown copy, the
// `index.md` beside it. The pages src/lib/page-markdown.mjs gives no Markdown
// copy, those that render their data through a component (the two landing
// pages and the catalogues among them), give the text of their <main> element
// instead, less what the site's frame puts there around every page: the
// release banner, the footer with the page's dates and the titles of the
// pages before and after it, and the credit that follows. A page the module
// gives a copy that the build did not write fails the build. Nothing in the
// record depends on when the build ran, so two builds of the same tree
// publish the same manifest. The header lines of a copy that
// name the release (`Version:` and `Install:`, listed in
// src/lib/page-markdown.mjs) are left out, so stamping a release does not
// report every page as changed; the landing pages state the release in their
// text, and the sitemap dates them by it, so they are reported.
//
// Usage:
//   node scripts/indexnow-diff.mjs manifest [dist]
//     writes <dist>/indexnow-manifest.json (package.json `postbuild`, last)
//   node scripts/indexnow-diff.mjs last-submitted [--except-run <id>]
//     asks the GitHub API (GITHUB_API_URL, GITHUB_REPOSITORY, GITHUB_TOKEN)
//     for the newest record an IndexNow job kept, and writes the id of its run
//     as `run-id` to $GITHUB_OUTPUT, for the workflow to download it from;
//     writes nothing when there is none; and the run of the newest list a
//     deploy handed IndexNow after that record, as `pending-run-id`, leaving
//     out the list of run <id>, the one a deploy re-run of that run works
//     out again
//   node scripts/indexnow-diff.mjs diff [--dist <dir> | --current <manifest>] --previous <file or URL> [--pending <dir>] [--out <dir>]
//     checks the published manifest against the pages, or reads the manifest
//     a build handed on (`--current`, where there are no pages: the IndexNow
//     job of a deploy re-run), compares it with the previous one (a record,
//     or a URL such as the live site's manifest, to compare a local build
//     with) and with the list a later deploy handed IndexNow (the folder
//     `--out` wrote), prints the changed, new and removed URLs, and writes
//     into <dir> the URLs to submit (urls.json: {"urls": [...]} and the
//     lists behind it) and the manifest they were worked out from, which the
//     IndexNow job keeps once it has submitted them
//   node scripts/indexnow-diff.mjs keep-record --deployed-at <time>
//     asks the GitHub API (GITHUB_GRAPHQL_URL as well) for the deployments of
//     the site made after <time>, when this run's pages went out, and writes
//     `keep=true` to $GITHUB_OUTPUT when none has gone out since (one that
//     failed has not), `keep=false` when one has or when the deployments
//     cannot be listed
import { createHash } from 'node:crypto';
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';
import { hasMarkdownCopy, withoutReleaseLines } from '../src/lib/page-markdown.mjs';
import { attributes, decode, markupOf, tags } from './shared/dist-pages.mjs';

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
/**
 * The artifact a build hands its IndexNow job the list in (urls.json and the
 * manifest), uploaded before the deploy, so before any submission: the next
 * build reads the newest one after the record for the pages it was to submit,
 * which a job that kept no record may have submitted or may never have, and
 * sends them again. The IndexNow job of a deploy re-run uploads the list it
 * works out again under the same name, in place of the build's, before it
 * submits.
 */
export const HANDED_ARTIFACT = 'indexnow-urls';
/** The branch the site deploys from: the IndexNow jobs of its runs are the only ones that submit. */
export const DEPLOY_BRANCH = 'main';
/** The most artifacts the GitHub API lists on one page. */
const PER_PAGE = 100;
/** The most pages of artifacts read before giving up, far more than a record kept 90 days can fill. */
const MAX_PAGES = 50;
/** The environment .github/workflows/docs.yml deploys the site to. */
export const PAGES_ENVIRONMENT = 'github-pages';
/**
 * The states, as the GitHub GraphQL API names them, of a deployment whose
 * pages never went out, so that the site still serves the deploy before it.
 */
export const NOT_DEPLOYED = new Set(['ABANDONED', 'ERROR', 'FAILURE']);
/** A moment as the deploy job writes it and the GitHub API gives one: UTC, to the second. */
const MOMENT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;
/** How many deployments one request lists, newest first: the newest one or two are all a check reads. */
const DEPLOYMENTS_PER_PAGE = 20;

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

/** The elements that have no end tag, so that a marked one takes nothing but itself out. */
const VOID_ELEMENTS = new Set(['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr']);

/**
 * Markup without the elements marked `data-pagefind-ignore`, each taken out
 * with everything it holds, down to the end tag that closes it, however many
 * elements of its name it nests. The mark is the site's own for text a page
 * shows that is not the page's: the release banner of
 * src/components/Banner.astro and the label of a heading's anchor. The build
 * writes balanced HTML, so a marked element it leaves open is a fault, and it
 * fails here rather than take the rest of the page with it.
 */
export function withoutIgnored(markup) {
	const tag = /<(\/?)([a-z][\w-]*)\b((?:[^>"]|"[^"]*")*)>/gi;
	let kept = '';
	let from = 0;
	for (let open = tag.exec(markup); open !== null; open = tag.exec(markup)) {
		const [whole, closing, name, rest] = open;
		if (closing || !Object.hasOwn(attributes(whole), 'data-pagefind-ignore')) continue;
		kept += markup.slice(from, open.index);
		const element = name.toLowerCase();
		if (!VOID_ELEMENTS.has(element) && !rest.endsWith('/')) {
			let depth = 1;
			while (depth > 0) {
				const next = tag.exec(markup);
				if (next === null) {
					throw new ManifestError(`a <${element} data-pagefind-ignore> is never closed: ${markup.slice(open.index, open.index + 120)}`);
				}
				if (next[2].toLowerCase() !== element) continue;
				if (next[1]) depth -= 1;
				else if (!next[3].endsWith('/')) depth += 1;
			}
		}
		from = tag.lastIndex;
	}
	return kept + markup.slice(from);
}

/**
 * The text of a page's <main> element that is the page's own, with its tags,
 * scripts and styles out and its spacing collapsed. What the site's frame
 * puts into <main> around the page is left out, since it changes on pages
 * whose text did not: the elements marked `data-pagefind-ignore` (see
 * {@link withoutIgnored}), and the page footer with what follows it, which is
 * Starlight's footer (the link to edit the page, its dates and the titles of
 * the pages before and after it) and the credit src/components/Footer.astro
 * adds. That footer is the last <footer> of the <main>, after the page's
 * content: the entries of a page may carry footers of their own, as the terms
 * of the glossary do, and those are the page's text.
 */
export function mainText(html) {
	const main = /<main\b[^>]*>([\s\S]*)<\/main>/i.exec(markupOf(html));
	if (!main) return null;
	const footer = [...main[1].matchAll(/<footer\b/gi)].at(-1);
	const own = footer === undefined ? main[1] : main[1].slice(0, footer.index);
	return decode(withoutIgnored(own).replace(/<[^>]*>/g, ' ')).replace(/\s+/g, ' ').trim();
}

/** The route of a sitemap URL, as src/lib/page-markdown.mjs names routes: no base path and no slash at either end. */
export const routeOfUrl = (loc) => decodeURIComponent(loc.slice(ORIGIN.length + 1)).replace(/\/$/, '');

/**
 * What one page says, as one string: its title, its meta description, its
 * date and its text. The text is the Markdown copy beside the page without its
 * release lines, or, on a page src/lib/page-markdown.mjs gives no copy, the
 * page's own text in its <main> ({@link mainText}). Which pages have a copy
 * is that module's rule, not whatever the build happens to hold: a copy the
 * build should have written and did not fails here, rather than the page
 * being read another way and reported as changed on this deploy and again on
 * the one that restores it.
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
 * build: without a previous manifest the full list goes out, as it always did,
 * and so it does when the manifest cannot be read, a body cut off on the way
 * or a path that holds no file, as a download that failed half way can leave.
 */
export async function loadPrevious(source) {
	if (/^https?:\/\//.test(source)) {
		let response;
		let text;
		try {
			response = await fetch(source, { signal: AbortSignal.timeout(FETCH_TIMEOUT_MS), redirect: 'follow' });
			if (response.status === 404) return { from: source, reason: 'the live site has none yet (404)' };
			if (!response.ok) return { from: source, reason: `the live site answered ${response.status}` };
			text = await response.text();
		} catch (error) {
			return { from: source, reason: `it could not be fetched (${error.cause?.code ?? error.message})` };
		}
		return { from: source, ...parseManifest(text) };
	}
	if (!existsSync(source)) return { from: source, reason: 'there is no such file' };
	let text;
	try {
		text = readFileSync(source, 'utf8');
	} catch (error) {
		return { from: source, reason: `it could not be read (${error.code ?? error.message})` };
	}
	return { from: source, ...parseManifest(text) };
}

/**
 * What to submit, given the current pages, the previous ones (or none) and
 * the list a later deploy handed IndexNow (or none), `{ pages, removed, new,
 * urls }`: the URLs whose digest changed, the new ones and the removed ones,
 * each list in URL order. A page is removed when the previous pages, the
 * handed list's pages, its removals or the pages it was to send name it and
 * the current pages do not. A current page is new when the previous pages
 * lack it, or the handed list removed it or was to send it as new, and
 * changed when its digest differs from theirs or from the handed list's, or
 * the list was to send it otherwise: what IndexNow was last told of a page
 * may be the handed list's, a page that list removed or changed and this
 * build puts back as the previous pages had it differs from what IndexNow
 * holds, and a page the list was to send may never have reached IndexNow,
 * its job having kept no record. With no previous pages, every current URL,
 * and the removals still.
 */
export function urlsToSubmit(current, previous, pending) {
	const urls = Object.keys(current).sort();
	const handed = pending?.pages ?? {};
	const handedRemoved = new Set(pending?.removed ?? []);
	const handedNew = new Set(pending?.new ?? []);
	const handedSent = new Set(pending?.urls ?? []);
	const named = new Set([...Object.keys(previous ?? {}), ...Object.keys(handed), ...handedRemoved, ...handedSent]);
	const removed = [...named].filter((url) => !Object.hasOwn(current, url)).sort();
	if (!previous) return { full: true, changed: [], added: [], removed, urls: [...urls, ...removed].sort() };
	const added = urls.filter((url) => !Object.hasOwn(previous, url) || handedRemoved.has(url) || handedNew.has(url));
	const changed = urls.filter(
		(url) =>
			Object.hasOwn(previous, url) &&
			!handedRemoved.has(url) &&
			!handedNew.has(url) &&
			(previous[url] !== current[url] || handedSent.has(url) || (Object.hasOwn(handed, url) && handed[url] !== current[url])),
	);
	return { full: false, changed, added, removed, urls: [...changed, ...added, ...removed].sort() };
}

/**
 * The list a deploy handed IndexNow, from the folder `diff --out` wrote:
 * `{ pages, removed, new, urls, from }`, `{ absent, from }` when there is no
 * such folder (no deploy after the record handed one, or its download was set
 * aside), or `{ reason, from }` when it cannot be read, or its removals or
 * the pages it was to send are not a list of pages of the site.
 * Nothing here fails the build either: the record is still compared with.
 */
export function loadPending(dir) {
	const from = dir;
	if (!existsSync(dir)) return { from, absent: true };
	let urls;
	try {
		urls = JSON.parse(readFileSync(join(dir, URLS_NAME), 'utf8'));
	} catch (error) {
		return { from, reason: error.code === 'ENOENT' ? `there is no ${URLS_NAME}` : `its ${URLS_NAME} is no list (${error.code ?? error.message})` };
	}
	const ofSite = (list) => Array.isArray(list) && list.every((url) => typeof url === 'string' && url.startsWith(`${ORIGIN}/`));
	const { removed, new: added, urls: sent } = urls ?? {};
	if (!ofSite(removed)) return { from, reason: `its ${URLS_NAME} names no removed pages of ${ORIGIN}/` };
	if (!ofSite(added) || !ofSite(sent)) return { from, reason: `its ${URLS_NAME} names no pages of ${ORIGIN}/ to send` };
	let text;
	try {
		text = readFileSync(join(dir, MANIFEST_NAME), 'utf8');
	} catch (error) {
		return { from, reason: `its ${MANIFEST_NAME} could not be read (${error.code ?? error.message})` };
	}
	const manifest = parseManifest(text);
	if (manifest.reason) return { from, reason: `its ${MANIFEST_NAME}: ${manifest.reason}` };
	return { from, pages: manifest.pages, removed, new: added, urls: sent };
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

/** Whether artifact `a` was created after `b`: later, or in the same second with a larger id. */
const createdAfter = (a, b) => a.created_at > b.created_at || (a.created_at === b.created_at && a.id > b.id);

/**
 * The list to read beside the record, out of the artifacts the GitHub API
 * lists: the newest {@link HANDED_ARTIFACT} that has not expired, uploaded by
 * a run of this repository's {@link DEPLOY_BRANCH} after the record was kept
 * (any, with no record). The record's own run handed its list before it kept
 * the record, which holds the same pages, so only a deploy after it can have
 * submitted pages no record holds. The list of the run `exceptRun` names is
 * left out: the IndexNow job of a deploy re-run works that run's list out
 * again, and reads the lists of the other deploys.
 *
 * @returns the artifact, or undefined when there is none after the record
 */
export function pendingList(artifacts, record, exceptRun) {
	let newest;
	for (const artifact of artifacts) {
		const run = artifact.workflow_run;
		if (artifact.name !== HANDED_ARTIFACT || artifact.expired !== false || !run) continue;
		if (run.head_branch !== DEPLOY_BRANCH || run.head_repository_id !== run.repository_id) continue;
		if (exceptRun !== undefined && run.id === exceptRun) continue;
		if (record !== undefined && !createdAfter(artifact, record)) continue;
		if (newest === undefined || createdAfter(artifact, newest)) newest = artifact;
	}
	return newest;
}

/**
 * The deploy that went out after this run's, out of deployments of
 * {@link PAGES_ENVIRONMENT} as the GitHub GraphQL API gives them
 * (`databaseId`, `createdAt`, `commitOid`, `state`): the newest one created
 * after `deployedAt`, the moment this run's pages went out, whose state is not
 * one of {@link NOT_DEPLOYED}. One that failed never replaced this run's
 * pages; one still under way is about to, and counts, as does one created at
 * a moment that cannot be read. The order of the deploys decides which record
 * is the newest, not the order their IndexNow jobs end in, so the job keeps
 * its manifest only when there is none: a job re-run after a newer deploy
 * keeps nothing, and the newer deploy's own job keeps its record, whenever it
 * runs and whatever an older job kept before it. A deploy job re-run goes out
 * anew, at a moment of its own, and its job, which works its list out again
 * against the newest record, keeps its record by the same rule.
 *
 * @returns the deployment, or undefined when no deploy has gone out after this run's
 */
export function newerDeploy(deployedAt, deployments) {
	const after = Date.parse(deployedAt);
	let newest;
	for (const deployment of deployments) {
		if (Date.parse(deployment.createdAt) <= after || NOT_DEPLOYED.has(deployment.state)) continue;
		const later =
			newest === undefined ||
			deployment.createdAt > newest.createdAt ||
			(deployment.createdAt === newest.createdAt && deployment.databaseId > newest.databaseId);
		if (later) newest = deployment;
	}
	return newest;
}

/** The headers every request to the GitHub API carries. */
const apiHeaders = (token) => ({ accept: 'application/vnd.github+json', authorization: `Bearer ${token}`, 'x-github-api-version': '2022-11-28' });

/** One answer of the GitHub API read as JSON, or an error that says what it answered. */
async function fromApi(url, token, init = {}) {
	const response = await fetch(url, { ...init, headers: { ...apiHeaders(token), ...init.headers }, signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) });
	if (!response.ok) throw new Error(`the API answered ${response.status} to ${url}`);
	return response.json();
}

/**
 * Every artifact named `name` ({@link SUBMITTED_ARTIFACT} by default) of a
 * repository, read from the GitHub API a page at a time until it has listed as
 * many as it counts.
 */
export async function submittedArtifacts({ api, repository, token }, name = SUBMITTED_ARTIFACT) {
	const artifacts = [];
	for (let page = 1; page <= MAX_PAGES; page += 1) {
		const url = `${api}/repos/${repository}/actions/artifacts?name=${name}&per_page=${PER_PAGE}&page=${page}`;
		const listed = await fromApi(url, token);
		if (!Array.isArray(listed?.artifacts) || !Number.isInteger(listed.total_count)) {
			throw new Error(`the API answered ${url} with no list of artifacts`);
		}
		artifacts.push(...listed.artifacts);
		if (listed.artifacts.length < PER_PAGE || artifacts.length >= listed.total_count) return artifacts;
	}
	throw new Error(`the API lists more than ${MAX_PAGES * PER_PAGE} artifacts named ${name}`);
}

/** The deployments of an environment, newest first, a page after the cursor `after`. */
const DEPLOYMENTS_QUERY = `query ($owner: String!, $name: String!, $environment: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    deployments(environments: [$environment], first: ${DEPLOYMENTS_PER_PAGE}, after: $after, orderBy: { field: CREATED_AT, direction: DESC }) {
      pageInfo { hasNextPage endCursor }
      nodes { databaseId createdAt commitOid state }
    }
  }
}`;

/**
 * The deployments of {@link PAGES_ENVIRONMENT} created after `deployedAt`, as
 * {@link newerDeploy} reads them. They come from the GraphQL API, which lists
 * a repository's deployments newest first, where the REST API states no
 * order: the listing is read until it reaches one created at or before
 * `deployedAt`, which on a deploy that is still the newest is the first page.
 */
export async function deploymentsAfter({ graphql, repository, token }, deployedAt) {
	const [owner, name] = repository.split('/');
	const after = Date.parse(deployedAt);
	const newer = [];
	let cursor = null;
	for (let page = 1; page <= MAX_PAGES; page += 1) {
		const variables = { owner, name, environment: PAGES_ENVIRONMENT, after: cursor };
		const answer = await fromApi(graphql, token, {
			method: 'POST',
			headers: { 'content-type': 'application/json' },
			body: JSON.stringify({ query: DEPLOYMENTS_QUERY, variables }),
		});
		if (answer?.errors?.length) throw new Error(`the API answered ${answer.errors[0].message}`);
		const listed = answer?.data?.repository?.deployments;
		if (!Array.isArray(listed?.nodes) || typeof listed.pageInfo?.hasNextPage !== 'boolean') {
			throw new Error(`the API answered ${graphql} with no list of deployments`);
		}
		for (const deployment of listed.nodes) {
			if (Date.parse(deployment.createdAt) <= after) return newer;
			newer.push(deployment);
		}
		if (!listed.pageInfo.hasNextPage) return newer;
		cursor = listed.pageInfo.endCursor;
	}
	throw new Error(`the API lists more than ${MAX_PAGES * DEPLOYMENTS_PER_PAGE} deployments of ${PAGES_ENVIRONMENT} after ${deployedAt}`);
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
 * `last-submitted [--except-run <id>]`: name the run whose IndexNow job kept
 * the newest record, in the step output `run-id`, for the workflow to
 * download the record from, and the run of the newest list a deploy handed
 * IndexNow after it (see {@link pendingList}), in `pending-run-id`, leaving
 * out the list of run `<id>`, which the IndexNow job of a deploy re-run of
 * that run holds already. A record that cannot be listed is not a reason to
 * stop a deploy: with no `run-id` the build compares with nothing and the
 * full list goes out, as it always did, with a warning on the run; lists that
 * cannot be listed leave the record alone to compare with, with a warning
 * too.
 */
async function findLastSubmitted(args) {
	const { GITHUB_API_URL: api = 'https://api.github.com', GITHUB_REPOSITORY: repository, GITHUB_TOKEN: token, GITHUB_OUTPUT: output } = process.env;
	if (!repository || !token || !output) {
		throw new ManifestError('last-submitted reads the GitHub API from a workflow step: it needs GITHUB_REPOSITORY, GITHUB_TOKEN and GITHUB_OUTPUT.');
	}
	const except = option(args, '--except-run');
	if (except !== undefined && !/^[1-9]\d*$/.test(except)) {
		throw new ManifestError(`--except-run takes the id of a run, as $GITHUB_RUN_ID gives it, not ${JSON.stringify(except)}.`);
	}
	const exceptRun = except === undefined ? undefined : Number(except);
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
	} else {
		const run = record.workflow_run;
		console.log(`[indexnow] the pages were last submitted by run ${run.id}, of commit ${run.head_sha}, on ${record.created_at}.`);
		appendFileSync(output, `run-id=${run.id}\n`);
	}
	let lists;
	try {
		lists = await submittedArtifacts({ api, repository, token }, HANDED_ARTIFACT);
	} catch (error) {
		console.log(
			`::warning::[indexnow] the lists the deploys handed IndexNow could not be listed (${error.cause?.code ?? error.message}): ` +
				'a page a deploy since the record submitted and this one removed is not sent as removed, nor one such a deploy removed or changed and this one puts back.',
		);
		return;
	}
	if (exceptRun !== undefined) console.log(`[indexnow] the list run ${exceptRun} handed IndexNow is left out: it is the list this job works out again.`);
	const pending = pendingList(lists, record, exceptRun);
	if (pending === undefined) {
		console.log(`[indexnow] no deploy of ${DEPLOY_BRANCH} handed IndexNow a list after ${record === undefined ? 'its last' : 'that'} record.`);
		return;
	}
	console.log(`[indexnow] run ${pending.workflow_run.id} handed IndexNow a list on ${pending.created_at}, after that record: its pages, its removals and the pages it was to send are read too.`);
	appendFileSync(output, `pending-run-id=${pending.workflow_run.id}\n`);
}

/**
 * `keep-record --deployed-at <time>`: say, as `keep` in $GITHUB_OUTPUT,
 * whether the IndexNow job keeps the manifest it submitted. It does unless a
 * deploy has gone out after this run's, at `<time>` (the deploy job's
 * `deployed-at`), which happens when a failed job is re-run after a newer
 * deploy (see {@link newerDeploy}). A re-run of the deploy job writes that
 * moment anew, since its pages go out again: its job, having worked its list
 * out again against the newest record, keeps the manifest of the pages the
 * site then serves. Deployments that cannot be listed keep nothing either,
 * and neither does a run whose deploy job named no time, as one made before
 * the job wrote it: the next deploy then compares with the record before this
 * one and sends these pages again, and reads this run's handed list (on a
 * deploy re-run, the one its job worked out again) for the pages it removes
 * from them, where keeping a stale record could leave a removed page out for
 * good.
 */
async function keepRecord(args) {
	const {
		GITHUB_API_URL: api = 'https://api.github.com',
		GITHUB_GRAPHQL_URL: graphql = `${api}/graphql`,
		GITHUB_REPOSITORY: repository,
		GITHUB_TOKEN: token,
		GITHUB_OUTPUT: output,
	} = process.env;
	if (!repository || !token || !output) {
		throw new ManifestError('keep-record reads the GitHub API from a workflow step: it needs GITHUB_REPOSITORY, GITHUB_TOKEN and GITHUB_OUTPUT.');
	}
	const deployedAt = option(args, '--deployed-at') ?? '';
	if (deployedAt === '') {
		console.log(
			'::warning::[indexnow] the deploy job named no time its pages went out, as the deploy job of a run made before it wrote one names none: ' +
				'this manifest is not kept, and the next deploy sends these pages again, and the pages it removes from them.',
		);
		appendFileSync(output, 'keep=false\n');
		return;
	}
	if (!MOMENT.test(deployedAt) || Number.isNaN(Date.parse(deployedAt))) {
		throw new ManifestError(`--deployed-at takes the moment the pages went out, as 2026-11-10T08:00:00Z, not ${JSON.stringify(deployedAt)}.`);
	}
	let newer;
	try {
		newer = newerDeploy(deployedAt, await deploymentsAfter({ graphql, repository, token }, deployedAt));
	} catch (error) {
		console.log(
			`::warning::[indexnow] the deployments of the site could not be listed (${error.cause?.code ?? error.message}): ` +
				'this manifest is not kept, and the next deploy sends these pages again, and the pages it removes from them.',
		);
		appendFileSync(output, 'keep=false\n');
		return;
	}
	if (newer !== undefined) {
		console.log(
			`[indexnow] deployment ${newer.databaseId}, of commit ${newer.commitOid}, was made on ${newer.createdAt}, after this run's pages went out on ${deployedAt}: ` +
				"this manifest is not kept, and the next deploy compares with that deploy's record, or the one before it.",
		);
		appendFileSync(output, 'keep=false\n');
		return;
	}
	console.log(`[indexnow] no deploy has gone out since this run's on ${deployedAt}: this manifest is kept.`);
	appendFileSync(output, 'keep=true\n');
}

/**
 * The manifest a build published, rebuilt from the pages in `dist` and held
 * to the one the build wrote beside them.
 */
function publishedManifest(dist) {
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
	return current;
}

/**
 * The manifest at `file`, as `diff --current` compares it where there are no
 * pages to rebuild it from: the one a build handed the IndexNow job, which
 * the job submits and keeps. One that cannot be read stops the job, since it
 * is the record the job would keep.
 */
function handedManifest(file) {
	let text;
	try {
		text = readFileSync(file, 'utf8');
	} catch (error) {
		throw new ManifestError(`the manifest to compare, ${file}, cannot be read (${error.code ?? error.message}).`);
	}
	const manifest = parseManifest(text);
	if (manifest.reason) throw new ManifestError(`the manifest to compare, ${file}, cannot be compared: ${manifest.reason}.`);
	return { format: MANIFEST_FORMAT, pages: manifest.pages };
}

/** `diff ...`: compare the build, or the manifest it handed on, with the previous manifest and say what to submit. */
async function diff(args) {
	const given = option(args, '--current');
	if (given !== undefined && option(args, '--dist') !== undefined) {
		throw new ManifestError('give --dist or --current, not both: the pages of a build, or the manifest it handed on.');
	}
	const current = given === undefined ? publishedManifest(resolve(option(args, '--dist') ?? join(here, '..', 'dist'))) : handedManifest(given);
	const source = option(args, '--previous');
	if (!source) throw new ManifestError('say where the previous manifest is: --previous <file or URL>.');
	const previous = await loadPrevious(source);
	const pendingDir = option(args, '--pending');
	let pending;
	if (pendingDir !== undefined) {
		const handed = loadPending(pendingDir);
		if (handed.absent) {
			console.log(`[indexnow] no list a later deploy handed IndexNow at ${handed.from}: the record alone is compared with.`);
		} else if (handed.reason) {
			console.log(
				`::warning::[indexnow] the list a deploy handed IndexNow, at ${handed.from}, cannot be read (${handed.reason}): ` +
					'a page it named and this build no longer has is not sent as removed, nor one it removed, changed or was to send and this build has as the record has it.',
			);
		} else {
			pending = handed;
			console.log(`[indexnow] read the list a later deploy handed IndexNow, at ${handed.from} (${Object.keys(handed.pages).length} pages, ${handed.removed.length} removed, ${handed.urls.length} to send).`);
		}
	}
	const result = urlsToSubmit(current.pages, previous.pages, pending);
	const total = Object.keys(current.pages).length;
	if (result.full) {
		console.log(`[indexnow] no previous manifest to compare with from ${previous.from}: ${previous.reason}.`);
		console.log(`[indexnow] the full list goes out: ${result.urls.length} URLs, ${result.removed.length} of them removed.`);
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
		else if (command === 'last-submitted') await findLastSubmitted(args);
		else if (command === 'diff') await diff(args);
		else if (command === 'keep-record') await keepRecord(args);
		else throw new ManifestError(`unknown command ${JSON.stringify(command)}: use \`manifest\`, \`last-submitted\`, \`diff\` or \`keep-record\`.`);
	} catch (error) {
		if (!(error instanceof ManifestError)) throw error;
		console.error(`[indexnow] FAIL ${error.message}`);
		process.exit(1);
	}
}
