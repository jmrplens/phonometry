/**
 * While VERSION is a PEP 440 pre-release, the header of every copy says the
 * version is a pre-release pip installs only when asked for it, in a line the IndexNow manifest leaves out with
 * the other release lines; at a final version the line is gone.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { test } from 'node:test';

import { isPreRelease } from '../../pep440.mjs';
import { releaseHeaderKeys, withoutReleaseLines } from '../../page-markdown.mjs';
import { header } from '../header.mjs';
import { SITE_DIR } from '../render.mjs';

const { cases } = JSON.parse(readFileSync(join(SITE_DIR, 'src', 'data', 'pep440-pre-releases.json'), 'utf8'));

test('a version is a pre-release by PEP 440, as the shared table says', () => {
  for (const [version, pre] of Object.entries(cases)) assert.equal(isPreRelease(version), pre, version);
});

const fields = (lang, version) => ({
  lang,
  canonical: 'https://phonometry.dev/signals/levels/',
  release: { version, install: 'pip install "phonometry[full]"', preRelease: isPreRelease(version) },
});

for (const lang of /** @type {const} */ (['en', 'es'])) {
  test(`the ${lang} header says 4.0.0rc1 is a pre-release pip installs only when asked for it, and nothing of it at 4.0.0`, () => {
    const pre = header(fields(lang, '4.0.0rc1'));
    const final = header(fields(lang, '4.0.0'));
    const said = lang === 'es' ? 'phonometry 4.0.0rc1 es una versión preliminar, que pip solo instala si se pide por su versión o con --pre' : 'phonometry 4.0.0rc1 is a pre-release, which pip installs only when it is asked for by version or with --pre';
    assert.match(pre, new RegExp(`^Pre-release: ${said}`, 'mu'));
    assert.doesNotMatch(final, /^Pre-release:/mu);
    assert.doesNotMatch(pre, /PyPI .*\d+\.\d+\.\d+(?!rc1)/u, 'it names no version PyPI serves');
  });
}

test('the stamp moves no copy: the copy of a pre-release and of the final differ only in release lines', () => {
  assert.ok(releaseHeaderKeys.includes('Pre-release'));
  const copy = (version) => ['# Levels', '', header(fields('en', version)), '', 'The body.'].join('\n');
  assert.equal(withoutReleaseLines(copy('4.0.0rc1')), withoutReleaseLines(copy('4.0.0')));
});
