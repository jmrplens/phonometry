/**
 * Catalogues: one published catalogue, as a Markdown table under a legend.
 *
 * Kept: every row and every column the page shows, in the page's order and
 * language. The row heading holds what the page stacks in the first cell
 * (the heading the book prints above a block of rows, the name, the variant
 * under it); then the word columns some row fills, a fluid's conditions,
 * every quantity with its unit in its heading, and the source, or for a
 * fluid what fixes its state. The words around the rows come from
 * src/data/catalogue-copy.mjs, which the component reads too.
 *
 * What a cell is, which the page shows as a mark and explains on the mark,
 * the copy writes as a word in brackets after the value: `(derived)`,
 * `(range)`, `(converted from 25 °F)`. The legend above the table says what
 * each word means, in the page's own sentences, for the kinds that table
 * holds. The notes the page opens from a mark or from an asterisked name (the
 * page's note on a row, the reason behind a cell, why a cell is blank) are
 * footnotes under the table, each written once however many cells share it.
 * The values are transcribed text, not Markdown, so the characters that
 * would turn into markup in them are escaped.
 *
 * Dropped: the filter and its suggestions, which are CatalogueFinder's
 * controls over these same rows, and the two sentences that only a screen
 * needs: the legend's instructions for opening a mark with a click or the
 * keyboard, and the label of the box that scrolls sideways.
 */
import { catalogueWords, cellNote, cellText, columnHeading, say, textColumns } from '../data/catalogue-copy.mjs';
import { catalogues } from '../generated/catalogues.mjs';
import { line, plainText, table } from '../lib/agent-md/markdown-table.mjs';
import { markdownFor } from '../lib/agent-md/types.mjs';

/** @typedef {import('../generated/catalogues.mjs').CatalogueCell} CatalogueCell */
/** @typedef {import('../generated/catalogues.mjs').CatalogueRow} CatalogueRow */

/**
 * The word the copy writes after a value for each kind of cell that is not a
 * plain number the page printed. In English it is the kind's own name, the
 * one `materials` reports for the cell; in Spanish, its translation.
 */
const KIND_WORDS = {
  en: {
    fixed: 'fixed',
    derived: 'derived',
    converted: 'converted',
    carried: 'carried',
    approximate: 'approximate',
    estimated: 'estimated',
    range: 'range',
    bound: 'bound',
    reported: 'reported',
    unquantified: 'unquantified',
  },
  es: {
    fixed: 'fijado',
    derived: 'calculado',
    converted: 'convertido',
    carried: 'arrastrado',
    approximate: 'aproximado',
    estimated: 'estimado',
    range: 'intervalo',
    bound: 'cota',
    reported: 'lecturas',
    unquantified: 'sin cifra',
  },
};

/** The sentences around the kinds, in each language. */
const LEGEND = {
  en: {
    lead: 'Each value is the number its page prints, unless a word in brackets after it says what else it is:',
    converted: (printed) => `converted from ${printed}`,
    notes: 'A note mark after a name or a value points to the note the page makes about that row or cell, listed under the table.',
  },
  es: {
    lead: 'Cada valor es el número que imprime su página, salvo que una palabra entre paréntesis detrás diga qué otra cosa es:',
    converted: (printed) => `convertido desde ${printed}`,
    notes: 'Una llamada de nota tras un nombre o un valor remite a la nota que la página hace sobre esa fila o esa celda, recogida bajo la tabla.',
  },
};

/**
 * One catalogue as its legend, its table and its notes.
 *
 * @param {string} section  The catalogue's key in `catalogues.mjs`.
 * @param {'en' | 'es'} lang
 * @returns {string}
 */
export function catalogueMarkdown(section, lang) {
  const data = catalogues[/** @type {keyof typeof catalogues} */ (section)];
  const { copy, rowHeading } = catalogueWords(section, lang);
  const words = KIND_WORDS[lang];
  const legend = LEGEND[lang];
  const fluids = section === 'fluids';
  const columns = textColumns(section, data.rows, lang);

  /** @type {Map<string, string>} note text to footnote label */
  const notes = new Map();
  const mark = (note) => {
    const text = line(note);
    if (!text) return '';
    if (!notes.has(text)) notes.set(text, `${section}-${notes.size + 1}`);
    return `[^${notes.get(text)}]`;
  };

  /** @type {Set<string>} the kinds this table holds, for the legend */
  const kinds = new Set();

  /** @param {CatalogueCell} one */
  const writeCell = (one) => {
    const value = plainText(cellText(one, lang));
    let kind = '';
    if (value && one.kind !== 'printed' && one.kind !== 'absent') {
      kinds.add(one.kind);
      const word = words[one.kind];
      kind = ` (${one.kind === 'converted' && one.printed ? legend.converted(plainText(one.printed)) : word})`;
    }
    return `${value}${kind}${mark(cellNote(one, lang))}`;
  };

  /** @param {CatalogueRow} row */
  const writeHeading = (row) => {
    const group = plainText(say(row, 'group', lang));
    const name = plainText(say(row, 'name', lang));
    const variant = plainText(say(row, 'variant', lang));
    const named = `${group ? `${group}: ` : ''}${name}${variant ? ` (${variant})` : ''}`;
    return `${named}${mark(say(row, 'note', lang))}`;
  };

  const head = [
    rowHeading,
    ...columns.map((column) => column.label),
    ...(fluids ? [copy.conditions] : []),
    ...data.columns.map((column) => {
      const heading = columnHeading(column, lang);
      return column.unit ? `${heading} (${column.unit})` : heading;
    }),
    fluids ? copy.fixedBy : copy.source,
  ];
  const body = data.rows.map((row) => [
    writeHeading(row),
    ...columns.map((column) => plainText(say(row, column.field, lang))),
    ...(fluids ? [`${row.temperature} °C, ${row.pressure} Pa`] : []),
    ...row.cells.map(writeCell),
    plainText(say(row, fluids ? 'model' : 'source', lang)),
  ]);
  const grid = table(head, body);

  const parts = [];
  if (kinds.size > 0) {
    const order = Object.keys(words).filter((kind) => kinds.has(kind));
    const list = order.map((kind) => `- **${words[kind]}**: ${copy.kinds[kind]}`).join('\n');
    parts.push(`${legend.lead}\n\n${list}`);
  }
  if (notes.size > 0) parts.push(legend.notes);
  parts.push(grid);
  if (notes.size > 0) {
    parts.push([...notes].map(([text, label]) => `[^${label}]: ${plainText(text)}`).join('\n'));
  }
  return parts.join('\n\n');
}

export default markdownFor({
  tag: 'Catalogues',
  props: ['catalogue', 'lang'],
  toMarkdown(node, ctx) {
    const section = ctx.attr(node, 'catalogue') ?? '';
    if (!Object.hasOwn(catalogues, section)) {
      ctx.issue(node, `Catalogues catalogue=${JSON.stringify(section)} is not a catalogue src/generated/catalogues.mjs holds`);
      return '';
    }
    const lang = ctx.attr(node, 'lang') === 'es' ? 'es' : 'en';
    if (lang !== ctx.lang) ctx.issue(node, `Catalogues lang="${lang}" on a page in ${ctx.lang}`);
    return catalogueMarkdown(section, lang);
  },
});
