// The retired addresses as Cloudflare Bulk Redirects list items.
//
// GitHub Pages can only answer a retired address with the stub page Astro
// writes for it, a 200 carrying a meta refresh. Search engines ask for a
// server-side permanent redirect wherever one is possible: Google treats an
// instant meta refresh as the fallback ("Redirects and Google Search"), and
// Bing's Webmaster Guidelines say "Use 301 redirects for permanent URL
// changes". docs.jmrp.io is proxied by Cloudflare, so the 301s are served
// there, from an account-level Bulk Redirects list built from the same map the
// stubs come from, src/data/redirects.mjs. The stubs stay in the build as the
// answer for anyone who reaches GitHub Pages directly.
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
// The output is the JSON array the list items endpoint takes; CONTRIBUTING.md
// says how to replace the list with it. No credential is read or needed here.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { redirects } from '../src/data/redirects.mjs';
import { basePath, siteUrl } from '../src/data/site.mjs';
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

/**
 * The Markdown copy of the page at *to*, a destination with the base path. A
 * Spanish API page is the English entry served again (src/lib/fallback-routes.mjs)
 * and has no copy of its own, so its English twin's copy stands for it.
 *
 * @param {string} to
 * @returns {string} The copy's path, with the base path.
 */
export function copyOf(to) {
	return `${isFallbackRoute(to, basePath) ? englishTwin(to, basePath) : to}index.md`;
}

/**
 * Every retired address and where it answers, as absolute sources without
 * the scheme (what a list item matches) and absolute targets.
 *
 * @param {Record<string, string>} map Old address without the base path ->
 *   destination with it, as src/data/redirects.mjs exports them.
 * @param {Record<string, string>} shards Retired shard name -> current name.
 * @returns {Map<string, string>} Source URL -> target URL, in the order listed.
 */
export function retiredAddresses(map = redirects, shards = retiredShards()) {
	const host = new URL(siteUrl).host;
	/** @type {Map<string, string>} */
	const addresses = new Map();
	const add = (source, target) => {
		if (addresses.has(source)) throw new Error(`${source} is retired twice`);
		addresses.set(source, target);
	};
	for (const [from, to] of Object.entries(map)) {
		const target = `${siteUrl}${to}`;
		add(`${host}${basePath}${from}`, target);
		if (from.endsWith('/') && from.length > 1) add(`${host}${basePath}${from.slice(0, -1)}`, target);
	}
	for (const [from, to] of Object.entries(map)) {
		if (!from.endsWith('/') || !to.endsWith('/')) continue;
		add(`${host}${basePath}${from}index.md`, `${siteUrl}${copyOf(to)}`);
	}
	for (const [from, to] of Object.entries(shards)) {
		add(`${host}${basePath}/llms/llms-${from}.txt`, `${siteUrl}${basePath}/llms/llms-${to}.txt`);
	}
	return addresses;
}

/**
 * Every retired address as a path, with the path it now answers at.
 *
 * The same addresses as the list items below, read without the host: the
 * `_redirects` file of the phonometry.dev preview (site/worker/lib/redirects.mjs)
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
 *   destination with it, as src/data/redirects.mjs exports them.
 * @param {Record<string, string>} [shards] Retired shard name -> current name.
 * @returns {object[]} One item per source URL: two per address that ends in a
 *   slash, one for its Markdown copy, and one per retired shard name.
 */
export function cloudflareItems(map = redirects, shards = retiredShards()) {
	return [...retiredAddresses(map, shards)].map(([source_url, target_url]) => ({
		redirect: {
			source_url,
			target_url,
			status_code: 301,
			preserve_query_string: true,
			include_subdomains: false,
			subpath_matching: false,
			preserve_path_suffix: false,
		},
	}));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.stdout.write(JSON.stringify(cloudflareItems()));
}
