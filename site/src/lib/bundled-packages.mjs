/**
 * The packages the prerender bundle carries inside it instead of importing.
 *
 * Vite leaves a bare import out of a server bundle when the name resolves
 * from the site's root, and that resolution walks up past `site/` as Node's
 * does: a `node_modules` in any directory above the checkout counts. A home
 * directory holding cookie 0.7.2, zod 3, yaml and picomatch supplied all four
 * to a build under it, and the pages then failed to render with "The requested
 * module 'cookie' does not provide an export named 'parseCookie'", because
 * astro 7 asks for cookie 2 through its own dependency. With pnpm's isolated
 * layout nothing but the site's own dependencies resolves from `site/`, so a
 * checkout with nothing above it bundled every other package already; this
 * says so to Vite, so that the bundle is the same in any checkout.
 *
 * It is a pattern of package names, the form `resolve.noExternal` reads: every
 * name except those `site/package.json` lists. A dependency the site names
 * still resolves from `site/node_modules` before any directory above it.
 */

/** A text as a regular expression reads it literally. */
const literal = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/**
 * A regular expression that matches the name of every package `manifest`
 * (a parsed package.json) does not list among its dependencies or
 * devDependencies, and no name it lists.
 */
export function packagesNotListedIn(manifest) {
	const listed = Object.keys({ ...manifest.dependencies, ...manifest.devDependencies });
	if (listed.length === 0) return /^/;
	return new RegExp(`^(?!(?:${listed.map(literal).join('|')})$)`);
}
