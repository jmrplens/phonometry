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

import { census } from '../../../../scripts/agent-md.mjs';
import { checkMarkdownWriters, isParseError, openingProblem, REMEDIES } from '../../../../scripts/check-markdown-writers.mjs';
import { codeLines, splitLines } from '../../markdown-fences.mjs';
import { markdownPlugins } from '../rewrites.mjs';
import { pageFiles } from '../content.mjs';
import { parse } from '../processor.mjs';
import { writerFiles, WRITER_SUFFIX } from '../registry.mjs';
import { CONTENT_DIR, DATA_MODULES, SITE_DIR } from '../render.mjs';

const TYPES = new URL('../types.mjs', import.meta.url).href;

/** A writer file with the opening comment every writer carries. */
const writer = (tag, { props = [], comment = `${tag}: kept whole, as its children. Dropped: nothing.` } = {}) =>
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

  test('an expression or a spread in an attribute of raw HTML, with a rule or without one', async (t) => {
    // `<a href={x}>` used to be written as its text alone: the HTML rule read
    // the unreadable href as absent, and nothing was recorded.
    const result = await check(t, {
      'a.mdx': [
        `${BOX}<Box />`,
        '',
        'A link with an expression: <a href={someVar}>see here</a>.',
        '',
        '<div {...props}>Spread.</div>',
        '',
        '<marquee title={x}>Moving.</marquee>',
        '',
      ].join('\n'),
    });
    assert.deepEqual(listed(result), ['expression a.mdx:5', 'expression a.mdx:9', 'html a.mdx:9', 'prop a.mdx:7']);
    const messages = result.failures.map((failure) => failure.message);
    assert.ok(messages.includes(`<a href={...}> is neither a literal nor a value imported from ${DATA_MODULES.join(' or ')}`), messages.join('\n'));
    assert.ok(messages.includes('<div> spreads attributes, which agent-md/render.mjs cannot read'), messages.join('\n'));
  });

  test('a literal in an attribute of raw HTML passes', async (t) => {
    const result = await check(t, { 'a.mdx': `${BOX}<Box />\n\nSee <a href={'/a/'}>the guide</a> and <span id="old" />.\n` });
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
      ' * Box: kept whole, until it throws. Dropped: nothing.',
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

  test('a site checked out with carriage returns passes as it does with line feeds', async (t) => {
    const crlf = (text) => text.replaceAll('\n', '\r\n');
    const result = await check(t, { 'a.mdx': crlf(`${BOX}<Box kind="x" />\n`) }, { 'Box.md.mjs': crlf(writer('Box', { props: ['kind'] })) });
    assert.deepEqual(listed(result), []);
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
  test('names its component and says what it keeps and what it drops', () => {
    assert.equal(openingProblem('/**\n * Box: kept whole.\n *\n * Dropped: the frame it draws.\n */\n', 'Box'), undefined);
    assert.match(openingProblem('/**\n * Other: kept whole.\n */\n', 'Box'), /about Other, not Box/u);
    assert.match(openingProblem('// Box: kept whole.\n', 'Box'), /does not open with/u);
  });

  test('one statement is not enough: what is kept, or what is dropped, alone fails', () => {
    assert.match(openingProblem('/**\n * Box: kept whole.\n */\n', 'Box'), /does not say what it drops \(/u);
    assert.match(openingProblem('/**\n * Box: a box.\n *\n * Dropped: its frame.\n */\n', 'Box'), /does not say what it keeps \(/u);
    assert.match(openingProblem('/**\n * Box: a box.\n */\nconst kept = 1; // dropped\n', 'Box'), /does not say what it keeps or what it drops/u);
  });

  test('a writer that writes nothing says so in its first line, and that is the whole statement', () => {
    assert.equal(openingProblem('/**\n * Box: dropped on purpose.\n *\n * It is a picker.\n */\n', 'Box'), undefined);
    assert.match(openingProblem('/**\n * Box: dropped on purpose, mostly.\n */\n', 'Box'), /does not say what it keeps \(one that writes nothing opens with 'Box: dropped on purpose\.'\)/u);
  });
});

/**
 * The components a page imports, read off its lines that are not code: an
 * import line a fenced example shows is no import of the page.
 *
 * @param {string} text
 * @returns {string[]}
 */
function componentImports(text) {
  const lines = splitLines(text);
  const code = codeLines(lines);
  const prose = lines.map((one, at) => (code[at] ? '' : one)).join('\n');
  return [...prose.matchAll(/^import\s+(\w+)\s+from\s+(["'])[^"'\n]*\/components\/[^"'\n]+\.astro\2;?[ \t]*$/gmu)].map((match) => match[1]);
}

test('an import line a fenced example shows is not an import of the page', () => {
  const page = "import Box from '../components/Box.astro';\n\n```mdx\nimport Shown from '../components/Shown.astro';\n```\n";
  assert.deepEqual(componentImports(page), ['Box']);
});

test('an import of a component is read in either quote, with or without its semicolon, and over two lines', () => {
  const page = 'import Box from "../components/Box.astro";\nimport Card from \'../components/Card.astro\'\nimport Wide\n  from "../components/Wide.astro";\n';
  assert.deepEqual(componentImports(page), ['Box', 'Card', 'Wide']);
});

test('every kind of failure the check reports has its remedy', () => {
  const sources = ['../../../../scripts/check-markdown-writers.mjs', '../render.mjs'].map((path) =>
    readFileSync(new URL(path, import.meta.url), 'utf8'),
  );
  const kinds = new Set(sources.flatMap((text) => [...text.matchAll(/\bkind: '(\w+)'|\breport\('(\w+)'/gu)].map((m) => m[1] ?? m[2])));
  for (const kind of ['parse', 'import', 'plugin', 'stale', 'opening']) assert.ok(kinds.has(kind), kind);
  for (const kind of kinds) assert.equal(typeof REMEDIES[kind], 'string', `no remedy for ${kind}`);
});

describe('the Markdown plugins of the site', () => {
  const site = (t, config) => {
    const root = mkdtempSync(join(tmpdir(), 'agent-md-plugins-'));
    t.after(() => rmSync(root, { recursive: true, force: true }));
    if (config !== undefined) writeFileSync(join(root, 'astro.config.mjs'), config);
    return root;
  };

  test('a site with no config has none, the real one has its two', async (t) => {
    assert.deepEqual(await markdownPlugins(site(t)), []);
    assert.deepEqual(
      (await markdownPlugins(SITE_DIR)).map((plugin) => plugin.module),
      ['src/lib/remark-bibliography.mjs', 'src/lib/wrappable-math.mjs'],
    );
  });

  test('a config whose markdown block is not where it is read, or that cannot be read, stops the check', async (t) => {
    const real = readFileSync(join(SITE_DIR, 'astro.config.mjs'), 'utf8');
    const reindented = real.replace(/\bmarkdown:\s*\{[\s\S]*?\n {2}\},/u, (block) => block.replaceAll('\n', '\n    '));
    assert.notEqual(reindented, real);
    await assert.rejects(markdownPlugins(site(t, reindented)), /no `markdown: \{ \.\.\. \},` block/u);
    const unreadable = site(t);
    mkdirSync(join(unreadable, 'astro.config.mjs'));
    await assert.rejects(markdownPlugins(unreadable), /EISDIR/u);
  });
});

test('the census reports a page that does not parse and goes on to the others', async (t) => {
  const root = mkdtempSync(join(tmpdir(), 'agent-md-census-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const good = join(root, 'good.mdx');
  const broken = join(root, 'broken.mdx');
  writeFileSync(good, '# Good\n\nText.\n');
  writeFileSync(broken, '# Broken\n\n<div>\n\nNever closed.\n');
  const lines = [];
  await census({ files: [broken, good], registry: new Map(), log: (line) => lines.push(line) });
  const out = lines.join('\n');
  assert.match(out, /^2 pages written: 1 with no issue, 1 with at least one\./mu);
  assert.match(out, /\[parse\] .*closing tag for `<div>`/u);
  assert.match(out, /Issues: 1 \(parse 1\)/u);
});

test('the writers are exactly the components the pages import', () => {
  const imported = new Set();
  for (const file of pageFiles(CONTENT_DIR)) {
    for (const name of componentImports(readFileSync(file, 'utf8'))) imported.add(name);
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
