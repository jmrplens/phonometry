/**
 * Does a standard a guide only cites stay out of what the guide says it
 * implements, and stay in its bibliography?
 *
 * A guide marks with `implemented: false` the bibliography entry of a normative
 * document it requires, cites or compares with but is not written to
 * (src/content.config.ts). Three views of the page drop such an entry and keep
 * the rest: the header chips (src/lib/reference-chips.ts), the weighted search
 * field (src/lib/standard-search.mjs) and the works the structured data says
 * the page is about and based on (src/lib/citations.mjs). The References
 * section keeps printing it. check:search already crosses the search field
 * against the frontmatter; this crosses the other two over the finished build,
 * and checks that the References section still prints every cited entry. Each
 * of those filters is a single line, and with one gone every page still builds,
 * validates and ranks as before, so nothing else would notice a cited standard
 * coming back as a chip or as a governing work.
 *
 * The page is read as it was built, through its own markup: a chip links to the
 * fragment id of a References entry, and that entry prints its designation in
 * brackets right after the title, so the chip is matched to the document by
 * what the reader sees rather than by recomputing ids here. The structured data
 * names works by `@id`, and the bibliography page is where every one of them is
 * defined in full, with its designation or report number. No browser, no
 * server.
 *
 * Usage: node scripts/check-cited-standards.mjs [dist directory]
 */

import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { readDeclaredDesignations } from './shared/search-index.mjs';

const siteRoot = fileURLToPath(new URL('..', import.meta.url));
const distDir = path.resolve(process.argv[2] ?? path.join(siteRoot, 'dist'));
const contentDir = path.join(siteRoot, 'src/content/docs');

const failures = [];
const fail = (message) => failures.push(message);

/** The entities Astro writes in text, decoded; `&amp;` last. */
function decode(text) {
  return text
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/&#x([0-9a-f]+);/gi, (_, code) => String.fromCodePoint(Number.parseInt(code, 16)))
    .replace(/&quot;/g, '"')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&');
}

/** @returns {Promise<string|undefined>} the built page at a route */
async function builtPage(route) {
  try {
    return await readFile(path.join(distDir, route, 'index.html'), 'utf8');
  } catch {
    return undefined;
  }
}

/** Every object in the JSON-LD blocks of a page, nested ones included. */
function graphObjects(html, route) {
  const out = [];
  const walk = (value) => {
    if (Array.isArray(value)) value.forEach(walk);
    else if (value && typeof value === 'object') {
      out.push(value);
      Object.values(value).forEach(walk);
    }
  };
  for (const [, body] of html.matchAll(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)) {
    try {
      walk(JSON.parse(body));
    } catch (error) {
      fail(`${route}: an ld+json block is not valid JSON (${error.message})`);
    }
  }
  return out;
}

const { declared, cited, problems } = await readDeclaredDesignations(contentDir);
for (const problem of problems) fail(problem);

// The bibliography page of each language defines every cited work in full.
/**
 * lang -> @id -> designation or report number, or null for a work that has
 * neither (a book or a paper flagged `primary`, which can govern a page too).
 *
 * @type {Map<string, Map<string, string|null>>}
 */
const definedWorks = new Map();
for (const [lang, route] of [
  ['en', '/reference/bibliography/'],
  ['es', '/es/reference/bibliography/'],
]) {
  const html = await builtPage(route);
  if (!html) {
    console.error(`check:cited-standards: ${route} is not under ${distDir}. Build first.`);
    process.exit(1);
  }
  const works = new Map();
  for (const node of graphObjects(html, route)) {
    const id = node['@id'];
    if (typeof id !== 'string' || !id.includes('/reference/bibliography/#') || works.has(id)) continue;
    const designation =
      node.genre === 'Technical standard' ? node.identifier : node['@type'] === 'Report' ? node.reportNumber : undefined;
    works.set(id, typeof designation === 'string' ? designation : null);
  }
  if (![...works.values()].some((designation) => designation !== null)) {
    fail(`${route}: defines no standard or numbered report in its structured data`);
  }
  definedWorks.set(lang, works);
}

const seen = { pages: 0, entries: 0, chips: 0, works: 0 };

for (const [route, list] of cited) {
  // A designation the page implements through another entry keeps its chip.
  const implemented = new Set(declared.get(route) ?? []);
  const only = new Set(list.filter((designation) => !implemented.has(designation)));
  if (only.size === 0) continue;
  const html = await builtPage(route);
  if (!html) {
    fail(`${route}: cites ${[...only].join(', ')} but the page was not built`);
    continue;
  }
  seen.pages += 1;

  // The References section: which entry prints which designation. A standard
  // or a report prints it in brackets right after its title, `(IEC 60942:2017).`
  const start = html.indexOf('class="page-references');
  if (start === -1) {
    fail(`${route}: cites ${[...only].join(', ')} but publishes no References section`);
    continue;
  }
  /** @type {Map<string, string>} fragment id -> designation printed there */
  const printed = new Map();
  const candidates = [...only, ...implemented];
  for (const [, id, body] of html.slice(start).matchAll(/<li id="([^"]+)"[^>]*>([\s\S]*?)<\/li>/g)) {
    const afterTitle = /<\/cite>(?:\s*<\/a>)?([^<]*)/.exec(body);
    if (!afterTitle) continue;
    const text = decode(afterTitle[1]).replace(/\s+/g, ' ');
    const designation = candidates.find((candidate) => text.startsWith(` (${candidate}).`));
    if (designation) printed.set(id, designation);
  }
  const printedDesignations = new Set(printed.values());
  for (const designation of only) {
    seen.entries += 1;
    if (!printedDesignations.has(designation)) {
      fail(`${route}: cites ${designation} (implemented: false), but its References section prints no entry for it`);
    }
  }

  // The header chips, standards and named works alike; "+N more" links the
  // whole section, not an entry.
  for (const [, attributes] of html.matchAll(/<a\b([^>]*\bclass="page-chip\b[^"]*"[^>]*)>/g)) {
    const anchor = /\bhref="#([^"]+)"/.exec(attributes)?.[1];
    if (!anchor || anchor === 'references') continue;
    seen.chips += 1;
    const designation = printed.get(anchor);
    if (designation && only.has(designation)) {
      fail(`${route}: has a header chip for ${designation}, which the page only cites (implemented: false)`);
    }
  }

  // The works the structured data says the page is about and based on. The
  // first `about` is the software, defined site-wide rather than in the
  // bibliography.
  const works = definedWorks.get(route.startsWith('/es/') ? 'es' : 'en');
  for (const node of graphObjects(html, route)) {
    for (const key of ['isBasedOn', 'about']) {
      for (const item of [node[key] ?? []].flat()) {
        const id = item?.['@id'];
        if (typeof id !== 'string' || !id.includes('/reference/bibliography/#')) continue;
        seen.works += 1;
        const designation = works.get(id);
        if (designation === undefined) {
          fail(`${route}: ${key} names ${id}, which the bibliography page does not define`);
        } else if (only.has(designation)) {
          fail(`${route}: ${key} names ${designation}, which the page only cites (implemented: false)`);
        }
      }
    }
  }
}

// A check that silently stopped finding what it reads would pass everything.
if (cited.size > 0 && seen.pages === 0) fail('no page cites a standard it does not implement: the frontmatter reader found nothing');
if (seen.pages > 0 && seen.chips === 0) fail('no header chip found on any page read: the chip markup changed under this check');
if (seen.pages > 0 && seen.works === 0) fail('no governing work found on any page read: the structured data changed under this check');

if (failures.length > 0) {
  console.error(`\ncheck:cited-standards: ${failures.length} problem(s)\n`);
  for (const message of failures) console.error(`  - ${message}`);
  process.exit(1);
}
console.log(
  `check:cited-standards: ${seen.entries} cited entries on ${seen.pages} pages, all in their References ` +
    `sections and none among ${seen.chips} header chips or ${seen.works} governing works. All good.`,
);
