// Checks, or puts, the zone rules of phonometry.dev (lib/rules.mjs).
//
// Usage:
//   CLOUDFLARE_API_TOKEN=... node site/worker/scripts/apply-rules.mjs
//       [--check | --apply] [--backup-dir <dir>] [--clip-base <url/>]
//
// --check (the default) reads both phase entrypoints and exits 1 when the live
// rules differ from the generated ones; nothing is written. --apply first
// saves what each entrypoint holds, one JSON file per phase under
// --backup-dir ($RUNNER_TEMP or the working directory by default), then
// replaces the entrypoint's rules with the generated ones. Rolling back is a
// PUT of a saved file's `rules`. The token needs, on the zone, Dynamic URL
// Redirects Edit and Transform Rules Edit (Read for --check).
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';

import { basePath, mediaOrigins } from '../../src/data/site.mjs';
import { CloudflareError, ZONE_ID, cfApi, ignoredTargets } from '../lib/cloudflare.mjs';
import { redirectRules, responseHeaderRules } from '../lib/rules.mjs';
import { ruleDrift } from '../lib/rulesets.mjs';
import { twinExclusions } from '../lib/twins.mjs';

export const HOST = 'phonometry.dev';
/** Until the R2 bucket serves the clips, docs.jmrp.io does: it answers ranges with 206. */
export const CLIP_BASE = 'https://docs.jmrp.io/phonometry/media/';

/**
 * Refuses a clip host the pages do not allow.
 *
 * A browser holds the address a clip is redirected to to the page's
 * Content-Security-Policy, so a host missing from `media-src` blocks every
 * clip while curl still sees a 302 and a 206. Both policies list
 * `mediaOrigins` (site/src/data/site.mjs); a new host goes there first, and a
 * build with it is deployed before the rule points at it.
 *
 * @param {string} clipBase The clip base, ending in `/`.
 */
export function checkClipBase(clipBase) {
	let url;
	try {
		url = new URL(clipBase);
	} catch {
		throw new Error(`clip base is not a URL: ${clipBase}`);
	}
	if (url.protocol !== 'https:' || !url.pathname.endsWith('/')) throw new Error(`clip base must be https and its path end in /: ${clipBase}`);
	// The clip name is appended to the base, so a query or a fragment would swallow it.
	if (url.search !== '' || url.hash !== '' || clipBase.includes('?') || clipBase.includes('#')) {
		throw new Error(`clip base must carry no query or fragment: ${clipBase}`);
	}
	// The rule appends the clip name to the string as given, so it must be the
	// URL a parser writes back: no surrounding space, no case or escape to fix.
	if (url.href !== clipBase) throw new Error(`clip base must be written the way it parses, ${url.href}; as written it is ${JSON.stringify(clipBase)}`);
	if (!mediaOrigins.includes(url.origin)) {
		throw new Error(`clip host ${url.origin} is not in mediaOrigins (site/src/data/site.mjs), so the pages would block its clips`);
	}
}

/** The two phases and the rules each takes. */
export function generatedPhases({ clipBase = CLIP_BASE, prefix = basePath } = {}) {
	checkClipBase(clipBase);
	return [
		{ phase: 'http_request_dynamic_redirect', rules: redirectRules({ host: HOST, prefix, exclusions: twinExclusions(prefix), clipBase }) },
		{ phase: 'http_response_headers_transform', rules: responseHeaderRules({ host: HOST, prefix }) },
	];
}

/** The rules a phase entrypoint holds, [] when the zone has none yet. */
async function liveRules(zone, phase, api) {
	try {
		const result = await api(`/zones/${zone}/rulesets/phases/${phase}/entrypoint`);
		return result?.rules ?? [];
	} catch (error) {
		if (error instanceof CloudflareError && error.status === 404) return [];
		throw error;
	}
}

/**
 * Runs the check or the apply.
 *
 * @param {{argv: string[], env: Record<string, string | undefined>, fetchImpl?: typeof fetch, sink?: {log: string[]}}} options
 * @returns {Promise<number>} 0 when the zone is (now) as generated, 1 on drift or error, 2 on usage.
 */
export async function runApplyRules({ argv, env, fetchImpl = fetch, sink = null }) {
	const log = (line) => (sink ? sink.log.push(line) : console.log(line));
	let args;
	try {
		args = parseArgs({
			args: argv,
			options: { check: { type: 'boolean' }, apply: { type: 'boolean' }, 'backup-dir': { type: 'string' }, 'clip-base': { type: 'string' } },
		}).values;
	} catch (error) {
		log(error.message);
		return 2;
	}
	if (args.check && args.apply) {
		log('pass at most one of --check and --apply');
		return 2;
	}
	const zone = ZONE_ID;
	for (const line of ignoredTargets(env)) log(line);
	const api = (path, options = {}) => cfApi(path, { ...options, env, fetchImpl });
	const backupDir = args['backup-dir'] ?? env.RUNNER_TEMP ?? process.cwd();
	const stamp = new Date().toISOString().replaceAll(':', '-');
	let drifted = false;
	try {
		for (const { phase, rules } of generatedPhases({ clipBase: args['clip-base'] ?? CLIP_BASE })) {
			const live = await liveRules(zone, phase, api);
			const drift = ruleDrift(live, rules);
			for (const line of drift) log(`${phase}: ${line}`);
			if (!args.apply) {
				if (drift.length > 0) drifted = true;
				else log(`${phase}: as generated (${rules.length} rules)`);
				continue;
			}
			mkdirSync(backupDir, { recursive: true });
			const saved = join(backupDir, `${phase}-${stamp}.json`);
			writeFileSync(saved, `${JSON.stringify({ phase, rules: live }, null, 2)}\n`);
			const result = await api(`/zones/${zone}/rulesets/phases/${phase}/entrypoint`, { method: 'PUT', body: { rules } });
			log(`${phase}: ${rules.length} rules put (version ${result?.version ?? '?'}); what was there is in ${saved}`);
		}
	} catch (error) {
		log(`error: ${error.message}`);
		return 1;
	}
	return drifted ? 1 : 0;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.exitCode = await runApplyRules({ argv: process.argv.slice(2), env: process.env });
}
