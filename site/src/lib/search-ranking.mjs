/**
 * Pagefind ranking options, shared by the site build and the check that proves
 * the ranking still does what it is for.
 *
 * They live in their own module rather than inline in astro.config.mjs so the
 * two cannot drift: scripts/check-search-designation.mjs imports this same
 * object and measures the index with it, so a weight changed in one place is a
 * weight changed in both.
 *
 * Only `metaWeights` is set. Starlight's schema gives every other ranking field
 * its own default and prefills the object, so naming one field keeps pageLength
 * 0.1, termFrequency 0.1, termSaturation 2, termSimilarity 9 and
 * diacriticSimilarity 0.8. Pagefind in turn merges `metaWeights` into its own
 * map, so the built-in title weight of 5 survives too.
 *
 * The weight is the lowest one that does the whole job. Measured on the real
 * index, over every designation the bibliographies declare, in both languages:
 * at 1 a guide that merely discusses ISO 3744 still outranks one written to it;
 * 2 fixes the order everywhere but leaves the worst case only 1.59 times ahead
 * of the best page that does not declare the standard; 3 puts it 2.38 times
 * ahead; 5 buys 3.95 times and correspondingly more pull on everything else.
 * The check asks for a factor of two, so 3 is what ships.
 */
export const PAGEFIND_RANKING = { metaWeights: { standards: 3 } };

/**
 * Starlight's own ranking defaults, repeated here because the check runs
 * Pagefind directly rather than through Starlight's Search component.
 * src/schemas/pagefind.js in @astrojs/starlight is the source.
 */
export const STARLIGHT_RANKING_DEFAULTS = {
  pageLength: 0.1,
  termFrequency: 0.1,
  termSaturation: 2,
  termSimilarity: 9,
  diacriticSimilarity: 0.8,
};
