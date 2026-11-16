/**
 * The pages under src/content/docs, read from disk the way the site's content
 * collection reads them, for the writers that show other pages: the glossary
 * links each term to its guide by the guide's title, and the catalogue index
 * lists every catalogue page with its label and description.
 *
 * In the build those come from `astro:content`, which only exists inside
 * Astro. The renderer runs in plain Node (`make llms` reads it without a site
 * build), so this reads the same files: an entry's id is its path under the
 * content directory without the extension, an `index` file standing for its
 * directory, which is how the docs collection names them; its data is the
 * YAML frontmatter, and its body is what follows the frontmatter.
 *
 * @module
 */
import { existsSync, readdirSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

import { parse as parseYaml } from 'yaml';

import { readCommittedText } from '../line-ends.mjs';
import { CONTENT_DIR } from './render.mjs';

/**
 * A page as the content collection holds it, narrowed to what the writers
 * read.
 *
 * @typedef {object} ContentEntry
 * @property {string} id  `reference/catalogues/solids`, `es/reference/glossary`.
 * @property {string} body  The source after the frontmatter.
 * @property {{ title?: string, description?: string, sidebar?: { label?: string } } & Record<string, unknown>} data
 */

/**
 * Every page file under a directory, sorted.
 *
 * @param {string} [dir]
 * @returns {string[]}  Absolute paths.
 */
export function pageFiles(dir = CONTENT_DIR) {
  /** @type {string[]} */
  const found = [];
  const walk = (current) => {
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const path = join(current, entry.name);
      if (entry.isDirectory()) walk(path);
      else if (/\.mdx?$/u.test(entry.name)) found.push(path);
    }
  };
  if (existsSync(dir)) walk(dir);
  return found.sort();
}

/**
 * The id the docs collection gives a page file.
 *
 * @param {string} file  Absolute path under `contentDir`.
 * @param {string} [contentDir]
 * @returns {string}
 */
export function entryId(file, contentDir = CONTENT_DIR) {
  const path = relative(contentDir, file).split(sep).join('/').replace(/\.mdx?$/u, '');
  return path === 'index' ? 'index' : path.replace(/\/index$/u, '');
}

/** The frontmatter block at the head of a page. */
const FRONTMATTER = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u;

/**
 * One page file as an entry.
 *
 * @param {string} file
 * @param {string} [contentDir]
 * @returns {ContentEntry}
 */
export function readEntry(file, contentDir = CONTENT_DIR) {
  const source = readCommittedText(file);
  const head = FRONTMATTER.exec(source);
  const data = head ? parseYaml(head[1]) : {};
  return {
    id: entryId(file, contentDir),
    body: head ? source.slice(head[0].length) : source,
    data: data && typeof data === 'object' ? data : {},
  };
}

/**
 * Every page under a directory of the content collection, as entries.
 *
 * @param {string} [under]  A directory below the content root, `reference/catalogues`;
 *   the whole collection when omitted.
 * @param {string} [contentDir]
 * @returns {ContentEntry[]}
 */
export function readEntries(under = '', contentDir = CONTENT_DIR) {
  return pageFiles(join(contentDir, under)).map((file) => readEntry(file, contentDir));
}

/** Titles by id, read once per process: a page lists many guides. */
let titles;

/**
 * The title of the page with this id, as its frontmatter gives it.
 *
 * @param {string} id  `signals/levels/levels` or `es/signals/levels/levels`.
 * @returns {string | undefined}  Nothing when no page has that id.
 */
export function pageTitle(id) {
  titles ??= new Map(readEntries().map((entry) => [entry.id, entry.data.title]));
  const title = titles.get(id);
  return typeof title === 'string' ? title : undefined;
}
