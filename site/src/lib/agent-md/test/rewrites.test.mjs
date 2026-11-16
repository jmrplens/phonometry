/**
 * What a Markdown plugin of the site writes into a page reaches the page's
 * Markdown copy too: the bibliography's lists, which its source holds only as
 * markers that remark-bibliography.mjs fills at build time.
 */
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';

import { checkMarkdownWriters } from '../../../../scripts/check-markdown-writers.mjs';
import { bibliographyOf } from '../../remark-bibliography.mjs';
import { CONTENT_DIR, renderFile } from '../render.mjs';
import { render } from './helpers.mjs';

for (const lang of /** @type {const} */ (['en', 'es'])) {
  test(`the ${lang} bibliography's copy lists every work its page lists, each with the pages that cite it`, async () => {
    const file = join(CONTENT_DIR, ...(lang === 'es' ? ['es'] : []), 'reference', 'bibliography.md');
    const issues = [];
    const { markdown } = await renderFile(file, { registry: new Map(), issues, lang });
    const works = (await bibliographyOf(CONTENT_DIR, lang)).reduce((total, section) => total + section.entries.length, 0);
    const lead = lang === 'es' ? 'Citado por' : 'Cited by';
    const entries = markdown.split('\n- ').slice(1).filter((entry) => entry.includes(`${lead} [`));
    assert.ok(works > 400, `the ${lang} bibliography lists ${works} works`);
    assert.equal(entries.length, works, `the copy lists ${entries.length} of the ${works} works`);
    assert.doesNotMatch(markdown, /<!--\s*bibliography:/u, 'no marker is left in the copy');
    assert.deepEqual(issues, []);
  });
}

test('a bibliography marker that reaches the renderer unwritten is reported, not dropped', () => {
  const { markdown, issues } = render('# Works\n\n<!-- bibliography: general -->\n\nThe end.\n', { mdx: false });
  assert.doesNotMatch(markdown, /bibliography:/u);
  assert.equal(issues.length, 1);
  assert.equal(issues[0].kind, 'html');
  assert.match(issues[0].message, /bibliography marker/u);
});

test('a Markdown plugin that writes into a page fails the check while the copies have no rule for it', async (t) => {
  const root = mkdtempSync(join(tmpdir(), 'agent-md-rewrites-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, 'src', 'content', 'docs'), { recursive: true });
  mkdirSync(join(root, 'src', 'components'), { recursive: true });
  mkdirSync(join(root, 'src', 'lib'), { recursive: true });
  writeFileSync(join(root, 'src', 'lib', 'remark-other.mjs'), "export const REWRITES = ['a.md'];\nexport function remarkOther() {}\n");
  writeFileSync(
    join(root, 'astro.config.mjs'),
    "import { remarkOther } from './src/lib/remark-other.mjs';\n\nexport default {\n  markdown: {\n    remarkPlugins: [remarkOther],\n  },\n};\n",
  );
  writeFileSync(join(root, 'src', 'content', 'docs', 'a.md'), '---\ntitle: "A"\n---\n\nText.\n');
  const { failures } = await checkMarkdownWriters({
    contentDir: join(root, 'src', 'content', 'docs'),
    componentsDir: join(root, 'src', 'components'),
    siteDir: root,
  });
  const plugin = failures.filter((failure) => failure.kind === 'plugin');
  assert.equal(plugin.length, 1, JSON.stringify(failures));
  assert.match(plugin[0].message, /src\/lib\/remark-other\.mjs writes into a\.md/u);
});
