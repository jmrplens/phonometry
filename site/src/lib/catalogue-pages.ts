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
 * The work is done by src/lib/catalogue-page-list.mjs, which needs no Astro,
 * so the Markdown copy of the overview lists the pages through the same
 * function; this module hands it the docs collection and keeps the result
 * for the build. The order is the one list, and that module holds it to the
 * pages both ways: a page under `reference/catalogues/` that `catalogueSlugs`
 * does not name, or a catalogue the generator writes that no page renders,
 * stops the build, in each language, naming the page or the key; so does a
 * table no entry of a page's references claims, and a catalogue with no name
 * or description for the dataset the page's structured data makes of it
 * (that module says what each of those needs).
 */
import { getCollection, getEntry, type CollectionEntry } from 'astro:content';

import { basePath } from '../data/site.mjs';
import { catalogueIndex, type CatalogueDataset, type CataloguePage } from './catalogue-page-list.mjs';

export type { CatalogueDataset, CataloguePage };

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
	/* Typed here because `getCollection` infers `any` for the docs schema (see
	   routeData.ts). */
	const docs: CollectionEntry<'docs'>[] = await getCollection('docs');
	return catalogueIndex(lang, docs);
}

/** The overview of the catalogues of `lang`, which lists them all. */
export async function catalogueOverview(lang: 'en' | 'es'): Promise<CatalogueOverview> {
	const id = `${lang === 'es' ? 'es/' : ''}reference/catalogues`;
	const entry = await getEntry('docs', id);
	if (!entry) throw new Error(`[catalogue-pages] there is no page ${id}, the overview of the catalogues.`);
	return { title: entry.data.title, href: `${basePath}/${id}/` };
}
