/**
 * CatalogueFinder: dropped on purpose.
 *
 * It is a picker: a select of catalogues, a filter by material and a filter
 * by published table, all driving the rows that the Catalogues component
 * prints on the same page. The rows are what a reader of the copy needs, and
 * the Catalogues writer writes all of them; the controls that narrow them on
 * a screen have no meaning in a text a reader can search.
 */
import { markdownFor } from '../lib/agent-md/types.mjs';

export default markdownFor({
  tag: 'CatalogueFinder',
  props: ['lang'],
  toMarkdown: () => '',
});
