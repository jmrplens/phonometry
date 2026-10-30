// What check-cited-standards.mjs holds a page's structured data to, on builds
// small enough to read.
//
// The real build hands the check only the Datasets the site publishes today,
// all of them catalogues, so a check that let every Dataset name what it
// liked would stay green there until some other page published one. Each test
// here writes the frontmatter of a page or two into a content directory of its
// own and the pages as built into a build directory beside it, runs the check
// on both the way CI does, and reads the exit status and what it printed.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-cited-standards.mjs');
const ORIGIN = `${siteUrl}${basePath}`;

/** A standard as the bibliography of `lang` defines it. */
const standard = (lang, designation) => ({
  '@type': 'CreativeWork',
  '@id': `${ORIGIN}${lang === 'es' ? '/es' : ''}/reference/bibliography/#std-${designation.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
  name: `Acoustics, ${designation}`,
  identifier: designation,
  genre: 'Technical standard',
});
const IMPLEMENTED = standard('en', 'ISO 1:2000');
const CITED = standard('en', 'ISO 2:2010');

/** The frontmatter of a page that implements one standard and only cites another. */
const FRONTMATTER = [
  '---',
  'title: "A page"',
  'references:',
  '  - type: standard',
  '    designation: "ISO 1:2000"',
  '    title: "Acoustics, ISO 1:2000"',
  '  - type: standard',
  '    designation: "ISO 2:2010"',
  '    title: "Acoustics, ISO 2:2010"',
  '    implemented: false',
  '---',
  '',
  'Prose.',
  '',
].join('\n');

/** A page as built: its graph, a chip for the standard it implements and its References section. */
function builtPage(nodes) {
  const graph = JSON.stringify({ '@context': 'https://schema.org', '@graph': nodes });
  return [
    `<!DOCTYPE html><html><head><script type="application/ld+json">${graph}</script></head><body>`,
    '<a class="page-chip" href="#ref-iso-1">ISO 1:2000</a>',
    '<section class="page-references"><ol>',
    '<li id="ref-iso-1"><cite>Acoustics, ISO 1:2000</cite> (ISO 1:2000).</li>',
    '<li id="ref-iso-2"><cite>Acoustics, ISO 2:2010</cite> (ISO 2:2010).</li>',
    '</ol></section></body></html>',
  ].join('');
}

/** The article of the page at `route`, based on the standard it implements. */
const article = (route) => ({
  '@type': 'TechArticle',
  '@id': `${ORIGIN}${route}#article`,
  isBasedOn: [{ '@id': IMPLEMENTED['@id'], '@type': 'CreativeWork', name: IMPLEMENTED.name }],
  about: [{ '@id': `${ORIGIN}/#software` }, { '@id': IMPLEMENTED['@id'] }],
});

/** A Dataset at `id` that says its rows were read off the standard the page only cites. */
const dataset = (id) => ({
  '@type': 'Dataset',
  '@id': id,
  name: 'Rows',
  isBasedOn: [{ '@id': CITED['@id'], '@type': 'CreativeWork', name: CITED.name }],
});

/**
 * Write `pages` (route -> the nodes of its graph) and their frontmatter, with
 * the two bibliographies, run the check on them, and say how it ended.
 */
function check(t, pages) {
  const root = mkdtempSync(join(tmpdir(), 'check-cited-standards-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const dist = join(root, 'dist');
  const content = join(root, 'content');
  const write = (file, text) => {
    mkdirSync(dirname(file), { recursive: true });
    writeFileSync(file, text);
  };
  for (const lang of ['en', 'es']) {
    const nodes = [standard(lang, 'ISO 1:2000'), standard(lang, 'ISO 2:2010')];
    write(join(dist, lang === 'es' ? 'es' : '', 'reference/bibliography/index.html'), builtPage(nodes));
  }
  for (const [route, nodes] of Object.entries(pages)) {
    write(join(dist, route, 'index.html'), builtPage(nodes));
    write(join(content, `${route.replace(/^\/|\/$/g, '')}.mdx`), FRONTMATTER);
  }
  const ran = spawnSync(process.execPath, [CHECK, dist, content], { encoding: 'utf8' });
  return { status: ran.status, out: ran.stdout, err: ran.stderr };
}

const CATALOGUE = '/reference/catalogues/fluids/';
const GUIDE = '/fluids/fluid-properties/';

test("a catalogue's dataset names the standard its rows were read from, which its page only cites", (t) => {
  const ran = check(t, {
    [CATALOGUE]: [article(CATALOGUE), dataset(`${ORIGIN}${CATALOGUE}#dataset-fluids`)],
    [GUIDE]: [article(GUIDE)],
  });
  assert.equal(ran.status, 0, ran.err);
  assert.match(ran.out, /2 cited entries on 2 pages/);
});

test("a Dataset on a page that is not a catalogue page is held to the page's claims", (t) => {
  const ran = check(t, {
    [CATALOGUE]: [article(CATALOGUE), dataset(`${ORIGIN}${CATALOGUE}#dataset-fluids`)],
    [GUIDE]: [article(GUIDE), dataset(`${ORIGIN}${GUIDE}#dataset`)],
  });
  assert.equal(ran.status, 1);
  assert.match(ran.err, /\/fluids\/fluid-properties\/: isBasedOn names ISO 2:2010, which the page only cites \(implemented: false\)/);
  assert.doesNotMatch(ran.err, /\/reference\/catalogues\/fluids\/:/);
});

test('a Dataset on a catalogue page that is not one of its catalogues is held to the same', (t) => {
  const ran = check(t, {
    [CATALOGUE]: [article(CATALOGUE), dataset(`${ORIGIN}${CATALOGUE}#dataset-summary`)],
  });
  assert.equal(ran.status, 1);
  assert.match(
    ran.err,
    /\/reference\/catalogues\/fluids\/: isBasedOn names ISO 2:2010, which the page only cites \(implemented: false\)/,
  );
});
