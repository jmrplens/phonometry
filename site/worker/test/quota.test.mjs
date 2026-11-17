// The daily quota check: thresholds, the day before, unexpected scripts, and
// what it hands GitHub (the level output and the job summary).
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { DAILY_LIMIT, assessQuota, quotaQuery, summaryMarkdown } from '../lib/quota.mjs';
import { runQuotaCheck } from '../scripts/check-quota.mjs';

const at = (iso) => new Date(iso);
const rows = (pairs) => pairs.map(([scriptName, requests]) => ({ dimensions: { scriptName }, sum: { requests } }));

describe('assessQuota', () => {
	const base = { now: at('2026-11-17T12:00:00Z'), yesterday: [], expected: ['phonometry-docs'] };

	test('the limit is the Workers Free daily count', () => {
		assert.equal(DAILY_LIMIT, 100000);
	});

	test('nothing at all is ok', () => {
		const r = assessQuota({ ...base, today: [] });
		assert.equal(r.level, 'ok');
		assert.deepEqual(r.failures, []);
		assert.equal(r.total, 0);
	});

	test('half the quota warns and passes', () => {
		const r = assessQuota({ ...base, today: rows([['phonometry-docs', 50000]]) });
		assert.equal(r.level, 'warn');
		assert.deepEqual(r.failures, []);
		assert.match(r.warnings.join('\n'), /50000 of 100000/);
	});

	test('seventy per cent fails, naming the projection to midnight', () => {
		const r = assessQuota({ ...base, today: rows([['phonometry-docs', 70000]]) });
		assert.equal(r.level, 'alert');
		assert.match(r.failures.join('\n'), /70000 of 100000 Worker requests today \(70\.0 %\)/);
		assert.equal(r.projection, 140000);
	});

	test('the quota is per account, so every script counts', () => {
		const r = assessQuota({ ...base, expected: ['a', 'b'], today: rows([['a', 40000], ['b', 31000]]) });
		assert.equal(r.total, 71000);
		assert.equal(r.level, 'alert');
	});

	test('a day before that reached 99 per cent fails even when today is quiet', () => {
		const r = assessQuota({ ...base, today: [], yesterday: rows([['phonometry-docs', 99000]]) });
		assert.equal(r.level, 'alert');
		assert.match(r.failures.join('\n'), /yesterday: 99000/);
	});

	test('a script nobody expects fails, whatever its count', () => {
		const r = assessQuota({ ...base, today: rows([['stray', 3]]) });
		assert.match(r.failures.join('\n'), /stray is not an expected script/);
		assert.equal(r.level, 'ok');
	});

	test('a threshold of zero fails on an empty day: the proof that the mail arrives', () => {
		const r = assessQuota({ ...base, today: [], alertFraction: 0 });
		assert.equal(r.level, 'alert');
		assert.equal(r.failures.length, 1);
	});

	test('a fraction outside [0, 1] is refused', () => {
		assert.throws(() => assessQuota({ ...base, today: [], alertFraction: 1.5 }), /alert fraction/);
		assert.throws(() => assessQuota({ ...base, today: [], alertFraction: Number.NaN }), /alert fraction/);
	});

	test('the summary names each script, the hour and the projection', () => {
		const r = assessQuota({ ...base, today: rows([['phonometry-docs', 70000]]) });
		const md = summaryMarkdown(r);
		assert.match(md, /\| phonometry-docs \| 70000 \|/);
		assert.match(md, /2026-11-17T12:00:00Z/);
		assert.match(md, /140000/);
	});
});

describe('quotaQuery', () => {
	test('asks the account for the day so far and the whole day before', () => {
		const { today, yesterday } = quotaQuery('acc', at('2026-11-17T12:34:56Z'));
		assert.deepEqual(today.variables, { account: 'acc', start: '2026-11-17T00:00:00Z', end: '2026-11-17T12:34:56Z' });
		assert.deepEqual(yesterday.variables, { account: 'acc', start: '2026-11-16T00:00:00Z', end: '2026-11-17T00:00:00Z' });
		assert.match(today.query, /workersInvocationsAdaptive\(limit: 10000, filter: \{ datetime_geq: \$start, datetime_lt: \$end \}\)/);
		assert.match(today.query, /sum \{ requests \}/);
		assert.match(today.query, /dimensions \{ scriptName \}/);
	});
});

describe('runQuotaCheck', () => {
	/** A GraphQL endpoint answering the recorded empty day of 2026-11-17, or what a case asks. */
	function endpoint(answers) {
		const calls = [];
		const fetchImpl = async (url, init) => {
			calls.push({ url, init });
			const body = answers.shift();
			return new Response(JSON.stringify(body), { status: 200, headers: { 'content-type': 'application/json' } });
		};
		return { calls, fetchImpl };
	}
	const empty = { data: { viewer: { accounts: [{ workersInvocationsAdaptive: [] }] } }, errors: null };
	const env = { CLOUDFLARE_API_TOKEN: 'secret-token', CLOUDFLARE_ACCOUNT_ID: 'acc' };

	test('an empty day exits 0, writes level=ok and a summary, and sends the token only in the header', async () => {
		const { calls, fetchImpl } = endpoint([empty, empty]);
		const out = { output: '', summary: '', log: [] };
		const code = await runQuotaCheck({ argv: [], env, fetchImpl, now: at('2026-11-17T12:00:00Z'), sink: out });
		assert.equal(code, 0);
		assert.equal(out.output, 'level=ok\n');
		assert.match(out.summary, /Workers requests/);
		assert.equal(calls.length, 2);
		assert.equal(calls[0].url, 'https://api.cloudflare.com/client/v4/graphql');
		assert.equal(calls[0].init.headers.authorization, 'Bearer secret-token');
		assert.ok(!out.log.join('\n').includes('secret-token'));
	});

	test('--threshold 0 exits 1 on the same empty day', async () => {
		const { fetchImpl } = endpoint([empty, empty]);
		const out = { output: '', summary: '', log: [] };
		const code = await runQuotaCheck({ argv: ['--threshold', '0'], env, fetchImpl, now: at('2026-11-17T12:00:00Z'), sink: out });
		assert.equal(code, 1);
		assert.equal(out.output, 'level=alert\n');
		assert.match(out.log.join('\n'), /::error::/);
	});

	test('a GraphQL error fails the check rather than reading as a quiet day', async () => {
		const { fetchImpl } = endpoint([{ data: null, errors: [{ message: 'not authorized' }] }, empty]);
		const out = { output: '', summary: '', log: [] };
		const code = await runQuotaCheck({ argv: [], env, fetchImpl, now: at('2026-11-17T12:00:00Z'), sink: out });
		assert.equal(code, 1);
		assert.match(out.log.join('\n'), /not authorized/);
	});

	test('no token, no account: a usage error, before any request', async () => {
		const { calls, fetchImpl } = endpoint([]);
		const out = { output: '', summary: '', log: [] };
		assert.equal(await runQuotaCheck({ argv: [], env: {}, fetchImpl, now: at('2026-11-17T12:00:00Z'), sink: out }), 2);
		assert.equal(calls.length, 0);
	});
});
