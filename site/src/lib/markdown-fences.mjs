/**
 * Where the fences of a markdown page open and close, as CommonMark reads them.
 *
 * The site's own JavaScript reads its pages here, as the Python scripts read
 * them through `scripts/markdown_fences.py`; the two are one reading written
 * twice, and `tests/test_markdown_fences.py` holds them to the same answer on
 * every page. A fence opens on a run of at least three backticks or three
 * tildes, and only a line of the same character, at least as long as that run,
 * with nothing after it but blanks, closes it (CommonMark 0.31.2, 4.5). An info
 * string after a run of backticks may not hold a backtick itself: such a line is
 * an inline code span, not a fence. A reader that flips a flag on any run of
 * three markers, or a regular expression that runs to the next three, loses
 * track at the first block that shows a fence inside another and reads the page
 * inside out from there; one that knows only backticks never sees a tilde fence.
 * `scripts/check_fence_readers.py` fails on a script of the site that reads
 * fences any other way.
 *
 * Any indentation of the marker is read as a fence, because the pages nest
 * fences inside list items, and the body of an indented fence loses as much
 * indentation as its opening marker carried.
 *
 * The marks of the containers that hold a fence are not the text of its line
 * (CommonMark 0.31.2, 5.1 and 5.2): a fence opens behind the marks of a
 * quotation and on the first line of a list item, each of its lines loses those
 * marks, and it ends with what holds it, where its quotation or its item ends.
 */

/** A run of three or more backticks or tildes opening a line, and the rest. */
const MARKER = /^(\s*)(`{3,}|~{3,})(.*)$/;

/** The mark of a quotation, what may stand before it and the one blank after it. */
const QUOTE_MARK = /^[ \t]*>[ \t]?/;

/** The marker of a list item and the blanks after it. */
const ITEM_MARKER = /^[ \t]*(?:[-*+]|\d{1,9}[.)])[ \t]+/;

/**
 * A line read past the quotation marks and the list markers that open it.
 *
 * @param {string} line
 * @returns {{depth: number, within: number, rest: string}} How many quotation
 *   marks stand before its text, the column of the content of the list item it
 *   opens (0 when the marks end on a quotation or there are none), and the line
 *   past its marks, each list marker left as blanks.
 */
export function pastMarks(line) {
  let rest = line;
  let depth = 0;
  let width = 0;
  for (;;) {
    const mark = QUOTE_MARK.exec(rest);
    if (mark) {
      depth += 1;
      width = 0;
      rest = rest.slice(mark[0].length);
      continue;
    }
    const marker = ITEM_MARKER.exec(rest);
    if (!marker) return { depth, within: width, rest: ' '.repeat(width) + rest };
    width += marker[0].length;
    rest = rest.slice(marker[0].length);
  }
}

/**
 * A line inside a block opened behind marks, or `null` if the block has ended:
 * at a line with fewer quotation marks than it opened behind, or a line of text
 * indented less than the content of the list item it opened on.
 *
 * @param {string} line
 * @param {number} depth The quotation marks it opened behind.
 * @param {number} within The column of the content of the item it opened on, or 0.
 * @returns {string | null}
 */
function insideBlock(line, depth, within) {
  let rest = line;
  for (let crossed = 0; crossed < depth; crossed += 1) {
    const mark = QUOTE_MARK.exec(rest);
    if (!mark) return null;
    rest = rest.slice(mark[0].length);
  }
  if (rest.trim() && rest.length - rest.replace(/^[ \t]+/, '').length < within) return null;
  return rest;
}

/**
 * The lines of a page, without their line ends.
 *
 * @param {string} text The page.
 * @returns {string[]} One entry per line; a final line end opens no line.
 */
export function splitLines(text) {
  return withEnds(text).map((line) => line.replace(/\r?\n$|\r$/, ''));
}

/**
 * The lines of a page, each with its own line end.
 *
 * @param {string} text The page.
 * @returns {string[]} One entry per line; only the last may lack a line end.
 */
function withEnds(text) {
  return text.match(/[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+$/g) ?? [];
}

/**
 * Every line with its part in the page.
 *
 * @param {Iterable<string>} lines The lines, without their line ends.
 * @returns {Generator<{text: string, inner: string, role: 'prose' | 'open' | 'body' | 'close', info: string, indent: number}>}
 */
function* read(lines) {
  let opening = '';
  let indent = 0;
  let depth = 0;
  let within = 0;
  for (const text of lines) {
    const inner = opening ? insideBlock(text, depth, within) : null;
    if (inner === null) {
      opening = '';
      const marks = pastMarks(text);
      const [, lead = '', run = '', rest = ''] = MARKER.exec(marks.rest) ?? [];
      if (run && !(run[0] === '`' && rest.includes('`'))) {
        opening = run;
        indent = lead.length;
        depth = marks.depth;
        within = marks.within;
        yield { text, inner: '', role: 'open', info: rest.trim(), indent };
      } else {
        yield { text, inner: '', role: 'prose', info: '', indent: 0 };
      }
      continue;
    }
    const marker = MARKER.exec(inner);
    if (
      marker !== null &&
      marker[2][0] === opening[0] &&
      marker[2].length >= opening.length &&
      !marker[3].trim()
    ) {
      opening = '';
      yield { text, inner, role: 'close', info: '', indent };
    } else {
      yield { text, inner, role: 'body', info: '', indent };
    }
  }
}

/**
 * Whether each line is code: a fence's opening line, its body or its closing
 * line. A fence never closed runs to the end of the page.
 *
 * @param {Iterable<string>} lines The lines, without their line ends.
 * @returns {boolean[]} One entry per line.
 */
export function codeLines(lines) {
  return Array.from(read(lines), (line) => line.role !== 'prose');
}

/**
 * The page with every line of a fence emptied, so that line numbers still hold.
 *
 * @param {string} text The page.
 * @returns {string} The prose of the page, its lines joined by a line feed.
 */
export function prose(text) {
  return Array.from(read(splitLines(text)), (line) =>
    line.role === 'prose' ? line.text : '',
  ).join('\n');
}

/**
 * The line without up to `indent` leading blanks.
 *
 * @param {string} text
 * @param {number} indent
 */
function dedent(text, indent) {
  const blanks = text.length - text.replace(/^[ \t]+/, '').length;
  return text.slice(Math.min(indent, blanks));
}

/**
 * @typedef {object} Fence One fenced block of a page.
 * @property {number} line The line number of the opening marker, counted from 1.
 * @property {string} info The info string after the opening marker, trimmed.
 * @property {string} language The first word of the info string, or ''.
 * @property {string} body The lines between the two markers, each with its
 *   line end, without the indentation the opening marker carried. A fence
 *   never closed runs to the end of the page.
 */

/**
 * @param {number} line
 * @param {string} info
 * @param {string[]} body
 * @returns {Fence}
 */
function fence(line, info, body) {
  return { line, info, language: info.split(/\s+/)[0] ?? '', body: body.join('') };
}

/**
 * Every fenced block of a page, in reading order.
 *
 * @param {string} text The page.
 * @returns {Fence[]} One entry per block, closed or running to the end.
 */
export function fences(text) {
  const found = [];
  let start = 0;
  let info = '';
  /** @type {string[]} */
  let body = [];
  const lines = withEnds(text);
  let number = 0;
  for (const line of read(splitLines(text))) {
    const end = lines[number].slice(line.text.length);
    number += 1;
    if (line.role === 'open') {
      start = number;
      info = line.info;
      body = [];
    } else if (line.role === 'body') {
      body.push(dedent(line.inner, line.indent) + end);
    } else if (line.role === 'close') {
      found.push(fence(start, info, body));
      start = 0;
    }
  }
  if (start) found.push(fence(start, info, body));
  return found;
}
