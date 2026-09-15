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
    super({ ...options, processTerm: normalizeDesignationQuery });
  }
}
