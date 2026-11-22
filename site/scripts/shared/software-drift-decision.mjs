// The pass/fail decision of jmrp.io's software drift check, as this site
// runs it on its own software node (scripts/check-software-drift.mjs).
//
// jmrp.io publishes the same SoftwareApplication node as this site, under the
// same `@id`, and its CI compares the two (scripts/ci/check-software-drift.mjs
// in the jmrp.io repository); this site holds itself to the same comparison
// before it deploys. The two blocks below are VERBATIM copies of
// scripts/ci/software-drift-decision.mjs in the jmrp.io repository: the first
// from the comment above ACCEPTED_DIVERGENCES to the end of CONTRADICTABLE,
// the second from the comment above LIST_PROPERTIES to the end of
// classifyDivergences, so the two sites call the same values the same thing.
// projectValues, between them there, reads jmrp.io's projects.yaml; this site
// reads the feed generated from it, which already states each value as the
// graph does, and maps it in jmrpValues (scripts/check-software-drift.mjs).
// Change the decision there first, then copy the blocks here whole: on every
// run, scripts/check-software-drift.mjs reads the decision on jmrp.io's main
// branch and fails when either block differs from the copy, and
// scripts/check-software-drift.test.mjs compares the texts too when that
// repository is on the machine. Nothing here is imported from outside this
// repository.
// Do not reformat this file: the comparison is of the text.

/**
 * Divergences the author decided to keep, matched by project id and property
 * (never by text, so rewording the summary cannot silently lift or hide the
 * exception). An accepted divergence is still printed, as "accepted".
 *
 * gitlab-mcp-server: the action count in `summary.en` and the tool count on
 * its docs site measure different GitLab tiers, so both are true (author
 * decision, 2026-09-03; see `src/content/profile/projects.yaml`).
 *
 * cs-routeros-bouncer: `summary` gained its final full stop on 2026-11-21
 * (GEO audit #13), because the documentation hub's llms.txt printed the
 * sentence running into the license note after it. Its docs site, another
 * repository, still publishes the sentence without one. Delete the entry
 * once that site carries the full stop.
 *
 * kleidos: kleidos.dev lists post 011's Spanish article with the headline "Un
 * llavero con bloqueo ante fallos...", a title jmrp.io never published (the
 * post is "Una bóveda con bloqueo ante fallos..."). The fix belongs in the
 * Kleidos site's repository; this entry names that one article, so any other
 * headline it misstates still fails the run (GEO audit #13).
 *
 * @type {Readonly<Record<string, {properties: readonly string[], reason: string, decided: string}>>}
 */
export const ACCEPTED_DIVERGENCES = Object.freeze({
  "gitlab-mcp-server": Object.freeze({
    properties: Object.freeze(["description"]),
    reason:
      "the action count and the tool count measure different GitLab tiers",
    decided: "2026-09-03",
  }),
  "cs-routeros-bouncer": Object.freeze({
    properties: Object.freeze(["description"]),
    reason:
      "jmrp.io added the final full stop its docs site has yet to publish",
    decided: "2026-11-21",
  }),
  kleidos: Object.freeze({
    properties: Object.freeze([
      "subjectOf headline https://jmrp.io/es/blog/011-encrypt-then-mac-vault/#article",
    ]),
    reason:
      "kleidos.dev states a Spanish headline for post 011 that jmrp.io never published; the fix is in the Kleidos repository",
    decided: "2026-11-21",
  }),
});

/**
 * Properties of the shared `#software` node where a divergence is a
 * contradiction, not detail. `description@es` is the Spanish literal of
 * `description`, read apart from the English one.
 *
 * `operatingSystem` joined on 2026-11-07. /projects/ states it as a list
 * (["Linux", "macOS", "Windows"]) and the docs sites as one comma-joined
 * string ("Windows, Linux, macOS"), and nothing compared the two, so a site
 * that named other systems shipped unnoticed.
 *
 * `applicationSubCategory`, `alternateName`, `disambiguatingDescription` and
 * `keywords` joined on 2026-11-21 (GEO audit #13). mikroscope's docs site
 * said "Network monitoring" and /projects/ "Monitoring", and Kleidos's site
 * spelled its board vendor "LILYGO" where projects.yaml wrote "LilyGO", on
 * properties nothing compared. Each localized property is read as its English
 * value and, under `<property>@es`, its Spanish one, as `description` is.
 *
 * @type {readonly string[]}
 */
export const CONTRADICTABLE = Object.freeze([
  "name",
  "alternateName",
  "description",
  "description@es",
  "disambiguatingDescription",
  "disambiguatingDescription@es",
  "keywords",
  "keywords@es",
  "license",
  "programmingLanguage",
  "applicationCategory",
  "applicationSubCategory",
  "operatingSystem",
  "codeRepository",
  "url",
]);

/**
 * Properties whose text can name several items in one comma-joined string.
 * schema.org's own examples write `operatingSystem` as "Windows 7, OS X 10.6,
 * Android 1.6" and `applicationCategory` as "Game, Multimedia"; a project in
 * two languages can write `programmingLanguage` the same way. jmrp.io splits
 * `operatingSystem` into a list (`operatingSystems()` in
 * `src/utils/projects.ts`) and the docs sites keep the string, so the same
 * systems arrive in two shapes and have to be compared as items.
 *
 * @type {readonly string[]}
 */
export const LIST_PROPERTIES = Object.freeze([
  "operatingSystem",
  "applicationCategory",
  "programmingLanguage",
]);

/**
 * Orders two strings by UTF-16 code unit, the one order that never calls two
 * different strings equal (`localeCompare` does, for two spellings of the
 * same accented letter). Pure.
 *
 * @param {string} a - One string.
 * @param {string} b - The other.
 * @returns {number} Negative, zero or positive, as `sort` expects.
 */
const byCodeUnit = (a, b) => Number(a > b) - Number(a < b);

/**
 * One JSON-LD value as canonical text: object keys sorted, every array read
 * as the unordered set JSON-LD makes it, and a one-element array the same as
 * its element. Pure.
 *
 * @param {unknown} value - A parsed JSON-LD value.
 * @returns {string} Text that is equal for two values exactly when they state
 *   the same thing, whatever the order of their arrays and keys.
 */
export function canonicalJson(value) {
  if (Array.isArray(value)) {
    const items = [...new Set(value.map((entry) => canonicalJson(entry)))].sort(
      byCodeUnit,
    );
    return items.length === 1 ? items[0] : `[${items.join(",")}]`;
  }
  if (value !== null && typeof value === "object") {
    const entries = Object.keys(value)
      .sort(byCodeUnit)
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`);
    return `{${entries.join(",")}}`;
  }
  return JSON.stringify(value ?? null);
}

/**
 * The names one item of a list property stands for: a string split at its
 * commas, a language-tagged literal the same way, and a node by its `name`
 * (a `ComputerLanguage` named "Go" is "Go"). Pure.
 *
 * @param {unknown} item - One value of the property.
 * @returns {string[] | null} The names, or `null` for an item that names
 *   nothing this way and is compared whole.
 */
function listNames(item) {
  const text = typeof item === "string" ? item : item?.["@value"];
  if (typeof text === "string") {
    return text
      .split(",")
      .map((name) => name.trim())
      .filter((name) => name !== "");
  }
  return typeof item?.name === "string" ? [item.name.trim()] : null;
}

/**
 * The values a property states, each as canonical text. A missing value
 * states none; an array states each of its items. Pure.
 *
 * @param {unknown} value - The property's value as published.
 * @param {{ list?: boolean }} [options] - `list` reads each item as
 *   {@link listNames} does, for the properties in {@link LIST_PROPERTIES}.
 * @returns {Set<string>} The stated values.
 */
export function statedValues(value, { list = false } = {}) {
  const stated = new Set();
  for (const item of [value ?? []].flat()) {
    const names = list ? listNames(item) : null;
    if (names === null) stated.add(canonicalJson(item));
    else for (const name of names) stated.add(JSON.stringify(name));
  }
  return stated;
}

/**
 * Whether two values of one property state the same set of things. Pure.
 *
 * @param {unknown} theirs - The value on the project's own site.
 * @param {unknown} ours - The value jmrp.io states.
 * @param {{ list?: boolean }} [options] - See {@link statedValues}.
 * @returns {boolean} True when neither side states a value the other lacks.
 */
export function sameValues(theirs, ours, options = {}) {
  const a = statedValues(theirs, options);
  const b = statedValues(ours, options);
  return a.size === b.size && [...a].every((value) => b.has(value));
}

/**
 * What each side of a divergent property states that the other does not,
 * for the report. Pure.
 *
 * @param {string} property - The property compared.
 * @param {unknown} theirs - The value on the project's own site.
 * @param {unknown} ours - The value from projects.yaml.
 * @returns {{ onlyTheirs: string[], onlyOurs: string[] }} The values each
 *   side alone states, each as JSON text (so a name prints quoted and a value
 *   with commas in it stays one value), sorted.
 */
export function valueDifference(property, theirs, ours) {
  const options = { list: LIST_PROPERTIES.includes(property) };
  const a = statedValues(theirs, options);
  const b = statedValues(ours, options);
  return {
    onlyTheirs: [...a.difference(b)].sort(byCodeUnit),
    onlyOurs: [...b.difference(a)].sort(byCodeUnit),
  };
}

/**
 * The properties whose values the two sides state differently. A property
 * only one side states is not compared: a site that leaves it out says
 * nothing against it. Pure.
 *
 * @param {Record<string, unknown>} theirs - The project site's values, by
 *   property.
 * @param {Record<string, unknown>} ours - The values from projects.yaml.
 * @param {readonly string[]} [properties] - What to compare.
 * @returns {string[]} The divergent properties, in the order given.
 */
export function divergentProperties(theirs, ours, properties = CONTRADICTABLE) {
  return properties.filter(
    (p) =>
      theirs[p] !== undefined &&
      ours[p] !== undefined &&
      !sameValues(theirs[p], ours[p], { list: LIST_PROPERTIES.includes(p) }),
  );
}

/**
 * Splits a project's divergent properties into contradictions and accepted
 * ones. Pure.
 *
 * @param {string} projectId - Project id from projects.yaml.
 * @param {readonly string[]} properties - Properties whose values differ.
 * @param {typeof ACCEPTED_DIVERGENCES} [accepted] - Exception table.
 * @returns {{contradicting: string[], accepted: string[]}} The split.
 */
export function classifyDivergences(
  projectId,
  properties,
  accepted = ACCEPTED_DIVERGENCES,
) {
  const allowed = new Set(accepted[projectId]?.properties);
  return {
    contradicting: properties.filter((p) => !allowed.has(p)),
    accepted: properties.filter((p) => allowed.has(p)),
  };
}
