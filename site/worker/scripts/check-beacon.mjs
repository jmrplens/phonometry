// The deploy's beacon check (site-preview.yml): a POST of /_v answers what
// the live deployment says it should.
//
// Usage:
//   CLOUDFLARE_API_TOKEN=... node site/worker/scripts/check-beacon.mjs
//
// Full code live: 204. Code paths held off (scripts/guard-state.mjs reads
// tripped): the WAF rule's 403, or, while that rule is not on yet, the
// assets-only half's 404 (no asset is called _v); a 204 then would mean code
// is running. The state is read just before and just after the probe, not
// before the deploy: the guard runs every 15 minutes and quota-switch.mjs at
// any time, and a switch during the deploy changes the answer to expect.
// When the live deployment changes during the probe, it probes again with the
// new state, up to three times. The probe is the page view the deploy checks
// have always sent (webdriver flag set), so it lands in the dataset as one.
// Exit 0 when the answer fits, 1 when it does not or the state could not be
// read, 2 on a usage error.
import { fileURLToPath } from 'node:url';

import { ignoredTargets } from '../lib/cloudflare.mjs';
import { readGuardState } from './guard-state.mjs';

export const BEACON = 'https://phonometry.dev/_v';
const ORIGIN = 'https://phonometry.dev';
const BODY = '{"p":"/phonometry/signals/","wd":1}';

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
 * @param {{env: Record<string, string | undefined>, fetchImpl?: typeof fetch, sink?: {log: string[]}, attempts?: number}} options
 * @returns {Promise<number>} The exit code.
 */
export async function runCheckBeacon({ env, fetchImpl = fetch, sink = null, attempts = 3 }) {
	const log = (line) => (sink ? sink.log.push(line) : console.log(line));
	if (!(env.CLOUDFLARE_API_TOKEN || (env.CLOUDFLARE_EMAIL && env.CLOUDFLARE_API_KEY))) {
		log('set CLOUDFLARE_API_TOKEN, or CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY');
		return 2;
	}
	for (const line of ignoredTargets(env)) log(line);
	// The deploy token cannot read the WAF rule: that note is printed once.
	const notes = new Set();
	const warn = (line) => {
		if (!notes.has(line)) log(line);
		notes.add(line);
	};
	for (let attempt = 1; attempt <= attempts; attempt += 1) {
		let before;
		let after;
		let status;
		try {
			before = await readGuardState({ env, fetchImpl, warn });
			const response = await fetchImpl(BEACON, { method: 'POST', headers: { origin: ORIGIN, 'content-type': 'text/plain' }, body: BODY, signal: AbortSignal.timeout(30_000) });
			status = response.status;
			await response.body?.cancel();
			after = await readGuardState({ env, fetchImpl, warn });
		} catch (error) {
			log(`::error::the beacon check could not run: ${error.message}`);
			return 1;
		}
		if (before.deployment !== after.deployment || before.tripped !== after.tripped) {
			log(`the live deployment changed during the probe (${before.deployment} to ${after.deployment}); probing again`);
			continue;
		}
		const want = before.tripped ? '403 or 404' : '204';
		if (!beaconFits(before.tripped, status)) {
			log(`::error::the beacon answered ${status}, not ${want} (live deployment ${before.message ? `"${before.message}"` : 'with no message'}, code paths ${before.tripped ? 'held off' : 'on'})`);
			return 1;
		}
		log(before.tripped ? `ok   the beacon answers ${status}: the code paths are off until they are switched back` : 'ok   the beacon answers 204');
		return 0;
	}
	log(`::error::the live deployment changed during each of ${attempts} probes of the beacon`);
	return 1;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.exitCode = await runCheckBeacon({ env: process.env });
}
