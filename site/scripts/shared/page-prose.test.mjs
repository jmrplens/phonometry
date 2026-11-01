// The two readings the site checks make of a page, called on one page.
//
// check-i18n-parity.mjs took every backtick for a code marker, so a figure
// written between two escaped backticks on a Spanish page passed unseen, and
// it joined the text either side of a code span it took out, so a page whose
// code span stood between `!` and `[alt](a.png)` failed the build for a figure
// it never shows. check-math-render.mjs read a `$$` delimiter on a content line
// the same way. Each case here runs through the reading the check itself makes.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { authorsFigure, strayDelimiter } from './page-prose.mjs';

test('a figure is found as the Spanish figure check reads a page', () => {
  assert.ok(authorsFigure('Texto \\`![alt](x.png)\\` aquí.'));
  assert.ok(authorsFigure('Texto ![alt][ref] aquí.'));
  assert.ok(authorsFigure('Texto <img src="x.png"> aquí.'));
  assert.ok(!authorsFigure('Texto `![alt](x.png)` aquí.'));
  assert.ok(!authorsFigure('Texto !``x``[alt](x.png) aquí.'));
  assert.ok(!authorsFigure('Texto !`x`[alt](x.png) aquí.'));
  assert.ok(!authorsFigure('```md\n![alt](x.png)\n```\n'));
});

test('a stray display delimiter is found as the maths check reads a line', () => {
  assert.equal(strayDelimiter('Un \\`$$ x\\` texto'), 'Un \\`$$ x\\` texto');
  assert.equal(strayDelimiter('Un `$$ x` texto'), null);
  assert.equal(strayDelimiter('$$'), null);
  assert.equal(strayDelimiter('$$ x = 1 $$'), null);
  assert.equal(strayDelimiter('$`x`$ texto'), null);
  assert.equal(strayDelimiter('$$ x = 1'), '$$ x = 1');
});
