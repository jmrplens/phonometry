// Whether the quota guard has switched the code paths off, read before a
// deploy (site-preview.yml) so the deploy keeps them off.
//
// Usage:
//   CLOUDFLARE_API_TOKEN=... node site/worker/scripts/guard-state.mjs
//
// It reads the live deployment of phonometry-docs: a message that starts with
// `quota guard: off` or `quota switch by hand: off` means the assets-only half
// is live because the guard, or the maintainer through quota-switch.mjs, put
// it there. It also reads the WAF rule quota-guard-beacon when the token can
// (the deploy token cannot, and an answer it is refused reads as unknown): a
// rule that is on also counts as switched off, since the guard reads it so.
// Only a mark on the live deployment says whose off state it is: the rule on
// above a deployment the guard did not mark was not left by the guard, which
// deploys before it turns the rule on, so the deploy keeps it as an off state
// set by hand, which only `quota-switch.mjs --mode on` switches back. A live
// deployment the guard made to switch back on (`quota guard: on`) may still
// have its rule to turn off, which the deploy token cannot see: the deploy is
// then not held off, and it carries the guard's mark forward so the guard's
// next run still owns that rule.
// It prints three lines for $GITHUB_OUTPUT:
//   tripped=true|false
//   mark=quota guard|quota switch by hand|   (whose state to carry; empty: none)
//   rule=on|off|absent|unknown
// A token needs Workers Scripts Read (the deploy token's Workers Scripts
// Write has it). Exit 0 when read, 1 when the deployment could not be read or
// the answer is not a list of deployments, 2 on a usage error.
import { fileURLToPath } from 'node:url';

import { ACCOUNT_ID, ZONE_ID, cfApi, ignoredTargets } from '../lib/cloudflare.mjs';
import { GUARD_MARK, GUARD_RULE_REF, HAND_MARK, SCRIPT } from '../lib/guard.mjs';

/**
 * The guard's state from what the API answered.
 *
 * @param {{message: string, rule: 'on' | 'off' | 'absent' | 'unknown'}} read The live deployment's message and the rule.
 * @returns {{tripped: boolean, mark: string, rule: string}} What a deploy has to keep.
 */
export function guardState({ message, rule }) {
	const guardOff = message.startsWith(`${GUARD_MARK}: off`);
	const guardOn = message.startsWith(`${GUARD_MARK}: on`);
	const tripped = guardOff || message.startsWith(`${HAND_MARK}: off`) || (rule === 'on' && !guardOn);
	if (tripped) return { tripped, mark: guardOff ? GUARD_MARK : HAND_MARK, rule };
	return { tripped, mark: guardOn ? GUARD_MARK : '', rule };
}

/**
 * The message of the live deployment, from the deployments the API listed.
 *
 * @param {unknown} listed The `result` of GET .../deployments.
 * @returns {string} Its `workers/message`, '' when it has none.
 * @throws {Error} When the answer is not a non-empty list of deployments.
 */
export function liveMessage(listed) {
	const deployments = listed !== null && typeof listed === 'object' && !Array.isArray(listed) ? listed.deployments : undefined;
	if (!Array.isArray(deployments) || deployments.length === 0) throw new Error('the answer lists no deployment');
	const live = deployments[0];
	if (live === null || typeof live !== 'object' || Array.isArray(live)) throw new Error('the live deployment is not an object');
	const message = live.annotations?.['workers/message'] ?? '';
	if (typeof message !== 'string') throw new Error('the live deployment message is not text');
	return message;
}

/**
 * Reads and prints the state.
 *
 * @param {{env: Record<string, string | undefined>, fetchImpl?: typeof fetch, sink?: {log: string[]}}} options
 * @returns {Promise<number>} The exit code.
 */
export async function runGuardState({ env, fetchImpl = fetch, sink = null }) {
	const log = (line) => (sink ? sink.log.push(line) : console.log(line));
	const warn = (line) => (sink ? sink.log.push(line) : console.error(line));
	if (!(env.CLOUDFLARE_API_TOKEN || (env.CLOUDFLARE_EMAIL && env.CLOUDFLARE_API_KEY))) {
		warn('set CLOUDFLARE_API_TOKEN, or CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY');
		return 2;
	}
	for (const line of ignoredTargets(env)) warn(line);
	const api = (path) => cfApi(path, { env, fetchImpl });
	let message;
	try {
		message = liveMessage(await api(`/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT}/deployments`));
	} catch (error) {
		warn(`the live deployment of ${SCRIPT} could not be read: ${error.message}`);
		return 1;
	}
	let rule = 'unknown';
	try {
		const entry = await api(`/zones/${ZONE_ID}/rulesets/phases/http_request_firewall_custom/entrypoint`);
		const found = entry?.rules?.find((r) => r.ref === GUARD_RULE_REF);
		rule = found ? (found.enabled ? 'on' : 'off') : 'absent';
	} catch (error) {
		rule = error.status === 404 ? 'absent' : 'unknown';
		if (rule === 'unknown') warn(`the WAF rule ${GUARD_RULE_REF} could not be read (${error.message}); going by the live deployment`);
	}
	const state = guardState({ message, rule });
	warn(`live deployment of ${SCRIPT}: ${message ? `"${message}"` : 'no message'}; rule ${rule}`);
	log(`tripped=${state.tripped}`);
	log(`mark=${state.mark}`);
	log(`rule=${state.rule}`);
	return 0;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.exitCode = await runGuardState({ env: process.env });
}
