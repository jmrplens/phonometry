// The Markdown copy of a page with no docs/ mirror keeps what the page shows.
//
// emit-page-markdown.mjs wrote that copy by taking the MDX machinery out with
// patterns over the page as written, so it took an `import` line of a code
// example for the page's own import and dropped it, and took a `<NC-15` in a
// code span for a component and dropped everything from it to the next `/>`.
// The copy is read as the site renders the page now (pageMarkup of
// markdown-spans.mjs): what it takes out is what the page renders as markup.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { stripFrontmatter, stripMdx } from './page-twin.mjs';

const FENCE = '```';

test("the page's own imports and components go, and a wrapper keeps its children", () => {
  const page = [
    "import Video from '../../components/Video.astro';",
    "import { Aside } from '@astrojs/starlight/components';",
    '',
    'A clip:',
    '',
    '<Video name="anim_fdtd_room" />',
    '',
    '<Aside type="note">',
    'Read this.',
    '</Aside>',
  ].join('\n');
  assert.equal(stripMdx(page), 'A clip:\n\nRead this.');
});

test('the import lines of a code example stay, on an .mdx page and on an .md page', () => {
  const example = [`${FENCE}python`, 'import phonometry', 'from phonometry import filters', '', `${FENCE}`].join('\n');
  for (const kind of ['mdx', 'md']) {
    assert.equal(stripMdx(`Run it:\n\n${example}\n`, { kind }), `Run it:\n\n${example}`, kind);
  }
});

test('a component written in a code span or a fence stays as the page shows it', () => {
  // The shape of the room-noise guide: a `<NC-15` in a code span, and a
  // component further down that closes on `/>`.
  const page = [
    'Out of range (`>NC-70` / `<NC-15` when the spectrum falls outside); the',
    'RC box shows `RC-nn(tag)`.',
    '',
    `${FENCE}mdx`,
    '<Video name="anim_fdtd_room" />',
    FENCE,
    '',
    '<ReportPreview name="ansi_s12_2_nc" />',
  ].join('\n');
  const shown = [
    'Out of range (`>NC-70` / `<NC-15` when the spectrum falls outside); the',
    'RC box shows `RC-nn(tag)`.',
    '',
    `${FENCE}mdx`,
    '<Video name="anim_fdtd_room" />',
    FENCE,
  ].join('\n');
  assert.equal(stripMdx(page), shown);
});

test('the blank lines of a code example stay, and runs of them in the prose close up', () => {
  const example = [`${FENCE}python`, 'def a():', '    pass', '', '', 'def b():', '    pass', FENCE].join('\n');
  assert.equal(stripMdx(`One.\n\n\n\nTwo.\n\n${example}`), `One.\n\nTwo.\n\n${example}`);
});

test('a component is written out only where the page renders it', () => {
  const expand = (tag) => (tag === '<CatalogueIndex lang="en" />' ? '- [Solids](/solids/)' : undefined);
  const page = 'Every catalogue:\n\n<CatalogueIndex lang="en" />\n\nWrite `<CatalogueIndex lang="en" />` to list them.';
  assert.equal(
    stripMdx(page, { expand }),
    'Every catalogue:\n\n- [Solids](/solids/)\n\nWrite `<CatalogueIndex lang="en" />` to list them.',
  );
});

test('the frontmatter goes as Astro finds it, after a byte order mark or blank lines too', () => {
  for (const opening of ['', '\n', '\n  \n', '﻿']) {
    assert.equal(stripFrontmatter(`${opening}---\ntitle: A\n---\nBody.\n`), 'Body.\n', JSON.stringify(opening));
  }
  assert.equal(stripFrontmatter('---\nno closing fence\n'), '---\nno closing fence\n');
  assert.equal(stripFrontmatter('Body.\n'), 'Body.\n');
});
