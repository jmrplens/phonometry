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
 * answered from the map.
 *
 * It used to be one `git log --follow` per page, and that was wrong twice. It
 * was slow: a synchronous process per page stops the event loop, so the build's
 * concurrency buys nothing while it runs, and in the blobless clone the docs
 * workflow checks out, each rename search can wait on old blobs from the
 * network as well: the same pages took 12 minutes on one day and 45 on the next.
 * And it was false: `--follow` looks for copies as well as renames, among all
 * the files of the parent commit, so a page written or split from another took
 * that page's date. Reading the tree in one pass pairs each deleted file with
 * one added file, and a page copied from one that is still there is an add of
 * its own.
 */
import { execFileSync } from 'node:child_process';
import { realpathSync } from 'node:fs';
import { isAbsolute, relative, resolve, sep } from 'node:path';

/** Where the docs collection lives, from the site's root, where a build runs. */
const DOCS_TREE = 'src/content/docs';

/** What is known where git cannot answer: nothing, so every caller falls back. */
const NO_HISTORY = { root: '', added: new Map() };

function git(...args) {
  return execFileSync('git', args, {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
    // The tree's history is about a megabyte today, the default limit, and past
    // the limit this would throw and every page would lose its date in silence.
    maxBuffer: 1 << 28,
  });
}

/** The older of two adds, each `{ time, date }`; `current` may be missing. */
function older(current, candidate) {
  return current && current.time <= candidate.time ? current : candidate;
}

/**
 * The add each path goes back to, from `git log -z --name-status` written
 * oldest first: `C <time> <date>` for a commit, then a status and its paths,
 * every field ended by a NUL so that no file name needs quoting.
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
      const [, time, stamp] = field.split(' ');
      commit = { time: Number(time), date: stamp.slice(0, 10) };
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

/** The repository's root and the adds of the docs tree, or nothing to go on. */
function readHistory() {
  try {
    const [root, shallow] = git('rev-parse', '--show-toplevel', '--is-shallow-repository').split('\n');
    // A shallow clone's oldest commit seems to add every page it holds.
    if (shallow !== 'false') return NO_HISTORY;
    // -M because the pass depends on renames whatever `diff.renames` says, and
    // -l0 because past a limit of candidates git stops comparing files without a
    // word, which a move of the whole tree would reach and the search for one
    // file never could. The rest because it depends on seeing every add:
    // --full-history keeps a branch whose merge left the tree as it was, --root
    // keeps the first commit, and --topo-order puts each add before the renames
    // of the file it added.
    const log = git(
      'log',
      '--reverse',
      '--topo-order',
      '--full-history',
      '--root',
      '-M',
      '-l0',
      '--name-status',
      '-z',
      '--format=C %ct %cI',
      '--',
      DOCS_TREE,
    );
    return { root: realpathSync(root), added: addsIn(log) };
  } catch {
    // No git, or not a repository. The caller falls back to the last-updated
    // date, which is the best available answer for a page with no history.
    return NO_HISTORY;
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
 *   the site's root, which is what `route.entry.filePath` is and where a build
 *   runs.
 * @returns {string|undefined} ISO-8601 date (`YYYY-MM-DD`), or undefined when
 *   the file is untracked or outside the docs tree, git is unavailable, or the
 *   checkout is shallow.
 */
export function firstPublished(filePath) {
  if (!filePath) return undefined;
  history ??= readHistory();
  if (history === NO_HISTORY) return undefined;
  return history.added.get(repoPath(filePath, history.root))?.date;
}
