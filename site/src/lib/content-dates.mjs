/**
 * The date each page's content last changed, read from git history.
 *
 * The date a page shows in its footer, the `dateModified` of its structured
 * data and the `<lastmod>` the sitemap gives it all come from here, so the
 * three cannot disagree. They used to come from the last commit that touched
 * the file, whatever it changed: the sweep that cut every meta description to
 * 160 characters touched 455 pages, and each of them took the day it merged
 * as the day its content last changed, in its footer, in its structured data
 * and in the sitemap crawlers read to decide what to fetch again.
 *
 * Which commits move a date is src/lib/date-rules.mjs's rule: not one that
 * changed only a page's title, description or sidebar entry, moved it
 * unchanged, or is listed in `site/date-ignore-revs.txt`; and a page
 * `site/date-sources.json` lists is dated by what it is built from too.
 * This module reads the history that rule is applied to.
 *
 * How it is read. The docs job checks out with `filter: blob:none`: every
 * commit and tree, no historical blob. A `git log -p` over the content tree
 * would fetch the old blobs on demand, a request per commit, and its output
 * (73 MB over 653 commits) would not fit the 64 MB buffer the old sitemap
 * script read git through, whose failures it caught and dropped. So the
 * history is read from trees alone: `--raw` names each changed file with its
 * old and new blob ids, and `--no-renames` keeps git from looking for renames
 * by content, which needs the blobs (a move with the same blob is followed
 * here by its id). Only the blob pairs that decide a date are read, fetched
 * in one request per round: a page is dated by its newest change most of the
 * time, and a page whose newest changes were frontmatter-only asks for twice
 * as many pairs in each round that follows, so a run of n such commits costs
 * about log2(n) requests. The sources are read from trees alone too: their
 * dates need no blob. Every git call streams its output, and any failure
 * throws: a build that cannot read the dates stops instead of publishing
 * guesses.
 *
 * It reads the history once per site root: routeData.ts asks for it as the
 * build starts, and every page gets that one reading. So it gives out the
 * reading and nothing else, which is what keeps git off every page that
 * imports it, and the rule, the paths and the day live in date-rules.mjs for
 * anything else to import.
 */
import { spawn } from 'node:child_process';
import { existsSync, realpathSync, statSync } from 'node:fs';
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';

import {
  CONTENT_DIR,
  DATE_SOURCES,
  FULL_SHA,
  IGNORE_REVS,
  frontmatterOnly,
  readDateSources,
  readIgnoreRevs,
} from './date-rules.mjs';

/**
 * Run git in `cwd` and hand its stdout to `onData` chunk by chunk.
 *
 * @param {string} cwd
 * @param {string[]} args
 * @param {{ input?: string, onData?: (chunk: Buffer) => void, env?: Record<string, string> }} [options]
 * @returns {Promise<void>} Settles when git exits; rejects on a non-zero exit,
 *   a signal or a spawn error, with what git wrote to stderr, and with the
 *   error `onData` throws on output it cannot read.
 */
function git(cwd, args, { input, onData, env } = {}) {
  return new Promise((resolvePromise, reject) => {
    const child = spawn('git', args, {
      cwd,
      env: { ...process.env, ...env },
      stdio: [input === undefined ? 'ignore' : 'pipe', 'pipe', 'pipe'],
    });
    const stderr = [];
    let failed = null;
    child.stdout.on('data', (chunk) => {
      if (failed) return;
      try {
        onData?.(chunk);
      } catch (error) {
        // Output this module cannot read fails the call, not the process.
        failed = error;
        child.kill();
      }
    });
    child.stderr.on('data', (chunk) => stderr.push(chunk));
    child.on('error', (error) => reject(new Error(`git ${args[0]}: ${error.message}`)));
    child.on('close', (code, signal) => {
      if (failed) reject(failed);
      else if (code === 0) resolvePromise();
      else {
        const said = Buffer.concat(stderr).toString('utf8').trim();
        reject(
          new Error(
            `git ${args.join(' ')} failed in ${cwd} (${signal ?? `exit ${code}`})` +
              (said ? `: ${said}` : ''),
          ),
        );
      }
    });
    if (input !== undefined) {
      child.stdin.on('error', () => {}); // An early exit is reported by `close`.
      child.stdin.end(input);
    }
  });
}

/** Run git and return its whole stdout as text (for short outputs). */
async function gitText(cwd, args, options) {
  const chunks = [];
  await git(cwd, args, { ...options, onData: (chunk) => chunks.push(chunk) });
  return Buffer.concat(chunks).toString('utf8');
}

/**
 * Split NUL-separated output into its fields as it streams.
 *
 * @param {(field: string) => void} onField
 * @returns {{ push: (chunk: Buffer) => void, end: () => void }}
 */
function nulFields(onField) {
  let rest = Buffer.alloc(0);
  return {
    push(chunk) {
      let buffer = rest.length ? Buffer.concat([rest, chunk]) : chunk;
      let at;
      while ((at = buffer.indexOf(0)) !== -1) {
        onField(buffer.subarray(0, at).toString('utf8'));
        buffer = buffer.subarray(at + 1);
      }
      rest = Buffer.from(buffer);
    },
    end() {
      if (rest.length) onField(rest.toString('utf8'));
      rest = Buffer.alloc(0);
    },
  };
}

/**
 * The history of some paths from trees alone: each commit, newest first, with
 * the files it changed under them and their old and new blob ids.
 *
 * @param {string} repo
 * @param {string[]} pathspecs
 * @returns {Promise<Array<{ sha: string, date: Date, changes: Array<{ status: string, from: string, to: string, path: string }> }>>}
 */
async function readHistory(repo, pathspecs) {
  const commits = [];
  let meta = null; // The raw line waiting for its path.
  let expectDate = false;
  const fields = nulFields((field) => {
    const token = field.replace(/^\n/, '');
    if (expectDate) {
      commits.at(-1).date = new Date(token);
      expectDate = false;
    } else if (meta !== null) {
      const [, , from, to, status] = meta.slice(1).split(' ');
      commits.at(-1).changes.push({ status: status[0], from, to, path: token });
      meta = null;
    } else if (token.startsWith(':')) {
      meta = token;
    } else if (FULL_SHA.test(token)) {
      commits.push({ sha: token, date: null, changes: [] });
      expectDate = true;
    } else if (token !== '') {
      throw new Error(`git log: unexpected field "${token.slice(0, 80)}"`);
    }
  });
  await git(
    repo,
    [
      '-c',
      'core.quotePath=false',
      'log',
      '--no-show-signature',
      '--format=%H%x00%cI',
      '--raw',
      '--no-abbrev',
      '--no-renames',
      '-z',
      '--',
      ...pathspecs,
    ],
    { onData: (chunk) => fields.push(chunk) },
  );
  fields.end();
  for (const commit of commits) {
    if (!(commit.date instanceof Date) || Number.isNaN(commit.date.getTime())) {
      throw new Error(`git log: no committer date for ${commit.sha}`);
    }
  }
  return commits;
}

/**
 * The text of the given blobs. In a partial clone the ones not present are
 * fetched first, in one request; lazy fetching is switched off for the read,
 * so a blob that is still missing fails here instead of costing a round trip
 * each.
 *
 * @param {string} repo
 * @param {string[]} oids
 * @returns {Promise<Map<string, string>>}
 */
async function readBlobs(repo, oids) {
  const noLazy = { GIT_NO_LAZY_FETCH: '1' };
  const list = `${oids.join('\n')}\n`;
  const present = await gitText(repo, ['cat-file', '--batch-check'], { input: list, env: noLazy });
  const missing = present
    .split('\n')
    .filter((line) => line.endsWith(' missing'))
    .map((line) => line.split(' ')[0]);
  if (missing.length > 0) {
    const remotes = await gitText(repo, ['config', '--get-regexp', '^remote\\..*\\.promisor$']).catch(
      () => '',
    );
    const promisor = remotes
      .split('\n')
      .map((line) => /^remote\.(.+)\.promisor\s+true$/i.exec(line.trim())?.[1])
      .find(Boolean);
    if (!promisor) {
      throw new Error(`${missing.length} blob(s) of the content history are missing, e.g. ${missing[0]}`);
    }
    await git(
      repo,
      [
        '-c',
        'fetch.negotiationAlgorithm=noop',
        'fetch',
        '--quiet',
        promisor,
        '--no-tags',
        '--no-write-fetch-head',
        '--recurse-submodules=no',
        '--filter=blob:none',
        '--stdin',
      ],
      { input: `${missing.join('\n')}\n` },
    );
  }

  const texts = new Map();
  let rest = Buffer.alloc(0);
  let pending = null; // { oid, size } of the object whose content is arriving.
  const take = (chunk) => {
    rest = rest.length ? Buffer.concat([rest, chunk]) : chunk;
    for (;;) {
      if (pending === null) {
        const eol = rest.indexOf(10);
        if (eol === -1) return;
        const header = rest.subarray(0, eol).toString('utf8');
        rest = rest.subarray(eol + 1);
        const [oid, type, size] = header.split(' ');
        if (type !== 'blob') throw new Error(`git cat-file: ${header}`);
        pending = { oid, size: Number(size) };
      }
      if (rest.length < pending.size + 1) return;
      texts.set(pending.oid, rest.subarray(0, pending.size).toString('utf8'));
      rest = rest.subarray(pending.size + 1);
      pending = null;
    }
  };
  await git(repo, ['cat-file', '--batch'], { input: list, env: noLazy, onData: take });
  for (const oid of oids) {
    if (!texts.has(oid)) throw new Error(`git cat-file: no content for blob ${oid}`);
  }
  return texts;
}

/**
 * The date each committed page last changed, keyed by its path relative to
 * the repository.
 *
 * @param {{ repo: string, pathspec: string, ignore: Set<string>, pages: string[] }} options
 * @returns {Promise<{ dates: Map<string, Date>, rounds: number, blobs: number }>}
 */
async function resolveDates({ repo, pathspec, ignore, pages }) {
  const history = await readHistory(repo, [pathspec]);

  const touched = new Set(history.map((commit) => commit.sha));
  const stale = [...ignore].filter((sha) => !touched.has(sha));
  if (stale.length > 0) {
    throw new Error(
      `${IGNORE_REVS} lists ${stale.join(', ')}, which changed no page of ${pathspec}: ` +
        'a commit rewritten by a rebase, or one that never touched the content.',
    );
  }

  /** path -> [{ index, change }], newest first. */
  const byPath = new Map();
  history.forEach((commit, index) => {
    for (const change of commit.changes) {
      if (!byPath.has(change.path)) byPath.set(change.path, []);
      byPath.get(change.path).push({ index, change });
    }
  });

  /** The page a deleted blob came from, per commit: for exact renames. */
  const deleted = history.map(
    (commit) =>
      new Map(commit.changes.filter((c) => c.status === 'D').map((c) => [c.from, c.path])),
  );

  const dates = new Map();
  const texts = new Map();

  /**
   * Walk a page back from where `state` stands, moving `state` along, until a
   * commit dates it. A change whose blobs are not read yet goes to `unknown`,
   * which says whether to pass over it as if it changed only frontmatter
   * (true) or to stop in front of it (false, and the walk returns null).
   */
  const walk = (state, unknown) => {
    for (;;) {
      const entry = (byPath.get(state.path) ?? [])[state.at];
      if (entry === undefined) {
        throw new Error(
          `content dates: the history of ${state.page} (followed to ${state.path}) ends ` +
            'without the commit that created it. A damaged clone?',
        );
      }
      const { index, change } = entry;
      const commit = history[index];
      state.at += 1;
      if (index <= state.after) continue; // Newer than the move followed: another file.
      if (change.status === 'D') continue;
      if (change.status === 'A') {
        const origin = deleted[index].get(change.to);
        if (origin === undefined) return commit.date;
        // Moved unchanged: carry on at the old address, with older commits only.
        state.path = origin;
        state.after = index;
        state.at = 0;
        continue;
      }
      if (change.status !== 'M') return commit.date; // A type change, say: it counts.
      if (ignore.has(commit.sha) || change.from === change.to) continue;
      if (!texts.has(change.from) || !texts.has(change.to)) {
        if (unknown(change)) continue;
        state.at -= 1; // Come back to this change once its blobs are read.
        return null;
      }
      if (!frontmatterOnly(texts.get(change.from), texts.get(change.to))) return commit.date;
    }
  };

  /** Pages still walking: where each one is in its history. */
  let walking = pages.map((page) => ({ page, path: page, at: 0, after: -1 }));
  let rounds = 0;
  while (walking.length > 0) {
    // Most pages are dated by their newest change; the few with a run of
    // frontmatter-only commits behind it ask for twice as many pairs each
    // round, so a run of n costs about log2(n) requests, not n.
    const budget = 2 ** rounds;
    const waiting = [];
    const wanted = new Set();
    for (const state of walking) {
      const date = walk(state, () => false);
      if (date !== null) {
        dates.set(state.page, date);
        continue;
      }
      waiting.push(state);
      let pairs = 0;
      try {
        walk({ ...state }, (change) => {
          for (const oid of [change.from, change.to]) if (!texts.has(oid)) wanted.add(oid);
          pairs += 1;
          return pairs < budget;
        });
      } catch {
        // The real walk reports a history that ends early, once it gets there.
      }
    }
    if (wanted.size > 0) {
      rounds += 1;
      const read = await readBlobs(repo, [...wanted]);
      for (const [oid, text] of read) texts.set(oid, text);
    }
    walking = waiting;
  }
  return { dates, rounds, blobs: texts.size };
}

/**
 * The files of HEAD that some pathspecs match, matched the way `git log`
 * matches them: a diff from the empty tree. (`git ls-files` reads the index,
 * and lets a file through that an excluded glob of every `index.*` at any
 * depth names.)
 *
 * @param {string} repo
 * @param {string[]} pathspecs
 * @returns {Promise<string[]>}
 */
async function filesAtHead(repo, pathspecs) {
  const empty = (await gitText(repo, ['hash-object', '-t', 'tree', '--stdin'], { input: '' })).trim();
  const files = [];
  const listing = nulFields((path) => path && files.push(path));
  await git(repo, ['diff-tree', '-r', '-z', '--name-only', '--no-renames', empty, 'HEAD', '--', ...pathspecs], {
    onData: (chunk) => listing.push(chunk),
  });
  listing.end();
  return files;
}

/** Whether a path from site/date-sources.json names `path`: the file, or a directory holding it. */
const names = (spec, path) => (spec.endsWith('/') ? path.startsWith(spec) : path === spec);

/** The later of two dates, either of which may be missing. */
const later = (a, b) => (a === undefined || (b !== undefined && b > a) ? b : a);

/**
 * Move the date of each page `site/date-sources.json` lists to the newest
 * change of what it is built from, when that is later than its own.
 *
 * @param {{ repo: string, pathspec: string, pages: string[], dates: Map<string, Date>, entries: ReturnType<typeof readDateSources> }} options
 * @returns {Promise<{ sourced: number, raised: number }>} How many pages have
 *   sources, and how many of them a source dates.
 */
async function applySources({ repo, pathspec, pages, dates, entries }) {
  const content = `${pathspec}/`;
  const stale = (what) =>
    new Error(`${DATE_SOURCES} names ${what}, which HEAD does not have: a file moved or renamed?`);
  for (const spec of entries.flatMap((entry) => entry.pages)) {
    if (!spec.startsWith(content)) {
      throw new Error(`${DATE_SOURCES} names ${spec} as a page, and pages are under ${content}.`);
    }
    if (!pages.some((page) => names(spec, page))) throw stale(`the page(s) ${spec}`);
  }

  /** Source path, or counted set as JSON -> the date it last changed. */
  const newest = new Map();

  // A source inside the content tree stands for its pages, each dated by the
  // page rule, as they stood before any of them was moved by a source here.
  const walked = new Map(dates);
  const sources = [...new Set(entries.flatMap((entry) => entry.sources))];
  for (const spec of sources.filter((spec) => spec.startsWith(content))) {
    const under = pages.filter((page) => names(spec, page));
    if (under.length === 0) throw stale(`the source ${spec}`);
    newest.set(spec, under.map((page) => walked.get(page)).reduce(later, undefined));
  }

  // Any other source is data: every commit that changed it counts, and its
  // history is read from trees alone.
  const files = sources.filter((spec) => !spec.startsWith(content));
  if (files.length > 0) {
    const tracked = await filesAtHead(repo, files);
    const missing = files.find((spec) => !tracked.some((path) => names(spec, path)));
    if (missing !== undefined) throw stale(`the source ${missing}`);
    for (const commit of await readHistory(repo, files)) {
      for (const { path } of commit.changes) {
        for (const spec of files) if (!newest.has(spec) && names(spec, path)) newest.set(spec, commit.date);
      }
      if (newest.size === sources.length) break;
    }
  }

  // A count moves only with a commit that added or deleted more files than
  // the other: a move inside the set, or an edit, leaves the number shown.
  const sets = new Map(
    entries.flatMap((entry) => Object.values(entry.counts)).map((set) => [JSON.stringify(set), set]),
  );
  for (const [key, set] of sets) {
    if ((await filesAtHead(repo, set)).length === 0) throw stale(`the counted files ${set.join(' ')}`);
    for (const commit of await readHistory(repo, set)) {
      const added = commit.changes.filter((change) => change.status === 'A').length;
      const deleted = commit.changes.filter((change) => change.status === 'D').length;
      if (added !== deleted) {
        newest.set(key, commit.date);
        break;
      }
    }
  }

  const sourced = new Set();
  const raised = new Set();
  for (const entry of entries) {
    const when = [
      ...entry.sources.map((spec) => newest.get(spec)),
      ...Object.values(entry.counts).map((set) => newest.get(JSON.stringify(set))),
    ].reduce(later, undefined);
    for (const page of pages.filter((path) => entry.pages.some((spec) => names(spec, path)))) {
      sourced.add(page);
      if (when !== undefined && when > dates.get(page)) {
        dates.set(page, when);
        raised.add(page);
      }
    }
  }
  return { sourced: sourced.size, raised: raised.size };
}

/** Memoised per site root: the build asks once per page. */
const loaded = new Map();

/**
 * A path with every symbolic link on it resolved, as git names the files of
 * its work tree: `git rev-parse --show-toplevel` answers with the real
 * directory, so a site reached through a link (macOS's temporary directory
 * is one) would otherwise give a pathspec that climbs out of the repository.
 * A path that does not exist yet keeps its last parts as written, under its
 * nearest ancestor that does.
 *
 * @param {string} path An absolute path.
 * @returns {string}
 */
function realPath(path) {
  const rest = [];
  let at = path;
  for (;;) {
    try {
      return join(realpathSync(at), ...rest);
    } catch {
      const parent = dirname(at);
      if (parent === at) return path;
      rest.unshift(basename(at));
      at = parent;
    }
  }
}

/**
 * The dates of every page of a site, read once.
 *
 * @param {{ siteRoot?: string }} [options] The directory holding
 *   `src/content/docs`, `date-ignore-revs.txt` and `date-sources.json`; the
 *   build runs from it.
 * @returns {Promise<{
 *   dateOf: (filePath: string) => Date,
 *   pages: number, rounds: number, blobs: number, sourced: number, raised: number,
 * }>} `dateOf` takes a content file's path, absolute or relative to the site
 *   root, and returns the date its content last changed. A file git has never
 *   seen (a page being written, not committed yet) is dated by the file
 *   itself; a committed one without a date, or a path that is no page, throws.
 *   `sourced` counts the pages date-sources.json lists and `raised` those of
 *   them a source dates.
 */
export function loadContentDates({ siteRoot = process.cwd() } = {}) {
  const root = realPath(resolve(siteRoot));
  if (!loaded.has(root)) loaded.set(root, readContentDates(root));
  return loaded.get(root);
}

async function readContentDates(siteRoot) {
  const contentDir = join(siteRoot, CONTENT_DIR);
  if (!existsSync(contentDir)) {
    throw new Error(`content dates: ${contentDir} does not exist; run the build from the site root.`);
  }
  let repo;
  try {
    repo = realPath((await gitText(siteRoot, ['rev-parse', '--show-toplevel'])).trim());
  } catch (error) {
    throw new Error(
      `content dates: ${siteRoot} is not in a git clone, and the date each page last changed ` +
        'is read from its history. Build the site from a clone with its full history (a ' +
        `blobless one is fine), not from an archive. ${error.message}`,
    );
  }
  if ((await gitText(repo, ['rev-parse', '--is-shallow-repository'])).trim() === 'true') {
    throw new Error(
      'content dates: this clone is shallow, so every page would be dated by its oldest ' +
        'fetched commit. Fetch the whole history (git fetch --unshallow); the docs job ' +
        'checks out with fetch-depth: 0.',
    );
  }
  const pathspec = relative(repo, contentDir).split(sep).join('/');
  const ignore = readIgnoreRevs(join(siteRoot, IGNORE_REVS));
  const entries = readDateSources(join(siteRoot, DATE_SOURCES));

  const pages = [];
  const listing = nulFields((path) => path && pages.push(path));
  await git(repo, ['ls-tree', '-r', '-z', '--name-only', 'HEAD', '--', pathspec], {
    onData: (chunk) => listing.push(chunk),
  });
  listing.end();
  if (pages.length === 0) {
    throw new Error(`content dates: HEAD has no file under ${pathspec}.`);
  }
  const committed = new Set(pages);

  const { dates, rounds, blobs } = await resolveDates({ repo, pathspec, ignore, pages });
  const { sourced, raised } = await applySources({ repo, pathspec, pages, dates, entries });

  return {
    pages: dates.size,
    rounds,
    blobs,
    sourced,
    raised,
    dateOf(filePath) {
      const absolute = isAbsolute(filePath) ? realPath(filePath) : join(siteRoot, filePath);
      const key = relative(repo, absolute).split(sep).join('/');
      const date = dates.get(key);
      if (date) return date;
      if (committed.has(key)) throw new Error(`content dates: no date for ${key}`);
      if (!existsSync(absolute)) throw new Error(`content dates: ${key} is not a file`);
      return statSync(absolute).mtime;
    },
  };
}
