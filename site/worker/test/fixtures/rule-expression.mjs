// A reader of the rules language, for the subset lib/rules.mjs writes, so a
// test can run the very expression a zone receives against a request instead
// of a model written beside it.
//
// It reads string literals, sets, parentheses, `not`, `and`, `or`, the
// operators `eq`, `ne`, `wildcard` and `in`, the functions `starts_with`,
// `ends_with`, `concat`, `wildcard_replace` and `any`, and the fields the
// rules name: `http.host`, `http.request.method`, `http.request.uri.path`
// and the Accept fields as `http.request.headers["accept"][*]`. Anything else
// throws, so an expression that grows a construct this reader does not know
// fails its test instead of passing it. `wildcard` and `wildcard_replace` are
// the models lib/rules.mjs already holds (case-insensitive, the whole value).
import { wildcardMatch, wildcardReplace } from '../../lib/rules.mjs';

const TOKEN = /\s*(?:("(?:[^"\\]|\\.)*")|([(){},])|([A-Za-z_][\w.]*(?:\["[^"]*"\])?(?:\[\*\])?))/y;

/**
 * The tokens of an expression.
 *
 * @param {string} text The expression.
 * @returns {{kind: 'string' | 'punct' | 'word', value: string}[]} The tokens.
 */
function tokens(text) {
	const out = [];
	TOKEN.lastIndex = 0;
	while (TOKEN.lastIndex < text.length) {
		const start = TOKEN.lastIndex;
		const match = TOKEN.exec(text);
		if (!match) {
			if (text.slice(start).trim() === '') break;
			throw new Error(`cannot read the expression at ${JSON.stringify(text.slice(start, start + 20))}`);
		}
		if (match[1] !== undefined) out.push({ kind: 'string', value: JSON.parse(match[1]) });
		else if (match[2] !== undefined) out.push({ kind: 'punct', value: match[2] });
		else out.push({ kind: 'word', value: match[3] });
	}
	return out;
}

/** The fields a request answers. */
function field(name, request) {
	switch (name) {
		case 'http.host':
			return request.host;
		case 'http.request.method':
			return request.method;
		case 'http.request.uri.path':
			return request.path;
		case 'http.request.headers["accept"][*]':
			return [...(request.accept ?? [])];
		default:
			throw new Error(`no field ${name} in this reader`);
	}
}

const COMPARISONS = {
	eq: (a, b) => a === b,
	ne: (a, b) => a !== b,
	wildcard: (a, b) => wildcardMatch(a, b),
	in: (a, b) => b.includes(a),
};

/**
 * Evaluates an expression for a request.
 *
 * @param {string} expression The rule's expression, or a target expression.
 * @param {{host: string, method: string, path: string, accept?: string[]}} request
 * @returns {boolean | string} What the expression gives.
 */
export function evaluate(expression, request) {
	const list = tokens(expression);
	let at = 0;
	const peek = () => list[at];
	const take = (value) => {
		const token = list[at];
		if (value !== undefined && token?.value !== value) throw new Error(`expected ${value}, found ${token?.value ?? 'the end'}`);
		at += 1;
		return token;
	};

	function orExpr() {
		let value = andExpr();
		while (peek()?.kind === 'word' && peek().value === 'or') {
			take();
			const right = andExpr();
			value = value || right;
		}
		return value;
	}
	function andExpr() {
		let value = notExpr();
		while (peek()?.kind === 'word' && peek().value === 'and') {
			take();
			const right = notExpr();
			value = value && right;
		}
		return value;
	}
	function notExpr() {
		if (peek()?.kind === 'word' && peek().value === 'not') {
			take();
			return !truth(notExpr());
		}
		return comparison();
	}
	function truth(value) {
		if (typeof value !== 'boolean') throw new Error(`${JSON.stringify(value)} is no truth value`);
		return value;
	}
	function comparison() {
		const left = operand();
		const op = peek();
		if (op?.kind === 'word' && op.value in COMPARISONS) {
			take();
			const right = operand();
			const test = COMPARISONS[op.value];
			return Array.isArray(left) ? left.map((item) => test(item, right)) : test(left, right);
		}
		return left;
	}
	function operand() {
		const token = take();
		if (!token) throw new Error('the expression ends early');
		if (token.kind === 'string') return token.value;
		if (token.value === '(') {
			const value = orExpr();
			take(')');
			return value;
		}
		if (token.value === '{') {
			const items = [];
			while (peek()?.value !== '}') items.push(take().value);
			take('}');
			return items;
		}
		if (token.kind === 'word' && peek()?.value === '(') return call(token.value);
		if (token.kind === 'word') return field(token.value, request);
		throw new Error(`unexpected ${token.value}`);
	}
	function call(name) {
		take('(');
		const args = [];
		while (peek()?.value !== ')') {
			args.push(orExpr());
			if (peek()?.value === ',') take(',');
		}
		take(')');
		switch (name) {
			case 'starts_with':
				return args[0].startsWith(args[1]);
			case 'ends_with':
				return args[0].endsWith(args[1]);
			case 'concat':
				return args.join('');
			case 'wildcard_replace':
				return wildcardReplace(args[0], args[1], args[2]);
			case 'any':
				if (!Array.isArray(args[0])) throw new Error('any() takes a comparison over a list');
				return args[0].some(Boolean);
			default:
				throw new Error(`no function ${name} in this reader`);
		}
	}

	const value = orExpr();
	if (at !== list.length) throw new Error(`unread tail: ${list.slice(at).map((t) => t.value).join(' ')}`);
	return value;
}

/**
 * What a redirect phase answers: the first rule whose expression holds, its
 * status and the address it sends to, the query kept when the rule says so.
 *
 * @param {object[]} rules The phase's rules, in order.
 * @param {{host: string, method?: string, path: string, query?: string, accept?: string[]}} request
 * @returns {{ref: string, status: number, location: string} | null} The answer, or null when no rule holds.
 */
export function redirectFor(rules, { method = 'GET', query = '', ...rest }) {
	const request = { method, ...rest };
	for (const rule of rules) {
		if (rule.enabled === false || evaluate(rule.expression, request) !== true) continue;
		const { status_code: status, target_url: target, preserve_query_string: keep } = rule.action_parameters.from_value;
		const location = target.value ?? evaluate(target.expression, request);
		return { ref: rule.ref, status, location: keep && query ? `${location}?${query}` : location };
	}
	return null;
}
