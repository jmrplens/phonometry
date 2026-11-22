// The software node held to what jmrp.io states about it, on small builds and
// feeds made to agree and to disagree. No request leaves the process: the feed
// is handed to the check through a fetch that answers from memory.
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after, describe, test } from 'node:test';

import { repositoryUrl } from '../src/data/site.mjs';
import { DECISION_URL, FEED_LACKS, LOCALIZED, PROJECTS_URL, SOFTWARE_ID, decisionBlocks, driftReport, feedRecord, jmrpValues, pageNodes, runCheck, siteValues, softwareNode } from './check-software-drift.mjs';
import { CONTRADICTABLE } from './shared/software-drift-decision.mjs';

const MIT = 'https://opensource.org/license/MIT';
const EASA = `${repositoryUrl}/blob/main/LICENSES/LicenseRef-EASA-ANP.txt`;
const EN = 'Acoustic measurement for Python, with 1899 CI-enforced conformance checks.';
const ES = 'Medición acústica para Python, con 1899 comprobaciones de conformidad en CI.';

/** The software node as every page of the site publishes it. */
const node = () => ({
	'@type': 'SoftwareApplication',
	'@id': SOFTWARE_ID,
	name: 'phonometry',
	alternateName: 'PyOctaveBand',
	applicationCategory: 'DeveloperApplication',
	applicationSubCategory: 'Scientific/Engineering',
	operatingSystem: ['Linux', 'macOS', 'Windows'],
	programmingLanguage: 'Python',
	url: repositoryUrl,
	codeRepository: repositoryUrl,
	license: [MIT, EASA],
	description: [
		{ '@value': EN, '@language': 'en' },
		{ '@value': ES, '@language': 'es' },
	],
});

/** jmrp.io's record once it states the licence expression the package declares, with both URLs. */
const agreeing = () => ({
	id: 'phonometry',
	name: 'phonometry',
	alternateName: ['PyOctaveBand'],
	applicationCategory: 'DeveloperApplication',
	applicationSubCategory: 'Scientific/Engineering',
	language: 'Python',
	license: 'MIT AND LicenseRef-EASA-ANP',
	licenseUrl: [EASA, MIT],
	operatingSystem: 'Linux, macOS, Windows',
	repo: repositoryUrl,
	docs: 'https://phonometry.dev/',
	description: EN,
	descriptionEs: ES,
});

/** jmrp.io's record as its main branch states it on 2026-11-21: MIT alone. */
const mitAlone = () => ({ ...agreeing(), license: 'MIT', licenseUrl: MIT });

const feedOf = (...records) => ({ $comment: 'test feed', generator: 'https://github.com/jmrplens/jmrp.io', projects: [{ id: 'other', name: 'other', repo: 'https://github.com/jmrplens/other', docs: 'x', description: 'y' }, ...records] });

const page = (...nodes) =>
	`<!doctype html><html><head><script type="application/ld+json">${JSON.stringify({ '@context': 'https://schema.org', '@graph': nodes })}</script>` +
	'<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage","@id":"x"}</script></head><body></body></html>';

const scratch = mkdtempSync(join(tmpdir(), 'software-drift-'));
after(() => rmSync(scratch, { recursive: true, force: true }));
let builds = 0;
/** A build whose home page carries the given nodes. */
const build = (...nodes) => {
	const dist = join(scratch, `dist-${(builds += 1)}`);
	mkdirSync(dist, { recursive: true });
	writeFileSync(join(dist, 'index.html'), page(...nodes));
	return dist;
};
/** The copy of jmrp.io's decision this site holds, as jmrp.io's main branch states it when the two agree. */
const COPY = readFileSync(new URL('./shared/software-drift-decision.mjs', import.meta.url), 'utf8');
/** The copy with a property jmrp.io would have added to the list it compares. */
const widened = COPY.replace('export const CONTRADICTABLE = Object.freeze([\n', 'export const CONTRADICTABLE = Object.freeze([\n  "sameAs",\n');

/** A fetch that answers the feed URL and the decision URL from memory and records what it was asked. */
const fetchFrom = (feed, decision = COPY) => {
	const asked = [];
	const fetchImpl = async (url, options) => {
		asked.push({ url, signal: options?.signal });
		const answer = url === DECISION_URL ? decision : feed;
		if (answer instanceof Error) throw answer;
		if (typeof answer === 'number') return new Response('not found', { status: answer });
		return typeof answer === 'string' ? new Response(answer) : Response.json(answer);
	};
	return { asked, fetchImpl };
};
const run = async (dist, feed, decision) => {
	const sink = { log: [] };
	const { asked, fetchImpl } = fetchFrom(feed, decision);
	const code = await runCheck({ argv: ['--from', dist], fetchImpl, sink });
	return { code, out: sink.log.join('\n'), asked };
};

describe('the comparison of the two nodes', () => {
	test('a record that states the licence expression with both URLs agrees, whatever the order', () => {
		const report = driftReport(node(), agreeing());
		assert.deepEqual(report.contradicting, []);
		assert.deepEqual(report.lines, []);
		assert.deepEqual(report.compared, CONTRADICTABLE.filter((property) => !FEED_LACKS.includes(property)));
	});

	test('MIT alone contradicts the two licences the site states, and names the one jmrp.io lacks', () => {
		const report = driftReport(node(), mitAlone());
		assert.deepEqual(report.contradicting, ['license']);
		assert.deepEqual(report.lines, [`license: this site states ${JSON.stringify(EASA)} that jmrp.io does not; jmrp.io states nothing that this site does not`]);
	});

	test('a description jmrp.io does not state yet contradicts, in English and in Spanish apart', () => {
		const changed = node();
		changed.description = [
			{ '@value': EN.replace('1899', '1900'), '@language': 'en' },
			{ '@value': ES, '@language': 'es' },
		];
		assert.deepEqual(driftReport(changed, agreeing()).contradicting, ['description']);
		const spanish = node();
		spanish.description = [
			{ '@value': EN, '@language': 'en' },
			{ '@value': ES.replace('1899', '1900'), '@language': 'es' },
		];
		assert.deepEqual(driftReport(spanish, agreeing()).contradicting, ['description@es']);
	});

	test('the systems are compared as items, a list on one side and a comma-joined string on the other', () => {
		assert.deepEqual(driftReport({ ...node(), operatingSystem: 'Windows, Linux, macOS' }, agreeing()).contradicting, []);
		assert.deepEqual(driftReport({ ...node(), operatingSystem: ['Linux', 'Windows'] }, agreeing()).contradicting, ['operatingSystem']);
	});

	test('every other property jmrp.io compares is held too', () => {
		const cases = {
			name: { name: 'PyOctaveBand' },
			alternateName: { alternateName: 'Octave' },
			programmingLanguage: { programmingLanguage: 'Rust' },
			applicationCategory: { applicationCategory: 'Game' },
			applicationSubCategory: { applicationSubCategory: 'Games/Entertainment' },
			codeRepository: { codeRepository: 'https://example.org/fork' },
			url: { url: 'https://example.org/fork' },
		};
		for (const [property, change] of Object.entries(cases)) {
			assert.deepEqual(driftReport({ ...node(), ...change }, agreeing()).contradicting, [property], property);
		}
	});

	test('a property only one side states is not compared', () => {
		const record = agreeing();
		delete record.applicationCategory;
		const report = driftReport({ ...node(), applicationCategory: 'Game' }, record);
		assert.deepEqual(report.contradicting, []);
		assert.equal(report.compared.includes('applicationCategory'), false);
		assert.equal(driftReport(node(), { ...agreeing(), descriptionEs: '' }).compared.includes('description@es'), false);
	});

	test('every property jmrp.io compares has its source on both sides', () => {
		assert.deepEqual(Object.keys(siteValues(node())), CONTRADICTABLE);
		assert.deepEqual(Object.keys(jmrpValues(agreeing())), CONTRADICTABLE);
	});

	test('the properties the feed does not publish are the ones jmrpValues states nothing for, and are named', () => {
		const record = { ...agreeing(), keywords: ['Acoustics'], disambiguatingDescription: 'x' };
		const silent = Object.entries(jmrpValues(record)).filter(([, value]) => value === undefined).map(([property]) => property);
		assert.deepEqual(silent, [...FEED_LACKS]);
		assert.ok(FEED_LACKS.every((property) => CONTRADICTABLE.includes(property)));
	});

	test('each localized property is compared in English and in Spanish, as jmrp.io names them', () => {
		for (const property of LOCALIZED) {
			assert.ok(CONTRADICTABLE.includes(property), property);
			assert.ok(CONTRADICTABLE.includes(`${property}@es`), `${property}@es`);
		}
		const values = siteValues({
			...node(),
			keywords: [{ '@value': 'acoustics', '@language': 'en' }, 'Python', { '@value': 'acústica', '@language': 'es' }],
			disambiguatingDescription: 'Untagged text',
		});
		assert.equal(values.keywords, 'acoustics');
		assert.equal(values['keywords@es'], 'acústica');
		assert.equal(values.disambiguatingDescription, 'Untagged text');
		assert.equal(values['disambiguatingDescription@es'], undefined);
	});

	test('the site is read as jmrp.io reads a docs site, and jmrp.io as its projectValues reads its entry', () => {
		assert.deepEqual(siteValues(node()), {
			name: 'phonometry',
			alternateName: 'PyOctaveBand',
			description: EN,
			'description@es': ES,
			disambiguatingDescription: undefined,
			'disambiguatingDescription@es': undefined,
			keywords: undefined,
			'keywords@es': undefined,
			license: [MIT, EASA],
			programmingLanguage: 'Python',
			applicationCategory: 'DeveloperApplication',
			applicationSubCategory: 'Scientific/Engineering',
			operatingSystem: ['Linux', 'macOS', 'Windows'],
			codeRepository: repositoryUrl,
			url: repositoryUrl,
		});
		assert.deepEqual(jmrpValues(mitAlone()), {
			name: 'phonometry',
			alternateName: ['PyOctaveBand'],
			description: EN,
			'description@es': ES,
			disambiguatingDescription: undefined,
			'disambiguatingDescription@es': undefined,
			keywords: undefined,
			'keywords@es': undefined,
			license: MIT,
			programmingLanguage: 'Python',
			applicationCategory: 'DeveloperApplication',
			applicationSubCategory: 'Scientific/Engineering',
			operatingSystem: 'Linux, macOS, Windows',
			codeRepository: repositoryUrl,
			url: repositoryUrl,
		});
	});
});

describe('reading the two sides', () => {
	test('the record is the one whose repository names the shared node', () => {
		assert.equal(feedRecord(feedOf(mitAlone())).id, 'phonometry');
		assert.throws(() => feedRecord(feedOf()), /no record for https:\/\/github\.com\/jmrplens\/phonometry#software/);
		assert.throws(() => feedRecord({}), /not jmrp\.io's project feed/);
		assert.throws(() => feedRecord('<!doctype html>'), /not jmrp\.io's project feed/);
		assert.throws(() => feedRecord(feedOf({ repo: repositoryUrl })), /no id or name/);
	});

	test('the node is the Software one with the shared @id, among every block of the page', () => {
		const nodes = pageNodes(page({ '@type': 'WebSite', '@id': 'w' }, node()) + '<script type="application/ld+json">not json</script>');
		assert.equal(nodes.length, 3);
		assert.equal(softwareNode(nodes)?.['@id'], SOFTWARE_ID);
		assert.equal(softwareNode([{ '@type': 'WebPage', '@id': SOFTWARE_ID }]), undefined);
	});

	test('the feed and the decision are jmrp.io main on raw.githubusercontent.com, the host the Person node is read from', () => {
		assert.equal(PROJECTS_URL, 'https://raw.githubusercontent.com/jmrplens/jmrp.io/main/public/identity/projects.json');
		assert.equal(DECISION_URL, 'https://raw.githubusercontent.com/jmrplens/jmrp.io/main/scripts/ci/software-drift-decision.mjs');
		const config = readFileSync(new URL('../astro.config.mjs', import.meta.url), 'utf8');
		assert.match(config, /https:\/\/raw\.githubusercontent\.com\/jmrplens\/jmrp\.io\/main\/public\/identity\/person\.jsonld/);
	});
});

describe('the check on a build', () => {
	test('green on a feed that agrees and a decision that is the copy: each URL asked once, with a time limit', async () => {
		const { code, out, asked } = await run(build(node()), feedOf(agreeing()));
		assert.equal(code, 0, out);
		assert.match(out, /^ok {3}https:\/\/github\.com\/jmrplens\/phonometry#software agrees with jmrp\.io on 11 properties/);
		assert.match(out, /\n {5}not compared, since jmrp\.io's feed does not publish them: disambiguatingDescription, disambiguatingDescription@es, keywords, keywords@es$/m);
		assert.deepEqual(asked.map(({ url }) => url), [PROJECTS_URL, DECISION_URL]);
		assert.ok(asked.every(({ signal }) => signal instanceof AbortSignal));
	});

	test('red when jmrp.io\'s decision is no longer the copy, naming the block, whatever the feed says', async () => {
		const { code, out } = await run(build(node()), feedOf(agreeing()), widened);
		assert.equal(code, 1, out);
		assert.match(out, /::error::jmrp\.io's decision \(https:\/\/raw\.githubusercontent\.com\/jmrplens\/jmrp\.io\/main\/scripts\/ci\/software-drift-decision\.mjs\) is no longer the copy in site\/scripts\/shared\/software-drift-decision\.mjs: its block of the accepted divergences and the compared properties differs\./);
		assert.match(out, /copy its two blocks here/);
		assert.doesNotMatch(out, /^ok /m);
		const comparison = COPY.replace('contradicting: properties.filter((p) => !allowed.has(p)),', 'contradicting: [],');
		assert.notEqual(comparison, COPY, 'the test edit lands in the second block');
		assert.match((await run(build(node()), feedOf(agreeing()), comparison)).out, /: its block of the comparison differs\./);
		const both = await run(build(node()), feedOf(agreeing()), widened.replace('contradicting: properties.filter((p) => !allowed.has(p)),', 'contradicting: [],'));
		assert.match(both.out, /: its block of the accepted divergences and the compared properties and its block of the comparison differ\./);
	});

	test('red when jmrp.io\'s decision cannot be read: a network error, an HTTP error, a document without the two blocks', async () => {
		for (const [answer, why] of [
			[new TypeError('fetch failed'), /fetch failed/],
			[404, /HTTP 404/],
			['<!doctype html><title>Not the decision</title>', /it holds no block from "Divergences the author decided to keep" to the end of CONTRADICTABLE/],
		]) {
			const { code, out } = await run(build(node()), feedOf(agreeing()), answer);
			assert.equal(code, 1, String(why));
			assert.match(out, why);
			assert.match(out, /::error::jmrp\.io's decision is unusable: .*The check stops here on purpose/);
		}
	});

	test('red on a feed that states MIT alone, naming the property and where to change it', async () => {
		const { code, out } = await run(build(node()), feedOf(mitAlone()));
		assert.equal(code, 1);
		assert.match(out, /::error::license: this site states "https:\/\/github\.com\/jmrplens\/phonometry\/blob\/main\/LICENSES\/LicenseRef-EASA-ANP\.txt" that jmrp\.io does not/);
		assert.match(out, /::error::1 property of https:\/\/github\.com\/jmrplens\/phonometry#software contradicts what jmrp\.io states .*: license\./);
		assert.match(out, /src\/content\/profile\/projects\.yaml first/);
	});

	test('red when the feed cannot be read: a network error, an HTTP error, a document that is not the feed', async () => {
		for (const [answer, why] of [
			[new TypeError('fetch failed'), /fetch failed/],
			[404, /HTTP 404/],
			[{ projects: 'none' }, /no "projects" list/],
			[feedOf(), /no record for/],
		]) {
			const { code, out } = await run(build(node()), answer);
			assert.equal(code, 1, String(why));
			assert.match(out, why);
			assert.match(out, /::error::jmrp\.io's project feed is unusable: .*The check stops here on purpose/);
		}
	});

	test('red when the build has no home page, or its home page no software node', async () => {
		const missing = await run(join(scratch, 'no-such-dist'), feedOf(agreeing()));
		assert.equal(missing.code, 1);
		assert.match(missing.out, /home page cannot be read/);
		const bare = await run(build({ '@type': 'WebSite', '@id': 'w' }), feedOf(agreeing()));
		assert.equal(bare.code, 1);
		assert.match(bare.out, /publishes no https:\/\/github\.com\/jmrplens\/phonometry#software node/);
		assert.equal(bare.asked.length, 0, 'the feed is not asked for when there is nothing to compare');
	});

	test('a feed and a decision given as files are read from disk, with no request', async () => {
		const file = join(scratch, 'projects.json');
		writeFileSync(file, JSON.stringify(feedOf(agreeing())));
		const decision = join(scratch, 'software-drift-decision.mjs');
		writeFileSync(decision, COPY);
		const sink = { log: [] };
		const fetchImpl = async () => assert.fail('no request for a file');
		assert.equal(await runCheck({ argv: ['--from', build(node()), '--feed', file, '--decision', decision], fetchImpl, sink }), 0, sink.log.join('\n'));
	});

	test('an unknown option is a usage error', async () => {
		const sink = { log: [] };
		assert.equal(await runCheck({ argv: ['--nope'], sink }), 2);
	});
});

describe('the decision is jmrp.io\'s own', () => {
	const JMRP = '/var/www/jmrp.io/scripts/ci/software-drift-decision.mjs';

	test('the copy is jmrp.io\'s two blocks, verbatim, against the jmrp.io repository on this machine', { skip: !existsSync(JMRP) && 'the jmrp.io repository is not on this machine' }, () => {
		assert.deepEqual(decisionBlocks(COPY), decisionBlocks(readFileSync(JMRP, 'utf8')));
	});

	test('the copy holds the two blocks and nothing else of jmrp.io\'s', () => {
		const [first, second] = decisionBlocks(COPY);
		assert.ok(COPY.endsWith(`${first}\n${second}`), 'something stands between or after the two blocks');
		assert.equal(COPY.includes('export function projectValues'), false);
	});

	test('the blocks are cut where the copy says: from the comment above ACCEPTED_DIVERGENCES through CONTRADICTABLE, and from the comment above LIST_PROPERTIES through classifyDivergences', () => {
		const [first, second] = decisionBlocks(`// header\n${COPY}\nexport function after() {}\n`);
		assert.match(first, /^\/\*\*\n \* Divergences the author decided to keep[\s\S]*\nexport const CONTRADICTABLE = Object\.freeze\(\[[\s\S]*?\]\);\n$/);
		assert.match(second, /^\/\*\*\n \* Properties whose text can name several items[\s\S]*\nexport function classifyDivergences\([\s\S]*\n\}\n$/);
		assert.throws(() => decisionBlocks(COPY.replace('export function classifyDivergences(', 'export function classify(')), /it holds no block from "Properties whose text can name several items" to the end of classifyDivergences/);
	});
});

describe('docs.yml runs the check after the build', () => {
	const workflow = readFileSync(new URL('../../.github/workflows/docs.yml', import.meta.url), 'utf8');
	const steps = workflow.split(/\n(?= {6}- name: )/);
	const at = (pattern) => steps.findIndex((step) => pattern.test(step));

	test('one step, id software-drift, in site/, after the build', () => {
		const step = at(/\n {8}id: software-drift\n/);
		assert.ok(step !== -1, 'no step with id software-drift');
		assert.match(steps[step], /\n {8}run: pnpm run check:software-drift\n {8}working-directory: site/);
		assert.ok(step > at(/\n {8}id: build\n/), 'the check runs before the build it reads');
	});

	test('after every other check of the build and before the hand-off, so a red here still shows them all (F78)', () => {
		const step = at(/\n {8}id: software-drift\n/);
		const handOff = at(/^ {6}- name: Find the pages IndexNow was last sent\n/);
		assert.ok(handOff !== -1, 'no IndexNow step to hand the build on');
		assert.ok(step < handOff, 'the check runs after the build is handed on');
		const others = steps.map((text, index) => ({ text, index })).filter(({ text, index }) => index < handOff && /\n {8}run: pnpm run check:(?!software-drift\b)/.test(text));
		assert.ok(others.length > 5, `only ${others.length} other checks found before the hand-off`);
		for (const { text, index } of others) assert.ok(index < step, `"${text.split('\n')[0].trim()}" runs after the drift check, and a red there would skip it`);
	});

	test('the package script runs this check', () => {
		const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
		assert.equal(pkg.scripts['check:software-drift'], 'node scripts/check-software-drift.mjs');
	});
});
