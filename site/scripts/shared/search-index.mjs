// Shared plumbing for the two scripts that read the built search index in Node:
// check-search-designation.mjs, which asserts on it, and search-ranks.mjs, which
// prints where the pages written to a standard land for a list of searches.
//
// Neither needs a browser, a server or a port. The built `pagefind.js` is a
// module that reads its index through `fetch`, and both `fetch` and the one
// `document` lookup it makes are answered from the file system here.
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { normalizeDesignationQuery } from '../../src/lib/designation-query.mjs';
import { STARLIGHT_RANKING_DEFAULTS } from '../../src/lib/search-ranking.mjs';
import { foldPartWords } from '../../src/lib/standard-search.mjs';

const FAKE_BASE = 'http://pagefind.invalid/pagefind/';

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

/**
 * The designations each page declares, read out of its frontmatter.
 *
 * A deliberately narrow reader rather than a YAML parser, because site/ has
 * none installed and this does not need one. The check that uses it crosses the
 * result against the tokens already emitted in the HTML, so a designation it
 * fails to see makes the two sets differ: it cannot read too little in silence.
 *
 * @param {string} contentDir site/src/content/docs
 * @returns {Promise<{declared: Map<string, string[]>, designations: Set<string>, problems: string[]}>}
 *   route -> designations in frontmatter order, every distinct designation, and
 *   the entries this reader could not follow
 */
export async function readDeclaredDesignations(contentDir) {
  const declared = new Map();
  const designations = new Set();
  const problems = [];
  for (const file of await filesUnder(contentDir, (name) => /\.mdx?$/.test(name))) {
    const text = await readFile(file, 'utf8');
    if (!text.startsWith('---')) continue;
    const end = text.indexOf('\n---', 3);
    if (end < 0) continue;
    const found = [];
    for (const line of text.slice(3, end).split('\n')) {
      const match = /^\s{2,}(?:designation|number):\s*(.+?)\s*$/.exec(line);
      if (!match) continue;
      let value = match[1];
      if (/^[>|]/.test(value)) {
        problems.push(`${file}: designation written as a block scalar, which this reader cannot follow`);
        continue;
      }
      if (/^(["']).*\1$/s.test(value)) value = value.slice(1, -1);
      found.push(value);
      designations.add(value);
    }
    if (found.length === 0) continue;
    const route = `/${path
      .relative(contentDir, file)
      .replace(/\.mdx?$/, '')
      .replace(/(^|\/)index$/, '')}/`.replace(/\/\/+/g, '/');
    declared.set(route, found);
  }
  return { declared, designations, problems };
}

/**
 * Load a fresh copy of the built Pagefind bundle, bound to one language and one
 * ranking. Starlight's own ranking defaults are filled in first, because these
 * scripts run Pagefind directly rather than through Starlight's Search
 * component.
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
  const href = `${pathToFileURL(path.join(pagefindDir, 'pagefind.js')).href}?lang=${lang}-${weight}`;
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
