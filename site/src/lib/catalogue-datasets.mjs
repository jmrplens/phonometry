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
 * The page is read as the site reads it. Its blocks come from the walk of
 * src/lib/markdown-fences.mjs, so an aside, a component, a list, a quotation
 * or a table is never taken for the paragraph that describes a dataset, and a
 * heading ends the paragraph above it. The text of a heading or a paragraph
 * is what the page shows of it, read once from left to right as the page
 * reads it, so that a comment owns what it holds and a tag what its
 * attributes write: its code spans, its escapes, its comments, its character
 * references, its links and its marks read as CommonMark and MDX read them. Its
 * quotes, dots and hyphens stay as the source writes them, as the page's meta
 * description keeps them: the site's typographer, remark-smartypants, curls
 * the quotes and sets three dots and two hyphens on the page alone, and the
 * structured data check compares the two with that setting undone. What the
 * page shows as something other than text, a component of its own, an
 * expression, a formula, is not text a dataset can carry, and stops the
 * build where a name or a description holds it.
 *
 * And what it leaves out is decided: no `license`, because these rows are
 * transcribed from works that keep their own rights and the site can grant
 * none over them, and no `contentUrl` or `distribution`, because the site
 * serves the rows on the page and nowhere else.
 */

import { inlineParts, pageMarkup } from '../../scripts/shared/markdown-spans.mjs';
import { referenceStub } from './citations.mjs';
import { printedTables } from './catalogue-sources.mjs';
import { flowOf, MDX_TAG, NOT_INLINE_ROLES, pageLines, splitLines } from './markdown-fences.mjs';

/** Where a `<Catalogues>` tag opens, in what a page renders of its source (`pageMarkup`). */
const CATALOGUE_OPENS = /<Catalogues(?![\w.:$-])/g;

/** A whole tag from where it opens, across its lines, as the walk of a page reads one. */
const WHOLE_TAG = new RegExp(MDX_TAG.source, 'y');

/**
 * Each attribute of a tag, past its name: the attribute's name, and its value
 * in quotes or as an expression, so nothing a value holds is read as a name.
 */
const ATTRIBUTE = /([^\s"'=<>/{}]+)(?:\s*=\s*("[^"]*"|'[^']*'|\{(?:[^{}]|\{[^{}]*\})*\}))?/g;

/**
 * A heading of the level a section of a page takes, past its blanks: its two
 * marks, its text, and the closing marks a blank sets apart from the text.
 */
const SECTION_HEADING = /^##[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$/;

/**
 * A line of an `.mdx` page that opens its ESM, an `import` or an `export`,
 * which runs to the next blank line and is code, not a paragraph.
 */
const MDX_ESM = /^(?:import|export)\s/;

/**
 * The first character of the private use area, from which each piece of a
 * paragraph that is read before its marks (a code span, an escaped
 * character, a character reference) takes a character of its own to hold its
 * place while the marks around it are read.
 */
const HELD = 0xe000;

/** Every character of the private use area, where the held pieces wait. */
const HELD_PLACE = /[\ue000-\uf8ff]/g;

/** The character references by name a page writes, and what each shows. */
const NAMED_REFERENCES = new Map([
  ['amp', '&'],
  ['lt', '<'],
  ['gt', '>'],
  ['quot', '"'],
  ['apos', "'"],
  ['nbsp', '\u00a0'],
]);

/** A character reference: a decimal or hexadecimal code point, or a name (CommonMark 2.5). */
const REFERENCE = /&(?:#(\d{1,7})|#[xX]([\da-fA-F]{1,6})|([A-Za-z][A-Za-z\d]{0,31}));/g;

/** Every tag of a paragraph, as the walk of the page reads a tag. */
const INLINE_TAG = new RegExp(MDX_TAG.source, 'g');

/**
 * A link or an image, `[text](address "title")` (CommonMark 6.3 and 6.4): its
 * text may hold brackets one level deep, its address parentheses one level
 * deep or anything but a line end between angle brackets, and its title
 * stands in quotes or parentheses.
 */
const LINK =
  /!?\[((?:[^[\]]|\[[^[\]]*\])*)\]\([ \t]*(?:<[^<>\n]*>|(?:[^()\s]|\([^()\s]*\))*)(?:[ \t]+(?:"[^"]*"|'[^']*'|\([^()]*\)))?[ \t]*\)/g;

/** Emphasis and strong emphasis by asterisks, the marks around the text they mark. */
const STARS = /(\*{1,2})(\S(?:.*?\S)?)\1/g;

/**
 * Emphasis and strong emphasis by underscores, which mark only where they open
 * or close a word, as CommonMark reads them: `snake_case` keeps its own.
 */
const UNDERSCORES = /(?<![\p{L}\p{N}_])(_{1,2})(\S(?:.*?\S)?)\1(?![\p{L}\p{N}_])/gu;

/** Struck text, by one tilde or two (GitHub Flavored Markdown 6.5). */
const STRUCK = /(~{1,2})(\S(?:.*?\S)?)\1/g;

/**
 * What is left of a paragraph, once read, that the page shows as something
 * other than its text: a tag that renders a component of its own, an
 * expression, or a character reference by a name it does not decode.
 */
const UNREAD = /<[^<>]*>?|\{[^{}]*\}?|\}|&[A-Za-z][A-Za-z\d]*;/g;

/** The blanks a page's source runs together into one space between words. */
const BLANKS = /[ \t\r\n]+/g;

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

/** What a character reference shows, or `undefined` for a name the reader does not decode. */
function referenceOf(decimal, hexadecimal, name) {
  if (name !== undefined) return NAMED_REFERENCES.get(name);
  const point = decimal !== undefined ? Number(decimal) : Number.parseInt(hexadecimal, 16);
  return point > 0 && point <= 0x10ffff && (point < 0xd800 || point > 0xdfff)
    ? String.fromCodePoint(point)
    : '\ufffd';
}

/** Whether a line ends on a backslash that breaks it: one no other backslash escapes. */
const breaksOnBackslash = (line) => /(?<!\\)(?:\\\\)*\\$/.test(line);

/**
 * What the page shows of a run of inline text, and what in it the page shows
 * as something other than text.
 *
 * The text is read once, left to right, as the page reads it, through
 * `inlineParts` of site/scripts/shared/markdown-spans.mjs: whichever of a code
 * span, a formula, a backslash escape (CommonMark 2.4), a comment, a tag and
 * an expression opens first takes what follows, so a comment owns a formula or
 * a backtick it holds, and a tag what its attributes write. What a code span
 * holds is code, and no mark inside one is read; a formula is not text; an
 * escape is the character it stands for, which opens nothing; and a comment,
 * or an expression that holds nothing but blanks and comments, shows nothing.
 * Then each character reference (2.5) is the character it stands for; a tag
 * around text shows the text; a link and an image show their text; and
 * emphasis, strong emphasis and struck text show what they mark, read until
 * no mark is left. A backslash at the end of a line breaks the line, and the
 * blanks between words are one space. Unicode spaces the page shows, a
 * non-breaking one or a thin one, stay as written.
 *
 * Left as written, and named in `markup`: a formula, a tag that renders a
 * component of its own (`<Badge text="new" />`), an expression (`{x}`) and a
 * character reference by a name the reader does not decode (`&shy;`).
 *
 * @param {string[]} lines The lines of a paragraph, or a heading's text.
 * @returns {{text: string, markup: string[]}}
 */
export function readInline(lines) {
  const held = [];
  const markup = [];
  const hold = (shown) => String.fromCharCode(HELD + held.push(shown) - 1);
  // The parts are read with the line ends where the page writes them, so a
  // line comment ends where its line does; the text around them reads each
  // line end as the blank it is, at the same index.
  const written = lines
    .map((line, index) => (index < lines.length - 1 && breaksOnBackslash(line) ? line.slice(0, -1) : line))
    .join('\n');
  const text = written.replaceAll('\n', ' ');
  let marked = '';
  let done = 0;
  for (const { start, end, what } of inlineParts(written)) {
    const part = text.slice(start, end);
    let shown = '';
    if (what === 'code') shown = hold(codeOf(text, start, end));
    else if (what === 'escape') shown = hold(part[1]);
    else if (what !== 'comment') {
      // A formula or an expression: not text, and named in `markup`.
      markup.push(part);
      shown = hold(part);
    }
    marked += text.slice(done, start) + shown;
    done = end;
  }
  let read = (marked + text.slice(done))
    .replace(REFERENCE, (reference, decimal, hexadecimal, name) => {
      const shown = referenceOf(decimal, hexadecimal, name);
      return shown === undefined ? reference : hold(shown);
    })
    .replace(INLINE_TAG, (tag) => (tag.endsWith('/>') ? tag : ''))
    .replace(LINK, '$1');
  for (let before; before !== read; ) {
    before = read;
    read = read.replace(STARS, '$2').replace(UNDERSCORES, '$2').replace(STRUCK, '$2');
  }
  const restore = (piece) => piece.replace(HELD_PLACE, (place) => held[place.charCodeAt(0) - HELD] ?? place);
  markup.push(...[...read.matchAll(UNREAD)].map(([piece]) => restore(piece)));
  return { text: restore(read).replace(BLANKS, ' ').trim(), markup };
}

/**
 * A paragraph as a reader sees it: inline code without its backticks, an
 * escaped character without its backslash, a link as its text, emphasis
 * without its marks, every run of blanks one space (`readInline`).
 *
 * @param {string[]} lines The paragraph's lines.
 * @returns {string}
 */
export function plainText(lines) {
  return readInline(lines).text;
}

/** A line's text past the blanks on either side of it. */
const pastBlanks = (text) => text.replace(/^[ \t]+|[ \t]+$/g, '');

/**
 * How a piece of an `.mdx` flow changes the elements open around the lines
 * after it: a tag opens one, a closing tag closes one, and a tag that closes
 * itself or an expression does neither.
 */
function nesting(piece) {
  if (!piece.startsWith('<')) return 0;
  if (piece.startsWith('</')) return -1;
  return piece.endsWith('/>') ? 0 : 1;
}

/**
 * The catalogue a `<Catalogues>` tag renders: the word its `catalogue` names
 * in quotes, wherever among its attributes. A value the reader cannot read as
 * a word, an expression, is the key as written, and a tag with no `catalogue`
 * is the tag as written: no catalogue has either for its key, so the build
 * stops on it by name, where a tag it did not see would leave its page a
 * catalogue short.
 */
function catalogueOf(tag) {
  for (const [, name, value] of tag.slice('<Catalogues'.length).matchAll(ATTRIBUTE)) {
    if (name === 'catalogue') return /^(["'])\w+\1$/.test(value ?? '') ? value.slice(1, -1) : (value ?? tag);
  }
  return tag;
}

/**
 * The catalogues a page renders, by the line each tag opens on: every
 * `<Catalogues>` tag of what the page renders of its source, read whole, so
 * one written over several lines or beside another on its line is there.
 *
 * @param {string[]} rendered The page's lines as `pageMarkup` leaves them.
 * @returns {Map<number, string[]>}
 */
function cataloguesByLine(rendered) {
  const text = rendered.join('\n');
  const byLine = new Map();
  // The line a tag opens on, and where the line feed that ends it stands.
  let line = 0;
  let lineEnd = rendered[0]?.length ?? 0;
  for (const { index } of text.matchAll(CATALOGUE_OPENS)) {
    WHOLE_TAG.lastIndex = index;
    const tag = WHOLE_TAG.exec(text);
    if (tag === null) continue;
    while (index > lineEnd) {
      line += 1;
      lineEnd += rendered[line].length + 1;
    }
    byLine.set(line, [...(byLine.get(line) ?? []), catalogueOf(tag[0])]);
  }
  return byLine;
}

/** A section's reading of a heading or a paragraph: its text, and its markup if any. */
function asRead(field, { text, markup }) {
  return { [field]: text, ...(markup.length > 0 ? { [`${field}Markup`]: markup } : {}) };
}

/**
 * Every catalogue a page renders, in order, with the `##` heading it sits
 * under and the paragraph that opens that heading's section.
 *
 * A heading counts for a catalogue only when it comes after the catalogue
 * before it, so a catalogue that follows another with no heading between them
 * has none. The first catalogue's lead is the paragraph that opens the page,
 * the first one before it whatever heading comes between them.
 *
 * The page is read in blocks, as the site reads it (`pageLines`): code is not
 * read, its ESM (`import`) neither, and a `##` inside a fence is not a heading.
 * A catalogue is a `<Catalogues>` tag the site renders (`pageMarkup`), so one
 * quoted in a code span, a comment or an expression, or written behind a
 * backslash, is no section; and the tag is read whole where it opens, as MDX
 * reads it, so one written over several lines, beside another on its line or
 * with its `catalogue` after another attribute is one. A paragraph or a heading
 * counts only where it stands on the page itself, outside any list, quotation,
 * aside (`:::note`) or component (`<Aside>`), so what those hold never
 * describes a dataset. A heading ends the paragraph above it, with no blank
 * line between them, and so does any other block; a line underlined with
 * hyphens is a `##` heading too. A heading or a lead whose text holds markup
 * carries it as `headingMarkup` or `leadMarkup` (`readInline`).
 *
 * @param {string} body The page's source, without its frontmatter.
 * @returns {{key: string, heading?: string, lead?: string, headingMarkup?: string[], leadMarkup?: string[]}[]}
 */
export function catalogueSections(body) {
  const lines = splitLines(body);
  // Each line as the site renders it: every part that renders no tag blanked,
  // the lines and the columns where the page writes them.
  const rendered = splitLines(pageMarkup(body));
  const tags = cataloguesByLine(rendered);
  const sections = [];
  let heading;
  let lead;
  // The page opens the first catalogue's paragraph; after it, only a heading does.
  let open = true;
  // The lines of the paragraph being read, when the page itself holds it.
  let paragraph = null;
  let opensSection = false;
  // The elements open around the line, and the line past the flow read last. The
  // asides open around it are the walk's to count: one ends with the quotation or
  // the list item it opened in as well as on its own fence.
  let depth = 0;
  let flowEnd = 0;
  const endParagraph = () => {
    if (paragraph !== null && opensSection && lead === undefined) lead = readInline(paragraph);
    paragraph = null;
  };
  const startSection = (title) => {
    heading = title;
    // Before the first catalogue, the paragraph that opened the page stays.
    if (sections.length > 0 || lead === undefined) {
      lead = undefined;
      open = true;
    }
  };
  pageLines(lines).forEach((line, index) => {
    if (NOT_INLINE_ROLES.has(line.role)) {
      endParagraph();
      return;
    }
    const keys = tags.get(index);
    if (keys) endParagraph();
    for (const key of keys ?? []) {
      sections.push({
        key,
        ...(heading !== undefined ? asRead('heading', heading) : {}),
        ...(lead?.text ? asRead('lead', lead) : {}),
      });
      heading = undefined;
      lead = undefined;
      open = false;
    }
    if (line.role === 'text') {
      paragraph?.push(line.rest);
      return;
    }
    if (line.role === 'underline' && paragraph !== null) {
      // The paragraph above was a heading all along: `##` under hyphens, `#` under equals signs.
      if (pastBlanks(line.rest).startsWith('-')) startSection(readInline(paragraph));
      paragraph = null;
      return;
    }
    endParagraph();
    // Where the page itself holds the line, with no container of the walk's around it.
    const onPage = depth === 0 && line.asides === 0 && line.rest === line.text;
    const written = pastBlanks(line.rest);
    if (line.role === 'paragraph' && onPage && !keys && !MDX_ESM.test(written)) {
      paragraph = [line.rest];
      opensSection = open && lead === undefined;
    } else if (line.role === 'heading' && onPage) {
      const title = SECTION_HEADING.exec(written);
      if (title) startSection(readInline([title[1]]));
    } else if (line.role === 'single' && index >= flowEnd && /^[<{]/.test(written)) {
      const flow = flowOf([written, ...lines.slice(index + 1)].join('\n'));
      if (flow !== null) {
        depth = Math.max(depth + flow.pieces.reduce((sum, piece) => sum + nesting(piece), 0), 0);
        flowEnd = index + flow.lines + 1;
      }
    }
  });
  endParagraph();
  return sections;
}

/** The markup a section's heading or lead holds, quoted, for a message. */
const quoted = (markup) => markup.map((piece) => JSON.stringify(piece)).join(', ');

/** What a message says of markup a dataset would publish as written. */
const AS_WRITTEN = 'markup the page shows as something other than text, which its dataset would publish as written';

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
 * describes it. A heading or a paragraph that holds markup the page does not
 * show as text names or describes nothing.
 *
 * @param {object} page
 * @param {string} page.id The page's entry id, which the messages name.
 * @param {string} page.title The page's title.
 * @param {string} page.description The page's description.
 * @param {{key: string, heading?: string, lead?: string, headingMarkup?: string[], leadMarkup?: string[]}[]} page.sections
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
    } else if (i === 0 && section.leadMarkup) {
      problems.push(
        `${id}: the paragraph that opens the page, which describes ${section.key}, holds ` +
          `${quoted(section.leadMarkup)}: ${AS_WRITTEN}`,
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
    } else if (section.headingMarkup || section.leadMarkup) {
      const held = [
        ...(section.headingMarkup
          ? [`the \`## ${section.heading}\` heading, which names ${section.key}, holds ${quoted(section.headingMarkup)}`]
          : []),
        ...(section.leadMarkup
          ? [`the paragraph that opens it, which describes ${section.key}, holds ${quoted(section.leadMarkup)}`]
          : []),
      ];
      problems.push(`${id}: ${held.join('; ')}: ${AS_WRITTEN}`);
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
