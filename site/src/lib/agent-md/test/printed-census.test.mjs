// The text a page prints as it is reads the same in its Markdown copy, on
// every page of the site: a figure's alt, a clip's and a fiche's title,
// description and caption, and every work of the References section, each
// written by the writer the copy uses (the component writers of the registry,
// the References writer of page.mjs) and read back by the site's own Markdown
// pipeline (scripts/shared/markdown-reader.mjs). The Spanish seat-vibration
// guide printed `a*wS = SEAT por a*wP` in an alt, and the copy printed
// `awS = SEAT por awP`.
//
// Usage (from site/, after `pnpm install`): pnpm run test:agent-md
import assert from 'node:assert/strict';
import { relative, sep } from 'node:path';
import { before, test } from 'node:test';

import { decodeReferences, oneLine, printed, withoutTags } from '../../../../scripts/shared/markdown-reader.mjs';
import { pageMarkup } from '../../../../scripts/shared/markdown-spans.mjs';
import { routeOf } from '../../page-markdown.mjs';
import { citationParts, noteParts, opening, sortedReferences } from '../../references-format.mjs';
import { pageFiles, readEntry } from '../content.mjs';
import { referencesMarkdown } from '../page.mjs';
import { loadRegistry } from '../registry.mjs';
import { CONTENT_DIR } from '../render.mjs';
import { render } from './helpers.mjs';

/** @type {Map<string, import('../types.mjs').ComponentMarkdown>} */
let registry;
before(async () => {
  registry = await loadRegistry();
});

/** An attribute of a component tag written as a string, as MDX reads it: its character references read. */
function attributeValue(tag, name) {
  const found = tag.match(new RegExp(String.raw`\b${name}="([^"]*)"`, 'u'));
  return found ? decodeReferences(found[1]) : undefined;
}

/** The word a clip's and a fiche's line opens with, in each language. */
const LEAD = { Video: { en: 'Video', es: 'Vídeo' }, ReportPreview: { en: 'Report', es: 'Informe' } };

test('the text a page prints as it is reads the same in its copy, on every page', async () => {
  const misread = [];
  let read = 0;
  for (const file of pageFiles()) {
    const path = relative(CONTENT_DIR, file).split(sep).join('/');
    const route = routeOf(path);
    const lang = route === 'es' || route.startsWith('es/') ? 'es' : 'en';
    const { body, data } = readEntry(file);
    if (path.endsWith('.mdx')) {
      for (const found of pageMarkup(body, { kind: 'mdx' }).matchAll(/<(ThemeImage|Video|ReportPreview)\b[^>]*\/>/gu)) {
        const tag = body.slice(found.index, found.index + found[0].length);
        const shown = await printed(render(`${tag}\n`, { registry, lang }).markdown);
        read += 1;
        if (found[1] === 'ThemeImage') {
          const alt = oneLine(attributeValue(tag, 'alt') ?? '');
          if (shown.alts[0] !== alt) misread.push(`${path}: the alt ${JSON.stringify(alt)} prints as ${JSON.stringify(shown.alts[0])}`);
          continue;
        }
        const caption = attributeValue(tag, 'caption');
        const words = [`${LEAD[found[1]][lang]}: ${attributeValue(tag, 'title')}: ${attributeValue(tag, 'description')}`, caption ?? ''];
        const expected = oneLine(words.join(' '));
        if (shown.text !== expected) misread.push(`${path}: ${JSON.stringify(expected)} prints as ${JSON.stringify(shown.text)}`);
      }
    }
    const references = /** @type {import('../../references-format.mjs').Reference[] | undefined} */ (data.references);
    if (!Array.isArray(references) || !references.length) continue;
    const shown = await printed(referencesMarkdown(references, lang));
    const items = [...shown.html.matchAll(/<li>([^]*?)<\/li>/gu)].map((item) => oneLine(decodeReferences(withoutTags(item[1]))));
    for (const [index, [, work]] of sortedReferences(references, lang).entries()) {
      const note = work.note ? ` ${noteParts(work.note).map((part) => part.text).join('')}` : '';
      const expected = oneLine(`${opening(work, lang)}${citationParts(work, lang).map((part) => part.text).join('')}${note}`);
      read += 1;
      if (items[index] !== expected) misread.push(`${path}: the work ${JSON.stringify(expected)} prints as ${JSON.stringify(items[index])}`);
    }
  }
  assert.ok(read > 3500, `only ${read} pieces read: the census lost its pages`);
  assert.deepEqual(misread, []);
});
