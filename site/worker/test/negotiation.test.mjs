// The zone rule that sends a Markdown-preferring request to a page's copy,
// against the negotiation docs.jmrp.io runs (docs-edge's prefersMarkdown).
//
// A rule expression cannot read q-values, so it approximates: Accept names
// text/markdown and names no HTML type before it. The two disagree in two
// classes, named below and in README.md; a generated grid of Accepts checks
// that every disagreement falls in one of them, so a new kind fails here.
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

/** The q of a parsed Accept member: 1 when absent or unreadable, as both sides read it. */
function members(accept) {
	return accept.split(',').map((part, at) => {
		const [type, ...params] = part.trim().split(';');
		let q = 1;
		for (const param of params) {
			const match = /^q\s*=\s*(\d*(?:\.\d+)?)$/i.exec(param.trim());
			if (match && match[1] !== '') q = Number.parseFloat(match[1]);
		}
		return { type: type.trim().toLowerCase(), q, at };
	});
}

const EXACT_HTML = new Set(['text/html', 'application/xhtml+xml']);

/**
 * The class a disagreement belongs to, or null for one nobody named.
 *
 * A: the rule answers HTML and docs.jmrp.io Markdown, because an HTML type is
 *    named before text/markdown (docs.jmrp.io weighs q-values and gives ties
 *    to Markdown; the rule sees only the order).
 * B: the rule answers Markdown and docs.jmrp.io HTML, because text/markdown
 *    carries q=0 (refused), or a lower q than an HTML type named after it.
 */
function disagreementClass(accept, edge, rule) {
	const parts = members(accept);
	const markdown = parts.filter(({ type }) => type === 'text/markdown');
	if (markdown.length !== 1) return null;
	const [md] = markdown;
	const html = parts.filter(({ type }) => EXACT_HTML.has(type));
	if (edge && !rule && html.some(({ at }) => at < md.at)) return 'A';
	if (!edge && rule && (md.q === 0 || html.some(({ at, q }) => at > md.at && q > md.q))) return 'B';
	return null;
}

/** Accepts built from text/markdown and up to two other types, every q and every order. */
function* grid() {
	const qs = ['', ';q=0', ';q=0.1', ';q=0.5', ';q=0.9', ';q=1'];
	const others = ['text/html', 'application/xhtml+xml', 'text/*', '*/*', 'text/plain'];
	const items = others.flatMap((type) => qs.map((q) => `${type}${q}`));
	for (const q of [...qs, ';level=1;q=0']) {
		const md = `text/markdown${q}`;
		for (const a of items) {
			yield `${md}, ${a}`;
			yield `${a}, ${md}`;
			for (const b of items) {
				if (b === a) continue;
				yield `${a}, ${md}, ${b}`;
				yield `${a}, ${b}, ${md}`;
				yield `${md}, ${a}, ${b}`;
			}
		}
	}
}

describe('the disagreements with prefersMarkdown', () => {
	test('every disagreement of the matrix falls in a named class', () => {
		for (const accept of MATRIX.keys()) {
			if (accept === null) continue;
			const edge = prefersMarkdown(accept);
			const rule = page(accept);
			if (edge !== rule) assert.notEqual(disagreementClass(accept, edge, rule), null, JSON.stringify(accept));
		}
	});

	test('every disagreement over the grid falls in class A or B, and both classes occur', () => {
		const seen = { A: 0, B: 0 };
		let total = 0;
		const unnamed = [];
		for (const accept of grid()) {
			total += 1;
			const edge = prefersMarkdown(accept);
			const rule = page(accept);
			if (edge === rule) continue;
			const kind = disagreementClass(accept, edge, rule);
			if (kind === null) unnamed.push(accept);
			else seen[kind] += 1;
		}
		assert.deepEqual(unnamed.slice(0, 10), [], `${unnamed.length} disagreements outside the named classes`);
		assert.ok(seen.A > 0 && seen.B > 0, JSON.stringify(seen));
		assert.ok(total > 15000, `${total} Accepts`);
	});

	test('class B needs text/markdown named first or refused: a browser Accept never reaches it', () => {
		for (const accept of [
			'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
			'*/*',
		]) {
			assert.equal(page(accept), false, accept);
		}
	});

	test('the class model is not vacuous: an agreement is never classed', () => {
		assert.equal(disagreementClass('text/markdown, text/html', true, true), null);
		assert.equal(disagreementClass('text/html, text/markdown', false, false), null);
	});
});

describe('markdown-twin rule against prefersMarkdown, the verbatim copy', () => {
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
