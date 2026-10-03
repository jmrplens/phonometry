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
 */

/** A run of three or more backticks or tildes opening a line, and the rest. */
const MARKER = /^(\s*)(`{3,}|~{3,})(.*)$/;

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
 * @returns {Generator<{text: string, role: 'prose' | 'open' | 'body' | 'close', info: string, indent: number}>}
 */
function* read(lines) {
  let opening = '';
  let indent = 0;
  for (const text of lines) {
    const marker = MARKER.exec(text);
    if (!opening) {
      const [, lead = '', run = '', rest = ''] = marker ?? [];
      if (run && !(run[0] === '`' && rest.includes('`'))) {
        opening = run;
        indent = lead.length;
        yield { text, role: 'open', info: rest.trim(), indent };
      } else {
        yield { text, role: 'prose', info: '', indent: 0 };
      }
      continue;
    }
    if (
      marker !== null &&
      marker[2][0] === opening[0] &&
      marker[2].length >= opening.length &&
      !marker[3].trim()
    ) {
      opening = '';
      yield { text, role: 'close', info: '', indent };
    } else {
      yield { text, role: 'body', info: '', indent };
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
      body.push(dedent(line.text, line.indent) + end);
    } else if (line.role === 'close') {
      found.push(fence(start, info, body));
      start = 0;
    }
  }
  if (start) found.push(fence(start, info, body));
  return found;
}
