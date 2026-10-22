// Fail the build when a social card lost its type, when its title runs into
// the bright part of its artwork, or when it carries the other language's
// strapline.
//
// Every documentation page gets a 1200x630 card under dist/og/, laid out by
// satori and rasterised by sharp (src/utils/og-image.ts). Neither stops the
// build when something on the card goes missing: an artwork sharp cannot
// decode draws nothing, and an element painted under the artwork is simply not
// seen. Both have happened. The first cards came out as a flat background,
// and satori 0.42, which started painting positioned boxes after the boxes in
// normal flow as CSS does, put the full-bleed artwork over the mark and every
// line of type, so each card was the bare artwork. The build stayed green and
// html-validate, pa11y and the link checker had nothing to say, because no
// page changed: only the images a link preview shows.
//
// The card is near-white type on artwork that is dark where the type sits, so
// the question has a measurable answer. In the box of the mark and in the
// column of the title, count the pixels whose three channels are all at least
// 200. No artwork has a pixel that bright there as the card draws it, and the
// postbuild's re-encode (below) brings one or two at most onto a card; the
// mark alone gives about a thousand, and the shortest title that gets a card
// ("Files", the io landing page) about two and a half thousand. A card short
// of either floor has lost the mark or the title.
//
// Each artwork brightens at a different x, and src/lib/og-areas.mjs keeps, per
// artwork, the title column that stops short of it (TITLE_COLUMN). Past the
// end of that column a card should hold its artwork and nothing else. What the
// artwork looks like there is read from the cards themselves: all the cards of
// one artwork share it, and their titles end at different places, so pixel by
// pixel the darkest of them is the drawing. A pixel of a card counts as title
// when its luminance is closer to the title's than to that drawing's, which
// is a pixel at least half covered by the title's ink. A straight stem 1 px
// past the limit puts a whole column of them there, and the title of every
// card there is today, moved 1 px past its limit, fails the check.
//
// The postbuild re-encodes every card with mozjpeg at quality 82. Two points
// of the wave-simulation drawing's grid, at (778, 242) and (807, 255), are a
// bright cyan in the drawing and come out of that encode at a luminance of 237
// to 245, against the title's 247, by an amount that varies from card to
// card. That artwork, and only that one, is allowed two pixels.
//
// The strapline under the wordmark is in the page's language. All the cards of
// one artwork share the drawing behind it, so a card's strapline has to look
// like its own language's cards of that artwork and not like the other
// language's. The Spanish home page, whose id is "es" and not "es/...", once
// got the English strapline this way.
//
// Usage: node scripts/check-social-cards.mjs [dist-directory]
import { readdirSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import sharp from 'sharp';

import { artKeyFor, TITLE_COLUMN, TITLE_COLUMN_START } from '../src/lib/og-areas.mjs';

const here = dirname(fileURLToPath(import.meta.url));
// An explicit directory is for reproducing a defect against a build kept aside;
// with none, the check reads the build that is there.
const DIST = process.argv[2] ? resolve(process.argv[2]) : join(here, '..', 'dist');
const OG = join(DIST, 'og');

// The geometry of src/utils/og-image.ts: 72 px of side padding, 60 px at the
// top, the mark 84 px square in the top left corner and the title in the
// column below it, above the rule that keeps the wordmark off the artwork, and
// the strapline at the right end of the row under that rule. Each box is the
// element's own with a margin of a dozen pixels.
const MARK = { x0: 48, y0: 48, x1: 168, y1: 168 };
const TITLE = { x0: 48, y0: 168, x1: 960, y1: 510 };
const STRAPLINE = { x0: 690, y0: 538, x1: 1140, y1: 580 };
const INK = 200;
// Floors well under what the smallest card measures (about 1100 for the mark,
// about 2500 for "Files", the shortest title that gets a card) and well over
// what any artwork gives (none as the card draws it, two after the re-encode).
const MIN_MARK = 400;
const MIN_TITLE = 300;
// The title's colour, #f2f8fa, as a luminance on the 0-255 scale of the card.
const TITLE_LUMA = luma(0xf2, 0xf8, 0xfa);
// Title pixels allowed past the limit, per artwork: none, except the few the
// re-encode can make of the two grid points of the wave-simulation drawing.
// None of its cards uses them today.
const PAST_LIMIT_ALLOWANCE = { simulation: 2 };
// How far apart, on average over the strapline's box, the English and the
// Spanish straplines of one artwork have to be for the two languages to carry
// different ones. They measure about 13 levels apart on every artwork, and
// each card's strapline comes within 0.7 of its own language's.
const MIN_STRAPLINE_CONTRAST = 6;

/**
 * Luminance of a colour, with the Rec. 709 weights, on its 0-255 values.
 * @param {number} r - Red.
 * @param {number} g - Green.
 * @param {number} b - Blue.
 */
function luma(r, g, b) {
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** Every .jpg under `root`. */
function walk(root, out = []) {
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) walk(path, out);
    else if (entry.name.endsWith('.jpg')) out.push(path);
  }
  return out;
}

/** Pixels inside `box` whose three channels are all at least INK. */
function inkIn(data, info, box) {
  let n = 0;
  for (let y = box.y0; y < Math.min(box.y1, info.height); y++) {
    for (let x = box.x0; x < Math.min(box.x1, info.width); x++) {
      const i = (y * info.width + x) * info.channels;
      if (data[i] >= INK && data[i + 1] >= INK && data[i + 2] >= INK) n++;
    }
  }
  return n;
}

/** The luminance of every pixel inside `box`, row by row. */
function lumaIn(data, info, box) {
  const out = new Float32Array((box.x1 - box.x0) * (box.y1 - box.y0));
  let k = 0;
  for (let y = box.y0; y < box.y1; y++) {
    for (let x = box.x0; x < box.x1; x++) {
      const i = (y * info.width + x) * info.channels;
      out[k++] = luma(data[i], data[i + 1], data[i + 2]);
    }
  }
  return out;
}

let files;
try {
  files = walk(OG).sort();
} catch {
  console.error(`check-social-cards: no cards under ${OG}; build the site first.`);
  process.exit(1);
}
if (files.length === 0) {
  console.error(`check-social-cards: ${OG} holds no .jpg; the card endpoint produced nothing.`);
  process.exit(1);
}

const lost = [];
const cards = [];
for (const file of files) {
  const { data, info } = await sharp(file).raw().toBuffer({ resolveWithObject: true });
  const mark = inkIn(data, info, MARK);
  const title = inkIn(data, info, TITLE);
  if (mark < MIN_MARK || title < MIN_TITLE) {
    lost.push(
      `  ${relative(DIST, file)}: mark ${mark} px (floor ${MIN_MARK}), title ${title} px (floor ${MIN_TITLE})`,
    );
  }
  // The card's path under og/ is the page's slug, which names its artwork
  // and its language.
  const slug = relative(OG, file).replace(/\.jpg$/, '').split(sep).join('/');
  const art = artKeyFor(slug);
  const limit = TITLE_COLUMN_START + TITLE_COLUMN[art];
  cards.push({
    name: relative(DIST, file),
    art,
    locale: slug === 'es' || slug.startsWith('es/') ? 'es' : 'en',
    limit,
    // From the first pixel column a title's ink must not reach: the limit is
    // the x where the title has to end, so the column [limit, limit + 1)
    // stays clear.
    past: lumaIn(data, info, { ...TITLE, x0: limit }),
    strapline: lumaIn(data, info, STRAPLINE),
  });
}

/**
 * The cards grouped by a key.
 * @param {typeof cards} list - Cards.
 * @param {(card: (typeof cards)[number]) => string} key - Grouping key.
 */
function groupBy(list, key) {
  const groups = new Map();
  for (const card of list) {
    const k = key(card);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(card);
  }
  return groups;
}

const crossed = [];
const alone = [];
for (const [art, group] of groupBy(cards, (c) => c.art)) {
  if (group.length < 2) {
    alone.push(`  ${art}: only ${group[0].name}`);
    continue;
  }
  // The drawing past the limit, pixel by pixel the darkest of its cards.
  const drawing = Float32Array.from(group[0].past);
  for (const card of group) {
    for (let p = 0; p < drawing.length; p++) drawing[p] = Math.min(drawing[p], card.past[p]);
  }
  const allowance = PAST_LIMIT_ALLOWANCE[art] ?? 0;
  for (const card of group) {
    let n = 0;
    for (let p = 0; p < drawing.length; p++) {
      if (card.past[p] > (TITLE_LUMA + drawing[p]) / 2) n++;
    }
    if (n > allowance) {
      crossed.push(
        `  ${card.name}: ${n} px of title past x = ${card.limit} (allowance ${allowance})`,
      );
    }
  }
}

/**
 * The pixel-by-pixel mean of some cards' strapline boxes.
 * @param {typeof cards} group - Cards of one artwork and one language.
 */
function meanStrapline(group) {
  const mean = new Float32Array(group[0].strapline.length);
  for (const card of group) {
    for (let p = 0; p < mean.length; p++) mean[p] += card.strapline[p] / group.length;
  }
  return mean;
}

/**
 * Mean absolute difference between two strapline boxes.
 * @param {Float32Array} a - One box.
 * @param {Float32Array} b - The other.
 */
function distance(a, b) {
  let sum = 0;
  for (let p = 0; p < a.length; p++) sum += Math.abs(a[p] - b[p]);
  return sum / a.length;
}

const LANGUAGE = { en: 'English', es: 'Spanish' };
const strayed = [];
for (const [art, group] of groupBy(cards, (c) => c.art)) {
  const byLocale = groupBy(group, (c) => c.locale);
  if (!byLocale.has('en') || !byLocale.has('es')) continue;
  const mean = { en: meanStrapline(byLocale.get('en')), es: meanStrapline(byLocale.get('es')) };
  const apart = distance(mean.en, mean.es);
  if (apart < MIN_STRAPLINE_CONTRAST) {
    strayed.push(
      `  ${art}: its English and Spanish cards carry the same strapline ` +
        `(${apart.toFixed(1)} levels apart, at least ${MIN_STRAPLINE_CONTRAST} expected)`,
    );
    continue;
  }
  for (const card of group) {
    const other = card.locale === 'en' ? 'es' : 'en';
    const own = distance(card.strapline, mean[card.locale]);
    const theirs = distance(card.strapline, mean[other]);
    if (own >= theirs) {
      strayed.push(
        `  ${card.name}: its strapline matches the ${LANGUAGE[other]} cards of its artwork ` +
          `(${theirs.toFixed(1)} levels off), not the ${LANGUAGE[card.locale]} ones ` +
          `(${own.toFixed(1)})`,
      );
    }
  }
}

/**
 * Prints one class of failure, at most forty cards of it.
 * @param {string[]} failures - One line per card.
 * @param {string} what - What those cards got wrong.
 */
function report(failures, what) {
  if (failures.length === 0) return;
  console.error(`${failures.length} of ${cards.length} social cards ${what}:`);
  console.error(failures.slice(0, 40).join('\n'));
  if (failures.length > 40) console.error(`  ... and ${failures.length - 40} more`);
}
report(lost, 'lost their mark or their title');
report(crossed, "have a title past the end of its artwork's title column (src/lib/og-areas.mjs)");
report(strayed, "carry a strapline that is not in their page's language");
if (alone.length > 0) {
  console.error(
    'Artworks on a single card, so the check cannot tell the drawing from a title there:\n' +
      alone.join('\n'),
  );
}
if (lost.length > 0 || crossed.length > 0 || strayed.length > 0 || alone.length > 0) {
  process.exit(1);
}
console.log(
  `${cards.length} social cards carry their mark, their title and their language's strapline, ` +
    'and every title stops where its artwork lets it.',
);
