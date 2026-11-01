// The spans the site checks step over, read as the site's Markdown reader
// reads them.
//
// check-i18n-parity.mjs and check-math-render.mjs took every backtick for a
// code marker, so an escaped backtick, which the page shows and which opens
// nothing, hid the prose up to the next one: a figure written between two
// escaped backticks on a Spanish page, or a `$$` delimiter on a content line,
// passed unseen. The cases are those of tests/test_markdown_spans.py, which
// holds the Python reader to the same rules, and the two the checks missed.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { dropInlineSpans, dropInlineSpansByLine, inlineSpans } from './markdown-spans.mjs';

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

test('an escaped backtick hides no figure from the Spanish figure check', () => {
  const page = 'Texto \\`![alt](x.png)\\` aquí.';
  assert.ok(dropInlineSpansByLine(page).includes('!['));
  assert.ok(!dropInlineSpansByLine('Texto `![alt](x.png)` aquí.').includes('!['));
});

test('an escaped backtick hides no display delimiter from the maths check', () => {
  assert.ok(dropInlineSpans('Un \\`$$ x\\` texto').includes('$$'));
  assert.ok(!dropInlineSpans('Un `$$ x` texto').includes('$$'));
});

test('a span is read within its line, as the checks read a page', () => {
  assert.equal(dropInlineSpansByLine('a `x\ny` b'), 'a `x\ny` b');
  assert.equal(dropInlineSpansByLine('a `x` b\nc `y` d'), 'a  b\nc  d');
});
