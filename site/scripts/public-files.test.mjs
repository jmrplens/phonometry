// The hand-written files that name the site's own addresses, held to the
// target they are written for (src/data/site-targets.json).
//
// public/ is copied into dist/ verbatim, so nothing Astro does moves the
// addresses robots.txt, sitemap.xml and manifest.json write: they are written
// for the build made with nothing set, the one target. .pa11yci.json lists
// the pages the accessibility audit opens on the local preview, which serves
// the build under its base path.
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { test } from 'node:test';

import { DEFAULT_SITE, SITE_TARGETS, basePath } from '../src/data/site.mjs';
import { englishTwin, isFallbackRoute } from '../src/lib/fallback-routes.mjs';

const { siteUrl: origin, basePath: base } = SITE_TARGETS[DEFAULT_SITE];
const read = (name) => readFileSync(new URL(`../${name}`, import.meta.url), 'utf8');
const exists = (name) => {
	try {
		readFileSync(new URL(`../public/${name}`, import.meta.url));
		return true;
	} catch {
		return false;
	}
};

test('robots.txt names the sitemap index of the site it is written for', () => {
	const sitemaps = read('public/robots.txt')
		.split('\n')
		.filter((line) => /^sitemap:/i.test(line));
	assert.deepEqual(sitemaps, [`Sitemap: ${origin}${base}/sitemap-index.xml`]);
});

test('sitemap.xml points at the shard of the site it is written for', () => {
	const locs = [...read('public/sitemap.xml').matchAll(/<loc>([^<]*)<\/loc>/g)].map((match) => match[1]);
	assert.deepEqual(locs, [`${origin}${base}/sitemap-0.xml`]);
});

test('manifest.json starts, scopes and finds its icons under the base path', () => {
	const manifest = JSON.parse(read('public/manifest.json'));
	assert.equal(manifest.start_url, `${base}/`);
	assert.equal(manifest.scope, `${base}/`);
	assert.ok(manifest.icons.length > 0);
	for (const { src } of manifest.icons) {
		assert.ok(src.startsWith(`${base}/`), `${src} is not under ${base}/`);
		assert.ok(exists(src.slice(base.length + 1)), `${src} names no file of public/`);
	}
});

// A route of the build is a page of src/content/docs, as a folder's index or a
// file of its own; a Spanish API route is served from its English entry.
const docs = new URL('../src/content/docs/', import.meta.url);
const isPage = (route) => {
	const entry = isFallbackRoute(route) ? englishTwin(route) : route;
	const names = entry === '' ? ['index'] : [`${entry}/index`, entry];
	return names.some((name) => ['md', 'mdx'].some((ext) => existsSync(new URL(`${name}.${ext}`, docs))));
};

test('every page the accessibility audit opens is a page the preview serves under its base path', () => {
	const { urls } = JSON.parse(read('.pa11yci.json'));
	const preview = `http://localhost:4321${basePath}/`;
	assert.ok(urls.length > 0);
	for (const url of urls) {
		assert.ok(url.startsWith(preview), `${url} is not under ${preview}`);
		const route = url.slice(preview.length).replace(/\/$/, '');
		assert.ok(isPage(route), `${url} names no page of src/content/docs`);
	}
});

test('a route names a page only without the base path, and a Spanish API route through its English entry', () => {
	assert.ok(isPage(''));
	assert.ok(isPage('start/getting-started'));
	assert.ok(isPage('es/reference/api/signals/levels'));
	assert.ok(!isPage('phonometry/start/getting-started'));
	assert.ok(!isPage('es/reference/api/no-such-page'));
});

// The AI policy, said three times in three vocabularies. A crawler reads one of
// them and believes it, so a disagreement publishes a contradiction: the three
// change together or this fails.
const SIGNAL = /^Content-Signal:\s*(.+)$/i;
const CONTENT_SIGNAL_KEYS = new Set(['search', 'ai-input', 'ai-train']);

/** The groups of robots.txt, each with its user agents and its lines. */
function robotsGroups(text) {
	const groups = [];
	let current = null;
	for (const raw of text.split('\n')) {
		const line = raw.replace(/#.*/, '').trim();
		if (line === '') continue;
		const [key, ...rest] = line.split(':');
		const value = rest.join(':').trim();
		if (/^user-agent$/i.test(key.trim())) {
			if (!current || current.lines.length > 0) groups.push((current = { agents: [], lines: [] }));
			current.agents.push(value);
		} else if (current && !/^sitemap$/i.test(key.trim())) current.lines.push(line);
	}
	return groups;
}

test('robots.txt gives every group the same Content Signals, in the keys the vocabulary defines', () => {
	// RFC 9309: a crawler obeys only the group that names it most closely, so a
	// signal declared under `*` alone never reaches GPTBot, ClaudeBot and the
	// rest. contentsignals.org and draft-romm-aipref-contentsignals define
	// exactly search, ai-input and ai-train; any other key is ignored.
	const groups = robotsGroups(read('public/robots.txt'));
	assert.ok(groups.length > 1);
	for (const { agents, lines } of groups) {
		const signals = lines.map((line) => SIGNAL.exec(line)?.[1]).filter(Boolean);
		assert.deepEqual(signals, ['search=yes, ai-input=yes, ai-train=yes'], `group ${agents.join(', ')}`);
		for (const pair of signals[0].split(',')) assert.ok(CONTENT_SIGNAL_KEYS.has(pair.split('=')[0].trim()), pair);
		assert.ok(lines.includes('Allow: /'), `group ${agents.join(', ')} allows /`);
		assert.ok(!lines.some((line) => /^disallow:\s*\/\s*$/i.test(line)), `group ${agents.join(', ')} disallows nothing`);
	}
});

test('ai.txt grants what robots.txt grants', () => {
	const ai = read('public/ai.txt');
	assert.match(ai, /^User-Agent:\s*\*\s*$/m);
	assert.match(ai, /^Allow:\s*\/\s*$/m);
	assert.doesNotMatch(ai, /^Disallow:/im);
});

test('tdmrep.json reserves no text and data mining rights, as ai-train=yes says', () => {
	const entries = JSON.parse(read('public/.well-known/tdmrep.json'));
	assert.deepEqual(entries, [{ location: '/', 'tdm-reservation': 0 }]);
});

test('traffic-advice lets Chrome\'s prefetch proxy in', () => {
	const advice = JSON.parse(read('public/.well-known/traffic-advice'));
	assert.deepEqual(advice, [{ user_agent: 'prefetch-proxy', disallow: false }]);
});

test('gpc.json declares Global Privacy Control honoured, and the privacy page says so', () => {
	assert.equal(JSON.parse(read('public/.well-known/gpc.json')).gpc, true);
	for (const page of ['src/content/docs/start/privacy.md', 'src/content/docs/es/start/privacy.md']) {
		assert.match(read(page), /\/\.well-known\/gpc\.json/, page);
	}
});

// RFC 9116: Contact and Expires are required, Expires should be under a year
// away, and Canonical names the address the file is served at. The file is
// signed, so its fields are read inside the signed block.
const SECURITY_RENEWAL_DAYS = 30;

test('security.txt is signed, names its contacts and policy, and is renewed before it expires', () => {
	const text = read('public/.well-known/security.txt');
	assert.match(text, /^-----BEGIN PGP SIGNED MESSAGE-----\nHash: SHA512\n\n/);
	assert.match(text, /\n-----BEGIN PGP SIGNATURE-----\n[\s\S]+\n-----END PGP SIGNATURE-----\n$/);
	const body = text.split('-----BEGIN PGP SIGNATURE-----')[0];
	const field = (name) => [...body.matchAll(new RegExp(`^${name}: (.+)$`, 'gm'))].map((match) => match[1]);
	assert.deepEqual(field('Contact'), ['https://github.com/jmrplens/phonometry/security/advisories/new', 'mailto:mail@jmrp.io']);
	assert.deepEqual(field('Canonical'), [`${origin}/.well-known/security.txt`]);
	assert.deepEqual(field('Policy'), ['https://github.com/jmrplens/phonometry/security/policy']);
	const [expires] = field('Expires');
	const days = (Date.parse(expires) - Date.now()) / 86_400_000;
	assert.ok(days > SECURITY_RENEWAL_DAYS, `Expires ${expires} is ${Math.floor(days)} days away: set a new date and sign the file again (CONTRIBUTING.md, 5b)`);
	assert.ok(days <= 366, `Expires ${expires} is more than a year away (RFC 9116, 2.5.5)`);
});
