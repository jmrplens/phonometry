#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for ocean ambient-noise spectrum levels (Wenz framework).

Oracles (independent of the implementation): the wind "rule of fives" anchor
(25 dB at 1 kHz for 5 knots, −5 dB/octave, +5 dB per doubling of wind speed) and
the Mellen thermal-noise formula ``<p²> = 4π·k·T·ρ·f²/c`` computed directly.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

from phonometry.ocean_ambient_noise import (
    AmbientNoiseResult,
    ocean_ambient_noise,
    thermal_noise_spectrum,
    wind_noise_spectrum,
)

_BOLTZMANN = 1.380649e-23
_P_REF = 1e-6


def test_wind_rule_of_fives_anchor() -> None:
    # 25 dB spectrum level at 1 kHz for 5 knots.
    assert float(wind_noise_spectrum(1000.0, 5.0)[0]) == pytest.approx(25.0, abs=1e-9)


def test_wind_minus_five_db_per_octave() -> None:
    nl = wind_noise_spectrum([1000.0, 2000.0], 5.0)
    assert float(nl[0] - nl[1]) == pytest.approx(5.0 * np.log10(2.0) * (10.0 / 3.0), abs=1e-9)
    assert float(nl[0] - nl[1]) == pytest.approx(5.017, abs=1e-3)


def test_wind_plus_five_db_per_doubling_of_speed() -> None:
    quiet = float(wind_noise_spectrum(1000.0, 5.0)[0])
    windy = float(wind_noise_spectrum(1000.0, 10.0)[0])
    assert windy - quiet == pytest.approx(5.017, abs=1e-3)


def test_thermal_matches_mellen_formula() -> None:
    f = np.array([1e4, 5e4, 1e5])
    t, rho, c = 16.85, 1025.0, 1500.0
    p2 = 4.0 * np.pi * _BOLTZMANN * (t + 273.15) * rho * f**2 / c
    expected = 10.0 * np.log10(p2 / _P_REF**2)
    got = thermal_noise_spectrum(f, temperature=t, density=rho, sound_speed=c)
    assert np.allclose(got, expected, atol=1e-9)


def test_thermal_rises_twenty_db_per_decade() -> None:
    nl = thermal_noise_spectrum([1e4, 1e5])
    assert float(nl[1] - nl[0]) == pytest.approx(20.0, abs=1e-9)


def test_composite_is_energy_sum_and_dominates_components() -> None:
    f = np.array([500.0, 1000.0, 5e4])
    res = ocean_ambient_noise(f, wind_speed_knots=10.0)
    assert isinstance(res, AmbientNoiseResult)
    expected = 10.0 * np.log10(10.0 ** (res.wind / 10.0) + 10.0 ** (res.thermal / 10.0))
    assert np.allclose(res.spectrum_level, expected, atol=1e-9)
    assert np.all(res.spectrum_level >= np.maximum(res.wind, res.thermal) - 1e-9)
    assert res.shipping is None


def test_shipping_component_added_in_energy() -> None:
    f = np.array([100.0, 1000.0])
    ship = np.array([80.0, 70.0])
    res = ocean_ambient_noise(f, wind_speed_knots=5.0, shipping=ship)
    expected = 10.0 * np.log10(
        10.0 ** (res.wind / 10.0) + 10.0 ** (res.thermal / 10.0) + 10.0 ** (ship / 10.0)
    )
    assert np.allclose(res.spectrum_level, expected, atol=1e-9)
    assert res.shipping is not None


def test_shipping_length_mismatch_rejected() -> None:
    with pytest.raises(ValueError, match="shipping"):
        ocean_ambient_noise([100.0, 1000.0], wind_speed_knots=5.0, shipping=[80.0])


def test_invalid_inputs_rejected() -> None:
    with pytest.raises(ValueError, match="frequency"):
        wind_noise_spectrum(-1.0, 5.0)
    with pytest.raises(ValueError, match="wind_speed"):
        wind_noise_spectrum(1000.0, 0.0)


def test_ambient_plot_smoke() -> None:
    f = np.logspace(2, 5, 50)
    res = ocean_ambient_noise(f, wind_speed_knots=10.0, shipping=np.full(50, 60.0))
    assert res.plot() is not None
