// The quota guard: at 95 % of the day's Workers requests it switches off
// every path that runs code, and after 00:00 UTC it switches them back.
//
// Workers Free gives the account 100 000 requests a day, reset at 00:00 UTC.
// Pages never run code and never count; the beacon and the agent files do
// (lib/agent-paths.mjs). Off means two things, in this order:
// phonometry-docs is rolled to the assets-only version uploaded beside its
// full one in the same deploy (tagged `assets-<k>` and `full-<k>`), so the
// agent files are served as plain assets again and /_v, which no asset
// answers, costs nothing; then the zone's WAF rule `quota-guard-beacon`
// blocks /_v before any Worker runs, and its last update records the day.
// The deploy comes first so that a run that fails halfway leaves a state the
// next run finishes: a marked assets-only deploy without the rule is
// switched back after 00:00 like a whole trip, while the rule on above a CI
// deploy would carry no mark the guard could recognise. Back on is the
// reverse order: the full version first, then the rule off, so /_v returns
// only when its Worker is live.
//
// reconcile() reads the whole state from Cloudflare each time and keeps none
// of its own. Once tripped, the rule's last_updated carries the day, so the
// site stays off until the first run after 00:00 UTC, when the count is near
// zero and the rule was updated the day before. It runs from the guard
// Worker's Cron Trigger (guard/src/index.mjs) and by hand from
// scripts/quota-switch.mjs.
//
// The guard switches back on only what it switched off itself. Each deploy it
// makes carries the message `quota guard: off|on at <count> of <threshold>`,
// and back on means the live deployment's message starts with
// `quota guard: off`. Anything else at 100 % (a CI deploy, a `wrangler
// rollback`, an assets-only version deployed by hand, or `quota-switch.mjs
// --mode off`, whose message starts with `quota switch by hand:`) is left as
// it is, and so is the rule, with a note in the log. Switching off does not
// ask: at the threshold the version goes to assets only and the rule goes on
// whoever deployed it, because that is what keeps the quota. The one case
// left alone is an assets-only version already live that neither the guard
// nor quota-switch.mjs marked: it runs no code, so the quota is kept without
// the rule, and a rule turned on beside it would have no owner to turn it
// off after 00:00 UTC, so a later full deploy would find the beacon blocked.

import { ACCOUNT_ID, ZONE_ID, cfApi, graphql } from './cloudflare.mjs';
import { quotaQuery, quotaRows } from './quota.mjs';

export const SCRIPT = 'phonometry-docs';
export const GUARD_RULE_REF = 'quota-guard-beacon';
export const DEFAULT_THRESHOLD = 95000;
/** The start of the message of every deploy the guard makes. */
export const GUARD_MARK = 'quota guard';
/** The start of the message of a deploy made by hand with quota-switch.mjs --mode off|on. */
export const HAND_MARK = 'quota switch by hand';
const MODES = new Set(['auto', 'dry-run', 'off', 'on']);

/**
 * Which half of a deploy's pair a version tag names, and the deploy it belongs to.
 *
 * @param {string} tag The version's `workers/tag` annotation.
 * @returns {{half: 'full' | 'assets', key: string} | null} Null for a tag of no pair.
 */
export function pairKey(tag) {
	const match = /^(full|assets)-(.+)$/.exec(tag ?? '');
	return match ? { half: match[1], key: match[2] } : null;
}

const utcDay = (value) => new Date(value).toISOString().slice(0, 10);

/**
 * The version to roll to: the other half of the live version's pair, or,
 * when there is none, the newest version of the wanted half.
 */
function target(versions, current, half, notes) {
	const live = pairKey(current.tag);
	if (live) {
		const pair = versions.find((v) => v.tag === `${half}-${live.key}`);
		if (pair) return pair;
	}
	const newest = versions.filter((v) => pairKey(v.tag)?.half === half).sort((a, b) => (a.created < b.created ? 1 : -1))[0];
	if (newest) notes.push(`no paired version for ${current.id} (${current.tag || 'no tag'}); using the newest ${half} version ${newest.id} (${newest.tag})`);
	else notes.push(`no ${half} version to roll to`);
	return newest ?? null;
}

/**
 * Whether a deployment message says the guard made that deploy, and in which
 * direction. A deploy made by hand through quota-switch.mjs --mode off|on is
 * not the guard's.
 *
 * @param {string} message The live deployment's `workers/message` annotation.
 * @returns {{guard: boolean, off: boolean}} Made by the guard; made to switch off.
 */
export function guardDeploy(message) {
	const text = message ?? '';
	return { guard: text.startsWith(`${GUARD_MARK}: `), off: text.startsWith(`${GUARD_MARK}: off`) };
}

/**
 * What the guard should do, from what it read.
 *
 * @param {object} state
 * @param {number} state.count The account's Workers requests since 00:00 UTC.
 * @param {number} state.threshold The count that switches off.
 * @param {string} state.mode auto, dry-run (decide, change nothing), off or on (pinned).
 * @param {Date} state.now The moment of the run.
 * @param {{enabled: boolean, lastUpdated: string} | null} state.rule The WAF rule, null when the zone has none.
 * @param {{id: string, tag: string, message?: string}} state.current The version at 100 %, and the message of the deployment that put it there.
 * @param {{id: string, tag: string, created: string}[]} state.versions The Worker's versions.
 * @returns {{desired: 'on' | 'off', actions: object[], notes: string[]}} The decision.
 */
export function decide({ count, threshold, mode, now, rule, current, versions }) {
	const notes = [];
	const trippedToday = Boolean(rule?.enabled) && utcDay(rule.lastUpdated) === utcDay(now);
	const pinned = mode === 'off' || mode === 'on';
	let desired = count >= threshold || trippedToday ? 'off' : 'on';
	if (pinned) desired = mode;
	if (rule === null) notes.push(`no WAF rule ${GUARD_RULE_REF} in the zone: only the version can switch`);
	const half = pairKey(current.tag)?.half ?? 'unpaired';
	const made = guardDeploy(current.message);
	const actions = [];
	const ruleAction = (enabled) => {
		if (rule !== null && rule.enabled !== enabled) actions.push({ kind: 'rule', enabled });
	};
	const versionAction = (wanted) => {
		if (half === wanted) return;
		const to = target(versions, current, wanted, notes);
		if (to && to.id !== current.id) actions.push({ kind: 'deploy', versionId: to.id, tag: to.tag });
	};
	const by = current.message ? `"${current.message}"` : 'a deployment with no message';
	if (desired === 'off') {
		versionAction('assets');
		// The rule follows an assets-only version, live or being deployed now:
		// blocked beacons beside a full version that keeps running would save
		// little, and the rule would stay on after 00:00 above a deploy the
		// guard never marked. A live one counts only when the guard or
		// quota-switch.mjs switched it off (or the mode pins off): whoever
		// switched it off is who switches the rule back.
		const owned = made.off || (current.message ?? '').startsWith(`${HAND_MARK}: off`) || pinned;
		if (actions.some((action) => action.kind === 'deploy') || (half === 'assets' && owned)) ruleAction(true);
		else if (half === 'assets') notes.push(`live ${current.id} (${current.tag}) was put there by ${by}, not by the guard or quota-switch.mjs: the rule is not turned on, since nothing would turn it off after 00:00 UTC (the assets-only version runs no code)`);
		else notes.push(`the rule stays as it is: there is no assets-only version to go with it`);
		return { desired, actions, notes };
	}
	// Back on: only what the guard switched off, unless the mode pins it on.
	if (pinned || made.off) versionAction('full');
	else if (half !== 'full') notes.push(`live ${current.id} (${current.tag || 'no tag'}) was put there by ${by}, not by the guard: left as it is`);
	if (pinned || made.guard) ruleAction(false);
	else if (rule?.enabled) notes.push(`the rule is on and the live deployment is ${by}, not the guard's: left on`);
	return { desired, actions, notes };
}

/** The state of the account, read through the API. */
async function readState(api, env, fetchImpl, now) {
	const { today } = quotaQuery(ACCOUNT_ID, now);
	const count = quotaRows(await graphql(today, { env, fetchImpl })).reduce((sum, row) => sum + row.requests, 0);
	const entry = await api(`/zones/${ZONE_ID}/rulesets/phases/http_request_firewall_custom/entrypoint`).catch((error) => {
		if (error.status === 404) return null;
		throw error;
	});
	const live = entry?.rules?.find((r) => r.ref === GUARD_RULE_REF) ?? null;
	const deployments = await api(`/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT}/deployments`);
	const latest = (deployments?.deployments ?? [])[0];
	const top = latest?.versions?.find((v) => v.percentage === 100);
	if (!top) throw new Error(`${SCRIPT} has no version at 100 % (a gradual deployment is left alone)`);
	const listed = await api(`/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT}/versions?deployable=true&per_page=100`);
	const versions = (listed?.items ?? []).map((v) => ({ id: v.id, tag: v.annotations?.['workers/tag'] ?? '', created: v.metadata?.created_on ?? '' }));
	const current = { id: top.version_id, tag: versions.find((v) => v.id === top.version_id)?.tag ?? '', message: latest.annotations?.['workers/message'] ?? '' };
	const rule = live && { enabled: Boolean(live.enabled), lastUpdated: live.last_updated, raw: live, rulesetId: entry.id };
	return { count, rule, current, versions };
}

/**
 * One run of the guard: read, decide, act (unless dry).
 *
 * The token (CF_GUARD_TOKEN, a secret of the guard Worker) needs Account
 * Analytics Read and Workers Scripts Write on the account and Zone WAF Write
 * on phonometry.dev. Without it the run is dry and makes no call.
 *
 * @param {object} options
 * @param {Record<string, string | undefined>} options.env CF_GUARD_TOKEN, THRESHOLD, MODE (or, by hand, CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY).
 * @param {typeof fetch} [options.fetchImpl] The fetch.
 * @param {Date} [options.now] The moment of the run.
 * @param {boolean} [options.byHand] Run from quota-switch.mjs: a deploy made in mode off or on
 *   says so in its message, so the guard never switches it back.
 * @returns {Promise<{dry: boolean, lines: string[], decision?: object, error?: string}>} What happened.
 */
export async function reconcile({ env, fetchImpl = fetch, now = new Date(), byHand = false }) {
	const lines = [];
	const mode = MODES.has(env.MODE) ? env.MODE : 'dry-run';
	const threshold = Number(env.THRESHOLD) > 0 ? Number(env.THRESHOLD) : DEFAULT_THRESHOLD;
	const auth = env.CF_GUARD_TOKEN ? { CLOUDFLARE_API_TOKEN: env.CF_GUARD_TOKEN } : env.CLOUDFLARE_API_TOKEN || (env.CLOUDFLARE_EMAIL && env.CLOUDFLARE_API_KEY) ? env : null;
	if (auth === null) {
		lines.push('dry: no CF_GUARD_TOKEN secret; nothing read, nothing changed (the token needs Account Analytics Read, Workers Scripts Write, Zone WAF Write on phonometry.dev)');
		return { dry: true, lines };
	}
	const api = (path, options = {}) => cfApi(path, { ...options, env: auth, fetchImpl });
	let state;
	try {
		state = await readState(api, auth, fetchImpl, now);
	} catch (error) {
		lines.push(`error: the state could not be read, nothing changed: ${error.message}`);
		return { dry: true, lines, error: error.message };
	}
	const decision = decide({ ...state, threshold, mode, now });
	lines.push(
		`${state.count} of ${threshold} requests today; rule ${state.rule ? (state.rule.enabled ? 'on' : 'off') : 'absent'}; live ${state.current.id} (${state.current.tag || 'no tag'}, deployed with ${state.current.message ? `"${state.current.message}"` : 'no message'}); wanted ${decision.desired}; mode ${mode}`,
	);
	const mark = byHand && (mode === 'off' || mode === 'on') ? HAND_MARK : GUARD_MARK;
	for (const note of decision.notes) lines.push(`note: ${note}`);
	const dry = mode === 'dry-run';
	for (const action of decision.actions) {
		const what = action.kind === 'rule' ? `turn the rule ${action.enabled ? 'on' : 'off'}` : `deploy ${action.versionId} (${action.tag})`;
		if (dry) {
			lines.push(`dry-run: would ${what}`);
			continue;
		}
		try {
			if (action.kind === 'rule') {
				const { raw, rulesetId } = state.rule;
				await api(`/zones/${ZONE_ID}/rulesets/${rulesetId}/rules/${raw.id}`, {
					method: 'PATCH',
					body: { ref: raw.ref, description: raw.description, expression: raw.expression, action: raw.action, enabled: action.enabled },
				});
			} else {
				await api(`/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT}/deployments`, {
					method: 'POST',
					body: {
						strategy: 'percentage',
						versions: [{ version_id: action.versionId, percentage: 100 }],
						annotations: { 'workers/message': `${mark}: ${decision.desired} at ${state.count} of ${threshold}` },
					},
				});
			}
			lines.push(`done: ${what}`);
		} catch (error) {
			lines.push(`error: could not ${what}: ${error.message}`);
			return { dry, lines, decision, error: error.message };
		}
	}
	return { dry, lines, decision };
}
