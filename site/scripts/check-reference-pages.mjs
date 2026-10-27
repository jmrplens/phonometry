// Behaviour checks for the two largest reference pages, which were slimmed
// and split so that a search engine reads all of them.
//
// The conformance report lost every byte a row did not need: the scoped
// class on each element, the lowercased copy of the row's text the search
// used to read, the class on each numeric cell and the SVG of each verdict
// mark. What has to survive that is behaviour, and only a browser can show
// it: the search still finds a row by the citation as the source writes it,
// a citation of several documents pasted whole included, the domain and
// failing filters still narrow the tables, a link to one row still opens the
// section that holds it, and the marks are still drawn, each section heading
// keeping Starlight's disclosure chevron beside its own.
//
// The errata registry became an index and one page per document family. A
// link written against the old single page, `/reference/errata/#<entry>`,
// has to land on the entry's new page, and a fragment the index holds itself
// has to stay where it is. The index lists every entry as its heading reads,
// mathematics typeset, not as the plain text a typeset formula leaves behind.
// And a family page is ranked in the site search by an empty title rather
// than its own, which the search panel must still show
// (src/lib/search-ui.mjs): the index check in check-search-designation.mjs
// reads Pagefind directly and never sees the panel.
//
// The published catalogues became an overview and one page per catalogue,
// with the markup of their rows cut to what a row's position does not say.
// The finder that was the one place to choose a catalogue, a material and a
// table now chooses among pages: it still lists every catalogue with its row
// count and opens the chosen one at its table, but only from the button
// beside the select, so a keyboard reader can walk the list by arrow or by
// letter without leaving the page; it filters the rows by name (on the
// Spanish page by the book's English name too) and by published table, and
// says so when nothing is left; every word its filter suggests, on every
// catalogue page and in both languages, finds a row of that catalogue
// through the finder itself; the marks still open their explanation on a
// click; and a phone still gets each row as a card, labelled by its column,
// with the cells the row does not have left out. A link to a section of the
// old single page has to land on that catalogue's page.
//
// Usage: node scripts/check-reference-pages.mjs [--base http://localhost:4321]
import { catalogueSlugs } from '../src/data/topics.mjs';
import { BASE_PATH, baseFrom, createExpect, launchBrowser } from './shared/audit.mjs';

const BASE = baseFrom();
const browser = await launchBrowser();
const { expect, failures } = createExpect();

/** Load a page with its scripts run, and hand back the tab. */
async function open(path) {
	const page = await browser.newPage();
	await page.setViewport({ width: 1280, height: 900 });
	await page.goto(`${BASE}${BASE_PATH}${path}`, { waitUntil: 'networkidle0', timeout: 90000 });
	return page;
}

// --- The conformance report ------------------------------------------------

for (const path of ['/reference/conformance/', '/es/reference/conformance/']) {
	const page = await open(path);

	const controls = await page.evaluate(() => {
		const box = document.querySelector('[data-controls]');
		return { present: !!box, shown: !!box && !box.hidden };
	});
	expect(`${path}: the controls are offered once the script runs`, controls, {
		present: true,
		shown: true,
	});

	/** Type a query into the search and report what the tables then show. */
	const search = async (query) => {
		await page.$eval('[data-search]', (input) => {
			input.value = '';
		});
		await page.type('[data-search]', query);
		return page.evaluate(() => {
			const rows = [...document.querySelectorAll('tr[data-verdict]')];
			const visible = rows.filter((row) => !row.hidden && !row.closest('details')?.hidden);
			return {
				total: rows.length,
				visible: visible.length,
				standards: visible.map((row) => row.cells[1].textContent.replace(/\s+/g, ' ').trim()),
				cites: visible.map((row) => row.dataset.cite ?? ''),
				// Everything the search reads: every cell but the verdict.
				texts: visible.map((row) =>
					[...row.cells]
						.slice(1)
						.map((cell) => cell.textContent)
						.join(' ')
						.replace(/\s+/g, ' '),
				),
			};
		});
	};

	// A designation finds its rows and only rows that name it.
	{
		const got = await search('ISO 3382-1');
		expect(
			`${path}: searching "ISO 3382-1" narrows the report to rows that name it`,
			{
				some: got.visible > 0,
				fewer: got.visible < got.total,
				allName: got.standards.every((text) => text.toLowerCase().includes('iso 3382-1')),
			},
			{ some: true, fewer: true, allName: true },
		);
	}

	// The citation as the source writes it. ANSI prints its edition after a
	// hyphen, and the row shows it after a colon; both find the row.
	for (const query of ['ANSI S1.11-2004', 'ANSI S1.11:2004']) {
		const got = await search(query);
		expect(
			`${path}: searching "${query}" finds the rows that cite ANSI S1.11-2004`,
			{
				some: got.visible > 0,
				allName: got.standards.every((text) => text.includes('ANSI S1.11:2004')),
			},
			{ some: true, allName: true },
		);
	}

	// A part number is not a prefix of an edition: "IEC 61260-1" must not
	// find the rows of IEC 61260:1995. A row may name part 1 outside its
	// citation (a quantity "of IEC 61260-1"), and the search reads that too,
	// so the row is judged on all it shows.
	{
		const got = await search('IEC 61260-1');
		expect(
			`${path}: searching "IEC 61260-1" finds no row of IEC 61260:1995 alone`,
			{
				some: got.visible > 0,
				allPartOne: got.texts.every((text) => text.includes('IEC 61260-1')),
			},
			{ some: true, allPartOne: true },
		);
	}

	// A citation of several documents, pasted whole as the report prints it
	// in "Closest to the limit" and in docs/CONFORMANCE.md. The cells write
	// the connector between the documents as words, so only the citation the
	// row keeps in `data-cite` can match it. One literal, and the first
	// citation the page holds for each connector the report prints.
	{
		const samples = await page.evaluate(() => {
			const cites = [...document.querySelectorAll('tr[data-cite]')].map((row) => row.dataset.cite);
			return {
				count: cites.length,
				picked: [' vs ', ' / ', ' + ', ' via ', ' against '].map(
					(connector) => cites.find((cite) => cite.includes(connector)) ?? null,
				),
			};
		});
		expect(`${path}: rows of several documents carry their citation`, samples.count > 0, true);
		for (const cite of new Set(['ISO 3747:2010 Eq. 11 vs ISO 3741:2010 Eq. 21', ...samples.picked])) {
			if (!cite) continue;
			const got = await search(cite);
			expect(`${path}: searching the whole citation "${cite}" finds its row`, got.cites.includes(cite), true);
		}
	}

	// A query that matches nothing says so.
	{
		const got = await search('zzzz-no-such-standard');
		const empty = await page.$eval('[data-empty]', (note) => !note.hidden);
		expect(`${path}: a search that matches nothing shows the empty note`, {
			visible: got.visible,
			empty,
		}, { visible: 0, empty: true });
	}

	// The domain filter: one domain, and only that one.
	{
		await page.$eval('[data-search]', (input) => {
			input.value = '';
			input.dispatchEvent(new Event('input'));
		});
		const domain = await page.$eval('[data-domain] option:nth-child(3)', (option) => option.value);
		await page.select('[data-domain]', domain);
		const got = await page.evaluate((wanted) => {
			const sections = [...document.querySelectorAll('[data-domain-section]')];
			const shown = sections.filter((section) => !section.hidden);
			return {
				shown: shown.map((section) => section.dataset.domainSection),
				open: shown.every((section) => section.open),
				rows: shown.flatMap((section) => [...section.querySelectorAll('tr[data-verdict]')]).length > 0,
				wanted,
			};
		}, domain);
		expect(`${path}: the domain filter shows the chosen domain alone, opened`, {
			shown: got.shown,
			open: got.open,
			rows: got.rows,
		}, { shown: [domain], open: true, rows: true });
		await page.select('[data-domain]', '');
	}

	// "Failing rows only" shows the verdict `fail` and nothing else.
	{
		await page.click('[data-failing]');
		const got = await page.evaluate(() => {
			const rows = [...document.querySelectorAll('tr[data-verdict]')];
			const failing = rows.filter((row) => row.dataset.verdict === 'fail').length;
			const visible = rows.filter((row) => !row.hidden && !row.closest('details')?.hidden);
			return {
				failing,
				visible: visible.length,
				onlyFailing: visible.every((row) => row.dataset.verdict === 'fail'),
				empty: !document.querySelector('[data-empty]').hidden,
			};
		});
		expect(`${path}: "failing rows only" shows the failing rows and no other`, {
			visible: got.visible,
			onlyFailing: got.onlyFailing,
			emptyWhenNone: got.empty === (got.failing === 0),
		}, { visible: got.failing, onlyFailing: true, emptyWhenNone: true });
		await page.click('[data-failing]');
	}

	// Every verdict is still drawn: the row's mark, the legend's and each
	// section heading's. A heading's mark sits on a child of the <summary>,
	// never on the summary's own `::before`: Starlight draws the disclosure
	// chevron there with a mask, and a mark drawn on it is cut to the
	// chevron's shape and turns with it, so neither the chevron nor the mark
	// is left. Both are read off the computed style, which is all a reader
	// sees of them.
	{
		const got = await page.evaluate(() => {
			const before = (element) => (element ? getComputedStyle(element, '::before') : null);
			const image = (element) => before(element)?.backgroundImage ?? '';
			const mask = (element) => {
				const box = before(element);
				return box ? box.maskImage || box.webkitMaskImage || 'none' : '';
			};
			const row = document.querySelector('tr[data-verdict] > td:first-child');
			const legend = document.querySelector('.legend-entry[data-mark]');
			const summaries = [...document.querySelectorAll('details[data-domain-section] > summary')];
			const marks = summaries.map((summary) => summary.querySelector('[data-mark]'));
			const box = before(row);
			return {
				row: image(row).includes('data:image/svg+xml'),
				legend: image(legend).includes('data:image/svg+xml'),
				sized: !!box && parseFloat(box.width) > 8,
				sections: summaries.length > 0,
				chevrons: summaries.every((summary) => !summary.hasAttribute('data-mark') && mask(summary) !== 'none'),
				headingMarks: marks.every(
					(mark) => !!mark && mask(mark) === 'none' && image(mark).includes('data:image/svg+xml'),
				),
			};
		});
		expect(`${path}: the verdict marks are drawn beside the words, and each section keeps its chevron`, got, {
			row: true,
			legend: true,
			sized: true,
			sections: true,
			chevrons: true,
			headingMarks: true,
		});
	}

	await page.close();

	// A link to one row opens the section that holds it, even a section the
	// report starts closed because every check in it passes.
	{
		const target = await (async () => {
			const probe = await open(path);
			const id = await probe.evaluate(() => {
				const closed = [...document.querySelectorAll('details[data-domain-section]')].find(
					(section) => !section.open,
				);
				return closed?.querySelector('tr[data-verdict]')?.id ?? null;
			});
			await probe.close();
			return id;
		})();
		const page = await open(`${path}#${target}`);
		const got = await page.evaluate((id) => {
			const row = document.getElementById(id);
			const box = row?.getBoundingClientRect();
			return {
				found: !!row,
				open: !!row?.closest('details')?.open,
				onScreen: !!box && box.top >= 0 && box.bottom <= innerHeight,
			};
		}, target);
		expect(`${path}: a link to a row of a closed section opens it and shows the row`, got, {
			found: true,
			open: true,
			onScreen: true,
		});
		await page.close();
	}
}

// --- The errata registry -----------------------------------------------------

/** Where the browser ends up after opening `path`, once the router has run. */
async function landing(path) {
	const page = await open(path);
	await new Promise((resolve) => setTimeout(resolve, 300));
	const got = await page.evaluate(() => {
		const id = decodeURIComponent(location.hash.slice(1));
		return {
			path: location.pathname,
			hash: id,
			target: !!id && !!document.getElementById(id),
		};
	});
	await page.close();
	return got;
}

const MOVED = [
	// An entry of a standards family, by the anchor it had on the single page.
	{
		from: '/reference/errata/#iso-717-22020-annex-c-example-c1-ci-of-the-bare-floor',
		page: '/reference/errata/iso-717/',
		id: 'iso-717-22020-annex-c-example-c1-ci-of-the-bare-floor',
	},
	// An anchor computed from typeset mathematics, which only the build knows.
	{
		from: '/reference/errata/#iso-51362003-annex-d-annex-h-and-annex-i-c34-according-to-equation-3',
		page: '/reference/errata/iso-5136/',
		id: 'iso-51362003-annex-d-annex-h-and-annex-i-c34-according-to-equation-3',
	},
	// A book, and the properties that are not errata.
	{
		from: '/reference/errata/#related-source-properties-that-are-not-errata',
		page: '/reference/errata/not-errata/',
		id: 'related-source-properties-that-are-not-errata',
	},
	// A Spanish anchor with accents, percent-encoded as a browser sends it.
	{
		from: `/es/reference/errata/#${encodeURIComponent('osses-garcía--kohlrausch-2016-modelo-de-intensidad-de-fluctuación-ec-3')}`,
		page: '/es/reference/errata/osses-garcia-kohlrausch/',
		id: 'osses-garcía--kohlrausch-2016-modelo-de-intensidad-de-fluctuación-ec-3',
	},
];

for (const moved of MOVED) {
	expect(`errata: ${decodeURIComponent(moved.from)} lands on the entry's page`, await landing(moved.from), {
		path: `${BASE_PATH}${moved.page}`,
		hash: moved.id,
		target: true,
	});
}

for (const path of ['/reference/errata/', '/es/reference/errata/']) {
	// A section of the index itself stays on the index.
	const section = await (async () => {
		const page = await open(path);
		const id = await page.evaluate(() => document.querySelector('.sl-markdown-content h2[id]')?.id);
		await page.close();
		return id;
	})();
	expect(`errata: ${path}#${section} stays on the index`, await landing(`${path}#${section}`), {
		path: `${BASE_PATH}${path}`,
		hash: section,
		target: true,
	});
	// A fragment no entry has is left alone.
	expect(`errata: ${path}#no-such-entry stays on the index`, await landing(`${path}#no-such-entry`), {
		path: `${BASE_PATH}${path}`,
		hash: 'no-such-entry',
		target: false,
	});
}

// Every entry link on the index reads as the entry's heading, mathematics
// typeset. The heading's plain text is what is left of a formula once it is
// typeset: a radical, an exponent and every subscript drop out, and KaTeX's
// zero-width spaces (U+200B) stay behind. The hydraulic diameter of ISO 5136,
// D_h = √(S_f2/π), was listed as "Dh=Sf2/π" with three of them. So outside
// a formula a link carries no zero-width space, and it carries the same
// formulas, by their TeX, as the heading it points at on the family page.
for (const path of ['/reference/errata/', '/es/reference/errata/']) {
	const page = await open(path);
	const got = await page.evaluate(async () => {
		const ZWSP = '\u200b';
		const flat = (element) => {
			const copy = element.cloneNode(true);
			for (const formula of copy.querySelectorAll('.katex')) formula.remove();
			return copy.textContent ?? '';
		};
		const tex = (element) =>
			[...element.querySelectorAll('.katex')].map((formula) => formula.getAttribute('aria-label') ?? '');
		const links = [...document.querySelectorAll('[data-errata-family] ul a')];
		const pages = new Map();
		const problems = [];
		let formulas = 0;
		for (const link of links) {
			const url = new URL(link.href);
			const id = decodeURIComponent(url.hash.slice(1));
			if (flat(link).includes(ZWSP)) problems.push(`#${id}: zero-width space in "${flat(link)}"`);
			if (!pages.has(url.pathname)) {
				const html = await (await fetch(url.pathname)).text();
				pages.set(url.pathname, new DOMParser().parseFromString(html, 'text/html'));
			}
			const heading = pages.get(url.pathname).getElementById(id);
			if (!heading) {
				problems.push(`#${id}: no heading with that id on ${url.pathname}`);
				continue;
			}
			const want = tex(heading);
			formulas += want.length;
			if (JSON.stringify(tex(link)) !== JSON.stringify(want)) {
				problems.push(`#${id}: the link carries ${JSON.stringify(tex(link))}, the heading ${JSON.stringify(want)}`);
			}
		}
		return { links: links.length, formulas, problems };
	});
	await page.close();
	expect(
		`errata: ${path} lists every entry as its heading reads, mathematics typeset ` +
			`(${got.links} links, ${got.formulas} formulas)` +
			(got.problems.length ? `\n    ${got.problems.slice(0, 5).join('\n    ')}` : ''),
		{ some: got.links > 0, withMath: got.formulas > 0, problems: got.problems.length },
		{ some: true, withMath: true, problems: 0 },
	);
}

// --- The search panel ----------------------------------------------------------

/** A result's own title link, not the links of the sections listed under it. */
const TITLE_LINK = '.pagefind-ui__result-inner > .pagefind-ui__result-title > .pagefind-ui__result-link';

/**
 * Search from the panel, as a reader does, and read back every result as the
 * panel draws it: its link, its title and the metadata tags under it.
 */
async function searchPanel(path, query, wanted) {
	const page = await open(path);
	await page.click('site-search button[data-open-modal]');
	await page.waitForSelector('#starlight__search input', { visible: true });
	await page.type('#starlight__search input', query);
	// The panel lays out every result at once and fills each one in as its
	// data arrives, so the order can be read only once every page the check
	// compares has arrived. A page that never does is reported by the
	// expectation below rather than by a timeout here.
	await page
		.waitForFunction(
			(hrefs, titleLink) =>
				hrefs.every((href) =>
					[...document.querySelectorAll(`.pagefind-ui__result ${titleLink}`)].some(
						(link) => link.getAttribute('href')?.includes(href) && link.textContent.trim(),
					),
				),
			{ timeout: 60000 },
			wanted,
			TITLE_LINK,
		)
		.catch(() => {});
	const results = await page.evaluate((titleLink) =>
		[...document.querySelectorAll('.pagefind-ui__result')].map((result) => {
			const link = result.querySelector(titleLink);
			return {
				href: link?.getAttribute('href') ?? '',
				title: link?.textContent.trim() ?? '',
				tags: [...result.querySelectorAll('[data-pagefind-ui-meta]')].map((tag) =>
					tag.getAttribute('data-pagefind-ui-meta'),
				),
			};
		}),
		TITLE_LINK,
	);
	await page.close();
	return results;
}

for (const { path, query, guide, errata, title } of [
	{
		path: '/reference/errata/',
		query: 'VDI 2081 Blatt 2',
		guide: '/devices/noise-control/vdi2081-air-systems/',
		errata: '/reference/errata/vdi-2081/',
		title: 'Errata in VDI 2081',
	},
	{
		path: '/es/reference/errata/',
		query: 'VDI 2081 Blatt 2',
		guide: '/es/devices/noise-control/vdi2081-air-systems/',
		errata: '/es/reference/errata/vdi-2081/',
		title: 'Erratas de VDI 2081',
	},
]) {
	const results = await searchPanel(path, query, [errata, guide]);
	const at = (route) => results.findIndex((result) => result.href.includes(route));
	const page = results[at(errata)];
	expect(
		`search "${query}" (${path}): the errata page is listed under its own title, after the guide`,
		{
			title: page?.title,
			noTag: !page?.tags.includes('display_title'),
			guideFirst: at(guide) !== -1 && at(guide) < at(errata),
		},
		{ title, noTag: true, guideFirst: true },
	);
}

// --- The published catalogues ---------------------------------------------

/** Every catalogue page the sidebar lists; the build holds the list to the pages. */
const CATALOGUE_PAGES = catalogueSlugs.length;

/** What the finder offers and where it sits, read off a loaded page. */
const finderState = (page) =>
	page.evaluate(() => {
		const finder = document.querySelector('[data-finder]');
		const jump = document.querySelector('[data-finder-jump]');
		const select = finder?.querySelector('[data-category]');
		const options = [...(select?.options ?? [])];
		return {
			shown: !!finder && !finder.hidden && !!jump && !jump.hidden,
			pages: options.filter((option) => option.value).length,
			selected: select?.selectedOptions[0]?.textContent.trim() ?? '',
			// The button that opens the chosen page waits for a choice.
			open: finder?.querySelector('[data-open]')?.disabled === false ? 'offered' : 'waiting',
			aboveTable: finder?.nextElementSibling?.classList.contains('table-scroll') ?? false,
			aboveIndex: finder?.nextElementSibling?.hasAttribute('data-catalogue-index') ?? false,
			filters: !!finder?.querySelector('[data-search]'),
			jump: jump?.querySelector('button')?.textContent.trim() ?? '',
		};
	});

/**
 * Run `act` on the finder and report whether the tab stayed where it was:
 * the address after it (a navigation it started has had time to commit),
 * whether the choice moved off the option the page was built with, whether
 * the select kept the focus and whether the button now offers to open.
 * A tab that left is brought back, so the checks after it run on the page
 * they name, and unless `keep` is set the select goes back to the page's
 * own choice.
 */
async function stays(page, act, { keep = false } = {}) {
	const start = page.url();
	await act();
	await new Promise((resolve) => setTimeout(resolve, 1000));
	const url = page.url();
	if (url !== start) {
		await page.goto(start, { waitUntil: 'networkidle0', timeout: 90000 });
		return { url, moved: true, focused: false, open: 'left the page' };
	}
	const state = await page.evaluate(() => {
		const select = document.querySelector('[data-category]');
		return {
			moved: !select.selectedOptions[0]?.defaultSelected,
			focused: document.activeElement === select,
		};
	});
	const { open } = await finderState(page);
	if (!keep) {
		await page.evaluate(() => {
			const select = document.querySelector('[data-category]');
			select.value = [...select.options].find((option) => option.defaultSelected)?.value ?? '';
			select.dispatchEvent(new Event('change'));
		});
	}
	return { url, ...state, open };
}

/** Type `query` into the finder and report the rows left and what it says. */
async function filterRows(page, query) {
	await page.$eval('[data-search]', (input) => {
		input.value = '';
	});
	await page.type('[data-search]', query);
	return page.evaluate(() => {
		const rows = [...document.querySelectorAll('[data-catalogue] tbody tr')];
		const visible = rows.filter((row) => !row.hidden);
		return {
			total: rows.length,
			visible: visible.length,
			names: visible.map((row) => row.cells[0].textContent.trim()),
			count: document.querySelector('[data-count]')?.textContent.trim() ?? '',
			empty: document.querySelector('[data-empty-message]')?.textContent.trim() ?? '',
		};
	});
}

for (const { path, lang, label, steel, english, table, jump } of [
	{
		path: '/reference/catalogues/solids/',
		lang: 'en',
		label: 'Solids (260 rows)',
		steel: 'steel',
		english: null,
		table: 'Published table',
		jump: 'Go to the table',
	},
	{
		path: '/es/reference/catalogues/solids/',
		lang: 'es',
		label: 'Sólidos (260 filas)',
		steel: 'acero',
		english: 'aluminium',
		table: 'Tabla publicada',
		jump: 'Ir a la tabla',
	},
]) {
	const page = await open(path);

	expect(`${path}: the finder lists every catalogue, this one chosen, above the table`, await finderState(page), {
		shown: true,
		pages: CATALOGUE_PAGES,
		selected: label,
		open: 'waiting',
		aboveTable: true,
		aboveIndex: false,
		filters: true,
		jump,
	});

	// The controls speak the page's language.
	{
		const labels = await page.evaluate(() =>
			[...document.querySelectorAll('[data-finder] label > span')].map((span) => span.textContent.trim()),
		);
		expect(`${path}: the table filter is labelled in ${lang}`, labels.includes(table), true);
	}

	// A material finds its rows and only rows that name it.
	{
		const got = await filterRows(page, steel);
		expect(
			`${path}: "${steel}" narrows the table to rows that name it, and the count says how many`,
			{
				some: got.visible > 0,
				fewer: got.visible < got.total,
				count: got.count.startsWith(`${got.visible} `),
			},
			{ some: true, fewer: true, count: true },
		);
	}

	// The Spanish page still finds a row by the book's own English.
	if (english) {
		const got = await filterRows(page, english);
		expect(`${path}: "${english}", the book's word, still finds the row that reads in Spanish`, got.visible > 0, true);
	}

	// A filter that empties the table says so, in the page's language.
	{
		const got = await filterRows(page, 'zzzz-no-such-material');
		expect(`${path}: a filter that matches nothing says so`, {
			visible: got.visible,
			says: got.empty.length > 0,
			spanish: lang === 'es' ? got.empty.startsWith('Ninguna') : got.empty.startsWith('No row'),
		}, { visible: 0, says: true, spanish: true });
		await page.$eval('[data-search]', (input) => {
			input.value = '';
			input.dispatchEvent(new Event('input'));
		});
	}

	// The published table: one book's table, and only its rows.
	{
		const wanted = await page.$eval('[data-table] option:nth-child(2)', (option) => option.value);
		await page.select('[data-table]', wanted);
		const got = await page.evaluate(() => {
			const rows = [...document.querySelectorAll('[data-catalogue] tbody tr')].filter((row) => !row.hidden);
			return { some: rows.length > 0, tables: [...new Set(rows.map((row) => row.dataset.table))] };
		});
		expect(`${path}: choosing a published table shows its rows alone`, got, { some: true, tables: [wanted] });
		await page.select('[data-table]', '');
	}

	// A mark opens its explanation on a click, and a second click closes it.
	{
		// One handle for both clicks: an open mark lends its `title` to the
		// tooltip, so a selector on `[title]` would find the next mark instead.
		const mark = await page.$('[data-catalogue] td > [class^="cell-"][title]');
		const title = await mark.evaluate((element) => element.getAttribute('title'));
		await mark.evaluate((element) => element.scrollIntoView({ block: 'center' }));
		await mark.click();
		const open = await page.$eval('.catalogue-tip', (tip) => ({ shown: !tip.hidden, text: tip.textContent }));
		await mark.click();
		const closed = await page.$eval('.catalogue-tip', (tip) => tip.hidden);
		expect(`${path}: a mark opens its explanation on a click and closes on the next`, { ...open, closed }, {
			shown: true,
			text: title,
			closed: true,
		});
	}

	// The button at the top lands on the panel.
	{
		await page.evaluate(() => window.scrollTo(0, 0));
		await page.click('[data-jump]');
		await new Promise((resolve) => setTimeout(resolve, 1200));
		const top = await page.$eval('[data-finder]', (finder) => finder.getBoundingClientRect().top);
		expect(`${path}: the button at the top brings the panel into view`, top >= 0 && top < 400, true);
	}

	// On a phone each row is a card: a quantity reads its column's heading and
	// unit, and a cell the row does not have is left out.
	{
		await page.setViewport({ width: 390, height: 844 });
		const got = await page.evaluate(() => {
			const section = document.querySelector('[data-catalogue]');
			const headings = [...section.querySelectorAll('thead th')].map((th) => th.firstChild?.textContent.trim());
			const units = [...section.querySelectorAll('thead th')].map((th) => th.querySelector('.unit')?.textContent.trim() ?? '');
			const row = [...section.querySelectorAll('tbody tr')].find((tr) =>
				[...tr.cells].some((cell, at) => at > 0 && units[at] && cell.textContent.trim()),
			);
			const at = [...row.cells].findIndex((cell, index) => index > 0 && units[index] && cell.textContent.trim());
			const cell = row.cells[at];
			const unquote = (text) => text.replace(/^"|"$/g, '');
			const blank = [...row.cells].find((candidate) => candidate.tagName === 'TD' && candidate.childNodes.length === 0);
			return {
				label: unquote(getComputedStyle(cell, '::before').content) === headings[at],
				unit: unquote(getComputedStyle(cell, '::after').content) === ` ${units[at]}`,
				blankHidden: !blank || getComputedStyle(blank).display === 'none',
				card: getComputedStyle(row).display === 'block',
			};
		});
		expect(`${path}: on a phone a row is a card whose cells carry their column's heading and unit`, got, {
			label: true,
			unit: true,
			blankHidden: true,
			card: true,
		});
		await page.setViewport({ width: 1280, height: 900 });
	}

	// Walking the list from the keyboard stays on the page: an arrow or a
	// letter on the closed select changes the choice, and most browsers call
	// each step a change.
	for (const [key, how] of [['ArrowDown', 'an arrow'], [lang === 'es' ? 'm' : 'p', 'a letter']]) {
		const got = await stays(page, async () => {
			await page.focus('[data-category]');
			await page.keyboard.press(key);
		});
		expect(`${path}: ${how} on the catalogue select moves the choice and stays on the page, focus kept`, got, {
			url: page.url(),
			moved: true,
			focused: true,
			open: 'offered',
		});
	}

	// Choosing another catalogue opens its page at its table, once the button
	// beside the select is pressed and not before.
	{
		const target = await page.$eval('[data-category]', (select) =>
			[...select.options].find((option) => option.value.includes('/porous-materials/'))?.value,
		);
		const chosen = await stays(page, () => page.select('[data-category]', target), { keep: true });
		expect(`${path}: choosing the porous materials alone leaves the page where it is`, {
			url: chosen.url,
			moved: chosen.moved,
			open: chosen.open,
		}, { url: page.url(), moved: true, open: 'offered' });
		// Without a button to press there is nothing more to see here, and the
		// line above has already said so.
		if (chosen.open === 'offered') {
			await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), page.click('[data-open]')]);
			await new Promise((resolve) => setTimeout(resolve, 300));
			const got = await page.evaluate(() => {
				const finder = document.querySelector('[data-finder]');
				const top = finder.getBoundingClientRect().top;
				return { path: location.pathname, hash: location.hash, panelInView: top >= 0 && top < innerHeight / 2 };
			});
			expect(`${path}: the button opens the porous materials' page at the table`, got, {
				path: `${BASE_PATH}${lang === 'es' ? '/es' : ''}/reference/catalogues/porous-materials/`,
				hash: '#catalogue-porous',
				panelInView: true,
			});
			// Back on the page the choice was made on, the select names that
			// page and the button waits again.
			await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), page.goBack()]);
			const back = await finderState(page);
			expect(`${path}: back from that page, the finder names this catalogue again`, {
				selected: back.selected,
				open: back.open,
			}, { selected: label, open: 'waiting' });
		}
	}

	await page.close();
}

// A page with two tables filters both: the absorption coefficients carry the
// few rows the same books price in equivalent absorption area.
{
	const page = await open('/reference/catalogues/absorption-coefficients/');
	const got = await page.evaluate(() => ({
		sections: document.querySelectorAll('[data-catalogue]').length,
		aboveFirst: document.querySelector('[data-finder]')?.closest('[data-catalogue]')?.dataset.catalogue,
	}));
	const filtered = await filterRows(page, 'audience');
	const byTable = await page.evaluate(() =>
		[...document.querySelectorAll('[data-catalogue]')].map((section) => [...section.querySelectorAll('tbody tr')].filter((row) => !row.hidden).length),
	);
	expect('/reference/catalogues/absorption-coefficients/: one panel filters both tables', {
		sections: got.sections,
		aboveFirst: got.aboveFirst,
		some: filtered.visible > 0,
		areasKept: byTable[1] > 0,
	}, { sections: 2, aboveFirst: 'absorption', some: true, areasKept: true });
	await page.close();
}

// Every word a filter suggests finds a row of its own catalogue, on every
// catalogue page and in both languages. A suggestion that finds nothing tells
// the reader the filter is broken. Each word is typed into the finder and the
// rows it leaves are counted, so what is searched is what the browser
// searches: the cells a row shows, the key of its table and the words it
// carries in `data-also`, and not a list of the fields the generator writes.
// A page with two tables suggests the words of its first one; the second
// keeps its own, and they have to find its rows too.
for (const slug of catalogueSlugs) {
	for (const path of [`/${slug}/`, `/es/${slug}/`]) {
		const page = await open(path);
		const got = await page.evaluate(() => {
			const search = document.querySelector('[data-search]');
			const sections = [...document.querySelectorAll('[data-catalogue]')];
			if (!search || sections.length === 0) return { shown: false, lost: [] };
			const lost = [];
			let words = 0;
			for (const section of sections) {
				for (const word of (section.dataset.placeholder ?? '').split(', ').filter(Boolean)) {
					words += 1;
					search.value = word;
					search.dispatchEvent(new Event('input'));
					if (![...section.querySelectorAll('tbody tr')].some((row) => !row.hidden)) {
						lost.push(`${section.dataset.catalogue}: "${word}"`);
					}
				}
			}
			search.value = '';
			search.dispatchEvent(new Event('input'));
			return {
				shown: words > 0 && search.placeholder === sections[0].dataset.placeholder,
				lost,
			};
		});
		expect(`${path}: every word the filter suggests finds a row of its catalogue`, got, { shown: true, lost: [] });
		await page.close();
	}
}

// The overview: the finder chooses a catalogue and sits above the list that
// a reader without the script follows.
for (const { path, choose, jump } of [
	{ path: '/reference/catalogues/', choose: 'Choose a catalogue', jump: 'Go to the catalogues' },
	{ path: '/es/reference/catalogues/', choose: 'Elige un catálogo', jump: 'Ir a los catálogos' },
]) {
	const page = await open(path);
	const got = await finderState(page);
	const links = await page.$$eval('[data-catalogue-index] a', (anchors) => anchors.length);
	expect(`${path}: the finder offers every catalogue above the list of them`, { ...got, links }, {
		shown: true,
		pages: CATALOGUE_PAGES,
		selected: choose,
		open: 'waiting',
		aboveTable: false,
		aboveIndex: true,
		filters: false,
		jump,
		links: CATALOGUE_PAGES,
	});
	// An arrow off the line that asks for a choice picks the first catalogue
	// and stays here; the button then opens it.
	const arrow = await stays(
		page,
		async () => {
			await page.focus('[data-category]');
			await page.keyboard.press('ArrowDown');
		},
		{ keep: true },
	);
	expect(`${path}: an arrow on the catalogue select stays on the overview, focus kept`, arrow, {
		url: page.url(),
		moved: true,
		focused: true,
		open: 'offered',
	});
	if (arrow.open === 'offered') {
		await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), page.click('[data-open]')]);
		expect(`${path}: the button then opens the first catalogue at its table`, new URL(page.url()).pathname.endsWith('/reference/catalogues/solids/') && new URL(page.url()).hash, '#catalogue-solids');
	}
	await page.close();
}

// A link written against the old single page lands on the catalogue's page.
const CATALOGUE_MOVES = [
	// An English heading.
	{ from: '/reference/catalogues/#porous-materials', page: '/reference/catalogues/porous-materials/', hash: '' },
	// A Spanish heading with an accent, percent-encoded as a browser sends it.
	{
		from: `/es/reference/catalogues/#${encodeURIComponent('coeficientes-de-absorción')}`,
		page: '/es/reference/catalogues/absorption-coefficients/',
		hash: '',
	},
	// The plain-ASCII anchor the Spanish guides linked.
	{ from: '/es/reference/catalogues/#solidos', page: '/es/reference/catalogues/solids/', hash: '' },
	// A table's own id, which the table keeps on its page.
	{
		from: '/reference/catalogues/#catalogue-gases',
		page: '/reference/catalogues/gases/',
		hash: 'catalogue-gases',
	},
	// A table that shares its page with another.
	{
		from: '/reference/catalogues/#catalogue-absorptionAreas',
		page: '/reference/catalogues/absorption-coefficients/',
		hash: 'catalogue-absorptionAreas',
	},
];

for (const moved of CATALOGUE_MOVES) {
	const got = await landing(moved.from);
	expect(`catalogues: ${decodeURIComponent(moved.from)} lands on the catalogue's page`, {
		path: got.path,
		hash: got.hash,
	}, { path: `${BASE_PATH}${moved.page}`, hash: moved.hash });
}

for (const path of ['/reference/catalogues/', '/es/reference/catalogues/']) {
	// A section of the overview itself stays on the overview.
	const section = await (async () => {
		const page = await open(path);
		const id = await page.evaluate(() => [...document.querySelectorAll('.sl-markdown-content h2[id]')].at(-1)?.id);
		await page.close();
		return id;
	})();
	expect(`catalogues: ${path}#${section} stays on the overview`, await landing(`${path}#${section}`), {
		path: `${BASE_PATH}${path}`,
		hash: section,
		target: true,
	});
}

await browser.close();
console.log(`\n${failures()} failing check(s).`);
process.exit(failures() ? 1 : 0);
