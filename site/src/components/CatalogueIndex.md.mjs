/**
 * CatalogueIndex: every published catalogue, as the overview lists it.
 *
 * Kept: one list item per catalogue page, in the sidebar's order, with its
 * label linked to the page, how many rows it holds and the line that says
 * what they are (the page's own description). The list is worked out by
 * src/lib/catalogue-page-list.mjs, the function the component's list comes
 * from, here fed the pages read from disk rather than the build's collection,
 * so the copy cannot list a page the overview does not, or count its rows
 * differently.
 *
 * Dropped: nothing the page shows.
 */
import { readEntries } from '../lib/agent-md/content.mjs';
import { literalText } from '../lib/agent-md/markdown-table.mjs';
import { markdownFor } from '../lib/agent-md/types.mjs';
import { catalogueIndex, rowCount } from '../lib/catalogue-page-list.mjs';

/**
 * One item of the list: the catalogue's label linked to its page, how many
 * rows it holds, then what they are, the label and the description written as
 * the overview prints them ({@link literalText}).
 *
 * @param {{ label: string, url: string, count: string, description: string }} catalogue
 * @returns {string}
 */
export function catalogueItem({ label, url, count, description }) {
  const lead = `- [${literalText(label)}](${url}) (${count})`;
  const what = literalText(description);
  return what ? `${lead}: ${what}` : lead;
}

export default markdownFor({
  tag: 'CatalogueIndex',
  props: ['lang'],
  toMarkdown(node, ctx) {
    const lang = ctx.attr(node, 'lang') === 'es' ? 'es' : 'en';
    if (lang !== ctx.lang) ctx.issue(node, `CatalogueIndex lang="${lang}" on a page in ${ctx.lang}`);
    let pages;
    try {
      pages = catalogueIndex(lang, readEntries(`${lang === 'es' ? 'es/' : ''}reference/catalogues`));
    } catch (error) {
      ctx.issue(node, error.message);
      return '';
    }
    return pages
      .map((page) =>
        catalogueItem({ label: page.label, url: ctx.site.url(page.href), count: rowCount(page.rows, lang), description: page.description }),
      )
      .join('\n');
  },
});
