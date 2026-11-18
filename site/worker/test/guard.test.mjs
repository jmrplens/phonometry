// The quota guard: what it decides from the day's count, the WAF rule and the
// live version, and the API calls that carry the decision out, on recorded
// answers.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { decide, guardDeploy, pairKey, reconcile, GUARD_RULE_REF } from '../lib/guard.mjs';

const NOW = new Date('2026-11-18T14:00:00Z');
const today = '2026-11-18T13:00:00.000000Z';
const yesterday = '2026-11-17T23:50:00.000000Z';
const versions = [
	{ id: 'v-full-2', tag: 'full-200-1', created: '2026-11-18T10:00:00Z' },
	{ id: 'v-assets-2', tag: 'assets-200-1', created: '2026-11-18T09:59:00Z' },
	{ id: 'v-full-1', tag: 'full-100-1', created: '2026-11-17T10:00:00Z' },
	{ id: 'v-assets-1', tag: 'assets-100-1', created: '2026-11-17T09:59:00Z' },
	{ id: 'v-hand', tag: '', created: '2026-11-16T10:00:00Z' },
];
const state = (over = {}) => ({ count: 1000, threshold: 95000, mode: 'auto', now: NOW, rule: { enabled: false, lastUpdated: yesterday }, current: { id: 'v-full-2', tag: 'full-200-1' }, versions, ...over });

describe('pairKey', () => {
	test('the run a tag belongs to, and which half of the pair it is', () => {
		assert.deepEqual(pairKey('full-200-1'), { half: 'full', key: '200-1' });
		assert.deepEqual(pairKey('assets-local-20261118T1400'), { half: 'assets', key: 'local-20261118T1400' });
		assert.equal(pairKey(''), null);
		assert.equal(pairKey('v1'), null);
	});
});

const TRIPPED = 'quota guard: off at 95012 of 95000';

describe('guardDeploy', () => {
	test('the guard mark, and which way it switched', () => {
		assert.deepEqual(guardDeploy('quota guard: off at 95012 of 95000'), { guard: true, off: true });
		assert.deepEqual(guardDeploy('quota guard: on at 4 of 95000'), { guard: true, off: false });
		assert.deepEqual(guardDeploy('quota switch by hand: off at 7 of 95000'), { guard: false, off: false });
		assert.deepEqual(guardDeploy('full half of 200-1'), { guard: false, off: false });
		assert.deepEqual(guardDeploy(''), { guard: false, off: false });
		assert.deepEqual(guardDeploy(undefined), { guard: false, off: false });
	});
});

describe('decide', () => {
	test('below the threshold with everything on: nothing to do', () => {
		assert.deepEqual(decide(state()), { desired: 'on', actions: [], notes: [] });
	});

	test('at the threshold: the rule on first, then the paired assets-only version', () => {
		assert.deepEqual(decide(state({ count: 95000 })).actions, [{ kind: 'rule', enabled: true }, { kind: 'deploy', versionId: 'v-assets-2', tag: 'assets-200-1' }]);
	});

	test('tripped today: stays off even when the count reads lower', () => {
		const d = decide(state({ count: 10, rule: { enabled: true, lastUpdated: today }, current: { id: 'v-assets-2', tag: 'assets-200-1' } }));
		assert.equal(d.desired, 'off');
		assert.deepEqual(d.actions, []);
	});

	test('a CI deploy while tripped: rolled to its own assets-only half', () => {
		const d = decide(state({ count: 10, rule: { enabled: true, lastUpdated: today }, current: { id: 'v-full-2', tag: 'full-200-1' } }));
		assert.deepEqual(d.actions, [{ kind: 'deploy', versionId: 'v-assets-2', tag: 'assets-200-1' }]);
	});

	test('the first tick after 00:00 UTC: the full version first, then the rule off', () => {
		const d = decide(state({ count: 5, rule: { enabled: true, lastUpdated: yesterday }, current: { id: 'v-assets-2', tag: 'assets-200-1', message: TRIPPED } }));
		assert.equal(d.desired, 'on');
		assert.deepEqual(d.actions, [{ kind: 'deploy', versionId: 'v-full-2', tag: 'full-200-1' }, { kind: 'rule', enabled: false }]);
	});

	test('a CI deploy made while tripped carries the guard mark, so the reset switches it back', () => {
		const d = decide(state({ count: 5, rule: { enabled: true, lastUpdated: yesterday }, current: { id: 'v-assets-2', tag: 'assets-200-1', message: 'quota guard: off, deploy of 200-1 while the quota guard is tripped' } }));
		assert.deepEqual(d.actions, [{ kind: 'deploy', versionId: 'v-full-2', tag: 'full-200-1' }, { kind: 'rule', enabled: false }]);
	});

	test('back on but the rule could not be turned off last time: only the rule', () => {
		const d = decide(state({ count: 5, rule: { enabled: true, lastUpdated: yesterday }, current: { id: 'v-full-2', tag: 'full-200-1', message: 'quota guard: on at 4 of 95000' } }));
		assert.deepEqual(d.actions, [{ kind: 'rule', enabled: false }]);
	});

	test('a version with no pair: the newest assets-only version, said loudly', () => {
		const d = decide(state({ count: 99000, current: { id: 'v-hand', tag: '' } }));
		assert.deepEqual(d.actions, [{ kind: 'rule', enabled: true }, { kind: 'deploy', versionId: 'v-assets-2', tag: 'assets-200-1' }]);
		assert.match(d.notes.join('\n'), /no paired version/);
	});

	test('back on with no paired full version: the newest full one', () => {
		const d = decide(state({ count: 5, rule: { enabled: false, lastUpdated: yesterday }, current: { id: 'v-hand', tag: 'assets-999-1', message: TRIPPED } }));
		assert.deepEqual(d.actions, [{ kind: 'deploy', versionId: 'v-full-2', tag: 'full-200-1' }]);
	});

	// What the guard did not switch off, it does not switch back on.
	test('a rollback to a version with no tag, at a low count: left as it is', () => {
		const d = decide(state({ count: 7, current: { id: 'v-hand', tag: '', message: '' } }));
		assert.equal(d.desired, 'on');
		assert.deepEqual(d.actions, []);
		assert.match(d.notes.join('\n'), /v-hand \(no tag\) was put there by a deployment with no message, not by the guard: left as it is/);
	});

	test('an assets-only version deployed by hand, at a low count: left as it is', () => {
		const d = decide(state({ count: 7, current: { id: 'v-assets-1', tag: 'assets-100-1', message: 'beacon off while I look at something' } }));
		assert.deepEqual(d.actions, []);
		assert.match(d.notes.join('\n'), /"beacon off while I look at something", not by the guard/);
	});

	test('the day after quota-switch.mjs --mode off: neither the version nor the rule comes back', () => {
		const d = decide(state({ count: 7, rule: { enabled: true, lastUpdated: yesterday }, current: { id: 'v-assets-2', tag: 'assets-200-1', message: 'quota switch by hand: off at 7 of 95000' } }));
		assert.equal(d.desired, 'on');
		assert.deepEqual(d.actions, []);
		assert.match(d.notes.join('\n'), /the rule is on and the live deployment is "quota switch by hand: off at 7 of 95000", not the guard's: left on/);
	});

	test('at the threshold a hand deploy is still switched off: the quota comes first', () => {
		const d = decide(state({ count: 96000, current: { id: 'v-full-1', tag: 'full-100-1', message: 'by hand' } }));
		assert.deepEqual(d.actions, [{ kind: 'rule', enabled: true }, { kind: 'deploy', versionId: 'v-assets-1', tag: 'assets-100-1' }]);
	});

	test('mode off and on pin a state whatever the count', () => {
		assert.equal(decide(state({ mode: 'off' })).desired, 'off');
		assert.equal(decide(state({ mode: 'on', count: 99999, rule: { enabled: true, lastUpdated: today } })).desired, 'on');
	});

	test('mode on switches back what someone else switched off', () => {
		const d = decide(state({ mode: 'on', count: 7, rule: { enabled: true, lastUpdated: yesterday }, current: { id: 'v-assets-2', tag: 'assets-200-1', message: 'quota switch by hand: off at 7 of 95000' } }));
		assert.deepEqual(d.actions, [{ kind: 'deploy', versionId: 'v-full-2', tag: 'full-200-1' }, { kind: 'rule', enabled: false }]);
	});

	test('no rule in the zone: said, and the version still switches', () => {
		const d = decide(state({ count: 96000, rule: null }));
		assert.deepEqual(d.actions, [{ kind: 'deploy', versionId: 'v-assets-2', tag: 'assets-200-1' }]);
		assert.match(d.notes.join('\n'), /no WAF rule quota-guard-beacon/);
	});
});

/** A fetch that answers from a table of recorded responses and records every call. */
function recorded(table) {
	const calls = [];
	const fetchImpl = async (url, init = {}) => {
		const method = init.method ?? 'GET';
		const path = String(url).replace('https://api.cloudflare.com/client/v4', '');
		calls.push({ method, path, body: init.body ? JSON.parse(init.body) : undefined, auth: init.headers?.authorization });
		const key = `${method} ${path.split('?')[0]}`;
		const answer = table[key];
		if (!answer) return new Response(JSON.stringify({ success: false, errors: [{ code: 404, message: `not recorded: ${key}` }] }), { status: 404 });
		return new Response(JSON.stringify(typeof answer === 'function' ? answer() : answer), { status: 200 });
	};
	return { calls, fetchImpl };
}

const A = '4dbfb3b955a0c856bfe066f2a6061dd5';
const Z = '594554a63737deee229566971a765fd4';
const RULE = { id: 'r1', ref: GUARD_RULE_REF, description: 'x', expression: 'http.host eq "phonometry.dev" and http.request.uri.path eq "/_v"', action: 'block', enabled: false, last_updated: yesterday };
const answers = (count) => ({
	'POST /graphql': { data: { viewer: { accounts: [{ workersInvocationsAdaptive: [{ sum: { requests: count }, dimensions: { scriptName: 'phonometry-docs' } }] }] } } },
	[`GET /zones/${Z}/rulesets/phases/http_request_firewall_custom/entrypoint`]: { success: true, result: { id: 'rs1', rules: [RULE] } },
	[`GET /accounts/${A}/workers/scripts/phonometry-docs/deployments`]: {
		success: true,
		result: { deployments: [{ id: 'd1', annotations: { 'workers/message': 'full half of 200-1', 'workers/triggered_by': 'deployment' }, versions: [{ version_id: 'v-full-2', percentage: 100 }] }] },
	},
	[`GET /accounts/${A}/workers/scripts/phonometry-docs/versions`]: {
		success: true,
		result: { items: versions.map((v) => ({ id: v.id, metadata: { created_on: v.created }, annotations: v.tag ? { 'workers/tag': v.tag } : {} })) },
	},
	[`PATCH /zones/${Z}/rulesets/rs1/rules/r1`]: { success: true, result: {} },
	[`POST /accounts/${A}/workers/scripts/phonometry-docs/deployments`]: { success: true, result: { id: 'd2' } },
});

describe('reconcile', () => {
	test('without a token: dry, no call made, the missing scope named', async () => {
		const { calls, fetchImpl } = recorded({});
		const report = await reconcile({ env: { THRESHOLD: '95000', MODE: 'auto' }, fetchImpl, now: NOW });
		assert.equal(calls.length, 0);
		assert.equal(report.dry, true);
		assert.match(report.lines.join('\n'), /no CF_GUARD_TOKEN/);
	});

	test('dry-run reads everything and writes nothing', async () => {
		const { calls, fetchImpl } = recorded(answers(97000));
		const report = await reconcile({ env: { CF_GUARD_TOKEN: 't', THRESHOLD: '95000', MODE: 'dry-run' }, fetchImpl, now: NOW });
		assert.deepEqual(calls.map((c) => c.method), ['POST', 'GET', 'GET', 'GET']);
		assert.equal(report.decision.desired, 'off');
		assert.match(report.lines.join('\n'), /dry-run: would turn the rule on/);
	});

	test('auto at 97 000: the rule patched on, then the assets-only version deployed', async () => {
		const { calls, fetchImpl } = recorded(answers(97000));
		await reconcile({ env: { CF_GUARD_TOKEN: 't', THRESHOLD: '95000', MODE: 'auto' }, fetchImpl, now: NOW });
		const writes = calls.filter((c) => c.method !== 'GET' && c.path !== '/graphql');
		assert.deepEqual(writes.map((c) => `${c.method} ${c.path}`), [`PATCH /zones/${Z}/rulesets/rs1/rules/r1`, `POST /accounts/${A}/workers/scripts/phonometry-docs/deployments`]);
		assert.deepEqual(writes[0].body, { ref: RULE.ref, description: RULE.description, expression: RULE.expression, action: 'block', enabled: true });
		assert.deepEqual(writes[1].body, { strategy: 'percentage', versions: [{ version_id: 'v-assets-2', percentage: 100 }], annotations: { 'workers/message': 'quota guard: off at 97000 of 95000' } });
		assert.ok(calls.every((c) => c.auth === 'Bearer t'));
	});

	test('the live deployment message is read and logged', async () => {
		const { fetchImpl } = recorded(answers(10));
		const report = await reconcile({ env: { CF_GUARD_TOKEN: 't', THRESHOLD: '95000', MODE: 'dry-run' }, fetchImpl, now: NOW });
		assert.match(report.lines[0], /live v-full-2 \(full-200-1, deployed with "full half of 200-1"\)/);
	});

	test('a GraphQL error never reads as an empty day: nothing is written', async () => {
		const table = answers(0);
		table['POST /graphql'] = { errors: [{ message: 'not authorized' }] };
		const { calls, fetchImpl } = recorded(table);
		const report = await reconcile({ env: { CF_GUARD_TOKEN: 't', THRESHOLD: '95000', MODE: 'auto' }, fetchImpl, now: NOW });
		assert.equal(report.error !== undefined, true);
		assert.equal(calls.filter((c) => c.method === 'PATCH' || (c.method === 'POST' && c.path !== '/graphql')).length, 0);
	});
});

describe('quota-switch.mjs', async () => {
	const { runQuotaSwitch } = await import('../scripts/quota-switch.mjs');

	test('dry-run by default: reads, writes nothing', async () => {
		const { calls, fetchImpl } = recorded(answers(97000));
		const sink = { log: [] };
		assert.equal(await runQuotaSwitch({ argv: [], env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl, now: NOW, sink }), 0);
		assert.ok(calls.every((c) => c.method === 'GET' || c.path === '/graphql'));
		assert.match(sink.log.join('\n'), /would turn the rule on/);
	});

	test('off switches now, whatever the count, and says it was done by hand', async () => {
		const { calls, fetchImpl } = recorded(answers(5));
		assert.equal(await runQuotaSwitch({ argv: ['--mode', 'off'], env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl, now: NOW, sink: { log: [] } }), 0);
		assert.equal(calls.filter((c) => c.method === 'PATCH').length, 1);
		const deploy = calls.find((c) => c.method === 'POST' && c.path.endsWith('/deployments'));
		assert.equal(deploy.body.annotations['workers/message'], 'quota switch by hand: off at 5 of 95000');
	});

	test('auto by hand is the guard deciding: its deploy carries the guard mark', async () => {
		const { calls, fetchImpl } = recorded(answers(97000));
		assert.equal(await runQuotaSwitch({ argv: ['--mode', 'auto'], env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl, now: NOW, sink: { log: [] } }), 0);
		const deploy = calls.find((c) => c.method === 'POST' && c.path.endsWith('/deployments'));
		assert.equal(deploy.body.annotations['workers/message'], 'quota guard: off at 97000 of 95000');
	});

	test('usage errors make no call', async () => {
		const { calls, fetchImpl } = recorded({});
		assert.equal(await runQuotaSwitch({ argv: ['--mode', 'maybe'], env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl, sink: { log: [] } }), 2);
		assert.equal(await runQuotaSwitch({ argv: [], env: {}, fetchImpl, sink: { log: [] } }), 2);
		assert.equal(calls.length, 0);
	});
});
