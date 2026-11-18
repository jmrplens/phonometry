// What a deploy reads of the quota guard before it goes live
// (scripts/guard-state.mjs): the live deployment's mark and, when the token
// can read it, the WAF rule.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { guardState, liveMessage, runGuardState } from '../scripts/guard-state.mjs';

const A = '4dbfb3b955a0c856bfe066f2a6061dd5';
const Z = '594554a63737deee229566971a765fd4';

describe('guardState', () => {
	test('the guard\'s off deploy, a hand switch off, the rule on, and everything on', () => {
		assert.deepEqual(guardState({ message: 'quota guard: off at 95012 of 95000', rule: 'unknown' }), { tripped: true, mark: 'quota guard', rule: 'unknown' });
		assert.deepEqual(guardState({ message: 'quota switch by hand: off at 7 of 95000', rule: 'unknown' }), { tripped: true, mark: 'quota switch by hand', rule: 'unknown' });
		assert.deepEqual(guardState({ message: 'quota guard: on at 3 of 95000', rule: 'off' }), { tripped: false, mark: 'quota switch by hand', rule: 'off' });
		assert.deepEqual(guardState({ message: '', rule: 'unknown' }), { tripped: false, mark: 'quota switch by hand', rule: 'unknown' });
	});

	test('the rule on above a deployment the guard did not mark: kept off as a hand switch, never under the guard mark', () => {
		assert.deepEqual(guardState({ message: 'full half of 200-1', rule: 'on' }), { tripped: true, mark: 'quota switch by hand', rule: 'on' });
		assert.deepEqual(guardState({ message: 'rollback', rule: 'on' }), { tripped: true, mark: 'quota switch by hand', rule: 'on' });
		assert.deepEqual(guardState({ message: '', rule: 'on' }), { tripped: true, mark: 'quota switch by hand', rule: 'on' });
	});
});

describe('liveMessage', () => {
	test('the message of the first deployment, empty when it has none', () => {
		assert.equal(liveMessage({ deployments: [{ annotations: { 'workers/message': 'quota guard: off at 1 of 2' } }, { annotations: { 'workers/message': 'older' } }] }), 'quota guard: off at 1 of 2');
		assert.equal(liveMessage({ deployments: [{ annotations: {} }] }), '');
		assert.equal(liveMessage({ deployments: [{}] }), '');
	});

	test('an answer that is not a list of deployments is refused, never read as no message', () => {
		for (const bad of [null, undefined, [], 'x', 3, {}, { deployments: null }, { deployments: {} }, { deployments: [] }, { deployments: [null] }, { deployments: ['d'] }, { deployments: [{ annotations: { 'workers/message': 7 } }] }]) {
			assert.throws(() => liveMessage(bad), Error, JSON.stringify(bad));
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
		assert.deepEqual(out, ['tripped=true', 'mark=quota guard', 'rule=unknown']);
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
