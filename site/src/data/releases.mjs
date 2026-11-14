/**
 * The conformance report as archived with each release.
 *
 * The report page renders the report of the code the site documents, which
 * moves with every change to main. A release freezes one: Zenodo mints a DOI
 * for the version's archive, and the report it holds is the one that release
 * was checked against. Each row here is one such release, newest first, and
 * the report page lists them as the archived reports; while the list is empty
 * the page shows nothing for it.
 *
 * A row is added by hand once Zenodo has minted the version's DOI, never
 * before: a DOI that does not resolve yet is a dead link on the page.
 *
 * @type {ReadonlyArray<Readonly<{ version: string, doi: string, date: string }>>}
 *   `version` as VERSION writes it ("4.0.0"), `doi` bare ("10.5281/zenodo.123"),
 *   `date` the day the release was published, ISO 8601 ("2026-11-30").
 */
export const releases = Object.freeze([]);
