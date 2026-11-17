// The `_redirects` file of the phonometry.dev preview.
//
// docs.jmrp.io answers a retired address with a 301 from the account Bulk
// Redirects list `phonometry_retired`; the preview answers it from the
// `_redirects` file Static Assets reads beside the build
// (https://developers.cloudflare.com/workers/static-assets/redirects/). Both
// are written from the same pairs, redirectPairs() in
// site/scripts/cloudflare-redirects.mjs, so they cannot drift apart. A redirect
// is followed whether or not an asset matches, so Astro's meta-refresh stubs
// at those addresses are never served. Limits: 2,000 static redirects and
// 1,000 characters a line.

export const REDIRECT_STATIC_LIMIT = 2000;
export const REDIRECT_LINE_LIMIT = 1000;

/**
 * The `_redirects` text: one `source target 301` line per pair, in order.
 *
 * @param {{from: string, to: string}[]} pairs From redirectPairs().
 * @returns {string} The file, ending in a newline.
 */
export function redirectsFile(pairs) {
	return pairs.map(({ from, to }) => `${from} ${to} 301\n`).join('');
}

/**
 * The lines of a `_redirects` text.
 *
 * @param {string} text The file.
 * @returns {{from: string, to: string, code: number}[]} Each line, comments and blanks skipped.
 */
export function parseRedirects(text) {
	return text
		.split('\n')
		.filter((line) => line.trim() !== '' && !line.startsWith('#'))
		.map((line) => {
			const [from, to, code = '302'] = line.trim().split(/\s+/);
			return { from, to, code: Number(code) };
		});
}

/**
 * Everything that would make the file wrong or refused.
 *
 * @param {{from: string, to: string}[]} pairs The pairs to write.
 * @param {{exists: (to: string) => boolean}} tree Whether the staged tree serves a target page.
 * @returns {string[]} One line per problem; empty when the file is good.
 */
export function redirectProblems(pairs, { exists }) {
	const problems = [];
	if (pairs.length > REDIRECT_STATIC_LIMIT) {
		problems.push(`${pairs.length} redirects, over the ${REDIRECT_STATIC_LIMIT} static redirects a _redirects file takes`);
	}
	const sources = new Set();
	for (const { from, to } of pairs) {
		if (sources.has(from)) problems.push(`source listed twice: ${from}`);
		sources.add(from);
		if (!/^\/[^\s*:]*$/.test(from) || !/^\/[^\s*:]*$/.test(to)) problems.push(`not a plain path: ${from} -> ${to}`);
		const line = `${from} ${to} 301`;
		if (line.length > REDIRECT_LINE_LIMIT) {
			problems.push(`${from}: ${line.length} characters, over the ${REDIRECT_LINE_LIMIT} a line takes`);
		}
		if (!exists(to)) problems.push(`${from} -> no page at ${to}`);
	}
	for (const { from, to } of pairs) if (sources.has(to)) problems.push(`${from} -> ${to} is itself redirected`);
	return problems;
}
