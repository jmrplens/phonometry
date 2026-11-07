// The join of the conformance report with the pages and the works they cite
// (src/lib/conformance-evidence.mjs), on reports and pages small enough to
// read.
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
    works: ['ISO 1:2000', 'ISO 2:2010'],
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

test('a work the page cites that is no standard is verified by the checks of the standard the report names it by', () => {
  // The report names the speech guide's reference program by the working
  // group that keeps it, the Chen and Millero equation by the body that
  // adopted it, and a directive by its number: a web page, an article and a
  // report on the page, each verified by the checks of the document it is.
  const kit = {
    type: 'web',
    authors: ['Pavlovic, C.'],
    organization: 'Acoustical Society of America, Working Group S3-79',
    title: "C program developer's kit for the Speech Intelligibility Index (SII.C)",
    url: 'https://www.sii.to/html/programs.html',
  };
  const article = {
    type: 'article',
    authors: ['Chen, C.-T.', 'Millero, F. J.'],
    year: 1977,
    title: 'Speed of sound in seawater at high pressures',
    journal: 'The Journal of the Acoustical Society of America',
    doi: '10.1121/1.381646',
  };
  const directive = { type: 'report', organization: 'European Parliament', year: 2002, title: 'Directive on vibration', number: 'Directive 2002/44/EC' };
  const handbook = {
    type: 'report',
    organization: 'American Society of Heating, Refrigerating and Air-Conditioning Engineers',
    year: 2019,
    title: 'ASHRAE handbook: HVAC applications (SI edition), Chapter 49, Noise and vibration control',
  };
  const sameWorks = [
    { document: 'ASA WG S3-79', works: [{ type: 'web', url: kit.url }], reason: 'The kit.' },
    { document: 'UNESCO', works: [{ type: 'article', doi: article.doi }], reason: 'The equation.' },
    { document: 'ASHRAE 2019', works: [{ type: 'report', year: 2019 }], reason: 'The handbook.' },
  ];
  const checks = [
    check('a/1', 'a', [['ANSI S3.5', '1997']]),
    check('a/2', 'a', [['ASA WG S3-79']]),
    check('a/3', 'a', [['ASA WG S3-79']]),
    check('b/1', 'b', [['UNESCO']]),
    check('c/1', 'c', [['Directive 2002/44/EC']]),
    check('d/1', 'd', [['ASHRAE 2019']]),
  ];
  const pages = [standard('ANSI S3.5-1997 (R2017)', 1997), kit, article, directive, handbook];
  const joined = evidence(checks, pages, { sameWorks });
  assert.deepEqual(joined.verifiedBy([standard('ANSI S3.5-1997 (R2017)', 1997), kit]), {
    checks: 3,
    works: ['ANSI S3.5-1997 (R2017)', "C program developer's kit for the Speech Intelligibility Index (SII.C)"],
    domains: [{ id: 'a', title: 'The a domain', checks: 3, path: `${REPORT_PATH}#a` }],
  });
  assert.deepEqual(joined.verifiedBy([article])?.works, ['Chen & Millero 1977']);
  assert.deepEqual(joined.verifiedBy([directive])?.works, ['Directive 2002/44/EC']);
  assert.deepEqual(joined.verifiedBy([handbook])?.works, ['ASHRAE handbook: HVAC applications (SI edition)']);
  // A Spanish page names the authors the way its header chips do.
  const spanish = conformanceEvidence({
    report: report(checks),
    pages: [{ id: 'es/topic/guide', references: pages }],
    bibliographyUrl: BIBLIOGRAPHY,
    reportPath: REPORT_PATH,
    sameWorks,
    lang: 'es',
  });
  assert.deepEqual(spanish.verifiedBy([article])?.works, ['Chen y Millero 1977']);
  // What the page only reads verifies nothing, whatever kind of work it is.
  assert.equal(joined.verifiedBy([{ ...directive, implemented: false }]), undefined);
});

test('the line names each work without a comma, since commas are what separate them', () => {
  const annex = standard('ICAO Annex 16, Vol. I, 8th ed.', 2017, { organization: 'International Civil Aviation Organization' });
  const manual = standard('Doc 9501, 3rd ed.', 2018, { organization: 'International Civil Aviation Organization' });
  const arp = standard('SAE ARP 5534, reaffirmed 2021', 2013, { organization: 'SAE International' });
  const gum = standard('JCGM 100:2008, the GUM', 2008, { organization: 'Joint Committee for Guides in Metrology' });
  const joined = evidence(
    [
      check('a/1', 'a', [['ICAO Annex 16', '2017']]),
      check('a/2', 'a', [['Doc 9501', '2018']]),
      check('a/3', 'a', [['SAE ARP 5534', '2013']]),
      check('b/1', 'b', [['JCGM 100', '2008']]),
    ],
    [annex, manual, arp, gum],
  );
  const named = joined.verifiedBy([annex, manual, arp, gum])?.works;
  assert.deepEqual(named, ['ICAO Annex 16', 'Doc 9501', 'SAE ARP 5534', 'JCGM 100:2008']);
  assert.ok(named.every((name) => !name.includes(',')), named.join(' | '));
});

test('a pairing that sends a standard away from the work its designation joins, or a second pairing of it, fails', () => {
  const pages = [standard('ISO 3745:2012', 2012), standard('ISO 3744:2010', 2010)];
  const checks = [check('a/1', 'a', [['ISO 3745', '2012']]), check('b/1', 'b', [['ISO 3744', '2010']])];
  const join = (sameWorks) => evidence(checks, pages, { sameWorks });
  assert.throws(
    () => join([{ document: 'ISO 3745:2012', works: [{ designation: 'ISO 3744:2010' }], reason: 'r' }]),
    /SAME_WORKS pairs ISO 3745:2012 with what the pages cite as other works than ISO 3745:2012, the work its designation already names/,
  );
  assert.throws(
    () =>
      join([
        { document: 'ISO 3744:2010', works: [{ designation: 'ISO 3744:2010' }, { designation: 'ISO 3745:2012' }], reason: 'first' },
        { document: 'ISO 3744:2010', works: [{ designation: 'ISO 3745:2012' }], reason: 'second' },
      ]),
    /SAME_WORKS pairs ISO 3744:2010 twice/,
  );
});

test('a pairing may add to the work its designation names only an amendment of it, which its checks then verify', () => {
  const base = standard('ISO 3745:2012', 2012);
  const amendment = standard('ISO 3745:2012/Amd 1:2017', 2017);
  const other = standard('ISO 3744:2010', 2010);
  const checks = [check('a/1', 'a', [['ISO 3745', '2012']]), check('b/1', 'b', [['ISO 3744', '2010']])];
  const join = (sameWorks) => evidence(checks, [base, amendment, other], { sameWorks });
  // The work its designation names and its amendment, cited as two works,
  // is what a pairing may add a work for.
  const amended = join([
    { document: 'ISO 3745:2012', works: [{ designation: 'ISO 3745:2012' }, { designation: 'ISO 3745:2012/Amd 1:2017' }], reason: 'r' },
  ]);
  assert.equal(amended.verifiedBy([amendment])?.checks, 1);
  // Another standard beside it would put the checks of ISO 3744 on a guide
  // that implements ISO 3745 alone.
  assert.throws(
    () => join([{ document: 'ISO 3744:2010', works: [{ designation: 'ISO 3744:2010' }, { designation: 'ISO 3745:2012' }], reason: 'r' }]),
    /SAME_WORKS pairs ISO 3744:2010 with ISO 3745:2012 beside ISO 3744:2010, which its designation already names, and ISO 3745:2012 amends none of them/,
  );
});

test('a pairing that picks one of the editions a standard with no year names may add to it only an amendment of that edition', () => {
  const pages = [standard('ISO 717-1:2020', 2020), standard('ISO 717-1:2013', 2013), standard('ISO 3745:2012', 2012)];
  const checks = [check('a/1', 'a', [['ISO 717-1']]), check('b/1', 'b', [['ISO 3745', '2012']])];
  const join = (works) => evidence(checks, pages, { sameWorks: [{ document: 'ISO 717-1', works, reason: 'r' }] });
  assert.equal(join([{ designation: 'ISO 717-1:2020' }]).verifiedBy([standard('ISO 717-1:2020', 2020)])?.checks, 1);
  assert.throws(
    () => join([{ designation: 'ISO 717-1:2020' }, { designation: 'ISO 3745:2012' }]),
    /SAME_WORKS pairs ISO 717-1 with ISO 3745:2012 beside ISO 717-1:2020, ISO 717-1:2013, which its designation already names, and ISO 3745:2012 amends none of them/,
  );
});
