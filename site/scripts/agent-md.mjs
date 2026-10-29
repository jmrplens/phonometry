// Writes the site's pages as Markdown, from the page source, outside the
// Astro build.
//
// The renderer under src/lib/agent-md/ turns a page's MDX into the Markdown a
// reader without a browser gets: prose, tables, TeX and code keep their bytes,
// and every component is replaced by the writer that sits beside it
// (src/components/**/<Name>.md.mjs). This command runs it in plain Node, so a
// page can be read back in a second instead of after a nine-minute build, and
// so the generators that will publish the copies need no build either.
//
// Usage (from site/, after `pnpm install`):
//   node scripts/agent-md.mjs --census
//       Parses and writes every page under src/content/docs, then reports
//       which components the pages use and whether each has a writer, the raw
//       HTML they carry, and every issue the renderer recorded (a component
//       with no writer, a prop a writer does not declare, an expression it
//       cannot read, HTML or an aside with no rule), with file and line.
//       A report: it exits 0 whatever it finds.
//   node scripts/agent-md.mjs --page <route> [--flavour agent|github]
//       Prints one page: `signals/filters/filter-banks`,
//       `es/signals/filters/filter-banks`, or `` / `es` for the two homes.
//       Issues go to stderr, and any issue makes the exit status 1.
import { existsSync, readdirSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import process from 'node:process';

import { CONTENT_DIR, renderFile } from '../src/lib/agent-md/render.mjs';
import { loadRegistry } from '../src/lib/agent-md/registry.mjs';

/** Every page file under the content directory, sorted. */
function pageFiles(dir = CONTENT_DIR) {
  const found = [];
  const walk = (current) => {
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const path = join(current, entry.name);
      if (entry.isDirectory()) walk(path);
      else if (/\.mdx?$/u.test(entry.name)) found.push(path);
    }
  };
  walk(dir);
  return found.sort();
}

/** A content path as the census prints it. */
const shown = (file) => relative(CONTENT_DIR, file).split(sep).join('/');

/**
 * The file a route is written from.
 *
 * @param {string} route
 * @returns {string | undefined}
 */
function fileFor(route) {
  const clean = route.replace(/^\/+|\/+$/gu, '').replace(/^phonometry\/?/u, '');
  const stems = clean ? [clean, `${clean}/index`] : ['index'];
  for (const stem of stems) {
    for (const ext of ['.mdx', '.md']) {
      const file = join(CONTENT_DIR, `${stem}${ext}`);
      if (existsSync(file)) return file;
    }
  }
  return undefined;
}

/**
 * The title a page's head carries: an explicit `<title>` override (the
 * homes have one) or the frontmatter title.
 *
 * @param {Record<string, unknown>} frontmatter
 * @returns {string}
 */
function titleOf(frontmatter) {
  const head = Array.isArray(frontmatter.head) ? frontmatter.head : [];
  const override = head.find((entry) => entry?.tag === 'title' && typeof entry.content === 'string');
  return String(override?.content ?? frontmatter.title ?? '');
}

/** Counts, per key, kept in insertion order and printed sorted. */
class Tally extends Map {
  add(key, by = 1) {
    this.set(key, (this.get(key) ?? 0) + by);
  }
}

async function census() {
  const registry = await loadRegistry();
  const files = pageFiles();
  const uses = new Tally();
  const pagesUsing = new Map();
  const html = new Tally();
  const kinds = new Tally();
  const report = [];
  const troubled = new Set();
  for (const file of files) {
    const { issues, tree } = await renderFile(file, { registry });
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
  console.log(
    `${files.length} pages written: ${files.length - troubled.size} with no issue, ${troubled.size} with at least one.`,
  );
  console.log(`\nComponents the pages use (${uses.size}; ${registry.size} writers):`);
  for (const [name, count] of [...uses].sort((a, b) => b[1] - a[1])) {
    const pages = pagesUsing.get(name).size;
    console.log(`  ${name.padEnd(16)} ${String(count).padStart(5)} uses on ${String(pages).padStart(4)} pages  ${registry.has(name) ? 'writer' : 'NO WRITER'}`);
  }
  const stale = [...registry.keys()].filter((tag) => !uses.has(tag));
  if (stale.length) console.log(`\nWriters no page uses: ${stale.join(', ')}`);
  console.log(`\nRaw HTML the pages carry: ${[...html].sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${v}`).join(', ')}`);
  console.log(`\nIssues: ${report.length}${kinds.size ? ` (${[...kinds].map(([k, v]) => `${k} ${v}`).join(', ')})` : ''}`);
  for (const row of report) console.log(row);
}

async function page(route, flavour) {
  const file = fileFor(route);
  if (!file) {
    console.error(`no page at "${route}" under ${CONTENT_DIR}`);
    return 2;
  }
  const registry = await loadRegistry();
  const { markdown, frontmatter, issues } = await renderFile(file, { registry, flavour });
  process.stdout.write(`# ${titleOf(frontmatter)}\n\n${markdown}`);
  for (const issue of issues) {
    console.error(`${shown(file)}${issue.line ? `:${issue.line}` : ''}  [${issue.kind}] ${issue.message}`);
  }
  return issues.length > 0 ? 1 : 0;
}

const args = process.argv.slice(2);
const option = (name) => {
  const at = args.indexOf(name);
  return at === -1 ? undefined : args[at + 1];
};
if (args.includes('--census')) {
  await census();
} else if (args.includes('--page')) {
  const flavour = option('--flavour') ?? 'agent';
  if (flavour !== 'agent' && flavour !== 'github') {
    console.error(`--flavour is agent or github, not ${flavour}`);
    process.exit(2);
  }
  process.exitCode = await page(option('--page') ?? '', flavour);
} else {
  console.error('usage: node scripts/agent-md.mjs --census | --page <route> [--flavour agent|github]');
  process.exitCode = 2;
}
