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
import { VERIFIED_BY_ATTRIBUTE } from '../../page-markdown.mjs';

const CHECK = fileURLToPath(new URL('../../../../scripts/check-markdown-twins.mjs', import.meta.url));
const ORIGIN = 'https://docs.jmrp.io';
const BASE = '/phonometry';
const SITE = `${ORIGIN}${BASE}`;
const UPDATED = '2026-10-20';

/**
 * A built page as the build writes one: its canonical, its hreflang pair, the
 * head link to its copy and the encoding of its structured data.
 *
 * @param {string} route
 * @param {{ lang?: string, copy?: string | null, encoding?: string | null, other?: string, canonical?: string, body?: string }} [options]
 *   `copy` and `encoding` are routes of the copy (null for none); `other` is
 *   the route of the page in the other language.
 */
function page(route, { lang = route.startsWith('/es/') || route === '/es/' ? 'es' : 'en', copy = `${route}index.md`, encoding = copy, other, canonical = route, body = '' } = {}) {
  const graph = { '@context': 'https://schema.org', '@graph': [{ '@type': 'TechArticle', ...(encoding ? { encoding: { '@type': 'MediaObject', encodingFormat: 'text/markdown', contentUrl: `${SITE}${encoding}` } } : {}) }] };
  return [
    `<!DOCTYPE html><html lang="${lang}"><head><meta charset="utf-8"><title>${route}</title>`,
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
 * A copy as src/lib/agent-md/page.mjs writes one.
 *
 * @param {string} route
 * @param {{ lang?: string, title?: string, other?: string, updated?: string, verified?: boolean, body?: string }} [options]
 */
function copy(route, { lang = route.startsWith('/es/') || route === '/es/' ? 'es' : 'en', title = `Page ${route}`, other, updated = UPDATED, verified = false, body = 'The body.' } = {}) {
  return [
    `# ${title}`,
    '',
    '> One page of the phonometry documentation, as Markdown. Index: https://docs.jmrp.io/phonometry/llms.txt',
    '',
    `Canonical: ${SITE}${route}`,
    `Language: ${lang}`,
    ...(other ? [`Alternate: ${SITE}${other}index.md`] : []),
    'Version: phonometry 4.0.0',
    'Install: pip install "phonometry[full]"',
    'Author: José Manuel Requena Plens (https://orcid.org/0000-0003-1250-6212)',
    'Published: 2026-01-06',
    `Updated: ${updated}`,
    ...(verified ? [`Verified: 3 conformance checks (IEC 61260-1:2014) ${SITE}/reference/conformance/#filters`] : []),
    'License: MIT (https://github.com/jmrplens/phonometry/blob/main/LICENSE)',
    'Summary: A page.',
    '',
    '---',
    '',
    body,
    '',
  ].join('\n');
}

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
    'reference/catalogues/solids/index.html': page('/reference/catalogues/solids/'),
    'reference/catalogues/solids/index.md': copy('/reference/catalogues/solids/'),
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
 */
function check(t, change = () => {}) {
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
  const result = checkMarkdownTwins(join(root, 'dist'), { contentDir: join(root, 'content') });
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

  test('the landing page with no copy', (t) => {
    const { found } = check(t, (files) => {
      files['index.md'] = undefined;
    });
    assert.ok(found.includes('copy: / has no copy (expected /index.md)'), found.join('\n'));
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
