// The quota guard: at 95 % of the day's Workers requests it switches off
// every path that runs code, and after 00:00 UTC it switches them back.
//
// Workers Free gives the account 100,000 requests a day, reset at 00:00 UTC.
// Pages never run code and never count; the beacon and the agent files do
// (lib/agent-paths.mjs). Off means two things, in this order: the zone's WAF
// rule `quota-guard-beacon` blocks /_v before any Worker runs, and
// phonometry-docs is rolled to the assets-only version uploaded beside its
// full one in the same deploy (tagged `assets-<k>` and `full-<k>`), so the
// agent files are served as plain assets again. Back on is the reverse
// order: the full version first, then the rule off, so /_v returns only when
// its Worker is live.
//
// reconcile() reads the whole state from Cloudflare each time and keeps none
// of its own. Once tripped, the rule's last_updated carries the day, so the
// site stays off until the first run after 00:00 UTC, when the count is near
// zero and the rule was updated the day before. It runs from the guard
// Worker's Cron Trigger (guard/src/index.mjs) and by hand from
// scripts/quota-switch.mjs.

import { ACCOUNT_ID, ZONE_ID, cfApi, graphql } from './cloudflare.mjs';
import { quotaQuery, quotaRows } from './quota.mjs';

export const SCRIPT = 'phonometry-docs';
export const GUARD_RULE_REF = 'quota-guard-beacon';
export const DEFAULT_THRESHOLD = 95000;
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
 * What the guard should do, from what it read.
 *
 * @param {object} state
 * @param {number} state.count The account's Workers requests since 00:00 UTC.
 * @param {number} state.threshold The count that switches off.
 * @param {string} state.mode auto, dry-run (decide, change nothing), off or on (pinned by hand).
 * @param {Date} state.now The moment of the run.
 * @param {{enabled: boolean, lastUpdated: string} | null} state.rule The WAF rule, null when the zone has none.
 * @param {{id: string, tag: string}} state.current The version at 100 %.
 * @param {{id: string, tag: string, created: string}[]} state.versions The Worker's versions.
 * @returns {{desired: 'on' | 'off', actions: object[], notes: string[]}} The decision.
 */
export function decide({ count, threshold, mode, now, rule, current, versions }) {
	const notes = [];
	const trippedToday = Boolean(rule?.enabled) && utcDay(rule.lastUpdated) === utcDay(now);
	let desired = count >= threshold || trippedToday ? 'off' : 'on';
	if (mode === 'off' || mode === 'on') desired = mode;
	if (rule === null) notes.push(`no WAF rule ${GUARD_RULE_REF} in the zone: only the version can switch`);
	const half = pairKey(current.tag)?.half ?? 'unpaired';
	const actions = [];
	const ruleAction = (enabled) => {
		if (rule !== null && rule.enabled !== enabled) actions.push({ kind: 'rule', enabled });
	};
	const versionAction = (wanted) => {
		if (half === wanted) return;
		const to = target(versions, current, wanted, notes);
		if (to && to.id !== current.id) actions.push({ kind: 'deploy', versionId: to.id, tag: to.tag });
	};
	if (desired === 'off') {
		ruleAction(true);
		versionAction('assets');
	} else {
		versionAction('full');
		ruleAction(false);
	}
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
	const top = (deployments?.deployments ?? [])[0]?.versions?.find((v) => v.percentage === 100);
	if (!top) throw new Error(`${SCRIPT} has no version at 100 % (a gradual deployment is left alone)`);
	const listed = await api(`/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT}/versions?deployable=true&per_page=100`);
	const versions = (listed?.items ?? []).map((v) => ({ id: v.id, tag: v.annotations?.['workers/tag'] ?? '', created: v.metadata?.created_on ?? '' }));
	const current = { id: top.version_id, tag: versions.find((v) => v.id === top.version_id)?.tag ?? '' };
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
 * @returns {Promise<{dry: boolean, lines: string[], decision?: object, error?: string}>} What happened.
 */
export async function reconcile({ env, fetchImpl = fetch, now = new Date() }) {
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
	lines.push(`${state.count} of ${threshold} requests today; rule ${state.rule ? (state.rule.enabled ? 'on' : 'off') : 'absent'}; live ${state.current.id} (${state.current.tag || 'no tag'}); wanted ${decision.desired}; mode ${mode}`);
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
						annotations: { 'workers/message': `quota guard: ${decision.desired} at ${state.count} of ${threshold}` },
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
