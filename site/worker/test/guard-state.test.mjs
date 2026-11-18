// What a deploy reads of the quota guard before it goes live
// (scripts/guard-state.mjs): the live deployment's mark and, when the token
// can read it, the WAF rule.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { guardState, liveDeployment, runGuardState, switchedDuring } from '../scripts/guard-state.mjs';

const A = '4dbfb3b955a0c856bfe066f2a6061dd5';
const Z = '594554a63737deee229566971a765fd4';

describe('guardState', () => {
	test('the guard\'s off deploy, a hand switch off, the rule on, and everything on', () => {
		assert.deepEqual(guardState({ message: 'quota guard: off at 95012 of 95000', rule: 'unknown' }), { tripped: true, mark: 'quota guard', rule: 'unknown' });
		assert.deepEqual(guardState({ message: 'quota switch by hand: off at 7 of 95000', rule: 'unknown' }), { tripped: true, mark: 'quota switch by hand', rule: 'unknown' });
		assert.deepEqual(guardState({ message: '', rule: 'unknown' }), { tripped: false, mark: '', rule: 'unknown' });
		assert.deepEqual(guardState({ message: 'full half of 200-1', rule: 'off' }), { tripped: false, mark: '', rule: 'off' });
	});

	test('a reset the guard has not finished: not held off, and the guard mark is carried so its next run still owns the rule', () => {
		for (const rule of ['on', 'off', 'unknown']) {
			assert.deepEqual(guardState({ message: 'quota guard: on at 3 of 95000', rule }), { tripped: false, mark: 'quota guard', rule });
		}
	});

	test('the rule on above a deployment the guard did not mark: kept off as a hand switch, never under the guard mark', () => {
		assert.deepEqual(guardState({ message: 'full half of 200-1', rule: 'on' }), { tripped: true, mark: 'quota switch by hand', rule: 'on' });
		assert.deepEqual(guardState({ message: 'rollback', rule: 'on' }), { tripped: true, mark: 'quota switch by hand', rule: 'on' });
		assert.deepEqual(guardState({ message: '', rule: 'on' }), { tripped: true, mark: 'quota switch by hand', rule: 'on' });
	});
});

describe('liveDeployment', () => {
	test('the id and message of the first deployment, the message empty when it has none', () => {
		assert.deepEqual(liveDeployment({ deployments: [{ id: 'd2', annotations: { 'workers/message': 'quota guard: off at 1 of 2' } }, { id: 'd1', annotations: { 'workers/message': 'older' } }] }), { id: 'd2', message: 'quota guard: off at 1 of 2' });
		assert.equal(liveDeployment({ deployments: [{ id: 'd', annotations: {} }] }).message, '');
		assert.equal(liveDeployment({ deployments: [{ id: 'd' }] }).message, '');
	});

	test('an answer that is not a list of deployments is refused, never read as no message', () => {
		for (const bad of [null, undefined, [], 'x', 3, {}, { deployments: null }, { deployments: {} }, { deployments: [] }, { deployments: [null] }, { deployments: ['d'] }, { deployments: [{ id: 'd', annotations: { 'workers/message': 7 } }] }, { deployments: [{ annotations: {} }] }, { deployments: [{ id: 'd' }, { id: 7 }] }]) {
			assert.throws(() => liveDeployment(bad), Error, JSON.stringify(bad));
		}
	});
});

/** A fetch answering from a table; anything else is refused the way a token without the scope is. */
function recorded(table) {
	return async (url) => {
		const path = String(url).replace('https://api.cloudflare.com/client/v4', '').split('?')[0];
		const answer = table[path];
		if (!answer) return new Response(JSON.stringify({ success: false, errors: [{ code: 10000, message: 'Authentication error' }] }), { status: 403 });
		return new Response(JSON.stringify(answer), { status: 200 });
	};
}

const deployments = (message) => ({ [`/accounts/${A}/workers/scripts/phonometry-docs/deployments`]: { success: true, result: { deployments: [{ id: 'd', annotations: message ? { 'workers/message': message } : {}, versions: [{ version_id: 'v', percentage: 100 }] }] } } });

describe('guard-state.mjs', () => {
	test('the deploy token cannot read the WAF: the deployment decides, and the lines are for $GITHUB_OUTPUT', async () => {
		const sink = { log: [] };
		assert.equal(await runGuardState({ env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl: recorded(deployments('quota guard: off at 96000 of 95000')), sink }), 0);
		const out = sink.log.filter((line) => /^[a-z]+=/.test(line));
		assert.deepEqual(out, ['tripped=true', 'mark=quota guard', 'rule=unknown', 'deployment=d']);
	});

	test('a token that reads the rule: on counts as off even under a CI deploy', async () => {
		const table = { ...deployments('full half of 200-1'), [`/zones/${Z}/rulesets/phases/http_request_firewall_custom/entrypoint`]: { success: true, result: { id: 'rs', rules: [{ ref: 'quota-guard-beacon', enabled: true }] } } };
		const sink = { log: [] };
		assert.equal(await runGuardState({ env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl: recorded(table), sink }), 0);
		assert.ok(sink.log.includes('tripped=true'));
		assert.ok(sink.log.includes('rule=on'));
	});

	test('a 200 whose result is not a list of deployments stops the deploy', async () => {
		const table = { [`/accounts/${A}/workers/scripts/phonometry-docs/deployments`]: { success: true, result: null } };
		const sink = { log: [] };
		assert.equal(await runGuardState({ env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl: recorded(table), sink }), 1);
		assert.ok(!sink.log.some((line) => line.startsWith('tripped=')));
	});

	test('a deployment that cannot be read stops the deploy', async () => {
		const sink = { log: [] };
		assert.equal(await runGuardState({ env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl: recorded({}), sink }), 1);
		assert.ok(!sink.log.some((line) => line.startsWith('tripped=')));
	});

	test('no credential: usage error, no call', async () => {
		assert.equal(await runGuardState({ env: {}, fetchImpl: () => assert.fail('called'), sink: { log: [] } }), 2);
	});
});

// Between the read and the deploy the guard, or quota-switch.mjs, may switch:
// the deploy then follows what that switch left, read from the deployments
// made since the read (newest first, as the API lists them).
const dep = (id, message) => ({ id, annotations: message ? { 'workers/message': message } : {}, versions: [{ version_id: `v-${id}`, percentage: 100 }] });

describe('switchedDuring', () => {
	const read = 'd0';
	test('the guard switched off during the deploy: its off state, under its mark', () => {
		const listed = { deployments: [dep('d2', 'full half of 300-1'), dep('d1', 'quota guard: off at 95100 of 95000'), dep(read, 'full half of 299-1')] };
		assert.deepEqual(switchedDuring(listed, { since: read, pair: '300-1' }), { tripped: true, mark: 'quota guard', rule: 'unknown' });
	});

	test('a hand switch off during the deploy: kept under the hand mark', () => {
		const listed = { deployments: [dep('d2', 'full half of 300-1'), dep('d1', 'quota switch by hand: off at 7 of 95000'), dep(read, '')] };
		assert.deepEqual(switchedDuring(listed, { since: read, pair: '300-1' }), { tripped: true, mark: 'quota switch by hand', rule: 'unknown' });
	});

	test('the guard switched back on during a deploy held off: on, with the guard mark carried', () => {
		const listed = { deployments: [dep('d2', 'quota guard: off, deploy of 300-1 while the code paths are off'), dep('d1', 'quota guard: on at 4 of 95000'), dep(read, 'quota guard: off at 95100 of 95000')] };
		assert.deepEqual(switchedDuring(listed, { since: read, pair: '300-1' }), { tripped: false, mark: 'quota guard', rule: 'unknown' });
	});

	test('nothing between the read and this deploy, or a deployment after it: null, nothing to follow', () => {
		assert.equal(switchedDuring({ deployments: [dep('d2', 'full half of 300-1'), dep(read, '')] }, { since: read, pair: '300-1' }), null);
		assert.equal(switchedDuring({ deployments: [dep('d3', 'quota guard: off at 95100 of 95000'), dep('d2', 'full half of 300-1'), dep(read, '')] }, { since: read, pair: '300-1' }), null);
		assert.equal(switchedDuring({ deployments: [dep('d2', 'full half of 300-10'), dep('d1', 'quota guard: off at 95100 of 95000'), dep(read, '')] }, { since: read, pair: '300-1' }), null, 'another pair is not this deploy');
	});

	test('a read deployment no longer listed is an error, never read as nothing switched', () => {
		assert.throws(() => switchedDuring({ deployments: [dep('d2', 'full half of 300-1')] }, { since: read, pair: '300-1' }), /d0/);
	});
});

describe('guard-state.mjs --since', () => {
	test('prints whether a switch happened during the deploy and the state to follow', async () => {
		const table = { [`/accounts/${A}/workers/scripts/phonometry-docs/deployments`]: { success: true, result: { deployments: [dep('d2', 'full half of 300-1'), dep('d1', 'quota guard: off at 95100 of 95000'), dep('d0', '')] } } };
		const sink = { log: [] };
		assert.equal(await runGuardState({ argv: ['--since', 'd0', '--pair', '300-1'], env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl: recorded(table), sink }), 0);
		assert.deepEqual(sink.log.filter((line) => /^[a-z]+=/.test(line)), ['switched=true', 'tripped=true', 'mark=quota guard']);
	});

	test('nothing switched: switched=false alone', async () => {
		const table = { [`/accounts/${A}/workers/scripts/phonometry-docs/deployments`]: { success: true, result: { deployments: [dep('d2', 'full half of 300-1'), dep('d0', '')] } } };
		const sink = { log: [] };
		assert.equal(await runGuardState({ argv: ['--since', 'd0', '--pair', '300-1'], env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl: recorded(table), sink }), 0);
		assert.deepEqual(sink.log.filter((line) => /^[a-z]+=/.test(line)), ['switched=false']);
	});

	test('--since without --pair, or a read deployment not listed: no state printed', async () => {
		const table = { [`/accounts/${A}/workers/scripts/phonometry-docs/deployments`]: { success: true, result: { deployments: [dep('d2', 'full half of 300-1')] } } };
		const sink = { log: [] };
		assert.equal(await runGuardState({ argv: ['--since', 'd0'], env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl: recorded(table), sink }), 2);
		assert.equal(await runGuardState({ argv: ['--since', 'd0', '--pair', '300-1'], env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl: recorded(table), sink }), 1);
		assert.ok(!sink.log.some((line) => /^(switched|tripped)=/.test(line)));
	});
});
