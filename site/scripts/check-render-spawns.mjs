// The processes the site's own source starts while it renders.
//
// A build renders about a thousand pages, so a process a page starts is a
// thousand processes, and a synchronous one stops the event loop for each:
// `build.concurrency` buys nothing while it runs. One `git log --follow` per
// page, called from the head of every page through a module under src/lib, was
// 86 % of the route phase in a CPU profile. In the docs workflow's blobless
// clone each one can wait on old blobs from the network as well, and the same
// pages took 12 minutes on one day and 45 on the next with every check of the
// job green: nothing fails on a build that is merely slow.
//
// So this reads everything a page can run (the modules and components under
// src/, the MDX pages, the config, and whatever they import from elsewhere in
// the site) and fails where one reaches for child_process or a package that
// wraps it, unless ONCE_PER_BUILD lists the file, with why it runs once per
// build and how many calls it holds. A second call in a listed file has to say
// why too, and an entry that covers nothing fails, so the list cannot go stale.
//
// It reads the text and does not parse it, so that it needs no install: a name
// built up at run time is not seen, a call under an alias is not counted, and a
// comment quoting the module's name is read as a use and has to be reworded.
// It does not read the dependencies, whose one known call of this kind is
// Starlight's lastUpdated pass, once per build.
//
// Usage: node scripts/check-render-spawns.mjs [site-directory]
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import { reporter } from './shared/dist-pages.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const SITE = process.argv[2] ? resolve(process.argv[2]) : join(here, '..');

/** The files allowed to start a process, by path from the site's root. */
const ONCE_PER_BUILD = new Map([
	[
		'astro.config.mjs',
		{ calls: 1, why: 'reads the date of the last commit once, when the config loads' },
	],
	[
		'src/lib/page-dates.mjs',
		{
			calls: 1,
			why: 'reads the docs tree in one pass on the first page that asks; scripts/page-dates.test.mjs counts the processes',
		},
	],
]);

/** A file a page can run: code in any spelling, a component, a page with imports. */
const CODE = /\.(?:[cm]?[jt]sx?|astro|mdx)$/;

/** The module that starts processes, or a package that wraps it, named in quotes. */
const SPAWNER = /['"`](?:node:)?(?:child_process|execa|cross-spawn|tinyexec|nano-spawn|zx)(?:\/[^'"`\n]*)?['"`]/;

/** A call of one of child_process's functions; `x.exec(` is a regular expression's. */
const CALL = /(?<![\w$])(?:execFileSync|execFile|execSync|spawnSync|spawn|fork)\s*\(|(?<![\w$.])exec\s*\(/g;

/** A relative path in quotes, which is how a module names another. */
const RELATIVE = /['"`](\.{1,2}\/[^'"`\n]+)['"`]/g;

/** Every file under `dir`, by absolute path. */
function* filesUnder(dir) {
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		const path = join(dir, entry.name);
		if (entry.isDirectory()) yield* filesUnder(path);
		else if (entry.isFile()) yield path;
	}
}

/** The file a relative specifier in `from` names, if it is one of the site's and code. */
function imported(from, specifier) {
	const base = resolve(dirname(from), specifier.split('?')[0]);
	if (relative(SITE, base).startsWith('..')) return undefined;
	for (const suffix of ['', '.mjs', '.js', '.ts']) {
		const path = base + suffix;
		if (CODE.test(path) && existsSync(path) && statSync(path).isFile()) return path;
	}
	return undefined;
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

const spawningPaths = new Set(spawning.map(([path]) => fromSite(path)));
report(
	[...ONCE_PER_BUILD.keys()].filter((path) => !spawningPaths.has(path)),
	'entries of ONCE_PER_BUILD that cover nothing',
	'every entry of the list covers a file that starts a process',
);

console.log(`\n${failures()} failing check(s).`);
process.exit(failures() ? 1 : 0);
