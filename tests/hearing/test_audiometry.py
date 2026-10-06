#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ISO 8253-1:2010: the test room, the threshold rules and their uncertainty."""

from __future__ import annotations

import math

import numpy as np
import pytest
from reference_data import (
    ISO8253_1_A33_EQUIPMENT_DB,
    ISO8253_1_A34_TRANSDUCER_DB,
    ISO8253_1_BANDS_HZ,
    ISO8253_1_RELAXED_ALLOWANCE_DB,
    ISO8253_1_TABLE_2,
    ISO8253_1_TABLE_3,
    ISO8253_1_TABLE_4,
    ISO8253_1_TABLE_A2_COMPONENTS_DB,
    ISO8253_1_TABLE_A2_EXPANDED_DB,
    ISO8253_1_TABLE_A2_U_DB,
    ISO8253_1_VIBROTACTILE_DB,
    ISO8253_2_BANDS_HZ,
)

from phonometry import hearing

# ---------------------------------------------------------------------------
# The published tables
# ---------------------------------------------------------------------------


def test_the_room_tables_are_the_printed_ones() -> None:
    """Tables 2, 3 and 4 cell for cell, on the band axis they print."""
    assert hearing.AMBIENT_NOISE_BANDS_HZ == ISO8253_1_BANDS_HZ
    for lowest, column in ISO8253_1_TABLE_2.items():
        np.testing.assert_array_equal(
            hearing.AIR_CONDUCTION_AMBIENT_LIMITS_DB[lowest], column
        )
    for lowest, column in ISO8253_1_TABLE_4.items():
        np.testing.assert_array_equal(
            hearing.BONE_CONDUCTION_AMBIENT_LIMITS_DB[lowest], column
        )
    for earphone, column in ISO8253_1_TABLE_3.items():
        np.testing.assert_array_equal(hearing.EARPHONE_ATTENUATION_DB[earphone], column)
    assert set(hearing.AIR_CONDUCTION_AMBIENT_LIMITS_DB) == set(ISO8253_1_TABLE_2)
    assert set(hearing.BONE_CONDUCTION_AMBIENT_LIMITS_DB) == set(ISO8253_1_TABLE_4)


def test_the_room_tables_cannot_be_changed() -> None:
    table = hearing.AIR_CONDUCTION_AMBIENT_LIMITS_DB[125.0]
    with pytest.raises(ValueError, match="read-only"):
        table[0] = 0.0


# ---------------------------------------------------------------------------
# The limits and the room check (Clause 11)
# ---------------------------------------------------------------------------


def test_the_limits_take_every_adjustment_of_clause_11() -> None:
    """+8 dB for a +5 dB shift, plus the lowest hearing level to be measured."""
    base = hearing.ambient_noise_limits("air", lowest_test_frequency_hz=250.0)
    np.testing.assert_array_equal(base, ISO8253_1_TABLE_2[250.0])
    raised = hearing.ambient_noise_limits(
        "air",
        lowest_test_frequency_hz=250.0,
        allowed_threshold_shift_db=5.0,
        lowest_hearing_level_db=10.0,
    )
    np.testing.assert_allclose(raised - base, 10.0 + ISO8253_1_RELAXED_ALLOWANCE_DB)


def test_an_insert_earphone_adds_its_extra_attenuation() -> None:
    """11.1: the difference from the supra-aural column of Table 3 is added."""
    limits = hearing.ambient_noise_limits("air", earphone="ER-3A")
    extra = np.subtract(ISO8253_1_TABLE_3["ER-3A"], ISO8253_1_TABLE_3["supra-aural"])
    np.testing.assert_allclose(limits, np.add(ISO8253_1_TABLE_2[125.0], extra))
    # 1 kHz: 23 dB + (37 - 15) dB.
    assert limits[ISO8253_1_BANDS_HZ.index(1000.0)] == pytest.approx(45.0)


def test_the_hda200_gets_no_allowance_where_table_3_prints_none() -> None:
    limits = hearing.ambient_noise_limits("air", earphone="HDA 200")
    np.testing.assert_array_equal(limits[:3], ISO8253_1_TABLE_2[125.0][:3])
    assert limits[3] == pytest.approx(42.0 + 17.0 - 1.0)


def test_another_earphone_is_given_by_its_attenuation() -> None:
    own = np.full(25, 20.0)
    limits = hearing.ambient_noise_limits("air", earphone_attenuation_db=own)
    expected = np.add(
        ISO8253_1_TABLE_2[125.0], 20.0 - np.asarray(ISO8253_1_TABLE_3["supra-aural"])
    )
    np.testing.assert_allclose(limits, expected)


def test_bone_conduction_and_sound_field_use_their_own_tables() -> None:
    bone = hearing.ambient_noise_limits("bone", lowest_test_frequency_hz=250.0)
    np.testing.assert_array_equal(bone, ISO8253_1_TABLE_4[250.0])
    field = hearing.ambient_noise_limits("sound field")
    assert field.size == len(ISO8253_2_BANDS_HZ)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"presentation": "insert"}, "presentation"),
        ({"lowest_test_frequency_hz": 1000.0}, "lowest_test_frequency_hz"),
        (
            {"presentation": "bone", "lowest_test_frequency_hz": 500.0},
            "lowest_test_frequency_hz",
        ),
        ({"allowed_threshold_shift_db": 3.0}, "allowed_threshold_shift_db"),
        ({"earphone": "TDH 39"}, "earphone"),
        ({"presentation": "bone", "earphone": "ER-3A"}, "air conduction"),
        (
            {"earphone": "ER-3A", "earphone_attenuation_db": np.zeros(25)},
            "not both",
        ),
        ({"earphone_attenuation_db": np.zeros(7)}, "earphone_attenuation_db"),
        ({"lowest_hearing_level_db": math.nan}, "lowest_hearing_level_db"),
    ],
)
def test_the_limits_refuse_what_the_tables_do_not_cover(
    kwargs: dict[str, object], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        hearing.ambient_noise_limits(**kwargs)  # type: ignore[arg-type]


def test_a_quiet_room_passes_and_a_loud_band_fails() -> None:
    quiet = np.asarray(ISO8253_1_TABLE_2[125.0], dtype=float) - 2.0
    check = hearing.check_audiometric_ambient_noise(quiet)
    assert check.passes
    assert check.lowest_measurable_hearing_level_db == pytest.approx(-2.0)
    loud = quiet.copy()
    loud[ISO8253_1_BANDS_HZ.index(250.0)] += 5.0
    failed = hearing.check_audiometric_ambient_noise(loud)
    assert not failed.passes
    assert failed.exceedance_db[ISO8253_1_BANDS_HZ.index(250.0)] == pytest.approx(3.0)
    assert failed.lowest_measurable_hearing_level_db == pytest.approx(3.0)


def test_the_room_check_judges_against_the_testers_choices() -> None:
    """The check's limits follow the shift and the earphone it was given.

    A 5 dB shift raises Table 2 by the printed allowance, and an ER-3A insert
    earphone adds its Table 3 attenuation beyond the supra-aural column; a
    check that dropped either choice would judge against the default table.
    """
    levels = np.asarray(ISO8253_1_TABLE_2[125.0], dtype=float)
    relaxed = hearing.check_audiometric_ambient_noise(
        levels, allowed_threshold_shift_db=5.0
    )
    assert relaxed.allowed_threshold_shift_db == pytest.approx(5.0)
    np.testing.assert_allclose(
        relaxed.limits_db,
        np.add(ISO8253_1_TABLE_2[125.0], ISO8253_1_RELAXED_ALLOWANCE_DB),
    )
    insert = hearing.check_audiometric_ambient_noise(levels, earphone="ER-3A")
    extra = np.subtract(ISO8253_1_TABLE_3["ER-3A"], ISO8253_1_TABLE_3["supra-aural"])
    np.testing.assert_allclose(
        insert.limits_db, np.add(ISO8253_1_TABLE_2[125.0], extra)
    )


def test_a_level_on_its_limit_is_within_it() -> None:
    """A reading that lands on the limit through arithmetic is on it."""
    levels = np.asarray(ISO8253_1_TABLE_4[125.0], dtype=float) + 0.1 - 0.1
    assert hearing.check_audiometric_ambient_noise(levels, presentation="bone").passes


def test_a_partial_measurement_is_judged_but_does_not_pass() -> None:
    bands = [125.0, 250.0, 500.0, 1000.0]
    check = hearing.check_audiometric_ambient_noise(
        [0.0, 0.0, 0.0, 0.0], frequencies=bands
    )
    assert np.all(check.within)
    assert not check.covers_all_bands
    assert not check.passes
    np.testing.assert_array_equal(check.limits_db, [28.0, 19.0, 18.0, 23.0])


def test_the_noise_floor_margin_is_six_decibels() -> None:
    """11.1: a reading 6 dB above the floor is clear of it, 5,9 dB is not."""
    levels = np.asarray(ISO8253_1_TABLE_2[125.0], dtype=float)
    floor = levels - 6.0
    floor[0] = levels[0] - 5.9
    check = hearing.check_audiometric_ambient_noise(levels, noise_floor_db=floor)
    assert check.floor_limited[0]
    assert not np.any(check.floor_limited[1:])


def test_a_reading_six_decibels_over_the_floor_through_arithmetic_is_clear() -> None:
    """11.1 asks for a floor at least 6 dB below; 20,4 - 14,4 dB is 6 dB.

    In binary floating point the difference is 5,999999999999998 dB, one
    last bit short of the margin the clause lets through.
    """
    check = hearing.check_audiometric_ambient_noise(
        [20.4, 20.4], frequencies=[125.0, 160.0], noise_floor_db=[14.4, 14.5]
    )
    np.testing.assert_array_equal(check.floor_limited, [False, True])


def test_the_noise_floor_flags_the_bands_it_limits() -> None:
    levels = np.asarray(ISO8253_1_TABLE_4[125.0], dtype=float) - 1.0
    floor = np.full(25, 0.0)
    check = hearing.check_audiometric_ambient_noise(
        levels, presentation="bone", noise_floor_db=floor
    )
    # Bone conduction's 2 dB limit at 4 kHz cannot be read with a 0 dB floor.
    assert check.floor_limited[ISO8253_1_BANDS_HZ.index(4000.0)]
    assert not check.floor_limited[0]
    assert check.passes


def test_the_sound_field_room_needs_the_two_extra_bands() -> None:
    levels = np.zeros(len(ISO8253_2_BANDS_HZ)) - 5.0
    check = hearing.check_audiometric_ambient_noise(levels, presentation="sound field")
    assert check.passes
    assert check.table_bands_hz[-1] == 12500.0


def test_the_room_check_has_no_truth_value() -> None:
    check = hearing.check_audiometric_ambient_noise(np.zeros(25))
    with pytest.raises(TypeError, match="passes"):
        bool(check)


@pytest.mark.parametrize(
    ("levels", "kwargs", "match"),
    [
        (np.zeros(5), {}, "levels_db"),
        (np.zeros(2), {"frequencies": [125.0, 333.0]}, "333"),
        (np.zeros(2), {"frequencies": [250.0, 125.0]}, "increasing"),
        (np.zeros(25), {"noise_floor_db": np.zeros(3)}, "noise_floor_db"),
    ],
)
def test_the_room_check_refuses_mismatched_bands(
    levels: np.ndarray, kwargs: dict[str, object], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        hearing.check_audiometric_ambient_noise(levels, **kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# The ascending method (6.2.3.2, 6.2.4.2)
# ---------------------------------------------------------------------------

#: A subject whose threshold is 30 dB: three ascents from 20 dB each end at
#: 30 dB, with the 10 dB drop after every response.
_THREE_AT_30 = ([20, 25, 30, 20, 25, 30, 20, 25, 30], [0, 0, 1, 0, 0, 1, 0, 0, 1])


def test_three_responses_at_one_level_set_the_threshold() -> None:
    levels, heard = _THREE_AT_30
    result = hearing.ascending_method_threshold(
        presentation_levels_db=levels, responses=heard, familiarization_level_db=30.0
    )
    assert result.determined
    assert result.threshold_db == 30.0
    assert result.responses_at_threshold == 3
    np.testing.assert_array_equal(result.ascent_levels_db, [30.0, 30.0, 30.0])
    assert math.isnan(result.next_level_db)
    assert not result.doubtful


def test_the_sequence_says_what_to_present_next() -> None:
    """Step 1 starts 10 dB below familiarization; a response drops 10 dB."""
    empty = hearing.ascending_method_threshold(
        presentation_levels_db=[], responses=[], familiarization_level_db=40.0
    )
    assert empty.next_level_db == 30.0
    after_miss = hearing.ascending_method_threshold(
        presentation_levels_db=[30.0], responses=[False]
    )
    assert after_miss.next_level_db == 35.0
    after_hit = hearing.ascending_method_threshold(
        presentation_levels_db=[30.0, 35.0], responses=[False, True]
    )
    assert after_hit.next_level_db == 25.0
    assert not after_hit.determined


def test_a_descent_that_is_still_heard_is_not_an_ascent() -> None:
    result = hearing.ascending_method_threshold(
        presentation_levels_db=[40, 30, 20, 25, 30],
        responses=[True, True, False, False, True],
    )
    np.testing.assert_array_equal(result.ascent_levels_db, [30.0])


def test_five_ascents_without_three_at_one_level_start_a_new_series() -> None:
    """Step 2: 10 dB above the last response, as a new series."""
    levels = [20, 25, 30, 20, 25, 30, 35, 25, 30, 20, 25, 30, 35, 25, 30, 35, 40]
    heard = [0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    result = hearing.ascending_method_threshold(
        presentation_levels_db=levels, responses=heard
    )
    assert result.series_exhausted
    assert not result.determined
    assert result.next_level_db == 50.0


def test_the_shortened_version_needs_two_out_of_three() -> None:
    result = hearing.ascending_method_threshold([35.0, 30.0, 30.0], shortened=True)
    assert result.determined
    assert result.threshold_db == 30.0
    full = hearing.ascending_method_threshold([35.0, 30.0, 30.0])
    assert not full.determined


def test_the_threshold_is_the_level_answered_in_more_than_half_the_ascents() -> None:
    """6.2.4.2 on five ascents: 30 dB three times out of five."""
    result = hearing.ascending_method_threshold([30.0, 35.0, 30.0, 25.0, 30.0])
    assert result.threshold_db == 30.0
    assert result.span_db == 10.0
    assert not result.doubtful


def test_a_span_over_ten_decibels_is_doubtful() -> None:
    result = hearing.ascending_method_threshold([30.0, 45.0, 30.0, 30.0])
    assert result.determined
    assert result.doubtful


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"presentation_levels_db": [20, 30], "responses": [0, 0]}, "presents 25 dB"),
        ({"presentation_levels_db": [30, 25], "responses": [1, 0]}, "presents 20 dB"),
        (
            {
                "presentation_levels_db": [25],
                "responses": [0],
                "familiarization_level_db": 40.0,
            },
            "first tone must be 30 dB",
        ),
        (
            {
                "presentation_levels_db": [*_THREE_AT_30[0], 20],
                "responses": [*_THREE_AT_30[1], 0],
            },
            "after the series ended",
        ),
        ({"presentation_levels_db": [20, 25], "responses": [0]}, "responses"),
        ({"presentation_levels_db": [20]}, "either"),
    ],
)
def test_the_replay_refuses_a_step_the_method_does_not_take(
    kwargs: dict[str, object], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        hearing.ascending_method_threshold(**kwargs)  # type: ignore[arg-type]


def test_the_ascents_alone_refuse_a_series_too_long() -> None:
    with pytest.raises(ValueError, match="at most 5 ascents"):
        hearing.ascending_method_threshold([30.0, 35.0, 30.0, 35.0, 40.0, 30.0])


def test_the_ascents_alone_refuse_ascents_after_the_end() -> None:
    with pytest.raises(ValueError, match="series ended at ascent 3"):
        hearing.ascending_method_threshold([30.0, 30.0, 30.0, 35.0])


# ---------------------------------------------------------------------------
# The bracketing method (6.2.4.3)
# ---------------------------------------------------------------------------


def test_the_bracketing_threshold_rounds_the_mean_to_five_decibels() -> None:
    result = hearing.bracketing_method_threshold([30, 30, 35], [35, 35, 35])
    assert result.ascent_mean_db == pytest.approx(95.0 / 3.0)
    assert result.descent_mean_db == pytest.approx(35.0)
    assert result.mean_db == pytest.approx(100.0 / 3.0)
    assert result.threshold_db == 35.0
    assert result.complete
    assert not result.repeat_advised


def test_the_library_sends_a_bracketing_tie_to_the_higher_step() -> None:
    """6.2.4.3 says "nearest" and no more; 32,5 dB going to 35 dB is the
    library's convention for the tie, not a value the standard gives.
    """
    result = hearing.bracketing_method_threshold([30, 30, 35], [30, 35, 35])
    assert result.mean_db == pytest.approx(32.5)
    assert result.threshold_db == 35.0


def test_the_bracketing_rounding_takes_the_nearest_step() -> None:
    assert (
        hearing.bracketing_method_threshold([30, 30, 30], [30, 30, 35]).threshold_db
        == 30.0
    )


def test_two_brackets_suffice_when_their_four_levels_agree() -> None:
    assert hearing.bracketing_method_threshold([30, 35], [30, 35]).complete
    assert not hearing.bracketing_method_threshold([30, 40], [30, 35]).complete
    assert not hearing.bracketing_method_threshold([30], [30]).complete


def test_a_bracketing_spread_over_ten_decibels_asks_for_a_repeat() -> None:
    assert hearing.bracketing_method_threshold(
        [20, 35, 25], [25, 25, 30]
    ).repeat_advised


def test_the_bracketing_method_refuses_no_levels() -> None:
    with pytest.raises(ValueError, match="descent_levels_db"):
        hearing.bracketing_method_threshold([30.0], [])


# ---------------------------------------------------------------------------
# Automatic recording audiometry (6.3.5)
# ---------------------------------------------------------------------------


def test_the_automatic_threshold_averages_peaks_and_valleys_and_rounds_up() -> None:
    result = hearing.automatic_audiometry_threshold(
        [30, 20, 31, 21, 32, 20, 30, 19, 31]
    )
    assert not result.retained[0]
    np.testing.assert_array_equal(result.peaks_db, [31.0, 32.0, 30.0, 31.0])
    np.testing.assert_array_equal(result.valleys_db, [20.0, 21.0, 20.0, 19.0])
    assert result.mean_db == pytest.approx(25.5)
    assert result.threshold_db == 26.0
    assert not result.doubtful


def test_a_fraction_below_a_half_is_rounded_up_too() -> None:
    """6.3.5 c) rounds up: a mean of 25,25 dB is 26 dB, not the nearest 25 dB."""
    result = hearing.automatic_audiometry_threshold(
        [30, 20, 30.5, 20, 30.5, 20, 30.5, 20]
    )
    assert result.mean_db == pytest.approx(25.25)
    assert result.threshold_db == 26.0


def test_a_whole_mean_is_not_rounded_up_a_decibel() -> None:
    """25 dB stays 25 dB: 'rounded up to the nearest whole number'."""
    result = hearing.automatic_audiometry_threshold([28, 20, 30, 20, 30, 20, 30, 20])
    assert result.mean_db == pytest.approx(25.0)
    assert result.threshold_db == 25.0


def test_small_excursions_are_ignored_at_both_ends() -> None:
    """6.3.5 a): an excursion of 3 dB or less drops both of its reversals."""
    result = hearing.automatic_audiometry_threshold(
        [30, 20, 30, 28, 30, 20, 30, 20, 30, 20]
    )
    np.testing.assert_array_equal(
        result.retained,
        [False, True, False, False, False, True, True, True, True, True],
    )
    assert result.doubtful is False


def test_an_excursion_of_three_decibels_is_small_and_one_of_more_is_not() -> None:
    """6.3.5 a): "3 dB or less" drops a 3 dB excursion and keeps a 3,5 dB one."""
    three = hearing.automatic_audiometry_threshold(
        [30, 20, 30, 27, 30, 20, 30, 20, 30, 20]
    )
    assert not np.any(three.retained[2:5])
    wider = hearing.automatic_audiometry_threshold(
        [30, 20, 30, 26.5, 30, 20, 30, 20, 30, 20]
    )
    assert np.all(wider.retained[1:])


def test_six_retained_reversals_are_enough_and_five_are_not() -> None:
    """6.3.5: fewer than six reversals left after a) make a tracing doubtful."""
    six = hearing.automatic_audiometry_threshold([30, 20, 30, 20, 30, 20, 30])
    assert int(np.sum(six.retained)) == 6
    assert not six.doubtful
    five = hearing.automatic_audiometry_threshold([30, 20, 30, 20, 30, 20])
    assert int(np.sum(five.retained)) == 5
    assert five.doubtful


def test_a_tracing_with_few_reversals_or_a_wide_spread_is_doubtful() -> None:
    few = hearing.automatic_audiometry_threshold([30, 20, 30, 20, 30])
    assert few.doubtful
    wide = hearing.automatic_audiometry_threshold([30, 20, 45, 20, 30, 20, 30, 20])
    assert wide.doubtful


@pytest.mark.parametrize(
    ("reversals", "match"),
    [
        ([30, 20], "at least 3"),
        ([30, 20, 15, 25], "alternate"),
        ([30, 30, 20, 30], "alternate"),
        ([30, 20, 22, 20], "no peak or no valley"),
    ],
)
def test_the_automatic_threshold_refuses_a_tracing_it_cannot_read(
    reversals: list[float], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        hearing.automatic_audiometry_threshold(reversals)


# ---------------------------------------------------------------------------
# Sweep-frequency audiometry (7.5)
# ---------------------------------------------------------------------------


def _sweep() -> tuple[np.ndarray, np.ndarray]:
    """A tracing from 250 Hz to 8 kHz, peaks at 30 dB and valleys at 20 dB."""
    freqs = np.geomspace(250.0, 8000.0, 24)
    levels = np.where(np.arange(24) % 2 == 0, 30.0, 20.0)
    return freqs, levels


def test_the_sweep_threshold_averages_the_three_nearest_peaks_and_valleys() -> None:
    freqs, levels = _sweep()
    result = hearing.sweep_audiometry_threshold(freqs, levels)
    np.testing.assert_array_equal(
        result.frequencies,
        [250.0, 500.0, 750.0, 1000.0, 1500.0, 2000.0]
        + [3000.0, 4000.0, 6000.0, 8000.0],
    )
    np.testing.assert_allclose(result.mean_db, 25.0)
    np.testing.assert_array_equal(result.threshold_db, 25.0)
    assert not np.any(result.less_reliable)


def test_the_running_threshold_sits_at_the_geometric_mean_frequency() -> None:
    freqs, levels = _sweep()
    result = hearing.sweep_audiometry_threshold(freqs, levels, frequencies=[1000.0])
    assert result.running_threshold_db.size == 24 - 5
    np.testing.assert_allclose(result.running_threshold_db, 25.0)
    assert result.running_frequencies[0] == pytest.approx(
        math.exp(np.mean(np.log(freqs[:6])))
    )


def test_the_sweep_threshold_rounds_to_the_nearest_decibel() -> None:
    freqs, levels = _sweep()
    shifted = levels + np.where(np.arange(24) % 2 == 0, 0.6, 0.0)
    result = hearing.sweep_audiometry_threshold(freqs, shifted, frequencies=[2000.0])
    assert result.mean_db[0] == pytest.approx(25.3)
    assert result.threshold_db[0] == 25.0


def test_the_nearest_reversals_are_found_on_the_logarithmic_axis() -> None:
    """7.5: a peak at 617 Hz is among the three nearest to 1 kHz on a linear
    axis but not on the logarithmic one the sweep runs on.
    """
    freqs, levels = _sweep()
    levels[6] = 40.0
    result = hearing.sweep_audiometry_threshold(freqs, levels, frequencies=[1000.0])
    assert result.mean_db[0] == pytest.approx(25.0)
    assert result.threshold_db[0] == 25.0


def test_a_sweep_whose_peaks_spread_is_less_reliable() -> None:
    freqs, levels = _sweep()
    levels[10] = 45.0
    result = hearing.sweep_audiometry_threshold(freqs, levels, frequencies=[1000.0])
    assert result.less_reliable[0]


def test_a_downward_sweep_reads_the_same() -> None:
    freqs, levels = _sweep()
    up = hearing.sweep_audiometry_threshold(freqs, levels)
    down = hearing.sweep_audiometry_threshold(freqs[::-1], levels[::-1])
    np.testing.assert_array_equal(up.threshold_db, down.threshold_db)


@pytest.mark.parametrize(
    ("change", "match"),
    [
        ("mismatch", "one positive frequency"),
        ("zigzag", "run one way"),
        ("short", "at least 6"),
        ("outside", "no audiometric frequency"),
    ],
)
def test_the_sweep_refuses_a_tracing_it_cannot_read(change: str, match: str) -> None:
    freqs, levels = _sweep()
    if change == "mismatch":
        freqs = freqs[:-1]
    elif change == "zigzag":
        freqs[3], freqs[4] = freqs[4], freqs[3]
    elif change == "short":
        freqs, levels = freqs[:4], levels[:4]
    else:
        freqs = np.geomspace(20.0, 100.0, 24)
    with pytest.raises(ValueError, match=match):
        hearing.sweep_audiometry_threshold(freqs, levels)


# ---------------------------------------------------------------------------
# The uncertainty (Annex A)
# ---------------------------------------------------------------------------


def test_the_budget_reproduces_table_a2() -> None:
    """Air conduction below 4 kHz, no masking: u = 4,9 dB and U = 10 dB."""
    budget = hearing.audiometric_uncertainty(1000.0)
    printed = ISO8253_1_TABLE_A2_COMPONENTS_DB
    np.testing.assert_allclose(np.round(budget.components_db[:4], 1), printed)
    assert budget.components_db[4:] == (0.0, 0.0, 0.0, 0.0)
    assert round(budget.combined_db, 1) == ISO8253_1_TABLE_A2_U_DB
    assert round(budget.expanded_db) == ISO8253_1_TABLE_A2_EXPANDED_DB
    # A.5: k = 2, which the whole-decibel rounding of A.6 alone would not pin.
    assert budget.expanded_db == pytest.approx(2.0 * budget.combined_db)


def test_the_components_are_those_of_a3() -> None:
    low = hearing.audiometric_uncertainty(4000.0)
    high = hearing.audiometric_uncertainty(6000.0)
    assert round(low.equipment_db, 1) == ISO8253_1_A33_EQUIPMENT_DB
    transducers = (round(low.transducer_db, 1), round(high.transducer_db, 1))
    assert transducers == ISO8253_1_A34_TRANSDUCER_DB
    assert high.repeatability_db == 4.0
    assert high.equipment_db == pytest.approx(math.hypot(5.0, 2.5) / math.sqrt(3.0))
    bone = hearing.audiometric_uncertainty(500.0, conduction="bone", masked=True)
    assert bone.repeatability_db == 3.0
    assert bone.equipment_db == pytest.approx(math.hypot(4.0, 2.5) / math.sqrt(3.0))
    assert bone.masking_db == 2.0
    # A.3.2 b) and A.3.3 b) above 4 kHz: 5 dB and a deviation of 5 dB.
    high_bone = hearing.audiometric_uncertainty(6000.0, conduction="bone")
    assert high_bone.repeatability_db == 5.0
    assert high_bone.equipment_db == pytest.approx(
        math.hypot(5.0, 2.5) / math.sqrt(3.0)
    )


def test_the_budget_takes_the_exceptional_components() -> None:
    fine = hearing.audiometric_uncertainty(
        1000.0, level_step_db=0.0, environment_db=0.0, tester_db=1.0, special_db=3.0
    )
    assert fine.equipment_db == pytest.approx(math.sqrt(3.0))
    assert fine.combined_db == pytest.approx(
        math.sqrt(2.5**2 + 3.0 + 1.5**2 + 2.5**2 + 1.0 + 9.0)
    )


@pytest.mark.parametrize(
    ("args", "kwargs", "match"),
    [
        ((1000.0,), {"conduction": "sound field"}, "conduction"),
        ((0.0,), {}, "frequency"),
        ((1000.0,), {"level_step_db": -1.0}, "level_step_db"),
        ((1000.0,), {"environment_db": -1.0}, "delta_n"),
    ],
)
def test_the_budget_refuses_what_annex_a_does_not_cover(
    args: tuple[float, ...], kwargs: dict[str, object], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        hearing.audiometric_uncertainty(*args, **kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# The repeat at 1 kHz and the cautions (6.2.3.2, 8.4)
# ---------------------------------------------------------------------------


def test_a_repeat_within_five_decibels_agrees() -> None:
    check = hearing.check_retest_agreement(25.0, 30.0)
    assert check.passes
    assert check.difference_db == 5.0
    assert not check.retest_further_frequencies
    assert check.frequency_hz == 1000.0


def test_a_change_of_ten_decibels_sends_the_test_back() -> None:
    worse = hearing.check_retest_agreement(25.0, 35.0)
    assert not worse.passes
    assert worse.retest_further_frequencies
    better = hearing.check_retest_agreement(25.0, 15.0, frequency_hz=2000.0)
    assert better.difference_db == -10.0
    assert better.retest_further_frequencies


def test_a_difference_between_the_two_rules_neither_agrees_nor_retests() -> None:
    """A finer control can give 7 dB, which Step 3 names no action for."""
    check = hearing.check_retest_agreement(25.0, 32.0)
    assert not check.passes
    assert not check.retest_further_frequencies


def test_the_retest_check_has_no_truth_value() -> None:
    check = hearing.check_retest_agreement(25.0, 25.0)
    with pytest.raises(TypeError, match="RetestAgreementCheck"):
        bool(check)


@pytest.mark.parametrize(
    ("args", "kwargs", "match"),
    [
        ((math.nan, 25.0), {}, "first_db"),
        ((25.0, 25.0), {"frequency_hz": 0.0}, "frequency_hz"),
    ],
)
def test_the_retest_check_refuses_what_it_cannot_judge(
    args: tuple[float, float], kwargs: dict[str, float], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        hearing.check_retest_agreement(*args, **kwargs)


def test_the_vibrotactile_levels_are_the_printed_ones() -> None:
    """8.4 (folio 13): 40 dB at 250 Hz, 60 dB at 500 Hz, 70 dB at 1 kHz."""
    assert dict(hearing.VIBROTACTILE_HEARING_LEVELS_DB) == ISO8253_1_VIBROTACTILE_DB


def test_the_vibrotactile_levels_cannot_be_changed() -> None:
    with pytest.raises(TypeError):
        hearing.VIBROTACTILE_HEARING_LEVELS_DB[250.0] = 30.0  # type: ignore[index]


def test_forty_decibels_by_air_conduction_calls_for_caution() -> None:
    """6.2.3.2: a hearing level of 40 dB or more, and 39,9 dB is less."""
    cautions = hearing.audiogram_cautions(
        [500.0, 1000.0, 2000.0], air_conduction_db=[39.9, 40.0, 55.0]
    )
    np.testing.assert_array_equal(cautions.cross_hearing, [False, True, True])
    assert not np.any(cautions.vibrotactile)
    assert cautions.any_caution


def test_a_bone_level_at_the_vibrotactile_threshold_may_be_felt() -> None:
    cautions = hearing.audiogram_cautions(
        [125.0, 250.0, 500.0, 1000.0, 2000.0],
        bone_conduction_db=[60.0, 40.0, 59.5, 70.0, 70.0],
    )
    np.testing.assert_array_equal(
        cautions.vibrotactile_levels_db, [math.nan, 40.0, 60.0, 70.0, math.nan]
    )
    np.testing.assert_array_equal(
        cautions.vibrotactile, [False, True, False, True, False]
    )
    assert not np.any(cautions.cross_hearing)


def test_forehead_placement_lowers_the_vibrotactile_levels_ten_decibels() -> None:
    cautions = hearing.audiogram_cautions(
        [250.0, 500.0, 1000.0],
        bone_conduction_db=[30.0, 49.0, 60.0],
        vibrator_placement="forehead",
    )
    np.testing.assert_array_equal(cautions.vibrotactile_levels_db, [30.0, 50.0, 60.0])
    np.testing.assert_array_equal(cautions.vibrotactile, [True, False, True])


def test_an_audiogram_without_a_caution_says_so() -> None:
    cautions = hearing.audiogram_cautions(
        [250.0, 1000.0],
        air_conduction_db=[10.0, 15.0],
        bone_conduction_db=[5.0, 10.0],
    )
    assert not cautions.any_caution


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({}, "air_conduction_db"),
        ({"air_conduction_db": [10.0]}, "one level per frequency"),
        (
            {"air_conduction_db": [10.0, 10.0], "vibrator_placement": "chin"},
            "placement",
        ),
    ],
)
def test_the_cautions_refuse_what_they_cannot_read(
    kwargs: dict[str, object], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        hearing.audiogram_cautions([250.0, 500.0], **kwargs)  # type: ignore[arg-type]
