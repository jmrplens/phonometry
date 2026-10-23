// How the postbuild re-encodes a raster the site serves, shared by
// scripts/optimize-images.mjs, which rewrites dist/ with it, and
// scripts/check-social-cards.mjs, which needs a social card's bare artwork
// encoded exactly as the cards it compares it with were.
import sharp from 'sharp';

// Distinct colours above which an image is treated as photographic and kept
// off the palette path. The app icons are two flat colours plus antialiasing
// and land around 500; the Open Graph fallback card is artwork and lands near
// 15000. Quantising that one to 256 took the flat dark area from 249 grey
// levels to 22, which bands visibly, for 295 KiB nobody was asking for.
//
// `palette: false` has to be explicit on the photographic branch: passing
// `effort` (or `quality`, or `colours`) to sharp's png encoder turns the
// palette on by itself, so leaving the flag out quantises the image anyway.
const PALETTE_MAX_COLOURS = 1024;

/**
 * Counts distinct colours, to decide whether a palette will be near-lossless.
 * @param {import('sharp').Sharp} image - The decoded image.
 */
async function tooManyColours(image) {
	const { data, info } = await image
		.clone()
		.raw()
		.toBuffer({ resolveWithObject: true });
	const seen = new Set();
	for (let i = 0; i < data.length; i += info.channels) {
		seen.add((data[i] << 16) | (data[i + 1] << 8) | data[i + 2]);
		if (seen.size > PALETTE_MAX_COLOURS) return true;
	}
	return false;
}

/** The encoder of each extension the postbuild re-encodes. */
export const encoders = {
	'.png': async (image) =>
		(await tooManyColours(image))
			? image.png({ palette: false, compressionLevel: 9, effort: 10 })
			: image.png({ palette: true, quality: 90, compressionLevel: 9, effort: 10 }),
	'.jpg': (image) => image.jpeg({ mozjpeg: true, quality: 82 }),
	// The staged figure previews and animation stills (see
	// scripts/stage-media.mjs). Re-encoded at the same effort the generators
	// do not spend, since they optimise for regeneration speed.
	'.webp': (image) => image.webp({ quality: 82, effort: 6 }),
	'.jpeg': (image) => image.jpeg({ mozjpeg: true, quality: 82 }),
};

/**
 * The bytes the postbuild serves for one raster: its re-encode when that comes
 * out smaller, the original otherwise. Throws when the encoder does.
 * @param {Buffer} original - The raster as the build wrote it.
 * @param {string} extension - Its extension, which picks the encoder: one of
 *   the keys of `encoders`.
 * @returns {Promise<Buffer>} `original` itself when it is kept.
 */
export async function recompress(original, extension) {
	const key = extension.toLowerCase();
	if (!Object.hasOwn(encoders, key)) {
		throw new Error(`recompress: the postbuild does not re-encode ${extension}.`);
	}
	const optimized = await (await encoders[key](sharp(original))).toBuffer();
	return optimized.length < original.length ? optimized : original;
}
