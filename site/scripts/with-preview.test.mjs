// How with-preview.mjs starts the preview and what it refuses, against a stand-in
// for `astro preview` small enough to read.
//
// The audits only ever run through it on a machine where the preview comes
// up, so a runner that polled one loopback while the preview listened on the
// other, or that took a server already on either for the build, would pass
// there and fail in a stock node:24 container, where `localhost` resolves to
// ::1 first for a server and to 127.0.0.1 alone for a client. Each test here
// puts a stand-in `astro` in a directory of its own, runs the runner there the
// way the audits do, and reads the exit status and what it printed.
//
// Usage: node --test 'scripts/**/*.test.mjs'
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const RUNNER = join(dirname(fileURLToPath(import.meta.url)), 'with-preview.mjs');

/**
 * A stand-in for `astro preview`: it writes the arguments it was given beside
 * itself, and serves a 404 on the host and port they name. Given no host, it
 * exits at once, as a preview the runner could never reach would leave it
 * waiting for good.
 */
const STAND_IN = `#!/usr/bin/env node
const { writeFileSync } = require('node:fs');
const { createServer } = require('node:http');
const args = process.argv.slice(2);
writeFileSync(__dirname + '/args.json', JSON.stringify(args));
const at = (flag) => (args.includes(flag) ? args[args.indexOf(flag) + 1] : undefined);
const host = at('--host');
if (!host) process.exit(3);
createServer((request, response) => response.writeHead(404).end()).listen(Number(at('--port')), host);
`;

/** A port nothing listens on now, on the IPv4 loopback. */
async function freePort() {
	const server = createServer();
	await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
	const { port } = server.address();
	await new Promise((resolve) => server.close(resolve));
	return port;
}

/** A server that answers every request on `host`:`port`, closed when the test ends. */
async function occupy(t, host, port) {
	const server = createServer((_request, response) => response.writeHead(200).end('a dev server'));
	await new Promise((resolve, reject) => {
		server.once('error', reject);
		server.listen(port, host, resolve);
	});
	t.after(() => new Promise((resolve) => server.close(resolve)));
}

/** Whether this machine can listen on the IPv6 loopback at all. */
async function hasIpv6Loopback() {
	const server = createServer();
	try {
		await new Promise((resolve, reject) => {
			server.once('error', reject);
			server.listen(0, '::1', resolve);
		});
		await new Promise((resolve) => server.close(resolve));
		return true;
	} catch {
		return false;
	}
}

/**
 * Put the stand-in in a directory of its own, run the runner there with
 * `command` after `--`, and say how it ended and what the stand-in was given.
 */
async function run(t, port, command) {
	const site = mkdtempSync(join(tmpdir(), 'with-preview-'));
	t.after(() => rmSync(site, { recursive: true, force: true }));
	mkdirSync(join(site, 'node_modules', '.bin'), { recursive: true });
	const astro = join(site, 'node_modules', '.bin', 'astro');
	writeFileSync(astro, STAND_IN);
	chmodSync(astro, 0o755);
	// A browser path of any kind, so that the runner does not go looking for one.
	const env = { ...process.env, PUPPETEER_EXECUTABLE_PATH: process.execPath };
	const child = spawn(process.execPath, [RUNNER, '--port', String(port), '--', ...command], {
		cwd: site,
		env,
		stdio: ['ignore', 'pipe', 'pipe'],
	});
	let err = '';
	child.stderr.on('data', (chunk) => {
		err += chunk;
	});
	child.stdout.resume();
	const status = await new Promise((resolve) => child.on('exit', (code) => resolve(code)));
	let args = null;
	try {
		args = JSON.parse(readFileSync(join(site, 'node_modules', '.bin', 'args.json'), 'utf8'));
	} catch {
		// The stand-in never ran.
	}
	return { status, err, args };
}

test('the preview starts on the IPv4 loopback, and the command runs once it answers there', async (t) => {
	const port = await freePort();
	const ran = await run(t, port, [process.execPath, '-e', 'process.exit(7)']);
	assert.deepEqual(ran.args, ['preview', '--port', String(port), '--host', '127.0.0.1']);
	assert.equal(ran.status, 7, ran.err);
});

test('a server already answering on the IPv4 loopback is refused before the preview starts', async (t) => {
	const port = await freePort();
	await occupy(t, '127.0.0.1', port);
	const ran = await run(t, port, [process.execPath, '-e', 'process.exit(0)']);
	assert.equal(ran.status, 1);
	assert.match(ran.err, new RegExp(`something is already serving on 127\\.0\\.0\\.1:${port}`));
	assert.equal(ran.args, null);
});

test('a server already answering on the IPv6 loopback is refused before the preview starts', async (t) => {
	if (!(await hasIpv6Loopback())) {
		t.skip('this machine cannot listen on ::1');
		return;
	}
	const port = await freePort();
	await occupy(t, '::1', port);
	const ran = await run(t, port, [process.execPath, '-e', 'process.exit(0)']);
	assert.equal(ran.status, 1);
	assert.match(ran.err, new RegExp(`something is already serving on \\[::1\\]:${port}`));
	assert.equal(ran.args, null);
});
