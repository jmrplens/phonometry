/**
 * ReportIndex: every fiche, grouped by area, as the page lists them.
 *
 * Kept: per area, a heading with its name and fiche count; per fiche, its
 * title linked to the PDF, the sentence its guide writes about it, and the
 * guide that shows it. The rows come from src/data/reports.mjs and the words
 * around them from src/data/report-index-copy.mjs, the two modules the
 * component reads, so the copy cannot list a fiche the page does not.
 *
 * The PDF link is the one the page uses. Dropped: nothing the page shows.
 */
import { reportsByArea, reportsByAreaEs } from '../data/reports.mjs';
import { COPY, areaName, sortedAreas } from '../data/report-index-copy.mjs';
import { bracketText, line } from '../lib/agent-md/markdown-table.mjs';
import { markdownFor } from '../lib/agent-md/types.mjs';

/** Where ReportIndex.astro links each fiche. */
const RAW = 'https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports';

/** A sentence, closed with a full stop when it has no closing mark. */
const sentence = (text) => (/[.!?]$/u.test(text) ? text : `${text}.`);

export default markdownFor({
  tag: 'ReportIndex',
  props: ['lang'],
  toMarkdown(node, ctx) {
    const lang = ctx.attr(node, 'lang') === 'es' ? 'es' : 'en';
    if (lang !== ctx.lang) ctx.issue(node, `ReportIndex lang="${lang}" on a page in ${ctx.lang}`);
    const copy = COPY[lang];
    const groups = lang === 'es' ? reportsByAreaEs : reportsByArea;
    return sortedAreas(groups, lang)
      .map(([area, list]) => {
        const items = list.map((report) => {
          const what = line(report.description);
          const link = `[${bracketText(report.title)}](${RAW}/${report.name}.pdf)`;
          const where = `${copy.source} [${bracketText(report.pageTitle)}](${report.page}).`;
          return what ? `- ${link}: ${sentence(what)} ${where}` : `- ${link}. ${where}`;
        });
        return `${ctx.heading(2, `${areaName(area, lang)} (${copy.count(list.length)})`)}\n\n${items.join('\n')}`;
      })
      .join('\n\n');
  },
});
