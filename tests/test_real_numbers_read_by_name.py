#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A caller's numbers are read as real numbers, or refused naming the parameter.

``np.asarray(x, dtype=np.float64)`` gives back the real part of a complex
value with no more than a ``ComplexWarning``, parses a text, and reads a
``bytearray`` as the codes of its characters. ISO/TS 12913-3's
``method_b_scale_values`` rated a mark given as ``0.5 + 0.3j`` as the mark at
0.5, and a level spectrum given as ``[bytearray(b"12")]`` was read as two
levels of 49 and 50 dB. Each parameter that takes numbers now reads them
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
    noise_control,
    psychoacoustics,
    room,
    underwater,
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
    """``0.5 + 0.3j`` used to come back as 3.0, the value of the mark at 0.5."""
    with pytest.raises(TypeError, match="'marked_fraction' must be real"):
        environment.method_b_scale_values(np.array([0.5 + 0.3j]))
    with pytest.raises(TypeError, match="'marked_fraction' must be"):
        environment.method_b_scale_values(np.complex128(0.5 + 0.3j))
    assert environment.method_b_scale_values(0.5) == pytest.approx(3.0)
