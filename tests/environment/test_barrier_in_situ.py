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
import warnings

import numpy as np
import pytest
from reference_data import barrier_in_situ as oracle
from reference_data import rounding

from phonometry import environment
from phonometry.environment.propagation.barrier_in_situ import (
    CLOSE_SOURCE_DISTANCE_M,
    CLOUD_COVER_CLASSES,
    EQUIVALENT_SECTOR_DEG,
    EQUIVALENT_SURROUNDINGS_RADIUS_M,
    ISO10847_BACKGROUND_CORRECTIONS_DB,
    ISO10847_MINIMUM_BACKGROUND_MARGIN_DB,
    ISO10847_OCTAVE_BAND_RANGE_HZ,
    ISO10847_PREFERRED_BACKGROUND_MARGIN_DB,
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
    # Measured as the NOTE words it, not as the implementation writes it: the
    # elevation from the near end of the source region to the microphone, less
    # the elevation to the top of the barrier, is the printed 10 degrees.
    # Restating the formula here would pass whatever the increment were
    # applied to. CEN/TS 16272-7:2015 8.2.3, printed folio 16 (PDF page 17),
    # words the same rule the same way, "10 degrees greater than to the top of
    # the barrier", which is what fixes this reading. All four geometries are
    # ones where the angle asks for more than the 1,5 m clearance, so the NOTE
    # is what sets the height.
    for distance, barrier in ((5.0, 4.0), (10.0, 4.0), (12.0, 2.5), (14.999, 5.0)):
        height = environment.reference_microphone_height_m(
            barrier, source_to_barrier_m=distance
        )
        to_the_top = math.degrees(math.atan(barrier / distance))
        to_the_microphone = math.degrees(math.atan(height / distance))
        assert height > barrier + REFERENCE_MICROPHONE_CLEARANCE_M
        assert to_the_microphone - to_the_top == pytest.approx(10.0, abs=1e-9)
    assert REFERENCE_ELEVATION_INCREMENT_DEG == 10.0


def test_the_clearance_governs_where_the_angle_asks_for_less() -> None:
    # ISO 10847:1997 7.2.2, printed folio 9 (PDF page 13): the height "shall be
    # at least 1,5 m above the top edge of the barriers". The NOTE under it
    # only ever raises the microphone, so it cannot take it under that. A 3 m
    # barrier 5 m from the source reaches its 10 degrees at 4,34 m, which is
    # under the 4,5 m the clause requires.
    angle = 5.0 * math.tan(math.atan(3.0 / 5.0) + math.radians(10.0))
    assert angle == pytest.approx(4.341, abs=1e-3)
    height = environment.reference_microphone_height_m(3.0, source_to_barrier_m=5.0)
    assert height == 4.5


def test_no_close_geometry_puts_the_microphone_under_the_clearance() -> None:
    # Every geometry of the NOTE's range on a 0,1 m grid whose barrier top
    # stands under 80 degrees from the source, where a finite height reaches
    # the increment. The result never falls under the clearance of 7.2.2, and
    # wherever it stands above it the 10 degrees of the NOTE hold exactly.
    limit = math.tan(math.radians(90.0 - REFERENCE_ELEVATION_INCREMENT_DEG))
    distances = [round(0.5 + 0.1 * step, 10) for step in range(145)]
    barriers = [round(0.1 + 0.1 * step, 10) for step in range(80)]
    governed = {"clearance": 0, "angle": 0}
    with warnings.catch_warnings():
        warnings.simplefilter("error", BarrierInSituWarning)
        for distance in distances:
            for barrier in barriers:
                if barrier / distance >= limit:
                    continue
                height = environment.reference_microphone_height_m(
                    barrier, source_to_barrier_m=distance
                )
                clearance = barrier + REFERENCE_MICROPHONE_CLEARANCE_M
                assert height >= clearance
                if height == clearance:
                    governed["clearance"] += 1
                else:
                    governed["angle"] += 1
                    to_the_top = math.degrees(math.atan(barrier / distance))
                    to_the_microphone = math.degrees(math.atan(height / distance))
                    assert to_the_microphone - to_the_top == pytest.approx(
                        REFERENCE_ELEVATION_INCREMENT_DEG, abs=1e-9
                    )
    # The sweep exercises both branches, not one of them.
    assert governed["clearance"] > 0
    assert governed["angle"] > 0


def test_a_barrier_top_past_eighty_degrees_keeps_the_clearance() -> None:
    # Once the top of the barrier stands 80 degrees or more above the near end
    # of the source region, no height puts the microphone 10 degrees higher
    # still, and the tangent of the NOTE's angle turns negative. The NOTE is a
    # preference and 7.2.2 a requirement, so the microphone keeps the 1,5 m
    # and the unreachable preference is reported.
    for distance, barrier, expected in ((1.0, 6.0, 7.5), (1.0, 10.0, 11.5)):
        with pytest.warns(BarrierInSituWarning, match="10 degrees"):
            height = environment.reference_microphone_height_m(
                barrier, source_to_barrier_m=distance
            )
        assert height == expected


def test_the_ten_degrees_are_not_measured_from_the_ground_plane() -> None:
    # FHWA-PD-96-046 6.1.2.1, printed folio 76 (PDF page 93), moves the
    # microphone of a barrier closer than 15 m to the source out to "a
    # distance of 15 m from the noise source", at a height where "the line of
    # sight between the microphone and the ground plane beneath the source is
    # at least 10 degrees", which is an absolute elevation and not an
    # increment. The two readings are not interchangeable: for a 4 m barrier
    # with the source 10 m away the absolute one, taken at the 15 m that page
    # prints, lands at 2,64 m, under the top of the barrier.
    # No document prints the height either reading yields, so the 6,2006 m
    # below is this library's answer pinned against change, not an oracle.
    absolute = 15.0 * math.tan(math.radians(REFERENCE_ELEVATION_INCREMENT_DEG))
    height = environment.reference_microphone_height_m(4.0, source_to_barrier_m=10.0)
    assert absolute < 4.0
    assert height == pytest.approx(6.2006, abs=1e-4)


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
        environment.wind_class(math.nan)


# The campaigns other people published against ISO 10847, which prints no
# worked example of its own. Every level was read on the printed page, and
# every expected value is the one that page prints beside those levels; both
# are in ``tests/reference_data/barrier_in_situ.py`` with the document, the
# folio and the PDF page. They report to 0,1 dB, so agreement is asserted to
# half of that.

PRINTED_TENTH_DB = 0.05


def test_the_cordero_campaign_reports_its_two_insertion_losses() -> None:
    # Cordero and others, "Metodología experimental para medida pérdidas por
    # inserción de pantallas acústicas de carretera", 41 Congreso Nacional de
    # Acústica, León, 2010, paper AAM_026. Tabla 1 on printed folio 5 (PDF
    # page 5) prints all four levels of two cases, and Tabla 2 on folio 6 the
    # insertion loss each gives; the running text prints them too, "13 dBA"
    # and "9,5 dBA". The screened object is a window rather than a barrier, so
    # what this anchors is the subtraction of 8.2.1 and the reporting rule of
    # 10 c), not the procedure around them.
    results = {}
    for case, levels in oracle.CORDERO_TABLA_1_DBA.items():
        reference_before, reference_after, receiver_before, receiver_after = levels
        results[case] = environment.measured_insertion_loss_direct(
            reference_before_db=[reference_before],
            reference_after_db=[reference_after],
            receiver_before_db=[receiver_before],
            receiver_after_db=[receiver_after],
        )
    for case, reported in oracle.CORDERO_TABLA_2_DBA.items():
        assert results[case].rounded().tolist() == [reported]
    assert float(results["con ruido"].insertion_loss_db[0]) == pytest.approx(
        oracle.CORDERO_UNROUNDED_CON_RUIDO_DBA, abs=PRINTED_TENTH_DB
    )


def test_the_lindeman_direct_runs_reproduce_their_printed_losses() -> None:
    # W. Lindeman, "Comparison of Noise Barrier Insertion-Loss
    # Methodologies", Transportation Research Record 1033, 1985. TABLE 8 on
    # printed folio 39 (PDF page 7), runs 2 and 3, the only ones whose four
    # levels are all printed and whose insertion loss the table gives.
    reference_before, reference_after, receiver_before, receiver_after = zip(
        *oracle.LINDEMAN_TABLE_8_DBA.values(), strict=True
    )
    res = environment.measured_insertion_loss_direct(
        reference_before_db=list(reference_before),
        reference_after_db=list(reference_after),
        receiver_before_db=list(receiver_before),
        receiver_after_db=list(receiver_after),
    )
    assert res.insertion_loss_db == pytest.approx(
        list(oracle.LINDEMAN_TABLE_8_INSERTION_LOSS_DBA.values()),
        abs=PRINTED_TENTH_DB,
    )


def test_the_lindeman_first_run_is_a_defect_of_the_source() -> None:
    # Run 1 of the same table prints 6,2 dB in column (7) where its own four
    # levels give 5,8 dB. TABLES 4 and 5 on printed folio 37 (PDF page 5)
    # reach both of those levels a second time through their own arithmetic,
    # and column (3) of TABLE 8 prints their difference as 6,6 dB, so the
    # levels are corroborated and the printed insertion loss is not. Neither
    # it nor the note's mean of 7,5 dBA is used as an expected value.
    reference_before, reference_after, receiver_before, receiver_after = (
        oracle.LINDEMAN_TABLE_8_RUN_1_DBA
    )
    res = environment.measured_insertion_loss_direct(
        reference_before_db=[reference_before],
        reference_after_db=[reference_after],
        receiver_before_db=[receiver_before],
        receiver_after_db=[receiver_after],
    )
    assert float(res.insertion_loss_db[0]) == pytest.approx(5.8, abs=PRINTED_TENTH_DB)
    assert float(res.insertion_loss_db[0]) != pytest.approx(
        oracle.LINDEMAN_TABLE_8_RUN_1_PRINTED_DBA, abs=PRINTED_TENTH_DB
    )


def test_the_lindeman_indirect_runs_and_their_mean() -> None:
    # TABLE 13 on printed folio 41 (PDF page 9): the equivalent site is the
    # "before" pair and the barrier site the "after" one. Both receivers stand
    # in the open, so C_r and C'_r cancel and this exercises the site pairing
    # of 8.2.2 rather than the facade branch.
    levels = oracle.LINDEMAN_TABLE_13_DBA
    res = environment.measured_insertion_loss_indirect(
        reference_before_db=list(levels["reference before"]),
        reference_after_db=list(levels["reference after"]),
        receiver_before_db=list(levels["receiver before"]),
        receiver_after_db=list(levels["receiver after"]),
    )
    assert res.insertion_loss_db == pytest.approx(
        list(oracle.LINDEMAN_TABLE_13_INSERTION_LOSS_DBA), abs=PRINTED_TENTH_DB
    )
    assert float(np.mean(res.insertion_loss_db)) == pytest.approx(
        oracle.LINDEMAN_TABLE_13_MEAN_DBA, abs=PRINTED_TENTH_DB
    )
    assert res.symbol == "D'_IL"


def test_the_lindeman_fourth_run_takes_its_level_from_the_table_above() -> None:
    # Column (2) of TABLE 13 prints 60,2 dBA for run 4, a repeat of run 3.
    # The table contradicts itself there rather than leaving it open: its own
    # column (3) prints 7,7 dBA for that run and 68,8 - 60,2 is 8,6. TABLE 12,
    # directly above on the same folio and covering the same microphone and
    # the same five runs, prints 61,1 dBA, which restores both columns.
    levels = oracle.LINDEMAN_TABLE_13_DBA
    run = 3
    res = environment.measured_insertion_loss_indirect(
        reference_before_db=[levels["reference before"][run]] * 2,
        reference_after_db=[levels["reference after"][run]] * 2,
        receiver_before_db=[
            levels["receiver before"][run],
            oracle.LINDEMAN_TABLE_13_RUN_4_MISPRINT_DBA,
        ],
        receiver_after_db=[levels["receiver after"][run]] * 2,
    )
    from_table_twelve, from_the_misprint = res.insertion_loss_db.tolist()
    assert from_table_twelve == pytest.approx(
        oracle.LINDEMAN_TABLE_13_INSERTION_LOSS_DBA[run], abs=PRINTED_TENTH_DB
    )
    assert from_the_misprint == pytest.approx(2.7, abs=1e-9)


def test_the_fhwa_worked_example_reaches_both_of_its_printed_answers() -> None:
    # C. S. Y. Lee and G. G. Fleming, Measurement of Highway-Related Noise,
    # FHWA-PD-96-046, May 1996, clause 6.6.3 on printed folio 84 (PDF page
    # 101), and the same example in FHWA-HEP-18-065 on folios 108 and 109.
    # L_edge is an FHWA edge-diffraction adjustment with no counterpart in
    # ISO 10847, so it is applied here rather than fed to the function. The
    # example lists a receiver level of 56,3 dB and then types 56,2 dB in its
    # expression, which is the whole of the difference between the 8,7 dB the
    # FHWA Noise Barrier Design Handbook prints for it in clause 15.1.2.1 and
    # the 8,8 dB the two manuals print.
    edge_db = oracle.FHWA_6_6_3_EDGE_DB
    for receiver_after, printed in oracle.FHWA_6_6_3_PRINTED_DB.values():
        res = environment.measured_insertion_loss_direct(
            reference_before_db=[oracle.FHWA_6_6_3_REFERENCE_BEFORE_DB],
            reference_after_db=[oracle.FHWA_6_6_3_REFERENCE_AFTER_DB],
            receiver_before_db=[oracle.FHWA_6_6_3_RECEIVER_BEFORE_DB],
            receiver_after_db=[receiver_after],
        )
        assert float(res.insertion_loss_db[0]) + edge_db == pytest.approx(
            printed, abs=PRINTED_TENTH_DB
        )


def test_an_exact_half_is_reported_as_the_even_whole_decibel() -> None:
    # Clause 10 c) asks for the nearest whole decibel and says nothing about a
    # tie. ISO 80000-1:2009 Annex B, B.3, printed folio 35 (PDF page 43),
    # supplies Rule A, the even multiple, and folio 36 (PDF page 44) calls it
    # "generally preferable". Its EXAMPLE 2 on folio 35 prints the ties at a
    # rounding range of 10: 1 225,0 becomes 1 220 and 1 235,0 becomes 1 240.
    # Divided by that range they are the exact halves below, both of them
    # binary-exact, which the ties of the printed 0,1 range are not. Rule B,
    # printed on folio 36, would give 1 230 for the first, so the pair
    # discriminates.
    ties = [
        rounding.ISO80000_1_ANNEX_B_ROUNDINGS[key]
        for key in rounding.ISO80000_1_RULE_A_TIES
    ]
    res = environment.measured_insertion_loss_direct(
        [0.0, 0.0],
        [number / scale for number, scale, _ in ties],
        [0.0, 0.0],
        [0.0, 0.0],
    )
    assert (res.rounded() * 10).tolist() == [
        multiples * scale for _, scale, multiples in ties
    ]
    ties = environment.measured_insertion_loss_direct(
        [0.0] * 6, [0.5, 1.5, 2.5, 3.5, 4.5, 5.5], [0.0] * 6, [0.0] * 6
    )
    assert ties.rounded().tolist() == [0, 2, 2, 4, 4, 6]


def test_the_upwind_class_is_printed_as_an_interval_by_the_fhwa_manual() -> None:
    # FHWA-PD-96-046 Table 3 "Classes of wind conditions", printed folio 35
    # (PDF page 52), prints "upwind -1 to -5", "calm -1 to +1" and "downwind
    # +1 to +5" of the source-to-receiver vector component, where ISO 10847
    # Table 1 prints the upwind row as "+ 1 to - 5". That is the corroboration
    # the errata entry rests on. FHWA gives one flat set with no distance
    # split, so it is read against the short-distance table, the only one of
    # the two in ISO 10847 with an upwind class at all. The shared endpoints
    # are left alone: neither document says which class -1 m/s belongs to.
    for name, (low, high) in oracle.FHWA_TABLE_3_WIND_CLASSES_M_S.items():
        for fraction in (0.25, 0.5, 0.75):
            component = low + fraction * (high - low)
            assert environment.wind_class(component, short_distance=True) == name


def test_the_background_table_is_reprinted_by_a_second_committee() -> None:
    # CEN/TS 16272-7:2015 (E), clause 7.3.7 and Table 4, printed folio 14 (PDF
    # page 15): the same correction in two grouped rows, "4 and 5" against
    # -2 dB and "6, 7, 8, 9" against -1 dB, with the same prose asking for a
    # 10 dB margin and calling a margin under 4 dB invalid.
    for margins, printed in oracle.CEN_TS_16272_7_TABLE_4_DB:
        corrections = environment.barrier_background_correction_db(list(margins))
        assert corrections.tolist() == [printed] * len(margins)
    assert (
        ISO10847_MINIMUM_BACKGROUND_MARGIN_DB == oracle.CEN_TS_16272_7_MINIMUM_MARGIN_DB
    )
    assert (
        ISO10847_PREFERRED_BACKGROUND_MARGIN_DB
        == oracle.CEN_TS_16272_7_PREFERRED_MARGIN_DB
    )
    with pytest.raises(ValueError, match="invalid"):
        environment.barrier_background_correction_db([3.9])


def test_the_jagniatinskis_campaign_uses_only_the_printed_difference() -> None:
    # A. Jagniatinskis, B. Fiks and M. Mickaitis, "Determination of Insertion
    # Loss of Acoustic Barriers under Specific Conditions", Procedia
    # Engineering 187, 2017. Table 1 on printed folio 293 (PDF page 5) prints
    # the reference level, the site level and one "environment correction",
    # -9,1 and -6,9 dBA with the sign the table gives them, which is the
    # "before" difference of 8.2.1 given as a single number with its sign
    # reversed: 76,0 - 56,3 - 9,1 = 10,6. The two levels behind it are free.
    # Site 1 is a 5 m barrier with the receiver 30 m away and site 2 a
    # separate 6 m barrier at 20 m. The 8,0 dBA is the same site read from its
    # total level, printed on folio 294. The residual levels came from an ISO
    # 1996 extraction, which is not the background treatment of 6.4 and is not
    # exercised here.
    printed = oracle.JAGNIATINSKIS_TABLE_1_DBA.values()
    for reference_after, receiver_after, correction, insertion_loss in printed:
        for offset in (0.0, 6.0, -13.25):
            reference_before = reference_after + offset
            res = environment.measured_insertion_loss_direct(
                reference_before_db=[reference_before],
                reference_after_db=[reference_after],
                receiver_before_db=[reference_before + correction],
                receiver_after_db=[receiver_after],
            )
            assert float(res.insertion_loss_db[0]) == pytest.approx(
                insertion_loss, abs=PRINTED_TENTH_DB
            )


def test_a_campaign_with_no_reference_microphone_is_the_plain_difference() -> None:
    # L. Rodiño and F. Masson, "Diseño e implementación de una barrera
    # acústica para motores fuera de borda", XIII Congreso Argentino de
    # Acústica, Buenos Aires, 2015, paper AdAA2015-A009. Tabla 2 on printed
    # folio 7 (PDF page 7): the level at the crew position without the screen
    # and with it, for three engine settings, unweighted and A-weighted. No
    # reference microphone was used, so 8.2.1 degenerates to the plain
    # difference and the reference pair below is a constant, not a
    # measurement. What that anchors is the sign, positive for a screen that
    # works, and the degenerate reduction; the paper cites ISO 14509, not
    # ISO 10847, and the screen sits in the near field of the source.
    for weighting in ("Z", "A"):
        rows = [
            row
            for setting, row in oracle.RODINO_TABLA_2_DB.items()
            if setting.startswith(f"{weighting},")
        ]
        assert len(rows) == 3
        res = environment.measured_insertion_loss_direct(
            [0.0] * len(rows),
            [0.0] * len(rows),
            [without for without, _, _ in rows],
            [with_screen for _, with_screen, _ in rows],
        )
        assert res.insertion_loss_db == pytest.approx(
            [printed for _, _, printed in rows], abs=PRINTED_TENTH_DB
        )


def test_the_six_decibels_are_a_pressure_doubling() -> None:
    # ISO 10847 8.2.2 prints C'_r = 6 dB and leaves it at that. D. A. Bies,
    # C. H. Hansen and C. Q. Howard, Engineering Noise Control, 5th edition,
    # CRC Press, 2017, printed folio 201 (PDF page 230), section 4.9.2, says
    # what it is: with the receiver within about a tenth of a wavelength of a
    # reflecting surface "pressure doubling occurs with an apparent increase
    # in sound pressure level of 6 dB". ISO 1996-2:2017 9.2.1.2 b) 2), printed
    # folio 14 (PDF page 20), prints the same figure in its NOTE 2 as the
    # ideal case, while asking for 5,7 dB when its Annex B conditions are met,
    # so it corroborates the mechanism and not the flat 6 dB.
    assert RECEIVER_CORRECTIONS_DB["reflecting_surface"] == pytest.approx(
        20.0 * math.log10(2.0), abs=0.021
    )
    assert RECEIVER_CORRECTIONS_DB["hemi_free_field"] == 0.0


def test_the_divergence_rates_are_printed_in_a_textbook_too() -> None:
    # M. J. Crocker (ed.), Handbook of Noise and Vibration Control, Wiley,
    # 2007, chapter 120, printed folios 1433 and 1434 (PDF pages 1442 and
    # 1443): "a 6-dB reduction in sound pressure level with each doubling of
    # distance" for a vehicle treated as a point source, and "a 3-dB reduction
    # in level with each doubling of distance" once the vehicles spread into a
    # line. Definition 3.10 of ISO 10847 states the same two in words.
    assert POINT_SOURCE_DIVERGENCE_DB == 6.0
    assert LINE_SOURCE_DIVERGENCE_DB == 3.0
