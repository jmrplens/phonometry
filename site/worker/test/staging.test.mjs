// The staging step on small trees made to fail each of its checks.
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { afterEach, describe, test } from 'node:test';

import { twinExclusions } from '../lib/twins.mjs';
import { MAX_FILE_BYTES, MAX_FILES, buildOrigin, exclusionProblems, listTree, noTwinPages, servedPages, stage, treeProblems, twinPairs } from '../lib/staging.mjs';

const prefix = '/phonometry';
const exclusions = twinExclusions(prefix);
const made = [];
afterEach(() => {
	while (made.length) rmSync(made.pop(), { recursive: true, force: true });
});

/** A build tree: a map of relative path -> contents. */
function tree(files) {
	const root = mkdtempSync(join(tmpdir(), 'phdev-stage-'));
	made.push(root);
	for (const [path, body] of Object.entries(files)) {
		mkdirSync(dirname(join(root, path)), { recursive: true });
		writeFileSync(join(root, path), body);
	}
	return root;
}

const home = (origin = 'https://docs.jmrp.io') => `<html><head><link rel="canonical" href="${origin}/phonometry/"/></head></html>`;
/** The smallest build the real checks accept. */
const good = () => ({
	'index.html': home(),
	'index.md': '# home',
	'404.html': 'not found',
	'es/index.html': 'es',
	'es/index.md': '# es',
	'signals/index.html': 'p',
	'signals/index.md': '# p',
	'es/reference/api/index.html': 'api',
	'es/reference/api/levels/index.html': 'api',
	'about/index.html': '<meta http-equiv="refresh">',
	'_astro/a.css': 'x',
	'robots.txt': 'Sitemap: https://docs.jmrp.io/phonometry/sitemap-index.xml\n',
});
const pairs = [
	{ from: '/phonometry/about/', to: '/phonometry/signals/' },
	{ from: '/phonometry/about', to: '/phonometry/signals/' },
];

describe('the checks', () => {
	test('the slash pages without a copy, retired addresses aside', () => {
		const files = listTree(tree(good()));
		assert.deepEqual(noTwinPages(files, prefix, pairs), ['/phonometry/es/reference/api/', '/phonometry/es/reference/api/levels/']);
	});

	test('the exclusions match the build', () => {
		const files = listTree(tree(good()));
		assert.deepEqual(exclusionProblems(noTwinPages(files, prefix, pairs), servedPages(files, prefix, pairs), exclusions), []);
	});

	test('a page that loses its copy is not covered by the exclusions', () => {
		const files = good();
		delete files['signals/index.md'];
		const listed = listTree(tree(files));
		assert.match(exclusionProblems(noTwinPages(listed, prefix, pairs), servedPages(listed, prefix, pairs), exclusions).join('\n'), /\/phonometry\/signals\/ has no Markdown copy/);
	});

	test('a retired address inside an excluded subtree is neither a page nor a copy', () => {
		const retired = [...pairs, { from: '/phonometry/es/reference/api/old/', to: '/phonometry/es/reference/api/levels/' }];
		const listed = listTree(tree({ ...good(), 'es/reference/api/old/index.html': '<meta http-equiv="refresh">' }));
		assert.deepEqual(exclusionProblems(noTwinPages(listed, prefix, retired), servedPages(listed, prefix, retired), exclusions), []);
	});

	test('an excluded subtree page that gains a copy is refused', () => {
		const listed = listTree(tree({ ...good(), 'es/reference/api/levels/index.md': '# x' }));
		assert.match(exclusionProblems(noTwinPages(listed, prefix, pairs), servedPages(listed, prefix, pairs), exclusions).join('\n'), /has a Markdown copy but is excluded/);
	});

	test('an excluded subtree the build no longer writes is refused', () => {
		const files = good();
		delete files['es/reference/api/index.html'];
		delete files['es/reference/api/levels/index.html'];
		const listed = listTree(tree(files));
		assert.match(exclusionProblems(noTwinPages(listed, prefix, pairs), servedPages(listed, prefix, pairs), exclusions).join('\n'), /no page under \/phonometry\/es\/reference\/api\//);
	});

	test('too many files, a file too large, a _headers or _redirects of its own', () => {
		const files = [{ path: 'a', size: MAX_FILE_BYTES + 1 }, { path: '_headers', size: 1 }, { path: 'x/_redirects', size: 1 }];
		const problems = treeProblems(files).join('\n');
		assert.match(problems, /a: \d+ bytes, over/);
		assert.match(problems, /_headers: the build carries its own/);
		assert.match(problems, /x\/_redirects: the build carries its own/);
		const many = Array.from({ length: MAX_FILES + 1 }, (_, i) => ({ path: `f${i}`, size: 1 }));
		assert.match(treeProblems(many).join('\n'), /20001 files, over the 20000/);
		assert.equal(MAX_FILES, 20000);
		assert.equal(MAX_FILE_BYTES, 25 * 1024 * 1024);
	});

	test('the origin the build names as canonical', () => {
		assert.equal(buildOrigin(tree(good()), prefix), 'https://docs.jmrp.io');
		assert.equal(buildOrigin(tree({ ...good(), 'index.html': home('https://phonometry.dev') }), prefix), 'https://phonometry.dev');
		assert.throws(() => buildOrigin(tree({ ...good(), 'index.html': '<html></html>' }), prefix), /canonical/);
	});

	test('a retired address also retires its Markdown copy when the target has one', () => {
		const listed = listTree(tree(good()));
		assert.deepEqual(twinPairs(pairs, listed, prefix), [{ from: '/phonometry/about/index.md', to: '/phonometry/signals/index.md' }]);
		assert.deepEqual(twinPairs([...pairs, { from: '/phonometry/about/index.md', to: '/x/' }], listed, prefix), []);
	});
});

describe('stage', () => {
	test('writes the tree under the prefix with _headers, _redirects, .assetsignore and a root 404', () => {
		const from = tree(good());
		const out = join(tree({}), 'stage');
		const report = stage({ from, out, prefix, origin: 'https://docs.jmrp.io', pairs, exclusions, indexable: false });
		assert.equal(report.problems.length, 0, report.problems.join('\n'));
		assert.ok(existsSync(join(out, 'phonometry', 'signals', 'index.html')));
		assert.equal(readFileSync(join(out, '404.html'), 'utf8'), 'not found');
		assert.equal(readFileSync(join(out, 'robots.txt'), 'utf8'), 'Sitemap: https://docs.jmrp.io/phonometry/sitemap-index.xml\n');
		assert.equal(existsSync(join(out, 'llms.txt')), false);
		assert.equal(report.files, 14);
		assert.match(readFileSync(join(out, '_headers'), 'utf8'), /^\/\*\n {2}X-Robots-Tag: noindex/);
		assert.equal(
			readFileSync(join(out, '_redirects'), 'utf8'),
			'/phonometry/about/ /phonometry/signals/ 301\n/phonometry/about /phonometry/signals/ 301\n/phonometry/about/index.md /phonometry/signals/index.md 301\n',
		);
		assert.equal(readFileSync(join(out, '.assetsignore'), 'utf8'), '.*\n');
		assert.equal(report.redirects, 3);
	});

	test('check-only writes nothing and reports the same problems', () => {
		const files = good();
		delete files['signals/index.md'];
		const out = join(tree({}), 'stage');
		const report = stage({ from: tree(files), out, prefix, origin: 'https://docs.jmrp.io', pairs, exclusions, indexable: false, checkOnly: true });
		assert.equal(existsSync(out), false);
		assert.match(report.problems.join('\n'), /has no Markdown copy/);
	});

	test('a build made for another origin is refused', () => {
		const from = tree({ ...good(), 'index.html': home('https://phonometry.dev') });
		const report = stage({ from, out: join(tree({}), 's'), prefix, origin: 'https://docs.jmrp.io', pairs, exclusions, indexable: false, checkOnly: true });
		assert.match(report.problems.join('\n'), /built for https:\/\/phonometry\.dev, not https:\/\/docs\.jmrp\.io/);
	});

	test('a redirect to a page the build does not hold is refused', () => {
		const report = stage({
			from: tree(good()),
			out: join(tree({}), 's'),
			prefix,
			origin: 'https://docs.jmrp.io',
			pairs: [{ from: '/phonometry/old/', to: '/phonometry/gone/' }],
			exclusions,
			indexable: false,
			checkOnly: true,
		});
		assert.match(report.problems.join('\n'), /no page at \/phonometry\/gone\//);
	});

	test('an existing output directory is refused rather than mixed into', () => {
		const out = tree({ 'stale.html': 'x' });
		assert.throws(() => stage({ from: tree(good()), out, prefix, origin: 'https://docs.jmrp.io', pairs, exclusions, indexable: false }), /already exists/);
	});
});
