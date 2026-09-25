# Virtual environment detection
VENV = .venv
BIN = $(VENV)/bin

# If venv doesn't exist, use system binaries
ifeq (,$(wildcard $(VENV)))
    PYTHON = python3
    RUFF = ruff
    MYPY = mypy
    BANDIT = bandit
    PNPM = pnpm
else
    PYTHON = $(BIN)/python3
    RUFF = $(BIN)/ruff
    MYPY = $(BIN)/mypy
    BANDIT = $(BIN)/bandit
    PNPM = pnpm
endif

# Deterministic figure rendering: pin numerical thread pools to one thread and
# fix the hash seed BEFORE the interpreter starts, so multi-threaded reductions
# and set ordering cannot perturb the committed SVG/PNG bytes across machines
# (this is what made the heavy compute figures flaky on CI). The scripts also
# set the thread vars internally; PYTHONHASHSEED can only be set from here.
FIGURE_ENV = OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
	NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
	PYTHONHASHSEED=0

# Where the generators write down what the Spanish tables could not translate,
# for `make figure-language` to read afterwards (see
# scripts/figure_language_audit.py). Recording only happens when this is set,
# it costs nothing measurable, and it cannot change a rendered byte; the
# directory is under build/, which is gitignored.
FIGURE_LANGUAGE_DIR = build/figure-language
FIGURE_LANGUAGE_ENV = PHONOMETRY_FIGURE_LANGUAGE_AUDIT=$(FIGURE_LANGUAGE_DIR)

# Where the generators write down which annotations cannot be read -- a curve
# drawn behind the letters, or something painted over them -- for `make
# figure-annotations` to read afterwards (see
# scripts/figure_annotation_audit.py). Recording only happens when this is
# set, because unlike the language one it costs renders: the light pass of
# each language is drawn a few more times, with pieces taken away, to count
# the pixels. It cannot change a rendered byte -- every artist it hides,
# unstrokes or lifts is put back before the figure is written, and the whole
# corpus regenerates byte for byte -- and the directory is under
# build/, which is gitignored.
FIGURE_ANNOTATION_DIR = build/figure-annotations
FIGURE_ANNOTATION_ENV = PHONOMETRY_FIGURE_ANNOTATION_AUDIT=$(FIGURE_ANNOTATION_DIR)

# Where the generators write down which tick labels run into each other --
# minor labels the scale writes beside major ticks set by hand, and any two
# labels of one axis that touch -- for `make figure-ticks` to read afterwards
# (see scripts/figure_tick_audit.py). One layout pass per language of each
# figure with nothing painted, and it cannot change a written byte; the
# directory is under build/, which is gitignored.
FIGURE_TICK_DIR = build/figure-ticks
FIGURE_TICK_ENV = PHONOMETRY_FIGURE_TICK_AUDIT=$(FIGURE_TICK_DIR)

# `[full]` rather than a bare `-e .`: a development environment wants every
# optional path importable, numba included, so `make test-perf` can exercise
# the jitted kernel here the way the tests-perf job does in CI. numba stays out
# of requirements-dev.txt on purpose: the main test matrix installs that file,
# and numba caps numpy (`<2.6` today), so declaring it there would hold the
# matrix back from the next numpy the day it ships, which is the one thing the
# perf job's separate environment exists to prevent.
install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -e ".[full]"

lint:
	$(RUFF) check .
	$(RUFF) format --check .
	$(MYPY) src scripts tests/static_typing

format:
	$(RUFF) check --fix .
	$(RUFF) format .

security:
	$(BANDIT) -r src

snyk:
	@echo "Running Snyk..."
	@if [ -f .env ]; then export $$(cat .env | xargs) && $(PNPM) exec snyk test --all-projects; else $(PNPM) exec snyk test --all-projects; fi

sonar:
	@echo "Running SonarQube Scanner..."
	@if [ -f .env ]; then export $$(cat .env | xargs) && $(PNPM) exec sonar-scanner; else $(PNPM) exec sonar-scanner; fi

graphs:
	# Clear the generated SVG/WebP first so a figure that is no longer produced
	# is actually removed (the generators only overwrite, never delete, so a
	# stale orphan would otherwise survive and slip past the staleness check).
	# Animations (*.gif/*.webm) come from the separate `animations` target and
	# are deliberately preserved.
	find .github/images -maxdepth 1 -type f \( -name '*.svg' -o -name '*.png' -o -name '*.webp' \) -delete
	# The language recording is per run, and the fragments accumulate: empty
	# the directory here so `make figure-language` cannot be answered by an
	# older, partial run.
	rm -rf $(FIGURE_LANGUAGE_DIR)
	# Same reasoning for the annotation measurement: it is per run, and a
	# leftover fragment would let `make figure-annotations` answer about a
	# figure this run never drew.
	rm -rf $(FIGURE_ANNOTATION_DIR)
	# And for the tick-label measurement.
	rm -rf $(FIGURE_TICK_DIR)
	$(FIGURE_ENV) $(FIGURE_LANGUAGE_ENV) $(FIGURE_ANNOTATION_ENV) $(FIGURE_TICK_ENV) $(PYTHON) scripts/generate_graphs.py
	$(FIGURE_ENV) $(FIGURE_LANGUAGE_ENV) $(PYTHON) scripts/generate_diagrams.py

# Every shaded region has to be visible against the page it is drawn on, on
# both themes; the staleness check cannot see that. Deliberately a target of
# its own rather than the tail of `graphs`: a contrast failure inside the
# generation step aborts it, and everything meant to run after generation
# (the staleness compare above all) is then skipped, so one illegible fill
# reads as "the figures could not be regenerated" instead of "this fill is
# invisible".
figure-contrast:
	$(PYTHON) scripts/check_figure_contrast.py

# A label mathtext cannot parse does not degrade into a worse label: generation
# raises and the figure is never written, which `check_figures` then reports as
# staleness -- sending the reader after a data change rather than a typo. This
# parses every `$...$` in the sources instead, in seconds, and covers labels no
# example exercises. It earns its place on a combination rather than a typo:
# `^{\prime}` is a good prime and `^{\prime}^{\prime}` is a double superscript
# matplotlib refuses, which is what a mechanical prime substitution makes of a
# double prime, and did make of three labels here.
mathtext:
	$(PYTHON) scripts/check_mathtext.py

# generate_api_docs copies the mathematics of a docstring to the site verbatim,
# and KaTeX reads what the docstring actually holds: `\\mathrm` is a line break
# with a `mathrm` after it, which it refuses, swallowing the rest of the block.
# The spelling is right in one kind of docstring and wrong in the other, so this
# reads the VALUE Python builds rather than the text of the file. The site's own
# check catches it after a full build; this costs a second.
docstring-math:
	$(PYTHON) scripts/check_docstring_math.py

# Every helper that takes a `language` defaults to English, so a call that does
# not pass the caller's on raises nothing and puts an English string or decimal
# point into the Spanish figure. On a log frequency axis nothing repairs it:
# localize_axes skips that axis because its labels are fixed strings by then.
# This reads the calls, following each helper through the imports, a result's
# .plot() through the class of its receiver, and a **kwargs through what it can
# carry. Static and dependency-free.
language-forwarding:
	$(PYTHON) scripts/check_language_forwarding.py

# Matplotlib aliases seven artist properties, and since 3.3 a call that receives
# both spellings of one is a TypeError. A renderer that defaults its own colour
# with kwargs.setdefault("color", ...) therefore refuses every caller who wrote
# c= instead. style_default() defaults a property only when neither spelling is
# there; this reads the tree and holds every renderer to it.
plot-style-defaults:
	$(PYTHON) scripts/check_plot_style_defaults.py

# ISO 80000-1 groups long numbers in threes, and the standards this library
# reads print them that way, so the corpus writes 6,251 5 and 101 325. Written
# with an ordinary space a line break can fall inside the number and leave half
# of it on the next line, reading as two numbers. This asks for U+202F, and it
# knows the two shapes that are not groupings at all: an array's printed output
# and a value followed by its unit.
digit-grouping:
	$(PYTHON) scripts/check_digit_grouping.py

# ISO 80000-2 sets a subscript by what it is, so a glyph pair can honestly take
# both slopes: the z of the ISO 9613-2 barrier screening is a path-length
# difference and the z of the ISO 2631-5 dose is a direction, and both
# documents print D_z. The decision therefore belongs to the file, which opens
# with the standard it implements -- and inside one file two slopes for one
# symbol is a page contradicting itself. That is what this reads. It needs no
# dependencies and no generation run.
subscripts:
	$(PYTHON) scripts/check_subscript_slope.py

# The blind spot of the Spanish pass, and the reason it needs a check of its
# own. That pass ends with the decimal comma, guarded by `"$" not in s` because
# a bare comma inside `$...$` sets with maths spacing -- but the guard tests the
# WHOLE string, so a label carrying mathematics anywhere keeps an English point
# everywhere. No other gate can see it: the language gate compares untranslated
# WORDS, and a number is not a word. This reads the translation tables and fails
# on a Spanish value that still has a point the pass will never reach.
decimal-comma:
	$(PYTHON) scripts/check_decimal_comma.py

# The words of the Spanish tables, read for the marks a keyboard without the
# Spanish layout drops. Twenty-nine entries shipped as "Correccion", "medicion"
# and "aqui", and every other gate was green: the language gate saw translated
# strings and the figures matched their generator. This fails on a Spanish
# value carrying a form that is never correct without its accent or eñe, in the
# tables and in the example fiches whose builders ask for Spanish.
spanish-accents:
	$(PYTHON) scripts/check_spanish_accents.py

# The same defect read from the other end: not the labels a pass might miss but
# the ones it did miss, in the figures as committed. Three machines write the
# Spanish decimal comma (the library's localize_axes, format_frequency_axis
# where a caller hands it the language, and the save-time pass), and a panel
# none of them reached -- a zoom inset, a contour colorbar, the z of a 3-D
# array, a log axis of distances -- shipped `31.5` beside `52,4` with every
# gate green. This reads the committed SVGs, where matplotlib records the text
# it drew, and fails on a label that is a number with a point in it.
figure-decimal-point:
	$(PYTHON) scripts/check_figure_decimal_point.py

# A legend is an opaque plate placed by hand and sized by its longest label,
# which is a defect waiting to happen in a bilingual corpus: the Spanish label
# is routinely half again as long, so a box that clears the data in one
# language reaches back over it in the other, and the drawing passes every
# other gate while the reader loses a reading. This reads the committed SVGs
# for a plotted point under a legend frame, so it costs seconds and needs no
# `make graphs` first. Stdlib only.
figure-legends:
	$(PYTHON) scripts/check_figure_legends.py

# The other thing a legend can land on is a tick label, and a curve can too:
# the radial labels of a polar plot sit inside it on one ray, and an inset
# writes its labels over the data of the panel it sits in. The tick audit
# measures the labels of one axis against each other and the annotation audit
# measures the labels a generator places, so neither sees it. This reads the
# committed SVGs for a legend, a stroke or a marker over any tick label, with
# the clip each one is drawn through, and needs no `make graphs` first.
# Stdlib only.
figure-tick-clearance:
	$(PYTHON) scripts/check_figure_tick_clearance.py

# A label placed by hand can land on a tick label, on another label, or under
# a curve, a guide line or the spine a note runs out through, and the tick
# gate measures marks over a tick label but not a text, while the annotation
# audit leaves the plates out. This reads the committed SVGs, figures and
# plates alike, glyph by glyph, so a label turned on a 3-D plate is read along
# its own baseline, and fails on a text drawn over another or a stroke run
# across one; the leader of an annotation, the grid and a line behind a chip
# pass. Needs no `make graphs` first. Stdlib only.
figure-text-clearance:
	$(PYTHON) scripts/check_figure_text_clearance.py

# The corpus signs a negative number with U+2212, and three things still wrote
# the hyphen-minus: the polar angle formatter, which ignores
# axes.unicode_minus; a reading built with an f-string; and the plates, which
# set the characters they are given. This reads the string every committed
# SVG records beside its outlines, all four variants, and fails on a hyphen
# in front of a number that is not a designation, a range or an exponent.
# Stdlib only.
figure-minus-sign:
	$(PYTHON) scripts/check_figure_minus_sign.py

# The Python fences of a documentation page form one sequential example, and
# one shipped page used names its own figure block defined further down --
# while a same-named variable from a different room sat in scope, so reading
# top to bottom produced numbers that were not the annotated ones. This reads
# every page's fences in order and fails on a name no earlier fence defined,
# unless the page registers it as a reader-owned placeholder. Stdlib only.
fence-names:
	$(PYTHON) scripts/check_fence_names.py

# A private constant nothing reads is either a leftover or the trace of a check
# that was planned and never written; the sweep that added this found one of
# each. Stdlib only.
dead-constants:
	$(PYTHON) scripts/check_dead_constants.py

# Every level is a ratio to an ISO 1683 reference value, and the package
# publishes them once, in phonometry.metrology.ISO1683_REFERENCE_VALUES. This
# fails on a reference value in src that is typed out again instead of read
# from the table, and on one that differs from it without naming the document
# it comes from. On the tree it was written against it found forty-three.
# Stdlib only.
reference-values:
	$(PYTHON) scripts/check_reference_values.py

# A pressure of 101 325 and a pressure of 101.325 are both legitimate values
# in this tree, so a bare `pressure` loses its unit the moment a caller types
# a number. This holds every public pressure, temperature and humidity to a
# name that ends in its unit, or in a suffix that says it carries none. Needs
# the package importable: the surface it checks is the one a caller reaches.
parameter-units:
	$(PYTHON) scripts/check_parameter_units.py

# A published table is shared by the whole process, and a dict behind a
# `Mapping` annotation or a writeable array lets one caller change a printed
# number for every caller after it. This holds every value reachable from a
# public name to immutable containers all the way down. Needs the package
# importable, for the same reason parameter-units does.
frozen-constants:
	$(PYTHON) scripts/check_frozen_constants.py

# A number transcribed from a book is only checkable if the next reader can
# open the same page, and nothing used to require that a published value say
# which one. This holds every record carrying a `source` to the grammar the
# errata registry uses, and every table transcribed from a book or a paper to a
# banner that names both its PDF page and its printed folio. Needs the package
# importable, for the same reason parameter-units does.
published-sources:
	$(PYTHON) scripts/check_published_sources.py

# A catalogue nobody can see is a catalogue nobody has. Every PUBLISHED_*
# mapping the package exposes has to reach /reference/catalogues/, which is the
# only place a reader who is not reading Python meets these rows at all. When
# this was first run it found six, two of them years old. Needs the package
# importable, like the two guards above it.
published-catalogues:
	$(PYTHON) scripts/check_published_catalogues_reach_the_page.py

# The solids catalogue holds the same material from up to four books, and two
# densities that disagree are a digit somebody typed wrong: every density the
# script does not already accept agrees across these tables to within 2,6 per
# cent. It puts the books side by side and fails above 8 per cent, so a real
# spread passes without a word, while reporting the moduli and speeds, which do
# disagree by thirty per cent without anybody being wrong. Needs the package
# importable, for the same reason published-sources does.
solid-agreement:
	$(PYTHON) scripts/check_solid_agreement.py

# The other half of the same idea, over every catalogue rather than the solids
# alone: where two books print one material and credit one study for it, they
# are two readings of one measurement and cannot exclude each other. Agreement
# is an overlap and not an equality, because a book that prints an interval and
# a book that prints a value inside it are saying the same thing at two
# resolutions. Needs the package importable.
shared-sources:
	$(PYTHON) scripts/check_shared_sources.py

# A conformance row that computes the expected value itself is comparing a
# formula with a second copy of it, and reports Pass whatever the library does.
# This resolves what each row reaches, through its helpers and whatever name
# the module's imports gave the library, and fails on one that reaches nothing
# and does not say why in ORACLE_ONLY. Stdlib only.
conformance-rows:
	$(PYTHON) scripts/check_conformance_rows.py

# The artefact's closed vocabularies (verdict, comparison shape, tolerance
# mode, document kind, relation) are stated three times: the Python enums that
# produce them, the Zod schema that validates the artefact into the site, and
# the label maps that word two of them in English and Spanish. A value added to
# the first and missing from the second stops the site build on every row that
# carries it; missing from the third it prints untranslated. This compares the
# three, both ways, so a vocabulary that grows or shrinks moves everywhere at
# once. Stdlib only.
conformance-vocabulary:
	$(PYTHON) scripts/check_conformance_vocabulary.py

# The Spanish variant of a figure is the English one with its strings looked
# up in a table at save time, so a string nobody added to the table ships in
# English inside `X_es.svg` and every other gate stays green: the page is
# Spanish, the figure in it is not. This reads what the generation run above
# wrote down and fails on any untranslated string the committed baseline does
# not already record -- and on a baseline line that is no longer true. Needs a
# `make graphs` first; it is answering about that run, not about the tree.
figure-language:
	$(PYTHON) scripts/check_figure_language.py --audit $(FIGURE_LANGUAGE_DIR)

# A label drawn across a curve with nothing behind it is hard to read, and a
# label something is painted over cannot be read at all. No other gate can see
# either: the figure matches its generator, its colours pass the contrast
# checks, and `svg.fonttype = "path"` means the committed file has no text node
# to look for the label in. The generation run above counts, for every label of
# both language editions, how many of its glyph pixels a stroke paints under
# them and how many never reach the page; this fails on any at or above the
# calibrated threshold and prints the band below it for a person to judge.
# Needs a `make graphs` first; it is answering about that run, not about the
# tree.
figure-annotations:
	$(PYTHON) scripts/check_figure_annotations.py --audit $(FIGURE_ANNOTATION_DIR)

# A band axis set by hand on a logarithmic scale keeps matplotlib's own minor
# labels between the bands unless the minor formatter is cleared, and an axis
# that should read "125 250 500" reads "2 × 10²50 4 × 10²500". Nothing else
# sees it: the figure matches its generator, the annotation audit measures the
# labels a generator places and not the ones an axis draws, and the committed
# file has no text node to find a tick in. The generation run above measures
# every axis of both language editions; this fails on minor labels left to
# the scale beside major ticks set by hand, and on any two labels of one axis
# that touch. Needs a `make graphs` first; it is answering about that run, not
# about the tree.
figure-ticks:
	$(PYTHON) scripts/check_figure_ticks.py --audit $(FIGURE_TICK_DIR)

# What to run locally before committing a figure change: regenerate, then
# verify legibility and staleness the way CI does, each as its own step.
# Recipe lines rather than prerequisites: prerequisites are free to run
# concurrently under `make -j`, which would let the contrast checker parse the
# SVGs while the generators are still deleting and rewriting them.
figures:
	# First, because it reads the sources and costs seconds: a label that
	# cannot parse aborts the generation below, and finding that out from the
	# traceback of a four-hundred-figure run is the slow way round.
	$(MAKE) mathtext
	$(MAKE) decimal-comma
	$(MAKE) graphs
	$(MAKE) figure-contrast
	$(MAKE) figure-language
	$(MAKE) figure-annotations
	$(MAKE) figure-ticks
	$(MAKE) figure-decimal-point
	$(MAKE) figure-legends
	$(MAKE) figure-tick-clearance
	$(MAKE) figure-text-clearance
	$(MAKE) figure-minus-sign
	$(PYTHON) scripts/check_figures.py

# Regenerate the Tier-1 documentation animations (WebM for the site, GIF for
# the GitHub docs). Kept out of `graphs`/CI because the ffmpeg encoding is slow
# and video is not byte-reproducible across platforms; run manually to refresh.
# The clips are binary and re-encoded whole whenever the code drawing one
# changes, and kept in this repository they made a clone of the code download
# gigabytes of old video. They live in jmrplens/phonometry-assets instead, in
# a checkout beside this one (or wherever PHONOMETRY_ASSETS_DIR in .env says),
# which this clones or fast-forwards. scripts/assets_dir.py is the one place
# that knows the path.
assets:
	$(PYTHON) -c "import sys; sys.path.insert(0, 'scripts'); import assets_dir; print(assets_dir.checkout_root(assets_dir.clips_dir()))" > .assets-checkout
	@dir=$$(cat .assets-checkout); rm -f .assets-checkout; \
	if [ -d "$$dir/.git" ]; then git -C "$$dir" pull -q --ff-only origin main && echo "$$dir is up to date"; \
	else git clone -q git@github.com:jmrplens/phonometry-assets.git "$$dir" && echo "cloned into $$dir"; fi

# Renders into the assets checkout (see `assets`) and then publishes what it
# rendered: commits and pushes there, and writes the resulting commit into
# assets.lock here, so the code and the clips say which version goes with
# which. Still records language fragments into the same directory as `make
# graphs`, so `make figure-language` afterwards sees figures, plates and
# clips at once. PUBLISH=no renders without pushing, for a look.
animations: assets
	$(FIGURE_LANGUAGE_ENV) $(PYTHON) scripts/generate_graphs.py --animations
	@if [ "$(PUBLISH)" != "no" ]; then $(PYTHON) scripts/publish_assets.py; fi

# The clips are never regenerated in CI, so nothing else can tell that the
# code drawing one has moved since the clip was published -- which is how
# twelve of them kept an ASCII hyphen in their Spanish tick labels for months
# after that was repaired. Each render stamps a fingerprint of the code that
# drew the clip; this recomputes them from the sources (no rendering, a couple
# of seconds) and names every clip whose fingerprint has moved. Locally it
# looks in the assets checkout for the files; CI hands it a manifest instead.
animation-freshness:
	$(PYTHON) scripts/check_animation_freshness.py

# Re-extract only the deferred-loading poster stills (anim_*_poster.webp) from
# the published animation WebMs, without the slow clip re-encode, and publish
# them the same way `animations` does. Posters are lossy WebP at the quality
# scripts/figures/media.py fixes, and live with the clips, outside the figure
# pipeline (`graphs` deletion and the check_figures.py staleness compare).
posters: assets
	$(PYTHON) scripts/generate_graphs.py --posters
	@if [ "$(PUBLISH)" != "no" ]; then $(PYTHON) scripts/publish_assets.py; fi

# Regenerate the brand mark and every icon derived from it (.github/brand and
# the site's favicon, touch icon and PWA icons). Deliberately outside `graphs`:
# that target wipes .github/images first, and these are design assets rather
# than computed figures, so they are refreshed only when the mark changes.
brand:
	$(PYTHON) scripts/generate_brand.py

llms:
	$(PYTHON) scripts/mirror_overviews.py
	$(PYTHON) scripts/mirror_glossary.py
	$(PYTHON) scripts/generate_llms.py

# Regenerate README_PYPI.md (the PyPI long description) from README.md:
# theme-aware <picture> elements collapse to their light <img> fallback and
# animated GIFs to poster stills, because PyPI strips <picture>/<source>.
# The packaging tests fail if the committed file drifts.
pypi-readme:
	$(PYTHON) scripts/generate_pypi_readme.py

# Run every Python snippet the guides print, hold the two languages to the
# same API and reject a block that shadows a name it imported (see the
# doc-snippets job in python-app.yml). `make snippets-static` skips the
# execution pass, which is the slow half.
snippets:
	$(PYTHON) scripts/check_doc_snippets.py

snippets-static:
	$(PYTHON) scripts/check_doc_snippets.py --static

# Catch a paragraph that wraps onto a "-" or a ">", which CommonMark reads as a
# new block and which then either takes the site build down or publishes a
# quoted block in the middle of a sentence (see the markdown-wrapping job).
hazards:
	$(PYTHON) scripts/check_markdown_hazards.py

# Catch a C0 control character in a text file. A form feed in a raw docstring
# is what \frac looks like once the backslash and the f have been eaten, and
# the published formula then loses its fraction with nothing reporting it.
control-characters:
	$(PYTHON) scripts/check_control_characters.py

# Every "we cover X" / "we do not cover Y" the guides declare, one line each,
# read off the <Scope>/<ScopeClaim> markup. Not a gate: it is the list an audit
# holds against the library, and its not-covered half is a backlog with the
# reasoning already attached. Add `--html site/dist` after a build to read the
# rendered pages instead, which also checks the components emitted what the
# pages asked for.
claims:
	$(PYTHON) scripts/list_coverage_claims.py

# Regenerate the committed Starlight API reference (site/src/content/docs/
# reference/api + site/src/generated/api-sidebar.mjs) from the source
# docstrings. CI fails if this drifts (see the api-docs job in python-app.yml).
api-docs:
	$(PYTHON) scripts/generate_api_docs.py

# Transplant the bodies of docs/CONFORMANCE.md and docs/ERRATA.md into their
# Starlight pages (site/src/content/docs/{,es/}reference/{conformance,errata}.md),
# below the hand-written introduction each page keeps. CI fails if this drifts
# (see the `site-reports` job in python-app.yml).
site-reports:
	$(PYTHON) scripts/generate_site_reports.py

# Dump the published catalogues (solids, porous materials, fluids) into the
# module the site imports at build time. The rows live in the package and the
# loader adds what follows from them, so the page shows what the library holds
# rather than a second reading of the same books. CI runs the --check form and
# fails if the committed module drifts (see the `catalogue-data` step of the
# quality job in python-app.yml).
catalogue-data:
	$(PYTHON) scripts/generate_catalogue_data.py

# Write the JSON Schema of a catalogue file (every published row class) into
# site/public/schemas/, where the site serves it for an editor to complete a
# catalogue file with. CI runs the --check form and fails if the committed
# file drifts from a fresh run (see the `published-sources` job).
catalogue-schema:
	$(PYTHON) scripts/generate_catalogue_schema.py

# Lighthouse over a fixed sample of built pages, against a local preview
# server (BASE_URL overrides for the live site; `-- --desktop` for desktop
# throttling). Needs `pnpm build` in site/ first; summary on stdout, JSON
# reports in site/lighthouse-results/ (gitignored).
lighthouse:
	cd site && pnpm run lighthouse

# Regenerate the committed example .report() fiches under .github/reports/,
# which the documentation links to as rendered normative-report examples. CI
# fails if this drifts (see the `reports` job in python-app.yml). The compare
# is tolerance-aware rather than a byte diff, for the same reason the figures'
# is: the embedded vector plot differs by ~1 ULP across CPUs. See
# scripts/check_reports.py.
#
# Renders into a scratch directory and swaps it in only once the whole set is
# written. Clearing the output first, which is how this used to work, means a
# generator that dies halfway leaves the working tree stripped of the committed
# examples and the maintainer reaching for `git checkout`. The clearing itself
# has to stay, because the generator only overwrites and never deletes, so a
# fiche that is no longer produced would survive as a stale orphan and slip
# past the staleness check; it just belongs after a successful run rather than
# before an attempted one. The trap covers the interrupted run the same way.
reports:
	set -e; \
	tmp=$$(mktemp -d .github/reports.tmp.XXXXXX); \
	old=$$(mktemp -d .github/reports.old.XXXXXX); \
	trap 'if [ -d "$$old"/current ]; then rm -rf .github/reports; mv "$$old"/current .github/reports; fi; rm -rf "$$tmp" "$$old"' EXIT INT TERM HUP; \
	$(FIGURE_ENV) $(PYTHON) scripts/generate_reports.py --output-dir "$$tmp"; \
	[ -n "$$(ls -A "$$tmp")" ] || { echo "no fiche was generated" >&2; exit 1; }; \
	mv .github/reports "$$old"/current; \
	mv "$$tmp" .github/reports; \
	mv "$$old"/current "$$old"/replaced; \
	rm -rf "$$old"

# Regenerate the committed numerical conformance evidence, then bring every
# count quoted from it into line. The chain is: the checks write
# docs/conformance.json, docs/CONFORMANCE.md is rendered from that document, and
# the counts quoted in prose are read from it too.
#
# The artefact is rewritten only when a fresh run differs from it by more than
# the numeric tolerance, so a value that wobbles in its last digit across BLAS
# builds leaves the committed bytes alone - which is what lets the Markdown keep
# a byte diff, being a pure function of bytes that are themselves committed.
#
# The --file-header flag prepends the "do not hand-edit" note. The badges step
# redraws the verdict marks and the summary banner under .github/badges from the
# same artefact, so the count on the banner is always the tree's own; it is
# deliberately not under `graphs`, which empties .github/images of SVGs before
# every figure run. The claims step rewrites the counts in the prose that has no
# build step to interpolate them through (.zenodo.json, the plain-markdown
# mirror under docs/, the site frontmatter); the Astro page bodies import them
# from site/src/data/conformance-stats.mjs and need nothing. The last two steps
# are the read-only validations CI also runs: the artefact against itself, and
# its vocabularies against the site that has to accept and word them. CI fails
# if any output drifts (see the `conformance` job in python-app.yml).
conformance:
	$(PYTHON) scripts/conformance_report.py --file-header > docs/CONFORMANCE.md
	$(PYTHON) scripts/conformance_badges.py
	$(PYTHON) scripts/check_conformance_claims.py --write
	$(PYTHON) scripts/check_conformance_artifact.py
	$(PYTHON) scripts/check_conformance_vocabulary.py

# Optional convenience: install a git pre-commit hook that regenerates
# docs/CONFORMANCE.md when the library source or the report generator changes.
# The CI staleness check is the enforcement; this only saves a round-trip.
install-hooks:
	@mkdir -p .git/hooks
	@cp hooks/pre-commit .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Installed .git/hooks/pre-commit (regenerates docs/CONFORMANCE.md when src/scripts change)."

# Pin every numerical thread pool to one thread so the pytest-xdist workers
# (one per core) do not each spawn a nested BLAS/OpenMP pool and oversubscribe
# the CPU. With one worker per core already saturating the machine, nested
# threads only add contention: measured ~25% faster wall-clock and ~40% less
# total CPU on this suite. (PYTHONHASHSEED is deliberately left unset here so
# the tests still exercise randomised hash/set ordering.)
TEST_ENV = OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
	NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMBA_NUM_THREADS=1

# -n auto fans the suite out across all CPU cores via pytest-xdist (workers are
# separate processes; pytest-cov combines their coverage data automatically).
test:
	$(TEST_ENV) $(PYTHON) -m pytest -n auto tests/

coverage:
	$(TEST_ENV) $(PYTHON) -m pytest -n auto --cov=src/phonometry --cov-report=term-missing tests/

# The jitted kernel, which the plain `test` target never reaches: conftest.py
# disables the JIT by default so coverage can trace inside the kernels, and
# `NUMBA_DISABLE_JIT=0` is what the tests-perf job in CI sets to exercise the
# compiled path. This target is that job, run here. It needs the optional
# extra: `pip install numba` (deliberately outside requirements-dev, since
# numba caps numpy and the main matrix must stay free to move ahead of it).
test-perf:
	$(TEST_ENV) NUMBA_DISABLE_JIT=0 $(PYTHON) -m pytest -n auto tests/

# The FDTD GPU parity, which needs a CUDA device. There is one either way: a
# local CuPy install, or the machine named by PHONO_GPU_HOST in .env, which is
# where the animation renders already run. With neither, every GPU case skips
# and says which of the two is missing.
test-gpu:
	$(TEST_ENV) $(PYTHON) -m pytest -rs tests/test_fdtd_gpu_parity.py

check: lint security test

.PHONY: install lint format security snyk sonar graphs figure-contrast figure-language \
	figure-annotations figure-ticks figures reports \
	assets animations animation-freshness posters brand lighthouse \
	llms pypi-readme api-docs site-reports conformance install-hooks test test-perf test-gpu coverage check \
	snippets snippets-static claims subscripts docstring-math language-forwarding \
	fence-names decimal-comma spanish-accents figure-decimal-point figure-legends figure-tick-clearance \
	figure-text-clearance figure-minus-sign control-characters hazards dead-constants reference-values \
	conformance-rows conformance-vocabulary parameter-units frozen-constants published-sources \
	solid-agreement shared-sources catalogue-data catalogue-schema published-catalogues
