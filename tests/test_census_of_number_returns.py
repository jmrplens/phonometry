#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every public function the census can call with numbers returns a number for them.

Rule A57 of the contributor guide: a function of a number or an array of
them returns a Python ``float`` (a ``complex`` where its result is complex)
when every argument that decides the shape is a number, and a reduction to
one number returns a ``float`` too. The check of return overloads reads the
heads that say so, and ``tests/test_scalar_or_array_returns.py`` calls each
function whose heads tell a value from an array; neither sees a function
annotated as an array alone, ``-> NDArray[np.complex128]``, that hands a
number back as a zero-dimensional array. This census calls the package
instead of reading it:

* every public function of every domain, and every public method of the
  records those calls return or that numbers build, is called with numbers
  alone: each parameter without a default takes a number, a ``Literal``
  takes its first choice, a count takes 2 and a record of numbers is built
  from the same number, trying the numbers of :data:`NUMBERS` in turn until
  a call runs;
* a call whose result is a zero-dimensional array, a one-element array or a
  numpy scalar fails the census, and so does a function that refuses every
  number and returns such a value for a sequence of three, a reduction that
  hands its one number back as an array;
* :data:`NOT_OF_A_NUMBER` names the calls whose result is no function of a
  number, each with its reason, and :data:`ONE_ELEMENT` the functions whose
  validator makes a number one-dimensional, which give a one-element array
  for a number until they are converted; an entry the census no longer
  flags fails, so neither list outlives what it excuses.

What the census cannot call with numbers alone (a function of a ``Signal``,
a text, a path or a record it cannot build) it leaves to the overload check
and its cases. It reads no source: an alias a module imports only for a type
checker is looked up in the modules of the package already loaded.
"""

from __future__ import annotations

import dataclasses
import inspect
import re
import sys
import types
import typing
import warnings
from functools import cache
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

import phonometry

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

#: Both tests read one census, which the cache keeps for the worker they share.
pytestmark = pytest.mark.xdist_group("census_of_number_returns")

#: The numbers a call is tried with, in turn, until one is accepted: a
#: function refuses a frequency of 1 Hz below its range, a ratio above 1 or a
#: level difference of 0 dB, and one of these makes a valid call of nearly
#: every function of numbers in the package.
NUMBERS = (1.0, 100.0, 0.5, 1000.0, 10.0, 0.1, 50.0, 2.0, 20.0, 0.01, 5000.0, 0.9, 3.0)

#: A parameter whose annotation names one of these takes a number.
_NUMERIC = re.compile(
    r"\b(float|int|complex|NumericArrayLike|RealValues|RealScalar|ComplexScalar"
    r"|ComplexValues|ArrayLike|NDArray|Real|Complex|_Complex|BandValues)\b"
)

#: A parameter annotated with one of these takes no number, beside a number or not.
_NOT_NUMERIC = re.compile(r"\b(str|Signal|Callable|Mapping|Path)\b")

#: An integer count, which takes 2.
_COUNT = re.compile(r"\s*int(\s*\|\s*np\.integer\[Any\])?\s*")

#: Names that draw, write or report: the census calls none of them.
_SKIPPED = re.compile(r"^(plot|report|save|write|export|to_)")

#: The calls whose result is no function of a number, with the reason.
NOT_OF_A_NUMBER: dict[str, str] = {
    "vibration.running_acceleration_level": (
        "a running level of a time record: a number is a record of one sample"
    ),
    "vibration.running_velocity_level": (
        "a running level of a time record: a number is a record of one sample"
    ),
    "vibration.running_velocity_rms": (
        "a running value of a time record: a number is a record of one sample"
    ),
    "vibration.kb_signal": "a weighted time record, as long as the record it filters",
    "vibration.kbf_signal": "a weighted time record, as long as the record it filters",
    "environment.acceleration_test_positions": (
        "the positions along a length: their count is what the value sets"
    ),
    "environment.adrienne_reflection_window": (
        "a window of samples: its length is what the sample rate sets"
    ),
    "metrology.exact_frequencies": (
        "the frequencies between two limits: their count is what the limits set"
    ),
    "vibration.track_excitation_frequency": (
        "the harmonics of a passing speed: their count is what the values set"
    ),
    "materials.TransferMatrix.absorption_hard_backed": (
        "one value per frequency the matrix holds: its fields decide the shape, "
        "and the census builds the matrix from numbers"
    ),
    "materials.TransferMatrix.material_wavenumber": (
        "one value per frequency the matrix holds: its fields decide the shape, "
        "and the census builds the matrix from numbers"
    ),
    "materials.TransferMatrix.reflection_hard_backed": (
        "one value per frequency the matrix holds: its fields decide the shape, "
        "and the census builds the matrix from numbers"
    ),
    "materials.TransferMatrix.transmission_loss": (
        "one value per frequency the matrix holds: its fields decide the shape, "
        "and the census builds the matrix from numbers"
    ),
    "signals.CorrelationResult.random_error": (
        "one value per lag the record holds: its fields decide the shape, and "
        "the census builds the record from numbers"
    ),
    "aircraft.ARP866AAttenuation.path_attenuation": (
        "one value per band the record holds for one length: its fields decide "
        "the shape, and the census builds the record from numbers"
    ),
    "building.RainfallSoundResult.sound_power_levels": (
        "one level per band the record holds for one area: its fields decide "
        "the shape, and the census builds the record from numbers"
    ),
}

#: The functions and methods whose validator makes a number one-dimensional,
#: so that a number gives a one-element array, as the detailed building model
#: did before it followed the rule. They are not converted yet, and each
#: leaves the list when it is: the census then fails its entry as stale.
ONE_ELEMENT: frozenset[str] = frozenset(
    {
        "environment.acceleration_test_positions",
        "environment.adrienne_reflection_window",
        "metrology.exact_frequencies",
        "underwater.seawater_absorption",
        "underwater.spreading_loss",
        "underwater.thermal_noise_spectrum",
        "underwater.wind_noise_spectrum",
        "vibration.assessment_velocity",
        "vibration.assessment_weighting_response",
        "vibration.band_limiting_factors",
        "vibration.beam_modal_density",
        "vibration.blast_peak_velocity_mm_s",
        "vibration.cylindrical_shell_modal_density",
        "vibration.elastic_insertion_loss",
        "vibration.far_field_velocity_mm_s",
        "vibration.foundation_to_floor_level_difference",
        "vibration.ground_attenuation_coefficient_per_m",
        "vibration.ground_transmission",
        "vibration.impact_peak_velocity_mm_s",
        "vibration.kbf_signal",
        "vibration.kb_signal",
        "vibration.kb_weighted_levels",
        "vibration.material_damping_factor",
        "vibration.passage_energy_spectral_density",
        "vibration.predict_floor_spectrum",
        "vibration.rescale_emission_for_speed",
        "vibration.running_acceleration_level",
        "vibration.running_velocity_level",
        "vibration.running_velocity_rms",
        "vibration.spectral_density_level",
        "vibration.track_excitation_frequency",
        "vibration.train_kb_fmax",
        "vibration.train_velocity_ratio",
        "vibration.velocity_psd_from_voltage",
        "vibration.velocity_spectrum_um_s",
        "vibration.weighting_factors",
    }
)

#: What a census row says of a call.
type Row = tuple[str, str]


def _choices(value: object) -> tuple[object, ...] | None:
    """The choices of a ``Literal``, written as one or as a ``type`` statement.

    The value of a ``type`` statement is evaluated when it is read, and one
    that names a type only a type checker imports cannot be: it is no
    ``Literal`` the census can use.
    """
    candidates = [value]
    if isinstance(value, typing.TypeAliasType):
        try:
            candidates.append(value.__value__)
        except NameError:
            return None
    for candidate in candidates:
        if typing.get_origin(candidate) is typing.Literal:
            return typing.get_args(candidate)
    return None


@cache
def _literal_aliases() -> dict[str, tuple[object, ...]]:
    """Every ``Literal`` alias the loaded modules of the package define, by name."""
    found: dict[str, tuple[object, ...]] = {}
    for name, module in sorted(sys.modules.items()):
        if not name.startswith("phonometry") or module is None:
            continue
        for attribute, value in vars(module).items():
            choices = _choices(value)
            if choices is not None:
                found.setdefault(attribute, choices)
    return found


def _first_choice(text: str, module: types.ModuleType) -> object:
    """The first choice of a ``Literal`` annotation, written out or through an alias."""
    written = re.fullmatch(r"Literal\[\s*(['\"])(.*?)\1.*\]", text.strip(), re.DOTALL)
    if written:
        return written.group(2)
    head = text.split("|")[0].strip()
    choices = _choices(getattr(module, head, None))
    if choices is None:
        choices = _literal_aliases().get(head)
    if choices is None:
        raise LookupError(text)
    return choices[0]


def _record_of(text: str, module: types.ModuleType) -> type | None:
    """The dataclass of the package an annotation names, if it names one alone."""
    name = text.strip().strip("'\"").rpartition(".")[2]
    value = getattr(module, name, None)
    if value is None:
        for loaded, candidate in sorted(sys.modules.items()):
            if loaded.startswith("phonometry") and candidate is not None:
                value = getattr(candidate, name, None)
                if value is not None:
                    break
    if (
        inspect.isclass(value)
        and value.__module__.startswith("phonometry")
        and dataclasses.is_dataclass(value)
    ):
        return value
    return None


#: How a census call fills one parameter: a number, a fixed value, or a record.
type Slot = tuple[str, object]


def _plan(function: Callable[..., object], *, depth: int = 0) -> dict[str, Slot] | None:
    """How to call *function* with numbers, or ``None`` when numbers cannot."""
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return None
    module = sys.modules[function.__module__]
    slots: dict[str, Slot] = {}
    for parameter in signature.parameters.values():
        if (
            parameter.name in {"self", "cls"}
            or parameter.kind in {parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD}
            or parameter.default is not parameter.empty
        ):
            continue
        annotation = parameter.annotation
        text = annotation if isinstance(annotation, str) else repr(annotation)
        try:
            slots[parameter.name] = ("fixed", _first_choice(text, module))
            continue
        except LookupError:
            pass
        record = _record_of(text, module) if depth == 0 else None
        if text.strip() == "bool":
            slots[parameter.name] = ("fixed", True)
        elif _COUNT.fullmatch(text):
            slots[parameter.name] = ("fixed", 2)
        elif _NUMERIC.search(text) and not _NOT_NUMERIC.search(
            text.replace("NumericArrayLike", "")
        ):
            slots[parameter.name] = ("number", None)
        elif record is not None:
            inner = _plan(record, depth=depth + 1)
            if inner is None:
                return None
            slots[parameter.name] = ("record", (record, inner))
        else:
            return None
    return slots


def _arguments(slots: dict[str, Slot], number: object) -> dict[str, object]:
    built: dict[str, object] = {}
    for name, (kind, value) in slots.items():
        if kind == "number":
            built[name] = number
        elif kind == "fixed":
            built[name] = value
        else:
            record, inner = typing.cast("tuple[type, dict[str, Slot]]", value)
            built[name] = record(**_arguments(inner, number))
    return built


def _first_call(
    function: Callable[..., object], slots: dict[str, Slot], numbers: Iterable[object]
) -> tuple[bool, object]:
    """Call *function* with each of *numbers* until one is accepted."""
    for number in numbers:
        # A call that raises, whatever it raises, returns nothing to judge.
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return True, function(**_arguments(slots, number))
        except Exception:
            continue
    return False, None


def _offence(result: object) -> str | None:
    """What is wrong with *result* as the answer to numbers, if anything."""
    if isinstance(result, np.ndarray) and result.ndim == 0:
        return "a zero-dimensional array"
    if isinstance(result, np.ndarray) and result.shape == (1,):
        return "a one-element array"
    if isinstance(result, np.generic):
        return "a numpy scalar"
    return None


def _public() -> Iterator[tuple[str, object]]:
    seen: set[int] = set()
    for package in phonometry.__all__:
        module = getattr(phonometry, package, None)
        if not isinstance(module, types.ModuleType):
            continue
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name, None)
            if obj is not None and id(obj) not in seen:
                seen.add(id(obj))
                yield f"{package}.{name}", obj


def _methods(instance: object) -> Iterator[tuple[str, Callable[..., object]]]:
    for klass in type(instance).__mro__:
        if not klass.__module__.startswith("phonometry"):
            continue
        for name, member in vars(klass).items():
            if not name.startswith("_") and inspect.isfunction(member):
                yield name, getattr(instance, name)


@cache
def census() -> tuple[Row, ...]:
    """Every call the census makes that returns something other than a number."""
    rows: list[Row] = []
    classes = {obj: name for name, obj in _public() if inspect.isclass(obj)}
    instances: dict[type, object] = {}
    for name, obj in _public():
        if not inspect.isfunction(obj) or _SKIPPED.match(name.rpartition(".")[2]):
            continue
        slots = _plan(obj)
        if slots is None or all(kind == "fixed" for kind, _ in slots.values()):
            continue
        called, result = _first_call(obj, slots, NUMBERS)
        if not called:
            called, result = _first_call(
                obj, slots, ([n, 1.1 * n, 0.9 * n] for n in NUMBERS)
            )
            offence = _offence(result) if called and np.ndim(result) == 0 else None
            if offence is not None:
                rows.append((name, f"{offence} for a sequence it reduces"))
            continue
        offence = _offence(result)
        if offence is not None:
            rows.append((name, offence))
        if type(result) in classes:
            instances.setdefault(type(result), result)
    for cls in classes:
        if cls in instances or not dataclasses.is_dataclass(cls):
            continue
        slots = _plan(cls)
        if slots is not None:
            called, built = _first_call(cls, slots, NUMBERS)
            if called:
                instances[cls] = built
    seen: set[str] = set()
    for cls, instance in instances.items():
        for method, bound in _methods(instance):
            qualified = f"{classes[cls]}.{method}"
            if qualified in seen or _SKIPPED.match(method):
                continue
            seen.add(qualified)
            slots = _plan(bound)
            if slots is None or not any(kind == "number" for kind, _ in slots.values()):
                continue
            called, result = _first_call(bound, slots, NUMBERS)
            offence = _offence(result) if called else None
            if offence is not None:
                rows.append((qualified, offence))
    return tuple(sorted(rows))


def _exempt(row: Row) -> bool:
    name, offence = row
    return name in NOT_OF_A_NUMBER or (
        name in ONE_ELEMENT and offence == "a one-element array"
    )


def test_numbers_give_a_number() -> None:
    """No call of numbers returns an array of one value or a numpy scalar."""
    offending = [
        f"{name}: {offence}"
        for name, offence in census()
        if not _exempt((name, offence))
    ]
    assert offending == [], (
        "these return an array of one value or a numpy scalar for numbers; "
        "return a float or a complex for them (rule A57):\n" + "\n".join(offending)
    )


def test_every_exemption_is_still_needed() -> None:
    """An entry of either list that the census no longer flags is stale."""
    flagged = dict(census())
    stale = sorted(
        name
        for name in NOT_OF_A_NUMBER.keys() | ONE_ELEMENT
        if name not in flagged
        or (name in ONE_ELEMENT and flagged[name] != "a one-element array")
    )
    assert stale == []


def test_the_census_calls_the_package() -> None:
    """The census reaches the functions of numbers it exists for.

    A plan that stopped building calls would pass every other test here by
    calling nothing: the functions converted to the complex form and to the
    real one, reached through the aliases their annotations name, must be
    among the calls it makes.
    """
    calls: dict[str, Any] = {}
    for name, obj in _public():
        if inspect.isfunction(obj):
            slots = _plan(obj)
            if slots is not None:
                calls[name] = slots
    for name in (
        "materials.normalized_surface_impedance",
        "materials.helmholtz_resonator_impedance",
        "noise_control.quarter_wave_impedance",
        "environment.kurze_anderson_attenuation",
        "vibration.sdof_mobility",
    ):
        assert name in calls, name
