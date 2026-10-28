/**
 * The conformance verdict marks, as CSS images the page draws beside each
 * verdict word.
 *
 * The same four files GitHub reads over `raw.githubusercontent.com`
 * (`.github/badges/verdict-*.svg`, written by `scripts/conformance_badges.py`),
 * read off disk at build time and turned into four `data:` URLs, which the
 * report sets once on its root element as custom properties
 * (`--cv-pass`, `--cv-fail`, ...). Every place that shows a verdict carries the
 * verdict as an attribute, and one CSS rule draws the matching mark in a
 * `::before` box beside the word.
 *
 * **Drawn by CSS, not by markup, and the reason is arithmetic.** The report
 * draws a mark on every one of its rows, and there are close to two thousand
 * of them. Fetched as `<img>`, each would be a layout box that arrives late and
 * an `alt` a screen reader announces beside a word the row already states.
 * Inlined as a sprite, the geometry costs a kilobyte once, but every row still
 * spends about a hundred bytes on the `<svg><use>` that points at it: 200 kB
 * of the page at 1,893 rows, which was a tenth of everything Googlebot reads
 * of a page before it stops (2 MB, counted uncompressed). As a CSS image the
 * mark costs nothing per row, needs no request, cannot flash, and is still
 * invisible to assistive technology, which hears the word.
 *
 * The fills come across unchanged. They were chosen against every ground the
 * marks land on at once - GitHub's three canvases and two table stripes, and
 * this site's own two page colours (`#ffffff` and `#0d1114`, because
 * `src/styles/theme.css` overrides Starlight's `--sl-color-black`) and two
 * card colours - precisely so that one file is right in every theme, and
 * `tests/test_conformance_badges.py` measures all nine rather than asserting
 * them, GitHub's dimmed table stripe included, which is the single ground the
 * fills fall short on and the one place that test names an exception. So
 * there is nothing here to re-theme, and re-theming would fork a palette that
 * is currently measured in one place.
 *
 * Read from the repository rather than copied into `public/`: a copy is a
 * second thing to keep in step, and `scripts/stage-media.mjs` exists for the
 * figures because those are megabytes, which these are not.
 */
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * Locate the committed badge directory by walking up from a starting point.
 *
 * Same shape as `src/data/conformance-stats.mjs`, and for the same reason: a
 * literal relative URL breaks once Astro bundles this module into
 * `dist/.prerender/chunks/`, where the hops count from the chunk instead of
 * from `src/lib/`.
 *
 * @returns {string} Absolute path of `.github/badges`.
 */
function findBadgeDir() {
  const starts = [dirname(fileURLToPath(import.meta.url)), process.cwd()];
  for (const start of starts) {
    let dir = start;
    for (;;) {
      const candidate = join(dir, '.github', 'badges');
      if (existsSync(join(candidate, 'verdict-pass.svg'))) return candidate;
      const parent = dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  }
  throw new Error(
    '.github/badges/verdict-pass.svg not found above ' +
      starts.join(' or ') +
      '. Regenerate the indicators with `make conformance`.',
  );
}

/**
 * The verdicts, in the order a legend should read them, paired with the file
 * each one is drawn in. Mirrors `MARKS` in `scripts/conformance/marks.py`,
 * which is the one thing here that cannot be derived: the order is editorial,
 * and the site does not run Python.
 *
 * What the mirror is held to is checked below rather than assumed. A rename
 * would already fail loudly, because the read throws; a *fifth* verdict added
 * on the Python side would not, and the page would quietly draw the
 * not-applicable ring for it for ever.
 */
const FILES = [
  ['pass', 'verdict-pass.svg'],
  ['fail', 'verdict-fail.svg'],
  ['by-design', 'verdict-by-design.svg'],
  ['not-applicable', 'verdict-not-applicable.svg'],
];

const BADGE_DIR = findBadgeDir();

// The directory is the authority on how many marks there are. Failing the
// build with this sentence is the whole point: the alternative is a page that
// renders, looks right, and is wrong about one verdict.
const onDisk = readdirSync(BADGE_DIR)
  .filter((name) => name.startsWith('verdict-') && name.endsWith('.svg'))
  .sort();
const named = FILES.map(([, file]) => file).sort();
if (onDisk.join() !== named.join()) {
  throw new Error(
    `.github/badges holds [${onDisk}] but this module names [${named}]. ` +
      'Add the new verdict to FILES in src/lib/verdict-marks.mjs, and its word ' +
      'to both `verdicts` tables in src/components/Conformance.astro.',
  );
}

/**
 * The drawn geometry of one mark, without its root element or its title.
 *
 * The `<title>` is dropped on purpose. It is the text alternative for a reader
 * who opens the file on its own; inside the page the word beside the mark is
 * the alternative, and a CSS image has no name to announce anyway.
 *
 * @param {string} file  Filename under `.github/badges`.
 * @returns {string} The inner markup.
 */
function geometry(file) {
  const source = readFileSync(join(BADGE_DIR, file), 'utf8');
  const inner = source.match(/<svg\b[^>]*>([\s\S]*)<\/svg>/);
  if (!inner) {
    throw new Error(`${file} is not a single <svg> element; regenerate the badges.`);
  }
  return inner[1].replace(/<title>[\s\S]*?<\/title>/, '').trim();
}

/**
 * Every verdict mark as a standalone SVG document in a `data:` URL.
 *
 * @type {{verdict: string, url: string}[]}
 */
export const marks = FILES.map(([verdict, file]) => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">${geometry(file)}</svg>`;
  return { verdict, url: `url("data:image/svg+xml,${encodeURIComponent(svg)}")` };
});

/**
 * The four marks as custom properties, for the `style` of the element that
 * holds the report: `--cv-pass:url(...);--cv-fail:url(...);...`.
 */
export const markStyle = marks.map((mark) => `--cv-${mark.verdict}:${mark.url}`).join(';');

/**
 * The verdict a mark is drawn for.
 *
 * The fallback is the hollow ring, which is the only honest one: it is the
 * mark that means "nothing was decided here". It cannot be reached by a mark
 * this module has drifted away from, because the check above makes that a
 * build failure; it is there for a verdict the artefact carries and the badge
 * vocabulary does not.
 *
 * @param {string} verdict  The verdict as the artefact spells it.
 * @returns {string} A verdict that has a mark.
 */
export function markOf(verdict) {
  return marks.some((mark) => mark.verdict === verdict) ? verdict : 'not-applicable';
}
