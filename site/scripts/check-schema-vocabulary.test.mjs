// The findings check-schema-vocabulary.mjs exists to report, on graphs small
// enough to read.
//
// The real build only ever hands the check the structured data that passes
// it, so a check that stopped resolving a reference, lost a superclass or
// learned to accept a property outside its domain would stay green there for
// good. The two defects that prompted it are replayed here and must fail,
// their corrected shapes must pass, and each rule (supertypes, references,
// literals, roles, the exceptions) has a case of its own. The cases run on
// the committed vocabulary, so a regenerated file that lost a relation the
// site relies on fails here too, and the command itself is run on builds of
// one page to read its exit status.
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
	checkVocabulary,
	createVocabulary,
	jsonLdBlocks,
	loadVocabulary,
} from './check-schema-vocabulary.mjs';
import { VOCABULARY_PATH, compactVocabulary, serializeVocabulary } from './generate-schema-vocabulary.mjs';

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-schema-vocabulary.mjs');
const vocabulary = loadVocabulary();
const ORIGIN = 'https://docs.jmrp.io/phonometry';

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
	const failing = ['unknownType', 'unknownProperty', 'outsideDomain', 'outOfRange', 'unusedException'];
	return Object.fromEntries(
		failing.filter((kind) => findings[kind].length > 0).map((kind) => [kind, findings[kind].map((f) => f.key)]),
	);
}

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

test('the committed vocabulary is exactly what the generator writes, so nobody edited it by hand', () => {
	const text = readFileSync(VOCABULARY_PATH, 'utf8');
	const { release, source, sha256, classes, properties } = JSON.parse(text);
	assert.equal(serializeVocabulary({ release, source, sha256 }, { classes, properties }), text);
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
