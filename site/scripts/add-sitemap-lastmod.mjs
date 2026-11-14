// Gives every URL of the built sitemap the date its page's content last changed.
//
// Starlight's sitemap (@astrojs/sitemap) writes each <loc> with no <lastmod>,
// so a crawler cannot tell which pages changed since its last visit. This step
// runs after `astro build` (package.json `postbuild`), maps each URL back to
// the content file it was built from and writes that file's date as <lastmod>.
// The date is the one src/lib/content-dates.mjs gives the page, the same one
// its footer shows and its structured data carries as `dateModified`: the last
// commit that changed its content, passing over the commits that only rewrote
// its title, description or sidebar entry and the sweeps listed in
// site/date-ignore-revs.txt.
//
// Every URL has to name its source. A section page is built from
// `<section>/index.mdx`, and the lookup used to try `<section>.mdx` alone, so
// all 87 of them carried the date of the build, which told every crawler that
// read the sitemap that 87 pages had changed on every deploy. A URL with no
// source now fails the build, listed with the rest, and so does any git
// failure while the dates are read: a sitemap that cannot be dated is not
// published with guessed dates. So does a build with no sitemap to stamp:
// the shards are the ones sitemap-index.xml lists, and the step used to look
// for them by a file name of its own, warn when it found none and pass, which
// a renamed shard would have turned into a sitemap with no dates at all.
// check-crawl.mjs then holds every URL of the sitemap to its page's
// `dateModified` and footer.
//
// Usage: node scripts/add-sitemap-lastmod.mjs [site root]   (default: this
// script's site, which is how `postbuild` runs it; the tests hand it a site
// of their own)
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { basePath, siteUrl } from "../src/data/site.mjs";
import { loadContentDates } from "../src/lib/content-dates.mjs";
import { CONTENT_DIR, isoDay } from "../src/lib/date-rules.mjs";

const siteRoot = resolve(
	process.argv[2] ?? join(dirname(fileURLToPath(import.meta.url)), ".."),
);
const distDir = join(siteRoot, "dist");
const docsDir = join(siteRoot, CONTENT_DIR);

// The content file a sitemap URL was built from, or null when there is none
// (or the URL is not on this site's origin).
function sourceFileFor(url) {
	let parsed;
	try {
		parsed = new URL(url);
	} catch {
		return null;
	}
	if (parsed.origin !== siteUrl) return null;
	let rel = parsed.pathname;
	if (rel.startsWith(basePath)) rel = rel.slice(basePath.length);
	rel = rel.replace(/^\/+|\/+$/g, ""); // "tools/overview" | "es" | ""
	const candidates =
		rel === "" ? ["index"] : [rel, `${rel}/index`]; // A section is its index.
	for (const base of candidates) {
		for (const ext of [".mdx", ".md"]) {
			const candidate = join(docsDir, base + ext);
			if (existsSync(candidate)) return candidate;
		}
	}
	return null;
}

const fail = (message) => {
	console.error(`[sitemap-lastmod] FAIL ${message}`);
	process.exit(1);
};

// The shards are the files the index lists, on this site's origin.
const index = join(distDir, "sitemap-index.xml");
if (!existsSync(index)) fail(`${index} does not exist: no sitemap to stamp.`);
const sitemaps = [...readFileSync(index, "utf8").matchAll(/<loc>([^<]+)<\/loc>/g)].map(([, loc]) => {
	const prefix = `${siteUrl}${basePath}/`;
	if (!loc.startsWith(prefix)) fail(`the sitemap index lists ${loc}, outside ${prefix}.`);
	const file = join(distDir, loc.slice(prefix.length));
	if (!existsSync(file)) fail(`the sitemap index lists ${loc}, which the build did not write.`);
	return file;
});
if (sitemaps.length === 0) fail(`${index} lists no sitemap: nothing would carry a date.`);

// Every <url> block that has no <lastmod> yet, matched whole so that a run
// over a sitemap already stamped leaves it as it is.
const URL_BLOCK = /<url>[\s\S]*?<\/url>/g;
const LOC = /<loc>([^<]+)<\/loc>/;
const unstamped = (xml) =>
	[...xml.matchAll(URL_BLOCK)]
		.map(([block]) => block)
		.filter((block) => !block.includes("<lastmod>"))
		.map((block) => LOC.exec(block)?.[1])
		.filter(Boolean);

const xmls = new Map(sitemaps.map((file) => [file, readFileSync(file, "utf8")]));
const sources = new Map();
const orphans = [];
for (const xml of xmls.values()) {
	for (const loc of unstamped(xml)) {
		const source = sourceFileFor(loc);
		if (source) sources.set(loc, source);
		else orphans.push(loc);
	}
}
if (orphans.length > 0) {
	console.error(
		`[sitemap-lastmod] FAIL ${orphans.length} sitemap URL(s) map to no file under ${CONTENT_DIR}, ` +
			"so they have no date to give:",
	);
	for (const loc of orphans) console.error(`  ${loc}`);
	process.exit(1);
}

let dates;
try {
	dates = await loadContentDates({ siteRoot });
} catch (error) {
	console.error(`[sitemap-lastmod] FAIL the page dates cannot be read: ${error.message}`);
	process.exit(1);
}

for (const [file, xml] of xmls) {
	let changed = 0;
	const out = xml.replace(URL_BLOCK, (block) => {
		if (block.includes("<lastmod>")) return block;
		return block.replace(LOC, (locMatch, loc) => {
			changed++;
			return `${locMatch}<lastmod>${isoDay(dates.dateOf(sources.get(loc)))}</lastmod>`;
		});
	});
	if (changed > 0) {
		writeFileSync(file, out);
		console.log(
			`[sitemap-lastmod] stamped ${changed} URLs in ${file.replace(distDir, "dist")} ` +
				`(${dates.pages} pages dated, ${dates.blobs} page versions read in ${dates.rounds} round(s), ` +
				`${dates.raised} of the ${dates.sourced} built from other files dated by them)`,
		);
	}
}
