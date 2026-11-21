// The one request that runs the Worker: the visitor beacon.
//
// wrangler.jsonc lists WORKER_PATHS as `assets.run_worker_first`; every other
// request (pages, _astro, media, images, PDFs, the search index, the Markdown
// copies, the llms files, the sitemaps, robots.txt and any path that is no
// file) is answered by Static Assets without running a script, so it costs
// no invocation and the daily quota of Workers Free cannot stop it
// (https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/).
// A request that matches here and arrives after the quota is spent gets a
// 429; the quota guard (guard/) switches the Worker to its assets-only
// version before that.
//
// Only the beacon needs code: it is a POST that no file answers, and the page
// view it reports is written to Analytics Engine. Every file is served as it
// is built, so a Worker that fails, a spent quota or a bad deploy of the code
// cannot take a page, a copy or a crawler file with it. Reads of the files
// agents fetch (copies, llms files, sitemaps) are counted by the zone's own
// analytics, which see every request, the Worker or not.

/** The beacon's path. Nothing below it (`/_v/`) runs the Worker. */
export const BEACON_PATH = '/_v';

/** The run_worker_first patterns: the beacon and nothing else. */
export const WORKER_PATHS = Object.freeze([BEACON_PATH]);

/**
 * A pattern as Static Assets reads it: `*` matches anything, `/` included,
 * the whole pathname must match, and case counts. A copy of
 * generateGlobOnlyRuleRegExp in Cloudflare's workers-shared router (the
 * miniflare bundle under node_modules carries it; test/worker-paths.test.mjs
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
 * Whether a request path runs the Worker.
 *
 * @param {string} path The URL pathname, as sent.
 * @param {readonly string[]} [patterns] The run_worker_first patterns.
 * @returns {boolean} True when a pattern matches it.
 */
export function runsWorker(path, patterns = WORKER_PATHS) {
	return patterns.some((pattern) => globRegExp(pattern).test(path));
}
