// The Markdown copy of a page that has no docs/ mirror, as the page shows it.
//
// emit-page-markdown.mjs publishes a Markdown copy beside every page but the
// ones src/lib/page-markdown.mjs withholds (the landing pages, and the pages
// that show their data through a component with no docs/ copy). Where docs/
// holds no mirror of the page (every Spanish page but the transplanted ones,
// and in English the API reference and the errata families), the copy is the
// page's own source with its frontmatter and its MDX machinery taken out: its
// import and export statements and its component tags, a wrapper keeping its
// children. That machinery was found by patterns over the page as written,
// which read code as machinery too: the `import` line of a Python example went
// as the page's own import, a `<NC-15` written in a code span opened a
// component that ran to the next `/>`, and two blank lines of an example
// closed up. The page is read here as the site renders it (pageMarkup and
// pageParts of markdown-spans.mjs), so only what the page renders as markup
// goes, and what it shows as code stays as it shows it.
//
// What else the copy needs to read as the page does is written here too: the
// page's title, which its source keeps in the frontmatter; its comments taken
// out; a count the page prints from a data module, written as the number; a
// link the page writes from the site's root, made absolute so that it leads
// somewhere from a copy fetched on its own; a figure, a clip and a fiche,
// written as an image and a line where the copy used to drop them with their
// text; and the References section the layout prints from the frontmatter.
// copyDefects then reads the copy against the page on its own.
//
// Nothing here imports a dependency.

import { codeLines } from '../../src/lib/markdown-fences.mjs';
import { citationParts, noteParts, opening, sortedReferences } from '../../src/lib/references-format.mjs';
import { mediaUrl } from '../../src/lib/media.mjs';
import { EXPRESSION_BLANK, frontmatterEnd, pageMarkup, pageParts } from './markdown-spans.mjs';

/** An import or an export statement of an `.mdx` page, on a line of its own. */
const ESM = /^(?:import|export)\s.*$/gm;

/** A component closed in its own tag: `<ThemeImage ... />`, `<Video ... />`. */
const SELF_CLOSING = /<[A-Z][\w.]*\b[^>]*\/>/g;

/** The opening or the closing tag of a component that wraps content. */
const WRAPPER = /<\/?[A-Z][\w.]*\b[^>]*>/g;

/**
 * A link the page writes from the site's root: the destination of a Markdown
 * link, written bare or in `<...>` and after white space or not, or of a
 * reference-style definition (`[g]: /x/`), or an `href` or `src` of a tag the
 * page renders, quoted either way or, on an `.md` page, not at all, that opens
 * on one slash. Two slashes open an address on another host, and stay. Any
 * other form stays as written, and copyDefects finds it.
 */
const ROOT_RELATIVE = /(\]\([ \t]*<?|\b(?:href|src)=["']?|^ {0,3}\[[^\]\n]+\]:[ \t]*<?)\/(?!\/)/gm;

/**
 * An expression that prints one name, `{totalChecks}`, with the blanks and
 * comments around it read left to right as MDX reads them (EXPRESSION_BLANK):
 * `{/* a count *\/ totalChecks}`, or `{// a count` with `totalChecks}` on the
 * next line.
 */
const NAME = new RegExp(String.raw`^\{${EXPRESSION_BLANK}*([A-Za-z_$][\w$]*)${EXPRESSION_BLANK}*\}$`);

/**
 * The page without its frontmatter, as Astro finds it, after a byte order mark
 * or blank lines too, and without the rest of the line its closing fence is on.
 *
 * @param {string} text The page as written.
 * @returns {string} What follows the frontmatter, or the page when it has none.
 */
export function stripFrontmatter(text) {
  const end = frontmatterEnd(text);
  if (end === 0) return text;
  const line = text.indexOf('\n', end);
  return line === -1 ? '' : text.slice(line + 1);
}

/**
 * The frontmatter of a page as written between its fences, for a YAML reader,
 * or `''` when the page has none.
 *
 * @param {string} text The page as written.
 * @returns {string}
 */
export function frontmatterSource(text) {
  const end = frontmatterEnd(text);
  if (end === 0) return '';
  const head = text.slice(0, end);
  const open = head.indexOf('\n');
  const close = head.lastIndexOf('\n');
  return close > open ? head.slice(open + 1, close + 1) : '';
}

/**
 * The names an `.mdx` page imports, each with the module it imports it from and
 * the name it has there: `import { totalChecks as checks } from '../x.mjs'`
 * gives `checks`, from `../x.mjs`, as `totalChecks`. Only the statements the
 * page renders as its own count, so an `import` line of a code example names
 * nothing.
 *
 * @param {string} text The page, its frontmatter out.
 * @returns {Map<string, { module: string, imported: string }>}
 */
export function pageImports(text) {
  const names = new Map();
  for (const found of pageMarkup(text, { kind: 'mdx' }).matchAll(ESM)) {
    const statement = text.slice(found.index, found.index + found[0].length);
    const named = statement.match(/^import\s*\{([^}]*)\}\s*from\s*(['"])([^'"]+)\2/);
    if (!named) continue;
    for (const piece of named[1].split(',')) {
      const [imported, local = imported] = piece.trim().split(/\s+as\s+/);
      if (imported) names.set(local, { module: named[3], imported });
    }
  }
  return names;
}

/**
 * The prose of a page with the MDX machinery that is noise as text taken out:
 * its import and export statements, its components closed in their own tag, and
 * the tags of the components that wrap content, whose children stay. Each is
 * taken out only where the page renders it as markup, so a tag or an `import`
 * line written in code stays. Its comments go too, an expression that prints a
 * name is written as the value `value` gives the name, and a link from the
 * site's root gets `origin` in front of it. A run of blank lines outside code
 * closes up to one; the blank lines of a code example stay.
 *
 * An expression `value` cannot write stops the copy: the page would print a
 * number where the copy prints the code that computes it.
 *
 * @param {string} text The page, its frontmatter out.
 * @param {{
 *   kind?: 'md' | 'mdx',
 *   expand?: (tag: string) => string | undefined,
 *   value?: (name: string) => string | number | undefined,
 *   origin?: string,
 *   firstLine?: number,
 * }} [options]
 *   The page's kind, an `.md` page having no import or export statement and no
 *   expression; what a component closed in its own tag is written out as, where
 *   it is not taken out; the value of a name the page prints; the scheme and
 *   host a link from the site's root is read against, none leaving it as it
 *   is; and the number of the page's line `text` opens on, for the message.
 * @returns {string} The prose, trimmed.
 */
export function stripMdx(
  text,
  { kind = 'mdx', expand = () => undefined, value = () => undefined, origin = '', firstLine = 1 } = {},
) {
  const shown = pageMarkup(text, { kind });
  const edits = [];
  const statements = [];
  if (kind === 'mdx') {
    for (const found of shown.matchAll(ESM)) statements.push([found.index, found.index + found[0].length]);
    for (const [start, end] of statements) edits.push([start, end, '']);
  }
  const inStatement = (at) => statements.some(([start, end]) => start <= at && at < end);
  for (const part of pageParts(text, { kind })) {
    if (part.what === 'comment') edits.push([part.start, part.end, '']);
    if (part.what !== 'expression' || inStatement(part.start)) continue;
    const written = text.slice(part.start, part.end);
    const name = NAME.exec(written)?.[1];
    const resolved = name === undefined ? undefined : value(name);
    if (resolved === undefined) {
      const line = text.slice(0, part.start).split('\n').length - 1 + firstLine;
      throw new Error(`line ${line} prints ${written}, which the Markdown copy cannot write as a value`);
    }
    edits.push([part.start, part.end, String(resolved)]);
  }
  for (const found of shown.matchAll(SELF_CLOSING)) {
    edits.push([found.index, found.index + found[0].length, expand(found[0]) ?? '']);
  }
  const taken = (at) => edits.some(([start, end]) => start <= at && at < end);
  for (const found of shown.matchAll(WRAPPER)) {
    if (!taken(found.index)) edits.push([found.index, found.index + found[0].length, '']);
  }
  if (origin) {
    for (const found of shown.matchAll(ROOT_RELATIVE)) {
      const at = found.index + found[1].length;
      if (!taken(at)) edits.push([at, at, origin]);
    }
  }
  edits.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  let kept = '';
  let done = 0;
  for (const [start, end, written] of edits) {
    if (start < done) continue;
    kept += text.slice(done, start) + written;
    done = end;
  }
  return closeUp(kept + text.slice(done), kind).trim();
}

/** `text` with each run of empty lines outside code closed up to one, on a page of `kind`. */
function closeUp(text, kind) {
  const lines = text.split('\n');
  const code = codeLines(lines, { kind });
  const blank = (index) => lines[index] === '' && !code[index];
  return lines.filter((_, index) => !(index > 0 && blank(index) && blank(index - 1))).join('\n');
}

/**
 * Text on one line, each run of the white space a browser collapses (spaces,
 * tabs and line breaks) one space. A no-break space stays: the page prints it,
 * as it prints the narrow one that groups the digits of `15 000`.
 */
const oneLine = (text) => text.replace(/[ \t\n\v\f\r]+/g, ' ').trim();

/**
 * Text a page prints as it is, written so that Markdown prints it as it is,
 * each character escaped that would open emphasis (a `*`, and a `_` that is
 * not inside a word), code, maths, strikethrough, a link or an image, a tag or
 * an autolink, or a table cell, or end the brackets of a link's text or an
 * image's alt. An `&` that opens a character reference is escaped too, so that
 * `&amp;` prints as written, except in the value of a component's attribute
 * (`attribute`): MDX reads the references of a value as Markdown reads them,
 * so they are left for the reader to read alike. A `_`, a `<` or an `&` at an
 * edge of the text is escaped whatever stands beyond it, since a fragment of a
 * citation is joined to the next one: `x <` before a link to `https://...`
 * would open an autolink.
 */
const escapeMarks = (text, attribute) => {
  const escaped = text
    .replace(/[\\`*~$[\]|]/g, '\\$&')
    .replace(/(?<![\p{L}\p{N}])_|_(?![\p{L}\p{N}])/gu, '\\_')
    .replace(/<(?=[A-Za-z/!?]|$)/g, '\\<');
  return attribute ? escaped : escaped.replace(/&(?=#\d+;|#[xX][\da-fA-F]+;|[A-Za-z][A-Za-z\d]*;|$)/g, '\\&');
};

/**
 * Text a page prints as it is, written for a link's text, an image's alt or a
 * run of prose: on one line ({@link oneLine}), its marks escaped as
 * `escapeMarks` says, with `attribute: true` for the value of a component's
 * attribute.
 *
 * @param {string} text
 * @param {{ attribute?: boolean }} [options]
 * @returns {string}
 */
export const literalText = (text, { attribute = false } = {}) => escapeMarks(oneLine(text), attribute);

/**
 * A fragment of a line, a part of a citation: {@link literalText} with the
 * space at its edges kept, which joins it to the next fragment.
 */
const fragmentText = (text) => escapeMarks(text.replace(/[ \t\n\v\f\r]+/g, ' '), false);

/**
 * Markdown written as a line of its own, a paragraph or the line under a list
 * item, with the mark that opens it escaped where it would open a heading, a
 * quotation, a list, a thematic break or a heading's underline.
 */
const lineStart = (markdown) =>
  markdown.replace(/^(?:([#>+=-])|(\d{1,9})([.)]))/, (_whole, mark, digits, delimiter) =>
    mark ? `\\${mark}` : `${digits}\\${delimiter}`,
  );

/**
 * The line a copy written from a page's source opens with: the page's title
 * as a heading, in {@link literalText}, with a closing run of `#` escaped,
 * which Markdown would take for the end of the heading's syntax.
 *
 * @param {string} title The page's title, from its frontmatter.
 * @returns {string}
 */
export const titleMarkdown = (title) => `# ${literalText(title).replace(/(^|[ \t])(#+)$/, '$1\\$2')}`;

/**
 * One item of the list of catalogues the copy writes for CatalogueIndex: the
 * catalogue's label linked to its page, then what it holds, each read from its
 * frontmatter and written in {@link literalText}.
 *
 * @param {{ label: string, url: string, description: string }} catalogue
 * @returns {string}
 */
export const catalogueItem = ({ label, url, description }) => `- [${literalText(label)}](${url}): ${literalText(description)}`;

/** One attribute of a component tag written as a string or as a number. */
function attribute(tag, name) {
  const found = tag.match(new RegExp(`\\b${name}=(?:"([^"]*)"|\\{\\s*(-?[\\d.]+)\\s*\\})`));
  return found ? (found[1] ?? found[2]) : undefined;
}

/** `figure.svg` with a suffix before its extension, as the components add one. */
const suffixed = (src, suffix) => src.replace(/(\.[A-Za-z0-9]+)$/, `${suffix}$1`);

/** Where Video.astro reads a clip from, by its name. */
const CLIPS = 'https://raw.githubusercontent.com/jmrplens/phonometry-assets/main/images';

/** Where ReportPreview.astro reads a fiche from, by its name. */
const FICHES = 'https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports';

/** The word the line of a clip and of a fiche opens with, in each language. */
const LEAD = { Video: { en: 'Video', es: 'Vídeo' }, ReportPreview: { en: 'Report', es: 'Informe' } };

/**
 * What the copy of a page written from its source does with each component a
 * page imports, besides the {@link DATA_COMPONENTS} of src/lib/page-markdown.mjs,
 * whose pages publish no copy: `written`, written out as Markdown here or by
 * the generator (the list of catalogues); `wrapper`, taken out with its
 * children kept, which are the page's own prose; `dropped`, taken out, being a
 * control or a script that shows nothing of its own (a picker over a table the
 * page also prints, a script that moves an old fragment to its new page).
 * scripts/page-markdown.test.mjs holds every component a page imports to one
 * of these, or to the data components, and each of them to a page.
 */
export const COMPONENT_READINGS = Object.freeze({
  CatalogueIndex: 'written',
  ReportPreview: 'written',
  ThemeImage: 'written',
  Video: 'written',
  Scope: 'wrapper',
  ScopeClaim: 'wrapper',
  SeeAlso: 'wrapper',
  CatalogueFinder: 'dropped',
  CatalogueRouter: 'dropped',
  ErrataRouter: 'dropped',
});

/**
 * A figure, a clip or a fiche as the copy writes it, or `undefined` for any
 * other tag.
 *
 * A figure (src/components/ThemeImage.astro) is an image: its alt, the text
 * written for a reader who cannot see it, and the address this site serves it
 * at, in the page's language as the component picks it, the light palette
 * alone. A clip (src/components/Video.astro) cannot be watched from text, and
 * a fiche (src/components/ReportPreview.astro) is a PDF, so each is a line:
 * its title linked to the clip or the PDF this site serves, then the
 * description written for a reader who cannot see it, and its caption, if it
 * has one, as a paragraph of its own. The italic caption a page writes under a
 * figure is prose and stays without help.
 *
 * @param {string} tag The tag as the page writes it.
 * @param {{ lang: 'en' | 'es', base: string }} where The page's language, and
 *   the address of the site the media are served under.
 * @returns {string | undefined}
 */
export function figureMarkdown(tag, { lang, base }) {
  const component = tag.match(/^<([A-Z][\w.]*)/)?.[1];
  if (component === 'ThemeImage') {
    const src = attribute(tag, 'src');
    const alt = attribute(tag, 'alt');
    if (!src || !alt) throw new Error(`a figure without its src or its alt: ${oneLine(tag)}`);
    const localised = lang === 'es' ? suffixed(src, '_es') : src;
    return `![${literalText(alt, { attribute: true })}](${mediaUrl(localised, base)})`;
  }
  if (component === 'Video' || component === 'ReportPreview') {
    const name = attribute(tag, 'name');
    const title = attribute(tag, 'title');
    if (!name || !title) throw new Error(`a clip or a fiche without its name or its title: ${oneLine(tag)}`);
    const url =
      component === 'Video'
        ? mediaUrl(`${CLIPS}/${name}${lang === 'es' ? '_es' : ''}.webm`, base)
        : mediaUrl(`${FICHES}/${name}.pdf`, base);
    const description = attribute(tag, 'description');
    const caption = attribute(tag, 'caption');
    const written = description ? `: ${literalText(description, { attribute: true })}` : '';
    const line = `**${LEAD[component][lang]}:** [${literalText(title, { attribute: true })}](${url})${written}`;
    return caption ? `${line}\n\n${lineStart(literalText(caption, { attribute: true }))}` : line;
  }
  return undefined;
}

/**
 * A link's destination as Markdown reads it: wrapped in `<...>` when it holds
 * a space or a parenthesis, which would end it early.
 */
const destination = (url) => (/[\s()<>]/.test(url) ? `<${url.replaceAll('<', '%3C').replaceAll('>', '%3E')}>` : url);

/** One fragment of a citation as Markdown: a bare URL stays bare, a title in italics, a link around what it carries. */
function partMarkdown(part) {
  if (part.href && part.text === part.href) return part.href;
  const text = fragmentText(part.text);
  const marked = part.italic && text.trim() ? `*${text}*` : text;
  return part.href ? `[${marked}](${destination(part.href)})` : marked;
}

/**
 * The References section of a page as its layout prints it
 * (src/components/References.astro), in the words of the same module
 * (src/lib/references-format.mjs): one item per entry in the order the page
 * prints them, its author and year in bold, its note on the line under it.
 *
 * @param {readonly import('../../src/lib/references-format.mjs').Reference[] | undefined} references
 *   The frontmatter's list.
 * @param {'en' | 'es'} lang
 * @param {string} heading The section's heading in the page's language.
 * @returns {string} Markdown, or `''` for a page that cites nothing.
 */
export function referencesMarkdown(references, lang, heading) {
  if (!references?.length) return '';
  const entries = sortedReferences(references, lang).map(([, ref]) => {
    const citation = citationParts(ref).map(partMarkdown).join('');
    const note = ref.note ? `\n  ${lineStart(noteParts(ref.note).map(partMarkdown).join('').trim())}` : '';
    return `- **${fragmentText(opening(ref, lang))}**${citation.trimEnd()}${note}`;
  });
  return `## ${heading}\n\n${entries.join('\n')}`;
}

/**
 * The text Markdown prints for the content of an ATX heading line, read on its
 * own for {@link copyDefects}: a closing run of `#` taken off as Markdown
 * takes it off, and each backslash escape of an ASCII punctuation character
 * read as that character. A character {@link literalText} escapes that stands
 * unescaped could be read as markup, so the line then reads as nothing
 * (`undefined`).
 *
 * @param {string} written What follows `# ` on the line.
 * @returns {string | undefined}
 */
function headingText(written) {
  const content = written.replace(/(^|[ \t])#+[ \t]*$/, '$1').trim();
  let text = '';
  for (let at = 0; at < content.length; at += 1) {
    const char = content[at];
    const next = content[at + 1] ?? '';
    if (char === '\\' && /[!-/:-@[-`{-~]/.test(next)) {
      text += next;
      at += 1;
      continue;
    }
    const before = content[at - 1] ?? '';
    const word = (c) => /[\p{L}\p{N}]/u.test(c);
    if (
      /[\\`*~$[\]|]/.test(char) ||
      (char === '_' && !(word(before) && word(next))) ||
      (char === '<' && /[A-Za-z/!?]/.test(next)) ||
      (char === '&' && /^&(?:#\d+|#[xX][\da-fA-F]+|[A-Za-z][A-Za-z\d]*);/.test(content.slice(at)))
    ) {
      return undefined;
    }
    text += char;
  }
  return text;
}

/** `text` with the characters a regular expression reads as syntax escaped. */
const literal = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** The text of a link or of an image's alt, one character at least, its escapes in. */
const BRACKETED = String.raw`(?:\\.|[^\\\]\n])+`;

/**
 * What the copy prints for each component {@link COMPONENT_READINGS} marks
 * `written`, as {@link copyDefects} finds it in the copy: a figure is an image
 * with an alt, of a file the site serves; a clip and a fiche a line that opens
 * on its word in either language and links the clip or the PDF the site
 * serves; the list of catalogues one item per catalogue, linked to its page and
 * followed by what it holds. Each is read from the copy as written, never from
 * figureMarkdown or the emitter, and `noun` names it in a message. A page may
 * link a catalogue in a list of its own, so the items of the list of
 * catalogues are counted only on a page that renders one (`listed`).
 * scripts/page-markdown.test.mjs holds the keys to the `written` readings, so a
 * component the copy writes out cannot go unchecked.
 */
export const COPY_FORMS = Object.freeze({
  ThemeImage: {
    noun: ['figure', 'figures'],
    pattern: (site) => new RegExp(String.raw`!\[${BRACKETED}\]\(${literal(site)}/media/[^)\s]+\)`, 'g'),
  },
  Video: {
    noun: ['clip', 'clips'],
    pattern: (site) =>
      new RegExp(String.raw`\*\*(?:Video|Vídeo):\*\* \[${BRACKETED}\]\(${literal(site)}/media/[^)\s]+\.webm\)`, 'g'),
  },
  ReportPreview: {
    noun: ['fiche', 'fiches'],
    pattern: (site) =>
      new RegExp(String.raw`\*\*(?:Report|Informe):\*\* \[${BRACKETED}\]\(${literal(site)}/media/[^)\s]+\.pdf\)`, 'g'),
  },
  CatalogueIndex: {
    noun: ['catalogue', 'catalogues'],
    listed: true,
    pattern: (site) =>
      new RegExp(String.raw`^- \[${BRACKETED}\]\(${literal(site)}/(?:es/)?reference/catalogues/[\w-]+/\): \S`, 'gm'),
  },
});

/**
 * What a copy written from a page's source misses of the page, one sentence
 * each, or nothing when it misses nothing.
 *
 * Each is read from the copy as written and from the source on its own, never
 * through the reading that wrote the copy, so a writer that goes wrong cannot
 * pass by agreeing with itself:
 *
 * - the copy opens with a heading that prints the page's title, a mark of
 *   the title escaped (headingText);
 * - it holds no comment outside its code;
 * - it holds no link from the site's root outside its code, in any syntax: the
 *   site's base path where no host comes before it;
 * - no name the page imports and prints is left in an expression outside its
 *   code;
 * - it prints a figure, a clip and a fiche for each one the page renders, and
 *   every catalogue for each list of them, in the forms {@link COPY_FORMS}
 *   reads;
 * - every line of the page's code is in it, as many times as the page has it;
 * - a page that cites works ends with a section holding one entry per work,
 *   and every DOI among them.
 *
 * @param {string} copy The copy as written, without the lines above its title.
 * @param {{
 *   source: string,
 *   kind: 'md' | 'mdx',
 *   title: string,
 *   references?: readonly { doi?: string }[],
 *   heading: string,
 *   site: string,
 *   catalogues?: number,
 *   firstLine?: number,
 * }} page
 *   The page's source with its frontmatter out, its kind, its title and the
 *   works it cites, the heading of its References section, the address of the
 *   site with its base path (`https://docs.jmrp.io/phonometry`), how many
 *   catalogues a list of them holds in the page's language, and the number of
 *   the page's line `source` opens on, for the messages.
 * @returns {string[]}
 */
export function copyDefects(copy, { source, kind, title, references = [], heading, site, catalogues = 0, firstLine = 1 }) {
  const defects = [];
  const first = copy.slice(0, copy.indexOf('\n') === -1 ? copy.length : copy.indexOf('\n'));
  if (!first.startsWith('# ') || headingText(first.slice(2)) !== oneLine(title)) {
    defects.push(`it opens with ${JSON.stringify(first)}, not with the page's title`);
  }
  const parts = pageParts(copy, { kind: 'md' });
  for (const part of parts.filter(({ what }) => what === 'comment')) {
    defects.push(`it keeps the comment ${JSON.stringify(oneLine(copy.slice(part.start, part.end)).slice(0, 80))}`);
  }
  const shown = pageMarkup(copy, { kind: 'md' });
  if (shown.includes('{/*')) defects.push('it keeps a comment of the page written as {/* */}');
  // The site's base path opening a path where no host or path comes before it:
  // a link from the root in any syntax, a Markdown link, a definition, an
  // attribute quoted or not, or a bare address. An address on this site or on
  // another host (github.com/jmrplens/phonometry/...) has a character of its
  // own before the base path.
  const basePath = new URL(site).pathname.replace(/\/$/, '');
  const rooted = new Set();
  for (const found of shown.matchAll(ROOT_RELATIVE)) rooted.add(found.index + found[1].length);
  if (basePath) {
    for (const found of shown.matchAll(new RegExp(String.raw`(?<![\w.~%/-])${literal(basePath)}/`, 'g'))) rooted.add(found.index);
  }
  for (const at of [...rooted].sort((a, b) => a - b)) {
    const start = copy.lastIndexOf('\n', at - 1) + 1;
    const end = copy.indexOf('\n', at);
    const line = copy.slice(start, end === -1 ? copy.length : end);
    const column = at - start;
    defects.push(`it links ${JSON.stringify(line.slice(Math.max(0, column - 40), column + 60))} from the site's root`);
  }
  if (kind === 'mdx') {
    for (const name of pageImports(source).keys()) {
      if (new RegExp(String.raw`\{[^{}]*(?<![\w$])${literal(name)}(?![\w$])[^{}]*\}`).test(shown)) {
        defects.push(`it prints {${name}} where the page prints its value`);
      }
    }
    const rendered = pageMarkup(source, { kind });
    for (const [component, { noun, pattern, listed = false }] of Object.entries(COPY_FORMS)) {
      const tags = (rendered.match(new RegExp(String.raw`<${component}\b`, 'g')) ?? []).length;
      if (listed && tags === 0) continue;
      const expected = tags * (listed ? catalogues : 1);
      const written = (shown.match(pattern(site)) ?? []).length;
      if (written !== expected) {
        const verb = listed ? 'lists' : 'renders';
        defects.push(`it writes ${written} of the ${expected} ${noun[expected === 1 ? 0 : 1]} the page ${verb}`);
      }
    }
  }
  const sourceLines = source.split('\n');
  const code = codeLines(sourceLines, { kind });
  const kept = new Map();
  for (const line of copy.split('\n')) kept.set(line, (kept.get(line) ?? 0) + 1);
  for (const [index, line] of sourceLines.entries()) {
    if (!code[index] || line.trim() === '') continue;
    const left = kept.get(line) ?? 0;
    if (left === 0) {
      defects.push(`it lost line ${index + firstLine} of the page's code, ${JSON.stringify(line.trim().slice(0, 60))}`);
    }
    else kept.set(line, left - 1);
  }
  if (references.length) {
    const at = copy.indexOf(`\n## ${heading}\n`);
    const entries = at === -1 ? 0 : (copy.slice(at).match(/^- \*\*/gm) ?? []).length;
    if (entries !== references.length) {
      const works = `${references.length} work${references.length === 1 ? '' : 's'}`;
      defects.push(`its ${heading} section holds ${entries} entr${entries === 1 ? 'y' : 'ies'}, and the page cites ${works}`);
    }
    for (const { doi } of references) {
      if (doi && !copy.includes(`https://doi.org/${doi}`)) defects.push(`it leaves out the DOI ${doi}`);
    }
  }
  return defects;
}
