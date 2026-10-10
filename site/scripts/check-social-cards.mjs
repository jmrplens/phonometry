// Fail the build when a social card lost its type.
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
// 200: none of the ten brand artworks has a single one in the left three
// quarters of the card, where both boxes are, the mark alone gives about a
// thousand, and the shortest title that gets a card ("Files", the io landing
// page) about two and a half thousand. A card short of either floor has lost
// the mark or the title.
//
// Usage: node scripts/check-social-cards.mjs [dist-directory]
import { readdirSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import sharp from 'sharp';

const here = dirname(fileURLToPath(import.meta.url));
// An explicit directory is for reproducing a defect against a build kept aside;
// with none, the check reads the build that is there.
const DIST = process.argv[2] ? resolve(process.argv[2]) : join(here, '..', 'dist');
const OG = join(DIST, 'og');

// The geometry of src/utils/og-image.ts: 72 px of side padding, 60 px at the
// top, the mark 84 px square in the top left corner and the title in the
// column below it, above the rule that keeps the wordmark off the artwork.
// Each box is the element's own with a margin of a dozen pixels.
const MARK = { x0: 48, y0: 48, x1: 168, y1: 168 };
const TITLE = { x0: 48, y0: 168, x1: 960, y1: 510 };
const INK = 200;
// Floors well under what the smallest card measures (about 1100 for the mark,
// about 2500 for "Files", the shortest title that gets a card) and well over
// what any artwork gives (0).
const MIN_MARK = 400;
const MIN_TITLE = 300;

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

let cards;
try {
  cards = walk(OG).sort();
} catch {
  console.error(`check-social-cards: no cards under ${OG}; build the site first.`);
  process.exit(1);
}
if (cards.length === 0) {
  console.error(`check-social-cards: ${OG} holds no .jpg; the card endpoint produced nothing.`);
  process.exit(1);
}

const failures = [];
for (const file of cards) {
  const { data, info } = await sharp(file).raw().toBuffer({ resolveWithObject: true });
  const mark = inkIn(data, info, MARK);
  const title = inkIn(data, info, TITLE);
  if (mark < MIN_MARK || title < MIN_TITLE) {
    failures.push(`  ${relative(DIST, file)}: mark ${mark} px (floor ${MIN_MARK}), title ${title} px (floor ${MIN_TITLE})`);
  }
}

if (failures.length > 0) {
  console.error(`${failures.length} of ${cards.length} social cards lost their mark or their title:`);
  console.error(failures.slice(0, 40).join('\n'));
  if (failures.length > 40) console.error(`  ... and ${failures.length - 40} more`);
  process.exit(1);
}
console.log(`${cards.length} social cards carry their mark and their title.`);
