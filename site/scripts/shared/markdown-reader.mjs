// What a Markdown reader prints for a piece of the Markdown copy, for the
// tests of the writer.
//
// The copy writes text a page prints as it is (a figure's alt, a clip's
// description, a work's title) into Markdown, where a `*`, a `_` or a `$` of
// that text opens emphasis or maths unless it is escaped. A test that compared
// the copy with the string the writer was meant to write would agree with the
// writer's own idea of Markdown, so the tests read it back here with the
// site's own pipeline instead (`createMarkdownProcessor` of
// @astrojs/markdown-remark, with remark-math as astro.config.mjs adds it, and
// with no typographic quotes, which would change the text on their own).
//
// The tests that use this run after the site's dependencies are installed.
import { createMarkdownProcessor } from '@astrojs/markdown-remark';
import remarkMath from 'remark-math';

/** The processor, made once by the first reading. */
let processor;

/** The named character references the HTML serializer writes. */
const NAMED = { amp: '&', lt: '<', gt: '>', quot: '"', nbsp: '\u00a0' };

/**
 * HTML text or an attribute value with its character references read: the
 * numeric ones, and the named ones the HTML serializer writes.
 *
 * @param {string} html
 * @returns {string}
 */
export const decodeReferences = (html) =>
  html.replace(/&(?:#x([\da-f]+)|#(\d+)|(amp|lt|gt|quot|nbsp));/gi, (_whole, hex, decimal, name) =>
    hex ? String.fromCodePoint(Number.parseInt(hex, 16)) : decimal ? String.fromCodePoint(Number(decimal)) : NAMED[name.toLowerCase()],
  );

/**
 * Text with each run of white space one space, as a browser collapses it:
 * spaces, tabs and line breaks, never a no-break space.
 *
 * @param {string} text
 * @returns {string}
 */
export const oneLine = (text) => text.replace(/[ \t\n\f\r]+/g, ' ').trim();

/** An HTML tag, a `>` inside a quoted attribute value read as part of the value. */
export const TAG = /<(?:[^>"']|"[^"]*"|'[^']*')*>/g;

/**
 * What a reader prints for `markdown`.
 *
 * @param {string} markdown
 * @returns {Promise<{ html: string, text: string, alts: string[] }>} The HTML
 *   the site's pipeline writes; its text, the tags out and each run of white
 *   space one space as a browser shows it (a no-break space stays); and the
 *   alt of each image, in order.
 */
export async function printed(markdown) {
  processor ??= createMarkdownProcessor({ syntaxHighlight: false, smartypants: false, remarkPlugins: [remarkMath] });
  const { code } = await (await processor).render(markdown);
  return {
    html: code,
    text: oneLine(decodeReferences(code.replace(TAG, ''))),
    alts: [...code.matchAll(/<img\b[^>]*?\balt="([^"]*)"/g)].map((found) => decodeReferences(found[1])),
  };
}
