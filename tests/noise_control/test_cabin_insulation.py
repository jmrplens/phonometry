#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the sound pressure insulation of a cabin (ISO 11957:1996).

The document prints no worked example, so the oracles are the ones it does
offer: the algebraic identities of Equations (1), (2) and (3); the identity
that makes the Annex A estimate agree with the A-weighted totals of its own
inputs; the ISO 3741 background correction the clauses delegate to, checked
against its own closed form; and the printed thresholds of 6.2, 6.4, 6.7,
7.2.1 and clause 10.

Two clauses compute nothing of their own, and those have printed arithmetic
behind them: 6.4 sends the background correction to ISO 3741, whose 9.1.2
prints the value of its own Equation (14) at the two margins it clamps at, and
clause 8 sends the single number to ISO 717-1, whose Annex C works a full
example. Three accredited laboratories have published cabin measurements rated
to clause 8, and Example 7-8 of Barron carries the A-weighted sum of Annex A
through a spectrum of its own. The last section of this file is those, and each
test names the document its numbers were read from.
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest
from reference_data import ISO717_1_ANNEX_C_R as _ANNEX_C_R

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


# ---------------------------------------------------------------------------
# Numbers borrowed from the documents ISO 11957 delegates to, and from three
# published cabin measurements. The standard itself prints no worked example;
# what follows pins the arithmetic of the clauses that send their work
# elsewhere, and the clause 8 rating of three real cabins.
# ---------------------------------------------------------------------------

#: ISO 3741:2010 9.1.2, the clause 6.4 of ISO 11957 sends the background
#: correction to. It prints Equation (14) on PDF p. 28, printed folio 19, and
#: evaluates it at two arguments on PDF p. 29, printed folio 20: "K1i shall be
#: set to 1,26 dB (the value for dLpi = 6 dB)" at 200 Hz and below and at
#: 6 300 Hz and above, and "to 0,46 dB (the value for dLpi = 10 dB)" from
#: 250 Hz to 5 000 Hz.
K1_CLAMP_BANDS_HZ = np.array([100.0, 1000.0, 6300.0])
K1_CLAMP_MARGIN_DB = np.array([6.0, 8.0, 6.0])
PRINTED_K1_DB = np.array([1.26, 0.46, 1.26])

#: Half of the last digit those two values are printed to. The library clamps
#: the margin and re-evaluates Equation (14) rather than taking the rounded
#: constant, so it lands 0,004 dB under 1,26 and 0,002 dB under 0,46.
PRINTED_K1_TOLERANCE_DB = 0.005

#: ISO 717-1:2013 Annex C, Table C.1 (PDF p. 24, printed folio 16): the two
#: A-weighted spectra the adaptation terms are formed against, in decibels.
ISO717_SPECTRUM_ONE_DB = np.array(
    [-29.0, -26.0, -23.0, -21.0, -19.0, -17.0, -15.0, -13.0]
    + [-12.0, -11.0, -10.0, -9.0, -9.0, -9.0, -9.0, -9.0]
)
ISO717_SPECTRUM_TWO_DB = np.array(
    [-20.0, -20.0, -18.0, -16.0, -15.0, -14.0, -13.0, -12.0]
    + [-11.0, -9.0, -8.0, -9.0, -10.0, -11.0, -13.0, -15.0]
)

#: The "-10 lg sum" the same table prints under each spectrum, in decibels.
#: Both are truncated rather than rounded, which the ellipsis of the table
#: marks: "sum = 147,619 9 ... x 10-5", "-10 lg sum = 28,308...".
ISO717_PRINTED_SUM_TERM_DB = (28.308, 26.859)

#: ISO 3744:2010 Annex E, Table E.1 (PDF p. 69, printed folio 60): the
#: one-third-octave C_k over the rating bands. Annex A of ISO 11957 takes the
#: spectrum unweighted and an attenuation A_i that is positive where the
#: weighting takes level away, so A_i = -C_k and the printed A-weighted
#: spectra are de-weighted with these before they are handed over.
ISO3744_TABLE_E1_CK_DB = np.array(
    [-19.1, -16.1, -13.4, -10.9, -8.6, -6.6, -4.8, -3.2]
    + [-1.9, -0.8, 0.0, 0.6, 1.0, 1.2, 1.3, 1.2]
)

#: SGS-CSTC Standards Technical Services, Shunde Branch, test report
#: SDHL260400706101HI of 7 May 2026, PDF p. 3, folio "Page 3 of 4": D_p of a
#: meeting pod measured in a 200 m3 reverberation room, in decibels. The report
#: also prints 36.2 dB at 4 000 Hz and 36.4 dB at 5 000 Hz, outside the rating
#: range, and rates the spectrum at D_p,w = 32 dB.
SGS_POD_DP_DB = np.array(
    [11.0, 22.5, 24.0, 26.0, 29.3, 32.1, 28.3, 30.6]
    + [31.9, 34.9, 34.5, 33.2, 32.1, 33.7, 32.6, 33.2]
)

#: AGH University, Department of Mechanics and Vibroacoustics, report 5.5.130.
#: of August 2023, PDF p. 10, folio "Strona 10 z 10": D of an acoustic booth
#: measured in a 180,4 m3 reverberation room, in decibels, rated there at
#: D_p,w = 22 dB. The printed table runs 50 Hz to 10 kHz; the eight bands
#: outside the rating range play no part in the rating.
AGH_BOOTH_DP_DB = np.array(
    [10.0, 20.1, 14.7, 19.3, 20.6, 19.9, 23.2, 20.4]
    + [17.6, 19.1, 18.8, 20.2, 21.8, 24.4, 26.8, 28.3]
)

#: AGH University, Laboratorium Akustyki Technicznej, report 5.5.130.680 of
#: October 2017, PDF p. 11, folio "Strona 11 z 12": D_p of a telephone booth
#: measured in the same room, tabulated to whole decibels and rated there at
#: D_p,w = 30 dB.
EURONOVA_BOOTH_DP_DB = np.array(
    [12.0, 18.0, 14.0, 15.0, 20.0, 25.0, 28.0, 31.0]
    + [31.0, 33.0, 34.0, 34.0, 31.0, 30.0, 32.0, 33.0]
)

#: Barron, Industrial Noise Control and Acoustics, Marcel Dekker, New York,
#: 2003, ISBN 0-8247-0701-X. Example 7-8 of Section 7.6, Table 7-5 on printed
#: folio 308: an enclosure around a production machine, in octave bands.
BARRON_BANDS_HZ = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
BARRON_OPEN_DB = np.array([93.4, 98.5, 102.9, 104.6, 102.8, 95.5])
BARRON_ENCLOSED_DB = np.array([82.4, 84.9, 85.9, 85.8, 83.9, 71.2])
BARRON_INSERTION_LOSS_DB = np.array([11.0, 13.6, 17.0, 18.8, 18.9, 24.3])

#: The two A-weighted totals the same example prints, on folios 309 and 311:
#: "L_A^o = 108.4 dBA (without the enclosure)" and "L_A = 89.8 dBA (with the
#: enclosure)". Each is printed to a tenth, so their difference carries a tenth
#: of uncertainty of its own and no test on it may be tighter than that.
BARRON_OPEN_TOTAL_DB = 108.4
BARRON_ENCLOSED_TOTAL_DB = 89.8
BARRON_TOLERANCE_DB = 0.1


def _a_weighted_total(spectrum_db: np.ndarray) -> float:
    """The A-weighted total of an already A-weighted spectrum, in closed form.

    Annex A needs ``L_A`` and Table C.1 of ISO 717-1 does not print it, because
    its own spectra sit within a hundredth of 0 dB and the adaptation term
    needs the sum alone. It is closed in here from the same printed integers,
    with no help from the library, so the expected value stays independent of
    what is being tested.
    """
    return float(10.0 * np.log10(np.sum(10.0 ** (0.1 * spectrum_db))))


def test_the_background_correction_matches_the_printed_clamps_of_iso_3741() -> None:
    """ISO 3741:2010 9.1.2, folios 19 and 20, read through clause 6.4.

    Three bands take the 6 dB rule, then the 10 dB one, then the 6 dB rule
    again, so one call crosses both band-edge thresholds. The middle band is
    given a margin of 8 dB, under its own 10 dB threshold, which is the clamp
    itself rather than Equation (14).
    """
    levels = np.full(K1_CLAMP_BANDS_HZ.size, 80.0)
    correction = reverberation_background_correction(
        levels, levels - K1_CLAMP_MARGIN_DB, K1_CLAMP_BANDS_HZ
    )
    assert correction == pytest.approx(PRINTED_K1_DB, abs=PRINTED_K1_TOLERANCE_DB)


def test_the_internal_noise_level_carries_the_printed_correction() -> None:
    """The two edges of the window of 6.7, against 80 - 1,26 and 80 - 0,46 dB.

    The window of 6.7 and the band thresholds of ISO 3741 share the numbers 6
    and 10 and are not the same rule. What is pinned here is the value of K_1
    at those two arguments, not where the window itself comes from.
    """
    for margin, printed in ((6.0, 80.0 - 1.26), (10.0, 80.0 - 0.46)):
        answer = noise_control.internal_noise_level(
            [80.0, 80.0, 80.0], background_level=80.0 - margin
        )
        assert answer == pytest.approx(printed, abs=PRINTED_K1_TOLERANCE_DB)


def test_the_cabin_insulation_carries_the_printed_correction() -> None:
    """The same two corrections, reached through Equation (1) instead."""
    cabin = np.full(K1_CLAMP_BANDS_HZ.size, 60.0)
    res = noise_control.cabin_insulation(
        np.full(K1_CLAMP_BANDS_HZ.size, 90.0),
        cabin,
        frequencies=K1_CLAMP_BANDS_HZ,
        method="laboratory",
        cabin_background_levels=cabin - K1_CLAMP_MARGIN_DB,
    )
    printed = 30.0 + PRINTED_K1_DB
    assert res.insulation == pytest.approx(printed, abs=PRINTED_K1_TOLERANCE_DB)


def test_a_margin_of_fifteen_decibels_takes_no_correction() -> None:
    """Folio 19: "If dLpi >= 15 dB, K1i is assumed to be zero"."""
    answer = noise_control.internal_noise_level(
        [80.0, 80.0, 80.0], background_level=65.0
    )
    assert answer == pytest.approx(80.0)


def test_clause_eight_rates_the_printed_example_of_iso_717_1() -> None:
    """ISO 717-1:2013 Annex C, Table C.1, PDF p. 24, printed folio 16.

    Clause 8 of ISO 11957 defines no arithmetic of its own: it says to use
    ISO 717-1 with D_p in place of R. The substitution is nominal, so the
    printed example of ISO 717-1 exercises the whole of clause 8. This is that
    example, not a measured cabin spectrum.
    """
    rating = noise_control.weighted_cabin_insulation(_ANNEX_C_R)
    assert rating.rating == 30
    assert rating.c == -2
    assert rating.ctr == -3
    assert rating.unfavourable_sum == pytest.approx(31.8, abs=0.05)
    assert rating.apparent is False


def test_the_prime_changes_nothing_but_the_name() -> None:
    """The same printed example under the in-situ flag: four identical
    numbers, and only the symbol the clause attaches to them moves.
    """
    laboratory = noise_control.weighted_cabin_insulation(_ANNEX_C_R)
    in_situ = noise_control.weighted_cabin_insulation(_ANNEX_C_R, apparent=True)
    assert (in_situ.rating, in_situ.c, in_situ.ctr) == (
        laboratory.rating,
        laboratory.c,
        laboratory.ctr,
    )
    assert in_situ.unfavourable_sum == pytest.approx(laboratory.unfavourable_sum)
    assert in_situ.apparent is True


def test_the_annex_a_estimate_reproduces_the_printed_sums() -> None:
    """ISO 717-1:2013 Table C.1 read as the summation term of Annex A.

    The table prints the 16 summands, their total and its ``-10 lg`` for two
    spectra, which is the second term of the Annex A estimate with D_p written
    where ISO 717-1 writes R. The total D_pA,e is not printed anywhere, so L_A
    is closed in from the same printed integers and taken back off.
    """
    for spectrum, printed in zip(
        (ISO717_SPECTRUM_ONE_DB, ISO717_SPECTRUM_TWO_DB),
        ISO717_PRINTED_SUM_TERM_DB,
        strict=True,
    ):
        estimate = noise_control.estimated_cabin_noise_insulation(
            spectrum - ISO3744_TABLE_E1_CK_DB,
            _ANNEX_C_R,
            frequencies=RATING_BANDS,
        )
        summation = estimate - _a_weighted_total(spectrum)
        # The printed value is a truncation, so a correct answer sits at or
        # just above it and never below.
        assert printed <= summation < printed + 0.001


def test_the_spectra_of_table_c1_are_normalised_to_about_zero() -> None:
    """Why the table can print the sum alone and never name L_A."""
    for spectrum in (ISO717_SPECTRUM_ONE_DB, ISO717_SPECTRUM_TWO_DB):
        assert abs(_a_weighted_total(spectrum)) < 0.02


def test_the_sgs_meeting_pod_rates_as_its_laboratory_published_it() -> None:
    """SGS-CSTC report SDHL260400706101HI, PDF p. 3, folio "Page 3 of 4".

    The report prints the rating and no adaptation terms, so C and Ctr are not
    anchored by it and are deliberately not asserted here.
    """
    rating = noise_control.weighted_cabin_insulation(SGS_POD_DP_DB)
    assert rating.rating == 32
    assert rating.unfavourable_sum <= 32.0


def test_the_agh_acoustic_booth_rates_as_its_laboratory_published_it() -> None:
    """AGH report 5.5.130. of August 2023, PDF p. 10, folio "Strona 10 z 10"."""
    rating = noise_control.weighted_cabin_insulation(AGH_BOOTH_DP_DB)
    assert rating.rating == 22
    assert rating.unfavourable_sum <= 32.0


def test_the_euronova_telephone_booth_rates_as_its_laboratory_published_it() -> None:
    """AGH report 5.5.130.680 of October 2017, PDF p. 11, folio "Strona 11 z 12".

    The plotted curve on the same card carries finer values than the table, so
    the laboratory rated unrounded data. Rating the published integers reaches
    the same 30 dB, which is the claim: the published spectrum rates as its
    laboratory published it, not that the shift is pinned to a fine tolerance.
    """
    rating = noise_control.weighted_cabin_insulation(EURONOVA_BOOTH_DP_DB)
    assert rating.rating == 30
    assert rating.unfavourable_sum <= 32.0


def test_a_spectrum_outside_the_rating_bands_cannot_leak_into_the_rating() -> None:
    """The SGS report prints 4 000 Hz and 5 000 Hz beside the 16 rating bands."""
    with pytest.raises(ValueError, match="16 bands"):
        noise_control.weighted_cabin_insulation([*SGS_POD_DP_DB, 36.2, 36.4])


def test_the_annex_a_estimate_reproduces_the_barron_worked_example() -> None:
    """Barron (2003) Example 7-8, Table 7-5 and folios 309 and 311.

    A machine enclosure predicted by the book's own model rather than a cabin
    measured to ISO 11957, so what it anchors is the arithmetic of Annex A: the
    A-weighted total of a spectrum with a per-band insulation taken off it,
    against the one without. The two totals are printed to a tenth each, so the
    difference is good to a tenth and no test on it may ask for more.
    """
    estimate = noise_control.estimated_cabin_noise_insulation(
        BARRON_OPEN_DB, BARRON_INSERTION_LOSS_DB, frequencies=BARRON_BANDS_HZ
    )
    printed = BARRON_OPEN_TOTAL_DB - BARRON_ENCLOSED_TOTAL_DB
    assert estimate == pytest.approx(printed, abs=BARRON_TOLERANCE_DB)


def test_the_printed_insertion_loss_is_the_difference_of_the_two_printed_rows() -> None:
    """Table 7-5 checked against itself before it is used as an oracle."""
    assert BARRON_INSERTION_LOSS_DB == pytest.approx(
        BARRON_OPEN_DB - BARRON_ENCLOSED_DB, abs=0.05
    )
    with_rows = noise_control.estimated_cabin_noise_insulation(
        BARRON_OPEN_DB,
        BARRON_OPEN_DB - BARRON_ENCLOSED_DB,
        frequencies=BARRON_BANDS_HZ,
    )
    with_printed_loss = noise_control.estimated_cabin_noise_insulation(
        BARRON_OPEN_DB, BARRON_INSERTION_LOSS_DB, frequencies=BARRON_BANDS_HZ
    )
    assert with_rows == pytest.approx(with_printed_loss)
