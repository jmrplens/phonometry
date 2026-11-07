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

import { dropInlineSpans, dropInlineSpansByBlock, inlineParts, inlineSpans, pageMarkup, SPAN_MARK } from './markdown-spans.mjs';

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
    '> | Run `python |\n> |---|\n> --version` here.',
    'Run `python\n> --version` here.',
    '- Run `python\n> --version` here.',
    '- Run `python\n- --version` here.',
  ];
  for (const text of cases) {
    assert.equal(dropInlineSpansByBlock(text), text, text);
  }
});

test('a span stops at a line that ends the paragraph', () => {
  // Each of these is two blocks to the site, so the two backticks stay apart.
  const cases = [
    'a `b\n---\nc` d',
    'a `b\n***\nc` d',
    'a `b\n___\nc` d',
    'a `b\n* * *\nc` d',
    'a `b\n- - -\nc` d',
    'a `b\n===\nc` d',
    'a `b\n-\nc` d',
    'a `b\n--\nc` d',
    '> a `b\n> ---\n> c` d',
    '> a `b\n> ===\n> c` d',
    '- a `b\n  ---\n  c` d',
    'a `b\n$$\nc` d',
    'a `b\n$$ meta\nc` d',
    '> a `b\n> $$\n> c` d',
    'a `b\n<!-- x -->\nc` d',
    '> a `b\n> <!-- x -->\n> c` d',
    '- a `b\n    - c` d',
    '1. a `b\n    - c` d',
    '> - a `b\n>     - c` d',
    '- a `b\n    ## c` d',
    '- a\n\n  b `c\n    - d` e',
    '- a\n  - b `c\n      - d` e',
    '- a\nb `c\n    - d` e',
    '> - a\n>\n>   b `c\n>     - d` e',
    '---\nkey: a `b\n---\nc` d',
    '- # h `b\nc` d',
    '- ## h `b\n  c` d',
    '1. # h `b\n   c` d',
    '> - # h `b\n> c` d',
    '- <!-- y --> `b\n  c` d',
    'a `b\n<div>\nc` d',
    'a `b\n</div>\nc` d',
    'a `b\n<details>\nc` d',
    'a `b\n<script>\nc` d',
    'a `b\n<pre>\nc` d',
    'a `b\n<?php\nc` d',
    'a `b\n<!x\nc` d',
    'a `b\n<![CDATA[\nc` d',
    '> a `b\n> <div>\n> c` d',
    '-\ta `b\n    - c` d',
    '-\ta `b\n\t- c` d',
    'a `b\n| c |\n|---|\nd` e',
    'a `b\nc | d\n--|--\ne` f',
    'a `b\nc\n:--\nd` e',
    '| a `b |\n|---|\n| c` d |',
    '| a |\n|---|\nb `c\nd` e',
    '| `a | b` |\n|---|---|',
    'a `b\n:::note\nc` d\n:::',
    ':::note\na `b\n:::\nc` d',
    'a `b\n::x\nc` d',
    '    a `b\nc` d',
  ];
  for (const text of cases) {
    assert.equal(dropInlineSpansByBlock(text), text, text);
  }
});

test('a span still runs over a line of its paragraph', () => {
  const cases = [
    ['a `b\n$$x$$\nc` d', `a ${SPAN_MARK}\n\n d`],
    ['a `b\n----x\nc` d', `a ${SPAN_MARK}\n\n d`],
    ['a `b\n<span>\nc` d', `a ${SPAN_MARK}\n\n d`],
    ['  a `b\n    - c` d', `  a ${SPAN_MARK}\n d`],
    ['- a `b\n      - c` d', `- a ${SPAN_MARK}\n d`],
    ['- a `b\n  c` d', `- a ${SPAN_MARK}\n d`],
    ['- a\n\nb `c\n    - d` e', `- a\n\nb ${SPAN_MARK}\n e`],
    // An underline is never lazy, and a pipe with no delimiter row under it, an
    // ordered marker other than 1 and an empty marker do not interrupt a paragraph.
    ['> a `b\n===\nc` d', `> a ${SPAN_MARK}\n\n d`],
    ['> a `b\n=\nc` d', `> a ${SPAN_MARK}\n\n d`],
    ['> a `b\n--\nc` d', `> a ${SPAN_MARK}\n\n d`],
    ['- a `b\n===\nc` d', `- a ${SPAN_MARK}\n\n d`],
    ['1. a `b\n===\nc` d', `1. a ${SPAN_MARK}\n\n d`],
    ['> > a `b\n> ===\n> c` d', `> > a ${SPAN_MARK}\n\n d`],
    ['- > a `b\n  ===\n  c` d', `- > a ${SPAN_MARK}\n\n d`],
    ['a `b\n2. c` d', `a ${SPAN_MARK}\n d`],
    ['- a `b\n    2. c` d', `- a ${SPAN_MARK}\n d`],
    ['a `b\n* \nc` d', `a ${SPAN_MARK}\n\n d`],
    ['a `b\n| c` d', `a ${SPAN_MARK}\n d`],
    ['- a `b\n    | c` d', `- a ${SPAN_MARK}\n d`],
    ['| a `b\nc` d', `| a ${SPAN_MARK}\n d`],
    ['> | Run `python |\n> --version` here.', `> | Run ${SPAN_MARK}\n here.`],
    ['a `b\n:::\nc` d', `a ${SPAN_MARK}\n\n d`],
    ['a `b\n:::x y\nc` d', `a ${SPAN_MARK}\n\n d`],
    ['a `b\n</span>\nc` d', `a ${SPAN_MARK}\n\n d`],
  ];
  for (const [text, shown] of cases) {
    assert.equal(dropInlineSpansByBlock(text), shown, text);
  }
});

test('the kind of a page says where a span stops', () => {
  // A `.md` page has raw HTML and indented code; an `.mdx` page has neither.
  const cases = [
    ['a `b\n<A />\nc` d', `a ${SPAN_MARK}\n\n d`, 'a `b\n<A />\nc` d'],
    ['a `b\n    - c` d', `a ${SPAN_MARK}\n d`, 'a `b\n    - c` d'],
    ['a `b\n{x}\nc` d', `a ${SPAN_MARK}\n\n d`, 'a `b\n{x}\nc` d'],
    ['<div>\n`a`\n</div>', '<div>\n`a`\n</div>', `<div>\n${SPAN_MARK}\n</div>`],
  ];
  for (const [text, md, mdx] of cases) {
    assert.equal(dropInlineSpansByBlock(text, '`', { kind: 'md' }), md, text);
    assert.equal(dropInlineSpansByBlock(text, '`', { kind: 'mdx' }), mdx, text);
    assert.equal(dropInlineSpansByBlock(text, '`', { comments: 'mdx' }), mdx, text);
  }
});

test('an MDX comment may stand between blanks in its braces', () => {
  // MDX shows nothing of an expression that holds only a comment, blanks and all.
  const cases = [
    ['a { /* b */ } c', `a ${SPAN_MARK} c`],
    ['{ /*\nb\n\nc\n*/ }\nd', `${SPAN_MARK}\n\n\n\n\nd`],
  ];
  for (const [text, shown] of cases) {
    assert.equal(dropInlineSpansByBlock(text, '`', { comments: 'mdx' }), shown, text);
  }
});

test('a line of code is not read for a span', () => {
  const text = 'a `b\n```\nc` d\n```\ne` f';
  assert.equal(dropInlineSpansByBlock(text), text);
});

// The page as the site renders it: page_markup of scripts/markdown_spans.py
// and tests/test_markdown_spans.py hold the Python reading to the same cases.
const TAG = '<Video name="a" />';

test('a tag the page does not render is blanked, the lines kept', () => {
  const cases = [
    [`---\ndescription: '${TAG}'\n---\n`, 'mdx'],
    [`\`\`\`mdx\n${TAG}\n\`\`\`\n`, 'mdx'],
    [`~~~\n${TAG}\n~~~\n`, 'mdx'],
    [`- item\n\n  \`\`\`\n  ${TAG}\n  \`\`\`\n`, 'mdx'],
    [`Embed it with \`${TAG}\` here.\n`, 'mdx'],
    [`Embed it with\n\`${TAG}\`\nhere.\n`, 'mdx'],
    [`{/* ${TAG} */}\n`, 'mdx'],
    [`{/*\n${TAG}\n*/}\n`, 'mdx'],
    [`$$\n${TAG}\n$$\n`, 'mdx'],
    [`<!-- ${TAG} -->\n`, 'md'],
    [`Text.\n\n    ${TAG}\n`, 'md'],
    [`Write \\${TAG} here.\n`, 'mdx'],
    [`Write \\${TAG} here.\n`, 'md'],
    [`<code>{'${TAG}'}</code>\n`, 'mdx'],
    [`Text {'${TAG}'} here.\n`, 'mdx'],
    [`\n---\ndescription: '${TAG}'\n---\n`, 'mdx'],
    [`\n \n---\ndescription: '${TAG}'\n---\n`, 'mdx'],
    [`﻿---\ndescription: '${TAG}'\n---\n`, 'mdx'],
    [`+++\ndescription = '${TAG}'\n+++\n`, 'mdx'],
  ];
  for (const [page, kind] of cases) {
    const shown = pageMarkup(page, { kind });
    assert.ok(!shown.includes('<Video'), JSON.stringify(page));
    assert.equal(shown.split('\n').length, page.split('\n').length, JSON.stringify(page));
  }
});

test('a tag the page renders stands where it is written', () => {
  const cases = [
    [`Text.\n\n${TAG}\n`, 'mdx'],
    ['<Video\n  name="a"\n/>\n', 'mdx'],
    [`A clip, ${TAG}, in a paragraph.\n`, 'mdx'],
    [`---\ntitle: A\n---\n\n${TAG}\n`, 'mdx'],
    [`Use \`code\` and then\n${TAG}\n`, 'mdx'],
    [`Text.\n\n    ${TAG}\n`, 'mdx'],
    [`Write \\\\${TAG} here.\n`, 'mdx'],
    [`---\n${TAG}\n`, 'mdx'],
  ];
  for (const [page, kind] of cases) {
    const where = (text) => text.split('\n').map((line) => line.indexOf('<Video'));
    assert.deepEqual(where(pageMarkup(page, { kind })), where(page), JSON.stringify(page));
  }
});

test('a tag the page renders is read whole', () => {
  // No span or expression opens inside it: what its quotes hold is its own.
  const cases = [
    ['<Video alt="from $20" name="a" caption="to $30" />', 'mdx'],
    ['<Video alt="a `b" name="a" caption="c` d" />', 'mdx'],
    ['<Video\n  alt="from $20" name="a" caption="to $30"\n/>', 'mdx'],
    ['<Video name="a" caption={`a ${b}`} />', 'mdx'],
    ['<span title="a `b">c</span>', 'md'],
  ];
  for (const [tag, kind] of cases) {
    assert.ok(pageMarkup(`Text.\n\n${tag} and \`d\`\n`, { kind }).includes(tag), tag);
  }
});

test('a run of inline text is read in parts, each with what it is, whichever opens first taking what follows', () => {
  const text = 'A `b` $c$ \\* {/* $d$ */} <x t="$e$" /> {f} {// g\n} {/* h */ i}.';
  const parts = inlineParts(text).map(({ start, end, what }) => [text.slice(start, end), what]);
  assert.deepEqual(parts, [
    ['`b`', 'code'],
    ['$c$', 'maths'],
    ['\\*', 'escape'],
    ['{/* $d$ */}', 'comment'],
    ['{f}', 'expression'],
    ['{// g\n}', 'comment'],
    ['{/* h */ i}', 'expression'],
  ]);
  // A tag is read whole and is no part: what its attributes write opens nothing.
  assert.deepEqual(inlineParts('<x t="`" /> `y`').map(({ what }) => what), ['code']);
  // On a `.md` page braces are text and an HTML comment shows nothing.
  assert.deepEqual(
    inlineParts('{a} <!-- `b` --> `c`', { kind: 'md' }).map(({ what }) => what),
    ['comment', 'code'],
  );
});

test('what opens first wins between a tag, a span and an expression', () => {
  const written = [
    ['`<Video name="a" />`', false],
    [' ', true],
    ['<Video alt="`" name="b" />', true],
    [' ', true],
    ['{x}', false],
    [' ', true],
    ['`c`', false],
    [' ', true],
    ['\\$', false],
    ['d ', true],
    ['$e$', false],
    ['\n', true],
  ];
  const page = written.map(([piece]) => piece).join('');
  const shown = written.map(([piece, kept]) => (kept ? piece : ' '.repeat(piece.length))).join('');
  assert.equal(pageMarkup(page), shown);
});
