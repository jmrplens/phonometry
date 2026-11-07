/**
 * Which pages have a published markdown copy, and where it sits.
 *
 * `scripts/emit-page-markdown.mjs` writes one `<route>/index.md` per file in
 * the docs content collection that has a copy. Two places on the page then
 * point readers at it: the `<link rel="alternate" type="text/markdown">` in
 * Head.astro and the page actions menu. Neither may offer a copy the generator
 * did not write, so the rule that decides is stated once here and imported by
 * all three, and by scripts/indexnow-diff.mjs, which reads the copy of every
 * page that has one.
 *
 * The route comes from the content entry's own id, never from the address of
 * the page being viewed. On a multilingual site those differ: Starlight serves
 * the whole English-only API reference under `/es/` as fallback content, and
 * those pages have a route but no file of their own, so no copy is written for
 * them. The copy that belongs to such a page is the one for the entry it is
 * actually rendering, which is the English text the reader has in front of
 * them.
 *
 * Nothing here starts a process: the content tree and docs/ are read from disk
 * as they stand, once, by the first caller that asks.
 */
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import { pageMarkup } from '../../scripts/shared/markdown-spans.mjs';

/**
 * The route a page is served at, from either a content file's path under
 * `src/content/docs/` or a content entry's id.
 *
 * Both sides need this and each used to spell it out for itself, with the same
 * regular expression Astro's own glob loader uses (`/\/index$/`). That
 * expression cannot match at the collection root, where the path is `index.mdx`
 * with no directory in front of it, so the two sides disagreed there: Starlight
 * hands the English splash page an entry id of `''` while the generator called
 * the same file `index` and wrote a copy of it at `/index/`, a route no page
 * occupies. Anchoring the segment at the start as well fixes both readings, and
 * the function is idempotent, so a route or an id that has already been through
 * it comes back unchanged.
 */
export const routeOf = (idOrPath) =>
  idOrPath
    .replace(/\\/g, '/')
    .replace(/\.mdx?$/, '')
    .replace(/(?:^|\/)index$/, '');

/**
 * The documents at the root of docs/ that are published at a route of their
 * own: the conformance report and the errata registry, in English, and the
 * Spanish edition of the registry. A copy of one of these routes is the
 * document, because the page renders its rows from data through a component
 * and its own source holds the introduction alone.
 */
export const TRANSPLANTED = Object.freeze({
  CONFORMANCE: 'reference/conformance',
  ERRATA: 'reference/errata',
  'ERRATA.es': 'es/reference/errata',
});

/** Whether a route is a Spanish page's. */
const isSpanish = (route) => route === 'es' || route.startsWith('es/');

/**
 * The file under docs/ a route's copy is written from, or `undefined` when the
 * copy is written from the page's own source.
 *
 * The mirror is laid out like the site, so `docs/signals/filters/filter-banks.md`
 * is the copy of `/signals/filters/filter-banks/`, and a section's page is its
 * folder's `index.md`. The mirror is English, so a Spanish route has one only
 * where a {@link TRANSPLANTED} document is published in Spanish.
 *
 * @param {string} route
 * @param {string} docsDir The docs/ folder.
 * @returns {string | undefined}
 */
export function mirrorOf(route, docsDir) {
  const document = Object.keys(TRANSPLANTED).find((name) => TRANSPLANTED[name] === route);
  if (document !== undefined) return join(docsDir, `${document}.md`);
  if (isSpanish(route)) return undefined;
  return [join(docsDir, `${route}.md`), join(docsDir, route, 'index.md')].find((path) => existsSync(path));
}

/**
 * The components that render a page's data rather than wrap its prose: a
 * catalogue's tables, the conformance report's rows, the errata of a document
 * family, the glossary, the index of fiches and the landing page. A copy
 * written from a page's own source takes every component out, so a page that
 * shows one of these would get a copy holding its introduction and none of what
 * it is there to show. Such a page publishes no copy, and its readers are sent
 * to the page itself. A page whose copy comes from docs/ keeps it: the mirror
 * writes the same data as text.
 *
 * scripts/emit-page-markdown.mjs writes out the components that stay
 * (src/components/ThemeImage.astro and Video.astro as a figure and a line,
 * CatalogueIndex.astro as its list) and keeps the children of the ones that
 * wrap prose; scripts/page-markdown.test.mjs holds every component a page
 * imports to one of those readings.
 */
export const DATA_COMPONENTS = Object.freeze(['Catalogues', 'Conformance', 'ErrataFamily', 'Glossary', 'Home', 'ReportIndex']);

/** A tag of a data component, as the page renders it. */
const DATA_TAG = new RegExp(`<(?:${DATA_COMPONENTS.join('|')})\\b`);

/** The pages of a content tree, as paths below it with forward slashes. */
function pagesUnder(dir, root = dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) pagesUnder(path, root, out);
    else if (/\.mdx?$/.test(entry.name)) out.push(relative(root, path).split(sep).join('/'));
  }
  return out;
}

/**
 * The routes of a content tree that publish no copy because the page renders
 * one of the {@link DATA_COMPONENTS} and has no copy in docs/ to stand for it:
 * the two landing pages, the catalogues, the indexes of fiches, and the Spanish
 * glossary and conformance report. A tag counts where the page renders it
 * (`pageMarkup`), so a page that only shows how to write one, in a code span or
 * a fence, keeps its copy, and an `.md` page renders no component at all.
 *
 * @param {{ contentDir: string, docsDir: string }} tree
 * @returns {Set<string>}
 */
export function withheldRoutes({ contentDir, docsDir }) {
  const withheld = new Set();
  for (const path of pagesUnder(contentDir).sort()) {
    if (!path.endsWith('.mdx')) continue;
    const route = routeOf(path);
    if (mirrorOf(route, docsDir) !== undefined) continue;
    const text = readFileSync(join(contentDir, path), 'utf8');
    if (!DATA_COMPONENTS.some((name) => text.includes(`<${name}`))) continue;
    if (DATA_TAG.test(pageMarkup(text, { kind: 'mdx' }))) withheld.add(route);
  }
  return withheld;
}

/**
 * The site's own content tree and docs/, found by walking up from this module
 * and from the directory the build runs in: once Astro bundles this module into
 * `dist/.prerender/chunks/`, a path relative to the module counts from there.
 */
function siteTree() {
  const starts = [dirname(fileURLToPath(import.meta.url)), process.cwd()];
  for (const start of starts) {
    for (let dir = start; ; dir = dirname(dir)) {
      const contentDir = join(dir, 'site', 'src', 'content', 'docs');
      if (existsSync(join(dir, 'VERSION')) && existsSync(contentDir)) {
        return { contentDir, docsDir: join(dir, 'docs') };
      }
      if (dirname(dir) === dir) break;
    }
  }
  throw new Error(`the site's content tree (site/src/content/docs beside VERSION) is not above ${starts.join(' or ')}`);
}

/** The routes of the site's own tree that publish no copy, read by the first caller. */
let withheld;

/**
 * Whether a route publishes a markdown copy: every page of the site's tree but
 * those {@link withheldRoutes} names. The two landing pages, the roots of the
 * two locales, are among them: each is a layout of the landing component
 * rather than prose.
 *
 * @param {string} route
 * @returns {boolean}
 */
export function hasMarkdownCopy(route) {
  withheld ??= withheldRoutes(siteTree());
  return !withheld.has(route);
}

/** The address of the copy for a route, under the site's base path. */
export const markdownCopyPath = (route, base = '') => `${base}/${route}/index.md`;

/**
 * The attribute the element that states a page's conformance checks carries
 * (the "Verified by N conformance checks" line under the title,
 * src/components/VerifiedBy.astro). A reader of the built page, a check or a
 * copy of the page that has to say the same, finds the line by it rather than
 * by its words, which are the page's language.
 */
export const VERIFIED_BY_ATTRIBUTE = 'data-verified-by';
