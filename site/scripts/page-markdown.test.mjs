// Which pages publish a Markdown copy, and where a route's GitHub copy is.
//
// Every page written as a file publishes a copy written from its own source
// (scripts/agent-md.mjs --public), the two landing pages and the pages that
// render their data through a component included: each component has a writer
// beside it (scripts/check-markdown-writers.mjs, rule F2). Every reader of the
// rule (the head link, the structured data, the page actions, the IndexNow
// manifest) asks hasMarkdownCopy. docs/ keeps the plain-Markdown edition GitHub
// serves, and mirrorOf says which file of it stands for a route.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, sep } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { hasMarkdownCopy, markdownCopyPath, mirrorOf, routeOf } from '../src/lib/page-markdown.mjs';

const SITE = join(dirname(fileURLToPath(import.meta.url)), '..');
const CONTENT = join(SITE, 'src', 'content', 'docs');

/** A tree of `files` (path below it to text) in a directory of its own. */
function tree(t, files) {
  const root = mkdtempSync(join(tmpdir(), 'page-markdown-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const [path, text] of Object.entries(files)) {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(join(root, path), text);
  }
  return { contentDir: join(root, 'content'), docsDir: join(root, 'docs') };
}


test('the copy of a route comes from docs/ where the mirror or a transplanted document holds it', (t) => {
  const { docsDir } = tree(t, {
    'docs/guides/levels.md': '# Levels\n',
    'docs/start/index.md': '# Start\n',
    'docs/ERRATA.es.md': '# Erratas\n',
    'docs/CONFORMANCE.md': '# Conformance\n',
  });
  assert.equal(mirrorOf('guides/levels', docsDir), join(docsDir, 'guides', 'levels.md'));
  assert.equal(mirrorOf('start', docsDir), join(docsDir, 'start', 'index.md'));
  assert.equal(mirrorOf('reference/conformance', docsDir), join(docsDir, 'CONFORMANCE.md'));
  assert.equal(mirrorOf('es/reference/errata', docsDir), join(docsDir, 'ERRATA.es.md'));
  assert.equal(mirrorOf('es/guides/levels', docsDir), undefined, 'the mirror is English');
  assert.equal(mirrorOf('guides/other', docsDir), undefined);
});

/** Every page of the site's content tree, as paths below it. */
function contentPages(dir = CONTENT, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) contentPages(path, out);
    else if (/\.mdx?$/.test(entry.name)) out.push(relative(CONTENT, path).split(sep).join('/'));
  }
  return out.sort();
}

test('every page of the site publishes a copy at <page>/index.md, the landing pages included, and the 404 none', () => {
  const routes = contentPages().map(routeOf);
  assert.ok(routes.includes('') && routes.includes('es') && routes.includes('reference/catalogues/solids'));
  for (const route of routes) assert.equal(hasMarkdownCopy(route), true, route);
  assert.equal(hasMarkdownCopy('404'), false);
  assert.equal(markdownCopyPath('', '/phonometry'), '/phonometry/index.md');
  assert.equal(markdownCopyPath('es/start', '/phonometry'), '/phonometry/es/start/index.md');
});
