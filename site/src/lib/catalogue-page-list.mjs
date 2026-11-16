/**
 * The published catalogues as pages, worked out from the pages themselves:
 * the part of src/lib/catalogue-pages.ts that does not need Astro.
 *
 * The build reads the pages through `astro:content`, which only exists inside
 * Astro; the Markdown copy of the catalogue overview is written in plain Node
 * (src/lib/agent-md/), which reads the same files from disk. Both hand their
 * entries to {@link catalogueIndex}, so the overview's list and its copy are
 * built by one function and cannot disagree about which pages exist, what
 * they are called or how many rows they hold.
 *
 * The order is `catalogueSlugs` in src/data/topics.mjs, and it is held to the
 * pages both ways. A page under `reference/catalogues/` that `catalogueSlugs`
 * does not name would build, reach the sitemap and the site search, and still
 * be missing from the sidebar, the finder, the overview's list and its
 * Markdown copy, and the router of old links; and a catalogue the generator
 * writes that no page renders would be rows no reader meets. Either is an
 * error, in each language, naming the page or the key.
 *
 * The rows are held to the page's bibliography the same way. Every table a
 * page prints is claimed by one entry of its frontmatter `references`, the
 * work it was read from, through that entry's `tables`; a table no entry
 * claims, a table claimed twice, a claim on a table the page does not print
 * or a claim on a key of another work is an error too
 * (src/lib/catalogue-sources.mjs says why), and so is a `tables` on a page
 * that is not a catalogue page, where nothing reads it.
 *
 * And each catalogue a page renders is a dataset in the page's structured
 * data (src/lib/catalogue-datasets.mjs), named and described by the page: the
 * first by its title, and by its description when it is the page's only
 * catalogue or else by the paragraph that opens the page, every later one by
 * the `##` heading it sits under and the paragraph that opens it. A first
 * catalogue of several with no paragraph before it, a later one with no
 * heading of its own, or a heading with no paragraph under it would be a
 * dataset with no name, nothing to say, or the page's words about rows it
 * does not hold, and a name or a description that holds a component, an
 * expression or a formula would publish it as written: each is an error too.
 *
 * @module
 */
import { basePath } from '../data/site.mjs';
import { catalogueSlugs } from '../data/topics.mjs';
import { catalogues } from '../generated/catalogues.mjs';
import { catalogueDatasets, catalogueSections } from './catalogue-datasets.mjs';
import { catalogueSourceProblems, printedTables, strayTableClaims } from './catalogue-sources.mjs';

/**
 * What a catalogue's dataset is called and what it says it holds.
 *
 * @typedef {object} CatalogueDataset
 * @property {keyof typeof catalogues} key  The catalogue: `absorption`, `absorptionAreas`.
 * @property {string} name  Its name: the page's title, or the heading it sits under.
 * @property {string} description  Its description: the page's when it is the page's only
 *   catalogue, or else the paragraph that opens the page or its own section.
 */

/**
 * One catalogue's page, in one language.
 *
 * @typedef {object} CataloguePage
 * @property {string} id  Its content entry: `reference/catalogues/porous-materials`, `es/...`.
 * @property {string} slug  The last segment of its address: `porous-materials`.
 * @property {string} href  Its address, with the site's base path and the locale.
 * @property {string} label  What the finder and the overview call it: the heading it had.
 * @property {string} description  The line a search result shows, which the overview lists under it.
 * @property {(keyof typeof catalogues)[]} keys  The catalogues it renders, in order: `absorption`, `absorptionAreas`.
 * @property {number} rows  How many rows those catalogues hold between them.
 * @property {CatalogueDataset[]} datasets  The dataset each of those catalogues is, in the same order.
 */

/**
 * A page as the content collection holds it, narrowed to what is read here.
 *
 * @typedef {object} CatalogueEntry
 * @property {string} id
 * @property {string | undefined} [body]
 * @property {{ title: string, description?: string, sidebar?: { label?: string }, references?: { tables?: string[] }[] }} data
 */

/**
 * Every catalogue page of `lang`, in the order the sidebar lists them.
 *
 * @param {'en' | 'es'} lang
 * @param {readonly CatalogueEntry[]} entries  The docs collection, or at least
 *   every page under `reference/catalogues/` of that language.
 * @returns {CataloguePage[]}
 * @throws {Error}  On a page `catalogueSlugs` does not list, a listed page
 *   that does not exist, a page that renders no catalogue or an unknown one,
 *   a table no reference claims or one claimed wrongly, a catalogue with no
 *   name or description for its dataset, and a catalogue no page renders.
 */
export function catalogueIndex(lang, entries) {
  const prefix = lang === 'es' ? 'es/' : '';
  /* Every page under the overview is a catalogue page, so every one has to
     be in the list. The overview's own id is `reference/catalogues`, with no
     slash after it, and is not caught here. */
  const listed = new Set(catalogueSlugs);
  const strays = entries
    .map((entry) => entry.id)
    .filter((id) => id.startsWith(`${prefix}reference/catalogues/`))
    .map((id) => id.slice(prefix.length))
    .filter((path) => !listed.has(path))
    .sort();
  if (strays.length > 0) {
    throw new Error(
      `[catalogue-pages] ${strays.map((path) => `${prefix}${path}`).join(', ')} ` +
        `${strays.length === 1 ? 'is' : 'are'} under reference/catalogues/ but not listed in catalogueSlugs ` +
        'in src/data/topics.mjs. Add each catalogue page there, where the sidebar, the finder, the ' +
        "overview's list and the router of old links read it.",
    );
  }

  /* What the pages say of their sources, gathered across the language so one
     build names every page to fix. A `tables` anywhere else is read by
     nothing, so it is refused rather than left to look like a source. */
  const sourceProblems = strayTableClaims(
    entries
      .filter((entry) => (entry.id === 'es' || entry.id.startsWith('es/')) === (lang === 'es'))
      .map((entry) => ({ id: entry.id, references: entry.data.references ?? [] })),
  );

  /* What stops a catalogue from being a dataset with a name and a
     description, gathered the same way. */
  /** @type {string[]} */
  const datasetProblems = [];

  const byId = new Map(entries.map((entry) => [entry.id, entry]));
  const pages = catalogueSlugs.map((path) => {
    const id = `${prefix}${path}`;
    const entry = byId.get(id);
    if (!entry) {
      throw new Error(
        `[catalogue-pages] src/data/topics.mjs lists "${path}", but there is no page ${id}. ` +
          'Every catalogue has a page in both languages.',
      );
    }
    const sections = catalogueSections(entry.body ?? '');
    const keys = sections.map(({ key }) => key);
    const unknown = keys.filter((key) => !(key in catalogues));
    if (keys.length === 0 || unknown.length > 0) {
      throw new Error(
        `[catalogue-pages] ${id} renders ${keys.length === 0 ? 'no catalogue' : `an unknown catalogue: ${unknown.join(', ')}`}.`,
      );
    }
    const known = /** @type {(keyof typeof catalogues)[]} */ (keys);
    sourceProblems.push(
      ...catalogueSourceProblems({
        page: id,
        references: entry.data.references ?? [],
        tables: printedTables(known.map((key) => catalogues[key])),
      }),
    );
    const { datasets, problems } = catalogueDatasets({
      id,
      title: entry.data.title,
      description: entry.data.description ?? '',
      sections,
    });
    datasetProblems.push(...problems);
    return {
      id,
      slug: path.split('/').at(-1) ?? path,
      href: `${basePath}/${id}/`,
      label: entry.data.sidebar?.label ?? entry.data.title,
      description: entry.data.description ?? '',
      keys: known,
      rows: known.reduce((total, key) => total + catalogues[key].rows.length, 0),
      datasets: /** @type {CatalogueDataset[]} */ (datasets),
    };
  });

  if (sourceProblems.length > 0) {
    throw new Error(
      `[catalogue-pages] the ${lang === 'es' ? 'Spanish' : 'English'} catalogue pages do not name the source ` +
        `of every table they print, in ${sourceProblems.length} place(s):\n  ${sourceProblems.join('\n  ')}\n` +
        'Give each catalogue page a `references` entry for every work its tables were read from, and list ' +
        "in that entry's `tables` the keys of the tables it printed (the `table` of each row in " +
        'src/generated/catalogues.mjs), the same on the English page and its Spanish twin.',
    );
  }

  if (datasetProblems.length > 0) {
    throw new Error(
      `[catalogue-pages] the ${lang === 'es' ? 'Spanish' : 'English'} catalogue pages leave a catalogue ` +
        `without a name or a description for its dataset, in ${datasetProblems.length} place(s):\n  ` +
        `${datasetProblems.join('\n  ')}\n` +
        "The first catalogue a page renders takes the page's title, and its description too unless the " +
        'page renders more than one, when the paragraph that opens the page describes it; give every ' +
        'later one a `##` heading of its own, after the catalogue before it, and open its section with ' +
        'a paragraph that says what it holds, written on the page itself and not inside an aside, a list ' +
        'or a component, in words alone: a dataset carries no component, expression or formula.',
    );
  }

  /* And every catalogue the generator writes is on a page of this language. */
  const shown = new Set(pages.flatMap((page) => page.keys));
  const unshown = Object.keys(catalogues).filter((key) => !shown.has(/** @type {keyof typeof catalogues} */ (key)));
  if (unshown.length > 0) {
    throw new Error(
      `[catalogue-pages] no ${lang === 'es' ? 'Spanish' : 'English'} catalogue page renders ` +
        `${unshown.join(', ')}. Render each with <Catalogues catalogue="..."> on a page under ` +
        `${prefix}reference/catalogues/ (a page of its own, listed in catalogueSlugs, or the page it ` +
        'belongs beside), and add its key to the union in src/components/Catalogues.astro.',
    );
  }
  return pages;
}

/**
 * How the overview counts a catalogue's rows, in each language.
 *
 * @param {number} rows
 * @param {'en' | 'es'} lang
 * @returns {string}
 */
export const rowCount = (rows, lang) =>
  lang === 'es' ? `${rows} ${rows === 1 ? 'fila' : 'filas'}` : `${rows} ${rows === 1 ? 'row' : 'rows'}`;
