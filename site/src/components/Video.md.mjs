/**
 * Video: a labelled link to the clip, with what it shows.
 *
 * A clip cannot be watched from text, so what is kept is what can still be
 * read or followed: the title, the address of the clip and the description
 * written for a reader who cannot see it, then the visible caption as a
 * paragraph of its own.
 *
 * Agent copy: the clip this site serves (src/lib/media.mjs), in the page's
 * language. GitHub edition: the clip in jmrplens/phonometry-assets at the
 * commit `assets.lock` pins, the one the site was built against, rather than
 * whatever that repository's main holds by the time someone reads the page.
 *
 * Dropped: the dark variant (the same clip in another palette), the size and
 * display width, the poster, and `id`, which only keeps two players' ids
 * apart on one page.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { mediaUrl } from '../lib/media.mjs';
import { lineStart, literalText } from '../lib/agent-md/markdown-table.mjs';
import { REPO_DIR } from '../lib/agent-md/render.mjs';
import { markdownFor } from '../lib/agent-md/types.mjs';

/** The clips as Video.astro names them. */
const IMAGES = 'https://raw.githubusercontent.com/jmrplens/phonometry-assets/main/images';

const LABEL = { en: 'Video', es: 'Vídeo' };

/** The phonometry-assets commit the site's clips come from. */
const lockedCommit = () => readFileSync(join(REPO_DIR, 'assets.lock'), 'utf8').trim().split(/\s+/u)[0];

export default markdownFor({
  tag: 'Video',
  props: ['name', 'title', 'description', 'width', 'height', 'displayWidth', 'caption', 'id'],
  toMarkdown(node, ctx) {
    const name = ctx.attr(node, 'name');
    const title = literalText(ctx.attr(node, 'title'));
    const description = literalText(ctx.attr(node, 'description'));
    if (!name || !title) {
      ctx.issue(node, 'Video needs a name and a title');
      return '';
    }
    const file = `${name}${ctx.lang === 'es' ? '_es' : ''}.webm`;
    const url =
      ctx.flavour === 'github'
        ? `https://raw.githubusercontent.com/jmrplens/phonometry-assets/${lockedCommit()}/images/${file}`
        : mediaUrl(`${IMAGES}/${file}`, `${ctx.site.origin}${ctx.site.base}`);
    const lead = `**${LABEL[ctx.lang]}:** [${title}](${url})`;
    const caption = lineStart(literalText(ctx.attr(node, 'caption')));
    const entry = description ? `${lead}: ${description}` : lead;
    return caption ? `${entry}\n\n${caption}` : entry;
  },
});
