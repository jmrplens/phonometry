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
//   node scripts/agent-md.mjs --dump <dir> [--undated]
//       Writes what scripts/generate_llms.py builds the llms files from:
//       <dir>/routes.json, every English route with its kind
//       (src/lib/page-markdown.mjs `pageKind`), title, description, the
//       standards it implements and the path of its copy, and under
//       <dir>/<route>/index.md the copy of every page whose whole text the
//       llms files carry (`FULL_TEXT_KINDS`: the guides, the catalogues and
//       the errata families, in English). The directory is emptied first, and
//       a directory that holds anything but a previous dump is refused.
//       `--undated` leaves out the two dated header lines, `Published:` and
//       `Updated:`, which llms.txt does not state and which cost a question to
//       git per page: `make llms` writes llms.txt alone and passes it.
//       With `--public` in the same run, both are written from one rendering,
//       so the llms files the build publishes carry the copies byte for byte
//       (package.json `prebuild`).
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
import { existsSync, mkdirSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { fileOfRoute, pageFiles, readEntry } from '../src/lib/agent-md/content.mjs';
import { handwrittenTargets, removeWrittenCopies } from '../src/lib/agent-md/copies.mjs';
import { pageMarkdown, titleOf } from '../src/lib/agent-md/page.mjs';
import { CONTENT_DIR, SITE_DIR, renderFile } from '../src/lib/agent-md/render.mjs';
import { loadRegistry } from '../src/lib/agent-md/registry.mjs';
import { unreadPage } from './check-markdown-writers.mjs';
import { verifiedProvider } from '../src/lib/agent-md/verified.mjs';
import { loadContentDates } from '../src/lib/content-dates.mjs';
import { FULL_TEXT_KINDS, hasMarkdownCopy, pageKind, routeOf } from '../src/lib/page-markdown.mjs';
import { implementedStandards } from '../src/lib/reference-chips.ts';
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

/** The name of the file of a dump that lists its routes. */
const ROUTES_FILE = 'routes.json';

/**
 * Whether a route is English: the English tree is the site's root, and the
 * Spanish one sits under `es/`.
 *
 * @param {string} route
 */
const isEnglish = (route) => route !== 'es' && !route.startsWith('es/');

/**
 * What routes.json says about one English route.
 *
 * @param {string} file
 * @param {string} route
 * @param {string | null} copy  The copy's path in the dump, or nothing for a
 *   page whose text the llms files do not carry.
 */
function routeEntry(file, route, copy) {
  const { data } = readEntry(file);
  const references = /** @type {import('../src/lib/reference-chips.ts').Reference[] | undefined} */ (data.references);
  return {
    route,
    kind: pageKind(route),
    title: titleOf(data),
    description: typeof data.description === 'string' ? data.description : '',
    standards: implementedStandards(references),
    copy,
  };
}

/**
 * Empties a dump directory before a run writes it, and refuses one that holds
 * anything but a previous dump: the run deletes what is there.
 *
 * @param {string} dir
 * @returns {boolean}  False when the directory is refused.
 */
function clearDump(dir) {
  if (!existsSync(dir)) return true;
  const entries = readdirSync(dir);
  if (entries.length > 0 && !entries.includes(ROUTES_FILE)) {
    console.error(`[agent-md] --dump ${dir} holds files and no ${ROUTES_FILE}: not a dump this command wrote, so it is left alone. Name an empty or new directory.`);
    return false;
  }
  rmSync(dir, { recursive: true, force: true });
  return true;
}

/**
 * Writes every page's copy under `publicOut`, and the English pages the llms
 * files carry, with routes.json, under `dumpDir`; either may be left out.
 *
 * @param {{ publicOut?: string, dumpDir?: string, undated?: boolean }} options
 * @returns {Promise<number>}  The exit status.
 */
async function write({ publicOut, dumpDir, undated = false }) {
  const registry = await loadRegistry();
  const all = pageFiles();
  const routeOfFile = (file) => routeOf(relative(CONTENT_DIR, file).split(sep).join('/'));
  const carried = (route) => isEnglish(route) && FULL_TEXT_KINDS.includes(pageKind(route));
  // A dump alone renders only the pages it carries; the copies for public/
  // need every page, and a run that writes both renders each page once.
  const files = publicOut ? all : all.filter((file) => carried(routeOfFile(file)));
  const dates = undated ? undefined : await pageDates();
  // What each page's "Verified by" line states, from the join the line is drawn by.
  const verified = verifiedProvider();
  /** @type {Map<string, string>} */
  const copies = new Map();
  /** @type {Map<string, string>} */
  const dumped = new Map();
  /** @type {string[]} */
  const problems = [];
  for (const file of files) {
    const { route, markdown, issues } = await pageMarkdown(file, { registry, dates, verified });
    if (!hasMarkdownCopy(route)) continue;
    for (const issue of issues) {
      problems.push(`  ${shown(file)}${issue.line ? `:${issue.line}` : ''}  [${issue.kind}] ${issue.message}`);
    }
    if (publicOut) copies.set(join(publicOut, route, 'index.md'), markdown);
    if (dumpDir && carried(route)) dumped.set(route, markdown);
  }
  if (problems.length > 0) {
    console.error(`[agent-md] FAIL ${problems.length} issue(s); no copy was written:`);
    for (const problem of problems) console.error(problem);
    console.error('  Run `pnpm run check:markdown-writers` for the remedy of each kind.');
    return 1;
  }
  // A file at a copy's place that no run wrote (docs/ holds 42 index.md files
  // written by hand) is neither removed nor written over: the run stops first,
  // before a dump is cleared or a copy written.
  const foreign = publicOut ? handwrittenTargets(copies.keys()) : [];
  if (foreign.length > 0) {
    console.error(`[agent-md] FAIL ${foreign.length} file(s) where a copy goes were not written by a run; nothing was removed or written:`);
    for (const path of foreign) console.error(`  ${path}`);
    return 2;
  }
  if (dumpDir && !clearDump(dumpDir)) return 2;
  if (publicOut) {
    mkdirSync(publicOut, { recursive: true });
    removeWrittenCopies(publicOut);
    for (const [target, markdown] of copies) {
      mkdirSync(dirname(target), { recursive: true });
      writeFileSync(target, markdown, 'utf8');
    }
    console.log(`[agent-md] wrote ${copies.size} Markdown copies into ${relative(SITE_DIR, publicOut) || '.'}`);
  }
  if (dumpDir) {
    const routes = [];
    for (const file of all) {
      const route = routeOfFile(file);
      if (!isEnglish(route) || !hasMarkdownCopy(route)) continue;
      const copy = dumped.has(route) ? `${route}/index.md` : null;
      if (copy) {
        const target = join(dumpDir, copy);
        mkdirSync(dirname(target), { recursive: true });
        writeFileSync(target, dumped.get(route), 'utf8');
      }
      routes.push(routeEntry(file, route, copy));
    }
    routes.sort((a, b) => (a.route < b.route ? -1 : a.route > b.route ? 1 : 0));
    mkdirSync(dumpDir, { recursive: true });
    writeFileSync(join(dumpDir, ROUTES_FILE), `${JSON.stringify({ pages: routes }, null, 1)}\n`, 'utf8');
    console.log(
      `[agent-md] dumped ${dumped.size} English copies${undated ? ' without their dates' : ''} and ${routes.length} routes into ${relative(SITE_DIR, dumpDir) || '.'}`,
    );
  }
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
} else if (args.includes('--public') || args.includes('--dump')) {
  const dump = option('--dump');
  if (args.includes('--dump') && !dump) {
    console.error('--dump needs a directory');
    process.exit(2);
  }
  if (args.includes('--undated') && args.includes('--public')) {
    console.error('--undated is for a dump alone: the copies the site publishes state their dates');
    process.exit(2);
  }
  process.exitCode = await write({
    publicOut: args.includes('--public') ? resolve(option('--out') ?? join(SITE_DIR, 'public')) : undefined,
    dumpDir: dump ? resolve(dump) : undefined,
    undated: args.includes('--undated'),
  });
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
  console.error(
    'usage: node scripts/agent-md.mjs [--public [--out <dir>]] [--dump <dir> [--undated]] | --census | --page <route> [--flavour agent|github]',
  );
  process.exitCode = 2;
}
