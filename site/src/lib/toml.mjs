/**
 * A reader of the TOML pyproject.toml is written in.
 *
 * The site reads the package's Python floor, its requirements and its extras
 * from pyproject.toml (src/data/repo-stats.mjs), and the Python tests import
 * that module too (tests/test_minimum_requirements.py), where none of the
 * site's packages is installed, so the reader has no dependency of its own.
 * It reads the TOML the file is written in, whole: tables and arrays of
 * tables, bare, quoted and dotted keys, the four kinds of string, integers,
 * floats, booleans, arrays over several lines with comments between their
 * values, and inline tables, with its lines ended by a line feed or by CRLF.
 *
 * What it does not read, a date or a hexadecimal integer among them, stops it
 * with the line it met it on rather than being read as something else: a
 * misread requirement would be published on every page.
 * scripts/pyproject.test.mjs holds its reading of the whole file to Python's
 * own TOML reader.
 */

const BARE_KEY = /[A-Za-z0-9_-]/;
const ESCAPES = { b: '\b', t: '\t', n: '\n', f: '\f', r: '\r', '"': '"', '\\': '\\' };

/**
 * Read `text` as TOML.
 *
 * @param {string} text The document.
 * @param {string} [source] What the document is, for the errors.
 * @returns {Record<string, unknown>} The document's root table.
 */
export function parseToml(text, source = 'TOML') {
	let at = 0;
	const root = {};

	const lineOf = (offset) => text.slice(0, offset).split('\n').length;
	const fail = (message, offset = at) => {
		throw new Error(`${source} line ${lineOf(offset)}: ${message}`);
	};
	const peek = (length = 1) => text.slice(at, at + length);
	const skipSpaces = () => {
		while (peek() === ' ' || peek() === '\t') at += 1;
	};
	const skipComment = () => {
		if (peek() === '#') while (at < text.length && peek() !== '\n') at += 1;
	};
	// Inside an array: spaces, newlines and comments, in any number.
	const skipBlank = () => {
		for (;;) {
			const before = at;
			skipSpaces();
			skipComment();
			if (peek() === '\n' || peek(2) === '\r\n') at += peek() === '\n' ? 1 : 2;
			if (at === before) return;
		}
	};
	const endOfLine = () => {
		skipSpaces();
		skipComment();
		if (at < text.length && peek() !== '\n' && peek(2) !== '\r\n') fail('unexpected text after the value');
	};

	/** The length of the line end at `offset`, a line feed or CRLF, or 0 where there is none. */
	const lineEndAt = (offset) => (text.startsWith('\r\n', offset) ? 2 : text[offset] === '\n' ? 1 : 0);

	/**
	 * Stop on a control character a string may not hold: any but the tab, a
	 * carriage return on its own among them. A multi-line string's line ends
	 * are read before this is asked.
	 */
	const refuseControl = (char, offset) => {
		if (/[\u0000-\u0008\u000a-\u001f\u007f]/.test(char)) {
			const code = char.codePointAt(0).toString(16).toUpperCase().padStart(4, '0');
			fail(`a string holds U+${code}, a control character TOML does not allow there`, offset);
		}
	};

	function basicString() {
		const start = at;
		const multiline = peek(3) === '"""';
		at += multiline ? 3 : 1;
		// The line end right after the opening quotes is not part of the
		// string, CRLF as much as a line feed, and every other line end in it
		// reads as one line feed, as Python's own reader reads it.
		if (multiline) at += lineEndAt(at);
		let value = '';
		for (;;) {
			if (at >= text.length || (!multiline && lineEndAt(at) > 0)) fail('a string is not closed', start);
			if (multiline ? peek(3) === '"""' : peek() === '"') {
				at += multiline ? 3 : 1;
				return value;
			}
			const lineEnd = multiline ? lineEndAt(at) : 0;
			if (lineEnd > 0) {
				value += '\n';
				at += lineEnd;
				continue;
			}
			const char = peek();
			at += 1;
			if (char !== '\\') {
				refuseControl(char, at - 1);
				value += char;
				continue;
			}
			const escape = peek();
			if (multiline && /[ \t\r\n]/.test(escape)) {
				// A backslash at the end of a line joins it to the next one.
				while (/[ \t\r\n]/.test(peek()) && at < text.length) at += 1;
			} else if (escape in ESCAPES) {
				value += ESCAPES[escape];
				at += 1;
			} else if (escape === 'u' || escape === 'U') {
				const digits = escape === 'u' ? 4 : 8;
				const hex = text.slice(at + 1, at + 1 + digits);
				if (!new RegExp(`^[0-9A-Fa-f]{${digits}}$`).test(hex)) fail(`\\${escape} is not followed by ${digits} hexadecimal digits`);
				value += String.fromCodePoint(Number.parseInt(hex, 16));
				at += 1 + digits;
			} else {
				fail(`\\${escape} is not an escape TOML defines`);
			}
		}
	}

	function literalString() {
		const start = at;
		const multiline = peek(3) === "'''";
		at += multiline ? 3 : 1;
		if (multiline) at += lineEndAt(at);
		const end = text.indexOf(multiline ? "'''" : "'", at);
		const newline = text.indexOf('\n', at);
		if (end < 0 || (!multiline && newline >= 0 && newline < end)) fail('a string is not closed', start);
		let value = '';
		for (let offset = at; offset < end; ) {
			const lineEnd = multiline ? lineEndAt(offset) : 0;
			if (lineEnd > 0) {
				value += '\n';
				offset += lineEnd;
				continue;
			}
			refuseControl(text[offset], offset);
			value += text[offset];
			offset += 1;
		}
		at = end + (multiline ? 3 : 1);
		return value;
	}

	function key() {
		const parts = [];
		for (;;) {
			skipSpaces();
			if (peek() === '"') parts.push(basicString());
			else if (peek() === "'") parts.push(literalString());
			else {
				const start = at;
				while (BARE_KEY.test(peek())) at += 1;
				if (at === start) fail('a key is missing');
				parts.push(text.slice(start, at));
			}
			skipSpaces();
			if (peek() !== '.') return parts;
			at += 1;
		}
	}

	function value() {
		const char = peek();
		if (char === '"') return basicString();
		if (char === "'") return literalString();
		if (char === '[') return array();
		if (char === '{') return inlineTable();
		const word = /^[A-Za-z0-9_.:+-]+/.exec(text.slice(at))?.[0] ?? '';
		if (!word) fail('a value is missing');
		if (/^\d{4}-\d{2}-\d{2}/.test(word) || /^\d{2}:\d{2}/.test(word)) fail(`${word} is a date or a time, which this reader does not read`);
		at += word.length;
		if (word === 'true') return true;
		if (word === 'false') return false;
		if (/^[+-]?(?:0|[1-9](?:_?\d)*)$/.test(word)) return Number(word.replaceAll('_', ''));
		if (/^[+-]?(?:0|[1-9](?:_?\d)*)(?:\.\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)?$/.test(word)) {
			return Number(word.replaceAll('_', ''));
		}
		return fail(`${word} is not a value this reader reads`, at - word.length);
	}

	function array() {
		const start = at;
		at += 1;
		const items = [];
		for (;;) {
			skipBlank();
			if (at >= text.length) fail('an array is not closed', start);
			if (peek() === ']') {
				at += 1;
				return items;
			}
			items.push(value());
			skipBlank();
			if (at >= text.length) fail('an array is not closed', start);
			if (peek() === ',') at += 1;
			else if (peek() !== ']') fail('array values are not separated by a comma');
		}
	}

	function inlineTable() {
		at += 1;
		const table = {};
		skipSpaces();
		if (peek() === '}') {
			at += 1;
			return table;
		}
		for (;;) {
			assign(table, key());
			skipSpaces();
			if (peek() === '}') {
				at += 1;
				return table;
			}
			if (peek() !== ',') fail('inline table entries are not separated by a comma');
			at += 1;
		}
	}

	// `key = value`, with the key's dotted parts as tables inside `table`.
	function assign(table, parts) {
		const offset = at;
		skipSpaces();
		if (peek() !== '=') fail(`${parts.join('.')} has no "=" after it`);
		at += 1;
		skipSpaces();
		if (peek() === '\n' || peek() === '#' || at >= text.length) fail(`${parts.join('.')} has no value`);
		let target = table;
		for (const part of parts.slice(0, -1)) {
			target[part] ??= {};
			target = target[part];
		}
		const last = parts.at(-1);
		if (Object.hasOwn(target, last)) fail(`${parts.join('.')} is defined twice`, offset);
		target[last] = value();
	}

	// The table a header names, made on the way if it is not there yet.
	function tableAt(parts, list) {
		let target = root;
		for (const [i, part] of parts.entries()) {
			const isLast = i === parts.length - 1;
			if (isLast && list) {
				target[part] ??= [];
				if (!Array.isArray(target[part])) fail(`[[${parts.join('.')}]] names a table, not an array of tables`);
				const table = {};
				target[part].push(table);
				return table;
			}
			target[part] ??= {};
			target = Array.isArray(target[part]) ? target[part].at(-1) : target[part];
		}
		return target;
	}

	let current = root;
	while (at < text.length) {
		skipBlank();
		if (at >= text.length) break;
		if (peek() === '[') {
			const list = peek(2) === '[[';
			at += list ? 2 : 1;
			const parts = key();
			if (peek(list ? 2 : 1) !== (list ? ']]' : ']')) fail('a table header is not closed');
			at += list ? 2 : 1;
			current = tableAt(parts, list);
		} else {
			assign(current, key());
		}
		endOfLine();
	}
	return root;
}
