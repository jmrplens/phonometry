← [Documentation index](../README.md)

# Numbers and data

This page governs how phonometry compares the numbers it computes and how it holds and publishes data: equality with zero and comparison with a printed limit, the guards a scalar, a count or a signal passes before it is read, the arrays a result keeps, units, reference values and the precision a numerical setting is sized to, the citations and cells of the packaged catalogues, and the operations an FDTD engine steps its fields with. Read it before you write or change code in `src/` that compares a computed value, validates an argument, stores an array, converts a unit or transcribes a printed number, before you edit a catalogue data file, and before you change a method of an FDTD engine. Examples that import from `phonometry._internal` stand for code inside the package, where the import is relative ([A11](api.md#a11)). Where a unit goes in a name is on [Naming](naming.md), and which error class a refusal raises is on [API shape](api.md).

## Comparing computed values

<a id="x1"></a>
### X1. Never compare a float for equality in src; make the zero stop being a case

**Why.** Floating point does not answer `==`, and the tree had stopped asking. `underwater.array_directivity_index` reintroduced one: `x == 0.0` guarded the removable singularity of `sin(x)**2 / x`, which an endfire steer reaches exactly. Writing the term as `x * sinc(x)**2` removed both the singularity and the comparison. SonarCloud's new-bugs gate also fails on a single one (S1244).

**Do**

```python
import numpy as np


def footprint(x: float) -> float:
    """sin(x)**2 / x, written so that x = 0 is not a special case."""
    return x * np.sinc(x / np.pi) ** 2


footprint(0.0)
```

**Don't**

```py
def footprint(x):
    if x == 0.0:
        return 0.0
    return np.sin(x) ** 2 / x
```

**Enforced by:** `tests/test_package_architecture.py::test_no_source_compares_a_float_for_equality`

**Exceptions.** An order comparison is not equality: a Taylor branch below a threshold (`if x < 1e-4: return 1 - x * x / 9`) is allowed and covers the exact zero too. The ways out, best first: make the zero stop being a case (an equivalent algebraic form, a subnormal term canceled by hand); close it at the door (`__post_init__`, or `<= 0.0` where the data cannot be negative); name the predicate once (`is_positive` in `phonometry._internal.validation`). The test sees `==` and `!=` with a float literal on one side only; `x == 0`, two float variables, `not x` on a float and `math.isclose(x, 0.0, abs_tol=0.0)` are the same equality in disguise, and review catches those.

<a id="x2"></a>
### X2. Settle a computed value before comparing it with a printed limit

**Why.** A standard prints its limits in decimal, and the value judged against one is usually computed: the difference of two readings, a mean, a ratio. In binary `66.1 - 60.1` is `5.999999999999993`, so `margin_db >= 6.0` refuses a margin that is 6 dB on the page, while other readings land a few units in the last place above 6 and pass. The verdict then turns on the readings, the order of a sum and the machine. The sweep that added `phonometry._internal.boundary` found more than a hundred such sites.

**Do**

```python
from phonometry._internal.boundary import settled

_MIN_BACKGROUND_MARGIN_DB = 6.0

margin_db = 66.1 - 60.1  # 5.999999999999993 in binary
background_clear = bool(settled(margin_db) >= _MIN_BACKGROUND_MARGIN_DB)
```

**Don't**

```py
background_clear = margin_db >= _MIN_BACKGROUND_MARGIN_DB  # False for 66.1 dB over 60.1 dB
```

**Enforced by:** `scripts/check_boundary_comparisons.py`, `make boundary-comparisons`, `CI: No verdict hangs on the last bits of a computed decimal`

**Exceptions.** `settled` is for a quantity of ordinary size; `settled_ratio` is for one in the caller's own unit, `settled_net_share` for a signed sum judged against zero (a canceling sum, a fit or a discriminant can land a few units in the last place either side), and the `round_half_*` helpers for a half. A named slack (`_RATIO_SLACK = 1e-12`) is the other way out; an epsilon that keeps a divisor off zero is no slack. A comparison of the refused shape that cannot sit on its limit (a level through a logarithm, a band edge at an irrational ratio) goes in `scripts/boundary_comparison_exemptions.tsv`, one line per comparison with its reason; a stale line fails. Code under `_plot` and `_report` is not scanned.

<a id="x3"></a>
### X3. Compare at a printed limit the way the source prints it, strict or inclusive

**Why.** A ratio exactly on a limit passes or fails on the comparison operator alone. Allard and Atalla print both limp-frame criteria as strict inequalities (`|K_c/K_f| < 0.05`), so a ratio on the threshold does not pass; ISO 12999-1 Formulae (4) and (5) are strict too, while a limit printed "at most" or "at least" is inclusive.

**Do**

```python
from phonometry import materials
from phonometry._internal.boundary import settled

ratio = 0.05  # |K_c/K_f| exactly on Beranek's criterion
limp = bool(settled(abs(ratio)) < materials.LIMP_FRAME_CRITERIA["beranek"])  # False
```

**Don't**

```py
limp = bool(settled(abs(ratio)) <= materials.LIMP_FRAME_CRITERIA["beranek"])  # the page prints <
```

**Enforced by:** `scripts/check_boundary_comparisons.py`, review

**Exceptions.** Read the comparison on the printed page before writing it: the checker sees whether a comparison is settled, not which way the page prints it.

<a id="x4"></a>
### X4. Name a number in a comparison, or give its `noqa` a reason

**Why.** A bare threshold in `if margin_db < 6.0:` hides which clause prints it, and the next reader cannot check it against the page. Every site in `src` was censused one by one before the rule went on.

**Do**

```python
#: ISO 3745:2012/Amd.1:2017 A.2.5: absorption coefficient of the reflecting
#: plane at most 0,06.
_MAX_PLANE_ABSORPTION = 0.06

absorption_coefficient = 0.04
plane_reflects = absorption_coefficient <= _MAX_PLANE_ABSORPTION
```

**Don't**

```py
plane_reflects = absorption_coefficient <= 0.06
```

**Enforced by:** `ruff PLR2004`

**Exceptions.** `scripts/` and `tests/` are exempt (figures lay out with bare halves; tests compare against printed oracle values). A comparison with a `str` or `bytes` value is exempt. Where a `noqa: PLR2004` stays, its reason goes on the line above, as every suppression's does ([C4](docstrings.md#c4)).

## Validating what a caller passes

<a id="x5"></a>
### X5. Make a guard that refuses non-positive values refuse NaN too

**Why.** `not x > 0.0` and `x <= 0.0` differ on NaN: the first refuses it, the second lets it through, and a NaN geometry once got past the plain form and came out in the result. SonarCloud's S1940 asks for exactly that rewrite, and following it opens the hole.

**Do**

```python
from phonometry._internal.validation import require_positive

spacing_m = require_positive(0.012, "spacing_m")
```

**Don't**

```py
if spacing_m <= 0.0:  # NaN <= 0.0 is False, so a NaN spacing passes
    msg = "'spacing_m' must be positive."
    raise ValueError(msg)
```

**Enforced by:** review

**Exceptions.** Where no shared guard fits, write `if not is_positive(x):` (`is_positive` and `is_at_most` in `phonometry._internal.validation` answer False for NaN, and a negated call gives S1940 no comparison to invert) or the explicit `if not math.isfinite(x) or x <= 0.0:`, the form `require_positive` uses, which refuses infinity too. A value already through a shared guard that refuses NaN may be compared plainly afterwards. Never apply S1940's rewrite of `not x > 0.0`.

<a id="x6"></a>
### X6. Ask a scalar parameter its rank before reading or comparing it as one number

**Why.** `float(np.array([54.0]))` is `54.0` with a `DeprecationWarning` on numpy 2.0 to 2.3 and a `TypeError` from 2.4 on, so a guard that left the refusal to `float()` or `math` took a one-element array as a number on the oldest supported numpy and refused it on the newest. ISO 354's relative humidity was found that way, by the suite run at the dependency floors.

**Do**

```python
import math

from phonometry._internal.validation import is_positive, require_scalar


def spreading_loss(distance: float) -> float:
    require_scalar(distance, "distance")
    if not is_positive(distance):
        msg = "'distance' must be positive."
        raise ValueError(msg)
    return 20.0 * math.log10(distance)
```

**Don't**

```py
def spreading_loss(distance: float) -> float:
    if float(distance) <= 0.0:  # numpy 2.0 to 2.3 read np.array([54.0]) as 54.0
        msg = "'distance' must be positive."
        raise ValueError(msg)
    return 20.0 * math.log10(distance)
```

**Enforced by:** `tests/test_scalar_guards.py::test_no_guard_in_the_tree_leaves_the_rank_to_numpy`, `tests/test_scalar_guards.py::test_every_public_scalar_parameter_refuses_an_array_or_a_text_by_name`

**Exceptions.** The rank helpers are `is_scalar`, `require_real` and `require_scalar` (`phonometry._internal.validation`); the refusal is a `TypeError` naming the parameter ([A43](api.md#a43)). The shared guards (`require_positive`, `require_finite`, `require_non_negative`, `require_above_absolute_zero`, `require_fraction`, `require_count`) ask the rank themselves: hand them the caller's value, never `float()` of it. A guard split across functions is held by the public-call probe of the second test.

<a id="x7"></a>
### X7. Read a whole-number parameter through `require_count`, never through `int()`

**Why.** `int()` truncates `2.5` to `2` without a word, takes `True` as `1` and parses `'3'`, so a count read through it accepts a fractional count, a flag and a text. `require_count` refuses the bool, the text and the array with `TypeError` and the fraction with `ValueError`, and takes a whole float such as `5.0` as `5`.

**Do**

```python
from phonometry._internal.validation import require_count

n_positions = require_count(6, "n_positions")
n_offsets = require_count(0, "n_offsets", at_least=None)
```

**Don't**

```py
n_positions = int(n_positions)
```

**Enforced by:** `tests/test_error_kinds.py::test_a_whole_number_goes_through_require_count`

**Exceptions.** The rule holds a parameter annotated `int` (or `Integral`, `np.integer`, optionally with `None`). The lower bound defaults to 1; pass `at_least=None` where the count has none.

<a id="x8"></a>
### X8. Refuse a 2-D signal in a single-channel analysis; never ravel it

**Why.** A raveled stereo signal concatenates the channels into one wrong series, and the result still looks like a level.

**Do**

```python
from phonometry._internal.validation import require_1d_signal

samples = require_1d_signal([0.0, 1.0, 0.0, -1.0], "x")
```

**Don't**

```py
x = np.asarray(x, dtype=np.float64).ravel()
```

**Enforced by:** `tests/test_multichannel_rejection.py`, review

**Exceptions.** A function that supports channels by design, such as the fractional-octave filter bank, takes them as `(channels, samples)` and says so in its docstring. The refusal names the parameter the caller passed, `x` ([A47](api.md#a47)). The test pins a list of analyses; it does not walk the API.

<a id="x9"></a>
### X9. Say in every `zip()` whether its inputs must be the same length

**Why.** A plain `zip()` stops at the shorter input without a word, so a band list one entry short of its levels drops a band. `strict=` is a judgment about the data, read one site at a time, not a formality.

**Do**

```python
pairs = list(zip([125.0, 250.0], [60.0, 55.0], strict=True))
```

**Don't**

```py
pairs = list(zip(frequencies, levels))
```

**Enforced by:** `ruff B905`

**Exceptions.** A `# noqa: B905` with its reason on the line above, where adding `strict=` would change a recorded fingerprint without changing what is computed (one site, in `scripts/figures/fields/tubes.py`).

## Arrays a result keeps

<a id="x10"></a>
### X10. Keep your own read-only copy of every array a result or object holds

**Why.** `np.asarray` and the validation helpers hand back the caller's own `float64` array, so a result that stores it shares memory with the caller, and the caller's next `levels[0] = 0.0` changes a result already computed without a sound.

**Do**

```python
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from phonometry._internal.frozen import OwnsArrays


@dataclass(frozen=True)
class DecayCurve(OwnsArrays):
    levels: NDArray[np.float64]


measured = np.array([60.0, 50.0, 40.0])
curve = DecayCurve(levels=measured)
measured[0] = 0.0  # curve.levels[0] is still 60.0, and read-only
```

**Don't**

```py
@dataclass(frozen=True)
class DecayCurve:
    levels: NDArray[np.float64]  # shares the caller's array
```

**Enforced by:** `scripts/check_array_aliasing.py`, `make array-aliasing`, `CI: Every result keeps its own copy of the arrays it was given`, `tests/test_owns_arrays.py`, `tests/test_bytearray_refusals.py`

**Exceptions.** A public record that can hold an array inherits `OwnsArrays` (`phonometry._internal.frozen`), last among its bases; it copies every array it is built with, inside a tuple, a list, a mapping or an array of objects too, and seals the copy read-only. Any other object NumPy reads as an array, through `__array__`, `__array_interface__`, `__array_struct__` or the buffer protocol (a column of a data frame, a labelled array, a `memoryview`), is read with `np.asarray` and the array that comes back is copied the same way, since it is the caller's own memory; `bytes` and a NumPy scalar stay what they are, a `bytearray` is a text as a `bytes` is and is held as the `bytes` it spells, never the caller's `bytearray` nor an array of the codes of its characters, and a record held in a field is not read. A check that names the type of a value it refuses, or quotes it, does so through `given_type` and `given_repr`, which name and quote that `bytes` as the `bytearray` the caller gave while the record's checks run, wherever the record holds it: inside a tuple, a list, a named tuple, a mapping or an array of objects as well. A `__post_init__` that takes the members out of a field a caller may give as any other sequence (a deque, a generator) reads them through `owned_members`, which copies each array the record could not reach before. A plain class stores `read_only_copy(array)`, never `read_only` of an argument, which would clear the flag on the caller's own array. A record held in a field answers for its own arrays, an `io.Signal` included, whose samples stay writeable ([A37](api.md#a37)). `RECORD_EXEMPT` (only `io.Signal`, which copies its samples itself) and `EXEMPT` at the top of the script take an entry with its reason; a stale entry fails.

<a id="x11"></a>
### X11. Hand a record its array as it is; never copy it first

**Why.** A record that inherits `OwnsArrays` copies every array it is built with, so an argument written `read_only_copy(x)`, `np.copy(x)`, `x.copy()` or `x.astype(t)` is copied twice; the guard refuses it.

**Do**

```python
import numpy as np

levels = np.asarray([60.0, 50.0, 40.0], dtype=np.float64)  # converts only when it must
decay = DecayCurve(levels=levels)  # the DecayCurve of X10 makes the one copy
```

**Don't**

```py
return DecayCurve(levels=levels.copy())
return DecayCurve(levels=read_only_copy(levels))
```

**Enforced by:** `scripts/check_array_aliasing.py`, `make array-aliasing`, `CI: Every result keeps its own copy of the arrays it was given`

**Exceptions.** A type that has to change is written `np.asarray(values, dtype=...)`, which converts only when it must. Normalize and seal inside the record's `__post_init__` with `read_only`, never with a second copy: what `__post_init__` reads back from `self` is already the record's copy. A copy the guard cannot vouch for (a helper's own return) is left alone.

<a id="x12"></a>
### X12. Use `handed_over` only for a new array the factory built and returns at once

**Why.** A result of hundreds of megabytes (the frames of a simulation, the field of a march) would be held twice while the record copies it, so `handed_over` lets the record keep that one array without a copy. The gate then has to prove from the code, with no exemption, that nothing else can reach it: the call is an argument of the record built in the `return` statement, and its name is bound once to `np.zeros`, `np.empty` or `np.ones` and otherwise only written into, tested against `None`, or passed to an undecorated package helper that does only that; anything else (a view, a second name, a closure) fails, and an array that cannot be proved alone is copied.

**Do**

```python
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from phonometry._internal.frozen import OwnsArrays, handed_over
from phonometry._internal.validation import require_count


@dataclass(frozen=True)
class Frames(OwnsArrays):
    snapshots: NDArray[np.float64]


def simulate(n_steps: int) -> Frames:
    n_steps = require_count(n_steps, "n_steps")
    snapshots = np.zeros(n_steps)
    for k in range(n_steps):
        snapshots[k] = 60.0 - k
    return Frames(snapshots=handed_over(snapshots))


simulate(8)
```

**Don't**

```py
snapshots = np.zeros(n_steps)
view = snapshots[::2]
return Frames(snapshots=handed_over(snapshots))  # a view escapes: the gate fails it
```

**Enforced by:** `scripts/check_array_aliasing.py`, `make array-aliasing`, `CI: Every result keeps its own copy of the arrays it was given`

## Units, references and precision

<a id="x13"></a>
### X13. Take the caller's unit and convert inside, keeping the source's printed constants literal

**Why.** A formula printed in kelvin (343.2 m/s at 293.15 K) stays checkable against the page when the API takes degrees Celsius ([N18](naming.md#n18)) and converts inside. The conversion is exact at the oracle points: `273.15 + 19.85` is `293.0` and `273.15 + 20.0` is `293.15` in floating point, so the oracles reproduce bit for bit.

**Do**

```python
from phonometry._internal.validation import ABSOLUTE_ZERO_C, require_above_absolute_zero


def _speed_of_sound(temperature_c: float) -> float:
    """Speed of sound 343.2 * sqrt(T / 293.15) m/s, T in kelvin as the formula prints it."""
    t = require_above_absolute_zero(temperature_c, "temperature_c")
    return 343.2 * ((t - ABSOLUTE_ZERO_C) / 293.15) ** 0.5


_speed_of_sound(20.0)
```

**Don't**

```py
def speed_of_sound(temperature_k):
    return 343.2 * (temperature_k / 293.15) ** 0.5
```

**Enforced by:** `tests/test_package_architecture.py::test_clause_poles_are_not_migrated_to_the_physical_bound`, review

**Exceptions.** A clause that prints its formula as `sqrt(273 + theta)` or `1245/(273 + t)` guards its own pole with the constant it prints (`-273.0`), not with the shared absolute zero; the test pins three such modules (`emission/_shared.py`, `emission/_sound_power_anechoic.py`, `building/measurement/intensity_insulation.py`).

<a id="x14"></a>
### X14. Read a reference value from `REFERENCE_VALUES`; never type it again

**Why.** Before the table existed, 20 µPa was typed seventeen times and 1 pW seven times, and `_P0` meant a pressure in four modules and a power in two. A copy is harmless until one is typed wrong, and then nothing says which is right.

**Do**

```python
from phonometry import metrology

p0 = metrology.REFERENCE_VALUES["gas"]["sound_pressure"].value
```

**Don't**

```py
_P0 = 2e-5  # reference sound pressure, ISO 1683
```

**Enforced by:** `scripts/check_reference_values.py`, `make reference-values`, `CI: Every reference value points at ISO 1683 or names its source`, `tests/test_check_reference_values.py::test_the_package_is_clean`

**Exceptions.** A reference that differs from the table (DIN 45672-2's 5e-8 m/s written in mm/s, ISO 226's squared reference pressure, ISO 9611's 50 nm/s) names the document it comes from in the comment above it or on its line (ISO 1683 itself does not count) and is listed in `DIFFERENT_REFERENCES` of the script with the value it holds. A bare `2e-05`, or a table value used as a logarithm's divisor or an antilogarithm's factor, is caught anywhere; a literal that is something else goes in `EXEMPT_LITERALS` with its reason. A name ending in `db` or naming a level holds a level, not a reference.

<a id="x15"></a>
### X15. Size a numerical setting until its error stops being measurable, not until it passes

**Why.** phonometry is a metrology library: a normative tolerance is a ceiling on error, not a budget to spend. Choosing the cheapest design inside the mask leaves error on the table by default; the weighting resampler once lost its antialiasing that way.

**Do**

```text
Taps: where the passband error stops being measurable, an order of
magnitude below the tightest tolerance in the corpus, shown as a curve of
error against taps. The cost is recovered by caching the design.
```

**Don't**

```text
Taps: the fewest that keep the response inside the class 1 mask.
```

**Enforced by:** review

**Exceptions.** The cost is mitigated afterwards and separately: cache deterministic designs, FFT convolution where it beats direct, the numba kernels, work shared between stages. First ask whether the cost is needed at all (an IIR filter fitted at the target rate can be both more exact and faster than oversampling a bilinear design).

## Published data

<a id="x16"></a>
### X16. Write a published record's source as `<Document> <Table>, PDF page N (printed p. M)`

**Why.** A number transcribed from a book is checkable only if the next reader can open the same page. The convention lived in review and was dropped there: one table cited a folio that prints no such number, and another credited a table with two columns it does not print.

**Do**

```python
source = "Hopkins (2007) Eq. (1.165), PDF page 108 (printed p. 81)"
```

**Don't**

```py
source = "Hopkins 2007, p. 81"
```

**Enforced by:** `scripts/check_published_sources.py`, `make published-sources`, `CI: Every published value names its page`, `tests/test_check_published_sources.py`

**Exceptions.** Several citations are joined by `; `. The folio has four forms: `printed p. N`, `printed pp. N-M`, `printed folio N`, and `no printed folio; between folios N and M` for a plate with no number; a handbook with independently paginated chapters writes N as chapter.page (`32.8`). The document must split and recompose character for character through `scripts/conformance/references.py` and have an entry in `docs/reference/bibliography.md`. The guard holds a standard (ISO, IEC, EN, DIN) to this form too: it refuses one cited by its clause or table number alone, and `docs/reference/bibliography.md` lists a standard under its publishing body, so no published record names one yet. The comment banner above a table transcribed from a standard cites it by its number ([D13](docstrings.md#d13)).

<a id="x17"></a>
### X17. Keep a packaged catalogue as strict JSON that cites its source, with unique keys

**Why.** A catalogue is the one place a wrong character is invisible: a row whose key was typed twice or whose citation was dropped imports cleanly and is quietly missing a material. The published tables are read from JavaScript too, which refuses NaN and Infinity, and JSON silently keeps the last of a name written twice. So the reader (`phonometry._internal.catalogue`) refuses at import a file that is not one JSON object, a missing or unknown top-level key (`source`, `about` and `rows` are required, `conventions` and `validity` optional), an empty table, a row without a key, a key that is not text or holds a `/` (it separates table from row in every catalogue key), two rows sharing a key, a name written twice in one object, NaN and infinities; and a data file is JSON, never Python, in UTF-8 with a final newline.

**Do**

```json
{
  "source": "Bies 5e Table 5.1, PDF page 256 (printed p. 227)",
  "about": "What the page prints and how its columns map to the fields.",
  "rows": [
    {"key": "sugar_snow", "name": "Sugar snow", "ranges": {"flow_resistivity_pa_s_m2": [25000.0, 50000.0]}}
  ]
}
```

**Don't**

```json
{"source": "Bies 5e", "rows": [{"key": "grass/turf", "flow_resistivity_pa_s_m2": NaN}, {"key": "grass/turf"}]}
```

**Enforced by:** `tests/test_internal_catalogue.py`

<a id="x18"></a>
### X18. Write a catalogue number as printed, and say in words why a cell is empty

**Why.** One field did two jobs: hundred-character sentences landed in the numeric columns of the published page, and dropping an `unquantified` let the library publish a 4265 m/s bar speed for a honeycomb panel that has none. A modulus typed `0.82e10` reads back as `8199999999.999999` and was published with sixteen digits; `8.2e9` round-trips.

**Do**

```json
{
  "unquantified": {"loss_factor": "Varies with frequency"},
  "not_derivable": {"bar_longitudinal_speed_m_s": "a one-dimensional speed does not mean anything in a honeycomb panel"}
}
```

**Don't**

```json
{
  "unquantified": {"loss_factor": "the page gives no value because the loss factor varies with frequency"},
  "youngs_modulus_pa": 0.82e10
}
```

**Enforced by:** `tests/test_internal_catalogue.py::test_no_number_carries_more_digits_than_a_page_prints`, `tests/test_internal_catalogue.py::test_an_unquantified_cell_holds_what_the_page_printed`, `tests/test_internal_catalogue.py::test_a_not_derivable_cell_says_why_in_words`, `tests/test_internal_catalogue.py::test_a_misprinted_cell_says_what_the_page_printed_and_why_it_cannot_be`

**Exceptions.** A number carries at most nine significant figures. `unquantified` holds what the page printed instead of a number, in at most 32 characters (`Varies with frequency`); `not_derivable` is the sentence, longer than 32 characters, saying why the library leaves the cell empty. Both stop the derivation. `misprinted` quotes what the page prints, points at `docs/ERRATA.md`, and the field it hedges holds no number.

<a id="x19"></a>
### X19. Publish both values when two printed sources disagree; never vote by majority

**Why.** Tin: Cremer and Mechel print a Young's modulus of 4.4 GPa and Bies prints 54 GPa, with the densities agreeing within 0.3 %. Each book reproduces its own printed wave speeds from its own figure, so it is a disagreement between books, not an errata; and the accepted value is about 50 GPa, so the two that agree are the wrong ones.

**Do**

```python
from phonometry import solids

tin = solids.solids_named("tin")  # every book's row, 4.4 GPa and 54 GPa side by side
```

**Don't**

```py
TIN_YOUNGS_MODULUS_PA = 4.4e9  # two books against one
```

**Enforced by:** `scripts/check_solid_agreement.py`, `scripts/check_shared_sources.py`, `make solid-agreement`, `make shared-sources`, `CI: The books agree about the solids they share`, `tests/test_check_solid_agreement.py`

**Exceptions.** A density two books print more than 8 % apart is read as a transcription error and fails; a disagreement that is the books' own goes in `ACCEPTED` of `scripts/check_solid_agreement.py` with its reason read from both pages (polypropylene, and the polystyrene, polyurethane and PVC that one book prints as foams). Moduli and speeds that differ between books are reported, never failed. An errata needs a page that contradicts itself, so a disagreement between books never enters `docs/ERRATA.md`.

<a id="x20"></a>
### X20. Rename a catalogue field in its data, spec, schema, baseline and translations together

**Why.** A catalogue row field is a column of a versioned file format users write; renaming it in the code alone breaks every catalogue already written and the published schema.

**Do**

```text
key renamed in src/phonometry/<domain>/data/*.json and in scripts/generate_catalogue_data.py,
then: make catalogue-data catalogue-schema, the baseline and catalogue-es.json updated
```

**Don't**

```text
key renamed in src/phonometry/<domain>/data/*.json only
```

**Enforced by:** `tests/test_published_catalogue_fingerprint.py::test_every_published_row_is_the_baseline_carried_through_the_changes`, `make catalogue-data`, `make catalogue-schema`

**Exceptions.** The pieces: the key in `src/phonometry/**/data/*.json`, the column spec in `scripts/generate_catalogue_data.py`, the regenerated site catalogues and published schema, `tests/data/published_catalogues/baseline.json`, and the Spanish catalogue strings in `site/src/data/catalogue-es.json` ([P5](prose.md#p5)).

## Fields an engine steps

<a id="x21"></a>
### X21. Touch an engine's field only with Array API standard operations

**Why.** The FDTD engines step on NumPy, CuPy and torch from one code. A NumPy-only call on a field (`div.fill(0.0)`, `np.divide(where=, out=)`, two index arrays at once) works on NumPy and breaks on a GPU, or quietly copies the field to the host and back every step.

**Do**

```python
import numpy as xp  # stands for the engine's namespace: NumPy's, CuPy's or torch's

p = xp.zeros((4, 5))
div = xp.ones((4, 5))
flat_index = xp.asarray([0, 7, 13])

div[...] = 0.0
values = xp.take(xp.reshape(p, (-1,)), flat_index)
```

**Don't**

```py
div.fill(0.0)
values = p[rows, cols]
```

**Enforced by:** `CI: FDTD engines on array-api-strict and torch (CPU)`, `CI: FDTD engines hold their golden digests`, `make engine-digests`, `tests/simulation/test_engine_golden_digests.py`, `tests/simulation/test_gpu_parity_lock.py`

**Exceptions.** The maps are built on the host in NumPy float64 when the engine is constructed and handed to the backend once; that code may use any NumPy call. Every method that reads or writes a field after that uses only the standard, in the order of operations the NumPy path had, with no fused kernels. The `array-api` job steps every scenario of `scripts/engine_scenarios.py` on array-api-strict, which refuses a call outside the standard and a NumPy call on a device array. The `engine-digests` job holds the NumPy path bit for bit to `engine-digests.json`, the SHA-256 digests of every array those scenarios return and the exact energy of the elastic engine's fluid branch at five seeds (the fluid-energy record), taken from the engines before they could step anywhere else (`make engine-digests` compares here, or takes a moved measurement from that job when the move is meant). The lock test fails when an engine file changes without a new CuPy proof (`make gpu-parity` on a GPU).
