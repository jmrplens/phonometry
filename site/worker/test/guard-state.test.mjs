// What a deploy reads of the quota guard before it goes live
// (scripts/guard-state.mjs): the live deployment's mark and, when the token
// can read it, the WAF rule.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { guardState, runGuardState } from '../scripts/guard-state.mjs';

const A = '4dbfb3b955a0c856bfe066f2a6061dd5';
const Z = '594554a63737deee229566971a765fd4';

describe('guardState', () => {
	test('the guard\'s off deploy, a hand switch off, the rule on, and everything on', () => {
		assert.deepEqual(guardState({ message: 'quota guard: off at 95012 of 95000', rule: 'unknown' }), { tripped: true, mark: 'quota guard', rule: 'unknown' });
		assert.deepEqual(guardState({ message: 'quota switch by hand: off at 7 of 95000', rule: 'unknown' }), { tripped: true, mark: 'quota switch by hand', rule: 'unknown' });
		assert.deepEqual(guardState({ message: 'full half of 200-1', rule: 'on' }), { tripped: true, mark: 'quota guard', rule: 'on' });
		assert.deepEqual(guardState({ message: 'quota guard: on at 3 of 95000', rule: 'off' }), { tripped: false, mark: 'quota guard', rule: 'off' });
		assert.deepEqual(guardState({ message: '', rule: 'unknown' }), { tripped: false, mark: 'quota guard', rule: 'unknown' });
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

	test('a deployment that cannot be read stops the deploy', async () => {
		const sink = { log: [] };
		assert.equal(await runGuardState({ env: { CLOUDFLARE_API_TOKEN: 't' }, fetchImpl: recorded({}), sink }), 1);
		assert.ok(!sink.log.some((line) => line.startsWith('tripped=')));
	});

	test('no credential: usage error, no call', async () => {
		assert.equal(await runGuardState({ env: {}, fetchImpl: () => assert.fail('called'), sink: { log: [] } }), 2);
	});
});
