#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for a removable screen measured in situ (ISO 11821:1997).

The standard prints eight pages, no worked example and one uncertainty number.
The oracles are its printed thresholds, the boxed background formula of 5.7
with its own window, the microphone geometry of 5.5.2 and the one thing it
flatly forbids: an A-weighted attenuation obtained with an artificial source.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import noise_control
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
    with pytest.raises(ValueError, match="12 positions"):
        noise_control.directivity_index_db(np.full(11, 80.0))


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
