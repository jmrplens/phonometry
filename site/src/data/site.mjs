/**
 * The site-wide strings that more than one place needs.
 *
 * astro.config.mjs builds every absolute URL from them, and the audit scripts
 * in site/scripts/ address the running preview with the same base, so a move
 * to another path or another host is one edit here rather than a hunt through
 * the checks. The repository and the author are read by the head of every page
 * and by the header of every page's Markdown copy (src/lib/agent-md/header.mjs).
 */
export const siteUrl = 'https://docs.jmrp.io';
export const basePath = '/phonometry';

/**
 * The `@id` of the Person node, which the build fetches from jmrp.io and
 * splices in as published. Each page's head names the maintainer by it, and
 * check-schema-vocabulary.mjs holds that one node to jmrp.io's rule rather
 * than this site's.
 */
export const personId = 'https://jmrp.io/#person';

/** Where the source, the issues and the licence live. */
export const repositoryUrl = 'https://github.com/jmrplens/phonometry';

/** Who writes and maintains the library and its documentation. */
export const author = Object.freeze({
  name: 'José Manuel Requena Plens',
  orcid: 'https://orcid.org/0000-0003-1250-6212',
});
