// Every link of the build, read the way PageSpeed Insights reads it.
//
// Lighthouse's SEO audit "Links do not have descriptive text" fails a page
// that carries a link whose whole text is a word that names no destination,
// "Start", "here" or "read more" in English, "aquí" or "más" in Spanish. The
// topic list above the sidebar linked the Start topic with the word "Start" on
// every English page, so PageSpeed Insights flagged the home page, and every
// other English page the same way, with every check of the build green.
//
// So this loads every page of the build in headless Chrome, at each of the two
// form factors PageSpeed reports, with Lighthouse's own mobile and desktop
// emulation, and runs Lighthouse's own code on it. Its AnchorElements gatherer
// collects the links: each address as the browser resolves it, each text as the
// browser shows it (innerText, so a word under the `hidden` attribute, one a
// stylesheet hides at that width and an SVG title are not read, and a link in a
// comment is no link at all) and the language of each, the closest `lang`
// around it. Its link-text audit then applies its own lists, one per language,
// and its own exclusions: a link with no address, a `javascript:` or `mailto:`
// one, a `rel="nofollow"` one and one to the page it is on. A page fails here
// exactly when the audit fails it, and there are no lists of words to keep in
// step with Lighthouse's.
//
// One shortcut. Besides the links, the gatherer asks the browser for the event
// listeners of every one, three round trips a link and half the time of the
// whole check, and the audit never reads them. The session handed to the
// gatherer answers those requests itself, with no listeners.
// check-link-text.test.mjs holds that the audit reads none, and that this
// check finds what a full Lighthouse run finds on pages made to fail it.
//
// A page is read when its load event fires. Lighthouse also waits for the
// network and the processor to go quiet, a second each by its own settings,
// which would multiply the time of this check; nothing on the site writes a
// link after the load event (the one script that shows a link, the language
// bar, runs on DOMContentLoaded).
//
// Usage: node scripts/with-preview.mjs -- node scripts/check-link-text.mjs
//        [--base <origin>] [dist-directory]
import { existsSync, readFileSync } from 'node:fs';
import { availableParallelism } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import LinkText from 'lighthouse/core/audits/seo/link-text.js';
import { screenEmulationMetrics, userAgents } from 'lighthouse/core/config/constants.js';
import { Driver } from 'lighthouse/core/gather/driver.js';
import AnchorElements from 'lighthouse/core/gather/gatherers/anchor-elements.js';
import { emulate } from 'lighthouse/core/lib/emulation.js';

import { BASE_PATH, DEFAULT_BASE, baseFrom, launchBrowser } from './shared/audit.mjs';
import { isErrorPage, isRedirectStub, reporter, walk } from './shared/dist-pages.mjs';

/** The two form factors PageSpeed Insights reports, as Lighthouse emulates them. */
export const FORM_FACTORS = {
	mobile: { formFactor: 'mobile', screenEmulation: screenEmulationMetrics.mobile, emulatedUserAgent: userAgents.mobile },
	desktop: { formFactor: 'desktop', screenEmulation: screenEmulationMetrics.desktop, emulatedUserAgent: userAgents.desktop },
};

/** The requests the gatherer makes only to read event listeners, and the answers that mean none. */
const LISTENER_ANSWERS = {
	'DOM.getDocument': {},
	'DOM.pushNodeByPathToFrontend': { nodeId: 0 },
	'DOM.resolveNode': { object: {} },
	'DOMDebugger.getEventListeners': { listeners: [] },
};

/**
 * The context the gatherer runs in: the driver's own, with a session that
 * answers the listener requests itself and passes every other one on.
 */
function gathererContext(driver) {
	const session = driver.defaultSession;
	const sendCommand = (method, ...params) =>
		Object.hasOwn(LISTENER_ANSWERS, method)
			? Promise.resolve(LISTENER_ANSWERS[method])
			: session.sendCommand(method, ...params);
	return { driver: { executionContext: driver.executionContext, defaultSession: { sendCommand } } };
}

/** An address as a reader of the report wants it: the path, when it is on the site read. */
function shown(href, base) {
	return href.startsWith(`${base}/`) ? href.slice(base.length) : href;
}

/**
 * The links Lighthouse's link-text audit fails on the given routes, at each
 * form factor.
 *
 * @param {object} options
 * @param {string} options.base The origin serving the build, `http://localhost:4321`.
 * @param {string[]} options.routes The routes to read, `/x/`, below the site's base path.
 * @param {string[]} [options.forms] The form factors, keys of FORM_FACTORS.
 * @param {number} [options.pages] How many pages are open at once.
 * @returns {Promise<{form: string, route: string, href: string, text: string, unread?: string}[]>}
 *   One entry per failing link, and one with `unread` set per page that did not load.
 */
export async function vagueLinks({ base, routes, forms = Object.keys(FORM_FACTORS), pages }) {
	const open = Math.max(forms.length, pages ?? Math.min(8, availableParallelism()));
	const perForm = Math.max(1, Math.floor(open / forms.length));
	const found = [];
	const browser = await launchBrowser();
	try {
		const worker = async (form, queue) => {
			const page = await browser.newPage();
			const driver = new Driver(page);
			await driver.connect();
			await emulate(driver.defaultSession, FORM_FACTORS[form]);
			const context = gathererContext(driver);
			for (let route = queue.shift(); route !== undefined; route = queue.shift()) {
				let response;
				try {
					response = await page.goto(`${base}${BASE_PATH}${route}`, { waitUntil: 'load' });
				} catch (error) {
					found.push({ form, route, href: '', text: '', unread: error.message });
					continue;
				}
				// A 304 is a page read before, from the browser's cache: the two
				// form factors share one browser. Only an error status means the
				// page read is not the one asked for.
				const status = response?.status() ?? 0;
				if (status === 0 || (status >= 400 && !isErrorPage(route))) {
					found.push({ form, route, href: '', text: '', unread: `HTTP ${status || 'no response'}` });
					continue;
				}
				const anchors = await new AnchorElements().getArtifact(context);
				const { details } = LinkText.audit({ URL: { finalDisplayedUrl: page.url() }, AnchorElements: anchors });
				for (const { href, text } of details.items) found.push({ form, route, href: shown(href, base), text });
			}
			await driver.disconnect();
			await page.close();
		};
		await Promise.all(
			forms.flatMap((form) => {
				const queue = [...routes];
				return Array.from({ length: perForm }, () => worker(form, queue));
			}),
		);
	} finally {
		await browser.close();
	}
	const order = (entry) => `${entry.route} ${forms.indexOf(entry.form)} ${entry.href}`;
	return found.sort((a, b) => order(a).localeCompare(order(b)));
}

/** The routes of a build that are pages, its redirect stubs left out. */
export function pageRoutes(dist) {
	return [...walk(dist)].filter(([, file]) => !isRedirectStub(readFileSync(file, 'utf8'))).map(([route]) => route);
}

const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
	const argv = process.argv.slice(2);
	const base = baseFrom(argv, DEFAULT_BASE);
	const rest = argv.filter((arg, i) => arg !== '--base' && argv[i - 1] !== '--base');
	const DIST = rest[0] ? resolve(rest[0]) : join(dirname(fileURLToPath(import.meta.url)), '..', 'dist');
	if (!existsSync(DIST)) throw new Error(`no build at ${DIST}: run \`pnpm build\` first`);

	const routes = pageRoutes(DIST);
	const started = performance.now();
	const found = await vagueLinks({ base, routes });
	const seconds = ((performance.now() - started) / 1000).toFixed(0);
	console.log(`read the links of ${routes.length} pages of ${DIST} at ${base}, as mobile and desktop, in ${seconds} s`);

	const { report, failures } = reporter();
	report(
		found.filter((entry) => entry.unread).map(({ form, route, unread }) => `${form} ${route}: ${unread}`),
		'page(s) that did not load',
		'every page loaded',
	);
	report(
		found.filter((entry) => !entry.unread).map(({ form, route, href, text }) => `${form} ${route}: a link to ${href} reads "${text}"`),
		'link(s) Lighthouse fails as naming no destination',
		'every link names where it goes',
	);
	console.log(`\n${failures()} failing check(s).`);
	process.exit(failures() ? 1 : 0);
}
