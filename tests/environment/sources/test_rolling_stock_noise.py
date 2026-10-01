#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the noise of railway rolling stock, ISO 3095:2013.

The printed oracles are the numbers ISO 3095 sets beside its figures: the
roughness limit of Figure 2, printed a second time as a table in the
EN 15610:2009 Annex B listing; the decay-rate limits of Figure 3; the
microphone positions Figure 10 dimensions for four units; and the worked
uncertainty budget of Table G.2 with the order Figure G.1 draws its bars in.
Everything else has no worked example, so it is held to closed forms: a
steady 1 kHz tone reads its own level, the transit exposure level of the 2005
edition is its Formulae 9 and 10, and at 36 km/h a band of wavelength falls
exactly on a band of frequency, which makes Annexes C and E sums of a few
known terms.
"""

from __future__ import annotations

import dataclasses
import itertools
import math

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from reference_data import rolling_stock_noise as ref

from phonometry import environment, metrology
from phonometry.environment.sources.acoustic_roughness import (
    AcousticRoughnessSpectrum,
    average_roughness_spectra,
)
from phonometry.environment.sources.rolling_stock_noise import (
    PREFERRED_PASS_BY_SPEEDS_KMH,
    REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M,
    REFERENCE_TRACK_ROUGHNESS_LIMIT_DB,
    ROLLING_STOCK_TEST_METHODS,
    STATIONARY_END_POSITION_LENGTH_M,
    ReferenceTrackCheck,
    SmallRoughnessDeviation,
    acceleration_test_positions,
    background_level_increase,
    check_adjacent_vehicle_neutrality,
    check_reference_track,
    check_small_roughness_deviations,
    impulsiveness_rise_speed,
    minimum_curve_radius,
    pass_by_measurement,
    pass_by_time,
    pass_by_uncertainty,
    rolling_stock_test,
    roughness_comparability,
    stationary_test,
    stationary_unit_level,
    transit_exposure_level,
    type_test_speeds,
)
from phonometry.environment.sources.track_decay import (
    TRACK_DECAY_DIRECTIONS,
    TrackDecayRate,
    track_decay_excitation_positions,
    track_decay_rate,
)
from phonometry.io import Signal

_FS = 48000
_P0 = 2.0e-5
#: At 10 m/s a base-ten band of wavenumber k lands exactly on band k + 10 of
#: frequency, so the roughness of one wavelength band is carried whole.
_ALIGNED_SPEED_KMH = 36.0
_NOISE_BANDS_HZ = (
    31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0, 250.0, 315.0,
    400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0,
    3150.0, 4000.0, 5000.0, 6300.0, 8000.0,
)  # fmt: skip


def _energy_sum(levels: np.ndarray) -> float:
    return float(10.0 * np.log10(np.sum(10.0 ** (levels / 10.0))))


def _limit_spectrum(offset_db: float = 0.0) -> AcousticRoughnessSpectrum:
    wavelengths = sorted(REFERENCE_TRACK_ROUGHNESS_LIMIT_DB, reverse=True)
    return AcousticRoughnessSpectrum(
        wavelengths,
        [REFERENCE_TRACK_ROUGHNESS_LIMIT_DB[w] + offset_db for w in wavelengths],
    )


# ---------------------------------------------------------------------------
# The printed tables
# ---------------------------------------------------------------------------


def test_the_roughness_limit_is_figure_2() -> None:
    """The 22 labels Figure 2 prints, from 40 cm to 0,315 cm."""
    wavelengths = [100.0 * w for w in REFERENCE_TRACK_ROUGHNESS_LIMIT_DB]
    np.testing.assert_allclose(wavelengths, ref.FIGURE_2_WAVELENGTHS_CM, rtol=1e-12)
    assert tuple(REFERENCE_TRACK_ROUGHNESS_LIMIT_DB.values()) == ref.FIGURE_2_LIMIT_DB


def test_figure_2_and_the_en_15610_listing_print_the_same_limit() -> None:
    """Two printings of one curve: ISO 3095 Figure 2 and EN 15610 Annex B.9.2."""
    assert ref.EN15610_LISTING_LIMIT_DB == ref.FIGURE_2_LIMIT_DB
    for listed, nominal in zip(
        ref.EN15610_LISTING_WAVELENGTHS_M,
        REFERENCE_TRACK_ROUGHNESS_LIMIT_DB,
        strict=True,
    ):
        # The listing types 3,15 cm as 0.032 and 3,15 mm as 0.003: the same band.
        assert round(-10.0 * math.log10(listed)) == round(-10.0 * math.log10(nominal))


def test_the_decay_limits_are_figure_3() -> None:
    """The table beside the curves of Figure 3, vertical (A) and lateral (B)."""
    vertical = REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M["vertical"]
    lateral = REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M["lateral"]
    assert tuple(vertical) == ref.FIGURE_3_FREQUENCIES_HZ
    assert tuple(vertical.values()) == ref.FIGURE_3_VERTICAL_DB_PER_M
    assert tuple(lateral) == ref.FIGURE_3_FREQUENCIES_HZ
    assert tuple(lateral.values()) == ref.FIGURE_3_LATERAL_DB_PER_M


def test_the_published_tables_are_immutable() -> None:
    """Nested mappings refuse assignment all the way down."""
    with pytest.raises(TypeError, match="does not support item assignment"):
        REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M["vertical"][250.0] = 0.0  # type: ignore[index]


def test_the_preferred_speeds_are_6_6_2() -> None:
    """Thirteen speeds, with no 180 km/h."""
    assert len(PREFERRED_PASS_BY_SPEEDS_KMH) == 13
    assert 180.0 not in PREFERRED_PASS_BY_SPEEDS_KMH
    assert PREFERRED_PASS_BY_SPEEDS_KMH[-1] == 350.0


@pytest.mark.parametrize(
    ("length_m", "positions"), sorted(ref.FIGURE_10_POSITIONS_M.items())
)
def test_the_starting_test_positions_are_figure_10(
    length_m: float, positions: tuple[float, ...]
) -> None:
    """42, 54, 87 and 108 m units, positions as Figure 10 dimensions them."""
    np.testing.assert_allclose(
        acceleration_test_positions(length_m), positions, atol=1e-12
    )


def test_a_50_m_unit_has_one_position_and_a_100_m_unit_two() -> None:
    """At 50 m no further position; at 100 m the centre position is exactly 50 m away."""
    np.testing.assert_allclose(acceleration_test_positions(50.0), [-10.0])
    np.testing.assert_allclose(acceleration_test_positions(100.0), [-10.0, 40.0])


def test_a_51_m_unit_has_two_positions_and_a_101_m_unit_three() -> None:
    """Past 50 m the centre position comes in; past 50 m apart, the gap is split in two."""
    np.testing.assert_allclose(acceleration_test_positions(51.0), [-10.0, 15.5])
    np.testing.assert_allclose(acceleration_test_positions(101.0), [-10.0, 15.25, 40.5])


def test_table_g2_is_reproduced() -> None:
    """55,68 dB, u_c = 0,83 dB and U = 1,66 dB, from the printed rows."""
    budget = pass_by_uncertainty(
        ref.TABLE_G2_READING_DB,
        [metrology.Quantity(v, u, name=n) for n, v, u in ref.TABLE_G2_ROWS],
    )
    assert budget.level_db == pytest.approx(ref.TABLE_G2_LEVEL_DB, abs=1e-12)
    assert (
        round(budget.combined_uncertainty_db, 2) == ref.TABLE_G2_COMBINED_UNCERTAINTY_DB
    )
    assert (
        round(budget.expanded_uncertainty_db, 2) == ref.TABLE_G2_EXPANDED_UNCERTAINTY_DB
    )


def test_figure_g1_draws_the_shares_largest_first() -> None:
    """Sorted by share, ties kept in Table G.2 order, the budget is Figure G.1."""
    budget = pass_by_uncertainty(
        ref.TABLE_G2_READING_DB,
        [metrology.Quantity(v, u, name=n) for n, v, u in ref.TABLE_G2_ROWS],
    )
    ranked = sorted(
        budget.variance_ratios, key=lambda name: -budget.variance_ratios[name]
    )
    assert tuple(ranked) == ref.FIGURE_G1_ORDER
    assert sum(budget.variance_ratios.values()) == pytest.approx(1.0)


def test_a_budget_built_from_lists_holds_tuples() -> None:
    """Direct construction with lists cannot leave the budget open to appends."""
    budget = environment.PassByUncertainty(
        reading_db=55.0, names=["tripod"], corrections_db=[0.0],
        standard_uncertainties_db=[0.35],
    )  # fmt: skip
    assert budget.names == ("tripod",)
    assert budget.corrections_db == (0.0,)
    assert budget.standard_uncertainties_db == (0.35,)


@pytest.mark.parametrize(
    ("name", "half_width", "printed"), ref.TABLE_G1_RECTANGULAR_ROWS
)
def test_table_g1_rows_are_a_over_root_3(
    name: str, half_width: float, printed: float
) -> None:
    """Formula G.2 gives every printed standard uncertainty of the rectangular rows."""
    assert round(metrology.rectangular(0.0, half_width, name).uncertainty, 2) == printed


def test_two_rows_of_table_g1_are_not_a_over_root_3() -> None:
    """The 25 m distance row prints 0,004 dB and the 7,5 m ground row 0,55 dB.

    Formula G.2 gives 0,040 dB and 0,30 dB; Table G.2 prints 0,30 dB for the
    same ground row. Both are in the errata register.
    """
    _, a_distance, printed_distance = ref.TABLE_G1_DISTANCE_25M
    _, a_ground, printed_ground = ref.TABLE_G1_GROUND_LEVEL_7_5M
    assert round(a_distance / math.sqrt(3.0), 3) == 0.040
    assert printed_distance == 0.004
    assert round(a_ground / math.sqrt(3.0), 2) == 0.30
    assert printed_ground == 0.55


# ---------------------------------------------------------------------------
# Speeds, times and the transit exposure level
# ---------------------------------------------------------------------------


def test_the_type_test_speeds() -> None:
    """6.6.2: 80 km/h and v_max above 80 km/h, v_max alone at or below."""
    assert type_test_speeds(160.0) == (80.0, 160.0)
    assert type_test_speeds(80.0) == (80.0,)
    assert type_test_speeds(60.0) == (60.0,)


@pytest.mark.parametrize(
    ("speed", "radius"),
    [(70.0, 1000.0), (70.5, 3000.0), (120.0, 3000.0), (121.0, 5000.0)],
)
def test_the_minimum_curve_radius(speed: float, radius: float) -> None:
    """6.2.2: 1 000 m to 70 km/h, 3 000 m to 120 km/h, 5 000 m above."""
    assert minimum_curve_radius(speed) == radius


def test_the_pass_by_time_is_length_over_speed() -> None:
    """A 200 m train at 144 km/h, 40 m/s, takes 5 s."""
    assert pass_by_time(200.0, speed_kmh=144.0) == pytest.approx(5.0)


def test_the_transit_exposure_level_is_formulae_9_and_10() -> None:
    """TEL = L_Aeq,T + 10 lg(T/Tp) = SEL + 10 lg(T0/Tp), with T0 = 1 s."""
    level, duration, passing = 84.0, 12.0, 5.0
    tel = transit_exposure_level(
        level, measurement_time_s=duration, pass_by_time_s=passing
    )
    sel = level + 10.0 * math.log10(duration)
    assert tel == pytest.approx(level + 10.0 * math.log10(duration / passing))
    assert tel == pytest.approx(sel + 10.0 * math.log10(1.0 / passing))


# ---------------------------------------------------------------------------
# The pass-by record
# ---------------------------------------------------------------------------


def _tone(amplitude_pa: float, seconds: float = 10.0) -> np.ndarray:
    t = np.arange(int(seconds * _FS)) / _FS
    return amplitude_pa * np.sin(2.0 * np.pi * 1000.0 * t)


def test_a_steady_1_khz_tone_reads_its_own_level() -> None:
    """A-weighting is 0 dB at 1 kHz, so L_Aeq and L_AFmax are 10 lg(A**2/2/p0**2)."""
    amplitude = 1.0
    record = pass_by_measurement(_tone(amplitude), _FS, start_s=2.0, end_s=8.0)
    expected = 10.0 * math.log10(amplitude**2 / 2.0 / _P0**2)
    assert record.equivalent_level_db == pytest.approx(expected, abs=0.02)
    assert record.max_level_db == pytest.approx(expected, abs=0.05)
    assert record.measurement_time_s == pytest.approx(6.0)
    assert record.exposure_level_db == pytest.approx(
        record.equivalent_level_db + 10.0 * math.log10(6.0)
    )
    assert record.normalized_level_db is None


def test_the_interval_spread_over_tp_is_the_transit_exposure_level() -> None:
    """Over 6 s spread over a 3 s pass-by the energy reads 10 lg 2 dB higher."""
    record = pass_by_measurement(
        _tone(0.5), _FS, start_s=2.0, end_s=8.0, pass_by_time_s=3.0
    )
    assert record.normalized_level_db == pytest.approx(
        record.equivalent_level_db + 10.0 * math.log10(2.0)
    )


def test_the_record_margins_of_6_6_3() -> None:
    """A burst centred in a quiet record starts and ends more than 10 dB down."""
    t = np.arange(int(20.0 * _FS)) / _FS
    envelope = np.exp(-(((t - 10.0) / 2.5) ** 2)) + 1.0e-3
    record = pass_by_measurement(
        np.sin(2.0 * np.pi * 1000.0 * t) * envelope, _FS, start_s=8.0, end_s=12.0
    )
    assert record.start_margin_db > 10.0
    assert record.end_margin_db > 10.0
    assert record.recording_interval_sufficient is True
    short = pass_by_measurement(
        np.sin(2.0 * np.pi * 1000.0 * t) * envelope, _FS, start_s=8.0, end_s=12.0,
        front_passing_s=0.5,
    )  # fmt: skip
    assert short.recording_interval_sufficient is False


def _stepped_tone(steps_db: tuple[float, float, float]) -> np.ndarray:
    """A 1 kHz tone of 0,1 Pa whose level steps at 2 s and 8 s, zero crossings both."""
    t = np.arange(int(10.0 * _FS)) / _FS
    gain = np.where(t < 2.0, steps_db[0], np.where(t < 8.0, steps_db[1], steps_db[2]))
    return 0.1 * 10.0 ** (gain / 20.0) * np.sin(2.0 * np.pi * 1000.0 * t)


@pytest.mark.parametrize("end", ["start", "end"])
@pytest.mark.parametrize(
    ("margin_db", "sufficient"),
    [(8.0, False), (9.5, False), (10.1, True), (11.0, True)],
)
def test_the_record_margin_is_10_db_at_either_end(
    end: str, margin_db: float, *, sufficient: bool
) -> None:
    """6.6.3: a record 9,5 dB down at either end is short, one 10,1 dB down is not.

    The level steps up at 2 s and down at 8 s. With the front passing at 5 s
    and the rear at 7 s, the record ends 12 dB down and the start margin
    decides; with the front at 3 s and the rear at 5 s, it starts 12 dB down
    and the end margin decides. 10 dB itself is not tried: time weighting F
    leaves a ripple of a few thousandths of a decibel on the tone.
    """
    if end == "start":
        steps, start_s, end_s = (-margin_db, 0.0, -12.0), 5.0, 7.0
    else:
        steps, start_s, end_s = (-12.0, 0.0, -margin_db), 3.0, 5.0
    record = pass_by_measurement(
        _stepped_tone(steps), _FS, start_s=start_s, end_s=end_s
    )
    margins = {"start": record.start_margin_db, "end": record.end_margin_db}
    other = "end" if end == "start" else "start"
    assert margins[end] == pytest.approx(margin_db, abs=0.05)
    assert margins[other] == pytest.approx(12.0, abs=0.05)
    assert record.recording_interval_sufficient is sufficient


def test_the_maximum_is_taken_within_the_interval() -> None:
    """A burst ten times louder outside T1 to T2 does not reach L_pAFmax (3.13).

    The burst ends 1,4 s before T1, by when time weighting F has let it fall
    about 49 dB, under the tone by more than 25 dB.
    """
    t = np.arange(int(10.0 * _FS)) / _FS
    p = _tone(0.1)
    burst = (t >= 0.2) & (t < 0.6)
    p[burst] *= 10.0
    record = pass_by_measurement(p, _FS, start_s=2.0, end_s=8.0)
    steady = 10.0 * math.log10(0.1**2 / 2.0 / _P0**2)
    assert record.max_level_db == pytest.approx(steady, abs=0.05)
    assert float(np.max(record.levels_db)) > steady + 15.0


def test_the_equivalent_level_is_the_mean_square_of_the_pressure() -> None:
    """L_pAeq,T is 10 lg of the mean of p_A^2 (3.14), not of the F-weighted square.

    A burst 30 times louder in the last 50 ms of the interval carries most
    of its energy; the F time weighting would spread it past T2 and read
    about 5,6 dB less. At 1 kHz the A-weighting is 0 dB, so the unweighted
    record gives the expected level.
    """
    t = np.arange(int(10.0 * _FS)) / _FS
    p = _tone(0.1)
    p[(t >= 7.95) & (t < 8.0)] *= 30.0
    record = pass_by_measurement(p, _FS, start_s=2.0, end_s=8.0)
    first, last = 2 * _FS, 8 * _FS
    expected = 10.0 * math.log10(float(np.mean(p[first:last] ** 2)) / _P0**2)
    assert record.equivalent_level_db == pytest.approx(expected, abs=0.05)


def test_a_signal_is_read_in_pascals() -> None:
    """A calibrated Signal gives the result of the samples times the factor."""
    samples = _tone(0.1, seconds=2.0)
    from_signal = pass_by_measurement(
        Signal(samples, _FS, calibration_factor=4.0), start_s=0.5, end_s=1.5
    )
    from_array = pass_by_measurement(4.0 * samples, _FS, start_s=0.5, end_s=1.5)
    assert from_signal.equivalent_level_db == from_array.equivalent_level_db


def test_the_interval_has_to_lie_inside_the_record() -> None:
    """An end past the record is refused by name."""
    samples = _tone(0.1, seconds=1.0)
    with pytest.raises(ValueError, match="'end_s' is .*past the end of the"):
        pass_by_measurement(samples, _FS, start_s=0.2, end_s=3.0)


@pytest.mark.parametrize("layout", ["columns", "rows", "signal"])
def test_a_record_of_two_channels_is_refused(layout: str) -> None:
    """A second channel is refused, not read as more of the same record.

    Flattened, a (samples, 2) array interleaves the channels into a record
    twice as long, and a (2, samples) array puts one channel after the other.
    """
    tone = _tone(0.1, seconds=3.0)
    silent = np.zeros_like(tone)
    records = {
        "columns": np.column_stack([tone, silent]),
        "rows": np.vstack([silent, tone]),
        "signal": Signal(np.vstack([tone, silent]), _FS),
    }
    rate = None if layout == "signal" else _FS
    with pytest.raises(ValueError, match="'signal' must be a 1-D time series"):
        pass_by_measurement(records[layout], rate, start_s=0.5, end_s=2.5)


def test_the_interval_is_not_empty() -> None:
    """The end comes after the start."""
    samples = _tone(0.1, seconds=1.0)
    with pytest.raises(ValueError, match="'end_s' must come after 'start_s'"):
        pass_by_measurement(samples, _FS, start_s=0.5, end_s=0.5)


# ---------------------------------------------------------------------------
# The stationary test and the tests of three runs
# ---------------------------------------------------------------------------


def test_the_stationary_average_is_formula_1() -> None:
    """Lengths weigh the energies; equal levels average to themselves."""
    levels = np.array([60.0, 66.0])
    lengths = np.array([4.0, 12.0])
    expected = 10.0 * math.log10(0.25 * 10**6.0 + 0.75 * 10**6.6)
    assert stationary_unit_level(levels, lengths) == pytest.approx(expected)
    assert stationary_unit_level([70.0, 70.0, 70.0], [3.0, 5.0, 11.0]) == pytest.approx(
        70.0
    )


def test_the_end_position_stands_for_a_quarter_circle() -> None:
    """5.8.1: (pi/2) x 7,5 m."""
    assert pytest.approx(math.pi * 3.75) == STATIONARY_END_POSITION_LENGTH_M


def test_the_stationary_result_is_the_rounded_mean_of_the_sets() -> None:
    """Three sets, each by Formula 1, averaged and rounded; a half goes up."""
    lengths = [4.0, 4.0]
    result = stationary_test([[62.0, 63.0], [62.0, 63.0], [62.0, 63.0]], lengths)
    unit = stationary_unit_level([62.0, 63.0], lengths)
    np.testing.assert_allclose(result.set_levels_db, [unit] * 3)
    assert result.reported_level_db == float(round(unit))
    half = stationary_test([[62.5, 62.5]] * 3, lengths)
    assert half.reported_level_db == 63.0
    assert half.valid is True


def test_samples_3_db_apart_are_valid() -> None:
    """9.3: no more than 3 dB is valid, so a spread of 3,0 dB is and one of 3,1 dB is not."""
    lengths = [4.0, 4.0]
    exact = stationary_test([[60.0, 70.0], [63.0, 70.0], [61.0, 70.0]], lengths)
    assert exact.valid is True
    over = stationary_test([[60.0, 70.0], [63.1, 70.0], [61.0, 70.0]], lengths)
    assert over.valid is False


def test_the_stationary_spread_is_judged_per_position() -> None:
    """9.3: a position whose samples are more than 3 dB apart invalidates the set."""
    result = stationary_test([[60.0, 70.0], [63.5, 70.0], [61.0, 70.0]], [4.0, 4.0])
    np.testing.assert_allclose(result.position_spreads_db, [3.5, 0.0])
    assert result.valid is False


def test_the_stationary_test_needs_three_sets() -> None:
    """5.7 asks for three valid samples at each position."""
    with pytest.raises(ValueError, match="5.7 asks for at least 3 sets"):
        stationary_test([[60.0, 61.0], [60.0, 61.0]], [4.0, 4.0])


def test_the_result_is_the_highest_rounded_mean() -> None:
    """6.7.1: the louder side, each side the rounded mean of its runs."""
    result = rolling_stock_test(
        {"left": [80.2, 80.9, 81.4], "right": [81.6, 82.4, 81.9]}
    )
    assert dict(result.reported_levels_db) == {"left": 81.0, "right": 82.0}
    assert result.final_level_db == 82.0
    assert result.governing_position == "right"
    assert result.valid is True


@pytest.mark.parametrize(
    ("runs", "expected"),
    [
        ((70.1, 70.3, 71.1), 71.0),
        ((70.3, 70.6, 70.6), 71.0),
        ((70.1, 71.3, 73.1), 72.0),
    ],
)
def test_a_mean_on_the_half_goes_up(
    runs: tuple[float, float, float], expected: float
) -> None:
    """Means of 70,5 dB and 71,5 dB round up, though binary arithmetic lands them a hair under."""
    assert rolling_stock_test({"p": runs}).final_level_db == expected


def test_every_mean_of_runs_in_tenths_on_a_half_goes_up() -> None:
    """Runs reported to 0,1 dB from 70,0 dB to 72,9 dB: every mean of three that is a half rounds up.

    In tenths, the mean of three runs is their sum over 30 dB, a half when
    the sum leaves 15 over a multiple of 30, and half up is then
    (sum + 15) // 30.
    """
    halves = 0
    for tenths in itertools.combinations_with_replacement(range(700, 730), 3):
        total = sum(tenths)
        if total % 30 != 15:
            continue
        halves += 1
        result = rolling_stock_test({"p": [t / 10.0 for t in tenths]})
        assert result.final_level_db == (total + 15) // 30, tenths
    assert halves > 100


def test_a_tie_goes_to_the_first_position() -> None:
    """Two positions that round alike: the first one given governs."""
    result = rolling_stock_test(
        {"front": [70.1, 70.2, 70.3], "centre": [69.8, 70.0, 70.1]}, method="braking"
    )
    assert result.governing_position == "front"


def test_runs_more_than_3_db_apart_are_not_valid() -> None:
    """9.3: a spread above 3 dB asks for more runs."""
    result = rolling_stock_test(
        {"a": [70.0, 73.5, 71.0]}, method="acceleration_maximum"
    )
    assert result.spreads_db["a"] == pytest.approx(3.5)
    assert result.valid is False


@pytest.mark.parametrize(("top_db", "valid"), [(73.0, True), (73.1, False)])
def test_runs_3_db_apart_are_valid(top_db: float, *, valid: bool) -> None:
    """9.3: runs 3,0 dB apart are valid, runs 3,1 dB apart are not."""
    assert rolling_stock_test({"a": [70.0, top_db, 71.0]}).valid is valid


def test_every_method_is_accepted_and_nothing_else() -> None:
    """The four tests decided by the highest rounded mean."""
    assert ROLLING_STOCK_TEST_METHODS == (
        "constant_speed",
        "acceleration_maximum",
        "acceleration_averaged",
        "braking",
    )
    with pytest.raises(ValueError, match="'method' must be one of"):
        rolling_stock_test({"a": [70.0, 70.0, 70.0]}, method="coasting")


def test_a_position_needs_three_runs() -> None:
    """Three valid runs per position."""
    with pytest.raises(ValueError, match="position 'a' has 2 runs"):
        rolling_stock_test({"a": [70.0, 70.0]})


# ---------------------------------------------------------------------------
# Annexes A and D and 6.3.4
# ---------------------------------------------------------------------------


def test_the_rise_speed_is_the_steepest_rise_of_a_10_db_slope() -> None:
    """A 12 dB ramp at 60 dB/s counts; an 8 dB ramp at 200 dB/s does not."""
    dt = 0.01
    times = np.arange(0.0, 3.0, dt)
    levels = np.full(times.size, 60.0)
    levels[50:71] = 60.0 + 0.6 * np.arange(21)  # 12 dB over 0,2 s
    levels[71:150] = 72.0
    levels[150:155] = 72.0 + 2.0 * np.arange(5)  # 8 dB in 0,04 s
    levels[155:] = 80.0
    result = impulsiveness_rise_speed(times, levels)
    assert result.slopes == ((50, 70),)
    assert result.rise_speed_db_per_s == pytest.approx(60.0)


def test_the_rise_speed_is_the_steepest_step_not_the_mean_slope() -> None:
    """Formula A.1 takes the maximum of the derivative along a slope.

    Steps of 1, 1, 5, 1, 1 and 1 dB every 10 ms climb 10 dB at 500 dB/s in
    the steepest step and 167 dB/s on average.
    """
    times = np.arange(0.0, 1.0, 0.01)
    levels = np.full(times.size, 60.0)
    levels[20:27] = 60.0 + np.cumsum([0.0, 1.0, 1.0, 5.0, 1.0, 1.0, 1.0])
    levels[27:] = 70.0
    result = impulsiveness_rise_speed(times, levels)
    assert result.slopes == ((20, 26),)
    assert result.rise_speed_db_per_s == pytest.approx(500.0)


@pytest.mark.parametrize(("rise_db", "counts"), [(9.5, False), (10.0, True)])
def test_a_slope_counts_from_a_rise_of_10_db(rise_db: float, *, counts: bool) -> None:
    """Annex A: a slope climbing 10,0 dB in 0,2 s counts, one climbing 9,5 dB does not."""
    times = np.arange(0.0, 1.0, 0.01)
    ramp = 60.0 + np.linspace(0.0, rise_db, 21)
    levels = np.concatenate(
        (np.full(20, 60.0), ramp, np.full(times.size - 41, ramp[-1]))
    )
    result = impulsiveness_rise_speed(times, levels)
    assert (result.slopes == ((20, 40),)) is counts
    if counts:
        assert result.rise_speed_db_per_s == pytest.approx(rise_db / 0.2)
    else:
        assert result.rise_speed_db_per_s is None


def test_the_rise_speed_result_holds_tuples() -> None:
    """Built directly from lists, the slopes and speeds are held as tuples."""
    result = environment.RiseSpeedResult(
        times_s=[0.0, 0.01], levels_db=[60.0, 61.0], slopes=[[0, 1]],
        rise_speeds_db_per_s=[100.0],
    )  # fmt: skip
    assert result.slopes == ((0, 1),)
    assert result.rise_speeds_db_per_s == (100.0,)


def test_no_slope_rising_10_db_gives_no_rise_speed() -> None:
    """A history that never climbs 10 dB without a break has no rise speed."""
    times = np.arange(0.0, 1.0, 0.01)
    result = impulsiveness_rise_speed(times, 60.0 + 5.0 * np.sin(2 * np.pi * times))
    assert result.rise_speed_db_per_s is None


def test_the_times_have_to_increase() -> None:
    """A derivative needs increasing times."""
    with pytest.raises(ValueError, match="'times_s' must increase"):
        impulsiveness_rise_speed([0.0, 0.0, 0.1], [60.0, 61.0, 62.0])


@pytest.mark.parametrize(
    ("with_adjacent", "unit", "difference", "neutral"),
    [
        (83.04, 81.05, 1.9, True),
        (83.05, 81.1, 2.0, True),
        (83.15, 81.1, 2.1, False),
    ],
)
def test_neutrality_is_judged_on_levels_rounded_to_a_decimal(
    with_adjacent: float, unit: float, difference: float, *, neutral: bool
) -> None:
    """6.3.4: no more than 2,0 dB, both levels rounded to one decimal first."""
    verdict = check_adjacent_vehicle_neutrality(with_adjacent, unit)
    assert verdict.difference_db == pytest.approx(difference)
    assert verdict.passes is neutral


def test_the_neutrality_plot_writes_the_levels_under_the_bars() -> None:
    """83,0 dB ends 0,1 dB under the allowance line, so the levels go in the tick labels."""
    ax = check_adjacent_vehicle_neutrality(83.0, 81.1).plot(language="es")
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels == [
        "Unidades en ensayo\n81,1 dB",
        "Con el vehículo contiguo\n83,0 dB",
    ]
    assert len(ax.texts) == 0
    plt.close(ax.figure)


def test_a_verdict_has_no_truth_value() -> None:
    """The verdict is read from .passes."""
    verdict = check_adjacent_vehicle_neutrality(83.0, 81.0)
    with pytest.raises(TypeError, match="has no truth value; read its '.passes'"):
        bool(verdict)


def test_the_background_increase_is_formula_d_1() -> None:
    """60 dB over a 55 dB background: 60 - 10 lg(10**6 - 10**5.5) dB."""
    expected = 60.0 - 10.0 * math.log10(10**6.0 - 10**5.5)
    assert background_level_increase(60.0, 55.0) == pytest.approx(expected)
    bands = background_level_increase([60.0, 70.0], [50.0, 60.0])
    assert isinstance(bands, np.ndarray)
    np.testing.assert_allclose(bands, [bands[0], bands[0]])


@pytest.mark.parametrize(
    ("measured_db", "background_db"),
    [(60.0, 57.0), (64.4, 61.4), (66.9, 63.9)],
)
def test_the_background_correction_needs_more_than_3_db(
    measured_db: float, background_db: float
) -> None:
    """D.4.2 applies it only above 3 dB of excess; 64,4 - 61,4 is 3 dB, though binary lands it a hair above."""
    with pytest.raises(ValueError, match="D.4.2 applies the correction only where"):
        background_level_increase(measured_db, background_db)


def test_no_decimal_level_exactly_3_db_up_is_corrected() -> None:
    """Every tenth of a decibel from 50,0 dB to 99,9 dB over a background 3,0 dB below is refused."""
    measured = np.round(np.arange(500, 1000) / 10.0, 1)
    background = np.round(measured - 3.0, 1)
    accepted = []
    for level, floor in zip(measured, background, strict=True):
        try:
            background_level_increase(float(level), float(floor))
        except ValueError:
            continue
        accepted.append((float(level), float(floor)))
    assert accepted == []


def test_the_background_correction_takes_an_excess_of_3_1_db() -> None:
    """3,1 dB over the background is more than 3 dB, and Formula D.1 applies."""
    expected = 60.0 - 10.0 * math.log10(10**6.0 - 10**5.69)
    assert background_level_increase(60.0, 56.9) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Annexes C and E
# ---------------------------------------------------------------------------


def test_roughness_below_the_limit_changes_nothing() -> None:
    """C.2.1: the corrected spectrum is the measured one; no correction, no effect."""
    verdict = check_small_roughness_deviations(
        _limit_spectrum(-1.0),
        np.full(len(_NOISE_BANDS_HZ), 70.0),
        frequencies_hz=_NOISE_BANDS_HZ,
        speed_kmh=80.0,
    )
    assert verdict.exceeded is False
    np.testing.assert_allclose(verdict.roughness_correction_db, 0.0, atol=1e-12)
    assert verdict.impact_db == pytest.approx(0.0, abs=1e-12)
    assert verdict.passes is True


def test_two_rails_on_the_limit_do_not_exceed_it() -> None:
    """C.2.1 and 6.2.5 agree that roughness on the limit does not exceed it.

    The quadratic average of two rails on Figure 2 is Figure 2, but binary
    arithmetic brings the 6,3 cm and 1,6 cm bands back a few units in the last
    place above 0,9 dB and -6,8 dB.
    """
    rail = _limit_spectrum()
    averaged = average_roughness_spectra([rail, rail])
    np.testing.assert_allclose(averaged.levels_db, rail.levels_db, rtol=0, atol=1e-12)
    verdict = check_small_roughness_deviations(
        averaged,
        np.full(len(_NOISE_BANDS_HZ), 70.0),
        frequencies_hz=_NOISE_BANDS_HZ,
        speed_kmh=80.0,
    )
    assert verdict.exceeded is False
    check = check_reference_track(
        [averaged],
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=80.0,
    )
    assert check.passes is True


def test_one_band_over_the_limit_at_36_kmh_corrects_one_noise_band() -> None:
    """At 10 m/s the 4 cm band carries onto 250 Hz whole: 3 dB there, 0 elsewhere."""
    roughness = _limit_spectrum(-1.0)
    levels = np.array(roughness.levels_db)
    index = roughness.bands.index(14)  # 4 cm
    levels[index] = REFERENCE_TRACK_ROUGHNESS_LIMIT_DB[0.04] + 3.0
    roughness = AcousticRoughnessSpectrum(roughness.wavelengths_m, levels)
    noise = np.full(len(_NOISE_BANDS_HZ), 70.0)
    verdict = check_small_roughness_deviations(
        roughness, noise, frequencies_hz=_NOISE_BANDS_HZ, speed_kmh=_ALIGNED_SPEED_KMH
    )
    correction = np.zeros(len(_NOISE_BANDS_HZ))
    correction[_NOISE_BANDS_HZ.index(250.0)] = 3.0
    np.testing.assert_allclose(verdict.roughness_correction_db, correction, atol=1e-9)
    count = len(_NOISE_BANDS_HZ)
    expected = 10.0 * math.log10(count) - 10.0 * math.log10(count - 1 + 10**-0.3)
    assert verdict.impact_db == pytest.approx(expected, abs=1e-9)
    assert verdict.passes is True


def test_a_large_exceedance_is_not_accepted() -> None:
    """The same band 20 dB over, in a spectrum that band dominates, moves it over 1 dB."""
    roughness = _limit_spectrum(-1.0)
    levels = np.array(roughness.levels_db)
    levels[roughness.bands.index(14)] = REFERENCE_TRACK_ROUGHNESS_LIMIT_DB[0.04] + 20.0
    roughness = AcousticRoughnessSpectrum(roughness.wavelengths_m, levels)
    noise = np.full(len(_NOISE_BANDS_HZ), 60.0)
    noise[_NOISE_BANDS_HZ.index(250.0)] = 80.0
    verdict = check_small_roughness_deviations(
        roughness, noise, frequencies_hz=_NOISE_BANDS_HZ, speed_kmh=_ALIGNED_SPEED_KMH
    )
    assert verdict.impact_db > 1.0
    assert verdict.passes is False
    with pytest.raises(TypeError, match="has no truth value; read its '.passes'"):
        bool(verdict)


#: The exceedance at 4 cm whose effect is 1 dB in the closed form below.
_ONE_DB_EXCEEDANCE = -10.0 * math.log10((124.0 / 10.0**0.1 - 24.0) / 100.0)


@pytest.mark.parametrize(
    ("exceedance_db", "accepted"),
    [(1.21, True), (_ONE_DB_EXCEEDANCE, True), (1.30, False)],
)
def test_annex_c_accepts_an_effect_of_1_db_and_no_more(
    exceedance_db: float, *, accepted: bool
) -> None:
    """C.3: effects of about 0,95 dB and of 1 dB are accepted, one of about 1,02 dB is not.

    At 36 km/h the 4 cm band corrects 250 Hz alone, and a noise spectrum
    of 60 dB with 80 dB at 250 Hz gives the effect in closed form,
    10 lg(24 + 10^2) - 10 lg(24 + 10^(2 - x/10)).
    """
    roughness = _limit_spectrum(-1.0)
    levels = np.array(roughness.levels_db)
    levels[roughness.bands.index(14)] = (
        REFERENCE_TRACK_ROUGHNESS_LIMIT_DB[0.04] + exceedance_db
    )
    roughness = AcousticRoughnessSpectrum(roughness.wavelengths_m, levels)
    noise = np.full(len(_NOISE_BANDS_HZ), 60.0)
    noise[_NOISE_BANDS_HZ.index(250.0)] = 80.0
    verdict = check_small_roughness_deviations(
        roughness, noise, frequencies_hz=_NOISE_BANDS_HZ, speed_kmh=_ALIGNED_SPEED_KMH
    )
    expected = 10.0 * math.log10(24.0 + 100.0) - 10.0 * math.log10(
        24.0 + 100.0 * 10.0 ** (-exceedance_db / 10.0)
    )
    assert abs(expected - 1.0) < 0.06  # 0,948 dB, 1 dB and 1,016 dB
    assert verdict.impact_db == pytest.approx(expected, abs=1e-9)
    assert verdict.passes is accepted


def test_the_annex_c_plot_names_both_spectra() -> None:
    """The two curves are the measured and the revised noise spectrum."""
    verdict = check_small_roughness_deviations(
        _limit_spectrum(-1.0),
        np.full(len(_NOISE_BANDS_HZ), 70.0),
        frequencies_hz=_NOISE_BANDS_HZ,
        speed_kmh=80.0,
    )
    ax = verdict.plot(language="es")
    assert ax.get_legend_handles_labels()[1] == ["Espectro medido", "Espectro revisado"]
    plt.close(ax.figure)


def test_annex_e_bounds_a_one_band_difference() -> None:
    """Situation 2 is 5 dB rougher in one band: the bound is what 5 dB does to it."""
    one = _limit_spectrum(-2.0)
    levels = np.array(one.levels_db)
    levels[one.bands.index(14)] += 5.0
    two = AcousticRoughnessSpectrum(one.wavelengths_m, levels)
    noise_1 = np.full(len(_NOISE_BANDS_HZ), 70.0)
    noise_2 = np.full(len(_NOISE_BANDS_HZ), 72.0)
    result = roughness_comparability(
        one,
        two,
        noise_1,
        noise_2,
        frequencies_hz=_NOISE_BANDS_HZ,
        speed_kmh=_ALIGNED_SPEED_KMH,
    )
    count = len(_NOISE_BANDS_HZ)
    up = 10.0 * math.log10(count) - 10.0 * math.log10(count - 1 + 10**0.5)
    down = 10.0 * math.log10(count) - 10.0 * math.log10(count - 1 + 10**-0.5)
    min_1, max_1, min_2, max_2 = result.level_differences_db
    assert min_1 == pytest.approx(0.0, abs=1e-9)
    assert max_1 == pytest.approx(up, abs=1e-9)
    assert min_2 == pytest.approx(down, abs=1e-9)
    assert max_2 == pytest.approx(0.0, abs=1e-9)
    assert result.bound_db == pytest.approx(abs(up), abs=1e-9)
    np.testing.assert_allclose(result.envelope_min.levels_db, one.levels_db)
    np.testing.assert_allclose(result.envelope_max.levels_db, two.levels_db)


def test_annex_e_needs_a_band_in_common() -> None:
    """Two spectra with no band in common cannot be compared."""
    one = AcousticRoughnessSpectrum([0.25, 0.2], [0.0, 0.0])
    two = AcousticRoughnessSpectrum([0.01, 0.008], [0.0, 0.0])
    noise = np.full(3, 70.0)
    with pytest.raises(
        ValueError, match="two roughness spectra have no band in common"
    ):
        roughness_comparability(
            one, two, noise, noise, frequencies_hz=[500.0, 630.0, 800.0], speed_kmh=80.0
        )


# ---------------------------------------------------------------------------
# 6.2: the reference track
# ---------------------------------------------------------------------------


def _decay_at(scale: float, direction: str) -> TrackDecayRate:
    limit = REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M[direction]
    return TrackDecayRate(direction, list(limit), [scale * v for v in limit.values()])


def test_a_track_inside_every_limit_passes() -> None:
    """Roughness 1 dB under Figure 2, decay rates 10 % over Figure 3."""
    check = check_reference_track(
        [_limit_spectrum(-1.0), _limit_spectrum(-1.5)],
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=160.0,
        curve_radius_m=6000.0,
        track_gradient_ratio=0.004,
    )
    assert check.passes is True
    assert check.failed == ()
    assert [c.clause for c in check.conditions] == [
        "6.2.5", "6.2.5", "6.2.6", "6.2.6", "6.2.2", "6.2.2",
    ]  # fmt: skip


def test_the_roughness_limit_is_judged_in_every_band() -> None:
    """One band 0,5 dB over the limit fails 6.2.5 without Annex C."""
    roughness = _limit_spectrum(-1.0)
    levels = np.array(roughness.levels_db)
    levels[5] += 1.5
    check = check_reference_track(
        [AcousticRoughnessSpectrum(roughness.wavelengths_m, levels)],
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=80.0,
    )
    assert check.passes is False
    assert [c.requirement for c in check.failed] == [
        "roughness at or below the limit of Figure 2"
    ]


def test_annex_c_accepts_a_small_exceedance() -> None:
    """The same exceedance passes when Annex C finds its effect at most 1 dB."""
    roughness = _limit_spectrum(-1.0)
    levels = np.array(roughness.levels_db)
    levels[roughness.bands.index(14)] += 1.5
    roughness = AcousticRoughnessSpectrum(roughness.wavelengths_m, levels)
    annex_c = check_small_roughness_deviations(
        roughness,
        np.full(len(_NOISE_BANDS_HZ), 70.0),
        frequencies_hz=_NOISE_BANDS_HZ,
        speed_kmh=_ALIGNED_SPEED_KMH,
    )
    check = check_reference_track(
        [roughness],
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=_ALIGNED_SPEED_KMH,
        small_deviations=annex_c,
    )
    assert check.passes is True
    assert "Annex C" in check.conditions[1].requirement
    assert check.small_deviations is annex_c
    ax = check.plot()
    assert ax.get_title() == (
        "Reference track, ISO 3095 6.2: passes (Annex C, $\\Delta L$ = 0.02 dB)"
    )
    plt.close(ax.figure)


def test_a_track_within_the_limit_keeps_no_annex_c_verdict() -> None:
    """Annex C is not needed where the roughness is under the limit, and not shown."""
    roughness = _limit_spectrum(-1.0)
    annex_c = _annex_c(roughness, 80.0)
    check = check_reference_track(
        [roughness],
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=80.0,
        small_deviations=annex_c,
    )
    assert check.passes is True
    assert check.small_deviations is None
    assert [c.requirement for c in check.conditions][1] == (
        "roughness at or below the limit of Figure 2"
    )


def test_the_roughness_reaches_down_to_3_mm() -> None:
    """6.2.5: a spectrum that stops at 4 mm misses the 3,15 mm band."""
    wavelengths = [w for w in REFERENCE_TRACK_ROUGHNESS_LIMIT_DB if w >= 0.004]
    short = AcousticRoughnessSpectrum(
        wavelengths, [REFERENCE_TRACK_ROUGHNESS_LIMIT_DB[w] - 1.0 for w in wavelengths]
    )
    decay = [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")]
    check = check_reference_track([short], decay, speed_kmh=80.0)
    assert check.passes is False
    assert [(c.requirement, c.detail) for c in check.failed] == [
        ("roughness measured from 0.003 m to 0.1 m", "missing 0.00315 m")
    ]


def test_above_190_kmh_the_roughness_reaches_0_25_m() -> None:
    """6.2.5: a spectrum that stops at 0,1 m will do at 190 km/h and is short at 195 km/h.

    Above 190 km/h one that reaches 0,25 m will do.
    """
    wavelengths = [w for w in REFERENCE_TRACK_ROUGHNESS_LIMIT_DB if w <= 0.1]
    short = AcousticRoughnessSpectrum(
        wavelengths, [REFERENCE_TRACK_ROUGHNESS_LIMIT_DB[w] - 1.0 for w in wavelengths]
    )
    decay = [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")]
    assert check_reference_track([short], decay, speed_kmh=190.0).passes is True
    for speed in (195.0, 250.0):
        fast = check_reference_track([short], decay, speed_kmh=speed)
        assert fast.passes is False
        assert "0.25 m" in fast.failed[0].detail
    wavelengths = [w for w in REFERENCE_TRACK_ROUGHNESS_LIMIT_DB if w <= 0.25]
    enough = AcousticRoughnessSpectrum(
        wavelengths, [REFERENCE_TRACK_ROUGHNESS_LIMIT_DB[w] - 1.0 for w in wavelengths]
    )
    assert check_reference_track([enough], decay, speed_kmh=250.0).passes is True


def test_both_decay_directions_are_required() -> None:
    """6.2.6 judges the vertical and the lateral rates; one missing is not a pass."""
    check = check_reference_track(
        [_limit_spectrum(-1.0)], [_decay_at(1.1, "vertical")], speed_kmh=80.0
    )
    assert check.passes is False
    assert check.failed == ()
    assert check.conditions[3].holds is None


def test_a_decay_rate_below_its_limit_fails() -> None:
    """The lateral rate 5 % under Figure 3 fails 6.2.6."""
    check = check_reference_track(
        [_limit_spectrum(-1.0)],
        [_decay_at(1.1, "vertical"), _decay_at(0.95, "lateral")],
        speed_kmh=80.0,
    )
    assert [c.requirement for c in check.failed] == [
        "lateral decay rate at or above the limit of Figure 3"
    ]


def _measured_lateral(
    scale: float, *, flat_band_hz: float | None = None
) -> TrackDecayRate:
    """Lateral responses on the grid of Figure 2 decaying at ``scale`` times Figure 3.

    With ``flat_band_hz``, one more band below the limits whose response stays
    flat to the last position and then drops 20 dB: Formula 1 reads it about
    0,12 dB/m, under twice the floor of Formula 2, while it drops far enough.
    """
    positions = track_decay_excitation_positions()
    limit = REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M["lateral"]
    rates = np.array(list(limit.values())) * scale
    responses = np.exp(-np.outer(positions, rates / (20 * math.log10(math.e))))
    frequencies = list(limit)
    if flat_band_hz is not None:
        flat = np.ones((positions.size, 1))
        flat[-1] = 0.1
        responses = np.hstack([flat, responses])
        frequencies = [flat_band_hz, *frequencies]
    return track_decay_rate(responses, frequencies_hz=frequencies, direction="lateral")


def _en_15461_conditions(check: ReferenceTrackCheck) -> dict[str, bool | None]:
    return {
        c.clause: c.holds for c in check.conditions if c.clause.startswith("EN 15461")
    }


def test_measured_rates_bring_the_en_15461_checks_with_them() -> None:
    """With the grid known, the floor of Formula 2 and the 10 dB drop are judged.

    Lateral rates 1,5 times Figure 3 drop at least 0,30 x 39,6 = 11,9 dB over
    the grid, and every one is above twice 4,343/39,6 = 0,219 dB/m.
    """
    check = check_reference_track(
        [_limit_spectrum(-1.0)],
        [_decay_at(1.1, "vertical"), _measured_lateral(1.5)],
        speed_kmh=80.0,
    )
    assert _en_15461_conditions(check) == {"EN 15461 7": True, "EN 15461 6.7": True}
    assert check.passes is True


def test_a_set_that_drops_less_than_10_db_fails_en_15461_6_7() -> None:
    """Lateral rates 1,2 times Figure 3 drop 0,24 x 39,6 = 9,5 dB at 1 kHz and 1,25 kHz."""
    check = check_reference_track(
        [_limit_spectrum(-1.0)],
        [_decay_at(1.1, "vertical"), _measured_lateral(1.2)],
        speed_kmh=80.0,
    )
    assert _en_15461_conditions(check) == {"EN 15461 7": True, "EN 15461 6.7": False}
    assert check.passes is False
    assert [(c.clause, c.detail) for c in check.failed] == [
        ("EN 15461 6.7", "1 set(s) short of 10 dB")
    ]


def test_a_rate_under_twice_the_floor_fails_en_15461_7() -> None:
    """A 200 Hz band that reads about 0,12 dB/m is unsuitable, below 2 x 0,110 dB/m.

    Figure 3 sets no limit at 200 Hz and the response still drops 20 dB, so
    clause 7 alone fails.
    """
    check = check_reference_track(
        [_limit_spectrum(-1.0)],
        [_decay_at(1.1, "vertical"), _measured_lateral(1.5, flat_band_hz=200.0)],
        speed_kmh=80.0,
    )
    assert _en_15461_conditions(check) == {"EN 15461 7": False, "EN 15461 6.7": True}
    assert check.passes is False
    assert [(c.clause, c.detail) for c in check.failed] == [
        ("EN 15461 7", "1 band(s) unsuitable")
    ]


def _exceeding_roughness() -> AcousticRoughnessSpectrum:
    """1 dB under the limit but 0,5 dB over it in the 4 cm band."""
    roughness = _limit_spectrum(-1.0)
    levels = np.array(roughness.levels_db)
    levels[roughness.bands.index(14)] += 1.5
    return AcousticRoughnessSpectrum(roughness.wavelengths_m, levels)


def _annex_c(
    roughness: AcousticRoughnessSpectrum, speed_kmh: float
) -> SmallRoughnessDeviation:
    return check_small_roughness_deviations(
        roughness,
        np.full(len(_NOISE_BANDS_HZ), 70.0),
        frequencies_hz=_NOISE_BANDS_HZ,
        speed_kmh=speed_kmh,
    )


def test_an_annex_c_verdict_of_another_speed_is_refused() -> None:
    """C.3 examines each speed: a verdict at 36 km/h cannot accept a track at 250 km/h."""
    roughness = _exceeding_roughness()
    annex_c = _annex_c(roughness, _ALIGNED_SPEED_KMH)
    decay = [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")]
    with pytest.raises(ValueError, match="'small_deviations' was judged at 36 km/h"):
        check_reference_track(
            [roughness], decay, speed_kmh=250.0, small_deviations=annex_c
        )


def test_an_annex_c_verdict_of_another_roughness_is_refused() -> None:
    """C.2.1 averages the spectra judged; a verdict on other rails cannot accept these."""
    annex_c = _annex_c(_limit_spectrum(-3.0), _ALIGNED_SPEED_KMH)
    decay = [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")]
    roughness = [_exceeding_roughness()]
    with pytest.raises(
        ValueError, match="'small_deviations' was judged on another roughness"
    ):
        check_reference_track(
            roughness, decay, speed_kmh=_ALIGNED_SPEED_KMH, small_deviations=annex_c
        )


def test_annex_c_takes_the_average_of_the_rails() -> None:
    """Two rails are judged with the Annex C verdict on their quadratic average."""
    rails = [_exceeding_roughness(), _limit_spectrum(-2.0)]
    annex_c = _annex_c(environment.average_roughness_spectra(rails), _ALIGNED_SPEED_KMH)
    check = check_reference_track(
        rails,
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=_ALIGNED_SPEED_KMH,
        small_deviations=annex_c,
    )
    assert check.passes is True
    assert check.small_deviations is annex_c


def _stricter_limit() -> dict[float, float]:
    """Figure 2 lowered by 1 dB in every band."""
    return {w: v - 1.0 for w, v in REFERENCE_TRACK_ROUGHNESS_LIMIT_DB.items()}


def test_an_annex_c_verdict_against_another_limit_is_refused() -> None:
    """Formula C.1 holds the roughness down to the limit 6.2.5 judges it against.

    A verdict against Figure 2 cannot accept a track judged against a limit
    1 dB stricter, nor one against the stricter limit a track judged against
    Figure 2; the verdict against the limit the track is judged by is taken.
    """
    roughness = _exceeding_roughness()
    decay = [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")]
    stricter = _stricter_limit()
    figure_2 = _annex_c(roughness, _ALIGNED_SPEED_KMH)
    strict = check_small_roughness_deviations(
        roughness,
        np.full(len(_NOISE_BANDS_HZ), 70.0),
        frequencies_hz=_NOISE_BANDS_HZ,
        speed_kmh=_ALIGNED_SPEED_KMH,
        limit_db=stricter,
    )
    message = "'small_deviations' was judged against another roughness limit"
    with pytest.raises(ValueError, match=message):
        check_reference_track(
            [roughness],
            decay,
            speed_kmh=_ALIGNED_SPEED_KMH,
            small_deviations=figure_2,
            roughness_limit_db=stricter,
        )
    with pytest.raises(ValueError, match=message):
        check_reference_track(
            [roughness], decay, speed_kmh=_ALIGNED_SPEED_KMH, small_deviations=strict
        )
    check = check_reference_track(
        [roughness],
        decay,
        speed_kmh=_ALIGNED_SPEED_KMH,
        small_deviations=strict,
        roughness_limit_db=stricter,
    )
    assert check.passes is True
    assert check.small_deviations is strict


def test_a_track_verdict_never_holds_an_annex_c_verdict_of_another_limit() -> None:
    """Replacing the limit of a verdict that rests on Annex C is refused like the call."""
    roughness = _exceeding_roughness()
    check = check_reference_track(
        [roughness],
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=_ALIGNED_SPEED_KMH,
        small_deviations=_annex_c(roughness, _ALIGNED_SPEED_KMH),
    )
    assert check.small_deviations is not None
    stricter = _stricter_limit()
    with pytest.raises(
        ValueError,
        match="'small_deviations' was judged against another roughness limit",
    ):
        dataclasses.replace(check, roughness_limit_db=stricter)


def test_an_annex_c_verdict_records_the_limit_it_was_judged_against() -> None:
    """The limit is held read-only, and the corrected spectrum must be Formula C.1 of it."""
    limit = dict(REFERENCE_TRACK_ROUGHNESS_LIMIT_DB)
    annex_c = check_small_roughness_deviations(
        _exceeding_roughness(),
        np.full(len(_NOISE_BANDS_HZ), 70.0),
        frequencies_hz=_NOISE_BANDS_HZ,
        speed_kmh=_ALIGNED_SPEED_KMH,
        limit_db=limit,
    )
    limit[0.04] = 99.0
    assert annex_c.limit_db[0.04] == pytest.approx(
        REFERENCE_TRACK_ROUGHNESS_LIMIT_DB[0.04]
    )
    with pytest.raises(TypeError, match="does not support item assignment"):
        annex_c.limit_db[0.04] = 0.0  # type: ignore[index]
    stricter = _stricter_limit()
    with pytest.raises(
        ValueError, match="'corrected_roughness_levels_db' is not Formula C.1"
    ):
        dataclasses.replace(annex_c, limit_db=stricter)


def test_the_verdict_keeps_the_limits_it_was_judged_against() -> None:
    """Limits passed as plain dicts are copied read-only; changing them later changes nothing."""
    roughness_limit = dict(REFERENCE_TRACK_ROUGHNESS_LIMIT_DB)
    decay_limits = {
        d: dict(v) for d, v in REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M.items()
    }
    check = check_reference_track(
        [_limit_spectrum(-1.0)],
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=80.0,
        roughness_limit_db=roughness_limit,
        decay_limits_db_per_m=decay_limits,
    )
    roughness_limit[0.4] = 99.0
    decay_limits["vertical"][250.0] = 0.0
    assert check.roughness_limit_db[0.4] == pytest.approx(17.1)
    assert check.decay_limits_db_per_m["vertical"][250.0] == pytest.approx(2.0)
    with pytest.raises(TypeError, match="does not support item assignment"):
        check.decay_limits_db_per_m["vertical"][250.0] = 0.0  # type: ignore[index]


def test_the_curve_radius_and_the_gradient() -> None:
    """6.2.2: 3 000 m at 100 km/h; 5:1 000 at most."""
    check = check_reference_track(
        [_limit_spectrum(-1.0)],
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=100.0,
        curve_radius_m=2500.0,
        track_gradient_ratio=-0.006,
    )
    assert [c.detail for c in check.failed] == ["2500 m", "6:1 000"]


@pytest.mark.parametrize(
    ("radius_m", "gradient", "failed"),
    [
        (3000.0, 0.005, []),
        (2990.0, 0.0051, ["2990 m", "5.1:1 000"]),
    ],
)
def test_the_curve_radius_and_the_gradient_at_their_limits(
    radius_m: float, gradient: float, failed: list[str]
) -> None:
    """6.2.2: 3 000 m and 5:1 000 themselves are accepted; 2 990 m and 5,1:1 000 are not."""
    check = check_reference_track(
        [_limit_spectrum(-1.0)],
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=100.0,
        curve_radius_m=radius_m,
        track_gradient_ratio=gradient,
    )
    assert [c.detail for c in check.failed] == failed


@pytest.mark.parametrize(
    ("limits", "message"),
    [
        (
            {"vertical": {250.0: 1.0}},
            "'decay_limits_db_per_m' has no limit for the lateral direction.",
        ),
        (
            {"vertical": {}, "lateral": {250.0: 1.0}},
            "'decay_limits_db_per_m' has no band in the vertical limit.",
        ),
        (
            {"vertical": {250.0: 1.0}, "lateral": {250.0: 1.0}, "axial": {}},
            "'decay_limits_db_per_m' has an unknown direction 'axial'.",
        ),
        (
            {"vertical": {250.0: 5.0, 251.0: 1.0}, "lateral": {250.0: 1.0}},
            "'decay_limits_db_per_m' has 250 Hz and 251 Hz in one one-third "
            "octave band of the vertical limit.",
        ),
        (
            {"vertical": {250.0: 1.0}, "lateral": {0.0: 1.0}},
            "'decay_limits_db_per_m' must be strictly positive.",
        ),
    ],
    ids=["missing", "empty", "unknown", "one-band-twice", "zero-hertz"],
)
def test_decay_limits_need_both_directions_and_no_other(
    limits: dict[str, dict[float, float]], message: str
) -> None:
    """Custom limits that leave out a direction, or give one band two rates, are refused by name."""
    roughness = [_limit_spectrum(-1.0)]
    decay = [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")]
    with pytest.raises(ValueError, match=f"^{message}$"):
        check_reference_track(
            roughness, decay, speed_kmh=80.0, decay_limits_db_per_m=limits
        )


def test_a_verdict_never_holds_a_decay_limit_it_did_not_apply() -> None:
    """Of 5 dB/m at 250 Hz and 1 dB/m at 251 Hz only one could be judged; neither verdict is built."""
    limits = {"vertical": {250.0: 5.0, 251.0: 1.0}, "lateral": {250.0: 1.0}}
    rates = [
        TrackDecayRate(direction, [250.0, 315.0], [3.0, 3.0])
        for direction in TRACK_DECAY_DIRECTIONS
    ]
    with pytest.raises(
        ValueError, match="250 Hz and 251 Hz in one one-third octave band"
    ):
        check_reference_track([], rates, speed_kmh=80.0, decay_limits_db_per_m=limits)
    check = check_reference_track([], rates, speed_kmh=80.0)
    with pytest.raises(
        ValueError, match="250 Hz and 251 Hz in one one-third octave band"
    ):
        dataclasses.replace(check, decay_limits_db_per_m=limits)


def test_a_roughness_limit_gives_one_level_per_band() -> None:
    """0,4 m and 0,41 m name one band; the 6.2.5 verdict and Annex C refuse the limit by name."""
    limit = {**REFERENCE_TRACK_ROUGHNESS_LIMIT_DB, 0.41: 0.0}
    roughness = [_limit_spectrum(-1.0)]
    decay = [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")]
    exceeding = _exceeding_roughness()
    noise = np.full(len(_NOISE_BANDS_HZ), 70.0)
    with pytest.raises(
        ValueError,
        match=r"^'roughness_limit_db' has 0\.4 m and 0\.41 m in one one-third octave band\.$",
    ):
        check_reference_track(
            roughness, decay, speed_kmh=80.0, roughness_limit_db=limit
        )
    with pytest.raises(
        ValueError,
        match=r"^'limit_db' has 0\.4 m and 0\.41 m in one one-third octave band\.$",
    ):
        check_small_roughness_deviations(
            exceeding,
            noise,
            frequencies_hz=_NOISE_BANDS_HZ,
            speed_kmh=_ALIGNED_SPEED_KMH,
            limit_db=limit,
        )


def test_a_track_verdict_has_no_truth_value() -> None:
    """The verdict is read from .passes."""
    check = check_reference_track([], [], speed_kmh=80.0)
    with pytest.raises(TypeError, match="has no truth value; read its '.passes'"):
        bool(check)


def test_the_track_plot_draws_either_panel() -> None:
    """The roughness panel against Figure 2, the decay panel against Figure 3."""
    check = check_reference_track(
        [_limit_spectrum(-1.0)],
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=80.0,
    )
    rough = check.plot(language="es")
    assert rough.get_title().endswith("cumple")
    decay = check.plot(panel="decay")
    assert decay.get_yscale() == "log"
    for ax in (rough, decay):
        plt.close(ax.figure)


def test_the_decay_panel_numbers_the_sets_of_a_direction_only_when_there_are_two() -> (
    None
):
    """One set a direction reads "Vertical"; two lateral sets read "Lateral 1" and "2"."""
    one_each = check_reference_track(
        [_limit_spectrum(-1.0), _limit_spectrum(-2.0)],
        [_decay_at(1.1, "vertical"), _decay_at(1.1, "lateral")],
        speed_kmh=80.0,
    )
    ax = one_each.plot(panel="decay")
    labels = ax.get_legend_handles_labels()[1]
    assert labels[:2] == ["Vertical", "Lateral"]
    plt.close(ax.figure)
    ax = one_each.plot(panel="roughness")
    assert ax.get_legend_handles_labels()[1][:2] == ["Measured 1", "Measured 2"]
    plt.close(ax.figure)
    two_lateral = check_reference_track(
        [_limit_spectrum(-1.0)],
        [
            _decay_at(1.1, "lateral"),
            _decay_at(1.1, "vertical"),
            _decay_at(1.2, "lateral"),
        ],
        speed_kmh=80.0,
    )
    ax = two_lateral.plot(panel="decay", language="es")
    labels = ax.get_legend_handles_labels()[1]
    assert labels[:3] == ["Lateral 1", "Vertical", "Lateral 2"]
    plt.close(ax.figure)


@pytest.mark.parametrize(
    ("method", "english", "spanish"),
    [
        ("constant_speed", "constant speed", "velocidad constante"),
        ("acceleration_maximum", "starting, maximum level", "arranque, nivel máximo"),
        (
            "acceleration_averaged",
            "starting, averaged level",
            "arranque, nivel promediado",
        ),
        ("braking", "braking", "frenado"),
    ],
)
def test_a_test_plot_is_titled_with_its_method_in_words(
    method: str, english: str, spanish: str
) -> None:
    """The title names the test in words, not by its identifier."""
    result = rolling_stock_test({"a": [80.0, 81.0, 80.5]}, method=method)
    ax = result.plot()
    assert ax.get_title() == f"ISO 3095 test: {english}"
    plt.close(ax.figure)
    ax = result.plot(language="es")
    assert ax.get_title() == f"Ensayo ISO 3095: {spanish}"
    plt.close(ax.figure)


def test_two_inputs_of_the_same_name_are_refused() -> None:
    """Each input has its own share of the variance, so each needs a name of its own."""
    inputs = [
        metrology.Quantity(0.0, 0.1, name="distance"),
        metrology.Quantity(0.0, 0.2, name="distance"),
    ]
    with pytest.raises(ValueError, match="needs a name of its own.*repeated: distance"):
        pass_by_uncertainty(55.0, inputs)


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        (["", "x1"], ("x1'", "x1")),
        (["x2", ""], ("x2", "x2'")),
        (["", "x1", "x1'"], ("x1''", "x1", "x1'")),
        (["", "", "x3"], ("x1", "x2", "x3")),
    ],
)
def test_an_unnamed_input_never_takes_a_name_given_to_another(
    names: list[str], expected: tuple[str, ...]
) -> None:
    """An input without a name is called by its place, primed when that name was given to another."""
    budget = pass_by_uncertainty(
        55.0,
        [metrology.Quantity(0.0, 0.1 * (i + 1), name=n) for i, n in enumerate(names)],
    )
    assert budget.names == expected
    assert tuple(budget.variance_ratios) == expected


def test_the_uncertainty_plot_is_figure_g1() -> None:
    """The bars are drawn in the order Figure G.1 prints its labels."""
    budget = pass_by_uncertainty(
        ref.TABLE_G2_READING_DB,
        [metrology.Quantity(v, u, name=n) for n, v, u in ref.TABLE_G2_ROWS],
    )
    ax = budget.plot()
    labels = tuple(t.get_text() for t in ax.get_xticklabels())
    assert labels == ref.FIGURE_G1_ORDER
    plt.close(ax.figure)


def test_the_figure_2_limit_is_the_cnossos_class_e_rail_roughness() -> None:
    """Appendix G names class E after ISO 3095 and prints the same 22 levels."""
    wavelengths_mm, levels = environment.rail_roughness("E")
    class_e = {
        round(float(w) / 1000.0, 5): float(v)
        for w, v in zip(wavelengths_mm, levels, strict=True)
    }
    for wavelength, level in REFERENCE_TRACK_ROUGHNESS_LIMIT_DB.items():
        assert class_e[wavelength] == pytest.approx(level, abs=1e-12)


def test_the_environment_package_publishes_the_module() -> None:
    """Every name is reachable from phonometry.environment."""
    assert environment.check_reference_track is check_reference_track
    assert (
        environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB
        is REFERENCE_TRACK_ROUGHNESS_LIMIT_DB
    )
