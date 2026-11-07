// Which package names src/lib/bundled-packages.mjs hands the prerender bundle
// to carry inside it.
//
// The build only meets a package from outside site/ on a machine that has a
// node_modules above the checkout, which CI does not, so the pattern is held
// here to the names it has to tell apart: those the site lists stay imports,
// every other one is bundled, including the four a home directory supplied.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

import { packagesNotListedIn } from '../src/lib/bundled-packages.mjs';

const SITE_MANIFEST = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));

test('a package the site does not list is bundled, a listed one stays an import', () => {
	const bundled = packagesNotListedIn({
		dependencies: { astro: '^7.4.4', '@astrojs/starlight': '^0.42.8', sharp: '^0.35.5' },
		devDependencies: { puppeteer: '25.16.0' },
	});
	for (const name of ['cookie', 'zod', 'yaml', 'picomatch', '@astrojs/internal-helpers']) {
		assert.ok(bundled.test(name), `${name} should be bundled`);
	}
	for (const name of ['astro', '@astrojs/starlight', 'sharp', 'puppeteer']) {
		assert.ok(!bundled.test(name), `${name} should stay an import`);
	}
});

test('a name that only starts or ends like a listed one is not taken for it', () => {
	const bundled = packagesNotListedIn({ dependencies: { astro: '^7.4.4', 'rehype-katex': '^7.0.1' } });
	for (const name of ['astro-icon', 'astr', '@astro', 'katex', 'rehype-katex-svelte', 'xastro']) {
		assert.ok(bundled.test(name), `${name} should be bundled`);
	}
});

test('a dot in a listed name matches a dot and nothing else', () => {
	const bundled = packagesNotListedIn({ dependencies: { 'lodash.merge': '^4.6.2' } });
	assert.ok(!bundled.test('lodash.merge'));
	assert.ok(bundled.test('lodashxmerge'));
});

test("a manifest that lists nothing bundles every package", () => {
	assert.ok(packagesNotListedIn({}).test('astro'));
});

test("the site's own manifest keeps its renderers as imports and bundles astro's dependencies", () => {
	const bundled = packagesNotListedIn(SITE_MANIFEST);
	for (const name of ['astro', 'katex', 'satori', 'sharp', '@astrojs/starlight']) {
		assert.ok(!bundled.test(name), `${name} is the site's own and should stay an import`);
	}
	for (const name of ['cookie', 'zod', 'yaml', 'picomatch']) {
		assert.ok(bundled.test(name), `${name} is astro's, not the site's, and should be bundled`);
	}
});
