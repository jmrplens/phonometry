// The beacon: the script the staged pages carry, what the Worker accepts
// from it, and the data point a page view becomes.
import assert from 'node:assert/strict';
import { test, describe } from 'node:test';

import { BEACON_MAX_BYTES, beaconPoint, beaconScript, ipLimitKey, pageFetchSite, parseBeacon } from '../lib/beacon.mjs';

describe('beaconScript', () => {
	test('one inline script under 1 KB, the 404 flag written in', () => {
		const page = beaconScript(false);
		const missing = beaconScript(true);
		assert.match(page, /^<script>\(\(\)=>\{.*\}\)\(\)<\/script>$/s);
		assert.ok(Buffer.byteLength(page) < 1024, `${Buffer.byteLength(page)} bytes`);
		assert.ok(Buffer.byteLength(missing) < 1024, `${Buffer.byteLength(missing)} bytes`);
		assert.match(page, /nf:0\b/);
		assert.match(missing, /nf:1\b/);
		for (const script of [page, missing]) assert.doesNotMatch(script, /\.test\(l\.pathname\)/, 'no path is skipped');
		assert.equal(missing.indexOf('</'), missing.length - '</script>'.length, 'nothing in it closes the script early');
	});

	/** Runs a beacon script in a fake page at `pathname` and returns what it sent once loaded. */
	const run = (script, pathname) => {
		const sent = [];
		const listeners = {};
		const scope = {
			navigator: { sendBeacon: (url, body) => (sent.push([url, JSON.parse(body)]), true), language: 'en', webdriver: false },
			document: { readyState: 'loading', referrer: '', prerendering: false, addEventListener() {} },
			location: { pathname, search: '' },
			performance: { getEntriesByType: () => [{ type: 'navigate', loadEventStart: 10, activationStart: 0 }] },
			screen: { width: 1, height: 1 },
			innerWidth: 1,
			innerHeight: 1,
			devicePixelRatio: 1,
			Intl: { DateTimeFormat: () => ({ resolvedOptions: () => ({ timeZone: 'UTC' }) }) },
			addEventListener: (name, fn) => (listeners[name] = fn),
			setTimeout: (fn) => fn(),
			fetch: () => Promise.resolve(),
		};
		new Function(...Object.keys(scope), script.slice('<script>'.length, -'</script>'.length))(...Object.values(scope));
		listeners.load?.();
		return sent;
	};

	test('the 404 page reports wherever it stands, a missing copy or llms file included', () => {
		// No Worker runs for a Markdown copy, an llms file or a sitemap, so
		// a browser that lands on the 404 page there is counted by the
		// beacon or not at all.
		const missing = beaconScript(true);
		const paths = ['/no-such/index.md', '/index.md', '/llms-nope.txt', '/no-such.xml', '/sitemap-nope.xml', '/robots.txt', '/no-such-page/', '/no-such-page', '/a.md', '/INDEX.MD'];
		for (const path of paths) {
			const sent = run(missing, path);
			assert.equal(sent.length, 1, path);
			assert.equal(sent[0][1].nf, 1, path);
		}
		assert.equal(run(beaconScript(false), '/signals/').length, 1, 'a page always sends');
	});

	test('it posts to the beacon path of its own origin, after load, with every field', () => {
		const script = beaconScript(false);
		assert.match(script, /sendBeacon\?\.\("\/_v",b\)/);
		assert.match(script, /fetch\("\/_v",\{method:"POST",body:b,keepalive:!0\}\)/);
		assert.match(script, /addEventListener\("load"/);
		assert.match(script, /prerenderingchange/);
		for (const key of ['p:', 'q:', 'r:', 'n:', 't:', 'w:', 'h:', 'vw:', 'vh:', 'dpr:', 'lg:', 'tz:', 'wd:', 'nf:']) assert.ok(script.includes(key), key);
	});

	test('it opts nobody out: no webdriver skip, no Do Not Track, no storage flag', () => {
		const script = beaconScript(false);
		assert.doesNotMatch(script, /doNotTrack|globalPrivacyControl|localStorage/);
		assert.match(script, /wd:n\.webdriver\?1:0/);
	});

	test('it runs as written, and sends what it read', () => {
		const sent = [];
		const listeners = {};
		const scope = {
			navigator: { sendBeacon: (url, body) => (sent.push([url, JSON.parse(body)]), true), language: 'es-ES', webdriver: false },
			document: { readyState: 'loading', referrer: 'https://example.org/a?b', prerendering: false, addEventListener() {} },
			location: { pathname: '/phonometry/signals/', search: '?x=1' },
			performance: { getEntriesByType: () => [{ type: 'navigate', loadEventStart: 420.6, activationStart: 0 }] },
			screen: { width: 1920, height: 1080 },
			innerWidth: 1280,
			innerHeight: 720,
			devicePixelRatio: 2,
			Intl: { DateTimeFormat: () => ({ resolvedOptions: () => ({ timeZone: 'Europe/Madrid' }) }) },
			addEventListener: (name, fn) => (listeners[name] = fn),
			setTimeout: (fn) => fn(),
			fetch: () => Promise.resolve(),
		};
		const body = beaconScript(false).slice('<script>'.length, -'</script>'.length);
		new Function(...Object.keys(scope), body)(...Object.values(scope));
		assert.equal(sent.length, 0, 'nothing before load');
		listeners.load();
		assert.deepEqual(sent, [
			['/_v', { p: '/phonometry/signals/', q: 'x=1', r: 'https://example.org/a?b', n: 'navigate', t: 421, w: 1920, h: 1080, vw: 1280, vh: 720, dpr: 2, lg: 'es-ES', tz: 'Europe/Madrid', wd: 0, nf: 0 }],
		]);
	});
});

describe('parseBeacon', () => {
	const full = { p: '/phonometry/signals/', q: 'x=1', r: 'https://example.org/', n: 'navigate', t: 421, w: 1920, h: 1080, vw: 1280, vh: 720, dpr: 2, lg: 'es-ES', tz: 'Europe/Madrid', wd: 0, nf: 0 };

	test('a full beacon is read field by field', () => {
		assert.deepEqual(parseBeacon(JSON.stringify(full)), {
			path: '/phonometry/signals/',
			query: 'x=1',
			referrer: 'https://example.org/',
			navType: 'navigate',
			loadMs: 421,
			screenWidth: 1920,
			screenHeight: 1080,
			viewportWidth: 1280,
			viewportHeight: 720,
			pixelRatio: 2,
			language: 'es-ES',
			timeZone: 'Europe/Madrid',
			webdriver: 0,
			notFound: 0,
		});
	});

	const refused = [
		['not JSON', 'p=/'],
		['an array', '[]'],
		['no path', '{}'],
		['a path not starting with /', '{"p":"phonometry"}'],
		['a path over 512 characters', JSON.stringify({ p: `/${'a'.repeat(512)}` })],
		['a path that is not a string', '{"p":1}'],
	];
	for (const [what, body] of refused) test(`refuses ${what}`, () => assert.equal(parseBeacon(body), null));

	test('a wrong optional field is dropped, not the beacon', () => {
		const read = parseBeacon(JSON.stringify({ p: '/x/', t: 'slow', w: -1, dpr: 'big', n: 42, lg: 7, wd: 'yes', nf: 3, q: 5 }));
		assert.deepEqual(read, { path: '/x/', query: '', referrer: '', navType: '', loadMs: 0, screenWidth: 0, screenHeight: 0, viewportWidth: 0, viewportHeight: 0, pixelRatio: 0, language: '', timeZone: '', webdriver: 0, notFound: 0 });
	});

	test('long strings are cut, not refused', () => {
		const read = parseBeacon(JSON.stringify({ p: '/x/', q: 'q'.repeat(300), r: 'r'.repeat(900), tz: 'z'.repeat(100) }));
		assert.equal(read.query.length, 128);
		assert.equal(read.referrer.length, 512);
		assert.equal(read.timeZone.length, 64);
	});

	test('the body limit is 2 KB', () => assert.equal(BEACON_MAX_BYTES, 2048));
});

describe('ipLimitKey', () => {
	test('IPv4 as it is, IPv6 by its /56', () => {
		assert.equal(ipLimitKey('203.0.113.7'), '203.0.113.7');
		assert.equal(ipLimitKey('2001:db8:aaaa:bbcc:1:2:3:4'), '2001:0db8:aaaa:bb');
		assert.equal(ipLimitKey('2001:db8:aaaa:bbff::9'), '2001:0db8:aaaa:bb');
		assert.equal(ipLimitKey('2001:db8::1'), '2001:0db8:0000:00');
		assert.equal(ipLimitKey('::1'), '0000:0000:0000:00');
		assert.equal(ipLimitKey(null), 'unknown');
		assert.equal(ipLimitKey(''), 'unknown');
	});
});

describe('beaconPoint', () => {
	const request = {
		method: 'POST',
		headers: new Headers({
			'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36',
			accept: '*/*',
			referer: 'https://phonometry.dev/phonometry/signals/',
			'cf-connecting-ip': '203.0.113.7',
			'accept-language': 'es-ES,es;q=0.9',
			'sec-fetch-dest': 'empty',
			'sec-fetch-mode': 'no-cors',
			'sec-fetch-site': 'same-origin',
			'cf-ray': 'abc',
		}),
		cf: { country: 'ES', colo: 'MAD', city: 'Madrid', latitude: '40.4', longitude: '-3.7', asn: 3352, region: 'Madrid', timezone: 'Europe/Madrid' },
	};
	const beacon = parseBeacon(JSON.stringify({ p: '/phonometry/signals/', q: 'x=1', r: 'https://www.google.com/', n: 'navigate', t: 421, w: 1920, h: 1080, vw: 1280, vh: 720, dpr: 2, lg: 'es-ES', tz: 'Europe/Madrid', wd: 1, nf: 0 }));

	test('a page view reads as the page request docs-edge logs, marked beacon', () => {
		const point = beaconPoint({ request, beacon, host: 'phonometry.dev', startedAt: 1700000000000, verdict: 'beacon' });
		assert.deepEqual(point.indexes, ['page']);
		assert.equal(point.blobs.length, 20);
		const [path, uaClass, country, agent, refHost, colo, city, , , , status, verdict, accept, method, ua, ip, lang, referer, query, misc] = point.blobs;
		assert.deepEqual(
			{ path, uaClass, country, agent, refHost, colo, city, status, verdict, accept, method, ip, lang, referer, query },
			{ path: '/phonometry/signals/', uaClass: 'browser', country: 'ES', agent: 'Chrome', refHost: 'www.google.com', colo: 'MAD', city: 'Madrid', status: '200', verdict: 'beacon', accept: '', method: 'GET', ip: '203.0.113.7', lang: 'es-ES,es;q=0.9', referer: 'https://www.google.com/', query: 'x=1' },
		);
		assert.equal(ua, request.headers.get('user-agent'));
		const parts = misc.split('|');
		assert.equal(parts.length, 19);
		assert.deepEqual(parts.slice(14), ['navigate', '0', '1', 'es-ES', 'Europe/Madrid']);
		assert.equal(point.doubles.length, 15);
		assert.deepEqual(point.doubles.slice(0, 6), [40.4, -3.7, 3352, 0, 0, 0]);
		assert.equal(point.doubles[8], 1700000000000);
		assert.deepEqual(point.doubles.slice(9), [421, 1920, 1080, 1280, 720, 2]);
	});

	test('the 404 page reports status 404', () => {
		const point = beaconPoint({ request, beacon: { ...beacon, notFound: 1 }, host: 'phonometry.dev', startedAt: 0, verdict: 'beacon' });
		assert.equal(point.blobs[10], '404');
	});

	test('the Sec-Fetch fields are the page navigation\'s, not the beacon POST\'s', () => {
		const misc = (referrer) => beaconPoint({ request, beacon: { ...beacon, referrer }, host: 'phonometry.dev', startedAt: 0, verdict: 'beacon' }).blobs[19].split('|').slice(5, 8);
		assert.deepEqual(misc('https://www.google.com/'), ['document', 'navigate', 'cross-site']);
		assert.deepEqual(misc(''), ['document', 'navigate', 'none']);
		assert.deepEqual(misc('https://phonometry.dev/phonometry/'), ['document', 'navigate', 'same-origin']);
		assert.deepEqual(misc('https://www.phonometry.dev/x'), ['document', 'navigate', 'same-site']);
		assert.deepEqual(misc('not a url'), ['document', 'navigate', '']);
	});

	test('pageFetchSite: the referrer mapped to the value a navigation carries', () => {
		const cases = [
			['', 'none'],
			['https://phonometry.dev/phonometry/signals/', 'same-origin'],
			['https://phonometry.dev:8443/', 'same-site'],
			['https://www.phonometry.dev/', 'same-site'],
			['http://phonometry.dev/', 'cross-site'],
			['https://docs.jmrp.io/phonometry/', 'cross-site'],
			['https://evilphonometry.dev/', 'cross-site'],
			['android-app://com.google.android.gm/', 'cross-site'],
			['::', ''],
		];
		for (const [referrer, site] of cases) assert.equal(pageFetchSite(referrer, 'phonometry.dev'), site, referrer);
	});

	test('a referrer on the same host leaves the host blob empty, as docs-edge does', () => {
		const point = beaconPoint({ request, beacon: { ...beacon, referrer: 'https://phonometry.dev/phonometry/' }, host: 'phonometry.dev', startedAt: 0, verdict: 'beacon' });
		assert.equal(point.blobs[4], '');
		assert.equal(point.blobs[17], 'https://phonometry.dev/phonometry/');
	});
});
