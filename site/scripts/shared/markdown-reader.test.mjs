// The tags the Markdown reader of the writer's tests takes out of the HTML.
//
// The reader prints a page's text as the HTML with its tags taken out. One
// pass of the tag pattern can leave a tag: a quote the first `<` never closes
// keeps that `<` from reading as a tag, the pass takes out the tag after it,
// and what is left joins up into a tag. In `<script "<"'">">` the pass takes
// out `<"'">` alone and leaves `<script "">`. The site's pipeline writes no
// such tag (it writes a quote in an attribute name as a reference), so taking
// the tags out until none is left changes no text it prints.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { withoutTags } from './markdown-reader.mjs';

test('no tag is left once the tags are out, whatever taking one out joins up', () => {
  assert.equal(withoutTags(`<script "<"'">">alert(1)</script>`), 'alert(1)');
  assert.equal(withoutTags(`<"<"'">">`), '');
  // A `<` inside a tag is part of it, so these hold no `<script` once read.
  assert.equal(withoutTags('<<script>script>'), 'script>');
  assert.equal(withoutTags('<scr<b>ipt>'), 'ipt>');
  // A `<` the page prints is written as a reference, which stays text.
  assert.equal(withoutTags('<p>a &lt;script&gt; b</p>'), 'a &lt;script&gt; b');
});
