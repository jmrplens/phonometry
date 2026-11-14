// Which pages publish a Markdown copy.
//
// A copy written from a page's own source takes every component out, so the
// 46 catalogue pages, the two indexes of fiches and the Spanish glossary and
// conformance report published a copy that held their introduction and none
// of the tables, rows or entries they are there to show, and the head of each
// page and the edge's negotiation sent agents to it. src/lib/page-markdown.mjs
// withholds the copy of a page that renders one of its data components and has
// no copy in docs/ to stand for it, and every reader of the rule (the
// generator, the head link, the page actions) asks hasMarkdownCopy.
//
// The census below reads the components a page imports, which is not how the
// module finds them (it reads the tags the page renders), and holds every
// component the content imports to one reading, so a new one cannot slip
// through as neither data nor prose.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, sep } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { parse as parseYaml } from 'yaml';

import { DATA_COMPONENTS, hasMarkdownCopy, mirrorOf, routeOf, withheldRoutes } from '../src/lib/page-markdown.mjs';
import { citationParts, noteParts, opening, sortedReferences } from '../src/lib/references-format.mjs';
import { TAG, decodeReferences, oneLine, printed } from './shared/markdown-reader.mjs';
import { pageMarkup } from './shared/markdown-spans.mjs';
import {
  COMPONENT_READINGS,
  COPY_FORMS,
  figureMarkdown,
  frontmatterSource,
  referencesMarkdown,
  stripFrontmatter,
} from './shared/page-twin.mjs';

const SITE = join(dirname(fileURLToPath(import.meta.url)), '..');
const CONTENT = join(SITE, 'src', 'content', 'docs');
const DOCS = join(SITE, '..', 'docs');

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

const page = (body) => `---\ntitle: A page\n---\n\n${body}\n`;

test('a page that renders a data component and has no copy in docs/ publishes none', (t) => {
  const withheld = withheldRoutes(
    tree(t, {
      'content/reference/catalogues/solids.mdx': page("import Catalogues from '../../../../components/Catalogues.astro';\n\n<Catalogues lang=\"en\" />"),
      'content/es/reference/glossary.mdx': page('<Glossary lang="es" />'),
      'content/reference/glossary.mdx': page('<Glossary lang="en" />'),
      'docs/reference/glossary.md': '# Glossary\n',
      'content/reference/conformance.mdx': page('<Conformance />'),
      'content/guides/levels.mdx': page('Prose only.'),
    }),
  );
  assert.deepEqual([...withheld].sort(), ['es/reference/glossary', 'reference/catalogues/solids']);
});

test('a data component a page only shows how to write does not withhold its copy', (t) => {
  const withheld = withheldRoutes(
    tree(t, {
      'content/guides/span.mdx': page('Write `<Catalogues lang="en" />` to list them.'),
      'content/guides/fence.mdx': page('```mdx\n<ReportIndex />\n```'),
      'content/guides/comment.mdx': page('{/* <Glossary /> */}'),
      'content/guides/page.md': page('A Markdown page shows <Glossary /> as text.'),
    }),
  );
  assert.deepEqual([...withheld], []);
});

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

/** The components a page imports from src/components, by the name it imports them under. */
function importedComponents(path) {
  const text = readFileSync(join(CONTENT, path), 'utf8');
  return [...text.matchAll(/^import\s+(\w+)\s+from\s+['"][^'"]*\/components\/(?:[\w-]+\/)*\w+\.astro['"]/gm)].map(
    (found) => found[1],
  );
}

test("the site's withheld copies are the pages that import a data component and have no mirror", () => {
  const expected = contentPages()
    .filter((path) => importedComponents(path).some((name) => DATA_COMPONENTS.includes(name)))
    .map(routeOf)
    .filter((route) => mirrorOf(route, DOCS) === undefined)
    .sort();
  const withheld = [...withheldRoutes({ contentDir: CONTENT, docsDir: DOCS })].sort();
  assert.deepEqual(withheld, expected);
  for (const route of ['', 'es', 'reference/catalogues/solids', 'es/reference/glossary', 'es/reference/conformance']) {
    assert.ok(withheld.includes(route), route);
  }
  for (const route of ['reference/glossary', 'reference/conformance', 'es/reference/errata']) {
    assert.ok(!withheld.includes(route), `${route} has its copy in docs/`);
  }
  for (const route of contentPages().map(routeOf)) assert.equal(hasMarkdownCopy(route), !expected.includes(route), route);
});

test('every component a page imports is read one way by the copy, and every reading names a component a page imports', () => {
  const imported = new Set(contentPages().flatMap(importedComponents));
  const read = new Set([...DATA_COMPONENTS, ...Object.keys(COMPONENT_READINGS)]);
  const unread = [...imported].filter((name) => !read.has(name)).sort();
  assert.deepEqual(unread, [], 'components the copy has no reading for: write one in COMPONENT_READINGS or DATA_COMPONENTS');
  const stale = [...read].filter((name) => !imported.has(name)).sort();
  assert.deepEqual(stale, [], 'readings of components no page imports');
  for (const name of DATA_COMPONENTS) assert.equal(COMPONENT_READINGS[name], undefined, `${name} is read twice`);
});

test('every component the copy writes out is one the copy check counts', () => {
  const written = Object.keys(COMPONENT_READINGS).filter((name) => COMPONENT_READINGS[name] === 'written').sort();
  assert.deepEqual(Object.keys(COPY_FORMS).sort(), written, 'a component the copy writes out needs its form in COPY_FORMS');
});

/** An attribute of a component tag written as a string, as MDX reads it: its character references read. */
function attributeValue(tag, name) {
  const found = tag.match(new RegExp(String.raw`\b${name}="([^"]*)"`));
  return found ? decodeReferences(found[1]) : undefined;
}

test('the text a page prints as it is reads the same in the copy written from its source, on every such page', async () => {
  // Read back by the site's own Markdown pipeline (shared/markdown-reader.mjs):
  // a figure's alt, a clip's and a fiche's title, description and caption, and
  // every work of the References section, on every page whose copy is written
  // from its source. The Spanish seat-vibration guide printed `a*wS = SEAT por
  // a*wP` in an alt, and the copy printed `awS = SEAT por awP`.
  const misread = [];
  let read = 0;
  for (const path of contentPages()) {
    const route = routeOf(path);
    if (!hasMarkdownCopy(route) || mirrorOf(route, DOCS) !== undefined) continue;
    const lang = route === 'es' || route.startsWith('es/') ? 'es' : 'en';
    const page = readFileSync(join(CONTENT, path), 'utf8');
    const kind = path.endsWith('.mdx') ? 'mdx' : 'md';
    const source = stripFrontmatter(page);
    if (kind === 'mdx') {
      for (const found of pageMarkup(source, { kind }).matchAll(/<(ThemeImage|Video|ReportPreview)\b[^>]*\/>/g)) {
        const tag = source.slice(found.index, found.index + found[0].length);
        const shown = await printed(figureMarkdown(tag, { lang, base: 'https://docs.jmrp.io/phonometry' }));
        read += 1;
        if (found[1] === 'ThemeImage') {
          const alt = oneLine(attributeValue(tag, 'alt'));
          if (shown.alts[0] !== alt) misread.push(`${path}: the alt ${JSON.stringify(alt)} prints as ${JSON.stringify(shown.alts[0])}`);
          continue;
        }
        const lead = { Video: { en: 'Video', es: 'Vídeo' }, ReportPreview: { en: 'Report', es: 'Informe' } }[found[1]][lang];
        const caption = attributeValue(tag, 'caption');
        const words = [`${lead}: ${attributeValue(tag, 'title')}: ${attributeValue(tag, 'description')}`, caption ?? ''];
        const expected = oneLine(words.join(' '));
        if (shown.text !== expected) misread.push(`${path}: ${JSON.stringify(expected)} prints as ${JSON.stringify(shown.text)}`);
      }
    }
    const frontmatter = parseYaml(frontmatterSource(page)) ?? {};
    if (!frontmatter.references?.length) continue;
    const shown = await printed(referencesMarkdown(frontmatter.references, lang, 'References'));
    const items = [...shown.html.matchAll(/<li>([^]*?)<\/li>/g)].map((item) => oneLine(decodeReferences(item[1].replace(TAG, ''))));
    for (const [index, [, work]] of sortedReferences(frontmatter.references, lang).entries()) {
      const note = work.note ? ` ${noteParts(work.note).map((part) => part.text).join('')}` : '';
      const expected = oneLine(`${opening(work, lang)}${citationParts(work).map((part) => part.text).join('')}${note}`);
      read += 1;
      if (items[index] !== expected) misread.push(`${path}: the work ${JSON.stringify(expected)} prints as ${JSON.stringify(items[index])}`);
    }
  }
  assert.ok(read > 1000, `only ${read} pieces read: the census lost its pages`);
  assert.deepEqual(misread, []);
});
