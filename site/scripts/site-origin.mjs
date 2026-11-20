// Moves the hand-written files of public/ to the host the build was made for.
//
// Everything Astro writes names the host through src/data/site.mjs, which
// reads PHONOMETRY_SITE. Two files of public/ are copied into dist/ verbatim
// and name docs.jmrp.io by hand: robots.txt (its Sitemap line and the
// addresses its comments give) and sitemap.xml (the shard it points to). A
// build for another host rewrites them here, after Astro. The default build
// is the one docs.jmrp.io serves, and this step leaves it alone, byte for
// byte. A listed file that no longer names docs.jmrp.io fails the build, so
// the list cannot outlive the files it describes.
//
// Usage: node scripts/site-origin.mjs   (package.json postbuild, first)
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { DEFAULT_SITE, SITE_TARGETS, siteUrl } from '../src/data/site.mjs';

/**
 * The origin public/ is written for: that of the build made with nothing set
 * (scripts/public-files.test.mjs holds the files to it).
 */
export const CANONICAL_ORIGIN = SITE_TARGETS[DEFAULT_SITE].siteUrl;

/** The files of public/ that name it, as dist/ holds them. */
export const ORIGIN_FILES = Object.freeze(['robots.txt', 'sitemap.xml']);

/**
 * Rewrites the listed files of a build for an origin.
 *
 * @param {string} dist The build.
 * @param {string} origin The origin the build was made for.
 * @returns {string[]} The files rewritten; none for the canonical origin.
 * @throws {Error} When a listed file does not name the canonical origin.
 */
export function moveOrigin(dist, origin) {
	if (origin === CANONICAL_ORIGIN) return [];
	const moved = [];
	for (const name of ORIGIN_FILES) {
		const path = join(dist, name);
		const text = readFileSync(path, 'utf8');
		const rewritten = text.replaceAll(CANONICAL_ORIGIN, origin);
		if (rewritten === text) throw new Error(`${name} names no ${CANONICAL_ORIGIN}; take it off ORIGIN_FILES`);
		writeFileSync(path, rewritten);
		moved.push(name);
	}
	return moved;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	const dist = fileURLToPath(new URL('../dist/', import.meta.url));
	const moved = moveOrigin(dist, siteUrl);
	if (moved.length > 0) console.log(`[site-origin] ${moved.join(', ')} now name ${siteUrl}`);
}
