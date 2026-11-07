// Publishes a clean markdown copy of every page next to its HTML, so an agent
// can fetch one page as text instead of choosing between parsing the rendered
// HTML and downloading the whole corpus.
//
// Why this exists: a page's HTML is roughly 90% chrome. The sidebar alone is
// ~76 kB on every one of the 442 pages, syntax highlighting adds hundreds of
// kilobytes of inline attributes to the deepest guides, and each KaTeX formula
// is still markup-heavy even now that it serialises as text once. The only clean
// alternative used to be llms-full.txt, which is far too large for a single
// fetch. Now `/signals/levels/levels/index.md` sits beside `/signals/levels/levels/`, and
// Head.astro advertises it with <link rel="alternate" type="text/markdown">.
//
// Source preference: docs/<page>.md where it exists (already plain markdown,
// the same text the llms artifacts carry), otherwise the site source with its
// frontmatter and MDX machinery stripped.
//
// A copy written from the site source opens with the page's title and ends
// with its References section, both of which the layout prints from the
// frontmatter; its figures and clips are an image and a line, a count it
// prints from src/data/conformance-stats.mjs is the number, and a link from
// the site's root is absolute (shared/page-twin.mjs says how each is read). A
// page whose source renders its data through a component publishes no copy:
// src/lib/page-markdown.mjs names those pages, and the head of each says so by
// offering none.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { glob } from "node:fs/promises";
import { parse as parseYaml } from "yaml";
import * as conformanceStats from "../src/data/conformance-stats.mjs";
import { TRANSPLANTED, hasMarkdownCopy, mirrorOf, routeOf } from "../src/lib/page-markdown.mjs";
import { basePath, siteUrl } from "../src/data/site.mjs";
import { catalogueSlugs } from "../src/data/topics.mjs";
import {
  copyDefects,
  figureMarkdown,
  frontmatterSource,
  pageImports,
  referencesMarkdown,
  stripFrontmatter,
  stripMdx,
} from "./shared/page-twin.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const siteRoot = join(here, "..");
const repoRoot = join(siteRoot, "..");
const contentDir = join(siteRoot, "src", "content", "docs");
const docsDir = join(repoRoot, "docs");
const outDir = process.env.ASTRO_OUT_DIR ?? join(siteRoot, "dist");
const SITE_URL = `${siteUrl}${basePath}`;


/**
 * The overview of the published catalogues lists them through a component
 * (src/components/CatalogueIndex.astro), and stripping the MDX takes the
 * component out with it: an agent would get the sentence that introduces the
 * list and no list. So the list is written here as Markdown, from the same
 * pages in the same order, each catalogue's label linked to its page and
 * followed by its description.
 */
function catalogueIndex(lang) {
  const prefix = lang === "es" ? "es/" : "";
  return catalogueSlugs
    .map((slug) => {
      const source = readFileSync(join(contentDir, `${prefix}${slug}.mdx`), "utf8");
      const field = (name) => source.match(new RegExp(`^\\s*${name}: "([^"]*)"`, "m"))?.[1] ?? "";
      return `- [${field("label") || field("title")}](${SITE_URL}/${prefix}${slug}/): ${field("description")}`;
    })
    .join("\n");
}

/**
 * Route for a content file: `guides/levels.mdx` -> `guides/levels`. The rule
 * itself is in src/lib/page-markdown.mjs, because the page has to reach the
 * same answer about itself and the two used to be written out separately.
 */
const routeOfFile = (file) => routeOf(relative(contentDir, file));

// The two generated evidence documents live at the repository root of the
// mirror and are published at the routes src/lib/page-markdown.mjs gives them
// (TRANSPLANTED). Both the link rewriter and the source lookup need the
// mapping: the conformance page is MDX that renders its rows from
// `docs/conformance.json` through a component, so stripping the MDX out of the
// page source would leave an agent with the introduction and no evidence.
// `docs/CONFORMANCE.md` is the text copy of the same rows.
//
// The errata registry is published as an index and one page per document
// family, and its Markdown copy at `reference/errata/` is still the whole
// registry: the index lists the entries and the registry's text is the
// evidence, so an agent reading the index's copy gets every entry in one
// fetch. The Spanish index gets the Spanish edition for the same reason, so
// it is the one Spanish route here.

/** The References heading in each language, as the site's own strings word it. */
const REFERENCES_HEADING = Object.fromEntries(
  ["en", "es"].map((lang) => {
    const strings = JSON.parse(readFileSync(join(siteRoot, "src", "content", "i18n", `${lang}.json`), "utf8"));
    return [lang, String(strings["phonometry.references.title"])];
  }),
);

/** The one data module a page prints a count from, and the counts it exports. */
const STATS_MODULE = join(siteRoot, "src", "data", "conformance-stats.mjs");

/**
 * The value of each name a page prints, from what it imports: a count of
 * src/data/conformance-stats.mjs, and nothing else.
 */
function valuesOf(source, file) {
  const imports = pageImports(source);
  return (name) => {
    const found = imports.get(name);
    if (!found || resolve(dirname(file), found.module) !== STATS_MODULE) return undefined;
    const value = conformanceStats[found.imported];
    return typeof value === "number" || typeof value === "string" ? value : undefined;
  };
}

/**
 * The copy of a page that has no docs/ mirror, written from its own source:
 * its title, its prose, and its References section.
 */
function sourceCopy(file, route) {
  const lang = route === "es" || route.startsWith("es/") ? "es" : "en";
  const kind = file.endsWith(".mdx") ? "mdx" : "md";
  const page = readFileSync(file, "utf8");
  const frontmatter = parseYaml(frontmatterSource(page)) ?? {};
  const source = stripFrontmatter(page);
  // The page's line the source opens on, so that a message names the line of the file.
  const firstLine = page.slice(0, page.length - source.length).split("\n").length;
  let body;
  try {
    body = stripMdx(source, {
      kind,
      expand: (tag) => {
        const index = tag.match(/^<CatalogueIndex lang="(en|es)" \/>$/);
        return index ? catalogueIndex(index[1]) : figureMarkdown(tag, { lang, base: SITE_URL });
      },
      value: kind === "mdx" ? valuesOf(source, file) : undefined,
      origin: siteUrl,
      firstLine,
    });
  } catch (error) {
    throw new Error(`${relative(siteRoot, file)}: ${error.message}`);
  }
  const title = String(frontmatter.title ?? "").trim();
  if (!title) throw new Error(`${relative(siteRoot, file)} has no title for its Markdown copy to open with`);
  const heading = REFERENCES_HEADING[lang];
  const copy = [`# ${title}`, body, referencesMarkdown(frontmatter.references, lang, heading)].filter(Boolean).join("\n\n");
  for (const defect of copyDefects(copy, { source, kind, title, references: frontmatter.references, heading, firstLine })) {
    defects.push(`${relative(siteRoot, file)}: ${defect}`);
  }
  return copy;
}

/** What the copies written from a page's source miss of their page, gathered over the whole run. */
const defects = [];

/**
 * Rewrite links that only work inside the docs/ folder.
 *
 * The mirrored files link each other by relative path, as
 * `[x](../filters/filter-banks.md)`, which resolves when reading the
 * repository and resolves to nothing when the same text is served as a
 * standalone page copy. The mirror is laid out like the site, so the link
 * target resolved against the page's own folder is the route.
 */
function absolutize(text, fromRoute) {
  const here = fromRoute.includes("/") ? fromRoute.replace(/\/[^/]*$/, "") : "";
  return text
    .split("\n")
    // The mirror's backlink to its own index, read by its target rather than
    // its words, so it goes in any language: a page copy is not read from
    // inside docs/, and the Spanish registry's, "Índice de la documentación",
    // would send a Spanish reader to the English documentation's root.
    .filter((line) => !/^← \[[^\]]*\]\((?:\.\.\/)*README\.md\)\s*$/.test(line))
    .join("\n")
    .replace(/\]\(((?:\.\.\/)*[\w./-]+)\.md(#[\w-]+)?\)/g, (_whole, target, anchor = "") => {
      const base = target.replace(/^.*\//, "");
      if (base === "README") return `](${SITE_URL}/${anchor})`;
      if (base === "CONTRIBUTING") {
        return `](https://github.com/jmrplens/phonometry/blob/main/CONTRIBUTING.md${anchor})`;
      }
      const parts = here ? here.split("/") : [];
      for (const step of target.split("/")) {
        if (step === "..") parts.pop();
        else if (step !== ".") parts.push(step);
      }
      const resolved = parts.join("/").replace(/\/index$/, "");
      // The two generated documents live at the repository root in the mirror
      // and are transplanted into these routes on the site.
      const route = TRANSPLANTED[resolved] ?? resolved;
      return `](${SITE_URL}/${route}/${anchor})`;
    });
}

let written = 0;
for await (const file of glob("**/*.{md,mdx}", { cwd: contentDir })) {
  const abs = join(contentDir, file);
  const route = routeOfFile(abs);
  // The two splash pages are a component layout, not prose, and a page that
  // renders its data through a component would get a copy without it; there
  // is no meaningful markdown to serve for either. The same test decides what
  // the page itself advertises (src/lib/page-markdown.mjs).
  if (!hasMarkdownCopy(route)) continue;

  // A route one of the docs/ root documents is published at.
  const isTransplanted = Object.values(TRANSPLANTED).includes(route);
  const mirror = mirrorOf(route, docsDir);

  // The page's own source, read as the site renders it (shared/page-twin.mjs):
  // the import line of a code example and a tag written in a code span stay.
  const raw = mirror ? readFileSync(mirror, "utf8") : sourceCopy(abs, route);
  // A transplanted document sits at the root of docs/, not at its route, so
  // its relative links resolve from there: `ERRATA.es.md` beside `ERRATA.md`
  // is the Spanish registry, not a page under reference/.
  const body = absolutize(raw, mirror && isTransplanted ? "" : route);

  const canonical = `${SITE_URL}/${route}/`;
  const text = `<!-- canonical: ${canonical} -->\nSource: ${canonical}\n\n${body.trim()}\n`;

  const target = join(outDir, route, "index.md");
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, text, "utf8");
  written += 1;
}

if (defects.length) {
  throw new Error(
    `${defects.length} things the Markdown copies written from a page's source miss of their page ` +
      `(scripts/shared/page-twin.mjs, copyDefects):\n  ${defects.join("\n  ")}`,
  );
}

console.log(`[emit-page-markdown] wrote ${written} .md page copies into ${relative(siteRoot, outDir) || "dist"}`);
