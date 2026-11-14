// Every published catalogue is a dataset with a name, a description, its
// variables and the works it was read from.
//
// src/lib/catalogue-datasets.mjs builds the Dataset node each catalogue page
// publishes, and src/lib/catalogue-pages.ts stops the build when a catalogue
// has no name or description to give it. The first tests hand the functions
// small pages and columns with each case they exist for; the last one reads
// the real pages of both languages, so a catalogue that would publish a
// dataset with no name, no description, no variables or no source fails here,
// before a twenty-minute build.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { catalogueSlugs } from '../src/data/topics.mjs';
import { catalogues } from '../src/generated/catalogues.mjs';
import {
  catalogueDatasets,
  catalogueSections,
  catalogueSources,
  datasetNode,
  datasetStub,
  plainText,
  readInline,
  variablesMeasured,
} from '../src/lib/catalogue-datasets.mjs';
import { isLibraryTable, printedTables } from '../src/lib/catalogue-sources.mjs';

const BIBLIOGRAPHY = 'https://docs.example/phonometry/reference/bibliography/';
const PAGE = 'https://docs.example/phonometry/reference/catalogues/absorption-coefficients/';
const TWIN = 'https://docs.example/phonometry/es/reference/catalogues/absorption-coefficients/';
const CATALOG = {
  '@id': 'https://docs.example/phonometry/reference/catalogues/#article',
  name: 'Published catalogues',
  url: 'https://docs.example/phonometry/reference/catalogues/',
};

const book = (author, year, tables) => ({
  type: 'book',
  authors: [`${author}, A.`],
  year,
  title: `A book by ${author}`,
  publisher: 'A Press',
  ...(tables ? { tables } : {}),
  note: 'Table 1: the source of the rows of the catalogue of things that cite it.',
});

const rows = (...tables) => tables.map((table) => ({ table }));

const band = (field, hertz, quantity, quantityEs, unit = '') => ({
  field: `${field}_${hertz}`,
  heading: hertz < 1000 ? `${hertz} Hz` : `${hertz / 1000} kHz`,
  headingEs: hertz < 1000 ? `${hertz} Hz` : `${String(hertz / 1000).replace('.', ',')} kHz`,
  unit,
  quantity,
  quantityEs,
});

// ---------------------------------------------------------------------------
// Reading a page
// ---------------------------------------------------------------------------

test('a page with one catalogue reads one section, with no heading of its own and the paragraph that opens the page', () => {
  const sections = catalogueSections(
    ['import Catalogues from "x";', '', '<CatalogueFinder lang="en" />', '', 'Prose.', '', '<Catalogues catalogue="solids" lang="en" />'].join('\n'),
  );
  assert.deepEqual(sections, [{ key: 'solids', lead: 'Prose.' }]);
});

test("the first catalogue's lead is the paragraph that opens the page, whatever heading comes before the catalogue", () => {
  const sections = catalogueSections(
    [
      '<CatalogueFinder lang="en" />',
      '',
      'What a finish did in a room,',
      'band by band.',
      '',
      'A second paragraph.',
      '',
      '## The coefficients',
      '',
      'The paragraph under the heading.',
      '',
      '<Catalogues catalogue="absorption" lang="en" />',
    ].join('\n'),
  );
  assert.deepEqual(sections, [{ key: 'absorption', heading: 'The coefficients', lead: 'What a finish did in a room, band by band.' }]);
});

test('a later catalogue takes the heading after the one before it and the paragraph that opens its section', () => {
  const sections = catalogueSections(
    [
      '## Before the first',
      '',
      'What the first catalogue holds.',
      '',
      '<Catalogues catalogue="absorption" lang="en" />',
      '',
      '## Absorption areas of people and air',
      '',
      'Bies and Long also print rows that are not',
      'coefficients, held in `PUBLISHED_ABSORPTION_AREAS` and [here](/x/).',
      '',
      'A second paragraph, which is not the description.',
      '',
      '<Catalogues catalogue="absorptionAreas" lang="en" />',
    ].join('\n'),
  );
  assert.deepEqual(sections[1], {
    key: 'absorptionAreas',
    heading: 'Absorption areas of people and air',
    lead: 'Bies and Long also print rows that are not coefficients, held in PUBLISHED_ABSORPTION_AREAS and here.',
  });
  // The first catalogue keeps the heading it sits under, which names nothing,
  // and the paragraph that opens the page.
  assert.deepEqual(sections[0], { key: 'absorption', heading: 'Before the first', lead: 'What the first catalogue holds.' });
});

test('a catalogue tag the page quotes rather than renders is no section', () => {
  // A tag in a code span, a comment or an expression, or behind a backslash,
  // is text the page shows or hides, and renders no table.
  const sections = catalogueSections(
    [
      'The page renders `<Catalogues catalogue="gases" />` for the gases.',
      '',
      '{/* <Catalogues catalogue="fluids" /> */}',
      '',
      '\\<Catalogues catalogue="carpets" />',
      '',
      'Prose.',
      '',
      '<Catalogues catalogue="solids" lang="en" />',
    ].join('\n'),
  );
  assert.deepEqual(
    sections.map(({ key }) => key),
    ['solids'],
  );
});

test('a catalogue tag is read whole, across its lines, beside another on its line and with its attributes in any order', () => {
  // MDX renders each of these tags, so each is a section where it opens: one
  // written over several lines, a second on the line of the first, one with
  // its catalogue after another attribute or in single quotes.
  const sections = catalogueSections(
    [
      'What the first catalogue holds.',
      '',
      '<Catalogues',
      '  catalogue="absorption"',
      '  lang="en"',
      '/>',
      '',
      '## Absorption areas of people and air',
      '',
      'The rows that are not coefficients.',
      '',
      '<Catalogues catalogue="absorptionAreas"',
      '  lang="en" /><Catalogues lang="en" catalogue="gases" />',
      '',
      '## Fluids',
      '',
      'The fluids.',
      '',
      "<Catalogues lang='en' catalogue='fluids' />",
    ].join('\n'),
  );
  assert.deepEqual(sections, [
    { key: 'absorption', lead: 'What the first catalogue holds.' },
    { key: 'absorptionAreas', heading: 'Absorption areas of people and air', lead: 'The rows that are not coefficients.' },
    { key: 'gases' },
    { key: 'fluids', heading: 'Fluids', lead: 'The fluids.' },
  ]);
});

test('a catalogue tag whose catalogue is no word in quotes is a section named by what it writes, which no catalogue is', () => {
  // The build then stops on a catalogue it does not know, naming the tag,
  // where a tag it did not see would leave the page one catalogue short.
  const sections = catalogueSections(
    ['Prose.', '', '<Catalogues catalogue={key} lang="en" />', '', '## Other', '', 'Other prose.', '', '<Catalogues lang="en" />'].join(
      '\n',
    ),
  );
  assert.deepEqual(
    sections.map(({ key }) => key),
    ['{key}', '<Catalogues lang="en" />'],
  );
});

test('a later catalogue under no heading of its own has none, and a subheading is not a section', () => {
  const sections = catalogueSections(
    [
      '## The rows',
      '',
      'A paragraph.',
      '',
      '<Catalogues catalogue="absorption" lang="en" />',
      '',
      '### Not a section of the page',
      '',
      'Prose between the two.',
      '',
      '<Catalogues catalogue="absorptionAreas" lang="en" />',
    ].join('\n'),
  );
  assert.deepEqual(sections[1], { key: 'absorptionAreas' });
});

test('a section that opens with a component and no paragraph has no lead', () => {
  const sections = catalogueSections(
    ['<Catalogues catalogue="a" />', '', '## Second', '', '<Catalogues catalogue="b" />'].join('\n'),
  );
  assert.deepEqual(sections[1], { key: 'b', heading: 'Second' });
});

/**
 * The second section of a page of two catalogues, its heading followed by the
 * lines of `opening` and then by a paragraph of its own.
 */
const secondSection = (opening) =>
  catalogueSections(
    [
      'Opening paragraph.',
      '',
      '<Catalogues catalogue="absorption" lang="en" />',
      '',
      '## Areas',
      '',
      ...opening,
      '',
      'The paragraph that describes it.',
      '',
      '<Catalogues catalogue="absorptionAreas" lang="en" />',
    ].join('\n'),
  )[1];

test('a section that opens with an aside, a list, a quotation, a table or a figure takes its own first paragraph, not what they hold', () => {
  for (const opening of [
    ['<Aside type="note">', 'A note that is not the description.', '</Aside>'],
    ['<Aside>', '', 'A paragraph inside an aside.', '', '<Aside>', 'One inside that.', '</Aside>', '', 'Still inside.', '', '</Aside>'],
    [':::note', 'A note.', ':::'],
    ['- one item', '- two item', '', '  A second paragraph of the item.'],
    ['1. A numbered item.'],
    ['> A quotation', 'that runs on.'],
    ['| Band | Area |', '| --- | --- |', '| 125 Hz | 0,1 |'],
    ['<ThemeImage', '  src="room.svg"', '  alt="A room"', '/>'],
  ]) {
    assert.deepEqual(
      secondSection(opening),
      { key: 'absorptionAreas', heading: 'Areas', lead: 'The paragraph that describes it.' },
      opening.join(' / '),
    );
  }
});

test('an aside ends with the quotation or the list item it opened in, so the paragraph after them describes the section', () => {
  // remark-directive closes the aside where its container ends, with no
  // closing fence: the paragraph after the blank line stands on the page.
  for (const opening of [
    ['> :::note', '> A note.'],
    ['- :::note', '  A note.'],
    ['> - :::note', '>   A note.'],
    ['> :::note', '> A note.', 'A paragraph of its own, which ends the quotation.'],
  ]) {
    assert.deepEqual(
      secondSection(opening),
      {
        key: 'absorptionAreas',
        heading: 'Areas',
        lead: opening.length === 3 ? opening[2] : 'The paragraph that describes it.',
      },
      opening.join(' / '),
    );
  }
  // An aside on the page itself still holds what follows it up to its fence.
  assert.deepEqual(secondSection([':::note', '> A quotation in the aside.', '', 'Still in the aside.', ':::']), {
    key: 'absorptionAreas',
    heading: 'Areas',
    lead: 'The paragraph that describes it.',
  });
});

test('a paragraph that opens with an inline tag keeps its first line, and shows what the tag holds', () => {
  const sections = catalogueSections(
    [
      '## Areas',
      '',
      '<abbr title="International Organization for Standardization">ISO</abbr> 354 rooms',
      'measured these areas per person.',
      '',
      '<Catalogues catalogue="absorptionAreas" lang="en" />',
    ].join('\n'),
  );
  assert.equal(sections[0].lead, 'ISO 354 rooms measured these areas per person.');
});

test('a heading right under a paragraph ends it: the opening one stays the first catalogue\'s, and no heading joins a lead', () => {
  const sections = catalogueSections(
    [
      'What the first holds,',
      'read band by band.',
      '## Coefficients',
      '',
      'Under the heading.',
      '',
      '<Catalogues catalogue="absorption" lang="en" />',
      '',
      '## Areas',
      'The paragraph that describes it.',
      '### A subheading',
      'Prose under the subheading.',
      '<Catalogues catalogue="absorptionAreas" lang="en" />',
    ].join('\n'),
  );
  assert.deepEqual(sections, [
    { key: 'absorption', heading: 'Coefficients', lead: 'What the first holds, read band by band.' },
    { key: 'absorptionAreas', heading: 'Areas', lead: 'The paragraph that describes it.' },
  ]);
});

test('a line underlined with hyphens is a section heading, and one underlined with equals signs is not', () => {
  const sections = catalogueSections(
    [
      'Opening paragraph.',
      '',
      '<Catalogues catalogue="absorption" lang="en" />',
      '',
      'Absorption areas',
      'of people and air',
      '----------------',
      '',
      'The paragraph that describes it.',
      '',
      '<Catalogues catalogue="absorptionAreas" lang="en" />',
      '',
      'Not a section',
      '=============',
      '',
      'A paragraph under no section heading.',
      '',
      '<Catalogues catalogue="solids" lang="en" />',
    ].join('\n'),
  );
  assert.deepEqual(sections.slice(1), [
    { key: 'absorptionAreas', heading: 'Absorption areas of people and air', lead: 'The paragraph that describes it.' },
    { key: 'solids' },
  ]);
});

test('markup a name or a description holds that the page shows otherwise is named as a problem, and the build stops', () => {
  const sections = catalogueSections(
    [
      'What the first holds, with a <Badge text="new" /> on it.',
      '',
      '<Catalogues catalogue="absorption" lang="en" />',
      '',
      '## Areas of {props.kind}',
      '',
      'Rows in $\\mathrm{m}^2$ per &shy;person.',
      '',
      '<Catalogues catalogue="absorptionAreas" lang="en" />',
    ].join('\n'),
  );
  const { datasets, problems } = catalogueDatasets({ id: 'reference/catalogues/x', title: 'T', description: 'D', sections });
  assert.deepEqual(datasets, []);
  assert.equal(problems.length, 2, problems.join('\n'));
  assert.match(problems[0], /reference\/catalogues\/x: the paragraph that opens the page, which describes absorption, holds "<Badge text=\\"new\\" \/>"/);
  assert.match(problems[1], /`## Areas of \{props\.kind\}` heading, which names absorptionAreas, holds "\{props\.kind\}"/);
  assert.match(problems[1], /the paragraph that opens it, which describes absorptionAreas, holds "\$\\\\mathrm\{m\}\^2\$", "&shy;"/);
  // Escaped, the same characters are text the page shows as written.
  const escaped = catalogueSections(
    ['A \\<Badge\\> and \\{braces\\}, \\$5 and &amp;shy; as text.', '', '<Catalogues catalogue="a" />', '', '## B', '', 'B.', '', '<Catalogues catalogue="b" />'].join('\n'),
  );
  assert.deepEqual(catalogueDatasets({ id: 'x', title: 'T', description: 'D', sections: escaped }).problems, []);
  assert.equal(escaped[0].lead, 'A <Badge> and {braces}, $5 and &shy; as text.');
});

test('plain text drops the marks a reader does not see and keeps the underscores of a name', () => {
  assert.equal(
    plainText(['A *word*, a **strong** one, an _emphasis_,', 'PUBLISHED_ABSORPTION_AREAS and `code`.']),
    'A word, a strong one, an emphasis, PUBLISHED_ABSORPTION_AREAS and code.',
  );
});

test('plain text reads a code span as the page does, whatever its run of backticks holds', () => {
  // A span of two backticks holds a backtick of its own, and the space that
  // pads it on both sides is not the code's (CommonMark 0.31.2, 6.1).
  assert.equal(plainText(['The ``a`b`` key.']), 'The a`b key.');
  assert.equal(plainText(['The `` `rows` `` key.']), 'The `rows` key.');
  // What a span holds is code, not emphasis or a link.
  assert.equal(plainText(['The `*_rows_*` and `[a](b)` keys.']), 'The *_rows_* and [a](b) keys.');
  // A span runs over the lines of its paragraph.
  assert.equal(plainText(['The `two', 'lines` key.']), 'The two lines key.');
  // An escaped backtick opens nothing and is shown without its backslash, and
  // a run no later run closes stays text.
  assert.equal(plainText(['A \\`tick and ``one`.']), 'A `tick and ``one`.');
});

test('plain text shows an escaped character as written, without its backslash, and opens nothing on it', () => {
  assert.equal(plainText(['Rows priced in \\*sabins\\* and \\_feet\\_.']), 'Rows priced in *sabins* and _feet_.');
  assert.equal(plainText(['A \\[bracket\\](not a link), a \\\\ backslash and a \\a.']), 'A [bracket](not a link), a \\ backslash and a \\a.');
  // Inside a code span a backslash escapes nothing.
  assert.equal(plainText(['The `C:\\rows\\*` path.']), 'The C:\\rows\\* path.');
});

test('plain text reads a link whose address holds parentheses, whose text holds brackets or that carries a title', () => {
  assert.equal(plainText(['See [the table](https://en.wikipedia.org/wiki/Sabin_(unit)) here.']), 'See the table here.');
  assert.equal(plainText(['See [the [first] table](/x/ "A title") and [this](</a b/>).']), 'See the [first] table and this.');
  assert.equal(plainText(['A figure, ![a room seen from above](room.svg), stands for its text.']), 'A figure, a room seen from above, stands for its text.');
});

test('plain text reads character references, line breaks, struck and nested marks, comments and inline tags as the page shows them', () => {
  assert.equal(plainText(['Bies &amp; Long, 1&#8201;250 Hz &#x2013; on &lt;dB&gt;.']), 'Bies & Long, 1\u2009250 Hz \u2013 on <dB>.');
  assert.equal(plainText(['A line that breaks\\', 'here, and one that ends in \\\\', 'a backslash.']), 'A line that breaks here, and one that ends in \\ a backslash.');
  assert.equal(plainText(['A ~~struck~~ word, ***both*** marks and __strong__ ones.']), 'A struck word, both marks and strong ones.');
  assert.equal(plainText(['An inline {/* note to self */} comment.']), 'An inline comment.');
  assert.equal(plainText(['<abbr title="x">ISO</abbr> 354 and <span class="a">b</span>.']), 'ISO 354 and b.');
  // A space the page shows as it is written stays that space.
  assert.equal(plainText(['1\u202f250 Hz,', 'at\u00a0once.']), '1\u202f250 Hz, at\u00a0once.');
});

// A paragraph is read once, left to right, as the page reads it: whichever of
// a code or maths span, an escape, a comment, a tag and an expression opens
// first takes what follows, so what a comment or a tag's attributes hold is
// neither text nor markup.

test('a comment owns what it holds: a formula, a lone backtick or a code span inside one is neither markup nor text', () => {
  assert.deepEqual(readInline(['Rows {/* $x$ */} in bands.']), { text: 'Rows in bands.', markup: [] });
  assert.deepEqual(readInline(['Rows {/* `x */} in `bands`.']), { text: 'Rows in bands.', markup: [] });
  // The backtick inside the comment opens nothing, so the code span after it is the page's.
  assert.deepEqual(readInline(['A {/* ` */} b `*/}` c.']), { text: 'A b */} c.', markup: [] });
  // What opens before a comment owns the comment's marks: a code span holds them as code, and a formula stays markup.
  assert.deepEqual(readInline(['Rows `{/* x */}` in bands.']), { text: 'Rows {/* x */} in bands.', markup: [] });
  assert.deepEqual(readInline(['Rows $x$ {/* note */} in bands.']), { text: 'Rows $x$ in bands.', markup: ['$x$'] });
});

test('an expression that holds nothing but blanks and comments shows nothing, a line comment that ends its line among them', () => {
  assert.deepEqual(readInline(['Rows {// $x$', '} in bands.']), { text: 'Rows in bands.', markup: [] });
  assert.deepEqual(readInline(['Rows {/* a */', '// `b', '} in bands.']), { text: 'Rows in bands.', markup: [] });
  assert.deepEqual(readInline(['Rows {} in { } bands.']), { text: 'Rows in bands.', markup: [] });
});

test('a tag owns what its attributes write: a formula or a backtick there is neither markup nor a span', () => {
  assert.deepEqual(readInline(['Rows of <abbr title="$x$">dB</abbr> in bands.']), { text: 'Rows of dB in bands.', markup: [] });
  assert.deepEqual(readInline(['Rows of <abbr title="a`b">dB</abbr> in `bands`.']), { text: 'Rows of dB in bands.', markup: [] });
});

test('an expression that prints a value between two comments is markup, not a comment', () => {
  assert.deepEqual(readInline(['Rows {/* a */ n /* b */} in bands.']).markup, ['{/* a */ n /* b */}']);
  assert.deepEqual(readInline(['Rows {// a', 'n} in bands.']).markup, ['{// a n}']);
});

test('a hidden comment in the paragraphs and the heading that name and describe two datasets stops nothing', () => {
  const body = [
    'Rows {/* $\\alpha$ */} of absorption coefficients.',
    '',
    '<Catalogues catalogue="absorption" />',
    '',
    '## Absorption areas {/* $A$ */}',
    '',
    'Areas of objects {/* `T */}, per object.',
    '',
    '<Catalogues catalogue="absorptionAreas" />',
    '',
  ].join('\n');
  const { datasets, problems } = catalogueDatasets({ id: 'x', title: 'T', description: 'D', sections: catalogueSections(body) });
  assert.deepEqual(problems, []);
  // As the page shows them: the blank written before a comment stays.
  assert.deepEqual(
    datasets.map(({ name, description }) => [name, description]),
    [
      ['T', 'Rows of absorption coefficients.'],
      ['Absorption areas', 'Areas of objects , per object.'],
    ],
  );
});

// ---------------------------------------------------------------------------
// Naming the datasets
// ---------------------------------------------------------------------------

test("a page's only catalogue takes the page's title and description", () => {
  const { datasets, problems } = catalogueDatasets({
    id: 'reference/catalogues/solids',
    title: 'Catalogue of solids',
    description: 'Elastic constants of solids.',
    sections: [{ key: 'solids', heading: 'Ignored', lead: 'The paragraph that opens the page.' }],
  });
  assert.deepEqual(problems, []);
  assert.deepEqual(datasets, [{ key: 'solids', name: 'Catalogue of solids', description: 'Elastic constants of solids.' }]);
});

test("on a page of several catalogues the first takes the page's title and its opening paragraph, not the page's description", () => {
  // The page's description speaks of everything the page holds, the audiences
  // and the air as well, which are rows of the second dataset.
  const description = 'What finishes absorbed, and the absorption area of audiences and air.';
  const { datasets, problems } = catalogueDatasets({
    id: 'reference/catalogues/absorption-coefficients',
    title: 'Catalogue of absorption coefficients',
    description,
    sections: [
      { key: 'absorption', lead: 'What a finish did in a reverberation room, band by band.' },
      { key: 'absorptionAreas', heading: 'Absorption areas of people and air', lead: 'Rows that are not coefficients.' },
    ],
  });
  assert.deepEqual(problems, []);
  assert.deepEqual(datasets, [
    {
      key: 'absorption',
      name: 'Catalogue of absorption coefficients',
      description: 'What a finish did in a reverberation room, band by band.',
    },
    { key: 'absorptionAreas', name: 'Absorption areas of people and air', description: 'Rows that are not coefficients.' },
  ]);
  assert.ok(datasets.every((dataset) => dataset.description !== description));
});

test('a later catalogue with no heading of its own, or a heading with no paragraph, is named as a problem', () => {
  const { datasets, problems } = catalogueDatasets({
    id: 'es/reference/catalogues/x',
    title: 'T',
    description: 'D',
    sections: [{ key: 'a', lead: 'L' }, { key: 'b' }, { key: 'c', heading: 'C' }],
  });
  assert.equal(datasets.length, 1);
  assert.equal(problems.length, 2);
  assert.match(problems[0], /es\/reference\/catalogues\/x renders b after another catalogue with no `##` heading/);
  assert.match(problems[1], /`## C` section that holds c opens with no paragraph/);
});

test('the first of several catalogues with no paragraph before it is named as a problem', () => {
  const { datasets, problems } = catalogueDatasets({
    id: 'reference/catalogues/x',
    title: 'T',
    description: 'D',
    sections: [{ key: 'a' }, { key: 'b', heading: 'B', lead: 'L' }],
  });
  assert.deepEqual(datasets, [{ key: 'b', name: 'B', description: 'L' }]);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /reference\/catalogues\/x renders 2 catalogues and opens with no paragraph before the first, a/);
});

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------

test('each column is a variable, named by its heading in the page language, with its unit when it has one', () => {
  const columns = [
    { field: 'density_kg_m3', heading: 'Density', headingEs: 'Densidad', unit: 'kg/m³' },
    { field: 'poisson_ratio', heading: 'Poisson ratio', headingEs: 'Coeficiente de Poisson', unit: '' },
  ];
  assert.deepEqual(variablesMeasured(columns, 'en'), [
    { '@type': 'PropertyValue', name: 'Density', unitText: 'kg/m³' },
    { '@type': 'PropertyValue', name: 'Poisson ratio' },
  ]);
  assert.deepEqual(
    variablesMeasured(columns, 'es').map((variable) => variable.name),
    ['Densidad', 'Coeficiente de Poisson'],
  );
});

test('the band columns of one quantity are one variable, named by the quantity, saying which bands', () => {
  const columns = [
    { field: 'angle_of_incidence_deg', heading: 'Angle of incidence', headingEs: 'Ángulo de incidencia', unit: '°' },
    band('scattering_coefficient', 100, 'Scattering coefficient', 'Coeficiente de dispersión'),
    band('scattering_coefficient', 1250, 'Scattering coefficient', 'Coeficiente de dispersión'),
    band('scattering_coefficient', 5000, 'Scattering coefficient', 'Coeficiente de dispersión'),
  ];
  assert.deepEqual(variablesMeasured(columns, 'en'), [
    { '@type': 'PropertyValue', name: 'Angle of incidence', unitText: '°' },
    {
      '@type': 'PropertyValue',
      name: 'Scattering coefficient',
      description: 'From the 100 Hz band to the 5 kHz band',
    },
  ]);
  assert.deepEqual(variablesMeasured(columns, 'es')[1], {
    '@type': 'PropertyValue',
    name: 'Coeficiente de dispersión',
    description: 'De la banda de 100 Hz a la de 5 kHz',
  });
});

test('a band column alone says its band, and a change of unit starts another variable', () => {
  const columns = [
    band('transmission_loss', 125, 'Transmission loss', 'Pérdida por transmisión', 'dB'),
    band('transmission_loss', 250, 'Transmission loss', 'Pérdida por transmisión', 'cB'),
  ];
  assert.deepEqual(variablesMeasured(columns, 'en'), [
    { '@type': 'PropertyValue', name: 'Transmission loss', description: 'In the 125 Hz band', unitText: 'dB' },
    { '@type': 'PropertyValue', name: 'Transmission loss', description: 'In the 250 Hz band', unitText: 'cB' },
  ]);
});

// ---------------------------------------------------------------------------
// Sources and the node
// ---------------------------------------------------------------------------

test("a catalogue's sources are the entries whose tables it prints, in the page's order", () => {
  const references = [
    book('Long', 2014, ['long-2014-table-7-1']),
    book('Cox', 2017, ['cox-2017-appendix-a']),
    book('Bies', 2017, ['bies-2017-table-6-2']),
    { type: 'standard', designation: 'ISO 354:2003', title: 'A standard the page cites for something else' },
  ];
  const areas = { rows: rows('bies-2017-table-6-2', 'long-2014-table-7-1', 'phonometry-solver') };
  assert.deepEqual(
    catalogueSources(references, areas).map((ref) => ref.authors[0]),
    ['Long, A.', 'Bies, A.'],
  );
});

test('a dataset names its sources, its catalogue and its twin, and claims no licence and no download', () => {
  const node = datasetNode({
    dataset: { key: 'absorptionAreas', name: 'Absorption areas of people and air', description: 'Rows.' },
    catalogue: {
      columns: [band('absorption_area', 125, 'Equivalent absorption area', 'Área de absorción equivalente', 'm²')],
      rows: rows('bies-2017-table-6-2'),
    },
    references: [book('Bies', 2017, ['bies-2017-table-6-2']), book('Cox', 2017, ['cox-2017-appendix-a'])],
    lang: 'en',
    pageUrl: PAGE,
    twinUrl: TWIN,
    bibliographyUrl: BIBLIOGRAPHY,
    dataCatalog: CATALOG,
  });
  assert.equal(node['@type'], 'Dataset');
  assert.equal(node['@id'], `${PAGE}#dataset-absorptionAreas`);
  assert.equal(node.url, `${PAGE}#catalogue-absorptionAreas`);
  assert.equal(node.inLanguage, 'en');
  assert.deepEqual(node.includedInDataCatalog, { '@type': 'DataCatalog', ...CATALOG });
  assert.deepEqual(node.workTranslation, { '@id': `${TWIN}#dataset-absorptionAreas` });
  assert.equal(node.translationOfWork, undefined);
  assert.equal(node.isBasedOn.length, 1);
  assert.equal(node.isBasedOn[0]['@type'], 'Book');
  assert.equal(node.isBasedOn[0].name, 'A book by Bies');
  assert.match(node.isBasedOn[0]['@id'], /^https:\/\/docs\.example\/phonometry\/reference\/bibliography\/#book-bies-2017-/);
  for (const field of ['license', 'contentUrl', 'distribution', 'encoding']) {
    assert.equal(node[field], undefined, `a dataset carries ${field}`);
  }
  const spanish = datasetNode({
    dataset: { key: 'absorptionAreas', name: 'N', description: 'D' },
    catalogue: { columns: [], rows: [] },
    references: [],
    lang: 'es',
    pageUrl: TWIN,
    twinUrl: PAGE,
    bibliographyUrl: BIBLIOGRAPHY,
    dataCatalog: CATALOG,
  });
  assert.deepEqual(spanish.translationOfWork, { '@id': `${PAGE}#dataset-absorptionAreas` });
  assert.equal(spanish.isBasedOn, undefined);
});

test("a dataset is dated as its page is, and says no date its page does not give", () => {
  const options = {
    dataset: { key: 'solids', name: 'N', description: 'D' },
    catalogue: { columns: [], rows: [] },
    references: [],
    lang: 'en',
    pageUrl: PAGE,
    twinUrl: TWIN,
    bibliographyUrl: BIBLIOGRAPHY,
    dataCatalog: CATALOG,
  };
  assert.equal(datasetNode({ ...options, dateModified: '2026-10-29' }).dateModified, '2026-10-29');
  assert.equal('dateModified' in datasetNode(options), false);
});

test('the overview lists a dataset by its type, address, name and table', () => {
  assert.deepEqual(datasetStub({ key: 'solids', name: 'Catalogue of solids' }, PAGE), {
    '@type': 'Dataset',
    '@id': `${PAGE}#dataset-solids`,
    name: 'Catalogue of solids',
    url: `${PAGE}#catalogue-solids`,
  });
});

// ---------------------------------------------------------------------------
// The real pages
// ---------------------------------------------------------------------------

const contentDir = fileURLToPath(new URL('../src/content/docs', import.meta.url));

/** A page's frontmatter scalar `key`, read off its own line, and its body. */
function readPage(text, file) {
  const end = text.indexOf('\n---', 3);
  assert.ok(text.startsWith('---') && end > 0, `${file} has no frontmatter`);
  const frontmatter = text.slice(3, end);
  const scalar = (key) => {
    const line = new RegExp(`^${key}: "(.*)"$`, 'm').exec(frontmatter);
    assert.ok(line, `${file} has no ${key} on a line of its own`);
    return line[1];
  };
  const tables = [...frontmatter.matchAll(/^ {4}tables: (\[.*\])$/gm)].map(([, list]) => JSON.parse(list));
  return {
    title: scalar('title'),
    description: scalar('description'),
    tables,
    body: text.slice(end + 4),
  };
}

test('every catalogue of both languages is a dataset with a name, a description, variables and a source', async () => {
  for (const prefix of ['', 'es/']) {
    const keys = [];
    for (const slug of catalogueSlugs) {
      const file = path.join(contentDir, `${prefix}${slug}.mdx`);
      const page = readPage(await readFile(file, 'utf8'), file);
      const sections = catalogueSections(page.body);
      const { datasets, problems: found } = catalogueDatasets({ id: `${prefix}${slug}`, ...page, sections });
      assert.deepEqual(found, [], found.join('\n'));
      assert.deepEqual(
        datasets.map(({ key }) => key),
        sections.map(({ key }) => key),
        `${file}: a catalogue it renders has no dataset`,
      );
      for (const dataset of datasets) {
        keys.push(dataset.key);
        assert.ok(dataset.key in catalogues, `${file} renders an unknown catalogue, ${dataset.key}`);
        assert.ok(dataset.name.length > 0 && dataset.description.length >= 50, `${file}: ${dataset.key} says too little`);
        // A page of several catalogues describes them all, so its description
        // is no one dataset's.
        assert.ok(
          datasets.length === 1 || dataset.description !== page.description,
          `${file}: ${dataset.key} takes the page's description, which speaks of the other catalogues too`,
        );
        const catalogue = catalogues[dataset.key];
        assert.ok(variablesMeasured(catalogue.columns, prefix ? 'es' : 'en').length > 0, `${dataset.key} has no column`);
        const read = printedTables([catalogue]).filter((table) => !isLibraryTable(table));
        const sources = catalogueSources(page.tables.map((tables) => ({ tables })), catalogue);
        assert.ok(read.length > 0 && sources.length > 0, `${file}: ${dataset.key} names no work it was read from`);
      }
    }
    assert.deepEqual([...keys].sort(), Object.keys(catalogues).sort(), `the ${prefix || 'en/'} pages do not hold every catalogue once`);
  }
});
