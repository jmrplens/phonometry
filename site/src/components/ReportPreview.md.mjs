/**
 * ReportPreview: a labelled link to the PDF fiche, with what it shows.
 *
 * Kept: the report kind (`title`), the PDF and the description written for a
 * reader who cannot see the preview, which is the content of the fiche in
 * words; then the visible caption as a paragraph of its own.
 *
 * Agent copy: the PDF this site serves (src/lib/media.mjs). GitHub edition:
 * the preview image linked to the PDF on raw.githubusercontent, the form
 * GitHub renders, with the title and description as its alt.
 *
 * Dropped: the preview's pixel size, display width and `id`, which lay out
 * and tell apart the thumbnails on the page.
 */
import { mediaUrl } from '../lib/media.mjs';
import { bracketText, line } from '../lib/agent-md/markdown-table.mjs';
import { markdownFor } from '../lib/agent-md/types.mjs';

/** The fiches as ReportPreview.astro names them. */
const REPORTS = 'https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports';

const LABEL = { en: 'Report', es: 'Informe' };

export default markdownFor({
  tag: 'ReportPreview',
  props: ['name', 'title', 'description', 'width', 'height', 'displayWidth', 'caption', 'id'],
  toMarkdown(node, ctx) {
    const name = ctx.attr(node, 'name');
    const title = line(ctx.attr(node, 'title'));
    const description = line(ctx.attr(node, 'description'));
    if (!name || !title) {
      ctx.issue(node, 'ReportPreview needs a name and a title');
      return '';
    }
    const caption = line(ctx.attr(node, 'caption'));
    let entry;
    if (ctx.flavour === 'github') {
      const alt = description ? `${title}: ${description}` : title;
      entry = `[![${bracketText(alt)}](${REPORTS}/${name}.webp)](${REPORTS}/${name}.pdf)`;
    } else {
      const pdf = mediaUrl(`${REPORTS}/${name}.pdf`, `${ctx.site.origin}${ctx.site.base}`);
      const lead = `**${LABEL[ctx.lang]}:** [${bracketText(title)}](${pdf})`;
      entry = description ? `${lead}: ${description}` : lead;
    }
    return caption ? `${entry}\n\n${caption}` : entry;
  },
});
