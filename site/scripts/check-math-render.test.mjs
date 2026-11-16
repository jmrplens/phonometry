// The sources check-math-render.mjs reads for a display delimiter on a line of
// content: the site's pages and the files of docs/ written by hand, never a
// file of the GitHub edition, which `make llms` writes from its site page.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, dirname, join } from 'node:path';
import { test } from 'node:test';

import { EDITION_MARK } from '../src/lib/agent-md/edition.mjs';
import { delimiterProblems } from './check-math-render.mjs';

/** A tree of `files` (path below it to text) in a directory of its own, removed after the test. */
function tree(t, files) {
  const root = mkdtempSync(join(tmpdir(), 'check-math-render-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const [path, text] of Object.entries(files)) {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(join(root, path), text);
  }
  return root;
}

/** A reported file, which the check names from the repository root, as a path below `root`. */
const below = (root, file) => file.slice(file.lastIndexOf(basename(root)) + basename(root).length + 1);

/** The text of a page whose display block opens on a line of content. */
const STRAY = '# Levels\n\nThe level is\n\n$$ L = 10 \\log_{10} x\n\nand no more.\n';

test('a stray delimiter is reported in a page and in a file of docs/ written by hand', (t) => {
  const root = tree(t, {
    'content/docs/levels.mdx': `---\ntitle: Levels\n---\n\n${STRAY}`,
    'docs/README.md': STRAY,
  });
  const found = delimiterProblems([join(root, 'docs'), join(root, 'content')]).map(({ file, line }) => [
    below(root, file),
    line,
  ]);
  assert.deepEqual(found, [
    ['docs/README.md', 5],
    ['content/docs/levels.mdx', 9],
  ]);
});

test('a file of the GitHub edition is left to its site page, where the delimiter is reported once', (t) => {
  const opening = `${EDITION_MARK}site/src/content/docs/levels.mdx: edit that page and its Spanish twin, then run \`make llms\`. -->\n`;
  const root = tree(t, {
    'content/docs/levels.mdx': `---\ntitle: Levels\n---\n\n${STRAY}`,
    'docs/levels.md': `${opening}${STRAY}`,
  });
  const found = delimiterProblems([join(root, 'docs'), join(root, 'content')]);
  assert.deepEqual(
    found.map(({ file, line }) => [below(root, file), line]),
    [['content/docs/levels.mdx', 9]],
  );
});

test('a Markdown file that only mentions the edition in its text is still read', (t) => {
  const root = tree(t, { 'docs/notes.md': `Some text, then ${EDITION_MARK}\n\n${STRAY}` });
  assert.equal(delimiterProblems([join(root, 'docs')]).length, 1);
});
