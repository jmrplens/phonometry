// The zone's WAF and rate limiting rules for the beacon, and the apply
// script's `--phase waf`, on recorded API answers.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { ZONE_ID } from '../lib/cloudflare.mjs';
import { GUARD_RULE_REF } from '../lib/guard.mjs';
import { firewallRules, rateLimitRules } from '../lib/rules.mjs';
import { ruleDrift } from '../lib/rulesets.mjs';
import { runApplyRules } from '../scripts/apply-rules.mjs';

const host = 'phonometry.dev';

describe('the WAF rules', () => {
	test('beacon-shape blocks anything at /_v but a POST from the site itself, and is on', () => {
		const [shape] = firewallRules({ host });
		assert.equal(shape.ref, 'beacon-shape');
		assert.equal(shape.action, 'block');
		assert.equal(shape.enabled, true);
		assert.equal(
			shape.expression,
			'http.host eq "phonometry.dev" and http.request.uri.path eq "/_v" and (http.request.method ne "POST" or not any(http.request.headers["origin"][*] eq "https://phonometry.dev"))',
		);
	});

	test('the guard rule blocks every request at /_v and is created off', () => {
		const guard = firewallRules({ host })[1];
		assert.equal(guard.ref, GUARD_RULE_REF);
		assert.equal(guard.expression, 'http.host eq "phonometry.dev" and http.request.uri.path eq "/_v"');
		assert.equal(guard.action, 'block');
		assert.equal(guard.enabled, false);
	});

	test('the rate rule: one address, ten beacons in ten seconds, then ten seconds blocked, matched on the path alone (the Free plan’s values and fields)', () => {
		assert.deepEqual(rateLimitRules(), [
			{
				ref: 'beacon-rate',
				description: 'At most 10 beacons in 10 seconds from one address, before any Worker runs',
				expression: 'http.request.uri.path eq "/_v"',
				action: 'block',
				ratelimit: { characteristics: ['cf.colo.id', 'ip.src'], period: 10, requests_per_period: 10, mitigation_timeout: 10 },
				enabled: true,
			},
		]);
	});

	test('a changed rate limit is drift', () => {
		const live = rateLimitRules().map((rule) => ({ ...rule, ratelimit: { ...rule.ratelimit, requests_per_period: 50 } }));
		assert.match(ruleDrift(live, rateLimitRules()).join('\n'), /beacon-rate: ratelimit is/);
	});
});

/** A recorded API: answers by method and path, and keeps every call. */
function api(routes) {
	const calls = [];
	const fetchImpl = async (url, init = {}) => {
		const path = url.replace('https://api.cloudflare.com/client/v4', '');
		const method = init.method ?? 'GET';
		calls.push({ method, path, body: init.body ? JSON.parse(init.body) : undefined });
		const route = routes[`${method} ${path.split('?')[0]}`];
		const [status, body] = typeof route === 'function' ? route(init) : (route ?? [404, { success: false, errors: [{ code: 10003, message: 'not found' }] }]);
		return new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
	};
	return { calls, fetchImpl };
}
const ok = (result) => [200, { success: true, errors: [], messages: [], result }];
const env = { CLOUDFLARE_API_TOKEN: 'secret-token' };
const custom = `/zones/${ZONE_ID}/rulesets/phases/http_request_firewall_custom/entrypoint`;
const rate = `/zones/${ZONE_ID}/rulesets/phases/http_ratelimit/entrypoint`;

describe('apply-rules --phase waf', () => {
	test('reads only the two WAF phases; --check on the empty zone fails', async () => {
		const { calls, fetchImpl } = api({});
		const sink = { log: [] };
		assert.equal(await runApplyRules({ argv: ['--phase', 'waf'], env, fetchImpl, sink }), 1);
		assert.deepEqual(calls.map(({ path }) => path), [custom, rate]);
		assert.match(sink.log.join('\n'), /quota-guard-beacon: missing/);
	});

	test('the default phases stay the two the CI token can read', async () => {
		const { calls, fetchImpl } = api({});
		await runApplyRules({ argv: [], env, fetchImpl, sink: { log: [] } });
		assert.ok(calls.every(({ path }) => !path.includes('firewall') && !path.includes('ratelimit')));
	});

	test('--apply creates the guard rule off, and keeps the value it finds off', async () => {
		const stale = firewallRules({ host }).map((rule) => ({ ...rule, description: `${rule.description} (old)` }));
		for (const liveRules of [[], stale]) {
			const { calls, fetchImpl } = api({
				[`GET ${custom}`]: () => ok({ rules: liveRules }),
				[`PUT ${custom}`]: () => ok({ version: '2' }),
				[`PUT ${rate}`]: () => ok({ version: '1' }),
			});
			const dir = `/tmp/claude-waf-${process.pid}-${liveRules.length}`;
			assert.equal(await runApplyRules({ argv: ['--phase', 'waf', '--apply', '--backup-dir', dir], env, fetchImpl, sink: { log: [] } }), 0);
			const put = calls.find(({ method, path }) => method === 'PUT' && path === custom);
			assert.equal(put.body.rules.find((rule) => rule.ref === GUARD_RULE_REF).enabled, false);
		}
	});

	test('--apply leaves a phase already as generated untouched, so no rule gets a new last update', async () => {
		const tripped = firewallRules({ host }).map((rule) => (rule.ref === GUARD_RULE_REF ? { ...rule, enabled: true } : rule));
		const { calls, fetchImpl } = api({ [`GET ${custom}`]: () => ok({ rules: tripped }), [`GET ${rate}`]: () => ok({ rules: rateLimitRules() }) });
		const sink = { log: [] };
		assert.equal(await runApplyRules({ argv: ['--phase', 'waf', '--apply', '--backup-dir', `/tmp/claude-waf-${process.pid}-same`], env, fetchImpl, sink }), 0);
		assert.deepEqual(calls.filter(({ method }) => method !== 'GET'), []);
		assert.match(sink.log.join('\n'), /http_request_firewall_custom: as generated \(2 rules\), nothing put/);
	});

	test('--apply refuses to rewrite the custom rules while the guard holds its rule on, and still puts the rate rule', async () => {
		const tripped = firewallRules({ host }).map((rule) => (rule.ref === GUARD_RULE_REF ? { ...rule, enabled: true } : { ...rule, description: 'old' }));
		const { calls, fetchImpl } = api({
			[`GET ${custom}`]: () => ok({ rules: tripped }),
			[`PUT ${rate}`]: () => ok({ version: '1' }),
		});
		const sink = { log: [] };
		assert.equal(await runApplyRules({ argv: ['--phase', 'waf', '--apply', '--backup-dir', `/tmp/claude-waf-${process.pid}-held`], env, fetchImpl, sink }), 1);
		assert.deepEqual(calls.filter(({ method }) => method === 'PUT').map(({ path }) => path), [rate]);
		assert.match(sink.log.join('\n'), /not put: the quota guard holds quota-guard-beacon on/);
	});

	test('--check passes while the guard holds its rule on', async () => {
		const liveRules = firewallRules({ host }).map((rule) => (rule.ref === GUARD_RULE_REF ? { ...rule, enabled: true } : rule));
		const { fetchImpl } = api({ [`GET ${custom}`]: () => ok({ rules: liveRules }), [`GET ${rate}`]: () => ok({ rules: rateLimitRules() }) });
		assert.equal(await runApplyRules({ argv: ['--phase', 'waf', '--check'], env, fetchImpl, sink: { log: [] } }), 0);
	});

	test('an unknown phase is a usage error', async () => {
		const { calls, fetchImpl } = api({});
		assert.equal(await runApplyRules({ argv: ['--phase', 'all'], env, fetchImpl, sink: { log: [] } }), 2);
		assert.deepEqual(calls, []);
	});
});
