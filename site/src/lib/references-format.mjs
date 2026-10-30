/**
 * A page's bibliography as APA 7 citations, in either language, for the two
 * places that print it: the References section of the page
 * (src/components/References.astro) and the References section of its
 * Markdown copy (src/lib/agent-md/page.mjs).
 *
 * Both read the typed `references` list of the page frontmatter (schema in
 * src/content.config.ts). The copy used to have no references at all, and a
 * second formatter written for it would have been a second reading of APA
 * that drifted from the first; so the wording lives here once, and each of
 * the two only decides how a fragment is marked up.
 *
 * Three deliberate departures from strict APA 7, and nothing else:
 *  - a standard prints its designation alone, `(IEC 61672-1:2013)`, rather than
 *    APA's `(IEC Standard No. 61672-1:2013)`, because the designation is how
 *    the rest of the site and the conformance tables name the document;
 *  - the title carries the link when a catalogue or store URL exists, so the
 *    link text is descriptive instead of a bare URL trailing the entry;
 *  - an entry may carry a note, which follows as an annotation line,
 *    annotated-bibliography style.
 *
 * The DOI form is not one of them: `https://doi.org/<doi>` with nothing after
 * it, not even a period, is what APA 7 asks for.
 *
 * Plain JavaScript with JSDoc rather than TypeScript, so the copy can import it
 * in plain Node, outside the Astro build.
 *
 * @module
 */

/**
 * One reference of the frontmatter list, as the schema in
 * src/content.config.ts defines it, narrowed to what is printed.
 *
 * @typedef {object} Reference
 * @property {'standard' | 'book' | 'report' | 'web' | 'article'} type
 * @property {string} title
 * @property {string[]} [authors]
 * @property {string} [organization]
 * @property {number | string} [year]
 * @property {string} [designation]  A standard's.
 * @property {string} [edition]  A book's.
 * @property {string} [number]  A report's.
 * @property {string} [publisher]
 * @property {string} [institution]
 * @property {string} [siteName]
 * @property {string} [journal]
 * @property {number | string} [volume]
 * @property {number | string} [issue]
 * @property {string} [pages]
 * @property {string} [url]
 * @property {string} [doi]
 * @property {string} [note]
 */

/**
 * One fragment of a citation: plain, italicized or linked text.
 *
 * @typedef {object} Part
 * @property {string} text
 * @property {'cite' | 'i'} [italic]  'cite' for work titles, 'i' for
 *   typographic italics (a journal volume).
 * @property {string} [href]
 */

/** @param {string} lang */
const isSpanish = (lang) => lang.startsWith('es');

/**
 * "Fastl, H." + "Zwicker, E." -> "Fastl, H., & Zwicker, E.". The Spanish
 * adaptation of APA-7 joins the last author with "y" (and no comma) instead
 * of the ampersand: "Fastl, H. y Zwicker, E."
 *
 * @param {readonly string[]} authors
 * @param {string} lang
 * @returns {string}
 */
export function joinAuthors(authors, lang) {
  if (authors.length === 1) return authors[0];
  const separator = isSpanish(lang) ? ' y ' : ', & ';
  return `${authors.slice(0, -1).join(', ')}${separator}${authors[authors.length - 1]}`;
}

/**
 * The author position: the authors, or the organization.
 *
 * @param {Reference} ref
 * @param {string} lang
 * @returns {string}
 */
export function who(ref, lang) {
  if (ref.authors?.length) return joinAuthors(ref.authors, lang);
  if (ref.organization) return ref.organization;
  // The schema (superRefine in content.config.ts) guarantees an author
  // position for every entry type, so this is unreachable for valid content.
  throw new Error(`reference "${ref.title}" has neither authors nor organization`);
}

/**
 * @param {Reference} ref
 * @param {string} lang
 * @returns {string}
 */
export function yearLabel(ref, lang) {
  if (ref.year === undefined) return isSpanish(lang) ? 's. f.' : 'n.d.';
  return String(ref.year);
}

/**
 * Parenthetical right after the title: edition, designation or report number.
 *
 * @param {Reference} ref
 * @returns {string | undefined}
 */
export function titleSuffix(ref) {
  switch (ref.type) {
    case 'standard':
      return ref.designation;
    case 'book':
      return ref.edition;
    case 'report':
      return ref.number;
    default:
      return undefined;
  }
}

/**
 * The source segment after the title: publisher, journal locator or site.
 *
 * @param {Reference} ref
 * @returns {Part[]}
 */
export function sourceParts(ref) {
  switch (ref.type) {
    case 'book':
      return [{ text: ref.publisher ?? '' }];
    case 'standard':
      // APA omits the publisher when it repeats the authoring organization.
      return ref.publisher && ref.publisher !== ref.organization ? [{ text: ref.publisher }] : [];
    case 'report':
      return ref.institution && ref.institution !== ref.organization ? [{ text: ref.institution }] : [];
    case 'web':
      return ref.siteName ? [{ text: ref.siteName }] : [];
    case 'article': {
      /** @type {Part[]} */
      const parts = [{ text: ref.journal ?? '', italic: 'cite' }];
      if (ref.volume !== undefined) {
        parts.push({ text: ', ' }, { text: String(ref.volume), italic: 'i' });
        if (ref.issue !== undefined) parts.push({ text: `(${ref.issue})` });
      }
      if (ref.pages) parts.push({ text: `, ${ref.pages}` });
      return parts;
    }
    default:
      return [];
  }
}

/**
 * The "Author. (Year)." that opens every entry, kept apart from the rest so
 * each place that prints it can give it the weight a reader scans a
 * bibliography for. It is always plain text: neither the author position nor
 * the year is ever a link or italicised, so unlike the rest of the citation it
 * needs no fragments.
 *
 * @param {Reference} ref
 * @param {string} lang
 * @returns {string}
 */
export function opening(ref, lang) {
  const author = who(ref, lang);
  return `${author.endsWith('.') ? author : `${author}.`} (${yearLabel(ref, lang)}).`;
}

/**
 * The rest of the citation as fragments, APA-7 punctuation included.
 *
 * @param {Reference} ref
 * @returns {Part[]}
 */
export function citationParts(ref) {
  /** @type {Part[]} */
  const parts = [];
  /** @type {'cite' | undefined} */
  const italicTitle = ref.type === 'article' ? undefined : 'cite';

  parts.push({ text: ' ' });
  parts.push({ text: ref.title, italic: italicTitle, href: ref.url });
  const suffix = titleSuffix(ref);
  if (suffix) parts.push({ text: ` (${suffix})` });
  parts.push({ text: '. ' });

  const source = sourceParts(ref);
  if (source.length) {
    parts.push(...source);
    parts.push({ text: '. ' });
  }
  if (ref.doi) {
    // APA-7: nothing follows a DOI, not even a period.
    const doiUrl = `https://doi.org/${ref.doi}`;
    parts.push({ text: doiUrl, href: doiUrl });
  }
  return parts;
}

/**
 * Note text split so bare URLs become links (e.g. a revision or index page).
 * The final character class keeps trailing sentence punctuation (".", ","...)
 * out of the link when the URL ends a clause.
 *
 * @param {string} note
 * @returns {Part[]}
 */
export function noteParts(note) {
  return note
    .split(/(https?:\/\/[^\s)]*[^\s.,;:)])/)
    .filter((piece) => piece !== '')
    .map((piece) => (piece.startsWith('http') ? { text: piece, href: piece } : { text: piece }));
}

/**
 * APA orders alphabetically by first author surname or organization; no-date
 * entries precede dated ones for the same author, then year, then title.
 *
 * @param {Reference} ref
 * @param {string} lang
 * @returns {string}
 */
export function sortKey(ref, lang) {
  const year = ref.year === undefined ? '' : String(ref.year);
  return `${who(ref, lang)} ${year} ${ref.title}`.toLowerCase();
}

/**
 * The entries in the order the section prints them, each with its position in
 * the frontmatter list, which is what its fragment id is derived from
 * (`referenceAnchors` in src/lib/reference-chips.ts), so sorting for display
 * does not change the ids.
 *
 * @template {Reference} R
 * @param {readonly R[]} references
 * @param {string} lang
 * @returns {[number, R][]}
 */
export function sortedReferences(references, lang) {
  return [...references.entries()].sort(([, a], [, b]) =>
    sortKey(a, lang).localeCompare(sortKey(b, lang), lang, { sensitivity: 'base' }),
  );
}
