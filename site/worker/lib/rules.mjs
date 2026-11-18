// The zone rules of phonometry.dev, as the JSON the rulesets API takes.
//
// Rules are zone configuration the edge evaluates before any Worker
// (https://developers.cloudflare.com/rules/url-forwarding/, "Execution
// order"), so they cost no Worker invocation and keep working whatever the
// daily quota says. A Free zone takes ten Single Redirect rules with wildcard
// matching and no regular expressions; these are four.
//
// scripts/apply-rules.mjs puts them in the two phase entrypoints, and with
// --check fails when the live rules differ from these.

/** The Accept patterns of the Markdown rule, shared by the expression and its model below. */
export const ACCEPT_WANTS_MARKDOWN = '*text/markdown*';
export const ACCEPT_HTML_FIRST = Object.freeze(['*text/html*text/markdown*', '*application/xhtml+xml*text/markdown*']);

/**
 * A literal for an expression, refused when it could end the string it sits in.
 *
 * @param {string} value The text.
 * @param {string} what What it is, for the error.
 * @returns {string} The value in double quotes.
 */
function literal(value, what) {
	if (/["\\]/.test(value)) throw new Error(`${what} cannot hold a quote or a backslash: ${value}`);
	return `"${value}"`;
}

const anyAccept = (pattern) => `any(http.request.headers["accept"][*] wildcard ${literal(pattern, 'Accept pattern')})`;

/**
 * The `http_request_dynamic_redirect` rules, in order.
 *
 * @param {object} options
 * @param {string} options.host The zone apex: `phonometry.dev`.
 * @param {string} options.prefix The base path the site is served under, or `` at the root.
 * @param {{pages: string[], subtrees: string[]}} options.exclusions Pages without a Markdown copy.
 * @param {string} options.clipBase Where a clip is answered with byte ranges, ending in `/`:
 *   `https://docs.jmrp.io/phonometry/media/` until the R2 bucket exists.
 * @returns {object[]} The rules.
 */
export function redirectRules({ host, prefix, exclusions, clipBase }) {
	const h = literal(host, 'host');
	literal(clipBase, 'clip base');
	const rules = [
		{
			ref: 'www-to-apex',
			description: 'www goes to the apex, path and query kept',
			expression: `http.host eq ${literal(`www.${host}`, 'host')}`,
			action: 'redirect',
			action_parameters: {
				from_value: {
					status_code: 301,
					target_url: { expression: `concat(${literal(`https://${host}`, 'host')}, http.request.uri.path)` },
					preserve_query_string: true,
				},
			},
			enabled: true,
		},
	];
	if (prefix !== '') {
		rules.push({
			ref: 'root-to-base',
			description: 'the bare root goes to the base path the site is built under',
			expression: `http.host eq ${h} and http.request.uri.path eq "/"`,
			action: 'redirect',
			action_parameters: {
				from_value: {
					status_code: 302,
					target_url: { value: `https://${host}${prefix}/` },
					preserve_query_string: true,
				},
			},
			enabled: true,
		});
	}
	const clips = `${prefix}/media/*.webm`;
	rules.push({
		ref: 'clips-to-range-host',
		description: 'a clip is served where a byte range gets a 206 (Static Assets answers 200 with the whole file)',
		expression: `http.host eq ${h} and http.request.uri.path wildcard ${literal(clips, 'prefix')}`,
		action: 'redirect',
		action_parameters: {
			from_value: {
				status_code: 302,
				target_url: {
					expression: `wildcard_replace(http.request.uri.path, ${literal(clips, 'prefix')}, ${literal(`${clipBase}\${1}.webm`, 'clip base')})`,
				},
				preserve_query_string: false,
			},
		},
		enabled: true,
	});
	rules.push({
		ref: 'markdown-twin',
		description: 'a request that asks for Markdown and names no HTML type before it gets the page Markdown copy',
		expression: markdownExpression({ host, prefix, exclusions }),
		action: 'redirect',
		action_parameters: {
			from_value: {
				status_code: 302,
				target_url: { expression: 'concat(http.request.uri.path, "index.md")' },
				preserve_query_string: false,
			},
		},
		enabled: true,
	});
	return rules;
}

/**
 * The expression of the Markdown rule.
 *
 * @param {{host: string, prefix: string, exclusions: {pages: string[], subtrees: string[]}}} options
 * @returns {string} The expression.
 */
export function markdownExpression({ host, prefix, exclusions }) {
	const parts = [
		`http.host eq ${literal(host, 'host')}`,
		'http.request.method in {"GET" "HEAD"}',
		`starts_with(http.request.uri.path, ${literal(`${prefix}/`, 'prefix')})`,
		'ends_with(http.request.uri.path, "/")',
		anyAccept(ACCEPT_WANTS_MARKDOWN),
		...ACCEPT_HTML_FIRST.map((pattern) => `not ${anyAccept(pattern)}`),
		...exclusions.subtrees.map((root) => `not starts_with(http.request.uri.path, ${literal(root, 'subtree')})`),
	];
	if (exclusions.pages.length > 0) {
		parts.push(`not http.request.uri.path in {${exclusions.pages.map((page) => literal(page, 'page')).join(' ')}}`);
	}
	return parts.join(' and ');
}

/** The cache lifetime of a content-hashed build file: its name changes when its bytes do. */
export const IMMUTABLE = 'public, max-age=31536000, immutable';

/**
 * The `http_response_headers_transform` rules, which can read the status that
 * `_headers` cannot (its patterns match a path whatever the answer):
 *
 * - the Markdown rule's 302 varies on Accept and is never stored, as
 *   docs-edge's own 302 does. Should this rule fail to apply, the 302 still
 *   works: a 302 without freshness information is not stored by a shared cache;
 * - a 404 announces nothing: `_headers` gives every slash path a `Link` to its
 *   copy and every `index.md` a canonical `Link`, and on an address that does
 *   not exist both name another 404. The answer is the site's 404 page, so it
 *   is labelled HTML whatever its extension, and it varies only on encoding,
 *   as docs.jmrp.io's 404 does;
 * - a content-hashed `_astro/` file is cached for a year when it is found, and
 *   only then: a missing one keeps the asset server's revalidating default.
 *
 * @param {{host: string, prefix: string}} options
 * @returns {object[]} The rules.
 */
export function responseHeaderRules({ host, prefix }) {
	const h = literal(host, 'host');
	return [
		{
			ref: 'markdown-twin-vary',
			description: 'the redirect to a Markdown copy varies on Accept and is never stored',
			expression: `http.host eq ${literal(host, 'host')} and http.response.code eq 302 and ends_with(http.request.uri.path, "/") and ${anyAccept(ACCEPT_WANTS_MARKDOWN)}`,
			action: 'rewrite',
			action_parameters: {
				headers: {
					Vary: { operation: 'set', value: 'Accept' },
					'Cache-Control': { operation: 'set', value: 'no-store' },
				},
			},
			enabled: true,
		},
		{
			ref: 'not-found-plain',
			description: 'a 404 is the site page and names no copy and no canonical',
			expression: `http.host eq ${h} and http.response.code eq 404`,
			action: 'rewrite',
			action_parameters: {
				headers: {
					Link: { operation: 'remove' },
					Vary: { operation: 'set', value: 'Accept-Encoding' },
					'Content-Type': { operation: 'set', value: 'text/html; charset=utf-8' },
				},
			},
			enabled: true,
		},
		{
			ref: 'astro-immutable',
			description: 'a content-hashed build file that was found is cached for a year',
			expression: `http.host eq ${h} and http.response.code in {200 304} and starts_with(http.request.uri.path, ${literal(`${prefix}/_astro/`, 'prefix')})`,
			action: 'rewrite',
			action_parameters: {
				headers: {
					'Cache-Control': { operation: 'set', value: IMMUTABLE },
				},
			},
			enabled: true,
		},
	];
}

/**
 * The `wildcard` operator: the whole value matches, case-insensitively, `*`
 * standing for any run of characters, none included.
 *
 * @param {string} value The field value.
 * @param {string} pattern The literal with `*`.
 * @returns {boolean} Whether the operator would match.
 */
export function wildcardMatch(value, pattern) {
	const body = pattern
		.split('*')
		.map((part) => part.replace(/[.+?^${}()|[\]\\/]/g, '\\$&'))
		.join('.*');
	return new RegExp(`^${body}$`, 'is').test(value);
}

/**
 * What the Markdown rule decides for a request: the model the negotiation
 * test holds against docs-edge's prefersMarkdown.
 *
 * @param {{host: string, method: string, path: string, accept: string[]}} request Every Accept field it carries.
 * @param {{host: string, prefix: string, exclusions: {pages: string[], subtrees: string[]}}} zone
 * @returns {boolean} True when the rule answers with the 302.
 */
export function markdownRuleMatches(request, zone) {
	const { host, method, path, accept } = request;
	const anyOf = (pattern) => accept.some((value) => wildcardMatch(value, pattern));
	return (
		host === zone.host &&
		(method === 'GET' || method === 'HEAD') &&
		path.startsWith(`${zone.prefix}/`) &&
		path.endsWith('/') &&
		anyOf(ACCEPT_WANTS_MARKDOWN) &&
		!ACCEPT_HTML_FIRST.some(anyOf) &&
		!zone.exclusions.subtrees.some((root) => path.startsWith(root)) &&
		!zone.exclusions.pages.includes(path)
	);
}

/** The path of the visitor beacon (lib/agent-paths.mjs). */
const BEACON = '/_v';

/**
 * The `http_request_firewall_custom` rules: they run before any Worker, so a
 * request they block costs no invocation.
 *
 * - `beacon-shape` (on): anything at /_v but a POST whose Origin is the site
 *   is blocked. A browser's beacon always passes; scanners and crawlers that
 *   probe the path never reach the Worker.
 * - `quota-guard-beacon` (created off): blocks every request at /_v. The
 *   quota guard (lib/guard.mjs) turns it on at 95 % of the day's Workers
 *   requests and off after 00:00 UTC; it owns the `enabled` bit, which the
 *   apply script keeps as it finds it.
 *
 * @param {{host: string}} options The zone apex.
 * @returns {object[]} The rules, in order.
 */
export function firewallRules({ host }) {
	const at = `http.host eq ${literal(host, 'host')} and http.request.uri.path eq ${literal(BEACON, 'path')}`;
	return [
		{
			ref: 'beacon-shape',
			description: 'Only a POST from the site itself reaches the beacon',
			expression: `${at} and (http.request.method ne "POST" or not any(http.request.headers["origin"][*] eq ${literal(`https://${host}`, 'origin')}))`,
			action: 'block',
			enabled: true,
		},
		{
			ref: 'quota-guard-beacon',
			description: 'Beacon off: the day is at 95 % of the Workers quota (the quota guard switches this)',
			expression: at,
			action: 'block',
			enabled: false,
		},
	];
}

/**
 * The `http_ratelimit` rule: one address may send ten beacons in ten seconds,
 * then it is blocked for ten seconds, before any Worker runs. A Free zone
 * takes one such rule, counted per address and data centre, with a period
 * and a timeout of ten seconds, and its expression may use the path and the
 * verified-bot field only, so it names the path alone: the zone is
 * phonometry.dev, whose www host only redirects, and beacon-shape checks the
 * host (https://developers.cloudflare.com/waf/rate-limiting-rules/#availability).
 * The agent files get none: crawlers fetch copies in bursts.
 *
 * @returns {object[]} The rule.
 */
export function rateLimitRules() {
	return [
		{
			ref: 'beacon-rate',
			description: 'At most 10 beacons in 10 seconds from one address, before any Worker runs',
			expression: `http.request.uri.path eq ${literal(BEACON, 'path')}`,
			action: 'block',
			ratelimit: { characteristics: ['cf.colo.id', 'ip.src'], period: 10, requests_per_period: 10, mitigation_timeout: 10 },
			enabled: true,
		},
	];
}
