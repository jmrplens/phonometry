// What the site checks read in the prose of a page, apart from the checks.
//
// check-i18n-parity.mjs and check-math-render.mjs read every page of the site
// when they are loaded and exit with its verdict, so nothing can call them on
// one page; the two readings they make of a page are here, where a test can.
// Both step over the code first: a fenced block, then the inline spans, read
// as the site reads them (markdown-spans.mjs), each span leaving a mark that
// keeps the text either side of it apart, as the page shows it apart.

import { pastMarks, prose } from '../../src/lib/markdown-fences.mjs';
import { dropInlineSpans, dropInlineSpansByBlock, SPAN_MARK } from './markdown-spans.mjs';

/**
 * A backslash and the ASCII punctuation character it escapes (CommonMark 2.4),
 * read left to right, so that `\\` is one escaped backslash and the
 * character after it is not escaped.
 */
const ESCAPE = /\\[!-\/:-@[-`{-~]/g;

/**
 * `text` with each backslash escape taken out, a mark left in its place: the
 * page shows the character as written, and it opens nothing, an image, a tag
 * or a display delimiter.
 *
 * @param {string} text Prose, its code already out.
 * @returns {string} The prose with nothing escaped left in it.
 */
function dropEscapes(text) {
  return text.replace(ESCAPE, SPAN_MARK);
}

/**
 * A line that opens a raw HTML block of type 6 (CommonMark 4.6): one of the
 * block tags, opening or closing, whatever follows it on the line. It may
 * interrupt a paragraph.
 */
const HTML_BLOCK_TAG = new RegExp(
  '^ {0,3}</?(?:address|article|aside|base|basefont|blockquote|body|caption|center|col|' +
    'colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|' +
    'frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|' +
    'nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|' +
    'tfoot|th|thead|title|tr|track|ul)(?:[\\s/>]|$)',
  'i',
);

/**
 * A line that opens a raw HTML block of type 7: any other complete tag,
 * opening or closing, alone on its line. It cannot interrupt a paragraph.
 */
const HTML_LONE_TAG =
  /^ {0,3}(?:<[A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z_:][\w.:-]*(?:\s*=\s*(?:[^\s"'=<>`]+|'[^']*'|"[^"]*"))?)*\s*\/?>|<\/[A-Za-z][A-Za-z0-9-]*\s*>)\s*$/;

/** Whether a line opens a raw HTML block of a `.md` page, after `previous`. */
function opensHtmlBlock(line, previous) {
  return HTML_BLOCK_TAG.test(line) || (!previous.trim() && HTML_LONE_TAG.test(line));
}

/** An HTML image: a tag named `img` in any case, its name ending there. */
const HTML_IMAGE = /<img(?=[\s/>])/i;

/** A markdown image written inline: `![alt](src)`. */
const INLINE_IMAGE = /!\[[^\]]*\]\(/;

/** A markdown image by reference: `![alt][label]`, `![alt][]` or `![label]`. */
const REFERENCE_IMAGE = /!\[([^\]]*)\](?:\[([^\]]*)\])?(?![[(])/g;

/** A link reference definition, `[label]: destination`, at the start of a line. */
const DEFINITION = /^ {0,3}\[([^\]]+)\]:/gm;

/** A label as CommonMark matches one: case folded, inner whitespace one space. */
function normalised(label) {
  return label.trim().replace(/\s+/g, ' ').toLowerCase();
}

/**
 * `source` with its escapes taken out, but on the lines of a raw HTML block
 * of a `.md` page, which the page shows as written, backslash and all.
 *
 * @param {string} source Prose, its code out, as many lines as the page.
 * @param {boolean} mdx Whether the page is MDX, where a backslash escapes
 *   inside a tag's text as anywhere else.
 */
function shownEscapes(source, mdx) {
  if (mdx) return dropEscapes(source);
  let raw = false;
  let previous = '';
  return source
    .split('\n')
    .map((line) => {
      if (!line.trim()) raw = false;
      else if (!raw && opensHtmlBlock(line, previous)) raw = true;
      previous = line;
      return raw ? line : dropEscapes(line);
    })
    .join('\n');
}

/**
 * Whether a page writes a figure of its own, as markdown or as HTML.
 *
 * A markdown image written inline, `![alt](src)`, is one wherever it stands.
 * One by reference, `![alt][label]`, `![alt][]` or the shortcut `![label]`,
 * is one only when the page defines its label: CommonMark shows one whose
 * label nothing defines as the text it is. An HTML image is a tag named
 * `img` in any case of its letters, as HTML reads a tag's name, and not a
 * longer name such as `img-card`. A backslash before the `!` or the `<`
 * shows it and opens neither, but on the lines of a raw HTML block of a
 * `.md` page, which go out as written: a block tag opens one wherever it
 * stands, with anything after it, and any other tag only alone on its line
 * after a blank one (CommonMark 4.6, types 6 and 7). A comment, HTML or MDX,
 * shows nothing, and is read with the code spans over the lines of their
 * block, as the page reads them, whichever opens first winning.
 *
 * @param {string} markdown The page, as written.
 * @param {{ mdx?: boolean }} [options] Whether the page is MDX (`.mdx`).
 * @returns {boolean} Whether a figure is written outside any code.
 */
export function authorsFigure(markdown, { mdx = false } = {}) {
  const spoken = dropInlineSpansByBlock(prose(markdown), '`', { comments: mdx ? 'mdx' : 'md' });
  const source = shownEscapes(spoken, mdx);
  if (INLINE_IMAGE.test(source) || HTML_IMAGE.test(source)) return true;
  const defined = new Set(Array.from(source.matchAll(DEFINITION), (m) => normalised(m[1])));
  for (const match of source.matchAll(REFERENCE_IMAGE)) {
    const label = match[2] ? match[2] : match[1];
    if (defined.has(normalised(label))) return true;
  }
  return false;
}

/**
 * The lines of a page as the maths check reads them: code spans and
 * comments out, read over the lines of their block, each line where it was.
 *
 * @param {string[]} lines The lines of a page.
 * @param {boolean[]} code Whether each line is inside a fenced block.
 * @param {{ mdx?: boolean }} [options] Whether the page is MDX (`.mdx`).
 * @returns {string[]} The lines, a fenced one left blank.
 */
export function shownLines(lines, code, { mdx = false } = {}) {
  const prose = lines.map((line, index) => (code[index] ? '' : line)).join('\n');
  return dropInlineSpansByBlock(prose, '`', { comments: mdx ? 'mdx' : 'md' }).split('\n');
}

/**
 * The prose of a line that carries a display-maths delimiter beside content.
 *
 * `$$` alone on its line opens or closes a display, and is fine. A line that
 * starts with `$$` and holds no other `$` opens a display with something
 * after the delimiter, which the parser does not read as maths. Any other
 * line is a paragraph, where `$$` pairs as inline maths (micromark's math
 * flow refuses a `$` after its opening run): it is fine when its delimiters
 * pair, an even count, and a line that writes a third `$$` after a complete
 * pair leaves one open. Prose that talks about `$$` writes it in a code span.
 * The marks of a quotation or a list item are not the line's text, so what
 * stands behind them is what is read.
 *
 * @param {string} line One line of a page, outside any fenced block.
 * @returns {string | null} The line's prose, trimmed, or `null` when it is fine.
 */
export function strayDelimiter(line) {
  const trimmed = dropInlineSpans(line).trim();
  const shown = dropEscapes(pastMarks(trimmed).rest).trim();
  const delimiters = shown.match(/\$\$/g)?.length ?? 0;
  if (!delimiters) return null;
  if (shown === '$$') return null;
  const opensDisplay = /^\${2,}[^$]*$/.test(shown);
  return opensDisplay || delimiters % 2 === 1 ? trimmed : null;
}
