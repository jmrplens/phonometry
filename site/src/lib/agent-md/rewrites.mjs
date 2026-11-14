/**
 * What the site's Markdown plugins write into a page before Astro renders it,
 * written the same way into the page's Markdown copy.
 *
 * astro.config.mjs runs Markdown plugins over every page, and a plugin that
 * writes into a page names the pages it writes into in `REWRITES`, paths below
 * the content tree (src/lib/remark-bibliography.mjs does: the two
 * bibliographies, whose source holds a marker, `<!-- bibliography: <area> -->`,
 * where the page shows the area's list). The copy is written from the page's
 * source, so without the plugin's work it would hold the markers and none of
 * what the page shows: the bibliography copies lost all 441 works that way.
 * Each such plugin has a rule here, keyed by its module, that writes the same
 * text with the plugin's own functions; `checkMarkdownWriters` fails on a
 * plugin that names pages and has no rule, and the renderer reports a marker
 * that reaches it unwritten.
 *
 * @module
 */
import { readFileSync } from 'node:fs';
import { join, relative, resolve, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

import { withSections } from '../bibliography-entries.mjs';
import { bibliographyOf } from '../remark-bibliography.mjs';

/**
 * The bibliographies of a content tree, by language, read once per process:
 * every page that asks reads the same lists.
 *
 * @type {Map<string, Promise<object[]>>}
 */
const bibliographies = new Map();

/**
 * One plugin's rule: the page's source with what the plugin writes into it.
 *
 * @callback Rewrite
 * @param {string} source  The page's source.
 * @param {{ contentDir: string, lang: 'en' | 'es', data?: object }} context
 * @returns {Promise<string>}
 */

/**
 * The rule of each Markdown plugin that writes into pages, keyed by its module
 * below the site: src/lib/remark-bibliography.mjs writes each area's list where
 * the page marks it, from every page's references, through `withSections`,
 * the functions the plugin's own lists come from.
 *
 * @type {Readonly<Record<string, Rewrite>>}
 */
export const PLUGIN_REWRITES = Object.freeze({
  'src/lib/remark-bibliography.mjs': async (source, { contentDir, lang, data }) => {
    const key = `${contentDir}\0${lang}`;
    let sections = data === undefined ? bibliographies.get(key) : undefined;
    if (sections === undefined) {
      sections = bibliographyOf(contentDir, lang, data);
      if (data === undefined) bibliographies.set(key, sections);
    }
    return withSections(source, await sections, lang);
  },
});

/** The content tree a page sits in, and its path below it, or undefined outside one. */
function placeOf(file) {
  const at = file.split(sep).join('/').lastIndexOf('/src/content/docs/');
  if (at < 0) return undefined;
  const contentDir = file.slice(0, at + '/src/content/docs'.length);
  return { contentDir, path: relative(contentDir, file).split(sep).join('/') };
}

/**
 * The Markdown plugins astro.config.mjs runs (`markdown:`), each with the
 * pages its module names in `REWRITES`, or `null` when it names none. The
 * reading is the one site/scripts/content-dates.test.mjs dates the pages by.
 *
 * @param {string} siteDir
 * @returns {Promise<{ module: string, rewrites: string[] | null }[]>}
 * @throws {Error}  When the config cannot be read for any reason but its
 *   absence, or holds no `markdown:` block where it is looked for.
 */
export async function markdownPlugins(siteDir) {
  let config;
  try {
    config = readFileSync(join(siteDir, 'astro.config.mjs'), 'utf8');
  } catch (error) {
    // A tree with no config (a test's) has no plugins; any other failure to
    // read it would hide every plugin from the check.
    if (/** @type {NodeJS.ErrnoException} */ (error)?.code === 'ENOENT') return [];
    throw error;
  }
  const block = /\bmarkdown:\s*\{([\s\S]*?)\n {2}\},/.exec(config)?.[1];
  if (block === undefined) {
    throw new Error(
      `${join(siteDir, 'astro.config.mjs')}: no \`markdown: { ... },\` block indented by two spaces, ` +
        'so the Markdown plugins the copies have to follow cannot be read',
    );
  }
  const used = new Set(block.match(/[\w$]+/g) ?? []);
  const plugins = [];
  for (const [, clause, spec] of config.matchAll(/^import\s+([^;]*?)\s+from\s+['"]([^'"]+)['"];?$/gm)) {
    if (!spec.startsWith('./src/')) continue;
    const names = clause.replace(/[{}]/g, ' ').split(/[\s,]+/).filter((name) => name && name !== 'as');
    if (!names.some((name) => used.has(name))) continue;
    const file = resolve(siteDir, spec);
    const module = await import(pathToFileURL(file).href);
    plugins.push({
      module: relative(siteDir, file).split(sep).join('/'),
      rewrites: Array.isArray(module.REWRITES) ? [...module.REWRITES] : null,
    });
  }
  return plugins;
}

/** The plugins of each site, read once per process. */
const pluginsOfSite = new Map();

/**
 * A page's source with what the site's Markdown plugins write into it, for a
 * page one of them names in `REWRITES`; any other page's source as it is.
 *
 * @param {string} file  The page's absolute path.
 * @param {string} source  Its text.
 * @param {{ lang: 'en' | 'es', plugins?: { module: string, rewrites: string[] | null }[], data?: object }} options
 *   The plugins are the site's above the page's content tree
 *   (`<site>/src/content/docs`) unless a test hands in its own.
 * @returns {Promise<string>}
 * @throws {Error}  On a plugin that writes into the page and has no rule here.
 */
export async function rewrittenSource(file, source, { lang, plugins, data }) {
  const place = placeOf(file);
  if (place === undefined) return source;
  const siteDir = resolve(place.contentDir, '..', '..', '..');
  if (plugins === undefined && !pluginsOfSite.has(siteDir)) pluginsOfSite.set(siteDir, await markdownPlugins(siteDir));
  const known = plugins ?? pluginsOfSite.get(siteDir);
  let text = source;
  for (const plugin of known) {
    if (!plugin.rewrites?.includes(place.path)) continue;
    const rule = PLUGIN_REWRITES[plugin.module];
    if (rule === undefined) {
      throw new Error(`${place.path}: ${plugin.module} writes into this page and the Markdown copy has no rule for it`);
    }
    text = await rule(text, { contentDir: place.contentDir, lang, data });
  }
  return text;
}
