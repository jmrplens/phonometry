// The deploy's beacon check (site-deploy.yml): a POST of /_v answers what
// the live deployment says it should.
//
// Usage:
//   CLOUDFLARE_API_TOKEN=... node site/worker/scripts/check-beacon.mjs
//
// The answer to expect comes from the live deployment alone, never from the
// WAF rule: a deployment marked off (`quota guard: off` or `quota switch by
// hand: off`) is the assets-only half, held off, and answers the WAF rule's
// 403 or, while that rule is not on yet, 404 (no asset is called _v); any
// other runs full code and answers 204, so a rule left on above it fails the
// check whatever the token can read. The deployment is read just before and
// just after the probe, not before the deploy: the guard runs every 15
// minutes and quota-switch.mjs at any time. A deployment that changed during
// the probe, or an answer that does not fit (a new deployment takes a few
// seconds to reach every Cloudflare location), is probed again after a
// pause, up to three attempts; a mismatch on the last one fails. The probe is
// the page view the deploy checks have always sent (webdriver flag set), so
// it lands in the dataset as one.
// Exit 0 when the answer fits, 1 when it does not or the state could not be
// read, 2 on a usage error.
import { fileURLToPath } from 'node:url';

import { basePath } from '../../src/data/site.mjs';
import { ignoredTargets } from '../lib/cloudflare.mjs';
import { readGuardState } from './guard-state.mjs';

export const BEACON = 'https://phonometry.dev/_v';
const ORIGIN = 'https://phonometry.dev';
/** The page view the probe sends: a page under the base path the deploy stages, from site.mjs. */
export const BODY = JSON.stringify({ p: `${basePath}/signals/`, wd: 1 });

/**
 * Whether a beacon status fits the state.
 *
 * @param {boolean} tripped The code paths are held off.
 * @param {number} status The status the POST answered.
 * @returns {boolean} 204 when on; 403 or 404 when held off.
 */
export function beaconFits(tripped, status) {
	return tripped ? status === 403 || status === 404 : status === 204;
}

/**
 * Runs the check.
 *
 * @param {{env: Record<string, string | undefined>, fetchImpl?: typeof fetch, sink?: {log: string[]}, attempts?: number, pause?: (ms: number) => Promise<void>, pauseMs?: number}} options
 * @returns {Promise<number>} The exit code.
 */
export async function runCheckBeacon({ env, fetchImpl = fetch, sink = null, attempts = 3, pause = (ms) => new Promise((done) => setTimeout(done, ms)), pauseMs = 5000 }) {
	const log = (line) => (sink ? sink.log.push(line) : console.log(line));
	if (!(env.CLOUDFLARE_API_TOKEN || (env.CLOUDFLARE_EMAIL && env.CLOUDFLARE_API_KEY))) {
		log('set CLOUDFLARE_API_TOKEN, or CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY');
		return 2;
	}
	for (const line of ignoredTargets(env)) log(line);
	const warn = (line) => log(line);
	let last = '';
	for (let attempt = 1; attempt <= attempts; attempt += 1) {
		if (attempt > 1) await pause(pauseMs);
		let before;
		let after;
		let status;
		try {
			before = await readGuardState({ env, fetchImpl, warn, readRule: false });
			const response = await fetchImpl(BEACON, { method: 'POST', headers: { origin: ORIGIN, 'content-type': 'text/plain' }, body: BODY, signal: AbortSignal.timeout(30_000) });
			status = response.status;
			await response.body?.cancel();
			after = await readGuardState({ env, fetchImpl, warn, readRule: false });
		} catch (error) {
			log(`::error::the beacon check could not run: ${error.message}`);
			return 1;
		}
		if (before.deployment !== after.deployment) {
			last = `the live deployment changed during the probe (${before.deployment} to ${after.deployment})`;
			log(`${last}; probing again`);
			continue;
		}
		const want = before.tripped ? '403 or 404' : '204';
		if (!beaconFits(before.tripped, status)) {
			last = `the beacon answered ${status}, not ${want} (live deployment ${before.message ? `"${before.message}"` : 'with no message'}, code paths ${before.tripped ? 'held off' : 'on'})`;
			if (attempt < attempts) log(`${last}; probing again`);
			continue;
		}
		log(before.tripped ? `ok   the beacon answers ${status}: the code paths are off until they are switched back` : 'ok   the beacon answers 204');
		return 0;
	}
	log(`::error::${last} (${attempts} attempts)`);
	return 1;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.exitCode = await runCheckBeacon({ env: process.env });
}
