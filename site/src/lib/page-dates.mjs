/**
 * First-publication dates, read from git history.
 *
 * Starlight's `lastUpdated` gives the last commit that touched a page, and the
 * structured data used to serve that same value as both `datePublished` and
 * `dateModified`. That claims every page was first published on the day it was
 * last edited: a typo fix moved a two-year-old guide's publication date to
 * today, and a corpus with real history looked freshly minted. It also
 * contradicted the `SoftwareApplication` node on the same page, which pins a
 * fixed `datePublished`.
 *
 * So `datePublished` comes from the commit that added the file, and a rename
 * carries that date to the file's new path. All of it is read in one pass over
 * the docs tree, on the first page that asks, and every page after that is
 * answered from the map. The day is the commit's day in UTC, as the modified
 * date's is (`isoDay` in src/lib/date-rules.mjs): on the day its committer
 * wrote, a page committed after midnight in a later time zone would be
 * published the day after the day it says it last changed.
 *
 * It used to be one `git log --follow` per page, and that was wrong twice. It
 * was slow: a synchronous process per page stops the event loop, so the build's
 * concurrency buys nothing while it runs, and in the blobless clone the docs
 * workflow checks out, each rename search can wait on old blobs from the
 * network as well. And it was false: `--follow` looks for copies as well as
 * renames, among all the files of the parent commit, so a page written or split
 * from another took that page's date. Reading the tree in one pass pairs each
 * deleted file with one added file, and a page copied from one that is still
 * there is an add of its own.
 *
 * A clone that holds no history, or no git to read it with, is an answer: every
 * caller falls back to the last-updated date. A history that is there and cannot
 * be read is not. One pass means one failure takes the date of every page at
 * once, and `datePublished` falling back to `dateModified` everywhere is the
 * false claim this module exists to remove, so it stops a CI build and warns
 * anywhere else.
 */
import { execFileSync } from 'node:child_process';
import { realpathSync } from 'node:fs';
import { isAbsolute, relative, resolve, sep } from 'node:path';

import { isoDay } from './date-rules.mjs';

/** Where the docs collection lives, from the repository's root. */
const DOCS_TREE = 'site/src/content/docs';

/** What is known where git cannot answer: nothing, so every caller falls back. */
const NO_HISTORY = { root: '', added: new Map() };

function git(...args) {
  return execFileSync('git', args, {
    encoding: 'utf8',
    // Piped so that a failure carries what git said on `error.stderr`.
    stdio: ['ignore', 'pipe', 'pipe'],
    // The tree's history is about a megabyte today, the default limit, and past
    // the limit this would throw.
    maxBuffer: 1 << 28,
  });
}

/** The older of two adds, each `{ time, date }`; `current` may be missing. */
function older(current, candidate) {
  return current && current.time <= candidate.time ? current : candidate;
}

/**
 * The add each path goes back to, from `git log -z --name-status` written
 * oldest first: `C <time>` for a commit, then a status and its paths,
 * every field ended by a NUL so that no file name needs quoting.
 *
 * A merge writes what it changed from all of its parents at once: a status
 * letter per parent, then the path in each parent and the path it holds. It
 * lists only a file it holds as no parent did, so a file it took from a
 * parent goes back to that parent's add, and one it wrote itself, or moved,
 * is read here: a letter `A` for a parent that did not hold it, which the
 * merge adds, and any other for one that did, whose add it keeps.
 *
 * @param {string} log
 * @returns {Map<string, {time: number, date: string}>} Repo-relative path to add.
 */
function addsIn(log) {
  const added = new Map();
  const fields = log.split('\0');
  let commit;
  for (let i = 0; i < fields.length; i += 1) {
    // Git ends a commit's own line with a newline, which reads as the start of
    // the next field.
    const field = fields[i].trimStart();
    if (field.startsWith('C ')) {
      const time = Number(field.slice(2));
      commit = { time, date: isoDay(new Date(time * 1000)) };
    } else if (/^[A-Z]{2,}$/.test(field)) {
      // A merge, read before a one-parent status that starts with the same
      // letter: one letter per parent, its path in each, and the path it holds.
      const letters = [...field];
      const from = fields.slice(i + 1, i + 1 + letters.length);
      const to = fields[(i += letters.length + 1)];
      if (letters.every((letter) => letter === 'D')) continue;
      for (const [index, letter] of letters.entries()) {
        const add = letter === 'A' ? commit : (added.get(from[index]) ?? commit);
        added.set(to, older(added.get(to), add));
      }
    } else if (field === 'A') {
      // A file resurrected after a delete has several adds; the oldest is the
      // publication date.
      const path = fields[(i += 1)];
      added.set(path, older(added.get(path), commit));
    } else if (field.startsWith('R')) {
      const from = fields[(i += 1)];
      const to = fields[(i += 1)];
      added.set(to, older(added.get(to), added.get(from) ?? commit));
    } else if (field) {
      // A modification, a delete or a change of type names one path and adds
      // nothing.
      i += 1;
    }
  }
  return added;
}

/**
 * What to do with a history that is there and could not be read: stop a CI
 * build, which would otherwise publish every page with the wrong date and pass
 * every check of its fields, and tell anyone else.
 */
function unreadable(error) {
  const said = String(error.stderr || error.message).trim();
  if (process.env.CI) {
    throw new Error(`git could not read ${DOCS_TREE}, so no page would have a first-publication date: ${said}`, {
      cause: error,
    });
  }
  console.warn(`git could not read ${DOCS_TREE}, so no page has a first-publication date: ${said}`);
  return NO_HISTORY;
}

/** The repository's root and the adds of the docs tree, or nothing to go on. */
function readHistory() {
  let root;
  try {
    // HEAD because a repository with no commits has nothing to read either, and
    // `git log` would fail on it as it does on a history it cannot read.
    const [top, shallow] = git('rev-parse', '--show-toplevel', '--is-shallow-repository', 'HEAD').split('\n');
    // A shallow clone's oldest commit seems to add every page it holds.
    if (shallow !== 'false') return NO_HISTORY;
    root = top;
  } catch {
    // No git, or not a repository. The caller falls back to the last-updated
    // date, which is the best available answer for a page with no history.
    return NO_HISTORY;
  }
  try {
    // From the root, like the other readers of this tree, so that the paths come
    // out the same from wherever the build runs and whatever `diff.relative` says.
    // --no-show-signature because `log.showSignature` prints in front of each
    // commit's line. -M because the pass depends on renames whatever
    // `diff.renames` says, and -l0 because past a limit of candidates git gives up
    // on similarity with only a warning on stderr, which a move of the whole tree
    // will reach once it passes a thousand pages and the search for one file never
    // could. The rest because it depends on seeing every add: --full-history keeps
    // a branch whose merge left the tree as it was, --root keeps the first commit,
    // --topo-order puts each add before the renames of the file it added, and
    // --diff-merges=combined with --combined-all-paths writes the files a merge
    // added or moved itself, with the path each parent held them at, where
    // git log writes nothing for a merge by default.
    const log = git(
      '-C',
      root,
      'log',
      '--no-show-signature',
      '--reverse',
      '--topo-order',
      '--full-history',
      '--root',
      '-M',
      '-l0',
      '--diff-merges=combined',
      '--combined-all-paths',
      '--name-status',
      '-z',
      '--format=C %ct',
      '--',
      DOCS_TREE,
    );
    return { root: realpathSync(root), added: addsIn(log) };
  } catch (error) {
    return unreadable(error);
  }
}

/** The path git knows a file by, or undefined outside the repository. */
function repoPath(filePath, root) {
  let file = resolve(filePath);
  try {
    file = realpathSync(file);
  } catch {
    // Nothing there to resolve: it will not be in the map either.
  }
  const path = relative(root, file);
  if (!path || path.startsWith('..') || isAbsolute(path)) return undefined;
  return path.split(sep).join('/');
}

let history;

/**
 * The date a file first appeared in history.
 *
 * @param {string} filePath Absolute path to the content file, or relative to
 *   the working directory: `route.entry.filePath` is relative to the site's
 *   root, which is where a build runs.
 * @returns {string|undefined} The UTC day (`YYYY-MM-DD`), or undefined when
 *   the file is untracked or outside the docs tree, git is unavailable, or the
 *   checkout is shallow.
 */
export function firstPublished(filePath) {
  if (!filePath) return undefined;
  history ??= readHistory();
  if (history === NO_HISTORY) return undefined;
  return history.added.get(repoPath(filePath, history.root))?.date;
}
