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
 */

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
 * every table an entry claims is one the page prints; and no entry claims a
 * table of the library's own, which has no printed source to name.
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
