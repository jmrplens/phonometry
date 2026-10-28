// What a search engine reads on every page the build wrote.
//
// A crawler takes a page through its <title>, its one <h1>, the canonical and
// hreflang links of its head, the sitemap that lists it and the links it
// carries, and none of that is anything a reader sees go wrong. The audit of
// the published site found every one of them off somewhere while the build,
// the HTML validation and the accessibility audit all stayed green:
//
// - the 269 Spanish API pages repeated the English title, description and body
//   of their twin and still declared themselves Spanish pages of their own,
//   with a self canonical, hreflang and a sitemap entry;
// - ten pages shared a title with another page of their language, and the
//   top-level API page was titled "phonometry | phonometry";
// - the errata page had a second <h1>, a stray `=` under a formula that
//   CommonMark read as a heading underline;
// - the header of every Spanish page linked `/phonometry/es`, which GitHub
//   Pages answers with a 301 to `/phonometry/es/`;
// - 150 links pointed at an accented heading through a percent-encoded
//   fragment, which matches no id as written (docs/contributing F13).
//
// So this reads the build the way a crawler does, with no browser and no
// server, and asserts each of those directly:
//
// 1. one <title> per page, unique within its language ignoring case (Bing's
//    "Too many pages with identical titles"; it does not say whether case
//    counts, so it is assumed not to), and never the site name twice;
// 2. exactly one <h1> per page (Bing's "More than one h1 tag");
// 3. one canonical and one og:url naming the page itself, or its English twin
//    on the routes src/lib/fallback-routes.mjs serves as fallback, one
//    og:locale, and hreflang links and one og:locale:alternate that pair each
//    page with its twin, except on the API reference, which names no other
//    language on either side;
// 4. a sitemap that lists every canonical page once and nothing else, not the
//    error page and not a fallback route, with no language alternates on the
//    API reference;
// 5. no link to an address of this site that answers with a redirect: a
//    retired address (a redirect stub) or a directory written without its
//    trailing slash;
// 6. no link to a page that was not built, and no fragment that names no id
//    on its target page as it is written in the href. Browsers also try the
//    percent-decoded form, but crawlers and the accessibility audit compare
//    the attribute as written.
//
// The redirect stubs are not pages and are only read to know where they are,
// and the error page is held to rules 1 and 2 alone.
//
// Usage: node scripts/check-crawl.mjs [dist-directory]
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';
import { englishTwin, isApiRoute, isFallbackRoute } from '../src/lib/fallback-routes.mjs';
import {
	decode,
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
const ORIGIN = `${siteUrl}${basePath}`;
/** Starlight titles a page "<frontmatter title> | <site title>". */
const SITE_TITLE = 'phonometry';
const TITLE_DELIMITER = ' | ';

const { fail, report, failures } = reporter();

if (!existsSync(DIST)) throw new Error(`no build at ${DIST}: run \`pnpm build\` first`);

/** route -> what the checks below need from that page. */
const pages = new Map();
/** Routes that are redirect stubs. */
const stubs = new Set();

for (const [route, file] of walk(DIST)) {
	const html = readFileSync(file, 'utf8');
	if (isRedirectStub(html)) {
		stubs.add(route);
		continue;
	}
	const markup = markupOf(html);
	const ids = new Set();
	for (const [, id] of markup.matchAll(/\sid="([^"]*)"/g)) ids.add(decode(id));
	for (const anchor of tags(markup, 'a')) if (anchor.name !== undefined) ids.add(anchor.name);
	pages.set(route, {
		titles: [...markup.matchAll(/<title>([^<]*)<\/title>/g)].map(([, title]) => decode(title).trim()),
		h1: [...markup.matchAll(/<h1[\s>]/gi)].length,
		links: tags(markup, 'link'),
		metas: tags(markup, 'meta'),
		hrefs: tags(markup, 'a')
			.map((anchor) => anchor.href)
			.filter((href) => href !== undefined && href !== ''),
		ids,
	});
}

const slugOf = (route) => route.replace(/^\/|\/$/g, '');
/** The address a page names as its own: itself, or the English twin of a fallback. */
const canonicalOf = (route) =>
	isFallbackRoute(slugOf(route)) ? `${ORIGIN}${englishTwin(route)}` : `${ORIGIN}${route}`;

console.log(`read ${pages.size} pages and ${stubs.size} redirect stubs in ${DIST}`);

// --- 1. Titles --------------------------------------------------------------
{
	const notOne = [];
	const doubled = [];
	const byTitle = new Map();
	for (const [route, page] of pages) {
		if (page.titles.length !== 1) {
			notOne.push(`${route}: ${page.titles.length} <title> elements`);
			continue;
		}
		const [title] = page.titles;
		const parts = title.split(TITLE_DELIMITER);
		if (parts.length > 1 && parts[0].trim().toLowerCase() === SITE_TITLE) {
			doubled.push(`${route}: "${title}"`);
		}
		// The fallback routes carry their English twin's title on purpose, and
		// name it canonical; the error page is not indexed.
		if (isFallbackRoute(slugOf(route)) || isErrorPage(route)) continue;
		const key = `${languageOf(route)}\u0000${title.toLowerCase()}`;
		byTitle.set(key, [...(byTitle.get(key) ?? []), route]);
	}
	const shared = [...byTitle]
		.filter(([, routes]) => routes.length > 1)
		.map(([key, routes]) => `"${key.split('\u0000')[1]}" (${key.split('\u0000')[0]}): ${routes.join(' ')}`);
	report(notOne, 'page(s) without exactly one <title>', `every page has one <title>`);
	report(doubled, 'title(s) that name the site twice', `no title repeats the site name`);
	report(
		shared,
		'title(s) shared by pages of one language, ignoring case',
		`every title is unique within its language, ignoring case`,
	);
}

// --- 2. One <h1> ------------------------------------------------------------
report(
	[...pages].filter(([, page]) => page.h1 !== 1).map(([route, page]) => `${route}: ${page.h1} <h1> elements`),
	'page(s) without exactly one <h1>',
	`every page has exactly one <h1>`,
);

// --- 3. Canonical, og:url, og:locale and hreflang ----------------------------
{
	const wrong = [];
	for (const [route, page] of pages) {
		if (isErrorPage(route)) continue;
		const slug = slugOf(route);
		const fallback = isFallbackRoute(slug);
		const expected = canonicalOf(route);
		const canonicals = page.links.filter((link) => link.rel === 'canonical').map((link) => link.href);
		if (canonicals.length !== 1 || canonicals[0] !== expected) {
			wrong.push(`${route}: canonical ${JSON.stringify(canonicals)}, expected ${expected}`);
		}
		const ogUrls = page.metas.filter((meta) => meta.property === 'og:url').map((meta) => meta.content);
		if (ogUrls.length !== 1 || ogUrls[0] !== expected) {
			wrong.push(`${route}: og:url ${JSON.stringify(ogUrls)}, expected ${expected}`);
		}
		const identity = fallback ? 'en' : languageOf(route);
		const locale = identity === 'es' ? 'es_ES' : 'en_US';
		const locales = page.metas.filter((meta) => meta.property === 'og:locale').map((meta) => meta.content);
		if (locales.length !== 1 || locales[0] !== locale) {
			wrong.push(`${route}: og:locale ${JSON.stringify(locales)}, expected ${locale}`);
		}
		// The other language, which the API reference does not have.
		const others = page.metas
			.filter((meta) => meta.property === 'og:locale:alternate')
			.map((meta) => meta.content);
		const other = isApiRoute(slug) ? [] : [locale === 'es_ES' ? 'en_US' : 'es_ES'];
		if (JSON.stringify(others) !== JSON.stringify(other)) {
			wrong.push(`${route}: og:locale:alternate ${JSON.stringify(others)}, expected ${JSON.stringify(other)}`);
		}
		const alternates = page.links
			.filter((link) => link.rel === 'alternate' && link.hreflang !== undefined)
			.map((link) => `${link.hreflang} ${link.href}`)
			.sort();
		const english = `${ORIGIN}/${slug.replace(/^es(\/|$)/, '')}`.replace(/\/?$/, '/');
		const spanish = `${ORIGIN}/es${english.slice(ORIGIN.length)}`;
		const pairs = isApiRoute(slug) ? [] : [`en ${english}`, `es ${spanish}`, `x-default ${english}`].sort();
		if (JSON.stringify(alternates) !== JSON.stringify(pairs)) {
			wrong.push(`${route}: hreflang ${JSON.stringify(alternates)}, expected ${JSON.stringify(pairs)}`);
		}
	}
	report(
		wrong,
		'head tag(s) that misname a page or its twin',
		`every page names itself, or its English twin on a fallback route, as canonical, ` +
			`and hreflang and og:locale:alternate pair every translated page and no API page`,
	);
}

// --- 4. The sitemap ---------------------------------------------------------
{
	const index = join(DIST, 'sitemap-index.xml');
	if (!existsSync(index)) {
		fail('no sitemap-index.xml in the build');
	} else {
		const wrong = [];
		const listed = new Set();
		const shards = [...readFileSync(index, 'utf8').matchAll(/<loc>([^<]+)<\/loc>/g)].map(([, loc]) => loc);
		for (const shard of shards) {
			const file = join(DIST, shard.slice(ORIGIN.length));
			if (!shard.startsWith(`${ORIGIN}/`) || !existsSync(file)) {
				wrong.push(`the index lists ${shard}, which the build did not write`);
				continue;
			}
			for (const [, block] of readFileSync(file, 'utf8').matchAll(/<url>([\s\S]*?)<\/url>/g)) {
				const loc = decode(/<loc>([^<]+)<\/loc>/.exec(block)?.[1] ?? '');
				const route = loc.startsWith(ORIGIN) ? loc.slice(ORIGIN.length) : loc;
				if (listed.has(loc)) wrong.push(`${loc} is listed twice`);
				listed.add(loc);
				if (!pages.has(route)) {
					wrong.push(`${loc} is ${stubs.has(route) ? 'a redirect' : 'not a page the build wrote'}`);
				} else if (isErrorPage(route)) {
					wrong.push(`${loc} is the error page`);
				} else if (canonicalOf(route) !== loc) {
					wrong.push(`${loc} names ${canonicalOf(route)} as canonical`);
				}
				const alternates = [...block.matchAll(/<xhtml:link[^>]*href="([^"]+)"/g)].map(([, href]) => decode(href));
				if (isApiRoute(slugOf(route)) && alternates.length > 0) {
					wrong.push(`${loc} lists language alternates: ${alternates.join(' ')}`);
				}
				for (const href of alternates) {
					const target = href.slice(ORIGIN.length);
					if (isFallbackRoute(slugOf(target))) wrong.push(`${loc} lists ${href} as an alternate`);
				}
			}
		}
		for (const route of pages.keys()) {
			if (isErrorPage(route) || canonicalOf(route) !== `${ORIGIN}${route}`) continue;
			if (!listed.has(`${ORIGIN}${route}`)) wrong.push(`${ORIGIN}${route} is a canonical page the sitemap leaves out`);
		}
		report(
			wrong,
			'problem(s) in the sitemap',
			`the sitemap lists the ${listed.size} canonical pages once each, and no fallback route or error page`,
		);
	}
}

// --- 5 and 6. Links: redirects, missing pages, fragments ---------------------
{
	const redirected = new Map();
	const missing = new Map();
	const fragments = new Map();
	const note = (map, key, route) => map.set(key, [...(map.get(key) ?? []), route]);
	for (const [route, page] of pages) {
		const here = new URL(`${ORIGIN}${route}`);
		for (const href of new Set(page.hrefs)) {
			let target;
			try {
				target = new URL(href, here);
			} catch {
				continue;
			}
			if (target.origin !== siteUrl) continue;
			if (target.pathname !== basePath && !target.pathname.startsWith(`${basePath}/`)) continue;
			let path = target.pathname.slice(basePath.length) || '';
			try {
				path = decodeURI(path);
			} catch {
				// Not valid percent-encoding: look the address up as written.
			}
			// A file, not a page: media, the markdown copies, llms.txt.
			if (/\.[a-z0-9]+$/i.test(path.split('/').pop() ?? '')) continue;
			const where = `${target.pathname}${target.hash}`;
			if (!path.endsWith('/')) {
				if (pages.has(`${path}/`) || stubs.has(`${path}/`)) {
					note(redirected, `${target.pathname} (GitHub Pages answers 301 to add the trailing slash)`, route);
				} else {
					note(missing, where, route);
				}
				continue;
			}
			if (stubs.has(path)) {
				note(redirected, `${target.pathname} (a retired address)`, route);
				continue;
			}
			const landing = pages.get(path);
			if (!landing) {
				note(missing, where, route);
				continue;
			}
			// The fragment exactly as the href carries it, not `target.hash`, which
			// the URL parser has percent-encoded: the decoded form is what a browser
			// falls back to, not what a crawler compares.
			const written = href.includes('#') ? href.slice(href.indexOf('#') + 1) : '';
			if (written === '') continue;
			if (!landing.ids.has(written)) note(fragments, `${target.pathname}#${written}`, route);
		}
	}
	const lines = (map) => [...map].map(([key, routes]) => `${key}, from ${routes.length} page(s): ${routes[0]}`);
	report(
		lines(redirected),
		'internal link target(s) that answer with a redirect',
		`no page links an address that answers with a redirect`,
	);
	report(lines(missing), 'internal link target(s) the build did not write', `every internal link lands on a built page`);
	report(
		lines(fragments),
		'fragment(s) that name no id on their page as written',
		`every fragment of an internal link names an id on its page, as written`,
	);
}

console.log(`\n${failures()} failing check(s).`);
process.exit(failures() ? 1 : 0);
