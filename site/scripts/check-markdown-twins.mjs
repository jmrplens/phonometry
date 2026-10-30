// Checks that every page's Markdown copy carries what the page carries.
//
// Four things have to agree about every page of the site, and until now
// nothing checked that they did:
//
//   1. the built page              dist/<route>/index.html
//   2. its Markdown copy           dist/<route>/index.md
//   3. what the page says of it    the <link rel="alternate" type="text/markdown">
//                                  in its head and the `encoding` of its
//                                  structured data
//   4. the sitemap                 the <lastmod> the copy's `Updated:` repeats
//
// The copies used to be cut out of the page source by regular expressions, and
// that left them short of the page in ways no check saw: the two landing pages
// had none, the Spanish copies had no title, a self-closing component took its
// data with it, `{expressions}`, `:::` asides, HTML comments and links that
// only resolve on the site leaked into the text. The copies are now written by
// src/lib/agent-md/; this check reads what the build published, so it holds
// the copies to the page whatever writes them.
//
// A CLOSURE CHECK, NOT AN ALLOWLIST (the design of jmrp.io's
// scripts/ci/check-markdown-twins.mjs, ported). Every built page has to match
// exactly one entry of PAGE_CLASSES, and each class states, with a reason,
// whether its pages owe a copy. A page that matches no class fails: that is
// the tripwire for a new kind of page that would quietly publish no copy. A
// class that matches no page fails too, so the table cannot rot into a list of
// exemptions for pages that no longer exist.
//
// THE TEXT RULES ARE READ ON THE PARSED COPY, NOT ON ITS RAW TEXT. Outside
// code, inline code and maths, a copy may hold no raw HTML (a component's tag
// or an HTML comment the source carried), no `{name}` an MDX expression left
// behind, no `:::` of an aside and no link that starts with `/`. Read on the
// raw text, the same rules would fail on what the copies keep on purpose: the
// TeX of 642 pages, `$L_\mathrm{Ceq} - L_\mathrm{Aeq}$`, sits between braces,
// and an API page prints `(EAV\<=value\<ELV)`, where the backslash makes the
// `<` text. A copy is parsed as an agent's Markdown reader parses it
// (CommonMark, GitHub tables and maths), one top-level section at a time,
// because the table parser's cost grows with the square of the rows in one
// document and the conformance report's copy holds a hundred tables.
//
// Usage: node scripts/check-markdown-twins.mjs [dist]   (default: dist/)
// Exit codes: 0 every rule holds; 1 a rule failed (each finding listed, with
// its remedy); 2 the check could not run (no build, no sitemap).
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkParse from 'remark-parse';
import { unified } from 'unified';

import { basePath, siteUrl } from '../src/data/site.mjs';
import { fileOfRoute } from '../src/lib/agent-md/content.mjs';
import { CONTENT_DIR } from '../src/lib/agent-md/render.mjs';
import { codeLines } from '../src/lib/markdown-fences.mjs';
import { VERIFIED_BY_ATTRIBUTE } from '../src/lib/page-markdown.mjs';
import { isRedirectStub, markupOf, tags, walk } from './shared/dist-pages.mjs';

/** The section of the API reference, in English and served under /es/. */
const API = /^\/reference\/api\//u;
const API_FALLBACK = /^\/es\/reference\/api\//u;
const CATALOGUE = /^\/(?:es\/)?reference\/catalogues\/[^/]+\/$/u;
const ERRATA_FAMILY = /^\/(?:es\/)?reference\/errata\/[^/]+\/$/u;
const HOMES = new Set(['/', '/es/']);

/**
 * One built page, as the classes read it.
 *
 * @typedef {object} BuiltPage
 * @property {string} route  `/signals/levels/levels/`, `/es/`, `/404/`.
 * @property {string} html
 * @property {boolean} stub  One of the pages that send a retired address on.
 * @property {boolean} content  Built from a file under src/content/docs.
 */

/**
 * What each kind of page owes, and why. `twin` is `required` (the page has a
 * copy at `<route>index.md`), `forbidden` (it has none and announces none) or
 * `english` (it has none of its own and announces the English page's).
 *
 * @type {readonly { id: string, twin: 'required' | 'forbidden' | 'english', reason: string, matches: (page: BuiltPage) => boolean }[]}
 */
export const PAGE_CLASSES = Object.freeze([
  {
    id: 'home',
    twin: 'required',
    reason:
      'The two landing pages. Their layout is a component, and their copy is what an agent ' +
      'asking "what is this library" fetches first: tagline, readout, install line and areas.',
    matches: (page) => page.content && HOMES.has(page.route),
  },
  {
    id: 'api',
    twin: 'required',
    reason: 'The API reference, generated from the docstrings, in English only.',
    matches: (page) => page.content && API.test(page.route),
  },
  {
    id: 'catalogue',
    twin: 'required',
    reason: 'One published catalogue per page: its copy carries the tables the page draws.',
    matches: (page) => page.content && CATALOGUE.test(page.route),
  },
  {
    id: 'errata-family',
    twin: 'required',
    reason: 'One family of documents of the errata register per page.',
    matches: (page) => page.content && ERRATA_FAMILY.test(page.route),
  },
  {
    id: 'guide',
    twin: 'required',
    reason:
      'Every other page written as a file under src/content/docs: the guides, the topic ' +
      'overviews, the start pages and the reference pages, in both languages.',
    matches: (page) =>
      page.content &&
      !HOMES.has(page.route) &&
      !API.test(page.route) &&
      !CATALOGUE.test(page.route) &&
      !ERRATA_FAMILY.test(page.route),
  },
  {
    id: 'api-fallback',
    twin: 'english',
    reason:
      'The English API reference served under /es/ as fallback content: it has no file and no ' +
      'copy of its own, and the copy of the text it shows is the English page\'s.',
    matches: (page) => !page.content && !page.stub && API_FALLBACK.test(page.route),
  },
  {
    id: 'redirect-stub',
    twin: 'forbidden',
    reason: 'A page that only sends a retired address to its new one has nothing to copy.',
    matches: (page) => page.stub,
  },
  {
    id: 'not-found',
    twin: 'forbidden',
    reason: 'The error page Starlight synthesises: no file, nothing a reader looks up.',
    matches: (page) => !page.content && !page.stub && page.route === '/404/',
  },
]);

/** What to do about each kind of finding, printed once under the findings. */
export const REMEDIES = Object.freeze({
  class:
    'A new kind of page owes a decision, not a silent skip: add a PAGE_CLASSES entry with ' +
    'what it owes and a reason, or remove the entry no page matches any more.',
  copy:
    'The copies are written before the build by `node scripts/agent-md.mjs --public` (package.json ' +
    '`prebuild`); a page written as a file gets one through src/lib/page-markdown.mjs ' +
    '`hasMarkdownCopy`. A copy with no page is left over from a page that moved: run the build ' +
    'again from a clean public/.',
  announce:
    'The head link and the structured data name the copy src/routeData.ts gives the page ' +
    '(`markdownCopy`); Head.astro writes both from it.',
  header:
    'The header is written by src/lib/agent-md/header.mjs from the page and from the modules ' +
    'that publish each value on the site; fix the value at its source.',
  text:
    'Something reached the copy that a reader of Markdown cannot use: a component or raw HTML ' +
    'with no writer or rule (src/lib/agent-md/render.mjs), an MDX expression, an aside, a link ' +
    'that only resolves on the site, or one written relative to the file the text came from. ' +
    '`pnpm run check:markdown-writers` names the source.',
});

/** CommonMark, GitHub tables and maths: how an agent's Markdown reader reads a copy. */
const READER = unified().use(remarkParse).use(remarkGfm).use(remarkMath).freeze();

/** A destination that resolves wherever the copy is read: a scheme, `//` or only a fragment. */
const WHOLE_DESTINATION = /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/iu;

/** A `{name}` or `{a.b}` an MDX expression left behind; `Re{Y}` (prose notation) is not one. */
const EXPRESSION = /(?<![\w$\\])\{\s*[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*\s*\}/u;

/**
 * The rule-breaking nodes of a copy, read one top-level section at a time.
 *
 * @param {string} text  The copy.
 * @returns {string[]}  `line N: what`, in reading order.
 */
export function textProblems(text) {
  const lines = text.split('\n');
  const inCode = codeLines(lines);
  /** @type {number[]} */
  const starts = [0];
  for (let i = 1; i < lines.length; i += 1) {
    if (!inCode[i] && /^#{1,2} /u.test(lines[i])) starts.push(i);
  }
  starts.push(lines.length);
  /** @type {string[]} */
  const problems = [];
  for (let s = 0; s + 1 < starts.length; s += 1) {
    const offset = starts[s];
    const chunk = lines.slice(offset, starts[s + 1]).join('\n');
    const tree = READER.parse(chunk);
    // Code, inline code and TeX are `code`, `inlineCode`, `math` and
    // `inlineMath` nodes, which no rule below reads: their braces and `<` are
    // content.
    const visit = (node) => {
      const at = `line ${offset + (node.position?.start.line ?? 1)}`;
      if (node.type === 'html') {
        const value = String(node.value ?? '').trim();
        const what = value.startsWith('<!--')
          ? 'an HTML comment'
          : /^<\/?[A-Z]/u.test(value)
            ? 'a component tag'
            : 'raw HTML';
        problems.push(`${at}: ${what}, ${JSON.stringify(value.slice(0, 60))}`);
      } else if (node.type === 'text') {
        // Read as written, where `\{` is still escaped: the parsed value has
        // lost the backslash a page writes to print a brace.
        const value = chunk.slice(node.position?.start.offset ?? 0, node.position?.end.offset ?? 0);
        const leaked = EXPRESSION.exec(value);
        if (leaked) problems.push(`${at}: an MDX expression, ${JSON.stringify(leaked[0])}`);
        if (/(?:^|\n):::/u.test(value)) problems.push(`${at}: the ::: of an aside`);
      } else if (['link', 'image', 'definition'].includes(node.type)) {
        const url = String(node.url ?? '');
        if (url.startsWith('/') && !url.startsWith('//')) {
          problems.push(`${at}: a link that only resolves on the site, ${JSON.stringify(url)}`);
        } else if (url !== '' && !WHOLE_DESTINATION.test(url)) {
          // A copy is read at the site's address, in an llms file and on
          // disk: a link relative to the file its text came from (the
          // conformance report's to its data) resolves to nothing there.
          problems.push(`${at}: a link that resolves only beside the file its text came from, ${JSON.stringify(url)}`);
        }
      }
      for (const child of node.children ?? []) visit(child);
    };
    visit(tree);
  }
  return problems;
}

/**
 * The `Key: value` lines of a copy's header: the block between the title and
 * the `---` that ends it.
 *
 * @param {string} text
 * @returns {Map<string, string> | undefined}  Nothing when the copy has no header.
 */
export function headerOf(text) {
  const lines = text.split('\n');
  const end = lines.indexOf('---');
  if (end === -1) return undefined;
  /** @type {Map<string, string>} */
  const fields = new Map();
  for (const one of lines.slice(1, end)) {
    const field = /^([A-Z][A-Za-z-]*): (.*)$/u.exec(one);
    if (field) fields.set(field[1], field[2]);
  }
  return fields.size > 0 ? fields : undefined;
}

/**
 * Every structured-data node of a page, at any depth.
 *
 * @param {string} html
 * @returns {Generator<Record<string, unknown>>}
 */
function* jsonLdNodes(html) {
  for (const [, body] of html.matchAll(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gu)) {
    let data;
    try {
      data = JSON.parse(body);
    } catch {
      continue;
    }
    const stack = [data];
    while (stack.length > 0) {
      const node = stack.pop();
      if (Array.isArray(node)) stack.push(...node);
      else if (node && typeof node === 'object') {
        yield /** @type {Record<string, unknown>} */ (node);
        stack.push(...Object.values(node));
      }
    }
  }
}

/** A site address or path as a route of the build: `/phonometry/x/` -> `/x/`. */
function routeOfAddress(address) {
  let path = address;
  try {
    path = new URL(address, `${siteUrl}/`).pathname;
  } catch {
    return address;
  }
  return path.startsWith(`${basePath}/`) ? path.slice(basePath.length) : path;
}

/** The copy's route for a page's route: `/x/` -> `/x/index.md`. */
const copyOf = (route) => `${route}index.md`;

/**
 * Every `.md` file of the build, as routes.
 *
 * @param {string} dir
 * @param {string} [route]
 * @param {string[]} [out]
 * @returns {string[]}
 */
function markdownFiles(dir, route = '/', out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) markdownFiles(join(dir, entry.name), `${route}${entry.name}/`, out);
    else if (entry.name.endsWith('.md')) out.push(`${route}${entry.name}`);
  }
  return out;
}

/**
 * `<loc>` -> `<lastmod>` for every page the sitemap lists.
 *
 * @param {string} dist
 * @returns {Map<string, string>}  Route -> `YYYY-MM-DD`.
 */
function sitemapDates(dist) {
  const index = join(dist, 'sitemap-index.xml');
  if (!existsSync(index)) throw new Error(`${index} does not exist: the build has no sitemap to read dates from.`);
  /** @type {Map<string, string>} */
  const dates = new Map();
  for (const [, shard] of readFileSync(index, 'utf8').matchAll(/<loc>([^<]+)<\/loc>/gu)) {
    const file = join(dist, routeOfAddress(shard));
    if (!existsSync(file)) throw new Error(`the sitemap index lists ${shard}, which the build did not write.`);
    for (const [, loc, lastmod] of readFileSync(file, 'utf8').matchAll(
      /<url>\s*<loc>([^<]+)<\/loc>(?:\s*<lastmod>([^<]+)<\/lastmod>)?/gu,
    )) {
      dates.set(routeOfAddress(loc), (lastmod ?? '').slice(0, 10));
    }
  }
  return dates;
}

/**
 * Runs every rule on a build.
 *
 * @param {string} dist
 * @param {{ contentDir?: string }} [options]
 * @returns {{ findings: Map<keyof typeof REMEDIES, string[]>, stats: { pages: number, copies: number, classes: Record<string, number> } }}
 */
export function checkMarkdownTwins(dist, { contentDir = CONTENT_DIR } = {}) {
  /** @type {Map<keyof typeof REMEDIES, string[]>} */
  const findings = new Map(Object.keys(REMEDIES).map((kind) => [/** @type {keyof typeof REMEDIES} */ (kind), []]));
  const add = (kind, message) => findings.get(kind)?.push(message);

  const built = walk(dist);
  /** @type {Map<string, BuiltPage>} */
  const pages = new Map();
  for (const [route, file] of built) {
    const html = readFileSync(file, 'utf8');
    const stub = isRedirectStub(html);
    const content = !stub && fileOfRoute(route.replace(/^\/|\/$/gu, ''), contentDir) !== undefined;
    pages.set(route, { route, html, stub, content });
  }
  const copies = new Set(markdownFiles(dist));
  const dates = sitemapDates(dist);

  // Every .md of the build is the copy of a page that was built.
  for (const copy of [...copies].sort()) {
    if (!copy.endsWith('/index.md')) add('copy', `${copy} is not a copy: every copy is <page>/index.md`);
    else if (!pages.has(copy.slice(0, -'index.md'.length))) add('copy', `${copy} has no page beside it`);
  }

  /** @type {Record<string, number>} */
  const counted = Object.fromEntries(PAGE_CLASSES.map((one) => [one.id, 0]));
  for (const page of [...pages.values()].sort((a, b) => a.route.localeCompare(b.route))) {
    const hits = PAGE_CLASSES.filter((one) => one.matches(page));
    if (hits.length !== 1) {
      add(
        'class',
        hits.length === 0
          ? `${page.route} matches no page class`
          : `${page.route} matches ${hits.map((one) => one.id).join(' and ')}: the classes must not overlap`,
      );
      continue;
    }
    const [pageClass] = hits;
    counted[pageClass.id] += 1;
    checkPage(page, pageClass.twin, { dist, copies, dates, add });
  }
  for (const [id, count] of Object.entries(counted)) {
    if (count === 0) add('class', `the page class "${id}" matches no page of the build: remove it`);
  }
  return { findings, stats: { pages: pages.size, copies: copies.size, classes: counted } };
}

/**
 * The rules one page and its copy are held to.
 *
 * @param {BuiltPage} page
 * @param {'required' | 'forbidden' | 'english'} owes
 * @param {{ dist: string, copies: Set<string>, dates: Map<string, string>, add: (kind: keyof typeof REMEDIES, message: string) => void }} context
 */
function checkPage(page, owes, { dist, copies, dates, add }) {
  const { route, html } = page;
  const copy = copyOf(route);
  const announced = tags(html, 'link')
    .filter((link) => (link.rel ?? '').split(/\s+/u).includes('alternate') && (link.type ?? '').startsWith('text/markdown'))
    .map((link) => routeOfAddress(link.href ?? ''));
  const encodings = [...jsonLdNodes(html)]
    .map((node) => /** @type {Record<string, unknown> | undefined} */ (node.encoding))
    .filter((encoding) => encoding && encoding.encodingFormat === 'text/markdown')
    .map((encoding) => routeOfAddress(String(encoding?.contentUrl ?? '')));

  if (owes !== 'required') {
    if (copies.has(copy)) add('copy', `${route} has a copy at ${copy}, and pages of its kind have none of their own`);
    const expected = owes === 'english' ? [copyOf(route.replace(/^\/es\//u, '/'))] : [];
    if (owes === 'english' && !copies.has(expected[0])) {
      add('copy', `${route} shows the English page, whose copy ${expected[0]} was not built`);
    }
    if (announced.join() !== expected.join()) {
      add('announce', `${route} announces ${announced.join(', ') || 'no copy'} in its head, not ${expected.join(', ') || 'none'}`);
    }
    if (encodings.join() !== expected.join()) {
      add('announce', `${route} declares ${encodings.join(', ') || 'no copy'} in its structured data, not ${expected.join(', ') || 'none'}`);
    }
    return;
  }

  if (!copies.has(copy)) {
    add('copy', `${route} has no copy (expected ${copy})`);
    return;
  }
  if (announced.length !== 1 || announced[0] !== copy) {
    add('announce', `${route} announces ${announced.join(', ') || 'no copy'} in its head, not ${copy}`);
  }
  if (encodings.length !== 1 || encodings[0] !== copy) {
    add('announce', `${route} declares ${encodings.join(', ') || 'no copy'} in its structured data, not ${copy}`);
  }

  const text = readFileSync(join(dist, copy), 'utf8');
  if (!/^# \S/u.test(text)) add('header', `${copy} does not open with its title as a "# " heading`);
  const fields = headerOf(text);
  if (!fields) {
    add('header', `${copy} has no header`);
  } else {
    const canonical = tags(html, 'link').find((link) => link.rel === 'canonical')?.href;
    if (fields.get('Canonical') !== canonical) {
      add('header', `${copy} says "Canonical: ${fields.get('Canonical') ?? ''}", and the page's canonical is ${canonical}`);
    }
    const lang = /^\/es(\/|$)/u.test(route) ? 'es' : 'en';
    if (fields.get('Language') !== lang) add('header', `${copy} says "Language: ${fields.get('Language') ?? ''}", not ${lang}`);
    const lastmod = dates.get(route);
    if (!lastmod) add('header', `${route} has a copy and no <lastmod> in the sitemap: nothing dates it`);
    else if (fields.get('Updated') !== lastmod) {
      add('header', `${copy} says "Updated: ${fields.get('Updated') ?? ''}", and the sitemap dates the page ${lastmod}`);
    }
    const other = tags(html, 'link').find(
      (link) => link.rel === 'alternate' && link.hreflang && link.hreflang !== 'x-default' && link.hreflang !== lang,
    );
    const alternate = other ? copyOf(routeOfAddress(other.href ?? '')) : undefined;
    const printed = fields.has('Alternate') ? routeOfAddress(fields.get('Alternate') ?? '') : undefined;
    if (printed !== alternate) {
      add('header', `${copy} names ${printed ?? 'no'} copy in the other language, and the page's translation is ${alternate ?? 'none'}`);
    } else if (alternate && !copies.has(alternate)) {
      add('header', `${copy} names ${alternate} as its copy in the other language, which was not built`);
    }
    const verifiedOnPage = new RegExp(`\\s${VERIFIED_BY_ATTRIBUTE}[\\s=>]`, 'u').test(markupOf(html));
    if (verifiedOnPage !== fields.has('Verified')) {
      add(
        'header',
        verifiedOnPage
          ? `${route} states the conformance checks that verify it, and ${copy} has no "Verified:" line`
          : `${copy} has a "Verified:" line, and ${route} states no conformance check`,
      );
    }
  }
  for (const problem of textProblems(text)) add('text', `${copy} ${problem}`);
}

/** The ok/FAIL lines of one group of findings, the first few spelled out. */
const SHOWN = 12;

function main() {
  const here = dirname(fileURLToPath(import.meta.url));
  const dist = resolve(process.argv[2] ?? join(here, '..', 'dist'));
  if (!existsSync(dist) || !statSync(dist).isDirectory() || !existsSync(join(dist, 'index.html'))) {
    console.error(`[markdown-twins] ${dist} holds no built site: run the build first.`);
    process.exitCode = 2;
    return;
  }
  let result;
  try {
    result = checkMarkdownTwins(dist);
  } catch (error) {
    console.error(`[markdown-twins] could not run: ${error instanceof Error ? error.message : error}`);
    process.exitCode = 2;
    return;
  }
  const { findings, stats } = result;
  const what = {
    class: 'page(s) or class(es) outside the table of page classes',
    copy: 'missing, extra or misplaced copy(ies)',
    announce: 'page(s) announcing a copy other than their own',
    header: 'copy header(s) that disagree with their page',
    text: 'place(s) in the copies a Markdown reader cannot use',
  };
  let failed = 0;
  for (const [kind, list] of findings) {
    if (list.length === 0) continue;
    failed += list.length;
    const shown = list.slice(0, SHOWN).map((line) => `\n       ${line}`).join('');
    const more = list.length > SHOWN ? `\n       ... and ${list.length - SHOWN} more` : '';
    console.error(`FAIL ${list.length} ${what[kind]}:${shown}${more}\n     Remedy: ${REMEDIES[kind]}`);
  }
  const classes = Object.entries(stats.classes)
    .map(([id, count]) => `${id} ${count}`)
    .join(', ');
  if (failed > 0) {
    console.error(`[markdown-twins] ${failed} finding(s) on ${stats.pages} pages and ${stats.copies} copies.`);
    process.exitCode = 1;
    return;
  }
  console.log(
    `ok   every page's Markdown copy carries what the page carries: ${stats.pages} pages ` +
      `(${classes}), ${stats.copies} copies`,
  );
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();

