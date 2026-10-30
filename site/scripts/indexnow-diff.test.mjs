// What scripts/indexnow-diff.mjs tells IndexNow, on builds small enough to read.
//
// The script runs for real only on a deploy, after the merge, so nothing in a
// pull request would show that it sends the pages that changed and only
// those. The deploy used to send every URL of the sitemap, and a script that
// fell back to that on every run would still deploy green. Each test here
// writes a build of a few pages with a sitemap, a Markdown copy beside each
// page and the head an engine reads, runs the script on it the way the build
// and the deploy do, and reads what it would submit.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { releaseHeaderKeys, withoutReleaseLines } from '../src/lib/page-markdown.mjs';
import { MANIFEST_NAME, ORIGIN, loadPrevious, serialize, urlsToSubmit } from './indexnow-diff.mjs';

const SCRIPT = join(dirname(fileURLToPath(import.meta.url)), 'indexnow-diff.mjs');

/** A copy as the build writes one today: a comment, a field block, the body. */
const copy = (route, body, header = []) =>
	[`<!-- canonical: ${ORIGIN}${route} -->`, `Source: ${ORIGIN}${route}`, ...header, '', body, ''].join('\n');

/** A guide page: its head, a <main>, a date and a copy. */
const guide = (route, { title = `Guide ${route}`, description = `About ${route}.`, lastmod = '2026-10-01', body = `Text of ${route}.`, header = [] } = {}) => ({
	title,
	description,
	lastmod,
	main: `<h1>${title}</h1><p>${body}</p>`,
	copy: copy(route, body, header),
});

/** The pages most tests start from. */
const BASE = {
	'/signals/levels/': guide('/signals/levels/'),
	'/signals/filters/': guide('/signals/filters/'),
	'/es/signals/levels/': guide('/es/signals/levels/'),
};

/**
 * Write a build of `pages` (route -> page) into a fresh directory: each page's
 * index.html with its title, description and <main>, its index.md when it has
 * a copy, and a sitemap listing every route with its date. `head` goes into
 * every page's head, as the asset links of a build do.
 */
function build(t, pages, { head = '' } = {}) {
	const dist = mkdtempSync(join(tmpdir(), 'indexnow-'));
	t.after(() => rmSync(dist, { recursive: true, force: true }));
	for (const [route, page] of Object.entries(pages)) {
		const dir = join(dist, ...route.split('/').filter(Boolean));
		mkdirSync(dir, { recursive: true });
		writeFileSync(
			join(dir, 'index.html'),
			`<!DOCTYPE html><html><head><title>${page.title}</title><meta name="description" content="${page.description}">${head}</head>` +
				`<body><nav>Sidebar</nav>${page.main === null ? '' : `<main data-pagefind-body>${page.main}</main>`}</body></html>`,
		);
		if (page.copy !== null) writeFileSync(join(dir, 'index.md'), page.copy);
	}
	const urls = Object.entries(pages)
		.map(([route, page]) => `<url><loc>${ORIGIN}${route}</loc>${page.lastmod ? `<lastmod>${page.lastmod}</lastmod>` : ''}</url>`)
		.join('');
	writeFileSync(join(dist, 'sitemap-0.xml'), `<urlset>${urls}</urlset>`);
	writeFileSync(join(dist, 'sitemap-index.xml'), `<sitemapindex><sitemap><loc>${ORIGIN}/sitemap-0.xml</loc></sitemap></sitemapindex>`);
	return dist;
}

/** Run the script with `args` and say how it ended. */
function run(...args) {
	const ran = spawnSync(process.execPath, [SCRIPT, ...args], { encoding: 'utf8' });
	return { status: ran.status, out: ran.stdout, err: ran.stderr };
}

/** Write the manifest of a build, as `postbuild` does, and return it. */
function manifest(dist) {
	const ran = run('manifest', dist);
	assert.equal(ran.status, 0, ran.err);
	return readFileSync(join(dist, MANIFEST_NAME), 'utf8');
}

/**
 * What the deploy of `pages` would submit after a deploy of `before` (a list
 * of pages, or `null` for no previous manifest at all), with the lines the
 * script printed.
 */
function submit(t, before, pages, options = {}) {
	const previous = join(mkdtempSync(join(tmpdir(), 'indexnow-previous-')), MANIFEST_NAME);
	t.after(() => rmSync(dirname(previous), { recursive: true, force: true }));
	if (before !== null) writeFileSync(previous, manifest(build(t, before)));
	const dist = build(t, pages, options);
	manifest(dist);
	const out = join(dirname(previous), 'urls.json');
	const ran = run('diff', '--dist', dist, '--previous', previous, '--out', out);
	assert.equal(ran.status, 0, ran.err);
	return { ...JSON.parse(readFileSync(out, 'utf8')), printed: ran.out };
}

const url = (route) => `${ORIGIN}${route}`;

test('a deploy that changed one page submits that page and none of the others', (t) => {
	const after = { ...BASE, '/signals/filters/': guide('/signals/filters/', { body: 'The filters, rewritten.' }) };
	const sent = submit(t, BASE, after);
	assert.equal(sent.full, false);
	assert.deepEqual(sent.changed, [url('/signals/filters/')]);
	assert.deepEqual(sent.urls, [url('/signals/filters/')]);
	assert.match(sent.printed, /1 changed, 0 new and 0 removed of 3 pages: 1 URLs to submit/);
});

test('a deploy that changed nothing submits nothing', (t) => {
	const sent = submit(t, BASE, BASE);
	assert.deepEqual(sent.urls, []);
	assert.equal(sent.full, false);
});

test('a page the previous deploy did not have is submitted as new', (t) => {
	const after = { ...BASE, '/signals/weighting/': guide('/signals/weighting/') };
	const sent = submit(t, BASE, after);
	assert.deepEqual(sent.new, [url('/signals/weighting/')]);
	assert.deepEqual(sent.urls, [url('/signals/weighting/')]);
});

test('a page the previous deploy had and this one does not is submitted as removed', (t) => {
	const { '/es/signals/levels/': _gone, ...after } = BASE;
	const sent = submit(t, BASE, after);
	assert.deepEqual(sent.removed, [url('/es/signals/levels/')]);
	assert.deepEqual(sent.urls, [url('/es/signals/levels/')]);
	assert.match(sent.printed, /removed https:\/\/docs\.jmrp\.io\/phonometry\/es\/signals\/levels\//);
});

test('with no previous manifest every URL of the sitemap is submitted', (t) => {
	const sent = submit(t, null, BASE);
	assert.equal(sent.full, true);
	assert.equal(sent.reason, 'there is no such file');
	assert.deepEqual(sent.urls, Object.keys(BASE).map(url).sort());
	assert.match(sent.printed, /the full list goes out: 3 URLs/);
});

test('a previous manifest that cannot be compared with sends every URL, and says why', (t) => {
	const dir = mkdtempSync(join(tmpdir(), 'indexnow-bad-'));
	t.after(() => rmSync(dir, { recursive: true, force: true }));
	const dist = build(t, BASE);
	manifest(dist);
	const cases = {
		'not JSON': ['<!DOCTYPE html><title>Not found</title>', /it is not JSON/],
		'another format': [JSON.stringify({ format: 0, pages: {} }), /it is format 0, and this script writes format 1/],
		'another site': [JSON.stringify({ format: 1, pages: { 'https://example.org/x/': 'a'.repeat(64) } }), /outside https:\/\/docs\.jmrp\.io\/phonometry\//],
		'not a digest': [JSON.stringify({ format: 1, pages: { [url('/x/')]: 'abc' } }), /is not a sha256/],
	};
	for (const [name, [text, reason]] of Object.entries(cases)) {
		const previous = join(dir, `${name}.json`);
		writeFileSync(previous, text);
		const out = join(dir, `${name}.out.json`);
		const ran = run('diff', '--dist', dist, '--previous', previous, '--out', out);
		assert.equal(ran.status, 0, `${name}: ${ran.err}`);
		const sent = JSON.parse(readFileSync(out, 'utf8'));
		assert.equal(sent.full, true, name);
		assert.match(sent.reason, reason, name);
		assert.equal(sent.urls.length, 3, name);
	}
});

test('a copy that differs only in its Version: and Install: lines hashes the same', (t) => {
	assert.deepEqual([...releaseHeaderKeys], ['Version', 'Install']);
	const stamped = (version) =>
		Object.fromEntries(
			Object.keys(BASE).map((route) => [
				route,
				guide(route, { header: [`Version: phonometry ${version}`, `Install: pip install "phonometry[full]>=${version}"`, 'License: MIT'] }),
			]),
		);
	const sent = submit(t, stamped('4.0.0'), stamped('4.0.1'));
	assert.deepEqual(sent.urls, []);
});

test('every other header line, and the same words in the body, still move a page', (t) => {
	const before = { '/signals/levels/': guide('/signals/levels/', { header: ['Version: phonometry 4.0.0', 'License: MIT'] }) };
	const header = { '/signals/levels/': guide('/signals/levels/', { header: ['Version: phonometry 4.0.0', 'License: BSD'] }) };
	assert.deepEqual(submit(t, before, header).urls, [url('/signals/levels/')]);
	const printing = (version) => ({
		'/signals/levels/': guide('/signals/levels/', {
			header: ['Version: phonometry 4.0.0', 'License: MIT'],
			body: `Text of /signals/levels/.\n\n\`\`\`text\nVersion: phonometry ${version}\n\`\`\`\n\nMore text.`,
		}),
	});
	assert.deepEqual(submit(t, printing('4.0.0'), printing('4.0.1')).urls, [url('/signals/levels/')]);
});

test('a new title, description or date moves a page whose copy did not change', (t) => {
	for (const change of [{ title: 'Levels, renamed' }, { description: 'A shorter description.' }, { lastmod: '2026-10-29' }]) {
		const after = { ...BASE, '/signals/levels/': guide('/signals/levels/', change) };
		assert.deepEqual(submit(t, BASE, after).urls, [url('/signals/levels/')], JSON.stringify(change));
	}
});

test('a landing page with no copy is read from its <main>, and its asset links do not move it', (t) => {
	const landing = (text) => ({ title: 'phonometry', description: 'The library.', lastmod: '2026-10-01', main: `<h1>phonometry</h1><p>${text}</p><script>let x = 1;</script>`, copy: null });
	const before = { ...BASE, '/': landing('1893 conformance checks') };
	const assets = submit(t, before, before, { head: '<link rel="stylesheet" href="/phonometry/_astro/index.C0ffee12.css">' });
	assert.deepEqual(assets.urls, []);
	const text = submit(t, before, { ...BASE, '/': landing('1900 conformance checks') });
	assert.deepEqual(text.urls, [url('/')]);
});

test('the build fails on a sitemap it cannot read every page of', (t) => {
	const cases = {
		'no <lastmod>': [{ ...BASE, '/signals/levels/': guide('/signals/levels/', { lastmod: '' }) }, /gives https:\S+\/signals\/levels\/ no <lastmod>/],
		'a copy the build should have written and did not': [
			{ ...BASE, '/x/': { ...guide('/x/'), copy: null } },
			/https:\S+\/x\/ has a Markdown copy by src\/lib\/page-markdown\.mjs, and the build wrote no \S+index\.md/,
		],
		'a landing page with no <main>': [
			{ ...BASE, '/': { ...guide('/'), copy: null, main: null } },
			/https:\S+\/phonometry\/ has no Markdown copy by src\/lib\/page-markdown\.mjs and no <main> element/,
		],
	};
	for (const [name, [pages, message]] of Object.entries(cases)) {
		const ran = run('manifest', build(t, pages));
		assert.equal(ran.status, 1, name);
		assert.match(ran.err, message, name);
	}
	const dist = build(t, BASE);
	rmSync(join(dist, 'signals', 'filters', 'index.html'));
	const missing = run('manifest', dist);
	assert.equal(missing.status, 1);
	assert.match(missing.err, /lists https:\S+\/signals\/filters\/, and the build wrote no/);
});

test('the deploy fails when a step after the manifest changed the pages it describes', (t) => {
	const dist = build(t, BASE);
	manifest(dist);
	writeFileSync(join(dist, 'signals', 'levels', 'index.md'), copy('/signals/levels/', 'Rewritten after the manifest.'));
	const ran = run('diff', '--dist', dist, '--previous', join(dist, 'none.json'));
	assert.equal(ran.status, 1);
	assert.match(ran.err, /is not the manifest the built pages give/);
});

test('the live manifest is read over HTTP, and a missing or failing one sends the full list', async (t) => {
	const pages = { [url('/a/')]: 'a'.repeat(64) };
	const server = createServer((request, response) => {
		if (request.url.startsWith('/ok')) {
			response.writeHead(200, { 'content-type': 'application/json' });
			response.end(serialize({ format: 1, pages }));
		} else if (request.url.startsWith('/error')) {
			response.writeHead(503);
			response.end('unavailable');
		} else {
			response.writeHead(404);
			response.end('<!DOCTYPE html><title>404</title>');
		}
	});
	await new Promise((done) => server.listen(0, '127.0.0.1', done));
	t.after(() => server.close());
	const base = `http://127.0.0.1:${server.address().port}`;
	assert.deepEqual((await loadPrevious(`${base}/ok?v=1`)).pages, pages);
	assert.equal((await loadPrevious(`${base}/missing?v=1`)).reason, 'the live site has none yet (404)');
	assert.equal((await loadPrevious(`${base}/error?v=1`)).reason, 'the live site answered 503');
	server.close();
	assert.match((await loadPrevious(`${base}/ok?v=2`)).reason, /it could not be fetched/);
	assert.equal(urlsToSubmit({ [url('/a/')]: 'b'.repeat(64) }, undefined).full, true);
});

test('only the header of a copy loses its release lines, in the shape of today and of a fuller header', () => {
	const today = copy('/x/', 'Body', ['Version: phonometry 4.0.0', 'Install: pip install phonometry']);
	assert.equal(withoutReleaseLines(today), copy('/x/', 'Body'));
	const fuller = [
		'# Octave filter banks',
		'',
		'> One page of the phonometry documentation, as Markdown.',
		'',
		`Canonical: ${url('/x/')}`,
		'Version: phonometry 4.0.0',
		'Install: pip install "phonometry[full]"',
		'Updated: 2026-10-20',
		'',
		'---',
		'',
		'Version: this line is content.',
	].join('\n');
	assert.equal(
		withoutReleaseLines(fuller),
		fuller.replace('Version: phonometry 4.0.0\n', '').replace('Install: pip install "phonometry[full]"\n', ''),
	);
	const noHeader = 'A paragraph.\nVersion: 4.0.0\n';
	assert.equal(withoutReleaseLines(noHeader), noHeader);
});
