/**
 * SeeAlso: kept whole, as the authored Markdown inside it.
 *
 * The component only draws a box around its children: the `## See also`
 * heading, the sentence that sometimes introduces the list, and the list of
 * links all stay Markdown inside the element, so the copy is those children.
 *
 * Dropped: the `<nav>` landmark and the heading id it points at, which are
 * the page's accessibility wiring, with nothing a reader of the copy needs.
 * The component declares no props.
 *
 * Checked on the way: the panel opens with its heading, `## See also` on an
 * English page and `## Véase también` on a Spanish one. SeeAlso.astro names
 * its landmark after that heading's id (its HEADING_ID), which it can only
 * know for those two words; a panel headed otherwise gets another id, and
 * the landmark is left without a name while the page looks the same. Three
 * Spanish guides headed theirs "Ver también" that way.
 */
import { markdownFor } from '../lib/agent-md/types.mjs';

/** The heading SeeAlso.astro takes the landmark's name from, in each language. */
export const HEADING = Object.freeze({ en: 'See also', es: 'Véase también' });

export default markdownFor({
  tag: 'SeeAlso',
  props: [],
  toMarkdown(node, ctx) {
    const expected = HEADING[ctx.lang];
    const first = node.children?.[0];
    const heading = first?.type === 'heading' ? `${'#'.repeat(first.depth ?? 0)} ${ctx.text(first)}` : undefined;
    if (heading !== `## ${expected}`) {
      ctx.issue(
        first ?? node,
        `the See also panel opens with ${heading ? `"${heading}"` : 'no heading'}, not "## ${expected}": ` +
          'SeeAlso.astro names its landmark after the id of that heading, so the landmark is left without a name',
      );
    }
    return ctx.body(node);
  },
});
