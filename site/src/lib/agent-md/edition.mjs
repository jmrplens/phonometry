/**
 * The GitHub edition: the English pages of the site as plain Markdown under
 * docs/, so a reader browsing the repository on GitHub reads each guide where
 * it sits in the tree, and every file says where its page is published.
 *
 * The edition used to be written by hand, a second text beside the site page
 * that drifted shorter and older than the page it copied. It is written from
 * the page source now, by the same renderer and writers as the copies the site
 * publishes, in their GitHub flavour (figures as `<picture>` with both
 * palettes from raw.githubusercontent, no header block, since GitHub shows a
 * file's history and address beside it). This module adds what only the
 * edition needs:
 *
 *  - which pages it holds ({@link editionPages}): every English page that is
 *    not a landing page, an API page, a catalogue or an errata family, less
 *    the pages {@link EDITION_LEFT_OUT} names, each with the reason it has no
 *    file of its own;
 *  - where each page's file is: `docs/<route>.md`, or `docs/<route>/index.md`
 *    for a page written as its folder's index, which is where the site keeps
 *    it too;
 *  - the opening every file carries ({@link editionOpening}): a comment that
 *    names the source to edit, then one line with the way back to the
 *    documentation index (`docs/README.md`) and the address the page is
 *    published at;
 *  - links between pages ({@link editionLinks}): a link to a page of the
 *    edition, or to one whose GitHub copy is a document of docs/
 *    ({@link EDITION_DOCUMENTS}), becomes a relative link to that file, so a
 *    reader on GitHub stays on GitHub; a link with a `#fragment` does so only
 *    when GitHub gives one of that file's headings that anchor, and otherwise
 *    keeps the site's address, where the fragment is the page's own;
 *  - the README check ({@link readmeProblems}): docs/README.md is the edition's
 *    front door, kept by hand, and it links every page of the edition and no
 *    file that is not there.
 *
 * Nothing here starts a process; scripts/agent-md.mjs --docs renders the pages
 * and writes the files.
 *
 * @module
 */
import { existsSync } from 'node:fs';
import { posix, relative, sep } from 'node:path';

import GithubSlugger from 'github-slugger';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkParse from 'remark-parse';
import { unified } from 'unified';

import { readCommittedText } from '../line-ends.mjs';
import { TRANSPLANTED, pageKind, routeOf } from '../page-markdown.mjs';
import { pageFiles } from './content.mjs';
import { rewriteLinks } from './links.mjs';
import { CONTENT_DIR, SITE } from './render.mjs';

/**
 * English pages of the kind `guide` that have no file in the edition, each
 * with the reason. Every other English page of that kind has one: the guides,
 * the overviews, the start pages and the reference pages written as guides
 * (the glossary, the bibliography, the theory pages and the determinism page).
 * A new guide joins the edition by its kind, with nothing to add here; the
 * route set test/edition-routes.json pins has to gain its route, and
 * docs/README.md a line that links it.
 */
export const EDITION_LEFT_OUT = Object.freeze({
  'start/guides': 'docs/README.md is its GitHub copy: the guides index, kept by hand as the front door of docs/',
  'reference/conformance': 'docs/CONFORMANCE.md is its GitHub copy, written from docs/conformance.json',
  'reference/errata': 'docs/ERRATA.md is its GitHub copy, the register every family page is generated from',
  reference: 'the reference hub, whose entries are the API, catalogue and errata pages the edition does not hold',
  'reference/catalogues': 'the index of the published catalogues, which the site alone publishes',
  'reference/reports': 'the index of the fiches, PDF reports the site publishes',
});

/**
 * The routes whose GitHub copy is a document of docs/ that the edition does
 * not write, and that document's path there. A link to one of these pages
 * becomes a link to the document.
 */
export const EDITION_DOCUMENTS = Object.freeze({
  'start/guides': 'README.md',
  ...Object.fromEntries(
    Object.entries(TRANSPLANTED)
      .filter(([, route]) => !route.startsWith('es/'))
      .map(([document, route]) => [route, `${document}.md`]),
  ),
});

/**
 * One page of the edition.
 *
 * @typedef {object} EditionPage
 * @property {string} route  The page's route, `signals/filters/filter-banks`.
 * @property {string} file  Its source, an absolute path under the content directory.
 * @property {string} source  Its source as the repository names it, `site/src/content/docs/...`.
 * @property {string} path  Its file in the edition, relative to docs/.
 */

/**
 * Whether a route is one of the edition's pages, from its kind and the list
 * of pages left out.
 *
 * @param {string} route
 * @returns {boolean}
 */
export const inEdition = (route) =>
  route !== 'es' && !route.startsWith('es/') && pageKind(route) === 'guide' && !Object.hasOwn(EDITION_LEFT_OUT, route);

/**
 * Every page of the edition, in the order of their files.
 *
 * @param {string} [contentDir]  The content collection, the site's by default.
 * @returns {EditionPage[]}
 */
export function editionPages(contentDir = CONTENT_DIR) {
  /** @type {EditionPage[]} */
  const pages = [];
  for (const file of pageFiles(contentDir)) {
    const shown = relative(contentDir, file).split(sep).join('/');
    const route = routeOf(shown);
    if (!inEdition(route)) continue;
    const isIndex = /(?:^|\/)index\.mdx?$/u.test(shown);
    pages.push({
      route,
      file,
      source: `site/src/content/docs/${shown}`,
      path: isIndex ? `${route}/index.md` : `${route}.md`,
    });
  }
  return pages;
}

/** The address a route's page is published at. */
export const publishedAt = (route) => SITE.url(`${SITE.base}/${route ? `${route}/` : ''}`);

/** How the comment that opens every file of the edition starts. */
export const EDITION_MARK = '<!-- Written by `make llms` from ';

/**
 * Whether a text is a file of the edition: one that opens with its comment.
 * A run removes the files a previous run wrote and this one does not, and
 * leaves every other file of docs/ alone.
 *
 * @param {string} text
 * @returns {boolean}
 */
export const isEditionFile = (text) => text.startsWith(`${EDITION_MARK}site/src/content/docs/`);

/**
 * What a file of the edition opens with: a comment that names the source to
 * edit, which GitHub does not show, then the line it does show first, with
 * the way back to the documentation index and the page's published address.
 *
 * @param {EditionPage} page
 * @returns {string}
 */
export function editionOpening(page) {
  const up = '../'.repeat(page.path.split('/').length - 1);
  return [
    `${EDITION_MARK}${page.source}: edit that page and its Spanish twin, then run \`make llms\`. -->`,
    '',
    `← [Documentation index](${up}README.md) · Published at ${publishedAt(page.route)}`,
  ].join('\n');
}

/**
 * The text of a heading as GitHub reads it to name its anchor: the words,
 * with emphasis and code marks gone and a link's label in place of the link.
 *
 * @param {import('./types.mjs').MdNode} node
 * @returns {string}
 */
function headingText(node) {
  if (node.type === 'text' || node.type === 'inlineCode') return node.value ?? '';
  if (node.type === 'inlineMath') return `$${node.value ?? ''}$`;
  if (node.type === 'html') return '';
  return (node.children ?? []).map(headingText).join('');
}

/**
 * Markdown as github.com reads a file: CommonMark with its own extensions
 * (tables, autolinks, strikethrough, task lists) and its maths, and nothing
 * else. Not the site's parser: that one reads Starlight's directives too, so
 * the `:2023` of `ISO 226:2023` in a heading would be a directive there and
 * text on GitHub, and the anchor would come out wrong.
 */
const GITHUB = unified().use(remarkParse).use(remarkGfm).use(remarkMath).freeze();

/** An anchor a page pins itself, `<a id="name"></a>`, which GitHub keeps. */
const EXPLICIT_ANCHOR = /<a\s+(?:id|name)="([^"]+)"\s*>/gu;

/**
 * The anchors GitHub gives a Markdown file: each heading's text slugged as
 * github.com does it (github-slugger), a repeat taking `-1`, `-2` and so on,
 * and every `<a id>` the file writes outside code.
 *
 * @param {string} markdown
 * @returns {Set<string>}
 */
export function githubAnchors(markdown) {
  const slugger = new GithubSlugger();
  /** @type {Set<string>} */
  const anchors = new Set();
  const visit = (node) => {
    if (node.type === 'html') for (const [, id] of (node.value ?? '').matchAll(EXPLICIT_ANCHOR)) anchors.add(id);
    if (node.type === 'heading') anchors.add(slugger.slug(headingText(node)));
    for (const child of node.children ?? []) visit(child);
  };
  visit(GITHUB.parse(markdown));
  return anchors;
}

/** The site's own address, every page under it. */
const SITE_ROOT = SITE.url(`${SITE.base}/`);

/**
 * The page an absolute address of the site names, with its fragment, or
 * nothing for an address that is not a page: a figure, a fiche, a copy or any
 * other file under the site, or another host.
 *
 * @param {string} url
 * @returns {{ route: string, fragment: string } | undefined}
 */
export function sitePage(url) {
  const root = SITE_ROOT.slice(0, -1);
  if (url !== root && !url.startsWith(SITE_ROOT)) return undefined;
  const rest = url.slice(root.length);
  const match = /^(?:\/([^/?#.]+(?:\/[^/?#.]+)*))?\/?(#.*)?$/u.exec(rest);
  if (!match) return undefined;
  return { route: match[1] ?? '', fragment: match[2] ?? '' };
}

/**
 * The file of docs/ that stands for a route in the edition, relative to
 * docs/, or nothing for a page the edition does not hold.
 *
 * @param {string} route
 * @param {ReadonlyMap<string, EditionPage>} pages  The edition, by route.
 * @returns {string | undefined}
 */
export const editionFileOf = (route, pages) => pages.get(route)?.path ?? EDITION_DOCUMENTS[route];

/**
 * Every link of a page's GitHub-flavoured text that leads to a page of the
 * edition (or to a document of docs/ that stands for one), made relative to
 * the page's own file. A link whose fragment GitHub would not find among the
 * target's headings keeps the site's address, where the fragment is the
 * page's own, and is reported. A fragment alone (`#section`) is left as it
 * is; the edition's tests hold every one to the page's headings.
 *
 * @param {string} markdown  The page as pageMarkdown writes it in the GitHub
 *   flavour, every link to the site absolute.
 * @param {EditionPage} page
 * @param {{
 *   pages: ReadonlyMap<string, EditionPage>,
 *   anchorsOf: (path: string) => ReadonlySet<string>,
 * }} edition  `anchorsOf` gives the anchors of a file of docs/ by its path
 *   there, the edition's own pages and the documents alike.
 * @returns {{ markdown: string, kept: string[] }}  The text, and the
 *   addresses left absolute because GitHub would not find their fragment.
 */
export function editionLinks(markdown, page, { pages, anchorsOf }) {
  /** @type {string[]} */
  const kept = [];
  const here = posix.dirname(page.path);
  const text = rewriteLinks(
    markdown,
    (url) => {
      const target = sitePage(url);
      if (!target) return undefined;
      const path = editionFileOf(target.route, pages);
      if (!path) return undefined;
      const fragment = target.fragment.slice(1);
      if (fragment && !anchorsOf(path).has(decodeURIComponent(fragment))) {
        kept.push(url);
        return undefined;
      }
      if (path === page.path) return target.fragment || posix.basename(path);
      return `${posix.relative(here, path)}${target.fragment}`;
    },
    SITE_ROOT.slice(0, -1),
  );
  return { markdown: text, kept };
}

/**
 * A report number with a run of hyphens, in parentheses after the title it
 * numbers: `(NRL/FR/7176--95-9628)`.
 */
const HYPHENED_NUMBER = /\(([^()\s`]*--[^()\s`]*)\)/gu;

/**
 * The text of a page with every report number that holds a run of hyphens
 * written in code: `(NRL/FR/7176--95-9628)` becomes
 * ``(`NRL/FR/7176--95-9628`)``. On the site the References section prints
 * the number outside the text smartypants reads; in the edition it is a line
 * of prose, where the run is the ASCII spelling of a dash the repository's
 * prose refuses (scripts/check_em_dashes.py), so it is set in code, as the
 * guides' reference lists wrote it when the edition was kept by hand. Only
 * text is read: code, maths, a link's address and a comment keep their own.
 *
 * @param {string} markdown
 * @returns {string}
 */
export function numbersInCode(markdown) {
  /** @type {{ at: number, end: number, text: string }[]} */
  const edits = [];
  const visit = (node) => {
    if (node.type === 'text' && node.position) {
      const start = node.position.start.offset ?? 0;
      const source = markdown.slice(start, node.position.end.offset);
      for (const match of source.matchAll(HYPHENED_NUMBER)) {
        const at = start + (match.index ?? 0);
        edits.push({ at, end: at + match[0].length, text: `(\`${match[1]}\`)` });
      }
    }
    for (const child of node.children ?? []) visit(child);
  };
  visit(GITHUB.parse(markdown));
  let text = markdown;
  for (const { at, end, text: code } of edits.sort((a, b) => b.at - a.at)) {
    text = `${text.slice(0, at)}${code}${text.slice(end)}`;
  }
  return text;
}

/**
 * The anchors of a document of docs/ the edition does not write, read from
 * the file as the commit holds it ({@link readCommittedText}), or none for a
 * file that is not there.
 *
 * @param {string} file
 * @returns {Set<string>}
 */
export function documentAnchors(file) {
  return existsSync(file) ? githubAnchors(readCommittedText(file)) : new Set();
}

/** A relative link to a Markdown file in a line of the README: `](start/index.md#a)`. */
const README_LINK = /\]\(<?(?![a-z][a-z0-9+.-]*:)([^)\s#>]+\.md)(?:#[^)\s>]*)?>?\)/giu;

/**
 * What is wrong with docs/README.md as the edition's front door: a page of
 * the edition it does not link, and a link to a Markdown file of docs/ that
 * is neither a page of the edition nor a file there (a page that left the
 * site, or a link that went stale).
 *
 * @param {string} readme  The text of docs/README.md.
 * @param {readonly EditionPage[]} pages
 * @param {(path: string) => boolean} exists  Whether a path, relative to
 *   docs/, is a file there; asked of links that are not edition pages.
 * @returns {string[]}  One sentence per problem; none when it is right.
 */
export function readmeProblems(readme, pages, exists) {
  const linked = new Set([...readme.matchAll(README_LINK)].map((match) => posix.normalize(match[1])));
  const paths = new Set(pages.map((page) => page.path));
  const unlinked = pages.filter((page) => !linked.has(page.path)).map((page) => page.path);
  const dangling = [...linked].filter((path) => !paths.has(path) && !exists(path)).sort();
  /** @type {string[]} */
  const problems = [];
  if (unlinked.length > 0) {
    problems.push(
      `docs/README.md links no line to ${unlinked.length} page(s) of the edition: ${unlinked.join(', ')}. ` +
        'List each where its area of the index belongs.',
    );
  }
  if (dangling.length > 0) {
    problems.push(
      `docs/README.md links ${dangling.length} Markdown file(s) that are neither a page of the edition nor a file of docs/: ` +
        `${dangling.join(', ')}. Point each at the page's file or remove the line.`,
    );
  }
  return problems;
}
