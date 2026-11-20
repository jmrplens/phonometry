// The failures check-link-text.mjs exists to report, on builds small enough
// to read.
//
// The real build only ever hands the check pages that pass, so a check that
// read a word the browser does not show, held a link to the wrong language's
// list or stopped leaving out the links Lighthouse leaves out would stay green
// there for good. These tests serve builds of a few pages made for each case,
// run the check on them and read what it reports. The last one runs a full
// Lighthouse, the one PageSpeed Insights runs, on the same pages at both form
// factors and holds the check to what it finds.
//
// They drive Chrome, as the check does, so they need the browser the audits
// use: `pnpm exec puppeteer browsers install chrome`.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { after, before, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';

import lighthouse from 'lighthouse';
import desktopConfig from 'lighthouse/core/config/desktop-config.js';

import { pageRoutes, vagueLinks } from './check-link-text.mjs';
import { BASE_PATH, launchBrowser } from './shared/audit.mjs';

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-link-text.mjs');

/**
 * A built page of language `lang` (none when null) whose body carries the
 * given markup. It declares the viewport the site's pages declare: without it
 * a phone lays the page out 980 pixels wide and a narrow-screen rule never
 * applies.
 */
const page = (body, lang = 'en') =>
	`<!DOCTYPE html><html${lang ? ` lang="${lang}"` : ''}><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>A page</title></head><body><h1>A page</h1>${body}</body></html>`;

/** One of the stubs that send a retired address on, which no engine reads as a page. */
const STUB = '<!DOCTYPE html><title>Redirecting</title><meta http-equiv="refresh" content="0;url=/a/"><a href="/a/">here</a>';

/**
 * A build made of `files`, a map from a path under dist/ to the HTML it holds,
 * served under the site's base path the way the preview serves the real one.
 */
async function serve(files) {
	const root = mkdtempSync(join(tmpdir(), 'link-text-'));
	for (const [path, html] of Object.entries(files)) {
		const file = join(root, path);
		mkdirSync(dirname(file), { recursive: true });
		writeFileSync(file, html);
	}
	const server = createServer((request, response) => {
		const path = decodeURIComponent(new URL(request.url, 'http://build').pathname);
		let file = path.startsWith(`${BASE_PATH}/`) ? join(root, path.slice(BASE_PATH.length)) : null;
		if (file && existsSync(file) && statSync(file).isDirectory()) file = join(file, 'index.html');
		if (!file || !existsSync(file)) {
			response.writeHead(404, { 'content-type': 'text/html; charset=utf-8' });
			response.end(page('<p>Not here.</p>'));
			return;
		}
		response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
		response.end(readFileSync(file));
	});
	await new Promise((ready) => server.listen(0, '127.0.0.1', ready));
	const base = `http://127.0.0.1:${server.address().port}`;
	const close = async () => {
		await new Promise((closed) => server.close(closed));
		rmSync(root, { recursive: true, force: true });
	};
	return { root, base, close };
}

/** Run the check on a served build the way CI does, and return its exit status and everything it printed. */
async function run({ root, base }) {
	try {
		const { stdout, stderr } = await promisify(execFile)(process.execPath, [CHECK, '--base', base, root]);
		return { status: 0, output: `${stdout}${stderr}` };
	} catch (error) {
		return { status: error.code, output: `${error.stdout}${error.stderr}` };
	}
}

/** Each case page: the markup, and the links it must fail at each form factor as `href "text"`. */
const CASES = {
	// The text read is the text the browser shows.
	'shown/index.html': {
		lang: 'en',
		body: [
			'<style>@media (max-width: 600px) { .wide { display: none } }</style>',
			'<a href="/hidden/">More<span hidden> about sound levels</span></a>',
			'<a href="/narrow/">More <span class="wide">sound level guides</span></a>',
			'<a href="/svg-title/">More<svg viewBox="0 0 1 1" width="8" height="8"><title>about sound levels</title><rect width="1" height="1"/></svg></a>',
			'<a href="/across-tags/"><span>\n  Read\n  <em>more</em> </span></a>',
			'<a href="/start/">Start here</a>',
			'<a href="/named/">Read more about the A-weighting</a>',
		].join('\n'),
		mobile: ['/hidden/ "More"', '/narrow/ "More"', '/svg-title/ "More"', '/across-tags/ "Read more"'],
		desktop: ['/hidden/ "More"', '/svg-title/ "More"', '/across-tags/ "Read more"'],
	},
	// The text under the site's own `content-visibility: auto` rule, which
	// site/src/styles/containment.css sets on collapsible sections, is read
	// as the browser shows it once drawn, not as the empty text it has before.
	'collapsible/index.html': {
		lang: 'en',
		body: [
			'<style>.sl-markdown-content details { content-visibility: auto; contain-intrinsic-size: auto 2.5rem }</style>',
			'<div class="sl-markdown-content">',
			'<details open><summary>Sources</summary><p>See <a href="/sources/">here</a>.</p></details>',
			'<details><summary>Further reading, <a href="/reading/">more</a></summary><p>A list.</p></details>',
			'</div>',
		].join('\n'),
		mobile: ['/reading/ "more"', '/sources/ "here"'],
		desktop: ['/reading/ "more"', '/sources/ "here"'],
	},
	// Each link is held to the list of its own language, and to every list when it has none.
	'languages/index.html': {
		lang: 'en',
		body: '<a href="/german/" lang="de">mehr</a> <a href="/spanish-word/">aquí</a> <a href="/word/">Start</a>',
		mobile: ['/german/ "mehr"', '/word/ "Start"'],
		desktop: ['/german/ "mehr"', '/word/ "Start"'],
	},
	'es/idiomas/index.html': {
		lang: 'es',
		body: '<a href="/es/mas/">M&aacute;s</a> <a href="/es/start/">Inicio</a> <a href="/es/aqui/">aqu&#237;</a>',
		mobile: ['/es/aqui/ "aquí"', '/es/mas/ "Más"'],
		desktop: ['/es/aqui/ "aquí"', '/es/mas/ "Más"'],
	},
	'no-language/index.html': {
		lang: null,
		body: '<a href="/mehr/">mehr</a> <a href="/mais/">mais</a> <a href="/levels/">Sound levels</a>',
		mobile: ['/mais/ "mais"', '/mehr/ "mehr"'],
		desktop: ['/mais/ "mais"', '/mehr/ "mehr"'],
	},
	// The links Lighthouse leaves out.
	'left-out/index.html': {
		lang: 'en',
		body: [
			'<a>more</a>',
			'<a href="">more</a>',
			'<a href="#top">more</a>',
			'<a href="./#top">more</a>',
			`<a href="${BASE_PATH}/left-out/">more</a>`,
			'<a href="javascript:void(0)">more</a>',
			'<a href="mailto:someone@example.org">here</a>',
			'<a href="/b/" rel="external nofollow">here</a>',
			'<!-- <a href="/b/">here</a> -->',
			'<noscript><a href="/b/">here</a></noscript>',
		].join('\n'),
		mobile: [],
		desktop: [],
	},
};

const FILES = Object.fromEntries(Object.entries(CASES).map(([path, { lang, body }]) => [path, page(body, lang)]));
const routeOf = (path) => `/${path.replace(/index\.html$/, '')}`;

let build;
let found;
before(async () => {
	build = await serve({ ...FILES, 'old/index.html': STUB });
	found = await vagueLinks({ base: build.base, routes: pageRoutes(build.root) });
});
after(() => build.close());

/** What the check found on one route at one form factor, as `href "text"`. */
const foundOn = (route, form) =>
	found.filter((entry) => entry.route === route && entry.form === form).map(({ href, text }) => `${href} "${text}"`).sort();

for (const [path, expected] of Object.entries(CASES)) {
	test(`${routeOf(path)} fails the links it was made to fail, and no other`, () => {
		for (const form of ['mobile', 'desktop']) {
			assert.deepEqual(foundOn(routeOf(path), form), [...expected[form]].sort(), `${form} ${routeOf(path)}`);
		}
	});
}

test('every page loaded, and the redirect stub was not read', () => {
	assert.deepEqual(found.filter((entry) => entry.unread), []);
	assert.ok(!found.some((entry) => entry.route === '/old/'));
	assert.deepEqual(pageRoutes(build.root).sort(), Object.keys(CASES).map(routeOf).sort());
});

test('a page that does not load is reported, not passed', async () => {
	const missing = await vagueLinks({ base: build.base, routes: ['/missing/'], forms: ['mobile'] });
	assert.deepEqual(missing, [{ form: 'mobile', route: '/missing/', href: '', text: '', unread: 'HTTP 404' }]);
});

test('run as CI runs it, a link that reads "Start" fails at both form factors and "Start here" passes', async () => {
	const vague = await serve({ 'index.html': page('<a href="/start/">Start</a>'), 'old/index.html': STUB });
	try {
		const result = await run(vague);
		assert.equal(result.status, 1, result.output);
		assert.match(result.output, /read the links of 1 pages/);
		assert.match(result.output, /mobile \/: a link to \/start\/ reads "Start"/);
		assert.match(result.output, /desktop \/: a link to \/start\/ reads "Start"/);
	} finally {
		await vague.close();
	}
	const named = await serve({ 'index.html': page('<a href="/start/">Start here</a>') });
	try {
		const result = await run(named);
		assert.equal(result.status, 0, result.output);
		assert.match(result.output, /ok {3}every link names where it goes/);
	} finally {
		await named.close();
	}
});

test("the audit reads no event listeners, so the gatherer's session may answer those requests itself", () => {
	const require = createRequire(import.meta.url);
	const source = readFileSync(
		join(dirname(require.resolve('lighthouse/package.json')), 'core/audits/seo/link-text.js'),
		'utf8',
	);
	assert.match(source, /artifacts\.AnchorElements/, 'the audit no longer reads AnchorElements the way this test expects');
	assert.doesNotMatch(source, /listeners/);
});

test('the check finds what a full Lighthouse run finds, at both form factors', async () => {
	const browser = await launchBrowser();
	try {
		const tab = await browser.newPage();
		for (const path of Object.keys(CASES)) {
			const route = routeOf(path);
			for (const [form, config] of [['mobile', undefined], ['desktop', desktopConfig]]) {
				const result = await lighthouse(
					`${build.base}${BASE_PATH}${route}`,
					{ logLevel: 'error', onlyAudits: ['link-text'] },
					config,
					tab,
				);
				const audit = result.lhr.audits['link-text'];
				assert.equal(result.lhr.configSettings.formFactor, form);
				const items = (audit.details?.items ?? [])
					.map(({ href, text }) => `${href.startsWith(`${build.base}/`) ? href.slice(build.base.length) : href} "${text}"`)
					.sort();
				assert.deepEqual(foundOn(route, form), items, `${form} ${route}: the check and Lighthouse disagree`);
			}
		}
	} finally {
		await browser.close();
	}
});
