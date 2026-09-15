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
"""

from __future__ import annotations

import numpy as np
import pytest

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

#: Table C.1: where the eleven microphones stood, in metres.
DISTANCES_M = np.array([2, 3, 4, 5, 6, 8, 12, 16, 24, 32, 48], dtype=float)

#: Table C.2: the sound power level of the source, in decibels.
SOURCE_POWER_DB = {
    125: 97.6,
    250: 98.6,
    500: 102.2,
    1000: 110.8,
    2000: 111.2,
    4000: 107.4,
}

#: Table C.4: the levels measured in the room, in decibels.
ROOM_LEVELS_DB = {
    125: [85.7, 82.5, 80.8, 78.3, 77.1, 75.4, 73.7, 71.3, 70.4, 67.3, 65.7],
    250: [84.9, 81.9, 79.6, 77.8, 77.9, 74.3, 72.1, 70.3, 69.8, 65.0, 63.5],
    500: [89.8, 85.7, 83.6, 81.8, 80.5, 78.8, 76.8, 76.3, 72.0, 70.5, 69.1],
    1000: [98.9, 95.1, 93.0, 92.0, 91.0, 87.9, 85.8, 83.5, 81.5, 77.0, 75.6],
    2000: [99.7, 96.0, 93.5, 92.2, 91.0, 89.6, 86.6, 85.0, 81.1, 79.4, 76.7],
    4000: [93.8, 91.2, 88.3, 86.8, 85.7, 84.3, 80.4, 78.1, 74.9, 72.5, 70.5],
}

#: Table C.3: the same source measured in a free field over a reflecting
#: plane, in decibels.
FREE_FIELD_LEVELS_DB = {
    125: [83.4, 79.8, 76.9, 74.9, 73.2, 70.7, 67.3, 65.1, 61.5, 59.1, 55.6],
    250: [84.8, 80.9, 78.8, 76.4, 75.1, 72.5, 69.1, 66.6, 62.8, 60.5, 56.5],
    500: [89.7, 85.5, 83.2, 81.4, 80.0, 77.5, 74.1, 71.2, 67.4, 65.3, 60.4],
    1000: [98.8, 94.7, 92.3, 90.3, 88.7, 86.1, 82.6, 79.8, 75.7, 73.7, 67.8],
    2000: [99.2, 94.8, 92.2, 90.1, 88.6, 85.9, 82.6, 80.1, 75.3, 73.4, 65.7],
    4000: [92.8, 90.2, 87.3, 85.0, 83.2, 80.4, 76.8, 75.2, 71.0, 68.0, 57.3],
}

#: Table C.6: the curve after the Annex B correction, in decibels.
CORRECTED_DB = {
    125: [-11.8, -14.9, -16.5, -19.0, -20.1, -21.9, -23.7, -26.2, -27.1, -30.2, -31.9],
    250: [-13.9, -16.5, -19.2, -20.7, -20.7, -24.3, -26.5, -28.3, -28.7, -33.6, -35.0],
    500: [-13.9, -17.3, -19.6, -21.4, -22.8, -24.4, -26.1, -26.2, -30.4, -32.0, -33.1],
    1000: [-13.8, -16.9, -19.1, -19.8, -20.6, -23.8, -25.6, -27.7, -29.4, -34.2, -34.9],
    2000: [-13.3, -16.1, -18.4, -19.5, -20.7, -21.9, -25.0, -26.5, -30.0, -31.9, -34.0],
    4000: [-13.1, -16.4, -19.0, -20.3, -21.3, -22.7, -26.5, -29.2, -32.2, -34.4, -35.8],
}

#: Table C.6, last column: the same curve for A-weighted pink noise.
CORRECTED_NORMALIZED_DB = [
    -13.4,
    -16.5,
    -18.9,
    -20.0,
    -21.1,
    -22.8,
    -25.7,
    -27.5,
    -30.4,
    -33.1,
    -34.6,
]

#: 6.2 of the example: the boundaries the annex used, in metres.
EXAMPLE_RANGES_M = {"near": (2.0, 5.0), "middle": (5.0, 24.0), "far": (24.0, 48.0)}

#: Table C.7: the printed rate of spatial decay, in decibels per doubling.
PRINTED_DECAY_DB = {
    "near": {125: 5.2, 250: 5.2, 500: 5.7, 1000: 4.6, 2000: 4.8, 4000: 5.5},
    "middle": {125: 3.7, 250: 4.0, 500: 3.5, 1000: 4.4, 2000: 4.5, 4000: 5.4},
    "far": {125: 4.6, 250: 6.0, 500: 2.6, 1000: 5.2, 2000: 4.0, 4000: 3.6},
}

#: Table C.9: the printed excess of sound pressure level, in decibels.
PRINTED_EXCESS_DB = {
    "near": {125: 5.6, 250: 3.8, 500: 4.3, 1000: 5.2, 2000: 5.4, 4000: 4.0},
    "middle": {125: 8.1, 250: 6.3, 500: 6.9, 1000: 7.3, 2000: 7.8, 4000: 5.6},
    "far": {125: 11.5, 250: 8.6, 500: 9.8, 1000: 8.3, 2000: 9.4, 4000: 6.6},
}

#: Tables C.8 and C.10: the same two quantities for A-weighted pink noise.
PRINTED_NORMALIZED_DECAY_DB = {"near": 5.1, "middle": 4.6, "far": 4.1}
PRINTED_NORMALIZED_EXCESS_DB = {"near": 4.8, "middle": 7.0, "far": 8.5}


def _raw(band: int) -> np.ndarray:
    """The uncorrected curve of Table C.5, from Equation (1)."""
    return room.sound_distribution_value(ROOM_LEVELS_DB[band], SOURCE_POWER_DB[band])


def _corrected(band: int) -> np.ndarray:
    """The Annex B corrected curve of Table C.6."""
    measured = room.sound_distribution_value(
        FREE_FIELD_LEVELS_DB[band], SOURCE_POWER_DB[band]
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
    assert np.allclose(got, CORRECTED_DB[band], atol=0.1)


def test_the_normalized_curve_reproduces_the_last_column_of_table_c6() -> None:
    corrected = {band: _corrected(band) for band in SOURCE_POWER_DB}
    got = [
        room.normalized_distribution_value([corrected[b][i] for b in SOURCE_POWER_DB])
        for i in range(DISTANCES_M.size)
    ]
    assert np.allclose(got, CORRECTED_NORMALIZED_DB, atol=0.1)


@pytest.mark.parametrize("region", ["near", "middle", "far"])
@pytest.mark.parametrize("band", [125, 250, 500, 1000, 2000, 4000])
def test_the_decay_rate_reproduces_table_c7(region: str, band: int) -> None:
    low, high = EXAMPLE_RANGES_M[region]
    keep = _select(low, high)
    got = room.spatial_decay_rate(_corrected(band)[keep], DISTANCES_M[keep])
    assert got == pytest.approx(PRINTED_DECAY_DB[region][band], abs=0.06)


@pytest.mark.parametrize("region", ["near", "middle", "far"])
@pytest.mark.parametrize("band", [125, 250, 500, 1000, 2000, 4000])
def test_the_excess_reproduces_table_c9(region: str, band: int) -> None:
    low, high = EXAMPLE_RANGES_M[region]
    keep = _select(low, high)
    got = room.mean_level_excess(_raw(band)[keep], DISTANCES_M[keep])
    assert got == pytest.approx(PRINTED_EXCESS_DB[region][band], abs=0.07)


@pytest.mark.parametrize("region", ["near", "middle", "far"])
def test_the_normalized_results_reproduce_tables_c8_and_c10(region: str) -> None:
    low, high = EXAMPLE_RANGES_M[region]
    keep = _select(low, high)
    corrected = {band: _corrected(band) for band in SOURCE_POWER_DB}
    raw = {band: _raw(band) for band in SOURCE_POWER_DB}
    norm_corrected = np.array(
        [
            room.normalized_distribution_value(
                [corrected[b][i] for b in SOURCE_POWER_DB]
            )
            for i in range(DISTANCES_M.size)
        ]
    )
    norm_raw = np.array(
        [
            room.normalized_distribution_value([raw[b][i] for b in SOURCE_POWER_DB])
            for i in range(DISTANCES_M.size)
        ]
    )
    decay = room.spatial_decay_rate(norm_corrected[keep], DISTANCES_M[keep])
    excess = room.mean_level_excess(norm_raw[keep], DISTANCES_M[keep])
    assert decay == pytest.approx(PRINTED_NORMALIZED_DECAY_DB[region], abs=0.06)
    assert excess == pytest.approx(PRINTED_NORMALIZED_EXCESS_DB[region], abs=0.11)


def test_the_annex_corrects_the_decay_but_not_the_excess() -> None:
    """The inconsistency Annex C leaves behind, pinned so it cannot drift.

    C.1 says the experimental reference curve "is known and used for
    correcting the values measured in the workroom", and Table C.7 needs that
    correction: without it the middle-range decay at 1 kHz comes out 4,7 dB
    where the annex prints 4,4. Table C.9 needs the opposite: with the
    correction the same range at 1 kHz gives 6,7 dB where the annex prints 7,3,
    and without it 7,3. See the errata registry.
    """
    keep = _select(*EXAMPLE_RANGES_M["middle"])
    raw, corrected = _raw(1000)[keep], _corrected(1000)[keep]
    distances = DISTANCES_M[keep]
    assert room.spatial_decay_rate(corrected, distances) == pytest.approx(4.4, abs=0.05)
    assert room.spatial_decay_rate(raw, distances) == pytest.approx(4.7, abs=0.05)
    assert room.mean_level_excess(raw, distances) == pytest.approx(7.3, abs=0.05)
    assert room.mean_level_excess(corrected, distances) == pytest.approx(6.7, abs=0.05)


def test_the_table_one_weights_are_the_printed_ones() -> None:
    assert PINK_NOISE_WEIGHTS_DB == {
        125.0: -16.1,
        250.0: -8.6,
        500.0: -3.2,
        1000.0: 0.0,
        2000.0: 1.2,
        4000.0: 1.0,
    }
    assert NORMALIZED_OFFSET_DB == 6.2


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
    keep = _select(*EXAMPLE_RANGES_M["middle"])
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
    keep = _select(*EXAMPLE_RANGES_M["middle"])
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

    keep = _select(*EXAMPLE_RANGES_M["middle"])
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

    keep = _select(*EXAMPLE_RANGES_M["middle"])
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
    assert 4.4 <= MAX_DIRECTIVITY_INDEX_DB
    assert 6.5 <= ADJACENT_BAND_LIMIT_DB


def test_the_a_weighted_source_power_reproduces_table_c2() -> None:
    """Table C.2 on printed folio 18 prints 115,7 dB in its last column.

    Equation (4) is the energy sum under the Table 1 weights less 6,2 dB, so
    adding the offset back leaves the plain A-weighted total. This is the one
    printed figure of Annex C that the Table C.6 chain never touches.
    """
    total = (
        room.normalized_distribution_value(list(SOURCE_POWER_DB.values()))
        + NORMALIZED_OFFSET_DB
    )
    assert total == pytest.approx(115.7, abs=0.05)


# ---------------------------------------------------------------------------
# Equation (8) against Tables C.11 and C.12
# ---------------------------------------------------------------------------

#: Table C.11: the excess read off the fitted line at the conventional distance
#: of each region, in decibels, by nominal octave centre in hertz.
PRINTED_EXCESS_AT_DB = {
    "near": {125: 6.2, 250: 4.0, 500: 4.4, 1000: 5.2, 2000: 5.3, 4000: 3.9},
    "middle": {125: 7.8, 250: 5.4, 500: 6.4, 1000: 6.9, 2000: 7.7, 4000: 5.8},
    "far": {125: 10.6, 250: 7.4, 500: 9.3, 1000: 7.2, 2000: 9.2, 4000: 6.1},
}

#: Table C.12: the same three figures for A-weighted pink noise, in decibels.
PRINTED_EXCESS_AT_NORMALIZED_DB = {"near": 4.8, "middle": 6.8, "far": 8.0}

#: Table C.5 on printed folio 21 (PDF page 31): the uncorrected curve
#: D = L_p - L_W as printed, in decibels, by nominal octave centre in hertz.
PRINTED_D_TABLE_C5 = {
    125: [-11.9, -15.1, -16.8, -19.3, -20.5, -22.2, -23.9, -26.3, -27.2, -30.3, -31.9],
    250: [-13.7, -16.7, -19.0, -20.8, -20.7, -24.3, -26.5, -28.3, -28.8, -33.6, -35.1],
    500: [-12.4, -16.5, -18.6, -20.4, -21.7, -23.4, -25.4, -25.9, -30.2, -31.7, -33.1],
    1000: [-11.9, -15.7, -17.8, -18.8, -19.8, -22.9, -25.0, -27.3, -29.3, -33.8, -35.2],
    2000: [-11.5, -15.2, -17.7, -19.0, -20.2, -21.6, -24.6, -26.2, -30.1, -31.8, -34.5],
    4000: [-13.6, -16.2, -19.1, -20.6, -21.7, -23.1, -27.0, -29.3, -32.5, -34.9, -36.9],
}


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
    for band, printed in PRINTED_D_TABLE_C5.items():
        difference = np.asarray(ROOM_LEVELS_DB[band]) - SOURCE_POWER_DB[band]
        assert difference == pytest.approx(printed, abs=1e-9), band
    band_departures = []
    for region, row in PRINTED_EXCESS_AT_DB.items():
        keep = _select(*EXAMPLE_RANGES_M[region])
        for band, want in row.items():
            got = room.level_excess_at(
                np.asarray(PRINTED_D_TABLE_C5[band])[keep],
                DISTANCES_M[keep],
                EVALUATION_DISTANCES_M[region],
            )
            band_departures.append(got - want)
    assert sum(abs(value) > 0.05 for value in band_departures) == 15
    assert min(band_departures) == pytest.approx(-0.408, abs=0.005)
    assert max(band_departures) == pytest.approx(1.546, abs=0.005)
    normalized = np.asarray(CORRECTED_NORMALIZED_DB)
    weighted_departures = []
    for region, want in PRINTED_EXCESS_AT_NORMALIZED_DB.items():
        keep = _select(*EXAMPLE_RANGES_M[region])
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

#: The seven columns Tableau 2 and the Figure 7 summary are both printed in.
#: The last is the total the instrument printed and not Equation (4) over the
#: other six, which runs 0,02 dB to 0,57 dB above it.
SUVA_COLUMNS = ("125 Hz", "250 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz", "total")

#: Tableau 2: the sound distribution curve, printed as "SAK en dB", which is
#: D = Lp - Lw of Equation (1), in decibels. One entry per printed row: the
#: distance in metres against the seven columns above.
SUVA_CURVE_DB: dict[float, tuple[float, ...]] = {
    1.0: (-9.9, -10.2, -8.0, -10.5, -8.1, -9.1, -8.9),
    2.0: (-15.0, -11.7, -13.1, -15.0, -12.2, -11.3, -13.0),
    3.0: (-21.7, -12.1, -15.0, -16.2, -12.6, -14.0, -14.2),
    4.0: (-19.2, -14.6, -15.4, -16.3, -13.3, -15.1, -14.9),
    5.0: (-19.4, -15.9, -15.9, -17.9, -13.8, -15.3, -15.6),
    6.0: (-20.5, -16.1, -14.9, -17.8, -14.1, -16.0, -15.6),
    7.0: (-20.0, -15.3, -16.4, -18.3, -15.3, -16.1, -16.4),
    8.0: (-19.5, -16.4, -17.3, -19.1, -15.5, -16.7, -17.0),
    9.0: (-20.3, -15.3, -18.2, -19.6, -15.8, -16.9, -17.4),
    10.0: (-22.1, -17.4, -18.1, -19.7, -16.0, -17.0, -17.6),
    12.0: (-21.0, -16.3, -18.9, -19.9, -16.7, -18.3, -18.2),
    14.0: (-23.3, -18.1, -19.7, -20.5, -16.3, -18.3, -18.4),
    16.0: (-23.1, -18.0, -20.4, -20.3, -17.4, -19.0, -19.0),
    18.0: (-22.4, -19.2, -18.6, -20.6, -16.9, -19.3, -18.7),
    20.0: (-22.3, -17.8, -21.5, -22.7, -18.4, -20.5, -20.3),
    24.0: (-24.5, -21.4, -21.6, -23.6, -19.2, -21.6, -21.2),
    28.0: (-25.0, -20.3, -21.3, -24.2, -19.7, -22.6, -21.5),
    32.0: (-24.7, -22.6, -23.7, -24.4, -20.7, -23.4, -22.7),
    36.0: (-24.9, -22.9, -22.7, -24.7, -21.5, -23.9, -23.0),
    40.0: (-26.4, -24.4, -23.0, -25.5, -21.1, -24.4, -23.2),
    48.0: (-26.5, -25.1, -24.7, -25.7, -22.3, -25.3, -24.2),
}

#: The Figure 7 summary: the decay rate the survey's own analysis program read
#: off that curve, in decibels per distance doubling. The printed rows are
#: labelled "pres", "moyen" and "loin".
SUVA_DECAY_DB: dict[str, tuple[float, ...]] = {
    "near": (4.5, 2.3, 3.4, 3.0, 2.4, 2.9, 2.8),
    "middle": (2.2, 1.4, 3.1, 1.7, 2.0, 2.2, 2.1),
    "far": (2.6, 4.7, 2.9, 3.4, 3.4, 4.1, 3.5),
}

#: The same summary: the excess of sound pressure level, in decibels.
SUVA_EXCESS_DB: dict[str, tuple[float, ...]] = {
    "near": (1.7, 5.8, 5.0, 3.3, 6.3, 5.7, 5.1),
    "middle": (9.0, 13.5, 12.4, 10.8, 14.4, 13.0, 12.8),
    "far": (15.4, 18.5, 17.9, 16.1, 20.1, 17.5, 18.2),
}

#: 2.6.2: the three ranges, printed with both bounds, in metres. The path stops
#: at 48 m, so the far range is evaluated over 16 m to 48 m.
SUVA_RANGES_M = {"near": (1.0, 5.0), "middle": (5.0, 16.0), "far": (16.0, 64.0)}

#: 2.6.3: the radii the same page tells a surveyor to stand at, in metres.
SUVA_RADII_M = (
    1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 14.0, 16.0, 18.0,
    20.0, 24.0, 28.0, 32.0, 36.0, 40.0, 48.0, 56.0, 64.0,
)  # fmt: skip


def _suva_range(column: str, region: str) -> tuple[np.ndarray, np.ndarray]:
    """One printed column over one printed range, as values and distances."""
    index = SUVA_COLUMNS.index(column)
    low, high = SUVA_RANGES_M[region]
    radii = [radius for radius in SUVA_CURVE_DB if low <= radius <= high]
    values = [SUVA_CURVE_DB[radius][index] for radius in radii]
    return np.array(values, dtype=float), np.array(radii, dtype=float)


@pytest.mark.parametrize("region", ["near", "middle", "far"])
@pytest.mark.parametrize("column", SUVA_COLUMNS)
def test_the_suva_decay_rates_reproduce(column: str, region: str) -> None:
    """Equation (5) over a curve this project had no part in measuring.

    The tolerance is 0,06 dB rather than the 0,05 dB the printed tenth would
    suggest, for two of the 21 values: DL2 in the far range at 250 Hz and at
    2 kHz land 0,001 dB the wrong side of the rounding boundary. That is
    Equation (5) printing 0,3 where the survey's program used lg 2, which is
    the same 0,3 % the errata registry records.
    """
    want = SUVA_DECAY_DB[region][SUVA_COLUMNS.index(column)]
    got = room.spatial_decay_rate(*_suva_range(column, region))
    assert got == pytest.approx(want, abs=0.06)


@pytest.mark.parametrize("region", ["near", "middle", "far"])
@pytest.mark.parametrize("column", SUVA_COLUMNS)
def test_the_suva_excesses_reproduce(column: str, region: str) -> None:
    """Equations (6) and (7) over the same curve, every value to the tenth."""
    want = SUVA_EXCESS_DB[region][SUVA_COLUMNS.index(column)]
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
        - SUVA_EXCESS_DB[region][index]
        for region in SUVA_RANGES_M
        for index, column in enumerate(SUVA_COLUMNS)
    ]
    implied = FREE_FIELD_OFFSET_DB - float(np.mean(residuals))
    assert implied == pytest.approx(float(10.0 * np.log10(4.0 * np.pi)), abs=0.02)
    assert abs(implied - 8.0) > 2.0


@pytest.mark.parametrize("radius_m", SUVA_RADII_M)
def test_every_printed_radius_lands_in_a_range_that_admits_it(radius_m: float) -> None:
    """The survey prints the partition as numbers, which 6.2 never does.

    It prints the three ranges as closed intervals, so 5 m and 16 m are each
    named by two of them, and 6.2 writes "from 1 m to d1", "from d1 to d2" and
    "from d2" without saying which side owns a boundary. Neither page pins it,
    so what is checked is that every radius lands in a range that admits it.
    """
    admitted = [
        name for name, (low, high) in SUVA_RANGES_M.items() if low <= radius_m <= high
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

#: Tab. 4.4: the four positions of the path, in metres.
IFA_DISTANCES_M = np.array([0.75, 1.50, 3.00, 6.00])

#: Tab. 4.4: the sound pressure levels measured there, in decibels. They are
#: bare Lp rather than D = Lp - Lw, which Equation (5) does not mind, and the
#: sheet feeds its own printed formula the same bare levels for the same
#: reason.
IFA_LEVELS_DB = {
    "500 Hz": [79.2, 74.4, 70.2, 67.1],
    "1 kHz": [81.9, 77.1, 73.0, 69.8],
    "2 kHz": [80.4, 75.3, 71.0, 67.4],
    "4 kHz": [84.3, 78.5, 73.2, 69.3],
}

#: Tab. 4.5: the decay rate the sheet prints for each band, in decibels per
#: distance doubling, identical under its two printed methods.
IFA_DECAY_DB = {"500 Hz": 4.0, "1 kHz": 4.0, "2 kHz": 4.3, "4 kHz": 5.0}


@pytest.mark.parametrize("band", ["500 Hz", "1 kHz", "2 kHz", "4 kHz"])
def test_the_ifa_decay_rates_reproduce(band: str) -> None:
    """Equation (5) against a second worked example, from a second country.

    The sheet's own Equation (4.4) is not Equation (5) verbatim: it is that
    regression specialised to these four fixed distances, with the sum of the
    logarithms rounded to 1,306 and 20 lg 2 rounded to 6. It therefore runs
    0,34 % high, which is far under the tenth of a decibel the sheet prints, so
    this example cannot tell the printed 0,3 of Equation (5) from lg 2.
    """
    got = room.spatial_decay_rate(IFA_LEVELS_DB[band], IFA_DISTANCES_M)
    assert got == pytest.approx(IFA_DECAY_DB[band], abs=0.05)


def test_a_constant_offset_leaves_the_decay_rate_alone() -> None:
    """Which is what lets Equation (5) be fed bare levels instead of D."""
    levels = IFA_LEVELS_DB["2 kHz"]
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
    want = IFA_DECAY_DB["2 kHz"]
    printed = room.spatial_decay_rate(IFA_LEVELS_DB["2 kHz"], IFA_DISTANCES_M)
    implied = list(IFA_LEVELS_DB["2 kHz"])
    implied[2] = implied[1] - 4.7
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

#: Anh. 1: the room, the fittings and the density each table prints. The room
#: is its length, breadth and height in metres followed by the volume it prints
#: in cubic metres; each fitting is a count and three dimensions in metres; the
#: last two entries are the cumulative fitting surface in square metres and the
#: density in reciprocal metres.
PROBST_ROOMS = {
    "Tab. 3, folio 79": (
        (14.0, 20.0, 4.5, 1260.0),
        ((5, 4.0, 2.0, 2.0), (1, 5.0, 5.0, 5.0), (10, 0.3, 0.3, 3.0)),
        321.9,
        0.064,
    ),
    "Tab. 6, folio 82": (
        (14.0, 22.0, 6.0, 1848.0),
        ((2, 3.0, 1.0, 2.0), (3, 6.0, 1.0, 2.0)),
        140.0,
        0.019,
    ),
    "Tab. 13, folio 93": (
        (23.0, 20.0, 6.0, 2760.0),
        ((5, 4.0, 2.0, 2.0),),
        160.0,
        0.014,
    ),
    "Tab. 22, folio 105": (
        (18.0, 11.0, 3.5, 693.0),
        ((1, 4.0, 3.0, 3.0),),
        54.0,
        0.019,
    ),
}


@pytest.mark.parametrize("table", list(PROBST_ROOMS))
def test_the_probst_fitting_densities_reproduce(table: str) -> None:
    """q = S/(4V) against an independent VDI 3760 tool, from printed S and V.

    The density is printed to three decimals, which at these magnitudes is two
    significant figures, so what this pins is the form of the quotient and the
    factor 4 rather than a tight tolerance.
    """
    room_data, _fittings, surface_m2, printed = PROBST_ROOMS[table]
    got = room.fitting_density(surface_area_m2=surface_m2, volume_m3=room_data[3])
    assert got == pytest.approx(printed, abs=0.0005)


@pytest.mark.parametrize("table", list(PROBST_ROOMS))
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
    room_data, fittings, surface_m2, _printed = PROBST_ROOMS[table]
    length_m, breadth_m, height_m, volume_m3 = room_data
    assert length_m * breadth_m * height_m == pytest.approx(volume_m3)
    envelope = sum(
        count * (2.0 * long_m * tall_m + 2.0 * wide_m * tall_m + long_m * wide_m)
        for count, long_m, wide_m, tall_m in fittings
    )
    assert envelope == pytest.approx(surface_m2)
