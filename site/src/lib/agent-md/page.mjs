/**
 * One page of the site as its Markdown copy: the title, the header, the body
 * and the references, in that order.
 *
 * The body is what the renderer writes from the page source
 * (src/lib/agent-md/render.mjs). The rest is what the page's layout adds
 * around that source and the source does not hold, so a copy written from the
 * body alone would start without a title and end without the references the
 * page prints:
 *
 *  - the `# ` title, from the frontmatter title, or from the `<title>` the
 *    landing pages set in their head, which is the one their readers see;
 *  - the header (src/lib/agent-md/header.mjs), which says where the page
 *    lives, in which language, for which release, by whom, when and against
 *    which standards;
 *  - the References section, which the layout renders from the frontmatter
 *    (src/components/References.astro) and the page source never writes by
 *    hand, worded by the same module (src/lib/references-format.mjs).
 *
 * The GitHub flavour (the edition under docs/) has no header block: GitHub
 * shows the file's own history and address beside it.
 *
 * @module
 */
import { readFileSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

import { author, siteTitle } from '../../data/site.mjs';
import { installCommand, preRelease, version } from '../../data/repo-stats.mjs';
import { implementedStandards } from '../reference-chips.ts';
import { isoInstant } from '../date-rules.mjs';
import { markdownCopyPath, routeOf } from '../page-markdown.mjs';
import { citationParts, noteParts, opening, sortedReferences } from '../references-format.mjs';
import { fileOfRoute } from './content.mjs';
import { header } from './header.mjs';
import { fragmentText, line, lineStart, titleMarkdown } from './markdown-table.mjs';
import { CONTENT_DIR, SITE, SITE_DIR, renderFile } from './render.mjs';

/** @typedef {import('../references-format.mjs').Reference} Reference */
/** @typedef {import('../references-format.mjs').Part} Part */
/** @typedef {import('./types.mjs').RenderIssue} RenderIssue */

/**
 * Where a page's dates come from.
 *
 * @typedef {object} PageDates
 * @property {(file: string) => Date} dateOf  The date its content last changed.
 * @property {(file: string) => string | undefined} publishedOf  The day it was
 *   first published, `YYYY-MM-DD`, or nothing when git cannot say.
 */

/** The heading of the References section, as the site's own strings word it. */
export const REFERENCES_HEADING = Object.freeze(
  Object.fromEntries(
    ['en', 'es'].map((lang) => {
      const strings = JSON.parse(readFileSync(join(SITE_DIR, 'src', 'content', 'i18n', `${lang}.json`), 'utf8'));
      return [lang, String(strings['phonometry.references.title'])];
    }),
  ),
);

/**
 * A link destination as Markdown reads it: wrapped in `<...>` when it holds a
 * space or a parenthesis, which would end it early.
 *
 * @param {string} url
 * @returns {string}
 */
const destination = (url) => (/[\s()<>]/u.test(url) ? `<${url.replaceAll('<', '%3C').replaceAll('>', '%3E')}>` : url);

/**
 * One fragment of a citation as Markdown: an address shown as itself an
 * autolink, `<https://...>`, which every Markdown reader links and which ends
 * where its bracket does (left bare, the full stop, comma or parenthesis of a
 * note's sentence after it was read as part of it by a reader of plain text),
 * a title in italics, a link around whatever it carries.
 *
 * @param {Part} part
 * @returns {string}
 */
function partMarkdown(part) {
  if (part.href && part.text === part.href) return `<${part.href}>`;
  const text = fragmentText(part.text);
  const marked = part.italic && text.trim() ? `*${text}*` : text;
  return part.href ? `[${marked}](${destination(part.href)})` : marked;
}

/**
 * The References section, as the page prints it: one entry per reference, in
 * the page's order, each opening with its author and year in bold and its
 * note on the line under it.
 *
 * @param {readonly Reference[] | undefined} references
 * @param {'en' | 'es'} lang
 * @returns {string}  Markdown, or `''` for a page with no references.
 */
export function referencesMarkdown(references, lang) {
  if (!references?.length) return '';
  const entries = sortedReferences(references, lang).map(([, ref]) => {
    const citation = citationParts(ref, lang).map(partMarkdown).join('');
    const note = ref.note ? `\n  ${lineStart(noteParts(ref.note).map(partMarkdown).join('').trim())}` : '';
    return `- **${fragmentText(opening(ref, lang))}**${citation.trimEnd()}${note}`;
  });
  return `## ${REFERENCES_HEADING[lang]}\n\n${entries.join('\n')}`;
}

/**
 * The title a page's head carries: an explicit `<title>` override (the
 * landing pages have one) or the frontmatter title. The site's name, which
 * Starlight appends to every other title and which an override that wants it
 * spells out (`Top-level API | phonometry`), is no part of the page's title.
 *
 * @param {Record<string, unknown>} frontmatter
 * @returns {string}
 */
export function titleOf(frontmatter) {
  const head = Array.isArray(frontmatter.head) ? frontmatter.head : [];
  const override = head.find((entry) => entry?.tag === 'title' && typeof entry.content === 'string');
  const title = line(String(override?.content ?? frontmatter.title ?? ''));
  const suffix = ` | ${siteTitle}`;
  return title.endsWith(suffix) ? title.slice(0, -suffix.length) : title;
}

/**
 * The route of the same page in the other language: `x` and `es/x`, and the
 * two landing pages for each other.
 *
 * @param {string} route
 * @returns {string}
 */
export function otherLanguage(route) {
  if (route === '') return 'es';
  if (route === 'es') return '';
  return route.startsWith('es/') ? route.slice(3) : `es/${route}`;
}

/** The address of a route's page. */
const pageUrl = (route) => SITE.url(`${SITE.base}/${route ? `${route}/` : ''}`);

/**
 * One page's copy.
 *
 * @param {string} file  The page file, under `contentDir`.
 * @param {{
 *   registry: Map<string, import('./types.mjs').ComponentMarkdown>,
 *   dates?: PageDates,
 *   flavour?: 'agent' | 'github',
 *   contentDir?: string,
 *   verified?: (route: string) => import('./header.mjs').HeaderFields['verified'],
 * }} options  `dates` is left out where git is not there to ask (a page
 *   written in a test), and the copy then prints no date. `verified` says
 *   what the page's "Verified by" line states, for the pages that show one.
 * @returns {Promise<{ route: string, lang: 'en' | 'es', markdown: string, issues: RenderIssue[] }>}
 */
export async function pageMarkdown(file, { registry, dates, flavour = 'agent', contentDir = CONTENT_DIR, verified }) {
  const route = routeOf(relative(contentDir, file).split(sep).join('/'));
  const lang = route === 'es' || route.startsWith('es/') ? 'es' : 'en';
  /** @type {RenderIssue[]} */
  const issues = [];
  const rendered = await renderFile(file, { registry, flavour, issues, lang });
  const { frontmatter } = rendered;
  // The shape the docs collection's schema (src/content.config.ts) gives the
  // list; the build refuses a page whose frontmatter does not have it.
  const references = /** @type {import('../reference-chips.ts').Reference[] | undefined} */ (frontmatter.references);
  const title = titleMarkdown(titleOf(frontmatter));
  // Blank lines off both ends, never the indentation of the first line: an
  // API page can open with indented code.
  const body = rendered.markdown.replace(/^(?:[ \t]*\n)+/u, '').trimEnd();
  const tail = referencesMarkdown(references, lang);
  const parts = [title];
  if (flavour === 'agent') {
    const other = otherLanguage(route);
    parts.push(
      header({
        lang,
        canonical: pageUrl(route),
        alternate: fileOfRoute(other, contentDir) ? SITE.url(markdownCopyPath(other, SITE.base)) : undefined,
        release: {
          version,
          install: installCommand,
          preRelease,
        },
        author,
        published: dates?.publishedOf(file),
        updated: dates ? isoInstant(dates.dateOf(file)) : undefined,
        standards: implementedStandards(references),
        verified: verified?.(route),
        summary: typeof frontmatter.description === 'string' ? frontmatter.description : undefined,
      }),
    );
  }
  if (body) parts.push(body);
  if (tail) parts.push(tail);
  return { route, lang, markdown: `${parts.join('\n\n')}\n`, issues };
}
