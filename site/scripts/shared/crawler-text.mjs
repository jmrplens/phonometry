// The text a crawler takes from a built page, and the places where that text
// runs a number into a word.
//
// A crawler that does not apply the page's stylesheet, which is how the
// language-model crawlers read a page, joins the text of inline elements as it
// is written and breaks it only where HTML itself puts a block. The site's
// components lay their pieces out with flex and grid, so on screen
// `<span>1897</span><span>conformance checks passing</span>` is a number above
// its label; to that crawler it is "1897conformance checks passing", and
// `<a>ISO 717</a><span>3 entries</span>` is "ISO 7173 entries", a standard that
// does not exist. Whitespace between two flex or grid items is not drawn, so a
// space between them costs the layout nothing and gives the crawler its word
// break.
//
// `numberGlue` reads a page's markup that way and returns every place where
// the text before an element boundary ends in a letter or a digit, the text
// after it starts with one, at least one of the two is a digit, and nothing
// between them is a block. A drawing (<svg>, an icon) is skipped and puts
// nothing between the words on either side of it, so "Next" after an arrow
// still meets the title before the arrow. Three kinds of boundary are not read
// as glue:
//
// - the edges of <sub> and <sup>, which join a symbol and its index by design
//   (L<sub>Aeq</sub>, 10<sup>3</sup>);
// - the edges of maths and code (KaTeX, <code>, <pre>, <kbd>, <samp>,
//   <math>), whose text is not prose and whose own spans glue digits on
//   purpose;
// - <wbr>, a break opportunity inside one word, and the scripts, styles and
//   templates, which put no text on the page.
//
// Usage: import { numberGlue } from './crawler-text.mjs';
import { decode } from './dist-pages.mjs';

/**
 * Elements whose text a CSS-less reader sets apart from what comes before and
 * after: the block elements of HTML's own rendering, the line break, the head
 * and the replaced or form elements that stand as a box of their own.
 */
const SEPARATE = new Set(
	[
		'address article aside audio blockquote body br button canvas caption col colgroup',
		'dd details dialog div dl dt embed fieldset figcaption figure footer form',
		'h1 h2 h3 h4 h5 h6 head header hgroup hr html iframe img input legend li link',
		'main menu meta nav object ol optgroup option p picture progress search section',
		'select source summary table tbody td textarea tfoot th thead title tr track ul video',
	]
		.join(' ')
		.split(' '),
);

/** Elements whose text is not prose: read as a break and not looked inside. */
const OPAQUE = new Set(['code', 'kbd', 'math', 'noscript', 'pre', 'samp']);

/** Drawings: not looked inside, and no break either, since they hold no prose. */
const DRAWING = new Set(['svg']);

/** Elements whose edges join a symbol to its index on purpose. */
const INDEX = new Set(['sub', 'sup']);

/** Elements HTML defines as empty, which have no closing tag. */
const VOID = new Set('area base br col embed hr img input link meta source track wbr'.split(' '));

/**
 * Elements that put nothing in the text and no boundary in it: a break
 * opportunity inside a word, and the scripts, styles and templates whose
 * bodies `markupOf` has already blanked.
 */
const TRANSPARENT = new Set(['script', 'style', 'template', 'wbr']);

/** Characters of context printed on each side of a glued boundary. */
const CONTEXT = 30;

const WORD = /[\p{L}\p{N}]/u;
const DIGIT = /\p{N}/u;

/**
 * One token at a time: a comment or a doctype, a start or end tag (whose
 * quoted attribute values may hold a `>`), or a run of text.
 */
const TOKEN =
	/<!--[\s\S]*?-->|<![^>]*>|<(\/?)([a-zA-Z][\w:-]*)((?:[^>"']|"[^"]*"|'[^']*')*)>|([^<]+)|</g;

const isMaths = (attributes) => /\sclass="[^"]*\bkatex/.test(attributes);

/**
 * Every place in `markup` where a number runs into a word across an element
 * boundary, as `{ before, after }`: up to thirty characters of the text on
 * each side, so a report can show what the crawler reads.
 */
export function numberGlue(markup) {
	const found = [];
	/** The end of the text read since the last break, and whether a boundary followed it. */
	let before = '';
	let crossed = false;
	/** Whether one of the boundaries crossed is the edge of a <sub> or <sup>. */
	let index = false;
	/** The element being skipped, and how deep inside it the reader is. */
	let skip;
	let depth = 0;
	const reset = () => {
		before = '';
		crossed = false;
		index = false;
	};
	for (const [, slash, rawName, attributes = '', text] of markup.matchAll(TOKEN)) {
		if (text === undefined && rawName === undefined) continue;
		if (text !== undefined) {
			if (skip !== undefined) continue;
			const read = decode(text);
			if (read === '') continue;
			if (crossed && !index && before !== '') {
				const last = before.at(-1);
				const first = read[0];
				if (WORD.test(last) && WORD.test(first) && (DIGIT.test(last) || DIGIT.test(first))) {
					found.push({ before, after: read.slice(0, CONTEXT) });
				}
			}
			before = (before + read).slice(-CONTEXT);
			crossed = false;
			index = false;
			continue;
		}
		const name = rawName.toLowerCase();
		const closing = slash === '/';
		const empty = VOID.has(name) || /\/\s*$/.test(attributes);
		if (skip !== undefined) {
			if (name === skip && !empty) depth += closing ? -1 : 1;
			if (depth === 0) {
				if (DRAWING.has(skip)) crossed = true;
				else reset();
				skip = undefined;
			}
			continue;
		}
		if (DRAWING.has(name)) {
			crossed = true;
			if (!closing && !empty) {
				skip = name;
				depth = 1;
			}
			continue;
		}
		if (!closing && !empty && (OPAQUE.has(name) || isMaths(attributes))) {
			skip = name;
			depth = 1;
			reset();
			continue;
		}
		if (TRANSPARENT.has(name)) continue;
		if (SEPARATE.has(name)) {
			reset();
			continue;
		}
		crossed = true;
		if (INDEX.has(name)) index = true;
	}
	return found;
}
