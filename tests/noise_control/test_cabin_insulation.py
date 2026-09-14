#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the sound pressure insulation of a cabin (ISO 11957:1996).

The document prints no worked example, so the oracles are the ones it does
offer: the algebraic identities of Equations (1), (2) and (3); the identity
that makes the Annex A estimate agree with the A-weighted totals of its own
inputs; the ISO 3741 background correction the clauses delegate to, checked
against its own closed form; and the printed thresholds of 6.2, 6.4, 6.7,
7.2.1 and clause 10.
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from phonometry import noise_control
from phonometry.emission import reverberation_background_correction
from phonometry.noise_control.cabin_insulation import (
    BAND_FLATNESS_LIMIT_DB,
    DEFAULT_BAND_FLATNESS_LIMIT_DB,
    IN_SITU_EXCESS_STANDARD_DEVIATION_DB,
    INTERNAL_NOISE_CENTRE_HEIGHT_M,
    INTERNAL_NOISE_CENTRE_TOLERANCE_M,
    INTERNAL_NOISE_CORRECTION_WINDOW_DB,
    LOW_BAND_CLEARANCE_M,
    MAX_LEAK_RATIO,
    MAX_SOURCE_POSITIONS_IN_SITU,
    MIN_FIXED_MICROPHONE_POSITIONS,
    MIN_ROOM_TO_CABIN_VOLUME_RATIO,
    MIN_SOURCE_POSITIONS_IN_SITU,
    OPERATOR_PATH_INCLINATION_DEG,
    OPERATOR_SPHERE_RADIUS_M,
    CabinInsulationWarning,
)

THIRD_OCTAVES = np.array(
    [
        100.0,
        125.0,
        160.0,
        200.0,
        250.0,
        315.0,
        400.0,
        500.0,
        630.0,
        800.0,
        1000.0,
        1250.0,
        1600.0,
        2000.0,
        2500.0,
        3150.0,
        4000.0,
        5000.0,
    ]
)
RATING_BANDS = THIRD_OCTAVES[:16]
OCTAVES = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])


def _room(offset: float = 0.0) -> np.ndarray:
    return np.linspace(88.0, 80.0, THIRD_OCTAVES.size) + offset


def _cabin() -> np.ndarray:
    return _room() - np.linspace(10.0, 38.0, THIRD_OCTAVES.size)


def test_equation_one_is_the_difference() -> None:
    room, cabin = _room(), _cabin()
    res = noise_control.cabin_insulation(room, cabin, frequencies=THIRD_OCTAVES)
    assert np.allclose(res.insulation, room - cabin)
    assert res.method == "laboratory"
    assert res.apparent is False
    assert res.symbol == "D_p"


def test_in_situ_carries_the_prime() -> None:
    for method in ("in-situ-loudspeaker", "in-situ-actual-noise"):
        res = noise_control.cabin_insulation(
            _room(), _cabin(), frequencies=THIRD_OCTAVES, method=method
        )
        assert res.apparent is True
        assert res.symbol == "D'_p"


def test_a_common_offset_leaves_the_insulation_alone() -> None:
    plain = noise_control.cabin_insulation(_room(), _cabin(), frequencies=THIRD_OCTAVES)
    raised = noise_control.cabin_insulation(
        _room() + 6.0, _cabin() + 6.0, frequencies=THIRD_OCTAVES
    )
    assert np.allclose(plain.insulation, raised.insulation)


def test_swapping_the_two_levels_changes_the_sign() -> None:
    forward = noise_control.cabin_insulation(
        _room(), _cabin(), frequencies=THIRD_OCTAVES
    )
    backward = noise_control.cabin_insulation(
        _cabin(), _room(), frequencies=THIRD_OCTAVES
    )
    assert np.allclose(forward.insulation, -backward.insulation)


def test_equation_three_belongs_to_the_actual_noise_method() -> None:
    res = noise_control.cabin_insulation(
        _room(),
        _cabin(),
        frequencies=THIRD_OCTAVES,
        method="in-situ-actual-noise",
        a_weighted_room_level=86.4,
        a_weighted_cabin_level=61.2,
    )
    assert res.a_weighted_insulation == pytest.approx(86.4 - 61.2)


def test_the_a_weighted_insulation_is_refused_under_the_other_methods() -> None:
    room, cabin = _room(), _cabin()
    for method in ("laboratory", "in-situ-loudspeaker"):
        with pytest.raises(ValueError, match="actual environmental noise"):
            noise_control.cabin_insulation(
                room,
                cabin,
                frequencies=THIRD_OCTAVES,
                method=method,
                a_weighted_room_level=86.4,
                a_weighted_cabin_level=61.2,
            )


def test_half_an_a_weighted_pair_is_refused() -> None:
    room, cabin = _room(), _cabin()
    with pytest.raises(ValueError, match="both"):
        noise_control.cabin_insulation(
            room,
            cabin,
            frequencies=THIRD_OCTAVES,
            method="in-situ-actual-noise",
            a_weighted_room_level=86.4,
        )


def test_the_background_correction_is_the_one_of_iso_3741() -> None:
    room, cabin = _room(), _cabin()
    background = cabin - 8.0
    res = noise_control.cabin_insulation(
        room,
        cabin,
        frequencies=THIRD_OCTAVES,
        cabin_background_levels=background,
    )
    k1 = reverberation_background_correction(cabin, background, THIRD_OCTAVES)
    assert np.allclose(res.cabin_levels, cabin - k1)
    assert np.allclose(res.insulation, room - (cabin - k1))


def test_a_thin_margin_over_the_background_is_reported() -> None:
    room, cabin = _room(), _cabin()
    background = cabin - 2.0
    with pytest.warns(CabinInsulationWarning, match="over the background"):
        noise_control.cabin_insulation(
            room,
            cabin,
            frequencies=THIRD_OCTAVES,
            cabin_background_levels=background,
        )


def test_the_room_background_is_corrected_too() -> None:
    room = _room()
    res = noise_control.cabin_insulation(
        room,
        _cabin(),
        frequencies=THIRD_OCTAVES,
        method="in-situ-actual-noise",
        room_background_levels=room - 12.0,
    )
    assert np.all(res.room_levels < room)


def test_a_background_without_frequencies_is_refused() -> None:
    room, cabin = _room(), _cabin()
    background = cabin - 10.0
    with pytest.raises(ValueError, match="frequencies"):
        noise_control.cabin_insulation(room, cabin, cabin_background_levels=background)


def test_mismatched_levels_are_refused() -> None:
    with pytest.raises(ValueError, match="cabin_levels"):
        noise_control.cabin_insulation([88.0, 88.0], [70.0])


def test_a_short_band_range_is_reported() -> None:
    with pytest.warns(CabinInsulationWarning, match="ISO 11957 requires"):
        noise_control.cabin_insulation(
            [88.0, 88.0], [70.0, 68.0], frequencies=[500.0, 1000.0]
        )


def test_rounding_is_the_report_rule() -> None:
    res = noise_control.cabin_insulation(_room(), _cabin(), frequencies=THIRD_OCTAVES)
    assert res.rounded().tolist() == np.rint(res.insulation).astype(int).tolist()


def test_the_internal_noise_level_rides_along() -> None:
    res = noise_control.cabin_insulation(
        _room(), _cabin(), frequencies=THIRD_OCTAVES, internal_noise_level=52.4
    )
    assert res.internal_noise_level == pytest.approx(52.4)


def test_the_rating_reads_the_rating_bands_and_keeps_the_prime() -> None:
    rating = noise_control.weighted_cabin_insulation(
        np.linspace(12.0, 40.0, RATING_BANDS.size), apparent=True
    )
    assert rating.band_centres_hz.tolist() == RATING_BANDS.tolist()
    assert rating.apparent is True


def test_a_spectrum_that_is_not_the_rating_bands_is_refused() -> None:
    with pytest.raises(ValueError, match="16 bands"):
        noise_control.weighted_cabin_insulation(np.zeros(18))


def test_a_flat_insulation_estimates_itself() -> None:
    spectrum = _room()
    for value in (0.0, 11.0, 29.5):
        estimate = noise_control.estimated_cabin_noise_insulation(
            spectrum, np.full(spectrum.size, value), frequencies=THIRD_OCTAVES
        )
        assert estimate == pytest.approx(value)


def test_the_estimate_is_the_difference_of_two_a_weighted_totals() -> None:
    spectrum = _room()
    insulation = np.linspace(8.0, 40.0, spectrum.size)
    estimate = noise_control.estimated_cabin_noise_insulation(
        spectrum, insulation, frequencies=THIRD_OCTAVES
    )
    reference = noise_control.estimated_a_weighted_insulation(
        spectrum, insulation, frequencies=THIRD_OCTAVES
    )
    assert estimate == pytest.approx(reference)


def test_the_estimate_needs_matching_inputs() -> None:
    with pytest.raises(ValueError, match="band for band"):
        noise_control.estimated_cabin_noise_insulation(
            [88.0, 88.0], [10.0], frequencies=[500.0, 1000.0]
        )


def test_the_internal_noise_level_is_an_energy_mean() -> None:
    levels = [58.0, 59.0, 60.0]
    expected = 10.0 * np.log10(np.mean(10.0 ** (np.asarray(levels) / 10.0)))
    assert noise_control.internal_noise_level(levels) == pytest.approx(expected)


def test_the_internal_noise_correction_stays_inside_its_window() -> None:
    levels = [60.0, 60.0, 60.0]
    lower, upper = INTERNAL_NOISE_CORRECTION_WINDOW_DB
    inside = noise_control.internal_noise_level(
        levels, background_level=60.0 - (lower + upper) / 2.0
    )
    outside = noise_control.internal_noise_level(
        levels, background_level=60.0 - (upper + 5.0)
    )
    assert inside < 60.0
    assert outside == pytest.approx(60.0)


def test_the_correction_is_the_printed_formula() -> None:
    margin = 8.0
    corrected = noise_control.internal_noise_level(
        [60.0, 60.0, 60.0], background_level=60.0 - margin
    )
    expected = 60.0 + 10.0 * np.log10(1.0 - 10.0 ** (-0.1 * margin))
    assert corrected == pytest.approx(expected)


def test_a_margin_under_six_decibels_is_an_upper_bound() -> None:
    with pytest.warns(CabinInsulationWarning, match="upper bound"):
        answer = noise_control.internal_noise_level(
            [60.0, 60.0, 60.0], background_level=56.0
        )
    assert answer == pytest.approx(60.0)


def test_an_empty_set_of_positions_is_refused() -> None:
    with pytest.raises(ValueError, match="levels"):
        noise_control.internal_noise_level([])


def test_the_source_count_criterion_of_7_2_1() -> None:
    # Three positions that agree within 2 dB in every octave: three is enough.
    close = np.vstack(
        [
            np.linspace(20.0, 40.0, OCTAVES.size),
            np.linspace(20.0, 40.0, OCTAVES.size) + 1.0,
            np.linspace(20.0, 40.0, OCTAVES.size) - 1.0,
        ]
    )
    verdict = noise_control.check_source_positions(close)
    assert verdict.positions_used == MIN_SOURCE_POSITIONS_IN_SITU
    assert verdict.max_octave_spread_db == pytest.approx(2.0)
    assert verdict.required_positions == MIN_SOURCE_POSITIONS_IN_SITU
    assert verdict.satisfied is True
    assert verdict.exceeds_maximum is False


def test_a_wide_spread_asks_for_more_positions() -> None:
    wide = np.vstack(
        [
            np.full(OCTAVES.size, 30.0),
            np.full(OCTAVES.size, 34.5),
            np.full(OCTAVES.size, 25.0),
        ]
    )
    verdict = noise_control.check_source_positions(wide)
    assert verdict.max_octave_spread_db == pytest.approx(9.5)
    assert verdict.required_positions == MAX_SOURCE_POSITIONS_IN_SITU
    assert verdict.satisfied is False
    assert verdict.exceeds_maximum is True


def test_a_spread_the_six_positions_can_carry_is_not_flagged() -> None:
    rows = [np.full(OCTAVES.size, 30.0 + step) for step in range(4)]
    verdict = noise_control.check_source_positions(np.vstack(rows))
    assert verdict.max_octave_spread_db == pytest.approx(3.0)
    assert verdict.required_positions == MIN_SOURCE_POSITIONS_IN_SITU
    assert verdict.exceeds_maximum is False


def test_fewer_than_three_positions_is_refused() -> None:
    with pytest.raises(ValueError, match="7.2.1"):
        noise_control.check_source_positions(
            np.vstack([np.full(OCTAVES.size, 30.0), np.full(OCTAVES.size, 31.0)])
        )


def test_the_flatness_limits_are_the_printed_ones() -> None:
    assert BAND_FLATNESS_LIMIT_DB == {125.0: 6.0, 250.0: 5.0}
    assert DEFAULT_BAND_FLATNESS_LIMIT_DB == 4.0
    levels = np.array([80.0, 80.0, 80.0, 70.0, 70.0, 70.0, 60.0, 60.0, 60.0])
    frequencies = np.array(
        [100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0]
    )
    check = noise_control.check_band_flatness(levels, frequencies=frequencies)
    assert check.octave_centres_hz.tolist() == [125.0, 250.0, 500.0]
    assert check.limit_db.tolist() == [6.0, 5.0, 4.0]
    assert check.all_satisfied is True


def test_a_peaky_octave_fails_its_limit() -> None:
    levels = np.array([80.0, 86.5, 80.0])
    frequencies = np.array([200.0, 250.0, 315.0])
    check = noise_control.check_band_flatness(levels, frequencies=frequencies)
    assert check.spread_db[0] == pytest.approx(6.5)
    assert check.satisfied.tolist() == [False]
    assert check.all_satisfied is False


def test_an_octave_below_125_hz_has_no_printed_limit() -> None:
    levels = np.array([70.0, 84.0, 70.0])
    frequencies = np.array([50.0, 63.0, 80.0])
    check = noise_control.check_band_flatness(levels, frequencies=frequencies)
    assert check.octave_centres_hz.tolist() == [63.0]
    assert np.isnan(check.limit_db[0])
    assert check.satisfied.tolist() == [True]


def test_an_incomplete_octave_is_refused() -> None:
    with pytest.raises(ValueError, match="3 one-third-octave bands"):
        noise_control.check_band_flatness([80.0, 80.0], frequencies=[200.0, 250.0])


def test_a_frequency_that_is_not_a_band_centre_is_refused() -> None:
    # 355 Hz sits on the boundary between the 250 Hz and 500 Hz octaves and
    # belongs to neither.
    with pytest.raises(ValueError, match="nominal one-third-octave"):
        noise_control.check_band_flatness(
            [80.0, 80.0, 80.0], frequencies=[200.0, 250.0, 355.0]
        )


def test_the_clearance_is_half_a_wavelength_above_the_low_range() -> None:
    assert noise_control.minimum_cabin_clearance_m(100.0) == pytest.approx(1.715)
    assert noise_control.minimum_cabin_clearance_m(
        200.0, speed_of_sound=340.0
    ) == pytest.approx(0.85)


def test_the_low_range_takes_the_flat_two_metres() -> None:
    for frequency in (50.0, 63.0, 80.0):
        assert noise_control.minimum_cabin_clearance_m(frequency) == pytest.approx(
            LOW_BAND_CLEARANCE_M
        )


def test_the_low_range_relaxes_rather_than_tightens() -> None:
    # At 50 Hz half a wavelength is 3.43 m, and the clause asks for 2 m: the
    # special case is the smaller number. Recorded as printed.
    half_wavelength = 0.5 * 343.0 / 50.0
    assert noise_control.minimum_cabin_clearance_m(50.0) < half_wavelength


def test_a_frequency_outside_the_covered_range_is_reported() -> None:
    with pytest.warns(CabinInsulationWarning, match="6.2 covers"):
        noise_control.minimum_cabin_clearance_m(12500.0)


def test_a_non_positive_frequency_is_refused() -> None:
    with pytest.raises(ValueError, match="lowest_band_frequency_hz"):
        noise_control.minimum_cabin_clearance_m(0.0)


def test_the_laboratory_uncertainty_needs_the_volume_ratio() -> None:
    verdict = noise_control.uncertainty_conditions(
        room_volume_m3=300.0, cabin_volume_m3=12.0
    )
    assert verdict.volume_ratio == pytest.approx(25.0)
    assert verdict.ratio_satisfied is True
    assert verdict.stateable is True
    assert verdict.stated_band_range_hz == (250.0, 10000.0)
    assert verdict.increased_uncertainty_band_range_hz == (50.0, 200.0)
    assert verdict.excess_standard_deviation_db == pytest.approx(0.0)


def test_a_cabin_too_large_for_the_room_is_reported() -> None:
    with pytest.warns(CabinInsulationWarning, match="20 times"):
        verdict = noise_control.uncertainty_conditions(
            room_volume_m3=200.0, cabin_volume_m3=25.0
        )
    assert verdict.ratio_satisfied is False


def test_the_loudspeaker_method_in_situ_adds_two_decibels() -> None:
    verdict = noise_control.uncertainty_conditions(
        room_volume_m3=300.0,
        cabin_volume_m3=12.0,
        method="in-situ-loudspeaker",
    )
    assert verdict.excess_standard_deviation_db == pytest.approx(
        IN_SITU_EXCESS_STANDARD_DEVIATION_DB
    )


def test_the_actual_noise_method_states_nothing() -> None:
    verdict = noise_control.uncertainty_conditions(
        room_volume_m3=300.0,
        cabin_volume_m3=12.0,
        method="in-situ-actual-noise",
    )
    assert verdict.stateable is False
    assert verdict.stated_band_range_hz is None
    assert verdict.excess_standard_deviation_db is None


def test_an_unknown_method_is_refused() -> None:
    room, cabin = _room(), _cabin()
    with pytest.raises(ValueError, match="method"):
        noise_control.cabin_insulation(
            room,
            cabin,
            frequencies=THIRD_OCTAVES,
            method="in-situ",  # type: ignore[arg-type]
        )


def test_the_scope_and_geometry_constants_are_the_printed_ones() -> None:
    assert MAX_LEAK_RATIO == 0.02
    assert MIN_ROOM_TO_CABIN_VOLUME_RATIO == 20.0
    assert MIN_FIXED_MICROPHONE_POSITIONS == 6
    assert OPERATOR_SPHERE_RADIUS_M == 0.3
    assert OPERATOR_PATH_INCLINATION_DEG == 45.0
    assert INTERNAL_NOISE_CENTRE_HEIGHT_M == 1.55
    assert INTERNAL_NOISE_CENTRE_TOLERANCE_M == 0.075


def test_the_leak_ratio_is_shared_with_the_enclosure_module() -> None:
    from phonometry.noise_control import enclosure_insulation

    assert (
        noise_control.cabin_insulation.__module__
        != enclosure_insulation.leak_ratio.__module__
    )
    assert noise_control.leak_ratio(0.02, 6.0) == pytest.approx(0.02 / 6.0)


def test_the_plot_draws_three_series() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res = noise_control.cabin_insulation(
        _room(), _cabin(), frequencies=THIRD_OCTAVES, method="in-situ-loudspeaker"
    )
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax)
    twin = [other for other in drawn.figure.axes if other is not drawn]
    assert len(drawn.lines) == 2
    assert len(twin) == 1
    assert len(twin[0].lines) == 1
    plt.close(fig)


def test_the_plot_without_frequencies_uses_band_indices() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res = noise_control.cabin_insulation(_room(), _cabin())
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax)
    assert drawn.get_xlabel() == "Band"
    plt.close(fig)


def test_the_spanish_plot_translates_its_labels() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res = noise_control.cabin_insulation(_room(), _cabin(), frequencies=THIRD_OCTAVES)
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax, language="es")
    assert "cabina" in drawn.get_title()
    assert "Nivel de presión" in drawn.get_ylabel()
    plt.close(fig)


def test_a_non_finite_a_weighted_level_is_refused() -> None:
    room, cabin = _room(), _cabin()
    with pytest.raises(ValueError, match="a_weighted_cabin_level"):
        noise_control.cabin_insulation(
            room,
            cabin,
            frequencies=THIRD_OCTAVES,
            method="in-situ-actual-noise",
            a_weighted_room_level=86.4,
            a_weighted_cabin_level=float("inf"),
        )


def test_a_frequency_that_names_no_band_is_refused() -> None:
    with pytest.raises(ValueError, match="nominal one-third-octave centre"):
        noise_control.check_band_flatness(
            [80.0, 82.0, 81.0], frequencies=[220.0, 250.0, 280.0]
        )


def test_a_band_given_twice_is_refused() -> None:
    with pytest.raises(ValueError, match="given twice"):
        noise_control.check_band_flatness(
            [80.0, 82.0, 81.0], frequencies=[250.0, 250.0, 315.0]
        )


def test_the_actual_noise_method_states_nothing_and_warns_about_nothing() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        verdict = noise_control.uncertainty_conditions(
            room_volume_m3=100.0,
            cabin_volume_m3=10.0,
            method="in-situ-actual-noise",
        )
    assert verdict.stateable is False
    assert verdict.ratio_satisfied is False


def test_a_band_centre_at_zero_is_refused() -> None:
    with pytest.raises(ValueError, match="frequencies"):
        reverberation_background_correction(
            [80.0, 82.0], [70.0, 71.0], frequencies=[0.0, 250.0]
        )


def test_the_exact_base_ten_centres_name_the_same_bands() -> None:
    """A caller who computes 10^(n/10) rather than reading the printed name."""
    check = noise_control.check_band_flatness(
        [80.0, 82.0, 81.0], frequencies=[199.526, 251.189, 316.228]
    )
    assert check.octave_centres_hz.tolist() == [250.0]


def test_the_tolerance_never_reaches_the_neighbouring_band() -> None:
    """Two adjacent thirds are 26 % apart; the slack is 2 %."""
    with pytest.raises(ValueError, match="nominal one-third-octave"):
        noise_control.check_band_flatness(
            [80.0, 82.0, 81.0], frequencies=[225.0, 250.0, 315.0]
        )
