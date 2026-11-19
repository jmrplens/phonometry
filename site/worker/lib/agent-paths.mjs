// The requests that run the Worker: the beacon and the files agents read.
//
// wrangler.jsonc lists these as `assets.run_worker_first`; every other
// request (pages, _astro, media, images, PDFs, the search index, and any path
// that is no file) is answered by Static Assets without running a script, so
// it costs no invocation and the daily quota of Workers Free cannot stop it
// (https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/).
// A request that matches here and arrives after the quota is spent gets a
// 429; the quota guard (guard/) switches the Worker to its assets-only
// version before that.
//
// Agents that read the Markdown copies, the llms files, robots.txt and the
// sitemaps run no JavaScript, so the beacon never sees them; running the
// Worker for exactly those files is how they are logged. The root names
// (`/llms*.txt`, `/sitemap*.xml`) are there although the build has only
// `/llms.txt` at the root: crawlers probe both, and a probe is logged too.

import { basePath } from '../../src/data/site.mjs';

/** The beacon's path. Nothing below it (`/_v/`) runs the Worker. */
export const BEACON_PATH = '/_v';

/**
 * The base path the preview serves the site under: site.basePath, from
 * site/src/data/site-targets.json, so it cannot lag the site. The Worker has
 * no PHONOMETRY_SITE, so it reads the target a build with nothing set is made
 * for, the one the deploy stages. wrangler.jsonc lists agentPaths(BASE_PATH),
 * and the Worker reads the same list; test/wrangler.test.mjs holds the two
 * equal.
 */
export const BASE_PATH = basePath;

/**
 * The run_worker_first patterns for a base path.
 *
 * @param {string} prefix The base path the site is served under (`/phonometry`), or `` at the root.
 * @returns {string[]} The patterns, without duplicates, in a fixed order.
 */
export function agentPaths(prefix) {
	const patterns = [
		BEACON_PATH,
		`${prefix}/index.md`,
		`${prefix}/*/index.md`,
		'/llms*.txt',
		`${prefix}/llms*.txt`,
		'/robots.txt',
		`${prefix}/robots.txt`,
		'/sitemap*.xml',
		`${prefix}/*.xml`,
	];
	return [...new Set(patterns)];
}

/**
 * A pattern as Static Assets reads it: `*` matches anything, `/` included,
 * the whole pathname must match, and case counts. A copy of
 * generateGlobOnlyRuleRegExp in Cloudflare's workers-shared router (the
 * miniflare bundle under node_modules carries it; test/agent-paths.test.mjs
 * fails when it changes there).
 *
 * @param {string} rule The pattern.
 * @returns {RegExp} The expression.
 */
export function globRegExp(rule) {
	const escapeRegex = (str) => str.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
	return RegExp(`^${rule.split('*').map(escapeRegex).join('.*')}$`);
}

/**
 * One regular expression for all the patterns, as source text a page script
 * can carry as a literal (every `/` is escaped).
 *
 * @param {string[]} patterns The run_worker_first patterns.
 * @returns {string} The source, anchored at both ends.
 */
export function patternsSource(patterns) {
	return `^(?:${patterns.map((pattern) => globRegExp(pattern).source.slice(1, -1)).join('|')})$`;
}

/**
 * Whether a request path runs the Worker.
 *
 * @param {string} path The URL pathname, as sent.
 * @param {string[]} patterns The run_worker_first patterns.
 * @returns {boolean} True when a pattern matches it.
 */
export function runsWorker(path, patterns) {
	return patterns.some((pattern) => globRegExp(pattern).test(path));
}
