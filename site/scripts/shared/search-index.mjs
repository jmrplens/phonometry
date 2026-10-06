// Shared plumbing for the two scripts that read the built search index in Node:
// check-search-designation.mjs, which asserts on it, and search-ranks.mjs, which
// prints where the pages written to a standard land for a list of searches. The
// frontmatter reader below also serves check-cited-standards.mjs.
//
// None needs a browser, a server or a port. The built `pagefind.js` is a
// module that reads its index through `fetch`, and both `fetch` and the one
// `document` lookup it makes are answered from the file system here.
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { normalizeDesignationQuery } from '../../src/lib/designation-query.mjs';
import { STARLIGHT_RANKING_DEFAULTS } from '../../src/lib/search-ranking.mjs';
import { declaredDesignation, foldPartWords } from '../../src/lib/standard-search.mjs';

const FAKE_BASE = 'http://pagefind.invalid/pagefind/';

/** How many copies of the bundle loadSearchIndex has loaded, to give each its own address. */
let loadedCopies = 0;

/** @returns {Promise<string[]>} every file under `dir` whose name passes `keep` */
export async function filesUnder(dir, keep) {
  const out = [];
  for (const item of await readdir(dir, { withFileTypes: true })) {
    const full = path.join(dir, item.name);
    if (item.isDirectory()) out.push(...(await filesUnder(full, keep)));
    else if (keep(item.name)) out.push(full);
  }
  return out;
}

/** The keys of a references entry that decide what it declares. */
const READ_KEYS = new Set(['type', 'designation', 'number', 'implemented']);

/** One frontmatter scalar as written: unquoted, with a trailing comment taken off. */
function scalarValue(raw) {
  const value = raw.trim();
  const quoted = /^(["'])(.*)\1(?:\s+#.*)?$/.exec(value);
  if (quoted) return quoted[2];
  return value.replace(/\s+#.*$/, '');
}

/**
 * The designations each page declares, read out of its frontmatter.
 *
 * A deliberately narrow reader rather than a YAML parser, because site/ has
 * none installed and this does not need one. The check that uses it crosses the
 * result against the tokens already emitted in the HTML, in both directions, so
 * a designation it fails to see makes the two sets differ: it cannot read too
 * little in silence. What it cannot follow at all (a bibliography in flow
 * style, a designation as a block scalar) it reports as a problem rather than
 * reading as nothing.
 *
 * A page declares the standards it implements. Which entry declares what is
 * decided by declaredDesignation in src/lib/standard-search.mjs, the function
 * the site itself builds the field with, so the rule exists once: a standard
 * declares its designation and a numbered report its number, unless the entry
 * is marked `implemented: false`, which the page cites but is not written to.
 * To apply it, the reader collects each entry's keys: an entry opens at a list
 * item under `references:`, and its keys are the lines at the column its first
 * key starts at, so a nested list (the authors of a report) neither splits an
 * entry nor lends it keys.
 *
 * Besides what each page implements, the reader returns what each page only
 * cites, for the check that those entries stay out of the chips and the
 * structured data; every designation the bibliographies print, which is what
 * the search check measures searches over (a search for a cited standard must
 * still find the guides that implement it first); and every route that has a
 * content file, so a page built at a route nothing declares can be told from an
 * English fallback served under the Spanish tree.
 *
 * @param {string} contentDir site/src/content/docs
 * @returns {Promise<{declared: Map<string, string[]>, cited: Map<string, string[]>, designations: Set<string>, routes: Set<string>, problems: string[]}>}
 *   route -> implemented designations in frontmatter order; route -> the
 *   designations of the entries marked `implemented: false`; every distinct
 *   designation printed in a bibliography; every route with a content file; and
 *   the entries this reader could not follow
 */
export async function readDeclaredDesignations(contentDir) {
  const declared = new Map();
  const cited = new Map();
  const designations = new Set();
  const routes = new Set();
  const problems = [];
  for (const file of await filesUnder(contentDir, (name) => /\.mdx?$/.test(name))) {
    const text = await readFile(file, 'utf8');
    if (!text.startsWith('---')) continue;
    const end = text.indexOf('\n---', 3);
    if (end < 0) continue;
    const route = `/${path
      .relative(contentDir, file)
      .replace(/\.mdx?$/, '')
      .replace(/(^|\/)index$/, '')}/`.replace(/\/\/+/g, '/');
    routes.add(route);
    /** @type {Array<Record<string, string>>} */
    const entries = [];
    /** The `references` line, when the frontmatter has one. */
    let referencesKey;
    let inReferences = false;
    /** Indent of the dash that opens an entry, set by the first one. */
    let itemIndent = -1;
    /** Column the keys of the current entry start at. */
    let keyColumn = -1;
    for (const line of text.slice(3, end).split('\n')) {
      if (/^\S/.test(line)) {
        // A top-level key opens or closes the bibliography; a comment after it
        // is still the block form.
        if (/^references\s*:/.test(line)) referencesKey = line;
        inReferences = /^references:\s*(?:#.*)?$/.test(line);
        itemIndent = -1;
        continue;
      }
      if (!inReferences) continue;
      const item = /^(\s*)-(\s+)\S/.exec(line);
      if (item && (itemIndent === -1 || item[1].length === itemIndent)) {
        itemIndent = item[1].length;
        keyColumn = itemIndent + 1 + item[2].length;
        entries.push({});
      } else if (item || /^\s*(?:#.*)?$/.test(line) || line.length - line.trimStart().length !== keyColumn) {
        // An item of a nested list, a blank line, a comment, or a line inside
        // a nested value.
        continue;
      }
      const entry = entries.at(-1);
      if (!entry) continue;
      const key = /^([A-Za-z_][\w-]*):(?:\s+(.*))?$/.exec(line.slice(keyColumn));
      if (!key) {
        problems.push(`${file}: a references entry not written as one key per line, which this reader cannot follow`);
        continue;
      }
      const raw = key[2] ?? '';
      if (/^[>|]/.test(raw.trim())) {
        // A note or a title often is one, and neither is read here.
        if (READ_KEYS.has(key[1])) {
          problems.push(`${file}: ${key[1]} written as a block scalar, which this reader cannot follow`);
        }
        continue;
      }
      entry[key[1]] = scalarValue(raw);
    }
    if (referencesKey !== undefined && entries.length === 0) {
      problems.push(`${file}: "${referencesKey.trim()}" opens no entry this reader can follow`);
    }
    const found = [];
    const citedHere = [];
    for (const entry of entries) {
      const ref = { ...entry, implemented: entry.implemented === 'false' ? false : undefined };
      // What the entry would declare if the page implemented it.
      const printed = declaredDesignation({ ...ref, implemented: undefined });
      if (!printed) continue;
      designations.add(printed);
      (declaredDesignation(ref) ? found : citedHere).push(printed);
    }
    if (found.length) declared.set(route, found);
    if (citedHere.length) cited.set(route, citedHere);
  }
  return { declared, cited, designations, routes, problems };
}

/**
 * Load a fresh copy of the built Pagefind bundle, bound to one language and one
 * ranking. Starlight's own ranking defaults are filled in first, because these
 * scripts run Pagefind directly rather than through Starlight's Search
 * component.
 *
 * Every call returns a copy of its own, with nothing of the index read yet,
 * even for a language and a ranking asked for before. Node keeps one module
 * per address, so the address carries a count: a copy that earlier searches
 * sent to more index chunks can rank the same search differently (see D in
 * check-search-designation.mjs), and a caller asking for a fresh copy must not
 * be handed that one.
 *
 * @param {string} distDir the built site
 * @param {'en'|'es'} lang
 * @param {{metaWeights?: Record<string, number>}} ranking
 */
export async function loadSearchIndex(distDir, lang, ranking) {
  const pagefindDir = path.join(distDir, 'pagefind');
  globalThis.fetch = async (input) => {
    const name = String(input?.url ?? input).slice(FAKE_BASE.length).split('?')[0];
    return new Response(await readFile(path.join(pagefindDir, name)));
  };
  globalThis.document = {
    currentScript: null,
    querySelector: (selector) => (selector === 'html' ? { getAttribute: () => lang } : null),
  };
  const weight = ranking.metaWeights?.standards ?? 'default';
  loadedCopies += 1;
  const href = `${pathToFileURL(path.join(pagefindDir, 'pagefind.js')).href}?lang=${lang}-${weight}&copy=${loadedCopies}`;
  const pagefind = await import(href);
  await pagefind.options({
    basePath: FAKE_BASE,
    baseUrl: '/',
    ranking: { ...STARLIGHT_RANKING_DEFAULTS, ...ranking },
  });
  return pagefind;
}

/**
 * Run one search the way the site's search panel runs it.
 *
 * @param {object} pagefind a bundle from loadSearchIndex
 * @param {string} query what the reader typed
 * @param {{asTyped?: boolean}} [options] skip the query normalizer, which is
 *   what the panel did before it had one
 * @returns {Promise<Array<{url: string, score: number}>>}
 */
export async function searchAsReader(pagefind, query, { asTyped = false } = {}) {
  const { results } = await pagefind.search(asTyped ? query : normalizeDesignationQuery(query));
  return Promise.all(results.map(async (r) => ({ url: (await r.data()).url, score: r.score })));
}

/**
 * Pagefind's own query normalisation: it deletes the punctuation categories
 * without putting a space in their place, then lowercases and splits on
 * whitespace. Reproduced so an expected set is derived the same way the engine
 * derives its terms.
 */
export function queryTerms(query) {
  return normalizeDesignationQuery(query)
    .replace(/[\p{Pd}\p{Pe}\p{Pf}\p{Pi}\p{Po}\p{Ps}]/gu, '')
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);
}

/**
 * The terms a query is judged on: the ones carrying a number, three characters
 * or more, read after "Blatt 2" has been folded into the part it names, as the
 * index folds it. "VDI 2081 Blatt 2" is judged against the pages declaring
 * Blatt 2, not against every page declaring any sheet of VDI 2081.
 *
 * The issuer is deliberately not one of them. ISO 12354-1 and EN 12354-1 are
 * the same document under two names, and a page is written to one or the other;
 * judging on the issuer would call a guide written to ISO 12354-1 an intruder
 * on a search for EN 12354-1, which is the opposite of useful. "en" is also a
 * two-letter prefix that matches a third of the English vocabulary, so it says
 * nothing about a page either way.
 *
 * The length floor drops a bare part number. "OJ L 5" ends in a term that
 * matches almost everything; keeping it would define an expected set of most
 * of the site and measure nothing.
 */
export function keyTerms(query) {
  return queryTerms(foldPartWords(query)).filter((term) => /[0-9]/.test(term) && term.length >= 3);
}

/** Does this token list answer every term, each by prefix, as Pagefind matches? */
export function answersEvery(tokens, terms) {
  return terms.every((term) => tokens.some((token) => token.startsWith(term)));
}
