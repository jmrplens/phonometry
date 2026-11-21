// site-deploy.yml checks out only a few directories of the repository, so a
// module a script imports from anywhere else is missing on the runner and the
// deploy stops at the first step that loads it. This walks every script the
// workflow runs with node, follows each relative import (and each file read
// through `new URL(..., import.meta.url)`), and fails on a file the sparse
// checkout leaves out. The checkout is the same whether docs.yml calls the
// workflow or it is run by hand, so one closure covers both. The rest plays
// the steps that tell the two apart, and the deploy while the quota guard
// holds the code paths off, in bash with the commands they call stubbed.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, resolve } from 'node:path';
import { describe, test } from 'node:test';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const WORKFLOW = join(ROOT, '.github/workflows/site-deploy.yml');

/** The directories the checkout step lists under `sparse-checkout`. */
function sparseDirectories(text) {
	const block = text.match(/^(\s*)sparse-checkout: \|\n((?:\1 +\S.*\n)+)/m);
	assert.ok(block, 'site-deploy.yml has no sparse-checkout block');
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

test('the workflow runs the five scripts it is meant to', () => {
	const scripts = nodeScripts(readFileSync(WORKFLOW, 'utf8'));
	for (const script of ['site/worker/scripts/site-address.mjs', 'site/worker/stage.mjs', 'site/worker/scripts/apply-rules.mjs', 'site/worker/scripts/check-clip.mjs', 'site/worker/scripts/check-clip-host.mjs']) {
		assert.ok(scripts.includes(script), `site-deploy.yml no longer runs ${script}`);
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

/** The steps of the workflow, each as its text, in order, named or not. */
function stepTexts(text) {
	return text.split(/\n(?=\s+- (?:name|uses):)/).slice(1);
}

/** A step's `run: |` block, as bash reads it. */
function runBlock(step) {
	const block = step.match(/\n(\s+)run: \|\n((?:\1 {2}.*\n|\s*\n)+)/);
	assert.ok(block, 'the step has no run block');
	return block[2].split('\n').map((line) => line.slice(block[1].length + 2)).join('\n');
}

describe('called by docs.yml, or run by hand on a docs.yml run', () => {
	const text = readFileSync(WORKFLOW, 'utf8');
	const steps = stepsByName(text);
	const named = (start) => [...steps.entries()].find(([name]) => name.startsWith(start))?.[1] ?? '';
	// A called workflow runs in its caller's run, so its run id is the one
	// docs.yml passes; a run by hand is a run of its own and names another.
	// github.event_name cannot tell the two apart: in a called workflow it
	// is the caller's event (push).
	const CALLED = '${{ inputs.run_id == github.run_id }}';
	const BY_HAND = '${{ inputs.run_id != github.run_id }}';
	const DOCS = 'jmrplens/phonometry/.github/workflows/docs.yml@refs/heads/main';
	const SUCCESS = { path: '.github/workflows/docs.yml', head_branch: 'main', event: 'push', head_repository: { full_name: 'jmrplens/phonometry' }, conclusion: 'success', head_sha: 'abc' };

	/**
	 * Runs the step that checks where the pages come from, with gh stubbed:
	 * a read of a run answers `run` (or fails when it is null), a comparison
	 * with main answers `compare`. Returns the exit status, what the step
	 * printed and the gh calls, each as its arguments joined with spaces.
	 */
	function runCheck(env, { run = null, compare = 'identical' } = {}) {
		const script = runBlock(named('Check the run is a docs.yml build of main'));
		const dir = mkdtempSync(join(tmpdir(), 'check-step-'));
		try {
			writeFileSync(join(dir, 'gh'), '#!/bin/bash\nprintf "%s\\n" "$*" >> "$CALLS"\ncase "$2" in\n*/actions/runs/*) [ -s "$RUN" ] || exit 1; cat "$RUN" ;;\n*/compare/*) echo "$COMPARE" ;;\n*) exit 9 ;;\nesac\n', { mode: 0o755 });
			writeFileSync(join(dir, 'run'), run === null ? '' : JSON.stringify(run));
			writeFileSync(join(dir, 'calls'), '');
			let status = 0;
			let output = '';
			try {
				output = execFileSync('bash', ['-c', script], { env: { PATH: `${dir}:/usr/bin:/bin`, CALLS: join(dir, 'calls'), RUN: join(dir, 'run'), COMPARE: compare, GITHUB_REPOSITORY: 'jmrplens/phonometry', GITHUB_STEP_SUMMARY: '/dev/null', RUN_ID: '300', ...env }, stdio: ['ignore', 'pipe', 'pipe'] }).toString();
			} catch (error) {
				status = error.status;
				output = `${error.stdout}${error.stderr}`;
			}
			const calls = readFileSync(join(dir, 'calls'), 'utf8').split('\n').filter(Boolean);
			return { status, output, calls };
		} finally {
			rmSync(dir, { recursive: true, force: true });
		}
	}

	const called = (overrides = {}) => ({ CALLED: 'true', WORKFLOW_REF: DOCS, REF: 'refs/heads/main', EVENT: 'push', SHA: 'abc', ...overrides });

	test('the check knows the two modes by the run id, the way the downloads do', () => {
		const step = named('Check the run is a docs.yml build of main');
		assert.ok(step.includes(`CALLED: ${CALLED}`), 'the check does not tell a call from docs.yml by the run id');
		for (const [name, value] of [['WORKFLOW_REF', 'github.workflow_ref'], ['REF', 'github.ref'], ['EVENT', 'github.event_name'], ['SHA', 'github.sha']]) {
			assert.ok(step.includes(`${name}: \${{ ${value} }}`), `the check reads ${value} through a step variable`);
		}
		const downloads = stepTexts(text).filter((step) => /uses: actions\/download-artifact@/.test(step));
		assert.equal(downloads.length, 2, 'one download for each mode');
		const [own, other] = [CALLED, BY_HAND].map((condition) => downloads.filter((step) => step.includes(`if: ${condition}`)));
		assert.equal(own.length, 1, 'no download, or two, for a call from docs.yml');
		assert.equal(other.length, 1, 'no download, or two, for a run by hand');
		assert.doesNotMatch(own[0], /run-id:/, 'the pages of the calling run are an artifact of this run, read without naming a run');
		assert.match(other[0], /run-id: \$\{\{ inputs\.run_id \}\}/);
		for (const step of downloads) assert.match(step, /name: github-pages-\$\{\{ inputs\.attempt \}\}/);
	});

	test('called from a push to main: the run is not read back, since it is still running, and main holds the commit', () => {
		const { status, calls } = runCheck(called());
		assert.equal(status, 0);
		assert.deepEqual(calls, ['api repos/jmrplens/phonometry/compare/main...abc --jq .status']);
	});

	test('called from a dispatch of docs.yml on main: deployed as a push is', () => {
		assert.equal(runCheck(called({ EVENT: 'workflow_dispatch' })).status, 0);
	});

	test('called from a docs.yml run on another branch: refused before anything is deployed', () => {
		const { status, output } = runCheck(called({ REF: 'refs/heads/feature', WORKFLOW_REF: 'jmrplens/phonometry/.github/workflows/docs.yml@refs/heads/feature' }));
		assert.equal(status, 1);
		assert.match(output, /built refs\/heads\/feature, not main/);
	});

	test('called by another workflow, or by docs.yml of another repository: refused', () => {
		for (const ref of ['jmrplens/phonometry/.github/workflows/python-app.yml@refs/heads/main', 'someone/phonometry/.github/workflows/docs.yml@refs/heads/main']) {
			const { status, output } = runCheck(called({ WORKFLOW_REF: ref }));
			assert.equal(status, 1, ref);
			assert.match(output, /is not docs\.yml of jmrplens\/phonometry/, ref);
		}
	});

	test('called from a pull request: refused', () => {
		assert.equal(runCheck(called({ EVENT: 'pull_request' })).status, 1);
	});

	test('called at a commit main does not hold: refused', () => {
		const { status, output } = runCheck(called(), { compare: 'diverged' });
		assert.equal(status, 1);
		assert.match(output, /abc is not on main \(diverged\)/);
	});

	test('by hand: the docs.yml run named is read back and has to have succeeded', () => {
		const ok = runCheck({ CALLED: 'false' }, { run: SUCCESS });
		assert.equal(ok.status, 0);
		assert.deepEqual(ok.calls, ['api repos/jmrplens/phonometry/actions/runs/300', 'api repos/jmrplens/phonometry/compare/main...abc --jq .status']);
		const running = runCheck({ CALLED: 'false' }, { run: { ...SUCCESS, conclusion: null } });
		assert.equal(running.status, 1);
		assert.match(running.output, /concluded null/);
		assert.equal(runCheck({ CALLED: 'false' }, { run: { ...SUCCESS, path: '.github/workflows/site-deploy.yml' } }).status, 1);
	});

	test('by hand, the call variables count for nothing: a run that cannot be read stops the deploy', () => {
		assert.equal(runCheck({ CALLED: 'false', WORKFLOW_REF: DOCS, REF: 'refs/heads/main', EVENT: 'push', SHA: 'abc' }).status, 1);
	});

	test('no step names the host or the base path of the pages: each comes from site-address.mjs', () => {
		const P = /(?<![\w.\-/])\/phonometry(?=[/'"`)\s#?]|$)/;
		const code = text.split('\n').filter((line) => !/^\s*#/.test(line));
		const spelled = code.filter((line) => P.test(line) || /phonometry\.dev\/phonometry|docs\.jmrp\.io\/phonometry/.test(line));
		assert.deepEqual(spelled, [], 'these lines spell the host or the base path the build already names');
		const address = named('Read where the pages are served');
		assert.match(address, /\bid: site\b/);
		assert.match(address, /node site\/worker\/scripts\/site-address\.mjs >> "\$GITHUB_OUTPUT"/);
	});

	test('the browser clip check plays a page of the deployed site, at the address site-address.mjs gives', () => {
		const step = named('Check a clip plays in a browser');
		assert.match(step, /PAGE_URL: \$\{\{ steps\.site\.outputs\.page_url \}\}/);
		const page = step.match(/node scripts\/check-clip\.mjs --page "\$\{PAGE_URL\}([^"$]+)"/);
		assert.ok(page, 'the clip check runs on its default page, which spells the host and the base path');
		const route = page[1].replace(/\/$/, '');
		const docs = join(ROOT, 'site/src/content/docs');
		assert.ok(
			['.mdx', '.md', '/index.mdx', '/index.md'].some((ending) => existsSync(join(docs, `${route}${ending}`))),
			`${page[1]} is no page of site/src/content/docs`,
		);
	});
});

describe('the checks after a deploy hold the site served at the root', () => {
	const text = readFileSync(WORKFLOW, 'utf8');
	const steps = stepsByName(text);
	const named = (start) => [...steps.entries()].find(([name]) => name.startsWith(start))?.[1] ?? '';
	const assets = named('Check what the assets answer');
	const rules = named('Check what the zone rules answer');

	test('the pages carry no noindex when the build is indexable, and the llms files keep theirs', () => {
		assert.match(assets, /INDEXABLE: \$\{\{ steps\.site\.outputs\.indexable \}\}/);
		const script = runBlock(assets);
		assert.match(script, /if \[ "\$INDEXABLE" = true \]; then/);
		assert.match(script, /absent "a page carries no noindex" '\^x-robots-tag:' "\$base\/signals\/"/);
		assert.match(script, /expect "a page, kept out of search indexes" "\$base\/signals\/" 200 '\^x-robots-tag: noindex'/);
		assert.match(script, /expect "llms\.txt stays out of search indexes" "\$base\/llms\.txt" 200 '\^x-robots-tag: noindex'/);
	});

	test('the home page answers itself at the root, with no redirect to a base path', () => {
		const script = runBlock(assets);
		assert.match(script, /expect "the home page answers" "\$base\/" 200/);
		assert.match(runBlock(rules), /if \[ -n "\$BASE" \]; then\n\s+check "the root goes to the base path"/);
	});

	test('the assets are checked after the zone rules are put, so an old rule does not answer for the home page', () => {
		const names = [...steps.keys()];
		const at = (start) => names.findIndex((name) => name.startsWith(start));
		assert.ok(at('Check what the assets answer') !== -1, 'no step checks what the assets answer');
		for (const earlier of ['Check the zone rules', 'Put the zone rules', 'Keep the rules that were replaced']) {
			assert.ok(at(earlier) !== -1, `no step named ${earlier}`);
			assert.ok(at(earlier) < at('Check what the assets answer'), `the assets are checked before "${earlier}"`);
		}
	});

	test('the old base path answers one 301 to the same page at the root, its query kept', () => {
		assert.match(rules, /LEGACY_BASE: \$\{\{ steps\.site\.outputs\.legacy_base \}\}/);
		const script = runBlock(rules);
		assert.match(script, /if \[ -n "\$LEGACY_BASE" \]; then/);
		assert.match(script, /check "a page under the old base path goes to the root" 301 "\$ORIGIN\/signals\/\\\?q=1" "\$ORIGIN\$LEGACY_BASE\/signals\/\?q=1"/);
		assert.match(script, /check "the old base path itself goes to the home page" 301 "\$ORIGIN\/\[\[:space:\]\]\*\$" "\$ORIGIN\$LEGACY_BASE"/);
	});

	test('a page without its slash answers one 301 to the page, its query kept', () => {
		assert.match(runBlock(rules), /check "a page without its slash goes to the page" 301 "\$ORIGIN\$BASE\/signals\/\\\?q=1" "\$ORIGIN\$BASE\/signals\?q=1"/);
	});

	test('robots.txt names a sitemap the stage holds', () => {
		const step = named('Check robots.txt names a sitemap the stage holds');
		assert.ok(step, 'no step holds the robots.txt sitemap to the stage');
		assert.match(step, /ORIGIN: \$\{\{ steps\.site\.outputs\.origin \}\}/);
		const script = runBlock(step);
		assert.match(script, /site\/worker\/stage\/robots\.txt/);
		assert.match(script, /\[ -f "site\/worker\/stage\$\{path\}" \]/);
	});

	test('every staged clip answers at the clip host with its size, before the rules point there', () => {
		const step = named('Check every staged clip answers at the clip host');
		assert.ok(step, 'no step holds the staged clips to the clip host');
		assert.match(step, /CLIP_BASE: \$\{\{ steps\.site\.outputs\.clip_base \}\}/);
		assert.match(step, /node site\/worker\/scripts\/check-clip-host\.mjs --stage "site\/worker\/stage\$BASE" --clip-base "\$CLIP_BASE"/);
		const order = stepTexts(text);
		const at = (part) => order.findIndex((one) => one.includes(part));
		assert.ok(at('check-clip-host.mjs') < at('apply-rules.mjs --apply'), 'the rules point at the clip host before its clips are checked');
		assert.ok(at('check-clip-host.mjs') > at('stage.mjs --from'), 'the clips are checked before they are staged');
	});
});

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

	/**
	 * Runs a step's `run: |` block in bash with `pnpm` and `node` stubbed:
	 * pnpm records each argument on its own (so an argument split by the
	 * shell shows), node prints what guard-state.mjs --since would, failing
	 * its first `nodeFails` calls. Returns the pnpm calls, each as its
	 * arguments joined with " | ".
	 */
	function runDeploy(env, after, nodeFails = 0) {
		const script = runBlock(named('Deploy the Worker'));
		const dir = mkdtempSync(join(tmpdir(), 'deploy-step-'));
		try {
			writeFileSync(join(dir, 'pnpm'), '#!/bin/bash\n{ for a in "$@"; do printf "%s\\x1f" "$a"; done; printf "\\n"; } >> "$CALLS"\n', { mode: 0o755 });
			writeFileSync(join(dir, 'node'), `#!/bin/bash\n[ "$*" = "scripts/guard-state.mjs --since d0 --pair 300-1" ] || { echo "unexpected node $*" >&2; exit 9; }\necho x >> "$NODE_CALLS"\n[ "$(wc -l < "$NODE_CALLS")" -gt ${nodeFails} ] || exit 1\ncat "$AFTER"\n`, { mode: 0o755 });
			writeFileSync(join(dir, 'after'), `${after}\n`);
			writeFileSync(join(dir, 'calls'), '');
			writeFileSync(join(dir, 'node-calls'), '');
			execFileSync('bash', ['-c', script], { env: { PATH: `${dir}:/usr/bin:/bin`, CALLS: join(dir, 'calls'), NODE_CALLS: join(dir, 'node-calls'), READ_RETRY_SECONDS: '0', AFTER: join(dir, 'after'), GITHUB_STEP_SUMMARY: '/dev/null', PAIR: '300-1', DEPLOYMENT: 'd0', ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
			return readFileSync(join(dir, 'calls'), 'utf8').split('\n').filter(Boolean).map((line) => line.split('\x1f').slice(0, -1).join(' | '));
		} finally {
			rmSync(dir, { recursive: true, force: true });
		}
	}

	/** A wrangler call as runDeploy returns it. */
	const wrangler = (...args) => ['exec', 'wrangler', ...args].join(' | ');
	const DEPLOY_FULL = (message) => wrangler('deploy', '--config', 'wrangler.jsonc', '--tag', 'full-300-1', '--message', message);
	const PROMOTE = (half, message) => wrangler('versions', 'deploy', '--config', 'wrangler.jsonc', '--version-tag', `${half}-300-1@100`, '--message', message, '--yes');
	const UPLOAD_FULL = wrangler('versions', 'upload', '--config', 'wrangler.jsonc', '--tag', 'full-300-1', '--message', 'full half of 300-1');

	test('the deploy step reads the deployment the guard state named', () => {
		const step = named('Deploy the Worker');
		assert.match(step, /TRIPPED: \$\{\{ steps\.guard\.outputs\.tripped \}\}/);
		assert.match(step, /MARK: \$\{\{ steps\.guard\.outputs\.mark \}\}/);
		assert.match(step, /DEPLOYMENT: \$\{\{ steps\.guard\.outputs\.deployment \}\}/);
		assert.match(step, /set -euo pipefail/);
	});

	test('on: the full half goes live with wrangler deploy, the guard mark carried when the read had one', () => {
		assert.deepEqual(runDeploy({ TRIPPED: 'false', MARK: '' }, 'switched=false'), [DEPLOY_FULL('full half of 300-1')]);
		assert.deepEqual(runDeploy({ TRIPPED: 'false', MARK: 'quota guard' }, 'switched=false'), [DEPLOY_FULL('quota guard: on, full half of 300-1')]);
	});

	test('tripped: the full half is only uploaded and the assets-only half goes live under the off mark', () => {
		assert.deepEqual(runDeploy({ TRIPPED: 'true', MARK: 'quota switch by hand' }, 'switched=false'), [UPLOAD_FULL, PROMOTE('assets', 'quota switch by hand: off, deploy of 300-1 while the code paths are off')]);
	});

	test('the guard switched off during the deploy: the assets-only half goes live again under its mark', () => {
		const calls = runDeploy({ TRIPPED: 'false', MARK: '' }, 'switched=true\ntripped=true\nmark=quota guard');
		assert.deepEqual(calls, [DEPLOY_FULL('full half of 300-1'), PROMOTE('assets', 'quota guard: off, deploy of 300-1 while the code paths are off')]);
	});

	test('switched back on during a deploy held off: the full half goes live, the guard mark carried', () => {
		const calls = runDeploy({ TRIPPED: 'true', MARK: 'quota guard' }, 'switched=true\ntripped=false\nmark=quota guard');
		assert.equal(calls.length, 3);
		assert.equal(calls[2], PROMOTE('full', 'quota guard: on, full half of 300-1'));
	});

	test('another deploy in between that changes nothing: no second promotion', () => {
		assert.equal(runDeploy({ TRIPPED: 'false', MARK: '' }, 'switched=true\ntripped=false\nmark=').length, 1);
	});

	test('a failed read of the deployments since is tried again, and the promotion is not repeated', () => {
		const calls = runDeploy({ TRIPPED: 'false', MARK: '' }, 'switched=true\ntripped=true\nmark=quota guard', 2);
		assert.deepEqual(calls, [DEPLOY_FULL('full half of 300-1'), PROMOTE('assets', 'quota guard: off, deploy of 300-1 while the code paths are off')]);
	});

	test('the deployments since the read cannot be read three times: the step fails and says what to run', () => {
		assert.throws(
			() => runDeploy({ TRIPPED: 'false', MARK: '' }, 'switched=false', 3),
			(error) => /could not be read: 300-1 was this run's last promotion and what is live now is unknown; run node scripts\/guard-state\.mjs --since d0 --pair 300-1 by hand/.test(String(error.stdout)),
		);
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

	test('the beacon check reads the live state itself, with the deploy token, never the state read before the deploy', () => {
		const step = named('Check what the assets answer');
		assert.match(step, /CLOUDFLARE_API_TOKEN: \$\{\{ secrets\.CF_PHONOMETRY_DEPLOY_TOKEN \}\}/);
		assert.match(step, /node site\/worker\/scripts\/check-beacon\.mjs \|\| fail=1/);
		assert.doesNotMatch(step, /steps\.guard\.outputs/, 'the state read before the deploy may be stale by the time of the probe');
		assert.doesNotMatch(step, /-X POST/, 'one beacon probe, in check-beacon.mjs');
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
	assert.ok(text.includes('--message "$1: off, deploy of $PAIR while the code paths are off"'));
});
