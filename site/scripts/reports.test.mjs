// The index of the fiches lists only what a guide renders.
//
// src/data/reports.mjs reads each guide's `<ReportPreview>` tags off its text
// and refuses to build when a shipped fiche is shown by no guide. It read the
// text as written, so a guide that only quoted the tag, in a fence, a code
// span, a comment or its frontmatter, counted as showing the fiche: the check
// passed and the index linked a guide that does not show it. The module reads
// the page as the site renders it now (pageMarkup of shared/markdown-spans.mjs).
//
// Each test writes a repository of one fiche and one guide in both languages
// into a directory of its own, with the module and the readers it imports
// beside it, and imports the module there.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';

const SITE = join(dirname(fileURLToPath(import.meta.url)), '..');
/** The module and the readers it imports, by their place under the site. */
const MODULES = ['src/data/reports.mjs', 'scripts/shared/markdown-spans.mjs', 'src/lib/markdown-fences.mjs', 'src/lib/line-ends.mjs'];

/** Import the reports module in a repository whose one guide is `guide` and whose fiches are `fiches`. */
async function reportsOf(t, guide, fiches = ['iso_x']) {
  const root = mkdtempSync(join(tmpdir(), 'reports-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  writeFileSync(join(root, 'VERSION'), '4.0.0\n');
  mkdirSync(join(root, '.github', 'reports'), { recursive: true });
  for (const fiche of fiches) writeFileSync(join(root, '.github', 'reports', `${fiche}.pdf`), '');
  for (const language of ['', 'es']) {
    const dir = join(root, 'site', 'src', 'content', 'docs', language, 'guides');
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, 'guide.mdx'), guide);
  }
  for (const module of MODULES) {
    mkdirSync(dirname(join(root, 'site', module)), { recursive: true });
    copyFileSync(join(SITE, module), join(root, 'site', module));
  }
  return import(pathToFileURL(join(root, 'site', 'src', 'data', 'reports.mjs')).href);
}

const FICHE = '<ReportPreview name="iso_x" title="A fiche" description="What it shows" />';

test('every fiche a guide renders is listed from a checkout with carriage returns', async (t) => {
  // A clone made with core.autocrlf=true writes a carriage return before each
  // line feed. The sound power guide's blank lines were then read as text, so
  // its code examples ran into its prose as one paragraph, a closing fence
  // opened a code span, and the fiche after it was shown by no guide.
  const guide = readFileSync(join(SITE, 'src', 'content', 'docs', 'devices', 'emission', 'sound-power-pressure.mdx'), 'utf8');
  const fiches = [...guide.matchAll(/<ReportPreview\s+name="([^"]+)"/g)].map((found) => found[1]);
  assert.ok(fiches.length >= 2, 'the guide renders its fiches');
  const { reports } = await reportsOf(t, guide.replace(/\r?\n/g, '\r\n'), fiches);
  assert.deepEqual(reports.map((report) => report.name).sort(), [...fiches].sort());
});

test('a fiche a guide renders is listed with that guide', async (t) => {
  const { reports, reportsEs } = await reportsOf(t, `---\ntitle: Guide\n---\n\n${FICHE}\n`);
  assert.deepEqual(
    reports.map((report) => [report.name, report.page, report.title]),
    [['iso_x', '/phonometry/guides/guide/', 'A fiche']],
  );
  assert.deepEqual(reportsEs.map((report) => report.page), ['/phonometry/es/guides/guide/']);
});

test('a fiche a guide only quotes is shown by no guide, and the module refuses to build', async (t) => {
  const quoted = {
    'a fence': `\`\`\`mdx\n${FICHE}\n\`\`\`\n`,
    'a code span': `Show one with \`${FICHE}\` in the guide.\n`,
    'a comment': `{/* ${FICHE} */}\n`,
    'an expression': `<code>{'${FICHE}'}</code>\n`,
    'a backslash': `Write \\${FICHE} to show one.\n`,
  };
  for (const [where, body] of Object.entries(quoted)) {
    await assert.rejects(reportsOf(t, `---\ntitle: Guide\n---\n\n${body}`), /shipped and shown by no guide: iso_x/, where);
  }
  await assert.rejects(
    reportsOf(t, `\n---\ntitle: Guide\ndescription: '${FICHE}'\n---\n\nNo fiche.\n`),
    /shipped and shown by no guide: iso_x/,
    'the frontmatter',
  );
});
