// What the renderer keeps byte for byte, what it replaces, and what it
// reports, each on a page small enough to read.
//
// Usage (from site/, after `pnpm install`): pnpm run test:agent-md
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { codeSpan, renderTree, SITE } from '../render.mjs';
import { parse } from '../processor.mjs';
import { pointDroppedAnchors, rewriteLinks } from '../links.mjs';
import { Box, Show, registryOf, render } from './helpers.mjs';

describe('what is kept byte for byte', () => {
  test('the imports of a Python example survive the imports of the page', () => {
    // The emitter this replaces ran an `^import` regex over the whole file,
    // fences included, and every Spanish example lost `import numpy as np`.
    const source = [
      "import Box from '../components/Box.astro';",
      '',
      '```python',
      'import numpy as np',
      'export_level = 3',
      '```',
      '',
    ].join('\n');
    const { markdown, issues } = render(source, { registry: registryOf(Box) });
    assert.equal(markdown, '```python\nimport numpy as np\nexport_level = 3\n```\n');
    assert.deepEqual(issues, []);
  });

  test('two blank lines inside a fence stay two', () => {
    const source = '```python\ndef a():\n    pass\n\n\ndef b():\n    pass\n```\n\n\n\nText.\n';
    const { markdown } = render(source);
    assert.equal(markdown, '```python\ndef a():\n    pass\n\n\ndef b():\n    pass\n```\n\nText.\n');
  });

  test('two blank lines inside indented code of a Markdown page stay two', () => {
    const source = 'Text.\n\n    s = \"\"\"a\n\n\n    b\"\"\"\n\n\n\nMore.\n';
    const { markdown } = render(source, { mdx: false });
    assert.equal(markdown, 'Text.\n\n    s = \"\"\"a\n\n\n    b\"\"\"\n\nMore.\n');
  });

  test('TeX keeps its braces, inline and in display', () => {
    const source = 'The level $L_{p} = 10\\lg(p^2/p_0^2)$ holds.\n\n$$\n\\frac{1}{T}\\int_{0}^{T} p^2(t)\\,\\mathrm{d}t\n$$\n';
    const { markdown, issues } = render(source);
    assert.equal(markdown, source);
    assert.deepEqual(issues, []);
  });

  test('a designation keeps its year although the parser reads `:2014` as a directive', () => {
    const { markdown } = render('IEC 61260-1:2014 and ISO 532-1:2017.\n');
    assert.equal(markdown, 'IEC 61260-1:2014 and ISO 532-1:2017.\n');
  });

  test('an indented code block of a Markdown page keeps its indentation', () => {
    const source = 'Rossing writes\n\n    beta = -(3 + K3 / K2)\n\nwith K2 and K3.\n';
    const { markdown } = render(source, { mdx: false });
    assert.equal(markdown, source);
  });

  test('a GFM table is sliced, and a component in a cell is replaced in place', () => {
    const source = '| a | b |\n| --- | --- |\n| <Show value="x" /> | 2 |\n';
    const { markdown } = render(source, { registry: registryOf(Show) });
    assert.equal(markdown, '| a | b |\n| --- | --- |\n| "x" | 2 |\n');
  });
});

describe('components', () => {
  test('a component is replaced by its writer, and its children are written in turn', () => {
    const source = '<Box kind="note">\n  First **bold** and `code`.\n\n  - one\n  - two\n</Box>\n';
    const { markdown, issues } = render(source, { registry: registryOf(Box) });
    // The two spaces each line inherited from the element are gone, so the
    // list is not read as nested under the paragraph.
    assert.equal(markdown, '[note]\n\nFirst **bold** and `code`.\n\n- one\n- two\n');
    assert.deepEqual(issues, []);
  });

  test('phrasing children are joined without a blank line and keep their spaces', () => {
    const source = '<Box>Uses **nonces** or **hashes**</Box>\n';
    const { markdown } = render(source, { registry: registryOf(Box) });
    assert.equal(markdown, '[box]\n\nUses **nonces** or **hashes**\n');
  });

  test('a component with no writer writes its children and is reported', () => {
    const { markdown, issues } = render('<Missing>\nThe text.\n</Missing>\n');
    assert.equal(markdown, 'The text.\n');
    assert.equal(issues.length, 1);
    assert.equal(issues[0].kind, 'component');
    assert.match(issues[0].message, /<Missing> has no Markdown writer: add Missing\.md\.mjs/);
    assert.equal(issues[0].line, 1);
  });

  test('a prop the writer does not declare is reported, and so is a spread', () => {
    const { issues } = render('<Box kind="a" links={[]} {...rest}>\nx\n</Box>\n', { registry: registryOf(Box) });
    assert.deepEqual(
      issues.map((issue) => issue.kind),
      ['prop', 'prop'],
    );
    assert.match(issues[0].message, /passes "links", which Box\.md\.mjs does not declare/);
    assert.match(issues[1].message, /spreads props/);
  });

  test('a writer that throws is reported and the children stand in', () => {
    const Broken = { tag: 'Broken', props: [], toMarkdown: () => { throw new Error('boom'); } };
    const { markdown, issues } = render('<Broken>\nkept\n</Broken>\n', { registry: registryOf(Broken) });
    assert.equal(markdown, 'kept\n');
    assert.equal(issues[0].kind, 'writer');
    assert.match(issues[0].message, /Broken\.md\.mjs threw: boom/);
  });
});

describe('props and expressions are read without evaluating code', () => {
  test('literals of every form', () => {
    const cases = [
      ['"text"', '"text"'],
      ["{'single'}", '"single"'],
      ['{`template`}', '"template"'],
      ['{-3}', '-3'],
      ["{[1, 'a', { k: true }]}", '[1,"a",{"k":true}]'],
      ['{null}', 'null'],
    ];
    for (const [written, expected] of cases) {
      const { markdown, issues } = render(`<Show value=${written} />\n`, { registry: registryOf(Show) });
      assert.equal(markdown, `${expected}\n`, written);
      assert.deepEqual(issues, [], written);
    }
  });

  test('a name resolves only through the scope the page imports', () => {
    const scope = new Map([['stats', { checks: 1893, label: 'checks' }]]);
    const { markdown, issues } = render('<Show value={stats.checks} />\n', { registry: registryOf(Show), scope });
    assert.equal(markdown, '1893\n');
    assert.deepEqual(issues, []);
  });

  test('a call, a template with a hole or an unknown name is reported, never run', () => {
    for (const written of ['{run()}', '{`a${b}`}', '{unknown}', '{stats.missing}']) {
      const scope = new Map([['stats', {}]]);
      const { markdown, issues } = render(`<Show value=${written} />\n`, { registry: registryOf(Show), scope });
      // Show prints what it was handed: nothing, and the renderer says why.
      assert.equal(markdown, '\n', written);
      assert.deepEqual(
        issues.map((issue) => issue.kind),
        ['expression', 'writer'],
        written,
      );
    }
  });

  test('a text expression prints its value; a comment prints nothing', () => {
    const scope = new Map([['totalChecks', 1893]]);
    const source = 'All {totalChecks} checks{" "}pass.{/* a note for the author */}\n';
    const { markdown, issues } = render(source, { scope });
    assert.equal(markdown, 'All 1893 checks pass.\n');
    assert.deepEqual(issues, []);
  });

  test('a text expression the renderer cannot read is reported, not left as braces', () => {
    const { markdown, issues } = render('All {totalChecks} checks.\n');
    assert.equal(markdown, 'All  checks.\n');
    assert.equal(issues[0].kind, 'expression');
    assert.match(issues[0].message, /\{totalChecks\} is neither a literal nor a value imported from/);
  });
});

describe('asides', () => {
  test('a titled aside is a bold label, in the page language, then its body', () => {
    const source = ':::caution[Read this]\nThe body, with a fence:\n\n```python\nx = 1\n```\n:::\n';
    assert.equal(
      render(source).markdown,
      '**Caution: Read this**\n\nThe body, with a fence:\n\n```python\nx = 1\n```\n',
    );
    assert.equal(render(':::note\nUna nota.\n:::\n', { lang: 'es' }).markdown, '**Nota**\n\nUna nota.\n');
    assert.equal(render(':::tip\nT.\n:::\n', { lang: 'es' }).markdown, '**Consejo**\n\nT.\n');
    assert.equal(render(':::danger\nD.\n:::\n').markdown, '**Danger**\n\nD.\n');
  });

  test('a directive Starlight does not draw is reported and kept as written', () => {
    const { markdown, issues } = render(':::warning\nW.\n:::\n');
    assert.equal(markdown, ':::warning\nW.\n:::\n');
    assert.equal(issues[0].kind, 'directive');
  });
});

describe('raw HTML', () => {
  test('details: the summary in bold, then the body whole', () => {
    const source = '<details>\n<summary>Show the code for this figure</summary>\n\n```python\nplot()\n```\n\n</details>\n';
    assert.equal(render(source).markdown, '**Show the code for this figure**\n\n```python\nplot()\n```\n');
  });

  test('sup and sub keep the exponent and the index attached', () => {
    assert.equal(render('10<sup>4</sup> and L<sub>Aeq</sub>.\n').markdown, '10^4 and L_Aeq.\n');
  });

  test('code, strong, em, a, br, and an empty anchor span', () => {
    const source =
      '<span id="old-anchor"></span>\n\nA <code>x`y</code>, <strong>b</strong>, <em>i</em>, <a href="/phonometry/start/">start</a>.\n';
    assert.equal(
      render(source).markdown,
      'A ``x`y``, **b**, *i*, [start](https://docs.jmrp.io/phonometry/start/).\n',
    );
  });

  test('code and kbd print the characters the page shows, not the references and escapes written for them', () => {
    // Inside backticks Markdown reads every character as it stands, so a
    // reference or an escape copied from the source would show as written.
    assert.equal(render('Use <code>a &lt; b</code> here.\n').markdown, 'Use `a < b` here.\n');
    assert.equal(render('Press <kbd>Ctrl &amp; C</kbd>.\n').markdown, 'Press `Ctrl & C`.\n');
    assert.equal(render('a <code>x\\*y</code> b\n').markdown, 'a `x*y` b\n');
    assert.equal(render('Use <code><em>x</em> and <strong>y</strong></code>.\n').markdown, 'Use `x and y`.\n');
    assert.doesNotMatch(render('<code>a<br />b</code>\n').markdown, /\\/u);
    // The attributes of a tag written as its text are still read.
    assert.equal(render('<code><em title={foo}>x</em></code>\n').issues[0]?.kind, 'expression');
  });

  test('br is a line break the copy keeps', () => {
    // A bare line end inside a paragraph is a space to a Markdown reader; a
    // backslash before it is the hard break CommonMark and GitHub both draw.
    assert.equal(render('first<br />second\n').markdown, 'first\\\nsecond\n');
    assert.equal(render('first<br />\nsecond\n').markdown, 'first\\\nsecond\n');
    assert.equal(render('last<br />\n\nNext.\n').markdown, 'last\n\nNext.\n');
    assert.equal(render('<strong>last<br /></strong>\n\nNext.\n').markdown, '**last**\n\nNext.\n');
    assert.equal(render('first<br /> \nsecond\n').markdown, 'first\\\nsecond\n');
    assert.equal(render('<strong>a<br /></strong>b\n').markdown, '**a**\\\nb\n');
    assert.equal(render('first<br /><em>second</em>\n').markdown, 'first\\\n*second*\n');
    const cells = '<table><tbody><tr><td>a<br />b</td></tr></tbody></table>\n';
    assert.doesNotMatch(render(cells).markdown, /\\/u);
  });

  test('a table under its caption, standing apart from the text inline around it', () => {
    const source =
      '<div class="r"><table><caption><strong>Result</strong><span>FAIL</span></caption>' +
      '<thead><tr><th>field</th><th>value</th></tr></thead>' +
      '<tbody><tr><td><code>level</code></td><td>2 | 3</td></tr></tbody></table><div>plot()</div></div>\n';
    assert.equal(
      render(source).markdown,
      '**Result FAIL**\n\n| field | value |\n| --- | --- |\n| `level` | 2 \\| 3 |\n\nplot()\n',
    );
  });

  test('a tag with no rule is reported', () => {
    const { issues } = render('<video src="x.webm"></video>\n');
    assert.equal(issues[0].kind, 'html');
    assert.match(issues[0].message, /<video> is raw HTML with no rule/);
  });

  test('in a Markdown page a comment is dropped and any other HTML reported', () => {
    const page = '<!-- Generated from docs/ERRATA.md -->\n\n# Errata\n\n<div>\nx\n</div>\n';
    const { markdown, issues } = render(page, { mdx: false });
    assert.equal(markdown, '# Errata\n\n<div>\nx\n</div>\n');
    // CommonMark reads `<div>` to the next blank line as one block of HTML.
    assert.deepEqual(
      issues.map((issue) => issue.kind),
      ['html'],
    );
  });
});

describe('links', () => {
  test('root-relative links are made absolute, and code is left alone', () => {
    const source = [
      'See [the guide](/phonometry/signals/) and ![a figure](/phonometry/media/a.svg).',
      '',
      '`[x](/phonometry/not-a-link/)` stays as written, and so does',
      '`a span that opens here',
      'and closes here`; see [`f`](/phonometry/reference/api/f/#f).',
      '',
      '[ref]: /phonometry/reference/',
      '',
      '```markdown',
      '[sample](/phonometry/sample/)',
      '```',
      '',
    ].join('\n');
    const { markdown } = render(source, { mdx: false });
    assert.equal(
      markdown,
      [
        'See [the guide](https://docs.jmrp.io/phonometry/signals/) and ![a figure](https://docs.jmrp.io/phonometry/media/a.svg).',
        '',
        '`[x](/phonometry/not-a-link/)` stays as written, and so does',
        '`a span that opens here',
        'and closes here`; see [`f`](https://docs.jmrp.io/phonometry/reference/api/f/#f).',
        '',
        '[ref]: https://docs.jmrp.io/phonometry/reference/',
        '',
        '```markdown',
        '[sample](/phonometry/sample/)',
        '```',
        '',
      ].join('\n'),
    );
  });

  test('a destination after spacing, a line break or an angle bracket is still found', () => {
    // A copy with no `](/` or `]: /` in it is not parsed for links at all,
    // so every form a root-relative destination can take has to show that
    // pair, or the link would be skipped as if there were none.
    const source = '[a]( /phonometry/a/) and [b](</phonometry/b/>) and [c](\n  /phonometry/c/).\n\n[d]:\n  /phonometry/d/\n';
    const { markdown } = render(source, { mdx: false });
    for (const name of ['a', 'b', 'c', 'd']) assert.ok(markdown.includes(`https://docs.jmrp.io/phonometry/${name}/`), name);
    assert.doesNotMatch(markdown, /[(<\s]\/phonometry\//u);
    const none = '| a | b |\n| --- | --- |\n| [x](https://example.org/) | `](/` in code |\n';
    assert.equal(render(none, { mdx: false }).markdown, none);
  });

  test('a destination written with a character reference or an escape is still made absolute', () => {
    // The parser hands over the destination decoded, so it cannot be found by
    // searching the source for the decoded text.
    const source = '[search](/phonometry/?a=1&amp;b=2) and [a](/phonometry/a\\_b/).\n\n[d]: </phonometry/d&#95;e/>\n';
    const { markdown } = render(source, { mdx: false });
    assert.equal(
      markdown,
      '[search](https://docs.jmrp.io/phonometry/?a=1&amp;b=2) and [a](https://docs.jmrp.io/phonometry/a\\_b/).\n\n' +
        '[d]: <https://docs.jmrp.io/phonometry/d&#95;e/>\n',
    );
  });

  test('a destination on the next line of a block quote is still made absolute', () => {
    const source = '> [a](/phonometry/a/)\n> [b](\n>   /phonometry/b/)\n';
    assert.equal(
      render(source, { mdx: false }).markdown,
      '> [a](https://docs.jmrp.io/phonometry/a/)\n> [b](\n>   https://docs.jmrp.io/phonometry/b/)\n',
    );
  });

  test('a title that holds a link form leaves the destination to be the one rewritten', () => {
    const source = '[x](/phonometry/p/ "see ](/phonometry/p/)")\n';
    assert.equal(render(source, { mdx: false }).markdown, '[x](https://docs.jmrp.io/phonometry/p/ "see ](/phonometry/p/)")\n');
  });

  test('an autolink and a bare address are left as written', () => {
    const text = 'See <https://docs.jmrp.io/phonometry/a/> and https://docs.jmrp.io/phonometry/a/.\n';
    assert.equal(rewriteLinks(text, () => '/elsewhere/'), text);
  });

  test('a link is rewritten whole however its destination is written', () => {
    const rewrite = (url) => (url === '/old/a_b' ? '/new/' : undefined);
    assert.equal(rewriteLinks('[x](/old/a\\_b) and [y](</old/a&#95;b>).\n', rewrite), '[x](/new/) and [y](</new/>).\n');
  });

  test('the site address builds absolute URLs from any of the forms writers hold', () => {
    assert.equal(SITE.url('/phonometry/start/'), 'https://docs.jmrp.io/phonometry/start/');
    assert.equal(SITE.url('/reference/conformance/'), 'https://docs.jmrp.io/phonometry/reference/conformance/');
    assert.equal(SITE.url('llms.txt'), 'https://docs.jmrp.io/phonometry/llms.txt');
    assert.equal(SITE.url('https://example.org/x'), 'https://example.org/x');
  });
});

describe('helpers', () => {
  test('a code span is always closed by a fence longer than any run inside it', () => {
    assert.equal(codeSpan('x'), '`x`');
    assert.equal(codeSpan('a`b'), '``a`b``');
    assert.equal(codeSpan('`edge'), '`` `edge ``');
  });

  test('a writer heading is clamped to the six levels Markdown has', () => {
    const Deep = { tag: 'Deep', props: [], toMarkdown: (_node, ctx) => `${ctx.heading(9, 'Deep')}\n\n${ctx.heading(0, 'Top')}` };
    assert.equal(render('<Deep />\n', { registry: registryOf(Deep) }).markdown, '###### Deep\n\n# Top\n');
  });

  test('a data string with inline HTML is written by the same rules as a page', () => {
    const Data = {
      tag: 'Data',
      props: [],
      toMarkdown: (_node, ctx) => ctx.markdown('Run <code>.plot()</code> on <a href="https://pypi.org/">PyPI</a>.'),
    };
    assert.equal(render('<Data />\n', { registry: registryOf(Data) }).markdown, 'Run `.plot()` on [PyPI](https://pypi.org/).\n');
  });
});

describe('what the per-element checks reach', () => {
  const kinds = (source) => render(source).issues.map((issue) => issue.kind);

  test('a spread on a cell, a row or a summary is reported as anywhere else', () => {
    assert.deepEqual(kinds('<table><tr><td {...{title: "x"}}>value</td></tr></table>\n'), ['prop']);
    assert.deepEqual(kinds('<table><tr {...{a: 1}}><td>v</td></tr></table>\n'), ['prop']);
    assert.deepEqual(kinds('<table><thead {...{a: 1}}><tr><td>v</td></tr></thead></table>\n'), ['prop']);
    assert.deepEqual(kinds('<details>\n<summary {...{title: "x"}}>sum</summary>\n\nBody.\n\n</details>\n'), ['prop']);
  });

  test('a tag with no rule or a component with no writer inside a caption or a row is reported', () => {
    assert.deepEqual(kinds('<table><caption><Unknown>cap</Unknown></caption><tr><td>v</td></tr></table>\n'), ['component']);
    assert.deepEqual(kinds('<table><caption><blink>x</blink></caption><tr><td>v</td></tr></table>\n'), ['html']);
    assert.deepEqual(kinds('<table><tr><blink>x</blink><td>v</td></tr></table>\n'), ['html']);
    assert.deepEqual(kinds('<table><blink><tr><td>v</td></tr></blink></table>\n'), ['html']);
  });
});

describe('expressions print what the page prints', () => {
  test('a string with Markdown marks prints as written, a space stays a space, and code is left as it is', () => {
    assert.equal(render('The marker is {"*not emphasis*"}.\n').markdown, 'The marker is \\*not emphasis\\*.\n');
    assert.equal(render('a{" "}b\n').markdown, 'a b\n');
    assert.equal(render('<code>{"a*b*"}</code>\n').markdown, '`a*b*`\n');
  });
});

describe('the body keeps its first line', () => {
  test('an indented code block that opens a Markdown page keeps its indentation', () => {
    assert.equal(render('    beta = 1\n\nprose\n', { mdx: false }).markdown, '    beta = 1\n\nprose\n');
    assert.equal(render('\n\n    beta = 1\n', { mdx: false }).markdown, '    beta = 1\n');
  });
});

describe('anchors the copy drops', () => {
  test('a link to an id only an empty span carried leads to the page, where the span still is', () => {
    const source = '<span id="tubo-o-camara"></span>\n\n## Tubo o cámara\n\nSee [the tube](#tubo-o-camara) and [the heading](#tubo-o-cámara).\n';
    const issues = [];
    const markdown = renderTree(parse(source, { mdx: true }), source, {
      registry: new Map(),
      issues,
      lang: 'es',
      pageUrl: 'https://docs.jmrp.io/phonometry/es/a/',
    });
    assert.match(markdown, /\[the tube\]\(https:\/\/docs\.jmrp\.io\/phonometry\/es\/a\/#tubo-o-camara\)/);
    assert.match(markdown, /\[the heading\]\(#tubo-o-cámara\)/);
    assert.deepEqual(issues, []);
  });

  test('a reference link and an angle-bracketed fragment lead to the page too', () => {
    const page = 'https://docs.jmrp.io/phonometry/a/';
    const anchors = new Set(['old']);
    assert.equal(
      pointDroppedAnchors('See [details][target] and [here](<#old>).\n\n[target]: #old\n', anchors, page),
      `See [details][target] and [here](<${page}#old>).\n\n[target]: ${page}#old\n`,
    );
    assert.equal(pointDroppedAnchors('[t]:\n  <#old>\n', anchors, page), `[t]:\n  <${page}#old>\n`);
    assert.equal(pointDroppedAnchors('[x][t]\n\n[t]: &#35;old\n', anchors, page), `[x][t]\n\n[t]: ${page}&#35;old\n`);
  });
});

describe('a data string that does not parse', () => {
  test('is reported and written as text, no tag left in it', () => {
    const Data = { tag: 'Data', props: [], toMarkdown: (_node, ctx) => ctx.markdown('An <script unclosed <b>bold') };
    const { markdown, issues } = render('<Data />\n', { registry: registryOf(Data) });
    assert.deepEqual(issues.map((issue) => issue.kind), ['writer']);
    assert.doesNotMatch(markdown, /(?<!\\)<[A-Za-z]/);
    assert.match(markdown, /\\<script/);
  });
});
