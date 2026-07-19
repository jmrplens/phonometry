#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for machine-enclosure insertion loss (Bies §7.4.2).

Oracles: the closed form ``IL = R - C`` with
``C = 10 log10(0.3 + S_E / R_i)`` and ``R_i`` the interior room constant
(Eqs. (7.103), (7.111)); the fully absorbing limit ``C -> 10 log10 0.3``
(``IL = R + 5.23``); consistency of ``R_i`` with
:func:`phonometry.room.room_constant`; and the panel ``R`` being supplied by
the caller (array or callable), never predicted here.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import enclosure_insertion_loss, room_constant
from phonometry.noise_control.enclosures import EnclosureResult


def test_closed_form() -> None:
    r = np.array([20.0, 30.0, 40.0])
    s_e, s_i, alpha = 6.0, 5.0, 0.3
    res = enclosure_insertion_loss(r, s_e, s_i, alpha)
    r_i = float(room_constant(s_i, alpha))
    c = 10.0 * math.log10(0.3 + s_e / r_i)
    assert np.allclose(res.correction, c)
    assert np.allclose(res.insertion_loss, r - c)


def test_room_constant_consistency() -> None:
    res = enclosure_insertion_loss([30.0], 6.0, 5.0, np.array([0.3]))
    assert res.room_constant[0] == pytest.approx(float(room_constant(5.0, 0.3)))


def test_fully_absorbing_interior_floor() -> None:
    # alpha -> 1: R_i -> inf, C -> 10 log10(0.3) = -5.23 dB, IL = R + 5.23.
    res = enclosure_insertion_loss([40.0], 6.0, 5.0, 0.999999)
    assert res.correction[0] == pytest.approx(10.0 * math.log10(0.3), abs=1e-3)
    assert res.insertion_loss[0] == pytest.approx(40.0 - 10.0 * math.log10(0.3), abs=1e-3)


def test_harder_interior_wastes_more_panel() -> None:
    live = enclosure_insertion_loss([40.0], 6.0, 5.0, 0.05)
    dead = enclosure_insertion_loss([40.0], 6.0, 5.0, 0.5)
    assert dead.insertion_loss[0] > live.insertion_loss[0]


def test_per_band_absorption() -> None:
    r = np.array([20.0, 25.0, 30.0, 35.0])
    alpha = np.array([0.1, 0.2, 0.3, 0.4])
    res = enclosure_insertion_loss(r, 6.0, 5.0, alpha)
    assert res.insertion_loss.shape == (4,)
    r_i = np.asarray(room_constant(5.0, alpha))
    assert np.allclose(res.correction, 10.0 * np.log10(0.3 + 6.0 / r_i))


def test_callable_panel_r() -> None:
    freqs = np.array([125.0, 250.0, 500.0, 1000.0])

    def mass_law(f: np.ndarray) -> np.ndarray:
        return 20.0 * np.log10(f) - 10.0  # arbitrary user-supplied R(f)

    res = enclosure_insertion_loss(mass_law, 6.0, 5.0, 0.3, frequencies=freqs)
    assert np.allclose(res.panel_transmission_loss, mass_law(freqs))
    assert res.frequencies is not None


def test_callable_requires_frequencies() -> None:
    with pytest.raises(ValueError, match="frequencies"):
        enclosure_insertion_loss(lambda f: f, 6.0, 5.0, 0.3)


def test_panel_result_bridge() -> None:
    # A predicted SoundReductionResult can be fed straight in; its per-band R
    # and its frequencies are read from the result, matching an explicit pass.
    from phonometry import single_panel_transmission_loss

    freqs = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0])
    panel = single_panel_transmission_loss(freqs, 15.0, critical_frequency=2000.0)

    via_result = enclosure_insertion_loss(panel, 6.0, 5.0, 0.3)
    via_arrays = enclosure_insertion_loss(
        panel.transmission_loss, 6.0, 5.0, 0.3, frequencies=freqs
    )
    assert np.allclose(via_result.panel_transmission_loss, panel.transmission_loss)
    assert np.allclose(via_result.frequencies, freqs)
    assert np.allclose(via_result.insertion_loss, via_arrays.insertion_loss)


def test_panel_result_frequencies_override() -> None:
    # An explicit 'frequencies' wins over the ones carried by the result.
    from phonometry import single_panel_transmission_loss

    freqs = np.array([125.0, 250.0, 500.0])
    panel = single_panel_transmission_loss(freqs, 15.0, critical_frequency=2000.0)
    other = np.array([100.0, 200.0, 400.0])
    res = enclosure_insertion_loss(panel, 6.0, 5.0, 0.3, frequencies=other)
    assert np.allclose(res.frequencies, other)


def test_result_type_and_plot() -> None:
    res = enclosure_insertion_loss(
        [20.0, 30.0, 40.0], 6.0, 5.0, 0.3,
        frequencies=[125.0, 250.0, 500.0],
    )
    assert isinstance(res, EnclosureResult)
    import matplotlib

    matplotlib.use("Agg")
    assert res.plot().get_ylabel()
    # No-frequency plot uses band indices.
    assert enclosure_insertion_loss([20.0, 30.0], 6.0, 5.0, 0.3).plot() is not None


def test_validation() -> None:
    with pytest.raises(ValueError):
        enclosure_insertion_loss([20.0], -1.0, 5.0, 0.3)
    with pytest.raises(ValueError):
        enclosure_insertion_loss([20.0], 6.0, 5.0, 1.0)
