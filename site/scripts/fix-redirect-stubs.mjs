// Brings Astro's redirect stub pages up to the standard the rest of the site
// is held to. Runs after every build.
//
// Two things about the stub Astro writes fail `html-validate`, which the site
// runs over every built page. The doctype is lowercase where the rest of the
// site's is upper, and the title is the destination spelled out in full,
// `Redirecting to: /phonometry/es/perception/psychoacoustics/...`, which runs
// past the 70-character limit of the `long-title` rule on any address more
// than four segments deep. That cost nothing while there were eight stubs and
// all of them were shallow; the redirect map covers every address the site has
// ever published, and 66 of those titles were over the limit.
//
// The title becomes plain "Redirecting". Nothing is lost by it: the stub is on
// screen for one frame, and the destination is still in the meta refresh, the
// canonical link and the visible link in the body, which is what a reader with
// scripting or refresh disabled follows.
//
// The third rewrite is for search engines. Astro marks every stub
// `<meta name="robots" content="noindex">` (core/routing/3xx.js), and on a
// static host that undoes the redirect it stands for: Google lists such an
// address under "Excluded by 'noindex' tag" rather than as a redirect, and
// advises against noindex for choosing a canonical within one site
// ("Consolidate duplicate URLs"), so what the old address had earned does not
// pass to the page it moved to. Without it, the instant refresh and the
// canonical say the same thing, which Google reads as a permanent redirect
// ("Redirects and Google Search"). Hugo dropped the same tag from its alias
// pages for the same reason. On docs.jmrp.io these addresses answer a real 301
// at the edge (scripts/cloudflare-redirects.mjs); the stubs are what anyone
// reaching GitHub Pages directly gets.
//
// Every rewrite is guarded on the exact shape Astro emits, so they are
// idempotent and cannot touch a real page. check-redirects.mjs fails a stub
// that still carries the noindex.
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const dist = fileURLToPath(new URL('../dist/', import.meta.url));

const LOWER_DOCTYPE = '<!doctype html>';
const UPPER_DOCTYPE = '<!DOCTYPE html>';
const STUB_TITLE = /^(<!DOCTYPE html>)<title>Redirecting to: [^<]*<\/title>/;
// Only in a stub: the tag Astro writes right after the refresh (with
// compressHTML on, the line breaks of its template are gone).
const STUB_NOINDEX = /(<meta http-equiv="refresh" content="[^"]*">)\s*<meta name="robots" content="noindex">/;

function* htmlFiles(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* htmlFiles(path);
    else if (entry.name.endsWith('.html')) yield path;
  }
}

let doctypes = 0;
let titles = 0;
let noindexes = 0;
for (const file of htmlFiles(dist)) {
  let html = readFileSync(file, 'utf8');
  const before = html;
  if (html.startsWith(LOWER_DOCTYPE)) {
    html = UPPER_DOCTYPE + html.slice(LOWER_DOCTYPE.length);
    doctypes += 1;
  }
  if (STUB_TITLE.test(html)) {
    html = html.replace(STUB_TITLE, '$1<title>Redirecting</title>');
    titles += 1;
  }
  if (STUB_NOINDEX.test(html)) {
    html = html.replace(STUB_NOINDEX, '$1');
    noindexes += 1;
  }
  if (html !== before) writeFileSync(file, html);
}
console.log(
  `[fix-redirect-stubs] uppercased DOCTYPE in ${doctypes} file(s), shortened ${titles} redirect title(s), ` +
    `dropped the noindex from ${noindexes}`,
);
