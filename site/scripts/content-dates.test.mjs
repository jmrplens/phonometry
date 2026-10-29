// The date a page's content last changed, on git histories small enough to read.
//
// The real history only ever hands the dates a build that reads them right,
// so a rule that stopped passing over a description-only commit, or a git
// failure that went back to leaving the dates empty, would stay unnoticed
// there for good. Each test here writes a repository of its own with the
// commits a case needs, dated a day apart, and reads the dates
// src/lib/content-dates.mjs gives it; the last ones run
// scripts/add-sitemap-lastmod.mjs on such a repository the way the build
// does, and read its exit status and the sitemap it wrote.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import {
	mkdirSync,
	mkdtempSync,
	readFileSync,
	renameSync,
	rmSync,
	utimesSync,
	writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';
import {
	DATELESS_KEYS,
	frontmatterOnly,
	isoDay,
	loadContentDates,
	readIgnoreRevs,
} from '../src/lib/content-dates.mjs';

const STAMP = join(dirname(fileURLToPath(import.meta.url)), 'add-sitemap-lastmod.mjs');

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
 * at noon UTC on 2026-01-<day>.
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
		move(from, to) {
			mkdirSync(dirname(join(docs, to)), { recursive: true });
			renameSync(join(docs, from), join(docs, to));
		},
		/** Commit everything, dated `day`; returns the commit's SHA. */
		commit(day, message = `day ${day}`) {
			git('add', '--all');
			const ran = spawnSync('git', ['commit', '-q', '-m', message], {
				cwd: work,
				env: { ...env, GIT_AUTHOR_DATE: at(day), GIT_COMMITTER_DATE: at(day) },
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
	await assert.rejects(loadContentDates({ siteRoot: site }), /git rev-parse --show-toplevel failed/);
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

	// The dates read the old versions with lazy fetching switched off, so they
	// come from the batched fetch or not at all.
	const dates = await loadContentDates({ siteRoot: join(clone, 'site') });
	assert.equal(day(dates, 'a.mdx'), '2026-01-02');
	assert.equal(day(dates, 'b.mdx'), '2026-01-01');
	assert.ok(!missing(oldA), 'the version that decided the date was fetched');
});

// --- The sitemap, stamped the way the build does it ----------------------

/** Write a sitemap listing `routes` into the site's build and run the stamp. */
function stamp(repo, routes) {
	const dist = join(repo.site, 'dist');
	mkdirSync(dist, { recursive: true });
	const urls = routes.map((route) => `<url><loc>${siteUrl}${basePath}/${route}</loc></url>`).join('');
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
