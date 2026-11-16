// The site's readers of committed text read a checkout with carriage returns
// as they read one without.
//
// A clone made with `core.autocrlf=true` writes a carriage return before every
// line feed of each text file the root .gitattributes does not pin. On such a
// checkout the build stopped at `CITATION.cff: cannot read line`, the Markdown
// copies stopped at a code example's `{"n_stories": 18}` read as an
// expression, the index of fiches lost a fiche that follows a code example,
// and the search check read no bibliography at all. Each test reads a file of
// the repository as it stands and the same file with carriage returns, and
// holds the two readings equal, each read from the file as the commit holds
// it, so that the test reads the same whatever checkout runs it.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { pageMarkdown } from '../src/lib/agent-md/page.mjs';
import { loadRegistry } from '../src/lib/agent-md/registry.mjs';
import { readCommittedText } from '../src/lib/line-ends.mjs';
import { pageLines, splitLines } from '../src/lib/markdown-fences.mjs';
import { readDeclaredDesignations } from './shared/search-index.mjs';
import { pageMarkup } from './shared/markdown-spans.mjs';

const SITE = join(dirname(fileURLToPath(import.meta.url)), '..');
const REPOSITORY = join(SITE, '..');
const CONTENT = join(SITE, 'src', 'content', 'docs');

/** `text` as a checkout with `core.autocrlf=true` writes it. */
const withCarriageReturns = (text) => text.replace(/\r?\n/g, '\r\n');

/** A directory of its own for one test, removed after it. */
function scratch(t) {
  const root = mkdtempSync(join(tmpdir(), 'line-ends-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  return root;
}

/** A guide with a code example followed by a fiche, as the sound power guide writes one. */
const GUIDE = join(CONTENT, 'devices', 'emission', 'sound-power-pressure.mdx');

test('the walk of a page reads its lines alike, their line ends carriage returns or not', () => {
  const text = readCommittedText(GUIDE);
  const roles = (lines) => pageLines(lines, { kind: 'mdx' }).map((line) => line.role);
  // A reader that splits the page on its line feeds hands the walk each line
  // with the carriage return that ended it.
  assert.deepEqual(roles(withCarriageReturns(text).split('\n')), roles(text.split('\n')));
  assert.deepEqual(roles(splitLines(withCarriageReturns(text))), roles(splitLines(text)));
});

test('the markup of a page and its Markdown copy are the same with carriage returns', async (t) => {
  const text = readCommittedText(GUIDE);
  const crlf = withCarriageReturns(text);
  const tags = (page) => (pageMarkup(page).match(/<ReportPreview\b/g) ?? []).length;
  assert.equal(tags(crlf), tags(text));
  // A code example that prints a mapping is code, not an expression the copy
  // has to write as a value. The copy is the one the build publishes, written
  // by scripts/agent-md.mjs from the page source.
  const page = join('es', 'vibration', 'structural', 'building-response.mdx');
  const building = readCommittedText(join(CONTENT, page));
  const registry = await loadRegistry();
  const root = scratch(t);
  const copy = async (source, name) => {
    const file = join(root, name, page);
    mkdirSync(dirname(file), { recursive: true });
    writeFileSync(file, source);
    return (await pageMarkdown(file, { registry, contentDir: join(root, name) })).markdown;
  };
  const lf = await copy(building, 'lf');
  assert.match(lf, /"n_stories": 18/, 'the code example is in the copy');
  const fromCrlf = await copy(withCarriageReturns(building), 'crlf');
  assert.ok(!fromCrlf.includes('\r'), 'no carriage return reaches the copy');
  assert.equal(fromCrlf, lf);
});

test('the bibliography of a page reads the same with carriage returns', async (t) => {
  const root = scratch(t);
  const page = readCommittedText(join(CONTENT, 'aircraft', 'aircraft-noise.mdx'));
  const read = async (text, name) => {
    const dir = join(root, name, 'aircraft');
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, 'aircraft-noise.mdx'), text);
    const { declared, cited, designations, problems } = await readDeclaredDesignations(join(root, name));
    return { declared: [...declared.values()], cited: [...cited.values()], designations: [...designations], problems };
  };
  const lf = await read(page, 'lf');
  assert.ok(lf.designations.length > 3, 'the page cites works');
  assert.deepEqual(await read(withCarriageReturns(page), 'crlf'), lf);
});

test('the citation of the project reads the same from a checkout with carriage returns', (t) => {
  // src/data/citation.mjs finds the repository from the working directory, so
  // it is run in a copy of the files it reads, once as committed and once
  // with carriage returns.
  const files = [
    'CITATION.cff',
    '.zenodo.json',
    'CHANGELOG.md',
    'site/src/content/docs/start/about.md',
    'site/src/content/docs/es/start/about.md',
    'docs/start/about.md',
  ];
  const module = pathToFileURL(join(SITE, 'src', 'data', 'citation.mjs')).href;
  const cite = (transform, name) => {
    const root = join(scratch(t), name);
    for (const file of files) {
      mkdirSync(dirname(join(root, file)), { recursive: true });
      writeFileSync(join(root, file), transform(readCommittedText(join(REPOSITORY, file))));
    }
    const script = `const m = await import(${JSON.stringify(module)}); process.stdout.write(JSON.stringify({ bibtex: m.bibtex, doi: m.doi }));`;
    return execFileSync(process.execPath, ['--input-type=module', '-e', script], { cwd: root, encoding: 'utf8' });
  };
  const lf = cite((text) => text, 'lf');
  assert.match(lf, /@software\{/);
  assert.equal(cite(withCarriageReturns, 'crlf'), lf);
});
