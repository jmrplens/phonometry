// scripts/shared/designation-scope.mjs holds the designations of each area of
// the landing page to the same scope in English and in Spanish. The landing
// pages only ever show it lists that agree, so each test hands it lists that
// do not, and lists that agree in other words.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { en, es } from '../../src/data/home.ts';
import { namedBy, scopeDefects } from './designation-scope.mjs';

const area = (name, href, standards) => ({ name, href, standards });

test('a designation names its words and numbers, each read as the English word', () => {
	assert.deepEqual(namedBy('CNOSSOS-EU (2002/49/EC Annex II, 2.2 and 2.3)'), [
		'cnossos', 'eu', '2002', '49', 'ec', 'annex', 'ii', '2.2', 'and', '2.3',
	]);
	assert.deepEqual(namedBy('CNOSSOS-EU (Directiva 2002/49/CE, anexo II, 2.2 y 2.3)'), [
		'cnossos', 'eu', '2002', '49', 'ec', 'annex', 'ii', '2.2', 'and', '2.3',
	]);
	assert.deepEqual(namedBy('Anexo 16 OACI'), ['annex', '16', 'icao']);
});

test('the two landing pages name the same designations in every area', () => {
	assert.deepEqual(scopeDefects(en.coverage.areas, es.coverage.areas), []);
});

test('a scope limit one language states and the other leaves out fails, naming both', () => {
	const defects = scopeDefects(
		[area('Environment and transport', '/phonometry/environment/', ['ISO 9613-2', 'CNOSSOS-EU (2002/49/EC Annex II, 2.2 and 2.3)'])],
		[area('Medio ambiente y transporte', '/phonometry/es/environment/', ['ISO 9613-2', 'CNOSSOS-EU (Directiva 2002/49/CE, anexo II)'])],
	);
	assert.equal(defects.length, 1);
	assert.match(defects[0], /^"Environment and transport" \/ "Medio ambiente y transporte": /);
	assert.match(defects[0], /English "CNOSSOS-EU \(2002\/49\/EC Annex II, 2\.2 and 2\.3\)" names "cnossos eu 2002 49 ec annex ii 2\.2 and 2\.3"/);
	assert.match(defects[0], /Spanish "CNOSSOS-EU \(Directiva 2002\/49\/CE, anexo II\)" names "cnossos eu 2002 49 ec annex ii"/);
});

test('a designation written in the page\'s own words, in another order, passes', () => {
	assert.deepEqual(
		scopeDefects(
			[area('Aircraft noise', '/phonometry/aircraft/', ['ICAO Annex 16', 'IEC 61094-2 Annex F'])],
			[area('Ruido de aeronaves', '/phonometry/es/aircraft/', ['Anexo 16 OACI', 'IEC 61094-2 Anexo F'])],
		),
		[],
	);
});

test('a designation one language lists and the other does not fails, and so does a part number', () => {
	const defects = scopeDefects(
		[area('Signal analysis', '/phonometry/signals/', ['IEC 61260-1', 'ISO 7196', 'IEC 61672-1'])],
		[area('Análisis de señal', '/phonometry/es/signals/', ['IEC 61260-1', 'IEC 61672-2'])],
	);
	assert.equal(defects.length, 1);
	assert.match(defects[0], /English "ISO 7196"/);
	assert.match(defects[0], /English "IEC 61672-1"/);
	assert.match(defects[0], /Spanish "IEC 61672-2"/);
});

test('areas that do not pair, by count or by the section they link, fail', () => {
	const one = area('Fluids', '/phonometry/fluids/', []);
	assert.deepEqual(scopeDefects([one, one], [one]), ['the English landing page lists 2 areas and the Spanish one 1']);
	assert.match(
		scopeDefects([one], [area('Sólidos', '/phonometry/es/solids/', [])])[0],
		/^area 1: "Fluids" links \/phonometry\/fluids\/ and "Sólidos" links \/phonometry\/es\/solids\//,
	);
});
