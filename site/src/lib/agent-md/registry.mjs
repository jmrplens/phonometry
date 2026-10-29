/**
 * The writers, found beside the components they write.
 *
 * Dropping a `<Name>.md.mjs` next to `<Name>.astro` is the whole of giving a
 * component its Markdown form: there is no central list to keep in step. The
 * directory is scanned with `fs` rather than `import.meta.glob`, because the
 * renderer runs in plain Node (`make llms` reads it without a site build);
 * `buildRegistry` takes the modules as an argument, as jmrp.io's does, so a
 * test can hand it the writers it wants.
 *
 * @module
 */
import { readdirSync } from 'node:fs';
import { basename, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { SITE_DIR } from './render.mjs';

/** @typedef {import('./types.mjs').ComponentMarkdown} ComponentMarkdown */

/** Where the components, and so the writers, live. */
export const COMPONENTS_DIR = resolve(SITE_DIR, 'src', 'components');

/** The suffix that makes a file a writer. */
export const WRITER_SUFFIX = '.md.mjs';

/**
 * Every writer file under a directory, sorted.
 *
 * @param {string} [dir]
 * @returns {string[]}  Absolute paths.
 */
export function writerFiles(dir = COMPONENTS_DIR) {
  /** @type {string[]} */
  const found = [];
  const walk = (current) => {
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const path = join(current, entry.name);
      if (entry.isDirectory()) walk(path);
      else if (entry.name.endsWith(WRITER_SUFFIX)) found.push(path);
    }
  };
  walk(dir);
  return found.sort();
}

/**
 * The tag-to-writer map.
 *
 * A writer is named after its component and declares the same tag, so the
 * file a reader opens to find what `<Video>` becomes is `Video.md.mjs`, and
 * two writers can never claim one tag.
 *
 * @param {Record<string, { default?: ComponentMarkdown }>} modules  Module
 *   namespaces keyed by file path.
 * @returns {Map<string, ComponentMarkdown>}
 * @throws {Error}  On a writer with no default export, a tag that does not
 *   match the file name, or a tag claimed twice.
 */
export function buildRegistry(modules) {
  /** @type {Map<string, ComponentMarkdown>} */
  const registry = new Map();
  for (const [path, module] of Object.entries(modules)) {
    const spec = module.default;
    if (!spec) throw new Error(`${path} has no default export: a writer default-exports markdownFor({...})`);
    const expected = basename(path, WRITER_SUFFIX);
    if (spec.tag !== expected) {
      throw new Error(`${path} declares tag "${spec.tag}"; a writer is named after its component (${expected})`);
    }
    if (registry.has(spec.tag)) throw new Error(`two writers claim <${spec.tag}>`);
    registry.set(spec.tag, spec);
  }
  return registry;
}

/**
 * Imports every writer under a directory and builds the registry.
 *
 * @param {string} [dir]
 * @returns {Promise<Map<string, ComponentMarkdown>>}
 */
export async function loadRegistry(dir = COMPONENTS_DIR) {
  const files = writerFiles(dir);
  const modules = await Promise.all(files.map((file) => import(pathToFileURL(file).href)));
  return buildRegistry(Object.fromEntries(files.map((file, i) => [file, modules[i]])));
}
