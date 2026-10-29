/**
 * Root-relative links made absolute.
 *
 * The site's pages link each other as `/phonometry/...`, which the browser
 * resolves against the page. A Markdown copy is read away from the site, in a
 * chat context, a corpus or a file on disk, where `](/phonometry/...)`
 * resolves nowhere. Every URL a writer composes is already absolute; this
 * pass covers the links the author wrote in the page's own Markdown.
 *
 * The finished copy is parsed and only the destinations of `link`, `image`
 * and `definition` nodes are rewritten, by offset. A scanner over lines
 * cannot do this safely: an inline code span may open on one line and close
 * on the next, and from inside it `](/` is sample text, not a link (the API
 * page of `tone_audibility` has exactly that). On the tree, code and TeX are
 * nodes of their own and carry no links. Protocol-relative `//host` URLs,
 * fragments and relative paths are left as written.
 *
 * @module
 */
import { parse } from './processor.mjs';

const LINK_TYPES = new Set(['link', 'image', 'definition']);

/**
 * @param {string} text
 * @returns {string}
 */
const escapeRegExp = (text) => text.replaceAll(/[.*+?^${}()|[\]\\]/gu, String.raw`\$&`);

/**
 * Every root-relative link in a Markdown document, made absolute.
 *
 * @param {string} markdown
 * @param {string} origin  Site origin, such as `https://docs.jmrp.io`; a
 *   trailing slash is tolerated.
 * @returns {string}
 */
export function absolutizeRootLinks(markdown, origin) {
  let root = origin;
  while (root.endsWith('/')) root = root.slice(0, -1);
  const tree = parse(markdown, { mdx: false });
  /** @type {number[]} */
  const inserts = [];
  const visit = (node) => {
    if (LINK_TYPES.has(node.type) && /^\/(?!\/)/u.test(node.url ?? '') && node.position) {
      const start = node.position.start.offset;
      const end = node.position.end.offset;
      // The destination follows the text: `](`, `](<` for a link or image,
      // `]:` and spacing for a definition. The last such occurrence in the
      // node is the destination; a title, if any, comes after it.
      const pattern = new RegExp(String.raw`(\]\(\s*<?|\]:\s*<?)(${escapeRegExp(node.url)})`, 'gu');
      let found;
      for (const match of markdown.slice(start, end).matchAll(pattern)) found = match;
      if (found?.index !== undefined) inserts.push(start + found.index + found[1].length);
    }
    for (const child of node.children ?? []) visit(child);
  };
  visit(tree);
  let out = markdown;
  for (const at of inserts.sort((a, b) => b - a)) out = `${out.slice(0, at)}${root}${out.slice(at)}`;
  return out;
}
