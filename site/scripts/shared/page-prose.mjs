// What the site checks read in the prose of a page, apart from the checks.
//
// check-i18n-parity.mjs and check-math-render.mjs read every page of the site
// when they are loaded and exit with its verdict, so nothing can call them on
// one page; the two readings they make of a page are here, where a test can.
// Both step over the code first: a fenced block, then the inline spans, read
// as the site reads them (markdown-spans.mjs), each span leaving a mark that
// keeps the text either side of it apart, as the page shows it apart.

import { codeLines, pageLines, splitLines } from '../../src/lib/markdown-fences.mjs';
import { dropInlineSpans, dropInlineSpansByBlock, linkLabel, pageDefinitions, SPAN_MARK } from './markdown-spans.mjs';

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

/** The lines of a raw HTML block of a `.md` page, which go out as written. */
const RAW_ROLES = new Set(['html', 'raw']);

/** An HTML image: a tag named `img` in any case, its name ending there. */
const HTML_IMAGE = /<img(?=[\s/>])/i;

/** A markdown image written inline: `![alt](src)`. */
const INLINE_IMAGE = /!\[[^\]]*\]\(/;

/** A markdown image by reference: `![alt][label]`, `![alt][]` or `![label]`. */
const REFERENCE_IMAGE = /!\[([^\]]*)\](?:\[([^\]]*)\])?(?![[(])/g;

/**
 * Whether a page writes a figure of its own, as markdown or as HTML.
 *
 * A markdown image written inline, `![alt](src)`, is one wherever it stands.
 * One by reference, `![alt][label]`, `![alt][]` or the shortcut `![label]`,
 * is one only when the page defines its label: CommonMark shows one whose
 * label nothing defines as the text it is, and a definition is one only where
 * the walk of the page reads one, opening a paragraph and alone on its lines
 * (`pageDefinitions` of markdown-spans.mjs). An HTML image is a tag named
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
  const kind = mdx ? 'mdx' : 'md';
  const lines = splitLines(markdown);
  const code = codeLines(lines, { kind });
  const read = pageLines(lines, { kind });
  const source = shownLines(lines, code, { mdx })
    .map((line, index) => (RAW_ROLES.has(read[index].role) ? line : dropEscapes(line)))
    .join('\n');
  if (INLINE_IMAGE.test(source) || HTML_IMAGE.test(source)) return true;
  const defined = pageDefinitions(read, { kind });
  for (const match of source.matchAll(REFERENCE_IMAGE)) {
    const label = match[2] ? match[2] : match[1];
    const line = source.slice(0, match.index).split('\n').length - 1;
    if (defined.at(line).has(linkLabel(label))) return true;
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
  return dropInlineSpansByBlock(lines.join('\n'), '`', { comments: mdx ? 'mdx' : 'md' })
    .split('\n')
    .map((line, index) => (code[index] ? '' : line));
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
 * stands behind them is what is read: the walk of the page says which marks those
 * are, an ordered marker other than 1 under a paragraph being the paragraph's text.
 *
 * @param {string} line One line of a page, outside any fenced block.
 * @param {string} [rest] What the walk of the page leaves of the line past its
 *   containers; with none, the line is read as a page of its own.
 * @returns {string | null} The line's prose, trimmed, or `null` when it is fine.
 */
export function strayDelimiter(line, rest) {
  const trimmed = dropInlineSpans(line).trim();
  const past = rest ?? pageLines([trimmed])[0].rest;
  const shown = dropEscapes(past).trim();
  const delimiters = shown.match(/\$\$/g)?.length ?? 0;
  if (!delimiters) return null;
  if (shown === '$$') return null;
  const opensDisplay = /^\${2,}[^$]*$/.test(shown);
  return opensDisplay || delimiters % 2 === 1 ? trimmed : null;
}
