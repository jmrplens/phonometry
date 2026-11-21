/**
 * Every key a page's frontmatter can hold, each in the class that says
 * whether a change to it moves the date the page's content last changed
 * (src/lib/date-rules.mjs).
 *
 * - `content`: what a reader reads on the page, or how the page is laid
 *   out: a change to it is a change to the page, and moves its date.
 * - `label`: what names the page in search snippets and in the navigation
 *   (the title, the description, the sidebar entry): a page renamed or
 *   reordered says the same as before, so its date stays.
 * - `metadata`: read only by machines (the structured data, the ranking of
 *   the site search), never shown as the page's text: its date stays.
 *
 * The date rule passes over a commit that changed only `label` and
 * `metadata` keys, and refuses a key in no class, so a key added for the
 * structured data cannot move every date it touches before anyone has said
 * which class it is in. The content collection (src/content.config.ts)
 * refuses a key its schema declares and this list does not class, so the
 * key is classed the day it is added, not the day a page first carries it.
 * Keys a page held once and no longer can (none today) stay here, since the
 * rule reads every version of a page it walks back over.
 */

/** The classes, with what each means for the date. */
export const KEY_CLASSES = Object.freeze({
  content: 'a change moves the date',
  label: 'search snippets and navigation; a change moves no date',
  metadata: 'read by machines only; a change moves no date',
});

/**
 * The class of each frontmatter key: Starlight's own (`@astrojs/starlight`,
 * its `docsSchema`), the topics plugin's `topic`, and the keys
 * src/content.config.ts adds.
 *
 * @type {Readonly<Record<string, keyof typeof KEY_CLASSES>>}
 */
export const FRONTMATTER_KEYS = Object.freeze({
  // Starlight.
  title: 'label',
  description: 'label',
  sidebar: 'label',
  slug: 'content',
  editUrl: 'content',
  // What the page writes into its <head> for machines: its <title>, the
  // structured data and the meta tags (presentationalHeadEntries says which
  // entries those are, and a test refuses any other).
  head: 'metadata',
  tableOfContents: 'content',
  template: 'content',
  hero: 'content',
  lastUpdated: 'content',
  prev: 'content',
  next: 'content',
  banner: 'content',
  pagefind: 'metadata',
  draft: 'content',
  // starlight-sidebar-topics: the topic of the navigation a page is under.
  topic: 'label',
  // This site.
  references: 'content',
  searchTitle: 'metadata',
  searchWeight: 'metadata',
  corrects: 'metadata',
});

/**
 * The tags a page's `head` may hold and stay metadata: what only browsers,
 * search engines and agents read. A `link` is one when its `rel` points to
 * another address of the page; a `script` only when it is structured data.
 */
const HEAD_TAGS = Object.freeze({
  title: () => true,
  meta: () => true,
  script: (attrs) => attrs?.type === 'application/ld+json',
  link: (attrs) => String(attrs?.rel ?? '').split(/\s+/).every((rel) => ['canonical', 'alternate'].includes(rel)),
});

/**
 * The entries of a page's `head` that are no metadata, each described. A
 * stylesheet, a script a browser runs or any other tag shapes what the page
 * shows, and the date rule would pass over a change to it, since `head` is a
 * `metadata` key: such an entry is refused, and the day one is wanted the key
 * is classed again by a person rather than by default.
 *
 * @param {unknown} head The frontmatter's `head`, as YAML reads it.
 * @returns {string[]}
 */
export function presentationalHeadEntries(head) {
  if (head === undefined || head === null) return [];
  if (!Array.isArray(head)) return ['head is not a list of tags'];
  return head.flatMap((entry, index) => {
    const tag = entry?.tag;
    const allowed = typeof tag === 'string' && Object.hasOwn(HEAD_TAGS, tag) ? HEAD_TAGS[tag] : undefined;
    if (allowed?.(entry.attrs)) return [];
    return [`head entry ${index + 1}, <${tag ?? '?'}>${entry?.attrs ? ` ${JSON.stringify(entry.attrs)}` : ''}`];
  });
}

/**
 * The keys of one class, in the order the list above gives them.
 *
 * @param {keyof typeof KEY_CLASSES} name
 * @returns {readonly string[]}
 */
export function keysOfClass(name) {
  if (!Object.hasOwn(KEY_CLASSES, name)) throw new Error(`frontmatter keys: no class "${name}".`);
  return Object.freeze(Object.keys(FRONTMATTER_KEYS).filter((key) => FRONTMATTER_KEYS[key] === name));
}

/** A key at column 0 as YAML writes one: in double quotes, in single quotes, or bare (dotted included). */
const KEY = /^(?:"((?:[^"\\]|\\.)*)"|'((?:[^']|'')*)'|([A-Za-z_][\w.-]*))[ \t]*:(?=[ \t]|$)/;

/**
 * The top-level key a line of a frontmatter opens, as YAML reads it: bare
 * (`title:`, `og.image:`) or in quotes (`"sameAs":`, `'sameAs':`), the quotes
 * taken off. `null` for a line that opens none and continues the key above:
 * an indented line, a list item or a comment at column 0, a blank line. Any
 * other line at column 0 opens a key no reader here can name, and comes back
 * as written up to its `: ` (the whole line when it has none), so a class
 * check refuses it by name instead of the line passing as part of the key
 * above it.
 *
 * @param {string} line
 * @returns {string | null}
 */
export function topLevelKey(line) {
  if (line.trim() === '' || /^[ \t#]/.test(line) || /^-(?:[ \t]|$)/.test(line)) return null;
  const key = KEY.exec(line);
  if (key) {
    if (key[1] !== undefined) return JSON.parse(`"${key[1]}"`);
    if (key[2] !== undefined) return key[2].replaceAll("''", "'");
    return key[3];
  }
  const colon = /:(?=[ \t]|$)/.exec(line);
  return (colon ? line.slice(0, colon.index) : line).trim();
}

/**
 * The keys of `keys` the list above does not class, in their order.
 *
 * @param {Iterable<string>} keys
 * @returns {string[]}
 */
export function unclassifiedKeys(keys) {
  return [...keys].filter((key) => !Object.hasOwn(FRONTMATTER_KEYS, key));
}

/**
 * Throw, naming each key of `keys` the list above does not class.
 *
 * @param {Iterable<string>} keys
 * @param {string} where What holds the keys, for the message.
 */
export function refuseUnclassifiedKeys(keys, where) {
  const unknown = unclassifiedKeys(keys);
  if (unknown.length === 0) return;
  const named = unknown.map((key) => `"${key}"`).join(', ');
  throw new Error(
    `${where}: frontmatter key${unknown.length > 1 ? 's' : ''} ${named} ${unknown.length > 1 ? 'are' : 'is'} in no class. ` +
      'Add each to FRONTMATTER_KEYS in site/src/lib/frontmatter-keys.mjs as "content" (a change to it moves ' +
      'the date the page last changed), "label" (search snippets and navigation) or "metadata" (read by ' +
      'machines only, never shown).',
  );
}
