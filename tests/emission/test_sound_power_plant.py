#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound power levels of multisource industrial plants: ISO 8297:1994.

Anchors, read on the printed pages of BS ISO 8297:1994 (PDF pages 9 to 16,
printed folios 1 to 8):

- Table 1 (folio 2): d/sqrt(Sp) 0,05 -> +3,0/-3,5 dB; 0,1 -> +/-2,5 dB;
  0,2 -> +2,0/-2,5 dB; 0,5 -> +1,5/-2,0 dB.
- Table 2 (folio 6): difference < 6 -> invalid; 6, 7, 8 -> 1 dB; 9, 10 ->
  0,5 dB; > 10 -> 0.
- Table 3 (folio 7): alpha 0, 0, 0, 0,001, 0,002, 0,005, 0,01, 0,026,
  0,046 dB/m in the octaves 31 (31,5) Hz to 8 kHz, at 15 degC and 70 %.
- 9.1.1 a) (folio 5): max(0,05 sqrt(Sp), 5 m) < d <= min(0,5 sqrt(Sp), 35 m);
  b) aspect angle <= 180 deg; c) Dm <= 2 d.
- 9.2 c) and NOTE 7: H = (1/n) sum hk; ten or more sources lower than 2 m
  may be taken at 1 m.
- 9.3 (folio 6): h = H + 0,025 sqrt(Sm), or 5 m, whichever is the greater.
- 10.1 to 10.9 (folios 7, 8): the energy mean; the cap Lp + 5 dB; dLS =
  10 lg((2 Sm + h l)/S0); dLF = lg(d/(4 sqrt(Sp))), with NOTE 11 putting it
  between -0,9 dB and -1,9 dB when 9.1 is met; dLM = 3 (1 - theta/90);
  dLalpha = 0,5 alpha sqrt(Sm); LW = Lp + dLS + dLF + dLM + dLalpha; LWA =
  10 lg sum 10^(0,1 (LWj + Cj)).

The ARP 866A coefficient of ISO 3891:1978 Annex A, which Table 3 cites and
the weather path evaluates, is checked against ISO 3891 Table 9 (70 %, 15 degC
column, PDF page 19, printed p. 16) as transcribed for the Doc 29 Appendix D
tests.
"""

from __future__ import annotations

import dataclasses
import math
import sys
import types
import warnings
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref

from phonometry import emission
from phonometry.emission import sound_power_plant as spp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "aircraft"))
from iso3891_tables_data import FREQUENCIES_HZ, TABLE_9, TEMPERATURES_C

OCTAVES = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
#: A 200 m by 120 m L-shaped plant area, and a rectangle round it 25 m out.
PLANT = np.array(
    [
        [0.0, 0.0],
        [200.0, 0.0],
        [200.0, 70.0],
        [140.0, 70.0],
        [140.0, 120.0],
        [0.0, 120.0],
    ]
)
CONTOUR = np.array([[-25.0, -25.0], [225.0, -25.0], [225.0, 145.0], [-25.0, 145.0]])


def _contour(**kwargs: object) -> spp.PlantMeasurementContour:
    return emission.plant_measurement_contour(
        PLANT, CONTOUR, characteristic_height_m=8.0, **kwargs
    )


def _levels(count: int, spread_db: float = 1.0) -> np.ndarray:
    base = np.array([80.0, 82.0, 81.0, 78.0, 75.0, 71.0, 65.0, 57.0])
    rng = np.random.default_rng(8297)
    return base + rng.uniform(-spread_db, spread_db, (count, OCTAVES.size))


# --------------------------------------------------------------------------- #
# Printed tables
# --------------------------------------------------------------------------- #


def test_table_3_is_transcribed_as_printed() -> None:
    assert dict(emission.PLANT_AIR_ABSORPTION_DB_PER_M) == dict(ref.ISO8297_TABLE_3)


def test_table_1_is_transcribed_as_printed() -> None:
    assert dict(emission.PLANT_METHOD_UNCERTAINTY_DB) == {
        ratio: (lower, upper) for ratio, lower, upper in ref.ISO8297_TABLE_1
    }


def test_table_2_is_transcribed_as_printed() -> None:
    assert dict(emission.PLANT_BACKGROUND_CORRECTION_DB) == dict(ref.ISO8297_TABLE_2)


@pytest.mark.parametrize(
    "table",
    [
        emission.PLANT_AIR_ABSORPTION_DB_PER_M,
        emission.PLANT_METHOD_UNCERTAINTY_DB,
        emission.PLANT_BACKGROUND_CORRECTION_DB,
    ],
)
def test_printed_tables_are_read_only(table: object) -> None:
    assert isinstance(table, types.MappingProxyType)
    with pytest.raises(TypeError, match="does not support item assignment"):
        table[1.0] = 0.0  # type: ignore[index]


# --------------------------------------------------------------------------- #
# Table 3 against the shared ISO 3891 transcription
# --------------------------------------------------------------------------- #


def test_air_absorption_without_weather_is_table_3() -> None:
    bands = [31.5, *OCTAVES.tolist()]
    alpha = emission.plant_air_absorption_db_per_m(bands)
    np.testing.assert_array_equal(
        alpha, [emission.PLANT_AIR_ABSORPTION_DB_PER_M[b] for b in bands]
    )


def test_weather_path_reproduces_iso_3891_table_9_at_15_degc() -> None:
    """ISO 3891 Table 9 (70 %), the 15 degC column, at the octave centres."""
    column = TEMPERATURES_C.index(15.0)
    printed = np.array(
        [TABLE_9[FREQUENCIES_HZ.index(f)][column] for f in OCTAVES], dtype=float
    )
    alpha = emission.plant_air_absorption_db_per_m(
        OCTAVES, temperature_c=15.0, relative_humidity_percent=70.0
    )
    np.testing.assert_array_equal(np.round(alpha * 100.0, 1), printed)


def test_table_3_meets_the_iso_3891_formula_in_five_of_its_eight_rows() -> None:
    """Table 3 says it is taken from ISO 3891 at 15 degC and 70 %: the formula
    agrees with it to the printed digit at 63 Hz and from 250 Hz to 2 kHz, and
    not at 125 Hz, 4 kHz or 8 kHz (see the module docstring).
    """
    alpha = emission.plant_air_absorption_db_per_m(
        OCTAVES, temperature_c=15.0, relative_humidity_percent=70.0
    )
    printed = np.array([emission.PLANT_AIR_ABSORPTION_DB_PER_M[b] for b in OCTAVES])
    agrees = np.isclose(np.round(alpha, 3), printed, rtol=0.0, atol=1e-12)
    np.testing.assert_array_equal(
        agrees, [True, False, True, True, True, True, False, False]
    )
    np.testing.assert_allclose(
        alpha[[1, 6, 7]], [0.000589, 0.02505, 0.06085], rtol=2e-3
    )


def test_weather_leaves_the_31_5_hz_band_at_zero() -> None:
    """ISO 3891 Table 2 starts at 50 Hz, so the 31,5 Hz octave keeps Table 3's 0."""
    alpha = emission.plant_air_absorption_db_per_m(
        [31.5, 63.0], temperature_c=-10.0, relative_humidity_percent=10.0
    )
    assert alpha[0] == pytest.approx(0.0, abs=0.0)
    assert alpha[1] > 0.0


def test_air_absorption_at_8_khz_in_moist_air_is_lower_at_30_than_at_0_degc() -> None:
    """ISO 3891 Table 11 (90 %) prints 9,5 dB/100 m at 0 degC and 5,2 at 30 degC."""
    cold = emission.plant_air_absorption_db_per_m(
        [8000.0], temperature_c=0.0, relative_humidity_percent=90.0
    )
    warm = emission.plant_air_absorption_db_per_m(
        [8000.0], temperature_c=30.0, relative_humidity_percent=90.0
    )
    assert warm[0] < cold[0]


def test_half_a_weather_is_refused() -> None:
    with pytest.raises(
        ValueError, match="'temperature_c' and 'relative_humidity_percent' go"
    ):
        emission.plant_air_absorption_db_per_m(OCTAVES, temperature_c=15.0)


def test_a_band_outside_the_method_is_refused() -> None:
    with pytest.raises(ValueError, match="'frequencies_hz' must name octave bands"):
        emission.plant_air_absorption_db_per_m([16.0])


def test_bands_out_of_order_are_refused() -> None:
    with pytest.raises(
        ValueError, match="'frequencies_hz' must name each octave band once"
    ):
        emission.plant_air_absorption_db_per_m([125.0, 63.0])


@pytest.mark.parametrize("frequency", [45.0, 80.0, 90.0, 5000.0])
def test_a_frequency_between_octaves_is_refused(frequency: float) -> None:
    """A one-third-octave centre is not read as the octave next to it."""
    with pytest.raises(ValueError, match="'frequencies_hz' must name octave bands"):
        emission.plant_air_absorption_db_per_m([frequency])


def test_exact_centres_name_the_nominal_bands() -> None:
    alpha = emission.plant_air_absorption_db_per_m([31.62, 62.5, 7943.0])
    np.testing.assert_array_equal(alpha, [0.0, 0.0, 0.046])


# --------------------------------------------------------------------------- #
# Tables 1 and 2 read between their rows
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("ratio", "expected"),
    [
        (0.05, (-3.5, 3.0)),
        (0.07, (-3.5, 3.0)),
        (0.1, (-2.5, 2.5)),
        (0.15, (-2.5, 2.5)),
        (0.2, (-2.5, 2.0)),
        (0.35, (-2.5, 2.0)),
        (0.5, (-2.0, 1.5)),
    ],
)
def test_uncertainty_takes_the_row_at_or_below_the_ratio(
    ratio: float, expected: tuple[float, float]
) -> None:
    assert emission.plant_method_uncertainty_db(ratio) == expected


@pytest.mark.parametrize("ratio", [0.049, 0.51])
def test_uncertainty_outside_table_1_is_refused(ratio: float) -> None:
    with pytest.raises(ValueError, match="Table 1 covers"):
        emission.plant_method_uncertainty_db(ratio)


@pytest.mark.parametrize(
    ("difference", "correction"),
    [
        (6.0, 1.0),
        (7.0, 1.0),
        (8.0, 1.0),
        (8.49, 1.0),
        (8.5, 0.5),
        (9.0, 0.5),
        (10.0, 0.5),
        (10.01, 0.0),
        (25.0, 0.0),
    ],
)
def test_background_correction_follows_table_2(
    difference: float, correction: float
) -> None:
    assert emission.plant_background_correction_db(difference) == correction


def test_background_correction_is_vectorised() -> None:
    out = emission.plant_background_correction_db([[6.0, 9.2], [12.0, 7.4]])
    np.testing.assert_array_equal(out, [[1.0, 0.5], [0.0, 1.0]])


def test_background_under_6_db_is_an_invalid_measurement() -> None:
    with pytest.raises(ValueError, match="Table 2 calls a measurement invalid"):
        emission.plant_background_correction_db([7.0, 5.99])


@pytest.mark.parametrize(
    ("operating", "background", "correction"),
    [
        (20.4, 14.4, 1.0),
        (64.1, 58.1, 1.0),
        (64.1, 55.6, 0.5),
        (64.4, 54.4, 0.5),
    ],
)
def test_background_correction_reads_decimal_readings_as_their_difference(
    operating: float, background: float, correction: float
) -> None:
    """Table 2 is read on the difference of two decimal readings, not on its
    last binary digits: 20,4 - 14,4 dB is 5,999 999 999 999 998 and 64,1 -
    58,1 dB 5,999 999 999 999 993 in binary, both the 6 dB of the first row;
    64,1 - 55,6 dB, 8,499 999 999 999 993, is the half that goes up to 9; and
    64,4 - 54,4 dB, 10,000 000 000 000 007, is the 10 dB row, not above it.
    """
    assert emission.plant_background_correction_db(operating - background) == (
        correction
    )


# --------------------------------------------------------------------------- #
# Clauses 9.1 to 9.3 on their own
# --------------------------------------------------------------------------- #


def test_characteristic_height_is_the_mean_source_height() -> None:
    assert emission.plant_characteristic_height_m([4.0, 10.0, 16.0]) == 10.0


def test_note_7_takes_ten_low_sources_at_one_metre() -> None:
    height = emission.plant_characteristic_height_m([20.0, 30.0], low_source_count=10)
    assert height == pytest.approx((20.0 + 30.0 + 10.0) / 12.0)


def test_note_7_needs_ten_sources() -> None:
    with pytest.raises(ValueError, match="NOTE 7"):
        emission.plant_characteristic_height_m([20.0], low_source_count=9)


def test_characteristic_height_needs_a_source() -> None:
    with pytest.raises(ValueError, match="at least one noise source"):
        emission.plant_characteristic_height_m([])


@pytest.mark.parametrize(
    ("height", "area", "expected"),
    [
        (10.0, 40000.0, 10.0 + 0.025 * 200.0),
        (1.0, 10000.0, 5.0),
        (4.0, 1600.0, 5.0),
    ],
)
def test_microphone_height_of_9_3(height: float, area: float, expected: float) -> None:
    assert emission.plant_microphone_height_m(height, area) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("area", "expected"),
    [
        (400.0, (5.0, 10.0)),
        (10000.0, (5.0, 35.0)),
        (40000.0, (10.0, 35.0)),
        (4900.0, (5.0, 35.0)),
    ],
)
def test_mean_distance_window_of_9_1_1_a(
    area: float, expected: tuple[float, float]
) -> None:
    assert emission.plant_mean_distance_limits_m(area) == pytest.approx(expected)


def test_mean_distance_window_is_empty_below_100_m2() -> None:
    lower, upper = emission.plant_mean_distance_limits_m(64.0)
    assert lower > upper


@pytest.mark.parametrize(("area", "bound"), [(100.0, 5.0), (490000.0, 35.0)])
def test_mean_distance_window_is_empty_at_its_two_ends(
    area: float, bound: float
) -> None:
    """The lower bound of 9.1.1 a) is strict: at 100 m2 and 490 000 m2 the
    window is (5, 5] and (35, 35], which no distance meets.
    """
    assert emission.plant_mean_distance_limits_m(area) == pytest.approx((bound, bound))


def test_steady_reading_is_the_arithmetic_mean() -> None:
    assert emission.plant_steady_reading_db(72.0, 68.4) == pytest.approx(70.2)


@pytest.mark.parametrize(("maximum", "minimum"), [(75.0, 70.0), (64.1, 59.1)])
def test_a_swing_of_5_db_is_not_steady(maximum: float, minimum: float) -> None:
    """9.5.2 calls a noise steady below 5 dB; 64,1 - 59,1 dB is a swing of
    5 dB, though 4,999 999 999 999 993 in binary.
    """
    with pytest.raises(ValueError, match="integrating instrument"):
        emission.plant_steady_reading_db(maximum, minimum)


# --------------------------------------------------------------------------- #
# The contour
# --------------------------------------------------------------------------- #


def test_contour_areas_and_length() -> None:
    contour = _contour()
    assert contour.plant_area_m2 == pytest.approx(200.0 * 120.0 - 60.0 * 50.0)
    assert contour.measurement_area_m2 == pytest.approx(250.0 * 170.0)
    assert contour.contour_length_m == pytest.approx(2.0 * (250.0 + 170.0))


def test_default_layout_is_the_fewest_positions_9_1_1_c_allows() -> None:
    contour = _contour()
    assert contour.position_spacing_m <= 2.0 * contour.mean_distance_m
    fewer = _contour(position_count=contour.position_count - 1)
    assert fewer.position_spacing_m > 2.0 * fewer.mean_distance_m


def test_positions_are_equidistant_along_the_contour() -> None:
    contour = _contour(position_count=16)
    assert contour.positions_m.shape == (16, 2)
    np.testing.assert_allclose(contour.positions_m[0], CONTOUR[0])
    # 16 positions round 840 m of rectangle: one every 52,5 m.
    np.testing.assert_allclose(contour.positions_m[1], [27.5, -25.0])
    assert contour.position_spacing_m == pytest.approx(52.5)


def test_distances_are_to_the_nearest_point_of_the_perimeter() -> None:
    contour = _contour(position_count=16)
    # Position 1 at (27,5; -25) is straight below the bottom edge.
    assert contour.distances_m[1] == pytest.approx(25.0)
    np.testing.assert_allclose(contour.nearest_perimeter_points_m[1], [27.5, 0.0])
    # Position 0 at the corner (-25; -25) is nearest the plant's corner (0; 0).
    assert contour.distances_m[0] == pytest.approx(25.0 * math.sqrt(2.0))
    assert contour.mean_distance_m == pytest.approx(float(np.mean(contour.distances_m)))


def test_microphones_point_into_the_contour_at_right_angles() -> None:
    contour = _contour(position_count=16)
    np.testing.assert_allclose(contour.microphone_directions[1], [0.0, 1.0], atol=1e-12)
    corner = contour.microphone_directions[0]
    np.testing.assert_allclose(corner, [math.sqrt(0.5), math.sqrt(0.5)], atol=1e-12)


def test_microphone_direction_does_not_depend_on_the_winding() -> None:
    forward = _contour(position_count=16)
    backward = emission.plant_measurement_contour(
        PLANT, CONTOUR[::-1], characteristic_height_m=8.0, position_count=16
    )
    inward = backward.plant_centre_m - backward.positions_m
    dots = np.sum(inward * backward.microphone_directions, axis=1)
    assert np.all(dots > 0.0)
    assert forward.mean_distance_m > 0.0


def test_aspect_angle_below_a_square_side() -> None:
    """From (0,5; -d) under a unit square, the plant subtends 180 - 2 atan(2d)."""
    square = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    for depth in (0.1, 0.5, 2.0):
        angle = spp._aspect_angle_deg(np.array([0.5, -depth]), square)
        assert angle == pytest.approx(
            180.0 - 2.0 * math.degrees(math.atan(2.0 * depth))
        )


def test_aspect_angle_inside_a_notch_exceeds_180_degrees() -> None:
    u_shape = np.array(
        [[0, 0], [30, 0], [30, 30], [20, 30], [20, 10], [10, 10], [10, 30], [0, 30]],
        dtype=float,
    )
    assert spp._aspect_angle_deg(np.array([15.0, 25.0]), u_shape) > 180.0


def test_contour_into_the_notch_of_a_plant_fails_9_1_1_b() -> None:
    u_shape = np.array(
        [[0, 0], [60, 0], [60, 60], [40, 60], [40, 20], [20, 20], [20, 60], [0, 60]],
        dtype=float,
    )
    # The contour dips into the notch as a narrow V, whose tip sees the plant
    # on three sides.
    hugging = np.array(
        [[-10, -10], [70, -10], [70, 70], [31, 70], [30, 40], [29, 70], [-10, 70]],
        dtype=float,
    )
    contour = emission.plant_measurement_contour(
        u_shape, hugging, characteristic_height_m=5.0, position_count=24
    )
    check = emission.check_plant_measurement(contour)
    row = check.requirement("aspect_angle")
    assert not row.holds
    assert row.value > 180.0
    outside = emission.plant_measurement_contour(
        u_shape,
        [[-10, -10], [70, -10], [70, 70], [-10, 70]],
        characteristic_height_m=5.0,
        position_count=24,
    )
    assert emission.check_plant_measurement(outside).requirement("aspect_angle").holds


@pytest.mark.parametrize("count", [3, 4, 5, 7, 12])
@pytest.mark.parametrize(("side", "gap"), [(40.0, 10.0), (100.0, 5.0)])
def test_largest_aspect_angle_is_the_closed_form_at_mid_side(
    side: float, gap: float, count: int
) -> None:
    """A square plant of side L inside a square contour a distance d out is
    seen at most at 2 atan(L/(2 d)), from the middle of each side of the
    contour, whatever the positions are.
    """
    plant = [[0.0, 0.0], [side, 0.0], [side, side], [0.0, side]]
    far = side + gap
    ring = [[-gap, -gap], [far, -gap], [far, far], [-gap, far]]
    contour = emission.plant_measurement_contour(
        plant, ring, characteristic_height_m=5.0, position_count=count
    )
    expected = 2.0 * math.degrees(math.atan(side / (2.0 * gap)))
    assert contour.largest_aspect_angle_deg == pytest.approx(expected, rel=1e-12)
    assert not contour.enters_convex_hull
    row = emission.check_plant_measurement(contour).requirement("aspect_angle")
    assert row.holds
    assert row.value == pytest.approx(expected, rel=1e-12)


def test_largest_aspect_angle_is_not_below_a_dense_walk() -> None:
    """On the L-shaped plant, no point of a dense walk round the contour sees
    the plant wider than the value reported, which is reached (to 1e-6 deg).
    """
    contour = _contour()
    points, _normals = spp._walk(contour.contour_m, 20000)
    walked = max(spp._aspect_angle_deg(p, contour.plant_outline_m) for p in points)
    assert walked <= contour.largest_aspect_angle_deg + 1e-9
    assert walked == pytest.approx(contour.largest_aspect_angle_deg, abs=1e-6)


def test_the_contour_keeps_copies_of_the_callers_arrays() -> None:
    plant = PLANT.copy()
    ring = np.vstack([CONTOUR, CONTOUR[:1]])
    contour = emission.plant_measurement_contour(
        plant, ring, characteristic_height_m=8.0
    )
    area, mean = contour.measurement_area_m2, contour.mean_distance_m
    ring *= 0.5
    plant += 1.0
    assert contour.measurement_area_m2 == pytest.approx(area)
    assert contour.mean_distance_m == pytest.approx(mean)
    np.testing.assert_array_equal(contour.contour_m, CONTOUR)


@pytest.mark.parametrize(
    "name",
    [
        "plant_outline_m",
        "contour_m",
        "positions_m",
        "microphone_directions",
        "distances_m",
        "aspect_angles_deg",
        "measured",
    ],
)
def test_the_arrays_of_a_contour_are_read_only(name: str) -> None:
    array = getattr(_contour(), name)
    assert not array.flags.writeable


@pytest.mark.parametrize(
    ("side", "offset", "radius", "count"),
    [(1.0, 4.0, 20.0, 4), (10.0, 6.0, 30.0, 4)],
)
def test_default_layout_meets_the_exhaustive_search_off_centre(
    side: float, offset: float, radius: float, count: int
) -> None:
    """A plant off the centre of a circular contour: the fewest positions
    9.1.1 c) allows, found by counting up from three, is what the default
    layout returns, whatever lower bound the search starts from.
    """
    angles = np.linspace(0.0, 2.0 * np.pi, 64, endpoint=False)
    ring = np.c_[radius * np.cos(angles), radius * np.sin(angles)]
    low = offset - 0.5 * side
    plant = [
        [low, -0.5 * side],
        [low + side, -0.5 * side],
        [low + side, 0.5 * side],
        [low, 0.5 * side],
    ]
    layout = emission.plant_measurement_contour(
        plant, ring, characteristic_height_m=5.0
    )
    exhaustive = 3
    while True:
        trial = emission.plant_measurement_contour(
            plant, ring, characteristic_height_m=5.0, position_count=exhaustive
        )
        if trial.position_spacing_m <= 2.0 * trial.mean_distance_m:
            break
        exhaustive += 1
    assert layout.position_count == exhaustive == count


def test_largest_dimension_and_receiver_distance() -> None:
    contour = _contour()
    diagonal = math.hypot(200.0, 120.0)
    assert contour.largest_plant_dimension_m == pytest.approx(diagonal)
    assert contour.minimum_receiver_distance_m == pytest.approx(1.5 * diagonal)


def test_plant_centre_is_the_centroid() -> None:
    square = emission.plant_measurement_contour(
        [[0, 0], [40, 0], [40, 40], [0, 40]],
        [[-10, -10], [50, -10], [50, 50], [-10, 50]],
        characteristic_height_m=5.0,
    )
    np.testing.assert_allclose(square.plant_centre_m, [20.0, 20.0])


def test_omitted_positions_leave_the_layout_and_the_mean() -> None:
    full = _contour(position_count=16)
    partial = _contour(position_count=16, omitted_positions=[3])
    assert partial.positions_m.shape == (15, 2)
    assert partial.omitted_percent == pytest.approx(100.0 / 16.0)
    kept = np.delete(full.distances_m, 3)
    assert partial.mean_distance_m == pytest.approx(float(np.mean(kept)))
    np.testing.assert_allclose(partial.layout_positions_m, full.layout_positions_m)


def test_omitted_positions_need_a_layout() -> None:
    with pytest.raises(ValueError, match="give its 'position_count'"):
        emission.plant_measurement_contour(
            PLANT, CONTOUR, characteristic_height_m=8.0, omitted_positions=[1]
        )


def test_a_contour_must_enclose_the_plant() -> None:
    small = CONTOUR * 0.2
    with pytest.raises(ValueError, match="'contour_m' must enclose every vertex"):
        emission.plant_measurement_contour(PLANT, small, characteristic_height_m=8.0)


def test_a_contour_touching_the_plant_is_refused() -> None:
    touching = np.array([[-25.0, 0.0], [225.0, 0.0], [225.0, 145.0], [-25.0, 145.0]])
    with pytest.raises(ValueError, match="'contour_m' must not touch"):
        emission.plant_measurement_contour(PLANT, touching, characteristic_height_m=8.0)


def test_a_self_crossing_outline_is_refused() -> None:
    bow_tie = np.array([[0.0, 0.0], [10.0, 10.0], [12.0, 0.0], [0.0, 12.0]])
    with pytest.raises(ValueError, match="'plant_outline_m' must be a simple polygon"):
        emission.plant_measurement_contour(
            bow_tie, CONTOUR, characteristic_height_m=8.0
        )


def test_a_repeated_closing_vertex_is_dropped() -> None:
    closed = np.vstack([PLANT, PLANT[:1]])
    contour = emission.plant_measurement_contour(
        closed, CONTOUR, characteristic_height_m=8.0
    )
    assert contour.plant_outline_m.shape == PLANT.shape


# --------------------------------------------------------------------------- #
# Clause 10
# --------------------------------------------------------------------------- #


def test_steps_1_and_4_to_8_by_hand() -> None:
    levels = np.array([[70.0, 60.0], [72.0, 61.0], [74.0, 59.0]])
    res = emission.plant_sound_power(
        levels,
        [1000.0, 4000.0],
        measurement_area_m2=40000.0,
        contour_length_m=800.0,
        microphone_height_m=10.0,
        mean_distance_m=20.0,
        plant_area_m2=10000.0,
    )
    mean = 10.0 * np.log10(np.mean(10.0 ** (levels / 10.0), axis=0))
    np.testing.assert_allclose(res.mean_level_db, mean)
    assert res.area_term_db == pytest.approx(
        10.0 * math.log10(2 * 40000.0 + 10.0 * 800.0)
    )
    assert res.near_field_term_db == pytest.approx(math.log10(20.0 / (4.0 * 100.0)))
    np.testing.assert_allclose(res.microphone_term_db, 0.0)
    np.testing.assert_allclose(
        res.air_absorption_term_db, 0.5 * np.array([0.005, 0.026]) * 200.0
    )
    expected = (
        mean + res.area_term_db + res.near_field_term_db + res.air_absorption_term_db
    )
    np.testing.assert_allclose(res.sound_power_level_db, expected)


def test_note_11_bounds_the_proximity_term() -> None:
    """At the two ends of 9.1.1 a), dLF = lg(0,5/4) and lg(0,05/4): -0,9 and -1,9 dB."""
    top = emission.plant_sound_power(
        [[70.0]], [1000.0], measurement_area_m2=1e4, contour_length_m=400.0,
        microphone_height_m=5.0, mean_distance_m=50.0, plant_area_m2=1e4,
    )  # fmt: skip
    bottom = dataclasses.replace(top, mean_distance_m=5.0)
    assert top.near_field_term_db == pytest.approx(-0.90309, abs=5e-6)
    assert bottom.near_field_term_db == pytest.approx(-1.90309, abs=5e-6)
    assert round(top.near_field_term_db, 1) == -0.9
    assert round(bottom.near_field_term_db, 1) == -1.9


def test_note_11_holds_for_every_contour_that_meets_9_1() -> None:
    """The proximity term of a determination made anywhere inside the window
    of 9.1.1 a) lies between the two ends NOTE 11 gives.
    """
    rng = np.random.default_rng(11)
    checked = 0
    for _ in range(200):
        area = float(rng.uniform(150.0, 400000.0))
        lower, upper = emission.plant_mean_distance_limits_m(area)
        if lower >= upper:
            continue
        distance = min(float(rng.uniform(lower, upper)) + 1e-9, upper)
        res = emission.plant_sound_power(
            [[70.0]], [1000.0], measurement_area_m2=4.0 * area,
            contour_length_m=8.0 * math.sqrt(area), microphone_height_m=5.0,
            mean_distance_m=distance, plant_area_m2=area,
        )  # fmt: skip
        assert -1.90309 - 1e-9 < res.near_field_term_db <= -0.90309 + 1e-9
        checked += 1
    assert checked > 150


def test_a_point_source_gives_its_own_sound_power_back() -> None:
    """A point source on the ground at the centre of a circular contour.

    Over a reflecting plane the level on the rim is LW - 10 lg(2 pi (R^2 +
    h^2)), and 2 Sm + h l of a circle is 2 pi R^2 + 2 pi R h, so Lp + dLS -
    LW = 10 lg((R^2 + R h)/(R^2 + h^2)), which is 0 as h goes to 0: the area
    term is the hemisphere over the contour. The proximity term is set to 0
    (d = 4 sqrt(Sp)) and alpha is 0 at 63 Hz, so only the area term acts.
    """
    source_lw = 120.0
    radius = 150.0
    count = 7200
    angles = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
    circle = np.c_[radius * np.cos(angles), radius * np.sin(angles)]
    sm = abs(spp._signed_area(circle))
    length = float(
        np.sum(np.hypot(*np.diff(np.vstack([circle, circle[:1]]), axis=0).T))
    )
    plant_area = 100.0
    for height in (1e-6, 5.0, 20.0):
        lp = source_lw - 10.0 * math.log10(2.0 * math.pi * (radius**2 + height**2))
        res = emission.plant_sound_power(
            np.full((24, 1), lp), [63.0], measurement_area_m2=sm,
            contour_length_m=length, microphone_height_m=height,
            mean_distance_m=4.0 * math.sqrt(plant_area), plant_area_m2=plant_area,
        )  # fmt: skip
        assert res.near_field_term_db == pytest.approx(0.0, abs=1e-12)
        expected = 10.0 * math.log10(
            (radius**2 + radius * height) / (radius**2 + height**2)
        )
        assert res.sound_power_level_db[0] - source_lw == pytest.approx(
            expected, abs=1e-5
        )


def test_a_result_keeps_copies_of_the_callers_readings() -> None:
    levels = np.array([[70.0, 60.0], [72.0, 61.0]])
    res = emission.plant_sound_power(
        levels, [500.0, 1000.0], measurement_area_m2=1e4, contour_length_m=400.0,
        microphone_height_m=5.0, mean_distance_m=10.0, plant_area_m2=4e3,
    )  # fmt: skip
    before = res.sound_power_level_db.copy()
    levels += 20.0
    np.testing.assert_array_equal(res.sound_power_level_db, before)
    assert not res.measured_levels_db.flags.writeable
    assert not res.frequencies_hz.flags.writeable


def test_background_is_corrected_position_by_position() -> None:
    levels = np.array([[70.0, 60.0], [72.0, 61.0]])
    background = levels - np.array([[6.0, 9.0], [12.0, 7.0]])
    res = emission.plant_sound_power(
        levels, [500.0, 1000.0], measurement_area_m2=1e4, contour_length_m=400.0,
        microphone_height_m=5.0, mean_distance_m=10.0, plant_area_m2=4e3,
        background_levels_db=background,
    )  # fmt: skip
    np.testing.assert_array_equal(
        res.background_correction_db, [[1.0, 0.5], [0.0, 1.0]]
    )
    np.testing.assert_allclose(res.levels_db, levels - [[1.0, 0.5], [0.0, 1.0]])


def test_a_background_too_close_makes_the_determination_invalid() -> None:
    levels = np.array([[70.0], [72.0]])
    background = np.array([[66.0], [60.0]])
    with pytest.raises(ValueError, match="Table 2 calls a measurement invalid"):
        emission.plant_sound_power(
            levels, [500.0], measurement_area_m2=1e4, contour_length_m=400.0,
            microphone_height_m=5.0, mean_distance_m=10.0, plant_area_m2=4e3,
            background_levels_db=background,
        )  # fmt: skip


def test_steps_2_and_3_cap_a_level_far_above_the_average() -> None:
    levels = np.array([[60.0], [60.0], [60.0], [60.0], [80.0]])
    with pytest.warns(emission.SoundPowerWarning, match="10.2"):
        res = emission.plant_sound_power(
            levels, [1000.0], measurement_area_m2=1e4, contour_length_m=400.0,
            microphone_height_m=5.0, mean_distance_m=10.0, plant_area_m2=4e3,
        )  # fmt: skip
    mean = 10.0 * math.log10(np.mean(10.0 ** (levels[:, 0] / 10.0)))
    assert res.steps_2_3_applied
    np.testing.assert_array_equal(res.capped[:, 0], [False, False, False, False, True])
    capped = np.array([60.0, 60.0, 60.0, 60.0, mean + 5.0])
    star = 10.0 * math.log10(np.mean(10.0 ** (capped / 10.0)))
    assert res.corrected_mean_level_db[0] == pytest.approx(star)
    assert res.sound_power_level_db[0] - res.corrected_mean_level_db[
        0
    ] == pytest.approx(
        res.area_term_db + res.near_field_term_db + res.air_absorption_term_db[0]
    )


def test_no_warning_when_every_level_is_within_5_db() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        res = _contour().sound_power(_levels(_contour().positions_m.shape[0]), OCTAVES)
    assert not res.steps_2_3_applied
    np.testing.assert_allclose(res.corrected_mean_level_db, res.mean_level_db)


@pytest.mark.parametrize(("theta", "term"), [(30.0, 2.0), (45.0, 1.5), (90.0, 0.0)])
def test_directional_microphone_term(theta: float, term: float) -> None:
    res = emission.plant_sound_power(
        [[70.0]], [1000.0], measurement_area_m2=1e4, contour_length_m=400.0,
        microphone_height_m=5.0, mean_distance_m=10.0, plant_area_m2=4e3,
        directional_microphone_angle_deg=theta,
    )  # fmt: skip
    assert res.microphone_term_db[0] == pytest.approx(term)


def test_directional_microphone_past_90_degrees_is_refused() -> None:
    with pytest.raises(ValueError, match="'directional_microphone_angle_deg' must lie"):
        emission.plant_sound_power(
            [[70.0]], [1000.0], measurement_area_m2=1e4, contour_length_m=400.0,
            microphone_height_m=5.0, mean_distance_m=10.0, plant_area_m2=4e3,
            directional_microphone_angle_deg=120.0,
        )  # fmt: skip


def test_a_weighted_level_uses_the_annex_e_octave_corrections() -> None:
    lw_levels = np.full((1, OCTAVES.size), 70.0)
    res = emission.plant_sound_power(
        lw_levels, OCTAVES, measurement_area_m2=1e4, contour_length_m=400.0,
        microphone_height_m=5.0, mean_distance_m=10.0, plant_area_m2=4e3,
    )  # fmt: skip
    ck = np.array([-26.2, -16.1, -8.6, -3.2, 0.0, 1.2, 1.0, -1.1])
    expected = 10.0 * math.log10(
        np.sum(10.0 ** ((res.sound_power_level_db + ck) / 10.0))
    )
    assert res.a_weighted_sound_power_level_db == pytest.approx(expected)


def test_the_31_5_hz_band_is_left_out_of_lwa() -> None:
    with_low = emission.plant_sound_power(
        [[90.0, 70.0]], [31.5, 1000.0], measurement_area_m2=1e4,
        contour_length_m=400.0, microphone_height_m=5.0, mean_distance_m=10.0,
        plant_area_m2=4e3,
    )  # fmt: skip
    np.testing.assert_array_equal(with_low.a_weighted_bands_hz, [1000.0])
    assert with_low.a_weighted_sound_power_level_db == pytest.approx(
        with_low.sound_power_level_db[1]
    )


def test_weather_changes_only_the_air_term() -> None:
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])
    table = contour.sound_power(levels, OCTAVES)
    weather = contour.sound_power(
        levels, OCTAVES, temperature_c=25.0, relative_humidity_percent=40.0
    )
    delta = weather.sound_power_level_db - table.sound_power_level_db
    np.testing.assert_allclose(
        delta, weather.air_absorption_term_db - table.air_absorption_term_db
    )


def test_uncertainty_follows_the_distance_ratio() -> None:
    res = _contour().sound_power(_levels(_contour().positions_m.shape[0]), OCTAVES)
    assert res.uncertainty_db == emission.plant_method_uncertainty_db(
        res.distance_ratio
    )
    outside = dataclasses.replace(res, mean_distance_m=1.0)
    assert outside.uncertainty_db is None


def test_contour_supplies_its_geometry_and_the_prescribed_height() -> None:
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])
    res = contour.sound_power(levels, OCTAVES)
    assert res.measurement_area_m2 == pytest.approx(contour.measurement_area_m2)
    assert res.contour_length_m == pytest.approx(contour.contour_length_m)
    assert res.mean_distance_m == pytest.approx(contour.mean_distance_m)
    assert res.plant_area_m2 == pytest.approx(contour.plant_area_m2)
    assert res.microphone_height_m == pytest.approx(
        contour.prescribed_microphone_height_m
    )


def test_contour_needs_one_row_per_measured_position() -> None:
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0] + 1)
    with pytest.raises(ValueError, match="'levels_db' has .* rows for"):
        contour.sound_power(levels, OCTAVES)


def test_levels_must_match_the_bands() -> None:
    with pytest.raises(ValueError, match="'measured_levels_db' has 2 columns"):
        emission.plant_sound_power(
            [[70.0, 71.0]], [1000.0], measurement_area_m2=1e4, contour_length_m=400.0,
            microphone_height_m=5.0, mean_distance_m=10.0, plant_area_m2=4e3,
        )  # fmt: skip


def test_a_spectrum_of_31_5_hz_alone_cannot_be_a_weighted() -> None:
    with pytest.raises(ValueError, match="A-weighting of 10.9"):
        emission.plant_sound_power(
            [[70.0]], [31.5], measurement_area_m2=1e4, contour_length_m=400.0,
            microphone_height_m=5.0, mean_distance_m=10.0, plant_area_m2=4e3,
        )  # fmt: skip


# --------------------------------------------------------------------------- #
# The verdict
# --------------------------------------------------------------------------- #


def _passing() -> tuple[spp.PlantMeasurementContour, spp.PlantSoundPowerResult]:
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])[:, :-1]
    res = contour.sound_power(levels, OCTAVES[:-1])
    return contour, res


def _requirement(res: spp.PlantSoundPowerResult, key: str) -> spp.PlantRequirement:
    """The row the readings of a determination give for one requirement."""
    return next(r for r in spp._reading_rows(res) if r.key == key)


def test_a_compliant_measurement_passes() -> None:
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])
    res = contour.sound_power(levels, OCTAVES, background_levels_db=levels - 12.0)
    check = emission.check_plant_measurement(contour, res, measurement_time_s=90.0)
    assert check.passes, check.failures
    assert check.deviations == ()
    keys = {r.key for r in check.requirements}
    assert {"mean_distance_min", "aspect_angle", "position_spacing"} <= keys
    assert {"background_margin", "octave_bands", "measurement_time"} <= keys


def test_the_verdict_has_no_truth_value() -> None:
    check = emission.check_plant_measurement(_contour())
    with pytest.raises(TypeError, match="no truth value"):
        bool(check)


def test_an_unknown_requirement_is_a_key_error() -> None:
    check = emission.check_plant_measurement(_contour())
    with pytest.raises(KeyError, match="nothing"):
        check.requirement("nothing")


def test_a_contour_too_far_out_fails_9_1_1_a() -> None:
    far = np.array([[-60.0, -60.0], [260.0, -60.0], [260.0, 180.0], [-60.0, 180.0]])
    contour = emission.plant_measurement_contour(
        PLANT, far, characteristic_height_m=8.0
    )
    check = emission.check_plant_measurement(contour)
    assert not check.passes
    assert [r.key for r in check.failures] == ["mean_distance_max"]


def test_too_few_positions_fail_9_1_1_c() -> None:
    contour = _contour(position_count=4)
    check = emission.check_plant_measurement(contour)
    assert not check.requirement("position_spacing").holds


def test_more_than_10_percent_omitted_fails_9_1_2_4() -> None:
    contour = _contour(position_count=16, omitted_positions=[1, 5])
    check = emission.check_plant_measurement(contour)
    assert not check.requirement("omitted_positions").holds
    assert check.requirement("omitted_positions").value == pytest.approx(12.5)


def test_a_low_microphone_is_a_deviation_above_5_m_and_a_failure_below() -> None:
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])
    low = contour.sound_power(levels, OCTAVES, microphone_height_m=6.0)
    check = emission.check_plant_measurement(contour, low)
    assert check.passes
    assert [r.key for r in check.deviations] == ["microphone_height"]
    lower = contour.sound_power(levels, OCTAVES, microphone_height_m=4.0)
    assert not emission.check_plant_measurement(contour, lower).passes


@pytest.mark.parametrize("height", [15.0, 30.0, 100.0])
def test_a_microphone_above_the_prescribed_height_is_a_deviation(height: float) -> None:
    """9.3 prescribes a height, not a lower bound: a microphone higher than
    H + 0,025 sqrt(Sm) is reported like a lower one.
    """
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])
    high = contour.sound_power(levels, OCTAVES, microphone_height_m=height)
    check = emission.check_plant_measurement(contour, high)
    assert check.passes
    assert [r.key for r in check.deviations] == ["microphone_height"]


@pytest.mark.parametrize("factor", [0.96, 1.0, 1.04])
def test_a_microphone_within_the_plan_accuracy_is_at_the_prescribed_height(
    factor: float,
) -> None:
    """9.2 reads H and Sm off the plan to +/-5 %, so h is known to that much."""
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])
    height = factor * contour.prescribed_microphone_height_m
    res = contour.sound_power(levels, OCTAVES, microphone_height_m=height)
    row = emission.check_plant_measurement(contour, res).requirement(
        "microphone_height"
    )
    assert row.holds
    assert row.comparison == "="
    assert row.tolerance == pytest.approx(0.05 * contour.prescribed_microphone_height_m)
    assert row.margin == pytest.approx(0.05 - abs(factor - 1.0))


def test_a_narrow_directional_microphone_fails_7_1() -> None:
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])
    res = contour.sound_power(levels, OCTAVES, directional_microphone_angle_deg=25.0)
    check = emission.check_plant_measurement(contour, res)
    assert not check.requirement("directional_microphone").holds
    assert res.microphone_term_db[0] == pytest.approx(3.0 * (1.0 - 25.0 / 90.0))


def test_background_under_10_db_is_a_deviation() -> None:
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])
    res = contour.sound_power(levels, OCTAVES, background_levels_db=levels - 8.0)
    check = emission.check_plant_measurement(contour, res)
    assert check.passes
    assert [r.key for r in check.deviations] == ["background_margin_preferred"]


def test_missing_octave_bands_fail_9_5_1_a() -> None:
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])[:, 1:]
    res = contour.sound_power(levels, OCTAVES[1:])
    check = emission.check_plant_measurement(contour, res)
    row = check.requirement("octave_bands")
    assert not row.holds
    assert row.value == 6.0


def test_a_level_far_above_the_average_is_a_deviation() -> None:
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])
    levels[2, 3] += 12.0
    with pytest.warns(emission.SoundPowerWarning, match="10.2"):
        res = contour.sound_power(levels, OCTAVES)
    check = emission.check_plant_measurement(contour, res)
    assert "level_excess" in {r.key for r in check.deviations}


def test_a_short_measurement_fails_9_5_1() -> None:
    check = emission.check_plant_measurement(
        _contour(), measurement_time_s=[90.0, 45.0]
    )
    row = check.requirement("measurement_time")
    assert not row.holds
    assert row.value == 45.0


@pytest.mark.parametrize(("spread", "holds"), [(0.0, True), (1.0, True), (1.2, False)])
def test_the_integrated_reading_fluctuates_by_at_most_half_a_decibel_9_5_3(
    spread: float, *, holds: bool
) -> None:
    check = emission.check_plant_measurement(_contour(), leq_range_db=[0.4, spread])
    row = check.requirement("integrated_reading")
    assert row.clause == "9.5.3"
    assert row.holds is holds
    assert check.passes is holds


def test_an_integrated_reading_moving_over_1_db_meets_9_5_3() -> None:
    """64,4 - 63,4 dB is a range of 1 dB, though 1,000 000 000 000 007 in
    binary, and ± 0,5 dB allows it.
    """
    check = emission.check_plant_measurement(_contour(), leq_range_db=64.4 - 63.4)
    row = check.requirement("integrated_reading")
    assert row.value == 1.0
    assert row.holds


def test_a_negative_range_of_the_integrated_reading_is_refused() -> None:
    contour = _contour()
    with pytest.raises(ValueError, match="'leq_range_db' must be finite"):
        emission.check_plant_measurement(contour, leq_range_db=-0.1)


def test_a_small_plant_fails_1_2() -> None:
    plant = [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]]
    ring = [[-6.0, -6.0], [16.0, -6.0], [16.0, 16.0], [-6.0, 16.0]]
    contour = emission.plant_measurement_contour(
        plant, ring, characteristic_height_m=4.0
    )
    check = emission.check_plant_measurement(contour)
    assert not check.requirement("plant_dimension_min").holds


def test_a_plant_over_320_m_is_a_deviation_not_a_failure() -> None:
    """1.2 gives the upper end as "approximately 320 m"."""
    plant = [[0.0, 0.0], [320.0, 0.0], [320.0, 100.0], [0.0, 100.0]]
    ring = [[-20.0, -20.0], [340.0, -20.0], [340.0, 120.0], [-20.0, 120.0]]
    contour = emission.plant_measurement_contour(
        plant, ring, characteristic_height_m=6.0
    )
    check = emission.check_plant_measurement(contour)
    assert contour.largest_plant_dimension_m > 330.0
    assert check.passes
    assert [r.key for r in check.deviations] == ["plant_dimension_max"]


def test_a_mean_distance_of_exactly_5_m_fails_9_1_1_a() -> None:
    """9.1.1 a): the average distance "shall exceed" 5 m; 5 m itself does not."""
    plant = [[0.0, 0.0], [100.0, 0.0], [100.0, 20.0], [0.0, 20.0]]
    # Four positions, each on a side 5 m out, starting at the middle of one.
    ring = [[50.0, -5.0], [105.0, -5.0], [105.0, 25.0], [-5.0, 25.0], [-5.0, -5.0]]
    contour = emission.plant_measurement_contour(
        plant, ring, characteristic_height_m=2.0, position_count=4
    )
    row = emission.check_plant_measurement(contour).requirement("mean_distance_min")
    assert contour.mean_distance_m == pytest.approx(5.0, abs=1e-12)
    assert row.limit == 5.0
    assert not row.holds


def test_a_3_db_angle_of_exactly_30_degrees_fails_7_1() -> None:
    """7.1: the angle "shall exceed +/-30 deg"."""
    contour = _contour()
    res = contour.sound_power(
        _levels(contour.positions_m.shape[0]), OCTAVES,
        directional_microphone_angle_deg=30.0,
    )  # fmt: skip
    row = emission.check_plant_measurement(contour, res).requirement(
        "directional_microphone"
    )
    assert not row.holds


@pytest.mark.parametrize(
    ("margin", "required", "preferred"),
    [(6.0, True, False), (10.0, True, False), (10.5, True, True)],
)
def test_background_margins_at_the_edges_of_6_b(
    margin: float, *, required: bool, preferred: bool
) -> None:
    """6 b): "at least 6 dB, and preferably more than 10 dB"."""
    contour = _contour()
    levels = np.round(2.0 * _levels(contour.positions_m.shape[0])) / 2.0
    res = contour.sound_power(levels, OCTAVES, background_levels_db=levels - margin)
    check = emission.check_plant_measurement(contour, res)
    assert check.requirement("background_margin").holds is required
    assert check.requirement("background_margin_preferred").holds is preferred


def test_one_omitted_position_in_ten_meets_9_1_2_4() -> None:
    """9.1.2.4 asks for another contour only when the omissions exceed 10 %."""
    contour = _contour(position_count=10, omitted_positions=[3])
    row = emission.check_plant_measurement(contour).requirement("omitted_positions")
    assert row.clause == "9.1.2.4, 12 n)"
    assert row.value == pytest.approx(10.0)
    assert row.holds


def test_a_level_exactly_5_db_above_the_average_is_not_replaced() -> None:
    """10.2 replaces a level that exceeds the average "by more than 5 dB"."""
    top = 10.0 * math.log10(3e6 * 10.0**0.5 / (4.0 - 10.0**0.5))
    res = emission.plant_sound_power(
        [[60.0], [60.0], [60.0], [top]], [1000.0], measurement_area_m2=1e4,
        contour_length_m=400.0, microphone_height_m=5.0, mean_distance_m=10.0,
        plant_area_m2=4e3,
    )  # fmt: skip
    excess = float(res.levels_db[3, 0] - res.mean_level_db[0])
    assert excess == pytest.approx(5.0, abs=1e-12)
    assert not res.capped[3, 0]
    assert _requirement(res, "level_excess").holds


@pytest.mark.parametrize(
    ("base", "top", "count"),
    [(74.5, 85.0402115764155, 4), (54.0, 60.9407770016165, 7)],
)
def test_a_level_a_hair_under_5_db_above_the_average_is_not_replaced(
    base: float, top: float, count: int
) -> None:
    """Readings that put the last level a few 10^-15 dB under the average plus
    5 dB, worked in exact arithmetic, come out of the energy mean in binary
    that much above it, 5,000 000 000 000 014 and 5,000 000 000 000 007 dB.
    Neither is "more than 5 dB" (10.2), so nothing is replaced and the check
    has no deviation.
    """
    levels = [[base]] * (count - 1) + [[top]]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        res = emission.plant_sound_power(
            levels, [1000.0], measurement_area_m2=1e4, contour_length_m=400.0,
            microphone_height_m=5.0, mean_distance_m=10.0, plant_area_m2=4e3,
        )  # fmt: skip
    assert not res.capped.any()
    assert not res.steps_2_3_applied
    np.testing.assert_array_equal(res.corrected_mean_level_db, res.mean_level_db)
    row = _requirement(res, "level_excess")
    assert row.value == 5.0
    assert row.holds


@pytest.mark.parametrize(
    ("operating", "background", "required", "preferred", "correction"),
    [(64.1, 58.1, True, False, 1.0), (64.4, 54.4, True, False, 0.5)],
)
def test_background_margins_of_decimal_readings_at_the_edges_of_6_b(
    operating: float,
    background: float,
    *,
    required: bool,
    preferred: bool,
    correction: float,
) -> None:
    """64,1 over 58,1 dB is the 6 dB 6 b) requires, 64,4 over 54,4 dB the
    10 dB it does not prefer, whatever the last binary digit of the
    difference says.
    """
    contour = _contour()
    shape = (contour.positions_m.shape[0], OCTAVES.size)
    res = contour.sound_power(
        np.full(shape, operating), OCTAVES,
        background_levels_db=np.full(shape, background),
    )  # fmt: skip
    np.testing.assert_array_equal(res.background_correction_db, correction)
    check = emission.check_plant_measurement(contour, res)
    assert check.requirement("background_margin").holds is required
    assert check.requirement("background_margin_preferred").holds is preferred


def test_a_determination_of_another_contour_is_refused() -> None:
    contour = _contour()
    other = _contour(position_count=contour.position_count + 3)
    res = other.sound_power(_levels(other.positions_m.shape[0]), OCTAVES)
    with pytest.raises(ValueError, match="another 'mean_distance_m'"):
        emission.check_plant_measurement(contour, res)


def test_a_determination_with_another_number_of_positions_is_refused() -> None:
    contour = _contour()
    count = contour.positions_m.shape[0] + 2
    res = emission.plant_sound_power(
        _levels(count), OCTAVES,
        measurement_area_m2=contour.measurement_area_m2,
        contour_length_m=contour.contour_length_m,
        microphone_height_m=contour.prescribed_microphone_height_m,
        mean_distance_m=contour.mean_distance_m,
        plant_area_m2=contour.plant_area_m2,
    )  # fmt: skip
    with pytest.raises(ValueError, match="another number of positions"):
        emission.check_plant_measurement(contour, res)


def test_requirement_margin_within_a_tolerance() -> None:
    row = spp._row("k", "c", "d", 10.2, "=", 10.0, "m", tolerance=0.5)
    assert row.holds
    assert row.margin == pytest.approx(0.03)
    row = spp._row("k", "c", "d", 9.4, "=", 10.0, "m", tolerance=0.5)
    assert not row.holds
    assert row.margin == pytest.approx(-0.01)


@pytest.mark.parametrize("tolerance", [-0.1, math.nan])
def test_a_requirement_with_a_negative_or_nan_tolerance_is_refused(
    tolerance: float,
) -> None:
    with pytest.raises(ValueError, match="'tolerance' must be >= 0"):
        emission.PlantRequirement(
            "k", "c", "d", 1.0, "=", 1.0, "m", holds=True, tolerance=tolerance
        )


def test_requirement_margin_sign() -> None:
    row = spp._row("k", "c", "d", 3.0, "<=", 4.0, "m")
    assert row.margin == pytest.approx(0.25)
    row = spp._row("k", "c", "d", 3.0, ">", 4.0, "m")
    assert row.margin == pytest.approx(-0.25)
    assert not row.holds


def test_a_requirement_with_an_unknown_comparison_is_refused() -> None:
    with pytest.raises(ValueError, match="'comparison' must be one of"):
        emission.PlantRequirement("k", "c", "d", 1.0, "==", 1.0, "m", holds=True)


# --------------------------------------------------------------------------- #
# Particular parts (0.2 b)
# --------------------------------------------------------------------------- #


def test_two_equal_parts_add_3_db() -> None:
    _contour_, res = _passing()
    parts = emission.partial_plant_contributions([res, res], names=["North", "South"])
    np.testing.assert_allclose(
        parts.total_level_db - res.sound_power_level_db, 10.0 * math.log10(2.0)
    )
    np.testing.assert_allclose(parts.contribution_db, -10.0 * math.log10(2.0))
    assert parts.a_weighted_total_db == pytest.approx(
        res.a_weighted_sound_power_level_db + 10.0 * math.log10(2.0)
    )


def test_parts_are_named_by_default() -> None:
    _contour_, res = _passing()
    parts = emission.partial_plant_contributions([res])
    assert parts.names == ("Part 1",)


def test_parts_over_different_bands_are_refused() -> None:
    _contour_, res = _passing()
    contour = _contour()
    other = contour.sound_power(_levels(contour.positions_m.shape[0]), OCTAVES)
    with pytest.raises(ValueError, match="same octave bands"):
        emission.partial_plant_contributions([res, other])


def test_no_parts_is_refused() -> None:
    with pytest.raises(ValueError, match="'parts' must hold at least one"):
        emission.partial_plant_contributions([])


# --------------------------------------------------------------------------- #
# Figures
# --------------------------------------------------------------------------- #


def test_contour_plot_draws_plant_contour_and_positions() -> None:
    contour = _contour(position_count=16, omitted_positions=[2])
    ax = contour.plot()
    labels = ax.get_legend().get_texts()
    texts = [t.get_text() for t in labels]
    assert "Measurement position" in texts
    assert "Omitted position" in texts
    assert "ISO 8297" in ax.get_title()
    assert len(ax.patches) >= 1
    plt.close("all")


def test_contour_plot_in_spanish() -> None:
    ax = _contour().plot(language="es")
    texts = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "Posición de medición" in texts
    assert "Contorno de medición ISO 8297" in ax.get_title()
    plt.close("all")


def test_sound_power_plot_draws_one_bar_per_band() -> None:
    contour = _contour()
    res = contour.sound_power(_levels(contour.positions_m.shape[0]), OCTAVES)
    ax = res.plot()
    heights = [p.get_height() for p in ax.patches]
    np.testing.assert_allclose(heights, res.sound_power_level_db)
    assert f"{res.a_weighted_sound_power_level_db:.1f}" in ax.get_title()
    plt.close("all")


def test_check_plot_draws_one_bar_per_requirement() -> None:
    contour = _contour(position_count=4)
    check = emission.check_plant_measurement(contour)
    ax = check.plot(language="es")
    assert len(ax.patches) == len(check.requirements)
    assert "incumplidos" in ax.get_title()
    plt.close("all")


def test_check_plot_marks_advisory_rows_hollow() -> None:
    """A row met exactly has a bar of no length and so no hatch; its hollow
    end mark still says it is advisory.
    """
    contour = _contour()
    levels = _levels(contour.positions_m.shape[0])
    res = contour.sound_power(levels, OCTAVES, background_levels_db=levels - 8.0)
    check = emission.check_plant_measurement(contour, res)
    ax = check.plot()
    marks = [c.get_offsets().shape[0] for c in ax.collections]
    advisory = sum(1 for r in check.requirements if r.advisory)
    assert sorted(marks) == sorted([len(check.requirements) - advisory, advisory])
    plt.close("all")


def test_partial_plot_draws_the_sum_and_each_part() -> None:
    _contour_, res = _passing()
    parts = emission.partial_plant_contributions([res, res], names=["A", "B"])
    ax = parts.plot()
    assert len(ax.lines) == 2
    np.testing.assert_allclose(
        [p.get_height() for p in ax.patches], parts.total_level_db
    )
    plt.close("all")
