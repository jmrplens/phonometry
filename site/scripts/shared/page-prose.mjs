// What the site checks read in the prose of a page, apart from the checks.
//
// check-i18n-parity.mjs and check-math-render.mjs read every page of the site
// when they are loaded and exit with its verdict, so nothing can call them on
// one page; the two readings they make of a page are here, where a test can.
// Both step over the code first: a fenced block, then the inline spans, read
// as the site reads them (markdown-spans.mjs), each span leaving a mark that
// keeps the text either side of it apart, as the page shows it apart.

import { prose } from '../../src/lib/markdown-fences.mjs';
import { dropInlineSpans, dropInlineSpansByLine, SPAN_MARK } from './markdown-spans.mjs';

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
 * Whether a page writes a figure of its own, as markdown or as HTML.
 *
 * Every markdown image opens with the same two characters, whatever comes
 * after them: the inline `![alt](src)`, the two reference forms `![alt][label]`
 * and `![alt][]`, and the shortcut `![label]` whose target is a link definition
 * somewhere else in the file. Matching what opens all four is both shorter and
 * complete, and prose has no other use for the sequence once code is out. An
 * HTML image is a tag named `img` in any case of its letters, as HTML reads a
 * tag's name. A backslash before the `!` or the `<` shows it and opens neither.
 *
 * @param {string} markdown The page, as written.
 * @returns {boolean} Whether a figure is written outside any code.
 */
export function authorsFigure(markdown) {
  const source = dropEscapes(dropInlineSpansByLine(prose(markdown)));
  return source.includes('![') || /<img\b/i.test(source);
}

/**
 * The prose of a line that carries a display-maths delimiter beside content.
 *
 * Inline `$$...$$` complete on one line is fine, and so is `$$` alone on its
 * line; what breaks the parser is a block that opens or closes on a line that
 * carries anything else. Prose that talks about `$$` writes it in a code span.
 *
 * @param {string} line One line of a page, outside any fenced block.
 * @returns {string | null} The line's prose, trimmed, or `null` when it is fine.
 */
export function strayDelimiter(line) {
  const trimmed = dropInlineSpans(line).trim();
  const shown = dropEscapes(trimmed);
  if (!shown.includes('$$')) return null;
  const only = shown === '$$';
  const complete = /^\$\$.*\$\$$/.test(shown) && shown.length > 4;
  return only || complete ? null : trimmed;
}
