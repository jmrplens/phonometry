// The failures scripts/check-markdown-writers.mjs exists to report, on sites
// small enough to read, and the one fact about the real site it pins.
//
// The real pages only ever hand the check what passes, so a check that
// stopped seeing a component without a writer, a prop nobody declared or an
// expression nobody can read would stay green there for good. Each test here
// writes a content directory and a components directory of a few files, runs
// the check on them and reads what it reports.
//
// Usage (from site/, after `pnpm install`): pnpm run test:agent-md
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, dirname, join, relative } from 'node:path';
import { describe, test } from 'node:test';

import { checkMarkdownWriters, isParseError, openingProblem } from '../../../../scripts/check-markdown-writers.mjs';
import { pageFiles } from '../content.mjs';
import { parse } from '../processor.mjs';
import { writerFiles, WRITER_SUFFIX } from '../registry.mjs';
import { CONTENT_DIR, SITE_DIR } from '../render.mjs';

const TYPES = new URL('../types.mjs', import.meta.url).href;

/** A writer file with the opening comment every writer carries. */
const writer = (tag, { props = [], comment = `${tag}: kept whole, as its children.` } = {}) =>
  [
    '/**',
    ` * ${comment}`,
    ' */',
    `import { markdownFor } from '${TYPES}';`,
    `export default markdownFor({ tag: '${tag}', props: ${JSON.stringify(props)}, toMarkdown: (node, ctx) => ctx.body(node) });`,
    '',
  ].join('\n');

/**
 * Writes a small site and checks it.
 *
 * @param {import('node:test').TestContext} t
 * @param {Record<string, string>} pages  Content files by path.
 * @param {Record<string, string>} [writers]  Writer files by path.
 */
async function check(t, pages, writers = { 'Box.md.mjs': writer('Box', { props: ['kind'] }) }) {
  const root = mkdtempSync(join(tmpdir(), 'check-markdown-writers-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const write = (dir, files) => {
    for (const [path, text] of Object.entries(files)) {
      mkdirSync(dirname(join(root, dir, path)), { recursive: true });
      writeFileSync(join(root, dir, path), text);
    }
  };
  mkdirSync(join(root, 'content'), { recursive: true });
  mkdirSync(join(root, 'components'), { recursive: true });
  write('content', pages);
  write('components', writers);
  return checkMarkdownWriters({ contentDir: join(root, 'content'), componentsDir: join(root, 'components') });
}

/** The failures, as `kind where` lines, sorted. */
const listed = (result) => result.failures.map((failure) => `${failure.kind} ${failure.where}`).sort();

const BOX = "import Box from '../components/Box.astro';\n\n";

describe('what the check refuses', () => {
  test('a site whose every component has its writer passes', async (t) => {
    const result = await check(t, {
      'a.mdx': `${BOX}Text $L_{p}$.\n\n<Box kind="x">Inside.</Box>\n`,
      'es/b.mdx': `${BOX}:::note[Ojo]\nTexto.\n:::\n\n<Box />\n`,
      'c.md': 'Plain <!-- a comment --> page.\n',
    });
    assert.deepEqual(result.failures, []);
    assert.equal(result.pages, 3);
    assert.deepEqual([...result.used], [['Box', 2]]);
  });

  test('a component with no writer, where it is imported and where it is used', async (t) => {
    const result = await check(t, {
      'a.mdx': `${BOX}import Missing from '../components/Missing.astro';\n\n<Box />\n\n<Missing />\n`,
    });
    assert.deepEqual(listed(result), ['component a.mdx:3', 'component a.mdx:7']);
  });

  test('a prop the writer does not declare (the SeeAlso links that published an empty panel)', async (t) => {
    const result = await check(t, { 'a.mdx': `${BOX}<Box kind="x" links={[{ href: '/a/' }]} />\n` });
    assert.deepEqual(listed(result), ['prop a.mdx:3']);
    assert.match(result.failures[0].message, /passes "links", which Box\.md\.mjs does not declare/u);
  });

  test('an expression that is neither a literal nor an allow-listed import ({totalChecks} without its import)', async (t) => {
    const result = await check(t, { 'a.mdx': `${BOX}<Box />\n\nThe report runs {totalChecks} checks.\n` });
    assert.deepEqual(listed(result), ['expression a.mdx:5']);
  });

  test('the same expression with its import from an allow-listed module passes', async (t) => {
    const root = mkdtempSync(join(tmpdir(), 'check-markdown-writers-'));
    t.after(() => rmSync(root, { recursive: true, force: true }));
    mkdirSync(join(root, 'content'));
    mkdirSync(join(root, 'components'));
    writeFileSync(join(root, 'components', 'Box.md.mjs'), writer('Box'));
    const stats = join(SITE_DIR, 'src', 'data', 'conformance-stats.mjs');
    const from = join(root, 'content');
    const specifier = relative(from, stats);
    writeFileSync(join(from, 'a.mdx'), `import { totalChecks } from '${specifier}';\n${BOX}<Box />\n\nThe report runs {totalChecks} checks.\n`);
    const result = await checkMarkdownWriters({ contentDir: from, componentsDir: join(root, 'components') });
    assert.deepEqual(result.failures, []);
  });

  test('raw HTML with no rule, and an aside Starlight does not draw', async (t) => {
    const result = await check(t, { 'a.mdx': `${BOX}<Box />\n\n<marquee>Moving.</marquee>\n\n:::warning\nCareful.\n:::\n` });
    assert.deepEqual(listed(result), ['directive a.mdx:7', 'html a.mdx:5']);
  });

  test('a page that does not parse, at the line the parser names', async (t) => {
    const result = await check(t, { 'a.mdx': `${BOX}<Box kind="x">\n\nNever closed.\n`, 'b.mdx': `${BOX}<Box />\n` });
    assert.deepEqual(listed(result), ['parse a.mdx:3']);
    assert.match(result.failures[0].message, /Expected a closing tag for `<Box>`/u);
  });

  test('a page that does not parse calls no writer stale: it may be the page that uses it', async (t) => {
    const only = "import Only from '../components/Only.astro';\n\n";
    const result = await check(
      t,
      { 'a.mdx': `${only}<Only>\n\nNever closed.\n`, 'b.mdx': `${BOX}<Box />\n` },
      { 'Box.md.mjs': writer('Box'), 'Only.md.mjs': writer('Only') },
    );
    assert.deepEqual(listed(result), ['parse a.mdx:3']);
  });

  test('a writer that throws or returns no string', async (t) => {
    const broken = [
      '/**',
      ' * Box: kept whole, until it throws.',
      ' */',
      `import { markdownFor } from '${TYPES}';`,
      "export default markdownFor({ tag: 'Box', props: [], toMarkdown: () => { throw new Error('no data'); } });",
      '',
    ].join('\n');
    const result = await check(t, { 'a.mdx': `${BOX}<Box />\n` }, { 'Box.md.mjs': broken });
    assert.deepEqual(listed(result), ['writer a.mdx:3']);
    assert.match(result.failures[0].message, /Box\.md\.mjs threw: no data/u);
  });

  test('a writer no page uses is stale', async (t) => {
    const result = await check(t, { 'a.mdx': `${BOX}<Box />\n` }, { 'Box.md.mjs': writer('Box'), 'old/Old.md.mjs': writer('Old') });
    assert.deepEqual(listed(result), ['stale Old.md.mjs']);
  });

  test('a writer without its keep/drop comment', async (t) => {
    const bare = `import { markdownFor } from '${TYPES}';\nexport default markdownFor({ tag: 'Box', props: [], toMarkdown: () => '' });\n`;
    const result = await check(t, { 'a.mdx': `${BOX}<Box />\n` }, { 'Box.md.mjs': bare });
    assert.deepEqual(listed(result), ['opening Box.md.mjs']);
  });
});

test('a syntax error is told apart from a module that failed to load', () => {
  let syntax;
  try {
    parse('<Box kind="x">\n\nNever closed.\n');
  } catch (error) {
    syntax = error;
  }
  assert.ok(isParseError(syntax));
  assert.equal(isParseError(new Error('docs/ERRATA.md not found')), false);
  assert.equal(isParseError(undefined), false);
});

describe('the opening comment', () => {
  test('names its component and says what it keeps or drops', () => {
    assert.equal(openingProblem('/**\n * Box: kept whole.\n */\n', 'Box'), undefined);
    assert.equal(openingProblem('/**\n * Box: dropped on purpose.\n */\n', 'Box'), undefined);
    assert.match(openingProblem('/**\n * Other: kept whole.\n */\n', 'Box'), /about Other, not Box/u);
    assert.match(openingProblem('/**\n * Box: a box.\n */\nconst kept = 1;\n', 'Box'), /does not say what it keeps or drops/u);
    assert.match(openingProblem('// Box: kept whole.\n', 'Box'), /does not open with/u);
  });
});

test('the writers are exactly the components the pages import', () => {
  const imported = new Set();
  for (const file of pageFiles(CONTENT_DIR)) {
    for (const match of readFileSync(file, 'utf8').matchAll(/^import (\w+) from '[^']*\/components\/[^']+\.astro';$/gmu)) {
      imported.add(match[1]);
    }
  }
  const writers = new Set(writerFiles().map((file) => basename(file, WRITER_SUFFIX)));
  assert.deepEqual([...writers].sort(), [...imported].sort());
  assert.deepEqual(
    [...writers].sort(),
    [
      'CatalogueFinder',
      'CatalogueIndex',
      'CatalogueRouter',
      'Catalogues',
      'Conformance',
      'ErrataFamily',
      'ErrataRouter',
      'Glossary',
      'Home',
      'ReportIndex',
      'ReportPreview',
      'Scope',
      'ScopeClaim',
      'SeeAlso',
      'ThemeImage',
      'Video',
    ],
  );
  assert.ok(readdirSync(CONTENT_DIR).length > 0);
});
