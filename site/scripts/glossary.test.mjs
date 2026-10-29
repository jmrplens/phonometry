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
// The DefinedTerm is named by the entry's `quantity`, which every entry
// carries in both languages; it used to be named by its symbol alone.
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
 * The places a definition opens: its first words and, when it opens with a
 * name and a colon, the first words after the colon, which is where "the same
 * construction" hid behind "Day-night level:".
 */
function openings(definition) {
	const colon = definition.indexOf(': ');
	const sentence = definition.search(/[.!?]\s/);
	const lead = colon > 0 && (sentence < 0 || colon < sentence);
	return lead ? [definition, definition.slice(colon + 2)] : [definition];
}

test('the openings a definition is read at include the words after its name', () => {
	assert.deepEqual(openings('Day-night level: the same construction.'), [
		'Day-night level: the same construction.',
		'the same construction.',
	]);
	assert.deepEqual(openings('The same integral. It is: plain.'), ['The same integral. It is: plain.']);
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
