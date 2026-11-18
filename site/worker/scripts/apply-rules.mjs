// Checks, or puts, the zone rules of phonometry.dev (lib/rules.mjs).
//
// Usage:
//   CLOUDFLARE_API_TOKEN=... node site/worker/scripts/apply-rules.mjs
//       [--check | --apply] [--phase edge|waf] [--backup-dir <dir>] [--clip-base <url/>]
//
// --phase edge (the default) is the redirect and response-header phases, the
// two the CI rules token can read and write. --phase waf is the beacon's WAF
// custom rules and its rate limiting rule (lib/rules.mjs), which that token
// cannot touch: they are applied by hand with a token that has Zone WAF Edit
// (or the account key). The quota guard owns the `enabled` bit of the rule
// quota-guard-beacon: an apply creates it off and otherwise keeps the
// value it finds, and --check does not count it as drift. While that rule is
// on, an apply refuses to rewrite the custom rules: a PUT of the entrypoint
// renews every rule's last update, which the guard reads as the day of its
// trip, and could put back an `enabled` the guard changed after the read.
// Apply them once the guard has switched the beacon back on (or after
// `quota-switch.mjs --mode on`).
//
// --check (the default) reads both phase entrypoints and exits 1 when the live
// rules differ from the generated ones; nothing is written. --apply puts only
// a phase that differs: it first saves what the entrypoint holds, one JSON
// file per phase under --backup-dir ($RUNNER_TEMP or the working directory by
// default), then replaces the entrypoint's rules with the generated ones. A
// phase already as generated is left untouched. Rolling back is a
// PUT of a saved file's `rules`. The token needs, on the zone, Dynamic URL
// Redirects Edit and Transform Rules Edit (Read for --check).
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';

import { basePath, mediaOrigins } from '../../src/data/site.mjs';
import { CloudflareError, ZONE_ID, cfApi, ignoredTargets } from '../lib/cloudflare.mjs';
import { GUARD_RULE_REF } from '../lib/guard.mjs';
import { firewallRules, rateLimitRules, redirectRules, responseHeaderRules } from '../lib/rules.mjs';
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

/** The beacon's WAF phases. */
export function wafPhases() {
	return [
		{ phase: 'http_request_firewall_custom', rules: firewallRules({ host: HOST }) },
		{ phase: 'http_ratelimit', rules: rateLimitRules() },
	];
}

/**
 * The generated rules with the guard rule's `enabled` as the zone holds it:
 * the guard switches it, and an apply or a check must neither undo nor
 * report that.
 *
 * @param {object[]} rules The generated rules of a phase.
 * @param {object[]} live What the entrypoint holds now.
 * @returns {object[]} The rules to compare and put.
 */
export function keepGuardState(rules, live) {
	const current = live.find((rule) => rule.ref === GUARD_RULE_REF);
	if (!current) return rules;
	return rules.map((rule) => (rule.ref === GUARD_RULE_REF ? { ...rule, enabled: Boolean(current.enabled) } : rule));
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
			options: { check: { type: 'boolean' }, apply: { type: 'boolean' }, phase: { type: 'string' }, 'backup-dir': { type: 'string' }, 'clip-base': { type: 'string' } },
		}).values;
	} catch (error) {
		log(error.message);
		return 2;
	}
	if (args.check && args.apply) {
		log('pass at most one of --check and --apply');
		return 2;
	}
	const which = args.phase ?? 'edge';
	if (which !== 'edge' && which !== 'waf') {
		log(`--phase is edge or waf, not ${which}`);
		return 2;
	}
	const zone = ZONE_ID;
	for (const line of ignoredTargets(env)) log(line);
	const api = (path, options = {}) => cfApi(path, { ...options, env, fetchImpl });
	const backupDir = args['backup-dir'] ?? env.RUNNER_TEMP ?? process.cwd();
	const stamp = new Date().toISOString().replaceAll(':', '-');
	let drifted = false;
	try {
		const phases = which === 'waf' ? wafPhases() : generatedPhases({ clipBase: args['clip-base'] ?? CLIP_BASE });
		for (const { phase, rules: generated } of phases) {
			const live = await liveRules(zone, phase, api);
			const rules = keepGuardState(generated, live);
			const drift = ruleDrift(live, rules);
			for (const line of drift) log(`${phase}: ${line}`);
			if (drift.length === 0) {
				log(`${phase}: as generated (${rules.length} rules)${args.apply ? ', nothing put' : ''}`);
				continue;
			}
			if (!args.apply) {
				drifted = true;
				continue;
			}
			if (live.some((rule) => rule.ref === GUARD_RULE_REF && rule.enabled)) {
				log(`${phase}: not put: the quota guard holds ${GUARD_RULE_REF} on, and a put would renew the date it reads as its trip; apply after it switches the beacon back on`);
				drifted = true;
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
