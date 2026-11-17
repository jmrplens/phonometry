// The zone rule that sends a Markdown-preferring request to a page's copy,
// against the negotiation docs.jmrp.io runs (docs-edge's prefersMarkdown).
//
// A rule expression cannot read q-values, so it approximates: Accept names
// text/markdown and names no HTML type before it. This file lists every
// Accept on which the two disagree; a new disagreement fails it.
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { describe, test } from 'node:test';

import { markdownRuleMatches } from '../lib/rules.mjs';
import { twinExclusions } from '../lib/twins.mjs';
import { prefersMarkdown } from './fixtures/prefers-markdown.mjs';

const DOCS_EDGE = '/var/www/jmrp.io/workers/docs-edge/markdown-negotiation.js';
const prefix = '/phonometry';
const zone = { host: 'phonometry.dev', prefix, exclusions: twinExclusions(prefix) };
const page = (accept, extra = {}) =>
	markdownRuleMatches(
		{ host: 'phonometry.dev', method: 'GET', path: '/phonometry/signals/levels/', accept: accept === null ? [] : [accept], ...extra },
		zone,
	);

/** Accept -> [prefersMarkdown, the rule]. The docs-edge D6 matrix, the measured Accepts and the edge cases. */
const MATRIX = new Map([
	['*/*', [false, false]],
	[null, [false, false]],
	['', [false, false]],
	['text/markdown', [true, true]],
	['text/markdown, text/html;q=0.1', [true, true]],
	['text/html, text/markdown;q=0.9', [false, false]],
	['text/plain', [false, false]],
	['text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', [false, false]],
	['text/markdown, text/html;q=0.9, */*;q=0.8', [true, true]],
	['text/markdown, text/html, */*', [true, true]],
	['text/html;q=0.9,text/markdown;q=0.8', [false, false]],
	['text/markdown;q=0.5, */*', [true, true]],
	['text/markdown;q=0.8, text/*;q=0.9', [true, true]],
	['text/markdown;q=.8', [true, true]],
	['TEXT/MARKDOWN', [true, true]],
	['text/*', [false, false]],
	['application/json', [false, false]],
	['text/x-markdown', [false, false]],
	// The disagreements, each one on purpose:
	['text/html,text/markdown', [true, false]], // a tie goes to Markdown there; HTML is named first here
	['application/xhtml+xml, text/markdown', [true, false]], // the same tie
	['text/markdown;q=0, text/html', [false, true]], // q=0 refuses Markdown there; the rule cannot read q
	['text/markdown;q=0.5, text/html', [false, true]], // a lower q loses there
	['text/markdown;level=1;q=0', [false, true]], // q=0 again
]);

/** The Accepts on which the preview and docs.jmrp.io answer differently. README.md lists the same five. */
const DIVERGENCES = [
	'text/html,text/markdown',
	'application/xhtml+xml, text/markdown',
	'text/markdown;q=0, text/html',
	'text/markdown;q=0.5, text/html',
	'text/markdown;level=1;q=0',
];

describe('markdown-twin rule against prefersMarkdown', () => {
	test('every Accept of the matrix gives the listed pair', () => {
		for (const [accept, [edge, rule]] of MATRIX) {
			assert.equal(prefersMarkdown(accept), edge, `prefersMarkdown(${JSON.stringify(accept)})`);
			assert.equal(page(accept), rule, `rule(${JSON.stringify(accept)})`);
		}
	});

	test('the disagreements are exactly the listed ones', () => {
		const found = [...MATRIX.keys()].filter((accept) => prefersMarkdown(accept) !== page(accept));
		assert.deepEqual(found, DIVERGENCES);
	});

	test('a disagreement never sends a browser to Markdown', () => {
		for (const accept of DIVERGENCES) assert.match(accept, /text\/markdown/);
	});

	test('the copy of prefersMarkdown is still verbatim', { skip: !existsSync(DOCS_EDGE) && 'no jmrp.io checkout here' }, () => {
		const fn = /^(function prefersMarkdown\([^)]*\) \{\n[\s\S]*?\n\}\n)/m;
		const ours = readFileSync(new URL('./fixtures/prefers-markdown.mjs', import.meta.url), 'utf8').match(fn)?.[1];
		const theirs = readFileSync(DOCS_EDGE, 'utf8').match(fn)?.[1];
		assert.ok(ours && theirs);
		assert.equal(ours, theirs);
	});
});

describe('markdown-twin rule scope', () => {
	const md = 'text/markdown';

	test('only GET and HEAD', () => {
		assert.equal(page(md, { method: 'HEAD' }), true);
		assert.equal(page(md, { method: 'POST' }), false);
	});

	test('only slash pages under the base path, on the zone host', () => {
		assert.equal(page(md, { path: '/phonometry/signals/levels' }), false);
		assert.equal(page(md, { path: '/phonometry/signals/levels/index.md' }), false);
		assert.equal(page(md, { path: '/other/' }), false);
		assert.equal(page(md, { host: 'www.phonometry.dev' }), false);
	});

	test('the homes are negotiated, the Spanish API pages are not', () => {
		assert.equal(page(md, { path: '/phonometry/' }), true);
		assert.equal(page(md, { path: '/phonometry/es/' }), true);
		assert.equal(page(md, { path: '/phonometry/es/reference/api/' }), false);
		assert.equal(page(md, { path: '/phonometry/es/reference/api/signals/levels/' }), false);
		assert.equal(page(md, { path: '/phonometry/reference/api/signals/levels/' }), true);
	});

	test('any one of several Accept fields can carry the type', () => {
		assert.equal(page(null, { accept: ['text/plain', 'text/markdown'] }), true);
	});
});
