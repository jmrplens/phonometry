/**
 * What the conformance report verifies, joined to the pages and to the works
 * the bibliography defines.
 *
 * Every check of `docs/conformance.json` cites the documents it is judged
 * against, each split into a designation and an edition ("IEC 61260-1",
 * "2014"). Every guide declares in its frontmatter the standards it
 * implements. The two used to meet nowhere: 21 of 186 English guides linked
 * the report at all, none said which of its checks bore on the page, and the
 * report's own Dataset named the script that writes it as the one thing it was
 * based on, under an MIT licence, while every expected value it holds is
 * quoted from a standard.
 *
 * This module is the join, read the same way from both ends:
 *
 * - `governing` is every work the checks are based on, as the reference a
 *   page cites it with, so the Dataset can name each one the way the
 *   bibliography defines it (src/lib/citations.mjs, `referenceStub`);
 * - `verifiedBy(references)` is what a page's "Verified by" line states: how
 *   many checks are based on the works the page implements, named as the
 *   line names them, and in which domains of the report.
 *
 * The standard a check is based on is not always a standard on the page: the
 * report names the speech guide's reference program by the working group
 * that keeps it, the Chen and Millero equation by the body that adopted it,
 * a directive by its number. The page cites each as what it is, a web page,
 * an article, a report, and the line counts the checks of whatever work the
 * document resolves to.
 *
 * What the join reads are the documents the report files as standards. A
 * book, an article, a report or a web page the report names is a source of
 * the numbers, and the line does not count it, even on a page that cites it;
 * a standard the report filed under one of those kinds would be left out of
 * the line and of the Dataset with nothing to say so, which is why the
 * report's own tests refuse one (tests/test_conformance_artifact.py, "no
 * standard is filed under another kind").
 *
 * A standard a check names is the work a page cites when the two designations
 * name the same document and edition: the punctuation of the year, a
 * "Recommendation" in front, an edition or a reaffirmation written after a
 * comma or in brackets, and the page's language set aside. A check that cites
 * a standard with no year means the one edition the pages cite. Every other
 * pairing is written out in `SAME_WORKS` with the reason it is one work, the
 * national edition of an international standard for instance, and an entry
 * that no check needs any more is refused, like one that pairs nothing, one
 * the designations already make, a second one for the same document, one
 * that sends a document away from the work its designation names, and one
 * that adds beside that work another than an amendment of it: either would
 * move its checks onto a guide that does not implement it. A pairing of a
 * document the designations resolve to no work rests on the reason it gives,
 * read in review, since the true ones share no designation (BS 5969 is
 * IEC 651, the UNESCO equation an article). A
 * standard the checks are based on that resolves to no work, or to two,
 * fails the build: the Dataset would otherwise name fewer standards than its
 * values come from, and nothing would say so.
 *
 * A document a citation names only in passing (the relation `mentions`: the
 * apparatus a table is for, the copy the numbers were read from, the source a
 * book took a model from) holds none of the values a check pins, so it is not
 * a work the checks are based on and verifies no page.
 *
 * Nothing here starts a process or reads a file: the report and the pages are
 * handed in, so a test can hand in its own.
 */
import { authorDate } from './author-date.mjs';
import { referenceId } from './citations.mjs';

/** The relation of a document a citation names in passing (scripts/conformance/references.py). */
const IN_PASSING = 'mentions';

/**
 * A designation reduced to what names the document and its edition, the same
 * way on both sides of the join: "ANSI S3.5-1997 (R2017)" and "ANSI S3.5" of
 * 1997 are both "ANSI S3.5:1997", "Recomendación UIT-R BS.468-4" is
 * "ITU-R BS.468-4", "Directiva 2002/44/CE" is "Directive 2002/44/EC". An
 * amendment stays part of the key: ISO 3745:2012 and its Amendment 1 are two
 * works.
 *
 * @param {string} designation
 * @param {string | number | undefined} [year] The year of the edition when the
 *   designation does not write one.
 * @returns {string}
 */
export function documentKey(designation, year) {
  const bare = String(designation)
    .replace(/,.*$/, '')
    .replace(/\s*\([^)]*\)/g, '')
    .replace(/^(?:Recommendation|Recomendación)\s+/i, '')
    .replace(/\bUIT-/g, 'ITU-')
    .replace(/^Directiva\b/, 'Directive')
    .replace(/\/CE$/, '/EC')
    .replace(/-((?:19|20)\d\d)$/, ':$1')
    .replace(/\s+/g, ' ')
    .trim();
  return /:\d{4}/.test(bare) || !/^\d{4}$/.test(String(year ?? '')) ? bare : `${bare}:${year}`;
}

/** The key without its edition, for a check that cites a standard with no year. */
const undated = (key) => key.replace(/:.*$/, '');

/** The key of a page reference that has one: a standard's designation, a report's number. */
const workKey = (ref) => {
  const designation = ref?.type === 'standard' ? ref.designation : ref?.type === 'report' ? ref.number : undefined;
  return designation === undefined ? undefined : documentKey(designation, ref.year);
};

/** The words of a name up to its first comma, which sets off an edition, a volume or a gloss. */
const beforeComma = (text) => String(text).split(',')[0].trim();

/**
 * The name the "Verified by" line gives a work: the one a reader finds it
 * under on the page, and never one with a comma in it, since commas are what
 * separate the works in the line. A standard is its designation and a report
 * its number, each up to the first comma ("ICAO Annex 16, Vol. I, 8th ed." is
 * "ICAO Annex 16"; the edition stays when the designation writes it with a
 * colon, so ISO 389-1:1998 and ISO 389-7:2005 stay apart); an article or a
 * book is its authors and year, as its header chip names it
 * (src/lib/author-date.mjs); a web page or a report with no number, which no
 * chip names, is its title up to the first comma.
 *
 * @param {object} ref A page reference.
 * @param {'en' | 'es'} lang
 * @returns {string}
 */
export function workName(ref, lang = 'en') {
  if (ref.type === 'standard') return beforeComma(ref.designation);
  if (ref.type === 'report' && ref.number) return beforeComma(ref.number);
  if (ref.type === 'article' || ref.type === 'book') {
    const named = authorDate(ref.authors, ref.year, lang === 'es');
    if (named) return named;
  }
  return beforeComma(ref.title);
}

/**
 * Standards a check cites under one designation and a page under another, and
 * the reason they are one work. `document` is the designation and edition as
 * the report writes them; each of `works` picks the page reference it is, by
 * its designation (compared as `documentKey` reads it) or by the fields of a
 * work that has none. A document that is two works on the pages (a standard
 * and its amendment) lists both.
 */
export const SAME_WORKS = Object.freeze(
  [
    {
      document: 'ANSI S12.2:2019',
      works: [{ designation: 'ANSI/ASA S12.2-2019' }],
      reason: 'ANSI/ASA S12.2-2019 is the American National Standard the Acoustical Society publishes; the report shortens it to ANSI.',
    },
    {
      document: 'ASA WG S3-79',
      works: [{ type: 'web', url: 'https://www.sii.to/html/programs.html' }],
      reason: 'The checks name the working group that maintains ANSI S3.5; its reference program SII.C is the work the speech guide cites.',
    },
    {
      document: 'ASHRAE 2019',
      works: [{ type: 'report', organization: 'American Society of Heating, Refrigerating and Air-Conditioning Engineers', year: 2019 }],
      reason: 'The 2019 ASHRAE Handbook, HVAC Applications, is the one ASHRAE document the report cites for 2019; its Chapter 49 holds the table the check reads.',
    },
    {
      document: 'BS 5969:1981',
      works: [{ designation: 'IEC 651:1979' }],
      reason: 'BS 5969:1981 is the British Standard identical to IEC 651:1979, and the check reads Table V of IEC 651 through it.',
    },
    {
      document: 'CTE Catálogo',
      works: [{ type: 'web', url: 'https://www.codigotecnico.org/Programas/CatalogoElementosConstructivos.html' }],
      reason: 'The report shortens the catalogue of construction elements of the Código Técnico de la Edificación to CTE Catálogo.',
    },
    {
      document: 'EN 61260:1995',
      works: [{ designation: 'IEC 61260:1995' }],
      reason: 'EN 61260:1995 is the European adoption of IEC 61260:1995, word for word.',
    },
    {
      document: 'EN ISO 11654:1997',
      works: [{ designation: 'ISO 11654:1997' }],
      reason: 'EN ISO 11654:1997 is the European adoption of ISO 11654:1997, word for word.',
    },
    {
      document: 'ICAO Doc 9501',
      works: [{ designation: 'Doc 9501, 3rd ed.' }],
      reason: 'The pages cite ICAO Doc 9501, the Environmental Technical Manual, under the number ICAO gives it.',
    },
    {
      document: 'IEC 60118-4:2014+A1',
      works: [{ designation: 'IEC 60118-4:2014' }, { designation: 'IEC 60118-4:2014/AMD1:2017' }],
      reason: 'The check reads IEC 60118-4:2014 as Amendment 1 of 2017 amends it, which the pages cite as two documents.',
    },
    {
      document: 'IEC 60268-5:2003',
      works: [{ designation: 'IEC 60268-5:2003+A1:2007' }],
      reason: 'The pages cite the consolidated edition that holds the 2003 text with its Amendment 1, and the clauses the check reads are those of 2003.',
    },
    {
      document: 'IEC 61400-11:2012',
      works: [{ designation: 'IEC 61400-11:2012+AMD1:2018 CSV' }],
      reason: 'The pages cite the consolidated version that holds the 2012 edition with its Amendment 1, and the formula the check reads is that of 2012.',
    },
    {
      document: 'IEC 62489-1:2010+A1',
      works: [{ designation: 'IEC 62489-1:2010+AMD1:2014' }],
      reason: 'The report writes A1 for the Amendment 1 of 2014 the page names in full.',
    },
    {
      document: 'ISO 5135:1999',
      works: [{ designation: 'ISO 5135:1997' }],
      reason: 'The report dates ISO 5135 by BS EN ISO 5135:1999, the copy read, whose national foreword says it is identical with ISO 5135:1997.',
    },
    {
      document: 'ISO 717-1',
      works: [{ designation: 'ISO 717-1:2020' }],
      reason: 'The building checks cite ISO 717-1 without a year beside the checks of its 2020 edition, the one the building guides implement; the cabin checks cite the 2013 edition by its year.',
    },
    {
      document: 'ISO 17497-1:2004',
      works: [{ designation: 'ISO 17497-1:2004+A1:2014' }],
      reason: 'The page cites the 2004 edition with its Amendment 1 of 2014, which leaves the equation the check reads as it is.',
    },
    {
      document: 'ISO/DIS 16032:2023',
      works: [{ designation: 'E DIN EN ISO 16032:2023-05' }],
      reason: 'E DIN EN ISO 16032:2023-05 is the German edition of the draft ISO/DIS 16032:2023, and the copy the page cites.',
    },
    {
      document: 'ISO/IEC Guide 98-3',
      works: [{ designation: 'JCGM 100:2008' }],
      reason: 'ISO/IEC Guide 98-3:2008 is JCGM 100:2008, the GUM, published by ISO and IEC.',
    },
    {
      document: 'ISO/IEC Guide 98-3-1',
      works: [{ designation: 'JCGM 101:2008' }],
      reason: 'ISO/IEC Guide 98-3-1:2008 is JCGM 101:2008, the first supplement to the GUM, published by ISO and IEC.',
    },
    {
      document: 'UNESCO',
      works: [{ type: 'article', doi: '10.1121/1.381646' }],
      reason: 'The UNESCO sound-speed algorithm is the equation of Chen and Millero (1977); its canonical check value is that equation evaluated.',
    },
    {
      document: 'UNESCO/Chen-Millero',
      works: [{ type: 'article', doi: '10.1121/1.381646' }],
      reason: 'The UNESCO sound-speed equation is the one Chen and Millero published in 1977.',
    },
  ].map((entry) => Object.freeze({ ...entry, works: Object.freeze(entry.works.map((work) => Object.freeze(work))) })),
);

/**
 * Every document the checks are based on, keyed as the report writes it.
 *
 * @param {{ checks: Array<{ id: string, domain: string, reference: { documents: Array<{ kind: string, designation: string, edition?: string, relation?: string }> } }> }} report
 * @returns {Map<string, { designation: string, edition?: string, checks: Map<string, string> }>}
 *   Each document (designation and edition joined by a colon) to the checks
 *   based on it, check id to domain id. A standard only ever named in passing
 *   is left out.
 */
export function governingDocuments(report) {
  const documents = new Map();
  for (const check of report.checks) {
    if (!Array.isArray(check?.reference?.documents)) {
      throw new Error(`the conformance check ${check?.id} names no documents (reference.documents)`);
    }
    for (const document of check.reference.documents) {
      if (document.kind !== 'standard' || document.relation === IN_PASSING) continue;
      const key = document.edition ? `${document.designation}:${document.edition}` : document.designation;
      if (!documents.has(key)) {
        documents.set(key, { designation: document.designation, edition: document.edition, checks: new Map() });
      }
      documents.get(key).checks.set(check.id, check.domain);
    }
  }
  return documents;
}

/**
 * Whether a page reference is the work an entry of `SAME_WORKS` names. A
 * designation written with no year names the reference whatever year it
 * carries.
 */
function isWork(ref, work) {
  return Object.entries(work).every(([field, value]) => {
    if (field !== 'designation') return ref[field] === value;
    if (ref.designation === undefined) return false;
    const wanted = documentKey(value);
    return (/:\d{4}/.test(wanted) ? documentKey(ref.designation, ref.year) : documentKey(ref.designation)) === wanted;
  });
}

/**
 * The evidence of one language: each document the checks are based on, the
 * works it is, and what a page of that language can say of them.
 *
 * @param {object} options
 * @param {object} options.report The parsed `docs/conformance.json`.
 * @param {Iterable<{ id: string, references?: object[] }>} options.pages The
 *   content entries of one language.
 * @param {string} options.bibliographyUrl Absolute URL of that language's bibliography.
 * @param {string} options.reportPath The report page's path in that language,
 *   "/phonometry/reference/conformance/".
 * @param {readonly { document: string, works: readonly object[], reason: string }[]} [options.sameWorks]
 * @param {'en' | 'es'} [options.lang] The pages' language, which names an
 *   article's two authors with "&" or "y".
 * @param {boolean} [options.strict] False to read the report as far as it
 *   resolves, counting the checks of the documents that do and leaving out the
 *   rest, instead of failing: how a report of the past is read, to tell which
 *   commit to it changed the line a page shows (src/lib/content-dates.mjs). A
 *   page is only ever rendered from a strict join.
 * @returns {{
 *   governing: object[],
 *   verifiedBy: (references: object[] | undefined) => ({ checks: number, works: string[], domains: { id: string, title: string, checks: number, path: string }[] } | undefined),
 * }} `governing` holds one page reference per work, in the order the report
 *   first names them. `verifiedBy` gives the works by the name the line
 *   gives them (`workName`).
 * @throws {Error} Listing every document that resolves to no work or to
 *   several, and every entry of `sameWorks` that names a document no check is
 *   based on, names one a second time, picks no work, gives no reason, is not
 *   needed, leaves out the work the designations already join it to, or adds
 *   beside it a work that does not amend it.
 */
export function conformanceEvidence({ report, pages, bibliographyUrl, reportPath, sameWorks = SAME_WORKS, lang = 'en', strict = true }) {
  // Every work the pages cite once, by `@id`, with each key it answers to.
  const works = new Map();
  for (const page of pages) {
    for (const ref of page.references ?? []) {
      const id = referenceId(ref, bibliographyUrl);
      if (!works.has(id)) works.set(id, ref);
    }
  }
  // A standard answers to its designation, and a report to its number: the
  // report cites a directive the way a page cites it as a report.
  const byKey = new Map();
  for (const [id, ref] of works) {
    const key = workKey(ref);
    if (key === undefined) continue;
    for (const answer of [key, `~${undated(key)}`]) {
      if (!byKey.has(answer)) byKey.set(answer, new Set());
      byKey.get(answer).add(id);
    }
  }

  /** The works the automatic rule finds for a document, by `@id`. */
  const automatic = ({ designation, edition }) => {
    const key = documentKey(edition ? `${designation}:${edition}` : designation);
    const exact = byKey.get(key);
    if (exact) return [...exact];
    return edition ? [] : [...(byKey.get(`~${undated(key)}`) ?? [])];
  };

  const documents = governingDocuments(report);
  const problems = [];
  const resolved = new Map();
  const listed = new Map();
  for (const entry of sameWorks) {
    // A second entry for one document would replace the first without a word.
    if (listed.has(entry.document)) problems.push(`SAME_WORKS pairs ${entry.document} twice`);
    else listed.set(entry.document, entry);
    if (typeof entry.reason !== 'string' || entry.reason.trim() === '') {
      problems.push(`SAME_WORKS pairs ${entry.document} and says no reason it is the work it names`);
    }
    if (!documents.has(entry.document)) {
      problems.push(`SAME_WORKS pairs ${entry.document}, which no check is based on any more`);
    }
  }
  for (const [key, document] of documents) {
    const entry = listed.get(key);
    const found = automatic(document);
    if (entry) {
      const picked = entry.works.map((work) => [...works].filter(([, ref]) => isWork(ref, work)).map(([id]) => id));
      picked.forEach((ids, i) => {
        if (ids.length !== 1) {
          problems.push(
            `SAME_WORKS pairs ${key} with ${JSON.stringify(entry.works[i])}, which ${ids.length ? `${ids.length} works` : 'no work'} the pages cite answer${ids.length < 2 ? 's' : ''} to`,
          );
        }
      });
      const ids = picked.flat();
      if (found.length === 1 && ids.length === 1 && found[0] === ids[0]) {
        problems.push(`SAME_WORKS pairs ${key}, which the designations already join to the work it names`);
      } else if (found.length > 0 && !found.some((id) => ids.includes(id))) {
        // The designations name the document's work and the entry another:
        // its checks would move to a guide that does not implement it. A
        // pairing may add an amendment to the work found (a standard and
        // its amendment, cited as two), or pick one of several, never leave
        // every one of them out.
        const named = found.map((id) => works.get(id)?.designation ?? id).join(', ');
        problems.push(`SAME_WORKS pairs ${key} with what the pages cite as other works than ${named}, the work its designation already names`);
      } else if (found.length > 0) {
        // A work added beside the one found is an amendment of it, its key
        // the found work's key and more after a "/" or a "+"; any other
        // work would take the document's checks to a guide that implements
        // that work and not this one.
        const keys = found.map((id) => workKey(works.get(id))).filter((found) => found !== undefined);
        const amends = (id) => {
          const key = workKey(works.get(id));
          return key !== undefined && keys.some((base) => key.length > base.length && key.startsWith(base) && '/+'.includes(key[base.length]));
        };
        const named = found.map((id) => works.get(id)?.designation ?? id).join(', ');
        for (const id of ids.filter((id) => !found.includes(id) && !amends(id))) {
          const extra = works.get(id)?.designation ?? id;
          problems.push(
            `SAME_WORKS pairs ${key} with ${extra} beside ${named}, which its designation already names, and ${extra} amends none of them`,
          );
        }
      }
      resolved.set(key, ids);
    } else if (found.length !== 1) {
      problems.push(
        found.length === 0
          ? `${key}: no page cites it, and no entry of SAME_WORKS says which work it is`
          : `${key}: ${found.length} works answer to it (${found.map((id) => id.slice(id.indexOf('#'))).join(', ')})`,
      );
    } else {
      resolved.set(key, found);
    }
  }
  if (problems.length > 0 && strict) {
    throw new Error(
      `the conformance report is based on standards the pages under ${bibliographyUrl} do not resolve, in ` +
        `${problems.length} place(s); cite each where it belongs, or say in SAME_WORKS ` +
        `(src/lib/conformance-evidence.mjs) which cited work it is:\n  ${problems.join('\n  ')}`,
    );
  }

  const governing = [];
  const named = new Set();
  for (const ids of resolved.values()) {
    for (const id of ids) {
      if (named.has(id)) continue;
      named.add(id);
      governing.push(works.get(id));
    }
  }

  /** `@id` to the checks based on it, check id to domain id. */
  const checksOf = new Map();
  for (const [key, ids] of resolved) {
    for (const id of ids) {
      if (!checksOf.has(id)) checksOf.set(id, new Map());
      for (const [check, domain] of documents.get(key).checks) checksOf.get(id).set(check, domain);
    }
  }
  const order = report.domains.map((domain) => domain.id);
  const titles = new Map(report.domains.map((domain) => [domain.id, domain.title]));

  return {
    governing,
    verifiedBy(references) {
      const checks = new Map();
      const named = [];
      for (const ref of references ?? []) {
        // A work the page reads and does not implement verifies nothing on
        // it; whatever else it cites is counted by what the join made of it.
        if (ref.implemented === false) continue;
        const based = checksOf.get(referenceId(ref, bibliographyUrl));
        if (!based) continue;
        const name = workName(ref, lang);
        if (!named.includes(name)) named.push(name);
        for (const [check, domain] of based) checks.set(check, domain);
      }
      if (checks.size === 0) return undefined;
      const perDomain = new Map();
      for (const domain of checks.values()) perDomain.set(domain, (perDomain.get(domain) ?? 0) + 1);
      return {
        checks: checks.size,
        works: named,
        domains: [...perDomain]
          .sort(([a], [b]) => order.indexOf(a) - order.indexOf(b))
          .map(([id, count]) => ({ id, title: titles.get(id) ?? id, checks: count, path: `${reportPath}#${id}` })),
      };
    },
  };
}

/** One reading per language and build: every page renders the line, and the join is the same for all of them. */
const built = new Map();

/**
 * `conformanceEvidence` for the build, read once per language.
 *
 * @param {string} lang
 * @param {() => Promise<Parameters<typeof conformanceEvidence>[0]>} options
 *   Called the first time the language is asked for, so the pages are read
 *   once and not once per page.
 * @returns {Promise<ReturnType<typeof conformanceEvidence>>} The same promise
 *   for every caller of a language; it rejects for all of them when the join
 *   does, which stops the build.
 */
export function evidenceOnce(lang, options) {
  if (!built.has(lang)) built.set(lang, Promise.resolve().then(options).then(conformanceEvidence));
  return built.get(lang);
}
