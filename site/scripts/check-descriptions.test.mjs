// The failures check-descriptions.mjs exists to report, on builds small enough
// to read.
//
// The real build only ever hands the check pages that pass, so a check that
// stopped seeing a missing description, counted one character too many or
// compared two descriptions as written rather than as read would stay green
// there for good. Each test here writes a build of a few pages into a
// directory of its own, runs the check on it the way CI does, and reads the
// exit status and the lines it printed.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-descriptions.mjs');

/**
 * A built page whose head carries one meta description per argument, written
 * as Astro writes it; `undefined` writes one with no content attribute.
 */
const page = (...descriptions) =>
	[
		'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">',
		...descriptions.map((text) =>
			text === undefined ? '<meta name="description">' : `<meta name="description" content="${text}">`,
		),
		'<title>A page</title></head><body><h1>A page</h1></body></html>',
	].join('');

/** One of the stubs that send a retired address on, which carry no description. */
const STUB = '<!DOCTYPE html><title>Redirecting</title><meta http-equiv="refresh" content="0;url=/a/">';

/** `n` characters of text, none of them spacing, so trimming leaves it whole. */
const text = (n) => 'x'.repeat(n);

/**
 * Write `files`, paths under the build mapped to their HTML, into a build of
 * its own, run the check on it, and say how it ended.
 */
function check(t, files) {
	const dist = mkdtempSync(join(tmpdir(), 'check-descriptions-'));
	t.after(() => rmSync(dist, { recursive: true, force: true }));
	for (const [path, html] of Object.entries(files)) {
		mkdirSync(dirname(join(dist, path)), { recursive: true });
		writeFileSync(join(dist, path), html);
	}
	const ran = spawnSync(process.execPath, [CHECK, dist], { encoding: 'utf8' });
	return { status: ran.status, out: ran.stdout, err: ran.stderr };
}

test('a build where every page has a short description of its own passes', (t) => {
	const ran = check(t, {
		'index.html': page('The home page.'),
		'a/index.html': page('A page about one thing.'),
		'es/a/index.html': page('Una página sobre una cosa.'),
	});
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /read 3 pages/);
	assert.match(ran.out, /ok {3}every meta description is unique within its language/);
	assert.match(ran.out, /\n0 failing check\(s\)\./);
	assert.equal(ran.err, '');
});

test('a page with no meta description fails', (t) => {
	const ran = check(t, { 'a/index.html': page(), 'b/index.html': page('Fine.') });
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 1 page\(s\) without exactly one meta description:\s+\/a\/: 0 meta descriptions/);
});

test('a page with two meta descriptions fails', (t) => {
	const ran = check(t, { 'a/index.html': page('One.', 'Two.') });
	assert.equal(ran.status, 1);
	assert.match(ran.err, /\/a\/: 2 meta descriptions/);
});

for (const [name, description] of [
	['an empty content', ''],
	['a content of nothing but spacing', ' \t '],
	['no content attribute', undefined],
]) {
	test(`a meta description with ${name} fails as empty`, (t) => {
		const ran = check(t, { 'a/index.html': page(description), 'b/index.html': page('Fine.') });
		assert.equal(ran.status, 1);
		assert.match(ran.err, /FAIL 1 page\(s\) whose meta description is empty:\s+\/a\//);
	});
}

test('160 characters pass and 161 fail', (t) => {
	const passes = check(t, { 'a/index.html': page(text(160)) });
	assert.equal(passes.status, 0, passes.err);
	assert.match(passes.out, /ok {3}every meta description is at most 160 characters/);

	const fails = check(t, { 'a/index.html': page(text(161)) });
	assert.equal(fails.status, 1);
	assert.match(fails.err, /FAIL 1 meta description\(s\) over 160 characters:\s+\/a\/: 161 characters/);
});

test('the length is counted as a reader counts it', (t) => {
	// Spacing around the text is not shown, an entity is one character once
	// decoded and a character outside the Basic Multilingual Plane is one, not
	// the two UTF-16 units JavaScript's own length would count.
	const ran = check(t, {
		'a/index.html': page(`  ${text(159)}  `),
		'b/index.html': page(`${text(155)}&amp;&quot;`),
		'c/index.html': page(`${text(159)}\u{1D43F}`),
	});
	assert.equal(ran.status, 0, ran.err);

	const astral = check(t, { 'a/index.html': page(`${text(160)}\u{1D43F}`) });
	assert.equal(astral.status, 1);
	assert.match(astral.err, /\/a\/: 161 characters/);
});

test('two pages of one language with the same description fail', (t) => {
	const ran = check(t, {
		'a/index.html': page('The same words.'),
		'b/index.html': page('The same words.'),
		'c/index.html': page('Other words.'),
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 1 meta description\(s\) shared by pages of one language/);
	assert.match(ran.err, /"the same words\." \(en\): \/a\/ \/b\//);
	assert.doesNotMatch(ran.err, /\/c\//);
});

test('descriptions that differ only in case and spacing are the same description', (t) => {
	const ran = check(t, {
		'es/a/index.html': page('Las mismas palabras.'),
		'es/b/index.html': page('  las MISMAS\t\tpalabras. '),
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, /"las mismas palabras\." \(es\): \/es\/a\/ \/es\/b\//);
});

test('the same description in the two languages is not a repeat', (t) => {
	const ran = check(t, {
		'a/index.html': page('Phonometry.'),
		'es/a/index.html': page('Phonometry.'),
	});
	assert.equal(ran.status, 0, ran.err);
});

test('redirect stubs, error pages and Spanish API routes are skipped', (t) => {
	// None of these would pass: the stub has no description, the error pages
	// carry the long site description, and the Spanish API page repeats its
	// English twin's description on purpose.
	const long = text(319);
	const ran = check(t, {
		'reference/api/index.html': page('The API reference.'),
		'es/reference/api/index.html': page('The API reference.'),
		'es/reference/api/signals/index.html': page(),
		'old-address/index.html': STUB,
		'404.html': page(long),
		'es/404.html': page(long),
	});
	assert.equal(ran.status, 0, ran.err);
	assert.match(ran.out, /read 1 pages .* and skipped 5 stubs, error pages and fallback routes/);
});

test('the English twin of a skipped Spanish API route is still checked', (t) => {
	const ran = check(t, {
		'reference/api/signals/index.html': page(),
		'es/reference/api/signals/index.html': page(),
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, /\/reference\/api\/signals\/: 0 meta descriptions/);
	assert.doesNotMatch(ran.err, /\/es\/reference\/api\//);
});

test('a route that only starts like a skipped one is checked', (t) => {
	const ran = check(t, {
		'es/reference/apis/index.html': page(),
		'es/404-guide/index.html': page(),
	});
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 2 page\(s\) without exactly one meta description/);
});

test('a missing build is an error, not a pass', () => {
	const dist = mkdtempSync(join(tmpdir(), 'check-descriptions-'));
	rmSync(dist, { recursive: true, force: true });
	const ran = spawnSync(process.execPath, [CHECK, dist], { encoding: 'utf8' });
	assert.notEqual(ran.status, 0);
	assert.match(ran.stderr, /no build at/);
});
