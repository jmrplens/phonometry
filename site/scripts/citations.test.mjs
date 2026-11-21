// What src/lib/citations.mjs makes of a page's references, read on lists small
// enough to see whole.
//
// The built site only ever shows this code the references the guides happen to
// cite today, so a page that cited one work twice, or one standard from a body
// with no identity, or a Spanish edition note that no English slug matches, or
// two pages that describe one work two ways, would build green whatever the
// code did with it. Each test here hands the functions such a list and reads
// what comes back.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { parse as parseYaml } from 'yaml';

import {
  citationsFor,
  citedWorks,
  correctedWorks,
  englishStandardIds,
  NOT_THE_BODY,
  bodyNamedIn,
  isBodyName,
  publisherName as publisherOf,
  publisherName,
  referenceId,
  referenceNode,
  referenceStub,
  standardsBody,
} from '../src/lib/citations.mjs';

const EN = 'https://example.org/docs/reference/bibliography/';
const ES = 'https://example.org/docs/es/reference/bibliography/';

const iso = (designation, extra = {}) => ({
  type: 'standard',
  organization: 'International Organization for Standardization',
  designation,
  title: `Title of ${designation}`,
  url: 'https://www.iso.org/standard/1.html',
  ...extra,
});
const paper = {
  type: 'article',
  authors: ['Doe, J.'],
  journal: 'A Journal',
  year: 2001,
  title: 'A paper',
  doi: '10.1000/xyz',
  volume: 3,
};
const book = { type: 'book', authors: ['Roe, R.'], publisher: 'A Press', year: 1999, title: 'A book' };

test('a page names each work at its first reference, in isBasedOn first, and points at it after', () => {
  const cited = citationsFor({
    references: [iso('ISO 1:2000', { primary: true }), paper, book, iso('ISO 1:2000')],
    bibliographyUrl: EN,
  });
  assert.deepEqual(Object.keys(cited), ['isBasedOn', 'citation', 'governingWorks']);

  const [standard] = cited.isBasedOn;
  assert.deepEqual(standard, {
    '@id': `${EN}#std-iso-1-2000`,
    '@type': 'CreativeWork',
    name: 'Title of ISO 1:2000',
    identifier: 'ISO 1:2000',
    url: 'https://www.iso.org/standard/1.html',
  });

  // The governing standard was named in isBasedOn, and the same entry listed
  // twice is named once; the paper and the book are named where they first
  // appear, in the citation list.
  assert.deepEqual(cited.citation[0], { '@id': `${EN}#std-iso-1-2000` });
  assert.deepEqual(cited.citation[3], { '@id': `${EN}#std-iso-1-2000` });
  assert.equal(cited.citation[1].name, 'A paper');
  assert.equal(cited.citation[1]['@type'], 'ScholarlyArticle');
  assert.deepEqual(cited.citation[1].identifier, { '@type': 'PropertyValue', propertyID: 'DOI', value: '10.1000/xyz' });
  assert.equal(cited.citation[1].sameAs, 'https://doi.org/10.1000/xyz');
  assert.equal(cited.citation[2].name, 'A book');
  assert.deepEqual(cited.governingWorks, [{ '@id': `${EN}#std-iso-1-2000` }]);
});

test('a stub carries the identity of the full node and none of its detail', () => {
  const full = referenceNode(paper, EN);
  const stub = referenceStub(paper, EN);
  for (const [key, value] of Object.entries(stub)) assert.deepEqual(value, full[key], key);
  for (const key of ['author', 'isPartOf', 'volumeNumber', 'datePublished']) assert.equal(stub[key], undefined, key);

  const report = { type: 'report', organization: 'An Agency', number: 'Doc 29', year: 2016, title: 'A report' };
  assert.equal(referenceStub(report, EN).reportNumber, 'Doc 29');
});

test('a data set is a Dataset under its own licence, by its creators and its repository, and a page names it with the licence', () => {
  const deposit = {
    type: 'dataset',
    authors: ['Zerwas, M.', 'Kayku, S.'],
    year: 2026,
    title: 'Room acoustic measurement and decay analysis data of the St. Nicholas Chapel, Aachen Cathedral',
    publisher: 'Zenodo',
    doi: '10.5281/zenodo.20428705',
    license: 'https://creativecommons.org/licenses/by/4.0/',
    note: 'The impulse response of the worked case.',
  };
  const node = referenceNode(deposit, EN);
  assert.equal(node['@id'], `${EN}#doi-10-5281-zenodo-20428705`);
  assert.equal(node['@type'], 'Dataset');
  assert.deepEqual(node.creator, [
    { '@type': 'Person', name: 'Zerwas, M.' },
    { '@type': 'Person', name: 'Kayku, S.' },
  ]);
  assert.deepEqual(node.publisher, { '@type': 'Organization', name: 'Zenodo' });
  assert.equal(node.license, 'https://creativecommons.org/licenses/by/4.0/');
  assert.equal(node.author, undefined);
  assert.equal(referenceStub(deposit, EN).license, 'https://creativecommons.org/licenses/by/4.0/');

  // A body that publishes data under its own name is its creator, and a data
  // set with no DOI keys on its type, its body, its year and its title.
  const series = {
    type: 'dataset',
    organization: 'Dublin City Council',
    year: 2017,
    title: 'Ambient sound monitoring network DCC',
    publisher: 'data.gov.ie',
    url: 'https://data.gov.ie/dataset/ambient-sound-monitoring-network',
    license: 'https://creativecommons.org/licenses/by/4.0/',
  };
  const seriesNode = referenceNode(series, EN);
  assert.equal(seriesNode['@id'], `${EN}#dataset-dublin-city-council-2017-ambient-sound-monitoring-network-dcc`);
  assert.deepEqual(seriesNode.creator, { '@type': 'Organization', name: 'Dublin City Council' });
});

test('a page that cites nothing publishes no citation properties', () => {
  assert.deepEqual(citationsFor({ references: undefined, bibliographyUrl: EN }), {});
  assert.deepEqual(citationsFor({ references: [], bibliographyUrl: EN }), {});
});

test('a page that marks nothing primary is based on its first implemented standards', () => {
  const cited = citationsFor({
    references: [book, iso('ISO 2:2000', { implemented: false }), iso('ISO 3:2000')],
    bibliographyUrl: EN,
  });
  assert.deepEqual(
    cited.isBasedOn.map((item) => item['@id']),
    [`${EN}#std-iso-3-2000`],
  );
  assert.equal(cited.isBasedOn[0].name, 'Title of ISO 3:2000');
});

test('every standards body has one identity, on the English bibliography, in both languages', () => {
  const en = referenceNode(iso('ISO 1:2000'), EN, { bodiesUrl: EN });
  const es = referenceNode(iso('ISO 1:2000'), ES, { bodiesUrl: EN });
  assert.deepEqual(en.publisher, { '@id': `${EN}#org-iso` });
  assert.deepEqual(es.publisher, en.publisher);
  assert.deepEqual(standardsBody(iso('ISO 1:2000'), EN), {
    '@type': 'Organization',
    '@id': `${EN}#org-iso`,
    name: 'International Organization for Standardization',
    alternateName: 'ISO',
    url: 'https://www.iso.org/',
  });

  // A named publisher is the body, not the issuing committee.
  const gum = {
    type: 'standard',
    organization: 'Joint Committee for Guides in Metrology',
    publisher: 'BIPM',
    designation: 'JCGM 100:2008',
    title: 'GUM',
  };
  assert.deepEqual(referenceNode(gum, EN).publisher, { '@id': `${EN}#org-bipm` });

  // The English and Spanish spellings of a Spanish authority are one body.
  const spain = { type: 'standard', organization: 'Jefatura del Estado (Spain)', designation: 'Ley 1/2000', title: 'Ley' };
  const espana = { ...spain, organization: 'Jefatura del Estado (España)' };
  assert.equal(standardsBody(spain, EN)['@id'], standardsBody(espana, EN)['@id']);

  // A body this file does not know stays anonymous, which is what the check
  // of the build looks for.
  const unknown = { type: 'standard', organization: 'Somebody Else', designation: 'SE 1', title: 'SE' };
  assert.equal(standardsBody(unknown, EN), undefined);
  assert.deepEqual(referenceNode(unknown, EN).publisher, { '@type': 'Organization', name: 'Somebody Else' });

  // A book from a publisher that is no body keeps the publisher's name.
  assert.equal(standardsBody(book, EN), undefined);
  assert.deepEqual(referenceNode(book, EN).publisher, { '@type': 'Organization', name: 'A Press' });
});

test('a body that publishes a report, a paper or a web page is named by the identity its standards name it by', () => {
  // An RFC cited as a report, ECAC Doc 29 and EASA's levels: each publisher is
  // the body its standards are filed under, read from the field the kind
  // writes it in. They used to be written out anonymously, because only a
  // standard looked its body up.
  const rfc = { type: 'report', organization: 'Internet Engineering Task Force', number: 'RFC 8259', year: 2017, title: 'JSON' };
  const doc29 = { type: 'report', organization: 'European Civil Aviation Conference', year: 2016, title: 'ECAC Doc 29' };
  const easa = { type: 'report', institution: 'European Union Aviation Safety Agency', year: 2024, title: 'Noise levels' };
  const aes = { type: 'web', organization: 'Audio Engineering Society', year: 2006, title: 'A convention paper' };
  const asaBook = { type: 'book', authors: ['Roe, R.'], publisher: 'Acoustical Society of America', year: 1993, title: 'A book' };
  assert.deepEqual(referenceNode(rfc, ES, { bodiesUrl: EN }).publisher, { '@id': `${EN}#org-ietf` });
  assert.deepEqual(referenceNode(doc29, EN).publisher, { '@id': `${EN}#org-ecac` });
  assert.deepEqual(referenceNode(easa, EN).publisher, { '@id': `${EN}#org-easa` });
  assert.deepEqual(referenceNode(aes, EN).publisher, { '@id': `${EN}#org-aes` });
  assert.deepEqual(referenceNode(asaBook, EN).publisher, { '@id': `${EN}#org-asa` });
  assert.equal(standardsBody(doc29, EN).url, 'https://www.ecac-ceac.org/');
  assert.equal(publisherName(easa), 'European Union Aviation Safety Agency');

  // A committee of a body is not the body: its pages keep the name they print.
  const wg = { type: 'web', organization: 'Acoustical Society of America, Working Group S3-79', title: 'Errata' };
  assert.deepEqual(referenceNode(wg, EN).publisher, {
    '@type': 'Organization',
    name: 'Acoustical Society of America, Working Group S3-79',
  });
  // A journal article names its journal and no publisher; a page that names
  // no organization names no publisher either.
  assert.equal(publisherName(paper), undefined);
  assert.equal('publisher' in referenceNode(paper, EN), false);
  assert.equal('publisher' in referenceNode({ type: 'web', title: 'A page' }, EN), false);
  assert.equal(isBodyName('Internet Engineering Task Force'), true);
  assert.equal(isBodyName('A Press'), false);
});

test('a Spanish standard is the English one it pairs with, translated edition notes included', () => {
  const pages = [
    { id: 'a/page', references: [iso('ISO 1:2000'), iso('ECMA-418-2, 4th ed.'), book] },
    { id: 'es/a/page', references: [iso('ISO 1:2000'), iso('ECMA-418-2, 4.ª ed.'), book] },
    // Out of step with its twin: the numbers differ, so no pair is made.
    { id: 'b/page', references: [iso('ISO 5:2005')] },
    { id: 'es/b/page', references: [iso('ISO 6:2006')] },
  ];
  const twins = englishStandardIds(pages, ES, EN);
  assert.deepEqual([...twins.get(`${ES}#std-iso-1-2000`)], [`${EN}#std-iso-1-2000`]);
  assert.deepEqual([...twins.get(`${ES}#std-ecma-418-2-4-ed`)], [`${EN}#std-ecma-418-2-4th-ed`]);
  assert.equal(twins.get(`${ES}#std-iso-6-2006`), undefined);

  const node = referenceNode(iso('ECMA-418-2, 4.ª ed.'), ES, {
    bodiesUrl: EN,
    translationOf: twins.get(`${ES}#std-ecma-418-2-4-ed`),
  });
  assert.equal(node.sameAs, `${EN}#std-ecma-418-2-4th-ed`);
});

test('a Spanish standard with a DOI keeps it beside its English address', () => {
  const node = referenceNode(iso('ISO 7:2007', { doi: '10.1000/iso7' }), ES, {
    bodiesUrl: EN,
    translationOf: [`${EN}#std-iso-7-2007`],
  });
  assert.deepEqual(node.sameAs, ['https://doi.org/10.1000/iso7', `${EN}#std-iso-7-2007`]);
  assert.equal(node.identifier, 'ISO 7:2007');
});

test('two works by one author in one year, or by one body, are two @ids', () => {
  // Two papers by one author in 2017: the DOI keys each.
  const iridescent = { ...paper, year: 2017, title: 'Iridescent perfect absorption', doi: '10.3390/app7060618' };
  const metadiffusers = { ...paper, year: 2017, title: 'Metadiffusers', doi: '10.1038/s41598-017-05710-5' };
  assert.equal(referenceId(iridescent, EN), `${EN}#doi-10-3390-app7060618`);
  assert.notEqual(referenceId(iridescent, EN), referenceId(metadiffusers, EN));

  // Two volumes of one report series carry one number; with no DOI, the title
  // keys them, and it reads the same in both languages where the number does not.
  const volume = (n, number) => ({
    type: 'report',
    organization: 'European Civil Aviation Conference',
    year: 2026,
    number,
    title: `Report on standard method of computing noise contours around civil airports, Volume ${n}`,
  });
  assert.notEqual(referenceId(volume(2, 'Doc 29, 5th ed.'), EN), referenceId(volume(3, 'Doc 29, 5th ed.'), EN));
  assert.equal(
    referenceId(volume(3, 'Doc 29, 5th ed.'), EN).slice(EN.length),
    referenceId(volume(3, 'Doc 29, 5.ª ed.'), ES).slice(ES.length),
  );
  assert.equal(
    referenceId(volume(3, 'Doc 29, 5th ed.'), EN),
    `${EN}#report-european-civil-aviation-conference-2026-report-on-standard-method-of-computing-noise-` +
      'contours-around-civil-airports-volume-3',
  );
});

test("a work's description is a guide's note before a catalogue page's, and every catalogue's when only catalogues cite it", () => {
  const harris = { type: 'book', authors: ['Harris, C. M. (Ed.)'], publisher: 'McGraw-Hill', year: 1995, title: 'Manual' };
  const at = (note, tables) => ({ ...harris, note, tables });
  const carpets = 'Tables 30.2 and 30.3: the source of the rows of the catalogue of carpets that cite it.';
  const impact = 'Tables 32.1 to 32.8: the source of the rows of the catalogue of impact insulation that cite it.';
  // Listed out of order: the catalogue pages are read in page order.
  const catalogues = [
    { id: 'reference/catalogues/impact-insulation', references: [at(impact, ['harris-1995-tables-32-1-to-32-8'])] },
    { id: 'reference/catalogues/carpets', references: [at(carpets, ['harris-1995-table-30-2'])] },
  ];
  const id = referenceId(harris, EN);
  assert.equal(citedWorks(catalogues, EN).get(id).note, `${carpets} ${impact}`);

  // A guide that cites the work, even one read after the catalogues, describes it.
  const guide = { id: 'room/acoustics/absorbers', references: [{ ...harris, note: 'The handbook of measurements.' }] };
  assert.equal(citedWorks([...catalogues, guide], EN).get(id).note, 'The handbook of measurements.');

  // In Spanish too, and one catalogue's note alone is that note.
  const es = [{ id: 'es/reference/catalogues/carpets', references: [at('Tablas 30.2 y 30.3.', ['harris-1995-table-30-2'])] }];
  assert.equal(citedWorks(es, ES).get(referenceId(harris, ES)).note, 'Tablas 30.2 y 30.3.');
});

test('the works a language cites, one reference each, refused when two pages describe one two ways', () => {
  const pages = [
    { id: 'a', references: [iso('ISO 1:2000', { note: 'Clause 4.' }), book] },
    // The note, primary and implemented fields belong to the page.
    { id: 'b', references: [iso('ISO 1:2000', { note: 'Annex A.', primary: true }), book] },
  ];
  const works = citedWorks(pages, EN);
  assert.deepEqual([...works.keys()], [`${EN}#std-iso-1-2000`, referenceId(book, EN)]);
  assert.equal(works.get(`${EN}#std-iso-1-2000`).note, 'Clause 4.');

  // One standard, two catalogue addresses.
  const twoUrls = [...pages, { id: 'c', references: [iso('ISO 1:2000', { url: 'https://www.iso.org/standard/2.html' })] }];
  assert.throws(
    () => citedWorks(twoUrls, EN),
    /two ways, in 1 place\(s\)[^]*#std-iso-1-2000 url: "https:\/\/www\.iso\.org\/standard\/1\.html" on a, b; "https:\/\/www\.iso\.org\/standard\/2\.html" on c/,
  );

  // One standard with a URL on one page and none on another.
  const noUrl = [...pages, { id: 'c', references: [iso('ISO 1:2000', { url: undefined })] }];
  assert.throws(() => citedWorks(noUrl, EN), /#std-iso-1-2000 url: [^;]+ on a, b; \(none\) on c/);

  // One book with its DOI on one page and without it on another: two @ids,
  // which nothing would compare.
  const withDoi = { ...book, doi: '10.1000/book' };
  assert.throws(
    () => citedWorks([{ id: 'a', references: [withDoi] }, { id: 'b', references: [book] }], EN),
    /#book-roe-1999-a-book doi: \(none\) on b; "10\.1000\/book" elsewhere/,
  );

  // One DOI on two standards' designations.
  const gum = (designation) => iso(designation, { doi: '10.59161/JCGM100-2008E' });
  assert.throws(
    () => citedWorks([{ id: 'a', references: [gum('JCGM 100:2008, la GUM'), gum('JCGM 100:2008, the GUM')] }], EN),
    /DOI 10\.59161\/jcgm100-2008e names 2 works/,
  );
});

test('one standard cited under two designations, translated or not, is refused, and two editions or two bodies are not', () => {
  const cite = (designation, year, organization = 'Ecma International') =>
    iso(designation, { year, organization, url: undefined });
  const ecma = [
    { id: 'a', references: [cite('ECMA-418-2, 4th ed.', 2025)] },
    { id: 'b', references: [cite('ECMA-418-2:2025', 2025)] },
    { id: 'c', references: [cite('ECMA-418-2:2025 (4th ed.)', 2025)] },
  ];
  assert.throws(
    () => citedWorks(ecma, EN),
    /ECMA-418-2 \(2025\) is cited as 3 standards: "ECMA-418-2, 4th ed\." on a; "ECMA-418-2:2025" on b; "ECMA-418-2:2025 \(4th ed\.\)" on c/,
  );

  // An annex cited as a work of its own, a date, a reaffirmation: each is
  // still the one standard.
  for (const [first, second, year] of [
    ['IEC 60268-1:1985, Appendix A (with Amendment 1:1988)', 'IEC 60268-1:1985', 1985],
    ['Recommendation ITU-R BS.1770-5 (11/2023)', 'Recommendation ITU-R BS.1770-5', 2023],
    ['ANSI S3.5-1997 (R2017)', 'ANSI S3.5-1997 (R2020)', 1997],
    ['ISO 7235:2003', 'ISO 7235:2003 (EN ISO 7235:2009)', 2003],
  ]) {
    const pages = [
      { id: 'a', references: [cite(first, year)] },
      { id: 'b', references: [cite(second, year)] },
    ];
    assert.throws(() => citedWorks(pages, EN), /is cited as 2 standards/, `${first} and ${second}`);
  }

  // A designation translated with the page, or written with its body's name
  // in front, is still the one standard: the body, the numbers of the base
  // and the year say which it is, whatever words surround them.
  const itu = (designation, year) => cite(designation, year, 'International Telecommunication Union');
  assert.throws(
    () =>
      citedWorks(
        [
          { id: 'es/a', references: [itu('Recomendación UIT-R BS.468-4', 1986)] },
          { id: 'es/b', references: [itu('Recommendation ITU-R BS.468-4', 1986)] },
        ],
        ES,
      ),
    /Recomendación UIT-R BS\.468-4 \(1986\) is cited as 2 standards: "Recomendación UIT-R BS\.468-4" on es\/a; "Recommendation ITU-R BS\.468-4" on es\/b/,
  );
  for (const [first, second, year, organization] of [
    ['Recomendación UIT-R BS.1770-5 (11/2023)', 'Recommendation ITU-R BS.1770-5', 2023, 'International Telecommunication Union'],
    ['ANSI/ASA S3.5-1997', 'ANSI S3.5-1997 (R2017)', 1997, 'American National Standards Institute'],
  ]) {
    const pages = [
      { id: 'a', references: [cite(first, year, organization)] },
      { id: 'b', references: [cite(second, year, organization)] },
    ];
    assert.throws(() => citedWorks(pages, EN), /is cited as 2 standards/, `${first} and ${second}`);
  }

  // The same numbers and year from two bodies are two documents: the
  // European adoption of an ISO standard is CEN's, with its own foreword.
  const adoption = [
    { id: 'a', references: [cite('ISO 354:2003', 2003, 'International Organization for Standardization')] },
    { id: 'b', references: [cite('EN ISO 354:2003', 2003, 'European Committee for Standardization')] },
  ];
  assert.equal(citedWorks(adoption, EN).size, 2);

  // Two editions are two works, with the year in the designation or only in
  // the year field.
  const editions = [
    { id: 'a', references: [cite('ISO 10140-1:2010', 2010), cite('ISO 1:2000', undefined)] },
    { id: 'b', references: [cite('ISO 10140-1:2021', 2021), cite('ISO 1:2010', undefined)] },
  ];
  assert.equal(citedWorks(editions, EN).size, 4);
});

test('two works sharing a base designation and a year pass only when listed with the reason they differ', () => {
  const volume = (designation) =>
    iso(designation, { year: 2017, organization: 'International Civil Aviation Organization', url: undefined });
  const pages = [
    { id: 'a', references: [volume('ICAO Annex 16, Vol. I')] },
    { id: 'b', references: [volume('ICAO Annex 16, Vol. II')] },
  ];
  assert.throws(() => citedWorks(pages, EN), /ICAO Annex 16 \(2017\) is cited as 2 standards/);

  const reason = 'Volume I is aircraft noise and Volume II engine emissions: two documents.';
  const listed = [{ designations: ['ICAO Annex 16, Vol. I', 'ICAO Annex 16, Vol. II'], reason }];
  assert.equal(citedWorks(pages, EN, { separateStandards: listed }).size, 2);

  // An entry without its reason is refused, and so is one that no longer
  // separates anything: only one of its designations is still cited, none of
  // them is, or the ones still cited no longer share a base and a year.
  assert.throws(
    () => citedWorks(pages, EN, { separateStandards: [{ designations: listed[0].designations, reason: ' ' }] }),
    /says no reason/,
  );
  assert.throws(
    () => citedWorks([pages[0]], EN, { separateStandards: listed }),
    /lists "ICAO Annex 16, Vol\. I", "ICAO Annex 16, Vol\. II" as separate works, and only "ICAO Annex 16, Vol\. I" is cited/,
  );
  const elsewhere = [{ id: 'c', references: [iso('ISO 1:2000', { year: 2000, url: undefined })] }];
  assert.throws(
    () => citedWorks(elsewhere, EN, { separateStandards: listed }),
    /lists "ICAO Annex 16, Vol\. I", "ICAO Annex 16, Vol\. II" as separate works, and none of them is cited/,
  );
  const apart = [
    { id: 'a', references: [volume('ICAO Annex 16, Vol. I')] },
    { id: 'b', references: [iso('ICAO Annex 16, Vol. II', { year: 2018, organization: 'International Civil Aviation Organization', url: undefined })] },
  ];
  assert.throws(
    () => citedWorks(apart, EN, { separateStandards: listed }),
    /lists "ICAO Annex 16, Vol\. I", "ICAO Annex 16, Vol\. II" as separate works, and no two of them share a base and a year any more/,
  );
});

test('an errata page names each work it corrects as the bibliography of its language describes it', () => {
  const pages = [
    { id: 'signals/levels', references: [iso('ISO 1:2000', { note: 'What the guide implements.', primary: true }), paper] },
    { id: 'es/signals/levels', references: [iso('ISO 1:2000', { note: 'Lo que implementa la guía.' })] },
  ];
  const english = citedWorks(pages.filter((page) => !page.id.startsWith('es/')), EN);
  const named = correctedWorks(['std-iso-1-2000', referenceId(paper, EN).split('#')[1]], english, EN);
  assert.deepEqual(named, [referenceStub(pages[0].references[0], EN), referenceStub(paper, EN)]);
  // A stub names the work and says nothing of the page that cites it.
  assert.equal(named[0].description, undefined);
  assert.equal(named[0]['@id'], `${EN}#std-iso-1-2000`);

  const spanish = citedWorks(pages.filter((page) => page.id.startsWith('es/')), ES);
  assert.equal(correctedWorks(['std-iso-1-2000'], spanish, ES)[0]['@id'], `${ES}#std-iso-1-2000`);
  assert.deepEqual(correctedWorks([], english, EN), []);
});

test('an errata page that corrects a work the bibliography does not define stops the build, naming it', () => {
  const english = citedWorks([{ id: 'signals/levels', references: [iso('ISO 1:2000')] }], EN);
  assert.throws(
    () => correctedWorks(['std-iso-1-2000', 'std-iso-9-1999', 'doi-10-1000-none'], english, EN),
    /corrects 2 work\(s\) the bibliography at .* does not define: std-iso-9-1999, doi-10-1000-none/,
  );
  // Each language's bibliography is a set of works of its own: a work only
  // English pages cite is not on the Spanish one.
  assert.throws(() => correctedWorks(['std-iso-1-2000'], citedWorks([], ES), ES), /does not define: std-iso-1-2000/);
});

test('a body written out inside a longer publisher name is found, and an organization of its own is not', () => {
  assert.equal(bodyNamedIn('Official Journal of the European Union'), 'eu');
  assert.equal(bodyNamedIn('Diario Oficial de la Unión Europea'), 'eu');
  assert.equal(bodyNamedIn('Internet Engineering Task Force (IETF)'), 'ietf');
  assert.equal(bodyNamedIn('European Union'), undefined, 'the body itself has its identity');
  assert.equal(bodyNamedIn('UNESCO'), undefined, 'UNE inside a word is no body');
  for (const name of Object.keys(NOT_THE_BODY)) assert.equal(bodyNamedIn(name), undefined, name);
});

test('no page cites a work from a body written out under a longer name, in either language', () => {
  // Two EU directives were cited from "Official Journal of the European
  // Union" (and, on one Spanish page, "Diario Oficial de la Unión Europea")
  // while four named the EU's identity.
  const found = [];
  const walk = (dir) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) walk(path);
      else if (/\.mdx?$/.test(entry.name)) {
        const frontmatter = /^---\r?\n([\s\S]*?)\r?\n---/.exec(readFileSync(path, 'utf8'))?.[1];
        const references = frontmatter ? (parseYaml(frontmatter)?.references ?? []) : [];
        for (const ref of references) {
          const body = bodyNamedIn(publisherOf(ref));
          if (body) found.push(`${path.slice(path.indexOf('src/content'))}: ${JSON.stringify(publisherOf(ref))} writes out the body ${body}`);
        }
      }
    }
  };
  walk(fileURLToPath(new URL('../src/content/docs', import.meta.url)));
  assert.deepEqual(found, []);
});
