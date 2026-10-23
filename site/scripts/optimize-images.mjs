// Recompresses the raster images the site serves (dist/ only; sources in
// public/ and src/ are never touched). PNGs are palette-quantized and JPEGs
// re-encoded with mozjpeg, each rewritten only when the result is smaller.
// SVG (all the figure pipeline output) passes through untouched, and WebP
// siblings are intentionally not emitted: every raster the site references
// today is a social-card or manifest image whose consumers (Open Graph and
// Twitter crawlers, web-app manifests) expect PNG/JPEG, and the content
// figures are remote SVG/WebP/WebM, so there is no <img> that could take a
// <picture> WebP source with fallback.
import { readdirSync, statSync, readFileSync, writeFileSync } from 'node:fs';
import { join, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { encoders, recompress } from './shared/recompress.mjs';

const dist = fileURLToPath(new URL('../dist', import.meta.url));

function* walk(dir) {
	for (const entry of readdirSync(dir)) {
		const p = join(dir, entry);
		if (statSync(p).isDirectory()) yield* walk(p);
		else yield p;
	}
}

// PNG IHDR colour type (byte 25): 3 = indexed/palette. An indexed PNG has
// already been through the palette quantization; skip it so re-running the
// postbuild by hand cannot re-quantize (and degrade) an optimized image.
function isIndexedPng(file, buffer) {
	return extname(file).toLowerCase() === '.png' && buffer.length > 25 && buffer[25] === 3;
}

// The animation posters are lossy WebP already, extracted from the clips at
// the quality scripts/figures/media.py chose. A second lossy encode at 82
// would come out a little smaller and be kept for it, having lost twice.
function isAnimationPoster(file) {
	return /\/anim_[^/]*_poster\.webp$/.test(file);
}

// How many images are in flight at once. The step used to run one image at
// a time and took two minutes over the ~630 rasters a build emits, almost
// all of it inside sharp's native encoders, which do their work off the
// event loop, on libuv's thread pool. Four matches the CI runner's cores;
// the encode order changes, the bytes written do not, and the log is
// printed per file as before, merely interleaved.
const IN_FLIGHT = 4;

/** @param {string} file - Absolute path of one raster inside dist/. */
async function optimize(file) {
	const extension = extname(file).toLowerCase();
	if (!Object.hasOwn(encoders, extension)) return null;
	const original = readFileSync(file);
	if (isIndexedPng(file, original) || isAnimationPoster(file)) return null;
	let kept;
	try {
		kept = await recompress(original, extension);
	} catch (error) {
		// A broken or mislabelled image must not kill the deploy: keep the
		// original byte-for-byte and report which file failed.
		console.warn(
			`[optimize-images] skipping ${file.slice(dist.length + 1)}: ${error.message}`,
		);
		return null;
	}
	if (kept !== original) writeFileSync(file, kept);
	console.log(
		`[optimize-images] ${file.slice(dist.length + 1)}: ` +
			`${(original.length / 1024).toFixed(0)} KiB -> ${(kept.length / 1024).toFixed(0)} KiB`,
	);
	return { before: original.length, after: kept.length };
}

let totalBefore = 0;
let totalAfter = 0;
const files = [...walk(dist)];
let next = 0;
await Promise.all(
	Array.from({ length: IN_FLIGHT }, async () => {
		while (next < files.length) {
			const file = files[next++];
			const result = await optimize(file);
			if (result) {
				totalBefore += result.before;
				totalAfter += result.after;
			}
		}
	}),
);
if (totalBefore === 0) {
	console.log('[optimize-images] nothing to recompress in dist/');
} else {
	const saved = ((1 - totalAfter / totalBefore) * 100).toFixed(0);
	console.log(
		`[optimize-images] total ${(totalBefore / 1024).toFixed(0)} KiB -> ` +
			`${(totalAfter / 1024).toFixed(0)} KiB (${saved}% smaller)`,
	);
}
