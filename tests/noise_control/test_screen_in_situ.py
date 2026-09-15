#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for a removable screen measured in situ (ISO 11821:1997).

The standard prints eight pages, no worked example and one uncertainty number.
The oracles are its printed thresholds, the boxed background formula of 5.7
with its own window, the microphone geometry of 5.5.2 and the one thing it
flatly forbids: an A-weighted attenuation obtained with an artificial source.

The level pairs come from elsewhere, and the tests that use them say where.
Four published worked examples print a level with the screen and a level
without it, which is what clauses 5.8 and 5.9 subtract, and two more print the
background correction of 5.7 at each end of its window. Their provenance, and
the scope caveat each carries, is in the header of
``scripts/conformance/domains/in_situ_measurement.py``, which pins the same
numbers as conformance rows.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from reference_data import screen_in_situ as oracle
from reference_data import silencer_in_situ, spatial_decay

from phonometry import building, noise_control
from phonometry.noise_control.screen_in_situ import (
    BACKGROUND_CORRECTION_WINDOW_DB,
    DIRECTIVITY_CIRCLE_RADIUS_M,
    DIRECTIVITY_INDEX_LIMIT_DB,
    DIRECTIVITY_POSITIONS,
    ENGINEERING_STANDARD_DEVIATION_DB,
    IMPULSE_INVALID_DEVIATION_DB,
    IMPULSE_REPEAT_DEVIATION_DB,
    IMPULSE_REPEATS,
    ISO11821_MINIMUM_BACKGROUND_MARGIN_DB,
    ISO11821_PREFERRED_BACKGROUND_MARGIN_DB,
    MINIMUM_MICROPHONE_DISTANCE_M,
    MINIMUM_SCREEN_DIMENSION_M,
    OPERATOR_HEIGHT_M,
    OPERATOR_HEIGHT_TOLERANCE_M,
    OPERATOR_SPHERE_RADIUS_M,
    OUTDOOR_RANGE_M,
    SCREEN_DISTANCE_FACTORS,
    ScreenInSituWarning,
)

BANDS = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])


def test_the_attenuation_is_the_difference() -> None:
    unscreened = np.array([78.0, 80.0, 81.0, 79.0, 76.0, 72.0])
    screened = np.array([74.0, 74.0, 72.0, 68.0, 63.0, 58.0])
    res = noise_control.screen_attenuation(unscreened, screened, frequencies=BANDS)
    assert res.attenuation_db.tolist() == [4.0, 6.0, 9.0, 11.0, 13.0, 14.0]
    assert res.source_kind == "actual"


def test_a_common_level_shift_leaves_the_attenuation_alone() -> None:
    unscreened = np.array([78.0, 80.0])
    screened = np.array([74.0, 74.0])
    plain = noise_control.screen_attenuation(unscreened, screened)
    shifted = noise_control.screen_attenuation(unscreened + 5.0, screened + 5.0)
    assert np.allclose(plain.attenuation_db, shifted.attenuation_db)


def test_the_a_weighted_attenuation_is_a_difference() -> None:
    res = noise_control.screen_attenuation(
        [78.0],
        [70.0],
        a_weighted_unscreened_level_db=81.4,
        a_weighted_screened_level_db=72.9,
    )
    assert res.a_weighted_attenuation_db == pytest.approx(8.5)


def test_an_artificial_source_may_not_give_an_a_weighted_attenuation() -> None:
    with pytest.raises(ValueError, match="artificial sound source"):
        noise_control.screen_attenuation(
            [78.0],
            [70.0],
            source_kind="artificial",
            a_weighted_unscreened_level_db=81.4,
            a_weighted_screened_level_db=72.9,
        )


def test_half_an_a_weighted_pair_is_refused() -> None:
    with pytest.raises(ValueError, match="both"):
        noise_control.screen_attenuation(
            [78.0], [70.0], a_weighted_unscreened_level_db=81.4
        )


def test_mismatched_spectra_are_refused() -> None:
    with pytest.raises(ValueError, match="screened_levels_db"):
        noise_control.screen_attenuation([78.0, 80.0], [70.0])


def test_an_unknown_source_kind_is_refused() -> None:
    with pytest.raises(ValueError, match="source_kind"):
        noise_control.screen_attenuation(
            [78.0],
            [70.0],
            source_kind="loudspeaker",  # type: ignore[arg-type]
        )


def test_the_background_correction_is_the_boxed_formula() -> None:
    corrected = noise_control.background_corrected_level_db([80.0], [72.0])
    expected = 10.0 * math.log10(10.0**8.0 - 10.0**7.2)
    assert corrected[0] == pytest.approx(expected)


def test_a_wide_margin_leaves_the_level_alone() -> None:
    corrected = noise_control.background_corrected_level_db([80.0], [60.0])
    assert corrected[0] == pytest.approx(80.0)


def test_the_correction_window_is_the_printed_one() -> None:
    lower, upper = BACKGROUND_CORRECTION_WINDOW_DB
    assert (lower, upper) == (6.0, 10.0)
    assert ISO11821_MINIMUM_BACKGROUND_MARGIN_DB == 6.0
    assert ISO11821_PREFERRED_BACKGROUND_MARGIN_DB == 10.0
    # At the two ends of the window the correction is 1,2563 dB and 0,4576 dB.
    at_six = noise_control.background_corrected_level_db([80.0], [74.0])
    at_ten = noise_control.background_corrected_level_db([80.0], [70.0])
    assert 80.0 - at_six[0] == pytest.approx(1.2563, abs=1e-4)
    assert 80.0 - at_ten[0] == pytest.approx(0.4576, abs=1e-3)


def test_a_thin_margin_is_refused_rather_than_corrected() -> None:
    with pytest.raises(ValueError, match="unacceptable"):
        noise_control.background_corrected_level_db([80.0], [76.0])


def test_the_directivity_index_is_the_mean_less_the_position() -> None:
    levels = np.full(DIRECTIVITY_POSITIONS, 80.0)
    levels[0] = 70.0
    index = noise_control.directivity_index_db(levels)
    mean = 10.0 * math.log10((11.0 * 10.0**8.0 + 10.0**7.0) / DIRECTIVITY_POSITIONS)
    assert index[0] == pytest.approx(mean - 70.0)
    assert index[0] > 0.0
    assert index[1] < 0.0


def test_the_directivity_index_needs_twelve_positions() -> None:
    eleven_positions = np.full(11, 80.0)
    with pytest.raises(ValueError, match="12 positions"):
        noise_control.directivity_index_db(eleven_positions)


def test_an_omnidirectional_source_has_no_directivity() -> None:
    index = noise_control.directivity_index_db(np.full(DIRECTIVITY_POSITIONS, 80.0))
    assert np.allclose(index, 0.0)


def test_the_directivity_limit_and_circle_are_the_printed_ones() -> None:
    assert DIRECTIVITY_INDEX_LIMIT_DB == 8.0
    assert DIRECTIVITY_CIRCLE_RADIUS_M == 1.5


def test_the_microphone_distances_are_four_multiples_of_the_height() -> None:
    distances = noise_control.microphone_distances_m(8.0)
    assert distances.tolist() == [2.0, 4.0, 8.0, 16.0]
    assert SCREEN_DISTANCE_FACTORS == (0.25, 0.5, 1.0, 2.0)


def test_the_one_metre_floor_holds_for_a_low_screen() -> None:
    distances = noise_control.microphone_distances_m(2.0)
    assert distances.tolist() == [
        MINIMUM_MICROPHONE_DISTANCE_M,
        MINIMUM_MICROPHONE_DISTANCE_M,
        2.0,
        4.0,
    ]


def test_a_screen_under_one_and_a_half_metres_is_reported() -> None:
    with pytest.warns(ScreenInSituWarning, match="1.5 m"):
        noise_control.microphone_distances_m(1.2)
    assert MINIMUM_SCREEN_DIMENSION_M == 1.5


def test_the_impulse_level_is_an_arithmetic_mean() -> None:
    assert noise_control.impulse_mean_level_db([80.0, 82.0, 81.0]) == pytest.approx(
        81.0
    )


def test_a_spread_past_three_decibels_asks_for_three_more() -> None:
    with pytest.warns(ScreenInSituWarning, match="more repeats"):
        noise_control.impulse_mean_level_db([80.0, 84.0, 82.0])


def test_a_spread_past_five_decibels_is_invalid() -> None:
    with pytest.raises(ValueError, match="invalid"):
        noise_control.impulse_mean_level_db([80.0, 86.0, 82.0])


def test_fewer_than_three_repeats_is_refused() -> None:
    with pytest.raises(ValueError, match="at least"):
        noise_control.impulse_mean_level_db([80.0, 82.0])
    assert IMPULSE_REPEATS == 3
    assert IMPULSE_REPEAT_DEVIATION_DB == 3.0
    assert IMPULSE_INVALID_DEVIATION_DB == 5.0


def test_the_operator_geometry_is_the_printed_one() -> None:
    assert OPERATOR_SPHERE_RADIUS_M == 0.3
    assert OPERATOR_HEIGHT_M == 1.55
    assert OPERATOR_HEIGHT_TOLERANCE_M == 0.075
    assert OUTDOOR_RANGE_M == 25.0
    assert ENGINEERING_STANDARD_DEVIATION_DB == 2.0


def test_the_sphere_is_the_one_the_cabin_standard_prints() -> None:
    from phonometry.noise_control.cabin_insulation import (
        OPERATOR_SPHERE_RADIUS_M as cabin_radius,
    )

    assert OPERATOR_SPHERE_RADIUS_M == cabin_radius


def test_the_band_ranges_are_the_printed_ones() -> None:
    assert noise_control.ISO11821_BAND_RANGE_HZ[3] == (100.0, 5000.0)
    assert noise_control.ISO11821_BAND_RANGE_HZ[1] == (125.0, 4000.0)


def test_the_result_carries_the_distance_for_the_spread() -> None:
    res = noise_control.screen_attenuation([78.0], [70.0], distance_m=4.0)
    assert res.distance_m == pytest.approx(4.0)


def test_the_plot_draws_three_series() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res = noise_control.screen_attenuation(
        np.full(BANDS.size, 80.0), np.full(BANDS.size, 70.0), frequencies=BANDS
    )
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax)
    twin = [other for other in drawn.figure.axes if other is not drawn]
    assert len(drawn.lines) == 2
    assert len(twin[0].lines) == 1
    plt.close(fig)


def test_the_spanish_plot_translates_its_labels() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res = noise_control.screen_attenuation(
        np.full(BANDS.size, 80.0), np.full(BANDS.size, 70.0), frequencies=BANDS
    )
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax, language="es")
    assert "pantalla" in drawn.get_title()
    plt.close(fig)


def test_a_band_centre_at_zero_is_refused() -> None:
    with pytest.raises(ValueError, match="frequencies"):
        noise_control.screen_attenuation(
            [78.0, 80.0], [74.0, 74.0], frequencies=[0.0, 250.0]
        )


def test_a_non_positive_distance_is_refused() -> None:
    with pytest.raises(ValueError, match="distance_m"):
        noise_control.screen_attenuation([78.0], [70.0], distance_m=0.0)


# ---------------------------------------------------------------------------
# The level pairs the standard does not print itself
# ---------------------------------------------------------------------------

#: Every printed level pair below is in ``tests/reference_data/screen_in_situ.py``
#: (and the Barron Table 3-2 and 3-4 data in ``silencer_in_situ.py``), with the
#: document, the PDF page and the folio it was read on.


def test_barrons_level_pair_gives_the_two_printed_band_reductions() -> None:
    res = noise_control.screen_attenuation(
        oracle.BARRON_TABLE_7_6_UNSCREENED_DB,
        oracle.BARRON_TABLE_7_6_SCREENED_DB,
        frequencies=oracle.BARRON_TABLE_7_6_BANDS_HZ,
        distance_m=oracle.BARRON_EXAMPLE_7_9_SCREEN_DISTANCE_M,
    )
    # Barron (2003) Table 7-6, folio 316, a concrete barrier around an outdoor
    # transformer station, which ISO 11821 sends to ISO 10847: what it pins
    # here is the subtraction of 5.8 and nothing about the method. Folio 317
    # works out two of the eight bands in prose: 71.6 - 64.0 at 63 Hz and
    # 48.6 - 24.4 at 8000 Hz.
    printed = oracle.BARRON_EXAMPLE_7_9_PRINTED_REDUCTIONS_DB
    assert res.attenuation_db[0] == pytest.approx(printed["63 Hz"])
    assert res.attenuation_db[-1] == pytest.approx(printed["8000 Hz"])
    # The other six are the difference of two printed rows and are printed
    # nowhere, which is why they are asserted as a derivation, not as oracles.
    assert res.attenuation_db.tolist() == pytest.approx(
        [7.6, 9.3, 11.7, 14.4, 17.4, 20.4, 23.4, 24.2]
    )


def test_barrons_a_weighted_pair_gives_the_printed_reduction() -> None:
    # Folio 315 prints 69.6 dBA without the barrier, folio 317 55.3 dBA with
    # it and the 14.3 dBA between them.
    unscreened, screened = oracle.BARRON_EXAMPLE_7_9_A_WEIGHTED_DB
    res = noise_control.screen_attenuation(
        oracle.BARRON_TABLE_7_6_UNSCREENED_DB,
        oracle.BARRON_TABLE_7_6_SCREENED_DB,
        frequencies=oracle.BARRON_TABLE_7_6_BANDS_HZ,
        source_kind="actual",
        a_weighted_unscreened_level_db=unscreened,
        a_weighted_screened_level_db=screened,
        distance_m=oracle.BARRON_EXAMPLE_7_9_SCREEN_DISTANCE_M,
    )
    assert res.a_weighted_attenuation_db == pytest.approx(
        oracle.BARRON_EXAMPLE_7_9_A_REDUCTION_DB
    )
    # 7.4 c) gives D_pA the same rounding as D_p.
    assert res.rounded_a_weighted() == 14
    assert isinstance(res.rounded_a_weighted(), int)


def test_the_reported_integers_round_a_tie_to_the_even_decibel() -> None:
    # ISO 11821:1997 7.4 c), printed folio 7 (PDF page 17): "rounded to the
    # nearest integer", with nothing said about a tie. The sibling in-situ
    # standards of this library take Rule A of ISO 80000-1:2009 Annex B, the
    # even multiple, and so does this one. The halves are binary-exact.
    res = noise_control.screen_attenuation([0.5, 1.5, 2.5, 3.5], [0.0, 0.0, 0.0, 0.0])
    assert res.rounded().tolist() == [0, 2, 2, 4]
    weighted = noise_control.screen_attenuation(
        [80.0],
        [70.0],
        a_weighted_unscreened_level_db=80.5,
        a_weighted_screened_level_db=78.0,
    )
    assert weighted.rounded_a_weighted() == 2


def test_no_a_weighted_pair_reports_no_a_weighted_integer() -> None:
    res = noise_control.screen_attenuation([78.0, 80.0], [70.0, 71.0])
    assert res.a_weighted_attenuation_db is None
    assert res.rounded_a_weighted() is None
    # The raw band values are left alone by the rounding.
    assert res.attenuation_db.tolist() == [8.0, 9.0]


def test_the_indoor_worked_example_gives_its_printed_reduction() -> None:
    # Barron (2003) Example 7-10, folios 319 to 321: a machine screened from
    # its operator, 92.3 dB down to 84.0 dB in the 1000 Hz octave. The screen
    # stands 1.00 m from the machine and the operator 3.00 m from it, so the
    # position is 2 m from the screen.
    unscreened, screened, printed = oracle.BARRON_EXAMPLE_7_10_DB
    res = noise_control.screen_attenuation(
        [unscreened],
        [screened],
        frequencies=[1000.0],
        distance_m=oracle.BARRON_EXAMPLE_7_10_SCREEN_DISTANCE_M,
    )
    assert res.attenuation_db[0] == pytest.approx(printed)


def test_the_office_screen_example_rounds_to_the_printed_integers() -> None:
    # Hansen (2005) Example 6.23, folios 317 and 318: the total level at the
    # receiver with the screen out and in, over the three bands that matter.
    res = noise_control.screen_attenuation(
        oracle.HANSEN_EXAMPLE_6_23_UNSCREENED_DB,
        oracle.HANSEN_EXAMPLE_6_23_SCREENED_DB,
        frequencies=oracle.HANSEN_EXAMPLE_6_23_BANDS_HZ,
        distance_m=2.0,
    )
    assert res.attenuation_db.tolist() == pytest.approx([9.8, 15.2, 19.6])
    # Clause 7.4 c) reports D_p rounded to the nearest integer, which is the
    # "Reduction due to barrier 10 15 20" row of folio 318. The raw difference
    # stays on the result and the reported integers come from rounded().
    assert res.rounded().tolist() == list(oracle.HANSEN_EXAMPLE_6_23_REDUCTION_DB)
    assert res.rounded().dtype.kind == "i"


def test_the_single_path_levels_of_the_1991_example_subtract() -> None:
    # Sound Research Laboratories (1991), folio 177: 80 dB without the screen,
    # 65, 70 and 62 dB by each surviving path, and 71 dB for the three
    # together. That 71 dB is the book's decibel-addition rule of thumb and
    # not the energy sum, which is 71.687 dB and would give 8.3 dB.
    paths = oracle.SRL_1991_SCREENED_DB
    res = noise_control.screen_attenuation(
        [oracle.SRL_1991_UNSCREENED_DB] * len(paths), list(paths.values())
    )
    assert res.attenuation_db.tolist() == pytest.approx([9.0, 15.0, 10.0, 18.0])


def test_the_ifa_worked_example_differences_are_the_printed_ones() -> None:
    # IFA-LSA 01-234 (2020) Tab. 4.5, folio 18, read against the levels of
    # Tab. 4.4 on folio 17. A test sound source, so 5.9 forbids D_pA.
    levels = spatial_decay.IFA_LSA_01_234_LEVELS_DB
    bands = [float(band) for band in levels]
    # Keyed by the nearer of the two positions: 0 is the "Lp1 - Lp2" row of
    # Tab. 4.5 and 2 the "Lp3 - Lp4" one. The row between them is the next
    # test, because the table misprints one of its cells.
    differences = spatial_decay.IFA_LSA_01_234_DIFFERENCES_DB
    printed = {0: differences["Lp1 - Lp2"], 2: differences["Lp3 - Lp4"]}
    for step, values in printed.items():
        res = noise_control.screen_attenuation(
            [levels[band][step] for band in levels],
            [levels[band][step + 1] for band in levels],
            frequencies=bands,
            source_kind="artificial",
        )
        assert res.attenuation_db.tolist() == pytest.approx(values, abs=5e-14)


def test_the_ifa_table_misprints_one_of_its_twelve_differences() -> None:
    # Tab. 4.5 prints 4,7 dB for Lp2 - Lp3 at 2000 Hz. Its own Tab. 4.4 gives
    # 75,3 dB and 71,0 dB there, so the difference is 4,3 dB. The other eleven
    # cells of the table agree with the levels; this one does not.
    levels = spatial_decay.IFA_LSA_01_234_LEVELS_DB
    res = noise_control.screen_attenuation(
        [levels[band][1] for band in levels],
        [levels[band][2] for band in levels],
        frequencies=[float(band) for band in levels],
        source_kind="artificial",
    )
    assert res.attenuation_db.tolist() == pytest.approx([4.2, 4.1, 4.3, 5.3])
    row, band = spatial_decay.IFA_LSA_01_234_MISPRINT
    printed = spatial_decay.IFA_LSA_01_234_DIFFERENCES_DB[row][list(levels).index(band)]
    assert printed == pytest.approx(4.7)
    assert res.attenuation_db[2] != pytest.approx(printed)


def test_the_background_correction_matches_a_printed_worked_example() -> None:
    # Barron (2003) Example 3-6, folio 73: a fan read at 83 dB over a 77 dB
    # background, corrected to 81.7 dB. A 6 dB margin, the lower edge of the
    # window of 5.7, so the clause corrects rather than refusing.
    level, background, printed = silencer_in_situ.BARRON_EXAMPLE_3_6_DB
    corrected = noise_control.background_corrected_level_db([level], [background])
    assert corrected[0] == pytest.approx(printed, abs=0.05)
    assert level - corrected[0] == pytest.approx(
        silencer_in_situ.BARRON_TABLE_3_4_DB[level - background], abs=0.05
    )


def test_the_printed_correction_table_holds_across_the_window() -> None:
    # Barron (2003) Table 3-4, folio 72, the rows inside the 6 dB to 10 dB
    # window of 5.7. The table prints to 0.1 dB, so that is what reproducing
    # it means.
    printed = {
        margin: correction
        for margin, correction in silencer_in_situ.BARRON_TABLE_3_4_DB.items()
        if 6.0 <= margin <= 10.0
    }
    assert len(printed) == 7
    for margin, correction in printed.items():
        corrected = noise_control.background_corrected_level_db([83.0], [83.0 - margin])
        assert round(83.0 - float(corrected[0]), 1) == pytest.approx(correction)


def test_the_upper_edge_of_the_window_is_still_corrected() -> None:
    # Hansen (2005) Example 3.25, folio 147: 90 dB over an 80 dB background
    # corrects to 89.5 dB, and 86.6 dB over the same background to 85.5 dB.
    # The first margin is exactly 10 dB, so this pins the edge itself: 5.7
    # drops the correction past 10 dB, not at it.
    rows = oracle.HANSEN_EXAMPLE_3_25_DB
    corrected = noise_control.background_corrected_level_db(
        [row[0] for row in rows], [row[1] for row in rows]
    )
    assert corrected[0] == pytest.approx(rows[0][2], abs=0.05)
    assert corrected[1] == pytest.approx(rows[1][2], abs=0.05)
    assert noise_control.background_corrected_level_db([90.1], [80.0])[
        0
    ] == pytest.approx(90.1)


def test_the_six_decibel_correction_is_the_one_two_standards_print() -> None:
    # ISO 140-3:1995 6.5 (folio 7) and ISO 3744:2010 8.2.3 (folio 23) both
    # print 1,3 dB for a 6 dB margin, from the same energy subtraction 5.7
    # boxes. Neither reads the margin as 5.7 does: both apply the value as a
    # floor below 6 dB, where ISO 11821 refuses the measurement instead.
    corrected = noise_control.background_corrected_level_db([70.0], [64.0])
    assert 70.0 - corrected[0] == pytest.approx(
        oracle.ISO140_3_SIX_DB_MARGIN_CORRECTION_DB, abs=0.05
    )
    with pytest.raises(ValueError, match="unacceptable"):
        noise_control.background_corrected_level_db([70.0], [64.5])


def test_the_logarithmic_mean_under_the_directivity_index_is_printed() -> None:
    # Barron (2003) Table 3-2 and Example 3-5, folios 61, 68 and 69: ten levels
    # measured around a motor, whose energy mean is printed as 80.6 dB, and
    # the ring of three at 41.4 degrees, printed as 81.8 dB. Definition 3.10
    # reads twelve positions on a horizontal circle, so directivity_index_db
    # refuses this set; the mean it takes internally is reached here through
    # the entry point that publishes one.
    levels = list(silencer_in_situ.BARRON_EXAMPLE_3_3_LEVELS_DB)
    means = oracle.BARRON_EXAMPLE_3_5_MEANS_DB
    assert building.energy_average_level(levels) == pytest.approx(
        means["ten positions"], abs=0.05
    )
    assert building.energy_average_level(levels[1:4]) == pytest.approx(
        means["ring of three"], abs=0.05
    )
    with pytest.raises(ValueError, match="12 positions"):
        noise_control.directivity_index_db(levels)
