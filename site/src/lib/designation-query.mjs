/**
 * What a reader typed, read as a standard designation.
 *
 * This is the only part of the designation search that runs in the browser, so
 * it lives apart from src/lib/standard-search.mjs: that module builds the index
 * tokens at build time and carries its overrides table with it, and none of
 * that has any business in the search panel's script. Keeping the two apart is
 * what keeps the table out of the client bundle; importing the tokenizer from
 * here would put it back.
 *
 * Written as .mjs with JSDoc for the same reason as the tokenizer: the
 * build-time check in scripts/check-search-designation.mjs imports it under
 * plain Node.
 */

/**
 * Stamped into the built bundle by src/lib/search-ui.mjs so the build-time
 * check can prove the query normalizer is actually wired into the search UI.
 * The wiring is a Vite alias, which fails silently if Starlight ever stops
 * importing the package by its bare name.
 */
export const SEARCH_TERM_NORMALIZER_MARK = 'phonometry-designation-normalizer-v1';

/**
 * Split a word the way Pagefind splits an indexed word: at runs of characters
 * that are not ASCII letters or digits, and at a lowercase-to-uppercase
 * boundary. Accented letters count as separators, which is what keeps
 * "Recomendación" and "3.ª" from producing half-words.
 *
 * Shared with the tokenizer in src/lib/standard-search.mjs, so the index and the
 * query cut a designation in the same places.
 *
 * @param {string} word
 * @returns {string[]}
 */
export function segmentsOf(word) {
  const out = [];
  for (const chunk of word.split(/[^0-9A-Za-z]+/)) {
    if (!chunk) continue;
    let start = 0;
    for (let i = 1; i < chunk.length; i += 1) {
      if (/[a-z]/.test(chunk[i - 1]) && /[A-Z]/.test(chunk[i])) {
        out.push(chunk.slice(start, i));
        start = i;
      }
    }
    out.push(chunk.slice(start));
  }
  return out;
}

/**
 * Is this parenthetical an alternative designation, or an edition note?
 *
 * "(EN ISO 7235:2009)" and "(BOE-A-2003-20976)" name the same document another
 * way and are worth indexing. "(3rd ed.)", "(Edición 5)", "(R2017)",
 * "(11/2023)" and "(withdrawn)" say something about the edition and are not.
 * The test is structural rather than a list of words: an alternative
 * designation carries both an issuer written in capitals and a number.
 *
 * @param {string} inner
 * @returns {boolean}
 */
export function isAlternativeDesignation(inner) {
  const segs = segmentsOf(inner);
  return (
    segs.some((s) => /[0-9]/.test(s)) && segs.some((s) => /^[A-Z]{2,}$/.test(s))
  );
}

/**
 * The prefixes the national members of CEN put in front of a European or
 * international standard they adopt: UNE-EN ISO in Spain, BS EN ISO in the
 * United Kingdom, DIN EN ISO in Germany, NEN-EN-ISO in the Netherlands, and so
 * on. The list is the membership, not a guess at which ones a reader is likely
 * to type, so a new spelling of an adoption is a new row here rather than a new
 * rule. Each entry is a regular expression source; the Latin spellings of the
 * accented, Greek and Cyrillic ones are listed too, because that is how most
 * keyboards produce them.
 */
export const NATIONAL_ADOPTION_PREFIXES = [
  'BDS', // Bulgaria
  'BS', // United Kingdom
  'ČSN', 'CSN', // Czech Republic
  'CYS', // Cyprus
  'DIN', // Germany
  'DS', // Denmark
  'ΕΛΟΤ', 'ELOT', // Greece
  'EVS', // Estonia
  'HRN', // Croatia
  'I\\.S\\.', // Ireland
  'ILNAS', // Luxembourg
  'ÍST', 'IST', // Iceland
  'LST', // Lithuania
  'LVS', // Latvia
  'МКС', 'MKS', // North Macedonia
  'MSA', // Malta
  'MSZ', // Hungary
  'NBN', // Belgium
  'NEN', // Netherlands
  'NF', // France
  'NP', // Portugal
  'NS', // Norway
  'ÖNORM', 'ONORM', 'OENORM', // Austria
  'PN', // Poland
  'SFS', // Finland
  'SIST', // Slovenia
  'SN', // Switzerland
  'SR', // Romania
  'SRPS', // Serbia
  'SS', // Sweden
  'STN', // Slovakia
  'TS', // Türkiye
  'UNE', // Spain
  'UNI', // Italy
];

const NATIONAL = `(?:${NATIONAL_ADOPTION_PREFIXES.join('|')})`;
/** Between the parts of an adoption prefix: a space, a hyphen or a slash. */
const SEP = '[\\s\\-/]';
/** ISO or IEC as a whole word, so "isolation" never counts as the issuer. */
const INTERNATIONAL = '(?=(?:ISO|IEC)(?![A-Za-z]))';

/**
 * A national prefix, with or without the EN of a European adoption, in front of
 * an ISO or IEC number. It may follow other words ("norma UNE-EN ISO 3744"),
 * so it is looked for at the start of any word, not only at the start of the
 * query.
 */
const NATIONAL_BEFORE_INTERNATIONAL = new RegExp(
  `(^|\\s)${NATIONAL}(?:${SEP}*EN)?${SEP}+${INTERNATIONAL}`,
  'iu',
);

/** A national prefix in front of a European number: UNE-EN 12354-1 is EN 12354-1. */
const NATIONAL_BEFORE_EUROPEAN = new RegExp(`(^|\\s)${NATIONAL}${SEP}*EN${SEP}+(?=[0-9])`, 'iu');

/**
 * A bare EN in front of an ISO or IEC number. Anchored at the start of the
 * query on purpose: "en" is also the Spanish preposition, and "ruido en ISO
 * 1996" must keep its first word.
 */
const EUROPEAN_BEFORE_INTERNATIONAL = new RegExp(`^\\s*EN${SEP}+${INTERNATIONAL}`, 'i');

/**
 * A note in brackets straight after a number: "ECMA-418-2:2025 (4.ª ed.)",
 * "ANSI S3.5-1997 (R2017)", "BS.1770-5 (11/2023)". The index leaves every such
 * note out, so a query copied from a bibliography has to leave it out too, or
 * its words become terms no page's field can answer. An alternative designation
 * in brackets stays, because the index keeps it.
 */
const BRACKETED_NOTE = /([0-9][^\s()]*)\s*\(([^)]*)\)/g;

/**
 * An issuer as a reader may type it: "ANSI", "ansi" or "Ansi". Two letters or
 * more, and no lowercase letter followed by a capital, which is where
 * segmentsOf cuts a word in two: "mV" and "dB" are not one word to the index,
 * let alone an issuer.
 */
const ISSUER_AS_TYPED = '(?=[A-Za-z]{2})[A-Z]*[a-z]*';

/**
 * Issuers printed glued together by a slash or a dot: ISO/TS, ANSI/ASA,
 * ECAC.CEAC. Pagefind would search for the single term `ansiasa`, which the
 * index never carries: it keeps each issuer as a word of its own.
 */
const GLUED_ISSUERS = new RegExp(`^${ISSUER_AS_TYPED}(?:[/.]${ISSUER_AS_TYPED})+$`);

/**
 * The sector letter of an ITU recommendation, ITU-R or UIT-T. Pagefind would
 * search for `itur`; the index keeps the issuer and drops a single letter.
 */
const SECTOR_LETTER = new RegExp(`^(${ISSUER_AS_TYPED})-[A-Za-z]$`);

/**
 * Split glued issuers and drop the sector letter, for the words of the query
 * that are issuers.
 *
 * The index tells an issuer from an ordinary word by two rules: it is written
 * in capitals, and it stands in front of its number. A query in capitals is
 * read by the first rule alone, as it always was. A query typed in lowercase,
 * or capitalised, has lost that evidence, so it is read by the second: "ansi/asa
 * s12.2-2019" and "itu-r bs.1770-5" are split because a number follows them,
 * while "mv/pa" or "input/output" with no number after them stay the single term
 * the reader typed.
 *
 * @param {string} text
 * @returns {string}
 */
function separateIssuers(text) {
  // Whitespace is kept at the odd indices, so joining restores the query.
  const words = text.split(/(\s+)/);
  // Not findLastIndex, which the older Safari this panel still serves lacks.
  const lastNumber = words.map((word) => /[0-9]/.test(word)).lastIndexOf(true);
  return words
    .map((word, i) => {
      if (/[a-z]/.test(word) && i >= lastNumber) return word;
      if (GLUED_ISSUERS.test(word)) return word.split(/[/.]/).join(' ');
      const sector = SECTOR_LETTER.exec(word);
      return sector ? sector[1] : word;
    })
    .join('');
}

/**
 * The edition at the end of a designation: ":2015", "-2015" or the German
 * ":2015-06". The digit in front is required, so the number of a Eurocode
 * such as "EN 1996" is never taken for a year. It is captured and put back
 * rather than asserted with a lookbehind, which older Safari cannot parse: a
 * syntax error here would take the whole search panel down with it.
 */
const TRAILING_EDITION = /([0-9])[:-](?:19|20)[0-9]{2}(?:-[0-9]{2})?\s*$/;

/**
 * The one function that touches what a reader typed.
 *
 * A Spanish reader looks for UNE-EN ISO 3744 and a British one for BS EN ISO
 * 3744; both are the national adoption of ISO 3744, and no page declares
 * either. Pagefind deletes the hyphen without splitting, so "UNE-EN ISO 3744"
 * searches for the term `uneen`, which appears on no guide at all, and the
 * search returns nothing useful. Stripping the prefix from the query is the
 * honest half of the fix: it changes what is searched for, not what the site
 * claims about the standard.
 *
 * When a national prefix is removed, the edition goes with it. The year of an
 * adoption is the year the national body published it, which is often not the
 * year of the document the bibliography declares: UNE-EN ISO 16283-1:2015
 * adopts ISO 16283-1:2014, and UNE-EN ISO 717-1:2021 adopts ISO 717-1:2020.
 * Kept, it searches for an edition no page is written to and the guide drops
 * out of the results; dropped, the search only widens to every edition of the
 * same document. A query with no national prefix keeps its edition, so
 * ISO 1996-2:2007 and ISO 1996-2:2017 are still told apart.
 *
 * The other rules exist because a reader copies a designation the way a
 * bibliography prints it, and the index is built from the same text with some
 * of it deliberately left out. Wherever the index drops something, the query
 * has to drop it too, or it searches for a term no field carries and the pages
 * written to the standard fall back to competing on their prose: a note in
 * brackets after the number, issuers glued by a slash or a dot, the sector
 * letter of an ITU recommendation.
 *
 * Everything else is left exactly as typed, and the search box keeps showing
 * the reader's own words.
 *
 * @param {string} query
 * @returns {string}
 */
export function normalizeDesignationQuery(query) {
  const typed = String(query ?? '');
  const unbracketed = typed.replace(BRACKETED_NOTE, (match, number, inner) =>
    isAlternativeDesignation(inner) ? match : number,
  );
  let text = unbracketed
    .replace(NATIONAL_BEFORE_INTERNATIONAL, '$1')
    .replace(NATIONAL_BEFORE_EUROPEAN, '$1EN ');
  if (text !== unbracketed) text = text.replace(TRAILING_EDITION, '$1');
  return separateIssuers(text.replace(EUROPEAN_BEFORE_INTERNATIONAL, ''));
}
