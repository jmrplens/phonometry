// The Markdown copy of a page with no docs/ mirror keeps what the page shows.
//
// emit-page-markdown.mjs wrote that copy by taking the MDX machinery out with
// patterns over the page as written, so it took an `import` line of a code
// example for the page's own import and dropped it, and took a `<NC-15` in a
// code span for a component and dropped everything from it to the next `/>`.
// The copy is read as the site renders the page now (pageMarkup of
// markdown-spans.mjs): what it takes out is what the page renders as markup.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  catalogueItem,
  copyDefects,
  figureMarkdown,
  frontmatterSource,
  pageImports,
  referencesMarkdown,
  stripFrontmatter,
  stripMdx,
  titleMarkdown,
} from './page-twin.mjs';
import { printed } from './markdown-reader.mjs';

const FENCE = '```';

test("the page's own imports and components go, and a wrapper keeps its children", () => {
  const page = [
    "import Video from '../../components/Video.astro';",
    "import { Aside } from '@astrojs/starlight/components';",
    '',
    'A clip:',
    '',
    '<Video name="anim_fdtd_room" />',
    '',
    '<Aside type="note">',
    'Read this.',
    '</Aside>',
  ].join('\n');
  assert.equal(stripMdx(page), 'A clip:\n\nRead this.');
});

test('the import lines of a code example stay, on an .mdx page and on an .md page', () => {
  const example = [`${FENCE}python`, 'import phonometry', 'from phonometry import filters', '', `${FENCE}`].join('\n');
  for (const kind of ['mdx', 'md']) {
    assert.equal(stripMdx(`Run it:\n\n${example}\n`, { kind }), `Run it:\n\n${example}`, kind);
  }
});

test('a component written in a code span or a fence stays as the page shows it', () => {
  // The shape of the room-noise guide: a `<NC-15` in a code span, and a
  // component further down that closes on `/>`.
  const page = [
    'Out of range (`>NC-70` / `<NC-15` when the spectrum falls outside); the',
    'RC box shows `RC-nn(tag)`.',
    '',
    `${FENCE}mdx`,
    '<Video name="anim_fdtd_room" />',
    FENCE,
    '',
    '<ReportPreview name="ansi_s12_2_nc" />',
  ].join('\n');
  const shown = [
    'Out of range (`>NC-70` / `<NC-15` when the spectrum falls outside); the',
    'RC box shows `RC-nn(tag)`.',
    '',
    `${FENCE}mdx`,
    '<Video name="anim_fdtd_room" />',
    FENCE,
  ].join('\n');
  assert.equal(stripMdx(page), shown);
});

test('the blank lines of a code example stay, and runs of them in the prose close up', () => {
  const example = [`${FENCE}python`, 'def a():', '    pass', '', '', 'def b():', '    pass', FENCE].join('\n');
  assert.equal(stripMdx(`One.\n\n\n\nTwo.\n\n${example}`), `One.\n\nTwo.\n\n${example}`);
});

test('a component is written out only where the page renders it', () => {
  const expand = (tag) => (tag === '<CatalogueIndex lang="en" />' ? '- [Solids](/solids/)' : undefined);
  const page = 'Every catalogue:\n\n<CatalogueIndex lang="en" />\n\nWrite `<CatalogueIndex lang="en" />` to list them.';
  assert.equal(
    stripMdx(page, { expand }),
    'Every catalogue:\n\n- [Solids](/solids/)\n\nWrite `<CatalogueIndex lang="en" />` to list them.',
  );
});

test('the frontmatter goes as Astro finds it, after a byte order mark or blank lines too', () => {
  for (const opening of ['', '\n', '\n  \n', '﻿']) {
    assert.equal(stripFrontmatter(`${opening}---\ntitle: A\n---\nBody.\n`), 'Body.\n', JSON.stringify(opening));
  }
  assert.equal(stripFrontmatter('---\nno closing fence\n'), '---\nno closing fence\n');
  assert.equal(stripFrontmatter('Body.\n'), 'Body.\n');
});

// What else a copy written from a page's source carries, so that it reads as
// the page does: the Spanish copies opened without a title, printed
// `{totalChecks}` where the page prints the count, kept the comment a generated
// page opens with, linked from the site's root, which leads nowhere from a copy
// fetched on its own, dropped every figure, clip and fiche with the text
// written for a reader who cannot see it, and ended without the References
// section the layout prints from the frontmatter, so none of their 219 DOIs.

const ORIGIN = 'https://docs.jmrp.io';
const BASE = `${ORIGIN}/phonometry`;

test('a comment goes, as an HTML comment and as an MDX one, and stays in code', () => {
  const page = [
    '<!-- Generated from docs/ERRATA.md. Edit the source document. -->',
    '',
    'Prose {/* a note to the editor */} goes on.',
    '',
    'Write `<!-- this -->` to leave a note.',
  ].join('\n');
  assert.equal(stripMdx(page), 'Prose  goes on.\n\nWrite `<!-- this -->` to leave a note.');
  assert.equal(stripMdx('<!-- A note. -->\n\nText.', { kind: 'md' }), 'Text.');
});

test('a name the page prints from a data module is written as its value, and one it cannot write stops the copy', () => {
  const page = [
    "import { totalChecks, domains as areas } from '../../data/conformance-stats.mjs';",
    '',
    'It runs {totalChecks} checks over { areas } domains.',
    '',
    'The page writes `{totalChecks}` to print it.',
  ].join('\n');
  const value = (name) => ({ totalChecks: 1897, areas: 113 })[name];
  assert.equal(stripMdx(page, { value }), 'It runs 1897 checks over 113 domains.\n\nThe page writes `{totalChecks}` to print it.');
  assert.throws(() => stripMdx('Only {unknown} here.', { value }), /line 1 prints \{unknown\}/);
  assert.throws(() => stripMdx('\nOnly {unknown} here.', { value, firstLine: 5 }), /line 6 prints \{unknown\}/);
  assert.throws(() => stripMdx('A {1 + 1} sum.', { value }), /prints \{1 \+ 1\}/);
});

test('the names a page imports, and not those of an import line in its code', () => {
  const page = [
    "import Video from '../components/Video.astro';",
    "import { totalChecks, domains as areas } from '../data/conformance-stats.mjs';",
    '',
    '```python',
    'import { nothing } from "here"',
    '```',
  ].join('\n');
  assert.deepEqual(Object.fromEntries(pageImports(page)), {
    totalChecks: { module: '../data/conformance-stats.mjs', imported: 'totalChecks' },
    areas: { module: '../data/conformance-stats.mjs', imported: 'domains' },
  });
});

test("a link from the site's root is made absolute, in prose and in a tag, and stays as written in code", () => {
  const page = [
    'See [the levels guide](/phonometry/signals/levels/) and <a href="/phonometry/es/">the Spanish one</a>.',
    '',
    'Another host stays: [x](//cdn.example.org/x) and [y](https://example.org/y).',
    '',
    'Write `[a](/phonometry/a/)` for a link.',
    '',
    '```md',
    '[b](/phonometry/b/)',
    '```',
  ].join('\n');
  assert.equal(
    stripMdx(page, { origin: ORIGIN }),
    [
      `See [the levels guide](${ORIGIN}/phonometry/signals/levels/) and <a href="${ORIGIN}/phonometry/es/">the Spanish one</a>.`,
      '',
      'Another host stays: [x](//cdn.example.org/x) and [y](https://example.org/y).',
      '',
      'Write `[a](/phonometry/a/)` for a link.',
      '',
      '```md',
      '[b](/phonometry/b/)',
      '```',
    ].join('\n'),
  );
});

test('a figure is an image of the figure this site serves in the page language, its alt the text', () => {
  const tag =
    '<ThemeImage src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sii_flow.svg" alt="The flow, the function clipped to [0, 1]" width="88%" />';
  assert.equal(
    figureMarkdown(tag, { lang: 'es', base: BASE }),
    `![The flow, the function clipped to \\[0, 1\\]](${BASE}/media/sii_flow_es.svg)`,
  );
  assert.equal(figureMarkdown(tag, { lang: 'en', base: BASE }), `![The flow, the function clipped to \\[0, 1\\]](${BASE}/media/sii_flow.svg)`);
});

test('a clip and a fiche are a line: the title linked to what this site serves, then the description and the caption', () => {
  const clip = [
    '<Video',
    '  name="anim_room"',
    '  width={2400}',
    '  height={1350}',
    '  title="A room"',
    '  description="The wave front spreads."',
    '  caption="Watch the corner."',
    '/>',
  ].join('\n');
  assert.equal(
    figureMarkdown(clip, { lang: 'es', base: BASE }),
    `**Vídeo:** [A room](${BASE}/media/anim_room_es.webm): The wave front spreads.\n\nWatch the corner.`,
  );
  const fiche = '<ReportPreview name="iso717_airborne_example" title="Informe ISO 717-1 (PDF)" description="Una ficha." caption="La ficha." />';
  assert.equal(
    figureMarkdown(fiche, { lang: 'es', base: BASE }),
    `**Informe:** [Informe ISO 717-1 (PDF)](${BASE}/media/iso717_airborne_example.pdf): Una ficha.\n\nLa ficha.`,
  );
  assert.equal(figureMarkdown('<SeeAlso />', { lang: 'es', base: BASE }), undefined);
  assert.throws(() => figureMarkdown('<ThemeImage src="x.svg" />', { lang: 'en', base: BASE }), /without its src or its alt/);
});

// The text a page prints as it is, written into the copy's Markdown. The
// Spanish seat-vibration guide gives a figure the alt `... a*wS = SEAT por
// a*wP.`, and a Markdown reader took the text between the two asterisks for
// emphasis and printed `awS = SEAT por awP`, a different formula. Each piece is
// read back by the site's own Markdown pipeline (shared/markdown-reader.mjs),
// never compared with the string the writer meant to write.

/** Every inline mark in one text, as a page may print it. */
const MARKED = 'a*wS = SEAT por a*wP, a*_wS, _b_ and __c__, `d`, $e$, ~~f~~, ~2 dB, [0, 1], 20 lg|H|, <g>, <https://x.y>, a\\b, n_1 and n_2';

/** Text that opens a block when it opens a line, as a caption or a note may. */
const OPENERS = ['# Not a heading', '> Not a quotation', '- Not a list', '+ Not a list', '1. Not a list', '2) Not a list', '--- not a rule'];

test("a figure's alt prints as the page prints it, whatever marks it holds", async () => {
  for (const lang of ['en', 'es']) {
    const tag = `<ThemeImage src="x.svg" alt="${MARKED}" width="94%" />`;
    const { alts, text } = await printed(figureMarkdown(tag, { lang, base: BASE }));
    assert.deepEqual(alts, [MARKED], lang);
    assert.equal(text, '', lang);
  }
  // MDX reads a character reference in an attribute as Markdown reads it, so
  // it prints as the page prints it, decoded once.
  const reference = await printed(figureMarkdown('<ThemeImage src="x.svg" alt="A &amp; B, &#916;L" />', { lang: 'en', base: BASE }));
  assert.deepEqual(reference.alts, ['A & B, ΔL']);
  // The narrow no-break space that groups the digits of a number stays one:
  // the copy read every white space as one plain space.
  const grouped = await printed(figureMarkdown('<ThemeImage src="x.svg" alt="15\u202f000 m, 1,186\u202f084 kg" />', { lang: 'es', base: BASE }));
  assert.deepEqual(grouped.alts, ['15\u202f000 m, 1,186\u202f084 kg']);
});

test("a clip's and a fiche's title, description and caption print as the page prints them", async () => {
  for (const [component, lead] of [['Video', 'Video'], ['ReportPreview', 'Report']]) {
    const tag = `<${component} name="n" title="${MARKED}" description="${MARKED}" caption="${MARKED}" />`;
    const { text, html } = await printed(figureMarkdown(tag, { lang: 'en', base: BASE }));
    assert.equal(text, `${lead}: ${MARKED}: ${MARKED} ${MARKED}`, component);
    assert.equal((html.match(/<p>/g) ?? []).length, 2, `${component}: the line and the caption, each a paragraph`);
    for (const opener of OPENERS) {
      const block = await printed(figureMarkdown(`<${component} name="n" title="T" description="D" caption="${opener}" />`, { lang: 'en', base: BASE }));
      assert.equal(block.text, `${lead}: T: D ${opener}`, `${component}: ${opener}`);
      assert.match(block.html, /^<p>[^]*<\/p>\n<p>[^]*<\/p>$/, `${component}: ${opener} stays a paragraph`);
    }
  }
});

test('a work in the References section prints its title and its note as the page prints them', async () => {
  for (const note of [MARKED, ...OPENERS]) {
    const work = { type: 'book', title: MARKED, authors: ['Doe, J.'], year: 2001, publisher: 'A &amp; B', note };
    const markdown = referencesMarkdown([work], 'en', 'References');
    const { text, html } = await printed(markdown);
    assert.equal(text, `References Doe, J. (2001). ${MARKED}. A &amp; B. ${note}`, note);
    assert.match(html, /^<h2\b[^>]*>References<\/h2>\n<ul>\n<li><strong>[^]*<\/li>\n<\/ul>$/, `${note}: one item, its note inside it`);
    assert.doesNotMatch(html, /<(?:h1|blockquote|ol|hr)\b|<ul>[^]*<ul>/, `${note}: no block of its own`);
  }
});

test("a page's title and a catalogue of the list of catalogues print as the page prints them", async () => {
  for (const title of [MARKED, 'A &amp; B', 'Notes #', 'C# ##', '# Not two headings']) {
    const { html, text } = await printed(titleMarkdown(title));
    assert.equal(text, title, title);
    assert.match(html, /^<h1\b[^]*<\/h1>$/, `${title}: one heading`);
    assert.equal((html.match(/<h1\b/g) ?? []).length, 1, `${title}: one heading`);
  }
  const { text, html } = await printed(catalogueItem({ label: MARKED, url: `${BASE}/reference/catalogues/solids/`, description: `${MARKED} &amp;` }));
  assert.equal(text, `${MARKED}: ${MARKED} &amp;`);
  assert.match(html, /^<ul>\n<li><a href="[^"]+">[^]*<\/li>\n<\/ul>$/);
});

const REFERENCES = [
  {
    type: 'article',
    title: 'P-SV wave propagation in heterogeneous media',
    authors: ['Virieux, J.'],
    year: 1986,
    journal: 'Geophysics',
    volume: 51,
    issue: 4,
    pages: '889-901',
    doi: '10.1190/1.1442147',
    note: 'The scheme of section 1.',
  },
  { type: 'standard', title: 'Electroacoustics: Sound level meters', organization: 'IEC', designation: 'IEC 61672-1:2013', year: 2013 },
];

test('the References section prints one entry per work, in the order the page prints them, each DOI with it', () => {
  assert.equal(
    referencesMarkdown(REFERENCES, 'es', 'Referencias'),
    [
      '## Referencias',
      '',
      '- **IEC. (2013).** *Electroacoustics: Sound level meters* (IEC 61672-1:2013).',
      '- **Virieux, J. (1986).** P-SV wave propagation in heterogeneous media. *Geophysics*, *51*(4), 889-901. https://doi.org/10.1190/1.1442147',
      '  The scheme of section 1.',
    ].join('\n'),
  );
  assert.equal(referencesMarkdown([], 'en', 'References'), '');
  assert.equal(referencesMarkdown(undefined, 'en', 'References'), '');
});

test('the frontmatter is read between its fences, for a YAML reader', () => {
  assert.equal(frontmatterSource('---\ntitle: "A"\nreferences: []\n---\nBody.\n'), 'title: "A"\nreferences: []\n');
  assert.equal(frontmatterSource('Body.\n'), '');
});

/** A copy as the generator writes one, from a page and what it cites. */
function copyOf(source, { title = 'A page', references = [], value } = {}) {
  const body = stripMdx(source, { value, origin: ORIGIN });
  return [`# ${title}`, body, referencesMarkdown(references, 'en', 'References')].filter(Boolean).join('\n\n');
}

const SOURCE = [
  "import { totalChecks } from '../data/conformance-stats.mjs';",
  '',
  'It runs {totalChecks} checks. See [the guide](/phonometry/guide/).',
  '',
  '```python',
  'import numpy as np',
  '',
  'x = np.zeros(3)',
  '```',
].join('\n');
const PAGE = { source: SOURCE, kind: 'mdx', title: 'A page', references: REFERENCES, heading: 'References', site: BASE };
const value = (name) => (name === 'totalChecks' ? 1897 : undefined);

test('a copy written as the generator writes it misses nothing of its page', () => {
  assert.deepEqual(copyDefects(copyOf(SOURCE, { references: REFERENCES, value }), PAGE), []);
});

test('a copy that misses its title, keeps a comment or a link from the root, prints a name, loses code or a work is told so', () => {
  const good = copyOf(SOURCE, { references: REFERENCES, value });
  const cases = [
    [good.replace('# A page\n\n', ''), /opens with .*not with the page's title/],
    [`${good}\n\n<!-- left over -->`, /keeps the comment/],
    [`${good}\n\n{/* left over */}`, /keeps a comment of the page written as/],
    [good.replace(`${ORIGIN}/phonometry/guide/`, '/phonometry/guide/'), /links .* from the site's root/],
    [good.replace('1897', '{totalChecks}'), /prints \{totalChecks\} where the page prints its value/],
    [good.replace('import numpy as np\n', ''), /lost line 6 of the page's code, "import numpy as np"/],
    [good.replace(/^- \*\*IEC.*\n/m, ''), /holds 1 entry, and the page cites 2 works/],
    [good.replace('https://doi.org/10.1190/1.1442147', ''), /leaves out the DOI 10.1190\/1.1442147/],
  ];
  for (const [copy, defect] of cases) {
    const found = copyDefects(copy, PAGE);
    assert.ok(found.some((line) => defect.test(line)), `${defect} in ${JSON.stringify(found)}`);
  }
  const offset = copyDefects(good.replace('import numpy as np\n', ''), { ...PAGE, firstLine: 5 });
  assert.ok(offset.some((line) => /lost line 10 of the page's code/.test(line)), JSON.stringify(offset));
});

test('a copy whose title holds a mark opens with the title when the mark is escaped, and is told so when it is not', () => {
  const page = { ...PAGE, references: [], title: 'a*wS = SEAT por a*wP, Notes #' };
  const copy = (first) => `${first}\n\n${stripMdx(SOURCE, { value, origin: ORIGIN })}`;
  assert.deepEqual(copyDefects(copy(titleMarkdown(page.title)), page), []);
  for (const first of ['# a*wS = SEAT por a*wP, Notes #', '# a\\*wS = SEAT por a\\*wP, Notes #', `# ${page.title} \\`]) {
    const found = copyDefects(copy(first), page);
    assert.ok(found.some((line) => /opens with .*not with the page's title/.test(line)), `${first}: ${JSON.stringify(found)}`);
  }
});

// What the copy writes for a figure, a clip, a fiche and the list of
// catalogues: the check read none of it, so an emitter that dropped every one
// of them again, with the text written for a reader who cannot see it, wrote
// its 915 copies and passed. The check counts what the source renders against
// what the copy prints, each read on its own.

const MEDIA_SOURCE = [
  "import ThemeImage from '../components/ThemeImage.astro';",
  '',
  'A figure:',
  '',
  '<ThemeImage src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sii_flow.svg" alt="The flow, clipped to [0, 1]" />',
  '',
  '<Video name="anim_room" title="A room" description="The wave front spreads." />',
  '',
  '<ReportPreview name="iso717_airborne_example" title="ISO 717-1 report (PDF)" description="A fiche." />',
  '',
  'Write `<ThemeImage src="x.svg" alt="x" />` to show one.',
  '',
  '<CatalogueIndex lang="en" />',
].join('\n');

const CATALOGUE_LIST = [
  `- [Solids](${BASE}/reference/catalogues/solids/): Elastic constants.`,
  `- [Gases](${BASE}/reference/catalogues/gases/): Gas properties.`,
].join('\n');

/** A copy of MEDIA_SOURCE as the generator writes one, its media written out. */
function mediaCopy(source = MEDIA_SOURCE) {
  const expand = (tag) => (tag.startsWith('<CatalogueIndex') ? CATALOGUE_LIST : figureMarkdown(tag, { lang: 'en', base: BASE }));
  return `# A page\n\n${stripMdx(source, { expand, origin: ORIGIN })}`;
}

const MEDIA_PAGE = { source: MEDIA_SOURCE, kind: 'mdx', title: 'A page', heading: 'References', site: BASE, catalogues: 2 };

test('a copy that writes every figure, clip, fiche and catalogue its page renders misses none', () => {
  assert.deepEqual(copyDefects(mediaCopy(), MEDIA_PAGE), []);
  // A page that links a catalogue in a list of its own lists no catalogues.
  const linked = `See also:\n\n- [Gases](${BASE}/reference/catalogues/gases/): Gas properties.`;
  assert.deepEqual(copyDefects(`# A page\n\n${linked}`, { ...MEDIA_PAGE, source: linked }), []);
});

test('a copy that drops a figure, a clip, a fiche or a catalogue of its page is told so', () => {
  const good = mediaCopy();
  const cases = [
    [good.replace(/^!\[.*$/m, ''), /writes 0 of the 1 figure the page renders/],
    [good.replace(`${BASE}/media/sii_flow.svg`, 'https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sii_flow.svg'), /writes 0 of the 1 figure/],
    [good.replace(/!\[[^\]]*\]/, '![]'), /writes 0 of the 1 figure/],
    [good.replace(/^\*\*Video:\*\*.*$/m, ''), /writes 0 of the 1 clip the page renders/],
    [good.replace(/^\*\*Report:\*\*.*$/m, ''), /writes 0 of the 1 fiche the page renders/],
    [good.replace(/^- \[Gases\].*$/m, ''), /writes 1 of the 2 catalogues the page lists/],
    // The emitter of the review's plant: every figure, clip and fiche dropped.
    [`# A page\n\n${stripMdx(MEDIA_SOURCE, { expand: (tag) => (tag.startsWith('<CatalogueIndex') ? CATALOGUE_LIST : undefined), origin: ORIGIN })}`, /writes 0 of the 1 figure/],
  ];
  for (const [copy, defect] of cases) {
    const found = copyDefects(copy, MEDIA_PAGE);
    assert.ok(found.some((line) => defect.test(line)), `${defect} in ${JSON.stringify(found)}`);
  }
});

// A link from the site's root that the writer's pattern did not know stayed in
// the copy, and the check, which read links with the same pattern, said
// nothing: a reference-style definition, and an unquoted or single-quoted
// attribute of a .md page.

test("a link from the site's root is made absolute in every syntax a page writes one", () => {
  const page = [
    "See [the guide][g], <a href=/phonometry/x/>x</a> and <a href='/phonometry/y/'>y</a>.",
    'Also [this]( /phonometry/z/) and [that](</phonometry/a b/>).',
    '',
    '[g]: /phonometry/signals/levels/',
    '  [h]: </phonometry/a b/>',
  ].join('\n');
  assert.equal(
    stripMdx(page, { kind: 'md', origin: ORIGIN }),
    [
      `See [the guide][g], <a href=${ORIGIN}/phonometry/x/>x</a> and <a href='${ORIGIN}/phonometry/y/'>y</a>.`,
      `Also [this]( ${ORIGIN}/phonometry/z/) and [that](<${ORIGIN}/phonometry/a b/>).`,
      '',
      `[g]: ${ORIGIN}/phonometry/signals/levels/`,
      `  [h]: <${ORIGIN}/phonometry/a b/>`,
    ].join('\n'),
  );
});

test("a link from the site's root is found in the copy whatever its syntax, and an address on another host is not", () => {
  const page = { source: 'Text.', kind: 'md', title: 'T', heading: 'References', site: BASE };
  const rooted = [
    '[g]: /phonometry/signals/levels/',
    '<a href=/phonometry/x/>x</a>',
    "<a href='/phonometry/x/'>x</a>",
    '<img src="https://docs.jmrp.io/phonometry/media/a.svg" srcset="/phonometry/media/a.svg 2x" alt="A" />',
    'See /phonometry/start/ for more.',
  ];
  for (const line of rooted) {
    const found = copyDefects(`# T\n\n${line}\n`, page);
    assert.ok(found.some((defect) => /from the site's root/.test(defect)), `${line}: ${JSON.stringify(found)}`);
  }
  const elsewhere = [
    'Its source is at https://github.com/jmrplens/phonometry/blob/main/docs/x.md.',
    '![A figure](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/a.svg)',
    `See ${BASE}/start/ and [it](${BASE}/start/).`,
    'Write `/phonometry/start/` for it.',
  ];
  for (const line of elsewhere) assert.deepEqual(copyDefects(`# T\n\n${line}\n`, page), [], line);
});

// A name written between comments stopped the copy: the writer wrote a name
// as its value only when it stood alone in its braces, and the check found a
// name left in a copy only in that form. The page prints the value whatever
// comments stand around the name, so the copy does, and an expression of
// comments alone is still a comment.

test('an expression is a comment only when it holds comments alone, and a name among comments is its value', () => {
  const counts = (name) => (name === 'totalChecks' ? 1897 : undefined);
  assert.equal(stripMdx('It runs {/* count */ totalChecks /* from the report */} checks.', { value: counts }), 'It runs 1897 checks.');
  assert.equal(stripMdx('It runs {totalChecks /* x */} checks.', { value: counts }), 'It runs 1897 checks.');
  assert.equal(stripMdx('Gone {/* a */ /* b */} here.', { value: counts }), 'Gone  here.');
  assert.throws(() => stripMdx('A {/* a */ 1 + 1 /* b */} sum.', { value: counts }), /prints \{\/\* a \*\/ 1 \+ 1/);
  const page = { source: SOURCE, kind: 'mdx', title: 'A page', heading: 'References', site: BASE };
  for (const left of ['{/* c */ totalChecks}', '{ totalChecks.toLocaleString() }']) {
    const found = copyDefects(`# A page\n\nIt runs ${left} checks.\n\n${SOURCE.split('\n').slice(4).join('\n')}`, page);
    assert.ok(found.some((defect) => /prints \{totalChecks\} where the page prints its value/.test(defect)), `${left}: ${JSON.stringify(found)}`);
  }
});

// MDX reads the comments of an expression left to right, a line comment
// running to the end of its line, so a name beside one prints its value as
// it does beside a block comment. The copy reads them with the reading the
// shared reader gives an expression of comments alone.

test('a name beside a line comment that ends its line is its value, the comments read left to right', () => {
  const counts = (name) => (name === 'totalChecks' ? 1897 : undefined);
  for (const written of [
    '{// a note\ntotalChecks}',
    '{totalChecks // a note\n}',
    '{/* a */\n// b\ntotalChecks}',
    '{// a /* b\ntotalChecks}',
    '{/* see http://x */ totalChecks}',
  ]) {
    assert.equal(stripMdx(`It runs ${written} checks.`, { value: counts }), 'It runs 1897 checks.', JSON.stringify(written));
  }
  assert.equal(stripMdx('Gone {// a note\n} here.', { value: counts }), 'Gone  here.');
});
