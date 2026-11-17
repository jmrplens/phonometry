// What `scripts/agent-md.mjs --dump` hands the llms generator, on a content
// tree small enough to read, and the directories and options it refuses.
//
// scripts/generate_llms.py reads nothing of a page but the dump: routes.json,
// with every English route's kind and the path of its copy, and the copies.
// Its tests write dumps of the same shape in Python, so nothing there sees a
// dump this command wrote; these do. The kind of each route is held to one
// table (page-kinds.json), which the Python port of `pageKind` that writes
// those test dumps is held to as well (tests/test_generate_llms.py).
//
// Usage (from site/, after `pnpm install`): pnpm run test:agent-md
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, sep } from 'node:path';
import { describe, test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { ROUTES_FILE, dumpRefusal, writePages } from '../../../../scripts/agent-md.mjs';
import { FULL_TEXT_KINDS, pageKind } from '../../page-markdown.mjs';

const COMMAND = fileURLToPath(new URL('../../../../scripts/agent-md.mjs', import.meta.url));
const TABLE = JSON.parse(readFileSync(new URL('./page-kinds.json', import.meta.url), 'utf8'));
const KINDS = TABLE.routes;
const DATES = Object.freeze({ dateOf: () => new Date('2026-10-20T10:00:00Z'), publishedOf: () => '2026-01-06' });

/** A page source with a frontmatter. */
const source = (title, body, extra = []) =>
  ['---', `title: ${title}`, `description: What ${title} is about.`, ...extra, '---', '', body, ''].join('\n');

/** A content tree with one page of every kind, in both languages where it matters. */
const TREE = Object.freeze({
  'index.mdx': source('Phonometry', 'The landing page.'),
  'es/index.mdx': source('Phonometry', 'La portada.'),
  '404.md': source('Not found', 'Nothing here.'),
  'reference/api/index.md': source('API reference', 'Every module.'),
  'reference/api/filters.md': source('filters', 'The filters module.'),
  'reference/catalogues/index.md': source('Catalogues', 'Every catalogue.'),
  'reference/catalogues/solids.md': source('Solids', '| Material | Density |\n| --- | --- |\n| Steel | 7850 |'),
  'reference/errata/iec.md': source('IEC errata', 'One correction.'),
  'signals/levels.mdx': source('Levels', 'Sound levels.\n\n## Weighting\n\nA and C.', [
    'references:',
    '  - type: standard',
    '    title: Sound level meters',
    '    designation: IEC 61672-1:2013',
    '    organization: IEC',
    '    year: 2013',
  ]),
  'es/signals/levels.mdx': source('Niveles', 'Niveles sonoros.'),
});

/** The routes.json the tree above dumps to, route by route. */
const ROUTES = Object.freeze([
  { route: '', kind: 'home', copy: null },
  { route: 'reference/api', kind: 'api', copy: null },
  { route: 'reference/api/filters', kind: 'api', copy: null },
  { route: 'reference/catalogues', kind: 'guide', copy: 'reference/catalogues/index.md' },
  { route: 'reference/catalogues/solids', kind: 'catalogue', copy: 'reference/catalogues/solids/index.md' },
  { route: 'reference/errata/iec', kind: 'errata-family', copy: 'reference/errata/iec/index.md' },
  { route: 'signals/levels', kind: 'guide', copy: 'signals/levels/index.md' },
]);

/** A directory made for one test and removed after it. */
function scratch(t, name) {
  const dir = mkdtempSync(join(tmpdir(), `agent-md-${name}-`));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  return dir;
}

/** Writes files under a directory. */
function writeTree(root, files) {
  for (const [name, text] of Object.entries(files)) {
    mkdirSync(dirname(join(root, name)), { recursive: true });
    writeFileSync(join(root, name), text);
  }
  return root;
}

/** Every file under a directory, by its path from there. */
function filesUnder(root) {
  const found = [];
  const walk = (dir) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      if (entry.isDirectory()) walk(join(dir, entry.name));
      else found.push(relative(root, join(dir, entry.name)).split(sep).join('/'));
    }
  };
  walk(root);
  return found.sort();
}

/** Runs the writer with its messages caught, and returns its status and them. */
async function run(t, options) {
  const said = [];
  t.mock.method(console, 'log', (...words) => said.push(words.join(' ')));
  t.mock.method(console, 'error', (...words) => said.push(words.join(' ')));
  const status = await writePages(options);
  t.mock.restoreAll();
  return { status, said: said.join('\n') };
}

describe('the kind of a route', () => {
  test('pageKind gives every route of the shared table its kind', () => {
    for (const [route, kind] of Object.entries(KINDS)) assert.equal(pageKind(route), kind, route || '(the landing page)');
  });

  test('slashes around a route and an index segment change nothing', () => {
    for (const [route, kind] of Object.entries(KINDS)) {
      assert.equal(pageKind(`/${route}/`), kind, route);
      assert.equal(pageKind(route ? `${route}/index` : 'index'), kind, route);
    }
  });

  test('the table holds every kind, and the kinds the llms files carry are the ones it names', () => {
    const kinds = new Set(Object.values(KINDS));
    assert.deepEqual([...kinds].sort(), ['api', 'catalogue', 'errata-family', 'guide', 'home']);
    assert.deepEqual([...FULL_TEXT_KINDS], TABLE.fullTextKinds);
  });
});

describe('a dump of a content tree', () => {
  test('lists every English route with its kind, and writes the copy of every page the llms files carry', async (t) => {
    const content = writeTree(scratch(t, 'content'), TREE);
    const dump = join(scratch(t, 'dump'), 'agent-md');
    const { status, said } = await run(t, { dumpDir: dump, contentDir: content, dates: DATES });
    assert.equal(status, 0, said);
    const { pages } = JSON.parse(readFileSync(join(dump, ROUTES_FILE), 'utf8'));
    assert.deepEqual(
      pages.map(({ route, kind, copy }) => ({ route, kind, copy })),
      ROUTES,
      'no Spanish route, no error page, the landing page and the API reference with no copy',
    );
    for (const page of pages) assert.equal(page.kind, pageKind(page.route), page.route);
    const levels = pages.find((page) => page.route === 'signals/levels');
    assert.equal(levels.title, 'Levels');
    assert.equal(levels.description, 'What Levels is about.');
    assert.deepEqual(levels.standards, ['IEC 61672-1:2013']);
    assert.deepEqual(filesUnder(dump), [ROUTES_FILE, ...ROUTES.filter((page) => page.copy).map((page) => page.copy)].sort());
    const copy = readFileSync(join(dump, 'signals/levels/index.md'), 'utf8');
    assert.match(copy, /^# Levels\n/u);
    assert.match(copy, /^Published: 2026-01-06$/mu);
    assert.match(copy, /^Updated: 2026-10-20T10:00:00Z$/mu);
    assert.match(copy, /^Standards: IEC 61672-1:2013$/mu);
    assert.match(copy, /^## Weighting$/mu);
  });

  test('--undated leaves out the Published and Updated lines of each copy, and nothing else', async (t) => {
    const content = writeTree(scratch(t, 'content'), TREE);
    const dump = scratch(t, 'dump');
    assert.equal((await run(t, { dumpDir: dump, contentDir: content, dates: DATES })).status, 0);
    const dated = Object.fromEntries(filesUnder(dump).map((path) => [path, readFileSync(join(dump, path), 'utf8')]));
    // The same directory again: an earlier dump is emptied and written anew.
    const { status, said } = await run(t, { dumpDir: dump, contentDir: content, dates: DATES, undated: true });
    assert.equal(status, 0, said);
    assert.match(said, /without their dates/u);
    assert.deepEqual(filesUnder(dump), Object.keys(dated).sort());
    assert.equal(readFileSync(join(dump, ROUTES_FILE), 'utf8'), dated[ROUTES_FILE], 'routes.json states no date');
    const copies = Object.keys(dated).filter((path) => path !== ROUTES_FILE);
    assert.equal(copies.length, 4);
    for (const path of copies) {
      const lines = dated[path].split('\n');
      const left = lines.filter((line) => !/^(?:Published: \d{4}-\d{2}-\d{2}|Updated: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)$/u.test(line));
      assert.equal(lines.length - left.length, 2, `${path} states both dates when dated`);
      assert.equal(readFileSync(join(dump, path), 'utf8'), left.join('\n'), path);
    }
  });

  test('with --public in the same run, the dump carries the published copies byte for byte', async (t) => {
    const content = writeTree(scratch(t, 'content'), TREE);
    const out = scratch(t, 'public');
    const dump = scratch(t, 'dump');
    const { status, said } = await run(t, { publicOut: out, dumpDir: dump, contentDir: content, dates: DATES });
    assert.equal(status, 0, said);
    assert.ok(existsSync(join(out, 'es/signals/levels/index.md')), 'the Spanish copy is published');
    assert.ok(existsSync(join(out, 'reference/api/filters/index.md')), 'the API copy is published');
    assert.ok(!existsSync(join(out, '404/index.md')), 'the error page has no copy');
    for (const { copy } of ROUTES.filter((page) => page.copy)) {
      assert.equal(readFileSync(join(dump, copy), 'utf8'), readFileSync(join(out, copy), 'utf8'), copy);
    }
  });
});

describe('a directory a dump is refused', () => {
  test('a new directory, an empty one and an earlier dump take a dump', (t) => {
    const root = scratch(t, 'dirs');
    assert.equal(dumpRefusal(join(root, 'new')), undefined);
    assert.equal(dumpRefusal(root), undefined);
    writeTree(root, {
      [ROUTES_FILE]: JSON.stringify({ pages: [{ route: 'signals/levels', copy: 'signals/levels/index.md' }, { route: '', copy: null }] }),
      'signals/levels/index.md': '# Levels\n',
    });
    assert.equal(dumpRefusal(root), undefined);
  });

  for (const [name, files, why] of [
    ['files and no routes.json', { 'precious.txt': 'kept' }, /holds files and no routes\.json/u],
    ['a file beside an earlier dump', { [ROUTES_FILE]: '{"pages": []}', 'notes.txt': 'kept' }, /holds notes\.txt, which no route/u],
    [
      'a folder no route of its routes.json writes',
      { [ROUTES_FILE]: '{"pages": [{"route": "signals/levels", "copy": "signals/levels/index.md"}]}', 'keep/notes.txt': 'kept' },
      /holds keep\/notes\.txt, which no route/u,
    ],
    [
      'a file inside a route folder that no route of its routes.json writes',
      {
        [ROUTES_FILE]: '{"pages": [{"route": "signals/a", "copy": "signals/a/index.md"}]}',
        'signals/a/index.md': '# A\n',
        'signals/notes.txt': 'kept',
      },
      /holds signals\/notes\.txt, which no route/u,
    ],
    ['a routes.json it cannot read', { [ROUTES_FILE]: 'not JSON', 'signals/levels/index.md': 'kept' }, /cannot read/u],
  ]) {
    test(`a directory with ${name} is refused before a page is rendered, and left as it was`, async (t) => {
      const dump = writeTree(scratch(t, 'refused'), files);
      const before = filesUnder(dump);
      assert.match(dumpRefusal(dump) ?? '', why);
      // A page the renderer cannot write: had it been rendered, the run would
      // have failed on it with status 1 rather than refused the directory.
      const content = writeTree(scratch(t, 'content'), { 'signals/levels.mdx': source('Levels', '<NoWriter />') });
      const { status, said } = await run(t, { dumpDir: dump, contentDir: content, dates: DATES });
      assert.equal(status, 2, said);
      assert.match(said, why);
      assert.match(said, /left alone/u);
      assert.deepEqual(filesUnder(dump), before);
    });
  }

  test('a file is refused', (t) => {
    const root = writeTree(scratch(t, 'file'), { 'routes.json': '{"pages": []}' });
    assert.match(dumpRefusal(join(root, ROUTES_FILE)) ?? '', /is a file, not a directory/u);
  });
});

describe('the options the command refuses', () => {
  const command = (...args) => spawnSync(process.execPath, [COMMAND, ...args], { encoding: 'utf8' });

  test('--dump with no directory, or with an option where the directory goes', () => {
    for (const args of [['--dump'], ['--dump', '--undated']]) {
      const result = command(...args);
      assert.equal(result.status, 2, args.join(' '));
      assert.match(result.stderr, /--dump needs a directory/u);
    }
  });

  test('--undated with --public', () => {
    const result = command('--public', '--undated');
    assert.equal(result.status, 2);
    assert.match(result.stderr, /--undated is for a dump alone/u);
  });

  test('a directory that is not a dump, before anything is rendered or removed', (t) => {
    const dump = writeTree(scratch(t, 'not-a-dump'), { 'precious.txt': 'kept' });
    const result = command('--dump', dump, '--undated');
    assert.equal(result.status, 2, result.stderr);
    assert.match(result.stderr, /holds files and no routes\.json/u);
    assert.equal(readFileSync(join(dump, 'precious.txt'), 'utf8'), 'kept');
  });
});
