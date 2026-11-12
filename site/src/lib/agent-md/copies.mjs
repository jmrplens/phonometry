/**
 * Which `index.md` files under a directory are copies a run of
 * `scripts/agent-md.mjs --public` wrote, so that the next run removes those
 * and nothing else.
 *
 * Every run starts by removing the copies the last one left, or a page that
 * moved would keep publishing its old copy. The directory it writes into is
 * public/ by default and any `--out` it is given otherwise, and an `index.md`
 * there may be no copy at all: docs/ holds 43, the GitHub edition's, the API
 * table's and the contributor guide's, which open otherwise. A copy
 * is told apart by its opening, the title and then the sentence every header
 * starts with (src/lib/agent-md/header.mjs `LEAD_OPENING`), and a file that
 * does not open that way is left where it is.
 *
 * @module
 */
import { existsSync, readdirSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';

import { LEAD_OPENING } from './header.mjs';

/**
 * Whether a text opens as a copy does: a `# ` title, a blank line, and the
 * lead sentence of either language.
 *
 * @param {string} text
 * @returns {boolean}
 */
export function isWrittenCopy(text) {
  const [title, blank, lead] = text.split('\n', 3);
  return (
    /^# \S/u.test(title ?? '') &&
    blank === '' &&
    Object.values(LEAD_OPENING).some((opening) => (lead ?? '').startsWith(`> ${opening}`))
  );
}

/**
 * Every copy a previous run left under a directory.
 *
 * @param {string} dir
 * @returns {string[]}  Paths of the `index.md` files that open as a copy.
 */
export function writtenCopies(dir) {
  /** @type {string[]} */
  const found = [];
  const walk = (current) => {
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const path = join(current, entry.name);
      if (entry.isDirectory()) walk(path);
      else if (entry.name === 'index.md' && isWrittenCopy(readFileSync(path, 'utf8'))) found.push(path);
    }
  };
  walk(dir);
  return found;
}

/**
 * Removes the copies a previous run left under a directory, and nothing else.
 *
 * @param {string} dir
 * @returns {number}  How many were removed.
 */
export function removeWrittenCopies(dir) {
  const stale = writtenCopies(dir);
  for (const file of stale) rmSync(file);
  return stale.length;
}

/**
 * The files a run would write over that are not copies: an `index.md` at the
 * place of a page's copy that some other hand wrote. The cleanup spares such a
 * file, and the run must not then overwrite it either, so it refuses before it
 * removes or writes anything.
 *
 * @param {Iterable<string>} targets  Where the run would write each copy.
 * @returns {string[]}  The targets that exist and do not open as a copy.
 */
export function handwrittenTargets(targets) {
  return [...targets].filter((target) => existsSync(target) && !isWrittenCopy(readFileSync(target, 'utf8')));
}
