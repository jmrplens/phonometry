#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for integrated and statistical sound levels (Leq, LAeq, LN).
"""

import numpy as np
import pytest

from pyoctaveband import laeq, leq

FS = 48000


def _tone(f0: float, seconds: float = 1.0, amp: float = 1.0) -> np.ndarray:
    t = np.arange(int(FS * seconds)) / FS
    return amp * np.sin(2 * np.pi * f0 * t)


def test_leq_sine_matches_rms() -> None:
    """Leq of a 1 Pa amplitude sine = 20*log10((1/sqrt2)/20u) = 90.97 dB."""
    x = _tone(1000)
    assert leq(x) == pytest.approx(90.97, abs=0.05)


def test_leq_dbfs() -> None:
    """RMS of a full-scale sine is -3.01 dBFS."""
    x = _tone(1000)
    assert leq(x, dbfs=True) == pytest.approx(-3.01, abs=0.05)


def test_leq_multichannel_returns_per_channel() -> None:
    x = np.stack([_tone(1000), 0.5 * _tone(1000)])
    out = leq(x)
    assert out.shape == (2,)
    assert out[0] - out[1] == pytest.approx(6.02, abs=0.05)


def test_leq_calibration_factor() -> None:
    x = _tone(1000)
    assert leq(x, calibration_factor=10.0) == pytest.approx(90.97 + 20.0, abs=0.05)


def test_laeq_1khz_equals_leq() -> None:
    """A-weighting is 0 dB at 1 kHz, so LAeq == Leq there."""
    x = _tone(1000, seconds=2.0)
    assert laeq(x, FS) == pytest.approx(leq(x), abs=0.3)


def test_laeq_100hz_attenuated() -> None:
    """A-weighting at 100 Hz is about -19.1 dB."""
    x = _tone(100, seconds=2.0)
    assert laeq(x, FS) - leq(x) == pytest.approx(-19.1, abs=0.5)


def test_ln_levels_constant_signal_all_equal() -> None:
    """For a steady tone, L10 == L90 and L50 == Leq (within envelope ripple)."""
    from pyoctaveband import ln_levels

    x = _tone(1000, seconds=3.0)
    out = ln_levels(x, FS, n=(10, 50, 90))
    assert set(out.keys()) == {10, 50, 90}
    assert out[10] == pytest.approx(out[90], abs=0.2)
    assert out[50] == pytest.approx(90.97, abs=0.3)


def test_ln_levels_ordering() -> None:
    """L10 (exceeded 10% of time) >= L50 >= L90 for a fluctuating signal."""
    from pyoctaveband import ln_levels

    rng = np.random.default_rng(0)
    x = rng.standard_normal(FS * 3) * np.linspace(0.1, 1.0, FS * 3)
    out = ln_levels(x, FS)
    assert out[10] >= out[50] >= out[90]


def test_ln_levels_weighting_a() -> None:
    from pyoctaveband import ln_levels

    x = _tone(100, seconds=3.0)
    unweighted = ln_levels(x, FS, n=(50,))[50]
    weighted = ln_levels(x, FS, n=(50,), weighting="A")[50]
    assert weighted - unweighted == pytest.approx(-19.1, abs=0.5)


def test_ln_levels_invalid_percentile_raises() -> None:
    from pyoctaveband import ln_levels

    with pytest.raises(ValueError, match="between 0 and 100"):
        ln_levels(_tone(1000), FS, n=(0,))


def test_ln_levels_multichannel() -> None:
    from pyoctaveband import ln_levels

    x = np.stack([_tone(1000, 2.0), 0.5 * _tone(1000, 2.0)])
    out = ln_levels(x, FS, n=(50,))
    assert out[50].shape == (2,)
    assert out[50][0] - out[50][1] == pytest.approx(6.02, abs=0.2)
