#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for spatial sound distribution curves (ISO 14257:2001).

The oracle is Annex C, a measurement in a 83 m by 32 m by 11 m shipyard hall
with eleven microphone positions from 2 m to 48 m. The annex prints the source
power (Table C.2), its free-field-over-a-reflecting-plane curve (Table C.3), the
levels measured in the room (Table C.4), the two sound distribution curves
(Tables C.5 and C.6) and the four result tables (C.7 to C.10), which is enough
to check Equations (1), (2), (4), (5), (6), (7), (B.1) and (B.4) against printed
numbers rather than against themselves.
"""

from __future__ import annotations

import numpy as np
import pytest

from phonometry import room
from phonometry.room.spatial_decay import (
    DECADE_TO_DOUBLING,
    EVALUATION_DISTANCES_M,
    ISO14257_REFERENCE_DISTANCE_M,
    NORMALIZED_OFFSET_DB,
    PINK_NOISE_WEIGHTS_DB,
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
