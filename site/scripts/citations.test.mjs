// What src/lib/citations.mjs makes of a page's references, read on lists small
// enough to see whole.
//
// The built site only ever shows this code the references the guides happen to
// cite today, so a page that cited one work twice, or one standard from a body
// with no identity, or a Spanish edition note that no English slug matches,
// would build green whatever the code did with it. Each test here hands the
// functions such a list and reads what comes back.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  citationsFor,
  englishStandardIds,
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
