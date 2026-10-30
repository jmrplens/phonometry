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
import { bracketText, plainText } from '../lib/agent-md/markdown-table.mjs';
import { markdownFor } from '../lib/agent-md/types.mjs';
import { catalogueIndex, rowCount } from '../lib/catalogue-page-list.mjs';

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
      .map((page) => {
        const what = plainText(page.description);
        const lead = `- [${bracketText(page.label)}](${ctx.site.url(page.href)}) (${rowCount(page.rows, lang)})`;
        return what ? `${lead}: ${what}` : lead;
      })
      .join('\n');
  },
});
