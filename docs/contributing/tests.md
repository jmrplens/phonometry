← [Documentation index](../README.md)

# Tests

This page governs the test suite and the checks around it: where a test lives and what it is called, where an expected value comes from, how a test waits on an error or a warning, which data the repository keeps, how a guard and its exemptions are written and proved, how a conformance row reaches the library, and how a workflow under `.github/` is held. Read it before you add or change a file under `tests/`, a guard under `scripts/check_*.py`, a row under `scripts/conformance/` or a workflow under `.github/workflows/`.

<a id="t1"></a>
### T1. Give each module one test file, named `test_<module>.py`

**Why.** A contributor finds the tests of a module by its name, and a reviewer sees at once which module a change left without tests.

**Do**

```text
src/phonometry/environment/assessment/impulsive_sound.py
tests/environment/assessment/test_impulsive_sound.py
```

**Don't**

```text
tests/test_misc.py
tests/test_new_stuff.py
```

**Enforced by:** review

**Exceptions.** A cross-cutting suite (a guard, the architecture, the vocabulary) takes a descriptive name. A private helper module (`_shared.py`, `_choices.py`) may be tested through the public modules that use it. Two modules with one basename cannot both have their `test_<module>.py` ([T2](#t2)): the second test file takes a longer name, as `building/regulation/spain.py` is tested by `test_spanish_building_code.py`.

<a id="t2"></a>
### T2. Give every test file a basename no other test file uses

**Why.** No folder that holds a test file has an `__init__.py`, so pytest imports a test file by its bare basename, and a second `test_spain.py` anywhere is an import mismatch that shows only when the whole tree is collected.

**Do**

```text
tests/environment/assessment/test_spain.py
tests/building/regulation/test_spanish_building_code.py
```

**Don't**

```text
tests/environment/assessment/test_spain.py
tests/building/regulation/test_spain.py
```

**Enforced by:** `tests/test_package_architecture.py::test_collected_test_modules_have_unique_import_names`

<a id="t3"></a>
### T3. Derive an expected value from the printed standard, never from the code under test

**Why.** The IEC 60268-3 DIM test (#143) listed the intermodulation products with the analyzer's own loop and synthesized only the sine and the products, so an off-by-one that dropped the ninth product of Table 2 (13.35 kHz) and a search window wider than the 750 Hz spacing (which caught the 3.15 kHz fundamental) both passed: the test checked self-consistency, not correctness. Feed the method the whole signal it meets in use, strong neighboring tones included, and keep a search half-window below the smallest spectral separation, so a window too wide or an off-by-one fails. Cite each printed number to its table or clause, PDF page and printed folio, so a reviewer can find it on the page; a report fiche is anchored the same way, on the worked example its standard publishes (ISO 717-1 Annex C, ISO 11654 Annex A, ISO 532-1 Annex B, EBU 3341 Table 1).

**Do**

```python
import numpy as np

from phonometry import emission

# ISO 6926:2016 Table 2, PDF page 20, folio 14: hemi-anechoic room, fixed positions
printed = [2.0, 0.8, 0.5, 0.5, 1.0, 1.0, 1.0]
got = emission.reference_source_reproducibility(
    [63, 125, 250, 2000, 4000, 8000, 16000],
    environment="hemi-anechoic",
    arrangement="fixed",
    fraction=1,
)
np.testing.assert_array_equal(got, printed)
```

**Don't**

```py
expected = [f1 + k * spacing for k in range(1, 9)]  # the analyzer's own loop, off-by-one included
```

**Enforced by:** review

**Exceptions.** Where the standard prints no worked example, the test anchors on closed forms instead ([T4](#t4)).

<a id="t4"></a>
### T4. Without a printed worked example, test closed forms and say so in the module

**Why.** Many standards print no worked example (ISO 10848-1 to -4, ISO 16251-1, ISO 17497-1 and -2, ISO 10846-4 and -5, ISO/TS 12913-2 and -3, IEC 61260-2 and others); their conformance then rests on closed forms synthesized to a known result and on structural identities, and the reader of the module must know which numbers are printed and which are not. A missing oracle does not block the change: anchor, say so, move on.

**Do**

```python
# src/phonometry/vibration/structural/_impact_mobility.py
"""Mechanical mobility measured by impact excitation (ISO 7626-5:2019).

The part prints no worked example, so the implementation is anchored in closed
form: a single-degree-of-freedom structure struck by a smooth pulse gives its
mobility back from the averaged estimate, and its damping and mobility back
after exponential windowing and the Annex A correction.
"""
```

**Don't**

```py
"""Mechanical mobility measured by impact excitation (ISO 7626-5:2019)."""
# and the tests compare against numbers an earlier run printed, which nothing says
```

**Enforced by:** review

**Exceptions.** When a later source prints the numbers in tables (not only in figures), those tables replace the closed-form anchor ([T3](#t3)).

<a id="t5"></a>
### T5. Commit the data a test reads, with a note of its source; never commit documents

**Why.** Committed data takes the downloads out of CI and keeps those tests simple. The line is data against document, not the license: the numeric reference attachment of ISO 532-1 is data and is committed, the standard's PDF is a document and is not. Agree the subset, size and terms of a new dataset with the maintainer before committing it.

**Do**

```text
tests/data/iso532_1/iso532_1_test_signal_10.wav     byte-identical to the attachment
tests/data/iso532_1/iso532_1_annexB_expected.json   transcribed from its workbooks
tests/data/iso532_1/README.md                       source, license, version, how it was obtained
```

**Don't**

```text
tests/data/iso532_1/ISO_532-1_2017.pdf
```

**Enforced by:** review

**Exceptions.** The generated example fiches (`.github/reports/*.pdf`) are outputs of the library, not documents, and are committed.

<a id="t6"></a>
### T6. Never skip an assertion on committed oracle data; skip only full-set tests, saying why

**Why.** The committed oracle under `tests/data/<dataset>/` is what CI runs; a skip there leaves the dataset unchecked on every pull request while a local full set hides it.

**Do**

```python
import pytest

FULL_BENCH_PRESENT = False  # true only where the full stipa.info bench is on disk


def test_the_committed_extract_decodes() -> None: ...  # never skipped: the extract is committed


@pytest.mark.skipif(not FULL_BENCH_PRESENT, reason="full stipa.info bench absent")
def test_certified_bench_inventory() -> None: ...
```

**Don't**

```py
@pytest.mark.skipif(not FULL_BENCH_PRESENT, reason="no data")
def test_committed_oracle_rows(): ...  # the committed subset is always there
```

**Enforced by:** review

<a id="t7"></a>
### T7. Put one call that can raise inside a `pytest.raises`, `pytest.warns` or `pytest.deprecated_call` block

**Why.** The block passes as soon as anything inside it raises the named error, so a block that also builds its input passes on a refusal from the builder. Seven catalogue-writer tests had `io.write_catalogue(_mine(), path)` inside the block, and six warning tests built their case inside the model's block.

**Do**

```python
import pytest

from phonometry import room

surfaces = [(120.0, 0.25)]
with pytest.raises(ValueError, match="'volume' must be positive"):
    room.sabine_reverberation_time(-200.0, surfaces)
```

**Don't**

```py
with pytest.raises(ValueError):
    surfaces = [(120.0, 0.25)]
    room.sabine_reverberation_time(-200.0, surfaces)
```

**Enforced by:** `scripts/check_raises_blocks.py`, `make raises-blocks`, `CI: Every exception test waits on one call`, `ruff PT012`, `tests/test_check_raises_blocks.py`

**Exceptions.** Calls SonarCloud holds safe do not count (python:S5778 and S9088, which the script copies): builtin conversions and containers (`float("nan")`, `len`, `list`), `pathlib` paths, `copy`, and anything in NumPy or SciPy. A call inside a lambda or a nested `def` is deferred. Unlike ruff PT012, the script refuses a block of several statements even with `noqa: PT012`. `EXEMPT` in the script, keyed by (file, test) with its reason, is empty.

<a id="t8"></a>
### T8. Match every `pytest.raises` to its quoted identifier and a stable predicate

**Why.** A withdrawn name, a misspelled field and an assignment to a frozen record all raise `AttributeError`, and a bare block passes on whichever happened; `match=` is `re.search`, so a loose fragment passes when the wrong guard fires, and one that quotes the whole sentence breaks every time the prose is reworded. Read the fragment off the real `raise` in the source, keep the identifier and the predicate, trim what moves (an enumeration of allowed values, a numeric bound, third-party wording, a compound predicate that could split into two guards), and check that no sibling guard of the same call matches it; a message that is already an identifier and a simple predicate stays whole (`'frequencies' must be positive`).

**Do**

```python
import pytest

from phonometry import fluids

# the message ends "above -273.15 degC.": the bound is trimmed, the predicate kept
with pytest.raises(ValueError, match="'temperature_c' must be a finite temperature"):
    fluids.air(temperature_c=-300.0)
```

**Don't**

```py
with pytest.raises(ValueError, match="finite"):
    fluids.air(temperature_c=-300.0)
```

**Enforced by:** `ruff PT011`, review

<a id="t9"></a>
### T9. Never pin a test to numpy's or Python's own message; validate in the function

**Why.** numpy's broadcast message is assembled in a C extension with no promise of stability, and a test that can only match it shows that the function lacks its own validation: fix the library, not the test.

**Do**

```python
import pytest

from phonometry import environment

with pytest.raises(ValueError, match="'levels' and 'probabilities' must have the same shape"):
    environment.long_term_sel([60.0, 62.0, 65.0], [0.5, 0.5])
```

**Don't**

```py
with pytest.raises(ValueError, match="operands could not be broadcast"):
    some_function(levels, frequencies[:-1])
```

**Enforced by:** review

**Exceptions.** A test that proves a removal pins Python's message on purpose, because nothing is left for the library to validate: `No module named` or `has no attribute` for a retired name ([T11](#t11)), `cannot unpack non-iterable` for a return that became a record.

<a id="t10"></a>
### T10. Name the topic warning class in `pytest.warns`, never `UserWarning`

**Why.** A test that waits on `UserWarning` passes on any advisory, and the topic class is what a caller filters on.

**Do**

```python
import pytest

from phonometry import emission

with pytest.warns(emission.SoundPowerWarning, match="16 kHz octave band"):
    emission.high_frequency_sound_power([60.0], frequencies=[8_000.0], room_constant=4.0)
```

**Don't**

```py
with pytest.warns(UserWarning):
    emission.high_frequency_sound_power([60.0], frequencies=[8_000.0], room_constant=4.0)
```

**Enforced by:** review

<a id="t11"></a>
### T11. Pin a retired public name as gone in `tests/test_removed_names.py`

**Why.** Without a pin, a later change can bring an old address back as a second one: a module re-exported one level up, a constant reintroduced under its old spelling, a stale file left on disk after a package split.

**Do**

```python
import importlib

import pytest

# tests/test_removed_names.py
with pytest.raises(ModuleNotFoundError, match="No module named 'phonometry.signals.correlation'"):
    importlib.import_module("phonometry.signals.correlation")
```

**Don't**

```py
# the rename's only test: the new name works, and nothing says the old path is gone
def test_correlation_is_callable():
    assert callable(signals.correlation)
```

**Enforced by:** review

<a id="t12"></a>
### T12. Test what a renderer draws, and add it to the plot contract

**Why.** Three review rounds (2026-09-02/03) found every defect in figure code and none in the normative arithmetic, which is checked against the page and comes out right first time; running a renderer and looking at it validates legibility, not code, and Sonar put new-code coverage at 68.8 % with the whole graph as the hole. So read the drawn artists back (line data, limits, labels, title) in English and Spanish in the domain's own test file, and give the result its row in `_KWARG_PLOT_CASES` of `tests/test_result_plots.py`, the cross-cutting contract (`ax` first, `language` by name, keywords reach the primary artist). A second segment or an overlay that the reader sees as one thing with the primary artist gets every option but `label` forwarded to it, and a test of its own; how a renderer defaults a style is [F33](docs-and-figures.md#f33).

**Do**

```python
from phonometry import materials

check = materials.check_base_plate_scattering([0.05] * 18)
ax = check.plot(language="es")
assert list(ax.get_lines()[0].get_ydata()) == [0.05] * 18
assert ax.get_title() == "Placa base sola frente a la tabla 1 (ISO 17497-1)"
```

**Don't**

```py
def test_the_coherence_plots():
    assert result.plot() is not None
```

**Enforced by:** `tests/test_result_plots.py`, `tests/test_answer_record_plots.py`, review

**Exceptions.** The contract tests run over the rows `_KWARG_PLOT_CASES` holds and the content tests over the renderers they name; that a new renderer has its row and a test of what it draws is review.

<a id="t13"></a>
### T13. Show a new value test failing on a deliberately broken copy

**Why.** A value test that passes on broken code tests nothing; a time axis scaled by 1.5 used to pass the whole metrology suite.

**Do**

```text
break _find_peak of src/phonometry/psychoacoustics/quality/tonality.py so it
ignores tone_frequency: the new test fails; restore it: the test passes
```

**Don't**

```text
a new value test only ever seen green
```

**Enforced by:** review

<a id="t14"></a>
### T14. Close a defect's whole class with a guard, and watch the guard fail on it

**Why.** On 2026-09-03/04 four point findings became three closed classes, and every sweep found cases nobody had reported (a published field type no package published, then a second one; `frozen=True` not reaching what a field points to). A guard only ever seen passing is not proven: only seeing it red tells "configured" from "detects". A new guard script ships with a test that shows it failing on the defect it closes (`tests/test_check_<name>.py`), and a new CI job is proved on a scratch draft pull request that carries the real defect, with a value that really falls outside the limit, then closed.

**Do**

```text
Found:   noise_control.HVACWarning raised and not published, reproduced by running it
Class:   a warning a package can raise and does not publish
Guard:   tests/test_package_architecture.py::test_every_warning_a_package_can_raise_is_published
Proved:  red on the base with the fix reverted in a scratch copy, then green on the branch
```

**Don't**

```text
Fixed the export of HVACWarning; nothing else looked at, nothing added.
```

**Enforced by:** review

<a id="t15"></a>
### T15. Key every guard exemption by location with its reason, and fail a stale one

**Why.** An exemption list without reasons cannot be reviewed, and one that is never pruned rots: an entry outlives the site it excused and silently covers the next defect written there. A two-way ratchet goes further and also fails when the excused defect is fixed and its line stays (`PAGE_UNKNOWN` of `scripts/check_published_sources.py`, `ACCEPTED` of `scripts/check_solid_agreement.py`).

**Do**

```python
POSITIONAL: dict[tuple[str, str, str], str] = {
    ("phonometry.metrology.calibration", "sensitivity", "reference_pressure_pa"): (
        "the positional form is part of the Signal overload contract of this function"
    ),
}
used: set[tuple[str, str, str]] = set()  # filled by the scan with every key it met
stale = [key for key in POSITIONAL if key not in used]  # each one fails the guard
```

**Don't**

```py
EXEMPT = {"sensitivity"}  # no location, no reason, never checked for staleness
```

**Enforced by:** review

**Exceptions.** A positional exemption that is part of the rule itself (the em-dash guard's standard titles) needs no table.

<a id="t16"></a>
### T16. Read public names from the imported package, and source text through `ast`

**Why.** Two guards missed their whole class: the unit guard first scanned files and never saw `ReportMetadata`, published from the root and defined in the private `_report/metadata.py`; the comma-decimal guard read src line by line, saw only the `msg = (` of each multi-line refusal and caught zero cases, and rewritten with `ast` found five (#674).

**Do**

```python
import ast
import inspect

from phonometry import environment

published = environment.__all__
module = inspect.getmodule(environment.long_term_sel)  # its private home
messages = [
    node.value
    for node in ast.walk(ast.parse(inspect.getsource(module)))
    if isinstance(node, ast.Assign) and ast.unparse(node.targets[0]) == "msg"
]
```

**Don't**

```py
for line in path.read_text().splitlines():
    if line.lstrip().startswith("msg = "):
        ...
```

**Enforced by:** review

**Exceptions.** What an f-string interpolates is invisible statically and cannot be required; only its literal parts can. A message scan leaves docstrings out on purpose, since a citation there keeps its source's separator, and a pattern for a decimal skips subscript notation such as `k2,1` and `F2,b` (`(?<![A-Za-z])\d,\d`).

<a id="t17"></a>
### T17. Fix a tool that misreads correct data; never trim the data to pass

**Why.** The conformance reference reader accepted only four-digit years, so `DIN 45669-1:2010-09` was cut to `:2010` and `Ber 1:2012-12` turned into a clause; measured, the class was larger (`VDI 2081 Blatt 1:2001-07` and `Blatt 2:2005-05` fused into one undated designation). A precedent that already degraded the data is another site to fix, not a permission.

**Do**

```text
DIN 45669-1:2010-09 kept; the reference reader learns month editions; the
tree is swept for the class; a test pins it.
```

**Don't**

```text
DIN 45669-1:2010  (edition trimmed so the reader accepts it)
```

**Enforced by:** review

<a id="t18"></a>
### T18. Mark a test of the figure, diagram or badge tooling `pinned_stack`

**Why.** The dependency-floors job runs the library's tests without the pinned figure stack and leaves the marked modules out before importing them, reading the module-level `pytestmark` from the source (`tests/pinned_stack.py`); an unmarked one fails there on a stack its figures were never drawn with.

**Do**

```python
import pytest

pytestmark = pytest.mark.pinned_stack
```

**Don't**

```py
# a test module of the figure tooling, with no pinned_stack mark
from figures import registry
```

**Enforced by:** `tests/test_minimum_requirements.py`, `CI: Library tests at the dependency floors`

<a id="t19"></a>
### T19. Group the tests of an expensive module fixture with `xdist_group`

**Why.** Under `-n` each worker would otherwise compute the same FDTD steady state, ECMA-418-2 reference or conformance registry once more.

**Do**

```python
import pytest

pytestmark = pytest.mark.xdist_group("conformance-report")
```

**Don't**

```py
# a module-scoped fixture that takes a minute, its consumers spread over workers
```

**Enforced by:** review

<a id="t20"></a>
### T20. Make every conformance row call the library; never recompute the expected value

**Why.** A row that computes its expected value from the same constants compares a formula with itself and passes whatever the library does: the rows for VDI 2081 Equations (16), (17) and (34) would have passed with a wrong sign in the straight-duct flow noise.

**Do**

```python
from phonometry import noise_control

# VDI 2081 Blatt 1:2001-07 Eq. (16), Table 1 element 5: printed as 38 dB
area_m2 = 0.5 * 0.4
got = noise_control.flow_noise_straight_duct_overall((4200.0 / 3600.0) / area_m2, area_m2)
assert abs(got - 38.0) <= 0.5
```

**Don't**

```py
got = 10 * math.log10(...)  # Eq. (16) again, from the same constants, not the library
assert abs(got - 38.0) <= 0.5
```

**Enforced by:** `scripts/check_conformance_rows.py`, `make conformance-rows`, `CI: Every conformance row runs the library`

**Exceptions.** `ORACLE_ONLY` in `scripts/check_conformance_rows.py`, keyed `'<module>.<check function>'`, each entry with its reason: a row that pins the geometry of a test case, checks the standard against itself, or pins a dependency's published constant. A declared row that has since learned to call the library fails, so the list cannot rot.

<a id="t21"></a>
### T21. Add a new conformance vocabulary value to the site schema and both label maps

**Why.** The verdict, comparison, tolerance, document-kind and relation vocabularies are Python enums restated in `site/src/content.config.ts` (Zod) and in `site/src/components/Conformance.astro` (English and Spanish labels). A fifth relation value, `supplies`, reached ten rows of the artifact and stopped the site build with an `InvalidContentEntryDataError` naming no cause; the Spanish table would have printed `supplies` raw.

**Do**

```text
scripts/conformance/references.py       Relation.SUPPLIES = "supplies"
site/src/content.config.ts              "supplies" in the relation z.enum
site/src/components/Conformance.astro   an English and a Spanish label for supplies
then                                    make conformance
```

**Don't**

```text
the enum member in Python only, and the artifact regenerated
```

**Enforced by:** `scripts/check_conformance_vocabulary.py`, `make conformance-vocabulary`, `CI: Conformance report up to date`

<a id="t22"></a>
### T22. Write every workflow so that zizmor finds nothing under `.github/`

**Why.** The workflows hold the repository's tokens and the release's identity, and nothing reviewed them: the release step expanded a workflow expression straight into a shell, eight checkouts left their token in `.git` for any later step to read, and the mirror waited on a `workflow_run` trigger that had never fired. The CI step reads every file under `.github/` and fails on any finding. Run it before you push a workflow change: `zizmor --config .github/zizmor.yml .github/` (zizmor is in `requirements-dev.txt`).

**Do**

```yaml
- uses: actions/checkout@v7
  with:
    persist-credentials: false
```

**Don't**

```yaml
- uses: actions/checkout@v7  # leaves the token in .git for every later step
```

**Enforced by:** `CI: Audit the workflows with zizmor`

**Exceptions.** A finding that is not a defect is settled once for the repository in `.github/zizmor.yml`, with its reason in a comment, never in a workflow.

<a id="t23"></a>
### T23. Pin every action to a release tag, never a branch or a commit SHA

**Why.** zizmor's `ref-pin` policy accepts any ref, so a workflow that ran an action at `@master` passed it: the JOSS draft action did, and a push to that branch would have run in the next build of the paper. A commit SHA is not used either: a tag is what Dependabot moves and what a reader can check against the action's releases.

**Do**

```yaml
- uses: openjournals/openjournals-draft-action@v1.0
```

**Don't**

```yaml
- uses: openjournals/openjournals-draft-action@master  # runs whatever lands on the branch next
```

**Enforced by:** `tests/test_repository_config.py::test_every_action_is_pinned_to_a_release_tag`, `CI: Audit the workflows with zizmor`

**Exceptions.** An action whose maintainers publish no moving major tag is followed on the branch its README names as the release channel, listed with its reason in `_ACTION_CHANNELS` of the test: `pypa/gh-action-pypi-publish@release/v1`.
