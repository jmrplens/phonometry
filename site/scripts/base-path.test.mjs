// The site links no page through the base path it had or the host it was
// published on before (scripts/base-path.mjs, docs/contributing F76).
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';

import { ALLOWED, SCANNED, SITE, basePathFindings, basePathReport } from './base-path.mjs';

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
		assert.deepEqual(basePathReport(site), { files: 2, findings: [], stale: [] });
	}
	assert.equal(basePathFindings(`  ${entry.line}\n`, 'src/data/home-en.ts').length, 1, 'only in its file');
});
