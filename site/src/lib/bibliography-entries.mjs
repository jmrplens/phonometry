/**
 * The entries of the bibliography page, in both languages, from the
 * references every page declares.
 *
 * The bibliography's structured data has described every work a page cites
 * since it was first built (src/lib/citations.mjs, `citedWorks`), but the list
 * a reader sees was written by hand, and it fell behind the pages: 213 entries
 * against 440 cited works, so more than half of what the guides cite had no
 * entry, and a work's "Cited by" list named the pages that cited it when the
 * entry was written and none of the ones that came after (Bendat and Piersol
 * was cited by ten pages and listed four). Nothing could hold a hand list to the
 * pages, because nothing read both.
 *
 * So the list is no longer written. Its entries are the works `citedWorks`
 * returns for the language, the same set the structured data describes; each
 * entry's citation is the one a References section prints
 * (scripts/shared/page-twin.mjs, `citationMarkdown`), and its "Cited by" list is
 * every page whose references name the work's `@id`. What is still written by
 * hand is what no frontmatter says: why a work matters, in a note, and the
 * section of the page it sits in. That is data keyed by the work
 * (src/data/bibliography.mjs), and a work with no note of its own still gets
 * its entry, in the section its citing pages point to.
 *
 * The page itself (`reference/bibliography.md` in each language) keeps its
 * prose and its headings, so the anchors other pages link to and the table of
 * contents stay where they were, and marks where each section's list goes
 * with a comment, `<!-- bibliography: signal-analysis -->`. The remark plugin
 * of src/lib/remark-bibliography.mjs puts the list there when the site is
 * built, and the Markdown copy of the Spanish page and the docs/ mirror write
 * the same lists from the same functions.
 *
 * Nothing here starts a process or reads a file; the caller hands in the
 * pages.
 */
import { citationMarkdown, literalText } from '../../scripts/shared/page-twin.mjs';
import { BIBLIOGRAPHY_PREFIXES, BIBLIOGRAPHY_SECTIONS, BIBLIOGRAPHY_WORKS } from '../data/bibliography.mjs';
import { basePath, siteUrl } from '../data/site.mjs';
import { topics } from '../data/topics.mjs';
import { citedWorks, englishStandardIds, referenceId } from './citations.mjs';
import { codeLines } from './markdown-fences.mjs';
import { sortedReferences } from './references-format.mjs';

/**
 * The comment that marks where a section's list goes on the page, on a line
 * of its own: `<!-- bibliography: signal-analysis -->`. Only blanks and tabs
 * may sit inside it, never a line end: the remark plugin reads the comment as
 * one HTML node and the Markdown writers read the page a line at a time, and
 * a marker either of them took that the other left would fill a list on the
 * page and drop it from the copy.
 */
export const MARKER = /^<!--[ \t]*bibliography:[ \t]*([a-z0-9]+(?:-[a-z0-9]+)*)[ \t]*-->$/;

/** Whether a content entry id is a Spanish page's. */
const isSpanish = (id) => id === 'es' || id.startsWith('es/');

/** The fragment of an `@id` on a bibliography, `std-iso-354-2003`. */
const fragmentOf = (id) => id.slice(id.indexOf('#') + 1);

/**
 * Whether two references, one a translation of the other, describe one work
 * by what a translation leaves as it is: the first author, or the
 * organization when there is none, the year, and the DOI and the address
 * whenever either side gives one. A title is translated and says nothing.
 *
 * @param {object} a
 * @param {object} b
 * @returns {boolean}
 */
function sameWork(a, b) {
  const first = (ref) => String(ref.authors?.[0] ?? ref.organization ?? ref.editors?.[0] ?? '').trim();
  const same = (x, y) => String(x ?? '').trim().toLowerCase() === String(y ?? '').trim().toLowerCase();
  return first(a) === first(b) && same(a.year, b.year) && same(a.doi, b.doi) && same(a.url, b.url);
}

/**
 * The English `@id` of every work the Spanish pages cite, where it has one.
 *
 * Most works keep their fragment in both languages: a DOI and a title are
 * written the same way in each. A standard whose designation the Spanish page
 * translates ("Recomendación UIT-R BS.468-4") is paired the way the Spanish
 * bibliography's `sameAs` pairs it (`englishStandardIds`), and a report or a
 * book whose title the Spanish page translates ("edición SI, capítulo 49") by
 * the reference at its position on the English twin, when the two are of one
 * type and name the same author, year, DOI and address (`sameWork`): two
 * references swapped on the twin would otherwise each pair with the other's
 * work.
 *
 * @param {Iterable<{id: string, references?: object[]}>} pages Every content
 *   entry, both languages.
 * @param {string} spanishUrl Absolute URL of the Spanish bibliography.
 * @param {string} englishUrl Absolute URL of the English bibliography.
 * @returns {Map<string, string>} Spanish `@id` to English `@id`.
 * @throws {Error} When a Spanish work pairs with two English works, or two
 *   Spanish works with one English work: one side of the pair then describes
 *   one work two ways. And when a translated work stands where its English
 *   twin cites a work of another author, year, DOI or address.
 */
export function englishWorkIds(pages, spanishUrl, englishUrl) {
  const all = [...pages];
  const english = new Map(all.filter((page) => !isSpanish(page.id)).map((page) => [page.id, page.references ?? []]));
  const defined = new Set([...english.values()].flat().map((ref) => fragmentOf(referenceId(ref, englishUrl))));
  const standards = englishStandardIds(all, spanishUrl, englishUrl);
  const problems = [];
  const candidates = new Map();
  const pair = (spanishId, englishId) => {
    if (!candidates.has(spanishId)) candidates.set(spanishId, new Set());
    candidates.get(spanishId).add(englishId);
  };
  for (const page of all) {
    if (!isSpanish(page.id)) continue;
    const twin = english.get(page.id.slice('es/'.length)) ?? [];
    for (const [i, ref] of (page.references ?? []).entries()) {
      const spanishId = referenceId(ref, spanishUrl);
      if (ref.type === 'standard') {
        for (const englishId of standards.get(spanishId) ?? []) pair(spanishId, englishId);
        continue;
      }
      const fragment = fragmentOf(spanishId);
      if (defined.has(fragment)) pair(spanishId, `${englishUrl}#${fragment}`);
      else if (twin[i]?.type === ref.type) {
        const englishId = referenceId(twin[i], englishUrl);
        if (sameWork(ref, twin[i])) pair(spanishId, englishId);
        else {
          problems.push(
            `${fragmentOf(spanishId)} stands where the English twin cites ${fragmentOf(englishId)}, ` +
              `and the two name another author, year, DOI or address`,
          );
        }
      }
    }
  }
  const pairs = new Map();
  const byEnglish = new Map();
  for (const [spanishId, englishIds] of candidates) {
    if (englishIds.size > 1) {
      problems.push(`${fragmentOf(spanishId)} pairs with ${[...englishIds].map(fragmentOf).join(' and ')}`);
      continue;
    }
    const [englishId] = englishIds;
    pairs.set(spanishId, englishId);
    if (!byEnglish.has(englishId)) byEnglish.set(englishId, []);
    byEnglish.get(englishId).push(spanishId);
  }
  for (const [englishId, spanishIds] of byEnglish) {
    if (spanishIds.length > 1) {
      problems.push(`${spanishIds.map(fragmentOf).join(' and ')} are both ${fragmentOf(englishId)}`);
    }
  }
  if (problems.length > 0) {
    throw new Error(
      `the Spanish pages cite works that do not pair with one English work each, in ${problems.length} place(s); ` +
        `write each work the same on every Spanish page, at the place its English twin cites it:\n  ${problems.join('\n  ')}`,
    );
  }
  return pairs;
}

/**
 * The section a work with no section of its own sits in: the one most of the
 * pages that cite it belong to, by the longest prefix of each page's route in
 * `prefixes`, the earlier section of `sections` on a tie, and the first
 * section when no citing page belongs to one.
 */
function derivedSection(citing, prefixes, sections) {
  const votes = new Map();
  for (const page of citing) {
    const route = page.replace(/^es\//, '');
    const match = prefixes
      .filter(([prefix]) => route === prefix || route.startsWith(`${prefix}/`))
      .sort((a, b) => b[0].length - a[0].length)[0];
    if (match) votes.set(match[1], (votes.get(match[1]) ?? 0) + 1);
  }
  const ranked = sections
    .map((section, index) => ({ key: section.key, index, votes: votes.get(section.key) ?? 0 }))
    .sort((a, b) => b.votes - a.votes || a.index - b.index);
  return ranked[0].votes > 0 ? ranked[0].key : sections[0].key;
}

/**
 * Every section of one language's bibliography with its entries: each work
 * that language's pages cite, once, with the pages that cite it.
 *
 * @param {readonly {id: string, title?: string, references?: object[]}[]} pages
 *   Every content entry, both languages: the Spanish page pairs its works with
 *   the English ones the data is keyed by.
 * @param {object} options
 * @param {'en' | 'es'} options.lang
 * @param {string} options.bibliographyUrl Absolute URL of that language's bibliography.
 * @param {string} options.englishUrl Absolute URL of the English bibliography.
 * @param {readonly {key: string}[]} options.sections The page's sections, in order.
 * @param {readonly (readonly [string, string])[]} options.prefixes Route prefix to
 *   section key: where a work with no section of its own goes.
 * @param {Readonly<Record<string, {section?: string, note?: {en?: string, es?: string}}>>} options.works
 *   What is written by hand of each work, by its fragment on the English bibliography.
 * @param {readonly string[]} options.navigation Every page route in the order the
 *   sidebar lists them; a "Cited by" list follows it.
 * @param {string} options.base The site's base path, `/phonometry`.
 * @returns {{key: string, entries: {id: string, fragment: string, ref: object, note?: string,
 *   citedBy: {id: string, title: string, href: string}[]}[]}[]}
 * @throws {Error} Listing every work the data describes that no page of the
 *   language cites, every section the data names that the page does not have,
 *   and every page that cites a work without a title to name it by.
 */
export function bibliographySections(
  pages,
  { lang, bibliographyUrl, englishUrl, sections, prefixes, works, navigation, base },
) {
  const own = pages.filter((page) => isSpanish(page.id) === (lang === 'es'));
  const described = citedWorks(own, bibliographyUrl);
  const toEnglish = lang === 'es' ? englishWorkIds(pages, bibliographyUrl, englishUrl) : null;
  const keyOf = (id) => fragmentOf(toEnglish ? (toEnglish.get(id) ?? id) : id);

  const citing = new Map();
  for (const page of own) {
    for (const ref of page.references ?? []) {
      const id = referenceId(ref, bibliographyUrl);
      if (!citing.has(id)) citing.set(id, []);
      if (!citing.get(id).includes(page)) citing.get(id).push(page);
    }
  }

  const problems = [];
  const sectionKeys = new Set(sections.map((section) => section.key));
  const keys = new Set([...described.keys()].map(keyOf));
  for (const [key, record] of Object.entries(works)) {
    if (!keys.has(key)) {
      const which = lang === 'es' ? 'Spanish' : 'English';
      problems.push(`src/data/bibliography.mjs describes ${key}, which no ${which} page cites`);
    }
    if (record.section !== undefined && !sectionKeys.has(record.section)) {
      problems.push(`src/data/bibliography.mjs puts ${key} in a section the page does not have, ${record.section}`);
    }
  }

  const order = new Map(navigation.map((route, index) => [route, index]));
  const rank = (page) => order.get(page.id.replace(/^es\//, '')) ?? navigation.length;
  const entriesBy = new Map(sections.map((section) => [section.key, []]));
  for (const [id, ref] of described) {
    const key = keyOf(id);
    const record = works[key] ?? {};
    const pagesCiting = [...citing.get(id)].sort((a, b) => rank(a) - rank(b) || a.id.localeCompare(b.id));
    for (const page of pagesCiting) {
      if (!page.title) problems.push(`${page.id} cites ${fragmentOf(id)} and has no title to name it by`);
    }
    const section = sectionKeys.has(record.section)
      ? record.section
      : derivedSection(pagesCiting.map((page) => page.id), prefixes, sections);
    entriesBy.get(section).push({
      id,
      fragment: fragmentOf(id),
      ref,
      note: record.note?.[lang],
      citedBy: pagesCiting.map((page) => ({ id: page.id, title: page.title, href: `${base}/${page.id}/` })),
    });
  }
  if (problems.length > 0) {
    throw new Error(`the bibliography in ${lang === 'es' ? 'Spanish' : 'English'} cannot be written:\n  ${problems.join('\n  ')}`);
  }
  return sections.map((section) => {
    const entries = entriesBy.get(section.key);
    const sorted = sortedReferences(
      entries.map((entry) => entry.ref),
      lang,
    ).map(([index]) => entries[index]);
    return { key: section.key, entries: sorted };
  });
}

/**
 * Every section of the site's bibliography in `lang`, from `pages`, with the
 * site's own sections, prefixes and records (src/data/bibliography.mjs) unless
 * a test hands in its own. The build's plugin, the Markdown copies and the
 * page's structured data all read the page through this, so each writes the
 * same lists.
 *
 * @param {readonly {id: string, title?: string, references?: object[]}[]} pages
 *   Every content entry, both languages.
 * @param {'en' | 'es'} lang
 * @param {{sections?: readonly {key: string}[], prefixes?: readonly (readonly [string, string])[],
 *   works?: Readonly<Record<string, object>>}} [data]
 */
export function siteBibliography(pages, lang, data = {}) {
  return bibliographySections(pages, {
    lang,
    bibliographyUrl: `${siteUrl}${basePath}${lang === 'es' ? '/es' : ''}/reference/bibliography/`,
    englishUrl: `${siteUrl}${basePath}/reference/bibliography/`,
    sections: data.sections ?? BIBLIOGRAPHY_SECTIONS,
    prefixes: data.prefixes ?? BIBLIOGRAPHY_PREFIXES,
    works: data.works ?? BIBLIOGRAPHY_WORKS,
    navigation: navigationOrder(topics),
    base: basePath,
  });
}

/**
 * The bibliography page's Markdown with each marker, a comment on a line of
 * its own, replaced by its section's list: the text the page shows, which its
 * source does not hold.
 *
 * The page is read a line at a time, and a line is a marker only when
 * `MARKER` takes the whole of it, blanks aside: the test the remark plugin
 * puts to each HTML node, so a comment split over lines is no marker to
 * either reader. A line inside a fence is code the page shows, a marker
 * quoted as an example among it, and is left as written.
 *
 * @param {string} source The page's Markdown.
 * @param {readonly {key: string, entries: object[]}[]} sections `siteBibliography`.
 * @param {'en' | 'es'} lang
 * @param {{kind?: 'md' | 'mdx'}} [options] The page's kind, which decides what
 *   is code; the bibliography is a `.md` page.
 * @returns {string}
 * @throws {Error} When the page marks a section `sections` does not have.
 */
export function withSections(source, sections, lang, { kind = 'md' } = {}) {
  const lines = source.split('\n');
  const code = codeLines(
    lines.map((line) => line.replace(/\r$/, '')),
    { kind },
  );
  return lines
    .map((line, index) => {
      const marker = code[index] ? null : MARKER.exec(line.trim());
      if (!marker) return line;
      const section = sections.find(({ key }) => key === marker[1]);
      if (!section) throw new Error(`the bibliography marks a section its data does not have, ${marker[1]}`);
      return sectionMarkdown(section, lang) + (line.endsWith('\r') ? '\r' : '');
    })
    .join('\n');
}

/** The words that open a "Cited by" list, and the one that joins its last two pages. */
export const CITED_BY = { en: { lead: 'Cited by', and: 'and' }, es: { lead: 'Citado por', and: 'y' } };

/**
 * One section's list as Markdown: an item per work, its citation as a
 * References section prints it, its note when it has one, and the pages that
 * cite it.
 *
 * @param {{entries: {ref: object, note?: string, citedBy: {title: string, href: string}[]}[]}} section
 * @param {'en' | 'es'} lang
 * @param {{href?: (page: {id: string, href: string}) => string}} [options] Where a
 *   "Cited by" link leads; the page's address on the site unless a copy says
 *   otherwise.
 * @returns {string}
 */
export function sectionMarkdown(section, lang, { href = (page) => page.href } = {}) {
  const words = CITED_BY[lang];
  return section.entries
    .map((entry) => {
      const links = entry.citedBy.map((page) => `[${literalText(page.title)}](${href(page)})`);
      const list =
        links.length > 1 ? `${links.slice(0, -1).join(', ')} ${words.and} ${links[links.length - 1]}` : links[0];
      const lines = [`- ${citationMarkdown(entry.ref, lang)}`];
      if (entry.note) lines.push(`  ${entry.note.trim().replace(/\s*\n\s*/g, ' ')}`);
      lines.push(`  ${words.lead} ${list}.`);
      return lines.join('\n');
    })
    .join('\n');
}

/**
 * Every page route in the order the sidebar lists it, from the topics'
 * items: a slug written bare or as `{slug}`, and the items of a group in
 * place.
 *
 * @param {readonly {items?: unknown[]}[]} topics src/data/topics.mjs, `topics`.
 * @returns {string[]}
 */
export function navigationOrder(topics) {
  const out = [];
  const walk = (items) => {
    for (const item of items ?? []) {
      if (typeof item === 'string') out.push(item);
      else if (item && typeof item === 'object') {
        if (typeof item.slug === 'string') out.push(item.slug);
        if (Array.isArray(item.items)) walk(item.items);
      }
    }
  };
  for (const topic of topics) walk(topic.items);
  return out;
}
