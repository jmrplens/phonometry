// The catalogue pages as src/lib/catalogue-page-list.mjs works them out, on
// the real pages and on small sets of entries carrying each defect it exists
// to stop.
//
// The build hands it the docs collection and the Markdown copy of the
// overview hands it the same pages read from disk, so a defect it stopped
// noticing would pass in both. Each test here gives it entries shaped like
// the collection's, built from the real pages with one thing wrong.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { describe, test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { catalogueSlugs } from '../src/data/topics.mjs';
import { catalogues } from '../src/generated/catalogues.mjs';
import { catalogueIndex, rowCount } from '../src/lib/catalogue-page-list.mjs';
import { readCommittedText } from '../src/lib/line-ends.mjs';
import { readReferences } from './shared/narrow-references.mjs';
import { basePath as SITE_BASE } from '../src/data/site.mjs';

const CONTENT = join(dirname(fileURLToPath(import.meta.url)), '..', 'src', 'content', 'docs');

/**
 * The catalogue pages of a language as the collection holds them: the id, the
 * body, the three frontmatter fields read here and the references whose
 * `tables` the list holds to the rows, taken from the files with no YAML
 * parser (this suite runs before the install).
 *
 * @param {'en' | 'es'} lang
 */
function entries(lang) {
  const dir = join(CONTENT, ...(lang === 'es' ? ['es'] : []), 'reference', 'catalogues');
  return readdirSync(dir)
    .filter((name) => /\.mdx?$/u.test(name))
    .map((name) => {
      const source = readCommittedText(join(dir, name));
      const [, head = '', body = source] = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/u.exec(source) ?? [];
      const value = (key, indented = false) =>
        new RegExp(indented ? `^  ${key}: "(.*)"$` : `^${key}: "(.*)"$`, 'mu').exec(head)?.[1];
      const slug = name.replace(/\.mdx?$/u, '');
      const id = `${lang === 'es' ? 'es/' : ''}reference/catalogues${slug === 'index' ? '' : `/${slug}`}`;
      return {
        id,
        body,
        data: {
          title: value('title') ?? '',
          description: value('description'),
          sidebar: { label: value('label', true) },
          references: readReferences(source, name),
        },
      };
    });
}

describe('the catalogue pages', () => {
  for (const lang of /** @type {const} */ (['en', 'es'])) {
    test(`every listed page of ${lang}, in the sidebar's order, with every catalogue and every row`, () => {
      const pages = catalogueIndex(lang, entries(lang));
      assert.deepEqual(
        pages.map((page) => `reference/catalogues/${page.slug}`),
        catalogueSlugs,
      );
      assert.deepEqual(
        pages.flatMap((page) => page.keys).sort(),
        Object.keys(catalogues).sort(),
      );
      const rows = Object.values(catalogues).reduce((total, table) => total + table.rows.length, 0);
      assert.equal(pages.reduce((total, page) => total + page.rows, 0), rows);
      for (const page of pages) {
        assert.ok(page.label, page.slug);
        assert.ok(page.description, page.slug);
        assert.equal(page.href, `${SITE_BASE}/${lang === 'es' ? 'es/' : ''}reference/catalogues/${page.slug}/`);
      }
    });
  }

  test('a page under the catalogues that the list does not name stops it', () => {
    const stray = { id: 'reference/catalogues/new-table', body: '<Catalogues catalogue="solids" />', data: { title: 'New' } };
    assert.throws(() => catalogueIndex('en', [...entries('en'), stray]), /reference\/catalogues\/new-table is under reference\/catalogues\/ but not listed in catalogueSlugs/u);
  });

  test('a listed page that does not exist stops it', () => {
    const missing = entries('es').filter((entry) => entry.id !== 'es/reference/catalogues/gases');
    assert.throws(() => catalogueIndex('es', missing), /lists "reference\/catalogues\/gases", but there is no page es\/reference\/catalogues\/gases/u);
  });

  test('a page with no catalogue, or an unknown one, stops it', () => {
    const blank = entries('en').map((entry) => (entry.id === 'reference/catalogues/gases' ? { ...entry, body: 'Prose only.' } : entry));
    assert.throws(() => catalogueIndex('en', blank), /reference\/catalogues\/gases renders no catalogue/u);
    const typo = entries('en').map((entry) =>
      entry.id === 'reference/catalogues/gases' ? { ...entry, body: '<Catalogues catalogue="gasses" lang="en" />' } : entry,
    );
    assert.throws(() => catalogueIndex('en', typo), /renders an unknown catalogue: gasses/u);
  });

  test('a catalogue no page renders stops it', () => {
    const dropped = entries('en').map((entry) =>
      entry.id === 'reference/catalogues/absorption-coefficients'
        ? { ...entry, body: entry.body.replace('<Catalogues catalogue="absorptionAreas" lang="en" />', '') }
        : entry,
    );
    assert.throws(() => catalogueIndex('en', dropped), /no English catalogue page renders absorptionAreas/u);
  });

  test('the count says row or rows, fila or filas', () => {
    assert.equal(rowCount(1, 'en'), '1 row');
    assert.equal(rowCount(260, 'en'), '260 rows');
    assert.equal(rowCount(1, 'es'), '1 fila');
    assert.equal(rowCount(2, 'es'), '2 filas');
  });
});
