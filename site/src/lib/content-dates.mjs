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
 * would fetch the old blobs on demand, a request per commit, and its output,
 * past 64 MB since the history passed some 650 commits and longer with each
 * one, would not fit the 64 MB buffer the old sitemap script read git
 * through, whose failures it caught and dropped. So the
 * history is read from trees alone: `--raw` names each changed file with its
 * old and new blob ids, and `--no-renames` keeps git from looking for renames
 * by content, which needs the blobs (a move with the same blob is followed
 * here by its id). Each commit comes with the commits it follows
 * (`--parents`), and a merge with what it changed from each of them, so every
 * reader walks back from HEAD along the versions HEAD holds, through a merge
 * to the parent whose version it kept, and never reads a side's change the
 * merge threw away. Only the blob pairs that decide a date are read, fetched
 * in one request per round: a page is dated by its newest change most of the
 * time, and a page whose newest changes were frontmatter-only asks for twice
 * as many pairs in each round that follows, so a run of n such commits costs
 * about log2(n) requests. The sources and the counts of files are read from
 * trees alone too: their dates need no blob. A count of the lines of a file
 * reads the versions of that one file, newest first and in the same doubling
 * rounds, until one changed the number, and a text reads the versions of its
 * files the same way, until one changed a match. The "Verified by" line of
 * each guide is read the same way from the versions of the conformance
 * report that hold the component that draws it, joined with the references
 * the pages cite now (src/lib/page-references.mjs), until every page that
 * shows one is dated or older than its own date. Every git call streams its
 * output,
 * and any failure throws: a build that cannot read the dates stops instead
 * of publishing guesses.
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

import { conformanceEvidence } from './conformance-evidence.mjs';
import {
  CONTENT_DIR,
  DATE_SOURCES,
  FULL_SHA,
  IGNORE_REVS,
  frontmatterOnly,
  readDateSources,
  readIgnoreRevs,
} from './date-rules.mjs';
import { readPageReferences } from './page-references.mjs';
import { basePath, siteUrl } from '../data/site.mjs';

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
 * One changed file of a commit from one of its parents, read from the raw line
 * git writes for it: `:`, the old and new mode, the old and new blob and the
 * status, `A` for a file the parent did not hold, `D` for one the commit
 * deleted, `M` for one it changed and `T` for one whose type it changed.
 *
 * @param {string} meta The raw line, without its path.
 * @returns {{ status: string, from: string, to: string }} `from` is the blob
 *   the parent held, and `to` the one the commit holds.
 */
function parseChange(meta) {
  const [, , from, to, letters] = meta.slice(1).split(' ');
  return { status: letters[0], from, to };
}

/**
 * @typedef {{ status: string, from: string, to: string }} Change
 * @typedef {{ sha: string, date: Date, parents: string[], diffs: Array<Map<string, Change>> }} Commit
 *   `diffs[i]` is what the commit changed from `parents[i]`, by path; a commit
 *   with no parent has one, every path it holds, added.
 * @typedef {{ head: Commit | null, commits: Map<string, Commit>, order: Commit[] }} History
 *   `head` stands for HEAD: the newest commit that changed the paths on the
 *   way to it, whose version of them is HEAD's. `order` lists every commit
 *   before the commits it follows.
 */

/**
 * The history of some paths from trees alone: each commit that changed them,
 * the commits it follows and what it changed from each.
 *
 * git simplifies the history to the paths. A commit that changed none of them
 * is left out, and the commit after it follows the commit before it in its
 * place (`--parents`), whose version of the paths is the same. A merge that
 * holds the paths as one parent held them is left out with the commits only
 * the other parents reached, since none of them made what HEAD holds. A merge
 * that holds them as no parent did, one it wrote itself or the two sides
 * joined, is kept, and what it changed from each parent is read on its own
 * (`git diff-tree`), so a reader can tell, path by path, which parent's
 * version it holds and follow that parent's history and no other. Without
 * that, a merge that kept one side's version of a page while it took the
 * other side's other files left the discarded side's newer edit to date the
 * page.
 *
 * @param {string} repo
 * @param {string[]} pathspecs
 * @returns {Promise<History>}
 */
async function readHistory(repo, pathspecs) {
  /** @type {Commit[]} */
  const order = [];
  let meta = null; // The raw line waiting for its path.
  let expect = null; // The field of the commit line that comes next.
  const fields = nulFields((field) => {
    const token = field.replace(/^\n/, '');
    if (expect === 'parents') {
      order.at(-1).parents = token === '' ? [] : token.split(' ');
      expect = 'date';
    } else if (expect === 'date') {
      order.at(-1).date = new Date(token);
      expect = null;
    } else if (meta !== null) {
      order.at(-1).diffs[0].set(token, parseChange(meta));
      meta = null;
    } else if (token.startsWith(':')) {
      meta = token;
    } else if (FULL_SHA.test(token)) {
      order.push({ sha: token, date: null, parents: [], diffs: [new Map()] });
      expect = 'parents';
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
      '--format=%H%x00%P%x00%cI',
      '--raw',
      '--diff-merges=off',
      '--no-abbrev',
      '--no-renames',
      '--topo-order',
      '--parents',
      '-z',
      '--',
      ...pathspecs,
    ],
    { onData: (chunk) => fields.push(chunk) },
  );
  fields.end();
  for (const commit of order) {
    if (!(commit.date instanceof Date) || Number.isNaN(commit.date.getTime())) {
      throw new Error(`git log: no committer date for ${commit.sha}`);
    }
  }
  const merges = order.filter((commit) => commit.parents.length > 1);
  if (merges.length > 0) await readMergeDiffs(repo, pathspecs, merges);
  const commits = new Map(order.map((commit) => [commit.sha, commit]));
  const followed = new Set(order.flatMap((commit) => commit.parents));
  for (const sha of followed) {
    if (!commits.has(sha)) throw new Error(`git log: ${sha} is a parent no commit of the history is. A damaged clone?`);
  }
  const heads = order.filter((commit) => !followed.has(commit.sha));
  if (heads.length > 1) throw new Error(`git log: the history has ${heads.length} ends, ${heads[0].sha} and ${heads[1].sha}, not one`);
  return { head: heads[0] ?? null, commits, order };
}

/**
 * What each merge changed from each of its parents, read in one `git
 * diff-tree` (`<merge> <parent>` on each line diffs the parent to the merge):
 * every merge's `diffs`, one per parent, in its parents' order.
 *
 * @param {string} repo
 * @param {string[]} pathspecs
 * @param {Commit[]} merges
 */
async function readMergeDiffs(repo, pathspecs, merges) {
  const pairs = merges.flatMap((merge) => merge.parents.map((parent, index) => ({ merge, parent, index })));
  for (const merge of merges) merge.diffs = merge.parents.map(() => new Map());
  let block = -1;
  let meta = null;
  const fields = nulFields((field) => {
    const token = field.replace(/^\n/, '');
    if (meta !== null) {
      const { merge, index } = pairs[block];
      merge.diffs[index].set(token, parseChange(meta));
      meta = null;
    } else if (token.startsWith(':')) {
      if (block < 0) throw new Error('git diff-tree: a change before any commit');
      meta = token;
    } else if (FULL_SHA.test(token)) {
      block += 1;
      if (pairs[block]?.merge.sha !== token) throw new Error(`git diff-tree: ${token} out of turn`);
    } else if (token !== '') {
      throw new Error(`git diff-tree: unexpected field "${token.slice(0, 80)}"`);
    }
  });
  await git(
    repo,
    ['-c', 'core.quotePath=false', 'diff-tree', '--stdin', '--always', '-r', '--raw', '--no-abbrev', '--no-renames', '-z', '--', ...pathspecs],
    { input: pairs.map(({ merge, parent }) => `${merge.sha} ${parent}\n`).join(''), onData: (chunk) => fields.push(chunk) },
  );
  fields.end();
  if (block !== pairs.length - 1) throw new Error(`git diff-tree: ${block + 1} of ${pairs.length} diffs of merges read`);
}

/**
 * Walk one line of a history back, a step at a time, reading the blobs a step
 * needs in rounds that each read ahead twice as far as the last, so the usual
 * walk, which stops at its first step, costs one request.
 *
 * @template S
 * @param {S} state Where the walk starts.
 * @param {(state: S) => { next: S } | { stop: Commit | null } | { wants: string[], guess: S | null }} step
 *   One step back: on to `next`; a stop at the commit that made the version
 *   the walk follows, or `null` once the walk runs past the first commit with
 *   nothing made; or the blobs it needs read before it can tell, with where it
 *   would go on if the commit made nothing (`guess`), to read ahead along.
 * @param {(oids: string[]) => Promise<void>} read Reads blobs into what `step` reads them from.
 * @param {{ size: number }} budget How many steps that need blobs a round reads
 *   for; doubled by each round, and shared by the walks of one reader.
 * @returns {Promise<Commit | null>}
 */
async function followLine(state, step, read, budget) {
  for (;;) {
    const result = step(state);
    if ('next' in result) {
      state = result.next;
      continue;
    }
    if ('stop' in result) return result.stop;
    const wanted = new Set(result.wants);
    let ahead = result.guess;
    for (let asked = 1; ahead !== null && asked < budget.size; ) {
      const further = step(ahead);
      if ('next' in further) ahead = further.next;
      else if ('stop' in further) break;
      else {
        for (const oid of further.wants) wanted.add(oid);
        ahead = further.guess;
        asked += 1;
      }
    }
    await read([...wanted]);
    budget.size *= 2;
  }
}

/**
 * A step of a walk that follows what some files read, `value` of each blob,
 * back along the line of versions HEAD holds: on to the first parent whose
 * version reads as the commit's, a file at a time (a file a parent did not
 * hold, or one the commit deleted, reads as `value` of no blob), or a stop at
 * a commit no parent's version reads as. A commit with no parent made what it
 * reads unless that is what no file reads.
 *
 * @param {History} history
 * @param {(oid: string) => unknown} value `undefined` for a blob not read yet.
 * @returns {(commit: Commit) => ReturnType<Parameters<typeof followLine>[1]>}
 */
function valueStep(history, value) {
  return (commit) => {
    const unread = [];
    for (const [index, diff] of commit.diffs.entries()) {
      let same = true;
      for (const change of diff.values()) {
        const before = value(change.from);
        const after = value(change.to);
        if (before === undefined || after === undefined) {
          for (const oid of [change.from, change.to]) if (value(oid) === undefined) unread.push(oid);
          same = undefined;
          continue;
        }
        if (before !== after) {
          same = false;
          break;
        }
      }
      if (same === undefined) {
        // The parents are read in order, so this one has to be told first.
        for (const later of commit.diffs.slice(index + 1)) {
          for (const change of later.values()) for (const oid of [change.from, change.to]) if (value(oid) === undefined) unread.push(oid);
        }
        const parent = commit.parents[index];
        return { wants: [...new Set(unread)], guess: parent === undefined ? null : history.commits.get(parent) };
      }
      if (same) return commit.parents.length === 0 ? { stop: null } : { next: history.commits.get(commit.parents[index]) };
    }
    return { stop: commit };
  };
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
 * @param {{ repo: string, pathspec: string, ignore: Set<string>, pages: string[], heads: Map<string, string> }} options
 *   `heads` is the blob each page has at HEAD.
 * @returns {Promise<{ dates: Map<string, Date>, rounds: number, blobs: number }>}
 */
async function resolveDates({ repo, pathspec, ignore, pages, heads }) {
  const history = await readHistory(repo, [pathspec]);

  const stale = [...ignore].filter((sha) => !history.commits.has(sha));
  if (stale.length > 0) {
    throw new Error(
      `${IGNORE_REVS} lists ${stale.join(', ')}, which changed no page of ${pathspec}: ` +
        'a commit rewritten by a rebase, or one that never touched the content.',
    );
  }

  /** For each diff, the path each blob it deleted stood at: where a page it added with that blob came from. */
  const deletedAt = new WeakMap();
  const originOf = (diff, blob) => {
    if (!deletedAt.has(diff)) {
      deletedAt.set(diff, new Map([...diff].filter(([, change]) => change.status === 'D').map(([path, change]) => [change.from, path])));
    }
    return deletedAt.get(diff).get(blob);
  };

  /**
   * What each parent of a commit held of a page the commit holds at `path`
   * as `blob`: the same version (`same`), at that path or, moved unchanged,
   * at the one it came from; another version at the path (`changed`); or no
   * version the commit could have kept (`absent`: a page it created, or one
   * whose type it changed).
   */
  const sidesOf = (commit, path, blob) =>
    commit.diffs.map((diff) => {
      const change = diff.get(path);
      if (change === undefined) return { kind: 'same', path, blob };
      if (change.status === 'M') return { kind: 'changed', path, blob: change.from };
      if (change.status === 'A') {
        const origin = originOf(diff, blob);
        if (origin !== undefined) return { kind: 'same', path: origin, blob };
      }
      return { kind: 'absent' };
    });

  const dates = new Map();
  const texts = new Map();

  /** Move a walk to the parent `index` of `commit`, at that parent's version of the page. */
  const follow = (state, commit, index, side) => {
    state.sha = commit.parents[index];
    state.path = side.path;
    state.blob = side.blob;
  };

  /**
   * Walk a page back from where `state` stands, moving `state` along, until a
   * commit dates it. A change whose blobs are not read yet goes to `unknown`
   * with the blobs it needs, which says whether to pass over it as if it
   * changed only frontmatter (true) or to stop in front of it (false, and the
   * walk returns null).
   *
   * The walk follows the versions of the page HEAD holds, one commit at a
   * time, and never another side's. A commit with one parent dates the page
   * unless that parent held the same text: the same blob, the same blob at
   * another path (a page moved unchanged, whose history carries on there), or
   * a blob that differs in frontmatter alone. A merge that holds a version of
   * the page a parent held, at the page's path or moved there, follows that
   * parent, the first such in its parents' order, and leaves the other sides
   * and their changes behind, however much newer, since none of them is the
   * text the page shows. A merge that holds a version no parent held dates
   * the page, unless one parent's version differs from it in frontmatter
   * alone, whose history then dates it.
   */
  const walk = (state, unknown) => {
    for (;;) {
      const commit = history.commits.get(state.sha);
      if (commit === undefined) {
        throw new Error(
          `content dates: the history of ${state.page} (followed to ${state.path}) ends ` +
            'without the commit that created it. A damaged clone?',
        );
      }
      if (commit.parents.length === 0) return commit.date;
      const sides = sidesOf(commit, state.path, state.blob);
      const kept = sides.findIndex((side) => side.kind === 'same');
      if (kept !== -1) {
        follow(state, commit, kept, sides[kept]);
        continue;
      }
      // The parents that held another version of the page here: the ones whose text it may keep.
      const held = sides.flatMap((side, index) => (side.kind === 'changed' ? [{ ...side, index }] : []));
      if (held.length === 0) return commit.date; // Created here, or a type change: it counts.
      if (ignore.has(commit.sha)) {
        follow(state, commit, held[0].index, held[0]);
        continue;
      }
      const needed = [state.blob, ...held.map(({ blob }) => blob)];
      if (needed.some((oid) => !texts.has(oid))) {
        if (unknown(needed)) {
          follow(state, commit, held[0].index, held[0]);
          continue;
        }
        return null; // Come back to this commit once its blobs are read.
      }
      const text = held.find(({ blob }) => frontmatterOnly(texts.get(blob), texts.get(state.blob)));
      if (text === undefined) return commit.date;
      follow(state, commit, text.index, text);
    }
  };

  if (history.head === null) {
    throw new Error(`content dates: no commit of the history changed ${pathspec}, which HEAD holds. A damaged clone?`);
  }
  /** Pages still walking: where each one is in its history. */
  let walking = pages.map((page) => ({ page, sha: history.head.sha, path: page, blob: heads.get(page) }));
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
        walk({ ...state }, (needed) => {
          for (const oid of needed) if (!texts.has(oid)) wanted.add(oid);
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

/** The blob id git writes for the side of a change where the file is absent. */
const NO_BLOB = /^0+$/;

/**
 * The date a count of the lines of one file last changed: the commit that
 * made the number HEAD's version has, walking back along the versions HEAD
 * holds, the first whose version has a different number of matching lines
 * from every parent's. A rewrap or an edit inside an entry leaves the number
 * the page shows, and so its date. The versions are read newest first, in
 * rounds that each read twice as far ahead as the last, so the usual case,
 * where the newest commit to the file is the one that changed the count,
 * costs one request for one version.
 *
 * @param {string} repo
 * @param {{ file: string, lines: string }} count
 * @returns {Promise<Date | undefined>}
 */
async function lineCountDate(repo, { file, lines }) {
  const history = await readHistory(repo, [file]);
  if (history.head === null) return undefined;
  const pattern = new RegExp(lines, 'gm');
  const counted = new Map();
  const count = (oid) => (NO_BLOB.test(oid) ? 0 : counted.get(oid));
  const read = async (oids) => {
    for (const [oid, text] of await readBlobs(repo, oids)) counted.set(oid, text.match(pattern)?.length ?? 0);
  };
  const made = await followLine(history.head, valueStep(history, count), read, { size: 1 });
  return made?.date;
}

/**
 * The date a text a page shows of other files last changed: the commit that
 * made the text HEAD's versions show, walking back along them, the first that
 * changed a match of the pattern in one of the files from every parent's
 * version, each match read with every run of white space as one space, so a
 * rewrap inside a match leaves the text, and so does an edit anywhere else in
 * the file. A file added or deleted goes from no match or to none, so a guide
 * moved to another folder, which moves its line to another heading of the
 * index, moves the page. The versions are read newest first, in the same
 * doubling rounds as a count of lines, so the usual case costs one request.
 *
 * @param {string} repo
 * @param {{ files: string[], pattern: string }} text
 * @returns {Promise<Date | undefined>}
 */
async function textDate(repo, { files, pattern }) {
  const history = await readHistory(repo, files);
  if (history.head === null) return undefined;
  const regex = new RegExp(pattern, 'gm');
  const matched = new Map();
  const matches = (oid) => (NO_BLOB.test(oid) ? '' : matched.get(oid));
  const read = async (oids) => {
    for (const [oid, text] of await readBlobs(repo, oids)) {
      matched.set(oid, (text.match(regex) ?? []).map((match) => match.replace(/\s+/g, ' ')).join('\n'));
    }
  };
  const made = await followLine(history.head, valueStep(history, matches), read, { size: 1 });
  return made?.date;
}

/**
 * The "Verified by" line each page would draw from one version of the
 * conformance report: page path to the line, as the join gives it
 * (src/lib/conformance-evidence.mjs), for every page that would show one.
 * The join reads the report as far as it resolves: a document a version
 * cites that no page cites now counts nowhere, and a version the join cannot
 * read at all, one from before the checks named their documents, draws no
 * line on any page.
 *
 * @param {object} report The parsed report.
 * @param {Array<{ key: string, lang: 'en' | 'es', references: object[] }>} pages
 * @returns {Map<string, string>}
 */
function verifiedLines(report, pages) {
  const lines = new Map();
  for (const lang of ['en', 'es']) {
    const own = pages.filter((page) => page.lang === lang);
    if (own.length === 0) continue;
    const prefix = lang === 'es' ? '/es' : '';
    let evidence;
    try {
      evidence = conformanceEvidence({
        report,
        pages: own,
        bibliographyUrl: `${siteUrl}${basePath}${prefix}/reference/bibliography/`,
        reportPath: `${basePath}${prefix}/reference/conformance/`,
        lang,
        strict: false,
      });
    } catch {
      continue;
    }
    for (const page of own) {
      const line = evidence.verifiedBy(page.references);
      if (line) lines.set(page.key, JSON.stringify(line));
    }
  }
  return lines;
}

/**
 * What a version of the report says that the lines are drawn from: each
 * check's domain and documents, and each domain's title. A commit that
 * changed only values, verdicts or names of checks leaves this as it was,
 * and so every line, and the join is not made again for it.
 */
const lineSource = (report) =>
  JSON.stringify([
    (report?.domains ?? []).map((domain) => [domain?.id, domain?.title]),
    (report?.checks ?? []).map((check) => [check?.id, check?.domain, check?.reference?.documents]),
  ]);

/**
 * The date each page's "Verified by" line last changed: the commit that made
 * the line the page shows at HEAD, walking back along the versions of the
 * report HEAD holds, the page's references being what they are now. Only the
 * commits that hold the component that draws the line are read, by their
 * place in the history and not by their dates, which a rebase can tie or put
 * out of order: before it, no page showed a line for a commit to change. So a
 * commit dates a page when its version of the report draws the page another
 * line than its parent's, and its parent holds the component too; the commit
 * that added the component dates no page, nor does a merge through which the
 * component arrived. A merge follows the first parent that holds the
 * component and draws the page the same line, wherever it took the report
 * from; and when none does, it dates the page if its first parent drew it a
 * line, the line main showed changing there, which no commit that drew one
 * made before it. A page is not walked further once no commit left to read is
 * dated later than its own content, since none of them could date it later
 * than it is. The versions are read newest first, in rounds that each read
 * twice as far ahead as the last, as a count of lines reads its file, and
 * shared by every page.
 *
 * @param {{ repo: string, contentDir: string, file: string, drawnBy: string, pages: string[], dates: Map<string, Date> }} options
 *   `pages` are the pages the count is for, as git names them, and `dates`
 *   the date each one's own content last changed.
 * @returns {Promise<Map<string, Date>>} The pages a commit to the report dates.
 */
async function verifiedLineDates({ repo, contentDir, file, drawnBy, pages, dates }) {
  const result = new Map();
  const history = await readHistory(repo, [file, drawnBy]);
  if (history.head === null) return result;
  /** The latest date of each commit and of every commit it follows: none of them can date a page later. */
  const latest = new Map();
  for (let at = history.order.length - 1; at >= 0; at -= 1) {
    const commit = history.order[at];
    latest.set(commit.sha, commit.parents.map((parent) => latest.get(parent)).reduce(later, commit.date));
  }
  const newest = latest.get(history.head.sha);
  if (!pages.some((page) => dates.get(page) < newest)) return result;
  const wanted = new Set(pages);
  const cited = (await readPageReferences(contentDir))
    .map((page) => ({ ...page, key: relative(repo, page.file).split(sep).join('/') }))
    .filter((page) => page.references.length > 0 && wanted.has(page.key) && dates.has(page.key));
  if (cited.length === 0) return result;
  const none = new Map();
  /** Blob id to the lines its version draws; versions alike in what lines are drawn from share one reading. */
  const lines = new Map();
  const byLineSource = new Map();
  const linesOf = (oid) => (NO_BLOB.test(oid) ? none : lines.get(oid));
  const read = async (oids) => {
    for (const [oid, text] of await readBlobs(repo, oids)) {
      let report;
      try {
        report = JSON.parse(text);
      } catch {
        lines.set(oid, none);
        continue;
      }
      const source = lineSource(report);
      if (!byLineSource.has(source)) byLineSource.set(source, verifiedLines(report, cited));
      lines.set(oid, byLineSource.get(source));
    }
  };
  const budget = { size: 1 };
  for (const { key } of cited) {
    const own = dates.get(key);
    const step = (commit) => {
      if (own >= latest.get(commit.sha)) return { stop: null };
      if (commit.parents.length === 0) return { stop: null }; // The component came with the first commit.
      // Which parents drew a line, and for those, whether it was this one.
      const draws = commit.diffs.map((diff) => diff.get(drawnBy)?.status !== 'A');
      const unread = [];
      const same = commit.diffs.map((diff, index) => {
        if (!draws[index]) return false;
        const change = diff.get(file);
        if (change === undefined) return true;
        const before = linesOf(change.from);
        const after = linesOf(change.to);
        if (before === undefined || after === undefined) {
          for (const oid of [change.from, change.to]) if (linesOf(oid) === undefined) unread.push(oid);
          return undefined;
        }
        return before.get(key) === after.get(key);
      });
      const first = same.findIndex((answer) => answer !== false);
      if (first !== -1 && same[first] === undefined) {
        return { wants: unread, guess: history.commits.get(commit.parents[first]) };
      }
      if (first !== -1) return { next: history.commits.get(commit.parents[first]) };
      return { stop: draws[0] ? commit : null };
    };
    const made = await followLine(history.head, step, read, budget);
    if (made !== null) result.set(key, made.date);
  }
  return result;
}

/** Whether a path from site/date-sources.json names `path`: the file, or a directory holding it. */
const names = (spec, path) => (spec.endsWith('/') ? path.startsWith(spec) : path === spec);

/** The later of two dates, either of which may be missing. */
const later = (a, b) => (a === undefined || (b !== undefined && b > a) ? b : a);

/**
 * Move the date of each page `site/date-sources.json` lists to the newest
 * change of what it is built from, when that is later than its own: a
 * source, a count or a text.
 *
 * @param {{ repo: string, pathspec: string, contentDir: string, pages: string[], dates: Map<string, Date>, entries: ReturnType<typeof readDateSources> }} options
 * @returns {Promise<{ sourced: number, raised: number, commits: Map<string, { sha: string, date: Date } | null> }>}
 *   How many pages have sources, how many of them a source dates, and for
 *   each source outside the content tree the commit that made the version
 *   HEAD has (null when no commit read made it).
 */
async function applySources({ repo, pathspec, contentDir, pages, dates, entries }) {
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
  // history is read from trees alone. Each source is followed back along the
  // versions HEAD holds to the commit that made HEAD's version: the first
  // that changed it from every parent's, a file or anything under a
  // directory. That commit dates the pages it is a source of, and is kept
  // with its date: the conformance report names it as the commit of the rows
  // it renders, and the Dataset hands out its files there. Past a merge that
  // kept one side's version, the other side's commits are not followed,
  // however much newer, since the page shows none of their rows, so the page
  // is dated by the commit its Dataset names.
  const files = sources.filter((spec) => !spec.startsWith(content));
  const commits = new Map();
  if (files.length > 0) {
    const tracked = await filesAtHead(repo, files);
    const missing = files.find((spec) => !tracked.some((path) => names(spec, path)));
    if (missing !== undefined) throw stale(`the source ${missing}`);
    const history = await readHistory(repo, files);
    for (const spec of files) {
      const step = (commit) => {
        const index = commit.diffs.findIndex((diff) => ![...diff.keys()].some((path) => names(spec, path)));
        if (index === -1) return { stop: commit };
        return commit.parents.length === 0 ? { stop: null } : { next: history.commits.get(commit.parents[index]) };
      };
      // A history in which no commit made HEAD's version is one this clone
      // does not have whole; the source is named, and asking for its commit fails.
      const made = history.head === null ? null : await followLine(history.head, step, async () => {}, { size: 1 });
      if (made !== null) newest.set(spec, made.date);
      commits.set(spec, made === null ? null : { sha: made.sha, date: made.date });
    }
  }

  // A count of files moves only with a commit that added or deleted more
  // files than the other: a move inside the set, or an edit, leaves the
  // number shown. A count of lines moves only with a commit that changed it.
  const sets = new Map(
    entries.flatMap((entry) => Object.values(entry.counts)).map((set) => [JSON.stringify(set), set]),
  );
  /** A count each page has of its own: set as JSON to the date of each page it dates. */
  const ownCounts = new Map();
  for (const [key, set] of sets) {
    if (set.report !== undefined) {
      const tracked = await filesAtHead(repo, [set.report, set.drawnBy]);
      for (const path of [set.report, set.drawnBy]) if (!tracked.includes(path)) throw stale(`the counted file ${path}`);
      const counted = pages.filter((page) =>
        entries.some(
          (entry) =>
            Object.values(entry.counts).some((other) => JSON.stringify(other) === key) &&
            entry.pages.some((spec) => names(spec, page)),
        ),
      );
      ownCounts.set(
        key,
        await verifiedLineDates({ repo, contentDir, file: set.report, drawnBy: set.drawnBy, pages: counted, dates: walked }),
      );
      continue;
    }
    if (!Array.isArray(set)) {
      if (!(await filesAtHead(repo, [set.file])).includes(set.file)) throw stale(`the counted file ${set.file}`);
      newest.set(key, await lineCountDate(repo, set));
      continue;
    }
    if ((await filesAtHead(repo, set)).length === 0) throw stale(`the counted files ${set.join(' ')}`);
    const history = await readHistory(repo, set);
    // A version counts as many files as its parent's when it added as many as it deleted.
    const step = (commit) => {
      const index = commit.diffs.findIndex((diff) => {
        let balance = 0;
        for (const change of diff.values()) balance += change.status === 'A' ? 1 : change.status === 'D' ? -1 : 0;
        return balance === 0;
      });
      if (index === -1) return { stop: commit };
      return commit.parents.length === 0 ? { stop: null } : { next: history.commits.get(commit.parents[index]) };
    };
    const made = history.head === null ? null : await followLine(history.head, step, async () => {}, { size: 1 });
    if (made !== null) newest.set(key, made.date);
  }

  // A text moves only with a commit that changed one of its matches.
  const texts = new Map(
    entries.flatMap((entry) => Object.values(entry.texts)).map((set) => [JSON.stringify(set), set]),
  );
  for (const [key, set] of texts) {
    if ((await filesAtHead(repo, set.files)).length === 0) throw stale(`the files of the text ${set.files.join(' ')}`);
    newest.set(key, await textDate(repo, set));
  }

  const sourced = new Set();
  const raised = new Set();
  for (const entry of entries) {
    const shared = [
      ...entry.sources.map((spec) => newest.get(spec)),
      ...Object.values(entry.counts).map((set) => newest.get(JSON.stringify(set))),
      ...Object.values(entry.texts).map((set) => newest.get(JSON.stringify(set))),
    ].reduce(later, undefined);
    for (const page of pages.filter((path) => entry.pages.some((spec) => names(spec, path)))) {
      sourced.add(page);
      const when = Object.values(entry.counts)
        .map((set) => ownCounts.get(JSON.stringify(set))?.get(page))
        .reduce(later, shared);
      if (when !== undefined && when > dates.get(page)) {
        dates.set(page, when);
        raised.add(page);
      }
    }
  }
  return { sourced: sourced.size, raised: raised.size, commits };
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
 *   sourceCommit: (source: string) => { sha: string, date: Date },
 *   pages: number, rounds: number, blobs: number, sourced: number, raised: number,
 * }>} `dateOf` takes a content file's path, absolute or relative to the site
 *   root, and returns the date its content last changed. A file git has never
 *   seen (a page being written, not committed yet) is dated by the file
 *   itself; a committed one without a date, or a path that is no page, throws.
 *   `sourceCommit` takes a source date-sources.json names outside the content
 *   tree, as it names it, and returns the commit that made the version HEAD
 *   has, a merge that joined two sides of it included, so that the files at
 *   that commit are the ones the page renders, and the page is dated by it;
 *   any other path throws. `sourced` counts the pages date-sources.json lists
 *   and `raised` those of them a source dates.
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
  /** The blob each page has at HEAD, where its walk back starts. */
  const heads = new Map();
  const listing = nulFields((entry) => {
    const tab = entry.indexOf('\t');
    if (tab === -1) return;
    const path = entry.slice(tab + 1);
    pages.push(path);
    heads.set(path, entry.slice(0, tab).split(' ')[2]);
  });
  await git(repo, ['ls-tree', '-r', '-z', 'HEAD', '--', pathspec], {
    onData: (chunk) => listing.push(chunk),
  });
  listing.end();
  if (pages.length === 0) {
    throw new Error(`content dates: HEAD has no file under ${pathspec}.`);
  }
  const committed = new Set(pages);

  const { dates, rounds, blobs } = await resolveDates({ repo, pathspec, ignore, pages, heads });
  const { sourced, raised, commits } = await applySources({ repo, pathspec, contentDir, pages, dates, entries });

  return {
    pages: dates.size,
    rounds,
    blobs,
    sourced,
    raised,
    sourceCommit(source) {
      const commit = commits.get(source);
      if (commit) return commit;
      if (commits.has(source)) {
        throw new Error(
          `content dates: no commit of the history holds the version of ${source} HEAD has, so the commit ` +
            'of what the page renders cannot be named. A damaged clone?',
        );
      }
      throw new Error(
        `content dates: ${source} is no source ${DATE_SOURCES} names outside the content tree, so no commit of it ` +
          'was read; list it as a source of the page that shows it.',
      );
    },
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
