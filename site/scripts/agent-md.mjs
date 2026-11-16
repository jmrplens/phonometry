// Writes the site's pages as Markdown, from the page source, outside the
// Astro build.
//
// The renderer under src/lib/agent-md/ turns a page's MDX into the Markdown a
// reader without a browser gets: prose, tables, TeX and code keep their bytes,
// and every component is replaced by the writer that sits beside it
// (src/components/**/<Name>.md.mjs). src/lib/agent-md/page.mjs puts the title,
// the header and the references around it. This command runs it in plain
// Node, so a page can be read back in a second instead of after a nine-minute
// build, and so the copies the site publishes are written before the build
// rather than cut out of its HTML.
//
// Usage (from site/, after `pnpm install`):
//   node scripts/agent-md.mjs --public [--out <dir>]
//       Writes every page's copy to <dir>/<route>/index.md (default public/,
//       which the build publishes beside the pages; package.json `prebuild`
//       runs it), the two landing pages included, after removing the copies a
//       previous run left there: the index.md files that open as a copy does
//       (src/lib/agent-md/copies.mjs), never another file of that name. Any
//       issue the renderer records fails the run before a file is written, so
//       no page publishes a copy that lost part of it.
//   node scripts/agent-md.mjs --census
//       Parses and writes every page under src/content/docs, then reports
//       which components the pages use and whether each has a writer, the raw
//       HTML they carry, and every issue the renderer recorded (a component
//       with no writer, a prop a writer does not declare, an expression it
//       cannot read, HTML or an aside with no rule), with file and line.
//       A report: it exits 0 whatever it finds.
//   node scripts/agent-md.mjs --page <route> [--flavour agent|github]
//       Prints one page's copy: `signals/filters/filter-banks`,
//       `es/signals/filters/filter-banks`, or `` / `es` for the two homes.
//       Issues go to stderr, and any issue makes the exit status 1.
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { fileOfRoute, pageFiles } from '../src/lib/agent-md/content.mjs';
import { handwrittenTargets, removeWrittenCopies } from '../src/lib/agent-md/copies.mjs';
import { pageMarkdown } from '../src/lib/agent-md/page.mjs';
import { CONTENT_DIR, SITE_DIR, renderFile } from '../src/lib/agent-md/render.mjs';
import { loadRegistry } from '../src/lib/agent-md/registry.mjs';
import { unreadPage } from './check-markdown-writers.mjs';
import { verifiedProvider } from '../src/lib/agent-md/verified.mjs';
import { loadContentDates } from '../src/lib/content-dates.mjs';
import { hasMarkdownCopy } from '../src/lib/page-markdown.mjs';
import { firstPublished } from '../src/lib/page-dates.mjs';

/** A content path as the census prints it. */
const shown = (file) => relative(CONTENT_DIR, file).split(sep).join('/');

/**
 * The dates every copy's header states, read from git once for every page by
 * the readers the build uses for the same dates: the last change from the
 * history of the content tree (src/lib/content-dates.mjs), the first
 * publication from one pass over the history of the docs tree
 * (src/lib/page-dates.mjs).
 */
async function pageDates() {
  const dates = await loadContentDates({ siteRoot: SITE_DIR });
  return { dateOf: dates.dateOf, publishedOf: firstPublished };
}

/**
 * Writes every page's copy under `out`.
 *
 * @param {string} out
 * @returns {Promise<number>}  The exit status.
 */
async function publish(out) {
  const registry = await loadRegistry();
  const files = pageFiles();
  const dates = await pageDates();
  // What each page's "Verified by" line states, from the join the line is drawn by.
  const verified = verifiedProvider();
  /** @type {Map<string, string>} */
  const copies = new Map();
  /** @type {string[]} */
  const problems = [];
  for (const file of files) {
    const { route, markdown, issues } = await pageMarkdown(file, { registry, dates, verified });
    if (!hasMarkdownCopy(route)) continue;
    for (const issue of issues) {
      problems.push(`  ${shown(file)}${issue.line ? `:${issue.line}` : ''}  [${issue.kind}] ${issue.message}`);
    }
    copies.set(join(out, route, 'index.md'), markdown);
  }
  if (problems.length > 0) {
    console.error(`[agent-md] FAIL ${problems.length} issue(s); no copy was written:`);
    for (const problem of problems) console.error(problem);
    console.error('  Run `pnpm run check:markdown-writers` for the remedy of each kind.');
    return 1;
  }
  // A file at a copy's place that no run wrote (docs/ holds 42 index.md files
  // written by hand) is neither removed nor written over: the run stops first.
  const foreign = handwrittenTargets(copies.keys());
  if (foreign.length > 0) {
    console.error(`[agent-md] FAIL ${foreign.length} file(s) where a copy goes were not written by a run; nothing was removed or written:`);
    for (const path of foreign) console.error(`  ${path}`);
    return 2;
  }
  mkdirSync(out, { recursive: true });
  removeWrittenCopies(out);
  for (const [target, markdown] of copies) {
    mkdirSync(dirname(target), { recursive: true });
    writeFileSync(target, markdown, 'utf8');
  }
  console.log(`[agent-md] wrote ${copies.size} Markdown copies into ${relative(SITE_DIR, out) || '.'}`);
  return 0;
}

/** Counts, per key, kept in insertion order and printed sorted. */
class Tally extends Map {
  add(key, by = 1) {
    this.set(key, (this.get(key) ?? 0) + by);
  }
}

/**
 * Writes every page and reports what the pages use and every issue. A page
 * that does not parse, or imports a module that fails to load, is one of the
 * pages with an issue, of kind `parse` or `import` with the parser's reason
 * and line, and the census goes on to the next page.
 *
 * @param {{ files?: string[], registry?: Map<string, import('../src/lib/agent-md/types.mjs').ComponentMarkdown>,
 *   log?: (line: string) => void }} [options]  Every page of the site, its
 *   writers and the console, unless a test hands in its own.
 */
export async function census({ files = pageFiles(), registry, log = console.log } = {}) {
  registry ??= await loadRegistry();
  const uses = new Tally();
  const pagesUsing = new Map();
  const html = new Tally();
  const kinds = new Tally();
  const report = [];
  const troubled = new Set();
  for (const file of files) {
    let rendered;
    try {
      rendered = await renderFile(file, { registry });
    } catch (error) {
      const failure = unreadPage(error, shown(file));
      troubled.add(file);
      kinds.add(failure.kind);
      report.push(`  ${failure.where}  [${failure.kind}] ${failure.message}`);
      continue;
    }
    const { issues, tree } = rendered;
    const walk = (node) => {
      if (node.type === 'mdxJsxFlowElement' || node.type === 'mdxJsxTextElement') {
        const name = node.name ?? '';
        if (/^[A-Z]/u.test(name)) {
          uses.add(name);
          if (!pagesUsing.has(name)) pagesUsing.set(name, new Set());
          pagesUsing.get(name).add(file);
        } else if (name) html.add(name);
      }
      for (const child of node.children ?? []) walk(child);
    };
    walk(tree);
    if (issues.length > 0) troubled.add(file);
    for (const issue of issues) {
      kinds.add(issue.kind);
      report.push(`  ${shown(file)}${issue.line ? `:${issue.line}` : ''}  [${issue.kind}] ${issue.message}`);
    }
  }
  log(
    `${files.length} pages written: ${files.length - troubled.size} with no issue, ${troubled.size} with at least one.`,
  );
  log(`\nComponents the pages use (${uses.size}; ${registry.size} writers):`);
  for (const [name, count] of [...uses].sort((a, b) => b[1] - a[1])) {
    const pages = pagesUsing.get(name).size;
    log(`  ${name.padEnd(16)} ${String(count).padStart(5)} uses on ${String(pages).padStart(4)} pages  ${registry.has(name) ? 'writer' : 'NO WRITER'}`);
  }
  const stale = [...registry.keys()].filter((tag) => !uses.has(tag));
  if (stale.length) log(`\nWriters no page uses: ${stale.join(', ')}`);
  log(`\nRaw HTML the pages carry: ${[...html].sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${v}`).join(', ')}`);
  log(`\nIssues: ${report.length}${kinds.size ? ` (${[...kinds].map(([k, v]) => `${k} ${v}`).join(', ')})` : ''}`);
  for (const row of report) log(row);
}

async function page(route, flavour) {
  const clean = route.replace(/^\/+|\/+$/gu, '').replace(/^phonometry\/?/u, '');
  const file = fileOfRoute(clean);
  if (!file) {
    console.error(`no page at "${route}" under ${CONTENT_DIR}`);
    return 2;
  }
  const registry = await loadRegistry();
  // One page: the same two readers as a full run, one pass each over the
  // history.
  const { dateOf } = await loadContentDates({ siteRoot: SITE_DIR });
  const dates = { dateOf, publishedOf: firstPublished };
  const { markdown, issues } = await pageMarkdown(file, { registry, flavour, dates, verified: verifiedProvider() });
  process.stdout.write(markdown);
  for (const issue of issues) {
    console.error(`${shown(file)}${issue.line ? `:${issue.line}` : ''}  [${issue.kind}] ${issue.message}`);
  }
  return issues.length > 0 ? 1 : 0;
}

const args = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url) ? process.argv.slice(2) : null;
const option = (name) => {
  const at = args.indexOf(name);
  return at === -1 ? undefined : args[at + 1];
};
if (args === null) {
  // Imported, by a test: nothing runs.
} else if (args.includes('--public')) {
  process.exitCode = await publish(resolve(option('--out') ?? join(SITE_DIR, 'public')));
} else if (args.includes('--census')) {
  await census();
} else if (args.includes('--page')) {
  const flavour = option('--flavour') ?? 'agent';
  if (flavour !== 'agent' && flavour !== 'github') {
    console.error(`--flavour is agent or github, not ${flavour}`);
    process.exit(2);
  }
  process.exitCode = await page(option('--page') ?? '', flavour);
} else {
  console.error('usage: node scripts/agent-md.mjs --public [--out <dir>] | --census | --page <route> [--flavour agent|github]');
  process.exitCode = 2;
}
