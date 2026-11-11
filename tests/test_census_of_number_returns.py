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
  records those calls return, that numbers build, that the package publishes
  in its tables or that :data:`FIXTURES` builds, is called with numbers
  alone. A parameter of numbers takes one of :data:`NUMBERS`, a ``Literal``
  one of its choices, a count one of :data:`COUNTS`, a flag either truth
  value and a record of numbers is built the same way. The calls first give
  every parameter of numbers the same number, a ``Literal`` its first choice
  and a count 2, number by number, and then draw each parameter on its own,
  :data:`TRIALS` times, until a call runs. A function with no required
  parameter is called as it stands, and a function or a method with an
  optional parameter of numbers whose default is ``None`` is called a second
  time with a number there too;
* a call whose result is a zero-dimensional array, a one-element array or a
  numpy scalar fails the census, and so does a function that refuses every
  number and returns such a value for a sequence of three, a reduction that
  hands its one number back as an array;
* :data:`NOT_OF_A_NUMBER` names the calls whose result is no function of a
  number, each with its reason: a time record, an output whose length a
  value sets, a record built from numbers. An entry the census no longer
  flags fails, so the list does not outlive what it excuses;
* :data:`UNREACHED` names, each with its reason, every public function and
  method that returns an array, takes numbers and that no call of the census
  runs: a table of a given shape, a time record, a record the census cannot
  build. A function of that kind that is neither reached nor named fails, and
  so does an entry the census reaches, so the list only shrinks.

It reads no source: an alias a module imports only for a type checker is
looked up in the modules of the package already loaded.
"""

from __future__ import annotations

import ast
import dataclasses
import functools
import inspect
import random
import re
import sys
import types
import typing
import warnings
from collections.abc import Mapping
from typing import TYPE_CHECKING

import numpy as np
import pytest
from ndarray_hints import ndarray_of

import phonometry

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

#: The tests read one census, which the cache keeps for the worker they share.
pytestmark = pytest.mark.xdist_group("census_of_number_returns")

#: The numbers a parameter of numbers is tried with. The first thirteen are
#: given to every parameter at once, in turn; then each parameter draws its
#: own: a function refuses a frequency of 1 Hz below its range, a ratio above
#: 1, a margin of 0 dB over a background or a duct of 1000 m, and a call that
#: needs a level 10 dB over another, a nominal band, a negative velocity and a
#: diameter under 2 m finds them among these.
NUMBERS = (
    1.0,
    100.0,
    0.5,
    1000.0,
    10.0,
    0.1,
    50.0,
    2.0,
    20.0,
    0.01,
    5000.0,
    0.9,
    3.0,
    0.0,
    -1.0,
    -10.0,
    200.0,
    500.0,
    0.2,
    5.0,
    60.0,
    80.0,
    4.0,
    0.05,
    30.0,
    250.0,
    2000.0,
    8000.0,
    125.0,
    40.0,
    343.0,
    1.5,
    0.3,
    45.0,
    90.0,
)

#: The counts a count is tried with, 2 first: Figure 3 of DIN 4150-1 reads a
#: machine count of 3, 5 or 10, and a table of twelve months or twenty-four
#: hours wants its own.
COUNTS = (2, 3, 1, 4, 5, 6, 9, 10, 12, 24)

#: How many calls, each parameter drawn on its own, a function is given
#: after the numbers shared by every parameter.
TRIALS = 240

#: A parameter whose annotation names one of these takes a number.
_NUMERIC = re.compile(
    r"\b(float|int|complex|NumericArrayLike|RealValues|RealScalar|ComplexScalar"
    r"|ComplexValues|ArrayLike|NDArray|Real|Complex|_Complex|BandValues)\b"
)

#: A parameter annotated with one of these takes no number, beside a number or not.
_NOT_NUMERIC = re.compile(r"\b(str|Signal|Callable|Mapping|Path)\b")

#: A parameter whose annotation names one of these takes an array of numbers.
_ARRAY_INPUT = re.compile(
    r"\b(NumericArrayLike|RealValues|ComplexValues|ArrayLike|BandValues)\b"
)

#: An integer count.
_COUNT = re.compile(r"\s*int(\s*\|\s*np\.integer\[Any\])?\s*")

#: Names that draw, write or report: the census calls none of them.
_SKIPPED = re.compile(r"^(plot|report|save|write|export|to_)")


def _peak_statistics() -> object:
    noise = np.random.default_rng(0).standard_normal(4000)
    return phonometry.metrology.peak_statistics(noise, fs=1000.0)


def _npd_curves() -> object:
    return phonometry.aircraft.ANPNPDCurves(
        aircraft_id="JET",
        npd_id="JET",
        metric="SEL",
        operation="D",
        power_parameter="CNT (lb)",
        powers=[1.0e4, 2.0e4],
        distances_m=[61.0, 122.0, 244.0],
        levels=[[95.0, 90.0, 85.0], [100.0, 95.0, 90.0]],
    )


def _time_selective_response() -> object:
    record = np.zeros(4800)
    record[288] = 96000.0
    record[624] = 0.3 * 96000.0
    return phonometry.metrology.time_selective_response(
        record, 96000.0, window_start_s=0.0025, window_end_s=0.006
    )


def _single_mode_fit() -> object:
    return phonometry.vibration.SingleModeFitResult(
        frequencies=np.array([30.0, 40.0, 50.0]),
        frf=np.array([1.0e-3 + 0.0j, 2.0e-3 + 1.0e-3j, 1.0e-3 + 0.0j]),
        pole_rad_s=complex(-5.0, 2.0 * np.pi * 40.0),
        residue=complex(0.0, -1.0e-2),
        direct_term=0.0j,
    )


def _sel_distribution() -> object:
    return phonometry.environment.sel_distribution(
        [30.0, 33.0, 36.0, 41.0, 45.0], [0.3, 0.3, 0.2, 0.15, 0.05]
    )


def _contour() -> object:
    return phonometry.simulation.ContourPhasors(
        frequency=500.0,
        positions=np.array([[0.1, 0.0], [0.0, 0.1], [-0.1, 0.0], [0.0, -0.1]]),
        normals=np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]]),
        pressure=np.array([1.0 + 0.0j, 1.0j, -1.0 + 0.0j, -1.0j]),
        normal_velocity=np.array([1.0e-3 + 0.0j, 1.0e-3j, -1.0e-3 + 0.0j, -1.0e-3j]),
        segment=0.157,
    )


def _inverse_filter() -> object:
    impulse = np.zeros(1024)
    impulse[0] = 1.0
    impulse[1] = 0.5
    return phonometry.signals.regularized_inverse_filter(
        impulse, 8000.0, f_range=(100.0, 2000.0)
    )


def _room_modes() -> object:
    return phonometry.room.room_modes(
        (7.0, 5.0, 3.0), max_frequency=120.0, reverberation_time=0.8
    )


#: Records that neither numbers nor the tables of the package build, each as
#: the tests build it: the census calls their methods, and hands one to a
#: function that takes such a record.
FIXTURES: dict[str, Callable[[], object]] = {
    "aircraft.ANPNPDCurves": _npd_curves,
    "environment.SELDistribution": _sel_distribution,
    "metrology.PeakStatisticsResult": _peak_statistics,
    "metrology.TimeSelectiveResponse": _time_selective_response,
    "room.RoomModesResult": _room_modes,
    "signals.InverseFilterResult": _inverse_filter,
    "simulation.ContourPhasors": _contour,
    "vibration.SingleModeFitResult": _single_mode_fit,
}


@functools.cache
def _fixtures() -> dict[type, object]:
    """One record of each class :data:`FIXTURES` builds, by class."""
    return {type(build()): build() for build in FIXTURES.values()}


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
    "vibration.assessment_velocity": (
        "a weighted time record, as long as the record it filters"
    ),
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
    "materials.biot_surface_impedance": (
        "one value per frequency the Biot waves it takes hold: the record decides "
        "the shape, and the census builds the record from numbers"
    ),
    "signals.CorrelationResult.random_error": (
        "one value per lag the record holds: its fields decide the shape, and "
        "the census builds the record from numbers"
    ),
    "aircraft.ARP866AAttenuation.path_attenuation": (
        "one value per band the record holds for one length: its fields decide "
        "the shape, and the census builds the record from numbers"
    ),
    "signals.InverseFilterResult.apply": (
        "an equalized time record, as long as the record it filters"
    ),
    "building.RainfallSoundResult.sound_power_levels": (
        "one level per band the record holds for one area: its fields decide "
        "the shape, and the census builds the record from numbers"
    ),
}

_BANDS_24 = "takes 24 values, one per one-third octave band, and refuses a number"
_BAND_AXIS = "takes a band axis of frequencies, one-dimensional, and refuses a number"
_RESPONSE = "takes a sampled frequency response, one-dimensional, and refuses a number"
_SURFACES = (
    "takes the surfaces of a room as records the census cannot build, and their "
    "absorption decides the shape"
)
_FOUR_POLE = (
    "takes a four-pole matrix or a stack of them, which a number is not; "
    "tests/noise_control/test_silencers.py holds what it gives for each"
)
_ROUGHNESS = (
    "takes a roughness record of three samples or more, a record along the rail"
)

#: The public functions and methods that return an array and take numbers,
#: which no call of the census runs, with the reason.
UNREACHED: dict[str, str] = {
    "aircraft.interpolated_source_level": (
        "takes the measured hemispheres of a rotorcraft, records the census "
        "cannot build"
    ),
    "aircraft.npd_level": (
        "takes a table of two or more powers by two or more distances, which "
        "numbers cannot be; its case in tests/test_scalar_or_array_returns.py "
        "calls it with a number distance"
    ),
    "aircraft.perceived_noisiness": _BANDS_24,
    "building.corner_level": (
        "takes the levels of each corner per band, a table of two or three axes, "
        "and refuses a number"
    ),
    "building.joint_sound_reduction_index": (
        "takes levels per band, or per position and band, and refuses a number"
    ),
    "building.limp_panel_reduction_index": _BAND_AXIS,
    "building.typical_element_mobility": (
        "each row of Table D.1 takes its own describing quantities and refuses "
        "the others, which no draw of the census lands on; its case in "
        "tests/test_scalar_or_array_returns.py calls it"
    ),
    "environment.amplitude_modulation_band_levels": (
        "takes logged band levels over a set of one-third octave bands that "
        "holds the band it reads, and refuses a number"
    ),
    "environment.curvature_processed_roughness": _ROUGHNESS,
    "environment.impact_roughness": _BANDS_24,
    "environment.octave_bands_from_third_octaves": _BANDS_24,
    "environment.remove_roughness_spikes": _ROUGHNESS,
    "environment.rolling_sound_power": _BANDS_24,
    "environment.roughness_to_frequency": (
        "resamples a table of roughness levels along a wavelength axis, "
        "one-dimensional, and refuses a number"
    ),
    "environment.source_directivity_corrections": (
        "takes the impulse responses of a measurement, time records"
    ),
    "environment.total_effective_roughness": _BANDS_24,
    "filters.time_weighting": "weights a time record, as long as the record",
    "materials.area_factors": (
        "takes the elevations of the receivers of a hemisphere, a one-dimensional "
        "sequence of angles, and refuses a number"
    ),
    "noise_control.cascade": _FOUR_POLE,
    "noise_control.combined_internal_levels": (
        "adds a sequence of two or more spectra, which a number is not"
    ),
    "noise_control.insertion_loss": _FOUR_POLE,
    "noise_control.internal_spectrum": _BAND_AXIS,
    "noise_control.pipe_transmission_loss": _BAND_AXIS,
    "noise_control.screen_source_directivity_index": (
        "takes the levels of twelve positions on a circle, and refuses a number"
    ),
    "noise_control.transmission_loss": _FOUR_POLE,
    "room.directivity_energy_average": (
        "averages the levels of a full turn of bearings, twelve or more, and "
        "refuses a number"
    ),
    "room.equivalent_absorption_area": (
        "takes the surfaces of a room as pairs of an area and its absorption, "
        "and their absorption decides the shape"
    ),
    "room.eyring_reverberation_time": _SURFACES,
    "room.gliding_directivity_deviation": (
        "takes the levels of a full turn of bearings, a whole number of them per "
        "30 degrees, and refuses a number"
    ),
    "room.millington_sette_reverberation_time": _SURFACES,
    "room.sabine_reverberation_time": _SURFACES,
    "signals.excess_phase": _RESPONSE,
    "signals.fractional_octave_smoothing": (
        "smooths values over a frequency axis, one-dimensional, and refuses a number"
    ),
    "signals.group_delay": _RESPONSE,
    "signals.min_phase": _RESPONSE,
    "vibration.characteristic_phase_deviation": (
        "reads pairs of adjacent bands, two frequencies or more, and refuses a number"
    ),
}

#: What a census row says of a call.
type Row = tuple[str, str]


@dataclasses.dataclass(frozen=True)
class Slot:
    """How a census call fills one parameter.

    :ivar kind: ``"number"``, ``"optional"`` (a number or the ``None`` an
        optional parameter of numbers defaults to), ``"choice"`` (a
        ``Literal``, a count or a flag, each from its own values) or
        ``"record"``.
    :ivar values: What a choice is drawn from, the first one first.
    :ivar record: The dataclass a record slot builds.
    :ivar inner: How the record's own fields are filled.
    """

    kind: str
    values: tuple[object, ...] = ()
    record: type | None = None
    inner: Mapping[str, Slot] = dataclasses.field(default_factory=dict)


#: How a census call fills the parameters of a function, by name.
type Plan = dict[str, Slot]


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


@functools.cache
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


def _literal_choices(text: str, module: types.ModuleType) -> tuple[object, ...]:
    """Every choice of a ``Literal`` annotation, written out or through an alias."""
    written = re.fullmatch(r"Literal\[(.*)\]", text.strip(), re.DOTALL)
    if written:
        return tuple(ast.literal_eval(f"({written.group(1)},)"))
    head = text.split("|")[0].strip()
    choices = _choices(getattr(module, head, None))
    if choices is None:
        choices = _literal_aliases().get(head)
    if choices is None:
        raise LookupError(text)
    return choices


def _loaded(name: str, module: types.ModuleType) -> object:
    """What *name* is in *module*, or in the first loaded module of the package."""
    value = getattr(module, name, None)
    if value is None:
        for loaded, candidate in sorted(sys.modules.items()):
            if loaded.startswith("phonometry") and candidate is not None:
                value = getattr(candidate, name, None)
                if value is not None:
                    break
    return value


def _record_of(text: str, module: types.ModuleType) -> type | None:
    """The dataclass of the package an annotation names, if it names one alone."""
    value = _loaded(text.strip().strip("'\"").rpartition(".")[2], module)
    if (
        inspect.isclass(value)
        and value.__module__.startswith("phonometry")
        and dataclasses.is_dataclass(value)
    ):
        return value
    return None


def _annotation(parameter: inspect.Parameter) -> str:
    annotation = parameter.annotation
    return annotation if isinstance(annotation, str) else repr(annotation)


def _numeric(text: str) -> bool:
    return bool(_NUMERIC.search(text)) and not _NOT_NUMERIC.search(
        text.replace("NumericArrayLike", "")
    )


def _slot(text: str, module: types.ModuleType, depth: int) -> Slot | None:
    """How to fill a parameter annotated *text*, or ``None`` when numbers cannot."""
    try:
        return Slot("choice", _literal_choices(text, module))
    except LookupError:
        pass
    if text.strip() == "bool":
        return Slot("choice", (True, False))
    if _COUNT.fullmatch(text):
        return Slot("choice", COUNTS)
    if _numeric(text):
        return Slot("number")
    record = _record_of(text, module) if depth == 0 else None
    if record in _fixtures():
        return Slot("choice", (_fixtures()[record],))
    if record is not None:
        inner = _plan(record, depth=depth + 1)
        if inner is not None:
            return Slot("record", record=record, inner=inner)
    return None


def _plan(
    function: Callable[..., object], *, depth: int = 0, optional: bool = False
) -> Plan | None:
    """How to call *function* with numbers, or ``None`` when numbers cannot.

    With *optional*, an optional parameter of numbers whose default is
    ``None`` takes a number too.
    """
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return None
    module = sys.modules[function.__module__]
    slots: Plan = {}
    for parameter in signature.parameters.values():
        if parameter.name in {"self", "cls"} or parameter.kind in {
            parameter.VAR_POSITIONAL,
            parameter.VAR_KEYWORD,
        }:
            continue
        text = _annotation(parameter)
        if parameter.default is not parameter.empty:
            if optional and parameter.default is None and _numeric(text):
                slots[parameter.name] = Slot("optional")
            continue
        slot = _slot(text, module, depth)
        if slot is None:
            return None
        slots[parameter.name] = slot
    return slots


def _shared(slots: Mapping[str, Slot], number: object) -> dict[str, object]:
    """Every parameter of numbers *number*, every choice its first value."""
    built: dict[str, object] = {}
    for name, slot in slots.items():
        if slot.kind in {"number", "optional"}:
            built[name] = number
        elif slot.kind == "choice":
            built[name] = slot.values[0]
        else:
            built[name] = typing.cast("type", slot.record)(
                **_shared(slot.inner, number)
            )
    return built


def _drawn(slots: Mapping[str, Slot], draw: random.Random) -> dict[str, object]:
    """Every parameter drawn on its own from its values.

    An optional parameter of numbers is left out one time in two, since a
    function may take one of two such parameters and refuse both, and one
    of them always takes a number.
    """
    built: dict[str, object] = {}
    optional = [name for name, slot in slots.items() if slot.kind == "optional"]
    given = {name for name in optional if draw.random() < 0.5}
    if optional and not given:
        given = {draw.choice(optional)}
    for name, slot in slots.items():
        if slot.kind == "number" or name in given:
            built[name] = draw.choice(NUMBERS)
        elif slot.kind == "optional":
            continue
        elif slot.kind == "choice":
            built[name] = draw.choice(slot.values)
        else:
            built[name] = typing.cast("type", slot.record)(**_drawn(slot.inner, draw))
    return built


def _attempts(name: str, slots: Plan) -> Iterator[Callable[[], dict[str, object]]]:
    """The calls a function is tried with, in order: shared numbers, then drawn.

    Each is a builder of the arguments, which a record of them may refuse,
    so that the refusal is the call's.
    """
    if not slots:
        yield dict
        return
    for number in NUMBERS[:13]:
        yield functools.partial(_shared, slots, number)
    draw = random.Random(name)
    for _ in range(TRIALS):
        yield functools.partial(_drawn, slots, draw)


def _first_call(
    function: Callable[..., object],
    attempts: Iterable[Callable[[], dict[str, object]]],
) -> tuple[bool, object]:
    """Call *function* with each of *attempts* until one is accepted."""
    for arguments in attempts:
        # A call that raises, whatever it raises, returns nothing to judge.
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return True, function(**arguments())
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


def _methods(klass: type) -> Iterator[tuple[str, Callable[..., object]]]:
    for owner in klass.__mro__:
        if not owner.__module__.startswith("phonometry"):
            continue
        for name, member in vars(owner).items():
            if not name.startswith("_") and inspect.isfunction(member):
                yield name, member


def _key(function: Callable[..., object]) -> str:
    """What tells one function from another, inherited by a class or not."""
    target = inspect.unwrap(function)
    return f"{target.__module__}.{target.__qualname__}"


def _published(value: object, found: dict[type, object], depth: int = 0) -> None:
    """The first instance of each class of the package a public table holds."""
    if depth > 1:
        return
    items: Iterable[object] = ()
    if isinstance(value, Mapping):
        items = value.values()
    elif isinstance(value, (tuple, list)):
        items = value
    for item in items:
        klass = type(item)
        if klass.__module__.startswith("phonometry"):
            found.setdefault(klass, item)
        else:
            _published(item, found, depth + 1)


@dataclasses.dataclass(frozen=True)
class Census:
    """What the census found.

    :ivar rows: Every call that returns something other than a number.
    :ivar reached: The functions and methods some call ran, by :func:`_key`.
    """

    rows: tuple[Row, ...]
    reached: frozenset[str]


def _judge(
    name: str,
    function: Callable[..., object],
    rows: list[Row],
    reached: set[str],
    *,
    reduces: bool,
) -> list[object]:
    """Call *function* as the census does and note what it returns."""
    results: list[object] = []
    for optional in (False, True):
        slots = _plan(function, optional=optional)
        if slots is None or (optional and slots == _plan(function)):
            continue
        called, result = _first_call(function, _attempts(name, slots))
        if not called and reduces and not optional:
            called, result = _first_call(
                function,
                (
                    functools.partial(_shared, slots, [n, 1.1 * n, 0.9 * n])
                    for n in NUMBERS[:13]
                ),
            )
            offence = _offence(result) if called and np.ndim(result) == 0 else None
            if offence is not None:
                rows.append((name, f"{offence} for a sequence it reduces"))
            if called:
                reached.add(_key(function))
            continue
        if not called:
            continue
        reached.add(_key(function))
        results.append(result)
        offence = _offence(result)
        if offence is not None:
            rows.append((name, offence))
    return results


@functools.cache
def census() -> Census:
    """Every call the census makes that returns something other than a number."""
    rows: list[Row] = []
    reached: set[str] = set()
    public = list(_public())
    classes = {obj: name for name, obj in public if inspect.isclass(obj)}
    instances: dict[type, object] = {}
    for name, obj in public:
        if not inspect.isfunction(obj) or _SKIPPED.match(name.rpartition(".")[2]):
            continue
        for result in _judge(name, obj, rows, reached, reduces=True):
            if type(result) in classes:
                instances.setdefault(type(result), result)
    published: dict[type, object] = {}
    for _name, obj in public:
        _published(obj, published)
    for cls, instance in published.items():
        if cls in classes:
            instances.setdefault(cls, instance)
    for cls, instance in _fixtures().items():
        instances.setdefault(cls, instance)
    for cls in classes:
        if cls in instances or not dataclasses.is_dataclass(cls):
            continue
        slots = _plan(cls)
        if slots is not None:
            called, built = _first_call(cls, _attempts(classes[cls], slots))
            if called:
                instances[cls] = built
    seen: set[str] = set()
    for cls, instance in instances.items():
        for method, _function in _methods(cls):
            qualified = f"{classes[cls]}.{method}"
            if qualified in seen or _SKIPPED.match(method):
                continue
            seen.add(qualified)
            bound = getattr(instance, method)
            slots = _plan(bound, optional=True)
            if slots is None or not any(
                slot.kind in {"number", "optional"} for slot in slots.values()
            ):
                continue
            _judge(qualified, bound, rows, reached, reduces=False)
    return Census(tuple(sorted(set(rows))), frozenset(reached))


def _names_an_array(text: str, module: types.ModuleType) -> bool:
    """Whether a return annotation names an array, written out or through an alias.

    An alias is read through numpy's ``NDArray`` to the ``np.ndarray`` it
    stands for (:mod:`ndarray_hints`): numpy writes ``NDArray`` as a generic
    alias of ``np.ndarray`` up to 2.4 and as a ``type`` statement from 2.5, so
    the origin of an alias alone tells an array at the dependency floors and
    not at the pins.
    """
    if re.search(r"\b(NDArray|ndarray)\b", text):
        return True
    return any(
        ndarray_of(_loaded(word, module)) is not None
        for word in re.findall(r"\b[A-Za-z_]\w*\b", text)
    )


def _of_numbers_returning_an_array() -> Iterator[tuple[str, Callable[..., object]]]:
    """Every public function and method that takes numbers and returns an array."""
    seen: set[str] = set()
    for name, obj in _public():
        members: list[tuple[str, Callable[..., object]]] = []
        if inspect.isfunction(obj):
            members = [(name, obj)]
        elif inspect.isclass(obj):
            members = [(f"{name}.{method}", member) for method, member in _methods(obj)]
        for qualified, function in members:
            key = _key(function)
            if key in seen or _SKIPPED.match(qualified.rpartition(".")[2]):
                continue
            seen.add(key)
            module = sys.modules[function.__module__]
            hints = function.__annotations__
            returns = hints.get("return")
            if not isinstance(returns, str) or not _names_an_array(returns, module):
                continue
            if any(
                isinstance(text, str) and _ARRAY_INPUT.search(text) and _numeric(text)
                for parameter, text in hints.items()
                if parameter != "return"
            ):
                yield qualified, function


def test_numbers_give_a_number() -> None:
    """No call of numbers returns an array of one value or a numpy scalar."""
    offending = [
        f"{name}: {offence}"
        for name, offence in census().rows
        if name not in NOT_OF_A_NUMBER
    ]
    assert offending == [], (
        "these return an array of one value or a numpy scalar for numbers; "
        "return a float or a complex for them (rule A57):\n" + "\n".join(offending)
    )


def test_every_exemption_is_still_needed() -> None:
    """An entry the census no longer flags is stale."""
    flagged = dict(census().rows)
    stale = sorted(name for name in NOT_OF_A_NUMBER if name not in flagged)
    assert stale == []


def test_every_function_of_numbers_is_reached_or_named() -> None:
    """A function of numbers the census cannot call shows up as a result.

    Every public function and method that returns an array and takes numbers
    is either called by the census or named in :data:`UNREACHED` with the
    reason no call of numbers runs; an entry the census reaches is stale, so
    the list only shrinks.
    """
    reached = census().reached
    unreached = {
        name
        for name, function in _of_numbers_returning_an_array()
        if _key(function) not in reached
    }
    assert sorted(unreached - set(UNREACHED)) == [], "neither reached nor named"
    assert sorted(set(UNREACHED) - unreached) == [], "named but reached or gone"


def test_the_census_calls_the_package() -> None:
    """The census reaches the functions of numbers it exists for.

    A plan that stopped building calls would pass every other test here by
    calling nothing: the functions converted to the complex form and to the
    real one, reached through the aliases their annotations name, a function
    whose call needs each parameter its own number, one with no required
    parameter, and the methods of records the tables of the package and the
    fixtures build, must be among the calls it makes.
    """
    for name, build in FIXTURES.items():
        record = build()
        assert name == f"{name.partition('.')[0]}.{type(record).__name__}", name
        assert getattr(phonometry, name.partition(".")[0]).__dict__[
            type(record).__name__
        ] is type(record), name
    reached = census().reached
    for function in (
        phonometry.materials.normalized_surface_impedance,
        phonometry.materials.helmholtz_resonator_impedance,
        phonometry.noise_control.quarter_wave_impedance,
        phonometry.environment.kurze_anderson_attenuation,
        phonometry.vibration.sdof_mobility,
        phonometry.emission.flow_modal_correction,
        phonometry.noise_control.screen_background_corrected_level,
        phonometry.vibration.machine_count_correction,
        phonometry.emission.radiation_impedance_correction,
        phonometry.metrology.PeakStatisticsResult.peak_exceedance,
        phonometry.aircraft.ANPNPDCurves.level,
        phonometry.materials.AbsorptionSpectrum.values_at,
    ):
        assert _key(function) in reached, _key(function)
