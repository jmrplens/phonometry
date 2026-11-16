/**
 * Writes docs/reference/bibliography.md, the GitHub copy of the bibliography,
 * from the references the site's pages declare, the way the site build writes
 * the page itself (src/lib/remark-bibliography.mjs).
 *
 * The copy is more than a copy: the site serves it as the English Markdown
 * version of /reference/bibliography/ (src/lib/page-markdown.mjs, `mirrorOf`),
 * the llms shards are cut from it (scripts/generate_llms.py) and
 * scripts/check_published_sources.py reads the authors its entries open with.
 * Written once by hand, it would have stayed behind the first reference a page
 * added while the site page and its Spanish twin moved on, with every check
 * green.
 *
 * So it is written here. The copy keeps its own opening, everything above its
 * first `## ` heading, which speaks of this folder rather than of the site.
 * From the first heading on it is the English page: its headings and the prose
 * under them, and in place of each marker the section's list, written by
 * `sectionMarkdown` from the same pages the build reads (`bibliographyOf`),
 * with a link to a page that has a copy in docs/ pointing at that copy and any
 * other link at the site.
 *
 * Run with `--check` to fail when the committed copy is not what this would
 * write; the docs workflow does. Run bare to rewrite it (`make
 * bibliography-mirror`), then `make llms`, which reads it.
 */
import { existsSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';
import { MARKER, sectionMarkdown } from '../src/lib/bibliography-entries.mjs';
import { readCommittedText } from '../src/lib/line-ends.mjs';
import { codeLines } from '../src/lib/markdown-fences.mjs';
import { mirrorOf } from '../src/lib/page-markdown.mjs';
import { bibliographyOf } from '../src/lib/remark-bibliography.mjs';

const here = dirname(fileURLToPath(import.meta.url));

/** A site address inside a Markdown link, `](/phonometry/x/y/#a)`. */
const SITE_LINK = /\]\((\/[^)\s]*)\)/g;

/**
 * The link from a file in `from` to `to`, separated by slashes as a Markdown
 * link is on every system. relative() separates by the system's own, and on
 * Windows would write `..\\signals\\a.md` into the copy, which the committed
 * copy, written with slashes, would then never equal.
 *
 * @param {string} from The folder the link is written in.
 * @param {string} to The file it leads to.
 * @param {{relative: typeof relative, sep: string}} [paths] node:path, unless a
 *   test hands in another system's (`path.win32`).
 * @returns {string}
 */
export function relativeLink(from, to, paths = { relative, sep }) {
  return paths.relative(from, to).split(paths.sep).join('/');
}

/**
 * A site address (`/phonometry/x/y/#a`) as the copy writes it: the copy of the
 * page in docs/ when it has one, relative to the bibliography's own copy, and
 * the page on the site otherwise.
 *
 * @param {string} href
 * @param {{docsDir: string, base?: string, site?: string}} where
 * @returns {string}
 */
export function mirrorLink(href, { docsDir, base = basePath, site = `${siteUrl}${basePath}` }) {
  const found = href.match(new RegExp(`^${base}/([^#]*?)/?(#.*)?$`));
  if (!found) return href;
  const [, route, anchor = ''] = found;
  const copy = route ? mirrorOf(route, docsDir) : undefined;
  if (copy && existsSync(copy)) return `${relativeLink(join(docsDir, 'reference'), copy)}${anchor}`;
  return `${site}/${route}${route ? '/' : ''}${anchor}`;
}

/**
 * The text of the GitHub copy.
 *
 * @param {object} parts
 * @param {string} parts.copy The committed copy, whose opening is kept.
 * @param {string} parts.page The English bibliography page's source.
 * @param {{key: string, entries: object[]}[]} parts.sections Its sections, `bibliographyOf`.
 * @param {(href: string) => string} parts.link Where a site address leads in the copy.
 * @returns {string}
 * @throws {Error} When the copy or the page has no `## ` heading, or the page
 *   marks a section the sections do not have.
 */
export function bibliographyMirror({ copy, page, sections, link }) {
  const opening = copy.search(/^## /m);
  if (opening < 0) throw new Error('docs/reference/bibliography.md has no "## " heading to keep its opening above');
  const body = page.replace(/^---\n[\s\S]*?\n---\n/, '');
  const first = body.search(/^## /m);
  if (first < 0) throw new Error('the bibliography page has no "## " heading');
  const rows = body.slice(first).split('\n');
  // A marker shown in a fence is code the page quotes, and stays as written,
  // as withSections leaves it (src/lib/bibliography-entries.mjs).
  const code = codeLines(rows, { kind: 'md' });
  const lines = rows.map((line, index) => {
      const marker = code[index] ? null : MARKER.exec(line.trim());
      if (!marker) return line;
      const section = sections.find(({ key }) => key === marker[1]);
      if (!section) throw new Error(`the bibliography page marks a section its data does not have, ${marker[1]}`);
      return (
        sectionMarkdown(section, 'en')
          // An entry opens with its author and year, not in bold as on the site.
          .replace(/^- \*\*(.+?)\*\*/gm, '- $1')
          // A report number with a run of hyphens is an identifier: in code, as
          // the guides' own reference lists write it, so GitHub does not set a dash.
          .replace(/\(([^()\s`]*--[^()\s`]*)\)/g, '(`$1`)')
      );
    });
  const written = lines.join('\n').replace(SITE_LINK, (_, href) => `](${link(href)})`);
  return `${copy.slice(0, opening)}${written.trimEnd()}\n`;
}

/**
 * The committed copy at `target` and the text {@link bibliographyMirror}
 * writes from it and the page at `page`, both files read as the commit holds
 * them ({@link readCommittedText}): a checkout with carriage returns would
 * otherwise hand the writer a page whose lines end in one and a copy that
 * never equals what it writes.
 *
 * @param {object} parts
 * @param {string} parts.target The committed copy, docs/reference/bibliography.md.
 * @param {string} parts.page The English bibliography page.
 * @param {{key: string, entries: object[]}[]} parts.sections Its sections, `bibliographyOf`.
 * @param {(href: string) => string} parts.link Where a site address leads in the copy.
 * @returns {{copy: string, text: string}}
 */
export function mirrorFiles({ target, page, sections, link }) {
  const copy = readCommittedText(target);
  return { copy, text: bibliographyMirror({ copy, page: readCommittedText(page), sections, link }) };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const root = join(here, '..', '..');
  const docsDir = join(root, 'docs');
  const target = join(docsDir, 'reference', 'bibliography.md');
  const contentDir = join(here, '..', 'src', 'content', 'docs');
  const { copy, text } = mirrorFiles({
    target,
    page: join(contentDir, 'reference', 'bibliography.md'),
    sections: await bibliographyOf(contentDir, 'en'),
    link: (href) => mirrorLink(href, { docsDir }),
  });
  const entries = (text.match(/^- /gm) ?? []).length;
  if (process.argv.includes('--check')) {
    if (text !== copy) {
      const was = copy.split('\n');
      const line = text.split('\n').findIndex((row, index) => row !== was[index]) + 1;
      console.error(
        `FAIL docs/reference/bibliography.md is not what the pages' references write (first difference on line ${line}): ` +
          'run `make bibliography-mirror` (or `pnpm run mirror:bibliography` in site/), then `make llms`, and commit both',
      );
      process.exit(1);
    }
    console.log(`ok   docs/reference/bibliography.md lists the ${entries} works the pages cite, as they write them`);
  } else {
    writeFileSync(target, text);
    console.log(`[mirror-bibliography] wrote docs/reference/bibliography.md, ${entries} works`);
  }
}
