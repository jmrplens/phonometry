// The Markdown copy of a page that has no docs/ mirror, as the page shows it.
//
// emit-page-markdown.mjs publishes a Markdown copy beside every page. Where
// docs/ holds no mirror of the page (every Spanish page but the transplanted
// ones), the copy is the page's own source with its frontmatter and its MDX
// machinery taken out: its import and export statements and its component
// tags, a wrapper keeping its children. That machinery was found by patterns
// over the page as written, which read code as machinery too: the `import`
// line of a Python example went as the page's own import, a `<NC-15` written in
// a code span opened a component that ran to the next `/>`, and two blank lines
// of an example closed up. The page is read here as the site renders it
// (pageMarkup of markdown-spans.mjs), so only what the page renders as markup
// goes, and what it shows as code stays as it shows it.

import { codeLines } from '../../src/lib/markdown-fences.mjs';
import { frontmatterEnd, pageMarkup } from './markdown-spans.mjs';

/** An import or an export statement of an `.mdx` page, on a line of its own. */
const ESM = /^(?:import|export)\s.*$/gm;

/** A component closed in its own tag: `<ThemeImage ... />`, `<Video ... />`. */
const SELF_CLOSING = /<[A-Z][\w.]*\b[^>]*\/>/g;

/** The opening or the closing tag of a component that wraps content. */
const WRAPPER = /<\/?[A-Z][\w.]*\b[^>]*>/g;

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
 * The prose of a page with the MDX machinery that is noise as text taken out:
 * its import and export statements, its components closed in their own tag, and
 * the tags of the components that wrap content, whose children stay. Each is
 * taken out only where the page renders it as markup, so a tag or an `import`
 * line written in code stays. A run of blank lines outside code closes up to
 * one; the blank lines of a code example stay.
 *
 * @param {string} text The page, its frontmatter out.
 * @param {{ kind?: 'md' | 'mdx', expand?: (tag: string) => string | undefined }} [options]
 *   The page's kind, an `.md` page having no import or export statement, and
 *   what a component closed in its own tag is written out as, where it is not
 *   taken out.
 * @returns {string} The prose, trimmed.
 */
export function stripMdx(text, { kind = 'mdx', expand = () => undefined } = {}) {
  const shown = pageMarkup(text, { kind });
  const edits = [];
  if (kind === 'mdx') {
    for (const found of shown.matchAll(ESM)) edits.push([found.index, found.index + found[0].length, '']);
  }
  for (const found of shown.matchAll(SELF_CLOSING)) {
    edits.push([found.index, found.index + found[0].length, expand(found[0]) ?? '']);
  }
  const taken = (at) => edits.some(([start, end]) => start <= at && at < end);
  for (const found of shown.matchAll(WRAPPER)) {
    if (!taken(found.index)) edits.push([found.index, found.index + found[0].length, '']);
  }
  edits.sort((a, b) => a[0] - b[0]);
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
