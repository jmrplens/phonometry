// Fails when the site build printed a warning.
//
// A build that passes says nothing about what it printed on the way, and
// nobody reads a log of a thousand route lines. Three warnings rode in every
// build that way: Astro saying that `markdown.remarkPlugins` and
// `markdown.rehypePlugins` were deprecated, KaTeX saying twice per language
// that it had no metrics for the µ of a formula, which the page then set from
// a fallback font, and Starlight's lookup of a 404 entry the site does not
// have. The first two were ours to fix and went unfixed until an audit read
// the log by hand; the third is printed glued to the end of a route line, so a
// search for lines that start with a warning misses it.
//
// So the docs workflow keeps the build's output, and this reads it for the
// shapes a warning takes there: Astro's logger at its warning level, which
// Vite and every integration log through; a notice that something is
// deprecated, whoever prints it; KaTeX's strict-mode report; and a process
// warning from Node. Each is read from where it starts to the end of its line,
// wherever on the line it starts, and a line two shapes read is one warning.
// A warning the site cannot silence is listed in KNOWN, word for word, with
// the reason; an entry the build no longer prints fails too, so the list
// empties as the fixes land upstream.
//
// Usage: pnpm build 2>&1 | tee build.log
//        node scripts/check-build-output.mjs build.log
import { existsSync, readFileSync } from 'node:fs';

import { reporter } from './shared/dist-pages.mjs';

/** The shapes a warning takes in the build's output, each read to the end of its line. */
const WARNINGS = [
	{ kind: "Astro's logger at its warning level", pattern: /\[WARN\][^\n]*/g },
	{ kind: 'a notice that something is deprecated', pattern: /[^\n]*\bdeprecated\b[^\n]*/gi },
	{ kind: 'a deprecation warning', pattern: /[^\n]*\bDeprecationWarning\b[^\n]*/g },
	{ kind: "KaTeX's strict-mode report", pattern: /LaTeX-incompatible input[^\n]*/g },
	{ kind: 'a process warning from Node', pattern: /\(node:\d+\)[^\n]*Warning\b[^\n]*/g },
];

/**
 * Warnings the site cannot silence, each as the build prints it from where
 * its shape starts, with the reason. Starlight 0.42.8 asks for a docs entry
 * named 404 on every build and serves a page of its own when there is none,
 * and Astro 7.4.4 warns for every entry `getEntry` does not find. A 404 page
 * of the site's own would need its Spanish twin and a place in every check
 * that reads the build, to silence a lookup that works.
 */
const KNOWN = [
	{
		line: '[WARN] [content] Entry docs → 404 was not found.',
		why: 'Starlight 0.42.8 looks up a 404 entry the site does not have, and Astro 7.4.4 warns for each entry getEntry misses',
	},
];

/** Colour and style escapes, which a terminal-aware tool may write even into a pipe. */
const ESCAPES = /\x1b\[[0-9;]*m/g;

const path = process.argv[2];
if (!path) {
	console.error('usage: node scripts/check-build-output.mjs <build log>');
	process.exit(2);
}
if (!existsSync(path)) {
	throw new Error(`no build log at ${path}: tee the output of \`pnpm build\` there first`);
}
const text = readFileSync(path, 'utf8').replace(ESCAPES, '').replace(/\r\n?/g, '\n');

// One warning per line it is printed on, read from the latest place a shape
// starts there: a [WARN] glued to the end of a route line is read from its
// bracket, not from the route.
const byLine = new Map();
for (const { kind, pattern } of WARNINGS) {
	for (const match of text.matchAll(pattern)) {
		const lineStart = text.lastIndexOf('\n', match.index) + 1;
		const held = byLine.get(lineStart);
		if (held === undefined || match.index > held.at) {
			byLine.set(lineStart, { at: match.index, kind, line: match[0].trim() });
		}
	}
}

const printed = new Set();
const unknown = [];
for (const { kind, line } of byLine.values()) {
	if (KNOWN.some((entry) => entry.line === line)) printed.add(line);
	else unknown.push(`${kind}: ${line}`);
}
const gone = KNOWN.filter((entry) => !printed.has(entry.line));

const { report, failures } = reporter();
console.log(`read ${text.split('\n').length} lines of build output in ${path}`);
report(unknown, 'warning(s) the build printed', 'the build printed no warning but the known ones');
report(
	gone.map((entry) => `${entry.line} (remove it from KNOWN: ${entry.why})`),
	'known warning(s) the build no longer prints',
	'every known warning is still printed',
);
console.log(`\n${failures()} failing check(s).`);
process.exit(failures() ? 1 : 0);
