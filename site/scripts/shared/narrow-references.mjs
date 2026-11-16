/**
 * A narrow reader of the `references` of a page's frontmatter, for the tests
 * that run before the install, when the site has no YAML parser: the catalogue
 * sources test (scripts/catalogue-sources.test.mjs) and the catalogue page list
 * test (scripts/catalogue-page-list.test.mjs) read the pages through it.
 *
 * @module
 */
import assert from 'node:assert/strict';

export const READ_KEYS = new Set(['type', 'authors', 'organization', 'designation', 'title', 'year', 'tables']);

/**
 * The entries of a page's `references`, each with the keys this test reads.
 *
 * A narrow reader, like the one in scripts/generate_site_reports.py: the site
 * has no YAML parser installed and the frontmatter is written one key per
 * line. An entry opens at a list item under `references:`, every other line of
 * it is one key with its value on that line, and `tables` and `authors` are
 * flow lists of quoted strings, read as JSON. Any other line under
 * `references:` fails the test rather than reading as no claim: a key whose
 * value is on the lines below it (`tables` written as a block list), a key
 * before the first item, an item or a comment at the margin, and a list
 * written on the line of its key. A blank line ends nothing.
 */
export function readReferences(text, file) {
  const end = text.indexOf('\n---', 3);
  assert.ok(text.startsWith('---') && end > 0, `${file} has no frontmatter`);
  const entries = [];
  let inReferences = false;
  // The first line split off is the rest of the opening fence, so each line's
  // index is its line number less one.
  for (const [index, line] of text.slice(3, end).split('\n').entries()) {
    if (!line.trim()) continue;
    const where = `${file}:${index + 1}`;
    if (/^\S/.test(line)) {
      // Under `references:` the only line at the margin is the next key: an
      // item or a comment there is YAML that would otherwise end the list.
      assert.ok(
        !inReferences || /^[A-Za-z_][A-Za-z0-9_]*:/.test(line),
        `${where}: a references line this reader cannot follow: ${JSON.stringify(line)}`,
      );
      const [name, ...rest] = line.split(':');
      const value = rest.join(':').trim();
      assert.ok(
        name !== 'references' || value === '' || value === '[]',
        `${where}: references written on the line of its key, which this reader cannot follow: ${JSON.stringify(line)}`,
      );
      inReferences = name === 'references' && value === '';
      continue;
    }
    if (!inReferences) continue;
    const key = /^ {2}(- | {2})([A-Za-z]+): (.+)$/.exec(line);
    assert.ok(
      key && (key[1] === '- ' || entries.length > 0),
      `${where}: a references line this reader cannot follow: ${JSON.stringify(line)}`,
    );
    if (key[1] === '- ') entries.push({});
    if (!READ_KEYS.has(key[2])) continue;
    const entry = entries.at(-1);
    if (key[2] === 'tables' || key[2] === 'authors') {
      assert.match(key[3], /^\[.*\]$/, `${where}: ${key[2]} is not written as a flow list on one line`);
      entry[key[2]] = JSON.parse(key[3]);
    } else {
      entry[key[2]] = key[3].replace(/^"(.*)"$/, '$1');
    }
  }
  return entries;
}
