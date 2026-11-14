// The text a check reads of a built page's markup.
//
// check-structured-data.mjs holds a catalogue's dataset to the headings and
// the paragraphs its page shows, so it reads the text of their markup. That
// text is what stands between the tags, read run by run; nothing is taken out
// of the markup, so no tag can be left behind half removed.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { decode, markupText } from './dist-pages.mjs';

test('the text of markup is its runs of text, with nothing of its tags', () => {
	assert.equal(markupText('Absorption <em>coefficients</em> of <a href="/x/">porous</a> layers'), 'Absorption coefficients of porous layers');
	assert.equal(markupText('<code>alpha_w</code>'), 'alpha_w');
	assert.equal(markupText('one<br>two<br/>three'), 'onetwothree');
	assert.equal(markupText(''), '');
});

test('a quoted attribute value may hold a `>`, which ends no tag', () => {
	assert.equal(markupText('<abbr title="f > 1 kHz">band</abbr> levels'), 'band levels');
	assert.equal(markupText("<span data-note='a > b'>text</span>"), 'text');
});

test('comments and doctypes show nothing, a `<` that opens no tag is text', () => {
	assert.equal(markupText('a<!-- b > c -->d'), 'ad');
	assert.equal(markupText('<!doctype html>page'), 'page');
	assert.equal(markupText('1 < 2 and 3 > 2'), '1 < 2 and 3 > 2');
	assert.equal(markupText('a <3 b'), 'a <3 b');
});

test('the references stay as written, for the decoding that follows', () => {
	assert.equal(markupText('<p>a &lt;em&gt; b &amp; c</p>'), 'a &lt;em&gt; b &amp; c');
	assert.equal(decode(markupText('<p>a &lt;em&gt; b</p>')), 'a <em> b');
});
