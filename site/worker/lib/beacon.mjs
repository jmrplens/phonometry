// The beacon: the script the staged pages carry, what the Worker accepts
// from it, and the data point a page view becomes.
//
// Pages are plain assets and never run code, so the page view a browser
// reports is the only way to count it. After `load` the script posts one
// small JSON object to /_v of the page's own origin with navigator.sendBeacon
// (a same-origin text/plain POST: no preflight, and the pages' policies
// already allow it through connect-src falling back to default-src 'self').
// It sends everything it reads and opts nobody out: an automated browser is
// flagged (`wd`), not skipped, so the preview's own browser checks are
// visible and can be filtered. A prerendered page reports when it is shown;
// a page restored from the back/forward cache does not run it again.

import { BASE_PATH, agentPaths, patternsSource } from './agent-paths.mjs';
import { logEdgeRequest } from './edge-log.mjs';

/** The largest beacon body the Worker reads; a real one is about 300 bytes. */
export const BEACON_MAX_BYTES = 2048;

/**
 * The inline script, minified by hand (it ships in every page of the
 * preview). `nf` is 1 in the 404 pages, written in at staging.
 *
 * A 404 page also answers a missing agent file (`/phonometry/x/index.md`),
 * and that request ran the Worker, which logged it with its 404. So the 404
 * page carries the agent paths for its base path and sends nothing when it
 * stands at one of them: the same miss is not counted twice, and the second
 * invocation is not spent.
 *
 * @param {boolean} notFound Whether the page is a 404 page.
 * @param {string} [prefix] The base path, for the agent paths a 404 page skips.
 * @returns {string} One `<script>` element.
 */
export function beaconScript(notFound, prefix = BASE_PATH) {
	const nf = notFound ? 1 : 0;
	const start = notFound ? `/${patternsSource(agentPaths(prefix))}/.test(l.pathname)||(` : '';
	const end = notFound ? ')' : '';
	return (
		'<script>(()=>{const n=navigator,d=document,l=location,s=()=>{' +
		'const t=performance.getEntriesByType("navigation")[0],a=t?.activationStart||0,' +
		'b=JSON.stringify({p:l.pathname,q:l.search.slice(1,129),r:d.referrer.slice(0,512),' +
		'n:a>0?"prerender":t?.type,t:t?Math.round(t.loadEventStart-a):-1,' +
		'w:screen.width,h:screen.height,vw:innerWidth,vh:innerHeight,dpr:devicePixelRatio,' +
		'lg:n.language,tz:Intl.DateTimeFormat().resolvedOptions().timeZone,' +
		`wd:n.webdriver?1:0,nf:${nf}});` +
		'n.sendBeacon?.("/_v",b)||fetch("/_v",{method:"POST",body:b,keepalive:!0}).catch(()=>{})},' +
		'g=()=>d.readyState=="complete"?setTimeout(s):addEventListener("load",()=>setTimeout(s),{once:!0});' +
		`${start}d.prerendering?d.addEventListener("prerenderingchange",g,{once:!0}):g()${end}})()</script>`
	);
}

const NAV_TYPES = new Set(['navigate', 'reload', 'back_forward', 'prerender']);
const text = (value, max) => (typeof value === 'string' ? value.slice(0, max) : '');
const count = (value, max) => (Number.isFinite(value) && value >= 0 && value <= max ? Math.round(value) : 0);
const flag = (value) => (value === 1 ? 1 : 0);

/**
 * A beacon body, field by field. Only the page path is required; any other
 * field of the wrong type or out of range reads as empty or zero instead of
 * losing the page view.
 *
 * @param {string} body The request body.
 * @returns {object | null} The beacon, or null when it is not one.
 */
export function parseBeacon(body) {
	let raw;
	try {
		raw = JSON.parse(body);
	} catch {
		return null;
	}
	if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) return null;
	if (typeof raw.p !== 'string' || !raw.p.startsWith('/') || raw.p.length > 512) return null;
	return {
		path: raw.p,
		query: text(raw.q, 128),
		referrer: text(raw.r, 512),
		navType: NAV_TYPES.has(raw.n) ? raw.n : '',
		loadMs: count(raw.t, 600000),
		screenWidth: count(raw.w, 100000),
		screenHeight: count(raw.h, 100000),
		viewportWidth: count(raw.vw, 100000),
		viewportHeight: count(raw.vh, 100000),
		pixelRatio: Number.isFinite(raw.dpr) && raw.dpr > 0 && raw.dpr <= 16 ? raw.dpr : 0,
		language: text(raw.lg, 35),
		timeZone: text(raw.tz, 64),
		webdriver: flag(raw.wd),
		notFound: flag(raw.nf),
	};
}

/** The eight groups of an IPv6 address, each four hex digits. */
function ipv6Groups(ip) {
	const [head, tail] = ip.includes('::') ? ip.split('::') : [ip, null];
	const left = head ? head.split(':') : [];
	const right = tail ? tail.split(':') : [];
	const fill = tail === null ? [] : Array(8 - left.length - right.length).fill('0');
	return [...left, ...fill, ...right].map((group) => group.padStart(4, '0').toLowerCase());
}

/**
 * The key of the per-address limit: an IPv4 address as it is, an IPv6 one by
 * its /56, the block an operator usually hands one household (as Antiga
 * Italia's beacon does).
 *
 * @param {string | null} ip CF-Connecting-IP.
 * @returns {string} The key.
 */
export function ipLimitKey(ip) {
	if (!ip) return 'unknown';
	if (!ip.includes(':')) return ip;
	const groups = ipv6Groups(ip);
	return `${groups.slice(0, 3).join(':')}:${groups[3].slice(0, 2)}`;
}


/**
 * The Sec-Fetch-Site the page's own navigation would have carried, from the
 * referrer the page reports: `none` with no referrer (typed, bookmarked, or a
 * referrer policy that sends none), `same-origin` from the site itself,
 * `same-site` from another host of its domain over https, `cross-site`
 * otherwise, and empty for a referrer that does not parse. A reload keeps
 * the referrer of the first load, so it reads as that load did.
 *
 * @param {string} referrer document.referrer, as the beacon sent it.
 * @param {string} host The site's host.
 * @returns {string} The value.
 */
export function pageFetchSite(referrer, host) {
	if (!referrer) return 'none';
	let from;
	try {
		from = new URL(referrer);
	} catch {
		return '';
	}
	if (from.origin === `https://${host}`) return 'same-origin';
	if (from.protocol === 'https:' && (from.hostname === host || from.hostname.endsWith(`.${host}`))) return 'same-site';
	return 'cross-site';
}

/**
 * The data point of a page view: the row docs-edge writes for the page
 * request on docs.jmrp.io, built by the same code (logEdgeRequest) from the
 * page the browser names, with the beacon's own request for everything the
 * edge knows about the visitor (address, User-Agent, location, network,
 * TLS). The page's path, query and referrer come from the beacon; its Accept
 * is unknown and left empty; the method is the page's GET; the status is 404
 * on the 404 page and 200 elsewhere. The three Sec-Fetch fields describe the
 * page's navigation, as docs-edge sees a page request (dest `document`, mode
 * `navigate`, site from the referrer: pageFetchSite), not the beacon's own
 * POST, which always reads empty, no-cors, same-origin. Blob 20 gets the beacon's navigation
 * type, 404 flag, webdriver flag, language and time zone appended after
 * docs-edge's 14 fields, and doubles 10 to 15 carry the load time, the
 * screen, the viewport and the pixel ratio: appended, never reordered, as
 * the docs-edge contract says.
 *
 * @param {object} options
 * @param {{method: string, headers: Headers, cf?: object}} options.request The beacon request.
 * @param {object} options.beacon From parseBeacon.
 * @param {string} options.host The site's host (phonometry.dev).
 * @param {number} options.startedAt When the Worker started on it (ms).
 * @param {string} options.verdict `beacon` or `beacon-limited`.
 * @returns {{indexes: string[], blobs: string[], doubles: number[]} | null} The point.
 */
export function beaconPoint({ request, beacon, host, startedAt, verdict }) {
	const headers = new Headers(request.headers);
	headers.delete('accept');
	headers.delete('referer');
	if (beacon.referrer) headers.set('referer', beacon.referrer);
	headers.set('sec-fetch-dest', 'document');
	headers.set('sec-fetch-mode', 'navigate');
	const site = pageFetchSite(beacon.referrer, host);
	if (site) headers.set('sec-fetch-site', site);
	else headers.delete('sec-fetch-site');
	const page = { method: 'GET', headers, cf: request.cf };
	let url;
	try {
		url = new URL(`https://${host}`);
		url.pathname = beacon.path;
		url.search = beacon.query;
	} catch {
		return null;
	}
	let point = null;
	logEdgeRequest({
		env: { REQS: { writeDataPoint: (p) => (point = p) } },
		request: page,
		url,
		startedAt,
		status: beacon.notFound ? 404 : 200,
		cacheStatus: verdict,
		response: null,
	});
	if (point === null) return null;
	const tail = [beacon.navType, String(beacon.notFound), String(beacon.webdriver), beacon.language.replaceAll('|', ''), beacon.timeZone.replaceAll('|', '')];
	point.blobs[19] = `${point.blobs[19]}|${tail.join('|')}`;
	point.doubles.push(beacon.loadMs, beacon.screenWidth, beacon.screenHeight, beacon.viewportWidth, beacon.viewportHeight, beacon.pixelRatio);
	return point;
}
