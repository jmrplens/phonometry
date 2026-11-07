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
import { test } from 'node:test';

import {
  citationsFor,
  citedWorks,
  englishStandardIds,
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

  // Only a standard has a standards body.
  assert.equal(standardsBody(book, EN), undefined);
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
