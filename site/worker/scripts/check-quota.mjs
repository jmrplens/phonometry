// Reads how much of its daily Workers request quota the Phonometry account has spent.
//
// Usage, by hand (the alert itself is a Cloudflare notification on the
// account; nothing in GitHub reads this count):
//   CLOUDFLARE_EMAIL=... CLOUDFLARE_API_KEY=... \
//     node site/worker/scripts/check-quota.mjs [--threshold <0..1>] [--expect <script>]...
//
// A token needs Account Analytics Read and nothing else. It prints the count
// per script with the projection to 00:00 UTC, and exits 0 when it is fine (a
// warning from 50 %), 1 when it fails (70 % of today, 99 % yesterday, a script
// not passed with --expect, or an answer that could not be read), 2 on a usage
// error. --threshold 0 fails on any day.
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';

import { ACCOUNT_ID, graphql, ignoredTargets } from '../lib/cloudflare.mjs';
import { ALERT_FRACTION, assessQuota, quotaQuery, quotaRows, summaryMarkdown } from '../lib/quota.mjs';

/**
 * Runs the check.
 *
 * @param {object} options
 * @param {string[]} options.argv The arguments.
 * @param {Record<string, string | undefined>} options.env The environment.
 * @param {typeof fetch} [options.fetchImpl] The fetch (tests pass a recorded endpoint).
 * @param {Date} [options.now] The moment of the check.
 * @param {{log: string[]}} [options.sink] Collects what would be printed (tests).
 * @returns {Promise<number>} The exit code.
 */
export async function runQuotaCheck({ argv, env, fetchImpl = fetch, now = new Date(), sink = null }) {
	const log = (line) => (sink ? sink.log.push(line) : console.log(line));
	let args;
	try {
		args = parseArgs({ args: argv, options: { threshold: { type: 'string' }, expect: { type: 'string', multiple: true } } }).values;
	} catch (error) {
		log(error.message);
		return 2;
	}
	if (!(env.CLOUDFLARE_API_TOKEN || (env.CLOUDFLARE_EMAIL && env.CLOUDFLARE_API_KEY))) {
		log('set CLOUDFLARE_API_TOKEN (Account Analytics Read), or CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY');
		return 2;
	}
	for (const line of ignoredTargets(env)) log(line);
	const alertFraction = args.threshold === undefined ? ALERT_FRACTION : Number(args.threshold);
	let report;
	try {
		const { today, yesterday } = quotaQuery(ACCOUNT_ID, now);
		const [a, b] = await Promise.all([graphql(today, { env, fetchImpl }), graphql(yesterday, { env, fetchImpl })]);
		report = assessQuota({ today: quotaRows(a), yesterday: quotaRows(b), now, expected: args.expect ?? [], alertFraction });
	} catch (error) {
		log(`FAIL the quota could not be read: ${error.message}`);
		return 1;
	}
	log(summaryMarkdown(report).trimEnd());
	return report.failures.length > 0 ? 1 : 0;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.exitCode = await runQuotaCheck({ argv: process.argv.slice(2), env: process.env });
}
