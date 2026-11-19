/**
 * A page whose content changed after the latest release says so in its copy's
 * header, as it says so under its title: an `Unreleased:` line, in the page's
 * language, which a page that has not changed since does not carry. The line
 * is a release line (`releaseHeaderKeys`), so the next release takes it off
 * every page without the IndexNow manifest reporting one of them, and the
 * dump the llms files are written from names it in routes.json whether its
 * copies are dated or not, so the shards are cut alike either way
 * (scripts/generate_llms.py).
 *
 * Usage (from site/, after `pnpm install`): pnpm run test:agent-md
 */
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, sep } from 'node:path';
import { describe, test } from 'node:test';

import { ROUTES_FILE, writePages } from '../../../../scripts/agent-md.mjs';
import { version } from '../../../data/repo-stats.mjs';
import { releaseHeaderKeys, withoutReleaseLines } from '../../page-markdown.mjs';
import { UNRELEASED_URL } from '../../release-rules.mjs';
import { UNRELEASED, header } from '../header.mjs';
import { pageMarkdown } from '../page.mjs';
import { Box, registryOf } from './helpers.mjs';

const SITE = 'https://phonometry.dev';

/** The release the fixtures are newer or older than, committed on 2026-11-17 at 10:30 UTC. */
const RELEASE = Object.freeze({ version, sha: 'f'.repeat(40), date: new Date('2026-11-17T10:30:31Z'), from: 'tag' });

/** When each fixture page's content last changed: one before the release, one after. */
const CHANGED = Object.freeze({
  'before.md': new Date('2026-11-16T09:00:00Z'),
  'after.md': new Date('2026-11-18T09:00:00Z'),
  'es/before.md': new Date('2026-11-16T09:00:00Z'),
  'es/after.md': new Date('2026-11-18T09:00:00Z'),
});

const fields = (lang, changedSince) => ({
  lang,
  canonical: `${SITE}/signals/levels/`,
  release: { version: '4.0.0', install: 'pip install "phonometry[full]"', changedSince },
});

describe('the Unreleased line', () => {
  test('says, in each language, that the page changed after the release and where the changelog lists what is new', () => {
    const en = header(fields('en', true));
    assert.match(
      en,
      new RegExp(
        '^Unreleased: this page changed after phonometry 4\\.0\\.0, the latest release on PyPI, so it may describe code ' +
          `that release does not have yet; what is new since then is listed under Unreleased in ${UNRELEASED_URL.replaceAll('.', '\\.')}$`,
        'mu',
      ),
    );
    const es = header(fields('es', true));
    assert.match(es, /^Unreleased: esta página cambió después de phonometry 4\.0\.0, la última versión publicada en PyPI, /mu);
    assert.ok(es.includes(`lo nuevo desde entonces figura en Unreleased en ${UNRELEASED_URL}`));
  });

  test('stands only on a page that changed after the release, after the other release lines', () => {
    assert.doesNotMatch(header(fields('en', false)), /^Unreleased:/mu);
    assert.doesNotMatch(header(fields('en', undefined)), /^Unreleased:/mu);
    const keys = header(fields('en', true))
      .split('\n')
      .map((line) => /^([A-Z][A-Za-z-]*): /u.exec(line)?.[1])
      .filter(Boolean);
    assert.deepEqual(keys, ['Canonical', 'Language', 'Version', 'Install', 'Unreleased', 'License']);
  });

  test('is a release line: the next release takes it off without the copy counting as changed', () => {
    assert.ok(releaseHeaderKeys.includes('Unreleased'));
    const copy = (changedSince) => ['# Levels', '', header(fields('en', changedSince)), '', 'The body.'].join('\n');
    assert.notEqual(copy(true), copy(false));
    assert.equal(withoutReleaseLines(copy(true)), withoutReleaseLines(copy(false)));
  });

  test('names the version it is newer than, which the words in both languages carry', () => {
    for (const lang of /** @type {const} */ (['en', 'es'])) {
      assert.ok(UNRELEASED[lang]('4.1.0').includes('phonometry 4.1.0,'), lang);
      assert.ok(!UNRELEASED[lang]('4.1.0').includes('\u2014'), `${lang}: no em dash`);
    }
  });
});

/** A directory made for one test and removed after it. */
function scratch(t, name) {
  const dir = mkdtempSync(join(tmpdir(), `agent-md-unreleased-${name}-`));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  return dir;
}

/** A content tree with the fixture pages, in both languages. */
function content(t) {
  const root = scratch(t, 'content');
  for (const name of Object.keys(CHANGED)) {
    mkdirSync(dirname(join(root, name)), { recursive: true });
    writeFileSync(join(root, name), `---\ntitle: ${name}\ndescription: What ${name} is about.\n---\n\nThe body of ${name}.\n`);
  }
  return root;
}

/** The dates of the fixture pages, with the release they are compared with. */
const dates = (root) => ({
  dateOf: (file) => {
    const date = CHANGED[relative(root, file).split(sep).join('/')];
    if (!date) throw new Error(`no fixture date for ${file}`);
    return date;
  },
  publishedOf: () => '2026-01-06',
  release: RELEASE,
});

describe('a page dated after the release and one dated before it', () => {
  for (const lang of /** @type {const} */ (['en', 'es'])) {
    test(`in ${lang === 'en' ? 'English' : 'Spanish'}, only the copy of the page changed after it carries the line`, async (t) => {
      const root = content(t);
      const prefix = lang === 'es' ? 'es/' : '';
      const copy = async (name) =>
        (await pageMarkdown(join(root, `${prefix}${name}`), { registry: registryOf(Box), contentDir: root, dates: dates(root) })).markdown;
      const after = await copy('after.md');
      const before = await copy('before.md');
      assert.ok(after.split('\n').includes(`Unreleased: ${UNRELEASED[lang](version)}`), after);
      assert.doesNotMatch(before, /^Unreleased:/mu);
      assert.match(after, /^Updated: 2026-11-18T09:00:00Z$/mu);
      assert.match(before, /^Updated: 2026-11-16T09:00:00Z$/mu);
    });
  }

  test('a page changed in the release commit itself carries no line', async (t) => {
    const root = content(t);
    const atRelease = { ...dates(root), dateOf: () => RELEASE.date };
    const { markdown } = await pageMarkdown(join(root, 'after.md'), { registry: registryOf(Box), contentDir: root, dates: atRelease });
    assert.doesNotMatch(markdown, /^Unreleased:/mu);
  });

  test('without dates (an undated dump, a page written in a test) no copy carries the line', async (t) => {
    const root = content(t);
    const { markdown } = await pageMarkdown(join(root, 'after.md'), { registry: registryOf(Box), contentDir: root });
    assert.doesNotMatch(markdown, /^Unreleased:/mu);
  });
});

describe('the dump the llms files are written from', () => {
  /** Every file under a directory, by its path from there, with its text. */
  const filesUnder = (root) => {
    const found = {};
    const walk = (dir) => {
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        if (entry.isDirectory()) walk(join(dir, entry.name));
        else found[relative(root, join(dir, entry.name)).split(sep).join('/')] = readFileSync(join(dir, entry.name), 'utf8');
      }
    };
    walk(root);
    return found;
  };

  /** Runs the writer with its messages caught. */
  async function run(t, options) {
    t.mock.method(console, 'log', () => {});
    t.mock.method(console, 'error', () => {});
    const status = await writePages(options);
    t.mock.restoreAll();
    return status;
  }

  test('routes.json names the line, dated or not, and only the dated copy of a page changed after the release holds it', async (t) => {
    const root = content(t);
    const dated = join(scratch(t, 'dated'), 'agent-md');
    const undated = join(scratch(t, 'undated'), 'agent-md');
    assert.equal(await run(t, { dumpDir: dated, contentDir: root, dates: dates(root) }), 0);
    assert.equal(await run(t, { dumpDir: undated, contentDir: root, dates: dates(root), undated: true }), 0);
    const withDates = filesUnder(dated);
    const without = filesUnder(undated);
    const line = `Unreleased: ${UNRELEASED.en(version)}`;
    assert.equal(JSON.parse(withDates[ROUTES_FILE]).unreleasedLine, line);
    assert.equal(withDates[ROUTES_FILE], without[ROUTES_FILE], 'routes.json is the same whatever git says of the pages');
    assert.ok(withDates['after/index.md'].split('\n').includes(line));
    assert.doesNotMatch(withDates['before/index.md'], /^Unreleased:/mu);
    assert.doesNotMatch(without['after/index.md'], /^Unreleased:/mu);
  });
});
