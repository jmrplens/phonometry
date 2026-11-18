// The few Cloudflare API calls the preview's scripts make.
//
// Credentials come from the environment only and go into request headers
// only: a scoped API token as CLOUDFLARE_API_TOKEN (what CI holds, one
// secret per job), or, run by hand on the maintainer's machine, the account
// email and Global API Key as CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY (the
// names wrangler reads too). Nothing here prints a header or a credential.

export const API = 'https://api.cloudflare.com/client/v4';

/**
 * The Phonometry account and its phonometry.dev zone. Neither id is a secret.
 * They are fixed here, not read from CLOUDFLARE_ACCOUNT_ID or
 * CLOUDFLARE_ZONE_ID, because a shell can hold those for another account (the
 * maintainer's does), and a rule apply aimed at another zone would replace
 * that zone's rules. wrangler.jsonc names the same account (its test holds the
 * two equal).
 */
export const ACCOUNT_ID = '4dbfb3b955a0c856bfe066f2a6061dd5';
export const ZONE_ID = '594554a63737deee229566971a765fd4';

/**
 * A note for a CLOUDFLARE_ZONE_ID or CLOUDFLARE_ACCOUNT_ID that names something else, which is ignored.
 *
 * @param {Record<string, string | undefined>} env The environment.
 * @returns {string[]} The lines to print, empty when nothing is set or it matches.
 */
export function ignoredTargets(env) {
	const lines = [];
	if (env.CLOUDFLARE_ZONE_ID && env.CLOUDFLARE_ZONE_ID !== ZONE_ID) lines.push(`CLOUDFLARE_ZONE_ID names another zone and is ignored: this acts on phonometry.dev (${ZONE_ID}) only`);
	if (env.CLOUDFLARE_ACCOUNT_ID && env.CLOUDFLARE_ACCOUNT_ID !== ACCOUNT_ID) lines.push(`CLOUDFLARE_ACCOUNT_ID names another account and is ignored: this reads the Phonometry account (${ACCOUNT_ID}) only`);
	return lines;
}

/**
 * The authentication headers the environment provides.
 *
 * @param {Record<string, string | undefined>} env The environment.
 * @returns {Record<string, string>} The headers.
 * @throws {Error} When neither form of credential is set.
 */
export function authHeaders(env) {
	if (env.CLOUDFLARE_API_TOKEN) return { authorization: `Bearer ${env.CLOUDFLARE_API_TOKEN}` };
	if (env.CLOUDFLARE_EMAIL && env.CLOUDFLARE_API_KEY) {
		return { 'x-auth-email': env.CLOUDFLARE_EMAIL, 'x-auth-key': env.CLOUDFLARE_API_KEY };
	}
	throw new Error('set CLOUDFLARE_API_TOKEN, or CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY');
}

/** An API error that says what was asked and what came back, never how it was signed. */
export class CloudflareError extends Error {
	constructor(method, path, status, errors) {
		const detail = (errors ?? []).map((e) => `${e.code ?? ''} ${e.message ?? ''}`.trim()).join('; ');
		super(`${method} ${path}: HTTP ${status}${detail ? `: ${detail}` : ''}`);
		this.status = status;
		this.errors = errors ?? [];
	}
}

/**
 * One REST call.
 *
 * @param {string} path The path under /client/v4, starting with `/`.
 * @param {{method?: string, body?: unknown, env: Record<string, string | undefined>, fetchImpl?: typeof fetch}} options
 * @returns {Promise<unknown>} The `result` of a successful answer.
 * @throws {CloudflareError} On a failed answer.
 */
export async function cfApi(path, { method = 'GET', body, env, fetchImpl = fetch }) {
	const headers = { ...authHeaders(env), accept: 'application/json' };
	if (body !== undefined) headers['content-type'] = 'application/json';
	const response = await fetchImpl(`${API}${path}`, {
		method,
		headers,
		body: body === undefined ? undefined : JSON.stringify(body),
	});
	let payload = null;
	try {
		payload = await response.json();
	} catch {
		// A body that is not JSON is reported by its status alone.
	}
	if (!response.ok || payload?.success === false) throw new CloudflareError(method, path, response.status, payload?.errors);
	return payload?.result;
}

/**
 * One GraphQL Analytics query.
 *
 * @param {{query: string, variables: object}} request The query.
 * @param {{env: Record<string, string | undefined>, fetchImpl?: typeof fetch}} options
 * @returns {Promise<any>} The `data` of the answer.
 * @throws {Error} When the answer carries errors or no data: an error must never read as an empty day.
 */
export async function graphql(request, { env, fetchImpl = fetch }) {
	const response = await fetchImpl(`${API}/graphql`, {
		method: 'POST',
		headers: { ...authHeaders(env), 'content-type': 'application/json' },
		body: JSON.stringify(request),
	});
	const payload = await response.json().catch(() => null);
	const errors = payload?.errors ?? [];
	if (!response.ok || errors.length > 0 || !payload?.data) {
		const detail = errors.map((e) => e.message).join('; ') || `HTTP ${response.status}`;
		throw new Error(`GraphQL: ${detail}`);
	}
	return payload.data;
}
