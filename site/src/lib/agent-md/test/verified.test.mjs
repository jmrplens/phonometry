/** A copy states `Verified:` exactly where its page shows the "Verified by" line, with the same count. */
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { join } from 'node:path';

import { pageMarkdown } from '../page.mjs';
import { loadRegistry } from '../registry.mjs';
import { CONTENT_DIR } from '../render.mjs';
import { verifiedProvider } from '../verified.mjs';

test("the copy of a guide the report verifies says so, as its page's line does, and a page with none says nothing", async () => {
  const registry = await loadRegistry();
  const verified = verifiedProvider();
  const guide = verified('signals/filters/filter-banks');
  assert.ok(guide && guide.checks > 0, 'the filter banks guide is verified by the report');
  assert.match(guide.url, /\/reference\/conformance\/(#[\w-]+)?$/u);
  const { markdown } = await pageMarkdown(join(CONTENT_DIR, 'signals', 'filters', 'filter-banks.mdx'), { registry, verified });
  assert.match(markdown, new RegExp(`^Verified: ${guide.checks} conformance checks? `, 'mu'));
  const { markdown: about } = await pageMarkdown(join(CONTENT_DIR, 'start', 'about.md'), { registry, verified });
  assert.doesNotMatch(about, /^Verified:/mu);
});
