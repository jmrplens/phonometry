// Shared fixtures for the renderer's tests: a renderer call that returns the
// issues with the Markdown, and stand-in writers small enough to read.
import { markdownFor } from '../types.mjs';
import { parse } from '../processor.mjs';
import { renderTree } from '../render.mjs';

/**
 * Renders a source string and returns the Markdown and the issues.
 *
 * @param {string} source
 * @param {{
 *   registry?: Map<string, import('../types.mjs').ComponentMarkdown>,
 *   lang?: 'en' | 'es',
 *   flavour?: 'agent' | 'github',
 *   scope?: Map<string, unknown>,
 *   mdx?: boolean,
 * }} [options]
 */
export function render(source, { registry = new Map(), lang = 'en', flavour = 'agent', scope = new Map(), mdx = true } = {}) {
  const issues = [];
  const tree = parse(source, { mdx });
  const markdown = renderTree(tree, source, { registry, lang, flavour, scope, issues });
  return { markdown, issues };
}

/** A registry from writer specs. */
export const registryOf = (...specs) => new Map(specs.map((spec) => [spec.tag, spec]));

/** A writer that wraps its children in brackets, declaring `kind`. */
export const Box = markdownFor({
  tag: 'Box',
  props: ['kind', 'count'],
  toMarkdown: (node, ctx) => `[${ctx.attr(node, 'kind') ?? 'box'}]\n\n${ctx.body(node)}`,
});

/** A writer that prints the value of its `value` prop as the renderer reads it. */
export const Show = markdownFor({
  tag: 'Show',
  props: ['value'],
  toMarkdown: (node, ctx) => JSON.stringify(ctx.expr(node, 'value')),
});
