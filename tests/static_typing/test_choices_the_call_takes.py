#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A choice offers the values its call takes, and no value the call refuses.

``straight_transmission_coefficient`` is typed with the two junctions that
have a straight section, ``"X"`` and ``"T1"``: Hopkins gives ``J3`` under
Eq. 5.13 for these alone, so the ``"T2"`` and ``"L"`` that the corner
coefficient takes always raised. ``improvement_octave_bands`` is typed with
the three quantities it folds by the average of transmitted power; the
rainfall intensity levels an ``OctaveBandSpectrum`` also holds sum their
energy instead (ISO 10140-1 Formula (K.3)), and the call always refused
them. A type checker now refuses each of those values, and the call's error
says why.

Each refused value is written as a caller types it, on a call line of its own
with the error code mypy reports for it, so that line's ignore becomes unused,
and fails, the day the annotation offers that value again. The cases that run
every refused value through the call reach it through a reference typed
``Callable[..., object]``: they hold what the call does when it runs, and
carry no ignore, so none of them needs an ignore that could never become
unused. CI type checks every file in this directory alongside ``src`` and
``scripts``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry import building, vibration

if TYPE_CHECKING:
    from collections.abc import Callable

#: The calls the runtime cases make, with no type to hold their argument to.
_STRAIGHT: Callable[..., object] = vibration.straight_transmission_coefficient
_OCTAVE_BANDS: Callable[..., object] = building.improvement_octave_bands


@pytest.mark.parametrize("junction", ["T2", "L"])
def test_a_junction_without_a_straight_section_is_refused(junction: str) -> None:
    with pytest.raises(ValueError, match=rf"junction '{junction}' has no straight"):
        _STRAIGHT(0.0, 1.0, 1.0, junction)


def test_the_type_checker_refuses_the_t2_junction() -> None:
    with pytest.raises(ValueError, match="has no straight section"):
        vibration.straight_transmission_coefficient(
            0.0,
            1.0,
            1.0,
            "T2",  # type: ignore[arg-type]
        )


def test_the_type_checker_refuses_the_l_junction() -> None:
    with pytest.raises(ValueError, match="has no straight section"):
        vibration.straight_transmission_coefficient(
            0.0,
            1.0,
            1.0,
            "L",  # type: ignore[arg-type]
        )


def test_the_two_straight_junctions_are_taken() -> None:
    x = vibration.straight_transmission_coefficient(0.0, 1.0, 1.0, "X")
    t1 = vibration.straight_transmission_coefficient(0.0, 1.0, 1.0, "T1")
    assert float(x) == pytest.approx(1.0 / 8.0)
    assert float(t1) == pytest.approx(2.0 / 9.0)


def test_the_straight_average_keeps_refusing_a_corner_only_junction() -> None:
    with pytest.raises(ValueError, match="junction 'T2' has no straight section"):
        vibration.angular_average_transmission_coefficient(
            1.0, 1.0, "T2", section="straight"
        )
    result = vibration.junction_transmission(
        "L", 0.1, 3500.0, 230.0, 0.1, 3500.0, 230.0
    )
    assert result.straight is None
    assert result.straight_average is None


@pytest.mark.parametrize("quantity", ["LI", "LI,norm"])
def test_a_rainfall_level_is_refused_by_the_octave_average(quantity: str) -> None:
    with pytest.raises(ValueError, match=r"Formula \(K\.3\)"):
        _OCTAVE_BANDS(
            np.array([6.0, 10.0, 14.0]),
            frequencies=[400.0, 500.0, 630.0],
            quantity=quantity,
        )


def test_the_type_checker_refuses_the_rainfall_intensity_level() -> None:
    with pytest.raises(ValueError, match="RainfallSoundResult.octave_bands"):
        building.improvement_octave_bands(
            np.array([6.0, 10.0, 14.0]),
            frequencies=[400.0, 500.0, 630.0],
            quantity="LI",  # type: ignore[arg-type]
        )


def test_the_type_checker_refuses_the_normalized_rainfall_level() -> None:
    with pytest.raises(ValueError, match="RainfallSoundResult.octave_bands"):
        building.improvement_octave_bands(
            np.array([6.0, 10.0, 14.0]),
            frequencies=[400.0, 500.0, 630.0],
            quantity="LI,norm",  # type: ignore[arg-type]
        )


def test_the_three_power_averaged_quantities_are_taken() -> None:
    thirds = np.array([6.0, 10.0, 14.0])
    frequencies = [400.0, 500.0, 630.0]
    assert [
        building.improvement_octave_bands(
            thirds, frequencies=frequencies, quantity="ΔL"
        ).quantity,
        building.improvement_octave_bands(
            thirds, frequencies=frequencies, quantity="ΔR"
        ).quantity,
        building.improvement_octave_bands(
            thirds, frequencies=frequencies, quantity="Rs"
        ).quantity,
    ] == ["ΔL", "ΔR", "Rs"]
