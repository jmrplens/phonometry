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

/** A module that reaches for child_process and calls it once, the way the listed ones do. */
const ONE_CALL = `import { execFileSync } from 'node:child_process';\nexecFileSync('git', ['log']);\n`;

/** The two files the list names, each as it should be. */
const LISTED = { 'astro.config.mjs': ONE_CALL, 'src/lib/page-dates.mjs': ONE_CALL };

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
	assert.match(ran.out, /read 4 files a page can run; 2 reach for a process/);
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
	'a package that wraps it': `import { execa } from 'execa';\nawait execa('git');\n`,
	'a path into a package that wraps it': `import spawn from 'cross-spawn/index.js';\nspawn('git');\n`,
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
		assert.match(ran.err, new RegExp(path.replace(/[.]/g, '\\.')));
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

test('a second call in a listed file fails', (t) => {
	const ran = check(t, {
		...LISTED,
		'src/lib/page-dates.mjs': `${ONE_CALL}export const again = (file) => execFileSync('git', ['log', file]);\n`,
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, /src\/lib\/page-dates\.mjs: 2 call\(s\) where the list says 1/);
});

test('a listed file with no calls left fails, and so does one that is gone', (t) => {
	const ran = check(t, { 'astro.config.mjs': `export default {};\n` });
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 2 entries of ONCE_PER_BUILD that cover nothing:\s+astro\.config\.mjs\s+src\/lib\/page-dates\.mjs/);
});
