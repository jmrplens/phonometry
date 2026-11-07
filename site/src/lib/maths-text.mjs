/**
 * Inline maths as plain text.
 *
 * The glossary writes its notation the way the page reads it, `$L_{Aeq}$, SEL`:
 * text, with inline maths between dollar signs. KaTeX typesets the maths on
 * the page, and everything that carries plain text instead (the structured
 * data, the symbol index) needs the same thing as characters: `$L_\mathrm{Aeq}$`
 * is the "LAeq" a search engine matches against a query, not the TeX that
 * produced it.
 *
 * A command stands for a character, a word or some space, and it is replaced
 * by that, never dropped. Dropping commands is what the glossary's own copy of
 * this step used to do, and the structured data read wrong in four ways: the
 * nine terms whose whole symbol is a Greek letter had an empty name,
 * "$K_{2\mathrm{A}} \le 4$ dB" read "K2A  4 dB", the thin space `\,` came out
 * as a comma beside a decimal comma ("2,2/(f,ηtot)"), and `10^{-5}` read
 * "10-5", the exponent glued to its base. So a command missing from the tables
 * below stops the build with its name, rather than leaving a hole in the text.
 *
 * What the text keeps of the typesetting:
 * - a subscript is written after its base, as the codes are ("LAeq");
 * - a superscript is written in superscript characters when every character
 *   of it has one (cos²φ, 10⁻⁵) and as `^x` or `^(...)` otherwise, so an
 *   exponent is never read as a factor;
 * - a relation or a binary operator gets a space on each side, as TeX gives it
 *   one, except inside a sub- or superscript and where a sign is unary;
 * - a named function (log, ln, cos ...) is kept apart from a number or a
 *   letter beside it ("-10 log10 τ", "L ln n");
 * - the spaces of the source are kept, but TeX swallows the one after a
 *   command, so `\Delta t` is "Δt";
 * - text outside the dollar signs is left exactly as written.
 *
 * Shared by src/components/Glossary.astro and scripts/maths-text.test.mjs,
 * which runs it over every string of the glossary. Written as .mjs with JSDoc
 * so that the test imports it under plain Node.
 */

/**
 * Greek letters, as the character a reader is actually holding: someone
 * looking for the sigma on a datasheet has to find a term that says σ.
 */
export const GREEK = Object.freeze({
	alpha: 'α', beta: 'β', gamma: 'γ', Gamma: 'Γ', delta: 'δ', Delta: 'Δ',
	epsilon: 'ε', varepsilon: 'ε', zeta: 'ζ', eta: 'η', theta: 'θ', vartheta: 'ϑ',
	Theta: 'Θ', iota: 'ι', kappa: 'κ', lambda: 'λ', Lambda: 'Λ', mu: 'µ', nu: 'ν',
	xi: 'ξ', Xi: 'Ξ', pi: 'π', Pi: 'Π', rho: 'ρ', varrho: 'ϱ', sigma: 'σ',
	Sigma: 'Σ', tau: 'τ', upsilon: 'υ', phi: 'φ', varphi: 'φ', Phi: 'Φ', chi: 'χ',
	psi: 'ψ', Psi: 'Ψ', omega: 'ω', Omega: 'Ω',
});

/** The Greek characters above, which the symbol index files under a letter of their own. */
export const GREEK_LETTERS = new Set(Object.values(GREEK));

/** Symbols that are neither letters nor operators. */
const SYMBOLS = Object.freeze({ infty: '∞', partial: '∂', nabla: '∇', prime: '′', ell: 'ℓ' });

/** Relations, always spaced. */
const RELATIONS = Object.freeze({
	le: '≤', leq: '≤', ge: '≥', geq: '≥', ne: '≠', neq: '≠', approx: '≈',
	sim: '∼', simeq: '≃', equiv: '≡', propto: '∝', to: '→', rightarrow: '→',
});

/** Binary operators, spaced unless they open the formula or follow another operator. */
const BINARY = Object.freeze({ pm: '±', mp: '∓', times: '×', cdot: '·', div: '÷' });

/** Named functions, set as their name. */
const FUNCTIONS = new Set([
	'log', 'lg', 'ln', 'exp', 'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh',
	'arcsin', 'arccos', 'arctan', 'max', 'min', 'lim', 'det', 'arg',
]);

/** Commands that set their argument in another font: the argument is the text. */
const FONTS = new Set(['mathrm', 'mathit', 'mathbf', 'mathsf', 'mathtt', 'mathcal', 'boldsymbol']);

/** Commands whose argument is text, taken as written. */
const TEXT = new Set(['text', 'textrm', 'textit', 'textbf', 'mbox']);

/** Spacing commands. `\!` is a negative thin space and takes nothing away from text. */
const SPACES = Object.freeze({ ',': ' ', ':': ' ', ';': ' ', ' ': ' ', '!': '', quad: ' ', qquad: ' ' });

/** Escaped characters that stand for themselves. */
const ESCAPED = Object.freeze({ '%': '%', '&': '&', '#': '#' });

/** Characters whose superscript form every font a reader has carries. */
const SUPERSCRIPT = Object.freeze({
	0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶', 7: '⁷', 8: '⁸', 9: '⁹',
	'+': '⁺', '-': '⁻', '−': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
});

/** How many arguments the commands that take any read. */
const ARITY = Object.freeze({
	...Object.fromEntries([...FONTS, ...TEXT, 'operatorname', 'sqrt'].map((name) => [name, 1])),
	frac: 2,
});

/** How many arguments a command reads, none for one that reads none. */
const arity = (name) => (Object.hasOwn(ARITY, name) ? ARITY[name] : 0);

/** Relations written as plain characters. */
const RELATION_CHARACTERS = new Set(['=', '<', '>']);

/** Signs written as plain characters, binary or unary by what comes before them. */
const SIGN_CHARACTERS = new Set(['+', '-', '−']);

/**
 * @typedef {object} Atom
 * @property {string} text What the atom reads as.
 * @property {'ord' | 'bin' | 'rel' | 'op' | 'space'} kind How TeX spaces it:
 *   an ordinary symbol, a binary operator, a relation, a named function, or
 *   space written in the source.
 */

/**
 * The index of the brace that closes the one at `open`.
 *
 * @param {string} tex The formula.
 * @param {number} open Index of an opening brace.
 * @returns {number} Index of its closing brace.
 */
function closing(tex, open) {
	let depth = 0;
	for (let i = open; i < tex.length; i += 1) {
		if (tex[i] === '\\') i += 1;
		else if (tex[i] === '{') depth += 1;
		else if (tex[i] === '}') {
			depth -= 1;
			if (depth === 0) return i;
		}
	}
	throw new Error(`maths-text: an unbalanced brace in "${tex}"`);
}

/**
 * A superscript as text: in superscript characters when each has one, and
 * after a caret otherwise, in brackets unless it is a single word or number.
 *
 * @param {string} text The superscript, already read as text.
 * @returns {string} What follows the base.
 */
function superscript(text) {
	const characters = [...text];
	if (characters.length > 0 && characters.every((character) => Object.hasOwn(SUPERSCRIPT, character))) {
		return characters.map((character) => SUPERSCRIPT[character]).join('');
	}
	return /^[\p{L}\p{N}.,′']+$/u.test(text) ? `^${text}` : `^(${text})`;
}

/**
 * Whether a sign at this point is binary: TeX makes it unary at the start of a
 * formula and after an operator, a relation, a function or an opening bracket.
 *
 * @param {Atom[]} atoms The atoms read so far.
 * @returns {boolean} True when the sign joins two operands.
 */
function signIsBinary(atoms) {
	const previous = atoms.findLast((atom) => atom.kind !== 'space');
	return previous !== undefined && previous.kind === 'ord' && !/[([{,]$/.test(previous.text);
}

/**
 * Read a formula, the text between the dollar signs, as atoms.
 *
 * @param {string} tex The formula.
 * @param {boolean} script Whether it is a sub- or superscript, where TeX puts
 *   no space around operators.
 * @returns {Atom[]} Its atoms, in order.
 */
function atomsOf(tex, script) {
	/** @type {Atom[]} */
	const atoms = [];
	let i = 0;

	/** The argument of a command or a script: a braced group or a single token. */
	const argument = () => {
		while (/\s/.test(tex[i] ?? '')) i += 1;
		if (i >= tex.length) throw new Error(`maths-text: a command or a script has no argument in "${tex}"`);
		if (tex[i] === '{') {
			const end = closing(tex, i);
			const inner = tex.slice(i + 1, end);
			i = end + 1;
			return inner;
		}
		const token =
			tex[i] === '\\' ? /^\\(?:[a-zA-Z]+|[\s\S])/.exec(tex.slice(i))[0] : String.fromCodePoint(tex.codePointAt(i));
		i += token.length;
		// `L_\mathrm{eq}`: a command taken as an argument brings its own
		// arguments with it, as TeX reads it.
		let taken = token;
		for (let n = arity(token.slice(1)); n > 0; n -= 1) taken += `{${argument()}}`;
		return taken;
	};

	/** The atom a script attaches to, which spaces in the source do not separate it from. */
	const base = () => {
		while (atoms.at(-1)?.kind === 'space') atoms.pop();
		if (atoms.length === 0) atoms.push({ text: '', kind: 'ord' });
		return atoms.at(-1);
	};

	while (i < tex.length) {
		const character = tex[i];
		if (character === '\\') {
			const [command, name] = /^\\([a-zA-Z]+|[\s\S])/.exec(tex.slice(i));
			i += command.length;
			// TeX reads the spaces after a control word as the end of its name.
			if (/^[a-zA-Z]/.test(name)) while (/\s/.test(tex[i] ?? '')) i += 1;
			if (Object.hasOwn(SPACES, name)) atoms.push({ text: SPACES[name], kind: 'space' });
			else if (Object.hasOwn(GREEK, name)) atoms.push({ text: GREEK[name], kind: 'ord' });
			else if (Object.hasOwn(SYMBOLS, name)) atoms.push({ text: SYMBOLS[name], kind: 'ord' });
			else if (Object.hasOwn(ESCAPED, name)) atoms.push({ text: ESCAPED[name], kind: 'ord' });
			else if (Object.hasOwn(RELATIONS, name)) atoms.push({ text: RELATIONS[name], kind: 'rel' });
			else if (Object.hasOwn(BINARY, name)) atoms.push({ text: BINARY[name], kind: signIsBinary(atoms) ? 'bin' : 'ord' });
			else if (FUNCTIONS.has(name)) atoms.push({ text: name, kind: 'op' });
			else if (name === 'operatorname') atoms.push({ text: textOf(argument(), script), kind: 'op' });
			else if (FONTS.has(name)) atoms.push({ text: textOf(argument(), script), kind: 'ord' });
			else if (TEXT.has(name)) atoms.push({ text: argument(), kind: 'ord' });
			else if (name === 'sqrt') {
				let index = '';
				if (tex[i] === '[') {
					const end = tex.indexOf(']', i);
					if (end < 0) throw new Error(`maths-text: an unclosed root index in "${tex}"`);
					index = superscript(textOf(tex.slice(i + 1, end), true));
					i = end + 1;
				}
				const radicand = textOf(argument(), script);
				atoms.push({ text: `${index}√${[...radicand].length === 1 ? radicand : `(${radicand})`}`, kind: 'ord' });
			} else if (name === 'frac') {
				const bracketed = (text) => (/^[\p{L}\p{N}.,′']+$/u.test(text) ? text : `(${text})`);
				const numerator = bracketed(textOf(argument(), script));
				const denominator = bracketed(textOf(argument(), script));
				atoms.push({ text: `${numerator}/${denominator}`, kind: 'ord' });
			} else {
				throw new Error(
					`maths-text: no text form for \\${name} in "${tex}"; add it to the tables in src/lib/maths-text.mjs`,
				);
			}
		} else if (character === '{') {
			const end = closing(tex, i);
			atoms.push({ text: textOf(tex.slice(i + 1, end), script), kind: 'ord' });
			i = end + 1;
		} else if (character === '}') {
			throw new Error(`maths-text: an unbalanced brace in "${tex}"`);
		} else if (character === '^' || character === '_') {
			i += 1;
			const target = base();
			const text = textOf(argument(), true);
			target.text += character === '^' ? superscript(text) : text;
		} else if (/\s/.test(character)) {
			if (atoms.at(-1)?.kind !== 'space') atoms.push({ text: ' ', kind: 'space' });
			i += 1;
		} else {
			const glyph = String.fromCodePoint(tex.codePointAt(i));
			i += glyph.length;
			if (RELATION_CHARACTERS.has(glyph)) atoms.push({ text: glyph, kind: 'rel' });
			else if (SIGN_CHARACTERS.has(glyph)) atoms.push({ text: glyph, kind: signIsBinary(atoms) ? 'bin' : 'ord' });
			else atoms.push({ text: glyph, kind: 'ord' });
		}
	}
	return atoms;
}

/**
 * A formula as text.
 *
 * @param {string} tex The formula, without its dollar signs.
 * @param {boolean} script Whether it is a sub- or superscript.
 * @returns {string} The text it reads as.
 */
function textOf(tex, script) {
	const atoms = atomsOf(tex, script);
	let text = '';
	atoms.forEach((atom, k) => {
		if ((atom.kind === 'bin' || atom.kind === 'rel') && !script) {
			text += ` ${atom.text} `;
		} else if (atom.kind === 'op') {
			// "-10 log10", "L ln n": a function name never runs into the number
			// or the letter on either side of it.
			if (/[\p{L}\p{N})]$/u.test(text)) text += ' ';
			text += atom.text;
			const next = atoms.slice(k + 1).find((other) => other.kind !== 'space');
			if (next?.kind === 'ord' && /^[\p{L}\p{N}]/u.test(next.text)) text += ' ';
		} else {
			text += atom.text;
		}
	});
	if (script) return text;
	return text
		.replace(/\s+/g, ' ')
		.replace(/([([]) /g, '$1')
		.replace(/ ([)\]])/g, '$1')
		.trim();
}

/**
 * A string of the glossary as plain text: each `$...$` run read as text, and
 * the text around it left as it is.
 *
 * @param {string} source Text with inline maths.
 * @returns {string} The same text with the maths written out.
 */
export function plainText(source) {
	return source
		.split(/(\$[^$]+\$)/g)
		.map((run) => (run.length > 1 && run.startsWith('$') && run.endsWith('$') ? textOf(run.slice(1, -1), false) : run))
		.join('');
}
