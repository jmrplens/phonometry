← [Documentation index](../README.md)

# API shape

This page governs the public surface of phonometry: where a name lives and how it is imported, how a module declares what it publishes, the shape of a signature, what a function hands back, how a verdict answers, which error or warning a refusal raises, and how a name is renamed or retired. Read it before you add, rename or remove a public name, change a signature or a result record, or raise an error or a warning. Examples that import from `phonometry._internal` stand for code inside the package, where the import is relative ([A11](#a11)).

<a id="a1"></a>
### A1. Give every public name exactly one public address

**Why.** A name reachable from two modules is two names for one object: the reference documents one and callers import the other. `building.measurement.insulation` re-exported the ISO 717 ratings after they moved, `vibration.partial_exposure` was a second name for `daily_exposure`, and `plot_excitation` was published by the root and by no domain.

**Do**

```python
from phonometry import building

building.weighted_rating
```

**Don't**

```py
from phonometry.building.measurement.insulation import weighted_rating
partial_exposure = daily_exposure  # a second name for one function
```

**Enforced by:** `scripts/check_api_reference.py`, `CI: Curated API quick table covers __all__`, `tests/test_removed_names.py::test_a_leaf_module_publishes_only_what_it_defines`, `tests/test_package_architecture.py::test_every_public_name_is_reachable_from_its_domain`, `tests/test_package_architecture.py::test_no_public_name_is_published_by_two_domains`

**Exceptions.** A name a private module defines is published by the one public module that imports it; the private path is not an address. `Signal` has two: `phonometry.io` owns it and the root re-exports it, because every package that takes measured audio accepts it ([A3](#a3), `ROOT_ONLY` in `tests/test_package_architecture.py`).

<a id="a2"></a>
### A2. Declare `__all__` in every public module, listing exactly what it defines and publishes

**Why.** 119 public modules had no `__all__`, so a constant one of them kept for itself looked as public as its functions, and some reached the guides by their full module path.

**Do**

```python
__all__ = ["octave_band_centers"]

_OCTAVE_BANDS_HZ = (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0)


def octave_band_centers() -> tuple[float, ...]:
    return _OCTAVE_BANDS_HZ
```

**Don't**

```py
# no __all__, and a bare constant the module only reads itself
OCTAVE_BANDS = (125.0, 250.0, 500.0)
```

**Enforced by:** `scripts/check_api_reference.py`, `CI: Curated API quick table covers __all__`

**Exceptions.** A type alias, a `TypeVar` or a `Protocol` needs neither a listing nor an underscore ([A5](#a5)). Any other exception is keyed by location, with its reason, in `UNLISTED_EXEMPTIONS` of `scripts/check_api_reference.py`.

<a id="a3"></a>
### A3. Keep the root to the domain packages and four shared names

**Why.** Of the 367 public classes only six crossed package borders, and only `Signal` did so for real (seven domains); a root that re-exported every function gave each name two addresses (decided 2026-08-19). The four shared names are `PhonometryWarning`, `ReportMetadata`, `Signal` and `__version__`; everything else in `phonometry.__all__` is a domain package.

**Do**

```python
import phonometry

phonometry.Signal, phonometry.room
```

**Don't**

```py
from phonometry import octave_filter
```

**Enforced by:** `scripts/check_api_reference.py`, `tests/test_package_architecture.py::test_every_public_name_is_reachable_from_its_domain`

<a id="a4"></a>
### A4. Import a domain package and reach every name through it

**Why.** Google's Python style guide imports packages and modules only, never single functions or classes, and SciPy asks the same. Six phonometry names collide with names in `scipy.signal` and `numpy` (`coherence`, `envelope`, `group_delay`, `spectrogram`, `zoom_fft`, `info`), which the docs used to dodge by hand with `from scipy import signal as sp_signal`.

**Do**

```python
from phonometry import signals

signals.envelope
```

**Don't**

```py
from phonometry.signals import envelope
```

**Enforced by:** review

**Exceptions.** Where the standard library's `io` and phonometry's meet, write `import phonometry as pm` and `pm.io`. `Signal` is written `io.Signal` or `phonometry.Signal`. Importing a submodule (`from phonometry.noise_control import hvac`) is the module form too. Outside the package, never import through a private module path (`phonometry.signals._correlation`): a value a guide needs that only a private module holds is published by its package, with its unit and a curated row ([A7](#a7)), or read off the result that carries it (`hearing.nipts(...).frequencies`). Tests may import a private helper by its leaf path.

<a id="a5"></a>
### A5. Never publish a type alias, a `TypeVar` or a `Protocol`

**Why.** Publishing an alias later is additive, while withdrawing one after 4.0 would need a 5.0; the API reference prints an unpublished alias as its definition, so a signature still reads its options. The alias stays in its module, unlisted, in PascalCase and with no underscore ([N34](naming.md#n34)). An unlisted protocol declares each member a frozen record meets by being read as a read-only `@property`, never as a plain annotation, which asks for an attribute a caller may set and so refuses every frozen record it was written to accept.

**Do**

```python
from typing import Literal

DeclarationForm = Literal["dual-number", "single-number"]
__all__ = ["NoiseEmissionDeclaration"]
```

**Don't**

```py
__all__ = ["DeclarationForm", "NoiseEmissionDeclaration"]
```

**Enforced by:** `scripts/check_api_reference.py`, `CI: Curated API quick table covers __all__`, `tests/test_package_architecture.py::test_a_protocol_declares_its_data_members_as_properties`

<a id="a6"></a>
### A6. Publish every type a published record's field can hold

**Why.** `TrackDescriptor` declared `TrackMeasure` and `RailJoints` as fields and `from_code` handed them back, so a caller held a type it had no supported way to import. The test resolves the annotations instead of skipping them: skipping had left 177 of 494 published dataclasses unchecked.

**Do**

```python
from phonometry import environment

environment.TrackDescriptor, environment.TrackMeasure, environment.RailJoints
```

**Don't**

```py
__all__ = ["TrackDescriptor"]  # its fields are TrackMeasure and RailJoints
```

**Enforced by:** `tests/test_package_architecture.py::test_a_published_field_type_is_published_too`

**Exceptions.** Fields with a leading underscore.

<a id="a7"></a>
### A7. Give every public name a curated API row whose type column is true

**Why.** The hand-written table in `docs/reference/api/index.md` is the GitHub and PyPI quick reference: it silently missed new names, twenty-one rows called a mapping, a tuple or an array a `function`, and a row for a name nothing publishes teaches an import that fails. The type column takes any word the gate finds true of the object: `function` or `method` for a callable; `class`, `dataclass`, `enum` or `warning class` for a class; `mapping` or `table` for a mapping; `constant`, `value` or the concrete type (`tuple`, `ndarray`) for any other value, so a printed table held in a tuple or an array says so in the prose of its cell. The gate does not read signatures: a renamed parameter changes its row, and the keys of `scripts/api_taxonomy.py`, in the same commit.

**Do**

```markdown
| `AUDIOMETRIC_FREQUENCIES_HZ` | `ndarray` | **The eleven audiometric frequencies of ISO 389-7:2005 Table 1** [Hz] |
```

**Don't**

```markdown
| `AUDIOMETRIC_FREQUENCIES_HZ` | `table` | The audiometric frequencies |
```

**Enforced by:** `scripts/check_api_reference.py`, `CI: Curated API quick table covers __all__`

**Exceptions.** Rows for methods, namespace subpackages and `convention` rows (`.plot()`) are allowed although no `__all__` lists them.

<a id="a8"></a>
### A8. Import across domain packages only along an edge the architecture test lists

**Why.** The dependency graph between domains is a contract: an import from one domain into another claims that one audience's work feeds the other's, and the claim is written down, not noticed. Every domain may import the toolbox (`filters`, `fluids`, `signals`, `metrology`) and `_internal`, and `_internal` imports no domain code.

**Do**

```python
# tests/test_package_architecture.py
ALLOWED_EDGES = {
    ("aircraft", "environment"),  # atmospheric absorption reuse
}
```

**Don't**

```py
# src/phonometry/room/x.py
from ..building.prediction import flanking  # no (room, building) edge
```

**Enforced by:** `tests/test_package_architecture.py::test_cross_package_edges_are_whitelisted`, `tests/test_package_architecture.py::test_family_edges_are_whitelisted`, `tests/test_package_architecture.py::test_internal_imports_no_domain_code`

**Exceptions.** An edge is declared in `ALLOWED_EDGES` (domain to domain) or `ALLOWED_FAMILY_EDGES` (subgroup to subgroup inside a domain) of `tests/test_package_architecture.py`, with a comment saying why; adding one is an explicit, reviewed decision. The root facade and the rendering leaves are not counted as sources.

<a id="a9"></a>
### A9. Import domain code in `_plot` and `_report` only under `TYPE_CHECKING`

**Why.** The rendering leaves are imported lazily by `.plot()` and `.report()`; a module-level import of domain code from them creates a cycle and drags the domain into every render.

**Do**

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..room.modes import RoomModesResult
```

**Don't**

```py
from ..room.modes import RoomModesResult  # at module level in src/phonometry/_plot/room.py
```

**Enforced by:** `tests/test_package_architecture.py::test_render_modules_only_type_check_domain_imports`

**Exceptions.** Imports from `_internal`, which imports nothing from the domains.

<a id="a10"></a>
### A10. Import matplotlib inside the function that draws, never at module scope

**Why.** matplotlib is a soft dependency: importing phonometry and computing must work without it, and `.plot()` without it must fail with the install command (`pip install "phonometry[plot]"`), not a bare `ModuleNotFoundError`.

**Do**

```python
from numpy.typing import ArrayLike


def draw(levels: ArrayLike) -> None:
    import matplotlib.pyplot as plt

    _, ax = plt.subplots()
    ax.plot(levels)
```

**Don't**

```py
import matplotlib.pyplot as plt  # at the top of a phonometry module

def draw(levels): ...
```

**Enforced by:** `tests/test_matplotlib_backend.py::test_no_module_scope_matplotlib_import_anywhere`, `tests/test_matplotlib_backend.py::test_import_succeeds_without_matplotlib`, `tests/test_result_plots.py::test_plot_raises_helpful_error_without_matplotlib`

**Exceptions.** An import under `if TYPE_CHECKING:`.

<a id="a11"></a>
### A11. Import the package's own modules relatively inside `src`

**Why.** The package imports its own modules relatively by design, which is why ruff's TID family is not selected.

**Do**

```text
from ..._internal.frozen import OwnsArrays
```

**Don't**

```text
from phonometry._internal.frozen import OwnsArrays
```

**Enforced by:** review

<a id="a12"></a>
### A12. Give every source directory an `__init__.py`

**Why.** A directory without one still imports locally, as a namespace package, and goes missing elsewhere.

**Do**

```text
src/phonometry/fluids/__init__.py
```

**Don't**

```text
src/phonometry/fluids/   (modules, and no __init__.py)
```

**Enforced by:** `ruff INP001`

<a id="a13"></a>
### A13. Remove a renamed or retired name outright, with no alias, shim or warning, before 4.0.0

**Why.** 3.x had no users to protect beyond a few beta testers, so a transition path only kept `_compat.py` alive (105 module-path shims, about 1000 lines with its test) to protect nobody (decided 2026-08-19).

**Do**

```python
from phonometry import filters

hasattr(filters, "octavefilter")  # False: the 3.x name went, with no alias
```

**Don't**

```py
octavefilter = octave_filter  # kept for old callers
```

**Enforced by:** `tests/test_removed_names.py`, `scripts/check_api_reference.py`, `tests/test_package_architecture.py::test_a_module_getattr_is_hidden_from_the_type_checker`, `tests/static_typing/test_root_names.py`

**Exceptions.** The module `__getattr__` that lazily imports the package's own domains (`src/phonometry/__init__.py`, PEP 562) is not an alias. It is defined under `if not TYPE_CHECKING:`, so a type checker reads the names the package publishes and refuses a misspelt one instead of typing it `object`; `tests/test_package_architecture.py` holds every module `__getattr__` of the package to that. After 4.0.0, a name no release shipped is still removed outright, and a shipped one follows [A16](#a16).

<a id="a14"></a>
### A14. Record every shipped name you rename or remove in the migration guide's three copies

**Why.** A caller upgrading from 3.3.0 or 4.0.0rc1 reads the migration guide, not the diff, and the guide maps the shipped name straight to the final one, never through an intermediate name. Its three copies are `docs/start/upgrading.md` and the English and Spanish site pages.

**Do**

```markdown
| 3.3.0 or 4.0.0rc1 | 4.0 |
| --- | --- |
| `vibration.partial_exposure` | `vibration.daily_exposure`, the function it was a second name for |
```

**Don't**

```text
CHANGELOG only: "partial_exposure is now daily_exposure"
```

**Enforced by:** review

**Exceptions.** A name newer than the last release goes in the CHANGELOG `[Unreleased]` only. `git grep -nw NAME v3.3.0 -- src` and `git grep -nw NAME v4.0.0rc1 -- src` tell whether a name shipped.

<a id="a15"></a>
### A15. Move every caller of a renamed name in the same commit

**Why.** A rename that leaves a caller behind breaks a test, a figure script, a guide example or an errata citation. Every caller means src, tests (fixtures and `match=` strings included), the conformance domains, the figure, diagram and report scripts, the guides in their three places (the `docs/` mirror and both site twins each carry their own copy of an example), the errata registers where they cite a code name, and the README.

**Do**

```text
git grep -nw old_name -- src tests scripts docs site README.md
```

**Don't**

```text
rename in src, and leave docs/ and the Spanish site page for later
```

**Enforced by:** `scripts/check_doc_snippets.py`, review

<a id="a16"></a>
### A16. After 4.0.0, keep a renamed shipped name working for one release with a `DeprecationWarning`

**Why.** A caller's code keeps running for a release and is told what to use instead; a deprecated name goes only in a major release. The message follows NEP 23 (the version that deprecates, the version that removes, the replacement) and says "deprecated since phonometry", which the suite's `filterwarnings` turns into an error, so every deprecation is met on purpose by a `pytest.warns(DeprecationWarning)` test. `stacklevel` is 2 from the deprecated function itself and 3 through a shared helper; a renamed module keeps a PEP 562 module `__getattr__` shim (SciPy's pattern), and a renamed keyword accepts the old one through a `"deprecated"` string sentinel and forwards it (scikit-learn's).

**Do**

```python
import warnings


def new_name(value: float) -> float:
    return 2.0 * value


def old_name(value: float) -> float:
    warnings.warn(
        "old_name is deprecated since phonometry 4.1.0 and will be removed in 5.0.0; use new_name instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return new_name(value)
```

**Don't**

```py
warnings.warn("old_name is deprecated", DeprecationWarning)  # no versions, no replacement, stacklevel 1
```

**Enforced by:** review

**Exceptions.** A name merged since the last release is renamed outright, without a shim ([A13](#a13)).

<a id="a17"></a>
### A17. Take a frequency or wavelength axis by keyword beside the values it labels

**Why.** Two arrays of one length bind either way round: given the tone frequencies and levels swapped, `combined_tone_level` answered 49.4 dB for the ISO/PAS 20065 Annex E tones whose combined level is 72.15 dB, and `perimeter_absorption_coefficient` 8.8e-11 instead of 0.139. Defaulted unit-named parameters and medium conditions are keyword-only too ([N22](naming.md#n22)).

**Do**

```python
from phonometry import room

levels = [60.0, 55.0, 50.0, 45.0, 40.0, 38.0, 36.0, 35.0]
frequencies = [63, 125, 250, 500, 1000, 2000, 4000, 8000]
nc = room.noise_criterion(levels, frequencies=frequencies)
```

**Don't**

```py
room.noise_criterion(levels, frequencies)
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_writes_every_function_axis_by_name`

**Exceptions.** The values the axis labels stay positional, in their order. A frequency axis is `frequencies`, `frequency` where a function is vectorized over it, `frequencies_hz` in underwater, or a name ending in one of them (`tone_frequencies`); a wavelength axis is `wavelengths`, a name starting with it (`wavelengths_mm`), or `wavelength` when vectorized. Any other exception is declared in `FUNCTION_AXIS_EXEMPT` of `scripts/check_parameter_units.py`, with its reason.

<a id="a18"></a>
### A18. Make every record a caller builds keyword-only

**Why.** An input record is built field by field like a function call, so two fields of one type bind either way round in it: a frequency axis and the values it labels ([A17](#a17)), a label and a code, a lower and an upper attenuation. A condition a record holds is keyword-only for the same reason ([N22](naming.md#n22)), and a record that takes its fields by name keeps every call site readable as the record grows.

**Do**

```python
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class TonalBands:
    levels: tuple[float, ...]
    frequencies: tuple[float, ...]


tones = TonalBands(levels=(60.0, 55.0), frequencies=(500.0, 1000.0))
```

**Don't**

```py
@dataclass(frozen=True)
class TonalBands:
    levels: tuple[float, ...]
    frequencies: tuple[float, ...]

TonalBands((500.0, 1000.0), (60.0, 55.0))  # swapped, no error
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_writes_every_input_record_axis_by_name`, `tests/test_check_parameter_units.py::test_the_tree_writes_every_input_record_by_name`, `tests/test_check_parameter_units.py::test_every_field_of_an_input_record_is_written_by_name`, `tests/test_check_parameter_units.py::test_a_record_behind_a_union_alias_is_written_by_name`, `tests/test_curated_examples.py::test_no_inline_example_builds_a_record_by_position_or_unpacks_one`

**Exceptions.** The rule covers every public record another public function takes (`aircraft.RotorcraftHemisphere`, `fluids.Fluid`, `noise_control.DuctElement`), each record a union alias in a signature stands for (the six layers `materials.layered_absorber` takes as `Layer`, the sources `simulation.FDTD2D.add_source` takes as `AnySource`), and every record one of those holds (the `environment.WavelengthSpectrum` a `RollingStock` holds): `@dataclass(kw_only=True)`. A result one function hands whole to another is declared in `RECORD_AXIS_EXEMPT` of `scripts/check_parameter_units.py`, with its reason; a record that keeps a positional field goes in `RECORD_POSITIONAL_EXEMPT` with its reason, and only `io.Signal` does: `Signal(x, fs)` is the pair every function takes by position. A stale entry fails.

<a id="a19"></a>
### A19. Write a boolean by name, in the definition and at the call

**Why.** `bank.filter(x, True)` says nothing about which of five flags was thrown, and a flag inserted before it changes what the same call means without changing a character of it. matplotlib's own flag is written the same way: `ax.grid(visible=True)`.

**Do**

```python
import numpy as np
from phonometry import filters

y = filters.weighting_filter(np.zeros(4800), 48000, weighting="A", high_accuracy=True)
```

**Don't**

```py
filters.weighting_filter(x, fs, "A", True)
ax.grid(True)
```

**Enforced by:** `ruff FBT`, `tests/test_package_architecture.py::test_the_grid_flag_is_named_the_way_matplotlib_names_it`

<a id="a20"></a>
### A20. Add a `bool` overload beside the `Literal[True]` and `Literal[False]` overloads of a flag

**Why.** mypy does not split a `bool` argument into the two literals, so a caller whose flag came from a variable got "No overload variant matches" for a call that runs (`building.estimate_reverberation_index(weighted=)`, `metrology.sensitivity(narrowband=)`). `tests/static_typing` calls each overload set with a variable.

**Do**

```python
from collections.abc import Sequence
from typing import Literal, overload


@overload
def rating(levels: Sequence[float], *, weighted: Literal[True]) -> float: ...
@overload
def rating(levels: Sequence[float], *, weighted: Literal[False] = ...) -> list[float]: ...
@overload
def rating(levels: Sequence[float], *, weighted: bool) -> float | list[float]: ...
def rating(levels: Sequence[float], *, weighted: bool = False) -> float | list[float]:
    return sum(levels) if weighted else list(levels)
```

**Don't**

```py
@overload
def f(x: float, *, weighted: Literal[True]) -> A: ...
@overload
def f(x: float, *, weighted: Literal[False] = ...) -> B: ...
```

**Enforced by:** `tests/test_package_architecture.py::test_an_overload_on_a_true_or_false_literal_also_takes_a_bool`

**Exceptions.** A choice of more than two options is a `Literal` of strings, not a flag ([A21](#a21)).

<a id="a21"></a>
### A21. Type every fixed choice as a `Literal` of its options, never `str`, and its options tuple alike

**Why.** About 675 public choices were typed `str` (`language` in some 374 places, `engine` in 76, `weighting_filter(weighting)`, `OctaveFilterBank.filter(mode)`): a misspelled choice reached the function as a plain string, an editor offered nothing, and a `| str` beside a `Literal` hid the options from the type checker. Typed alike, `require_choice` hands the value back as the alias. A choice offered in more than one place reads the same in every one: the band set, the sound field and the weighting are its cases ([A22](#a22) to [A24](#a24)).

**Do**

```python
from typing import Literal

from phonometry._internal.validation import require_choice

Field = Literal["free", "diffuse", "pressure"]
FIELDS: tuple[Field, ...] = ("free", "diffuse", "pressure")
field = require_choice("free", "field", FIELDS)
```

**Don't**

```py
def response(field: Literal["free", "diffuse"] | str = "free"): ...
def response(field: str = "free"):
    if field not in ("free", "diffuse"): ...
```

**Enforced by:** `scripts/check_choice_literals.py`, `make choice-literals`, `CI: Check that every fixed public choice is typed Literal`, `tests/test_check_choice_literals.py::test_every_public_choice_of_the_package_is_a_literal`, `tests/test_check_choice_literals.py::test_every_vocabulary_offers_what_its_table_holds`, `tests/test_check_choice_literals.py::test_every_published_table_of_a_vocabulary_is_keyed_by_it`, `tests/test_choice_vocabulary.py::test_no_choice_offers_a_band_set_by_name`, `tests/test_choice_vocabulary.py::test_a_sound_field_is_free_diffuse_or_pressure`, `tests/test_choice_vocabulary.py::test_a_weighting_is_chosen_by_weighting`

**Exceptions.** The guard calls a public `str` parameter or field, alone or in a union (`str | float`, `Literal[...] | str`), a closed choice when the code treats it as one: it hands it to a shared validator (`require_choice`, `check_language`, `check_engine`), compares it with a set of strings, looks it up by key, documents two quoted options or more, writes it beside an `Enum` of the options (`RoadSurface | str`), or passes it on to a function that does one of those. It reads the text through `str(...)`, `.strip().lower()` and the locals bound from it, through a dict spread into a call and into a function the body imports, and a table handed on beside it (`_area_key(area_type, _ACTIVITY_LIMITS)`) closes the helper's `key not in table`. A collection of strings (`Sequence[str]`, `tuple[str, ...]`) and the keys of a mapping are read the same way, item by item through a loop, a comprehension, `.items()` and `.keys()`, and a set difference with the options (`set(sides) - _SIDES`) or a subset test (`<=`, `issubset`) closes them as a whole. A table held in a local (`table = _SIDES`), picked by a conditional expression, picked out of a table of tables (`_BUDGET_TABLES[field]`, read as the keys of all of them) or imported from another module of the package is the table written in place, and a frozen table the source builds with code (`MappingProxyType({**_rows(...)})`) is read off the imported module. A copy of the items made by a comprehension (`{str(d) for d in limits}`) holds the caller's strings, and an annotation is read through the module's type aliases, an imported one in the module that writes it, so a `str` hidden behind an alias (`_Sides = Iterable[str]`) is a `str` all the same. A string a caller writes below the top level (the columns of `Mapping[int, Mapping[str, float]]`, the items of `Sequence[Sequence[str]]`) is not followed through the code, so the guard calls it a choice as it stands: it takes its `Literal`, or `OPEN` says why it is open. A record field is followed out of `__post_init__` into the helper it is handed to, and a comparison of `<record>.<field>` with a string anywhere in the record's module closes it too. A string open by its nature (a label, a catalogue name, a clause a caller writes) stays `str` and goes in `OPEN` of `scripts/check_choice_literals.py`, keyed by (module, qualified name, parameter) with its reason; a stale entry fails. A catalogue row keeps its text cells `str`, as the catalogue contract requires. A published table read by a choice is keyed by the same `Literal` (`Mapping[CoefficientModel, ...]`, `tuple[Earphone, ...]`), at any depth: one typed `Mapping[str, ...]` whose keys are the options of a `Literal` of its package, or part of one of its own module, is the vocabulary written twice, and a caller indexing it with a misspelling meets a `KeyError` that `mypy` would have refused; a table whose keys match a vocabulary by coincidence goes in `OPEN_TABLES` with its reason. A record field the package fills only with fixed texts (`ReactiveSilencerResult.kind`) is a `Literal` too. A band set is the integer `Literal[1, 3]` ([A22](#a22)), not a string. `Literal[True]` and `Literal[False]` in `@overload` signatures are typing devices, not choices ([A20](#a20)).

<a id="a22"></a>
### A22. Choose a band set with `fraction`: 1 for octaves, 3 for one-third octaves

**Why.** The same choice was `band="third"`, `bands="third-octave"`, `band_type="third"` or `bandwidth="octave"` from one module to the next, and `fraction=True` was read as octaves.

**Do**

```python
from phonometry import filters

bank = filters.OctaveFilterBank(48000, fraction=3)
```

**Don't**

```py
def rating(levels, bands: str = "third-octave"): ...
```

**Enforced by:** `tests/test_choice_vocabulary.py::test_no_choice_offers_a_band_set_by_name`, `tests/test_choice_vocabulary.py::test_no_table_or_tuple_holds_a_band_set_word`, `tests/test_choice_vocabulary.py::test_a_band_fraction_is_one_or_three`, `tests/test_choice_vocabulary.py::test_anything_else_is_refused_as_a_band_set`

**Exceptions.** `speech.sii_procedure(method="one-third-octave")` names an ANSI S3.5 procedure and keeps its words; so does the ISO 3745 test-signal kind. A table read by band set is keyed by the integer. The share of energy a path carries is `energy_fraction`. The filter bank and `octave_filter` take any b of 1/b as `fraction: float`. Other kept spellings go in `_BAND_SET_EXEMPT` of `tests/test_choice_vocabulary.py`, with their reason.

<a id="a23"></a>
### A23. Name a sound field `"free"`, `"diffuse"` or `"pressure"`

**Why.** `hearing.reference_threshold` read `"free-field"`, the calibrations `"free_field"` and the loudness models `"free"` for the same thing.

**Do**

```python
from phonometry import hearing

hearing.reference_threshold(field="free")
```

**Don't**

```py
hearing.reference_threshold("free-field")
```

**Enforced by:** `tests/test_choice_vocabulary.py::test_a_sound_field_is_free_diffuse_or_pressure`, `tests/test_choice_vocabulary.py::test_a_retired_spelling_is_refused`

**Exceptions.** The quasi-free field of ISO 8253-2 5.4, the plane wave at normal incidence of the slit model (`"normal"`), and the eardrum of the Moore-Glasberg models. A catalogue column, a record field named in a message and an FDTD field quantity are not sound fields.

<a id="a24"></a>
### A24. Choose a frequency weighting with `weighting=`; an unweighted signal is `"Z"`

**Why.** The weighting was `curve=` on the filter, a `weighted=True` flag on the quasi-peak meter, `a_weighted=` on the program level and `None` on the signal levels.

**Do**

```python
import numpy as np
from phonometry import filters

y = filters.weighting_filter(np.zeros(4800), 48000, weighting="Z")
```

**Don't**

```py
quasi_peak_meter(x, fs, weighted=False)
weighting_filter(x, fs, curve="A")
ln_levels(x, fs, weighting=None)
```

**Enforced by:** `tests/test_choice_vocabulary.py::test_a_flat_weighting_is_z`, `tests/test_choice_vocabulary.py::test_a_weighting_is_chosen_by_weighting`

**Exceptions.** `emission.error_factor(a_weighted=)` reads the A-weighted row of ISO 9614-1 Table B.1 and `building.estimate_reverberation_index(weighted=)` the A/C column of ISO 10052 Table 4: table rows, not weightings. The generalized cross-correlation weighting of `TimeDelayResult` and the underwater weighting-function arrays are other meanings of the word.

<a id="a25"></a>
### A25. Take several values of one kind as one sequence, not as `*args`

**Why.** `combined_internal_levels(*levels)` summed one spectrum passed on its own over its bands instead of refusing it.

**Do**

```python
from phonometry import metrology

metrology.combined_standard_uncertainty([0.3, 0.4])
```

**Don't**

```py
def combined_stage_level(*levels: float) -> float: ...
```

**Enforced by:** review

**Exceptions.** `noise_control.cascade(*matrices)`, `vibration.combine_fault_lines(*results)` and `io.catalogue_schema(*row_types)` stay variadic.

<a id="a26"></a>
### A26. Make `axis` keyword-only

**Why.** `axis` was positional on `building.energy_average_level` and `room.directivity_energy_average` and keyword-only on `vibration.passage_average_level`.

**Do**

```python
import numpy as np


def energy_average(levels: np.ndarray, *, axis: int = 0) -> np.ndarray:
    return 10.0 * np.log10(np.mean(10.0 ** (levels / 10.0), axis=axis))
```

**Don't**

```py
def energy_average(levels, axis=0): ...
```

**Enforced by:** review

<a id="a27"></a>
### A27. Put the two ends of a range lower first

**Why.** The vibration tolerance limits came `(upper, lower)` while the filter and weighting masks came `(lower, upper)`, and `plant_steady_reading` took `max_level` before `min_level`; the swap is silent, because both arrays have the same shape and both numbers are levels.

**Do**

```python
from phonometry import emission, vibration

lower, upper = vibration.weighting_tolerance_percent("Wk", [16.0])
reading = emission.plant_steady_reading(min_level=78.0, max_level=82.0)
```

**Don't**

```py
upper, lower = weighting_tolerance_percent(name, frequencies)
def plant_steady_reading(max_level, min_level): ...
```

**Enforced by:** `tests/test_public_vocabulary.py::test_the_two_ends_of_a_range_come_lower_first`, `tests/test_public_vocabulary.py::test_the_range_order_rule_reads_a_list`, review

**Exceptions.** The test reads every public signature and record field list for a twin written upper first: `upper` before `lower`, `max` before `min`, `high` before `low`. An ordered set the source prints that is not a range keeps its printed order (`HMLRatingResult`: high, medium, low), declared in `_RANGE_ORDER_EXEMPT` of the test with its reason; a stale entry fails. A returned pair is review.

<a id="a28"></a>
### A28. Take `ax` first in `.plot()`, data first in `plot_` helpers, the rest by name

**Why.** Three results put a choice before the axes, so `result.plot(ax)` bound the axes to a frequency vector; six took `language` by position, so `plot(ax, "es")` worked on those six only; seventeen helpers took the axes after their data, so a forgotten dimension bound the axes to a length. The shapes are a result's `.plot(ax=None, *, language="en", **kwargs)` and a helper's `plot_x(<data>, *, ax=None, ..., language="en", **kwargs)`: `ax=None` creates a figure, a given `ax` is drawn into and returned, and styling keywords reach the primary artist over its default.

**Do**

```python
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from phonometry import filters

fig, ax = plt.subplots()
result = filters.octave_filter(np.random.default_rng(0).standard_normal(48000), fs=48000)
result.plot(ax, language="es")
```

**Don't**

```py
def plot(self, quantity, ax=None, language="en"): ...
def plot_plate_geometry(width_m, height_m, ax=None): ...
```

**Enforced by:** `tests/test_result_plots.py::test_every_plot_takes_ax_first_and_the_rest_by_name`, `tests/test_result_plots.py::test_every_plot_helper_takes_its_axes_and_language_by_name`, `tests/test_result_plots.py::test_single_axes_plots_accept_external_ax`, `tests/test_result_plots.py::test_every_plot_forwards_kwargs_to_primary_artist`

<a id="a29"></a>
### A29. Take a report's path first, then `metadata` and `language` by name

**Why.** The ISO 717 fiche set the pattern every fiche reuses: one shared, frozen, validated `ReportMetadata` record, not a loose set of keywords per fiche that each validates its own way. The shape is `.report(path, *, metadata=None, language="en", ...)`: every argument after the path is keyword-only.

**Do**

```python
from phonometry import ReportMetadata, building

wall = building.weighted_rating(
    [33.0, 36.0, 39.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0, 60.0, 63.0, 66.0, 69.0, 72.0, 75.0, 78.0]
)
wall.report("wall.pdf", metadata=ReportMetadata(client="Acme Labs", specimen="Wall A"), language="en")
```

**Don't**

```py
result.report("fiche.pdf", client="Acme Labs", specimen="Wall A")
```

**Enforced by:** review

<a id="a30"></a>
### A30. Never take a private-named argument in a public constructor

**Why.** `AnpAircraft(..., _database=db)` asked callers to pass an underscore name. The field is now the public `database`, left out of `repr()` and comparisons with `repr=False, compare=False`.

**Do**

```python
import dataclasses

from phonometry import aircraft

database = next(f for f in dataclasses.fields(aircraft.ANPAircraft) if f.name == "database")
database.repr, database.compare  # (False, False)
```

**Don't**

```py
ANPAircraft(..., _database=db)
```

**Enforced by:** review

<a id="a31"></a>
### A31. Annotate every parameter and return; use `Any` only where the set is open

**Why.** The test suite was the last unannotated corner, and an `Any` that is not forwarding keyword arguments promises nothing a reader can check.

**Do**

```python
from typing import Any


def label(template: str, **kwargs: Any) -> str:
    return template.format(**kwargs)
```

**Don't**

```py
def plot(ax, values):
    ...
```

**Enforced by:** `ruff ANN001`, `ruff ANN401`, `mypy`, `tests/test_package_architecture.py::test_no_published_field_is_typed_any`, `tests/test_package_architecture.py::test_no_published_field_is_typed_dict`

**Exceptions.** A forwarding `*args` or `**kwargs` may be `Any` (matplotlib's keyword surface is open). Elsewhere write `object` when the code never looks inside, or give the `noqa` its reason ([C4](docstrings.md#c4)). A field of a published record is never `Any` and never a `dict`, which a caller's narrower `dict` does not match: it says what it holds (`Mapping[...]` for a mapping, read-only as [A34](#a34) holds it); one that must stay `Any` goes in `ANY_FIELD_EXEMPT` of `tests/test_package_architecture.py` with its reason.

<a id="a32"></a>
### A32. Return several different quantities as a frozen record, never a tuple

**Why.** A tuple is read by position: `upper, lower = weighting_tolerance_percent(...)` still ran after the order changed and swapped the two arrays without an error.

**Do**

```python
from phonometry import filters

bands = filters.nominal_frequencies(1)
bands.frequencies, bands.lower_edges, bands.upper_edges
```

**Don't**

```py
freq, lower, upper, labels = filters.nominal_frequencies(1)
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_answers_several_quantities_as_records`, `tests/test_public_vocabulary.py::test_no_record_unpacks_like_a_tuple`

**Exceptions.** A tuple stays only for like items whose order nobody has to remember (the two ends of a range, lower first; the two biquad stages of BS.1770 in cascade order; the `*_named` collections), declared in `TUPLE_RETURN_EXEMPT` of `scripts/check_parameter_units.py`, keyed by module and qualified name, with the reason. The panels of one figure are like items too: a multi-panel `.plot()` without `ax` returns a tuple of its `Axes`, top first, in the order matplotlib's `subplots` lays them out ([A57](#a57)), and the check reads a tuple of axes as no bundle. A `NamedTuple` counts as a tuple, and a public record is never one: a record has no `__iter__`, so unpacking it raises `TypeError`.

<a id="a33"></a>
### A33. Give a result a `.plot()` that draws its guide figure where a figure says something

**Why.** The user should not write plotting code: `.plot()` draws exactly the figure the guide shows. The first figures of one group of guides plotted curves of the standard without `.plot()` and diverged from every guide before them.

**Do**

```python
from phonometry import materials

check = materials.check_base_plate_scattering([0.05] * 18)
check.plot()
```

**Don't**

```text
T30 returned as a bare array, and the guide's figure drawn by twenty lines
of matplotlib only the guide has.
```

**Enforced by:** review

**Exceptions.** A scalar verdict stays without a plot, and setup diagrams and infographics are schematics with none. A function that returns an array or a scalar today gains a result record with `.plot()` when a figure says something; its renderer lives in `src/phonometry/_plot/`.

<a id="a34"></a>
### A34. Publish every module-level table immutable, all the way down

**Why.** 109 tables were dicts and 31 arrays were writeable: `REFERENCE_CURVE[500] = 0` or `BAND_IMPORTANCE *= 2` changed the number for every caller in the process without a word, and three results handed `OCTAVE_BANDS` back by reference. A dict becomes a `types.MappingProxyType` (nested ones too), a list a tuple, an array goes through `phonometry._internal.frozen.read_only`, and a dataclass is `frozen=True` with no mutable container inside. A function that returns a bare array never hands a published one back by reference, and a record that owns its arrays takes it as it is, since it copies on construction ([X11](numerics.md#x11)).

**Do**

```python
import types

import numpy as np

from phonometry._internal.frozen import read_only

TOLERANCE_DB = types.MappingProxyType({"class 1": 1.1, "class 2": 1.4})
BANDS_HZ = read_only(np.array([125.0, 250.0, 500.0]))
```

**Don't**

```py
TOLERANCE_DB = {"class 1": 1.1, "class 2": 1.4}
BANDS_HZ = np.array([125.0, 250.0, 500.0])
```

**Enforced by:** `scripts/check_frozen_constants.py`, `make frozen-constants`, `CI: Every published table refuses writes`, `tests/test_package_architecture.py::test_a_record_holding_a_read_only_mapping_travels`, `tests/test_record_conversions.py::test_every_record_survives_pickle_and_deepcopy`

**Exceptions.** A mapping proxy does not pickle, deepcopy or serialize to JSON: never patch `copyreg`. A public record with mapping fields freezes them in `__post_init__`, whoever built it, and defines `__reduce__` returning `phonometry._internal.frozen.reduce_with_plain_rows(self)`, as `environment.RoadEmissionCoefficients` does, so that it travels to a process pool or a cache as plain dictionaries and wraps them again on arrival.

<a id="a35"></a>
### A35. Make a field the computation reads required, and refuse `None` for it by name

**Why.** Fields that defaulted to `None` so a hand-built result would still construct then failed later, in a report or a drawing, far from the call.

**Do**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Barrier:
    height_m: float

    def __post_init__(self) -> None:
        if self.height_m is None:
            msg = "'height_m' is required"
            raise TypeError(msg)
```

**Don't**

```py
@dataclass(frozen=True)
class Aperture:
    depth_m: float | None = None  # for compatibility
```

**Enforced by:** `tests/test_required_fields.py::test_a_required_field_refuses_none`, `tests/test_required_fields.py::test_an_optional_quantity_may_still_be_absent`

**Exceptions.** A field absent by meaning keeps `None`: a datasheet cell not printed, optional metadata, the tube diameter not supplied. The test pins a curated list of fields; it does not walk every record.

<a id="a36"></a>
### A36. Derive a value the stored fields determine as a read-only property

**Why.** `CeilingAttenuationResult.rounded` was passed in and could disagree with `measured`, and a regime held as a constructor field (`TappingForceResult.over_critical`, `HydrodynamicValveNoise.regime`) could disagree with the numbers it describes. Both became properties, as the verdicts are (decided 2026-10-07).

**Do**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class BandMargins:
    levels: tuple[float, ...]
    limits: tuple[float, ...]

    @property
    def margins(self) -> tuple[float, ...]:
        return tuple(limit - level for level, limit in zip(self.levels, self.limits, strict=True))
```

**Don't**

```py
over_critical: bool  # a field a caller can set against the numbers
```

**Enforced by:** `tests/test_derived_regimes.py`, `tests/test_printed_limits.py::test_no_verdict_takes_a_printed_limit_at_construction`, `tests/test_printed_limits.py::test_no_result_stores_a_verdict_flag`

<a id="a37"></a>
### A37. Keep an `io.Signal` a result holds as the object itself, by composition

**Why.** A result that flattened a Signal into a bare array lost its calibration and origin. A result that owns its arrays copies none of a Signal's: the Signal answers for its own samples, which stay writeable, and the record's docstring says the field holds a Signal when one came in (decided 2026-10-07).

**Do**

```python
import numpy as np
from phonometry import io, signals

x = io.Signal(np.sin(2 * np.pi * 1000.0 * np.arange(4800) / 48000), 48000)
isinstance(signals.envelope(x).signal, io.Signal)  # True
```

**Don't**

```py
signal: NDArray[np.float64]  # the Signal flattened to samples, its calibration lost
```

**Enforced by:** review

<a id="a38"></a>
### A38. Give one formula one function, and one computation one name

**Why.** The root-sum-square of independent uncertainties was written three times in three packages, and one conversion had two names in `materials`.

**Do**

```python
metrology.combined_standard_uncertainty([0.3, 0.4])
```

**Don't**

```py
building.combine_uncertainties(...)
environment.combined_standard_uncertainty(...)
```

**Enforced by:** review

<a id="a39"></a>
### A39. Return a judgment as a record that carries its reasons, never a bare `bool`

**Why.** `is_significant_change`, `limp_frame_applicable` and `perceptibly_different` returned a `bool` and `check_base_plate_scattering` a tuple, so the reasons behind the answer were lost to the caller.

**Do**

```python
from phonometry import materials

check = materials.check_base_plate_scattering([0.05] * 18)
check.passes, check.margins
```

**Don't**

```py
def limp_frame_applicable(k_c: float) -> bool: ...
```

**Enforced by:** `tests/test_verdict_shape.py::test_every_judging_verb_returns_a_record`, `tests/test_verdict_shape.py::test_every_judging_method_returns_a_record`, `tests/test_verdict_shape.py::test_every_exempt_method_still_exists`, `tests/test_verdict_shape.py::test_every_regime_predicate_is_still_published`

**Exceptions.** A `check_` whose only answer is an advisory warning returns `None`. A regime predicate keeps its `bool` ([N9](naming.md#n9)).

<a id="a40"></a>
### A40. Spell a pass-or-fail verdict's overall flag `passes`

**Why.** Verdicts said `complies`, `acceptable`, `satisfied`, `all_satisfied` or `applicable` for the same answer.

**Do**

```python
from phonometry import building

verdict = building.check_lining_curing(28.0, 2.0)
verdict.passes
```

**Don't**

```py
check.complies
check.all_satisfied
```

**Enforced by:** `tests/test_verdict_shape.py::test_the_overall_flag_is_spelled_passes`, `tests/test_verdict_shape.py::test_every_kept_flag_still_exists`, `tests/test_public_vocabulary.py::test_one_concept_is_spelled_one_way`

**Exceptions.** A flag that answers something other than pass or fail keeps its name in `KEPT_FLAGS` of `tests/test_verdict_shape.py`, keyed by class and flag, with its reason (`within_guideline` of DIN 4150-3, `significant`, `conforms` of IEC 61400-11). A verdict that grades or classifies answers by that attribute and has no `passes` (`overall_class` of the filter verifications, `category`). A per-band mask is `within_limit` or `within_tolerance`.

<a id="a41"></a>
### A41. Make a verdict refuse a truth value, naming the attribute to read

**Why.** A dataclass is always true, so `if result:` would pass every failure. `__bool__` raises `TypeError`, saying the record has no truth value and naming the attribute to read: `.passes` for a pass-or-fail verdict, the grade otherwise (`.overall_class`).

**Do**

```python
import pytest

with pytest.raises(TypeError, match=r"no truth value; read its '\.passes'"):
    bool(verdict)
```

**Don't**

```py
if verdict:  # TypeError: read verdict.passes
    ...
```

**Enforced by:** `tests/test_verdict_shape.py::test_every_verdict_refuses_a_truth_value`, `tests/test_verdict_shape.py::test_the_bool_of_every_verdict_raises`, `tests/test_verdict_shape.py::test_a_built_verdict_refuses_a_truth_value`, `tests/test_verdict_shape.py::test_a_real_verdict_refuses_a_truth_value`

<a id="a42"></a>
### A42. Raise `TypeError` for a wrong type and `ValueError` for a right type's wrong value

**Why.** Seventy-six refusals tested a type and raised `ValueError`, and thirty-two handlers turned a `TypeError` into a `ValueError` on the way out, so a caller could not catch `TypeError` to tell a programming error from a bad measurement. A wrong type is a text, a `bool` or `None` for a number, an array for one number, a complex for a real, an array of the wrong dtype, a number where a pair or a sequence belongs, an object that is not the record the function takes, or a choice that is not a text. A type question joined to a value question with `or` is split, and a handler never re-raises a `TypeError` as a `ValueError`.

**Do**

```python
from phonometry import room

surfaces = [(120.0, 0.25)]
with pytest.raises(TypeError, match="'volume' must be one number, not an array"):
    room.sabine_reverberation_time([200.0, 300.0], surfaces)
with pytest.raises(ValueError, match="'volume' must be positive"):
    room.sabine_reverberation_time(-200.0, surfaces)
```

**Don't**

```py
if not isinstance(n, int) or n < 1:
    raise ValueError("n must be a positive integer")
```

**Enforced by:** `tests/test_error_kinds.py::test_a_wrong_type_raises_type_error`, `tests/test_error_kinds.py::test_every_exemption_names_a_function_that_exists`

**Exceptions.** Data the library reads refuses with `ValueError` ([A46](#a46)); those helpers are keyed in `EXEMPT` of `tests/test_error_kinds.py`, with their reason.

<a id="a43"></a>
### A43. Refuse an array or a text where one number belongs with a `TypeError` naming it

**Why.** A one-element array used to pass as its element, a longer one raised numpy's anonymous "truth value is ambiguous" or broadcast into an answer of the wrong shape, and a text was parsed into a number by one guard and refused as a value by the next. `float()` and `np.asarray(..., dtype=float)` parse text, but a guard is not a parser: `"94.0"` and `"fifty"` are refused alike.

**Do**

```python
with pytest.raises(TypeError, match="'volume' must be one number, not a text"):
    room.sabine_reverberation_time("200", surfaces)
```

**Don't**

```py
volume = float(volume)  # accepts "200"
```

**Enforced by:** `tests/test_scalar_guards.py::test_every_public_scalar_parameter_refuses_an_array_or_a_text_by_name`, `tests/test_scalar_guards.py::test_a_text_where_a_number_belongs_is_one_class_everywhere`, `tests/test_scalar_guards.py::test_a_field_of_text_is_a_type_error`

**Exceptions.** A sidecar or a catalogue cell is data and refuses with `ValueError` ([A46](#a46)).

<a id="a44"></a>
### A44. Raise `KeyError` for a missing name or key, `ValueError` for an uncovered value

**Why.** A lookup that missed raised `KeyError` in one result and `ValueError` in the next for the same kind of question. A key behaves as a `dict` key does (`RegulationLimits["noon"]`, `verdict.requirement("no_such")`); a frequency, wavelength or class outside what the result covers or the standard defines is a bad value (`TrackDecayRate.rate_at(400.0)`, `binding_margin(requirement, 0)`).

**Do**

```python
from phonometry import environment

limits = environment.activity_limits("a")
with pytest.raises(KeyError, match="RegulationLimits holds the periods"):
    limits["noon"]
```

**Don't**

```py
def __getitem__(self, period):
    raise ValueError(f"unknown period {period!r}")
```

**Enforced by:** review

**Exceptions.** A plot selector is a choice and raises `ValueError` ([A45](#a45)); a printed catalogue cell without a number raises `ValueError` naming what the page holds.

<a id="a45"></a>
### A45. Refuse an unknown choice with `ValueError`, and a choice that is not text with `TypeError`, checked as written

**Why.** A choice names an option whatever it looks up inside, so a miss is a bad value; a number where a name belongs is the wrong type, as `require_choice` has it. The check reads the text as the caller wrote it: a `Literal` lists one spelling of each option, and a body that folds the case, strips the spaces, swaps separators, maps an alias of its own or makes a text of any value with `str()` before it checks took `"a"` for `"A"`, `" fast "` for `"fast"` and `2023` for `"2023"` at run time while a type checker refused all three. 198 public parameters and record fields did, the core filters among them (`WeightingFilter(48000, "a")`, `time_weighting(x, fs, mode="FAST")`), twelve of them through a method of their own class or of the database a record holds. A check as written holds the text to the `Literal` only when its options are the ones the `Literal` lists: `require_choice(quantity, "quantity", (*_SINGLE, *_ALIASES))` and `if mode not in ("fast", "slow", "quick"): raise` take a spelling of their own as surely as a fold does, and so does a subset or leftover test of a collection against a wider set.

**Do**

```python
options = ("day", "evening", "night")
with pytest.raises(ValueError, match="'period' must be one of "):
    require_choice("noon", "period", options)
with pytest.raises(TypeError, match="'period' must be one of .*, a text"):
    require_choice(5, "period", options)
with pytest.raises(ValueError, match="'period' must be one of "):
    require_choice("Day", "period", options)
```

**Don't**

```py
if period not in PERIODS:
    raise KeyError(period)
key = period.strip().lower()
year = require_choice(str(edition), "edition", EDITIONS)
row = require_choice(quantity, "quantity", (*_SINGLE, *_ALIASES))
if mode not in ("fast", "slow", "quick"):
    raise ValueError(mode)
```

**Enforced by:** `scripts/check_choice_literals.py`, `make choice-literals`, `tests/test_check_choice_literals.py::test_every_literal_choice_is_checked_as_written`, `tests/test_check_choice_literals.py::test_every_literal_choice_is_checked_on_every_path`, `tests/test_choice_vocabulary.py::test_a_retired_spelling_is_refused`

The check runs on every path: where the function starts, or in the `__post_init__` of a record a caller builds, so the record refuses an unknown choice when it is built and not when something reads it. A choice checked only beside another argument, behind a test of its text, or with `if text not in OPTIONS` (a `ValueError` for a number) fails, and so does one never checked: `if mode == "fast": require_choice(...)` and `if mode == "typo": return` before the check send the other texts, a misspelling among them, past it. A test of its form (`text is None`, `isinstance(text, str)`, the emptiness of a collection) runs the check whenever there is a text to check, and a test that holds only for an option the `Literal` lists (`if method == "vdi2081": return ...` before `require_choice(method, "method", ("bies", "long"))`) lets no misspelling past either. Each key of a mapping and each item of a sequence is checked as written, one by one, through a copy of them too (`tuple(dict.fromkeys(rows))`, `dict(levels.items())`, `{side: float(v) for side, v in limits.items()}`). A filter of a comprehension is a test of each item, and drops the ones it fails for before any check sees them: `{side: float(v) for side, v in limits.items() if side in SIDES}` hands on only the keys it keeps, and a check in the element of `[require_choice(s, "sides", SIDES) for s in sides if s != "both"]` runs only for the items the filter keeps, so both leave a misspelling unchecked; a filter that fails only for an option the `Literal` lists (`if side != "top"`) drops none.

**Exceptions.** A spelling the `Literal` lists on purpose (`"docente"` for `"educational"`, `"dnt_w"` for `"r_w"`) is mapped to its option once the text is checked as written, and a clean-up after the check accepts nothing more. Text the library reads from a file, such as the operation column of an ANP database or a flap identifier a procedure spells, is data, not a caller's choice, and is folded as the file needs ([A46](#a46)). A plot selector (`FilterComplianceResult.plot(requirement=...)`, `BinauralIndicators.plot(parameter=...)`) chooses what to draw, so an unknown name is a `ValueError`; the same name read back from the result (`binding_margin(requirement, ...)`) is a key, and its miss is a `KeyError` ([A44](#a44)). A field the catalogue contract reads (the `kind` of a `Provenance`) is refused, of any type, with the `CatalogueError` that names the field, and goes in `UNCHECKED` of `scripts/check_choice_literals.py` with its reason; a stale entry fails.

<a id="a46"></a>
### A46. Refuse malformed data the library reads with `ValueError` naming the file

**Why.** The file is malformed, not the call: a sidecar whose factor is a text, or a catalogue cell holding a word where a number goes, is a bad value of the data.

**Do**

```text
raise CatalogueError(f"{path}: row 'mineral wool': 'thickness_mm' holds 'n/a', not a number")  # a ValueError
```

**Don't**

```text
raise TypeError("thickness_mm must be a number")  # while parsing a user's file
```

**Enforced by:** review

**Exceptions.** `CatalogueError` is a `ValueError` on purpose. The sidecar payload parser and the checks of `CalibrationSidecar` are the named exemptions of the type rule's test ([A42](#a42)).

<a id="a47"></a>
### A47. Name in an error message the parameter the caller passed

**Why.** When `frequency` became `frequencies`, a caller told that "frequency" must be positive looked for a parameter the function no longer had. The check follows each parameter through the functions of its module it is passed to, and reads the defaulted name argument of a shared helper too (`resolve_samples(x, name="x")`).

**Do**

```python
def total(frequencies: Sequence[float]) -> float:
    if not frequencies:
        msg = "'frequencies' must hold at least one band"
        raise ValueError(msg)
    return sum(frequencies)
```

**Don't**

```py
def total(frequencies):
    if not frequencies:
        raise ValueError("'frequency' must hold at least one band")
```

**Enforced by:** `tests/test_public_vocabulary.py::test_a_message_names_the_parameter_the_caller_passed`, review

**Exceptions.** The test catches a message that calls a parameter by a retired spelling of the vocabulary tables, in a module whose path is public; any other wrong name is review. The shared helpers in `_internal/validation.py`, `_internal/utils.py` and `io/_resolve.py` name a value by their `name` argument, which has no default where a default would name a parameter the caller does not have (`require_1d_signal(values, name)`).

<a id="a48"></a>
### A48. Put an error message in a variable before raising it

**Why.** A traceback then shows `raise ValueError(msg)` and the text once, not a message split across the frame.

**Do**

```python
import math
from collections.abc import Sequence


def require_finite_levels(levels: Sequence[float]) -> list[float]:
    if not all(math.isfinite(level) for level in levels):
        msg = "'levels' must be finite"
        raise ValueError(msg)
    return list(levels)
```

**Don't**

```py
raise ValueError("'levels' must be finite")
```

**Enforced by:** `ruff EM`

<a id="a49"></a>
### A49. Derive every warning from `PhonometryWarning` and publish it from its domain

**Why.** `HVACWarning` fired and `phonometry.noise_control` did not publish it, so a caller could not write a filter for it; `RoadDeviceWarning` derived from `UserWarning` alone, so `simplefilter("error", PhonometryWarning)` let it through. Each topic class is still a `UserWarning`, so a filter on that class still matches, and one filter on `PhonometryWarning` reaches every advisory. The class is named `<Topic>Warning` ([N6](naming.md#n6)).

**Do**

```python
from phonometry import PhonometryWarning


class DuctWarning(PhonometryWarning):
    """A duct calculation outside its validated range."""


__all__ = ["DuctWarning"]
```

**Don't**

```py
class RoadDeviceWarning(UserWarning): ...
```

**Enforced by:** `tests/test_package_architecture.py::test_every_warning_a_package_can_raise_is_published`, `tests/test_package_architecture.py::test_every_published_warning_is_a_phonometry_warning`

<a id="a50"></a>
### A50. Warn with the topic's published class, never `UserWarning` or the bare root

**Why.** Seven calls warned as `UserWarning` (two naming no category) and five as the bare root, so none of them could be silenced or escalated without every other advisory too.

**Do**

```python
import warnings

from phonometry import filters


def warn_low_rate(fs: int) -> None:
    if fs < 8000:
        warnings.warn(f"Low sampling rate: {fs} Hz", filters.FilterBankWarning, stacklevel=2)
```

**Don't**

```py
warnings.warn("low sampling rate")
warnings.warn(msg, UserWarning)
```

**Enforced by:** `tests/test_package_architecture.py::test_every_warning_names_a_published_topic`

**Exceptions.** A helper that warns on behalf of several topics takes the category as a parameter typed `type[PhonometryWarning]`.

<a id="a51"></a>
### A51. Silence inside the library only the warning topic you mean

**Why.** The railway passage bank silenced `UserWarning` around the filter bank it builds, and every other advisory the bank raised inside that block went unseen.

**Do**

```python
from phonometry import fluids

with warnings.catch_warnings():
    warnings.simplefilter("ignore", fluids.FluidAssumptionWarning)
    air = fluids.air(temperature_c=20.0)
```

**Don't**

```py
with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)
```

**Enforced by:** `tests/test_package_architecture.py::test_a_warning_filter_in_the_library_names_its_topic`

**Exceptions.** A filter on a third-party warning names that library's class (`src/phonometry/io/_wav.py` filters scipy's `WavFileWarning`); `Warning`, `UserWarning`, `PhonometryWarning` or no category are refused.

<a id="a52"></a>
### A52. Speak to the caller through warnings, never `print`

**Why.** A library that prints writes into its caller's output; an advisory is a warning a caller can filter.

**Do**

```python
def warn_long_duct(length_m: float) -> None:
    if length_m > 10.0:
        warnings.warn(f"a {length_m} m duct is past the validated range", DuctWarning, stacklevel=2)
```

**Don't**

```py
print(f"warning: a {length_m} m duct is past the validated range")
```

**Enforced by:** `ruff T20`

**Exceptions.** `scripts/` and `tests/` may print.

<a id="a53"></a>
### A53. Refuse a value only where the standard bounds it or physics forbids it

**Why.** A guard drawn around "laboratory temperatures" refuses 150 °C exhaust gas and 150 K cryogenics, and still cannot catch the caller who typed kelvin inside the range: false safety that costs legitimate inputs. The maintainer settled it on 2026-09-03: a range is limited only where the standard limits it, and otherwise only to the physically possible values, so the bound is absolute zero, never a laboratory range. The unit hazard itself is closed by naming (the unit in the name, keyword-only), never by magnitude.

**Do**

```python
from phonometry._internal.validation import require_above_absolute_zero

exhaust_temperature_c = require_above_absolute_zero(150.0, "temperature_c")
```

**Don't**

```py
if not -20.0 <= temperature_c <= 50.0:
    raise ValueError("'temperature_c' must be a laboratory temperature.")
```

**Enforced by:** review

**Exceptions.** A range the clause prints is reflected, as an error or a warning as the clause reads. The physical limits are the only unconditional errors: T ≤ 0 K, t ≤ −273.15 °C, a non-positive pressure.

<a id="a54"></a>
### A54. Report progress to a `phonometry.` logger at INFO or DEBUG; never configure logging

**Why.** A run on a node can last an hour, and a caller wants to see it move. A library that prints writes into its caller's output (A52), and a library that configures logging rewrites its caller's. The standard logger is silent until the caller asks: nothing below WARNING reaches standard error by default, so messages at INFO and DEBUG cost the caller nothing. An advisory is a warning with its topic class (A50), never a log line at WARNING, which would print.

**Do**

```python
import logging

_LOG = logging.getLogger("phonometry.simulation")


def report(label: str, done: int, total: int) -> None:
    _LOG.info("%s: step %d of %d", label, done, total)


report("the NAS", 3, 10)
```

**Don't**

```py
logging.basicConfig(level=logging.INFO)  # the caller's logging, not the library's
_LOG.warning("the node is slow")  # an advisory is a warning, and WARNING prints
```

**Enforced by:** `tests/test_package_architecture.py::test_the_library_logs_quietly_to_loggers_of_its_own`, `tests/test_package_architecture.py::test_the_logging_rule_reads_a_loud_logger`, `tests/test_package_architecture.py::test_the_logging_rule_reads_every_spelling_of_a_logger`, `tests/test_package_architecture.py::test_the_logging_rule_reads_every_way_of_configuring`, `tests/test_package_architecture.py::test_the_logging_rule_follows_a_logger_from_module_to_module`

**Exceptions.** None. The caller turns the messages on, with `logging.basicConfig(level=logging.INFO)` or a handler on `phonometry.simulation`; the encoder a video is written with is logged on `phonometry.io`.

<a id="a55"></a>
### A55. Give every parameter of a function that runs on a node, and every field of the records it takes, a form that travels as data

**Why.** A run sent to a node carries the function's name and its arguments, never code: numbers, texts, arrays, and the library's own records field by field, the run record first among them. A parameter or a field whose value cannot travel works here and fails the day someone first sends it to a node, and a callable would have to travel as code, which the remote route refuses by design. A waveform is the one callable that travels: the `.value` of a library source, which the node rebuilds from its record.

**Do**

```python
from phonometry import simulation

pulse = simulation.GaussianPulse(ix=0, iy=0, half_width_s=1e-5)
source = simulation.ExplosionSource(ix=5, iy=5, waveform=pulse.value)  # rebuilt on the node from the record
```

**Don't**

```py
source = simulation.ExplosionSource(ix=5, iy=5, waveform=lambda t: 0.0)  # code: refused on the way to a node
```

**Enforced by:** `tests/simulation/test_remote_wire.py::test_every_parameter_of_a_remote_function_travels`, `tests/simulation/test_remote_wire.py::test_every_field_of_a_run_travels`, `tests/simulation/test_remote_wire.py::test_the_guard_names_every_function_a_node_runs`, `tests/simulation/test_remote_simulation.py::test_the_remote_route_sends_every_parameter`, `tests/simulation/test_video_remote.py::test_the_remote_route_sends_every_parameter`, `CI: Remote simulation on a localhost node`

**Exceptions.** `compute`, which says where the run goes and travels as the job's placement; and `path`, the file a video writer writes on this machine: it stays on the client, and only its container travels, as `container` (the node encodes into a scratch file of its own and the video's bytes come back to be written there). A new field of `FDTDRun`, `ElasticRun` or the boundaries records they hold (`FDTDBoundaries`, `ElasticBoundaries`) gets a value in the tables of `tests/simulation/test_remote_wire.py`, away from its default where the run takes another, and a new function a node runs gets a row in `_EVERY_PARAMETER`, or the tests above fail.

<a id="a56"></a>
### A56. Run a program the library does not ship by its full path, check everything before it starts, and fake it in tests

**Why.** phonometry runs two programs it does not ship: ffmpeg, to write videos, and ssh, to reach a node. A bad argument found after the program started leaves a half-written file or a node busy for nothing; a program found on `PATH` by a bare name in one place and by a setting in another runs a different binary from the one the user configured; and a test that needs the real program either skips on every runner that lacks it or never runs at all. Both programs keep two more rules on Windows. Windows looks a bare name up in the working directory before `PATH`, so a file of that name left in a notebook's folder would run in place of the program the user installed: `find_ffmpeg` and `ssh_program` pass over it to the one on `PATH`, which runs by its full path, and refuse a program found only there, `find_ffmpeg` with `FFmpegNotFoundError` and `ssh_program` with a `FileNotFoundError` that the remote route raises as `ComputeRemoteError`. A working directory that `PATH` itself lists is the user's own choice, and so is an ffmpeg named by its full path in `rcParams["animation.ffmpeg_path"]`. And a console program started from a process with no console (`pythonw`, or a notebook kernel a GUI front end started) opens a window of its own, so ffmpeg starts with `NO_WINDOW`, as the example shows, and ssh with `CREATE_NO_WINDOW` beside the process group of its own that lets an interrupt reach this process, which stops ssh.

**Do**

```python
import subprocess

from phonometry import io
from phonometry.io._video import video_request
from phonometry.io._video_encoders import NO_WINDOW, find_ffmpeg

# The setting the user knows, rcParams["animation.ffmpeg_path"], resolved once to a full path
# (on Windows the one on PATH, past an ffmpeg in the working directory).
ffmpeg = find_ffmpeg()
# The records checked themselves when built; the path is checked here, before the program starts.
request = video_request("wave.webm", io.VideoOptions(quality="small"))
done = subprocess.run(  # nosec B603 - an argument list to the full path find_ffmpeg resolved; no shell
    [ffmpeg, "-hide_banner", "-version"],
    capture_output=True,
    timeout=60.0,
    check=False,
    creationflags=NO_WINDOW,  # no console window on Windows
)
reason = done.stderr.decode(errors="replace")[-400:]  # the last of its standard error, for the message
```

**Don't**

```py
subprocess.run(f"ffmpeg -i - {output}", shell=True)
```

Keep the last lines of the program's standard error for the error message. A new program named by a bare name goes through `past_the_working_directory` of `phonometry._internal.programs`, as `find_ffmpeg` and `ssh_program` do, and refuses, with an error of its own, a program it gives `None` for; `tests/test_internal_programs.py` tests the rule once and holds both lookups to it. In tests, a stand-in written in Python takes the program's place on every system. `tests/fake_ffmpeg.py` writes a launcher (a shell script, or a `.cmd` file on Windows) that runs it with the test's interpreter, points `rcParams["animation.ffmpeg_path"]` at it and puts its directory first on `PATH`, and is steered by a JSON file the test writes and rewrites (the encoders it lists, the ones that work, when it dies). `tests/simulation/fake_ssh.py` is run through `command._SSH_PROGRAM`, which the `node` fixture points at it (a batch file on `PATH` could not carry the remote command intact on Windows), and is steered by `FAKE_SSH_MODE` (a refused key, a login banner, a hang, bytes that are no frame) and `FAKE_SSH_LOG` (a line per start). The Windows lookup is tested on every system: `tests/windows_lookup.py` answers as `shutil.which` does on Windows, and a test that puts it in the place of `shutil.which` and sets `sys.platform` to `"win32"` plants the program in the working directory and on `PATH`. A test that needs the real program skips without it, with a reason that names the CI job that runs it there. Bandit reports every call as `B603`, and its `nosec` gives the reason ([C4](docstrings.md#c4)).

**Enforced by:** `CI: Videos encode with a real ffmpeg`, `CI: Remote simulation on a localhost node`, `tests/io/test_video_encoders.py`, `tests/simulation/test_remote_command.py`, `tests/test_internal_programs.py`, `bandit`

<a id="a57"></a>
### A57. Overload a return whose type one argument decides

**Why.** Twenty-seven multi-panel `.plot()` methods and `room.plot_excitation` drew one panel on the axes a caller handed them and returned it, and without one made a column of panels and returned an ndarray of them, annotated `Axes | ndarray` and nothing more: a typed caller narrowed a value the call had already fixed, and `result.plot(ax=ax).set_title(...)` was a type error. Seven public plots that draw on a polar axes returned it typed plain `Axes`. Each case now has an overload head that says what it returns: a tuple of exactly its axes without `ax`, the `Axes` it was handed with one, and `PolarAxes` where the axes is polar, always or for the `view` or `quantity` that chooses the polar panel. The union stays on the implementation, which no caller sees. In the package the tuples are written `TwoPanels` and `ThreePanels`, the aliases of `phonometry._internal.types` ([A5](#a5)), which the API reference prints as `tuple[Axes, Axes]` and `tuple[Axes, Axes, Axes]`.

A function of a number or an array of them is the same case. Eighty-four returned `float | ndarray`, or a grade or an array of grades, with no overload, and a zero-dimensional array came back as a `float`, so neither the type nor the rule followed what the caller handed over. They follow it now, an array in and an array out: a `float` only when every argument that decides the shape is a number, an array as soon as one is a sequence or an array, a zero-dimensional one included, which `as_float_or_array(values, like=(...))` of `phonometry._internal.types` applies. The heads say it in three forms, and one more for each further argument that decides: a number, a sequence or an array, and a last head for what a type checker cannot shape, an `ArrayLike` or a nested list, which returns the union. The heads return the value alone and the array alone between them, since a type checker reads only the heads; where the last one stands is mypy's to check (`overload-cannot-match`), and a function with two routes to its input, `room.critical_distance`, has one for each. Each head takes its argument as a type parameter bounded by the form rather than the form itself: mypy reads an argument whose type holds an explicit `Any` (a bare `np.ndarray`, the `dtype[Any]` that `np.array(...)` returns, a shape written `tuple[Any, ...]`) as matching every head it fits, and answers `Any` unless those heads agree on its type, which a type parameter makes them do. `room.room_constant(100.0, np.array([0.2, 0.3]))` reads as `NDArray[np.float64]` with type parameters, and as `Any` with heads written with the plain forms.

**Do**

```python
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from matplotlib.axes import Axes


class TwoPanelResult:
    @overload
    def plot(self, ax: None = None) -> "tuple[Axes, Axes]": ...

    @overload
    def plot(self, ax: "Axes") -> "Axes": ...

    def plot(self, ax: "Axes | None" = None) -> "Axes | tuple[Axes, Axes]":
        import matplotlib.pyplot as plt

        if ax is not None:
            return ax
        _fig, (top, bottom) = plt.subplots(2, 1)
        return top, bottom


top, bottom = TwoPanelResult().plot()
```

```python
from typing import overload

import numpy as np
from numpy.typing import ArrayLike, NDArray

from phonometry._internal.types import RealScalar, RealValues, as_float_or_array


@overload
def doubled[S: RealScalar](level: S) -> float: ...


@overload
def doubled[V: RealValues](level: V) -> NDArray[np.float64]: ...


@overload
def doubled[A: ArrayLike](level: A) -> float | NDArray[np.float64]: ...


def doubled(level: ArrayLike) -> float | NDArray[np.float64]:
    return as_float_or_array(2.0 * np.asarray(level, dtype=np.float64), like=(level,))


doubled(3.0), doubled([3.0, 4.0]), doubled(np.array(3.0))
```

**Don't**

```py
def plot(self, ax: Axes | None = None) -> Axes | np.ndarray:  # the caller narrows what ax decided
    ...
def doubled(level: ArrayLike) -> float | np.ndarray:  # and narrows what it handed over
    ...
```

**Enforced by:** `scripts/check_return_overloads.py`, `make return-overloads`, `CI: Every return an argument decides is overloaded on it`, `tests/test_check_return_overloads.py::test_the_package_keeps_the_rule`, `tests/test_result_plots.py::test_a_plot_returns_what_its_signature_promises`, `tests/test_result_plots.py::test_every_decided_plot_has_a_built_result`, `tests/test_scalar_or_array_returns.py::test_every_function_of_a_number_or_an_array_has_a_case`

**Exceptions.** A return the data decide rather than an argument keeps its union on that one head, with its reason in `EXEMPT` of `scripts/check_return_overloads.py`, keyed by the parameters that tell the head from its siblings (`ZwickerLoudness.plot (overload ax: None)`), so that the other heads are still held to the rule: `ZwickerLoudness.plot` without `ax` draws a second panel only for a time-varying result. A private helper that takes the projection from a table row it is handed rather than from an argument of its own is exempt the same way. Of the functions of a number or an array, the exempt ones keep the union with their reason: one that reduces an axis (`signals.leq`, `room.directivity_energy_average`, and `signals.ln_levels`, whose dictionary holds such a level for each percentile), where the rank of the input decides whether one number is left, which `as_float_if_reduced` applies; one whose shape comes from values inside a tuple or a record (`room.sabine_reverberation_time` and its surfaces); a property, which has no argument to overload on; and one where four or more arguments broadcast (`room.steady_state_spl`), whose heads would number more than the union says. Each of them still applies the rule at run time.

<a id="a58"></a>
### A58. Annotate a parameter with every type its validation accepts

**Why.** 559 public parameters of 313 functions and methods were annotated narrower than what their body takes. 534 handed the value, or each of its items, to `np.asarray`, or to a helper that does, so a tuple, a `list[int]`, an integer array or a nested `[channels, samples]` list ran; and each was annotated `list[float]`, `NDArray[np.float64]`, `Sequence[float] | np.ndarray` or a sequence of fixed pairs, so a typed caller's code that ran was a type error. The other 25 held a `list` or a `dict` that their body only reads. `list` adds a trap of its own: it is invariant, so a `list[int]` is not a `list[float]`, and the 2-D list that `broadcast.true_peak_level` documents for a multichannel signal was refused by the `SignalInput` alias. A parameter the body converts takes `ArrayLike`, numpy's type for what `np.asarray` converts (`Signal | ArrayLike` where a Signal is taken too, the `SignalInput` alias of `io/_resolve.py`); a sequence of records or texts takes `Sequence[...]`, and a mapping `Mapping[...]`, which say what the body reads and take a tuple or a read-only mapping as well.

The same holds for one number. 231 counts, band fractions and flags of public functions and records were annotated `int`, `BandFraction` or `bool` while their validator (`require_count`, `require_band_fraction`, an `isinstance` check) took the `np.int64` that `np.argmax` or a shape gives and the `np.True_` of a comparison, so a typed caller converted a value the function would have taken; they take `int | np.integer[Any]`, `BandFraction | np.integer[Any]` and `bool | np.bool_`, and so do 43 more counts, orders and indices that a scalar check read as one number, which `require_count` now reads as a whole one. A mapping is invariant in its key: the 11 mappings of band values that were `Mapping[float, float]` refused the `{125: 40.0}` a caller writes for a band spectrum, so a mapping keyed by `float` stands beside one keyed by `int` (`BandMapping`). And a quantity of the vocabulary keeps one family of numbers across the API: 40 sample rates that run at any positive value were `int` while 149 were `float`, so the `float` rate `signals.resample_signal` returns, or a `Signal` holds, was refused by the next function; every such rate is a `float`.

**Do**

```python
from collections.abc import Mapping, Sequence

import numpy as np
from numpy.typing import ArrayLike


def band_mean(levels: ArrayLike) -> float:
    return float(np.mean(np.asarray(levels, dtype=np.float64)))


def section_area(section: Mapping[str, float]) -> float:
    return section["width"] * section["height"]


def surface_names(surfaces: Sequence[str]) -> str:
    return ", ".join(surfaces)


band_mean([60, 62]), band_mean((60.0, 61.5)), band_mean(np.array([60, 62]))
```

```python
from collections.abc import Mapping
from typing import Any

import numpy as np


def band_count(n_bands: int | np.integer[Any]) -> int:
    return int(n_bands)


def rating(by_band: Mapping[int, float] | Mapping[float, float]) -> float:
    return max(by_band.values())


band_count(np.argmax([0.0, 3.0, 1.0])), rating({125: 40.0, 250: 42.0})
```

**Don't**

```py
def band_mean(levels: list[float]) -> float:  # refuses a list[int], a tuple and an array
    ...
def band_mean(levels: NDArray[np.float64]) -> float:  # refuses the list np.asarray takes
    ...
def section_area(section: dict[str, float]) -> float:  # refuses a read-only mapping
    ...
def band_count(n_bands: int) -> int:  # refuses the np.int64 np.argmax returns
    return require_count(n_bands, "n_bands")
def rating(by_band: Mapping[float, float]) -> float:  # refuses a dict[int, float]
    ...
def laeq(x: ArrayLike, fs: int) -> float:  # refuses the float rate a Signal holds
    ...
```

**Enforced by:** `scripts/check_parameter_annotations.py`, `make parameter-annotations`, `CI: Every public parameter admits what its body converts`, `tests/test_check_parameter_annotations.py::test_the_package_keeps_the_rule`, `tests/test_record_constructors.py::test_every_record_says_what_its_constructor_takes`, `scripts/check_array_aliasing.py`, `tests/test_record_conversions.py::test_a_list_given_to_a_converted_field_is_held_converted`, `mypy`

**Exceptions.** The rule reads the parameters of public functions and methods, an explicit `__init__` or `__call__` included, and of each overload head: a head that takes the parameter takes `ArrayLike` too, unless it takes it as a type parameter, as the heads of [A57](#a57) do beside a last head that takes `ArrayLike`. A field of a dataclass is the record's own annotation, not a parameter, and is not read here: it says what the record holds. A record a caller builds that converts a field annotated as an array, a tuple, a list or a set, or as a sequence of numbers, says what its constructor takes in a `TYPE_CHECKING` `__init__` in its body, `ArrayLike` (or an open `Sequence`) for the converted field and every other field's annotation or a wider one, with the fields' names, order, keyword-only kind and defaults; `tests/test_record_constructors.py` holds every declared constructor to its fields, the API reference shows it, and the catalogue rows, whose sets arrive from a file as lists, are exempt in `STUB_EXEMPT` of `scripts/check_parameter_annotations.py`. Such a field is converted, never kept as given: the fifth part of `scripts/check_array_aliasing.py` fails one nothing converts, and `tests/test_record_conversions.py` gives each converted field a list and wants it back converted. A body that converts a parameter one item at a time (`for item in contributions: np.asarray(item)`) holds each item type to the rule instead: it takes a number, a sequence of numbers or `ArrayLike`, as `metrology.combined_standard_uncertainty` takes `Sequence[float | Sequence[float] | NDArray[Any]]`, with an array of any dtype, integers included, and the annotation of a vararg types each argument, so `noise_control.cascade(*matrices: ArrayLike)`. A `tuple` of a fixed length (`tuple[float, float]` for the band `limits` of `room.sound_strength`) states its arity and stays; a pair read by index that callers write as a list, the `limits` of `filters.octave_filter`, is a sequence or an array of the two (`RealValues`, a sequence of Python or numpy numbers or an array), since an array of two numbers is read by index as well. Labels that must refuse one text, which is a `Sequence[str]` too, name the two containers the function takes (`tuple[str, ...] | list[str]`) with the reason in `EXEMPT` of `scripts/check_parameter_annotations.py`, keyed by file, function and parameter. The files `scripts/gpu_parity.py` fingerprints are exempt as a whole, read from its `_COVERED`: an annotation there moves the fingerprint `gpu-parity.lock` holds, so their parameters are typed in a batch of their own with the GPU run that records the lock again. `ArrayLike` admits a `str` as well, which none of these functions takes: a text where numbers belong is refused when the call runs ([A42](#a42)), not by the annotation. A count's annotation leaves out the whole float `require_count` also takes (`3.0`), a leniency the type does not state. A value handed to a record's generated constructor is followed into its `__post_init__` as one handed to a function is. A result record that validates a count or a band fraction stores the `int` its validator returns and keeps that annotation. An input record, one a public function takes, is typed where its caller writes the value: one that keeps the value as given (`metrology.CapillaryTube`) takes the numpy integer in its field, and one that stores the value its validator returns (`simulation.Compute`) keeps the stored type in its field and takes the numpy scalar in its constructor, a `TYPE_CHECKING` `__init__`; a record a function returns and another takes whole is a result, listed in `HANDED_ON_RESULTS` or `RECORD_AXIS_EXEMPT` of `scripts/check_parameter_units.py`, and an input record whose constructor does not take the numpy scalar yet is listed in `CONSTRUCTOR_EXEMPT` with the reason. A sample rate that must be a whole number of samples per second (a WAV header, a resampling by an integer ratio, a generated test signal) stays `int | np.integer[Any]`, and `io.write`, the sink of every Signal, takes `float | np.integer[Any]` and refuses a fraction when the call runs; each rate of another family, and each `fraction` that is the bandwidth designator of a filter rather than a band set, is listed in `FAMILY_EXEMPT` of `scripts/check_parameter_annotations.py` with its reason, and a stale entry fails as one of `EXEMPT` does.
