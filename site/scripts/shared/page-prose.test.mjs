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

import { authorsFigure, shownLines, strayDelimiter } from './page-prose.mjs';

test('a figure is found as the Spanish figure check reads a page', () => {
  assert.ok(authorsFigure('Texto \\`![alt](x.png)\\` aquí.'));
  assert.ok(authorsFigure('Texto ![alt][ref] aquí.\n\n[ref]: x.png'));
  assert.ok(authorsFigure('Texto <img src="x.png"> aquí.'));
  assert.ok(!authorsFigure('Texto `![alt](x.png)` aquí.'));
  assert.ok(!authorsFigure('Texto !``x``[alt](x.png) aquí.'));
  assert.ok(!authorsFigure('Texto !`x`[alt](x.png) aquí.'));
  assert.ok(!authorsFigure('```md\n![alt](x.png)\n```\n'));
});

test('an escaped opener writes no figure, and a tag is read in any case', () => {
  // A backslash before `!` or `<` shows the character and opens nothing
  // (CommonMark 2.4): the page shows a link, or the text of a tag. Two
  // backslashes are one shown, and the figure after them is one.
  assert.ok(!authorsFigure('Texto \\![alt](x.png) aquí.'));
  assert.ok(!authorsFigure('Texto \\<img src="x.png"> aquí.'));
  assert.ok(authorsFigure('Texto \\\\![alt](x.png) aquí.'));
  // HTML names a tag in any case; a Markdown page shows `<IMG>` as an image.
  assert.ok(authorsFigure('Texto <IMG src="x.png"> aquí.'));
  assert.ok(authorsFigure('Texto <Img src="x.png"> aquí.'));
});

test('a stray display delimiter is found as the maths check reads a line', () => {
  assert.equal(strayDelimiter('Un \\`$$ x\\` texto'), 'Un \\`$$ x\\` texto');
  assert.equal(strayDelimiter('Un `$$ x` texto'), null);
  assert.equal(strayDelimiter('$$'), null);
  assert.equal(strayDelimiter('$$ x = 1 $$'), null);
  assert.equal(strayDelimiter('$`x`$ texto'), null);
  assert.equal(strayDelimiter('$$ x = 1'), '$$ x = 1');
  // An escaped dollar is shown and opens nothing: no `$$` stands on the line.
  assert.equal(strayDelimiter('Coste \\$$ en euros'), null);
  assert.equal(strayDelimiter('Coste \\\\$$ x'), 'Coste \\\\$$ x');
});

test('a code span read over the lines of its paragraph hides what it holds', () => {
  // The renderer reads a code span across the line breaks of its paragraph;
  // read line by line, a `![`, a `<img` or a `$$` inside one was prose.
  assert.ok(!authorsFigure('Texto `a\n![alt](x.png)\nb` fin.'));
  assert.ok(!authorsFigure('Texto `a\n<img src="x.png">\nb` fin.'));
  // A blank line ends the paragraph, and a span never crosses it.
  assert.ok(authorsFigure('Texto `a\n\n![alt](x.png) `b'));
  const lines = ['Un `ejemplo', '$$ x', 'aquí` y fin.'];
  const shown = shownLines(lines, [false, false, false]);
  assert.equal(shown.length, 3);
  assert.equal(strayDelimiter(shown[1]), null);
  assert.equal(strayDelimiter(shownLines(['Un', '$$ x'], [false, false])[1]), '$$ x');
});

test('a comment shows no figure, and a figure after one is still one', () => {
  assert.ok(!authorsFigure('<!-- <IMG src="old.png"> -->'));
  assert.ok(!authorsFigure('<!-- ![alt](x.png) -->'));
  assert.ok(authorsFigure('<!-- nota --> <img src="x.png">'));
  assert.ok(!authorsFigure('{/* <img src="x.png"> */}', { mdx: true }));
});

test('a tag is an image only when its name is img', () => {
  assert.ok(!authorsFigure('Texto <img-card src="x.png"> aquí.'));
  assert.ok(!authorsFigure('Texto <img.card> aquí.'));
  assert.ok(!authorsFigure('Texto <img:card> aquí.'));
  assert.ok(authorsFigure('Texto <img/> aquí.'));
  assert.ok(authorsFigure('Texto <img\nsrc="x.png"> aquí.'));
});

test('a backslash in a raw HTML block of a .md page escapes nothing', () => {
  // CommonMark sends an HTML block as written: the image shows after the
  // backslash. In MDX the backslash is a markdown escape, and shows the `<`.
  assert.ok(authorsFigure('<div>\\<img src="x.png"></div>'));
  assert.ok(!authorsFigure('<div>\\<img src="x.png"></div>', { mdx: true }));
  assert.ok(!authorsFigure('Texto \\<img src="x.png"> aquí.'));
});

test('an image by reference is one only when the page defines its label', () => {
  assert.ok(!authorsFigure('Texto ![alt] fin.'));
  assert.ok(!authorsFigure('Texto ![alt][missing] fin.'));
  assert.ok(authorsFigure('Texto ![alt][ref] fin.\n\n[ref]: x.png'));
  assert.ok(authorsFigure('Texto ![Alt  Text][] fin.\n\n[alt text]: x.png'));
  assert.ok(authorsFigure('Texto ![logo] fin.\n\n[LOGO]: x.png'));
  assert.ok(authorsFigure('Texto ![alt](x.png) fin.'));
});

test('a pair of display delimiters with a third after it is stray', () => {
  assert.equal(strayDelimiter('$$x$$ text $$'), '$$x$$ text $$');
  assert.equal(strayDelimiter('$$x$$ $$y$$'), '$$x$$ $$y$$');
  assert.equal(strayDelimiter('$$x$$'), null);
});
