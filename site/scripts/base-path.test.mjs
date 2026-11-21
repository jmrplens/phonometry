// The site links no page through the base path it had or the host it was
// published on before (scripts/base-path.mjs, docs/contributing F76).
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';

import { fences } from '../src/lib/markdown-fences.mjs';
import { ALLOWED, OUTSIDE, SCANNED, SITE, basePathFindings, basePathReport, outsideReport } from './base-path.mjs';

/** A site folder with every path the check reads, the pages and astro.config.mjs empty. */
function emptySite() {
	const site = mkdtempSync(join(tmpdir(), 'base-path-'));
	mkdirSync(join(site, 'src/content/docs'), { recursive: true });
	writeFileSync(join(site, 'astro.config.mjs'), 'export default {};\n');
	return site;
}

/** Write `text` at `path` under `site`. */
function plant(site, path, text) {
	mkdirSync(dirname(join(site, path)), { recursive: true });
	writeFileSync(join(site, path), text);
}

test('no file of the site\'s source writes the old base path or host', () => {
	const { files, findings, stale } = basePathReport();
	assert.ok(files > 900, `only ${files} files read: the check would pass by finding nothing`);
	assert.deepEqual(findings.map(({ file, line, text }) => `${file}:${line}: ${text}`), []);
	assert.deepEqual(stale, []);
});

test('every shape a site link takes is caught', () => {
	const shapes = [
		'See [levels](/phonometry/signals/levels/).',
		'    link: /phonometry/start/getting-started/',
		"  { href: '/phonometry/signals/' },",
		'  { href: "/phonometry/signals/" },',
		'<a href="/phonometry/es/">inicio</a>',
		'<img src="/phonometry/media/figure.svg" alt="" />',
		'const home = `/phonometry/${lang}/`;',
		'[home](/phonometry)',
		'"basePath": "/phonometry"',
		'[report](https://docs.jmrp.io/phonometry/reference/conformance/)',
		'"url": "https://docs.jmrp.io/phonometry/signals/"',
	];
	for (const shape of shapes) assert.equal(basePathFindings(shape, 'src/content/docs/x.md').length, 1, shape);
});

test('a name that only contains the word is no site link', () => {
	const names = [
		'[source](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters.py)',
		'pip install phonometry',
		'`src/phonometry/signals/levels.py`',
		'the phonometry-assets repository at /phonometry-assets/',
		'[home](/signals/)',
		'https://docs.jmrp.io/kleidos/',
	];
	for (const name of names) assert.deepEqual(basePathFindings(name, 'src/content/docs/x.md'), [], name);
});

test('the legacy origin is allowed, and only in its file', () => {
	const [entry] = ALLOWED;
	assert.deepEqual(basePathFindings(`    ${entry.line}\n`, entry.file), []);
	assert.equal(basePathFindings(`    ${entry.line}\n`, 'src/data/home-en.ts').length, 1);
	assert.ok(entry.why.length > 0);
});

test('an allowance that excuses no line is reported, so the list cannot outlive what it excuses', () => {
	const site = emptySite();
	plant(site, 'src/content/docs/a.md', 'See [b](/phonometry/b/).\n');
	const report = basePathReport(site, [{ file: 'src/data/site-targets.json', line: 'gone', why: 'test' }]);
	assert.equal(report.files, 2);
	assert.deepEqual(report.findings, [{ file: 'src/content/docs/a.md', line: 1, text: 'See [b](/phonometry/b/).' }]);
	assert.deepEqual(report.stale, ['src/data/site-targets.json: gone']);
});

test('every file of the site\'s source is read, the routes, utilities, styles and astro.config.mjs too', () => {
	assert.deepEqual([...SCANNED], ['src', 'astro.config.mjs']);
	const site = emptySite();
	const planted = {
		'src/pages/zz-plant.astro': "---\nconst a = 'https://docs.jmrp.io/phonometry/signals/';\n---\n",
		'src/utils/zz-plant.ts': "export const b = '/phonometry/signals/';\n",
		'src/styles/zz-plant.css': "a { background: url('/phonometry/media/x.svg'); }\n",
		'src/routeData.ts': "export const c = `/phonometry/${'es'}/`;\n",
		'astro.config.mjs': "export default { base: '/phonometry' };\n",
	};
	for (const [path, text] of Object.entries(planted)) plant(site, path, text);
	const report = basePathReport(site, []);
	assert.deepEqual(report.findings.map(({ file }) => file).sort(), Object.keys(planted).sort());
});

test('a path the check is meant to read and cannot find fails it, rather than passing by reading nothing', () => {
	const site = mkdtempSync(join(tmpdir(), 'base-path-'));
	mkdirSync(join(site, 'src'));
	assert.throws(() => basePathReport(site, []), /astro\.config\.mjs/);
});

/** The allowances of site-targets.json, for a tree that holds no other file of the site. */
const TARGETS = ALLOWED.filter((entry) => entry.file === 'src/data/site-targets.json');

test('About names the old address in plain text on the two lines allowed, and a link to it or any other mention still fails', () => {
	const about = ALLOWED.filter((entry) => entry.file.endsWith('start/about.md'));
	assert.deepEqual(about.map((entry) => entry.file), ['src/content/docs/start/about.md', 'src/content/docs/es/start/about.md']);
	for (const { file, line } of about) {
		assert.ok(!/\]\(|https?:/.test(line), `${file}: the old address in plain text, never a link`);
		assert.deepEqual(basePathFindings(`${line}\n`, file), [], file);
		assert.equal(basePathFindings(`${line}\n`, 'src/content/docs/start/support.mdx').length, 1, 'only in its own file');
		assert.equal(basePathFindings('See [the old site](https://docs.jmrp.io/phonometry/).\n', file).length, 1, 'a link to the old host, even on About');
	}
});

test('an optional allowance is let through where its line is, and not asked for where it is not', () => {
	const optional = ALLOWED.filter((entry) => entry.optional);
	assert.deepEqual(optional.map(({ file, line }) => `${file}: ${line}`), ['src/data/site-targets.json: "clipBase": "https://docs.jmrp.io/phonometry/media/"']);
	const [entry] = optional;
	const targets = readFileSync(join(SITE, entry.file), 'utf8');
	const switched = targets.replace(/"clipBase": .*$/m, entry.line);
	assert.notEqual(switched, targets);
	for (const text of [targets, switched]) {
		const site = emptySite();
		plant(site, entry.file, text);
		assert.deepEqual(basePathReport(site, TARGETS), { files: 2, findings: [], stale: [] });
	}
	assert.equal(basePathFindings(`  ${entry.line}\n`, 'src/data/home-en.ts').length, 1, 'only in its file');
});
test('either clip host the Worker README names is one edit of site-targets.json, which the check lets through', () => {
	const readme = readFileSync(join(SITE, 'worker/README.md'), 'utf8');
	const section = readme.slice(readme.indexOf('### Where the clips are served from'));
	const hosts = fences(section, { kind: 'md' })
		.filter((block) => block.language === 'json')
		.slice(0, 2)
		.map((block) => JSON.parse(`{${block.body.trim()}}`));
	assert.equal(hosts.length, 2, 'the README names the clip host and the one to fall back on');
	const [, fallback] = hosts;
	assert.deepEqual(Object.keys(fallback), Object.keys(hosts[0]));
	assert.match(fallback.clipBase, /^https:\/\/docs\.jmrp\.io\/phonometry\/media\/$/);
	const targets = readFileSync(join(SITE, 'src/data/site-targets.json'), 'utf8');
	const parsed = JSON.parse(targets);
	assert.ok(
		hosts.some((host) => Object.entries(host).every(([key, value]) => JSON.stringify(parsed[key]) === JSON.stringify(value))),
		'site-targets.json carries one of the two the README names',
	);
	for (const host of hosts) {
		// The edit as a maintainer makes it: each value on its own line, the rest of the file as it is.
		const switched = Object.entries(host).reduce(
			(text, [key, value]) => text.replace(new RegExp(`"${key}": .*?(,?)$`, 'm'), (_, comma) => `"${key}": ${JSON.stringify(value).replaceAll(',', ', ')}${comma}`),
			targets,
		);
		assert.deepEqual(JSON.parse(switched), { ...parsed, ...host });
		assert.deepEqual(basePathFindings(switched, 'src/data/site-targets.json'), [], host.clipBase);
		const site = emptySite();
		plant(site, 'src/data/site-targets.json', switched);
		assert.deepEqual(basePathReport(site, TARGETS), { files: 2, findings: [], stale: [] }, `${host.clipBase}: no finding, and no allowance stale`);
	}
	const optional = ALLOWED.filter((entry) => entry.optional);
	assert.equal(optional.length, 1);
	assert.equal(basePathFindings(`  ${optional[0].line}\n`, 'src/data/home-en.ts').length, 1, 'the fallback is allowed only in its file');
});

test('no repository file outside the site that names it writes the old host', () => {
	const { files, findings } = outsideReport();
	assert.ok(files >= OUTSIDE.length, `${files} files read`);
	assert.deepEqual(findings, []);
});

test('outside the site the old host is found, and a bare /phonometry is not taken for a site link', () => {
	const root = mkdtempSync(join(tmpdir(), 'base-path-outside-'));
	const site = join(root, 'site');
	mkdirSync(site);
	plant(root, 'README.md', 'pip install phonometry\nSee https://docs.jmrp.io/phonometry/signals/ for more.\nsrc/phonometry/signals and /phonometry are paths.\n');
	plant(root, 'pyproject.toml', '"Homepage" = "https://docs.jmrp.io/phonometry/"\n');
	plant(root, '.github/ISSUE_TEMPLATE/config.yml', 'url: https://phonometry.dev/\n');
	const report = outsideReport(site, ['../README.md', '../pyproject.toml', '../.github/ISSUE_TEMPLATE']);
	assert.equal(report.files, 3);
	assert.deepEqual(report.findings, [
		{ file: 'README.md', line: 2, text: 'See https://docs.jmrp.io/phonometry/signals/ for more.' },
		{ file: 'pyproject.toml', line: 1, text: '"Homepage" = "https://docs.jmrp.io/phonometry/"' },
	]);
});

test('a file outside the site the check is meant to read and cannot find fails it', () => {
	const root = mkdtempSync(join(tmpdir(), 'base-path-outside-'));
	mkdirSync(join(root, 'site'));
	assert.throws(() => outsideReport(join(root, 'site'), ['../SECURITY.md']), /SECURITY\.md/);
});
