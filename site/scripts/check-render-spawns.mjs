// The processes the site's own source starts while it renders.
//
// A build renders about a thousand pages, so a process a page starts is a
// thousand processes, and a synchronous one stops the event loop for each:
// `build.concurrency` buys nothing while it runs. One `git log --follow` per
// page, called from the head of every page through a module under src/lib, was
// 86 % of the route phase in a CPU profile. In the docs workflow's blobless
// clone each one can wait on old blobs from the network as well. And the same
// pages took 12 minutes on one day and 45 on the next with every check of the
// job green: nothing fails on a build that is merely slow.
//
// So this reads everything a page can run (the modules and components under
// src/, the MDX pages, the config, and whatever they import from elsewhere in
// the site, found the way Vite finds them) and fails where one reaches for
// child_process or a package that wraps it, unless ONCE_PER_BUILD lists the file,
// with why it runs once per build, how many calls it holds and what it exports. A
// second call in a listed file has to say why too, an export the entry does not
// name fails because it would hand the process to every page, and an entry that
// covers nothing fails, so the list cannot go stale.
//
// It reads the text and does not parse it, so that it needs no install: a name
// built up at run time is not seen, a call under an alias is not counted, and a
// comment quoting the module's name is read as a use and has to be reworded.
// The packages that wrap child_process are a closed list, SPAWNER: a package not
// on it is not seen, and a new wrapper has to be added to it. A directory's
// package.json is not read, nor are the dependencies, whose one known call of
// this kind is Starlight's lastUpdated pass, once per build.
//
// Usage: node scripts/check-render-spawns.mjs [site-directory]
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, extname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import { reporter } from './shared/dist-pages.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const SITE = process.argv[2] ? resolve(process.argv[2]) : join(here, '..');

/** The files allowed to start a process, by path from the site's root. */
const ONCE_PER_BUILD = new Map([
	[
		'astro.config.mjs',
		{ calls: 1, exports: ['default'], why: 'reads the date of the last commit once, when the config loads' },
	],
	[
		'src/lib/page-dates.mjs',
		{
			calls: 1,
			exports: ['firstPublished'],
			why: 'reads the docs tree in one pass on the first page that asks; scripts/page-dates.test.mjs counts the processes',
		},
	],
]);

/** A file a page can run: code in any spelling, a component, a page with imports. */
const CODE = /\.(?:[cm]?[jt]sx?|astro|mdx)$/;

/**
 * The module that starts processes, or a package that wraps it, named in quotes.
 * The packages are a closed list: one that is not here is not seen.
 */
const SPAWNER =
	/['"`](?:node:)?(?:child_process|execa|cross-spawn|tinyexec|nano-spawn|zx|simple-git|shelljs|spawndamnit|gitlog|@actions\/exec)(?:\/[^'"`\n]*)?['"`]/;

/** A call of one of child_process's functions; `x.exec(` is a regular expression's. */
const CALL = /(?<![\w$])(?:execFileSync|execFile|execSync|spawnSync|spawn|fork)\s*\(|(?<![\w$.])exec\s*\(/g;

/** A path in quotes from the module or from the site's root, which is how a module names another. */
const RELATIVE = /['"`]((?:\.{1,2})?\/[^'"`\n]+)['"`]/g;

/** What Vite tries after a path that names no file, in its order, leaving out JSON, which runs nothing. */
const EXTENSIONS = ['.mjs', '.js', '.mts', '.ts', '.jsx', '.tsx'];

/** What Vite tries in place of a path that looks like TypeScript's output: x.js can be x.ts or x.tsx. */
const TS_SOURCES = { '.js': ['.ts', '.tsx'], '.mjs': ['.mts'], '.cjs': ['.cts'], '.jsx': ['.tsx'] };

/** A statement that gives something out, up to what says what: a list of names, or the rest of its line. */
const EXPORT = /(?<![\w$.])export(?![\w$])\s*(\{[^}]*\}|[^\n]*)|(?<![\w$.])module\s*\.\s*exports\b|(?<![\w$.])exports\s*\.\s*[\w$]+/g;

/** The start of an export that declares one name, or the module's default. */
const DECLARATION = /^(?:default\b|(?:async\s+)?function\s*\*?\s*([\w$]+)|class\s+([\w$]+))/;

/** Every file under `dir`, by absolute path. */
function* filesUnder(dir) {
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		const path = join(dir, entry.name);
		if (entry.isDirectory()) yield* filesUnder(path);
		else if (entry.isFile()) yield path;
	}
}

/** The file a specifier in `from` names, if it is one of the site's and code. */
function imported(from, specifier) {
	const path = specifier.split('?')[0];
	// Vite reads a path that starts at `/` from the project's root.
	const base = path.startsWith('/') ? join(SITE, path) : resolve(dirname(from), path);
	if (relative(SITE, base).startsWith('..')) return undefined;
	const written = extname(base);
	const candidates = [
		base,
		...(TS_SOURCES[written] ?? []).map((source) => base.slice(0, -written.length) + source),
		...EXTENSIONS.map((extension) => base + extension),
		...EXTENSIONS.map((extension) => join(base, `index${extension}`)),
	];
	return candidates.find((file) => CODE.test(file) && existsSync(file) && statSync(file).isFile());
}

/**
 * What a module gives out, one name per export: a function or a class by its
 * name, `default`, and what a list gives each name out as. Anything else, a
 * constant, a re-export of everything, is named as it is written and no entry
 * holds it: a statement can declare more names than a reading of its text finds.
 */
function exportsOf(text) {
	return [...text.matchAll(EXPORT)].flatMap(([statement, what]) => {
		if (what?.startsWith('{')) {
			return what
				.slice(1, -1)
				.split(',')
				.map((name) => name.trim().split(/\s+as\s+/).at(-1))
				.filter(Boolean);
		}
		const declared = what?.match(DECLARATION);
		if (declared) return [declared[1] ?? declared[2] ?? 'default'];
		return [(what ?? statement).replace(/\s*(?:=|from\b|;).*$/, '')];
	});
}

/** What a page can run: the source, the config, and what they import from outside the source. */
function renderPath() {
	const roots = [join(SITE, 'astro.config.mjs')].filter(existsSync);
	if (existsSync(join(SITE, 'src'))) roots.push(...[...filesUnder(join(SITE, 'src'))].filter((path) => CODE.test(path)));
	const seen = new Map();
	const pending = [...roots];
	while (pending.length > 0) {
		const path = pending.pop();
		if (seen.has(path)) continue;
		const text = readFileSync(path, 'utf8');
		seen.set(path, text);
		for (const [, specifier] of text.matchAll(RELATIVE)) {
			const next = imported(path, specifier);
			if (next) pending.push(next);
		}
	}
	return seen;
}

/** A path from the site's root, written the one way ONCE_PER_BUILD writes it. */
const fromSite = (path) => relative(SITE, path).split(sep).join('/');

const { report, failures } = reporter();

const files = renderPath();
const spawning = [...files].filter(([, text]) => SPAWNER.test(text));
console.log(`read ${files.size} files a page can run; ${spawning.length} reach for a process`);

report(
	spawning.map(([path]) => fromSite(path)).filter((path) => !ONCE_PER_BUILD.has(path)),
	'file(s) that start a process where a page renders, which is once per page unless it is shown otherwise and listed in ONCE_PER_BUILD',
	'every file that starts a process is listed as once per build',
);

report(
	spawning.flatMap(([path, text]) => {
		const listed = ONCE_PER_BUILD.get(fromSite(path));
		const calls = text.match(CALL)?.length ?? 0;
		return listed && calls !== listed.calls
			? [`${fromSite(path)}: ${calls} call(s) where the list says ${listed.calls}, because it ${listed.why}`]
			: [];
	}),
	'listed file(s) whose calls are not the ones the list explains',
	'every listed file holds the calls its reason covers',
);

report(
	spawning.flatMap(([path, text]) => {
		const listed = ONCE_PER_BUILD.get(fromSite(path));
		if (!listed) return [];
		const given = exportsOf(text);
		return [
			...given
				.filter((name) => !listed.exports.includes(name))
				.map((name) => `${fromSite(path)}: exports ${name}, which the list does not name`),
			...listed.exports
				.filter((name) => !given.includes(name))
				.map((name) => `${fromSite(path)}: the list names ${name}, which it does not export`),
		];
	}),
	'listed file(s) that give out something other than what the list says a page may call, which hands the process to every page that imports it',
	'every listed file exports what the list names and nothing else',
);

const spawningPaths = new Set(spawning.map(([path]) => fromSite(path)));
report(
	[...ONCE_PER_BUILD.keys()].filter((path) => !spawningPaths.has(path)),
	'entries of ONCE_PER_BUILD that cover nothing',
	'every entry of the list covers a file that starts a process',
);

console.log(`\n${failures()} failing check(s).`);
process.exit(failures() ? 1 : 0);
