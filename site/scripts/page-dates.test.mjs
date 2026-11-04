// The dates src/lib/page-dates.mjs reads from git history, on histories small
// enough to read.
//
// The real history only ever shows the module the shapes it already has, and
// its bugs looked like a slow build and a date nobody checks: one git process
// per page cost the build most of an hour, and a page written from another
// published the older page's date. Each test here builds a repository of its
// own, laid out as this one is with the pages under site/src/content/docs, and
// asks from the site's root the way a build does.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { devNull, tmpdir } from 'node:os';
import { delimiter, dirname, join } from 'node:path';
import { test } from 'node:test';

const MODULE = new URL('../src/lib/page-dates.mjs', import.meta.url).href;

// Only what a test sets may decide its result: the configuration of the machine
// running it could turn rename detection off, and a temporary directory inside
// someone's checkout would be a repository to the test that needs it not to be.
const TEMP = realpathSync(tmpdir());
process.env.GIT_CONFIG_GLOBAL = devNull;
process.env.GIT_CONFIG_NOSYSTEM = '1';
process.env.GIT_CEILING_DIRECTORIES = TEMP;
for (const name of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_COUNT']) delete process.env[name];

const DOCS = 'src/content/docs';

let loads = 0;

/** The module as a build first loads it, with nothing remembered yet. */
async function fresh() {
	loads += 1;
	return (await import(`${MODULE}?load=${loads}`)).firstPublished;
}

/** Run the rest of the test from `dir`, as a build runs from the site's root. */
function chdir(t, dir) {
	const back = process.cwd();
	process.chdir(dir);
	t.after(() => process.chdir(back));
}

/** Set an environment variable for the rest of the test. */
function setEnv(t, name, value) {
	const before = process.env[name];
	process.env[name] = value;
	t.after(() => {
		if (before === undefined) delete process.env[name];
		else process.env[name] = before;
	});
}

/** A directory of its own for one test. */
function tempDir(t, prefix = 'page-dates-') {
	const dir = mkdtempSync(join(TEMP, prefix));
	t.after(() => rmSync(dir, { recursive: true, force: true }));
	return dir;
}

/** Forty lines of text that are this page's own, so a similarity search can tell it from another. */
const body = (seed, count = 40) =>
	Array.from({ length: count }, (_, i) => `${seed} line ${i} of the text ${seed.length * i}`).join('\n') + '\n';

/** A repository with the layout of this one, and what a test does to it. */
function repository(t) {
	const root = tempDir(t);
	const site = join(root, 'site');
	const docs = join(site, DOCS);
	mkdirSync(docs, { recursive: true });
	const git = (args, env = {}) =>
		execFileSync('git', args, {
			cwd: root,
			encoding: 'utf8',
			stdio: ['ignore', 'pipe', 'ignore'],
			env: { ...process.env, ...env },
		});
	git(['init', '-q', '-b', 'main']);
	git(['config', 'user.name', 'A Maintainer']);
	git(['config', 'user.email', 'maintainer@example.org']);
	const write = (name, text) => {
		const file = join(docs, name);
		mkdirSync(dirname(file), { recursive: true });
		writeFileSync(file, text);
	};
	const commit = (date) => {
		git(['add', '-A']);
		const at = `${date}T12:00:00+00:00`;
		git(['commit', '-q', '-m', `work of ${date}`], { GIT_AUTHOR_DATE: at, GIT_COMMITTER_DATE: at });
	};
	return { root, site, docs, git, write, commit, path: (name) => `${DOCS}/${name}` };
}

/**
 * A `git` first on the PATH that notes each run and hands it to the real one,
 * so what is counted is processes, whichever call of the module started them.
 */
function countGit(t) {
	const dir = tempDir(t, 'page-dates-shim-');
	const real = execFileSync('sh', ['-c', 'command -v git'], { encoding: 'utf8' }).trim();
	const calls = join(dir, 'calls');
	writeFileSync(calls, '');
	const shim = join(dir, 'git');
	writeFileSync(shim, `#!/bin/sh\nprintf '%s\\n' "$*" >> '${calls}'\nexec '${real}' "$@"\n`);
	chmodSync(shim, 0o755);
	setEnv(t, 'PATH', `${dir}${delimiter}${process.env.PATH}`);
	return () => readFileSync(calls, 'utf8').split('\n').filter(Boolean);
}

test('a page is dated by the commit that added it, on the day its committer wrote', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', body('a'));
	repo.commit('2024-03-01');
	repo.write('a.mdx', `${body('a')}and an edit\n`);
	repo.commit('2024-05-01');
	repo.write('late.mdx', body('late'));
	repo.git(['add', '-A']);
	repo.git(['commit', '-q', '-m', 'late at night'], {
		GIT_AUTHOR_DATE: '2024-06-01T23:30:00-05:00',
		GIT_COMMITTER_DATE: '2024-06-01T23:30:00-05:00',
	});
	chdir(t, repo.site);
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('a.mdx')), '2024-03-01');
	assert.equal(firstPublished(repo.path('late.mdx')), '2024-06-01');
});

test('a page renamed twice keeps the date of the commit that first added it', async (t) => {
	const repo = repository(t);
	repo.write('old.mdx', body('moved'));
	repo.commit('2024-01-10');
	repo.git(['mv', join(repo.docs, 'old.mdx'), join(repo.docs, 'middle.mdx')]);
	repo.commit('2024-02-10');
	mkdirSync(join(repo.docs, 'deep'));
	renameSync(join(repo.docs, 'middle.mdx'), join(repo.docs, 'deep/new.mdx'));
	// Edited in the commit that moves it, so only similarity can find the rename.
	repo.write('deep/new.mdx', `${body('moved')}and a line the move added\n`);
	repo.commit('2024-03-10');
	chdir(t, repo.site);
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('deep/new.mdx')), '2024-01-10');
});

test('a page deleted and added again keeps its first date', async (t) => {
	const repo = repository(t);
	repo.write('back.mdx', body('back'));
	repo.commit('2024-01-15');
	rmSync(join(repo.docs, 'back.mdx'));
	repo.write('other.mdx', body('other'));
	repo.commit('2024-02-15');
	repo.write('back.mdx', body('back again, written anew'));
	repo.commit('2024-03-15');
	chdir(t, repo.site);
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('back.mdx')), '2024-01-15');
});

test('a page added on two branches takes the older add', async (t) => {
	const repo = repository(t);
	repo.write('base.mdx', body('base'));
	repo.commit('2024-01-01');
	repo.git(['checkout', '-q', '-b', 'side']);
	repo.write('twice.mdx', body('from the side branch'));
	repo.commit('2024-02-01');
	repo.git(['checkout', '-q', 'main']);
	repo.write('twice.mdx', body('from main'));
	repo.commit('2024-03-01');
	const at = '2024-04-01T12:00:00+00:00';
	const env = { GIT_AUTHOR_DATE: at, GIT_COMMITTER_DATE: at };
	repo.git(['merge', '-q', '-s', 'ours', '--no-edit', 'side'], env);
	chdir(t, repo.site);
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('twice.mdx')), '2024-02-01');
});

test('a page written from another gets its own date, not the date of the page it came from', async (t) => {
	const repo = repository(t);
	repo.write('guide.mdx', body('guide'));
	repo.commit('2024-01-20');
	repo.write('copy.mdx', `${body('guide')}and a line of its own\n`);
	repo.commit('2024-06-20');
	chdir(t, repo.site);
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('guide.mdx')), '2024-01-20');
	assert.equal(firstPublished(repo.path('copy.mdx')), '2024-06-20');
});

test('a page split off a guide that moves in the same commit gets its own date, and the guide keeps its', async (t) => {
	const repo = repository(t);
	repo.write('guide.mdx', body('guide'));
	repo.commit('2024-01-25');
	rmSync(join(repo.docs, 'guide.mdx'));
	repo.write('moved/guide.mdx', `${body('guide')}a closing line\n`);
	repo.write('split.mdx', `${body('guide', 25)}${body('the part that is new', 15)}`);
	repo.commit('2024-07-25');
	chdir(t, repo.site);
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('moved/guide.mdx')), '2024-01-25');
	assert.equal(firstPublished(repo.path('split.mdx')), '2024-07-25');
});

for (const setting of ['false', 'copies']) {
	test(`diff.renames set to ${setting} in the environment changes no date`, async (t) => {
		const repo = repository(t);
		repo.write('old.mdx', body('moved'));
		repo.write('guide.mdx', body('guide'));
		repo.commit('2024-01-05');
		rmSync(join(repo.docs, 'old.mdx'));
		repo.write('new.mdx', `${body('moved')}and an edit\n`);
		repo.write('copy.mdx', `${body('guide')}and a line of its own\n`);
		repo.commit('2024-08-05');
		chdir(t, repo.site);
		setEnv(t, 'GIT_CONFIG_COUNT', '1');
		setEnv(t, 'GIT_CONFIG_KEY_0', 'diff.renames');
		setEnv(t, 'GIT_CONFIG_VALUE_0', setting);
		const firstPublished = await fresh();
		assert.equal(firstPublished(repo.path('new.mdx')), '2024-01-05');
		assert.equal(firstPublished(repo.path('copy.mdx')), '2024-08-05');
	});
}

test('more renames in one commit than the limit of rename candidates still carry their dates', async (t) => {
	const repo = repository(t);
	repo.write('old-a.mdx', body('first page'));
	repo.write('old-b.mdx', body('second page'));
	repo.commit('2024-01-12');
	rmSync(join(repo.docs, 'old-a.mdx'));
	rmSync(join(repo.docs, 'old-b.mdx'));
	repo.write('new-a.mdx', `${body('first page')}and an edit\n`);
	repo.write('new-b.mdx', `${body('second page')}and an edit\n`);
	repo.commit('2024-08-12');
	chdir(t, repo.site);
	// The real limit is a thousand of each; this one is reached by two.
	setEnv(t, 'GIT_CONFIG_COUNT', '1');
	setEnv(t, 'GIT_CONFIG_KEY_0', 'diff.renameLimit');
	setEnv(t, 'GIT_CONFIG_VALUE_0', '1');
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('new-a.mdx')), '2024-01-12');
	assert.equal(firstPublished(repo.path('new-b.mdx')), '2024-01-12');
});

test('a path from the site root and an absolute one reach the same page', async (t) => {
	const repo = repository(t);
	repo.write('sub/page.mdx', body('page'));
	repo.commit('2024-04-04');
	chdir(t, repo.site);
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('sub/page.mdx')), '2024-04-04');
	assert.equal(firstPublished(join(repo.docs, 'sub/page.mdx')), '2024-04-04');
});

test('a page whose name holds a space or an accent is read whole', async (t) => {
	const repo = repository(t);
	repo.write('a page.mdx', body('spaced'));
	repo.write('guía.mdx', body('accented'));
	repo.commit('2024-04-14');
	chdir(t, repo.site);
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('a page.mdx')), '2024-04-14');
	assert.equal(firstPublished(repo.path('guía.mdx')), '2024-04-14');
});

test('a file git does not track, and a path that names nothing, have no date', async (t) => {
	const repo = repository(t);
	repo.write('tracked.mdx', body('tracked'));
	repo.commit('2024-05-05');
	repo.write('untracked.mdx', body('untracked'));
	chdir(t, repo.site);
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('tracked.mdx')), '2024-05-05');
	assert.equal(firstPublished(repo.path('untracked.mdx')), undefined);
	assert.equal(firstPublished(repo.path('missing.mdx')), undefined);
	assert.equal(firstPublished(''), undefined);
	assert.equal(firstPublished(undefined), undefined);
});

test('a directory in no repository has no dates', async (t) => {
	const dir = tempDir(t);
	mkdirSync(join(dir, DOCS), { recursive: true });
	writeFileSync(join(dir, DOCS, 'a.mdx'), body('a'));
	chdir(t, dir);
	const firstPublished = await fresh();
	assert.equal(firstPublished(`${DOCS}/a.mdx`), undefined);
});

test('a shallow clone has no dates, because its oldest commit seems to add every page', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', body('a'));
	repo.commit('2024-01-01');
	repo.write('a.mdx', `${body('a')}and an edit\n`);
	repo.commit('2024-02-01');
	const clone = join(tempDir(t), 'clone');
	execFileSync('git', ['clone', '-q', '--depth', '1', `file://${repo.root}`, clone], {
		stdio: ['ignore', 'ignore', 'ignore'],
	});
	chdir(t, join(clone, 'site'));
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('a.mdx')), undefined);
});

test('a history longer than the default limit of a child process is read whole', async (t) => {
	const repo = repository(t);
	const names = Array.from({ length: 9000 }, (_, i) => `${'long-name-'.repeat(12)}${i}.mdx`);
	for (const name of names) repo.write(name, 'a page\n');
	repo.commit('2024-10-10');
	chdir(t, repo.site);
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path(names.at(-1))), '2024-10-10');
});

test('no git to run means no dates', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', body('a'));
	repo.commit('2024-01-01');
	chdir(t, repo.site);
	setEnv(t, 'PATH', tempDir(t));
	const firstPublished = await fresh();
	assert.equal(firstPublished(repo.path('a.mdx')), undefined);
});

test(
	'however many pages ask, git runs once to find the repository and once to read its history',
	{ skip: process.platform === 'win32' && 'counts through a shell script on the PATH' },
	async (t) => {
		const repo = repository(t);
		const names = Array.from({ length: 30 }, (_, i) => `page-${i}.mdx`);
		for (const name of names) repo.write(name, body(name));
		repo.commit('2024-09-09');
		chdir(t, repo.site);
		const calls = countGit(t);
		const firstPublished = await fresh();
		for (const name of names) {
			assert.equal(firstPublished(repo.path(name)), '2024-09-09');
			assert.equal(firstPublished(repo.path(name)), '2024-09-09');
		}
		assert.equal(firstPublished(repo.path('missing.mdx')), undefined);
		const seen = calls();
		assert.equal(seen.length, 2, seen.join('\n'));
		assert.match(seen[0], /^rev-parse /);
		assert.match(seen[1], /^log /);
	},
);

test(
	'where git cannot answer it is asked once, not once per page',
	{ skip: process.platform === 'win32' && 'counts through a shell script on the PATH' },
	async (t) => {
		const dir = tempDir(t);
		chdir(t, dir);
		const calls = countGit(t);
		const firstPublished = await fresh();
		for (let i = 0; i < 10; i += 1) assert.equal(firstPublished(`${DOCS}/page-${i}.mdx`), undefined);
		assert.equal(calls().length, 1, calls().join('\n'));
	},
);
