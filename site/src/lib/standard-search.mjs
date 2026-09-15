/**
 * Search tokens for the standards a page declares.
 *
 * A reader looking for "ISO 3744" wants the guides that are written to ISO
 * 3744, and until now the order ignored that entirely: the chips and the
 * bibliography are indexed as ordinary prose at weight 1, so the page that
 * happens to say "3744" most often wins, declaring page or not. The fix is to
 * hand Pagefind a separate metadata field carrying the designations the page
 * declares, and to weight that field (src/lib/search-ranking.mjs). The field is
 * derived here, from the same `references` frontmatter the chips and the
 * References section already come from, so there is no second source of truth
 * to keep in step and no page to migrate.
 *
 * Written as .mjs with JSDoc rather than .ts on purpose: the build-time check
 * in scripts/check-search-designation.mjs imports it under plain Node, which
 * must not depend on type stripping being available.
 *
 * WHAT GOES IN THE FIELD, AND WHAT DOES NOT
 *
 * Only two kinds of word survive: an issuer acronym written in capitals in front
 * of its number, and a token containing a digit. Ordinary words are deliberately excluded, because
 * a weighted field is a blunt instrument. "Standard", "Annex", "Directive",
 * "Recommendation" and "Blatt" all appear inside designations, and indexing
 * them at a multiplier was measured to reorder searches that have nothing to do
 * with designations: searching for "blatt" pushed the two pages that explain
 * what a Blatt is down the list in favour of pages that merely cite one. Those
 * words carry lowercase letters, which is what the issuer rule below keys on,
 * so they never reach the field.
 *
 * Numbers are emitted as progressive joins, "iso 8041 80411 804112017" rather
 * than "ISO 8041-1:2017", because Pagefind deletes punctuation from a query
 * without splitting the word: a reader typing "ISO 8041-1:2017" searches for
 * the single term `804112017`, one typing "ISO 8041-1" searches for `80411`,
 * and every term matches by prefix. Pre-joining is what makes all three
 * spellings of the same standard land on the same pages.
 *
 * National adoption prefixes (UNE-EN, BS EN, DIN EN) are handled at the other
 * end, in src/lib/designation-query.mjs, by interpreting what the reader typed.
 * They are deliberately not written into the index: the bibliography records
 * the designation the page was actually written to, and adding "UNE-EN" to it
 * would have the site assert an adoption nobody has verified.
 *
 * This module is build-time only. The search panel needs the query side and
 * nothing else, so it imports designation-query.mjs directly and this file,
 * with the overrides table it reads, never reaches the browser.
 */

import overrides from '../data/standard-search-overrides.json' with { type: 'json' };
import { isAlternativeDesignation, segmentsOf } from './designation-query.mjs';

/**
 * Designations no rule can parse, with the tokens to use instead.
 *
 * Kept as data rather than as special cases in the tokenizer, and kept small:
 * a designation that produces no token carrying a digit throws rather than
 * indexing nothing, so a new shape shows up as a failed build on the pull
 * request that introduces it, which is where it can be decided.
 *
 * @type {Record<string, string[]>}
 */
export const DESIGNATION_OVERRIDES = Object.fromEntries(
  Object.entries(overrides).filter(([key]) => !key.startsWith('_')),
);

/**
 * Issuer acronyms whose English and Spanish spellings differ.
 *
 * The site publishes every page twice and the two bibliographies name the same
 * document, so the two indexes have to carry the same tokens or a search works
 * in one language and not in the other. There are exactly two cases in the
 * corpus: the ITU, which is the UIT in Spanish, and the document code of a
 * European directive, whose final segment is EC in English and CE in Spanish
 * (2002/44/EC and 2002/44/CE are one directive). Both directions are listed, so
 * the expansion is symmetric whichever spelling a page used.
 *
 * A new pair belongs here, never in the page content.
 *
 * @type {Record<string, string>}
 */
export const ISSUER_ALIASES = {
  itu: 'uit',
  uit: 'itu',
};

/** Suffix pair for the document code of a European directive: 2002/44/EC = 2002/44/CE. */
const DIRECTIVE_CODE_ALIASES = { ec: 'ce', ce: 'ec' };

const TOKEN_SHAPE = /^[a-z0-9]+$/;

const hasDigit = (s) => /[0-9]/.test(s);
const isAlpha = (s) => /^[A-Za-z]+$/.test(s);
const hasLower = (s) => /[a-z]/.test(s);

/**
 * An ordinal, in either language: "108th", "3rd", "22.ª", "5.º". It counts an
 * edition or a meeting and never names a document, so it never becomes a token.
 */
const ORDINAL = /^[0-9]+(?:st|nd|rd|th|\.?[ªº])$/i;

/**
 * A year and a month run together, which is what the German edition date
 * ":2001-07" turns into once its punctuation is gone. Like a bare year, it is
 * dropped unless it is the whole word.
 */
const YEAR_MONTH = /^(?:19|20)[0-9]{2}(?:0[1-9]|1[0-2])$/;

/**
 * "VDI 2081 Blatt 1" is VDI 2081-1 written the German way, and "Teil" and
 * "Part" are the same idea. The hyphenated form is added next to the number as
 * written, so the part gets its own join (20811) exactly as "ISO 8041-1" gets
 * 80411, and the two sheets of one guideline stop indexing identically. The
 * number keeps its own word because a four-digit family can look like a year
 * ("2081") and would otherwise be dropped as one. Only a one- or two-digit
 * number directly after a number is taken for a part: the "Ber 1" of a DIN
 * corrigendum is not a part and stays out.
 */
const PART_WORD = /(?<![0-9])([0-9]+)\s+(?:Blatt|Teil|Part)\s+([0-9]{1,2})(?![0-9])/g;

/**
 * Add the hyphenated form of every "Blatt N", "Teil N" or "Part N" that follows
 * a number, keeping the words as written.
 *
 * Exported for the build-time check, which judges a query such as "VDI 2081
 * Blatt 2" by the part it names and not by the family alone.
 *
 * @param {string} text
 * @returns {string}
 */
export function foldPartWords(text) {
  return String(text ?? '').replace(PART_WORD, '$1 $1-$2');
}

/**
 * Tokens for one word that contains a digit.
 *
 * The word is segmented, then emitted as the progressive joins of those
 * segments: "60534-8-3:2010" gives 60534, 605348, 6053483, 60534832010, so that
 * the family, the part, the sub-part and the full designation each match. When
 * the word opens with an issuer glued to the number ("ECMA-418-1:2024",
 * "BS.1770-5") the joins starting at the second segment are emitted too, so the
 * designation is found whether the reader writes the issuer attached or
 * separated. A join that carries no digit of its own is dropped: it is an
 * issuer fragment, and issuers are the other rule's business.
 *
 * Nothing that is only an ordinal or only a date comes out of here, which is
 * what lets designationTokens trust any token carrying a digit as evidence the
 * designation was understood.
 *
 * @param {string} word
 * @returns {string[]}
 */
function digitWordTokens(word) {
  if (ORDINAL.test(word)) return [];
  const segs = segmentsOf(word);
  if (segs.length === 0) return [];
  const whole = segs.join('').toLowerCase();
  const starts = [0];
  // An issuer glued to the number, or a bare leading number such as the "1"
  // of the corrigendum "Ber 1:2012-12", is worth nothing on its own. Whatever
  // follows it is still considered, and the date rules below throw out what is
  // only an edition.
  if (segs.length > 1 && (isAlpha(segs[0]) || /^[0-9]$/.test(segs[0]))) starts.push(1);
  if (/^[0-9]$/.test(segs[0])) starts.shift();

  const out = [];
  for (const start of starts) {
    let joined = '';
    for (let i = start; i < segs.length; i += 1) {
      joined += segs[i];
      const token = joined.toLowerCase();
      if (!hasDigit(token)) continue; // issuer fragment
      if (token.length < 2) continue;
      const isWholeWord = token === whole;
      // A two-digit number only means something as a whole designation
      // ("ICAO Annex 16"); inside a longer one it is a part number that
      // would match far too much.
      if (/^[0-9]{1,2}$/.test(token) && !isWholeWord) continue;
      // An edition year is not a designation. Without this, every page
      // declaring a 1996 edition of anything would answer to "ISO 1996".
      if (/^(19|20)[0-9]{2}$/.test(token) && !isWholeWord) continue;
      // Nor is an edition month. "VDI 2081 Blatt 1:2001-07" used to index
      // 200107, which no reader types and which a search for "2001" matched
      // at the full weight of the field.
      if (YEAR_MONTH.test(token) && !isWholeWord) continue;
      out.push(token);
    }
  }
  return out;
}

/**
 * Tokens for one word that contains no digit: an issuer acronym, or nothing.
 *
 * "ISO/TS" gives iso and ts, "ANSI/ASA" gives ansi and asa, "ITU-R" gives itu.
 * The glued form (isots, ansiasa) is never emitted: a second token sharing the
 * prefix inflates the field's contribution, and that was measured to reorder
 * the declaring pages among themselves, a guide that declares both ISO 1996 and
 * ISO/PAS 1996-3 overtaking one whose subject is the query.
 *
 * A word carrying a lowercase letter is not an issuer. That single rule is what
 * keeps "Standard", "Annex", "Directive", "Recommendation", "Publication",
 * "Technical", "Blatt" and "Ley" out of a weighted field. The caller adds the
 * second rule, about position: see designationTokens.
 *
 * @param {string} word
 * @returns {string[]}
 */
function issuerWordTokens(word) {
  if (hasLower(word)) return [];
  const letters = word.replace(/[^A-Za-z]/g, '');
  if (letters.length < 2) return [];
  return segmentsOf(word)
    .filter((s) => isAlpha(s) && s.length >= 2)
    .map((s) => s.toLowerCase());
}

/**
 * Expand a token list with the aliases that keep the English and Spanish
 * indexes identical.
 *
 * @param {string[]} tokens
 * @returns {string[]}
 */
function withAliases(tokens) {
  const out = [];
  for (const token of tokens) {
    out.push(token);
    // Own properties only, throughout this module: a token is an arbitrary
    // lowercase word, and a plain object answers "constructor" and
    // "toString" with something inherited that is not a table entry.
    if (Object.hasOwn(ISSUER_ALIASES, token)) out.push(ISSUER_ALIASES[token]);
    // The directive code: only the trailing letters of a token that carries
    // a number, so "2002/44/EC" gains 200244ce while the word "ec" on its
    // own gains nothing.
    if (hasDigit(token)) {
      const tail = /[a-z]+$/.exec(token);
      if (tail && Object.hasOwn(DIRECTIVE_CODE_ALIASES, tail[0])) {
        out.push(token.slice(0, tail.index) + DIRECTIVE_CODE_ALIASES[tail[0]]);
      }
    }
  }
  return out;
}

/**
 * The search tokens for one designation as the bibliography spells it.
 *
 * @param {string} designation e.g. "ISO 8041-1:2017"
 * @returns {string[]} e.g. ["iso", "8041", "80411", "804112017"]
 * @throws if the designation yields no token carrying a digit and has no entry
 *   in src/data/standard-search-overrides.json.
 */
export function designationTokens(designation) {
  const literal = String(designation ?? '').trim();
  if (Object.hasOwn(DESIGNATION_OVERRIDES, literal)) return [...DESIGNATION_OVERRIDES[literal]];

  // The tail after a comma is where the two languages diverge (", 3rd ed."
  // against ", 3.ª ed.", ", the GUM" against ", la GUM"), so it is cut. It
  // usually carries no number, but not always: "108th AES Convention, Paris,
  // preprint 5093" keeps its only identifying number there. Such an entry has
  // nothing left that identifies it, so the check below throws and the
  // overrides file decides its tokens; the tail is never read on a guess.
  let body = foldPartWords(literal.split(',')[0]);

  // Parentheses either name the document another way or describe its edition.
  const extra = [];
  body = body.replace(/\(([^)]*)\)/g, (_match, inner) => {
    if (isAlternativeDesignation(inner)) extra.push(inner);
    return ' ';
  });

  const tokens = [];
  // The body and each alternative designation are read on their own, because
  // the position rule below is about one designation at a time.
  for (const segment of [body, ...extra]) {
    // "+" joins a standard to its amendment ("IEC 60268-5:2003+A1:2007");
    // both halves are designations in their own right.
    const words = segment.split(/[\s+]+/).filter(Boolean);
    // An issuer is written in front of its number. A word in capitals after
    // the last number describes the publication, not the document: IEC's CSV
    // for a consolidated version ("IEC 61400-11:2012+AMD1:2018 CSV"), the
    // language code of a JRC report ("EUR 25379 EN"). Indexed at a
    // multiplier, CSV put a wind-turbine guide first on a search for "csv".
    const lastNumber = words.findLastIndex(hasDigit);
    words.forEach((word, i) => {
      if (hasDigit(word)) tokens.push(...digitWordTokens(word));
      else if (i < lastNumber) tokens.push(...issuerWordTokens(word));
    });
  }

  const out = [];
  for (const token of withAliases(tokens)) {
    if (!TOKEN_SHAPE.test(token)) {
      throw new Error(
        `standard-search: designation ${JSON.stringify(literal)} produced the malformed token ${JSON.stringify(token)}`,
      );
    }
    if (!out.includes(token)) out.push(token);
  }

  // Any token carrying a digit is enough here because digitWordTokens emits no
  // ordinal and no bare edition date. Before it did, "108th" alone let a
  // preprint through with its number lost.
  if (!out.some(hasDigit)) {
    throw new Error(
      `standard-search: designation ${JSON.stringify(literal)} produced no token carrying a number ` +
        `(tokens: ${JSON.stringify(out)}). Add it to src/data/standard-search-overrides.json ` +
        `with the tokens a reader would search it by.`,
    );
  }
  return out;
}

/**
 * The search tokens for a page, from its `references` frontmatter.
 *
 * Every declared standard is indexed, including the ones whose chip does not
 * fit under the nine-chip cap: the cap is a layout budget, not a statement
 * about which standards govern the page, and the "+N more" chip points at the
 * bibliography where those standards are printed in full.
 *
 * @param {Array<{type?: string, designation?: string, number?: string}>|undefined} references
 * @returns {string[]} deduplicated, in the order the bibliography declares them
 */
export function pageStandardTokens(references) {
  const out = [];
  for (const ref of references ?? []) {
    const literal = ref?.type === 'standard' ? ref.designation : ref?.type === 'report' ? ref.number : undefined;
    if (!literal) continue;
    for (const token of designationTokens(literal)) {
      if (!out.includes(token)) out.push(token);
    }
  }
  return out;
}
