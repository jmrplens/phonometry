#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Amplitude modulation at a receptor (IEC TS 61400-11-2:2024, clause 13).

The oracle is the IOA AMWG reference code: its three sample series with the
results it printed, and synthetic blocks and periods run through the
unmodified code (``tests/reference_data/wind_turbine_receptor.py``). The
implementation is written from the TS and the AMWG Final Report; these tests
hold it to the code's numbers on the steps the two share, and to the TS where
the TS departs from the AMWG (a period under 30 valid blocks is rated 0 dB
rather than discarded).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from reference_data import wind_turbine_receptor as ref

from phonometry import environment as env
from phonometry.environment.assessment import wind_turbine_modulation as wtm
from phonometry.filters import weighting_compliance

if TYPE_CHECKING:
    from collections.abc import Callable


def _sample(band: int) -> np.ndarray:
    return np.asarray(ref.IOA_SAMPLE_SERIES_TENTHS_DB[band][:100]) / 10.0


@pytest.mark.parametrize("band", [1, 2, 3])
@pytest.mark.parametrize("frequency_range", ref.IOA_SAMPLE_RANGES_HZ)
def test_sample_series_reproduce_the_printed_ioa_results(
    band: int, frequency_range: tuple[float, float]
) -> None:
    prominence, frequency, depth = ref.IOA_SAMPLE_RESULTS[band]
    block = env.amplitude_modulation_block(
        _sample(band), modulation_frequency_range_hz=frequency_range
    )
    assert block.valid
    assert round(block.prominence, 2) == prominence
    assert round(block.fundamental_frequency_hz, 2) == frequency
    assert round(block.modulation_depth_db, 2) == depth


def test_the_spectrum_is_half_the_ioa_code_s_over_its_49_lines() -> None:
    """Equation (12) from the positive lines only, 0.1 Hz to 4.9 Hz (13.6.2.3 c))."""
    block = env.amplitude_modulation_block(
        _sample(2), modulation_frequency_range_hz=(0.4, 0.9)
    )
    np.testing.assert_allclose(block.frequencies_hz, np.arange(1, 50) / 10.0)
    np.testing.assert_allclose(
        2.0 * block.power_spectrum, ref.IOA_SAMPLE_2_POWER_SPECTRUM, rtol=1e-12
    )


@pytest.mark.parametrize(
    "case", ref.IOA_BLOCK_CASES, ids=[c[0] for c in ref.IOA_BLOCK_CASES]
)
def test_synthetic_blocks_agree_with_the_ioa_code(
    case: tuple[str, tuple[float, float], tuple[int, ...], float, float, float],
) -> None:
    _, frequency_range, values, prominence, frequency, depth = case
    block = env.amplitude_modulation_block(
        np.asarray(values) / 10.0, modulation_frequency_range_hz=frequency_range
    )
    if depth > 0.0:
        assert block.status is env.ModulationBlockStatus.VALID
        assert block.prominence == pytest.approx(prominence, rel=1e-10)
        assert block.fundamental_frequency_hz == pytest.approx(frequency, abs=1e-9)
        assert block.modulation_depth_db == pytest.approx(depth, abs=1e-10)
    elif prominence > 0.0:
        assert block.status is env.ModulationBlockStatus.LOW_PROMINENCE
        assert block.prominence == pytest.approx(prominence, rel=1e-10)
        assert block.modulation_depth_db is None
    else:
        assert block.status is env.ModulationBlockStatus.NO_PEAK
        assert block.prominence is None
        assert block.fundamental_frequency_hz is None


def test_the_third_harmonic_is_found_two_lines_off_its_estimate() -> None:
    """Three times 0.5 Hz is 1.5 Hz; the local maximum is at 1.7 Hz (13.6.2.3 f)."""
    case = next(
        c for c in ref.IOA_BLOCK_CASES if c[0] == "third harmonic off its estimate"
    )
    block = env.amplitude_modulation_block(
        np.asarray(case[2]) / 10.0, modulation_frequency_range_hz=case[1]
    )
    assert block.harmonic_frequencies_hz == pytest.approx((1.0, 1.7))


@pytest.mark.parametrize(
    ("name", "included"),
    [
        ("fundamental under 1.5 dB", (0.9, 1.0, 1.1)),
        ("fundamental under 1.5 dB, second harmonic over it", (0.4, 0.5, 0.6)),
        ("fundamental just under 1.5 dB", (0.4, 0.5, 0.6)),
    ],
)
def test_a_weak_fundamental_keeps_no_harmonic(
    name: str, included: tuple[float, ...]
) -> None:
    """Under 1.5 dB peak to peak the harmonics are not added (13.6.2.3 f)).

    In the second and third blocks the harmonic alone swings over 1.5 dB and
    is a local maximum, so only the fundamental's own condition keeps it
    out; the IOA code gives the depth of the fundamental alone.
    """
    case = next(c for c in ref.IOA_BLOCK_CASES if c[0] == name)
    block = env.amplitude_modulation_block(
        np.asarray(case[2]) / 10.0, modulation_frequency_range_hz=case[1]
    )
    assert block.valid
    assert block.harmonic_frequencies_hz == ()
    assert block.included_frequencies_hz == pytest.approx(included)
    assert block.modulation_depth_db == pytest.approx(case[5], abs=1e-10)


@pytest.mark.parametrize(
    ("name", "swing_db"),
    [
        ("fundamental under 1.5 dB, second harmonic over it", 1.4137),
        ("fundamental just under 1.5 dB", 1.4989),
        ("fundamental just over 1.5 dB", 1.5028),
    ],
)
def test_the_gate_blocks_harmonic_passes_its_own_condition(
    name: str, swing_db: float
) -> None:
    """The harmonic of each gate block is a local maximum swinging over 1.5 dB.

    So the fundamental's swing, on either side of 1.5 dB, is all that decides.
    """
    case = next(c for c in ref.IOA_BLOCK_CASES if c[0] == name)
    block = env.amplitude_modulation_block(
        np.asarray(case[2]) / 10.0, modulation_frequency_range_hz=case[1]
    )
    transform = np.fft.fft(block.detrended_db)
    fundamental = wtm._swing(wtm._reconstruct(transform, [4, 5, 6]))
    harmonic = wtm._swing(wtm._reconstruct(transform, [9, 10, 11]))
    assert fundamental == pytest.approx(swing_db, abs=5e-5)
    assert harmonic > 1.5
    spectrum = block.power_spectrum
    assert spectrum[9] > max(spectrum[8], spectrum[10])


def test_a_fundamental_just_over_1_5_db_keeps_its_harmonic() -> None:
    """1.503 dB peak to peak lets the harmonic in (13.6.2.3 f)).

    With the block that swings 1.499 dB, which differs from this one in a
    single value (sample 75, 40.1 dB there and 40.0 dB here), the
    fundamental's own condition is held on both sides of 1.5 dB: the IOA
    code's depth here is that of the fundamental with the harmonic.
    """
    case = next(
        c for c in ref.IOA_BLOCK_CASES if c[0] == "fundamental just over 1.5 dB"
    )
    under = next(
        c for c in ref.IOA_BLOCK_CASES if c[0] == "fundamental just under 1.5 dB"
    )
    differ = [
        (i, a, b)
        for i, (a, b) in enumerate(zip(under[2], case[2], strict=True))
        if a != b
    ]
    assert differ == [(74, 401, 400)]
    block = env.amplitude_modulation_block(
        np.asarray(case[2]) / 10.0, modulation_frequency_range_hz=case[1]
    )
    assert block.valid
    assert block.harmonic_frequencies_hz == pytest.approx((1.0,))
    assert block.included_frequencies_hz == pytest.approx(
        (0.4, 0.5, 0.6, 0.9, 1.0, 1.1)
    )
    assert block.modulation_depth_db == pytest.approx(case[5], abs=1e-10)


@pytest.mark.parametrize(
    "case", ref.IOA_PERIOD_CASES, ids=[c[0] for c in ref.IOA_PERIOD_CASES]
)
def test_periods_agree_with_the_ioa_code_and_the_ts(
    case: tuple[str, tuple[int, ...], int, float | None],
) -> None:
    _, indices, valid, rating = case
    series = (
        np.concatenate([ref.IOA_PERIOD_BLOCKS_TENTHS_DB[i] for i in indices]) / 10.0
    )
    period = env.amplitude_modulation_period(
        series, modulation_frequency_range_hz=ref.IOA_PERIOD_RANGE_HZ
    )
    assert period.valid_blocks == valid
    if rating is None:
        # The AMWG discards the period; the TS keeps it at 0 dB (13.6.3).
        assert not period.rated
        assert period.rating_db == pytest.approx(0.0)
        assert period.mean_modulation_frequency_hz is None
        assert period.mode_modulation_frequency_hz is None
    else:
        assert period.rated
        assert period.rating_db == pytest.approx(rating, abs=1e-10)


def test_a_rated_period_reports_the_mean_and_mode_fundamental() -> None:
    """13.6.3: 20 of 36 valid blocks at 0.7 Hz, the rest at 0.5 Hz to 1.0 Hz.

    The mean and the mode are those of the fundamentals the IOA code prints for
    the valid blocks of the same period.
    """
    indices, valid, rating, mean, mode = ref.IOA_PERIOD_FREQUENCY_CASE
    series = (
        np.concatenate([ref.IOA_PERIOD_BLOCKS_TENTHS_DB[i] for i in indices]) / 10.0
    )
    period = env.amplitude_modulation_period(
        series, modulation_frequency_range_hz=ref.IOA_PERIOD_RANGE_HZ
    )
    assert period.valid_blocks == valid
    assert period.rating_db == pytest.approx(rating, abs=1e-10)
    assert period.mean_modulation_frequency_hz == pytest.approx(mean, abs=1e-12)
    assert period.mode_modulation_frequency_hz == pytest.approx(mode, abs=1e-12)


def test_band_filtering_workbook_sums_to_the_sample_series() -> None:
    """The unweighted bands, A-weighted and summed, round to the three series."""
    levels = np.asarray(ref.IOA_BAND_EXAMPLE_UNWEIGHTED_TENTHS_DB) / 10.0
    for band in (1, 2, 3):
        summed = env.amplitude_modulation_band_levels(
            levels, ref.IOA_BAND_EXAMPLE_FREQUENCIES_HZ, band=band, weighting="Z"
        )
        np.testing.assert_array_equal(
            np.rint(summed * 10.0).astype(int), ref.IOA_SAMPLE_SERIES_TENTHS_DB[band]
        )


def test_already_weighted_bands_are_summed_without_weighting_again() -> None:
    levels = np.full((3, 7), 30.0)
    out = env.amplitude_modulation_band_levels(
        levels, wtm.AM_FREQUENCY_BANDS_HZ[2], band=2, weighting="A"
    )
    np.testing.assert_allclose(out, 30.0 + 10.0 * np.log10(7.0))


def test_the_a_weighting_is_iec_61672_table_3() -> None:
    table = {row[0]: row[1] for row in weighting_compliance._WEIGHTING_TABLE3}
    for frequency, value in wtm._A_WEIGHTING_DB.items():
        assert table[frequency] == pytest.approx(value)


def test_band_levels_need_every_band_of_the_range() -> None:
    levels = np.zeros((2, 6))
    with pytest.raises(ValueError, match=r"centred at 400 Hz"):
        env.amplitude_modulation_band_levels(
            levels, (100.0, 125.0, 160.0, 200.0, 250.0, 315.0), band=2, weighting="A"
        )


def test_an_unknown_band_is_refused() -> None:
    with pytest.raises(ValueError, match=r"'band' must be one of the band numbers"):
        env.amplitude_modulation_band_levels([[0.0]], [50.0], band=7, weighting="A")


def test_the_weighting_has_to_be_said() -> None:
    levels = np.zeros((1, 7))
    with pytest.raises(ValueError, match=r"'weighting' must be 'A' or 'Z'"):
        env.amplitude_modulation_band_levels(
            levels, wtm.AM_FREQUENCY_BANDS_HZ[1], band=1, weighting="C"
        )


def test_a_pure_sinusoid_is_rated_near_its_own_swing() -> None:
    """A 0.8 Hz sine of 3 dB amplitude is found, prominent and rated near 6 dB.

    Its own L5 - L95 is 2 * 3 * sin(0.45 pi) = 5.93 dB. The cubic de-trending
    takes a little of the sine with it, as eight cycles are not orthogonal to
    the polynomial, so the depth sits a few tenths under that.
    """
    t = np.arange(100) * 0.1
    x = 40.0 + 3.0 * np.sin(2 * np.pi * 0.8 * t)
    block = env.amplitude_modulation_block(x, modulation_frequency_range_hz=(0.5, 1.0))
    assert block.fundamental_frequency_hz == pytest.approx(0.8)
    assert block.prominence > 100.0
    assert block.modulation_depth_db == pytest.approx(
        6.0 * np.sin(0.45 * np.pi), abs=0.3
    )


def test_all_lines_transformed_back_give_the_detrended_series() -> None:
    """Footnote 6 of 13.6.2.3: the full inverse transform is the input."""
    x = _sample(2)
    block = env.amplitude_modulation_block(x, modulation_frequency_range_hz=(0.4, 0.9))
    spectrum = np.fft.fft(block.detrended_db)
    restored = wtm._reconstruct(spectrum, list(range(1, 50)))
    # The zero-frequency and Nyquist lines are not among 1..49; the detrended
    # series has no mean, and its Nyquist line is restored separately.
    nyquist = np.real(spectrum[50]) / 100.0 * np.cos(np.pi * np.arange(100))
    np.testing.assert_allclose(
        restored + nyquist + np.mean(block.detrended_db), block.detrended_db, atol=1e-9
    )


def test_the_upper_limit_of_the_range_is_inclusive() -> None:
    """A fundamental on the 1.6 Hz line is found with a range ending at 1.6 Hz."""
    t = np.arange(100) * 0.1
    x = 40.0 + 3.0 * np.sin(2 * np.pi * 1.6 * t) + 0.01 * np.cos(2 * np.pi * 0.2 * t)
    block = env.amplitude_modulation_block(x, modulation_frequency_range_hz=(1.0, 1.6))
    assert block.fundamental_frequency_hz == pytest.approx(1.6)


def test_a_steady_block_has_no_peak() -> None:
    """40 dB throughout leaves only rounding to de-trend: no local maximum (13.6.2.3 d))."""
    block = env.amplitude_modulation_block(
        np.full(100, 40.0), modulation_frequency_range_hz=(0.4, 1.2)
    )
    assert block.status is env.ModulationBlockStatus.NO_PEAK
    assert block.prominence is None
    assert block.fundamental_frequency_hz is None


def test_a_block_that_follows_a_cubic_has_no_peak() -> None:
    """The cubic of 13.6.2.3 a) takes the whole block; no 4e-15 dB depth is rated."""
    t = np.arange(100) * 0.1
    block = env.amplitude_modulation_block(
        40.0 + 0.3 * t - 0.05 * t**2 + 0.002 * t**3,
        modulation_frequency_range_hz=(0.4, 1.2),
    )
    assert block.status is env.ModulationBlockStatus.NO_PEAK
    assert block.modulation_depth_db is None


def test_one_unit_in_the_last_place_does_not_change_a_steady_block() -> None:
    """A steady 37.3 dB block with any one sample raised by one unit in the last place."""
    statuses = set()
    for sample in range(100):
        levels = np.full(100, 37.3)
        levels[sample] = np.nextafter(37.3, np.inf)
        statuses.add(
            env.amplitude_modulation_block(
                levels, modulation_frequency_range_hz=(0.4, 1.2)
            ).status
        )
    assert statuses == {env.ModulationBlockStatus.NO_PEAK}


def test_masking_lines_of_rounding_give_an_infinite_prominence() -> None:
    """A 0.8 Hz line whose masking lines hold nothing, whatever the rounding.

    Slow components at 0.1 Hz to 0.4 Hz make the 1.5 dB swing orthogonal to
    every cubic, so the de-trending leaves it whole and the lines at 0.5 Hz,
    0.6 Hz, 1.0 Hz and 1.1 Hz are rounding of the levels.
    """
    n = np.arange(100)
    columns = [np.cos(2 * np.pi * 8 * n / 100)]
    for line in (1, 2, 3, 4):
        columns += [
            np.cos(2 * np.pi * line * n / 100),
            np.sin(2 * np.pi * line * n / 100),
        ]
    basis = np.array(columns).T
    cubic = np.vander(n * 0.1, 4, increasing=True).T @ basis
    slow = np.linalg.lstsq(cubic[:, 1:], -1.5 * cubic[:, 0], rcond=None)[0]
    levels = 40.0 + basis @ np.concatenate([[1.5], slow])
    block = env.amplitude_modulation_block(
        levels, modulation_frequency_range_hz=(0.5, 1.0)
    )
    assert block.valid
    assert block.fundamental_frequency_hz == pytest.approx(0.8)
    assert block.prominence == float("inf")


def test_the_ioa_blocks_clear_the_rounding_threshold_by_far() -> None:
    """No line of the IOA sample series or the designed blocks is read as rounding.

    Their smallest line is more than 10^8 times the square of 1e-9 of their
    largest level, so the IOA rows above keep the code's numbers exactly.
    """
    blocks = [(_sample(band), (0.4, 0.9)) for band in (1, 2, 3)]
    blocks += [(np.asarray(c[2]) / 10.0, c[1]) for c in ref.IOA_BLOCK_CASES]
    for levels, frequency_range in blocks:
        block = env.amplitude_modulation_block(
            levels, modulation_frequency_range_hz=frequency_range
        )
        floor = (wtm._ROUNDING_FRACTION * np.max(np.abs(levels))) ** 2
        assert np.min(block.power_spectrum) > 1e8 * floor


def test_a_range_outside_the_method_is_refused() -> None:
    block = np.zeros(100)
    with pytest.raises(ValueError, match=r"0.3 Hz <= low < high <= 1.6 Hz"):
        env.amplitude_modulation_block(block, modulation_frequency_range_hz=(0.2, 1.0))


def test_a_block_needs_one_hundred_values() -> None:
    short = np.zeros(99)
    with pytest.raises(ValueError, match=r"must hold the 100 values"):
        env.amplitude_modulation_block(short, modulation_frequency_range_hz=(0.4, 1.0))


def test_a_period_needs_six_thousand_values() -> None:
    short = np.zeros(600)
    with pytest.raises(ValueError, match=r"must hold the 6000 values"):
        env.amplitude_modulation_period(short, modulation_frequency_range_hz=(0.4, 1.0))


def test_excluded_blocks_do_not_count() -> None:
    case = ref.IOA_PERIOD_CASES[0]
    series = (
        np.concatenate([ref.IOA_PERIOD_BLOCKS_TENTHS_DB[i] for i in case[1]]) / 10.0
    )
    excluded = np.zeros(60, dtype=bool)
    excluded[:10] = True
    period = env.amplitude_modulation_period(
        series,
        modulation_frequency_range_hz=ref.IOA_PERIOD_RANGE_HZ,
        excluded_blocks=excluded,
    )
    assert period.valid_blocks == case[2] - 10
    assert all(
        b.status is env.ModulationBlockStatus.EXCLUDED for b in period.blocks[:10]
    )


def test_exclusion_flags_may_be_zero_and_one() -> None:
    """Integer 0 and 1 flags exclude exactly what the booleans do."""
    case = ref.IOA_PERIOD_CASES[0]
    series = (
        np.concatenate([ref.IOA_PERIOD_BLOCKS_TENTHS_DB[i] for i in case[1]]) / 10.0
    )
    flags = np.zeros(60, dtype=int)
    flags[:10] = 1
    as_integers = env.amplitude_modulation_period(
        series,
        modulation_frequency_range_hz=ref.IOA_PERIOD_RANGE_HZ,
        excluded_blocks=flags,
    )
    assert as_integers.valid_blocks == case[2] - 10
    ratings, speeds, _ = _ratings()
    by_integers = env.bin_amplitude_modulation(
        ratings, speeds, excluded=[0, 1, 0, 0, 0]
    )
    by_booleans = env.bin_amplitude_modulation(
        ratings, speeds, excluded=[False, True, False, False, False]
    )
    np.testing.assert_array_equal(by_integers.counts, by_booleans.counts)
    np.testing.assert_array_equal(
        by_integers.mean_ratings_db, by_booleans.mean_ratings_db
    )


def test_numpy_integer_bands_are_band_numbers() -> None:
    ratings, speeds, _ = _ratings()
    binned = env.bin_amplitude_modulation(ratings, speeds, bands=np.array([1, 2, 3]))
    assert binned.bands == (1, 2, 3)
    assert all(type(b) is int for b in binned.bands)


def test_bands_may_be_given_by_any_iterable() -> None:
    """A generator is read once: validated and converted from the same values."""
    ratings, speeds, _ = _ratings()
    from_generator = env.bin_amplitude_modulation(
        ratings, speeds, bands=(b for b in (1, 2, 3))
    )
    assert from_generator.bands == (1, 2, 3)
    assert env.bin_amplitude_modulation(
        ratings, speeds, bands=iter([1, 2, 3])
    ).bands == (1, 2, 3)


def test_the_mode_is_the_lowest_of_equally_frequent_fundamentals() -> None:
    assert wtm._mode_frequency(np.array([0.7, 0.8, 0.7, 0.8, 0.9])) == pytest.approx(
        0.7
    )


def _ratings() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ratings = np.array(
        [
            [2.0, 4.0, 1.0],
            [0.0, 6.5, 3.5],
            [5.0, 1.0, 9.5],
            [3.0, 3.0, 0.0],
            [7.0, 2.0, 2.0],
        ]
    )
    speeds = np.array([4.6, 5.4, 5.49, 7.0, 7.4])
    directions = np.array([350.0, 14.0, 20.0, 200.0, 200.0])
    return ratings, speeds, directions


def test_bins_average_the_zeros_and_pick_the_worst_band() -> None:
    ratings, speeds, directions = _ratings()
    binned = env.bin_amplitude_modulation(ratings, speeds, directions)
    np.testing.assert_allclose(binned.wind_directions_deg, [0.0, 30.0, 210.0])
    np.testing.assert_allclose(binned.wind_speeds_m_s, [5.0, 5.0, 7.0])
    # 350 degrees at 4.6 m/s and 14 degrees at 5.4 m/s share sector 0, bin 5.
    first = binned.counts[0]
    assert first == 2
    np.testing.assert_allclose(binned.mean_ratings_db[0], [1.0, 5.25, 2.25])
    assert binned.selected_bands[0] == 2
    np.testing.assert_array_equal(binned.nonzero_counts[0], [1, 2, 2])
    np.testing.assert_allclose(binned.exceedance_percent[0, 1], [100.0, 50.0, 0.0])
    # Equation (9) by arithmetic mean (13.6.5): two points give |a - b| / 2.
    np.testing.assert_allclose(binned.type_a_uncertainty_db[0], [1.0, 1.25, 1.25])
    assert np.all(np.isnan(binned.type_a_uncertainty_db[1]))
    # 13.7 a) iii): ratings of 3.0 dB and 7.0 dB; 3.0 is not above 3 dB.
    np.testing.assert_allclose(binned.exceedance_percent[2, 0], [50.0, 50.0, 0.0])


def test_the_exceedance_thresholds_are_those_of_13_7() -> None:
    """13.7 a) iii) (folio 55): data points above 3 dB, 6 dB and 9 dB."""
    assert env.AM_EXCEEDANCE_THRESHOLDS_DB == (3.0, 6.0, 9.0)


def test_exceedance_counts_ratings_strictly_above_each_threshold() -> None:
    """Ratings at and 0.01 dB either side of 3 dB, 6 dB and 9 dB, in one bin."""
    ratings = np.array(
        [[2.99], [3.0], [3.01], [5.99], [6.0], [6.01], [8.99], [9.0], [9.01], [12.0]]
    )
    binned = env.bin_amplitude_modulation(ratings, np.full(10, 5.0), bands=(1,))
    # Above 3 dB: 3.01 to 12.0 (8 of 10); above 6 dB: 6.01 to 12.0 (5); above
    # 9 dB: 9.01 and 12.0 (2).
    np.testing.assert_allclose(binned.exceedance_percent[0, 0], [80.0, 50.0, 20.0])


def test_a_tie_selects_the_lowest_band() -> None:
    ratings, speeds, _ = _ratings()
    binned = env.bin_amplitude_modulation(ratings[3:4], speeds[3:4])
    assert binned.selected_bands[0] == 1


def test_excluded_periods_leave_their_bins() -> None:
    ratings, speeds, directions = _ratings()
    binned = env.bin_amplitude_modulation(
        ratings, speeds, directions, excluded=[False, True, False, False, False]
    )
    assert binned.counts[0] == 1


def test_bins_need_one_column_per_band() -> None:
    ratings, speeds, _ = _ratings()
    with pytest.raises(ValueError, match=r"one column per band"):
        env.bin_amplitude_modulation(ratings, speeds, bands=(1, 2))


def test_block_and_period_plots_draw_what_they_say() -> None:
    block = env.amplitude_modulation_block(
        _sample(2), modulation_frequency_range_hz=(0.4, 0.9)
    )
    ax = block.plot()
    heights = [p.get_height() for p in ax.patches]
    assert max(heights) == pytest.approx(float(np.max(block.power_spectrum)))
    assert "44,64" in block.plot(language="es").get_title()
    ax = block.plot(kind="series")
    assert any(
        np.allclose(line.get_ydata(), block.reconstructed_db) for line in ax.lines
    )
    plt.close("all")
    series = np.concatenate(
        [ref.IOA_PERIOD_BLOCKS_TENTHS_DB[i] for i in ref.IOA_PERIOD_CASES[0][1]]
    )
    period = env.amplitude_modulation_period(
        series / 10.0, modulation_frequency_range_hz=(0.4, 1.1)
    )
    ax = period.plot()
    assert any(
        np.allclose(line.get_ydata(), period.rating_db)
        for line in ax.lines
        if len(line.get_ydata()) == 2
    )
    plt.close("all")


def test_block_plot_refuses_an_unknown_kind() -> None:
    block = env.amplitude_modulation_block(
        _sample(2), modulation_frequency_range_hz=(0.4, 0.9)
    )
    with pytest.raises(ValueError, match=r"'kind' must be"):
        block.plot(kind="waterfall")  # type: ignore[arg-type]


def test_a_prominence_failed_block_draws_no_harmonic() -> None:
    """13.6.2.3 e): a block under the threshold is not analysed further."""
    rng = np.random.default_rng(0)
    block = env.amplitude_modulation_block(
        40.0 + rng.normal(0.0, 1.0, 100), modulation_frequency_range_hz=(0.5, 1.1)
    )
    assert block.status is env.ModulationBlockStatus.LOW_PROMINENCE
    ax = block.plot()
    labels = [line.get_label() for line in ax.lines]
    assert "Estimated harmonics" not in labels
    plt.close("all")


def test_the_binned_plot_names_each_band_it_draws() -> None:
    ratings, speeds, _ = _ratings()
    binned = env.bin_amplitude_modulation(ratings, speeds)
    ax = binned.plot(language="es")
    texts = [t.get_text() for t in ax.get_legend().get_texts()]
    # Only the bands the bins selected are keyed: 1 at 5 m/s, 3 at 7 m/s.
    assert texts[1:] == ["Banda 1: 50 Hz a 200 Hz", "Banda 3: 200 Hz a 800 Hz"]
    chips = [t.get_text() for t in ax.texts]
    assert chips == [str(int(b)) for b in binned.selected_bands]
    plt.close("all")


def test_the_binned_plot_draws_twelve_sectors_in_twelve_colours() -> None:
    """The twelve 30° sectors of 13.7 are told apart by colour, none grey."""
    from matplotlib.colors import to_hex, to_rgb

    from phonometry._plot.common import delta_e_2000

    directions = np.repeat(np.arange(0.0, 360.0, 30.0), 2)
    speeds = np.tile([5.0, 6.0], 12)
    binned = env.bin_amplitude_modulation(
        np.full((24, 1), 3.0), speeds, directions, bands=[1]
    )
    ax = binned.plot()
    legend = ax.get_legend()
    colours = {
        text.get_text(): handle.get_color()
        for text, handle in zip(legend.get_texts(), legend.legend_handles, strict=True)
    }
    sectors = [to_hex(colours[f"Sector {angle}°"]) for angle in range(0, 360, 30)]
    assert len(set(sectors)) == 12
    band_key = to_rgb(colours["Band 1: 50 Hz to 200 Hz"])
    for colour in sectors:
        assert delta_e_2000(to_rgb(colour), band_key) >= 16.0
    plt.close("all")


@pytest.mark.parametrize(
    ("language", "name"), [("en", "Sector 22.5°"), ("es", "Sector 22,5°")]
)
def test_the_binned_plot_writes_a_sector_centre_in_its_language(
    language: str, name: str
) -> None:
    binned = env.bin_amplitude_modulation(
        np.full((2, 1), 3.0), [5.0, 5.0], [22.5, 45.0], bands=[1], sector_width_deg=22.5
    )
    texts = [
        t.get_text() for t in binned.plot(language=language).get_legend().get_texts()
    ]
    assert texts[0] == name
    plt.close("all")


def _refusal_cases() -> list[tuple[str, object, str]]:
    ratings, speeds, _ = _ratings()
    return [
        (
            "columns without centres",
            lambda: env.amplitude_modulation_band_levels(
                np.zeros((2, 7)),
                wtm.AM_FREQUENCY_BANDS_HZ[1][:6],
                band=1,
                weighting="A",
            ),
            r"'frequencies_hz' has 6 centres",
        ),
        (
            "range of one value",
            lambda: env.amplitude_modulation_block(
                np.zeros(100), modulation_frequency_range_hz=(0.4,)
            ),
            r"must be two finite frequencies",
        ),
        (
            "range between two lines",
            lambda: env.amplitude_modulation_block(
                np.zeros(100), modulation_frequency_range_hz=(0.31, 0.39)
            ),
            r"holds no line of the 0.1 Hz",
        ),
        (
            "fifty-nine exclusion flags",
            lambda: env.amplitude_modulation_period(
                np.zeros(6000),
                modulation_frequency_range_hz=(0.4, 1.0),
                excluded_blocks=np.zeros(59, dtype=bool),
            ),
            r"'excluded_blocks' must flag each of the 60",
        ),
        (
            "a band twice",
            lambda: env.bin_amplitude_modulation(ratings, speeds, bands=(1, 1, 2)),
            r"'bands' must name at least one band, each once",
        ),
        (
            "an unknown band",
            lambda: env.bin_amplitude_modulation(ratings, speeds, bands=(1, 2, 7)),
            r"'bands' holds \[7\], which are not band numbers",
        ),
        (
            "a fractional band",
            lambda: env.bin_amplitude_modulation(ratings, speeds, bands=(1.5, 2, 3)),
            r"'bands' holds \[1.5\], which are not band numbers",
        ),
        (
            "True as a band",
            lambda: env.bin_amplitude_modulation(ratings, speeds, bands=(True, 2, 3)),
            r"'bands' holds \[True\], which are not band numbers",
        ),
        (
            "bands as a string",
            lambda: env.bin_amplitude_modulation(ratings, speeds, bands="123"),
            r"'bands' must be a sequence of band numbers; got '123'",
        ),
        (
            "True as the band of the band levels",
            lambda: env.amplitude_modulation_band_levels(
                np.zeros((2, 7)), wtm.AM_FREQUENCY_BANDS_HZ[1], band=True, weighting="A"
            ),
            r"'band' must be one of the band numbers .*; got True",
        ),
        (
            "1.0 as the band of the band levels",
            lambda: env.amplitude_modulation_band_levels(
                np.zeros((2, 7)), wtm.AM_FREQUENCY_BANDS_HZ[1], band=1.0, weighting="A"
            ),
            r"'band' must be one of the band numbers .*; got 1.0",
        ),
        (
            "block exclusion flags as strings",
            lambda: env.amplitude_modulation_period(
                np.zeros(6000),
                modulation_frequency_range_hz=(0.4, 1.0),
                excluded_blocks=["False"] * 60,
            ),
            r"'excluded_blocks' must hold booleans .*; got values of type <U5",
        ),
        (
            "block exclusion flags of NaN",
            lambda: env.amplitude_modulation_period(
                np.zeros(6000),
                modulation_frequency_range_hz=(0.4, 1.0),
                excluded_blocks=[np.nan] * 60,
            ),
            r"'excluded_blocks' must hold booleans .*; got values of type float64",
        ),
        (
            "block exclusion flags of 2",
            lambda: env.amplitude_modulation_period(
                np.zeros(6000),
                modulation_frequency_range_hz=(0.4, 1.0),
                excluded_blocks=[2] * 60,
            ),
            r"'excluded_blocks' must hold booleans .*; got an integer other than 0",
        ),
        (
            "period exclusion flags as strings",
            lambda: env.bin_amplitude_modulation(ratings, speeds, excluded=["no"] * 5),
            r"'excluded' must hold booleans .*; got values of type <U2",
        ),
        (
            "a negative rating",
            lambda: env.bin_amplitude_modulation(-ratings, speeds),
            r"'ratings_db' must not be negative",
        ),
        (
            "four exclusion flags",
            lambda: env.bin_amplitude_modulation(ratings, speeds, excluded=[False] * 4),
            r"'excluded' must flag each of the 5 periods",
        ),
        (
            "every period excluded",
            lambda: env.bin_amplitude_modulation(ratings, speeds, excluded=[True] * 5),
            r"Every period is excluded",
        ),
    ]


@pytest.mark.parametrize(
    ("call", "match"),
    [case[1:] for case in _refusal_cases()],
    ids=[case[0] for case in _refusal_cases()],
)
def test_the_clause_13_functions_refuse_what_they_cannot_rate(
    call: Callable[[], object], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        call()


# ---------------------------------------------------------------------------
# The status is read from the prominence, not stated
# ---------------------------------------------------------------------------
def test_a_block_s_status_is_read_from_its_prominence() -> None:
    """13.6.2.3 e): a prominence under 4 is LOW_PROMINENCE whatever is claimed."""
    import dataclasses

    block = env.amplitude_modulation_block(
        _sample(2), modulation_frequency_range_hz=(0.4, 0.9)
    )
    assert block.status is env.ModulationBlockStatus.VALID
    low = dataclasses.replace(block, prominence=3.9, modulation_depth_db=None)
    assert low.status is env.ModulationBlockStatus.LOW_PROMINENCE
    assert not low.valid


def test_a_block_cannot_state_its_status() -> None:
    import dataclasses

    block = env.amplitude_modulation_block(
        _sample(2), modulation_frequency_range_hz=(0.4, 0.9)
    )
    with pytest.raises(TypeError, match="status"):
        dataclasses.replace(block, status=env.ModulationBlockStatus.VALID)


def test_a_depth_on_a_block_that_is_not_valid_is_refused() -> None:
    """A low prominence with a modulation depth beside it is no block 13.6.2.3 produces."""
    import dataclasses

    block = env.amplitude_modulation_block(
        _sample(2), modulation_frequency_range_hz=(0.4, 0.9)
    )
    with pytest.raises(ValueError, match="modulation depth is read from a valid block"):
        dataclasses.replace(block, prominence=1.0)


def test_an_excluded_block_reads_as_excluded() -> None:
    import dataclasses

    block = env.amplitude_modulation_block(
        _sample(2), modulation_frequency_range_hz=(0.4, 0.9)
    )
    excluded = dataclasses.replace(block, excluded=True, modulation_depth_db=None)
    assert excluded.status is env.ModulationBlockStatus.EXCLUDED
