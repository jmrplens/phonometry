// The retired addresses as Cloudflare Bulk Redirects list items.
//
// A static host can only answer a retired address with the stub page Astro
// writes for it, a 200 carrying a meta refresh. Search engines ask for a
// server-side permanent redirect wherever one is possible: Google treats an
// instant meta refresh as the fallback ("Redirects and Google Search"), and
// Bing's Webmaster Guidelines say "Use 301 redirects for permanent URL
// changes". phonometry.dev answers them from the `_redirects` file the
// Worker's staging writes from the pairs below (site/worker/lib/redirects.mjs).
// docs.jmrp.io, where the site was published under /phonometry before it
// moved to the root of phonometry.dev, is proxied by Cloudflare and answers
// from account-level Bulk Redirects lists: `--legacy` prints the one that
// sends every address the old site retired, and every page it served, written
// without its trailing slash, straight to the page here (CONTRIBUTING.md, 5b).
// The stubs stay in the build as the answer for a host with neither.
//
// Each address is listed with and without its trailing slash, so neither form
// takes a second hop through GitHub's own slash redirect. The query string is
// kept and nothing else is matched: no subdomains, no subpaths.
//
// Two more kinds of address are agents' rather than readers', and have no
// stub to fall back on. Every page publishes its Markdown copy at
// `<page>/index.md`, and a retired page's copy answered 404 while the page
// itself answered 301: crawlers asked for those copies after the pages moved.
// So each retired address gets a second item, its `index.md` to the copy of
// the page it moved to; every page but the 404 page has one, and a Spanish
// API page, served from the English entry, has its English twin's. And the llms
// shard names that were retired before the generator kept every name it
// publishes (src/data/llms-shards.json, `redirects`) answer with the file
// that now carries their first page. Matching a subpath instead would cover
// the copies too, but it changes which item wins where one retired address
// sits under another, so they are listed one by one.
//
// Usage: node scripts/cloudflare-redirects.mjs > items.json
//        node scripts/cloudflare-redirects.mjs --legacy [--dist dist] > items.json
// The output is the JSON array the list items endpoint takes; CONTRIBUTING.md
// says how to load a list with it. `--legacy` reads the pages from the
// sitemap of the build in dist/. No credential is read or needed here.
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

import { redirects } from '../src/data/redirects.mjs';
import { LEGACY_ORIGINS, basePath, siteUrl } from '../src/data/site.mjs';
import { englishTwin, isFallbackRoute } from '../src/lib/fallback-routes.mjs';

/** Where the record of the llms shard names lives (scripts/generate_llms.py `SHARD_NAMES`). */
export const SHARD_NAMES = new URL('../src/data/llms-shards.json', import.meta.url);

/**
 * The retired llms shard names and the name each redirects to.
 *
 * @param {URL | string} [file]
 * @returns {Record<string, string>}
 */
export function retiredShards(file = SHARD_NAMES) {
	const record = JSON.parse(readFileSync(file, 'utf8'));
	const map = record?.redirects;
	if (typeof map !== 'object' || map === null || Array.isArray(map)) {
		throw new Error(`${file}: no "redirects" object of retired shard name to current name`);
	}
	for (const [from, to] of Object.entries(map)) {
		if (typeof to !== 'string' || !/^[a-z0-9-]+$/u.test(from) || !/^[a-z0-9-]+$/u.test(to)) {
			throw new Error(`${file}: the redirect ${JSON.stringify(from)} -> ${JSON.stringify(to)} is no pair of shard names`);
		}
	}
	return map;
}

/** The site this build is made for: where every retired address now answers. */
const CURRENT = Object.freeze({ siteUrl, basePath });

/**
 * The Markdown copy of the page at *to*, a destination with the base path. A
 * Spanish API page is the English entry served again (src/lib/fallback-routes.mjs)
 * and has no copy of its own, so its English twin's copy stands for it.
 *
 * @param {string} to
 * @param {string} [base] The base path *to* carries; the build's by default.
 * @returns {string} The copy's path, with the base path.
 */
export function copyOf(to, base = basePath) {
	return `${isFallbackRoute(to, base) ? englishTwin(to, base) : to}index.md`;
}

/**
 * Every retired address and where it answers, as absolute sources without
 * the scheme (what a list item matches) and absolute targets.
 *
 * The sources are the old addresses on the site that published them, and the
 * targets the pages that replace them on the site they are served from now.
 * By default both are this build's site; with a legacy origin
 * (src/data/site.mjs `LEGACY_ORIGINS`) as *source*, each address the old site
 * retired goes straight to its final page on the current one, in one hop.
 *
 * @param {Record<string, string>} map Old address without the base path ->
 *   destination with the target's base path, as src/data/redirects.mjs exports them.
 * @param {Record<string, string>} shards Retired shard name -> current name.
 * @param {object} [sites]
 * @param {{siteUrl: string, basePath: string}} [sites.target] Where the pages answer now.
 * @param {{siteUrl: string, basePath: string}} [sites.source] Where the old addresses were published.
 * @returns {Map<string, string>} Source URL -> target URL, in the order listed.
 */
export function retiredAddresses(map = redirects, shards = retiredShards(), { target = CURRENT, source = target } = {}) {
	const host = new URL(source.siteUrl).host;
	const old = `${host}${source.basePath}`;
	/** @type {Map<string, string>} */
	const addresses = new Map();
	const add = (from, to) => {
		if (addresses.has(from)) throw new Error(`${from} is retired twice`);
		addresses.set(from, to);
	};
	for (const [from, to] of Object.entries(map)) {
		const answer = `${target.siteUrl}${to}`;
		add(`${old}${from}`, answer);
		if (from.endsWith('/') && from.length > 1) add(`${old}${from.slice(0, -1)}`, answer);
	}
	for (const [from, to] of Object.entries(map)) {
		if (!from.endsWith('/') || !to.endsWith('/')) continue;
		add(`${old}${from}index.md`, `${target.siteUrl}${copyOf(to, target.basePath)}`);
	}
	for (const [from, to] of Object.entries(shards)) {
		add(`${old}/llms/llms-${from}.txt`, `${target.siteUrl}${target.basePath}/llms/llms-${to}.txt`);
	}
	return addresses;
}

/**
 * Every retired address as a path, with the path it now answers at.
 *
 * The same addresses as the list items below, read without the host: the
 * `_redirects` file of phonometry.dev (site/worker/lib/redirects.mjs)
 * is written from these, so the two edges cannot drift apart.
 *
 * @param {Record<string, string>} [map] Old address without the base path ->
 *   destination with it, as src/data/redirects.mjs exports them.
 * @param {Record<string, string>} [shards] Retired shard name -> current name.
 * @returns {{from: string, to: string}[]} One pair per source path, in the order listed.
 */
export function redirectPairs(map = redirects, shards = retiredShards()) {
	const host = new URL(siteUrl).host;
	return [...retiredAddresses(map, shards)].map(([source, target]) => {
		if (!source.startsWith(`${host}/`) || !target.startsWith(`${siteUrl}/`)) {
			throw new Error(`${source} -> ${target} is not on ${siteUrl}`);
		}
		return { from: source.slice(host.length), to: target.slice(siteUrl.length) };
	});
}

/**
 * The list items for a redirect map.
 *
 * @param {Record<string, string>} [map] Old address without the base path ->
 *   destination with the target's base path, as src/data/redirects.mjs exports them.
 * @param {Record<string, string>} [shards] Retired shard name -> current name.
 * @param {object} [sites] The target and source sites, as retiredAddresses takes them.
 * @returns {object[]} One item per source URL: two per address that ends in a
 *   slash, one for its Markdown copy, and one per retired shard name.
 */
export function cloudflareItems(map = redirects, shards = retiredShards(), sites = {}) {
	return [...retiredAddresses(map, shards, sites)].map(([source, target]) => listItem(source, target));
}

/**
 * One list item: a 301 from exactly *source* to *target*, the query kept.
 *
 * @param {string} source The address matched, without the scheme.
 * @param {string} target The absolute address answered.
 * @returns {object} The item, as the list items endpoint takes it.
 */
function listItem(source, target) {
	return {
		redirect: {
			source_url: source,
			target_url: target,
			status_code: 301,
			preserve_query_string: true,
			include_subdomains: false,
			subpath_matching: false,
			preserve_path_suffix: false,
		},
	};
}

/**
 * The list items that send each address a legacy origin retired straight to
 * its page on the current site: the sources on the old host under its old
 * base path, the targets where the pages answer now.
 *
 * @param {{siteUrl: string, basePath: string}} legacy The old site (an entry of LEGACY_ORIGINS).
 * @param {Record<string, string>} [map] Old address without the base path ->
 *   destination with the current base path.
 * @param {Record<string, string>} [shards] Retired shard name -> current name.
 * @param {{siteUrl: string, basePath: string}} [target] The current site.
 * @returns {object[]} The items, as cloudflareItems writes them.
 */
export function legacyItems(legacy, map = redirects, shards = retiredShards(), target = CURRENT) {
	return cloudflareItems(map, shards, { target, source: legacy });
}

/**
 * The pages a build's sitemap lists, as paths on the current site.
 *
 * @param {string} dist The build.
 * @param {{siteUrl: string, basePath: string}} [target] The site the build is made for.
 * @returns {string[]} Every page, from `/`, each ending in `/`, in sitemap order.
 * @throws {Error} When the build has no sitemap index, it lists no page, or a
 *   page is on another site or does not end in `/`.
 */
export function sitemapPages(dist, target = CURRENT) {
	const site = `${target.siteUrl}${target.basePath}`;
	const locs = (file) => [...readFileSync(file, 'utf8').matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]);
	const index = join(dist, 'sitemap-index.xml');
	if (!existsSync(index)) throw new Error(`${index}: no sitemap index; build the site first`);
	const pages = [];
	for (const shard of locs(index)) {
		if (!shard.startsWith(`${site}/`)) throw new Error(`the sitemap shard ${shard} is not on ${site}`);
		for (const page of locs(join(dist, shard.slice(site.length)))) {
			if (!page.startsWith(`${site}/`)) throw new Error(`the sitemap page ${page} is not on ${site}`);
			const path = page.slice(site.length);
			if (!path.endsWith('/')) throw new Error(`the sitemap page ${page} does not end in /`);
			pages.push(path);
		}
	}
	if (pages.length === 0) throw new Error(`${index}: the sitemap lists no page`);
	return pages;
}

/**
 * The list items that send each page the old site served, written without
 * its trailing slash, straight to the page here.
 *
 * The old host answered such an address with one 301 to the slash form. A
 * list that sent only the slash form would leave it to a catch-all redirect
 * to the same path here, and then to the static host's own redirect to the
 * slash: two hops where there was one. The home page's address without its
 * slash is the old base path itself.
 *
 * @param {string[]} pages The pages, as paths on the current site ending in `/`.
 * @param {{siteUrl: string, basePath: string}} legacy The old site.
 * @param {{siteUrl: string, basePath: string}} [target] The current site.
 * @returns {object[]} One item per page, as cloudflareItems writes them.
 */
export function legacyPageItems(pages, legacy, target = CURRENT) {
	const old = `${new URL(legacy.siteUrl).host}${legacy.basePath}`;
	return pages.map((path) => listItem(`${old}${path.slice(0, -1)}`, `${target.siteUrl}${target.basePath}${path}`));
}

/**
 * The whole list a legacy origin answers from: every address it retired, its
 * Markdown copy and retired shard names, and every page without its slash.
 *
 * @param {{siteUrl: string, basePath: string}} legacy The old site.
 * @param {string[]} pages The pages of the current build (sitemapPages).
 * @param {Record<string, string>} [map] The redirect map.
 * @param {Record<string, string>} [shards] Retired shard name -> current name.
 * @param {{siteUrl: string, basePath: string}} [target] The current site.
 * @returns {object[]} The items; a source listed twice stops the list.
 */
export function legacyList(legacy, pages, map = redirects, shards = retiredShards(), target = CURRENT) {
	const items = [...legacyItems(legacy, map, shards, target), ...legacyPageItems(pages, legacy, target)];
	const seen = new Set();
	for (const { redirect } of items) {
		if (seen.has(redirect.source_url)) throw new Error(`${redirect.source_url} is retired twice`);
		seen.add(redirect.source_url);
	}
	return items;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	const { values } = parseArgs({ args: process.argv.slice(2), options: { legacy: { type: 'boolean' }, dist: { type: 'string' } } });
	if (values.legacy) {
		if (LEGACY_ORIGINS.length === 0) throw new Error('site-targets.json names no legacy origin');
		// The build beside this script's folder, unless another is named.
		const pages = sitemapPages(values.dist ?? join(dirname(fileURLToPath(import.meta.url)), '..', 'dist'));
		process.stdout.write(JSON.stringify(LEGACY_ORIGINS.flatMap((legacy) => legacyList(legacy, pages))));
	} else {
		process.stdout.write(JSON.stringify(cloudflareItems()));
	}
}
