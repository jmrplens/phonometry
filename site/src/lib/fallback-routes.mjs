/**
 * The Spanish routes that serve an English page, and what they declare.
 *
 * Starlight gives every English page a route in each other locale and, where
 * no translation exists, renders the English entry there (its `isFallback`
 * routes). Here that is the whole API reference: it is generated from the
 * docstrings in English only, by decision, and check-i18n-parity.mjs keeps it
 * the one subtree without a Spanish file. So every `/es/reference/api/` page
 * carries the English title, description and body of its English twin.
 *
 * Google reads such a pair as one page in two places: "Localized versions of a
 * page are only considered duplicates if the main content of the page remains
 * untranslated" (Search Central, "Tell Google about localized versions of your
 * page"), and Bing reports identical titles and descriptions across indexed
 * pages. So the Spanish copy says what it is. Its canonical, `og:url` and
 * structured data name the English page as the page's own, no hreflang pairs
 * the two (on either side: an English page pointing `hreflang="es"` at a URL
 * that canonicalises back to it is a contradiction), and the sitemap lists the
 * English page alone. No `noindex` on top: Google advises against it for
 * choosing a canonical within one site ("Consolidate duplicate URLs").
 *
 * src/routeData.ts rewrites the head, src/components/Head.astro the graph,
 * astro.config.mjs filters the sitemap, and the dist checks
 * (check-structured-data.mjs, check-crawl.mjs) hold the build to it. They all
 * read the rule from here, so it is stated once.
 */

/** A slug of the API reference, in either locale: `[es/]reference/api[/...]`. */
const API_SLUG = /^(?:es\/)?reference\/api(?:\/|$)/;

/** A slug of the Spanish API reference, the routes served as fallback. */
const SPANISH_API_SLUG = /^es\/reference\/api(?:\/|$)/;

/**
 * A route as these predicates read it: no base path, no leading or trailing
 * slash. `/phonometry/es/reference/api/` and `es/reference/api` are the same.
 *
 * @param {string} route A slug, an entry id or a pathname.
 * @param {string} [base] The site's base path, stripped when the route has it.
 * @returns {string} The bare slug.
 */
export function slugOf(route, base = '') {
  let slug = route;
  if (base && (slug === base || slug.startsWith(`${base}/`))) slug = slug.slice(base.length);
  return slug.replace(/^\/+|\/+$/g, '');
}

/**
 * Whether a route belongs to the API reference, in either locale. These are the
 * pairs whose two sides carry no hreflang to each other.
 *
 * @param {string} route A slug, an entry id or a pathname.
 * @param {string} [base] The site's base path.
 * @returns {boolean} True for the API index and every page below it.
 */
export const isApiRoute = (route, base = '') => API_SLUG.test(slugOf(route, base));

/**
 * Whether a route is a Spanish API page, which Starlight serves from the
 * English entry and which declares the English page canonical.
 *
 * @param {string} route A slug, an entry id or a pathname.
 * @param {string} [base] The site's base path.
 * @returns {boolean} True for `/es/reference/api/` and every page below it.
 */
export const isFallbackRoute = (route, base = '') => SPANISH_API_SLUG.test(slugOf(route, base));

/**
 * The English twin of a Spanish address, for a slug, a pathname or an absolute
 * URL: the `/es` segment after the base path goes, and nothing else changes.
 *
 * @param {string} address The Spanish slug, pathname or URL.
 * @param {string} [base] The site's base path.
 * @returns {string} The same address in English.
 */
export function englishTwin(address, base = '') {
  if (/^es(?:\/|$)/.test(address)) return address.replace(/^es\/?/, '');
  const prefix = `${base}/es/`;
  const at = address.indexOf(prefix);
  if (at === -1) return address;
  return `${address.slice(0, at)}${base}/${address.slice(at + prefix.length)}`;
}
