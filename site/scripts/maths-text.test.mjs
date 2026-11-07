// What src/lib/maths-text.mjs makes of the glossary's maths.
//
// The glossary's structured data and its symbol index carry the notation as
// plain text, and the step that writes it used to drop every command it met
// and turn the rest of the TeX into punctuation: nine terms whose symbol is a
// Greek letter had an empty name, "$K_{2\mathrm{A}} \le 4$ dB" read
// "K2A  4 dB", the thin space in "$2{,}2/(f\,\eta)$" became a comma beside a
// decimal comma, and "$10^{-5}$" read "10-5". None of it showed on the page,
// where KaTeX typesets the same strings, so nothing noticed.
//
// These tests pin what each construction becomes and then run the step over
// every string of the glossary, in both languages, for the defects that class
// produced.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { glossary } from '../src/data/glossary.mjs';
import { plainText } from '../src/lib/maths-text.mjs';

test('each construction the glossary writes reads as the text it stands for', () => {
	const cases = [
		// Subscripts follow their base, as the codes are written.
		['$L_\\mathrm{Aeq}$', 'LAeq'],
		['$L_{\\mathrm{A}E}$, SEL', 'LAE, SEL'],
		['$L_{p,\\mathrm{A,S},4\\,\\mathrm{m}}$', 'Lp,A,S,4 m'],
		['$C_{\\mathrm{I},50\\text{–}2500}$', 'CI,50–2500'],
		// A Greek letter is the letter, and TeX swallows the space after it.
		['$\\tau$', 'τ'],
		['$\\Delta R_\\mathrm{w}$', 'ΔRw'],
		['$\\alpha R$', 'αR'],
		// A relation or an operator is spaced, a unary sign is not.
		['valid where $K_{2\\mathrm{A}} \\le 4$ dB', 'valid where K2A ≤ 4 dB'],
		['$\\mathrm{SNR}/(1+\\mathrm{SNR})$', 'SNR/(1 + SNR)'],
		['$-1{,}5$ dB', '-1,5 dB'],
		['$+12{,}2$ dB', '+12,2 dB'],
		['$\\gamma^2_{iy\\cdot(i-1)!}$', 'γ²iy·(i-1)!'],
		// A thin space is a space, and a braced comma a decimal comma.
		['$T_\\mathrm{s} = 2{,}2/(f\\,\\eta_\\mathrm{tot})$', 'Ts = 2,2/(f ηtot)'],
		// An exponent never runs into its base.
		['$10^{-5}$', '10⁻⁵'],
		['$|G_{xy}|^2/(G_{xx}G_{yy})$', '|Gxy|²/(GxxGyy)'],
		['$1/\\cos^2\\varphi$', '1/cos² φ'],
		['$-10\\log_{10}(1 - 10^{-0,1\\Delta L_p})$', '-10 log10(1 - 10^(-0,1ΔLp))'],
		['$x^{1.75}$', 'x^1.75'],
		// A function name keeps clear of the number or letter beside it.
		['$R = -10\\log_{10}\\tau$', 'R = -10 log10 τ'],
		['$10\\log_{10}B$', '10 log10 B'],
		['$L\\ln n$', 'L ln n'],
		// A root and a fraction keep their operand together.
		['$c\\,\\Delta t\\sqrt{1/\\Delta x^2 + 1/\\Delta y^2}$', 'c Δt√(1/Δx² + 1/Δy²)'],
		['$\\frac{a+b}{2}$', '(a + b)/2'],
		// Text outside the dollar signs is left as written.
		['m/s^1.75', 'm/s^1.75'],
		['harmonic order $n$', 'harmonic order n'],
	];
	for (const [source, expected] of cases) assert.equal(plainText(source), expected, source);
});

test('a command with no text form stops the build with its name instead of vanishing', () => {
	assert.throws(() => plainText('$\\left( x \\right)$'), /no text form for \\left/);
	assert.throws(() => plainText('$\\constructor$'), /no text form for \\constructor/);
	assert.throws(() => plainText('$L_{p$'), /unbalanced brace/);
});

/** Every string of the glossary that is written to be read, in both languages. */
function glossaryStrings() {
	const strings = [];
	for (const term of glossary.flatMap((group) => group.terms)) {
		for (const field of ['symbol', 'name', 'quantity', 'alias', 'qualifier', 'unit', 'standard', 'clause', 'definition']) {
			const value = term[field];
			if (value === undefined) continue;
			const values = typeof value === 'object' && !Array.isArray(value) ? Object.entries(value) : [['both', value]];
			for (const [lang, text] of values) {
				for (const one of [text].flat()) strings.push({ where: `${term.id}.${field} (${lang})`, source: one });
			}
		}
	}
	return strings;
}

/** Characters the step writes for an exponent. */
const SUPERSCRIPT_RUN = /[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾]+/gu;

/** How many times `pattern` occurs in `text`. */
const count = (text, pattern) => (text.match(pattern) ?? []).length;

test('no string of the glossary comes out with TeX left, a hole, or a symbol turned into another', () => {
	const strings = glossaryStrings();
	assert.ok(strings.length > 1000, `only ${strings.length} strings read from the glossary`);
	const defects = [];
	for (const { where, source } of strings) {
		const text = plainText(source);
		const report = (what) => defects.push(`${where}: ${what}: ${JSON.stringify(text)}`);
		if (/[$\\{}_]/.test(text)) report('TeX left in the text');
		if (/\^(?![\p{L}\p{N}(])/u.test(text)) report('a caret with no exponent after it');
		// A thin space is a space: a comma in the text comes from a comma.
		if (count(text, /,/g) !== count(source, /,/g) - count(source, /\\,/g)) report('a comma that was a thin space');
		// Every exponent is either in superscript characters or after a caret,
		// beside the ones the text already writes that way ("m²").
		const exponents = (string) => count(string, /\^/g) + count(string, SUPERSCRIPT_RUN);
		if (exponents(source) !== exponents(text)) report('an exponent run into its base');
		if (/Δ \p{L}/u.test(text)) report('a space between Δ and what it applies to');
		if (/\s{2}|\s[,.;:)]|\(\s/.test(text)) report('a hole where something was dropped');
		if (source.trim() !== '' && text.trim() === '') report('nothing left at all');
	}
	assert.deepEqual(defects, [], defects.join('\n'));
});
