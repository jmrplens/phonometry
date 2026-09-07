#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ISO 7235:2003 and ISO 11691:1995, the substitution measurement.

Neither standard prints a worked example, so there is no column of
intermediates to reproduce. What there is instead is closed form: the
subtraction of Equation (1), the energy average of ISO 11691 Equation (2)
and the two printed tables, and each of those pins the module exactly.

The tests here name the clause or the table each value comes from, and the
bounds tests state the inequalities Equation (2) has to satisfy for every
input rather than for the one that happens to be tabulated.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

from phonometry.noise_control import silencer_measurement as sm

#: A plausible run of one-third-octave insertion losses for a 1 m
#: parallel-baffle silencer, 50 Hz to 10 kHz being 24 bands.
SUBSTITUTION = np.array([88.0, 90.0, 91.0, 92.0, 92.0, 91.0])
WITH_OBJECT = np.array([84.0, 83.0, 79.0, 72.0, 66.0, 63.0])


class TestSubstitutionInsertionLoss:
    """Equation (1) of both standards, and 6.3's reverberation term."""

    def test_it_is_the_level_the_silencer_took_away(self) -> None:
        found = sm.substitution_insertion_loss(SUBSTITUTION, WITH_OBJECT)
        assert found == pytest.approx([4.0, 7.0, 12.0, 20.0, 26.0, 28.0])

    def test_a_single_band_may_be_given_as_a_scalar(self) -> None:
        found = sm.substitution_insertion_loss(90.0, 65.0)
        assert found == pytest.approx([25.0])

    def test_the_two_printed_subscript_conventions_agree(self) -> None:
        # ISO 7235 Equation (1) writes D_i = L_WII - L_WI with II the
        # substitution duct; ISO 11691 Equation (1) writes D = L_p1 - L_p2
        # with 1 the substitution duct. Same subtraction, opposite numbering,
        # and the argument names here are neither.
        iso7235 = sm.substitution_insertion_loss(
            substitution_level=SUBSTITUTION, object_level=WITH_OBJECT
        )
        iso11691 = sm.substitution_insertion_loss(SUBSTITUTION, WITH_OBJECT)
        assert iso7235 == pytest.approx(iso11691)

    def test_a_silencer_that_does_nothing_measures_zero(self) -> None:
        found = sm.substitution_insertion_loss(SUBSTITUTION, SUBSTITUTION)
        assert found == pytest.approx(np.zeros(SUBSTITUTION.size))

    def test_doubling_the_reverberation_time_adds_three_decibels(self) -> None:
        # 6.3: a receiving room that has become twice as live between the two
        # series holds the second level up by 10 lg 2, and the correction
        # gives that back to the insertion loss.
        plain = sm.substitution_insertion_loss(90.0, 65.0)
        corrected = sm.substitution_insertion_loss(
            90.0, 65.0, reverberation_times=(1.0, 2.0)
        )
        assert corrected - plain == pytest.approx([10.0 * math.log10(2.0)])

    def test_an_unchanged_room_leaves_the_difference_alone(self) -> None:
        # 6.3 allows T_2 = T_1 when the test object is outside the room.
        corrected = sm.substitution_insertion_loss(
            SUBSTITUTION, WITH_OBJECT, reverberation_times=(1.8, 1.8)
        )
        assert corrected == pytest.approx(
            sm.substitution_insertion_loss(SUBSTITUTION, WITH_OBJECT)
        )

    def test_the_correction_may_vary_band_by_band(self) -> None:
        times = (np.full(SUBSTITUTION.size, 2.0), np.full(SUBSTITUTION.size, 1.0))
        corrected = sm.substitution_insertion_loss(
            SUBSTITUTION, WITH_OBJECT, reverberation_times=times
        )
        plain = sm.substitution_insertion_loss(SUBSTITUTION, WITH_OBJECT)
        assert corrected == pytest.approx(plain - 10.0 * math.log10(2.0))

    def test_two_series_of_different_lengths_are_refused(self) -> None:
        with pytest.raises(ValueError, match="one length"):
            sm.substitution_insertion_loss([90.0, 88.0], [65.0, 60.0, 55.0])

    def test_a_reverberation_pair_of_the_wrong_length_is_refused(self) -> None:
        times = ([1.0, 1.0, 1.0], [2.0, 2.0])
        with pytest.raises(ValueError, match="one length"):
            sm.substitution_insertion_loss(
                [90.0, 88.0], [65.0, 60.0], reverberation_times=times
            )

    def test_the_reverberation_times_cannot_set_the_band_count(self) -> None:
        # One measured band and two reverberation times is one measurement,
        # not two, and letting the singleton level broadcast would have
        # returned two answers from it.
        with pytest.raises(ValueError, match="one length"):
            sm.substitution_insertion_loss(
                90.0, 65.0, reverberation_times=([1.0, 1.0], [2.0, 2.0])
            )

    def test_one_reverberation_time_stands_for_every_band(self) -> None:
        # A room measured once for the whole run, rather than band by band.
        corrected = sm.substitution_insertion_loss(
            SUBSTITUTION, WITH_OBJECT, reverberation_times=(1.0, 2.0)
        )
        plain = sm.substitution_insertion_loss(SUBSTITUTION, WITH_OBJECT)
        assert corrected == pytest.approx(plain + 10.0 * math.log10(2.0))

    @pytest.mark.parametrize("bad", [float("nan"), float("inf")])
    def test_a_level_that_is_not_finite_is_refused(self, bad: float) -> None:
        with pytest.raises(ValueError, match="finite"):
            sm.substitution_insertion_loss([90.0, bad], [65.0, 60.0])

    @pytest.mark.parametrize("bad", [0.0, -1.0])
    def test_a_reverberation_time_that_is_not_positive_is_refused(
        self, bad: float
    ) -> None:
        with pytest.raises(ValueError, match="reverberation_times"):
            sm.substitution_insertion_loss(90.0, 65.0, reverberation_times=(1.0, bad))


class TestOctaveInsertionLoss:
    """ISO 11691 Equation (2), the energy average over three thirds."""

    def test_three_equal_thirds_give_the_same_octave(self) -> None:
        assert sm.octave_insertion_loss([12.0, 12.0, 12.0]) == pytest.approx([12.0])

    def test_the_leaky_band_decides_the_octave(self) -> None:
        # 30, 30 and 5 dB average to 21,7 dB on the decibels and to 9,7 dB on
        # the energy, and it is the second that the standard asks for: the
        # 5 dB band carries almost all of the transmitted sound.
        assert sm.octave_insertion_loss([30.0, 30.0, 5.0]) == pytest.approx(
            [9.744], abs=5e-4
        )

    def test_it_never_beats_the_worst_third_and_never_by_more_than_ten_lg_three(
        self,
    ) -> None:
        rng = np.random.default_rng(20260907)
        thirds = rng.uniform(0.0, 45.0, size=(200, 3))
        octaves = sm.octave_insertion_loss(thirds.reshape(-1))
        worst = thirds.min(axis=1)
        assert np.all(octaves >= worst - 1e-9)
        assert np.all(octaves <= worst + 10.0 * math.log10(3.0) + 1e-9)

    def test_several_octaves_at_once(self) -> None:
        found = sm.octave_insertion_loss([5.0, 5.0, 5.0, 20.0, 20.0, 20.0])
        assert found == pytest.approx([5.0, 20.0])

    def test_the_octaves_come_back_in_the_order_they_went_in(self) -> None:
        found = sm.octave_insertion_loss([5.0] * 3 + [20.0] * 3 + [12.0] * 3)
        assert found.shape == (3,)
        assert found == pytest.approx([5.0, 20.0, 12.0])

    def test_a_band_count_that_is_not_a_multiple_of_three_is_refused(self) -> None:
        with pytest.raises(ValueError, match="multiple of three"):
            sm.octave_insertion_loss([10.0, 12.0, 14.0, 16.0])

    def test_no_bands_at_all_is_refused(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            sm.octave_insertion_loss([])

    def test_one_band_on_its_own_is_refused(self) -> None:
        with pytest.raises(ValueError, match="multiple of three"):
            sm.octave_insertion_loss(12.0)


class TestMicrophonePositions:
    """ISO 7235 Table 6 and the rule of 6.2.1 it serves."""

    @pytest.mark.parametrize(
        ("frequency", "limit"),
        [(50.0, 10.0), (63.0, 10.0), (80.0, 8.0), (100.0, 8.0), (125.0, 7.0)],
    )
    def test_the_printed_rows(self, frequency: float, limit: float) -> None:
        assert sm.microphone_spread_limit(frequency) == pytest.approx(limit)

    @pytest.mark.parametrize("frequency", [160.0, 200.0, 1000.0, 10000.0])
    def test_the_gap_table_6_leaves_at_one_hundred_and_sixty_hertz(
        self, frequency: float
    ) -> None:
        # The printed row says "> 160", which leaves the 160 Hz one-third
        # octave with no limit of its own. Every other row names a single
        # band, so 160 Hz is read here as belonging to the last row. The gap
        # is registered in docs/ERRATA.md.
        assert sm.microphone_spread_limit(frequency) == pytest.approx(6.0)

    def test_a_band_below_the_table_takes_the_first_row(self) -> None:
        assert sm.microphone_spread_limit(40.0) == pytest.approx(10.0)

    def test_the_step_sits_immediately_above_the_last_printed_row(self) -> None:
        # A frequency between two tabulated centres takes the limit of the
        # next centre at or above it, so 125 Hz is the last band with 7 dB
        # and everything above it has 6, rather than the step floating
        # somewhere in the gap the printed table leaves between 125 and 160.
        assert sm.microphone_spread_limit(125.0) == pytest.approx(7.0)
        assert sm.microphone_spread_limit(130.0) == pytest.approx(6.0)

    def test_the_limit_never_rises_with_frequency(self) -> None:
        bands = [50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0, 500.0, 5000.0]
        limits = [sm.microphone_spread_limit(f) for f in bands]
        assert limits == sorted(limits, reverse=True)

    def test_three_positions_that_agree_stay_three(self) -> None:
        assert sm.microphone_positions_required([70.0, 71.5, 73.0], 125.0) == 3

    def test_three_positions_that_disagree_become_five(self) -> None:
        assert sm.microphone_positions_required([70.0, 72.0, 79.0], 125.0) == 5

    def test_the_limit_itself_is_still_three_positions(self) -> None:
        # 6.2.1 sends the test to five positions when the spread *exceeds*
        # the table, so a spread of exactly 7 dB at 125 Hz does not.
        assert sm.microphone_positions_required([70.0, 74.0, 77.0], 125.0) == 3

    def test_the_same_spread_passes_low_and_fails_high(self) -> None:
        levels = [70.0, 74.0, 79.0]
        assert sm.microphone_positions_required(levels, 50.0) == 3
        assert sm.microphone_positions_required(levels, 1000.0) == 5

    def test_it_wants_exactly_three_positions(self) -> None:
        with pytest.raises(ValueError, match="three levels"):
            sm.microphone_positions_required([70.0, 72.0], 125.0)

    @pytest.mark.parametrize("bad", [0.0, -125.0])
    def test_a_frequency_that_is_not_positive_is_refused(self, bad: float) -> None:
        with pytest.raises(ValueError, match="frequency"):
            sm.microphone_spread_limit(bad)


class TestReproducibility:
    """ISO 11691 Table 1 and ISO 7235 Table 7."""

    @pytest.mark.parametrize(
        ("frequency", "sigma"),
        [(50.0, 2.0), (1250.0, 2.0), (1600.0, 3.0), (10000.0, 3.0)],
    )
    def test_the_survey_table(self, frequency: float, sigma: float) -> None:
        assert sm.survey_reproducibility(frequency) == pytest.approx(sigma)

    @pytest.mark.parametrize(
        ("frequency", "sigma"),
        [(50.0, 1.5), (100.0, 1.5), (125.0, 1.0), (500.0, 1.0), (630.0, 2.0)],
    )
    def test_the_insertion_loss_column(self, frequency: float, sigma: float) -> None:
        assert sm.measurement_reproducibility(frequency) == pytest.approx(sigma)

    def test_the_insertion_loss_column_is_worst_at_the_top(self) -> None:
        assert sm.measurement_reproducibility(4000.0) == pytest.approx(3.0)

    @pytest.mark.parametrize(
        ("frequency", "sigma"),
        [(50.0, 3.0), (500.0, 3.0), (5000.0, 3.0), (10000.0, 3.0)],
    )
    def test_the_transmission_loss_column_is_flat(
        self, frequency: float, sigma: float
    ) -> None:
        # 7.9 says only the insertion-loss column came from tests; a column
        # that does not move with frequency is the shape of an estimate.
        found = sm.measurement_reproducibility(frequency, quantity="transmission_loss")
        assert found == pytest.approx(sigma)

    @pytest.mark.parametrize(
        ("frequency", "sigma"),
        [(50.0, 3.0), (500.0, 1.5), (1250.0, 1.0), (5000.0, 1.0)],
    )
    def test_the_intensity_column_runs_the_other_way(
        self, frequency: float, sigma: float
    ) -> None:
        found = sm.measurement_reproducibility(frequency, quantity="intensity")
        assert found == pytest.approx(sigma)

    def test_the_intensity_column_stops_at_five_kilohertz(self) -> None:
        # The footnote to Table 7 limits that column, and the other two go on
        # to 10 kHz.
        with pytest.raises(ValueError, match="5000 Hz"):
            sm.measurement_reproducibility(6300.0, quantity="intensity")

    def test_above_ten_kilohertz_nothing_is_tabulated(self) -> None:
        with pytest.raises(ValueError, match="10000 Hz"):
            sm.measurement_reproducibility(12500.0)

    def test_the_survey_table_stops_there_too(self) -> None:
        with pytest.raises(ValueError, match="10000 Hz"):
            sm.survey_reproducibility(12500.0)

    def test_a_column_the_table_does_not_print_is_refused(self) -> None:
        with pytest.raises(ValueError, match="quantity"):
            sm.measurement_reproducibility(500.0, quantity="pressure_loss")

    @pytest.mark.parametrize("frequency", [250.0, 4000.0])
    def test_the_expanded_uncertainty_is_twice_the_deviation(
        self, frequency: float
    ) -> None:
        sigma = sm.measurement_reproducibility(frequency)
        assert sm.measurement_expanded_uncertainty(frequency) == pytest.approx(
            sm.ISO7235_COVERAGE_FACTOR * sigma
        )

    def test_the_coverage_factor_is_two(self) -> None:
        assert sm.ISO7235_COVERAGE_FACTOR == pytest.approx(2.0)

    def test_the_expanded_uncertainty_follows_the_chosen_column(self) -> None:
        found = sm.measurement_expanded_uncertainty(500.0, quantity="intensity")
        assert found == pytest.approx(3.0)


class TestSubstitutionAreaRatio:
    """ISO 11691 4.5, the test duct against what it feeds."""

    def test_a_duct_matched_to_the_silencer_is_one(self) -> None:
        assert sm.substitution_area_ratio(0.09, 0.09) == pytest.approx(1.0)

    @pytest.mark.parametrize("ratio", [0.6, 1.0, 1.7])
    def test_the_range_ends_are_inside_it(self, ratio: float) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            found = sm.substitution_area_ratio(0.1 * ratio, 0.1)
        assert found == pytest.approx(ratio)

    @pytest.mark.parametrize("ratio", [0.5, 2.0])
    def test_outside_the_range_it_warns(self, ratio: float) -> None:
        with pytest.warns(sm.SilencerMeasurementWarning, match="ISO 11691 4.5"):
            sm.substitution_area_ratio(0.1 * ratio, 0.1)

    @pytest.mark.parametrize("bad", [0.0, -0.1])
    def test_an_area_that_is_not_positive_is_refused(self, bad: float) -> None:
        with pytest.raises(ValueError, match="element_area"):
            sm.substitution_area_ratio(0.1, bad)

    def test_the_published_range_is_the_printed_one(self) -> None:
        assert sm.SURVEY_AREA_RATIO_RANGE == (0.6, 1.7)


class TestPublishedScope:
    """The limits ISO 11691 writes into its own scope."""

    def test_the_design_velocity_ceiling(self) -> None:
        assert sm.SURVEY_MAX_VELOCITY_M_S == pytest.approx(15.0)

    def test_the_diameter_range(self) -> None:
        assert sm.SURVEY_DIAMETER_RANGE_M == (0.080, 2.0)

    def test_the_band_range(self) -> None:
        assert sm.SURVEY_BAND_RANGE_HZ == (50.0, 10000.0)
