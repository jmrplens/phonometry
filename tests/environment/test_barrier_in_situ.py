#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for an outdoor barrier measured in situ (ISO 10847:1997).

The document prints no worked example, no uncertainty table and no figures.
Its strongest oracle is its own algebra: the indirect method reduces exactly to
the direct one when the receiver is of the same kind in both campaigns, and
moves by exactly 6 dB when it is not. Beside that are the source-normalisation
invariance, the two printed tables, the short-distance predicate and the two
pieces of geometry.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import environment
from phonometry.environment.propagation.barrier_in_situ import (
    CLOSE_SOURCE_DISTANCE_M,
    CLOUD_COVER_CLASSES,
    EQUIVALENT_SECTOR_DEG,
    EQUIVALENT_SURROUNDINGS_RADIUS_M,
    ISO10847_BACKGROUND_CORRECTIONS_DB,
    ISO10847_MINIMUM_BACKGROUND_MARGIN_DB,
    ISO10847_OCTAVE_BAND_RANGE_HZ,
    ISO10847_THIRD_OCTAVE_BAND_RANGE_HZ,
    LINE_SOURCE_DIVERGENCE_DB,
    LONG_DISTANCE_M,
    MAXIMUM_WIND_SPEED_M_S,
    MINIMUM_RECEIVER_HEIGHT_M,
    MINIMUM_REPETITIONS,
    POINT_SOURCE_DIVERGENCE_DB,
    RECEIVER_CORRECTIONS_DB,
    REFERENCE_ELEVATION_INCREMENT_DEG,
    REFERENCE_MICROPHONE_CLEARANCE_M,
    SHORT_DISTANCE_RATIO,
    TEMPERATURE_TOLERANCE_C,
    WIND_VECTOR_TOLERANCE_M_S,
    BarrierInSituWarning,
)

BANDS = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
REFERENCE_BEFORE = np.array([70.0, 72.0, 74.0, 73.0, 70.0, 66.0, 60.0])
RECEIVER_BEFORE = np.array([60.0, 62.0, 63.0, 62.0, 59.0, 55.0, 49.0])
ATTENUATION = np.array([3.0, 5.0, 8.0, 11.0, 14.0, 16.0, 17.0])


def _campaign(gain_db: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """The "after" pair for a barrier of the stated attenuation, plus a gain."""
    return REFERENCE_BEFORE + gain_db, RECEIVER_BEFORE - ATTENUATION + gain_db


def test_the_direct_method_returns_the_barrier_attenuation() -> None:
    reference_after, receiver_after = _campaign()
    res = environment.measured_insertion_loss_direct(
        REFERENCE_BEFORE,
        reference_after,
        RECEIVER_BEFORE,
        receiver_after,
        frequencies=BANDS,
    )
    assert np.allclose(res.insertion_loss_db, ATTENUATION)
    assert res.symbol == "D_IL"
    assert res.method == "direct"


def test_a_barrier_that_does_nothing_gives_zero() -> None:
    res = environment.measured_insertion_loss_direct(
        REFERENCE_BEFORE, REFERENCE_BEFORE, RECEIVER_BEFORE, RECEIVER_BEFORE
    )
    assert np.allclose(res.insertion_loss_db, 0.0)


def test_a_source_that_got_louder_is_normalised_away() -> None:
    # The whole point of the reference position: a source that changed output
    # between the two campaigns is heard at both microphones, and subtracting
    # the reference term leaves the barrier alone.
    reference_after, receiver_after = _campaign()
    plain = environment.measured_insertion_loss_direct(
        REFERENCE_BEFORE, reference_after, RECEIVER_BEFORE, receiver_after
    )
    louder_reference, louder_receiver = _campaign(4.0)
    louder = environment.measured_insertion_loss_direct(
        REFERENCE_BEFORE, louder_reference, RECEIVER_BEFORE, louder_receiver
    )
    assert np.allclose(plain.insertion_loss_db, louder.insertion_loss_db)


def test_the_rounding_is_the_reporting_rule() -> None:
    res = environment.measured_insertion_loss_direct(
        [70.0, 70.0], [70.0, 70.0], [60.0, 60.0], [55.4, 55.6]
    )
    assert res.rounded().tolist() == [5, 4]


def test_the_indirect_method_matches_the_direct_one_for_one_receiver_kind() -> None:
    reference_after, receiver_after = _campaign()
    direct = environment.measured_insertion_loss_direct(
        REFERENCE_BEFORE, reference_after, RECEIVER_BEFORE, receiver_after
    )
    for kind in RECEIVER_CORRECTIONS_DB:
        indirect = environment.measured_insertion_loss_indirect(
            REFERENCE_BEFORE,
            reference_after,
            RECEIVER_BEFORE,
            receiver_after,
            receiver_type_before=kind,  # type: ignore[arg-type]
            receiver_type_after=kind,  # type: ignore[arg-type]
        )
        assert np.allclose(indirect.insertion_loss_db, direct.insertion_loss_db)
        assert indirect.symbol == "D'_IL"


def test_mixing_the_two_receiver_kinds_moves_the_answer_by_six_decibels() -> None:
    reference_after, receiver_after = _campaign()
    direct = environment.measured_insertion_loss_direct(
        REFERENCE_BEFORE, reference_after, RECEIVER_BEFORE, receiver_after
    )
    with pytest.warns(BarrierInSituWarning, match="essentially the same"):
        mixed = environment.measured_insertion_loss_indirect(
            REFERENCE_BEFORE,
            reference_after,
            RECEIVER_BEFORE,
            receiver_after,
            receiver_type_after="reflecting_surface",
        )
    assert np.allclose(mixed.insertion_loss_db - direct.insertion_loss_db, 6.0)
    assert RECEIVER_CORRECTIONS_DB["reflecting_surface"] == 6.0
    assert RECEIVER_CORRECTIONS_DB["hemi_free_field"] == 0.0


def test_an_unknown_receiver_type_is_refused() -> None:
    reference_after, receiver_after = _campaign()
    with pytest.raises(ValueError, match="receiver_type_before"):
        environment.measured_insertion_loss_indirect(
            REFERENCE_BEFORE,
            reference_after,
            RECEIVER_BEFORE,
            receiver_after,
            receiver_type_before="facade",  # type: ignore[arg-type]
        )


def test_levels_that_do_not_match_are_refused() -> None:
    with pytest.raises(ValueError, match="band for band"):
        environment.measured_insertion_loss_direct(
            [70.0, 70.0], [70.0], [60.0, 60.0], [55.0, 55.0]
        )


def test_table_three_reproduces_its_two_rows() -> None:
    assert ISO10847_BACKGROUND_CORRECTIONS_DB == {
        4: -2.0,
        5: -2.0,
        6: -1.0,
        7: -1.0,
        8: -1.0,
        9: -1.0,
    }
    margins = np.arange(4, 14, dtype=float)
    corrections = environment.barrier_background_correction_db(margins)
    assert corrections[:6].tolist() == [-2.0, -2.0, -1.0, -1.0, -1.0, -1.0]
    assert np.all(corrections[6:] == 0.0)


def test_the_correction_is_added_rather_than_subtracted() -> None:
    assert np.all(environment.barrier_background_correction_db([4.0, 9.0]) < 0.0)


def test_a_margin_under_four_decibels_is_refused() -> None:
    with pytest.raises(ValueError, match="invalid"):
        environment.barrier_background_correction_db([3.9])
    assert ISO10847_MINIMUM_BACKGROUND_MARGIN_DB == 4.0


def test_this_table_is_not_the_one_the_silencer_standard_prints() -> None:
    from phonometry.noise_control import silencer_background_correction_db

    # At a 9 dB margin ISO 11820 takes off 0,5 dB and ISO 10847 takes off 1.
    assert silencer_background_correction_db([9.0])[0] == 0.5
    assert environment.barrier_background_correction_db([9.0])[0] == -1.0


def test_the_short_distance_predicate_is_the_printed_pair() -> None:
    before, after = environment.is_short_distance(
        source_height_m=1.0,
        receiver_height_m=1.5,
        barrier_height_m=4.0,
        source_to_barrier_m=10.0,
        barrier_to_receiver_m=15.0,
    )
    assert before is ((1.0 + 1.5) / 25.0 > SHORT_DISTANCE_RATIO)
    assert after is True


def test_the_inequality_is_strict_at_the_ratio() -> None:
    before, _ = environment.is_short_distance(
        source_height_m=1.0,
        receiver_height_m=1.0,
        barrier_height_m=4.0,
        source_to_barrier_m=10.0,
        barrier_to_receiver_m=10.0,
    )
    assert before is False


def test_the_after_pair_needs_both_halves() -> None:
    _, after = environment.is_short_distance(
        source_height_m=1.0,
        receiver_height_m=1.0,
        barrier_height_m=1.0,
        source_to_barrier_m=10.0,
        barrier_to_receiver_m=100.0,
    )
    assert after is False


def test_the_wind_classes_of_table_one() -> None:
    assert environment.wind_class(3.0) == "downwind"
    assert environment.wind_class(0.0) == "calm"
    assert environment.wind_class(-3.0) is None
    assert environment.wind_class(-3.0, short_distance=True) == "upwind"


def test_the_upwind_class_is_read_as_negative() -> None:
    # The print reads "+ 1 to - 5"; an interval starting at +1 m/s would sit
    # inside the downwind class, so it is read as -1 to -5 (see the errata).
    assert environment.wind_class(1.5, short_distance=True) == "downwind"
    assert environment.wind_class(-1.5, short_distance=True) == "upwind"


def test_no_measurement_above_five_metres_per_second() -> None:
    with pytest.raises(ValueError, match="5 m/s"):
        environment.wind_class(5.5)
    assert MAXIMUM_WIND_SPEED_M_S == 5.0
    assert WIND_VECTOR_TOLERANCE_M_S == 2.0


def test_the_reference_microphone_clears_the_barrier_top() -> None:
    assert environment.reference_microphone_height_m(4.0) == pytest.approx(5.5)
    assert REFERENCE_MICROPHONE_CLEARANCE_M == 1.5


def test_a_distant_source_takes_the_plain_clearance() -> None:
    height = environment.reference_microphone_height_m(4.0, source_to_barrier_m=20.0)
    assert height == pytest.approx(5.5)
    assert CLOSE_SOURCE_DISTANCE_M == 15.0


def test_a_close_source_takes_the_ten_degree_rule() -> None:
    height = environment.reference_microphone_height_m(4.0, source_to_barrier_m=10.0)
    expected = 10.0 * math.tan(
        math.atan(4.0 / 10.0) + math.radians(REFERENCE_ELEVATION_INCREMENT_DEG)
    )
    assert height == pytest.approx(expected)
    assert height > 5.5


def test_the_hemi_free_field_rule_takes_the_shorter_of_the_two() -> None:
    assert environment.hemi_free_field_distance_m(5.0) == pytest.approx(10.0)
    assert environment.hemi_free_field_distance_m(20.0) == pytest.approx(30.0)
    # The two rules cross at 15 m.
    assert environment.hemi_free_field_distance_m(15.0) == pytest.approx(30.0)


def test_the_printed_constants() -> None:
    assert ISO10847_OCTAVE_BAND_RANGE_HZ == (63.0, 4000.0)
    assert ISO10847_THIRD_OCTAVE_BAND_RANGE_HZ == (50.0, 5000.0)
    assert MINIMUM_RECEIVER_HEIGHT_M == 1.2
    assert MINIMUM_REPETITIONS == 3
    assert LONG_DISTANCE_M == 250.0
    assert TEMPERATURE_TOLERANCE_C == 10.0
    assert EQUIVALENT_SECTOR_DEG == 60.0
    assert EQUIVALENT_SURROUNDINGS_RADIUS_M == 30.0
    assert POINT_SOURCE_DIVERGENCE_DB == 6.0
    assert LINE_SOURCE_DIVERGENCE_DB == 3.0


def test_the_far_field_divergence_is_the_closed_form() -> None:
    assert POINT_SOURCE_DIVERGENCE_DB == pytest.approx(
        20.0 * math.log10(2.0), abs=0.021
    )
    assert LINE_SOURCE_DIVERGENCE_DB == pytest.approx(10.0 * math.log10(2.0), abs=0.011)


def test_table_two_has_its_four_classes() -> None:
    assert sorted(CLOUD_COVER_CLASSES) == [1, 2, 3, 4]
    assert "80 %" in CLOUD_COVER_CLASSES[1]
    assert CLOUD_COVER_CLASSES[4] == "clear night"


def test_the_plot_draws_three_series() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    reference_after, receiver_after = _campaign()
    res = environment.measured_insertion_loss_direct(
        REFERENCE_BEFORE,
        reference_after,
        RECEIVER_BEFORE,
        receiver_after,
        frequencies=BANDS,
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

    reference_after, receiver_after = _campaign()
    res = environment.measured_insertion_loss_direct(
        REFERENCE_BEFORE,
        reference_after,
        RECEIVER_BEFORE,
        receiver_after,
        frequencies=BANDS,
    )
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax, language="es")
    assert "barrera" in drawn.get_title()
    plt.close(fig)


def test_a_band_centre_at_zero_is_refused() -> None:
    with pytest.raises(ValueError, match="frequencies"):
        environment.measured_insertion_loss_direct(
            [76.0, 74.0],
            [78.0, 76.0],
            [63.0, 61.0],
            [58.0, 53.0],
            frequencies=[0.0, 250.0],
        )


def test_a_non_finite_wind_component_is_refused() -> None:
    with pytest.raises(ValueError, match="vector_component_m_s"):
        environment.wind_class(float("nan"))
