/**
 * The PDF fiches, read off the guides that already show them.
 *
 * Seventy-one fiches ship in `.github/reports`, one per reporting format a
 * standard defines, and until this module there was no page that listed them:
 * a reader met one where a guide happened to print it, and had no way to find
 * out what the others were. An index needs a title and a sentence for each,
 * and writing seventy-one of those by hand would have produced a second set of
 * descriptions to keep in step with the first.
 *
 * So it is built from the first set. Every guide that shows a fiche already
 * declares it as `<ReportPreview name title description />`, where the title
 * names the report kind and the description is the textual alternative a
 * screen reader gets. Those are exactly the two sentences an index wants, they
 * are already reviewed, already translated in the Spanish twin of each guide,
 * and they cannot drift from the fiche they describe because they sit next to
 * it.
 *
 * Reading the source of the guides rather than importing them is deliberate.
 * The declarations are MDX component props, which only exist once Astro has
 * compiled the page; a regular expression over the text gets them at the
 * moment a data module can still use them, and the cost of that choice is
 * bounded by the shape of the prop list, which `ReportPreview.astro` fixes.
 *
 * The pairing is checked rather than assumed: a fiche a guide declares and the
 * repository does not ship, or a fiche that ships and no guide shows, is a
 * defect in one of the two and this module refuses to build until it is gone.
 * When it was written both sets held the same seventy-one names.
 */

import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

/** The repository root, found the way `repo-stats.mjs` finds it. */
function findRoot() {
  const starts = [dirname(fileURLToPath(import.meta.url)), process.cwd()];
  for (const start of starts) {
    let dir = start;
    for (;;) {
      if (existsSync(join(dir, 'VERSION')) && existsSync(join(dir, '.github', 'reports'))) {
        return dir;
      }
      const parent = dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  }
  throw new Error('repository root (VERSION) not found above ' + starts.join(' or '));
}

const ROOT = findRoot();
const DOCS = join(ROOT, 'site', 'src', 'content', 'docs');

/** Every `.mdx` under the English guides, deepest last. */
function pages(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'es') continue;
      out.push(...pages(path));
    } else if (entry.name.endsWith('.mdx')) {
      out.push(path);
    }
  }
  return out;
}

/** One `name="..."`-style prop of a component tag, or undefined. */
function prop(tag, key) {
  const match = tag.match(new RegExp(`\\b${key}=(?:"([^"]*)"|\\{\`([^\`]*)\`\\})`, 's'));
  if (!match) return undefined;
  return (match[1] ?? match[2]).replace(/\s+/g, ' ').trim();
}

/** The documentation area a guide belongs to: its first path segment. */
function areaOf(path) {
  const [area] = relative(DOCS, path).split(sep);
  return area.endsWith('.mdx') ? area.replace(/\.mdx$/, '') : area;
}

/** The site path of a guide, as its URL is built. */
function hrefOf(path) {
  const slug = relative(DOCS, path).replace(/\.mdx$/, '').split(sep).join('/');
  return `/phonometry/${slug.replace(/\/index$/, '')}/`;
}

/**
 * The guide's own title, off its frontmatter.
 *
 * An index that printed the URL instead would be asking the reader to decode
 * a path to find out which guide shows a fiche, and the guide has already
 * written the answer at the top of itself.
 */
function titleOf(text, path) {
  const match = text.match(/^title:\s*"?(.+?)"?\s*$/m);
  return match ? match[1] : relative(DOCS, path);
}

function collect(root) {
  const found = new Map();
  for (const path of pages(root)) {
    const text = readFileSync(path, 'utf8');
    for (const match of text.matchAll(/<ReportPreview\b([^>]*?)\/>/gs)) {
      const [tag] = match;
      const name = prop(tag, 'name');
      if (!name || found.has(name)) continue;
      found.set(name, {
        name,
        title: prop(tag, 'title') ?? name,
        description: prop(tag, 'description') ?? '',
        area: areaOf(path),
        page: hrefOf(path),
        pageTitle: titleOf(text, path),
      });
    }
  }
  return found;
}

const declared = collect(DOCS);

/**
 * The same, from the Spanish twin of every guide.
 *
 * The Spanish pages carry their own `title` and `description`, written as
 * Spanish rather than translated from the English at render time, so the index
 * reads in each language the way its guides do. A fiche the Spanish twins do
 * not yet declare falls back to its English entry rather than disappearing:
 * the fiche exists in both languages either way, and a gap in the prose is not
 * a reason to hide it.
 */
const declaredEs = collect(join(DOCS, 'es'));
const shipped = new Set(
  readdirSync(join(ROOT, '.github', 'reports'))
    .filter((file) => file.endsWith('.pdf'))
    .map((file) => file.replace(/\.pdf$/, '')),
);

const missing = [...declared.keys()].filter((name) => !shipped.has(name));
const orphans = [...shipped].filter((name) => !declared.has(name));
if (missing.length || orphans.length) {
  const lines = [];
  if (missing.length) {
    lines.push(`declared by a guide and not shipped: ${missing.join(', ')}`);
  }
  if (orphans.length) {
    lines.push(`shipped and shown by no guide: ${orphans.join(', ')}`);
  }
  throw new Error(
    'the fiches and the guides that show them disagree. ' +
      lines.join('; ') +
      '. Either render the missing fiche with `make reports`, or show the ' +
      'orphan in the guide it belongs to: an index built from the guides can ' +
      'only list what a guide introduces.',
  );
}

/** Every fiche, with the title and sentence its own guide gives it. */
export const reports = [...declared.values()].sort(
  (a, b) => a.area.localeCompare(b.area) || a.title.localeCompare(b.title),
);

/** The same list as the Spanish guides write it, falling back to English. */
export const reportsEs = reports
  .map((report) => ({ ...report, ...(declaredEs.get(report.name) ?? {}), area: report.area }))
  .sort((a, b) => a.area.localeCompare(b.area) || a.title.localeCompare(b.title));

/** Group a list of fiches by documentation area, in the order they are listed. */
function byArea(list) {
  return list.reduce((groups, report) => {
    (groups[report.area] ??= []).push(report);
    return groups;
  }, {});
}

/** The fiches grouped by documentation area. */
export const reportsByArea = byArea(reports);

/** The same, as the Spanish guides write them. */
export const reportsByAreaEs = byArea(reportsEs);

/** How many fiches there are, which is what the landing page prints. */
export const reportCount = reports.length;
