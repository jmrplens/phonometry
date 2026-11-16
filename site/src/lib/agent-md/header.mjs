/**
 * The block of `Key: value` lines that heads every page's Markdown copy.
 *
 * A copy is read away from the page: pasted into a chat, fetched by an agent,
 * cut into the llms files. Whatever a reader of the page learns from around
 * the text (which address it lives at, which language it is in and where the
 * other one is, which release it documents and how to install it, who wrote
 * it, when it was first published and last changed, which standards it
 * implements, under which licence) has to travel inside the copy, or the copy
 * is a text nobody can cite or date. The old copies carried a bare source line
 * and nothing else.
 *
 * The keys stay in English in both languages, because they are a schema a
 * program reads; the values and the sentence above them are in the page's
 * language. A line whose value is unknown is left out rather than printed
 * empty, so a key present always means a value present. A line that lists
 * documents separates them with `; `, since a designation can hold a comma of
 * its own (`JCGM 100:2008, the GUM`).
 *
 * Every value comes from the module that already publishes it on the site:
 * the version and the install line from src/data/repo-stats.mjs, the dates
 * from src/lib/content-dates.mjs (the sitemap's `<lastmod>`) and
 * src/lib/page-dates.mjs (the structured data's `datePublished`), the
 * standards from src/lib/reference-chips.ts (the standards the header chips
 * stand for), the author and the repository from src/data/site.mjs. Nothing
 * here is typed a second time.
 *
 * There is no build date: a line that moves on every build would read as a
 * date of the content and would make every copy differ from the last one. The
 * lines that name the release (`Version:` and `Install:`) are the ones
 * src/lib/page-markdown.mjs lists in `releaseHeaderKeys`, and they are
 * written from that list, so anything that compares copies across a release
 * can leave exactly those out.
 *
 * @module
 */
import { basePath, repositoryUrl, siteUrl } from '../../data/site.mjs';
import { releaseHeaderKeys } from '../page-markdown.mjs';
import { line } from './markdown-table.mjs';

/**
 * What the header of one copy states. Every field but the two the page
 * always has (`canonical`, `lang`) may be missing, and a missing one prints
 * no line.
 *
 * @typedef {object} HeaderFields
 * @property {'en' | 'es'} lang
 * @property {string} canonical  The page's own address.
 * @property {string} [alternate]  The address of the copy in the other language.
 * @property {{ version: string, install: string, preRelease?: boolean }} release
 * @property {{ name: string, orcid: string }} [author]
 * @property {string} [published]  `YYYY-MM-DD`.
 * @property {string} [updated]  `YYYY-MM-DD`.
 * @property {readonly string[]} [standards]  Designations the page implements.
 * @property {{ checks: number, designations: readonly string[], url: string }} [verified]
 *   What the page's "Verified by" line states: how many conformance checks
 *   verify it, against which documents, and the section of the conformance
 *   report that lists them.
 * @property {boolean} [license]  `false` on a page that carries no licence of
 *   its own (a catalogue transcribing published tables).
 * @property {string} [summary]  The page's description.
 */

/** Where the index of every copy is. */
export const INDEX_URL = `${siteUrl}${basePath}/llms.txt`;

/** The licence line every page but a catalogue carries. */
export const LICENSE = `MIT (${repositoryUrl}/blob/main/LICENSE)`;

/**
 * The words the sentence under every copy's title opens with, per language:
 * what tells a copy from any other `index.md` (scripts/agent-md.mjs removes
 * only files that open this way).
 */
export const LEAD_OPENING = Object.freeze({
  en: 'One page of the phonometry documentation',
  es: 'Una página de la documentación de phonometry',
});

/** The sentence under the title that says what the reader is holding, per language. */
const LEAD = Object.freeze({
  en: `${LEAD_OPENING.en}, as Markdown. Index: ${INDEX_URL}`,
  es: `${LEAD_OPENING.es}, en Markdown. Índice: ${INDEX_URL}`,
});

/** Between the documents of a line that lists several. */
export const LIST_SEPARATOR = '; ';

/**
 * The value of each release line, keyed by the names `releaseHeaderKeys`
 * gives them. A key in that list with no value here is an error, never a
 * silent omission: the list is what a comparison across releases leaves out,
 * and a release line written under a key it does not hold would move every
 * copy on every release.
 *
 * A pre-release (`preRelease`, read from VERSION by PEP 440 in
 * src/data/repo-stats.mjs) adds a line that says the version is not on PyPI
 * yet, since the install line installs the last release there; it names no
 * version PyPI serves, so it cannot go stale, and it goes at the stamp with
 * nothing to change.
 *
 * @param {{ version: string, install: string, preRelease?: boolean }} release
 * @param {'en' | 'es'} lang
 * @returns {[string, string][]}
 */
function releaseLines(release, lang) {
  /** @type {Record<string, string | undefined>} */
  const values = {
    Version: `phonometry ${release.version}`,
    Install: release.install,
    'Pre-release': release.preRelease ? PRE_RELEASE[lang](release.version) : undefined,
  };
  for (const key of Object.keys(values)) {
    if (!releaseHeaderKeys.includes(key)) {
      throw new Error(`header: ${key} names the release and is not in releaseHeaderKeys (src/lib/page-markdown.mjs)`);
    }
  }
  return releaseHeaderKeys.flatMap((key) => {
    if (!(key in values)) {
      throw new Error(`header: releaseHeaderKeys lists ${key}, and the header has no value for it`);
    }
    const value = values[key];
    return value === undefined ? [] : [/** @type {[string, string]} */ ([key, value])];
  });
}

/** The `Pre-release:` value in each language. */
export const PRE_RELEASE = Object.freeze({
  en: (version) => `phonometry ${version} is not on PyPI yet`,
  es: (version) => `phonometry ${version} aún no está en PyPI`,
});

/**
 * The `Verified:` value in the page's language.
 *
 * @param {NonNullable<HeaderFields['verified']>} verified
 * @param {'en' | 'es'} lang
 * @returns {string}
 */
function verifiedValue(verified, lang) {
  const what = lang === 'es' ? 'comprobaciones de conformidad' : 'conformance checks';
  const against = verified.designations.length ? ` (${verified.designations.join(LIST_SEPARATOR)})` : '';
  return `${verified.checks} ${what}${against} ${verified.url}`;
}

/**
 * The header: the lead sentence, the `Key: value` lines, and the rule that
 * ends them.
 *
 * @param {HeaderFields} fields
 * @returns {string}  Markdown, ending with the closing `---` and no newline.
 */
export function header(fields) {
  /** @type {[string, string | undefined][]} */
  const lines = [
    ['Canonical', fields.canonical],
    ['Language', fields.lang],
    ['Alternate', fields.alternate],
    ...releaseLines(fields.release, fields.lang),
    ['Author', fields.author ? `${fields.author.name} (${fields.author.orcid})` : undefined],
    ['Published', fields.published],
    ['Updated', fields.updated],
    ['Standards', fields.standards?.length ? fields.standards.join(LIST_SEPARATOR) : undefined],
    ['Verified', fields.verified ? verifiedValue(fields.verified, fields.lang) : undefined],
    ['License', fields.license === false ? undefined : LICENSE],
    ['Summary', fields.summary],
  ];
  const block = lines
    .map(([key, value]) => [key, line(value)])
    .filter(([, value]) => value !== '')
    .map(([key, value]) => `${key}: ${value}`);
  return [`> ${LEAD[fields.lang]}`, '', ...block, '', '---'].join('\n');
}
