/**
 * The works each page of the content tree cites, read from its frontmatter
 * outside the build.
 *
 * Inside the build a page's `references` come from the content collection.
 * Two things that run outside it need them too: the history reading that
 * dates a guide by the "Verified by" line it shows (src/lib/content-dates.mjs,
 * which the sitemap step also runs, after the build), and the check that
 * holds the conformance report's Dataset to the works its checks are based
 * on (scripts/check-structured-data.mjs). Both read them here, with the
 * parser the content collection reads them with (`parseFrontmatter`, which
 * @astrojs/markdown-remark exports from Astro's own helpers), so neither can
 * read a frontmatter otherwise than the page it stands for.
 *
 * Nothing here starts a process; the files are read from disk as they stand.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

import { routeOf } from './page-markdown.mjs';

/** The pages of a content tree, as paths below it. */
function pagesUnder(dir, out = []) {
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		const path = join(dir, entry.name);
		if (entry.isDirectory()) pagesUnder(path, out);
		else if (/\.mdx?$/.test(entry.name)) out.push(path);
	}
	return out;
}

/** The parser, loaded once and only by a caller that needs it: it brings Astro's Markdown pipeline with it. */
let parser;

/**
 * Every page of `contentDir` with the references its frontmatter cites.
 *
 * @param {string} contentDir The content tree, `src/content/docs`.
 * @param {{ parseFrontmatter?: Function }} [options] The parser, when the caller
 *   has it already: a remark plugin the site build runs (src/lib/remark-bibliography.mjs)
 *   imports it with the configuration, since a module the build loaded cannot
 *   import one later.
 * @returns {Promise<Array<{ file: string, path: string, id: string, title?: string, lang: 'en' | 'es', references: object[] }>>}
 *   `file` is the page's absolute path and `path` the same below the tree,
 *   with forward slashes; `id` is the content entry's id, the path without its
 *   extension or a closing `index` (`routeOf`), and `title` the page's own; a
 *   page under `es/` is Spanish. A page with no `references` cites none.
 */
export async function readPageReferences(contentDir, { parseFrontmatter: given } = {}) {
	const parseFrontmatter =
		given ?? (await (parser ??= import('@astrojs/markdown-remark').then((module) => module.parseFrontmatter)));
	return pagesUnder(contentDir)
		.sort()
		.map((file) => {
			const path = relative(contentDir, file).split(sep).join('/');
			const { frontmatter } = parseFrontmatter(readFileSync(file, 'utf8'));
			const references = Array.isArray(frontmatter.references) ? frontmatter.references : [];
			const title = typeof frontmatter.title === 'string' ? frontmatter.title : undefined;
			return { file, path, id: routeOf(path), title, lang: path.startsWith('es/') ? 'es' : 'en', references };
		});
}

/**
 * What a page gives the bibliography, read off one version of its text: the
 * works its frontmatter cites and, when it cites any and `titles` holds, its
 * title, as one string; empty for a page that cites nothing. The history
 * reading dates the bibliography by it (src/lib/content-dates.mjs, a text of
 * `"frontmatter": "references"`, or `"works"` without the titles), so only a
 * commit that changed it for some page moves the bibliography. The Spanish
 * bibliography reads the English pages without their titles: it names no
 * English page, and reads each English page only for the works it cites. A
 * version whose frontmatter does not parse is read whole, so any change to
 * it counts.
 *
 * @param {{ titles?: boolean }} [options]
 * @returns {Promise<(text: string) => string>}
 */
/**
 * The fields of a cited reference the bibliography shows or publishes. A
 * page's own marks on it (`primary`, `implemented`, `tables`) reach no entry,
 * and its `note` only describes a work src/data/bibliography.mjs holds no
 * note for, so a change to them moves no bibliography date.
 */
function shownFields(ref, { works, referenceId }) {
	if (ref === null || typeof ref !== 'object' || Array.isArray(ref)) return ref;
	const { primary, implemented, tables, ...shown } = ref;
	if (shown.note !== undefined && typeof shown.type === 'string') {
		const id = referenceId(shown, '');
		if (works[id.slice(id.indexOf('#') + 1)]?.note !== undefined) delete shown.note;
	}
	return shown;
}

export async function citationReader({ titles = true } = {}) {
	const parseFrontmatter = await (parser ??= import('@astrojs/markdown-remark').then((module) => module.parseFrontmatter));
	// Read when the history is read, not when a page imports this module: the
	// pages that read their references here show none of the bibliography's data.
	const { BIBLIOGRAPHY_WORKS: works } = await import('../data/bibliography.mjs');
	const { referenceId } = await import('./citations.mjs');
	return (text) => {
		let frontmatter;
		try {
			({ frontmatter } = parseFrontmatter(text));
		} catch {
			return `unparsed\n${text}`;
		}
		const cited = Array.isArray(frontmatter?.references) ? frontmatter.references : [];
		if (cited.length === 0) return '';
		const references = cited.map((ref) => shownFields(ref, { works, referenceId }));
		return JSON.stringify(titles ? { title: frontmatter.title, references } : { references });
	};
}
