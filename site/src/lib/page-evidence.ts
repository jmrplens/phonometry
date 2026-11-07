/**
 * The conformance join of the build's pages in one language
 * (src/lib/conformance-evidence.mjs), as the line under a guide's title
 * (src/components/VerifiedBy.astro) and the report's Dataset
 * (src/components/Head.astro) both read it.
 *
 * The join is made once per language, from the options of whichever page
 * asks first; both callers take it from here, so neither can hand it other
 * pages or other links and get a join that depends on which page rendered
 * first.
 */
import { getCollection, type CollectionEntry } from 'astro:content';
import { evidenceOnce } from './conformance-evidence.mjs';
import { report } from '../data/conformance-stats.mjs';
import { siteUrl } from '../data/site.mjs';

const SITE = import.meta.env.SITE ?? siteUrl;
const BASE = (import.meta.env.BASE_URL ?? '/').replace(/\/$/, '');

/** The join for the pages of `lang`, read once per build. */
export function pageEvidence(lang: 'en' | 'es') {
	const prefix = lang === 'es' ? '/es' : '';
	return evidenceOnce(lang, async () => {
		// Typed here because `getCollection` infers `any` for the docs schema
		// (see src/routeData.ts).
		const docs: CollectionEntry<'docs'>[] = await getCollection('docs');
		return {
			report,
			pages: docs
				.filter((page) => (page.id === 'es' || page.id.startsWith('es/')) === (lang === 'es'))
				.map((page) => ({ id: page.id, references: page.data.references })),
			bibliographyUrl: `${SITE}${BASE}${prefix}/reference/bibliography/`,
			reportPath: `${BASE}${prefix}/reference/conformance/`,
		};
	});
}
