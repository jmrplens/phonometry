// Fail when a social card title is set against the rules that place its line
// break and choose its size.
//
// The card sets a page's title in one or two lines of the column its artwork
// leaves (src/utils/og-image.ts, layOutTitle). Where the title breaks follows
// rules about words: a line never ends on an article, a preposition or a
// conjunction; a standard's designation ("E DIN 45672-3", "ECAC Doc 29",
// "ISO/TS 12913"), a part number, a slash or an ampersand standing alone, a
// hyphenated compound and a number with its unit are never parted; a phrase
// boundary is preferred to a break inside a term. The size comes from the
// title's length, and steps down only when the column cannot hold the title in
// two lines with all of that kept whole. check-social-cards.mjs reads the
// built cards back and measures pixels and language, so it catches a title
// that runs into the artwork, but not one that is broken in the wrong place:
// "Sound Power in the / Reverberation Room" fits its column as well as
// "Sound Power / in the Reverberation Room" does.
//
// So this holds the rules themselves, in two halves, with the card's own
// layOutTitle and the brand fonts and no build:
//
// 1. A table of titles, each with the size and the exact lines it has to get
//    in the column of a given artwork: the English and Spanish examples the
//    comments in og-image.ts give, titles that only keep a designation, a part
//    number, a slash, an ampersand or a number with its unit whole because the
//    rule says so, titles that step down a size, titles whose break only a
//    preference between breaks that fit decides, a title in the column of
//    each artwork that narrows it and one in the widest, and one title that
//    fits no size at all and has to stop the build with the error the card
//    documents. A change to a rule shows here as the case it moves.
// 2. Every page title that gets a card, read from the content frontmatter as
//    the card endpoint (src/pages/og/[...slug].jpg.ts) reads it, set in its
//    page's column, and held to what no title may do whatever the rules
//    prefer: more than two lines, lines that do not give the title back, a
//    line ending on a weak word, any of the parts above split, a size larger
//    than the title's length gives it, or a line that passes the end of the
//    column, measured by setting it again in the card's type at its size.
//
// The weak words, the shape of a designation, the units and the size table
// are written out here a second time rather than imported, so that an edit to
// one copy has to be made to the other on purpose.
//
// Usage: node scripts/check-social-card-titles.mjs
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import satori from 'satori';

import { artKeyFor, TITLE_COLUMN_START, titleColumnFor } from '../src/lib/og-areas.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const SITE = join(here, '..');
const CONTENT = join(SITE, 'src', 'content', 'docs');

// og-image.ts finds the brand fonts from the working directory, which is the
// site root for the build and for `pnpm run`; this makes it so for a direct
// `node site/scripts/...` too. Node strips the module's types itself, which it
// does without a flag from Node 22.18 and 23.6 on, so the import is the file
// the build compiles, not a copy of it.
process.chdir(SITE);
const { cardFonts, layOutTitle, titleType } = await import('../src/utils/og-image.ts');

/**
 * Words no line may end on: the articles, prepositions and conjunctions of
 * both languages, which belong with the word after them. A word in capitals is
 * an abbreviation and none of these: "E" in "E DIN 4150-2", "EN" in
 * "EN 16487".
 */
const WEAK = new Set(
  (
    'a an the of in on at to for by and or nor but with from as into onto per via vs versus ' +
    'under over between through within without ' +
    'el la lo los las un una unos unas de del al en y e o u ni pero por para con sin sobre ' +
    'entre desde hasta bajo según mediante hacia tras durante contra que se su sus'
  ).split(' '),
);
/** An abbreviation set in capitals: "ISO", "E", "ITU-R", "ISO/TS", "BS.468-4". */
const CAPITALS = /^[A-Z][A-Z0-9]*(?:[./-][A-Z0-9]+)*$/;
/** Words a designation is spelled with besides abbreviations and numbers. */
const DESIGNATION_WORDS = new Set(['Doc', 'Mark']);
/** A unit a number keeps on its line. */
const UNIT = /^(?:[kMG]?Hz|dB[A-Z]?|m?s|[mck]?m|kg|k?Pa|°C|K|%)$/;
/** Every size a title can be set at. */
const SIZES = [68, 58, 48, 44, 40, 34];

/**
 * The size a title's length gives it, which the card never exceeds: 68 px up
 * to 22 characters, 58 up to 38, 48 up to 56, 40 up to 78 and 34 beyond.
 * @param {string} title - The page title.
 */
function tableSize(title) {
  const n = title.length;
  if (n <= 22) return 68;
  if (n <= 38) return 58;
  if (n <= 56) return 48;
  if (n <= 78) return 40;
  return 34;
}

/**
 * A word without the brackets and punctuation around it.
 * @param {string} word - One space-separated word.
 */
function bare(word) {
  return word.replace(/^[([¿¡«"]+/, '').replace(/[)\]»",;:.?!]+$/, '');
}

/**
 * What a layout does that no title may: an empty list when it does nothing.
 * @param {string} title - The page title.
 * @param {string[]} lines - The lines the card set it in.
 * @param {number} size - The size it set them at.
 */
function brokenRules(title, lines, size) {
  const out = [];
  if (lines.length < 1 || lines.length > 2) out.push(`${lines.length} lines`);
  if (lines.join(' ') !== title) {
    out.push(
      lines.join('') === title
        ? 'breaks inside a word, as a hyphenated compound broken at its hyphen'
        : 'lines that do not give the title back',
    );
  }
  if (!SIZES.includes(size)) out.push(`${size} px, which is not a size of the scale`);
  if (size > tableSize(title)) {
    out.push(`${size} px, larger than the ${tableSize(title)} px its length gives it`);
  }
  if (lines.length !== 2) return out;
  const last = lines[0].split(' ').at(-1) ?? '';
  const first = lines[1].split(' ')[0] ?? '';
  if (!CAPITALS.test(last) && WEAK.has(last.toLowerCase())) {
    out.push(`the first line ends on "${last}"`);
  }
  const opens =
    !/[,;:]$/.test(last) && (CAPITALS.test(bare(last)) || DESIGNATION_WORDS.has(bare(last)));
  const continues =
    !first.startsWith('(') &&
    (/^\d/.test(bare(first)) || CAPITALS.test(bare(first)) || DESIGNATION_WORDS.has(bare(first)));
  if (opens && continues) out.push(`a designation split between "${last}" and "${first}"`);
  if (/^-\d/.test(first)) out.push(`the second line starts on the part number "${first}"`);
  if (['/', '&'].includes(last) || ['/', '&'].includes(first)) {
    out.push(`a break beside a "${['/', '&'].includes(last) ? last : first}" standing alone`);
  }
  if (/^\d[\d.,]*$/.test(last) && UNIT.test(bare(first))) {
    out.push(`the number "${last}" parted from its unit "${first}"`);
  }
  return out;
}

/** The width of the column an artwork leaves, and where it ends on the card. */
function columnOf(art) {
  const width = titleColumnFor(art);
  return { width, edge: TITLE_COLUMN_START + width };
}

/*
 * The table. `art` is the artwork whose column the title is set in, and `edge`
 * where that column ends on the card, x = 72 plus its width; `size` and
 * `lines` are what the card has to set, or `error` what it has to stop with.
 */
const CASES = [
  // The examples the comments in og-image.ts give.
  {
    rule: 'a conjunction opens a phrase after a comma',
    title: 'Silencers, Screens and Barriers In Situ',
    locale: 'en',
    art: 'sources-devices',
    size: 48,
    lines: ['Silencers, Screens', 'and Barriers In Situ'],
  },
  {
    rule: 'a preposition opens a phrase',
    title: 'Medición del aislamiento en laboratorio',
    locale: 'es',
    art: 'sources-devices',
    size: 48,
    lines: ['Medición del aislamiento', 'en laboratorio'],
  },
  {
    rule: 'a preposition opens a phrase, after an article inside the first',
    title: 'Sending a simulation to a remote node',
    locale: 'en',
    art: 'simulation',
    size: 58,
    lines: ['Sending a simulation', 'to a remote node'],
  },
  {
    rule: 'a Spanish "a" opens a phrase before an article',
    title: 'Ruido de climatización a la alemana',
    locale: 'es',
    art: 'simulation',
    size: 58,
    lines: ['Ruido de climatización', 'a la alemana'],
  },
  {
    rule: 'a Spanish "a" opens a phrase before an article, on the real title',
    title: 'Ruido de climatización a la alemana (VDI 2081)',
    locale: 'es',
    art: 'sources-devices',
    size: 48,
    lines: ['Ruido de climatización', 'a la alemana (VDI 2081)'],
  },
  {
    rule: 'a Spanish "a" without an article ties a term, so "de" breaks instead',
    title: 'Mejora del aislamiento a impacto de suelos (ISO 16251-1)',
    locale: 'es',
    art: 'rooms-buildings',
    size: 48,
    lines: ['Mejora del aislamiento a impacto', 'de suelos (ISO 16251-1)'],
  },
  {
    rule: 'a break before "of" keeps the term after it whole',
    title: 'Sound Power of Multisource Industrial Plants',
    locale: 'en',
    art: 'sources-devices',
    size: 48,
    lines: ['Sound Power', 'of Multisource Industrial Plants'],
  },
  {
    rule: 'no break before a conjunction joining two hyphenated modifiers',
    title: 'Random-Incidence and Diffuse-Field Response (IEC 61183)',
    locale: 'en',
    art: 'core-signal-analysis',
    size: 48,
    lines: ['Random-Incidence and Diffuse-Field', 'Response (IEC 61183)'],
  },
  {
    rule: 'a break after a designation that opens the title',
    title: '2D FDTD wave simulation',
    locale: 'en',
    art: 'simulation',
    size: 58,
    lines: ['2D FDTD', 'wave simulation'],
  },
  {
    rule: 'a break before a designation that closes the title',
    title: 'Emisión de la fuente ferroviaria CNOSSOS-EU',
    locale: 'es',
    art: 'environment-transport',
    size: 48,
    lines: ['Emisión de la fuente ferroviaria', 'CNOSSOS-EU'],
  },
  {
    rule: 'a phrase an article opens stays whole, so the title steps down to 48 px',
    title: 'HVAC Noise the German Way (VDI 2081)',
    locale: 'en',
    art: 'sources-devices',
    size: 48,
    lines: ['HVAC Noise the German Way', '(VDI 2081)'],
  },
  {
    rule: 'a conjunction opens no phrase after a first line that is a stub',
    title: 'Reading and writing measurement audio',
    locale: 'en',
    art: 'generic',
    size: 58,
    lines: ['Reading and writing', 'measurement audio'],
  },

  // Which of the breaks that fit the card takes.
  {
    rule: 'a preposition opens no phrase after a first line that is a stub',
    title: 'Predicción del comportamiento de capas elásticas',
    locale: 'es',
    art: 'rooms-buildings',
    size: 48,
    lines: ['Predicción del comportamiento', 'de capas elásticas'],
  },
  {
    rule: 'a Spanish "a" before an article opens a phrase, ahead of a "de" that opens none',
    title: 'Climatización silenciosa de oficinas a la alemana',
    locale: 'es',
    art: 'rooms-buildings',
    size: 48,
    lines: ['Climatización silenciosa de oficinas', 'a la alemana'],
  },
  {
    rule: 'the break the title had, on a phrase boundary, is kept',
    title: 'Underwater acoustics: radiated noise and pile driving',
    locale: 'en',
    art: 'underwater',
    size: 48,
    lines: ['Underwater acoustics: radiated noise', 'and pile driving'],
  },
  {
    rule: 'a second line of one short word is avoided',
    title: 'Wave propagation models',
    locale: 'en',
    art: 'simulation',
    size: 58,
    lines: ['Wave', 'propagation models'],
  },

  // Sizes: the largest and the smallest the length gives, then line ends and
  // the steps down they force.
  {
    rule: 'up to 22 characters, 68 px',
    title: 'Sound Power in a Duct',
    locale: 'en',
    art: 'sources-devices',
    size: 68,
    lines: ['Sound Power', 'in a Duct'],
  },
  {
    rule: 'beyond 78 characters, 34 px, though 40 px would fit',
    title: 'Determinación de los niveles de potencia acústica de fuentes de ruido por presión',
    locale: 'es',
    art: 'generic',
    size: 34,
    lines: ['Determinación de los niveles de potencia acústica', 'de fuentes de ruido por presión'],
  },
  {
    rule: 'no line ends on "the", so the title steps down to 48 px',
    title: 'Sound Power in the Reverberation Room',
    locale: 'en',
    art: 'sources-devices',
    size: 48,
    lines: ['Sound Power', 'in the Reverberation Room'],
  },
  {
    rule: 'no line ends on "de", so the title steps down to 44 px',
    title: 'Potencia acústica en salas de ensayo pequeñas (ISO 3743)',
    locale: 'es',
    art: 'sources-devices',
    size: 44,
    lines: ['Potencia acústica en salas', 'de ensayo pequeñas (ISO 3743)'],
  },
  {
    rule: 'the break after a colon holds two sizes down, at 40 px',
    title: 'Dónde se calcula una simulación: NumPy, CuPy y torch',
    locale: 'es',
    art: 'simulation',
    size: 40,
    lines: ['Dónde se calcula una simulación:', 'NumPy, CuPy y torch'],
  },
  {
    rule: 'a title that fits no size of the column stops the build',
    title:
      'Determination of sound power levels and sound energy levels of noise sources using ' +
      'sound pressure (ISO 3744)',
    locale: 'en',
    art: 'simulation',
    error: /does not fit two lines of a 599 px column even at 34 px\. Shorten it/,
  },

  // Designations and the other parts a line never splits.
  {
    rule: '"E DIN 45672-3" stays whole',
    title: 'Railway vibration E DIN 45672-3 prediction',
    locale: 'en',
    art: 'simulation',
    size: 48,
    lines: ['Railway vibration', 'E DIN 45672-3 prediction'],
  },
  {
    rule: '"E DIN 45672-3" stays whole, so the title steps down to 48 px',
    title: 'Pronóstico E DIN 45672-3 de vibración',
    locale: 'es',
    art: 'simulation',
    size: 48,
    lines: ['Pronóstico E DIN 45672-3', 'de vibración'],
  },
  {
    rule: '"E DIN 45672-3" in brackets',
    title: 'Predicting railway vibration (E DIN 45672-3)',
    locale: 'en',
    art: 'vibration',
    edge: 917,
    size: 48,
    lines: ['Predicting railway vibration', '(E DIN 45672-3)'],
  },
  {
    rule: '"ECAC Doc 29" stays whole and opens the title',
    title: 'ECAC Doc 29 airport noise contours',
    locale: 'en',
    art: 'simulation',
    size: 58,
    lines: ['ECAC Doc 29', 'airport noise contours'],
  },
  {
    rule: '"ECAC Doc 29" in brackets',
    title: 'Ruido de aeropuertos (ECAC Doc 29)',
    locale: 'es',
    art: 'environment-transport',
    size: 58,
    lines: ['Ruido de aeropuertos', '(ECAC Doc 29)'],
  },
  {
    rule: '"ISO/TS 12913" stays whole',
    title: 'Soundscape ISO/TS 12913 survey analysis',
    locale: 'en',
    art: 'simulation',
    size: 48,
    lines: ['Soundscape ISO/TS 12913', 'survey analysis'],
  },
  {
    rule: '"ISO/TS 12913" in brackets',
    title: 'Análisis del paisaje sonoro (ISO/TS 12913)',
    locale: 'es',
    art: 'environment-transport',
    size: 48,
    lines: ['Análisis del paisaje sonoro', '(ISO/TS 12913)'],
  },
  {
    rule: 'a part number never starts a line',
    title: 'Audiometry ISO 8253-1, -2 compared',
    locale: 'en',
    art: 'simulation',
    size: 48,
    lines: ['Audiometry', 'ISO 8253-1, -2 compared'],
  },
  {
    rule: 'no break beside a slash standing alone',
    title: 'Ruido de salas NC / RC Mark II',
    locale: 'es',
    art: 'simulation',
    size: 58,
    lines: ['Ruido de salas', 'NC / RC Mark II'],
  },
  {
    rule: 'no break beside a slash standing alone, nor inside "RC Mark II"',
    title: 'Room noise NC / RC Mark II ratings',
    locale: 'en',
    art: 'simulation',
    size: 58,
    lines: ['Room noise', 'NC / RC Mark II ratings'],
  },
  {
    rule: 'no break beside an ampersand standing alone',
    title: 'Speech STOI & ESTOI intelligibility',
    locale: 'en',
    art: 'simulation',
    size: 58,
    lines: ['Speech STOI & ESTOI', 'intelligibility'],
  },
  {
    rule: 'a number keeps its unit',
    title: 'Wind turbine 63 Hz tonal audibility',
    locale: 'en',
    art: 'simulation',
    size: 58,
    lines: ['Wind turbine 63 Hz', 'tonal audibility'],
  },
  {
    rule: 'a hyphenated compound stays whole',
    title: 'Ondas elásticas y acoplamiento fluido-sólido',
    locale: 'es',
    art: 'simulation',
    size: 48,
    lines: ['Ondas elásticas', 'y acoplamiento fluido-sólido'],
  },

  // One title per artwork whose column is narrower than the card's widest,
  // and one in the widest, each set as that column sets it.
  {
    rule: 'the wave-simulation column',
    title: 'Where a simulation runs: NumPy, CuPy and torch',
    locale: 'en',
    art: 'simulation',
    edge: 671,
    size: 48,
    lines: ['Where a simulation runs:', 'NumPy, CuPy and torch'],
  },
  {
    rule: 'the sources-and-devices column, with a number and its unit',
    title: 'Sound Power in the 16 kHz Octave (ISO 9295)',
    locale: 'en',
    art: 'sources-devices',
    edge: 719,
    size: 48,
    lines: ['Sound Power', 'in the 16 kHz Octave (ISO 9295)'],
  },
  {
    rule: 'the materials column',
    title: 'Dynamic stiffness of resilient materials',
    locale: 'en',
    art: 'materials-surfaces',
    edge: 795,
    size: 48,
    lines: ['Dynamic stiffness', 'of resilient materials'],
  },
  {
    rule: 'the vibration column, with a hyphenated compound',
    title: 'Verifying a human-vibration meter',
    locale: 'en',
    art: 'vibration',
    edge: 917,
    size: 58,
    lines: ['Verifying', 'a human-vibration meter'],
  },
  {
    rule: 'the widest column, on the generic artwork',
    title: 'Erratas de las fuentes publicadas',
    locale: 'es',
    art: 'generic',
    edge: 932,
    size: 58,
    lines: ['Erratas de las fuentes publicadas'],
  },
];

/**
 * Every page that gets a card, with its title, as the card endpoint sees
 * them: the docs collection, which Starlight loads from every .md and .mdx
 * file here whose name does not start with an underscore, under the id Astro
 * derives from its path, less the API reference (src/pages/og/[...slug].jpg.ts,
 * isApiReference).
 *
 * The titles are read out of the frontmatter by hand, as a top-level `title:`
 * holding one scalar on one line, because site/ has no YAML parser installed.
 * A title written any other way stops the check rather than being read wrong.
 */
function readPages() {
  const pages = [];
  const problems = [];
  const walk = (dir) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) walk(path);
      else if (/^[^_].*\.(?:markdown|mdown|mkdn|mkd|mdwn|md|mdx)$/.test(entry.name)) {
        pages.push({ file: path });
      }
    }
  };
  walk(CONTENT);
  const out = [];
  for (const page of pages) {
    const name = relative(SITE, page.file);
    const text = readFileSync(page.file, 'utf8');
    const end = text.indexOf('\n---', 3);
    if (!text.startsWith('---') || end < 0) {
      problems.push(`${name}: no frontmatter`);
      continue;
    }
    const fields = {};
    const lines = text.slice(3, end).split(/\r?\n/);
    lines.forEach((line, i) => {
      const field = /^(title|slug):[ \t]*(.*)$/.exec(line);
      if (!field) return;
      fields[field[1]] = scalar(field[2], name, problems);
      // A value that goes on over the next line, which YAML allows and this
      // reader would cut short.
      if (/^[ \t]+[^ \t#]/.test(lines[i + 1] ?? '')) {
        problems.push(`${name}: a ${field[1]} that goes on over more than one line`);
      }
    });
    if (typeof fields.title !== 'string' || fields.title === '') {
      problems.push(`${name}: no title this reader can follow`);
      continue;
    }
    // Astro's id: the path without its extension, each segment slugged, and
    // without a closing "/index"; a `slug` in the frontmatter replaces it.
    // The segments are already slugs, which this keeps true rather than
    // slugging them again here.
    const segments = relative(CONTENT, page.file)
      .replace(/\.\w+$/, '')
      .split(sep);
    if (!segments.every((s) => /^[a-z0-9_-]+$/.test(s))) {
      problems.push(`${name}: a path Astro would slug into another id`);
      continue;
    }
    const id = fields.slug ?? segments.join('/').replace(/\/index$/, '');
    if (/^(es\/)?reference\/api\//.test(id)) continue;
    const locale = id === 'es' || id.startsWith('es/') ? 'es' : 'en';
    out.push({ id, title: fields.title, locale, art: artKeyFor(id) });
  }
  return { pages: out, problems };
}

/**
 * One frontmatter scalar on one line: double-quoted, single-quoted or plain.
 * @param {string} raw - What follows the key.
 * @param {string} name - The file, for a problem.
 * @param {string[]} problems - Where a value this cannot follow goes.
 */
function scalar(raw, name, problems) {
  const value = raw.trim();
  const double = /^("(?:[^"\\]|\\.)*")[ \t]*(?:#.*)?$/.exec(value);
  if (double) {
    try {
      return JSON.parse(double[1]);
    } catch {
      problems.push(`${name}: an escape in ${value} this reader does not follow`);
      return undefined;
    }
  }
  const single = /^'((?:[^']|'')*)'[ \t]*(?:#.*)?$/.exec(value);
  if (single) return single[1].replaceAll("''", "'");
  if (/^["'|>&*!%@`[{]/.test(value) || value === '') {
    problems.push(
      `${name}: ${value || 'an empty value'}, written in a form this reader does not follow`,
    );
    return undefined;
  }
  return value.replace(/[ \t]+#.*$/, '');
}

/**
 * The width of each line set in the card's title type at its size, in pixels,
 * laid out by satori as the card lays it out. Lines of one size go in one
 * layout, keyed by size and text.
 * @param {{ size: number, lines: string[] }[]} layouts - What the card set.
 * @param {unknown} fonts - The card's fonts.
 */
async function measure(layouts, fonts) {
  const bySize = new Map();
  for (const { size, lines } of layouts) {
    if (!bySize.has(size)) bySize.set(size, new Set());
    for (const line of lines) bySize.get(size).add(line);
  }
  const widths = new Map();
  for (const [size, set] of bySize) {
    const lines = [...set];
    const children = lines.map((line, i) => ({
      type: 'div',
      key: i,
      props: { style: { display: 'flex', ...titleType(size) }, children: line },
    }));
    await satori(
      {
        type: 'div',
        key: null,
        props: {
          style: { display: 'flex', flexDirection: 'column', alignItems: 'flex-start' },
          children,
        },
      },
      {
        width: 16 * 1200,
        fonts,
        pointScaleFactor: 1000,
        onNodeDetected: (node) => {
          if (typeof node.key === 'number') widths.set(`${size}|${lines[node.key]}`, node.width);
        },
      },
    );
  }
  return (size, line) => widths.get(`${size}|${line}`) ?? Infinity;
}

// The card prices a line at one size and scales it to the others; set again
// at its own size here, a line comes out within a thousandth of a pixel of
// that, which this much slack absorbs.
const EDGE_SLACK = 0.01;

/**
 * The lines of a layout that pass the end of their column.
 * @param {(size: number, line: string) => number} widthOf - Measured widths.
 * @param {{ size: number, lines: string[] }} layout - What the card set.
 * @param {{ width: number, edge: number }} column - The column.
 */
function overflows(widthOf, layout, column) {
  return layout.lines
    .map((line) => ({ line, width: widthOf(layout.size, line) }))
    .filter(({ width }) => width > column.width + EDGE_SLACK)
    .map(
      ({ line, width }) =>
        `"${line}" ends at x = ${(TITLE_COLUMN_START + width).toFixed(1)}, past the column's ${column.edge}`,
    );
}

const show = (size, lines) => `${size} px: ${lines.map((l) => `"${l}"`).join(' / ')}`;

const fonts = await cardFonts();

// 1. The table.
const caseFailures = [];
const caseLayouts = [];
for (const c of CASES) {
  const column = columnOf(c.art);
  const where = `"${c.title}" (${c.locale}, ${c.art} column, x = ${TITLE_COLUMN_START} to ${column.edge})`;
  const fail = (...what) =>
    caseFailures.push(`  ${c.rule}: ${where}\n${what.map((w) => `    ${w}`).join('\n')}`);
  if (c.edge !== undefined && c.edge !== column.edge) {
    fail(
      `the column ends at x = ${column.edge}, and the case is written for one ending at ${c.edge}`,
    );
    continue;
  }
  let got;
  try {
    got = await layOutTitle(c.title, column.width, fonts, c.locale);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (!c.error) fail(`expected ${show(c.size, c.lines)}`, `stopped with: ${message}`);
    else if (!c.error.test(message))
      fail(`expected an error matching ${c.error}`, `stopped with: ${message}`);
    continue;
  }
  if (c.error) {
    fail(`expected an error matching ${c.error}`, `got ${show(got.size, got.lines)}`);
    continue;
  }
  const broken = brokenRules(c.title, got.lines, got.size);
  if (got.size !== c.size || got.lines.join('\n') !== c.lines.join('\n') || broken.length > 0) {
    fail(`expected ${show(c.size, c.lines)}`, `got      ${show(got.size, got.lines)}`, ...broken);
  }
  caseLayouts.push({ c, column, got });
}

// 2. Every page title.
const { pages, problems } = readPages();
if (problems.length > 0) {
  console.error(
    `check-social-card-titles: frontmatter this check cannot read:\n  ${problems.join('\n  ')}`,
  );
  process.exit(1);
}
if (pages.length === 0) {
  console.error(`check-social-card-titles: no page titles under ${CONTENT}.`);
  process.exit(1);
}
const pageFailures = [];
const pageLayouts = [];
for (const page of pages) {
  const column = columnOf(page.art);
  try {
    const got = await layOutTitle(page.title, column.width, fonts, page.locale);
    pageLayouts.push({ page, column, got });
  } catch (error) {
    pageFailures.push(
      `  ${page.id}, "${page.title}": ${error instanceof Error ? error.message : error}`,
    );
  }
}

const widthOf = await measure(
  [...caseLayouts, ...pageLayouts].map(({ got }) => got),
  fonts,
);
for (const { c, column, got } of caseLayouts) {
  const past = overflows(widthOf, got, column);
  if (past.length > 0) caseFailures.push(`  ${c.rule}: "${c.title}"\n    ${past.join('\n    ')}`);
}
for (const { page, column, got } of pageLayouts) {
  const broken = [
    ...brokenRules(page.title, got.lines, got.size),
    ...overflows(widthOf, got, column),
  ];
  if (broken.length > 0) {
    pageFailures.push(
      `  ${page.id}, ${show(got.size, got.lines)} in the ${page.art} column:\n    ${broken.join('\n    ')}`,
    );
  }
}

if (caseFailures.length > 0) {
  console.error(
    `${caseFailures.length} of ${CASES.length} titles of the table in ` +
      'scripts/check-social-card-titles.mjs are not set as they state (src/utils/og-image.ts):',
  );
  console.error(caseFailures.join('\n'));
}
if (pageFailures.length > 0) {
  console.error(
    `${pageFailures.length} of ${pages.length} page titles break a rule of the social card:`,
  );
  console.error(pageFailures.slice(0, 40).join('\n'));
  if (pageFailures.length > 40) console.error(`  ... and ${pageFailures.length - 40} more`);
}
if (caseFailures.length > 0 || pageFailures.length > 0) process.exit(1);

const english = pages.filter((p) => p.locale === 'en').length;
console.log(
  `${CASES.length} titles of the table are set at their stated size and lines, and the ` +
    `${pages.length} page titles that get a social card (${english} English, ` +
    `${pages.length - english} Spanish) take at most two lines inside their column, at no ` +
    'larger size than their length gives them, with no line ending on a weak word and no ' +
    'designation, part number, slash, ampersand, compound or number and unit split.',
);
