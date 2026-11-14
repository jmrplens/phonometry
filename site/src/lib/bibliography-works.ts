/**
 * The works each language's bibliography describes, read once per build.
 *
 * Every page names the works it cites from its own frontmatter, and the
 * bibliography page describes them all, from every page of its language
 * (src/lib/citations.mjs, `citedWorks`). An errata page cites nothing and
 * still names the works it corrects (`correctedWorks`), so it reads them from
 * the bibliography's set of works. Read on every errata page, that set would
 * walk every page's references again each time; it is read once per language
 * here instead, and the bibliography page reads the same one.
 */
import { getCollection, type CollectionEntry } from 'astro:content';

import { citedWorks } from './citations.mjs';

/** One page's `references`, as the citation helpers take them. */
export interface PageReferences {
	id: string;
	references: object[];
}

let everyPage: Promise<PageReferences[]> | undefined;
const byLanguage = new Map<string, Promise<Map<string, object>>>();

/** Every page of the site with its frontmatter `references`, both languages. */
export function referencesOfEveryPage(): Promise<PageReferences[]> {
	const pages =
		everyPage ??
		getCollection('docs').then((docs: CollectionEntry<'docs'>[]) =>
			docs.map((entry) => ({
				id: entry.id,
				references: (entry.data as { references?: object[] }).references ?? [],
			})),
		);
	everyPage = pages;
	return pages;
}

/**
 * Every work one language's pages cite, by its `@id` on that language's
 * bibliography, with the reference whose note describes it.
 *
 * Only that language's pages. The `@id`s are per language (they hang off the
 * bibliography's URL), and the `note` that becomes each node's `description`
 * is written in the page's own language, so mixing the two puts Spanish prose
 * on the English works. `citedWorks` fails the build when two of those pages
 * describe one work differently, which is what lets every other page name a
 * work from its own references and still say what the bibliography says.
 *
 * @param lang The language.
 * @param bibliographyUrl Absolute URL of that language's bibliography.
 */
export function bibliographyWorks(lang: 'en' | 'es', bibliographyUrl: string): Promise<Map<string, object>> {
	let works = byLanguage.get(bibliographyUrl);
	if (!works) {
		works = referencesOfEveryPage().then((pages) =>
			citedWorks(
				pages.filter((page) => (page.id === 'es' || page.id.startsWith('es/')) === (lang === 'es')),
				bibliographyUrl,
			),
		);
		byLanguage.set(bibliographyUrl, works);
	}
	return works;
}
