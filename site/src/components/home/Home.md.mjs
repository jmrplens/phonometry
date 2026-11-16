/**
 * Home: the landing page, block by block, in the page's order.
 *
 * The landing is a component layout rather than prose: everything it prints
 * comes from the object src/data/home.ts holds for its language, which the
 * page passes as `content`, and from the hero in the page's frontmatter. The
 * writer reads the same two sources, so the copy says what the page says.
 *
 * Kept, in order: the hero's tagline and its actions as links; the four
 * numbers of the readout under the readout's own name; "What this is" with
 * its paragraphs (their inline HTML written as Markdown by the renderer's own
 * rules), who it is for and what it is not; the three demonstrations, with
 * their code as fenced blocks and the clip, the figure and the fiche written
 * by the Video, ThemeImage and ReportPreview writers, as a guide's would be;
 * the coverage table, one row per area with its link, summary and the
 * standards implemented there; the three starting steps with the install
 * line and their links; and a last line naming llms.txt, the index of the
 * Markdown copies.
 *
 * Dropped on purpose: the area icons and the step numbers drawn beside the
 * headings, which are decoration (the steps are a numbered list instead).
 */
import { line, table } from '../../lib/agent-md/markdown-table.mjs';
import { markdownFor } from '../../lib/agent-md/types.mjs';
import ReportPreview from '../ReportPreview.md.mjs';
import ThemeImage from '../ThemeImage.md.mjs';
import Video from '../Video.md.mjs';

/** The figure Home.astro shows beside the spectrum demonstration. */
const SPECTRUM = 'https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_response_fraction_3.svg';

/** The last line, which the page carries in its head rather than its body. */
const LLMS = {
  en: (url) => `For language models: [llms.txt](${url}), the index of every page of this documentation as Markdown.`,
  es: (url) => `Para modelos de lenguaje: [llms.txt](${url}), el índice de todas las páginas de esta documentación en Markdown (en inglés).`,
};

/**
 * An element as the page would write it, for a writer that reads attributes.
 *
 * @param {string} name
 * @param {Record<string, string | undefined>} props
 */
const element = (name, props) => ({
  type: 'mdxJsxFlowElement',
  name,
  attributes: Object.entries(props)
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => ({ type: 'mdxJsxAttribute', name: key, value })),
  children: [],
});

/**
 * A fenced block whose fence no line of the code can close: its backticks
 * outnumber the longest run of them anywhere in the code, as `codeSpan` sizes
 * an inline span.
 */
const fence = (code, lang) => {
  const longest = Math.max(2, ...(code.match(/`+/gu) ?? []).map((run) => run.length));
  const marks = '`'.repeat(longest + 1);
  return `${marks}${lang}\n${code.replace(/\n+$/u, '')}\n${marks}`;
};

/** Each line of a block indented under a numbered list item. */
const indent = (text) =>
  text
    .split('\n')
    .map((one) => (one.trim() === '' ? '' : `   ${one}`))
    .join('\n');

export default markdownFor({
  tag: 'Home',
  props: ['content'],
  toMarkdown(node, ctx) {
    const content = /** @type {import('../../data/home.ts').HomeContent | undefined} */ (ctx.expr(node, 'content'));
    if (!content || typeof content !== 'object') {
      ctx.issue(node, 'Home needs content={en} or content={es} from src/data/home.ts');
      return '';
    }
    const blocks = [];
    const hero = /** @type {{ tagline?: string, actions?: { text: string, link: string }[] }} */ (
      ctx.frontmatter.hero ?? {}
    );
    if (hero.tagline) blocks.push(line(hero.tagline));
    if (hero.actions?.length) {
      blocks.push(hero.actions.map((action) => `- [${line(action.text)}](${action.link})`).join('\n'));
    }

    blocks.push(
      `**${line(content.statsLabel)}**`,
      content.stats
        .map((stat) => `- **${stat.value}** ${stat.href ? `[${line(stat.label)}](${stat.href})` : line(stat.label)}`)
        .join('\n'),
    );

    const { what, who, honest, proof, coverage, start } = content;
    blocks.push(ctx.heading(2, what.title), ...what.body.map((paragraph) => ctx.markdown(paragraph)));
    blocks.push(ctx.heading(3, who.title), who.items.map((item) => `- ${line(item)}`).join('\n'));
    blocks.push(ctx.heading(3, honest.title), honest.items.map((item) => `- ${line(item)}`).join('\n'));

    blocks.push(ctx.heading(2, proof.title), line(proof.lead));
    if (proof.banner) {
      blocks.push(
        Video.toMarkdown(
          element('Video', {
            name: 'anim_fdtd_pillar_hall',
            title: proof.banner.title,
            description: proof.banner.description,
            caption: proof.banner.caption,
          }),
          ctx,
        ),
      );
    }
    blocks.push(
      ctx.heading(3, proof.spectrum.title),
      line(proof.spectrum.note),
      fence(proof.spectrum.code, 'python'),
      ThemeImage.toMarkdown(element('ThemeImage', { src: SPECTRUM, alt: proof.spectrum.alt }), ctx),
      line(proof.spectrum.caption),
    );
    blocks.push(
      ctx.heading(3, proof.fiche.title),
      line(proof.fiche.note),
      fence(proof.fiche.code, 'python'),
      ReportPreview.toMarkdown(
        element('ReportPreview', {
          name: 'iso717_airborne_example',
          title: proof.fiche.linkTitle,
          description: proof.fiche.description,
          caption: proof.fiche.caption,
        }),
        ctx,
      ),
    );

    blocks.push(
      ctx.heading(2, coverage.title),
      line(coverage.lead),
      table(
        coverage.headers,
        coverage.areas.map((area) => [`[${line(area.name)}](${area.href}): ${line(area.summary)}`, area.standards.length > 0 ? area.standards.join(', ') : coverage.noStandard]),
      ),
    );

    const steps = start.steps.map((step, i) => {
      const parts = [line(step.body)];
      if (step.code) parts.push(fence(step.code, 'bash'));
      const links = [`[${line(step.linkText)}](${step.href})`];
      if (step.also) links.push(`[${line(step.also.linkText)}](${step.also.href})`);
      parts.push(links.join(' · '));
      return `${i + 1}. **${line(step.title)}.** ${indent(parts.join('\n\n')).trimStart()}`;
    });
    blocks.push(ctx.heading(2, start.title), line(start.lead), steps.join('\n'));

    blocks.push(LLMS[ctx.lang](ctx.site.url('/llms.txt')));
    return blocks.filter((block) => block.trim() !== '').join('\n\n');
  },
});
