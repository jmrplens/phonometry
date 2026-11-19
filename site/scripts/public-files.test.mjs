// The hand-written files that name the site's own addresses, held to the
// target they are written for (src/data/site-targets.json).
//
// public/ is copied into dist/ verbatim, so nothing Astro does moves the
// addresses robots.txt, sitemap.xml and manifest.json write; site-origin.mjs
// moves only the origin of the first two, for a build made for another host.
// They are written for the build made with nothing set. .pa11yci.json lists
// the pages the accessibility audit opens on the local preview, which serves
// the build under its base path.
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { test } from 'node:test';

import { DEFAULT_SITE, SITE_TARGETS, basePath } from '../src/data/site.mjs';
import { englishTwin, isFallbackRoute } from '../src/lib/fallback-routes.mjs';

const { siteUrl: origin, basePath: base } = SITE_TARGETS[DEFAULT_SITE];
const read = (name) => readFileSync(new URL(`../${name}`, import.meta.url), 'utf8');
const exists = (name) => {
	try {
		readFileSync(new URL(`../public/${name}`, import.meta.url));
		return true;
	} catch {
		return false;
	}
};

test('robots.txt names the sitemap index of the site it is written for', () => {
	const sitemaps = read('public/robots.txt')
		.split('\n')
		.filter((line) => /^sitemap:/i.test(line));
	assert.deepEqual(sitemaps, [`Sitemap: ${origin}${base}/sitemap-index.xml`]);
});

test('sitemap.xml points at the shard of the site it is written for', () => {
	const locs = [...read('public/sitemap.xml').matchAll(/<loc>([^<]*)<\/loc>/g)].map((match) => match[1]);
	assert.deepEqual(locs, [`${origin}${base}/sitemap-0.xml`]);
});

test('manifest.json starts, scopes and finds its icons under the base path', () => {
	const manifest = JSON.parse(read('public/manifest.json'));
	assert.equal(manifest.start_url, `${base}/`);
	assert.equal(manifest.scope, `${base}/`);
	assert.ok(manifest.icons.length > 0);
	for (const { src } of manifest.icons) {
		assert.ok(src.startsWith(`${base}/`), `${src} is not under ${base}/`);
		assert.ok(exists(src.slice(base.length + 1)), `${src} names no file of public/`);
	}
});

// A route of the build is a page of src/content/docs, as a folder's index or a
// file of its own; a Spanish API route is served from its English entry.
const docs = new URL('../src/content/docs/', import.meta.url);
const isPage = (route) => {
	const entry = isFallbackRoute(route) ? englishTwin(route) : route;
	const names = entry === '' ? ['index'] : [`${entry}/index`, entry];
	return names.some((name) => ['md', 'mdx'].some((ext) => existsSync(new URL(`${name}.${ext}`, docs))));
};

test('every page the accessibility audit opens is a page the preview serves under its base path', () => {
	const { urls } = JSON.parse(read('.pa11yci.json'));
	const preview = `http://localhost:4321${basePath}/`;
	assert.ok(urls.length > 0);
	for (const url of urls) {
		assert.ok(url.startsWith(preview), `${url} is not under ${preview}`);
		const route = url.slice(preview.length).replace(/\/$/, '');
		assert.ok(isPage(route), `${url} names no page of src/content/docs`);
	}
});

test('a route names a page only without the base path, and a Spanish API route through its English entry', () => {
	assert.ok(isPage(''));
	assert.ok(isPage('start/getting-started'));
	assert.ok(isPage('es/reference/api/signals/levels'));
	assert.ok(!isPage('phonometry/start/getting-started'));
	assert.ok(!isPage('es/reference/api/no-such-page'));
});
