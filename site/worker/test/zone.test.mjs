// The zone plan, the rule drift, and the two scripts that apply them, run
// against recorded API answers (the empty zone of 2026-11-17 and cases made
// to disagree with it). No request leaves the process.
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, test } from 'node:test';

import { redirectRules, responseHeaderRules } from '../lib/rules.mjs';
import { ruleDrift } from '../lib/rulesets.mjs';
import { twinExclusions } from '../lib/twins.mjs';
import { DNS_RECORDS, ZONE_SETTINGS, zonePlan } from '../lib/zone.mjs';
import { runApplyRules } from '../scripts/apply-rules.mjs';
import { runApplyZone } from '../scripts/apply-zone.mjs';

const zone = 'phonometry.dev';
/** The settings as the zone read on 2026-11-17. */
const MEASURED = {
	email_obfuscation: 'on',
	automatic_https_rewrites: 'on',
	always_use_https: 'off',
	min_tls_version: '1.0',
	security_header: { strict_transport_security: { enabled: false, max_age: 0, include_subdomains: false, preload: false, nosniff: false } },
};

describe('zonePlan', () => {
	test('the empty zone of 2026-11-17: every record created, every setting changed', () => {
		const plan = zonePlan({ zone, records: [], settings: MEASURED });
		assert.deepEqual(plan.create.map(({ type, name }) => `${type} ${name}`), [
			'AAAA www.phonometry.dev',
			'MX phonometry.dev',
			'TXT phonometry.dev',
			'TXT _dmarc.phonometry.dev',
			'TXT *._domainkey.phonometry.dev',
		]);
		assert.deepEqual(plan.settings.map(({ id }) => id), Object.keys(ZONE_SETTINGS));
		assert.deepEqual(plan.conflicts, []);
		assert.ok(plan.create.every(({ ttl }) => ttl === 1));
	});

	test('a zone already in place: nothing to do', () => {
		const records = DNS_RECORDS.map((r, i) => ({ id: `r${i}`, ...r, name: r.name === '@' ? zone : `${r.name}.${zone}` }));
		const plan = zonePlan({ zone, records, settings: { ...ZONE_SETTINGS } });
		assert.deepEqual(plan.create, []);
		assert.deepEqual(plan.settings, []);
		assert.equal(plan.keep.length, DNS_RECORDS.length);
	});

	test('a record of the maintainer in the same place is reported and left alone', () => {
		const records = [{ id: 'x', type: 'TXT', name: zone, content: '"v=spf1 include:_spf.example -all"', proxied: false }];
		const plan = zonePlan({ zone, records, settings: MEASURED });
		assert.match(plan.conflicts.join('\n'), /TXT phonometry\.dev: holds .*left alone/);
		assert.equal(plan.create.some(({ type, name, content }) => type === 'TXT' && name === zone && content.includes('spf1')), false);
	});

	test('another TXT record at the apex does not stand in the SPF place', () => {
		const records = [{ id: 'g', type: 'TXT', name: zone, content: '"google-site-verification=abc"', proxied: false }];
		const plan = zonePlan({ zone, records, settings: MEASURED });
		assert.ok(plan.create.some(({ type, name }) => type === 'TXT' && name === zone));
		assert.deepEqual(plan.conflicts, []);
	});

	test('HSTS on but without preload is still a change', () => {
		const settings = { ...ZONE_SETTINGS, security_header: { strict_transport_security: { ...ZONE_SETTINGS.security_header.strict_transport_security, preload: false } } };
		assert.deepEqual(zonePlan({ zone, records: [], settings }).settings.map(({ id }) => id), ['security_header']);
	});
});

describe('ruleDrift', () => {
	const wanted = redirectRules({ host: zone, prefix: '/phonometry', exclusions: twinExclusions('/phonometry'), clipBase: 'https://docs.jmrp.io/phonometry/media/' });
	const live = wanted.map((rule, i) => ({ ...rule, id: `id${i}`, version: '1', last_updated: '2026-11-17T00:00:00Z' }));

	test('the same rules with Cloudflare ids and dates: no drift', () => {
		assert.deepEqual(ruleDrift(live, wanted), []);
	});

	test('an empty entrypoint: every rule missing', () => {
		assert.deepEqual(ruleDrift([], wanted), wanted.map(({ ref }) => `${ref}: missing`));
	});

	test('an edited expression, a rule nobody generated, and a new order', () => {
		const edited = live.map((rule) => (rule.ref === 'markdown-twin' ? { ...rule, expression: 'true' } : rule));
		assert.match(ruleDrift(edited, wanted).join('\n'), /markdown-twin: expression is "true"/);
		assert.match(ruleDrift([...live, { id: 'z', ref: 'by-hand' }], wanted).join('\n'), /by-hand: not generated here/);
		assert.match(ruleDrift([...live].reverse(), wanted).join('\n'), /^order is markdown-twin/);
	});
});

/** A recorded API: answers by method and path, and keeps every call. */
function api(routes) {
	const calls = [];
	const fetchImpl = async (url, init = {}) => {
		const path = url.replace('https://api.cloudflare.com/client/v4', '');
		const method = init.method ?? 'GET';
		calls.push({ method, path, body: init.body ? JSON.parse(init.body) : undefined, headers: init.headers });
		const route = routes[`${method} ${path.split('?')[0]}`];
		const [status, body] = typeof route === 'function' ? route(init) : (route ?? [404, { success: false, errors: [{ code: 10003, message: 'not found' }] }]);
		return new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
	};
	return { calls, fetchImpl };
}
const ok = (result) => [200, { success: true, errors: [], messages: [], result }];
const env = { CLOUDFLARE_API_TOKEN: 'secret-token', CLOUDFLARE_ZONE_ID: 'zone1' };
const sinkOf = () => ({ log: [] });

describe('apply-rules', () => {
	const phases = ['http_request_dynamic_redirect', 'http_response_headers_transform'];

	test('--check on the empty zone fails and changes nothing', async () => {
		const { calls, fetchImpl } = api({});
		const sink = sinkOf();
		assert.equal(await runApplyRules({ argv: [], env, fetchImpl, sink }), 1);
		assert.deepEqual(calls.map(({ method }) => method), ['GET', 'GET']);
		assert.match(sink.log.join('\n'), /markdown-twin: missing/);
	});

	test('--apply saves what was there, then puts the generated rules in both entrypoints', async () => {
		const dir = mkdtempSync(join(tmpdir(), 'rules-'));
		try {
			const { calls, fetchImpl } = api({
				[`PUT /zones/zone1/rulesets/phases/${phases[0]}/entrypoint`]: () => ok({ version: '1' }),
				[`PUT /zones/zone1/rulesets/phases/${phases[1]}/entrypoint`]: () => ok({ version: '1' }),
			});
			const code = await runApplyRules({ argv: ['--apply', '--backup-dir', dir], env, fetchImpl, sink: sinkOf() });
			assert.equal(code, 0);
			const puts = calls.filter(({ method }) => method === 'PUT');
			assert.equal(puts.length, 2);
			assert.deepEqual(puts[0].body.rules.map(({ ref }) => ref), ['www-to-apex', 'root-to-base', 'clips-to-range-host', 'markdown-twin']);
			assert.deepEqual(puts[1].body, { rules: responseHeaderRules({ host: zone }) });
			const saved = readdirSync(dir).sort();
			assert.equal(saved.length, 2);
			assert.deepEqual(JSON.parse(readFileSync(join(dir, saved[0]), 'utf8')), { phase: saved[0].includes('dynamic_redirect') ? phases[0] : phases[1], rules: [] });
		} finally {
			rmSync(dir, { recursive: true, force: true });
		}
	});

	test('--check on a zone that holds the generated rules passes', async () => {
		const wanted = redirectRules({ host: zone, prefix: '/phonometry', exclusions: twinExclusions('/phonometry'), clipBase: 'https://docs.jmrp.io/phonometry/media/' });
		const { fetchImpl } = api({
			[`GET /zones/zone1/rulesets/phases/${phases[0]}/entrypoint`]: () => ok({ rules: wanted }),
			[`GET /zones/zone1/rulesets/phases/${phases[1]}/entrypoint`]: () => ok({ rules: responseHeaderRules({ host: zone }) }),
		});
		assert.equal(await runApplyRules({ argv: ['--check'], env, fetchImpl, sink: sinkOf() }), 0);
	});

	test('an API error other than "no entrypoint" stops it', async () => {
		const { fetchImpl } = api({ [`GET /zones/zone1/rulesets/phases/${phases[0]}/entrypoint`]: () => [403, { success: false, errors: [{ code: 10000, message: 'Authentication error' }] }] });
		const sink = sinkOf();
		assert.equal(await runApplyRules({ argv: [], env, fetchImpl, sink }), 1);
		assert.match(sink.log.join('\n'), /HTTP 403: 10000 Authentication error/);
		assert.ok(!sink.log.join('\n').includes('secret-token'));
	});
});

describe('apply-zone', () => {
	const settingsRoutes = Object.fromEntries(Object.entries(MEASURED).map(([id, value]) => [`GET /zones/zone1/settings/${id}`, () => ok({ id, value })]));

	test('a dry run reads, prints the plan and writes nothing', async () => {
		const { calls, fetchImpl } = api({ 'GET /zones/zone1/dns_records': () => [200, { success: true, result: [], result_info: { page: 1, total_pages: 1 } }], ...settingsRoutes });
		const sink = sinkOf();
		assert.equal(await runApplyZone({ argv: [], env, fetchImpl, sink }), 0);
		assert.ok(calls.every(({ method }) => method === 'GET'));
		assert.match(sink.log.join('\n'), /would create MX phonometry\.dev/);
		assert.match(sink.log.join('\n'), /would set email_obfuscation: "on" -> "off"/);
	});

	test('--apply backs up first, then creates and patches', async () => {
		const dir = mkdtempSync(join(tmpdir(), 'zone-'));
		try {
			const { calls, fetchImpl } = api({
				'GET /zones/zone1/dns_records': () => [200, { success: true, result: [], result_info: { page: 1, total_pages: 1 } }],
				...settingsRoutes,
				'POST /zones/zone1/dns_records': (init) => ok({ id: 'new', ...JSON.parse(init.body) }),
				...Object.fromEntries(Object.keys(MEASURED).map((id) => [`PATCH /zones/zone1/settings/${id}`, (init) => ok({ id, ...JSON.parse(init.body) })])),
			});
			assert.equal(await runApplyZone({ argv: ['--apply', '--backup-dir', dir], env, fetchImpl, sink: sinkOf() }), 0);
			const writes = calls.filter(({ method }) => method !== 'GET');
			assert.equal(writes.filter(({ method }) => method === 'POST').length, DNS_RECORDS.length);
			assert.deepEqual(writes.filter(({ method }) => method === 'PATCH').map(({ body }) => body), Object.values(ZONE_SETTINGS).map((value) => ({ value })));
			const [backup] = readdirSync(dir);
			assert.deepEqual(JSON.parse(readFileSync(join(dir, backup), 'utf8')).settings, MEASURED);
		} finally {
			rmSync(dir, { recursive: true, force: true });
		}
	});

	test('a conflict fails the run and is never overwritten', async () => {
		const { calls, fetchImpl } = api({
			'GET /zones/zone1/dns_records': () => [200, { success: true, result: [{ id: 'm', type: 'MX', name: zone, content: 'mx.example', priority: 10, proxied: false }], result_info: { page: 1, total_pages: 1 } }],
			...settingsRoutes,
		});
		const sink = sinkOf();
		assert.equal(await runApplyZone({ argv: [], env, fetchImpl, sink }), 1);
		assert.match(sink.log.join('\n'), /MX phonometry\.dev: holds "mx\.example"/);
		assert.ok(calls.every(({ method }) => method === 'GET'));
	});
});
