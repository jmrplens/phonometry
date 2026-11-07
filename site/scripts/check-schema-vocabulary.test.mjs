// The findings check-schema-vocabulary.mjs exists to report, on graphs small
// enough to read.
//
// The real build only ever hands the check the structured data that passes
// it, so a check that stopped resolving a reference, lost a superclass or
// learned to accept a property outside its domain would stay green there for
// good. The defects that prompted it are replayed here and must fail, their
// corrected shapes must pass, and each rule (supertypes, references, untyped
// nodes, literals, roles, the exceptions, the nodes another site publishes)
// has a case of its own. The cases run on the committed vocabulary, so a
// regenerated file that lost a relation the site relies on fails here too,
// and the command itself is run on builds of one page to read its exit
// status.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import {
	DOMAIN_EXCEPTIONS,
	FAILING,
	checkVocabulary,
	createVocabulary,
	jsonLdBlocks,
	loadVocabulary,
} from './check-schema-vocabulary.mjs';
import { VOCABULARY_PATH, compactVocabulary, serializeVocabulary } from './generate-schema-vocabulary.mjs';
import { referenceNode } from '../src/lib/citations.mjs';

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-schema-vocabulary.mjs');
const vocabulary = loadVocabulary();
const ORIGIN = 'https://docs.jmrp.io/phonometry';
const PERSON_ID = 'https://jmrp.io/#person';

/**
 * The software node as the site publishes it, carrying the two properties
 * DOMAIN_EXCEPTIONS allows; without it every case would also report the two
 * exceptions as unused.
 */
const SOFTWARE = {
	'@type': 'SoftwareApplication',
	'@id': 'https://github.com/jmrplens/phonometry#software',
	name: 'phonometry',
	codeRepository: 'https://github.com/jmrplens/phonometry',
	programmingLanguage: 'Python',
};

/** One page holding one `@graph`, the software node included. */
const onePage = (graph, file = '/page/') => ({
	file,
	blocks: [{ '@context': 'https://schema.org', '@graph': [SOFTWARE, ...graph] }],
});

/** The keys of every failing finding, by kind, leaving out the empty kinds. */
function failuresOf(...pages) {
	const { findings } = checkVocabulary(pages, vocabulary);
	return Object.fromEntries(
		Object.keys(FAILING)
			.filter((kind) => findings[kind].length > 0)
			.map((kind) => [kind, findings[kind].map((f) => f.key)]),
	);
}

/** The keys of one reported kind of finding. */
const reported = (kind, ...pages) => checkVocabulary(pages, vocabulary).findings[kind].map((f) => f.key);

test('the committed vocabulary is schema.org, with the relations the site relies on', () => {
	assert.match(vocabulary.release, /^\d+\.\d+$/);
	assert.equal(vocabulary.isA('APIReference', 'CreativeWork'), true);
	assert.equal(vocabulary.isA('ItemList', 'CreativeWork'), false);
	assert.equal(vocabulary.isA('URL', 'Text'), true);
	assert.deepEqual(vocabulary.property('hasPart').range, ['CreativeWork']);
	assert.deepEqual(vocabulary.property('volumeNumber').domain, ['PublicationVolume']);
	assert.deepEqual(vocabulary.property('issueNumber').domain, ['PublicationIssue']);
	assert.equal(vocabulary.property('notAProperty'), undefined);
});

test("the committed vocabulary is in the generator's format: keys sorted, one term per line, each list sorted", () => {
	const text = readFileSync(VOCABULARY_PATH, 'utf8');
	const { release, source, sha256, classes, properties } = JSON.parse(text);
	assert.equal(serializeVocabulary({ release, source, sha256 }, { classes, properties }), text);
	// The generator sorts every list by code point and a term appears once in
	// it; the round trip above keeps a list in whatever order it is written.
	const sortedOnce = (list) => list.every((name, i) => i === 0 || list[i - 1] < name);
	for (const [name, superclasses] of Object.entries(classes)) {
		assert.ok(sortedOnce(superclasses), `classes.${name}: ${superclasses}`);
	}
	for (const [name, { range, domain, supersededBy = [] }] of Object.entries(properties)) {
		for (const [field, list] of Object.entries({ range, domain, supersededBy })) {
			assert.ok(sortedOnce(list), `properties.${name}.${field}: ${list}`);
		}
	}
});

test('inLanguage on an ItemList fails: the guides hub shipped it', () => {
	assert.deepEqual(
		failuresOf(
			onePage([
				{ '@type': 'ItemList', '@id': `${ORIGIN}/start/guides/#areas`, inLanguage: 'en', numberOfItems: 13 },
			]),
		),
		{
			outsideDomain: [
				'ItemList.inLanguage (domain BroadcastService|CommunicateAction|CreativeWork|Event|LinkRole|PronounceableText|WriteAction)',
			],
		},
	);
});

test('volumeNumber and issueNumber on a ScholarlyArticle fail: the bibliography shipped them', () => {
	assert.deepEqual(
		failuresOf(
			onePage([
				{
					'@type': 'ScholarlyArticle',
					name: 'An article',
					isPartOf: { '@type': 'Periodical', name: 'A journal' },
					volumeNumber: '64',
					issueNumber: '1',
				},
			]),
		),
		{
			outsideDomain: [
				'ScholarlyArticle.issueNumber (domain PublicationIssue)',
				'ScholarlyArticle.volumeNumber (domain PublicationVolume)',
			],
		},
	);
});

test('the article inside its issue, inside its volume, inside its periodical passes', () => {
	assert.deepEqual(
		failuresOf(
			onePage([
				{
					'@type': 'ScholarlyArticle',
					name: 'An article',
					pagination: '1-10',
					isPartOf: {
						'@type': 'PublicationIssue',
						issueNumber: '1',
						isPartOf: {
							'@type': 'PublicationVolume',
							volumeNumber: '64',
							isPartOf: { '@type': 'Periodical', name: 'A journal' },
						},
					},
				},
			]),
		),
		{},
	);
});

test("the bibliography's own writer gives every kind of reference a node the vocabulary holds", () => {
	// The bibliography pages carry what referenceNode writes, so the writer
	// itself is checked here: an article names its volume and its issue only
	// through the parts it sits in, whichever of the two its reference has.
	const bibliography = `${ORIGIN}/reference/bibliography/`;
	const journal = { type: 'article', authors: ['A. Author'], title: 'An article', journal: 'A journal' };
	const references = [
		{ label: 'both', ...journal, year: 2001, volume: 64, issue: 1, pages: '1-10', doi: '10.1000/x' },
		{ label: 'volume', ...journal, year: 2002, volume: 12 },
		{ label: 'issue', ...journal, year: 2003, issue: 4 },
		{ label: 'neither', ...journal, year: 2004 },
		{ label: 'iso', type: 'standard', designation: 'ISO 1996-1:2016', title: 'A standard', organization: 'ISO' },
		{ label: 'book', type: 'book', authors: ['B. Author'], title: 'A book', publisher: 'A press', edition: '2nd' },
		{ label: 'report', type: 'report', title: 'A report', institution: 'A lab', number: 'R-1' },
		{ label: 'web', type: 'web', title: 'A page', organization: 'A body', url: 'https://example.org/' },
	];
	const nodes = references.map((ref) => referenceNode(ref, bibliography));
	assert.deepEqual(failuresOf(onePage(nodes)), {});
	const partOf = Object.fromEntries(
		nodes.slice(0, 4).map((node, i) => {
			const chain = [];
			for (let part = node.isPartOf; part; part = part.isPartOf) chain.push(part['@type']);
			return [references[i].label, chain.join(' > ')];
		}),
	);
	assert.deepEqual(partOf, {
		both: 'PublicationIssue > PublicationVolume > Periodical',
		volume: 'PublicationVolume > Periodical',
		issue: 'PublicationIssue > Periodical',
		neither: 'Periodical',
	});
});

test('codeRepository and programmingLanguage fail on an APIReference', () => {
	assert.deepEqual(
		failuresOf(
			onePage([
				{
					'@type': 'APIReference',
					programmingModel: 'Library API',
					executableLibraryName: 'phonometry',
					programmingLanguage: { '@type': 'ComputerLanguage', name: 'Python' },
					codeRepository: 'https://github.com/jmrplens/phonometry',
				},
			]),
		),
		{
			outsideDomain: [
				'APIReference.codeRepository (domain SoftwareSourceCode)',
				'APIReference.programmingLanguage (domain SoftwareSourceCode)',
			],
		},
	);
});

test('the two exceptions pass on the software node, and each has a reason', () => {
	const { findings, excepted } = checkVocabulary([onePage([])], vocabulary);
	assert.deepEqual(findings.outsideDomain, []);
	assert.deepEqual(
		excepted.map((f) => f.key),
		['SoftwareApplication.codeRepository', 'SoftwareApplication.programmingLanguage'],
	);
	for (const reason of DOMAIN_EXCEPTIONS.values()) assert.ok(reason.length > 40, reason);
});

test('an exception no page uses any more fails, so the list cannot outlive its reason', () => {
	const bare = { '@type': 'SoftwareApplication', name: 'phonometry', codeRepository: 'https://github.com/x' };
	const page = { file: '/page/', blocks: [{ '@context': 'https://schema.org', '@graph': [bare] }] };
	assert.deepEqual(failuresOf(page), { unusedException: ['SoftwareApplication.programmingLanguage'] });
});

test('an exception covers its own type only', () => {
	assert.deepEqual(
		failuresOf(onePage([{ '@type': 'WebSite', codeRepository: 'https://github.com/x' }])),
		{ outsideDomain: ['WebSite.codeRepository (domain SoftwareSourceCode)'] },
	);
});

test('a property sits in its domain through a supertype, and through any one of several types', () => {
	assert.deepEqual(
		failuresOf(
			onePage([
				{ '@type': 'APIReference', inLanguage: 'en', wordCount: 120 },
				{ '@type': ['CollectionPage', 'TechArticle'], articleSection: 'Signal analysis' },
			]),
		),
		{},
	);
});

test('a property schema.org does not define fails, and so does a type it does not define', () => {
	assert.deepEqual(
		failuresOf(onePage([{ '@type': 'TechArticle', governingWorks: [] }, { '@type': 'TechArticles', name: 'x' }])),
		{
			unknownType: ['@type TechArticles'],
			unknownProperty: ['TechArticle.governingWorks'],
			outsideDomain: ['TechArticles.name (domain Thing)'],
		},
	);
});

test('a node value of a type outside the range fails', () => {
	assert.deepEqual(
		failuresOf(onePage([{ '@type': 'CollectionPage', hasPart: { '@type': 'ItemList', '@id': `${ORIGIN}/#list` } }])),
		{ outOfRange: ['CollectionPage.hasPart = ItemList (range CreativeWork)'] },
	);
});

test('a subtype of a range class passes, and one fitting type among several is enough', () => {
	assert.deepEqual(
		failuresOf(
			onePage([
				{
					'@type': 'CollectionPage',
					hasPart: [{ '@type': 'TechArticle' }, { '@type': ['WebAPI', 'SoftwareApplication'] }],
					mainEntity: { '@type': 'ItemList' },
				},
			]),
		),
		{},
	);
});

test('a bare @id is held to the types its node has on the page, then anywhere in the build', () => {
	const list = { '@type': 'ItemList', '@id': `${ORIGIN}/x/#list` };
	const article = { '@type': 'TechArticle', '@id': `${ORIGIN}/x/#article` };
	const refersTo = (id) => ({ '@type': 'CollectionPage', hasPart: { '@id': id } });
	assert.deepEqual(failuresOf(onePage([list, refersTo(list['@id'])])), {
		outOfRange: ['CollectionPage.hasPart = ItemList (range CreativeWork)'],
	});
	assert.deepEqual(failuresOf(onePage([article, refersTo(article['@id'])])), {});
	assert.deepEqual(failuresOf(onePage([list], '/x/'), onePage([refersTo(list['@id'])], '/y/')), {
		outOfRange: ['CollectionPage.hasPart = ItemList (range CreativeWork)'],
	});
});

test('a reference to no typed node is reported, not failed', () => {
	const page = onePage([{ '@type': 'CollectionPage', hasPart: { '@id': `${ORIGIN}/nowhere/` } }]);
	assert.deepEqual(failuresOf(page), {});
	assert.deepEqual(
		checkVocabulary([page], vocabulary).findings.unresolvedReference.map((f) => f.key),
		[`CollectionPage.hasPart -> ${ORIGIN}/nowhere/`],
	);
});

test('a node with no type of its own is held to the types its @id has, and fails on what they do not take', () => {
	const website = { '@type': 'WebSite', '@id': `${ORIGIN}/#website`, name: 'phonometry' };
	const article = (isPartOf) => ({ '@type': 'TechArticle', '@id': `${ORIGIN}/start/guides/#article`, isPartOf });
	assert.deepEqual(
		failuresOf(onePage([website, article({ '@id': website['@id'], dateModifed: 'x', volumeNumber: '3' })])),
		{
			unknownProperty: ['WebSite.dateModifed'],
			outsideDomain: ['WebSite.volumeNumber (domain PublicationVolume)'],
		},
	);
	assert.deepEqual(failuresOf(onePage([website, article({ '@id': website['@id'], name: 'phonometry' })])), {});
	assert.deepEqual(
		failuresOf(onePage([website], '/x/'), onePage([article({ '@id': website['@id'], volumeNumber: '3' })], '/y/')),
		{ outsideDomain: ['WebSite.volumeNumber (domain PublicationVolume)'] },
	);
});

test("a node with properties and no type anywhere fails, unless its @id is another site's", () => {
	const holding = (isPartOf) => onePage([{ '@type': 'TechArticle', isPartOf }]);
	assert.deepEqual(failuresOf(holding({ name: 'A journal' })), {
		untypedNode: ['TechArticle.isPartOf = a node {name}'],
	});
	assert.deepEqual(failuresOf(holding({ '@id': `${ORIGIN}/nowhere/#x`, name: 'A journal' })), {
		untypedNode: [`TechArticle.isPartOf = ${ORIGIN}/nowhere/#x {name}`],
	});
	const elsewhere = holding({ '@id': 'https://example.org/#journal', name: 'A journal' });
	assert.deepEqual(failuresOf(elsewhere), {});
	assert.deepEqual(reported('unresolvedReference', elsewhere), ['TechArticle.isPartOf -> https://example.org/#journal']);
	// A @context is not data, whatever terms it defines.
	const context = {
		file: '/page/',
		blocks: [{ '@context': { '@vocab': 'https://schema.org/', ex: 'https://example.org/' }, '@graph': [SOFTWARE] }],
	};
	assert.deepEqual(failuresOf(context), {});
});

test('on the node another site publishes, and every node in it, only a range fails; the rest is reported', () => {
	const person = (extra) => ({
		'@type': 'Person',
		'@id': PERSON_ID,
		name: 'A maintainer',
		inLanguage: 'en',
		dateModifed: '2026-10-29',
		alumniOf: { '@type': ['EducationalOrganization', 'CollegeOrUniversityy'], name: 'A university' },
		owns: { '@type': 'SoftwareApplication', '@id': `${ORIGIN}/#owned`, volumeNumber: '3' },
		knowsAbout: { '@id': `${ORIGIN}/#nothing`, name: 'A topic' },
		...extra,
	});
	const page = onePage([person({})]);
	assert.deepEqual(failuresOf(page), {});
	assert.deepEqual(reported('elsewhere', page), [
		'a property schema.org does not define: Person.dateModifed',
		'a type schema.org does not define: @type CollegeOrUniversityy',
		`no type: Person.knowsAbout = ${ORIGIN}/#nothing {name}`,
		'outside its domain: Person.inLanguage (domain BroadcastService|CommunicateAction|CreativeWork|Event|LinkRole|PronounceableText|WriteAction)',
		'outside its domain: SoftwareApplication.volumeNumber (domain PublicationVolume)',
	]);
	assert.deepEqual(failuresOf(onePage([person({ alumniOf: { '@type': 'Place', name: 'A city' } })])), {
		outOfRange: ['Person.alumniOf = Place (range EducationalOrganization|Organization)'],
	});
});

test("the project's own nodes fail, whatever @id the nodes nested in them carry", () => {
	const software = {
		...SOFTWARE,
		volumeNumber: '3',
		about: { '@type': 'Thing', '@id': 'http://www.wikidata.org/entity/Q193040', issueNumber: '1' },
	};
	const page = { file: '/page/', blocks: [{ '@context': 'https://schema.org', '@graph': [software] }] };
	assert.deepEqual(failuresOf(page), {
		outsideDomain: [
			'SoftwareApplication.volumeNumber (domain PublicationVolume)',
			'Thing.issueNumber (domain PublicationIssue)',
		],
	});
	assert.deepEqual(reported('elsewhere', page), []);
});

test('a literal stands for Text in any range, and is still held to the domain', () => {
	assert.deepEqual(
		failuresOf(
			onePage([
				{
					'@type': 'CreativeWork',
					author: 'A name as plain text',
					hasPart: 'a string',
					dateModified: '2026-10-29',
					position: 3,
					description: { '@value': 'texto', '@language': 'es' },
				},
			]),
		),
		{},
	);
	assert.deepEqual(failuresOf(onePage([{ '@type': 'ItemList', wordCount: 3 }])), {
		outsideDomain: ['ItemList.wordCount (domain Article|CreativeWork)'],
	});
});

test('a Role stands in for the value it qualifies, and carries that property outside its domain', () => {
	assert.deepEqual(
		failuresOf(
			onePage([
				{
					'@type': 'Person',
					hasOccupation: [
						{ '@type': 'Occupation', name: 'Firmware engineer' },
						{
							'@type': 'Role',
							startDate: '2019',
							endDate: '2023',
							hasOccupation: { '@type': 'Occupation', name: 'Acoustics researcher' },
						},
					],
				},
			]),
		),
		{},
	);
});

test('a Role is still held to the domain for any property other than the one it qualifies', () => {
	assert.deepEqual(
		failuresOf(
			onePage([
				{
					'@type': 'Person',
					hasOccupation: {
						'@type': 'Role',
						hasOccupation: { '@type': 'Occupation', name: 'Acoustics researcher' },
						worksFor: { '@type': 'Organization', name: 'A university' },
					},
				},
			]),
		),
		{ outsideDomain: ['Role.worksFor (domain Person)'] },
	);
});

test('nested nodes are checked, not only the nodes at the top of the graph', () => {
	assert.deepEqual(
		failuresOf(
			onePage([
				{
					'@type': 'WebPage',
					mainEntity: {
						'@type': 'ItemList',
						itemListElement: {
							'@type': 'ListItem',
							item: { '@type': 'CreativeWork', hasPart: { '@type': 'Place' } },
						},
					},
				},
			]),
		),
		{ outOfRange: ['CreativeWork.hasPart = Place (range CreativeWork)'] },
	);
});

test('a superseded property is reported, not failed', () => {
	const page = onePage([{ '@type': 'CreativeWork', fileFormat: 'text/html' }]);
	assert.deepEqual(failuresOf(page), {});
	assert.deepEqual(
		checkVocabulary([page], vocabulary).findings.superseded.map((f) => f.key),
		['CreativeWork.fileFormat -> encodingFormat'],
	);
});

test('jsonLdBlocks reads every block, wherever the type attribute sits', () => {
	const html =
		'<head><script nonce="n" type="application/ld+json">{"@type":"WebSite"}</script>' +
		'<script type="application/ld+json" data-x="1">[{"@type":"Person"}]</script>' +
		'<script type="application/ld+json">{broken</script>' +
		'<script type="module">{"@type":"Nope"}</script></head>';
	const { blocks, errors } = jsonLdBlocks(html);
	assert.deepEqual(blocks, [{ '@type': 'WebSite' }, [{ '@type': 'Person' }]]);
	assert.equal(errors.length, 1);
	assert.match(errors[0], /block 3 is not valid JSON/);
});

test('the generator keeps superclasses, ranges, domains and supersession, and reads back', () => {
	const graph = [
		{ '@id': 'schema:Thing', '@type': 'rdfs:Class' },
		{ '@id': 'schema:CreativeWork', '@type': 'rdfs:Class', 'rdfs:subClassOf': { '@id': 'schema:Thing' } },
		{ '@id': 'schema:Text', '@type': ['schema:DataType', 'rdfs:Class'] },
		{ '@id': 'schema:URL', '@type': 'rdfs:Class', 'rdfs:subClassOf': { '@id': 'schema:Text' } },
		{
			'@id': 'schema:hasPart',
			'@type': 'rdf:Property',
			'schema:domainIncludes': { '@id': 'schema:CreativeWork' },
			'schema:rangeIncludes': { '@id': 'schema:CreativeWork' },
		},
		{
			'@id': 'schema:oldProp',
			'@type': 'rdf:Property',
			'schema:rangeIncludes': [{ '@id': 'schema:URL' }, { '@id': 'schema:Text' }],
			'schema:supersededBy': { '@id': 'schema:hasPart' },
		},
		// An enumeration member and a term of another vocabulary: neither is
		// something the check reads.
		{ '@id': 'schema:Monday', '@type': 'schema:DayOfWeek' },
		{ '@id': 'bibo:Thesis', '@type': 'rdfs:Class' },
	];
	const compact = compactVocabulary(graph);
	assert.deepEqual(compact, {
		classes: { Thing: [], CreativeWork: ['Thing'], Text: [], URL: ['Text'] },
		properties: {
			hasPart: { range: ['CreativeWork'], domain: ['CreativeWork'] },
			oldProp: { range: ['Text', 'URL'], domain: [], supersededBy: ['hasPart'] },
		},
	});
	const parsed = JSON.parse(serializeVocabulary({ release: '1.0', source: 's', sha256: 'h' }, compact));
	assert.equal(parsed.release, '1.0');
	const round = createVocabulary(parsed);
	assert.equal(round.isA('URL', 'Text'), true);
	assert.deepEqual(round.property('oldProp').supersededBy, ['hasPart']);
});

/**
 * Writes a build of one page whose head carries `graph` as Astro writes it,
 * runs the check on it, and says how it ended. `graph` null writes no page.
 */
function check(t, graph) {
	const dist = mkdtempSync(join(tmpdir(), 'check-schema-vocabulary-'));
	t.after(() => rmSync(dist, { recursive: true, force: true }));
	if (graph) {
		const block = JSON.stringify({ '@context': 'https://schema.org', '@graph': [SOFTWARE, ...graph] });
		writeFileSync(
			join(dist, 'index.html'),
			`<!DOCTYPE html><html lang="en"><head><script type="application/ld+json">${block}</script></head><body></body></html>`,
		);
	}
	const ran = spawnSync(process.execPath, [CHECK, dist], { encoding: 'utf8' });
	return { status: ran.status, out: ran.stdout, err: ran.stderr };
}

test('the command exits 0 on a clean build', (t) => {
	const ran = check(t, [{ '@type': 'CollectionPage', hasPart: { '@type': 'TechArticle' } }]);
	assert.equal(ran.status, 0, ran.out + ran.err);
	assert.match(ran.out, /SoftwareApplication\.codeRepository is outside its domain on 1 page, on purpose/);
});

test('the command exits 1 and names the property on a build with the defect', (t) => {
	const ran = check(t, [{ '@type': 'ItemList', inLanguage: 'en' }]);
	assert.equal(ran.status, 1, ran.out + ran.err);
	assert.match(ran.err, /ItemList\.inLanguage \(domain [^)]*CreativeWork[^)]*\), on 1 page, e\.g\. \//);
});

test('the command exits 2, not 1, when there is no build to read', (t) => {
	const ran = check(t, null);
	assert.equal(ran.status, 2, ran.out + ran.err);
	assert.match(ran.err, /holds no index\.html/);
});
