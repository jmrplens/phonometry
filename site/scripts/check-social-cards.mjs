// Fail the build when a social card lost its type, when its title runs into
// the bright part of its artwork, when an artwork is too bright inside the
// column its titles take, or when a card carries the other language's
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
// artwork looks like there comes from the card's own code: generateBareArtwork
// in src/utils/og-image.ts draws the artwork with nothing over it, placed and
// encoded as on every card, and the postbuild's re-encode follows, from the
// code the postbuild runs (scripts/shared/recompress.mjs). The drawing was
// once read from the cards themselves, pixel by pixel the darkest of the
// cards of one artwork, and that kept whatever title ink they all shared: an
// artwork left with two cards whose titles crossed the limit at the same place
// could pass. A pixel of a card counts as title when its luminance is closer to
// the title's than to that drawing's, which is a pixel at least half covered
// by the title's ink. A straight stem 1 px past the limit puts a whole column
// of them there, and a round ending, the bowl of an "s" or a closing bracket,
// five to fourteen. An ending that reaches the limit at a point, the tail of
// an "l" or the arm of a "y" or an "x", puts one or two, and that is where the
// check is thinnest: the title of every card there is today, moved 1 px past
// its limit, fails it, some by a single pixel, and any ending less than 1 px
// past the limit can pass.
//
// The postbuild re-encodes every card with mozjpeg at quality 82, and the
// encode of each block of a card depends on the rest of the card, so no card
// is the bare drawing pixel for pixel past its limit. None comes near the
// midpoint either: on the 457 cards, and on every page's title set on each of
// the ten artworks, 4570 cards, the closest a pixel comes is 0.8 of a level.
// That is at (778, 242), a point of the wave-simulation drawing's grid in a
// bright cyan that comes out at a luminance of 245.2 on every card of that
// drawing, 467 of them, and bare alike, against the title's 246.9. The grid's
// other bright point, (807, 255), comes out at 236.7 or 238.5 depending on the
// card and at 236.7 bare, 3.3 levels short of its midpoint at the brighter. So
// no artwork is allowed a pixel past its limit.
//
// Every page but the API reference has its Spanish twin
// (check-i18n-parity.mjs), so every artwork of TITLE_COLUMN is on two cards at
// least. One on fewer, or on none, has lost cards on the way from the sidebar
// to the card endpoint, and stops the check.
//
// Where each column ends comes from where its artwork brightens, measured by
// hand (BRIGHT_FROM in og-areas.mjs), so the check above alone would let a
// redrawn artwork, or a column widened by an edit there, put titles over
// bright drawing with nothing failing. So the drawings are read as well, from
// their masters, resized to the card by sharp and smoothed over 3 x 3 pixels
// as BRIGHT_FROM is measured: across the rows a title can occupy, everywhere
// inside its column, each has to keep the WCAG contrast for large type,
// 4.5:1, against the title's colour. They keep 4.90:1 at worst today, on the
// vibration drawing.
//
// The strapline under the wordmark is in the page's language, and where it
// starts tells which language that is. Both are set in the same type against
// the right padding, so the Spanish one, "Herramientas de medida acústica para
// Python", which is the longer, starts 44 px left of the English one,
// "Acoustic measurement toolkit for Python". The Spanish home page, whose id
// is "es" and not "es/...", once got the English strapline.
//
// Usage: node scripts/check-social-cards.mjs [dist-directory]
import { readdirSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import sharp from 'sharp';

import {
  artKeyFor,
  artworkFile,
  TITLE_COLUMN,
  TITLE_COLUMN_START,
} from '../src/lib/og-areas.mjs';
import { recompress } from './shared/recompress.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const SITE = join(here, '..');
// The artwork masters, which the cards draw from (src/utils/og-image.ts).
const ART = join(SITE, '..', '.github', 'brand', 'art');
// An explicit directory is for reproducing a defect against a build kept aside;
// with none, the check reads the build that is there.
const DIST = process.argv[2] ? resolve(process.argv[2]) : join(SITE, 'dist');
const OG = join(DIST, 'og');

// The card's own code draws each artwork bare, below. It finds the brand
// assets from the working directory, which is the site root for `pnpm run`;
// this makes it so for a direct `node site/scripts/...` too, once the
// directory above is resolved. Node strips the module's types itself.
process.chdir(SITE);
const { generateBareArtwork } = await import('../src/utils/og-image.ts');

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
// The rows a title can occupy, over which og-areas.mjs measures where each
// artwork brightens. The titles' ink spans y 281 to 418 on every card.
const TITLE_ROWS = { y0: 230, y1: 471 };
// The contrast every artwork keeps against the title inside its column: WCAG's
// for large type.
const MIN_ARTWORK_CONTRAST = 4.5;
// Where each language's strapline starts: the first column of the strapline's
// row with strapline ink in it, the same on every card.
const STRAPLINE_START = { en: 780, es: 736 };
// How far from it a card's strapline may start, for the antialiasing of its
// first stroke.
const STRAPLINE_TOLERANCE = 2;
// Strapline ink is a pixel at least three quarters as bright as the
// strapline's colour, #84bccf. Left of where the straplines start, no artwork
// comes near that in their row: 88 at most, on the wave-simulation card.
const STRAPLINE_INK = 0.75 * luma(0x84, 0xbc, 0xcf);

/**
 * Luminance of a colour, with the Rec. 709 weights, on its 0-255 values.
 * @param {number} r - Red.
 * @param {number} g - Green.
 * @param {number} b - Blue.
 */
function luma(r, g, b) {
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * WCAG relative luminance of a colour, from its 0-255 sRGB values.
 * @param {number} r - Red.
 * @param {number} g - Green.
 * @param {number} b - Blue.
 */
function relativeLuminance(r, g, b) {
  const lin = (c) => (c / 255 <= 0.04045 ? c / 255 / 12.92 : ((c / 255 + 0.055) / 1.055) ** 2.4);
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
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

/**
 * The first column of the strapline's row with strapline ink in it, or -1 when
 * there is none.
 */
function straplineStart(data, info) {
  for (let x = STRAPLINE.x0; x < STRAPLINE.x1; x++) {
    for (let y = STRAPLINE.y0; y < STRAPLINE.y1; y++) {
      const i = (y * info.width + x) * info.channels;
      if (luma(data[i], data[i + 1], data[i + 2]) >= STRAPLINE_INK) return x;
    }
  }
  return -1;
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
    strapline: straplineStart(data, info),
  });
}

/**
 * The luminance of an artwork past `limit`, in the title's box, as a card
 * shows it with nothing over it: drawn by the card's code, then put through
 * the postbuild's re-encode as every card is.
 * @param {string} art - Artwork key.
 * @param {number} limit - The first column past the artwork's title column.
 */
async function bareDrawing(art, limit) {
  const jpeg = await recompress(await generateBareArtwork(art), '.jpg');
  const { data, info } = await sharp(jpeg).raw().toBuffer({ resolveWithObject: true });
  return lumaIn(data, info, { ...TITLE, x0: limit });
}

const crossed = [];
const missing = [];
for (const [art, width] of Object.entries(TITLE_COLUMN)) {
  const group = cards.filter((card) => card.art === art);
  if (group.length < 2) {
    missing.push(`  ${art}: ${group.length === 0 ? 'no card' : `only ${group[0].name}`}`);
  }
  if (group.length === 0) continue;
  const drawing = await bareDrawing(art, TITLE_COLUMN_START + width);
  for (const card of group) {
    let n = 0;
    for (let p = 0; p < drawing.length; p++) {
      if (card.past[p] > (TITLE_LUMA + drawing[p]) / 2) n++;
    }
    if (n > 0) crossed.push(`  ${card.name}: ${n} px of title past x = ${card.limit}`);
  }
}

const LANGUAGE = { en: 'English', es: 'Spanish' };
const strayed = [];
for (const card of cards) {
  const own = STRAPLINE_START[card.locale];
  if (Math.abs(card.strapline - own) <= STRAPLINE_TOLERANCE) continue;
  const other = card.locale === 'en' ? 'es' : 'en';
  if (card.strapline < 0) {
    strayed.push(`  ${card.name}: no strapline`);
  } else if (Math.abs(card.strapline - STRAPLINE_START[other]) <= STRAPLINE_TOLERANCE) {
    strayed.push(
      `  ${card.name}: the ${LANGUAGE[other]} strapline, starting at x = ${card.strapline}; ` +
        `the ${LANGUAGE[card.locale]} one starts at ${own}`,
    );
  } else {
    strayed.push(
      `  ${card.name}: a strapline starting at x = ${card.strapline}, where neither ` +
        `language's does (English ${STRAPLINE_START.en}, Spanish ${STRAPLINE_START.es})`,
    );
  }
}

// The drawings themselves, inside the columns their titles take.
const titleLuminance = relativeLuminance(0xf2, 0xf8, 0xfa);
const brightest = (titleLuminance + 0.05) / MIN_ARTWORK_CONTRAST - 0.05;
const glaring = [];
for (const [art, width] of Object.entries(TITLE_COLUMN)) {
  const { data, info } = await sharp(join(ART, artworkFile(art)))
    .resize(1200, 630, { fit: 'cover' })
    .removeAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });
  const lum = new Float64Array(info.width * info.height);
  for (let p = 0; p < lum.length; p++) {
    lum[p] = relativeLuminance(data[3 * p], data[3 * p + 1], data[3 * p + 2]);
  }
  const limit = TITLE_COLUMN_START + width;
  let worst = { value: 0, x: 0, y: 0 };
  for (let y = TITLE_ROWS.y0; y < TITLE_ROWS.y1; y++) {
    for (let x = TITLE_COLUMN_START; x < limit; x++) {
      let sum = 0;
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) sum += lum[(y + dy) * info.width + x + dx];
      }
      if (sum / 9 > worst.value) worst = { value: sum / 9, x, y };
    }
  }
  if (worst.value > brightest) {
    const contrast = (titleLuminance + 0.05) / (worst.value + 0.05);
    glaring.push(
      `  ${art}: ${contrast.toFixed(2)}:1 against the title at (${worst.x}, ${worst.y}), ` +
        `inside its column, which ends at x = ${limit}`,
    );
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
if (glaring.length > 0) {
  console.error(
    `Artworks under ${MIN_ARTWORK_CONTRAST}:1 against the title inside their title column ` +
      '(BRIGHT_FROM and TITLE_MARGIN in src/lib/og-areas.mjs):\n' +
      glaring.join('\n'),
  );
}
if (missing.length > 0) {
  console.error(
    'Artworks on fewer than two cards, where every page but the API reference has one in ' +
      'each language (src/pages/og/[...slug].jpg.ts, artKeyFor in src/lib/og-areas.mjs):\n' +
      missing.join('\n'),
  );
}
const failed = [lost, crossed, strayed, missing, glaring].some((list) => list.length > 0);
if (failed) {
  process.exit(1);
}
console.log(
  `${cards.length} social cards carry their mark, their title and their language's strapline, ` +
    'every title stops where its artwork lets it, and every artwork stays dark enough for the ' +
    'title inside its column.',
);
