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
// record before it and sends those pages along with its own. A record is kept
// only while the one its build compared with is still the newest: a failed
// job re-run after a newer deploy kept its record would otherwise put back a
// manifest older than that deploy, and a page the newer deploy added and the
// next one removes would be in neither manifest the next build compares, so
// its removal would never be sent.
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
//   node scripts/indexnow-diff.mjs last-submitted
//     asks the GitHub API (GITHUB_API_URL, GITHUB_REPOSITORY, GITHUB_TOKEN)
//     for the newest record an IndexNow job kept, and writes the id of its run
//     as `run-id` and its own id as `artifact-id` to $GITHUB_OUTPUT, for the
//     workflow to download it from; writes nothing when there is none
//   node scripts/indexnow-diff.mjs diff [--dist <dir>] --previous <file or URL> [--out <dir>] [--record <id>]
//     checks the published manifest against the pages, compares it with the
//     previous one (a record, or a URL such as the live site's manifest, to
//     compare a local build with), prints the changed, new and removed URLs,
//     and writes into <dir> the URLs to submit (urls.json: {"urls": [...]},
//     the lists behind it and the id of the newest record, given by
//     `--record`) and the manifest they were worked out from, which the
//     IndexNow job keeps once it has submitted them
//   node scripts/indexnow-diff.mjs keep-record --urls <urls.json>
//     asks the GitHub API whether a record newer than the one urls.json
//     names has been kept since the build compared with it, and writes
//     `keep=true` to $GITHUB_OUTPUT when none has, `keep=false` when one has
//     or when the records cannot be listed
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
 * The record kept since the build compared with `compared` (the id of the
 * newest record then, or null when there was none): the newest record now,
 * when it is another one. The IndexNow job keeps its manifest only when there
 * is none, so a job re-run after a newer deploy kept its record leaves that
 * record the newest; that deploy's pages, and whatever it added, stay in the
 * record the next build compares with.
 *
 * @returns the newer artifact, or undefined when the build compared with the
 *   newest record, or there is none
 */
export function newerRecord(compared, artifacts) {
	const newest = lastSubmitted(artifacts);
	return newest !== undefined && newest.id !== compared ? newest : undefined;
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
	appendFileSync(output, `run-id=${run.id}\nartifact-id=${record.id}\n`);
}

/**
 * `keep-record --urls <urls.json>`: say, as `keep` in $GITHUB_OUTPUT, whether
 * the IndexNow job keeps the manifest it submitted. It does unless a record
 * newer than the one its build compared with has been kept meanwhile, which
 * happens when a failed job is re-run after a newer deploy submitted its
 * pages. A record that cannot be listed keeps nothing either: the next deploy
 * then compares with the record before this one and sends these pages again,
 * where keeping a stale record could leave a removed page out for good.
 */
async function keepRecord(args) {
	const { GITHUB_API_URL: api = 'https://api.github.com', GITHUB_REPOSITORY: repository, GITHUB_TOKEN: token, GITHUB_OUTPUT: output } = process.env;
	if (!repository || !token || !output) {
		throw new ManifestError('keep-record reads the GitHub API from a workflow step: it needs GITHUB_REPOSITORY, GITHUB_TOKEN and GITHUB_OUTPUT.');
	}
	const urls = option(args, '--urls');
	if (!urls || !existsSync(urls)) throw new ManifestError(`say where the list the build handed over is: --urls <${URLS_NAME}>, not ${urls}.`);
	const listed = JSON.parse(readFileSync(urls, 'utf8'));
	if (!Object.hasOwn(listed, 'record') || !(listed.record === null || Number.isSafeInteger(listed.record))) {
		console.log(
			`::warning::[indexnow] ${urls} does not name the record its build compared with, as one written by another version of this script does not: ` +
				'this manifest is not kept, and the next deploy sends these pages again.',
		);
		appendFileSync(output, 'keep=false\n');
		return;
	}
	let artifacts;
	try {
		artifacts = await submittedArtifacts({ api, repository, token });
	} catch (error) {
		console.log(
			`::warning::[indexnow] the records of the pages IndexNow was sent could not be listed (${error.cause?.code ?? error.message}): ` +
				'this manifest is not kept, and the next deploy sends these pages again.',
		);
		appendFileSync(output, 'keep=false\n');
		return;
	}
	const newer = newerRecord(listed.record, artifacts);
	if (newer !== undefined) {
		const run = newer.workflow_run;
		console.log(
			`[indexnow] run ${run.id}, of commit ${run.head_sha}, kept a newer record on ${newer.created_at} than the one this build compared with ` +
				`(${listed.record ?? 'none'}): this manifest is not kept, and the next deploy compares with that one.`,
		);
		appendFileSync(output, 'keep=false\n');
		return;
	}
	console.log(`[indexnow] no newer record than the one this build compared with (${listed.record ?? 'none'}): this manifest is kept.`);
	appendFileSync(output, 'keep=true\n');
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
	const given = option(args, '--record') ?? '';
	if (!/^\d*$/.test(given)) throw new ManifestError(`--record takes the id of an artifact, not ${JSON.stringify(given)}.`);
	const record = given === '' ? null : Number(given);
	const out = option(args, '--out');
	if (out) {
		mkdirSync(out, { recursive: true });
		const reason = result.full ? previous.reason : null;
		writeFileSync(
			join(out, URLS_NAME),
			`${JSON.stringify({ previous: previous.from, record, reason, full: result.full, changed: result.changed, new: result.added, removed: result.removed, urls: result.urls }, null, 1)}\n`,
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
		else if (command === 'keep-record') await keepRecord(args);
		else throw new ManifestError(`unknown command ${JSON.stringify(command)}: use \`manifest\`, \`last-submitted\`, \`diff\` or \`keep-record\`.`);
	} catch (error) {
		if (!(error instanceof ManifestError)) throw error;
		console.error(`[indexnow] FAIL ${error.message}`);
		process.exit(1);
	}
}
