// Finds a site link written with the base path the site no longer has, or
// with the host it was published on before (docs/contributing F76).
//
// The site is served at the root of phonometry.dev, and every page links the
// others root-relative: `[levels](/signals/levels/)`. Until the move it was
// served under /phonometry on docs.jmrp.io, and 12 000 links wrote that base
// by hand. A link that still writes it, in a page, a data file, a component or
// a library module, points at an address that only answers through a
// redirect, and one written with the old host leaves the site for it. The
// links validator of the build catches a leftover in Markdown; this catches
// every other shape too (a quoted href, a `src=`, a component string), and
// the old host, which the validator takes for an outside link. It reads
// every text file of the site's source, `src/` and astro.config.mjs, so a
// route, a utility or a stylesheet cannot write one either.
//
// Usage: node scripts/base-path.mjs   (exit 1 on a finding)
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

/** The site folder, from which every path below is written. */
export const SITE = fileURLToPath(new URL('..', import.meta.url));

/**
 * What the check reads, from the site folder: every file a site link can be
 * written in, the pages, the data, the components, the routes, the utilities
 * and the styles under `src/`, and the build's own configuration.
 */
export const SCANNED = Object.freeze(['src', 'astro.config.mjs']);

/**
 * The repository files outside the site that name it, from the site folder:
 * the README and its PyPI copy, the security policy, the package metadata,
 * the Zenodo record, the paper, the two hand-written pages of the GitHub
 * edition and the issue and discussion templates. They link the site by its
 * full address, so only the old host is looked for in them: `/phonometry`
 * is no site link outside the site (`pip install phonometry`, a repository
 * path), and a path of the site never starts there.
 */
export const OUTSIDE = Object.freeze([
	'../README.md',
	'../README_PYPI.md',
	'../SECURITY.md',
	'../pyproject.toml',
	'../.zenodo.json',
	'../paper/paper.md',
	'../docs/README.md',
	'../docs/reference/api/index.md',
	'../.github/ISSUE_TEMPLATE',
	'../.github/DISCUSSION_TEMPLATE',
]);

/** The files read: every text file a page, a data file or code can live in. */
const TEXT = /\.(?:md|mdx|astro|ts|mjs|js|json|css|ya?ml|txt|html)$/;

/**
 * The old base path written as the start of a path: after a delimiter (a
 * bracket, a quote, a space, a backtick or the line's start), never inside
 * another path (`src/phonometry`, `github.com/jmrplens/phonometry`) or a
 * longer name (`/phonometry-assets`), and followed by a path, a quote, a
 * closing bracket, a fragment, a query, a space or the end.
 */
export const BASE_LINK = /(?<![\w.\-/])\/phonometry(?=[/'"`)\s#?]|$)/;

/** The host and base the site was published under before. */
export const OLD_HOST = /docs\.jmrp\.io\/phonometry/;

/**
 * The lines that may write them, each with its reason. A line listed here
 * that no longer exists fails the check, so the list cannot outlive what it
 * excuses, unless it is `optional`: a value the file holds only while a
 * switch it names is made, which the check lets through when it is there and
 * does not ask for when it is not.
 */
export const ALLOWED = Object.freeze([
	Object.freeze({
		file: 'src/data/site-targets.json',
		line: '{ "siteUrl": "https://docs.jmrp.io", "basePath": "/phonometry" }',
		why: 'the legacy origin: the redirect list for the old host is written from it (scripts/cloudflare-redirects.mjs --legacy)',
	}),
	Object.freeze({
		file: 'src/data/site-targets.json',
		line: '"clipBase": "https://docs.jmrp.io/phonometry/media/"',
		optional: true,
		why: 'the clip host to fall back on while media.phonometry.dev does not hold every clip: switching to it is this value and mediaOrigins, and nothing else, and the old host answers its clips with 206 under that path',
	}),
]);

/**
 * The findings in one file's text.
 *
 * @param {string} text The file.
 * @param {string} file Its path from the site folder.
 * @param {readonly {file: string, line: string, optional?: boolean}[]} [allowed]
 * @returns {{file: string, line: number, text: string}[]} One per line that writes either.
 */
export function basePathFindings(text, file, allowed = ALLOWED) {
	const excused = new Set(allowed.filter((entry) => entry.file === file).map((entry) => entry.line));
	const findings = [];
	text.split('\n').forEach((line, index) => {
		if (!BASE_LINK.test(line) && !OLD_HOST.test(line)) return;
		if (excused.has(line.trim())) return;
		findings.push({ file, line: index + 1, text: line.trim() });
	});
	return findings;
}

/**
 * Every text file the check reads, as a path from the site folder.
 *
 * @param {string} [site]
 * @returns {string[]}
 * @throws {Error} When a path of `SCANNED` is not there: a check that read
 *   nothing of it would pass.
 */
export function scannedFiles(site = SITE) {
	const files = [];
	const add = (path) => files.push(relative(site, path).split('\\').join('/'));
	const walk = (dir) => {
		for (const entry of readdirSync(dir, { withFileTypes: true })) {
			const path = join(dir, entry.name);
			if (entry.isDirectory()) walk(path);
			else if (TEXT.test(entry.name)) add(path);
		}
	};
	for (const scanned of SCANNED) {
		const path = join(site, scanned);
		if (!existsSync(path)) throw new Error(`scripts/base-path.mjs reads ${scanned}, which ${site} does not have: moved or renamed?`);
		if (statSync(path).isDirectory()) walk(path);
		else add(path);
	}
	return files.sort();
}

/**
 * What the check reports for a tree: every finding, and every allowance that
 * excuses nothing and is not `optional`.
 *
 * @param {string} [site]
 * @param {readonly {file: string, line: string, optional?: boolean}[]} [allowed]
 * @returns {{files: number, findings: {file: string, line: number, text: string}[], stale: string[]}}
 */
export function basePathReport(site = SITE, allowed = ALLOWED) {
	const files = scannedFiles(site);
	const findings = [];
	const used = new Set();
	for (const file of files) {
		const text = readFileSync(join(site, file), 'utf8');
		findings.push(...basePathFindings(text, file, allowed));
		for (const entry of allowed) {
			if (entry.file === file && text.split('\n').some((line) => line.trim() === entry.line)) used.add(entry);
		}
	}
	const stale = allowed.filter((entry) => !entry.optional && !used.has(entry)).map((entry) => `${entry.file}: ${entry.line}`);
	return { files: files.length, findings, stale };
}

/**
 * The lines of the repository files outside the site that write the old host.
 *
 * @param {string} [site]
 * @param {readonly string[]} [outside]
 * @returns {{files: number, findings: {file: string, line: number, text: string}[]}} Paths from the repository root.
 * @throws {Error} When a path of `outside` is not there.
 */
export function outsideReport(site = SITE, outside = OUTSIDE) {
	const root = join(site, '..');
	const files = [];
	const walk = (dir) => {
		for (const entry of readdirSync(dir, { withFileTypes: true })) {
			const path = join(dir, entry.name);
			if (entry.isDirectory()) walk(path);
			else if (TEXT.test(entry.name) || entry.name.endsWith('.toml')) files.push(path);
		}
	};
	for (const name of outside) {
		const path = join(site, name);
		if (!existsSync(path)) throw new Error(`scripts/base-path.mjs reads ${name}, which is not there: moved or renamed?`);
		if (statSync(path).isDirectory()) walk(path);
		else files.push(path);
	}
	const findings = [];
	for (const path of files.sort()) {
		const file = relative(root, path).split('\\').join('/');
		readFileSync(path, 'utf8').split('\n').forEach((line, index) => {
			if (OLD_HOST.test(line)) findings.push({ file, line: index + 1, text: line.trim() });
		});
	}
	return { files: files.length, findings };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	const { files, findings, stale } = basePathReport();
	const outside = outsideReport();
	for (const { file, line, text } of findings) {
		console.log(`::error file=site/${file},line=${line}::a site link with the old base path or host (docs/contributing F76): ${text}`);
	}
	for (const { file, line, text } of outside.findings) {
		console.log(`::error file=${file},line=${line}::a link to the old host of the site (docs/contributing F76): ${text}`);
	}
	for (const entry of stale) console.log(`::error::an allowance of scripts/base-path.mjs excuses no line any more: ${entry}`);
	console.log(`${files} files read (${SCANNED.join(', ')}): ${findings.length} finding(s), ${stale.length} stale allowance(s)`);
	console.log(`${outside.files} files read outside the site: ${outside.findings.length} finding(s)`);
	process.exit(findings.length + outside.findings.length + stale.length === 0 && files > 0 && outside.files > 0 ? 0 : 1);
}
