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
//       the errata families, in English). The directory is emptied first, so
//       one that holds anything but an earlier dump (its routes.json and the
//       copies it lists, at whatever depth) is refused before a page is
//       rendered.
//       `--undated` leaves out the two dated header lines, `Published:` and
//       `Updated:`, which llms.txt does not state and which cost a question to
//       git per page, and the `Unreleased:` line, which git decides as well:
//       `make llms` writes llms.txt alone and passes it. It is refused with
//       `--public`, since the copies the site publishes state their dates.
//       routes.json also gives, as `unreleasedLine`, the `Unreleased:` line an
//       English copy carries when the page changed after the release, dated
//       dump or not, so generate_llms.py measures every page as if it held it
//       and cuts the shards at the same places either way.
//       With `--public` in the same run, both are written from one rendering,
//       so the llms files the build publishes carry the copies byte for byte
//       (package.json `prebuild`).
//   node scripts/agent-md.mjs --docs <dir>
//       Writes the GitHub edition into <dir> (`../docs` from `make llms`):
//       every English page the edition holds (src/lib/agent-md/edition.mjs),
//       as the GitHub flavour of its copy writes it, at <route>.md or, for a
//       page written as its folder's index, <route>/index.md; each file opens
//       with a comment naming its source and one line with the way back to
//       <dir>/README.md and the address the page is published at, and a link
//       to another page of the edition is relative. A file a previous run
//       wrote that this one does not write is removed; every other file of
//       <dir> is left alone. The run fails before a file is written on any
//       issue the renderer records, and when <dir>/README.md, the edition's
//       hand-kept front door, does not link every page or links a file that
//       is not there (rule F3). It combines with `--dump`, as `make llms`
//       runs it.
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
//       With `--flavour github`, a page of the GitHub edition is printed as
//       `--docs` writes its file. Issues go to stderr, and any issue makes the
//       exit status 1.
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { fileOfRoute, pageFiles, readEntry } from '../src/lib/agent-md/content.mjs';
import { handwrittenTargets, removeWrittenCopies } from '../src/lib/agent-md/copies.mjs';
import {
  documentAnchors,
  editionLinks,
  editionOpening,
  editionPages,
  githubAnchors,
  inEdition,
  isEditionFile,
  numbersInCode,
  readmeProblems,
  sitePage,
} from '../src/lib/agent-md/edition.mjs';
import { pageMarkdown, titleOf } from '../src/lib/agent-md/page.mjs';
import { CONTENT_DIR, REPO_DIR, SITE_DIR, renderFile } from '../src/lib/agent-md/render.mjs';
import { loadRegistry } from '../src/lib/agent-md/registry.mjs';
import { UNRELEASED } from '../src/lib/agent-md/header.mjs';
import { unreadPage } from './check-markdown-writers.mjs';
import { verifiedProvider } from '../src/lib/agent-md/verified.mjs';
import { loadContentDates } from '../src/lib/content-dates.mjs';
import { loadRelease } from '../src/lib/release-commit.mjs';
import { version } from '../src/data/repo-stats.mjs';
import { readCommittedText } from '../src/lib/line-ends.mjs';
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
 * (src/lib/page-dates.mjs). With them, the latest release
 * (src/lib/release-commit.mjs), which a page whose content changed after it
 * says it is newer than, in the `Unreleased:` line, as the page does under its
 * title.
 */
async function pageDates() {
  const dates = await loadContentDates({ siteRoot: SITE_DIR });
  const release = await loadRelease({ siteRoot: SITE_DIR, version });
  return { dateOf: dates.dateOf, publishedOf: firstPublished, release };
}

/** The name of the file of a dump that lists its routes. */
export const ROUTES_FILE = 'routes.json';

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
 * @param {string} contentDir
 */
function routeEntry(file, route, copy, contentDir) {
  const { data } = readEntry(file, contentDir);
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
 * Why a directory cannot take a dump, or nothing when it can: a run empties
 * the directory before it writes, so it takes only a new directory, an empty
 * one, or one that holds an earlier dump and nothing else, which is its
 * routes.json and the copies that routes.json lists: every file below it, at
 * any depth, is one of those.
 * Asked before a page is rendered, so a refused directory costs nothing.
 *
 * @param {string} dir
 * @returns {string | undefined}
 */
export function dumpRefusal(dir) {
  if (!existsSync(dir)) return undefined;
  const leave = 'so it is left alone. Name an empty or new directory, or one a dump was written to.';
  if (!statSync(dir).isDirectory()) return `--dump ${dir} is a file, not a directory, ${leave}`;
  const entries = readdirSync(dir, { withFileTypes: true });
  if (entries.length === 0) return undefined;
  const listing = join(dir, ROUTES_FILE);
  if (!entries.some((entry) => entry.name === ROUTES_FILE && entry.isFile())) {
    return `--dump ${dir} holds files and no ${ROUTES_FILE}, so it is not a dump this command wrote, ${leave}`;
  }
  let copies;
  try {
    const { pages } = JSON.parse(readFileSync(listing, 'utf8'));
    copies = new Set(pages.filter((page) => typeof page.copy === 'string').map((page) => page.copy));
  } catch (error) {
    return `--dump ${dir} holds a ${ROUTES_FILE} this command cannot read (${error.message}), ${leave}`;
  }
  // Every file below the directory, at any depth, is one the listing names: a
  // folder that a route writes into can still hold a file no route wrote, and
  // the dump is removed whole before it is written again.
  /** @type {string[]} */
  const foreign = [];
  const walk = (current, prefix) => {
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const path = prefix ? `${prefix}/${entry.name}` : entry.name;
      if (entry.isDirectory()) walk(join(current, entry.name), path);
      else if (path !== ROUTES_FILE && !copies.has(path)) foreign.push(path);
    }
  };
  walk(dir, '');
  foreign.sort();
  if (foreign.length > 0) {
    return `--dump ${dir} holds ${foreign.join(', ')}, which no route of its ${ROUTES_FILE} writes, so it is more than an earlier dump, ${leave}`;
  }
  return undefined;
}

/** An address of the site in a Markdown text, up to its first blank or bracket. */
const SITE_ADDRESS = /https:\/\/docs\.jmrp\.io\/phonometry[^\s)>\]]*/gu;

/**
 * The files of the GitHub edition, as `--docs` writes them: every page the
 * edition holds, or only `only` and the pages they link to with a fragment,
 * whose headings a link's fragment is held to.
 *
 * @param {{
 *   docsDir: string,
 *   registry: Map<string, import('../src/lib/agent-md/types.mjs').ComponentMarkdown>,
 *   contentDir?: string,
 *   only?: ReadonlySet<string>,
 * }} options  `only` is a set of routes; every page by default.
 * @returns {Promise<{
 *   files: Map<string, string>,
 *   pages: import('../src/lib/agent-md/edition.mjs').EditionPage[],
 *   problems: string[],
 *   kept: number,
 * }>}  `files` by path relative to `docsDir`; `problems` one line each, the
 *   renderer's issues and the README's; `kept` how many links keep the site's
 *   address because GitHub would not find their fragment on the target.
 */
export async function editionFiles({ docsDir, registry, contentDir = CONTENT_DIR, only }) {
  const pages = editionPages(contentDir);
  const byRoute = new Map(pages.map((page) => [page.route, page]));
  const byPath = new Map(pages.map((page) => [page.path, page]));
  /** @type {Map<string, string>} */
  const rendered = new Map();
  /** @type {string[]} */
  const problems = [];
  const render = async (page) => {
    if (rendered.has(page.route)) return rendered.get(page.route);
    const { markdown, issues } = await pageMarkdown(page.file, { registry, flavour: 'github', contentDir });
    for (const issue of issues) {
      problems.push(`  ${relative(contentDir, page.file).split(sep).join('/')}${issue.line ? `:${issue.line}` : ''}  [${issue.kind}] ${issue.message}`);
    }
    rendered.set(page.route, markdown);
    return markdown;
  };
  const wanted = only ? pages.filter((page) => only.has(page.route)) : pages;
  for (const page of wanted) await render(page);
  // A link's fragment is held to the headings of the page it leads to, so
  // those pages are rendered too.
  for (const page of wanted) {
    for (const [url] of rendered.get(page.route).matchAll(SITE_ADDRESS)) {
      const target = sitePage(url);
      const linked = target?.fragment ? byRoute.get(target.route) : undefined;
      if (linked) await render(linked);
    }
  }
  /** @type {Map<string, Set<string>>} */
  const anchors = new Map();
  const anchorsOf = (path) => {
    if (!anchors.has(path)) {
      const page = byPath.get(path);
      if (page && !rendered.has(page.route)) throw new Error(`${path} was not rendered before a link to it was read`);
      anchors.set(path, page ? githubAnchors(rendered.get(page.route)) : documentAnchors(join(docsDir, path)));
    }
    return anchors.get(path);
  };
  /** @type {Map<string, string>} */
  const files = new Map();
  let kept = 0;
  for (const page of wanted) {
    const linked = editionLinks(rendered.get(page.route), page, { pages: byRoute, anchorsOf });
    kept += linked.kept.length;
    files.set(page.path, `${editionOpening(page)}\n\n${numbersInCode(linked.markdown)}`);
  }
  if (!only) {
    const readme = join(docsDir, 'README.md');
    if (existsSync(readme)) {
      // A file of the edition no planned page writes is removed by this run,
      // so it does not count as there: a link to it would dangle once it goes.
      const present = (path) => {
        const file = join(docsDir, path);
        return existsSync(file) && !(path.endsWith('.md') && isEditionFile(readCommittedText(file)));
      };
      for (const problem of readmeProblems(readCommittedText(readme), pages, present)) {
        problems.push(`  ${problem}`);
      }
    } else problems.push(`  ${relative(SITE_DIR, readme)} is missing: it is the edition's front door, and links every page of it`);
  }
  return { files, pages, problems, kept };
}

/**
 * The files of a directory that a previous run of `--docs` wrote: the
 * Markdown files that open with the edition's comment.
 *
 * @param {string} dir
 * @returns {string[]}  Paths relative to `dir`.
 */
export function editionFilesUnder(dir) {
  /** @type {string[]} */
  const found = [];
  const walk = (current) => {
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const path = join(current, entry.name);
      if (entry.isDirectory()) walk(path);
      else if (entry.name.endsWith('.md') && isEditionFile(readCommittedText(path))) {
        found.push(relative(dir, path).split(sep).join('/'));
      }
    }
  };
  if (existsSync(dir)) walk(dir);
  return found.sort();
}

/**
 * Writes every page's copy under `publicOut`, the English pages the llms
 * files carry, with routes.json, under `dumpDir`, and the GitHub edition
 * under `docsDir`; any of them may be left out.
 *
 * @param {{
 *   publicOut?: string,
 *   dumpDir?: string,
 *   docsDir?: string,
 *   undated?: boolean,
 *   contentDir?: string,
 *   dates?: import('../src/lib/agent-md/page.mjs').PageDates,
 * }} options  `contentDir` is the content collection the pages are read
 *   from (the site's own by default); `dates` the dates the headers state,
 *   which by default are asked of git, and which `undated` leaves out.
 * @returns {Promise<number>}  The exit status.
 */
export async function writePages({ publicOut, dumpDir, docsDir, undated = false, contentDir = CONTENT_DIR, dates: given }) {
  const refusal = dumpDir && dumpRefusal(dumpDir);
  if (refusal) {
    console.error(`[agent-md] ${refusal}`);
    return 2;
  }
  const registry = await loadRegistry();
  const all = pageFiles(contentDir);
  const routeOfFile = (file) => routeOf(relative(contentDir, file).split(sep).join('/'));
  const shownFile = (file) => relative(contentDir, file).split(sep).join('/');
  const carried = (route) => isEnglish(route) && FULL_TEXT_KINDS.includes(pageKind(route));
  // A dump alone renders only the pages it carries; the copies for public/
  // need every page, and a run that writes both renders each page once.
  const files = publicOut ? all : dumpDir ? all.filter((file) => carried(routeOfFile(file))) : [];
  const dates = undated || files.length === 0 ? undefined : (given ?? (await pageDates()));
  // What each page's "Verified by" line states, from the join the line is drawn by.
  const verified = verifiedProvider(contentDir);
  /** @type {Map<string, string>} */
  const copies = new Map();
  /** @type {Map<string, string>} */
  const dumped = new Map();
  /** @type {string[]} */
  const problems = [];
  for (const file of files) {
    const { route, markdown, issues } = await pageMarkdown(file, { registry, dates, contentDir, verified });
    if (!hasMarkdownCopy(route)) continue;
    for (const issue of issues) {
      problems.push(`  ${shownFile(file)}${issue.line ? `:${issue.line}` : ''}  [${issue.kind}] ${issue.message}`);
    }
    if (publicOut) copies.set(join(publicOut, route, 'index.md'), markdown);
    if (dumpDir && carried(route)) dumped.set(route, markdown);
  }
  const edition = docsDir ? await editionFiles({ docsDir, registry, contentDir }) : undefined;
  if (edition) problems.push(...edition.problems);
  if (problems.length > 0) {
    console.error(`[agent-md] FAIL ${problems.length} issue(s); no copy was written:`);
    for (const problem of problems) console.error(problem);
    if (problems.length > (edition?.problems.length ?? 0)) {
      console.error('  Run `pnpm run check:markdown-writers` for the remedy of each kind.');
    }
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
  // Asked again before the directory is emptied, since it can have changed
  // while the pages were rendered.
  const late = dumpDir && dumpRefusal(dumpDir);
  if (late) {
    console.error(`[agent-md] ${late}`);
    return 2;
  }
  if (dumpDir) rmSync(dumpDir, { recursive: true, force: true });
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
      routes.push(routeEntry(file, route, copy, contentDir));
    }
    routes.sort((a, b) => (a.route < b.route ? -1 : a.route > b.route ? 1 : 0));
    mkdirSync(dumpDir, { recursive: true });
    // The line a dated copy carries when its page changed after the release:
    // generate_llms.py counts it on every page, there or not, so that the
    // shards are cut at the same places from a dated dump and an undated one.
    const unreleasedLine = `Unreleased: ${UNRELEASED.en(version)}`;
    writeFileSync(join(dumpDir, ROUTES_FILE), `${JSON.stringify({ pages: routes, unreleasedLine }, null, 1)}\n`, 'utf8');
    console.log(
      `[agent-md] dumped ${dumped.size} English copies${undated ? ' without their dates' : ''} and ${routes.length} routes into ${relative(SITE_DIR, dumpDir) || '.'}`,
    );
  }
  if (docsDir && edition) {
    const stale = editionFilesUnder(docsDir).filter((path) => !edition.files.has(path));
    for (const path of stale) rmSync(join(docsDir, path));
    for (const [path, text] of edition.files) {
      const target = join(docsDir, path);
      mkdirSync(dirname(target), { recursive: true });
      writeFileSync(target, text, 'utf8');
    }
    console.log(
      `[agent-md] wrote the GitHub edition into ${relative(SITE_DIR, docsDir) || '.'}: ${edition.files.size} pages` +
        `${stale.length ? `, ${stale.length} no longer in it removed` : ''}; ${edition.kept} link(s) keep the site's address, ` +
        'their fragment being no heading GitHub anchors on the target',
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
  if (flavour === 'github' && inEdition(clean)) {
    // A page of the GitHub edition, as --docs writes its file.
    const { files, pages, problems } = await editionFiles({ docsDir: join(REPO_DIR, 'docs'), registry, only: new Set([clean]) });
    const path = pages.find((one) => one.route === clean)?.path;
    process.stdout.write(files.get(path) ?? '');
    for (const problem of problems) console.error(problem.trim());
    return problems.length > 0 ? 1 : 0;
  }
  // One page: the same two readers as a full run, one pass each over the
  // history.
  const dates = await pageDates();
  const { markdown, issues } = await pageMarkdown(file, { registry, flavour, dates, verified: verifiedProvider() });
  process.stdout.write(markdown);
  for (const issue of issues) {
    console.error(`${shown(file)}${issue.line ? `:${issue.line}` : ''}  [${issue.kind}] ${issue.message}`);
  }
  return issues.length > 0 ? 1 : 0;
}

/**
 * Runs the command line.
 *
 * @param {readonly string[]} args
 * @returns {Promise<number>}  The exit status.
 */
async function main(args) {
  // The value an option takes, or nothing when the option is absent or the
  // word after it is another option: `--dump --undated` names no directory.
  const option = (name) => {
    const at = args.indexOf(name);
    const value = at === -1 ? undefined : args[at + 1];
    return value === undefined || value.startsWith('--') ? undefined : value;
  };
  if (args.includes('--public') || args.includes('--dump') || args.includes('--docs')) {
    const dump = option('--dump');
    if (args.includes('--dump') && !dump) {
      console.error('--dump needs a directory');
      return 2;
    }
    const docs = option('--docs');
    if (args.includes('--docs') && !docs) {
      console.error('--docs needs a directory');
      return 2;
    }
    if (args.includes('--undated') && args.includes('--public')) {
      console.error('--undated is for a dump alone: the copies the site publishes state their dates');
      return 2;
    }
    return writePages({
      publicOut: args.includes('--public') ? resolve(option('--out') ?? join(SITE_DIR, 'public')) : undefined,
      dumpDir: dump ? resolve(dump) : undefined,
      docsDir: docs ? resolve(docs) : undefined,
      undated: args.includes('--undated'),
    });
  }
  if (args.includes('--census')) {
    await census();
    return 0;
  }
  if (args.includes('--page')) {
    const flavour = option('--flavour') ?? 'agent';
    if (flavour !== 'agent' && flavour !== 'github') {
      console.error(`--flavour is agent or github, not ${flavour}`);
      return 2;
    }
    return page(option('--page') ?? '', flavour);
  }
  console.error(
    'usage: node scripts/agent-md.mjs [--public [--out <dir>]] [--dump <dir> [--undated]] [--docs <dir>] | --census | --page <route> [--flavour agent|github]',
  );
  return 2;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = await main(process.argv.slice(2));
}
