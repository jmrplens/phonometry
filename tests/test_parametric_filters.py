#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for parametric filters: Weighting (A, C), Time Weighting and Linkwitz-Riley.
"""

import numpy as np
import pytest

from pyoctaveband import WeightingFilter, calculate_sensitivity, linkwitz_riley, octavefilter, time_weighting, weighting_filter


def test_calibration_logic() -> None:
    """
    Verify that calibration correctly maps digital RMS to target SPL.

    **Purpose:**
    Confirm that the `calculate_sensitivity` function produces a multiplier that accurately
    scales a digital signal to a known physical Sound Pressure Level (SPL) in dB.

    **Verification:**
    - Simulate a digital recording of a calibrator tone (e.g., 94 dB).
    - Calculate the sensitivity factor.
    - Analyze the same signal using that factor.

    **Expectation:**
    - The resulting SPL must be exactly the target value (e.g., 94.0 dB).
    """
    fs = 48000
    # Create a 'recording' of a 94dB tone (RMS = 0.5 for example)
    rms_ref = 0.5
    t = np.linspace(0, 1, fs)
    ref_signal = rms_ref * np.sqrt(2) * np.sin(2 * np.pi * 1000 * t)
    
    # Calculate sensitivity
    factor = calculate_sensitivity(ref_signal, target_spl=94.0)
    
    # Analyze same signal with that factor
    spl, _ = octavefilter(ref_signal, fs, fraction=1, limits=[800, 1200], calibration_factor=factor)
    
    # It should be exactly 94 dB
    assert abs(spl[0] - 94.0) < 0.01


def test_dbfs_logic() -> None:
    """
    Verify dBFS mode returns RMS relative to 1.0.

    **Purpose:**
    Ensure the `dbfs=True` option correctly calculates decibels relative to full scale (0 dBFS = RMS of 1.0).

    **Verification:**
    - Pass a sine wave with a peak of 1.0 (RMS = 0.707).

    **Expectation:**
    - The output should be approximately -3.01 dBFS.
    """
    fs = 48000
    # Sine wave with peak 1.0 -> RMS 0.707 -> -3.01 dBFS
    t = np.linspace(0, 1, fs)
    x = np.sin(2 * np.pi * 1000 * t)
    
    spl, _ = octavefilter(x, fs, fraction=1, limits=[800, 1200], dbfs=True)
    
    assert abs(spl[0] - (-3.01)) < 0.05


def test_peak_mode_logic() -> None:
    """
    Verify that Peak mode returns the absolute maximum of the filtered band.

    **Purpose:**
    Addressing Issue #10 regarding consistency with professional software (peak-holding).

    **Verification:**
    - Create a signal with a single high peak (impulse-like).
    - Compare RMS vs Peak output.

    **Expectation:**
    - Peak value should be significantly higher than RMS for a transient signal.
    - Peak value should match 20*log10(max_abs / 2e-5) approximately.
    """
    fs = 48000
    x = np.zeros(fs)
    x[100] = 0.5  # Large peak
    
    spl_rms, _ = octavefilter(x, fs, mode="rms", fraction=1)
    spl_peak, _ = octavefilter(x, fs, mode="peak", fraction=1)
    
    # Peak must be greater than RMS for an impulse
    assert np.all(spl_peak > spl_rms)
    
    # Theoretical peak for 0.5: 20*log10(0.5 / 2e-5) = 20*log10(25000) approx 87.9 dB
    # (Minus some attenuation due to the filter bandwidth and energy spreading)
    assert np.max(spl_peak) > 75.0


def test_a_weighting_response() -> None:
    """
    Verify A-weighting frequency response.

    **Purpose:**
    Confirm that the A-weighting filter matches the standardized IEC 61672-1:2013 gains at key frequencies.

    **Verification:**
    - Measure gain at 100Hz (expected -19.1 dB).
    - Measure gain at 1000Hz (expected 0.0 dB).
    - Measure gain at 8000Hz (expected -1.1 dB).

    **Expectation:**
    - Measured gains should match standard values within 1.0 dB.
    """
    fs = 48000
    duration = 1.0
    t = np.linspace(0, duration, fs, endpoint=False)
    
    test_freqs = [100, 1000, 8000]
    expected_gain = [-19.1, 0.0, -1.1]
    
    for f, expected in zip(test_freqs, expected_gain):
        # Generate tone
        x = np.sin(2 * np.pi * f * t)
        y = weighting_filter(x, fs, curve="A")
        
        # Calculate gain in dB (RMS)
        gain_db = 20 * np.log10(np.std(y) / np.std(x))
        assert abs(gain_db - expected) < 1.0, f"A-weighting at {f}Hz failed. Got {gain_db:.1f}dB, expected {expected}dB"


def test_c_weighting_response() -> None:
    """
    Verify C-weighting frequency response.

    **Purpose:**
    Confirm that the C-weighting filter matches the standardized IEC 61672-1:2013 gains.

    **Verification:**
    - Measure gain at 31.5Hz (expected -3.0 dB).
    - Measure gain at 1000Hz (expected 0.0 dB).
    - Measure gain at 8000Hz (expected -3.0 dB).

    **Expectation:**
    - Measured gains should match standard values within 1.0 dB.
    """
    fs = 48000
    duration = 1.0
    t = np.linspace(0, duration, fs, endpoint=False)
    
    test_freqs = [31.5, 1000, 8000]
    expected_gain = [-3.0, 0.0, -3.0]
    
    for f, expected in zip(test_freqs, expected_gain):
        x = np.sin(2 * np.pi * f * t)
        y = weighting_filter(x, fs, curve="C")
        
        gain_db = 20 * np.log10(np.std(y) / np.std(x))
        assert abs(gain_db - expected) < 1.0, f"C-weighting at {f}Hz failed. Got {gain_db:.1f}dB, expected {expected}dB"


def test_weighting_filter_c_output_shape() -> None:
    """Verify C-weighting preserves signal length."""
    fs = 48000
    rng = np.random.default_rng(42)
    x = rng.standard_normal(fs)

    y = weighting_filter(x, fs, curve="C")

    assert y.shape == x.shape


def test_weighting_filter_class_direct_use() -> None:
    """Verify direct WeightingFilter usage, Z bypass, and constructor validation."""
    fs = 48000
    rng = np.random.default_rng(42)
    x = rng.standard_normal((2, fs))

    wf = WeightingFilter(fs, curve="A")
    y = wf.filter(x)
    assert y.shape == x.shape

    wf_z = WeightingFilter(fs, curve="Z")
    y_z = wf_z.filter(x)
    np.testing.assert_allclose(y_z, x)

    with pytest.raises(ValueError):
        WeightingFilter(0)
    with pytest.raises(ValueError):
        WeightingFilter(fs, curve="invalid")


def test_time_weighting_fast() -> None:
    """
    Verify Fast (125ms) time weighting response to a step.

    **Purpose:**
    Validate the exponential integration constant ($\tau$) for time ballistics.

    **Verification:**
    - Apply a unit step (DC 1.0) to the fast integrator.
    - Measure the value at $t = \tau$.

    **Expectation:**
    - The value should be approximately $1 - e^{-1} \approx 0.632$ (63.2% rise).
    """
    fs = 1000
    tau = 0.125
    x = np.ones(int(fs * 2)) # Step signal
    
    y = time_weighting(x, fs, mode="fast")
    
    # Check at index corresponding to tau
    idx_tau = int(fs * tau)
    # Expected: 1 - exp(-1) approx 0.632
    assert abs(y[idx_tau] - 0.632) < 0.05


def test_time_weighting_initial_state_first() -> None:
    """
    Verify that initial_state='first' starts the integrator from the first energy value.
    """
    fs = 1000
    x = np.ones(fs)

    y = time_weighting(x, fs, mode="fast", initial_state="first")

    np.testing.assert_allclose(y, np.ones_like(y), rtol=1e-12, atol=1e-12)


def test_time_weighting_initial_state_custom() -> None:
    """
    Verify custom initial_state matches the recursive equation with y[-1] set.
    """
    fs = 1000
    tau = 0.125
    alpha = 1 - np.exp(-1 / (fs * tau))
    x = np.array([2.0, 0.5, -1.0, 0.0])
    initial_state = 0.25

    y = time_weighting(x, fs, mode="fast", initial_state=initial_state)

    expected = np.zeros_like(x)
    current = initial_state
    for idx, value in enumerate(x**2):
        current = alpha * value + (1 - alpha) * current
        expected[idx] = current

    np.testing.assert_allclose(y, expected, rtol=1e-12, atol=1e-12)


def test_time_weighting_initial_state_zero_matches_default() -> None:
    """Verify explicit zero initialization matches the default rest state."""
    fs = 1000
    x = np.array([2.0, 0.5, -1.0, 0.0])

    y_default = time_weighting(x, fs, mode="fast")
    y_zero = time_weighting(x, fs, mode="fast", initial_state="zero")

    np.testing.assert_allclose(y_zero, y_default, rtol=1e-12, atol=1e-12)


def test_time_weighting_initial_state_array_per_channel() -> None:
    """Verify array initial state is applied per input channel."""
    fs = 1000
    tau = 0.125
    alpha = 1 - np.exp(-1 / (fs * tau))
    x = np.vstack([np.ones(4), 2 * np.ones(4)])
    initial_state = np.array([0.25, 4.0])

    y = time_weighting(x, fs, mode="fast", initial_state=initial_state)

    expected = np.empty_like(x)
    current = initial_state.copy()
    for idx in range(x.shape[-1]):
        current = alpha * x[:, idx] ** 2 + (1 - alpha) * current
        expected[:, idx] = current

    np.testing.assert_allclose(y, expected, rtol=1e-12, atol=1e-12)


def test_time_weighting_initial_state_multichannel_first() -> None:
    """
    Verify initial_state='first' is applied independently per channel.
    """
    fs = 1000
    x = np.vstack([np.ones(fs), 2 * np.ones(fs)])

    y = time_weighting(x, fs, mode="fast", initial_state="first")

    expected = x**2
    np.testing.assert_allclose(y, expected, rtol=1e-12, atol=1e-12)


def test_time_weighting_initial_state_invalid() -> None:
    """
    Verify invalid initial_state names are rejected.
    """
    fs = 1000
    x = np.ones(fs)

    with pytest.raises(ValueError, match="initial_state"):
        time_weighting(x, fs, mode="fast", initial_state="invalid")

    with pytest.raises(ValueError, match="broadcastable"):
        time_weighting(np.ones((2, 10)), fs, mode="fast", initial_state=np.ones(3))


def test_time_weighting_initial_state_first_rejects_empty_input() -> None:
    """Verify initial_state='first' requires at least one sample."""
    with pytest.raises(ValueError, match="initial_state"):
        time_weighting(np.array([]), 1000, mode="fast", initial_state="first")


@pytest.mark.parametrize("mode", ["fast", "slow", "impulse"])
def test_time_weighting_rejects_non_positive_sample_rate(mode: str) -> None:
    """Verify time weighting rejects non-positive sample rates before coefficient math."""
    with pytest.raises(ValueError, match="Sample rate 'fs' must be positive"):
        time_weighting(np.ones(10), 0, mode=mode)


def test_time_weighting_impulse_multichannel() -> None:
    """Verify impulse time weighting supports multichannel input."""
    fs = 1000
    x = np.zeros((2, fs))
    x[:, 0] = 1.0

    y = time_weighting(x, fs, mode="impulse")

    assert y.shape == x.shape
    assert y[0, 100] < y[0, 0]


def test_time_weighting_impulse_initial_state_first_1d() -> None:
    """Verify impulse time weighting can start from the first sample energy."""
    fs = 1000
    x = np.ones(fs)

    y = time_weighting(x, fs, mode="impulse", initial_state="first")

    np.testing.assert_allclose(y, np.ones_like(y), rtol=1e-12, atol=1e-12)


def test_linkwitz_riley_sum() -> None:
    """
    Verify that the sum of Linkwitz-Riley bands is flat.

    **Purpose:**
    The defining characteristic of an LR4 crossover is that the combined response of the
    low-pass and high-pass bands is perfectly flat.

    **Verification:**
    - Split white noise at 1000 Hz using `linkwitz_riley`.
    - Sum the resulting bands.
    - Measure the total RMS gain.

    **Expectation:**
    - The gain of the sum should be 1.0 (0 dB) with very low error ($< 0.1$ dB).
    """
    fs = 48000
    rng = np.random.default_rng(42)
    x = rng.standard_normal(fs)
    
    # Split at 1000 Hz
    lp, hp = linkwitz_riley(x, fs, freq=1000, order=4)
    
    # Sum of bands
    y_sum = lp + hp
    
    # Check RMS ratio
    gain_db = 20 * np.log10(np.std(y_sum) / np.std(x))
    assert abs(gain_db) < 0.1, f"Linkwitz-Riley sum not flat: {gain_db:.2f} dB"


def test_weighting_z_bypass() -> None:
    """
    Verify Z-weighting is a bypass.

    **Purpose:**
    Confirm that 'Z' (Zero weighting) does not modify the signal.

    **Verification:**
    - Compare input and output arrays.

    **Expectation:**
    - Arrays must be identical.
    """
    rng = np.random.default_rng(42)
    x = rng.standard_normal(1000)
    y = weighting_filter(x, 48000, curve="Z")
    assert np.all(x == y)