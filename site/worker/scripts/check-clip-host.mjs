// Checks that every clip a deploy staged answers at the clip host.
//
// The zone rule clips-to-range-host sends every `/media/*.webm` request to
// `clipBase` (src/data/site-targets.json), because Static Assets answers a
// byte range with the whole file and browsers then cannot seek. The clip host
// is filled apart from the deploy, so a clip added or re-rendered in the build
// and missing there, or there at another size, would 404 or play the old
// file on the site with every other check green. This asks the clip host for
// the first byte of each staged clip and holds the answer to a 206 whose
// Content-Range names the staged size.
//
// Usage:
//   node site/worker/scripts/check-clip-host.mjs --stage <staged site> --clip-base <url ending in />
//
// --stage is the directory the pages are staged in under the base path (the
// folder that holds media/). Exit 0 when every clip answers, 1 otherwise, 2
// on a usage error.
import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

/** How many clips are asked for at once. */
const PARALLEL = 8;

/**
 * The clips a staged site holds: the `.webm` files of its `media/`, by name.
 *
 * @param {string} site The staged site, the folder that holds media/.
 * @returns {{name: string, size: number}[]} Sorted by name.
 */
export function stagedClips(site) {
	const media = join(site, 'media');
	return readdirSync(media)
		.filter((name) => name.endsWith('.webm'))
		.sort()
		.map((name) => ({ name, size: statSync(join(media, name)).size }));
}

/**
 * What is wrong with the clip host for these clips, one line each.
 *
 * @param {{name: string, size: number}[]} clips The staged clips.
 * @param {string} clipBase Where a clip is redirected to, its name appended.
 * @param {typeof fetch} [fetchImpl]
 * @returns {Promise<string[]>} Empty when every clip answers a 206 with its staged size.
 */
export async function clipHostProblems(clips, clipBase, fetchImpl = fetch) {
	if (clips.length === 0) return ['the build staged no clip (.webm under media/)'];
	const problems = [];
	const check = async ({ name, size }) => {
		try {
			const response = await fetchImpl(`${clipBase}${name}`, { headers: { Range: 'bytes=0-0' }, redirect: 'manual' });
			await response.body?.cancel();
			if (response.status !== 206) {
				problems.push(`${name}: the clip host answered ${response.status}${response.status === 200 ? ', not 206' : ''}`);
				return;
			}
			const total = /\/(\d+)$/.exec(response.headers.get('content-range') ?? '')?.[1];
			if (Number(total) !== size) problems.push(`${name}: ${total ?? 'no'} bytes at the clip host, ${size} staged`);
		} catch (error) {
			problems.push(`${name}: ${error.message}`);
		}
	};
	for (let start = 0; start < clips.length; start += PARALLEL) {
		await Promise.all(clips.slice(start, start + PARALLEL).map(check));
	}
	return problems.sort();
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	let args;
	try {
		args = parseArgs({ args: process.argv.slice(2), options: { stage: { type: 'string' }, 'clip-base': { type: 'string' } } }).values;
	} catch (error) {
		console.log(error.message);
		process.exit(2);
	}
	if (!args.stage || !args['clip-base']?.endsWith('/')) {
		console.log('usage: check-clip-host.mjs --stage <staged site> --clip-base <url ending in />');
		process.exit(2);
	}
	const clips = stagedClips(args.stage);
	const problems = await clipHostProblems(clips, args['clip-base']);
	for (const problem of problems) console.log(`::error::${problem}`);
	console.log(`${clips.length - problems.length} of ${clips.length} clips answer at ${args['clip-base']} with their staged size`);
	process.exit(problems.length === 0 ? 0 : 1);
}
