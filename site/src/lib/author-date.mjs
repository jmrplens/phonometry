/**
 * A work named by its authors and its year, the way a reader of the page
 * sees it named: "Schroeder 1962", "Chen & Millero 1977" ("Chen y Millero"
 * in Spanish), "Kuttruff et al. 2009".
 *
 * The header chips name the articles and books a page is based on this way
 * (src/lib/reference-chips.ts), and so does the "Verified by" line under the
 * title when a check is based on one of them (src/lib/conformance-evidence.mjs),
 * so the two cannot name one work two ways on the same page.
 */

/**
 * The surname of an APA-formatted name: "Schroeder, M. R." is "Schroeder".
 *
 * @param {string} author
 * @returns {string}
 */
export function surname(author) {
	return author.split(',')[0].trim();
}

/**
 * The authors and the year of a work, or undefined when it names no author.
 *
 * @param {readonly string[] | undefined} authors APA-formatted names, one per author.
 * @param {number | string | undefined} year
 * @param {boolean} isEs Whether the page is Spanish, which joins two names with "y".
 * @returns {string | undefined}
 */
export function authorDate(authors, year, isEs) {
	if (!authors?.length) return undefined;
	const names =
		authors.length === 1
			? surname(authors[0])
			: authors.length === 2
				? `${surname(authors[0])} ${isEs ? 'y' : '&'} ${surname(authors[1])}`
				: `${surname(authors[0])} et al.`;
	return year === undefined ? names : `${names} ${year}`;
}
