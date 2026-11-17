/**
 * The site-wide strings that more than one place needs.
 *
 * astro.config.mjs builds every absolute URL from them, and the audit scripts
 * in site/scripts/ address the running preview with the same base, so a move
 * to another path or another host is one edit here rather than a hunt through
 * the checks. The repository and the author are read by the head of every page
 * and by the header of every page's Markdown copy (src/lib/agent-md/header.mjs).
 */

/**
 * The hosts the site can be built for, and the base path under each.
 *
 * docs.jmrp.io is the canonical site and the build with nothing set.
 * phonometry.dev is the preview served from Cloudflare (site/worker/README.md):
 * `PHONOMETRY_SITE=phonometry.dev pnpm build` names it in every canonical URL,
 * `og:url`, structured data `@id`, sitemap, Markdown copy and llms file, and in
 * robots.txt (scripts/site-origin.mjs). It keeps the base
 * path for now, so every link the pages write is the same in both builds; the
 * move to the root is a later change.
 */
export const SITE_TARGETS = Object.freeze({
  'docs.jmrp.io': Object.freeze({ siteUrl: 'https://docs.jmrp.io', basePath: '/phonometry' }),
  'phonometry.dev': Object.freeze({ siteUrl: 'https://phonometry.dev', basePath: '/phonometry' }),
});

/**
 * The target a value of PHONOMETRY_SITE names.
 *
 * @param {string | undefined} name The variable's value; unset or empty means docs.jmrp.io.
 * @returns {{siteUrl: string, basePath: string}} The target.
 * @throws {Error} For any other value, so a typo stops the build instead of publishing it.
 */
export function siteTarget(name) {
  const key = name === undefined || name === '' ? 'docs.jmrp.io' : name;
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
