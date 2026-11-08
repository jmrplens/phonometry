#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A number a public entry computes with is read by its name before the arithmetic.

Following arithmetic on a caller's value, the real-conversions guard found
public entries that computed with a number no check had read and converted
only the result: a text failed inside the arithmetic with an error that named
nothing, and a NumPy complex number came out as its real part with no more
than a ``ComplexWarning``, or went into the phase of a reflection factor as a
complex delay. Each is read through the shared reader of one number now, and
refused by the name of its parameter.
"""

from __future__ import annotations

import dataclasses
import warnings
from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry import aircraft, noise_control
from phonometry.materials.surfaces.road_absorption import in_situ_reflection_factor

if TYPE_CHECKING:
    from collections.abc import Callable


def _valve_noise() -> noise_control.AerodynamicValveNoise:
    return noise_control.valve_aerodynamic_noise(
        noise_control.GasStream(
            mass_flow=2.22,
            inlet_pressure_pa=1.0e6,
            outlet_pressure_pa=7.2e5,
            inlet_density=5.3,
            inlet_temperature_c=176.85,
            specific_heat_ratio=1.22,
            molar_mass_kg_kmol=19.8,
        ),
        noise_control.ValveTrim(
            flow_coefficient=90.0,
            style_modifier=noise_control.valve_style_modifier(0.00137, 0.181, 6),
            pressure_recovery=0.792 / 0.984,
            outlet_diameter_m=0.1,
            efficiency_correction=-3.8,
            strouhal_number=0.2,
        ),
        noise_control.DownstreamPipe(
            internal_diameter_m=0.2031, wall_thickness_m=0.008, density=8000.0
        ),
    )


def _reflection(delay: object) -> np.ndarray:
    incident = np.zeros(256)
    incident[0] = 1.0
    return in_situ_reflection_factor(
        incident,
        0.5 * np.roll(incident, 8),
        fs=48000.0,
        delay=delay,  # type: ignore[arg-type]
    )


def _fft_length(n: object) -> np.ndarray:
    incident = np.zeros(256)
    incident[0] = 1.0
    return in_situ_reflection_factor(
        incident,
        0.5 * np.roll(incident, 8),
        n=n,  # type: ignore[arg-type]
    )


def _plane() -> aircraft.MeanGroundPlaneResult:
    return aircraft.mean_ground_plane([0.0, 100.0], [0.0, 100.0])


#: Each entry, handed the value in place of one number, and the name it is
#: refused by.
_ENTRIES: dict[str, tuple[Callable[[object], object], str]] = {
    "Aerodrome.pressure_ratio": (
        lambda value: aircraft.Aerodrome(elevation_ft=0.0).pressure_ratio(value),  # type: ignore[arg-type]
        "altitude_ft",
    ),
    "MeanGroundPlaneResult.equivalent_height, distance": (
        lambda value: _plane().equivalent_height(value, 60.0),  # type: ignore[arg-type]
        "distance_m",
    ),
    "MeanGroundPlaneResult.equivalent_height, height": (
        lambda value: _plane().equivalent_height(50.0, value),  # type: ignore[arg-type]
        "height_m",
    ),
    "in_situ_reflection_factor": (_reflection, "delay"),
    "in_situ_reflection_factor, FFT length": (_fft_length, "'n' must"),
    "AerodynamicValveNoise": (
        lambda value: dataclasses.replace(
            _valve_noise(),
            efficiency_correction=value,  # type: ignore[arg-type]
        ),
        "efficiency_correction",
    ),
}


@pytest.mark.parametrize("entry", sorted(_ENTRIES))
@pytest.mark.parametrize(
    "value",
    [pytest.param("12", id="text"), pytest.param(np.complex128(12 + 1j), id="complex")],
)
def test_a_number_computed_with_is_refused_by_its_name(
    entry: str, value: object
) -> None:
    call, name = _ENTRIES[entry]
    with warnings.catch_warnings():
        warnings.simplefilter("error", np.exceptions.ComplexWarning)
        with pytest.raises(TypeError, match=name):
            call(value)


def test_a_real_number_is_read_as_before() -> None:
    assert _plane().equivalent_height(50.0, 60.0) == pytest.approx(10.0 / np.sqrt(2.0))
    assert aircraft.Aerodrome(elevation_ft=0.0).pressure_ratio(0.0) == pytest.approx(
        1.0
    )
    assert np.all(np.isfinite(np.abs(_reflection(1.0e-4))))


def test_a_numpy_integer_is_an_fft_length_as_an_int_is() -> None:
    """The FFT length is read as a count, which takes a NumPy integer."""
    np.testing.assert_array_equal(_fft_length(np.int64(512)), _fft_length(512))
    assert _fft_length(np.int64(512)).shape == (257,)
