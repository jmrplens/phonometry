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
 * One table cell: whitespace flattened to single spaces, pipes escaped.
 *
 * @param {CellValue} value
 * @returns {string}
 */
export function cell(value) {
  return String(value ?? '')
    .replaceAll(/\s+/gu, ' ')
    .replaceAll('|', String.raw`\|`)
    .trim();
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
  return (value ?? '').replaceAll(/\s+/gu, ' ').trim();
}

/**
 * Data that is plain text, not Markdown, made safe to print as Markdown: on
 * one line, with the characters that would turn part of it into something
 * else escaped. A transcribed table prints `200 mm CMU*` and `~0,65 to
 * 0,68`; written raw, two asterisks in one cell would italicize the words
 * between them, two tildes would strike them through, a `$` would open
 * maths, a backtick code and a `<` before a letter a tag.
 *
 * Strings a page or a data module holds as Markdown (with TeX in `$...$`, as
 * the glossary does) must not go through this: their markup is meant.
 *
 * @param {string | undefined | null} value
 * @returns {string}
 */
export function plainText(value) {
  return line(value)
    .replaceAll(/([\\`*~$])/gu, String.raw`\$1`)
    .replaceAll(/<(?=[A-Za-z/!?])/gu, String.raw`\<`);
}

/**
 * Text for the inside of `[...]`, a link's text or an image's alt: on one
 * line, with the brackets that would end it and the pipe that would split a
 * table cell escaped.
 *
 * @param {string | undefined | null} value
 * @returns {string}
 */
export function bracketText(value) {
  return line(value).replaceAll(/([\\[\]|])/gu, String.raw`\$1`);
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
