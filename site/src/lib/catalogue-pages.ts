/**
 * The published catalogues as pages: what the catalogue finder offers, what
 * the overview lists and where a link to the old single page is sent.
 *
 * Every catalogue used to be a section of `/reference/catalogues/`, and the
 * finder read its options out of that page. Each one is a page of its own now
 * (src/data/topics.mjs says why), so the finder on any of them has to know the
 * others without having them in the document. This reads them off the pages
 * themselves at build time, in the order `catalogueSlugs` gives: the label is
 * the page's sidebar label, which is the heading its section had, and the
 * catalogues it shows are the `<Catalogues catalogue="...">` it renders, which
 * is also how the row count is known. Nothing here keeps a second list of
 * names, labels or keys to fall out of step with the pages.
 *
 * The order is the one list, so the build holds it to the pages both ways. A
 * page under `reference/catalogues/` that `catalogueSlugs` does not name would
 * build, reach the sitemap and the site search, and still be missing from the
 * sidebar, the finder, the overview's list and its Markdown copy, and the
 * router of old links; and a catalogue the generator writes that no page
 * renders would be rows no reader meets. Either stops the build, in each
 * language, naming the page or the key.
 *
 * The rows are held to the page's bibliography the same way. Every table a
 * page prints is claimed by one entry of its frontmatter `references`, the
 * work it was read from, through that entry's `tables`; a table no entry
 * claims, a table claimed twice, a claim on a table the page does not print
 * or a claim on a key of another work stops the build too
 * (src/lib/catalogue-sources.mjs says why), and so does a `tables` on a page
 * that is not a catalogue page, where nothing reads it.
 *
 * And each catalogue a page renders is a dataset in the page's structured
 * data (src/lib/catalogue-datasets.mjs), named and described by the page: the
 * first by its title, and by its description when it is the page's only
 * catalogue or else by the paragraph that opens the page, every later one by
 * the `##` heading it sits under and the paragraph that opens it. A first
 * catalogue of several with no paragraph before it, a later one with no
 * heading of its own, or a heading with no paragraph under it would be a
 * dataset with no name, nothing to say, or the page's words about rows it
 * does not hold, and stops the build too.
 */
import { getCollection, getEntry, type CollectionEntry } from 'astro:content';

import { basePath } from '../data/site.mjs';
import { catalogueSlugs } from '../data/topics.mjs';
import { catalogues } from '../generated/catalogues.mjs';
import { catalogueDatasets, catalogueSections } from './catalogue-datasets.mjs';
import { catalogueSourceProblems, printedTables, strayTableClaims } from './catalogue-sources.mjs';

/** What a catalogue's dataset is called and what it says it holds. */
export interface CatalogueDataset {
	/** The catalogue: `absorption`, `absorptionAreas`. */
	key: keyof typeof catalogues;
	/** Its name: the page's title, or the heading it sits under. */
	name: string;
	/** Its description: the page's when it is the page's only catalogue, or else
	    the paragraph that opens the page or its own section. */
	description: string;
}

/** One catalogue's page, in one language. */
export interface CataloguePage {
	/** Its content entry: `reference/catalogues/porous-materials`, `es/...`. */
	id: string;
	/** The last segment of its address: `porous-materials`. */
	slug: string;
	/** Its address, with the site's base path and the locale. */
	href: string;
	/** What the finder and the overview call it: the heading it had. */
	label: string;
	/** The line a search result shows, which the overview lists under it. */
	description: string;
	/** The catalogues it renders, in order: `absorption`, `absorptionAreas`. */
	keys: (keyof typeof catalogues)[];
	/** How many rows those catalogues hold between them. */
	rows: number;
	/** The dataset each of those catalogues is, in the same order. */
	datasets: CatalogueDataset[];
}

/** The overview of the catalogues, in one language: the `DataCatalog` of them all. */
export interface CatalogueOverview {
	/** Its title. */
	title: string;
	/** Its address, with the site's base path and the locale. */
	href: string;
}

/** The pages of each language, read once per build: the finder, the overview's
    list and the router all ask for them on the pages they render. The dev
    server reads them afresh, so an edited page shows at once. */
const cache = new Map<'en' | 'es', Promise<CataloguePage[]>>();

/** Every catalogue page of `lang`, in the order the sidebar lists them. */
export function cataloguePages(lang: 'en' | 'es'): Promise<CataloguePage[]> {
	if (import.meta.env.DEV) return readPages(lang);
	let pages = cache.get(lang);
	if (!pages) {
		pages = readPages(lang);
		cache.set(lang, pages);
	}
	return pages;
}

async function readPages(lang: 'en' | 'es'): Promise<CataloguePage[]> {
	const prefix = lang === 'es' ? 'es/' : '';
	/* Every page under the overview is a catalogue page, so every one has to
	   be in the list. The overview's own id is `reference/catalogues`, with no
	   slash after it, and is not caught here. */
	const listed = new Set<string>(catalogueSlugs);
	/* Typed here because `getCollection` infers `any` for the docs schema (see
	   routeData.ts). */
	const docs: CollectionEntry<'docs'>[] = await getCollection('docs');
	const strays = docs
		.map((entry) => entry.id)
		.filter((id) => id.startsWith(`${prefix}reference/catalogues/`))
		.map((id) => id.slice(prefix.length))
		.filter((path) => !listed.has(path))
		.sort();
	if (strays.length > 0) {
		throw new Error(
			`[catalogue-pages] ${strays.map((path) => `${prefix}${path}`).join(', ')} ` +
				`${strays.length === 1 ? 'is' : 'are'} under reference/catalogues/ but not listed in catalogueSlugs ` +
				'in src/data/topics.mjs. Add each catalogue page there, where the sidebar, the finder, the ' +
				"overview's list and the router of old links read it.",
		);
	}

	/* What the pages say of their sources, gathered across the language so one
	   build names every page to fix. A `tables` anywhere else is read by
	   nothing, so it is refused rather than left to look like a source. */
	const sourceProblems: string[] = strayTableClaims(
		docs
			.filter((entry) => (entry.id === 'es' || entry.id.startsWith('es/')) === (lang === 'es'))
			.map((entry) => ({ id: entry.id, references: (entry.data.references ?? []) as { tables?: string[] }[] })),
	);

	/* What stops a catalogue from being a dataset with a name and a
	   description, gathered the same way. */
	const datasetProblems: string[] = [];

	const pages = await Promise.all(
		catalogueSlugs.map(async (path) => {
			const id = `${prefix}${path}`;
			const entry = await getEntry('docs', id);
			if (!entry) {
				throw new Error(
					`[catalogue-pages] src/data/topics.mjs lists "${path}", but there is no page ${id}. ` +
						'Every catalogue has a page in both languages.',
				);
			}
			const sections = catalogueSections(entry.body ?? '');
			const keys = sections.map(({ key }) => key);
			const unknown = keys.filter((key) => !(key in catalogues));
			if (keys.length === 0 || unknown.length > 0) {
				throw new Error(
					`[catalogue-pages] ${id} renders ${keys.length === 0 ? 'no catalogue' : `an unknown catalogue: ${unknown.join(', ')}`}.`,
				);
			}
			const known = keys as (keyof typeof catalogues)[];
			sourceProblems.push(
				...catalogueSourceProblems({
					page: id,
					references: (entry.data.references ?? []) as { tables?: string[] }[],
					tables: printedTables(known.map((key) => catalogues[key])),
				}),
			);
			const { datasets, problems } = catalogueDatasets({
				id,
				title: entry.data.title,
				description: entry.data.description ?? '',
				sections,
			});
			datasetProblems.push(...problems);
			return {
				id,
				slug: path.split('/').at(-1) ?? path,
				href: `${basePath}/${id}/`,
				label: entry.data.sidebar?.label ?? entry.data.title,
				description: entry.data.description ?? '',
				keys: known,
				rows: known.reduce((total, key) => total + catalogues[key].rows.length, 0),
				datasets: datasets as CatalogueDataset[],
			};
		}),
	);

	if (sourceProblems.length > 0) {
		throw new Error(
			`[catalogue-pages] the ${lang === 'es' ? 'Spanish' : 'English'} catalogue pages do not name the source ` +
				`of every table they print, in ${sourceProblems.length} place(s):\n  ${sourceProblems.join('\n  ')}\n` +
				'Give each catalogue page a `references` entry for every work its tables were read from, and list ' +
				'in that entry\'s `tables` the keys of the tables it printed (the `table` of each row in ' +
				'src/generated/catalogues.mjs), the same on the English page and its Spanish twin.',
		);
	}

	if (datasetProblems.length > 0) {
		throw new Error(
			`[catalogue-pages] the ${lang === 'es' ? 'Spanish' : 'English'} catalogue pages leave a catalogue ` +
				`without a name or a description for its dataset, in ${datasetProblems.length} place(s):\n  ` +
				`${datasetProblems.join('\n  ')}\n` +
				'The first catalogue a page renders takes the page\'s title, and its description too unless the ' +
				'page renders more than one, when the paragraph that opens the page describes it; give every ' +
				'later one a `##` heading of its own, after the catalogue before it, and open its section with ' +
				'a paragraph that says what it holds.',
		);
	}

	/* And every catalogue the generator writes is on a page of this language. */
	const shown = new Set<string>(pages.flatMap((page) => page.keys));
	const unshown = Object.keys(catalogues).filter((key) => !shown.has(key));
	if (unshown.length > 0) {
		throw new Error(
			`[catalogue-pages] no ${lang === 'es' ? 'Spanish' : 'English'} catalogue page renders ` +
				`${unshown.join(', ')}. Render each with <Catalogues catalogue="..."> on a page under ` +
				`${prefix}reference/catalogues/ (a page of its own, listed in catalogueSlugs, or the page it ` +
				'belongs beside), and add its key to the union in src/components/Catalogues.astro.',
		);
	}
	return pages;
}

/** The overview of the catalogues of `lang`, which lists them all. */
export async function catalogueOverview(lang: 'en' | 'es'): Promise<CatalogueOverview> {
	const id = `${lang === 'es' ? 'es/' : ''}reference/catalogues`;
	const entry = await getEntry('docs', id);
	if (!entry) throw new Error(`[catalogue-pages] there is no page ${id}, the overview of the catalogues.`);
	return { title: entry.data.title, href: `${basePath}/${id}/` };
}
