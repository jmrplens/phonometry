/**
 * Where do the pages written to a standard land when a reader searches for it?
 *
 * Prints, for each search and each language, how many results come back, the
 * rank of every page whose bibliography declares the standard, and the rank of
 * the first page that does not. It is the measurement behind the ranking in
 * src/lib/search-ranking.mjs, kept runnable so anyone can repeat it on a build.
 *
 * A declaring page is defined the same way the check in
 * check-search-designation.mjs defines it: its bibliography's tokens answer every
 * number in the query. The tokens come from the frontmatter, not from the built
 * HTML, so the script also runs against a build that has no standards field.
 *
 * Usage:
 *   node scripts/search-ranks.mjs [--dist dist] [--weight N] [--as-typed] [query ...]
 *
 *   --weight N   rank with the standards field weighted N instead of the
 *                shipped weight; 0 leaves it out of the order entirely
 *   --as-typed   search for the query exactly as typed, without the query
 *                normalizer, which is what the search panel did before it had one
 *
 * With no query, the searches the ranking was designed and reviewed against.
 */

import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { PAGEFIND_RANKING } from '../src/lib/search-ranking.mjs';
import { designationTokens } from '../src/lib/standard-search.mjs';
import {
  answersEvery,
  keyTerms,
  loadSearchIndex,
  readDeclaredDesignations,
  searchAsReader,
} from './shared/search-index.mjs';

const DEFAULT_QUERIES = [
  'ISO 3744',
  'ISO 3744:2010',
  'UNE-EN ISO 3744',
  'ISO 8041-1',
  'ISO 8041-1:2017',
  'IEC 61672-1',
  'ISO 9613-2',
  'ISO 1996-2',
  'EN 12354-1',
  'DIN 4150-3',
  'ANSI S1.11',
  'ISO 16283-1',
  'ISO 14257',
  'UNE-EN ISO 16283-1:2015',
  'BS EN ISO 717-1:2021',
  'la norma UNE-EN ISO 3744',
  'ANSI/ASA S12.2-2019',
  'Recommendation ITU-R BS.1770-5',
  'VDI 2081 Blatt 2',
];

const args = process.argv.slice(2);
const option = (name) => {
  const at = args.indexOf(name);
  if (at === -1) return undefined;
  const [, value] = args.splice(at, 2);
  return value;
};
const flag = (name) => {
  const at = args.indexOf(name);
  if (at !== -1) args.splice(at, 1);
  return at !== -1;
};

const siteRoot = fileURLToPath(new URL('..', import.meta.url));
const distDir = path.resolve(option('--dist') ?? path.join(siteRoot, 'dist'));
const weightOption = option('--weight');
const asTyped = flag('--as-typed');
const queries = args.length > 0 ? args : DEFAULT_QUERIES;
const ranking =
  weightOption === undefined ? PAGEFIND_RANKING : { metaWeights: { standards: Number(weightOption) } };

const { declared } = await readDeclaredDesignations(path.join(siteRoot, 'src/content/docs'));
/** @type {Map<string, string[]>} route -> tokens its bibliography indexes */
const tokensByRoute = new Map();
for (const [route, list] of declared) {
  tokensByRoute.set(route, [...new Set(list.flatMap((designation) => designationTokens(designation)))]);
}

console.log(
  `standards weight ${ranking.metaWeights.standards}, ` +
    `${asTyped ? 'queries as typed' : 'queries through the normalizer'}, ${distDir}`,
);
for (const lang of ['en', 'es']) {
  const pagefind = await loadSearchIndex(distDir, lang, ranking);
  const inLanguage = (route) => (lang === 'es') === route.startsWith('/es/');
  console.log(`\n[${lang}]`);
  console.log('query | results | declaring pages ranked | first other page');
  for (const query of queries) {
    const terms = keyTerms(query);
    const declaring = [...tokensByRoute]
      .filter(([route, tokens]) => inLanguage(route) && terms.length > 0 && answersEvery(tokens, terms))
      .map(([route]) => route);
    const results = await searchAsReader(pagefind, query, { asTyped });
    const urls = results.map((r) => r.url);
    const ranks = declaring
      .map((route) => urls.indexOf(route) + 1)
      .sort((a, b) => (a || Infinity) - (b || Infinity))
      .map((rank) => (rank === 0 ? '-' : String(rank)));
    const firstOther = urls.findIndex((url) => !declaring.includes(url)) + 1;
    console.log(
      `${query} | ${results.length} | [${ranks.join(', ')}] | ${firstOther === 0 ? '-' : `#${firstOther}`}`,
    );
  }
}
