// The staging step: a site build becomes the asset directory of the Worker.
//
// The build is what GitHub Pages serves (docs.yml's artifact, or a local
// site/dist), with its files at the root and served under the base path. The
// Worker serves the asset directory from the root of phonometry.dev, so the
// build goes under `<out>/<prefix>/`, beside the three files Static Assets
// reads and never serves: `_headers`, `_redirects` and `.assetsignore`. Every
// check below runs before anything is written, and a problem stops the
// deploy: the limits of the Free plan, a file of the build that would
// shadow a generated one, the pages without a Markdown copy against the
// exclusions the headers and the zone rule are written from, the retired
// addresses against the pages they lead to, and the clip hosts against the
// Content-Security-Policy of every page.
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

import { mediaOrigins } from '../../src/data/site.mjs';
import { headersFile, parseHeaders, HEADER_LINE_LIMIT, HEADER_RULE_LIMIT } from './headers.mjs';
import { redirectProblems, redirectsFile } from './redirects.mjs';
import { isExcluded } from './twins.mjs';

/** Workers Free: files per Worker version, and bytes per file. */
export const MAX_FILES = 20000;
export const MAX_FILE_BYTES = 25 * 1024 * 1024;

/**
 * Files of the build also served at the root of the host when the build sits
 * under a base path: crawlers read robots.txt only at the root, and agents
 * look for llms.txt there first. Both name absolute URLs, so a copy is right.
 */
export const ROOT_COPIES = Object.freeze(['robots.txt', 'llms.txt']);

/** The files Static Assets reads beside the assets and never serves. */
const CONTROL_FILES = new Set(['_headers', '_redirects', '.assetsignore']);

/**
 * Every file under a directory.
 *
 * @param {string} root The directory.
 * @returns {{path: string, size: number}[]} Paths relative to it with `/`, sorted.
 */
export function listTree(root) {
	const files = [];
	(function walk(dir) {
		for (const entry of readdirSync(dir, { withFileTypes: true })) {
			const full = join(dir, entry.name);
			if (entry.isDirectory()) walk(full);
			else files.push({ path: relative(root, full).split(sep).join('/'), size: statSync(full).size });
		}
	})(root);
	return files.sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
}

/**
 * The limits of the plan and the files the build must not carry.
 *
 * @param {{path: string, size: number}[]} files The build's files.
 * @returns {string[]} One line per problem.
 */
export function treeProblems(files) {
	const problems = [];
	if (files.length > MAX_FILES) problems.push(`${files.length} files, over the ${MAX_FILES} a Workers Free version takes`);
	for (const { path, size } of files) {
		if (size > MAX_FILE_BYTES) problems.push(`${path}: ${size} bytes, over the ${MAX_FILE_BYTES} a static asset takes`);
		if (CONTROL_FILES.has(path.split('/').at(-1))) problems.push(`${path}: the build carries its own, which the generated one would replace`);
	}
	return problems;
}

/** The slash page a build file serves, or null. */
const pageOf = (path, prefix) => {
	if (path === 'index.html') return `${prefix}/`;
	return path.endsWith('/index.html') ? `${prefix}/${path.slice(0, -'index.html'.length)}` : null;
};

/**
 * The slash pages the build serves: every index.html, the retired addresses
 * aside (their stubs are never served, `_redirects` answers first).
 *
 * @param {{path: string}[]} files The build's files.
 * @param {string} prefix The base path.
 * @param {{from: string}[]} pairs The retired addresses.
 * @returns {string[]} The pages, sorted.
 */
export function servedPages(files, prefix, pairs) {
	const retired = new Set(pairs.map(({ from }) => from));
	return files
		.map(({ path }) => pageOf(path, prefix))
		.filter((page) => page !== null && !retired.has(page))
		.sort();
}

/**
 * The served slash pages without a Markdown copy beside them.
 *
 * @param {{path: string}[]} files The build's files.
 * @param {string} prefix The base path.
 * @param {{from: string}[]} pairs The retired addresses.
 * @returns {string[]} The pages, sorted.
 */
export function noTwinPages(files, prefix, pairs) {
	const have = new Set(files.map(({ path }) => `${prefix}/${path}`));
	return servedPages(files, prefix, pairs).filter((page) => !have.has(`${page}index.md`));
}

/**
 * Whether the exclusions describe exactly the pages without a copy.
 *
 * @param {string[]} noTwin From noTwinPages.
 * @param {string[]} pages From servedPages.
 * @param {{pages: string[], subtrees: string[]}} exclusions lib/twins.mjs.
 * @returns {string[]} One line per disagreement.
 */
export function exclusionProblems(noTwin, pages, exclusions) {
	const problems = [];
	const without = new Set(noTwin);
	for (const page of noTwin) {
		if (!isExcluded(page, exclusions)) problems.push(`${page} has no Markdown copy and is not excluded (lib/twins.mjs)`);
	}
	for (const root of exclusions.subtrees) {
		const under = pages.filter((page) => page.startsWith(root));
		if (under.length === 0) problems.push(`no page under ${root}, which is excluded`);
		for (const page of under) if (!without.has(page)) problems.push(`${page} has a Markdown copy but is excluded (lib/twins.mjs)`);
	}
	for (const page of exclusions.pages) {
		if (!without.has(page)) problems.push(`${page} has a Markdown copy, or no page, but is excluded (lib/twins.mjs)`);
	}
	return problems;
}

/**
 * The origin the build names as canonical on its home page.
 *
 * @param {string} root The build.
 * @param {string} prefix The base path.
 * @returns {string} `https://host`.
 */
export function buildOrigin(root, prefix) {
	const html = readFileSync(join(root, 'index.html'), 'utf8');
	const href = /<link rel="canonical" href="([^"]+)"/.exec(html)?.[1];
	if (!href) throw new Error('the home page names no canonical URL');
	const url = new URL(href);
	if (url.pathname !== `${prefix}/`) throw new Error(`the home page canonical ${href} is not under ${prefix}/`);
	return url.origin;
}

/**
 * The pages whose own Content-Security-Policy would block a clip host.
 *
 * Every page carries a meta policy, and a browser enforces it beside the
 * header, holding the address a clip is redirected to to both. A build made
 * before a clip host was added to `mediaOrigins` would play no clip on the
 * preview, so it is refused here. Pages with no meta policy (the stubs of
 * retired addresses) load no media and are skipped; the home must have one.
 *
 * @param {string} root The build.
 * @param {{path: string}[]} files The build's files.
 * @param {readonly string[]} origins The clip hosts (mediaOrigins).
 * @returns {string[]} One line per page that blocks one, at most ten and a count.
 */
export function mediaPolicyProblems(root, files, origins) {
	const blocked = [];
	let homeHasPolicy = false;
	for (const { path } of files) {
		if (!path.endsWith('.html')) continue;
		const html = readFileSync(join(root, path), 'utf8');
		const content = /<meta http-equiv="Content-Security-Policy" content="([^"]*)"/i.exec(html)?.[1];
		if (content === undefined) continue;
		if (path === 'index.html') homeHasPolicy = true;
		const directives = new Map(
			content
				.split(';')
				.map((part) => part.trim().split(/\s+/))
				.filter(([name]) => name)
				.map(([name, ...sources]) => [name.toLowerCase(), sources]),
		);
		const sources = directives.get('media-src') ?? directives.get('default-src') ?? [];
		const missing = origins.filter((origin) => !sources.includes(origin));
		if (missing.length > 0) blocked.push(`${path}: media-src does not allow ${missing.join(' ')}`);
	}
	const problems = blocked.slice(0, 10);
	if (blocked.length > 10) problems.push(`and ${blocked.length - 10} more pages whose media-src blocks a clip host`);
	if (!homeHasPolicy) problems.push('the home page carries no Content-Security-Policy meta tag');
	return problems;
}

/**
 * Checks a build and, unless checkOnly, writes the asset directory.
 *
 * @param {object} options
 * @param {string} options.from The build.
 * @param {string} options.out The asset directory to create; it must not exist.
 * @param {string} options.prefix The base path the build was made for.
 * @param {string} options.origin The origin the build was made for (its site URL).
 * @param {{from: string, to: string}[]} options.pairs The retired addresses (redirectPairs()).
 * @param {{pages: string[], subtrees: string[]}} options.exclusions Pages without a copy.
 * @param {boolean} options.indexable Whether the noindex goes.
 * @param {boolean} [options.checkOnly] Check, and write nothing.
 * @returns {{problems: string[], files: number, redirects: number, headerRules: number}} What was found.
 */
export function stage({ from, out, prefix, origin, pairs, exclusions, indexable, checkOnly = false }) {
	if (!checkOnly && existsSync(out)) throw new Error(`${out} already exists; staging writes a fresh directory`);
	const files = listTree(from);
	const problems = treeProblems(files);
	let built = null;
	try {
		built = buildOrigin(from, prefix);
	} catch (error) {
		problems.push(error.message);
	}
	if (built !== null && built !== origin) problems.push(`the build was built for ${built}, not ${origin}`);
	problems.push(...exclusionProblems(noTwinPages(files, prefix, pairs), servedPages(files, prefix, pairs), exclusions));
	problems.push(...mediaPolicyProblems(from, files, mediaOrigins));
	const have = new Set(files.map(({ path }) => `${prefix}/${path}`));
	problems.push(...redirectProblems(pairs, { exists: (to) => have.has(to.endsWith('/') ? `${to}index.html` : to) }));
	const headers = headersFile({ prefix, origin, exclusions, indexable });
	const rules = parseHeaders(headers).length;
	if (rules > HEADER_RULE_LIMIT) problems.push(`_headers has ${rules} rules, over the ${HEADER_RULE_LIMIT}`);
	for (const line of headers.split('\n')) {
		if (line.length > HEADER_LINE_LIMIT) problems.push(`_headers line over ${HEADER_LINE_LIMIT} characters: ${line.slice(0, 40)}`);
	}
	const rootCopies = prefix === '' ? [] : ['404.html', ...ROOT_COPIES].filter((name) => have.has(`${prefix}/${name}`));
	const extra = rootCopies.length;
	if (files.length + extra > MAX_FILES) problems.push(`${files.length + extra} files once staged, over the ${MAX_FILES}`);
	const report = { problems, files: files.length + extra, redirects: pairs.length, headerRules: rules };
	if (checkOnly || problems.length > 0) return report;

	const site = join(out, ...prefix.split('/').filter(Boolean));
	mkdirSync(site, { recursive: true });
	cpSync(from, site, { recursive: true });
	// Outside the base path the nearest 404.html is the root's, so the site's
	// own page answers there too (not_found_handling: "404-page"); robots.txt
	// and llms.txt answer at the root as well.
	for (const name of rootCopies) cpSync(join(from, name), join(out, name));
	writeFileSync(join(out, '_headers'), headers);
	writeFileSync(join(out, '_redirects'), redirectsFile(pairs));
	writeFileSync(join(out, '.assetsignore'), '.*\n');
	return report;
}
