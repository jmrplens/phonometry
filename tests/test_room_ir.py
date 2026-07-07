#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for ISO 18233:2006 impulse-response acquisition (room_ir).

Validation strategy (closed-form, not self-consistency):
- Ideal chain (recorded == excitation) -> band-limited delta at t=0.
- Known IIR system -> recovered in-band magnitude equals the analytic
  filter response (scipy.signal.freqz) within 0.1 dB (ISO 18233 5.4/B.5).
- Added noise -> IR peak-to-floor ratio grows ~3 dB per doubling of the
  sweep duration (ISO 18233 B.6).
- MLS: circular autocorrelation is L at lag 0 and -1 elsewhere with a flat
  magnitude spectrum (ISO 18233 A.1); a known IIR system is recovered in
  band within 0.1 dB via circular cross-correlation.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import signal

from phonometry import (
    impulse_response,
    inverse_filter,
    mls_impulse_response,
    mls_signal,
    sweep_signal,
)
from phonometry.room_ir import _MLS_TAPS

FS = 48000


def _band_response_db(b: np.ndarray, a: np.ndarray, ir: np.ndarray, fs: int,
                      f_lo: float, f_hi: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (estimated, true) magnitudes in dB on the rfft grid, in band."""
    n = ir.size
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    h_est = np.fft.rfft(ir)
    _, h_true = signal.freqz(b, a, worN=freqs, fs=fs)
    mask = (freqs >= f_lo) & (freqs <= f_hi)
    est_db = 20.0 * np.log10(np.abs(h_est[mask]))
    true_db = 20.0 * np.log10(np.abs(h_true[mask]))
    return est_db, true_db


# --------------------------------------------------------------------------
# Sweep generation
# --------------------------------------------------------------------------
def test_sweep_length_and_bounds() -> None:
    x = sweep_signal(FS, 20.0, 20000.0, 1.0)
    assert x.size == FS
    assert np.max(np.abs(x)) <= 1.0 + 1e-12


def test_sweep_instantaneous_frequency_is_exponential() -> None:
    # Zero crossings of an exponential sweep should follow f(t)=f1*(f2/f1)^(t/T).
    fs, f1, f2, secs = 48000, 100.0, 10000.0, 2.0
    x = sweep_signal(fs, f1, f2, secs, fade=0.0)
    # Analytic phase; verify start/end instantaneous frequency via finite diff.
    # Use the analytic model directly: compare against the closed-form phase.
    t = np.arange(x.size) / fs
    ts = x.size / fs
    k = 2.0 * np.pi * f1 * ts / np.log(f2 / f1)
    phase = k * ((f2 / f1) ** (t / ts) - 1.0)
    assert np.allclose(x, np.sin(phase), atol=1e-9)


# --------------------------------------------------------------------------
# Ideal chain -> delta
# --------------------------------------------------------------------------
def test_sweep_ideal_chain_is_delta() -> None:
    # Near-full-band sweep -> the recovered IR is a clean band-limited delta.
    x = sweep_signal(FS, 5.0, 23800.0, 2.0, fade=0.005)
    ir = impulse_response(x, x, FS, regularization=1e-8)
    assert int(np.argmax(np.abs(ir))) == 0
    peak = np.abs(ir[0])
    sidelobe = np.abs(ir[20:]).max()
    assert 20.0 * np.log10(sidelobe / peak) < -40.0


def test_farina_inverse_filter_compresses_sweep() -> None:
    f1, f2, secs = 50.0, 20000.0, 1.0
    x = sweep_signal(FS, f1, f2, secs, fade=0.02)
    inv = inverse_filter(FS, f1, f2, secs, fade=0.02)
    y = signal.fftconvolve(x, inv)
    peak = np.abs(y).max()
    ipk = int(np.argmax(np.abs(y)))
    # Everything more than 1 ms away from the compression peak is a sidelobe.
    guard = FS // 1000
    mask = np.ones(y.size, dtype=bool)
    mask[max(0, ipk - guard):ipk + guard] = False
    assert 20.0 * np.log10(np.abs(y[mask]).max() / peak) < -30.0


# --------------------------------------------------------------------------
# Known IIR system -> recovered response
# --------------------------------------------------------------------------
def test_sweep_recovers_iir_response_in_band() -> None:
    b, a = signal.butter(4, [200.0, 2000.0], btype="band", fs=FS)
    x = sweep_signal(FS, 20.0, 20000.0, 2.0)
    y = signal.lfilter(b, a, x)
    ir = impulse_response(y, x, FS, length=16384)
    est_db, true_db = _band_response_db(b, a, ir, FS, 300.0, 1500.0)
    assert np.max(np.abs(est_db - true_db)) < 0.1


def test_farina_method_recovers_iir_response_in_band() -> None:
    b, a = signal.butter(4, [200.0, 2000.0], btype="band", fs=FS)
    f1, f2, secs = 20.0, 20000.0, 2.0
    x = sweep_signal(FS, f1, f2, secs)
    y = signal.lfilter(b, a, x)
    ir = impulse_response(y, x, FS, method="farina", f_range=(f1, f2), length=16384)
    est_db, true_db = _band_response_db(b, a, ir, FS, 300.0, 1500.0)
    # Farina inverse-filter whitening is approximate; use a looser band bound.
    assert np.max(np.abs(est_db - true_db)) < 0.5


# --------------------------------------------------------------------------
# Harmonic separation (Farina): distortion products at negative times
# --------------------------------------------------------------------------
def test_harmonic_products_appear_at_negative_time() -> None:
    f1, f2, secs = 50.0, 12000.0, 3.0
    x = sweep_signal(FS, f1, f2, secs)
    # Memoryless quadratic non-linearity -> strong 2nd-harmonic product.
    y = x + 0.3 * x**2
    full = impulse_response(y, x, FS, return_full=True)
    n = full.size

    # The 2nd harmonic of an ESS arrives ahead of the linear IR by
    # dt = T*ln(2)/ln(f2/f1) (Farina 2000); in the wrapped deconvolution this
    # negative time sits near index n - dt*fs.
    advance = int(round(secs * np.log(2.0) / np.log(f2 / f1) * FS))
    predicted = n - advance
    window = np.abs(full[predicted - 500:predicted + 500])
    harmonic_peak = window.max()
    peak_idx = predicted - 500 + int(np.argmax(window))
    assert abs(peak_idx - predicted) < 50

    floor = np.sqrt(np.mean(full[n // 2:predicted - 5000] ** 2))
    assert harmonic_peak > 15.0 * floor

    # The default (trimmed) IR is causal, so it excludes the harmonic product.
    causal = impulse_response(y, x, FS)
    assert int(np.argmax(np.abs(causal))) == 0
    assert causal.size == x.size


# --------------------------------------------------------------------------
# Noise -> SNR improves with sweep duration (~3 dB/doubling)
# --------------------------------------------------------------------------
def test_sweep_snr_improves_3db_per_doubling() -> None:
    rng = np.random.default_rng(12345)
    f1, f2, noise_amp = 20.0, 20000.0, 2e-3

    def snr_for(seconds: float) -> float:
        x = sweep_signal(FS, f1, f2, seconds)
        noise = rng.standard_normal(x.size) * noise_amp
        ir = impulse_response(x + noise, x, FS, length=x.size)
        peak = np.abs(ir).max()
        lo, hi = ir.size // 4, 3 * ir.size // 4
        floor = np.sqrt(np.mean(ir[lo:hi] ** 2))
        return 20.0 * np.log10(peak / floor)

    snr_1 = snr_for(1.0)
    snr_2 = snr_for(2.0)
    snr_4 = snr_for(4.0)
    assert snr_2 - snr_1 == pytest.approx(3.0, abs=1.0)
    assert snr_4 - snr_2 == pytest.approx(3.0, abs=1.0)


# --------------------------------------------------------------------------
# MLS
# --------------------------------------------------------------------------
def test_mls_length_and_levels() -> None:
    for order in (4, 8, 12, 15):
        a = mls_signal(order)
        assert a.size == 2**order - 1
        assert set(np.unique(a)).issubset({-1.0, 1.0})
        # bipolar sum of a maximum-length sequence is exactly -1
        assert int(round(a.sum())) == -1


def test_mls_taps_cover_supported_orders() -> None:
    for order, taps in _MLS_TAPS.items():
        assert max(taps) == order  # highest tap must be the register length
        assert min(taps) >= 1


def test_all_mls_orders_are_primitive() -> None:
    # Every tap set must yield a true maximum-length sequence: circular
    # autocorrelation == length at lag 0 and -1 elsewhere (ISO 18233 A.1).
    for order in _MLS_TAPS:
        a = mls_signal(order)
        length = a.size
        autocorr = np.fft.irfft(np.abs(np.fft.rfft(a)) ** 2, length)
        assert autocorr[0] == pytest.approx(length, rel=1e-9)
        assert np.max(np.abs(autocorr[1:] + 1.0)) < 1e-6


def test_mls_autocorrelation_is_delta() -> None:
    order = 12
    a = mls_signal(order)
    length = a.size
    spec = np.fft.rfft(a)
    autocorr = np.fft.irfft(np.abs(spec) ** 2, length)
    assert autocorr[0] == pytest.approx(length, abs=1e-6)
    assert np.allclose(autocorr[1:], -1.0, atol=1e-6)
    # Flat magnitude spectrum away from DC.
    mag = np.abs(spec[1:])
    assert mag.std() / mag.mean() < 1e-9


def test_mls_ideal_chain_is_delta() -> None:
    order = 12
    a = mls_signal(order)
    ir = mls_impulse_response(a, a)
    assert int(np.argmax(np.abs(ir))) == 0
    assert ir[0] == pytest.approx(1.0, abs=1e-3)
    assert np.max(np.abs(ir[1:])) < 2e-3


def test_mls_recovers_iir_response_in_band() -> None:
    order = 14
    a = mls_signal(order)
    length = a.size
    b, coef_a = signal.butter(4, [200.0, 2000.0], btype="band", fs=FS)
    # Periodic excitation -> steady-state period == circular convolution.
    x = np.tile(a, 3)
    y = signal.lfilter(b, coef_a, x)
    y_period = y[-length:]
    ir = mls_impulse_response(y_period, a)
    freqs = np.fft.rfftfreq(length, d=1.0 / FS)
    h_est = np.fft.rfft(ir)
    _, h_true = signal.freqz(b, coef_a, worN=freqs, fs=FS)
    mask = (freqs >= 300.0) & (freqs <= 1500.0)
    est_db = 20.0 * np.log10(np.abs(h_est[mask]))
    true_db = 20.0 * np.log10(np.abs(h_true[mask]))
    assert np.max(np.abs(est_db - true_db)) < 0.1


def test_mls_snr_improves_with_averaging() -> None:
    order = 14
    a = mls_signal(order)
    length = a.size
    rng = np.random.default_rng(7)
    noise_amp = 0.5

    def snr_for(n_avg: int) -> float:
        # Average n_avg noisy periods before recovery (ISO 18233 6.3.6).
        acc = np.zeros(length)
        for _ in range(n_avg):
            acc += a + rng.standard_normal(length) * noise_amp
        recorded = acc / n_avg
        ir = mls_impulse_response(recorded, a)
        peak = np.abs(ir).max()
        floor = np.sqrt(np.mean(ir[length // 4:length // 2] ** 2))
        return 20.0 * np.log10(peak / floor)

    snr_1 = snr_for(1)
    snr_4 = snr_for(4)
    # 4x averaging -> +6 dB (3 dB per doubling, ISO 18233 6.3.6).
    assert snr_4 - snr_1 == pytest.approx(6.0, abs=1.5)


def test_mls_multi_period_recording_averages_internally() -> None:
    """A >1-period recording exercises the internal reshape/mean averaging
    branch and recovers a known filter, beating a single noisy period."""
    order = 14
    a = mls_signal(order)
    length = a.size
    b = np.array([0.6, 0.25, 0.1, 0.05])  # known short FIR filter
    reps = 4
    rng = np.random.default_rng(2026)
    # Steady-state periodic response: filter reps+1 tiles and drop the first
    # (transient) period so every remaining period is the circular response.
    x = np.tile(a, reps + 1)
    y = signal.lfilter(b, 1.0, x)[length:]
    noisy = y + rng.standard_normal(y.size) * 0.3
    assert noisy.size == reps * length  # multi-period recording

    ir_multi = mls_impulse_response(noisy, a)  # internal averaging over reps
    ir_single = mls_impulse_response(noisy[:length], a)  # one noisy period

    err_multi = float(np.max(np.abs(ir_multi[: b.size] - b)))
    err_single = float(np.max(np.abs(ir_single[: b.size] - b)))
    assert err_multi < err_single  # averaging lowers the error
    assert err_multi < 0.02  # recovers the filter within a tight tolerance


def test_invalid_arguments() -> None:
    with pytest.raises(ValueError):
        sweep_signal(FS, 100.0, 100.0, 1.0)  # f1 == f2
    with pytest.raises(ValueError):
        sweep_signal(FS, 100.0, 50.0, 1.0)  # f1 > f2
    with pytest.raises(ValueError):
        sweep_signal(FS, 20.0, 30000.0, 1.0)  # f2 > Nyquist
    with pytest.raises(ValueError):
        mls_signal(1)  # order too small
    with pytest.raises(ValueError):
        mls_signal(99)  # unsupported order
    with pytest.raises(ValueError):
        impulse_response(np.zeros(10), np.zeros(10), FS, method="bogus")
    with pytest.raises(ValueError):
        impulse_response(np.zeros(10), np.zeros(10), FS, method="farina")  # no f_range
    with pytest.raises(ValueError):
        mls_impulse_response(np.zeros(10), mls_signal(4))  # not a multiple of L
