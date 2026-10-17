← [Documentation index](../README.md)

# Naming

This page governs every name phonometry gives: modules, classes, exceptions and warnings, functions, parameters and record fields, published and private constants, and the words, units and spelling those names are made of. Read it before you add or rename a public name, a parameter or a constant, and whenever a review cites an N rule. How a signature is shaped (order, keyword-only arguments, choices, returns) is on [API shape](api.md), and how a test file is named is on [Tests](tests.md).

<a id="n1"></a>
### N1. Name a module for its subject in words, never for a standard's designation

**Why.** A reader looks for a module by what it computes, and an edition can change without a rename, so the designation lives in the module docstring ([D1](docstrings.md#d1)). The subject fits in at most four words, as every public module's does. A reference page titled `tonality (ECMA-418-2)` ranked almost level with the guides written to that standard in the site search.

**Do**

```text
src/phonometry/hearing/noise_induced_hearing_loss.py
src/phonometry/emission/sound_power.py
```

**Don't**

```text
src/phonometry/hearing/iso1999.py
```

**Enforced by:** `tests/test_api_docs_generator.py::test_no_page_title_carries_a_number`, review

**Exceptions.** Private fiche modules under `src/phonometry/_report/` are named for the standard their fiche implements (`iso717.py`) and are not held to it. The reference page of a private module is titled by its domain and subject in words (`signals: correlation`) and says which package its names are imported from.

<a id="n2"></a>
### N2. Make a module private when a function of its package takes its name

**Why.** `signals/correlation.py` sat beside `signals.correlation()`, so `import phonometry.signals.correlation` bound the function, `signals.correlation.time_delay` raised `AttributeError`, and the API reference still had a page at that address. Thirty-one modules were hidden this way. The private module follows PEP 8, `numpy._core` and SciPy since 1.8: its names are reached through the package (`signals.time_delay`).

**Do**

```text
src/phonometry/signals/_correlation.py, its names reached as phonometry.signals.<name>
```

**Don't**

```text
src/phonometry/signals/correlation.py beside the published function signals.correlation
```

**Enforced by:** `scripts/check_api_reference.py`, `tests/test_removed_names.py::test_a_module_hidden_behind_its_function_is_private`, `CI: Curated API quick table covers __all__`

<a id="n3"></a>
### N3. Give every top-level name a module keeps for itself a leading underscore

**Why.** A bare name reads as public to every reader and every tool, ends up in a guide or a script through the full module path, and then cannot be renamed without breaking it. What the module does publish is listed in its `__all__` ([A2](api.md#a2)).

**Do**

```python
_OCTAVE_BANDS = (125.0, 250.0, 500.0, 1000.0)


def _warn_above_plane_wave_limit(frequency: float) -> None: ...
```

**Don't**

```py
OCTAVE_BANDS = (125.0, 250.0, 500.0, 1000.0)  # read by this module only, missing from __all__
```

**Enforced by:** `scripts/check_api_reference.py`, `CI: Curated API quick table covers __all__`

**Exceptions.** Typing constructs (a type alias, a `TypeVar`, a `Protocol`) stay PascalCase, unlisted and unprefixed. A rare public-looking name may go in `UNLISTED_EXEMPTIONS` of `scripts/check_api_reference.py`, keyed by location with its reason.

<a id="n4"></a>
### N4. Name a result class `<Concept>Result` for what its function returns

**Why.** One suffix tells a caller which class a function returns. `EnclosureResult` was what `enclosure_insertion_loss` returned, beside `EnclosureInsulationResult`, and the two names did not say which was which.

**Do**

```python
from phonometry import noise_control

noise_control.EnclosureInsertionLossResult
```

**Don't**

```py
class EnclosureResult: ...  # returned by enclosure_insertion_loss
```

**Enforced by:** review

**Exceptions.** The psychoacoustic `<Method><Metric>` family is sanctioned (`ZwickerLoudness`, `EcmaLoudness`), and value and input objects take a plain name (`Quantity`, `Fluid`). A verdict record takes its family's noun, as the existing verdicts do: a `check_` returns a `<Concept>Check`, a `verify_` a `<Concept>Verification` or a compliance `<Concept>Result`, an `assess_` a `<Concept>Assessment`.

<a id="n5"></a>
### N5. Write an acronym in capitals in a class name

**Why.** `HtlanResult`, `AnpAircraft` and `DbHrCheck` sat beside `STIResult`, `EPNLResult` and `ZoomFFTResult`, so a caller had to remember which spelling each class used.

**Do**

```python
from phonometry import aircraft, hearing

aircraft.ANPAircraft, hearing.HTLANResult
```

**Don't**

```py
class HtlanResult: ...
class AnpAircraft: ...
```

**Enforced by:** `tests/test_public_vocabulary.py::test_an_acronym_is_written_in_capitals`

**Exceptions.** Ecma keeps its spelling (`EcmaLoudness`): Ecma International spells its own name so, and it is not an acronym (`_PROPER_NAMES` of the test). The acronyms are the curated `_ACRONYMS` of the test plus any run of capitals another public class writes. Ruff's N naming rules are not selected (they would rename the standards' symbols; only N812, on import aliases, is), so this test is the only enforcer.

<a id="n6"></a>
### N6. Name an exception `<Topic>Error` and a warning `<Topic>Warning`

**Why.** `fluids.FluidPropertyUnavailable` was the one published exception without the suffix, beside `CatalogueError`; in an `except` clause a reader could not tell it from a value (PEP 8). A warning class named for its topic is what a filter names; the class it derives from is [A49](api.md#a49).

**Do**

```python
from phonometry import fluids, io, room

io.CatalogueError, fluids.FluidPropertyUnavailableError, room.AuditoriumWarning
```

**Don't**

```py
class FluidPropertyUnavailable(AttributeError): ...
class AuditoriumNotice(PhonometryWarning): ...
```

**Enforced by:** `tests/test_package_architecture.py::test_every_published_exception_is_named_an_error`, `tests/test_package_architecture.py::test_every_published_warning_is_a_phonometry_warning`

**Exceptions.** An exception subclasses the built-in it refines, so the `except` a caller already writes still catches it: `CatalogueError(ValueError)`, and `FluidPropertyUnavailableError(AttributeError)`, which keeps `hasattr` and `getattr` with a default working.

<a id="n7"></a>
### N7. Name a function for the quantity it returns; keep a verb for an action

**Why.** `combine_linings`, `combine_subareas` and `combine_age_and_noise` returned numbers under verb names, and the same root-sum-square had three names in three packages.

**Do**

```python
from phonometry import vibration

vibration.combined_daily_exposure
```

**Don't**

```py
combine_partial_exposures(...)
get_daily_exposure(...)
calculate_daily_exposure(...)
```

**Enforced by:** review

**Exceptions.** A verb stays where the function acts (`apply_weighting`), merges objects (`combine_fault_lines`, `combine_duct_paths`) or judges (`verify_`, `assess_`, `check_`, see [N9](#n9)). No public name starts with `get_`, `calculate_` or `compute_`. Where the bare noun would collide with another function or claim more than the function computes, it takes its family's prefix (`silencer_sound_power_level`).

<a id="n8"></a>
### N8. Leave `_db` and `_hz` off a function name; keep a unit where two compete

**Why.** Thirty-five functions were named for the unit of their answer, and `air_attenuation_m` returned a coefficient in 1/m, not a length. The prefix of `screen_background_corrected_level` is [N7](#n7)'s: a bare name that would collide takes its family's.

**Do**

```python
from phonometry import noise_control

noise_control.screen_background_corrected_level
```

**Don't**

```py
background_corrected_level_db(...)
air_attenuation_m(...)
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_every_public_function_is_named_for_what_it_returns`

**Exceptions.** A unit stays where the quantity has more than one customary unit (`peak_velocity_from_kb_mm_s`, `admissible_exposure_s`, `air_power_attenuation_per_m`). A method that reads a printed row's columns, or returns a quantity the record also holds in another unit, goes in `FUNCTION_UNIT_EXEMPT` of the guard, keyed by (module, qualified name) with its reason (`WindowMetricsResult.enbw_hz` sits beside the `enbw_bins` its record holds).

<a id="n9"></a>
### N9. Name a judgment `verify_` for an instrument, `assess_` for a situation, `check_` for a setup

**Why.** The three verbs are not interchangeable: `verify_weighting` asks whether a meter's filter meets ISO 8041-1, `check_source_positions` whether a measurement had enough loudspeaker positions for its clause to apply; both may fail, and only the first is about equipment. What a judgment returns is [A39](api.md#a39).

**Do**

```python
from phonometry import noise_control, vibration

vibration.verify_weighting  # an instrument: a meter's weighting filter
vibration.assess_building_vibration  # a situation: a measured peak velocity against its guideline value
noise_control.check_source_positions  # a setup: the positions the method needs
```

**Don't**

```py
check_weighting(...)  # judges a meter's filter, an instrument
verify_source_positions(...)  # judges the measurement setup
```

**Enforced by:** `tests/test_verdict_shape.py::test_every_judgement_is_named_with_its_verb`, `tests/test_verdict_shape.py::test_every_judging_method_is_named_with_its_verb`, review

**Exceptions.** A predicate that only selects which procedure a clause applies answers no pass or fail, keeps its verb and returns a `bool` (`low_frequency_procedure_applies`, `resolve_tones_separately`, listed in `REGIME_PREDICATES` of the test with their reason). A method that tests membership or provenance, looks up one requirement of a verdict, or says how a value is reported goes in `PREDICATE_METHODS`, keyed by location with its reason. The tests prove that a judgment carries one of the three verbs; which verb fits is review.

<a id="n10"></a>
### N10. Never start a public function or class name with `test` or `Test`

**Why.** pytest collects every function named `test*` and every class named `Test*` from a module a test file imports, so `from phonometry.noise_control import *` in a user's test file collected `test_environment_applicability` and failed on a fixture it never asked for.

**Do**

```python
from phonometry import noise_control

noise_control.check_enclosure_test_environment
```

**Don't**

```py
test_environment_applicability(...)
```

**Enforced by:** `tests/test_verdict_shape.py::test_no_public_name_is_collected_by_pytest`

**Exceptions.** Upper-case constants (`TEST_REPORT_ITEMS`, `TEST_RUNS`) are not collected by pytest and are not held to it, nor is a field or a method of a class whose name does not start with `Test` (`Provenance.test_standard_of`). A module named `test_*.py` is collected from the repository root, but pytest finds nothing to run in `signals.test_signals`.

<a id="n11"></a>
### N11. Name a catalogue lookup `<x>_named` after its `PUBLISHED_<X>`, and take `catalogue=`

**Why.** `duct_wall_named` searched the duct transmission loss catalogue, so its name did not say which table it read; and a lookup that searches only the published table cannot search the caller's own catalogue, read from a file or joined with the published one by `|`.

**Do**

```python
from phonometry import materials

materials.porous_materials_named, materials.PUBLISHED_POROUS_MATERIALS
```

**Don't**

```py
duct_wall_named(...)
PUBLISHED_AIR
```

**Enforced by:** `tests/io/test_catalogue_lookups.py::test_a_lookup_is_named_after_the_catalogue_it_searches`, `tests/io/test_catalogue_lookups.py::test_every_lookup_the_packages_publish_takes_a_catalogue`, `tests/io/test_catalogue_lookups.py::test_the_table_here_lists_every_lookup_the_packages_publish`

**Exceptions.** `PUBLISHED_` names a mapping of rows only; a single published object is named for its role (`ABSORBER_AIR`, `SIMULATION_AIR`). A lookup answers every match as a tuple, in the order the mapping holds them, and never picks one. A new lookup is added to `LOOKUPS` in the test.

<a id="n12"></a>
### N12. Name each concept with the one word the library already uses for it

**Why.** A sample rate was `fs` in 165 places and `fs_hz` or `sample_rate_hz` in the newest modules, and a band axis went by six names, so code written against one module had to be relearned for the next. The vocabulary: `fs`, `x`, `frequencies`, `levels`, `times`, `distances`, `speeds_of_sound`, `volume`, `coverage` for a coverage probability, `confidence` for an interval, `weighting`, `fraction`, `energy_fraction`.

**Do**

```python
import numpy as np
from phonometry import filters

fs = 48000
x = np.zeros(fs)
result = filters.octave_filter(x, fs)
bands = result.frequencies
```

**Don't**

```py
result = filters.octave_filter(signal, sample_rate_hz)
bands = result.band_centers
```

**Enforced by:** `tests/test_public_vocabulary.py::test_one_concept_is_spelled_one_way`, `tests/test_public_vocabulary.py::test_every_kept_minority_spelling_still_exists`

**Exceptions.** The retired spellings are the `_MINORITY` table of the test (`sample_rate` and `fs_hz` for `fs`; `freqs` and `band_centers` for `frequencies`; `sound_speed` for `speed_of_sound`; `passed` for `passes`; `band_type` for `fraction`; `curve` for `weighting`; and more). A minority spelling is kept only in `_MINORITY_EXEMPT`, keyed by location with its reason, and an entry that matches nothing fails: the aircraft NPD `distances_m` (tables printed in feet), the underwater `frequencies_hz` (formulas printed in kHz), `BandAveragedStiffness.center_frequencies`.

<a id="n13"></a>
### N13. Name the time signal `x`, as the first parameter

**Why.** Thirty functions took the time signal as `signal` or `signal_in` while `octave_filter(x, fs)` took `x`, and their error messages named a parameter the caller had not written.

**Do**

```python
import numpy as np
from phonometry import filters

x = np.zeros(48000)
result = filters.octave_filter(x, 48000)
```

**Don't**

```py
def thd(signal, fs): ...
def loudness_ecma(signal_in, fs): ...
```

**Enforced by:** `tests/test_public_vocabulary.py::test_the_time_signal_is_x`

**Exceptions.** A record field that holds an output signal keeps `signal` (`EnvelopeResult.signal`). Two signals are named by role (`x` and `y`; `p1` and `p2`; `incident_ir` and `reflected_ir`; `clean` and `degraded`), and an impulse response is `ir`. The test refuses the names `signal` and `signal_in`; it does not check the position.

<a id="n14"></a>
### N14. Name a parameter `speed_of_sound` or `density`, never by its symbol `c` or `rho`

**Why.** A bare `c` or `rho` at a call site reads as any number, while the API spells the quantity out everywhere else.

**Do**

```python
def impedance(density: float, speed_of_sound: float) -> float:
    return density * speed_of_sound
```

**Don't**

```py
def impedance(rho, c): ...
```

**Enforced by:** `tests/test_public_vocabulary.py::test_a_symbol_is_not_a_parameter_name_outside_the_solvers`

**Exceptions.** The simulation package is exempt as a whole: its solvers take maps of the symbols their equations are written in (`c`, `rho`, `c_p`, `c_s`, `dx`). One parameter elsewhere is kept by location with its reason in `_SYMBOL_EXEMPT` of the test: the downstream amplitude `C` of ASTM E2611-19 in `four_microphone.face_quantities`.

<a id="n15"></a>
### N15. Name an array in the plural; a singular vectorized name says it takes either

**Why.** Thirteen functions took a band axis as `level=` or `frequency=`, and 34 vectorized parameters did not say whether they take one value or many, so a caller could not tell what to pass.

**Do**

```python
import numpy as np
from numpy.typing import ArrayLike


def energy_mean(levels: ArrayLike) -> float:
    """Energy mean of ``levels``, in dB."""
    return float(10 * np.log10(np.mean(10 ** (np.asarray(levels) / 10))))
```

**Don't**

```py
def energy_mean(level: ArrayLike) -> float: ...
```

**Enforced by:** `tests/test_public_vocabulary.py::test_an_array_of_a_quantity_is_named_in_the_plural`

**Exceptions.** A vectorized evaluator keeps its singular name when its `:param` text says it takes one value or many, `(scalar or array)` (the porous models' `frequency`). A unit suffix does not change the rule (`frequency_hz` holding a band axis is a singular array).

<a id="n16"></a>
### N16. Put a unit in a name wherever two customary units compete for the quantity

**Why.** A number the caller types is where a unit is lost, silently: a static pressure of `101325` handed to a function that wants kilopascals is a thousand atmospheres, and every result is still a float. No guard on magnitude can catch it, because both readings are legitimate elsewhere in the library. A band axis is the other way round: `frequencies`, `levels`, `times` and `distances` are one word each across the library, and a suffix would give the same field a second spelling.

**Do**

```python
from phonometry import fluids

air = fluids.air(temperature_c=20.0, static_pressure_pa=101325.0, relative_humidity_percent=50.0)
```

**Don't**

```py
atmospheric_absorption(100.0, temperature=15.0, humidity=70.0, pressure=101.325)
result.frequencies_hz  # a band axis carries no unit
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py`, `tests/test_public_vocabulary.py::test_one_concept_is_spelled_one_way`

**Exceptions.** The quantities that compete are the ones `scripts/check_parameter_units.py` lists (pressure, temperature, humidity, diameter, angle, period, gradient, molar mass, thickness, spacing, height, phase, speed, attenuation rates; distance inside `aircraft`). A name built on one of them may instead end in a suffix that says it has no unit of its own (`pressure_ratio`, `temperature_correction`: `_level`, `_index`, `_ratio`, `_coefficient`, `_correction`, `_uncertainty`); a quantity in decibels follows [N23](#n23) and [N24](#n24). A `bool` parameter is outside the rule. Anything else goes in `EXEMPT` of the guard, keyed by (module, qualified name, parameter) with its reason (acoustic waveforms, ratios of two figures in any unit); a stale entry fails. The guard refuses no unit on any other name: a single frequency keeps `frequency_hz`, and the underwater ones read formulas printed in kHz. A band axis carries none ([N12](#n12)), except two second units: `distances_m` in `aircraft` (NPD tables in feet) and `frequencies_hz` in `underwater` (formulas in kHz).

<a id="n17"></a>
### N17. Spell each unit suffix one way: `_deg`, `_s`, `_minutes`, `_hours`, `_kmh`, `_kt`

**Why.** `phase_tolerance_degrees` sat beside `_deg`, a trailing `_h` meant hours on one name and henries on `inductance_h`, `_min` read as a minimum in `assessment_period_min`, and `subject_m` read as meters. One spelling per unit: `_deg`, `_rad`, `_s`, `_minutes`, `_hours`, `_kmh`, `_kt`, `_db_per_s`.

**Do**

```python
def exposure(duration_s: float, angle_deg: float, period_hours: float) -> float:
    return duration_s * angle_deg * period_hours
```

**Don't**

```py
def exposure(duration_seconds, angle_degrees, period_h): ...
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_spells_every_unit_one_way`, review

**Exceptions.** The retired spellings the guard refuses are `_degrees`, `_seconds`, `_km_h`, `_db_s`, `_knots` and an `_h` that means hours. An `_min` that means minutes is retired too (`_min` is a minimum): the guard reports it on a period or another quantity it lists (`assessment_period_min` names no unit), and on any other duration it is review. A name that means something else by the suffix goes in `SPELLING_EXEMPT` of the guard with its reason (`inductance_h` is the henry). An hour or a minute that ends a compound rate is a denominator and stays (`_mm_h`, `_ft_per_min`).

<a id="n18"></a>
### N18. Name every public temperature in degrees Celsius, ending `_c`

**Why.** `GasStream(inlet_temperature_k=450.0)` renamed to `_c` with the number kept made the gas 273.15 K hotter without an error. With 29 of 31 public temperatures already in degrees Celsius, the other two moved to Celsius rather than keeping a kelvin name: one scale, without exceptions. The guard demands a temperature unit and accepts `_k`, so the Celsius half is review.

**Do**

```python
from phonometry import environment

attenuation = environment.air_attenuation([1000.0], temperature_c=10.0, relative_humidity_percent=70.0)
```

**Don't**

```py
fluids.air(temperature_k=293.15)
```

**Enforced by:** `scripts/check_parameter_units.py`, review

<a id="n19"></a>
### N19. Name the pressure of the medium `static_pressure_pa` or `static_pressure_kpa`

**Why.** The absolute pressure of the medium had five names: `static_pressure_kpa`, `atmospheric_pressure_kpa`, `atmospheric_pressure_pa`, `barometric_pressure_pa` and `ambient_pressure_pa`.

**Do**

```python
from phonometry import materials

density = materials.air_density_iso10534(temperature_c=23.0, static_pressure_kpa=101.325)
```

**Don't**

```py
def air_density(temperature_c, ambient_pressure): ...
def speed_of_sound(temperature_c, barometric_pressure_hpa): ...
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_pressure_of_the_medium_has_one_stem`

**Exceptions.** Each function keeps the pascal or kilopascal its clause prints. `atmospheric_pressure_pa` names only the outside atmosphere, where the same signature also takes a stream pressure (`ATMOSPHERIC_ADMITTED` of the guard: `pipe_transmission_loss`, `normal_air_density` and others).

<a id="n20"></a>
### N20. End a rate per distance in `_db_per_m`, `_db_per_km` or `_per_m`

**Why.** An attenuation in dB/m, dB/km or Np/m differs by orders of magnitude for one number, and an `absorption_coefficient` in dB/km beside the dimensionless absorption coefficient of a wall reads as the wall's.

**Do**

```python
def air_loss(distance_m: float, air_absorption_db_per_m: float) -> float:
    return distance_m * air_absorption_db_per_m
```

**Don't**

```py
def air_loss(distance_m, absorption_coefficient): ...  # documented in dB/km
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_holds_every_closing_rule`

**Exceptions.** The guard holds a name that says absorption, attenuation or coefficient and whose docstring gives a unit per distance. A name that is not a rate goes in `RATE_EXEMPT` of the guard with its reason.

<a id="n21"></a>
### N21. Never publish one name both bare and with its unit in one subpackage

**Why.** A subpackage where `thickness` and `thickness_m` are both public makes the caller guess whether the bare one is in meters. Keep the unit where a second unit competes for the word ([N16](#n16)), and otherwise pick one spelling for the subpackage.

**Do**

```python
def layer(thickness_m: float, spacing_m: float) -> float:
    return thickness_m + spacing_m
```

**Don't**

```py
def layer(thickness_m): ...
def plate(thickness): ...  # same subpackage, same quantity
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_holds_every_closing_rule`

**Exceptions.** Two different quantities under one word (a subscript such as `r_w` beside a watt, `l_n` beside newtons, an A-weighted figure beside the band one) go in `PAIR_EXEMPT` of the guard with their reason. A frequency is the one quantity kept both ways on purpose: the bare word is a result's stated frequency or a vectorized argument, `frequency_hz` the scalar argument ([N16](#n16)), and the pair is listed there for each subpackage that has both.

<a id="n22"></a>
### N22. Make every defaulted unit-named parameter and every medium condition keyword-only

**Why.** A unit in the name helps only if the name appears at the call: with a default and a positional slot the number is written bare, and `ground_attenuation(200, 2, 2, bands, 1, 1, 1)` or `sound_exposure(x, fs, 8.0, cal)` reads as a row of numbers in an order nobody remembers. A frequency axis and a record a caller builds are taken by keyword too ([A17](api.md#a17), [A18](api.md#a18)).

**Do**

```python
from phonometry import environment

attenuations = environment.atmospheric_absorption(100.0, temperature_c=15.0, relative_humidity_percent=70.0)
```

**Don't**

```py
def absorption(distance, temperature_c=20.0, speed_of_sound=343.0): ...

absorption(100.0, 15.0, 340.0)
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_every_condition_on_the_tree_is_written_by_name`, review

**Exceptions.** The conditions of the medium and of the measuring chain are held to it whatever their suffix (`speed_of_sound`, `air_density`, `air_sound_speed`, `water_density`, `calibration_factor`, the ground factors; `CONDITIONS` of the guard). The first parameter is not held to it, nor an option (`mode`, `method`, `fraction`, `n`, `seed`), nor a condition the call cannot do without (`tube_wavenumber(frequency, speed_of_sound)`). A dataclass field uses `KW_ONLY`. A signature that must stay positional goes in `POSITIONAL` of the guard with its reason (`metrology.sensitivity(reference_pressure_pa)`, part of the `Signal` overload contract). The guard holds the conditions and the parameters that name a quantity of [N16](#n16); any other defaulted parameter that ends in a unit is review.

<a id="n23"></a>
### N23. Leave `_db` off a level or a level difference; keep it on other decibel quantities

**Why.** About 400 names ended in `_db` beside as many that did not, often the same concept in two modules (`background_levels_db` and `background_levels`, `insertion_loss_db` and `insertion_loss`). The head noun decides: a level, loss, insulation, reduction, difference, improvement, correction, adjustment, index or emergence carries no `_db`; a tolerance, margin, limit, uncertainty, deviation, step, slope, rate or ratio keeps it.

**Do**

```python
def correct(levels: list[float], background_levels: list[float], fixture_uncertainty_db: float) -> list[float]:
    return [a - b + fixture_uncertainty_db for a, b in zip(levels, background_levels, strict=True)]
```

**Don't**

```py
def correct(levels_db, background_levels_db, fixture_uncertainty): ...
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_no_level_carries_a_unit_suffix`

**Exceptions.** The head noun is the last noun once trailing qualifiers are set aside (`_1000`, `_a`, `_before`, `_with`, `_max`). Level nouns: level, loss, insulation, isolation, reduction, rejection, difference, improvement, single-value attenuation, correction, adjustment, index, emergence, the ISO 717 adaptation term, and a shift, increase, decrease or excess of a named level; also a printed symbol of one (`l_n`, `delta_lw`; `kij` in `building`, `max_k3` in `emission`). A drop, rise, change or increment of a named level is one too (`level_drop`); a bare `shift` or `drop_db` names no level and keeps its unit, and in `materials` an `l1` is the length of ASTM E2611, not a level. A tolerance, margin, uncertainty, deviation, step, slope (`_db_per_decade`), rate (`_db_per_m`) or ratio keeps `_db`, and so does a statistic of a level (`sigma_level_db`: a leading `sigma_` or `u_` says it). A difference or a loss of another quantity keeps that quantity's unit (`phase_difference_deg`; a pressure loss is in pascals). `LEVEL_SUFFIX_EXEMPT` of the guard lists, with its reason, a name that holds something else under the word.

<a id="n24"></a>
### N24. Give a name in decibels the noun of its quantity, never qualifiers plus `_db`

**Why.** `corrected_db`, `floor_db`, `threshold_db` and `mean_db` said the unit and not the number: a caller could not tell a level from an uncertainty or a margin.

**Do**

```python
def hearing_threshold(threshold_level: float, *, expanded_uncertainty_db: float) -> float:
    """The threshold level, in dB, with its expanded uncertainty."""
    return threshold_level
```

**Don't**

```py
def hearing_threshold(threshold_db, floor_db): ...
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_every_name_in_decibels_says_its_quantity`

**Exceptions.** A level takes the noun that says so and then loses its `_db` (`corrected_levels`, `threshold_level`), a level difference takes its own (`floor_level_difference`), and any other quantity keeps `_db` after its noun (`fixture_uncertainty_db`, `lower_tolerance_db`). The nouns read as a quantity are `DECIBEL_QUANTITY_NOUNS` of the guard; `QUALIFIER_ONLY_EXEMPT` lists, with its reason, a name whose `_db` is not the unit of a number it holds (a flag, a printed symbol, the DB HR of the Spanish building code).

<a id="n25"></a>
### N25. End a published constant's name in its unit unless it is a pure number

**Why.** A constant is a number nobody types, so the unit lost is the one a reader assumes: a reference speed of 70 is km/h in CNOSSOS-EU while other speeds are in m/s or kt, and a reference velocity of 5e-8 is m/s only to a reader with the docstring open.

**Do**

```python
from phonometry import fluids

static_pressure = fluids.DEFAULT_STATIC_PRESSURE_PA
```

**Don't**

```py
ROAD_REFERENCE_SPEED = 70.0
UNIVERSAL_GAS_CONSTANT = 8314.0
```

**Enforced by:** `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_every_published_constant_says_its_unit`

**Exceptions.** A single number ends in its unit, in the one spelling each unit has (`_HZ`, `_M_S`, `_KMH`, `_KT`, `_DEG`, `_S`, `_HOURS`), or in `_DB` when it is in decibels and its head noun does not say so (a tolerance, a margin); a constant named for a level carries none (`EARPHONE_ATTENUATION`). A factor, a fraction or a ratio carries none. A table ends in its unit when its name names a quantity (`NOY_BANDS_HZ`). A count, a label or a pure number goes in `CONSTANT_EXEMPT` of the guard, keyed by (module, name) with its reason.

<a id="n26"></a>
### N26. Name a private constant `_UPPER_SNAKE`, and a transcribed table after its printed table

**Why.** A private table named for where it is printed can be checked against the page, and the leading underscore keeps it out of the public API.

**Do**

```text
_TABLE1   Table 1 of ISO 12999-1, in building/measurement/uncertainty.py
_UVL0     the columns u, v and L0 of Table 1 of ISO 1999, in hearing/noise_induced_hearing_loss.py
```

**Don't**

```text
table1, _table_1, TABLE1 (public by accident)
```

**Enforced by:** review

**Exceptions.** A private constant that is not a transcription is named for its content (`_OCTAVE_BANDS`).

<a id="n27"></a>
### N27. Delete a private constant nothing reads

**Why.** A private constant nobody reads is a leftover, or the trace of a check its docstring still promises: the sweep that created this guard found a recommended specimen velocity the code carried and never checked, and a docstring promising a default the code did not take.

**Do**

```python
_MAX_SPECIMEN_VELOCITY_M_S = 0.5


def specimen_velocity_margin(velocity_m_s: float) -> float:
    return _MAX_SPECIMEN_VELOCITY_M_S - velocity_m_s
```

**Don't**

```py
_MAX_SPECIMEN_VELOCITY_M_S = 0.5  # defined, cited in a docstring, never compared
```

**Enforced by:** `scripts/check_dead_constants.py`, `make dead-constants`, `CI: No private constant goes unread`

**Exceptions.** A name counts as read when it is loaded, used as an attribute, imported or named in a string anywhere in `src`, `tests` or `scripts`. `KEPT` in the script takes a constant, keyed (module, name), with its reason, and nothing belongs there that could be used instead. A constant kept only for documentation belongs in a docstring.

<a id="n28"></a>
### N28. Spell words out: `microphone`, `laboratory`, `standard_deviation`, `frequency`, `confidence`

**Why.** `mic_calibration_factor`, `lab_airborne_insulation`, `delay_std`, `bank.freq` and `ci_lower` each had a spelled-out twin elsewhere in the API.

**Do**

```python
from phonometry import materials

materials.microphone_calibration_factor
```

**Don't**

```py
mic_calibration_factor(...)
result.delay_std
result.ci_lower
```

**Enforced by:** `tests/test_public_vocabulary.py::test_words_are_spelled_out`, `tests/test_public_vocabulary.py::test_the_row_keys_of_a_verdict_are_spelled_out`, `tests/test_public_vocabulary.py::test_every_kept_spelling_still_exists`

**Exceptions.** A confidence bound is `confidence_lower` or `confidence_upper`; `ci` is a word of no public name except the impact sound adaptation term of ISO 717-2 (`ci`, `ci_delta`, `ci_r`). `fs`, `min`, `max` and `n_` are established terms, not abbreviations. The public attributes a plain class sets on `self` and the row keys of verdict dictionaries are held too. A spelling kept on purpose goes in `_SPELLING_EXEMPT` of the test, keyed by location with its reason.

<a id="n29"></a>
### N29. Write `min` and `max` in every public name, `MIN` and `MAX` in a constant

**Why.** Scientific Python writes `min` and `max` (numpy `min` and `max`, SciPy `maxiter`, scikit-learn `max_iter`, Matplotlib `vmin`), the standards print Lmax and Lmin, and the library already wrote `min_` and `max_` about three times as often as `minimum_` and `maximum_`. A maximum in decibels is the maximum level, `max_level`.

**Do**

```python
from phonometry import environment

environment.RAILWAY_MIN_SPEED_KMH
```

**Don't**

```py
railway_source_power(minimum_speed_kmh=...)
plant_steady_reading(maximum_level=..., max_db=...)
```

**Enforced by:** `tests/test_public_vocabulary.py::test_words_are_spelled_out`

**Exceptions.** A class writes `Min` and `Max` (`MaxUncertaintyRow`). Terms of art are included: Lmax and Lmin are `max_level` and `min_level`, never a bare `max_db`, and the minimum-phase reconstruction is `min_phase`.

<a id="n30"></a>
### N30. Name a count `n_<plural>`, and a limit on one `min_n_` or `max_n_`

**Why.** `events=3` could be read as the events themselves, and `num_points`, `blade_count` and `harmonics` each spelled a count differently from `n_samples`.

**Do**

```python
from phonometry import vibration

vibration.story_fundamental_frequency(n_stories=8)
```

**Don't**

```py
story_fundamental_frequency(stories=8)
verify_filter_class(..., num_points=16)
```

**Enforced by:** `tests/test_public_vocabulary.py::test_a_count_is_n_plural`, `tests/test_public_vocabulary.py::test_every_kept_count_spelling_still_exists`

**Exceptions.** Not counts: a class or grade number (`filter_class`), an axis, the `decimals` a value is rounded to, degrees of freedom, a length counted in samples or grid cells (`delay_samples`). A vectorized argument that takes one count or many keeps its plural, and an array of tallies is not one count (`counts`). Kept spellings go in `_COUNT_EXEMPT` of the test, keyed by location with their reason. `num_` is refused by [N28](#n28).

<a id="n31"></a>
### N31. Name a duration by its quantity, then its unit

**Why.** The sweep generators took `seconds=`, `lden` took `hours=` and the ISO 1999 functions took `years=`: names that say a unit and not what lasts. The rule holds whatever the name holds: one number, the durations of several periods, or an array.

**Do**

```python
from phonometry import signals

noise = signals.noise_signal(48000, duration_s=1.0)
```

**Don't**

```py
sweep_signal(fs, seconds=2.0)
htlan(..., years=10)
```

**Enforced by:** `tests/test_public_vocabulary.py::test_a_count_is_n_plural`, review

**Exceptions.** A rate is not a duration (`seconds_per_decade`). The test refuses a name that is a unit alone; how the unit is spelled, a minute included, is [N17](#n17).

<a id="n32"></a>
### N32. Spell every identifier and every value a caller types in American English

**Why.** `acoustic_centre` sat beside `center_frequencies` and `programme` beside `program_loudness`, so a caller who wrote one spelling met a `TypeError` on the next function. Values count too: a `Literal` choice, a default, an enum value, a table key, a string of a published tuple.

**Do**

```python
from phonometry import materials, vibration

vibration.centered_interval, materials.in_situ_absorption_coefficient
```

**Don't**

```py
centred_interval(...)
insitu_absorption_coefficient(...)
location="centre"
```

**Enforced by:** `scripts/check_identifier_spelling.py`, `make identifier-spelling`, `CI: Every public quantity names its unit`

**Exceptions.** In situ is `in_situ` (`InSitu` in a class). `catalogue` is the one sanctioned British form: it is an American variant too, used uniformly, and part of the file format users write (the `catalogue` key, `phonometry-catalogue`, the schema URN). A string a published source prints keeps its print, in `EXEMPT` of the script, keyed by location with its reason ('optimised brushed down concrete', 'aluminium', the surname Doutres). The check reads `-ise`, `-yse`, `-our`, `-tre` and `-bre` as whole families. Prose in docstrings, guides and comments is not held to it.

<a id="n33"></a>
### N33. Write a printed symbol in a public name in lower snake case

**Why.** The standards print `Rw`, `LAeq` and `R'`; a public name writes them `r_w`, `l_aeq` and `r_prime`, so the API reads in one case and a symbol's prime is a word, not a quote.

**Do**

```python
def sound_reduction(r_w: float, l_aeq: float) -> float:
    return l_aeq - r_w
```

**Don't**

```py
def sound_reduction(Rw: float, LAeq: float) -> float: ...
```

**Enforced by:** review

**Exceptions.** A local variable may keep the printed case (`Rw = ...`); that is why ruff's N naming rules are not selected (only N812, on import aliases, is).

<a id="n34"></a>
### N34. Name a type alias in PascalCase

**Why.** An alias reads as a type at the call site and in the API reference, which prints it as its definition. It stays private to its module ([A5](api.md#a5)).

**Do**

```python
from typing import Literal

Language = Literal["en", "es"]
```

**Don't**

```py
language_t = Literal["en", "es"]
```

**Enforced by:** review
