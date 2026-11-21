// The staging step on small trees made to fail each of its checks.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { afterEach, describe, test } from 'node:test';

import { twinExclusions } from '../lib/twins.mjs';
import { beaconScript } from '../lib/beacon.mjs';
import { DEFAULT_SITE, SITE_TARGETS, mediaOrigins } from '../../src/data/site.mjs';
import { CANONICAL_ORIGIN, MAX_FILE_BYTES, MAX_FILES, SERVED_ORIGIN, workerPathProblems, beaconProblems, slashRuleProblems, buildOrigin, indexableBuild, withBeacon, exclusionProblems, listTree, mediaPolicyProblems, noTwinPages, servedPages, stage, treeProblems } from '../lib/staging.mjs';

// The site as it is served: at the root of phonometry.dev, its clips on the
// clip host of site-targets.json.
const prefix = '';
const ORIGIN = 'https://phonometry.dev';
const [CLIP_HOST] = mediaOrigins;
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

/** The meta policy every page of a build carries; `media` is its media-src. */
const policy = (media = `'self' ${mediaOrigins.join(' ')}`) =>
	`<meta http-equiv="Content-Security-Policy" content="default-src 'self'; media-src ${media}; object-src 'none'">`;
const home = (origin = ORIGIN, base = prefix) => `<html><head>${policy()}<link rel="canonical" href="${origin}${base}/"/></head></html>`;
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
	'robots.txt': 'Sitemap: https://phonometry.dev/sitemap-index.xml\n',
});
// As redirectPairs() lists them: the address with and without its slash, and its Markdown copy.
const pairs = [
	{ from: '/about/', to: '/signals/' },
	{ from: '/about', to: '/signals/' },
	{ from: '/about/index.md', to: '/signals/index.md' },
];

describe('the checks', () => {
	test('every page with a meta policy allows the clip hosts; stubs without one are skipped', () => {
		const root = tree({ ...good(), 'signals/index.html': `<html><head>${policy()}</head></html>` });
		assert.deepEqual(mediaPolicyProblems(root, listTree(root), mediaOrigins), []);
	});

	test('a page whose policy keeps clips to its own origin blocks the redirected clips', () => {
		const root = tree({ ...good(), 'signals/index.html': `<html><head>${policy("'self'")}</head></html>` });
		assert.deepEqual(mediaPolicyProblems(root, listTree(root), [CLIP_HOST]), [`signals/index.html: media-src does not allow ${CLIP_HOST}`]);
		assert.match(mediaPolicyProblems(root, listTree(root), [CLIP_HOST, 'https://clips.example.org']).join('\n'), /index\.html: media-src does not allow https:\/\/clips\.example\.org/);
	});

	test('without media-src the default-src decides', () => {
		const root = tree({ ...good(), 'index.html': `<meta http-equiv="Content-Security-Policy" content="default-src 'self'">` });
		assert.deepEqual(mediaPolicyProblems(root, listTree(root), [CLIP_HOST]), [`index.html: media-src does not allow ${CLIP_HOST}`]);
	});

	test('a home with no meta policy is refused, so the check cannot pass by finding nothing', () => {
		const root = tree({ ...good(), 'index.html': '<link rel="canonical" href="https://phonometry.dev/"/>' });
		assert.deepEqual(mediaPolicyProblems(root, listTree(root), mediaOrigins), ['the home page carries no Content-Security-Policy meta tag']);
	});

	test('stage refuses a build made before the clip host was allowed', () => {
		const root = tree({ ...good(), 'signals/index.html': `<html><head>${policy("'self'")}</head></html>` });
		const report = stage({ from: root, out: join(root, 'never'), prefix, origin: ORIGIN, pairs, exclusions, indexable: false, checkOnly: true });
		assert.match(report.problems.join('\n'), new RegExp(`signals/index\\.html: media-src does not allow ${CLIP_HOST.replaceAll('.', '\\.')}`));
	});

	test('the slash pages without a copy, retired addresses aside', () => {
		const files = listTree(tree(good()));
		assert.deepEqual(noTwinPages(files, prefix, pairs), ['/es/reference/api/', '/es/reference/api/levels/']);
	});

	test('the exclusions match the build', () => {
		const files = listTree(tree(good()));
		assert.deepEqual(exclusionProblems(noTwinPages(files, prefix, pairs), servedPages(files, prefix, pairs), exclusions), []);
	});

	test('a page that loses its copy is not covered by the exclusions', () => {
		const files = good();
		delete files['signals/index.md'];
		const listed = listTree(tree(files));
		assert.match(exclusionProblems(noTwinPages(listed, prefix, pairs), servedPages(listed, prefix, pairs), exclusions).join('\n'), /^\/signals\/ has no Markdown copy/m);
	});

	test('a retired address inside an excluded subtree is neither a page nor a copy', () => {
		const retired = [...pairs, { from: '/es/reference/api/old/', to: '/es/reference/api/levels/' }];
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
		assert.match(exclusionProblems(noTwinPages(listed, prefix, pairs), servedPages(listed, prefix, pairs), exclusions).join('\n'), /no page under \/es\/reference\/api\//);
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
		assert.equal(buildOrigin(tree(good()), prefix), 'https://phonometry.dev');
		assert.equal(buildOrigin(tree({ ...good(), 'index.html': home('https://docs.jmrp.io') }), prefix), 'https://docs.jmrp.io');
		assert.equal(buildOrigin(tree({ ...good(), 'index.html': home(ORIGIN, '/docs') }), '/docs'), 'https://phonometry.dev');
		assert.throws(() => buildOrigin(tree({ ...good(), 'index.html': '<html></html>' }), prefix), /canonical/);
	});

});

describe('whether a staged build is indexable', () => {
	const served = 'https://phonometry.dev';
	const other = 'https://docs.jmrp.io';

	test('exactly when the build names the host it is served on, and that host is the canonical site', () => {
		assert.equal(SERVED_ORIGIN, served);
		assert.equal(indexableBuild(served, false, served), true);
		assert.equal(indexableBuild(served, true, served), true);
		assert.equal(indexableBuild(other, false, served), false);
		assert.equal(indexableBuild(null, false, served), false);
	});

	test('a build for this host stays noindex while another host is the canonical site', () => {
		assert.equal(indexableBuild(served, false, other), false);
		assert.equal(indexableBuild(other, false, other), false);
	});

	test('--indexable on a build that would not be indexable is refused, not obeyed', () => {
		assert.throws(() => indexableBuild(other, true, served), /--indexable.*names https:\/\/docs\.jmrp\.io as canonical, not https:\/\/phonometry\.dev/);
		assert.throws(() => indexableBuild(null, true, served), /--indexable.*names no canonical origin/);
		assert.throws(() => indexableBuild(served, true, other), /--indexable.*the canonical site is https:\/\/docs\.jmrp\.io, not https:\/\/phonometry\.dev/);
	});

	test('the canonical site the Worker is given is the default target of site-targets.json', () => {
		assert.equal(CANONICAL_ORIGIN, SITE_TARGETS[DEFAULT_SITE].siteUrl);
	});
});

describe('stage', () => {
	test('writes the tree at the root with _headers, _redirects and .assetsignore', () => {
		const from = tree(good());
		const out = join(tree({}), 'stage');
		const report = stage({ from, out, prefix, origin: ORIGIN, pairs, exclusions, indexable: false });
		assert.equal(report.problems.length, 0, report.problems.join('\n'));
		assert.ok(existsSync(join(out, 'signals', 'index.html')));
		assert.equal(readFileSync(join(out, '404.html'), 'utf8'), 'not found');
		assert.equal(readFileSync(join(out, 'robots.txt'), 'utf8'), 'Sitemap: https://phonometry.dev/sitemap-index.xml\n');
		assert.equal(report.files, Object.keys(good()).length);
		assert.match(readFileSync(join(out, '_headers'), 'utf8'), /^\/\*\n {2}X-Robots-Tag: noindex/);
		assert.equal(readFileSync(join(out, '_redirects'), 'utf8'), '/about/ /signals/ 301\n/about /signals/ 301\n/about/index.md /signals/index.md 301\n');
		assert.equal(readFileSync(join(out, '.assetsignore'), 'utf8'), '.*\n!/.well-known/\n');
		assert.equal(report.redirects, 3);
	});

	test('under a base path, writes the tree under it and copies the 404 page and robots.txt to the root', () => {
		const base = '/docs';
		const from = tree({ ...good(), 'index.html': home(ORIGIN, base), 'robots.txt': 'Sitemap: https://phonometry.dev/docs/sitemap-index.xml\n' });
		const out = join(tree({}), 'stage');
		const moved = pairs.map(({ from: old, to }) => ({ from: `${base}${old}`, to: `${base}${to}` }));
		const report = stage({ from, out, prefix: base, origin: ORIGIN, pairs: moved, exclusions: twinExclusions(base), indexable: false });
		assert.equal(report.problems.length, 0, report.problems.join('\n'));
		assert.ok(existsSync(join(out, 'docs', 'signals', 'index.html')));
		assert.equal(readFileSync(join(out, '404.html'), 'utf8'), 'not found');
		assert.equal(readFileSync(join(out, 'robots.txt'), 'utf8'), 'Sitemap: https://phonometry.dev/docs/sitemap-index.xml\n');
		assert.equal(existsSync(join(out, 'llms.txt')), false);
		assert.equal(
			readFileSync(join(out, '_redirects'), 'utf8'),
			'/docs/about/ /docs/signals/ 301\n/docs/about /docs/signals/ 301\n/docs/about/index.md /docs/signals/index.md 301\n',
		);
	});

	test('check-only writes nothing and reports the same problems', () => {
		const files = good();
		delete files['signals/index.md'];
		const out = join(tree({}), 'stage');
		const report = stage({ from: tree(files), out, prefix, origin: ORIGIN, pairs, exclusions, indexable: false, checkOnly: true });
		assert.equal(existsSync(out), false);
		assert.match(report.problems.join('\n'), /has no Markdown copy/);
	});

	test('a build made for another origin is refused', () => {
		const from = tree({ ...good(), 'index.html': home('https://docs.jmrp.io') });
		const report = stage({ from, out: join(tree({}), 's'), prefix, origin: ORIGIN, pairs, exclusions, indexable: false, checkOnly: true });
		assert.match(report.problems.join('\n'), /built for https:\/\/docs\.jmrp\.io, not https:\/\/phonometry\.dev/);
	});

	test('a redirect to a page the build does not hold is refused', () => {
		const report = stage({
			from: tree(good()),
			out: join(tree({}), 's'),
			prefix,
			origin: ORIGIN,
			pairs: [{ from: '/old/', to: '/gone/' }],
			exclusions,
			indexable: false,
			checkOnly: true,
		});
		assert.match(report.problems.join('\n'), /no page at \/gone\//);
	});

	test('an existing output directory is refused rather than mixed into', () => {
		const out = tree({ 'stale.html': 'x' });
		assert.throws(() => stage({ from: tree(good()), out, prefix, origin: ORIGIN, pairs, exclusions, indexable: false }), /already exists/);
	});
});

describe('the beacon in the staged copy', () => {
	/** good() with every HTML file a page with one body, as the build writes them. */
	const bodied = () => Object.fromEntries(Object.entries(good()).map(([path, body]) => [path, path.endsWith('.html') ? `${body}<body><main>x</main></body></html>` : body]));
	/** sha256 of every file under a directory, by relative path. */
	const hashes = (root) => Object.fromEntries(listTree(root).map(({ path }) => [path, createHash('sha256').update(readFileSync(join(root, path))).digest('hex')]));

	test('withBeacon puts the script right before the one closing body tag', () => {
		assert.equal(withBeacon('<html><body>x</body></html>', false), `<html><body>x${beaconScript(false)}</body></html>`);
		assert.equal(withBeacon('<body>x</body>', true), `<body>x${beaconScript(true)}</body>`);
		assert.throws(() => withBeacon('<body>x</body></body>', false), /closing body tags/);
		assert.throws(() => withBeacon('<meta http-equiv="refresh">', false), /closing body tags/);
	});

	test('a page with no closing body tag, or two, stops a staging with the beacon', () => {
		const root = tree({ ...bodied(), 'signals/index.html': '<html><head></head></html>' });
		assert.deepEqual(beaconProblems(root, listTree(root)), ['signals/index.html: 0 closing body tags, the beacon needs exactly one']);
		const report = stage({ from: root, out: join(tree({}), 's'), prefix, origin: ORIGIN, pairs, exclusions, indexable: false, beacon: true, checkOnly: true });
		assert.match(report.problems.join('\n'), /signals\/index\.html: 0 closing body tags/);
	});

	test('without it, every staged file of the build is the build\u2019s file, byte for byte', () => {
		const from = tree(bodied());
		const out = join(tree({}), 'stage');
		stage({ from, out, prefix, origin: ORIGIN, pairs, exclusions, indexable: false });
		const source = hashes(from);
		const staged = hashes(out);
		for (const name of ['_headers', '_redirects', '.assetsignore']) delete staged[name];
		assert.deepEqual(staged, source);
	});

	test('with it, the build is left as it was and each staged page differs by the one script', () => {
		const from = tree(bodied());
		const before = hashes(from);
		const out = join(tree({}), 'stage');
		const report = stage({ from, out, prefix, origin: ORIGIN, pairs, exclusions, indexable: false, beacon: true });
		assert.equal(report.problems.length, 0, report.problems.join('\n'));
		assert.equal(report.beaconPages, 7);
		assert.deepEqual(hashes(from), before, 'the build was not touched');
		for (const { path } of listTree(from)) {
			const built = readFileSync(join(from, path), 'utf8');
			const staged = readFileSync(join(out, path), 'utf8');
			if (!path.endsWith('.html')) {
				assert.equal(staged, built, path);
				continue;
			}
			const script = beaconScript(path === '404.html');
			assert.equal(staged.replace(script, ''), built, path);
			assert.equal(staged.split(script).length, 2, path);
		}
		assert.match(readFileSync(join(out, '404.html'), 'utf8'), /nf:1/);
	});
});

describe('the paths that run the Worker', () => {
	test('no file of a build stands at the beacon, the Markdown copies, llms files and sitemaps included', () => {
		const files = listTree(tree({ ...good(), 'llms.txt': 'x', 'llms/llms-signals.txt': 'x', 'sitemap-index.xml': 'x', 'rss.xml': 'x', 'signals/index.md': 'x' }));
		assert.deepEqual(workerPathProblems(files, prefix, ['404.html', 'robots.txt', 'llms.txt']), []);
	});

	test('a file at the beacon path is refused: the Worker would answer there instead of it', () => {
		assert.deepEqual(workerPathProblems([{ path: '_v' }, { path: '_v/x.txt' }, { path: 'llms-notes/readme.txt' }], ''), ['/_v would run the Worker instead of being served as a file (lib/worker-paths.mjs)']);
	});
});

describe('what the trailing-slash rule needs of the build', () => {
	test('every file has an extension and no page sits in a folder with a dot: nothing to report', () => {
		assert.deepEqual(slashRuleProblems(listTree(tree(good())), prefix), []);
		assert.deepEqual(slashRuleProblems([{ path: 'signals/index.html' }, { path: 'llms/llms-signals-2.txt' }, { path: '_astro/a.B1.css' }, { path: '.well-known/security.txt' }], ''), []);
	});

	test('a file without an extension under a folder whose name holds a dot is no address the rule reads: nothing to report', () => {
		assert.deepEqual(slashRuleProblems([{ path: '.well-known/atproto-did' }, { path: '.well-known/apple-app-site-association' }, { path: 'v1.2/LICENSE' }], ''), []);
		assert.deepEqual(slashRuleProblems([{ path: 'LICENSE' }], '/v1.2'), []);
	});

	test('a file whose address holds no dot would be sent to an address with a slash that answers 404', () => {
		assert.deepEqual(slashRuleProblems([{ path: 'signals/index.html' }, { path: 'LICENSE' }, { path: 'media/clip' }], ''), [
			'/LICENSE has no dot in its address: the trailing-slash rule (lib/rules.mjs) would send it to /LICENSE/, which answers 404',
			'/media/clip has no dot in its address: the trailing-slash rule (lib/rules.mjs) would send it to /media/clip/, which answers 404',
		]);
		assert.deepEqual(slashRuleProblems([{ path: 'media/clip' }], '/phonometry'), [
			'/phonometry/media/clip has no dot in its address: the trailing-slash rule (lib/rules.mjs) would send it to /phonometry/media/clip/, which answers 404',
		]);
	});

	test('a page served flat would loop between the rule and the assets; the not-found page at the root is the one it leaves alone', () => {
		assert.deepEqual(slashRuleProblems([{ path: '404.html' }, { path: 'signals/index.html' }], ''), []);
		assert.deepEqual(slashRuleProblems([{ path: '404.html' }], '/phonometry'), []);
		assert.deepEqual(slashRuleProblems([{ path: 'about.html' }, { path: 'es/404.html' }, { path: 'signals/legacy.html' }], ''), [
			'/about.html is a page served flat, at /about: the trailing-slash rule (lib/rules.mjs) would send /about to /about/, which the asset server sends back, a loop',
			'/es/404.html is a page served flat, at /es/404: the trailing-slash rule (lib/rules.mjs) would send /es/404 to /es/404/, which the asset server sends back, a loop',
			'/signals/legacy.html is a page served flat, at /signals/legacy: the trailing-slash rule (lib/rules.mjs) would send /signals/legacy to /signals/legacy/, which the asset server sends back, a loop',
		]);
	});

	test('a page under a folder whose name holds a dot keeps the 307 the rule exists to replace', () => {
		assert.deepEqual(slashRuleProblems([{ path: 'reference/api/phonometry.filters/index.html' }, { path: 'v1.2/guide/index.html' }], '/phonometry'), [
			'/phonometry/reference/api/phonometry.filters/ is a page under a folder whose name holds a dot: the trailing-slash rule (lib/rules.mjs) leaves /phonometry/reference/api/phonometry.filters to the asset server\'s 307',
			'/phonometry/v1.2/guide/ is a page under a folder whose name holds a dot: the trailing-slash rule (lib/rules.mjs) leaves /phonometry/v1.2/guide to the asset server\'s 307',
		]);
	});
});
