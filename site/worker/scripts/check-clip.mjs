// Plays clips of the phonometry.dev preview in Chrome and fails unless they
// play with no Content-Security-Policy violation (lib/clip-check.mjs says why
// curl cannot see this).
//
// Usage:
//   pnpm exec puppeteer browsers install chrome     # once, from site/worker
//   node site/worker/scripts/check-clip.mjs [--page <url>] [--count <n>]
//
// PUPPETEER_EXECUTABLE_PATH picks another Chrome. Exit 0 when every clip
// tried played, 1 otherwise, 2 on a usage error.
import { parseArgs } from 'node:util';

import { clipVerdict } from '../lib/clip-check.mjs';

/** A page of the preview with clips near the top. */
export const DEFAULT_PAGE = 'https://phonometry.dev/phonometry/vibration/machinery/machine-diagnostics/';

let args;
try {
	args = parseArgs({ args: process.argv.slice(2), options: { page: { type: 'string' }, count: { type: 'string' } } }).values;
} catch (error) {
	console.log(error.message);
	process.exit(2);
}
const page = args.page ?? DEFAULT_PAGE;
const count = Number(args.count ?? 2);
if (!Number.isInteger(count) || count < 1) {
	console.log(`--count must be a positive whole number: ${args.count}`);
	process.exit(2);
}

const { default: puppeteer } = await import('puppeteer');
// The page is this site's own; the sandbox is off because the Ubuntu runners
// refuse the unprivileged user namespaces Chrome's sandbox needs.
const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
let seen;
try {
	const tab = await browser.newPage();
	const violations = [];
	tab.on('console', (message) => {
		if (/Content Security Policy/i.test(message.text())) violations.push(message.text().slice(0, 300));
	});
	await tab.evaluateOnNewDocument(() => {
		globalThis.__violations = [];
		document.addEventListener('securitypolicyviolation', (event) => {
			globalThis.__violations.push(`${event.violatedDirective} blocked ${event.blockedURI}`);
		});
	});
	const response = await tab.goto(page, { waitUntil: 'networkidle0', timeout: 60000 });
	if (!response?.ok()) throw new Error(`${page} answered ${response?.status()}`);
	const videos = await tab.evaluate(async (n) => {
		const out = [];
		for (const video of [...document.querySelectorAll('video')].slice(0, n)) {
			video.muted = true;
			video.preload = 'auto';
			video.load();
			try {
				await video.play();
			} catch {
				// The state below says what went wrong.
			}
			await new Promise((resolve) => setTimeout(resolve, 4000));
			out.push({ src: video.currentSrc, readyState: video.readyState, error: video.error ? video.error.code : null, currentTime: video.currentTime });
		}
		return out;
	}, count);
	violations.push(...(await tab.evaluate(() => globalThis.__violations)));
	seen = { videos, violations: [...new Set(violations)] };
} finally {
	await browser.close();
}

const problems = clipVerdict(seen);
for (const video of seen.videos) console.log(`${video.src}: readyState ${video.readyState}, at ${video.currentTime.toFixed(1)} s`);
for (const line of problems) console.log(`FAIL ${line}`);
if (problems.length === 0) console.log(`ok   ${seen.videos.length} clips played on ${page}`);
process.exitCode = problems.length === 0 ? 0 : 1;
