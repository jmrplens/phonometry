// Every component a page uses has a Markdown writer beside it, and every
// writer still has a page to write.
//
// The Markdown copy of a page is written from its source by the renderer in
// src/lib/agent-md/: prose, tables, TeX and code keep their bytes, and each
// component is replaced by the writer that sits beside it
// (src/components/**/<Name>.md.mjs). The renderer never drops anything
// silently. What it cannot write faithfully it still writes as well as it
// can, and records as an issue with its file and line; this check reads every
// page under src/content/docs the way the copy does and turns each issue
// into a failure, before the site is built:
//
// - a component a page uses or imports with no writer beside it (what it
//   shows would reach the copy as nothing, which is how the copies cut from
//   the source by regular expressions lost every figure and table a
//   component drew);
// - a prop the writer does not declare (the 14 guides that passed their See
//   also links as a `links` prop SeeAlso never had published an empty panel),
//   and a spread of props or attributes, which nothing can read;
// - an expression that is neither a literal nor a name imported from an
//   allow-listed data module, in the text, in a prop or in an attribute of
//   raw HTML (`{totalChecks}` without its import; `<a href={x}>`, whose link
//   was dropped);
// - raw HTML with no rule, and an aside Starlight does not draw;
// - a writer that throws or returns something other than a string;
// - a page that does not parse as the site's MDX pipeline reads it, or whose
//   data module fails to load, as either would fail the site build.
//
// And two that concern the writers themselves:
//
// - a writer whose component no page uses is stale, and goes with it (asked
//   only when every page was read: the page that did not parse may be the
//   one that uses it);
// - a writer opens with a comment that names its component and says what it
//   keeps and what it drops on purpose, so a reader of the copy who misses
//   something on the page can find out whether that was meant. Both are
//   asked for: a comment that only lists what is kept leaves the reader
//   guessing about the rest. A writer that writes nothing says so in its
//   first line, `<Name>: dropped on purpose.`, and why below it.
//
// Its tests live under src/lib/agent-md/test/ (`pnpm run test:agent-md`),
// because they import the parser, and `test:scripts` stays free of
// dependencies so that it can run before the install.
//
// Usage (from site/, after `pnpm install`): node scripts/check-markdown-writers.mjs
import { readFileSync } from 'node:fs';
import { basename, relative, sep } from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

import { pageFiles } from '../src/lib/agent-md/content.mjs';
import { COMPONENTS_DIR, loadRegistry, WRITER_SUFFIX, writerFiles } from '../src/lib/agent-md/registry.mjs';
import { CONTENT_DIR, DATA_MODULES, renderFile, SITE_DIR } from '../src/lib/agent-md/render.mjs';
import { markdownPlugins, PLUGIN_REWRITES } from '../src/lib/agent-md/rewrites.mjs';

/**
 * What to do about each kind of failure, printed once under its list.
 *
 * @type {Record<string, string>}
 */
export const REMEDIES = {
  component:
    'add <Name>.md.mjs beside <Name>.astro, default-exporting markdownFor({ tag, props, toMarkdown }) from src/lib/agent-md/types.mjs',
  prop: "declare the prop in the writer's props and write what it carries, or stop passing it; write a spread out as the props or attributes it stands for",
  expression: `write the value as a literal, or import it from ${DATA_MODULES.join(' or ')}`,
  html: 'write it as Markdown, or give the tag a rule in HTML_RULES in src/lib/agent-md/render.mjs',
  directive: 'use an aside Starlight draws: note, tip, caution or danger',
  writer: 'fix what the message names: a writer that threw or returned something other than a string, or what the writer found wrong on the page',
  parse: 'the page does not parse as the site build reads it; fix the syntax at that line',
  import: 'a data module the page imports failed to load, as it would in the site build; the message says what it could not read',
  stale: 'no page uses the component: delete its writer (and the component, if nothing else renders it)',
  opening:
    "open the writer with a /** ... */ comment whose first line is '<Name>: ...' and which says what it keeps and what it drops on purpose; a writer that writes nothing opens with '<Name>: dropped on purpose.' and says why",
};

/**
 * Whether an error is the parser's: a message with a reason and the rule that
 * raised it, as unified reports a syntax error. Anything else a page throws
 * comes from loading a module it imports.
 *
 * @param {unknown} error
 * @returns {error is { reason: string, ruleId: string, line?: number, place?: any }}
 */
export const isParseError = (error) =>
  typeof error === 'object' && error !== null && typeof (/** @type {any} */ (error).reason) === 'string' && 'ruleId' in error;

/** Where a parse error happened when it gives no line of its own: `(3:1-3:15)` in its reason. */
const PLACE = /\((\d+):\d+(?:-\d+:\d+)?\)/u;

/** The first line of a writer's opening comment: `/**`, then ` * <Name>: ...`. */
const OPENING = /^\/\*\*\n \* ([A-Z][A-Za-z0-9]*): (\S[^\n]*)/u;

/** The first line of a writer that writes nothing, after its name: the whole statement. */
const DROPPED_WHOLE = 'dropped on purpose.';

/** The two things every other opening comment says. */
const KEEPS = /\b(?:kept|keeps)\b/iu;
const DROPS = /\b(?:dropped|drops)\b/iu;

/**
 * Why a writer's opening comment does not do its job, if it does not.
 *
 * @param {string} source  The writer file.
 * @param {string} tag  The component it writes.
 * @returns {string | undefined}
 */
export function openingProblem(source, tag) {
  const opening = OPENING.exec(source);
  if (!opening) return 'does not open with a /** ... */ comment whose first line names its component';
  if (opening[1] !== tag) return `opens with a comment about ${opening[1]}, not ${tag}`;
  if (opening[2] === DROPPED_WHOLE) return undefined;
  const comment = source.slice(0, source.indexOf('*/'));
  const missing = [KEEPS.test(comment) ? '' : 'what it keeps', DROPS.test(comment) ? '' : 'what it drops'].filter(Boolean);
  if (missing.length === 0) return undefined;
  return `opens with a comment that does not say ${missing.join(' or ')} (one that writes nothing opens with '${tag}: ${DROPPED_WHOLE}')`;
}

/**
 * @typedef {object} Failure
 * @property {string} where  `es/reference/glossary.mdx:14`, or a writer's file name.
 * @property {keyof typeof REMEDIES} kind
 * @property {string} message
 */

/**
 * Reads every page and every writer.
 *
 * @param {{ contentDir?: string, componentsDir?: string, siteDir?: string }} [options]
 *   The directories to read, the site's own by default; the tests pass small
 *   ones. `siteDir` holds the astro.config.mjs whose Markdown plugins are
 *   held to a rule of src/lib/agent-md/rewrites.mjs each.
 * @returns {Promise<{ failures: Failure[], pages: number, writers: number, used: Map<string, number> }>}
 */
export async function checkMarkdownWriters({ contentDir = CONTENT_DIR, componentsDir = COMPONENTS_DIR, siteDir = SITE_DIR } = {}) {
  /** @type {Failure[]} */
  const failures = [];
  /** @type {Map<string, number>} */
  const used = new Map();
  let registry;
  try {
    registry = await loadRegistry(componentsDir);
  } catch (error) {
    failures.push({ where: componentsDir, kind: 'writer', message: error.message });
    return { failures, pages: 0, writers: 0, used };
  }

  for (const file of writerFiles(componentsDir)) {
    const tag = basename(file, WRITER_SUFFIX);
    const problem = openingProblem(readFileSync(file, 'utf8'), tag);
    if (problem) {
      failures.push({ where: relative(componentsDir, file).split(sep).join('/'), kind: 'opening', message: `${tag}${WRITER_SUFFIX} ${problem}` });
    }
  }

  // A Markdown plugin of the site that writes into pages needs a rule that
  // writes the same into their copies (src/lib/agent-md/rewrites.mjs); without
  // one, a copy holds the page's source where the page shows what the plugin
  // wrote, as the bibliography's held its markers.
  for (const plugin of await markdownPlugins(siteDir)) {
    for (const page of PLUGIN_REWRITES[plugin.module] ? [] : (plugin.rewrites ?? [])) {
      failures.push({ where: plugin.module, kind: 'plugin', message: `${plugin.module} writes into ${page}, and the Markdown copies have no rule for it in src/lib/agent-md/rewrites.mjs` });
    }
  }

  const files = pageFiles(contentDir);
  /** Pages that could not be read, whose components are then not counted. */
  let unread = 0;
  for (const file of files) {
    const shown = relative(contentDir, file).split(sep).join('/');
    /** @type {import('../src/lib/agent-md/types.mjs').RenderIssue[]} */
    const issues = [];
    let tree;
    try {
      ({ tree } = await renderFile(file, { registry, issues, lang: shown.startsWith('es/') ? 'es' : 'en' }));
    } catch (error) {
      unread += 1;
      if (isParseError(error)) {
        const at = error.line ?? error.place?.line ?? error.place?.start?.line ?? PLACE.exec(error.reason)?.[1];
        failures.push({ where: at ? `${shown}:${at}` : shown, kind: 'parse', message: error.reason });
      } else {
        failures.push({ where: shown, kind: 'import', message: error.message });
      }
      continue;
    }
    for (const issue of issues) {
      failures.push({ where: issue.line ? `${shown}:${issue.line}` : shown, kind: issue.kind, message: issue.message });
    }
    const walk = (node) => {
      if ((node.type === 'mdxJsxFlowElement' || node.type === 'mdxJsxTextElement') && /^[A-Z]/u.test(node.name ?? '')) {
        used.set(node.name, (used.get(node.name) ?? 0) + 1);
      }
      for (const child of node.children ?? []) walk(child);
    };
    walk(tree);
  }

  // A writer is stale when no page uses its component, which only every page
  // read can tell: a page that did not parse may be the one that uses it.
  for (const tag of unread === 0 ? registry.keys() : []) {
    if (!used.has(tag)) {
      failures.push({ where: `${tag}${WRITER_SUFFIX}`, kind: 'stale', message: `no page under the content directory uses <${tag}>` });
    }
  }
  return { failures, pages: files.length, writers: registry.size, used };
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  const { failures, pages, writers, used } = await checkMarkdownWriters();
  if (failures.length === 0) {
    console.log(
      `Every component the ${pages} pages use has a Markdown writer: ${used.size} components, ${writers} writers, ` +
        'every prop declared, every expression readable, every tag with a rule.',
    );
  } else {
    const byKind = Map.groupBy(failures, (failure) => failure.kind);
    for (const [kind, list] of byKind) {
      console.error(`\nFAIL ${list.length} ${kind} problem(s):`);
      for (const failure of list) console.error(`  ${failure.where}  ${failure.message}`);
      console.error(`  -> ${REMEDIES[kind]}`);
    }
    console.error(`\n${failures.length} problem(s) on ${new Set(failures.map((f) => f.where.split(':')[0])).size} file(s).`);
    process.exitCode = 1;
  }
}
