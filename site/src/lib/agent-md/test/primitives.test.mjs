// The parser, the table and list primitives and the writer registry: the
// pieces every writer builds on.
//
// Usage (from site/, after `pnpm install`): pnpm run test:agent-md
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, join } from 'node:path';
import { describe, test } from 'node:test';

import { bracketText, cell, htmlAttribute, line, listItem, table } from '../markdown-table.mjs';
import { frontmatterOf, isMdx, parse } from '../processor.mjs';
import { buildRegistry, COMPONENTS_DIR, loadRegistry, writerFiles } from '../registry.mjs';
import { markdownFor } from '../types.mjs';

describe('the parser reads a page as the site does', () => {
  test('MDX with frontmatter, TeX braces, an aside and a component', () => {
    const source = '---\ntitle: "A page"\nsidebar:\n  label: Short\n---\n\nThe level $L_{p}$.\n\n:::note[Why]\nBody.\n:::\n\n<Box kind="x" />\n';
    const tree = parse(source);
    assert.deepEqual(
      tree.children.map((node) => node.type),
      ['yaml', 'paragraph', 'containerDirective', 'mdxJsxFlowElement'],
    );
    assert.equal(tree.children[1].children[1].type, 'inlineMath');
    assert.deepEqual(frontmatterOf(tree), { title: 'A page', sidebar: { label: 'Short' } });
  });

  test('a Markdown page has no MDX: braces and angle brackets are text, HTML is a node', () => {
    const tree = parse('Re{Y} and a <b>bold</b> tag.\n', { mdx: false });
    const types = tree.children[0].children.map((node) => node.type);
    assert.deepEqual(types, ['text', 'html', 'text', 'html', 'text']);
  });

  test('a page without frontmatter has none', () => {
    assert.deepEqual(frontmatterOf(parse('Text.\n')), {});
    assert.equal(isMdx('a/b.mdx'), true);
    assert.equal(isMdx('a/b.md'), false);
  });
});

describe('table and list primitives', () => {
  test('a cell is one line with its pipes escaped', () => {
    assert.equal(cell('a | b\n  c'), String.raw`a \| b c`);
    assert.equal(cell(undefined), '');
    assert.equal(cell(3.5), '3.5');
  });

  test('a short row is padded so the columns after a missing value do not shift', () => {
    assert.equal(table(['a', 'b', 'c'], [['1'], ['1', '2', '3']]), '| a | b | c |\n| --- | --- | --- |\n| 1 |  |  |\n| 1 | 2 | 3 |');
  });

  test('link text and HTML attributes are escaped for where they go', () => {
    assert.equal(bracketText('a [b] | c\nd'), String.raw`a \[b\] \| c d`);
    assert.equal(htmlAttribute('say "a" & <b>'), 'say &quot;a&quot; &amp; &lt;b&gt;');
    assert.equal(line('  a\n\tb  '), 'a b');
  });

  test('a list item keeps a multi-block body inside the item', () => {
    assert.equal(listItem('**Covered.**', 'First line\nsecond line.\n\nA second paragraph.'), '- **Covered.** First line\n  second line.\n\n  A second paragraph.');
    assert.equal(listItem('**Covered.**', '- a\n- b'), '- **Covered.**\n\n  - a\n  - b');
    assert.equal(listItem('**Covered.**', '```python\nx = 1\n```'), '- **Covered.**\n\n  ```python\n  x = 1\n  ```');
    assert.equal(listItem('**Covered.**', ''), '- **Covered.**');
  });
});

describe('the registry', () => {
  const writer = (tag) => ({ default: markdownFor({ tag, props: [], toMarkdown: () => '' }) });

  test('a writer is named after its component and claims one tag', () => {
    const registry = buildRegistry({ '/c/Box.md.mjs': writer('Box'), '/c/home/Home.md.mjs': writer('Home') });
    assert.deepEqual([...registry.keys()], ['Box', 'Home']);
    assert.throws(() => buildRegistry({ '/c/Box.md.mjs': writer('Other') }), /declares tag "Other"; a writer is named after its component \(Box\)/);
    assert.throws(() => buildRegistry({ '/a/Box.md.mjs': writer('Box'), '/b/Box.md.mjs': writer('Box') }), /two writers claim <Box>/);
    assert.throws(() => buildRegistry({ '/c/Box.md.mjs': {} }), /has no default export/);
  });

  test('markdownFor refuses a writer without a component name, its props or a function', () => {
    assert.throws(() => markdownFor({ tag: 'div', props: [], toMarkdown: () => '' }), /needs a component name/);
    assert.throws(() => markdownFor({ tag: 'Box', toMarkdown: () => '' }), /needs the list of props/);
    assert.throws(() => markdownFor({ tag: 'Box', props: [] }), /needs a toMarkdown function/);
  });

  test('writers are found under any depth of the components directory', async (t) => {
    const dir = mkdtempSync(join(tmpdir(), 'agent-md-registry-'));
    t.after(() => rmSync(dir, { recursive: true, force: true }));
    mkdirSync(join(dir, 'nested'));
    const types = new URL('../types.mjs', import.meta.url).href;
    for (const [path, tag] of [['Box.md.mjs', 'Box'], ['nested/Deep.md.mjs', 'Deep']]) {
      writeFileSync(join(dir, path), `import { markdownFor } from '${types}';\nexport default markdownFor({ tag: '${tag}', props: [], toMarkdown: () => '${tag}' });\n`);
    }
    writeFileSync(join(dir, 'Box.astro'), '---\n---\n');
    assert.deepEqual(writerFiles(dir).map((file) => basename(file)), ['Box.md.mjs', 'Deep.md.mjs']);
    assert.deepEqual([...(await loadRegistry(dir)).keys()], ['Box', 'Deep']);
  });

  test('every writer of the site sits beside its component and opens with what it keeps and drops', async () => {
    const registry = await loadRegistry();
    for (const file of writerFiles()) {
      const astro = file.replace(/\.md\.mjs$/u, '.astro');
      assert.doesNotThrow(() => readFileSync(astro), `${file} has no ${basename(astro)} beside it`);
      assert.match(readFileSync(file, 'utf8'), /^\/\*\*\n \* \S/u, `${basename(file)} opens with its keep/drop comment`);
    }
    assert.ok(registry.size >= 12, `expected the writers under ${COMPONENTS_DIR}`);
  });
});
