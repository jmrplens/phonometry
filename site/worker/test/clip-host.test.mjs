// The deploy check that every clip the build staged answers at the clip
// host, the same name and the same size, with a byte range
// (scripts/check-clip-host.mjs). A clip added or re-rendered while the clip
// host is frozen fails the deploy instead of 404-ing on the site.
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, test } from 'node:test';

import { clipHostProblems, stagedClips } from '../scripts/check-clip-host.mjs';

const made = [];
afterEach(() => {
	while (made.length) rmSync(made.pop(), { recursive: true, force: true });
});

const BASE = 'https://media.example.org/';

/** A fetch that answers each clip as `served` says: a size, a status, or a throw. */
function host(served) {
	const asked = [];
	const fetchImpl = async (url, init) => {
		asked.push({ url, range: init?.headers?.Range ?? init?.headers?.range });
		const name = url.slice(BASE.length);
		const answer = served[name];
		if (answer === undefined) return new Response('not found', { status: 404 });
		if (answer instanceof Error) throw answer;
		if (typeof answer === 'object') return new Response('x', answer);
		return new Response('x', { status: 206, headers: { 'content-range': `bytes 0-0/${answer}` } });
	};
	return { asked, fetchImpl };
}

test('every staged clip at the clip host, same size, as a 206: no problem, one ranged request each', async () => {
	const { asked, fetchImpl } = host({ 'a.webm': 10, 'b.webm': 2000 });
	const clips = [{ name: 'a.webm', size: 10 }, { name: 'b.webm', size: 2000 }];
	assert.deepEqual(await clipHostProblems(clips, BASE, fetchImpl), []);
	assert.deepEqual(asked.map(({ url }) => url).sort(), [`${BASE}a.webm`, `${BASE}b.webm`]);
	assert.ok(asked.every(({ range }) => range === 'bytes=0-0'));
});

test('a clip the host lacks, one of another size, one answered whole and one that cannot be fetched are named', async () => {
	const { fetchImpl } = host({
		'a.webm': 11,
		'whole.webm': { status: 200, headers: { 'content-length': '5' } },
		'down.webm': new Error('connect ECONNREFUSED'),
	});
	const clips = [
		{ name: 'a.webm', size: 10 },
		{ name: 'gone.webm', size: 3 },
		{ name: 'whole.webm', size: 5 },
		{ name: 'down.webm', size: 7 },
	];
	const problems = (await clipHostProblems(clips, BASE, fetchImpl)).join('\n');
	assert.match(problems, /a\.webm: 11 bytes at the clip host, 10 staged/);
	assert.match(problems, /gone\.webm: the clip host answered 404/);
	assert.match(problems, /whole\.webm: the clip host answered 200, not 206/);
	assert.match(problems, /down\.webm: connect ECONNREFUSED/);
});

test('no staged clip is a problem itself: the check cannot pass by finding nothing', async () => {
	assert.deepEqual(await clipHostProblems([], BASE, host({}).fetchImpl), ['the build staged no clip (.webm under media/)']);
});

test('the staged clips are the .webm files of media/, with their sizes', () => {
	const root = mkdtempSync(join(tmpdir(), 'clip-host-'));
	made.push(root);
	mkdirSync(join(root, 'media'));
	writeFileSync(join(root, 'media', 'b.webm'), 'xyz');
	writeFileSync(join(root, 'media', 'a.webm'), 'x');
	writeFileSync(join(root, 'media', 'a_poster.webp'), 'p');
	assert.deepEqual(stagedClips(root), [{ name: 'a.webm', size: 1 }, { name: 'b.webm', size: 3 }]);
});
