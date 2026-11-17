// Every frontmatter key in a class, and the date rule built from the classes.
//
// src/lib/frontmatter-keys.mjs says, of each key a page's frontmatter can
// hold, whether a change to it moves the date the page last changed. The
// content collection refuses a key its schema declares and the list does not
// class, and the date rule refuses one it meets in a page; these tests hold
// the list to the keys Starlight and the topics plugin declare, which the
// site does not write itself and an upgrade can add to, and to every key the
// pages carry today.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { docsSchema } from '@astrojs/starlight/schema';
import { z } from 'astro/zod';
import { topicSchema } from 'starlight-sidebar-topics/schema';

import { CONTENT_DIR, DATELESS_KEYS } from '../src/lib/date-rules.mjs';
import {
	FRONTMATTER_KEYS,
	KEY_CLASSES,
	keysOfClass,
	refuseUnclassifiedKeys,
	topLevelKey,
	unclassifiedKeys,
} from '../src/lib/frontmatter-keys.mjs';

const SITE = resolve(dirname(fileURLToPath(import.meta.url)), '..');

test('every key is in one of the three classes', () => {
	assert.deepEqual(Object.keys(KEY_CLASSES), ['content', 'label', 'metadata']);
	for (const [key, name] of Object.entries(FRONTMATTER_KEYS)) {
		assert.ok(Object.hasOwn(KEY_CLASSES, name), `${key}: "${name}" is no class`);
	}
	assert.ok(Object.isFrozen(FRONTMATTER_KEYS) && Object.isFrozen(KEY_CLASSES));
	assert.throws(() => keysOfClass('dateless'), /no class "dateless"/);
});

test('the dateless keys are the label and metadata classes, and nothing else', () => {
	assert.deepEqual([...DATELESS_KEYS].sort(), [...keysOfClass('label'), ...keysOfClass('metadata')].sort());
	assert.deepEqual(keysOfClass('label'), ['title', 'description', 'sidebar', 'topic']);
	assert.ok(keysOfClass('metadata').includes('corrects'), 'corrects is read by the structured data only');
	assert.ok(keysOfClass('content').includes('references'), 'the References section is text of the page');
});

test('a key in no class is named, every one of them', () => {
	assert.deepEqual(unclassifiedKeys(['title', 'sameAs', 'corrects', 'isPartOf']), ['sameAs', 'isPartOf']);
	assert.doesNotThrow(() => refuseUnclassifiedKeys(['title', 'corrects'], 'here'));
	assert.throws(() => refuseUnclassifiedKeys(['sameAs'], 'here'), /^Error: here: frontmatter key "sameAs" is in no class\. Add each to FRONTMATTER_KEYS/);
	assert.throws(() => refuseUnclassifiedKeys(['a', 'b'], 'here'), /frontmatter keys "a", "b" are in no class/);
	assert.deepEqual(unclassifiedKeys(['constructor', 'toString', '__proto__']), ['constructor', 'toString', '__proto__']);
});

test('every key Starlight and the topics plugin declare is in a class', () => {
	// The schema the content collection builds, without the keys this site
	// adds (which src/content.config.ts refuses at the build when unclassed).
	const schema = docsSchema({ extend: z.object({}).extend(topicSchema.shape) })({ image: () => z.string() });
	const declared = Object.keys(schema.shape);
	assert.ok(declared.includes('title') && declared.includes('topic'), declared.join(', '));
	assert.deepEqual(unclassifiedKeys(declared), []);
});

/** Every page of the site, as file paths. */
function sitePages(dir = join(SITE, CONTENT_DIR), out = []) {
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		const path = join(dir, entry.name);
		if (entry.isDirectory()) sitePages(path, out);
		else if (/\.mdx?$/.test(entry.name)) out.push(path);
	}
	return out;
}

test('a top-level key is read bare, dotted or in quotes, and a column-0 line that opens none is given back to be refused', () => {
	assert.equal(topLevelKey('title: A page'), 'title');
	assert.equal(topLevelKey('template : splash'), 'template');
	assert.equal(topLevelKey('sidebar:'), 'sidebar');
	assert.equal(topLevelKey('og.image: a.png'), 'og.image');
	assert.equal(topLevelKey('"sameAs": x'), 'sameAs');
	assert.equal(topLevelKey('"say \\"it\\"": x'), 'say "it"');
	assert.equal(topLevelKey("'sameAs': x"), 'sameAs');
	assert.equal(topLevelKey("'it''s': x"), "it's");
	for (const line of ['  order: 1', '\tlabel: x', '- item', '-', '# note', '']) assert.equal(topLevelKey(line), null, JSON.stringify(line));
	assert.equal(topLevelKey('weird key here: x'), 'weird key here');
	assert.equal(topLevelKey('https://example.org'), 'https://example.org');
	assert.equal(topLevelKey('no colon at all'), 'no colon at all');
});

test('every key the pages carry today is in a class', () => {
	const unclassed = [];
	for (const file of sitePages()) {
		const text = readFileSync(file, 'utf8').replace(/\r\n?/g, '\n');
		const head = /^---[ \t]*\n(?:([\s\S]*?)\n)?---[ \t]*(?:\n|$)/.exec(text)?.[1] ?? '';
		const keys = head.split('\n').flatMap((line) => topLevelKey(line) ?? []);
		for (const key of unclassifiedKeys(keys)) unclassed.push(`${relative(SITE, file)}: ${key}`);
	}
	assert.deepEqual(unclassed, []);
});
