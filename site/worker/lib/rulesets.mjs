// Comparing the zone's live rules with the generated ones.

/** The fields of a rule this repository decides; ids, versions and dates are Cloudflare's. */
const FIELDS = ['description', 'expression', 'action', 'action_parameters', 'ratelimit', 'enabled'];

/** A JSON value with its object keys sorted, so two equal rules print the same. */
function canonical(value) {
	if (Array.isArray(value)) return value.map(canonical);
	if (value && typeof value === 'object') {
		return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonical(value[key])]));
	}
	return value;
}

/**
 * Every way the live rules of a phase differ from the wanted ones.
 *
 * @param {{ref?: string, id?: string}[]} live The rules the entrypoint holds now ([] when it has none).
 * @param {{ref: string}[]} wanted The generated rules, in order.
 * @returns {string[]} One line per difference; empty when the phase is as generated.
 */
export function ruleDrift(live, wanted) {
	const drift = [];
	const byRef = new Map(live.map((rule) => [rule.ref ?? rule.id, rule]));
	for (const rule of wanted) {
		const current = byRef.get(rule.ref);
		if (!current) {
			drift.push(`${rule.ref}: missing`);
			continue;
		}
		for (const field of FIELDS) {
			const a = JSON.stringify(canonical(current[field] ?? null));
			const b = JSON.stringify(canonical(rule[field] ?? null));
			if (a !== b) drift.push(`${rule.ref}: ${field} is ${a}, generated ${b}`);
		}
	}
	const refs = new Set(wanted.map(({ ref }) => ref));
	for (const rule of live) if (!refs.has(rule.ref ?? rule.id)) drift.push(`${rule.ref ?? rule.id}: not generated here (an apply removes it)`);
	const order = live.map((rule) => rule.ref ?? rule.id).filter((ref) => refs.has(ref));
	const wantedOrder = wanted.map(({ ref }) => ref).filter((ref) => order.includes(ref));
	if (drift.length === 0 && order.join() !== wantedOrder.join()) drift.push(`order is ${order.join(', ')}, generated ${wantedOrder.join(', ')}`);
	return drift;
}
