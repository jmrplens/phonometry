// The deploy's beacon check (scripts/check-beacon.mjs): the answer a POST of
// /_v must give follows the live deployment read just before and just after
// the probe, not a state read before the deploy.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { beaconFits, runCheckBeacon } from '../scripts/check-beacon.mjs';

const A = '4dbfb3b955a0c856bfe066f2a6061dd5';
const DEPLOYMENTS = `/accounts/${A}/workers/scripts/phonometry-docs/deployments`;

describe('beaconFits', () => {
	test('on: only 204; held off: the WAF 403 or the assets-only 404, never 204', () => {
		assert.ok(beaconFits(false, 204));
		for (const status of [403, 404, 429, 500]) assert.ok(!beaconFits(false, status), String(status));
		assert.ok(beaconFits(true, 403) && beaconFits(true, 404));
		for (const status of [204, 200, 429, 500]) assert.ok(!beaconFits(true, status), String(status));
	});
});

/**
 * A fetch that answers the API from a sequence of deployment lists (one per
 * read) and the beacon with a fixed status, recording the beacon request.
 */
function site(lists, status) {
	const calls = { reads: 0, beacon: [] };
	const fetchImpl = async (url, init = {}) => {
		const text = String(url);
		if (text === 'https://phonometry.dev/_v') {
			calls.beacon.push({ method: init.method, headers: init.headers, body: init.body });
			return new Response(null, { status });
		}
		const path = text.replace('https://api.cloudflare.com/client/v4', '').split('?')[0];
		if (path === DEPLOYMENTS) {
			const list = lists[Math.min(calls.reads, lists.length - 1)];
			calls.reads += 1;
			return new Response(JSON.stringify({ success: true, result: { deployments: list } }), { status: 200 });
		}
		return new Response(JSON.stringify({ success: false, errors: [{ code: 10000, message: 'Authentication error' }] }), { status: 403 });
	};
	return { calls, fetchImpl };
}

const dep = (id, message) => [{ id, annotations: { 'workers/message': message }, versions: [{ version_id: 'v', percentage: 100 }] }];
const FULL = dep('d1', 'full half of 300-1');
const OFF = dep('d2', 'quota guard: off at 95100 of 95000');
const env = { CLOUDFLARE_API_TOKEN: 't' };

describe('check-beacon.mjs', () => {
	test('full code live and 204: passes, with the page view the deploy checks have always sent', async () => {
		const { calls, fetchImpl } = site([FULL], 204);
		const sink = { log: [] };
		assert.equal(await runCheckBeacon({ env, fetchImpl, sink }), 0);
		assert.equal(calls.beacon.length, 1);
		assert.equal(calls.beacon[0].method, 'POST');
		assert.equal(calls.beacon[0].headers.origin, 'https://phonometry.dev');
		assert.equal(calls.beacon[0].body, '{"p":"/phonometry/signals/","wd":1}');
		assert.match(sink.log.join('\n'), /ok {3}the beacon answers 204/);
	});

	test('full code live and 403: fails (a rule left on above code that should log)', async () => {
		const { fetchImpl } = site([FULL], 403);
		const sink = { log: [] };
		assert.equal(await runCheckBeacon({ env, fetchImpl, sink }), 1);
		assert.match(sink.log.join('\n'), /::error::the beacon answered 403, not 204/);
	});

	test('held off: 403 or 404 passes, 204 fails', async () => {
		for (const [status, code] of [[403, 0], [404, 0], [204, 1]]) {
			const { fetchImpl } = site([OFF], status);
			assert.equal(await runCheckBeacon({ env, fetchImpl, sink: { log: [] } }), code, String(status));
		}
	});

	test('the guard switched back on after the deploy: the live state decides, so 204 passes', async () => {
		const { fetchImpl } = site([FULL], 204);
		assert.equal(await runCheckBeacon({ env, fetchImpl, sink: { log: [] } }), 0);
	});

	test('the live deployment changed during the probe: probed again with the new state', async () => {
		const { calls, fetchImpl } = site([FULL, OFF, OFF, OFF], 403);
		const sink = { log: [] };
		assert.equal(await runCheckBeacon({ env, fetchImpl, sink }), 0);
		assert.equal(calls.beacon.length, 2);
		assert.match(sink.log.join('\n'), /changed during the probe/);
	});

	test('a deployment changing on every attempt fails, never passes on a guess', async () => {
		const { fetchImpl } = site([FULL, OFF, FULL, OFF, FULL, OFF], 204);
		assert.equal(await runCheckBeacon({ env, fetchImpl, sink: { log: [] }, attempts: 3 }), 1);
	});

	test('a deployment that cannot be read fails, and no credential is a usage error', async () => {
		const fetchImpl = async () => new Response('{}', { status: 500 });
		assert.equal(await runCheckBeacon({ env, fetchImpl, sink: { log: [] } }), 1);
		assert.equal(await runCheckBeacon({ env: {}, fetchImpl: () => assert.fail('called'), sink: { log: [] } }), 2);
	});
});
