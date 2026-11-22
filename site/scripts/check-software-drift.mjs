// The software node this site publishes, held to what jmrp.io states about it.
//
// jmrp.io's /projects/ publishes the same SoftwareApplication node as every
// page of this site, under the same `@id` (`${repositoryUrl}#software`), and
// a crawler that reads both merges them into one entity. Where the two state
// different values for a property such as `license` or `description`, the
// merged entity says two contradictory things. jmrp.io's CI compares the two
// (scripts/ci/check-software-drift.mjs there), but only on jmrp.io's own
// pushes and pull requests: twice in four days a change made here (the
// conformance count in the description, then the licence) went out with every
// check of this site green, and the contradiction waited for jmrp.io's next
// unrelated commit to turn its CI red.
//
// So this site runs the same comparison on its own build, before it deploys.
// It reads the software node of the built home page, the node jmrp.io's check
// reads on the live site, and the record jmrp.io publishes for the project in
// `public/identity/projects.json`, the feed /projects/ is generated from, and
// fails when a property in jmrp.io's CONTRADICTABLE list that both sides
// state differs. The decision is jmrp.io's own, copied verbatim
// (shared/software-drift-decision.mjs): values compared as the sets JSON-LD
// makes them, a list property's comma-joined string split into its items, a
// property only one side states left uncompared, and the divergences jmrp.io
// accepts accepted here. A change to one of these properties goes to jmrp.io
// first (`src/content/profile/projects.yaml` there), then here.
//
// The check also reads that decision where jmrp.io keeps it, on the same
// branch and host as the feed, and fails when its two blocks are no longer
// the copy. A property jmrp.io adds to the list it compares would otherwise
// be compared there and not here, and a change here to that property would
// pass this site's checks and turn jmrp.io's next commit red, the very thing
// this check exists to stop. A change to the decision is made there first,
// and every run here is red until the copy follows it.
//
// The feed and the decision are read from raw.githubusercontent.com, the way
// astro.config.mjs reads jmrp.io's Person node and for the same reason: this
// runs on a CI runner, and jmrp.io sits behind a firewall that may block one,
// while GitHub serves the same bytes and is already the host the checkout
// came from. And as there, a feed or a decision that cannot be read, or that
// is not what it should be, fails the check. jmrp.io's own check passes when the docs site cannot be read, because
// that site is someone else's server and an outage says nothing about drift.
// Here the source is the host the build already cannot do without (the build
// stops when it cannot read the Person node from it), so a run that reaches
// this step can read the feed, and one that cannot would pass the very change
// this check exists to stop without having compared anything.
//
// Usage: node scripts/check-software-drift.mjs [--from dist] [--feed <url-or-file>] [--decision <url-or-file>]
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

import { repositoryUrl } from '../src/data/site.mjs';
import { CONTRADICTABLE, classifyDivergences, divergentProperties, valueDifference } from './shared/software-drift-decision.mjs';

/** Where jmrp.io publishes its project feed for builds like this one. */
export const PROJECTS_URL = 'https://raw.githubusercontent.com/jmrplens/jmrp.io/main/public/identity/projects.json';

/** Where jmrp.io keeps the decision this site copies, on the branch the feed is read from. */
export const DECISION_URL = 'https://raw.githubusercontent.com/jmrplens/jmrp.io/main/scripts/ci/software-drift-decision.mjs';

/** The copy of that decision this site runs. */
const DECISION_COPY = new URL('./shared/software-drift-decision.mjs', import.meta.url);

/** What each copied block holds, in the order decisionBlocks returns them. */
const BLOCK_NAMES = ['the accepted divergences and the compared properties', 'the comparison'];

/** The node both sites publish for the software. */
export const SOFTWARE_ID = `${repositoryUrl}#software`;

/** How long the feed may take to answer. */
const TIMEOUT_MS = 10_000;

/**
 * Every node of every JSON-LD block of a page, a graph's nodes one by one.
 *
 * @param {string} html The page.
 * @returns {Record<string, unknown>[]} The nodes; a block that is not JSON is skipped.
 */
export function pageNodes(html) {
	const nodes = [];
	for (const match of html.matchAll(/<script type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)) {
		try {
			const parsed = JSON.parse(match[1]);
			nodes.push(...(parsed['@graph'] ?? [parsed]));
		} catch {
			// check-structured-data.mjs fails on a block that does not parse.
		}
	}
	return nodes;
}

/**
 * The software node of a page, as jmrp.io's check finds it: the node with
 * the shared `@id` whose type is a Software one.
 *
 * @param {Record<string, unknown>[]} nodes The page's nodes.
 * @param {string} [id] The node's `@id`.
 * @returns {Record<string, unknown> | undefined} The node.
 */
export function softwareNode(nodes, id = SOFTWARE_ID) {
	return nodes.find((node) => node['@id'] === id && String(node['@type'] ?? '').startsWith('Software'));
}

/**
 * The properties jmrp.io states as an English and a Spanish literal, LOCALIZED
 * in its decision module (beside its siteValues, between the two blocks this
 * site copies). A localized property is read as `<property>`, its English
 * literal or else its untagged value, and `<property>@es`, its Spanish
 * literal; CONTRADICTABLE names both.
 */
export const LOCALIZED = Object.freeze(['description', 'disambiguatingDescription', 'keywords']);

/**
 * What this site states for each property jmrp.io compares, read from its
 * software node the way jmrp.io's check reads a docs site (siteValues there):
 * a localized property gives the first literal tagged `en`, or its untagged
 * value when none is, as `<property>`, and the first literal tagged `es` as
 * `<property>@es`; every other property is read as written.
 *
 * @param {Record<string, unknown>} node The software node.
 * @returns {Record<string, unknown>} The values, by property.
 */
export function siteValues(node) {
	const tagged = (value, language) => [value ?? []].flat().find((literal) => literal?.['@language'] === language)?.['@value'];
	const value = (property) => {
		const [base, language] = property.split('@', 2);
		if (!LOCALIZED.includes(base)) return node[property];
		if (language) return tagged(node[base], language);
		return tagged(node[base], 'en') ?? node[base];
	};
	return Object.fromEntries(CONTRADICTABLE.map((property) => [property, value(property)]));
}

/**
 * The record jmrp.io publishes for the software, found by the node it
 * describes (`${repo}#software`), as jmrp.io names that node.
 *
 * @param {unknown} feed The parsed feed.
 * @param {string} [id] The software node's `@id`.
 * @returns {Record<string, unknown>} The record.
 * @throws {Error} When the feed is not jmrp.io's project feed or names no such record.
 */
export function feedRecord(feed, id = SOFTWARE_ID) {
	const projects = /** @type {{projects?: unknown}} */ (feed)?.projects;
	if (!Array.isArray(projects)) throw new Error('the document is not jmrp.io\'s project feed: it has no "projects" list');
	const record = projects.find((project) => typeof project?.repo === 'string' && `${project.repo}#software` === id);
	if (!record) throw new Error(`jmrp.io's project feed has no record for ${id}`);
	if (typeof record.id !== 'string' || typeof record.name !== 'string') throw new Error(`jmrp.io's record for ${id} has no id or name`);
	return record;
}

/**
 * What jmrp.io states for each property it compares, from its feed record,
 * mapped as jmrp.io's projectValues maps the projects.yaml entry the record is
 * generated from (scripts/ci/build-projects.mjs there): the English and the
 * Spanish summary as the two descriptions, the licence as the URL or the list
 * of URLs the record states (the identifier only when it states none), and
 * the repository as both `codeRepository` and `url`. The feed writes a
 * missing Spanish summary as an empty string, which states nothing. Every
 * property of CONTRADICTABLE has its entry here, and the test holds the two
 * lists equal: a compared property with no source would pass as agreement.
 * The feed does not publish projects.yaml's `disambiguatingDescription` or its
 * `keywords` (the feed's own `keywords` lists the project's topics, another
 * value), so those four entries state nothing, are never compared, and the
 * check names them on every run (FEED_LACKS).
 *
 * @param {Record<string, any>} record The feed record.
 * @returns {Record<string, unknown>} The values, by property.
 */
export function jmrpValues(record) {
	return {
		name: record.name,
		alternateName: record.alternateName,
		description: record.description,
		'description@es': record.descriptionEs || undefined,
		disambiguatingDescription: undefined,
		'disambiguatingDescription@es': undefined,
		keywords: undefined,
		'keywords@es': undefined,
		license: record.licenseUrl ?? record.license,
		programmingLanguage: record.language,
		applicationCategory: record.applicationCategory,
		applicationSubCategory: record.applicationSubCategory,
		operatingSystem: record.operatingSystem,
		codeRepository: record.repo,
		url: record.repo,
	};
}

/** The properties jmrp.io compares that its feed does not publish (see jmrpValues). */
export const FEED_LACKS = Object.freeze(['disambiguatingDescription', 'disambiguatingDescription@es', 'keywords', 'keywords@es']);

/**
 * The comparison of this site's node with jmrp.io's record. jmrp.io's
 * functions name the project's own site "theirs" and jmrp.io "ours"; this
 * site is the first argument of each.
 *
 * @param {Record<string, unknown>} node This site's software node.
 * @param {Record<string, any>} record jmrp.io's feed record for it.
 * @returns {{compared: string[], contradicting: string[], accepted: string[], lines: string[]}}
 *   The properties both sides state, those that contradict, those jmrp.io
 *   accepts, and one line for each property that differs.
 */
export function driftReport(node, record) {
	const site = siteValues(node);
	const jmrp = jmrpValues(record);
	const compared = CONTRADICTABLE.filter((property) => site[property] !== undefined && jmrp[property] !== undefined);
	const { contradicting, accepted } = classifyDivergences(record.id, divergentProperties(site, jmrp));
	const lines = [];
	for (const property of [...contradicting, ...accepted]) {
		const { onlyTheirs: onlyHere, onlyOurs: onlyJmrp } = valueDifference(property, site[property], jmrp[property]);
		const tag = accepted.includes(property) ? ' (accepted by jmrp.io)' : '';
		lines.push(`${property}${tag}: this site states ${onlyHere.join(', ') || 'nothing'} that jmrp.io does not; jmrp.io states ${onlyJmrp.join(', ') || 'nothing'} that this site does not`);
	}
	return { compared, contradicting, accepted, lines };
}

/**
 * The two blocks of jmrp.io's decision this site copies: from the comment
 * above ACCEPTED_DIVERGENCES to the end of CONTRADICTABLE, and from the
 * comment above LIST_PROPERTIES to the end of classifyDivergences.
 *
 * @param {string} source The text of a decision module.
 * @returns {[string, string]} The two blocks, as written.
 * @throws {Error} When the text holds either block nowhere.
 */
export function decisionBlocks(source) {
	const cut = (comment, last, through, end) => {
		const start = source.indexOf(`/**\n * ${comment}`);
		const at = start < 0 ? -1 : source.indexOf(through, start);
		const stop = at < 0 ? -1 : source.indexOf(end, at);
		if (stop < 0) throw new Error(`it holds no block from ${JSON.stringify(comment)} to the end of ${last}`);
		return source.slice(start, stop + end.length);
	};
	return [
		cut('Divergences the author decided to keep', 'CONTRADICTABLE', 'export const CONTRADICTABLE = Object.freeze([', ']);\n'),
		cut('Properties whose text can name several items', 'classifyDivergences', 'export function classifyDivergences(', '\n}\n'),
	];
}

/**
 * Reads a text from a URL or a file.
 *
 * @param {string} source An https URL, or a path.
 * @param {typeof fetch} fetchImpl The fetch to use.
 * @returns {Promise<string>} The text.
 */
async function readSource(source, fetchImpl) {
	if (!/^https?:\/\//.test(source)) return readFileSync(source, 'utf8');
	const response = await fetchImpl(source, { signal: AbortSignal.timeout(TIMEOUT_MS) });
	if (!response.ok) throw new Error(`HTTP ${response.status}`);
	return response.text();
}

/**
 * The blocks of jmrp.io's decision that are no longer the copy here.
 *
 * @param {string} source Where to read jmrp.io's decision: an https URL, or a path.
 * @param {typeof fetch} fetchImpl The fetch to use.
 * @returns {Promise<string[]>} What each differing block holds, by BLOCK_NAMES.
 */
async function decisionDrift(source, fetchImpl) {
	const theirs = decisionBlocks(await readSource(source, fetchImpl));
	const ours = decisionBlocks(readFileSync(DECISION_COPY, 'utf8'));
	return BLOCK_NAMES.filter((_, index) => theirs[index] !== ours[index]);
}

/**
 * Runs the check.
 *
 * @param {{argv: string[], fetchImpl?: typeof fetch, sink?: {log: string[]} | null}} options
 * @returns {Promise<0 | 1 | 2>} 0 when the two agree, 1 on a contradiction or
 *   when either side cannot be read, 2 on usage.
 */
export async function runCheck({ argv, fetchImpl = fetch, sink = null }) {
	const log = (line) => (sink ? sink.log.push(line) : console.log(line));
	let args;
	try {
		args = parseArgs({ args: argv, options: { from: { type: 'string' }, feed: { type: 'string' }, decision: { type: 'string' } } }).values;
	} catch (error) {
		log(error.message);
		return 2;
	}
	const dist = resolve(args.from ?? join(dirname(fileURLToPath(import.meta.url)), '..', 'dist'));
	const source = args.feed ?? PROJECTS_URL;
	const decision = args.decision ?? DECISION_URL;
	// Named before anything can fail, so a red run says it too (F78).
	log(`note jmrp.io compares ${FEED_LACKS.join(', ')}, which its feed does not publish: never compared here`);

	let node;
	try {
		node = softwareNode(pageNodes(readFileSync(join(dist, 'index.html'), 'utf8')));
	} catch (error) {
		log(`::error::the build's home page cannot be read (${error.message}); build the site first`);
		return 1;
	}
	if (!node) {
		log(`::error::the build's home page publishes no ${SOFTWARE_ID} node`);
		return 1;
	}

	const ON_PURPOSE = 'The check stops here on purpose: a run that compares nothing would pass the very change it is here to stop.';
	let record;
	try {
		record = feedRecord(JSON.parse(await readSource(source, fetchImpl)));
	} catch (error) {
		log(`::error::jmrp.io's project feed is unusable: ${error.message} (${source}). ${ON_PURPOSE}`);
		return 1;
	}
	let drift;
	try {
		drift = await decisionDrift(decision, fetchImpl);
	} catch (error) {
		log(`::error::jmrp.io's decision is unusable: ${error.message} (${decision}). ${ON_PURPOSE}`);
		return 1;
	}

	const { compared, contradicting, accepted, lines } = driftReport(node, record);
	for (const line of lines) log(`${contradicting.some((property) => line.startsWith(`${property}:`)) ? '::error::' : ''}${line}`);
	if (contradicting.length > 0) {
		log(
			`::error::${contradicting.length} propert${contradicting.length === 1 ? 'y' : 'ies'} of ${SOFTWARE_ID} ` +
				`contradict${contradicting.length === 1 ? 's' : ''} what jmrp.io states (${source}): ${contradicting.join(', ')}. ` +
				'jmrp.io publishes the same node; change the value in its src/content/profile/projects.yaml first, ' +
				'then here (docs/contributing/docs-and-figures.md#f78).',
		);
	}
	if (drift.length > 0) {
		log(
			`::error::jmrp.io's decision (${decision}) is no longer the copy in site/scripts/shared/software-drift-decision.mjs: ` +
				`its block of ${drift.join(' and its block of ')} differ${drift.length === 1 ? 's' : ''}. The comparison above ran with the copy. A change to the ` +
				'decision is made there first; copy its two blocks here, verbatim (docs/contributing/docs-and-figures.md#f78).',
		);
	}
	if (contradicting.length > 0 || drift.length > 0) return 1;
	log(`ok   ${SOFTWARE_ID} agrees with jmrp.io on ${compared.length} properties (${compared.join(', ')})${accepted.length ? `, ${accepted.length} accepted` : ''}, from ${source}, by the decision ${decision} states`);
	return 0;
}

const invokedDirectly = process.argv[1] !== undefined && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) process.exitCode = await runCheck({ argv: process.argv.slice(2) });
