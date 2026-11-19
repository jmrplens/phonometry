/**
 * ThemeImage: a real image, the figure in the page's language.
 *
 * Kept: the figure and its `alt`, the text written for a reader who cannot
 * see it. The caption is the italic paragraph the author writes after the
 * element, already Markdown, so the copy carries it without help.
 *
 * Agent copy: `![alt](https://phonometry.dev/media/<figure>.svg)`,
 * the copy this site serves (src/lib/media.mjs), never raw.githubusercontent,
 * which is not a host for assets. The `_es` figure on a Spanish page, as the
 * component picks it. Only the light palette: the dark one is the same
 * drawing for another theme, and naming both would describe the site's
 * styling, not the content.
 *
 * GitHub edition: the `<picture>` GitHub renders, with the dark variant as a
 * `prefers-color-scheme` source and the authored width, the absolute
 * raw.githubusercontent URLs GitHub can resolve on its own.
 *
 * Dropped: `loading` (when the browser fetches the figure).
 */
import { mediaUrl } from '../lib/media.mjs';
import { htmlAttribute, line, literalText } from '../lib/agent-md/markdown-table.mjs';
import { markdownFor } from '../lib/agent-md/types.mjs';

/** `figure.svg` with a suffix before the extension, as the component does. */
const suffixed = (src, suffix) => src.replace(/(\.[A-Za-z0-9]+)$/u, `${suffix}$1`);

export default markdownFor({
  tag: 'ThemeImage',
  props: ['src', 'alt', 'width', 'loading'],
  toMarkdown(node, ctx) {
    const src = ctx.attr(node, 'src');
    const alt = line(ctx.attr(node, 'alt'));
    if (!src) {
      ctx.issue(node, 'ThemeImage without a src');
      return '';
    }
    if (!alt) ctx.issue(node, `ThemeImage without an alt (src: ${src})`);
    const localised = ctx.lang === 'es' ? suffixed(src, '_es') : src;
    if (ctx.flavour === 'github') {
      const width = ctx.attr(node, 'width');
      const dark = suffixed(localised, '_dark');
      return (
        `<picture><source media="(prefers-color-scheme: dark)" srcset="${dark}">` +
        `<img src="${localised}" alt="${htmlAttribute(alt)}"${width ? ` width="${htmlAttribute(width)}"` : ''}></picture>`
      );
    }
    return `![${literalText(alt)}](${mediaUrl(localised, `${ctx.site.origin}${ctx.site.base}`)})`;
  },
});
