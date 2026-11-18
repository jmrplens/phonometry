/**
 * The contract between the Markdown renderer and the writer that sits beside
 * each component.
 *
 * A page is turned into Markdown by `render.mjs`, which keeps the bytes of
 * everything the author wrote as Markdown and asks a writer for every
 * component. Each component that a page can import has a sibling file
 * `<Name>.md.mjs` next to its `<Name>.astro`, so what a component means as
 * text lives with the component, and a central switch cannot fall out of step
 * with the components it lists.
 *
 * The shapes are written as JSDoc rather than TypeScript because the renderer
 * runs in plain Node, outside Astro and Vite: `make llms` reads it without a
 * site build.
 *
 * @module
 */

/**
 * A node of the parsed page, narrowed to the fields the renderer reads.
 *
 * @typedef {object} MdNode
 * @property {string} type  mdast node type (`paragraph`, `mdxJsxFlowElement`, ...).
 * @property {string | null} [name]  Tag or directive name.
 * @property {MdAttribute[]} [attributes]  JSX attributes, for elements.
 * @property {MdNode[]} [children]
 * @property {string} [value]  Raw text of `text`, `code`, `inlineCode`, `math`, `html`.
 * @property {string | null} [lang]  Info string of a fenced code block.
 * @property {number} [depth]  Heading depth.
 * @property {{ estree?: EstreeNode, directiveLabel?: boolean }} [data]
 * @property {{ start: Point, end: Point }} [position]
 */

/**
 * @typedef {object} Point
 * @property {number} line
 * @property {number} column
 * @property {number} offset
 */

/**
 * A JSX attribute: `foo="bar"`, `foo={expr}`, a bare `foo` or `{...spread}`.
 *
 * @typedef {object} MdAttribute
 * @property {string} type  `mdxJsxAttribute` or `mdxJsxExpressionAttribute`.
 * @property {string} [name]
 * @property {string | null | { type: string, value?: string, data?: { estree?: EstreeNode } }} [value]
 */

/**
 * An ESTree node, as remark-mdx attaches it to every expression.
 *
 * @typedef {object} EstreeNode
 * @property {string} type
 * @property {unknown} [value]
 * @property {string} [name]
 * @property {string} [operator]
 * @property {boolean} [computed]
 * @property {EstreeNode} [argument]
 * @property {EstreeNode} [object]
 * @property {EstreeNode} [property]
 * @property {EstreeNode} [expression]
 * @property {EstreeNode} [key]
 * @property {(EstreeNode | null)[]} [elements]
 * @property {EstreeNode[]} [properties]
 * @property {EstreeNode[]} [expressions]
 * @property {{ value?: { cooked?: string } }[]} [quasis]
 * @property {EstreeNode[]} [body]
 * @property {EstreeNode[]} [specifiers]
 * @property {EstreeNode} [source]
 * @property {EstreeNode} [local]
 * @property {EstreeNode} [imported]
 */

/**
 * Something the renderer could not write faithfully. The page still renders,
 * and `check-markdown-writers.mjs` turns every issue into a failure.
 *
 * @typedef {object} RenderIssue
 * @property {'component' | 'prop' | 'expression' | 'html' | 'directive' | 'writer'} kind
 * @property {string} message
 * @property {number} [line]  1-based line in the source file, when known.
 */

/**
 * What the renderer hands every writer.
 *
 * @typedef {object} MarkdownContext
 * @property {'en' | 'es'} lang  Language of the page being written.
 * @property {'agent' | 'github'} flavour
 *   `agent`: the Markdown copy published beside each page, with absolute
 *   links and images. `github`: the edition under docs/ that GitHub renders,
 *   with figures as `<picture>` elements.
 * @property {SiteAddress} site
 * @property {Record<string, unknown>} frontmatter  The page's frontmatter,
 *   for a writer that shows what the page's layout draws from it (the
 *   home's tagline and actions).
 * @property {(node: MdNode, name: string) => string | undefined} attr
 *   String value of an attribute: `foo="bar"` or `foo={"bar"}`.
 * @property {(node: MdNode, name: string) => boolean} flag
 *   A boolean attribute: bare `foo`, `foo={true}` or `foo="true"`.
 * @property {(node: MdNode, name: string) => unknown} expr
 *   Value of an attribute read without evaluating anything: literals, and
 *   names the page imports from an allow-listed data module.
 * @property {(node: MdNode) => string} body  The children, already written.
 * @property {(node: MdNode) => string} text  The children as plain text.
 * @property {(node: MdNode) => string} render  One node, written.
 * @property {(markdown: string) => string} markdown
 *   A fragment of Markdown or inline HTML held by a data module, written by
 *   the same rules as a page (for the strings `home-en.ts` and `home-es.ts`
 *   carry).
 * @property {(depth: number, text: string) => string} heading
 *   A heading line, its depth clamped to the six Markdown has.
 * @property {(node: MdNode, message: string) => void} issue
 *   Report something the writer could not write; the page still renders.
 */

/**
 * Where the site is published, for the absolute URLs the copy carries.
 *
 * @typedef {object} SiteAddress
 * @property {string} origin  `https://docs.jmrp.io`
 * @property {string} base  `/phonometry`
 * @property {(path: string) => string} url
 *   An absolute URL for a path under the base, or for a root-relative path
 *   that already starts with it.
 */

/**
 * What a `<Name>.md.mjs` file default-exports.
 *
 * @typedef {object} ComponentMarkdown
 * @property {string} tag  The component name, as pages write the element.
 * @property {readonly string[]} props
 *   Every prop the component declares. A page that passes any other is an
 *   error in the coverage check: a prop the writer does not know is a prop
 *   whose content the Markdown copy silently loses.
 * @property {(node: MdNode, ctx: MarkdownContext) => string} toMarkdown
 *   The Markdown for one use of the component. Return `""` to drop it on
 *   purpose (the file's opening comment says why). Never throw: report with
 *   `ctx.issue` and write what can still be written.
 */

/**
 * Declares a component's Markdown form.
 *
 * An identity helper, so every writer has the same shape and the contract is
 * checked where the writer is defined rather than where it is registered.
 *
 * @param {ComponentMarkdown} spec
 * @returns {ComponentMarkdown}
 */
export function markdownFor(spec) {
  if (typeof spec?.tag !== 'string' || !/^[A-Z][A-Za-z0-9]*$/.test(spec.tag)) {
    throw new TypeError(`markdownFor needs a component name as tag, got ${JSON.stringify(spec?.tag)}`);
  }
  if (!Array.isArray(spec.props)) {
    throw new TypeError(`markdownFor(${spec.tag}) needs the list of props the component declares`);
  }
  if (typeof spec.toMarkdown !== 'function') {
    throw new TypeError(`markdownFor(${spec.tag}) needs a toMarkdown function`);
  }
  return Object.freeze({ ...spec, props: Object.freeze([...spec.props]) });
}
