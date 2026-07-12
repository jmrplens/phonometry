#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for aircraft-noise EPNL (ICAO Annex 16 Vol. I, Appendix 2).

The oracles are independent of the implementation: the analytic noy breakpoints
of Table A2-3, and the worked examples of the ICAO Doc 9501 Environmental
Technical Manual Vol. I (2018) -- the turbofan tone-correction Table 3-7 and the
integrated-method EPNL Table 4-4.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

from phonometry.aircraft_noise import (
    NOY_BANDS,
    perceived_noise_level,
    perceived_noisiness,
)

_B = list(NOY_BANDS)


def test_noy_breakpoints() -> None:
    # Table A2-3, band 14 (1000 Hz): SPL(b)=40 -> n=1, SPL(e)=25 -> n=0.3,
    # SPL(d)=16 -> n=0.1.
    b14 = _B.index(1000.0)
    spl = np.full(24, -999.0)
    spl[b14] = 40.0
    assert perceived_noisiness(spl)[b14] == pytest.approx(1.0, rel=1e-6)
    spl[b14] = 25.0
    assert perceived_noisiness(spl)[b14] == pytest.approx(0.3, rel=1e-6)
    spl[b14] = 16.0
    assert perceived_noisiness(spl)[b14] == pytest.approx(0.1, rel=1e-6)


def test_noy_floor_below_spld_is_zero() -> None:
    b14 = _B.index(1000.0)
    spl = np.full(24, -999.0)
    spl[b14] = 10.0  # < SPL(d) = 16
    assert perceived_noisiness(spl)[b14] == 0.0


def test_noy_requires_24_bands() -> None:
    with pytest.raises(ValueError):
        perceived_noisiness([1.0, 2.0, 3.0])


def test_pnl_closed_form() -> None:
    # One band at 1000 Hz, SPL = SPL(b) = 40 -> n = 1, others 0.
    # N = 0.85*1 + 0.15*1 = 1.0 -> PNL = 40 + (10/lg2)*lg(1) = 40.
    b14 = _B.index(1000.0)
    spl = np.full(24, -999.0)
    spl[b14] = 40.0
    assert perceived_noise_level(spl) == pytest.approx(40.0, abs=1e-6)


def test_pnl_two_equal_bands() -> None:
    # Two bands each n = 1 -> n_max = 1, Σn = 2 -> N = 0.85 + 0.15*2 = 1.15.
    b14 = _B.index(1000.0)
    b11 = _B.index(500.0)  # SPL(b) @ 500 Hz = 40
    spl = np.full(24, -999.0)
    spl[b14] = 40.0
    spl[b11] = 40.0
    expected = 40.0 + (10.0 / np.log10(2.0)) * np.log10(1.15)
    assert perceived_noise_level(spl) == pytest.approx(expected, rel=1e-9)
