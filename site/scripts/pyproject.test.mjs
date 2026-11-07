// What src/lib/toml.mjs and src/lib/pyproject.mjs read out of pyproject.toml.
//
// The site states the package's Python floor, its install line and its
// requirements, and every one of them used to be typed by hand: the software
// node said "Python >= 3.12 with NumPy and SciPy (matplotlib and numba
// optional)", naming two of the five optional extras, the year after the
// other three were added. They are read from pyproject.toml now, by a reader
// small enough to run before the site's dependencies are installed, which is
// when these tests run.
//
// A hand reader of TOML that misreads a multi-line array or a marker writes a
// wrong requirement onto every page, so it is tested on the exact lines the
// file holds, which give each Python its own floor behind a `python_version`
// marker, and on a table that gives every requirement one floor, and its
// reading of the whole file is compared with Python's own TOML reader.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { parseToml } from '../src/lib/toml.mjs';
import {
	describeRequirements,
	installLine,
	parseRequirement,
	platformOf,
	pythonFloor,
	readProject,
} from '../src/lib/pyproject.mjs';
import { ONE_FLOOR, PER_PYTHON } from './shared/pyproject-fixture.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const PYPROJECT = join(here, '..', '..', 'pyproject.toml');

/**
 * What Python's own TOML reader makes of `text`, as JSON.
 *
 * The docs job runs these tests on the runner's python3, which is 3.12 there
 * and has tomllib, as every Python the package supports does.
 */
function tomllib(text) {
	const ran = spawnSync(
		'python3',
		['-I', '-c', 'import json, sys, tomllib; json.dump(tomllib.loads(sys.stdin.read()), sys.stdout)'],
		{ input: text, encoding: 'utf8' },
	);
	assert.equal(ran.status, 0, `python3 could not read the TOML: ${ran.stderr || ran.error}`);
	return JSON.parse(ran.stdout);
}

test("the lines that give every requirement one floor read as Python's TOML reader reads them", () => {
	const read = parseToml(ONE_FLOOR);
	assert.deepEqual(read, tomllib(ONE_FLOOR));
	assert.equal(read.project['requires-python'], '>=3.12');
	assert.deepEqual(read.project.dependencies, ['numpy>=2.0.2', 'scipy>=1.14.0']);
	assert.deepEqual(Object.keys(read.project['optional-dependencies']), [
		'perf',
		'plot',
		'report',
		'audio',
		'torch',
		'full',
	]);
	assert.deepEqual(read.project.authors, [{ name: 'José Manuel Requena Plens', email: 'mail@jmrp.io' }]);
});

test('the lines that give each Python a floor of its own read as Python reads them', () => {
	const read = parseToml(PER_PYTHON);
	assert.deepEqual(read, tomllib(PER_PYTHON));
	assert.equal(read.project.dependencies[1], "numpy>=2.1.0; python_version=='3.13'");
	assert.deepEqual(read.project['optional-dependencies'].report, ['reportlab>=4.3.0', 'svglib>=0.9.1,!=1.4.0']);
});

test('the whole of pyproject.toml reads as Python reads it', () => {
	const text = readFileSync(PYPROJECT, 'utf8');
	assert.deepEqual(parseToml(text), tomllib(text));
});

test('what an array, a string or a comment can hold reads as Python reads it', () => {
	const text = [
		'# a comment with "quotes", [brackets] and = signs',
		'[a]',
		'list = [ # a comment after the bracket',
		'    "x]y", # a bracket inside a string',
		"    'z#w',",
		'    [1, 2.5, -3, 1_000, 6e2],',
		'    { inline = true, "quoted key" = false },',
		'] # and after the array',
		'escaped = "tab\\there \\"quoted\\" \\u00e9"',
		'literal = \'C:\\path\\to\'',
		'multi = """',
		'two \\',
		'   lines"""',
		'raw = \'\'\'',
		'kept \\n as written\'\'\'',
		'dotted.key = "value"',
		'[[b.c]]',
		'n = 1',
		'[[b.c]]',
		'n = 2',
		'',
	].join('\n');
	assert.deepEqual(parseToml(text), tomllib(text));
});

test('what the reader cannot read stops it, with the line, rather than being misread', () => {
	const refusals = [
		['[project]\ndependencies = [\n    "numpy>=2.0.2",\n', /line 2: .*array/],
		['[project]\nname = "phonometry\n', /line 2: .*string/],
		['[project]\nreleased = 2026-01-06\n', /line 2: .*date/],
		['[project]\nname = "a"\nname = "b"\n', /line 3: .*name.*twice/],
		['[project]\nname =\n', /line 2: .*value/],
		['[project]\nname = "a" "b"\n', /line 2: .*after/],
	];
	for (const [text, message] of refusals) {
		assert.throws(() => parseToml(text), message, text);
	}
});

test('a requirement reads into its name, its version clauses and its Python marker', () => {
	assert.deepEqual(parseRequirement('numpy>=2.0.2'), {
		text: 'numpy>=2.0.2',
		name: 'numpy',
		clauses: [{ operator: '>=', version: '2.0.2' }],
		marker: null,
	});
	assert.deepEqual(parseRequirement('svglib>=0.9.1,!=1.4.0').clauses, [
		{ operator: '>=', version: '0.9.1' },
		{ operator: '!=', version: '1.4.0' },
	]);
	assert.deepEqual(parseRequirement("numba>=0.61.0; python_version=='3.13'").marker, {
		operator: '==',
		version: '3.13',
	});
	assert.deepEqual(parseRequirement('torch >= 2.9.0 ; python_version >= "3.14"').marker, {
		operator: '>=',
		version: '3.14',
	});
});

test('a requirement the site cannot state in words stops the build, naming it', () => {
	for (const text of [
		'numpy[dev]>=2.0.2',
		'numpy @ https://example.org/numpy.whl',
		"numpy>=2.0.2; sys_platform=='win32'",
		"numpy>=2.0.2; python_version<'3.13' and os_name=='nt'",
	]) {
		assert.throws(() => parseRequirement(text), new RegExp(text.replace(/[[\]().*+?^$|\\]/g, '\\$&')), text);
	}
});

test('the Python floor, the platform and the install line come from the project', () => {
	const project = readProject(parseToml(ONE_FLOOR));
	assert.equal(project.name, 'phonometry');
	assert.equal(pythonFloor(project.requiresPython), '3.12');
	assert.equal(platformOf(project.requiresPython), 'Python >= 3.12');
	assert.equal(installLine(project), 'pip install "phonometry[full]"');
	// "3.12 or newer" is only true of a floor with no ceiling.
	assert.throws(() => pythonFloor('>=3.12,<4'), /or newer/);
	assert.throws(() => installLine({ ...project, extras: project.extras.filter((extra) => extra.name !== 'full') }), /full/);
});

test('requirements of one floor each are stated with every floor and every extra', () => {
	assert.equal(
		describeRequirements(readProject(parseToml(ONE_FLOOR))),
		'Python >= 3.12 with numpy >= 2.0.2 and scipy >= 1.14.0. ' +
			'Optional extras: perf, plot, report, audio and torch; full installs perf, plot, report and audio.',
	);
});

test('a floor of its own for each Python is stated with the Python it holds for', () => {
	assert.equal(
		describeRequirements(readProject(parseToml(PER_PYTHON))),
		'Python >= 3.12 with numpy >= 2.0.2 on Python < 3.13, numpy >= 2.1.0 on Python 3.13, ' +
			'numpy >= 2.3.2 on Python >= 3.14, scipy >= 1.14.0 on Python < 3.13, scipy >= 1.14.1 on Python 3.13 ' +
			'and scipy >= 1.16.1 on Python >= 3.14. ' +
			'Optional extras: perf, plot, report, audio and torch; full installs perf, plot, report and audio.',
	);
});

test('an extra that installs something no other extra names is stated as an extra of its own', () => {
	const project = readProject(
		parseToml(ONE_FLOOR.replace('"svglib>=0.9.0", "soundfile>=0.12.0"]', '"svglib>=0.9.0", "soundfile>=0.12.0", "extra>=1"]')),
	);
	assert.match(describeRequirements(project), /Optional extras: perf, plot, report, audio, torch and full\.$/);
});

test('a project table missing what the site states stops the build, naming the key', () => {
	const without = (key) => ONE_FLOOR.split('\n').filter((line) => !line.startsWith(`${key} =`)).join('\n');
	assert.throws(() => readProject(parseToml(without('requires-python'))), /requires-python/);
	assert.throws(() => readProject(parseToml(without('name'))), /name/);
	assert.throws(() => readProject(parseToml('[tool.x]\na = 1\n')), /\[project\]/);
});
