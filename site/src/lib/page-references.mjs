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
 * @returns {Promise<Array<{ file: string, path: string, lang: 'en' | 'es', references: object[] }>>}
 *   `file` is the page's absolute path and `path` the same below the tree,
 *   with forward slashes; a page under `es/` is Spanish. A page with no
 *   `references` cites none.
 */
export async function readPageReferences(contentDir) {
	parser ??= import('@astrojs/markdown-remark').then((module) => module.parseFrontmatter);
	const parseFrontmatter = await parser;
	return pagesUnder(contentDir)
		.sort()
		.map((file) => {
			const path = relative(contentDir, file).split(sep).join('/');
			const { frontmatter } = parseFrontmatter(readFileSync(file, 'utf8'));
			const references = Array.isArray(frontmatter.references) ? frontmatter.references : [];
			return { file, path, lang: path.startsWith('es/') ? 'es' : 'en', references };
		});
}
