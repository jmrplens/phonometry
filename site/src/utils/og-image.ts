/**
 * Open Graph card generator.
 *
 * Builds the 1200x630 image a link preview shows, using satori to lay the card
 * out as SVG with the text converted to outlines, then sharp to rasterise. Both
 * are already how the rest of the build handles images, and neither needs a
 * browser.
 *
 * The artwork, the mark and the fonts are the committed brand assets under
 * `.github/brand`, read from disk rather than copied into the site tree, so
 * there is one master for the README, the repository card and these.
 *
 * Every page carries the artwork of its documentation area, so a link to a
 * room-acoustics guide previews differently from a link to an underwater one
 * while staying recognisably the same family.
 */

import { readFile } from 'node:fs/promises';
import path from 'node:path';

import satori from 'satori';
import sharp from 'sharp';

import { TITLE_COLUMN_START, titleColumnFor } from '../lib/og-areas.mjs';

/**
 * Where the brand assets live, relative to the working directory.
 *
 * `process.cwd()` and not `import.meta.url`: during the static build this
 * module is bundled into `dist/.prerender/chunks/`, so a URL-relative path
 * resolves against that directory and the fonts are not there. The build fails
 * with ENOENT on the first card. The working directory is the site root for
 * every entry point that exists, `pnpm build` and `astro build` alike.
 */
const BRAND = path.join(process.cwd(), '..', '.github', 'brand');

const OG_WIDTH = 1200;
const OG_HEIGHT = 630;

// The side padding is where the title column starts, which src/lib/og-areas.mjs
// sets beside the column widths it measures from there.
const PAD_X = TITLE_COLUMN_START;
const PAD_Y = 60;

// Straight from scripts/generate_brand.py, so a card cannot drift from the mark.
const HEADING = '#f2f8fa';
const SUPPORT = '#a8d8e6';
const SUPPORT_DIM = '#84bccf';
const ACCENT = '#4ec4e0';

type Cache<T> = { value?: T };
const fontDisplay: Cache<Buffer> = {};
const fontRegular: Cache<Buffer> = {};
const markUri: Cache<string> = {};
const artUris = new Map<string, string>();

/**
 * Reads a file once and keeps it for the rest of the build.
 * @param cache - Slot holding the value after the first read.
 * @param file - Absolute path to read.
 */
async function once(cache: Cache<Buffer>, file: string): Promise<Buffer> {
  cache.value ??= await readFile(file);
  return cache.value;
}

/**
 * The mark, reversed out for a dark ground, as a data URI.
 *
 * A PNG rather than the SVG: satori rasterises `img` sources itself and its
 * SVG support does not cover the whole file, so the raster is the safe input.
 */
async function getMark(): Promise<string> {
  if (!markUri.value) {
    const buf = await readFile(path.join(BRAND, 'logo-on-dark-512.png'));
    markUri.value = `data:image/png;base64,${buf.toString('base64')}`;
  }
  return markUri.value;
}

/**
 * The artwork for one documentation area, as a data URI.
 *
 * Transcoded to JPEG on the way in. The committed masters are WebP, which is
 * the right format to store them in, but satori only lays the card out: it
 * emits the artwork as an <image> in an SVG, and sharp's SVG rasteriser does
 * not decode WebP there. It does not fail, it draws nothing, so the first
 * cards came out as a flat background. Rendering the same tree with a JPEG
 * source and measuring the result is what separated the two.
 * @param key - Area slug, or "generic" for everything outside the areas.
 */
async function getArt(key: string): Promise<string> {
  const cached = artUris.get(key);
  if (cached) return cached;
  const file = key === 'generic' ? 'generic.webp' : `area-${key}.webp`;
  const buf = await readFile(path.join(BRAND, 'art', file));
  const jpeg = await sharp(buf).jpeg({ quality: 92 }).toBuffer();
  const uri = `data:image/jpeg;base64,${jpeg.toString('base64')}`;
  artUris.set(key, uri);
  return uri;
}

type Style = Record<string, string | number | undefined>;
interface Node {
  type: string;
  key: string | number | null;
  props: { style?: Style; children?: unknown; [k: string]: unknown };
}
type Fonts = Parameters<typeof satori>[1]['fonts'];

/**
 * Creates one satori node. Satori takes a React-shaped tree without React.
 * @param type - HTML tag name.
 * @param style - Inline style, CSS properties in camelCase.
 * @param children - Child nodes or text.
 */
function el(type: string, style: Style, ...children: (Node | string | null)[]): Node {
  const kept = children.filter((c): c is Node | string => c !== null);
  return {
    type,
    key: null,
    props: {
      style,
      children: kept.length === 0 ? undefined : kept.length === 1 ? kept[0] : kept,
    },
  };
}

/**
 * The title's type at one size. The card and the measurement below both set
 * the title in it, so a width measured is the width the card gets.
 *
 * Each line is set unbroken: the card decides where the title breaks (see
 * `layOutTitle`), and satori draws those lines as they are.
 * @param size - Font size in pixels.
 */
function titleType(size: number): Style {
  return {
    fontFamily: 'Familjen Grotesk',
    fontSize: `${size}px`,
    color: HEADING,
    lineHeight: '1.12',
    letterSpacing: '-0.015em',
    whiteSpace: 'nowrap',
  };
}

/**
 * The title sizes, largest first: the five sizes the card has always used,
 * and 44 px, which a title only reaches by stepping down (see `layOutTitle`).
 */
const TITLE_SIZES = [68, 58, 48, 44, 40, 34] as const;

/**
 * The size a title gets by its length: 68 px up to 22 characters, 58 px up to
 * 38, 48 px up to 56, 40 px up to 78 and 34 px beyond. This is the table the
 * card has always sized titles by, and it keeps titles of near-equal length,
 * the pages of one section or a page and its translation, at the same size.
 * @param title - The page title.
 */
function tableSize(title: string): number {
  const n = title.length;
  if (n <= 22) return 68;
  if (n <= 38) return 58;
  if (n <= 56) return 48;
  if (n <= 78) return 40;
  return 34;
}

/**
 * The widest title column any card has, x = 72 to 932, where a title sits
 * when its artwork leaves it the whole width, and where every title sat
 * before the column depended on the artwork.
 */
const FULL_COLUMN = 860;

/** The longest last line still too short to stand alone: one word this long or shorter. */
const LONE_WORD_MAX = 8;

/** Words a line should not end on: they belong with what follows them. */
const WEAK_END = new Set(
  (
    'a an the of in on at to for by and or nor but with from as into onto per via vs versus ' +
    'under over between through within without ' +
    'el la lo los las un una unos unas de del al en y e o u ni pero por para con sin sobre ' +
    'entre desde hasta bajo según mediante hacia tras durante contra que se su sus'
  ).split(' '),
);

/**
 * Conjunctions and prepositions that open a phrase of their own, so a line
 * may start with one: "Silencers, Screens / and Barriers In Situ", "Medición
 * del aislamiento / en laboratorio".
 */
const PHRASE_OPENERS = new Set(
  (
    'and or nor but in on at for by with from into onto per via vs versus under over ' +
    'between through within without y e o u ni pero en por para con sin sobre entre ' +
    'desde hasta bajo según mediante hacia tras durante contra al del'
  ).split(' '),
);

/**
 * "of" and "de" open a phrase only before an article, "of a Sound Level
 * Meter", "de un sonómetro". Without one they join two nouns into one term,
 * "tiempo de reverberación", "presión sonora de emisión", which a break would
 * split.
 */
const OF = new Set(['of', 'de']);
const ARTICLE = new Set('a an the el la lo los las un una unos unas'.split(' '));

/**
 * The shortest a first line may be, as a fraction of the second, for a break
 * before a conjunction or a preposition to count as a phrase boundary. A
 * shorter one leaves the title hanging off a stub: "Emisión" over "de la
 * fuente ferroviaria CNOSSOS-EU", "Reading" over "and writing measurement
 * audio".
 */
const PHRASE_FIRST_LINE_MIN = 0.4;

/** An abbreviation set in capitals: "ISO", "E", "ITU-R", "ISO/TS", "BS.468-4", "DB-HR". */
const CAPITALS = /^[A-Z][A-Z0-9]*(?:[./-][A-Z0-9]+)*$/;
/** Words a designation is spelled with besides abbreviations and numbers. */
const DESIGNATION_WORDS = new Set(['Doc', 'Mark']);
/** A unit a number keeps on its line. */
const UNIT = /^(?:[kMG]?Hz|dB[A-Z]?|m?s|[mck]?m|kg|k?Pa|°C|K|%)$/;

/**
 * A word without the brackets and punctuation around it.
 * @param word - One space-separated word of the title.
 */
function bare(word: string): string {
  return word.replace(/^[([¿¡«"]+/, '').replace(/[)\]»",;:.?!]+$/, '');
}

/**
 * Whether the title may break at the space between two words.
 *
 * Only spaces are break points, so a hyphenated compound ("Steady-State",
 * "fluid-solid", "tiempo-frecuencia") is never split at its hyphen. Of the
 * spaces, the card does not break
 * - inside a standard's designation: an abbreviation in capitals, or "Doc" or
 *   "Mark", keeps the number, abbreviation or designation word after it, so
 *   "ISO 532-2", "E DIN 45672-3", "ECAC Doc 29", "IEC TS 61400-11-2" and
 *   "RC Mark II" stay on one line;
 * - before a part number: "-2" in "ISO 8253-1 and -2" never starts a line;
 * - around a slash or an ampersand standing alone, as in "NC / RC" and
 *   "STOI & ESTOI";
 * - between a number and its unit, "16 kHz".
 * @param before - The word before the space.
 * @param after - The word after it.
 */
function breakable(before: string, after: string): boolean {
  if (/^-\d/.test(after)) return false;
  if (['/', '&'].includes(before) || ['/', '&'].includes(after)) return false;
  const opens =
    !/[,;:]$/.test(before) &&
    (CAPITALS.test(bare(before)) || DESIGNATION_WORDS.has(bare(before)));
  const continues =
    !after.startsWith('(') &&
    (/^\d/.test(bare(after)) || CAPITALS.test(bare(after)) || DESIGNATION_WORDS.has(bare(after)));
  if (opens && continues) return false;
  if (/^\d[\d.,]*$/.test(before) && UNIT.test(bare(after))) return false;
  return true;
}

/**
 * A word as the lists of function words above spell it, in lower case, or
 * nothing for an abbreviation in capitals: "EN" in "EN 16487" is no Spanish
 * "en", nor "E" in "E DIN 4150-2" a Spanish "e".
 * @param word - One space-separated word of the title.
 */
function functionWord(word: string): string {
  return CAPITALS.test(word) ? '' : word.toLowerCase();
}

/**
 * What kind of boundary a break falls on: `mark`, before a bracket or after a
 * colon or semicolon; `word`, before a conjunction or a preposition that opens
 * a phrase; `none`, anywhere else, and anywhere inside brackets, where the
 * "and" of "(ISO 8253-1 and -2)" opens nothing.
 * @param words - The title's words.
 * @param i - Index of the first word of the second line.
 */
function boundary(words: string[], i: number): 'mark' | 'word' | 'none' {
  const before = words.slice(0, i).join(' ');
  if (before.split('(').length > before.split(')').length) return 'none';
  if (words[i].startsWith('(') || /[:;]$/.test(words[i - 1])) return 'mark';
  const opener = functionWord(words[i]);
  if (PHRASE_OPENERS.has(opener)) return 'word';
  if (OF.has(opener) && ARTICLE.has(functionWord(words[i + 1] ?? ''))) return 'word';
  return 'none';
}

interface TitleBreak {
  lines: [string] | [string, string];
  /** Width of each line at 1 px; multiply by the size. */
  widths: number[];
  /** The second line is a single short word. */
  lone: boolean;
  /** The first line ends on a word that belongs with the next. */
  weak: boolean;
  /** The boundary the break falls on, from `boundary`. */
  phrase: 'mark' | 'word' | 'none';
  /** The break the title had while the card filled its full column line by line. */
  had: boolean;
}

/**
 * Every way to set the title in one or two lines, breaking where `breakable`
 * allows: the whole title, then one entry per break point.
 * @param title - The page title.
 */
function titleBreaks(title: string): TitleBreak[] {
  const words = title.split(' ');
  const out: TitleBreak[] = [
    { lines: [title], widths: [], lone: false, weak: false, phrase: 'none', had: false },
  ];
  for (let i = 1; i < words.length; i++) {
    if (!breakable(words[i - 1], words[i])) continue;
    const second = words.slice(i).join(' ');
    out.push({
      lines: [words.slice(0, i).join(' '), second],
      widths: [],
      lone: !second.includes(' ') && second.length <= LONE_WORD_MAX,
      weak: WEAK_END.has(functionWord(words[i - 1])),
      phrase: boundary(words, i),
      had: false,
    });
  }
  return out;
}

/**
 * Every first line the card's earlier line breaking could end a line with:
 * at each space, and after a hyphen or a slash that a letter follows, as in
 * "Low-" or "(ISO/". Each comes with the index of the word the second line
 * would start with, or -1 when the break falls inside a word.
 * @param title - The page title.
 */
function earlierBreaks(title: string): { first: string; at: number }[] {
  const words = title.split(' ');
  const out: { first: string; at: number }[] = [];
  for (let i = 0; i < words.length; i++) {
    if (i > 0) out.push({ first: words.slice(0, i).join(' '), at: i });
    for (const m of words[i].matchAll(/[-/](?=\p{L})/gu)) {
      out.push({ first: [...words.slice(0, i), words[i].slice(0, m.index + 1)].join(' '), at: -1 });
    }
  }
  return out;
}

/** Size the lines are measured at; any other size scales from it. */
const MEASURE_SIZE = 100;

/**
 * Lays out every string once with satori, as the card sets a title line, and
 * returns its width at 1 px.
 *
 * Text width is proportional to the size, the advances, the kerning and the
 * letter spacing in em all scale with it, so one layout at MEASURE_SIZE prices
 * every line at every size; a fine point scale keeps the layout from rounding
 * the widths to whole pixels. Checked against a layout at each size of the
 * scale, the scaled widths agree to a thousandth of a pixel.
 * @param strings - The lines to measure.
 * @param fonts - The fonts the card is set in.
 */
async function measureLines(strings: string[], fonts: Fonts): Promise<Map<string, number>> {
  const unique = [...new Set(strings)];
  const widths = new Map<string, number>();
  const lines: Node[] = unique.map((s, i) => ({
    type: 'div',
    key: i,
    props: { style: { display: 'flex', ...titleType(MEASURE_SIZE) }, children: s },
  }));
  const stack = el(
    'div',
    { display: 'flex', flexDirection: 'column', alignItems: 'flex-start' },
    ...lines,
  );
  await satori(stack as never, {
    width: 16 * OG_WIDTH,
    fonts,
    pointScaleFactor: 1000,
    onNodeDetected: (node) => {
      if (typeof node.key === 'number') widths.set(unique[node.key], node.width / MEASURE_SIZE);
    },
  });
  for (const s of unique) {
    if (!widths.has(s)) throw new Error(`og-image: satori did not lay out "${s}".`);
  }
  return widths;
}

/**
 * The layouts that fit a column at one size: the one-line layout alone when
 * the title fits on one line, otherwise the two-line layouts whose lines both
 * fit. Empty when the title needs three lines or more.
 * @param breaks - Measured candidate layouts.
 * @param size - Font size in pixels.
 * @param column - Column width in pixels.
 */
function fitting(breaks: TitleBreak[], size: number, column: number): TitleBreak[] {
  const fits = (b: TitleBreak) => b.widths.every((w) => w * size <= column);
  return fits(breaks[0]) ? [breaks[0]] : breaks.slice(1).filter(fits);
}

/**
 * The items of `list` that pass `test`, or all of `list` when none does.
 * @param list - Candidates.
 * @param test - The preference.
 */
function prefer<T>(list: T[], test: (item: T) => boolean): T[] {
  const kept = list.filter(test);
  return kept.length > 0 ? kept : list;
}

/**
 * Sets the title for a column: its size, and its one or two lines.
 *
 * The size is the one `tableSize` gives the title's length, so near-identical
 * titles keep the same size and none gets larger than it was. The card steps
 * down the scale, 58, 48, 44, 40, 34 px, only while the title cannot be set
 * in two lines of its column at that size, breaking only where `breakable`
 * allows, so a title gets smaller than its table size only where the column
 * its artwork leaves cannot hold it. Nothing fitting at 34 px stops the
 * build: the card neither adds a third line nor cuts the title.
 *
 * At that size the title takes one line when it fits, and otherwise two. Of
 * the two-line breaks that fit, the card prefers, in order:
 * 1. a break at a phrase boundary, and of those the one the title had while
 *    the card filled its full column line by line, then one before a bracket
 *    or after a colon or semicolon, then one before a conjunction or a
 *    preposition that opens a phrase (`boundary`) on a first line that is no
 *    stub (PHRASE_FIRST_LINE_MIN);
 * 2. a first line that does not end on an article, preposition or conjunction;
 * 3. a second line longer than one short word (LONE_WORD_MAX characters);
 * 4. the pair of lines closest to equal length.
 * @param title - The page title.
 * @param column - Width of the card's title column, in pixels.
 * @param fonts - The fonts the card is set in.
 */
async function layOutTitle(
  title: string,
  column: number,
  fonts: Fonts,
): Promise<{ size: number; lines: string[] }> {
  const breaks = titleBreaks(title);
  const earlier = earlierBreaks(title);
  const widths = await measureLines(
    [...breaks.flatMap((b) => b.lines), ...earlier.map((e) => e.first)],
    fonts,
  );
  for (const b of breaks) b.widths = b.lines.map((line) => widths.get(line) ?? Infinity);

  // The break the title had: the last place where the first line still fit
  // the full column at the table size. Only a break between words that is
  // still allowed can be kept.
  const start = tableSize(title);
  if ((widths.get(title) ?? Infinity) * start > FULL_COLUMN) {
    const last = earlier.findLast((e) => (widths.get(e.first) ?? Infinity) * start <= FULL_COLUMN);
    const words = title.split(' ');
    const first = last && last.at > 0 ? words.slice(0, last.at).join(' ') : undefined;
    for (const b of breaks) b.had = b.lines.length === 2 && b.lines[0] === first;
  }

  const size = TITLE_SIZES.find((s) => s <= start && fitting(breaks, s, column).length > 0);
  if (size === undefined) {
    throw new Error(
      `og-image: the title "${title}" does not fit two lines of a ${column} px column even at ` +
        `${TITLE_SIZES.at(-1)} px. Shorten it: the card neither adds a third line nor cuts it.`,
    );
  }
  const atPhrase = (b: TitleBreak) =>
    b.phrase === 'mark' ||
    (b.phrase === 'word' && b.widths[0] >= PHRASE_FIRST_LINE_MIN * b.widths[1]);
  let fit = fitting(breaks, size, column);
  fit = prefer(fit, (b) => b.had && atPhrase(b));
  fit = prefer(fit, (b) => b.phrase === 'mark');
  fit = prefer(fit, atPhrase);
  fit = prefer(fit, (b) => !b.weak);
  fit = prefer(fit, (b) => !b.lone);
  const imbalance = (b: TitleBreak) => Math.abs(b.widths[0] - (b.widths[1] ?? b.widths[0]));
  const best = fit.reduce((a, b) => (imbalance(b) < imbalance(a) ? b : a));
  return { size, lines: [...best.lines] };
}

/** The strapline under the wordmark, in the card's own language. */
const TAGLINE: Record<'en' | 'es', string> = {
  en: 'Acoustic measurement toolkit for Python',
  es: 'Herramientas de medida acústica para Python',
};

export interface OgCard {
  /** Large heading: the page's own title. */
  title: string;
  /** Muted kicker above it: the documentation area, when the page has one. */
  kicker?: string;
  /** Artwork key, from `artKeyFor`. */
  art: string;
  /** Which language the card's own furniture is written in. */
  locale: 'en' | 'es';
}

/**
 * Renders one card to PNG bytes.
 * @param card - Title, kicker and artwork key for this page.
 */
export async function generateOgImage(card: OgCard): Promise<Buffer> {
  const [display, regular, mark, art] = await Promise.all([
    once(fontDisplay, path.join(BRAND, 'fonts', 'FamiljenGrotesk-Bold.ttf')),
    once(fontRegular, path.join(BRAND, 'fonts', 'IBMPlexSans-Regular.ttf')),
    getMark(),
    getArt(card.art),
  ]);
  const fonts: Fonts = [
    { name: 'Familjen Grotesk', data: display, weight: 700, style: 'normal' },
    { name: 'IBM Plex Sans', data: regular, weight: 400, style: 'normal' },
  ];
  // The title stops short of where its artwork brightens, which is a
  // different place on each drawing (src/lib/og-areas.mjs).
  const column = titleColumnFor(card.art);
  const title = await layOutTitle(card.title, column, fonts);

  const tree = el(
    'div',
    {
      display: 'flex',
      width: '100%',
      height: '100%',
      position: 'relative',
      backgroundColor: '#04222b',
    },
    // The artwork, full bleed. It is already dark on the left, which is where
    // the type sits, so it needs no scrim over it.
    {
      type: 'img',
      key: null,
      props: {
        src: art,
        width: OG_WIDTH,
        height: OG_HEIGHT,
        style: { position: 'absolute', top: 0, left: 0, objectFit: 'cover' },
      },
    } as Node,
    // Positioned as well, so it paints over the artwork. CSS paints positioned
    // boxes after the boxes in normal flow, whatever their order in the tree,
    // and the artwork above is positioned. Satori 0.41 and older painted in
    // tree order, so the card came out right by accident; 0.42 paints as CSS
    // does, and without this the artwork covered the mark and every line of
    // type. scripts/check-social-cards.mjs fails the build on such a card.
    el(
      'div',
      {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        flex: '1',
        position: 'relative',
        padding: `${PAD_Y}px ${PAD_X}px`,
      },
      // Top: the mark, at the size it keeps its grid legible.
      {
        type: 'img',
        key: null,
        props: { src: mark, width: 84, height: 84, style: { display: 'flex' } },
      } as Node,
      // Middle: the area, then the page title.
      el(
        'div',
        { display: 'flex', flexDirection: 'column', gap: '14px', maxWidth: `${FULL_COLUMN}px` },
        card.kicker
          ? el(
              'div',
              {
                fontFamily: 'IBM Plex Sans',
                fontSize: '21px',
                color: ACCENT,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
              },
              card.kicker,
            )
          : null,
        el(
          'div',
          { display: 'flex', flexDirection: 'column', maxWidth: `${column}px` },
          ...title.lines.map((line) => el('div', titleType(title.size), line)),
        ),
      ),
      // Bottom: the wordmark, with a rule keeping it off the artwork.
      el(
        'div',
        {
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          borderTop: '1px solid rgba(168,216,230,0.25)',
          paddingTop: '16px',
        },
        el(
          'div',
          { fontFamily: 'Familjen Grotesk', fontSize: '28px', color: SUPPORT },
          'phonometry',
        ),
        el(
          'div',
          { fontFamily: 'IBM Plex Sans', fontSize: '19px', color: SUPPORT_DIM },
          TAGLINE[card.locale],
        ),
      ),
    ),
  );

  const svg = await satori(tree as never, { width: OG_WIDTH, height: OG_HEIGHT, fonts });

  // JPEG, not PNG: the cards carry photographic artwork, so a lossless encode
  // costs several times the bytes for a difference no scraper will ever show.
  return sharp(Buffer.from(svg)).jpeg({ quality: 88, progressive: true }).toBuffer();
}
