// The spans the site checks step over, read as the site's Markdown reader
// reads them.
//
// check-i18n-parity.mjs and check-math-render.mjs took every backtick for a
// code marker, so an escaped backtick, which the page shows and which opens
// nothing, hid the prose up to the next one. The cases are those of
// tests/test_markdown_spans.py, which holds the Python reader to the same
// rules; page-prose.test.mjs holds the two checks' readings of a page.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { dropInlineSpans, dropInlineSpansByBlock, inlineSpans, SPAN_MARK } from './markdown-spans.mjs';

const spans = (text, markers = '`') =>
  inlineSpans(text, markers).map(([start, end]) => text.slice(start, end));

test('a span is read as the site reads it', () => {
  const cases = [
    ['a `x` b', '`', ['`x`']],
    ['a ``x ` y`` b', '`', ['``x ` y``']],
    ['a `` x ` b', '`', []],
    ['a \\`x -- y\\` b', '`', []],
    ['\\``x` and `y`', '`', ['`x`', '`y`']],
    ['a \\\\`x` b', '`', ['`x`']],
    ['`%APPDATA%\\phonometry\\` on Windows', '`', ['`%APPDATA%\\phonometry\\`']],
    ['`\\\\` ends a row', '`', ['`\\\\`']],
    ['$x$ and `y`', '`', ['`y`']],
    ['$x$ and `y`', '`$', ['$x$', '`y`']],
    ['\\$5 -- \\$10', '`$', []],
    ['$a\\$ -- b$', '`$', ['$a\\$']],
    ['`$x` then $`y$`', '`$', ['`$x`', '$`y$']],
    ['$a$$b$', '`$', ['$a$$b$']],
  ];
  for (const [text, markers, expected] of cases) {
    assert.deepEqual(spans(text, markers), expected, text);
  }
});

test('the text either side of a span taken out stays apart', () => {
  // The two sides were joined, so a figure, an entity or a display delimiter
  // the page never shows read as written.
  assert.ok(!dropInlineSpans('!``x``[alt](a.png)').includes('!['));
  assert.ok(!dropInlineSpans('&`x`mdash;').includes('&mdash;'));
  assert.ok(!dropInlineSpans('$`x`$', '`').includes('$$'));
});

test('a span wraps inside a quotation', () => {
  // A quotation's marks are not its text, so its paragraph reads as one: each
  // line that opened with `>` was a block of its own, and the two backticks
  // of a span the quotation wraps never paired.
  const cases = [
    ['> Run `python\n> --version` here.', `> Run ${SPAN_MARK}\n here.`],
    ['> - Run `python\n>   --version` here.', `> - Run ${SPAN_MARK}\n here.`],
    ['> Run `python\n--version` here.', `> Run ${SPAN_MARK}\n here.`],
    ['> > Run `python\n> --version` here.', `> > Run ${SPAN_MARK}\n here.`],
    ['> Run\nlazily\n> `python\n> --version` here.', `> Run\nlazily\n> ${SPAN_MARK}\n here.`],
  ];
  for (const [text, shown] of cases) {
    assert.equal(dropInlineSpansByBlock(text), shown, text);
  }
});

test('a span stays inside the paragraph of a quotation', () => {
  // Each of these is two blocks to the site, so the two backticks stay apart.
  const cases = [
    '> Run `python\n>\n> --version` here.',
    '> - Run `python\n> - --version` here.',
    '> Run `python\n> > --version` here.',
    '> # Run `python\n> --version` here.',
    '> | Run `python |\n> --version` here.',
    'Run `python\n> --version` here.',
    '- Run `python\n> --version` here.',
    '- Run `python\n- --version` here.',
  ];
  for (const text of cases) {
    assert.equal(dropInlineSpansByBlock(text), text, text);
  }
});
