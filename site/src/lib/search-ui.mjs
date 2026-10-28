/**
 * Starlight's search UI with the designation query normalizer wired in.
 *
 * A reader looking for the Spanish adoption of a standard types "UNE-EN ISO
 * 3744", and a British one "BS EN ISO 3744". No page declares either: the
 * bibliography records ISO 3744, which is the document the guide was written
 * to. Pagefind deletes the hyphen without splitting the word, so the query
 * becomes the term `uneen`, which appears nowhere, and the search comes back
 * with nothing worth reading.
 *
 * The fix belongs on the query, not in the index. Writing UNE-EN into the
 * index would have the site assert a national adoption nobody has verified;
 * dropping the prefix from what was typed asserts nothing and finds the guide.
 * `processTerm` is the option Pagefind's UI provides for exactly this, and it
 * cannot be set from Starlight's `pagefind` config, which is serialised to JSON
 * and so drops functions. Hence this subclass, aliased over the package name in
 * astro.config.mjs.
 *
 * The search box keeps showing the reader's own words; only what is searched
 * for changes.
 *
 * The same subclass shows a page's `display_title` in place of the title it is
 * ranked by, when the page has one. The errata pages are ranked by an empty
 * title and shown by their own (src/lib/search-ranking.mjs says why);
 * `processResult` is the option Pagefind's UI calls on every result before it
 * draws it, and Starlight already passes one, which rewrites the URLs, so it
 * runs first and this one after it.
 */
import { PagefindUI as Upstream } from 'pagefind-default-ui-upstream';
// From its own module, never from standard-search.mjs: the tokenizer and its
// overrides table are build-time data, and importing through it would ship
// them to every reader who opens the search panel.
import { normalizeDesignationQuery, SEARCH_TERM_NORMALIZER_MARK } from './designation-query.mjs';

export class PagefindUI extends Upstream {
  constructor(options) {
    // The marker is the only evidence that reaches the built bundle. The
    // alias above is a silent piece of wiring: if Starlight ever stops
    // importing the package by its bare name it simply stops applying, with
    // nothing to notice. scripts/check-search-designation.mjs greps the
    // built JavaScript for this string.
    globalThis.__phonometrySearchNormalizer = SEARCH_TERM_NORMALIZER_MARK;
    // A fresh object, not the caller's: the upstream constructor `delete`s
    // the keys it consumes out of whatever it is handed.
    const upstreamResult = options?.processResult;
    super({
      ...options,
      processTerm: normalizeDesignationQuery,
      processResult: (result) => {
        const processed = upstreamResult?.(result) ?? result;
        return showDisplayTitle(processed);
      },
    });
  }
}

/**
 * Put a result's `display_title` where the panel reads its title, and drop
 * the field, which the panel would otherwise print as a tag under the result.
 *
 * @param {{meta?: Record<string, string>}} result  One Pagefind result.
 * @returns {typeof result} The same result.
 */
export function showDisplayTitle(result) {
  const shown = result?.meta?.display_title;
  if (shown) {
    result.meta.title = shown;
    delete result.meta.display_title;
  }
  return result;
}
