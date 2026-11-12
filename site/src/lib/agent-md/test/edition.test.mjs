// The GitHub edition under docs/ (scripts/agent-md.mjs --docs,
// src/lib/agent-md/edition.mjs): which pages it holds, the line each file
// opens with, links between its pages, the anchors GitHub gives a heading,
// the README it is entered from, and the files a run writes and removes; then
// the committed edition itself, every relative link and fragment of which has
// to land on GitHub.
//
// Usage (from site/, after `pnpm install`): pnpm run test:agent-md
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, posix, relative, sep } from 'node:path';
import { describe, test } from 'node:test';

import { editionFilesUnder, writePages } from '../../../../scripts/agent-md.mjs';
import {
  EDITION_DOCUMENTS,
  EDITION_LEFT_OUT,
  EDITION_MARK,
  editionLinks,
  editionOpening,
  editionPages,
  githubAnchors,
  inEdition,
  isEditionFile,
  numbersInCode,
  publishedAt,
  readmeProblems,
  sitePage,
} from '../edition.mjs';
import { parse } from '../processor.mjs';
import { REPO_DIR } from '../render.mjs';
import { render } from './helpers.mjs';

const PINNED = JSON.parse(readFileSync(new URL('./edition-routes.json', import.meta.url), 'utf8')).routes;
const DOCS = join(REPO_DIR, 'docs');
const SITE = 'https://docs.jmrp.io/phonometry';

/** A directory made for one test and removed after it. */
function scratch(t, name) {
  const dir = mkdtempSync(join(tmpdir(), `agent-md-edition-${name}-`));
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

/** A page source with a frontmatter. */
const source = (title, body) => ['---', `title: ${title}`, `description: What ${title} is about.`, '---', '', body, ''].join('\n');

/** An edition page as editionPages gives it. */
const page = (route, path = `${route}.md`) => ({ route, path, file: `/x/${path}`, source: `site/src/content/docs/${path}x` });

describe('the pages the edition holds', () => {
  test('the six English pages left out are the ones the edition stands in for or cannot hold', () => {
    assert.deepEqual(Object.keys(EDITION_LEFT_OUT).sort(), [
      'reference',
      'reference/catalogues',
      'reference/conformance',
      'reference/errata',
      'reference/reports',
      'start/guides',
    ]);
    for (const reason of Object.values(EDITION_LEFT_OUT)) assert.ok(reason.length > 20);
  });

  test('a guide, an overview, a start or a reference page joins it; a landing, API, catalogue or errata page does not', () => {
    for (const route of ['signals/filters/filter-banks', 'signals', 'start/tasks', 'reference/bibliography', 'reference/theory']) {
      assert.ok(inEdition(route), route);
    }
    for (const route of ['', 'es', 'reference/api', 'reference/api/filters', 'reference/catalogues/solids', 'reference/errata/iec', 'es/signals/levels', 'start/guides']) {
      assert.ok(!inEdition(route), route || '(the landing page)');
    }
  });

  test('the documents of docs/ stand for the pages the edition leaves to them', () => {
    assert.deepEqual(
      { ...EDITION_DOCUMENTS },
      { 'start/guides': 'README.md', 'reference/conformance': 'CONFORMANCE.md', 'reference/errata': 'ERRATA.md' },
    );
  });

  test('a page written as its folder index keeps that name in docs/', (t) => {
    const content = writeTree(scratch(t, 'content'), {
      'index.mdx': source('Phonometry', 'Landing.'),
      'signals/index.mdx': source('Signals', 'The area.'),
      'signals/levels.mdx': source('Levels', 'A guide.'),
      'es/signals/levels.mdx': source('Niveles', 'Una guía.'),
      'reference/api/filters.md': source('filters', 'Module.'),
    });
    assert.deepEqual(
      editionPages(content).map(({ route, path, source: from }) => ({ route, path, from })),
      [
        { route: 'signals', path: 'signals/index.md', from: 'site/src/content/docs/signals/index.mdx' },
        { route: 'signals/levels', path: 'signals/levels.md', from: 'site/src/content/docs/signals/levels.mdx' },
      ],
    );
  });

  test('the site holds exactly the pinned routes, so no page leaves docs/ unnoticed', () => {
    const routes = editionPages().map((one) => one.route);
    const missing = PINNED.filter((route) => !routes.includes(route));
    const unpinned = routes.filter((route) => !PINNED.includes(route));
    assert.deepEqual(missing, [], `pages of edition-routes.json the edition no longer holds: ${missing.join(', ')}`);
    assert.deepEqual(unpinned, [], `pages of the edition edition-routes.json does not list (add them): ${unpinned.join(', ')}`);
    assert.deepEqual([...PINNED].sort(), PINNED, 'edition-routes.json is sorted');
  });
});

describe('the line a file of the edition opens with', () => {
  test('a comment naming its source, then the way back to the index and the published address', () => {
    const opening = editionOpening(page('signals/filters/filter-banks'));
    const [comment, blank, line] = opening.split('\n');
    assert.equal(
      comment,
      `${EDITION_MARK}site/src/content/docs/signals/filters/filter-banks.mdx: edit that page and its Spanish twin, then run \`make llms\`. -->`,
    );
    assert.equal(blank, '');
    assert.equal(line, `← [Documentation index](../../README.md) · Published at ${SITE}/signals/filters/filter-banks/`);
    assert.ok(isEditionFile(`${opening}\n\n# Filter banks\n`));
  });

  test('the way back climbs as many folders as the file sits in', () => {
    assert.match(editionOpening(page('start/about')), /\]\(\.\.\/README\.md\)/u);
    assert.match(editionOpening(page('signals', 'signals/index.md')), /\]\(\.\.\/README\.md\)/u);
    assert.match(editionOpening(page('start/environments/conda')), /\]\(\.\.\/\.\.\/README\.md\)/u);
  });

  test('a file without the comment is not one of the edition, whatever else it says', () => {
    assert.ok(!isEditionFile('# Contributing\n'));
    assert.ok(!isEditionFile(`\n${EDITION_MARK}site/src/content/docs/x.md -->\n`));
  });

  test('the published address is the page on the site', () => {
    assert.equal(publishedAt('signals'), `${SITE}/signals/`);
    assert.deepEqual(sitePage(publishedAt('signals/levels')), { route: 'signals/levels', fragment: '' });
  });
});

describe('an address of the site', () => {
  test('a page, with its fragment, and the landing page', () => {
    assert.deepEqual(sitePage(`${SITE}/signals/levels/`), { route: 'signals/levels', fragment: '' });
    assert.deepEqual(sitePage(`${SITE}/signals/levels/#a-b`), { route: 'signals/levels', fragment: '#a-b' });
    assert.deepEqual(sitePage(`${SITE}/signals/levels#a`), { route: 'signals/levels', fragment: '#a' });
    assert.deepEqual(sitePage(`${SITE}/`), { route: '', fragment: '' });
  });

  test('a file under the site, another host or another path is no page', () => {
    for (const url of [`${SITE}/media/a.svg`, `${SITE}/signals/index.md`, `${SITE}/llms.txt`, `${SITE}x/`, 'https://example.org/phonometry/signals/', `${SITE}/a/?q=1`]) {
      assert.equal(sitePage(url), undefined, url);
    }
  });
});

describe('the anchors GitHub gives a file', () => {
  test('a heading is slugged as github.com does it, a repeat numbered', () => {
    const anchors = githubAnchors('# Title\n\n## Notes\n\n## Notes\n\n## Report metadata (`ReportMetadata`)\n');
    assert.deepEqual([...anchors], ['title', 'notes', 'notes-1', 'report-metadata-reportmetadata']);
  });

  test('a colon in a heading is text on GitHub, not one of the site directives', () => {
    assert.ok(githubAnchors('## Equal-loudness contours (ISO 226:2023)\n').has('equal-loudness-contours-iso-2262023'));
  });

  test('maths, a link and inline HTML in a heading, and an anchor a page pins itself', () => {
    const anchors = githubAnchors('## The $L_p$ level\n\n## [Absorbers](a.md)\n\n## The ERB<sub>N</sub> scale\n\n<a id="pinned"></a>\n\n```md\n<a id="fenced"></a>\n```\n');
    for (const anchor of ['the-l_p-level', 'absorbers', 'the-erbn-scale', 'pinned']) assert.ok(anchors.has(anchor), anchor);
    assert.ok(!anchors.has('fenced'));
  });
});

describe('links between pages of the edition', () => {
  const pages = new Map(
    [page('signals/levels'), page('signals/filters/filter-banks'), page('signals', 'signals/index.md'), page('start/about')].map((one) => [one.route, one]),
  );
  const anchors = { 'signals/levels.md': new Set(['weighting']), 'README.md': new Set(['guides']), 'signals/index.md': new Set() };
  const anchorsOf = (path) => anchors[path] ?? new Set();
  const from = pages.get('signals/filters/filter-banks');

  test('a page of the edition, the folder index and a document of docs/ are linked as files', () => {
    const text = [
      `See [levels](${SITE}/signals/levels/), [the area](${SITE}/signals/) and [all guides](${SITE}/start/guides/).`,
      `[About][about] and [the report](${SITE}/reference/conformance/).`,
      '',
      `[about]: ${SITE}/start/about/`,
      '',
    ].join('\n');
    const { markdown, kept } = editionLinks(text, from, { pages, anchorsOf });
    assert.equal(
      markdown,
      [
        'See [levels](../levels.md), [the area](../index.md) and [all guides](../../README.md).',
        '[About][about] and [the report](../../CONFORMANCE.md).',
        '',
        '[about]: ../../start/about.md',
        '',
      ].join('\n'),
    );
    assert.deepEqual(kept, []);
  });

  test('a fragment GitHub finds on the target travels with it; one it does not keeps the site address', () => {
    const text = `[A](${SITE}/signals/levels/#weighting), [B](${SITE}/signals/levels/#gone) and [C](${SITE}/start/guides/#guides).\n`;
    const { markdown, kept } = editionLinks(text, from, { pages, anchorsOf });
    assert.equal(markdown, `[A](../levels.md#weighting), [B](${SITE}/signals/levels/#gone) and [C](../../README.md#guides).\n`);
    assert.deepEqual(kept, [`${SITE}/signals/levels/#gone`]);
  });

  test('a link to the page itself is its fragment', () => {
    const { markdown } = editionLinks(`[up](${SITE}/signals/levels/#weighting)\n`, pages.get('signals/levels'), { pages, anchorsOf });
    assert.equal(markdown, '[up](#weighting)\n');
  });

  test('a page the edition does not hold, a figure, code and maths keep what they say', () => {
    const text = [
      `[API](${SITE}/reference/api/filters/), [catalogue](${SITE}/reference/catalogues/solids/), ![fig](${SITE}/signals/levels/)`,
      '',
      `\`[x](${SITE}/signals/levels/)\` and $a$`,
      '',
      '```md',
      `[y](${SITE}/signals/levels/)`,
      '```',
      '',
    ].join('\n');
    assert.equal(editionLinks(text, from, { pages, anchorsOf }).markdown, text);
  });
});

describe('a report number with a run of hyphens', () => {
  test('is written in code in a reference entry', () => {
    const entry = '- **Breeding, J. E. (1996).** *RANDI 3.1 physics description* (NRL/FR/7176--95-9628). Naval Research Laboratory.\n';
    assert.equal(
      numbersInCode(entry),
      '- **Breeding, J. E. (1996).** *RANDI 3.1 physics description* (`NRL/FR/7176--95-9628`). Naval Research Laboratory.\n',
    );
  });

  test('a number already in code, code, maths and an address keep what they say', () => {
    const text = [
      '(`NRL/FR/7176--95-9628`) and `(A--B)`',
      '',
      '$(a--b)$ and [r](https://example.org/(x--y))',
      '',
      '```sh',
      'echo (a--b)',
      '```',
      '',
      '<!-- (c--d) -->',
      '',
    ].join('\n');
    assert.equal(numbersInCode(text), text);
  });

  test('a spaced double hyphen in prose is no number and is left for the dash check', () => {
    const text = 'one (two -- three) and --keep\n';
    assert.equal(numbersInCode(text), text);
  });
});

describe('the README the edition is entered from', () => {
  const pages = [page('signals/levels'), page('signals', 'signals/index.md')];
  const exists = (path) => ['ERRATA.md', 'contributing/index.md', '../CONTRIBUTING.md'].includes(path);

  test('a README that links every page, and files that are there, is right', () => {
    const readme = '[Signals](signals/index.md), [Levels](signals/levels.md#a), [Errata](ERRATA.md), [Guide](contributing/index.md), [How](../CONTRIBUTING.md), [web](https://example.org/x.md)\n';
    assert.deepEqual(readmeProblems(readme, pages, exists), []);
  });

  test('a page it does not link and a file it links that is not there are both named', () => {
    const problems = readmeProblems('[Signals](signals/index.md) and [Old](signals/gone.md)\n', pages, exists);
    assert.equal(problems.length, 2);
    assert.match(problems[0], /links no line to 1 page\(s\) of the edition: signals\/levels\.md/u);
    assert.match(problems[1], /signals\/gone\.md/u);
  });
});

describe('the GitHub flavour of the renderer', () => {
  test('a collapsible stays one, with its body as Markdown', () => {
    const { markdown } = render('<details>\n<summary>Show the code</summary>\n\n```python\nx = 1\n```\n\n</details>\n', { flavour: 'github' });
    assert.equal(markdown, '<details>\n<summary>Show the code</summary>\n\n```python\nx = 1\n```\n\n</details>\n');
    assert.equal(render('<details>\n<summary>Show the code</summary>\n\nBody.\n\n</details>\n').markdown, '**Show the code**\n\nBody.\n');
  });

  test('an aside is the alert GitHub draws, every line of it quoted', () => {
    const { markdown } = render(':::caution[Mind the gap]\nOne line.\n\n```python\nx = 1\n```\n:::\n', { flavour: 'github' });
    assert.equal(markdown, '> [!WARNING]\n> **Mind the gap**\n>\n> One line.\n>\n> ```python\n> x = 1\n> ```\n');
    const tree = parse(markdown, { mdx: false });
    assert.equal(tree.children[0].type, 'blockquote');
  });

  test('a subscript, a superscript and a pinned anchor keep their HTML', () => {
    const { markdown } = render('<span id="old"></span>\n\nERB<sub>N</sub> and 10<sup>4</sup>.\n', { flavour: 'github' });
    assert.equal(markdown, '<a id="old"></a>\n\nERB<sub>N</sub> and 10<sup>4</sup>.\n');
    assert.equal(render('<span id="old"></span>\n\nERB<sub>N</sub> and 10<sup>4</sup>.\n').markdown, 'ERB_N and 10^4.\n');
  });
});

describe('a run of --docs', () => {
  const TREE = Object.freeze({
    'index.mdx': source('Phonometry', 'Landing.'),
    'signals/index.mdx': source('Signals', 'The area. Start at [Levels](/phonometry/signals/levels/#weighting).'),
    'signals/levels.mdx': source('Levels', 'Sound levels.\n\n## Weighting\n\nA and C.'),
    'es/signals/levels.mdx': source('Niveles', 'Niveles.'),
  });
  const README = '# Docs\n\n- [Signals](signals/index.md)\n- [Levels](signals/levels.md)\n';

  async function run(t, docsDir, contentDir) {
    const said = [];
    t.mock.method(console, 'log', (...words) => said.push(words.join(' ')));
    t.mock.method(console, 'error', (...words) => said.push(words.join(' ')));
    const status = await writePages({ docsDir, contentDir });
    t.mock.restoreAll();
    return { status, said: said.join('\n') };
  }

  test('writes every page, removes the files it no longer writes and leaves the rest', async (t) => {
    const content = writeTree(scratch(t, 'content'), TREE);
    const docs = writeTree(scratch(t, 'docs'), {
      'README.md': README,
      'ERRATA.md': '# Errata\n',
      'contributing/index.md': '# Contributing\n',
      'signals/levels.md': '# An old hand-written copy\n',
      'signals/moved.md': `${EDITION_MARK}site/src/content/docs/signals/moved.mdx: x -->\n\n# Moved\n`,
    });
    const { status, said } = await run(t, docs, content);
    assert.equal(status, 0, said);
    assert.deepEqual(filesUnder(docs), ['ERRATA.md', 'README.md', 'contributing/index.md', 'signals/index.md', 'signals/levels.md']);
    const index = readFileSync(join(docs, 'signals/index.md'), 'utf8');
    assert.ok(index.startsWith(`${EDITION_MARK}site/src/content/docs/signals/index.mdx`), index);
    assert.match(index, /\n← \[Documentation index\]\(\.\.\/README\.md\) · Published at https:\/\/docs\.jmrp\.io\/phonometry\/signals\/\n\n# Signals\n/u);
    assert.match(index, /\[Levels\]\(levels\.md#weighting\)/u);
    assert.ok(isEditionFile(readFileSync(join(docs, 'signals/levels.md'), 'utf8')));
    assert.deepEqual(editionFilesUnder(docs), ['signals/index.md', 'signals/levels.md']);
    assert.match(said, /2 pages, 1 no longer in it removed/u);
  });

  test('a checkout with carriage returns writes the same files, line feeds only, and still knows the files it wrote', async (t) => {
    // A clone made with `core.autocrlf=true` writes the page sources, the
    // README and the committed files of the edition with a carriage return
    // before each line feed; the run reads each as the commit holds it.
    const crlf = (files) => Object.fromEntries(Object.entries(files).map(([name, text]) => [name, text.replaceAll('\n', '\r\n')]));
    const stale = { 'signals/moved.md': `${EDITION_MARK}site/src/content/docs/signals/moved.mdx: x -->\n\n# Moved\n` };
    // The renderer copies code and tables out of the source by position, so a
    // carriage return read with the source would reach the file it writes.
    const tree = {
      ...TREE,
      'signals/levels.mdx': source('Levels', 'Sound levels.\n\n## Weighting\n\n| Curve | At 1 kHz |\n| --- | --- |\n| A | 0 dB |\n\n```python\nimport phonometry\nprint(1)\n```'),
    };
    const written = {};
    for (const [ends, convert] of [['lf', (files) => files], ['crlf', crlf]]) {
      const content = writeTree(scratch(t, `content-${ends}`), convert(tree));
      const docs = writeTree(scratch(t, `docs-${ends}`), convert({ 'README.md': README, ...stale }));
      const { status, said } = await run(t, docs, content);
      assert.equal(status, 0, said);
      assert.deepEqual(filesUnder(docs), ['README.md', 'signals/index.md', 'signals/levels.md'], `${ends}: the stale file of the edition is removed`);
      written[ends] = ['signals/index.md', 'signals/levels.md'].map((name) => readFileSync(join(docs, name), 'utf8'));
    }
    for (const text of written.crlf) assert.ok(!text.includes('\r'), text);
    assert.deepEqual(written.crlf, written.lf);
  });

  test('a README that links a stale file of the edition fails the run before that file is removed', async (t) => {
    const content = writeTree(scratch(t, 'content'), TREE);
    const stale = `${EDITION_MARK}site/src/content/docs/signals/gone.mdx: x -->\n\n# Gone\n`;
    const docs = writeTree(scratch(t, 'docs'), { 'README.md': `${README}- [Gone](signals/gone.md)\n`, 'signals/gone.md': stale });
    const { status, said } = await run(t, docs, content);
    assert.equal(status, 1, said);
    assert.match(said, /docs\/README\.md links 1 Markdown file\(s\) that are neither a page of the edition nor a file of docs\/: signals\/gone\.md/u);
    assert.deepEqual(filesUnder(docs), ['README.md', 'signals/gone.md'], 'nothing removed, nothing written');
    assert.equal(readFileSync(join(docs, 'signals/gone.md'), 'utf8'), stale);
  });

  test('a README that misses a page fails the run before a file is written', async (t) => {
    const content = writeTree(scratch(t, 'content'), TREE);
    const docs = writeTree(scratch(t, 'docs'), { 'README.md': '# Docs\n\n- [Signals](signals/index.md)\n' });
    const { status, said } = await run(t, docs, content);
    assert.equal(status, 1);
    assert.match(said, /docs\/README\.md links no line to 1 page\(s\) of the edition: signals\/levels\.md/u);
    assert.deepEqual(filesUnder(docs), ['README.md']);
  });
});

describe('the committed edition', () => {
  const files = editionFilesUnder(DOCS);

  test('holds exactly the files of the pinned routes', () => {
    const paths = new Set(editionPages().map((one) => one.path));
    assert.deepEqual(files, [...paths].sort());
    assert.equal(files.length, PINNED.length);
  });

  test('every relative link lands on a file, and every fragment on an anchor GitHub gives it', () => {
    /** @type {Map<string, Set<string>>} */
    const anchors = new Map();
    const anchorsOf = (path) => {
      if (!anchors.has(path)) anchors.set(path, githubAnchors(readFileSync(join(DOCS, path), 'utf8')));
      return anchors.get(path);
    };
    const broken = [];
    let checked = 0;
    for (const path of files) {
      const visit = (node) => {
        if ((node.type === 'link' || node.type === 'definition') && node.url && !/^[a-z][a-z0-9+.-]*:/iu.test(node.url)) {
          const [file, fragment] = node.url.split('#');
          const target = file ? posix.normalize(posix.join(posix.dirname(path), decodeURI(file))) : path;
          const where = `${path}:${node.position?.start.line}`;
          checked += 1;
          if (!existsSync(join(DOCS, target))) broken.push(`${where} ${node.url} (no such file)`);
          else if (fragment && target.endsWith('.md') && !anchorsOf(target).has(decodeURIComponent(fragment))) {
            broken.push(`${where} ${node.url} (no such anchor)`);
          }
        }
        for (const child of node.children ?? []) visit(child);
      };
      visit(parse(readFileSync(join(DOCS, path), 'utf8'), { mdx: false }));
    }
    assert.deepEqual(broken, []);
    assert.ok(checked > 3000, `only ${checked} relative links read`);
  });
});
