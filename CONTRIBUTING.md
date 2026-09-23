# Contributing to phonometry

Thank you for your interest in contributing to phonometry! We welcome contributions from the community to help improve this project.

## 💬 Where to Ask

Not every contribution starts with code. [Discussions](https://github.com/jmrplens/phonometry/discussions)
is the right place for anything that is not yet a defect or a pull request:

| You want to | Go to |
|---|---|
| Ask how to compute or measure something with the library | [Q&A](https://github.com/jmrplens/phonometry/discussions/categories/q-a) |
| Ask whether a clause or edition is implemented, report a value that disagrees with the standard or with a reference implementation, or flag a defect in a published standard | [Standards & conformance](https://github.com/jmrplens/phonometry/discussions/categories/standards-conformance) |
| Propose a standard, method or feature | [Ideas](https://github.com/jmrplens/phonometry/discussions/categories/ideas) |
| Give feedback on the guides, figures or animations | [Documentation & learning](https://github.com/jmrplens/phonometry/discussions/categories/documentation-learning) |
| Share a measurement, study or tool you built | [Show and tell](https://github.com/jmrplens/phonometry/discussions/categories/show-and-tell) |
| Report a reproducible failure with no standard in play, or work on an agreed change | [Issues](https://github.com/jmrplens/phonometry/issues) |
| Report a suspected security vulnerability | Privately, following the [security policy](SECURITY.md) |

A discrepancy against a standard or a reference implementation belongs in
Standards & conformance even when it reproduces every time, because settling it
means reading the clause first. Issues is for crashes, results that contradict
the library's own documentation, and broken installations.

The documentation is published in English and Spanish, and both languages are
welcome in Discussions.

Two conventions worth knowing before posting about a standard:

- Cite clauses, tables and equations by number rather than pasting substantial
  verbatim text. Standards are copyrighted.
- A proposal moves faster when it names reference data the implementation can be
  validated against. Methods here are implemented from the standard and checked
  against reference values, never from a textbook summary alone.

Participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md).

## 🛠️ Development Setup

To set up your development environment:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jmrplens/phonometry.git
   cd phonometry
   ```

   The documentation figures under `.github/images/` are in the tree and you
   will not need them to work on the code; a partial clone leaves them out
   (see [Cloning without the figures](#cloning-without-the-figures) below).

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   Install both production and development dependencies to run tests and linters.
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## ✅ Code Quality Standards

We enforce strict code quality standards. Before submitting a Pull Request, please ensure your code passes the following checks:

### 1. Type Checking (MyPy)
We use strict type checking. Ensure no errors are reported:
```bash
mypy .
```

### 2. Linting & Formatting (Ruff)
We use `ruff` for fast linting and formatting.
```bash
ruff check .
```

### 3. Testing (Pytest)
Run the full test suite to ensure no regressions. We aim for 100% code coverage.
```bash
pytest tests/
```
To check coverage locally:
```bash
pytest --cov=src/phonometry --cov-report=term-missing tests/
```

### 3b. Oracle data (committed vs local)

Some suites are validated against reference material that is too large or not
redistributable. Each of them keeps a small committed oracle under
`tests/data/<dataset>/` (a derived measurement series, or a lossless extract of
a representative subset) and prefers a full local copy when one is available.
Resolution order, applied by `tests/oracle_data.py`: the dataset's environment
variable, then the gitignored `tests/data-local/<dataset>/`, then the committed
data. **The assertions on the committed data never skip**: that is what CI
runs. Tests that exist only to exercise the full set, and have no committed
counterpart, do skip there and say so. `pytest` prints which copy each dataset
resolved to in its run header.

To run a suite against the full original set, drop it in `tests/data-local/`:

| Dataset | `tests/data-local/…` | Environment override |
| :--- | :--- | :--- |
| [stipa.info STIPA verification bench](https://www.stipa.info/index.php/download-test-signals) | `stipa-verification/` | `STIPA_VERIFICATION_DATA` |
| [EBU loudness test set](https://tech.ebu.ch/publications/ebu_loudness_test_set) | `ebu-loudness-test-set/` | `EBU_LOUDNESS_TEST_SET` |
| NORAH2 V2.0.74 public release | `norah2/NORAH2_V2.0.74_public.zip` | `NORAH2_DATA` (extraction root) |

See `tests/data/README.md` for the convention and what each committed oracle
can and cannot assert.

### 4. Documentation media (auto-generated)

Every figure, diagram, animation and report preview in the documentation is
generated with the library itself, never hand-made. There are two pipelines,
and they end in two different places. What separates them is whether CI can
regenerate the output on a pull request: the figures, yes; the clips, no,
because a clip is an FDTD run plus four video encodes, minutes of GPU each,
and the encoders are not bit-reproducible across machines anyway.

| What | Made by | Lives in | Checked by CI |
| --- | --- | --- | --- |
| Figures: SVG, and lossless WebP for the few rasters an SVG would bloat | `make graphs` | `.github/images`, this repository | `check_figures.py` regenerates every one and compares within tolerance |
| Animation clips: WebM in four language and theme variants, plus two GIF editions for GitHub | `make animations` | `images/` of [phonometry-assets](https://github.com/jmrplens/phonometry-assets) | `check_animation_freshness.py`: every file present at the locked commit, fingerprint of the drawing code unchanged |
| Poster stills: one lossy WebP per clip variant | `make posters`, and `make animations` on the way | with the clips | with the clips |
| Example `.report()` fiches: PDF and WebP preview | `make reports` | `.github/reports`, this repository | `check_reports.py` |

The clips live apart because they are binary and re-encoded whole whenever
the code that draws one changes, and kept here every re-encode stayed in the
history of every clone. The figures stay because they are text: git stores a
new revision of one as a small delta, and regenerating and comparing them on
every pull request is what catches an unintended change to a plotted result.

#### Figures

If your change alters filter responses, weighting curves or any other plotted
behaviour, regenerate the figures and commit the affected ones together with
the code change:

```bash
make graphs   # runs both: python scripts/generate_graphs.py && python scripts/generate_diagrams.py
make figures  # the same generation, then the legibility and staleness checks CI runs
```

A label drawn across a curve gets the opaque chip the corpus uses everywhere
else, with a `zorder` above the curves and the `pad` its neighbours use:

```python
bbox={"boxstyle": "round,pad=0.5", "facecolor": COLOR_PANEL, "edgecolor": COLOR_GRID}
```

That is not the translucent box a note in an empty corner takes
(`{"boxstyle": "round", "facecolor": COLOR_GRID, "alpha": 0.6}`), which loses its
contrast over a line on the dark page. The `zorder` is half of the convention
and not a detail: a chip drawn under the curve is painted over with the letters
it was meant to back.

`make figures` measures both halves, on the English figure and on the Spanish
one, because Spanish prose is longer and grows into curves the English strings
clear. For every label it counts how many of its glyph pixels a stroke paints
underneath and how many never reach the page at all, and fails on the ones a
reader would struggle with. The two counts carry their own thresholds, because
they are two measurements: a struck pixel is a character still fully drawn and
merely competing with a curve, while a covered one is ink the reader never
receives. See `scripts/check_figure_annotations.py` for both numbers and for
the exemption file, which is where an annotation that must stay as it is gets
recorded with its reason.

The same run measures the tick labels of every axis. Set a frequency axis with
`format_frequency_axis(ax, language=_LANG)`; if you place the ticks of a
logarithmic axis yourself, clear its minor labels with
`ax.xaxis.set_minor_formatter(NullFormatter())`, or matplotlib keeps writing
its own between yours. `make figures` fails on either defect: minor labels
left to the scale beside major ticks set by hand, and two labels of one axis
that touch. See `scripts/check_figure_ticks.py`.

Nothing may be drawn over a tick label either. A polar plot writes its radial
labels inside the plot, along one ray, so park them where no curve runs with
`ax.set_rlabel_position(angle)` (or the `angle=` of `set_rgrids`), and label
every other ring if the curves leave no ray all of them clear. An inset writes
its labels over the data of the panel it sits in, so place it where the
parent's curves do not run under them. A legend moved out beside the axes has
to clear their labels as well as the data. `make figure-tick-clearance` reads
the committed figures for a legend, a stroke or a marker over any tick label;
see `scripts/check_figure_tick_clearance.py`.

A label you place by hand must not land on a tick label, on another label or
under a line. The Spanish wording is longer, so anchor a note near the right
of the axes by its right end (`ha="right"`) rather than letting it run out
through the spine; stop a guide line short of the words above or below it
(`axvline(..., ymin=..., ymax=...)`); and where a line has to pass behind a
note, give the note a chip and a `zorder` above the line. The same holds for
the headings and values of a plate. `make figure-text-clearance` reads the
committed figures and plates for a text over a tick label or over another
text, and for a stroke run across a text or into its letters; the leader of an
annotation, the grid and a line behind a chip pass. A text that has to stay
where it is goes in the exemption list of
`scripts/check_figure_text_clearance.py` with its reason.

When adding a feature with visual output, write its `generate_*` function in the
package the two commands are a front end for, not in the command itself:

| What you are adding | Where the builder goes | Where you register it |
| --- | --- | --- |
| A plot | `scripts/figures/<subject>.py`, beside the figures of the guide that embeds it | `_FIGURE_FUNCS` in `scripts/figures/registry.py` |
| A setup or signal-flow diagram | `scripts/diagrams/<domain>.py` | `DIAGRAMS` in `scripts/diagrams/registry.py` |
| An example `.report()` fiche | `scripts/reports/<subject>.py` | `_FICHES` in `scripts/generate_reports.py`, then `make reports` |

`scripts/generate_graphs.py` and `scripts/generate_diagrams.py` hold no builders:
they are the command lines, and `make graphs` walks the registry, so a function
added to them is never drawn. Reference the resulting image from the docs; do
not commit images produced any other way.

#### Clips

The clips are rendered into a local checkout of the assets repository and
published from it in the same command. Where that checkout is:

- `PHONOMETRY_ASSETS_DIR` in `.env`, beside the GPU settings, naming the
  `images/` directory of a checkout; or otherwise
- `../phonometry-assets`, a sibling of this repository, which `make assets`
  clones, and fast-forwards when it already exists.

Nothing falls back to `.github/images`. A clip written there would be reported
by `check_figures.py` as a figure nobody committed, and no clip enters this
repository again.

```bash
make assets                                              # once: the checkout
make animations                                          # render every clip
python scripts/generate_graphs.py --animations --anim anim_<name>   # or one
make posters                                             # only the stills, no re-encode
```

After rendering, `make animations` and `make posters` publish what they
wrote: `scripts/publish_assets.py` stages `images/` in the assets checkout,
commits with a message naming the clips and the commit here they were rendered
from, pushes to that repository's `main`, and writes the resulting commit into
`assets.lock` here. It refuses a checkout that is off `main` or carries changes
outside `images/`, so a stray file is never published under a message about
clips, and it does nothing when a render changed no bytes. `PUBLISH=no` on
either target renders without pushing, for a look.

Your commit in this repository is then two text files:

- `scripts/animation_fingerprints.txt`, the fingerprint of the code each clip
  was drawn by. The render stamps it, and so does `make posters`, because the
  poster extractor is part of that code: a change to how a poster is cut marks
  every clip stale, and re-extracting is the answer that renders nothing.
- `assets.lock`, the assets commit the clips were published to.

This works from any branch. A clip is published the moment it is rendered and
reaches the published site the moment the branch merges and the lock moves
with it, because the site is built against the locked commit and not against
that repository's `main`. An abandoned branch therefore cannot change what
`main` shows; it only leaves files nothing references in the assets
repository.

#### How each consumer gets the media

- **The site** serves its own copy of everything. `site/scripts/stage-media.mjs`
  copies the figures from `.github/images`, the WebM and posters from the
  assets checkout and the fiches from `.github/reports` into `public/media`
  before the build, and the docs workflow makes the assets checkout at the
  commit `assets.lock` records. `Video.astro`, `ThemeImage.astro` and
  `ReportPreview.astro` author the raw URL and `src/lib/media.mjs` rewrites it
  to the local copy. A missing assets checkout stops the build rather than
  warning, since a site without its videos is broken.
- **The GitHub README and the guide twins under `docs/`** load figures from
  this repository and clips from the assets repository, both at `main`,
  through `raw.githubusercontent.com`, because GitHub renders them with no
  build step.
- **The PyPI README** is generated from the GitHub one by `make pypi-readme`,
  which pins every link into this repository to the release tag and every
  poster to the commit `assets.lock` records, so a published page keeps the
  images it was released with.
- **CI** never fetches a clip to check one. The quality job does a blobless
  fetch of the locked assets commit, lists the names in its tree and hands
  `check_animation_freshness.py` that list.

#### Cloning without the figures

The figures are in this repository's tree and history, and you will not need
them to work on the code. A partial clone leaves them out and brings a working
tree of the code alone:

```bash
git clone --filter=blob:none --no-checkout https://github.com/jmrplens/phonometry.git
cd phonometry
git sparse-checkout set --cone src tests scripts docs
git checkout main
```

Cone mode keeps the root files, so `pyproject.toml`, the `Makefile` and the
requirements are there. `git sparse-checkout add .github` brings the figures
in later, and only then does git fetch them.

### 5. Conformance report (auto-generated)
`docs/CONFORMANCE.md` is generated by `scripts/conformance_report.py` from the
library's own computations against the standards, never hand-edited. If CI's
`conformance` job flags it as stale (or you changed a check, `src/phonometry`, or
a reference table), regenerate and commit it:

```bash
make conformance   # writes docs/CONFORMANCE.md, then the counts quoted from it
```

The header line of that report (`N/N conformance checks pass across D domains
and S standards`) is the only place those three integers are authoritative.
Nothing else states them by hand:

- the Astro pages import them from `site/src/data/conformance-stats.mjs`, which
  parses the header at build time;
- everything with no build step to interpolate through (`.zenodo.json`, the
  plain-markdown mirror under `docs/`, the landing-page meta descriptions and
  the JSON-LD blocks in the site frontmatter) is rewritten by the second step
  of `make conformance`, which is
  `scripts/check_conformance_claims.py --write`. It replaces only the digits of
  a recognised claim, so unrelated numbers and the surrounding prose are left
  alone.

Run `make conformance` and commit whatever it changes; do not edit those counts
by hand. The read-only `python scripts/check_conformance_claims.py` is the CI
gate, and is worth running after every rebase: a file that quotes two counts and
only disagrees on one merges without a conflict and comes out silently wrong.

Optionally run `make install-hooks` once to install a pre-commit hook that does
this automatically when relevant sources change; the CI check is the enforcement,
the hook is just convenience.

### 6. Filing an errata entry

`docs/ERRATA.md` records every defect this project claims to have found in a
published standard, guidance document, textbook or paper. Each entry is a
permanent, public statement about a named issuing body or a living author, so
it carries a higher evidential bar than the rest of the documentation.

> **The page rule.** Every errata entry whose claim depends on the exact
> characters of a formula, constant, coefficient, symbol, inequality or table
> cell must be verified against the **page as printed**, read as an image, and
> its Evidence bullet must cite that page by PDF page index and printed folio.
> Extracted text may locate a page; it may never be
> quoted as "the print". Establish the page offset empirically. Before filing,
> run the entry's own arithmetic against the familiar irrationals: if the ratio
> between printed and derived is within 0,5 % of √2, √3, π, 2π, 1/√2, ln 2 or a
> small integer, treat the entry as unproven until the page has been read as an
> image, because that ratio is the signature of a lost glyph rather than an
> author's error.

The rule exists because text extraction silently deletes glyphs. Of the
twenty-five source documents the glyph census covers, twenty-two emit
no `√` (U+221A) at all over their whole text layer, so every radical in them
extracts as if it were not there: `f_T/√2` becomes `f_T/2`. Eleven of the
twenty-five emit no `−` (U+2212) either, while emitting ASCII hyphens, and
several replace `+` with a `þ` ligature. An entry drafted on that basis accused an
author of printing `2/(3 π)` where the page prints `2/(√3 π)`; three
independent extractors agreed with each other and all three were wrong. It was
caught in review before it reached this registry. The registry's
own ISO/PAS 20065 entry is the live example: `pdftotext` reads DIN 45681's
`f_T/√2` back as `f_T/2` on both edges, which makes the DIN and ISO prints look
identical when they are not.

Practical notes:

- Render with `pypdfium2` (or any renderer) into a **private temporary
  directory per call**. Writing intermediate images to a fixed path and reading
  back "the last one" races with any other render running at the same time and
  can return a page from a different document.
- 200 dpi is enough to read a heading; use 400 to 1200 dpi for a single
  formula, especially to tell `+` from `−` or to see a radical.
- The page offset differs per document and drifts inside one document
  (books omit blank versos), so confirm the printed folio on the render itself
  rather than assuming a constant offset.
- Close the Evidence bullet with `Verified on PDF page N (printed p. M) of
  <designation>:<year>.` Cite the document, never a file path: the registry is
  a public statement about a published source, and a path pins it to one
  machine. Two checks read that sentence.
- Keep the procedure out of the entry. The resolution you rendered at is on
  this page because you need it; in the registry it reads as a machine's
  account of itself rather than a finding a maintainer stands behind, and a
  third check rejects it.

Three checks run in CI over the registry
([`scripts/check_errata_evidence.py`](scripts/check_errata_evidence.py)):

```bash
python scripts/check_errata_evidence.py          # all three checks
python scripts/check_errata_evidence.py --ratios # only the irrational-ratio linter
```

1. **The ratio linter** parses each entry for printed-versus-derived value
   pairs and flags any ratio within 0,5 % of √2, √3, π, 2π, 1/√2, ln 2 or a
   small integer. A flagged entry is not necessarily wrong (a genuine
   factor-of-ten misprint trips it too), but it must then say, in the same
   entry, that the page was read as an image. The withdrawn entry above tripped
   it twice on its own text.
2. **The page-citation check** requires every entry to cite the page it quotes,
   or to be listed, with a reason, in the allowlist at the top of the script.
   The allowlist is meant to shrink: do not add to it to get a new entry
   through, and a line whose entry now cites its page fails the build until it
   is deleted.
3. **The procedure check** rejects an entry that says how its page was read:
   a dpi figure, or the word render. That belongs here, not in a public
   statement about someone else's document.

A Spanish edition of the registry lives in
[`docs/ERRATA.es.md`](docs/ERRATA.es.md), translated entry for entry. A new or
removed entry must land in both files: `make site-reports` (and its CI job)
fails while the two editions differ in entry count, order, or the document
each heading names. Quoted print, mathematics, printed values and decimal
separators stay exactly as the cited source prints them, in both editions; the
English wording is the authoritative one and the three checks above run on it
alone.

A second script is a contributor tool rather than a gate:

```bash
python scripts/glyph_census.py plan/some-standard.pdf ...
```

It reports, per document, whether the text layer emits any `√` or `−`, and how
many C0 control characters and `þ ð ¼` ligatures it produces. A maths-bearing
document with zero `√` has invisible radicals and must not be read through its
text layer.

An OCR pass over a rendered crop, compared against the extraction, is the
screen that would have caught that entry directly; `tesseract` is not
installed in this environment, so it is not wired up. If it is added, the
comparison has to be **asymmetric**: flag tokens that OCR sees and the
extraction lacks, which is the direction a dropped glyph shows up in.

### 7. Setting a subscript

The slope of a subscript is a claim about what the subscript is, and
ISO 80000-2 fixes it. A subscript that is itself a **quantity symbol** stays
italic: the $p$ of $L_p$ is the pressure and the $W$ of $L_W$ is the power,
so both keep the slope they have standing alone. A subscript that is a
**word, a name or an abbreviation** is upright: the w of $R_\mathrm{w}$ is
"weighted". A subscript that is a **number** is upright by definition, and an
**index** that runs over a sum is a variable, so it is italic.

Where nothing in this documentation expands the letter, leave it italic.
Setting a subscript upright asserts that it abbreviates something; leaving it
italic merely omits the claim, and an omission costs less than a wrong claim.
That is why the pass which applied this rule stopped where the meaning was not
established rather than guessing, and why a new upright subscript is expected
to arrive with the sentence in this corpus, or the clause in its standard,
that expands the letter.

The drawn labels reach the same result by another route. The plate composer
keys the slope on the letter run alone (`_ROMAN_SCRIPTS` in
`scripts/diagrams/canvas.py`), so a run is upright in every plate or in none,
and the nine runs that have to stay italic somewhere are deliberately absent
from that set. Extend it only for a run that abbreviates a word.

**One meaning per subscript per file.** The rule above settles a subscript
once its meaning is known, and some glyphs honestly have two meanings. $D_z$
is the ISO 9613-2 barrier screening, whose *z* is the difference between the
diffracted and the direct path length (a quantity, italic) and it is the
ISO 2631-5 acceleration dose, whose *z* names a direction (upright). Both
documents print `D_z`, so neither spelling is ours to change, and a single
slope applied to that pair across the whole tree would be wrong in one of the
two modules by construction. Twenty pairs behave this way here: $L_N$ is a
percentile level, a loudness level and a microphone's inherent noise; $K_c$ is
a bulk modulus in the Biot model and the ISO 15186 intensity correction.

So the unit of decision is the file, not the glyph. Every module opens with
the standard it implements and every guide with the standard it explains, so
within one file a subscript has one meaning, and it is set once accordingly.
Across files, nothing is required to agree, and requiring it would force a
false claim onto one side of every pair above.

**Re-letter an index; never re-letter a quantity.** When the collision does
fall inside one file, look first at whether one of the two is an index. An
index is a bound variable: the letter is ours, it means nothing outside the
formula it runs over, and re-lettering it changes no claim. A named quantity's
letter belongs to the standard that defines it, and changing that breaks the
citation. `insulation.py` energy-averaged microphone positions with
$\sum_i 10^{L_i/10}$ on the same page as ISO 16283-2's impact sound pressure
level $L_\mathrm{i}$; the index moved to *j* and the quantity could not move at
all. Before proposing any rename, check what the source prints: in this corpus
the clash is nearly always the standards' and not ours.

**A page whose subject is the collision registers it.** The glossary exists to
put colliding symbols side by side, and cannot do that without printing both
slopes. Such a page is listed in `DECLARED` in the checker below, with both
meanings named. That list is the escape hatch for a page about the ambiguity,
not a way to land one, and it is meant to stay short.

A collision where **both uses take the same slope** is a different problem, and
typography cannot solve it: $L_\mathrm{U}$ is the magnitude of the ISO 226
linear transfer function and the upper contiguous critical band of the
prominence ratio, one section apart on one page, and $C_\mathrm{P}$ is a
specific heat capacity in a porous absorber and a propulsion coefficient in
CNOSSOS-EU. Those belong in the ambiguity table at the top of
[the glossary](docs/reference/glossary.md), beside $T_\mathrm{s}$, $R$ and
$L_N$, which is where a reader holding a symbol from someone else's report
goes to find out which one they have.

The file-level invariant is a gate; the reading behind it is not:

```bash
python scripts/check_subscript_slope.py   # or: make subscripts
```

It fails when one file writes the same base and subscript both ways, and
prints the lines of each. A comma-separated subscript is read component by
component, because that is how it is written: $\alpha_{\mathrm{s},i}$ is one
abbreviation and one index, and the run inside a single wrapper
($L_\mathrm{n,w,eq}$) is upright throughout.

It cannot check that the slope a file chose is the right one for its
standard: that is a reading of a source document, and no script does it. It
does not read `docs/ERRATA.md`, where a symbol reproduces what a published
page prints and restyling it would make the citation say something its source
does not. And it does not read the drawing modules (`src/phonometry/_plot`,
`src/phonometry/_report`, `scripts/`), which are filed by domain rather than
by standard: one plotting module holds the figures of a dozen of them, so the
file is not the scope in which a letter has one meaning. The guide that embeds
the figure is, and its snippets are read here.

The other half of the same subject is the backslash, and it has its own gate:

```bash
python scripts/check_docstring_math.py   # or: make docstring-math
```

`generate_api_docs.py` copies the mathematics of a docstring to the site
verbatim, so KaTeX reads what the docstring actually holds. A doubled
backslash is not a command: `\\mathrm` is a line break with a `mathrm` after
it, which KaTeX refuses, and the page still ships with everything after the
bad block swallowed. What makes it invisible in review is that the same four
characters are right in one kind of docstring and wrong in the other: a raw
docstring (`r"""`) takes `\mathrm`, a plain one takes `\\mathrm`. The gate
reads the value Python builds rather than the text of the file, which is the
only way to tell the two apart. The site's own `check:math` catches it too,
after a full build of every page.

### 7b. Passing the language on

A result's `.plot(language="es")` reaches the page in Spanish only if every
helper on the way is handed the language, and every one of them defaults to
English. A call that drops it raises nothing: the Spanish figure ships with an
English label, or with `31.5` on its frequency axis where it should read
`31,5`. The axis is where it cannot be caught later. `format_frequency_axis`
writes the band centres as fixed strings, which `localize_axes` will not
overwrite, so the comma can only be written by the call that makes the labels.
The rule is therefore at the call: a function that has a language in scope
passes it to every helper that takes one.

A plot function ends on `localize_axes(ax, language)`, and it needs one call
per axes it built, not one per figure: a twin axis, a colorbar and the `z` of a
3-D panel each carry a formatter of their own, and each shipped in English
beside a panel already in Spanish. A panel the save-time pass of
`scripts/figures/i18n.py` cannot reach, a zoom inset made with
`Axes.inset_axes` (a child of its host panel rather than of the figure) or a
contour colorbar (spaced by its boundaries, so its scale is not linear), is
localised by the generator with `figures.i18n.localize_panel`.

```bash
python scripts/check_language_forwarding.py   # or: make language-forwarding
```

The gate indexes every function and method of `src/phonometry` and `scripts`
that takes a `language` parameter and prints `file:line` and the helper for
each call that does not forward it, from a function that names `language` as
a parameter or a local (or one nested in it), or from any figure generator in
`scripts/figures`, which reads the language of its pass from `_LANG`. It
follows a helper through the imports, a result's `.plot()` through the class of
its receiver, and a `**kwargs` through what it can carry; a helper that takes
`**kwargs` and hands them to one that takes the language is held to the rule
too, and so is a helper reached through a local alias or a
`functools.partial`. Three shapes stay out of reach and the gate says so rather
than claiming them: a callable pulled out of a mapping, one reached by
`getattr`, and one passed in as a `Callable` parameter. Writing `language="en"`
in place of the caller's language counts as dropping it. A call that must stay
English on purpose goes in `EXEMPT` at the top of the script with its reason,
keyed by its line so one approved call cannot cover a second one written beside
it; an entry whose call has since learned to forward the language, or that has
moved, fails, so the table cannot rot.

The untyped-receiver fallback needs every method of a name to take the
language, so one namesake without it switches the name off for every call. That
state is now a failure of its own, naming the outlier, unless the name belongs
to two unrelated things and is declared in `MIXED_NAMESAKES`.

The figures are read from the other end as well, after they are drawn:

```bash
python scripts/check_figure_decimal_point.py   # or: make figure-decimal-point
```

It reads every committed `*_es.svg` and fails on a tick label that is a number
with a point in it, whichever pass was meant to write the comma. That is the
gate that closes the class: a panel none of the three passes reached shipped
`31.5` beside `52,4` in the same figure, and nothing else could see it.

The sign is read the same way, in both languages:

```bash
python scripts/check_figure_minus_sign.py   # or: make figure-minus-sign
```

A negative number is signed with U+2212. Build a reading with `_fmt_minus`
(the library's renderers with `fmt_minus`), restate the angle grid of a polar
plot that reaches below zero with explicit labels, since its formatter ignores
`axes.unicode_minus`, and format a number on a plate with `signed` from
`scripts/diagrams/canvas.py`. The check reads every committed SVG and fails on
a hyphen in front of a number; a hyphen that is not a sign, such as the part
number in "ISO 9053-1/-2", goes in its `ALLOWED` table with the reason.

### 7c. Defaulting a style the caller may spell either way

Matplotlib gives seven artist properties two names: `color` is also `c`,
`linewidth` is `lw`, `linestyle` is `ls`, `markersize` is `ms`, and the
marker-edge and marker-face colours and widths have short forms of their own.
Since matplotlib 3.3 an artist that receives both spellings of one property
raises `TypeError: Got both 'color' and 'c', which are aliases of one another`.

A renderer that installs its own default and then forwards `**kwargs` is
therefore choosing a spelling on the caller's behalf. `result.plot(c="red")`
came back as a traceback, and the shape that reads the default back out was
quieter and worse: `kwargs.pop("color", _C_PRIMARY)` takes one name, so the
second artist was drawn in the library's blue while the first kept the
caller's red, with nothing in the figure to say why.

Use the helpers of `phonometry._plot.common` rather than touching the mapping
by hand:

| Instead of | Write |
|---|---|
| `kwargs.setdefault("color", _C_PRIMARY)` | `style_default(kwargs, "color", _C_PRIMARY)` |
| `kwargs["color"]` | `style_get(kwargs, "color", _C_PRIMARY)` |
| `kwargs.pop("color", _C_PRIMARY)` | `style_pop(kwargs, "color", _C_PRIMARY)` |
| `{"color": _C_PRIMARY, "lw": 1.5, **kwargs}` | `styled(kwargs, color=_C_PRIMARY, lw=1.5)` |

```bash
python scripts/check_plot_style_defaults.py   # or: make plot-style-defaults
```

The gate reads every module of `src/phonometry` and prints `file:line` for each
of those four shapes on a mapping that is the function's own `**kwargs`. A
local dictionary the caller never sees is left alone, and so are the properties
with one name: `label`, `marker` and `zorder` cost nothing. It also compares its
own alias table against the one the helpers read, so teaching the helpers an
eighth pair without teaching the gate fails rather than passing quietly.

### 7d. Writing a long number

ISO 80000-1 and the SI Brochure group long strings of digits in threes on both
sides of the decimal marker, and the standards this library reads print their
numbers that way, so the corpus does too: `6,251 5`, `0,647 829`, `101 325`.

The separator is **U+202F, the narrow no-break space**, not an ordinary space.
With an ordinary one a line break may fall inside the number and leave `6,251`
at the end of one line and `5` at the start of the next, which reads as two
numbers. The character is in the font the figures are drawn with and in the web
fonts the site loads, and it survives the plain-Markdown twins and `llms.txt`.

```bash
python scripts/check_digit_grouping.py   # or: make digit-grouping
```

Two things the gate deliberately leaves alone, and the reasons are worth
knowing before writing a sweep of your own.

A figure or diagram label is exempt, because the defect cannot occur there: the
label is drawn as one line of text in an SVG and SVG text does not reflow.
Inside `$...$` mathtext the separator is `\,`, which is a different rule for a
different renderer.

In a Python file only the docstrings and the comments count as prose. Every
other string may be data, and one of them is: the CNOSSOS traction table is
keyed by names such as `"diesel locomotive, c. 2 200 kW"` that a caller passes
in, and an invisible character inside a key breaks the lookup on the spot. A
first pass over the corpus did exactly that and the conformance run caught it.
### 8. Writing the code fences of a documentation page

The Python fences of one page form **one sequential example**: a later fence
may use names an earlier fence defined, so a page can build a result step by
step without repeating a prelude in every block. Two rules keep that
readable, and the first is enforced in CI by
[`scripts/check_fence_names.py`](scripts/check_fence_names.py)
(`make fence-names`):

1. **A fence may only use names defined by an earlier fence of the same
   page**: never a later one, never another page. One shipped page used
   names its own figure block defined further down, while a same-named
   variable from a different room sat in scope, so reading the page top to
   bottom produced numbers that were not the annotated ones, with no visible
   error. That is the failure mode the gate exists for.
2. **When a value carries an annotated output** (`# 62.9 dB`), the fence
   that annotates should define it itself or stand right after the fence
   that does, not a section away. This one is editorial: no script can tell
   which values matter.

Names the reader owns (their measurement, their recording, their stream)
are deliberately never defined by the page, because inventing a value would
replace the reader's data with the page's. Register each one in the
`PLACEHOLDERS` table at the top of the script, keyed by the page's route
with the `es/` prefix stripped, so the Spanish twin is held to the same set;
the page must introduce the name as the reader's own, in prose or in the
fence's own marker comment (`# audio_blocks: successive frames of your
microphone recording`), which travels with the code wherever the fence is
copied. Binding the name to `...` (Ellipsis) with the same comment is the
older idiom and also valid: it defines the name, so no registry line is
needed, at the price of a fence that cannot run. A page's language twins
(site English, site Spanish, `docs/` mirror) are fixed together, never one
at a time; the `docs/` mirror is hand-written for GitHub and may carry fewer
examples, but what it does carry follows the same rules.

## 🏷️ Naming Conventions

All identifiers follow PEP 8 with the project-specific rules below (validated
against numpy/scipy, pandas, matplotlib, scikit-learn, statsmodels and librosa).

| Group | Convention | Examples |
|---|---|---|
| Modules | `snake_case` **concept** name, ≤3-4 words: never a standard number (the standard designation lives in the docstring and the guide) | `noise_induced_hearing_loss.py`, `sound_power.py` |
| Classes | `PascalCase`; the primary result of a computation is `<Concept>Result`; psychoacoustic family `<Method><Metric>` is sanctioned; value/input objects get a plain name | `ImpulseProminenceResult`, `ZwickerLoudness`, `Quantity` |
| Functions | `snake_case` noun phrase for computations; a verb only for actions/predicates; no `get_`/`calculate_` prefixes | `reverberation_time`, `apply_weighting`, `sensitivity` (not `calculate_sensitivity`) |
| Public constants | `UPPER_SNAKE_CASE`, **no unit suffixes**: units go in the docstring | `OCTAVE_BANDS`, `REFERENCE_ACCELERATION` |
| Private constants | `_UPPER_SNAKE` named after the standard's table | `_TABLE1`, `_UVL0` |
| Parameters | `snake_case` with the canonical vocabulary: `fs`, `frequencies`, `volume`, `relative_humidity`, `temperature`, `x` (time signal); durations carry `_s`/`_hours` only where mixed units coexist | — |
| Type aliases / Literals | `PascalCase` aliases; plain-string `Literal` values | `Real`, `Sex = Literal["male", "female"]` |
| Warnings | `<Topic>Warning`, all inheriting from `PhonometryWarning` | `OccupationalExposureWarning` |
| Spelling | American English in identifiers | `normalized_frequencies`, `BAND_CENTERS` |
| Tests | `test_<module>.py`, 1:1 with the module; cross-cutting suites get a descriptive name | `test_impulse_prominence.py` |

### The three verbs of a judgement

Of the public functions, the overwhelming majority are noun phrases, because
they return a magnitude: `reverberation_time`, `sound_power_level`,
`airflow_resistivity`. A verb marks the few that return a *judgement* instead,
and there are three of them. They are not interchangeable, and the difference
is what is being judged, not how strict the answer is.

| Prefix | Judges | Answers | Returns |
|---|---|---|---|
| `verify_` | an instrument or a measuring system, against the requirements a standard sets for it | may this device be used for this grade of measurement | a result dataclass with one verdict per requirement and an overall pass |
| `assess_` | a situation that was measured, against limits or categories | how bad is what we measured, and in which class does it fall | a result dataclass with the rating, the category and what drove it |
| `check_` | the arrangement or the input a method requires before its numbers mean anything | am I allowed to apply this method here | a result dataclass with the conditions and whether each holds, or nothing at all when the answer is only an advisory warning |

The boundary that used to be blurred is `check_` against `verify_`, and it is
this: `verify_` judges the **instrument**, `check_` judges the **setup**.
`verify_weighting` asks whether a vibration meter's weighting filter is inside
the tolerances of ISO 8041-1; `check_source_positions` asks whether the source
positions of a room measurement are far enough apart for the clause to apply.
Both may fail, and only the first is about a piece of equipment.

Two consequences worth stating. A summary line may open however it reads best,
as a question ("Is the band flat enough for the clause?") or with any verb that
is not one of these three, but it must not open with *another family's* verb: a
`check_` function whose docstring begins "Verify", or a `verify_` one that
begins "Check", tells a reader the family was arbitrary. And a judgement carries
its reasons, so the return is a result dataclass rather than a bare `bool`: the
caller who has to act on a failure needs to know which requirement failed and by
how much.

### Module length

There is no line limit, because no Python authority sets one. PEP 8 limits the
*line*, not the file, and subordinates its own rules to context; the Google
style guide sets no file limit either. Only two tools ship the rule at all,
both at 1000 physical lines: pylint's `too-many-lines` (C0302) and Sonar's
`python:S104`. Both hedge it. pylint's own configuration raises the limit to
2000 and then disables the checker that carries it; `S104` is not in Sonar's
default Python profile. ruff has rejected the rule twice as incompatible with
its formatter, and flake8 has never had it.

What matters is whether the file is **one subject**. A module that implements
one standard end to end is not too long at 1800 lines when half of it is the
prose that makes the implementation auditable; that prose is the reason a
reader can check the code against the clause. A module is too long when it
holds several subjects that would each be a module someone would look for by
name: three standards behind three banner comments, a translation table beside
a plot library, a topography solver inside an aircraft-noise chain.

So the test is not `wc -l`. Ask what the file is about. If the answer needs the
word "and", and each half has its own constants, its own result types and its
own callers, it is two modules. If the answer is one sentence and the length is
what documenting that sentence costs, leave it alone: forcing a split is worse
than a long file, and a package of fragments is harder to read than the file it
came from.

A split is a **move**: every name keeps its spelling, its docstring and its
body, the public API does not change, and the artifacts the module generates
come out byte-identical. That last one is the proof, and it is why the
conformance report, the figures and the diagrams are regenerated and diffed
after any such change.

The one rename a split may carry is a private name that named nothing: the
diagram builders were `_d1` to `_d9`, referenced from a registry that already
carried the real name, and moving them was the moment to call them what they
draw. That is a separate, deliberate change with its own justification, not
part of the move, and it stops at names no caller outside the file can see.

### Deprecations

Renames of **published** API keep the old name working for one cycle:

- Warn with `warnings.warn(msg, DeprecationWarning, stacklevel=...)` using
  the NEP 23 message format (deprecated-since version, removal version, and
  the replacement to use). Pick the `stacklevel` so the warning points at the
  *caller's* line: `2` when warning directly from the deprecated function,
  `3` when the warning is emitted through a shared helper.
- Renamed **modules**: keep a shim using a PEP 562 module `__getattr__`
  (scipy pattern).
- Renamed **keyword arguments**: accept the old keyword with a `"deprecated"`
  string sentinel default (scikit-learn pattern) and forward to the new one.
- Each alias gets a `pytest.warns(DeprecationWarning)` test.
- Deprecated names are removed only in a **major** release. Unpublished API
  (merged since the last release) is renamed outright, without shims.

## 📦 Releasing

Releases are fully automated from the repository-root `VERSION` file:

1. Open a PR that bumps `VERSION` (semver) and carries the three things that
   have to move with it. Bumping `VERSION` on its own turns the build red.
   - Move the `[Unreleased]` CHANGELOG section to the new version.
   - Update `CITATION.cff`'s `version` and `date-released` to match.
     `site/src/data/citation.mjs` fails the build when the CFF's `version`
     differs from `VERSION`, or when its `date-released` is later than the
     CHANGELOG heading for that version, and the docs workflow runs on any
     PR touching any of them.
   - Run `make pypi-readme` and commit `README_PYPI.md`. The PyPI page pins
     every link into this repository to the release tag and reads that tag
     from `VERSION`, so a bump on its own leaves the whole guide map on the
     published page pointing at the previous release. The packaging tests
     fail until the page is regenerated.
2. When the PR merges to `main`, the release workflow validates the version,
   builds the package, publishes to PyPI and creates the GitHub Release
   (tag included). Zenodo registers the DOI from the release webhook.

Never push tags manually; the workflow is idempotent (an existing tag is
skipped).

## 🚀 How to Contribute

### Reporting Bugs
Search the [Issues](https://github.com/jmrplens/phonometry/issues) first, then open a
new one. There is a form for each kind:

| Form | For |
|---|---|
| Bug report | A crash, a result that contradicts the library's own documentation, or a broken installation |
| Conformance defect | A disagreement with a standard that has already been established, usually in a discussion |
| Implement a standard or method | An agreed work item, once the scope and the reference data are settled |
| Documentation defect | A wrong value or formula, an example that no longer runs, a broken link |

Pull requests are labelled automatically from the paths they touch, through
`.github/labeler.yml`. Adding a package under `src/phonometry/` means adding its
`area:` entry there too.

### Pull Requests
1. **Fork** the repository.
2. **Create a branch** for your feature (`git checkout -b feature/amazing-feature`).
3. **Commit** your changes with clear messages.
4. **Verify** your code using the commands above (`pytest`, `mypy`, `ruff`).
5. **Push** to your fork and **Open a Pull Request**.

The pull request description is prefilled from
[`.github/pull_request_template.md`](.github/pull_request_template.md). Its
checklist is the CI gates written out, including the regeneration steps above
and the rule that matters most here: a new normative implementation must name
the numeric oracle it was validated against, and that oracle must be independent
of the implementation.

### Security

A suspected vulnerability goes through
[GitHub's private reporting](https://github.com/jmrplens/phonometry/security/advisories/new)
rather than an issue or a discussion. The [security policy](SECURITY.md) sets
out what is treated as a vulnerability, what is not (a value that disagrees with
a standard is a conformance defect, not a security issue), and what response to
expect.

## License
By contributing to this project, you agree that your contributions will be licensed under the project's [LICENSE](LICENSE) file.
