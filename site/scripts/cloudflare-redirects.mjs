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
// Usage: node scripts/cloudflare-redirects.mjs > items.json
// The output is the JSON array the list items endpoint takes; CONTRIBUTING.md
// says how to replace the list with it. No credential is read or needed here.
import { fileURLToPath } from 'node:url';

import { redirects } from '../src/data/redirects.mjs';
import { basePath, siteUrl } from '../src/data/site.mjs';

/**
 * The list items for a redirect map.
 *
 * @param {Record<string, string>} map Old address without the base path ->
 *   destination with it, as src/data/redirects.mjs exports them.
 * @returns {object[]} One item per source URL, two per address that ends in a slash.
 */
export function cloudflareItems(map = redirects) {
	const host = new URL(siteUrl).host;
	const items = [];
	for (const [from, to] of Object.entries(map)) {
		const target = `${siteUrl}${to}`;
		const sources = [`${host}${basePath}${from}`];
		if (from.endsWith('/') && from.length > 1) sources.push(`${host}${basePath}${from.slice(0, -1)}`);
		for (const source_url of sources) {
			items.push({
				redirect: {
					source_url,
					target_url: target,
					status_code: 301,
					preserve_query_string: true,
					include_subdomains: false,
					subpath_matching: false,
					preserve_path_suffix: false,
				},
			});
		}
	}
	return items;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.stdout.write(JSON.stringify(cloudflareItems()));
}
