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
 */
import { getEntry } from 'astro:content';

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

/** Every catalogue page of `lang`, in the order the sidebar lists them. */
export async function cataloguePages(lang: 'en' | 'es'): Promise<CataloguePage[]> {
	return Promise.all(
		catalogueSlugs.map(async (path) => {
			const id = `${lang === 'es' ? 'es/' : ''}${path}`;
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
}
