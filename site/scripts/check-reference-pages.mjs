// Behaviour checks for the two largest reference pages, which were slimmed
// and split so that a search engine reads all of them.
//
// The conformance report lost every byte a row did not need: the scoped
// class on each element, the lowercased copy of the row's text the search
// used to read, the class on each numeric cell and the SVG of each verdict
// mark. What has to survive that is behaviour, and only a browser can show
// it: the search still finds a row by the citation as the source writes it,
// the domain and failing filters still narrow the tables, a link to one row
// still opens the section that holds it, and the marks are still drawn.
//
// The errata registry became an index and one page per document family. A
// link written against the old single page, `/reference/errata/#<entry>`,
// has to land on the entry's new page, and a fragment the index holds itself
// has to stay where it is. And a family page is ranked in the site search by
// the register's name rather than its own title, which the search panel
// must still show (src/lib/search-ui.mjs): the index check in
// check-search-designation.mjs reads Pagefind directly and never sees the
// panel.
//
// Usage: node scripts/check-reference-pages.mjs [--base http://localhost:4321]
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

	// Every verdict is still drawn: the row's mark, and the legend's.
	{
		const got = await page.evaluate(() => {
			const image = (element) =>
				element ? getComputedStyle(element, '::before').backgroundImage : '';
			const row = document.querySelector('tr[data-verdict] > td:first-child');
			const legend = document.querySelector('.legend-entry[data-mark]');
			const box = row ? getComputedStyle(row, '::before') : null;
			return {
				row: image(row).includes('data:image/svg+xml'),
				legend: image(legend).includes('data:image/svg+xml'),
				sized: !!box && parseFloat(box.width) > 8,
			};
		});
		expect(`${path}: the verdict marks are drawn beside the words`, got, {
			row: true,
			legend: true,
			sized: true,
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
	await page.waitForFunction(
		(href, titleLink) =>
			[...document.querySelectorAll(`.pagefind-ui__result ${titleLink}`)].some(
				(link) => link.getAttribute('href')?.includes(href) && link.textContent.trim(),
			),
		{ timeout: 60000 },
		wanted,
		TITLE_LINK,
	);
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
	const results = await searchPanel(path, query, errata);
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

await browser.close();
console.log(`\n${failures()} failing check(s).`);
process.exit(failures() ? 1 : 0);
