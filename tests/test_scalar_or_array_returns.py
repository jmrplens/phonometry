#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A function of a number or an array of them returns what its overloads say.

An array in, an array out: such a function returns a Python ``float`` (a
string, for a grade) only when every argument that decides the shape of the
result is a number, and an array as soon as one of them is a sequence or a
numpy array, a zero-dimensional array included. Its ``typing.overload``
heads say the same to a type checker, and these tests hold the runtime to
them, call by call:

* every public function whose heads tell a single value from an array has a
  case here, so a new one cannot ship without its runtime being checked;
* with numbers, Python or numpy ones, it returns a ``float``, compared with
  ``type(r) is float`` so that a ``numpy.float64`` (which is a ``float``
  subclass) does not pass for one;
* with each deciding argument in turn given as a list, it returns an array,
  and as a zero-dimensional array it returns a zero-dimensional array, each
  holding the value the numbers gave.

The functions keyed on another argument (``axis``, ``limits``, ``weighted``,
a missing ``frequency``) have a test of their own below.
"""

from __future__ import annotations

import ast
import functools
import importlib
import inspect
import pathlib
import sys
import types
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

import phonometry
from phonometry import (
    broadcast,
    building,
    electroacoustics,
    emission,
    environment,
    fluids,
    hearing,
    materials,
    noise_control,
    psychoacoustics,
    room,
    vibration,
)

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import ast_scan
import check_return_overloads as cro

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from numpy.typing import NDArray

_ZONES = vibration.ZoneBoundaries(a_b=1.0, b_c=2.0, c_d=3.0)


@dataclass(frozen=True)
class Case:
    """One call of a function of a number or an array of them.

    :ivar function: The public function or method, as a caller reaches it.
    :ivar arguments: Keyword arguments that make a valid call, every deciding
        one a Python number.
    :ivar deciding: The arguments whose shape the result follows.
    :ivar single: What the function returns for numbers: ``float``, or
        ``str`` for a grade.
    :ivar together: Whether the deciding arguments take one shape between
        them (one value per band each) rather than broadcasting, so that a
        sequence is given to all of them at once.
    :ivar label: Tells two cases of one function apart.
    """

    function: Callable[..., object]
    arguments: Mapping[str, Any]
    deciding: tuple[str, ...]
    single: type = float
    together: bool = False
    label: str = field(default="")

    @property
    def name(self) -> str:
        """The qualified name of the function, which the cases are keyed by."""
        target = inspect.unwrap(self.function)
        return f"{target.__module__}.{target.__qualname__}"

    def call(self, **changed: object) -> object:
        """Call the function with *changed* in place of the case's arguments."""
        return self.function(**{**self.arguments, **changed})


def _cases() -> tuple[Case, ...]:
    modes = room.room_modes(
        (7.0, 5.0, 3.0), max_frequency=120.0, reverberation_time=0.8
    )
    shear = environment.wind_shear_profile(5.0, 9.0, upper_height_m=120.0)
    sel = environment.sel_distribution(
        [30.0, 33.0, 36.0, 41.0, 45.0], [0.3, 0.3, 0.2, 0.15, 0.05]
    )
    box = (7.0, 5.0, 3.0)
    return (
        Case(
            broadcast.channel_weight,
            {"azimuth": 90.0, "elevation": 10.0},
            ("azimuth", "elevation"),
        ),
        Case(electroacoustics.piston_resistance, {"x": 1.0}, ("x",)),
        Case(electroacoustics.piston_reactance, {"x": 1.0}, ("x",)),
        Case(
            electroacoustics.piston_directivity,
            {"ka": 2.0, "theta": 0.3},
            ("ka", "theta"),
        ),
        Case(
            emission.plant_background_correction,
            {"level_difference": 8.0},
            ("level_difference",),
        ),
        Case(emission.local_environmental_correction, {"ratio": 0.5}, ("ratio",)),
        Case(emission.precision_uncertainty, {"sigma_r0": 0.5}, ("sigma_r0",)),
        Case(
            emission.turbine_background_correction,
            {"level_difference": 8.0},
            ("level_difference",),
        ),
        Case(
            emission.environmental_ratio_from_absorption,
            {
                "absorption_area": 50.0,
                "measurement_surface_m2": 20.0,
                "directivity_index": 1.0,
            },
            ("absorption_area", "directivity_index"),
        ),
        Case(
            emission.environmental_ratio_from_k2,
            {"environmental_correction": 1.0, "directivity_index": 1.0},
            ("environmental_correction", "directivity_index"),
        ),
        Case(
            emission.emission_sound_pressure_level,
            {
                "measured_level": 80.0,
                "background_correction": 0.5,
                "local_correction": 1.0,
            },
            ("measured_level", "background_correction", "local_correction"),
        ),
        Case(
            emission.excess_sound_pressure_level,
            {"level": 80.0, "reference_sound_power_levels": 90.0, "distance": 2.0},
            ("level", "reference_sound_power_levels", "distance"),
        ),
        Case(
            emission.environmental_correction,
            {"surface_area": 20.0, "absorption_area": 50.0},
            ("absorption_area",),
            label="absorption area",
        ),
        Case(
            emission.environmental_correction,
            {"surface_area": 20.0, "reverberation_time": 1.0, "volume": 100.0},
            ("reverberation_time",),
            label="reverberation time",
        ),
        Case(
            emission.environmental_correction,
            {
                "surface_area": 20.0,
                "mean_absorption_coefficient": 0.3,
                "room_surface": 150.0,
            },
            ("mean_absorption_coefficient",),
            label="mean absorption",
        ),
        Case(
            environment.method_a_scale_values,
            {"positions": 2.0, "part": 1},
            ("positions",),
        ),
        Case(
            environment.method_b_scale_values,
            {"marked_fraction": 0.5},
            ("marked_fraction",),
        ),
        Case(
            environment.amplitude_modulation_adjustment,
            {"modulation_depth_db": 4.0},
            ("modulation_depth_db",),
        ),
        Case(
            environment.logarithmic_wind_speed,
            {"reference_speed_m_s": 5.0, "height_m": 100.0, "reference_height_m": 10.0},
            ("reference_speed_m_s",),
        ),
        Case(
            environment.power_law_wind_speed,
            {
                "reference_speed_m_s": 5.0,
                "height_m": 100.0,
                "reference_height_m": 10.0,
                "shear_exponent": 0.2,
            },
            ("reference_speed_m_s", "shear_exponent"),
        ),
        Case(
            environment.wind_shear_exponent,
            {
                "speed_m_s": 7.0,
                "reference_speed_m_s": 5.0,
                "height_m": 100.0,
                "reference_height_m": 10.0,
            },
            ("speed_m_s", "reference_speed_m_s"),
        ),
        Case(
            environment.background_level_increase,
            {"measured_level": 70.0, "background_level": 60.0},
            ("measured_level", "background_level"),
            together=True,
        ),
        Case(shear.speed_at, {"height_m": 80.0}, ("height_m",)),
        Case(sel.class_density, {"levels": 35.0}, ("levels",)),
        Case(sel.density, {"levels": 35.0}, ("levels",)),
        Case(sel.exceedance, {"levels": 35.0}, ("levels",)),
        Case(sel.exceedance_level, {"percent": 10.0}, ("percent",)),
        Case(
            fluids.sea_water_sound_speed,
            {"temperature_c": 10.0, "salinity_psu": 35.0, "depth_m": 100.0},
            ("temperature_c", "salinity_psu", "depth_m"),
        ),
        Case(
            hearing.min_significant_difference,
            {"expanded_uncertainty_db": 2.0},
            ("expanded_uncertainty_db",),
        ),
        Case(
            materials.apparent_dynamic_stiffness,
            {"resonant_frequency_hz": 50.0, "total_mass_per_area_kg_m2": 8.0},
            ("resonant_frequency_hz",),
        ),
        Case(
            materials.enclosed_gas_stiffness,
            {"thickness_m": 0.02, "porosity": 0.9},
            ("thickness_m",),
        ),
        Case(
            materials.natural_frequency,
            {"dynamic_stiffness_n_m3": 1.0e7, "mass_per_area_kg_m2": 100.0},
            ("dynamic_stiffness_n_m3",),
        ),
        Case(
            noise_control.plenum_attenuation,
            {
                "exit_area": 0.5,
                "line_of_sight": 2.0,
                "wall_area": 20.0,
                "mean_absorption": 0.3,
            },
            ("mean_absorption",),
        ),
        Case(
            noise_control.room_effect,
            {"distance": 2.0, "room_constant": 50.0, "directivity": 2.0},
            ("room_constant", "directivity"),
            label="room constant",
        ),
        Case(
            noise_control.room_effect,
            {"distance": 2.0, "absorption_area": 50.0, "directivity": 2.0},
            ("absorption_area", "directivity"),
            label="absorption area",
        ),
        Case(psychoacoustics.erb_bandwidth, {"frequency": 1000.0}, ("frequency",)),
        Case(psychoacoustics.cam_from_frequency, {"frequency": 1000.0}, ("frequency",)),
        Case(psychoacoustics.frequency_from_cam, {"cam": 15.0}, ("cam",)),
        Case(modes.density, {"frequency": 100.0}, ("frequency",)),
        Case(
            room.absorption_per_table,
            {"distance": 1.0, "speech_to_noise": 3.0},
            ("distance",),
        ),
        Case(room.air_absorption_area, {"m": 0.001, "volume": 100.0}, ("m",)),
        Case(
            room.critical_distance,
            {"room_constant": 50.0, "directivity": 2.0},
            ("room_constant", "directivity"),
            label="room constant",
        ),
        Case(
            room.critical_distance,
            {"absorption_area": 50.0, "directivity": 2.0},
            ("absorption_area", "directivity"),
            label="absorption area",
        ),
        Case(
            room.crowd_noise_level,
            {"talkers": 10.0, "absorption_area": 50.0},
            ("talkers", "absorption_area"),
        ),
        Case(room.filter_bandwidth, {"center": 1000.0}, ("center",)),
        Case(
            room.free_field_reference_level,
            {"level": 80.0, "distance": 10.0},
            ("level",),
        ),
        Case(room.min_receiver_positions, {"seats": 800.0}, ("seats",)),
        Case(
            room.min_reliable_reverberation_time, {"bandwidth": 100.0}, ("bandwidth",)
        ),
        Case(room.reflection_density, {"time": 0.1, "volume": 100.0}, ("time",)),
        Case(
            room.reverberation_room_reference_level,
            {"reverberation_room_level": 80.0, "absorption_area": 20.0},
            ("reverberation_room_level", "absorption_area"),
        ),
        Case(
            room.reverberation_time,
            {"absorption_area": 20.0, "volume": 100.0},
            ("absorption_area",),
        ),
        Case(
            room.room_constant,
            {"surface_area": 100.0, "mean_absorption": 0.2},
            ("mean_absorption",),
        ),
        Case(
            room.room_modal_density,
            {"dimensions": box, "frequency": 100.0},
            ("frequency",),
        ),
        Case(
            room.room_mode_count,
            {"dimensions": box, "frequency": 100.0},
            ("frequency",),
        ),
        Case(
            room.sabine_absorption_area,
            {"volume": 100.0, "reverberation_time": 1.0},
            ("reverberation_time",),
        ),
        Case(
            room.schroeder_frequency,
            {"reverberation_time": 1.0, "volume": 100.0},
            ("reverberation_time",),
        ),
        Case(
            room.sound_strength_from_power,
            {"pressure_level": 80.0, "power_level": 90.0},
            ("pressure_level", "power_level"),
        ),
        Case(room.speech_direct_level, {"distance": 1.0}, ("distance",)),
        Case(
            room.speech_to_noise_ratio,
            {"distance": 1.0, "absorption_per_table": 5.0},
            ("distance", "absorption_per_table"),
        ),
        Case(
            vibration.allowable_velocity,
            {
                "frequency": 50.0,
                "constant_velocity_mm_s": 4.5,
                "corner_low_hz": 10.0,
                "corner_high_hz": 1000.0,
            },
            ("frequency",),
        ),
        Case(
            vibration.gear_housing_velocity_limit,
            {"frequency": 50.0, "rating": 4.5},
            ("frequency",),
        ),
        Case(
            vibration.gear_shaft_displacement_limit,
            {"frequency": 50.0, "rating": 100.0},
            ("frequency",),
        ),
        Case(
            vibration.bending_stress,
            {
                "peak_velocity_m_s": 0.01,
                "dynamic_modulus_pa": 3.0e10,
                "density": 2400.0,
            },
            ("peak_velocity_m_s",),
        ),
        Case(
            vibration.guideline_velocity,
            {"building_class": "residential", "frequency": 20.0},
            ("frequency",),
        ),
        Case(vibration.height_fundamental_frequency, {"height_m": 30.0}, ("height_m",)),
        Case(vibration.injury_probability, {"risk": 0.5}, ("risk",)),
        Case(
            vibration.evaluation_zone,
            {"magnitude": 2.5, "boundaries": _ZONES},
            ("magnitude",),
            single=str,
        ),
        Case(
            vibration.industrial_machine_zone,
            {
                "group": "group_1",
                "support": "rigid",
                "displacement_um": 40.0,
                "velocity_mm_s": 2.0,
            },
            ("displacement_um", "velocity_mm_s"),
            single=str,
        ),
    )


CASES = _cases()

#: The functions keyed on another argument than the shape of their input,
#: each held by a test of its own below.
_KEYED = frozenset(
    {
        "phonometry.room.auditorium.sound_pressure_exposure_level",
        "phonometry.vibration.immission.railway.passage_average_level",
        "phonometry.building.measurement.survey_insulation.estimate_reverberation_index",
    }
)


def _ids(case: Case) -> str:
    return (
        f"{case.name.rpartition('.')[2]} ({case.label})"
        if case.label
        else case.name.rpartition(".")[2]
    )


def _public_callables() -> Iterator[Callable[..., object]]:
    """Every public function and method of the package, once each."""
    seen: set[int] = set()
    for package in phonometry.__all__:
        module = getattr(phonometry, package)
        if not isinstance(module, types.ModuleType):
            continue
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name, None)
            members: list[object] = [obj]
            if inspect.isclass(obj):
                members = [
                    member
                    for member_name, member in vars(obj).items()
                    if not member_name.startswith("_")
                ]
            for member in members:
                function = member.fget if isinstance(member, property) else member
                if inspect.isfunction(function) and id(function) not in seen:
                    seen.add(id(function))
                    yield function


@functools.cache
def _source() -> cro.Package:
    """The package as the gate reads it: every head, its aliases expanded."""
    return cro.Package(ast_scan.python_files([], cro.SOURCE), cro.SOURCE)


def _tells_a_value_from_an_array(function: Callable[..., object]) -> bool:
    """Whether the heads of *function* return a single value alone and an array alone.

    Read from the source by the gate's own reader, so a head that spells the
    array or the value through an alias (``Real``, ``Grade``) or as a numpy
    scalar is classified as the gate classifies it.
    """
    package = _source()
    read = package.functions.get(f"{function.__module__}.{function.__qualname__}")
    return read is not None and cro.tells_a_value_from_an_array(package, read)


def test_every_function_of_a_number_or_an_array_has_a_case() -> None:
    """A new overloaded function cannot ship without its runtime being called."""
    named = {case.name for case in CASES} | _KEYED
    found = {
        f"{function.__module__}.{function.__qualname__}"
        for function in _public_callables()
        if _tells_a_value_from_an_array(function)
    }
    assert found - named == set(), "overloaded with no case here"
    assert named - found == set(), "a case for a function the heads do not split"


@pytest.mark.parametrize("case", CASES, ids=_ids)
def test_numbers_give_a_single_value(case: Case) -> None:
    """Python numbers in, a Python ``float`` (or a grade) out, not a numpy scalar."""
    result = case.call()
    assert type(result) is case.single


@pytest.mark.parametrize("case", CASES, ids=_ids)
@pytest.mark.parametrize("kind", [np.float64, np.float32])
def test_numpy_numbers_give_a_single_value(case: Case, kind: type[np.floating]) -> None:
    """A numpy number is a number: it gives what a Python one gives."""
    changed = {name: kind(case.arguments[name]) for name in case.deciding}
    assert type(case.call(**changed)) is case.single


@pytest.mark.parametrize("case", CASES, ids=_ids)
def test_a_sequence_gives_an_array(case: Case) -> None:
    """Each deciding argument given as a list makes the result an array."""
    expected = case.call()
    groups = [case.deciding] if case.together else [(name,) for name in case.deciding]
    for names in groups:
        result = case.call(
            **{name: [case.arguments[name], case.arguments[name]] for name in names}
        )
        assert isinstance(result, np.ndarray), names
        assert result.shape == (2,), names
        np.testing.assert_array_equal(result, [expected, expected])


@pytest.mark.parametrize("case", CASES, ids=_ids)
def test_a_zero_dimensional_array_gives_one(case: Case) -> None:
    """An array in, an array out, even with nothing to broadcast."""
    expected = case.call()
    for name in case.deciding:
        result = case.call(**{name: np.asarray(case.arguments[name])})
        assert isinstance(result, np.ndarray), name
        assert result.ndim == 0, name
        assert result[()] == expected, name


def test_the_exposure_level_is_keyed_on_limits() -> None:
    """``limits=None`` reads the broadband response, one number; bands give one each."""
    rng = np.random.default_rng(1)
    ir = rng.standard_normal(4800) * np.exp(-np.arange(4800) / 600.0)
    broadband = room.sound_pressure_exposure_level(ir, 48000, limits=None)
    banded = room.sound_pressure_exposure_level(ir, 48000)
    assert type(broadband) is float
    assert isinstance(banded, np.ndarray)
    assert banded.ndim == 1


def test_the_passage_average_is_keyed_on_axis() -> None:
    """Without ``axis`` every level is averaged to one; with one, an array is left."""
    levels = np.array([[60.0, 62.0], [61.0, 63.0]])
    assert type(vibration.passage_average_level(levels)) is float
    per_band = vibration.passage_average_level(levels, axis=0)
    assert isinstance(per_band, np.ndarray)
    assert per_band.shape == (2,)
    # One dimension averaged over its axis leaves a zero-dimensional array, as
    # the head for a given axis says, not a float.
    reduced = vibration.passage_average_level([60.0, 70.0], axis=0)
    assert isinstance(reduced, np.ndarray)
    assert reduced.ndim == 0


def test_only_the_route_k2_reads_decides_its_shape() -> None:
    """``absorption_area`` wins over the pairs, and ``T`` over ``alpha``.

    The input of a route that is not read never reaches the result, so an
    array handed to it leaves the number the route read gave.
    """
    by_area = emission.environmental_correction(20.0, absorption_area=50.0)
    unread_t = emission.environmental_correction(
        20.0, absorption_area=50.0, reverberation_time=[1.0, 2.0], volume=100.0
    )
    assert type(unread_t) is float
    assert unread_t == by_area
    by_t = emission.environmental_correction(20.0, reverberation_time=1.0, volume=100.0)
    unread_alpha = emission.environmental_correction(
        20.0,
        reverberation_time=1.0,
        volume=100.0,
        mean_absorption_coefficient=[0.2, 0.3],
        room_surface=150.0,
    )
    assert type(unread_alpha) is float
    assert unread_alpha == by_t
    per_band = emission.environmental_correction(
        20.0, absorption_area=[50.0, 60.0], reverberation_time=1.0, volume=100.0
    )
    assert isinstance(per_band, np.ndarray)
    assert per_band.shape == (2,)


def test_the_reverberation_index_is_keyed_on_weighted() -> None:
    """The weighted index is one number, the unweighted one a band each."""
    assert (
        type(building.estimate_reverberation_index(30.0, "furnished", weighted=True))
        is float
    )
    bands = building.estimate_reverberation_index(30.0, "furnished")
    assert isinstance(bands, np.ndarray)


def test_a_guideline_without_a_frequency_is_one_number() -> None:
    """The floors and the long-term table read no frequency, and print one value."""
    top = vibration.guideline_velocity("residential", location="top_floor")
    assert type(top) is float


def test_a_validator_s_one_element_array_is_read_as_the_number_it_holds() -> None:
    """A one-element list is a sequence, and gives a one-element array back."""
    single = emission.local_environmental_correction(0.5)
    listed = emission.local_environmental_correction([0.5])
    assert type(single) is float
    assert isinstance(listed, np.ndarray)
    assert listed.shape == (1,)
    assert listed[0] == single


def test_the_piston_functions_return_a_python_float() -> None:
    """They returned ``numpy.float64`` through ``out[()]``; a number gives a ``float`` now."""
    for function in (
        electroacoustics.piston_resistance,
        electroacoustics.piston_reactance,
    ):
        assert type(function(1.0)) is float
    assert type(electroacoustics.piston_directivity(2.0, 0.3)) is float


def _stationary(f1: float | NDArray[np.float64]) -> object:
    return emission.FieldStationarityCheck(f1).stationary


def _workstation_correction(margin: float | NDArray[np.float64]) -> object:
    return emission.WorkstationBackgroundCorrection(margin).correction


@pytest.mark.parametrize(
    ("read", "number", "single"),
    [(_stationary, 0.3, bool), (_workstation_correction, 8.0, float)],
    ids=[
        "FieldStationarityCheck.stationary",
        "WorkstationBackgroundCorrection.correction",
    ],
)
def test_the_two_properties_follow_the_field_they_read(
    read: Callable[[float | NDArray[np.float64]], object], number: float, single: type
) -> None:
    """A property has no argument to overload on: the field it reads decides its form."""
    expected = read(number)
    assert type(expected) is single
    assert type(read(np.float64(number))) is single
    listed = read(np.array([number, number]))
    assert isinstance(listed, np.ndarray)
    assert listed.shape == (2,)
    zero = read(np.asarray(number))
    assert isinstance(zero, np.ndarray)
    assert zero.ndim == 0
    assert zero[()] == expected


def test_the_helper_refuses_a_result_its_like_does_not_shape() -> None:
    """An argument left out of ``like`` that does shape the result fails loudly."""
    from phonometry._internal.types import as_float_or_array

    with pytest.raises(ValueError, match="missing from 'like'"):
        as_float_or_array(np.array([1.0, 2.0]), like=(1.0,))


def test_the_modules_of_the_cases_import() -> None:
    """Each case names a function its module still defines."""
    for case in CASES:
        module = importlib.import_module(inspect.unwrap(case.function).__module__)
        assert module is not None


#: The shortest run of words a return description may not say twice: five
#: words of 25 characters or more. A formula left behind beside the sentence
#: that took its place (``:math:`A_{\text{air}} = 4 m V (1 - \psi)`, m2``) is
#: a run of five words that short, and no return description of the package
#: repeats one on purpose.
_REPEATED_WORDS = 5
_REPEATED_CHARACTERS = 25


def _repeated_phrase(text: str, span: int = _REPEATED_WORDS) -> str | None:
    """A run of ``span`` words, :data:`_REPEATED_CHARACTERS` long or more, said twice."""
    words = text.split()
    first: dict[str, int] = {}
    for start in range(len(words) - span + 1):
        phrase = " ".join(words[start : start + span])
        if len(phrase) < _REPEATED_CHARACTERS:
            continue
        if phrase in first and start - first[phrase] >= span:
            return phrase
        first.setdefault(phrase, start)
    return None


def _return_blocks(source: str) -> list[tuple[int, str]]:
    """``(line, text)`` of every ``:return:`` field of every docstring in ``source``."""
    blocks: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Module
        ):
            continue
        doc = ast.get_docstring(node, clean=False)
        if not doc:
            continue
        lines = doc.split("\n")
        for index, line in enumerate(lines):
            if not line.strip().startswith((":return:", ":returns:")):
                continue
            indent = len(line) - len(line.lstrip())
            body = [line.strip()]
            for following in lines[index + 1 :]:
                if not following.strip():
                    break
                if len(following) - len(following.lstrip()) <= indent:
                    break
                body.append(following.strip())
            blocks.append((getattr(node, "lineno", 1), " ".join(body)))
    return blocks


def test_a_return_description_says_its_rule_once() -> None:
    """A ``:return:`` field states what the function returns once.

    Rewriting a return to state the array rule left the old sentence behind
    it in four places (``room.mean_absorption``,
    ``vibration.injury_probability``, and the reverberation time and the air
    absorption area of ``room.enclosed_space_absorption``), so their
    reference pages gave the formula and the rule twice in two wordings.
    """
    package = pathlib.Path(phonometry.__file__).parent
    repeated = []
    for path in sorted(package.rglob("*.py")):
        for line, text in _return_blocks(path.read_text(encoding="utf-8")):
            phrase = _repeated_phrase(text)
            if phrase is not None:
                repeated.append(f"{path.relative_to(package)}:{line}: {phrase!r}")
    assert not repeated, "\n".join(repeated)
