// site-preview.yml checks out only a few directories of the repository, so a
// module a script imports from anywhere else is missing on the runner and the
// deploy stops at the first step that loads it. This walks every script the
// workflow runs with node, follows each relative import (and each file read
// through `new URL(..., import.meta.url)`), and fails on a file the sparse
// checkout leaves out.
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { describe, test } from 'node:test';
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

/**
 * Whether cone-mode sparse checkout brings a path: anything under a listed
 * directory, and the files directly inside the root or any ancestor of one.
 */
function checkedOut(path, directories) {
	const parent = path.includes('/') ? path.slice(0, path.lastIndexOf('/')) : '';
	if (parent === '') return true;
	return directories.some(
		(directory) => path === directory || path.startsWith(`${directory}/`) || directory.startsWith(`${parent}/`),
	);
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
	// Cone mode also brings the files directly inside an ancestor, not its subdirectories.
	assert.equal(checkedOut('site/package.json', ['site/worker']), true);
	assert.equal(checkedOut('site/src/env.d.ts', ['site/src/data']), true);
	assert.equal(checkedOut('site/public/robots.txt', ['site/worker']), false);
});

/** The steps of the workflow, each as its text, by name. */
function stepsByName(text) {
	const steps = new Map();
	for (const step of text.split(/\n(?=\s+- (?:name|uses):)/)) {
		const name = step.match(/^\s+- name: (.+)$/m)?.[1];
		if (name) steps.set(name.trim(), step);
	}
	return steps;
}

describe('a deploy while the quota guard holds the code paths off', () => {
	const text = readFileSync(WORKFLOW, 'utf8');
	const steps = stepsByName(text);
	const named = (start) => [...steps.entries()].find(([name]) => name.startsWith(start))?.[1] ?? '';

	test('the guard state is read before anything is uploaded, and a failed read stops the job', () => {
		const names = [...steps.keys()];
		const read = names.findIndex((name) => name.startsWith('Read whether the quota guard'));
		assert.ok(read !== -1, 'no step reads the guard state');
		for (const later of ['Upload the assets-only version', 'Deploy the Worker']) {
			const at = names.findIndex((name) => name.startsWith(later));
			assert.ok(at !== -1, `no step named ${later}`);
			assert.ok(read < at, `${later} runs before the guard state is read`);
		}
		const step = named('Read whether the quota guard');
		assert.match(step, /\bid: guard\b/);
		assert.match(step, /set -euo pipefail/, 'without pipefail a failed read would pass through tee as not tripped');
		assert.match(step, /node scripts\/guard-state\.mjs \| tee -a "\$GITHUB_OUTPUT"/);
	});

	test('tripped: the full half is only uploaded and the assets-only half goes live under the off mark', () => {
		const step = named('Deploy the Worker');
		assert.match(step, /TRIPPED: \$\{\{ steps\.guard\.outputs\.tripped \}\}/);
		assert.match(step, /MARK: \$\{\{ steps\.guard\.outputs\.mark \}\}/);
		const [tripped, clear] = step.split(/\n\s+else\n/);
		assert.match(tripped, /if \[ "\$TRIPPED" = true \]/);
		assert.match(tripped, /wrangler versions upload --config wrangler\.jsonc --tag "full-\$PAIR"/);
		assert.match(tripped, /wrangler versions deploy --config wrangler\.jsonc --version-tag "assets-\$PAIR@100" --message "\$MARK: off, /);
		assert.doesNotMatch(tripped, /wrangler deploy /, 'no full deploy while tripped');
		assert.match(clear, /wrangler deploy --config wrangler\.jsonc --tag "full-\$PAIR" --message "\$message"/);
		assert.match(clear, /if \[ -n "\$MARK" \]; then message="\$MARK: on, \$message"; fi/);
	});

	test('a deploy over an unfinished switch back carries the guard mark, so the guard still clears its rule', async () => {
		const { decide } = await import('../lib/guard.mjs');
		const versions = [{ id: 'f', tag: 'full-301-1', created: '2026-11-19T00:20:00Z' }, { id: 'a', tag: 'assets-301-1', created: '2026-11-19T00:19:00Z' }];
		const d = decide({ count: 5, threshold: 95000, mode: 'auto', now: new Date('2026-11-19T00:30:00Z'), rule: { enabled: true, lastUpdated: '2026-11-18T22:00:00Z' }, current: { id: 'f', tag: 'full-301-1', message: 'quota guard: on, full half of 301-1' }, versions });
		assert.deepEqual(d.actions, [{ kind: 'rule', enabled: false }]);
	});

	test('each run of the workflow names its own pair, so a re-run never uploads a second version under a taken tag', () => {
		for (const name of ['Upload the assets-only version', 'Deploy the Worker']) {
			const step = named(name);
			assert.match(step, /PAIR: \$\{\{ github\.run_id \}\}-\$\{\{ github\.run_attempt \}\}/, name);
			assert.doesNotMatch(step, /PAIR: \$\{\{ inputs\./, `${name}: the docs.yml run is the same on every re-run`);
		}
	});

	test('the beacon check expects 204, or while tripped the WAF\'s 403 or the assets-only 404, never a 204', () => {
		const step = named('Check what the assets answer');
		assert.match(step, /TRIPPED: \$\{\{ steps\.guard\.outputs\.tripped \}\}/);
		assert.match(step, /want=204\n\s+if \[ "\$TRIPPED" = true \]; then want="403 404"; fi/);
		assert.match(step, /if ! grep -qwF -- "\$code" <<<"\$want"; then/);
		assert.doesNotMatch(step, /"\$code" != 204/, 'a fixed 204 fails every deploy while the guard is tripped');
		const accepts = (code, want) => want.split(' ').includes(code);
		assert.ok(accepts('403', '403 404') && accepts('404', '403 404') && !accepts('204', '403 404'));
		assert.ok(accepts('204', '204') && !accepts('404', '204'));
	});
});

test('the off mark the workflow writes is the one the guard switches back', async () => {
	const { decide } = await import('../lib/guard.mjs');
	const message = 'quota guard: off, deploy of 300-1 while the code paths are off';
	const versions = [
		{ id: 'f', tag: 'full-300-1', created: '2026-11-18T10:00:01Z' },
		{ id: 'a', tag: 'assets-300-1', created: '2026-11-18T10:00:00Z' },
	];
	const d = decide({ count: 5, threshold: 95000, mode: 'auto', now: new Date('2026-11-19T00:15:00Z'), rule: { enabled: true, lastUpdated: '2026-11-18T09:00:00Z' }, current: { id: 'a', tag: 'assets-300-1', message }, versions });
	assert.deepEqual(d.actions, [{ kind: 'deploy', versionId: 'f', tag: 'full-300-1' }, { kind: 'rule', enabled: false }]);
	const text = readFileSync(WORKFLOW, 'utf8');
	assert.ok(text.includes('--message "$MARK: off, deploy of $PAIR while the code paths are off"'));
});
