// The label of a header chip is the family of the document a reader knows.
//
// src/lib/reference-chips.ts reduces a standard's designation, or a report's
// number, to the family the chip under a page's title shows: the parts of one
// standard collapse onto one chip, and its year and part number go. A report
// number is not a designation, and a four-digit serial at its end was cut as if
// it were a year, so the RANDI report's chip read "NRL/FR/7176-" and NASA's
// contractor report "NASA CR". These tests hold the reduction to the families
// the function's own comment promises and to the report numbers the pages cite.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { standardFamily } from '../src/lib/reference-chips.ts';

test('a standard loses its year, its part and its edition, and keeps its number', () => {
	for (const [designation, family] of [
		['ISO 10140-2:2010', 'ISO 10140'],
		['ANSI S3.5-1997 (R2017)', 'ANSI S3.5'],
		['ANSI/ASA S12.2-2019', 'ANSI/ASA S12.2'],
		['ANSI S1.4-1983', 'ANSI S1.4'],
		['Recommendation ITU-R BS.468-4', 'ITU-R BS.468'],
		['IEC 60118-4:2014+AMD1:2017', 'IEC 60118'],
		['ECAC.CEAC Doc 29, 4th ed.', 'ECAC.CEAC Doc 29'],
	]) {
		assert.equal(standardFamily(designation), family, designation);
	}
});

test('a report keeps the serial it is numbered by, four digits or three', () => {
	for (const [number, family] of [
		['NRL/FR/7176--95-9628', 'NRL/FR/7176--95-9628'],
		['NASA CR-3406', 'NASA CR-3406'],
		['DHHS/NIOSH Publication No. 98-126', 'DHHS/NIOSH Publication No. 98-126'],
		['Technical Report 3026', 'Technical Report 3026'],
		['EUR 25379 EN', 'EUR 25379 EN'],
	]) {
		assert.equal(standardFamily(number), family, number);
	}
});

test('no family ends on the hyphen a cut tail leaves behind', () => {
	for (const number of ['NRL/FR/7176--95-9628', 'A--95-1234', 'B-2-3456']) {
		assert.doesNotMatch(standardFamily(number), /-$/, number);
	}
});
