// The size of every page the build wrote, as a crawler downloads it.
//
// Googlebot "crawls the first 2MB of a supported file type", "the file size
// limit is applied on the uncompressed data", and only the part it downloaded
// is sent on for indexing (Google Search Central, "Googlebot", updated
// 2026-02-03). Nothing reports the cut: the page shows as indexed, and the
// text past it is simply never in the index. Six pages of this site were past
// it while every check of the build stayed green, and the largest lost most of
// what it published:
//
// - the published catalogues, 4.7 MB in English and 5.2 MB in Spanish, kept 13
//   of their 25 sections out of the index, from the carpets to the air
//   attenuation;
// - the errata registry, 4.9 MB, lost 227 of its 351 entries;
// - the conformance report, 2.5 MB, lost its last 349 rows.
//
// So this reads the build with no browser and no server and fails on any HTML
// file over 1 800 000 bytes. That is a tenth under the 2 000 000 bytes the
// smaller reading of "2MB" gives, so a page is caught while a table can still
// grow by some rows, rather than on the day its tail drops out of the index.
// The size is counted on the file as written, which is the uncompressed size
// the limit applies to.
//
// Usage: node scripts/check-page-size.mjs [dist-directory]
import { existsSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { reporter, walk } from './shared/dist-pages.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const DIST = process.argv[2] ? resolve(process.argv[2]) : join(here, '..', 'dist');
/** The most bytes of HTML a page may carry: a tenth under a 2 000 000-byte fetch. */
const MAX_BYTES = 1_800_000;

const { report, failures } = reporter();

if (!existsSync(DIST)) throw new Error(`no build at ${DIST}: run \`pnpm build\` first`);

/** Bytes with a space every three digits, the way the site writes numbers. */
const bytes = (count) => `${String(count).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')} bytes`;

const sizes = [...walk(DIST)].map(([route, file]) => ({ route, size: statSync(file).size }));
sizes.sort((a, b) => b.size - a.size);
console.log(`read ${sizes.length} HTML files in ${DIST}`);
if (sizes.length > 0) console.log(`the largest is ${sizes[0].route}, ${bytes(sizes[0].size)}`);

report(
	sizes.filter(({ size }) => size > MAX_BYTES).map(({ route, size }) => `${route}: ${bytes(size)}`),
	`page(s) over ${bytes(MAX_BYTES)} of HTML, whose tail a crawler never reads`,
	`every page is at most ${bytes(MAX_BYTES)} of HTML`,
);

console.log(`\n${failures()} failing check(s).`);
process.exit(failures() ? 1 : 0);
