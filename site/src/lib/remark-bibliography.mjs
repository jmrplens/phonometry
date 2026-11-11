/**
 * Puts the bibliography's entries on its page when the site is built.
 *
 * The page (`reference/bibliography.md`, and `es/reference/bibliography.md`)
 * keeps its prose and its headings and marks where each section's list goes
 * with a comment on a line of its own, `<!-- bibliography: signal-analysis -->`.
 * This plugin reads the references of every page of the content tree, builds
 * each section's entries from them (src/lib/bibliography-entries.mjs), parses
 * the list as Markdown with the page's own parser, so a note's maths, code and
 * links read as they would anywhere on the page, and puts it where the comment
 * was. Each item carries the fragment of the work's `@id` as its `id`, so the
 * address the structured data names a work by,
 * `/reference/bibliography/#std-iec-61672-1-2013`, opens on its entry.
 *
 * The build stops when the page marks a section the data does not have, marks
 * one twice, or leaves a section unmarked: a work in that section would have
 * no entry. It stops too on a list the page writes itself, anywhere in it: the
 * page's prose holds none, so such a list is an entry added by hand, which no
 * reference would keep in step with the pages that cite its work.
 * check:structured-data then reads the built page against the structured data
 * and the pages that cite each work (scripts/check-structured-data.mjs, "the
 * bibliography lists"), and fails an item no reference wrote there too.
 *
 * Every other page goes through untouched. The plugin runs after remark-math,
 * so a note's `$...$` is read as maths, and after smartypants, so a report
 * number's `--` stays as the References section of each guide prints it.
 */
import { parseFrontmatter } from '@astrojs/markdown-remark';

import { CITED_BY, MARKER, sectionMarkdown, siteBibliography, withSections } from './bibliography-entries.mjs';
import { readPageReferences } from './page-references.mjs';

/** The bibliography page of either language, by its path, and the content tree above it. */
const PAGE = /^(.*[\\/]src[\\/]content[\\/]docs)[\\/](es[\\/])?reference[\\/]bibliography\.md$/;

/**
 * The bibliography's language when `path` is one of its two pages, and
 * `undefined` for every other file: the test this plugin puts to a file
 * before it writes a list into it.
 *
 * @param {string} path The file, below `src/content/docs`.
 * @returns {'en' | 'es' | undefined}
 */
export function bibliographyLanguage(path) {
  const found = PAGE.exec(String(path ?? ''));
  if (!found) return undefined;
  return found[2] ? 'es' : 'en';
}

/**
 * A page's Markdown as its copy reads it: the bibliography's with each marker
 * replaced by its section's list (`withSections`), as this plugin fills the
 * page, and every other page's as written. A guide that shows a marker as an
 * example, in a fence or out of one, is left alone here as the plugin leaves
 * it, so its copy prints the example its page prints.
 *
 * @param {string} source The page's Markdown, frontmatter stripped.
 * @param {string} path The page's file.
 * @param {(lang: 'en' | 'es') => readonly {key: string, entries: object[]}[]} sectionsOf
 *   The sections of a language's bibliography, asked for only on its page.
 * @returns {string}
 */
export function withBibliographyLists(source, path, sectionsOf) {
  const lang = bibliographyLanguage(path);
  return lang ? withSections(source, sectionsOf(lang), lang) : source;
}

/**
 * Every section of a language's bibliography, from the pages under `contentDir`.
 *
 * @param {string} contentDir The content tree, `src/content/docs`.
 * @param {'en' | 'es'} lang
 * @param {{sections?: readonly {key: string}[], prefixes?: readonly (readonly [string, string])[],
 *   works?: Readonly<Record<string, object>>}} [data] What src/data/bibliography.mjs
 *   gives, unless a test hands in its own.
 */
export async function bibliographyOf(contentDir, lang, data = {}) {
  return siteBibliography(await readPageReferences(contentDir, { parseFrontmatter }), lang, data);
}

/**
 * Wrap the "Cited by" list that closes an entry in a span marked
 * `data-cited-by`, so the check of the built page reads the pages an entry
 * lists apart from any link its note holds.
 *
 * @param {object} item The entry's list item, as the page's parser read it.
 * @param {string} lead The words that open the list, `Cited by`.
 * @returns {boolean} Whether the list was found.
 */
function markCitedBy(item, lead) {
  const paragraph = item.children?.[0];
  const children = paragraph?.type === 'paragraph' ? paragraph.children : [];
  for (let index = children.length - 1; index >= 0; index -= 1) {
    const node = children[index];
    const at = node.type === 'text' ? node.value.lastIndexOf(`\n${lead} `) : -1;
    if (at < 0) continue;
    const opening = { type: 'text', value: node.value.slice(at + 1) };
    node.value = node.value.slice(0, at + 1);
    const span = {
      type: 'bibliographyCitedBy',
      data: { hName: 'span', hProperties: { dataCitedBy: '' } },
      children: [opening, ...children.slice(index + 1)],
    };
    paragraph.children = [...children.slice(0, index + 1), span];
    return true;
  }
  return false;
}

/** The text of a Markdown node and everything under it, as a reader reads it. */
const textOf = (node) =>
  typeof node.value === 'string' ? node.value : (node.children ?? []).map(textOf).join(node.type === 'list' ? ' ' : '');

/** Every list under `node`, outermost first, not looking inside one it found. */
function listsUnder(node, out = []) {
  for (const child of node.children ?? []) {
    if (child.type === 'list') out.push(child);
    else listsUnder(child, out);
  }
  return out;
}

/**
 * The remark plugin.
 *
 * @param {Parameters<typeof bibliographyOf>[2]} [data] What the sections, the
 *   prefixes and the works are, when a test says; src/data/bibliography.mjs
 *   otherwise.
 */
export function remarkBibliography(data = {}) {
  const processor = this;
  return async function transform(tree, file) {
    const found = PAGE.exec(String(file.path ?? ''));
    const lang = bibliographyLanguage(file.path);
    if (!found || !lang) return;
    const sections = await bibliographyOf(found[1], lang, data);
    const byKey = new Map(sections.map((section) => [section.key, section]));
    const placed = new Set();
    const problems = [];
    // Before the markers are filled in, every list on the page is one it wrote.
    for (const list of listsUnder(tree)) {
      const text = textOf(list.children?.[0] ?? list).replace(/\s+/g, ' ').trim();
      problems.push(
        `it holds a list src/data/bibliography.mjs did not write, from "${text.length > 120 ? `${text.slice(0, 117)}...` : text}": ` +
          `an entry is written from the references of the pages that cite its work, and its note and section are data ` +
          `keyed by the work there`,
      );
    }
    tree.children = tree.children.flatMap((node) => {
      const marker = node.type === 'html' ? MARKER.exec(node.value.trim()) : null;
      if (!marker) return [node];
      const section = byKey.get(marker[1]);
      if (!section) {
        problems.push(`it marks a section src/data/bibliography.mjs does not have, ${marker[1]}`);
        return [];
      }
      if (placed.has(section.key)) problems.push(`it marks the section ${section.key} twice`);
      placed.add(section.key);
      if (section.entries.length === 0) return [];
      const list = processor.parse(sectionMarkdown(section, lang)).children;
      const items = list.length === 1 && list[0].type === 'list' ? list[0].children : [];
      if (items.length !== section.entries.length) {
        problems.push(`the list of ${section.key} parsed as ${items.length} item(s) for ${section.entries.length} work(s)`);
        return list;
      }
      for (const [index, item] of items.entries()) {
        item.data = { ...item.data, hProperties: { ...item.data?.hProperties, id: section.entries[index].fragment } };
        if (!markCitedBy(item, CITED_BY[lang].lead)) {
          problems.push(`the entry ${section.entries[index].fragment} parsed with no "${CITED_BY[lang].lead}" list`);
        }
      }
      return list;
    });
    for (const section of sections) {
      if (!placed.has(section.key) && section.entries.length > 0) {
        problems.push(`it leaves the section ${section.key} unmarked, so its ${section.entries.length} work(s) have no entry`);
      }
    }
    if (problems.length > 0) {
      throw new Error(`${file.path}: the bibliography cannot be written, ${problems.join('; ')}`);
    }
  };
}
