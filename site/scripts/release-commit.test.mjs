// Which pages changed after the latest release, on git histories small enough
// to read.
//
// The real history has had one release since the notice exists, so a rule
// that read the wrong commit as the release, or compared days where it has to
// compare times, would show the notice on the wrong pages there without a
// test to say so. Each test here writes a repository of its own: a VERSION,
// the release commit (tagged as the release workflow tags it, or not yet),
// one page whose content last changed before it and one after, and reads the
// release src/lib/release-commit.mjs finds and the pages it says changed after
// it, from the content dates src/lib/content-dates.mjs gives them, as
// src/routeData.ts and scripts/agent-md.mjs read both.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { loadContentDates } from '../src/lib/content-dates.mjs';
import { UNRELEASED_URL, changedAfter, loadRelease, releaseTag } from '../src/lib/release-commit.mjs';

/** This site and the repository holding it, for the test that reads the real tree. */
const SITE = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const REPO = resolve(SITE, '..');

/** A repository with a site in `site/`, committed at the times its tests name. */
function repository(t) {
	const root = mkdtempSync(join(tmpdir(), 'release-commit-'));
	t.after(() => rmSync(root, { recursive: true, force: true }));
	const home = join(root, 'home');
	mkdirSync(home);
	writeFileSync(join(home, 'gitconfig'), '[commit]\n\tgpgsign = false\n[tag]\n\tgpgsign = false\n[core]\n\thooksPath = /nonexistent\n');
	const work = join(root, 'repo');
	const site = join(work, 'site');
	mkdirSync(join(site, 'src', 'content', 'docs'), { recursive: true });
	const env = {
		...process.env,
		GIT_CONFIG_NOSYSTEM: '1',
		GIT_CONFIG_GLOBAL: join(home, 'gitconfig'),
		GIT_AUTHOR_NAME: 'Test',
		GIT_AUTHOR_EMAIL: 'test@example.org',
		GIT_COMMITTER_NAME: 'Test',
		GIT_COMMITTER_EMAIL: 'test@example.org',
	};
	const git = (args, extra = {}) => {
		const ran = spawnSync('git', args, { cwd: work, env: { ...env, ...extra }, encoding: 'utf8' });
		assert.equal(ran.status, 0, `git ${args.join(' ')}: ${ran.stderr}`);
		return ran.stdout.trim();
	};
	git(['init', '-q', '-b', 'main']);
	return {
		work,
		site,
		/** Write a file, `path` relative to the repository. */
		write(path, text) {
			mkdirSync(dirname(join(work, path)), { recursive: true });
			writeFileSync(join(work, path), text);
		},
		/** Write a page, `path` relative to the content directory. */
		page(path, body) {
			this.write(join('site', 'src', 'content', 'docs', path), `---\ntitle: ${path}\ndescription: A page.\n---\n\n${body}\n`);
		},
		/** Commit everything at `when` (an ISO time); returns the commit's SHA. */
		commit(when, message = when) {
			git(['add', '--all']);
			git(['commit', '-q', '-m', message], { GIT_AUTHOR_DATE: when, GIT_COMMITTER_DATE: when });
			return git(['rev-parse', 'HEAD']);
		},
		tag(name, sha) {
			git(['tag', name, sha]);
		},
	};
}

const AT = (day, time = '12:00:00') => `2026-03-${String(day).padStart(2, '0')}T${time}Z`;
const PAGE = (name) => join('src', 'content', 'docs', name);

/** Whether each page's content changed after the release the repository's VERSION names. */
async function newer(repo, version, ...pages) {
	const release = await loadRelease({ siteRoot: repo.site, version });
	const dates = await loadContentDates({ siteRoot: repo.site });
	return { release, newer: Object.fromEntries(pages.map((page) => [page, changedAfter(release, dates.dateOf(PAGE(page)))])) };
}

test('the release is the commit its tag names, and only a page changed after it is newer', async (t) => {
	const repo = repository(t);
	repo.write('VERSION', '1.0.0\n');
	repo.page('before.md', 'Written before the release.');
	repo.page('after.md', 'First text.');
	repo.commit(AT(1));
	repo.write('VERSION', '1.1.0\n');
	const released = repo.commit(AT(2), 'phonometry 1.1.0');
	repo.tag(releaseTag('1.1.0'), released);
	repo.page('after.md', 'Rewritten after the release.');
	repo.commit(AT(3));
	const { release, newer: is } = await newer(repo, '1.1.0', 'before.md', 'after.md');
	assert.equal(release.from, 'tag');
	assert.equal(release.sha, released);
	assert.equal(release.date.toISOString(), new Date(AT(2)).toISOString());
	assert.deepEqual(is, { 'before.md': false, 'after.md': true });
});

test('a page changed in the release commit itself is not newer than the release', async (t) => {
	const repo = repository(t);
	repo.write('VERSION', '1.1.0\n');
	repo.page('stamped.md', 'Stamped with the version by the release.');
	const released = repo.commit(AT(2));
	repo.tag('v1.1.0', released);
	assert.deepEqual((await newer(repo, '1.1.0', 'stamped.md')).newer, { 'stamped.md': false });
});

test('the times are compared, not the days: a change an hour after the release is newer', async (t) => {
	const repo = repository(t);
	repo.write('VERSION', '1.1.0\n');
	repo.page('same-day.md', 'First text.');
	repo.page('earlier.md', 'Changed the morning of the release.');
	repo.tag('v1.1.0', repo.commit(AT(2, '10:00:00')));
	repo.page('same-day.md', 'Fixed an hour after the release.');
	repo.commit(AT(2, '11:00:00'));
	assert.deepEqual((await newer(repo, '1.1.0', 'same-day.md', 'earlier.md')).newer, {
		'same-day.md': true,
		'earlier.md': false,
	});
});

test('with no tag yet, the release is the commit that made VERSION say what it says', async (t) => {
	const repo = repository(t);
	repo.write('VERSION', '1.0.0\n');
	repo.page('before.md', 'Written before the release.');
	repo.page('after.md', 'First text.');
	repo.commit(AT(1));
	repo.write('VERSION', '1.1.0\n');
	const stamped = repo.commit(AT(2), 'phonometry 1.1.0');
	repo.page('after.md', 'Rewritten after the release.');
	repo.commit(AT(3));
	const { release, newer: is } = await newer(repo, '1.1.0', 'before.md', 'after.md');
	assert.equal(release.from, 'VERSION');
	assert.equal(release.sha, stamped);
	assert.deepEqual(is, { 'before.md': false, 'after.md': true });
});

test('the tag wins over the commit that set VERSION when the two differ', async (t) => {
	const repo = repository(t);
	repo.write('VERSION', '1.1.0\n');
	repo.page('between.md', 'First text.');
	repo.commit(AT(1));
	repo.page('between.md', 'Changed after VERSION was set and before the release was published.');
	const published = repo.commit(AT(2));
	repo.tag('v1.1.0', published);
	const { release, newer: is } = await newer(repo, '1.1.0', 'between.md');
	assert.equal(release.from, 'tag');
	assert.equal(release.sha, published);
	assert.deepEqual(is, { 'between.md': false }, 'the release carries what its tag carries');
});

test('the tag of another version is not the release', async (t) => {
	const repo = repository(t);
	repo.write('VERSION', '1.0.0\n');
	repo.page('a.md', 'Text.');
	repo.tag('v1.0.0', repo.commit(AT(1)));
	repo.write('VERSION', '1.1.0\n');
	const stamped = repo.commit(AT(5));
	const { release } = await newer(repo, '1.1.0', 'a.md');
	assert.equal(release.sha, stamped, 'v1.0.0 is an older release; 1.1.0 has no tag yet');
});

test('a page written and not committed yet is newer than any release', async (t) => {
	const repo = repository(t);
	repo.write('VERSION', '1.1.0\n');
	repo.page('a.md', 'Text.');
	repo.tag('v1.1.0', repo.commit(AT(1)));
	repo.page('draft.md', 'Being written.');
	assert.deepEqual((await newer(repo, '1.1.0', 'a.md', 'draft.md')).newer, { 'a.md': false, 'draft.md': true });
});

test('an edit to a committed page counts once committed: the working tree alone moves no date', async (t) => {
	const repo = repository(t);
	repo.write('VERSION', '1.1.0\n');
	repo.page('a.md', 'Text.');
	repo.tag('v1.1.0', repo.commit(AT(1)));
	repo.page('a.md', 'Edited, not committed yet.');
	assert.deepEqual((await newer(repo, '1.1.0', 'a.md')).newer, { 'a.md': false });
});

test('a commit to the Spanish landing text leaves the English landing page as the release left it', async (t) => {
	// The entries site/date-sources.json gives the two landing pages, with
	// every file they name copied as it is: a source that holds the text of
	// both languages would date the English page by a Spanish edit, and show
	// it the notice for a change nobody reading it can see. The counts are
	// left out: they are numbers both pages show alike, of files the copy
	// does not hold.
	const english = 'site/src/content/docs/index.mdx';
	const spanish = 'site/src/content/docs/es/index.mdx';
	const { entries } = JSON.parse(readFileSync(join(SITE, 'date-sources.json'), 'utf8'));
	const landing = entries
		.filter((entry) => entry.pages.includes(english) || entry.pages.includes(spanish))
		.map(({ counts, ...entry }) => entry);
	const repo = repository(t);
	for (const path of new Set([english, spanish, ...landing.flatMap((entry) => entry.sources ?? [])])) {
		cpSync(join(REPO, path), join(repo.work, path), { recursive: true });
	}
	repo.write('site/date-sources.json', JSON.stringify({ entries: landing }));
	const version = readFileSync(join(REPO, 'VERSION'), 'utf8').trim();
	repo.tag(releaseTag(version), repo.commit(AT(1)));
	// The module the Spanish page takes its text from, edited inside the
	// Spanish object alone.
	const page = readFileSync(join(REPO, spanish), 'utf8');
	const from = /^import \{ es \} from '([^']+)';$/mu.exec(page)?.[1];
	assert.ok(from, `${spanish} imports its text as { es }`);
	const module = ['.ts', ''].map((ext) => join(dirname(join(repo.work, spanish)), `${from}${ext}`)).find((path) => {
		try {
			return readFileSync(path, 'utf8').includes('export const es');
		} catch {
			return false;
		}
	});
	assert.ok(module, `${from} holds the Spanish object`);
	const text = readFileSync(module, 'utf8');
	const title = text.indexOf("title: '", text.indexOf('export const es')) + "title: '".length;
	writeFileSync(module, `${text.slice(0, title)}Nuevo: ${text.slice(title)}`);
	repo.commit(AT(3));
	const release = await loadRelease({ siteRoot: repo.site, version });
	const dates = await loadContentDates({ siteRoot: repo.site });
	const after = (path) => changedAfter(release, dates.dateOf(path.replace(/^site\//u, '')));
	assert.deepEqual({ english: after(english), spanish: after(spanish) }, { english: false, spanish: true });
});

test('a clone with neither the tag nor a commit that set VERSION stops the build', async (t) => {
	const repo = repository(t);
	repo.page('a.md', 'Text.');
	repo.commit(AT(1));
	await assert.rejects(loadRelease({ siteRoot: repo.site, version: '9.9.9' }), /no tag v9\.9\.9 and no commit that set VERSION/u);
});

test('a directory outside any clone stops the build', async (t) => {
	const root = mkdtempSync(join(tmpdir(), 'release-commit-bare-'));
	t.after(() => rmSync(root, { recursive: true, force: true }));
	await assert.rejects(loadRelease({ siteRoot: root, version: '1.0.0' }), /release commit: git rev-parse --show-toplevel failed/u);
});

test('the tag is v and the version, and the changelog section is Unreleased on main', () => {
	assert.equal(releaseTag('4.0.0'), 'v4.0.0');
	assert.equal(releaseTag('4.1.0rc1'), 'v4.1.0rc1');
	assert.equal(UNRELEASED_URL, 'https://github.com/jmrplens/phonometry/blob/main/CHANGELOG.md#unreleased');
});
