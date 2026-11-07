/**
 * Each published catalogue as a dataset, in the structured data of its page.
 *
 * A catalogue page used to describe itself to machines as an article and a
 * breadcrumb trail, and nothing in its graph said that it holds a table of
 * numbers, which numbers, or whose. The rows are the point of the page, each
 * read off a table some book or standard printed. Every catalogue is now a
 * `Dataset`, the page's article names it as its `mainEntity`, and the
 * overview of the catalogues is the `DataCatalog` that lists them all.
 *
 * What a dataset says comes from what the page already holds, never from a
 * second list kept beside it:
 *
 *   - its name is the page's title, and its description the page's own when
 *     the page renders one catalogue; a page that renders a second one (the
 *     absorption areas beside the absorption coefficients) describes all it
 *     holds, so there the first takes the paragraph that opens the page, and
 *     the second sits under a `##` heading of its own, whose text names it
 *     and whose opening paragraph describes it;
 *   - its variables are the columns src/generated/catalogues.mjs gives the
 *     table, one per quantity, the band columns of one quantity taken
 *     together under the quantity the generator names for them;
 *   - the works it is based on are the entries of the page's `references`
 *     whose `tables` it prints (src/lib/catalogue-sources.mjs), each named
 *     with the short node the page's article names it with, so the dataset
 *     says whose numbers these are read on its own;
 *   - its date is the page's `dateModified`, the day the page's content last
 *     changed: the dataset is the page's text and the rows the page renders.
 *
 * And what it leaves out is decided: no `license`, because these rows are
 * transcribed from works that keep their own rights and the site can grant
 * none over them, and no `contentUrl` or `distribution`, because the site
 * serves the rows on the page and nowhere else.
 */

import { inlineSpans } from '../../scripts/shared/markdown-spans.mjs';
import { referenceStub } from './citations.mjs';
import { printedTables } from './catalogue-sources.mjs';
import { prose } from './markdown-fences.mjs';

/** The catalogues a page renders, in its source. */
const CATALOGUE_TAG = /<Catalogues\s+catalogue="(\w+)"/;

/** A heading of the level a section of a page takes. */
const SECTION_HEADING = /^##\s+(.+?)\s*#*\s*$/;

/**
 * A line that is markup rather than prose: an import, a component tag or
 * a heading of any level.
 */
const NOT_PROSE = /^\s*(?:import\s|<|#)/;

/**
 * The first character of the private use area, from which each code span of a
 * paragraph takes a character of its own to hold its place while the marks
 * around it are read.
 */
const SPAN_PLACE = 0xe000;

/**
 * What a code span shows: the text between its runs of backticks, a space
 * taken off each end when it has one on both and is not all spaces
 * (CommonMark 0.31.2, 6.1).
 */
function codeOf(text, start, end) {
  let run = 0;
  while (text[start + run] === '`') run += 1;
  const code = text.slice(start + run, end - run);
  return code.length > 1 && code.startsWith(' ') && code.endsWith(' ') && /[^ ]/.test(code)
    ? code.slice(1, -1)
    : code;
}

/**
 * A paragraph as a reader sees it: inline code without its backticks, a link
 * as its text, emphasis without its marks, every run of blanks one space.
 *
 * The code spans are read as the page reads them, through
 * site/scripts/shared/markdown-spans.mjs, and what they hold is code: no mark
 * inside one is read as emphasis or a link. An underscore marks emphasis only
 * where it opens or closes a word, as CommonMark reads it, so `snake_case`
 * written outside code keeps its own.
 *
 * @param {string[]} lines The paragraph's lines.
 * @returns {string}
 */
export function plainText(lines) {
  const text = lines.join(' ');
  const codes = [];
  let marked = '';
  let done = 0;
  for (const [start, end] of inlineSpans(text)) {
    marked += text.slice(done, start) + String.fromCharCode(SPAN_PLACE + codes.length);
    codes.push(codeOf(text, start, end));
    done = end;
  }
  return (marked + text.slice(done))
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/(\*{1,2})(\S(?:.*?\S)?)\1/g, '$2')
    .replace(/(?<![\p{L}\p{N}_])_(\S(?:.*?\S)?)_(?![\p{L}\p{N}_])/gu, '$1')
    .replace(/[\ue000-\uf8ff]/g, (place) => codes[place.charCodeAt(0) - SPAN_PLACE] ?? place)
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Every catalogue a page renders, in order, with the `##` heading it sits
 * under and the paragraph that opens that heading's section.
 *
 * A heading counts for a catalogue only when it comes after the catalogue
 * before it, so a catalogue that follows another with no heading between them
 * has none. The first catalogue's lead is the paragraph that opens the page,
 * the first one before it whatever heading comes between them. Fenced code is
 * not read: a `##` inside a fence is not a heading.
 *
 * @param {string} body The page's source, without its frontmatter.
 * @returns {{key: string, heading?: string, lead?: string}[]}
 */
export function catalogueSections(body) {
  const lines = prose(body).split('\n');
  const sections = [];
  let heading;
  let lead;
  // The page opens the first catalogue's paragraph; after it, only a heading does.
  let paragraph = [];
  for (const line of lines) {
    const tag = CATALOGUE_TAG.exec(line);
    if (tag) {
      if (paragraph && lead === undefined) lead = plainText(paragraph);
      sections.push({
        key: tag[1],
        ...(heading !== undefined ? { heading } : {}),
        ...(lead ? { lead } : {}),
      });
      heading = undefined;
      lead = undefined;
      paragraph = undefined;
      continue;
    }
    const title = SECTION_HEADING.exec(line);
    if (title) {
      heading = plainText([title[1]]);
      // Before the first catalogue, the paragraph that opened the page stays.
      if (sections.length > 0 || lead === undefined) {
        lead = undefined;
        paragraph = [];
      }
      continue;
    }
    // Only the first paragraph under a heading opens its section.
    if (paragraph === undefined || lead !== undefined) continue;
    if (line.trim() === '') {
      if (paragraph.length > 0) lead = plainText(paragraph);
    } else if (paragraph.length > 0 || !NOT_PROSE.test(line)) {
      paragraph.push(line);
    }
  }
  return sections;
}

/**
 * The name and description of each catalogue a page renders, or what stops
 * one from having either.
 *
 * The first catalogue on a page is what the page is about, and takes the
 * page's own title. It takes the page's description too when it is the only
 * one; a page that renders more describes them all, and what that says of
 * the others is not this one's, so there the paragraph that opens the page
 * describes it. Every later one is a table the page holds beside it, and has
 * to sit under a `##` heading of its own, after the catalogue before it: the
 * heading names its dataset and the paragraph that opens the section
 * describes it.
 *
 * @param {object} page
 * @param {string} page.id The page's entry id, which the messages name.
 * @param {string} page.title The page's title.
 * @param {string} page.description The page's description.
 * @param {{key: string, heading?: string, lead?: string}[]} page.sections
 *   What `catalogueSections` read off the page.
 * @returns {{datasets: {key: string, name: string, description: string}[], problems: string[]}}
 */
export function catalogueDatasets({ id, title, description, sections }) {
  const datasets = [];
  const problems = [];
  for (const [i, section] of sections.entries()) {
    if (i === 0 && sections.length === 1) {
      datasets.push({ key: section.key, name: title, description });
    } else if (i === 0 && !section.lead) {
      problems.push(
        `${id} renders ${sections.length} catalogues and opens with no paragraph before the first, ` +
          `${section.key}, and with the page's description speaking of them all, that paragraph is what ` +
          'describes its dataset',
      );
    } else if (i === 0) {
      datasets.push({ key: section.key, name: title, description: section.lead });
    } else if (section.heading === undefined) {
      problems.push(
        `${id} renders ${section.key} after another catalogue with no \`##\` heading of its own between ` +
          'them, and that heading is what names its dataset',
      );
    } else if (!section.lead) {
      problems.push(
        `${id}: the \`## ${section.heading}\` section that holds ${section.key} opens with no paragraph, ` +
          'and that paragraph is what describes its dataset',
      );
    } else {
      datasets.push({ key: section.key, name: section.heading, description: section.lead });
    }
  }
  return { datasets, problems };
}

/** What a dataset's variables say of a run of band columns, in each language. */
const BANDS = {
  en: (first, last) => (first === last ? `In the ${first} band` : `From the ${first} band to the ${last} band`),
  es: (first, last) => (first === last ? `En la banda de ${first}` : `De la banda de ${first} a la de ${last}`),
};

/**
 * What a catalogue measures, as schema.org's `variableMeasured`.
 *
 * One `PropertyValue` per column, named by its heading, with its unit when it
 * has one; except that the columns of one quantity measured band by band,
 * which the page heads by their band alone, are one variable named by that
 * quantity, its description saying which bands it covers.
 *
 * @param {{heading: string, headingEs: string, unit: string, quantity?: string, quantityEs?: string}[]} columns
 *   The catalogue's columns, as src/generated/catalogues.mjs holds them.
 * @param {'en' | 'es'} lang The language of the page.
 * @returns {object[]}
 */
export function variablesMeasured(columns, lang) {
  const runs = [];
  for (const column of columns) {
    const heading = lang === 'es' ? column.headingEs : column.heading;
    const quantity = lang === 'es' ? column.quantityEs : column.quantity;
    const last = runs.at(-1);
    if (quantity !== undefined && last?.quantity === quantity && last.unit === column.unit) {
      last.bands.push(heading);
    } else {
      runs.push({ name: quantity ?? heading, quantity, unit: column.unit, bands: [heading] });
    }
  }
  return runs.map((run) => ({
    '@type': 'PropertyValue',
    name: run.name,
    ...(run.quantity !== undefined ? { description: BANDS[lang](run.bands[0], run.bands.at(-1)) } : {}),
    ...(run.unit ? { unitText: run.unit } : {}),
  }));
}

/**
 * The entries of a page's references that a catalogue's rows were read from:
 * the ones whose `tables` name a table the catalogue prints, in the page's
 * order.
 *
 * @param {object[]} references The page's frontmatter references.
 * @param {{rows: {table: string}[]}} catalogue The catalogue, as
 *   src/generated/catalogues.mjs holds it.
 * @returns {object[]}
 */
export function catalogueSources(references, catalogue) {
  const printed = new Set(printedTables([catalogue]));
  return (references ?? []).filter((ref) => (ref.tables ?? []).some((table) => printed.has(table)));
}

/** The fragment a catalogue's dataset takes on its page. */
const datasetFragment = (key) => `dataset-${key}`;

/** The fragment of the table a catalogue renders (src/components/Catalogues.astro). */
const tableFragment = (key) => `catalogue-${key}`;

/**
 * One catalogue's `Dataset` node.
 *
 * @param {object} options
 * @param {{key: string, name: string, description: string}} options.dataset
 *   Its name and description (`catalogueDatasets`).
 * @param {{columns: object[], rows: {table: string}[]}} options.catalogue
 *   The catalogue, as src/generated/catalogues.mjs holds it.
 * @param {object[]} options.references The page's frontmatter references.
 * @param {'en' | 'es'} options.lang The language of the page.
 * @param {string} options.pageUrl The page's canonical URL.
 * @param {string} options.twinUrl The canonical URL of the same page in the
 *   other language.
 * @param {string} options.bibliographyUrl The bibliography of the page's language.
 * @param {{'@id': string, name: string, url: string}} options.dataCatalog
 *   The overview of the catalogues, in the page's language.
 * @param {string} [options.dateModified] The day the page's content last
 *   changed, its article's `dateModified`. A dataset is the page's text and
 *   the rows the page renders, so it changed when its page did; with no day
 *   for the page, it says none.
 * @returns {Record<string, unknown> & {'@id': string}}
 */
export function datasetNode({
  dataset,
  catalogue,
  references,
  lang,
  pageUrl,
  twinUrl,
  bibliographyUrl,
  dataCatalog,
  dateModified,
}) {
  const sources = catalogueSources(references, catalogue);
  return {
    '@type': 'Dataset',
    '@id': `${pageUrl}#${datasetFragment(dataset.key)}`,
    name: dataset.name,
    description: dataset.description,
    url: `${pageUrl}#${tableFragment(dataset.key)}`,
    inLanguage: lang,
    includedInDataCatalog: { '@type': 'DataCatalog', ...dataCatalog },
    [lang === 'en' ? 'workTranslation' : 'translationOfWork']: {
      '@id': `${twinUrl}#${datasetFragment(dataset.key)}`,
    },
    variableMeasured: variablesMeasured(catalogue.columns, lang),
    ...(sources.length > 0 ? { isBasedOn: sources.map((ref) => referenceStub(ref, bibliographyUrl)) } : {}),
    ...(dateModified ? { dateModified } : {}),
  };
}

/**
 * How the overview of the catalogues lists one: enough to name it and find it.
 *
 * @param {{key: string, name: string}} dataset
 * @param {string} pageUrl The canonical URL of the page that renders it.
 * @returns {object}
 */
export function datasetStub(dataset, pageUrl) {
  return {
    '@type': 'Dataset',
    '@id': `${pageUrl}#${datasetFragment(dataset.key)}`,
    name: dataset.name,
    url: `${pageUrl}#${tableFragment(dataset.key)}`,
  };
}
