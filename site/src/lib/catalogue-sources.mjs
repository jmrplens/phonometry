/**
 * The source of every table a catalogue page prints, held to the page's own
 * bibliography.
 *
 * Every row of a published catalogue names the page of the book it was read
 * on ("Arau-Puchades (1999) Table 4.1, PDF page 129 (printed p. 126)"), and the
 * reader sees that citation in the table. The page itself named no book: no
 * catalogue page had a `references` list, so the books behind every row had no
 * References section, and four of them (Arau-Puchades 1999, both Harris
 * handbooks and Rossing 2014) were cited by no page at all, which left them
 * out of the bibliography's structured data, where every other source the
 * site relies on is described once and named from the pages that cite it.
 *
 * Each catalogue page now lists the works its tables come from, and each such
 * entry says which tables it is the source of, by the key the table carries in
 * every row (`arau-1999-table-4-1`, src/generated/catalogues.mjs). The key is
 * how a row reaches its work without parsing the citation text, whose short
 * forms differ from book to book ("Bies 5e", "Harris (1977)"). The page build
 * (src/lib/catalogue-pages.ts) holds the two together both ways: a table no
 * entry claims, or claims twice, and a claimed table the page does not print,
 * each stop the build, in each language.
 *
 * The tables the library fixes itself (the airs its models assume, keyed
 * `phonometry-...`) were printed by no one and claim no source.
 *
 * A claim is held to the work that makes it, too. A table's key starts with
 * its work, so an entry that claims a key of another book (Harris's 1995
 * carpets under his 1977 handbook) is refused, rather than leaving the page
 * to name the wrong source for those rows.
 */

/**
 * Whether a content entry is a catalogue page, in either language.
 *
 * The overview of the catalogues (`reference/catalogues`) is not one: it
 * prints no table.
 *
 * @param {string} id A content entry id, `reference/catalogues/solids` or
 *   `es/reference/catalogues/solids`.
 * @returns {boolean}
 */
export function isCataloguePage(id) {
  return /^(?:es\/)?reference\/catalogues\/./.test(id);
}

/**
 * Whether a table is one the library fixes itself rather than reads off a page.
 *
 * @param {string} table A table key, as a catalogue row carries it.
 * @returns {boolean}
 */
export function isLibraryTable(table) {
  return table.startsWith('phonometry-');
}

/**
 * The tables some catalogues print, each once, in the order their rows come.
 *
 * @param {Iterable<{rows: {table: string}[]}>} catalogues The catalogues a page
 *   renders, as src/generated/catalogues.mjs holds them.
 * @returns {string[]}
 */
export function printedTables(catalogues) {
  const tables = new Set();
  for (const catalogue of catalogues) {
    for (const row of catalogue.rows) tables.add(row.table);
  }
  return [...tables];
}

/**
 * The pages that carry `tables` and are not catalogue pages, one message each.
 *
 * Nothing reads `tables` anywhere else, so an entry that carries it there
 * would look like the source of a table and hold nothing to it.
 *
 * @param {Iterable<{id: string, references?: object[]}>} pages Content
 *   entries, each with its frontmatter references.
 * @returns {string[]}
 */
export function strayTableClaims(pages) {
  return [...pages]
    .filter((page) => !isCataloguePage(page.id))
    .filter((page) => (page.references ?? []).some((ref) => ref.tables !== undefined))
    .map((page) => `${page.id} is not a catalogue page, and an entry of its references names \`tables\``);
}

/** Slugify a name the way src/lib/citations.mjs mints `@id` fragments. */
function slug(value) {
  return String(value)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

/**
 * The word a table key gives an organization whose name does not start with
 * it. Any other organization's key starts with the first word of its name.
 */
const ORGANIZATION_KEYS = new Map([
  ['American Society of Heating, Refrigerating and Air-Conditioning Engineers', 'ashrae'],
]);

/**
 * Why a table's key names another work than the entry that claims it, or
 * `undefined` when it names this one.
 *
 * A standard's key carries its issuer and its number (`iec-61094-2-annex-f`,
 * `en-12354-6-table-1`), and that number is in the designation; a series key
 * (`en-12354-annex-a`) carries the series number every part's designation
 * starts with. The issuer is not compared: one text carries the designations
 * of several bodies, and the EN 12354 series key is claimed by ISO
 * 12354-1:2017, which Europe publishes as EN ISO 12354-1:2017. Any other
 * work's key starts with the first word of its first author's surname, or of
 * its organization, and carries its year: `harris-1995-table-30-2`,
 * `norton-karczub-2003-table-3-1` (Norton and Karczub), `arau-1999-table-4-1`
 * (Arau-Puchades), `ashrae-2019-table-40`.
 *
 * @param {object} ref A frontmatter reference.
 * @param {string} table A table key it claims.
 * @returns {string|undefined}
 */
function keyMismatch(ref, table) {
  if (ref.type === 'standard') {
    const number = /^[a-z]+(?:-[a-z]+)*-(\d+(?:-\d+)*)/.exec(table)?.[1];
    if (!number) return 'the key carries no standard number';
    if (!new RegExp(`(?<!\\d)${number}(?!\\d)`).test(String(ref.designation ?? ''))) {
      return `the key's number, ${number}, is not in the designation`;
    }
    return undefined;
  }
  const author = ref.authors?.[0];
  const who = author
    ? slug(String(author).split(',')[0]).split('-')[0]
    : (ORGANIZATION_KEYS.get(ref.organization) ?? slug(ref.organization ?? '').split('-')[0]);
  const reasons = [];
  if (!who || table.split('-')[0] !== who) reasons.push(`a key of this work starts with ${who || '(no author)'}-`);
  if (ref.year === undefined || !`${table}-`.includes(`-${ref.year}-`)) {
    reasons.push(`a key of this work carries its year, ${ref.year ?? '(none)'}`);
  }
  return reasons.length > 0 ? reasons.join(', and ') : undefined;
}

/** How a message names a reference: its designation or number, else its lead name and year. */
function label(ref) {
  if (ref.designation) return ref.designation;
  if (ref.number) return ref.number;
  const who = ref.authors?.[0]?.split(',')[0] ?? ref.organization ?? ref.title;
  return ref.year === undefined ? who : `${who} (${ref.year})`;
}

/**
 * What is wrong with the sources a catalogue page names, or an empty list.
 *
 * Every table the page prints, other than the library's own, is claimed by
 * exactly one entry of the page's references through that entry's `tables`;
 * every table an entry claims is one the page prints, and its key names that
 * entry's work; and no entry claims a table of the library's own, which has
 * no printed source to name.
 *
 * @param {object} options
 * @param {string} options.page The page's entry id, which the messages name.
 * @param {object[]} options.references The page's frontmatter references.
 * @param {string[]} options.tables The tables the page prints (printedTables).
 * @returns {string[]} One message per defect.
 */
export function catalogueSourceProblems({ page, references, tables }) {
  const problems = [];
  const claims = new Map();
  for (const ref of references) {
    for (const table of ref.tables ?? []) {
      if (!claims.has(table)) claims.set(table, []);
      claims.get(table).push(label(ref));
      const mismatch = isLibraryTable(table) ? undefined : keyMismatch(ref, table);
      if (mismatch) problems.push(`${page}: ${label(ref)} claims ${table}, a table of another work (${mismatch})`);
    }
  }
  const printed = new Set(tables);
  for (const table of tables) {
    if (isLibraryTable(table)) continue;
    const by = claims.get(table) ?? [];
    if (by.length === 0) {
      problems.push(`${page} prints rows of ${table}, and no entry of its references names it in \`tables\``);
    } else if (by.length > 1) {
      problems.push(`${page}: ${table} is claimed by ${by.length} entries of its references (${by.join('; ')}); one work printed it`);
    }
  }
  for (const [table, by] of claims) {
    if (isLibraryTable(table)) {
      problems.push(`${page}: ${by.join('; ')} claims ${table}, a table the library fixes itself and no work printed`);
    } else if (!printed.has(table)) {
      problems.push(`${page}: ${by.join('; ')} claims ${table}, which no catalogue on the page prints`);
    }
  }
  return problems;
}
