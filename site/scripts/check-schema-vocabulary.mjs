// The structured data the build wrote, held to the schema.org vocabulary.
//
// check-structured-data.mjs proves that every graph parses, that each page
// carries the nodes it should and that they join by `@id`. It does not ask
// whether schema.org allows a property on the type that carries it, or allows
// the type of the value it is given, and three misplacements shipped past it:
//
// - the guides hub's ItemList carried `inLanguage`, which schema.org defines
//   on CreativeWork, Event and a few others, and an ItemList is none of them;
// - the journal articles in the bibliography carried `volumeNumber` and
//   `issueNumber`, as far as their reference named them, and those belong to
//   PublicationVolume and PublicationIssue, not to the ScholarlyArticle that
//   held them;
// - every API page carried `codeRepository` and `programmingLanguage`, which
//   belong to SoftwareSourceCode, not to an APIReference.
//
// A consumer that reads the vocabulary drops such a property, so the page
// says less than its source does and nothing reports it.
//
// So this reads every JSON-LD block of every built page, with `@graph` and
// nested nodes flattened, against the schema.org release pinned in
// schema-vocabulary.json (generate-schema-vocabulary.mjs writes it), so it
// runs offline and gives the same answer on every run. Each of these fails:
//
// - a property schema.org does not define, or a `@type` it does not define;
// - a property on a node none of whose types, or their supertypes, is in the
//   property's `domainIncludes`, unless DOMAIN_EXCEPTIONS below names it with
//   its reason, and an exception that no page uses any more;
// - a node value whose types, and their supertypes, are all outside the
//   property's `rangeIncludes`. A bare `{"@id"}` reference is resolved to the
//   types its node has on the same page, else anywhere in the build;
// - a node with properties and no `@type`. One that only adds properties to
//   a node typed elsewhere, by its `@id`, is held to that node's types, on
//   the same page first, then anywhere in the build.
//
// Two shapes are accepted on purpose, as the Schema Markup Validator accepts
// them: a literal (text, a number, a date or an `@value` object) stands for
// Text in any property, and a Role stands in for the value it qualifies, and
// carries the property it qualifies, outside that property's domain.
//
// Reported and not failed: a property schema.org has superseded, which it
// still defines, and a reference to an `@id` no page of the build types,
// which check-structured-data.mjs holds for the joins a page must make.
//
// The Person node is jmrp.io's: the build fetches it from jmrp.io's main
// branch and splices it in as published, so a change made there reaches
// this site's next build with nothing changed here. On that node, and on
// every node nested in it, a value outside its range still fails, as it
// does in jmrp.io's own check, but the other findings are reported and do
// not fail, so that change cannot stop this site from deploying. A node is
// another site's when the top-level node it sits in has an `@id` that is
// neither a page of this site nor this project's repository (OWN_ORIGINS).
//
// It is ported from the check jmrp.io runs on its own build, against the same
// release. That one fails on a range and only warns on a domain; all three
// misplacements above are domain errors, so here a domain fails as a range
// does.
//
// Usage: node scripts/check-schema-vocabulary.mjs [dist-directory]
// Exit status: 0 nothing found, 1 findings (listed), 2 the check could not
// run (no build, or an unreadable vocabulary).
import { existsSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { basePath, siteUrl } from '../src/data/site.mjs';
import { VOCABULARY_PATH } from './generate-schema-vocabulary.mjs';
import { isRedirectStub, reporter, walk as walkBuild } from './shared/dist-pages.mjs';

/**
 * Properties this site states outside their schema.org domain on purpose,
 * each with the reason, keyed `Type.property` as the findings name them.
 * Every entry must still be used somewhere in the build.
 */
export const DOMAIN_EXCEPTIONS = new Map([
	[
		'SoftwareApplication.codeRepository',
		'jmrp.io publishes the same node, @id for @id, with codeRepository on it, ' +
			'and its check-software-drift.mjs compares the two values',
	],
	[
		'SoftwareApplication.programmingLanguage',
		'jmrp.io publishes the same node, @id for @id, with programmingLanguage on it, ' +
			'and its check-software-drift.mjs compares the two values',
	],
]);

/**
 * `schema:Thing` or `https://schema.org/Thing` as `Thing`.
 *
 * @param {string} type A `@type` value as written.
 * @returns {string} The bare term name.
 */
const bare = (type) => type.replace(/^(?:schema:|https?:\/\/schema\.org\/)/, '');

/**
 * A node's `@type` values, bare.
 *
 * @param {Record<string, unknown>} node A JSON-LD node.
 * @returns {string[]} Its types; empty when it declares none.
 */
const typesOf = (node) =>
	[node['@type'] ?? []]
		.flat()
		.filter((t) => typeof t === 'string')
		.map(bare);

/**
 * The compact vocabulary, with the subclass lookups the check needs.
 *
 * @param {{release?: string, classes: Record<string, string[]>,
 *   properties: Record<string, {range: string[], domain: string[],
 *   supersededBy?: string[]}>}} raw The parsed vocabulary file.
 * @returns {{release: string, isA: (type: string, cls: string) => boolean,
 *   knowsType: (type: string) => boolean, property: (name: string) =>
 *   {range: string[], domain: string[], supersededBy?: string[]} | undefined}}
 *   The lookups.
 */
export function createVocabulary(raw) {
	/** @type {Map<string, Set<string>>} */
	const ancestors = new Map();
	const lineage = (type) => {
		const known = ancestors.get(type);
		if (known) return known;
		const out = new Set([type]);
		ancestors.set(type, out); // a cycle in the source data ends here
		for (const parent of raw.classes[type] ?? []) for (const a of lineage(parent)) out.add(a);
		return out;
	};
	return {
		release: raw.release ?? 'unknown',
		isA: (type, cls) => lineage(type).has(cls),
		knowsType: (type) => Object.hasOwn(raw.classes, type),
		property: (name) => (Object.hasOwn(raw.properties, name) ? raw.properties[name] : undefined),
	};
}

/**
 * The pinned vocabulary.
 *
 * @param {string} [file] Another vocabulary file, for the tests.
 * @returns {ReturnType<typeof createVocabulary>} The lookups.
 */
export function loadVocabulary(file = VOCABULARY_PATH) {
	return createVocabulary(JSON.parse(readFileSync(file, 'utf8')));
}

/**
 * A `<script type="application/ld+json">` element and its body. A pattern and
 * not a DOM parse, as in check-structured-data.mjs: the attribute is matched
 * wherever the element carries it, and a JSON body cannot hold `</script>`
 * without breaking the page it is on.
 */
const JSON_LD_SCRIPT = /<script\b[^>]*\btype=["']?application\/ld\+json["']?[^>]*>([\s\S]*?)<\/script\s*>/gi;

/**
 * The JSON-LD blocks of a page, parsed.
 *
 * @param {string} html The page.
 * @returns {{blocks: unknown[], errors: string[]}} The blocks that parse, and
 *   a message for each block that is not valid JSON.
 */
export function jsonLdBlocks(html) {
	const blocks = [];
	const errors = [];
	let i = 0;
	for (const [, body] of html.matchAll(JSON_LD_SCRIPT)) {
		i += 1;
		try {
			blocks.push(JSON.parse(body));
		} catch (error) {
			errors.push(`JSON-LD block ${i} is not valid JSON: ${error.message}`);
		}
	}
	return { blocks, errors };
}

/**
 * @typedef {{via: string | undefined, owner: string | null,
 *   parent: Record<string, unknown> | undefined}} Position Where a node sits:
 *   the property it is the value of (undefined at the top), the `@id` of the
 *   top-level node it sits in (null when that node has none, so this page
 *   wrote it), and the node it is the value of.
 */

/**
 * Calls `fn` on every object node under `value`, depth first, with where it
 * sits. Each member of a `@graph` is a top-level node, and so is the block
 * itself when it has no `@graph`; `@context` is not data and is not entered.
 *
 * @param {unknown} value A parsed block, or any part of one.
 * @param {(node: Record<string, unknown>, position: Position) => void} fn The
 *   visitor.
 * @param {Position} [position] Where `value` sits; omitted at the top.
 * @returns {void}
 */
function visit(value, fn, position) {
	if (Array.isArray(value)) {
		for (const item of value) visit(item, fn, position);
		return;
	}
	if (!value || typeof value !== 'object') return;
	const here = position ?? {
		via: undefined,
		owner: typeof value['@id'] === 'string' ? value['@id'] : null,
		parent: undefined,
	};
	fn(value, here);
	for (const [key, child] of Object.entries(value)) {
		if (key === '@context') continue;
		if (key === '@graph') visit(child, fn);
		else if (key.startsWith('@')) visit(child, fn, here);
		else visit(child, fn, { via: key, owner: here.owner, parent: value });
	}
}

/**
 * Every `@id` declared with a `@type`, with all the types it is given.
 *
 * @param {unknown[]} blocks Parsed JSON-LD.
 * @param {Map<string, Set<string>>} [into] The map to add to.
 * @returns {Map<string, Set<string>>} `@id` to its types.
 */
export function typedIds(blocks, into = new Map()) {
	visit(blocks, (node) => {
		const id = node['@id'];
		const types = typesOf(node);
		if (typeof id !== 'string' || types.length === 0) return;
		const known = into.get(id) ?? new Set();
		for (const t of types) known.add(t);
		into.set(id, known);
	});
	return into;
}

/**
 * @typedef {{file: string, blocks: unknown[]}} Page One built page: its route
 *   and its parsed JSON-LD.
 * @typedef {{key: string, files: string[]}} Finding What was found, and on
 *   which pages.
 */

/** Adds `file` under `key`. */
function note(map, key, file) {
	const files = map.get(key) ?? new Set();
	files.add(file);
	map.set(key, files);
}

/** A findings map as a list, the most widespread first. */
function listed(map) {
	return [...map]
		.map(([key, files]) => ({ key, files: [...files].sort((a, b) => a.localeCompare(b)) }))
		.sort((a, b) => b.files.length - a.files.length || a.key.localeCompare(b.key));
}

/**
 * The types one value of a property stands for: its own `@type`, or the types
 * of the node a bare `{"@id"}` names, on the same page first, then anywhere in
 * the build.
 *
 * @param {unknown} item One value of a property.
 * @param {Map<string, Set<string>>} pageIds Typed `@id`s of this page.
 * @param {Map<string, Set<string>>} siteIds Typed `@id`s of the build.
 * @returns {string[] | null} The types; empty for a literal or an untyped
 *   value; null for a reference to no typed node.
 */
function valueTypes(item, pageIds, siteIds) {
	if (item === null || typeof item !== 'object' || '@value' in item) return [];
	const own = typesOf(item);
	const id = item['@id'];
	if (own.length > 0 || typeof id !== 'string') return own;
	const target = pageIds.get(id) ?? siteIds.get(id);
	return target ? [...target] : null;
}

/**
 * Adds a finding of a failing kind, or, on a node another site publishes,
 * reports it under `elsewhere` with what it would have been.
 *
 * @param {object} ctx The page, the findings, and whether the node is
 *   another site's.
 * @param {keyof typeof ELSEWHERE} kind The failing kind.
 * @param {string} key The finding.
 * @returns {void}
 */
function flag(ctx, kind, key) {
	if (ctx.elsewhere) note(ctx.found.elsewhere, `${ELSEWHERE[kind]}: ${key}`, ctx.file);
	else note(ctx.found[kind], key, ctx.file);
}

/**
 * Holds the properties of one node to the vocabulary, as a node of `own`.
 *
 * @param {Record<string, unknown>} node The node.
 * @param {string[]} own Its types, or those its `@id` has elsewhere.
 * @param {string | undefined} via The property the node is the value of.
 * @param {object} ctx The lookups, the page, the findings to add to, and
 *   whether the node is another site's.
 * @returns {number} How many properties were held to the vocabulary.
 */
function checkNode(node, own, via, ctx) {
	const { vocabulary, found, file } = ctx;
	const where = own.join('+');
	const isRole = own.some((t) => vocabulary.isA(t, 'Role'));
	let checked = 0;
	for (const [key, value] of Object.entries(node)) {
		if (key.startsWith('@')) continue;
		const label = `${where}.${key}`;
		const property = vocabulary.property(key);
		if (!property) {
			flag(ctx, 'unknownProperty', label);
			continue;
		}
		checked += 1;
		// A Role carries the property it qualifies: `hasOccupation` holds a
		// Role, and the Role holds `hasOccupation` again with the Occupation.
		const qualified = isRole && key === via;
		const { domain, supersededBy } = property;
		if (
			!qualified &&
			domain.length > 0 &&
			own.every((t) => domain.every((d) => !vocabulary.isA(t, d)))
		) {
			if (DOMAIN_EXCEPTIONS.has(label)) note(found.excepted, label, file);
			else flag(ctx, 'outsideDomain', `${label} (domain ${domain.join('|')})`);
		}
		if (supersededBy) note(found.superseded, `${label} -> ${supersededBy.join('|')}`, file);
		checkValues(label, value, property.range, ctx);
	}
	return checked;
}

/**
 * Holds a property's node values to its range.
 *
 * @param {string} label `Type.property`, as the findings name it.
 * @param {unknown} value The property's value, one or an array.
 * @param {string[]} range Its `rangeIncludes`; empty checks nothing.
 * @param {object} ctx The lookups, the page, and the findings to add to.
 * @returns {void}
 */
function checkValues(label, value, range, ctx) {
	if (range.length === 0) return;
	const { vocabulary, found, file } = ctx;
	for (const item of [value].flat(Infinity)) {
		const types = valueTypes(item, ctx.pageIds, ctx.siteIds);
		if (types === null) {
			note(found.unresolvedReference, `${label} -> ${item['@id']}`, file);
			continue;
		}
		if (types.length === 0) continue;
		const fits = types.some((t) => vocabulary.isA(t, 'Role') || range.some((r) => vocabulary.isA(t, r)));
		if (!fits) note(found.outOfRange, `${label} = ${types.join('+')} (range ${range.join('|')})`, file);
	}
}

/**
 * The kinds of finding that fail the check, in the order they are printed:
 * what a failure counts, and what a pass says.
 */
export const FAILING = {
	unknownType: ['type(s) schema.org does not define', 'every @type is one schema.org defines'],
	unknownProperty: ['propert(ies) schema.org does not define', 'every property is one schema.org defines'],
	outsideDomain: [
		'propert(ies) on a type outside their domainIncludes',
		'every property sits on a type in its domain, or is one of the exceptions',
	],
	outOfRange: [
		'value(s) whose type is outside their property rangeIncludes',
		'every node value has a type in its property range',
	],
	untypedNode: [
		'node(s) with properties and no @type, of their own or through their @id',
		'every node with properties has a type, of its own or through its @id',
	],
	unusedException: ['domain exception(s) no page uses any more', 'every domain exception is still used'],
};

/** The kinds of finding that are reported and do not fail. */
export const REPORTED = {
	superseded: 'a property schema.org has superseded and still defines',
	unresolvedReference: 'a reference to an @id of this site that no page types',
	elsewhere: 'a finding on a node another site publishes, which does not fail here',
};

/**
 * The failing kinds reported rather than failed on a node another site
 * publishes, each with how its report names it. A value outside its range
 * is not among them: it fails wherever it is.
 */
const ELSEWHERE = {
	unknownType: 'a type schema.org does not define',
	unknownProperty: 'a property schema.org does not define',
	outsideDomain: 'outside its domain',
	untypedNode: 'no type',
};

/**
 * Where this project mints `@id`s: the pages of the site, and the
 * repository, whose `#software` and `#source-code` nodes astro.config.mjs
 * writes.
 */
const OWN_ORIGINS = [`${siteUrl}${basePath}`, 'https://github.com/jmrplens/phonometry'];

/** Whether an `@id` is one this project mints rather than another site's. */
const isOwnId = (id) =>
	OWN_ORIGINS.some((origin) => id === origin || id.startsWith(`${origin}/`) || id.startsWith(`${origin}#`));

/**
 * `Type.property`, naming the property a node is the value of, for a node
 * that has no type to name itself by.
 *
 * @param {Position} position Where the node sits.
 * @returns {string} The label.
 */
function slot(position) {
	const { via, parent } = position;
	if (!parent) return 'a top-level node';
	return `${typesOf(parent).join('+') || 'an untyped node'}.${via}`;
}

/**
 * Holds every node of every page to the vocabulary.
 *
 * @param {Page[]} pages Every page's parsed JSON-LD.
 * @param {ReturnType<typeof createVocabulary>} vocabulary The lookups.
 * @returns {{findings: Record<string, Finding[]>, excepted: Finding[],
 *   checked: number}} The findings by kind (the keys of FAILING and
 *   REPORTED), the exceptions used, and how many properties were checked.
 */
export function checkVocabulary(pages, vocabulary) {
	const siteIds = new Map();
	for (const page of pages) typedIds(page.blocks, siteIds);

	const found = Object.fromEntries(
		[...Object.keys(FAILING), ...Object.keys(REPORTED), 'excepted'].map((kind) => [kind, new Map()]),
	);
	let checked = 0;
	for (const page of pages) {
		const pageIds = typedIds(page.blocks);
		visit(page.blocks, (node, position) => {
			const ctx = {
				vocabulary,
				pageIds,
				siteIds,
				file: page.file,
				found,
				elsewhere: position.owner !== null && !isOwnId(position.owner),
			};
			const own = typesOf(node);
			for (const t of own) if (!vocabulary.knowsType(t)) flag(ctx, 'unknownType', `@type ${t}`);
			if (own.length > 0) {
				checked += checkNode(node, own, position.via, ctx);
				return;
			}
			const properties = Object.keys(node).filter((key) => !key.startsWith('@'));
			if (properties.length === 0) return;
			// A node with properties and no type of its own adds them to the
			// node its @id names, so it is held to that node's types.
			const id = typeof node['@id'] === 'string' ? node['@id'] : undefined;
			const named = id === undefined ? undefined : (pageIds.get(id) ?? siteIds.get(id));
			if (named) {
				checked += checkNode(node, [...named], position.via, ctx);
			} else if (id !== undefined && !isOwnId(id)) {
				// Another site types that node; this build cannot see how.
				note(found.unresolvedReference, `${slot(position)} -> ${id}`, page.file);
			} else {
				flag(ctx, 'untypedNode', `${slot(position)} = ${id ?? 'a node'} {${properties.join(', ')}}`);
			}
		});
	}
	for (const label of DOMAIN_EXCEPTIONS.keys()) {
		if (!found.excepted.has(label)) note(found.unusedException, label, '(no page)');
	}
	const { excepted, ...rest } = found;
	return {
		findings: Object.fromEntries(Object.entries(rest).map(([kind, map]) => [kind, listed(map)])),
		excepted: listed(excepted),
		checked,
	};
}

/**
 * Every built page's JSON-LD, read from the build.
 *
 * @param {string} dist The build.
 * @returns {{pages: Page[], parseErrors: Finding[], stubs: number}} The pages,
 *   every block that is not valid JSON, and how many redirect stubs were
 *   passed over.
 */
export function readBuild(dist) {
	const pages = [];
	const parseErrors = new Map();
	let stubs = 0;
	for (const [route, file] of [...walkBuild(dist)].sort(([a], [b]) => a.localeCompare(b))) {
		const html = readFileSync(file, 'utf8');
		if (isRedirectStub(html)) {
			stubs += 1;
			continue;
		}
		const { blocks, errors } = jsonLdBlocks(html);
		for (const error of errors) note(parseErrors, error, route);
		pages.push({ file: route, blocks });
	}
	return { pages, parseErrors: listed(parseErrors), stubs };
}

/** `count pages`, or `1 page`. */
const pagesCount = (count) => `${count} page${count === 1 ? '' : 's'}`;

/** One finding as one line: what, on how many pages, and the first of them. */
const line = ({ key, files }) => `${key}, on ${pagesCount(files.length)}, e.g. ${files[0]}`;

/**
 * Reads the build named by `argv`, prints what it finds and returns the exit
 * status.
 *
 * @param {string[]} argv `[dist-directory]`.
 * @returns {number} 0 when nothing fails, 1 when something does.
 * @throws {Error} When there is no build to read.
 */
function main(argv) {
	const here = dirname(fileURLToPath(import.meta.url));
	const dist = argv[0] ? resolve(argv[0]) : join(here, '..', 'dist');
	if (!existsSync(dist) || !statSync(dist).isDirectory()) {
		throw new Error(`no build at ${dist}: run \`pnpm build\` first`);
	}
	if (!existsSync(join(dist, 'index.html'))) {
		throw new Error(`${dist} holds no index.html, so it is not a build of this site`);
	}
	const vocabulary = loadVocabulary();
	const { pages, parseErrors, stubs } = readBuild(dist);
	const { findings, excepted, checked } = checkVocabulary(pages, vocabulary);
	const { report, ok, failures } = reporter();

	console.log(
		`read ${pages.length} pages in ${dist} (${stubs} redirect stubs passed over), ` +
			`against schema.org ${vocabulary.release}`,
	);
	report(parseErrors.map(line), 'JSON-LD block(s) that do not parse', 'every JSON-LD block parses');
	for (const [kind, [what, passed]] of Object.entries(FAILING)) report(findings[kind].map(line), what, passed);
	for (const { key, files } of excepted) {
		ok(`${key} is outside its domain on ${pagesCount(files.length)}, on purpose: ${DOMAIN_EXCEPTIONS.get(key)}`);
	}
	for (const finding of findings.superseded) console.log(`note ${REPORTED.superseded}: ${line(finding)}`);
	for (const finding of findings.elsewhere) console.log(`note ${REPORTED.elsewhere}: ${line(finding)}`);
	// The Person node is jmrp.io's, and names the other projects it owns by
	// their own sites' @ids, which no page of this build types; those are not
	// this site's to resolve, and are counted rather than listed.
	const target = ({ key }) => key.slice(key.indexOf(' -> ') + 4);
	const [onSite, elsewhere] = [true, false].map((wanted) =>
		findings.unresolvedReference.filter((finding) => isOwnId(target(finding)) === wanted),
	);
	for (const finding of onSite) console.log(`note ${REPORTED.unresolvedReference}: ${line(finding)}`);
	if (elsewhere.length > 0) {
		ok(`${elsewhere.length} reference(s) name a node of another site, e.g. ${target(elsewhere[0])}`);
	}
	ok(`${checked} properties held to the vocabulary`);
	console.log(`\n${failures()} failing check(s).`);
	return failures() ? 1 : 0;
}

const invokedDirectly = process.argv[1] !== undefined && resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (invokedDirectly) {
	try {
		process.exitCode = main(process.argv.slice(2));
	} catch (error) {
		// 2, never 1: a check that could not run must not read as a finding.
		console.error(`check-schema-vocabulary could not run: ${error.message}`);
		process.exitCode = 2;
	}
}
