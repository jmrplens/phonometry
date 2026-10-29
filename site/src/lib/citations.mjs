/**
 * The page bibliography, as linked structured data.
 *
 * Every guide already declares a typed `references` list in its frontmatter,
 * and the site renders it as an APA-7 section and as the header chips. None of
 * it reached the structured data, which is a strange gap for a library whose
 * whole claim is that each metric comes from the text of a named standard: the
 * machine-readable layer said "a technical article by one author" and nothing
 * about the 129 designations the corpus implements.
 *
 * The design point that makes this a graph rather than a few hundred loose
 * blobs: each work gets a stable `@id` minted from its designation and hung off
 * `/reference/bibliography/`, which is where the site already aggregates them.
 * The bibliography page emits the full node, so "IEC 61672-1:2013" is one
 * entity cited by many pages rather than many identical strings.
 *
 * Every other page names each work it cites once, at its first reference, with
 * a short typed node: what it is, its title, its designation or DOI and its
 * address. A page used to carry the `@id` alone, and a reader of that one page
 * (a search engine's snippet, an assistant handed the page) saw a list of
 * addresses with nothing at them, because the names live on another page it
 * never fetched.
 */

/** Slugify a designation or title into an `@id` fragment. */
function slug(value) {
  return String(value)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

/**
 * Stable fragment identifier for one reference entry.
 *
 * Standards key on their designation, which names one edition of one document
 * ("IEC 61672-1:2013"). A work with a DOI keys on the DOI, which is what names
 * it everywhere else. Anything else keys on type, first author or
 * organization, year and title.
 *
 * The author and year alone, which an APA short cite uses, are not a key: one
 * author publishes two papers in a year, and one organization issues several
 * reports. Keyed that way, two papers by Jiménez in 2017 were one `@id`, and
 * three ECAC reports of 2026 were another. A report number does not separate
 * them either: two volumes of ECAC Doc 29 carry the same one, and the Spanish
 * pages translate it ("5.ª ed."), which would part the two languages' `@id`s.
 * A DOI and a title are written the same in both.
 */
export function referenceId(ref, bibliographyUrl) {
  if (ref.type === 'standard') return `${bibliographyUrl}#std-${slug(ref.designation)}`;
  if (ref.doi) return `${bibliographyUrl}#doi-${slug(ref.doi)}`;
  return `${bibliographyUrl}#${withoutDoi(ref)}`;
}

/** The fragment a work that is not a standard takes when it carries no DOI. */
function withoutDoi(ref) {
  const who = ref.authors?.[0] ?? ref.organization;
  const parts = [ref.type, ...(who ? [String(who).split(',')[0]] : []), ref.year ?? 'nd', ref.title];
  return parts.map(slug).join('-');
}

/**
 * Fields of a reference that are about the page citing the work, not the
 * work: what it anchors there, whether the page marks it, whether the page
 * implements it.
 */
const PAGE_FIELDS = new Set(['note', 'primary', 'implemented']);

/**
 * Every work one language's pages cite, once each, by `@id`.
 *
 * A page describes each work it cites in its own frontmatter, and many pages
 * cite the same work. The bibliography page used to keep the first
 * description it read while every other page named the work by its own, so
 * one standard had two catalogue addresses on two pages and one book a DOI on
 * fifteen pages and none on two. This refuses that: every reference to one
 * `@id` says the same of the work, field for field, so the short node a page
 * names a work with (`referenceStub`) is the bibliography's whichever page it
 * is read on. The `note`, `primary` and `implemented` fields are the page's
 * and may differ.
 *
 * It refuses two `@id`s for one DOI as well, and the case that makes them: a
 * work given its DOI on one page and not on another, which keys on the DOI
 * there and on its title here, and so would never be compared above.
 *
 * @param {Iterable<{id: string, references?: object[]}>} pages The content
 *   entries of one language.
 * @param {string} bibliographyUrl Absolute URL of that language's bibliography.
 * @returns {Map<string, object>} Each `@id` to the first reference to it, the
 *   one whose `note` the bibliography prints.
 * @throws {Error} Listing every `@id` described two ways, every DOI under two
 *   `@id`s and every work cited with its DOI on one page and without it on
 *   another.
 */
export function citedWorks(pages, bibliographyUrl) {
  const works = new Map();
  const doiIds = new Map();
  const doiOf = new Map();
  const withoutDoiOn = [];
  for (const page of pages) {
    for (const ref of page.references ?? []) {
      const id = referenceId(ref, bibliographyUrl);
      if (!works.has(id)) works.set(id, []);
      works.get(id).push({ page: page.id, ref });
      if (ref.doi) {
        const key = ref.doi.toLowerCase();
        if (!doiIds.has(key)) doiIds.set(key, new Set());
        doiIds.get(key).add(id);
      }
      if (ref.type === 'standard') continue;
      if (ref.doi) doiOf.set(withoutDoi(ref), ref.doi);
      else withoutDoiOn.push({ page: page.id, ref });
    }
  }

  const problems = [];
  const at = (id) => id.slice(bibliographyUrl.length);
  const listed = (on) => `${on.slice(0, 2).join(', ')}${on.length > 2 ? ` and ${on.length - 2} more` : ''}`;
  for (const [id, citing] of works) {
    const fields = new Set(citing.flatMap(({ ref }) => Object.keys(ref)));
    for (const field of [...fields].filter((key) => !PAGE_FIELDS.has(key)).sort()) {
      const pagesBy = new Map();
      for (const { page, ref } of citing) {
        const value = ref[field] === undefined ? '(none)' : JSON.stringify(ref[field]);
        if (!pagesBy.has(value)) pagesBy.set(value, []);
        pagesBy.get(value).push(page);
      }
      if (pagesBy.size < 2) continue;
      problems.push(`${at(id)} ${field}: ${[...pagesBy].map(([value, on]) => `${value} on ${listed(on)}`).join('; ')}`);
    }
  }
  for (const [doi, ids] of doiIds) {
    if (ids.size > 1) problems.push(`DOI ${doi} names ${ids.size} works: ${[...ids].map(at).join(', ')}`);
  }
  for (const { page, ref } of withoutDoiOn) {
    const doi = doiOf.get(withoutDoi(ref));
    if (doi) problems.push(`#${withoutDoi(ref)} doi: (none) on ${page}; ${JSON.stringify(doi)} elsewhere`);
  }
  if (problems.length > 0) {
    throw new Error(
      `the pages' references describe works cited under ${bibliographyUrl} two ways, in ` +
        `${problems.length} place(s); write each work the same on every page that cites it:\n  ` +
        problems.join('\n  '),
    );
  }
  return new Map([...works].map(([id, [first]]) => [id, first.ref]));
}

/**
 * The bodies that issue the standards the guides cite, one identity each.
 *
 * A standard's publisher used to be an anonymous Organization written out
 * again in every node that named it, 146 times for ISO on the English
 * bibliography alone and as many again on the Spanish one, and nothing in the
 * graph said those were one body or where it lives. Each body now has one
 * `@id`, `#org-<id>` on the English bibliography whichever language names it,
 * with its official site.
 *
 * `spelled` lists the names a standard's frontmatter gives its publisher, or
 * its issuing organization when no separate publisher is named
 * (src/content.config.ts); it defaults to `name`. A standard whose body is
 * missing here keeps an anonymous publisher, and check:structured-data fails
 * on it, so a new body is added here rather than left without an identity.
 *
 * The three Spanish state issuers carry no `url`. They are the authorities the
 * Boletín Oficial del Estado prints on those texts, the two ministries have
 * been renamed since, and none of them publishes the texts: the BOE does, and
 * each of those references links its BOE record.
 */
const STANDARDS_BODIES = [
  { id: 'iso', name: 'International Organization for Standardization', alternateName: 'ISO', url: 'https://www.iso.org/' },
  { id: 'iec', name: 'International Electrotechnical Commission', alternateName: 'IEC', url: 'https://www.iec.ch/' },
  { id: 'cen', name: 'European Committee for Standardization', alternateName: 'CEN', url: 'https://www.cencenelec.eu/' },
  { id: 'din', name: 'Deutsches Institut für Normung', alternateName: 'DIN', url: 'https://www.din.de/' },
  { id: 'bsi', name: 'British Standards Institution', alternateName: 'BSI', url: 'https://www.bsigroup.com/' },
  { id: 'ansi', name: 'American National Standards Institute', alternateName: 'ANSI', url: 'https://www.ansi.org/' },
  { id: 'asa', name: 'Acoustical Society of America', alternateName: 'ASA', url: 'https://acousticalsociety.org/' },
  { id: 'astm', name: 'ASTM International', url: 'https://www.astm.org/' },
  { id: 'jsa', name: 'Japanese Standards Association', alternateName: 'JSA', url: 'https://www.jsa.or.jp/' },
  { id: 'itu', name: 'International Telecommunication Union', alternateName: 'ITU', url: 'https://www.itu.int/' },
  { id: 'ebu', name: 'European Broadcasting Union', alternateName: 'EBU', url: 'https://www.ebu.ch/' },
  { id: 'aes', name: 'Audio Engineering Society', alternateName: 'AES', url: 'https://www.aes.org/' },
  { id: 'ecma', name: 'Ecma International', url: 'https://ecma-international.org/' },
  { id: 'ietf', name: 'Internet Engineering Task Force', alternateName: 'IETF', url: 'https://www.ietf.org/' },
  { id: 'sae', name: 'SAE International', url: 'https://www.sae.org/' },
  { id: 'icao', name: 'International Civil Aviation Organization', alternateName: 'ICAO', url: 'https://www.icao.int/' },
  { id: 'vdi', name: 'Verein Deutscher Ingenieure', alternateName: 'VDI', url: 'https://www.vdi.de/' },
  { id: 'une', name: 'Asociación Española de Normalización', alternateName: 'UNE', url: 'https://www.une.org/' },
  {
    id: 'ahri',
    name: 'Air-Conditioning, Heating, and Refrigeration Institute',
    alternateName: 'AHRI',
    url: 'https://www.ahrinet.org/',
    spelled: ['Air-Conditioning, Heating and Refrigeration Institute'],
  },
  { id: 'nordtest', name: 'Nordtest', url: 'https://www.nordtest.info/' },
  {
    id: 'bipm',
    name: 'Bureau International des Poids et Mesures',
    alternateName: 'BIPM',
    url: 'https://www.bipm.org/',
    spelled: ['BIPM'],
  },
  { id: 'eu', name: 'European Union', alternateName: 'EU', url: 'https://european-union.europa.eu/' },
  {
    id: 'es-ministerio-de-la-presidencia',
    name: 'Ministerio de la Presidencia',
    spelled: ['Ministerio de la Presidencia (Spain)', 'Ministerio de la Presidencia (España)'],
  },
  {
    id: 'es-ministerio-de-fomento',
    name: 'Ministerio de Fomento',
    spelled: ['Ministerio de Fomento (Spain)', 'Ministerio de Fomento (España)'],
  },
  {
    id: 'es-jefatura-del-estado',
    name: 'Jefatura del Estado',
    spelled: ['Jefatura del Estado (Spain)', 'Jefatura del Estado (España)'],
  },
];

/** Each body under every name the frontmatter spells it with. */
const BODY_BY_NAME = new Map(
  STANDARDS_BODIES.flatMap((body) => (body.spelled ?? [body.name]).map((name) => [name, body])),
);

/**
 * The Organization node of the body that issues a standard, or undefined when
 * the reference is not a standard or its body has no identity yet.
 *
 * @param {object} ref A frontmatter reference.
 * @param {string} bodiesUrl Absolute URL of the English bibliography page,
 *   where the bodies are defined once for both languages.
 */
export function standardsBody(ref, bodiesUrl) {
  if (ref.type !== 'standard') return undefined;
  const body = BODY_BY_NAME.get(ref.publisher ?? ref.organization);
  if (!body) return undefined;
  return {
    '@type': 'Organization',
    '@id': `${bodiesUrl}#org-${body.id}`,
    name: body.name,
    ...(body.alternateName ? { alternateName: body.alternateName } : {}),
    ...(body.url ? { url: body.url } : {}),
  };
}

/** APA-formatted author strings to schema.org Person nodes. */
function people(authors) {
  return (authors ?? []).map((name) => ({ '@type': 'Person', name }));
}

/** Join `sameAs` values into the shape schema.org takes: one string, or a list. */
function sameAs(...values) {
  const all = [...new Set(values.flat().filter(Boolean))];
  if (all.length === 0) return {};
  return { sameAs: all.length === 1 ? all[0] : all };
}

/**
 * What a journal article is part of: its issue, inside its volume, inside the
 * journal, as far as the reference names them.
 *
 * schema.org defines `volumeNumber` on PublicationVolume and `issueNumber` on
 * PublicationIssue, not on the article, and a consumer that reads the
 * vocabulary drops them anywhere else (site/scripts/check-schema-vocabulary.mjs
 * fails on it). So the article names the innermost of the three it can, and
 * each names the next through its own `isPartOf`.
 */
function container(ref) {
  let part = { '@type': 'Periodical', name: ref.journal };
  if (ref.volume) {
    part = { '@type': 'PublicationVolume', volumeNumber: String(ref.volume), isPartOf: part };
  }
  if (ref.issue) {
    part = { '@type': 'PublicationIssue', issueNumber: String(ref.issue), isPartOf: part };
  }
  return part;
}

/**
 * Full schema.org node for one reference.
 *
 * There is no schema.org type for a technical standard. `CreativeWork` with an
 * `identifier`, a publisher `Organization` and `genre: "Technical standard"`
 * is the modelling the standards bodies use on their own catalogue pages, so
 * that is what is emitted here.
 *
 * @param {object} ref A frontmatter reference.
 * @param {string} bibliographyUrl Absolute URL of this language's bibliography.
 * @param {object} [options]
 * @param {string} [options.bodiesUrl] Absolute URL of the English bibliography,
 *   where the standards bodies are defined; defaults to `bibliographyUrl`.
 * @param {Iterable<string>} [options.translationOf] The `@id`s of the same work
 *   on the English bibliography, for a node on the Spanish one.
 */
export function referenceNode(ref, bibliographyUrl, { bodiesUrl = bibliographyUrl, translationOf = [] } = {}) {
  const id = referenceId(ref, bibliographyUrl);
  const doiUrl = ref.doi ? `https://doi.org/${ref.doi}` : undefined;
  const common = {
    '@id': id,
    name: ref.title,
    ...(ref.year ? { datePublished: String(ref.year) } : {}),
    ...(ref.url ? { url: ref.url } : {}),
    ...(ref.doi
      ? { identifier: { '@type': 'PropertyValue', propertyID: 'DOI', value: ref.doi } }
      : {}),
    ...sameAs(doiUrl, [...translationOf]),
    ...(ref.note ? { description: ref.note } : {}),
  };

  switch (ref.type) {
    case 'standard': {
      const body = standardsBody(ref, bodiesUrl);
      return {
        ...common,
        '@type': 'CreativeWork',
        alternateName: ref.designation,
        // The DOI branch above would otherwise win; a standard's designation is
        // the identifier that matters, and standards rarely carry a DOI.
        identifier: ref.designation,
        genre: 'Technical standard',
        publisher: body
          ? { '@id': body['@id'] }
          : { '@type': 'Organization', name: ref.publisher ?? ref.organization },
      };
    }
    case 'book':
      return {
        ...common,
        '@type': 'Book',
        author: people(ref.authors),
        ...(ref.edition ? { bookEdition: ref.edition } : {}),
        publisher: { '@type': 'Organization', name: ref.publisher },
      };
    case 'article':
      return {
        ...common,
        '@type': 'ScholarlyArticle',
        author: people(ref.authors),
        isPartOf: container(ref),
        ...(ref.pages ? { pagination: ref.pages } : {}),
      };
    case 'report':
      return {
        ...common,
        '@type': 'Report',
        ...(ref.authors ? { author: people(ref.authors) } : {}),
        ...(ref.number ? { reportNumber: ref.number } : {}),
        publisher: {
          '@type': 'Organization',
          name: ref.institution ?? ref.organization,
        },
      };
    default:
      return {
        ...common,
        '@type': 'WebPage',
        ...(ref.authors ? { author: people(ref.authors) } : {}),
        ...(ref.organization ? { publisher: { '@type': 'Organization', name: ref.organization } } : {}),
      };
  }
}

/**
 * What a page says of a work at its first reference: enough to name it on that
 * page alone.
 *
 * The fields are picked from the full node of the page's own reference rather
 * than rebuilt, so the stub and that node agree. The bibliography builds its
 * node from another page's reference to the same work, and the two agree
 * because `citedWorks` fails the build when two references to one `@id`
 * differ; check:structured-data compares every named stub with the
 * bibliography's node on the built pages. A JSON-LD processor that reads both
 * the page and the bibliography merges them into one node.
 */
const STUB_FIELDS = ['@id', '@type', 'name', 'identifier', 'reportNumber', 'url', 'sameAs'];

/** The short node a page names a work with at its first reference. */
export function referenceStub(ref, bibliographyUrl) {
  const full = referenceNode(ref, bibliographyUrl);
  return Object.fromEntries(STUB_FIELDS.filter((key) => full[key] !== undefined).map((key) => [key, full[key]]));
}

/** The numbers of a designation, in order: what a translation leaves alone. */
const numbersOf = (designation) => (String(designation).match(/\d+/g) ?? []).join(' ');

/**
 * The English `@id`s of every standard the Spanish pages cite.
 *
 * A Spanish standard is the same work as its English one, and its node says so
 * with `sameAs`. The two `@id`s usually differ only by the locale, but some
 * designations are translated with the page: an edition note ("ECMA-418-2,
 * 4.ª ed." against "ECMA-418-2, 4th ed."), "Recomendación UIT-R",
 * "texto consolidado", "retirada", and the slugs differ too. A Spanish page
 * cites the works of its English twin in the same order, so each standard is
 * paired with the one at its position on the twin, and the pair counts only
 * when both designations carry the same numbers in the same order, which a
 * translation keeps and a list that fell out of step does not. A standard with
 * the same designation on any English page is that work as well.
 *
 * @param {Iterable<{id: string, references?: object[]}>} pages Every content
 *   entry, both languages; a Spanish entry's id starts with `es/`.
 * @param {string} spanishBibliographyUrl Absolute URL of the Spanish bibliography.
 * @param {string} englishBibliographyUrl Absolute URL of the English bibliography.
 * @returns {Map<string, Set<string>>} Spanish `@id` to the English `@id`s.
 */
export function englishStandardIds(pages, spanishBibliographyUrl, englishBibliographyUrl) {
  const english = new Map();
  for (const page of pages) {
    if (page.id === 'es' || page.id.startsWith('es/')) continue;
    english.set(page.id, page.references ?? []);
  }
  const defined = new Set(
    [...english.values()]
      .flat()
      .filter((ref) => ref.type === 'standard')
      .map((ref) => referenceId(ref, englishBibliographyUrl)),
  );

  const twins = new Map();
  const pair = (spanishId, englishId) => {
    if (!twins.has(spanishId)) twins.set(spanishId, new Set());
    twins.get(spanishId).add(englishId);
  };
  for (const page of pages) {
    if (!page.id.startsWith('es/')) continue;
    const twin = english.get(page.id.slice('es/'.length)) ?? [];
    for (const [i, ref] of (page.references ?? []).entries()) {
      if (ref.type !== 'standard') continue;
      const spanishId = referenceId(ref, spanishBibliographyUrl);
      const sameDesignation = referenceId(ref, englishBibliographyUrl);
      if (defined.has(sameDesignation)) pair(spanishId, sameDesignation);
      const other = twin[i];
      if (other?.type === 'standard' && numbersOf(other.designation) === numbersOf(ref.designation)) {
        pair(spanishId, referenceId(other, englishBibliographyUrl));
      }
    }
  }
  return twins;
}

/**
 * The citation properties for one page.
 *
 * The three are deliberately different claims, and the frontmatter already
 * carries the flags that separate them:
 *   - `isBasedOn`  the standards the page actually implements (the `primary`
 *                  entries), stated as provenance.
 *   - `citation`   the full bibliography, primary or not, implemented or not.
 *   - `about`      what the page is about: the software plus the same primary
 *                  standards. Returned as `governingWorks`, for the caller to
 *                  put beside the software.
 *
 * An entry marked `implemented: false` is a document the page cites without
 * being written to it, so it is only ever a `citation`.
 *
 * Each work is named at its first reference and pointed at by `@id` after, so
 * a page with a long bibliography does not repeat it. The properties come back
 * in the order a page should print them, `isBasedOn` first: that is where a
 * reader looks for what the page is based on, so that is where the names are.
 *
 * @param {object} options
 * @param {Array | undefined} options.references Frontmatter `references`, possibly undefined.
 * @param {string} options.bibliographyUrl Absolute URL of the bibliography page.
 * @returns {{ isBasedOn?: object[], citation?: object[], governingWorks?: object[] }}
 */
export function citationsFor({ references, bibliographyUrl }) {
  const refs = references ?? [];
  if (refs.length === 0) return {};

  const named = new Set();
  const node = (ref) => {
    const id = referenceId(ref, bibliographyUrl);
    if (named.has(id)) return { '@id': id };
    named.add(id);
    return referenceStub(ref, bibliographyUrl);
  };

  const primary = refs.filter((ref) => ref.primary);
  // A page that marks nothing still has a governing source; fall back to the
  // first standards it lists among those it implements.
  const governing = primary.length
    ? primary
    : refs.filter((ref) => ref.type === 'standard' && ref.implemented !== false).slice(0, 3);

  // Built in this order on purpose: whichever property names a work first
  // carries its name, and the governing works are named in `isBasedOn`.
  const isBasedOn = governing.map(node);
  const citation = refs.map(node);
  return {
    ...(governing.length ? { isBasedOn } : {}),
    citation,
    ...(governing.length
      ? { governingWorks: governing.map((ref) => ({ '@id': referenceId(ref, bibliographyUrl) })) }
      : {}),
  };
}
