// Shared plumbing for the checks that read the built HTML the way a crawler
// does, with no browser and no server: check-crawl.mjs, which holds titles,
// headings, head links, the sitemap and the links a page carries, and
// check-descriptions.mjs, which holds the meta descriptions.
//
// Both walk the same build, skip the same redirect stubs, decode the same
// entities and print the same ok/FAIL lines, so those live here once.
import { readdirSync } from 'node:fs';
import { join } from 'node:path';

/** Failures of one kind printed in full before the rest are counted. */
const SHOWN = 12;

/** The entities Astro writes in attribute values and text, decoded; `&amp;` last. */
export function decode(text) {
	return text
		.replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
		.replace(/&#x([0-9a-f]+);/gi, (_, code) => String.fromCodePoint(Number.parseInt(code, 16)))
		.replace(/&quot;/g, '"')
		.replace(/&#39;/g, "'")
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&amp;/g, '&');
}

/** The attributes of one start tag, decoded. Astro double-quotes every value. */
export function attributes(tag) {
	const attrs = {};
	for (const [, name, value] of tag.matchAll(/\s([\w:-]+)(?:="([^"]*)")?/g)) {
		attrs[name.toLowerCase()] = value === undefined ? '' : decode(value);
	}
	return attrs;
}

/**
 * Every start tag of one element name in a document, as attribute maps. A
 * quoted value may hold a `>`, which ends no tag.
 */
export const tags = (html, name) =>
	[...html.matchAll(new RegExp(`<${name}\\b(?:[^>"]|"[^"]*")*>`, 'gi'))].map(([tag]) => attributes(tag));

/**
 * The document with the bodies of its scripts, styles and templates blanked:
 * the markup a crawler parses, without the JSON-LD and inline code that only
 * look like it.
 */
export const markupOf = (html) =>
	html.replace(/<(script|style|template)\b[^>]*>[\s\S]*?<\/\1>/gi, '<$1></$1>');

/** Whether a built file is one of the stubs that send a retired address on. */
export const isRedirectStub = (html) => /http-equiv="refresh"/.test(html);

/** Every route the build wrote, from `x/index.html` to `/x/`, `404.html` to `/404/`. */
export function walk(dir, route = '/', out = new Map()) {
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		if (entry.isDirectory()) walk(join(dir, entry.name), `${route}${entry.name}/`, out);
		else if (entry.name === 'index.html') out.set(route, join(dir, entry.name));
		else if (entry.name.endsWith('.html')) out.set(`${route}${entry.name.slice(0, -5)}/`, join(dir, entry.name));
	}
	return out;
}

/** The language of a route: Spanish under `/es/`, English everywhere else. */
export const languageOf = (route) => (/^\/es(\/|$)/.test(route) ? 'es' : 'en');

/** The error page of either language, which no engine indexes. */
export const isErrorPage = (route) => /^\/(es\/)?404\/$/.test(route);

/**
 * The ok/FAIL printer of one check run. `report` turns a list of findings
 * into one failure with the first few spelled out, or into one ok line when
 * the list is empty; `failures` counts what failed so far.
 */
export function reporter() {
	let failures = 0;
	const fail = (message) => {
		console.error(`FAIL ${message}`);
		failures += 1;
	};
	const ok = (message) => console.log(`ok   ${message}`);
	const report = (findings, what, passed) => {
		if (findings.length === 0) {
			ok(passed);
			return;
		}
		const shown = findings.slice(0, SHOWN).map((line) => `\n       ${line}`).join('');
		const more = findings.length > SHOWN ? `\n       ... and ${findings.length - SHOWN} more` : '';
		fail(`${findings.length} ${what}:${shown}${more}`);
	};
	return { fail, ok, report, failures: () => failures };
}
