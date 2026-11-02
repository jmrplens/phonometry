// What the site checks read in the prose of a page, apart from the checks.
//
// check-i18n-parity.mjs and check-math-render.mjs read every page of the site
// when they are loaded and exit with its verdict, so nothing can call them on
// one page; the two readings they make of a page are here, where a test can.
// Both step over the code first: a fenced block, then the inline spans, read
// as the site reads them (markdown-spans.mjs), each span leaving a mark that
// keeps the text either side of it apart, as the page shows it apart.

import { prose } from '../../src/lib/markdown-fences.mjs';
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
 * Whether a line opens a raw HTML block of a `.md` page (CommonMark 4.6): a
 * tag, opening or closing, at the start of a block. Its lines go to the page
 * as they are written, a backslash in them included.
 */
const HTML_BLOCK = /^ {0,3}<\/?[A-Za-z]/;

/** An HTML comment, and an MDX one: a sample or a note, never markup shown. */
const COMMENTS = { md: /<!--[\s\S]*?-->/g, mdx: /<!--[\s\S]*?-->|\{\/\*[\s\S]*?\*\/\}/g };

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
      else if (!previous.trim() && HTML_BLOCK.test(line)) raw = true;
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
 * `.md` page, which go out as written. A comment, HTML or MDX, shows
 * nothing. Code spans are read over the lines of their block, as the page
 * reads them.
 *
 * @param {string} markdown The page, as written.
 * @param {{ mdx?: boolean }} [options] Whether the page is MDX (`.mdx`).
 * @returns {boolean} Whether a figure is written outside any code.
 */
export function authorsFigure(markdown, { mdx = false } = {}) {
  const spoken = dropInlineSpansByBlock(prose(markdown));
  const source = shownEscapes(spoken, mdx).replace(COMMENTS[mdx ? 'mdx' : 'md'], SPAN_MARK);
  if (INLINE_IMAGE.test(source) || HTML_IMAGE.test(source)) return true;
  const defined = new Set(Array.from(source.matchAll(DEFINITION), (m) => normalised(m[1])));
  for (const match of source.matchAll(REFERENCE_IMAGE)) {
    const label = match[2] ? match[2] : match[1];
    if (defined.has(normalised(label))) return true;
  }
  return false;
}

/**
 * The lines of a page as the maths check reads them: code spans out, read
 * over the lines of their block, each line where it was.
 *
 * @param {string[]} lines The lines of a page.
 * @param {boolean[]} code Whether each line is inside a fenced block.
 * @returns {string[]} The lines, a fenced one left blank.
 */
export function shownLines(lines, code) {
  const prose = lines.map((line, index) => (code[index] ? '' : line)).join('\n');
  return dropInlineSpansByBlock(prose).split('\n');
}

/**
 * The prose of a line that carries a display-maths delimiter beside content.
 *
 * Inline `$$...$$` complete on one line is fine, and so is `$$` alone on its
 * line; what breaks the parser is a block that opens or closes on a line that
 * carries anything else, a line that writes a third `$$` after a complete
 * pair among them. Prose that talks about `$$` writes it in a code span.
 *
 * @param {string} line One line of a page, outside any fenced block.
 * @returns {string | null} The line's prose, trimmed, or `null` when it is fine.
 */
export function strayDelimiter(line) {
  const trimmed = dropInlineSpans(line).trim();
  const shown = dropEscapes(trimmed);
  const delimiters = shown.match(/\$\$/g)?.length ?? 0;
  if (!delimiters) return null;
  const only = shown === '$$';
  const complete =
    delimiters === 2 && shown.startsWith('$$') && shown.endsWith('$$') && shown.length > 4;
  return only || complete ? null : trimmed;
}
