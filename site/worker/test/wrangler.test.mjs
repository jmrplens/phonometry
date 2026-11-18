// The Worker runs no code, which is what makes it fail open: a request that
// runs no script cannot be stopped by the daily quota of Workers Free. This
// holds wrangler.jsonc to that, so adding a script, a binding or
// run_worker_first fails here until the change is made on purpose.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

import { ACCOUNT_ID } from '../lib/cloudflare.mjs';

/** wrangler.jsonc without its comments and trailing commas. */
function readConfig() {
	const text = readFileSync(new URL('../wrangler.jsonc', import.meta.url), 'utf8');
	const stripped = text
		.replace(/("(?:[^"\\]|\\.)*")|\/\/[^\n]*|\/\*[\s\S]*?\*\//g, (_match, string) => string ?? '')
		.replace(/,(\s*[}\]])/g, '$1');
	return JSON.parse(stripped);
}

/** Keys that put a script or a binding on the request path. */
const CODE_KEYS = [
	'main',
	'durable_objects',
	'kv_namespaces',
	'r2_buckets',
	'd1_databases',
	'services',
	'analytics_engine_datasets',
	'queues',
	'ai',
	'browser',
	'vectorize',
	'hyperdrive',
	'workflows',
	'tail_consumers',
	'triggers',
];

test('no script, no binding, no run_worker_first', () => {
	const config = readConfig();
	for (const key of CODE_KEYS) assert.equal(key in config, false, `wrangler.jsonc sets ${key}`);
	assert.equal('run_worker_first' in config.assets, false);
	assert.equal('binding' in config.assets, false);
});

test('the assets are the staged build, served as a static site', () => {
	const { name, assets, routes, workers_dev: workersDev, preview_urls: previewUrls } = readConfig();
	assert.equal(name, 'phonometry-docs');
	assert.deepEqual(assets, { directory: './stage', html_handling: 'auto-trailing-slash', not_found_handling: '404-page' });
	assert.deepEqual(routes, [{ pattern: 'phonometry.dev', custom_domain: true }]);
	assert.equal(workersDev, false);
	assert.equal(previewUrls, false);
});

test('the account is pinned, so the ambient CLOUDFLARE_ACCOUNT_ID cannot pick another one', () => {
	assert.equal(readConfig().account_id, '4dbfb3b955a0c856bfe066f2a6061dd5');
	assert.equal(readConfig().account_id, ACCOUNT_ID);
});
