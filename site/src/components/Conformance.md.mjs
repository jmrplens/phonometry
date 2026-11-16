/**
 * Conformance: the report's rows, as the plain table of record.
 *
 * Kept, on the English page: every section and every row of the report, in
 * the report's order, with every verdict in words. They are the body of
 * docs/CONFORMANCE.md, which scripts/conformance/render.py writes from the
 * same docs/conformance.json the component renders, so the copy and the page
 * read one document. Its collapsible sections become sections of the copy:
 * each `<details>` turns into an `## <summary>` heading, because a reader
 * without a viewport reads every section whole, and because a heading is
 * where a long copy can be cut into parts (the report runs to several hundred
 * kilobytes). The small print loses its `<sub>`, `<b>` turns bold, and the
 * character references the generator writes (`&#916;`, `&ge;`, `&amp;`) are
 * written as the characters they stand for. Any other HTML tag in the file is
 * reported: the generator would have grown a construct this writer does not
 * know.
 *
 * Dropped: the verdict marks (`![Pass][cv-pass]`), together with the image
 * references they point to, because every mark travels beside its verdict in
 * words; and the generator's header comment, addressed to contributors.
 *
 * Spanish: one paragraph pointing to the English copy, and the rows dropped.
 * The page translates the column headings and verdicts but not the
 * designations, clauses, quantities and units, and it says itself that the
 * plain-text rows are the English page's; a second copy of 400 kB of English
 * rows would say nothing the first does not.
 */
import { join } from 'node:path';

import { inlineSpans } from '../../scripts/shared/markdown-spans.mjs';

import { line } from '../lib/agent-md/markdown-table.mjs';
import { REPO_DIR } from '../lib/agent-md/render.mjs';
import { readCommittedText } from '../lib/line-ends.mjs';
import { markdownFor } from '../lib/agent-md/types.mjs';

/** Character references the generator writes, and what they stand for. */
const ENTITIES = { amp: '&', ge: '≥', le: '≤', middot: '·', nbsp: ' ', times: '×', minus: '−', plusmn: '±' };

/** Tags the generator writes, which the transform below handles. */
const KNOWN_TAGS = new Set(['details', 'summary', 'b', 'sub']);

/**
 * `&#916;`, `&ge;` and their kin, as characters. `&lt;` and `&gt;` stay as
 * written: as characters they could open a tag the copy never had.
 *
 * @param {string} text
 * @returns {string}
 */
function decodeEntities(text) {
  return text.replaceAll(/&(#x[0-9a-f]+|#[0-9]+|[a-z]+);/giu, (match, ref) => {
    if (ref.startsWith('#x') || ref.startsWith('#X')) return String.fromCodePoint(Number.parseInt(ref.slice(2), 16));
    if (ref.startsWith('#')) return String.fromCodePoint(Number.parseInt(ref.slice(1), 10));
    return Object.hasOwn(ENTITIES, ref) ? ENTITIES[ref] : match;
  });
}

/**
 * docs/CONFORMANCE.md as the body of the conformance page's Markdown copy.
 *
 * @param {string} text  The file.
 * @param {(message: string) => void} [report]  Told about a tag this does not know.
 * @returns {string}
 */
export function conformanceMarkdown(text, report = () => {}) {
  let body = text.replace(/^\s*<!--[\s\S]*?-->\s*/u, '');
  body = body
    .replaceAll(/^\[cv-[a-z-]+\]:.*$\n?/gmu, '')
    .replaceAll(/!\[[^\]]*\]\[cv-[a-z-]+\] ?/gu, '')
    .replaceAll(/^<\/?details>[ \t]*$/gmu, '')
    .replaceAll(/^<summary>([\s\S]*?)<\/summary>[ \t]*$/gmu, (_match, inner) => {
      const title = line(inner.replaceAll(/<\/?b>/gu, ''));
      return `## ${title}`;
    })
    .replaceAll(/<\/?sub>/gu, '')
    .replaceAll(/<b>([\s\S]*?)<\/b>/gu, '**$1**');
  const leftover = new Set();
  // A tag outside code spans that this transform did not consume. The spans
  // are read as the page reads them (scripts/shared/markdown-spans.mjs, rule
  // F65), so a backtick a span holds or escapes ends no span here either.
  let at = 0;
  const outside = [];
  for (const [start, end] of inlineSpans(body)) {
    outside.push(body.slice(at, start));
    at = end;
  }
  outside.push(body.slice(at));
  for (const segment of outside) {
    for (const [, name] of segment.matchAll(/<\/?([a-zA-Z][a-zA-Z0-9]*)\b/gu)) {
      if (!KNOWN_TAGS.has(name.toLowerCase())) leftover.add(name);
    }
  }
  for (const name of leftover) report(`docs/CONFORMANCE.md carries <${name}>, which Conformance.md.mjs has no rule for`);
  return decodeEntities(body)
    .replaceAll(/\n{3,}/gu, '\n\n')
    .trim();
}

/** What the Spanish copy says instead of the rows. */
const POINTER = {
  es:
    'Las filas del informe, con sus designaciones de norma, apartados, magnitudes y unidades tal como las ' +
    'ejecuta el registro de comprobaciones, están en texto plano en la copia en Markdown de la página en ' +
    'inglés: ',
};

export default markdownFor({
  tag: 'Conformance',
  props: ['lang'],
  toMarkdown(node, ctx) {
    const lang = ctx.attr(node, 'lang') === 'es' ? 'es' : 'en';
    if (lang !== ctx.lang) ctx.issue(node, `Conformance lang="${lang}" on a page in ${ctx.lang}`);
    if (lang === 'es') {
      return `${POINTER.es}${ctx.site.url('/reference/conformance/index.md')}.`;
    }
    const text = readCommittedText(join(REPO_DIR, 'docs', 'CONFORMANCE.md'));
    return conformanceMarkdown(text, (message) => ctx.issue(node, message));
  },
});
