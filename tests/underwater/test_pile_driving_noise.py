#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for pile-driving underwater sound metrics (ISO 18406).

The single-strike SEL matches the underwater SEL primitive; the cumulative SEL
is the exact energy sum, equal to SEL_ss + 10·lg(N) for identical strikes.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

from phonometry import (
    PileStrikeResult,
    cumulative_sel,
    cumulative_sel_identical,
    peak_sound_pressure_level,
    pile_strike_metrics,
    single_strike_sel,
    sound_exposure_level,
)

FS = 48000


def _pulse(amplitude: float, seconds: float) -> np.ndarray:
    # A decaying sinusoidal burst, the shape of an impulsive strike.
    t = np.arange(round(seconds * FS)) / FS
    return amplitude * np.exp(-t / (0.3 * seconds)) * np.sin(2 * np.pi * 200.0 * t)


def test_single_strike_sel_matches_primitive() -> None:
    x = _pulse(50.0, 0.2)
    assert single_strike_sel(x, FS) == pytest.approx(sound_exposure_level(x, FS))


def test_cumulative_sel_identical_strikes() -> None:
    # N identical strikes -> SEL_cum = SEL_ss + 10 lg(N).
    sel_ss = 180.0
    assert cumulative_sel_identical(sel_ss, 10) == pytest.approx(sel_ss + 10.0)
    assert cumulative_sel_identical(sel_ss, 100) == pytest.approx(sel_ss + 20.0)
    assert cumulative_sel_identical(sel_ss, 1) == pytest.approx(sel_ss)


def test_cumulative_sel_energy_sum_matches_identical() -> None:
    sel_ss = 175.0
    n = 8
    assert cumulative_sel([sel_ss] * n) == pytest.approx(
        cumulative_sel_identical(sel_ss, n)
    )


def test_cumulative_sel_differing_strikes() -> None:
    sels = [170.0, 176.0, 173.0]
    expected = 10.0 * np.log10(sum(10.0 ** (s / 10.0) for s in sels))
    assert cumulative_sel(sels) == pytest.approx(expected)


def test_cumulative_sel_rejects_empty() -> None:
    with pytest.raises(ValueError):
        cumulative_sel([])


def test_cumulative_sel_identical_rejects_zero_strikes() -> None:
    with pytest.raises(ValueError):
        cumulative_sel_identical(180.0, 0)


def test_cumulative_sel_identical_rejects_fractional_strikes() -> None:
    # A non-integer count must be rejected, not silently truncated to int().
    with pytest.raises(ValueError):
        cumulative_sel_identical(180.0, 1.9)  # type: ignore[arg-type]


def test_pile_strike_metrics_bundle_and_plot() -> None:
    x = _pulse(100.0, 0.25)
    res = pile_strike_metrics(x, FS)
    assert isinstance(res, PileStrikeResult)
    assert res.single_strike_sel == pytest.approx(sound_exposure_level(x, FS))
    assert res.peak_spl == pytest.approx(peak_sound_pressure_level(x))
    assert 0.0 < res.pulse_duration < 0.25
    axes = res.plot()
    assert len(axes) == 2


def test_pile_strike_metrics_rejects_short_signal() -> None:
    with pytest.raises(ValueError):
        pile_strike_metrics(np.array([1.0]), FS)
