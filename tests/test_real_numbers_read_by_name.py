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

from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry import (
    building,
    emission,
    environment,
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
