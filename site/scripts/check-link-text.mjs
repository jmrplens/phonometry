// The words of every link the build wrote, read the way Lighthouse reads them.
//
// Lighthouse's SEO audit "Links do not have descriptive text" fails a page
// that carries a link whose whole text is a word that names no destination,
// "Start", "here" or "read more" in English, "aquí" or "más" in Spanish. The
// topic list above the sidebar linked the Start topic with the word "Start" on
// every English page, so PageSpeed Insights flagged the home page, and every
// other English page the same way, with every check of the build green.
//
// So this reads the build with no browser and no server, takes the text of
// every link a reader can follow off the page (Lighthouse leaves out a link
// with no address, a `javascript:` or `mailto:` one, a `rel="nofollow"` one
// and a link to a place on the same page), and fails on one whose text, its
// spacing collapsed and its case folded, is one of the words Lighthouse's
// audit lists for English or Spanish. Both lists are held on every page,
// whatever its language, so a Spanish word in an English page fails too.
// check-link-text.test.mjs holds the two lists to the ones in the installed
// Lighthouse, so an update that adds a word fails there until it is added
// here.
//
// Usage: node scripts/check-link-text.mjs [dist-directory]
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { attributes, decode, isRedirectStub, markupOf, markupText, reporter, walk } from './shared/dist-pages.mjs';

/**
 * Link texts that name no destination, as Lighthouse 13.6.0 lists them in
 * `nonDescriptiveLinkTexts` of core/audits/seo/link-text.js, for the two
 * languages the site is written in.
 */
export const NON_DESCRIPTIVE = {
	en: [
		'click here',
		'click this',
		'go',
		'here',
		'information',
		'learn more',
		'more',
		'more info',
		'more information',
		'right here',
		'read more',
		'see more',
		'start',
		'this',
	],
	es: [
		'click aquí',
		'click aqui',
		'clicka aquí',
		'clicka aqui',
		'pincha aquí',
		'pincha aqui',
		'aquí',
		'aqui',
		'más',
		'mas',
		'más información',
		'más informacion',
		'mas información',
		'mas informacion',
		'este',
		'enlace',
		'este enlace',
		'empezar',
	],
};

const BLOCKED = new Set(Object.values(NON_DESCRIPTIVE).flat());

/** Every link of a document, its start tag's attributes and the markup inside it. */
const LINK = /<a\b((?:[^>"]|"[^"]*")*)>([\s\S]*?)<\/a\s*>/gi;

/**
 * Whether Lighthouse reads a link at all: it needs an address, one that is
 * neither script nor mail, a link that is not `nofollow`, and a destination
 * other than the page it is on.
 */
function followed(attrs, route) {
	const href = attrs.href;
	if (!href) return false;
	if ((attrs.rel ?? '').split(/\s+/).includes('nofollow')) return false;
	const lower = href.trim().toLowerCase();
	if (lower.startsWith('javascript:') || lower.startsWith('mailto:')) return false;
	const target = href.split('#', 1)[0];
	return target !== '' && target !== route;
}

/** The text of a link as Lighthouse compares it: spacing collapsed, case folded. */
export const linkText = (inner) => decode(markupText(inner)).replace(/\s+/g, ' ').trim().toLowerCase();

/**
 * The links of one built page whose text names no destination.
 *
 * @param {string} html The built page.
 * @param {string} route The route the page is served at, `/x/`.
 * @returns {{ href: string, text: string }[]} Each offending link.
 */
export function vagueLinks(html, route) {
	const found = [];
	for (const [, tag, inner] of markupOf(html).matchAll(LINK)) {
		const attrs = attributes(` ${tag}`);
		if (!followed(attrs, route)) continue;
		const text = linkText(inner);
		if (BLOCKED.has(text)) found.push({ href: attrs.href, text });
	}
	return found;
}

const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
	const here = dirname(fileURLToPath(import.meta.url));
	const DIST = process.argv[2] ? resolve(process.argv[2]) : join(here, '..', 'dist');
	const { report, failures } = reporter();
	if (!existsSync(DIST)) throw new Error(`no build at ${DIST}: run \`pnpm build\` first`);

	const findings = [];
	let pages = 0;
	for (const [route, file] of walk(DIST)) {
		const html = readFileSync(file, 'utf8');
		if (isRedirectStub(html)) continue;
		pages += 1;
		for (const { href, text } of vagueLinks(html, route)) findings.push(`${route}: a link to ${href} reads "${text}"`);
	}
	console.log(`read the links of ${pages} pages in ${DIST}`);
	report(
		findings,
		'link(s) whose whole text is a word Lighthouse lists as naming no destination',
		'every link names where it goes',
	);
	console.log(`\n${failures()} failing check(s).`);
	process.exit(failures() ? 1 : 0);
}
