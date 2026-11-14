// Every table a catalogue page prints names the work it was read from.
//
// src/lib/catalogue-sources.mjs holds a catalogue page's rows to its
// frontmatter `references`, and src/lib/catalogue-pages.ts stops the build on
// what it finds. The first tests hand the functions small pages with each
// defect they exist for; the last two read the real pages of both languages,
// so the gate fails here, before a twenty-minute build, when a page loses or
// never had the source of one of its tables, names the wrong one, or carries
// `tables` where nothing reads it.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { catalogueSlugs } from '../src/data/topics.mjs';
import { catalogues } from '../src/generated/catalogues.mjs';
import { catalogueSections } from '../src/lib/catalogue-datasets.mjs';
import { withLineFeeds } from '../src/lib/line-ends.mjs';
import {
  catalogueSourceProblems,
  isCataloguePage,
  isLibraryTable,
  printedTables,
  strayTableClaims,
} from '../src/lib/catalogue-sources.mjs';

const book = (author, year, tables) => ({
  type: 'book',
  authors: [`${author}, A.`],
  year,
  title: `A book by ${author}`,
  publisher: 'A Press',
  ...(tables ? { tables } : {}),
});

const rows = (...tables) => ({ rows: tables.map((table) => ({ table })) });

test('the tables a page prints come once each, in the order of their rows', () => {
  const printed = printedTables([rows('a-2000-table-1', 'a-2000-table-1', 'b-2001-table-2'), rows('a-2000-table-1')]);
  assert.deepEqual(printed, ['a-2000-table-1', 'b-2001-table-2']);
});

test('a page whose every printed table is claimed once passes', () => {
  const problems = catalogueSourceProblems({
    page: 'reference/catalogues/solids',
    references: [book('Roe', 2000, ['roe-2000-table-1']), book('Doe', 2001, ['doe-2001-table-3', 'doe-2001-table-4'])],
    tables: ['roe-2000-table-1', 'doe-2001-table-3', 'doe-2001-table-4'],
  });
  assert.deepEqual(problems, []);
});

test('a table no entry claims is named with its page', () => {
  const problems = catalogueSourceProblems({
    page: 'reference/catalogues/carpets',
    references: [book('Roe', 2000, ['roe-2000-table-1'])],
    tables: ['roe-2000-table-1', 'harris-1995-table-30-2'],
  });
  assert.equal(problems.length, 1);
  assert.match(problems[0], /reference\/catalogues\/carpets prints rows of harris-1995-table-30-2/);
});

test('a page with no references fails once for each table it prints', () => {
  const problems = catalogueSourceProblems({
    page: 'reference/catalogues/carpets',
    references: [],
    tables: ['harris-1995-table-30-2', 'harris-1995-table-30-3'],
  });
  assert.equal(problems.length, 2);
});

test('a table two entries claim is refused, naming both', () => {
  const problems = catalogueSourceProblems({
    page: 'reference/catalogues/solids',
    references: [
      book('Roe', 2000, ['roe-2000-table-1']),
      { ...book('Roe', 2000, ['roe-2000-table-1']), title: 'Another book by Roe' },
    ],
    tables: ['roe-2000-table-1'],
  });
  assert.equal(problems.length, 1);
  assert.match(problems[0], /claimed by 2 entries.*Roe \(2000\); Roe \(2000\)/);
});

test('a table claimed by another work than the one its key names is refused', () => {
  const carpets = { page: 'reference/catalogues/carpets', tables: ['harris-1995-table-30-2'] };
  const harris = (year, tables) => ({ ...book('Harris', year, tables), authors: ['Harris, C. M. (Ed.)'] });
  // Under the other Harris handbook: the author is right and the year is not.
  const otherYear = catalogueSourceProblems({ ...carpets, references: [harris(1977, ['harris-1995-table-30-2'])] });
  assert.equal(otherYear.length, 1);
  assert.match(otherYear[0], /Harris \(1977\) claims harris-1995-table-30-2, a table of another work \(a key of this work carries its year, 1977\)/);
  // Under Bies: neither is.
  const otherBook = catalogueSourceProblems({ ...carpets, references: [book('Bies', 2017, ['harris-1995-table-30-2'])] });
  assert.equal(otherBook.length, 1);
  assert.match(otherBook[0], /Bies \(2017\) claims harris-1995-table-30-2, a table of another work \(a key of this work starts with bies-, and a key of this work carries its year, 2017\)/);
  // Under its own book, it is the one claim the page needs.
  assert.deepEqual(catalogueSourceProblems({ ...carpets, references: [harris(1995, ['harris-1995-table-30-2'])] }), []);
});

test("a key names its work by the first word of the first surname, an organization's short name or a standard's number", () => {
  const passes = (references, tables) =>
    assert.deepEqual(catalogueSourceProblems({ page: 'reference/catalogues/solids', references, tables }), []);
  passes([{ ...book('Norton', 2003, ['norton-karczub-2003-table-3-1']), authors: ['Norton, M. P.', 'Karczub, D. G.'] }], [
    'norton-karczub-2003-table-3-1',
  ]);
  passes([{ ...book('Arau-Puchades', 1999, ['arau-1999-table-4-1']) }], ['arau-1999-table-4-1']);
  passes([{ ...book('Vér', 2006, ['ver-beranek-2006-table-14-1']) }], ['ver-beranek-2006-table-14-1']);
  const ashrae = {
    type: 'report',
    organization: 'American Society of Heating, Refrigerating and Air-Conditioning Engineers',
    year: 2019,
    title: 'Handbook',
  };
  passes([{ ...ashrae, tables: ['ashrae-2019-table-40'] }], ['ashrae-2019-table-40']);
  const standard = (designation, tables) => ({ type: 'standard', organization: 'IEC', designation, title: 't', tables });
  passes([standard('IEC 61094-2:2009', ['iec-61094-2-annex-f'])], ['iec-61094-2-annex-f']);
  // The issuer is not held: one text carries the designations of several bodies.
  passes([standard('ISO 12354-1:2017', ['en-12354-annex-a'])], ['en-12354-annex-a']);

  // A standard's table under another standard, and an organization's under another.
  const wrong = catalogueSourceProblems({
    page: 'reference/catalogues/fluids',
    references: [standard('IEC 61094-2:2009', ['en-12354-6-table-1']), { ...ashrae, organization: 'Nordtest', tables: ['ashrae-2019-table-40'] }],
    tables: ['en-12354-6-table-1', 'ashrae-2019-table-40'],
  });
  assert.equal(wrong.length, 2);
  assert.match(wrong[0], /IEC 61094-2:2009 claims en-12354-6-table-1, a table of another work \(the key's number, 12354-6, is not in the designation\)/);
  assert.match(wrong[1], /Nordtest \(2019\) claims ashrae-2019-table-40, a table of another work \(a key of this work starts with nordtest-\)/);
});

test('a claim on a table the page does not print is refused', () => {
  const problems = catalogueSourceProblems({
    page: 'reference/catalogues/solids',
    references: [book('Roe', 2000, ['roe-2000-table-1', 'roe-2000-table-9'])],
    tables: ['roe-2000-table-1'],
  });
  assert.equal(problems.length, 1);
  assert.match(problems[0], /Roe \(2000\) claims roe-2000-table-9, which no catalogue on the page prints/);
});

test("the library's own tables claim no source, and none may be claimed", () => {
  assert.ok(isLibraryTable('phonometry-solver'));
  assert.ok(!isLibraryTable('iec-61094-2-annex-f'));
  assert.deepEqual(
    catalogueSourceProblems({ page: 'reference/catalogues/fluids', references: [], tables: ['phonometry-solver'] }),
    [],
  );
  const claimed = catalogueSourceProblems({
    page: 'reference/catalogues/fluids',
    references: [book('Roe', 2000, ['phonometry-solver'])],
    tables: ['phonometry-solver'],
  });
  assert.equal(claimed.length, 1);
  assert.match(claimed[0], /a table the library fixes itself/);
});

test('a page that is not a catalogue page and carries tables is named, in either language', () => {
  assert.ok(isCataloguePage('reference/catalogues/solids'));
  assert.ok(isCataloguePage('es/reference/catalogues/solids'));
  assert.ok(!isCataloguePage('reference/catalogues'));
  assert.ok(!isCataloguePage('room/absorbers/porous'));
  const problems = strayTableClaims([
    { id: 'reference/catalogues/solids', references: [book('Roe', 2000, ['roe-2000-table-1'])] },
    { id: 'reference/catalogues', references: [book('Roe', 2000, ['roe-2000-table-1'])] },
    { id: 'es/materials/absorbers/porous', references: [book('Doe', 2001), book('Roe', 2000, [])] },
    { id: 'materials/absorbers/porous', references: [book('Doe', 2001)] },
    { id: 'start/guides' },
  ]);
  assert.deepEqual(problems, [
    'reference/catalogues is not a catalogue page, and an entry of its references names `tables`',
    'es/materials/absorbers/porous is not a catalogue page, and an entry of its references names `tables`',
  ]);
});

test('an entry without tables, a work the page cites for something else, is no problem', () => {
  const problems = catalogueSourceProblems({
    page: 'reference/catalogues/solids',
    references: [book('Roe', 2000, ['roe-2000-table-1']), book('Doe', 2001)],
    tables: ['roe-2000-table-1'],
  });
  assert.deepEqual(problems, []);
});

// ---------------------------------------------------------------------------
// The pages as they are.
// ---------------------------------------------------------------------------

const contentDir = fileURLToPath(new URL('../src/content/docs', import.meta.url));

/** The keys of an entry this test reads; any other key is followed and skipped. */
const READ_KEYS = new Set(['type', 'authors', 'organization', 'designation', 'title', 'year', 'tables']);

/**
 * The entries of a page's `references`, each with the keys this test reads.
 *
 * A narrow reader, like the one in scripts/generate_site_reports.py: the site
 * has no YAML parser installed and the frontmatter is written one key per
 * line. An entry opens at a list item under `references:`, every other line of
 * it is one key with its value on that line, and `tables` and `authors` are
 * flow lists of quoted strings, read as JSON. Any other line under
 * `references:` fails the test rather than reading as no claim: a key whose
 * value is on the lines below it (`tables` written as a block list), a key
 * before the first item, an item or a comment at the margin, and a list
 * written on the line of its key. A blank line ends nothing.
 */
function readReferences(text, file) {
  const end = text.indexOf('\n---', 3);
  assert.ok(text.startsWith('---') && end > 0, `${file} has no frontmatter`);
  const entries = [];
  let inReferences = false;
  // The first line split off is the rest of the opening fence, so each line's
  // index is its line number less one.
  for (const [index, line] of text.slice(3, end).split('\n').entries()) {
    if (!line.trim()) continue;
    const where = `${file}:${index + 1}`;
    if (/^\S/.test(line)) {
      // Under `references:` the only line at the margin is the next key: an
      // item or a comment there is YAML that would otherwise end the list.
      assert.ok(
        !inReferences || /^[A-Za-z_][A-Za-z0-9_]*:/.test(line),
        `${where}: a references line this reader cannot follow: ${JSON.stringify(line)}`,
      );
      const [name, ...rest] = line.split(':');
      const value = rest.join(':').trim();
      assert.ok(
        name !== 'references' || value === '' || value === '[]',
        `${where}: references written on the line of its key, which this reader cannot follow: ${JSON.stringify(line)}`,
      );
      inReferences = name === 'references' && value === '';
      continue;
    }
    if (!inReferences) continue;
    const key = /^ {2}(- | {2})([A-Za-z]+): (.+)$/.exec(line);
    assert.ok(
      key && (key[1] === '- ' || entries.length > 0),
      `${where}: a references line this reader cannot follow: ${JSON.stringify(line)}`,
    );
    if (key[1] === '- ') entries.push({});
    if (!READ_KEYS.has(key[2])) continue;
    const entry = entries.at(-1);
    if (key[2] === 'tables' || key[2] === 'authors') {
      assert.match(key[3], /^\[.*\]$/, `${where}: ${key[2]} is not written as a flow list on one line`);
      entry[key[2]] = JSON.parse(key[3]);
    } else {
      entry[key[2]] = key[3].replace(/^"(.*)"$/, '$1');
    }
  }
  return entries;
}

test('the reader of the pages follows the one way they write references, and stops on any other', () => {
  const page = (...lines) => ['---', 'title: "A page"', ...lines, '---', '', 'Text.', ''].join('\n');
  const entry = ['  - type: book', '    authors: ["Mechel, F. P. (Ed.)"]', '    year: 2008', '    title: "Formulas of acoustics"'];
  const read = readReferences(
    page('references:', ...entry, '    tables: ["mechel-2008-table-d-3"]', '', ...entry, 'sidebar:', '  order: 1'),
    'two.mdx',
  );
  assert.deepEqual(
    read.map((ref) => ref.tables),
    [['mechel-2008-table-d-3'], undefined],
    'an entry after a blank line, and the claim of the one before it, are read',
  );
  assert.equal(read[0].title, 'Formulas of acoustics');
  assert.deepEqual(readReferences(page('references: []'), 'none.mdx'), []);
  const refused = {
    'a block list of tables': page('references:', ...entry, '    tables:', '      - "mechel-2008-table-d-3"'),
    'a block list of authors': page('references:', '  - type: book', '    authors:', '      - "Mechel, F. P. (Ed.)"'),
    'a key before the first item': page('references:', '    tables: ["mechel-2008-table-d-3"]', ...entry),
    'an item at the margin': page('references:', ...entry, '- type: book', '  tables: ["mechel-2008-table-d-3"]'),
    'a comment at the margin': page('references:', ...entry, '# the catalogue source', ...entry),
    'a list on the line of its key': page('references: [{type: book, tables: ["mechel-2008-table-d-3"]}]'),
  };
  for (const [what, text] of Object.entries(refused)) {
    assert.throws(() => readReferences(text, 'page.mdx'), /page\.mdx:\d+: .*this reader cannot follow/, what);
  }
});

test('every catalogue page of both languages names the work behind every table it prints', async () => {
  const problems = [];
  let claimed = 0;
  for (const prefix of ['', 'es/']) {
    for (const slug of catalogueSlugs) {
      const file = path.join(contentDir, `${prefix}${slug}.mdx`);
      const text = withLineFeeds(await readFile(file, 'utf8'));
      // The catalogues it renders, read off its source as catalogue-pages.ts does.
      const keys = catalogueSections(text).map(({ key }) => key);
      assert.ok(keys.length > 0, `${file} renders no catalogue`);
      const references = readReferences(text, file);
      const tables = printedTables(keys.map((key) => catalogues[key]));
      claimed += tables.filter((table) => !isLibraryTable(table)).length;
      problems.push(...catalogueSourceProblems({ page: `${prefix}${slug}`, references, tables }));
    }
  }
  assert.deepEqual(problems, [], `${problems.length} table(s) without their source:\n  ${problems.join('\n  ')}`);
  assert.ok(claimed > 0, 'no catalogue page prints a table read from a work');
});

/** Every page under the content directory, as an entry id and its file. */
async function contentPages(dir = contentDir, prefix = '') {
  const pages = [];
  for (const item of await readdir(dir, { withFileTypes: true })) {
    const file = path.join(dir, item.name);
    if (item.isDirectory()) pages.push(...(await contentPages(file, `${prefix}${item.name}/`)));
    else if (/\.mdx?$/.test(item.name)) {
      const stem = item.name.replace(/\.mdx?$/, '');
      const id = stem === 'index' ? prefix.replace(/\/$/, '') : `${prefix}${stem}`;
      pages.push({ id, file });
    }
  }
  return pages;
}

test('no page of either language but a catalogue page carries tables', async () => {
  const pages = await contentPages();
  const read = await Promise.all(
    pages.map(async ({ id, file }) => ({ id, references: readReferences(withLineFeeds(await readFile(file, 'utf8')), file) })),
  );
  assert.deepEqual(strayTableClaims(read), []);
  const cited = read.filter((page) => !isCataloguePage(page.id) && page.references.length > 0);
  assert.ok(cited.length > 200, `only ${cited.length} pages that are not catalogue pages cite a work: the reader lost them`);
  assert.ok(read.some((page) => page.id.startsWith('es/')), 'no Spanish page was read');
});
