// The failures scripts/check-markdown-twins.mjs exists to report, on builds
// small enough to read.
//
// The real build only ever hands the check pages whose copies pass, so a check
// that stopped seeing a missing copy, a copy with no title, a leaked
// expression or a link that only resolves on the site would stay green there
// for good. Each test here writes a build of one page of every class, with the
// content files those pages are built from, breaks one thing, and reads what
// the check reports. The copies that keep TeX, code and an escaped `<` have to
// pass: those are the bytes the rules must not mistake for leaks.
//
// Usage (from site/, after `pnpm install`): pnpm run test:agent-md
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { describe, test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { PAGE_CLASSES, REMEDIES, checkMarkdownTwins, headerOf, textProblems } from '../../../../scripts/check-markdown-twins.mjs';
import { preRelease, version } from '../../../data/repo-stats.mjs';
import { PRE_RELEASE } from '../header.mjs';
import { VERIFIED_BY_ATTRIBUTE } from '../../page-markdown.mjs';

const CHECK = fileURLToPath(new URL('../../../../scripts/check-markdown-twins.mjs', import.meta.url));
const ORIGIN = 'https://docs.jmrp.io';
const BASE = '/phonometry';
const SITE = `${ORIGIN}${BASE}`;
const UPDATED = '2026-10-20';
const PUBLISHED = '2026-01-06';
const SUMMARY = 'A page &amp; its copy.';
const HOMES = new Set(['/', '/es/']);

/**
 * A built page as the build writes one: its title, description, canonical,
 * hreflang pair, the head link to its copy and the encoding of its structured
 * data, on a node that gives the day the page was first published.
 *
 * @param {string} route
 * @param {{ lang?: string, copy?: string | null, encoding?: string | null, other?: string, canonical?: string, body?: string, title?: string, published?: string | null }} [options]
 *   `copy` and `encoding` are routes of the copy (null for none); `other` is
 *   the route of the page in the other language; `title` is the whole
 *   `<title>`.
 */
function page(route, { lang = route.startsWith('/es/') || route === '/es/' ? 'es' : 'en', copy = `${route}index.md`, encoding = copy, other, canonical = route, body = '', title = HOMES.has(route) ? `Page ${route}` : `Page ${route} | phonometry`, published = PUBLISHED } = {}) {
  const node = {
    '@type': HOMES.has(route) ? 'WebPage' : 'TechArticle',
    ...(published ? { datePublished: published } : {}),
    ...(encoding ? { encoding: { '@type': 'MediaObject', encodingFormat: 'text/markdown', contentUrl: `${SITE}${encoding}` } } : {}),
  };
  const graph = { '@context': 'https://schema.org', '@graph': [node] };
  return [
    `<!DOCTYPE html><html lang="${lang}"><head><meta charset="utf-8"><title>${title}</title>`,
    `<meta name="description" content="${SUMMARY}">`,
    `<link rel="canonical" href="${SITE}${canonical}"/>`,
    ...(other
      ? [
          `<link rel="alternate" hreflang="${lang}" href="${SITE}${route}"/>`,
          `<link rel="alternate" hreflang="${lang === 'en' ? 'es' : 'en'}" href="${SITE}${other}"/>`,
          `<link rel="alternate" hreflang="x-default" href="${SITE}${lang === 'en' ? route : other}"/>`,
        ]
      : []),
    `<link rel="alternate" type="text/plain" href="${BASE}/llms.txt" title="llms.txt"/>`,
    ...(copy ? [`<link rel="alternate" type="text/markdown" href="${BASE}${copy}">`] : []),
    `<script type="application/ld+json">${JSON.stringify(graph)}</script>`,
    `</head><body><main><h1>${route}</h1>${body}</main></body></html>`,
  ].join('');
}

/**
 * A copy as src/lib/agent-md/page.mjs writes one. A line given as `null` is
 * left out.
 *
 * @param {string} route
 * @param {{ lang?: string, title?: string, other?: string, updated?: string, verified?: boolean, body?: string, published?: string | null, license?: boolean, summary?: string, release?: string | null, install?: string | null, author?: string | null }} [options]
 */
/** The `Pre-release:` value a copy of `lang` carries while VERSION is a pre-release. */
const preReleaseLine = (lang) => (preRelease ? PRE_RELEASE[lang](version) : undefined);

function copy(route, { lang = route.startsWith('/es/') || route === '/es/' ? 'es' : 'en', title = `Page ${route}`, other, updated = UPDATED, verified = false, body = 'The body.', published = PUBLISHED, license = true, summary = 'A page & its copy.', release = `phonometry ${version}`, install = 'pip install "phonometry[full]"', pre = preReleaseLine(lang), author = 'José Manuel Requena Plens (https://orcid.org/0000-0003-1250-6212)' } = {}) {
  return [
    `# ${title}`,
    '',
    '> One page of the phonometry documentation, as Markdown. Index: https://docs.jmrp.io/phonometry/llms.txt',
    '',
    `Canonical: ${SITE}${route}`,
    `Language: ${lang}`,
    ...(other ? [`Alternate: ${SITE}${other}index.md`] : []),
    ...(release ? [`Version: ${release}`] : []),
    ...(install ? [`Install: ${install}`] : []),
    ...(pre ? [`Pre-release: ${pre}`] : []),
    ...(author ? [`Author: ${author}`] : []),
    ...(published ? [`Published: ${published}`] : []),
    `Updated: ${updated}`,
    ...(verified ? [`Verified: 3 conformance checks (IEC 61260-1:2014) ${SITE}/reference/conformance/#filters`] : []),
    ...(license ? ['License: MIT (https://github.com/jmrplens/phonometry/blob/main/LICENSE)'] : []),
    `Summary: ${summary}`,
    '',
    '---',
    '',
    body,
    '',
  ].join('\n');
}

/** The two rows of the catalogue fixture, as the page draws them and as its copy writes them. */
const CATALOGUE_TABLE = '<table><thead><tr><th>Material</th><th>E (GPa)</th></tr></thead><tbody><tr><td>Steel</td><td>210</td></tr><tr><td>Lead</td><td>16</td></tr></tbody></table>';
const CATALOGUE_ROWS = ['| Material | E (GPa) |', '| --- | --- |', '| Steel | 210 |', '| Lead | 16 |'];

/** A page that only sends a retired address on. */
const STUB = `<!DOCTYPE html><title>Redirecting</title><meta http-equiv="refresh" content="0;url=${BASE}/a/">`;

/**
 * A build with one page of every class and the content files they come from.
 *
 * @returns {{ dist: Record<string, string>, content: Record<string, string> }}
 */
function site() {
  const dist = {
    'index.html': page('/', { other: '/es/' }),
    'index.md': copy('/', { other: '/es/' }),
    'es/index.html': page('/es/', { other: '/' }),
    'es/index.md': copy('/es/', { other: '/' }),
    'a/index.html': page('/a/', { other: '/es/a/' }),
    'a/index.md': copy('/a/', { other: '/es/a/' }),
    'es/a/index.html': page('/es/a/', { other: '/a/' }),
    'es/a/index.md': copy('/es/a/', { other: '/a/' }),
    'reference/api/m/index.html': page('/reference/api/m/'),
    'reference/api/m/index.md': copy('/reference/api/m/'),
    'es/reference/api/m/index.html': page('/es/reference/api/m/', {
      lang: 'es',
      copy: '/reference/api/m/index.md',
      canonical: '/reference/api/m/',
    }),
    'reference/catalogues/solids/index.html': page('/reference/catalogues/solids/', { body: CATALOGUE_TABLE }),
    'reference/catalogues/solids/index.md': copy('/reference/catalogues/solids/', { license: false, body: CATALOGUE_ROWS.join('\n') }),
    'reference/errata/iso/index.html': page('/reference/errata/iso/'),
    'reference/errata/iso/index.md': copy('/reference/errata/iso/'),
    'old/index.html': STUB,
    '404.html': page('/404/', { copy: null }),
  };
  const routes = ['/', '/es/', '/a/', '/es/a/', '/reference/api/m/', '/reference/catalogues/solids/', '/reference/errata/iso/'];
  dist['sitemap-index.xml'] = `<?xml version="1.0" encoding="UTF-8"?><sitemapindex><sitemap><loc>${SITE}/sitemap-0.xml</loc></sitemap></sitemapindex>`;
  dist['sitemap-0.xml'] = `<?xml version="1.0" encoding="UTF-8"?><urlset>${routes
    .map((route) => `<url><loc>${SITE}${route}</loc><lastmod>${UPDATED}</lastmod></url>`)
    .join('')}</urlset>`;
  const source = '---\ntitle: A page\n---\n\nText.\n';
  const content = {
    'index.mdx': source,
    'es/index.mdx': source,
    'a.mdx': source,
    'es/a.mdx': source,
    'reference/api/m.md': source,
    'reference/catalogues/solids.mdx': source,
    'reference/errata/iso.mdx': source,
  };
  return { dist, content };
}

/**
 * Writes a build and its content files, applies `change` to the build's files
 * first, and checks it.
 *
 * @param {import('node:test').TestContext} t
 * @param {(files: Record<string, string | undefined>) => void} [change]
 * @param {typeof PAGE_CLASSES} [classes]  The table of page classes, when not the check's own.
 */
function check(t, change = () => {}, classes = PAGE_CLASSES) {
  const root = mkdtempSync(join(tmpdir(), 'check-markdown-twins-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const { dist, content } = site();
  change(dist);
  for (const [dir, files] of [['dist', dist], ['content', content]]) {
    for (const [path, text] of Object.entries(files)) {
      if (text === undefined) continue;
      mkdirSync(dirname(join(root, dir, path)), { recursive: true });
      writeFileSync(join(root, dir, path), text);
    }
  }
  const result = checkMarkdownTwins(join(root, 'dist'), { contentDir: join(root, 'content'), classes });
  /** @type {string[]} */
  const found = [];
  for (const [kind, list] of result.findings) for (const message of list) found.push(`${kind}: ${message}`);
  return { found, stats: result.stats, root };
}

describe('a build whose copies carry what their pages carry', () => {
  test('passes, with one page in every class', (t) => {
    const { found, stats } = check(t);
    assert.deepEqual(found, []);
    assert.deepEqual(stats.classes, {
      home: 2,
      api: 1,
      catalogue: 1,
      'errata-family': 1,
      guide: 2,
      'api-fallback': 1,
      'redirect-stub': 1,
      'not-found': 1,
    });
  });

  test('every class says why, and every kind of finding has its remedy', () => {
    for (const one of PAGE_CLASSES) assert.ok(one.reason.length > 40, one.id);
    for (const remedy of Object.values(REMEDIES)) assert.ok(remedy.length > 40);
  });

  test('keeps TeX braces in inline and display maths, code, an escaped brace and an escaped < as text', () => {
    const body = [
      'The ratio $L_\\mathrm{Ceq} - L_\\mathrm{Aeq}$ and $\\frac{a}{b}$, then',
      '',
      '$$',
      'L = 10 \\lg \\left\\{ \\frac{p^2}{p_0^2} \\right\\}',
      '$$',
      '',
      'Exposure between limits: (EAV\\<=value\\<ELV), and P = ½·Re{Y}·|F|².',
      '',
      '```python',
      'print(f"{totalChecks} <ThemeImage/> <!-- -->")',
      '```',
      '',
      'Inline `{name}` and `<Video/>` are code, and \\{name\\} is a brace a page escaped.',
    ].join('\n');
    assert.deepEqual(textProblems(copy('/a/', { body })), []);
  });
});

describe('the copies the old cut-and-paste left short', () => {
  test('a Spanish copy without its title', (t) => {
    const { found } = check(t, (files) => {
      files['es/a/index.md'] = copy('/es/a/', { other: '/a/' }).replace(/^# .*\n\n/u, '');
    });
    assert.deepEqual(found, ['header: /es/a/index.md does not open with its title as a "# " heading']);
  });

  test('a leaked {totalChecks}', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', body: 'The library passes {totalChecks} checks.' });
    });
    assert.equal(found.length, 1);
    assert.match(found[0], /^text: \/a\/index\.md line \d+: an MDX expression, "\{totalChecks\}"$/u);
  });

  test('a leaked call, member call or expression in an image\'s alt text', () => {
    const body = [
      'The library passes {totalChecks.toLocaleString()} checks.',
      '',
      'A label {t(\'x\')} and {item?.name} and {rows[0]}.',
      '',
      '![{totalChecks}](https://docs.jmrp.io/phonometry/media/x.svg)',
    ].join('\n');
    const problems = textProblems(copy('/a/', { body }));
    assert.deepEqual(
      problems.map((one) => one.replace(/^line \d+: /u, '')),
      [
        'an MDX expression, "{totalChecks.toLocaleString()}"',
        'an MDX expression, "{t(\'x\')}"',
        'an MDX expression in alt text, "{totalChecks}"',
      ],
    );
  });

  test('the landing page with no copy, which its Spanish copy names', (t) => {
    const { found } = check(t, (files) => {
      files['index.md'] = undefined;
    });
    assert.deepEqual(found, [
      'copy: / has no copy (expected /index.md)',
      'header: /es/index.md names /index.md as its copy in the other language, which was not built',
    ]);
  });

  test('a copy that keeps its title and lead line and lost the header block', (t) => {
    const { found } = check(t, (files) => {
      const [title, blank, lead] = copy('/a/', { other: '/es/a/' }).split('\n');
      files['a/index.md'] = [title, blank, lead, '', 'The body.', ''].join('\n');
    });
    assert.deepEqual(found, ['header: /a/index.md has no header']);
  });

  test('a copy with nothing between its header and its references', (t) => {
    const empty = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', body: '' });
    });
    assert.deepEqual(empty.found, ['body: /a/index.md has nothing between its header and its references']);
    const referencesOnly = check(t, (files) => {
      files['es/a/index.md'] = copy('/es/a/', { other: '/a/', body: '## Referencias\n\n- **ISO (2014).** *Una norma*.' });
    });
    assert.deepEqual(referencesOnly.found, ['body: /es/a/index.md has nothing between its header and its references']);
  });

  test('a catalogue copy short of a row the page shows', (t) => {
    const { found } = check(t, (files) => {
      files['reference/catalogues/solids/index.md'] = copy('/reference/catalogues/solids/', {
        license: false,
        body: CATALOGUE_ROWS.slice(0, -1).join('\n'),
      });
    });
    assert.deepEqual(found, ['body: /reference/catalogues/solids/index.md holds 1 table row(s), and /reference/catalogues/solids/ shows 2']);
  });

  test('a link that only resolves on the site', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', body: 'See [the levels](/phonometry/signals/levels/levels/).' });
    });
    assert.deepEqual(found.length, 1);
    assert.match(found[0], /a link that only resolves on the site, "\/phonometry\/signals\/levels\/levels\/"$/u);
  });

  test('a link relative to the file its text came from', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/', {
        other: '/es/a/',
        body: 'See [the data](conformance.json), [up](../b/) and [this](#here), [mail](mailto:a@b.c), [host](//x.org/).',
      });
    });
    assert.deepEqual(found.length, 2, found.join('\n'));
    assert.match(found[0], /a link that resolves only beside the file its text came from, "conformance\.json"$/u);
    assert.match(found[1], /a link that resolves only beside the file its text came from, "\.\.\/b\/"$/u);
  });

  test('an HTML comment', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', body: '<!-- a note for the editor -->\n\nText.' });
    });
    assert.deepEqual(found.length, 1);
    assert.match(found[0], /an HTML comment, "<!-- a note for the editor -->"$/u);
  });

  test('a component tag, raw HTML and the ::: of an aside', () => {
    const body = ['<ThemeImage src="x.svg" alt="x" />', '', 'Text <sub>2</sub>.', '', ':::note', 'An aside.', ':::'].join('\n');
    const problems = textProblems(copy('/a/', { body }));
    assert.equal(problems.length, 4, problems.join('\n'));
    assert.match(problems[0], /a component tag, "<ThemeImage/u);
    assert.match(problems[1], /raw HTML, "<sub>"/u);
    assert.match(problems[3], /the ::: of an aside/u);
  });
});

describe('the copy and what the page says of it', () => {
  test('a head link to another copy', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.html'] = page('/a/', { other: '/es/a/', copy: '/es/a/index.md', encoding: '/a/index.md' });
    });
    assert.deepEqual(found, ['announce: /a/ announces /es/a/index.md in its head, not /a/index.md']);
  });

  test('structured data that declares no copy', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.html'] = page('/a/', { other: '/es/a/', encoding: null });
    });
    assert.deepEqual(found, ['announce: /a/ declares no copy in its structured data, not /a/index.md']);
  });

  test('a Spanish API page with a copy of its own, or announcing one', (t) => {
    const own = check(t, (files) => {
      files['es/reference/api/m/index.md'] = copy('/es/reference/api/m/');
    });
    assert.ok(own.found.includes('copy: /es/reference/api/m/ has a copy at /es/reference/api/m/index.md, and pages of its kind have none of their own'));
    const announced = check(t, (files) => {
      files['es/reference/api/m/index.html'] = page('/es/reference/api/m/', { lang: 'es', canonical: '/reference/api/m/' });
    });
    assert.ok(
      announced.found.includes('announce: /es/reference/api/m/ announces /es/reference/api/m/index.md in its head, not /reference/api/m/index.md'),
      announced.found.join('\n'),
    );
  });

  test('a Spanish API page whose English copy was not built', (t) => {
    const { found } = check(t, (files) => {
      files['reference/api/m/index.md'] = undefined;
    });
    assert.deepEqual(found.sort(), [
      'copy: /es/reference/api/m/ shows the English page, whose copy /reference/api/m/index.md was not built',
      'copy: /reference/api/m/ has no copy (expected /reference/api/m/index.md)',
    ]);
  });

  test('the error page declaring a copy in its structured data, and a redirect stub announcing one', (t) => {
    const { found } = check(t, (files) => {
      files['404.html'] = page('/404/', { copy: null, encoding: '/404/index.md' });
      files['old/index.html'] = `${STUB}<link rel="alternate" type="text/markdown" href="${BASE}/old/index.md">`;
    });
    assert.deepEqual(found, [
      'announce: /404/ declares /404/index.md in its structured data, not none',
      'announce: /old/ announces /old/index.md in its head, not none',
    ]);
  });

  test('a redirect stub with a copy, a copy beside no page, and a .md that is no copy', (t) => {
    const { found } = check(t, (files) => {
      files['old/index.md'] = copy('/old/');
      files['gone/index.md'] = copy('/gone/');
      files['a/notes.md'] = 'notes';
    });
    assert.deepEqual(found.sort(), [
      'copy: /a/notes.md is not a copy: every copy is <page>/index.md',
      'copy: /gone/index.md has no page beside it',
      'copy: /old/ has a copy at /old/index.md, and pages of its kind have none of their own',
    ]);
  });
});

describe('the header and the page', () => {
  test('a date the sitemap does not give the page', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', updated: '2026-10-19' });
    });
    assert.deepEqual(found, [`header: /a/index.md says "Updated: 2026-10-19", and the sitemap dates the page ${UPDATED}`]);
  });

  test('a canonical other than the page\'s, and a language other than its own', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', lang: 'es' }).replace(`Canonical: ${SITE}/a/`, `Canonical: ${SITE}/b/`);
    });
    assert.deepEqual(found, [
      `header: /a/index.md says "Canonical: ${SITE}/b/", and the page's canonical is ${SITE}/a/`,
      'header: /a/index.md says "Language: es", not en',
    ]);
  });

  test('no copy in the other language named where the page has a translation, and one named where it has none', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/');
      files['reference/api/m/index.md'] = copy('/reference/api/m/', { other: '/es/reference/api/m/' });
    });
    assert.deepEqual(found, [
      'header: /a/index.md names no copy in the other language, and the page\'s translation is /es/a/index.md',
      'header: /reference/api/m/index.md names /es/reference/api/m/index.md copy in the other language, and the page\'s translation is none',
    ]);
  });

  test('a Verified line exactly where the page states its conformance checks', (t) => {
    const mark = `<p ${VERIFIED_BY_ATTRIBUTE}>Verified by 3 conformance checks</p>`;
    const missing = check(t, (files) => {
      files['a/index.html'] = page('/a/', { other: '/es/a/', body: mark });
    });
    assert.deepEqual(missing.found, ['header: /a/ states the conformance checks that verify it, and /a/index.md has no "Verified:" line']);
    const extra = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', verified: true });
    });
    assert.deepEqual(extra.found, ['header: /a/index.md has a "Verified:" line, and /a/ states no conformance check']);
    const both = check(t, (files) => {
      files['a/index.html'] = page('/a/', { other: '/es/a/', body: mark });
      files['a/index.md'] = copy('/a/', { other: '/es/a/', verified: true });
    });
    assert.deepEqual(both.found, []);
  });

  test('a title other than the page\'s, the landing pages\' whole <title> included', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', title: 'Page /a/ | phonometry' });
      files['es/index.md'] = copy('/es/', { other: '/', title: 'Page' });
    });
    assert.deepEqual(found, [
      'header: /a/index.md is titled "Page /a/ | phonometry", and the page\'s <title> names it "Page /a/"',
      'header: /es/index.md is titled "Page", and the page\'s <title> names it "Page /es/"',
    ]);
  });

  test('a title that holds a mark, escaped in the copy as Markdown reads it, and one that is not', (t) => {
    const marked = 'a*wS = SEAT por a*wP, Notes #';
    const written = (title) => (files) => {
      files['a/index.html'] = page('/a/', { other: '/es/a/', title: `${marked} | phonometry` });
      files['a/index.md'] = copy('/a/', { other: '/es/a/', title });
    };
    assert.deepEqual(check(t, written(String.raw`a\*wS = SEAT por a\*wP, Notes \#`)).found, []);
    for (const title of [marked, String.raw`a\*wS = SEAT por a*wP, Notes \#`]) {
      assert.deepEqual(check(t, written(title)).found, [
        `header: /a/index.md is titled "${title}", and the page's <title> names it "${marked}"`,
      ]);
    }
  });

  test('a publication day other than the structured data\'s, or none where it gives one', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', published: '2026-01-07' });
      files['es/a/index.md'] = copy('/es/a/', { other: '/a/', published: null });
      files['index.html'] = page('/', { other: '/es/', published: null });
    });
    assert.deepEqual(found, [
      'header: /index.md says "Published: 2026-01-06", and the page\'s structured data gives no datePublished',
      `header: /a/index.md says "Published: 2026-01-07", and the page's structured data gives ${PUBLISHED}`,
      `header: /es/a/index.md has no "Published:" line, and the page's structured data gives ${PUBLISHED}`,
    ]);
  });

  test('a summary other than the page\'s description', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', summary: 'A page &amp; its copy.' });
    });
    assert.deepEqual(found, ['header: /a/index.md says "Summary: A page &amp; its copy.", and the page\'s description is "A page & its copy."']);
  });

  test('a licence line on every page but a catalogue', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', license: false });
      files['reference/catalogues/solids/index.md'] = copy('/reference/catalogues/solids/', { body: CATALOGUE_ROWS.join('\n') });
    });
    assert.deepEqual(found, [
      'header: /a/index.md has no "License:" line',
      'header: /reference/catalogues/solids/index.md has a "License:" line, and a catalogue carries no licence of its own',
    ]);
  });

  test('the release lines and the author, the version being the one built', (t) => {
    const { found } = check(t, (files) => {
      files['a/index.md'] = copy('/a/', { other: '/es/a/', install: null, author: null });
      files['es/a/index.md'] = copy('/es/a/', { other: '/a/', release: 'phonometry 0.0.1' });
      files['reference/api/m/index.md'] = copy('/reference/api/m/', { release: null });
    });
    assert.deepEqual(found, [
      'header: /a/index.md has no "Install:" line',
      'header: /a/index.md has no "Author:" line',
      `header: /es/a/index.md says "Version: phonometry 0.0.1", and the build is of phonometry ${version}`,
      'header: /reference/api/m/index.md has no "Version:" line',
    ]);
  });

  test('a page the sitemap does not date', (t) => {
    const { found } = check(t, (files) => {
      files['sitemap-0.xml'] = (files['sitemap-0.xml'] ?? '').replace(`<lastmod>${UPDATED}</lastmod>`, '');
    });
    assert.deepEqual(found, ['header: / has a copy and no <lastmod> in the sitemap: nothing dates it']);
  });

  test('a header reads as its Key: value lines up to the rule that ends it', () => {
    const fields = headerOf(copy('/a/', { other: '/es/a/' }));
    assert.equal(fields?.get('Canonical'), `${SITE}/a/`);
    assert.equal(fields?.get('Alternate'), `${SITE}/es/a/index.md`);
    assert.equal(headerOf('# Title\n\nNo header here.\n'), undefined);
  });
});

describe('the table of page classes', () => {
  test('a new kind of page no class claims', (t) => {
    const { found } = check(t, (files) => {
      files['tools/index.html'] = page('/tools/', { copy: null });
    });
    assert.deepEqual(found, ['class: /tools/ matches no page class']);
  });

  test('two classes that claim the same page', (t) => {
    const overlapping = {
      id: 'first-guide',
      twin: /** @type {const} */ ('required'),
      reason: 'A class written to claim a page another class already claims.',
      matches: (/** @type {{ route: string }} */ one) => one.route === '/a/',
    };
    const { found } = check(t, () => {}, [...PAGE_CLASSES, overlapping]);
    assert.deepEqual(found, [
      'class: /a/ matches guide and first-guide: the classes must not overlap',
      'class: the page class "first-guide" matches no page of the build: remove it',
    ]);
  });

  test('a class no page of the build matches any more', (t) => {
    const { found } = check(t, (files) => {
      files['404.html'] = undefined;
    });
    assert.deepEqual(found, ['class: the page class "not-found" matches no page of the build: remove it']);
  });
});

describe('the command', () => {
  test('exits 1 with each finding and its remedy, and 2 when there is no build', (t) => {
    const sound = check(t);
    const run = (dist) => spawnSync(process.execPath, [CHECK, dist], { encoding: 'utf8' });
    // The command reads the site's own content directory, so only the exit
    // statuses that do not depend on it are asserted on the fixture build.
    const missing = run(join(sound.root, 'nowhere'));
    assert.equal(missing.status, 2, missing.stderr);
    assert.match(missing.stderr, /holds no built site/u);
    const broken = check(t, (files) => {
      files['index.md'] = undefined;
    });
    const failed = run(join(broken.root, 'dist'));
    assert.equal(failed.status, 1, failed.stdout + failed.stderr);
    assert.match(failed.stderr, /FAIL \d+ missing, extra or misplaced copy\(ies\):/u);
    assert.match(failed.stderr, /Remedy: /u);
  });
});
