// Where the pages a deploy put live are, for the checks that follow it
// (.github/workflows/site-deploy.yml), as `name=value` lines for
// $GITHUB_OUTPUT.
//
// Usage:
//   node site/worker/scripts/site-address.mjs
//
// The host is the one the Worker serves; the base path, the canonical address
// a page names and the clip host come from src/data/site-targets.json, for
// the target PHONOMETRY_SITE picks as it does for the build and stage.mjs
// (unset: the default target). Whether the staged pages are indexable follows
// the rule stage.mjs applies (lib/staging.mjs indexableBuild), and the old
// base path is the one the zone rules send to the root (apply-rules.mjs
// legacyPrefixOf). The checks read every address from here, so moving the
// pages to another base path or making another host canonical changes that
// file and no check.
import { fileURLToPath } from 'node:url';

import { LEGACY_ORIGINS, basePath, clipBase, siteUrl } from '../../src/data/site.mjs';
import { CANONICAL_ORIGIN, SERVED_ORIGIN, indexableBuild } from '../lib/staging.mjs';
import { legacyPrefixOf } from './apply-rules.mjs';

/**
 * The addresses the deploy checks use.
 *
 * @param {{siteUrl: string, basePath: string, clipBase: string}} target The build's target and its clip host.
 * @param {string} served The origin the Worker serves.
 * @param {{canonical?: string, legacy?: readonly {siteUrl: string, basePath: string}[]}} [site]
 *   The canonical site's origin and the origins the site was published on
 *   before; the default target and LEGACY_ORIGINS by default.
 * @returns {{origin: string, base: string, canonical: string, page_url: string, clip_base: string, indexable: string, legacy_base: string}}
 *   `origin` the served host, `base` the base path (`` at the root),
 *   `canonical` the canonical site with the base path, `page_url` the home
 *   page as served, `clip_base` where a clip is redirected to, `indexable`
 *   `true` when the staged pages carry no noindex, and `legacy_base` the old
 *   base path the zone rules send to the root (`` when there is none, or the
 *   site is not at the root).
 */
export function siteAddress(target, served, { canonical = CANONICAL_ORIGIN, legacy = LEGACY_ORIGINS } = {}) {
	return {
		origin: served,
		base: target.basePath,
		canonical: `${target.siteUrl}${target.basePath}`,
		page_url: `${served}${target.basePath}/`,
		clip_base: target.clipBase,
		indexable: String(indexableBuild(target.siteUrl, false, canonical)),
		legacy_base: target.basePath === '' ? legacyPrefixOf(legacy) : '',
	};
}

/**
 * The addresses as `$GITHUB_OUTPUT` takes them.
 *
 * @param {Record<string, string>} address What {@link siteAddress} returns.
 * @returns {string} One `name=value` line each.
 */
export function outputLines(address) {
	return Object.entries(address)
		.map(([name, value]) => `${name}=${value}\n`)
		.join('');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.stdout.write(outputLines(siteAddress({ siteUrl, basePath, clipBase }, SERVED_ORIGIN)));
}
