// Injects <lastmod> into the generated sitemap.
//
// Starlight's built-in sitemap (via @astrojs/sitemap) emits <loc> entries with
// no <lastmod>, so crawlers — including AI crawlers — can't tell when a page last
// changed. This post-build step maps each sitemap URL back to its source content
// file and stamps the file's last Git commit date as <lastmod>. Runs after
// `astro build` (see package.json `postbuild`).
//
// Date resolution per URL: Git commit date of the source .mdx/.md → file mtime →
// build time. In a shallow CI checkout Git dates may collapse to the latest
// commit; the deploy workflow uses fetch-depth: 0 so per-file dates are accurate.
import { execFileSync } from "node:child_process";
import {
	existsSync,
	readdirSync,
	readFileSync,
	statSync,
	writeFileSync,
} from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const siteRoot = join(here, "..");
const repoRoot = join(siteRoot, "..");
const distDir = join(siteRoot, "dist");
const docsDir = join(siteRoot, "src", "content", "docs");

const SITE = "https://jmrplens.github.io";
const BASE = "/phonometry";
const buildDate = new Date().toISOString().slice(0, 10);

// Map a sitemap URL to its source content file, or null if none is found or the
// URL is not on this site's origin (so unrelated URLs are never stamped).
function sourceFileFor(url) {
	let parsed;
	try {
		parsed = new URL(url);
	} catch {
		return null;
	}
	if (parsed.origin !== SITE) return null;
	let rel = parsed.pathname;
	if (rel.startsWith(BASE)) rel = rel.slice(BASE.length);
	rel = rel.replace(/^\/+|\/+$/g, ""); // trim slashes → "tools/overview" | "es" | ""
	const base = rel === "" ? "index" : rel === "es" ? "es/index" : rel;
	for (const ext of [".mdx", ".md"]) {
		const candidate = join(docsDir, base + ext);
		if (existsSync(candidate)) return candidate;
	}
	return null;
}

// Absolute-path → last commit date (YYYY-MM-DD), built in a single `git log`
// pass over the docs tree instead of one subprocess per URL. Output is
// newest-first, so the first date seen for a file is its last-modified date.
function buildGitDateMap() {
	const map = new Map();
	try {
		const out = execFileSync(
			"git",
			["log", "--format=%cI", "--name-only", "--", "site/src/content/docs"],
			{ cwd: repoRoot, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 },
		);
		let current = null;
		for (const line of out.split("\n")) {
			if (line === "") continue;
			if (/^\d{4}-\d{2}-\d{2}T/.test(line)) {
				current = line.slice(0, 10);
			} else {
				const abs = join(repoRoot, line);
				if (!map.has(abs)) map.set(abs, current);
			}
		}
	} catch {
		// Leave the map empty; callers fall back to file mtime / build date.
	}
	return map;
}
const gitDates = buildGitDateMap();

// Last commit date (YYYY-MM-DD) for a file, or null if unavailable.
function gitDate(absPath) {
	return gitDates.get(absPath) ?? null;
}

function lastmodFor(url) {
	const src = sourceFileFor(url);
	if (!src) return buildDate;
	return (
		gitDate(src) ?? statSync(src).mtime.toISOString().slice(0, 10) ?? buildDate
	);
}

// Add <lastmod> to each <url> that lacks one. Matching the whole <url>…</url>
// block (not just <loc>) keeps this idempotent: if an entry already carries a
// <lastmod>, it is left untouched rather than getting a duplicate.
function stampSitemap(file) {
	const xml = readFileSync(file, "utf8");
	let changed = 0;
	const out = xml.replace(/<url>[\s\S]*?<\/url>/g, (block) => {
		if (block.includes("<lastmod>")) return block;
		return block.replace(/<loc>([^<]+)<\/loc>/, (locMatch, loc) => {
			changed++;
			return `<loc>${loc}</loc><lastmod>${lastmodFor(loc)}</lastmod>`;
		});
	});
	if (changed > 0) {
		writeFileSync(file, out);
		console.log(
			`[sitemap-lastmod] stamped ${changed} URLs in ${file.replace(distDir, "dist")}`,
		);
	}
}

if (!existsSync(distDir)) {
	console.warn("[sitemap-lastmod] dist/ not found — skipping");
	process.exit(0);
}

// Match sitemap.xml and sitemap-<n>.xml, but never the sitemap index.
const sitemaps = readdirSync(distDir).filter(
	(f) => /^sitemap(-\d+)?\.xml$/.test(f) && f !== "sitemap-index.xml",
);
if (sitemaps.length === 0) {
	console.warn("[sitemap-lastmod] no child sitemap found — skipping");
	process.exit(0);
}
for (const f of sitemaps) stampSitemap(join(distDir, f));
