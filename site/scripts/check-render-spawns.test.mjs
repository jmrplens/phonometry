// The failures check-render-spawns.mjs exists to report, on sites small enough
// to read.
//
// The real source only ever hands the check files that pass, so a check that
// stopped seeing an import, a spelling of one or a file type would stay green
// there for good. Each test here writes a site of a few files into a directory
// of its own, runs the check on it the way CI does, and reads the exit status
// and the lines it printed.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-render-spawns.mjs');

/** A path as a regular expression matches it literally. */
const literal = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** A module that reaches for child_process and calls it once, the way the listed ones do. */
const ONE_CALL = `import { execFileSync } from 'node:child_process';\nexecFileSync('git', ['log']);\n`;

/** The files the list names, each as it should be. */
const LISTED = {
	'astro.config.mjs': `${ONE_CALL}export default {};\n`,
	'src/lib/page-dates.mjs': `${ONE_CALL}export function firstPublished() {}\n`,
	'src/lib/content-dates.mjs': `import { spawn } from 'node:child_process';\nspawn('git', ['log']);\nexport function loadContentDates() {}\n`,
};

/**
 * Write `files`, paths under the site mapped to their text, into a site of its
 * own, run the check on it, and say how it ended.
 */
function check(t, files) {
	const site = mkdtempSync(join(tmpdir(), 'check-render-spawns-'));
	t.after(() => rmSync(site, { recursive: true, force: true }));
	for (const [path, text] of Object.entries(files)) {
		mkdirSync(dirname(join(site, path)), { recursive: true });
		writeFileSync(join(site, path), text);
	}
	const ran = spawnSync(process.execPath, [CHECK, site], { encoding: 'utf8' });
	return { status: ran.status, out: ran.stdout, err: ran.stderr };
}

test('a site where only the listed files start a process passes', (t) => {
	const ran = check(t, {
		...LISTED,
		'src/components/Head.astro': `---\nimport { firstPublished } from '../lib/page-dates.mjs';\n---\n<head></head>\n`,
		'src/lib/quiet.mjs': `export const quiet = /a/.exec('a');\n`,
	});
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /read 5 files a page can run; 3 reach for a process/);
	assert.match(ran.out, /\n0 failing check\(s\)\./);
	assert.equal(ran.err, '');
});

const SPELLINGS = {
	'a static import': `import { execFileSync } from 'node:child_process';\nexecFileSync('git');\n`,
	'the bare module name': `import { spawnSync } from "child_process";\nspawnSync('git');\n`,
	'a default import': `import cp from 'node:child_process';\ncp.execSync('git');\n`,
	'an import across lines': `import {\n\texecSync,\n} from\n\t'node:child_process';\nexecSync('git');\n`,
	'a dynamic import': "const cp = await import(\n\t'node:child_process',\n);\ncp.fork('x');\n",
	'a require': `const cp = require('child_process');\ncp.spawn('git');\n`,
	'the process object': `const cp = process.getBuiltinModule('node:child_process');\ncp.spawn('git');\n`,
	'a path into a package that wraps it': `import spawn from 'cross-spawn/index.js';\nspawn('git');\n`,
	...Object.fromEntries(
		[
			'@actions/exec',
			'cross-spawn',
			'execa',
			'gitlog',
			'nano-spawn',
			'shelljs',
			'simple-git',
			'spawndamnit',
			'tinyexec',
			'zx',
		].map((name) => [`the package ${name}`, `import run from '${name}';\nawait run('git');\n`]),
	),
};

for (const [spelling, source] of Object.entries(SPELLINGS)) {
	test(`${spelling} in a module a page runs fails`, (t) => {
		const ran = check(t, { ...LISTED, 'src/lib/spawns.mjs': source });
		assert.equal(ran.status, 1);
		assert.match(ran.err, /FAIL 1 file\(s\) that start a process where a page renders[^\n]*:\s+src\/lib\/spawns\.mjs/);
	});
}

for (const path of [
	'src/components/Head.astro',
	'src/routeData.ts',
	'src/data/stats.mjs',
	'src/utils/cards.tsx',
	'src/lib/old.cjs',
	'src/content/docs/page.mdx',
]) {
	test(`a planted spawn in ${path} fails`, (t) => {
		const ran = check(t, { ...LISTED, [path]: ONE_CALL });
		assert.equal(ran.status, 1);
		assert.ok(ran.err.includes(path), ran.err);
	});
}

test('a module outside the source that a page imports is read as well', (t) => {
	const ran = check(t, {
		...LISTED,
		'src/components/Head.astro': `---\nimport { date } from '../../scripts/shared/date.mjs';\n---\n`,
		'scripts/shared/date.mjs': `import './deeper';\n`,
		'scripts/shared/deeper.mjs': ONE_CALL,
		'scripts/unrelated.mjs': ONE_CALL,
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 1 file\(s\)[^\n]*:\s+scripts\/shared\/deeper\.mjs/);
	assert.doesNotMatch(ran.err, /unrelated/);
});

/** A module outside the source that spawns, by the path each test imports it under. */
const OUTSIDE = (specifier, path) => ({
	'src/components/Head.astro': `---\nimport { date } from '${specifier}';\n---\n`,
	[path]: ONE_CALL,
});

for (const [form, specifier, path] of [
	['a directory holding index.mjs', '../../scripts/zz', 'scripts/zz/index.mjs'],
	['a directory holding index.js', '../../scripts/zz', 'scripts/zz/index.js'],
	['a directory holding index.mts', '../../scripts/zz', 'scripts/zz/index.mts'],
	['a directory holding index.ts', '../../scripts/zz', 'scripts/zz/index.ts'],
	['a directory holding index.jsx', '../../scripts/zz', 'scripts/zz/index.jsx'],
	['a directory holding index.tsx', '../../scripts/zz', 'scripts/zz/index.tsx'],
	['no extension, to a .mjs file', '../../scripts/zz/sp', 'scripts/zz/sp.mjs'],
	['no extension, to a .js file', '../../scripts/zz/sp', 'scripts/zz/sp.js'],
	['no extension, to a .mts file', '../../scripts/zz/sp', 'scripts/zz/sp.mts'],
	['no extension, to a .ts file', '../../scripts/zz/sp', 'scripts/zz/sp.ts'],
	['no extension, to a .jsx file', '../../scripts/zz/sp', 'scripts/zz/sp.jsx'],
	['no extension, to a .tsx file', '../../scripts/zz/sp', 'scripts/zz/sp.tsx'],
	['a path from the root of the site', '/scripts/zz/sp.mjs', 'scripts/zz/sp.mjs'],
	['a path from the root of the site, with no extension', '/scripts/zz/sp', 'scripts/zz/sp.mts'],
	['a directory, from the root of the site', '/scripts/zz', 'scripts/zz/index.mjs'],
	['a .js path to a .ts file', '../../scripts/zz/sp.js', 'scripts/zz/sp.ts'],
	['a .js path to a .tsx file', '../../scripts/zz/sp.js', 'scripts/zz/sp.tsx'],
	['a .mjs path to a .mts file', '../../scripts/zz/sp.mjs', 'scripts/zz/sp.mts'],
	['a .cjs path to a .cts file', '../../scripts/zz/sp.cjs', 'scripts/zz/sp.cts'],
	['a .jsx path to a .tsx file', '../../scripts/zz/sp.jsx', 'scripts/zz/sp.tsx'],
]) {
	test(`a module outside the source imported as ${form} is read as well`, (t) => {
		const ran = check(t, { ...LISTED, ...OUTSIDE(specifier, path) });
		assert.equal(ran.status, 1);
		assert.match(ran.err, new RegExp(`FAIL 1 file\\(s\\)[^\\n]*:\\s+${literal(path)}`));
	});
}

test('a path from the root that leaves the site, or names no file, is read as nothing', (t) => {
	const ran = check(t, {
		...LISTED,
		'src/components/Head.astro': `---\nconst a = '/../outside/sp.mjs';\nconst b = '/no/such/page/';\n---\n`,
	});
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /read 4 files a page can run; 3 reach for a process/);
});

test('the helper of a listed file handed to every page fails, though the call it counts is still one', (t) => {
	const ran = check(t, {
		...LISTED,
		'src/lib/page-dates.mjs': `import { execFileSync } from 'node:child_process';
export function git(...args) {
	return execFileSync('git', args);
}
export function firstPublished() {}
`,
		'src/components/Head.astro': `---
import { git } from '../lib/page-dates.mjs';
const perPage = git('log', '-1', '--format=%cI', '--', Astro.url.pathname);
---
`,
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, /src\/lib\/page-dates\.mjs: exports git, which the list does not name/);
	assert.doesNotMatch(ran.err, /call\(s\) where the list says/);
});

for (const [form, source, name] of [
	['an async function', `export async function git() {}\n`, 'git'],
	['a generator', `export function* git() {}\n`, 'git'],
	['a generator, with the star on its name', `export function *git() {}\n`, 'git'],
	['a class', `export class Git {}\n`, 'Git'],
	['a declaration across lines', `export\n\tfunction git() {}\n`, 'git'],
	['a constant', `export const git = () => {};\n`, 'const git'],
	['a second constant behind the allowed name', `export const firstPublished = 1, git = () => {};\n`, 'const firstPublished'],
	['a destructured constant', `export const { git } = helpers;\n`, 'const \\{ git \\}'],
	['a let', `export let git;\n`, 'let git'],
	['a list', `function git() {}\nexport { git };\n`, 'git'],
	['a list across lines', `export {\n\thelper,\n\tgit as run,\n};\n`, 'run'],
	['a default', `export default function git() {}\n`, 'default'],
	['a default in a list', `function git() {}\nexport { git as default };\n`, 'default'],
	['a re-export', `export { git } from './helpers.mjs';\n`, 'git'],
	['a re-export of everything', `export * from './helpers.mjs';\n`, '\\*'],
	['a re-export under a name', `export * as helpers from './helpers.mjs';\n`, '\\* as helpers'],
	['module.exports', `module.exports = { git };\n`, 'module\\.exports'],
	['exports.name', `exports.git = git;\n`, 'exports\\.git'],
]) {
	test(`${form} beside what a listed file may give out fails`, (t) => {
		const ran = check(t, { ...LISTED, 'src/lib/page-dates.mjs': `${LISTED['src/lib/page-dates.mjs']}${source}` });
		assert.equal(ran.status, 1);
		assert.match(ran.err, new RegExp(`src/lib/page-dates\\.mjs: exports ${name}[^\\n]*, which the list does not name`));
	});
}

test('astro.config.mjs may give out its default and nothing else', (t) => {
	const ran = check(t, { ...LISTED, 'astro.config.mjs': `${LISTED['astro.config.mjs']}export function git() {}\n` });
	assert.equal(ran.status, 1);
	assert.match(ran.err, /astro\.config\.mjs: exports git, which the list does not name/);
});

test('an export the list names and the file no longer holds fails, so the list cannot go stale', (t) => {
	const ran = check(t, { ...LISTED, 'src/lib/page-dates.mjs': ONE_CALL });
	assert.equal(ran.status, 1);
	assert.match(ran.err, /src\/lib\/page-dates\.mjs: the list names firstPublished, which it does not export/);
});

test('the word in a sentence about a package map is not an export', (t) => {
	const ran = check(t, {
		...LISTED,
		'astro.config.mjs': `// The package publishes no \`exports\` map.\n${LISTED['astro.config.mjs']}`,
	});
	assert.equal(ran.status, 0, ran.err);
});

test('a second call in a listed file fails', (t) => {
	const ran = check(t, {
		...LISTED,
		'src/lib/page-dates.mjs': `${LISTED['src/lib/page-dates.mjs']}const again = (file) => execFileSync('git', ['log', file]);\n`,
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, /src\/lib\/page-dates\.mjs: 2 call\(s\) where the list says 1/);
});

test('a listed file with no calls left fails, and so does one that is gone', (t) => {
	const ran = check(t, { 'astro.config.mjs': `export default {};\n` });
	assert.equal(ran.status, 1);
	assert.match(
		ran.err,
		/FAIL 3 entries of ONCE_PER_BUILD that cover nothing:\s+astro\.config\.mjs\s+src\/lib\/page-dates\.mjs\s+src\/lib\/content-dates\.mjs/,
	);
});
