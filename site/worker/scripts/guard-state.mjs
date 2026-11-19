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
// It prints four lines for $GITHUB_OUTPUT:
//   tripped=true|false
//   mark=quota guard|quota switch by hand|   (whose state to carry; empty: none)
//   rule=on|off|absent|unknown
//   deployment=<id>   (the live deployment it read)
//
// After the deploy, `--since <id> --pair <k>` reads the deployments made
// since the one read before it. The guard runs every 15 minutes and
// quota-switch.mjs at any time, so either can switch between the read and
// the deploy, which would then promote a state read too early: full code
// over the guard's off switch, and a rule the guard no longer owns after
// 00:00 UTC. When the newest deployment is this deploy's (its message names
// the pair) and another came between, it prints `switched=true` and the
// state that one left (tripped=, mark=), which the deploy then follows;
// otherwise `switched=false`.
//
// A token needs Workers Scripts Read (the deploy token's Workers Scripts
// Write has it). Exit 0 when read, 1 when the deployment could not be read or
// the answer is not a list of deployments (or no longer lists the one read
// before), 2 on a usage error.
import { parseArgs } from 'node:util';
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

/** The deployments the API listed, newest first, each checked to be an object with an id and a text message. */
function deploymentList(listed) {
	const deployments = listed !== null && typeof listed === 'object' && !Array.isArray(listed) ? listed.deployments : undefined;
	if (!Array.isArray(deployments) || deployments.length === 0) throw new Error('the answer lists no deployment');
	return deployments.map((deployment, index) => {
		const what = index === 0 ? 'the live deployment' : `deployment ${index}`;
		if (deployment === null || typeof deployment !== 'object' || Array.isArray(deployment)) throw new Error(`${what} is not an object`);
		const message = deployment.annotations?.['workers/message'] ?? '';
		if (typeof message !== 'string') throw new Error(`${what} message is not text`);
		if (typeof deployment.id !== 'string' || deployment.id === '') throw new Error(`${what} has no id`);
		return { id: deployment.id, message };
	});
}

/**
 * The live deployment, from the deployments the API listed.
 *
 * @param {unknown} listed The `result` of GET .../deployments.
 * @returns {{id: string, message: string}} Its id and `workers/message` ('' when it has none).
 * @throws {Error} When the answer is not a non-empty list of deployments.
 */
export function liveDeployment(listed) {
	return deploymentList(listed)[0];
}

/**
 * The state a deploy has to follow when another deployment came between the
 * read before it and its own.
 *
 * @param {unknown} listed The `result` of GET .../deployments, read after the deploy.
 * @param {{since: string, pair: string}} options The deployment read before the deploy, and the deploy's pair.
 * @returns {{tripped: boolean, mark: string, rule: string} | null} What the deployment just before this deploy's
 *   left; null when none came between, or when the newest is not this deploy's (that one stands).
 * @throws {Error} When the answer is not a list of deployments, or no longer lists the one read before.
 */
export function switchedDuring(listed, { since, pair }) {
	const deployments = deploymentList(listed);
	const index = deployments.findIndex((deployment) => deployment.id === since);
	if (index < 0) throw new Error(`the deployment read before the deploy (${since}) is not among the ${deployments.length} listed`);
	const escaped = pair.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
	const own = new RegExp(` of ${escaped}(?![\\w.-])`);
	if (index < 2 || !own.test(deployments[0].message)) return null;
	return guardState({ message: deployments[1].message, rule: 'unknown' });
}

/**
 * The guard's state as the API answers it now: the live deployment and, when
 * the token can read it, the WAF rule.
 *
 * @param {{env: Record<string, string | undefined>, fetchImpl?: typeof fetch, warn: (line: string) => void, readRule?: boolean}} options
 *   With readRule false the rule is not read and counts as unknown: the state is the live deployment's alone.
 * @returns {Promise<{deployment: string, message: string, tripped: boolean, mark: string, rule: string}>} The state.
 * @throws {Error} When the live deployment cannot be read.
 */
export async function readGuardState({ env, fetchImpl = fetch, warn, readRule = true }) {
	const api = (path) => cfApi(path, { env, fetchImpl });
	let live;
	try {
		live = liveDeployment(await api(`/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT}/deployments`));
	} catch (error) {
		throw new Error(`the live deployment of ${SCRIPT} could not be read: ${error.message}`);
	}
	let rule = 'unknown';
	if (readRule) {
		try {
			const entry = await api(`/zones/${ZONE_ID}/rulesets/phases/http_request_firewall_custom/entrypoint`);
			const found = entry?.rules?.find((r) => r.ref === GUARD_RULE_REF);
			rule = found ? (found.enabled ? 'on' : 'off') : 'absent';
		} catch (error) {
			rule = error.status === 404 ? 'absent' : 'unknown';
			if (rule === 'unknown') warn(`the WAF rule ${GUARD_RULE_REF} could not be read (${error.message}); going by the live deployment`);
		}
	}
	return { deployment: live.id, message: live.message, ...guardState({ message: live.message, rule }) };
}

/**
 * Reads and prints the state, or, with --since and --pair, what switched during the deploy.
 *
 * @param {{argv?: string[], env: Record<string, string | undefined>, fetchImpl?: typeof fetch, sink?: {log: string[]}}} options
 * @returns {Promise<number>} The exit code.
 */
export async function runGuardState({ argv = [], env, fetchImpl = fetch, sink = null }) {
	const log = (line) => (sink ? sink.log.push(line) : console.log(line));
	const warn = (line) => (sink ? sink.log.push(line) : console.error(line));
	let args;
	try {
		args = parseArgs({ args: argv, options: { since: { type: 'string' }, pair: { type: 'string' } } }).values;
	} catch (error) {
		warn(error.message);
		return 2;
	}
	if ((args.since === undefined) !== (args.pair === undefined) || args.since === '' || args.pair === '') {
		warn('--since <deployment> and --pair <k> go together');
		return 2;
	}
	if (!(env.CLOUDFLARE_API_TOKEN || (env.CLOUDFLARE_EMAIL && env.CLOUDFLARE_API_KEY))) {
		warn('set CLOUDFLARE_API_TOKEN, or CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY');
		return 2;
	}
	for (const line of ignoredTargets(env)) warn(line);
	if (args.since !== undefined) {
		let switched;
		try {
			switched = switchedDuring(await cfApi(`/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT}/deployments`, { env, fetchImpl }), { since: args.since, pair: args.pair });
		} catch (error) {
			warn(`the deployments of ${SCRIPT} since ${args.since} could not be read: ${error.message}`);
			return 1;
		}
		log(`switched=${switched !== null}`);
		if (switched !== null) {
			warn(`another deployment came between the read and the deploy of ${args.pair}: it left the code paths ${switched.tripped ? 'off' : 'on'}${switched.mark ? ` under "${switched.mark}"` : ''}`);
			log(`tripped=${switched.tripped}`);
			log(`mark=${switched.mark}`);
		}
		return 0;
	}
	let state;
	try {
		state = await readGuardState({ env, fetchImpl, warn });
	} catch (error) {
		warn(error.message);
		return 1;
	}
	warn(`live deployment of ${SCRIPT}: ${state.message ? `"${state.message}"` : 'no message'}; rule ${state.rule}`);
	log(`tripped=${state.tripped}`);
	log(`mark=${state.mark}`);
	log(`rule=${state.rule}`);
	log(`deployment=${state.deployment}`);
	return 0;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.exitCode = await runGuardState({ argv: process.argv.slice(2), env: process.env });
}
