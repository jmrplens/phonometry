/**
 * CatalogueRouter: dropped on purpose.
 *
 * It renders nothing: it is a script that sends a link written against the
 * old single catalogues page (`#porous-materials`) to the page that catalogue
 * has now. A fragment means nothing in a Markdown copy, which lists every
 * catalogue page by its own address.
 */
import { markdownFor } from '../lib/agent-md/types.mjs';

export default markdownFor({
  tag: 'CatalogueRouter',
  props: ['lang'],
  toMarkdown: () => '',
});
