/**
 * ErrataRouter: dropped on purpose.
 *
 * It renders nothing: it is a script that sends a link written against the
 * old single errata page (`/reference/errata/#<entry>`) to the family page
 * the entry moved to. A fragment means nothing in a Markdown copy, and the
 * family list the index prints already links every entry where it lives.
 */
import { markdownFor } from '../lib/agent-md/types.mjs';

export default markdownFor({
  tag: 'ErrataRouter',
  props: [],
  toMarkdown: () => '',
});
