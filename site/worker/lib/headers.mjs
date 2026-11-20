// The `_headers` file of phonometry.dev.
//
// On docs.jmrp.io the response headers come from zone Transform Rules and
// from docs-edge. The preview has no script on any request, so every header
// it adds lives here, in the file Static Assets reads beside the build
// (https://developers.cloudflare.com/workers/static-assets/headers/): one
// splat per pattern, `:splat` usable in a value, `! Name` removing what an
// EARLIER rule added, rules applied in file order, at most 100 rules and
// 2 000 characters a line. None of it applies to a response that Worker code
// builds, which is one more reason the preview has no code.

import { mediaOrigins } from '../../src/data/site.mjs';

/** The documented limits of a `_headers` file. */
export const HEADER_RULE_LIMIT = 100;
export const HEADER_LINE_LIMIT = 2000;

/**
 * What every response carries: docs.jmrp.io's response header rule 1 (zone
 * ruleset "Response header transforms", copied verbatim on 2026-11-17), plus
 * the `nosniff` that HSTS settings of that zone send. Order kept. The one
 * change is `media-src`: on docs.jmrp.io a clip is served from the page's own
 * origin, while here the zone rule clips-to-range-host redirects it to a host
 * of `mediaOrigins` (site/src/data/site.mjs), and a browser holds the
 * redirect target to this policy as well as to the page's meta tag.
 */
export const SECURITY_HEADERS = Object.freeze([
	['Access-Control-Allow-Origin', '*'],
	[
		'Content-Security-Policy',
		`default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://img.shields.io https://cursor.com https://kiro.dev https://files.lmstudio.ai; font-src 'self' data:; ${["media-src 'self'", ...mediaOrigins].join(' ')}; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; report-uri https://jmrp.io/csp-report`,
	],
	['Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=(), usb=()'],
	['Referrer-Policy', 'strict-origin-when-cross-origin'],
	['X-Frame-Options', 'DENY'],
	['X-Content-Type-Options', 'nosniff'],
]);

/**
 * The text types whose files carry UTF-8 that is not ASCII (Markdown copies,
 * llms files, robots.txt). The asset server names the type from the
 * extension with no charset, and a browser then reads the bytes as
 * windows-1252; docs.jmrp.io says utf-8, and so does this.
 */
export const TEXT_TYPES = Object.freeze([
	['/*.md', 'text/markdown; charset=utf-8'],
	['/*.txt', 'text/plain; charset=utf-8'],
]);

/**
 * Refuses a base path or an origin that would write wrong patterns.
 *
 * @param {string} prefix `` at the root, or a path such as `/docs`.
 * @param {string} origin `https://phonometry.dev`, with no trailing slash.
 */
export function checkPrefixAndOrigin(prefix, origin) {
	if (prefix !== '' && (!prefix.startsWith('/') || prefix.endsWith('/'))) {
		throw new Error(`prefix must be empty or start with / and not end with one: ${JSON.stringify(prefix)}`);
	}
	if (origin !== undefined && !/^https:\/\/[a-z0-9.-]+$/.test(origin)) {
		throw new Error(`origin must be https://host with no path: ${JSON.stringify(origin)}`);
	}
}

/**
 * The `_headers` text.
 *
 * @param {object} options
 * @param {string} options.prefix The base path the build is served under.
 * @param {string} options.origin The origin the build names as canonical (its site URL).
 * @param {{pages: string[], subtrees: string[]}} options.exclusions Slash pages without a
 *   Markdown copy (lib/twins.mjs).
 * @param {boolean} options.indexable False for the preview: every response says noindex.
 *   True on migration day, when only the llms files keep it, as on docs.jmrp.io.
 * @returns {string} The file, ending in a newline.
 */
export function headersFile({ prefix, origin, exclusions, indexable }) {
	checkPrefixAndOrigin(prefix, origin);
	const blocks = [];
	const block = (pattern, ...lines) => blocks.push([pattern, ...lines.map((line) => `  ${line}`)].join('\n'));
	const announce = (twin) => [`Vary: Accept, Accept-Encoding`, `Link: <${twin}>; rel="alternate"; type="text/markdown"`];

	block('/*', ...(indexable ? [] : ['X-Robots-Tag: noindex']), ...SECURITY_HEADERS.map(([name, value]) => `${name}: ${value}`));
	// A page names its Markdown copy, and varies on Accept because the zone's
	// redirect rule answers a Markdown-preferring request for it with a 302.
	// The Vary list repeats Accept-Encoding because a set replaces it.
	block(`${prefix}/`, ...announce(`${prefix}/index.md`));
	block(`${prefix}/*/`, ...announce(`${prefix}/:splat/index.md`));
	// Pages without a copy, after the rules that announced one.
	for (const page of exclusions.pages) block(page, '! Link', '! Vary');
	for (const root of exclusions.subtrees) {
		block(root, '! Link', '! Vary');
		block(`${root}*`, '! Link', '! Vary');
	}
	// A copy names its page as canonical, on the origin the build was made for.
	block(`${prefix}/index.md`, `Link: <${origin}${prefix}/>; rel="canonical"`);
	block(`${prefix}/*/index.md`, `Link: <${origin}${prefix}/:splat/>; rel="canonical"`);
	// The llms files stay out of search indexes, as on docs.jmrp.io; the
	// staging step also copies llms.txt to the host root.
	if (indexable) {
		block(`${prefix}/llms*`, 'X-Robots-Tag: noindex');
		if (prefix !== '') block('/llms*', 'X-Robots-Tag: noindex');
	}
	for (const [pattern, type] of TEXT_TYPES) block(pattern, '! Content-Type', `Content-Type: ${type}`);
	// No rule for the content-hashed `_astro/` files: a pattern matches a 404
	// as well, and a one-year immutable 404 would outlive the deploy that
	// fixes it. The zone rule astro-immutable (lib/rules.mjs) sets it on a 200.
	return `${blocks.join('\n\n')}\n`;
}

/**
 * The rules of a `_headers` text, in order.
 *
 * @param {string} text The file.
 * @returns {{pattern: string, lines: string[]}[]} Each pattern with its indented lines, trimmed.
 */
export function parseHeaders(text) {
	const rules = [];
	for (const raw of text.split('\n')) {
		if (raw.trim() === '' || raw.trimStart().startsWith('#')) continue;
		if (/^\s/.test(raw)) rules.at(-1).lines.push(raw.trim());
		else rules.push({ pattern: raw.trim(), lines: [] });
	}
	return rules;
}
