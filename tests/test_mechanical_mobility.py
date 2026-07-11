#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for ISO 7626-1:2011 mechanical mobility and the FRF family.

Anchored on the closed-form single-degree-of-freedom resonator (Annex A): at
its resonance the driving-point mobility is purely real and equal to ``1/c``
(the mobility peak measures the damping), the static receptance is ``1/k``, and
the Table-1 FRFs are exact reciprocals / (jω)-powers of one another.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import (
    MobilityResult,
    convert_frf,
    resonance_frequency,
    sdof_accelerance,
    sdof_mobility,
    sdof_mobility_result,
    sdof_receptance,
)

M, K, C = 2.0, 8000.0, 5.0          # mass [kg], stiffness [N/m], damping [N.s/m]
F0 = math.sqrt(K / M) / (2.0 * math.pi)   # ~10.066 Hz


# ---------------------------------------------------------------------------
# SDOF closed-form oracles (Annex A)
# ---------------------------------------------------------------------------
def test_resonance_frequency() -> None:
    assert resonance_frequency(M, K) == pytest.approx(F0, rel=1e-12)
    assert resonance_frequency(2.0, 8000.0) == pytest.approx(10.06578, abs=1e-4)


def test_mobility_peak_equals_inverse_damping() -> None:
    """At omega0 the driving-point mobility is real and |Y| = 1/c."""
    y0 = complex(sdof_mobility(F0, M, K, C))
    assert y0.real == pytest.approx(1.0 / C, rel=1e-9)
    assert y0.imag == pytest.approx(0.0, abs=1e-9)   # purely real at resonance


def test_static_receptance_is_inverse_stiffness() -> None:
    """As f -> 0 the receptance tends to the static compliance 1/k."""
    h = complex(sdof_receptance(1e-6, M, K, C))
    assert h.real == pytest.approx(1.0 / K, rel=1e-6)
    assert h.imag == pytest.approx(0.0, abs=1e-9)


def test_receptance_hand_value_off_resonance() -> None:
    """H(f) = 1/(k - w^2 m + j w c) at f = 20 Hz, hand-computed."""
    f = 20.0
    w = 2.0 * math.pi * f
    expected = 1.0 / (K - w**2 * M + 1j * w * C)
    assert complex(sdof_receptance(f, M, K, C)) == pytest.approx(expected, rel=1e-12)


# ---------------------------------------------------------------------------
# Table-1 conversion identities
# ---------------------------------------------------------------------------
def test_mobility_and_accelerance_are_jomega_powers_of_receptance() -> None:
    f = 37.0
    w = 2.0 * math.pi * f
    h = sdof_receptance(f, M, K, C)
    assert convert_frf(h, f, "receptance", "mobility") == pytest.approx(1j * w * h)
    assert convert_frf(h, f, "receptance", "accelerance") == pytest.approx(-(w**2) * h)


def test_reciprocals_multiply_to_one() -> None:
    f = 37.0
    h = sdof_receptance(f, M, K, C)
    y = convert_frf(h, f, "receptance", "mobility")
    a = convert_frf(h, f, "receptance", "accelerance")
    assert convert_frf(y, f, "mobility", "impedance") * y == pytest.approx(1.0)
    assert convert_frf(a, f, "accelerance", "apparent_mass") * a == pytest.approx(1.0)
    assert convert_frf(h, f, "receptance", "dynamic_stiffness") * h == pytest.approx(1.0)


def test_conversion_round_trip() -> None:
    f = np.array([10.0, 20.0, 50.0, 100.0])
    y = sdof_mobility(f, M, K, C)
    back = convert_frf(
        convert_frf(
            convert_frf(y, f, "mobility", "receptance"),
            f, "receptance", "accelerance",
        ),
        f, "accelerance", "mobility",
    )
    assert np.allclose(back, y)


def test_accelerance_matches_impedance_route() -> None:
    """Apparent mass at high frequency approaches the rigid mass m."""
    a = sdof_accelerance(5000.0, M, K, C)   # well above resonance
    apparent_mass = convert_frf(a, 5000.0, "accelerance", "apparent_mass")
    assert complex(apparent_mass).real == pytest.approx(M, rel=1e-2)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def test_unknown_frf_raises() -> None:
    with pytest.raises(ValueError, match="unknown source FRF"):
        convert_frf(1.0, 100.0, "velocity", "mobility")
    with pytest.raises(ValueError, match="unknown target FRF"):
        convert_frf(1.0, 100.0, "mobility", "velocity")


def test_non_positive_frequency_raises() -> None:
    with pytest.raises(ValueError, match="frequency"):
        convert_frf(1.0, 0.0, "receptance", "mobility")
    with pytest.raises(ValueError, match="mass"):
        sdof_receptance(100.0, 0.0, K, C)
    with pytest.raises(ValueError, match="damping"):
        sdof_receptance(100.0, M, K, -1.0)


# ---------------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------------
def test_mobility_result_bundle() -> None:
    f = np.linspace(1.0, 50.0, 400)
    res = sdof_mobility_result(f, M, K, C)
    assert isinstance(res, MobilityResult)
    assert res.driving_point
    # the magnitude peak sits at the resonance
    peak_f = res.frequencies[int(np.argmax(res.magnitude))]
    assert peak_f == pytest.approx(F0, abs=0.2)
    # .to() converts to impedance = 1/Y
    z = res.to("impedance")
    assert np.allclose(z, 1.0 / res.mobility)


def test_plot_returns_axes() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    res = sdof_mobility_result(np.linspace(1.0, 50.0, 200), M, K, C)
    assert res.plot() is not None
