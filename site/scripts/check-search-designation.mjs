/**
 * Does a search for a standard designation still return the guides written to
 * that standard first?
 *
 * The site indexes the designations a page declares as a weighted Pagefind
 * metadata field (src/components/Head.astro, src/lib/standard-search.mjs,
 * src/lib/search-ranking.mjs), and reads what the reader typed through
 * src/lib/designation-query.mjs. Nothing about that arrangement is visible in
 * the pages themselves: the field is hidden from the reader by one stylesheet
 * rule, the weight is one number in a config, and the query normalizer is wired
 * in by a Vite alias that would simply stop applying if Starlight changed how it
 * imports the search UI. Every one of those can break without a page looking
 * any different, so this runs Pagefind's own index, in Node, over the finished
 * build (scripts/shared/search-index.mjs), and reads the built bundle for the
 * rest. No browser, no server, no port.
 *
 * Usage: node scripts/check-search-designation.mjs [dist directory]
 */

import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  NATIONAL_ADOPTION_PREFIXES,
  SEARCH_TERM_NORMALIZER_MARK,
  normalizeDesignationQuery,
} from '../src/lib/designation-query.mjs';
import { PAGEFIND_RANKING } from '../src/lib/search-ranking.mjs';
import { designationTokens } from '../src/lib/standard-search.mjs';
import {
  answersEvery,
  filesUnder,
  keyTerms,
  loadSearchIndex,
  queryTerms,
  readDeclaredDesignations,
  searchAsReader,
} from './shared/search-index.mjs';

const siteRoot = fileURLToPath(new URL('..', import.meta.url));
const distDir = path.resolve(process.argv[2] ?? path.join(siteRoot, 'dist'));
const contentDir = path.join(siteRoot, 'src/content/docs');
const LANGS = ['en', 'es'];

/**
 * The queries the work was asked for, with the pages that declare them written
 * out by hand. The mechanical expectation below would pass on an index that had
 * quietly lost half its tokens, as long as it stayed self-consistent; this
 * cannot. Paths are the English ones; the Spanish twin of each is checked too,
 * unless `langs` narrows the query to the language it is written in.
 */
const ISO_3744 = [
  '/devices/emission/sound-power-pressure/',
  '/buildings/rooms/workroom-sound-decay/',
  '/reference/theory/environment-transport/',
];
const ISO_8041_1 = ['/vibration/human/meter-verification/', '/vibration/human/human-vibration/'];
const ISO_16283_1 = [
  '/buildings/insulation/insulation-field/',
  '/buildings/insulation/low-frequency-procedure/',
  '/reference/theory/rooms-buildings/',
];
const ISO_717_1 = [
  '/buildings/insulation/insulation-ratings/',
  '/buildings/insulation/insulation-field/',
  '/buildings/insulation/facade-insulation/',
  '/buildings/insulation/low-frequency-procedure/',
  '/devices/noise-control/enclosure-cabin-insulation/',
  '/reference/theory/rooms-buildings/',
];

/** @type {Array<{query: string, routes: string[], langs?: string[]}>} */
const ANCHORED = [
  { query: 'ISO 3744', routes: ISO_3744 },
  { query: 'ISO 8041-1', routes: ISO_8041_1 },
  { query: 'ISO 8041-1:2017', routes: ISO_8041_1 },
  { query: 'UNE-EN ISO 3744', routes: ISO_3744 },
  {
    query: 'IEC 61672-1',
    routes: [
      '/signals/levels/levels/',
      '/signals/levels/time-weighting/',
      '/signals/levels/weighting/',
      '/signals/sound-level-meter/',
      '/signals/metrology/compliance-verification/',
      '/signals/metrology/free-field-corrections/',
      '/signals/filters/block-processing/',
      '/signals/filters/multichannel/',
      '/reference/theory/signal-analysis/',
    ],
  },
  {
    query: 'DIN 4150-3',
    routes: ['/vibration/structural/structural-damage/', '/vibration/immission/vibration-meter/'],
  },
  // A national adoption as its catalogue prints it, edition included. The year
  // is the national body's, never the one the bibliography declares
  // (ISO 16283-1:2014, ISO 717-1:2020), so it has to be dropped with the prefix.
  { query: 'UNE-EN ISO 16283-1:2015', routes: ISO_16283_1 },
  { query: 'BS EN ISO 717-1:2021', routes: ISO_717_1 },
  // The prefix hyphenated all the way through, and typed after other words.
  { query: 'UNE-EN-ISO 3744', routes: ISO_3744 },
  { query: 'la norma UNE-EN ISO 3744', routes: ISO_3744, langs: ['es'] },
];

/**
 * Searches that are not designations, run twice: once with the weight the site
 * ships and once with it at zero. Their top five must be identical, which is
 * what proves the new field ranks designations without disturbing everything
 * else. The list is stocked with the words that live inside designations
 * ("standard", "annex", "directive", "blatt", "recommendation") and with
 * ordinary searches in both languages, including Spanish ones built around
 * "en", which is also the issuer EN in the field.
 *
 * Every word the field itself carries is checked the same way, mechanically,
 * further down; this list is for the words it deliberately does not carry.
 */
const CONTROLS = [
  'standard',
  'annex',
  'directive',
  'blatt',
  'recommendation',
  'reverberation time',
  'sound power',
  'norma',
  'directiva',
  'ruido',
  'aire',
  'potencia acústica',
  'ruido en interiores',
  'aislamiento en obra',
  'vibración en edificios',
  'filtros de octava',
];

/**
 * The words in the field that are allowed to reorder a search for themselves,
 * because that is their purpose: each names an issuer or a document series, and
 * a reader who types it wants the pages that declare such a document. Any other
 * word the field carries must leave the search for that word exactly as it was,
 * and that is checked for every one of them rather than for a hand-picked few.
 *
 * "air" (SAE AIR 5662) and "noise" (the NOISE research project) are deliberately
 * absent: they are ordinary words on an acoustics site first. "en" is here even
 * though it is the Spanish preposition, because a search is never "en" alone and
 * the Spanish searches built around it are in CONTROLS.
 */
const ISSUER_WORDS = new Set([
  'acou', 'aes', 'ahri', 'ansi', 'arp', 'asa', 'astm', 'bs', 'ceac', 'cte', 'dbhr',
  'dhhs', 'din', 'ebu', 'ecac', 'en', 'eur', 'icao', 'iec', 'iso', 'itu', 'jcgm',
  'jis', 'nasa', 'niosh', 'noaa', 'nt', 'oj', 'pas', 'rd', 'rfc', 'sae', 'tr',
  'ts', 'uit', 'vdi',
]);

/** Score ratio a declaring page must keep over the best page that does not declare. */
const MIN_MARGIN = 2;

const failures = [];
const fail = (message) => failures.push(message);

// ---------------------------------------------------------------------------
// The built pages: which routes carry the field, and with which tokens.
// ---------------------------------------------------------------------------

const STANDARDS_META =
  /<meta[^>]*\bdata-pagefind-meta=["']standards\[content\]["'][^>]*>/i;

/** @type {Map<string, {lang: string, tokens: string[]}>} url -> field as built */
const built = new Map();
for (const file of await filesUnder(distDir, (name) => name === 'index.html')) {
  const html = await readFile(file, 'utf8');
  // Redirect stubs carry neither a body marker nor this field.
  const match = STANDARDS_META.exec(html);
  if (!match) continue;
  const content = /\bcontent=["']([^"']*)["']/i.exec(match[0]);
  if (!content) {
    fail(`${file}: the standards meta tag carries no content attribute`);
    continue;
  }
  const url = `/${path.relative(distDir, path.dirname(file))}/`.replace(/^\/\.\/$/, '/');
  built.set(url, {
    lang: url.startsWith('/es/') ? 'es' : 'en',
    tokens: content[1].split(/\s+/).filter(Boolean),
  });
}

if (built.size === 0) {
  console.error(`check:search: no page under ${distDir} carries the standards field. Build first.`);
  process.exit(1);
}

// E'. Shape.
for (const [url, page] of built) {
  for (const token of page.tokens) {
    if (!/^[a-z0-9]+$/.test(token)) fail(`${url}: malformed token ${JSON.stringify(token)}`);
  }
}

// ---------------------------------------------------------------------------
// The frontmatter: the designations each page declares.
// ---------------------------------------------------------------------------

const { declared, designations, problems } = await readDeclaredDesignations(contentDir);
for (const problem of problems) fail(problem);

// Every designation must tokenise. designationTokens throws on one that cannot,
// which already fails the site build; calling it here names the file too.
for (const designation of designations) designationTokens(designation);

// The cross-check: what the frontmatter says, against what the page published.
for (const [route, list] of declared) {
  const page = built.get(route);
  const expected = new Set();
  for (const designation of list) for (const token of designationTokens(designation)) expected.add(token);
  if (!page) {
    // A route can be missing from the build for a good reason (the Spanish
    // tree serves some pages as English fallbacks under another address);
    // a route that is built but silent about standards it declares is not.
    if (expected.size > 0 && built.has(route.replace(/^\/es\//, '/'))) continue;
    if (expected.size > 0) fail(`${route}: declares ${list.length} standards but published no tokens`);
    continue;
  }
  const got = new Set(page.tokens);
  const missing = [...expected].filter((t) => !got.has(t));
  const extra = [...got].filter((t) => !expected.has(t));
  if (missing.length || extra.length) {
    fail(
      `${route}: published tokens do not match its bibliography` +
        (missing.length ? ` (missing ${missing.join(' ')})` : '') +
        (extra.length ? ` (unexpected ${extra.join(' ')})` : ''),
    );
  }
}

// F. Both languages index the same standards.
for (const [url, page] of built) {
  if (page.lang !== 'es') continue;
  const twin = built.get(url.replace(/^\/es\//, '/'));
  if (!twin) continue;
  const a = [...new Set(page.tokens)].sort().join(' ');
  const b = [...new Set(twin.tokens)].sort().join(' ');
  if (a !== b) fail(`${url}: Spanish and English twins index different standards\n  es: ${a}\n  en: ${b}`);
}

// ---------------------------------------------------------------------------
// H. What the reader typed.
//
// The normalizer is plain string work, so it is checked as such, over every
// national body it knows rather than over the one or two a test happens to
// remember. The spellings are the ones catalogues and readers actually use:
// spaced, hyphenated through, with a slash, after other words, with the
// national edition, and lowercase.
// ---------------------------------------------------------------------------

/** Queries the normalizer must leave exactly as typed. */
const UNTOUCHED = [
  'ISO 1996-2:2007',
  'EN 12354-1',
  'EN 1996',
  'DIN 4150-3:1999-02',
  'ruido en ISO 1996',
  'isolation',
  'ECMA-418-1',
  'ISO 7235:2003 (EN ISO 7235:2009)',
  'CTE DB-HR',
  'dB(A)',
  'mV/Pa',
  // Typed without capitals, a word is read as an issuer only in front of a
  // number, so the lowercase forms of ordinary words keep their single term,
  // and a unit with a capital inside it is never an issuer wherever it stands.
  'mv/pa',
  'db/oct',
  'input/output',
  'itu-r',
  'sensitivity in mV/Pa to IEC 61094-4',
];
for (const query of UNTOUCHED) {
  const got = normalizeDesignationQuery(query);
  if (got !== query) fail(`normalizer: ${JSON.stringify(query)} must stay as typed, got ${JSON.stringify(got)}`);
}
/** Queries copied from a bibliography, with what the index does not carry taken out. */
const REWRITTEN = [
  ['EN ISO 3744:2010', 'ISO 3744:2010'],
  ['ANSI/ASA S12.2-2019', 'ANSI ASA S12.2-2019'],
  ['ISO/TS 7849-1:2009', 'ISO TS 7849-1:2009'],
  ['ECAC.CEAC Doc 29', 'ECAC CEAC Doc 29'],
  ['Recommendation ITU-R BS.1770-5 (11/2023)', 'Recommendation ITU BS.1770-5'],
  ['Recomendación UIT-R BS.468-4', 'Recomendación UIT BS.468-4'],
  ['ECMA-418-2:2025 (4.ª ed.)', 'ECMA-418-2:2025'],
  ['ANSI S3.5-1997 (R2017)', 'ANSI S3.5-1997'],
  // The same designations typed in lowercase or capitalised, as a reader does.
  ['ansi/asa s12.2-2019', 'ansi asa s12.2-2019'],
  ['Ansi/Asa S12.2-2019', 'Ansi Asa S12.2-2019'],
  ['iso/ts 7849-1:2009', 'iso ts 7849-1:2009'],
  ['ecac.ceac doc 29', 'ecac ceac doc 29'],
  ['recommendation itu-r bs.1770-5 (11/2023)', 'recommendation itu bs.1770-5'],
  ['Itu-R BS.1770-5', 'Itu BS.1770-5'],
  ['recomendación uit-r bs.468-4', 'recomendación uit bs.468-4'],
];
for (const [query, want] of REWRITTEN) {
  const got = normalizeDesignationQuery(query);
  if (got !== want) fail(`normalizer: ${JSON.stringify(query)} gave ${JSON.stringify(got)}, want ${JSON.stringify(want)}`);
}

for (const source of NATIONAL_ADOPTION_PREFIXES) {
  const prefix = source.replace(/\\(.)/g, '$1');
  const cases = [
    [`${prefix} EN ISO 3744`, 'ISO 3744'],
    [`${prefix}-EN ISO 3744`, 'ISO 3744'],
    [`${prefix}-EN-ISO 3744`, 'ISO 3744'],
    [`${prefix}/EN ISO 3744`, 'ISO 3744'],
    [`${prefix} ISO 9613-2`, 'ISO 9613-2'],
    [`${prefix} EN ISO 717-1:2021`, 'ISO 717-1'],
    [`${prefix} EN IEC 61672-1:2014-07`, 'IEC 61672-1'],
    [`${prefix}-EN 12354-1:2018`, 'EN 12354-1'],
    [`norma ${prefix}-EN ISO 3744`, 'norma ISO 3744'],
  ];
  for (const [query, want] of cases) {
    // Pagefind lowercases every term, so case is compared the same way.
    for (const q of [query, query.toLowerCase()]) {
      const got = normalizeDesignationQuery(q);
      if (got.toLowerCase() !== want.toLowerCase()) {
        fail(`normalizer: ${JSON.stringify(q)} gave ${JSON.stringify(got)}, want ${JSON.stringify(want)}`);
      }
    }
  }
}

// Every ISO, IEC and EN designation in the corpus, typed as a Spanish or
// British reader finds it in a catalogue, must come out as a query this check
// already measures below: the prefixed form is then covered by the same order
// and margin assertions as the form the bibliography prints.
for (const designation of designations) {
  const bare = bareDesignation(designation);
  if (!/^(?:ISO|IEC|EN)\b/.test(bare)) continue;
  const adopted = bare.startsWith('EN ') ? bare.slice(3) : bare;
  for (const typed of [`UNE-EN ${adopted}:2099`, `BS EN ${adopted}:2099`]) {
    const got = normalizeDesignationQuery(typed);
    const want = normalizeDesignationQuery(bare);
    if (got !== want) {
      fail(`normalizer: ${JSON.stringify(typed)} gave ${JSON.stringify(got)}, want the measured query ${JSON.stringify(want)}`);
    }
  }
}

// Every designation in the corpus, typed in lowercase or capitalised, must
// search for the same terms as the capitals the bibliography prints. Pagefind
// lowercases the terms, so that is how they are compared. A note in brackets is
// taken off first: without capitals, an alternative designation in brackets
// cannot be told from an edition note, and it is dropped, which only searches
// for fewer of the terms the index carries.
const capitalised = (text) => text.replace(/[A-Za-z]+/g, (w) => w[0].toUpperCase() + w.slice(1).toLowerCase());
for (const designation of designations) {
  for (const printed of new Set([designation.replace(/\s*\([^)]*\)/g, ''), bareDesignation(designation)])) {
    const want = normalizeDesignationQuery(printed).toLowerCase();
    for (const typed of [printed.toLowerCase(), capitalised(printed)]) {
      const got = normalizeDesignationQuery(typed);
      if (got.toLowerCase() !== want) {
        fail(`normalizer: ${JSON.stringify(typed)} gave ${JSON.stringify(got)}, want ${JSON.stringify(want)} as for ${JSON.stringify(printed)}`);
      }
    }
  }
}

// ---------------------------------------------------------------------------
// The index itself.
// ---------------------------------------------------------------------------

/**
 * The pages a query is expected to reach, defined mechanically: a page whose
 * own tokens answer every key term by prefix. That is the property the ranking
 * has to respect, and it is not a judgement about which standard supersedes
 * which. Deciding that would mean maintaining a table of equivalences, and a
 * full sweep showed such a table failing on pages that are perfectly correct.
 *
 * Only pages that publish a bibliography can be expected, because only they
 * carry the field. Every other page stays in the result list the assertions
 * read: the API reference, the conformance table and the errata register are
 * exactly the pages that used to win these searches, so they are the ones that
 * must be seen to lose.
 */
function inScope(lang) {
  return [...built].filter(([, page]) => page.lang === lang).map(([url]) => url);
}

function expectedPages(terms, scope) {
  return new Set([...scope].filter((url) => answersEvery(built.get(url).tokens, terms)));
}

/** A designation without its qualifiers and its edition, as a reader types it. */
function bareDesignation(designation) {
  return designation
    .split(',')[0]
    .replace(/\(.*?\)/g, ' ')
    .split(':')[0]
    .replace(/-(19|20)\d{2}$/, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * The query shapes checked for one designation: as the bibliography spells it,
 * and without the edition, which is how a reader usually types it. The
 * adoption-prefix forms are proven above to normalise to the second shape, so
 * they are measured here without a search of their own; the family forms are
 * covered by the anchored list instead of by every designation, to keep this
 * inside its time budget.
 */
function queryShapes(designation) {
  return [...new Set([designation, bareDesignation(designation)])].filter(Boolean);
}

const shapes = [...new Set([...designations].flatMap(queryShapes))];
const started = Date.now();
/** Every word-only token the field carries, in either language. */
const allFieldWords = new Set();

for (const lang of LANGS) {
  const pagefind = await loadSearchIndex(distDir, lang, PAGEFIND_RANKING);

  /** @returns {Promise<Array<{url: string, score: number}>>} */
  const run = (engine, query) => searchAsReader(engine, query);

  const scope = new Set(inScope(lang));
  let worstMargin = Infinity;
  let worstMarginQuery = '';
  let proseShapes = 0;
  let worstProseMargin = Infinity;
  let worstProseMarginQuery = '';
  let measured = 0;

  for (const shape of shapes) {
    const terms = keyTerms(shape);
    if (terms.length === 0) continue;
    const expected = expectedPages(terms, scope);
    if (expected.size === 0) continue;
    measured += 1;
    const all = await run(pagefind, shape);
    const inExpected = (url) => expected.has(url);

    // E. Index coverage. A page whose field answers every term of the query,
    // issuer included, is a result on the strength of that field alone, so it
    // has to come back whatever its body says. This is what would notice the
    // day Pagefind stopped collecting metadata out of the head: the attribute
    // would still be in the HTML and every other assertion here would still
    // pass on the handful of pages that happen to rank by their prose.
    const returned = new Set(all.map((r) => r.url));
    const allTerms = queryTerms(shape);
    for (const url of expected) {
      const { tokens } = built.get(url);
      if (!answersEvery(tokens, allTerms)) continue;
      if (!returned.has(url)) {
        fail(`[${lang}] "${shape}": ${url} indexes this standard but is not among the results`);
      }
    }

    // A. Order, over every result, bibliography or not.
    const firstStranger = all.findIndex((r) => !inExpected(r.url));
    const lastExpected = all.map((r) => inExpected(r.url)).lastIndexOf(true);
    if (firstStranger !== -1 && lastExpected > firstStranger) {
      const intruder = all[firstStranger].url;
      fail(
        `[${lang}] "${shape}": ${intruder}${scope.has(intruder) ? '' : ' (no bibliography)'} outranks ` +
          `${all[lastExpected].url}, which declares the standard (#${firstStranger + 1} against #${lastExpected + 1})`,
      );
    }

    // B. Margin, against the best page of any kind that does not declare it.
    //
    // Enforced when the declaring page's own field answers every term of the
    // query, which is when the order is the field's to decide. A query that
    // carries a word the field deliberately leaves out ("Blatt", "Directive",
    // "Recommendation") is scored partly on prose, where a page quoting the
    // designation verbatim can come close; A above still holds it to the
    // order, and the closest such margin is printed rather than hidden.
    if (firstStranger !== -1 && lastExpected !== -1 && lastExpected < firstStranger) {
      const margin = all[lastExpected].score / all[firstStranger].score;
      const { tokens } = built.get(all[lastExpected].url);
      const fieldDecides = answersEvery(tokens, queryTerms(shape));
      if (!fieldDecides) {
        proseShapes += 1;
        if (margin < worstProseMargin) {
          worstProseMargin = margin;
          worstProseMarginQuery = shape;
        }
        continue;
      }
      if (margin < worstMargin) {
        worstMargin = margin;
        worstMarginQuery = shape;
      }
      if (margin < MIN_MARGIN) {
        fail(
          `[${lang}] "${shape}": the last declaring page scores only ${margin.toFixed(2)}x ` +
            `the best page that does not declare it (want >= ${MIN_MARGIN})`,
        );
      }
    }
  }

  // C. The anchored list.
  for (const { query, routes, langs } of ANCHORED) {
    if (langs && !langs.includes(lang)) continue;
    const want = new Set(routes.map((r) => (lang === 'es' ? `/es${r}` : r)));
    const ranked = await run(pagefind, query);
    const urls = ranked.map((r) => r.url);
    for (const route of want) {
      if (!urls.includes(route)) {
        fail(`[${lang}] "${query}": ${route} declares the standard but is not in the results`);
      }
    }
    const lastWanted = urls.map((u) => want.has(u)).lastIndexOf(true);
    const firstOther = urls.findIndex((u) => !want.has(u));
    if (firstOther !== -1 && lastWanted > firstOther) {
      fail(
        `[${lang}] "${query}": ${urls[firstOther]} is ahead of the declaring page ${urls[lastWanted]}`,
      );
    }
  }

  // D. No regression on searches that are not designations: the hand-written
  // controls, and every word the field carries that does not name an issuer.
  const unweighted = await loadSearchIndex(distDir, lang, { metaWeights: { standards: 0 } });
  const fieldWords = new Set();
  for (const url of scope) for (const token of built.get(url).tokens) if (!/[0-9]/.test(token)) fieldWords.add(token);
  const plainFieldWords = [...fieldWords].filter((word) => !ISSUER_WORDS.has(word)).sort();
  for (const query of [...CONTROLS, ...plainFieldWords]) {
    const before = (await run(unweighted, query)).slice(0, 5).map((r) => r.url);
    const after = (await run(pagefind, query)).slice(0, 5).map((r) => r.url);
    if (before.join('|') !== after.join('|')) {
      const why = fieldWords.has(query)
        ? 'is in the standards field without naming an issuer (add it to ISSUER_WORDS only if it names one), and the field reordered it'
        : 'is not a designation but the weighted field reordered it';
      fail(`[${lang}] "${query}" ${why}\n  without: ${before.join(' ')}\n  with:    ${after.join(' ')}`);
    }
  }
  for (const word of fieldWords) allFieldWords.add(word);

  console.log(
    `check:search [${lang}]: ${measured}/${shapes.length} query shapes, ${scope.size} pages with the field, ` +
      `worst margin ${worstMargin === Infinity ? 'n/a' : `${worstMargin.toFixed(1)}x`}` +
      `${worstMarginQuery ? ` ("${worstMarginQuery}")` : ''}` +
      `${worstProseMarginQuery ? `; ${proseShapes} carry prose the field leaves out, closest ${worstProseMargin.toFixed(1)}x ("${worstProseMarginQuery}")` : ''}; ` +
      `${CONTROLS.length + plainFieldWords.length} control searches`,
  );
}

// ---------------------------------------------------------------------------
// The index as a whole, the issuer list, and G. the wiring that reaches the
// browser.
// ---------------------------------------------------------------------------

const entry = JSON.parse(await readFile(path.join(distDir, 'pagefind', 'pagefind-entry.json'), 'utf8'));
for (const lang of LANGS) {
  const withField = [...built.values()].filter((p) => p.lang === lang).length;
  const pageCount = entry.languages?.[lang]?.page_count;
  if (typeof pageCount !== 'number') fail(`the Pagefind index has no ${lang} language`);
  else if (pageCount < withField) {
    fail(`the ${lang} index holds ${pageCount} pages but ${withField} carry the standards field`);
  }
}

for (const word of ISSUER_WORDS) {
  if (!allFieldWords.has(word)) {
    fail(`ISSUER_WORDS names "${word}", which no page carries any more: remove it so the list stays the one in use`);
  }
}

const bundle = path.join(distDir, '_astro');
let joined = '';
let styles = '';
for (const file of await readdir(bundle)) {
  if (file.endsWith('.js')) joined += await readFile(path.join(bundle, file), 'utf8');
  if (file.endsWith('.css')) styles += await readFile(path.join(bundle, file), 'utf8');
}
if (!joined.includes('metaWeights')) {
  fail('the built search bundle carries no metaWeights: the ranking never reaches the browser');
}
if (!joined.includes(SEARCH_TERM_NORMALIZER_MARK)) {
  fail(
    'the built search bundle carries no query normalizer: the Vite alias over ' +
      '@pagefind/default-ui in astro.config.mjs is no longer being applied',
  );
}
if (joined.includes('Search tokens for the designations')) {
  fail(
    'the built bundle carries src/data/standard-search-overrides.json: something in the browser ' +
      'imports src/lib/standard-search.mjs instead of src/lib/designation-query.mjs',
  );
}

// I. The field stays out of sight. The default result list prints every
// metadata field it does not know as a visible tag, keyed by the attribute
// below, and one rule in src/styles/search.css is all that hides ours. Both
// halves are checked on what was built: the upstream UI still writes that
// attribute and that tag list, and the stylesheet still hides the field with
// them. Otherwise every guide in the search panel would print its tokens.
for (const marker of ['data-pagefind-ui-meta', 'pagefind-ui__result-tags']) {
  if (!joined.includes(marker)) {
    fail(
      `the search UI no longer writes ${marker}, which src/styles/search.css keys on to hide ` +
        'the standards field: the panel would print the tokens under every guide',
    );
  }
}
// The rule has to select the tag itself. The second rule in search.css names
// the same attribute inside :not(), and it hides nothing on its own.
const hidden = [...styles.matchAll(/(?<![\w-])li\[data-pagefind-ui-meta=(["']?)standards\1\]/g)].some((match) => {
  const open = styles.indexOf('{', match.index);
  const close = styles.indexOf('}', open);
  const selector = styles.slice(match.index, open);
  return open !== -1 && !selector.includes('}') && /display:\s*none/.test(styles.slice(open, close));
});
if (!hidden) {
  fail(
    'no built stylesheet hides [data-pagefind-ui-meta=standards]: the search panel would print ' +
      'the standards tokens under every guide (src/styles/search.css)',
  );
}

const seconds = ((Date.now() - started) / 1000).toFixed(0);
if (failures.length > 0) {
  console.error(`\ncheck:search: ${failures.length} problem(s) in ${seconds}s\n`);
  for (const message of failures) console.error(`  - ${message}`);
  process.exit(1);
}
console.log(`check:search: ${designations.size} designations, ${built.size} pages, ${seconds}s. All good.`);
