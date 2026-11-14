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
	symlinkSync,
	utimesSync,
	writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { delimiter, dirname, join, relative, resolve, sep } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';
import { domainIds } from '../src/data/topics.mjs';
import { loadContentDates } from '../src/lib/content-dates.mjs';
import {
	CONTENT_DIR,
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

test('a count of lines moves the page only with a commit that changed how many lines match', async (t) => {
	const repo = repository(t);
	const registry = (...entries) => ['# Errata', '', ...entries.flatMap((entry) => [`## ${entry}`, '', 'What the source prints.', ''])].join('\n');
	repo.write('a.mdx', page());
	repo.write('b.mdx', page());
	repo.writeFile('docs/ERRATA.md', registry('One', 'Two'));
	repo.commit(1);
	repo.writeFile('docs/ERRATA.md', registry('One', 'Two', 'Three'));
	repo.commit(2, 'an entry more: the count changes');
	repo.writeFile('docs/ERRATA.md', registry('One', 'Two', 'Three').replace('What the source prints.', 'What the source\nprints.'));
	repo.commit(3, 'a line rewrapped inside an entry: the count stays');
	repo.writeFile('docs/ERRATA.md', registry('Uno', 'Two', 'Three'));
	repo.commit(4, 'an entry retitled: the count stays');
	repo.writeFile('docs/ERRATA.md', `${registry('Uno', 'Two', 'Three')}\n### A subsection\n\n##Not a heading\n`);
	repo.commit(5, 'lines the pattern does not match');
	repo.sources({ pages: ['site/src/content/docs/a.mdx'], counts: { errataEntries: { file: 'docs/ERRATA.md', lines: '^## .+$' } } });
	repo.commit(6, 'the list, for the clone below');
	const dates = await repo.dates();
	assert.equal(day(dates, 'a.mdx'), '2026-01-02', 'the commit that added an entry');
	assert.equal(day(dates, 'b.mdx'), '2026-01-01', 'a page that does not show the count');

	// The docs job's clone has no old version of the file: they are fetched
	// newest first, one request per round, each round asking for twice as many
	// commits as the last (here the newest, then the two before it, then the
	// one that added the entry), never one version at a time.
	repo.git('config', 'uploadpack.allowFilter', 'true');
	repo.git('config', 'uploadpack.allowAnySHA1InWant', 'true');
	const clone = join(repo.root, 'blobless');
	const ran = spawnSync('git', ['clone', '-q', '--filter=blob:none', `file://${repo.work}`, clone], { env: repo.env, encoding: 'utf8' });
	assert.equal(ran.status, 0, ran.stderr);
	const packs = () => readdirSync(join(clone, '.git', 'objects', 'pack')).filter((name) => name.endsWith('.promisor')).length;
	const before = packs();
	const fromClone = await loadContentDates({ siteRoot: join(clone, 'site') });
	assert.equal(day(fromClone, 'a.mdx'), '2026-01-02');
	assert.equal(packs() - before, 3, 'one fetch per round');
});

/** What the index of fiches reads off a guide: the declaration of each fiche it shows. */
const FICHE = '<ReportPreview\\b[^>]*?/>';
/** A guide that shows one fiche under `title`, with `more` after it. */
const guide = (title, more = '') =>
	page({ body: `The text.\n\n<ReportPreview\n\tname="one"\n\ttitle="${title}"\n\tdescription="One page."\n/>\n${more}` });
/** The English guides and nothing under es/, as the English index reads them. */
const ENGLISH_GUIDES = [':(glob)site/src/content/docs/**/*.mdx', ':(exclude,glob)site/src/content/docs/es/**'];

test('a text moves the page only with a commit that changed one of its matches', async (t) => {
	const repo = repository(t);
	repo.write('reports.mdx', page({ title: 'Fiches' }));
	repo.write('signals/guide.mdx', guide('First title'));
	repo.write('es/signals/guide.mdx', guide('Primer título'));
	repo.commit(1);
	repo.write('signals/guide.mdx', guide('Second title'));
	repo.commit(2, 'the title the index prints: the page moves');
	repo.write('signals/guide.mdx', guide('Second title', '\nA paragraph more.\n'));
	repo.commit(3, 'the guide changes outside its fiche: the page stays');
	repo.write('signals/guide.mdx', guide('Second title', '\nA paragraph more.\n').replace('\n\tdescription', ' description'));
	repo.commit(4, 'the declaration rewrapped: the page stays');
	repo.write('es/signals/guide.mdx', guide('Segundo título'));
	repo.commit(5, 'a guide the text leaves out');
	repo.sources({ pages: ['site/src/content/docs/reports.mdx'], texts: { reportsByArea: { files: ENGLISH_GUIDES, pattern: FICHE } } });
	repo.commit(6, 'the list, for the clone below');
	const dates = await repo.dates();
	assert.equal(day(dates, 'reports.mdx'), '2026-01-02', 'the commit that retitled the fiche');
	assert.equal(day(dates, 'signals/guide.mdx'), '2026-01-04', 'the guide keeps its own date');

	// The docs job's clone has no old version of a guide: they are fetched as
	// a count of lines fetches them, in rounds, and the date is the same.
	repo.git('config', 'uploadpack.allowFilter', 'true');
	repo.git('config', 'uploadpack.allowAnySHA1InWant', 'true');
	const clone = join(repo.root, 'blobless');
	const ran = spawnSync('git', ['clone', '-q', '--filter=blob:none', `file://${repo.work}`, clone], { env: repo.env, encoding: 'utf8' });
	assert.equal(ran.status, 0, ran.stderr);
	const fromClone = await loadContentDates({ siteRoot: join(clone, 'site') });
	assert.equal(day(fromClone, 'reports.mdx'), '2026-01-02');
});

test('a guide moved to another folder, or a fiche added or taken out, moves the page that shows its text', async (t) => {
	for (const [change, expected] of [
		[(repo) => repo.move('signals/guide.mdx', 'vibration/guide.mdx'), 'a guide moved'],
		[(repo) => repo.write('signals/other.mdx', guide('Another fiche')), 'a fiche added'],
		[(repo) => repo.write('signals/guide.mdx', page()), 'a fiche taken out'],
	]) {
		const repo = repository(t);
		repo.write('reports.mdx', page({ title: 'Fiches' }));
		repo.write('signals/guide.mdx', guide('A title'));
		repo.sources({ pages: ['site/src/content/docs/reports.mdx'], texts: { reportsByArea: { files: ENGLISH_GUIDES, pattern: FICHE } } });
		repo.commit(1);
		change(repo);
		repo.commit(2, expected);
		assert.equal(day(await repo.dates(), 'reports.mdx'), '2026-01-02', expected);
	}
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
		[{ pages: ['site/src/content/docs/a.mdx'], counts: { entries: { file: 'docs/GONE.md', lines: '^## ' } } }, /the counted file docs\/GONE\.md, which HEAD does not have/],
		[{ pages: ['site/src/content/docs/a.mdx'], texts: { shown: { files: [':(glob)site/guides/*.mdx'], pattern: 'x' } } }, /the files of the text :\(glob\)site\/guides\/\*\.mdx, which HEAD does not have/],
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
		{ pages, sources: ['docs/a.json'], counts: {}, texts: {} },
	]);
	assert.throws(read('{ not json'), /date-sources\.json: /);
	assert.throws(read({ pages }), /no "entries" list/);
	assert.throws(read({ entries: [{ pages, sources: ['a'], source: ['b'] }] }), /entry 1: unknown key\(s\) source/);
	assert.throws(read({ entries: [{ pages, sources: ['../outside.json'] }] }), /"sources" takes paths from the repository root, not "\.\.\/outside\.json"/);
	assert.throws(read({ entries: [{ pages, sources: [':(glob)*.json'] }] }), /"sources" takes paths/);
	assert.throws(read({ entries: [{ pages, counts: [['a/']] }] }), /"counts" maps the name of each number/);
	assert.throws(read({ entries: [{ pages, counts: { fiches: [] } }] }), /no pathspec for the count fiches/);
	const entries = { file: 'docs/ERRATA.md', lines: '^## .+$' };
	assert.deepEqual(read({ entries: [{ pages, counts: { entries } }] })(), [{ pages, sources: [], counts: { entries }, texts: {} }]);
	assert.throws(read({ entries: [{ pages, counts: { entries: { ...entries, file: 'docs/' } } }] }), /counts\.entries\.file names a file, not "docs\/"/);
	assert.throws(read({ entries: [{ pages, counts: { entries: { ...entries, file: '../ERRATA.md' } } }] }), /"counts\.entries\.file" takes paths from the repository root/);
	assert.throws(read({ entries: [{ pages, counts: { entries: { file: 'docs/ERRATA.md' } } }] }), /counts\.entries\.lines is the pattern of the lines it counts/);
	assert.throws(read({ entries: [{ pages, counts: { entries: { ...entries, lines: '(' } } }] }), /counts\.entries\.lines: Invalid regular expression/);
	assert.throws(read({ entries: [{ pages, counts: { entries: { ...entries, glob: '*' } } }] }), /unknown key\(s\) glob in counts\.entries/);
	const fiches = { files: [':(glob)site/src/content/docs/**/*.mdx'], pattern: '<ReportPreview\\b[^>]*?/>' };
	assert.deepEqual(read({ entries: [{ pages, texts: { fiches } }] })(), [{ pages, sources: [], counts: {}, texts: { fiches } }]);
	assert.throws(read({ entries: [{ pages, texts: [fiches] }] }), /"texts" maps the name of each text to its files and its pattern/);
	assert.throws(read({ entries: [{ pages, texts: { fiches: fiches.files } }] }), /texts\.fiches is \{ "files": pathspecs, "pattern": pattern \}/);
	assert.throws(read({ entries: [{ pages, texts: { fiches: { ...fiches, files: [] } } }] }), /no pathspec for the text fiches/);
	assert.throws(read({ entries: [{ pages, texts: { fiches: { ...fiches, files: ['../guides/'] } } }] }), /"texts\.fiches\.files" takes paths from the repository root or git pathspecs/);
	assert.throws(read({ entries: [{ pages, texts: { fiches: { files: fiches.files } } }] }), /texts\.fiches\.pattern is the pattern of the text it shows/);
	assert.throws(read({ entries: [{ pages, texts: { fiches: { ...fiches, pattern: '(' } } }] }), /texts\.fiches\.pattern: Invalid regular expression/);
	assert.throws(read({ entries: [{ pages, texts: { fiches: { ...fiches, lines: 'x' } } }] }), /unknown key\(s\) lines in texts\.fiches/);
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
/** An import that brings a value, with what it binds: `import type` brings none. */
const IMPORT = /^\s*import\s+(?!type\s)([^;]*?)\s*from\s+['"]([^'"]+)['"]/gm;

/** The banner that make conformance draws from the report, with the counts every page states. */
const BANNER = '.github/badges/conformance-summary.svg';

/**
 * The modules that read the repository when the site builds, and what each
 * of their exports is read from: the files whose commits change it, any one
 * of which the entry of a page that shows it has to name as a source;
 * `count`, a number of files or lines the entry has to carry under the
 * export's own name; or `text`, the matches of a pattern in some files,
 * which the entry has to carry under the export's own name too. A page that
 * shows an export is dated by what it is read from, which the imports alone
 * do not show.
 */
const READS = {
	'site/src/data/repo-stats.mjs': {
		version: ['VERSION'],
		guides: 'count',
		apiPages: 'count',
		figures: 'count',
		fiches: 'count',
		catalogueRows: ['site/src/generated/catalogues.mjs'],
		catalogueCount: ['site/src/generated/catalogues.mjs'],
	},
	'site/src/data/conformance-stats.mjs': {
		passingChecks: [BANNER, 'docs/conformance.json'],
		totalChecks: [BANNER, 'docs/conformance.json'],
		domains: [BANNER, 'docs/conformance.json'],
		designations: [BANNER, 'docs/conformance.json'],
		sources: [BANNER, 'docs/conformance.json'],
		checksRatio: [BANNER, 'docs/conformance.json'],
		report: ['docs/conformance.json'],
		errataEntries: 'count',
	},
	// The title and the sentence each guide gives a fiche in its
	// <ReportPreview>, read off the guides, English and Spanish.
	'site/src/data/reports.mjs': {
		reports: 'text',
		reportsEs: 'text',
		reportsByArea: 'text',
		reportsByAreaEs: 'text',
		reportCount: 'count',
	},
};

/** The names an import clause binds from its module; `*` for all of them. */
function boundNames(clause) {
	const names = [];
	const braces = /\{([^}]*)\}/.exec(clause);
	if (braces) {
		for (const part of braces[1].split(',').map((text) => text.trim())) {
			if (part === '' || part.startsWith('type ')) continue;
			const name = part.split(/\s+as\s+/)[0];
			names.push(name === 'default' ? '*' : name);
		}
	}
	// A default or a namespace binding takes the whole module.
	if (/^\s*[\w$]+\s*(,|$)/.test(clause) || /\*\s+as\s/.test(clause)) names.push('*');
	return names;
}

/**
 * What a module brings into a page from outside the page's own file, as
 * repository paths, each under its kind: every data module it reaches
 * (`src/data`, `src/generated`), through any chain of imports and the data
 * modules' own, as `data`, and every module that reads the content
 * collection as `collection`. With `carriers`, also every component
 * (`src/components`) on the way to one of those, which writes what it
 * reaches into the page in words of its own, as `carrier`. `bound` gathers,
 * for each module that reads the repository at build time, the names
 * imported from it on the way.
 *
 * @param {string} file
 * @param {string} [site]
 * @param {Map<string, 'data' | 'collection' | 'carrier'>} [out]
 * @param {Set<string>} [seen]
 * @param {Map<string, Set<string>>} [bound]
 * @param {boolean} [carriers]
 * @param {Map<string, boolean>} [carrying] whether each module read so far reaches data
 * @returns {Map<string, 'data' | 'collection' | 'carrier'>}
 */
function reach(file, site = SITE, out = new Map(), seen = new Set(), bound = new Map(), carriers = false, carrying = new Map()) {
	if (seen.has(file)) return out;
	seen.add(file);
	const rel = relative(site, file).split(sep).join('/');
	if (NOT_CONTENT.has(rel)) return out;
	const path = relative(resolve(site, '..'), file).split(sep).join('/');
	let carries = /^src\/(data|generated)\//.test(rel);
	if (carries) out.set(path, 'data');
	carrying.set(file, carries);
	if (!/\.(astro|mjs|ts|mdx?)$/.test(file)) return out;
	let text = '';
	try {
		text = readFileSync(file, 'utf8');
	} catch {
		return out; // A package or a virtual module: not this site's data.
	}
	if (/\b(getCollection|getEntry)\s*\(/.test(text)) {
		out.set(path, 'collection');
		carries = true;
	}
	for (const [, clause, spec] of text.matchAll(IMPORT)) {
		if (!spec.startsWith('.')) continue;
		const target = resolveImport(file, spec);
		const module = relative(resolve(site, '..'), target).split(sep).join('/');
		if (!bound.has(module)) bound.set(module, new Set());
		for (const name of boundNames(clause)) bound.get(module).add(name);
		reach(target, site, out, seen, bound, carriers, carrying);
		if (carrying.get(target)) carries = true;
	}
	carrying.set(file, carries);
	if (carriers && carries && !out.has(path) && /^src\/components\/.+\.astro$/.test(rel)) out.set(path, 'carrier');
	return out;
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

/** Every page of the site, as file paths. */
function sitePages(dir = join(SITE, CONTENT_DIR), out = []) {
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		const path = join(dir, entry.name);
		if (entry.isDirectory()) sitePages(path, out);
		else if (/\.mdx?$/.test(entry.name)) out.push(path);
	}
	return out;
}

const REPO = resolve(SITE, '..');

/**
 * What a site's date-sources.json leaves out of what its pages show: a page
 * that reaches data and has no entry, a listed page that reaches none, and
 * for each entry a data module or a reader of the content collection that
 * its pages reach, or a component that carries one of them into the page,
 * and that neither "sources" nor "_via" names. "_via" maps
 * such a module to the source the entry dates it by (a path, which the
 * entry has to name in "sources" or as a count) or to the reason it moves
 * no page (a sentence). A reader of the content collection always needs
 * one, since naming the reader as a source dates the page by the reader's
 * code, not by the pages it reads. A "_via" key that none of the entry's
 * pages reaches, or that "sources" already names, is wrong too. And an
 * export of a module that reads the repository at build time (`reads`)
 * that the pages import has to be dated by what it is read from.
 *
 * @param {string} [site]
 * @param {Record<string, Record<string, string[] | 'count' | 'text'>>} [reads]
 * @returns {{ problems: string[], built: number }}
 */
function auditDateSources(site = SITE, reads = READS) {
	const file = join(site, DATE_SOURCES);
	const raw = JSON.parse(readFileSync(file, 'utf8')).entries;
	const entries = readDateSources(file);
	const repo = resolve(site, '..');
	const matches = (spec, path) => (spec.endsWith('/') ? path.startsWith(spec) : path === spec);
	const problems = [];
	const reached = entries.map(() => new Map());
	const imported = entries.map(() => new Map());
	let built = 0;
	for (const page of sitePages(join(site, CONTENT_DIR))) {
		const path = relative(repo, page).split(sep).join('/');
		const bound = new Map();
		const behind = reach(page, site, new Map(), new Set(), bound, true);
		const owners = entries.flatMap((entry, index) => (entry.pages.some((spec) => matches(spec, path)) ? [index] : []));
		if (behind.size > 0) built += 1;
		if (behind.size > 0 && owners.length === 0) {
			problems.push(`${path} shows what ${[...behind.keys()].join(', ')} hold(s), and no entry lists it`);
		}
		if (behind.size === 0 && owners.length > 0) problems.push(`${path} is listed, and renders nothing from outside its file`);
		for (const index of owners) {
			for (const [module, kind] of behind) reached[index].set(module, kind);
			for (const [module, names] of bound) {
				if (!imported[index].has(module)) imported[index].set(module, new Set());
				for (const name of names) imported[index].get(module).add(name);
			}
		}
	}
	entries.forEach((entry, index) => {
		const where = `entry ${index + 1} (${entry.pages[0]})`;
		const via = raw[index]._via ?? {};
		const named = (path) => entry.sources.some((spec) => matches(spec, path));
		for (const [module, kind] of reached[index]) {
			if (kind !== 'collection' && named(module)) {
				if (Object.hasOwn(via, module)) problems.push(`${where}: "_via" explains ${module}, which "sources" already names`);
			} else if (!Object.hasOwn(via, module)) {
				const what = {
					data: 'the data of',
					carrier: 'what is written from data by',
					collection: 'the pages of the content collection that are read by',
				}[kind];
				problems.push(`${where}: its pages show ${what} ${module}, and neither "sources" nor "_via" names it`);
			}
		}
		for (const [module, why] of Object.entries(via)) {
			if (!reached[index].has(module)) problems.push(`${where}: "_via" names ${module}, which none of its pages reaches`);
			if (typeof why !== 'string' || why.trim() === '') {
				problems.push(`${where}: "_via" gives ${module} neither a source nor a reason`);
			} else if (!/\s/.test(why) && !named(why) && !Object.hasOwn(entry.counts, why)) {
				problems.push(`${where}: "_via" dates ${module} by ${why}, which is neither a source nor a count of the entry`);
			}
		}
		for (const [module, exports] of Object.entries(reads)) {
			const names = imported[index].get(module) ?? new Set();
			for (const name of names.has('*') ? Object.keys(exports) : names) {
				const from = exports[name];
				if (from === undefined) problems.push(`${where}: its pages show ${name} of ${module}, and the test does not say what that is read from`);
				else if (from === 'count' && !Object.hasOwn(entry.counts, name)) {
					problems.push(`${where}: its pages show ${name} of ${module}, a count the entry does not carry`);
				} else if (from === 'text' && !Object.hasOwn(entry.texts, name)) {
					problems.push(`${where}: its pages show ${name} of ${module}, a text the entry does not carry`);
				} else if (Array.isArray(from) && !from.some((file) => named(file))) {
					problems.push(`${where}: its pages show ${name} of ${module}, read from ${from.join(' or ')}, which "sources" does not name`);
				}
			}
		}
	});
	return { problems, built };
}

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

test('a listed page has to name every module it reaches, in "sources" or in "_via"', (t) => {
	const root = mkdtempSync(join(tmpdir(), 'content-dates-'));
	t.after(() => rmSync(root, { recursive: true, force: true }));
	const site = join(root, 'repo', 'site');
	const write = (path, text) => {
		mkdirSync(dirname(join(site, path)), { recursive: true });
		writeFileSync(join(site, path), text);
	};
	write('src/content/docs/a.mdx', "import { count } from '../../data/numbers.mjs';\n\n{count} rows.\n");
	write('src/content/docs/b.mdx', "import Index from '../../components/Index.astro';\n\n<Index />\n");
	write('src/content/docs/c.mdx', 'Plain text.\n');
	write('src/data/numbers.mjs', "import { rows } from './rows.mjs';\nimport { siteUrl } from './site.mjs';\nexport const count = rows.length;\n");
	write('src/data/rows.mjs', 'export const rows = [1, 2];\n');
	write('src/data/site.mjs', "export const siteUrl = 'https://example.org';\n");
	write('src/components/Index.astro', "---\nimport type { Shape } from '../data/shape.mjs';\nimport { getCollection } from 'astro:content';\nconst docs = await getCollection('docs');\n---\n");
	write('src/data/shape.mjs', 'export const shape = 1;\n');
	const page = (name) => `site/src/content/docs/${name}`;
	const audit = (...entries) => {
		write(DATE_SOURCES, JSON.stringify({ entries }));
		return auditDateSources(site, {}).problems;
	};
	const a = { pages: [page('a.mdx')], sources: ['site/src/data/numbers.mjs'], _via: { 'site/src/data/rows.mjs': 'the rows that numbers.mjs counts, as the page shows them' } };
	const b = { pages: [page('b.mdx')], sources: [page('c.mdx')], _via: { 'site/src/components/Index.astro': page('c.mdx') } };

	assert.deepEqual(audit(a, b), [], 'every module named; the site address and a type import are not data');
	assert.deepEqual(audit({ ...a, _via: {} }, b), [
		'entry 1 (site/src/content/docs/a.mdx): its pages show the data of site/src/data/rows.mjs, and neither "sources" nor "_via" names it',
	]);
	assert.deepEqual(audit(a, { ...b, sources: [page('c.mdx'), 'site/src/components/Index.astro'], _via: {} }), [
		'entry 2 (site/src/content/docs/b.mdx): its pages show the pages of the content collection that are read by site/src/components/Index.astro, and neither "sources" nor "_via" names it',
	]);
	assert.deepEqual(audit(a, { ...b, _via: { 'site/src/components/Index.astro': page('a.mdx') } }), [
		'entry 2 (site/src/content/docs/b.mdx): "_via" dates site/src/components/Index.astro by site/src/content/docs/a.mdx, which is neither a source nor a count of the entry',
	]);
	assert.deepEqual(audit({ ...a, _via: { ...a._via, 'site/src/data/numbers.mjs': 'the number of rows', 'site/src/data/gone.mjs': 'a module no page imports' } }, b), [
		'entry 1 (site/src/content/docs/a.mdx): "_via" explains site/src/data/numbers.mjs, which "sources" already names',
		'entry 1 (site/src/content/docs/a.mdx): "_via" names site/src/data/gone.mjs, which none of its pages reaches',
	]);
	assert.deepEqual(audit(a, b, { pages: [page('c.mdx')], sources: ['site/src/data/rows.mjs'] }), [
		'site/src/content/docs/c.mdx is listed, and renders nothing from outside its file',
	]);
	assert.deepEqual(audit(a), [
		'site/src/content/docs/b.mdx shows what site/src/components/Index.astro hold(s), and no entry lists it',
	]);

	// A module that reads the repository as the site builds: what the page
	// shows of it is dated by the files each export is read from.
	const readsOf = (count) => auditDateSources(site, { 'site/src/data/numbers.mjs': { count } }).problems;
	write(DATE_SOURCES, JSON.stringify({ entries: [a, b] }));
	assert.deepEqual(readsOf(['site/src/data/rows.mjs']), [
		'entry 1 (site/src/content/docs/a.mdx): its pages show count of site/src/data/numbers.mjs, read from site/src/data/rows.mjs, which "sources" does not name',
	]);
	assert.deepEqual(readsOf('count'), [
		'entry 1 (site/src/content/docs/a.mdx): its pages show count of site/src/data/numbers.mjs, a count the entry does not carry',
	]);
	// What a page shows of the guides, as the index of fiches shows the title
	// and the sentence of each fiche, is a text the entry has to carry: the
	// module that reads it is a source of the entry, which dates the page by
	// its code and not by the guides.
	assert.deepEqual(readsOf('text'), [
		'entry 1 (site/src/content/docs/a.mdx): its pages show count of site/src/data/numbers.mjs, a text the entry does not carry',
	]);
	write(DATE_SOURCES, JSON.stringify({ entries: [{ ...a, texts: { count: { files: [page('c.mdx')], pattern: 'Plain' } } }, b] }));
	assert.deepEqual(readsOf('text'), []);
	assert.deepEqual(auditDateSources(site, { 'site/src/data/numbers.mjs': {} }).problems, [
		'entry 1 (site/src/content/docs/a.mdx): its pages show count of site/src/data/numbers.mjs, and the test does not say what that is read from',
	]);
	write(DATE_SOURCES, JSON.stringify({ entries: [{ ...a, sources: ['site/src/data/numbers.mjs', 'site/src/data/rows.mjs'], _via: {} }, b] }));
	assert.deepEqual(readsOf(['site/src/data/rows.mjs']), []);

	// A component that writes what a data module holds into the page carries
	// it: the page shows the component's words around the data, so the entry
	// names the component as well, or says why it moves no page.
	write('src/content/docs/d.mdx', "import Rows from '../../components/Rows.astro';\n\n<Rows />\n");
	write('src/components/Rows.astro', "---\nimport { rows } from '../data/rows.mjs';\n---\n<p>{rows.length} rows</p>\n");
	const d = { pages: [page('d.mdx')], sources: ['site/src/data/rows.mjs'] };
	assert.deepEqual(audit(a, b, d), [
		'entry 3 (site/src/content/docs/d.mdx): its pages show what is written from data by site/src/components/Rows.astro, and neither "sources" nor "_via" names it',
	]);
	assert.deepEqual(audit(a, b, { ...d, sources: [...d.sources, 'site/src/components/Rows.astro'] }), []);
	assert.deepEqual(audit(a, b, { ...d, _via: { 'site/src/components/Rows.astro': 'what it writes around the rows moves no page' } }), []);
	assert.deepEqual(audit(a, b, { ...d, sources: [...d.sources, 'site/src/components/Rows.astro'], _via: { 'site/src/components/Rows.astro': 'site/src/data/rows.mjs' } }), [
		'entry 3 (site/src/content/docs/d.mdx): "_via" explains site/src/components/Rows.astro, which "sources" already names',
	]);
});

test('every page that renders data from outside its file is listed in date-sources.json with all of it, and no other', async () => {
	const { problems, built } = auditDateSources();
	assert.ok(built > 0, 'the scan found no page built from data, so it is not looking');
	assert.deepEqual(problems, [], `${DATE_SOURCES} has to say what these pages are built from`);
	// The table of what each export is read from covers every export, so a
	// number added to one of these modules has to say where it comes from.
	for (const [module, exports] of Object.entries(READS)) {
		const names = Object.keys(await import(pathToFileURL(join(REPO, module)).href)).filter((name) => name !== 'default');
		assert.deepEqual(names.sort(), Object.keys(exports).sort(), `what each export of ${module} is read from`);
	}
});

test('each count in date-sources.json is the number the page shows: files as repo-stats.mjs counts them, lines as conformance-stats.mjs does', async (t) => {
	const stats = await import(pathToFileURL(join(SITE, 'src', 'data', 'repo-stats.mjs')).href);
	const conformance = await import(pathToFileURL(join(SITE, 'src', 'data', 'conformance-stats.mjs')).href);
	const counts = readDateSources(join(SITE, DATE_SOURCES)).flatMap((entry) => Object.entries(entry.counts));
	assert.ok(counts.some(([, set]) => Array.isArray(set)), 'the landing page counts guides, API pages and fiches');
	assert.ok(counts.some(([, set]) => !Array.isArray(set)), 'the guide on why phonometry counts the errata entries');
	for (const [name, set] of counts) {
		if (!Array.isArray(set)) {
			assert.equal(typeof conformance[name], 'number', `${name} is no number src/data/conformance-stats.mjs exports`);
			const head = spawnSync('git', ['show', `HEAD:${set.file}`], { cwd: REPO, encoding: 'utf8', maxBuffer: 1 << 28 });
			assert.equal(head.status, 0, head.stderr);
			const dirty = spawnSync('git', ['status', '--porcelain', '--', set.file], { cwd: REPO, encoding: 'utf8' });
			if (dirty.stdout.trim() !== '') {
				t.diagnostic(`${name}: uncommitted changes to ${set.file}, not compared`);
				continue;
			}
			assert.equal(head.stdout.match(new RegExp(set.lines, 'gm'))?.length ?? 0, conformance[name], `${name}: ${set.file} ${set.lines}`);
			continue;
		}
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

test('each text in date-sources.json is the one the page shows: the fiches reports.mjs reads off the guides', async (t) => {
	const reports = await import(pathToFileURL(join(SITE, 'src', 'data', 'reports.mjs')).href);
	const texts = readDateSources(join(SITE, DATE_SOURCES)).flatMap((entry) => Object.entries(entry.texts));
	assert.ok(texts.length > 0, 'the index of fiches shows what the guides say of each fiche');
	for (const [name, set] of texts) {
		assert.ok(Object.hasOwn(READS['site/src/data/reports.mjs'], name), `${name} is no export of src/data/reports.mjs`);
		// The comparison is at HEAD, which is what the dates read.
		const dirty = spawnSync('git', ['status', '--porcelain', '--', ...set.files], { cwd: REPO, encoding: 'utf8' });
		if (dirty.stdout.trim() !== '') {
			t.diagnostic(`${name}: uncommitted changes under its files, not compared`);
			continue;
		}
		const matched = new Set();
		for (const file of filesAtHead(REPO, set.files)) {
			const head = spawnSync('git', ['show', `HEAD:${file}`], { cwd: REPO, encoding: 'utf8', maxBuffer: 1 << 28 });
			assert.equal(head.status, 0, head.stderr);
			for (const [match] of head.stdout.matchAll(new RegExp(set.pattern, 'gm'))) {
				const fiche = /\bname="([^"]*)"/.exec(match);
				assert.ok(fiche, `${name}: ${file} matches ${set.pattern} with no fiche named in it`);
				matched.add(fiche[1]);
			}
		}
		const shown = reports[name];
		const fiches = (Array.isArray(shown) ? shown : Object.values(shown).flat()).map((report) => report.name);
		assert.ok(fiches.length > 0, `${name} lists no fiche`);
		assert.deepEqual([...matched].sort(), [...new Set(fiches)].sort(), `${name}: the fiches ${set.pattern} finds in ${set.files.join(' ')}`);
	}
});

test('the index of fiches moves with a commit that changes only what a guide says of a fiche, and the errata index with one that changes only how it lists the entries', async (t) => {
	// The site's own entries, on a history where nothing but the declaration
	// in one guide changes, and then nothing but the component that writes
	// each line of the errata index.
	const raw = JSON.parse(readFileSync(join(SITE, DATE_SOURCES), 'utf8'));
	const entryOf = (path) => raw.entries.find((entry) => entry.pages.includes(path));
	const cases = [
		{
			entry: entryOf('site/src/content/docs/reference/reports.mdx'),
			before: (repo) => {
				repo.writeFile('.github/reports/one.pdf', 'one\n');
				repo.write('signals/guide.mdx', guide('A title'));
				repo.write('es/signals/guide.mdx', guide('Un título'));
			},
			change: (repo) => repo.write('signals/guide.mdx', guide('A better title')),
			pages: ['reference/reports.mdx', 'es/reference/reports.mdx'],
		},
		{
			entry: entryOf('site/src/content/docs/reference/errata/index.mdx'),
			before: (repo) => repo.write('reference/errata/iso-1.md', page({ title: 'ISO 1' })),
			change: (repo) => repo.writeFile('site/src/components/ErrataFamily.astro', 'each entry linked by its typeset heading\n'),
			pages: ['reference/errata/index.mdx'],
		},
		{
			entry: entryOf('site/src/content/docs/es/reference/errata/index.mdx'),
			before: (repo) => repo.write('es/reference/errata/iso-1.md', page({ title: 'ISO 1' })),
			change: (repo) => repo.writeFile('site/src/components/ErrataFamily.astro', 'each entry linked by its typeset heading\n'),
			pages: ['es/reference/errata/index.mdx'],
		},
	];
	for (const { entry, before, change, pages } of cases) {
		assert.ok(entry, `an entry for ${pages[0]}`);
		const repo = repository(t);
		for (const spec of entry.pages) repo.writeFile(spec, page());
		for (const spec of entry.sources.filter((spec) => !spec.endsWith('/'))) repo.writeFile(spec, 'one\n');
		before(repo);
		writeFileSync(join(repo.site, DATE_SOURCES), JSON.stringify({ entries: [entry] }));
		repo.commit(1);
		change(repo);
		repo.commit(2, 'the index changes for its readers, and no page file does');
		const dates = await repo.dates();
		for (const path of pages) assert.equal(day(dates, path), '2026-01-02', path);
	}
});

test('the catalogue pages move with a commit that changes only the words of the overview list or of the finder', async (t) => {
	// The site's own entries for the catalogue pages, on a history where no
	// page and no catalogue changes, and only the component that writes the
	// overview's list, or the one that writes the finder, does.
	const raw = JSON.parse(readFileSync(join(SITE, DATE_SOURCES), 'utf8'));
	for (const lang of ['', 'es/']) {
		const dir = `${lang}reference/catalogues/`;
		const entry = raw.entries.find((candidate) => candidate.pages.includes(`site/src/content/docs/${dir}`));
		assert.ok(entry, `an entry for site/src/content/docs/${dir}`);
		const cases = [
			['site/src/components/CatalogueIndex.astro', [`${dir}index.mdx`]],
			['site/src/components/CatalogueFinder.astro', [`${dir}index.mdx`, `${dir}carpets.mdx`]],
		];
		for (const [component, pages] of cases) {
			const repo = repository(t);
			for (const path of [`${dir}index.mdx`, `${dir}carpets.mdx`]) repo.write(path, page());
			for (const spec of entry.sources) repo.writeFile(spec, 'one\n');
			repo.writeFile(component, 'one\n');
			writeFileSync(join(repo.site, DATE_SOURCES), JSON.stringify({ entries: [entry] }));
			repo.commit(1);
			repo.writeFile(component, 'two\n');
			repo.commit(2, 'the component changes what the pages say, and no page file does');
			const dates = await repo.dates();
			for (const path of pages) assert.equal(day(dates, path), '2026-01-02', `${path} after a commit to ${component} alone`);
		}
	}
});

test('the landing page moves with a commit that changes only how its numbers are computed', async (t) => {
	// The site's own entry for the landing page, on a history where nothing it
	// counts changes and only the module that computes the numbers does: the
	// guides went from 163 to 168 that way, by a change to the topics
	// repo-stats.mjs counts, with no guide added or removed.
	const raw = JSON.parse(readFileSync(join(SITE, DATE_SOURCES), 'utf8'));
	const landing = raw.entries.find((entry) => entry.pages.includes('site/src/content/docs/index.mdx'));
	/** A file each pathspec matches: a topic's guide, an API page, a fiche. */
	const instance = (spec) =>
		spec
			.replace(/^:\([^)]*\)/, '')
			.replaceAll('{topic}', domainIds[0])
			.replaceAll('**/', '')
			.replaceAll('*', 'one')
			.replace(/\/$/, '/one.mdx');
	for (const module of ['site/src/data/repo-stats.mjs', 'site/src/data/conformance-stats.mjs']) {
		const repo = repository(t);
		for (const spec of landing.pages) repo.writeFile(spec, page());
		for (const spec of landing.sources) repo.writeFile(spec.endsWith('/') ? `${spec}One.astro` : spec, 'one\n');
		for (const set of Object.values(landing.counts)) {
			for (const spec of set.filter((spec) => !spec.startsWith(':(exclude'))) repo.writeFile(instance(spec), 'one\n');
		}
		repo.writeFile(module, 'export const counted = 1;\n');
		writeFileSync(join(repo.site, DATE_SOURCES), JSON.stringify({ entries: [landing] }));
		repo.commit(1);
		repo.writeFile(module, 'export const counted = 2;\n');
		repo.commit(2, `${module} counts another way`);
		assert.equal(day(await repo.dates(), 'index.mdx'), '2026-01-02', `a commit to ${module} alone`);
	}
});

// --- The sitemap, stamped the way the build does it ----------------------

/**
 * Write a sitemap listing `routes` into the site's build and run the stamp,
 * handing it the site as `siteRoot` spells it.
 */
function stamp(repo, routes, siteRoot = repo.site) {
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
	const ran = spawnSync(process.execPath, [STAMP, siteRoot], { env: repo.env, encoding: 'utf8' });
	const xml = readFileSync(join(dist, 'sitemap-0.xml'), 'utf8');
	const lastmod = (route) =>
		new RegExp(`<loc>${RegExp.escape(`${siteUrl}${basePath}/${route}`)}</loc><lastmod>([^<]+)</lastmod>`).exec(xml)?.[1];
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

test('a site reached through a symbolic link is dated as the directory the link names', async (t) => {
	const repo = repository(t);
	repo.write('index.mdx', page());
	repo.write('guide.mdx', page());
	repo.commit(1);
	repo.write('guide.mdx', page({ body: 'Edited.\n' }));
	repo.commit(2);
	// macOS hands out its temporary directory through such a link, and git
	// names the work tree by the directory it points to.
	const link = join(repo.root, 'link');
	symlinkSync(repo.work, link, 'dir');
	const site = join(link, 'site');
	const dates = await loadContentDates({ siteRoot: site });
	assert.equal(isoDay(dates.dateOf(join(site, 'src', 'content', 'docs', 'guide.mdx'))), '2026-01-02');
	assert.equal(isoDay(dates.dateOf('src/content/docs/index.mdx')), '2026-01-01');
	assert.equal(day(dates, 'guide.mdx'), '2026-01-02', 'the real path and the linked one are one page');
	const ran = stamp(repo, ['', 'guide/'], site);
	assert.equal(ran.status, 0, ran.err);
	assert.equal(ran.lastmod(''), '2026-01-01');
	assert.equal(ran.lastmod('guide/'), '2026-01-02');
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
