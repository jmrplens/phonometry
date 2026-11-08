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
	ORIGIN,
	SUBMITTED_ARTIFACT,
	URLS_NAME,
	lastSubmitted,
	loadPrevious,
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

/**
 * Run `last-submitted` against a GitHub API that answers each page of the
 * listing with `pages[page - 1]` (or 503 when `pages` is `'fail'`), and say
 * what it fetched, printed and wrote to the step output.
 */
function lastSubmittedAgainst(t, pages, env = {}) {
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
		'  process.stderr.write(`fetched ${url} with ${init.headers.authorization}\\n`);',
		"  if (pages === 'fail') return new Response('unavailable', { status: 503 });",
		"  const page = Number(new URL(url).searchParams.get('page'));",
		'  return new Response(JSON.stringify(pages[page - 1]), { status: 200 });',
		'};',
	].join('\n');
	const ran = spawnSync(process.execPath, ['--import', `data:text/javascript,${encodeURIComponent(stub)}`, SCRIPT, 'last-submitted'], {
		encoding: 'utf8',
		env: {
			...process.env,
			GITHUB_API_URL: 'https://api.github.example',
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
