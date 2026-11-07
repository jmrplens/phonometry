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
### A8. Import across domain packages only along an edge the architecture test lists, and only through the names the package publishes

**Why.** The dependency graph between domains is a contract: an import from one domain into another claims that one audience's work feeds the other's, and the claim is written down, not noticed. Every domain may import the toolbox (`filters`, `fluids`, `signals`, `metrology`) and `_internal`, and `_internal` imports no domain code. The import names the package and a name it publishes, never a module inside it: CPython takes a module's lock before its package's, and a thread importing the package meanwhile takes the two the other way round. `from ..filters.weighting import weighting_filter` in `electroacoustics` made two threads importing `electroacoustics` and `vibration` raise `_DeadlockError` five times in five. A kernel several domains share that no package publishes lives in `_internal`, whose `__init__` imports nothing. No module reads a name off the root package, whose lazy `__getattr__` imports a domain on its first read under a lock. And no cycle of imports that run at import time joins two domains: `filters`, `metrology` and `signals` imported one another in one, which held only because each step named a module inside the next.

**Do**

```python
# tests/test_package_architecture.py
ALLOWED_EDGES = {
    ("aircraft", "environment"),  # atmospheric absorption reuse
}
# and aircraft takes what it reuses by a name the package publishes:
# from ..environment import air_attenuation
```

**Don't**

```py
# src/phonometry/room/x.py
from ..building.prediction import flanking  # no (room, building) edge
from ..filters.weighting import weighting_filter  # a module inside filters
```

**Enforced by:** `tests/test_package_architecture.py::test_cross_package_edges_are_whitelisted`, `tests/test_package_architecture.py::test_family_edges_are_whitelisted`, `tests/test_package_architecture.py::test_every_allowed_edge_is_still_taken`, `tests/test_package_architecture.py::test_a_domain_reaches_another_only_through_its_published_names`, `tests/test_package_architecture.py::test_no_cycle_runs_between_domains_at_import`, `tests/test_package_architecture.py::test_internal_imports_no_domain_code`, `tests/test_package_architecture.py::test_no_import_names_a_module_its_support_package_loads`, `tests/test_package_architecture.py::test_no_module_reads_a_name_off_the_root`, `tests/test_concurrent_imports.py`

**Exceptions.** An edge is declared in `ALLOWED_EDGES` (domain to domain) or `ALLOWED_FAMILY_EDGES` (subgroup to subgroup inside a domain) of `tests/test_package_architecture.py`, with a comment saying why; adding one is an explicit, reviewed decision, and an edge no import takes any more fails until it is removed. The root facade and the rendering leaves are not counted as sources. An import only a type checker reads, under `if TYPE_CHECKING:`, may name a module inside another domain, and a type alias the package does not publish ([A5](#a5)): it never runs. A module of `_internal` imports nothing above it when it runs; inside a function it may import from `_plot` and `_i18n` the renderer and the language check of the one record it defines that draws, `io.Signal`. Inside `_internal`, `_plot` and `_report` the lock order holds too: a package whose `__init__` loads some of its own modules is imported by name from outside it (`from .geometry import _draft`), never through one of those modules.

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

**Why.** matplotlib is a soft dependency: importing phonometry and computing must work without it, and `.plot()` without it must fail with the install command, pip's and conda's ([A64](#a64)), not a bare `ModuleNotFoundError`.

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

**Why.** A caller's code keeps running for a release and is told what to use instead; a deprecated name goes only in a major release. The message follows NEP 23 (the version that deprecates, the version that removes, the replacement) and says "deprecated since phonometry", which the suite's `filterwarnings` turns into an error, so every deprecation is met on purpose by a `pytest.warns(DeprecationWarning)` test. The warning goes through `warn_caller` ([A62](#a62)), which names the caller's line however many frames of the library stand between; a renamed module keeps a PEP 562 module `__getattr__` shim (SciPy's pattern), and a renamed keyword accepts the old one through a `"deprecated"` string sentinel and forwards it (scikit-learn's).

**Do**

```python
from phonometry._internal.warnings import warn_caller


def new_name(value: float) -> float:
    return 2.0 * value


def old_name(value: float) -> float:
    warn_caller(
        "old_name is deprecated since phonometry 4.1.0 and will be removed in 5.0.0; use new_name instead.",
        DeprecationWarning,
    )
    return new_name(value)
```

**Don't**

```py
warnings.warn("old_name is deprecated", DeprecationWarning)  # no versions, no replacement, the library's own line
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

**Exceptions.** The guard calls a public `str` parameter or field, alone or in a union (`str | float`, `Literal[...] | str`), a closed choice when the code treats it as one: it hands it to a shared validator (`require_choice`, `check_language`, `check_engine`), compares it with a set of strings, looks it up by key, documents two quoted options or more, writes it beside an `Enum` of the options (`RoadSurface | str`), or passes it on to a function that does one of those. It reads the text through `str(...)`, `.strip().lower()` and the locals bound from it, through a dict spread into a call and into a function the body imports, and a table handed on beside it (`_area_key(area_type, _ACTIVITY_LIMITS)`) closes the helper's `key not in table`. A collection of strings (`Sequence[str]`, `tuple[str, ...]`) and the keys of a mapping are read the same way, item by item through a loop, a comprehension, `.items()` and `.keys()`, and a set difference with the options (`set(sides) - _SIDES`) or a subset test (`<=`, `issubset`) closes them as a whole. A table held in a local (`table = _SIDES`), picked by a conditional expression, picked out of a table of tables (`_BUDGET_TABLES[field]`, read as the keys of all of them) or imported from another module of the package is the table written in place, and a frozen table the source builds with code (`MappingProxyType({**_rows(...)})`) is read off the imported module. A copy of the items made by a comprehension (`{str(d) for d in limits}`) holds the caller's strings, and an annotation is read through the module's type aliases, an imported one in the module that writes it, so a `str` hidden behind an alias (`_Sides = Iterable[str]`) is a `str` all the same. A name is read where Python binds it: a comprehension's variable, a lambda's parameter or a nested function's name of the same spelling as the choice, one of its items or a local bound from it is another name, what fills a record field is read in the scope that binds it, and a table held in a local that two scopes of the function bind under one spelling holds no strings. A string a caller writes below the top level (the columns of `Mapping[int, Mapping[str, float]]`, the items of `Sequence[Sequence[str]]`) is not followed through the code, so the guard calls it a choice as it stands: it takes its `Literal`, or `OPEN` says why it is open. A record field is followed out of `__post_init__` into the helper it is handed to, and a comparison of `<record>.<field>` with a string anywhere in the record's module closes it too. A string open by its nature (a label, a catalogue name, a clause a caller writes) stays `str` and goes in `OPEN` of `scripts/check_choice_literals.py`, keyed by (module, qualified name, parameter) with its reason; a stale entry fails. A catalogue row keeps its text cells `str`, as the catalogue contract requires. A published table read by a choice is keyed by the same `Literal` (`Mapping[CoefficientModel, ...]`, `tuple[Earphone, ...]`), at any depth: one typed `Mapping[str, ...]` whose keys are the options of a `Literal` of its package, or part of one of its own module, is the vocabulary written twice, and a caller indexing it with a misspelling meets a `KeyError` that `mypy` would have refused; a table whose keys match a vocabulary by coincidence goes in `OPEN_TABLES` with its reason. A record field the package fills only with fixed texts (`ReactiveSilencerResult.kind`) is a `Literal` too. A band set is the integer `Literal[1, 3]` ([A22](#a22)), not a string. `Literal[True]` and `Literal[False]` in `@overload` signatures are typing devices, not choices ([A20](#a20)).

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

**Exceptions.** `noise_control.cascade(*matrices)`, `vibration.combine_fault_lines(*results)` and `io.catalogue_schema(*row_types)` stay variadic. `io.Signal.pipe(func, *args, **kwargs)` takes no values of one kind at all: it hands the arguments of another function on to it, as the `pipe` of pandas does.

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

**Exceptions.** A forwarding `*args` or `**kwargs` may be `Any` (matplotlib's keyword surface is open). Elsewhere write `object` when the code never looks inside, or give the `noqa` its reason ([C4](docstrings.md#c4)). A field of a published record is never `Any` and never a `dict`, which a caller's narrower `dict` does not match, at any depth of its annotation and through any alias (`Untyped = Any`, `Table = Dict[str, float]`), which the tests read as `scripts/check_parameter_annotations.py` reads them: it says what it holds (`Mapping[...]` for a mapping, read-only as [A34](#a34) holds it); one that must stay `Any` goes in `ANY_FIELD_EXEMPT` of `tests/test_package_architecture.py` with its reason.

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

**Enforced by:** `scripts/check_frozen_constants.py`, `make frozen-constants`, `CI: Every published table refuses writes`, `tests/test_package_architecture.py::test_a_record_holding_a_read_only_mapping_travels`, `tests/test_record_conversions.py::test_every_record_survives_pickle_and_deepcopy`, `tests/test_record_conversions.py::test_every_record_holding_a_mapping_is_built_here`

**Exceptions.** A mapping proxy does not pickle, deepcopy or serialize to JSON: never patch `copyreg`. A public record with mapping fields freezes them in `__post_init__`, whoever built it, and defines `__reduce__` returning `phonometry._internal.frozen.reduce_with_plain_rows(self)`, as `environment.RoadEmissionCoefficients` does, so that it travels to a process pool or a cache as plain dictionaries and wraps them again on arrival. `tests/test_record_conversions.py` builds one instance of every published record whose fields name a mapping, sends it through `pickle` and `copy.deepcopy` and wants every value back, every array as read-only as it left; a record no instance can be built of goes in `MAPPING_HOLDERS_UNBUILT` there with its reason. An `OwnsArrays` record without `__reduce__` seals its arrays again in `__setstate__`, since neither round trip runs `__post_init__`.

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

The check runs on every path: where the function starts, or in the `__post_init__` of a record a caller builds, so the record refuses an unknown choice when it is built and not when something reads it. A choice checked only beside another argument, behind a test of its text, or with `if text not in OPTIONS` (a `ValueError` for a number) fails, and so does one never checked: `if mode == "fast": require_choice(...)` and `if mode == "typo": return` before the check send the other texts, a misspelling among them, past it. A test of its form keeps a path whole only the way it comes out holding nothing to check: a check behind `if text is not None` or `if isinstance(text, str)`, and a return behind `if text is None`, `if not isinstance(text, str)` or the emptiness of a collection, leave no text unchecked when the annotation lists the value that is no text (`Pace | float`, `Pace | None`); for a `Literal` of texts alone a number or `None` is the check's to refuse with `TypeError`, and a return before it, or a check behind `if text is not None`, lets it through unrefused, in the function, in a helper the choice is handed to whole or in a method of the record that reads it back through `self`, while `if text is not None: return`, `if isinstance(text, str): return`, `case str(): return` and `if texts: return` leave with what the check reads, and `if isinstance(sides, Mapping): return` leaves with no single name but with every key of the mapping. A test that holds only for an option the `Literal` lists (`if method == "vdi2081": return ...` before `require_choice(method, "method", ("bies", "long"))`) lets no misspelling past either. Each key of a mapping and each item of a sequence is checked as written, one by one, through a copy of them too (`tuple(dict.fromkeys(rows))`, `dict(levels.items())`, `{side: float(v) for side, v in limits.items()}`). A filter of a comprehension is a test of each item, and drops the ones it fails for before any check sees them: `{side: float(v) for side, v in limits.items() if side in SIDES}` hands on only the keys it keeps, and a check in the element of `[require_choice(s, "sides", SIDES) for s in sides if s != "both"]` runs only for the items the filter keeps, so both leave a misspelling unchecked; a filter that fails only for an option the `Literal` lists (`if side != "top"`) drops none. A check in a later link of a chained comparison runs only when the links before it hold, one in an `assert` not at all under `python -O`, and one in a generator only as far as something draws from it (`tuple(...)` draws it whole, `any(...)` and `all(...)` stop at the first item that settles them), so each checks on some paths only. A choice its annotation lets a caller write in several parts is checked in each: `FDTDBoundaries(sides=...)`, typed `AcousticBoundary | Mapping[Side, AcousticBoundary | float | Field2D]`, checks the single name, each side it maps and each name a side maps to, and a check of one part says nothing of the others; a single choice beside a sequence of them (`free_sides: Side | Iterable[Side]`) is checked as the one item of a tuple that holds it (`(free_sides,) if isinstance(free_sides, str) else free_sides`, annotated or not), there or in a helper that checks each item it is handed, never letter by letter. A path that leaves on the single choice (`if sides == "rigid": return`) holds a text, so it skips no key, item or value of the other parts.

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

**Exceptions.** The test catches a message that calls a parameter by a retired spelling of the vocabulary tables, in a module whose path is public; any other wrong name is review. The shared helpers in `_internal/validation.py`, `_internal/utils.py` and `_internal/resolve.py` name a value by their `name` argument, which has no default where a default would name a parameter the caller does not have (`require_1d_signal(values, name)`).

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

A warning written in a private module, because two modules of the package raise it, is named by the package that publishes it with `published_by`: a class carries the module it was written in as `__module__`, and a traceback under `python -W error` ended with `phonometry.fluids._state.FluidAssumptionWarning`, a path the reference never shows. The decorator sets `__module__` once the class exists, which drops the line Python recorded for it, so `inspect` says it has no source rather than reading the public module's file at the private module's line, as an assignment in the class body made it do.

**Do**

```python
from phonometry import PhonometryWarning


class DuctWarning(PhonometryWarning):
    """A duct calculation outside its validated range."""


__all__ = ["DuctWarning"]
```

```text
# phonometry/fluids/_state.py, which phonometry.fluids re-exports
from .._internal.warnings import PhonometryWarning, published_by


@published_by("phonometry.fluids")
class FluidWarning(PhonometryWarning):
    """A fluid state outside the domain its model states for itself."""
```

**Don't**

```py
class RoadDeviceWarning(UserWarning): ...


class FluidWarning(PhonometryWarning):
    __module__ = "phonometry.fluids"  # inspect then reads fluids/__init__.py at this line
```

**Enforced by:** `tests/test_package_architecture.py::test_every_warning_a_package_can_raise_is_published`, `tests/test_package_architecture.py::test_every_published_warning_is_a_phonometry_warning`, `tests/test_package_architecture.py::test_every_published_warning_is_named_by_the_package_that_publishes_it`, `tests/test_package_architecture.py::test_inspect_reads_each_published_class_from_the_file_that_writes_it`

<a id="a50"></a>
### A50. Warn with the topic's published class, never `UserWarning` or the bare root

**Why.** Seven calls warned as `UserWarning` (two naming no category) and five as the bare root, so none of them could be silenced or escalated without every other advisory too.

**Do**

```python
from phonometry import filters
from phonometry._internal.warnings import warn_caller


def warn_low_rate(fs: int) -> None:
    if fs < 8000:
        warn_caller(f"Low sampling rate: {fs} Hz", filters.FilterBankWarning)
```

**Don't**

```py
warn_caller("low sampling rate", UserWarning)
warn_caller(msg, PhonometryWarning)
```

**Enforced by:** `tests/test_package_architecture.py::test_every_warning_names_a_published_topic`

**Exceptions.** A helper that warns on behalf of several topics takes the category as a parameter typed `type[PhonometryWarning]`.

<a id="a51"></a>
### A51. Silence inside the library only the warning topic you mean

**Why.** The railway passage bank silenced `UserWarning` around the filter bank it builds, and every other advisory the bank raised inside that block went unseen.

**Do**

```python
import warnings

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
        warn_caller(f"a {length_m} m duct is past the validated range", DuctWarning)
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
from phonometry._internal.video import video_request
from phonometry._internal.video_encoders import NO_WINDOW, find_ffmpeg

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

**Why.** 559 public parameters of 313 functions and methods were annotated narrower than what their body takes. 534 handed the value, or each of its items, to `np.asarray`, or to a helper that does, so a tuple, a `list[int]`, an integer array or a nested `[channels, samples]` list ran; and each was annotated `list[float]`, `NDArray[np.float64]`, `Sequence[float] | np.ndarray` or a sequence of fixed pairs, so a typed caller's code that ran was a type error. The other 25 held a `list` or a `dict` that their body only reads. `list` adds a trap of its own: it is invariant, so a `list[int]` is not a `list[float]`, and the 2-D list that `broadcast.true_peak_level` documents for a multichannel signal was refused by the `SignalInput` alias. A parameter the body converts takes `ArrayLike`, numpy's type for what `np.asarray` converts (`Signal | ArrayLike` where a Signal is taken too, the `SignalInput` alias of `_internal/resolve.py`); a sequence of records or texts takes `Sequence[...]`, and a mapping `Mapping[...]`, which say what the body reads and take a tuple or a read-only mapping as well. A window that `scipy.signal.get_window` or a Welch estimator reads is a name or a tuple of a name and its parameters: 19 `window` parameters were `str`, so `("kaiser", 8.6)` was a type error while the call ran, and they take `str | tuple[ArrayLike, ...]`.

The same holds for one number. 231 counts, band fractions and flags of public functions and records were annotated `int`, `BandFraction` or `bool` while their validator (`require_count`, `require_band_fraction`, an `isinstance` check) took the `np.int64` that `np.argmax` or a shape gives and the `np.True_` of a comparison, so a typed caller converted a value the function would have taken; they take `int | np.integer[Any]`, `BandFraction | np.integer[Any]` and `bool | np.bool_`, and so do 43 more counts, orders and indices that a scalar check read as one number, which `require_count` now reads as a whole one. A mapping is invariant in its key: the 11 mappings of band values that were `Mapping[float, float]` refused the `{125: 40.0}` a caller writes for a band spectrum, so a mapping keyed by `float` stands beside one keyed by `int` (`BandMapping`). A union of mappings whose key or value is more than a plain number, a text or a record (a `Literal`, a mapping, a sequence) asks one step more: mypy reads a `dict` written in the call against the type it is passed for only when that type holds one mapping, and otherwise on its own, a `Literal` column name as a `str` and two inner mappings of different key types as `object`, so `vibration.verify_signal_burst_response("whole-body", "Wk", {16: {"rms": 0.115}})` was refused while it ran, and so was a directional response of `aircraft.verify_aircraft_noise_system` with one band read at 22.5 degrees; each mapping of such a union is offered alone in an overload head, the implementation keeping the union, unless another mapping of the union takes the `dict` as mypy reads it on its own (a `Mapping[str, float]` beside a `Mapping[Literal["rms"], float]` takes the `dict[str, float]` that `{"rms": 1.0}` is). A record's generated constructor has no heads, so a field holds at most one such mapping, and a record that declares its own `__init__` offers them in its heads. The heads that split a union take the same other arguments, or wider ones, read as Python binds a call (a keyword-only parameter or `**kwargs` takes what the other head takes by place) and as a type checker reads the items of a container (a `Sequence[float]` takes a `list[int]`): a head reached only by `kind="a"` is no context, and offers no key, to a call with `kind="b"`, so the `dict[int, float]` of that call stays refused by its own head keyed by `float`. And a quantity of the vocabulary keeps one family of numbers across the API: 40 sample rates that run at any positive value were `int` while 149 were `float`, so the `float` rate `signals.resample_signal` returns, or a `Signal` holds, was refused by the next function; every such rate is a `float`. A NumPy number an annotation takes on its own it takes in the sequences beside it too: `io.Signal.pick(channels: int | np.integer[Any] | Sequence[int])` took one `np.int64` and, for a type checker, refused a list of them, and the impedance profile of `simulation.FDTDBoundaries` took a NumPy float alone and only a `Sequence[float]` beside it, while each call ran; `tests/test_package_architecture.py::test_a_numpy_number_taken_alone_is_taken_in_a_sequence_too` fails a parameter or a field whose sequences, read together (`RealValues` holds the NumPy numbers in sequences of their own) as far as they take the same container a caller writes (a `tuple[np.integer[Any], ...]` beside `Sequence[int]` takes a tuple of NumPy integers, not a list of them), and at every depth, leave out a NumPy number its annotation takes alone.

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
def verify(measured: Mapping[int, Row] | Mapping[None, Row]) -> bool:  # reads {16: {"rms": 0.1}} on its own
    ...
def psd(x: ArrayLike, window: str = "hann") -> float:  # refuses ("kaiser", 8.6), which get_window takes
    ...
def laeq(x: ArrayLike, fs: int) -> float:  # refuses the float rate a Signal holds
    ...
```

**Enforced by:** `scripts/check_parameter_annotations.py`, `make parameter-annotations`, `CI: Every public parameter admits what its body converts`, `tests/test_check_parameter_annotations.py::test_the_package_keeps_the_rule`, `tests/test_record_constructors.py::test_every_record_says_what_its_constructor_takes`, `tests/test_record_constructors.py::test_every_record_a_guide_builds_is_read_as_built_by_a_caller`, `scripts/check_array_aliasing.py`, `tests/test_record_conversions.py::test_a_list_given_to_a_converted_field_is_held_converted`, `tests/test_package_architecture.py::test_a_static_case_names_an_array_of_a_given_dtype_before_the_call`, `tests/test_package_architecture.py::test_a_numpy_number_taken_alone_is_taken_in_a_sequence_too`, `mypy`

**Exceptions.** The rule reads the parameters of public functions and methods, an explicit `__init__` or `__call__` included, and of each overload head: a head that takes the parameter takes `ArrayLike` too, unless it takes it as a type parameter, as the heads of [A57](#a57) do beside a last head that takes `ArrayLike`. A field of a dataclass is the record's own annotation, not a parameter, and is not read here: it says what the record holds. A record a caller builds that converts a field annotated as an array, a tuple, a list or a set, or as a sequence of numbers, says what its constructor takes in a `TYPE_CHECKING` `__init__` in its body, `ArrayLike` (or an open `Sequence`) for the converted field and every other field's annotation or a wider one, an open `Sequence` of numbers or of arrays beside the numpy array of them, which is one at run time and not to a type checker (`RealValues` for three thresholds, `ArrayRows` for a curve's `(x, y)` pair), with the fields' names, order, keyword-only kind and defaults; a record of more fields than the 13 parameters a function takes (Sonar's rule S107, `MOST_PARAMETERS`) declares them as the keys of a `TypedDict` written in its module instead, `def __init__(self, **measurements: Unpack[...]) -> None: ...`, a key a caller may leave out for each field with a default, as `metrology.SoundLevelMeterPeriodicMeasurements` does with its 38; `tests/test_record_constructors.py` holds every declared constructor to its fields, the API reference shows it, and the catalogue rows, whose sets arrive from a file as lists, are exempt in `STUB_EXEMPT` of `scripts/check_parameter_annotations.py`. Such a field is converted, never kept as given: the fifth part of `scripts/check_array_aliasing.py` fails one nothing converts, a field annotated as a mapping that keeps the caller's `dict` included, and `tests/test_record_conversions.py` gives each converted field a list and wants it back converted. A record a guide builds by hand (`vibration.TransferStiffnessResult(...)` in a Python block of `docs/` or `site/`) is one a caller builds: `tests/test_record_constructors.py` reads every guide and fails such a record unless a public function takes it or `CALLER_BUILT` of `scripts/check_parameter_annotations.py` names it with where its construction is documented. A body that converts a parameter one item at a time (`for item in contributions: np.asarray(item)`) holds each item type to the rule instead: it takes a number, a sequence of numbers or `ArrayLike`, as `metrology.combined_standard_uncertainty` takes `Sequence[float | Sequence[float] | NDArray[Any]]`, with an array of any dtype, integers included, and the annotation of a vararg types each argument, so `noise_control.cascade(*matrices: ArrayLike)`. A `tuple` of a fixed length (`tuple[float, float]` for the band `limits` of `room.sound_strength`) states its arity and stays; a pair read by index that callers write as a list, the `limits` of `filters.octave_filter`, is a sequence or an array of the two (`RealValues`, a sequence of Python or numpy numbers or an array), since an array of two numbers is read by index as well. Labels that must refuse one text, which is a `Sequence[str]` too, name the two containers the function takes (`tuple[str, ...] | list[str]`) with the reason in `EXEMPT` of `scripts/check_parameter_annotations.py`, keyed by file, function and parameter. `ArrayLike` admits a `str` and a `bytes` as well: where a parameter takes numbers alone, a text where numbers belong is refused when the call runs ([A42](#a42)), not by the annotation, and where it takes a `Literal` choice beside the numbers, the numbers are `NumericArrayLike`, which admits no text ([A59](#a59)). A count's annotation leaves out the whole float `require_count` also takes (`3.0`), a leniency the type does not state. A tuple in a window's annotation takes a text first and, after it, any count of items that each take a number and a sequence of numbers, as `("kaiser", 8.6)`, `("general_gaussian", 1.5, 7.0)` and `("general_cosine", [0.5, 0.5])` need: `tuple[float, ...]`, `tuple[str, float]` and `tuple[str, *tuple[float, ...]]` each refuse one of them, and the check fails them. Heads that pair each mapping of a union with a value of another parameter on purpose, because the call refuses the mapping beside the other values, take different calls and stay: the IEC 61094 budgets of `metrology.comparison_uncertainty_budget` and `metrology.reciprocity_uncertainty_budget` offer the components of each table with that table's `field` and those both tables list with a field held in a variable, and are listed in `PAIRED_MAPPINGS` of `scripts/check_parameter_annotations.py` with the reason; the listing excuses no mapping that no head offers alone, and a stale entry fails. A window's annotation leaves out the bare number `get_window` reads as the beta of a Kaiser window (`8.6`), which the Welch estimators refuse and `("kaiser", 8.6)` names everywhere: `signals.spectrogram`, `signals.zoom_fft`, `signals.envelope_spectrum`, `signals.window_metrics` and the eleven functions of `electroacoustics` that take a window run with it, a leniency the type does not state. A value handed to a record's generated constructor is followed into its `__post_init__` as one handed to a function is, and from there into a function handed the record and the field's name, as `_hold_cells(self, "ix", "iy")` validates and stores the cell indices of an FDTD source. An item a body unpacks or indexes (`ny, nx = shape`, `shape[0]`) is read as an item of the annotation, and an element of an item it unpacks (`for entry in probes: ix, iy = entry`) as an element of the annotation's items: `FDTD2D.plot_geometry(probes: Iterable[Sequence[int | np.integer[Any]]] | NDArray[np.integer[Any]] | None)` takes each index as `require_count` does, where `Iterable[tuple[int, int]]` refused a NumPy index the call took. A result record that validates a count or a band fraction stores the `int` its validator returns and keeps that annotation. An input record, one a public function takes, is typed where its caller writes the value: one that keeps the value as given (`metrology.CapillaryTube`) takes the numpy integer in its field, and one that stores the value its validator returns (`simulation.Compute`) keeps the stored type in its field and takes the numpy scalar in its constructor, a `TYPE_CHECKING` `__init__`; a record a function returns and another takes whole is a result, listed in `HANDED_ON_RESULTS` or `RECORD_AXIS_EXEMPT` of `scripts/check_parameter_units.py`, and an input record whose constructor does not take the numpy scalar yet is listed in `CONSTRUCTOR_EXEMPT` with the reason. A sample rate that must be a whole number of samples per second (a WAV header, a resampling by an integer ratio, a generated test signal) stays `int | np.integer[Any]`, and `io.write`, the sink of every Signal, takes `float | np.integer[Any]` and refuses a fraction when the call runs; each rate of another family, and each `fraction` that is the bandwidth designator of a filter rather than a band set, is listed in `FAMILY_EXEMPT` of `scripts/check_parameter_annotations.py` with its reason, and a stale entry fails as one of `EXEMPT` does. A case in `tests/static_typing` that holds a parameter to an integer array names the array, typed with its dtype, before the call (`integers: NDArray[np.int64] = np.zeros(4000, dtype=np.int64)`): written in the call, the array takes its type from the parameter, which mypy reads as `NDArray[Any]` against a floating array, so the case would pass however narrow the parameter were; `tests/test_package_architecture.py::test_a_static_case_names_an_array_of_a_given_dtype_before_the_call` fails one written in the call.

<a id="a59"></a>
### A59. Set a `Literal` choice beside numbers as `NumericArrayLike`, never beside a type that takes any text, and refuse a text where its numbers go

**Why.** Seven public parameters take one of a few words or an array of numbers: the `initial_state` of `filters.time_weighting`, the `flow_resistivity` of `aircraft.terrain_screening_adjustment` and of `aircraft.RotorcraftGround`, the `termination` of `materials.layered_absorber` and of `materials.diffuse_field_absorption`, the `coefficients` of `materials.delany_bazley` and the `speech_spectrum` of `speech.speech_intelligibility_index`. Five were annotated `Literal[...] | ArrayLike`, and numpy's `ArrayLike` admits any `str` and any `bytes`, so `termination="rigidd"` type-checked as numbers and only the call refused it: the `Literal` listed its options and enforced none of them. The coefficients were annotated a tuple of floats, narrower than the list or the array the call took, and the speech spectrum `ArrayLike` alone, its four vocal efforts stated nowhere but in the body. `NumericArrayLike`, beside the other shared aliases in `src/phonometry/_internal/types.py`, is `ArrayLike` without its texts and without arrays typed with another dtype: a number, a sequence of numbers at any depth, a numpy number or array of a number or truth-value dtype, anything else whose `__array__` gives one, and a sequence of such arrays. Beside a `Literal` it stands for the numbers, so a misspelt choice is a type error, and the checks that read `ArrayLike` as a conversion read it the same way. `str`, `LiteralString`, numpy's `DTypeLike` (a dtype by its name), `Any`, `object`, a sequence of texts, since a text is a sequence of texts, and a type parameter bound to one of them or to nothing take any text too, and swallow a choice the same way.

The annotation is half of it. The body reads a `str` as the choice and anything else as the numbers, so a text given in another form, a `bytes`, a `bytearray`, or a text or a `bytearray` inside a sequence or an array, reached the conversion of the numbers, which parses it or reads a `bytearray` as the codes of its characters (`[bytearray(b"12")]` as `[[49, 50]]`): `materials.layered_absorber(termination=["400", "400"])` closed the stack with an impedance of 400 Pa s/m, `materials.delany_bazley` took `coefficients=b"12345678"` as the codes of its eight characters, `filters.time_weighting` started from `initial_state=["0.5"]`, `speech.speech_intelligibility_index` read `["60"] * 18` as eighteen levels of 60 dB, and `aircraft.RotorcraftGround` stored a `bytes`, `None` or a complex value as given and left it to the event that read it, which failed with an error that named nothing. `refuse_text_beside_choice`, in `src/phonometry/_internal/validation.py`, refuses such a text with `TypeError` before the numbers are read, naming the parameter and its options, and a sequence nested more than 32 deep the same way, a sequence that holds itself among them, which its search for a `bytearray` would otherwise follow until Python's recursion limit; `None` where it is no option, and an object that is no number, are a `TypeError` naming the parameter as well, and a record refuses each when it is built.

**Do**

```python
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from phonometry._internal.types import NumericArrayLike
from phonometry._internal.validation import refuse_text_beside_choice, require_choice


def closing_impedance(
    termination: Literal["rigid", "free"] | NumericArrayLike = "rigid",
) -> NDArray[np.complex128] | None:
    if isinstance(termination, str):
        named = require_choice(termination, "termination", ("rigid", "free"))
        return None if named == "rigid" else np.asarray(413.0 + 0.0j)
    refuse_text_beside_choice(termination, "termination", ("rigid", "free"))
    refusal = "'termination' must be one of ('rigid', 'free') or an impedance in Pa s/m."
    if termination is None:  # np.asarray reads None as nan
        raise TypeError(refusal)
    try:
        return np.asarray(termination, dtype=np.complex128)
    except TypeError:  # an object that is no number, which numpy does not name
        raise TypeError(refusal) from None


closing_impedance("free"), closing_impedance([400.0, 410.0]), closing_impedance(400.0 + 10.0j)
```

**Don't**

```py
def closing_impedance(termination: Literal["rigid", "free"] | ArrayLike = "rigid") -> ...:  # "rigidd" type-checks as numbers
    ...
def labels(names: Literal["auto"] | Sequence[str] = "auto") -> ...:  # "autoo" is a sequence of texts
    ...
def closing_impedance(termination: Literal["rigid", "free"] | NumericArrayLike = "rigid") -> ...:
    if isinstance(termination, str):
        ...
    return np.asarray(termination, dtype=np.complex128)  # reads ["400"] as 400+0j
```

**Enforced by:** `scripts/check_parameter_annotations.py`, `make parameter-annotations`, `CI: Every public parameter admits what its body converts`, `tests/test_check_parameter_annotations.py::test_a_choice_beside_an_alternative_that_takes_any_text_is_refused`, `tests/test_check_parameter_annotations.py::test_the_array_like_of_numbers_is_read_as_one`, `tests/test_check_parameter_annotations.py::test_the_package_keeps_the_rule`, `tests/test_choices_beside_numbers.py::test_every_choice_beside_numbers_is_walked`, `tests/test_choices_beside_numbers.py::test_a_choice_beside_numbers_refuses_what_is_no_number_by_name`, `tests/test_choices_beside_numbers.py::test_no_body_reads_a_choice_its_annotation_does_not_state`, `mypy`

**Exceptions.** The rule reads every union of a public parameter, of each overload head, of a public record's field and of the constructor a record declares under `TYPE_CHECKING`, at the top and inside a container or a mapping (`Sequence[Literal["a"] | ArrayLike]`), through the package's aliases and the type parameters of the function or record, so an alias that hides `ArrayLike` (`Signal | ArrayLike`, a band mapping beside an array-like) is read as `ArrayLike`. A choice beside a tuple of a fixed length, or the `Literal` key of a mapping whose values are `ArrayLike`, takes no text in its place and passes. A `Literal` of numbers beside numbers is no choice of words and is not read here. A window keeps `str | tuple[ArrayLike, ...]` ([A58](#a58)): its names are open, so it lists no `Literal`. Beside the texts, the alias refuses what `ArrayLike` admitted of an array typed with a dtype that is no number or truth value (`np.object_`, `np.generic`, `np.datetime64`, `np.timedelta64`) and of a buffer such as `memoryview`: the type of an object array says nothing of what it holds, and `NDArray[np.generic]` cannot be admitted without an array of texts, whose dtype is one. The seven parameters convert an object array of numbers all the same, a leniency the type does not state. `tests/static_typing/test_numeric_choices.py` pins the alias to the forms `np.asarray` takes of numbers that it lists, refuses the other dtypes and a buffer, and holds each of the seven parameters to its misspelling, the coefficients of `materials.delany_bazley` and the speech spectrum included. `tests/test_choices_beside_numbers.py` finds every choice beside numbers of the imported package from its annotation, read as this rule reads it, a `Literal` of texts beside a number, an array of numbers or a sequence of them at the top or inside a container or a mapping, and calls each with a text in every form but a `str`, with `None` where it is no option and with an object: each one found has its call in `CALLS`, a call no choice answers to fails, and a probe a choice takes on purpose is keyed in `EXEMPT` with the reason; it holds none, since a record holds a `bytearray` as the `bytes` it spells and an FDTD boundary refuses it as the text it is. The walk sees a choice only where the annotation states it, so the same test reads the bodies as well: a public parameter or record field whose annotation names numbers and sets no choice, but whose body, or a function of the package it is handed to, tests it with `isinstance(..., str)` and reads the text as something other than numbers, fails until the annotation states the choice. A test of a text that ends in a `raise`, or one under a `not`, is a refusal or an exclusion and reads no choice.

<a id="a60"></a>
### A60. Open a file a caller or the environment names only through the shared check of what the name holds

**Why.** A name a caller hands a reader, or one the environment does, can hold something other than a file. A named pipe no one writes to keeps an open waiting for a writer that never comes: `io.read` on one hung at the open of its sniffer, `load_anp_database` on a directory holding one hung at its `read_text`, and the hosts file of the remote runs, whose name `PHONOMETRY_HOSTS_FILE` gives, hung at its `read_bytes`. A device such as `/dev/zero` keeps a read going without end, and a directory raised the `IsADirectoryError` of whichever open met it first. `src/phonometry/_internal/json_input.py` holds the one check: `open_regular` and `read_at_most` look at the name, refuse anything but a regular file before it is opened, open it without waiting and ask the open file again, so that a pipe put in its place in between is refused too, and `read_at_most` reads no more than the limit it is given; `not_regular_at` says what is at a name that a reader of another library (SciPy, python-soundfile) is about to open itself, and cannot see a pipe put at the name after it looks, since that library opens the name on its own. Each reader turns what they find into its own `ValueError`, naming the file through `escaped`, so that a name that is not UTF-8 or holds a control character prints as its escapes, and saying what it holds.

**Do**

```python
from pathlib import Path

from phonometry._internal.json_input import (
    NotRegularError,
    TooLargeError,
    escaped,
    read_at_most,
)


def read_table(path: Path) -> str:
    named = escaped(str(path))  # a name that is not UTF-8 prints as its escapes
    try:
        raw = read_at_most(path, 1024 * 1024)
    except NotRegularError as exc:
        msg = f"{named}: is {exc.kind}, and a table is read only from a regular file"
        raise ValueError(msg) from None
    except TooLargeError:
        msg = f"{named}: a table is at most 1 MiB"
        raise ValueError(msg) from None
    return raw.decode("utf-8")
```

**Don't**

```py
def read_table(path: Path) -> str:
    return path.read_text(encoding="utf-8")  # a pipe at the name waits for a writer forever
def describe(path: Path) -> object:
    return soundfile.info(str(path))  # nothing asked what the name holds before soundfile opens it
```

**Enforced by:** `scripts/check_regular_file_reads.py`, `make regular-file-reads`, `CI: Every reader asks what a name holds before it opens it`, `tests/test_check_regular_file_reads.py::test_the_library_reads_every_name_through_the_check`, `tests/io/test_io_regular_files.py`, `tests/io/test_io_write_target.py`, `tests/aircraft/test_anp_tables_read.py`

**Exceptions.** A read of the library's own files, which no caller names (a published table through `importlib.resources`, the `VERSION` file of a source checkout, the bootstrap module the client sends a node, the video a node's encoder wrote in the scratch directory of the run), is listed in `EXEMPT` of `scripts/check_regular_file_reads.py`, keyed by file and function with the reason; an entry that covers nothing fails. A mode that writes (`"wb"`, `"xb"`, `"ab"`, `"r+b"`) is a writer's and is not read here, and this rule holds no writer. `io.write`, the target of `io.convert`, every `.report()` and the response plot of a filter bank write through `writing_beside` of the same module: with nothing at the name, or a regular file that no link stands for, the file is written beside it and renamed over it once whole, so a write stopped half way leaves the name as it was; a link, a pipe, a device or a directory at the name is opened there as Python opens a name, so a link is followed, a pipe waits for a reader and a directory raises `IsADirectoryError`, since a caller who names a pipe streams the file into it on purpose. The sidecar and catalogue writers write beside the name through `write_beside` and rename the file into place after refusing a pipe, a device and a directory, so they never open the name for writing; the video writers put a hidden partial file beside the name and rename it once ffmpeg has finished it. The check names a call by what the imports, assignments and parameters of its own scope bind it to, as Python looks the name up (the function, the functions around it, then the module; a class body's names are not its methods', a comprehension's loop target is its own, a name declared `global` is the module's, and a name a scope both defines and rebinds names no function), and knows a check by the module that defines it, so a call that only shares a check's name (`np.info(path)` beside the library's `info`, a method of another object called `read_at_most`) checks nothing; it reads the order of the calls in the source, not the paths a function can take; a `.open()` given its mode through a name, and a reader reached through `getattr()` or a `functools.partial`, are not read. The tests of each reader, which put a pipe, a link to a device and a directory at the name and want the refusal within seconds, are what prove it refuses.

<a id="a61"></a>
### A61. Read a caller's numbers through `real_array`, `complex_array`, `real_number` or `complex_number`, which refuse what is no number by name

**Why.** `np.asarray(x, dtype=np.float64)` converts three inputs that hold no real numbers into ones that pass every guard after it. A complex value comes back as its real part with no more than a `ComplexWarning`, and a NumPy complex number held in a list or an array of objects the same way; a text is parsed; and a `bytearray`, alone or inside a list, is read as the codes of its characters. `np.asarray(x, dtype=np.complex128)` parses a text and reads a `bytearray` the same way. `environment.method_b_scale_values(np.complex128(0.5 + 0.3j))` rated the mark at 0.5, `building.energy_average_level([bytearray(b"12")])` came back as 49.5 dB, `vibration.injected_power([bytearray(b"12")], [1e-3 + 1e-4j])` read a force of 49 and 50 N, and a column of readings left as text passed for numbers. The library converted a caller's numbers that way in 1049 places. `real_array(x, name)`, in `src/phonometry/_internal/validation.py`, is the one reading of a caller's real numbers: it refuses each of the three with a `TypeError` that names the parameter, names an element that is no number and a ragged nesting too, and converts an array of numbers as `np.asarray` does, at the cost of a test of its dtype. `complex_array(x, name)` is its twin where a complex value belongs (a reflection factor, an impedance, a mobility): it refuses a text and a `bytearray` the same way and reads a real number as a complex one. Python's `float(x)` misreads one number the same way, parsing a text (`npd_atmosphere_increment(temperature_c="25")` read 25 °C) and keeping the real part of a NumPy complex number, and `complex(x)` parses a text: `real_number(value, name)` and `complex_number(value, name)` are the readers of one number. Arithmetic on the value first changes nothing: `aircraft.Aerodrome(elevation_ft=0.0).pressure_ratio(np.complex128(100 + 1j))` computed with the complex altitude and handed back the real part of the result, and a text failed inside the arithmetic with an error that named no parameter. A function that has checked the value already, on every path to the conversion, through a shared check or one of its own module, converts it as it likes.

**Do**

```python
import numpy as np
import pytest

from phonometry._internal.validation import real_array


def scale_values(marked_fraction):
    fraction = real_array(marked_fraction, "marked_fraction")
    return np.round(1.0 + 4.0 * fraction, 1)


scale_values([0.25, 0.5])
with pytest.raises(TypeError, match="'marked_fraction' must be real, not complex"):
    scale_values(np.array([0.5 + 0.3j]))
with pytest.raises(TypeError, match="'marked_fraction' must be numbers, not text"):
    scale_values([bytearray(b"12")])
```

**Don't**

```py
def scale_values(marked_fraction):
    fraction = np.asarray(marked_fraction, dtype=np.float64)  # np.complex128(0.5 + 0.3j) reads as 0.5
    return np.round(1.0 + 4.0 * fraction, 1)
```

**Enforced by:** `scripts/check_real_conversions.py`, `make real-conversions`, `CI: Every conversion of a caller's numbers goes through a check`, `tests/test_check_real_conversions.py::test_the_package_keeps_the_rule`, `tests/test_check_real_conversions.py::test_each_shape_of_a_caller_s_value_is_found`, `tests/test_check_real_conversions.py::test_a_caller_s_value_no_check_reads_on_every_path_is_found`, `tests/test_check_real_conversions.py::test_every_check_said_to_refuse_a_complex_value_does`, `tests/test_check_real_conversions.py::test_every_check_said_to_refuse_a_text_does`, `tests/test_check_real_conversions.py::test_a_private_helper_reads_what_its_calls_hand_it`, `tests/test_real_numbers_read_by_name.py`, `tests/test_reader_names.py`, `tests/test_numbers_read_before_arithmetic.py`, `tests/test_scalar_guards.py::test_every_public_scalar_parameter_refuses_an_array_or_a_text_by_name`

**Exceptions.** The check reads every function of `src/phonometry`, private and nested ones included, since a public function hands its caller's value on to the helper that converts it. A function no caller of the library reaches, one at the top of a module whose name opens with an underscore or that sits in a private module, which no `__all__` publishes and which the package only calls (never hands on, keeps in a table or decorates with), is read through its calls: each parameter holds what the calls across the package hand it, joined, a caller's value no check read where any call hands one, and the modules are read again until no call hands anything new. Any other function's parameters, a method's and a nested function's included, are a caller's values; a nested function's count as much as those of the function around it, and a nested function or a `lambda` reads the names it shares with the function around it as that function holds them where it uses the nested one (calls it, hands it on or returns it), or, used nowhere there, where it defines it. A conversion is one to floats or to complex numbers: `np.asarray`, `np.array` and their kin with the dtype given by keyword or in second place, as a type, as a text with its byte order such as `"<f8"`, as `np.dtype(...)` or through a name bound to one; the fill value of `np.full`; `.astype()`; `np.float64()` or `np.complex128()` of a value; and Python's `float()` and `complex()` of one value. A caller's value is a parameter of the function that converts it, read bare, through an item, through a call or an attribute that keeps its values (`np.atleast_1d`, `list`, `.ravel()`, `np.concatenate`, `.T`), through `getattr(x, name, x)`, through a tuple or a list that holds it, or through a loop or a comprehension over it, and in a record's `__post_init__` a field, which the caller set; an item assigned to it (`x[0] = v`) holds `v` from there on, and the whole value holds it among its items, so a check of the whole holds only as far as `v` was checked; arithmetic on it (`x * 2`, `-x`, `x += y`) keeps it the caller's value, since a complex value stays complex through it and a list or a text repeats or joins, checked only as far as every operand it is made of was; and a field a method reads outside `__post_init__` was read when the record was built. A closure handed out may run after its function rebinds what it reads, so it is read where it is used and at the end of its function, joined, and a method of a class written in a function reads the names it shares with that function where the class is written and at the end. A check is a call of one of the shared checks the script lists with what each refuses, a complex value, a text or both, which `tests/test_check_real_conversions.py` calls one by one, or of a function of the package that hands that parameter to one on every path that leaves it by its end or a `return`: a check after an earlier `return`, in the body of a `try` a handler of which goes on, or of a parameter the function has rebound to another value first, makes no check of it, and a check handed what NumPy made of the value first (`np.asarray(x)`, `np.atleast_1d(x)` and the other NumPy calls that keep its values, given no floating dtype, or a name bound to it on any path that reaches the check), in which a `bytearray` is already the codes of its characters, is reported as a conversion no check precedes, and so is a name a `with` binds or a `match` captures from that reading. What a call of a check of the package hands back is what it returns of its parameters, checked as far as it checked them on the way; a parameter it returns unchecked comes back the caller's value, whether it returns it bare or through what keeps it (arithmetic, `.T`, a loop or a comprehension over it, a name it added it to with `+=` or an array it set an item of to it, a name a `:=` binds to it or a `case` captures of it), and a value it computes is computed; a comprehension's own variable stands for the items it walks only inside the comprehension, and what a nested function or a lambda binds is its own, as Python scopes them, but a name it declares `nonlocal` is the function's, and so is an item it fills of a name of the function; a name a function declares `global` is the module's, in it and in the functions nested in it, whatever a function around binds of that spelling; and a nested function's parameter stands for what each call of it by name hands it, and for its default. A `*` argument or a `**` mapping may hand its values to any parameter from its place on, or to any that takes a keyword, but not to one an argument of the call fills in its place or by its name, since the call would raise. An `isinstance` test that finds the value a real number refuses a text and a complex value where it holds, and one that finds it a number of any kind a text; a check handed `x or 0.0` checks `x`. A conversion to floats needs both refused, one to complex numbers a text, and only a check on every path to the conversion counts: one in a single branch of an `if`, in a loop's body, on the right of `and` or `or`, in a later link of a chained comparison, in an `assert` (which `python -O` leaves out), handed one branch of a conditional expression (`x if flag else [1.0]`; `d if x is None else x` checks `x`) or the default of `getattr`, or of an item (`x[0]`) rather than the whole value does not. A conversion of a value that is no caller's number but that the rule cannot tell from one (an array of objects an `isinstance` test has read item by item, the text a catalogue prints, the quick path of the readers themselves, a stage or an equation handed to another function or a root finder, which calls it with values of its own, a function held in a table, and a private method, whose calls are not followed) is listed in `EXEMPT` of the script, keyed by file and function with the reason; an entry that covers nothing fails. A parameter written as one number reads it through a shared scalar guard ([A43](#a43)), which refuses a complex number of either kind the same way. A function that reads a value a public function hands it, however many calls down, private or public, in its module or one it imports from, names it as that public function's parameter: the caller's name is handed on with the value where callers name it differently (`_coerce(alpha_p, centers, "alpha_p")`), or the public function reads the value under its own name first, on every path to the call, before handing it to another public function that would name it after its own parameter (`ra` reads `reduction_index` before the index function would read it as `band_values`); a reading on one side of a conditional expression, after an `and`, an `or` or the first link of a chained comparison, in a lambda, a comprehension, a generator or an `assert` may be skipped, so it reads nothing first. A name of the parameter's spelling that a comprehension, a lambda or a nested function binds for itself is another name, as Python scopes it. A field read off a record is named after the field. `tests/test_reader_names.py` follows the chains of calls across the package and fails on such a reading.

<a id="a62"></a>
### A62. Warn through `warn_caller`, which names the caller's line, never through `warnings.warn`

**Why.** A warning is shown at a file and a line, a filter by module reads that file, and Python's `default` action keys its memory of what it has shown on that line. Of the library's 178 warnings, 175 passed a `stacklevel` counted by hand for one route to it, the other three already skipping the package's files, and the same advisory is reached through several: a public function, a method, a record's `__post_init__`, another domain that calls it. Where the route was deeper or shallower than the count the warning landed on a library line, 33 of them in the suite: `OctaveFilterBank(44100)` and `octave_filter(x, 44100)` both warned at `filters/core.py:698`, inside the bank, so a notebook showed the warning for its first bank and never again, whatever line made the next one, and `filterwarnings("error", module="my_analysis")` let it through. `warn_caller(message, category)`, in `src/phonometry/_internal/warnings.py`, passes `skip_file_prefixes` with the package's own directory, which Python 3.12 added, and counts the frames that run the package's code from elsewhere (the `__init__` a dataclass compiles from a string, `functools.cached_property`, the exit of a `contextlib.contextmanager`, `dataclasses.replace`), so the warning lands on the first line of the caller's code however deep the route is, and a forwarded `stacklevel` parameter has nothing left to count. A warning instance relayed from a node is raised again through it with its own class.

**Do**

```python
from phonometry._internal.warnings import warn_caller


def warn_wide_bands(n_bands: int) -> None:
    if n_bands > 40:
        warn_caller(f"{n_bands} bands is past the validated range", DuctWarning)
```

**Don't**

```py
def _warn_wide_bands(n_bands, stacklevel):
    warnings.warn(f"{n_bands} bands", DuctWarning, stacklevel=stacklevel)  # counted for one route
```

**Enforced by:** `tests/test_package_architecture.py::test_the_library_warns_only_through_warn_caller`, `tests/test_package_architecture.py::test_the_warning_rule_reads_every_way_to_reach_warnings_warn`, `tests/test_internal_warnings.py`, `tests/test_warning_attribution.py`

**Exceptions.** `src/phonometry/_internal/warnings.py` itself, which holds the one call of `warnings.warn`. The guard refuses a call of `warnings.warn` or `warnings.warn_explicit`, a reference to either handed on, an import of either from `warnings` or `_warnings`, a `getattr` of either, and either reached through `__import__`, `importlib.import_module` or `sys.modules`; it does not follow a name bound to the function inside an expression it cannot read, which review catches.

<a id="a63"></a>
### A63. Check every argument before the first advisory, and advise once the result stands

**Why.** Under `python -W error` a warning raised ahead of a refusal takes its place: the caller who wrote `except ValueError` meets the advisory instead and never learns which argument was wrong. The in situ and reverberation-room sound power determinations warned that no background was given, or that there were too few microphone positions, before they checked the temperature, the bands or the background's shape; `speech.stipa` warned that a clip was short before refusing one too short to hold a single modulation period; `fluids.air` warned that a pressure lay outside its formula's domain before refusing a pressure and a humidity that cannot hold together. A refusal may also come from the result itself, as the loudness ratio a silent recording leaves undefined; the advisory then waits for the result, not the other way round.

**Do**

```python
import numpy as np

from phonometry import emission
from phonometry._internal.validation import require_finite, require_finite_array
from phonometry._internal.warnings import warn_caller


def determine(levels, *, background_levels=None, temperature_c=23.0):
    grid = require_finite_array(levels, "levels")
    if background_levels is not None and np.shape(background_levels) != grid.shape:
        raise ValueError("'background_levels' must match 'levels' band for band.")
    require_finite(temperature_c, "temperature_c")
    total = 10.0 * np.log10(np.sum(10.0 ** (grid / 10.0)))
    if background_levels is None:
        warn_caller(
            "No background levels were supplied ...", emission.SoundPowerWarning
        )
    return total
```

**Don't**

```py
def determine(levels, *, background_levels=None, temperature_c=23.0):
    grid = require_finite_array(levels, "levels")
    if background_levels is None:
        warn_caller(
            "No background levels were supplied ...", emission.SoundPowerWarning
        )
    require_finite(temperature_c, "temperature_c")  # under -W error the advisory wins
```

**Enforced by:** `tests/refusal_order.py`, `tests/test_refusal_order.py`, `tests/test_refusals_before_advisories.py`

**Exceptions.** None. NumPy's warnings count too when they are shown at a line of the package; silence the operation with `np.errstate` once the library has said what it has to say.

<a id="a64"></a>
### A64. Take the install command of a missing extra from `install_hint`, which names pip and conda

**Why.** A message for a missing soft dependency is copied and run as written. Eleven of them said only `pip install "phonometry[plot]"` and the like, and in a conda environment that command installs matplotlib and eight of its dependencies from PyPI beside conda-forge's NumPy. Each was spelled where it was raised, so the extra was named twice in one ("ships as the [audio] extra. Install the [audio] extra with"), the FLAC writers said "Reading FLAC", and the docstrings repeated the pip command 439 times. `install_hint(*extras)` in `src/phonometry/_internal/extras.py` builds the hint from one table of the conda-forge packages that bring each extra (`matplotlib-base`, not `matplotlib`, which pulls a GUI toolkit; `pysoundfile`, conda-forge's name for python-soundfile), so every message gives both commands, and a docstring names the extra.

**Do**

```python
from phonometry._internal.extras import install_hint


def draw() -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        msg = f"Plotting requires matplotlib. Install it with: {install_hint('plot')}"
        raise ImportError(msg) from exc
    plt.subplots()
```

**Don't**

```py
msg = 'Plotting requires matplotlib. Install it with: pip install "phonometry[plot]"'
```

**Enforced by:** `scripts/check_quoted_extras.py`, `CI: Every install command quotes its extras`, `tests/test_check_quoted_extras.py::test_the_package_spells_no_install_command_outside_its_hints`, `tests/test_install_hints.py`

**Exceptions.** `src/phonometry/_internal/extras.py` itself, which spells the commands. A library no extra brings, CuPy's wheel for the CUDA version, takes `package_hint(pip_package, conda_package)` from the same module. The check reads the text of every file of the package, so a command split between two string literals escapes it, which review catches.
