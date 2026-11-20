// The failures check-link-text.mjs exists to report, on builds small enough
// to read.
//
// The real build only ever hands the check pages that pass, so a check that
// stopped seeing a link's text across its tags, read a link Lighthouse leaves
// out or fell behind the words Lighthouse lists would stay green there for
// good. Each test here writes a build of a few pages into a directory of its
// own, runs the check on it the way CI does, and reads the exit status and the
// lines it printed; the last holds the check's two lists to the ones in the
// installed Lighthouse.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { NON_DESCRIPTIVE } from './check-link-text.mjs';

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-link-text.mjs');

/** A built page of language `lang` whose body carries the given links. */
const page = (links, lang = 'en') =>
	`<!DOCTYPE html><html lang="${lang}"><head><meta charset="utf-8"><title>A page</title></head><body><h1>A page</h1>${links}</body></html>`;

/** One of the stubs that send a retired address on, which no engine reads as a page. */
const STUB = '<!DOCTYPE html><title>Redirecting</title><meta http-equiv="refresh" content="0;url=/a/"><a href="/a/">here</a>';

/**
 * Run the check on a build made of `files`, a map from a path under dist/ to
 * the HTML it holds, and return its exit status and everything it printed.
 */
function run(files) {
	const root = mkdtempSync(join(tmpdir(), 'link-text-'));
	try {
		for (const [path, html] of Object.entries(files)) {
			const file = join(root, path);
			mkdirSync(dirname(file), { recursive: true });
			writeFileSync(file, html);
		}
		const result = spawnSync(process.execPath, [CHECK, root], { encoding: 'utf8' });
		return { status: result.status, output: `${result.stdout}${result.stderr}` };
	} finally {
		rmSync(root, { recursive: true, force: true });
	}
}

test('a link that reads "Start" fails, and one that reads "Start here" passes', () => {
	const vague = run({ 'index.html': page('<a href="/start/">Start</a>') });
	assert.equal(vague.status, 1, vague.output);
	assert.match(vague.output, /\/: a link to \/start\/ reads "start"/);
	const named = run({ 'index.html': page('<a href="/start/">Start here</a>') });
	assert.equal(named.status, 0, named.output);
});

test("a link's text is read across its tags, entities and spacing, as a reader sees it", () => {
	const icon = '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M0 0"/></svg>';
	const wrapped = run({
		'index.html': page(`<a href="/a/" class="topic"><div class="icon">${icon}</div><span>\n  Read\n  <em>more</em> </span></a>`),
	});
	assert.equal(wrapped.status, 1, wrapped.output);
	assert.match(wrapped.output, /reads "read more"/);
	const accented = run({ 'es/index.html': page('<a href="/es/a/">M&#225;s</a>', 'es') });
	assert.equal(accented.status, 1, accented.output);
	assert.match(accented.output, /reads "más"/);
});

test('both languages are held on every page, and a descriptive Spanish label passes', () => {
	const spanishWordInEnglish = run({ 'a/index.html': page('<a href="/b/">aquí</a>') });
	assert.equal(spanishWordInEnglish.status, 1, spanishWordInEnglish.output);
	const inicio = run({ 'es/index.html': page('<a href="/es/start/">Inicio</a>', 'es') });
	assert.equal(inicio.status, 0, inicio.output);
});

test('the links Lighthouse leaves out are left out, and so are the redirect stubs', () => {
	const skipped = run({
		'a/index.html': page(
			[
				'<a>more</a>',
				'<a href="">more</a>',
				'<a href="#top">more</a>',
				'<a href="/a/#top">more</a>',
				'<a href="/a/">more</a>',
				'<a href="javascript:void(0)">more</a>',
				'<a href="mailto:someone@example.org">here</a>',
				'<a href="/b/" rel="external nofollow">here</a>',
			].join(''),
		),
		'old/index.html': STUB,
	});
	assert.equal(skipped.status, 0, skipped.output);
	assert.match(skipped.output, /read the links of 1 pages/);
});

test("the two lists are Lighthouse's own", () => {
	const require = createRequire(import.meta.url);
	const source = readFileSync(
		join(dirname(require.resolve('lighthouse/package.json')), 'core/audits/seo/link-text.js'),
		'utf8',
	);
	for (const lang of Object.keys(NON_DESCRIPTIVE)) {
		const block = source.match(new RegExp(`'${lang}': new Set\\(\\[([\\s\\S]*?)\\]\\)`));
		assert.ok(block, `Lighthouse no longer lists link texts for "${lang}" the way this test reads them`);
		const listed = [...block[1].matchAll(/'([^']*)'/g)].map(([, text]) => text);
		assert.deepEqual([...NON_DESCRIPTIVE[lang]].sort(), listed.sort(), `the "${lang}" list differs from Lighthouse's`);
	}
});
