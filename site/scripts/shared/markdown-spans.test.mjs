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

import { dropInlineSpans, inlineSpans, SPAN_MARK } from './markdown-spans.mjs';

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

