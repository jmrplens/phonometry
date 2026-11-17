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
 * What every root-relative destination is preceded by: the `](` of an inline
 * link or image, or the `]:` of a definition, then optional spacing with at
 * most one line break (and the `>` of the block quotes the next line sits in),
 * an optional `<`, and a single `/`, or an `&` that may open a character
 * reference to one.
 *
 * A copy without it holds no link to rewrite, and is returned without being
 * parsed. That is not only quicker: the GFM table extension resolves every
 * table of a document through one list of edits that it searches from the
 * start for each new one, so its cost grows with the square of the document's
 * table rows. The conformance report, all tables and no root-relative link,
 * cost more to parse for nothing than every other page together.
 */
const ROOT_DESTINATION = /\](?:\(|:)[ \t]*(?:\r?\n(?:[ \t]*>)*[ \t]*)?<?(?:\/(?!\/)|&)/u;

/**
 * What every fragment destination is preceded by, in the same forms as
 * {@link ROOT_DESTINATION}: an inline link's `](#`, a reference definition's
 * `]: #`, either with spacing, a line break or a `<` before the `#`, or an
 * `&` that may open a character reference to it (`&#35;`).
 */
const FRAGMENT_DESTINATION = /\](?:\(|:)[ \t]*(?:\r?\n(?:[ \t]*>)*[ \t]*)?<?(?:#|&)/u;

/**
 * The destination as the source writes it, from just after the `](` of a link
 * or image or the `]:` of a definition: the spacing (at most one line break)
 * skipped, then either `<...>` up to its closing bracket or a run without
 * spacing whose parentheses balance, a backslash keeping the character after
 * it. `start` and `end` bound the text inside the brackets of the `<...>`
 * form, which is the part a rewrite replaces.
 *
 * @param {string} text
 * @param {number} from
 * @returns {{ start: number, end: number, angle: boolean } | undefined}
 */
function writtenDestination(text, from) {
  const lead = /^[ \t]*(?:\r?\n(?:[ \t]*>)*[ \t]*)?/u.exec(text.slice(from));
  const at = from + (lead ? lead[0].length : 0);
  if (text[at] === '<') {
    for (let i = at + 1; i < text.length; i += 1) {
      if (text[i] === '\\') i += 1;
      else if (text[i] === '>') return { start: at + 1, end: i, angle: true };
      else if (text[i] === '\n' || text[i] === '<') return undefined;
    }
    return undefined;
  }
  let depth = 0;
  let end = at;
  for (; end < text.length; end += 1) {
    const char = text[end];
    if (char === '\\' && end + 1 < text.length) end += 1;
    else if (/\s/u.test(char)) break;
    else if (char === '(') depth += 1;
    else if (char === ')') {
      if (depth === 0) break;
      depth -= 1;
    }
  }
  return end > at ? { start: at, end, angle: false } : undefined;
}

/** @type {Map<string, string | undefined>} */
const DECODED = new Map();

/**
 * What the parser makes of a destination written as the source writes it:
 * its character references and backslash escapes resolved, exactly as the
 * node's `url` was. The same parser does it, so the two cannot disagree.
 *
 * @param {string} written
 * @param {boolean} angle
 * @returns {string | undefined}
 */
function decodedDestination(written, angle) {
  const key = `${angle ? '<' : ' '}${written}`;
  if (!DECODED.has(key)) {
    const probe = parse(`[x](${angle ? `<${written}>` : written})\n`, { mdx: false });
    const link = probe.children?.[0]?.children?.[0];
    DECODED.set(key, link?.type === 'link' ? link.url : undefined);
  }
  return DECODED.get(key);
}

/**
 * The destination of every `link` and `definition` node (and of every `image`
 * node too when `images` is set) whose URL `wanted` accepts: where its written
 * text starts and ends in the document, and the URL it decodes to.
 *
 * Each `](` of the node (each `]:` of a definition) is read, and the last
 * whose destination decodes to the node's URL is the one; a title, if any,
 * comes after it. A destination with a character reference or an escape
 * decodes to text the source does not hold, so a search for the URL itself
 * would miss it and leave the link as it was without a word. A destination
 * that cannot be found is refused instead.
 *
 * @param {string} markdown
 * @param {(url: string) => boolean} wanted
 * @param {{ images?: boolean }} [options]
 * @returns {{ start: number, end: number, url: string }[]}
 */
function destinations(markdown, wanted, { images = true } = {}) {
  const types = images ? LINK_TYPES : new Set(['link', 'definition']);
  const tree = parse(markdown, { mdx: false });
  /** @type {{ start: number, end: number, url: string }[]} */
  const found = [];
  const visit = (node) => {
    if (types.has(node.type) && wanted(node.url ?? '') && node.position) {
      const start = node.position.start.offset;
      const text = markdown.slice(start, node.position.end.offset);
      const opener = node.type === 'definition' ? /\]:/gu : /\]\(/gu;
      const openers = [...text.matchAll(opener)];
      // An autolink (`<https://...>`) and a bare address have no destination
      // apart from their text, which is what the reader sees: left as written.
      if (openers.length === 0 && node.type === 'link') return;
      // The destination comes right after the label and before any title, so
      // the first opener past the label that decodes to the URL is the one; an
      // opener inside a title (`"see ](/p)"`) comes later and is never taken.
      const labelEnd = node.children?.at(-1)?.position?.end.offset;
      let match;
      for (const one of openers) {
        if (labelEnd !== undefined && start + one.index < labelEnd) continue;
        const written = writtenDestination(text, one.index + 2);
        if (written && decodedDestination(text.slice(written.start, written.end), written.angle) === node.url) {
          match = written;
          break;
        }
      }
      if (!match) {
        const line = node.position.start.line;
        throw new Error(`line ${line}: the destination ${JSON.stringify(node.url)} is not found where its link is written`);
      }
      found.push({ start: start + match.start, end: start + match.end, url: node.url });
    }
    for (const child of node.children ?? []) visit(child);
  };
  visit(tree);
  return found;
}

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
  if (!ROOT_DESTINATION.test(markdown)) return markdown;
  let out = markdown;
  const found = destinations(markdown, (url) => /^\/(?!\/)/u.test(url));
  for (const { start } of found.sort((a, b) => b.start - a.start)) out = `${out.slice(0, start)}${root}${out.slice(start)}`;
  return out;
}

/**
 * Every link and link definition whose destination `rewrite` gives a new
 * one, rewritten by offset; images are left alone, since a picture is not a
 * page a reader moves to. The same parse as {@link absolutizeRootLinks}, so a
 * URL inside code or TeX is never touched.
 *
 * @param {string} markdown
 * @param {(url: string) => string | undefined} rewrite  The new destination,
 *   or nothing to leave the link as it is.
 * @param {string} [hint]  Text every destination worth rewriting contains; a
 *   document without it is returned without being parsed.
 * @returns {string}
 */
export function rewriteLinks(markdown, rewrite, hint) {
  if (hint !== undefined && !markdown.includes(hint)) return markdown;
  const found = destinations(markdown, (url) => rewrite(url) !== undefined, { images: false });
  let out = markdown;
  for (const { start, end, url } of found.sort((a, b) => b.start - a.start)) {
    out = `${out.slice(0, start)}${rewrite(url)}${out.slice(end)}`;
  }
  return out;
}

/**
 * Every fragment link to one of `anchors`, ids the copy leaves out, sent to
 * the page itself: `[x](#old-id)` becomes `[x](<page>#old-id)`, and so does a
 * reference definition `[x]: #old-id` or an `<#old-id>` destination. The copy is
 * parsed, as {@link absolutizeRootLinks} parses it, so a fragment written in
 * code is left alone; a fragment to any other id is left as written.
 *
 * @param {string} markdown
 * @param {ReadonlySet<string>} anchors
 * @param {string} pageUrl  The page's address, ending in `/`.
 * @returns {string}
 */
export function pointDroppedAnchors(markdown, anchors, pageUrl) {
  if (anchors.size === 0 || !FRAGMENT_DESTINATION.test(markdown)) return markdown;
  const dropped = (url) => {
    if (!url.startsWith('#')) return false;
    let id = url.slice(1);
    try {
      id = decodeURIComponent(id);
    } catch {
      // A fragment that is no valid escape is compared as written.
    }
    return anchors.has(id);
  };
  let out = markdown;
  for (const { start } of destinations(markdown, dropped).sort((a, b) => b.start - a.start)) {
    out = `${out.slice(0, start)}${pageUrl}${out.slice(start)}`;
  }
  return out;
}
