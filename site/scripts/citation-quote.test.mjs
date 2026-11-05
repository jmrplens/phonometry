// The APA reference src/data/citation.mjs reads from the pages that cite the
// project, quoted under its label.
//
// The quotation was read with a pattern of a line opening with `>`, its marks
// stripped with `>` and one blank, so a second mark behind a tab stayed in the
// reference and a mark behind a space opened no quotation at all, where the
// published page reads both as quoted. The marks are read by their columns now,
// as the walk of the page reads them, and the twin readers agree on them.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { quotedUnder, showsInProse } from '../src/data/citation.mjs';
import { quotationMarks } from '../src/lib/markdown-fences.mjs';

const REFERENCE = 'Requena (2026). *phonometry*.';

for (const kind of ['md', 'mdx']) {
  test(`a quotation is read past its marks as the page reads them (${kind})`, () => {
    for (const quoted of [
      `> ${REFERENCE}`,
      `>\t> ${REFERENCE}`,
      ` > ${REFERENCE}`,
      `>${REFERENCE}`,
    ]) {
      const page = `Cite it.\n\nAPA:\n\n${quoted}\n\nNext.\n`;
      assert.equal(quotedUnder(page, 'APA:', { kind }), REFERENCE, quoted);
    }
  });

  test(`a quotation's lines are joined, a lazy line among them, and a blank one ends it (${kind})`, () => {
    // A line no mark opens carries the quotation's paragraph on, as the walk
    // of the page reads it; it was read as the end of the quotation.
    const lazy = `APA:\n> Requena (2026).\n>\n> *phonometry*.\nAfter.\n`;
    assert.equal(quotedUnder(lazy, 'APA:', { kind }), 'Requena (2026).\n\n*phonometry*.\nAfter.');
    const ended = `APA:\n> Requena (2026).\n>\n> *phonometry*.\n\nAfter.\n`;
    assert.equal(quotedUnder(ended, 'APA:', { kind }), 'Requena (2026).\n\n*phonometry*.');
    const doi = `APA:\n\n> Requena (2026). *phonometry*.\nhttps://doi.org/10.5281/zenodo.1\n\nNext.\n`;
    assert.equal(
      quotedUnder(doi, 'APA:', { kind }),
      'Requena (2026). *phonometry*.\nhttps://doi.org/10.5281/zenodo.1',
    );
  });

  test(`a block of code inside the quotation is no part of the reference (${kind})`, () => {
    // The lines of a fence in the quotation were read as the reference's, so
    // an example could carry what the reference itself lacks.
    const page = `APA:\n\n> Requena (2026).\n> \`\`\`\n> ${REFERENCE}\n> \`\`\`\n\nNext.\n`;
    assert.equal(quotedUnder(page, 'APA:', { kind }), 'Requena (2026).');
  });

  test(`a label no quotation follows quotes nothing (${kind})`, () => {
    assert.equal(quotedUnder('APA:\n\nNot quoted.\n', 'APA:', { kind }), null);
  });
}

test('a label the page does not show is passed over for the next one', () => {
  // The first line that spelt the label stood for it, a commented one too,
  // and a quotation that did not follow it hid the one under the label shown.
  const commented = (comment) => `Text.\n\n${comment}\n\nAPA:\n\n> ${REFERENCE}\n`;
  assert.equal(quotedUnder(commented('<!--\nAPA:\n-->'), 'APA:', { kind: 'md' }), REFERENCE);
  assert.equal(quotedUnder(commented('{/*\nAPA:\n*/}'), 'APA:', { kind: 'mdx' }), REFERENCE);
  // A label shown with no quotation under it gives way to a later one.
  const twice = `APA:\n\nNot quoted.\n\nAPA:\n\n> ${REFERENCE}\n`;
  assert.equal(quotedUnder(twice, 'APA:', { kind: 'md' }), REFERENCE);
});

test('a link the page does not show is no link of the page', () => {
  // The bold link to the record was looked for in the whole source, so one
  // left in a comment or a block of code stood for one the page shows.
  const link = '**[doi.org/10.5281/zenodo.1](https://doi.org/10.5281/zenodo.1)**';
  assert.equal(showsInProse(`Text.\n\n${link}\n`, link, { kind: 'md' }), true);
  assert.equal(showsInProse(`Text.\n\n<!--\n${link}\n-->\n`, link, { kind: 'md' }), false);
  assert.equal(showsInProse(`Text.\n\n{/*\n${link}\n*/}\n`, link, { kind: 'mdx' }), false);
  assert.equal(showsInProse(`Text.\n\n\`\`\`\n${link}\n\`\`\`\n`, link, { kind: 'mdx' }), false);
});

test('a label in a block of code quotes nothing', () => {
  // Indented four columns, the label and the quotation are code on a .md page.
  assert.equal(quotedUnder('Text.\n\n    APA:\n    > x\n', 'APA:', { kind: 'md' }), null);
});

test('a mark four columns deep is indented code on a .md page only', () => {
  assert.deepEqual(quotationMarks(`    > ${REFERENCE}`, { kind: 'md' }), [0, `    > ${REFERENCE}`]);
  assert.deepEqual(quotationMarks(`    > ${REFERENCE}`, { kind: 'mdx' }), [1, REFERENCE]);
});
