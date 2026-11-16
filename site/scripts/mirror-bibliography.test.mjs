/**
 * The GitHub copy of the bibliography (scripts/mirror-bibliography.mjs): it
 * keeps its own opening, writes each section's list from the sections the
 * pages' references make, and points each link at the copy of the page in
 * docs/ when there is one.
 */
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, win32 } from 'node:path';
import { test } from 'node:test';

import { bibliographyMirror, mirrorFiles, mirrorLink, relativeLink } from './mirror-bibliography.mjs';

/** A docs/ tree holding a copy of `signals/a` only. */
function docsTree(t) {
  const docsDir = mkdtempSync(join(tmpdir(), 'bibliography-mirror-'));
  t.after(() => rmSync(docsDir, { recursive: true, force: true }));
  mkdirSync(join(docsDir, 'signals'), { recursive: true });
  mkdirSync(join(docsDir, 'reference'), { recursive: true });
  writeFileSync(join(docsDir, 'signals', 'a.md'), '# A\n');
  return docsDir;
}

const book = {
  type: 'book',
  authors: ['Doe, J.'],
  year: 2000,
  title: 'A book',
  publisher: 'Wiley',
};

const sections = [
  {
    key: 'general',
    entries: [
      {
        ref: book,
        note: 'The note, which [links a page](/phonometry/signals/b/).',
        citedBy: [
          { id: 'signals/a', title: 'Page A', href: '/phonometry/signals/a/' },
          { id: 'signals/b', title: 'Page B', href: '/phonometry/signals/b/' },
        ],
      },
    ],
  },
];

test('the copy keeps its opening and writes each marked section from the references, links pointing at the copies', (t) => {
  const docsDir = docsTree(t);
  const text = bibliographyMirror({
    copy: '# Bibliography\n\nThe copy\'s own opening.\n\n## Old heading\n\n- An entry written by hand.\n',
    page: '---\ntitle: "Bibliography"\n---\n\nThe site\'s opening.\n\n## General\n\nAn introduction.\n\n<!-- bibliography: general -->\n',
    sections,
    link: (href) => mirrorLink(href, { docsDir, site: 'https://example.org/docs' }),
  });
  assert.equal(
    text,
    '# Bibliography\n\nThe copy\'s own opening.\n\n## General\n\nAn introduction.\n\n' +
      '- Doe, J. (2000). *A book*. Wiley.\n' +
      '  The note, which [links a page](https://example.org/docs/signals/b/).\n' +
      '  Cited by [Page A](../signals/a.md) and [Page B](https://example.org/docs/signals/b/).\n',
  );
  assert.doesNotMatch(text, /written by hand|site's opening|\*\*Doe/);
});

test('a page link keeps its anchor, the site root and any other address stay as they are', (t) => {
  const docsDir = docsTree(t);
  const where = { docsDir, site: 'https://example.org/docs' };
  assert.equal(mirrorLink('/phonometry/signals/a/#eq-2', where), '../signals/a.md#eq-2');
  assert.equal(mirrorLink('/phonometry/reference/catalogues/solids/', where), 'https://example.org/docs/reference/catalogues/solids/');
  assert.equal(mirrorLink('/phonometry/', where), 'https://example.org/docs/');
  assert.equal(mirrorLink('https://doi.org/10.1000/x', where), 'https://doi.org/10.1000/x');
});

test('a link to a copy is separated by slashes on Windows too, as the committed copy writes it', () => {
  assert.equal(relativeLink('C:\\repo\\docs\\reference', 'C:\\repo\\docs\\signals\\a.md', win32), '../signals/a.md');
  assert.equal(relativeLink('C:\\repo\\docs\\reference', 'C:\\repo\\docs\\reference\\b.md', win32), 'b.md');
  assert.equal(relativeLink('/repo/docs/reference', '/repo/docs/signals/a.md'), '../signals/a.md');
});

test('a marker the page shows in a fence stays as written, the one on a line of its own takes its list', (t) => {
  const docsDir = docsTree(t);
  const text = bibliographyMirror({
    copy: '# Bibliography\n\n## Old\n',
    page: '## General\n\n```markdown\n<!-- bibliography: elsewhere -->\n```\n\n<!-- bibliography: general -->\n',
    sections,
    link: (href) => mirrorLink(href, { docsDir, site: 'https://example.org/docs' }),
  });
  assert.match(text, /```markdown\n<!-- bibliography: elsewhere -->\n```/);
  assert.match(text, /^- Doe, J\. \(2000\)/m);
});

test('a section the page marks and the sections lack, or a copy with no heading, stops the writer', () => {
  const link = (href) => href;
  assert.throws(
    () => bibliographyMirror({ copy: '# B\n\n## A\n', page: '## A\n\n<!-- bibliography: elsewhere -->\n', sections, link }),
    /marks a section its data does not have, elsewhere/,
  );
  assert.throws(
    () => bibliographyMirror({ copy: '# B\n', page: '## A\n\n<!-- bibliography: general -->\n', sections, link }),
    /has no "## " heading to keep its opening above/,
  );
});

test('a checkout with carriage returns reads its committed copy as current, and the copy written from it has line feeds', (t) => {
  const docsDir = docsTree(t);
  const link = (href) => mirrorLink(href, { docsDir, site: 'https://example.org/docs' });
  const copy = '# Bibliography\n\nThe copy\'s own opening.\n\n## Old heading\n';
  const page = '---\ntitle: "Bibliography"\n---\n\nThe site\'s opening.\n\n## General\n\nAn introduction.\n\n<!-- bibliography: general -->\n';
  const current = bibliographyMirror({ copy, page, sections, link });
  // A clone made with `core.autocrlf=true` writes both files with a carriage
  // return before each line feed.
  const withCarriageReturns = (text) => text.replace(/\n/g, '\r\n');
  const target = join(docsDir, 'reference', 'bibliography.md');
  const source = join(docsDir, 'bibliography-page.md');
  writeFileSync(target, withCarriageReturns(current));
  writeFileSync(source, withCarriageReturns(page));
  const read = mirrorFiles({ target, page: source, sections, link });
  assert.equal(read.copy, current);
  assert.equal(read.text, current);
});
