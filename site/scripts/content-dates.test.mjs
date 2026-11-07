// The date a page's content last changed, on git histories small enough to read.
//
// The real history only ever hands the dates a build that reads them right,
// so a rule that stopped passing over a description-only commit, or a git
// failure that went back to leaving the dates empty, would stay unnoticed
// there for good. Each test here writes a repository of its own with the
// commits a case needs, dated a day apart, and reads the dates
// src/lib/content-dates.mjs gives it under the rule src/lib/date-rules.mjs
// states; the last ones run
// scripts/add-sitemap-lastmod.mjs on such a repository the way the build
// does, and read its exit status and the sitemap it wrote.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import {
	chmodSync,
	mkdirSync,
	mkdtempSync,
	readdirSync,
	readFileSync,
	renameSync,
	rmSync,
	utimesSync,
	writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { delimiter, dirname, join, relative, resolve } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';
import { domainIds } from '../src/data/topics.mjs';
import { loadContentDates } from '../src/lib/content-dates.mjs';
import {
	DATE_SOURCES,
	DATELESS_KEYS,
	frontmatterOnly,
	isoDay,
	readDateSources,
	readIgnoreRevs,
} from '../src/lib/date-rules.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const STAMP = join(HERE, 'add-sitemap-lastmod.mjs');
const PAGE_DATES = join(HERE, '..', 'src', 'lib', 'page-dates.mjs');
/** This site, for the tests that read the real tree. */
const SITE = resolve(HERE, '..');

/** Git as the tests run it: no user or system configuration, no signing. */
function gitEnv(home) {
	return {
		...process.env,
		GIT_CONFIG_NOSYSTEM: '1',
		GIT_CONFIG_GLOBAL: join(home, 'gitconfig'),
		GIT_AUTHOR_NAME: 'Test',
		GIT_AUTHOR_EMAIL: 'test@example.org',
		GIT_COMMITTER_NAME: 'Test',
		GIT_COMMITTER_EMAIL: 'test@example.org',
	};
}

/**
 * A repository with a site in `site/`, whose `commit(day)` dates each commit
 * at noon UTC on 2026-01-<day>, or at the moment a date string names.
 */
function repository(t) {
	const root = mkdtempSync(join(tmpdir(), 'content-dates-'));
	t.after(() => rmSync(root, { recursive: true, force: true }));
	const home = join(root, 'home');
	mkdirSync(home);
	writeFileSync(join(home, 'gitconfig'), '[commit]\n\tgpgsign = false\n[core]\n\thooksPath = /nonexistent\n');
	const work = join(root, 'repo');
	const site = join(work, 'site');
	const docs = join(site, 'src', 'content', 'docs');
	mkdirSync(docs, { recursive: true });
	const env = gitEnv(home);
	const git = (...args) => {
		const ran = spawnSync('git', args, { cwd: work, env, encoding: 'utf8' });
		assert.equal(ran.status, 0, `git ${args.join(' ')}: ${ran.stderr}`);
		return ran.stdout.trim();
	};
	git('init', '-q', '-b', 'main');
	const at = (day) => `2026-01-${String(day).padStart(2, '0')}T12:00:00Z`;
	return {
		root,
		work,
		site,
		env,
		git,
		/** Write a page, `path` relative to the content directory. */
		write(path, text) {
			mkdirSync(dirname(join(docs, path)), { recursive: true });
			writeFileSync(join(docs, path), text);
		},
		/** Write any file, `path` relative to the repository. */
		writeFile(path, text) {
			mkdirSync(dirname(join(work, path)), { recursive: true });
			writeFileSync(join(work, path), text);
		},
		/** Write `site/date-sources.json` with these entries. */
		sources(...entries) {
			writeFileSync(join(site, 'date-sources.json'), JSON.stringify({ entries }, null, 2));
		},
		move(from, to) {
			mkdirSync(dirname(join(docs, to)), { recursive: true });
			renameSync(join(docs, from), join(docs, to));
		},
		/** Commit everything, dated `day` (or at a date string); returns the commit's SHA. */
		commit(day, message = `day ${day}`) {
			git('add', '--all');
			const when = typeof day === 'string' ? day : at(day);
			const ran = spawnSync('git', ['commit', '-q', '-m', message], {
				cwd: work,
				env: { ...env, GIT_AUTHOR_DATE: when, GIT_COMMITTER_DATE: when },
				encoding: 'utf8',
			});
			assert.equal(ran.status, 0, ran.stderr);
			return git('rev-parse', 'HEAD');
		},
		/** Write `site/date-ignore-revs.txt`. */
		ignore(...lines) {
			writeFileSync(join(site, 'date-ignore-revs.txt'), `${lines.join('\n')}\n`);
		},
		async dates() {
			return loadContentDates({ siteRoot: site });
		},
	};
}

/** A page with the given frontmatter lines and body. */
const page = ({ title = 'A page', description = 'What it is.', extra = [], body = 'The text.\n' } = {}) =>
	['---', `title: ${title}`, `description: ${description}`, ...extra, '---', '', body].join('\n');

/** The day a page is dated, `path` relative to the content directory. */
const day = (dates, path) => isoDay(dates.dateOf(join('src', 'content', 'docs', path)));

// --- What counts as a change to the content ------------------------------

test('the dateless keys are title, description and sidebar', () => {
	assert.deepEqual([...DATELESS_KEYS], ['title', 'description', 'sidebar']);
});

test('a change inside the title, the description or the sidebar entry is frontmatter-only', () => {
	const before = page({ extra: ['sidebar:', '  order: 2', '  label: Short'] });
	assert.equal(frontmatterOnly(before, page({ description: 'Another line.', extra: ['sidebar:', '  order: 2', '  label: Short'] })), true);
	assert.equal(frontmatterOnly(before, page({ title: 'Renamed', extra: ['sidebar:', '  order: 2', '  label: Short'] })), true);
	assert.equal(frontmatterOnly(before, page({ extra: ['sidebar:', '  order: 7', '  badge: New'] })), true);
	assert.equal(frontmatterOnly(before, page()), true, 'dropping the sidebar entry');
	assert.equal(frontmatterOnly(before, before), true, 'no change at all');
});

test('a folded description and Windows line endings are read as one key', () => {
	const folded = (text) => page({ description: `>-\n  ${text}\n  over two lines.` });
	assert.equal(frontmatterOnly(folded('A long description'), folded('A longer description')), true);
	assert.equal(frontmatterOnly(page(), page({ description: 'New.' }).replace(/\n/g, '\r\n')), true);
});

test('the frontmatter ends at a fence line of its own, not at three hyphens ending a line', () => {
	const fenced = (text) => ['---', 'title: A page', `description: ${text} ---`, 'template: doc', '---', '', 'Body.', ''].join('\n');
	assert.equal(frontmatterOnly(fenced('One'), fenced('Two')), true);
	const changedKey = fenced('One').replace('template: doc', 'template: splash');
	assert.equal(frontmatterOnly(fenced('One'), changedKey), false, 'a key after the hyphens is still frontmatter');
	assert.equal(frontmatterOnly('---\n---\nBody.\n', '---\ndescription: New.\n---\nBody.\n'), true, 'an empty frontmatter');
});

test('a description added where there was none is frontmatter-only', () => {
	const bare = ['---', 'title: A page', '---', '', 'The text.', ''].join('\n');
	assert.equal(frontmatterOnly(bare, page()), true);
});

test('a change to the body counts', () => {
	assert.equal(frontmatterOnly(page(), page({ body: 'The text, corrected.\n' })), false);
	assert.equal(frontmatterOnly(page(), page({ description: 'New.', body: 'New text.\n' })), false);
});

test('a change to any other frontmatter key counts', () => {
	const references = (year) => page({ extra: ['references:', '  - type: standard', `    year: ${year}`] });
	assert.equal(frontmatterOnly(references(2010), references(2021)), false);
	assert.equal(frontmatterOnly(page(), page({ extra: ['template: splash'] })), false);
	assert.equal(frontmatterOnly(page(), page({ extra: ['# a note for editors'] })), false);
});

test('a frontmatter added to a page or taken from it counts', () => {
	const bare = 'The text.\n';
	assert.equal(frontmatterOnly(bare, `---\ntitle: A page\n---\n${bare}`), false);
	assert.equal(frontmatterOnly(`---\ntitle: A page\n---\n${bare}`, bare), false);
});

// --- Dates read from a history --------------------------------------------

test('a description-only commit does not move the date, and a body commit does', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', page());
	repo.commit(1);
	repo.write('a.mdx', page({ body: 'The text, corrected.\n' }));
	repo.commit(2);
	repo.write('a.mdx', page({ description: 'Cut to fit a search result.', body: 'The text, corrected.\n' }));
	repo.commit(3);
	repo.write('a.mdx', page({ title: 'Retitled', description: 'Cut to fit a search result.', body: 'The text, corrected.\n', extra: ['sidebar:', '  order: 1'] }));
	repo.commit(4);
	const dates = await repo.dates();
	assert.equal(day(dates, 'a.mdx'), '2026-01-02');
});

test('a run of frontmatter-only commits longer than one request is walked to its end', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', page());
	repo.write('b.md', page());
	repo.commit(1);
	repo.write('a.mdx', page({ body: 'Rewritten.\n' }));
	repo.commit(2);
	for (let n = 3; n <= 12; n += 1) {
		repo.write('a.mdx', page({ description: `Version ${n}.`, body: 'Rewritten.\n' }));
		repo.commit(n);
	}
	const dates = await repo.dates();
	assert.equal(day(dates, 'a.mdx'), '2026-01-02');
	assert.equal(day(dates, 'b.md'), '2026-01-01');
	assert.ok(dates.rounds >= 2, `${dates.rounds} round(s)`);
	assert.ok(dates.rounds <= 5, `${dates.rounds} rounds for a run of ten`);
});

test('a listed commit does not move the date, and a page it created is dated by it', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', page());
	repo.commit(1);
	repo.write('a.mdx', page({ body: 'Every lead sentence rewritten by a script.\n' }));
	repo.write('b.mdx', page());
	const sweep = repo.commit(2, 'a sweep');
	repo.ignore('# the sweep', `${sweep}  # trailing comment`);
	const dates = await repo.dates();
	assert.equal(day(dates, 'a.mdx'), '2026-01-01');
	assert.equal(day(dates, 'b.mdx'), '2026-01-02');
});

test('a page moved unchanged keeps its date, and one moved with an edit is dated by the move', async (t) => {
	const repo = repository(t);
	repo.write('old/a.mdx', page());
	repo.write('old/b.mdx', page({ title: 'B' }));
	repo.commit(1);
	repo.write('old/a.mdx', page({ body: 'Edited.\n' }));
	repo.commit(2);
	repo.move('old/a.mdx', 'new/a.mdx');
	repo.move('old/b.mdx', 'new/b.mdx');
	repo.write('new/b.mdx', page({ title: 'B', body: 'Moved and edited.\n' }));
	repo.commit(3);
	repo.write('new/a.mdx', page({ description: 'Moved, then described.', body: 'Edited.\n' }));
	repo.commit(4);
	const dates = await repo.dates();
	assert.equal(day(dates, 'new/a.mdx'), '2026-01-02');
	assert.equal(day(dates, 'new/b.mdx'), '2026-01-03');
});

test('a page git has never seen is dated by its file, and a path that is no page fails', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', page());
	repo.commit(1);
	repo.write('draft.mdx', page());
	const when = new Date('2026-03-04T05:06:07Z');
	utimesSync(join(repo.site, 'src', 'content', 'docs', 'draft.mdx'), when, when);
	const dates = await repo.dates();
	assert.equal(day(dates, 'draft.mdx'), '2026-03-04');
	assert.throws(() => dates.dateOf('src/content/docs/missing.mdx'), /missing\.mdx is not a file/);
});

test('the ignore list takes full SHAs only, and only of commits that changed a page', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', page());
	const first = repo.commit(1);
	writeFileSync(join(repo.site, 'notes.txt'), 'not content\n');
	const elsewhere = repo.commit(2);

	repo.ignore(first.slice(0, 9));
	assert.throws(() => readIgnoreRevs(join(repo.site, 'date-ignore-revs.txt')), /is not a full 40-character commit SHA/);

	repo.ignore(elsewhere);
	await assert.rejects(repo.dates(), new RegExp(`lists ${elsewhere}, which changed no page`));
});

test('a git failure fails instead of leaving the dates empty', async (t) => {
	const root = mkdtempSync(join(tmpdir(), 'content-dates-'));
	t.after(() => rmSync(root, { recursive: true, force: true }));
	const site = join(root, 'site');
	mkdirSync(join(site, 'src', 'content', 'docs'), { recursive: true });
	writeFileSync(join(site, 'src', 'content', 'docs', 'a.mdx'), page());
	// GIT_CEILING_DIRECTORIES keeps git from finding a repository above the
	// temporary directory, so this is a site with no history at all.
	process.env.GIT_CEILING_DIRECTORIES = root;
	t.after(() => delete process.env.GIT_CEILING_DIRECTORIES);
	await assert.rejects(
		loadContentDates({ siteRoot: site }),
		/is not in a git clone.*Build the site from a clone with its full history.*not from an archive.*git rev-parse --show-toplevel failed/s,
	);
});

test('a shallow clone fails instead of dating every page by its oldest fetched commit', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', page());
	repo.commit(1);
	repo.write('a.mdx', page({ body: 'Later.\n' }));
	repo.commit(2);
	const clone = join(repo.root, 'shallow');
	const ran = spawnSync('git', ['clone', '-q', '--depth', '1', `file://${repo.work}`, clone], {
		env: repo.env,
		encoding: 'utf8',
	});
	assert.equal(ran.status, 0, ran.stderr);
	await assert.rejects(loadContentDates({ siteRoot: join(clone, 'site') }), /this clone is shallow/);
});

test('a blobless clone fetches the page versions it needs in batches, never one by one', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', page());
	repo.write('b.mdx', page({ title: 'B' }));
	repo.commit(1);
	repo.write('a.mdx', page({ body: 'Edited.\n' }));
	repo.commit(2);
	repo.write('a.mdx', page({ description: 'Described.', body: 'Edited.\n' }));
	repo.write('b.mdx', page({ title: 'B', description: 'Described.' }));
	repo.commit(3);
	repo.git('config', 'uploadpack.allowFilter', 'true');
	repo.git('config', 'uploadpack.allowAnySHA1InWant', 'true');

	const clone = join(repo.root, 'blobless');
	const ran = spawnSync('git', ['clone', '-q', '--filter=blob:none', `file://${repo.work}`, clone], {
		env: repo.env,
		encoding: 'utf8',
	});
	assert.equal(ran.status, 0, ran.stderr);
	const missing = (oid) =>
		spawnSync('git', ['cat-file', '-e', oid], {
			cwd: clone,
			env: { ...repo.env, GIT_NO_LAZY_FETCH: '1' },
		}).status !== 0;
	const oldA = repo.git('rev-parse', 'HEAD~2:site/src/content/docs/a.mdx');
	assert.ok(missing(oldA), 'the clone starts without the first version of a.mdx');

	// Each fetch from the promisor remote, batched or lazy, leaves one pack
	// marked `.promisor`. The dates read the old versions with lazy fetching
	// switched off, so they come from one fetch per round or not at all; a
	// read that let git fetch each missing version on demand, or that fetched
	// them one per request, would leave a pack per version instead. Each round
	// of this history has a version to fetch: the first the two versions
	// before the description-only commit, the second the first a.mdx.
	const packs = () =>
		readdirSync(join(clone, '.git', 'objects', 'pack')).filter((name) => name.endsWith('.promisor')).length;
	const before = packs();
	const dates = await loadContentDates({ siteRoot: join(clone, 'site') });
	assert.equal(day(dates, 'a.mdx'), '2026-01-02');
	assert.equal(day(dates, 'b.mdx'), '2026-01-01');
	assert.ok(!missing(oldA), 'the version that decided the date was fetched');
	assert.equal(dates.rounds, 2);
	assert.equal(packs() - before, dates.rounds, 'one fetch per round, and no version fetched alone');
});

test('the dates are read once for a site, so a second load and every page\'s date start no process', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', page());
	repo.write('b.mdx', page({ title: 'B' }));
	repo.commit(1);
	repo.write('a.mdx', page({ description: 'Described.' }));
	repo.commit(2);
	// A git first on the PATH that notes each run and hands it to the real one,
	// so what is counted is processes, whichever call of the module started them.
	const shims = join(repo.root, 'shims');
	mkdirSync(shims);
	const real = spawnSync('sh', ['-c', 'command -v git'], { encoding: 'utf8' }).stdout.trim();
	const log = join(shims, 'calls');
	writeFileSync(log, '');
	writeFileSync(join(shims, 'git'), `#!/bin/sh\nprintf '%s\\n' "$*" >> '${log}'\nexec '${real}' "$@"\n`);
	chmodSync(join(shims, 'git'), 0o755);
	const path = process.env.PATH;
	process.env.PATH = `${shims}${delimiter}${path}`;
	t.after(() => {
		process.env.PATH = path;
	});
	const calls = () => readFileSync(log, 'utf8').split('\n').filter(Boolean).length;

	const first = await loadContentDates({ siteRoot: repo.site });
	const reading = calls();
	assert.ok(reading > 0, 'the count sees the git the dates are read with');
	for (let i = 0; i < 50; i += 1) {
		const again = await loadContentDates({ siteRoot: repo.site });
		assert.equal(again, first, 'every page gets the one reading');
		assert.equal(day(again, i % 2 ? 'a.mdx' : 'b.mdx'), '2026-01-01');
	}
	assert.equal(calls(), reading, 'no page after the first starts a process');
});

// --- Pages built from other files ----------------------------------------

test('a page is dated by a source that its description-only commit also changed', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', page());
	repo.write('b.mdx', page());
	repo.writeFile('site/src/data/table.json', '[1]\n');
	repo.commit(1);
	// The page's own change is to its description; what it shows changed in
	// the table it renders, in the same commit.
	repo.write('a.mdx', page({ description: 'Now with two rows.' }));
	repo.write('b.mdx', page({ description: 'Now with two rows.' }));
	repo.writeFile('site/src/data/table.json', '[1, 2]\n');
	repo.commit(2);
	repo.sources({ pages: ['site/src/content/docs/a.mdx'], sources: ['site/src/data/table.json'] });
	const dates = await repo.dates();
	assert.equal(day(dates, 'a.mdx'), '2026-01-02', 'the page that renders the table');
	assert.equal(day(dates, 'b.mdx'), '2026-01-01', 'a page that does not');
	assert.equal(dates.sourced, 1);
	assert.equal(dates.raised, 1);
});

test('a later commit that changed only a source moves the page, and an earlier one does not', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', page());
	repo.write('b.mdx', page());
	repo.writeFile('site/src/components/Table.astro', '<table />\n');
	repo.commit(1);
	repo.write('a.mdx', page({ body: 'Rewritten.\n' }));
	repo.write('b.mdx', page({ body: 'Rewritten.\n' }));
	repo.commit(2);
	repo.writeFile('site/src/components/Table.astro', '<table class="wide" />\n');
	repo.commit(3);
	repo.write('b.mdx', page({ body: 'Rewritten again.\n' }));
	repo.commit(4);
	repo.sources({
		pages: ['site/src/content/docs/a.mdx', 'site/src/content/docs/b.mdx'],
		sources: ['site/src/components/'],
	});
	const dates = await repo.dates();
	assert.equal(day(dates, 'a.mdx'), '2026-01-03', 'the component changed after the page');
	assert.equal(day(dates, 'b.mdx'), '2026-01-04', 'the page changed after the component');
});

test('a count moves the page only with a commit that changed how many files there are', async (t) => {
	const repo = repository(t);
	repo.write('a.mdx', page());
	repo.writeFile('site/fiches/one.pdf', 'one\n');
	repo.writeFile('site/fiches/one.txt', 'not counted\n');
	repo.commit(1);
	repo.writeFile('site/fiches/two.pdf', 'two\n');
	repo.commit(2, 'a fiche more: the count changes');
	repo.writeFile('site/fiches/one.pdf', 'one, redrawn\n');
	repo.commit(3, 'a fiche redrawn: the count stays');
	repo.git('mv', 'site/fiches/two.pdf', 'site/fiches/deux.pdf');
	repo.commit(4, 'a fiche renamed: the count stays');
	repo.writeFile('site/fiches/three.txt', 'not counted either\n');
	repo.commit(5, 'a file that is not counted');
	repo.sources({ pages: ['site/src/content/docs/a.mdx'], counts: { fiches: [':(glob)site/fiches/*.pdf'] } });
	const dates = await repo.dates();
	assert.equal(day(dates, 'a.mdx'), '2026-01-02');
});

test('a directory of the content tree stands for its pages, each dated by the page rule', async (t) => {
	const repo = repository(t);
	repo.write('errata/index.mdx', page({ title: 'Errata' }));
	repo.write('errata/iso-1.md', page({ title: 'ISO 1' }));
	repo.write('errata/iso-2.md', page({ title: 'ISO 2' }));
	repo.commit(1);
	repo.write('errata/iso-2.md', page({ title: 'ISO 2', body: 'A new entry.\n' }));
	repo.commit(2);
	repo.write('errata/iso-1.md', page({ title: 'ISO 1', description: 'Cut to 160 characters.' }));
	repo.commit(3);
	repo.sources({
		pages: ['site/src/content/docs/errata/index.mdx'],
		sources: ['site/src/content/docs/errata/'],
	});
	const dates = await repo.dates();
	assert.equal(day(dates, 'errata/index.mdx'), '2026-01-02', 'the newest entry, not the newest description');
	assert.equal(day(dates, 'errata/iso-1.md'), '2026-01-01', 'a listed page is no source of the others');
});

test('a page, a source or a count that HEAD does not have fails the build', async (t) => {
	const cases = [
		[{ pages: ['site/src/content/docs/gone.mdx'], sources: ['site/src/data/table.json'] }, /the page\(s\) site\/src\/content\/docs\/gone\.mdx, which HEAD does not have/],
		[{ pages: ['site/src/content/docs/a.mdx'], sources: ['site/src/data/renamed.json'] }, /the source site\/src\/data\/renamed\.json, which HEAD does not have/],
		[{ pages: ['site/src/content/docs/a.mdx'], counts: { fiches: [':(glob)site/fiches/*.pdf'] } }, /the counted files :\(glob\)site\/fiches\/\*\.pdf, which HEAD does not have/],
		[{ pages: ['site/src/data/table.json'], sources: ['site/src/data/table.json'] }, /as a page, and pages are under site\/src\/content\/docs\//],
	];
	for (const [entry, message] of cases) {
		const repo = repository(t);
		repo.write('a.mdx', page());
		repo.writeFile('site/src/data/table.json', '[1]\n');
		repo.commit(1);
		repo.sources(entry);
		await assert.rejects(repo.dates(), message);
	}
});

test('date-sources.json takes paths from the repository root, and an entry with pages and sources', (t) => {
	const root = mkdtempSync(join(tmpdir(), 'content-dates-'));
	t.after(() => rmSync(root, { recursive: true, force: true }));
	const file = join(root, DATE_SOURCES);
	const read = (data) => {
		writeFileSync(file, typeof data === 'string' ? data : JSON.stringify(data));
		return () => readDateSources(file);
	};
	const pages = ['site/src/content/docs/a.mdx'];
	assert.deepEqual(readDateSources(join(root, 'none.json')), [], 'no file, no sources');
	assert.deepEqual(read({ _comment: 'a note', entries: [{ _why: 'a note', pages, sources: ['docs/a.json'] }] })(), [
		{ pages, sources: ['docs/a.json'], counts: {} },
	]);
	assert.throws(read('{ not json'), /date-sources\.json: /);
	assert.throws(read({ pages }), /no "entries" list/);
	assert.throws(read({ entries: [{ pages, sources: ['a'], source: ['b'] }] }), /entry 1: unknown key\(s\) source/);
	assert.throws(read({ entries: [{ pages, sources: ['../outside.json'] }] }), /"sources" takes paths from the repository root, not "\.\.\/outside\.json"/);
	assert.throws(read({ entries: [{ pages, sources: [':(glob)*.json'] }] }), /"sources" takes paths/);
	assert.throws(read({ entries: [{ pages, counts: [['a/']] }] }), /"counts" maps the name of each number/);
	assert.throws(read({ entries: [{ pages, counts: { fiches: [] } }] }), /no pathspec for the count fiches/);
	assert.throws(read({ entries: [{ pages }] }), /entry 1 names no source/);
	assert.throws(read({ entries: [{ sources: ['a.json'] }] }), /entry 1 names no page/);
});

test('a count written over {topic} takes one directory per topic the navigation teaches', (t) => {
	const root = mkdtempSync(join(tmpdir(), 'content-dates-'));
	t.after(() => rmSync(root, { recursive: true, force: true }));
	const file = join(root, DATE_SOURCES);
	const index = ':(exclude,glob)site/src/content/docs/**/index.*';
	writeFileSync(
		file,
		JSON.stringify({
			entries: [{ pages: ['site/src/content/docs/index.mdx'], counts: { guides: ['site/src/content/docs/{topic}/', index] } }],
		}),
	);
	const guides = (options) => readDateSources(file, options)[0].counts.guides;
	assert.deepEqual(guides({ topics: ['signals', 'io'] }), [
		'site/src/content/docs/signals/',
		'site/src/content/docs/io/',
		index,
	]);
	// A topic added to the navigation is counted the day it is added, here and
	// in src/data/repo-stats.mjs alike, with no list of folders to keep.
	assert.deepEqual(guides(), [...domainIds.map((id) => `site/src/content/docs/${id}/`), index]);
	assert.throws(() => guides({ topics: [] }), /\{topic\} in counts\.guides, and the navigation teaches no topic/);
});

test('the day a page was published is its first commit\'s day in UTC, as the day it changed is', async (t) => {
	const repo = repository(t);
	repo.write('late.mdx', page());
	// Half past midnight in Madrid in summer is still the evening before in UTC.
	repo.commit('2026-07-02T00:30:00+02:00');
	const ran = spawnSync(
		process.execPath,
		[
			'--input-type=module',
			'-e',
			`import { firstPublished } from ${JSON.stringify(pathToFileURL(PAGE_DATES).href)};` +
				`console.log(firstPublished('src/content/docs/late.mdx'));`,
		],
		{ cwd: repo.site, env: repo.env, encoding: 'utf8' },
	);
	assert.equal(ran.status, 0, ran.stderr);
	assert.equal(ran.stdout.trim(), '2026-07-01');
	assert.equal(day(await repo.dates(), 'late.mdx'), '2026-07-01');
});

// --- The site's own list of pages built from other files -----------------

/** Modules that hold no text a page shows: the site's address and the icon shapes. */
const NOT_CONTENT = new Set(['src/data/site.mjs', 'src/data/icons.mjs']);
const IMPORT = /^\s*import\s[^;]*?from\s+['"]([^'"]+)['"]/gm;

/**
 * Why a module puts data from outside a page into it, or null: it is a data
 * module, it reads the content collection, or it imports one that does.
 */
function dataBehind(file, seen = new Map()) {
	if (seen.has(file)) return seen.get(file);
	seen.set(file, null);
	const rel = relative(SITE, file).split('\\').join('/');
	let why = null;
	if (/^src\/(data|generated)\//.test(rel)) why = NOT_CONTENT.has(rel) ? null : rel;
	else if (/\.(astro|mjs|ts)$/.test(file)) {
		let text = '';
		try {
			text = readFileSync(file, 'utf8');
		} catch {
			// A package or a virtual module: not this site's data.
		}
		if (/\b(getCollection|getEntry)\s*\(/.test(text)) why = `${rel} reads the content collection`;
		for (const [, spec] of text.matchAll(IMPORT)) {
			if (why || !spec.startsWith('.')) continue;
			const behind = dataBehind(resolveImport(file, spec), seen);
			if (behind) why = `${rel} imports ${behind}`;
		}
	}
	seen.set(file, why);
	return why;
}

/** An import specifier as the file it names, extension supplied as Vite would. */
function resolveImport(from, spec) {
	const target = resolve(dirname(from), spec);
	for (const candidate of [target, `${target}.ts`, `${target}.mjs`]) {
		try {
			readFileSync(candidate);
			return candidate;
		} catch {
			// Try the next spelling.
		}
	}
	return target;
}

/** Every page of the site, as repository paths. */
function sitePages(dir = join(SITE, 'src', 'content', 'docs'), out = []) {
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		const path = join(dir, entry.name);
		if (entry.isDirectory()) sitePages(path, out);
		else if (/\.mdx?$/.test(entry.name)) out.push(path);
	}
	return out;
}

const REPO = resolve(SITE, '..');
const repoPath = (file) => relative(REPO, file).split('\\').join('/');

/**
 * The files of HEAD some pathspecs match, matched the way src/lib/content-dates.mjs
 * matches a count: as `git log` matches them, by a diff from the empty tree.
 */
function filesAtHead(repo, pathspecs) {
	const git = (args, input) => spawnSync('git', args, { cwd: repo, input, encoding: 'utf8' });
	const empty = git(['hash-object', '-t', 'tree', '--stdin'], '').stdout.trim();
	const listed = git(['diff-tree', '-r', '-z', '--name-only', '--no-renames', empty, 'HEAD', '--', ...pathspecs]);
	assert.equal(listed.status, 0, listed.stderr);
	return listed.stdout.split('\0').filter(Boolean);
}

test('every page that renders data from outside its file is listed in date-sources.json, and no other', () => {
	const entries = readDateSources(join(SITE, DATE_SOURCES));
	const listed = (path) => entries.some((entry) => entry.pages.some((spec) => (spec.endsWith('/') ? path.startsWith(spec) : path === spec)));
	const unlisted = [];
	const needless = [];
	let built = 0;
	for (const file of sitePages()) {
		const text = readFileSync(file, 'utf8');
		let why = null;
		for (const [, spec] of text.matchAll(IMPORT)) {
			if (!why && spec.startsWith('.')) why = dataBehind(resolveImport(file, spec));
		}
		if (why) built += 1;
		if (why && !listed(repoPath(file))) unlisted.push(`${repoPath(file)}: ${why}`);
		if (!why && listed(repoPath(file))) needless.push(repoPath(file));
	}
	assert.ok(built > 0, 'the scan found no page built from data, so it is not looking');
	assert.deepEqual(unlisted, [], `${DATE_SOURCES} has to say what these pages are built from`);
	assert.deepEqual(needless, [], `${DATE_SOURCES} lists pages that render no data from outside their file`);
});

test('each count in date-sources.json covers the files repo-stats.mjs counts for the same number', async (t) => {
	const stats = await import(pathToFileURL(join(SITE, 'src', 'data', 'repo-stats.mjs')).href);
	const counts = readDateSources(join(SITE, DATE_SOURCES)).flatMap((entry) => Object.entries(entry.counts));
	assert.ok(counts.length > 0, 'the landing page counts guides, API pages and fiches');
	for (const [name, set] of counts) {
		assert.equal(typeof stats[name], 'number', `${name} is no number src/data/repo-stats.mjs exports`);
		// The comparison is at HEAD, which is what the dates read; a file added
		// or deleted and not committed yet would make it meaningless.
		const dirty = spawnSync('git', ['status', '--porcelain', '--', ...set], { cwd: REPO, encoding: 'utf8' });
		if (dirty.stdout.trim() !== '') {
			t.diagnostic(`${name}: uncommitted changes under its files, not compared`);
			continue;
		}
		assert.equal(filesAtHead(REPO, set).length, stats[name], `${name}: ${set.join(' ')}`);
	}
});

// --- The sitemap, stamped the way the build does it ----------------------

/** Write a sitemap listing `routes` into the site's build and run the stamp. */
function stamp(repo, routes) {
	const dist = join(repo.site, 'dist');
	mkdirSync(dist, { recursive: true });
	const urls = routes.map((route) => `<url><loc>${siteUrl}${basePath}/${route}</loc></url>`).join('');
	writeFileSync(
		join(dist, 'sitemap-index.xml'),
		`<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">` +
			`<sitemap><loc>${siteUrl}${basePath}/sitemap-0.xml</loc></sitemap></sitemapindex>`,
	);
	writeFileSync(
		join(dist, 'sitemap-0.xml'),
		`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`,
	);
	const ran = spawnSync(process.execPath, [STAMP, repo.site], { env: repo.env, encoding: 'utf8' });
	const xml = readFileSync(join(dist, 'sitemap-0.xml'), 'utf8');
	const lastmod = (route) =>
		new RegExp(`<loc>${siteUrl}${basePath}/${route}</loc><lastmod>([^<]+)</lastmod>`).exec(xml)?.[1];
	return { status: ran.status, out: ran.stdout, err: ran.stderr, lastmod };
}

test('the sitemap gives a page the date of its last content change, and a section the date of its index', async (t) => {
	const repo = repository(t);
	repo.write('index.mdx', page());
	repo.write('guide.mdx', page());
	repo.write('section/index.mdx', page());
	repo.write('es/index.mdx', page());
	repo.commit(1);
	repo.write('guide.mdx', page({ body: 'Edited.\n' }));
	repo.commit(2);
	repo.write('guide.mdx', page({ description: 'Cut to 160 characters.', body: 'Edited.\n' }));
	repo.write('section/index.mdx', page({ description: 'Cut to 160 characters.' }));
	repo.commit(3);
	const ran = stamp(repo, ['', 'guide/', 'section/', 'es/']);
	assert.equal(ran.status, 0, ran.err);
	assert.equal(ran.lastmod(''), '2026-01-01');
	assert.equal(ran.lastmod('guide/'), '2026-01-02');
	assert.equal(ran.lastmod('section/'), '2026-01-01');
	assert.equal(ran.lastmod('es/'), '2026-01-01');
	assert.match(ran.out, /stamped 4 URLs/);
});

test('a sitemap URL with no source fails the build, listed with every other one', async (t) => {
	const repo = repository(t);
	repo.write('guide.mdx', page());
	repo.commit(1);
	const ran = stamp(repo, ['guide/', 'gone/', 'also-gone/']);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL 2 sitemap URL\(s\) map to no file/);
	assert.match(ran.err, /\/gone\/\n.*\/also-gone\//);
	assert.equal(ran.lastmod('guide/'), undefined, 'nothing is written when a URL has no source');
});

test('a sitemap that cannot be dated fails the build instead of taking guessed dates', async (t) => {
	const repo = repository(t);
	repo.write('guide.mdx', page());
	repo.commit(1);
	rmSync(join(repo.work, '.git'), { recursive: true, force: true });
	const ran = stamp(repo, ['guide/']);
	assert.equal(ran.status, 1);
	assert.match(ran.err, /FAIL the page dates cannot be read/);
	assert.equal(ran.lastmod('guide/'), undefined);
});

test('a build with no sitemap to stamp fails instead of publishing one without dates', async (t) => {
	const repo = repository(t);
	repo.write('guide.mdx', page());
	repo.commit(1);
	const dist = join(repo.site, 'dist');
	mkdirSync(dist, { recursive: true });
	const run = () => spawnSync(process.execPath, [STAMP, repo.site], { env: repo.env, encoding: 'utf8' });

	let ran = run();
	assert.equal(ran.status, 1);
	assert.match(ran.stderr, /FAIL .*sitemap-index\.xml does not exist/);

	writeFileSync(join(dist, 'sitemap-index.xml'), '<sitemapindex></sitemapindex>');
	ran = run();
	assert.equal(ran.status, 1);
	assert.match(ran.stderr, /FAIL .*lists no sitemap/);

	writeFileSync(
		join(dist, 'sitemap-index.xml'),
		`<sitemapindex><sitemap><loc>${siteUrl}${basePath}/sitemap-renamed.xml</loc></sitemap></sitemapindex>`,
	);
	ran = run();
	assert.equal(ran.status, 1);
	assert.match(ran.stderr, /FAIL the sitemap index lists .*sitemap-renamed\.xml, which the build did not write/);
});
