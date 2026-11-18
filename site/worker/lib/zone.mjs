// The DNS records and zone settings of phonometry.dev, and the plan that
// brings a zone to them.
//
// The apex record is not here: the Worker's Custom Domain creates it (and its
// certificate) on the first deploy and owns it. What is here is everything
// else a domain that serves a site and sends no mail needs: a proxied
// placeholder so `www` can be redirected by a zone rule, and the records that
// tell every mail server this domain sends and receives nothing (null MX,
// RFC 7505; an SPF that authorises no one; DMARC reject; a revoked DKIM key),
// on the apex and on `www`, the two names that resolve.
// Settings turn off the two features that rewrite the bytes the build wrote
// (email obfuscation, automatic HTTPS rewrites), so the preview serves the
// build as built, and turn on HTTPS everywhere with HSTS on every response,
// redirects and errors included.

/** The records, without the zone apex suffix in `name` ('@' is the apex). */
export const DNS_RECORDS = Object.freeze([
	Object.freeze({ type: 'AAAA', name: 'www', content: '100::', proxied: true, comment: 'www-to-apex redirect placeholder' }),
	// www has an address, so it gets the same refusals as the apex: without
	// them it would take an implicit MX from its address (RFC 5321 5.1) and
	// read as SPF "none" to a receiver that does not enforce DMARC.
	Object.freeze({ type: 'MX', name: 'www', content: '.', priority: 0, proxied: false, comment: 'null MX, RFC 7505' }),
	Object.freeze({ type: 'TXT', name: 'www', content: '"v=spf1 -all"', proxied: false, comment: 'no sender' }),
	Object.freeze({ type: 'MX', name: '@', content: '.', priority: 0, proxied: false, comment: 'null MX, RFC 7505' }),
	Object.freeze({ type: 'TXT', name: '@', content: '"v=spf1 -all"', proxied: false, comment: 'no sender' }),
	Object.freeze({ type: 'TXT', name: '_dmarc', content: '"v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s"', proxied: false, comment: 'reject all' }),
	Object.freeze({ type: 'TXT', name: '*._domainkey', content: '"v=DKIM1; p="', proxied: false, comment: 'revoked key, RFC 6376 3.6.1' }),
]);

/** The settings, by the id the settings API uses. */
export const ZONE_SETTINGS = Object.freeze({
	email_obfuscation: 'off',
	automatic_https_rewrites: 'off',
	always_use_https: 'on',
	min_tls_version: '1.2',
	security_header: Object.freeze({
		strict_transport_security: Object.freeze({
			enabled: true,
			max_age: 31536000,
			include_subdomains: true,
			preload: true,
			nosniff: true,
		}),
	}),
});

/** The full name of a record. */
export const fqdn = (name, zone) => (name === '@' ? zone : `${name}.${zone}`);

/** Which record of the same name and type stands in the place of a wanted one. */
function samePlace(wanted, record, zone) {
	if (record.type !== wanted.type || record.name !== fqdn(wanted.name, zone)) return false;
	if (wanted.type !== 'TXT') return true;
	// Every TXT record at a key name is a key, whatever it starts with: DKIM
	// lets the v= tag be left out (RFC 6376 3.6.1).
	if (wanted.name.endsWith('_domainkey')) return true;
	// Several TXT records can share a name; the one in this place starts with the same tag.
	const tag = (text) => text.replace(/^"/, '').split(/[;\s]/, 1)[0].toLowerCase();
	return tag(record.content) === tag(wanted.content);
}

/** Whether a record already says what the wanted one says. */
function sameRecord(wanted, record) {
	const unquote = (text) => text.replace(/^"|"$/g, '');
	return (
		unquote(record.content) === unquote(wanted.content) &&
		Boolean(record.proxied) === wanted.proxied &&
		(wanted.priority === undefined || record.priority === wanted.priority)
	);
}

/**
 * What it takes to bring a zone to the records and settings above.
 *
 * A record that is missing is created. A place whose every record is right is
 * left alone. A record in the same place that says something else is a
 * conflict, even beside a right one: it is reported and never changed, since it
 * may be one the maintainer added.
 *
 * @param {object} options
 * @param {string} options.zone The zone name.
 * @param {{id: string, type: string, name: string, content: string, proxied?: boolean, priority?: number}[]} options.records
 *   The zone's records (GET /zones/:id/dns_records).
 * @param {Record<string, unknown>} options.settings The current value of each setting above, by id.
 * @returns {{create: object[], conflicts: string[], keep: string[], settings: {id: string, from: unknown, to: unknown}[]}}
 */
export function zonePlan({ zone, records, settings }) {
	const create = [];
	const conflicts = [];
	const keep = [];
	for (const wanted of DNS_RECORDS) {
		const here = records.filter((record) => samePlace(wanted, record, zone));
		const label = `${wanted.type} ${fqdn(wanted.name, zone)}`;
		if (here.length === 0) {
			const { name, ...rest } = wanted;
			create.push({ ...rest, name: fqdn(name, zone), ttl: 1 });
		} else if (here.every((record) => sameRecord(wanted, record))) {
			keep.push(label);
		} else {
			// One record that says something else spoils the place (a second MX
			// beside the null MX, a second SPF record), even beside a right one.
			const wrong = here.filter((record) => !sameRecord(wanted, record));
			conflicts.push(`${label}: holds ${wrong.map((r) => JSON.stringify(r.content)).join(', ')}, not ${JSON.stringify(wanted.content)}; left alone`);
		}
	}
	const changes = [];
	for (const [id, to] of Object.entries(ZONE_SETTINGS)) {
		const from = settings[id];
		if (!sameSetting(from, to)) changes.push({ id, from, to });
	}
	return { create, conflicts, keep, settings: changes };
}

/** Whether a setting's current value already holds every field the wanted one sets. */
function sameSetting(current, wanted) {
	if (wanted === null || typeof wanted !== 'object') return current === wanted;
	if (current === null || typeof current !== 'object') return false;
	return Object.entries(wanted).every(([key, value]) => sameSetting(current[key], value));
}
