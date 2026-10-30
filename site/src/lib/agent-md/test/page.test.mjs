// What a page's Markdown copy puts around the body the renderer writes: the
// title, the header and the references, on pages small enough to read.
//
// Usage (from site/, after `pnpm install`): pnpm run test:agent-md
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { describe, test } from 'node:test';

import { printed } from '../../../../scripts/shared/markdown-reader.mjs';
import { releaseHeaderKeys } from '../../page-markdown.mjs';
import { author } from '../../../data/site.mjs';
import { INDEX_URL, LICENSE, header } from '../header.mjs';
import { isCatalogueRoute, otherLanguage, pageMarkdown, referencesMarkdown, titleOf } from '../page.mjs';
import { titleMarkdown } from '../markdown-table.mjs';
import { Box, registryOf } from './helpers.mjs';

const SITE = 'https://docs.jmrp.io/phonometry';

/** Every inline mark in one text, as a page may print it. */
const MARKED = 'a*wS = SEAT por a*wP, a*_wS, _b_ and __c__, `d`, $e$, ~~f~~, ~2 dB, [0, 1], 20 lg|H|, <g>, <https://x.y>, a\\b, n_1 and n_2';

/** Text that opens a block when it opens a line, as a note may. */
const OPENERS = ['# Not a heading', '> Not a quotation', '- Not a list', '+ Not a list', '1. Not a list', '2) Not a list', '--- not a rule'];
const RELEASE = Object.freeze({ version: '4.0.0', install: 'pip install "phonometry[full]"' });

/** Every field the header can state, as a guide in English has them. */
const FULL = Object.freeze({
  lang: /** @type {const} */ ('en'),
  canonical: `${SITE}/signals/filters/filter-banks/`,
  alternate: `${SITE}/es/signals/filters/filter-banks/index.md`,
  release: RELEASE,
  author,
  published: '2026-01-06',
  updated: '2026-10-20',
  standards: ['IEC 61260-1:2014', 'ANSI S1.11-2004'],
  summary: 'Fractional-octave band mathematics and the octave_filter parameters.',
});

describe('the header', () => {
  test('states, in this order, where the page lives, its release, author, dates, standards, licence and summary', () => {
    assert.equal(
      header(FULL),
      [
        `> One page of the phonometry documentation, as Markdown. Index: ${INDEX_URL}`,
        '',
        `Canonical: ${SITE}/signals/filters/filter-banks/`,
        'Language: en',
        `Alternate: ${SITE}/es/signals/filters/filter-banks/index.md`,
        'Version: phonometry 4.0.0',
        'Install: pip install "phonometry[full]"',
        'Author: José Manuel Requena Plens (https://orcid.org/0000-0003-1250-6212)',
        'Published: 2026-01-06',
        'Updated: 2026-10-20',
        'Standards: IEC 61260-1:2014; ANSI S1.11-2004',
        `License: ${LICENSE}`,
        'Summary: Fractional-octave band mathematics and the octave_filter parameters.',
        '',
        '---',
      ].join('\n'),
    );
  });

  test('keeps its keys in English and says the rest in the page language', () => {
    const text = header({ ...FULL, lang: 'es' });
    assert.match(text, /^> Una página de la documentación de phonometry, en Markdown\. Índice: /u);
    assert.match(text, /^Language: es$/mu);
    assert.match(text, /^Canonical: /mu);
  });

  test('leaves out a line whose value is unknown rather than printing it empty', () => {
    const text = header({ lang: 'en', canonical: `${SITE}/x/`, release: RELEASE });
    assert.deepEqual(
      text.split('\n').filter((one) => /^[A-Z][A-Za-z]*: /u.test(one)).map((one) => one.split(':')[0]),
      ['Canonical', 'Language', 'Version', 'Install', 'License'],
    );
    assert.doesNotMatch(text, /: $/mu);
  });

  test('a catalogue carries no licence of its own', () => {
    assert.doesNotMatch(header({ ...FULL, license: false }), /^License:/mu);
  });

  test('lists its documents with "; " between them, since a designation can hold a comma of its own', () => {
    const standards = ['JCGM 100:2008, the GUM', 'JCGM 101:2008'];
    assert.match(header({ ...FULL, standards }), /^Standards: JCGM 100:2008, the GUM; JCGM 101:2008$/mu);
    const verified = { checks: 7, designations: standards, url: `${SITE}/reference/conformance/#uncertainty` };
    assert.match(header({ ...FULL, verified }), /^Verified: 7 conformance checks \(JCGM 100:2008, the GUM; JCGM 101:2008\) /mu);
  });

  test('a description that wraps is one line', () => {
    assert.match(header({ ...FULL, summary: 'One\n  line,\tno more.' }), /^Summary: One line, no more\.$/mu);
  });

  test('the Verified line states the checks, the documents and the section of the report, in each language', () => {
    const verified = { checks: 42, designations: ['IEC 61260-1:2014'], url: `${SITE}/reference/conformance/#filters` };
    assert.match(
      header({ ...FULL, verified }),
      /^Verified: 42 conformance checks \(IEC 61260-1:2014\) https:\/\/docs\.jmrp\.io\/phonometry\/reference\/conformance\/#filters$/mu,
    );
    assert.match(header({ ...FULL, lang: 'es', verified }), /^Verified: 42 comprobaciones de conformidad \(IEC 61260-1:2014\) /mu);
    assert.doesNotMatch(header(FULL), /^Verified:/mu);
  });

  test('a new release changes only the lines releaseHeaderKeys names, so a comparison across releases can leave them out', () => {
    const before = header(FULL).split('\n');
    const after = header({ ...FULL, release: { version: '4.0.1', install: 'pip install "phonometry[full]==4.0.1"' } }).split('\n');
    assert.equal(before.length, after.length);
    const changed = before.filter((one, i) => one !== after[i]).map((one) => one.split(':')[0]);
    assert.deepEqual(changed, [...releaseHeaderKeys]);
  });
});

describe('the references section', () => {
  /** @type {import('../../references-format.mjs').Reference[]} */
  const references = [
    {
      type: 'standard',
      title: 'Electroacoustics: Octave-band filters',
      designation: 'IEC 61260-1:2014',
      organization: 'International Electrotechnical Commission',
      publisher: 'International Electrotechnical Commission',
      year: 2014,
      url: 'https://webstore.iec.ch/en/publication/5063',
      note: 'The band edges of section 1. Index: https://example.org/iec.',
    },
    {
      type: 'book',
      title: 'Psychoacoustics: Facts and *models*',
      authors: ['Fastl, H.', 'Zwicker, E.'],
      publisher: 'Springer',
      edition: '3rd ed.',
      year: 2007,
      doi: '10.1007/978-3-540-68888-4',
    },
    {
      type: 'article',
      title: 'A [bracketed] title',
      authors: ['Smith, J. O.'],
      journal: 'J. Acoust. Soc. Am.',
      volume: 12,
      issue: 3,
      pages: '1-9',
    },
  ];

  test('prints the entries as the page does: APA order, author and year in bold, titles in italics and linked, the note under its entry', () => {
    assert.equal(
      referencesMarkdown(references, 'en'),
      [
        '## References',
        '',
        '- **Fastl, H., & Zwicker, E. (2007).** *Psychoacoustics: Facts and \\*models\\** (3rd ed.). Springer. https://doi.org/10.1007/978-3-540-68888-4',
        '- **International Electrotechnical Commission. (2014).** [*Electroacoustics: Octave-band filters*](https://webstore.iec.ch/en/publication/5063) (IEC 61260-1:2014).',
        '  The band edges of section 1. Index: https://example.org/iec.',
        '- **Smith, J. O. (n.d.).** A \\[bracketed\\] title. *J. Acoust. Soc. Am.*, *12*(3), 1-9.',
      ].join('\n'),
    );
  });

  test('in Spanish, under the Spanish heading, with the Spanish conjunction and no-date label', () => {
    const text = referencesMarkdown(references, 'es');
    assert.match(text, /^## Referencias$/mu);
    assert.match(text, /\*\*Fastl, H\. y Zwicker, E\. \(2007\)\.\*\*/u);
    assert.match(text, /\*\*Smith, J\. O\. \(s\. f\.\)\.\*\*/u);
  });

  test('a page with no references prints no section', () => {
    assert.equal(referencesMarkdown(undefined, 'en'), '');
    assert.equal(referencesMarkdown([], 'en'), '');
  });

  test('a work prints its title and its note as the page prints them, whatever marks they hold', async () => {
    // Read back by the site's own Markdown pipeline, not compared with the
    // string the writer means to write.
    for (const note of [MARKED, ...OPENERS]) {
      const work = { type: 'book', title: MARKED, authors: ['Doe, J.'], year: 2001, publisher: 'A &amp; B', note };
      const { text, html } = await printed(referencesMarkdown([work], 'en'));
      assert.equal(text, `References Doe, J. (2001). ${MARKED}. A &amp; B. ${note}`, note);
      assert.match(html, /^<h2\b[^>]*>References<\/h2>\n<ul>\n<li><strong>[^]*<\/li>\n<\/ul>$/u, `${note}: one item, its note inside it`);
      assert.doesNotMatch(html, /<(?:h1|blockquote|ol|hr)\b|<ul>[^]*<ul>/u, `${note}: no block of its own`);
    }
  });
});

describe('a page', () => {
  test('is titled by the title its head carries, the landing pages\' override included', () => {
    assert.equal(titleOf({ title: 'Filter Banks' }), 'Filter Banks');
    assert.equal(
      titleOf({ title: 'phonometry', head: [{ tag: 'title', content: 'phonometry: acoustics in Python' }] }),
      'phonometry: acoustics in Python',
    );
  });

  test('opens with its title as one heading that prints as the page prints it, whatever marks it holds', async () => {
    for (const title of [MARKED, 'A &amp; B', 'Notes #', 'C# ##', '# Not two headings']) {
      const { html, text } = await printed(titleMarkdown(title));
      assert.equal(text, title, title);
      assert.match(html, /^<h1\b[^]*<\/h1>$/u, `${title}: one heading`);
      assert.equal((html.match(/<h1\b/gu) ?? []).length, 1, `${title}: one heading`);
    }
  });

  test('leaves out the site\'s name an override spells out, as Starlight adds it to every other title', () => {
    assert.equal(titleOf({ title: 'phonometry', head: [{ tag: 'title', content: 'Top-level API | phonometry' }] }), 'Top-level API');
  });

  test('has its counterpart in the other language, the two landing pages each other\'s', () => {
    assert.equal(otherLanguage(''), 'es');
    assert.equal(otherLanguage('es'), '');
    assert.equal(otherLanguage('signals/levels/levels'), 'es/signals/levels/levels');
    assert.equal(otherLanguage('es/signals/levels/levels'), 'signals/levels/levels');
  });

  test('is a catalogue only on the pages of the published catalogues', () => {
    assert.equal(isCatalogueRoute('reference/catalogues/solids'), true);
    assert.equal(isCatalogueRoute('es/reference/catalogues/solids'), true);
    assert.equal(isCatalogueRoute('reference/catalogues'), false);
    assert.equal(isCatalogueRoute('reference/catalogues/not-a-catalogue'), false);
  });

  /**
   * Writes a content directory and returns the copy of one of its pages.
   *
   * @param {import('node:test').TestContext} t
   * @param {Record<string, string>} pages
   * @param {string} path
   * @param {Partial<Parameters<typeof pageMarkdown>[1]>} [options]
   */
  async function copyOf(t, pages, path, options = {}) {
    const root = mkdtempSync(join(tmpdir(), 'agent-md-page-'));
    t.after(() => rmSync(root, { recursive: true, force: true }));
    for (const [name, text] of Object.entries(pages)) {
      mkdirSync(dirname(join(root, name)), { recursive: true });
      writeFileSync(join(root, name), text);
    }
    return pageMarkdown(join(root, path), {
      registry: registryOf(Box),
      contentDir: root,
      dates: { dateOf: () => new Date('2026-10-20T10:00:00Z'), publishedOf: () => '2026-01-06' },
      ...options,
    });
  }

  const GUIDE = [
    '---',
    'title: A guide',
    'description: What the guide is for.',
    'references:',
    '  - type: standard',
    '    title: Octave-band filters',
    '    designation: IEC 61260-1:2014',
    '    organization: IEC',
    '    year: 2014',
    '  - type: standard',
    '    title: Cited only',
    '    designation: ISO 1:2000',
    '    organization: ISO',
    '    implemented: false',
    '---',
    '',
    'The body.',
    '',
    '<Box kind="note">Inside.</Box>',
    '',
  ].join('\n');

  test('opens with its title and header and closes with its references', async (t) => {
    const { route, lang, markdown, issues } = await copyOf(t, { 'a.mdx': GUIDE, 'es/a.mdx': GUIDE }, 'a.mdx');
    assert.deepEqual(issues, []);
    assert.equal(route, 'a');
    assert.equal(lang, 'en');
    const [title, , lead] = markdown.split('\n');
    assert.equal(title, '# A guide');
    assert.match(lead, /^> One page of the phonometry documentation/u);
    assert.ok(markdown.split('\n').includes(`Canonical: ${SITE}/a/`));
    assert.ok(markdown.split('\n').includes(`Alternate: ${SITE}/es/a/index.md`));
    assert.match(markdown, /^Published: 2026-01-06$/mu);
    assert.match(markdown, /^Updated: 2026-10-20$/mu);
    assert.match(markdown, /^Standards: IEC 61260-1:2014$/mu, 'a document the page only cites is not one it implements');
    assert.match(markdown, /^Summary: What the guide is for\.$/mu);
    assert.match(markdown, /---\n\nThe body\.\n\n\[note\]\n\nInside\.\n\n## References\n\n- \*\*IEC\. \(2014\)\.\*\*/u);
    assert.match(markdown, /- \*\*ISO\. \(n\.d\.\)\.\*\* \*Cited only\* \(ISO 1:2000\)\.\n$/u, 'a cited document stays in the references');
  });

  test('writes its title so that it prints as the page prints it', async (t) => {
    const page = GUIDE.replace('title: A guide', 'title: "a*wS = SEAT por a*wP, Notes #"');
    const { markdown } = await copyOf(t, { 'a.mdx': page }, 'a.mdx');
    const [first] = markdown.split('\n');
    assert.equal(first, String.raw`# a\*wS = SEAT por a\*wP, Notes \#`);
    assert.equal((await printed(first)).text, 'a*wS = SEAT por a*wP, Notes #');
  });

  test('names no copy in the other language where the page has no translation', async (t) => {
    const { markdown } = await copyOf(t, { 'a.mdx': GUIDE }, 'a.mdx');
    assert.doesNotMatch(markdown, /^Alternate:/mu);
  });

  test('the landing page lives at the root, and its Spanish twin at /es/', async (t) => {
    const home = '---\ntitle: phonometry\nhead:\n  - tag: title\n    content: "phonometry: acoustics"\n---\n\nHello.\n';
    const { route, markdown } = await copyOf(t, { 'index.mdx': home, 'es/index.mdx': home }, 'index.mdx');
    assert.equal(route, '');
    assert.match(markdown, /^# phonometry: acoustics\n/u);
    assert.ok(markdown.split('\n').includes(`Canonical: ${SITE}/`));
    assert.ok(markdown.split('\n').includes(`Alternate: ${SITE}/es/index.md`));
  });

  test('a catalogue page carries no licence line', async (t) => {
    const { markdown } = await copyOf(t, { 'reference/catalogues/solids.mdx': GUIDE }, 'reference/catalogues/solids.mdx');
    assert.doesNotMatch(markdown, /^License:/mu);
  });

  test('the GitHub flavour has no header block', async (t) => {
    const { markdown } = await copyOf(t, { 'a.mdx': GUIDE }, 'a.mdx', { flavour: 'github' });
    assert.match(markdown, /^# A guide\n\nThe body\./u);
    assert.doesNotMatch(markdown, /^Canonical:/mu);
  });

  test('without git there is no date line rather than a guessed one', async (t) => {
    const { markdown } = await copyOf(t, { 'a.mdx': GUIDE }, 'a.mdx', { dates: undefined });
    assert.doesNotMatch(markdown, /^(?:Published|Updated):/mu);
  });

  test('the Verified line comes from whoever knows what the page states', async (t) => {
    const verified = () => ({ checks: 3, designations: ['IEC 61260-1:2014'], url: `${SITE}/reference/conformance/#f` });
    const { markdown } = await copyOf(t, { 'a.mdx': GUIDE }, 'a.mdx', { verified });
    assert.match(markdown, /^Verified: 3 conformance checks /mu);
  });
});
