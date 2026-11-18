/**
 * Landing-page content: the shape both locales share, and what they show
 * alike.
 *
 * The two locales share this single shape, so a block cannot exist in one
 * language and quietly go missing in the other. Each language's object lives
 * in a module of its own, home-en.ts and home-es.ts, which index.mdx and
 * es/index.mdx import and pass down to the components in
 * src/components/home/. A page is dated by the commits to the files it shows
 * (site/date-sources.json), and the two objects once shared this file: a
 * commit that changed only the Spanish text then dated the English landing
 * page as well, and gave it the notice of a page changed after the release.
 * This module keeps what both pages show alike, the DOI and the two code
 * examples, so a commit to it moves both.
 *
 * Every number in `stats` and every claim in `honest` is taken from the
 * repository, not written by hand from memory:
 *   checks/domains/designations/sources
 *       conformance-stats.mjs, read from the counts of docs/conformance.json
 *       at build time
 *   guides/apiPages/figures/fiches/version
 *       repo-stats.mjs, counted from the tree at build time (definitions in
 *       that module)
 *   the Python floor and the install line
 *       repo-stats.mjs, read from pyproject.toml, the table pip installs from
 *
 * All of these used to be typed out here by hand, and every hand-written copy
 * fell a release behind. They are imported now, so there is exactly one place
 * that can be wrong.
 */
export interface Stat {
	value: string;
	label: string;
	href?: string;
}

export interface Area {
	name: string;
	href: string;
	/**
	 * The designations implemented in the area. Empty where no standard
	 * governs it: the row then shows the locale's `coverage.noStandard`, and
	 * the structured data built from these rows states no standard for it,
	 * rather than publishing the placeholder as one.
	 */
	standards: string[];
	summary: string;
	/**
	 * The area as a search keyword, where its name is not one: "Files" says
	 * nothing about acoustics on its own. The name, in lower case, otherwise.
	 */
	keyword?: string;
}

export interface Step {
	title: string;
	body: string;
	code?: string;
	href: string;
	linkText: string;
	/**
	 * A second, subordinate destination for the same step. Optional while the
	 * Spanish strings are still to be written: a locale without it renders the
	 * step with one link, exactly as before.
	 */
	also?: { href: string; linkText: string };
}

export interface HomeContent {
	/** Accessible name for the numbers row, which has no visible heading. */
	statsLabel: string;
	stats: Stat[];
	what: { title: string; body: string[] };
	who: { title: string; items: string[] };
	honest: { title: string; items: string[] };
	proof: {
		title: string;
		lead: string;
		/**
		 * The banner clip that opens the block. Optional while the Spanish
		 * strings are still to be written: a locale without it simply renders
		 * the block without the clip.
		 */
		banner?: { title: string; description: string; caption: string };
		spectrum: { title: string; note: string; code: string; alt: string; caption: string };
		fiche: { title: string; note: string; code: string; caption: string; description: string; linkTitle: string };
	};
	coverage: {
		title: string;
		lead: string;
		areas: Area[];
		headers: [string, string];
		/** What the standards cell of an area says when no standard governs it. */
		noStandard: string;
	};
	start: { title: string; lead: string; steps: Step[] };
}

/**
 * The concept DOI of the Zenodo archive, the one that always resolves to the
 * latest release. Stated once here; `astro.config.mjs` and the About page
 * carry the same value in their own machine-readable and citation contexts.
 */
const DOI = '10.5281/zenodo.21215280';

// `octave_filter` is the one-shot function and returns an OctaveFilterResult;
// the "draws itself" claim is carried by the PSD estimate, whose
// SpectralDensityResult `.plot()` is the whole figure call. The snippet runs
// under scripts/check_doc_snippets.py, like every guide's.
const SPECTRUM_CODE = `import numpy as np
from phonometry import filters, signals

fs = 48_000
t = np.linspace(0, 1, fs, endpoint=False)
signal = np.sin(2 * np.pi * 100 * t) + np.sin(2 * np.pi * 1000 * t)

bands = filters.octave_filter(signal, fs=fs, fraction=3)

psd = signals.power_spectral_density(signal, fs=fs)
ax = psd.plot()          # the result draws itself`;

// The call that renders the committed fiche shown beside it
// (scripts/generate_reports.py), with the metadata block cut to the four
// fields the page discusses. Same inputs, same Rw (C; Ctr) = 31 (-1; -3) dB
// and the same PASS against the 30 dB requirement.
const FICHE_CODE = `import numpy as np
from phonometry import building, ReportMetadata

freqs = np.array([100, 125, 160, 200, 250, 315,
                  400, 500, 630, 800, 1000, 1250,
                  1600, 2000, 2500, 3150])

R = building.single_panel_transmission_loss(
    freqs, mass_per_area=15.0,
    critical_frequency=2000.0, loss_factor=0.02,
)

meta = ReportMetadata(
    specimen="6 mm float glass pane",
    laboratory="Phonometry reference example",
    report_id="EXAMPLE-717-1",
    requirement=30.0,  # adds the verdict row
)

R.report("Rw_fiche.pdf", metadata=meta)`;

export { DOI, FICHE_CODE, SPECTRUM_CODE };
