#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for underwater transmission loss (spreading + volume absorption).

Oracles: the closed-form spreading laws (hand recomputation), the Thorp,
Francois-Garrison and Ainslie-McColm absorption formulae (independent inline
recomputation), and the mutual agreement of Francois-Garrison and Ainslie-McColm
(the latter's paper states within 10 % of the former).
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

from phonometry.underwater.propagation import (
    TransmissionLossResult,
    seawater_absorption,
    spreading_loss,
    transmission_loss,
)


def test_spherical_spreading_6db_per_doubling() -> None:
    loss = spreading_loss([1.0, 10.0, 100.0, 200.0], law="spherical")
    np.testing.assert_allclose(loss, [0.0, 20.0, 40.0, 40.0 + 20.0 * np.log10(2.0)])


def test_cylindrical_spreading_3db_per_doubling() -> None:
    loss = spreading_loss([100.0, 200.0], law="cylindrical")
    assert loss[1] - loss[0] == pytest.approx(10.0 * np.log10(2.0))


def test_practical_spreading_matches_pieces() -> None:
    r0 = 1000.0
    loss = spreading_loss([500.0, 1000.0, 4000.0], law="practical", transition_range=r0)
    assert loss[0] == pytest.approx(20.0 * np.log10(500.0))  # spherical below R0
    assert loss[1] == pytest.approx(20.0 * np.log10(1000.0))
    assert loss[2] == pytest.approx(20.0 * np.log10(r0) + 10.0 * np.log10(4.0))


def test_practical_requires_transition_range() -> None:
    with pytest.raises(ValueError, match="transition_range"):
        spreading_loss([100.0], law="practical")


def test_thorp_absorption_recompute() -> None:
    f_khz = 10.0
    expected = 1.0936 * (0.1 * f_khz**2 / (1 + f_khz**2) + 40 * f_khz**2 / (4100 + f_khz**2))
    got = seawater_absorption(10_000.0, model="thorp")
    assert got[0] == pytest.approx(expected, rel=1e-9)
    assert got[0] == pytest.approx(1.1498, abs=1e-3)


def test_francois_garrison_recompute() -> None:
    # Independent inline recomputation at 10 kHz, 10 C, 35 ppt, 0 m, pH 8.
    f = 10.0
    t, s, z, ph = 10.0, 35.0, 0.0, 8.0
    c = 1412 + 3.21 * t + 1.19 * s + 0.0167 * z
    a1 = (8.68 / c) * 10 ** (0.78 * ph - 5)
    f1 = 2.8 * (s / 35) ** 0.5 * 10 ** (4 - 1245 / (273 + t))
    a2 = 21.44 * (s / c) * (1 + 0.025 * t)
    f2 = 8.17 * 10 ** (8 - 1990 / (273 + t)) / (1 + 0.0018 * (s - 35))
    a3 = 4.937e-4 - 2.59e-5 * t + 9.11e-7 * t**2 - 1.50e-8 * t**3
    expected = a1 * f1 * f**2 / (f**2 + f1**2) + a2 * f2 * f**2 / (f**2 + f2**2) + a3 * f**2
    got = seawater_absorption(10_000.0, temperature=t, salinity=s, depth=z, ph=ph,
                              model="francois-garrison")
    assert got[0] == pytest.approx(expected, rel=1e-9)


def test_francois_garrison_and_ainslie_mccolm_agree() -> None:
    # Ainslie-McColm 1998: within 10 % of Francois-Garrison, 100 Hz - 1 MHz.
    freqs = np.array([1e3, 1e4, 1e5, 5e5])
    fg = seawater_absorption(freqs, temperature=10.0, salinity=35.0, depth=0.0, ph=8.0,
                             model="francois-garrison")
    am = seawater_absorption(freqs, temperature=10.0, salinity=35.0, depth=0.0, ph=8.0,
                             model="ainslie-mccolm")
    assert np.all(np.abs(am - fg) <= 0.10 * fg)


def test_ainslie_mccolm_depth_in_km() -> None:
    # Depth enters A-M in km; 1000 m must reduce the MgSO4 term vs the surface.
    shallow = seawater_absorption(50_000.0, depth=0.0, model="ainslie-mccolm")
    deep = seawater_absorption(50_000.0, depth=1000.0, model="ainslie-mccolm")
    assert deep[0] < shallow[0]


def test_unknown_absorption_model_rejected() -> None:
    with pytest.raises(ValueError, match="model"):
        seawater_absorption(1000.0, model="fisher-simmons")


def test_transmission_loss_is_spreading_plus_absorption() -> None:
    res = transmission_loss(
        [100.0, 1000.0, 10000.0], 10_000.0, law="spherical",
        temperature=10.0, salinity=35.0, depth=0.0, model="francois-garrison",
    )
    assert isinstance(res, TransmissionLossResult)
    alpha = seawater_absorption(10_000.0, temperature=10.0, salinity=35.0, depth=0.0,
                                model="francois-garrison")[0]
    expected = 20.0 * np.log10(res.range_m) + alpha * (res.range_m / 1000.0)
    np.testing.assert_allclose(res.tl, expected, rtol=1e-9)
    np.testing.assert_allclose(res.spreading + res.absorption, res.tl)
    assert res.absorption_coefficient == pytest.approx(alpha)


def test_transmission_loss_rejects_nonpositive_range() -> None:
    with pytest.raises(ValueError, match="range_m"):
        transmission_loss([0.0, 100.0], 1000.0)


def test_transmission_loss_plot_smoke() -> None:
    res = transmission_loss(np.linspace(10.0, 10000.0, 50), 12_000.0)
    assert res.plot() is not None
