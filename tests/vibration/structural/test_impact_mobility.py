#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for mobility measured by impact excitation (ISO 7626-5:2019).

ISO 7626-5 prints no worked example, so every number here is anchored in
closed form. The structure is a single-degree-of-freedom resonator struck by a
Gaussian force pulse, whose response has an exact expression (the convolution
of the modal impulse response with the pulse, through the complementary error
function of a complex argument). The pulse is smooth enough that its spectrum
is negligible at the Nyquist frequency, so the discrete Fourier transform of
the sampled records is the continuous one to about 1e-9 below 500 Hz: the
averaged estimate of 8.6 must return the resonator's mobility, and after an
exponential window the Annex A correction must return its damping and its
mobility.
"""

from __future__ import annotations

import math
import warnings
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pytest
import reference_data as ref

from phonometry import vibration
from phonometry.io import Signal
from phonometry.vibration.structural.impact_mobility import (
    CHANNEL_MAGNITUDE_TOLERANCE,
    CHANNEL_PHASE_TOLERANCE_DEG,
    COHERENCE_RECORDS,
    HIGH_COHERENCE,
    RESPONSE_END_RATIO,
    RESPONSE_MIDPOINT_RATIO,
    WINDOWED_RESPONSE_END_RATIO,
    ExponentialWindowCorrection,
    ImpactExcitationWarning,
    ImpactMobilityResult,
)
from phonometry.vibration.structural.mechanical_mobility import (
    sdof_accelerance,
    sdof_mobility,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from numpy.typing import NDArray

    from phonometry.vibration.structural.impact_mobility import ResponseQuantity

FS = ref.ISO7626_5_FS_HZ
N = ref.ISO7626_5_SAMPLES
MASS_KG = ref.ISO7626_5_MASS_KG
F_N_HZ = ref.ISO7626_5_NATURAL_FREQUENCY_HZ
PULSE_SIGMA_S = ref.ISO7626_5_PULSE_SIGMA_S
PEAK_N = ref.ISO7626_5_PEAK_N


def _stiffness(mass_kg: float, natural_frequency_hz: float) -> float:
    return mass_kg * (2.0 * math.pi * natural_frequency_hz) ** 2


def _damping(
    mass_kg: float, natural_frequency_hz: float, damping_ratio: float
) -> float:
    return (
        2.0
        * damping_ratio
        * math.sqrt(_stiffness(mass_kg, natural_frequency_hz) * mass_kg)
    )


def _sdof_impact(
    damping_ratio: float, *, quantity: str = "acceleration"
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Force and exact response of the resonator (see ``reference_data``)."""
    return ref.sdof_gaussian_impact(damping_ratio, quantity=quantity)


def _band(frequencies: NDArray[np.float64], top_hz: float = 500.0) -> NDArray[np.bool_]:
    return np.asarray(frequencies) <= top_hz


# ---------------------------------------------------------------------------
# Spectra and windows.
# ---------------------------------------------------------------------------


def test_energy_spectral_density_of_a_gaussian_pulse_is_twice_its_squared_transform() -> (
    None
):
    """3.3 and 3.4: G = 2|F|^2 with F the continuous transform of the pulse."""
    force, _ = _sdof_impact(0.1)
    freqs, esd = vibration.energy_spectral_density(force, FS)
    analytic = (
        PEAK_N
        * PULSE_SIGMA_S
        * math.sqrt(2.0 * math.pi)
        * np.exp(-((2.0 * math.pi * freqs * PULSE_SIGMA_S) ** 2) / 2.0)
    )
    inside = (freqs > 0.0) & _band(freqs)
    np.testing.assert_allclose(esd[inside], 2.0 * analytic[inside] ** 2, rtol=1e-9)
    assert esd[0] == pytest.approx(analytic[0] ** 2, rel=1e-9)


def test_energy_spectral_density_keeps_the_energy_of_the_record() -> None:
    """Parseval: the one-sided density, DC and Nyquist bins single, sums to the energy."""
    rng = np.random.default_rng(7626)
    record = rng.standard_normal(N)
    freqs, esd = vibration.energy_spectral_density(record, FS)
    assert freqs[-1] == pytest.approx(FS / 2.0)
    energy = float(np.sum(record**2)) / FS
    assert float(np.sum(esd)) * FS / N == pytest.approx(energy, rel=1e-12)


def test_the_force_density_is_averaged_over_the_impacts_and_one_sided() -> None:
    """3.4 and 8.6: G_FF is 2|F|^2 averaged over the impacts."""
    force, response = _sdof_impact(0.1)
    scales = np.array([1.0, 1.25, 1.5])
    res = vibration.impact_mobility(
        scales[:, np.newaxis] * force, scales[:, np.newaxis] * response, FS
    )
    freqs = res.frequencies
    transform = (
        PEAK_N
        * PULSE_SIGMA_S
        * math.sqrt(2.0 * math.pi)
        * np.exp(-((2.0 * math.pi * freqs * PULSE_SIGMA_S) ** 2) / 2.0)
    )
    expected = 2.0 * transform**2 * float(np.mean(scales**2))
    inside = _band(freqs)
    np.testing.assert_allclose(
        res.force_energy_spectral_density[inside], expected[inside], rtol=1e-9
    )


def test_force_window_is_unity_over_its_width_and_exactly_zero_elsewhere() -> None:
    window = vibration.force_window(N, FS, width_s=0.02, start_s=0.001)
    t = np.arange(N) / FS
    inside = (t >= 0.001) & (t < 0.021)
    assert np.all(window[inside] == 1.0)
    assert np.all(window[~inside] == 0.0)


def test_force_window_taper_lies_outside_the_unity_part() -> None:
    window = vibration.force_window(N, FS, width_s=0.02, start_s=0.01, taper_s=0.005)
    t = np.arange(N) / FS
    assert np.all(window[(t >= 0.01) & (t < 0.03)] == 1.0)
    ramp = (t >= 0.03) & (t < 0.035)
    assert np.all(np.diff(window[ramp]) < 0.0)
    assert np.all((window[ramp] > 0.0) & (window[ramp] <= 1.0))
    assert np.all(window[t >= 0.035] == 0.0)
    assert np.all(window[t < 0.005] == 0.0)


def test_force_window_must_end_inside_the_record() -> None:
    with pytest.raises(ValueError, match="force window ends"):
        vibration.force_window(N, FS, width_s=2.0)


def test_a_force_window_open_at_the_last_sample_is_refused() -> None:
    """8.5.1: the window sets the samples after the pulse to zero.

    The last sample sits at (N - 1)/fs. A unity part that reaches it, or a
    ramp that does, leaves no sample at zero, however short of N/fs it ends.
    """
    with pytest.raises(ValueError, match="force window ends"):
        vibration.force_window(64, 64.0, width_s=1.0)
    with pytest.raises(ValueError, match="force window ends"):
        vibration.force_window(64, 64.0, width_s=0.99)
    with pytest.raises(ValueError, match="falling ramp"):
        vibration.force_window(64, 64.0, width_s=0.1, start_s=0.2, taper_s=100.0)
    closing = vibration.force_window(64, 64.0, width_s=63.0 / 64.0)
    assert np.all(closing[:-1] == 1.0)
    assert closing[-1] == 0.0


def test_exponential_window_ends_at_the_stated_value() -> None:
    """8.5.2 and Figure 10: a window that decays to 5 % at the end of the record."""
    rate = vibration.exponential_decay_rate(N, FS, final_value=0.05)
    window = vibration.exponential_window(N, FS, decay_rate_per_s=rate)
    assert window[0] == 1.0
    assert window[-1] == pytest.approx(0.05, rel=1e-12)
    assert rate == pytest.approx(-math.log(0.05) * FS / (N - 1), rel=1e-15)


def test_exponential_decay_rate_refuses_a_growing_window() -> None:
    with pytest.raises(ValueError, match="final_value"):
        vibration.exponential_decay_rate(N, FS, final_value=1.5)


# ---------------------------------------------------------------------------
# The averaged estimate (8.6).
# ---------------------------------------------------------------------------


def test_a_well_damped_resonator_gives_its_mobility_back() -> None:
    """With the decay inside the record the estimate is the resonator's mobility."""
    zeta = 0.1
    force, response = _sdof_impact(zeta)
    res = vibration.impact_mobility(force, response, FS)
    band = _band(res.frequencies)
    expected = sdof_mobility(
        res.frequencies[band],
        MASS_KG,
        _stiffness(MASS_KG, F_N_HZ),
        _damping(MASS_KG, F_N_HZ, zeta),
    )
    # 2e-8 at 1 Hz, where the mobility is smallest and the record's finite
    # length (the decay is 1e-11 of its start at the end) weighs the most.
    np.testing.assert_allclose(res.mobility[band], expected, rtol=1e-7)
    assert np.all(res.coherence == pytest.approx(1.0))


@pytest.mark.parametrize("quantity", ["acceleration", "velocity", "displacement"])
def test_every_response_quantity_gives_the_same_mobility(quantity: str) -> None:
    zeta = 0.1
    force, response = _sdof_impact(zeta, quantity=quantity)
    res = vibration.impact_mobility(
        force, response, FS, response_quantity=cast("ResponseQuantity", quantity)
    )
    band = _band(res.frequencies)
    expected = sdof_mobility(
        res.frequencies[band],
        MASS_KG,
        _stiffness(MASS_KG, F_N_HZ),
        _damping(MASS_KG, F_N_HZ, zeta),
    )
    np.testing.assert_allclose(res.mobility[band], expected, rtol=1e-7)
    assert res.response_quantity == quantity


def test_exponential_window_shifts_every_pole_by_the_decay_rate() -> None:
    """Formula (A.2): the windowed accelerance is A(s + a), exactly."""
    zeta, rate = 0.005, 20.0
    force, response = _sdof_impact(zeta)
    res = vibration.impact_mobility(
        force, response, FS, exponential_decay_rate_per_s=rate
    )
    band = _band(res.frequencies)
    s = 2j * np.pi * res.frequencies[band]
    omega_n = 2.0 * math.pi * F_N_HZ
    shifted = (s + rate) ** 2 / (
        MASS_KG * ((s + rate) ** 2 + 2.0 * zeta * omega_n * (s + rate) + omega_n**2)
    )
    np.testing.assert_allclose(res.to("accelerance")[band], shifted, rtol=1e-7)


def test_the_window_lowers_the_resonance_peak() -> None:
    """Figure 10: every resonance peak shows reduced amplitude."""
    force, response = _sdof_impact(0.005)
    bare = vibration.impact_mobility(force, response, FS)
    windowed = vibration.impact_mobility(
        force, response, FS, exponential_decay_rate_per_s=5.0
    )
    assert np.max(windowed.magnitude) < 0.5 * np.max(bare.magnitude)


def test_a_rigid_mass_calibrates_to_one_over_its_mass() -> None:
    """7.2: the accelerance of a free rigid block is 1/m at every frequency."""
    force, _ = _sdof_impact(0.1)
    block_kg = 3.0
    res = vibration.impact_mobility(
        force,
        force / block_kg,
        FS,
        exponential_decay_rate_per_s=10.0,
        force_window_s=0.02,
    )
    band = _band(res.frequencies)
    np.testing.assert_allclose(res.to("accelerance")[band], 1.0 / block_kg, rtol=1e-12)
    check = vibration.rigid_mass_calibration_check(
        res.to("accelerance")[band], res.frequencies[band], block_kg
    )
    assert check.passes


def test_averaging_is_the_ratio_of_averaged_spectra() -> None:
    """8.6: the averaged cross-spectrum over the averaged force auto-spectrum."""
    rng = np.random.default_rng(7)
    force, response = _sdof_impact(0.1)
    forces = np.array([force * (1.0 + 0.2 * i) for i in range(4)])
    responses = np.array(
        [response * (1.0 + 0.2 * i) + 0.02 * rng.standard_normal(N) for i in range(4)]
    )
    res = vibration.impact_mobility(forces, responses, FS)
    f_spec = np.fft.rfft(forces, axis=1) / FS
    x_spec = np.fft.rfft(responses, axis=1) / FS
    cross = np.sum(x_spec * np.conj(f_spec), axis=0)[1:]
    auto_f = np.sum(np.abs(f_spec) ** 2, axis=0)[1:]
    auto_x = np.sum(np.abs(x_spec) ** 2, axis=0)[1:]
    np.testing.assert_allclose(res.to("accelerance"), cross / auto_f, rtol=1e-12)
    np.testing.assert_allclose(
        res.coherence, np.abs(cross) ** 2 / (auto_f * auto_x), rtol=1e-10
    )
    assert res.impacts == 4
    assert np.min(res.coherence) < 1.0


def test_response_only_window_scales_each_force_by_its_peak_value() -> None:
    """Annex A: with the response windowed alone, F times w(t at peak force)."""
    force, response = _sdof_impact(0.005)
    rate = 20.0
    res = vibration.impact_mobility(
        force,
        response,
        FS,
        exponential_decay_rate_per_s=rate,
        exponential_on_force=False,
    )
    window = vibration.exponential_window(N, FS, decay_rate_per_s=rate)
    peak = int(np.argmax(force))
    manual = (np.fft.rfft(response * window) / np.fft.rfft(force * window[peak]))[1:]
    np.testing.assert_allclose(res.to("accelerance"), manual, rtol=1e-12)


def test_a_force_window_that_removes_an_impact_warns() -> None:
    """6.4: never use a force window to eliminate secondary impacts."""
    force, response = _sdof_impact(0.1)
    double = force + 0.6 * np.roll(force, 245)
    with pytest.warns(ImpactExcitationWarning, match="6.4"):
        vibration.impact_mobility(double, response, FS, force_window_s=0.02)


def test_a_force_window_around_the_whole_pulse_is_silent() -> None:
    force, response = _sdof_impact(0.1)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ImpactExcitationWarning)
        vibration.impact_mobility(force, response, FS, force_window_s=0.02)


def test_records_of_different_shapes_are_refused() -> None:
    force, response = _sdof_impact(0.1)
    with pytest.raises(ValueError, match="same shape"):
        vibration.impact_mobility(force, response[:-1], FS)


def test_a_vanishing_force_spectrum_is_refused() -> None:
    # Alternate samples: the spectrum holds DC and the Nyquist bin, nothing else.
    pulse_train = np.tile(np.array([1.0, 0.0]), N // 2)
    response = np.zeros(N)
    with pytest.raises(ValueError, match="force spectrum vanishes"):
        vibration.impact_mobility(pulse_train, response, FS)


def test_a_notch_between_two_equal_impacts_is_refused() -> None:
    """Two equal impacts 1/6 s apart cancel at 3, 9, 15, ... Hz.

    On 1 500 samples the transform leaves those notches at about 1e-16 of the
    pulse and at an exact zero only in a few of them, so the refusal cannot
    wait for a zero: the rigid block's accelerance would otherwise come back
    as rounding over rounding at every notch.
    """
    fs = 1500.0
    t = np.arange(1500) / fs
    pulse = np.exp(-(((t - 0.05) / 0.004) ** 2) / 2.0)
    double = pulse + np.roll(pulse, 250)
    with pytest.raises(ValueError, match="force spectrum vanishes at 15 Hz"):
        vibration.impact_mobility(
            double, double / MASS_KG, fs, frequency_range_hz=(10.0, 100.0)
        )
    between = vibration.impact_mobility(
        double, double / MASS_KG, fs, frequency_range_hz=(10.0, 14.0)
    )
    np.testing.assert_allclose(between.to("accelerance"), 1.0 / MASS_KG, rtol=1e-12)


def test_the_frequency_range_of_interest_keeps_the_estimate_inside_it() -> None:
    """3.2: the range crops the bins and leaves the estimate on them unchanged."""
    force, response = _sdof_impact(0.1)
    whole = vibration.impact_mobility(force, response, FS)
    kept = vibration.impact_mobility(
        force, response, FS, frequency_range_hz=(20.0, 400.0)
    )
    inside = (whole.frequencies >= 20.0) & (whole.frequencies <= 400.0)
    np.testing.assert_array_equal(kept.frequencies, whole.frequencies[inside])
    np.testing.assert_array_equal(kept.mobility, whole.mobility[inside])
    np.testing.assert_array_equal(kept.coherence, whole.coherence[inside])
    np.testing.assert_array_equal(
        kept.force_energy_spectral_density,
        whole.force_energy_spectral_density[inside],
    )


def test_a_range_between_two_bins_is_refused() -> None:
    force, response = _sdof_impact(0.1)
    with pytest.raises(ValueError, match="holds no DFT bin"):
        vibration.impact_mobility(force, response, FS, frequency_range_hz=(10.2, 10.8))


def test_a_range_above_the_nyquist_frequency_is_refused() -> None:
    force, response = _sdof_impact(0.1)
    with pytest.raises(ValueError, match="Nyquist"):
        vibration.impact_mobility(force, response, FS, frequency_range_hz=(10.0, FS))


def test_an_odd_record_reaches_the_nyquist_frequency_itself() -> None:
    """8.3: the Nyquist frequency is half the sample rate, bin or no bin.

    An odd record has no bin at fs/2; its last one lies half a bin below. A
    range that ends at fs/2 holds that bin, and one just above fs/2 is refused
    with the two numbers printed apart.
    """
    force, response = _sdof_impact(0.1)
    odd = N - 1
    kept = vibration.impact_mobility(
        force[:odd], response[:odd], FS, frequency_range_hz=(10.0, FS / 2.0)
    )
    assert kept.frequencies[-1] == pytest.approx((odd - 1) / 2.0 * FS / odd)
    check = vibration.check_force_spectrum(
        force[:odd], FS, frequency_range_hz=(10.0, FS / 2.0), max_drop_db=400.0
    )
    assert check.frequencies[-1] == kept.frequencies[-1]
    with pytest.raises(
        ValueError, match=r"2048\.001 Hz, above the Nyquist frequency 2048 Hz"
    ):
        vibration.impact_mobility(
            force[:odd], response[:odd], FS, frequency_range_hz=(10.0, 2048.001)
        )


@pytest.mark.parametrize(
    ("call", "name"),
    [
        (
            lambda f, x: vibration.impact_mobility(
                f, x, FS, frequency_range_hz=cast("Any", (10.0,))
            ),
            "frequency_range_hz",
        ),
        (
            lambda f, x: vibration.check_force_spectrum(
                f, FS, frequency_range_hz=cast("Any", 400.0), max_drop_db=10.0
            ),
            "frequency_range_hz",
        ),
        (
            lambda f, x: vibration.single_mode_fit(
                np.linspace(1.0, 100.0, 100), np.ones(100), band_hz=cast("Any", (50.0,))
            ),
            "band_hz",
        ),
        (
            lambda f, x: vibration.check_coherence(
                vibration.impact_mobility(f, x, FS),
                frequency_range_hz=(10.0, 400.0),
                exclude_hz=cast("Any", (40.0, 50.0)),
            ),
            "exclude_hz",
        ),
        (
            lambda f, x: vibration.check_coherence(
                vibration.impact_mobility(f, x, FS),
                frequency_range_hz=(10.0, 400.0),
                exclude_hz=cast("Any", [(40.0, 50.0, 60.0)]),
            ),
            r"exclude_hz\[0\]",
        ),
    ],
    ids=[
        "one-number-range",
        "bare-number-range",
        "one-number-band",
        "bare-band",
        "triple",
    ],
)
def test_a_malformed_pair_is_refused_by_name(
    call: Callable[[NDArray[np.float64], NDArray[np.float64]], object], name: str
) -> None:
    """A one-number range, a bare number or a bare band says which argument."""
    force, response = _sdof_impact(0.1)
    with pytest.raises(ValueError, match=f"'{name}' must be a"):
        call(force, response)


def test_result_rejects_an_unknown_response_quantity() -> None:
    frequencies = np.array([1.0, 2.0])
    mobility = np.array([1.0, 1.0], dtype=complex)
    ones = np.ones(2)
    with pytest.raises(ValueError, match="response_quantity"):
        ImpactMobilityResult(
            frequencies=frequencies,
            mobility=mobility,
            coherence=ones,
            force_energy_spectral_density=ones,
            impacts=1,
            response_quantity="jerk",  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# One mode, and the correction of Annex A.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("quantity", ["acceleration", "velocity", "displacement"])
def test_windowing_and_correction_give_the_resonator_back(quantity: str) -> None:
    """The closed-form anchor: damping and mobility back after Annex A."""
    zeta, rate = 0.005, 20.0
    force, response = _sdof_impact(zeta, quantity=quantity)
    res = vibration.impact_mobility(
        force,
        response,
        FS,
        response_quantity=cast("ResponseQuantity", quantity),
        exponential_decay_rate_per_s=rate,
    )
    fit = res.fit_mode((30.0, 50.0))
    omega_d = 2.0 * math.pi * F_N_HZ * math.sqrt(1.0 - zeta**2)
    assert fit.damped_natural_frequency_hz == pytest.approx(
        omega_d / (2.0 * math.pi), rel=1e-8
    )
    correction = fit.correction
    assert correction.exact_damping_ratio[0] == pytest.approx(zeta, rel=1e-6)
    band = _band(res.frequencies)
    expected = sdof_mobility(
        res.frequencies[band],
        MASS_KG,
        _stiffness(MASS_KG, F_N_HZ),
        _damping(MASS_KG, F_N_HZ, zeta),
    )
    np.testing.assert_allclose(
        fit.corrected_mobility(res.frequencies[band]), expected, rtol=1e-6
    )


def test_the_fitted_accelerance_carries_the_mass_line() -> None:
    """For accelerance the direct term of the fit is 1/m (the mass line)."""
    force, response = _sdof_impact(0.005)
    res = vibration.impact_mobility(
        force, response, FS, exponential_decay_rate_per_s=20.0
    )
    fit = res.fit_mode((30.0, 50.0))
    assert fit.kind == "accelerance"
    assert complex(fit.direct_term).real == pytest.approx(1.0 / MASS_KG, rel=1e-8)


def test_formula_a3_as_printed() -> None:
    """Formula (A.3): zeta_r = zeta_hat_r - a / omega_r, omega_r damped, in rad/s."""
    correction = vibration.exponential_window_correction(
        [40.0, 125.0], [0.03, 0.02], exponential_decay_rate_per_s=5.0
    )
    omega = 2.0 * math.pi * np.array([40.0, 125.0])
    np.testing.assert_allclose(correction.window_damping_ratio, 5.0 / omega, rtol=1e-15)
    np.testing.assert_allclose(
        correction.damping_ratio, np.array([0.03, 0.02]) - 5.0 / omega, rtol=1e-15
    )
    np.testing.assert_allclose(
        correction.peak_correction_factor,
        np.array([0.03, 0.02]) / correction.damping_ratio,
        rtol=1e-15,
    )


def test_formula_a3_is_the_first_order_of_the_pole_shift() -> None:
    """A.3 and the exact pole shift differ by about (zeta_hat**3 - zeta**3) / 2."""
    zeta, rate = 0.005, 20.0
    force, response = _sdof_impact(zeta)
    res = vibration.impact_mobility(
        force, response, FS, exponential_decay_rate_per_s=rate
    )
    correction = res.fit_mode((30.0, 50.0)).correction
    zeta_hat = float(correction.apparent_damping_ratio[0])
    difference = float(correction.damping_ratio[0] - correction.exact_damping_ratio[0])
    assert difference == pytest.approx(-(zeta_hat**3 - zeta**3) / 2.0, rel=0.02)
    assert difference < 0.0


def _modal_mobility(
    frequencies: NDArray[np.float64], natural_frequency_hz: float, damping_ratio: float
) -> NDArray[np.complex128]:
    return np.asarray(
        sdof_mobility(
            frequencies,
            MASS_KG,
            _stiffness(MASS_KG, natural_frequency_hz),
            _damping(MASS_KG, natural_frequency_hz, damping_ratio),
        ),
        dtype=np.complex128,
    )


def test_the_fit_holds_its_mode_against_one_outside_the_band() -> None:
    """The direct term and the reweighting absorb a second mode out of band."""
    freqs = np.arange(1.0, 501.0)
    two_modes = _modal_mobility(freqs, F_N_HZ, 0.005) + _modal_mobility(
        freqs, 125.0, 0.01
    )
    fit = vibration.single_mode_fit(freqs, two_modes, band_hz=(30.0, 50.0))
    damped = F_N_HZ * math.sqrt(1.0 - 0.005**2)
    assert fit.damped_natural_frequency_hz == pytest.approx(damped, abs=2e-3)
    assert fit.apparent_damping_ratio == pytest.approx(0.005, rel=5e-3)


def test_the_fit_settles_on_noisy_data() -> None:
    """1 % complex noise on the mobility moves the fitted mode by little."""
    freqs = np.arange(1.0, 501.0)
    rng = np.random.default_rng(7626)
    noise = rng.standard_normal(freqs.size) + 1j * rng.standard_normal(freqs.size)
    noisy = _modal_mobility(freqs, F_N_HZ, 0.005) * (1.0 + 0.01 * noise / math.sqrt(2))
    fit = vibration.single_mode_fit(freqs, noisy, band_hz=(30.0, 50.0))
    damped = F_N_HZ * math.sqrt(1.0 - 0.005**2)
    assert fit.damped_natural_frequency_hz == pytest.approx(damped, abs=5e-3)
    assert fit.apparent_damping_ratio == pytest.approx(0.005, rel=0.02)


def test_peak_factor_restores_a_lightly_damped_peak() -> None:
    """Annex A: for a lightly damped mode the peak scales by zeta_hat / zeta."""
    zeta, rate = 0.005, 5.0
    force, response = _sdof_impact(zeta, quantity="velocity")
    windowed = vibration.impact_mobility(
        force,
        response,
        FS,
        response_quantity="velocity",
        exponential_decay_rate_per_s=rate,
    )
    correction = windowed.fit_mode((30.0, 50.0)).correction
    true_peak = 1.0 / _damping(MASS_KG, F_N_HZ, zeta)
    band = _band(windowed.frequencies)
    measured_peak = float(np.max(windowed.magnitude[band]))
    restored = measured_peak * float(correction.peak_correction_factor[0])
    assert restored == pytest.approx(true_peak, rel=0.01)


def test_a_window_heavier_than_the_apparent_damping_is_refused() -> None:
    with pytest.raises(ValueError, match="not below the apparent damping"):
        vibration.exponential_window_correction(
            40.0, 0.01, exponential_decay_rate_per_s=10.0
        )


def test_correction_rejects_a_damping_ratio_outside_the_unit_interval() -> None:
    frequency = np.array([40.0])
    damping = np.array([1.2])
    with pytest.raises(ValueError, match="apparent_damping_ratio"):
        ExponentialWindowCorrection(
            damped_natural_frequency_hz=frequency,
            apparent_damping_ratio=damping,
            exponential_decay_rate_per_s=0.0,
        )


_LINE_FREQUENCIES = np.linspace(1.0, 100.0, 200)
_LINE_OMEGA = 2.0 * math.pi * _LINE_FREQUENCIES


def _flat(relative_noise: float = 0.0) -> NDArray[np.complex128]:
    """A constant mobility, with complex noise of the given relative level."""
    rng = np.random.default_rng(7626)
    noise = rng.standard_normal(_LINE_FREQUENCIES.size) + 1j * rng.standard_normal(
        _LINE_FREQUENCIES.size
    )
    return np.asarray(
        1e-3 * (1.0 + relative_noise * noise / math.sqrt(2.0)), dtype=np.complex128
    )


def _flat_one_ulp_up() -> NDArray[np.complex128]:
    """The constant mobility with one sample raised by one unit in the last place."""
    flat = _flat()
    flat[42] = np.nextafter(1e-3, 1.0)
    return flat


@pytest.mark.parametrize(
    ("frf", "kind"),
    [
        pytest.param(_flat(), "mobility", id="flat"),
        pytest.param(_flat(1e-12), "mobility", id="flat-with-noise-1e-12"),
        pytest.param(_flat_one_ulp_up(), "mobility", id="flat-one-ulp-up"),
        pytest.param(1.0 / (1j * _LINE_OMEGA * MASS_KG), "mobility", id="mass-line"),
        pytest.param(1j * _LINE_OMEGA / 1e5, "mobility", id="spring-line"),
        pytest.param(
            -1.0 / (MASS_KG * _LINE_OMEGA**2) + 0j, "receptance", id="free-mass"
        ),
    ],
)
def test_a_band_without_a_mode_is_refused(
    frf: NDArray[np.complex128], kind: str
) -> None:
    """A line without a resonance fixes no pole, down to the last bit.

    A constant, a mass line or a spring line fits the numerator alone and
    leaves the denominator to rounding; the free mass determines its pole, at
    zero frequency and without decay. Neither is a mode, on any platform.
    """
    with pytest.raises(ValueError, match="no lightly damped mode"):
        vibration.single_mode_fit(
            _LINE_FREQUENCIES, frf, band_hz=(20.0, 60.0), kind=kind
        )


def test_a_mode_over_the_same_band_is_found() -> None:
    """The refusal leaves a lightly damped mode on the same line, noise and all."""
    zeta = 0.01
    frf = _flat(1e-12) + _modal_mobility(_LINE_FREQUENCIES, F_N_HZ, zeta)
    fit = vibration.single_mode_fit(_LINE_FREQUENCIES, frf, band_hz=(20.0, 60.0))
    damped = F_N_HZ * math.sqrt(1.0 - zeta**2)
    assert fit.damped_natural_frequency_hz == pytest.approx(damped, rel=1e-8)
    assert fit.apparent_damping_ratio == pytest.approx(zeta, rel=1e-8)
    assert complex(fit.direct_term) == pytest.approx(1e-3, rel=1e-8)


def test_a_band_of_two_frequencies_is_refused() -> None:
    freqs = np.array([10.0, 20.0, 30.0])
    values = np.ones(3, dtype=complex)
    with pytest.raises(ValueError, match="band_hz"):
        vibration.single_mode_fit(freqs, values, band_hz=(15.0, 30.0))


# ---------------------------------------------------------------------------
# Double hits (6.4).
# ---------------------------------------------------------------------------


def test_two_equal_impacts_cut_notches_every_one_over_their_delay() -> None:
    """Figure 5: the notches of two pulses tau apart fall at (2k + 1)/(2 tau)."""
    force, _ = _sdof_impact(0.1)
    shift = 256  # tau = 62.5 ms: the notches land on DFT bins 8, 24, 40, ...
    double = force + np.roll(force, shift)
    freqs, esd = vibration.energy_spectral_density(double, FS)
    _, single = vibration.energy_spectral_density(force, FS)
    notches = (2 * np.arange(6) + 1) * (N // (2 * shift))
    assert np.all(esd[notches] <= 1e-20 * single[notches])
    peaks = 2 * np.arange(1, 6) * (N // (2 * shift))
    np.testing.assert_allclose(esd[peaks], 4.0 * single[peaks], rtol=1e-12)
    check = vibration.check_double_hit(double, FS)
    assert not check.passes
    assert check.impacts == 2
    assert check.delay_s == pytest.approx(shift / FS)
    assert check.notch_spacing_hz == pytest.approx(FS / shift)
    assert math.isinf(check.ripple_db)


def test_ripple_of_a_smaller_second_impact() -> None:
    force, _ = _sdof_impact(0.1)
    check = vibration.check_double_hit(force + 0.6 * np.roll(force, 245), FS)
    assert check.secondary_ratio == pytest.approx(0.6, rel=1e-6)
    assert check.ripple_db == pytest.approx(20.0 * math.log10(1.6 / 0.4), rel=1e-6)


def test_a_single_impact_passes() -> None:
    force, _ = _sdof_impact(0.1)
    check = vibration.check_double_hit(force, FS)
    assert check.passes
    assert check.impacts == 1
    assert check.delay_s is None
    assert check.notch_spacing_hz is None
    assert check.ripple_db == 0.0


def test_the_threshold_decides_what_counts_as_an_impact() -> None:
    force, _ = _sdof_impact(0.1)
    record = force + 0.05 * np.roll(force, 245)
    assert vibration.check_double_hit(record, FS).passes
    assert not vibration.check_double_hit(record, FS, threshold_ratio=0.02).passes


def test_a_force_transducer_wired_backwards_reads_the_same() -> None:
    force, _ = _sdof_impact(0.1)
    check = vibration.check_double_hit(-(force + 0.6 * np.roll(force, 245)), FS)
    assert check.impacts == 2


def test_a_record_without_force_is_refused() -> None:
    silence = np.zeros(N)
    with pytest.raises(ValueError, match="holds no force"):
        vibration.check_double_hit(silence, FS)


def test_the_threshold_must_lie_below_the_largest_force() -> None:
    force, _ = _sdof_impact(0.1)
    with pytest.raises(ValueError, match="threshold_ratio"):
        vibration.check_double_hit(force, FS, threshold_ratio=1.0)


def test_a_steep_anti_aliasing_filter_can_ring_above_the_threshold() -> None:
    """6.4: a hard tip through a steep filter reads as several impacts."""
    from scipy import signal as sp_signal

    oversampling = 16
    fast = FS * oversampling
    t = np.arange(N * oversampling) / fast
    hard_tip = PEAK_N * np.exp(-((t - 0.005) ** 2) / (2.0 * 5e-5**2))
    sos = sp_signal.ellip(8, 0.1, 90.0, 0.4 * FS, output="sos", fs=fast)
    filtered = sp_signal.sosfilt(sos, hard_tip)[::oversampling]
    assert not vibration.check_double_hit(filtered, FS).passes
    unfiltered = hard_tip[::oversampling]
    assert vibration.check_double_hit(unfiltered, FS).passes


def test_a_softer_rebound_ripples_more_than_its_peak_says() -> None:
    """6.4: a wide, weak second pulse passes the threshold but not the spectrum."""
    t = np.arange(N) / FS
    first = PEAK_N * np.exp(-((t - 0.005) ** 2) / (2.0 * 0.0005**2))
    rebound = 8.0 * np.exp(-((t - 0.065) ** 2) / (2.0 * 0.0015**2))
    check = vibration.check_double_hit(first + rebound, FS)
    assert check.passes
    same_shape_bound = 20.0 * math.log10(1.1 / 0.9)
    _, both = vibration.energy_spectral_density(first + rebound, FS)
    freqs, one = vibration.energy_spectral_density(first, FS)
    low = (freqs > 0.0) & (freqs <= 60.0)
    ratio_db = 10.0 * np.log10(both[low] / one[low])
    assert float(np.ptp(ratio_db)) > 2.0 * same_shape_bound


# ---------------------------------------------------------------------------
# Record checks.
# ---------------------------------------------------------------------------


def test_force_spectrum_drop_of_a_gaussian_pulse() -> None:
    """The ESD of a Gaussian falls by (2 pi f sigma)^2 / ln 10 * 10 dB at f."""
    force, _ = _sdof_impact(0.1)
    check = vibration.check_force_spectrum(
        force, FS, frequency_range_hz=(1.0, 500.0), max_drop_db=15.0
    )
    lowest = 1.0 * FS / N  # the first bin in the range is 1 Hz
    expected = (
        10.0
        * ((2.0 * math.pi * PULSE_SIGMA_S) ** 2)
        * (500.0**2 - lowest**2)
        / math.log(10.0)
    )
    assert check.drop_db == pytest.approx(expected, rel=1e-8)
    assert check.passes
    tight = vibration.check_force_spectrum(
        force, FS, frequency_range_hz=(1.0, 500.0), max_drop_db=expected - 0.01
    )
    assert not tight.passes
    at_the_limit = vibration.check_force_spectrum(
        force, FS, frequency_range_hz=(1.0, 500.0), max_drop_db=check.drop_db
    )
    assert at_the_limit.passes
    assert 0.0 < check.energy_fraction_above < 1.0


def test_a_double_hit_fails_the_force_spectrum_check() -> None:
    """6.4: multiple impacts are most easily detected in the frequency domain."""
    force, _ = _sdof_impact(0.1)
    double = force + np.roll(force, 256)
    check = vibration.check_force_spectrum(
        double, FS, frequency_range_hz=(1.0, 200.0), max_drop_db=20.0
    )
    assert not check.passes


def test_force_spectrum_range_above_nyquist_is_refused() -> None:
    force, _ = _sdof_impact(0.1)
    with pytest.raises(ValueError, match="Nyquist"):
        vibration.check_force_spectrum(
            force, FS, frequency_range_hz=(1.0, 5000.0), max_drop_db=10.0
        )


def test_overload_fails_at_the_full_scale_itself() -> None:
    record = np.sin(np.linspace(0.0, 20.0, 1000))
    peak = float(np.max(np.abs(record)))
    below = vibration.check_overload(record, FS, full_scale=peak * 1.0000001)
    at = vibration.check_overload(record, FS, full_scale=peak)
    assert below.passes
    assert not at.passes
    assert at.clipped_samples >= 1
    assert below.headroom_db == pytest.approx(20.0 * math.log10(1.0000001), abs=1e-9)


def _decay_to(end_ratio: float, frequency_hz: float = 200.0) -> NDArray[np.float64]:
    """A steady decay whose envelope is ``end_ratio`` at the last sample."""
    t = np.arange(N) / FS
    envelope = np.exp(math.log(end_ratio) * t / t[-1])
    return np.asarray(envelope * np.cos(2.0 * math.pi * frequency_hz * t))


@pytest.mark.parametrize("segment_s", [None, 0.01, 1.0 / 200.0])
def test_a_record_ending_at_one_per_cent_passes(segment_s: float | None) -> None:
    """8.3 and 8.5.2: about 1 % at the end and about 10 % at the midpoint."""
    record = _decay_to(RESPONSE_END_RATIO)
    check = vibration.check_response_decay(record, FS, segment_s=segment_s)
    assert check.end_ratio == pytest.approx(RESPONSE_END_RATIO, rel=0.02)
    assert check.midpoint_ratio == pytest.approx(RESPONSE_MIDPOINT_RATIO, rel=0.01)
    assert check.last_segment_ratio > check.end_ratio
    assert check.limit_ratio == RESPONSE_END_RATIO
    assert check.passes


def test_the_end_level_is_compared_to_a_whole_per_cent() -> None:
    """The "about 1 %" of 8.3 accepts any level below 1,5 %, which rounds to 1 %."""
    assert vibration.check_response_decay(_decay_to(0.014), FS).passes
    just_below = vibration.check_response_decay(_decay_to(0.0151), FS)
    assert 0.0149 < just_below.end_ratio < 0.015
    assert just_below.passes
    just_above = vibration.check_response_decay(_decay_to(0.0152), FS)
    assert 0.015 <= just_above.end_ratio < 0.0151
    assert not just_above.passes
    assert not vibration.check_response_decay(_decay_to(0.016), FS).passes
    windowed = vibration.check_response_decay(
        _decay_to(0.254), FS, exponential_window=True
    )
    assert windowed.passes
    too_slow = vibration.check_response_decay(
        _decay_to(0.26), FS, exponential_window=True
    )
    assert not too_slow.passes


def test_a_response_on_its_noise_floor_is_read_at_its_last_segment() -> None:
    """A flat end is not carried below the peak of the last segment."""
    rng = np.random.default_rng(7626)
    record = _decay_to(1e-8) + 0.004 * rng.standard_normal(N)
    check = vibration.check_response_decay(record, FS)
    assert check.end_ratio <= check.last_segment_ratio
    assert check.end_ratio >= 0.9 * check.last_segment_ratio


def test_response_decay_limits_with_and_without_a_window() -> None:
    record = _decay_to(0.2)
    assert not vibration.check_response_decay(record, FS).passes
    windowed = vibration.check_response_decay(record, FS, exponential_window=True)
    assert windowed.limit_ratio == WINDOWED_RESPONSE_END_RATIO
    assert windowed.passes


def test_the_force_record_leaves_the_mass_line_out_of_the_highest_peak() -> None:
    """A driving-point acceleration peaks at the impact itself (the mass line).

    Read as the clause words it, from the highest peak of the whole record,
    the decay passes 25 %; judged from after the pulse, on the free decay the
    guideline of 8.5.2 is about, it does not.
    """
    force, response = _sdof_impact(0.005)
    whole = vibration.check_response_decay(response, FS, exponential_window=True)
    assert whole.peak_time_s < 0.01  # the impact, 5 ms into the record
    assert whole.passes
    free = vibration.check_response_decay(
        response, FS, exponential_window=True, force=force
    )
    assert free.start_s > ref.ISO7626_5_PULSE_TIME_S
    assert free.peak < whole.peak
    assert free.end_ratio > WINDOWED_RESPONSE_END_RATIO
    assert not free.passes
    by_hand = vibration.check_response_decay(
        response, FS, exponential_window=True, start_s=0.02
    )
    assert not by_hand.passes
    later = vibration.check_response_decay(
        response, FS, exponential_window=True, force=force, start_s=0.02
    )
    assert later.start_s == pytest.approx(0.02)


def test_a_force_record_of_another_length_is_refused() -> None:
    force, response = _sdof_impact(0.005)
    short = force[: N // 2]
    with pytest.raises(ValueError, match="one length"):
        vibration.check_response_decay(response, FS, force=short)


def test_a_force_that_never_falls_back_is_refused() -> None:
    _, response = _sdof_impact(0.005)
    ramp = np.linspace(0.0, 1.0, N)
    with pytest.raises(ValueError, match="does not fall back"):
        vibration.check_response_decay(response, FS, force=ramp)


def test_response_decay_rejects_a_start_past_the_midpoint() -> None:
    _, response = _sdof_impact(0.005)
    with pytest.raises(ValueError, match="start_s"):
        vibration.check_response_decay(response, FS, start_s=0.6)


def test_a_silent_response_is_refused() -> None:
    """A dead channel ends at zero, but it has not decayed: it measured nothing.

    As check_double_hit refuses a force record without force.
    """
    silent = np.zeros(N)
    with pytest.raises(ValueError, match="holds no motion"):
        vibration.check_response_decay(silent, FS)
    late = np.zeros(N)
    late[0] = 1.0
    with pytest.raises(ValueError, match="no motion from 'start_s' on"):
        vibration.check_response_decay(late, FS, start_s=0.1)


def test_coherence_check_needs_high_coherence_and_enough_records() -> None:
    force, response = _sdof_impact(0.1)
    single = vibration.impact_mobility(force, response, FS)
    check = vibration.check_coherence(single, frequency_range_hz=(10.0, 200.0))
    assert np.all(check.high)
    assert not check.enough_records
    assert not check.passes
    records = vibration.impact_mobility(
        np.tile(force, (COHERENCE_RECORDS, 1)),
        np.tile(response, (COHERENCE_RECORDS, 1)),
        FS,
    )
    assert vibration.check_coherence(records, frequency_range_hz=(10.0, 200.0)).passes


def test_coherence_must_exceed_the_minimum_strictly() -> None:
    """9.1: high means greater than 0,9."""
    result = ImpactMobilityResult(
        frequencies=np.array([10.0, 20.0, 30.0]),
        mobility=np.ones(3, dtype=complex),
        coherence=np.array([HIGH_COHERENCE, 0.95, 0.99]),
        force_energy_spectral_density=np.ones(3),
        impacts=5,
    )
    check = vibration.check_coherence(result, frequency_range_hz=(5.0, 40.0))
    assert not check.passes
    excluded = vibration.check_coherence(
        result, frequency_range_hz=(5.0, 40.0), exclude_hz=[(8.0, 12.0)]
    )
    assert excluded.passes
    np.testing.assert_allclose(
        excluded.random_error_percent,
        vibration.random_error_percent(result.coherence, 5),
        rtol=1e-15,
    )


def test_exclusions_that_leave_nothing_to_judge_are_refused() -> None:
    """With no judged frequency the verdict would pass on no coherence at all."""
    force, response = _sdof_impact(0.1)
    records = vibration.impact_mobility(
        np.tile(force, (COHERENCE_RECORDS, 1)),
        np.tile(response, (COHERENCE_RECORDS, 1)),
        FS,
    )
    with pytest.raises(ValueError, match="covers every frequency"):
        vibration.check_coherence(
            records, frequency_range_hz=(10.0, 400.0), exclude_hz=[(0.0, 1000.0)]
        )
    check = vibration.check_coherence(records, frequency_range_hz=(10.0, 400.0))
    none_judged = np.zeros(check.frequencies.size, dtype=bool)
    with pytest.raises(ValueError, match="no frequency is judged"):
        vibration.CoherenceCheck(
            frequencies=check.frequencies,
            coherence=check.coherence,
            judged=none_judged,
            impacts=COHERENCE_RECORDS,
        )


@pytest.mark.parametrize("minimum_records", [5.9, True, 0, "5"])
def test_minimum_records_is_a_whole_number(minimum_records: object) -> None:
    """int() would read 5.9 as 5 and True as 1, and loosen the verdict."""
    force, response = _sdof_impact(0.1)
    records = vibration.impact_mobility(
        np.tile(force, (COHERENCE_RECORDS, 1)),
        np.tile(response, (COHERENCE_RECORDS, 1)),
        FS,
    )
    minimum = cast("Any", minimum_records)
    with pytest.raises(ValueError, match="minimum_records"):
        vibration.check_coherence(
            records, frequency_range_hz=(10.0, 400.0), minimum_records=minimum
        )


def test_a_whole_float_minimum_is_a_count() -> None:
    force, response = _sdof_impact(0.1)
    records = vibration.impact_mobility(
        np.tile(force, (COHERENCE_RECORDS, 1)),
        np.tile(response, (COHERENCE_RECORDS, 1)),
        FS,
    )
    check = vibration.check_coherence(
        records, frequency_range_hz=(10.0, 400.0), minimum_records=cast("Any", 5.0)
    )
    assert check.minimum_records == COHERENCE_RECORDS
    assert isinstance(check.minimum_records, int)
    not_a_count: Any = True
    with pytest.raises(ValueError, match="impacts"):
        vibration.CoherenceCheck(
            frequencies=check.frequencies,
            coherence=check.coherence,
            judged=check.judged,
            impacts=not_a_count,
        )


def test_channel_match_tolerances() -> None:
    """8.1: unity within +/- 5 % and zero phase within +/- 5 degrees."""
    freqs = np.linspace(10.0, 1000.0, 50)
    inside = (1.0 + 0.999 * CHANNEL_MAGNITUDE_TOLERANCE) * np.exp(
        1j * np.radians(0.999 * CHANNEL_PHASE_TOLERANCE_DEG)
    )
    assert vibration.verify_channel_match(
        freqs, np.full(50, inside), frequency_range_hz=(10.0, 1000.0)
    ).passes
    magnitude_out = vibration.verify_channel_match(
        freqs, np.full(50, 1.051 + 0j), frequency_range_hz=(10.0, 1000.0)
    )
    assert not magnitude_out.passes
    assert np.all(magnitude_out.phase_within)
    phase_out = vibration.verify_channel_match(
        freqs,
        np.full(50, np.exp(1j * np.radians(5.1))),
        frequency_range_hz=(10.0, 1000.0),
    )
    assert not phase_out.passes


@pytest.mark.parametrize(
    "response",
    [
        1.0 + CHANNEL_MAGNITUDE_TOLERANCE,
        1.0 - CHANNEL_MAGNITUDE_TOLERANCE,
        np.exp(1j * np.radians(CHANNEL_PHASE_TOLERANCE_DEG)),
        np.exp(-1j * np.radians(CHANNEL_PHASE_TOLERANCE_DEG)),
    ],
)
def test_the_channel_tolerances_include_their_bounds(response: complex) -> None:
    """8.1: "within +/- 5 %" and "within +/- 5 degrees" hold the bounds themselves."""
    freqs = np.array([100.0, 200.0])
    check = vibration.verify_channel_match(
        freqs, np.full(2, response, dtype=complex), frequency_range_hz=(50.0, 300.0)
    )
    assert check.passes


def test_channel_data_that_are_not_finite_are_refused_outside_the_range_too() -> None:
    """A NaN frequency drops out of the range selection, and a NaN response with it."""
    freqs = np.linspace(10.0, 1000.0, 100)
    unit = np.ones(100)
    holed_response = np.r_[np.ones(99), np.nan]
    with pytest.raises(ValueError, match="must be finite"):
        vibration.verify_channel_match(
            freqs, holed_response, frequency_range_hz=(10.0, 500.0)
        )
    holed = freqs.copy()
    holed[-1] = np.nan
    with pytest.raises(ValueError, match="must be finite"):
        vibration.verify_channel_match(holed, unit, frequency_range_hz=(10.0, 500.0))


@pytest.mark.parametrize(
    "build",
    [
        lambda f: vibration.check_double_hit(f, FS),
        lambda f: vibration.check_force_spectrum(
            f, FS, frequency_range_hz=(1.0, 200.0), max_drop_db=10.0
        ),
        lambda f: vibration.check_overload(f, FS, full_scale=1e3),
        lambda f: vibration.check_response_decay(f, FS),
        lambda f: vibration.verify_channel_match(
            np.array([1.0, 2.0]),
            np.ones(2, dtype=complex),
            frequency_range_hz=(0.5, 3.0),
        ),
    ],
)
def test_verdicts_have_no_truth_value(build: object) -> None:
    force, _ = _sdof_impact(0.1)
    verdict = build(force)  # type: ignore[operator]
    with pytest.raises(TypeError, match="no truth value"):
        bool(verdict)


def test_coherence_verdict_has_no_truth_value() -> None:
    force, response = _sdof_impact(0.1)
    check = vibration.check_coherence(
        vibration.impact_mobility(force, response, FS), frequency_range_hz=(10.0, 100.0)
    )
    with pytest.raises(TypeError, match="no truth value"):
        bool(check)


def test_published_constants_carry_the_printed_values() -> None:
    assert RESPONSE_END_RATIO == ref.ISO7626_5_RESPONSE_END_RATIO
    assert RESPONSE_MIDPOINT_RATIO == ref.ISO7626_5_RESPONSE_MIDPOINT_RATIO
    assert WINDOWED_RESPONSE_END_RATIO == ref.ISO7626_5_WINDOWED_END_RATIO
    assert HIGH_COHERENCE == ref.ISO7626_5_HIGH_COHERENCE
    assert COHERENCE_RECORDS == ref.ISO7626_5_COHERENCE_RECORDS
    assert CHANNEL_MAGNITUDE_TOLERANCE == ref.ISO7626_5_CHANNEL_MAGNITUDE
    assert CHANNEL_PHASE_TOLERANCE_DEG == ref.ISO7626_5_CHANNEL_PHASE_DEG


# ---------------------------------------------------------------------------
# Records as Signals: the rate comes along, the calibration factor does not.
# ---------------------------------------------------------------------------

#: A digital-to-pascal factor a Signal may carry; a force is not a pressure.
_CAL = 5.0


def test_a_signal_brings_its_rate_and_keeps_its_factor_out_of_the_force() -> None:
    force, response = _sdof_impact(0.1)
    bare = vibration.impact_mobility(force, response, FS)
    calibrated = vibration.impact_mobility(
        Signal(force, int(FS), calibration_factor=_CAL), response
    )
    np.testing.assert_array_equal(calibrated.mobility, bare.mobility)
    pre_scaled = vibration.impact_mobility(_CAL * force, response, FS)
    assert not np.allclose(pre_scaled.mobility, bare.mobility)


def test_a_signal_of_several_channels_is_one_impact_per_channel() -> None:
    force, response = _sdof_impact(0.1)
    forces = np.stack([force, 1.5 * force])
    responses = np.stack([response, 1.5 * response])
    rows = vibration.impact_mobility(forces, responses, FS)
    channels = vibration.impact_mobility(
        Signal(forces, int(FS)), Signal(responses, int(FS))
    )
    assert channels.impacts == 2
    np.testing.assert_array_equal(channels.mobility, rows.mobility)


def test_two_signals_at_different_rates_are_refused() -> None:
    force, response = _sdof_impact(0.1)
    force_signal = Signal(force, int(FS))
    response_signal = Signal(response, 2 * int(FS))
    with pytest.raises(ValueError, match="different rates"):
        vibration.impact_mobility(force_signal, response_signal)


def test_an_explicit_rate_that_disagrees_with_the_signal_is_refused() -> None:
    force, response = _sdof_impact(0.1)
    force_signal = Signal(force, int(FS))
    with pytest.raises(ValueError, match="conflicts with the Signal's own fs"):
        vibration.impact_mobility(force_signal, response, FS + 1.0)


def test_bare_records_without_a_rate_are_refused() -> None:
    force, response = _sdof_impact(0.1)
    with pytest.raises(ValueError, match="fs is required when 'force'"):
        vibration.impact_mobility(force, response)


def test_a_check_keeps_the_samples_it_judged_as_a_bare_array() -> None:
    force, response = _sdof_impact(0.1)
    double = vibration.check_double_hit(Signal(force, int(FS), calibration_factor=_CAL))
    overload = vibration.check_overload(
        Signal(force, int(FS), calibration_factor=_CAL), full_scale=2.0 * PEAK_N
    )
    decay = vibration.check_response_decay(
        Signal(response, int(FS), calibration_factor=_CAL)
    )
    for kept, record in (
        (double.force, force),
        (overload.record, force),
        (decay.record, response),
    ):
        assert type(kept) is np.ndarray
        np.testing.assert_array_equal(kept, record)
    assert overload.fs == FS


# ---------------------------------------------------------------------------
# Figures and the fiche.
# ---------------------------------------------------------------------------


def test_spanish_labels_on_the_impact_figures() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    force, response = _sdof_impact(0.005)
    res = vibration.impact_mobility(
        force, response, FS, exponential_decay_rate_per_s=20.0
    )
    axes = np.asarray(res.plot(language="es"))
    title = axes[0].get_title()
    assert title.startswith("ISO 7626-5 movilidad por excitación con impacto")
    assert axes[1].get_xlabel() == "Frecuencia [Hz]"
    fit_ax = res.fit_mode((30.0, 50.0)).plot(language="es")
    assert fit_ax.get_title().startswith("Ajuste de un modo en 40,")
    double = vibration.check_double_hit(force + np.roll(force, 245), FS)
    check_axes = np.asarray(double.plot(language="es"))
    assert check_axes[0].get_title().endswith("(NO CUMPLE)")
    plt.close("all")


def _figure_width_px(axes: object) -> tuple[Figure, float]:
    """The figure a renderer drew *axes* on, drawn, and its width in pixels."""
    first = cast("Axes", np.asarray(axes).ravel()[0])
    figure = cast("Figure", first.get_figure(root=True))
    figure.canvas.draw()
    return figure, float(figure.bbox.width)


def _impact_verdicts() -> list[Any]:
    """Every ISO 7626-5 verdict, once passing and once failing."""
    force, response = _sdof_impact(0.005)
    single = vibration.impact_mobility(force, response, FS)
    five = vibration.impact_mobility(
        np.tile(force, (5, 1)), np.tile(response, (5, 1)), FS
    )
    freqs = np.linspace(10.0, 1000.0, 50)
    double = force + 0.6 * np.roll(force, 245)
    return [
        vibration.check_double_hit(force, FS),
        vibration.check_double_hit(double, FS),
        vibration.check_force_spectrum(
            force, FS, frequency_range_hz=(1.0, 400.0), max_drop_db=20.0
        ),
        vibration.check_force_spectrum(
            double, FS, frequency_range_hz=(1.0, 400.0), max_drop_db=3.0
        ),
        vibration.check_overload(force, FS, full_scale=2.0 * PEAK_N),
        vibration.check_overload(force, FS, full_scale=0.5 * PEAK_N),
        vibration.check_response_decay(_decay_to(0.2), FS, exponential_window=True),
        vibration.check_response_decay(_decay_to(0.4), FS, exponential_window=True),
        vibration.check_response_decay(_decay_to(0.01), FS),
        vibration.check_response_decay(_decay_to(0.2), FS),
        vibration.check_coherence(five, frequency_range_hz=(10.0, 400.0)),
        vibration.check_coherence(single, frequency_range_hz=(10.0, 400.0)),
        vibration.verify_channel_match(
            freqs, np.ones(50, dtype=complex), frequency_range_hz=(10.0, 1000.0)
        ),
        vibration.verify_channel_match(
            freqs, np.full(50, 1.2 + 0j), frequency_range_hz=(10.0, 1000.0)
        ),
    ]


@pytest.mark.parametrize("language", ["en", "es"])
def test_every_impact_verdict_title_fits_its_figure(language: str) -> None:
    """A title and its verdict word stay on the canvas in both languages."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    for verdict in _impact_verdicts():
        figure, width = _figure_width_px(verdict.plot(language=language))
        for axis in figure.axes:
            if axis.get_title():
                extent = axis.title.get_window_extent()
                assert extent.x0 >= 0.0, axis.get_title()
                assert extent.x1 <= width, axis.get_title()
        plt.close("all")


def test_the_decay_figure_marks_the_readings_where_the_check_takes_them() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    check = vibration.check_response_decay(_decay_to(0.01), FS)
    ax = check.plot()
    segment = round(check.segment_s * FS)
    steps = ax.get_lines()[1]
    edges = np.asarray(steps.get_xdata(), dtype=float)
    assert edges[-1] == pytest.approx(N / FS)
    assert edges[-2] == pytest.approx((N - segment) / FS)
    end = ax.get_lines()[-1]
    assert float(np.asarray(end.get_xdata())[0]) == pytest.approx((N - 1) / FS)
    assert float(np.asarray(end.get_ydata())[0]) == pytest.approx(
        20.0 * math.log10(check.end_ratio)
    )
    plt.close("all")


def test_the_channel_figure_holds_every_deviation() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    freqs = np.arange(1.0, 1001.0, 5.0)
    response = (1.0 + 0.2 * freqs / 1000.0) * np.exp(
        1j * np.radians(20.0 * freqs / 1000.0)
    )
    check = vibration.verify_channel_match(
        freqs, response, frequency_range_hz=(20.0, 800.0)
    )
    magnitude_ax, phase_ax = np.asarray(check.plot())
    low, high = magnitude_ax.get_ylim()
    assert high >= 100.0 * float(np.max(np.abs(check.magnitude_deviation)))
    assert low <= -high + 1e-9
    assert phase_ax.get_ylim()[1] >= float(np.max(np.abs(check.phase_deg)))
    plt.close("all")


def test_a_single_impact_is_not_called_an_average() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    from phonometry._report.iso7626 import _impact_basis

    force, response = _sdof_impact(0.1)
    single = vibration.impact_mobility(
        force, response, FS, frequency_range_hz=(5.0, 400.0)
    )
    for language, word in (("en", "single impact"), ("es", "un solo impacto")):
        axes = np.asarray(single.plot(language=language))
        labels = axes[0].get_legend_handles_labels()[1]
        assert any(word in label for label in labels)
        coherence = vibration.check_coherence(single, frequency_range_hz=(10.0, 400.0))
        assert word in coherence.plot(language=language).get_title()
        assert word in _impact_basis(single, language)
        plt.close("all")


def test_report_names_iso_7626_5(tmp_path: Path) -> None:
    pytest.importorskip("reportlab")
    pytest.importorskip("matplotlib")
    from pypdf import PdfReader

    force, response = _sdof_impact(0.1)
    res = vibration.impact_mobility(
        np.tile(force, (3, 1)),
        np.tile(response, (3, 1)),
        FS,
        exponential_decay_rate_per_s=5.0,
    )
    out = tmp_path / "impact.pdf"
    assert res.report(str(out)) == str(out)
    text = " ".join(
        " ".join(p.extract_text() for p in PdfReader(str(out)).pages).split()
    )
    assert "ISO 7626-5:2019" in text
    assert "Impacts averaged" in text
    assert "5.0" in text


def test_sdof_accelerance_helper_agrees_with_the_simulated_record() -> None:
    """The simulator itself: its accelerance is the module's closed form."""
    zeta = 0.1
    force, response = _sdof_impact(zeta)
    res = vibration.impact_mobility(force, response, FS)
    band = _band(res.frequencies)
    expected = sdof_accelerance(
        res.frequencies[band],
        MASS_KG,
        _stiffness(MASS_KG, F_N_HZ),
        _damping(MASS_KG, F_N_HZ, zeta),
    )
    np.testing.assert_allclose(res.to("accelerance")[band], expected, rtol=1e-7)
