/**
 * Which pages have a published markdown copy, and where it sits.
 *
 * `scripts/agent-md.mjs --public` writes one `<route>/index.md` per file in
 * the docs content collection, before the build, and the build publishes it
 * beside the page. Three places on the page then point readers at it: the
 * `<link rel="alternate" type="text/markdown">` and the `encoding` of the
 * structured data in Head.astro, and the page actions menu. None of them may
 * offer a copy the generator did not write, so the rule that decides is
 * stated once here and imported by all of them, and by
 * scripts/indexnow-diff.mjs, which reads the copy of every page that has one.
 *
 * The route comes from the content entry's own id, never from the address of
 * the page being viewed. On a multilingual site those differ: Starlight serves
 * the whole English-only API reference under `/es/` as fallback content, and
 * those pages have a route but no file of their own, so no copy is written for
 * them. The copy that belongs to such a page is the one for the entry it is
 * actually rendering, which is the English text the reader has in front of
 * them.
 *
 * Nothing here starts a process or reads a page.
 */
import { existsSync } from 'node:fs';
import { join } from 'node:path';

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
 * Spanish edition of the registry. The GitHub copy of one of these routes is
 * the document, because the page renders its rows from data through a
 * component and its own source holds the introduction alone.
 */
export const TRANSPLANTED = Object.freeze({
  CONFORMANCE: 'reference/conformance',
  ERRATA: 'reference/errata',
  'ERRATA.es': 'es/reference/errata',
});

/** Whether a route is a Spanish page's. */
const isSpanish = (route) => route === 'es' || route.startsWith('es/');

/**
 * The file under docs/ that is a route's GitHub copy, or `undefined` for a
 * route with none. The copy the site publishes beside every page is written
 * from the page's own source (scripts/agent-md.mjs --public); this names the
 * plain-Markdown edition GitHub serves, which scripts/mirror-bibliography.mjs
 * writes for the bibliography.
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
 * family, the glossary, the index of fiches and the landing page. Each has a
 * Markdown writer beside it that writes the same data as text into the page's
 * copy (src/lib/agent-md/), and a page that renders one counts its words apart
 * in the structured-data check, since its own source holds its introduction
 * alone (scripts/check-structured-data.mjs).
 */
export const DATA_COMPONENTS = Object.freeze(['Catalogues', 'Conformance', 'ErrataFamily', 'Glossary', 'Home', 'ReportIndex']);

/**
 * Every page written as a file has a copy, the two landing pages included:
 * theirs carries the tagline, the readout, the install line and the areas the
 * landing shows, written by the landing's own writer
 * (src/components/home/Home.md.mjs). The one route without one is the error
 * page Starlight synthesises, which has no file and which nobody looks up.
 */
export const hasMarkdownCopy = (route) => routeOf(route) !== '404';

/**
 * What kind of page a route of the content collection is, in either
 * language: one of the two landing pages (`home`), the API reference
 * generated from the docstrings (`api`, its index included), one published
 * catalogue (`catalogue`), one family of the errata register
 * (`errata-family`), or any other page (`guide`: the guides, the topic
 * overviews, the start pages and the reference pages).
 *
 * The Markdown copies' check of the build (scripts/check-markdown-twins.mjs)
 * classes every built page by it, and the llms files take their pages by it
 * (scripts/agent-md.mjs --dump hands them the kind of every route), so the two
 * cannot disagree about which page is which.
 *
 * @param {string} route  `signals/levels/levels`, `es/reference/errata/iec`,
 *   `` or `es` for the landing pages; slashes around it are ignored.
 * @returns {'home' | 'api' | 'catalogue' | 'errata-family' | 'guide'}
 */
export function pageKind(route) {
  const bare = routeOf(route.replace(/^\/+|\/+$/gu, ''));
  const english = bare === 'es' ? '' : bare.replace(/^es\//u, '');
  if (english === '') return 'home';
  if (/^reference\/api(?:\/|$)/u.test(english)) return 'api';
  if (/^reference\/catalogues\/[^/]+$/u.test(english)) return 'catalogue';
  if (/^reference\/errata\/[^/]+$/u.test(english)) return 'errata-family';
  return 'guide';
}

/**
 * The kinds of English page whose whole text the llms files carry: each in
 * one shard of `/llms/` (or in the numbered parts of one) and in
 * `llms-full.txt`, as its Markdown copy reads. The landing page is left out,
 * because llms.txt is the index that does its work for an agent, and so is the
 * API reference, which llms.txt lists as optional reading one link per module
 * and which no agent needs whole. scripts/agent-md.mjs --dump hands
 * scripts/generate_llms.py the copies of exactly these pages, and the copies'
 * check of the build holds every one of them to its copy.
 */
export const FULL_TEXT_KINDS = Object.freeze(['guide', 'catalogue', 'errata-family']);

/**
 * The address of the copy for a route, under the site's base path: the
 * landing page's copy sits at the root, `/index.md`, with no empty segment
 * before it.
 */
export const markdownCopyPath = (route, base = '') => `${base}/${route ? `${route}/` : ''}index.md`;

/**
 * The attribute the element that states a page's conformance checks carries
 * (the "Verified by N conformance checks" line under the title,
 * src/components/VerifiedBy.astro). A reader of the built page, a check or a
 * copy of the page that has to say the same, finds the line by it rather than
 * by its words, which are the page's language.
 */
export const VERIFIED_BY_ATTRIBUTE = 'data-verified-by';

/**
 * The header lines of a copy that name the release rather than the page: the
 * version it documents, the command that installs it and, while the version
 * is a pre-release, the line that says it is not on PyPI yet. A copy opens with a
 * block of `Key: value` lines, and a release changes these two on every page
 * at once while no page says anything new.
 *
 * scripts/indexnow-diff.mjs tells search engines which pages changed by
 * hashing each copy, and it hashes the copy without these lines, so stamping
 * a release does not report every page of the site as changed. The header
 * writer (src/lib/agent-md/header.mjs) writes its release lines from this
 * list and has no list of its own, so that the two cannot drift apart.
 */
export const releaseHeaderKeys = Object.freeze(['Version', 'Install', 'Pre-release']);

/** One `Key: value` line of a copy's header. */
const HEADER_FIELD = /^([A-Z][A-Za-z-]*): /;

/** What may come before the header: blank lines, the title, a quoted line and a comment. */
const BEFORE_HEADER = /^(?:\s*$|# |>|<!--)/;

/**
 * A copy's text without its release lines. Only the header is read: the run
 * of consecutive `Key: value` lines that follows the title, quote and comment
 * lines a copy opens with. A copy whose first other line is not such a field
 * has no header, and the same words anywhere in the body, prose or code, are
 * content and stay.
 */
export function withoutReleaseLines(text) {
  const lines = text.split('\n');
  let start = 0;
  while (start < lines.length && BEFORE_HEADER.test(lines[start])) start += 1;
  if (start === lines.length || !HEADER_FIELD.test(lines[start])) return text;
  let end = start;
  while (end < lines.length && HEADER_FIELD.test(lines[end])) end += 1;
  const header = lines
    .slice(start, end)
    .filter((line) => !releaseHeaderKeys.includes(HEADER_FIELD.exec(line)[1]));
  return [...lines.slice(0, start), ...header, ...lines.slice(end)].join('\n');
}
