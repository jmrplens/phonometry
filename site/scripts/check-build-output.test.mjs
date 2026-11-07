// The failures check-build-output.mjs exists to report, on build logs small
// enough to read.
//
// A real build only hands the check the output of a build that passes it, so a
// check that stopped reading one shape of warning, or read one only at the
// start of a line, would stay green there for good. Each test here writes a
// few lines of build output to a file of its own, runs the check on it the way
// CI does, and reads the exit status and the lines it printed.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-build-output.mjs');

/** The one warning the site cannot silence, as Starlight's lookup prints it. */
const KNOWN_404 = '22:05:22 [WARN] [content] Entry docs → 404 was not found.';

/** Route lines as Astro writes them, one glued to the next with no newline. */
const ROUTES =
	'22:05:21   ├─ /reference/api/signals/warnings/index.html (+3ms)\n' +
	'22:05:21   ├─ /404.html22:05:21   ├─ /about/index.html (+2ms)\n';

/** Write `text` as a build log of its own, run the check on it, and say how it ended. */
function check(t, text) {
	const dir = mkdtempSync(join(tmpdir(), 'check-build-output-'));
	t.after(() => rmSync(dir, { recursive: true, force: true }));
	const log = join(dir, 'build.log');
	writeFileSync(log, text);
	const ran = spawnSync(process.execPath, [CHECK, log], { encoding: 'utf8' });
	return { status: ran.status, out: ran.stdout, err: ran.stderr };
}

test('a build that printed only the known warning passes', (t) => {
	const ran = check(t, `$ astro build\n${ROUTES}${KNOWN_404}\n[build] Complete!\n`);
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}the build printed no warning but the known ones/);
	assert.match(ran.out, /ok {3}every known warning is still printed/);
	assert.match(ran.out, /\n0 failing check\(s\)\./);
	assert.equal(ran.err, '');
});

test('a known warning the build no longer prints fails, naming it', (t) => {
	const ran = check(t, `$ astro build\n${ROUTES}[build] Complete!\n`);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /1 known warning\(s\) the build no longer prints/);
	assert.match(ran.err, /Entry docs → 404 was not found\. \(remove it from KNOWN: Starlight/);
});

const SHAPES = {
	"Astro's deprecation of a config key": {
		line: '[astro] `markdown.remarkPlugins`, `markdown.rehypePlugins`, and `markdown.remarkRehype` are deprecated. Pass them to `unified({...})` instead.',
		kind: 'a notice that something is deprecated',
	},
	"KaTeX's strict mode": {
		line: 'LaTeX-incompatible input and strict mode is set to \'warn\': Unrecognized Unicode character "µ" (181) [unknownSymbol]',
		kind: "KaTeX's strict-mode report",
	},
	"Astro's logger": {
		line: '22:05:23 [WARN] [vite] Some chunks are larger than 500 kB after minification.',
		kind: "Astro's logger at its warning level",
		read: '[WARN] [vite] Some chunks are larger than 500 kB after minification.',
	},
	'a process warning from Node': {
		line: '(node:4242) ExperimentalWarning: CommonJS module loading of ES modules is experimental',
		kind: 'a process warning from Node',
	},
};

for (const [name, { line, kind, read = line }] of Object.entries(SHAPES)) {
	test(`${name} fails the check, read from where it starts`, (t) => {
		const ran = check(t, `$ astro build\n${ROUTES}${line}\n${KNOWN_404}\n`);
		assert.equal(ran.status, 1, ran.out);
		assert.match(ran.err, /1 warning\(s\) the build printed/);
		assert.ok(ran.err.includes(`${kind}: ${read}`), ran.err);
	});
}

test('a warning glued to the end of a route line is read from its bracket', (t) => {
	const glued = '22:05:21   ├─ /environment/levels/index.html22:05:21 [WARN] [router] A route was matched twice.';
	const ran = check(t, `${ROUTES}${glued}\n${KNOWN_404}\n`);
	assert.equal(ran.status, 1, ran.out);
	assert.ok(
		ran.err.includes("Astro's logger at its warning level: [WARN] [router] A route was matched twice."),
		ran.err,
	);
});

test('a warning in colour and with Windows line ends is read as plain text', (t) => {
	const coloured = '\x1b[33m[WARN]\x1b[39m \x1b[2m[content]\x1b[22m Entry docs → 404 was not found.';
	const ran = check(t, `$ astro build\r\n${coloured}\r\n[build] Complete!\r\n`);
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /ok {3}every known warning is still printed/);
});

test('a line two shapes read is one warning', (t) => {
	const node = '(node:4242) [DEP0040] DeprecationWarning: The `punycode` module is deprecated.';
	const ran = check(t, `${node}\n${KNOWN_404}\n`);
	assert.equal(ran.status, 1, ran.out);
	assert.match(ran.err, /1 warning\(s\) the build printed/);
});

test('a page whose route names warnings is no warning', (t) => {
	const ran = check(t, `${ROUTES}22:05:22   ├─ /es/reference/warnings/deprecations/index.html (+1ms)\n${KNOWN_404}\n`);
	assert.equal(ran.status, 0, ran.err);
});

test('no log to read is a usage error', (t) => {
	const ran = spawnSync(process.execPath, [CHECK], { encoding: 'utf8' });
	assert.equal(ran.status, 2);
	assert.match(ran.stderr, /usage: node scripts\/check-build-output\.mjs <build log>/);
	t.diagnostic('the check needs the path of a saved build log');
});
