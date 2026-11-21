/**
 * Whether a commit to a data source changed what the pages built from it
 * render (site/date-sources.json, src/lib/content-dates.mjs).
 *
 * A page is dated by every commit to its sources, so a commit that changed
 * none of what a page shows dated it all the same: one JSDoc line of home.ts
 * dated both landing pages, and the commit that took the old base path out of
 * a note's link in bibliography.mjs dated both bibliographies. Two kinds of
 * change render nothing, and are passed over:
 *
 * - every link through a legacy origin of site-targets.json rewritten for the
 *   current target, the rewrite the page rule passes over in a page
 *   (`linksMovedOnly` in src/lib/date-rules.mjs), run on the old side alone,
 *   so a link given the old base path still counts;
 * - in a JavaScript or TypeScript module, its comments and the layout of its
 *   code: the module printed back without comments by TypeScript's own
 *   printer reads the same before and after.
 *
 * Any other change counts, a refactor that writes the same output another way
 * included: a module whose output the page shows only through what it reads
 * from other files is dated by those files (a `texts` reader), not by its
 * code.
 */
import ts from 'typescript';

/** The modules whose comments and layout render nothing. */
const CODE = /\.(?:[cm]?js|[cm]?ts)$/;

/**
 * A module as TypeScript prints it back without its comments.
 *
 * @param {string} text
 * @param {string} path For the kind of script.
 * @returns {string}
 */
function bareCode(text, path) {
  const kind = /\.[cm]?ts$/.test(path) ? ts.ScriptKind.TS : ts.ScriptKind.JS;
  const file = ts.createSourceFile(path, text, ts.ScriptTarget.Latest, false, kind);
  return ts.createPrinter({ removeComments: true }).printFile(file);
}

/**
 * Whether `before` and `after`, two versions of the source at `path`, render
 * alike.
 *
 * @param {string} path
 * @param {string} before
 * @param {string} after
 * @param {Array<[RegExp, string]>} moves The legacy link rewrites (date-rules.mjs `MOVES`).
 * @returns {boolean}
 */
export function renderedAlike(path, before, after, moves) {
  if (before === after) return true;
  const moved = moves.reduce((text, [pattern, replace]) => text.replace(pattern, replace), before);
  if (moved === after) return true;
  if (!CODE.test(path)) return false;
  // The old side as it was and with its links moved: a comment changed in a
  // module whose links still go through the old base path is told by the
  // first, a comment changed beside a link rewrite by the second.
  const bare = bareCode(after, path);
  return bareCode(before, path) === bare || (moved !== before && bareCode(moved, path) === bare);
}
