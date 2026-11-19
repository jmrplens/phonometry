// The deploy's beacon check (scripts/check-beacon.mjs): the answer a POST of
// /_v must give follows the live deployment read just before and just after
// the probe, not a state read before the deploy.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { basePath } from '../../src/data/site.mjs';
import { BODY, beaconFits, runCheckBeacon } from '../scripts/check-beacon.mjs';

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
	const statuses = Array.isArray(status) ? status : [status];
	const calls = { reads: 0, beacon: [], zone: 0 };
	const fetchImpl = async (url, init = {}) => {
		const text = String(url);
		if (text === 'https://phonometry.dev/_v') {
			calls.beacon.push({ method: init.method, headers: init.headers, body: init.body });
			return new Response(null, { status: statuses[Math.min(calls.beacon.length - 1, statuses.length - 1)] });
		}
		const path = text.replace('https://api.cloudflare.com/client/v4', '').split('?')[0];
		if (path === DEPLOYMENTS) {
			const list = lists[Math.min(calls.reads, lists.length - 1)];
			calls.reads += 1;
			return new Response(JSON.stringify({ success: true, result: { deployments: list } }), { status: 200 });
		}
		calls.zone += 1;
		// A token that reads the WAF: the rule is on.
		return new Response(JSON.stringify({ success: true, result: { id: 'rs', rules: [{ ref: 'quota-guard-beacon', enabled: true }] } }), { status: 200 });
	};
	return { calls, fetchImpl };
}

const dep = (id, message) => [{ id, annotations: { 'workers/message': message }, versions: [{ version_id: 'v', percentage: 100 }] }];
const FULL = dep('d1', 'full half of 300-1');
const OFF = dep('d2', 'quota guard: off at 95100 of 95000');
const env = { CLOUDFLARE_API_TOKEN: 't' };
const pauses = [];
const run = (options) => runCheckBeacon({ env, sink: { log: [] }, pause: async (ms) => pauses.push(ms), ...options });

describe('check-beacon.mjs', () => {
	test('full code live and 204: passes, with the page view the deploy checks have always sent', async () => {
		const { calls, fetchImpl } = site([FULL], 204);
		const sink = { log: [] };
		assert.equal(await run({ fetchImpl, sink }), 0);
		assert.equal(calls.beacon.length, 1);
		assert.equal(calls.beacon[0].method, 'POST');
		assert.equal(calls.beacon[0].headers.origin, 'https://phonometry.dev');
		assert.equal(calls.beacon[0].body, BODY);
		// The page view lands on a page of the site as served, under its base path.
		const view = JSON.parse(BODY);
		assert.ok(view.p.startsWith(`${basePath}/`), view.p);
		assert.deepEqual(view, { p: `${basePath}/signals/`, wd: 1 });
		assert.match(sink.log.join('\n'), /ok {3}the beacon answers 204/);
	});

	test('full code live and 403 on every attempt: fails (a rule left on above code that should log), whatever the token reads of the WAF', async () => {
		const { calls, fetchImpl } = site([FULL], 403);
		const sink = { log: [] };
		assert.equal(await run({ fetchImpl, sink }), 1);
		assert.equal(calls.beacon.length, 3);
		assert.equal(calls.zone, 0, 'the WAF rule is never read: the deployment alone sets the answer');
		assert.match(sink.log.join('\n'), /::error::the beacon answered 403, not 204 .*\(3 attempts\)/);
	});

	test('a new deployment not yet everywhere: a 404 then a 204 passes after a pause', async () => {
		pauses.length = 0;
		const { calls, fetchImpl } = site([FULL], [404, 204]);
		assert.equal(await run({ fetchImpl }), 0);
		assert.equal(calls.beacon.length, 2);
		assert.deepEqual(pauses, [5000]);
	});

	test('held off: 403 or 404 passes, 204 fails', async () => {
		for (const [status, code] of [[403, 0], [404, 0], [204, 1]]) {
			const { fetchImpl } = site([OFF], status);
			assert.equal(await run({ fetchImpl }), code, String(status));
		}
	});

	test('the guard switched back on after the deploy: the live state decides, so 204 passes', async () => {
		const { fetchImpl } = site([FULL], 204);
		assert.equal(await run({ fetchImpl }), 0);
	});

	test('the live deployment changed during the probe: probed again with the new state', async () => {
		const { calls, fetchImpl } = site([FULL, OFF, OFF, OFF], 403);
		const sink = { log: [] };
		assert.equal(await run({ fetchImpl, sink }), 0);
		assert.equal(calls.beacon.length, 2);
		assert.match(sink.log.join('\n'), /changed during the probe/);
	});

	test('a deployment changing on every attempt fails, never passes on a guess', async () => {
		const { fetchImpl } = site([FULL, OFF, FULL, OFF, FULL, OFF], 204);
		assert.equal(await run({ fetchImpl, attempts: 3 }), 1);
	});

	test('a deployment that cannot be read fails, and no credential is a usage error', async () => {
		const fetchImpl = async () => new Response('{}', { status: 500 });
		assert.equal(await run({ fetchImpl }), 1);
		assert.equal(await run({ env: {}, fetchImpl: () => assert.fail('called') }), 2);
	});
});
