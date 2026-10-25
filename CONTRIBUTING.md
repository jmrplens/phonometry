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

3. **Install dependencies and the package:**
   Install both production and development dependencies to run tests and
   linters, then phonometry itself in editable mode, as CI does (`make install`
   runs the same three lines).
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e ".[full]"
   ```

## ✅ Code Quality Standards

We enforce strict code quality standards. Before submitting a Pull Request, please ensure your code passes the following checks:

### 1. Type Checking (MyPy)
We use strict type checking. Ensure no errors are reported on the paths CI
checks:
```bash
mypy src scripts stub/src tests/static_typing
```

### 2. Linting & Formatting (Ruff)
We use `ruff` for fast linting and formatting.
```bash
ruff check .
ruff format --check .
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
A warning filter in the pytest configuration names a builtin class, never
an imported one, or coverage misses every line that runs when the package
is imported ([T25](docs/contributing/tests.md#t25)).

A test still running after fifteen minutes ends the run
(`faulthandler_timeout` in `pyproject.toml`): pytest prints the stack of
every thread, the test's own frames among them. Under `-n` the controller
also names the test and fails it, and the run stops once the other workers
have run the tests already sent to them; the tests still queued do not run.
Without `-n` the process ends at the stacks, with no summary. pytest lifts
the limit when a test fails, and [`tests/hang_guard.py`](tests/hang_guard.py)
sets it again, so the teardown of a failed test has fifteen minutes from the
failure. `-o faulthandler_timeout=0` lifts the limit for a session that
needs longer.
A wait on another process or thread carries a bound of its own
([T24](docs/contributing/tests.md#t24)).

How a test is written, from where its expected values come from to how it
waits on an error or a warning, is in the [Tests](docs/contributing/tests.md)
page of the style guide. `make raises-blocks` runs
[`scripts/check_raises_blocks.py`](scripts/check_raises_blocks.py), which holds
an error or warning block to one call ([T7](docs/contributing/tests.md#t7)).

### 3a. Pinned versions and dependency floors

phonometry supports Python 3.12 and newer, and the test matrix runs 3.12,
3.13 and 3.14. Two sets of versions describe its dependencies, and they answer
different questions:

- **The pins** in `requirements*.txt` are what this repository develops, tests
  and draws its figures with. They are exact and stay at the latest releases:
  Dependabot proposes each upgrade and the suite decides. It does so with the
  `increase-if-necessary` strategy, which moves an exact pin and leaves a
  floor that already admits the new release where it is; the `increase`
  strategy would raise every floor to the newest release in the same pull
  request, and `tests/test_minimum_requirements.py` refuses it.
- **The floors** in `pyproject.toml`, under `[project.dependencies]` and
  `[project.optional-dependencies]`, are what a user may install. Each one is
  the oldest release the library's tests pass with on Python 3.12, measured
  with every other floor installed beside it, and the comment above them says
  what each one rests on. The `minimum-versions` CI job installs exactly those
  floors and runs the library's tests on them, so a floor that stops being
  true fails the pull request that made it so.

The rule: keep the pins at the latest releases, keep the floors measured, and
**never raise a floor without a failure measured at it**. When new code needs
a newer release, the `minimum-versions` job is what says so; raise that floor
to the oldest release that passes, and write the failure beside it. A floor
raised on a guess turns away every user whose environment would have worked.

The job reads the floors with
[`scripts/minimum_requirements.py`](scripts/minimum_requirements.py), which
also refuses a requirement that is not a single `>=` floor and, with
`--check`, an environment where pip settled on anything else. To run it as the
job does, in a fresh Python 3.12 environment:

```bash
python scripts/minimum_requirements.py > minimum-requirements.txt
pip install -r minimum-requirements.txt pytest pytest-xdist pypdf pypdfium2 pystoi pyyaml jsonschema
pip install --no-deps -e .
python scripts/minimum_requirements.py --check
NUMBA_DISABLE_JIT=0 pytest -n auto --without-pinned-stack
```

The figure, diagram and badge tooling is tied to the pinned stack its
committed artefacts are drawn with, so `--without-pinned-stack` leaves every
test module marked `pinned_stack` out of the run before importing it: some of
them import names the floor matplotlib does not have, and a module that fails
on import is an error whatever mark it carries. Which modules carry the mark is
[T18](docs/contributing/tests.md#t18).

The NumPy floor is also why a guard asks a value its rank before it reads it
as one number: `float()`, `int()` and `math` take a one-element array as its
element on NumPy 2.0 to 2.3 and refuse it from 2.4 on. How a guard does that
is [X6](docs/contributing/numerics.md#x6).

### 3b. Oracle data (committed vs local)

Some suites are validated against reference material that is too large or not
redistributable. Each of them keeps a small committed oracle under
`tests/data/<dataset>/` (a derived measurement series, or a lossless extract of
a representative subset) and prefers a full local copy when one is available.
Resolution order, applied by `tests/oracle_data.py`: the dataset's environment
variable, then the gitignored `tests/data-local/<dataset>/`, then the committed
data, which is what CI runs. What is committed and which tests may skip are
[T5](docs/contributing/tests.md#t5) and [T6](docs/contributing/tests.md#t6).
`pytest` prints which copy each dataset resolved to in its run header.

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

`make figures` then reads every figure for what makes it hard to read, the
English one and the Spanish one, because Spanish prose is longer and grows into
curves the English strings clear: its contrast and its language, a label
across a curve ([F44](docs/contributing/docs-and-figures.md#f44)), the tick labels of
an axis ([F35](docs/contributing/docs-and-figures.md#f35)), anything drawn over a tick
label ([F45](docs/contributing/docs-and-figures.md#f45)), a label placed by hand
([F46](docs/contributing/docs-and-figures.md#f46)), the decimal marker of a Spanish
number and the sign of a negative one. The script behind each target says what
it measures and keeps its exemptions, each with its reason.

When adding a feature with visual output, write its builder in the package the
two commands are a front end for and register it there
([F41](docs/contributing/docs-and-figures.md#f41)): `make graphs` walks the registry,
so a function added to `scripts/generate_graphs.py` or
`scripts/generate_diagrams.py` is never drawn. Reference the resulting image
from the docs, and commit exactly what the generation wrote
([F40](docs/contributing/docs-and-figures.md#f40)).

#### Clips

The clips are rendered into a local checkout of the assets repository and
published from it in the same command. Where that checkout is:

- `PHONOMETRY_ASSETS_DIR` in `.env`, beside the GPU settings, naming the
  `images/` directory of a checkout; or otherwise
- `../phonometry-assets`, a sibling of this repository, which `make assets`
  clones, and fast-forwards when it already exists.

Nothing falls back to `.github/images`. A clip written there would be reported
by `check_figures.py` as a figure nobody committed
([F51](docs/contributing/docs-and-figures.md#f51)).

```bash
make assets                                              # once: the checkout
make animations                                          # render every clip
python scripts/generate_graphs.py --animations --anim anim_<name>   # or one
make posters                                             # only the stills, no re-encode
make animation-audit ANIM=anim_<name>                    # inspect every frame, encode nothing
```

Before a clip is encoded, every frame of it is held to the gates the figures
pass ([F60](docs/contributing/docs-and-figures.md#f60)):
`scripts/clip_frame_audit.py` draws each frame, in the order the animation
draws it, as the SVG the figures are saved as, and reads it for a label a line
strikes through or a later fill paints over, a mark over a tick label, a
legend or a label's chip over a datum, tick labels run together, a fill or a
line the page swallows, a hyphen for a minus and, in Spanish, a decimal
point. The four variants of a clip are inspected before any of them is
encoded, so a finding in one stops the clip: it names the clip, the variant,
the frame and the finding, and nothing is encoded or published.
`make animation-audit` runs the same inspection without rendering a video,
stamping a fingerprint or publishing anything, and lists every finding with
the frames it holds over: the way to look at a clip after changing its
drawing code, and at every clip after changing the audit or a checker. A
finding that is a decision goes in the gate's own exemption table, keyed for
the clip the way that table keys a figure, with the reason. No CI job runs the
audit, because CI cannot render a clip; the freshness check
(`scripts/check_animation_freshness.py`) fails a change to a clip's drawing
code, in `scripts/figures` or in the `phonometry._plot` helpers it draws
with, until the clip is rendered again, and the render runs the audit.

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

Run `make conformance` and commit whatever it changes
([F6](docs/contributing/docs-and-figures.md#f6)). The read-only `python scripts/check_conformance_claims.py` is the CI
gate, and is worth running after every rebase: a file that quotes two counts and
only disagrees on one merges without a conflict and comes out silently wrong.

Optionally run `make install-hooks` once to install a pre-commit hook that does
this automatically when relevant sources change; the CI check is the enforcement,
the hook is just convenience.

### 5a. API reference and llms files (auto-generated)
Two more sets of committed files are generated, and CI fails when either is
stale:

```bash
make api-docs   # site/src/content/docs/reference/api/ and site/src/generated/api-sidebar.mjs
make llms       # llms.txt, llms-full.txt, site/public/llms/, and the section indexes and glossary under docs/
```

`make api-docs` reads every public module's `__all__` and docstrings, so run it
after changing a public name, a signature or a docstring; `make llms` reads the
guides, so run it after changing one. Commit whatever each changes: the
"Generated API reference up to date" and "llms artifacts up to date" jobs diff
those paths and fail on any difference.

### 6. Filing an errata entry

`docs/ERRATA.md` records every defect this project claims to have found in a
published standard, guidance document, textbook or paper. Each entry is a
permanent, public statement about a named issuing body or a living author, so
it carries a higher evidential bar than the rest of the documentation.

> **The page rule.** Every errata entry whose claim depends on the exact
> characters of a formula, constant, coefficient, symbol, inequality or table
> cell must be verified against the **page as printed**, read as an image, and
> its Evidence bullet cites that page as [F57](docs/contributing/docs-and-figures.md#f57) says.
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

An entry is a `## ` heading that names the document and the place, then its
bullets in this order: **Location** (the clause, table or formula, with its
printed folio), **The print** (what the page prints, quoted as printed),
**The problem**, **Evidence** (how the claim was established, citing the page),
**Library behaviour** (what the library implements, and the test or check that
pins it) and **Status**. Status says whether the defect has been reported to
its issuing body or author: `unreported` until the maintainer reports it, then
`reported` with the date and the reference. Every entry closes with its Status,
in both registers.

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
- How the Evidence bullet cites the page is [F57](docs/contributing/docs-and-figures.md#f57), and
  the procedure stays out of the entry ([P10](docs/contributing/prose.md#p10)): the
  resolution you rendered at is on this page because you need it, never in the
  registry.

Five checks run in CI over the registers
([`scripts/check_errata_evidence.py`](scripts/check_errata_evidence.py)):

```bash
python scripts/check_errata_evidence.py          # every check
python scripts/check_errata_evidence.py --ratios # only the irrational-ratio linter
```

1. **The ratio linter** parses each entry for printed-versus-derived value
   pairs and flags any ratio within 0,5 % of √2, √3, π, 2π, 1/√2, ln 2 or a
   small integer. A flagged entry is not necessarily wrong (a genuine
   factor-of-ten misprint trips it too), but it must then cite, in the same
   entry, the page it read ([F57](docs/contributing/docs-and-figures.md#f57)).
   The withdrawn entry above tripped it twice on its own text.
2. **The page-citation check** requires every entry to cite the page it quotes,
   or to be listed, with a reason, in the allowlist at the top of the script
   ([F57](docs/contributing/docs-and-figures.md#f57) says how that list may
   change). A line whose entry now cites its page fails the build until it is
   deleted.
3. **The procedure check** rejects an entry that says how its page was read:
   a dpi figure, or the word render. That belongs here, not in a public
   statement about someone else's document.
4. **The record check** requires every entry, in both registers, to close with
   its Status bullet.
5. **The count check** requires the two registers to hold the same number of
   entries.

A Spanish edition of the registry lives in
[`docs/ERRATA.es.md`](docs/ERRATA.es.md), translated entry for entry, and
`make site-reports` (and its CI job) fails while the two editions differ in
entry count, order, or the document each heading names
([F59](docs/contributing/docs-and-figures.md#f59)). How both quote the print, its mathematics
and its separators is [F58](docs/contributing/docs-and-figures.md#f58). The English wording is
the authoritative one, and the ratio, page-citation and procedure checks
read it alone.

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

## 🧭 Style

How phonometry names things, shapes its API, writes docstrings and comments,
handles numbers, writes tests, documents and draws, and words its prose is in
the [contributor style guide](docs/contributing/index.md): read the index, then
the page for the area you are changing. Every rule there says which check
enforces it.

- [Naming](docs/contributing/naming.md)
- [API shape](docs/contributing/api.md)
- [Docstrings and comments](docs/contributing/docstrings.md)
- [Numbers and data](docs/contributing/numerics.md)
- [Tests](docs/contributing/tests.md)
- [Documentation and figures](docs/contributing/docs-and-figures.md)
- [Prose, commits and pull requests](docs/contributing/prose.md)

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
2. Before merging it, rehearse the release: run the **Release** workflow by
   hand on the PR's branch (Actions, Release, Run workflow). A manual run is
   always a rehearsal and no input turns it into a release. It reads the
   version and its CHANGELOG section, waits for the PR's CI, builds the sdist
   and the wheel, checks both against git, installs the wheel with every extra
   on Linux, macOS and Windows with each supported Python and runs the
   conformance report on it, writes the SBOM and the release notes, and asks
   PyPI for an upload token with this workflow's identity, which proves the
   trusted publisher is configured, without uploading anything. The job
   summary shows the notes the release will carry.
3. When the PR merges to `main`, the same workflow runs for real: it uploads
   to PyPI through trusted publishing (no token is stored; PyPI attaches a
   signed PEP 740 attestation to each file), creates the GitHub Release with
   its tag, the files, `SHA256SUMS` and the SBOM, records the build provenance
   of each file, dispatches the GitLab mirror, and finally installs the
   published version back from PyPI on every platform. Zenodo registers the
   DOI from the release webhook. `SECURITY.md` says how anyone can verify the
   files.

Never push tags manually; the workflow is idempotent (an existing tag is
skipped). The trusted publisher is configured on pypi.org, in the project's
publishing settings: owner `jmrplens`, repository `phonometry`, workflow
`release.yml`, no environment. The PyOctaveBand bridge is published the same
way from `publish-stub.yml`.

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
3. **Commit** your changes, with messages written as
   [Prose, commits and pull requests](docs/contributing/prose.md) asks.
4. **Verify** your code using the commands above (`pytest`, `mypy`, `ruff`).
5. **Push** to your fork and **Open a Pull Request**.

The pull request description is prefilled from
[`.github/pull_request_template.md`](.github/pull_request_template.md). Its
checklist is the CI gates written out, including the regeneration steps above
and the rule that matters most here: a new normative implementation names the
numeric oracle it was validated against, independent of the implementation
([T3](docs/contributing/tests.md#t3)).

### Manufacturers' data

The library publishes the tables of books and standards, with the page each
row was read from, and no manufacturer's data sheet, declaration of
performance or test report. A sheet is revised under the same title, its terms
rarely allow copying it, and the value a project needs is the one on the
sheet the project was specified against. So such data is never merged, from an
issue or from a pull request, however it is offered. Keep it in a catalogue
file of your own and read it with `phonometry.io.read_catalogue`, as
[Your own catalogues](docs/io/material-catalogues.md) shows: that is what the
reader is for, and a problem with how it reads your file is a bug report that
needs the shape of the file, not its numbers.

### Security

A suspected vulnerability goes through
[GitHub's private reporting](https://github.com/jmrplens/phonometry/security/advisories/new)
rather than an issue or a discussion. The [security policy](SECURITY.md) sets
out what is treated as a vulnerability, what is not (a value that disagrees with
a standard is a conformance defect, not a security issue), and what response to
expect.

## License
By contributing to this project, you agree that your contributions will be licensed under the project's [LICENSE](LICENSE) file.
