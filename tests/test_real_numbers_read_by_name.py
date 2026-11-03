#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A caller's numbers are read as real numbers, or refused naming the parameter.

``np.asarray(x, dtype=np.float64)`` gives back the real part of a complex
value with no more than a ``ComplexWarning``, parses a text, and reads a
``bytearray`` as the codes of its characters. ISO/TS 12913-3's
``method_b_scale_values`` rated a mark given as ``np.complex128(0.5 + 0.3j)``
as the mark at 0.5, and a level spectrum given as ``[bytearray(b"12")]`` was
read as two levels of 49 and 50 dB. Each parameter that takes numbers now reads them
through the shared reader of ``_internal/validation.py``, which refuses all
three by the parameter's name; ``scripts/check_real_conversions.py`` holds
the tree to it, and these calls hold a public function of each domain to it
at run time.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry import (
    aircraft,
    building,
    emission,
    environment,
    io,
    materials,
    noise_control,
    psychoacoustics,
    room,
    signals,
    underwater,
    vibration,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

#: A public call per domain, given the numbers it reads, and the name of the
#: parameter that takes them.
_CALLS: list[tuple[str, Callable[[object], object], object, str]] = [
    (
        "environment.method_b_scale_values",
        environment.method_b_scale_values,
        [0.5, 0.25],
        "marked_fraction",
    ),
    (
        "building.energy_average_level",
        building.energy_average_level,
        [60.0, 62.0],
        "levels",
    ),
    (
        "room.directivity_energy_average",
        room.directivity_energy_average,
        [80.0] * 30,
        "levels",
    ),
    (
        "psychoacoustics.erb_bandwidth",
        psychoacoustics.erb_bandwidth,
        [500.0, 1000.0],
        "frequency",
    ),
    (
        "underwater.cumulative_sel",
        underwater.cumulative_sel,
        [150.0, 152.0],
        "single_sels",
    ),
    (
        "emission.background_noise_correction",
        lambda levels: emission.background_noise_correction(levels, [40.0, 40.0]),
        [60.0, 62.0],
        "source_levels",
    ),
    (
        "environment.atmospheric_attenuation",
        environment.atmospheric_attenuation,
        [500.0, 1000.0],
        "frequencies",
    ),
    (
        "noise_control.combined_internal_levels",
        lambda level: noise_control.combined_internal_levels([level, [60.0, 61.0]]),
        [60.0, 62.0],
        "levels",
    ),
]

_IDS = [call[0] for call in _CALLS]


@pytest.mark.parametrize(("label", "call", "numbers", "name"), _CALLS, ids=_IDS)
def test_the_numbers_of_each_call_are_taken(
    label: str, call: Callable[[object], object], numbers: object, name: str
) -> None:
    """The calls below are the right calls: their numbers go through."""
    del label, name
    call(numbers)


def _complex(numbers: list[float]) -> list[complex]:
    return [complex(value, 0.5) for value in numbers]


@pytest.mark.parametrize(("label", "call", "numbers", "name"), _CALLS, ids=_IDS)
@pytest.mark.parametrize(
    "given",
    [
        pytest.param(lambda n: np.asarray(_complex(n)), id="complex-array"),
        pytest.param(
            lambda n: [np.complex128(v) for v in _complex(n)], id="numpy-complex-list"
        ),
    ],
)
@pytest.mark.filterwarnings("error")
def test_a_complex_value_is_refused_naming_the_parameter(
    label: str,
    call: Callable[[object], object],
    numbers: list[float],
    name: str,
    given: Callable[[list[float]], object],
) -> None:
    """The real part of a complex value is a number the caller never gave."""
    del label
    complex_numbers = given(numbers)
    with pytest.raises(TypeError, match=f"'{name}' must be real, not complex"):
        call(complex_numbers)


@pytest.mark.parametrize(("label", "call", "numbers", "name"), _CALLS, ids=_IDS)
@pytest.mark.parametrize(
    "given",
    [
        pytest.param(lambda n: [bytearray(b"12")] * len(n), id="bytearrays"),
        pytest.param(lambda n: [str(v) for v in n], id="texts"),
    ],
)
def test_a_text_is_refused_naming_the_parameter(
    label: str,
    call: Callable[[object], object],
    numbers: list[float],
    name: str,
    given: Callable[[list[float]], object],
) -> None:
    """A text is no number, whatever it reads as, and a ``bytearray`` is one."""
    del label
    texts = given(numbers)
    with pytest.raises(TypeError, match=f"'{name}' must be numbers, not text"):
        call(texts)


def _subclassed(numbers: list[float], kind: str) -> np.ndarray:
    """The numbers as a matrix of one row, or as an array with its last masked."""
    if kind == "matrix":
        return np.matrix(numbers)
    return np.ma.array(numbers, mask=[False] * (len(numbers) - 1) + [True])


def _outcome(call: Callable[[object], object], given: object) -> object:
    """What *call* gives back for *given*, or the refusal it raises, worded."""
    try:
        return call(given)
    except (TypeError, ValueError) as exc:
        return f"{type(exc).__name__}: {exc}"


def _assert_same(got: object, expected: object) -> None:
    """The same type and the same values, a record's field by field."""
    assert type(got) is type(expected)
    if dataclasses.is_dataclass(expected):
        for field in dataclasses.fields(expected):
            _assert_same(getattr(got, field.name), getattr(expected, field.name))
        return
    np.testing.assert_array_equal(got, expected)  # type: ignore[arg-type]


@pytest.mark.parametrize(("label", "call", "numbers", "name"), _CALLS, ids=_IDS)
@pytest.mark.parametrize("kind", ["matrix", "masked"])
@pytest.mark.filterwarnings("ignore:the matrix subclass:PendingDeprecationWarning")
def test_a_subclass_of_an_array_is_read_as_numpy_reads_it(
    label: str,
    call: Callable[[object], object],
    numbers: list[float],
    name: str,
    kind: str,
) -> None:
    """The conversions the reader replaced read a matrix or a masked array as
    the plain array of its values; so does the reader, so a matrix's ``**``
    is no matrix power and a masked value is not skipped by a reduction.
    """
    del label, name
    given = _subclassed(numbers, kind)
    _assert_same(_outcome(call, given), _outcome(call, np.asarray(given)))


@pytest.mark.filterwarnings("ignore:the matrix subclass:PendingDeprecationWarning")
def test_a_matrix_of_mode_orders_is_read_as_the_array_of_them() -> None:
    """Read as a matrix, the orders' ``** 2`` was a matrix power, refused for a
    row of three; read as the array of them, the mode (1, 0, 0) of a 4 m room
    lies at a speed of sound over 8 m.
    """
    got = room.room_mode_frequency(np.matrix([[1, 0, 0]]), [4.0, 5.0, 6.0])
    _assert_same(got, room.room_mode_frequency(np.array([[1, 0, 0]]), [4.0, 5.0, 6.0]))


def test_a_scale_mark_given_as_a_complex_number_is_not_rated() -> None:
    """``np.complex128(0.5 + 0.3j)`` used to come back as 3.0, the value of the
    mark at 0.5; a Python complex raised an anonymous ``TypeError``.
    """
    with pytest.raises(TypeError, match="'marked_fraction' must be real"):
        environment.method_b_scale_values(np.array([0.5 + 0.3j]))
    with pytest.raises(TypeError, match="'marked_fraction' must be"):
        environment.method_b_scale_values(np.complex128(0.5 + 0.3j))
    assert environment.method_b_scale_values(0.5) == pytest.approx(3.0)


_OCTAVES = [63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0]


def _miso_inputs() -> tuple[np.ndarray, np.ndarray]:
    noise = np.random.default_rng(0).standard_normal((3, 4096))
    return noise[:2] + 1j * noise[2], noise[0] + noise[1]


#: Calls that read a caller's value through a path no check covered, each
#: with what it used to take for numbers: the value of the real part, a
#: parsed text, or the codes of a bytearray.
_MISREAD: list[tuple[str, Callable[[], object], str]] = [
    (
        "miso_coherence: a complex 2-D array of inputs",
        lambda: signals.miso_coherence(*_miso_inputs(), fs=1000.0),
        "'inputs' must be real",
    ),
    (
        "environmental_correction: a NumPy complex absorption area",
        lambda: emission.environmental_correction(
            surface_area=20.0, absorption_area=np.complex128(10 + 5j)
        ),
        "'absorption_area' must be real",
    ),
    (
        "environmental_correction: an absorption area as text",
        lambda: emission.environmental_correction(
            surface_area=20.0, absorption_area=["10"]
        ),
        "'absorption_area' must be numbers, not text",
    ),
    (
        "duct_path: a complex source spectrum",
        lambda: noise_control.duct_path(
            np.array([80 + 5j] * 8), [], frequencies=_OCTAVES
        ),
        "'source_level' must be real",
    ),
    (
        "duct_path: a source spectrum of NumPy complex numbers",
        lambda: noise_control.duct_path(
            [np.complex128(80 + 5j)] * 8, [], frequencies=_OCTAVES
        ),
        "'source_level' must be real",
    ),
    (
        "duct_path: a source spectrum as text",
        lambda: noise_control.duct_path(["80"] * 8, [], frequencies=_OCTAVES),
        "'source_level' must be numbers, not text",
    ),
    (
        "duct_path: a source spectrum of bytearrays",
        lambda: noise_control.duct_path(
            [bytearray(b"80")] * 8, [], frequencies=_OCTAVES
        ),
        "'source_level' must be numbers, not text",
    ),
    (
        "duct_path: a NumPy complex self-noise floor",
        lambda: noise_control.duct_path(
            [80.0] * 8,
            [noise_control.DuctElement(label="duct", attenuation=[1.0] * 8)],
            frequencies=_OCTAVES,
            self_noise_floor=np.complex128(5 + 1j),
        ),
        "'self_noise_floor' must be a number, not a complex one",
    ),
    (
        "composite_rating_level: a complex duration",
        lambda: environment.composite_rating_level(
            [(60, np.complex128(12 + 3j), 0), (55, 4, 5), (50, 8, 10)]
        ),
        "'periods' must be real",
    ),
    (
        "composite_rating_level: a complex level",
        lambda: environment.composite_rating_level(
            [(np.complex128(60 + 3j), 12, 0), (55, 4, 5), (50, 8, 10)]
        ),
        "'periods' must be real",
    ),
    (
        "injected_power: a force of bytearrays",
        lambda: vibration.injected_power([bytearray(b"12")], [1e-3 + 1e-4j]),
        "'force_n' must be numbers, not text",
    ),
    (
        "injected_power: a force as text",
        lambda: vibration.injected_power(["2"], [1e-3 + 1e-4j]),
        "'force_n' must be numbers, not text",
    ),
    (
        "absorption_from_reflection: a reflection factor as text",
        lambda: materials.absorption_from_reflection(["0.5"]),
        "'reflection' must be numbers, not text",
    ),
    (
        "coupling_term: a source mobility as text",
        lambda: building.coupling_term(["1e-4"], [1e-5]),
        "'source_mobility' must be numbers, not text",
    ),
    (
        "seawater_absorption: a NumPy complex pH",
        lambda: underwater.seawater_absorption([1000.0], ph=np.complex128(7 + 3j)),
        "'ph' must be a number, not a complex one",
    ),
    (
        "crowd_noise_level: a NumPy complex sound power level",
        lambda: room.crowd_noise_level(
            [10.0] * 8, [100.0] * 8, sound_power_level=np.complex128(70 + 5j)
        ),
        "'sound_power_level' must be a number, not a complex one",
    ),
    (
        "flanking_element: a NumPy complex lining improvement",
        lambda: building.flanking_element(
            label="wall",
            r_flanking=50.0,
            r_separating=52.0,
            k_ff=10.0,
            k_fd=12.0,
            k_df=12.0,
            separating_area=10.0,
            coupling_length=4.0,
            delta_r_ff=np.complex128(1j),
        ),
        "'delta_r_ff' must be a number, not a complex one",
    ),
    (
        "phase_mismatch_from_residual_index: a NumPy complex speed of sound",
        lambda: emission.phase_mismatch_from_residual_index(
            [10.0],
            0.012,
            frequency=[1000.0],
            speed_of_sound=np.complex128(343 + 1j),
        ),
        "'speed_of_sound' must be a number, not a complex one",
    ),
]


@pytest.mark.parametrize(
    ("label", "call", "message"), _MISREAD, ids=[case[0] for case in _MISREAD]
)
def test_a_value_read_off_every_checked_path_is_refused_by_name(
    label: str, call: Callable[[], object], message: str
) -> None:
    """Each call used to return a result from a value the caller never gave."""
    del label
    with pytest.raises(TypeError, match=message):
        call()


_SCAN_AREAS = np.full(4, 0.5)
_SCAN = np.full((4, 1), 5.0e-4)
_SCAN_KEYWORDS: dict[str, object] = {"frequencies": np.array([1000.0]), "fraction": 1}


def _indicators() -> emission.PrecisionFieldIndicators:
    return emission.precision_field_indicators(
        np.full((4, 1), 2.0e-6), np.full((4, 1), 60.0)
    )


#: Calls whose numbers a private helper reads: each refusal names the public
#: parameter, not the helper's own (``'arr'``, ``'value'``,
#: ``'absorption_area'``), and a ``bytearray`` reaches the reader as text,
#: not as the codes ``np.asarray`` made of it before the reader saw it.
_HANDED_ON: list[tuple[str, Callable[[], object], str]] = [
    (
        "sound_power_intensity: a complex second scan",
        lambda: emission.sound_power_intensity(
            _SCAN, _SCAN_AREAS, normal_intensity_2=_SCAN + 0.5j, **_SCAN_KEYWORDS
        ),
        "'normal_intensity_2' must be real, not complex",
    ),
    (
        "sound_power_intensity: a second scan of bytearrays",
        lambda: emission.sound_power_intensity(
            _SCAN,
            _SCAN_AREAS,
            normal_intensity_2=[bytearray(b"1")] * 4,
            **_SCAN_KEYWORDS,
        ),
        "'normal_intensity_2' must be numbers, not text",
    ),
    (
        "sound_power_intensity: complex pressure levels",
        lambda: emission.sound_power_intensity(
            _SCAN, _SCAN_AREAS, pressure_levels=_SCAN + 0.5j, **_SCAN_KEYWORDS
        ),
        "'pressure_levels' must be real, not complex",
    ),
    (
        "sound_power_intensity: pressure levels of bytearrays",
        lambda: emission.sound_power_intensity(
            _SCAN, _SCAN_AREAS, pressure_levels=[bytearray(b"_")] * 4, **_SCAN_KEYWORDS
        ),
        "'pressure_levels' must be numbers, not text",
    ),
    (
        "precision_qualification: a complex first field non-uniformity",
        lambda: emission.precision_qualification(
            _indicators(),
            field_nonuniformity_1=np.array([1.0 + 1.0j]),
            field_nonuniformity_2=np.array([1.0]),
        ),
        "'field_nonuniformity_1' must be real, not complex",
    ),
    (
        "precision_qualification: a complex second field non-uniformity",
        lambda: emission.precision_qualification(
            _indicators(),
            field_nonuniformity_1=np.array([1.0]),
            field_nonuniformity_2=np.array([1.0 + 1.0j]),
        ),
        "'field_nonuniformity_2' must be real, not complex",
    ),
    (
        "room_effect: a complex room constant",
        lambda: noise_control.room_effect(2.0, room_constant=np.array([4.0 + 1.0j])),
        "'room_constant' must be real, not complex",
    ),
    (
        "weighted_absorption: a text in a mapping of bands",
        lambda: materials.weighted_absorption({**_OCTAVE_ALPHA, 250: "bad"}),
        "'alpha_p' must be one number, not a text",
    ),
    (
        "weighted_absorption_from_third_octave: a text in a mapping of bands",
        lambda: materials.weighted_absorption_from_third_octave(
            {**_THIRD_OCTAVE_ALPHA, 200: "bad"}
        ),
        "'third_octave_alpha_s' must be one number, not a text",
    ),
    (
        "practical_absorption_coefficient: a text in a mapping of bands",
        lambda: materials.practical_absorption_coefficient(
            {**_THIRD_OCTAVE_ALPHA, 200: "bad"}
        ),
        "'third_octave_alpha_s' must be one number, not a text",
    ),
    (
        "event_level: a text among the exposure levels",
        lambda: aircraft.event_level(
            _PATH, [0.0, 0.0, 0.0], _POWERS, _DISTANCES, [["x"] * 3] * 2, _NPD
        ),
        "'exposure_levels' must be numbers, not text",
    ),
    (
        "noise_contour: a text among the maximum levels",
        lambda: aircraft.noise_contour(
            _PATH,
            _POWERS,
            _DISTANCES,
            _NPD,
            [["x"] * 3] * 2,
            x=[0.0, 100.0],
            y=[0.0, 100.0],
        ),
        "'max_levels' must be numbers, not text",
    ),
    (
        "sound_intensity: a text for the speed of sound",
        lambda: emission.sound_intensity(
            _PROBE, _PROBE, 48000, spacing_m=0.012, speed_of_sound="343"
        ),
        "'speed_of_sound' must be one number, not a text",
    ),
    (
        "sound_intensity: a text for the density",
        lambda: emission.sound_intensity(
            _PROBE, _PROBE, 48000, spacing_m=0.012, density="1.2"
        ),
        "'density' must be one number, not a text",
    ),
    (
        "sound_intensity: a text for the spacing",
        lambda: emission.sound_intensity(_PROBE, _PROBE, 48000, spacing_m="0.012"),
        "'spacing_m' must be one number, not a text",
    ),
    (
        "room_absorption_coefficient: a text for the surface area",
        lambda: emission.room_absorption_coefficient(
            [1.0], volume=100.0, surface_area="130"
        ),
        "'surface_area' must be one number, not a text",
    ),
    (
        "barrier_insertion_loss: a text for the barrier height",
        lambda: environment.barrier_insertion_loss([500.0], 1.0, 5.0, "3", 5.0, 1.0),
        "'barrier_height_m' must be one number, not a text",
    ),
    (
        "lined_rectangular_duct_attenuation: a text for the width",
        lambda: noise_control.lined_rectangular_duct_attenuation(
            None, "0.3", 0.3, 3.0, 0.025
        ),
        "'width_m' must be one number, not a text",
    ),
    (
        "elbow_insertion_loss: a text for the width of a VDI 2081 bend",
        lambda: noise_control.elbow_insertion_loss([500.0], "0.3", model="vdi2081"),
        "'width_m' must be one number, not a text",
    ),
    (
        "reflection_index: a text among the directivity corrections",
        lambda: environment.reflection_index(
            [np.zeros(64)] * 9,
            [np.zeros(64)] * 9,
            48000,
            speed_of_sound=343.0,
            directivity_corrections=[["x"] * 18] * 9,
        ),
        "'directivity_corrections' must be numbers, not text",
    ),
]

#: A small table the calls above read: two powers, three distances.
_POWERS = [1000.0, 2000.0]
_DISTANCES = [100.0, 200.0, 400.0]
_NPD = np.full((2, 3), 80.0)
_PATH = np.array(
    [[0.0, -1000.0, 300.0, 70.0, 1000.0], [0.0, 1000.0, 300.0, 70.0, 1000.0]]
)
_PROBE = np.random.default_rng(0).standard_normal(4096)
_OCTAVE_ALPHA: dict[int, object] = dict.fromkeys(materials.RATING_OCTAVE_BANDS_HZ, 0.5)
_THIRD_OCTAVE_ALPHA: dict[int, object] = dict.fromkeys(
    materials.RATING_THIRD_OCTAVE_BANDS_HZ, 0.5
)
_ROUGHNESS = environment.AcousticRoughnessSpectrum(
    wavelengths_m=sorted(environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB, reverse=True),
    levels=[
        environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB[w] - 1.0
        for w in sorted(environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB, reverse=True)
    ],
)

#: The refusals of a value's size or range that a private helper writes,
#: each of which named the helper's own variable.
_HANDED_ON_RANGE: list[tuple[str, Callable[[], object], str]] = [
    (
        "event_level: maximum levels of the wrong shape",
        lambda: aircraft.event_level(
            _PATH, [0.0, 0.0, 0.0], _POWERS, _DISTANCES, _NPD, np.full((3, 3), 80.0)
        ),
        "'max_levels' must have shape",
    ),
    (
        "qualification_frequencies: a lowest band below zero",
        lambda: emission.qualification_frequencies(-1.0, high_hz=1000.0),
        "'low_hz' must be positive and finite",
    ),
    (
        "qualification_frequencies: a highest band that is no number",
        lambda: emission.qualification_frequencies(100.0, high_hz=float("nan")),
        "'high_hz' must be positive and finite",
    ),
    (
        "roughness_comparability: a second noise spectrum of the wrong length",
        lambda: environment.roughness_comparability(
            _ROUGHNESS,
            _ROUGHNESS,
            [80.0, 81.0],
            [80.0],
            frequencies=[500.0, 630.0],
            speed_kmh=80.0,
        ),
        "'noise_levels_2' and 'frequencies' need one value per band each",
    ),
]


@pytest.mark.parametrize(
    ("label", "call", "message"), _HANDED_ON, ids=[case[0] for case in _HANDED_ON]
)
def test_a_value_a_helper_reads_is_refused_by_the_public_name(
    label: str, call: Callable[[], object], message: str
) -> None:
    """Each refusal named the helper's parameter; two scans of bytearrays
    were read as the codes of their characters and gave a result.
    """
    del label
    with pytest.raises(TypeError, match=message):
        call()


@pytest.mark.parametrize(
    ("label", "call", "message"),
    _HANDED_ON_RANGE,
    ids=[case[0] for case in _HANDED_ON_RANGE],
)
def test_a_value_a_helper_refuses_is_named_by_the_public_name(
    label: str, call: Callable[[], object], message: str
) -> None:
    """Each refusal named the helper's variable (``'levels'``,
    ``'frequencies'``, ``'noise_levels'``) where the caller wrote another.
    """
    del label
    with pytest.raises(ValueError, match=message):
        call()


def test_a_bytearray_given_as_samples_is_not_written(tmp_path: Path) -> None:
    """``np.asarray`` read a list of ``bytearray`` as an integer array of the
    codes of its characters, which the writer passed through as samples: the
    file held 97, 98, 99 and 100.
    """
    target = tmp_path / "codes.wav"
    with pytest.raises(TypeError, match="'x' must be numbers, not text"):
        io.write(target, [bytearray(b"abcd")], fs=8000)
    assert not target.exists()
