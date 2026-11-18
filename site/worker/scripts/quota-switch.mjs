// The quota guard's decision, run by hand: the lever for the maintainer when
// the guard cannot act (no token yet, or an account whose quota ran out
// before the guard's cron could, which stops that cron too).
//
// Usage:
//   CLOUDFLARE_EMAIL=... CLOUDFLARE_API_KEY=... \
//     node site/worker/scripts/quota-switch.mjs [--mode dry-run|auto|off|on] [--threshold <n>]
//
// dry-run (the default) reads the day's count, the WAF rule
// quota-guard-beacon and the live version of phonometry-docs, and prints what
// the guard would do. auto does it. off switches the code paths off now (the
// rule on, the assets-only version live) and on switches them back (the full
// version, then the rule off), whatever the count. A deploy made with off or
// on says `quota switch by hand` in its message, so the guard's cron leaves
// it alone: the site stays off until `--mode on`, also after 00:00 UTC (the
// guard still switches off at the threshold). A token needs Account
// Analytics Read, Workers Scripts Write and Zone WAF Write on phonometry.dev.
// Exit 0 when done, 1 on an error, 2 on a usage error.
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';

import { ignoredTargets } from '../lib/cloudflare.mjs';
import { DEFAULT_THRESHOLD, reconcile } from '../lib/guard.mjs';

/**
 * Runs the switch.
 *
 * @param {{argv: string[], env: Record<string, string | undefined>, fetchImpl?: typeof fetch, now?: Date, sink?: {log: string[]}}} options
 * @returns {Promise<number>} The exit code.
 */
export async function runQuotaSwitch({ argv, env, fetchImpl = fetch, now = new Date(), sink = null }) {
	const log = (line) => (sink ? sink.log.push(line) : console.log(line));
	let args;
	try {
		args = parseArgs({ args: argv, options: { mode: { type: 'string' }, threshold: { type: 'string' } } }).values;
	} catch (error) {
		log(error.message);
		return 2;
	}
	const mode = args.mode ?? 'dry-run';
	if (!['dry-run', 'auto', 'off', 'on'].includes(mode)) {
		log(`--mode is dry-run, auto, off or on, not ${mode}`);
		return 2;
	}
	if (!(env.CLOUDFLARE_API_TOKEN || (env.CLOUDFLARE_EMAIL && env.CLOUDFLARE_API_KEY))) {
		log('set CLOUDFLARE_API_TOKEN, or CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY');
		return 2;
	}
	for (const line of ignoredTargets(env)) log(line);
	const credentials = { CLOUDFLARE_API_TOKEN: env.CLOUDFLARE_API_TOKEN, CLOUDFLARE_EMAIL: env.CLOUDFLARE_EMAIL, CLOUDFLARE_API_KEY: env.CLOUDFLARE_API_KEY };
	const report = await reconcile({ env: { ...credentials, MODE: mode, THRESHOLD: args.threshold ?? String(DEFAULT_THRESHOLD) }, fetchImpl, now, byHand: true });
	for (const line of report.lines) log(line);
	return report.error ? 1 : 0;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.exitCode = await runQuotaSwitch({ argv: process.argv.slice(2), env: process.env });
}
