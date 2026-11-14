// What the glossary's data has to hold for each term to read on its own.
//
// A definition in src/data/glossary.mjs is read in two places: on the page,
// one card after another, and in the structured data, where it is the
// `description` of a DefinedTerm that a search engine or an assistant quotes
// with no neighbour beside it. Five definitions opened by pointing at the card
// before them, "The same integral applied to the A-weighted signal" for LAeq,
// "The same extrapolation" for T30, "The same reference-curve rating" for
// Dn,e,w, "The same global index" for DnT,A and "The extended measure" for
// ESTOI, and their Spanish twins did the same; four more did it right after
// the name they open with ("Day-night level: the same construction ...").
// Each read correctly under its neighbour and named nothing in the
// structured data.
//
// Leaning on the card above can also happen in the middle of a sentence:
// "Everything else in this group is a ratio of these", "Table B.3 of the same
// standard", "read off the same regression line". Six definitions did, and
// the phrases they used are held here wherever they stand.
//
// The DefinedTerm is named by the entry's `quantity`, which every entry
// carries in both languages; it used to be named by its symbol alone. Every
// definition carries that name, so the name a search result shows is one the
// reader then finds on the card: 27 definitions in each language did not, and
// "G frequency weighting" was named over a card that said "Infrasound
// weighting".
//
// A field is text with inline maths in `$...$` and nothing else: the card
// prints the rest as typed, and the structured data quotes it. Two
// definitions wrote Markdown, "*before*" for the harmonic transfer function
// and "the `ls` subscript" for the loudspeaker facade rating, and the card
// and the DefinedTerm both showed the asterisks and the backticks.
//
// A quantity that is a reduction, a difference or a loss is defined as that,
// not as a level: RA, the A-weighted global sound reduction index of DB-HR,
// was defined as "the A-weighted level a partition transmits", the opposite
// quantity (51.4 dBA for the index of the guide's worked example, -51.4 dBA
// for the level it transmits under the normalised spectrum).
//
// A standard that rates octave bands by a rule of its own has it stated
// where a definition gives the one-third-octave rule. ISO 717-2 reads the
// shifted curve at 500 Hz for one-third octaves (4.3.1) and takes 5 dB off
// that reading for octaves (4.3.2); the impact ratings were defined by the
// 500 Hz reading alone, which rates an octave-band field measurement 5 dB
// too high, and CI by its one-third-octave range alone (A.2.1 sums the
// octaves 125 Hz to 2000 Hz).
//
// These tests read the data the page and the structured data are both built
// from, so they fail before a build does. check-structured-data.mjs holds the
// built nodes to the same names.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { glossary } from '../src/data/glossary.mjs';

const TERMS = glossary.flatMap((group) => group.terms);
const LANGUAGES = ['en', 'es'];

/**
 * Openings that lean on another entry: "the same" whatever, "likewise", "as
 * above", "the extended measure", and their Spanish counterparts. A sentence
 * that opens this way says nothing until the reader has the entry it points
 * at.
 */
const BACK_REFERENCE = {
	en: /^(?:the same|same|likewise|similarly|as above|as before|ditto|idem|the previous|the preceding|the former|the latter|the extended|the other)\b/i,
	es: /^(?:(?:el|la|lo|los|las) mism[oa]s?|igualmente|análogamente|asimismo|del mismo modo|de igual modo|como arriba|como antes|ídem|(?:el|la|lo) anterior|la versión extendida|(?:el|la) otr[oa])(?![\p{L}\p{N}])/iu,
};

/**
 * Phrases that lean on another entry wherever they stand in a definition: the
 * group or the family the card sits in, left unnamed, "the same standard"
 * another card names, the card above. A family the definition names, "the
 * junction family", is not leaning on anything. Each one is a phrase a
 * definition of this glossary used; "the same" on its own is not on the list,
 * because a definition says "the same mean-square pressure" or "the same
 * four-stage filter" of itself.
 */
const LEANING_PHRASE = {
	en: /\b(?:this group|the whole group|the (?:whole )?family(?! of)|everything else in|the same standard|the same regression line|the modulation form|the (?:card|entry) above)\b/i,
	es: /(?<![\p{L}\p{N}])(?:este grupo|todo el grupo|toda la familia(?! de)|todo lo demás de|la misma norma|la misma recta de regresión|la forma por modulación|la (?:tarjeta|entrada) anterior)(?![\p{L}\p{N}])/iu,
};

/**
 * The places a definition opens: its first words and, when its first sentence
 * opens with a name followed by a colon or a comma, the first words after
 * them, which is where "the same construction" hid behind "Day-night level:".
 * Only the first sentence is split: a later one that opens "The same clause"
 * is speaking of the entry's own standard.
 */
function openings(definition) {
	const sentence = definition.search(/[.!?]\s/);
	const leads = [];
	for (const separator of [': ', ', ']) {
		const at = definition.indexOf(separator);
		if (at > 0 && (sentence < 0 || at < sentence)) leads.push(definition.slice(at + separator.length));
	}
	return [definition, ...leads];
}

test('the openings a definition is read at include the words after its name', () => {
	assert.deepEqual(openings('Day-night level: the same construction.'), [
		'Day-night level: the same construction.',
		'the same construction.',
	]);
	assert.deepEqual(openings('Day-night level, the same construction.'), [
		'Day-night level, the same construction.',
		'the same construction.',
	]);
	assert.deepEqual(openings('The same integral. It is: plain.'), ['The same integral. It is: plain.']);
	assert.deepEqual(openings('Spread over a band. The same clause, then.'), ['Spread over a band. The same clause, then.']);
});

test('the back-reference patterns recognise the openings the glossary used to have', () => {
	const old = {
		en: [
			'The same integral applied to the A-weighted signal',
			'the same construction with the 10 dB night penalty only.',
			'The extended measure, row- and column-normalised',
		],
		es: [
			'La misma integral aplicada a la señal ponderada A',
			'El mismo índice global aplicado a una diferencia de niveles',
			'la misma relación con la frontera en 80 ms.',
			'La versión extendida, normalizada por filas',
		],
	};
	for (const lang of LANGUAGES) {
		for (const opening of old[lang]) assert.match(opening, BACK_REFERENCE[lang], `${lang}: ${opening}`);
	}
	// A definition that names its own quantity is not caught by the word "same"
	// later on.
	assert.doesNotMatch('the level of the steady sound carrying the same mean-square pressure', BACK_REFERENCE.en);
	assert.doesNotMatch('el nivel del sonido estacionario que transporta la misma presión', BACK_REFERENCE.es);
});

test('the leaning phrases recognise the six the glossary used to have, and not a definition speaking of itself', () => {
	const old = {
		en: [
			'Everything else in this group is a ratio of these',
			'It is the quantity the whole group is a logarithm of',
			'displacement response per unit force, the pivot the whole family converts through.',
			'Table B.3 of the same standard gives 0,005 for concrete',
			'read off the same regression line rather than measured at that distance',
			'Its test signal and its products are both different from the modulation form',
		],
		es: [
			'Todo lo demás de este grupo es un cociente de estas magnitudes',
			'Es la magnitud de la que es logaritmo todo el grupo',
			'el pivote por el que convierte toda la familia.',
			'la tabla B.3 de la misma norma da 0,005 para el hormigón',
			'leído sobre la misma recta de regresión y no medido a esa distancia',
			'Tanto su señal de ensayo como sus productos difieren de la forma por modulación',
		],
	};
	for (const lang of LANGUAGES) {
		for (const phrase of old[lang]) assert.match(phrase, LEANING_PHRASE[lang], `${lang}: ${phrase}`);
	}
	for (const phrase of [
		'one parameter row each of the same four-stage filter',
		'the transmission loss is the same logarithm',
		'AES17 reuses the same curve with an r.m.s. detector',
		'The same clause gives the tolerance',
		'Noise rating, the European counterpart curve family of NC.',
		'the single number the difference-frequency family reports',
		'the wave-approach quantity the junction family bottoms out in',
	]) {
		assert.doesNotMatch(phrase, LEANING_PHRASE.en, phrase);
	}
	assert.doesNotMatch('El mismo apartado da la tolerancia', LEANING_PHRASE.es);
	assert.doesNotMatch('en la que se apoya toda la familia de uniones', LEANING_PHRASE.es);
});

test('no definition opens by pointing at another entry, in either language', () => {
	const leaning = [];
	for (const term of TERMS) {
		for (const lang of LANGUAGES) {
			for (const opening of openings(term.definition[lang])) {
				if (BACK_REFERENCE[lang].test(opening)) leaning.push(`${term.id} (${lang}): "${opening.slice(0, 50)}"`);
			}
		}
	}
	assert.deepEqual(leaning, [], `definitions that lean on another entry:\n${leaning.join('\n')}`);
});

test('no definition leans on its group, its family or the card above, wherever it says so', () => {
	const leaning = [];
	for (const term of TERMS) {
		for (const lang of LANGUAGES) {
			const found = LEANING_PHRASE[lang].exec(term.definition[lang]);
			if (found) leaning.push(`${term.id} (${lang}): "${found[0]}"`);
		}
	}
	assert.deepEqual(leaning, [], `definitions that lean on another entry:\n${leaning.join('\n')}`);
});

test('every definition carries the name of its quantity, in either language', () => {
	const unnamed = [];
	for (const term of TERMS) {
		for (const lang of LANGUAGES) {
			const name = term.quantity?.[lang];
			if (typeof name === 'string' && !term.definition[lang].toLowerCase().includes(name.toLowerCase())) {
				unnamed.push(`${term.id} (${lang}): ${JSON.stringify(name)} is not in "${term.definition[lang].slice(0, 60)}"`);
			}
		}
	}
	assert.deepEqual(unnamed, [], `definitions that never say what they define:\n${unnamed.join('\n')}`);
});

test('an alias belongs to an entry named rather than symbolised, and is another name than its quantity', () => {
	const wrong = [];
	for (const term of TERMS.filter((entry) => entry.alias !== undefined)) {
		if (term.symbol !== undefined) wrong.push(`${term.id}: has a symbol, which is its alternate name already`);
		for (const lang of LANGUAGES) {
			const declared = typeof term.alias === 'object' && !Array.isArray(term.alias) ? term.alias[lang] : term.alias;
			for (const alias of [declared].flat()) {
				if (typeof alias !== 'string' || alias.trim() === '' || alias !== alias.trim() || alias.includes('$')) {
					wrong.push(`${term.id} (${lang}): ${JSON.stringify(alias)} is not a name in words`);
				} else if (alias.toLowerCase() === term.quantity[lang].toLowerCase()) {
					wrong.push(`${term.id} (${lang}): ${JSON.stringify(alias)} is its quantity`);
				}
			}
		}
	}
	assert.deepEqual(wrong, [], wrong.join('\n'));
});

test('every entry names its quantity in both languages, in words', () => {
	const missing = [];
	for (const term of TERMS) {
		for (const lang of LANGUAGES) {
			const name = term.quantity?.[lang];
			if (typeof name !== 'string' || name.trim() === '') missing.push(`${term.id} (${lang}): no quantity`);
			else if (name !== name.trim() || name.includes('$') || /[.:;]$/.test(name)) {
				missing.push(`${term.id} (${lang}): ${JSON.stringify(name)} is not a bare name`);
			}
		}
	}
	assert.deepEqual(missing, [], missing.join('\n'));
	assert.ok(TERMS.length > 0, 'the glossary has no terms');
});

/** Every string an entry holds, with the field it is in, in each language it is given in. */
function* stringsOf(term) {
	const walk = function* (value, where) {
		if (typeof value === 'string') yield [where, value];
		else if (Array.isArray(value)) for (const item of value) yield* walk(item, where);
		else if (value !== null && typeof value === 'object') {
			for (const [key, item] of Object.entries(value)) yield* walk(item, `${where}.${key}`);
		}
	};
	for (const [field, value] of Object.entries(term)) yield* walk(value, field);
}

/** What a field writes outside its inline maths, which the card prints as typed. */
const outsideMaths = (text) =>
	text
		.split(/(\$[^$]+\$)/)
		.filter((_, i) => i % 2 === 0)
		.join(' ');

test('no field writes Markdown outside its maths, which neither the card nor the structured data reads', () => {
	const marked = [];
	for (const term of TERMS) {
		for (const [where, text] of stringsOf(term)) {
			const found = /[*`]/.exec(outsideMaths(text));
			if (found) marked.push(`${term.id}.${where}: "${found[0]}" in "${text.slice(0, 70)}"`);
		}
	}
	assert.deepEqual(marked, [], `fields that write Markdown:\n${marked.join('\n')}`);
});

test('the Markdown a field may not write is found beside its maths, and not inside it', () => {
	assert.match(outsideMaths('places $L\\ln n$ seconds *before* the linear one'), /\*/);
	assert.match(outsideMaths('The `ls` subscript of $D_{ls}$'), /`/);
	assert.doesNotMatch(outsideMaths('the conjugate $G^*_{xy}$ of the cross spectrum'), /[*`]/);
});

test('no two entries share a quantity name in one language', () => {
	for (const lang of LANGUAGES) {
		const seen = new Map();
		const shared = [];
		for (const term of TERMS) {
			const name = term.quantity?.[lang];
			if (seen.has(name)) shared.push(`${JSON.stringify(name)}: ${seen.get(name)} and ${term.id}`);
			else seen.set(name, term.id);
		}
		assert.deepEqual(shared, [], `${lang}: ${shared.join('; ')}`);
	}
});

/**
 * The quantities that are a reduction, a difference, an insulation, a loss,
 * an attenuation or an improvement, by the words of their names.
 */
const REDUCTION = {
	en: /\b(?:reduction|difference|insulation|loss|attenuation|improvement)\b/i,
	es: /(?:reducci[oó]n|diferencia|aislamiento|p[eé]rdida|atenuaci[oó]n|mejora)/iu,
};

/** A sentence that opens on a level: "the A-weighted level", "el nivel". */
const ONE_LEVEL = { en: /^the\s+(?:[\p{L}\p{N}'’-]+\s+){0,3}level\b/iu, es: /^(?:el|un)\s+nivel\b/iu };

/** The words that make a sentence about levels one about their difference. */
const DIFFERENCE = { en: /\b(?:minus|difference|logarithm|less)\b/i, es: /(?:menos|diferencia|logaritmo)/iu };

/** The first sentence of a definition after the name it opens with. */
function firstSentenceAfterName(definition) {
	const colon = definition.indexOf(': ');
	const body = colon > 0 ? definition.slice(colon + 2) : definition;
	const end = body.search(/[.!?](?:\s|$)/);
	return end < 0 ? body : body.slice(0, end);
}

test('a reduction, a level difference, a loss or an attenuation is not defined as one level, in either language', () => {
	const wrong = [];
	let read = 0;
	for (const term of TERMS) {
		for (const language of LANGUAGES) {
			if (!REDUCTION[language].test(term.quantity[language])) continue;
			read += 1;
			const first = firstSentenceAfterName(term.definition[language]);
			if (ONE_LEVEL[language].test(first) && !DIFFERENCE[language].test(first)) {
				wrong.push(`${term.id} (${language}): ${first.slice(0, 60)}`);
			}
		}
	}
	assert.ok(read > 0, 'no quantity of this kind was read');
	assert.deepEqual(wrong, []);
});

/**
 * The standards whose print rates octave bands by a rule of its own, each
 * with what a definition can state that holds for one-third-octave bands
 * alone. ISO 717-2 reads the shifted curve at 500 Hz for one-third octaves
 * (4.3.1) and takes 5 dB off that reading for octaves (4.3.2), and sums CI
 * over 100 Hz to 2500 Hz or over the octaves 125 Hz to 2000 Hz (A.2.1, with
 * 50 Hz or the 63 Hz octave for the enlarged range). ISO 717-1 reads the
 * curve at 500 Hz for both (4.4), so there only the one-third-octave ranges
 * and the 32.0 dB sum are its own.
 */
const OCTAVE_RULE = [
	{ standard: /ISO 717-2/, thirdsOnly: /\b500 Hz|\b(?:50|100|2500|3150) Hz\b|\b32(?:[.,]0)? dB\b/ },
	{ standard: /ISO 717-1/, thirdsOnly: /\b(?:50|100|3150|5000) Hz\b|\b32(?:[.,]0)? dB\b/ },
];

/** Octave bands named as such, which "one-third-octave bands" does not do. */
const OCTAVE_BANDS = {
	en: /(?<!third[- ])\boctave(?:s\b|[- ]bands?\b)/i,
	es: /bandas? de octava|(?<!tercios? de )\boctavas\b/iu,
};

/** The standard an entry names in one language. */
const standardOf = (term, language) =>
	typeof term.standard === 'string' ? term.standard : (term.standard?.[language] ?? '');

test('octave bands are told apart from one-third-octave bands in either language', () => {
	assert.match('or over the octave bands 125 Hz to 2000 Hz', OCTAVE_BANDS.en);
	assert.match('a field measurement in octaves', OCTAVE_BANDS.en);
	assert.doesNotMatch('over eighteen one-third-octave bands', OCTAVE_BANDS.en);
	assert.doesNotMatch('the sixteen one-third octaves', OCTAVE_BANDS.en);
	assert.match('o en las bandas de octava de 125 Hz a 2000 Hz', OCTAVE_BANDS.es);
	assert.doesNotMatch('en las bandas de tercio de octava', OCTAVE_BANDS.es);
	assert.doesNotMatch('dieciséis tercios de octava', OCTAVE_BANDS.es);
});

test('a definition that states a rule of one-third-octave bands says what octave bands do, in either language', () => {
	const missing = [];
	let read = 0;
	for (const term of TERMS) {
		for (const language of LANGUAGES) {
			const rule = OCTAVE_RULE.find(({ standard }) => standard.test(standardOf(term, language)));
			const prose = outsideMaths(term.definition[language]);
			if (!rule || !rule.thirdsOnly.test(prose)) continue;
			read += 1;
			if (!OCTAVE_BANDS[language].test(prose)) {
				missing.push(`${term.id} (${language}): "${rule.thirdsOnly.exec(prose)[0]}" in ${prose.slice(0, 70)}`);
			}
		}
	}
	assert.ok(read > 0, 'no definition of a band-dependent rating was read');
	assert.deepEqual(missing, [], `definitions that give the one-third-octave rule alone:\n${missing.join('\n')}`);
});
