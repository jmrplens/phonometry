#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 60118-4:2014 with Amendment 1:2017: an installed induction-loop system."""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import TYPE_CHECKING

import numpy as np
import pytest
import reference_data as ref
from scipy import signal

import phonometry as ph

if TYPE_CHECKING:
    from collections.abc import Callable

ea = ph.electroacoustics
FS = 48000


# ---------------------------------------------------------------------------
# Levels, units and the telecoil
# ---------------------------------------------------------------------------


def test_reference_is_400_milliamperes_per_metre() -> None:
    assert ea.REFERENCE_FIELD_STRENGTH_A_PER_M == pytest.approx(
        ref.IEC60118_4_REFERENCE_A_PER_M
    )
    assert ea.field_strength_level(0.4) == pytest.approx(0.0, abs=1e-12)


def test_long_term_level_of_clause_4_3_is_100_milliamperes_per_metre() -> None:
    level = float(ea.field_strength_level(ref.IEC60118_4_LONG_TERM_A_PER_M))
    assert level == pytest.approx(ref.IEC60118_4_LONG_TERM_LEVEL_DB, abs=0.05)
    assert float(ea.field_strength(level)) == pytest.approx(0.1, rel=1e-12)


def test_commissioning_window_spans_283_to_565_milliamperes_per_metre() -> None:
    low, high = ea.field_strength([-3.0, 3.0]) * 1e3
    assert low == pytest.approx(ref.IEC60118_4_A1_COMMISSIONING_MA_PER_M[0], abs=0.5)
    # 10.2 prints 566, which is 400 sqrt(2); +3 dB is 565.0.
    assert high == pytest.approx(565.015, abs=1e-3)
    assert 400.0 * math.sqrt(2.0) == pytest.approx(
        ref.IEC60118_4_A1_COMMISSIONING_MA_PER_M[1], abs=0.5
    )


def test_field_strength_level_refuses_a_non_positive_field() -> None:
    with pytest.raises(ValueError, match="field_strength_a_per_m"):
        ea.field_strength_level([0.4, 0.0])


def test_field_strength_refuses_a_nan_level() -> None:
    with pytest.raises(ValueError, match="level_db"):
        ea.field_strength(math.nan)


@pytest.mark.parametrize(
    ("call", "name"),
    [
        (
            lambda: ea.field_strength_level(np.array([0.4 + 0.1j])),
            "field_strength_a_per_m",
        ),
        (lambda: ea.field_strength_level("a"), "field_strength_a_per_m"),
        (lambda: ea.field_strength(np.array([1.0j])), "level_db"),
        (lambda: ea.magnetic_flux_density(np.array([1.0j])), "field_strength_a_per_m"),
        (lambda: ea.telecoil_response(np.array([45.0 + 1.0j])), "angle_deg"),
        (
            lambda: ea.verify_induction_loop_system(np.array([5.0j, 0.0j])),
            "field_strength_levels_db",
        ),
        (
            lambda: ea.verify_small_volume_system(
                np.full((3, 3), 9.0j), layout="counter"
            ),
            "field_strength_levels_db",
        ),
        (
            lambda: ea.verify_small_volume_system(
                [0.0, 0.0],
                layout="refuge_useful_volume",
                heights_m=np.array([1.2 + 1.0j, 1.7]),
            ),
            "heights_m",
        ),
        (
            lambda: ea.verify_small_volume_system(
                np.zeros((3, 3)),
                layout="counter",
                standing_area_levels_db=np.array([9.0j]),
            ),
            "standing_area_levels_db",
        ),
        (
            lambda: ea.verify_induction_loop_system(
                [0.0],
                frequencies_hz=[100.0, 1000.0, 5000.0],
                response_db=np.array([0.0, 0.0, 1.0j]),
            ),
            "response_db",
        ),
    ],
)
def test_complex_or_text_input_is_refused_by_name(
    call: Callable[[], object], name: str
) -> None:
    # A complex array converted to float64 would drop its imaginary part with
    # only a warning and go on to a verdict.
    with pytest.raises(ValueError, match=f"'{name}' must be (real|numeric)"):
        call()


def test_flux_density_of_one_ampere_per_metre() -> None:
    microtesla = float(ea.magnetic_flux_density(1.0)) * 1e6
    assert microtesla == pytest.approx(4.0 * math.pi / 10.0, rel=1e-12)
    # E.6 prints 1,256, the last digit truncated rather than rounded.
    assert round(microtesla, 3) == pytest.approx(1.257)
    assert microtesla == pytest.approx(
        ref.IEC60118_4_E6_MICROTESLA_PER_A_PER_M, abs=1e-3
    )


def test_one_oersted_in_amperes_per_metre() -> None:
    oersted = 1e-4 / float(ea.magnetic_flux_density(1.0))
    assert oersted == pytest.approx(ref.IEC60118_4_E6_OERSTED_A_PER_M, abs=0.005)


@pytest.mark.parametrize(
    ("angle", "printed"), sorted(ref.IEC60118_4_TELECOIL_DB.items())
)
def test_telecoil_cosine_law(angle: float, printed: float) -> None:
    assert float(ea.telecoil_response(angle)) == pytest.approx(printed, abs=0.05)


def test_telecoil_nulls_at_right_angles() -> None:
    # At right angles a telecoil picks up nothing: minus infinity, not the
    # -324 dB that the cosine of a rounded pi/2 would leave.
    response = ea.telecoil_response([0.0, 90.0, 180.0, 270.0, -90.0])
    assert response[0] == pytest.approx(0.0, abs=1e-12)
    assert response[2] == pytest.approx(0.0, abs=1e-12)
    for null in response[[1, 3, 4]]:
        assert math.isinf(null)
        assert null < 0.0


# ---------------------------------------------------------------------------
# The meter
# ---------------------------------------------------------------------------


def _sine(level_db: float, frequency_hz: float, seconds: float = 2.0) -> np.ndarray:
    t = np.arange(round(seconds * FS)) / FS
    amplitude = float(ea.field_strength(level_db)) * math.sqrt(2.0)
    return amplitude * np.sin(2.0 * np.pi * frequency_hz * t)


def test_meter_reads_a_sine_at_its_level() -> None:
    reading = ea.field_strength_meter(_sine(-6.0, 1000.0), FS)
    assert reading.maximum_db == pytest.approx(-6.0, abs=0.01)
    assert reading.equivalent_db == pytest.approx(-6.0, abs=1e-6)
    assert reading.weighting == "Z"
    assert reading.levels_db.shape == reading.times_s.shape


def test_meter_a_weighting_is_transparent_at_1_khz_and_19_db_down_at_100_hz() -> None:
    at_1k = ea.field_strength_meter(_sine(0.0, 1000.0), FS, weighting="A")
    at_100 = ea.field_strength_meter(_sine(0.0, 100.0), FS, weighting="A")
    assert at_1k.maximum_db == pytest.approx(0.0, abs=0.02)
    assert at_100.equivalent_db == pytest.approx(-19.1, abs=0.1)


def test_meter_levels_are_read_only() -> None:
    reading = ea.field_strength_meter(_sine(0.0, 1000.0, seconds=0.5), FS)
    with pytest.raises(ValueError, match="read-only"):
        reading.levels_db[0] = 0.0


def test_meter_refuses_a_silent_record() -> None:
    silence = np.zeros(1000)
    with pytest.raises(ValueError, match="silent"):
        ea.field_strength_meter(silence, FS)


def test_meter_refuses_an_unknown_weighting() -> None:
    record = _sine(0.0, 1000.0, seconds=0.1)
    with pytest.raises(ValueError, match="weighting"):
        ea.field_strength_meter(record, FS, weighting="C")


# ---------------------------------------------------------------------------
# Test signals
# ---------------------------------------------------------------------------


def test_band_limit_response_is_the_printed_pair_exchanged() -> None:
    at_100, at_5k = ea.band_limit_response([100.0, 5000.0])
    assert at_100 == pytest.approx(
        ref.IEC60118_4_BAND_LIMIT_COMPUTED_DB[100.0], abs=5e-4
    )
    assert at_5k == pytest.approx(
        ref.IEC60118_4_BAND_LIMIT_COMPUTED_DB[5000.0], abs=5e-4
    )
    printed = ref.IEC60118_4_BAND_LIMIT_PRINTED_DB
    # Rounded to the one decimal NOTE 2 prints, the two values swap places.
    assert round(at_100, 1) == pytest.approx(printed[5000.0])
    assert round(at_5k, 1) == pytest.approx(printed[100.0])


def test_band_limit_is_3_db_down_at_its_corners() -> None:
    low, high = ea.band_limit_response(list(ref.IEC60118_4_BAND_LIMIT_HZ))
    assert low == pytest.approx(-3.0103, abs=1e-3)
    assert high == pytest.approx(-3.0103, abs=1e-3)


def test_band_limit_matches_the_scipy_butterworth_prototypes() -> None:
    f = np.array([60.0, 100.0, 1000.0, 5000.0, 8000.0])
    hp = signal.butter(3, 2 * np.pi * 75.0, "highpass", analog=True)
    lp = signal.butter(3, 2 * np.pi * 6500.0, "lowpass", analog=True)
    _, h1 = signal.freqs(*hp, worN=2 * np.pi * f)
    _, h2 = signal.freqs(*lp, worN=2 * np.pi * f)
    np.testing.assert_allclose(
        ea.band_limit_response(f), 20 * np.log10(np.abs(h1 * h2)), atol=1e-9
    )


def _band_levels(x: np.ndarray, centres: list[float]) -> np.ndarray:
    f, p = signal.welch(x, FS, nperseg=1 << 15)
    out = []
    for c in centres:
        band = (f >= c * 2 ** (-1 / 6)) & (f < c * 2 ** (1 / 6))
        out.append(10 * np.log10(np.trapezoid(p[band], f[band])))
    return np.array(out)


def test_pink_noise_is_flat_within_1_db_from_100_hz_to_5_khz() -> None:
    x = ea.loop_test_noise(FS, 30.0, seed=7)
    centres = [100.0, 200.0, 400.0, 1000.0, 2000.0, 4000.0, 5000.0]
    levels = _band_levels(x, centres)
    assert np.max(np.abs(levels - levels[3])) < 1.0


def test_pink_noise_has_crest_factor_4_and_the_peak_to_peak_ratio() -> None:
    x = ea.loop_test_noise(FS, 30.0, rms=0.25, seed=11)
    rms = math.sqrt(float(np.mean(x * x)))
    assert rms == pytest.approx(0.25, rel=1e-12)
    assert float(np.max(np.abs(x))) / rms == pytest.approx(4.0, abs=1e-3)
    ratio = 20 * math.log10(float(np.max(x) - np.min(x)) / rms)
    assert ratio >= ref.IEC60118_4_NOISE_PEAK_TO_PEAK_DB
    assert abs(ratio - 18.0) <= ref.IEC62489_1_NOISE_PEAK_TO_PEAK_TOL_DB


def test_pink_noise_is_reproducible_from_its_seed() -> None:
    a = ea.loop_test_noise(FS, 1.0, seed=3)
    b = ea.loop_test_noise(FS, 1.0, seed=3)
    np.testing.assert_array_equal(a, b)


def test_pink_noise_refuses_a_rate_below_the_low_pass() -> None:
    with pytest.raises(ValueError, match="fs"):
        ea.loop_test_noise(8000, 1.0)


def test_pink_noise_refuses_a_duration_shorter_than_one_sample() -> None:
    with pytest.raises(ValueError, match="shorter than one sample"):
        ea.loop_test_noise(FS, 1.0e-6)


def test_combi_signal_levels_and_durations() -> None:
    x = ea.combi_signal(FS, sine_seconds=1.0, noise_seconds=4.0, cycles=2, seed=5)
    n_sine = FS
    ramp = round(ref.IEC60118_4_COMBI_RAMP_MS * 1e-3 * FS)
    burst = x[ramp : n_sine - ramp]
    assert math.sqrt(float(np.mean(burst * burst))) == pytest.approx(1.0, abs=0.01)
    noise = x[n_sine : n_sine + 4 * FS]
    noise_db = 20 * math.log10(math.sqrt(float(np.mean(noise * noise))))
    assert noise_db == pytest.approx(ref.IEC60118_4_COMBI_NOISE_RELATIVE_DB, abs=0.1)
    assert x.size / FS == pytest.approx(10.0, abs=0.01)
    assert x[0] == pytest.approx(0.0, abs=1e-12)


def test_combi_sine_peaks_sit_3_db_below_the_noise_peaks() -> None:
    peak_ratio_db = 20 * math.log10(
        math.sqrt(2.0) / (4.0 * 10 ** (ref.IEC60118_4_COMBI_NOISE_RELATIVE_DB / 20.0))
    )
    assert -peak_ratio_db == pytest.approx(
        ref.IEC60118_4_COMBI_SINE_PEAK_BELOW_NOISE_PEAK_DB, abs=0.05
    )
    x = ea.combi_signal(FS, seed=9)
    sine_peak = float(np.max(np.abs(x[:FS])))
    noise_peak = float(np.max(np.abs(x[FS:])))
    assert 20 * math.log10(sine_peak / noise_peak) == pytest.approx(
        peak_ratio_db, abs=0.02
    )


def test_combi_transitions_are_near_zero_crossings() -> None:
    x = ea.combi_signal(FS, cycles=2, seed=4)
    # The burst ramps to zero; the noise starts at the sample nearest its
    # first crossing, which lies within one sample step of zero.
    step = float(np.max(np.abs(np.diff(x[FS:]))))
    assert abs(x[FS - 1]) < 1e-3
    assert abs(x[FS]) <= step


def test_combi_refuses_too_short_a_burst() -> None:
    with pytest.raises(ValueError, match="Table 2"):
        ea.combi_signal(FS, sine_seconds=0.5)


def test_combi_refuses_less_than_four_times_the_noise() -> None:
    with pytest.raises(ValueError, match="at least 4 times"):
        ea.combi_signal(FS, sine_seconds=2.0, noise_seconds=5.0)


@pytest.mark.parametrize(("sine", "noise"), [(1.2496, 4.9984), (2.4995, 9.998)])
def test_combi_keeps_four_times_the_noise_once_the_sine_is_rounded(
    sine: float, noise: float
) -> None:
    # 1,2496 s of sine rounds up to 1 250 whole periods, 1,25 s, and 4,9984 s
    # of noise would leave a ratio of 3,999: Table 2 says the ratio of 4:1
    # shall not be reduced.
    x = ea.combi_signal(FS, sine_seconds=sine, noise_seconds=noise, seed=1)
    n_sine = round(round(sine * 1000.0) * FS / 1000.0)
    assert n_sine > sine * FS
    assert x.size - n_sine >= 4 * n_sine


# ---------------------------------------------------------------------------
# Measurement points of small-volume systems
# ---------------------------------------------------------------------------


def test_refuge_small_source_points_sit_on_the_two_radii() -> None:
    points = ea.small_volume_measurement_points("refuge_small")
    assert points.shape == (2, 6, 3)
    radii = np.hypot(points[0, :, 0], points[0, :, 1]) * 1e3
    np.testing.assert_allclose(radii[:3], ref.IEC60118_4_A1_FIGURE2A_MM["inner_radius"])
    np.testing.assert_allclose(radii[3:], ref.IEC60118_4_A1_FIGURE2A_MM["outer_radius"])
    angles = np.degrees(np.arctan2(points[0, :3, 0], points[0, :3, 1]))
    np.testing.assert_allclose(angles, [-45.0, 0.0, 45.0], atol=1e-9)
    np.testing.assert_allclose(points[:, 0, 2], ref.IEC60118_4_A1_REFUGE_HEIGHTS_M)


def test_refuge_large_source_rows() -> None:
    points = ea.small_volume_measurement_points("refuge_large")
    dims = ref.IEC60118_4_A1_FIGURE2B_MM
    near, far = points[0, :3], points[0, 3:]
    assert np.ptp(near[:, 0]) * 1e3 == pytest.approx(dims["l4"])
    assert np.ptp(far[:, 0]) * 1e3 == pytest.approx(dims["l5"])
    np.testing.assert_allclose(near[:, 1] * 1e3, dims["l2"])
    np.testing.assert_allclose(far[:, 1] * 1e3, dims["l2"] + dims["l3"])


def test_counter_points_on_the_semicircle_at_three_heights() -> None:
    points = ea.small_volume_measurement_points("counter")
    assert points.shape == (3, 3, 3)
    dims = ref.IEC60118_4_A1_FIGURE3_MM
    np.testing.assert_allclose(
        np.hypot(points[0, :, 0], points[0, :, 1]) * 1e3, dims["radius"]
    )
    np.testing.assert_allclose(
        points[0, :, 0] * 1e3, [-dims["lateral"], 0.0, dims["lateral"]]
    )
    np.testing.assert_allclose(points[:, 0, 2], ref.IEC60118_4_A1_COUNTER_HEIGHTS_M)


def test_measurement_points_are_read_only() -> None:
    points = ea.small_volume_measurement_points("counter")
    with pytest.raises(ValueError, match="read-only"):
        points[0, 0, 0] = 1.0


def test_measurement_points_refuse_an_unknown_layout() -> None:
    with pytest.raises(ValueError, match="layout"):
        ea.small_volume_measurement_points("kiosk")


# ---------------------------------------------------------------------------
# Background noise (7.2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("worst_db", "category", "report"),
    [
        (-47.01, "ideal", False),
        (-47.0, "acceptable", False),
        (-32.0, "acceptable", False),
        (-31.99, "tolerable_for_short_periods", True),
        (-22.0, "tolerable_for_short_periods", True),
        (-21.99, "below_tolerable", True),
    ],
)
def test_background_noise_categories_at_the_boundaries(
    worst_db: float,
    category: str,
    report: bool,  # noqa: FBT001
) -> None:
    result = ea.assess_background_noise([-60.0, worst_db, -55.0])
    assert result.category == category
    assert result.report_required is report
    assert result.reference_signal_to_noise_ratio_db == pytest.approx(-worst_db)


def test_tonal_noise_withholds_the_22_db_relaxation() -> None:
    result = ea.assess_background_noise([-25.0], noise_is_tonal=True)
    assert result.category == "below_tolerable"
    assert result.noise_is_tonal is True


def test_background_noise_thresholds_are_the_printed_ones() -> None:
    ideal = ea.assess_background_noise([-ref.IEC60118_4_SNR_IDEAL_DB - 0.1])
    minimum = ea.assess_background_noise([-ref.IEC60118_4_SNR_MINIMUM_DB])
    short = ea.assess_background_noise([-ref.IEC60118_4_SNR_SHORT_PERIODS_DB])
    assert (ideal.category, minimum.category, short.category) == (
        "ideal",
        "acceptable",
        "tolerable_for_short_periods",
    )


# ---------------------------------------------------------------------------
# The system verdict (clause 8 and 10.4)
# ---------------------------------------------------------------------------

_F = [100.0, 1000.0, 5000.0]


def test_field_strength_within_3_db_passes_and_the_edges_are_inclusive() -> None:
    result = ea.verify_induction_loop_system([-3.0, 0.0, 3.0])
    assert result.passes
    assert result.requirement("field_strength").worst_margin_db == pytest.approx(0.0)


def test_field_strength_outside_3_db_fails() -> None:
    result = ea.verify_induction_loop_system([0.0, 3.1])
    assert not result.passes
    assert result.failed == ("field_strength",)
    assert result.requirement("field_strength").worst_margin_db == pytest.approx(-0.1)


def test_specified_level_moves_the_window() -> None:
    # Pink noise on the RMS meter reads -6 dB for 400 mA/m (Table 3).
    specified = ref.IEC60118_4_TABLE3["pink_noise"][0]
    result = ea.verify_induction_loop_system([-8.0, -4.0], specified_level_db=specified)
    assert result.passes
    assert result.requirement("field_strength_reached").lower_db == (specified,)


def test_clause_8_judges_the_window_and_the_maximum() -> None:
    result = ea.verify_induction_loop_system([0.0, -1.5])
    assert [r.name for r in result.requirements] == [
        "field_strength",
        "field_strength_reached",
    ]
    reached = result.requirement("field_strength_reached")
    assert reached.clause == "8.2.7"
    assert reached.values_db == (0.0,)
    assert reached.upper_db == (math.inf,)


def test_a_spread_wholly_below_400_ma_per_m_fails_8_2_7() -> None:
    # Inside the 3 dB window everywhere, but the maximum never reaches the
    # 400 mA/m that 8.2.7 sets at one point at least of the useful volume.
    result = ea.verify_induction_loop_system([-3.0, -2.5, -0.01])
    assert result.failed == ("field_strength_reached",)
    assert result.requirement("field_strength_reached").worst_margin_db == (
        pytest.approx(-0.01)
    )


def test_specified_level_moves_the_8_2_7_maximum_too() -> None:
    result = ea.verify_induction_loop_system([-8.5, -6.5], specified_level_db=-6.0)
    assert result.failed == ("field_strength_reached",)


def test_frequency_response_is_normalized_to_1_khz_per_point() -> None:
    result = ea.verify_induction_loop_system(
        [0.0],
        frequencies_hz=_F,
        response_db=[[10.0, 12.0, 9.0], [-5.0, -5.0, -8.0]],
    )
    req = result.requirement("frequency_response")
    assert req.values_db == pytest.approx((-2.0, 0.0, -3.0, 0.0, 0.0, -3.0))
    assert req.passes


def test_frequency_response_outside_the_band_is_not_judged() -> None:
    result = ea.verify_induction_loop_system(
        [0.0],
        frequencies_hz=[50.0, 100.0, 1000.0, 5000.0, 8000.0],
        response_db=[-20.0, 0.0, 0.0, -1.0, -30.0],
    )
    assert result.passes
    assert len(result.requirement("frequency_response").values_db) == 3


def test_frequency_response_beyond_3_db_fails() -> None:
    result = ea.verify_induction_loop_system(
        [0.0], frequencies_hz=_F, response_db=[0.0, 0.0, -3.5]
    )
    assert result.failed == ("frequency_response",)


def test_frequency_response_needs_100_hz_1_khz_and_5_khz() -> None:
    frequencies = [125.0, 1000.0, 5000.0]
    response = [0.0, 0.0, 0.0]
    with pytest.raises(ValueError, match="100 Hz"):
        ea.verify_induction_loop_system(
            [0.0], frequencies_hz=frequencies, response_db=response
        )


def test_frequency_response_needs_1_khz_exactly_once() -> None:
    # The response is normalized to the one at 1 kHz; two of them leave the
    # reference ambiguous.
    with pytest.raises(ValueError, match="1000 Hz exactly once"):
        ea.verify_induction_loop_system(
            [0.0],
            frequencies_hz=[100.0, 1000.0, 1000.0, 5000.0],
            response_db=[[0.0, 0.0, 5.0, 0.0]],
        )


def test_frequencies_and_response_go_together() -> None:
    with pytest.raises(ValueError, match="go together"):
        ea.verify_induction_loop_system([0.0], frequencies_hz=_F)


def test_system_noise_on_a_quiet_site_is_held_to_minus_47_db() -> None:
    result = ea.verify_induction_loop_system(
        [0.0],
        background_noise_levels_db=[-55.0, -50.0],
        system_noise_levels_db=[-47.0, -48.0],
    )
    req = result.requirement("system_noise")
    assert req.upper_db == (-47.0, -47.0)
    assert req.passes
    assert result.background_noise is not None
    assert result.background_noise.category == "ideal"


def test_system_noise_on_a_noisier_site_may_rise_by_1_db() -> None:
    result = ea.verify_induction_loop_system(
        [0.0],
        background_noise_levels_db=[-40.0, -45.0],
        system_noise_levels_db=[-39.0, -43.9],
    )
    req = result.requirement("system_noise")
    assert req.upper_db == pytest.approx((-39.0, -44.0))
    assert req.values_db[1] > req.upper_db[1]
    assert result.failed == ("system_noise",)


def test_system_noise_at_exactly_47_db_uses_the_1_db_rule() -> None:
    result = ea.verify_induction_loop_system(
        [0.0],
        background_noise_levels_db=[-47.0],
        system_noise_levels_db=[-46.0],
    )
    assert result.requirement("system_noise").upper_db == pytest.approx((-46.0,))
    assert result.passes


# The windows of 8.3.7 ("within the range +/-3 dB"), 8.4.3 ("within +/-3 dB")
# and 10.4.7 ("shall not exceed ... by more than 1 dB") hold their edges, and
# an edge reached from decimal readings is on the window, not one unit in the
# last place outside it.


def test_response_exactly_3_db_from_1_khz_is_on_the_edge() -> None:
    # -18,6 - (-15,6) is -3,000 000 000 000 001 8 in binary, and -31,7 - (-34,7)
    # is +3,000 000 000 000 003 6.
    result = ea.verify_induction_loop_system(
        [0.0],
        frequencies_hz=_F,
        response_db=[[-18.6, -15.6, -15.6], [-34.7, -34.7, -31.7]],
    )
    requirement = result.requirement("frequency_response")
    assert requirement.passes
    assert requirement.worst_margin_db == 0.0
    assert result.passes


def test_field_strength_3_db_from_a_specified_level_is_on_the_edge() -> None:
    # A meter that reads 400 mA/m as -5,9 dB: -5,9 + 3 is
    # -2,900 000 000 000 000 4 in binary, below the reading of -2,9 dB.
    result = ea.verify_induction_loop_system([-8.9, -2.9], specified_level_db=-5.9)
    assert result.requirement("field_strength").worst_margin_db == 0.0
    assert result.passes


def test_system_noise_exactly_1_db_up_is_on_the_edge() -> None:
    # A site at a reference signal-to-noise ratio of 32,7 dB: -32,7 + 1 is
    # -31,700 000 000 000 003 in binary, below the reading of -31,7 dB.
    result = ea.verify_induction_loop_system(
        [0.0], background_noise_levels_db=[-32.7], system_noise_levels_db=[-31.7]
    )
    assert result.requirement("system_noise").worst_margin_db == 0.0
    assert result.passes


def test_a_small_volume_response_on_the_edge_passes() -> None:
    response = np.tile([-18.6, -15.6, -15.6], (9, 1))
    result = ea.verify_small_volume_system(
        np.zeros((3, 3)), layout="counter", frequencies_hz=_F, response_db=response
    )
    assert result.requirement("frequency_response").passes


def test_requirement_plot_marks_no_failure_on_the_edge() -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    requirement = ea.verify_induction_loop_system(
        [0.0], frequencies_hz=_F, response_db=[-18.6, -15.6, -15.6]
    ).requirement("frequency_response")
    ax = requirement.plot()
    assert not [line for line in ax.lines if line.get_marker() == "x"]
    assert _title_verdict(ax.get_title()) == "pass"
    plt.close("all")


def test_system_noise_needs_the_background() -> None:
    with pytest.raises(ValueError, match="background_noise_levels_db"):
        ea.verify_induction_loop_system([0.0], system_noise_levels_db=[-50.0])


def test_system_noise_pairs_point_by_point() -> None:
    with pytest.raises(ValueError, match="point by point"):
        ea.verify_induction_loop_system(
            [0.0],
            background_noise_levels_db=[-50.0, -50.0],
            system_noise_levels_db=[-50.0],
        )


def test_tonal_background_noise_is_forwarded_to_the_7_2_class() -> None:
    plain = ea.verify_induction_loop_system(
        [0.0], background_noise_levels_db=[-25.0, -27.0]
    )
    tonal = ea.verify_induction_loop_system(
        [0.0], background_noise_levels_db=[-25.0, -27.0], noise_is_tonal=True
    )
    assert plain.background_noise is not None
    assert tonal.background_noise is not None
    assert plain.background_noise.category == "tolerable_for_short_periods"
    assert tonal.background_noise.category == "below_tolerable"
    assert tonal.background_noise.noise_is_tonal is True


def test_background_noise_does_not_decide_the_verdict() -> None:
    result = ea.verify_induction_loop_system([0.0], background_noise_levels_db=[-20.0])
    assert result.passes
    assert result.background_noise is not None
    assert result.background_noise.category == "below_tolerable"


def test_verdict_has_no_truth_value() -> None:
    result = ea.verify_induction_loop_system([0.0])
    with pytest.raises(TypeError, match="passes"):
        bool(result)


def test_requirement_has_no_truth_value() -> None:
    requirement = ea.verify_induction_loop_system([0.0]).requirement("field_strength")
    with pytest.raises(TypeError, match="passes"):
        bool(requirement)


def test_unknown_requirement_raises_key_error() -> None:
    result = ea.verify_induction_loop_system([0.0])
    with pytest.raises(KeyError, match="system_noise"):
        result.requirement("system_noise")


def test_nan_level_is_refused() -> None:
    with pytest.raises(ValueError, match="field_strength_levels_db"):
        ea.verify_induction_loop_system([0.0, math.nan])


# ---------------------------------------------------------------------------
# Small-volume systems (clause 9 as amended)
# ---------------------------------------------------------------------------


def test_counter_within_6_db_reaching_0_db_passes() -> None:
    levels = np.array([[-6.0, 0.0, 6.0], [-2.0, 1.0, 3.0], [-5.0, -1.0, 2.0]])
    result = ea.verify_small_volume_system(levels, layout="counter")
    assert result.passes
    assert result.clause == "9"
    assert [r.name for r in result.requirements] == [
        "field_strength_range",
        "field_strength_reached",
        "standing_area",
    ]


def test_small_volume_below_0_db_everywhere_fails() -> None:
    levels = np.full((2, 6), -0.5)
    result = ea.verify_small_volume_system(levels, layout="refuge_small")
    assert result.failed == ("field_strength_reached",)


def test_small_volume_above_6_db_fails_the_range() -> None:
    levels = np.zeros((2, 6))
    levels[1, 2] = 6.5
    result = ea.verify_small_volume_system(levels, layout="refuge_large")
    assert result.failed == ("field_strength_range",)


def test_standing_area_survey_above_8_db_fails() -> None:
    result = ea.verify_small_volume_system(
        np.zeros((3, 3)), layout="counter", standing_area_levels_db=[7.5, 8.0, 8.2]
    )
    assert result.failed == ("standing_area",)
    assert result.requirement("standing_area").worst_margin_db == pytest.approx(-0.2)


def test_small_volume_frequency_response_is_judged_at_every_point() -> None:
    response = np.zeros((9, 3))
    response[4, 2] = -3.2
    result = ea.verify_small_volume_system(
        np.zeros((3, 3)), layout="counter", frequencies_hz=_F, response_db=response
    )
    assert result.failed == ("frequency_response",)


def test_layout_fixes_the_shape_of_the_levels() -> None:
    levels = np.zeros((2, 6))
    with pytest.raises(ValueError, match=r"shape \(3, 3\)"):
        ea.verify_small_volume_system(levels, layout="counter")


def test_counter_useful_volume_covers_the_three_heights_of_9_3() -> None:
    result = ea.verify_small_volume_system(
        [0.5, 1.0, -4.0, 5.0],
        layout="counter_useful_volume",
        heights_m=[1.2, 1.45, 1.7, 1.7],
    )
    assert result.passes
    assert result.layout == "counter_useful_volume"


def test_refuge_useful_volume_needs_only_the_two_heights_of_9_2() -> None:
    result = ea.verify_small_volume_system(
        [[0.5, -2.0], [1.0, 3.0]],
        layout="refuge_useful_volume",
        heights_m=[[1.2, 1.2], [1.7, 1.7]],
    )
    assert result.passes


def test_useful_volume_missing_a_height_of_9_3_is_refused() -> None:
    levels = [0.0, 1.0, 2.0]
    heights = [1.2, 1.2, 1.7]
    with pytest.raises(ValueError, match=r"none is at 1\.45 m"):
        ea.verify_small_volume_system(
            levels, layout="counter_useful_volume", heights_m=heights
        )


@pytest.mark.parametrize(
    ("heights", "missing"), [([1.2, 1.2, 1.2], r"1\.7 m"), ([1.7, 1.7, 1.7], r"1\.2 m")]
)
def test_useful_volume_missing_a_height_of_9_2_is_refused(
    heights: list[float], missing: str
) -> None:
    with pytest.raises(ValueError, match=rf"none is at {missing}"):
        ea.verify_small_volume_system(
            [0.0, 1.0, 2.0], layout="refuge_useful_volume", heights_m=heights
        )


def test_useful_volume_needs_the_heights_of_its_points() -> None:
    with pytest.raises(ValueError, match="heights_m"):
        ea.verify_small_volume_system([0.0], layout="refuge_useful_volume")


def test_useful_volume_heights_follow_the_shape_of_the_levels() -> None:
    levels = [0.0, 1.0]
    heights = [1.2, 1.7, 1.7]
    with pytest.raises(ValueError, match="shape"):
        ea.verify_small_volume_system(
            levels, layout="refuge_useful_volume", heights_m=heights
        )


def test_fixed_layout_refuses_heights() -> None:
    levels = np.zeros((3, 3))
    heights = np.full((3, 3), 1.2)
    with pytest.raises(ValueError, match="heights_m"):
        ea.verify_small_volume_system(levels, layout="counter", heights_m=heights)


# ---------------------------------------------------------------------------
# The overload test (10.3 as amended)
# ---------------------------------------------------------------------------


def test_table_4_is_the_printed_one() -> None:
    table = ea.OVERLOAD_TEST_FREQUENCIES
    assert isinstance(table, MappingProxyType)
    printed = tuple(
        (key, row.power_bandwidth_limit_hz, row.test_frequency_hz)
        for key, row in table.items()
    )
    assert printed == ref.IEC60118_4_A1_TABLE4


def test_table_4_rows_are_frozen() -> None:
    row = ea.OVERLOAD_TEST_FREQUENCIES["speech"]
    with pytest.raises(AttributeError, match="test_frequency_hz"):
        row.test_frequency_hz = 1.0  # type: ignore[misc]


def _doubling_frequency(resistance: float, inductance: float) -> float:
    """Where sqrt(R^2 + (2 pi f L)^2) is twice its value at 1 kHz."""
    w1 = 2.0 * math.pi * 1000.0 * inductance
    return math.sqrt(3.0 * resistance**2 + 4.0 * w1**2) / (2.0 * math.pi * inductance)


def test_overload_test_level_is_7_db_down() -> None:
    impedance = ea.loop_impedance(0.69, 109e-6)
    result = ea.verify_amplifier_overload(3.0, impedance, 20.0)
    offset = 20 * math.log10(result.test_current_a / 3.0)
    assert offset == pytest.approx(ref.IEC60118_4_A1_OVERLOAD_OFFSET_DB, abs=1e-12)


def test_inductive_loop_doubles_before_the_table_frequency() -> None:
    impedance = ea.loop_impedance(0.69, 109e-6)
    result = ea.verify_amplifier_overload(3.0, impedance, 20.0)
    expected = _doubling_frequency(0.69, 109e-6)
    assert result.doubling_frequency_hz == pytest.approx(expected, rel=1e-9)
    assert result.end_frequency_hz == pytest.approx(3150.0)
    assert result.frequencies_hz[-1] == pytest.approx(3150.0)


def test_doubling_above_the_table_frequency_extends_the_sweep() -> None:
    impedance = ea.loop_impedance(2.0, 109e-6)
    result = ea.verify_amplifier_overload(
        1.0, impedance, 20.0, programme="transient_speech"
    )
    expected = _doubling_frequency(2.0, 109e-6)
    assert expected > 2500.0
    assert result.end_frequency_hz == pytest.approx(expected, rel=1e-9)


def test_resistive_loop_that_never_doubles_stops_at_table_4() -> None:
    impedance = ea.loop_impedance(8.0, 10e-6)
    result = ea.verify_amplifier_overload(1.0, impedance, 20.0, programme="music")
    assert math.isinf(result.doubling_frequency_hz)
    assert result.end_frequency_hz == pytest.approx(4000.0)


def test_overload_passes_on_the_compliance_voltage() -> None:
    impedance = ea.loop_impedance(0.69, 109e-6)
    probe = ea.verify_amplifier_overload(3.0, impedance, 100.0)
    needed = probe.test_frequency_voltage_v
    assert needed == pytest.approx(
        3.0 * 10 ** (-7 / 20) * float(impedance.at(3150.0)), rel=1e-12
    )
    assert probe.max_voltage_v == pytest.approx(needed, rel=1e-12)
    assert ea.verify_amplifier_overload(3.0, impedance, needed).passes
    assert not ea.verify_amplifier_overload(3.0, impedance, 0.99 * needed).passes


def test_overload_is_judged_at_the_table_4_frequency() -> None:
    # The voltage doubles above 2,5 kHz, so the sweep runs on past Table 4;
    # 10.3.3 forbids clipping at the Table 4 frequency, not beyond it.
    impedance = ea.loop_impedance(2.0, 109e-6)
    at_table_4 = 10 ** (-7 / 20) * float(impedance.at(2500.0))
    probe = ea.verify_amplifier_overload(
        1.0, impedance, 100.0, programme="transient_speech"
    )
    assert probe.test_frequency_voltage_v == pytest.approx(at_table_4, rel=1e-12)
    assert probe.max_voltage_v > 1.2 * at_table_4
    between = 0.5 * (at_table_4 + probe.max_voltage_v)
    result = ea.verify_amplifier_overload(
        1.0, impedance, between, programme="transient_speech"
    )
    assert result.passes
    assert result.headroom_db == pytest.approx(
        20 * math.log10(between / at_table_4), rel=1e-12
    )


def test_current_response_scales_the_loop_voltage_in_decibels() -> None:
    # The current doubles from 1 kHz to 2 kHz and holds: 6,02 dB of lift,
    # read log-linearly between the measured frequencies.
    impedance = ea.loop_impedance(0.69, 109e-6)
    response = ea.amplifier_frequency_response(
        [50.0, 1000.0, 2000.0, 20000.0], [1.0, 1.0, 2.0, 2.0]
    )
    result = ea.verify_amplifier_overload(
        3.0, impedance, 100.0, current_response=response
    )
    test_current = 3.0 * 10 ** (-7 / 20)
    assert result.test_frequency_voltage_v == pytest.approx(
        test_current * 2.0 * float(impedance.at(3150.0)), rel=1e-9
    )
    inside = np.flatnonzero(
        (result.frequencies_hz > 1100.0) & (result.frequencies_hz < 1900.0)
    )[0]
    f = float(result.frequencies_hz[inside])
    gain = 2.0 ** (math.log(f / 1000.0) / math.log(2.0))
    assert result.voltage_v[inside] == pytest.approx(
        test_current * gain * float(impedance.at(f)), rel=1e-9
    )


def test_current_boost_for_metal_loss_raises_the_voltage() -> None:
    impedance = ea.loop_impedance(0.69, 109e-6)
    response = ea.amplifier_frequency_response(
        [50.0, 1000.0, 2000.0, 4000.0, 8000.0], [1.0, 1.0, 1.26, 1.58, 2.0]
    )
    flat = ea.verify_amplifier_overload(3.0, impedance, 100.0)
    boosted = ea.verify_amplifier_overload(
        3.0, impedance, 100.0, current_response=response
    )
    assert boosted.max_voltage_v > flat.max_voltage_v
    assert boosted.doubling_frequency_hz < flat.doubling_frequency_hz


def test_current_response_has_to_reach_the_table_frequency() -> None:
    impedance = ea.loop_impedance(0.69, 109e-6)
    response = ea.amplifier_frequency_response([100.0, 1000.0, 2000.0], [1.0, 1.0, 1.0])
    with pytest.raises(ValueError, match="Table 4"):
        ea.verify_amplifier_overload(3.0, impedance, 10.0, current_response=response)


def _first_doubling(
    impedance: ph.electroacoustics.LoopImpedance,
    frequencies_hz: list[float],
    currents_a: list[float],
) -> float:
    """The first frequency above 1 kHz where the loop voltage doubles.

    Read on its own: the current log-linearly between the measured
    frequencies, the voltage on a fine logarithmic grid, and the first grid
    point at or above twice the start refined by bisection.
    """
    log_f = np.log(frequencies_hz)
    gain_db = 20 * np.log10(
        np.asarray(currents_a) / currents_a[frequencies_hz.index(1000.0)]
    )

    def voltage(f: np.ndarray) -> np.ndarray:
        gain = 10 ** (np.interp(np.log(f), log_f, gain_db) / 20)
        return gain * np.hypot(
            impedance.resistance_ohm, 2 * np.pi * f * impedance.inductance_h
        )

    target = 2 * float(voltage(np.array(1000.0)))
    grid = np.geomspace(1000.0, frequencies_hz[-1], 200001)
    k = int(np.argmax(voltage(grid) >= target))
    low, high = float(grid[k - 1]), float(grid[k])
    for _ in range(80):
        middle = 0.5 * (low + high)
        if float(voltage(np.array(middle))) >= target:
            high = middle
        else:
            low = middle
    return high


def test_overload_sweep_stops_at_the_first_doubling_of_a_peaked_response() -> None:
    # A correction that peaks at 5 kHz and falls away above it doubles the
    # voltage near 4,2 kHz and brings it back below twice its start by
    # 10 kHz: the sweep ends at that first doubling, above the 4 kHz of Table 4.
    impedance = ea.loop_impedance(2.0, 20e-6)
    frequencies = [
        100.0,
        1000.0,
        2000.0,
        3150.0,
        4000.0,
        5000.0,
        6300.0,
        8000.0,
        10000.0,
    ]
    currents = [1.0, 1.0, 1.2, 1.5, 1.8, 2.6, 1.5, 0.6, 0.3]
    response = ea.amplifier_frequency_response(frequencies, currents)
    result = ea.verify_amplifier_overload(
        1.0, impedance, 10.0, programme="music", current_response=response
    )
    expected = _first_doubling(impedance, frequencies, currents)
    assert 4000.0 < expected < 5000.0
    assert result.doubling_frequency_hz == pytest.approx(expected, rel=1e-9)
    assert result.end_frequency_hz == pytest.approx(expected, rel=1e-9)
    assert result.frequencies_hz[-1] == pytest.approx(expected, rel=1e-9)
    assert result.voltage_v[-1] == pytest.approx(2 * result.voltage_v[0], rel=1e-9)


def test_overload_sweep_takes_the_first_of_several_doublings() -> None:
    # The voltage doubles near 2,3 kHz, falls back and doubles again near
    # 9 kHz; the first doubling is below the 3,15 kHz of Table 4, where the
    # sweep for speech ends.
    impedance = ea.loop_impedance(2.0, 20e-6)
    frequencies = [1000.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0]
    frequencies += [10000.0, 20000.0]
    currents = [1.0, 1.5, 2.4, 1.2, 1.0, 1.0, 1.1, 1.5, 2.0, 3.0]
    response = ea.amplifier_frequency_response(frequencies, currents)
    result = ea.verify_amplifier_overload(
        1.0, impedance, 10.0, current_response=response
    )
    expected = _first_doubling(impedance, frequencies, currents)
    assert 2000.0 < expected < 2500.0
    assert result.doubling_frequency_hz == pytest.approx(expected, rel=1e-9)
    assert result.end_frequency_hz == pytest.approx(3150.0)


def test_overload_verdict_has_no_truth_value() -> None:
    result = ea.verify_amplifier_overload(3.0, ea.loop_impedance(0.69, 109e-6), 20.0)
    with pytest.raises(TypeError, match="passes"):
        bool(result)


def test_overload_refuses_an_unknown_programme() -> None:
    impedance = ea.loop_impedance(0.69, 109e-6)
    with pytest.raises(ValueError, match="programme"):
        ea.verify_amplifier_overload(3.0, impedance, 20.0, programme="opera")


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "es"])
def test_every_result_plots(language: str) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    impedance = ea.loop_impedance(0.69, 109e-6)
    verification = ea.verify_induction_loop_system(
        [0.0, 1.0],
        frequencies_hz=_F,
        response_db=[0.0, 0.0, -1.0],
        background_noise_levels_db=[-50.0, -48.0],
        system_noise_levels_db=[-48.0, -47.5],
    )
    results = (
        ea.field_strength_meter(_sine(-3.0, 1000.0, seconds=0.5), FS),
        ea.assess_background_noise([-50.0, -40.0]),
        verification,
        verification.requirement("system_noise"),
        ea.verify_small_volume_system(np.zeros((3, 3)), layout="counter"),
        ea.verify_amplifier_overload(3.0, impedance, 20.0),
    )
    for result in results:
        ax = result.plot(language=language)
        assert ax.get_title()
        plt.close("all")


# ---------------------------------------------------------------------------
# What the plots draw
# ---------------------------------------------------------------------------

_VERDICT_WORDS = {("en", True): "pass", ("en", False): "fail"}
_VERDICT_WORDS |= {("es", True): "cumple", ("es", False): "no cumple"}


def _title_verdict(title: str) -> str:
    """The verdict word a plot title ends with."""
    return title.rsplit(": ", 1)[1]


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("compliance", [100.0, 5.0])
def test_overload_plot_draws_the_sweep_the_compliance_and_the_verdict(
    language: str, compliance: float
) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    result = ea.verify_amplifier_overload(
        1.0, ea.loop_impedance(2.0, 109e-6), compliance, programme="transient_speech"
    )
    ax = result.plot(language=language)
    np.testing.assert_array_equal(ax.lines[0].get_xdata(), result.frequencies_hz)
    np.testing.assert_array_equal(ax.lines[0].get_ydata(), result.voltage_v)
    compliance_line = ax.lines[1]
    assert tuple(compliance_line.get_ydata()) == (compliance, compliance)
    judged = [
        line
        for line in ax.lines
        if tuple(line.get_xdata()) == (result.programme.test_frequency_hz,)
    ]
    assert len(judged) == 1
    assert tuple(judged[0].get_ydata()) == (result.test_frequency_voltage_v,)
    expected = _VERDICT_WORDS[(language, result.passes)]
    assert _title_verdict(ax.get_title()) == expected
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
def test_verification_plot_draws_the_worst_margins_and_the_verdict(
    language: str,
) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    result = ea.verify_induction_loop_system(
        [-0.5, -3.4],
        frequencies_hz=_F,
        response_db=[0.0, 0.0, -2.0],
    )
    assert not result.passes
    ax = result.plot(language=language)
    heights = [patch.get_height() for patch in ax.patches]
    assert heights == pytest.approx([r.worst_margin_db for r in result.requirements])
    assert _title_verdict(ax.get_title()) == _VERDICT_WORDS[(language, False)]
    ticks = [label.get_text() for label in ax.get_xticklabels()]
    clause = "apartado 8.4.3" if language == "es" else "\n8.4.3"
    assert clause in ticks[0]
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
def test_requirement_plot_draws_each_value_against_its_limits(language: str) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    requirement = ea.verify_induction_loop_system([0.5, -1.0, 2.0]).requirement(
        "field_strength"
    )
    ax = requirement.plot(language=language)
    np.testing.assert_array_equal(ax.lines[0].get_ydata(), requirement.values_db)
    steps = {tuple(np.unique(line.get_ydata())) for line in ax.lines[1:]}
    assert (-3.0,) in steps
    assert (3.0,) in steps
    assert _title_verdict(ax.get_title()) == _VERDICT_WORDS[(language, True)]
    if language == "es":
        assert "(apartado 8.4.3)" in ax.get_title()
    plt.close("all")


def test_meter_plot_marks_the_maximum_where_it_occurs() -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    reading = ea.field_strength_meter(_sine(-3.0, 1000.0, seconds=0.5), FS)
    ax = reading.plot()
    marker = ax.lines[-1]
    assert tuple(marker.get_ydata()) == (reading.maximum_db,)
    peak = int(np.argmax(reading.levels_db))
    assert tuple(marker.get_xdata()) == (reading.times_s[peak],)
    plt.close("all")
