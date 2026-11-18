// site-preview.yml checks out only a few directories of the repository, so a
// module a script imports from anywhere else is missing on the runner and the
// deploy stops at the first step that loads it. This walks every script the
// workflow runs with node, follows each relative import (and each file read
// through `new URL(..., import.meta.url)`), and fails on a file the sparse
// checkout leaves out.
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const WORKFLOW = join(ROOT, '.github/workflows/site-preview.yml');

/** The directories the checkout step lists under `sparse-checkout`. */
function sparseDirectories(text) {
	const block = text.match(/^(\s*)sparse-checkout: \|\n((?:\1 +\S.*\n)+)/m);
	assert.ok(block, 'site-preview.yml has no sparse-checkout block');
	return block[2]
		.split('\n')
		.map((line) => line.trim())
		.filter(Boolean);
}

/** Every `node <script>.mjs` a step runs, as a path from the repository root. */
function nodeScripts(text) {
	const scripts = [];
	for (const step of text.split(/\n(?=\s+- (?:name|uses):)/)) {
		const directory = step.match(/^\s+working-directory: (\S+)/m)?.[1] ?? '.';
		for (const match of step.matchAll(/\bnode (\S+\.mjs)\b/g)) scripts.push(join(directory, match[1]));
	}
	return scripts;
}

/** The repository files a module loads, itself included, following relative specifiers. */
function importClosure(entries, root = ROOT) {
	const seen = new Set();
	const queue = entries.map((entry) => resolve(root, entry));
	while (queue.length > 0) {
		const file = queue.pop();
		if (seen.has(file)) continue;
		seen.add(file);
		if (!existsSync(file) || !/\.(?:mjs|js)$/.test(file)) continue;
		const source = readFileSync(file, 'utf8');
		const specifiers = [
			...source.matchAll(/(?:\bfrom|\bimport)\s*\(?\s*['"](\.{1,2}\/[^'"]+)['"]/g),
			...source.matchAll(/new URL\(\s*['"](\.{1,2}\/[^'"]+)['"]\s*,\s*import\.meta\.url\s*\)/g),
		];
		for (const [, specifier] of specifiers) queue.push(resolve(dirname(file), specifier));
	}
	return [...seen].map((file) => relative(root, file));
}

/** Whether cone-mode sparse checkout brings a path: a listed directory, or a file at the root. */
function checkedOut(path, directories) {
	return !path.includes('/') || directories.some((directory) => path === directory || path.startsWith(`${directory}/`));
}

test('the workflow runs the three scripts it is meant to', () => {
	const scripts = nodeScripts(readFileSync(WORKFLOW, 'utf8'));
	for (const script of ['site/worker/stage.mjs', 'site/worker/scripts/apply-rules.mjs', 'site/worker/scripts/check-clip.mjs']) {
		assert.ok(scripts.includes(script), `site-preview.yml no longer runs ${script}`);
	}
});

test('the sparse checkout holds every module those scripts load', () => {
	const text = readFileSync(WORKFLOW, 'utf8');
	const directories = sparseDirectories(text);
	const closure = importClosure(nodeScripts(text));
	// The staging directory is written by the run, not checked out.
	const needed = closure.filter((path) => path !== 'site/worker/stage' && !path.startsWith('site/worker/stage/'));
	const missing = needed.filter((path) => !checkedOut(path, directories));
	assert.deepEqual(missing, [], `sparse-checkout (${directories.join(', ')}) leaves out ${missing.join(', ')}`);
	for (const path of needed) assert.ok(existsSync(join(ROOT, path)), `${path} is loaded but does not exist`);
});

test('a module outside the listed directories is caught', () => {
	assert.equal(checkedOut('site/src/lib/fallback-routes.mjs', ['site/worker', 'site/src/data', 'site/scripts']), false);
	assert.equal(checkedOut('site/src/data/site.mjs', ['site/worker', 'site/src/data', 'site/scripts']), true);
	assert.equal(checkedOut('package.json', ['site/worker']), true);
});
