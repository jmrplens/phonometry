// What the bibliography page lists, read on content trees small enough to see
// whole.
//
// The page's lists are written from the references of every page when the
// site is built (src/lib/bibliography-entries.mjs, src/lib/remark-bibliography.mjs),
// and the real build only ever hands that code the works the guides cite
// today, each already in the data it reads. A work cited by a new page, a note
// left behind by a work no page cites any more, a Spanish page that describes
// one work two ways or a section the page forgot to mark would build green
// there whatever the code did with it. Each test here hands the functions such
// a tree and reads what comes back; the last ones run the remark plugin through
// the Markdown processor Astro builds the page with, and read the HTML.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { test } from 'node:test';

import { createMarkdownProcessor } from '@astrojs/markdown-remark';
import remarkMath from 'remark-math';

import { BIBLIOGRAPHY_PREFIXES, BIBLIOGRAPHY_SECTIONS, BIBLIOGRAPHY_WORKS } from '../src/data/bibliography.mjs';
import { topics } from '../src/data/topics.mjs';
import { citedWorks } from '../src/lib/citations.mjs';
import { plainText as mathsText } from '../src/lib/maths-text.mjs';
import {
  bibliographySections,
  describedWorks,
  englishWorkIds,
  MARKER,
  navigationOrder,
  noteText,
  sectionMarkdown,
  withSections,
} from '../src/lib/bibliography-entries.mjs';
import { remarkBibliography, withBibliographyLists } from '../src/lib/remark-bibliography.mjs';
import { printed } from './shared/markdown-reader.mjs';

const EN = 'https://example.org/docs/reference/bibliography/';
const ES = 'https://example.org/docs/es/reference/bibliography/';

const SECTIONS = [{ key: 'general' }, { key: 'signals' }, { key: 'rooms' }];
const PREFIXES = [
  ['signals', 'signals'],
  ['buildings', 'rooms'],
  ['buildings/insulation', 'general'],
];

const iso = (designation, extra = {}) => ({
  type: 'standard',
  organization: 'International Organization for Standardization',
  designation,
  title: `Title of ${designation}`,
  year: Number(designation.slice(-4)),
  ...extra,
});
const book = {
  type: 'book',
  authors: ['Doe, J.'],
  year: 2001,
  title: 'A book',
  publisher: 'A Press',
  doi: '10.1000/book',
};

/** The options every call takes, over the ones a test gives. */
const options = (extra = {}) => ({
  lang: 'en',
  bibliographyUrl: EN,
  englishUrl: EN,
  sections: SECTIONS,
  prefixes: PREFIXES,
  works: {},
  navigation: ['signals/b', 'signals/a', 'buildings/rooms/c'],
  base: '/docs',
  ...extra,
});

const entriesOf = (sections) => sections.flatMap((section) => section.entries.map((entry) => [section.key, entry]));

test('every work the pages cite gets one entry, with every page that cites it in the order of the sidebar', () => {
  const pages = [
    { id: 'signals/a', title: 'Page A', references: [iso('ISO 1:2000'), book] },
    { id: 'signals/b', title: 'Page B', references: [book, { ...book, note: 'Another note.' }] },
    { id: 'buildings/rooms/c', title: 'Page C', references: [iso('ISO 1:2000', { note: 'Its own note.' })] },
  ];
  const entries = entriesOf(bibliographySections(pages, options()));
  assert.deepEqual(
    entries.map(([, entry]) => [entry.fragment, entry.citedBy.map((page) => page.href)]),
    [
      ['doi-10-1000-book', ['/docs/signals/b/', '/docs/signals/a/']],
      ['std-iso-1-2000', ['/docs/signals/a/', '/docs/buildings/rooms/c/']],
    ],
  );
  assert.deepEqual(
    entries.map(([, entry]) => entry.citedBy.map((page) => page.title)),
    [['Page B', 'Page A'], ['Page A', 'Page C']],
  );
});

test('a work with nothing written of it sits where most of its citing pages are, by the longest prefix', () => {
  const pages = [
    { id: 'signals/a', title: 'A', references: [iso('ISO 1:2000'), iso('ISO 2:2000'), iso('ISO 4:2000')] },
    { id: 'buildings/rooms/c', title: 'C', references: [iso('ISO 1:2000'), iso('ISO 2:2000')] },
    { id: 'buildings/rooms/d', title: 'D', references: [iso('ISO 2:2000')] },
    { id: 'buildings/insulation/e', title: 'E', references: [iso('ISO 3:2000')] },
    { id: 'reference/catalogues/f', title: 'F', references: [iso('ISO 5:2000')] },
  ];
  const where = Object.fromEntries(
    entriesOf(bibliographySections(pages, options())).map(([key, entry]) => [entry.fragment, key]),
  );
  assert.deepEqual(where, {
    // One page each way: the earlier section.
    'std-iso-1-2000': 'signals',
    // Two rooms pages against one signals page.
    'std-iso-2-2000': 'rooms',
    // `buildings/insulation` is longer than `buildings`.
    'std-iso-3-2000': 'general',
    'std-iso-4-2000': 'signals',
    // No prefix: the first section.
    'std-iso-5-2000': 'general',
  });
});

test("a work's section and note are the data's, in the page's language, and a work with no note has none", () => {
  const pages = [
    { id: 'signals/a', title: 'A', references: [iso('ISO 1:2000'), book] },
    { id: 'es/signals/a', title: 'A', references: [iso('ISO 1:2000'), book] },
  ];
  const works = { 'std-iso-1-2000': { section: 'rooms', note: { en: 'Why it matters.', es: 'Por qué importa.' } } };
  const english = entriesOf(bibliographySections(pages, options({ works })));
  const spanish = entriesOf(bibliographySections(pages, options({ works, lang: 'es', bibliographyUrl: ES })));
  assert.deepEqual(
    english.map(([key, entry]) => [key, entry.fragment, entry.note]),
    [
      ['signals', 'doi-10-1000-book', undefined],
      ['rooms', 'std-iso-1-2000', 'Why it matters.'],
    ],
  );
  assert.deepEqual(
    spanish.map(([key, entry]) => [key, entry.note, entry.citedBy.map((page) => page.href)]),
    [
      ['signals', undefined, ['/docs/es/signals/a/']],
      ['rooms', 'Por qué importa.', ['/docs/es/signals/a/']],
    ],
  );
});

test('a note left for a work no page cites, or a section the page does not have, stops the build', () => {
  const pages = [{ id: 'signals/a', title: 'A', references: [iso('ISO 1:2000')] }];
  const works = {
    'std-iso-9-1999': { note: { en: 'A work nobody cites any more.' } },
    'std-iso-1-2000': { section: 'nowhere' },
  };
  assert.throws(
    () => bibliographySections(pages, options({ works })),
    (error) =>
      /describes std-iso-9-1999, which no English page cites/.test(error.message) &&
      /puts std-iso-1-2000 in a section the page does not have, nowhere/.test(error.message),
  );
});

test('a page that cites a work and has no title to be named by stops the build', () => {
  const pages = [{ id: 'signals/a', references: [iso('ISO 1:2000')] }];
  assert.throws(() => bibliographySections(pages, options()), /signals\/a cites std-iso-1-2000 and has no title/);
});

test("a work's description in the structured data is the bibliography's own note when it has one, as plain text, and the citing page's otherwise", () => {
  const pages = [
    {
      id: 'signals/a',
      title: 'A',
      references: [iso('ISO 1:2000', { note: 'What page A says of the standard.' }), { ...book, note: 'What page A says of the book.' }],
    },
    { id: 'es/signals/a', title: 'A', references: [iso('ISO 1:2000', { note: 'Lo que dice la página.' }), book] },
  ];
  const note =
    'Why it matters: `level()` reads $L_{p}$, as the [list](https://example.org/list/) says, printed in the *Journal* and **its** \\*errata\\* &amp; notes.';
  const works = {
    'std-iso-1-2000': { note: { en: note, es: 'Por qué importa: lo lee `level()`, como dice el *Manual* (Xiang, *Digital Sequences*).' } },
  };
  for (const [lang, url, said] of [
    ['en', EN, `Why it matters: level() reads ${mathsText('$L_{p}$')}, as the list says, printed in the Journal and its *errata* & notes.`],
    ['es', ES, 'Por qué importa: lo lee level(), como dice el Manual (Xiang, Digital Sequences).'],
  ]) {
    const own = pages.filter((page) => page.id.startsWith('es/') === (lang === 'es'));
    const sections = bibliographySections(pages, options({ lang, bibliographyUrl: url, works }));
    const described = describedWorks(citedWorks(own, url), sections);
    assert.equal(described.get(`${url}#std-iso-1-2000`).note, said, `${lang}: the data's note, as plain text`);
    assert.equal(described.get(`${url}#std-iso-1-2000`).designation, 'ISO 1:2000', `${lang}: the rest of the reference is the page's`);
    const bookId = [...described.keys()].find((id) => id !== `${url}#std-iso-1-2000`);
    assert.equal(described.get(bookId).note, lang === 'en' ? 'What page A says of the book.' : undefined, `${lang}: no note in the data, the page's`);
  }
});

test('two pages that describe one work two ways stop the build, as the structured data does', () => {
  const pages = [
    { id: 'signals/a', title: 'A', references: [iso('ISO 1:2000', { url: 'https://example.org/1' })] },
    { id: 'signals/b', title: 'B', references: [iso('ISO 1:2000', { url: 'https://example.org/2' })] },
  ];
  assert.throws(() => bibliographySections(pages, options()), /#std-iso-1-2000 url/);
});

test('a Spanish work reads the English data by the English work it is, whatever its own fragment', () => {
  const report = (title) => ({ type: 'report', organization: 'A Society', year: 2019, title });
  const pages = [
    { id: 'signals/a', title: 'A', references: [iso('ISO 1:2000'), report('Handbook, SI edition'), book] },
    {
      id: 'es/signals/a',
      title: 'A',
      references: [iso('ISO 1:2000', { designation: 'ISO 1:2000 (edición inglesa)' }), report('Handbook, edición SI'), book],
    },
    { id: 'signals/b', title: 'B', references: [iso('ISO 1:2000')] },
    { id: 'es/signals/b', title: 'B', references: [iso('ISO 1:2000', { designation: 'ISO 1:2000 (edición inglesa)' })] },
  ];
  const pairs = englishWorkIds(pages, ES, EN);
  assert.equal(pairs.get(`${ES}#std-iso-1-2000-edicion-inglesa`), `${EN}#std-iso-1-2000`);
  assert.equal(
    pairs.get(`${ES}#report-a-society-2019-handbook-edicion-si`),
    `${EN}#report-a-society-2019-handbook-si-edition`,
  );
  assert.equal(pairs.get(`${ES}#doi-10-1000-book`), `${EN}#doi-10-1000-book`);
  const works = {
    'std-iso-1-2000': { note: { es: 'Nota.' } },
    'report-a-society-2019-handbook-si-edition': { section: 'rooms', note: { es: 'Otra nota.' } },
  };
  const spanish = entriesOf(bibliographySections(pages, options({ works, lang: 'es', bibliographyUrl: ES })));
  assert.deepEqual(
    spanish.map(([key, entry]) => [key, entry.fragment, entry.note]),
    [
      ['signals', 'doi-10-1000-book', undefined],
      ['signals', 'std-iso-1-2000-edicion-inglesa', 'Nota.'],
      ['rooms', 'report-a-society-2019-handbook-edicion-si', 'Otra nota.'],
    ],
  );
});

test('two Spanish descriptions of one English work stop the build, naming both', () => {
  const report = (title) => ({ type: 'report', organization: 'A Society', year: 2019, title });
  const pages = [
    { id: 'signals/a', title: 'A', references: [report('Handbook')] },
    { id: 'signals/b', title: 'B', references: [report('Handbook')] },
    { id: 'es/signals/a', title: 'A', references: [report('Manual')] },
    { id: 'es/signals/b', title: 'B', references: [report('Manual técnico')] },
  ];
  assert.throws(
    () => englishWorkIds(pages, ES, EN),
    /report-a-society-2019-manual and report-a-society-2019-manual-tecnico are both report-a-society-2019-handbook/,
  );
});

test('two translated works swapped on the Spanish twin pair with no English work and stop the build, naming both', () => {
  const report = (organization, year, title) => ({ type: 'report', organization, year, title });
  const pages = [
    { id: 'signals/a', title: 'A', references: [report('Org A', 2001, 'Alpha report'), report('Org B', 2002, 'Beta report')] },
    { id: 'es/signals/a', title: 'A', references: [report('Org B', 2002, 'Informe beta'), report('Org A', 2001, 'Informe alfa')] },
  ];
  assert.throws(
    () => englishWorkIds(pages, ES, EN),
    (error) =>
      /report-org-b-2002-informe-beta stands where the English twin cites report-org-a-2001-alpha-report/.test(error.message) &&
      /report-org-a-2001-informe-alfa stands where the English twin cites report-org-b-2002-beta-report/.test(error.message),
  );
  const doi = (value, title) => ({ type: 'book', authors: ['Doe, J.'], year: 2001, title, publisher: 'P', doi: value });
  assert.throws(
    () =>
      englishWorkIds(
        [
          { id: 'signals/a', title: 'A', references: [{ ...doi('10.1/a', 'A book'), url: 'https://example.org/a' }] },
          { id: 'es/signals/a', title: 'A', references: [{ ...doi(undefined, 'Un libro'), url: 'https://example.org/b' }] },
        ],
        ES,
        EN,
      ),
    /stands where the English twin cites doi-10-1-a/,
  );
});

test('a section is written as the References section of every page writes a work, then its note and its pages', () => {
  const pages = [
    { id: 'signals/a', title: 'Page [A]', references: [book] },
    { id: 'signals/b', title: 'Page B', references: [book] },
    { id: 'buildings/rooms/c', title: 'Page C', references: [book] },
  ];
  const works = { 'doi-10-1000-book': { note: { en: 'Chapter 2,\n  with $x^2$.', es: 'Capítulo 2.' } } };
  const english = bibliographySections(pages, options({ works })).find((section) => section.entries.length > 0);
  assert.equal(
    sectionMarkdown(english, 'en'),
    '- **Doe, J. (2001).** *A book*. A Press. https://doi.org/10.1000/book\n' +
      '  Chapter 2, with $x^2$.\n' +
      '  Cited by [Page B](/docs/signals/b/), [Page \\[A\\]](/docs/signals/a/) and [Page C](/docs/buildings/rooms/c/).',
  );
  const one = { ...english, entries: [{ ...english.entries[0], note: undefined, citedBy: english.entries[0].citedBy.slice(0, 1) }] };
  assert.equal(
    sectionMarkdown(one, 'es', { href: (page) => `https://example.org${page.href}` }),
    '- **Doe, J. (2001).** *A book*. A Press. https://doi.org/10.1000/book\n' +
      '  Citado por [Page B](https://example.org/docs/signals/b/).',
  );
});

test("the title of a page in a Cited by list prints as the page prints it, whatever marks it holds", async () => {
  // A page's title is text the page prints as it is; written into the link
  // bare, its `*`, `_`, `$`, `~~`, `<` or `&amp;` would print as emphasis,
  // maths, strikethrough, a tag or an ampersand instead.
  const title = 'a*wS = SEAT por a*wP, a*_wS, _b_ and __c__, `d`, $e$, ~~f~~, [0, 1], 20 lg|H|, <g>, A &amp; B, n_1 and n_2';
  const pages = [
    { id: 'signals/a', title, references: [book] },
    { id: 'signals/b', title: 'Page B', references: [book] },
  ];
  const section = bibliographySections(pages, options()).find(({ entries }) => entries.length > 0);
  const { text, html } = await printed(sectionMarkdown(section, 'en'));
  assert.equal(text, `Doe, J. (2001). A book. A Press. https://doi.org/10.1000/book Cited by Page B and ${title}.`);
  assert.match(html, /^<ul>\n<li>[^]*<\/li>\n<\/ul>$/, 'one entry, its list inside it');
  assert.equal((html.match(/<a\b/g) ?? []).length, 3, 'the DOI and the two pages, each one link');
});

test('the sidebar order reads every slug of the topics, in groups and out', () => {
  const order = navigationOrder([
    { items: ['a', { slug: 'b', label: 'B' }, { label: 'Group', items: ['c', { label: 'Inner', items: [{ slug: 'd' }] }] }] },
    { link: '/e/' },
    { items: ['f'] },
  ]);
  assert.deepEqual(order, ['a', 'b', 'c', 'd', 'f']);
  assert.ok(navigationOrder(topics).includes('reference/bibliography'));
});

test('a marker is a comment of its own naming one section', () => {
  assert.equal(MARKER.exec('<!-- bibliography: signal-analysis -->')?.[1], 'signal-analysis');
  assert.equal(MARKER.exec('<!--bibliography:files-->')?.[1], 'files');
  assert.equal(MARKER.exec('<!-- bibliography: Signal Analysis -->'), null);
  assert.equal(MARKER.exec('text <!-- bibliography: files -->'), null);
  assert.equal(MARKER.exec('<!--\nbibliography: files\n-->'), null);
  assert.equal(MARKER.exec('<!-- bibliography:\nfiles -->'), null);
});

test('the Markdown writers fill a marker on a line of its own, and leave one split over lines or shown in a fence as written', () => {
  const sections = [{ key: 'signals', entries: [] }];
  const split = '<!--\nbibliography: signals\n-->\n';
  assert.equal(withSections(split, sections, 'en'), split);
  const fenced = '# Guide\n\n```markdown\n<!-- bibliography: example -->\n```\n\n~~~\n<!-- bibliography: signals -->\n~~~\n';
  assert.equal(withSections(fenced, sections, 'en'), fenced);
  assert.equal(withSections('Intro.\n\n  <!-- bibliography: signals -->  \n', sections, 'en'), 'Intro.\n\n\n');
  assert.throws(() => withSections('<!-- bibliography: example -->\n', sections, 'en'), /marks a section its data does not have, example/);
});

test("the site's own data names only works its pages cite, in sections the page has, with both languages' notes", async () => {
  const { readPageReferences } = await import('../src/lib/page-references.mjs');
  const pages = await readPageReferences(new URL('../src/content/docs', import.meta.url).pathname);
  const english = bibliographySections(pages, {
    ...options(),
    sections: BIBLIOGRAPHY_SECTIONS,
    prefixes: BIBLIOGRAPHY_PREFIXES,
    works: BIBLIOGRAPHY_WORKS,
    navigation: navigationOrder(topics),
  });
  const notes = Object.values(BIBLIOGRAPHY_WORKS).filter((record) => record.note);
  assert.ok(notes.every((record) => record.note.en && record.note.es), 'a note in one language only');
  assert.ok(english.flatMap((section) => section.entries).length > Object.keys(BIBLIOGRAPHY_WORKS).length);
});

// The remark plugin, through the processor Astro builds the page with.

/** A content tree in a directory of its own, removed when the test ends, with `files` (path to text) in it. */
function tree(t, files) {
  const root = mkdtempSync(join(tmpdir(), 'bibliography-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const docs = join(root, 'src', 'content', 'docs');
  for (const [path, text] of Object.entries(files)) {
    mkdirSync(dirname(join(docs, path)), { recursive: true });
    writeFileSync(join(docs, path), text);
  }
  return docs;
}

const guide = (title, references) => `---\ntitle: ${title}\nreferences: ${JSON.stringify(references)}\n---\n\nText.\n`;

/** Render the bibliography page of `docs` as the build does, with `data` for the sections, prefixes and works. */
async function render(docs, page, data) {
  const processor = await createMarkdownProcessor({ remarkPlugins: [remarkMath, [remarkBibliography, data]] });
  const file = join(docs, 'reference', 'bibliography.md');
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, page);
  return (await processor.render(page, { fileURL: pathToFileURL(file) })).code;
}

const DATA = {
  sections: [{ key: 'general' }, { key: 'signals' }],
  prefixes: [['signals', 'signals']],
  works: { 'doi-10-1000-book': { section: 'general', note: { en: 'The book, with $x^2$ and `code`.' } } },
};

test('the plugin puts each section where the page marks it, every item carrying its work and its pages', async (t) => {
  const docs = tree(t, {
    'signals/a.md': guide('Page A', [book, iso('ISO 1:2000')]),
    'signals/b.md': guide('Page B', [iso('ISO 1:2000')]),
  });
  const html = await render(
    docs,
    '# Bibliography\n\n## General\n\nIntro.\n\n<!-- bibliography: general -->\n\n## Signals\n\n<!-- bibliography: signals -->\n',
    DATA,
  );
  assert.doesNotMatch(html, /bibliography:/);
  assert.match(html, /<li id="doi-10-1000-book">/);
  assert.match(html, /<li id="std-iso-1-2000">/);
  assert.match(html, /<span class="katex"|<code>code<\/code>/);
  const [, cited] = html.match(/<li id="std-iso-1-2000">[\s\S]*?<span data-cited-by="">([\s\S]*?)<\/span>/);
  assert.deepEqual(
    [...cited.matchAll(/href="([^"]+)"/g)].map(([, href]) => href),
    ['/phonometry/signals/a/', '/phonometry/signals/b/'],
  );
  assert.ok(html.indexOf('id="doi-10-1000-book"') < html.indexOf('<h2 id="signals"') || !html.includes('<h2 id="signals"'));
});

test('a page that leaves a section with works unmarked, marks one twice or marks one the data lacks stops the build', async (t) => {
  const docs = tree(t, { 'signals/a.md': guide('Page A', [book, iso('ISO 1:2000')]) });
  await assert.rejects(render(docs, '## General\n\n<!-- bibliography: general -->\n', DATA), /leaves the section signals unmarked, so its 1 work\(s\) have no entry/);
  await assert.rejects(
    render(docs, '<!-- bibliography: general -->\n\n<!-- bibliography: signals -->\n\n<!-- bibliography: signals -->\n', DATA),
    /marks the section signals twice/,
  );
  await assert.rejects(
    render(docs, '<!-- bibliography: general -->\n\n<!-- bibliography: signals -->\n\n<!-- bibliography: elsewhere -->\n', DATA),
    /marks a section src\/data\/bibliography\.mjs does not have, elsewhere/,
  );
});

test('the plugin reads a marker split over lines as no marker, as the Markdown writers do, so its section is left unmarked', async (t) => {
  const docs = tree(t, { 'signals/a.md': guide('Page A', [book, iso('ISO 1:2000')]) });
  await assert.rejects(
    render(docs, '<!-- bibliography: general -->\n\n<!--\nbibliography: signals\n-->\n', DATA),
    /leaves the section signals unmarked, so its 1 work\(s\) have no entry/,
  );
});

test('the plugin leaves every other page as it is', async (t) => {
  const docs = tree(t, { 'signals/a.md': guide('Page A', [book]) });
  const processor = await createMarkdownProcessor({ remarkPlugins: [[remarkBibliography, DATA]] });
  const file = join(docs, 'signals', 'a.md');
  const { code } = await processor.render('<!-- bibliography: general -->\n\nText.\n', { fileURL: pathToFileURL(file) });
  assert.match(code, /<!-- bibliography: general -->/);
});

test('a copy fills the markers of the two bibliography pages only, and writes a guide that shows one as written', () => {
  const sections = [{ key: 'general', entries: [] }];
  const sectionsOf = () => sections;
  const guidePage = '# Guide\n\n```markdown\n<!-- bibliography: example -->\n```\n\n<!-- bibliography: general -->\n';
  assert.equal(withBibliographyLists(guidePage, '/r/site/src/content/docs/signals/guide.mdx', sectionsOf), guidePage);
  assert.equal(withBibliographyLists(guidePage, '/r/site/src/content/docs/es/reference/glossary.mdx', sectionsOf), guidePage);
  const marked = 'Intro.\n\n<!-- bibliography: general -->\n';
  assert.equal(withBibliographyLists(marked, '/r/site/src/content/docs/reference/bibliography.md', sectionsOf), 'Intro.\n\n\n');
  assert.equal(withBibliographyLists(marked, 'C:\\r\\site\\src\\content\\docs\\es\\reference\\bibliography.md', sectionsOf), 'Intro.\n\n\n');
});

test('a list the page writes itself, an entry added by hand, stops the build, wherever it sits', async (t) => {
  const docs = tree(t, { 'signals/a.md': guide('Page A', [book, iso('ISO 1:2000')]) });
  const marked = '<!-- bibliography: general -->\n\n## Signals\n\n<!-- bibliography: signals -->\n';
  await assert.rejects(
    render(
      docs,
      `## General\n\n${marked}\n- **Reviewer, C. (2003).** *A work written into the page by hand*. Wiley.\n  Cited by [Page A](/phonometry/signals/a/).\n`,
      DATA,
    ),
    /holds a list src\/data\/bibliography\.mjs did not write, from "Reviewer, C\. \(2003\)\. A work written into the page by hand\. Wiley\./,
  );
  await assert.rejects(
    render(docs, `${marked}\n> 1. A numbered entry, quoted.\n`, DATA),
    /holds a list src\/data\/bibliography\.mjs did not write, from "A numbered entry, quoted\."/,
  );
});

test('a note keeps a code span and an escaped dollar as written, and writes out only its maths', () => {
  assert.equal(noteText('Use `$L_{p}$` for literal TeX.'), 'Use $L_{p}$ for literal TeX.');
  assert.equal(noteText('Priced at \\$5 and \\$10.'), 'Priced at $5 and $10.');
  assert.equal(noteText('The level $L_{p}$ and `code`.'), `The level ${mathsText('$L_{p}$')} and code.`);
  // A command inside maths is maths: read by the maths reader, not held back
  // as an escaped character (`\mathrm` is no escape of `m`).
  assert.equal(noteText('Uses $L_{p\\mathrm{AF}}$ levels.'), 'Uses LpAF levels.');
  assert.equal(noteText('$a\\,b$ costs \\$5.'), `${mathsText('$a\\,b$')} costs $5.`);
});
