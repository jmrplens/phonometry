// Brings the phonometry.dev zone to its DNS records and settings (lib/zone.mjs).
//
// Usage, from the maintainer's machine (it is not run by CI):
//   CLOUDFLARE_EMAIL=... CLOUDFLARE_API_KEY=... \
//     node site/worker/scripts/apply-zone.mjs [--apply] [--backup-dir <dir>]
//
// Without --apply it reads and prints the plan, and writes nothing. With it,
// it saves every record and setting it read to one JSON file first, then
// creates the missing records and sets the settings that differ. A record in
// the place of a wanted one that says something else is never changed: the
// run reports it and exits 1. Rolling back is deleting the records it lists
// as created and setting each saved value back.
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';

import { API, ZONE_ID, authHeaders, cfApi, ignoredTargets } from '../lib/cloudflare.mjs';
import { ZONE_SETTINGS, zonePlan } from '../lib/zone.mjs';

export const ZONE = 'phonometry.dev';

/** Every DNS record of the zone, page by page. */
async function allRecords(zone, fetchPage) {
	const records = [];
	for (let page = 1; ; page += 1) {
		const { result, info } = await fetchPage(`/zones/${zone}/dns_records?per_page=100&page=${page}`);
		records.push(...result);
		if (!info || page >= (info.total_pages ?? 1)) return records;
	}
}

/**
 * Runs the plan, or applies it.
 *
 * @param {{argv: string[], env: Record<string, string | undefined>, fetchImpl?: typeof fetch, sink?: {log: string[]}}} options
 * @returns {Promise<number>} 0 when done (or nothing to do), 1 on a conflict or an error, 2 on usage.
 */
export async function runApplyZone({ argv, env, fetchImpl = fetch, sink = null }) {
	const log = (line) => (sink ? sink.log.push(line) : console.log(line));
	let args;
	try {
		args = parseArgs({ args: argv, options: { apply: { type: 'boolean' }, 'backup-dir': { type: 'string' } } }).values;
	} catch (error) {
		log(error.message);
		return 2;
	}
	const zone = ZONE_ID;
	for (const line of ignoredTargets(env)) log(line);
	const api = (path, options = {}) => cfApi(path, { ...options, env, fetchImpl });
	// The records endpoint pages; cfApi keeps only `result`, so this one call reads the envelope.
	const fetchPage = async (path) => {
		const response = await fetchImpl(`${API}${path}`, { headers: { ...authHeaders(env), accept: 'application/json' } });
		const payload = await response.json();
		if (!response.ok || payload.success === false) throw new Error(`GET ${path}: HTTP ${response.status}`);
		return { result: payload.result ?? [], info: payload.result_info };
	};
	try {
		const records = await allRecords(zone, fetchPage);
		const settings = {};
		for (const id of Object.keys(ZONE_SETTINGS)) settings[id] = (await api(`/zones/${zone}/settings/${id}`))?.value;
		const plan = zonePlan({ zone: ZONE, records, settings });
		const verb = args.apply ? 'create' : 'would create';
		for (const record of plan.create) log(`${verb} ${record.type} ${record.name} ${JSON.stringify(record.content)}`);
		for (const { id, from, to } of plan.settings) log(`${args.apply ? 'set' : 'would set'} ${id}: ${JSON.stringify(from)} -> ${JSON.stringify(to)}`);
		for (const label of plan.keep) log(`already right: ${label}`);
		for (const line of plan.conflicts) log(`CONFLICT ${line}`);
		if (plan.conflicts.length > 0) return 1;
		if (!args.apply) return 0;
		const dir = args['backup-dir'] ?? process.cwd();
		mkdirSync(dir, { recursive: true });
		const saved = join(dir, `zone-${new Date().toISOString().replaceAll(':', '-')}.json`);
		writeFileSync(saved, `${JSON.stringify({ zone: ZONE, records, settings }, null, 2)}\n`);
		log(`what was there is in ${saved}`);
		for (const record of plan.create) {
			const created = await api(`/zones/${zone}/dns_records`, { method: 'POST', body: record });
			log(`created ${record.type} ${record.name}: id ${created?.id}`);
		}
		for (const { id, to } of plan.settings) {
			await api(`/zones/${zone}/settings/${id}`, { method: 'PATCH', body: { value: to } });
			log(`set ${id}`);
		}
	} catch (error) {
		log(`error: ${error.message}`);
		return 1;
	}
	return 0;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	process.exitCode = await runApplyZone({ argv: process.argv.slice(2), env: process.env });
}
