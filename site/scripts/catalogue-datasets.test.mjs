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

test('plain text drops the marks a reader does not see and keeps the underscores of a name', () => {
  assert.equal(
    plainText(['A *word*, a **strong** one, an _emphasis_,', 'PUBLISHED_ABSORPTION_AREAS and `code`.']),
    'A word, a strong one, an emphasis, PUBLISHED_ABSORPTION_AREAS and code.',
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
    band('transmission_loss', 125, 'Transmission loss', 'Pérdidas por transmisión', 'dB'),
    band('transmission_loss', 250, 'Transmission loss', 'Pérdidas por transmisión', 'cB'),
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
