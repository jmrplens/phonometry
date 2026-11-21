// What runs code, and for which requests.
//
// Pages, _astro, media and every other file are plain assets: they run no
// script, so the daily quota of Workers Free cannot stop them. The Worker runs
// only for the beacon (lib/worker-paths.mjs), and writes one data point for
// each; everything else a Worker could bind
// (storage, queues, services, triggers) fails here until it is added on
// purpose. wrangler.assets-only.jsonc is the same Worker with the code taken
// out, which the quota guard rolls to at 95 % of the day; it is derived from
// the full one here, so the two cannot drift. The guard itself is a Worker of
// its own with a Cron Trigger and no route.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

import { WORKER_PATHS } from '../lib/worker-paths.mjs';
import { ACCOUNT_ID } from '../lib/cloudflare.mjs';

/** A wrangler config without its comments and trailing commas. */
export function readConfig(name) {
	const text = readFileSync(new URL(`../${name}`, import.meta.url), 'utf8');
	const stripped = text
		.replace(/("(?:[^"\\]|\\.)*")|\/\/[^\n]*|\/\*[\s\S]*?\*\//g, (_match, string) => string ?? '')
		.replace(/,(\s*[}\]])/g, '$1');
	return JSON.parse(stripped);
}

/** Keys that put a binding or a trigger on the Worker; each is either listed as wanted below or absent. */
const CODE_KEYS = [
	'durable_objects',
	'kv_namespaces',
	'r2_buckets',
	'd1_databases',
	'services',
	'queues',
	'ai',
	'browser',
	'vectorize',
	'hyperdrive',
	'workflows',
	'tail_consumers',
	'triggers',
	'vars',
	'secrets_store_secrets',
	'send_email',
	'dispatch_namespaces',
	'mtls_certificates',
	'unsafe',
];

/** What the full Worker has that the assets-only one does not. */
const CODE_ONLY = ['main', 'analytics_engine_datasets', 'ratelimits'];

test('the full Worker: one script, the assets, one dataset, one limiter, nothing else', () => {
	const config = readConfig('wrangler.jsonc');
	assert.equal(config.main, 'src/index.mjs');
	assert.deepEqual(config.analytics_engine_datasets, [{ binding: 'REQS', dataset: 'phonometry_dev_requests' }]);
	assert.deepEqual(config.ratelimits, [{ name: 'PER_IP', namespace_id: '3001', simple: { limit: 30, period: 60 } }]);
	for (const key of CODE_KEYS) assert.equal(key in config, false, `wrangler.jsonc sets ${key}`);
	assert.equal(config.assets.binding, 'ASSETS');
});

test('the Worker runs only for the beacon', () => {
	assert.deepEqual(readConfig('wrangler.jsonc').assets.run_worker_first, [...WORKER_PATHS]);
});

test('the assets are the staged build, served as a static site, on phonometry.dev only', () => {
	const { name, assets, routes, workers_dev: workersDev, preview_urls: previewUrls, observability } = readConfig('wrangler.jsonc');
	assert.equal(name, 'phonometry-docs');
	assert.deepEqual({ ...assets, binding: undefined, run_worker_first: undefined }, { directory: './stage', html_handling: 'auto-trailing-slash', not_found_handling: '404-page', binding: undefined, run_worker_first: undefined });
	assert.deepEqual(routes, [{ pattern: 'phonometry.dev', custom_domain: true }]);
	assert.equal(workersDev, false);
	assert.equal(previewUrls, false);
	assert.deepEqual(observability, { enabled: false });
});

test('the assets-only Worker is the full one with the code taken out', () => {
	const full = readConfig('wrangler.jsonc');
	const expected = structuredClone(full);
	for (const key of CODE_ONLY) delete expected[key];
	delete expected.assets.binding;
	delete expected.assets.run_worker_first;
	assert.deepEqual(readConfig('wrangler.assets-only.jsonc'), expected);
});

test('the accounts are pinned, so the ambient CLOUDFLARE_ACCOUNT_ID cannot pick another one', () => {
	for (const name of ['wrangler.jsonc', 'wrangler.assets-only.jsonc', 'guard/wrangler.jsonc']) {
		assert.equal(readConfig(name).account_id, '4dbfb3b955a0c856bfe066f2a6061dd5', name);
		assert.equal(readConfig(name).account_id, ACCOUNT_ID, name);
	}
});

test('the guard: a cron every 15 minutes, no route, no binding, dry run until told otherwise', () => {
	const guard = readConfig('guard/wrangler.jsonc');
	assert.equal(guard.name, 'phonometry-quota-guard');
	assert.equal(guard.main, 'src/index.mjs');
	assert.deepEqual(guard.triggers, { crons: ['*/15 * * * *'] });
	assert.equal('routes' in guard || 'route' in guard, false);
	assert.equal(guard.workers_dev, false);
	assert.equal(guard.preview_urls, false);
	assert.deepEqual(guard.vars, { THRESHOLD: '95000', MODE: 'dry-run' });
	for (const key of [...CODE_KEYS.filter((key) => key !== 'triggers' && key !== 'vars'), 'assets', 'analytics_engine_datasets', 'ratelimits']) assert.equal(key in guard, false, `guard sets ${key}`);
});
