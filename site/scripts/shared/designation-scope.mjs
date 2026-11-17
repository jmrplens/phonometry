// The designations the landing page lists for each area, held to the same
// scope in English and in Spanish.
//
// The two landing pages (src/data/home.ts) list, area by area, the standards
// implemented there, and src/data/scope.mjs makes the site-wide graph's
// `featureList` and `keywords` of every page from those lists. A designation
// is mostly the same in both languages, "ISO 9613-2" is not translated, but a
// few are written in the page's own words ("ICAO Annex 16", "Anexo 16 OACI"),
// and one of those carried a scope limit in English that the Spanish never
// got: "CNOSSOS-EU (2002/49/EC Annex II, 2.2 and 2.3)" against
// "CNOSSOS-EU (Directiva 2002/49/CE, anexo II)", the whole annex claimed on
// the Spanish home and in the graph every page carries. Comparing the two lists
// as written cannot tell a translation from a scope that differs, so each
// designation is read as the words and numbers it names, the language's own
// words for the same thing read as one, and the two lists of an area must
// name the same things.

/**
 * The words a designation writes in one language for what the other writes
 * in its own, each read as the English one. A word that only names the kind
 * of document ("Directiva" before "2002/49/CE") reads as nothing: the English
 * designation names the directive by its number alone.
 */
const SAME_WORD = new Map([
	['anexo', 'annex'],
	['parte', 'part'],
	['oaci', 'icao'],
	['ce', 'ec'],
	['ue', 'eu'],
	['y', 'and'],
	['directiva', ''],
	['directive', ''],
]);

/**
 * What a designation names, in order: its words and numbers, lower case, the
 * dot of a section number kept ("2.2") and every word read as its English
 * one. Punctuation and parentheses carry nothing.
 *
 * @param {string} designation As a landing page lists it.
 * @returns {string[]}
 */
export function namedBy(designation) {
	return designation
		.toLowerCase()
		.split(/[^\p{L}\p{N}.]+/u)
		.map((token) => token.replace(/^\.+|\.+$/g, ''))
		.filter(Boolean)
		.map((token) => (SAME_WORD.has(token) ? SAME_WORD.get(token) : token))
		.filter(Boolean);
}

/** The same tokens whatever their order: "Anexo 16 OACI" names what "ICAO Annex 16" does. */
const asSet = (designation) => namedBy(designation).sort().join(' ');

/**
 * Every area whose designations do not name the same things in the two
 * languages, with the designations that differ.
 *
 * The areas are paired by their place on the page, as the landing pages list
 * them in one order; an area whose two rows link different sections, or a
 * page that lists more areas than the other, is a defect of its own.
 *
 * @param {{name: string, href: string, standards: string[]}[]} english
 * @param {{name: string, href: string, standards: string[]}[]} spanish
 * @returns {string[]}
 */
export function scopeDefects(english, spanish) {
	const defects = [];
	if (english.length !== spanish.length) {
		defects.push(`the English landing page lists ${english.length} areas and the Spanish one ${spanish.length}`);
	}
	const count = Math.min(english.length, spanish.length);
	for (let i = 0; i < count; i += 1) {
		const en = english[i];
		const es = spanish[i];
		if (en.href.replace('/es/', '/') !== es.href.replace('/es/', '/')) {
			defects.push(`area ${i + 1}: "${en.name}" links ${en.href} and "${es.name}" links ${es.href}`);
			continue;
		}
		const left = new Map(en.standards.map((designation) => [asSet(designation), designation]));
		const right = new Map(es.standards.map((designation) => [asSet(designation), designation]));
		const onlyEnglish = [...left].filter(([key]) => !right.has(key)).map(([, designation]) => designation);
		const onlySpanish = [...right].filter(([key]) => !left.has(key)).map(([, designation]) => designation);
		if (onlyEnglish.length > 0 || onlySpanish.length > 0) {
			defects.push(
				`"${en.name}" / "${es.name}": ` +
					[
						...onlyEnglish.map((designation) => `English ${JSON.stringify(designation)} names ${JSON.stringify(namedBy(designation).join(' '))}`),
						...onlySpanish.map((designation) => `Spanish ${JSON.stringify(designation)} names ${JSON.stringify(namedBy(designation).join(' '))}`),
					].join('; ') +
					', and the other language names nothing the same',
			);
		}
	}
	return defects;
}
