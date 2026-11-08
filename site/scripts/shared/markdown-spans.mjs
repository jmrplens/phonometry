// Where the inline code and maths spans of a page open and close.
//
// The site checks that read the prose of a page step over its inline code
// first; they read the spans here, as the site's Markdown reader does, and as
// scripts/markdown_spans.py reads them for the Python checks. A code span
// opens on a run of backticks and closes on the next run of exactly as many
// (CommonMark 0.31.2, 6.1); remark-math reads a run of dollar signs the same
// way, and the first run on a line that finds its closing run is the span,
// whichever of the two it is. A run that no later run matches opens nothing
// and stays text.
//
// A backslash before the first character of a run escapes that character
// alone (CommonMark 2.4): it is shown as written and opens nothing, and the
// rest of the run, if any, is a run of its own. "\`x\`" is prose. Inside a
// span a backslash is a character like any other, so it escapes nothing
// there: "`%APPDATA%\phonometry\`" is one code span, its closing backtick
// behind a backslash. A reader that took an escaped backtick for an opening
// one hid the prose up to the next backtick from its check.

import { cellSpans, MDX_EXPRESSION, MDX_TAG, NOT_INLINE_ROLES, pageLines } from '../../src/lib/markdown-fences.mjs';

/** A run of backticks or of dollar signs. */
const RUN = /`+|\$+/g;

/** Whether an odd number of backslashes stands right before `text[start]`. */
function escaped(text, start) {
  let count = 0;
  while (start - count > 0 && text[start - count - 1] === '\\') count += 1;
  return count % 2 === 1;
}

/** The first of the sorted `indexes` past `after`, or `undefined`. */
function nextAfter(indexes, after) {
  let low = 0;
  let high = indexes.length;
  while (low < high) {
    const middle = (low + high) >> 1;
    if (indexes[middle] <= after) low = middle + 1;
    else high = middle;
  }
  return indexes[low];
}

/**
 * The `[start, end]` of every span of `text` that opens on one of `markers`.
 *
 * Read left to right: a run of a marker opens a span when a later run of the
 * same marker and the same length closes it, the runs between them being part
 * of the span; its first character is taken off when a backslash escapes it.
 * A run of a character not in `markers` is text.
 *
 * @param {string} text A line, or the lines of a paragraph joined.
 * @param {string} markers "`" for the code spans, "`$" for code and maths.
 * @returns {Array<[number, number]>} The spans, in the order they open.
 */
export function inlineSpans(text, markers = '`') {
  const runs = [...text.matchAll(RUN)].filter((run) => markers.includes(run[0][0]));
  const alike = new Map();
  runs.forEach((run, index) => {
    if (!alike.has(run[0])) alike.set(run[0], []);
    alike.get(run[0]).push(index);
  });
  const spans = [];
  let index = 0;
  while (index < runs.length) {
    let start = runs[index].index;
    let written = runs[index][0];
    if (escaped(text, start)) {
      start += 1;
      written = written.slice(1);
    }
    const closing = nextAfter(alike.get(written) ?? [], index);
    if (closing === undefined) {
      index += 1;
      continue;
    }
    spans.push([start, runs[closing].index + runs[closing][0].length]);
    index = closing + 1;
  }
  return spans;
}

/**
 * What a span taken out leaves in its place: the object replacement
 * character, which no check reads as a letter, a digit, a space or markup.
 * The text on either side of a span stays apart, as the page shows it apart:
 * "!``x``[alt](a.png)" is no figure, and "$`x`$" no display delimiter.
 */
export const SPAN_MARK = '\uFFFC';

/** `text` with every span of {@link inlineSpans} taken out, each leaving {@link SPAN_MARK}. */
export function dropInlineSpans(text, markers = '`') {
  let kept = '';
  let done = 0;
  for (const [start, end] of inlineSpans(text, markers)) {
    kept += text.slice(done, start) + SPAN_MARK;
    done = end;
  }
  return kept + text.slice(done);
}

/**
 * A comment, by the page's kind: an HTML comment on a `.md` page, which
 * opening a line is an HTML block (CommonMark 4.6, type 2) that runs to its
 * `-->` and may interrupt a paragraph, and an MDX comment, an expression,
 * beside it on a `.mdx` page.
 */
const COMMENTS = { md: /<!--[\s\S]*?-->/g, mdx: /<!--[\s\S]*?-->|\{\/\*[\s\S]*?\*\/\}/g };

/** A line that opens a comment, by the page's kind. */
const COMMENT_LINE = { md: /^ {0,3}<!--/, mdx: /^ {0,3}(?:<!--|\{\/\*)/ };

/**
 * `text` with every span of {@link inlineSpans} taken out, each block read
 * whole: a code span may run over the lines of its paragraph, as the page
 * reads it, but never past a blank line or into another block. Each span
 * leaves {@link SPAN_MARK} and the line breaks it held, so the text keeps its
 * lines, each where it was. A line of code or display maths is not read, and a
 * line of a raw HTML block holds no span.
 *
 * With `comments` set to the page's kind, its comments go too, read with
 * the spans in one pass left to right, whichever opens first winning: a
 * comment opened inside a span is code, and a backtick inside a comment is
 * the comment's. A line that opens a comment opens a block that runs to the
 * comment's end, blank lines included.
 *
 * @param {string} text The lines of a page, joined by a line feed.
 * @param {string} markers "`" for the code spans, "`$" for code and maths.
 * @param {{ comments?: 'md' | 'mdx', kind?: 'md' | 'mdx' }} [options] The page's
 *   kind, `comments` to read its comments with its spans, `kind` if not said by
 *   `comments`; a `.md` page if neither says.
 * @returns {string} The text, its spans out, with as many lines as it had.
 */
export function dropInlineSpansByBlock(text, markers = '`', { comments, kind } = {}) {
  return blocksOf(text.split('\n'), comments, kind ?? comments ?? 'md')
    .map((block) => dropBlockSpans(block, markers, comments))
    .join('\n');
}

/**
 * The lines of a page in the blocks a code span stays inside, every line in one.
 * The walk of the page says what each line is (`pageLines`): only the lines of a
 * paragraph, and those of a raw HTML block, stay together. A blank line is a block
 * of its own, a line that holds only the marks of a quotation among them, and so is
 * a heading, a row of a table, a thematic break, a setext underline, an aside's
 * fence, a line of a fence or of a display block.
 *
 * Each block says how it `reads`: `text`, spans read over its lines; `raw`, a raw
 * HTML block, where no span opens; `row`, a row of a table, whose cells each bound
 * what opens in them; `code`, a line of code or display maths, which nothing reads.
 * `walked` is the walk of the page as written, for a reader that blanked some of
 * its lines first: a line blanked is no line the walk can read.
 */
function blocksOf(lines, comments, kind, walked = pageLines(lines, { kind })) {
  const opener = comments ? COMMENT_LINE[comments] : null;
  const blocks = [];
  let current = null;
  const close = () => {
    if (current !== null) blocks.push(current);
    current = null;
  };
  walked.forEach((read, index) => {
    const line = lines[index];
    if (current !== null && opener && unclosed(current.lines, comments)) {
      current.lines.push(line);
      return;
    }
    if (current !== null && (read.role === 'text' || read.role === 'raw')) {
      current.lines.push(line);
      return;
    }
    close();
    if (NOT_INLINE_ROLES.has(read.role)) {
      blocks.push({ lines: [line], reads: 'code' });
    } else if (opener?.test(line)) {
      current = { lines: [line], reads: 'text' };
    } else if (read.role === 'paragraph' || read.role === 'text') {
      current = { lines: [line], reads: 'text' };
    } else if (read.role === 'html' || read.role === 'raw') {
      current = { lines: [line], reads: 'raw' };
    } else {
      blocks.push({ lines: [line], reads: read.role === 'row' ? 'row' : 'text' });
    }
  });
  close();
  return blocks;
}

/** Whether a block opens with a comment its lines have not closed yet. */
function unclosed(block, comments) {
  if (!COMMENT_LINE[comments].test(block[0])) return false;
  const pattern = new RegExp(COMMENTS[comments].source, 'y');
  return !pattern.test(block.join('\n').trimStart());
}

/** The spans of a piece of a block, and its comments with `comments`, left to right. */
function spansAndComments(block, markers, comments) {
  if (!comments) return inlineSpans(block, markers);
  const found = [];
  let done = 0;
  for (;;) {
    const spans = inlineSpans(block.slice(done), markers);
    const pattern = new RegExp(COMMENTS[comments].source, 'g');
    pattern.lastIndex = done;
    const comment = pattern.exec(block);
    let next = spans.length ? [spans[0][0] + done, spans[0][1] + done] : null;
    if (comment && (!next || comment.index < next[0])) {
      next = [comment.index, comment.index + comment[0].length];
    }
    if (!next) return found;
    found.push(next);
    done = next[1];
  }
}

/** The spans and comments of one block, whose lines are joined in `text`. */
function blockSpans(block, text, markers, comments) {
  if (block.reads === 'code') return [];
  if (block.reads === 'raw') return spansAndComments(text, '', comments);
  if (block.reads === 'text') return spansAndComments(text, markers, comments);
  return cellSpans(text).flatMap(([start, end]) =>
    spansAndComments(text.slice(start, end), markers, comments).map(([first, last]) => [
      first + start,
      last + start,
    ]),
  );
}

/** One block with its spans out, each leaving its mark and its line breaks. */
function dropBlockSpans(block, markers, comments) {
  const text = block.lines.join('\n');
  let kept = '';
  let done = 0;
  for (const [start, end] of blockSpans(block, text, markers, comments)) {
    const breaks = text.slice(start, end).split('\n').length - 1;
    kept += text.slice(done, start) + SPAN_MARK + '\n'.repeat(breaks);
    done = end;
  }
  return kept + text.slice(done);
}

/**
 * A page's frontmatter as Astro reads it (`frontmatterRE` of
 * `@astrojs/internal-helpers`): fenced by `---` or by `+++`, at the start of the
 * page behind a byte order mark or after blank lines, its closing fence opening
 * a line. One that never closes is no frontmatter.
 */
const FRONTMATTER = /(?:^﻿?|^\s*\n)(?:---|\+\+\+)([\s\S]*?\n)(?:---|\+\+\+)/;

/**
 * A backslash and the ASCII punctuation character it escapes (CommonMark 0.31.2,
 * 2.4): the page shows the character, and it opens nothing.
 */
const ESCAPE = /\\[!-\/:-@[-`{-~]/y;

/**
 * A tag of raw HTML written in the prose of a `.md` page, open or closing, and an
 * autolink (CommonMark 0.31.2, 6.6 and 6.5), each taken whole.
 */
const HTML_TAG =
  /<[A-Za-z][A-Za-z0-9-]*(?:[ \t\n]+[A-Za-z_:][A-Za-z0-9_.:-]*(?:[ \t\n]*=[ \t\n]*(?:[^ \t\n"'=<>`]+|'[^']*'|"[^"]*"))?)*[ \t\n]*\/?>|<\/[A-Za-z][A-Za-z0-9-]*[ \t\n]*>|<[A-Za-z][A-Za-z0-9+.-]{1,31}:[^ \t\n<>]*>/y;

/**
 * Where the frontmatter of a page ends, as Astro finds it ({@link FRONTMATTER}):
 * the index right past its closing fence, 0 when the page has none.
 *
 * @param {string} text The page as written.
 * @returns {number} How many code units of the page its frontmatter takes.
 */
export function frontmatterEnd(text) {
  const head = FRONTMATTER.exec(text);
  return head === null ? 0 : head[0].length;
}

/** What may open where a backslash, a tag, an expression or a comment does. */
const OPENER = /[\\<{]/g;

/** The tags and expressions of an `.mdx` page, read here apart from the walk's. */
const TAG = new RegExp(MDX_TAG.source, 'y');
const EXPRESSION = new RegExp(MDX_EXPRESSION.source, 'y');

/**
 * `text` with every character but a line end a space, one for each code unit, so
 * that every index of the page stays where it was: a reader maps what it finds
 * back onto the page by its index. Python's `page_markup` keeps its own columns,
 * which count code points, so a character outside the basic plane blanked there
 * is one space and two here.
 */
function blank(text) {
  return text.replace(/[^\n]/g, ' ');
}

/** The end of what the sticky `pattern` matches at `at`, or `null`. */
function endOf(pattern, text, at) {
  pattern.lastIndex = at;
  const found = pattern.exec(text);
  return found === null ? null : found.index + found[0].length;
}

/**
 * Where what opens at `text[at]` ends, and whether the page renders it as
 * markup, or `null` when nothing opens there. A backslash escape and a comment
 * end inside the piece of a block that ends at `end`; a tag and an expression
 * may run on over the lines after it. On the lines of a raw HTML block only a
 * comment opens.
 */
function openedAt(text, at, end, kind, reads) {
  const opened = text[at];
  if (opened === '<' || opened === '{') {
    const comment = endOf(new RegExp(COMMENTS[kind].source, 'y'), text, at);
    if (comment !== null && comment <= end) return [comment, false];
  }
  if (reads === 'raw') return null;
  if (opened === '\\') {
    const escape = endOf(ESCAPE, text, at);
    return escape !== null && escape <= end ? [escape, false] : null;
  }
  if (opened === '<') {
    const tag = endOf(kind === 'mdx' ? TAG : HTML_TAG, text, at);
    return tag === null ? null : [tag, true];
  }
  if (kind === 'mdx') {
    const expression = endOf(EXPRESSION, text, at);
    return expression === null ? null : [expression, false];
  }
  return null;
}

/**
 * The first escape, comment, tag or expression past `at` and before `end`: where
 * it opens and ends, and whether the page renders it as markup.
 */
function firstOpened(text, at, end, kind, reads) {
  OPENER.lastIndex = at;
  for (let found = OPENER.exec(text); found !== null && found.index < end; found = OPENER.exec(text)) {
    const opened = openedAt(text, found.index, end, kind, reads);
    if (opened !== null) return [found.index, ...opened];
    OPENER.lastIndex = found.index + 1;
  }
  return null;
}

/**
 * The `[start, end]` of each part of `text` the page shows as text or hides,
 * read left to right over each block of the page and each cell of a row on its
 * own: at each character the first of a code or maths span, a backslash escape,
 * a comment, a tag and an expression that opens there takes what follows. A tag
 * the page renders is markup, and the rest is read again from its end. A tag and
 * an expression may run on over the lines after their block. The spans of a
 * piece are read once and taken in turn, and read again only past what else
 * opened; the next opener is looked for again only once a span has held it.
 */
function unrendered(text, kind, walked) {
  const found = [];
  let at = 0;
  let start = 0;
  for (const block of blocksOf(text.split('\n'), kind, kind, walked)) {
    const joined = block.lines.join('\n');
    const pieces =
      block.reads === 'row'
        ? cellSpans(joined).map(([first, last]) => [start + first, start + last])
        : [[start, start + joined.length]];
    start += joined.length + 1;
    if (block.reads === 'code') continue;
    const markers = block.reads === 'raw' ? '' : '`$';
    for (const [first, last] of pieces) {
      at = Math.max(at, first);
      let spans = null;
      let opened = null;
      let looked = false;
      while (at < last) {
        if (spans === null) {
          spans = inlineSpans(text.slice(at, last), markers)
            .map(([a, b]) => [at + a, at + b])
            .reverse();
        }
        if (!looked || (opened !== null && opened[0] < at)) {
          opened = firstOpened(text, at, last, kind, block.reads);
          looked = true;
        }
        const span = spans.length ? spans[spans.length - 1] : null;
        if (span !== null && (opened === null || span[0] < opened[0])) {
          found.push(spans.pop());
          at = span[1];
        } else if (opened !== null) {
          if (!opened[2]) found.push([opened[0], opened[1]]);
          at = opened[1];
          spans = null;
          looked = false;
        } else {
          break;
        }
      }
    }
  }
  return found;
}

/**
 * `text` with every part of the page that renders no tag blanked: the reading of
 * `page_markup` of `scripts/markdown_spans.py`, which the Python checks read a
 * page's components through.
 *
 * A component a page renders, a `<ReportPreview>` or a `<Catalogues>`, is a tag
 * written outside its frontmatter, its code, fenced or indented, its display
 * maths, its inline code and maths spans, its comments and its expressions, and
 * not behind a backslash. Written in any of those it is text the page shows or
 * hides, and a reader that looks for a component in the page as written counts
 * it as one the page renders. Each of them is blanked as the site reads it: the
 * frontmatter as Astro finds it, after a byte order mark or blank lines too, the
 * blocks by one walk of the page, and the rest left to right over each block,
 * whichever opens first taking what follows: a span written before a tag holds
 * it, and a tag holds what its attributes write, a `$` or a backtick among them.
 * On a `.md` page a tag is one of raw HTML, and there is no expression. Every
 * code unit blanked but a line end becomes a space, so a tag found in the result
 * stands at the index where the page writes it, as the page writes it.
 *
 * @param {string} text The page as written, its frontmatter in.
 * @param {{ kind?: 'md' | 'mdx' }} [options] The page's kind.
 * @returns {string} The page, as many lines long as it was.
 */
export function pageMarkup(text, { kind = 'mdx' } = {}) {
  const head = frontmatterEnd(text);
  const body = blank(text.slice(0, head)) + text.slice(head);
  const lines = body.split('\n');
  const walked = pageLines(lines, { kind });
  const prose = lines.map((line, index) => (NOT_INLINE_ROLES.has(walked[index].role) ? blank(line) : line)).join('\n');
  let shown = '';
  let done = 0;
  for (const [start, end] of unrendered(prose, kind, walked)) {
    shown += prose.slice(done, start) + blank(prose.slice(start, end));
    done = end;
  }
  return shown + prose.slice(done);
}
