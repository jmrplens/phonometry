// What numberGlue reads as a number run into a word, and what it leaves alone.
//
// The built site only ever hands it markup the components wrote, so each case
// here is the smallest piece of markup that shows one decision: which
// boundaries join the text, which break it, and which edges are glue by design.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { numberGlue } from './crawler-text.mjs';

test('a number and its label written as two spans run together', () => {
	assert.deepEqual(
		numberGlue('<div><span class="value">1897</span><span class="label"><a href="/x/">conformance checks passing</a></span></div>'),
		[{ before: '1897', after: 'conformance checks passing' }],
	);
});

test('a label and the count after it run together', () => {
	assert.deepEqual(numberGlue('<a><span class="label">Theory</span><span class="count">7 pages</span></a>'), [
		{ before: 'Theory', after: '7 pages' },
	]);
});

test('a designation and the count after it run into another number', () => {
	assert.deepEqual(numberGlue('<p><a href="/e/">ISO 717</a><span>3 entries</span></p>'), [
		{ before: 'ISO 717', after: '3 entries' },
	]);
});

test('a space between the two elements, written or as an entity, is the word break', () => {
	assert.deepEqual(numberGlue('<div><span>1897</span> <span>checks</span></div>'), []);
	assert.deepEqual(numberGlue('<div><span>1897 </span><span>checks</span></div>'), []);
	assert.deepEqual(numberGlue('<div><span>1897</span>&#32;<span>checks</span></div>'), []);
	assert.deepEqual(numberGlue('<div><span>1897</span>&#xA0;<span>checks</span></div>'), []);
});

test('a block between the two breaks the text', () => {
	assert.deepEqual(numberGlue('<div>1897</div><div>checks</div>'), []);
	assert.deepEqual(numberGlue('<li><a>Theory</a></li><li><a>7 pages</a></li>'), []);
	assert.deepEqual(numberGlue('<td>12</td><td>dB</td>'), []);
	assert.deepEqual(numberGlue('<span>12</span><br><span>dB</span>'), []);
});

test('two words without a number are not this check', () => {
	assert.deepEqual(numberGlue('<p><b>Note</b>text</p>'), []);
});

test('punctuation on either side of the boundary is not glue', () => {
	assert.deepEqual(numberGlue('<p><a>ISO 717</a>, and <a>3 more</a></p>'), []);
	assert.deepEqual(numberGlue('<p><span>+3</span><span>(2019)</span></p>'), []);
});

test('the edges of an index join a symbol and its subscript or exponent on purpose', () => {
	assert.deepEqual(numberGlue('<p>L<sub>Aeq</sub>2 and 10<sup>3</sup>Pa</p>'), []);
});

test('maths and code are not read', () => {
	assert.deepEqual(
		numberGlue('<p><span class="katex"><span class="mord">1</span><span class="mord">0</span></span>dB</p>'),
		[],
	);
	assert.deepEqual(numberGlue('<p>Size<code>x</code>3</p>'), []);
	assert.deepEqual(numberGlue('<pre><span>1</span><span>a</span></pre>'), []);
});

test('a drawing puts nothing between the words on either side of it', () => {
	assert.deepEqual(numberGlue('<p><a>ISO 3095<svg><text>9</text><path/></svg>Next page</a></p>'), [
		{ before: 'ISO 3095', after: 'Next page' },
	]);
	assert.deepEqual(numberGlue('<p><a><svg><path/></svg>Next</a> <span>2D FDTD</span></p>'), []);
	assert.deepEqual(numberGlue('<p>12<svg/>dB</p>'), [{ before: '12', after: 'dB' }]);
});

test('the text after maths or code is read again from there', () => {
	assert.deepEqual(numberGlue('<p><code>x</code> then <span>12</span><span>dB</span></p>'), [
		{ before: ' then 12', after: 'dB' },
	]);
});

test('a comment, a break opportunity or a blanked script is no word break', () => {
	assert.deepEqual(numberGlue('<p><span>12</span><!-- note --><span>dB</span></p>'), [
		{ before: '12', after: 'dB' },
	]);
	assert.deepEqual(numberGlue('<p>12<wbr>34</p>'), []);
	assert.deepEqual(numberGlue('<p><span>12</span><script></script><span>dB</span></p>'), [
		{ before: '12', after: 'dB' },
	]);
});

test('a quoted > inside an attribute ends no tag', () => {
	assert.deepEqual(numberGlue('<p><a title="a > b">7</a><span>pages</span></p>'), [{ before: '7', after: 'pages' }]);
});

test('the context printed on each side is cut to thirty characters', () => {
	const [found] = numberGlue(`<p><span>${'x'.repeat(40)}1</span><span>${'y'.repeat(40)}</span></p>`);
	assert.equal(found.before, `${'x'.repeat(29)}1`);
	assert.equal(found.after, 'y'.repeat(30));
});
