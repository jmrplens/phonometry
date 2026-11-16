// Which pages publish a Markdown copy, and where it is.
//
// Every page written as a file publishes a copy written from its own source
// (scripts/agent-md.mjs --public), the two landing pages and the pages that
// render their data through a component included: each component has a writer
// beside it (scripts/check-markdown-writers.mjs, rule F2). Every reader of the
// rule (the head link, the structured data, the page actions, the IndexNow
// manifest) asks hasMarkdownCopy.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { readdirSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { hasMarkdownCopy, markdownCopyPath, routeOf } from '../src/lib/page-markdown.mjs';

const SITE = join(dirname(fileURLToPath(import.meta.url)), '..');
const CONTENT = join(SITE, 'src', 'content', 'docs');

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
