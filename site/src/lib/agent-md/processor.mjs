/**
 * The parser every Markdown copy of a page is read with.
 *
 * It has to read a page the way the site's own build reads it, or the copy and
 * the page would disagree about what the source says. The site compiles its
 * `.mdx` pages with MDX (remark-mdx), GitHub-flavoured Markdown, remark-math
 * (`astro.config.mjs`, `markdown.remarkPlugins`) and the directives Starlight
 * turns into asides, so the same micromark extensions are loaded here, in the
 * same order Astro loads them. Without remark-math, the braces of
 * `$L_{p}$` would be read as an MDX expression, and TeX that is not valid
 * JavaScript would stop the parse; with it, `math` and `inlineMath` are nodes
 * the renderer keeps byte for byte.
 *
 * `.md` pages are compiled by Astro without MDX, so they are parsed without it
 * here too: in a `.md` file `<` and `{` are text, and raw HTML is an `html`
 * node.
 *
 * Frontmatter is parsed as a `yaml` node at the head of the tree, so every
 * position the renderer reports is a line of the file as it is on disk.
 *
 * @module
 */
import remarkDirective from 'remark-directive';
import remarkFrontmatter from 'remark-frontmatter';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkMdx from 'remark-mdx';
import remarkParse from 'remark-parse';
import { unified } from 'unified';
import { parse as parseYaml } from 'yaml';

const MDX = unified()
  .use(remarkParse)
  .use(remarkFrontmatter, ['yaml'])
  .use(remarkMdx)
  .use(remarkGfm)
  .use(remarkMath)
  .use(remarkDirective)
  .freeze();

const MARKDOWN = unified()
  .use(remarkParse)
  .use(remarkFrontmatter, ['yaml'])
  .use(remarkGfm)
  .use(remarkMath)
  .use(remarkDirective)
  .freeze();

/**
 * Whether a content file is MDX, from its name.
 *
 * @param {string} file
 * @returns {boolean}
 */
export const isMdx = (file) => file.endsWith('.mdx');

/**
 * Parses one page.
 *
 * @param {string} source  The file as it is on disk, frontmatter included.
 * @param {{ mdx?: boolean }} [options]  `mdx: false` for a `.md` page.
 * @returns {import('./types.mjs').MdNode}  The mdast root.
 * @throws {Error}  When the source does not parse, as the site build would.
 */
export function parse(source, { mdx = true } = {}) {
  return /** @type {import('./types.mjs').MdNode} */ ((mdx ? MDX : MARKDOWN).parse(source));
}

/**
 * The page's frontmatter, as data.
 *
 * @param {import('./types.mjs').MdNode} tree  A tree from {@link parse}.
 * @returns {Record<string, unknown>}  The parsed YAML, or `{}` without one.
 */
export function frontmatterOf(tree) {
  const head = tree.children?.[0];
  if (head?.type !== 'yaml') return {};
  const data = parseYaml(head.value ?? '');
  return data && typeof data === 'object' ? /** @type {Record<string, unknown>} */ (data) : {};
}
