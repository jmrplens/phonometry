// Stages a site build as the asset directory of the phonometry.dev Worker.
//
// Usage (site/worker/README.md):
//   node site/worker/stage.mjs --from <build> [--out <dir>] [--site docs.jmrp.io|phonometry.dev]
//                               [--indexable] [--check]
//
// --from is a build: a local site/dist, or the unpacked github-pages artifact
// docs.yml uploads. --site names the host that build was made for (its
// PHONOMETRY_SITE; unset means docs.jmrp.io, the build docs.yml makes), and
// the base path and the canonical origin of the headers follow from it.
// --out defaults to site/worker/stage, the directory wrangler.jsonc names.
// --indexable drops the noindex every response carries while the site is a
// preview. --check runs every check and writes nothing. Exit 0 when staged
// (or the checks pass), 1 when a check fails, 2 on a usage error.
import { resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';

const usage = 'usage: node site/worker/stage.mjs --from <build> [--out <dir>] [--site <host>] [--indexable] [--check]';

let args;
try {
	args = parseArgs({
		options: {
			from: { type: 'string' },
			out: { type: 'string' },
			site: { type: 'string' },
			indexable: { type: 'boolean' },
			check: { type: 'boolean' },
		},
	}).values;
} catch (error) {
	console.error(`${error.message}\n${usage}`);
	process.exit(2);
}
if (!args.from) {
	console.error(usage);
	process.exit(2);
}
// The modules below read PHONOMETRY_SITE when they load, so it is set first.
if (args.site !== undefined) process.env.PHONOMETRY_SITE = args.site;

let site;
try {
	site = await import('../src/data/site.mjs');
} catch (error) {
	console.error(error.message);
	process.exit(2);
}
const { redirectPairs } = await import('../scripts/cloudflare-redirects.mjs');
const { stage } = await import('./lib/staging.mjs');
const { twinExclusions } = await import('./lib/twins.mjs');

const out = resolve(args.out ?? fileURLToPath(new URL('./stage', import.meta.url)));
const report = stage({
	from: resolve(args.from),
	out,
	prefix: site.basePath,
	origin: site.siteUrl,
	pairs: redirectPairs(),
	exclusions: twinExclusions(site.basePath),
	indexable: Boolean(args.indexable),
	checkOnly: Boolean(args.check),
});
for (const problem of report.problems) console.error(`FAIL ${problem}`);
if (report.problems.length > 0) process.exit(1);
console.log(
	`${args.check ? 'checked' : `staged into ${out}`}: ${report.files} files, ${report.redirects} redirects, ` +
		`${report.headerRules} header rules, origin ${site.siteUrl}, base ${site.basePath || '/'}${args.indexable ? ', indexable' : ', noindex'}`,
);
