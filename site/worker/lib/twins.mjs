// Which slash pages of the site publish no Markdown copy.
//
// Every page of the site has a Markdown copy at `<page>index.md`, the one
// convention docs-edge negotiates on docs.jmrp.io, the two homes included,
// except the 269 Spanish API fallback pages, which carry the English
// reference and point at its copy instead (measured on the build of
// 2026-11-17). The preview names those exceptions in two places: the
// `_headers` blocks that keep the `Link` and the `Vary: Accept` off them
// (lib/headers.mjs) and the exclusions of the Markdown redirect rule
// (lib/rules.mjs). Both read them from here, and stage.mjs fails unless the
// set this describes is exactly the set of slash pages the build wrote
// without a copy, so a page that gains or loses one cannot leave the two
// behind.

/**
 * The pages and subtrees without a Markdown copy, under a base path.
 *
 * @param {string} prefix The base path the site is served under: `/phonometry`, or `` at the root.
 * @returns {{pages: string[], subtrees: string[]}} Slash pages listed one by one, and
 *   subtrees (ending in `/`) whose every slash page has no copy, the subtree's own page included.
 */
export function twinExclusions(prefix) {
	return {
		pages: [],
		subtrees: [`${prefix}/es/reference/api/`],
	};
}

/**
 * Whether a slash page is one of the exclusions.
 *
 * @param {string} path A request path ending in `/`.
 * @param {{pages: string[], subtrees: string[]}} exclusions From twinExclusions.
 * @returns {boolean} True when the page publishes no Markdown copy.
 */
export function isExcluded(path, exclusions) {
	return exclusions.pages.includes(path) || exclusions.subtrees.some((root) => path.startsWith(root));
}
