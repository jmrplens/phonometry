// What scripts/indexnow-diff.mjs tells IndexNow, on builds small enough to read.
//
// The script runs for real only on a deploy, after the merge, so nothing in a
// pull request would show that it sends the pages that changed and only
// those. The deploy used to send every URL of the sitemap, and a script that
// fell back to that on every run would still deploy green. Each test here
// writes a build of a few pages with a sitemap, a Markdown copy beside each
// page and the head an engine reads, runs the script on it the way the build
// and the deploy do, and reads what it would submit. The record it compares
// with is found through the GitHub API, which the tests stand in for.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { hasMarkdownCopy, releaseHeaderKeys, withheldRoutes, withoutReleaseLines } from '../src/lib/page-markdown.mjs';
import {
	DEPLOY_BRANCH,
	MANIFEST_NAME,
	ManifestError,
	NOT_DEPLOYED,
	ORIGIN,
	PAGES_ENVIRONMENT,
	SUBMITTED_ARTIFACT,
	URLS_NAME,
	lastSubmitted,
	loadPrevious,
	mainText,
	newerDeploy,
	serialize,
	urlsToSubmit,
} from './indexnow-diff.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const SCRIPT = join(HERE, 'indexnow-diff.mjs');

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
 * What the deploy of `pages` would submit after the IndexNow job that kept the
 * manifest of `before` (a list of pages, or `null` for no record at all), with
 * the lines the script printed and the folder it handed the IndexNow job.
 */
function submit(t, before, pages, options = {}) {
	const previous = join(mkdtempSync(join(tmpdir(), 'indexnow-previous-')), MANIFEST_NAME);
	t.after(() => rmSync(dirname(previous), { recursive: true, force: true }));
	if (before !== null) writeFileSync(previous, manifest(build(t, before)));
	const dist = build(t, pages, options);
	manifest(dist);
	const out = join(dirname(previous), 'handed');
	const ran = run('diff', '--dist', dist, '--previous', previous, '--out', out);
	assert.equal(ran.status, 0, ran.err);
	return { ...JSON.parse(readFileSync(join(out, URLS_NAME), 'utf8')), printed: ran.out, out, dist };
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

test('the IndexNow job is handed the manifest the URLs were worked out from, to keep once it has submitted them', (t) => {
	const after = { ...BASE, '/signals/filters/': guide('/signals/filters/', { body: 'The filters, rewritten.' }) };
	const sent = submit(t, BASE, after);
	assert.equal(readFileSync(join(sent.out, MANIFEST_NAME), 'utf8'), readFileSync(join(sent.dist, MANIFEST_NAME), 'utf8'));
});

test('a deploy whose IndexNow job kept no record leaves its pages to the next deploy, which compares with the record before it', (t) => {
	// The deploy of `failed` went live and its IndexNow job submitted nothing,
	// so the record is still the manifest of BASE.
	const failed = { ...BASE, '/signals/filters/': guide('/signals/filters/', { body: 'The filters, rewritten.' }) };
	const next = { ...failed, '/signals/levels/': guide('/signals/levels/', { body: 'The levels, rewritten.' }) };
	assert.deepEqual(submit(t, BASE, next).urls, [url('/signals/filters/'), url('/signals/levels/')]);
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
		const out = join(dir, `${name}.out`);
		const ran = run('diff', '--dist', dist, '--previous', previous, '--out', out);
		assert.equal(ran.status, 0, `${name}: ${ran.err}`);
		const sent = JSON.parse(readFileSync(join(out, URLS_NAME), 'utf8'));
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

test('a page that renders its data through a component is read from its <main>, whatever copy lies beside it', (t) => {
	// The rule is src/lib/page-markdown.mjs's, on the site's own tree: pages
	// such as the catalogues publish no copy, and the manifest reads what the
	// page shows instead, as it does on the landing pages.
	const tree = { contentDir: join(HERE, '..', 'src', 'content', 'docs'), docsDir: join(HERE, '..', '..', 'docs') };
	const route = [...withheldRoutes(tree)].find((name) => name !== '' && name !== 'es');
	assert.ok(route, 'the site has no page besides the landing pages that publishes no copy');
	assert.equal(hasMarkdownCopy(route), false);
	const at = `/${route}/`;
	const data = (row, stray = null) => ({ ...guide(at), main: `<h1>Data</h1><table><tr><td>${row}</td></tr></table>`, copy: stray });
	const before = { ...BASE, [at]: data('7850 kg/m3') };
	assert.deepEqual(submit(t, before, { ...BASE, [at]: data('7860 kg/m3') }).urls, [url(at)]);
	assert.deepEqual(submit(t, before, before, { head: '<link rel="stylesheet" href="/phonometry/_astro/index.C0ffee12.css">' }).urls, []);
	const stray = (text) => ({ ...BASE, [at]: data('7850 kg/m3', copy(at, text)) });
	assert.deepEqual(submit(t, stray('One copy.'), stray('Another copy.')).urls, []);
});

/**
 * The <main> of a catalogue page as the site builds it: the release banner,
 * the title, the page's content with a heading, a table and an entry with a
 * footer of its own, then Starlight's footer and the credit after it. Each
 * part can be swapped for another.
 */
const framed = ({
	banner = '<div class="sl-banner" data-pagefind-ignore><div class="notice">Pre-release.</div> This documentation describes <strong>version 4.0.0</strong>, which is not released yet.</div>',
	anchor = 'Section titled “Data”',
	updated = 'Nov 7, 2026',
	next = 'Damping materials',
	credit = 'All projects',
	cell = '7850 kg/m3',
	entry = 'Defined in: ISO 1683:2015',
	after = 'The values are those of the sources cited.',
} = {}) =>
	`${banner}<div class="content-panel"><div class="sl-container"><h1 id="_top">Data</h1></div></div>` +
	'<div class="content-panel"><div class="sl-container"><div class="sl-markdown-content">' +
	`<div class="sl-heading-wrapper"><h2 id="data">Data</h2><a class="sl-anchor-link" href="#data"><span aria-hidden="true"><svg><path d="M0 0"/></svg></span><span class="sr-only" data-pagefind-ignore>${anchor}</span></a></div>` +
	`<table><tr><th>Density</th></tr><tr><td>${cell}</td></tr></table>` +
	`<article><p>A term.</p><footer><span>${entry}</span> <a href="/phonometry/x/">A guide</a></footer></article><p>${after}</p></div>` +
	'<footer class="sl-flex"><div class="meta"><a href="https://github.com/jmrplens/phonometry/edit/main/site/x.mdx">Edit page</a>' +
	`<p>Published <time datetime="2026-10-28">Oct 28, 2026</time>, updated <time datetime="2026-11-07">${updated}</time></p></div>` +
	'<div class="pagination-links"><a href="/phonometry/prev/" rel="prev"><span>Previous</span> <span class="link-title">Overview</span></a>' +
	`<a href="/phonometry/next/" rel="next"><span>Next</span> <span class="link-title">${next}</span></a></div></footer>` +
	`<div class="maintainer"><span class="credit">Created and maintained by <a href="https://jmrp.io">José Manuel Requena Plens</a></span><span class="links"><a href="https://jmrp.io/projects/">${credit}</a></span></div>` +
	'</div></div>';

const textOf = (parts) => mainText(`<!DOCTYPE html><html><body><nav>Sidebar</nav><main data-pagefind-body>${framed(parts)}</main></body></html>`);

test("what the frame puts in a page's <main> does not move it, and the page's own text does", (t) => {
	// The release banner goes when a release is stamped, and the footer of a
	// page changes with the title of the page after it or one word of the
	// credit: none of that is what the page says. The entries of a page can
	// carry footers of their own, as the terms of the glossary do, and those,
	// like the cells of a table, are its text.
	const frame = {
		'the banner taken down': { banner: '' },
		'the banner reworded': {
			banner: '<div class="sl-banner" data-pagefind-ignore><div class="notice">Released.</div> This documentation describes <strong>version 4.0.1</strong>.</div>',
		},
		"a heading's anchor label": { anchor: 'Sección titulada «Data»' },
		'the date in the footer': { updated: 'Nov 9, 2026' },
		'the title of the next page': { next: 'Gases' },
		'the credit after the footer': { credit: 'All of my projects' },
	};
	for (const [what, parts] of Object.entries(frame)) assert.equal(textOf(parts), textOf(), what);
	const own = {
		'a cell of the table': { cell: '7860 kg/m3' },
		"the footer of one of the page's entries": { entry: 'Defined in: ISO 1683:2024' },
		'the text after that footer': { after: 'The values are those of the sources cited, rounded.' },
	};
	for (const [what, parts] of Object.entries(own)) assert.notEqual(textOf(parts), textOf(), what);
	assert.match(textOf(), /^Data Data Density 7850 kg\/m3 A term\. Defined in: ISO 1683:2015 A guide The values are those of the sources cited\.$/);

	// The same on a build: the manifest reads a page the site gives no copy
	// that way, so a deploy that changed only the frame submits nothing.
	const tree = { contentDir: join(HERE, '..', 'src', 'content', 'docs'), docsDir: join(HERE, '..', '..', 'docs') };
	const route = [...withheldRoutes(tree)].find((name) => name !== '' && name !== 'es');
	const at = `/${route}/`;
	const page = (parts) => ({ ...guide(at), main: framed(parts), copy: null });
	const before = { ...BASE, [at]: page() };
	const reframed = { banner: '', anchor: 'Sección titulada «Data»', updated: 'Nov 9, 2026', next: 'Gases', credit: 'All of my projects' };
	assert.deepEqual(submit(t, before, { ...BASE, [at]: page(reframed) }).urls, []);
	assert.deepEqual(submit(t, before, { ...BASE, [at]: page({ ...reframed, cell: '7860 kg/m3' }) }).urls, [url(at)]);
});

test('an element marked data-pagefind-ignore goes with all it nests, and one left open fails the build', () => {
	const text = (main) => mainText(`<main>${main}</main>`);
	assert.equal(text('<div data-pagefind-ignore><div>In</div> still in <div><div>deep</div></div></div><p>Out</p>'), 'Out');
	assert.equal(text('<p>Before <img data-pagefind-ignore src="x.png" alt="x"> after</p>'), 'Before after');
	assert.equal(text('<p title="data-pagefind-ignore">Kept</p>'), 'Kept');
	assert.throws(() => text('<p>Before</p><div data-pagefind-ignore>never closed <div>in</div>'), (error) => error instanceof ManifestError && /never closed/.test(error.message));
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

test('a previous manifest named by its URL is read over HTTP, and a missing or failing one sends the full list', async (t) => {
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

/** An artifact as the GitHub API lists one, kept by a run of main of this repository unless `run` says otherwise. */
const artifact = (id, createdAt, run = {}) => ({
	id,
	name: SUBMITTED_ARTIFACT,
	expired: false,
	created_at: createdAt,
	workflow_run: { id: id * 10, repository_id: 1, head_repository_id: 1, head_branch: DEPLOY_BRANCH, head_sha: `c0ffee${id}`, ...run },
});

test('the record compared with is the newest one a run of main kept, in whatever order the API lists them', () => {
	const older = artifact(1, '2026-11-01T10:00:00Z');
	const newest = artifact(2, '2026-11-03T10:00:00Z');
	const middle = artifact(3, '2026-11-02T10:00:00Z');
	for (const order of [[older, newest, middle], [newest, middle, older], [middle, older, newest]]) {
		assert.equal(lastSubmitted(order), newest);
	}
	const later = '2026-11-05T10:00:00Z';
	const never = {
		'a pull request': artifact(4, later, { head_branch: 'site/a-change' }),
		'a fork, from its own main': artifact(5, later, { head_repository_id: 2 }),
		'an expired record': { ...artifact(6, later), expired: true },
		'another artifact': { ...artifact(7, later), name: 'indexnow-urls' },
		'an artifact of no run': { ...artifact(8, later), workflow_run: null },
	};
	for (const [what, stranger] of Object.entries(never)) assert.equal(lastSubmitted([older, stranger, newest]), newest, what);
	const sameSecond = artifact(9, newest.created_at);
	assert.equal(lastSubmitted([sameSecond, newest]), sameSecond);
	assert.equal(lastSubmitted([newest, sameSecond]), sameSecond);
	assert.equal(lastSubmitted(Object.values(never)), undefined);
});

/** A deployment of the site as the GitHub GraphQL API lists one. */
const deployment = (databaseId, createdAt, state = 'ACTIVE') => ({ databaseId, createdAt, commitOid: `c0ffee${databaseId}`, state });

/**
 * The site, its deploys and the IndexNow jobs that follow them, played in the
 * order a test gives. A deploy builds against the newest record of its time
 * and goes out; the job of a run, when it runs, submits that run's list and
 * keeps its manifest when `keeps(run, { records, deployments })` says so.
 */
function site(keeps) {
	const records = [];
	const manifests = new Map();
	const deployments = [];
	const runs = new Map();
	let clock = Date.parse('2026-11-01T10:00:00Z');
	const tick = () => new Date((clock += 60_000)).toISOString().replace('.000Z', 'Z');
	return {
		/** Run `name` builds `pages` and deploys them, and says what its list holds. */
		deploy(name, pages) {
			const compared = lastSubmitted(records);
			deployments.push(deployment(deployments.length + 1, tick()));
			const sent = urlsToSubmit(pages, compared && manifests.get(compared.id));
			runs.set(name, { pages, compared: compared?.id ?? null, deployedAt: tick() });
			return sent;
		},
		/** The IndexNow job of run `name`, run for the first time or re-run: whether it kept its manifest. */
		job(name) {
			const run = runs.get(name);
			if (!keeps(run, { records, deployments })) return false;
			const id = records.length + 1;
			records.push(artifact(id, tick()));
			manifests.set(id, run.pages);
			return true;
		},
	};
}

/** The job keeps its manifest while no deploy has gone out after its run's, as the IndexNow job does. */
const byDeploy = (run, { deployments }) => newerDeploy(run.deployedAt, deployments) === undefined;
/** The job keeps its manifest whatever happened since. */
const always = () => true;
/** The job keeps its manifest while the record its build compared with is the newest. */
const byRecord = (run, { records }) => (lastSubmitted(records)?.id ?? null) === run.compared;

/**
 * What the deploy that removes page y sends as removed, after run A changed
 * page x and run B added y, both with jobs that failed, and the jobs played
 * in `order` (A's and B's, first runs or re-runs).
 */
function removedAfter(keeps, order) {
	const x = url('/x/');
	const y = url('/y/');
	const played = site(keeps);
	played.deploy('R', { [x]: 'x0' });
	played.job('R');
	played.deploy('A', { [x]: 'x1' });
	played.deploy('B', { [x]: 'x1', [y]: 'y1' });
	for (const name of order) played.job(name);
	return played.deploy('C', { [x]: 'x1' }).removed;
}

test('the newest record is the newest deploy that kept one, in whatever order failed jobs are re-run', () => {
	const y = url('/y/');
	const orders = {
		"B's job keeps its record, then A's is re-run": ['B', 'A'],
		"A's job is re-run, then B's": ['A', 'B'],
	};
	for (const [what, order] of Object.entries(orders)) {
		assert.deepEqual(removedAfter(byDeploy, order), [y], what);
	}
	// A rule decided by when a record was kept leaves the removal of y out in
	// one of the two orders: keeping always when A's job runs last, keeping
	// while the record its build compared with is the newest when B's does.
	assert.deepEqual(removedAfter(always, ['A', 'B']), [y]);
	assert.deepEqual(removedAfter(always, ['B', 'A']), []);
	assert.deepEqual(removedAfter(byRecord, ['B', 'A']), [y]);
	assert.deepEqual(removedAfter(byRecord, ['A', 'B']), []);

	// A's job re-run after B's deploy keeps nothing, whatever B's job does
	// later, so the next deploy compares with the record both builds compared
	// with and sends A's page again.
	const x = url('/x/');
	const played = site(byDeploy);
	played.deploy('R', { [x]: 'x0' });
	played.job('R');
	played.deploy('A', { [x]: 'x1' });
	played.deploy('B', { [x]: 'x1', [y]: 'y1' });
	assert.equal(played.job('A'), false);
	assert.deepEqual(played.deploy('C', { [x]: 'x1' }).changed, [x]);
});

test("a deploy that went out after this run's, and only such a deploy, stops the record from being kept", () => {
	const at = '2026-11-06T08:00:00Z';
	const own = deployment(1, '2026-11-06T07:59:30Z');
	const later = '2026-11-08T08:00:00Z';
	assert.equal(newerDeploy(at, []), undefined, 'no deployment listed');
	assert.equal(newerDeploy(at, [own, deployment(0, '2026-11-01T08:00:00Z')]), undefined, "this run's own deployment and an older one");
	assert.equal(newerDeploy(at, [own, deployment(2, at)]), undefined, 'one made in the second the pages went out is not after them');
	for (const state of ['ACTIVE', 'INACTIVE', 'IN_PROGRESS', 'QUEUED', 'PENDING', 'WAITING', 'SUCCESS', null]) {
		const newer = deployment(3, later, state);
		assert.equal(newerDeploy(at, [own, newer]), newer, `a later deploy whose state is ${state}`);
	}
	for (const state of NOT_DEPLOYED) {
		assert.equal(newerDeploy(at, [own, deployment(3, later, state)]), undefined, `a later deploy that ended ${state}, whose pages never went out`);
	}
	const unreadable = deployment(4, 'soon');
	assert.equal(newerDeploy(at, [own, unreadable]), unreadable, 'one made at a moment that cannot be read counts');
	const first = deployment(5, '2026-11-07T08:00:00Z');
	const second = deployment(6, later);
	for (const order of [[first, second, own], [own, second, first]]) assert.equal(newerDeploy(at, order), second, 'the newest of two');
	// A whole run re-run after them deploys again, and its pages are the newest.
	assert.equal(newerDeploy('2026-11-09T08:00:30Z', [own, first, second, deployment(7, '2026-11-09T08:00:00Z')]), undefined);
});

/**
 * Run the script's `command` against a GitHub API that answers each page of
 * a listing with `pages[page - 1]` (or 503 when `pages` is `'fail'`), and say
 * what it fetched, printed and wrote to the step output. A REST listing names
 * its page in the URL; a GraphQL one names the page after the cursor `pN`, and
 * page 1 when there is none.
 */
function againstApi(t, pages, command, env = {}) {
	const dir = mkdtempSync(join(tmpdir(), 'indexnow-api-'));
	t.after(() => rmSync(dir, { recursive: true, force: true }));
	const answers = join(dir, 'pages.json');
	writeFileSync(answers, JSON.stringify(pages));
	const output = join(dir, 'output');
	// The script's fetch, swapped before it loads for one that writes down
	// what it was asked and answers from `pages`, so the test needs no
	// network.
	const stub = [
		"import { readFileSync } from 'node:fs';",
		`const pages = JSON.parse(readFileSync(${JSON.stringify(answers)}, 'utf8'));`,
		'globalThis.fetch = async (url, init) => {',
		'  const asked = init.body === undefined ? undefined : JSON.parse(init.body).variables;',
		'  const about = asked === undefined ? "" : ` for ${asked.owner}/${asked.name} in ${asked.environment} after ${asked.after}`;',
		'  process.stderr.write(`fetched ${url} with ${init.headers.authorization}${about}\\n`);',
		"  if (pages === 'fail') return new Response('unavailable', { status: 503 });",
		"  const page = asked === undefined ? Number(new URL(url).searchParams.get('page')) : asked.after === null ? 1 : Number(asked.after.slice(1));",
		'  return new Response(JSON.stringify(pages[page - 1]), { status: 200 });',
		'};',
	].join('\n');
	const ran = spawnSync(process.execPath, ['--import', `data:text/javascript,${encodeURIComponent(stub)}`, SCRIPT, ...command], {
		encoding: 'utf8',
		env: {
			...process.env,
			GITHUB_API_URL: 'https://api.github.example',
			GITHUB_GRAPHQL_URL: 'https://api.github.example/graphql',
			GITHUB_REPOSITORY: 'jmrplens/phonometry',
			GITHUB_TOKEN: 't0ken',
			GITHUB_OUTPUT: output,
			...env,
		},
	});
	return {
		status: ran.status,
		fetched: ran.stderr.match(/^fetched .*$/gm) ?? [],
		err: ran.stderr,
		out: ran.stdout,
		output: existsSync(output) ? readFileSync(output, 'utf8') : '',
	};
}

/** Run `last-submitted` against `pages` of the API. */
const lastSubmittedAgainst = (t, pages, env = {}) => againstApi(t, pages, ['last-submitted'], env);

const listing = (page) =>
	`fetched https://api.github.example/repos/jmrplens/phonometry/actions/artifacts?name=${SUBMITTED_ARTIFACT}&per_page=100&page=${page} with Bearer t0ken`;

test('the run of the newest record is read from every page the API lists, for the workflow to download it from', (t) => {
	const first = Array.from({ length: 100 }, (_, index) => artifact(100 + index, `2026-10-${String(1 + (index % 28)).padStart(2, '0')}T08:00:00Z`));
	first[50] = artifact(50, '2026-11-07T08:00:00Z', { head_branch: 'site/a-change' });
	const newest = artifact(7, '2026-11-06T08:00:00Z');
	const pages = [
		{ total_count: 102, artifacts: first },
		{ total_count: 102, artifacts: [newest, artifact(8, '2026-10-30T08:00:00Z')] },
	];
	const found = lastSubmittedAgainst(t, pages);
	assert.equal(found.status, 0, found.err);
	assert.deepEqual(found.fetched, [listing(1), listing(2)]);
	assert.equal(found.output, 'run-id=70\n');
	assert.match(found.out, /last submitted by run 70, of commit c0ffee7, on 2026-11-06T08:00:00Z/);
});

test('with no record to find, or no API to ask, the build goes on and the full list goes out', (t) => {
	const none = lastSubmittedAgainst(t, [{ total_count: 1, artifacts: [artifact(4, '2026-11-05T10:00:00Z', { head_branch: 'site/a-change' })] }]);
	assert.equal(none.status, 0, none.err);
	assert.equal(none.output, '');
	assert.match(none.out, new RegExp(`no IndexNow job of a run of ${DEPLOY_BRANCH} has kept a record .* the full list goes out`));
	const failing = lastSubmittedAgainst(t, 'fail');
	assert.equal(failing.status, 0, failing.err);
	assert.equal(failing.output, '');
	assert.match(failing.out, /^::warning::.*answered 503.*the full list goes out/m);
	const outside = lastSubmittedAgainst(t, [], { GITHUB_TOKEN: '' });
	assert.equal(outside.status, 1);
	assert.match(outside.err, /needs GITHUB_REPOSITORY, GITHUB_TOKEN and GITHUB_OUTPUT/);
});

/** Run `keep-record` for pages that went out at `deployedAt` (none given when undefined), against `pages` of the API. */
const keepRecordAgainst = (t, pages, deployedAt, env = {}) =>
	againstApi(t, pages, ['keep-record', ...(deployedAt === undefined ? [] : ['--deployed-at', deployedAt])], env);

/** A page of deployments as the GraphQL API answers one, with the cursor of the next when there is one. */
const deploymentsPage = (nodes, next = null) => ({ data: { repository: { deployments: { pageInfo: { hasNextPage: next !== null, endCursor: next }, nodes } } } });

/** The line the stub writes for a request of the deployments after the cursor `after`. */
const asked = (after) =>
	`fetched https://api.github.example/graphql with Bearer t0ken for jmrplens/phonometry in ${PAGES_ENVIRONMENT} after ${after}`;

test("the IndexNow job keeps its manifest only while no deploy has gone out after its run's", (t) => {
	const at = '2026-11-06T08:00:00Z';
	const own = deployment(7, '2026-11-06T07:59:30Z');
	const older = deployment(6, '2026-11-01T08:00:00Z');
	// The listing comes newest first, so it is read only down to this run's deployment.
	const kept = keepRecordAgainst(t, [deploymentsPage([own, older], 'p2')], at);
	assert.equal(kept.status, 0, kept.err);
	assert.deepEqual(kept.fetched, [asked(null)]);
	assert.equal(kept.output, 'keep=true\n');
	assert.match(kept.out, /no deploy has gone out since this run's on 2026-11-06T08:00:00Z: this manifest is kept/);

	// A failed job re-run after a newer deploy went out.
	const newer = deployment(9, '2026-11-08T08:00:00Z', 'INACTIVE');
	const stale = keepRecordAgainst(t, [deploymentsPage([deployment(10, '2026-11-09T08:00:00Z', 'FAILURE'), newer, own])], at);
	assert.equal(stale.status, 0, stale.err);
	assert.equal(stale.output, 'keep=false\n');
	assert.match(stale.out, /deployment 9, of commit c0ffee9, was made on 2026-11-08T08:00:00Z, after this run's pages went out on 2026-11-06T08:00:00Z: this manifest is not kept/);

	// A deploy that failed after this one, on as many pages as it takes.
	const failed = deployment(8, '2026-11-07T08:00:00Z', 'FAILURE');
	const paged = keepRecordAgainst(t, [deploymentsPage([failed], 'p2'), deploymentsPage([own, older])], at);
	assert.equal(paged.status, 0, paged.err);
	assert.deepEqual(paged.fetched, [asked(null), asked('p2')]);
	assert.equal(paged.output, 'keep=true\n');
});

test('a manifest whose deploy cannot be placed among the others is not kept, so the next deploy sends these pages again', (t) => {
	const at = '2026-11-06T08:00:00Z';
	const failing = keepRecordAgainst(t, 'fail', at);
	assert.equal(failing.status, 0, failing.err);
	assert.equal(failing.output, 'keep=false\n');
	assert.match(failing.out, /^::warning::.*answered 503.*this manifest is not kept/m);
	const refused = keepRecordAgainst(t, [{ errors: [{ message: 'Resource not accessible by integration' }] }], at);
	assert.equal(refused.status, 0, refused.err);
	assert.equal(refused.output, 'keep=false\n');
	assert.match(refused.out, /^::warning::.*Resource not accessible by integration.*this manifest is not kept/m);
	const unnamed = keepRecordAgainst(t, [], '');
	assert.equal(unnamed.status, 0, unnamed.err);
	assert.deepEqual(unnamed.fetched, []);
	assert.equal(unnamed.output, 'keep=false\n');
	assert.match(unnamed.out, /^::warning::.*named no time its pages went out/m);
	const malformed = keepRecordAgainst(t, [], '2026-11-06 08:00');
	assert.equal(malformed.status, 1);
	assert.match(malformed.err, /--deployed-at takes the moment the pages went out, as 2026-11-10T08:00:00Z, not "2026-11-06 08:00"/);
	const outside = keepRecordAgainst(t, [], at, { GITHUB_TOKEN: '' });
	assert.equal(outside.status, 1);
	assert.match(outside.err, /keep-record .* needs GITHUB_REPOSITORY, GITHUB_TOKEN and GITHUB_OUTPUT/);
});

// ---------------------------------------------------------------------------
// A deploy job re-run after a newer deploy
// ---------------------------------------------------------------------------

/**
 * The sequence, through the CLI. The record holds BASE, with z and without
 * y. Run A builds BASE again, so its list is empty, and its deploy fails.
 * Run B changes x, adds y and drops z, deploys, submits and keeps its
 * record. A's failed jobs are re-run: the deploy puts A's pages back, x as
 * the record had it, z back and y gone, after B's deploy. The list A's
 * build handed on still says nothing changed, so the IndexNow job of the
 * re-run works it out again against the newest record, B's, and keeps A's
 * manifest, which the site now serves.
 */
test('a deploy job re-run after a newer deploy works its list out again against the newest record, and sends what its pages put back', (t) => {
	const x = url('/signals/filters/');
	const y = url('/signals/weighting/');
	const z = url('/es/signals/levels/');
	const { '/es/signals/levels/': _dropped, ...withoutZ } = BASE;
	const bPages = { ...withoutZ, '/signals/filters/': guide('/signals/filters/', { body: 'The filters, rewritten.' }), '/signals/weighting/': guide('/signals/weighting/') };
	const a = submit(t, BASE, BASE);
	assert.deepEqual(a.urls, []);
	const handedManifest = readFileSync(join(a.out, MANIFEST_NAME), 'utf8');
	const b = submit(t, BASE, bPages);
	assert.deepEqual(b.urls, [z, x, y]);

	// The job of the re-run finds B's record, the newest.
	const found = lastSubmittedAgainst(t, [{ total_count: 2, artifacts: [artifact(1, '2026-11-10T09:00:00Z'), artifact(2, '2026-11-10T11:31:00Z')] }]);
	assert.equal(found.status, 0, found.err);
	assert.equal(found.output, 'run-id=20\n');

	// It compares the manifest A's build handed on with B's record, and writes
	// the list it submits over the one it was handed.
	const again = run('diff', '--current', join(a.out, MANIFEST_NAME), '--previous', join(b.out, MANIFEST_NAME), '--out', a.out);
	assert.equal(again.status, 0, again.err);
	const sent = JSON.parse(readFileSync(join(a.out, URLS_NAME), 'utf8'));
	assert.deepEqual(sent.changed, [x]);
	assert.deepEqual(sent.new, [z]);
	assert.deepEqual(sent.removed, [y]);
	assert.deepEqual(sent.urls, [z, x, y]);
	assert.match(again.out, /1 changed, 1 new and 1 removed of 3 pages: 3 URLs to submit/);
	assert.equal(readFileSync(join(a.out, MANIFEST_NAME), 'utf8'), handedManifest, 'the manifest the job keeps is the one the build handed on');

	// The re-run's deploy is the newest, so the job keeps A's manifest.
	const rerun = { databaseId: 13, createdAt: '2026-11-10T12:00:00Z', commitOid: 'a0', state: 'ACTIVE' };
	const ofB = { databaseId: 12, createdAt: '2026-11-10T11:20:00Z', commitOid: 'b0', state: 'INACTIVE' };
	const failed = { databaseId: 11, createdAt: '2026-11-10T10:10:00Z', commitOid: 'a0', state: 'FAILURE' };
	const kept = keepRecordAgainst(t, [deploymentsPage([rerun, ofB, failed])], '2026-11-10T12:01:00Z');
	assert.equal(kept.output, 'keep=true\n');

	// The next deploy compares with A's record: BASE again sends nothing, B's
	// pages again send x, y and z.
	assert.deepEqual(submit(t, BASE, BASE).urls, []);
	assert.deepEqual(submit(t, BASE, bPages).urls, [z, x, y]);
});

test('the manifest a build handed IndexNow is compared as it is, and one that cannot be read stops the job', (t) => {
	const retitled = { ...BASE, '/signals/filters/': guide('/signals/filters/', { title: 'Filter banks' }) };
	const handedOn = submit(t, BASE, retitled);
	const record = join(dirname(handedOn.out), 'record.json');
	writeFileSync(record, manifest(build(t, BASE)));
	const out = join(dirname(handedOn.out), 'again');
	const same = run('diff', '--current', join(handedOn.out, MANIFEST_NAME), '--previous', record, '--out', out);
	assert.equal(same.status, 0, same.err);
	assert.deepEqual(JSON.parse(readFileSync(join(out, URLS_NAME), 'utf8')).urls, handedOn.urls);
	assert.equal(readFileSync(join(out, MANIFEST_NAME), 'utf8'), readFileSync(join(handedOn.out, MANIFEST_NAME), 'utf8'));
	const notJson = join(dirname(handedOn.out), 'not-json.json');
	writeFileSync(notJson, '{"format": 1, "pages": {');
	for (const [what, current, pattern] of [
		['no such file', join(dirname(handedOn.out), 'missing.json'), /the manifest to compare, .*missing\.json, cannot be read \(ENOENT\)/],
		['not JSON', notJson, /the manifest to compare, .*not-json\.json, cannot be compared: it is not JSON/],
	]) {
		const refused = run('diff', '--current', current, '--previous', record, '--out', join(dirname(handedOn.out), 'refused'));
		assert.equal(refused.status, 1, what);
		assert.match(refused.err, pattern, what);
	}
	const both = run('diff', '--current', join(handedOn.out, MANIFEST_NAME), '--dist', handedOn.dist, '--previous', record);
	assert.equal(both.status, 1);
	assert.match(both.err, /--dist or --current, not both/);
});
