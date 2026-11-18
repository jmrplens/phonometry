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
//   4. the sitemap                 the <lastmod> whose day the copy's
//                                  `Updated:` names
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
// THE HEADER IS HELD TO THE PAGE, NOT TO THE MODULES ITS WRITER READS. The
// copy's title is the page's <title> without the site's name; `Canonical:`,
// `Language:`, `Summary:` and `Published:` are the page's canonical link, its
// language, its meta description and the `datePublished` of the node that
// declares the copy; `Updated:` is the moment the last <time datetime> of the
// page's footer gives, to the second, on the day of the sitemap's <lastmod>
// (the edge serves the page's Last-Modified from the one and the copy's from
// the other, and a day alone would read as midnight); `Alternate:` is
// the copy of the page its hreflang link names; `Verified:` stands exactly
// where the page states its conformance checks; `Unreleased:` stands exactly
// where the page shows the notice that it changed after the latest release,
// and names the release the notice names; `License:` stands on every page but
// a catalogue. Only the release lines are read from the release: `Version:`
// names the VERSION being built, and every key of `releaseHeaderKeys` but the
// two that stand on some pages only, and `Author:`, are there.
//
// THE BODY HAS TO BE THERE. A copy of a page that owes one has text between its
// header and its references, and a catalogue's copy has as many table rows as
// the page's tables have rows in their bodies: a copy that lost the data is
// the defect the copies cut out of the source had.
//
// THE TEXT RULES ARE READ ON THE PARSED COPY, NOT ON ITS RAW TEXT. Outside
// code, inline code and maths, a copy may hold no raw HTML (a component's tag
// or an HTML comment the source carried), no `{name}`, `{a.b}` or `{f(...)}`
// an MDX expression left behind (in the text or in an image's alt text), no
// `:::` of an aside and no link that starts with `/`. Read on the raw text,
// the same rules would fail on what the copies keep on purpose: the TeX of
// 642 pages, `$L_\mathrm{Ceq} - L_\mathrm{Aeq}$`, sits between braces, and
// an API page prints `(EAV\<=value\<ELV)`, where the backslash makes the `<`
// text. A copy is parsed as an agent's Markdown reader parses it
// (CommonMark, GitHub tables and maths), one top-level section at a time,
// because the table parser's cost grows with the square of the rows in one
// document and the conformance report's copy holds a hundred tables.
//
// THE LLMS FILES CARRY THE COPIES, BYTE FOR BYTE. Every English page whose
// whole text the llms files carry (src/lib/page-markdown.mjs
// `FULL_TEXT_KINDS`: the guides, the catalogues and the errata families) is in
// exactly one shard of llms/ and once in llms-full.txt, as its copy reads,
// header included; no other page is in either. A page too long for one fetch
// is cut into the numbered parts of its shard, each part opening with the
// page's own head, and joined back in order it is the copy again; a part that
// continues a table opens with that table's header row and delimiter row,
// which are taken out before the parts are joined. The files used to be cut
// from the hand-written mirror under docs/, so what an agent fetched there was
// not what the page said; they are written now from the same copies
// (scripts/generate_llms.py --build, package.json `prebuild`), and this reads
// what the build published. llms.txt links exactly the shard files the build
// wrote.
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
import { parse as parseYaml } from 'yaml';

import { preRelease, version } from '../src/data/repo-stats.mjs';
import { basePath, siteTitle, siteUrl } from '../src/data/site.mjs';
import { catalogueSlugs } from '../src/data/topics.mjs';
import { fileOfRoute } from '../src/lib/agent-md/content.mjs';
import { LEAD_OPENING, PRE_RELEASE, UNRELEASED } from '../src/lib/agent-md/header.mjs';
import { REFERENCES_HEADING } from '../src/lib/agent-md/page.mjs';
import { CONTENT_DIR } from '../src/lib/agent-md/render.mjs';
import { rewrittenSource } from '../src/lib/agent-md/rewrites.mjs';
import { readCommittedText } from '../src/lib/line-ends.mjs';
import { codeLines } from '../src/lib/markdown-fences.mjs';
import {
  FULL_TEXT_KINDS,
  NEWER_THAN_RELEASE_ATTRIBUTE,
  VERIFIED_BY_ATTRIBUTE,
  pageKind,
  releaseHeaderKeys,
} from '../src/lib/page-markdown.mjs';
import { decode, isRedirectStub, markupOf, tags, walk } from './shared/dist-pages.mjs';
import { copyDefects, frontmatterSource, headingText, stripFrontmatter } from './shared/page-twin.mjs';

/** The `Updated:` value src/lib/agent-md/header.mjs writes: a moment in UTC, to the second. */
const UPDATED_MOMENT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/u;

/** The API reference served under /es/, which has no file of its own. */
const API_FALLBACK = /^\/es\/reference\/api\//u;

/** The kind of a page written as a file (src/lib/page-markdown.mjs `pageKind`). */
const kindOf = (page) => page.content && pageKind(page.route);

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
    matches: (page) => kindOf(page) === 'home',
  },
  {
    id: 'api',
    twin: 'required',
    reason: 'The API reference, generated from the docstrings, in English only.',
    matches: (page) => kindOf(page) === 'api',
  },
  {
    id: 'catalogue',
    twin: 'required',
    reason: 'One published catalogue per page: its copy carries the tables the page draws.',
    matches: (page) => kindOf(page) === 'catalogue',
  },
  {
    id: 'errata-family',
    twin: 'required',
    reason: 'One family of documents of the errata register per page.',
    matches: (page) => kindOf(page) === 'errata-family',
  },
  {
    id: 'guide',
    twin: 'required',
    reason:
      'Every other page written as a file under src/content/docs: the guides, the topic ' +
      'overviews, the start pages and the reference pages, in both languages.',
    matches: (page) => kindOf(page) === 'guide',
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
  body:
    'The body is written from the page source by src/lib/agent-md/render.mjs and the writer ' +
    'beside each component; `node scripts/agent-md.mjs --page <route>` prints one copy, to ' +
    'compare with the page.',
  text:
    'Something reached the copy that a reader of Markdown cannot use: a component or raw HTML ' +
    'with no writer or rule (src/lib/agent-md/render.mjs), an MDX expression, an aside, a link ' +
    'that only resolves on the site, or one written relative to the file the text came from. ' +
    '`pnpm run check:markdown-writers` names the source.',
  llms:
    'The llms files are written before the build by `python3 ../scripts/generate_llms.py ' +
    '--pages ../build/agent-md --build` from the copies `node scripts/agent-md.mjs --public ' +
    '--dump ../build/agent-md` writes in the same run (package.json `prebuild`): a page that ' +
    'differs from its copy, is missing or is there twice was written from another run, or the ' +
    'generator cut it wrong. Build again from a clean public/, and fix the generator if it persists.',
});

/** CommonMark, GitHub tables and maths: how an agent's Markdown reader reads a copy. */
const READER = unified().use(remarkParse).use(remarkGfm).use(remarkMath).freeze();

/** A destination that resolves wherever the copy is read: a scheme, `//` or only a fragment. */
const WHOLE_DESTINATION = /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/iu;

/**
 * The opening of an expression an MDX page left behind: `{name}`, `{a.b}`,
 * `{f(x)}`, `{a?.b}`, `{list[0]}`. A brace a page escaped (`\{`) and prose
 * notation such as `Re{Y}` are not one.
 */
const EXPRESSION = /(?<![\w$\\])\{\s*[A-Za-z_$][\w$]*\s*[.(?[}]/u;

/**
 * The expression a piece of text holds, from its `{` to the brace that closes
 * it (at most 60 characters), or nothing.
 *
 * @param {string} value
 * @returns {string | undefined}
 */
function expressionIn(value) {
  const found = EXPRESSION.exec(value);
  if (!found) return undefined;
  const close = value.indexOf('}', found.index);
  return value.slice(found.index, close === -1 ? found.index + 60 : Math.min(close + 1, found.index + 60));
}

/**
 * A copy cut into its top-level sections and parsed as a reader parses it, one
 * section at a time: the table parser's cost grows with the square of the rows
 * in one document.
 *
 * @param {string} text  The copy.
 * @returns {Generator<{ offset: number, chunk: string, tree: import('mdast').Root }>}
 *   `offset` is the line the section starts at, counting from 0.
 */
function* sections(text) {
  const lines = text.split('\n');
  const inCode = codeLines(lines);
  /** @type {number[]} */
  const starts = [0];
  for (let i = 1; i < lines.length; i += 1) {
    if (!inCode[i] && /^#{1,2} /u.test(lines[i])) starts.push(i);
  }
  starts.push(lines.length);
  for (let s = 0; s + 1 < starts.length; s += 1) {
    const chunk = lines.slice(starts[s], starts[s + 1]).join('\n');
    yield { offset: starts[s], chunk, tree: READER.parse(chunk) };
  }
}

/**
 * The data rows of a copy's tables: every row of every table but its header.
 *
 * @param {string} text  The copy.
 * @returns {number}
 */
export function dataRows(text) {
  let rows = 0;
  const visit = (node) => {
    if (node.type === 'table') rows += Math.max(0, (node.children?.length ?? 0) - 1);
    for (const child of node.children ?? []) visit(child);
  };
  for (const { tree } of sections(text)) visit(tree);
  return rows;
}

/**
 * The rows in the bodies of a page's tables, as the page shows them.
 *
 * @param {string} html
 * @returns {number}
 */
export function rowsOnPage(html) {
  let rows = 0;
  for (const [, body] of markupOf(html).matchAll(/<tbody\b[^>]*>([\s\S]*?)<\/tbody>/gu)) {
    rows += body.match(/<tr\b/gu)?.length ?? 0;
  }
  return rows;
}

/**
 * The text of a copy between the header's closing `---` and the References
 * section the copy ends with.
 *
 * @param {string} text  The copy.
 * @param {'en' | 'es'} lang
 * @returns {string}  Trimmed; `''` when there is none, or no header to end.
 */
export function bodyOf(text, lang) {
  const lines = text.split('\n');
  const end = lines.indexOf('---');
  if (end === -1) return '';
  const rest = lines.slice(end + 1);
  const references = rest.lastIndexOf(`## ${REFERENCES_HEADING[lang]}`);
  return (references === -1 ? rest : rest.slice(0, references)).join('\n').trim();
}

/**
 * The rule-breaking nodes of a copy, read one top-level section at a time.
 *
 * @param {string} text  The copy.
 * @returns {string[]}  `line N: what`, in reading order.
 */
export function textProblems(text) {
  /** @type {string[]} */
  const problems = [];
  for (const { offset, chunk, tree } of sections(text)) {
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
        const leaked = expressionIn(value);
        if (leaked) problems.push(`${at}: an MDX expression, ${JSON.stringify(leaked)}`);
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
        const inAlt = node.type === 'image' ? expressionIn(String(node.alt ?? '')) : undefined;
        if (inAlt) problems.push(`${at}: an MDX expression in alt text, ${JSON.stringify(inAlt)}`);
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

/** What closes every page in a shard and in llms-full.txt (scripts/generate_llms.py `PAGE_END`). */
export const PAGE_END = '\n\n---\n';

/** A link of llms.txt to a shard file, capturing its name. */
const SHARD_LINK = /\/llms\/(llms-[a-z0-9-]+\.txt)\b/gu;

/** A row of a GitHub table, and the delimiter row under its header row. */
const TABLE_ROW = /^ {0,3}\|/u;
const TABLE_DELIMITER = /^ {0,3}\|?(?: *:?-+:? *\|)+ *:?-*:? *$/u;

/**
 * The pages an llms file carries, in order. Each opens as a copy does, with a
 * `# ` title, a blank line and the sentence under it (src/lib/agent-md/header.mjs
 * `LEAD_OPENING`), and is closed by {@link PAGE_END}; the file's own head (or
 * llms.txt, at the top of llms-full.txt) comes before the first.
 *
 * @param {string} text
 * @returns {{ pages: { text: string, canonical: string | undefined }[], problems: string[] }}
 */
export function llmsPages(text) {
  const lines = text.split('\n');
  const inCode = codeLines(lines);
  const leads = Object.values(LEAD_OPENING).map((opening) => `> ${opening}`);
  /** @type {number[]} */
  const starts = [];
  let offset = 0;
  for (let i = 0; i < lines.length; i += 1) {
    if (
      !inCode[i] &&
      lines[i].startsWith('# ') &&
      lines[i + 1] === '' &&
      leads.some((lead) => (lines[i + 2] ?? '').startsWith(lead))
    ) {
      starts.push(offset);
    }
    offset += lines[i].length + 1;
  }
  /** @type {{ text: string, canonical: string | undefined }[]} */
  const pages = [];
  /** @type {string[]} */
  const problems = [];
  starts.forEach((start, index) => {
    const last = index + 1 === starts.length;
    const raw = text.slice(start, last ? text.length : starts[index + 1]);
    const end = last ? PAGE_END : `${PAGE_END}\n`;
    if (!raw.endsWith(end)) {
      problems.push(`the page that opens "${raw.slice(0, raw.indexOf('\n'))}" is not closed by a blank line and a "---" rule before what follows`);
      return;
    }
    const page = raw.slice(0, -end.length);
    pages.push({ text: page, canonical: /^Canonical: (\S+)$/mu.exec(page.slice(0, page.indexOf('\n---\n') + 1 || undefined))?.[1] });
  });
  return { pages, problems };
}

/**
 * A copy, or a page in an llms file, as its head (the title through the rule
 * that closes the header) and the lines after it.
 *
 * @param {string} text  Without the copy's final newline.
 * @returns {{ head: string, rest: string[] } | undefined}
 */
export function headAndRest(text) {
  const lines = text.split('\n');
  const close = lines.indexOf('---', 3);
  if (close === -1) return undefined;
  const rest = lines.slice(close + 1);
  if (rest[0] === '') rest.shift();
  return { head: lines.slice(0, close + 1).join('\n'), rest };
}

/**
 * The header row and delimiter row of the table some lines end inside, when
 * they end on a row of one.
 *
 * @param {readonly string[]} lines
 * @returns {[string, string] | undefined}
 */
function tableEndedIn(lines) {
  if (!TABLE_ROW.test(lines.at(-1) ?? '')) return undefined;
  let first = lines.length - 1;
  while (first > 0 && TABLE_ROW.test(lines[first - 1])) first -= 1;
  for (let i = first + 1; i < lines.length; i += 1) {
    if (TABLE_DELIMITER.test(lines[i])) return [lines[i - 1], lines[i]];
  }
  return undefined;
}

/**
 * The text of a page cut into parts, joined back: the rest of each part after
 * the first, without the table header a part repeats when it opens in the
 * middle of a table, follows the rest of the one before.
 *
 * @param {readonly string[][]} rests
 * @returns {string[]}
 */
export function joinedParts(rests) {
  const joined = [...(rests[0] ?? [])];
  for (const rest of rests.slice(1)) {
    const header = tableEndedIn(joined);
    const repeats = header && rest[0] === header[0] && rest[1] === header[1];
    joined.push(...(repeats ? rest.slice(2) : rest));
  }
  return joined;
}

/**
 * The shard files of a build, grouped into shards: a shard in one file, or
 * the numbered parts of one, in order.
 *
 * @param {string[]} names  `llms-<slug>.txt` file names.
 * @param {(name: string) => string} read
 * @returns {{ shards: Map<string, string[]>, problems: string[] }}
 */
function shardsOf(names, read) {
  /** @type {Map<string, string[]>} */
  const shards = new Map();
  /** @type {string[]} */
  const problems = [];
  /** @type {Map<string, Map<number, string>>} */
  const parts = new Map();
  /** @type {Map<string, number>} */
  const counts = new Map();
  for (const name of names) {
    const title = read(name).split('\n', 1)[0];
    const part = /, part (\d+) of (\d+)$/u.exec(title);
    const numbered = /^llms-(.+)-(\d+)\.txt$/u.exec(name);
    if (!part) {
      shards.set(name, [name]);
      continue;
    }
    if (!numbered || Number(numbered[2]) !== Number(part[1])) {
      problems.push(`llms/${name} opens as part ${part[1]} of ${part[2]} and is not named llms-<shard>-${part[1]}.txt`);
      continue;
    }
    const slug = numbered[1];
    if (Number(part[1]) < 1 || Number(part[1]) > Number(part[2])) {
      problems.push(`llms/${name} opens as part ${part[1]} of ${part[2]}, past the parts llms-${slug} is cut into`);
    }
    if (!parts.has(slug)) parts.set(slug, new Map());
    parts.get(slug)?.set(Number(part[1]), name);
    if ((counts.get(slug) ?? Number(part[2])) !== Number(part[2])) {
      problems.push(`the parts of llms-${slug} disagree on how many there are`);
    }
    counts.set(slug, Number(part[2]));
  }
  for (const [slug, found] of parts) {
    const count = counts.get(slug) ?? 0;
    const names = Array.from({ length: count }, (_, i) => found.get(i + 1));
    if (names.some((name) => name === undefined) || found.size !== count) {
      problems.push(`llms-${slug} is cut into ${count} parts and the build wrote ${found.size} of them`);
    }
    shards.set(`llms-${slug}`, names.filter((name) => name !== undefined));
  }
  return { shards, problems };
}

/**
 * Holds the llms files of a build to the copies they carry.
 *
 * @param {string} dist
 * @param {Map<string, BuiltPage>} pages
 * @param {(kind: keyof typeof REMEDIES, message: string) => void} add
 * @returns {{ files: number, pages: number }}
 */
export function checkLlmsFiles(dist, pages, add) {
  const index = join(dist, 'llms.txt');
  const full = join(dist, 'llms-full.txt');
  const dir = join(dist, 'llms');
  const missing = [index, full, dir].filter((path) => !existsSync(path));
  if (missing.length > 0) {
    add('llms', `the build has no ${missing.map((path) => path.slice(dist.length + 1)).join(', ')}`);
    return { files: 0, pages: 0 };
  }
  const names = readdirSync(dir).filter((name) => /^llms-[a-z0-9-]+\.txt$/u.test(name)).sort();
  const linked = new Set([...readFileSync(index, 'utf8').matchAll(SHARD_LINK)].map((found) => found[1]));
  for (const name of names) if (!linked.has(name)) add('llms', `llms/${name} was built and llms.txt does not link it`);
  for (const name of [...linked].sort()) if (!names.includes(name)) add('llms', `llms.txt links llms/${name}, which the build did not write`);

  // Every English page whose whole text the llms files carry, with its copy:
  // a page whose copy is missing is the copy rule's finding, not this one's.
  /** @type {Map<string, string>} */
  const owed = new Map();
  for (const page of pages.values()) {
    const kind = kindOf(page);
    const copy = join(dist, copyOf(page.route));
    if (kind && FULL_TEXT_KINDS.includes(kind) && !page.route.startsWith('/es/') && existsSync(copy)) {
      owed.set(page.route, readFileSync(copy, 'utf8'));
    }
  }
  // A page of an llms file is found by its text, which is its copy's, or by
  // its head, which every part of a page cut into parts repeats; only a page
  // that is neither is placed by its "Canonical:" line. A copy whose own
  // header is wrong is then the header rule's finding and not this one's too.
  /** @type {Map<string, string>} */
  const byText = new Map();
  /** @type {Map<string, string>} */
  const byHead = new Map();
  for (const [route, copy] of owed) {
    byText.set(copy.replace(/\n$/u, ''), route);
    const head = headAndRest(copy.replace(/\n$/u, ''))?.head;
    if (head) byHead.set(head, route);
  }
  const routeOfPage = (found, where) => {
    const known = byText.get(found.text) ?? byHead.get(headAndRest(found.text)?.head ?? '');
    if (known) return known;
    const route = found.canonical ? routeOfAddress(found.canonical) : undefined;
    if (!route) add('llms', `${where} carries a page with no "Canonical:" line`);
    else if (!owed.has(route)) {
      add('llms', `${where} carries ${route}, ${pages.has(route) ? 'whose whole text the llms files do not carry' : 'which is no page of the build'}`);
      return undefined;
    }
    return route;
  };

  // llms-full.txt: every page once, whole.
  const inFull = new Map();
  const fullPages = llmsPages(readFileSync(full, 'utf8'));
  for (const problem of fullPages.problems) add('llms', `llms-full.txt: ${problem}`);
  for (const found of fullPages.pages) {
    const route = routeOfPage(found, 'llms-full.txt');
    if (!route) continue;
    inFull.set(route, (inFull.get(route) ?? 0) + 1);
    if (`${found.text}\n` !== owed.get(route)) add('llms', `llms-full.txt carries ${route} other than its copy ${copyOf(route)}`);
  }

  // The shards: every page in exactly one, in one run across its parts.
  const read = (name) => readFileSync(join(dir, name), 'utf8');
  const grouped = shardsOf(names, read);
  for (const problem of grouped.problems) add('llms', problem);
  /** @type {Map<string, string>} */
  const shardOf = new Map();
  for (const [shard, files] of grouped.shards) {
    /** @type {{ route: string, texts: string[] }[]} */
    const runs = [];
    for (const name of files) {
      const found = llmsPages(read(name));
      for (const problem of found.problems) add('llms', `llms/${name}: ${problem}`);
      for (const one of found.pages) {
        const route = routeOfPage(one, `llms/${name}`);
        if (!route) continue;
        if (runs.at(-1)?.route === route) runs.at(-1)?.texts.push(one.text);
        else runs.push({ route, texts: [one.text] });
      }
    }
    for (const { route, texts } of runs) {
      if (shardOf.has(route)) {
        add('llms', `${route} is in ${shardOf.get(route)} and again in ${shard}`);
        continue;
      }
      shardOf.set(route, shard);
      const copy = owed.get(route) ?? '';
      if (texts.length === 1) {
        if (`${texts[0]}\n` !== copy) add('llms', `${shard} carries ${route} other than its copy ${copyOf(route)}`);
        continue;
      }
      const whole = headAndRest(copy.replace(/\n$/u, ''));
      const cut = texts.map(headAndRest);
      if (!whole || cut.some((part) => !part || part.head !== whole.head)) {
        add('llms', `${shard} cuts ${route} into ${texts.length} parts that do not each open with its copy's head`);
      } else if (joinedParts(cut.map((part) => part?.rest ?? [])).join('\n') !== whole.rest.join('\n')) {
        add('llms', `${shard} cuts ${route} into ${texts.length} parts that, joined in order, are not its copy ${copyOf(route)}`);
      }
    }
  }
  for (const route of [...owed.keys()].sort()) {
    if (!shardOf.has(route)) add('llms', `${route} is in no shard of llms/`);
    const times = inFull.get(route) ?? 0;
    if (times !== 1) add('llms', `${route} is in llms-full.txt ${times === 0 ? 'not at all' : `${times} times`}`);
  }
  return { files: names.length, pages: owed.size };
}

/**
 * Runs every rule on a build.
 *
 * @param {string} dist
 * @param {{ contentDir?: string, classes?: typeof PAGE_CLASSES }} [options]  `classes`
 *   replaces the table of page classes, for a test of the table's own rules.
 * @returns {{ findings: Map<keyof typeof REMEDIES, string[]>, stats: { pages: number, copies: number, classes: Record<string, number>, llms: { files: number, pages: number } } }}
 */
export function checkMarkdownTwins(dist, { contentDir = CONTENT_DIR, classes = PAGE_CLASSES } = {}) {
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
  const counted = Object.fromEntries(classes.map((one) => [one.id, 0]));
  for (const page of [...pages.values()].sort((a, b) => a.route.localeCompare(b.route))) {
    const hits = classes.filter((one) => one.matches(page));
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
    checkPage(page, pageClass, { dist, copies, dates, add });
  }
  for (const [id, count] of Object.entries(counted)) {
    if (count === 0) add('class', `the page class "${id}" matches no page of the build: remove it`);
  }
  const llms = checkLlmsFiles(dist, pages, add);
  return { findings, stats: { pages: pages.size, copies: copies.size, classes: counted, llms } };
}

/**
 * The rules one page and its copy are held to.
 *
 * @param {BuiltPage} page
 * @param {(typeof PAGE_CLASSES)[number]} pageClass
 * @param {{ dist: string, copies: Set<string>, dates: Map<string, string>, add: (kind: keyof typeof REMEDIES, message: string) => void }} context
 */
function checkPage(page, pageClass, { dist, copies, dates, add }) {
  const { route, html } = page;
  const owes = pageClass.twin;
  const copy = copyOf(route);
  const announced = tags(html, 'link')
    .filter((link) => (link.rel ?? '').split(/\s+/u).includes('alternate') && (link.type ?? '').startsWith('text/markdown'))
    .map((link) => routeOfAddress(link.href ?? ''));
  // The structured-data nodes that declare a copy, each with the address it gives.
  const carriers = [...jsonLdNodes(html)].filter((node) => {
    const encoding = /** @type {Record<string, unknown> | undefined} */ (node.encoding);
    return Boolean(encoding) && encoding?.encodingFormat === 'text/markdown';
  });
  const encodings = carriers.map((node) =>
    routeOfAddress(String(/** @type {Record<string, unknown>} */ (node.encoding).contentUrl ?? '')),
  );

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
  const lang = /^\/es(\/|$)/u.test(route) ? 'es' : 'en';
  if (/^# \S/u.test(text)) {
    // The page's <title> is "<title> | <site>", or the whole title on a page
    // that sets its own (the landing pages).
    const pageTitle = decode(/<title>([^<]*)<\/title>/u.exec(html)?.[1] ?? '');
    const suffix = ` | ${siteTitle}`;
    const title = pageTitle.endsWith(suffix) ? pageTitle.slice(0, -suffix.length) : pageTitle;
    // The copy writes the title so that Markdown prints it as the page does,
    // a mark escaped (src/lib/agent-md/markdown-table.mjs, titleMarkdown), so
    // the heading is read as Markdown reads it.
    const heading = text.slice(2, text.indexOf('\n') === -1 ? undefined : text.indexOf('\n'));
    if (headingText(heading) !== title) add('header', `${copy} is titled "${heading}", and the page's <title> names it "${title}"`);
  } else {
    add('header', `${copy} does not open with its title as a "# " heading`);
  }
  const fields = headerOf(text);
  if (!fields) {
    add('header', `${copy} has no header`);
  } else {
    /** What the copy states on one line: `says "Key: value"`, or that it has no such line. */
    const said = (key) => (fields.has(key) ? `says "${key}: ${fields.get(key)}"` : `has no "${key}:" line`);
    const canonical = tags(html, 'link').find((link) => link.rel === 'canonical')?.href;
    if (fields.get('Canonical') !== canonical) {
      add('header', `${copy} ${said('Canonical')}, and the page's canonical is ${canonical}`);
    }
    if (fields.get('Language') !== lang) add('header', `${copy} ${said('Language')}, not ${lang}`);
    const sometimes = new Set(['Unreleased', ...(preRelease ? [] : ['Pre-release'])]);
    for (const key of [...releaseHeaderKeys.filter((key) => !sometimes.has(key)), 'Author']) {
      if (!fields.has(key)) add('header', `${copy} has no "${key}:" line`);
    }
    // Read in the copy's own language, so a copy in the wrong one fails once, on Language:.
    const preLine = preRelease ? PRE_RELEASE[fields.get('Language') === 'es' ? 'es' : 'en'](version) : undefined;
    if (fields.get('Pre-release') !== preLine) {
      add('header', `${copy} ${said('Pre-release')}, and ${version} is ${preRelease ? `a pre-release: "Pre-release: ${preLine}"` : 'no pre-release'}`);
    }
    if (fields.has('Version') && fields.get('Version') !== `phonometry ${version}`) {
      add('header', `${copy} says "Version: ${fields.get('Version')}", and the build is of phonometry ${version}`);
    }
    const carrier = carriers[0];
    if (carrier) {
      const datePublished = typeof carrier.datePublished === 'string' ? carrier.datePublished.slice(0, 10) : undefined;
      if (fields.get('Published') !== datePublished) {
        add('header', `${copy} ${said('Published')}, and the page's structured data gives ${datePublished ?? 'no datePublished'}`);
      }
    }
    const lastmod = dates.get(route);
    const updated = fields.get('Updated');
    if (!lastmod) add('header', `${route} has a copy and no <lastmod> in the sitemap: nothing dates it`);
    else if (!UPDATED_MOMENT.test(updated ?? '')) {
      add(
        'header',
        `${copy} ${said('Updated')}${/^\d{4}-\d{2}-\d{2}$/u.test(updated ?? '') ? ', a day with no time' : ''}: ` +
          "the line states the moment the page's footer gives, as YYYY-MM-DDTHH:MM:SSZ",
      );
    } else if (updated?.slice(0, 10) !== lastmod) {
      add('header', `${copy} ${said('Updated')}, and the sitemap dates the page ${lastmod}`);
    } else {
      // The footer's last <time datetime> is where the edge reads the page's
      // Last-Modified, and the copy's Updated: line is where it reads the
      // copy's: the two name one moment.
      const footer = tags(html, 'time').map((time) => time.datetime).filter((at) => at !== undefined).at(-1);
      if (footer === undefined || Date.parse(footer) !== Date.parse(updated ?? '')) {
        add('header', `${copy} ${said('Updated')}, and the page's footer dates it ${footer ?? 'nowhere'}`);
      }
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
    // The notice under the title of a page changed after the latest release,
    // and the copy's line that says the same, in the copy's language.
    const notices = tags(html, 'p').filter((p) => Object.hasOwn(p, NEWER_THAN_RELEASE_ATTRIBUTE));
    const newerThan = notices.length === 1 ? notices[0][NEWER_THAN_RELEASE_ATTRIBUTE] : undefined;
    if (notices.length > 1) add('header', `${route} shows ${notices.length} notices that it changed after the release, not one`);
    const unreleasedLine = newerThan === undefined ? undefined : UNRELEASED[fields.get('Language') === 'es' ? 'es' : 'en'](newerThan);
    if (fields.get('Unreleased') !== unreleasedLine) {
      add(
        'header',
        newerThan === undefined
          ? `${copy} ${said('Unreleased')}, and ${route} shows no notice that it changed after the release`
          : `${copy} ${said('Unreleased')}, and ${route} shows the notice that it changed after phonometry ${newerThan}: "Unreleased: ${unreleasedLine}"`,
      );
    }
    if (newerThan !== undefined && newerThan !== version) {
      add('header', `${route} says it changed after phonometry ${newerThan}, and the build is of phonometry ${version}`);
    }
    // A catalogue transcribes published tables and carries no licence of its own.
    const licensed = pageClass.id !== 'catalogue';
    if (fields.has('License') !== licensed) {
      add('header', licensed ? `${copy} has no "License:" line` : `${copy} has a "License:" line, and a catalogue carries no licence of its own`);
    }
    const description = tags(html, 'meta').find((meta) => meta.name === 'description')?.content;
    if (fields.get('Summary') !== description) {
      add('header', `${copy} ${said('Summary')}, and the page's description is ${description === undefined ? 'none' : JSON.stringify(description)}`);
    }
    if (!bodyOf(text, lang)) add('body', `${copy} has nothing between its header and its references`);
  }
  if (pageClass.id === 'catalogue') {
    const inCopy = dataRows(text);
    const onPage = rowsOnPage(html);
    if (inCopy !== onPage) add('body', `${copy} holds ${inCopy} table row(s), and ${route} shows ${onPage}`);
  }
  for (const problem of textProblems(text)) add('text', `${copy} ${problem}`);
}

/** The ok/FAIL lines of one group of findings, the first few spelled out. */
const SHOWN = 12;

/**
 * What a copy lost of the page's own source, read from the source and the
 * copy as built (scripts/shared/page-twin.mjs, `copyDefects`): a line of the
 * page's code, an entry or a DOI of its references, and a figure, a clip, a
 * fiche or a catalogue the page renders. The source is read as the site's
 * Markdown plugins write it (src/lib/agent-md/rewrites.mjs), so the
 * bibliography is held to its lists. And the bibliography's copy lists one
 * entry for each entry its built page lists (`data-cited-by`), which no copy
 * of its source can show.
 *
 * @param {string} dist
 * @param {{ contentDir?: string, routes?: readonly string[] }} [options]  The
 *   routes to read, every copy of the build by default.
 * @returns {Promise<string[]>}
 */
export async function checkCopiesAgainstSources(dist, { contentDir = CONTENT_DIR, routes } = {}) {
  const found = [];
  const site = `${siteUrl}${basePath}`;
  const catalogues = { en: 0, es: 0 };
  const listed = routes ?? markdownFiles(dist).filter((copy) => copy.endsWith('/index.md')).map((copy) => copy.slice(0, -'index.md'.length));
  for (const route of listed) {
    const id = route.replace(/^\/|\/$/gu, '');
    const file = fileOfRoute(id, contentDir);
    const copyFile = join(dist, ...id.split('/').filter(Boolean), 'index.md');
    if (file === undefined || !existsSync(copyFile)) continue;
    const lang = id === 'es' || id.startsWith('es/') ? 'es' : 'en';
    const text = readCommittedText(file);
    const asWritten = stripFrontmatter(text);
    const firstLine = text.slice(0, text.length - asWritten.length).split('\n').length;
    const frontmatter = /** @type {Record<string, unknown>} */ (parseYaml(frontmatterSource(text)) ?? {});
    catalogues[lang] ||= catalogueSlugs.length;
    const source = await rewrittenSource(file, asWritten, { lang });
    const copy = readFileSync(copyFile, 'utf8');
    for (const defect of copyDefects(copy, {
      source,
      kind: file.endsWith('.mdx') ? 'mdx' : 'md',
      title: undefined,
      references: /** @type {{ doi?: string }[]} */ (Array.isArray(frontmatter.references) ? frontmatter.references : []),
      heading: REFERENCES_HEADING[lang],
      site,
      catalogues: catalogues[lang],
      firstLine,
      forms: pageKind(route) !== 'home',
    })) {
      found.push(`${route}: ${defect}`);
    }
  }
  for (const route of ['/reference/bibliography/', '/es/reference/bibliography/']) {
    const html = join(dist, ...route.split('/').filter(Boolean), 'index.html');
    const copyFile = join(dist, ...route.split('/').filter(Boolean), 'index.md');
    if (!existsSync(html) || !existsSync(copyFile)) continue;
    const works = (readFileSync(html, 'utf8').match(/<span data-cited-by\b/gu) ?? []).length;
    const lead = route.startsWith('/es/') ? 'Citado por' : 'Cited by';
    const entries = readFileSync(copyFile, 'utf8')
      .split('\n- ')
      .slice(1)
      .filter((entry) => entry.includes(`${lead} [`)).length;
    if (entries !== works) found.push(`${route}: its copy lists ${entries} of the ${works} works the page lists`);
  }
  return found;
}

async function main() {
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
    result.findings.get('body')?.push(...(await checkCopiesAgainstSources(dist)));
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
    body: 'copy(ies) that carry less than their page',
    text: 'place(s) in the copies a Markdown reader cannot use',
    llms: 'place(s) where the llms files do not carry the copies as they read',
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
      `(${classes}), ${stats.copies} copies; the llms files carry ${stats.llms.pages} of them ` +
      `as they read, in ${stats.llms.files} shard files and llms-full.txt`,
  );
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();

