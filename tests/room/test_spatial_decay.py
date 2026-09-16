#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for spatial sound distribution curves (ISO 14257:2001).

The oracle is Annex C, a measurement in a 83 m by 32 m by 11 m shipyard hall
with eleven microphone positions from 2 m to 48 m. The annex prints the source
power (Table C.2), its free-field-over-a-reflecting-plane curve (Table C.3), the
levels measured in the room (Table C.4), the two sound distribution curves
(Tables C.5 and C.6) and the four result tables (C.7 to C.10), which is enough
to check Equations (1), (2), (4), (5), (6), (7), (B.1) and (B.4) against printed
numbers rather than against themselves.

Annex C is printed in the document that defines the method, so it cannot say
whether the method was read right. Three published sources can, and the second
half of this file is theirs. Suva 66008.f, a Swiss guide for industrial
workrooms, prints a 21 position curve and the 42 descriptors its own analysis
program read off it, without ever naming ISO 14257: it takes the two quantities
from VDI 3760 and EN ISO 11690-1. IFA-LSA 01-234, a German guidance sheet,
prints four levels at four distances and the decay rate they give. And BAuA
research report Fb 1083 prints the fitting density an independent VDI 3760 tool
computed for surveyed workrooms, which is the quantity the prediction of
ISO 11690-3 takes instead of the fittings themselves.

Every printed number is in ``tests/reference_data/spatial_decay.py``, with the
folio and the page it was read on, and the conformance rows read it there too.
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest
from reference_data import spatial_decay as oracle

from phonometry import room
from phonometry.room.spatial_decay import (
    ADJACENT_BAND_LIMIT_DB,
    DECADE_TO_DOUBLING,
    EVALUATION_DISTANCES_M,
    FREE_FIELD_OFFSET_DB,
    ISO14257_REFERENCE_DISTANCE_M,
    MAX_DIRECTIVITY_INDEX_DB,
    NORMALIZED_OFFSET_DB,
    OMNIDIRECTIONAL_RAMP_HZ,
    OMNIDIRECTIONAL_TOLERANCE_DB,
    PINK_NOISE_WEIGHTS_DB,
    STABILITY_TOLERANCE_DB,
    TYPICAL_FAR_LIMIT_M,
    TYPICAL_NEAR_LIMIT_M,
)

#: Table C.1: where the eleven microphones stood, as an array to select from.
DISTANCES_M = np.array(oracle.ANNEX_C_DISTANCES_M, dtype=float)


def _raw(band: int) -> np.ndarray:
    """The uncorrected curve of Table C.5, from Equation (1)."""
    return room.sound_distribution_value(
        oracle.ANNEX_C_ROOM_LEVELS_DB[band], oracle.ANNEX_C_SOURCE_POWER_DB[band]
    )


def _corrected(band: int) -> np.ndarray:
    """The Annex B corrected curve of Table C.6."""
    measured = room.sound_distribution_value(
        oracle.ANNEX_C_FREE_FIELD_LEVELS_DB[band], oracle.ANNEX_C_SOURCE_POWER_DB[band]
    )
    return room.corrected_distribution_value(
        _raw(band), measured, DISTANCES_M, source_height_m=0.0
    )


def _select(low: float, high: float) -> np.ndarray:
    return (DISTANCES_M >= low) & (DISTANCES_M <= high)


def test_the_distribution_value_is_the_level_less_the_power() -> None:
    got = room.sound_distribution_value([85.7, 82.5], 97.6)
    assert got.tolist() == [pytest.approx(-11.9), pytest.approx(-15.1)]


def test_the_reference_curve_falls_six_decibels_per_doubling() -> None:
    ref = room.reference_distribution_value([1.0, 2.0, 4.0])
    assert ref[0] == pytest.approx(-11.0)
    assert ref[0] - ref[1] == pytest.approx(6.0206, abs=1e-3)
    assert ref[1] - ref[2] == pytest.approx(6.0206, abs=1e-3)


def test_the_printed_eleven_is_ten_lg_four_pi() -> None:
    exact = 10.0 * np.log10(4.0 * np.pi)
    assert exact == pytest.approx(10.99, abs=5e-3)
    assert ISO14257_REFERENCE_DISTANCE_M == 1.0


def test_a_source_on_the_floor_gains_three_decibels() -> None:
    free = room.reference_distribution_value([4.0])
    floor = room.floor_reference_value([4.0], source_height_m=0.0)
    assert floor[0] - free[0] == pytest.approx(10.0 * np.log10(2.0), abs=1e-9)


def test_a_source_high_above_the_path_loses_the_floor_gain() -> None:
    near = room.floor_reference_value([2.0], source_height_m=0.0)
    high = room.floor_reference_value([2.0], source_height_m=8.0)
    assert high[0] < near[0]


@pytest.mark.parametrize("band", [125, 250, 500, 1000, 2000, 4000])
def test_annex_b_reproduces_table_c6(band: int) -> None:
    got = _corrected(band)
    assert np.allclose(got, oracle.ANNEX_C_TABLE_C6_DB[band], atol=0.1)


def test_the_normalized_curve_reproduces_the_last_column_of_table_c6() -> None:
    """Within 0,1 dB and not the printed 0,05: the printed 6,2 dB is 0,05 dB
    short of the sum of the printed Table 1 weights, which is what the annex
    normalised with, so every value comes out 0,05 dB high, and
    ``test_the_annex_normalized_with_the_table_one_sum_and_not_the_printed_offset``
    holds the split (see the errata registry).
    """
    corrected = {band: _corrected(band) for band in oracle.ANNEX_C_SOURCE_POWER_DB}
    got = [
        room.normalized_distribution_value(
            [corrected[b][i] for b in oracle.ANNEX_C_SOURCE_POWER_DB]
        )
        for i in range(DISTANCES_M.size)
    ]
    assert np.allclose(got, oracle.ANNEX_C_TABLE_C6_NORMALIZED_DB, atol=0.1)


@pytest.mark.parametrize("region", ["near", "middle", "far"])
@pytest.mark.parametrize("band", [125, 250, 500, 1000, 2000, 4000])
def test_the_decay_rate_reproduces_table_c7(region: str, band: int) -> None:
    low, high = oracle.ANNEX_C_RANGES_M[region]
    keep = _select(low, high)
    got = room.spatial_decay_rate(_corrected(band)[keep], DISTANCES_M[keep])
    assert got == pytest.approx(oracle.ANNEX_C_TABLE_C7_DB[region][band], abs=0.06)


@pytest.mark.parametrize("region", ["near", "middle", "far"])
@pytest.mark.parametrize("band", [125, 250, 500, 1000, 2000, 4000])
def test_the_excess_reproduces_table_c9(region: str, band: int) -> None:
    low, high = oracle.ANNEX_C_RANGES_M[region]
    keep = _select(low, high)
    got = room.mean_level_excess(_raw(band)[keep], DISTANCES_M[keep])
    assert got == pytest.approx(oracle.ANNEX_C_TABLE_C9_DB[region][band], abs=0.07)


@pytest.mark.parametrize("region", ["near", "middle", "far"])
def test_the_normalized_results_reproduce_tables_c8_and_c10(region: str) -> None:
    """The decay rate at 0,06 dB, a slope that does not see the offset of
    Equation (4); the excess at 0,11 dB, a level that carries the 0,05 dB the
    printed 6,2 falls short of the sum of the printed Table 1 weights, which is
    what the annex normalised with, on top of the rounding (see the errata
    registry and the test that pins the split).
    """
    low, high = oracle.ANNEX_C_RANGES_M[region]
    keep = _select(low, high)
    corrected = {band: _corrected(band) for band in oracle.ANNEX_C_SOURCE_POWER_DB}
    raw = {band: _raw(band) for band in oracle.ANNEX_C_SOURCE_POWER_DB}
    norm_corrected = np.array(
        [
            room.normalized_distribution_value(
                [corrected[b][i] for b in oracle.ANNEX_C_SOURCE_POWER_DB]
            )
            for i in range(DISTANCES_M.size)
        ]
    )
    norm_raw = np.array(
        [
            room.normalized_distribution_value(
                [raw[b][i] for b in oracle.ANNEX_C_SOURCE_POWER_DB]
            )
            for i in range(DISTANCES_M.size)
        ]
    )
    decay = room.spatial_decay_rate(norm_corrected[keep], DISTANCES_M[keep])
    excess = room.mean_level_excess(norm_raw[keep], DISTANCES_M[keep])
    assert decay == pytest.approx(oracle.ANNEX_C_TABLE_C8_DB[region], abs=0.06)
    assert excess == pytest.approx(oracle.ANNEX_C_TABLE_C10_DB[region], abs=0.11)


def test_the_annex_corrects_the_decay_but_not_the_excess() -> None:
    """The inconsistency Annex C leaves behind, pinned so it cannot drift.

    C.1 says the experimental reference curve "is known and used for
    correcting the values measured in the workroom", and Table C.7 needs that
    correction: without it the middle-range decay at 1 kHz comes out 4,7 dB
    where the annex prints 4,4. Table C.9 needs the opposite: with the
    correction the same range at 1 kHz gives 6,7 dB where the annex prints 7,3,
    and without it 7,3. See the errata registry.
    """
    keep = _select(*oracle.ANNEX_C_RANGES_M["middle"])
    raw, corrected = _raw(1000)[keep], _corrected(1000)[keep]
    distances = DISTANCES_M[keep]
    assert room.spatial_decay_rate(corrected, distances) == pytest.approx(4.4, abs=0.05)
    assert room.spatial_decay_rate(raw, distances) == pytest.approx(4.7, abs=0.05)
    assert room.mean_level_excess(raw, distances) == pytest.approx(7.3, abs=0.05)
    assert room.mean_level_excess(corrected, distances) == pytest.approx(6.7, abs=0.05)


def test_the_table_one_weights_are_the_printed_ones() -> None:
    assert PINK_NOISE_WEIGHTS_DB == oracle.TABLE_1_PINK_NOISE_WEIGHTS_DB
    assert NORMALIZED_OFFSET_DB == 6.2


def test_the_annex_normalized_with_the_table_one_sum_and_not_the_printed_offset() -> (
    None
):
    """Equation (4) prints 6,2 dB where Table 1 sums to 6,251 5 dB (see the errata).

    The printed weights are the A-weighting to one decimal and the printed
    constant is the A-weighting's energy sum to one decimal, rounded apart, so
    the printed table sums to 6,3 and not to the printed 6,2. Annex C was
    normalised exactly: Equation (3) under the Table 1 weights, which is
    Equation (4) with the sum of those weights, lands all eleven values of the
    last column of Table C.6 and the three of Table C.10 inside their printed
    rounding, and the printed 6,2 dB lands nine of the fourteen one unit high
    in the last place, every departure positive. The library keeps the printed
    constant, so both counts are held here so that neither the constant nor
    the 0,1 dB tolerances of the two tests above can drift.
    """
    weights = [
        PINK_NOISE_WEIGHTS_DB[float(band)] for band in oracle.ANNEX_C_SOURCE_POWER_DB
    ]
    exact_sum = 10.0 * np.log10(np.sum(10.0 ** (np.asarray(weights) / 10.0)))
    assert exact_sum == pytest.approx(6.2515, abs=5e-4)
    assert round(float(exact_sum), 1) == 6.3
    assert NORMALIZED_OFFSET_DB == 6.2

    corrected = {band: _corrected(band) for band in oracle.ANNEX_C_SOURCE_POWER_DB}
    raw = {band: _raw(band) for band in oracle.ANNEX_C_SOURCE_POWER_DB}

    def _both(curve: dict[int, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
        rows = [
            [curve[b][i] for b in oracle.ANNEX_C_SOURCE_POWER_DB]
            for i in range(DISTANCES_M.size)
        ]
        by_sum = np.array([room.spectrum_distribution_value(r, weights) for r in rows])
        by_print = np.array([room.normalized_distribution_value(r) for r in rows])
        return by_sum, by_print

    by_sum, by_print = _both(corrected)
    assert np.allclose(by_print - by_sum, exact_sum - NORMALIZED_OFFSET_DB, atol=1e-9)
    dep_sum = by_sum - np.asarray(oracle.ANNEX_C_TABLE_C6_NORMALIZED_DB)
    dep_print = by_print - np.asarray(oracle.ANNEX_C_TABLE_C6_NORMALIZED_DB)
    assert np.all(np.abs(dep_sum) <= 0.05)
    assert np.all(dep_print > 0.0)
    assert int(np.sum(np.abs(dep_print) > 0.05)) == 6

    raw_by_sum, raw_by_print = _both(raw)
    high = 0
    for region, want in oracle.ANNEX_C_TABLE_C10_DB.items():
        keep = _select(*oracle.ANNEX_C_RANGES_M[region])
        with_sum = room.mean_level_excess(raw_by_sum[keep], DISTANCES_M[keep])
        with_print = room.mean_level_excess(raw_by_print[keep], DISTANCES_M[keep])
        assert abs(with_sum - want) <= 0.05
        assert with_print - want > 0.0
        high += int(abs(with_print - want) > 0.05)
    assert high == 3


def test_the_printed_factor_is_not_the_logarithm_of_two() -> None:
    """Equation (5) prints 0,3 where Equation (8) prints lg 2 (see the errata)."""
    assert DECADE_TO_DOUBLING == 0.3
    assert np.log10(2.0) == pytest.approx(0.30103, abs=1e-5)
    assert abs(DECADE_TO_DOUBLING - np.log10(2.0)) / np.log10(2.0) < 0.005


def test_a_frequency_outside_table_one_is_refused() -> None:
    with pytest.raises(ValueError, match="Table 1"):
        room.normalized_distribution_value(
            [0.0] * 6, frequencies=[63, 125, 250, 500, 1000, 2000]
        )


def test_a_near_boundary_inside_the_first_metre_is_refused() -> None:
    """A d1 under 1 m leaves no near region, not a narrow one."""
    with pytest.raises(ValueError, match="near region"):
        room.distance_region(1.0, near_limit_m=0.5)


def test_a_repeated_band_is_refused_rather_than_weighed_twice() -> None:
    """Six values that repeat 125 Hz leave 4 kHz out of Equation (4)."""
    with pytest.raises(ValueError, match="once"):
        room.normalized_distribution_value(
            [-13.0, -14.0, -15.0, -16.0, -17.0, -18.0],
            frequencies=[125, 125, 250, 500, 1000, 2000],
        )


def test_the_six_bands_may_come_in_any_order() -> None:
    values = [-13.0, -14.0, -15.0, -16.0, -17.0, -18.0]
    shuffled = room.normalized_distribution_value(
        values, frequencies=[4000, 125, 250, 500, 1000, 2000]
    )
    canonical = room.normalized_distribution_value(
        [-14.0, -15.0, -16.0, -17.0, -18.0, -13.0]
    )
    assert shuffled == pytest.approx(canonical)


def test_the_spectrum_curve_collapses_to_the_band_value_for_one_band() -> None:
    got = room.spectrum_distribution_value([-20.0], [95.0])
    assert got == pytest.approx(-20.0)


def test_a_louder_band_dominates_the_spectrum_curve() -> None:
    quiet = room.spectrum_distribution_value([-10.0, -30.0], [80.0, 80.0])
    loud = room.spectrum_distribution_value([-10.0, -30.0], [60.0, 100.0])
    assert loud < quiet


def test_the_regions_are_the_printed_boundaries() -> None:
    assert TYPICAL_NEAR_LIMIT_M == 5.0
    assert TYPICAL_FAR_LIMIT_M == 16.0
    assert room.distance_region(4.0) == "near"
    assert room.distance_region(10.0) == "middle"
    assert room.distance_region(30.0) == "far"
    assert EVALUATION_DISTANCES_M == {"near": 4.0, "middle": 10.0, "far": 30.0}


def test_a_distance_inside_the_first_metre_is_refused() -> None:
    with pytest.raises(ValueError, match="near region"):
        room.distance_region(0.5)


def test_the_omnidirectionality_ramp_lands_on_its_printed_ends() -> None:
    assert room.omnidirectionality_tolerance_db(500.0) == pytest.approx(2.0)
    assert room.omnidirectionality_tolerance_db(630.0) == pytest.approx(2.0)
    assert room.omnidirectionality_tolerance_db(800.0) == pytest.approx(5.0)
    assert room.omnidirectionality_tolerance_db(1000.0) == pytest.approx(8.0)
    assert room.omnidirectionality_tolerance_db(5000.0) == pytest.approx(8.0)


def test_a_frequency_that_names_no_third_octave_is_refused() -> None:
    with pytest.raises(ValueError, match="nominal one-third-octave"):
        room.omnidirectionality_tolerance_db(700.0)


def test_a_curve_carries_its_region_and_its_two_descriptors() -> None:
    keep = _select(*oracle.ANNEX_C_RANGES_M["middle"])
    res = room.spatial_decay_curve(
        _corrected(1000)[keep], DISTANCES_M[keep], region="whole", band_hz=1000.0
    )
    assert res.region == "whole"
    assert res.band_hz == 1000.0
    assert res.decay_rate_db == pytest.approx(4.4, abs=0.05)
    assert res.level_excess_db.size == res.distances_m.size


def test_a_region_with_one_position_is_refused() -> None:
    with pytest.raises(ValueError, match="at least"):
        room.spatial_decay_curve([-20.0, -30.0], [2.0, 30.0], region="middle")


def test_an_unknown_region_is_refused() -> None:
    with pytest.raises(ValueError, match="region"):
        room.spatial_decay_curve([-20.0, -30.0], [2.0, 4.0], region="close")


def test_positions_at_one_distance_cannot_be_regressed() -> None:
    with pytest.raises(ValueError, match="distinct distances"):
        room.spatial_decay_rate([-20.0, -21.0], [4.0, 4.0])


def test_distances_that_do_not_increase_are_refused() -> None:
    with pytest.raises(ValueError, match="increase"):
        room.mean_level_excess([-20.0, -21.0, -22.0], [4.0, 8.0, 6.0])


def test_the_excess_at_a_distance_reads_the_line_not_the_points() -> None:
    keep = _select(*oracle.ANNEX_C_RANGES_M["middle"])
    values, distances = _raw(1000)[keep], DISTANCES_M[keep]
    at_ten = room.level_excess_at(values, distances, EVALUATION_DISTANCES_M["middle"])
    mean = room.mean_level_excess(values, distances)
    assert at_ten == pytest.approx(mean, abs=1.0)


def test_a_correction_that_removes_every_joule_is_refused() -> None:
    with pytest.raises(ValueError, match="cannot be louder"):
        room.corrected_distribution_value([-30.0], [-10.0], [4.0], source_height_m=0.0)


def test_the_plot_draws_the_curve_the_reference_and_the_fit() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    keep = _select(*oracle.ANNEX_C_RANGES_M["middle"])
    res = room.spatial_decay_curve(
        _corrected(1000)[keep], DISTANCES_M[keep], region="whole"
    )
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax)
    assert len(drawn.lines) == 3
    plt.close(fig)


def test_the_spanish_plot_translates_its_title() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    keep = _select(*oracle.ANNEX_C_RANGES_M["middle"])
    res = room.spatial_decay_curve(
        _corrected(1000)[keep], DISTANCES_M[keep], region="whole"
    )
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax, language="es")
    assert "espacial" in drawn.get_title()
    plt.close(fig)


# ---------------------------------------------------------------------------
# Annex A, and the source Annex C qualified against it
# ---------------------------------------------------------------------------


def test_the_annex_a_limits_are_the_printed_ones() -> None:
    """A.1 on printed folio 14, A.2 and A.4 on printed folio 15."""
    assert MAX_DIRECTIVITY_INDEX_DB == 8.0
    assert OMNIDIRECTIONAL_TOLERANCE_DB == (2.0, 8.0)
    assert OMNIDIRECTIONAL_RAMP_HZ == (630.0, 1000.0)
    assert ADJACENT_BAND_LIMIT_DB == 8.0
    assert STABILITY_TOLERANCE_DB == {(100.0, 160.0): 1.0, (200.0, 5000.0): 0.5}


def test_the_annex_c_source_is_inside_the_limits_it_is_declared_against() -> None:
    """C.3 on printed folio 19, which prints the declaration and then "OK".

    The annex gives one maximum directivity index with no band attached, so it
    says nothing about the ramp of A.1: 4,4 dB would fail the +/- 2 dB the ramp
    allows at or below 630 Hz, and the annex still passes the source. Only the
    8 dB cap and the adjacent-band step can be read off this declaration.
    """
    declared = oracle.ANNEX_C_SOURCE_DECLARATION_DB
    assert declared["directivity index"] <= MAX_DIRECTIVITY_INDEX_DB
    assert declared["adjacent band step"] <= ADJACENT_BAND_LIMIT_DB


def test_the_a_weighted_source_power_reproduces_table_c2() -> None:
    """Table C.2 on printed folio 18 prints 115,7 dB in its last column.

    Equation (4) is the energy sum under the Table 1 weights less 6,2 dB, so
    adding the offset back leaves the plain A-weighted total. This is the one
    printed figure of Annex C that the Table C.6 chain never touches.
    """
    total = (
        room.normalized_distribution_value(
            list(oracle.ANNEX_C_SOURCE_POWER_DB.values())
        )
        + NORMALIZED_OFFSET_DB
    )
    assert total == pytest.approx(oracle.ANNEX_C_SOURCE_POWER_A_WEIGHTED_DB, abs=0.05)


# ---------------------------------------------------------------------------
# Equation (8) against Tables C.11 and C.12
# ---------------------------------------------------------------------------


def test_equation_eight_does_not_give_tables_c11_and_c12() -> None:
    """The annex is inconsistent here, and it is not a misprint.

    Equation (8) is read over printed curves only, so what is pinned is the
    annex against itself and not a curve this library rebuilt. Over the
    printed D of Table C.5, the curve the excess of Table C.9 is computed on
    and the basis of the errata entry, it misses 15 of the 18 figures of Table
    C.11, by as much as 1,55 dB; over the one printed A-weighted curve, the
    last column of Table C.6, it misses all three of Table C.12. The departures
    carry no systematic sign. The BS printing of ISO 14257:2001 (printed folio
    24) and the AENOR printing UNE-EN ISO 14257:2002 (printed folio 30) carry
    the same digits, so neither is a corrupted copy of the other and the two
    tables cannot be used as an oracle of Equation (8).
    """
    # The transcription of Table C.5 is checked against the two printed tables
    # it is the difference of before it is used.
    for band, printed in oracle.ANNEX_C_TABLE_C5_DB.items():
        difference = (
            np.asarray(oracle.ANNEX_C_ROOM_LEVELS_DB[band])
            - oracle.ANNEX_C_SOURCE_POWER_DB[band]
        )
        assert difference == pytest.approx(printed, abs=1e-9), band
    band_departures = []
    for region, row in oracle.ANNEX_C_TABLE_C11_DB.items():
        keep = _select(*oracle.ANNEX_C_RANGES_M[region])
        for band, want in row.items():
            got = room.level_excess_at(
                np.asarray(oracle.ANNEX_C_TABLE_C5_DB[band])[keep],
                DISTANCES_M[keep],
                EVALUATION_DISTANCES_M[region],
            )
            band_departures.append(got - want)
    assert sum(abs(value) > 0.05 for value in band_departures) == 15
    assert min(band_departures) == pytest.approx(-0.408, abs=0.005)
    assert max(band_departures) == pytest.approx(1.546, abs=0.005)
    normalized = np.asarray(oracle.ANNEX_C_TABLE_C6_NORMALIZED_DB)
    weighted_departures = []
    for region, want in oracle.ANNEX_C_TABLE_C12_DB.items():
        keep = _select(*oracle.ANNEX_C_RANGES_M[region])
        got = room.level_excess_at(
            normalized[keep], DISTANCES_M[keep], EVALUATION_DISTANCES_M[region]
        )
        weighted_departures.append(got - want)
    assert weighted_departures == pytest.approx([-0.350, -0.272, 0.453], abs=0.005)


# ---------------------------------------------------------------------------
# Suva 66008.f, 8th revised edition, August 2006
# ---------------------------------------------------------------------------
#
# Walter Lips, "Acoustique des locaux industriels. Informations pour
# projeteurs, architectes et ingenieurs", Suva (Caisse nationale suisse
# d'assurance en cas d'accidents), reference 66008.f. Tableau 2 and the
# "Parametres resumes" summary inside Figure 7 are on PDF page 13, printed
# page 11; the distance ranges and the measurement radii are on PDF page 11,
# printed page 9.


def _suva_range(column: str, region: str) -> tuple[np.ndarray, np.ndarray]:
    """One printed column over one printed range, as values and distances."""
    index = oracle.SUVA_COLUMNS.index(column)
    low, high = oracle.SUVA_RANGES_M[region]
    radii = [radius for radius in oracle.SUVA_CURVE_DB if low <= radius <= high]
    values = [oracle.SUVA_CURVE_DB[radius][index] for radius in radii]
    return np.array(values, dtype=float), np.array(radii, dtype=float)


@pytest.mark.parametrize("region", ["near", "middle", "far"])
@pytest.mark.parametrize("column", oracle.SUVA_COLUMNS)
def test_the_suva_decay_rates_reproduce(column: str, region: str) -> None:
    """Equation (5) over a curve this project had no part in measuring.

    The tolerance is 0,06 dB rather than the 0,05 dB the printed tenth would
    suggest, for two of the 21 values: DL2 in the far range at 250 Hz and at
    2 kHz land 0,001 dB the wrong side of the rounding boundary. That is
    Equation (5) printing 0,3 where the survey's program used lg 2, which is
    the same 0,3 % the errata registry records.
    """
    want = oracle.SUVA_DECAY_DB[region][oracle.SUVA_COLUMNS.index(column)]
    got = room.spatial_decay_rate(*_suva_range(column, region))
    assert got == pytest.approx(want, abs=0.06)


@pytest.mark.parametrize("region", ["near", "middle", "far"])
@pytest.mark.parametrize("column", oracle.SUVA_COLUMNS)
def test_the_suva_excesses_reproduce(column: str, region: str) -> None:
    """Equations (6) and (7) over the same curve, every value to the tenth."""
    want = oracle.SUVA_EXCESS_DB[region][oracle.SUVA_COLUMNS.index(column)]
    got = room.mean_level_excess(*_suva_range(column, region))
    assert got == pytest.approx(want, abs=0.05)


def test_the_suva_excesses_pin_the_free_field_reference() -> None:
    """A wrong offset in Equation (2) shifts every DLf by the same constant.

    So the mean of the 21 residuals says which reference the other program
    measured its excess against. It is the whole sphere, 10 lg(4 pi), not the
    hemisphere a source standing on the floor would suggest and not an Annex B
    correction.
    """
    residuals = [
        room.mean_level_excess(*_suva_range(column, region))
        - oracle.SUVA_EXCESS_DB[region][index]
        for region in oracle.SUVA_RANGES_M
        for index, column in enumerate(oracle.SUVA_COLUMNS)
    ]
    implied = FREE_FIELD_OFFSET_DB - float(np.mean(residuals))
    assert implied == pytest.approx(float(10.0 * np.log10(4.0 * np.pi)), abs=0.02)
    assert abs(implied - 8.0) > 2.0


@pytest.mark.parametrize("radius_m", oracle.SUVA_RADII_M)
def test_every_printed_radius_lands_in_a_range_that_admits_it(radius_m: float) -> None:
    """The survey prints the partition as numbers, which 6.2 never does.

    It prints the three ranges as closed intervals, so 5 m and 16 m are each
    named by two of them, and 6.2 writes "from 1 m to d1", "from d1 to d2" and
    "from d2" without saying which side owns a boundary. Neither page pins it,
    so what is checked is that every radius lands in a range that admits it.
    """
    admitted = [
        name
        for name, (low, high) in oracle.SUVA_RANGES_M.items()
        if low <= radius_m <= high
    ]
    assert room.distance_region(radius_m) in admitted


# ---------------------------------------------------------------------------
# IFA-LSA 01-234, DGUV, April 2020
# ---------------------------------------------------------------------------
#
# Laermschutz-Arbeitsblatt IFA-LSA 01-234, "Raumakustik in industriellen
# Arbeitsraeumen". Tab. 4.4 and Equation (4.4) are on PDF page 17, printed
# folio 17; the worked 500 Hz line, Equation (4.5) and Tab. 4.5 are on PDF
# page 18, printed folio 18.

#: Tab. 4.4: the four positions of the path, as an array.
IFA_DISTANCES_M = np.array(oracle.IFA_LSA_01_234_DISTANCES_M)


@pytest.mark.parametrize("band", list(oracle.IFA_LSA_01_234_DECAY_DB))
def test_the_ifa_decay_rates_reproduce(band: int) -> None:
    """Equation (5) against a second worked example, from a second country.

    The sheet's own Equation (4.4) is not Equation (5) verbatim: it is that
    regression specialised to these four fixed distances, with the sum of the
    logarithms rounded to 1,306 and 20 lg 2 rounded to 6. It therefore runs
    0,34 % high, which is far under the tenth of a decibel the sheet prints, so
    this example cannot tell the printed 0,3 of Equation (5) from lg 2.
    """
    got = room.spatial_decay_rate(
        oracle.IFA_LSA_01_234_LEVELS_DB[band], IFA_DISTANCES_M
    )
    assert got == pytest.approx(oracle.IFA_LSA_01_234_DECAY_DB[band], abs=0.05)


def test_a_constant_offset_leaves_the_decay_rate_alone() -> None:
    """Which is what lets Equation (5) be fed bare levels instead of D."""
    levels = oracle.IFA_LSA_01_234_LEVELS_DB[2000]
    plain = room.spatial_decay_rate(levels, IFA_DISTANCES_M)
    shifted = room.spatial_decay_rate(np.asarray(levels) - 95.0, IFA_DISTANCES_M)
    assert shifted == pytest.approx(plain, abs=1e-12)


def test_the_ifa_result_table_prints_one_difference_its_own_data_denies() -> None:
    """Tab. 4.5 prints Lp2 - Lp3 = 4,7 dB at 2 kHz; Tab. 4.4 gives 4,3 dB.

    The regression settles which cell is right. With the 71,0 dB Tab. 4.4
    prints at the third position, Equation (5) gives the 4,3 dB Tab. 4.5 prints
    for the decay rate; with the 70,6 dB the printed difference would need, it
    gives 4,4 dB and contradicts it. Eleven of the twelve difference cells
    reproduce, so the defect is that one cell and it touches nothing else.
    """
    want = oracle.IFA_LSA_01_234_DECAY_DB[2000]
    levels = oracle.IFA_LSA_01_234_LEVELS_DB[2000]
    printed = room.spatial_decay_rate(levels, IFA_DISTANCES_M)
    implied = list(levels)
    implied[2] = implied[1] - oracle.IFA_LSA_01_234_DIFFERENCES_DB["Lp2 - Lp3"][2]
    assert printed == pytest.approx(want, abs=0.05)
    assert room.spatial_decay_rate(implied, IFA_DISTANCES_M) == pytest.approx(
        4.355, abs=0.005
    )


# ---------------------------------------------------------------------------
# W. Probst, BAuA Schriftenreihe Fb 1083, 2006
# ---------------------------------------------------------------------------
#
# "Gestaltung laermarmer Fertigungsstaetten in metallverarbeitenden Betrieben",
# Forschung Fb 1083, Dortmund/Berlin/Dresden 2006. Anh. 1 prints one table per
# surveyed workroom, headed "Streukoerperberechnung nach VDI 3760, 1996"; in
# this copy the PDF page number equals the printed folio. The fitting density
# is the quantity a category 2a or 2b prediction of ISO 11690-3 takes instead
# of the fittings themselves, which is why it is anchored beside the curve it
# feeds.


@pytest.mark.parametrize("table", list(oracle.PROBST_ROOMS))
def test_the_probst_fitting_densities_reproduce(table: str) -> None:
    """q = S/(4V) against an independent VDI 3760 tool, from printed S and V.

    The density is printed to three decimals, which at these magnitudes is two
    significant figures, so what this pins is the form of the quotient and the
    factor 4 rather than a tight tolerance.
    """
    room_data, _fittings, surface_m2, printed = oracle.PROBST_ROOMS[table]
    got = room.fitting_density(surface_area_m2=surface_m2, volume_m3=room_data[3])
    assert got == pytest.approx(printed, abs=0.0005)


@pytest.mark.parametrize("table", list(oracle.PROBST_ROOMS))
def test_the_probst_fitting_surfaces_are_the_envelope_without_the_base(
    table: str,
) -> None:
    """Which surface rule the report summed is nowhere printed on those pages.

    It was read off the cumulative column, and the enveloping surface without
    the base area reproduces every one of them, including the mixed geometry of
    Tab. 3. This test says so out loud, so that the inference is visible rather
    than buried in the number the density row consumes. The printed volume is
    the product of the printed dimensions in all four rooms.
    """
    room_data, fittings, surface_m2, _printed = oracle.PROBST_ROOMS[table]
    length_m, breadth_m, height_m, volume_m3 = room_data
    assert length_m * breadth_m * height_m == pytest.approx(volume_m3)
    envelope = sum(
        count * (2.0 * long_m * tall_m + 2.0 * wide_m * tall_m + long_m * wide_m)
        for count, long_m, wide_m, tall_m in fittings
    )
    assert envelope == pytest.approx(surface_m2)


# ---------------------------------------------------------------------------
# The three conditions of SpatialDecayWarning (5.1.4, 5.3.2, 6.4.3).
# ---------------------------------------------------------------------------


def test_a_clear_background_says_nothing() -> None:
    """The one case 5.1.4 asks nothing of: 10 dB over the background."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        check = room.check_background_margin([80.0, 75.0], [70.0, 60.0])
    assert check.satisfied
    assert not check.needs_correction.any()
    assert not check.unusable.any()
    assert check.margins_db == pytest.approx([10.0, 15.0])


def test_a_margin_in_the_correction_window_asks_for_iso_3744() -> None:
    """Between 6 dB and 10 dB the clause corrects rather than refuses."""
    with pytest.warns(room.SpatialDecayWarning, match="5.1.4"):
        check = room.check_background_margin([80.0], [72.0])
    assert not check.satisfied
    assert check.needs_correction.tolist() == [True]
    assert check.unusable.tolist() == [False]


def test_a_margin_of_six_decibels_is_not_corrected_at_all() -> None:
    """At 6 dB the clause stops offering the correction, so the point is lost."""
    with pytest.warns(room.SpatialDecayWarning, match="offers no correction"):
        check = room.check_background_margin([80.0, 80.0], [74.0, 60.0])
    assert check.unusable.tolist() == [True, False]
    assert check.needs_correction.tolist() == [False, False]


def test_one_background_stands_for_every_position() -> None:
    """A single background level is the shape a quiet room is reported in."""
    with pytest.warns(room.SpatialDecayWarning):
        check = room.check_background_margin([80.0, 70.0, 66.0], 60.0)
    assert check.margins_db == pytest.approx([20.0, 10.0, 6.0])
    assert check.unusable.tolist() == [False, False, True]


def test_a_background_that_does_not_match_the_positions_is_refused() -> None:
    with pytest.raises(ValueError, match="position for position"):
        room.check_background_margin([80.0, 75.0], [70.0, 60.0, 50.0])


def test_two_positions_are_a_line_and_not_a_regression() -> None:
    """The count 5.3.2 calls a minimum, met exactly, leaves nothing to spare."""
    with pytest.warns(room.SpatialDecayWarning, match="line through them"):
        rate = room.spatial_decay_rate([-20.0, -26.0], [5.0, 10.0])
    assert rate == pytest.approx(
        -DECADE_TO_DOUBLING * (-6.0 / np.log10(2.0)), rel=1e-12
    )


def test_three_positions_are_a_regression_and_say_nothing() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        room.spatial_decay_rate([-20.0, -23.0, -26.0], [5.0, 7.0, 10.0])


def test_reading_the_line_past_the_last_position_says_so() -> None:
    """6.4.3 reads the far region at 30 m, which a path may never reach."""
    values = [-20.0, -23.0, -26.0]
    distances = [5.0, 10.0, 24.0]
    with pytest.warns(room.SpatialDecayWarning, match="extrapolation"):
        room.level_excess_at(values, distances, EVALUATION_DISTANCES_M["far"])


def test_reading_the_line_inside_the_measured_range_says_nothing() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        room.level_excess_at(
            [-20.0, -23.0, -26.0], [5.0, 10.0, 24.0], EVALUATION_DISTANCES_M["middle"]
        )


def test_the_annex_c_middle_region_raises_none_of_the_three() -> None:
    """The worked example is what a measurement that meets the clauses looks like."""
    keep = _select(*oracle.ANNEX_C_RANGES_M["middle"])
    values, distances = _raw(1000)[keep], DISTANCES_M[keep]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        room.spatial_decay_rate(values, distances)
        room.level_excess_at(values, distances, EVALUATION_DISTANCES_M["middle"])
