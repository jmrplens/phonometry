// What a run of `scripts/agent-md.mjs --public` removes before it writes: the
// copies the last run left, and no other file named index.md.
//
// The run can be pointed at any directory with `--out`, and one that already
// holds index.md files of its own (docs/ holds 43 that open otherwise) must keep
// them: the old removal took every index.md under the directory.
//
// Usage (from site/, after `pnpm install`): pnpm run test:agent-md
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { describe, test } from 'node:test';

import { handwrittenTargets, isWrittenCopy, removeWrittenCopies, writtenCopies } from '../copies.mjs';
import { header } from '../header.mjs';

const RELEASE = Object.freeze({ version: '4.0.0', install: 'pip install "phonometry[full]"' });

/** A copy as the header writer opens one, in either language. */
const copy = (lang) =>
  ['# A page', '', header({ lang, canonical: 'https://docs.jmrp.io/phonometry/a/', release: RELEASE }), '', 'Text.', ''].join('\n');

describe('the copies a run removes', () => {
  test('a copy opens with its title and the lead sentence of its language', () => {
    assert.ok(isWrittenCopy(copy('en')));
    assert.ok(isWrittenCopy(copy('es')));
    assert.ok(!isWrittenCopy('← [Documentation index](../../README.md)\n\n# API Reference\n'));
    assert.ok(!isWrittenCopy('# A page\n\nSome text written by hand.\n'));
    assert.ok(!isWrittenCopy(''));
  });

  test('a foreign index.md under the output directory survives, and the copies go', (t) => {
    const out = mkdtempSync(join(tmpdir(), 'agent-md-out-'));
    t.after(() => rmSync(out, { recursive: true, force: true }));
    const files = {
      'a/index.md': copy('en'),
      'es/a/index.md': copy('es'),
      'keep/index.md': '# Notes\n\nAn index written by hand, which no run wrote.\n',
      'keep/README.md': copy('en'),
    };
    for (const [path, text] of Object.entries(files)) {
      mkdirSync(dirname(join(out, path)), { recursive: true });
      writeFileSync(join(out, path), text);
    }
    assert.deepEqual(writtenCopies(out).map((path) => path.slice(out.length + 1)).sort(), ['a/index.md', 'es/a/index.md']);
    assert.equal(removeWrittenCopies(out), 2);
    assert.ok(existsSync(join(out, 'keep', 'index.md')));
    assert.ok(existsSync(join(out, 'keep', 'README.md')));
    assert.ok(!existsSync(join(out, 'a', 'index.md')));
    assert.ok(!existsSync(join(out, 'es', 'a', 'index.md')));
  });
});

describe('the files a run would write over', () => {
  test('an index.md written by hand at a copy\'s place is named, and a copy or a free place is not', (t) => {
    const out = mkdtempSync(join(tmpdir(), 'agent-md-targets-'));
    t.after(() => rmSync(out, { recursive: true, force: true }));
    const handwritten = '# Signals\n\nThe index of this folder, written by hand.\n';
    mkdirSync(join(out, 'signals'), { recursive: true });
    mkdirSync(join(out, 'a'), { recursive: true });
    writeFileSync(join(out, 'signals', 'index.md'), handwritten);
    writeFileSync(join(out, 'a', 'index.md'), copy('en'));
    const targets = ['signals', 'a', 'fresh'].map((route) => join(out, route, 'index.md'));
    assert.deepEqual(handwrittenTargets(targets), [join(out, 'signals', 'index.md')]);
    assert.equal(readFileSync(join(out, 'signals', 'index.md'), 'utf8'), handwritten, 'the check reads, never writes');
  });
});
