/**
 * The check of the copies against the pages' sources (scripts/check-markdown-twins.mjs,
 * `checkCopiesAgainstSources`): a line of the page's code, the entries and DOIs of
 * its references, the figures, clips and fiches it renders, and the bibliography's
 * entries, each lost from a copy, fail it.
 */
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';

import { checkCopiesAgainstSources } from '../../../../scripts/check-markdown-twins.mjs';

const SITE = 'https://docs.jmrp.io/phonometry';
const SOURCE = [
  '---',
  'title: "A guide"',
  'references:',
  '  - type: article',
  '    authors: ["Doe, J."]',
  '    year: 2001',
  '    title: "A paper"',
  '    doi: "10.1000/xyz"',
  '---',
  '',
  "import ThemeImage from '../../components/ThemeImage.astro';",
  '',
  'Some text.',
  '',
  '<ThemeImage name="filters/bank" alt="A bank" />',
  '',
  '```python',
  'from phonometry import filters',
  'bank = filters.OctaveFilterBank(48000)',
  '```',
  '',
].join('\n');
const COPY = [
  '# A guide',
  '',
  'Canonical: https://docs.jmrp.io/phonometry/signals/guide/',
  '',
  'Some text.',
  '',
  `![A bank](${SITE}/media/filters/bank.svg)`,
  '',
  '```python',
  'from phonometry import filters',
  'bank = filters.OctaveFilterBank(48000)',
  '```',
  '',
  '## References',
  '',
  '- **Doe, J. (2001).** A paper. https://doi.org/10.1000/xyz',
  '',
].join('\n');

/**
 * A content tree with one guide and a build with its copy, changed by `edit`;
 * `source` changes the page as the checkout writes it.
 */
function tree(t, edit = (text) => text, source = (text) => text) {
  const root = mkdtempSync(join(tmpdir(), 'source-copies-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const write = (path, text) => {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(join(root, path), text);
  };
  write('content/signals/guide.mdx', source(SOURCE));
  write('dist/signals/guide/index.md', edit(COPY));
  return { contentDir: join(root, 'content'), dist: join(root, 'dist') };
}

test('a copy that carries its page passes', async (t) => {
  const { contentDir, dist } = tree(t);
  assert.deepEqual(await checkCopiesAgainstSources(dist, { contentDir, routes: ['/signals/guide/'] }), []);
});

test('a page checked out with carriage returns is read as the commit holds it', async (t) => {
  // A clone made with core.autocrlf=true writes a carriage return before every
  // line feed of the page; its copy is written from the page as committed.
  const { contentDir, dist } = tree(t, undefined, (text) => text.replaceAll('\n', '\r\n'));
  assert.deepEqual(await checkCopiesAgainstSources(dist, { contentDir, routes: ['/signals/guide/'] }), []);
});

for (const [what, edit, message] of [
  ['a line of its code', (text) => text.replace('bank = filters.OctaveFilterBank(48000)\n', ''), /lost line .* of the page's code/u],
  ['a DOI', (text) => text.replace(' https://doi.org/10.1000/xyz', ''), /leaves out the DOI 10\.1000\/xyz/u],
  ['an entry of its references', (text) => text.replace(/^- \*\*Doe.*$/mu, 'https://doi.org/10.1000/xyz'), /References section holds 0 entries/u],
  ['a figure', (text) => text.replace(/^!\[A bank\].*$/mu, ''), /writes 0 of the 1 figure/u],
]) {
  test(`a copy that loses ${what} of its page fails`, async (t) => {
    const { contentDir, dist } = tree(t, edit);
    const found = await checkCopiesAgainstSources(dist, { contentDir, routes: ['/signals/guide/'] });
    assert.equal(found.length, 1, JSON.stringify(found));
    assert.match(found[0], message);
  });
}

test("the bibliography's copy holds one entry per entry its built page lists", async (t) => {
  const root = mkdtempSync(join(tmpdir(), 'source-copies-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, 'dist', 'reference', 'bibliography'), { recursive: true });
  const items = '<li id="std-iso-1">ISO 1. <span data-cited-by>Cited by <a href="/phonometry/a/">A</a></span></li>'.repeat(2);
  writeFileSync(join(root, 'dist', 'reference', 'bibliography', 'index.html'), `<main><ul>${items}</ul></main>`);
  const entry = '- ISO 1. Cited by [A](https://docs.jmrp.io/phonometry/a/).\n';
  writeFileSync(join(root, 'dist', 'reference', 'bibliography', 'index.md'), `# Bibliography\n\n${entry}`);
  const found = await checkCopiesAgainstSources(join(root, 'dist'), { contentDir: join(root, 'content'), routes: [] });
  assert.equal(found.length, 1, JSON.stringify(found));
  assert.match(found[0], /\/reference\/bibliography\/: its copy lists 1 of the 2 works the page lists/u);
});
