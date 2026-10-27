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
 */
import { getCollection, getEntry, type CollectionEntry } from 'astro:content';

import { basePath } from '../data/site.mjs';
import { catalogueSlugs } from '../data/topics.mjs';
import { catalogues } from '../generated/catalogues.mjs';

/** One catalogue's page, in one language. */
export interface CataloguePage {
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
}

/** The catalogues a page renders, read off its source in order. */
const KEYS = /<Catalogues\s+catalogue="(\w+)"/g;

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
			const keys = [...(entry.body ?? '').matchAll(KEYS)].map(([, key]) => key);
			const unknown = keys.filter((key) => !(key in catalogues));
			if (keys.length === 0 || unknown.length > 0) {
				throw new Error(
					`[catalogue-pages] ${id} renders ${keys.length === 0 ? 'no catalogue' : `an unknown catalogue: ${unknown.join(', ')}`}.`,
				);
			}
			const known = keys as (keyof typeof catalogues)[];
			return {
				slug: path.split('/').at(-1) ?? path,
				href: `${basePath}/${id}/`,
				label: entry.data.sidebar?.label ?? entry.data.title,
				description: entry.data.description ?? '',
				keys: known,
				rows: known.reduce((total, key) => total + catalogues[key].rows.length, 0),
			};
		}),
	);

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
