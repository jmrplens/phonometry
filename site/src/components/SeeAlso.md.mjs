/**
 * SeeAlso: kept whole, as the authored Markdown inside it.
 *
 * The component only draws a box around its children: the `## See also`
 * heading, the sentence that sometimes introduces the list, and the list of
 * links all stay Markdown inside the element, so the copy is those children.
 * The component declares no props: the `<nav>` landmark and the heading id it
 * points at are the page's accessibility wiring, with nothing a reader of the
 * copy needs.
 */
import { markdownFor } from '../lib/agent-md/types.mjs';

export default markdownFor({
  tag: 'SeeAlso',
  props: [],
  toMarkdown: (node, ctx) => ctx.body(node),
});
