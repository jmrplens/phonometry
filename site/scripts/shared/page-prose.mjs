// What the site checks read in the prose of a page, apart from the checks.
//
// check-i18n-parity.mjs and check-math-render.mjs read every page of the site
// when they are loaded and exit with its verdict, so nothing can call them on
// one page; the two readings they make of a page are here, where a test can.
// Both step over the code first: a fenced block, then the inline spans, read
// as the site reads them (markdown-spans.mjs), each span leaving a mark that
// keeps the text either side of it apart, as the page shows it apart.

import { prose } from '../../src/lib/markdown-fences.mjs';
import { dropInlineSpans, dropInlineSpansByLine } from './markdown-spans.mjs';

/**
 * Whether a page writes a figure of its own, as markdown or as HTML.
 *
 * Every markdown image opens with the same two characters, whatever comes
 * after them: the inline `![alt](src)`, the two reference forms `![alt][label]`
 * and `![alt][]`, and the shortcut `![label]` whose target is a link definition
 * somewhere else in the file. Matching what opens all four is both shorter and
 * complete, and prose has no other use for the sequence once code is out.
 *
 * @param {string} markdown The page, as written.
 * @returns {boolean} Whether a figure is written outside any code.
 */
export function authorsFigure(markdown) {
  const source = dropInlineSpansByLine(prose(markdown));
  return source.includes('![') || /<img\b/.test(source);
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
  if (!trimmed.includes('$$')) return null;
  const only = trimmed === '$$';
  const complete = /^\$\$.*\$\$$/.test(trimmed) && trimmed.length > 4;
  return only || complete ? null : trimmed;
}
