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
  copyDefects,
  figureMarkdown,
  frontmatterSource,
  pageImports,
  referencesMarkdown,
  stripFrontmatter,
  stripMdx,
} from './page-twin.mjs';

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
const PAGE = { source: SOURCE, kind: 'mdx', title: 'A page', references: REFERENCES, heading: 'References' };
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
