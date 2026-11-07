/**
 * Where the blocks of a markdown page open and close, as the site's parser reads them.
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
 * Whether a line opens a block depends on the lines above it, so the page is
 * walked once, line by line (`pageLines`), as a parser's first phase walks it,
 * keeping the quotations and the list items open at each line and what stands
 * open inside them. A block ends with what holds it. A paragraph carries on
 * through a line with fewer marks or less indentation than it opened with, unless
 * that line opens a block of its own, which a setext underline never does; an
 * ordered marker other than 1 and an empty marker do not interrupt the paragraph
 * above them in their own container. A pipe opens a table only over a delimiter
 * row with as many cells, and a cell bounds what opens in it. An aside
 * (`:::note`) interrupts a paragraph, and a lone `:::` closes one and is text with
 * none open. `scripts/markdown_fences.py` says the same at more length.
 *
 * The page's kind decides what indentation and a tag mean. On a `.md` page, four
 * columns past the container open no block, and a raw HTML block runs to its end
 * condition. On a `.mdx` page any indentation opens a block, there is no HTML,
 * and a tag or an expression with its lines to itself ends a paragraph. A reader
 * that does not say which page it holds is read as `.mdx`, whose fences are the
 * wider reading.
 *
 * The body of an indented fence loses as much indentation as its opening marker
 * carried.
 */

/** A run of three or more backticks or tildes opening a line, and the rest. */
const MARKER = /^(\s*)(`{3,}|~{3,})(.*)$/;

/**
 * A line that may open or close display maths, as remark-math reads it: a run of
 * two dollar signs or more and a meta with no dollar sign in it.
 */
const DISPLAY = /^[ \t]*(\${2,})([^$]*)$/;

/** What stands for a quotation among the containers open at a line. */
const QUOTATION = -1;

/** Four columns past its container, a line opens no block on a `.md` page. */
const CODE_INDENT = 4;

/**
 * How many columns a marker may leave before its text and still set its column,
 * on a `.md` page: past those, the item opens on indented code.
 */
const MOST_BLANKS_AFTER_MARKER = 4;

/** A tab's stop, in columns. */
const TAB_STOP = 4;

/** The marker of a list item, the number of an ordered one captured. */
const ITEM_MARKER = /^(?:[-*+]|(\d{1,9})[.)])(?=[ \t]|$)/;

/** A heading written with its marks. */
const ATX_HEADING = /^#{1,6}(?:[ \t]|$)/;

/** A thematic break, as written past what opens the line. */
const THEMATIC_BREAK = /^([-*_])[ \t]*(?:\1[ \t]*){2,}$/;

/** A setext underline, as written past what opens the line. */
const UNDERLINE = /^(?:=+|-+)[ \t]*$/;

/** The delimiter row of a table: one cell or more of hyphens and alignment colons. */
const DELIMITER_ROW = /^\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$/;

/** What decides a table's cells, left to right: an escape, or the pipe between two. */
const CELL_MARK = /\\.|\|/g;

/** The attributes and the label a directive may carry. */
const DIRECTIVE_REST = '[A-Za-z0-9][A-Za-z0-9_-]*(?:\\[[^\\]]*\\])?(?:\\{[^}]*\\})?[ \\t]*$';

/** A line that opens an aside, a container directive of three colons or more. */
const ASIDE = new RegExp(`^(:{3,})${DIRECTIVE_REST}`);

/** A line that is one leaf directive, of two colons exactly. */
const LEAF_DIRECTIVE = new RegExp(`^::${DIRECTIVE_REST}`);

/** A line of colons alone, which closes an aside as long as it or longer. */
const ASIDE_CLOSE = /^(:{3,})[ \t]*$/;

/**
 * The element names of a raw HTML block of type 6, which may interrupt a paragraph
 * (CommonMark 4.6). `_HTML_BLOCK_NAMES` of `scripts/markdown_fences.py`.
 */
const HTML_BLOCK_NAMES =
  'address|article|aside|base|basefont|blockquote|body|caption|center|col|' +
  'colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|' +
  'form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|' +
  'menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|' +
  'table|tbody|td|tfoot|th|thead|title|tr|track|ul';

/**
 * How a raw HTML block of types 1 to 6 opens and what ends it, `null` being a
 * blank line (CommonMark 0.31.2, 4.6). These are the ends the Markdown parser
 * reads, which is what decides this page: `--!>`, which a browser takes as the end
 * of a comment, does not end a block here.
 */
const HTML_BLOCKS = [
  [
    /^<(?:script|pre|style|textarea)(?:[ \t>]|$)/i,
    (line) => /<\/(?:script|pre|style|textarea)>/i.test(line),
  ],
  [/^<!--/, (line) => line.includes('-->')],
  [/^<\?/, (line) => line.includes('?>')],
  [/^<![A-Za-z]/, (line) => line.includes('>')],
  [/^<!\[CDATA\[/, (line) => line.includes(']]>')],
  [new RegExp(`^</?(?:${HTML_BLOCK_NAMES})(?:[ \\t]|/?>|$)`, 'i'), null],
];

/**
 * A raw HTML block of type 7: any other complete tag alone on its line. It runs to
 * a blank line, it cannot interrupt a paragraph in its own container, and on a lazy
 * line the site's parser opens it in the paragraph's container, which stays.
 */
const HTML_LONE_TAG =
  /^(?:<[A-Za-z][A-Za-z0-9-]*(?:[ \t]+[A-Za-z_:][\w.:-]*(?:[ \t]*=[ \t]*(?:[^ \t"'=<>`]+|'[^']*'|"[^"]*"))?)*[ \t]*\/?>|<\/[A-Za-z][A-Za-z0-9-]*[ \t]*>)[ \t]*$/;

/**
 * A tag of an `.mdx` page, over as many lines as it takes: a quoted value and an
 * expression among its attributes may hold a `>`. Sticky: a reader sets its
 * `lastIndex` to where the tag would open, and one that looks for every tag of a
 * text builds its own from the `source`. `pageMarkup` of
 * `scripts/shared/markdown-spans.mjs` reads the tags of a page by it too.
 */
export const MDX_TAG = /<\/?(?:[A-Za-z_$][\w.:$-]*(?:[^"'>{]|"[^"]*"|'[^']*'|\{(?:[^{}]|\{[^{}]*\})*\})*)?>/y;

/**
 * An expression of an `.mdx` page, over as many lines as it takes: a comment, or
 * braces balanced three levels down. Sticky, as {@link MDX_TAG} is.
 */
export const MDX_EXPRESSION = /\{\s*\/\*[\s\S]*?\*\/\s*\}|\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}/y;

/** The roles of a line that is code. */
const CODE_ROLES = new Set(['open', 'body', 'close', 'indented']);

/** The roles of a line whose text no inline span of the page reaches. */
export const NOT_INLINE_ROLES = new Set([...CODE_ROLES, 'maths-open', 'maths']);

/** What is blank on a line, as CommonMark has it: nothing but spaces and tabs. */
function isBlank(text) {
  return /^[ \t]*$/.test(text);
}

/** `text` without the spaces and tabs that open it. */
function pastBlanks(text) {
  return text.replace(/^[ \t]+/, '');
}

/** `text` without the spaces and tabs on either side of it. */
function stripBlanks(text) {
  return pastBlanks(text).replace(/[ \t]+$/, '');
}

/** How many columns the blanks that open `text` take, it standing at `column`. */
function blankColumns(text, column) {
  let at = column;
  for (const char of text) {
    if (char === ' ') at += 1;
    else if (char === '\t') at += TAB_STOP - (at % TAB_STOP);
    else break;
  }
  return at - column;
}

/** `text` past `width` columns of its opening blanks, a split tab left as spaces. */
function pastColumns(text, column, width) {
  let at = column;
  const end = column + width;
  for (let index = 0; index < text.length; index += 1) {
    if (at >= end) return ' '.repeat(at - end) + text.slice(index);
    if (text[index] === ' ') at += 1;
    else if (text[index] === '\t') at += TAB_STOP - (at % TAB_STOP);
    else return text.slice(index);
  }
  return ' '.repeat(Math.max(at - end, 0));
}

/**
 * What a quotation's mark leaves of `rest`, standing at `column`, and the column
 * past it, or `null`: up to three columns of blanks may stand before the mark on a
 * `.md` page, where four open indented code, and any number on an `.mdx` one; one
 * column of blank after it is the mark's own, a tab there leaving the rest of its
 * columns as spaces (CommonMark 0.31.2, 2.2 and 5.1).
 *
 * @param {string} rest
 * @param {number} column
 * @param {boolean} markdown Whether the page is `.md`, not `.mdx`.
 * @returns {[string, number] | null}
 */
function quoteMarkAt(rest, column, markdown) {
  const blanks = blankColumns(rest, column);
  const body = pastBlanks(rest);
  if (!body.startsWith('>') || (markdown && blanks >= CODE_INDENT)) return null;
  const at = column + blanks + 1;
  const after = body.slice(1);
  if (after[0] === ' ' || after[0] === '\t') return [pastColumns(after, at, 1), at + 1];
  return [after, at];
}

/**
 * How many quotation marks open `line`, and what they leave of it, read column by
 * column as the walk of the page reads them, a tab to its stop: a line read apart
 * from its page, as one a reader has already placed outside code. The twin of
 * `quotation_marks` in `scripts/markdown_fences.py`.
 *
 * @param {string} line
 * @param {{ kind?: 'md' | 'mdx' }} [options] The page's kind.
 * @returns {[number, string]} The number of marks, and the line past them and the
 *   blank each may take.
 */
export function quotationMarks(line, { kind = 'mdx' } = {}) {
  let depth = 0;
  let rest = line;
  let column = 0;
  for (;;) {
    const mark = quoteMarkAt(rest, column, kind === 'md');
    if (mark === null) return [depth, rest];
    [rest, column] = mark;
    depth += 1;
  }
}

/**
 * The `[start, end]` of each piece of a table's row, between its unescaped pipes.
 *
 * @param {string} row
 * @returns {Array<[number, number]>}
 */
export function cellSpans(row) {
  const spans = [];
  let start = 0;
  for (const mark of row.matchAll(CELL_MARK)) {
    if (mark[0] === '|') {
      spans.push([start, mark.index]);
      start = mark.index + 1;
    }
  }
  spans.push([start, row.length]);
  return spans;
}

/** How many cells a row holds, its outer pipes opening and closing none. */
function cellCount(row) {
  const stripped = stripBlanks(row);
  const pieces = cellSpans(stripped).map(([start, end]) => stripped.slice(start, end));
  if (pieces.length > 1 && isBlank(pieces[0])) pieces.shift();
  if (pieces.length > 1 && isBlank(pieces[pieces.length - 1])) pieces.pop();
  return pieces.length;
}

/**
 * @typedef {object} PageLine One line of a page, as the walk reads it.
 * @property {string} text The line as written.
 * @property {string} role Its part in the page: `blank`, `paragraph`, `text` (a line
 *   that carries a paragraph on, a lazy one among them), `heading` (a heading
 *   written with its marks), `single` (any other block of its own: a thematic break,
 *   an aside's fence, a tag or an expression alone), `underline`, `row`, `html` (it
 *   opens a raw HTML block), `raw` (it carries one on), `indented`, `open`, `body`,
 *   `close` (a line of a fence), `maths-open` and `maths` (any other line of a
 *   display block).
 * @property {string} info The info string of a fence or the meta of a display block,
 *   on the line that opens it.
 * @property {number} indent The indentation of the opening marker, on every line of
 *   a fence.
 * @property {string} rest The line past the marks and the columns of its containers,
 *   and past those it opens.
 * @property {boolean} item Whether the last container it opens is a list item, so
 *   that `rest` opens with the item's text.
 */

/** @returns {PageLine} */
function pageLine(text, role, rest, info = '', indent = 0) {
  return { text, role, rest, info, indent, item: false };
}

/** What stands open at each line of a page, read a line at a time. */
class Walk {
  /**
   * @param {string[]} lines The lines, without their line ends.
   * @param {string} kind The page's kind.
   */
  constructor(lines, kind) {
    this.lines = lines;
    this.markdown = kind === 'md';
    this.held = [];
    this.fresh = false;
    this.leaf = '';
    this.opening = '';
    this.indent = 0;
    this.htmlEnd = null;
    this.asides = [];
    this.left = 0;
    this.item = false;
  }

  /** The line at `index`, which has to come after the one read last. */
  read(index) {
    const text = this.lines[index];
    const closed = this.closesAside(text);
    if (closed !== null) return pageLine(text, 'single', closed);
    const [rest, column, matched] = this.pastHeld(text, this.held.length);
    this.fresh = false;
    if (this.left) {
      this.left -= 1;
      return pageLine(text, 'single', rest);
    }
    if (['fence', 'maths', 'html'].includes(this.leaf)) {
      if (matched === this.held.length && !this.endsOnBlank(rest)) {
        return this.inside(text, rest);
      }
      this.leaf = '';
    }
    const opened = this.opens(index, text, rest, column, matched);
    opened.item = this.item;
    return opened;
  }

  /** `text` past the first `upto` containers: what is left, its column, how many held it. */
  pastHeld(text, upto) {
    let rest = text;
    let column = 0;
    for (let index = 0; index < upto; index += 1) {
      [rest, column] = this.pastAside(rest, column, index);
      const held = this.held[index];
      if (held === QUOTATION) {
        const mark = this.quoteMark(rest, column);
        if (mark === null) return [rest, column, index];
        [rest, column] = mark;
      } else if (!isBlank(rest)) {
        if (blankColumns(rest, column) < held) return [rest, column, index];
        rest = pastColumns(rest, column, held);
        column += held;
      } else if (this.fresh && index === this.held.length - 1) {
        return [rest, column, index];
      }
    }
    [rest, column] = this.pastAside(rest, column, upto);
    return [rest, column, upto];
  }

  /** `text` past the indentation of the asides at `depth` containers, and its column. */
  pastAside(text, start, depth) {
    let rest = text;
    let column = start;
    for (const [, around, indent] of this.asides) {
      if (around === depth) {
        const width = Math.min(indent, blankColumns(rest, column));
        rest = pastColumns(rest, column, width);
        column += width;
      }
    }
    return [rest, column];
  }

  /** What a quotation's mark leaves of `rest`, and at which column, or `null`. */
  quoteMark(rest, column) {
    return quoteMarkAt(rest, column, this.markdown);
  }

  /** What is left of a line that closes the innermost aside, or `null`. */
  closesAside(text) {
    if (!this.asides.length) return null;
    const [colons, around] = this.asides[this.asides.length - 1];
    const [rest, column, matched] = this.pastHeld(text, around);
    const close = ASIDE_CLOSE.exec(pastBlanks(rest));
    if (
      matched < around ||
      close === null ||
      close[1].length < colons ||
      (this.markdown && blankColumns(rest, column) >= CODE_INDENT)
    ) {
      return null;
    }
    this.asides.pop();
    this.closeTo(around);
    this.leaf = '';
    return rest;
  }

  /** Whether `rest` ends a raw HTML block that a blank line ends. */
  endsOnBlank(rest) {
    return this.leaf === 'html' && this.htmlEnd === null && isBlank(rest);
  }

  /** A line that the fence, the display block or the HTML block open holds. */
  inside(text, rest) {
    if (this.leaf === 'html') {
      if (this.htmlEnd !== null && this.htmlEnd(rest)) this.leaf = '';
      return pageLine(text, 'raw', rest);
    }
    const deep = this.markdown && blankColumns(rest, 0) >= CODE_INDENT;
    if (this.leaf === 'maths') {
      const closing = DISPLAY.exec(rest);
      if (
        closing !== null &&
        !deep &&
        closing[1].length >= this.opening.length &&
        !closing[2].trim()
      ) {
        this.leaf = '';
      }
      return pageLine(text, 'maths', rest);
    }
    const marker = MARKER.exec(rest);
    if (
      marker !== null &&
      !deep &&
      marker[2][0] === this.opening[0] &&
      marker[2].length >= this.opening.length &&
      !marker[3].trim()
    ) {
      this.leaf = '';
      return pageLine(text, 'close', rest, '', this.indent);
    }
    return pageLine(text, 'body', rest, '', this.indent);
  }

  /** Close the containers past the first `kept`, and the asides they held. */
  closeTo(kept) {
    this.held.length = Math.min(this.held.length, kept);
    this.asides = this.asides.filter(([, around]) => around <= kept);
  }

  /** A line that nothing concrete holds: what it opens, or the paragraph it carries on. */
  opens(index, text, written, startColumn, startMatched) {
    let rest = written;
    let column = startColumn;
    let matched = startMatched;
    let paragraph =
      this.leaf === 'paragraph' && this.asides.every(([, around]) => around <= matched);
    const strict = (paragraph || this.leaf === 'indented') && matched === this.held.length;
    let opened = false;
    this.item = false;
    while (!(this.markdown && blankColumns(rest, column) >= CODE_INDENT)) {
      const container = this.container(rest, column, strict);
      if (container === null) break;
      if (!opened) {
        this.closeTo(matched);
        this.leaf = '';
        opened = true;
        paragraph = false;
      }
      [rest, column] = container;
      this.item = container[2] !== QUOTATION;
      this.held.push(container[2]);
      this.fresh = container[3];
      matched = this.held.length;
    }
    if (isBlank(rest)) {
      const kept = this.leaf === 'indented' && matched === this.held.length;
      this.closeTo(matched);
      this.leaf = kept ? 'indented' : '';
      return pageLine(text, 'blank', rest);
    }
    if (this.markdown && blankColumns(rest, column) >= CODE_INDENT) {
      if (paragraph) return pageLine(text, 'text', rest);
      this.closeTo(matched);
      this.leaf = 'indented';
      return pageLine(text, 'indented', rest);
    }
    return this.leafOf(index, text, rest, matched, paragraph);
  }

  /**
   * The container `rest` opens: what it leaves, at which column, itself, whether
   * empty. `strict`: whether a paragraph or indented code stood open above in the
   * line's own container, which an ordered marker other than 1 and an empty marker
   * do not interrupt, on any container the line opens.
   */
  container(rest, column, strict) {
    const mark = this.quoteMark(rest, column);
    if (mark !== null) return [mark[0], mark[1], QUOTATION, false];
    const body = pastBlanks(rest);
    if ((strict && UNDERLINE.test(body)) || THEMATIC_BREAK.test(body)) return null;
    const marker = ITEM_MARKER.exec(body);
    if (marker === null) return null;
    const after = body.slice(marker[0].length);
    const empty = isBlank(after);
    if (strict && (empty || (marker[1] !== undefined && marker[1] !== '1'))) return null;
    const blanks = blankColumns(rest, column);
    const start = column + blanks + marker[0].length;
    const spaces = blankColumns(after, start);
    const deep = this.markdown && spaces > MOST_BLANKS_AFTER_MARKER;
    const padding = empty || deep ? 1 : spaces;
    const left = empty ? '' : pastColumns(after, start, padding);
    return [left, start + padding, blanks + marker[0].length + padding, empty];
  }

  /** What a line with text on it opens past its containers, or the paragraph it continues. */
  leafOf(index, text, rest, matched, paragraph) {
    const body = stripBlanks(rest);
    const strict = paragraph && matched === this.held.length;
    const role = this.oneLineRole(index, body, strict);
    if (role !== null) {
      this.closeTo(matched);
      this.leaf = '';
      return pageLine(text, role, rest);
    }
    const opened = this.concrete(text, rest, body, matched, paragraph);
    if (opened !== null) return opened;
    if (this.tableRow(index, body, matched, paragraph)) return pageLine(text, 'row', rest);
    if (paragraph) return pageLine(text, 'text', rest);
    this.closeTo(matched);
    this.leaf = 'paragraph';
    return pageLine(text, 'paragraph', rest);
  }

  /** The role of a line that is a block by itself, or `null`. */
  oneLineRole(index, body, strict) {
    if (strict && UNDERLINE.test(body)) return 'underline';
    if (ATX_HEADING.test(body)) return 'heading';
    if (THEMATIC_BREAK.test(body)) return 'single';
    if (LEAF_DIRECTIVE.test(body)) return 'single';
    if (!this.markdown && (body[0] === '<' || body[0] === '{')) {
      const taken = this.mdxFlow(index, body);
      if (taken !== null) {
        this.left = taken;
        return 'single';
      }
    }
    return null;
  }

  /**
   * How many more lines the tags and expressions `body` opens take. `null` when
   * text stands beside them, so they are inline ones of a paragraph.
   */
  mdxFlow(index, body) {
    return flowOf([body, ...this.lines.slice(index + 1)].join('\n'))?.lines ?? null;
  }

  /** The fence, the display block, the aside or the HTML block a line opens, or `null`. */
  concrete(text, rest, body, matched, paragraph) {
    const marker = MARKER.exec(rest);
    if (marker !== null && !(marker[2][0] === '`' && marker[3].includes('`'))) {
      this.closeTo(matched);
      this.leaf = 'fence';
      this.opening = marker[2];
      this.indent = marker[1].length;
      return pageLine(text, 'open', rest, marker[3].trim(), this.indent);
    }
    const display = DISPLAY.exec(rest);
    if (display !== null) {
      this.closeTo(matched);
      this.leaf = 'maths';
      this.opening = display[1];
      return pageLine(text, 'maths-open', rest, display[2].trim());
    }
    const aside = ASIDE.exec(body);
    if (aside !== null) {
      this.closeTo(matched);
      this.leaf = '';
      this.asides.push([aside[1].length, this.held.length, blankColumns(rest, 0)]);
      return pageLine(text, 'single', rest);
    }
    return this.markdown ? this.html(text, rest, body, matched, paragraph) : null;
  }

  /** The raw HTML block a line of a `.md` page opens, or `null`. */
  html(text, rest, body, matched, paragraph) {
    for (const [opens, ends] of HTML_BLOCKS) {
      if (opens.test(body)) {
        this.closeTo(matched);
        this.leaf = ends !== null && ends(body) ? '' : 'html';
        this.htmlEnd = ends;
        return pageLine(text, 'html', rest);
      }
    }
    const lazy = paragraph && matched < this.held.length;
    if ((lazy || !paragraph) && HTML_LONE_TAG.test(body)) {
      if (!lazy) this.closeTo(matched);
      this.leaf = 'html';
      this.htmlEnd = null;
      return pageLine(text, 'html', rest);
    }
    return null;
  }

  /** Whether a line of text is a row of a table: the open one's, or a new one's head. */
  tableRow(index, body, matched, paragraph) {
    if (this.leaf === 'table' && matched === this.held.length) return true;
    if (!paragraph) this.closeTo(matched);
    if (index + 1 >= this.lines.length || body === '|') return false;
    const [rest, column, held] = this.pastHeld(this.lines[index + 1], this.held.length);
    const delimiter = stripBlanks(rest);
    if (
      held !== this.held.length ||
      (this.markdown && blankColumns(rest, column) >= CODE_INDENT) ||
      !(delimiter.includes('|') || delimiter.includes(':')) ||
      !DELIMITER_ROW.test(delimiter) ||
      ITEM_MARKER.test(delimiter) ||
      cellCount(body) !== cellCount(delimiter)
    ) {
      return false;
    }
    this.leaf = 'table';
    return true;
  }
}

/**
 * The tags and expressions an `.mdx` flow is made of, as the walk of a page reads
 * one: from the start of `text`, one after another with blanks between them, up to
 * the end of a line with nothing else on it, each as written, and how many lines
 * past the first they take. `null` when text stands beside them on that line, so
 * they are inline ones of a paragraph.
 *
 * @param {string} text A line from its first `<` or `{` on, its blanks off its end,
 *   and the lines after it, joined by a line feed.
 * @returns {{pieces: string[], lines: number} | null}
 */
export function flowOf(text) {
  const pieces = [];
  let at = 0;
  for (;;) {
    const reader = text[at] === '<' ? MDX_TAG : MDX_EXPRESSION;
    reader.lastIndex = at;
    const found = reader.exec(text);
    if (found === null) return null;
    pieces.push(found[0]);
    at = found.index + found[0].length;
    while (text[at] === ' ' || text[at] === '\t') at += 1;
    if (at >= text.length || text[at] === '\n') {
      return { pieces, lines: text.slice(0, at).split('\n').length - 1 };
    }
    if (text[at] !== '<' && text[at] !== '{') return null;
  }
}

/**
 * Every line of a page with its part in the page, read in one walk.
 *
 * @param {Iterable<string>} lines The lines, without their line ends.
 * @param {{ kind?: 'md' | 'mdx' }} [options] The page's kind, which decides what
 *   indentation and a tag mean; a reader that does not know it reads `mdx`.
 * @returns {PageLine[]} One entry per line.
 */
export function pageLines(lines, { kind = 'mdx' } = {}) {
  const walk = new Walk(Array.from(lines), kind);
  return walk.lines.map((_, index) => walk.read(index));
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
 * Whether each line is code: a fence's opening line, its body or its closing line,
 * and indented code on the one kind of page that has it. A fence never closed runs
 * to the end of the page or of what holds it.
 *
 * @param {Iterable<string>} lines The lines, without their line ends.
 * @param {{ kind?: 'md' | 'mdx' }} [options] The page's kind.
 * @returns {boolean[]} One entry per line.
 */
export function codeLines(lines, { kind = 'mdx' } = {}) {
  return pageLines(lines, { kind }).map((line) => CODE_ROLES.has(line.role));
}

/**
 * The page with every line of a fence emptied, so that line numbers still hold.
 *
 * @param {string} text The page.
 * @param {{ kind?: 'md' | 'mdx' }} [options] The page's kind.
 * @returns {string} The prose of the page, its lines joined by a line feed.
 */
export function prose(text, { kind = 'mdx' } = {}) {
  return pageLines(splitLines(text), { kind })
    .map((line) => (CODE_ROLES.has(line.role) ? '' : line.text))
    .join('\n');
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
 * @param {{ kind?: 'md' | 'mdx' }} [options] The page's kind (`pageLines`): a
 *   `.md` page shows a fence indented four columns as code, written out.
 * @returns {Fence[]} One entry per block, closed or running to the end.
 */
export function fences(text, { kind = 'mdx' } = {}) {
  const found = [];
  let start = 0;
  let info = '';
  /** @type {string[]} */
  let body = [];
  const lines = withEnds(text);
  let number = 0;
  for (const line of pageLines(splitLines(text), { kind })) {
    const end = lines[number].slice(line.text.length);
    number += 1;
    if (line.role === 'body') {
      body.push(dedent(line.rest, line.indent) + end);
      continue;
    }
    if (start) {
      found.push(fence(start, info, body));
      start = 0;
    }
    if (line.role === 'open') {
      start = number;
      info = line.info;
      body = [];
    }
  }
  if (start) found.push(fence(start, info, body));
  return found;
}
