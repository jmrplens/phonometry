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


#: A 350 mm circular test duct, as its cross-sectional area in m².
DUCT_AREA = 0.0962
BANDS = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0])


class TestOpenEnd:
    """ISO 7235 Annex B.3, the duct mouth that keeps sound in."""

    def test_the_loss_falls_to_nothing_at_high_frequency(self) -> None:
        found = sm.open_end_transmission_loss(BANDS, DUCT_AREA)
        assert found[0] > found[-1]
        assert found[-1] == pytest.approx(0.0, abs=0.1)

    def test_the_loss_is_large_where_the_mouth_is_small(self) -> None:
        # At 63 Hz a 350 mm duct is a tenth of a wavelength across, and
        # nine tenths of the energy turns round.
        found = sm.open_end_transmission_loss(BANDS, DUCT_AREA)
        assert float(found[0]) == pytest.approx(11.23, abs=5e-3)

    def test_a_duct_in_free_space_reflects_less_than_a_flush_one(self) -> None:
        # Twice the solid angle is twice the room to radiate into.
        flush = sm.open_end_transmission_loss(
            BANDS, DUCT_AREA, solid_angle=sm.RADIATION_SOLID_ANGLES["A"]
        )
        free = sm.open_end_transmission_loss(
            BANDS, DUCT_AREA, solid_angle=sm.RADIATION_SOLID_ANGLES["C"]
        )
        assert np.all(free > flush)

    def test_the_two_annex_b_equations_close_on_the_energy(self) -> None:
        # (B.3) and (B.4) are the same physics said twice: what is not
        # transmitted is reflected, so D_td = -10 lg(1 - r^2) exactly.
        for angle in sm.RADIATION_SOLID_ANGLES.values():
            loss = sm.open_end_transmission_loss(BANDS, DUCT_AREA, solid_angle=angle)
            reflected = sm.open_end_reflection_coefficient(
                BANDS, DUCT_AREA, solid_angle=angle
            )
            assert loss == pytest.approx(-10.0 * np.log10(1.0 - reflected**2))

    def test_the_reflection_coefficient_stays_in_range(self) -> None:
        found = sm.open_end_reflection_coefficient(BANDS, DUCT_AREA)
        assert np.all(found > 0.0)
        assert np.all(found < 1.0)

    def test_the_anechoic_termination_limit_of_five_two_four(self) -> None:
        # A test duct qualifies as anechoic only below r = 0,3, which this
        # bare open end reaches only above 700 Hz or so.
        bands = np.array([500.0, 1000.0])
        found = sm.open_end_reflection_coefficient(bands, DUCT_AREA)
        assert float(found[0]) > 0.3
        assert float(found[1]) < 0.3

    def test_the_five_printed_solid_angles(self) -> None:
        assert sm.RADIATION_SOLID_ANGLES == {
            "A": 2.0 * math.pi,
            "B": math.pi,
            "C": 4.0 * math.pi,
            "D": 2.0 * math.pi,
            "E": 4.0 * math.pi,
        }

    @pytest.mark.parametrize("bad", [0.0, -0.1])
    def test_an_area_that_is_not_positive_is_refused(self, bad: float) -> None:
        with pytest.raises(ValueError, match="area"):
            sm.open_end_transmission_loss(BANDS, bad)

    @pytest.mark.parametrize("bad", [0.0, -1.0])
    def test_a_solid_angle_that_is_not_positive_is_refused(self, bad: float) -> None:
        with pytest.raises(ValueError, match="solid_angle"):
            sm.open_end_reflection_coefficient(BANDS, DUCT_AREA, solid_angle=bad)


class TestMeasuredTransmissionLoss:
    """ISO 7235 Equation (6) and Equation (7)."""

    def test_it_adds_what_the_open_end_was_keeping_in(self) -> None:
        insertion = np.array([4.0, 7.0, 12.0, 20.0, 26.0, 28.0])
        open_end = sm.open_end_transmission_loss(BANDS, DUCT_AREA)
        found = sm.measured_transmission_loss(insertion, open_end)
        assert found == pytest.approx(insertion + open_end)

    def test_a_transparent_mouth_leaves_the_insertion_loss_alone(self) -> None:
        insertion = np.array([20.0, 26.0])
        found = sm.measured_transmission_loss(insertion, [0.0, 0.0])
        assert found == pytest.approx(insertion)

    def test_the_flow_noise_power_is_the_sum_of_its_three_terms(self) -> None:
        open_end = sm.open_end_transmission_loss(BANDS, DUCT_AREA)
        found = sm.flow_noise_power_level(np.full(BANDS.size, 70.0), open_end, 5.0)
        assert found == pytest.approx(75.0 + open_end)

    def test_the_room_correction_may_vary_band_by_band(self) -> None:
        correction = np.linspace(4.0, 6.0, BANDS.size)
        found = sm.flow_noise_power_level(
            np.full(BANDS.size, 70.0), np.zeros(BANDS.size), correction
        )
        assert found == pytest.approx(70.0 + correction)

    def test_only_the_room_correction_may_stand_for_the_whole_run(self) -> None:
        # The open-end loss is a per-band quantity, so a single value for it
        # is a mistake, where a single room correction is a measurement made
        # once.
        with pytest.raises(ValueError, match="one length"):
            sm.flow_noise_power_level(np.full(BANDS.size, 70.0), 0.0, 5.0)

    def test_mismatched_band_counts_are_refused(self) -> None:
        with pytest.raises(ValueError, match="one length"):
            sm.measured_transmission_loss([4.0, 7.0, 12.0], [1.0, 2.0])


class TestModalFilterCutOn:
    """ISO 7235 Equations (4) and (5), and the requirement they serve."""

    def test_the_circular_form(self) -> None:
        assert sm.modal_filter_cut_on(diameter_m=0.4) == pytest.approx(
            0.59 * 343.0 / 0.4
        )

    def test_the_rectangular_form_is_a_half_wavelength(self) -> None:
        assert sm.modal_filter_cut_on(larger_dimension=0.5) == pytest.approx(343.0)

    def test_the_rectangular_form_is_exact(self) -> None:
        # A rigid rectangular duct's first mode is c / 2H, which is what
        # Equation (5) prints, so the library's own eigenvalue route agrees
        # to the last bit.
        from phonometry.noise_control import rectangular_duct_cut_on

        exact = rectangular_duct_cut_on(0.5, 0.2, speed_of_sound=343.0, count=1)
        found = sm.modal_filter_cut_on(larger_dimension=0.5, sound_speed=343.0)
        assert found == pytest.approx(float(exact.cut_on_no_flow[0]))

    def test_the_circular_constant_is_rounded_high(self) -> None:
        # The exact coefficient is the first zero of J_1', 1,8412 / pi, so
        # the printed 0,59 sits 0,67 % above it.
        from phonometry.noise_control import circular_duct_cut_on

        exact = circular_duct_cut_on(0.4, speed_of_sound=343.0, count=1)
        found = sm.modal_filter_cut_on(diameter_m=0.4, sound_speed=343.0)
        ratio = found / float(exact.cut_on_no_flow[0])
        assert ratio == pytest.approx(1.0067, abs=5e-5)

    def test_the_two_attenuation_minimums(self) -> None:
        assert sm.MODAL_FILTER_ATTENUATION_DB == (3.0, 5.0)

    def test_neither_dimension_is_refused(self) -> None:
        with pytest.raises(ValueError, match="exactly one"):
            sm.modal_filter_cut_on()

    def test_both_dimensions_are_refused(self) -> None:
        with pytest.raises(ValueError, match="exactly one"):
            sm.modal_filter_cut_on(diameter_m=0.4, larger_dimension=0.5)

    @pytest.mark.parametrize("bad", [0.0, -0.4])
    def test_a_dimension_that_is_not_positive_is_refused(self, bad: float) -> None:
        with pytest.raises(ValueError, match="diameter_m"):
            sm.modal_filter_cut_on(diameter_m=bad)


class TestFlowQuantities:
    """ISO 7235 6.5, Equations (8) to (13) and (16)."""

    def test_the_gas_law_with_the_printed_constants(self) -> None:
        # (101 325 + 200) / (287 x 293) = 1,2073 kg/m3.
        found = sm.normal_air_density(200.0, 101325.0, 20.0)
        assert found == pytest.approx(101525.0 / (287.0 * 293.0))

    def test_the_gauge_pressure_may_be_negative(self) -> None:
        # A duct on the suction side of a fan sits below the ambient.
        found = sm.normal_air_density(-300.0, 101325.0, 20.0)
        assert found == pytest.approx(101025.0 / (287.0 * 293.0))

    def test_the_printed_offset_is_two_hundred_and_seventy_three(self) -> None:
        # Not 273,15, and the gas constant is 287 and not 287,05. Together
        # they put the density 0,069 % high at 20 degrees, and both cancel in
        # the pressure loss coefficient because the same density is in the
        # dynamic pressure of each series.
        assert sm.ISO7235_ABSOLUTE_ZERO_OFFSET == pytest.approx(273.0)
        assert sm.ISO7235_GAS_CONSTANT == pytest.approx(287.0)
        exact = 101525.0 / (287.05 * 293.15)
        printed = sm.normal_air_density(200.0, 101325.0, 20.0)
        assert printed / exact == pytest.approx(1.000686, abs=5e-6)

    def test_an_absolute_pressure_that_is_not_positive_is_refused(self) -> None:
        with pytest.raises(ValueError, match="absolute pressure"):
            sm.normal_air_density(-101325.0, 101325.0, 20.0)

    def test_a_temperature_below_the_printed_absolute_zero_is_refused(self) -> None:
        with pytest.raises(ValueError, match="absolute temperature"):
            sm.normal_air_density(200.0, 101325.0, -273.0)

    def test_the_volume_flow_is_the_mass_flow_over_the_density(self) -> None:
        assert sm.volume_flow_rate(1.2, 1.2) == pytest.approx(1.0)

    def test_the_density_window_the_correction_starts_at(self) -> None:
        assert sm.DENSITY_RATIO_RANGE == (0.98, 1.02)

    def test_the_dynamic_pressure_is_half_rho_v_squared(self) -> None:
        # 1 m3/s through 0,0962 m2 is 10,395 m/s, and 1,2 kg/m3 makes that
        # 64,83 Pa.
        found = sm.dynamic_pressure(1.0, 0.0962, 1.2)
        assert found == pytest.approx(0.5 * 1.2 * (1.0 / 0.0962) ** 2)

    def test_the_dynamic_pressure_grows_as_the_square_of_the_flow(self) -> None:
        single = sm.dynamic_pressure(1.0, 0.0962, 1.2)
        double = sm.dynamic_pressure(2.0, 0.0962, 1.2)
        assert double / single == pytest.approx(4.0)

    def test_the_total_pressure_is_static_plus_dynamic(self) -> None:
        head = sm.dynamic_pressure(1.0, 0.0962, 1.2)
        assert sm.total_pressure(200.0, 1.0, 0.0962, 1.2) == pytest.approx(200.0 + head)

    @pytest.mark.parametrize("bad", [0.0, -0.1])
    def test_an_area_that_is_not_positive_is_refused_here_too(self, bad: float) -> None:
        with pytest.raises(ValueError, match="area"):
            sm.dynamic_pressure(1.0, bad, 1.2)

    def test_a_pressure_measured_in_one_plane_is_one_number(self) -> None:
        # Taking the first element of a sequence and dropping the rest is
        # how a run of five test points quietly becomes one.
        with pytest.raises(ValueError, match="one number"):
            sm.total_pressure([200.0, 300.0], 1.0, 0.0962, 1.2)

    def test_a_temperature_measured_in_one_plane_is_one_number_too(self) -> None:
        with pytest.raises(ValueError, match="one number"):
            sm.normal_air_density(200.0, 101325.0, [20.0, 21.0])


class TestPressureLossCoefficient:
    """ISO 7235 Equations (12), (14), (17) and (18)."""

    def test_equal_ducts_leave_the_static_loss_alone(self) -> None:
        # The NOTE to Equation (14): as a rule S_1 = S_2, and the bracket of
        # Equation (12) vanishes.
        head = sm.dynamic_pressure(1.0, 0.0962, 1.2)
        found = sm.total_pressure_loss(45.0, head, 0.0962, 0.0962)
        assert found == pytest.approx(45.0)

    def test_a_widening_object_is_not_credited_with_the_recovery(self) -> None:
        # Doubling the outlet area turns three quarters of the inlet velocity
        # head into static pressure, and Equation (12) adds it back so the
        # object is not paid for bookkeeping.
        head = sm.dynamic_pressure(1.0, 0.0962, 1.2)
        found = sm.total_pressure_loss(45.0, head, 0.0962, 2.0 * 0.0962)
        assert found == pytest.approx(45.0 + 0.75 * head)

    def test_a_narrowing_object_pays_for_the_speed_it_adds(self) -> None:
        head = sm.dynamic_pressure(1.0, 0.0962, 1.2)
        found = sm.total_pressure_loss(45.0, head, 0.0962, 0.5 * 0.0962)
        assert found == pytest.approx(45.0 - 3.0 * head)

    def test_the_coefficient_is_the_loss_in_velocity_heads(self) -> None:
        head = sm.dynamic_pressure(1.0, 0.0962, 1.2)
        assert sm.pressure_loss_coefficient(45.0, head) == pytest.approx(45.0 / head)

    def test_the_coefficient_does_not_move_with_the_flow_rate(self) -> None:
        # A loss that grows as the square of the velocity divided by a head
        # that does the same is a property of the object.
        first = sm.pressure_loss_coefficient(45.0, sm.dynamic_pressure(1.0, 0.1, 1.2))
        second = sm.pressure_loss_coefficient(
            4.0 * 45.0, sm.dynamic_pressure(2.0, 0.1, 1.2)
        )
        assert first == pytest.approx(second)

    def test_the_substitution_average_of_equation_eighteen(self) -> None:
        heads = np.array([20.0, 40.0, 60.0, 80.0, 100.0])
        with_object = 2.5 * heads
        without = 0.4 * heads
        found = sm.average_pressure_loss_coefficient(with_object, heads, without, heads)
        assert found == pytest.approx(2.1)

    def test_the_two_series_need_not_be_the_same_length(self) -> None:
        # 6.5.2.2.3 averages the coefficients, not the pressures, so the two
        # series need not share their flow rates or their point count.
        first_head = np.array([20.0, 40.0, 60.0, 80.0, 100.0])
        second_head = np.array([25.0, 50.0, 75.0, 100.0, 125.0, 150.0])
        found = sm.average_pressure_loss_coefficient(
            2.5 * first_head, first_head, 0.4 * second_head, second_head
        )
        assert found == pytest.approx(2.1)

    def test_a_series_shorter_than_five_points_warns(self) -> None:
        heads = np.array([20.0, 40.0, 60.0])
        with pytest.warns(sm.SilencerMeasurementWarning, match="airflow rates"):
            sm.average_pressure_loss_coefficient(2.5 * heads, heads, 0.4 * heads, heads)

    def test_a_series_whose_two_arrays_disagree_is_refused(self) -> None:
        heads = np.array([20.0, 40.0, 60.0, 80.0, 100.0])
        with pytest.raises(ValueError, match="one length"):
            sm.average_pressure_loss_coefficient(
                np.array([1.0, 2.0]), heads, 0.4 * heads, heads
            )

    def test_the_five_rates_and_the_ten_pascals(self) -> None:
        assert sm.MINIMUM_FLOW_RATES == 5
        assert sm.MINIMUM_PRESSURE_DIFFERENCE_PA == pytest.approx(10.0)

    def test_a_point_below_ten_pascals_warns(self) -> None:
        # 6.5.2.1 wants even the lowest airflow rate of a series to produce
        # more than 10 Pa, so that the smallest number in the fit is still a
        # measurement rather than the resolution of the manometer.
        with pytest.warns(sm.SilencerMeasurementWarning, match="10 Pa"):
            sm.pressure_loss_coefficient(6.0, 64.0)

    def test_a_point_exactly_on_ten_pascals_warns(self) -> None:
        # The clause reads "greater than 10 Pa", so the boundary itself is
        # outside what it allows and cannot be the lowest rate of a series.
        with pytest.warns(sm.SilencerMeasurementWarning, match="10 Pa"):
            sm.pressure_loss_coefficient(sm.MINIMUM_PRESSURE_DIFFERENCE_PA, 64.0)

    def test_a_point_just_above_ten_pascals_is_quiet(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            found = sm.pressure_loss_coefficient(10.5, 64.0)
        assert found == pytest.approx(10.5 / 64.0)

    def test_a_point_above_ten_pascals_is_quiet(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            found = sm.pressure_loss_coefficient(45.0, 64.0)
        assert found == pytest.approx(45.0 / 64.0)

    def test_a_loss_that_is_a_vector_is_refused(self) -> None:
        with pytest.raises(ValueError, match="one number"):
            sm.pressure_loss_coefficient([45.0, 50.0], 64.0)


class TestUpstreamStraightLength:
    """ISO 7235 6.5.2.2.1, the settling length before the test object."""

    def test_a_small_duct_takes_the_two_metre_floor(self) -> None:
        # A 350 mm duct is 1,75 m of five diameters, so the floor binds.
        assert sm.upstream_straight_length(0.0962) == pytest.approx(2.0)

    def test_a_large_duct_takes_five_equivalent_diameters(self) -> None:
        equivalent = math.sqrt(4.0 * 0.5 / math.pi)
        assert sm.upstream_straight_length(0.5) == pytest.approx(5.0 * equivalent)

    def test_the_two_rules_cross_where_five_diameters_reach_two_metres(self) -> None:
        area = math.pi * (2.0 / 5.0) ** 2 / 4.0
        assert sm.upstream_straight_length(area) == pytest.approx(2.0)

    def test_the_published_profile_tolerance(self) -> None:
        assert sm.VELOCITY_PROFILE_TOLERANCE_PERCENT == pytest.approx(10.0)

    @pytest.mark.parametrize("bad", [0.0, -0.5])
    def test_an_area_that_is_not_positive_is_refused(self, bad: float) -> None:
        with pytest.raises(ValueError, match="area"):
            sm.upstream_straight_length(bad)


#: Five test points of an air-terminal device, ISO 5135 5.5.2 a): the
#: A-weighted level against the volume flow rate at a constant pressure loss
#: coefficient. Twenty decibels per decade is the sixth power of the velocity
#: a diffuser is usually quoted at.
DUTY = np.array([0.05, 0.1, 0.2, 0.4, 0.8])
DUTY_LEVELS = np.array([38.0, 44.5, 50.0, 56.5, 62.0])


class TestDuctSoundPowerLevel:
    """ISO 5135 Equation (1), and the formula it shares with ISO 7235."""

    def test_it_adds_the_end_reflection_back(self) -> None:
        found = sm.duct_sound_power_level([60.0, 62.0], [4.0, 2.0])
        assert found == pytest.approx([64.0, 64.0])

    def test_iso_5135_equation_two_is_iso_7235_equation_b_three(self) -> None:
        # ISO 5135 prints Delta L_r = 10 lg[1 + (c / 4 pi f)^2 (Omega / S)];
        # ISO 7235 prints D_td = 10 lg[1 + Omega / (4 pi f sqrt(S) / c)^2].
        # Expand either and they are the same expression, which is why the
        # library has one function for both.
        c, area = 343.0, DUCT_AREA
        for angle in sm.RADIATION_SOLID_ANGLES.values():
            printed = 10.0 * np.log10(
                1.0 + (c / (4.0 * math.pi * BANDS)) ** 2 * (angle / area)
            )
            found = sm.open_end_transmission_loss(BANDS, area, solid_angle=angle)
            assert found == pytest.approx(printed)

    def test_the_two_solid_angle_tables_agree_entry_for_entry(self) -> None:
        # Table 1 of ISO 5135 and Table B.1 of ISO 7235 print the same five
        # configurations with the same five values.
        assert list(sm.RADIATION_SOLID_ANGLES.values()) == pytest.approx(
            [2.0 * math.pi, math.pi, 4.0 * math.pi, 2.0 * math.pi, 4.0 * math.pi]
        )

    def test_mismatched_band_counts_are_refused(self) -> None:
        with pytest.raises(ValueError, match="one length"):
            sm.duct_sound_power_level([60.0, 62.0, 64.0], [4.0, 2.0])


class TestOperatingLine:
    """ISO 5135 5.5.2, the straight line fitted through the test points."""

    def test_a_clean_power_law_comes_back_as_its_slope(self) -> None:
        duty = np.array([0.05, 0.1, 0.2, 0.4, 0.8])
        levels = 50.0 + 20.0 * np.log10(duty / 0.2)
        line = sm.fit_operating_line(duty, levels)
        assert line.slope == pytest.approx(20.0)
        assert line.maximum_deviation == pytest.approx(0.0, abs=1e-9)
        assert line.level_at(0.2) == pytest.approx(50.0)

    def test_it_keeps_the_points_it_was_given(self) -> None:
        line = sm.fit_operating_line(DUTY, DUTY_LEVELS)
        assert line.duty == pytest.approx(DUTY)
        assert line.levels == pytest.approx(DUTY_LEVELS)

    def test_the_extension_range_is_half_to_twice(self) -> None:
        line = sm.fit_operating_line(DUTY, DUTY_LEVELS)
        assert line.valid_range == pytest.approx((0.025, 1.6))
        assert line.smallest_duty == pytest.approx(0.05)
        assert line.largest_duty == pytest.approx(0.8)

    def test_reading_inside_the_range_is_quiet(self) -> None:
        line = sm.fit_operating_line(DUTY, DUTY_LEVELS)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            found = line.level_at(0.3)
        assert found == pytest.approx(53.71, abs=5e-3)

    def test_the_range_ends_are_inside_it(self) -> None:
        line = sm.fit_operating_line(DUTY, DUTY_LEVELS)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            low = line.level_at(0.025)
            high = line.level_at(1.6)
        assert low < high

    def test_reading_beyond_it_warns(self) -> None:
        line = sm.fit_operating_line(DUTY, DUTY_LEVELS)
        with pytest.warns(sm.SilencerMeasurementWarning, match="5.5.2"):
            line.level_at(3.0)

    def test_points_that_are_not_a_straight_line_warn(self) -> None:
        bent = DUTY_LEVELS.copy()
        bent[2] += 6.0
        with pytest.warns(sm.SilencerMeasurementWarning, match="fitted line"):
            sm.fit_operating_line(DUTY, bent)

    def test_the_three_decibel_limit_and_the_half_decibel_report(self) -> None:
        assert sm.EXTRAPOLATION_MAX_DEVIATION_DB == pytest.approx(3.0)
        assert sm.EXTRAPOLATION_RANGE_FACTORS == (0.5, 2.0)
        assert sm.REPORTING_RESOLUTION_DB == pytest.approx(0.5)

    def test_one_point_cannot_make_a_line(self) -> None:
        with pytest.raises(ValueError, match="at least two points"):
            sm.fit_operating_line([0.2], [50.0])

    def test_every_point_at_one_duty_cannot_either(self) -> None:
        with pytest.raises(ValueError, match="more than one duty"):
            sm.fit_operating_line([0.2, 0.2, 0.2], [50.0, 51.0, 49.0])

    def test_two_arrays_of_different_lengths_are_refused(self) -> None:
        with pytest.raises(ValueError, match="one length"):
            sm.fit_operating_line([0.1, 0.2, 0.4], [50.0, 52.0])

    @pytest.mark.parametrize("bad", [0.0, -0.2])
    def test_a_duty_that_is_not_positive_is_refused(self, bad: float) -> None:
        with pytest.raises(ValueError, match="duty"):
            sm.fit_operating_line([0.1, bad], [50.0, 52.0])


class TestOperatingLinePlot:
    """The renderer, checked on what it draws rather than by looking."""

    @staticmethod
    def _axes() -> object:
        matplotlib = pytest.importorskip("matplotlib")
        matplotlib.use("Agg")
        line = sm.fit_operating_line(DUTY, DUTY_LEVELS)
        return line.plot()

    def test_it_draws_the_fit_and_the_points(self) -> None:
        ax = self._axes()
        assert len(ax.lines) == 2  # type: ignore[attr-defined]
        labels = [line.get_label() for line in ax.lines]  # type: ignore[attr-defined]
        assert any("Least-squares fit" in str(label) for label in labels)
        assert any("Measured points" in str(label) for label in labels)

    def test_the_measured_points_are_the_ones_given(self) -> None:
        ax = self._axes()
        points = next(
            line
            for line in ax.lines  # type: ignore[attr-defined]
            if "Measured" in str(line.get_label())
        )
        assert points.get_xdata() == pytest.approx(DUTY)
        assert points.get_ydata() == pytest.approx(DUTY_LEVELS)

    def test_the_duty_axis_is_logarithmic(self) -> None:
        # The fit is made in lg of the duty, so a linear axis would draw a
        # straight line as a curve.
        assert self._axes().get_xscale() == "log"  # type: ignore[attr-defined]

    def test_the_duty_ticks_are_plain_decimals(self) -> None:
        # A log axis labels 0,1 as 10^-1 by default, which reads as an
        # exponent rather than as the flow rate a point was taken at.
        ax = self._axes()
        ax.figure.canvas.draw()  # type: ignore[attr-defined]
        labels = [
            text.get_text()
            for text in ax.get_xticklabels()  # type: ignore[attr-defined]
            if text.get_text()
        ]
        assert "0.05" in labels
        assert not any("10" in label and "^" in label for label in labels)

    def test_the_two_extrapolated_ends_are_shaded(self) -> None:
        ax = self._axes()
        assert len(ax.patches) == 2  # type: ignore[attr-defined]

    def test_the_title_carries_the_worst_deviation(self) -> None:
        ax = self._axes()
        assert "0.30 dB" in ax.get_title()  # type: ignore[attr-defined]

    def test_the_spanish_labels(self) -> None:
        matplotlib = pytest.importorskip("matplotlib")
        matplotlib.use("Agg")
        line = sm.fit_operating_line(DUTY, DUTY_LEVELS)
        ax = line.plot(language="es")
        assert "Recta de servicio" in ax.get_title()
        labels = [artist.get_label() for artist in ax.lines]
        assert any("mínimos cuadrados" in str(label) for label in labels)
        # The slope and the deviation carry a decimal comma in Spanish, and
        # the unit is translated with them.
        assert any("19,9 dB/década" in str(label) for label in labels)
        assert "0,30 dB" in ax.get_title()

    def test_the_spanish_duty_ticks_use_a_decimal_comma(self) -> None:
        matplotlib = pytest.importorskip("matplotlib")
        matplotlib.use("Agg")
        line = sm.fit_operating_line(DUTY, DUTY_LEVELS)
        ax = line.plot(language="es")
        ax.figure.canvas.draw()
        labels = [text.get_text() for text in ax.get_xticklabels()]
        assert "0,05" in labels
