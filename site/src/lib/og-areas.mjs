/**
 * Which documentation area a page belongs to, derived from the sidebar.
 *
 * The areas are already declared once, as the sidebar's top-level groups,
 * and every page is placed in exactly one of them there. Reading that tree back
 * means the Open Graph cards inherit the same taxonomy the navigation uses, with
 * nothing to keep in step by hand: moving a guide into another group moves its
 * card artwork with it on the next build.
 */
import { navigationTree as sidebar } from '../data/topics.mjs';

/**
 * Sidebar group label to area slug.
 *
 * The slugs are the historical area names of the artwork, kept because the
 * drawings are named after them, so the artwork lands on
 * the same identifiers rather than on a second set slugified from the labels.
 * A group missing here is simply not an area: Start, Reference and the API
 * tree carry the generic card.
 */
const AREA_SLUG = new Map([
  ['Signal analysis', 'core-signal-analysis'],
  ['Hearing and perception', 'hearing-perception'],
  ['Rooms and buildings', 'rooms-buildings'],
  ['Materials and surfaces', 'materials-surfaces'],
  ['Vibration and structure-borne sound', 'vibration'],
  ['Environment and transport', 'environment-transport'],
  // Aircraft noise was part of the environment area when the artwork was
  // drawn, and it is a topic of its own now. It keeps that card until a
  // drawing of its own exists; the kicker stays the environment label.
  ['Aircraft noise', 'environment-transport'],
  ['Underwater acoustics', 'underwater'],
  ['Sources and devices', 'sources-devices'],
  ['Wave simulation', 'simulation'],
]);

/**
 * Where each artwork gets too bright for the title: the first x at which the
 * drawing, resized to the 1200 x 630 card with a Lanczos filter, smoothed over
 * 3 x 3 pixels and taken at its brightest across the rows a title can occupy
 * (y 230 to 470), reaches the luminance that brings the title colour, #f2f8fa,
 * under 4.5:1, the WCAG contrast for large type. `null` is an artwork that
 * never gets there.
 *
 * Every artwork key needs an entry, measured on its drawing: a key missing
 * here stops the build below rather than taking a column nobody checked.
 * @type {Map<string, number | null>}
 */
const BRIGHT_FROM = new Map([
  ['simulation', 695], // the grid of the wave field
  ['sources-devices', 743], // the loudspeaker
  ['materials-surfaces', 819],
  ['vibration', 941],
  ['generic', 1036],
  ['rooms-buildings', 1151],
  ['core-signal-analysis', null],
  ['hearing-perception', null],
  ['environment-transport', null],
  ['underwater', null],
]);

/**
 * How far short of the bright zone a title stops, in pixels.
 *
 * The card, which draws the artwork with satori, brightens each drawing at the
 * x in BRIGHT_FROM or later, never earlier: at 758 instead of 743 on the
 * loudspeaker and at 1059 instead of 1036 on the generic card, and at the same
 * x on the other four drawings that brighten. So BRIGHT_FROM is the early side
 * of where the cards brighten, and the margin is room left on top of it. In
 * the columns this leaves, the drawing behind any pixel a title can reach,
 * smoothed over 3 x 3 pixels as above, stays at 4.7:1 or better against the
 * title: 4.73:1 at worst, on the vibration drawing resized with a Lanczos
 * filter, 4.90:1 resized by sharp and 5.02:1 as the card draws it. Single
 * pixels, unsmoothed, go lower; specks of the generic drawing come to 3.2:1
 * as the card draws it.
 */
const TITLE_MARGIN = 24;

/** Left edge of the title column: the card's side padding. */
export const TITLE_COLUMN_START = 72;

/**
 * The widest the title column gets, which is where it ended on every card
 * before it depended on the artwork: x = 932.
 */
const TITLE_COLUMN_MAX = 860;

/**
 * Width of the title column on each artwork's card, in pixels: from
 * TITLE_COLUMN_START to TITLE_MARGIN short of the bright zone, and no wider
 * than TITLE_COLUMN_MAX. That gives 599 px on the simulation card, 647 on
 * sources and devices, 723 on materials, 845 on vibration and 860 on the
 * other six. A title never passes TITLE_COLUMN_START plus the width of its
 * card's column, and scripts/check-social-cards.mjs fails the build on a card
 * whose title does, and on an artwork that comes under 4.5:1 against the
 * title anywhere inside its column, measured as BRIGHT_FROM is.
 * @type {Readonly<Record<string, number>>}
 */
export const TITLE_COLUMN = Object.freeze(
  Object.fromEntries(
    [...new Set([...AREA_SLUG.values(), 'generic'])].map((key) => {
      if (!BRIGHT_FROM.has(key)) {
        throw new Error(
          `og-areas: artwork "${key}" has no BRIGHT_FROM entry. Measure where it ` +
            'gets too bright for the title and add it in src/lib/og-areas.mjs.',
        );
      }
      const bright = BRIGHT_FROM.get(key) ?? Infinity;
      return [key, Math.min(TITLE_COLUMN_MAX, bright - TITLE_MARGIN - TITLE_COLUMN_START)];
    }),
  ),
);

/**
 * The file of an artwork's master under .github/brand/art.
 * @param {string} art - Artwork key, from `artKeyFor`.
 */
export function artworkFile(art) {
  return art === 'generic' ? 'generic.webp' : `area-${art}.webp`;
}

/**
 * The title column width for an artwork key.
 * @param {string} art - Artwork key, from `artKeyFor`.
 */
export function titleColumnFor(art) {
  const width = TITLE_COLUMN[art];
  if (width === undefined) throw new Error(`og-areas: no title column for artwork "${art}".`);
  return width;
}

/**
 * Collects every slug reachable under a sidebar node, at any depth.
 * @param {unknown} node - A sidebar entry: a slug string, a link object or a group.
 * @param {string[]} out - Accumulator.
 */
function collectSlugs(node, out) {
  if (typeof node === 'string') {
    out.push(node);
    return;
  }
  if (!node || typeof node !== 'object') return;
  if (typeof node.slug === 'string') out.push(node.slug);
  if (Array.isArray(node.items)) {
    for (const child of node.items) collectSlugs(child, out);
  }
}

/** Slug (locale-free, no leading or trailing slash) to area key. */
const areaBySlug = (() => {
  /** @type {Map<string, string>} */
  const map = new Map();
  for (const group of sidebar) {
    const key = AREA_SLUG.get(group?.label);
    if (!key) continue;
    /** @type {string[]} */
    const slugs = [];
    collectSlugs(group, slugs);
    for (const slug of slugs) {
      if (!map.has(slug)) map.set(slug, key);
    }
  }
  return map;
})();

// Renaming a group label is a legitimate edit, and check-sidebar.mjs accepts
// it: it compares the rendered tree against sidebar.mjs and knows nothing about
// this file. Without this check the lookup above would simply stop matching and
// every page in that group would quietly lose its area and fall back to the
// generic card, with nothing failing. Adding an area already fails loudly, on
// the missing artwork file.
const matched = sidebar.filter((group) => AREA_SLUG.has(group?.label)).length;
if (matched !== AREA_SLUG.size) {
  const missing = [...AREA_SLUG.keys()].filter(
    (label) => !sidebar.some((group) => group?.label === label),
  );
  throw new Error(
    `og-areas: ${missing.length} sidebar group label(s) in AREA_SLUG no longer ` +
      `exist: ${missing.join(', ')}. Update the map in src/lib/og-areas.mjs.`,
  );
}

/** Human-readable area label, keyed the same way, for the card's kicker. */
const areaLabel = (() => {
  /** @type {Map<string, {en: string, es: string}>} */
  const map = new Map();
  for (const group of sidebar) {
    const key = AREA_SLUG.get(group?.label);
    // First label wins: two topics may share a card, and the kicker names the
    // area the drawing was made for.
    if (!key || map.has(key)) continue;
    map.set(key, { en: group.label, es: group.translations?.es ?? group.label });
  }
  return map;
})();

/**
 * The artwork key for a page, falling back to the generic card.
 * @param {string} id - The page's collection id, e.g. "guides/filter-banks" or
 *   "es/guides/filter-banks".
 */
export function artKeyFor(id) {
  const slug = id.replace(/^es\//, '').replace(/\.mdx?$/, '').replace(/\/index$/, '');
  return areaBySlug.get(slug) ?? 'generic';
}

/**
 * The area's display label for a page, or undefined outside the areas.
 * @param {string} id - The page's collection id.
 * @param {'en'|'es'} locale - Which language to label it in.
 */
export function areaLabelFor(id, locale) {
  const key = artKeyFor(id);
  return key === 'generic' ? undefined : areaLabel.get(key)?.[locale];
}
