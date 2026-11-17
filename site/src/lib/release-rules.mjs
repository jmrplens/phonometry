/**
 * What the release notice needs to know about the latest release, without
 * reading it. The release is read in src/lib/release-commit.mjs, with git,
 * once per build; nothing here starts a process, so a page, its Markdown copy
 * and the notice can all import the rule and the changelog link without
 * reaching for git.
 *
 * @module
 */
import { repositoryUrl } from '../data/site.mjs';

/** The file that names the release, at the root of the repository. */
export const VERSION_FILE = 'VERSION';

/** The tag the release workflow gives the commit it publishes `version` from. */
export const releaseTag = (version) => `v${version}`;

/** Where the changelog lists what changed after the latest release. */
export const UNRELEASED_URL = `${repositoryUrl}/blob/main/CHANGELOG.md#unreleased`;

/**
 * The latest release, as the build reads it.
 *
 * @typedef {object} Release
 * @property {string} version  As VERSION names it.
 * @property {string} sha  The commit it was published from.
 * @property {Date} date  When that commit was committed.
 * @property {'tag' | 'VERSION'} from  Read from the release tag, or from the
 *   commit that set VERSION when the clone has no such tag yet.
 */

/**
 * Whether content dated `date` changed after `release`: later than the
 * release commit, to the second.
 *
 * @param {Pick<Release, 'date'>} release
 * @param {Date} date
 * @returns {boolean}
 */
export function changedAfter(release, date) {
  return date.getTime() > release.date.getTime();
}
