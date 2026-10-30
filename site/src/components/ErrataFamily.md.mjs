/**
 * ErrataFamily: one document family of the errata registry, as the index
 * lists it.
 *
 * Kept: the family's name linked to its page, how many entries the page
 * holds, and every entry's heading as the family page writes it, mathematics
 * and code included, in the page's order. The headings are read from the
 * generated family page, `reference/errata/<slug>.md` in the page's language,
 * which is where the component reads them too.
 *
 * Dropped: the link from each entry to its own place on the family page. The
 * page links each heading by the id the build gives it, and that id is
 * computed after the heading's mathematics is typeset (ErrataFamily.astro
 * says why only the build can know it); a fragment guessed here would be
 * wrong on exactly the entries about a formula. The family link leads to the
 * page, where the entries follow in the order listed.
 */
import { existsSync } from 'node:fs';
import { join } from 'node:path';

import { bracketText, line } from '../lib/agent-md/markdown-table.mjs';
import { parse } from '../lib/agent-md/processor.mjs';
import { CONTENT_DIR } from '../lib/agent-md/render.mjs';
import { markdownFor } from '../lib/agent-md/types.mjs';
import { readCommittedText } from '../lib/line-ends.mjs';

/** How the index counts a family's entries, in each language. */
const COUNT = {
  en: (n) => `${n} ${n === 1 ? 'entry' : 'entries'}`,
  es: (n) => `${n} ${n === 1 ? 'entrada' : 'entradas'}`,
};

/**
 * The `##` headings of a family page, each as its source writes it.
 *
 * @param {string} source  The family page, a `.md` file.
 * @returns {string[]}
 */
export function entryHeadings(source) {
  const tree = parse(source, { mdx: false });
  return (tree.children ?? [])
    .filter((node) => node.type === 'heading' && node.depth === 2)
    .map((node) => {
      const children = node.children ?? [];
      const start = children[0]?.position?.start.offset;
      const end = children.at(-1)?.position?.end.offset;
      return start === undefined || end === undefined ? '' : line(source.slice(start, end));
    })
    .filter(Boolean);
}

export default markdownFor({
  tag: 'ErrataFamily',
  props: ['slug', 'name'],
  toMarkdown(node, ctx) {
    const slug = ctx.attr(node, 'slug') ?? '';
    const name = ctx.attr(node, 'name') ?? slug;
    const id = `${ctx.lang === 'es' ? 'es/' : ''}reference/errata/${slug}`;
    const file = join(CONTENT_DIR, `${id}.md`);
    if (!slug || !existsSync(file)) {
      ctx.issue(node, `the errata index lists "${slug}", but there is no page ${id}.md: regenerate the errata pages with make site-reports`);
      return '';
    }
    const headings = entryHeadings(readCommittedText(file));
    if (headings.length === 0) ctx.issue(node, `${id}.md has no entry heading (##) to list`);
    const title = `${ctx.heading(3, `[${bracketText(name)}](${ctx.site.url(`/${id}/`)})`)} (${COUNT[ctx.lang](headings.length)})`;
    return [title, headings.map((heading) => `- ${heading}`).join('\n')].filter(Boolean).join('\n\n');
  },
});
