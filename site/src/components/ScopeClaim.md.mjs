/**
 * ScopeClaim: one list item, its legend in bold, then the claim.
 *
 * Kept: the claim's prose whole (links, maths, code, further paragraphs or a
 * list), and the side of the boundary it is on. The page prints the `label`
 * the author wrote in the panel's gutter, so the copy prints it too; where a
 * panel omits it because every entry shares one state, the copy names the
 * state anyway, in the page's language, because a reader of the copy sees the
 * entry without the panel around it and `status` is the one thing that says
 * which side of the boundary the entry is on.
 *
 * Dropped: nothing the page shows. `data-coverage` is the machine form of
 * `status`, which the legend already states.
 */
import { listItem, line } from '../lib/agent-md/markdown-table.mjs';
import { markdownFor } from '../lib/agent-md/types.mjs';

/** The state, in words, for an entry the page prints without a legend. */
const STATUS = {
  en: { covered: 'Covered', 'not-covered': 'Not covered' },
  es: { covered: 'Cubierto', 'not-covered': 'No cubierto' },
};

export default markdownFor({
  tag: 'ScopeClaim',
  props: ['status', 'label'],
  toMarkdown(node, ctx) {
    const status = ctx.attr(node, 'status') ?? '';
    const words = STATUS[ctx.lang];
    if (!Object.hasOwn(words, status)) {
      ctx.issue(node, `ScopeClaim needs status="covered" or status="not-covered", got ${JSON.stringify(status)}`);
    }
    const legend = line(ctx.attr(node, 'label')) || words[status] || '';
    const lead = legend ? `**${legend.replace(/[.:]$/u, '')}.**` : '';
    return listItem(lead, ctx.body(node)).replace(/^- {2}/u, '- ');
  },
});
