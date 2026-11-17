/**
 * Writes one page of the site as Markdown, from the same source the site
 * builds the page from.
 *
 * The design is jmrp.io's (`src/utils/llms/mdx/render.ts`, PR #417 there),
 * ported to this site's syntax.
 *
 * WHY A PARSER AND NOT A LINE SCANNER. The emitter this replaces walked the
 * text line by line with regular expressions. It could not tell an `import`
 * statement of the page from the `import numpy as np` of a Python example, so
 * every Spanish example lost its imports; it dropped every self-closing
 * component together with the data it showed; and it left `{expressions}`,
 * `:::` asides and raw HTML in the copy. A parser settles all of that by
 * construction: code is a `code` or `inlineCode` node, TeX is a `math` or
 * `inlineMath` node, and neither ever reaches the branch that rewrites
 * components.
 *
 * WHY THE SOURCE IS SLICED RATHER THAN RE-SERIALIZED. Every node carries its
 * byte offsets. Anything that is not a component is written by slicing the
 * original source, so prose, GFM tables, TeX and above all fenced code keep
 * their exact bytes; only the ranges of components (and of the few constructs
 * listed below) are replaced, right to left so the earlier offsets stay
 * valid. A Markdown serializer would have to round-trip all of that, and
 * every bug in it would corrupt a code sample or an equation.
 *
 * WHAT IS REPLACED, in order of precedence:
 *  - a component (`<ThemeImage .../>`), by the writer beside it
 *    (`ThemeImage.md.mjs`);
 *  - raw HTML the author wrote (`<details>`, `<sub>`, `<table>`, ...), by the
 *    rule table below;
 *  - a Starlight aside (`:::note[Title]`), by a bold localized label and its
 *    body, never a blockquote: an aside can hold a fenced block, and `> `
 *    would land inside the fence;
 *  - an `{expression}`, by its value when it is a literal or a name the page
 *    imports from an allow-listed data module, never by evaluating code;
 *  - imports, exports, `{/* comments *\/}`, HTML comments and the
 *    frontmatter, by nothing.
 *
 * WHAT IS NEVER SILENT. An element with no writer and no rule, a prop the
 * writer does not declare, a spread of props or attributes, an expression
 * that is neither a literal nor an allow-listed name (in text, in a prop, or
 * in an attribute of raw HTML), an aside type Starlight does not have: each
 * still renders (an unknown element as its children, never its own syntax),
 * and each is recorded as an issue. The coverage check fails on any issue, so
 * the fail-safe is unreachable for anything a page actually uses.
 *
 * @module
 */
import { existsSync } from 'node:fs';
import { dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { basePath, siteUrl } from '../../data/site.mjs';
import { readCommittedText } from '../line-ends.mjs';
import { codeLines } from '../markdown-fences.mjs';
import { MARKER } from '../bibliography-entries.mjs';
import { absolutizeRootLinks, pointDroppedAnchors } from './links.mjs';
import { escapeMarks, htmlAttribute, line, LINE_BREAK, plainText as plainMarkdown, resolveBreaks, table } from './markdown-table.mjs';
import { frontmatterOf, isMdx, parse } from './processor.mjs';
import { rewrittenSource } from './rewrites.mjs';

/** @typedef {import('./types.mjs').MdNode} MdNode */
/** @typedef {import('./types.mjs').MdAttribute} MdAttribute */
/** @typedef {import('./types.mjs').EstreeNode} EstreeNode */
/** @typedef {import('./types.mjs').RenderIssue} RenderIssue */
/** @typedef {import('./types.mjs').ComponentMarkdown} ComponentMarkdown */
/** @typedef {import('./types.mjs').MarkdownContext} MarkdownContext */

/** The site directory (`site/`), which every relative path below is from. */
export const SITE_DIR = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');

/** The repository root, where `docs/` and `assets.lock` live. */
export const REPO_DIR = resolve(SITE_DIR, '..');

/** Where the pages live. */
export const CONTENT_DIR = resolve(SITE_DIR, 'src', 'content', 'docs');

/**
 * The data modules a page may read a value from in an `{expression}` or a
 * prop. Anything else a page imports that is not a component is an error,
 * because the copy could only print it by running code it cannot trust or by
 * leaving a blank where the page shows a number.
 */
export const DATA_MODULES = Object.freeze(['src/data/conformance-stats.mjs', 'src/data/home.ts']);

/**
 * Where the site is published.
 *
 * @type {import('./types.mjs').SiteAddress}
 */
export const SITE = Object.freeze({
  origin: siteUrl,
  base: basePath,
  url(path) {
    if (/^[a-z][a-z0-9+.-]*:/i.test(path)) return path;
    if (path === basePath || path.startsWith(`${basePath}/`)) return `${siteUrl}${path}`;
    return `${siteUrl}${basePath}${path.startsWith('/') ? '' : '/'}${path}`;
  },
});

/** JSX elements, flow and inline. */
const ELEMENT_TYPES = new Set(['mdxJsxFlowElement', 'mdxJsxTextElement']);

/** MDX `{...}` nodes. */
const EXPRESSION_TYPES = new Set(['mdxFlowExpression', 'mdxTextExpression']);

/**
 * Nodes whose range is replaced rather than sliced, and whose descendants
 * are therefore handled when they themselves are written.
 */
const REPLACED_TYPES = new Set([
  ...ELEMENT_TYPES,
  ...EXPRESSION_TYPES,
  'mdxjsEsm',
  'containerDirective',
  'html',
  'yaml',
]);

/**
 * `inner` between two `mark`s, with any line break it opens or ends with
 * put outside them: a mark cannot close after a break (or open before one)
 * and still touch its text, so `<strong>a<br /></strong>b` is `**a**`, the
 * break, then `b`. The spacing and the line ends of the source on the far
 * side of such a break go out with it, since a mark that a line end or a
 * space parts from its text does not close (or open) either.
 *
 * @param {string} mark
 * @param {string} inner
 * @returns {string}
 */
function marked(mark, inner) {
  const edges = new RegExp(
    `^((?:[ \\t\\r\\n]*${LINE_BREAK}[ \\t\\r\\n]*)*)([\\s\\S]*?)((?:[ \\t\\r\\n]*${LINE_BREAK}[ \\t\\r\\n]*)*)$`,
    'u',
  ).exec(inner);
  const [, before = '', text = inner, after = ''] = edges ?? [];
  return `${before}${mark}${text}${mark}${after}`;
}

/**
 * Marks a code span cannot hold: inside `<code>` or `<kbd>` they are written
 * as the text they wrap.
 */
const CODE_DROPS_MARK = new Set(['emphasis', 'strong', 'delete']);

/** The HTML elements of those marks, written as their text there too. */
const CODE_DROPS_TAG = new Set(['em', 'i', 'strong', 'b', 'del', 's']);

/**
 * Node types that sit inside a paragraph rather than beside it.
 *
 * jmrp.io found that a shorter list split `<li>Uses **nonces** or
 * **hashes**</li>` into three paragraphs: children are joined with nothing
 * when every one of them is phrasing, and with a blank line otherwise, so
 * every phrasing type the parser can produce belongs here. `inlineMath` and
 * `textDirective` are this site's additions: the second is what the
 * directive parser makes of the `:2014` in `IEC 61260-1:2014`, which
 * Starlight writes back as the text it was.
 */
const INLINE_TYPES = new Set([
  'text',
  'inlineCode',
  'inlineMath',
  'mdxJsxTextElement',
  'mdxTextExpression',
  'strong',
  'emphasis',
  'delete',
  'link',
  'linkReference',
  'image',
  'imageReference',
  'break',
  'footnoteReference',
  'html',
  'textDirective',
]);

/**
 * The asides Starlight draws from `:::type`, with the label each language
 * prints for it (Starlight's own translations).
 */
export const ASIDES = Object.freeze({
  note: { en: 'Note', es: 'Nota' },
  tip: { en: 'Tip', es: 'Consejo' },
  caution: { en: 'Caution', es: 'Precaución' },
  danger: { en: 'Danger', es: 'Peligro' },
});

/**
 * The alert GitHub draws for each aside, in the GitHub edition: the same
 * four levels, Starlight's caution being GitHub's warning and its danger
 * GitHub's caution.
 */
const GITHUB_ALERTS = Object.freeze({ note: 'NOTE', tip: 'TIP', caution: 'WARNING', danger: 'CAUTION' });

/**
 * Raw HTML tags that are blocks: written inline (inside a paragraph, as MDX
 * parses `<div><table>...` on one line), their Markdown still has to stand
 * apart from what surrounds it, or a table runs into the next sentence.
 */
const BLOCK_TAGS = new Set(['details', 'div', 'table']);

/** Raw HTML tags with a rule below; anything else is an issue. */
export const HTML_TAGS = Object.freeze([
  'a',
  'abbr',
  'b',
  'br',
  'caption',
  'code',
  'del',
  'details',
  'div',
  'em',
  'i',
  'kbd',
  'mark',
  's',
  'small',
  'span',
  'strong',
  'sub',
  'summary',
  'sup',
  'table',
  'tbody',
  'td',
  'tfoot',
  'th',
  'thead',
  'tr',
  'wbr',
]);

/**
 * Deepest heading Markdown has. `#######` is not a heading in any parser but
 * a paragraph that starts with seven hashes, so a writer that nests a heading
 * too deep would otherwise turn a title into body text without any error.
 */
const MAX_HEADING_DEPTH = 6;

/** What `evaluate` returns for anything it will not read. */
const UNREAD = Symbol('unread');

/**
 * An inline code span around `text`, with a fence one backtick longer than
 * the longest run inside it, so a backtick in the content cannot close it.
 *
 * @param {string} text
 * @returns {string}
 */
export function codeSpan(text) {
  const runs = text.match(/`+/g) ?? [];
  const fence = '`'.repeat(Math.max(0, ...runs.map((run) => run.length)) + 1);
  const pad = text.startsWith('`') || text.endsWith('`') ? ' ' : '';
  return `${fence}${pad}${text}${pad}${fence}`;
}

/**
 * Removes the indentation a block inherited from the component around it.
 *
 * A slice starts at the node's first character, so the first line arrives
 * with no indent while the following lines keep what they had inside the
 * component, which turns a flat list into a nested one. Restoring the first
 * line's indent and then removing the common minimum fixes that and keeps
 * the indentation that is structure (a nested list, the body of a fence).
 *
 * @param {string} text
 * @param {number} column  1-based column the node started at.
 * @returns {string}
 */
function dedent(text, column) {
  const restored = column > 1 ? ' '.repeat(column - 1) + text : text;
  const lines = restored.split('\n');
  let min = Infinity;
  for (const one of lines) {
    if (one.trim() === '') continue;
    min = Math.min(min, /^ */u.exec(one)?.[0].length ?? 0);
  }
  if (!Number.isFinite(min) || min === 0) return restored;
  return lines.map((one) => one.slice(min)).join('\n');
}

/** A line indented as a line of indented code is: four spaces or a tab. */
const INDENTED = /^(?: {4}|\t)/u;

/**
 * Runs of blank lines collapsed to one, outside code.
 *
 * Inside a fence a blank line is content: two of them between two Python
 * functions are what PEP 8 asks for, and a copy must not change the bytes of
 * an example. So is a run between two indented lines, which indented code
 * holds the same way (a triple-quoted string with two blank lines in it).
 *
 * @param {string} text
 * @returns {string}
 */
function collapseBlankRuns(text) {
  const lines = text.split('\n');
  const code = codeLines(lines);
  const blank = (at) => !code[at] && lines[at].trim() === '';
  /** @type {string[]} */
  const out = [];
  lines.forEach((one, at) => {
    if (blank(at) && out.length > 0 && out.at(-1)?.trim() === '') {
      let next = at;
      while (next < lines.length && blank(next)) next += 1;
      let before = at;
      while (before >= 0 && blank(before)) before -= 1;
      const insideIndentedCode = before >= 0 && next < lines.length && INDENTED.test(lines[before]) && INDENTED.test(lines[next]);
      if (!insideIndentedCode) return;
    }
    out.push(one);
  });
  return out.join('\n');
}

/**
 * The one expression a program attached by remark-mdx consists of.
 *
 * @param {EstreeNode | undefined} program
 * @returns {EstreeNode | undefined}
 */
function soleExpression(program) {
  const body = program?.body ?? [];
  return body.length === 1 && body[0].type === 'ExpressionStatement' ? body[0].expression : undefined;
}

/**
 * Reads a value from an ESTree without evaluating anything.
 *
 * Props are hand-written JavaScript literals (unquoted keys, single quotes,
 * template strings), so `JSON.parse` cannot read them, and `new Function`
 * would run whatever it is handed. remark-mdx has already parsed every
 * expression into an ESTree; walking it and accepting only literal forms and
 * names bound by an allow-listed import gives the value with no evaluation
 * at all.
 *
 * @param {EstreeNode | null | undefined} node
 * @param {Map<string, unknown>} scope  Names bound by allow-listed imports.
 * @returns {unknown}  The value, or {@link UNREAD}.
 */
function evaluate(node, scope) {
  if (!node) return UNREAD;
  switch (node.type) {
    case 'Literal':
      return node.value;
    case 'TemplateLiteral':
      return (node.expressions ?? []).length > 0
        ? UNREAD
        : (node.quasis ?? []).map((quasi) => quasi.value?.cooked ?? '').join('');
    case 'UnaryExpression': {
      const value = evaluate(node.argument, scope);
      if (typeof value !== 'number') return UNREAD;
      if (node.operator === '-') return -value;
      return node.operator === '+' ? value : UNREAD;
    }
    case 'ArrayExpression': {
      const values = (node.elements ?? []).map((element) => evaluate(element, scope));
      return values.includes(UNREAD) ? UNREAD : values;
    }
    case 'ObjectExpression': {
      /** @type {Record<string, unknown>} */
      const out = {};
      for (const property of node.properties ?? []) {
        if (property.type !== 'Property' || property.computed) return UNREAD;
        const key = property.key?.type === 'Identifier' ? property.key.name : property.key?.value;
        const value = evaluate(property.value, scope);
        if (typeof key !== 'string' && typeof key !== 'number') return UNREAD;
        if (value === UNREAD) return UNREAD;
        out[String(key)] = value;
      }
      return out;
    }
    case 'Identifier':
      return node.name !== undefined && scope.has(node.name) ? scope.get(node.name) : UNREAD;
    case 'MemberExpression': {
      const object = evaluate(node.object, scope);
      if (object === UNREAD || object === null || typeof object !== 'object') return UNREAD;
      const key = node.computed ? evaluate(node.property, scope) : node.property?.name;
      if (typeof key !== 'string' && typeof key !== 'number') return UNREAD;
      return Object.hasOwn(object, key) ? /** @type {Record<string, unknown>} */ (object)[key] : UNREAD;
    }
    default:
      return UNREAD;
  }
}

/**
 * Builds the renderer for one source text.
 *
 * @param {string} source
 * @param {RenderOptions} options
 * @param {{ fragment: boolean }} mode  A fragment is a string a writer hands
 *   back through `ctx.markdown`; its line numbers are not the page's.
 */
function createRenderer(source, options, mode) {
  const { registry, scope, issues, lang, flavour, frontmatter, droppedAnchors } = options;

  /**
   * How many `<code>` or `<kbd>` elements the node being written sits in: a
   * string expression there is code, printed as it is, never escaped.
   */
  let codeDepth = 0;

  /**
   * The children of a code element, written with {@link codeDepth} raised.
   *
   * @param {MdNode} node
   * @returns {string}
   */
  const codeChildren = (node) => {
    codeDepth += 1;
    try {
      return renderChildren(node);
    } finally {
      codeDepth -= 1;
    }
  };

  /**
   * @param {RenderIssue['kind']} kind
   * @param {MdNode | undefined} node
   * @param {string} message
   */
  const report = (kind, node, message) => {
    issues.push({
      kind,
      message,
      ...(mode.fragment || !node?.position ? {} : { line: node.position.start.line }),
    });
  };

  /** @param {MdNode} node */
  const slice = (node) => {
    const start = node.position?.start.offset;
    const end = node.position?.end.offset;
    return start === undefined || end === undefined ? '' : source.slice(start, end);
  };

  /**
   * The attribute called `name`, if the element has one.
   *
   * @param {MdNode} node
   * @param {string} name
   */
  const attribute = (node, name) =>
    (node.attributes ?? []).find((one) => one.type === 'mdxJsxAttribute' && one.name === name);

  /**
   * What one attribute reads as: a string as written, `true` for a bare
   * attribute, or the value of its expression.
   *
   * @param {MdAttribute} one
   * @returns {unknown}  The value, or UNREAD.
   */
  const readAttribute = (one) => {
    const { value } = one;
    if (value === null || value === undefined) return true;
    if (typeof value === 'string') return value;
    return evaluate(soleExpression(value.data?.estree), scope);
  };

  /**
   * The value of the attribute called `name`.
   *
   * @param {MdNode} node
   * @param {string} name
   * @returns {unknown}  The value, `undefined` when absent, or UNREAD.
   */
  const attributeValue = (node, name) => {
    const found = attribute(node, name);
    return found ? readAttribute(found) : undefined;
  };

  /** @type {MarkdownContext} */
  const ctx = {
    lang,
    flavour,
    site: SITE,
    frontmatter,
    attr(node, name) {
      const value = attributeValue(node, name);
      if (typeof value === 'string') return value;
      return typeof value === 'number' ? String(value) : undefined;
    },
    flag(node, name) {
      const value = attributeValue(node, name);
      return value === true || value === 'true';
    },
    expr(node, name) {
      const value = attributeValue(node, name);
      return value === UNREAD ? undefined : value;
    },
    body: (node) => renderChildren(node),
    text: (node) => line(plainText(node)),
    render: (node) => renderNode(node),
    markdown(fragment) {
      let tree;
      try {
        tree = parse(fragment, { mdx: true });
      } catch (error) {
        report('writer', undefined, `a data string does not parse as MDX (${error.message}): ${line(fragment).slice(0, 80)}`);
        // Written as text, every mark escaped (markdown-table.mjs, `plainText`):
        // a `<` that could open a tag gets a backslash, so no markup survives,
        // and the issue above still fails the check.
        return plainMarkdown(fragment);
      }
      return createRenderer(fragment, options, { fragment: true }).renderRoot(tree);
    },
    heading(depth, text) {
      return `${'#'.repeat(Math.min(MAX_HEADING_DEPTH, Math.max(1, depth)))} ${text}`;
    },
    issue(node, message) {
      report('writer', node, message);
    },
  };

  /**
   * Visible text of a subtree, markup dropped.
   *
   * @param {MdNode} node
   * @returns {string}
   */
  function plainText(node) {
    if (node.type === 'text' || node.type === 'inlineCode' || node.type === 'code') return node.value ?? '';
    if (node.type === 'inlineMath') return `$${node.value ?? ''}$`;
    if (EXPRESSION_TYPES.has(node.type)) return renderExpression(node);
    return (node.children ?? []).map(plainText).join('');
  }

  /**
   * Text of a subtree with a space between the parts of different elements,
   * for a label assembled from several tags (`<strong>A</strong><span>B</span>`
   * must read "A B", not "AB").
   *
   * @param {MdNode} node
   * @returns {string}
   */
  function spacedText(node) {
    if (ELEMENT_TYPES.has(node.type)) return ` ${(node.children ?? []).map(spacedText).join('')} `;
    if (node.children) return node.children.map(spacedText).join('');
    return plainText(node);
  }

  /**
   * Every descendant that is replaced, outermost first, without entering it.
   *
   * @param {MdNode} node
   * @returns {MdNode[]}
   */
  function replacedDescendants(node) {
    /** @type {MdNode[]} */
    const found = [];
    const walk = (current) => {
      for (const child of current.children ?? []) {
        if (REPLACED_TYPES.has(child.type)) found.push(child);
        else walk(child);
      }
    };
    walk(node);
    return found;
  }

  /**
   * A node written by slicing its source and replacing only what is nested in
   * it that has to be replaced, right to left so earlier offsets hold.
   *
   * @param {MdNode} node
   * @param {{ dedented?: boolean }} [options]  `dedented: false` for a node at
   *   the top of the page, which inherited no indentation from a component.
   * @returns {string}
   */
  function renderWithSubstitutions(node, { dedented = true } = {}) {
    const base = node.position?.start.offset;
    if (base === undefined) return '';
    let out = slice(node);
    for (const inner of replacedDescendants(node).toReversed()) {
      const start = inner.position?.start.offset;
      const end = inner.position?.end.offset;
      if (start === undefined || end === undefined) continue;
      out = out.slice(0, start - base) + renderNode(inner) + out.slice(end - base);
    }
    // Only a flow node inside a component is dedented. An inline node starts
    // mid-line, so its column is an offset into a sentence, not indentation,
    // and restoring it as spaces would strip the space before `or` in
    // `**a** or **b**`. A node at the top of the page inherited no indentation
    // from anything: there the indentation is the author's, and an indented
    // code block of a `.md` page would turn into a paragraph without it.
    // At the top, the first line's own indentation is put back: a slice starts
    // after it, and a `$$` indented like its closing fence must stay so, or
    // the TeX between them changes.
    if (INLINE_TYPES.has(node.type)) return out;
    const column = node.position?.start.column ?? 1;
    if (!dedented) return column > 1 ? ' '.repeat(column - 1) + out : out;
    return dedent(out, column);
  }

  /**
   * An `{expression}`: its literal value, a name the page imports from an
   * allow-listed data module, or nothing for a `{/* comment *\/}`.
   *
   * @param {MdNode} node
   * @returns {string}
   */
  function renderExpression(node) {
    const program = node.data?.estree;
    if (program && (program.body ?? []).length === 0) return '';
    const value = evaluate(soleExpression(program), scope);
    // A string prints as the page prints it: its marks escaped, so that
    // `{"*a*"}` is not emphasis in the copy, but its spaces kept, so that
    // `{" "}` stays the space between two words. Inside code it is code.
    if (typeof value === 'string') return codeDepth > 0 ? value : escapeMarks(value, { pipe: false });
    if (typeof value === 'number' && Number.isFinite(value)) return String(value);
    report(
      'expression',
      node,
      `{${line(node.value)}} is neither a literal nor a value imported from ${DATA_MODULES.join(' or ')}`,
    );
    return '';
  }

  /**
   * A Starlight aside: the localized label, its title if any, then the body.
   * In the GitHub edition, the alert GitHub draws for it (`> [!NOTE]`), every
   * line of the title and the body quoted under it, a fenced block included,
   * which GitHub reads inside the quote as it should.
   *
   * @param {MdNode} node
   * @returns {string}
   */
  function renderAside(node) {
    const labels = ASIDES[/** @type {keyof typeof ASIDES} */ (node.name ?? '')];
    if (!labels) {
      report('directive', node, `:::${node.name} is not an aside Starlight draws (${Object.keys(ASIDES).join(', ')})`);
      return renderWithSubstitutions(node);
    }
    const children = node.children ?? [];
    const titled = children[0]?.data?.directiveLabel === true;
    const title = titled ? renderChildren(children[0]).trim() : '';
    const body = joinFlow(titled ? children.slice(1) : children);
    if (flavour === 'github') {
      const inner = [title && `**${title}**`, body].filter(Boolean).join('\n\n');
      const lines = [`[!${GITHUB_ALERTS[/** @type {keyof typeof GITHUB_ALERTS} */ (node.name)]}]`, ...inner.split('\n')];
      return lines.map((one) => (one ? `> ${one}` : '>')).join('\n');
    }
    const label = title ? `**${labels[lang]}: ${title}**` : `**${labels[lang]}**`;
    return body ? `${label}\n\n${body}` : label;
  }

  /**
   * Raw HTML in a `.md` page: a comment is dropped, anything else is kept as
   * written and reported, because no rule covers it. A comment that marks
   * where a plugin writes a list, `<!-- bibliography: <area> -->`, is dropped
   * and reported: the page shows a list there, and a marker that reaches the
   * renderer is one no rule of ./rewrites.mjs wrote.
   *
   * @param {MdNode} node
   * @returns {string}
   */
  function renderHtml(node) {
    const value = node.value ?? '';
    if (MARKER.test(value.trim())) {
      report('html', node, `a bibliography marker no rule wrote, where the page shows a list: ${line(value).slice(0, 60)}`);
      return '';
    }
    if (/^\s*<!--[\s\S]*-->\s*$/u.test(value)) return '';
    report('html', node, `raw HTML in a Markdown page has no rule: ${line(value).slice(0, 60)}`);
    return value;
  }

  /**
   * Checks every attribute of an element: a spread cannot be read at all, a
   * component's prop must be one its writer declares, and an expression must
   * be a literal or an allow-listed name.
   *
   * Components and raw HTML go through this one walk. Raw HTML used to skip
   * it: `<a href={x}>` reached the `a` rule with an href it could not read,
   * which the rule took for an absent one, so the link was dropped and
   * nothing was recorded.
   *
   * @param {MdNode} node
   * @param {{ tag: string, reader: string, props?: readonly string[] }} owner
   *   What writes the element: a component's writer, with the props it
   *   declares, or the rules of this file for raw HTML, which may carry any
   *   attribute.
   */
  function checkAttributes(node, { tag, reader, props }) {
    for (const one of node.attributes ?? []) {
      if (one.type !== 'mdxJsxAttribute') {
        report('prop', node, `<${tag}> spreads ${props ? 'props' : 'attributes'}, which ${reader} cannot read`);
        continue;
      }
      if (props && !props.includes(one.name ?? '')) {
        report('prop', node, `<${tag}> passes "${one.name}", which ${reader} does not declare`);
        continue;
      }
      if (readAttribute(one) === UNREAD) {
        report('expression', node, `<${tag} ${one.name}={...}> is neither a literal nor a value imported from ${DATA_MODULES.join(' or ')}`);
      }
    }
  }

  /**
   * The checks {@link renderElement} makes of an element, for an element a
   * rule consumes without writing it through that path (a table's rows and
   * cells, its caption, a summary): a component with no writer, a tag with no
   * rule, a spread, an undeclared prop and an unreadable expression are each
   * reported here as anywhere else.
   *
   * @param {MdNode} node
   */
  function checkElement(node) {
    const name = node.name ?? '';
    if (!name) return;
    const spec = registry.get(name);
    if (spec) {
      checkAttributes(node, { tag: spec.tag, reader: `${spec.tag}.md.mjs`, props: spec.props });
      return;
    }
    if (/^[A-Z]/.test(name)) {
      report('component', node, `<${name}> has no Markdown writer: add ${name}.md.mjs beside the component`);
      return;
    }
    checkAttributes(node, { tag: name, reader: 'agent-md/render.mjs' });
    if (!Object.hasOwn(HTML_RULES, name)) report('html', node, `<${name}> is raw HTML with no rule in agent-md/render.mjs`);
  }

  /**
   * A caption's text on one line, the parts of its elements spaced apart
   * (`<strong>A</strong><span>B</span>` reads "A B"), every element in it
   * checked as {@link checkElement} checks one.
   *
   * @param {MdNode} node
   * @returns {string}
   */
  function captionText(node) {
    const walk = (current) => {
      for (const child of current.children ?? []) {
        if (ELEMENT_TYPES.has(child.type)) checkElement(child);
        walk(child);
      }
    };
    walk(node);
    return line(spacedText(node));
  }

  /**
   * A raw `<table>`: a Markdown table under its caption in bold.
   *
   * @param {MdNode} node
   * @returns {string}
   */
  function renderTable(node) {
    /** @type {MdNode[][]} */
    const rows = [];
    let caption = '';
    const visit = (current) => {
      for (const child of current.children ?? []) {
        if (!ELEMENT_TYPES.has(child.type)) {
          visit(child);
          continue;
        }
        checkElement(child);
        if (child.name === 'caption') caption = captionText(child);
        else if (child.name === 'tr') {
          /** @type {MdNode[]} */
          const row = [];
          for (const one of child.children ?? []) {
            if (!ELEMENT_TYPES.has(one.type)) continue;
            checkElement(one);
            if (one.name === 'td' || one.name === 'th') row.push(one);
            else if (Object.hasOwn(HTML_RULES, one.name ?? '')) {
              report('html', one, `<${one.name}> sits in a <tr> outside any cell, and a Markdown table has nowhere to put it`);
            }
          }
          rows.push(row);
        } else visit(child);
      }
    };
    visit(node);
    const cells = rows.map((row) => row.map((one) => renderChildren(one)));
    if (cells.length === 0) return caption ? `**${caption}**` : '';
    // The first row heads the table, whether or not the author put it in a
    // <thead>: a Markdown table cannot have a body without a header.
    const width = Math.max(...cells.map((row) => row.length));
    const head = Array.from({ length: width }, (_, i) => cells[0][i] ?? '');
    const grid = table(head, cells.slice(1));
    return caption ? `**${caption}**\n\n${grid}` : grid;
  }

  /**
   * `<details>`: the summary in bold, then the body, which a reader without
   * a viewport reads whole. The GitHub edition keeps the collapsible, which
   * GitHub draws closed as the site does, with the body written as Markdown
   * inside it (a blank line after `<summary>` lets GitHub read it as such):
   * the code of a figure stays one click away instead of between the figure
   * and the next paragraph.
   *
   * @param {MdNode} node
   * @returns {string}
   */
  function renderDetails(node) {
    let summary = '';
    /** @type {string[]} */
    const parts = [];
    for (const child of node.children ?? []) {
      // The summary is a flow child, or, as MDX parses the figure-code
      // blocks of the guides, an inline element inside the first paragraph.
      const found =
        child.name === 'summary'
          ? child
          : child.type === 'paragraph'
            ? (child.children ?? []).find((c) => c.name === 'summary')
            : undefined;
      if (!summary && found) {
        checkElement(found);
        summary = line(renderChildren(found));
        if (found !== child) {
          const others = (child.children ?? []).filter((c) => c !== found);
          parts.push(others.map((c) => renderNode(c)).join('').trim());
        }
        continue;
      }
      parts.push(renderNode(child));
    }
    const body = parts.filter((part) => part.trim() !== '').join('\n\n');
    if (flavour === 'github' && summary) {
      return `<details>\n<summary>${summary}</summary>\n\n${body}\n\n</details>`;
    }
    if (!summary) return body;
    return body ? `**${summary}**\n\n${body}` : `**${summary}**`;
  }

  /**
   * Raw HTML the author wrote inside an MDX page.
   *
   * These are not components, so there is no `.astro` to put a writer beside
   * and the rules live here. The correctness one is `<sup>`: without it,
   * `10<sup>4</sup>` would read "104", which is not a lost nuance but a false
   * magnitude.
   *
   * @type {Record<string, (node: MdNode) => string>}
   */
  const HTML_RULES = {
    a(node) {
      const inner = renderChildren(node);
      const href = ctx.attr(node, 'href');
      return href && inner ? `[${inner}](${href})` : inner;
    },
    abbr: (node) => renderChildren(node),
    b: (node) => marked('**', renderChildren(node)),
    // A bare line end inside a paragraph is a space to a Markdown reader, so
    // the break is held as LINE_BREAK until the copy is whole, and then made
    // the backslash CommonMark and GitHub both draw, or dropped where its
    // paragraph ends (resolveBreaks, markdown-table.mjs). Inside a code span a
    // backslash is text, so there the break is the line end it always was.
    br: () => (codeDepth > 0 ? '\n' : LINE_BREAK),
    caption: (node) => `**${captionText(node)}**`,
    code: (node) => codeSpan(codeChildren(node)),
    del: (node) => marked('~~', renderChildren(node)),
    details: renderDetails,
    div: (node) => renderChildren(node),
    em: (node) => marked('*', renderChildren(node)),
    i: (node) => marked('*', renderChildren(node)),
    kbd: (node) => codeSpan(codeChildren(node)),
    mark: (node) => renderChildren(node),
    s: (node) => marked('~~', renderChildren(node)),
    small: (node) => renderChildren(node),
    // An empty `<span id>` is an anchor kept for old links (F13): it has no
    // text, and a Markdown copy has no anchors to keep. The GitHub edition
    // keeps it as the `<a id>` GitHub honours, so a link to it from another
    // page of the edition lands where it lands on the site; the agent copy
    // records its id, so a link to it can be sent to the page, where the
    // anchor still is.
    span(node) {
      const id = ctx.attr(node, 'id');
      const inner = renderChildren(node);
      if (flavour === 'github' && id && !inner.trim()) return `<a id="${htmlAttribute(id)}"></a>`;
      if (id && (node.children ?? []).length === 0) droppedAnchors?.add(id);
      return inner;
    },
    strong: (node) => marked('**', renderChildren(node)),
    // GitHub draws both, so the GitHub edition keeps them as the page has them.
    sub: (node) => (flavour === 'github' ? `<sub>${renderChildren(node)}</sub>` : `_${renderChildren(node)}`),
    summary: (node) => `**${line(renderChildren(node))}**`,
    // Markdown has no superscript; `^` is the plain-text notation for one, and
    // it keeps the exponent attached to its base.
    sup: (node) => (flavour === 'github' ? `<sup>${renderChildren(node)}</sup>` : `^${renderChildren(node)}`),
    table: renderTable,
    tbody: (node) => renderChildren(node),
    td: (node) => renderChildren(node),
    tfoot: (node) => renderChildren(node),
    th: (node) => renderChildren(node),
    thead: (node) => renderChildren(node),
    tr: (node) => renderChildren(node),
    wbr: () => '',
  };

  /**
   * An element: its writer, its rule, or its children.
   *
   * @param {MdNode} node
   * @returns {string}
   */
  function renderElement(node) {
    const name = node.name ?? '';
    if (!name) return renderChildren(node);
    const spec = registry.get(name);
    if (spec) {
      checkAttributes(node, { tag: spec.tag, reader: `${spec.tag}.md.mjs`, props: spec.props });
      try {
        const written = spec.toMarkdown(node, ctx);
        if (typeof written === 'string') return written;
        report('writer', node, `${name}.md.mjs returned ${typeof written}, not a string`);
        return '';
      } catch (error) {
        report('writer', node, `${name}.md.mjs threw: ${error.message}`);
        return renderChildren(node);
      }
    }
    if (/^[A-Z]/.test(name)) {
      report('component', node, `<${name}> has no Markdown writer: add ${name}.md.mjs beside the component`);
      return renderChildren(node);
    }
    checkAttributes(node, { tag: name, reader: 'agent-md/render.mjs' });
    const rule = Object.hasOwn(HTML_RULES, name) ? HTML_RULES[name] : undefined;
    if (rule) {
      const written = rule(node);
      return node.type === 'mdxJsxTextElement' && BLOCK_TAGS.has(name) ? `\n\n${written}\n\n` : written;
    }
    report('html', node, `<${name}> is raw HTML with no rule in agent-md/render.mjs`);
    return renderChildren(node);
  }

  /**
   * @param {MdNode} node
   * @param {{ dedented?: boolean }} [options]  Passed on to the slicer.
   * @returns {string}
   */
  function renderNode(node, options) {
    if (node.type === 'yaml' || node.type === 'mdxjsEsm') return '';
    if (codeDepth > 0) {
      // Between backticks every character reads as it stands, so the text of
      // a `<code>` or `<kbd>` is what the page shows: `&lt;` written as `<`,
      // `\*` as `*`, and a mark, which a code span cannot carry, as its text.
      if (node.type === 'text' || node.type === 'inlineCode') return node.value ?? '';
      if (CODE_DROPS_MARK.has(node.type)) return renderChildren(node);
      if (ELEMENT_TYPES.has(node.type) && CODE_DROPS_TAG.has(node.name)) {
        checkElement(node);
        return renderChildren(node);
      }
    }
    if (EXPRESSION_TYPES.has(node.type)) return renderExpression(node);
    if (ELEMENT_TYPES.has(node.type)) return renderElement(node);
    if (node.type === 'containerDirective') return renderAside(node);
    if (node.type === 'html') return renderHtml(node);
    return renderWithSubstitutions(node, options);
  }

  /**
   * Flow nodes, written and separated by a blank line.
   *
   * @param {MdNode[]} nodes
   * @param {{ dedented?: boolean }} [options]
   * @returns {string}
   */
  function joinFlow(nodes, options) {
    return nodes
      .map((child) => renderNode(child, options))
      .filter((part) => part.trim() !== '')
      .join('\n\n');
  }

  /**
   * The children of a node: joined with nothing when every one is phrasing,
   * with a blank line otherwise.
   *
   * @param {MdNode} node
   * @returns {string}
   */
  function renderChildren(node) {
    const children = node.children ?? [];
    const inline = children.length > 0 && children.every((child) => INLINE_TYPES.has(child.type));
    if (!inline) return joinFlow(children, { dedented: node.type !== 'root' });
    return children.map((child) => renderNode(child)).join('');
  }

  /**
   * The written text without what surrounds it: a fragment a writer hands
   * back trimmed whole, a page only of its leading blank lines and its
   * trailing blanks, since the indentation of its first line can be
   * structure (an indented code block that opens a `.md` page).
   *
   * @param {string} text
   * @returns {string}
   */
  const outerTrim = (text) => (mode.fragment ? text.trim() : text.replace(/^(?:[ \t]*\n)+/u, '').trimEnd());

  return {
    ctx,
    /**
     * @param {MdNode} tree
     * @param {(block: string) => string} [eachBlock]  Applied to what each
     *   top-level node is written as, before the blocks are joined.
     * @returns {string}
     */
    renderRoot(tree, eachBlock) {
      const children = tree.children ?? [];
      const inline = children.length > 0 && children.every((child) => INLINE_TYPES.has(child.type));
      if (!eachBlock || inline) {
        const whole = renderChildren(tree);
        return outerTrim(collapseBlankRuns(eachBlock ? eachBlock(whole) : whole));
      }
      const blocks = children
        .map((child) => renderNode(child, { dedented: false }))
        .filter((part) => part.trim() !== '')
        .map(eachBlock);
      return outerTrim(collapseBlankRuns(blocks.join('\n\n')));
    },
  };
}

/**
 * @typedef {object} RenderOptions
 * @property {Map<string, ComponentMarkdown>} registry  Tag to writer.
 * @property {'en' | 'es'} lang
 * @property {'agent' | 'github'} flavour
 * @property {Map<string, unknown>} scope  Names bound by allow-listed imports.
 * @property {RenderIssue[]} issues  Collects what could not be written.
 * @property {Record<string, unknown>} frontmatter  The page's frontmatter.
 * @property {Set<string>} [droppedAnchors]  The ids of the empty anchors the
 *   copy leaves out, gathered while it is written.
 * @property {string} [pageUrl]  The page's address on the site, where a link
 *   to an anchor the copy leaves out is sent.
 */

/**
 * Writes a parsed page as Markdown.
 *
 * @param {MdNode} tree  From `processor.parse`.
 * @param {string} source  The text the tree was parsed from.
 * @param {Partial<RenderOptions> & { registry: Map<string, ComponentMarkdown> }} options
 * @returns {string}  The body, ending with one newline.
 */
export function renderTree(tree, source, options) {
  /** @type {RenderOptions} */
  const full = {
    lang: 'en',
    flavour: 'agent',
    scope: new Map(),
    issues: [],
    frontmatter: frontmatterOf(tree),
    ...options,
    droppedAnchors: new Set(),
  };
  // Links are made absolute block by block: no link crosses from one
  // top-level block into the next, and a block that holds none (the
  // conformance report's hundreds of kilobytes of tables) is then never
  // parsed again for links (links.mjs says why that matters).
  const written = resolveBreaks(
    createRenderer(source, full, { fragment: false }).renderRoot(tree, (block) => absolutizeRootLinks(block, SITE.origin)),
  );
  // A link to an anchor only an empty span carried leads nowhere in the copy,
  // which leaves the span out: it goes to the page, where the span still is.
  // The GitHub edition keeps such anchors, so this is the agent copy's alone.
  const body =
    full.flavour === 'agent' && full.pageUrl
      ? pointDroppedAnchors(written, full.droppedAnchors ?? new Set(), full.pageUrl)
      : written;
  return `${body}\n`;
}

/**
 * Parses and writes a source string. The page's imports are not read, so a
 * name in an expression resolves only through `options.scope`.
 *
 * @param {string} source
 * @param {Partial<RenderOptions> & { registry: Map<string, ComponentMarkdown>, mdx?: boolean }} options
 * @returns {string}
 */
export function renderMarkdown(source, options) {
  const { mdx = true, ...rest } = options;
  return renderTree(parse(source, { mdx }), source, rest);
}

/**
 * The language of a content file, from its path.
 *
 * @param {string} file  Absolute, or relative to the content directory.
 * @returns {'en' | 'es'}
 */
export function langOf(file) {
  const path = (file.startsWith(CONTENT_DIR) ? relative(CONTENT_DIR, file) : file).split(sep).join('/');
  return path.startsWith('es/') ? 'es' : 'en';
}

/**
 * The file an import specifier names, trying the extensions Astro resolves.
 *
 * @param {string} from  The importing file.
 * @param {string} specifier
 * @returns {string | undefined}
 */
function resolveImport(from, specifier) {
  if (!specifier.startsWith('.')) return undefined;
  const target = resolve(dirname(from), specifier);
  for (const candidate of [target, `${target}.ts`, `${target}.mjs`, `${target}.js`]) {
    if (existsSync(candidate)) return candidate;
  }
  return undefined;
}

/**
 * Reads a page's imports: components are checked against the registry, and
 * allow-listed data modules are loaded so their exports can stand in for the
 * names the page uses.
 *
 * @param {MdNode} tree
 * @param {{ file: string, registry: Map<string, ComponentMarkdown>, issues: RenderIssue[] }} options
 * @returns {Promise<Map<string, unknown>>}  The names the page may print.
 */
export async function loadScope(tree, { file, registry, issues }) {
  /** @type {Map<string, unknown>} */
  const scope = new Map();
  const allowed = new Set(DATA_MODULES.map((path) => resolve(SITE_DIR, path)));
  for (const node of tree.children ?? []) {
    if (node.type !== 'mdxjsEsm') continue;
    for (const statement of node.data?.estree?.body ?? []) {
      const at = node.position?.start.line;
      if (statement.type !== 'ImportDeclaration') {
        issues.push({ kind: 'expression', line: at, message: `a page export is not read into its Markdown copy (${statement.type})` });
        continue;
      }
      const specifier = String(statement.source?.value ?? '');
      const specifiers = statement.specifiers ?? [];
      if (specifier.endsWith('.astro')) {
        for (const one of specifiers) {
          const name = one.local?.name ?? '';
          if (!registry.has(name)) {
            issues.push({ kind: 'component', line: at, message: `imports <${name}> (${specifier}) with no Markdown writer: add ${name}.md.mjs beside the component` });
          }
        }
        continue;
      }
      const target = resolveImport(file, specifier);
      if (!target || !allowed.has(target)) {
        issues.push({ kind: 'expression', line: at, message: `imports ${specifier}, which is neither a component nor one of ${DATA_MODULES.join(', ')}` });
        continue;
      }
      const module = await import(pathToFileURL(target).href);
      for (const one of specifiers) {
        const local = one.local?.name ?? '';
        if (one.type === 'ImportNamespaceSpecifier') scope.set(local, module);
        else if (one.type === 'ImportDefaultSpecifier') scope.set(local, module.default);
        else scope.set(local, module[one.imported?.name ?? one.imported?.value ?? local]);
      }
    }
  }
  return scope;
}

/**
 * The address on the site of the page a content file builds, or undefined
 * for a file outside the content directory.
 *
 * @param {string} file
 * @returns {string | undefined}
 */
export function pageUrlOf(file) {
  if (!file.startsWith(CONTENT_DIR)) return undefined;
  const path = relative(CONTENT_DIR, file).split(sep).join('/').replace(/\.mdx?$/u, '');
  const route = path === 'index' ? '' : path.replace(/\/index$/u, '');
  return SITE.url(`/${route}${route ? '/' : ''}`);
}

/**
 * Reads, parses and writes one content file.
 *
 * @param {string} file  Absolute path of a page under `src/content/docs`.
 * @param {{ registry: Map<string, ComponentMarkdown>, flavour?: 'agent' | 'github', issues?: RenderIssue[], lang?: 'en' | 'es' }} options
 *   `lang` defaults to the language of the file's place under the content
 *   directory; a check that reads another directory passes it.
 * @returns {Promise<{ markdown: string, frontmatter: Record<string, unknown>, issues: RenderIssue[], tree: MdNode }>}
 * @throws {Error}  When the file does not parse, as the site build would.
 */
export async function renderFile(file, { registry, flavour = 'agent', issues = [], lang = langOf(file) }) {
  // What a Markdown plugin of the site writes into the page before Astro
  // renders it is written into the source first (./rewrites.mjs): the
  // bibliography's lists, which its source holds only as markers. The file
  // is read as the commit holds it, with line feeds whatever the checkout
  // gave it: the renderer copies code and tables out of the source by
  // position, so a carriage return left in would reach the copy.
  const source = await rewrittenSource(file, readCommittedText(file), { lang });
  const mdx = isMdx(file);
  const tree = parse(source, { mdx });
  const scope = mdx ? await loadScope(tree, { file, registry, issues }) : new Map();
  const frontmatter = frontmatterOf(tree);
  const markdown = renderTree(tree, source, { registry, flavour, scope, issues, frontmatter, lang, pageUrl: pageUrlOf(file) });
  return { markdown, frontmatter, issues, tree };
}
