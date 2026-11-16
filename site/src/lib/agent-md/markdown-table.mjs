/**
 * Markdown table, list and escaping primitives the writers share.
 *
 * Several writers write tables (the home's coverage table, the raw `<table>`
 * rule), and a table cell has two structural characters a value can carry by
 * accident: a newline ends the row and an unescaped `|` starts a new column.
 * Link text, image alt text and HTML attributes have their own characters
 * that end them early. Escaping each in one place means no writer can forget
 * one.
 *
 * The whitespace pattern is one class with a plus, never a starred class on
 * both sides of a newline: the second form can split a run of blank lines in
 * many ways and backtracks super-linearly on input an author controls.
 *
 * @module
 */
import { codeLines } from '../markdown-fences.mjs';

/** @typedef {string | number | boolean | null | undefined} CellValue */

/**
 * The whitespace a line can break at, as Markdown reads it: space, tab and
 * the line endings.
 *
 * Not `\s`, which also matches the no-break spaces the pages write on
 * purpose: the narrow one that groups a number's digits (U+202F) and the one
 * that ties a value to its unit (U+00A0). Folded into plain spaces, they left
 * a number a line could break inside.
 */
const SPACES = /[ \t\n\v\f\r]+/gu;

/**
 * Text on one line: each run of {@link SPACES} becomes one space, and none is
 * left at either end. The no-break spaces stay where they are, ends included.
 *
 * @param {string} text
 * @returns {string}
 */
const flatten = (text) => text.replaceAll(SPACES, ' ').replace(/^ /u, '').replace(/ $/u, '');

/**
 * One table cell: whitespace flattened to single spaces, pipes escaped. A pipe
 * a child writer has escaped already (an image whose alt text holds one) keeps
 * its one backslash: escaping it again would leave the backslash escaped and
 * the pipe bare, and split the cell.
 *
 * @param {CellValue} value
 * @returns {string}
 */
export function cell(value) {
  return flatten(String(value ?? '')).replace(/(\\*)\|/gu, (match, slashes) => (slashes.length % 2 === 1 ? match : `${slashes}\\|`));
}

/**
 * A Markdown table from a header row and body rows.
 *
 * A row shorter than the header is padded with empty cells, so a missing
 * value cannot shift the columns after it.
 *
 * @param {CellValue[]} head  Header labels.
 * @param {CellValue[][]} body  Rows.
 * @returns {string}  The table, without a trailing newline.
 */
export function table(head, body) {
  const width = head.length;
  const row = (values) =>
    `| ${Array.from({ length: width }, (_, i) => cell(values[i])).join(' | ')} |`;
  return [row(head), `| ${head.map(() => '---').join(' | ')} |`, ...body.map(row)].join('\n');
}

/**
 * A value collapsed to one line, for a list item or a bold label.
 *
 * Same flattening as {@link cell} without the pipe escaping, which outside a
 * table would only show the reader a stray backslash.
 *
 * @param {string | undefined | null} value
 * @returns {string}
 */
export function line(value) {
  return flatten(value ?? '');
}

/**
 * Text a page prints as it is, written so that Markdown prints it as it is:
 * each character escaped that would open emphasis (a `*`, and a `_` that is
 * not inside a word), code, maths, strikethrough, a link or an image, a tag or
 * an autolink, or end the brackets of a link's text or an image's alt, and an
 * `&` that opens a character reference, so that `&amp;` prints as written. A
 * `_`, a `<` or an `&` at an edge of the text is escaped whatever stands
 * beyond it, since the text is joined to what the writer puts after it. A `|`
 * is escaped when `pipe` is set, the default.
 *
 * The values of a component's attributes reach the writers as the MDX parser
 * decodes them, character references read, so they take this form too: the
 * text is the one the page prints.
 *
 * @param {string} text
 * @param {{ pipe?: boolean }} [options]
 * @returns {string}
 */
export const escapeMarks = (text, { pipe = true } = {}) =>
  text
    .replaceAll(pipe ? /[\\`*~$[\]|]/gu : /[\\`*~$[\]]/gu, String.raw`\$&`)
    .replaceAll(/(?<![\p{L}\p{N}])_|_(?![\p{L}\p{N}])/gu, String.raw`\_`)
    .replaceAll(/<(?=[A-Za-z/!?]|$)/gu, String.raw`\<`)
    .replaceAll(/&(?=#\d+;|#[xX][\da-fA-F]+;|[A-Za-z][A-Za-z\d]*;|$)/gu, String.raw`\&`);

/**
 * Text a page prints as it is, written for a link's text, an image's alt or a
 * run of prose: on one line ({@link line}), its marks escaped as
 * {@link escapeMarks} says, the pipe that would split a table cell and the
 * brackets that would end a link's text among them.
 *
 * @param {string | undefined | null} value
 * @returns {string}
 */
export function literalText(value) {
  return escapeMarks(line(value));
}

/**
 * A fragment of a line, a part of a citation: {@link literalText} with the
 * space at its edges kept, since a citation is printed fragment by fragment
 * and the spaces between fragments are the fragments' own. Each run of the
 * white space a browser collapses is one space; a no-break space stays.
 *
 * @param {string} text
 * @returns {string}
 */
export function fragmentText(text) {
  return escapeMarks(text.replaceAll(/[ \t\n\v\f\r]+/gu, ' '));
}

/**
 * The line a copy opens with: the page's title as a heading, in
 * {@link literalText}, with a closing run of `#` escaped, which Markdown would
 * take for the end of the heading's syntax.
 *
 * @param {string} title
 * @returns {string}
 */
export function titleMarkdown(title) {
  return `# ${literalText(title).replace(/(^|[ \t])(#+)$/u, String.raw`$1\$2`)}`;
}

/**
 * Data that is plain text, not Markdown, made safe to print as Markdown: a
 * table cell or a note of a transcribed table, which prints `200 mm CMU*` and
 * “~0,65 to 0,68”; written raw, two asterisks in one cell would italicize the
 * words between them, two tildes would strike them through, a `$` would open
 * maths, a backtick code and a `<` before a letter a tag. It is
 * {@link literalText} with the pipe left to {@link cell}, which escapes it in
 * a table, where it splits a cell.
 *
 * Strings a page or a data module holds as Markdown (with TeX in `$...$`, as
 * the glossary does) must not go through this: their markup is meant.
 *
 * @param {string | undefined | null} value
 * @returns {string}
 */
export function plainText(value) {
  return escapeMarks(line(value), { pipe: false });
}

/**
 * Markdown written as a line of its own, a paragraph or the line under a list
 * item, with the mark that opens it escaped where it would open a heading, a
 * quotation, a list, a thematic break or a heading's underline.
 *
 * @param {string} markdown
 * @returns {string}
 */
export function lineStart(markdown) {
  return markdown.replace(/^(?:([#>+=-])|(\d{1,9})([.)]))/u, (_whole, mark, digits, delimiter) =>
    mark ? `\\${mark}` : `${digits}\\${delimiter}`,
  );
}

/**
 * Text for a double-quoted HTML attribute.
 *
 * @param {string | undefined | null} value
 * @returns {string}
 */
export function htmlAttribute(value) {
  return line(value)
    .replaceAll('&', '&amp;')
    .replaceAll('"', '&quot;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}

/**
 * A list item whose body may run to several blocks.
 *
 * The lead (a bold label) and the first paragraph share the bullet's line;
 * every following line is indented under the bullet so a second paragraph,
 * a nested list or a fenced block stays inside the item. A body that opens
 * with a block of its own (a list, a fence, display maths, a table) starts on
 * the line after the lead, where it can still be read as that block.
 *
 * @param {string} lead
 * @param {string} body  Markdown, already written.
 * @returns {string}
 */
export function listItem(lead, body) {
  const blocks = body.trim();
  if (!blocks) return `- ${lead}`;
  const indent = (text) =>
    text
      .split('\n')
      .map((one) => (one.trim() === '' ? '' : `  ${one}`))
      .join('\n');
  const opensBlock =
    /^(?:[-*+] |\d+[.)] |\$\$|\||#{1,6} |>)/u.test(blocks) || codeLines([blocks.split('\n')[0]])[0];
  if (opensBlock) {
    return `- ${lead}\n\n${indent(blocks)}`;
  }
  const [first, ...rest] = blocks.split('\n');
  return rest.length > 0 ? `- ${lead} ${first}\n${indent(rest.join('\n'))}` : `- ${lead} ${first}`;
}
