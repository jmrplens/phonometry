/**
 * Scope: kept whole, as the claims inside it.
 *
 * The panel is a list whose every entry is a ScopeClaim, and the section
 * heading and any framing sentence stay authored Markdown above it, so the
 * copy already carries them. What this writer returns is the claims, each
 * written by ScopeClaim.md.mjs as a list item. The optional `id` is an anchor
 * for links into the page, which a Markdown copy has no use for: dropped.
 */
import { markdownFor } from '../lib/agent-md/types.mjs';

export default markdownFor({
  tag: 'Scope',
  props: ['id'],
  toMarkdown: (node, ctx) => ctx.body(node),
});
