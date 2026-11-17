// Fails when the Phonometry account nears its daily Workers request quota.
//
// Usage (the scheduled job in .github/workflows/workers-quota.yml):
//   CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=... \
//     node site/worker/scripts/check-quota.mjs [--threshold <0..1>] [--expect <script>]...
//
// The token needs Account Analytics Read and nothing else. Exit 0 when the
// count is fine (a warning annotation from 50 %), 1 when it fails (70 % of
// today, 99 % yesterday, a script not passed with --expect, or an answer that
// could not be read), 2 on a usage error. It writes `level=ok|warn|alert` to
// $GITHUB_OUTPUT and a table to $GITHUB_STEP_SUMMARY when they are set.
// --threshold 0 fails on any day: it is how the mail is proved to arrive.
import { appendFileSync } from 'node:fs';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';

import { graphql } from '../lib/cloudflare.mjs';
import { ALERT_FRACTION, assessQuota, quotaQuery, quotaRows, summaryMarkdown } from '../lib/quota.mjs';

/**
 * Runs the check.
 *
 * @param {object} options
 * @param {string[]} options.argv The arguments.
 * @param {Record<string, string | undefined>} options.env The environment.
 * @param {typeof fetch} [options.fetchImpl] The fetch (tests pass a recorded endpoint).
 * @param {Date} [options.now] The moment of the check.
 * @param {{output: string, summary: string, log: string[]}} [options.sink] Collects what would go to
 *   $GITHUB_OUTPUT, $GITHUB_STEP_SUMMARY and the console (tests); absent, those are written.
 * @returns {Promise<number>} The exit code.
 */
export async function runQuotaCheck({ argv, env, fetchImpl = fetch, now = new Date(), sink = null }) {
	const log = (line) => (sink ? sink.log.push(line) : console.log(line));
	let args;
	try {
		args = parseArgs({ args: argv, options: { threshold: { type: 'string' }, expect: { type: 'string', multiple: true } } }).values;
	} catch (error) {
		log(`::error::${error.message}`);
		return 2;
	}
	const account = env.CLOUDFLARE_ACCOUNT_ID;
	if (!account || !(env.CLOUDFLARE_API_TOKEN || (env.CLOUDFLARE_EMAIL && env.CLOUDFLARE_API_KEY))) {
		log('::error::set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN (Account Analytics Read)');
		return 2;
	}
	const alertFraction = args.threshold === undefined ? ALERT_FRACTION : Number(args.threshold);
	const write = (kind, text) => {
		if (sink) sink[kind] += text;
		else if (kind === 'output' && env.GITHUB_OUTPUT) appendFileSync(env.GITHUB_OUTPUT, text);
		else if (kind === 'summary' && env.GITHUB_STEP_SUMMARY) appendFileSync(env.GITHUB_STEP_SUMMARY, text);
	};
	let report;
	try {
		const { today, yesterday } = quotaQuery(account, now);
		const [a, b] = await Promise.all([graphql(today, { env, fetchImpl }), graphql(yesterday, { env, fetchImpl })]);
		report = assessQuota({ today: quotaRows(a), yesterday: quotaRows(b), now, expected: args.expect ?? [], alertFraction });
	} catch (error) {
		log(`::error::the quota could not be read: ${error.message}`);
		write('output', 'level=alert\n');
		return 1;
	}
	write('output', `level=${report.level}\n`);
	write('summary', summaryMarkdown(report));
	for (const line of report.warnings) log(`::warning::${line}`);
	for (const line of report.failures) log(`::error::${line}`);
	log(`Workers requests today: ${report.total} (level ${report.level})`);
	return report.failures.length > 0 ? 1 : 0;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.exitCode = await runQuotaCheck({ argv: process.argv.slice(2), env: process.env });
}
