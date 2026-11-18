// How close the account is to the daily Workers request quota.
//
// Workers Free gives an account 100 000 Worker requests a day, counted from
// 00:00 UTC across every script of the account
// (https://developers.cloudflare.com/workers/platform/limits/). Requests for
// static assets that no script runs for are free and unlimited and do not
// count. The alert lives in the account, as a Cloudflare notification on the
// same count; this module reads it from the GraphQL Analytics API (dataset
// workersInvocationsAdaptive) for scripts/check-quota.mjs, a check run by
// hand.

export const DAILY_LIMIT = 100000;
/** The fraction of the quota that warns, and the one that fails the job. */
export const WARN_FRACTION = 0.5;
export const ALERT_FRACTION = 0.7;
/** The fraction of the quota a day before has to reach to count as "probably ran out". */
export const SPENT_FRACTION = 0.99;

const QUERY = `query Quota($account: string!, $start: Time!, $end: Time!) {
  viewer {
    accounts(filter: { accountTag: $account }) {
      workersInvocationsAdaptive(limit: 10000, filter: { datetime_geq: $start, datetime_lt: $end }) {
        sum { requests }
        dimensions { scriptName }
      }
    }
  }
}`;

const iso = (date) => `${date.toISOString().slice(0, 19)}Z`;
const midnight = (date) => new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));

/**
 * The two queries: the day so far, and the whole day before.
 *
 * @param {string} account The account id.
 * @param {Date} now The moment of the check.
 * @returns {{today: {query: string, variables: object}, yesterday: {query: string, variables: object}}}
 */
export function quotaQuery(account, now) {
	const start = midnight(now);
	const before = new Date(start.getTime() - 86400000);
	return {
		today: { query: QUERY, variables: { account, start: iso(start), end: iso(now) } },
		yesterday: { query: QUERY, variables: { account, start: iso(before), end: iso(start) } },
	};
}

/**
 * The rows of an answer, as {scriptName, requests}, summed per script.
 *
 * @param {any} data The `data` of a quota query.
 * @returns {{scriptName: string, requests: number}[]} One row per script, largest first.
 */
export function quotaRows(data) {
	const rows = data?.viewer?.accounts?.[0]?.workersInvocationsAdaptive;
	if (!Array.isArray(rows)) throw new Error('the answer holds no workersInvocationsAdaptive rows');
	const per = new Map();
	for (const row of rows) {
		const name = row?.dimensions?.scriptName ?? '(unnamed)';
		per.set(name, (per.get(name) ?? 0) + Number(row?.sum?.requests ?? 0));
	}
	return [...per].map(([scriptName, requests]) => ({ scriptName, requests })).sort((a, b) => b.requests - a.requests);
}

/**
 * What the counts mean.
 *
 * @param {object} options
 * @param {{dimensions: {scriptName: string}, sum: {requests: number}}[] | {scriptName: string, requests: number}[]} options.today
 * @param {typeof options.today} options.yesterday
 * @param {Date} options.now The moment of the check.
 * @param {string[]} options.expected The scripts the account is meant to run.
 * @param {number} [options.alertFraction] The fraction that fails; 0 fails on any day (the proof).
 * @returns {{level: 'ok' | 'warn' | 'alert', total: number, yesterdayTotal: number, projection: number,
 *   scripts: {scriptName: string, requests: number}[], failures: string[], warnings: string[], now: Date}}
 */
export function assessQuota({ today, yesterday, now, expected, alertFraction = ALERT_FRACTION }) {
	if (!(alertFraction >= 0 && alertFraction <= 1)) throw new Error(`alert fraction must be in [0, 1]: ${alertFraction}`);
	const norm = (rows) => quotaRows({ viewer: { accounts: [{ workersInvocationsAdaptive: rows.map(toRow) }] } });
	const scripts = norm(today);
	const total = scripts.reduce((sum, { requests }) => sum + requests, 0);
	const yesterdayTotal = norm(yesterday).reduce((sum, { requests }) => sum + requests, 0);
	const hours = Math.max((now.getTime() - midnight(now).getTime()) / 3600000, 0.25);
	const projection = Math.round((total / hours) * 24);
	const percent = ((100 * total) / DAILY_LIMIT).toFixed(1);
	const failures = [];
	const warnings = [];
	if (total >= alertFraction * DAILY_LIMIT) {
		failures.push(
			`${total} of ${DAILY_LIMIT} Worker requests today (${percent} %), at or over ${Math.round(alertFraction * 100)} %; at this pace ${projection} by 00:00 UTC`,
		);
	} else if (total >= WARN_FRACTION * DAILY_LIMIT) {
		warnings.push(`${total} of ${DAILY_LIMIT} Worker requests today (${percent} %); at this pace ${projection} by 00:00 UTC`);
	}
	if (yesterdayTotal >= SPENT_FRACTION * DAILY_LIMIT) {
		failures.push(`yesterday: ${yesterdayTotal} of ${DAILY_LIMIT} Worker requests; the quota was probably reached`);
	}
	for (const { scriptName, requests } of scripts) {
		if (!expected.includes(scriptName)) failures.push(`${scriptName} is not an expected script (${requests} requests today)`);
	}
	// The level follows from what was found, so a failure can never read as ok.
	const level = failures.length > 0 ? 'alert' : warnings.length > 0 ? 'warn' : 'ok';
	return { level, total, yesterdayTotal, projection, scripts, failures, warnings, now };
}

function toRow(row) {
	return 'dimensions' in row ? row : { dimensions: { scriptName: row.scriptName }, sum: { requests: row.requests } };
}

/**
 * The report check-quota.mjs prints.
 *
 * @param {ReturnType<typeof assessQuota>} report From assessQuota.
 * @returns {string} Markdown.
 */
export function summaryMarkdown(report) {
	const lines = [
		'## Workers requests on the Phonometry account',
		'',
		`Checked at ${iso(report.now)}. Limit: ${DAILY_LIMIT} a day (Workers Free), from 00:00 UTC.`,
		'',
		'| Script | Requests today |',
		'|--------|----------------|',
		...(report.scripts.length > 0 ? report.scripts.map(({ scriptName, requests }) => `| ${scriptName} | ${requests} |`) : ['| (none) | 0 |']),
		'',
		`Total today: ${report.total}. Projected by 00:00 UTC: ${report.projection}. Yesterday: ${report.yesterdayTotal}.`,
		`Level: **${report.level}**.`,
	];
	for (const line of report.failures) lines.push('', `- FAIL: ${line}`);
	for (const line of report.warnings) lines.push('', `- WARN: ${line}`);
	return `${lines.join('\n')}\n`;
}
