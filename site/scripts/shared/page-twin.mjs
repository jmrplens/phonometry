// The Markdown copy of a page that has no docs/ mirror, as the page shows it.
//
// emit-page-markdown.mjs publishes a Markdown copy beside every page. Where
// docs/ holds no mirror of the page (every Spanish page but the transplanted
// ones), the copy is the page's own source with its frontmatter and its MDX
// machinery taken out: its import and export statements and its component
// tags, a wrapper keeping its children. That machinery was found by patterns
// over the page as written, which read code as machinery too: the `import`
// line of a Python example went as the page's own import, a `<NC-15` written in
// a code span opened a component that ran to the next `/>`, and two blank lines
// of an example closed up. The page is read here as the site renders it
// (pageMarkup and pageParts of markdown-spans.mjs), so only what the page
// renders as markup goes, and what it shows as code stays as it shows it.
//
// What else the copy needs to read as the page does is written here too: the
// page's title, which its source keeps in the frontmatter; its comments taken
// out; a count the page prints from a data module, written as the number; a
// link the page writes from the site's root, made absolute so that it leads
// somewhere from a copy fetched on its own; a figure and a clip, written as an
// image and a line where the copy used to drop them with their text; and the
// References section the layout prints from the frontmatter.
//
// Nothing here imports a dependency, so the tests run before the install.

import { codeLines } from '../../src/lib/markdown-fences.mjs';
import { citationParts, noteParts, opening, sortedReferences } from '../../src/lib/references-format.mjs';
import { mediaUrl } from '../../src/lib/media.mjs';
import { frontmatterEnd, pageMarkup, pageParts } from './markdown-spans.mjs';

/** An import or an export statement of an `.mdx` page, on a line of its own. */
const ESM = /^(?:import|export)\s.*$/gm;

/** A component closed in its own tag: `<ThemeImage ... />`, `<Video ... />`. */
const SELF_CLOSING = /<[A-Z][\w.]*\b[^>]*\/>/g;

/** The opening or the closing tag of a component that wraps content. */
const WRAPPER = /<\/?[A-Z][\w.]*\b[^>]*>/g;

/**
 * A link the page writes from the site's root: the destination of a Markdown
 * link, or an `href` or `src` of a tag the page renders, that opens on one
 * slash. Two slashes open an address on another host, and stay.
 */
const ROOT_RELATIVE = /(\]\(|\b(?:href|src)=")\/(?!\/)/g;

/** An expression that prints one name: `{totalChecks}`. */
const NAME = /^\{\s*([A-Za-z_$][\w$]*)\s*\}$/;

/**
 * The page without its frontmatter, as Astro finds it, after a byte order mark
 * or blank lines too, and without the rest of the line its closing fence is on.
 *
 * @param {string} text The page as written.
 * @returns {string} What follows the frontmatter, or the page when it has none.
 */
export function stripFrontmatter(text) {
  const end = frontmatterEnd(text);
  if (end === 0) return text;
  const line = text.indexOf('\n', end);
  return line === -1 ? '' : text.slice(line + 1);
}

/**
 * The frontmatter of a page as written between its fences, for a YAML reader,
 * or `''` when the page has none.
 *
 * @param {string} text The page as written.
 * @returns {string}
 */
export function frontmatterSource(text) {
  const end = frontmatterEnd(text);
  if (end === 0) return '';
  const head = text.slice(0, end);
  const open = head.indexOf('\n');
  const close = head.lastIndexOf('\n');
  return close > open ? head.slice(open + 1, close + 1) : '';
}

/**
 * The names an `.mdx` page imports, each with the module it imports it from and
 * the name it has there: `import { totalChecks as checks } from '../x.mjs'`
 * gives `checks`, from `../x.mjs`, as `totalChecks`. Only the statements the
 * page renders as its own count, so an `import` line of a code example names
 * nothing.
 *
 * @param {string} text The page, its frontmatter out.
 * @returns {Map<string, { module: string, imported: string }>}
 */
export function pageImports(text) {
  const names = new Map();
  for (const found of pageMarkup(text, { kind: 'mdx' }).matchAll(ESM)) {
    const statement = text.slice(found.index, found.index + found[0].length);
    const named = statement.match(/^import\s*\{([^}]*)\}\s*from\s*(['"])([^'"]+)\2/);
    if (!named) continue;
    for (const piece of named[1].split(',')) {
      const [imported, local = imported] = piece.trim().split(/\s+as\s+/);
      if (imported) names.set(local, { module: named[3], imported });
    }
  }
  return names;
}

/**
 * The prose of a page with the MDX machinery that is noise as text taken out:
 * its import and export statements, its components closed in their own tag, and
 * the tags of the components that wrap content, whose children stay. Each is
 * taken out only where the page renders it as markup, so a tag or an `import`
 * line written in code stays. Its comments go too, an expression that prints a
 * name is written as the value `value` gives the name, and a link from the
 * site's root gets `origin` in front of it. A run of blank lines outside code
 * closes up to one; the blank lines of a code example stay.
 *
 * An expression `value` cannot write stops the copy: the page would print a
 * number where the copy prints the code that computes it.
 *
 * @param {string} text The page, its frontmatter out.
 * @param {{
 *   kind?: 'md' | 'mdx',
 *   expand?: (tag: string) => string | undefined,
 *   value?: (name: string) => string | number | undefined,
 *   origin?: string,
 *   firstLine?: number,
 * }} [options]
 *   The page's kind, an `.md` page having no import or export statement and no
 *   expression; what a component closed in its own tag is written out as, where
 *   it is not taken out; the value of a name the page prints; the scheme and
 *   host a link from the site's root is read against, none leaving it as it
 *   is; and the number of the page's line `text` opens on, for the message.
 * @returns {string} The prose, trimmed.
 */
export function stripMdx(
  text,
  { kind = 'mdx', expand = () => undefined, value = () => undefined, origin = '', firstLine = 1 } = {},
) {
  const shown = pageMarkup(text, { kind });
  const edits = [];
  const statements = [];
  if (kind === 'mdx') {
    for (const found of shown.matchAll(ESM)) statements.push([found.index, found.index + found[0].length]);
    for (const [start, end] of statements) edits.push([start, end, '']);
  }
  const inStatement = (at) => statements.some(([start, end]) => start <= at && at < end);
  for (const part of pageParts(text, { kind })) {
    if (part.what === 'comment') edits.push([part.start, part.end, '']);
    if (part.what !== 'expression' || inStatement(part.start)) continue;
    const written = text.slice(part.start, part.end);
    const name = NAME.exec(written)?.[1];
    const resolved = name === undefined ? undefined : value(name);
    if (resolved === undefined) {
      const line = text.slice(0, part.start).split('\n').length - 1 + firstLine;
      throw new Error(`line ${line} prints ${written}, which the Markdown copy cannot write as a value`);
    }
    edits.push([part.start, part.end, String(resolved)]);
  }
  for (const found of shown.matchAll(SELF_CLOSING)) {
    edits.push([found.index, found.index + found[0].length, expand(found[0]) ?? '']);
  }
  const taken = (at) => edits.some(([start, end]) => start <= at && at < end);
  for (const found of shown.matchAll(WRAPPER)) {
    if (!taken(found.index)) edits.push([found.index, found.index + found[0].length, '']);
  }
  if (origin) {
    for (const found of shown.matchAll(ROOT_RELATIVE)) {
      const at = found.index + found[1].length;
      if (!taken(at)) edits.push([at, at, origin]);
    }
  }
  edits.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  let kept = '';
  let done = 0;
  for (const [start, end, written] of edits) {
    if (start < done) continue;
    kept += text.slice(done, start) + written;
    done = end;
  }
  return closeUp(kept + text.slice(done), kind).trim();
}

/** `text` with each run of empty lines outside code closed up to one, on a page of `kind`. */
function closeUp(text, kind) {
  const lines = text.split('\n');
  const code = codeLines(lines, { kind });
  const blank = (index) => lines[index] === '' && !code[index];
  return lines.filter((_, index) => !(index > 0 && blank(index) && blank(index - 1))).join('\n');
}

/** Text on one line, each run of white space one space. */
const oneLine = (text) => text.replace(/\s+/g, ' ').trim();

/**
 * Text for the inside of `[...]`, a link's text or an image's alt: the
 * characters that would end it or open a table cell escaped.
 *
 * @param {string} text
 * @returns {string}
 */
export const bracketText = (text) => oneLine(text).replace(/([\\[\]|])/g, '\\$1');

/**
 * Plain text made safe to print as Markdown: the characters that would turn
 * part of it into emphasis, code, maths, a link or a tag escaped.
 *
 * @param {string} text
 * @returns {string}
 */
const plainText = (text) =>
  text
    .replace(/[ \t\n\v\f\r]+/g, ' ')
    .replace(/([\\`*~$[\]])/g, '\\$1')
    .replace(/<(?=[A-Za-z/!?])/g, '\\<');

/** One attribute of a component tag written as a string or as a number. */
function attribute(tag, name) {
  const found = tag.match(new RegExp(`\\b${name}=(?:"([^"]*)"|\\{\\s*(-?[\\d.]+)\\s*\\})`));
  return found ? (found[1] ?? found[2]) : undefined;
}

/** `figure.svg` with a suffix before its extension, as the components add one. */
const suffixed = (src, suffix) => src.replace(/(\.[A-Za-z0-9]+)$/, `${suffix}$1`);

/** Where Video.astro reads a clip from, by its name. */
const CLIPS = 'https://raw.githubusercontent.com/jmrplens/phonometry-assets/main/images';

/** Where ReportPreview.astro reads a fiche from, by its name. */
const FICHES = 'https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports';

/** The word the line of a clip and of a fiche opens with, in each language. */
const LEAD = { Video: { en: 'Video', es: 'Vídeo' }, ReportPreview: { en: 'Report', es: 'Informe' } };

/**
 * What the copy of a page written from its source does with each component a
 * page imports, besides the {@link DATA_COMPONENTS} of src/lib/page-markdown.mjs,
 * whose pages publish no copy: `written`, written out as Markdown here or by
 * the generator (the list of catalogues); `wrapper`, taken out with its
 * children kept, which are the page's own prose; `dropped`, taken out, being a
 * control or a script that shows nothing of its own (a picker over a table the
 * page also prints, a script that moves an old fragment to its new page).
 * scripts/page-markdown.test.mjs holds every component a page imports to one
 * of these, or to the data components, and each of them to a page.
 */
export const COMPONENT_READINGS = Object.freeze({
  CatalogueIndex: 'written',
  ReportPreview: 'written',
  ThemeImage: 'written',
  Video: 'written',
  Scope: 'wrapper',
  ScopeClaim: 'wrapper',
  SeeAlso: 'wrapper',
  CatalogueFinder: 'dropped',
  CatalogueRouter: 'dropped',
  ErrataRouter: 'dropped',
});

/**
 * A figure, a clip or a fiche as the copy writes it, or `undefined` for any
 * other tag.
 *
 * A figure (src/components/ThemeImage.astro) is an image: its alt, the text
 * written for a reader who cannot see it, and the address this site serves it
 * at, in the page's language as the component picks it, the light palette
 * alone. A clip (src/components/Video.astro) cannot be watched from text, and
 * a fiche (src/components/ReportPreview.astro) is a PDF, so each is a line:
 * its title linked to the clip or the PDF this site serves, then the
 * description written for a reader who cannot see it, and its caption, if it
 * has one, as a paragraph of its own. The italic caption a page writes under a
 * figure is prose and stays without help.
 *
 * @param {string} tag The tag as the page writes it.
 * @param {{ lang: 'en' | 'es', base: string }} where The page's language, and
 *   the address of the site the media are served under.
 * @returns {string | undefined}
 */
export function figureMarkdown(tag, { lang, base }) {
  const component = tag.match(/^<([A-Z][\w.]*)/)?.[1];
  if (component === 'ThemeImage') {
    const src = attribute(tag, 'src');
    const alt = attribute(tag, 'alt');
    if (!src || !alt) throw new Error(`a figure without its src or its alt: ${oneLine(tag)}`);
    const localised = lang === 'es' ? suffixed(src, '_es') : src;
    return `![${bracketText(alt)}](${mediaUrl(localised, base)})`;
  }
  if (component === 'Video' || component === 'ReportPreview') {
    const name = attribute(tag, 'name');
    const title = attribute(tag, 'title');
    if (!name || !title) throw new Error(`a clip or a fiche without its name or its title: ${oneLine(tag)}`);
    const url =
      component === 'Video'
        ? mediaUrl(`${CLIPS}/${name}${lang === 'es' ? '_es' : ''}.webm`, base)
        : mediaUrl(`${FICHES}/${name}.pdf`, base);
    const description = attribute(tag, 'description');
    const caption = attribute(tag, 'caption');
    const line = `**${LEAD[component][lang]}:** [${bracketText(title)}](${url})${description ? `: ${oneLine(description)}` : ''}`;
    return caption ? `${line}\n\n${oneLine(caption)}` : line;
  }
  return undefined;
}

/**
 * A link's destination as Markdown reads it: wrapped in `<...>` when it holds
 * a space or a parenthesis, which would end it early.
 */
const destination = (url) => (/[\s()<>]/.test(url) ? `<${url.replaceAll('<', '%3C').replaceAll('>', '%3E')}>` : url);

/** One fragment of a citation as Markdown: a bare URL stays bare, a title in italics, a link around what it carries. */
function partMarkdown(part) {
  if (part.href && part.text === part.href) return part.href;
  const text = plainText(part.text);
  const marked = part.italic && text.trim() ? `*${text}*` : text;
  return part.href ? `[${marked}](${destination(part.href)})` : marked;
}

/**
 * The References section of a page as its layout prints it
 * (src/components/References.astro), in the words of the same module
 * (src/lib/references-format.mjs): one item per entry in the order the page
 * prints them, its author and year in bold, its note on the line under it.
 *
 * @param {readonly import('../../src/lib/references-format.mjs').Reference[] | undefined} references
 *   The frontmatter's list.
 * @param {'en' | 'es'} lang
 * @param {string} heading The section's heading in the page's language.
 * @returns {string} Markdown, or `''` for a page that cites nothing.
 */
export function referencesMarkdown(references, lang, heading) {
  if (!references?.length) return '';
  const entries = sortedReferences(references, lang).map(([, ref]) => {
    const citation = citationParts(ref).map(partMarkdown).join('');
    const note = ref.note ? `\n  ${noteParts(ref.note).map(partMarkdown).join('').trim()}` : '';
    return `- **${plainText(opening(ref, lang))}**${citation.trimEnd()}${note}`;
  });
  return `## ${heading}\n\n${entries.join('\n')}`;
}

/**
 * What a copy written from a page's source misses of the page, one sentence
 * each, or nothing when it misses nothing.
 *
 * Each is read from the copy as written and from the source on its own, never
 * through the reading that wrote the copy, so a writer that goes wrong cannot
 * pass by agreeing with itself:
 *
 * - the copy opens with `# <title>`;
 * - it holds no comment, and no link from the site's root, outside its code;
 * - no name the page imports and prints is left in braces outside its code;
 * - every line of the page's code is in it, as many times as the page has it;
 * - a page that cites works ends with a section holding one entry per work,
 *   and every DOI among them.
 *
 * @param {string} copy The copy as written, without the lines above its title.
 * @param {{ source: string, kind: 'md' | 'mdx', title: string, references?: readonly { doi?: string }[], heading: string, firstLine?: number }} page
 *   The page's source with its frontmatter out, its kind, its title and the
 *   works it cites, the heading of its References section, and the number of
 *   the page's line `source` opens on, for the messages.
 * @returns {string[]}
 */
export function copyDefects(copy, { source, kind, title, references = [], heading, firstLine = 1 }) {
  const defects = [];
  const first = copy.slice(0, copy.indexOf('\n') === -1 ? copy.length : copy.indexOf('\n'));
  if (first !== `# ${title}`) defects.push(`it opens with ${JSON.stringify(first)}, not with the page's title`);
  const parts = pageParts(copy, { kind: 'md' });
  for (const part of parts.filter(({ what }) => what === 'comment')) {
    defects.push(`it keeps the comment ${JSON.stringify(oneLine(copy.slice(part.start, part.end)).slice(0, 80))}`);
  }
  const shown = pageMarkup(copy, { kind: 'md' });
  if (shown.includes('{/*')) defects.push('it keeps a comment of the page written as {/* */}');
  for (const found of shown.matchAll(ROOT_RELATIVE)) {
    defects.push(`it links ${JSON.stringify(copy.slice(found.index, found.index + 60).split('\n')[0])} from the site's root`);
  }
  if (kind === 'mdx') {
    for (const name of pageImports(source).keys()) {
      if (shown.includes(`{${name}}`)) defects.push(`it prints {${name}} where the page prints its value`);
    }
  }
  const sourceLines = source.split('\n');
  const code = codeLines(sourceLines, { kind });
  const kept = new Map();
  for (const line of copy.split('\n')) kept.set(line, (kept.get(line) ?? 0) + 1);
  for (const [index, line] of sourceLines.entries()) {
    if (!code[index] || line.trim() === '') continue;
    const left = kept.get(line) ?? 0;
    if (left === 0) {
      defects.push(`it lost line ${index + firstLine} of the page's code, ${JSON.stringify(line.trim().slice(0, 60))}`);
    }
    else kept.set(line, left - 1);
  }
  if (references.length) {
    const at = copy.indexOf(`\n## ${heading}\n`);
    const entries = at === -1 ? 0 : (copy.slice(at).match(/^- \*\*/gm) ?? []).length;
    if (entries !== references.length) {
      const works = `${references.length} work${references.length === 1 ? '' : 's'}`;
      defects.push(`its ${heading} section holds ${entries} entr${entries === 1 ? 'y' : 'ies'}, and the page cites ${works}`);
    }
    for (const { doi } of references) {
      if (doi && !copy.includes(`https://doi.org/${doi}`)) defects.push(`it leaves out the DOI ${doi}`);
    }
  }
  return defects;
}
