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

import { quotedUnder } from '../src/data/citation.mjs';
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

  test(`a quotation's lines are joined, and it ends where no mark opens one (${kind})`, () => {
    const page = `APA:\n> Requena (2026).\n>\n> *phonometry*.\nAfter.\n`;
    assert.equal(quotedUnder(page, 'APA:', { kind }), 'Requena (2026).\n\n*phonometry*.');
  });

  test(`a label no quotation follows quotes nothing (${kind})`, () => {
    assert.equal(quotedUnder('APA:\n\nNot quoted.\n', 'APA:', { kind }), null);
  });
}

test('a label in a block of code quotes nothing', () => {
  // Indented four columns, the label and the quotation are code on a .md page.
  assert.equal(quotedUnder('Text.\n\n    APA:\n    > x\n', 'APA:', { kind: 'md' }), null);
});

test('a mark four columns deep is indented code on a .md page only', () => {
  assert.deepEqual(quotationMarks(`    > ${REFERENCE}`, { kind: 'md' }), [0, `    > ${REFERENCE}`]);
  assert.deepEqual(quotationMarks(`    > ${REFERENCE}`, { kind: 'mdx' }), [1, REFERENCE]);
});
