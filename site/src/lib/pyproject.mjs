/**
 * What the site states about the package, read from its `[project]` table.
 *
 * The software node of the structured data used to say "Python >= 3.12 with
 * NumPy and SciPy (matplotlib and numba optional)", a sentence typed once and
 * edited once since, by then naming two of the five optional extras; the
 * landing page typed the install line and the Python floor twice more. Each of
 * them is written here from the table pip installs from, so the page and the
 * package cannot disagree.
 *
 * A requirement is read as PEP 508 writes it, as far as the site states it in
 * words: a name, its version clauses, and a marker that limits it to some
 * versions of Python, which is how the package gives each Python a floor of
 * its own. Anything else, an extra of a requirement, a URL, a marker on the
 * platform, stops the build naming the requirement, since a sentence that
 * left it out would state a requirement the package does not have.
 */

const NAME = /^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)\s*/;
const CLAUSE = /^(~=|===|==|!=|<=|>=|<|>)\s*([0-9][0-9A-Za-z.*+!_-]*)$/;
const PYTHON_MARKER = /^python_version\s*(==|!=|<=|>=|<|>)\s*(['"])(\d+(?:\.\d+)*)\2$/;

/**
 * One requirement, as PEP 508 writes it.
 *
 * @param {string} text A dependency string of the `[project]` table.
 * @returns {{text: string, name: string, clauses: {operator: string, version: string}[],
 *   marker: {operator: string, version: string}|null}} Its name, its version clauses and
 *   the Python versions it is limited to, if any.
 */
export function parseRequirement(text) {
	const refuse = (why) => {
		throw new Error(`pyproject.toml: the requirement ${JSON.stringify(text)} ${why}, which the site cannot state`);
	};
	const [requirement, marker, ...more] = text.split(';');
	if (more.length > 0) refuse('carries more than one marker');
	const name = NAME.exec(requirement.trim());
	if (!name) refuse('names no distribution');
	const rest = requirement.trim().slice(name[0].length).trim();
	if (rest.startsWith('[')) refuse('asks for extras of the distribution');
	if (rest.startsWith('@')) refuse('is a URL');
	const clauses = rest
		? rest.split(',').map((clause) => {
				const parsed = CLAUSE.exec(clause.trim());
				if (!parsed) refuse(`has a version clause ${JSON.stringify(clause.trim())} PEP 440 does not define`);
				return { operator: parsed[1], version: parsed[2] };
			})
		: [];
	let python = null;
	if (marker !== undefined) {
		const parsed = PYTHON_MARKER.exec(marker.trim());
		if (!parsed) refuse('has a marker other than one comparison of python_version');
		python = { operator: parsed[1], version: parsed[3] };
	}
	return { text, name: name[1], clauses, marker: python };
}

/**
 * The parts of the `[project]` table the site states, checked for their types.
 *
 * @param {Record<string, any>} document pyproject.toml, as `parseToml` reads it.
 * @returns {{name: string, requiresPython: string, dependencies: ReturnType<typeof parseRequirement>[],
 *   extras: {name: string, requirements: ReturnType<typeof parseRequirement>[]}[]}} The project.
 */
export function readProject(document) {
	const project = document.project;
	if (!project || typeof project !== 'object') throw new Error('pyproject.toml has no [project] table');
	const text = (key) => {
		if (typeof project[key] !== 'string' || !project[key]) {
			throw new Error(`pyproject.toml: [project] ${key} is not a string`);
		}
		return project[key];
	};
	const requirements = (list, where) => {
		if (!Array.isArray(list) || !list.every((item) => typeof item === 'string')) {
			throw new Error(`pyproject.toml: ${where} is not a list of strings`);
		}
		return list.map(parseRequirement);
	};
	const optional = project['optional-dependencies'] ?? {};
	return {
		name: text('name'),
		requiresPython: text('requires-python'),
		dependencies: requirements(project.dependencies ?? [], '[project] dependencies'),
		extras: Object.entries(optional).map(([name, list]) => ({
			name,
			requirements: requirements(list, `[project.optional-dependencies] ${name}`),
		})),
	};
}

/**
 * The page the software node links for each SPDX licence the package may
 * declare. A licence of LicenseRef- form is linked to its text in the
 * repository instead, the file `license-files` gives it.
 */
export const SPDX_PAGES = Object.freeze({ MIT: 'https://opensource.org/license/MIT' });

/**
 * The licences the package declares, as PEP 639 writes them in `[project]`:
 * the `license` expression, identifiers joined by AND, and the
 * `license-files` that hold their texts.
 *
 * The software node of every page listed both licences from a literal while
 * the landing page said MIT alone; read here, the node states what PyPI
 * states. An expression the site cannot state as a list (OR, WITH,
 * parentheses), an identifier whose page it does not know, a LicenseRef
 * without its file under LICENSES/ and a file that is the text of no
 * licence the expression names each stop the build, naming it.
 *
 * @param {Record<string, any>} document pyproject.toml, as `parseToml` reads it.
 * @param {string} repositoryUrl The repository a LicenseRef's file is linked in.
 * @returns {{expression: string, licenses: {id: string, file: string, url: string}[]}}
 *   The expression and, in its order, each licence with the file of its text
 *   and the address the software node gives it.
 */
export function readLicenses(document, repositoryUrl) {
	const project = document.project;
	if (!project || typeof project !== 'object') throw new Error('pyproject.toml has no [project] table');
	const expression = project.license;
	if (typeof expression !== 'string' || !expression.trim()) {
		throw new Error('pyproject.toml: [project] license is not an SPDX expression');
	}
	const files = project['license-files'];
	if (!Array.isArray(files) || !files.every((file) => typeof file === 'string')) {
		throw new Error('pyproject.toml: [project] license-files is not a list of strings');
	}
	const ids = expression.trim().split(/\s+AND\s+/);
	for (const id of ids) {
		if (!/^[A-Za-z0-9][A-Za-z0-9.+-]*$/.test(id) || /^(?:OR|WITH|AND)$/.test(id)) {
			throw new Error(
				`pyproject.toml: license ${JSON.stringify(expression)} is more than licences joined by AND ` +
					`(${JSON.stringify(id)}), which the site cannot state as a list`,
			);
		}
	}
	const plain = ids.filter((id) => !id.startsWith('LicenseRef-'));
	const textOf = (id) => {
		const own = `LICENSES/${id}.txt`;
		if (files.includes(own)) return own;
		if (!id.startsWith('LicenseRef-') && plain.length === 1 && files.includes('LICENSE')) return 'LICENSE';
		throw new Error(`pyproject.toml: license names ${id}, and license-files holds no text of it (${own})`);
	};
	const unknown = plain.find((id) => !Object.hasOwn(SPDX_PAGES, id));
	if (unknown !== undefined) {
		throw new Error(`pyproject.toml: license names ${unknown}, whose page the site does not know (SPDX_PAGES in src/lib/pyproject.mjs)`);
	}
	const licenses = ids.map((id) => {
		const file = textOf(id);
		return { id, file, url: id.startsWith('LicenseRef-') ? `${repositoryUrl}/blob/main/${file}` : SPDX_PAGES[id] };
	});
	const texts = new Set(licenses.map((license) => license.file));
	for (const file of files) {
		if (!texts.has(file)) {
			throw new Error(
				`pyproject.toml: license-files holds ${file}, the text of no licence ${JSON.stringify(expression)} names`,
			);
		}
	}
	return { expression, licenses };
}

/** A version clause as the site writes it: `>= 3.12`. */
const clauseText = ({ operator, version }) => `${operator} ${version}`;

/**
 * The oldest Python the package installs on, from `requires-python`, for a
 * sentence that says "3.12 or newer".
 *
 * @param {string} requiresPython The specifier, `>=3.12`.
 * @returns {string} The version, `3.12`.
 */
export function pythonFloor(requiresPython) {
	const floor = /^>=\s*(\d+(?:\.\d+)*)$/.exec(requiresPython.trim());
	if (!floor) {
		throw new Error(
			`pyproject.toml: requires-python ${JSON.stringify(requiresPython)} is not one floor, ` +
				'so the site cannot say which Python "or newer" the package needs',
		);
	}
	return floor[1];
}

/**
 * The Python the package runs on, as the API pages state it: `Python >= 3.12`.
 *
 * @param {string} requiresPython The specifier of `requires-python`.
 * @returns {string} The platform.
 */
export function platformOf(requiresPython) {
	const clauses = requiresPython.split(',').map((clause) => {
		const parsed = CLAUSE.exec(clause.trim());
		if (!parsed) throw new Error(`pyproject.toml: requires-python ${JSON.stringify(requiresPython)} is not a specifier`);
		return clauseText({ operator: parsed[1], version: parsed[2] });
	});
	return `Python ${clauses.join(', ')}`;
}

/**
 * The line that installs the package with everything the guides use, the
 * `full` extra, quoted so that a shell does not read the brackets.
 *
 * @param {{name: string, extras: {name: string}[]}} project The project.
 * @returns {string} `pip install "phonometry[full]"`.
 */
export function installLine(project) {
	if (!project.extras.some((extra) => extra.name === 'full')) {
		throw new Error('pyproject.toml has no full extra, which the install line the site gives installs');
	}
	return `pip install "${project.name}[full]"`;
}

/** "a", "a and b", "a, b and c". */
const listed = (items) => (items.length < 2 ? items.join('') : `${items.slice(0, -1).join(', ')} and ${items.at(-1)}`);

/** A requirement as the site writes it: `numpy >= 2.1.0 on Python 3.13`. */
function requirementText({ name, clauses, marker }) {
	const versions = clauses.length > 0 ? ` ${clauses.map(clauseText).join(' and ')}` : '';
	const python = marker
		? ` on Python ${marker.operator === '==' ? marker.version : clauseText(marker)}`
		: '';
	return `${name}${versions}${python}`;
}

/**
 * What the package needs and what it offers, in one sentence for the software
 * node's `softwareRequirements`: the Python it needs, each requirement with
 * its floor and the Python it holds for, and every optional extra by name.
 *
 * An extra that installs exactly what two or more other extras do, as `full`
 * does, is named for what it gathers rather than listed beside them.
 *
 * @param {ReturnType<typeof readProject>} project The project.
 * @returns {string} The sentence.
 */
export function describeRequirements(project) {
	const required = project.dependencies.map(requirementText);
	const texts = (extra) => new Set(extra.requirements.map((requirement) => requirement.text));
	const gathers = new Map();
	for (const extra of project.extras) {
		const own = texts(extra);
		const parts = project.extras.filter(
			(other) =>
				other !== extra && other.requirements.length > 0 && [...texts(other)].every((text) => own.has(text)),
		);
		const covered = new Set(parts.flatMap((part) => [...texts(part)]));
		if (parts.length >= 2 && covered.size === own.size) gathers.set(extra.name, parts.map((part) => part.name));
	}
	const plain = project.extras.filter((extra) => !gathers.has(extra.name)).map((extra) => extra.name);
	const bundles = [...gathers].map(([name, parts]) => `${name} installs ${listed(parts)}`);
	const extras =
		plain.length + bundles.length === 0
			? ''
			: ` Optional extras: ${listed(plain)}${bundles.length > 0 ? `; ${bundles.join('; ')}` : ''}.`;
	return `${platformOf(project.requiresPython)}${required.length > 0 ? ` with ${listed(required)}` : ''}.${extras}`;
}
