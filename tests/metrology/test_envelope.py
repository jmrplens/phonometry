#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for the Hilbert envelope and instantaneous phase.

Oracles are the closed forms of Bendat & Piersol Chapter 13: the
Table 13.1 pair ``cos → sin`` recovered from the analytic signal, the
exact envelope of a known AM waveform (Eq. 13.27), a unit envelope and
constant instantaneous frequency for a pure tone (Eqs. 13.17-13.19), a
linear instantaneous-frequency ramp for a chirp, and exact consistency of
the plain-subsampling decimation with the ECMA-internal convention.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

import phonometry as ph  # noqa: E402

FS = 8192.0
N = 16384
#: Slice keeping clear of the discrete Hilbert transform's edge effects.
INTERIOR = slice(1024, N - 1024)


def _tone(f0: float, amp: float = 1.0) -> np.ndarray:
    t = np.arange(N) / FS
    return np.asarray(amp * np.cos(2.0 * np.pi * f0 * t), dtype=np.float64)


def _am(fc: float, fm: float, m: float) -> tuple[np.ndarray, np.ndarray]:
    """AM waveform and its exact envelope ``1 + m·cos(2πfm·t)``."""
    t = np.arange(N) / FS
    env = 1.0 + m * np.cos(2.0 * np.pi * fm * t)
    return env * np.cos(2.0 * np.pi * fc * t), env


# ---------------------------------------------------------------------------
# Closed forms (B&P Table 13.1, Eqs. 13.17-13.19, 13.27)
# ---------------------------------------------------------------------------


def test_pure_tone_has_unit_envelope_and_carrier_frequency() -> None:
    res = ph.envelope(_tone(1000.0, amp=2.5), FS)
    np.testing.assert_allclose(res.envelope[INTERIOR], 2.5, atol=1e-9)
    np.testing.assert_allclose(
        res.instantaneous_frequency[INTERIOR], 1000.0, atol=1e-6
    )


def test_hilbert_transform_of_cos_is_sin() -> None:
    """Table 13.1: x̃(t) = A(t)·sin(θ(t)) recovers sin(2πf0t) from cos."""
    f0 = 500.0
    res = ph.envelope(_tone(f0), FS)
    t = np.arange(N) / FS
    reconstructed = res.envelope * np.sin(res.phase)
    np.testing.assert_allclose(
        reconstructed[INTERIOR],
        np.sin(2.0 * np.pi * f0 * t)[INTERIOR],
        atol=1e-9,
    )


def test_am_envelope_is_recovered_exactly() -> None:
    """Eq. 13.27: the envelope of u(t)·cos(2πf0t) is u(t) exactly."""
    x, exact = _am(1000.0, 10.0, 0.5)
    res = ph.envelope(x, FS)
    np.testing.assert_allclose(res.envelope[INTERIOR], exact[INTERIOR],
                               atol=1e-9)


def test_instantaneous_phase_of_tone_advances_linearly() -> None:
    f0 = 250.0
    res = ph.envelope(_tone(f0), FS)
    slope = float(np.polyfit(res.times[INTERIOR],
                             res.phase[INTERIOR], 1)[0])
    assert slope / (2.0 * np.pi) == pytest.approx(f0, rel=1e-6)


def test_chirp_instantaneous_frequency_tracks_the_sweep() -> None:
    from scipy.signal import chirp

    t = np.arange(N) / FS
    f0, f1 = 200.0, 2000.0
    x = chirp(t, f0=f0, t1=t[-1], f1=f1, method="linear")
    res = ph.envelope(x, FS)
    expected = f0 + (f1 - f0) * t / t[-1]
    np.testing.assert_allclose(
        res.instantaneous_frequency[INTERIOR], expected[INTERIOR], rtol=0.01
    )


# ---------------------------------------------------------------------------
# Decimation
# ---------------------------------------------------------------------------


def test_plain_subsampling_matches_the_ecma_internal_convention() -> None:
    """antialias=False is exactly |hilbert(x)|[::q] (ECMA Formulae 65/119)."""
    from scipy.signal import hilbert

    x, _ = _am(1000.0, 10.0, 0.5)
    res = ph.envelope(x, FS, decimation_factor=32, antialias=False)
    np.testing.assert_array_equal(res.envelope, np.abs(hilbert(x))[::32])
    assert res.fs == pytest.approx(FS / 32.0)
    assert res.decimation_factor == 32
    assert not res.antialias


def test_antialiased_decimation_tracks_the_smooth_envelope() -> None:
    x, exact = _am(1000.0, 10.0, 0.5)
    res = ph.envelope(x, FS, decimation_factor=16)
    exact_dec = exact[::16]
    inner = slice(64, res.envelope.size - 64)
    np.testing.assert_allclose(res.envelope[inner], exact_dec[inner],
                               atol=1e-3)
    assert res.times[1] - res.times[0] == pytest.approx(16.0 / FS)


def test_decimated_outputs_share_one_time_axis() -> None:
    x, _ = _am(2000.0, 20.0, 0.3)
    res = ph.envelope(x, FS, decimation_factor=8)
    assert res.envelope.size == res.phase.size
    assert res.envelope.size == res.instantaneous_frequency.size
    assert res.envelope.size == res.times.size
    # Phase/instantaneous frequency are subsampled from the full rate.
    full = ph.envelope(x, FS)
    np.testing.assert_array_equal(res.phase, full.phase[::8])
    np.testing.assert_array_equal(
        res.instantaneous_frequency, full.instantaneous_frequency[::8]
    )


def test_no_decimation_keeps_the_full_rate() -> None:
    x, _ = _am(1000.0, 10.0, 0.5)
    res = ph.envelope(x, FS)
    assert res.fs == FS
    assert res.envelope.size == x.size
    assert res.decimation_factor == 1
    np.testing.assert_array_equal(res.signal, x)
    assert res.signal_fs == FS


# ---------------------------------------------------------------------------
# Validation and API surface
# ---------------------------------------------------------------------------


def test_envelope_rejects_invalid_inputs() -> None:
    x, _ = _am(1000.0, 10.0, 0.5)
    with pytest.raises(ValueError, match="one-dimensional"):
        ph.envelope(np.stack([x, x]), FS)
    with pytest.raises(ValueError, match="'fs'"):
        ph.envelope(x, 0.0)
    with pytest.raises(ValueError, match="decimation_factor"):
        ph.envelope(x, FS, decimation_factor=0)
    with pytest.raises(ValueError, match="decimation_factor"):
        ph.envelope(x, FS, decimation_factor=x.size)
    with pytest.raises(ValueError, match="finite"):
        ph.envelope(np.full(4096, np.nan), FS)


def test_result_is_frozen() -> None:
    res = ph.envelope(_tone(1000.0), FS)
    with pytest.raises(AttributeError):
        res.envelope = res.envelope * 2.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# .plot() renderer
# ---------------------------------------------------------------------------


def test_envelope_plot_two_panels_and_external_ax() -> None:
    x, _ = _am(1000.0, 10.0, 0.5)
    res = ph.envelope(x, FS)
    axes = res.plot()
    assert len(axes) == 2
    assert len(axes[0].lines) == 2  # signal + envelope
    fig, ext = plt.subplots()
    assert res.plot(ax=ext) is ext
    plt.close("all")


def test_envelope_plot_with_decimated_result() -> None:
    x, _ = _am(1000.0, 10.0, 0.5)
    res = ph.envelope(x, FS, decimation_factor=32)
    axes = res.plot()
    assert len(axes) == 2
    plt.close("all")
