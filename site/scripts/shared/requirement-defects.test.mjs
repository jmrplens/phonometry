// What scripts/shared/requirement-defects.mjs makes of a softwareRequirements
// sentence.
//
// The structured-data check holds the software node's requirements to
// pyproject.toml, which gives each Python a floor of its own behind a
// `python_version` marker. These tests hand it the lines copied from that
// file and a table that gives every requirement one floor, so that a
// sentence that keeps every version but ties a floor to the wrong Python,
// drops the comparison of a marker, or states a longer version than the
// table fails on either shape.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { describeRequirements, readProject } from '../../src/lib/pyproject.mjs';
import { parseToml } from '../../src/lib/toml.mjs';
import { ONE_FLOOR, PER_PYTHON } from './pyproject-fixture.mjs';
import { requirementDefects } from './requirement-defects.mjs';

const oneFloor = readProject(parseToml(ONE_FLOOR));
const perPython = readProject(parseToml(PER_PYTHON));

const EXTRAS = '. Optional extras: perf, plot, report, audio and torch; full installs perf, plot, report and audio.';

/** The sentence the site writes from the per-Python lines, with its requirements as given. */
const perPythonSentence = (requirements) => `Python >= 3.12 with ${requirements}${EXTRAS}`;

/** The one failure line of a sentence that leaves `missing` out. */
const leavesOut = (missing) => [
	`SoftwareApplication softwareRequirements leaves out ${missing}, which pyproject.toml gives`,
];

test('the sentence the site writes from either table holds', () => {
	assert.deepEqual(requirementDefects(`Python >= 3.12 with numpy >= 2.0.2 and scipy >= 1.14.0${EXTRAS}`, oneFloor), []);
	assert.deepEqual(
		requirementDefects(
			perPythonSentence(
				'numpy >= 2.0.2 on Python < 3.13, numpy >= 2.1.0 on Python 3.13, numpy >= 2.3.2 on Python >= 3.14, ' +
					'scipy >= 1.14.0 on Python < 3.13, scipy >= 1.14.1 on Python 3.13 and scipy >= 1.16.1 on Python >= 3.14',
			),
			perPython,
		),
		[],
	);
	// The spaces are the site's to choose, and "==" may be written or left out.
	assert.deepEqual(
		requirementDefects(
			perPythonSentence(
				'NumPy>=2.0.2 on Python<3.13, numpy>=2.1.0 on Python == 3.13, numpy >= 2.3.2 on Python >=3.14, ' +
					'scipy >= 1.14.0 on Python < 3.13, scipy >= 1.14.1 on Python 3.13, scipy >= 1.16.1 on Python >= 3.14',
			),
			perPython,
		),
		[],
	);
	// And the sentence src/lib/pyproject.mjs writes from each table, so that
	// the writer is held to the check on the per-Python lines pyproject.toml
	// holds and on one floor per requirement, with no marker.
	for (const project of [oneFloor, perPython]) {
		assert.deepEqual(requirementDefects(describeRequirements(project), project), []);
	}
});

test("a marker stated without its comparison fails, naming each requirement it no longer states", () => {
	assert.deepEqual(
		requirementDefects(
			perPythonSentence(
				'numpy >= 2.0.2 on Python 3.13, numpy >= 2.1.0 on Python 3.13, numpy >= 2.3.2 on Python 3.14, ' +
					'scipy >= 1.14.0 on Python 3.13, scipy >= 1.14.1 on Python 3.13 and scipy >= 1.16.1 on Python 3.14',
			),
			perPython,
		),
		leavesOut(
			"numpy>=2.0.2 (python_version<'3.13'), numpy>=2.3.2 (python_version>='3.14'), " +
				"scipy>=1.14.0 (python_version<'3.13') and scipy>=1.16.1 (python_version>='3.14')",
		),
	);
});

test('a floor tied to the Python of another floor fails, though every version is in the sentence', () => {
	assert.deepEqual(
		requirementDefects(
			perPythonSentence(
				'numpy >= 2.0.2 on Python >= 3.14, numpy >= 2.1.0 on Python 3.13, numpy >= 2.3.2 on Python < 3.13, ' +
					'scipy >= 1.14.0 on Python >= 3.14, scipy >= 1.14.1 on Python 3.13 and scipy >= 1.16.1 on Python < 3.13',
			),
			perPython,
		),
		leavesOut(
			"numpy>=2.0.2 (python_version<'3.13'), numpy>=2.3.2 (python_version>='3.14'), " +
				"scipy>=1.14.0 (python_version<'3.13') and scipy>=1.16.1 (python_version>='3.14')",
		),
	);
});

test('a version that only starts with the one the table gives fails', () => {
	assert.deepEqual(
		requirementDefects(
			perPythonSentence(
				'numpy >= 2.0.20 on Python < 3.13, numpy >= 2.1.0 on Python 3.13, numpy >= 2.3.2 on Python >= 3.14, ' +
					'scipy >= 1.14.0 on Python < 3.13, scipy >= 1.14.1 on Python 3.13 and scipy >= 1.16.1 on Python >= 3.14',
			),
			perPython,
		),
		leavesOut("numpy>=2.0.2 (python_version<'3.13')"),
	);
	assert.deepEqual(
		requirementDefects(`Python >= 3.12 with numpy >= 2.0.2.1 and scipy >= 1.14.0${EXTRAS}`, oneFloor),
		leavesOut('numpy>=2.0.2'),
	);
	assert.deepEqual(
		requirementDefects(`Python >= 3.120 with numpy >= 2.0.2 and scipy >= 1.14.0${EXTRAS}`, oneFloor),
		leavesOut('requires-python >=3.12'),
	);
});

test('a requirement stated for some Pythons, which the table gives for every one, fails', () => {
	assert.deepEqual(
		requirementDefects(`Python >= 3.12 with numpy >= 2.0.2 on Python < 3.13 and scipy >= 1.14.0${EXTRAS}`, oneFloor),
		leavesOut('numpy>=2.0.2'),
	);
});

test('another operator, a name that only ends with the one given, and an extra left out fail', () => {
	assert.deepEqual(
		requirementDefects(
			'Python >= 3.12 with numpy > 2.0.2 and pyscipy >= 1.14.0. Optional extras: perf, plot, report and audio; full installs perf, plot, report and audio.',
			oneFloor,
		),
		leavesOut('numpy>=2.0.2, scipy>=1.14.0 and the extra torch'),
	);
	assert.deepEqual(requirementDefects(undefined, oneFloor), [
		'SoftwareApplication softwareRequirements is undefined, not a text naming what pyproject.toml requires',
	]);
});
