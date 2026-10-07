#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Verdicts at a printed limit that do not hang on the last bits of a float.

Every case below puts a quantity exactly on a printed limit in decimal: two
readings whose difference is the 6 dB of a background criterion, a ratio of
two areas that is the 0,6 of a range, a mean that is a half. In binary such a
quantity comes out a few units in the last place off the limit, and which way
depends on the readings: 32,3 - 26,3 dB lands under 6 dB and 32,2 - 26,2 dB
over it on the machines this library is tested on. Each verdict is therefore
checked with readings that land on both sides, and the assertion is the
decimal verdict for both. Nothing here asserts which side a residual falls
on, so the cases hold on any platform and with the JIT kernels as well.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

from phonometry import (
    building,
    electroacoustics,
    emission,
    environment,
    hearing,
    materials,
    metrology,
    noise_control,
    room,
    vibration,
)

#: Pairs of readings whose difference is the key in decimal, one landing under
#: it and one over it in binary on the reference machines.
_PAIRS: dict[float, tuple[tuple[float, float], tuple[float, float]]] = {
    3.0: ((32.3, 29.3), (32.2, 29.2)),
    6.0: ((32.3, 26.3), (32.2, 26.2)),
    9.0: ((32.3, 23.3), (32.2, 23.2)),
    10.0: ((32.3, 22.3), (32.2, 22.2)),
    15.0: ((35.3, 20.3), (35.2, 20.2)),
}


def _pairs(limit: float) -> list[tuple[float, float]]:
    return list(_PAIRS[limit])


# ---------------------------------------------------------------------------
# Background corrections of a band level (a margin of two readings)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("signal", "background"), _pairs(6.0))
def test_floor_covering_background_subtracts_at_6_db(
    signal: float, background: float
) -> None:
    # ISO 16251-1 Formula (2): 6 dB is the first margin it energy-subtracts.
    corrected, limited = building.background_corrected_level([signal], [background])
    expected = 10.0 * math.log10(10.0 ** (signal / 10.0) - 10.0 ** (background / 10.0))
    assert corrected[0] == pytest.approx(expected, abs=1e-9)
    assert not bool(limited[0])


@pytest.mark.parametrize(("signal", "background"), _pairs(15.0))
def test_floor_covering_background_leaves_15_db_alone(
    signal: float, background: float
) -> None:
    corrected, limited = building.background_corrected_level([signal], [background])
    assert corrected[0] == signal
    assert not bool(limited[0])


@pytest.mark.parametrize(("signal", "background"), _pairs(6.0))
def test_lab_background_caps_at_6_db(signal: float, background: float) -> None:
    # ISO 10140-4 4.3: a margin of 6 dB or less takes the fixed 1,3 dB.
    with pytest.warns(building.LabInsulationWarning, match="at or below 6 dB"):
        corrected = building.background_correction([signal], [background])
    assert corrected[0] == pytest.approx(signal - 1.3, abs=1e-12)


@pytest.mark.parametrize(("signal", "background"), _pairs(15.0))
def test_lab_background_leaves_15_db_alone(signal: float, background: float) -> None:
    corrected = building.background_correction([signal], [background])
    assert corrected[0] == signal


@pytest.mark.parametrize(("signal", "background"), _pairs(15.0))
def test_iso3744_k1_is_not_zero_at_15_db(signal: float, background: float) -> None:
    # ISO 3744 8.2.3: K1 is zero only above 15 dB; at 15 dB it is Formula (13).
    k1 = emission.background_noise_correction(
        np.array([signal]), np.array([background])
    )
    assert k1[0] == pytest.approx(-10.0 * math.log10(1.0 - 10.0**-1.5), abs=1e-9)


@pytest.mark.parametrize(("signal", "background"), _pairs(6.0))
def test_iso3744_6_db_is_not_below_the_criterion(
    signal: float, background: float
) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", emission.SoundPowerWarning)
        k1 = emission.background_noise_correction(
            np.array([signal]), np.array([background])
        )
    assert k1[0] == pytest.approx(-10.0 * math.log10(1.0 - 10.0**-0.6), abs=1e-9)


@pytest.mark.parametrize(("signal", "background"), _pairs(15.0))
def test_iso3745_k1_is_zero_at_15_db(signal: float, background: float) -> None:
    # ISO 3745 9.4.2: K1 is zero from 15 dB.
    k1 = emission.precision_background_correction(
        np.array([signal]), np.array([background]), np.array([1000.0])
    )
    assert k1[0] == 0.0


@pytest.mark.parametrize(("signal", "background"), _pairs(10.0))
def test_iso3745_10_db_is_not_below_the_mid_band_criterion(
    signal: float, background: float
) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", emission.SoundPowerWarning)
        k1 = emission.precision_background_correction(
            np.array([signal]), np.array([background]), np.array([1000.0])
        )
    assert k1[0] == pytest.approx(-10.0 * math.log10(1.0 - 10.0**-1.0), abs=1e-9)


@pytest.mark.parametrize(("signal", "background"), _pairs(15.0))
def test_iso3741_k1_is_zero_at_15_db(signal: float, background: float) -> None:
    k1 = emission.reverberation_background_correction([signal], [background], [1000.0])
    assert k1[0] == 0.0


@pytest.mark.parametrize(("signal", "background"), _pairs(15.0))
def test_workstation_k1_is_not_zero_at_15_db(signal: float, background: float) -> None:
    correction, held = emission.background_noise_correction_at_workstation(
        [signal], [background]
    )
    assert np.atleast_1d(correction)[0] == pytest.approx(
        -10.0 * math.log10(1.0 - 10.0**-1.5), abs=1e-9
    )
    assert not held


@pytest.mark.parametrize(("signal", "background"), _pairs(6.0))
def test_screen_background_at_6_db_is_acceptable(
    signal: float, background: float
) -> None:
    # ISO 11821 5.7: under 6 dB is unacceptable; 6 dB itself is corrected.
    corrected = noise_control.background_corrected_level_db([signal], [background])
    expected = 10.0 * math.log10(10.0 ** (signal / 10.0) - 10.0 ** (background / 10.0))
    assert corrected[0] == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize(("signal", "background"), _pairs(10.0))
def test_screen_background_at_10_db_is_still_corrected(
    signal: float, background: float
) -> None:
    corrected = noise_control.background_corrected_level_db([signal], [background])
    expected = 10.0 * math.log10(10.0 ** (signal / 10.0) - 10.0 ** (background / 10.0))
    assert corrected[0] == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize(("signal", "background"), _pairs(10.0))
def test_silencer_background_10_db_is_the_last_row(
    signal: float, background: float
) -> None:
    # ISO 11820 Table 1 prints 0,5 dB against 10 dB, and nothing above it.
    correction = noise_control.silencer_background_correction_db([signal - background])
    assert correction[0] == 0.5


@pytest.mark.parametrize(("signal", "background"), _pairs(9.0))
def test_silencer_background_9_db_reads_its_own_row(
    signal: float, background: float
) -> None:
    correction = noise_control.silencer_background_correction_db([signal - background])
    assert correction[0] == 0.5


@pytest.mark.parametrize(("signal", "background"), _pairs(10.0))
def test_barrier_background_10_db_takes_nothing_off(
    signal: float, background: float
) -> None:
    # ISO 10847 6.4 prints rows to 9 dB; 10 dB is past the table.
    correction = environment.barrier_background_correction_db([signal - background])
    assert correction[0] == 0.0


@pytest.mark.parametrize(("signal", "background"), _pairs(6.0))
def test_spatial_decay_6_db_is_unusable(signal: float, background: float) -> None:
    # ISO 14257 5.1.4: a margin at or under 6 dB has no correction.
    with pytest.warns(room.SpatialDecayWarning):
        check = room.check_background_margin([signal], [background])
    assert bool(check.unusable[0])
    assert check.margins_db[0] == signal - background


@pytest.mark.parametrize(("signal", "background"), _pairs(10.0))
def test_spatial_decay_10_db_is_satisfied(signal: float, background: float) -> None:
    check = room.check_background_margin([signal], [background])
    assert check.satisfied
    assert not bool(check.needs_correction[0])


@pytest.mark.parametrize(("signal", "background"), _pairs(3.0))
def test_residual_at_3_db_is_not_reliable(signal: float, background: float) -> None:
    # ISO 1996-2 10.4: the residual has to be more than 3 dB below.
    with pytest.warns(environment.EnvironmentalMeasurementWarning):
        result = environment.residual_sound_correction(signal, background)
    assert not result.reliable


@pytest.mark.parametrize(("signal", "background"), _pairs(6.0))
def test_cabin_internal_level_at_6_db_is_corrected(
    signal: float, background: float
) -> None:
    # ISO 11957 6.7: at least 6 dB over the background, corrected up to 10 dB.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        level = noise_control.internal_noise_level(
            [signal], background_level=background
        )
    assert level < signal


@pytest.mark.parametrize(("signal", "background"), _pairs(10.0))
def test_cabin_internal_level_at_10_db_is_corrected(
    signal: float, background: float
) -> None:
    level = noise_control.internal_noise_level([signal], background_level=background)
    assert level < signal


@pytest.mark.parametrize(("signal", "background"), _pairs(3.0))
def test_cabin_spread_of_3_db_asks_for_three_positions(
    signal: float, background: float
) -> None:
    # ISO 11957 7.2.1: positions at least the spread in dB, three to begin with.
    check = noise_control.check_source_positions(
        [[signal, 20.0], [background, 20.0], [background, 20.0]]
    )
    assert check.required_positions == 3
    assert check.satisfied


@pytest.mark.parametrize(("room_volume", "cabin_volume"), [(1.4, 0.07), (9.4, 0.47)])
def test_cabin_volume_ratio_of_exactly_20_is_satisfied(
    room_volume: float, cabin_volume: float
) -> None:
    # Both ratios are 20 in decimal; clause 10 asks for at least 20.
    statement = noise_control.uncertainty_conditions(
        room_volume_m3=room_volume, cabin_volume_m3=cabin_volume
    )
    assert statement.ratio_satisfied


@pytest.mark.parametrize(("level", "background"), _pairs(6.0))
def test_a_cabin_band_exactly_6_db_over_its_background_does_not_warn(
    level: float, background: float
) -> None:
    # ISO 11957 6.4 by way of ISO 3741: at least 6 dB over the background.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", noise_control.CabinInsulationWarning)
        warnings.filterwarnings(
            "error",
            message="ISO 11957 asks for at least",
            category=noise_control.CabinInsulationWarning,
        )
        result = noise_control.cabin_insulation(
            [level + 20.0],
            [level],
            frequencies=[1000.0],
            cabin_background_levels=[background],
        )
    assert result.insulation[0] > 20.0


# ---------------------------------------------------------------------------
# Spreads, ratios and deviations of readings against a printed limit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("high", "low"), _pairs(6.0))
def test_silencer_spread_of_6_db_keeps_three_positions(high: float, low: float) -> None:
    # ISO 11691 Figure 8: five positions only past the 6 dB spread at 1 kHz.
    assert noise_control.microphone_positions_required([high, low, low], 1000.0) == 3


@pytest.mark.parametrize(
    ("duct", "element"), [(2.01, 3.35), (1.23, 2.05), (0.119, 0.07), (0.493, 0.29)]
)
def test_silencer_area_ratio_at_the_range_ends_does_not_warn(
    duct: float, element: float
) -> None:
    # ISO 11691 4.5: between 0,6 and 1,7 times the area, both ends included.
    with warnings.catch_warnings():
        warnings.simplefilter("error", noise_control.SilencerMeasurementWarning)
        ratio = noise_control.substitution_area_ratio(duct, element)
    assert ratio == pytest.approx(round(ratio, 1), abs=1e-12)


@pytest.mark.parametrize(("high", "low"), _pairs(3.0))
def test_impulse_spread_of_3_db_is_not_repeated(high: float, low: float) -> None:
    # ISO 11821 5.6.2.1: past 3 dB the measurement is repeated, at 3 dB it is not.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        level = noise_control.impulse_mean_level_db([high, low, low])
    assert low < level < high


@pytest.mark.parametrize(("high", "low"), _pairs(3.0))
def test_repeated_levels_spreading_3_db_do_not_warn(high: float, low: float) -> None:
    # ISO 1996-2 Formula (20) is flagged only past a 3 dB spread.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        environment.uncertainty_from_repeated_measurements([high, low, low])


@pytest.mark.parametrize(("tone", "neighbour"), [(32.3, 27.3), (32.2, 27.2)])
def test_a_band_exactly_5_db_over_its_neighbours_is_flagged(
    tone: float, neighbour: float
) -> None:
    # ISO 1996-2 Annex K: from 500 Hz a band 5 dB or more above both neighbours.
    flags = environment.tonal_seeking_survey(
        [neighbour, tone, neighbour], [800.0, 1000.0, 1250.0]
    )
    assert bool(flags[1])


@pytest.mark.parametrize(
    ("open_loop", "at_microphone", "at_listener"),
    [(-3.3, 60.3, 67.0), (-2.2, 80.2, 88.0)],
)
def test_a_loop_gain_exactly_at_the_margin_is_stable(
    open_loop: float, at_microphone: float, at_listener: float
) -> None:
    # Long Eq. (18.21): stable while the loop gain is at most minus the margin.
    result = electroacoustics.feedback_stability(
        open_loop, at_microphone, at_listener, stability_margin=10.0
    )
    assert result.loop_gain == pytest.approx(-10.0, abs=1e-12)
    assert result.is_stable


@pytest.mark.parametrize(("value", "requirement"), [(32.3, 30.3), (32.2, 30.2)])
def test_a_value_exactly_u_above_a_minimum_does_not_provably_exceed_it(
    value: float, requirement: float
) -> None:
    # ISO 12999-1 Formula (5) is a strict inequality.
    assert not building.satisfies_lower_requirement(value, 2.0, requirement)


@pytest.mark.parametrize(("value", "requirement"), [(30.9, 32.2), (31.4, 32.7)])
def test_a_value_exactly_u_below_a_maximum_does_not_provably_stay_under_it(
    value: float, requirement: float
) -> None:
    # Formula (4), strict too: 30,9 + 1,3 is 32,2 in decimal, under it in binary.
    assert not building.satisfies_upper_requirement(value, 1.3, requirement)


def test_like_elements_couple_strongly_at_exactly_3_db() -> None:
    # ISO 12354-1 (E.3): Dv,ij >= 3 - 10 lg(mi fcj / (mj fci)). These masses
    # and frequencies give a ratio of 1 in decimal, a unit under it in binary.
    satisfied = building.strong_coupling_satisfied([3.0], 0.3, 3.0, 0.1, 1.0)
    assert bool(satisfied[0])


@pytest.mark.parametrize(("frame", "fluid"), [(0.01, 0.05), (0.07, 0.35)])
def test_a_modulus_ratio_of_exactly_0_2_is_limp(frame: float, fluid: float) -> None:
    # Doutres: limp while |Kc / Kf| does not exceed 0,2.
    assert materials.limp_frame_applicable(frame, fluid_bulk_modulus=fluid)


@pytest.mark.parametrize(("with_specimen", "empty"), [(0.009, 0.008), (0.01, 0.009)])
def test_an_air_correction_of_exactly_0_05_does_not_warn(
    with_specimen: float, empty: float
) -> None:
    # ISO 354-related clause 4.2.1 of the ceiling standard: at most 0,05.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        correction = materials.air_absorption_correction(
            volume_m3=200.0,
            specimen_area_m2=16.0,
            attenuation_with=[with_specimen],
            attenuation_empty=[empty],
        )
    assert correction[0] == pytest.approx(0.05, abs=1e-12)


@pytest.mark.parametrize(("gas", "frame"), [(0.007, 0.07), (0.07, 0.7)])
def test_an_enclosed_gas_share_of_exactly_a_tenth_is_disregarded(
    gas: float, frame: float
) -> None:
    # EN 29052-1 8.2: below 10 kPa s/m2 the gas is negligible up to a tenth,
    # and s' is then s't, stated in the report; past it s' cannot be resolved.
    with pytest.warns(materials.DynamicStiffnessWarning, match="disregarded"):
        stiffness = materials.installed_dynamic_stiffness(
            frame, airflow_resistivity_kpa_s_m2=5.0, gas_stiffness_n_m3=gas
        )
    assert stiffness == frame


@pytest.mark.parametrize(("first", "second"), [(32.3, 31.3), (32.2, 31.2)])
def test_a_difference_of_exactly_one_jnd_is_perceptible(
    first: float, second: float
) -> None:
    # ISO 3382-1 Table A.1: the JND of C80 is 1 dB.
    assert room.perceptibly_different("C80", [first], [second])


@pytest.mark.parametrize(("first", "second"), [(2.05, 1.95), (1.23, 1.17)])
def test_a_difference_of_exactly_one_relative_jnd_is_perceptible(
    first: float, second: float
) -> None:
    # ISO 3382-1 Table A.1: the JND of EDT is 5 %, here of the mean of the
    # two; 2,05 and 1,95 s differ by 0,1 s, which is 5 % of 2,0 s.
    assert room.perceptibly_different("EDT", [first], [second])


@pytest.mark.parametrize(("measured", "mass"), [(0.525, 2.0), (0.21, 5.0)])
def test_a_rigid_mass_exactly_5_percent_off_is_within_tolerance(
    measured: float, mass: float
) -> None:
    # ISO 7626-2: the accelerance of a rigid mass is 1/m to within 5 %.
    result = vibration.rigid_mass_calibration_check([measured], [100.0], mass)
    assert bool(result.within_tolerance[0])


@pytest.mark.parametrize(("before", "after"), [(2.64, 3.3), (3.24, 4.05)])
def test_a_growth_of_exactly_25_percent_is_not_tolerable(
    before: float, after: float
) -> None:
    # E DIN 4150-2 6.5.3.6: the requirements count as met for growth under 25 %.
    from phonometry.vibration.immission.train_categories import railway_guide_values

    change = vibration.assess_railway_change(
        kb_fmax_before=before,
        kb_fmax_after=after,
        kb_ftr_before=0.05,
        kb_ftr_after=0.05,
        guide=railway_guide_values("residential"),
    )
    assert not change.kb_fmax_met


@pytest.mark.parametrize(("before", "after"), [(0.28, 0.35), (0.16, 0.2)])
def test_a_kb_ftr_growth_of_exactly_25_percent_is_not_tolerable(
    before: float, after: float
) -> None:
    # E DIN 4150-2 6.5.3.6, the same 25 % for KB_FTr above A_r; 0,28 to 0,35
    # comes out 24,999 999 999 999 98 % in binary.
    from phonometry.vibration.immission.train_categories import railway_guide_values

    change = vibration.assess_railway_change(
        kb_fmax_before=0.3,
        kb_fmax_after=0.3,
        kb_ftr_before=before,
        kb_ftr_after=after,
        guide=railway_guide_values("residential"),
    )
    assert change.kb_fmax_met
    assert not change.kb_ftr_met


@pytest.mark.parametrize(("first", "second"), [(32.3, 31.8), (32.2, 31.7)])
def test_a_difference_equal_to_the_combined_uncertainty_is_not_significant(
    first: float, second: float
) -> None:
    # ISO 4869-1 Annex: significant only when it exceeds the root sum of squares.
    result = hearing.assess_attenuation_difference(
        [first],
        [second],
        first_expanded_uncertainty_db=[0.3],
        second_expanded_uncertainty_db=[0.4],
        frequencies=[1000.0],
    )
    assert not bool(result.significant[0])


@pytest.mark.parametrize(("position", "reference"), [(32.3, 29.8), (32.2, 29.7)])
def test_a_field_position_exactly_2_5_db_off_is_uniform(
    position: float, reference: float
) -> None:
    # ISO 4869-1 Annex: each position within ±2,5 dB of the reference point.
    levels = dict.fromkeys(("front", "back", "left", "right", "down"), [reference])
    check = hearing.check_reat_sound_field(
        {**levels, "up": [position]}, [reference], frequencies=[1000.0]
    )
    assert bool(np.all(check.uniform))


@pytest.mark.parametrize(("right", "left"), _pairs(3.0))
def test_left_and_right_exactly_3_db_apart_are_balanced(
    right: float, left: float
) -> None:
    levels = dict.fromkeys(("front", "back", "up", "down"), [left])
    check = hearing.check_reat_sound_field(
        {**levels, "right": [right], "left": [left]}, [left], frequencies=[1000.0]
    )
    assert bool(np.all(check.balanced))


@pytest.mark.parametrize(("high", "low"), [(32.3, 27.3), (32.2, 27.2)])
def test_a_rotation_varying_exactly_the_table_1_allowance_is_diffuse(
    high: float, low: float
) -> None:
    # ISO 4869-1 4.2.2 b): a microphone of 10 dB rejection may see 5 dB.
    levels = dict.fromkeys(("front", "back", "left", "right", "up", "down"), [high])
    check = hearing.check_reat_sound_field(
        levels,
        [high],
        rotation_levels_db=[[high], [low]],
        free_field_rejection_db=10.0,
        frequencies=[1000.0],
    )
    assert bool(np.all(check.diffuse))


@pytest.mark.parametrize("start", [26.2, 26.3])
def test_an_ear_step_exactly_1_db_off_is_linear(start: float) -> None:
    # EN 352-4 / ISO 4869-1 linearity: each 5 dB step is 5 dB ± 1 dB at the ear.
    ear = [start, round(start + 6.0, 1), round(start + 11.0, 1), round(start + 16.0, 1)]
    result = hearing.assess_anr_linearity([90.0, 95.0, 100.0, 105.0], [ear])
    assert result.passes


@pytest.mark.parametrize(("high", "low"), _pairs(3.0))
def test_three_whole_days_spreading_3_db_raise_the_advisory(
    high: float, low: float
) -> None:
    # ISO 9612 11.3: three whole-day levels spanning 3 dB or more ask for more.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        hearing.full_day_exposure([high, low, low], 8.0)
    assert any("spanning 3.0 dB" in str(w.message) for w in caught)


@pytest.mark.parametrize("centre", [60.4, 60.0])
def test_a_sampling_contribution_of_exactly_3_5_db_is_not_above_it(
    centre: float,
) -> None:
    # ISO 9612 Table C.4: seven samples with u1 = 4,0 dB give c1 u1 = 3,5 dB,
    # and 10.4 asks for a revised plan only above it. Three readings 4 dB over
    # the centre, three 4 dB under it and one on it have u1 = 4 in decimal.
    high, low = round(centre + 4.0, 1), round(centre - 4.0, 1)
    result = hearing.job_based_exposure([high] * 3 + [low] * 3 + [centre], 8.0)
    assert result.c1u1 == pytest.approx(3.5, abs=1e-9)
    assert not result.sampling_advisory


@pytest.mark.parametrize(("high", "low"), _pairs(3.0))
def test_task_samples_spanning_3_db_raise_the_advisory(high: float, low: float) -> None:
    # ISO 9612 9.3: task samples spanning 3 dB or more ask for more.
    task = hearing.Task(samples=(high, low, low), duration_hours=8.0)
    result = hearing.task_based_exposure([task], warn=False)
    assert result.tasks[0].spread_advisory
    assert result.sampling_advisory


# ---------------------------------------------------------------------------
# Qualification criteria and classifications read off computed quantities
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("first", "second"), [(32.3, 31.8), (32.2, 31.7)])
def test_two_scans_exactly_s_over_2_apart_meet_criterion_1(
    first: float, second: float
) -> None:
    # ISO 9614-3 Criterion 1: the two scans agree to within s/2.
    scan = np.full((4, 1), 1.0e-6)
    indicators = emission.precision_field_indicators(
        scan, 10.0 * np.log10(scan / 1.0e-12) + 3.0
    )
    criteria = emission.precision_qualification(
        indicators,
        scan_intensity_level_1=np.array([first]),
        scan_intensity_level_2=np.array([second]),
        repeatability_limit=1.0,
        frequencies=np.array([1000.0]),
    )
    assert criteria.criterion_1 is not None
    assert bool(criteria.criterion_1[0])


@pytest.mark.parametrize(("highest", "other"), [(40.2, 30.2), (40.3, 30.3)])
def test_a_line_exactly_10_db_under_the_highest_is_still_a_tone_line(
    highest: float, other: float
) -> None:
    # IEC 61400-11 9.5.3: tone lines are within 10 dB of the highest one.
    frequencies = np.arange(400.0, 601.0, 1.0)
    levels = np.full(frequencies.size, 10.0)
    peak = int(np.argmin(np.abs(frequencies - 500.0)))
    levels[peak] = highest
    levels[peak + 3] = other
    result = environment.wind_turbine_tonality(
        levels, frequencies, tone_frequency=500.0
    )
    both = 10.0 * math.log10(10.0 ** (highest / 10.0) + 10.0 ** (other / 10.0))
    assert result.tone_level == pytest.approx(both, abs=1e-9)


def _narrowband(background: float) -> tuple[np.ndarray, np.ndarray, int]:
    """A flat 1 Hz spectrum about 500 Hz and the index of its 500 Hz line."""
    frequencies = np.arange(400.0, 601.0, 1.0)
    return frequencies, np.full(frequencies.size, background), 100


# The energy mean of equal lines is that level only to its last bits, so a
# line exactly 6 dB over it lands either side; these backgrounds give both.
@pytest.mark.parametrize("background", [21.3, 20.0])
def test_a_peak_exactly_6_db_over_the_screen_average_is_no_possible_tone(
    background: float,
) -> None:
    # IEC 61400-11 9.5.2: a possible tone is more than 6 dB above the energy
    # average of the critical band without the peak and its two neighbours.
    # The neighbours are low, so the peak still classifies as a tone line.
    frequencies, levels, peak = _narrowband(background)
    levels[peak] = round(background + 6.0, 1)
    levels[peak - 1] = levels[peak + 1] = round(background - 20.0, 1)
    result = environment.wind_turbine_tonality(
        levels, frequencies, tone_frequency=500.0
    )
    assert not result.has_identified_tone


@pytest.mark.parametrize("background", [20.3, 20.0])
def test_a_line_exactly_6_db_over_l70_is_not_masking_noise(background: float) -> None:
    # IEC 61400-11 9.5.3: masking lines are those less than L70 + 6 dB.
    frequencies, levels, peak = _narrowband(background)
    levels[peak] = round(background + 15.0, 1)
    levels[peak - 30] = round(background + 6.0, 1)
    result = environment.wind_turbine_tonality(
        levels, frequencies, tone_frequency=500.0
    )
    expected = background + 10.0 * math.log10(result.critical_bandwidth / 1.5)
    assert result.masking_level == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("background", [20.4, 20.0])
def test_a_line_exactly_6_db_over_the_masking_average_is_no_tone_line(
    background: float,
) -> None:
    # IEC 61400-11 9.5.3: tone lines are those above L_pn,avg + 6 dB.
    frequencies, levels, peak = _narrowband(background)
    levels[peak] = round(background + 15.0, 1)
    levels[peak - 30] = round(background + 6.0, 1)
    result = environment.wind_turbine_tonality(
        levels, frequencies, tone_frequency=500.0
    )
    assert result.tone_level == pytest.approx(levels[peak], abs=1e-9)


@pytest.mark.parametrize(("specimen", "background"), _pairs(10.0))
def test_an_alternating_airflow_margin_of_exactly_10_db_warns(
    specimen: float, background: float
) -> None:
    # ISO 9053-2: the specimen level has to clear the background by more.
    with pytest.warns(materials.AirflowResistanceWarning, match="background margin"):
        materials.alternating_airflow_resistance(
            specimen,
            specimen - 0.5,
            piston_stroke_specimen=1.0e-3,
            piston_stroke_termination=0.2e-3,
            frequency=2.0,
            cavity_volume=1.0e-3,
            background_level=background,
        )


#: Ten short-time intensities whose standard deviation is 0,6 of their mean
#: in decimal (a mean of 1,9 and of 1,1 W/m^2, four readings 0,9 of the mean
#: either side of it and six on it); F1 lands over 0,6 in binary for the
#: first and under it for the second.
_F1_ON_THE_LIMIT = (
    [3.61, 0.19, 3.61, 0.19, 1.9, 1.9, 1.9, 1.9, 1.9, 1.9],
    [2.09, 0.11, 2.09, 0.11, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1],
)


@pytest.mark.parametrize("samples", _F1_ON_THE_LIMIT)
def test_a_temporal_variability_of_exactly_0_6_is_stationary(
    samples: list[float],
) -> None:
    # ISO 9614-1 Table B.3: action (e) only for F1 > 0,6.
    indicators = emission.field_indicators(
        np.full(10, 121.0), np.ones(10), temporal_intensity=samples
    )
    assert indicators.field_is_stationary()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", emission.SoundPowerWarning)
        result = emission.sound_power_intensity_points(
            np.ones((10, 1)),
            np.ones(10),
            pressure_levels=np.full((10, 1), 121.0),
            pressure_residual_index=20.0,
            temporal_intensity=np.array(samples).reshape(-1, 1),
            frequencies=[1000.0],
        )
    assert (
        emission.ActionCode.REDUCE_TEMPORAL_VARIABILITY
        not in (result.required_actions()[0])
    )
    # A uniform field of ten equal intensities reaches the precision grade,
    # by band and A-weighted, once F1 lets it through the first gate.
    assert result.achieved_grade is not None
    assert result.achieved_grade[0] == "precision"
    assert result.achieved_grade_a == "precision"


#: Ten intensities, in W/m^2, for which 29 F4^2 is 10 in decimal: criterion 2
#: of the engineering grade at 1 kHz, N > C F4^2, sits on its limit. The first
#: set lands under 10 in binary, the second on or over it.
_CRITERION_2_ON_THE_LIMIT = (
    [3.0, 4.0, 1.6, 3.9, 5.6, 0.1, 0.5, 2.9, 3.8, 3.6],
    [4.6, 1.7, 0.8, 1.5, 5.3, 4.6, 2.8, 0.6, 3.0, 4.1],
)


@pytest.mark.parametrize("intensity", _CRITERION_2_ON_THE_LIMIT)
def test_ten_positions_exactly_c_f4_squared_do_not_meet_criterion_2(
    intensity: list[float],
) -> None:
    # ISO 9614-1 (B.2): N > C F4^2, strict, with C = 29 at 1 kHz (Table B.2).
    values = np.array(intensity).reshape(-1, 1)
    pressure = 10.0 * np.log10(values / 1.0e-12) + 1.0
    result = emission.sound_power_intensity_points(
        values,
        np.ones(10),
        pressure_levels=pressure,
        pressure_residual_index=20.0,
        frequencies=[1000.0],
        grade="engineering",
    )
    assert result.criterion_2 is not None
    assert not bool(result.criterion_2[0])
    assert result.achieved_grade is not None
    assert result.achieved_grade[0] == "none"
    # B.1.2: the A-weighted F4 of a lone 1 kHz band is the band's own, and
    # its engineering row is the same 29, so it reaches only the survey grade.
    surveyed = emission.sound_power_intensity_points(
        values,
        np.ones(10),
        pressure_levels=pressure,
        pressure_residual_index=20.0,
        frequencies=[1000.0],
        grade="survey",
    )
    assert surveyed.achieved_grade_a == "survey"


@pytest.mark.parametrize("offset", [5.3, 5.1])
def test_positions_exactly_twice_the_mean_distance_apart_meet_9_1_1_c(
    offset: float,
) -> None:
    # ISO 8297 9.1.1 c): D_m = l/N at most 2 d. A rectangle round a plant
    # 8 offsets by 4, its contour the offset away and started mid-side, so all
    # sixteen positions face a side: d is the offset and l/16 twice it.
    width, depth = round(8.0 * offset, 1), round(4.0 * offset, 1)
    plant = [(0.0, 0.0), (width, 0.0), (width, depth), (0.0, depth)]
    contour = [
        (0.0, -offset),
        (width + offset, -offset),
        (width + offset, depth + offset),
        (-offset, depth + offset),
        (-offset, -offset),
    ]
    laid = emission.plant_measurement_contour(
        plant, contour, characteristic_height_m=3.0, position_count=16
    )
    assert emission.check_plant_measurement(laid).requirement("position_spacing").holds
    smallest = emission.plant_measurement_contour(
        plant, contour, characteristic_height_m=3.0
    )
    assert smallest.position_count == 16


@pytest.mark.parametrize(("pressure", "intensity"), _pairs(10.0))
def test_a_pressure_intensity_indicator_of_exactly_10_db_qualifies(
    pressure: float, intensity: float
) -> None:
    # ISO 15186-3 6.4.2: F_pI at most 10 dB on a non-absorbing surface.
    from phonometry.building.measurement.intensity_insulation import (
        _FPI_LIMIT_REFLECTING,
        _low_frequency_qualification,
        _qualified,
    )

    indicator = _low_frequency_qualification(
        np.array([pressure]),
        np.array([intensity]),
        owner="test",
        absorbing_specimen_surface=False,
    )
    verdict = _qualified(indicator, _FPI_LIMIT_REFLECTING)
    assert verdict is not None
    assert bool(verdict[0])


def test_a_position_spread_of_exactly_1_5_db_does_not_warn() -> None:
    # ISO 3741 8.4.2.2: the sM criterion is exceeded only past 1,5 dB. Three
    # levels 1,5 dB apart have a standard deviation of exactly 1,5 dB.
    from phonometry.emission.sound_power_reverberation import (
        _position_sampling_warnings,
    )

    for start in (29.2, 30.3):
        levels = np.array([[start], [round(start + 1.5, 1)], [round(start + 3.0, 1)]])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _position_sampling_warnings(levels, stacklevel=2)
        assert not [w for w in caught if "sM" in str(w.message)]


@pytest.mark.parametrize(
    ("volume", "surface", "time"), [(255.51, 150.3, 1.7), (255.34, 150.2, 1.7)]
)
def test_a_reverberation_time_exactly_at_v_over_s_warns(
    volume: float, surface: float, time: float
) -> None:
    # ISO 3741 Table 1 / 5.2: T at or below V/S makes the room too absorptive.
    from phonometry.emission.sound_power_reverberation import (
        _room_qualification_warnings,
    )

    with pytest.warns(emission.SoundPowerWarning, match="V/S floor"):
        _room_qualification_warnings(
            np.array([80.0]), np.array([time]), volume, surface, np.array([1000.0])
        )


@pytest.mark.parametrize(
    ("band", "diameter", "velocity"), [(63.0, 0.1, 6.3), (63.0, 0.21, 13.23)]
)
def test_a_strouhal_number_of_exactly_one_is_outside_the_branch_fit(
    band: float, diameter: float, velocity: float
) -> None:
    # VDI 2081 Figures 17 and 18 hold only above a Strouhal number of one.
    from phonometry.noise_control.hvac import _vdi2081_branch_flow_noise

    level = _vdi2081_branch_flow_noise(
        np.array([band]),
        branch_diameter_m=diameter,
        branch_velocity=velocity,
        approach_velocity=velocity,
        rounding_ratio=None,
    )
    assert level[0] == -np.inf


def test_a_change_of_slope_of_exactly_5_db_is_not_encircled() -> None:
    # ICAO Annex 16 App. 2 4.3 Step 2: encircle a change of slope above 5 dB.
    from phonometry.aircraft.certification import _tone_marked_slopes

    spl = np.full(24, 63.9)
    spl[10:] = 68.9  # 68,9 - 63,9 is 5 dB in decimal and over it in binary
    _, marked = _tone_marked_slopes(spl, 2)
    assert not bool(np.any(marked))


def test_samples_equally_far_from_the_10_db_down_level_keep_the_inner_one() -> None:
    # The 10 dB-down points take the nearer sample; at a tie, the one inside.
    from phonometry.aircraft.certification import _ten_db_down_limits

    pnlt = np.array([50.0, 60.2, 60.4, 70.3, 60.4, 60.2, 50.0])
    assert _ten_db_down_limits(pnlt, 70.3 - 10.0) == (2, 4)


def test_burst_readings_exactly_10_percent_over_the_table_conform() -> None:
    # ISO 8041-1 12.13 and Table 7: within 10 % of the printed response. The
    # readings are the printed ones times 1,1 to six decimals, which binary
    # leaves a unit or two either side of 10 % from one row to the next.
    from phonometry.vibration.human.signal_burst import SIGNAL_BURST_RESPONSE

    measured = {
        cycles: {
            "rms": round(
                SIGNAL_BURST_RESPONSE["hand-arm", "band-limiting", cycles]["rms"] * 1.1,
                6,
            )
        }
        for cycles in (1, 2, 4, 8, 16, None)
    }
    verdict = vibration.verify_signal_burst_response(
        "hand-arm", "band-limiting", measured
    )
    assert verdict.passes


@pytest.mark.parametrize(("tone", "neighbour"), [(32.3, 27.3), (32.2, 27.2)])
def test_a_band_exactly_5_db_over_its_neighbours_takes_3_db(
    tone: float, neighbour: float
) -> None:
    # RD 1367/2007 Annex IV: from 3 dB to 5 dB, Kt = 3 dB, past 5 dB 6 dB.
    result = environment.assessment.spain.tonal_correction(
        [neighbour, tone, neighbour], [800.0, 1000.0, 1250.0]
    )
    assert result.correction == 3.0


@pytest.mark.parametrize(
    ("source", "receiver", "first", "second"),
    [(1.1, 3.7, 0.5, 47.5), (1.2, 1.2, 1.0, 23.0)],
)
def test_heights_a_tenth_of_the_distance_are_not_a_short_distance(
    source: float, receiver: float, first: float, second: float
) -> None:
    # ISO 10847 6.3: short distance when the height ratio exceeds 0,1.
    before, _ = environment.is_short_distance(
        source_height_m=source,
        receiver_height_m=receiver,
        barrier_height_m=1.0,
        source_to_barrier_m=first,
        barrier_to_receiver_m=second,
    )
    assert not before


#: Geometries whose "after" ratio of ISO 10847 6.3 is 0,1 in decimal, one
#: through each of its two conditions, landing over 0,1 in binary (the first
#: of each pair) and under it (the second); the other condition holds clearly.
_AFTER_ON_A_TENTH = (
    (0.1, 1.0, 1.1, 12.0, 5.0),
    (0.1, 1.0, 0.5, 6.0, 5.0),
    (1.0, 0.1, 1.1, 5.0, 12.0),
    (1.0, 0.1, 0.5, 5.0, 6.0),
)


@pytest.mark.parametrize(
    ("source", "receiver", "barrier", "first", "second"), _AFTER_ON_A_TENTH
)
def test_a_barrier_a_tenth_of_its_distance_is_not_a_short_distance_after(
    source: float, receiver: float, barrier: float, first: float, second: float
) -> None:
    # ISO 10847 6.3.1: both "after" ratios must exceed 0,1.
    _, after = environment.is_short_distance(
        source_height_m=source,
        receiver_height_m=receiver,
        barrier_height_m=barrier,
        source_to_barrier_m=first,
        barrier_to_receiver_m=second,
    )
    assert not after


@pytest.mark.parametrize(
    "levels", [[60.3, 64.8, 60.3], [60.2, 64.7, 60.2], [32.3, 36.8, 32.3]]
)
def test_an_operating_point_exactly_3_db_off_the_line_is_accepted(
    levels: list[float],
) -> None:
    # ISO 11691 5.5.2: the points sit within 3 dB of the fitted line.
    with warnings.catch_warnings():
        warnings.simplefilter("error", noise_control.SilencerMeasurementWarning)
        line = noise_control.fit_operating_line([1.0, 10.0, 100.0], levels)
    assert line.maximum_deviation == pytest.approx(3.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Halves rounded the way the standards print them
# ---------------------------------------------------------------------------


def test_a_protector_level_that_is_a_half_rounds_away_from_zero() -> None:
    from phonometry.hearing.hearing_protectors import _round_half_up

    assert _round_half_up(64.1 - 3.6) == 61  # 60,5 in decimal, under it in binary
    assert _round_half_up(-(64.1 - 3.6)) == -61


def test_a_db_hr_value_that_is_a_half_rounds_up() -> None:
    from phonometry.building.regulation.spain import _round_half_up

    assert _round_half_up(64.1 - 3.6) == 61.0
    # 64,1 - 1,35 is 62,75 in decimal and 62,749 999 999 999 99 in binary.
    assert _round_half_up(64.1 - 1.35, 1) == pytest.approx(62.8, abs=1e-12)


def test_a_pass_by_level_that_is_a_half_tenth_rounds_up() -> None:
    from phonometry.environment.sources.statistical_pass_by import _round_tenth

    # 64,1 - 1,35 is 62,75 in decimal and 62,749 999 999 999 99 in binary.
    assert _round_tenth(64.1 - 1.35) == pytest.approx(62.8, abs=1e-12)
    assert _round_tenth(40.65) == pytest.approx(40.7, abs=1e-12)


def test_iso_717_reductions_round_a_decimal_half_outwards() -> None:
    from phonometry.building.measurement.ratings import (
        _reduce,
        _round_half_up_tenths,
    )

    half = 64.1 - 1.35  # 62,75 in decimal, under it in binary
    np.testing.assert_allclose(
        _round_half_up_tenths(np.array([half, -half])), [62.8, -62.8], atol=1e-12
    )
    assert _reduce(64.1 - 3.6, one_decimal=False) == 61.0
    assert _reduce(half, one_decimal=True) == pytest.approx(62.8, abs=1e-12)


def test_a_declared_level_that_is_a_half_rounds_up() -> None:
    from phonometry.emission.declaration import _round_db

    assert _round_db(64.1 - 3.6) == 61


def test_a_practical_coefficient_mean_on_a_half_rounds_up() -> None:
    # ISO 11654 4.1: the mean of 0,03, 0,285 and 0,06 is 0,125, rounded to
    # 0,13 and then to the 0,15 step; a last-bit 0,1249 would give 0,10.
    alpha = [0.03, 0.285, 0.06] * 5
    np.testing.assert_allclose(
        materials.practical_absorption_coefficient(alpha), [0.15] * 5, atol=1e-12
    )


def test_a_loudness_value_on_a_half_hundredth_encodes_away_from_zero() -> None:
    # EBU Tech 3285 2.4: the value times 100, rounded half away from zero.
    from phonometry.io._bext import _encode_loudness

    assert _encode_loudness(-20.455) == -2046
    assert _encode_loudness(-22.645) == -2265


@pytest.mark.parametrize(
    ("stiffness", "impedance"), [(9805363.28, 1107.1), (10117801.28, 1124.6)]
)
def test_a_critically_damped_tapping_hammer_has_a_finite_force(
    stiffness: float, impedance: float
) -> None:
    # Hopkins Eq. (3.95): K m = 4 Zdp^2 is critical damping. With the hammer
    # of 0,5 kg these contact stiffnesses and impedances meet it in decimal,
    # and the discriminant of the pulse came out a few units in the last place
    # negative, so its square root was NaN.
    from phonometry.building.prediction import (
        force_pulse,
        tapping_cut_off_frequency,
        tapping_force_spectrum,
    )

    time = np.array([0.0, 1.0e-4, 2.0e-4])
    decay = stiffness / (2.0 * impedance)
    pulse = force_pulse(time, stiffness, impedance, impact_velocity=1.0)
    np.testing.assert_allclose(
        pulse, stiffness * time * np.exp(-decay * time), rtol=1e-6, atol=1e-9
    )
    assert tapping_cut_off_frequency(stiffness, impedance) == pytest.approx(
        decay / (2.0 * math.pi), rel=1e-6
    )
    spectrum = tapping_force_spectrum(
        np.array([100.0, 1000.0]), contact_stiffness=stiffness, impedance=impedance
    )
    assert bool(np.all(np.isfinite(spectrum.mean_square_force)))


# ---------------------------------------------------------------------------
# A raw reading against a limit raised by a printed share
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("area", "time_of_day", "kb_fmax"),
    [
        ("industrial", "day", 0.46),  # 0,4 x 1,15 lands under 0,46 in binary
        ("commercial", "night", 0.23),  # 0,2 x 1,15 lands under 0,23
        ("sensitive", "day", 0.115),  # 0,1 x 1,15 lands under 0,115
        ("industrial", "night", 0.345),  # 0,3 x 1,15 lands on 0,345
        ("mixed", "night", 0.1725),  # 0,15 x 1,15 lands on 0,1725
    ],
)
def test_a_kb_value_exactly_15_percent_over_a_u_is_within_the_uncertainty(
    area: str, time_of_day: str, kb_fmax: float
) -> None:
    # DIN 4150-2:1999 5.4: KB values are uncertain by up to about 15 %, which
    # Example 3 (C.3.3) reads as the requirement still met as a rule.
    guide = vibration.guide_values(area, time_of_day=time_of_day)
    verdict = vibration.assess_people_in_buildings(kb_fmax, guide)
    assert verdict.complies
    assert verdict.within_uncertainty
    assert verdict.criterion == "A_u"


def test_a_kb_value_past_the_15_percent_is_not_within_the_uncertainty() -> None:
    guide = vibration.guide_values("industrial", time_of_day="day")
    verdict = vibration.assess_people_in_buildings(0.461, guide, kb_ftr=0.1)
    assert not verdict.within_uncertainty


# ---------------------------------------------------------------------------
# Sums of partial powers: a share of the total, and a sign
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "intensity",
    [
        # The two strongest segments carry exactly half the power in decimal;
        # the cumulative sum lands over half in binary for the first set and
        # under it for the second, and B.1.3 asks for more than half.
        [3.5, 2.9, 2.4, 1.1, 1.0, 0.7, 0.5, 0.4, 0.2, 0.1],
        [3.9, 2.2, 1.4, 1.1, 0.9, 0.9, 0.6, 0.5, 0.5, 0.2],
    ],
)
def test_a_subset_carrying_exactly_half_the_power_is_not_enough(
    intensity: list[float],
) -> None:
    # ISO 9614-1 B.1.3: take segments until more than half has passed.
    result = emission.partial_power_concentration(np.array(intensity), np.ones(10))
    assert result.subset_positions == 3


#: Normal intensities, in tenths of a watt per square metre, that cancel in
#: decimal; their sum lands a few units in the last place above zero for the
#: first set and below it for the second.
_CANCELLING = (
    [9, 5, -5, 2, -6, -8, -5, 6, -3, 5],
    [9, 4, 9, -2, 1, -9, -1, -4, 1, -8],
)


@pytest.mark.parametrize("tenths", _CANCELLING)
def test_intensities_that_cancel_have_no_net_power_by_iso_9614_1(
    tenths: list[int],
) -> None:
    # Clause 9.2 and A.2.3: no positive net power, no test conditions met.
    intensity = np.array(tenths, dtype=np.float64).reshape(-1, 1) / 10.0
    with pytest.warns(emission.SoundPowerWarning):
        result = emission.sound_power_intensity_points(intensity, np.ones(10))
    assert bool(result.not_applicable_band[0])
    assert math.isnan(result.sound_power_level[0])


@pytest.mark.parametrize("tenths", _CANCELLING)
def test_intensities_that_cancel_have_no_net_power_by_iso_9614_2(
    tenths: list[int],
) -> None:
    intensity = np.array(tenths, dtype=np.float64).reshape(-1, 1) / 10.0
    with pytest.warns(emission.SoundPowerWarning):
        result = emission.sound_power_intensity(intensity, np.ones(10))
    assert bool(result.negative_band[0])
    assert math.isnan(result.sound_power_level[0])


@pytest.mark.parametrize("tenths", _CANCELLING)
def test_intensities_that_cancel_have_no_net_power_by_iso_9614_3(
    tenths: list[int],
) -> None:
    intensity = np.array(tenths, dtype=np.float64).reshape(-1, 1) / 10.0
    with pytest.warns(emission.SoundPowerWarning, match="not applicable"):
        result = emission.sound_power_intensity_precision(intensity, np.ones(10))
    assert bool(result.not_applicable_band[0])


@pytest.mark.parametrize("column", [[0.1, 0.2, -0.3], [0.3, -0.1, -0.2]])
def test_a_weighted_intensities_that_cancel_have_no_f4_in_either_order(
    column: list[float],
) -> None:
    # ISO 9614-1 B.1.2 and A.2.3: the A-weighted intensities per position of
    # the one band that counts (1 kHz) cancel in decimal, so F4_A is not
    # defined; read in either order they must not refuse the determination.
    intensity = np.column_stack([np.array(column + [0.0] * 7), np.full(10, -1.0)])
    areas = np.array([1.0, 1.0, 0.5] + [1.0] * 7)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", emission.SoundPowerWarning)
        result = emission.sound_power_intensity_points(
            intensity, areas, frequencies=[1000.0, 2000.0]
        )
    assert math.isnan(result.field_nonuniformity_a)
    assert math.isfinite(result.sound_power_level_a)


@pytest.mark.parametrize("partial", [[0.1, 0.2, -0.3, 0.0], [0.3, -0.1, -0.2, 0.0]])
def test_partial_powers_that_cancel_have_nothing_to_concentrate(
    partial: list[float],
) -> None:
    # ISO 9614-1 9.2: no positive net power, read the way
    # sound_power_intensity_points reads it, in either order.
    areas = np.ones(4)
    with pytest.raises(ValueError, match="clause 9.2"):
        emission.partial_power_concentration(partial, areas)


@pytest.mark.parametrize(
    "intensity",
    [[1.3, 1.1, 0.7, 0.3, 0.3, 0.3], [0.13, 0.11, 0.07, 0.03, 0.03, 0.03]],
)
def test_a_remainder_that_uses_up_the_error_factor_leaves_no_budget(
    intensity: list[float],
) -> None:
    # ISO 9614-1 (B.4): the top two carry 0,6 of the power and the other four
    # have F4 = 0,5, so 0,20 - 0,4 x (2/2) x 0,5 leaves Delta_alpha = 0 at the
    # precision grade; in binary it came out 1,4e-16 and asked for 3e30 more
    # positions.
    areas = np.ones(6)
    with pytest.raises(ValueError, match="exhaust the ISO 9614-1"):
        emission.partial_power_concentration(intensity, areas, grade="precision")


@pytest.mark.parametrize("tenths", _CANCELLING)
def test_samples_that_cancel_have_no_temporal_variability_indicator(
    tenths: list[int],
) -> None:
    # ISO 9614-1 (A.1) divides by the mean of the samples; a mean that is zero
    # in decimal leaves no indicator, whichever side of zero the bits fall.
    samples = np.array(tenths, dtype=np.float64) / 10.0
    with pytest.raises(ValueError, match="F1 of ISO 9614-1"):
        emission.temporal_variability_indicator(samples)


# ---------------------------------------------------------------------------
# Reported integers whose tie goes to the even neighbour
# ---------------------------------------------------------------------------

#: Pairs of readings whose difference is a half in decimal, landing under it
#: (15,5 dB, reported 16) and over it (14,5 dB, reported 14) in binary.
_HALVES = (((30.9, 15.4), 16), ((30.1, 15.6), 14))


@pytest.mark.parametrize(("pair", "reported"), _HALVES)
def test_a_screen_attenuation_on_a_half_is_reported_even(
    pair: tuple[float, float], reported: int
) -> None:
    # ISO 11821 7.4 c), a tie to the even decibel (Rule A of ISO 80000-1).
    result = noise_control.screen_attenuation(
        [pair[0]],
        [pair[1]],
        a_weighted_unscreened_level_db=pair[0],
        a_weighted_screened_level_db=pair[1],
    )
    assert int(result.rounded()[0]) == reported
    assert result.rounded_a_weighted() == reported


@pytest.mark.parametrize(("pair", "reported"), _HALVES)
def test_a_cabin_insulation_on_a_half_is_reported_even(
    pair: tuple[float, float], reported: int
) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", noise_control.CabinInsulationWarning)
        result = noise_control.cabin_insulation([pair[0]], [pair[1]])
    assert int(result.rounded()[0]) == reported


@pytest.mark.parametrize(("pair", "reported"), _HALVES)
def test_an_enclosure_insulation_on_a_half_is_reported_even(
    pair: tuple[float, float], reported: int
) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", noise_control.EnclosureInsulationWarning)
        result = noise_control.sound_pressure_insulation([pair[0]], [pair[1]])
    assert int(result.rounded()[0]) == reported


@pytest.mark.parametrize(("pair", "reported"), _HALVES)
def test_a_barrier_insertion_loss_on_a_half_is_reported_even(
    pair: tuple[float, float], reported: int
) -> None:
    # ISO 10847 clause 10 c): the reference microphone saw no change here.
    result = environment.measured_insertion_loss_direct(
        [50.0], [50.0], [pair[0]], [pair[1]]
    )
    assert int(result.rounded()[0]) == reported


@pytest.mark.parametrize(
    ("mid", "rating"), [([49.3, 30.9, 38.3], 40), ([32.1, 35.7, 41.7], 36)]
)
def test_an_rc_mid_frequency_average_on_a_half_rates_even(
    mid: list[float], rating: int
) -> None:
    # ANSI/ASA S12.2 Annex D: the RC rating is LMF to the nearest decibel;
    # these averages are 39,5 and 36,5 in decimal, under and over in binary.
    levels = np.full(10, 30.0)
    levels[5:8] = mid
    result = room.room_criterion(levels, room.noise_criteria.OCTAVE_BANDS)
    assert result.rating == rating


@pytest.mark.parametrize(
    ("sil_levels", "rating"),
    [([33.9, 31.2, 27.1, 25.8], 30.0), ([29.8, 25.4, 22.1, 20.7], 24.0)],
)
def test_an_nc_speech_interference_level_on_a_half_rates_even(
    sil_levels: list[float], rating: float
) -> None:
    # ANSI/ASA S12.2 5.2.2: NC-(SIL) when no band exceeds that curve; these
    # SIL are 29,5 and 24,5 in decimal, under and over in binary.
    levels = np.zeros(10)
    levels[5:9] = sil_levels
    result = room.noise_criterion(levels, room.noise_criteria.OCTAVE_BANDS)
    assert result.method == "SIL"
    assert result.rating == rating


# ---------------------------------------------------------------------------
# Differences, ratios and sums of readings the earlier passes filed as raw
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("high", "low"), _pairs(6.0))
def test_thirds_6_db_apart_are_flat_enough_at_125_hz(high: float, low: float) -> None:
    # ISO 11957 6.4 and 7.2.1: at 125 Hz the thirds may differ by up to 6 dB.
    check = noise_control.check_band_flatness(
        [high, 30.0, low], frequencies=[100.0, 125.0, 160.0]
    )
    assert bool(check.satisfied[0])


@pytest.mark.parametrize(("signal", "background"), [*_pairs(15.0), *_pairs(6.0)])
def test_iso_3747_reads_a_margin_on_its_criterion_as_decimal(
    signal: float, background: float
) -> None:
    # ISO 3747 8.1: K1 is zero only above 15 dB, and 6 dB is a valid margin,
    # so neither a 15 dB nor a 6 dB margin takes K1 to zero or marks it short.
    from phonometry.emission.sound_power_in_situ import _background_correction

    k1, met = _background_correction(np.array([signal - background]))
    assert float(k1[0]) > 0.0
    assert bool(met[0])


@pytest.mark.parametrize(("first", "second"), [(2.46, 2.05), (2.58, 2.15), (1.2, 1.0)])
def test_a_field_nonuniformity_ratio_of_exactly_1_2_meets_criterion_5(
    first: float, second: float
) -> None:
    # ISO 9614-3 criterion 5: 0,83 <= FS(1)/FS(2) <= 1,2, both ends included.
    scan = np.full((4, 1), 1.0e-6)
    indicators = emission.precision_field_indicators(
        scan, 10.0 * np.log10(scan / 1.0e-12) + 3.0
    )
    criteria = emission.precision_qualification(
        indicators,
        field_nonuniformity_1=np.array([first]),
        field_nonuniformity_2=np.array([second]),
    )
    assert criteria.criterion_5 is not None
    assert bool(criteria.criterion_5[0])


@pytest.mark.parametrize(
    ("measured", "tau", "method"),
    [(0.129, 0.125, "linear"), (0.119, 0.125, "linear"), (0.61, 0.125, "exponential")],
)
def test_a_decay_time_on_the_edge_of_its_interval_passes(
    measured: float, tau: float, method: str
) -> None:
    # ISO 8041-1 Tables 10 and 11: the printed time plus or minus its tolerance.
    verdict = vibration.verify_running_rms_decay(
        measured, integration_time_s=tau, method=method
    )
    assert verdict.passes


@pytest.mark.parametrize(("source", "output"), [(40.3, 20.3), (40.2, 20.2)])
def test_a_blocked_output_exactly_20_db_down_holds(
    source: float, output: float
) -> None:
    # ISO 10846-2: the output level at least 20 dB below the input level.
    check = vibration.check_blocked_output([100.0], [source], [output])
    assert bool(check.holds[0])


@pytest.mark.parametrize(("high", "low"), _pairs(10.0))
def test_a_spanish_low_frequency_difference_of_10_db_takes_nothing(
    high: float, low: float
) -> None:
    # RD 1367/2007 Annex IV: Kf is 0 dB up to 10 dB of LCeq - LAeq.
    assert environment.assessment.spain.low_frequency_correction(high, low) == 0.0


@pytest.mark.parametrize(("high", "low"), _pairs(15.0))
def test_a_spanish_impulsive_difference_of_15_db_takes_3_db(
    high: float, low: float
) -> None:
    # RD 1367/2007 Annex IV: Ki is 3 dB from 10 dB to 15 dB of LAIeq - LAeq.
    assert environment.assessment.spain.impulsive_correction(high, low) == 3.0


@pytest.mark.parametrize("weights", [[0.5, 0.3, 0.2], [0.2, 0.2, 0.2, 0.3, 0.1]])
def test_area_weights_adding_up_to_one_are_refused(weights: list[float]) -> None:
    # ISO 17497-2 Formula (6) divides by the total weight less one.
    levels = [70.0] * len(weights)
    with pytest.raises(ValueError, match="total area weight"):
        materials.directional_diffusion_coefficient(levels, area_weights=weights)


@pytest.mark.parametrize("external", [[54.97, 60.02, 65.02], [50.06, 55.06, 60.01]])
def test_external_steps_on_the_reading_tolerance_are_accepted(
    external: list[float],
) -> None:
    # EN 352-4 / 5.4.4: 5 dB steps, read to 0,05 dB.
    result = hearing.assess_anr_linearity(external, [[40.0, 45.0, 50.0]])
    assert result.passes


@pytest.mark.parametrize(("frequency", "velocity"), [(65.1, 43.02), (30.0, 30.0)])
def test_a_velocity_on_the_interpolated_guideline_keeps_to_it(
    frequency: float, velocity: float
) -> None:
    # DIN 4150-3 Table 1: the guideline between 50 and 100 Hz is interpolated,
    # 43,02 mm/s at 65,1 Hz for a commercial building, and keeping to it is
    # not exceeding it.
    assessment = vibration.assess_building_vibration(
        velocity, building_class="commercial", frequency_hz=frequency
    )
    assert assessment.within_guideline


@pytest.mark.parametrize(("section", "canal"), [(20.22, 33.7), (18.12, 30.2)])
def test_a_canal_section_of_six_tenths_of_the_canal_is_not_less_than_that(
    section: float, canal: float
) -> None:
    # IEC 60268-7 Annex B b): in the rest of the canal "an area less than 0,6"
    # of the canal's. 20,22 / 33,7 is 0,6 and comes out under it in binary.
    check = electroacoustics.verify_ear_canal_microphone(
        entrance_area_mm2=4.0,
        canal_section_area_mm2=section,
        volume_mm3=100.0,
        pink_noise_band_levels_db=[60.0, 61.0],
        open_levels_db=[80.0],
        sealed_levels_db=[60.0],
        ear_canal_area_mm2=canal,
    )
    assert not check.requirements["b"]


def _coupler_check(
    length_mm: float, depth_mm: float, diameter_mm: float
) -> metrology.CouplerCheck:
    microphone = metrology.ReciprocityMicrophone(
        equivalent_volume_m3=144e-9,
        resonance_frequency_hz=8200.0,
        loss_factor=1.05,
        front_cavity_volume_m3=0.534e-6,
        front_cavity_depth_m=depth_mm / 1000.0,
        front_cavity_diameter_m=18.6e-3,
    )
    coupler = metrology.PlaneWaveCoupler(
        length_m=length_mm / 1000.0, diameter_m=diameter_mm / 1000.0
    )
    return metrology.check_coupler(
        [250.0, 1000.0],
        coupler,
        (microphone, microphone),
        temperature_c=23.0,
        static_pressure_pa=101325.0,
        relative_humidity_percent=50.0,
    )


@pytest.mark.parametrize(
    ("length_mm", "depth_mm", "diameter_mm"),
    [(5.4, 1.95, 18.6), (7.9, 0.7, 18.6), (10.05, 1.95, 18.6), (5.9, 2.0, 13.2)],
)
def test_a_coupler_on_the_ends_of_the_recommended_ratio_is_recommended(
    length_mm: float, depth_mm: float, diameter_mm: float
) -> None:
    # IEC 61094-2 C.2: a length to diameter ratio "within the range of 0,5 to
    # 0,75", the length between the diaphragms. 5,4 + 2 x 1,95 mm over
    # 18,6 mm is 0,5 and comes out under it in binary; 5,9 + 2 x 2 mm over
    # 13,2 mm is 0,75 and comes out over it.
    check = _coupler_check(length_mm, depth_mm, diameter_mm)
    assert check.ratio_recommended is True


@pytest.mark.parametrize(
    ("frequency", "pressure"), [(36.01, 90025.0), (36.09, 90225.0)]
)
def test_a_frequency_of_four_tenths_hz_per_kpa_is_inside_the_stated_accuracy(
    frequency: float, pressure: float
) -> None:
    # IEC 61094-3 B.2: the attenuation is accurate to 10 % for a ratio of
    # frequency to static pressure of 0,4 Hz/kPa to 10^4 Hz/kPa. 36,01 Hz at
    # 90,025 kPa is 0,4 Hz/kPa and comes out under it in binary.
    attenuation = metrology.reciprocity_air_attenuation(
        [frequency],
        temperature_c=23.0,
        static_pressure_pa=pressure,
        relative_humidity_percent=50.0,
    )
    assert bool(attenuation.within_stated_accuracy[0])
