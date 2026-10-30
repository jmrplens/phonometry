/**
 * What a page's "Verified by" line states, for the `Verified:` line of its
 * Markdown copy: the same join of the conformance report to the works the page
 * implements that src/components/VerifiedBy.astro draws (src/lib/page-evidence.ts
 * hands it the docs collection; this hands it the pages read from disk).
 *
 * @module
 */
import { report } from '../../data/conformance-stats.mjs';
import { basePath, siteUrl } from '../../data/site.mjs';
import { conformanceEvidence } from '../conformance-evidence.mjs';
import { readEntries } from './content.mjs';
import { CONTENT_DIR } from './render.mjs';

/**
 * The `Verified:` provider for the copies of one content tree: each route to
 * what its page's line states, or nothing for a page that shows no line.
 *
 * @param {string} [contentDir]
 * @returns {(route: string) => { checks: number, designations: readonly string[], url: string } | undefined}
 */
export function verifiedProvider(contentDir = CONTENT_DIR) {
  const entries = readEntries('', contentDir);
  /** @type {Map<'en' | 'es', ReturnType<typeof conformanceEvidence>>} */
  const evidence = new Map();
  const byId = new Map(entries.map((entry) => [entry.id, entry]));
  const evidenceOf = (lang) => {
    if (!evidence.has(lang)) {
      const prefix = lang === 'es' ? '/es' : '';
      evidence.set(
        lang,
        conformanceEvidence({
          report,
          pages: entries
            .filter((page) => (page.id === 'es' || page.id.startsWith('es/')) === (lang === 'es'))
            .map((page) => ({ id: page.id, references: page.data.references })),
          bibliographyUrl: `${siteUrl}${basePath}${prefix}/reference/bibliography/`,
          reportPath: `${basePath}${prefix}/reference/conformance/`,
          lang,
          // The site's own tree is held to the report as the pages' line is; a
          // small tree a test hands in cites only some of its works.
          strict: contentDir === CONTENT_DIR,
        }),
      );
    }
    return evidence.get(lang);
  };
  return (route) => {
    const entry = byId.get(route);
    if (entry === undefined) return undefined;
    const lang = route === 'es' || route.startsWith('es/') ? 'es' : 'en';
    const line = evidenceOf(lang).verifiedBy(entry.data.references);
    if (!line || line.checks === 0) return undefined;
    const path = line.domains.length === 1 ? line.domains[0].path : `${basePath}${lang === 'es' ? '/es' : ''}/reference/conformance/`;
    return { checks: line.checks, designations: line.works, url: `${siteUrl}${path}` };
  };
}
