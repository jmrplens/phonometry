/**
 * The site-wide strings that more than one place needs.
 *
 * astro.config.mjs builds every absolute URL from them, and the audit scripts
 * in site/scripts/ address the running preview with the same base, so a move
 * to another path or another host is one edit of site-targets.json rather
 * than a hunt through the checks. The repository and the author are read by the head of every page
 * and by the header of every page's Markdown copy (src/lib/agent-md/header.mjs).
 */

import targets from './site-targets.json' with { type: 'json' };

/**
 * The hosts the site can be built for, the base path under each, and the
 * build made with nothing set: site-targets.json, the one file every reader
 * takes them from. This module serves it to the build, the site scripts and
 * the Worker; scripts/site_target.py serves the same file to the Python
 * generators that write site links (the API reference, the errata pages, the
 * llms files), so no copy of a base path can lag another.
 *
 * docs.jmrp.io is the canonical site and the build with nothing set.
 * phonometry.dev is the preview served from Cloudflare (site/worker/README.md):
 * `PHONOMETRY_SITE=phonometry.dev pnpm build` names it in every canonical URL,
 * `og:url`, structured data `@id`, sitemap, Markdown copy and llms file, and in
 * robots.txt (scripts/site-origin.mjs). It keeps the base
 * path for now, so every link the pages write is the same in both builds; the
 * move to the root is a later change.
 */
export const SITE_TARGETS = Object.freeze(
  Object.fromEntries(Object.entries(targets.targets).map(([name, target]) => [name, checkedTarget(target, `target ${name}`)])),
);

/** The target a build with PHONOMETRY_SITE unset or empty is made for. */
export const DEFAULT_SITE = targets.default;

/**
 * Where the site was published before, each an origin and the base path it
 * served the pages under. Nothing is built for them: the redirect map reads
 * them to send each old address to the same page on the current target.
 */
export const LEGACY_ORIGINS = Object.freeze(targets.legacy.map((legacy, i) => checkedTarget(legacy, `legacy origin ${i}`)));

/**
 * One origin and base path, checked and frozen.
 *
 * @param {{siteUrl: string, basePath: string}} entry The entry as site-targets.json writes it.
 * @param {string} what Where it sits, for the error.
 * @returns {Readonly<{siteUrl: string, basePath: string}>} The two strings.
 * @throws {Error} When the URL is no bare https origin of a host with no port,
 *   or the base path is neither empty nor a path that starts with `/` and does
 *   not end with one: every reader appends `/route/` to the base and the route
 *   to the origin. scripts/site_target.py refuses the same values, a port
 *   among them, so a target this module accepts never stops a Python
 *   generator.
 */
export function checkedTarget({ siteUrl, basePath }, what) {
  if (typeof siteUrl !== 'string' || !siteUrl.startsWith('https://') || originOf(siteUrl) !== siteUrl || new URL(siteUrl).port !== '') {
    throw new Error(`site-targets.json: the ${what} siteUrl ${JSON.stringify(siteUrl)} is not an https origin with no port`);
  }
  if (typeof basePath !== 'string' || (basePath !== '' && !/^(?:\/[a-z0-9-]+)+$/.test(basePath))) {
    throw new Error(`site-targets.json: the ${what} basePath ${JSON.stringify(basePath)} is neither empty nor /segment`);
  }
  return Object.freeze({ siteUrl, basePath });
}

/**
 * The origin a URL names, or null when it is no URL.
 *
 * @param {string} url
 * @returns {string | null}
 */
function originOf(url) {
  try {
    return new URL(url).origin;
  } catch {
    return null;
  }
}

if (!Object.hasOwn(SITE_TARGETS, DEFAULT_SITE)) {
  throw new Error(`site-targets.json: the default ${DEFAULT_SITE} is not one of ${Object.keys(SITE_TARGETS).join(', ')}`);
}

/**
 * The target a value of PHONOMETRY_SITE names.
 *
 * @param {string | undefined} name The variable's value; unset or empty means the default target.
 * @returns {{siteUrl: string, basePath: string}} The target.
 * @throws {Error} For any other value, so a typo stops the build instead of publishing it.
 */
export function siteTarget(name) {
  const key = name === undefined || name === '' ? DEFAULT_SITE : name;
  if (!Object.hasOwn(SITE_TARGETS, key)) {
    throw new Error(`PHONOMETRY_SITE=${name} is not one of ${Object.keys(SITE_TARGETS).join(', ')}`);
  }
  return SITE_TARGETS[key];
}

// globalThis.process, not process: this module is read by the build and the
// scripts under Node, and nothing else reaches it, but the guard costs nothing.
const target = siteTarget(globalThis.process?.env?.PHONOMETRY_SITE);

export const siteUrl = target.siteUrl;
export const basePath = target.basePath;

/**
 * The origins besides the page's own that may answer a clip (`<video>`).
 *
 * The phonometry.dev preview answers a clip with a redirect to docs.jmrp.io,
 * which serves byte ranges (site/worker/lib/rules.mjs, rule
 * clips-to-range-host), and a browser checks the Content-Security-Policy of
 * the page against the address a media load is redirected to. Both policies
 * every page carries, the meta tag in astro.config.mjs and the header in
 * site/worker/lib/headers.mjs, list these in `media-src`. On docs.jmrp.io the
 * entry is the page's own origin, so the build it serves behaves as before.
 * A new clip host is added here first: the staging step refuses a build whose
 * pages do not allow every origin listed, and apply-rules.mjs refuses a clip
 * host that is not listed.
 */
export const mediaOrigins = Object.freeze([...targets.mediaOrigins]);

/**
 * Where the phonometry.dev zone rule clips-to-range-host sends a clip, the
 * clip's name appended: a host that answers a byte range with 206, which
 * Static Assets does not. site/worker/scripts/apply-rules.mjs puts it in the
 * rule, and refuses it unless its origin is one of `mediaOrigins`.
 */
export const clipBase = targets.clipBase;

/**
 * The `@id` of the Person node, which the build fetches from jmrp.io and
 * splices in as published. Each page's head names the maintainer by it, and
 * check-schema-vocabulary.mjs holds that one node to jmrp.io's rule rather
 * than this site's.
 */
export const personId = 'https://jmrp.io/#person';

/**
 * The site's name, which Starlight puts after every page title in the head
 * (`Filter Banks | phonometry`) and which a page's Markdown copy leaves out of
 * its `# ` title.
 */
export const siteTitle = 'phonometry';

/** Where the source, the issues and the licence live. */
export const repositoryUrl = 'https://github.com/jmrplens/phonometry';

/** Who writes and maintains the library and its documentation. */
export const author = Object.freeze({
  name: 'José Manuel Requena Plens',
  orcid: 'https://orcid.org/0000-0003-1250-6212',
});
