/**
 * When a commit moves the date a page's content last changed, and the two
 * files that tell the rule what it cannot see for itself. The history is
 * read in src/lib/content-dates.mjs, once per build; nothing here starts a
 * process, so a page, the sitemap stamp and the first-publication dates can
 * all import the rule and the day they publish without reaching for git.
 *
 * The rule: a commit moves a page's date unless
 *
 * - every change it made to the file is inside the frontmatter keys `title`,
 *   `description` or `sidebar` (search snippets and navigation, not the text
 *   of the page), or a mode change that left the content as it was;
 * - it moved the file without changing it: the page reached its new address
 *   with the same blob, and its history carries on at the old one;
 * - or it is listed in `site/date-ignore-revs.txt`, which names the
 *   mechanical sweeps the first rule cannot see (one that rewrote the lead
 *   sentence of every API page along with its description).
 *
 * The commit that created a page always counts, listed or not: no page is
 * older than its first version.
 *
 * Some pages are built from data outside their own file: the landing page
 * states the conformance counts and the release, the conformance report
 * renders `docs/conformance.json`, a catalogue page renders its table.
 * Their file can stand still while what a reader sees changes, so
 * `site/date-sources.json` lists them with the files they are built from,
 * and such a page is dated by the newest of its own date and theirs. Every
 * commit to a source counts, since a source is data rather than a page with
 * frontmatter; a source inside the content tree stands for the pages there,
 * each dated by the rule above; and a count of files, which is all some
 * pages show of a directory, moves only with a commit that changed how many
 * there are. The build fails on a page or a source that HEAD does not have,
 * and site/scripts/content-dates.test.mjs fails on a page that imports data
 * or a component built from it without being listed.
 */
import { existsSync, readFileSync } from 'node:fs';

import { domainIds } from '../data/topics.mjs';

/** The content collection, relative to the site root. */
export const CONTENT_DIR = 'src/content/docs';

/** The commits that move no date, relative to the site root. */
export const IGNORE_REVS = 'date-ignore-revs.txt';

/** The pages built from data outside their file, and that data; relative to the site root. */
export const DATE_SOURCES = 'date-sources.json';

/** The frontmatter keys whose changes move no date. */
export const DATELESS_KEYS = Object.freeze(['title', 'description', 'sidebar']);

/** A commit as git names it in full, and as the ignore list has to. */
export const FULL_SHA = /^[0-9a-f]{40}$/;

/** What a pathspec of a count writes for each topic of the navigation. */
const TOPIC = '{topic}';

const DATELESS = new Set(DATELESS_KEYS);

/**
 * The frontmatter and the body of a page, line endings normalised.
 *
 * @param {string} text
 * @returns {{ head: string | null, body: string }}
 */
function splitPage(text) {
  const normal = text.replace(/\r\n?/g, '\n');
  // The closing fence is a line of its own, so a `---` at the end of a
  // description line does not close the frontmatter early.
  const match = /^---[ \t]*\n(?:([\s\S]*?)\n)?---[ \t]*(?:\n|$)/.exec(normal);
  if (!match) return { head: null, body: normal };
  return { head: match[1] ?? '', body: normal.slice(match[0].length) };
}

/**
 * The frontmatter with the dateless keys taken out: each top-level key with
 * the lines that continue it (a folded description, the fields of `sidebar`),
 * trailing blank lines dropped, so the same text before and after a commit
 * means the commit changed nothing else up there. A comment at column 0 is a
 * block of its own and counts like any other key.
 *
 * @param {string} head
 * @returns {string}
 */
function datedFrontmatter(head) {
  const blocks = [];
  for (const line of head.split('\n')) {
    const key = /^([A-Za-z_][\w-]*)\s*:/.exec(line);
    if (key || line.startsWith('#') || blocks.length === 0) {
      blocks.push({ key: key?.[1] ?? null, lines: [line] });
    } else {
      blocks.at(-1).lines.push(line);
    }
  }
  return blocks
    .filter((block) => !DATELESS.has(block.key))
    .map((block) => block.lines.join('\n').replace(/\s+$/, ''))
    .join('\n');
}

/**
 * Whether going from `before` to `after` changed only the dateless keys of
 * the frontmatter (or nothing at all).
 *
 * @param {string} before The page as it was.
 * @param {string} after The page as the commit left it.
 * @returns {boolean}
 */
export function frontmatterOnly(before, after) {
  const a = splitPage(before);
  const b = splitPage(after);
  if (a.body !== b.body) return false;
  if (a.head === null || b.head === null) return a.head === b.head;
  return datedFrontmatter(a.head) === datedFrontmatter(b.head);
}

/**
 * The commits `site/date-ignore-revs.txt` lists: one full 40-character SHA
 * per line, `#` starting a comment, blank lines ignored.
 *
 * @param {string} file
 * @returns {Set<string>}
 */
export function readIgnoreRevs(file) {
  const revs = new Set();
  if (!existsSync(file)) return revs;
  readFileSync(file, 'utf8')
    .split('\n')
    .forEach((raw, index) => {
      const line = raw.replace(/#.*/, '').trim();
      if (line === '') return;
      if (!FULL_SHA.test(line)) {
        throw new Error(
          `${file}:${index + 1}: "${line}" is not a full 40-character commit SHA ` +
            '(abbreviated ones can grow ambiguous as the history does).',
        );
      }
      revs.add(line);
    });
  return revs;
}

/**
 * The entries of `site/date-sources.json`: each names pages (`pages`), the
 * files they are built from (`sources`) and the sets of files they count
 * (`counts`, each a list of git pathspecs under the name of the number the
 * page shows). Paths are from the repository root, as git names them, and
 * one ending in `/` is a directory. A pathspec of a count that holds
 * `{topic}` stands for one per topic, so a count over the topic directories
 * follows the navigation the way `src/data/repo-stats.mjs` does and needs no
 * list of folders kept beside it. Keys that begin with an underscore are
 * notes. No file means no page has sources.
 *
 * @param {string} file
 * @param {{ topics?: readonly string[] }} [options] What `{topic}` stands
 *   for: the topics the navigation teaches unless a caller says otherwise.
 * @returns {Array<{ pages: string[], sources: string[], counts: Record<string, string[]> }>}
 */
export function readDateSources(file, { topics = domainIds } = {}) {
  if (!existsSync(file)) return [];
  let data;
  try {
    data = JSON.parse(readFileSync(file, 'utf8'));
  } catch (error) {
    throw new Error(`${file}: ${error.message}`);
  }
  if (!Array.isArray(data?.entries)) throw new Error(`${file}: no "entries" list.`);
  return data.entries.map((entry, index) => {
    const where = `${file}, entry ${index + 1}`;
    const unknown = Object.keys(entry ?? {}).filter(
      (key) => !key.startsWith('_') && !['pages', 'sources', 'counts'].includes(key),
    );
    if (unknown.length > 0) throw new Error(`${where}: unknown key(s) ${unknown.join(', ')}.`);
    const paths = (value, key, { magic = false } = {}) => {
      const list = value ?? [];
      const bad = Array.isArray(list)
        ? list.filter(
            (path) =>
              typeof path !== 'string' ||
              path === '' ||
              path.startsWith('/') ||
              path.split('/').includes('..') ||
              (!magic && path.startsWith(':')),
          )
        : [list];
      if (bad.length > 0) {
        throw new Error(
          `${where}: "${key}" takes paths from the repository root` +
            `${magic ? ' or git pathspecs' : ''}, not ${JSON.stringify(bad[0])}.`,
        );
      }
      return list;
    };
    const pages = paths(entry.pages, 'pages');
    const sources = paths(entry.sources, 'sources');
    const counted = entry.counts ?? {};
    if (typeof counted !== 'object' || Array.isArray(counted) || counted === null) {
      throw new Error(`${where}: "counts" maps the name of each number to its pathspecs.`);
    }
    const counts = Object.fromEntries(
      Object.entries(counted).map(([name, set]) => {
        const specs = paths(set, `counts.${name}`, { magic: true }).flatMap((spec) => {
          if (!spec.includes(TOPIC)) return [spec];
          if (topics.length === 0) {
            throw new Error(`${where}: ${TOPIC} in counts.${name}, and the navigation teaches no topic.`);
          }
          return topics.map((topic) => spec.replaceAll(TOPIC, topic));
        });
        if (specs.length === 0) throw new Error(`${where}: no pathspec for the count ${name}.`);
        return [name, specs];
      }),
    );
    if (pages.length === 0) throw new Error(`${where} names no page.`);
    if (sources.length === 0 && Object.keys(counts).length === 0) {
      throw new Error(`${where} names no source.`);
    }
    return { pages, sources, counts };
  });
}

/**
 * The day a date falls on in UTC, as `YYYY-MM-DD`: the form the sitemap and
 * the structured data publish, and the day the footer shows.
 *
 * @param {Date} date
 * @returns {string}
 */
export function isoDay(date) {
  return date.toISOString().slice(0, 10);
}
