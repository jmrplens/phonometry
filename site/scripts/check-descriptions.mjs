// The meta description of every page the build wrote.
//
// The description is the one line of a page written for a search result and
// for nobody on the page itself, so nothing a reader does would notice it go
// wrong. The audit of the published site found it too long on 461 of 996
// pages, with a median of about 300 characters, while every check of the
// build stayed green:
//
// - Bing's own tools flag "Meta Description too long or too short" in URL
//   Inspection and Site Scan. It publishes no threshold; 160 characters is the
//   figure its older guidelines stated, and pages rewritten below it were seen
//   to clear the flag.
// - Google raises nothing, but "There's no limit on how long a meta
//   description can be, but the snippet is truncated in Google Search results
//   as needed" (Search Central, "Control your snippets in search results"),
//   so past the cut the reader sees half a sentence.
// - Bing's Recommendations report "Too many pages with identical meta
//   descriptions", and its Webmaster Guidelines say that "Missing, duplicate,
//   or overly short title tags and meta descriptions may reduce indexing
//   reliability".
//
// So this reads the build with no browser and no server and asserts that
// every page carries exactly one meta description, that it says something,
// that it is at most 160 characters long, and that no other page of the same
// language says the same thing, ignoring case and spacing. A page whose
// frontmatter has no description inherits the 319-character site description,
// so a forgotten one fails here as too long, and as a duplicate once a second
// page of its language forgets too.
//
// Three kinds of file are not held to it: the redirect stubs, which are not
// pages; the error page, which no engine indexes and which carries the site
// description; and the Spanish routes src/lib/fallback-routes.mjs serves as
// fallback, which repeat their English twin's description on purpose and name
// that twin canonical. The English twin is checked.
//
// Usage: node scripts/check-descriptions.mjs [dist-directory]
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { isFallbackRoute } from '../src/lib/fallback-routes.mjs';
import {
	isErrorPage,
	isRedirectStub,
	languageOf,
	markupOf,
	reporter,
	tags,
	walk,
} from './shared/dist-pages.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const DIST = process.argv[2] ? resolve(process.argv[2]) : join(here, '..', 'dist');
/** The longest description, in characters, that Bing's tools are known to leave alone. */
const MAX_LENGTH = 160;

const { report, failures } = reporter();

if (!existsSync(DIST)) throw new Error(`no build at ${DIST}: run \`pnpm build\` first`);

/** route -> the content of every meta description its head carries. */
const descriptions = new Map();
let skipped = 0;
for (const [route, file] of walk(DIST)) {
	const html = readFileSync(file, 'utf8');
	if (isRedirectStub(html) || isErrorPage(route) || isFallbackRoute(route)) {
		skipped += 1;
		continue;
	}
	const metas = tags(markupOf(html), 'meta').filter((meta) => meta.name === 'description');
	descriptions.set(
		route,
		metas.map((meta) => meta.content ?? ''),
	);
}

console.log(`read ${descriptions.size} pages in ${DIST}, and skipped ${skipped} stubs, error pages and fallback routes`);

/** Length as a reader counts it: one per character, astral ones included. */
const lengthOf = (text) => [...text].length;
/** The form two descriptions are compared in: case and runs of spacing do not count. */
const keyOf = (text) => text.trim().replace(/\s+/g, ' ').toLowerCase();

const notOne = [];
const empty = [];
const long = [];
const byText = new Map();
for (const [route, contents] of descriptions) {
	if (contents.length !== 1) {
		notOne.push(`${route}: ${contents.length} meta descriptions`);
		continue;
	}
	const [content] = contents;
	if (content.trim() === '') {
		empty.push(route);
		continue;
	}
	const length = lengthOf(content.trim());
	if (length > MAX_LENGTH) long.push(`${route}: ${length} characters`);
	const key = `${languageOf(route)}\u0000${keyOf(content)}`;
	byText.set(key, [...(byText.get(key) ?? []), route]);
}
const shared = [...byText]
	.filter(([, routes]) => routes.length > 1)
	.map(([key, routes]) => {
		const [language, text] = key.split('\u0000');
		const quoted = lengthOf(text) > 60 ? `${[...text].slice(0, 60).join('')}...` : text;
		return `"${quoted}" (${language}): ${routes.join(' ')}`;
	});

report(notOne, 'page(s) without exactly one meta description', 'every page has one meta description');
report(empty, 'page(s) whose meta description is empty', 'no meta description is empty');
report(
	long,
	`meta description(s) over ${MAX_LENGTH} characters`,
	`every meta description is at most ${MAX_LENGTH} characters`,
);
report(
	shared,
	'meta description(s) shared by pages of one language, ignoring case and spacing',
	'every meta description is unique within its language',
);

console.log(`\n${failures()} failing check(s).`);
process.exit(failures() ? 1 : 0);
