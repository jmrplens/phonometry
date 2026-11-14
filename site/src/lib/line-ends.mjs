/**
 * A committed text file as the repository holds it, whatever line ends the
 * checkout gave it.
 *
 * The repository stores its text with line feeds, but a clone made with
 * `core.autocrlf=true` (the default of Git for Windows, and a setting a clone
 * on Linux or macOS can carry too) writes every file the root .gitattributes
 * does not pin with a carriage return before each line feed. The readers of
 * the site's own files were written against line feeds: one split a file on
 * `\n` and matched each line to its end with a pattern whose `.` stops at the
 * carriage return, and one compared a committed file with the text its
 * generator writes. On such a checkout `CITATION.cff` could not be read at
 * all, a page's code fence was taken for prose, and a generated file was
 * reported stale. Each reader of a committed text file reads it through this
 * module instead, so the text it reads is the text the commit holds.
 *
 * A lone carriage return stays: no checkout writes one as a line end, so it is
 * part of what the file says.
 */
import { readFileSync } from 'node:fs';

/**
 * `text` with each carriage return and line feed pair a line feed.
 *
 * @param {string} text
 * @returns {string}
 */
export const withLineFeeds = (text) => text.replace(/\r\n/g, '\n');

/**
 * The committed text file at `path`, read as UTF-8 with its line ends line
 * feeds ({@link withLineFeeds}).
 *
 * @param {string | URL} path
 * @returns {string}
 */
export const readCommittedText = (path) => withLineFeeds(readFileSync(path, 'utf8'));
