/**
 * The commit the latest release was published from, and whether a page's
 * content changed after it.
 *
 * The site is built from main, not from the release tag, so a documentation
 * fix reaches readers the day it merges. The price is that a page can then
 * describe code no release carries yet, while everything around it (the
 * `Version:` line of its Markdown copy, `softwareVersion`, llms.txt) still
 * names the release on PyPI. A banner on every page said so up to 4.0.0, and
 * was taken down at the final release: after almost any merge it would have
 * been back on every page, the untouched ones included. What replaces it says
 * it only where it can be true: a page whose content changed after the
 * release commit shows a notice under its title
 * (src/components/ReleaseNotice.astro), and its copy carries an `Unreleased:`
 * line in its header (src/lib/agent-md/header.mjs); a page that has not
 * changed since reads as it did on the day of the release.
 *
 * The content date is the one the footer, `dateModified` and the sitemap
 * give the page (src/lib/content-dates.mjs): the time the commit that last
 * changed what the page says was committed. Main takes squash merges, so that
 * is the time the change reached main, and the release commit's own time is
 * compared with it, to the second. A page changed in the release commit
 * itself (the version stamp) is not newer than the release. A page git has
 * never seen, a new page not committed yet, is dated by its file, which is
 * later than any release, so a local build shows the notice on it; an edit to
 * a page git already holds is dated by its commit, and counts once committed.
 *
 * Which commit is the release. VERSION holds the version the release
 * workflow publishes (src/data/repo-stats.mjs reads it), and the workflow
 * tags the commit it published as `v<version>`: that tag is the release when
 * the clone has it (the docs job checks out every tag with the history).
 * The workflow pushes the tag after CI has passed on the merge that set
 * VERSION, an hour or more after the docs job built that same merge, so a
 * build can find VERSION already naming a release whose tag does not exist
 * yet. The release is then the commit that made VERSION say what it says,
 * which is the commit the tag will point at. Nothing here is typed per
 * release: the next VERSION names the next tag.
 *
 * Read once per site root and version, with git; a git that fails, or a
 * VERSION no commit ever set, stops the build rather than leaving the notice
 * off every page.
 *
 * @module
 */
import { execFile } from 'node:child_process';
import { realpathSync } from 'node:fs';
import { resolve } from 'node:path';

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
 * Run git in `cwd`; resolves with its stdout, or with `null` when git exits 1
 * and `quietMiss` says that exit is an answer (`rev-parse --verify --quiet`
 * on a name that does not exist).
 *
 * @param {string} cwd
 * @param {string[]} args
 * @param {{ quietMiss?: boolean }} [options]
 * @returns {Promise<string | null>}
 */
function git(cwd, args, { quietMiss = false } = {}) {
  return new Promise((resolvePromise, reject) => {
    execFile('git', args, { cwd, encoding: 'utf8', maxBuffer: 1024 * 1024 }, (error, stdout, stderr) => {
      if (!error) {
        resolvePromise(stdout);
        return;
      }
      if (quietMiss && error.code === 1 && !stderr.trim()) {
        resolvePromise(null);
        return;
      }
      const said = String(stderr ?? '').trim();
      reject(new Error(`release commit: git ${args.join(' ')} failed in ${cwd}${said ? `: ${said}` : ''}`));
    });
  });
}

/**
 * A commit and its committer time from `%H%x00%cI` output.
 *
 * @param {string} text
 * @returns {{ sha: string, date: Date } | null}
 */
function commitOf(text) {
  const [sha, when] = text.trim().split('\0');
  if (!sha || !when) return null;
  const date = new Date(when);
  if (Number.isNaN(date.getTime())) throw new Error(`release commit: git gave ${JSON.stringify(when)} as the time of ${sha}`);
  return { sha, date };
}

/**
 * Read the latest release of the repository holding `siteRoot`.
 *
 * @param {string} siteRoot
 * @param {string} version
 * @returns {Promise<Release>}
 */
async function readRelease(siteRoot, version) {
  if (!version) throw new Error('release commit: no version to find the release of; VERSION is empty');
  const repo = (await git(siteRoot, ['rev-parse', '--show-toplevel']))?.trim();
  if (!repo) throw new Error(`release commit: ${siteRoot} is not in a git clone`);
  const tag = releaseTag(version);
  const tagged = await git(repo, ['rev-parse', '--verify', '--quiet', `refs/tags/${tag}^{commit}`], { quietMiss: true });
  if (tagged) {
    const commit = commitOf((await git(repo, ['show', '-s', '--format=%H%x00%cI', tagged.trim()])) ?? '');
    if (!commit) throw new Error(`release commit: the tag ${tag} names no commit git can show`);
    return { version, ...commit, from: 'tag' };
  }
  const set = commitOf((await git(repo, ['log', '-1', '--format=%H%x00%cI', 'HEAD', '--', VERSION_FILE])) ?? '');
  if (!set) {
    throw new Error(
      `release commit: the clone has no tag ${tag} and no commit that set ${VERSION_FILE}, so no page can be ` +
        'told apart from the release. Build from a clone with its history and its tags.',
    );
  }
  return { version, ...set, from: 'VERSION' };
}

/** Memoised per site root and version: every page asks. */
const loaded = new Map();

/**
 * The latest release, read once.
 *
 * @param {{ siteRoot?: string, version: string }} options  `version` is the
 *   one VERSION names (src/data/repo-stats.mjs).
 * @returns {Promise<Release>}
 */
export function loadRelease({ siteRoot = process.cwd(), version }) {
  let root = resolve(siteRoot);
  try {
    root = realpathSync(root);
  } catch {
    // A root that does not exist fails in git, with the path in the message.
  }
  const key = `${root}\0${version}`;
  if (!loaded.has(key)) loaded.set(key, readRelease(root, version));
  return loaded.get(key);
}

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
