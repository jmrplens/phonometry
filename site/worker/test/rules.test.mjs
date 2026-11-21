// The zone rulesets of the preview: their exact expressions and targets.
import assert from 'node:assert/strict';
import { describe, test } from 'node:test';

import { IMMUTABLE, redirectRules, responseHeaderRules, wildcardMatch, wildcardReplace } from '../lib/rules.mjs';
import { twinExclusions } from '../lib/twins.mjs';
import { evaluate, redirectFor } from './fixtures/rule-expression.mjs';

const prefix = '/phonometry';
const options = {
	host: 'phonometry.dev',
	prefix,
	exclusions: twinExclusions(prefix),
	clipBase: 'https://docs.jmrp.io/phonometry/media/',
};

describe('redirectRules', () => {
	const rules = redirectRules(options);
	const byRef = Object.fromEntries(rules.map((rule) => [rule.ref, rule]));

	test('five rules in order, within the ten a Free zone takes', () => {
		assert.deepEqual(
			rules.map(({ ref }) => ref),
			['www-to-apex', 'root-to-base', 'clips-to-range-host', 'trailing-slash', 'markdown-twin'],
		);
		for (const rule of rules) {
			assert.equal(rule.action, 'redirect');
			assert.equal(rule.enabled, true);
			assert.ok(rule.description.length > 0);
		}
	});

	test('www goes to the apex, path and query kept, permanently', () => {
		const { expression, action_parameters: p } = byRef['www-to-apex'];
		assert.equal(expression, 'http.host eq "www.phonometry.dev"');
		assert.deepEqual(p.from_value, {
			status_code: 301,
			target_url: { expression: 'concat("https://phonometry.dev", http.request.uri.path)' },
			preserve_query_string: true,
		});
	});

	test('the bare root goes to the base path while there is one', () => {
		const { expression, action_parameters: p } = byRef['root-to-base'];
		assert.equal(expression, 'http.host eq "phonometry.dev" and http.request.uri.path eq "/"');
		assert.deepEqual(p.from_value, {
			status_code: 302,
			target_url: { value: 'https://phonometry.dev/phonometry/' },
			preserve_query_string: true,
		});
		assert.equal(redirectRules({ ...options, prefix: '', exclusions: twinExclusions('') }).some(({ ref }) => ref === 'root-to-base'), false);
	});

	test('a clip goes to a host that answers byte ranges', () => {
		const { expression, action_parameters: p } = byRef['clips-to-range-host'];
		assert.equal(expression, 'http.host eq "phonometry.dev" and http.request.uri.path wildcard "/phonometry/media/*.webm"');
		assert.deepEqual(p.from_value, {
			status_code: 302,
			target_url: {
				expression:
					'wildcard_replace(http.request.uri.path, "/phonometry/media/*.webm", "https://docs.jmrp.io/phonometry/media/${1}.webm")',
			},
			preserve_query_string: false,
		});
	});

	test('the Markdown rule names the copy beside the page and excludes the pages without one', () => {
		const { expression, action_parameters: p } = byRef['markdown-twin'];
		assert.equal(
			expression,
			[
				'http.host eq "phonometry.dev"',
				'http.request.method in {"GET" "HEAD"}',
				'starts_with(http.request.uri.path, "/phonometry/")',
				'ends_with(http.request.uri.path, "/")',
				'any(http.request.headers["accept"][*] wildcard "*text/markdown*")',
				'not any(http.request.headers["accept"][*] wildcard "*text/html*text/markdown*")',
				'not any(http.request.headers["accept"][*] wildcard "*application/xhtml+xml*text/markdown*")',
				'not starts_with(http.request.uri.path, "/phonometry/es/reference/api/")',
			].join(' and '),
		);
		assert.deepEqual(p.from_value, {
			status_code: 302,
			target_url: { expression: 'concat(http.request.uri.path, "index.md")' },
			preserve_query_string: false,
		});
	});

	test('pages listed one by one are excluded by an in-set', () => {
		const rule = redirectRules({ ...options, exclusions: { pages: ['/phonometry/x/', '/phonometry/y/'], subtrees: [] } }).at(-1);
		assert.match(rule.expression, / and not http\.request\.uri\.path in \{"\/phonometry\/x\/" "\/phonometry\/y\/"\}$/);
	});

	test('the clip host moves to R2 by changing one argument', () => {
		const rule = redirectRules({ ...options, clipBase: 'https://media.phonometry.dev/' })[2];
		assert.match(rule.action_parameters.from_value.target_url.expression, /"https:\/\/media\.phonometry\.dev\/\$\{1\}\.webm"\)$/);
	});

	test('a quote in a host or path is refused, so no expression can be broken out of', () => {
		assert.throws(() => redirectRules({ ...options, host: 'a"b' }), /host/);
		assert.throws(() => redirectRules({ ...options, clipBase: 'https://x/"' }), /clip/);
	});
});

describe('legacy-base, the old base path sent to the root', () => {
	const root = { ...options, prefix: '', exclusions: twinExclusions('') };
	const rules = redirectRules({ ...root, legacyPrefix: '/phonometry' });
	const byRef = Object.fromEntries(rules.map((rule) => [rule.ref, rule]));

	test('not generated while the site keeps a base path, nor at the root with no old one', () => {
		for (const set of [redirectRules(options), redirectRules({ ...options, legacyPrefix: '/phonometry' }), redirectRules(root)]) {
			assert.equal(set.some(({ ref }) => ref.startsWith('legacy-base')), false);
		}
	});

	test('at the root, right after www and before the clip, slash and Markdown rules', () => {
		assert.deepEqual(
			rules.map(({ ref }) => ref),
			['www-to-apex', 'legacy-base-slash', 'legacy-base-bare', 'clips-to-range-host', 'trailing-slash', 'markdown-twin'],
		);
		for (const ref of ['legacy-base-slash', 'legacy-base-bare']) {
			assert.equal(byRef[ref].action, 'redirect');
			assert.equal(byRef[ref].enabled, true);
			assert.equal(byRef[ref].action_parameters.from_value.status_code, 301);
			assert.equal(byRef[ref].action_parameters.from_value.preserve_query_string, true);
		}
	});

	test('an address under the old base answers the same path at the root, one hop', () => {
		const { expression, action_parameters: p } = byRef['legacy-base-slash'];
		assert.equal(expression, 'http.host eq "phonometry.dev" and http.request.uri.path wildcard "/phonometry/*"');
		assert.deepEqual(p.from_value.target_url, {
			expression: 'wildcard_replace(http.request.uri.path, "/phonometry/*", "https://phonometry.dev/${1}")',
		});
		const sent = (path) => (wildcardMatch(path, '/phonometry/*') ? wildcardReplace(path, '/phonometry/*', 'https://phonometry.dev/${1}') : null);
		assert.equal(sent('/phonometry/signals/levels/'), 'https://phonometry.dev/signals/levels/');
		assert.equal(sent('/phonometry/signals/index.md'), 'https://phonometry.dev/signals/index.md');
		assert.equal(sent('/phonometry/'), 'https://phonometry.dev/');
		assert.equal(sent('/PHONOMETRY/llms.txt'), 'https://phonometry.dev/llms.txt');
		assert.equal(sent('/phonometryx/'), null);
		assert.equal(sent('/signals/phonometry/'), null);
		assert.equal(sent('/phonometry'), null);
	});

	test('the old base itself answers the root', () => {
		const { expression, action_parameters: p } = byRef['legacy-base-bare'];
		assert.equal(expression, 'http.host eq "phonometry.dev" and http.request.uri.path wildcard "/phonometry"');
		assert.deepEqual(p.from_value.target_url, { value: 'https://phonometry.dev/' });
		assert.equal(wildcardMatch('/phonometry', '/phonometry'), true);
		assert.equal(wildcardMatch('/phonometry/', '/phonometry'), false);
	});

	test('a legacy prefix that could end the expression string is refused', () => {
		assert.throws(() => redirectRules({ ...root, legacyPrefix: '/a"b' }), /legacy prefix/);
	});
});

describe('responseHeaderRules', () => {
	const rules = responseHeaderRules({ host: 'phonometry.dev', prefix });
	const byRef = Object.fromEntries(rules.map((rule) => [rule.ref, rule]));

	test('three rules in order, all rewrites', () => {
		assert.deepEqual(
			rules.map(({ ref }) => ref),
			['markdown-twin-vary', 'not-found-plain', 'astro-immutable'],
		);
		for (const rule of rules) {
			assert.equal(rule.action, 'rewrite');
			assert.equal(rule.enabled, true);
			assert.ok(rule.description.length > 0);
		}
	});

	test('the 302 of the Markdown rule varies on Accept and is never stored', () => {
		const rule = byRef['markdown-twin-vary'];
		assert.equal(
			rule.expression,
			'http.host eq "phonometry.dev" and http.response.code eq 302 and ends_with(http.request.uri.path, "/") and any(http.request.headers["accept"][*] wildcard "*text/markdown*")',
		);
		assert.deepEqual(rule.action_parameters.headers, {
			Vary: { operation: 'set', value: 'Accept' },
			'Cache-Control': { operation: 'set', value: 'no-store' },
		});
	});

	test('a 404 names no copy and no canonical, is HTML and varies on encoding only', () => {
		const rule = byRef['not-found-plain'];
		assert.equal(rule.expression, 'http.host eq "phonometry.dev" and http.response.code eq 404');
		assert.deepEqual(rule.action_parameters.headers, {
			Link: { operation: 'remove' },
			Vary: { operation: 'set', value: 'Accept-Encoding' },
			'Content-Type': { operation: 'set', value: 'text/html; charset=utf-8' },
		});
	});

	test('a content-hashed file is immutable only when it was found', () => {
		const rule = byRef['astro-immutable'];
		assert.equal(
			rule.expression,
			'http.host eq "phonometry.dev" and http.response.code in {200 304} and starts_with(http.request.uri.path, "/phonometry/_astro/")',
		);
		assert.deepEqual(rule.action_parameters.headers, { 'Cache-Control': { operation: 'set', value: IMMUTABLE } });
		assert.equal(IMMUTABLE, 'public, max-age=31536000, immutable');
		const root = responseHeaderRules({ host: 'phonometry.dev', prefix: '' }).at(-1);
		assert.match(root.expression, /starts_with\(http\.request\.uri\.path, "\/_astro\/"\)$/);
	});
});

describe('wildcardReplace, the model of wildcard_replace', () => {
	test('fills ${n} with the run each * matched, case-insensitively', () => {
		assert.equal(wildcardReplace('/Phonometry/a/b', '/phonometry/*', 'https://x/${1}'), 'https://x/a/b');
		assert.equal(wildcardReplace('/m/a.webm', '/m/*.webm', 'https://y/${1}.webm'), 'https://y/a.webm');
		assert.equal(wildcardReplace('/other', '/phonometry/*', 'https://x/${1}'), '/other');
	});
});

describe('wildcardMatch, the model of the wildcard operator', () => {
	test('matches the whole value, case-insensitively, * as any run including none', () => {
		assert.equal(wildcardMatch('Text/Markdown', '*text/markdown*'), true);
		assert.equal(wildcardMatch('text/markdown', 'text/markdown'), true);
		assert.equal(wildcardMatch('x text/markdown', 'text/markdown'), false);
		assert.equal(wildcardMatch('text/html, text/markdown', '*text/html*text/markdown*'), true);
		assert.equal(wildcardMatch('text/markdown, text/html', '*text/html*text/markdown*'), false);
		assert.equal(wildcardMatch('a.b+c', 'a.b+c'), true);
		assert.equal(wildcardMatch('aXb+c', 'a.b+c'), false);
	});
});

describe('trailing-slash, a page address written without its slash', () => {
	// The deployed set: the site at the root, the old base path sent there.
	const root = { ...options, prefix: '', exclusions: twinExclusions(''), clipBase: 'https://media.phonometry.dev/', legacyPrefix: '/phonometry' };
	const rules = redirectRules(root);
	const answer = (request) => redirectFor(rules, { host: 'phonometry.dev', accept: ['text/html,application/xhtml+xml,*/*;q=0.8'], ...request });
	const slash = (path) => ({ ref: 'trailing-slash', status: 301, location: `https://phonometry.dev${path}` });

	test('one rule, after the old base path and the clips, before the Markdown rule, within the ten a Free zone takes', () => {
		assert.deepEqual(
			rules.map(({ ref }) => ref),
			['www-to-apex', 'legacy-base-slash', 'legacy-base-bare', 'clips-to-range-host', 'trailing-slash', 'markdown-twin'],
		);
		assert.ok(rules.length <= 10);
	});

	test('its expression and target, exactly', () => {
		const rule = rules.find(({ ref }) => ref === 'trailing-slash');
		assert.equal(
			rule.expression,
			[
				'http.host eq "phonometry.dev"',
				'http.request.method in {"GET" "HEAD"}',
				'not ends_with(http.request.uri.path, "/")',
				'not http.request.uri.path wildcard "*.*"',
				'not ends_with(http.request.uri.path, "/index")',
				'http.request.uri.path ne "/404"',
				'http.request.uri.path ne "/_v"',
				'not starts_with(http.request.uri.path, "/cdn-cgi/")',
			].join(' and '),
		);
		assert.deepEqual(rule.action_parameters.from_value, {
			status_code: 301,
			target_url: { expression: 'concat("https://phonometry.dev", http.request.uri.path, "/")' },
			preserve_query_string: true,
		});
		assert.equal(rule.action, 'redirect');
		assert.equal(rule.enabled, true);
	});

	test('a page without its slash answers 301 to the page, in one hop', () => {
		for (const path of ['/signals', '/es', '/start/getting-started', '/es/reference/api/levels', '/underwater', '/environment']) {
			assert.deepEqual(answer({ path }), slash(`${path}/`), path);
			assert.deepEqual(answer({ path, method: 'HEAD' }), slash(`${path}/`), `HEAD ${path}`);
		}
	});

	// The asset server as wrangler.jsonc sets it up (`html_handling:
	// "auto-trailing-slash"`), as phonometry.dev answers today: a folder's
	// page at its address with a slash, its `index` alias sent to the folder,
	// a flat page at its address without a slash, and each other form sent
	// to the one it serves. Measured live on 2026-11-21 before the rule.
	const files = new Set(['index.html', 'signals/index.html', 'es/index.html', '404.html']);
	const assets = (path) => {
		const bare = path.replace(/^\//, '');
		if (path.endsWith('/')) {
			if (files.has(`${bare}index.html`)) return { status: 200 };
			if (files.has(`${bare.slice(0, -1)}.html`)) return { status: 307, location: path.slice(0, -1) };
			return { status: 404 };
		}
		if (path.endsWith('/index') && files.has(`${bare}.html`)) return { status: 307, location: path.slice(0, -'index'.length) };
		if (files.has(`${bare}.html`)) return { status: 200 };
		if (files.has(`${bare}/index.html`)) return { status: 307, location: `${path}/` };
		return { status: 404 };
	};
	// Every hop a browser takes: the zone rules first, then the assets.
	const hops = (start) => {
		const seen = [];
		let path = start;
		for (let hop = 0; hop < 5; hop += 1) {
			seen.push(path);
			const rule = answer({ path });
			if (rule) {
				path = new URL(rule.location, 'https://phonometry.dev').pathname;
				continue;
			}
			const asset = assets(path);
			if (asset.status !== 307) return { seen, status: asset.status };
			path = asset.location;
		}
		return { seen, status: 'loop' };
	};

	test('every address ends at an answer, the not-found page and a folder page\'s index alias with no loop between the rule and the assets', () => {
		assert.deepEqual(hops('/signals'), { seen: ['/signals', '/signals/'], status: 200 });
		assert.deepEqual(hops('/signals/index'), { seen: ['/signals/index', '/signals/'], status: 200 });
		assert.deepEqual(hops('/signals/index/'), { seen: ['/signals/index/', '/signals/index', '/signals/'], status: 200 });
		assert.deepEqual(hops('/index'), { seen: ['/index', '/'], status: 200 });
		assert.deepEqual(hops('/404'), { seen: ['/404'], status: 200 });
		assert.deepEqual(hops('/404/'), { seen: ['/404/', '/404'], status: 200 });
		assert.deepEqual(hops('/nothing'), { seen: ['/nothing', '/nothing/'], status: 404 });
		assert.equal(answer({ path: '/404' }), null);
		assert.equal(answer({ path: '/signals/index' }), null);
		assert.deepEqual(answer({ path: '/es/404' }), slash('/es/404/'));
	});

	test('the query string is kept', () => {
		assert.deepEqual(answer({ path: '/signals', query: 'q=1' }), slash('/signals/?q=1'));
		assert.deepEqual(answer({ path: '/es', query: 'a=1&b=2' }), slash('/es/?a=1&b=2'));
	});

	test('a page with its slash, and the root, are left to the assets', () => {
		for (const path of ['/', '/signals/', '/es/', '/start/getting-started/']) assert.equal(answer({ path }), null, path);
	});

	test('a file with an extension is left to the assets, wherever its dot is', () => {
		for (const path of ['/llms.txt', '/llms/llms-signals-2.txt', '/robots.txt', '/sitemap-index.xml', '/signals/index.md', '/index.md', '/start/getting-started/index.html', '/_astro/index.A1B2.css', '/favicon.svg', '/og-image.png', '/pagefind/pagefind.js', '/.well-known/security.txt']) {
			assert.equal(answer({ path }), null, path);
		}
	});

	test('a Markdown request for a page with its slash still gets the copy, and one without its slash gets the slash first', () => {
		const markdown = ['text/markdown'];
		assert.deepEqual(answer({ path: '/signals/', accept: markdown }), { ref: 'markdown-twin', status: 302, location: '/signals/index.md' });
		assert.deepEqual(answer({ path: '/signals', accept: markdown }), slash('/signals/'));
	});

	test('the beacon and every method but GET and HEAD are left to the Worker and the assets', () => {
		assert.equal(answer({ path: '/_v', method: 'POST' }), null);
		assert.equal(answer({ path: '/_v' }), null);
		assert.equal(answer({ path: '/signals', method: 'POST' }), null);
		assert.equal(answer({ path: '/signals', method: 'OPTIONS' }), null);
	});

	test('Cloudflare\'s own /cdn-cgi/ paths are left alone, a challenge\'s orchestration requests among them', () => {
		for (const path of ['/cdn-cgi/trace', '/cdn-cgi/challenge-platform/h/b/orchestrate/chl_page/v1', '/cdn-cgi/l/email-protection', '/cdn-cgi/rum']) {
			assert.equal(answer({ path, query: 'ray=x' }), null, path);
			assert.equal(answer({ path, method: 'HEAD' }), null, `HEAD ${path}`);
		}
		assert.deepEqual(answer({ path: '/cdn-cgix' }), slash('/cdn-cgix/'));
	});

	test('the old base path and www keep their own rules, which hand the slash rule a path it then finishes', () => {
		assert.deepEqual(answer({ path: '/phonometry' }), { ref: 'legacy-base-bare', status: 301, location: 'https://phonometry.dev/' });
		const legacy = answer({ path: '/phonometry/signals', query: 'q=1' });
		assert.deepEqual(legacy, { ref: 'legacy-base-slash', status: 301, location: 'https://phonometry.dev/signals?q=1' });
		assert.deepEqual(answer({ path: '/signals', query: 'q=1' }), slash('/signals/?q=1'));
		assert.deepEqual(answer({ host: 'www.phonometry.dev', path: '/signals' }), { ref: 'www-to-apex', status: 301, location: 'https://phonometry.dev/signals' });
		assert.equal(redirectFor(rules.filter(({ ref }) => ref === 'trailing-slash'), { host: 'www.phonometry.dev', path: '/signals' }), null);
	});

	test('a clip keeps its own rule', () => {
		assert.equal(answer({ path: '/media/sweep.webm' }).ref, 'clips-to-range-host');
	});

	test('under a base path the rule covers that path and the bare base', () => {
		const based = redirectRules(options);
		const at = (path) => redirectFor(based, { host: 'phonometry.dev', path, accept: ['text/html'] });
		assert.deepEqual(at('/phonometry'), slash('/phonometry/'));
		assert.deepEqual(at('/phonometry/signals'), slash('/phonometry/signals/'));
		assert.equal(at('/other'), null);
		assert.equal(at('/phonometryx'), null);
		assert.equal(at('/phonometry/llms.txt'), null);
		assert.match(based.find(({ ref }) => ref === 'trailing-slash').expression, / and \(http\.request\.uri\.path eq "\/phonometry" or starts_with\(http\.request\.uri\.path, "\/phonometry\/"\)\) and /);
		assert.match(based.find(({ ref }) => ref === 'trailing-slash').expression, / and http\.request\.uri\.path ne "\/phonometry\/404" and /);
	});

	test('the reader of these tests reads every rule the phase holds', () => {
		for (const rule of [...rules, ...redirectRules(options)]) {
			assert.equal(typeof evaluate(rule.expression, { host: 'phonometry.dev', method: 'GET', path: '/x/', accept: [] }), 'boolean', rule.ref);
		}
	});
});
