// Text a page prints as it is reaches its Markdown copy so that a Markdown
// reader prints it the same: a figure's alt, a clip's and a fiche's title,
// description and caption, a catalogue's label and description, an errata
// family's name. Each is read back with the site's own Markdown pipeline
// (site/scripts/shared/markdown-reader.mjs), not compared with the string the
// writer was meant to write, which would agree with the writer's own idea of
// Markdown. The page is read as the commit holds it, so a checkout with
// carriage returns writes the same copy as one with line feeds.
//
// Usage (from site/, after `pnpm install`): pnpm run test:agent-md
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { before, describe, test } from 'node:test';

import { printed } from '../../../../scripts/shared/markdown-reader.mjs';
import { catalogueItem } from '../../../components/CatalogueIndex.md.mjs';
import { lineStart, literalText, plainText } from '../markdown-table.mjs';
import { readCommittedText } from '../../line-ends.mjs';
import { loadRegistry } from '../registry.mjs';
import { CONTENT_DIR, renderFile } from '../render.mjs';
import { render } from './helpers.mjs';

/** Every inline mark in one text, as a page may print it. */
const MARKED = 'a*wS = SEAT por a*wP, a*_wS, _b_ and __c__, `d`, $e$, ~~f~~, ~2 dB, [0, 1], 20 lg|H|, <g>, <https://x.y>, a\\b, n_1 and n_2';

/** Text that opens a block when it opens a line, as a caption may. */
const OPENERS = ['# Not a heading', '> Not a quotation', '- Not a list', '+ Not a list', '1. Not a list', '2) Not a list', '--- not a rule'];

/** @type {Map<string, import('../types.mjs').ComponentMarkdown>} */
let registry;
before(async () => {
  registry = await loadRegistry();
});

/** Renders with the site's writers. */
const write = (source, options = {}) => render(source, { registry, ...options });

describe('the escapes', () => {
  test('a mark is escaped where it would open markup, and a word keeps its underscores', () => {
    assert.equal(literalText('a*b_c _d_ [e] | `f` $g$ ~h <i> x <'), String.raw`a\*b_c \_d\_ \[e\] \| \`f\` \$g\$ \~h \<i> x \<`);
    assert.equal(literalText('A &amp; B, &#916;L, R&D, A & B &'), String.raw`A \&amp; B, \&#916;L, R&D, A & B \&`);
    assert.equal(plainText('a | b'), 'a | b', 'a table cell leaves the pipe to cell()');
    assert.equal(literalText('6 300 Hz\nand 20 µPa'), '6 300 Hz and 20 µPa', 'the no-break spaces stay');
  });

  test('a line that would open a block opens with its mark escaped', () => {
    for (const opener of OPENERS) assert.match(lineStart(opener), /^\d*\\/u, opener);
    assert.equal(lineStart('Text # with a mark'), 'Text # with a mark');
  });
});

describe('what the copy writes prints as the page prints it', () => {
  test("a figure's alt, whatever marks it holds, in both languages and the alt of a character reference decoded once", async () => {
    for (const lang of ['en', 'es']) {
      const { markdown, issues } = write(`<ThemeImage src="x.svg" alt="${MARKED}" width="94%" />\n`, { lang });
      assert.deepEqual(issues, [], lang);
      const { alts, text } = await printed(markdown);
      assert.deepEqual(alts, [MARKED], lang);
      assert.equal(text, '', lang);
    }
    // MDX reads a character reference in an attribute as Markdown reads it:
    // the writer has the decoded text, and writes it so that it is read once.
    const reference = await printed(write('<ThemeImage src="x.svg" alt="A &amp; B, &#916;L" />\n').markdown);
    assert.deepEqual(reference.alts, ['A & B, ΔL']);
    const twice = await printed(write('<ThemeImage src="x.svg" alt="x &amp;amp; y" />\n').markdown);
    assert.deepEqual(twice.alts, ['x &amp; y'], 'a reference the page prints as written stays written');
    const grouped = await printed(write('<ThemeImage src="x.svg" alt="15 000 m, 1,186 084 kg" />\n', { lang: 'es' }).markdown);
    assert.deepEqual(grouped.alts, ['15 000 m, 1,186 084 kg']);
  });

  test("a clip's and a fiche's title, description and caption, whatever marks they hold", async () => {
    for (const [component, lead] of [['Video', 'Video'], ['ReportPreview', 'Report']]) {
      const { markdown, issues } = write(`<${component} name="n" title="${MARKED}" description="${MARKED}" caption="${MARKED}" />\n`);
      assert.deepEqual(issues, [], component);
      const { text, html } = await printed(markdown);
      assert.equal(text, `${lead}: ${MARKED}: ${MARKED} ${MARKED}`, component);
      assert.equal((html.match(/<p>/g) ?? []).length, 2, `${component}: the line and the caption, each a paragraph`);
      for (const opener of OPENERS) {
        const block = await printed(write(`<${component} name="n" title="T" description="D" caption="${opener}" />\n`).markdown);
        assert.equal(block.text, `${lead}: T: D ${opener}`, `${component}: ${opener}`);
        assert.match(block.html, /^<p>[^]*<\/p>\n<p>[^]*<\/p>$/, `${component}: ${opener} stays a paragraph`);
      }
    }
    const preview = await printed(write(`<ReportPreview name="n" title="${MARKED}" description="${MARKED}" />\n`, { flavour: 'github' }).markdown);
    assert.deepEqual(preview.alts, [`${MARKED}: ${MARKED}`], 'the GitHub edition alt');
  });

  test('a catalogue of the overview, its label and its description', async () => {
    const item = catalogueItem({ label: MARKED, url: 'https://phonometry.dev/reference/catalogues/solids/', count: '3 rows', description: `${MARKED} &amp;` });
    const { text, html } = await printed(item);
    assert.equal(text, `${MARKED} (3 rows): ${MARKED} &amp;`);
    assert.match(html, /^<ul>\n<li><a href="[^"]+">[^]*<\/li>\n<\/ul>$/u);
  });

  test("an errata family's name, linked to its page", async () => {
    const { markdown, issues } = write(`<ErrataFamily slug="ainslie" name="${MARKED}" />\n`);
    assert.deepEqual(issues, []);
    const heading = markdown.split('\n')[0];
    const { html, text } = await printed(heading);
    assert.match(text, new RegExp(`^${MARKED.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')} \\(\\d+ `, 'u'));
    assert.match(html, /^<h3\b[^>]*><a href="[^"]+">/u);
  });
});

describe('an expression of a page', () => {
  test('a name beside comments, line comments among them, prints its value; comments alone print nothing', () => {
    const scope = new Map([['totalChecks', 1897]]);
    for (const written of [
      '{// a note\ntotalChecks}',
      '{totalChecks // a note\n}',
      '{/* a */\n// b\ntotalChecks}',
      '{// a /* b\ntotalChecks}',
      '{/* see http://x */ totalChecks}',
    ]) {
      const { markdown, issues } = render(`It runs ${written} checks.\n`, { scope });
      assert.deepEqual(issues, [], JSON.stringify(written));
      assert.equal(markdown, 'It runs 1897 checks.\n', JSON.stringify(written));
    }
    const { markdown, issues } = render('Gone {// a note\n} here.\n', { scope });
    assert.deepEqual(issues, []);
    assert.equal(markdown, 'Gone  here.\n');
  });
});

describe('a checkout with carriage returns', () => {
  test('writes the copy of a page it writes with line feeds', async (t) => {
    const root = mkdtempSync(join(tmpdir(), 'agent-md-crlf-'));
    t.after(() => rmSync(root, { recursive: true, force: true }));
    for (const [page, lang] of [
      ['es/vibration/structural/building-response.mdx', 'es'],
      ['devices/emission/sound-power.mdx', 'en'],
    ]) {
      // Read as the commit holds it: on a checkout with carriage returns a raw
      // read would already hold them, and the fixture below would double them.
      const text = readCommittedText(join(CONTENT_DIR, page));
      const copies = {};
      for (const [ends, body] of [['lf', text], ['crlf', text.replaceAll('\n', '\r\n')]]) {
        const file = join(root, ends, page);
        mkdirSync(dirname(file), { recursive: true });
        writeFileSync(file, body);
        copies[ends] = (await renderFile(file, { registry, lang })).markdown;
      }
      assert.ok(copies.lf.length > 1000, `${page}: a copy with its text`);
      assert.ok(!copies.crlf.includes('\r'), `${page}: no carriage return reaches the copy`);
      assert.equal(copies.crlf, copies.lf, page);
    }
  });
});
