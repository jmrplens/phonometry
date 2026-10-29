// Each writer on a fixture small enough to read, in each language and
// flavour it writes, through the same registry the pages use.
//
// Usage (from site/, after `pnpm install`): pnpm run test:agent-md
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { before, describe, test } from 'node:test';

import { conformanceMarkdown } from '../../../components/Conformance.md.mjs';
import { reports, reportsByAreaEs } from '../../../data/reports.mjs';
import { en, es } from '../../../data/home.ts';
import { loadRegistry } from '../registry.mjs';
import { REPO_DIR } from '../render.mjs';
import { render } from './helpers.mjs';

const FIGURES = 'https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images';
const SITE = 'https://docs.jmrp.io/phonometry';

/** @type {Map<string, import('../types.mjs').ComponentMarkdown>} */
let registry;
before(async () => {
  registry = await loadRegistry();
});

/** Renders with the site's writers. */
const write = (source, options = {}) => render(source, { registry, ...options });

describe('Scope and ScopeClaim', () => {
  const panel = [
    '<Scope>',
    '<ScopeClaim status="covered" label="Covered">',
    'IEC 61260-1:2014 band edges, `nominal_frequencies` and $f_m$.',
    '</ScopeClaim>',
    '',
    '<ScopeClaim status="not-covered">',
    'The gallery is [another page](/phonometry/signals/filters/filter-gallery/).',
    '',
    'A second paragraph:',
    '',
    '- with a list',
    '</ScopeClaim>',
    '</Scope>',
    '',
  ].join('\n');

  test('each claim is a list item led by its legend, the state named where the page omits it', () => {
    const { markdown, issues } = write(panel);
    assert.equal(
      markdown,
      [
        '- **Covered.** IEC 61260-1:2014 band edges, `nominal_frequencies` and $f_m$.',
        '',
        `- **Not covered.** The gallery is [another page](${SITE}/signals/filters/filter-gallery/).`,
        '',
        '  A second paragraph:',
        '',
        '  - with a list',
        '',
      ].join('\n'),
    );
    assert.deepEqual(issues, []);
  });

  test('the state is named in the page language', () => {
    const { markdown } = write('<Scope>\n<ScopeClaim status="not-covered">\nNada.\n</ScopeClaim>\n</Scope>\n', { lang: 'es' });
    assert.equal(markdown, '- **No cubierto.** Nada.\n');
  });

  test('a status outside the two is reported', () => {
    const { issues } = write('<ScopeClaim status="partial">\nx\n</ScopeClaim>\n');
    assert.equal(issues[0].kind, 'writer');
    assert.match(issues[0].message, /status="covered" or status="not-covered"/);
  });
});

test('SeeAlso is its authored heading and links', () => {
  const { markdown, issues } = write('<SeeAlso>\n\n## See also\n\n- [A guide](/phonometry/a/): why.\n\n</SeeAlso>\n');
  assert.equal(markdown, `## See also\n\n- [A guide](${SITE}/a/): why.\n`);
  assert.deepEqual(issues, []);
});

describe('ThemeImage', () => {
  const figure = `<ThemeImage src="${FIGURES}/levels.svg" alt="Band levels | in [dB]" width="80%" loading="eager" />\n`;

  test('the copy shows the figure this site serves, in the page language', () => {
    assert.equal(write(figure).markdown, String.raw`![Band levels \| in \[dB\]](${SITE}/media/levels.svg)` + '\n');
    assert.equal(write(figure, { lang: 'es' }).markdown, String.raw`![Band levels \| in \[dB\]](${SITE}/media/levels_es.svg)` + '\n');
  });

  test('the GitHub edition draws the picture GitHub renders, both palettes and the width', () => {
    assert.equal(
      write(figure, { flavour: 'github', lang: 'es' }).markdown,
      `<picture><source media="(prefers-color-scheme: dark)" srcset="${FIGURES}/levels_es_dark.svg">` +
        `<img src="${FIGURES}/levels_es.svg" alt="Band levels | in [dB]" width="80%"></picture>\n`,
    );
  });

  test('inside a table cell the figure stays on one line', () => {
    const source = `| a | b |\n| --- | --- |\n| x | <ThemeImage src="${FIGURES}/f.svg" alt="f" /> |\n`;
    assert.equal(write(source).markdown, `| a | b |\n| --- | --- |\n| x | ![f](${SITE}/media/f.svg) |\n`);
  });

  test('a figure without alt is reported', () => {
    assert.equal(write(`<ThemeImage src="${FIGURES}/f.svg" alt="" />\n`).issues[0].kind, 'writer');
  });
});

describe('Video', () => {
  const clip =
    '<Video name="anim_decay" title="A decay" description="The level falls." width={1600} height={900} displayWidth="88%" caption="Caption line." id="decay" />\n';

  test('the copy links the clip this site serves, then the caption', () => {
    assert.equal(write(clip).markdown, `**Video:** [A decay](${SITE}/media/anim_decay.webm): The level falls.\n\nCaption line.\n`);
    assert.equal(write(clip, { lang: 'es' }).markdown, `**Vídeo:** [A decay](${SITE}/media/anim_decay_es.webm): The level falls.\n\nCaption line.\n`);
  });

  test('the GitHub edition links the clip at the commit assets.lock pins', () => {
    const lock = readFileSync(join(REPO_DIR, 'assets.lock'), 'utf8').trim();
    assert.match(lock, /^[0-9a-f]{40}$/u);
    assert.equal(
      write(clip, { flavour: 'github' }).markdown,
      `**Video:** [A decay](https://raw.githubusercontent.com/jmrplens/phonometry-assets/${lock}/images/anim_decay.webm): The level falls.\n\nCaption line.\n`,
    );
  });
});

describe('ReportPreview', () => {
  const fiche = '<ReportPreview name="iso717_airborne_example" title="Airborne report (PDF)" description="One page." caption="Rw (C; Ctr)." />\n';

  test('the copy links the PDF this site serves with what it shows', () => {
    assert.equal(
      write(fiche, { lang: 'es' }).markdown,
      `**Informe:** [Airborne report (PDF)](${SITE}/media/iso717_airborne_example.pdf): One page.\n\nRw (C; Ctr).\n`,
    );
  });

  test('the GitHub edition shows the preview linked to the PDF', () => {
    const raw = 'https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports/iso717_airborne_example';
    assert.equal(
      write(fiche, { flavour: 'github' }).markdown,
      `[![Airborne report (PDF): One page.](${raw}.webp)](${raw}.pdf)\n\nRw (C; Ctr).\n`,
    );
  });
});

test('the pickers and the routers write nothing, on purpose', () => {
  const { markdown, issues } = write('Before.\n\n<CatalogueFinder lang="en" />\n\n<CatalogueRouter lang="en" />\n\n<ErrataRouter />\n\nAfter.\n');
  assert.equal(markdown, 'Before.\n\nAfter.\n');
  assert.deepEqual(issues, []);
});

describe('Conformance', () => {
  const fixture = [
    '<!--',
    '  AUTO-GENERATED FILE - DO NOT EDIT BY HAND.',
    '-->',
    '',
    '## Numerical conformance report',
    '',
    '<sub><b>&#916;</b> is the difference; &ge; 0 &amp; more.</sub>',
    '',
    '<details>',
    '<summary><b>Levels</b>: IEC 61672-1 &amp; ISO 1996</summary>',
    '',
    '| Standard | Status |',
    '|:---|:---|',
    '| IEC 61672-1 Table 3 | ![Pass][cv-pass] Pass |',
    '',
    '</details>',
    '',
    '[cv-pass]: https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/badges/verdict-pass.svg',
    '',
  ].join('\n');

  test('each collapsible section becomes a section, the marks go and the verdict stays', () => {
    const reported = [];
    assert.equal(
      conformanceMarkdown(fixture, (message) => reported.push(message)),
      [
        '## Numerical conformance report',
        '',
        '**Δ** is the difference; ≥ 0 & more.',
        '',
        '## Levels: IEC 61672-1 & ISO 1996',
        '',
        '| Standard | Status |',
        '|:---|:---|',
        '| IEC 61672-1 Table 3 | Pass |',
      ].join('\n'),
    );
    assert.deepEqual(reported, []);
  });

  test('a tag the generator did not write before is reported', () => {
    const reported = [];
    conformanceMarkdown('<table><tr><td>x</td></tr></table>\n\n`<code in a span>`\n', (message) => reported.push(message));
    assert.deepEqual(reported, [
      'docs/CONFORMANCE.md carries <table>, which Conformance.md.mjs has no rule for',
      'docs/CONFORMANCE.md carries <tr>, which Conformance.md.mjs has no rule for',
      'docs/CONFORMANCE.md carries <td>, which Conformance.md.mjs has no rule for',
    ]);
  });

  test('the real report becomes one section per collapsible block, with no HTML left', () => {
    const text = readFileSync(join(REPO_DIR, 'docs', 'CONFORMANCE.md'), 'utf8');
    const { markdown, issues } = write('<Conformance lang="en" />\n');
    assert.deepEqual(issues, []);
    const blocks = text.match(/^<details>/gmu).length;
    assert.equal(markdown.match(/^## /gmu).length, blocks + 1);
    assert.doesNotMatch(markdown, /<\/?(details|summary|sub|b)>|\]\[cv-|&#\d+;/u);
  });

  test('the Spanish page points to the English copy', () => {
    const { markdown } = write('<Conformance lang="es" />\n', { lang: 'es' });
    assert.match(markdown, /en texto plano en la copia en Markdown de la página en inglés: https:\/\/docs\.jmrp\.io\/phonometry\/reference\/conformance\/index\.md\.\n$/u);
  });
});

describe('ReportIndex', () => {
  test('every fiche, once, under its area', () => {
    const { markdown, issues } = write('<ReportIndex lang="en" />\n');
    assert.deepEqual(issues, []);
    assert.equal(markdown.match(/^- \[/gmu).length, reports.length);
    for (const report of reports) assert.ok(markdown.includes(`/.github/reports/${report.name}.pdf)`), report.name);
    assert.match(markdown, /^## Aircraft noise \(1 fiche\)$/mu);
  });

  test('the Spanish index uses the Spanish areas and guides', () => {
    const { markdown } = write('<ReportIndex lang="es" />\n', { lang: 'es' });
    assert.equal(markdown.match(/^## /gmu).length, Object.keys(reportsByAreaEs).length);
    assert.match(markdown, /^## Ruido de aeronaves \(1 ficha\)$/mu);
    assert.match(markdown, /Se muestra en \[[^\]]+\]\(https:\/\/docs\.jmrp\.io\/phonometry\/es\//u);
  });
});

describe('Home', () => {
  const page = (name) =>
    [
      '---',
      'hero:',
      '  tagline: Acoustic measurement in Python.',
      '  actions:',
      '    - text: Start here',
      '      link: /phonometry/start/getting-started/',
      '---',
      '',
      `<Home content={${name}} />`,
      '',
    ].join('\n');

  test('the landing, block by block, from the content the page passes', () => {
    const { markdown, issues } = write(page('en'), { scope: new Map([['en', en]]) });
    assert.deepEqual(issues, []);
    assert.ok(markdown.startsWith(`Acoustic measurement in Python.\n\n- [Start here](${SITE}/start/getting-started/)\n\n**${en.statsLabel}**`));
    for (const stat of en.stats) assert.ok(markdown.includes(`- **${stat.value}** `), stat.label);
    for (const heading of [en.what.title, en.proof.title, en.coverage.title, en.start.title]) {
      assert.match(markdown, new RegExp(`^## ${heading}$`, 'mu'));
    }
    assert.ok(markdown.includes('```bash\n   pip install "phonometry[full]"\n   ```'));
    assert.ok(markdown.includes('`.plot()`'), 'inline HTML of a data string written as Markdown');
    assert.equal(markdown.match(/^\| \[/gmu).length, en.coverage.areas.length);
    assert.match(markdown, /For language models: \[llms\.txt\]\(https:\/\/docs\.jmrp\.io\/phonometry\/llms\.txt\)/u);
    assert.doesNotMatch(markdown, /<[a-z]+[ >]/u);
  });

  test('the Spanish landing reads the Spanish content', () => {
    const { markdown, issues } = write(page('es'), { scope: new Map([['es', es]]), lang: 'es' });
    assert.deepEqual(issues, []);
    assert.match(markdown, new RegExp(`^## ${es.what.title}$`, 'mu'));
    assert.match(markdown, /Para modelos de lenguaje: \[llms\.txt\]/u);
  });

  test('without the content the writer says so', () => {
    const { markdown, issues } = write(page('en'));
    assert.equal(markdown, '\n');
    assert.deepEqual(
      issues.map((issue) => issue.kind),
      ['expression', 'writer'],
    );
  });
});
