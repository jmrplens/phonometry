// Fail the build when a formula did not render.
//
// KaTeX does not stop a build when it cannot parse an expression: with
// `throwOnError` off, rehype-katex emits `<span class="katex-error">` carrying
// the parse message as its title and the page ships. Worse, a display block
// whose `$$` delimiters sit on a content line is not merely mis-rendered: the
// parser consumes the rest of the document as math, so `spanish-building-code`
// silently lost **six** `## ` sections and everything after them, in both
// locales, for as long as it took someone to read that page to the end.
//
// Nothing in the pipeline noticed. `html-validate` sees well-formed markup and
// pa11y sees an accessible page; both are right, and both are answering a
// different question. This script asks the one that matters: did every formula
// on the site actually render?
//
// It also flags the delimiter shape that caused it, in the sources rather than
// in the output, because that failure is silent by construction: a display
// block must open and close on its own line. Every one of the site's other
// display blocks already does.
//
// And it reads the glossary's cards for a formula that never reached KaTeX at
// all: a field the card prints as typed keeps its dollar signs, and no parse
// error says so.
//
// Usage: node scripts/check-math-render.mjs [--dist dist] [--sources ../docs ../site]

import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { codeLines, pageLines, splitLines } from '../src/lib/markdown-fences.mjs';
import { shownLines, strayDelimiter } from './shared/page-prose.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const SITE = resolve(HERE, '..');
const REPO = resolve(SITE, '..');

/** Every file under `root` whose name ends in one of `exts`. */
function walk(root, exts, out = []) {
  let entries;
  try {
    entries = readdirSync(root, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const entry of entries) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) {
      // `superpowers/` is gitignored working notes, not published prose.
      if (entry.name === 'node_modules' || entry.name === '.astro') continue;
      if (entry.name === 'superpowers') continue;
      walk(path, exts, out);
    } else if (exts.some((ext) => entry.name.endsWith(ext))) {
      out.push(path);
    }
  }
  return out;
}

/** Parse errors KaTeX left in the built HTML, with the message it recorded. */
function renderFailures(distDir) {
  const failures = [];
  for (const file of walk(distDir, ['.html'])) {
    const html = readFileSync(file, 'utf8');
    if (!html.includes('katex-error')) continue;
    // The parse message is the title attribute of the offending span.
    const messages = [...html.matchAll(/class="katex-error"[^>]*title="([^"]*)"/g)].map(
      (m) => m[1],
    );
    failures.push({
      file: relative(REPO, file),
      count: Math.max(messages.length, 1),
      messages: [...new Set(messages)].slice(0, 3),
    });
  }
  return failures;
}

/**
 * Display blocks whose delimiters share a line with content.
 *
 * Inline `$$...$$` complete on one line is fine; what breaks the parser is a
 * block that opens or closes on a line carrying other content.
 */
function delimiterProblems(sourceDirs) {
  const problems = [];
  for (const dir of sourceDirs) {
    for (const file of walk(dir, ['.md', '.mdx'])) {
      const lines = splitLines(readFileSync(file, 'utf8'));
      const mdx = file.endsWith('.mdx');
      const kind = mdx ? 'mdx' : 'md';
      // A formula shown inside a code block is a sample, not a formula.
      const code = codeLines(lines, { kind });
      // Prose that talks *about* `$$` writes it inside a code span, read as
      // the site reads one, over the lines of its block (shared/page-prose.mjs).
      const shown = shownLines(lines, code, { mdx });
      const read = pageLines(shown, { kind });
      lines.forEach((_line, index) => {
        if (code[index]) return;
        const trimmed = strayDelimiter(shown[index], read[index].rest);
        if (trimmed === null) return;
        problems.push({
          file: relative(REPO, file),
          line: index + 1,
          text: trimmed.slice(0, 72),
        });
      });
    }
  }
  return problems;
}

/**
 * The shipped stylesheet must be the one that matches the renderer.
 *
 * Two different copies of KaTeX decide how a formula looks. `rehype-katex`
 * writes the markup using the katex it depends on, while the site imports
 * `katex/dist/katex.min.css` from its own katex dependency. Nothing used to tie
 * the two versions together, and they drifted: the site served 0.18 CSS over
 * 0.16 markup, and the class names for the base box and the strut were renamed
 * between those lines. Every formula on the site therefore rendered with no
 * `white-space: nowrap` on its base box and no struts setting its line height,
 * free to wrap in the middle of an expression.
 *
 * Nothing caught it, because each half was valid on its own: the markup parsed,
 * the stylesheet loaded, the pages validated. The mismatch only exists in the
 * relationship between them, so that is what this checks. For each class KaTeX
 * renamed, take the spelling the built markup actually uses and require the
 * built CSS to carry a rule for that exact spelling.
 *
 * They are tied now: `site/package.json` and the `katex: 'catalog:'` override
 * in `site/pnpm-workspace.yaml` both read katex from one catalog entry there,
 * so every katex in the tree resolves to the same version. This check is what
 * notices if that link is ever cut, for instance by a literal version written
 * in place of `catalog:` on either side.
 */
function stylesheetMismatch(distDir) {
  // Renamed in KaTeX 0.18: `.katex .base` -> `.katex-base`, likewise the strut.
  const RENAMED = [
    { html: 'base', legacy: '.katex .base', current: '.katex-base' },
    { html: 'strut', legacy: '.katex .strut', current: '.katex-strut' },
  ];
  const page = walk(distDir, ['.html']).find((file) =>
    readFileSync(file, 'utf8').includes('class="katex"'),
  );
  // No rendered formula anywhere means there is no relationship to check.
  if (!page) return [];
  const html = readFileSync(page, 'utf8');
  const css = walk(distDir, ['.css'])
    .map((file) => readFileSync(file, 'utf8'))
    .join('\n');

  const mismatches = [];
  for (const { html: name, legacy, current } of RENAMED) {
    const usesLegacy = html.includes(`class="${name}"`);
    const usesCurrent = html.includes(`class="katex-${name}"`);
    if (!usesLegacy && !usesCurrent) continue;
    const wanted = usesCurrent ? current : legacy;
    // `.katex-base` is a substring of nothing in the legacy sheet and
    // `.katex .base` of nothing in the current one, so a plain search
    // discriminates the two spellings even after minification.
    if (css.includes(wanted)) continue;
    mismatches.push({
      page: relative(REPO, page),
      emitted: usesCurrent ? `katex-${name}` : name,
      wanted,
      served: css.includes(usesCurrent ? legacy : current)
        ? `the other spelling, ${usesCurrent ? legacy : current}`
        : 'no rule at all',
    });
  }
  return mismatches;
}

/**
 * Inline maths the glossary printed as typed.
 *
 * The glossary's cards and its symbol index are written by
 * src/components/Glossary.astro from src/data/glossary.mjs, where a field is
 * text with its maths between dollar signs, and the component hands KaTeX the
 * fields it chooses to typeset. It typeset the symbol, the qualifier and the
 * definition and printed the unit and the standard as typed, so
 * "(unit of $x$)²/Hz" and "Annex I uses $L_{90}$ as the residual level"
 * reached the page with their dollar signs, in both languages. KaTeX never
 * saw them, so it reported nothing, and neither did any other check.
 *
 * The text of every card and of the index, once the TeX each formula keeps in
 * its MathML annotation is taken out, has no dollar sign left. The cards are
 * found by their class, and a build with none is reported: a renamed class
 * would otherwise leave this with nothing to read and nothing to say.
 */
function glossaryAsTyped(distDir) {
  const found = [];
  let cards = 0;
  for (const file of walk(distDir, ['.html'])) {
    const html = readFileSync(file, 'utf8');
    if (!html.includes('glossary-term')) continue;
    const blocks = [];
    for (const [, attributes, inner] of html.matchAll(
      /<article\b([^>]*\bclass="glossary-term\b[^"]*"[^>]*)>([\s\S]*?)<\/article>/g,
    )) {
      cards += 1;
      blocks.push({ where: `#${/\bid="([^"]*)"/.exec(attributes)?.[1] ?? '(no id)'}`, inner });
    }
    for (const [, inner] of html.matchAll(
      /<details\b[^>]*\bclass="symbol-index\b[^"]*"[^>]*>([\s\S]*?)<\/details>/g,
    )) {
      blocks.push({ where: ' (symbol index)', inner });
    }
    for (const { where, inner } of blocks) {
      const text = inner
        .replace(/<annotation\b[^>]*>[\s\S]*?<\/annotation>/g, '')
        .replace(/<[^>]+>/g, '');
      const at = text.indexOf('$');
      if (at < 0) continue;
      found.push({
        place: `${relative(REPO, file)}${where}`,
        text: text.slice(Math.max(0, at - 30), at + 30).replace(/\s+/g, ' '),
      });
    }
  }
  return { cards, found };
}

const args = process.argv.slice(2);
const distArg = args.indexOf('--dist');
const distDir = resolve(SITE, distArg === -1 ? 'dist' : args[distArg + 1]);
const sourceDirs = [join(REPO, 'docs'), join(SITE, 'src', 'content')];

const failures = renderFailures(distDir);
const problems = delimiterProblems(sourceDirs);
const mismatches = stylesheetMismatch(distDir);
const glossary = glossaryAsTyped(distDir);

if (
  failures.length === 0 &&
  problems.length === 0 &&
  mismatches.length === 0 &&
  glossary.cards > 0 &&
  glossary.found.length === 0
) {
  console.log(
    'Math renders: no KaTeX parse errors in the build, no stray display\n' +
      `delimiters, no formula printed as typed on the ${glossary.cards} glossary cards or\n` +
      'their symbol index, and the stylesheet matches the markup the renderer emits.',
  );
  process.exit(0);
}

if (failures.length > 0) {
  console.error(
    `\n${failures.length} built page(s) contain a formula KaTeX could not parse.\n` +
      'The page still ships, and everything after the bad block may be swallowed:\n',
  );
  for (const failure of failures) {
    console.error(`  ${failure.file}: ${failure.count} error(s)`);
    for (const message of failure.messages) console.error(`      ${message}`);
  }
}

if (problems.length > 0) {
  console.error(
    `\n${problems.length} display-math delimiter(s) share a line with content.\n` +
      'A `$$` block must open and close on its own line, or the parser runs on\n' +
      'past the end of the formula and eats the rest of the document:\n',
  );
  for (const problem of problems) {
    console.error(`  ${problem.file}:${problem.line}: ${problem.text}`);
  }
}

if (mismatches.length > 0) {
  console.error(
    '\nThe KaTeX stylesheet does not match the markup the renderer emits.\n' +
      'Every formula on the site is missing the rules for the classes below.\n' +
      'site/package.json and the override in site/pnpm-workspace.yaml must both\n' +
      "read `katex` from its catalog entry (`katex: 'catalog:'`); check that\n" +
      'neither was replaced by a literal version. To see which katex the renderer\n' +
      'resolves: `node -e \'console.log(require.resolve("katex", {paths: [require.resolve("rehype-katex")]}))\'`\n' +
      'The classes that do not match:\n',
  );
  for (const mismatch of mismatches) {
    console.error(
      `  ${mismatch.page}: markup emits class="${mismatch.emitted}", ` +
        `stylesheet has ${mismatch.served} (wanted \`${mismatch.wanted}\`)`,
    );
  }
}

if (glossary.cards === 0) {
  console.error(
    '\nThe build has no glossary card (<article class="glossary-term">), so no\n' +
      'card could be read for maths printed as typed. If src/components/Glossary.astro\n' +
      'renamed the class, rename it in glossaryAsTyped() too.',
  );
}

if (glossary.found.length > 0) {
  console.error(
    `\n${glossary.found.length} glossary card(s) or index print a formula as typed, dollar signs\n` +
      'and all. src/components/Glossary.astro typesets a field only through notation();\n' +
      'a field it prints as text shows its TeX:\n',
  );
  for (const { place, text } of glossary.found) console.error(`  ${place}: "${text}"`);
}

process.exit(1);
