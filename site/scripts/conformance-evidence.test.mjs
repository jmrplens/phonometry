// The join of the conformance report with the pages and the works they cite
// (src/lib/conformance-evidence.mjs), on reports and pages small enough to
// read, and once on the real ones.
//
// The real report and the real pages only ever hand the join the documents
// the checks cite today, written the way they are written today, so a branch
// that stopped refusing an unresolved standard, or a "Verified by" line that
// started counting a standard the page only cites, would stay green there.
// Each test here writes the report and the references it needs. The real ones
// are joined by the build itself: the report page cannot be rendered while a
// standard its checks are based on resolves to no work.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { conformanceEvidence, documentKey } from '../src/lib/conformance-evidence.mjs';

const BIBLIOGRAPHY = 'https://example.org/reference/bibliography/';
const REPORT_PATH = '/site/reference/conformance/';

/** A standard as a page's frontmatter cites it. */
const standard = (designation, year, extra = {}) => ({
  type: 'standard',
  organization: 'International Organization for Standardization',
  year,
  title: `Acoustics, ${designation}`,
  designation,
  ...extra,
});

/** A check of `domain` citing `documents`, each `[designation, edition, relation]`. */
const check = (id, domain, documents) => ({
  id,
  domain,
  reference: {
    documents: documents.map(([designation, edition, relation], i) => ({
      kind: 'standard',
      designation,
      ...(edition ? { edition } : {}),
      ...(i > 0 ? { relation: relation ?? 'corroborates' } : {}),
    })),
  },
});

/** A report of these checks over the domains they name. */
const report = (checks) => ({
  checks,
  domains: [...new Set(checks.map((c) => c.domain))].map((id) => ({ id, title: `The ${id} domain` })),
});

/** The join of `checks` with one page citing `references`, and any other pages. */
const evidence = (checks, references, { others = [], sameWorks = [] } = {}) =>
  conformanceEvidence({
    report: report(checks),
    pages: [{ id: 'topic/guide', references }, ...others],
    bibliographyUrl: BIBLIOGRAPHY,
    reportPath: REPORT_PATH,
    sameWorks,
  });

test('a designation is read without its punctuation of the year, its qualifiers or its language', () => {
  assert.equal(documentKey('ANSI S3.5-1997 (R2017)'), 'ANSI S3.5:1997');
  assert.equal(documentKey('ANSI S3.5:1997'), 'ANSI S3.5:1997');
  assert.equal(documentKey('Recomendación UIT-R BS.468-4', 1986), 'ITU-R BS.468-4:1986');
  assert.equal(documentKey('Recommendation ITU-R BS.468-4', 1986), 'ITU-R BS.468-4:1986');
  assert.equal(documentKey('SAE ARP 5534, reaffirmed 2021', 2013), 'SAE ARP 5534:2013');
  assert.equal(documentKey('Directiva 2002/44/CE'), 'Directive 2002/44/EC');
  assert.equal(documentKey('IEC 60268-16:2020 (Edition 5)'), 'IEC 60268-16:2020');
  // An amendment is part of the document; a part number is not a year.
  assert.equal(documentKey('ISO 3745:2012/Amd.1:2017'), 'ISO 3745:2012/Amd.1:2017');
  assert.equal(documentKey('ISO 1996-2'), 'ISO 1996-2');
});

test('a page is verified by the checks of the standards it implements, counted once and by domain', () => {
  const joined = evidence(
    [
      check('a/1', 'a', [['ISO 1', '2000']]),
      check('a/2', 'a', [['ISO 1', '2000'], ['ISO 2', '2010']]),
      check('b/1', 'b', [['ISO 2', '2010']]),
      check('c/1', 'c', [['ISO 3', '2020']]),
    ],
    [standard('ISO 1:2000', 2000), standard('ISO 2:2010', 2010)],
    { others: [{ id: 'topic/other', references: [standard('ISO 3:2020', 2020)] }] },
  );
  assert.deepEqual(joined.verifiedBy([standard('ISO 1:2000', 2000), standard('ISO 2:2010', 2010)]), {
    checks: 3,
    designations: ['ISO 1:2000', 'ISO 2:2010'],
    domains: [
      { id: 'a', title: 'The a domain', checks: 2, path: `${REPORT_PATH}#a` },
      { id: 'b', title: 'The b domain', checks: 1, path: `${REPORT_PATH}#b` },
    ],
  });
});

test('a standard the page only cites, and one a check names in passing, verify nothing', () => {
  const joined = evidence(
    [check('a/1', 'a', [['ISO 1', '2000']]), check('b/1', 'b', [['ISO 9', '1999'], ['ISO 2', '2010', 'mentions']])],
    [standard('ISO 1:2000', 2000, { implemented: false }), standard('ISO 2:2010', 2010), standard('ISO 9:1999', 1999)],
  );
  assert.equal(joined.verifiedBy([standard('ISO 1:2000', 2000, { implemented: false })]), undefined);
  assert.equal(joined.verifiedBy([standard('ISO 2:2010', 2010)]), undefined);
  // Named in passing, it is not a work the report is based on either.
  assert.deepEqual(
    joined.governing.map((ref) => ref.designation),
    ['ISO 1:2000', 'ISO 9:1999'],
  );
});

test('a check that cites a standard with no year means the one edition the pages cite, and two editions fail', () => {
  const one = evidence([check('a/1', 'a', [['ISO 717-1']])], [standard('ISO 717-1:2020', 2020)]);
  assert.equal(one.verifiedBy([standard('ISO 717-1:2020', 2020)])?.checks, 1);
  assert.throws(
    () =>
      evidence([check('a/1', 'a', [['ISO 717-1']])], [standard('ISO 717-1:2020', 2020)], {
        others: [{ id: 'topic/other', references: [standard('ISO 717-1:2013', 2013)] }],
      }),
    /ISO 717-1: 2 works answer to it \(#std-iso-717-1-2020, #std-iso-717-1-2013\)/,
  );
});

test('a standard the checks are based on that no page cites fails the join, with every other one', () => {
  assert.throws(
    () =>
      evidence(
        [check('a/1', 'a', [['ISO 1', '2000']]), check('a/2', 'a', [['ISO 4', '2004']]), check('a/3', 'a', [['EN 5', '2005']])],
        [standard('ISO 1:2000', 2000)],
      ),
    (error) => {
      assert.match(error.message, /in 2 place\(s\)/);
      assert.match(error.message, /ISO 4:2004: no page cites it, and no entry of SAME_WORKS says which work it is/);
      assert.match(error.message, /EN 5:2005: no page cites it/);
      return true;
    },
  );
});

test('a pairing says which work a standard written otherwise is, and the work it picks is verified by its checks', () => {
  const sameWorks = [{ document: 'EN 61260:1995', works: [{ designation: 'IEC 61260:1995' }], reason: 'The adoption.' }];
  const joined = evidence(
    [check('a/1', 'a', [['EN 61260', '1995']])],
    [standard('IEC 61260:1995', 1995, { organization: 'International Electrotechnical Commission' })],
    { sameWorks },
  );
  assert.deepEqual(joined.governing.map((ref) => ref.designation), ['IEC 61260:1995']);
  assert.equal(joined.verifiedBy([standard('IEC 61260:1995', 1995, { organization: 'International Electrotechnical Commission' })])?.checks, 1);
});

test('a pairing with no reason, no work, two works, or none needed fails, and so does one no check needs', () => {
  const pages = [standard('ISO 1:2000', 2000), standard('ISO 2:2010', 2010)];
  const fails = (sameWorks, pattern) =>
    assert.throws(() => evidence([check('a/1', 'a', [['EN 1', '2000']]), check('a/2', 'a', [['ISO 2', '2010']])], pages, { sameWorks }), pattern);
  fails([{ document: 'EN 1:2000', works: [{ designation: 'ISO 1:2000' }], reason: ' ' }], /SAME_WORKS pairs EN 1:2000 and says no reason/);
  fails([{ document: 'EN 1:2000', works: [{ designation: 'ISO 7:2000' }], reason: 'r' }], /which no work the pages cite answers to/);
  fails(
    [{ document: 'EN 1:2000', works: [{ organization: 'International Organization for Standardization' }], reason: 'r' }],
    /which 2 works the pages cite answer to/,
  );
  fails(
    [
      { document: 'EN 1:2000', works: [{ designation: 'ISO 1:2000' }], reason: 'r' },
      { document: 'ISO 2:2010', works: [{ designation: 'ISO 2:2010' }], reason: 'r' },
    ],
    /SAME_WORKS pairs ISO 2:2010, which the designations already join to the work it names/,
  );
  fails(
    [
      { document: 'EN 1:2000', works: [{ designation: 'ISO 1:2000' }], reason: 'r' },
      { document: 'EN 9:1999', works: [{ designation: 'ISO 1:2000' }], reason: 'r' },
    ],
    /SAME_WORKS pairs EN 9:1999, which no check is based on any more/,
  );
});

test('a standard and its amendment, cited by the pages as two works, are both what one document of the report is', () => {
  const sameWorks = [
    {
      document: 'IEC 60118-4:2014+A1',
      works: [{ designation: 'IEC 60118-4:2014' }, { designation: 'IEC 60118-4:2014/AMD1:2017' }],
      reason: 'The amended text.',
    },
  ];
  const base = standard('IEC 60118-4:2014', 2014);
  const amendment = standard('IEC 60118-4:2014/AMD1:2017', 2017);
  const joined = evidence([check('a/1', 'a', [['IEC 60118-4', '2014+A1']])], [base, amendment], { sameWorks });
  assert.deepEqual(joined.governing.map((ref) => ref.designation), ['IEC 60118-4:2014', 'IEC 60118-4:2014/AMD1:2017']);
  assert.equal(joined.verifiedBy([amendment])?.checks, 1);
});
