// What the software node's `softwareRequirements` leaves out of pyproject.toml.
//
// The structured-data check holds the sentence to the `[project]` table, as
// src/data/repo-stats.mjs reads it; it is a module of its own so that its
// tests can hand it a table of either shape: the lines that give each Python
// a floor of its own, as pyproject.toml does, and one floor per requirement.

/** "a", "a and b", "a, b and c". */
const listed = (items) => (items.length < 2 ? items.join('') : `${items.slice(0, -1).join(', ')} and ${items.at(-1)}`);

/** A value cut to a length a failure line can carry. */
const shown = (value) => {
	const text = JSON.stringify(value);
	return text === undefined ? 'undefined' : text.length > 120 ? `${text.slice(0, 117)}...` : text;
};

/** A comparison, `>= 2.0.2`, as a pattern: the spaces around the operator are the site's to choose. */
const comparison = ({ operator, version }) => `${RegExp.escape(operator)}\\s*${RegExp.escape(version)}`;

/** Version clauses, joined by "and" or by a comma. */
const comparisons = (clauses) => clauses.map(comparison).join('(?:\\s*,\\s*|\\s+and\\s+)');

/**
 * A phrase as one unit, bounded on both sides: a name that only ends with the
 * one given ("pyscipy") and a version that only starts with it ("2.0.20",
 * "2.0.2.1") are not it, and the full stop that ends the sentence is not part
 * of a version.
 */
const bounded = (source) => new RegExp(`(?<![\\w.-])${source}(?!\\w|\\.\\w)`);

/** A PEP 440 comparison of `requires-python`, ">=3.12". */
const CLAUSE = /^(~=|===|==|!=|<=|>=|<|>)\s*(\S+)$/;

/**
 * The phrase the site has to state for one requirement: its name, each of its
 * version clauses, and with a Python marker "on Python" and the marker's own
 * comparison, "==" being the one a sentence may leave out ("on Python 3.13").
 * A requirement with no marker holds for every Python, so a phrase that limits
 * it to some is not it. Written here, not taken from src/lib/pyproject.mjs, so
 * that a sentence that module writes wrong is not held to itself.
 *
 * @param {{name: string, clauses: {operator: string, version: string}[],
 *   marker: {operator: string, version: string}|null}} requirement The requirement.
 * @returns {RegExp} The phrase, over the sentence in lower case.
 */
function phraseOf({ name, clauses, marker }) {
	const versions = clauses.length > 0 ? `\\s*${comparisons(clauses)}` : '';
	const python = marker
		? `\\s+on\\s+python\\s*${marker.operator === '==' ? '(?:==\\s*)?' : `${RegExp.escape(marker.operator)}\\s*`}${RegExp.escape(marker.version)}`
		: '(?!\\s+on\\s+python)';
	return bounded(`${RegExp.escape(name.toLowerCase())}${versions}${python}`);
}

/** A requirement as pyproject.toml writes it, without its spaces, its marker in brackets. */
const shownRequirement = ({ text }) => {
	const [requirement, marker] = text.split(';').map((part) => part.replace(/\s+/g, ''));
	return marker ? `${requirement} (${marker})` : requirement;
};

/**
 * What the software node's requirements leave out of pyproject.toml: the
 * Python it requires, each requirement as one phrase with every version of
 * its clauses and the Python its marker limits it to, and every extra by name.
 * The words between the phrases are the site's; what is held is that each
 * phrase is there whole, so a floor stated for the Python of another floor, a
 * marker without its comparison or a version longer than the table's fails.
 *
 * @param {unknown} requirements The node's `softwareRequirements`.
 * @param {{requiresPython: string, dependencies: {text: string, name: string,
 *   clauses: {operator: string, version: string}[], marker: {operator: string, version: string}|null}[],
 *   extras: {name: string}[]}} project The `[project]` table, as src/lib/pyproject.mjs reads it.
 * @returns {string[]} The defects.
 */
export function requirementDefects(requirements, { requiresPython, dependencies, extras }) {
	if (typeof requirements !== 'string' || !requirements) {
		return [`SoftwareApplication softwareRequirements is ${shown(requirements)}, not a text naming what pyproject.toml requires`];
	}
	const sentence = requirements.toLowerCase();
	const missing = [];
	const floors = requiresPython.split(',').map((clause) => {
		const parsed = CLAUSE.exec(clause.trim());
		return parsed ? { operator: parsed[1], version: parsed[2] } : { operator: '', version: clause.trim() };
	});
	if (!bounded(`python\\s*${comparisons(floors)}`).test(sentence)) missing.push(`requires-python ${requiresPython}`);
	for (const requirement of dependencies) {
		if (!phraseOf(requirement).test(sentence)) missing.push(shownRequirement(requirement));
	}
	for (const extra of extras) {
		if (!new RegExp(`\\b${RegExp.escape(extra.name)}\\b`).test(requirements)) missing.push(`the extra ${extra.name}`);
	}
	return missing.length === 0
		? []
		: [`SoftwareApplication softwareRequirements leaves out ${listed(missing)}, which pyproject.toml gives`];
}
