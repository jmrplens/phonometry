#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Airborne noise of steam turbine sets: IEC 61063:1991 (EN 61063:1996).

Normative anchors (BS EN 61063:1996, the English text of IEC 1063:1991):
- Table 1, printed folio 4 (PDF page 10): 5 dB with prominent tones, 4 dB
  broadband.
- 4.2 and 4.3, printed folios 5 and 6: background at least 3 dB below; wind
  below 6 m/s, a windscreen above 1 m/s.
- 7.1 and Figure 2, printed folio 7 (PDF page 13): d = 1 m, Equation (1)
  S = 2 hmax bmax + sum l_i (2 h_i + b_i), the five key positions.
- 7.2.2 NOTE, printed folio 8: overhead positions deleted within 1,0 dB.
- Table 2, printed folio 8 (PDF page 14): the stepped background correction.
- 8.3 and 8.4, printed folio 9 (PDF page 15): Equations (2) and (3), K <= 7 dB,
  the arithmetic average within 0,7 dB when the range is within 5 dB.
- 9.4 g), printed folio 10: LWA rounded to the nearest whole decibel.
- Figure A.3, printed folio 12 (PDF page 18): K = 10 lg[1 + 4/(A/S)],
  A = 0,16 V/T, K = LW - LWr; A.3.3 K <= 7, A/S >= 1 on folio 13.

The standard prints no worked example; every value below is a closed form
computed by hand from these clauses.
"""

from __future__ import annotations

import math
import warnings

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from reference_data import steam_turbines as oracle

from phonometry import emission
from phonometry.emission import SoundPowerWarning

#: The four parts of a large set, as Figure 2 b draws them: HP and IP casings
#: in one box, the LP turbine in its own, then generator and exciter.
LARGE_SET = (
    emission.TurbineReferenceBox(6.0, 4.0, 3.5, "HP-IP"),
    emission.TurbineReferenceBox(5.0, 5.0, 4.5, "LP"),
    emission.TurbineReferenceBox(7.0, 3.5, 3.0, "Generator"),
    emission.TurbineReferenceBox(3.0, 2.5, 2.2, "Exciter"),
)


def _energy_mean(levels: np.ndarray) -> float:
    return 10.0 * math.log10(float(np.mean(10.0 ** (np.asarray(levels) / 10.0))))


# --- Table 2 ----------------------------------------------------------------


@pytest.mark.parametrize(("difference", "printed"), oracle.IEC61063_TABLE_2_DB.items())
def test_table_2_every_printed_cell(difference: int, printed: float) -> None:
    assert emission.turbine_background_correction(float(difference)) == printed


@pytest.mark.parametrize(
    ("difference", "expected"),
    [
        (2.0, 3.0),  # below the criterion: the first row, an upper limit
        (3.49, 3.0),
        (3.5, 2.0),  # rounds to 4
        (5.49, 2.0),
        (5.5, 1.0),  # rounds to 6
        (8.5, 0.5),  # rounds to 9
        (9.5, 0.5),  # rounds to 10
        (10.0, 0.5),  # the row 10 itself
        (10.2, 0.0),  # above 10 dB: the "> 10" row, before any rounding
        (10.49, 0.0),
        (10.5, 0.0),
        (25.0, 0.0),
    ],
)
def test_table_2_reads_the_difference_in_whole_decibels(
    difference: float, expected: float
) -> None:
    assert emission.turbine_background_correction(difference) == expected


@pytest.mark.parametrize(
    ("operating", "background", "expected"),
    [
        (32.3, 28.8, 2.0),  # 3,499 999 999 999 996 in binary: 3,5 dB, up to 4
        (20.4, 14.9, 1.0),  # 5,499 999 999 999 998: 5,5 dB, rounded up to 6
        (20.1, 10.1, 0.5),  # 10,000 000 000 000 002: the row 10, not "> 10"
    ],
)
def test_table_2_reads_a_difference_of_decimal_readings_as_printed(
    operating: float, background: float, expected: float
) -> None:
    """The difference of two readings to 0,1 dB is not exact in binary."""
    difference = operating - background
    assert difference != round(difference, 1)
    assert emission.turbine_background_correction(difference) == expected


def test_table_2_keeps_the_shape_of_its_input() -> None:
    scalar = emission.turbine_background_correction(4.0)
    array = emission.turbine_background_correction([4.0, 12.0])
    assert isinstance(scalar, float)
    assert isinstance(array, np.ndarray)
    np.testing.assert_array_equal(array, [2.0, 0.0])


def test_table_2_departs_from_the_iso_3746_formula_by_tenths() -> None:
    """At the printed rows the steps stay within 0,35 dB of Equation (12)."""
    rows = np.arange(3.0, 11.0)
    steps = np.asarray(emission.turbine_background_correction(rows))
    exact = -10.0 * np.log10(1.0 - 10.0 ** (-0.1 * rows))
    np.testing.assert_allclose(steps, exact, atol=0.36)
    assert steps[2] - exact[2] > 0.3  # 5 dB: 2 against 1,65
    assert exact[3] - steps[3] > 0.25  # 6 dB: 1 against 1,26


def test_table_2_refuses_a_difference_that_is_not_finite() -> None:
    with pytest.raises(ValueError, match="level_difference_db"):
        emission.turbine_background_correction(math.nan)


# --- The measurement surface, Equation (1) ----------------------------------


def test_one_box_is_the_iso_3746_parallelepiped() -> None:
    surface = emission.turbine_measurement_surface(
        [emission.TurbineReferenceBox(8.0, 3.0, 2.5)]
    )
    d = oracle.IEC61063_MEASUREMENT_DISTANCE_M
    length, width, height = 8.0 + 2 * d, 3.0 + 2 * d, 2.5 + d
    assert surface.lengths_m.tolist() == [length]
    assert surface.widths_m.tolist() == [width]
    assert surface.heights_m.tolist() == [height]
    expected = length * width + 2 * length * height + 2 * width * height
    assert surface.area_m2 == pytest.approx(expected, rel=1e-12)
    assert surface.enveloping_area_m2 == pytest.approx(expected, rel=1e-12)


def test_equation_1_for_the_large_set_by_hand() -> None:
    surface = emission.turbine_measurement_surface(LARGE_SET)
    lengths = [7.0, 5.0, 7.0, 4.0]  # 1 m added at each end of the set
    widths = [6.0, 7.0, 5.5, 4.5]
    heights = [4.5, 5.5, 4.0, 3.2]
    expected = 2 * 5.5 * 7.0 + sum(
        length * (2 * h + b)
        for length, h, b in zip(lengths, heights, widths, strict=True)
    )
    np.testing.assert_allclose(surface.lengths_m, lengths)
    np.testing.assert_allclose(surface.x_edges_m, [0.0, 7.0, 12.0, 19.0, 23.0])
    assert surface.area_m2 == pytest.approx(expected, rel=1e-12)
    assert surface.max_height_m == 5.5
    assert surface.max_width_m == 7.0


def test_equation_1_is_the_exact_area_when_the_sections_nest() -> None:
    """Both drawings of Figure 2 nest: the largest section, then smaller ones."""
    surface = emission.turbine_measurement_surface(LARGE_SET)
    assert surface.area_m2 == pytest.approx(surface.enveloping_area_m2, rel=1e-12)


def test_equation_1_overcounts_when_the_tallest_box_is_not_the_widest() -> None:
    """A tall narrow box beside a low wide one."""
    surface = emission.turbine_measurement_surface(
        [
            emission.TurbineReferenceBox(4.0, 1.0, 5.0),
            emission.TurbineReferenceBox(4.0, 5.0, 1.0),
        ]
    )
    # Sections 3 m wide by 6 m tall and 7 m by 2 m: ends of 18 and 14 m2 and
    # a step of 18 + 14 - 2 (3 x 2) = 20 m2, 52 m2 of transverse faces, where
    # Equation (1) counts 2 x 6 x 7 = 84 m2.
    assert surface.area_m2 - surface.enveloping_area_m2 == pytest.approx(
        84.0 - 52.0, rel=1e-12
    )


def test_equation_1_undercounts_a_small_box_between_two_large_ones() -> None:
    surface = emission.turbine_measurement_surface(
        [
            emission.TurbineReferenceBox(3.0, 3.0, 4.0),
            emission.TurbineReferenceBox(3.0, 1.0, 1.0),
            emission.TurbineReferenceBox(3.0, 3.0, 4.0),
        ]
    )
    # Sections 5 x 5, 3 x 2 and 5 x 5: ends of 25 m2 each and two steps of
    # 25 - 6 = 19 m2, 88 m2 where Equation (1) counts 2 x 5 x 5 = 50 m2.
    assert surface.enveloping_area_m2 - surface.area_m2 == pytest.approx(
        88.0 - 50.0, rel=1e-12
    )


def test_surface_refuses_no_box() -> None:
    with pytest.raises(ValueError, match="at least one reference box"):
        emission.turbine_measurement_surface([])


def test_surface_refuses_something_that_is_not_a_box() -> None:
    boxes = [(1.0, 2.0, 3.0)]
    with pytest.raises(ValueError, match="TurbineReferenceBox"):
        emission.turbine_measurement_surface(boxes)  # type: ignore[list-item]


@pytest.mark.parametrize("field", ["length_m", "width_m", "height_m"])
def test_box_refuses_a_dimension_that_is_not_positive(field: str) -> None:
    values = {"length_m": 1.0, "width_m": 1.0, "height_m": 1.0, field: 0.0}
    with pytest.raises(ValueError, match=field):
        emission.TurbineReferenceBox(**values)


def test_surface_arrays_are_read_only() -> None:
    surface = emission.turbine_measurement_surface(LARGE_SET)
    with pytest.raises(ValueError, match="read-only"):
        surface.lengths_m[0] = 1.0


# --- The microphone positions, Figure 2 --------------------------------------


def _large_array(**kwargs: object) -> emission.TurbineMicrophoneArray:
    surface = emission.turbine_measurement_surface(LARGE_SET)
    options: dict[str, object] = {
        "microphone_height_m": 1.5,
        "spacing_m": 2.0,
        "turbine_boxes": 2,
    }
    options.update(kwargs)
    return emission.turbine_microphone_positions(surface, **options)  # type: ignore[arg-type]


def test_the_five_key_positions_of_figure_2_b() -> None:
    array = _large_array()
    keys = {
        label: tuple(row)
        for label, row in zip(array.labels, array.positions_m, strict=True)
        if label
    }
    # 1 and 5 at the centres of the ends, 2 and 4 on the sides and 3 overhead
    # in the plane between the LP turbine and the generator, at the corner of
    # the LP box, the wider and taller of the two.
    assert keys == {
        "1": (0.0, 0.0, 1.5),
        "2": (12.0, 3.5, 1.5),
        "5": (23.0, 0.0, 1.5),
        "4": (12.0, -3.5, 1.5),
        "3": (12.0, 0.0, 5.5),
    }
    assert int(np.count_nonzero(array.key_mask)) == 5


def test_figure_2_a_puts_the_coupling_after_the_turbine() -> None:
    surface = emission.turbine_measurement_surface(
        [
            emission.TurbineReferenceBox(4.0, 3.0, 3.0, "turbine"),
            emission.TurbineReferenceBox(9.0, 2.0, 2.0, "gear and compressor"),
        ]
    )
    array = emission.turbine_microphone_positions(
        surface, microphone_height_m=1.0, spacing_m=1.5
    )
    key_2 = array.positions_m[array.labels.index("2")]
    np.testing.assert_allclose(key_2, [5.0, 2.5, 1.0])


def test_a_single_box_has_its_coupling_plane_at_mid_length() -> None:
    surface = emission.turbine_measurement_surface(
        [emission.TurbineReferenceBox(8.0, 3.0, 2.5)]
    )
    array = emission.turbine_microphone_positions(
        surface, microphone_height_m=1.0, spacing_m=2.0
    )
    np.testing.assert_allclose(
        array.positions_m[array.labels.index("3")], [5.0, 0.0, 3.5]
    )


def test_positions_mirror_across_the_shaft_line() -> None:
    array = _large_array()
    sides = np.asarray(array.positions_m)[~np.asarray(array.overhead_mask)]
    upper = {tuple(np.round(p, 9)) for p in sides if p[1] > 0.0}
    lower = {tuple(np.round(p * [1, -1, 1], 9)) for p in sides if p[1] < 0.0}
    assert upper == lower


def test_neighbours_along_the_path_are_no_further_apart_than_the_spacing() -> None:
    array = _large_array(spacing_m=1.7)
    loop = np.asarray(array.positions_m)[~np.asarray(array.overhead_mask)]
    closed = np.vstack([loop, loop[:1]])
    # The straight distance never exceeds the distance along the path.
    steps = np.hypot(*np.diff(closed[:, :2], axis=0).T)
    assert np.all(steps <= 1.7 + 1e-9)
    positions = np.asarray(array.positions_m)
    ends = positions[[array.labels.index("1"), array.labels.index("5")]]
    over = np.vstack([ends[:1], positions[np.asarray(array.overhead_mask)], ends[1:]])
    steps = np.hypot(*np.diff(over[:, [0, 2]], axis=0).T)
    assert np.all(steps <= 1.7 + 1e-9)


def test_the_overhead_line_climbs_the_front_end_and_crosses_the_top() -> None:
    """From key 1 up the front end, over the top to 3, and on to the rear.

    With a 2 m spacing the run from 1 to 3 (3 m up the front end, 7 m along
    the top, 1 m up the step and 5 m along) is 16 m, eight intervals of 2 m:
    the first position stands on the front end, 2 m above key position 1, as
    the elevations of Figure 2 draw one. The run from 3 to 5 (1,5 m down the
    step, 7 m along, 0,8 m down, 4 m along and 1,7 m down the rear end) is
    15 m, eight intervals of 1,875 m.
    """
    array = _large_array()
    top = np.asarray(array.positions_m)[np.asarray(array.overhead_mask)]
    assert len(top) == 7 + 1 + 7
    np.testing.assert_allclose(top[0], [0.0, 0.0, 3.5], atol=1e-12)
    np.testing.assert_allclose(top[1], [1.0, 0.0, 4.5], atol=1e-12)
    np.testing.assert_allclose(top[8], [12.375, 0.0, 4.0], atol=1e-12)
    np.testing.assert_allclose(top[-1], [22.825, 0.0, 3.2], atol=1e-12)
    assert np.all(top[:, 1] == 0.0)


def test_the_overhead_line_comes_down_the_rear_end() -> None:
    """A tall rear box puts positions on the rear end above key position 5."""
    surface = emission.turbine_measurement_surface(
        [
            emission.TurbineReferenceBox(4.0, 3.0, 3.0, "turbine"),
            emission.TurbineReferenceBox(2.0, 3.0, 5.0, "generator"),
        ]
    )
    array = emission.turbine_microphone_positions(
        surface, microphone_height_m=1.0, spacing_m=2.0
    )
    mask = np.asarray(array.overhead_mask)
    top = np.asarray(array.positions_m)[mask]
    key_3 = [label for label, over in zip(array.labels, mask, strict=True) if over]
    # Key 3 at the step, on the taller box (x = 5 m, z = 6 m). Down from it:
    # 3 m along the top and 5 m down the rear end, 8 m in four intervals.
    np.testing.assert_allclose(
        top[key_3.index("3") + 1 :],
        [[7.0, 0.0, 6.0], [8.0, 0.0, 5.0], [8.0, 0.0, 3.0]],
        atol=1e-12,
    )


def test_overhead_positions_can_be_left_out() -> None:
    array = _large_array(include_overhead=False)
    assert not np.any(array.overhead_mask)
    assert "3" not in array.labels
    assert int(np.count_nonzero(array.key_mask)) == 4


def test_every_casing_gets_a_measurement_section() -> None:
    array = _large_array()
    assert array.every_box_sampled
    assert all(count >= 1 for count in array.positions_per_box)


def test_one_position_on_a_parallelepiped_is_enough() -> None:
    """7.2.2 asks for at least one: the guide's 4 m spacing leaves the exciter one."""
    array = _large_array(spacing_m=4.0)
    assert array.positions_per_box == (2, 2, 2, 1)
    assert array.every_box_sampled


def test_a_spacing_too_long_for_a_casing_is_reported() -> None:
    surface = emission.turbine_measurement_surface(
        [
            emission.TurbineReferenceBox(10.0, 4.0, 3.0),
            emission.TurbineReferenceBox(0.4, 3.0, 2.0),
            emission.TurbineReferenceBox(10.0, 4.0, 3.0),
        ]
    )
    with pytest.warns(SoundPowerWarning, match="7.2.2"):
        array = emission.turbine_microphone_positions(
            surface, microphone_height_m=1.0, spacing_m=6.0
        )
    assert not array.every_box_sampled


def test_positions_refuse_a_height_above_the_lowest_box() -> None:
    surface = emission.turbine_measurement_surface(LARGE_SET)
    with pytest.raises(ValueError, match="microphone_height_m"):
        emission.turbine_microphone_positions(
            surface, microphone_height_m=3.5, spacing_m=2.0, turbine_boxes=2
        )


def test_positions_refuse_a_turbine_that_leaves_no_driven_machine() -> None:
    surface = emission.turbine_measurement_surface(LARGE_SET)
    with pytest.raises(ValueError, match="turbine_boxes"):
        emission.turbine_microphone_positions(
            surface, microphone_height_m=1.5, spacing_m=2.0, turbine_boxes=4
        )


def test_positions_refuse_a_spacing_that_is_not_positive() -> None:
    surface = emission.turbine_measurement_surface(LARGE_SET)
    with pytest.raises(ValueError, match="spacing_m"):
        emission.turbine_microphone_positions(
            surface, microphone_height_m=1.5, spacing_m=0.0
        )


# --- The environmental correction, Figure A.3 and A.3.2 ----------------------


def test_figure_a3_at_a_over_s_of_one_is_ten_lg_five() -> None:
    correction = emission.turbine_environmental_correction(
        200.0, absorption_area_m2=200.0
    )
    assert correction.environmental_correction_db == pytest.approx(
        10.0 * math.log10(5.0)
    )
    assert correction.ratio == 1.0


def test_absorption_area_from_the_reverberation_time() -> None:
    correction = emission.turbine_environmental_correction(
        400.0, volume_m3=30000.0, reverberation_time_s=2.4
    )
    area = 0.16 * 30000.0 / 2.4
    assert correction.absorption_area_m2 == pytest.approx(area)
    assert correction.environmental_correction_db == pytest.approx(
        10.0 * math.log10(1.0 + 4.0 / (area / 400.0))
    )


def test_environmental_correction_needs_exactly_one_route() -> None:
    with pytest.raises(ValueError, match="not both"):
        emission.turbine_environmental_correction(
            100.0, absorption_area_m2=50.0, volume_m3=1000.0
        )


def test_environmental_correction_needs_both_halves_of_the_room() -> None:
    with pytest.raises(ValueError, match="reverberation_time_s"):
        emission.turbine_environmental_correction(100.0, volume_m3=1000.0)


def test_reference_source_takes_the_mean_of_the_determinations() -> None:
    correction = emission.turbine_reference_source_correction(
        [95.4, 96.2], calibrated_level_db=93.0, machine_length_m=8.0
    )
    assert correction.environmental_correction_db == pytest.approx(2.8)
    assert correction.ratio is None
    assert correction.method == "reference source"


def test_a_machine_longer_than_ten_metres_takes_four_determinations() -> None:
    correction = emission.turbine_reference_source_correction(
        [95.0, 96.0, 97.0, 96.0], calibrated_level_db=93.0, machine_length_m=10.5
    )
    assert correction.environmental_correction_db == pytest.approx(3.0)


def test_ten_metres_exactly_still_takes_two() -> None:
    with pytest.raises(ValueError, match="needs 2 determinations"):
        emission.turbine_reference_source_correction(
            [95.0, 96.0, 97.0, 96.0], calibrated_level_db=93.0, machine_length_m=10.0
        )


# --- The qualification, A.3.3 and 4.3 ----------------------------------------


def test_seven_decibels_qualifies_and_a_hair_more_does_not() -> None:
    limit = oracle.IEC61063_K_LIMIT_DB
    check = emission.check_turbine_test_environment
    assert check(environmental_correction_db=limit).passes
    assert not check(environmental_correction_db=limit + 1e-6).passes


def test_seven_decibels_from_two_decimal_readings_qualifies() -> None:
    """(85,4 + 89,2)/2 - 80,3 is 7,000 000 000 000 014 in binary: 7 dB, within."""
    correction = emission.turbine_reference_source_correction(
        [85.4, 89.2], calibrated_level_db=80.3, machine_length_m=8.0
    )
    assert correction.environmental_correction_db > oracle.IEC61063_K_LIMIT_DB
    assert emission.check_turbine_test_environment(correction).passes
    levels, background = _levels()
    result = emission.turbine_sound_power(
        levels,
        surface_area_m2=100.0,
        background_levels_db=background,
        environmental_correction_db=correction.environmental_correction_db,
    )
    assert result.conforms


def test_the_check_takes_a_correction_or_a_bare_k_but_not_both() -> None:
    room = emission.turbine_environmental_correction(100.0, absorption_area_m2=400.0)
    with pytest.raises(ValueError, match="one of the two"):
        emission.check_turbine_test_environment(room, environmental_correction_db=1.0)


def test_the_check_needs_a_correction() -> None:
    with pytest.raises(ValueError, match="one of the two"):
        emission.check_turbine_test_environment()


def test_the_check_refuses_a_bare_k_in_place_of_a_correction() -> None:
    with pytest.raises(ValueError, match="environmental_correction_db"):
        emission.check_turbine_test_environment(2.0)  # type: ignore[arg-type]


def test_the_a_over_s_bound_and_the_seven_decibels_agree_to_the_decibel() -> None:
    ratio_at_limit = 4.0 / (10.0 ** (oracle.IEC61063_K_LIMIT_DB / 10.0) - 1.0)
    assert ratio_at_limit == pytest.approx(oracle.IEC61063_MINIMUM_RATIO, abs=0.003)
    check = emission.check_turbine_test_environment(
        emission.turbine_environmental_correction(100.0, absorption_area_m2=100.0)
    )
    assert check.passes
    assert check.ratio == 1.0


@pytest.mark.parametrize(
    ("wind", "ok", "screen"),
    [
        (0.5, True, False),
        (1.0, True, False),
        (1.5, True, True),
        (5.99, True, True),
        (6.0, False, True),
    ],
)
def test_the_wind_outdoors(wind: float, *, ok: bool, screen: bool) -> None:
    check = emission.check_turbine_test_environment(
        environmental_correction_db=0.0, wind_speed_m_s=wind
    )
    assert check.wind_ok is ok
    assert check.windscreen_advised is screen
    assert check.passes is ok


def test_a_check_has_no_truth_value() -> None:
    check = emission.check_turbine_test_environment(environmental_correction_db=2.0)
    with pytest.raises(TypeError, match="passes"):
        bool(check)


# --- Equations (2) and (3) ---------------------------------------------------


def _levels() -> tuple[np.ndarray, np.ndarray]:
    levels = np.array([88.0, 90.0, 91.0, 89.5, 92.0, 90.5])
    background = levels - np.array([12.0, 7.0, 4.0, 9.3, 20.0, 5.6])
    return levels, background


def test_equations_2_and_3_by_hand() -> None:
    levels, background = _levels()
    result = emission.turbine_sound_power(
        levels,
        surface_area_m2=410.1,
        background_levels_db=background,
        environmental_correction_db=2.0,
    )
    # Table 2 at 12, 7, 4, 9,3, 20 and 5,6 dB: 0, 1, 2, 0,5, 0 and 1 dB.
    corrections = np.array([0.0, 1.0, 2.0, 0.5, 0.0, 1.0])
    np.testing.assert_array_equal(result.background_corrections_db, corrections)
    surface = _energy_mean(levels - corrections) - 2.0
    assert result.surface_pressure_level_db == pytest.approx(surface, abs=1e-12)
    assert result.sound_power_level_db == pytest.approx(
        surface + 10.0 * math.log10(410.1), abs=1e-12
    )
    assert result.conforms
    assert not result.upper_limit


def test_without_a_background_no_correction_is_applied() -> None:
    levels, _ = _levels()
    result = emission.turbine_sound_power(
        levels,
        surface_area_m2=100.0,
        background_levels_db=None,
        environmental_correction_db=0.0,
    )
    assert result.level_differences_db is None
    np.testing.assert_array_equal(result.corrected_levels_db, levels)
    assert result.sound_power_level_db == pytest.approx(_energy_mean(levels) + 20.0)


def test_a_background_within_three_decibels_is_an_upper_limit() -> None:
    levels, background = _levels()
    background[0] = levels[0] - 2.0
    with pytest.warns(SoundPowerWarning, match="upper limit"):
        result = emission.turbine_sound_power(
            levels,
            surface_area_m2=100.0,
            background_levels_db=background,
            environmental_correction_db=0.0,
        )
    assert result.upper_limit
    assert result.limited_positions is not None
    np.testing.assert_array_equal(
        result.limited_positions, [True, False, False, False, False, False]
    )
    assert not result.conforms
    assert result.background_corrections_db[0] == 3.0


def test_a_background_3_db_below_in_decimal_readings_is_valid() -> None:
    """32,3 - 29,3 dB is 2,999 999 999 999 996 in binary: 3 dB, at the criterion."""
    levels = np.array([32.3, 40.0, 40.0, 40.0, 40.0])
    background = np.array([29.3, 20.0, 20.0, 20.0, 20.0])
    with warnings.catch_warnings():
        warnings.simplefilter("error", SoundPowerWarning)
        result = emission.turbine_sound_power(
            levels,
            surface_area_m2=100.0,
            background_levels_db=background,
            environmental_correction_db=0.0,
        )
    assert result.level_differences_db is not None
    assert result.level_differences_db[0] < oracle.IEC61063_BACKGROUND_CRITERION_DB
    assert not result.upper_limit
    assert result.conforms


def test_seven_decibels_exactly_conforms_and_is_reported() -> None:
    """8.3 and A.3.3 allow K up to 7 dB: at 7 dB the report accepts it."""
    levels, background = _levels()
    result = emission.turbine_sound_power(
        levels,
        surface_area_m2=100.0,
        background_levels_db=background,
        environmental_correction_db=oracle.IEC61063_K_LIMIT_DB,
    )
    assert result.conforms
    declaration = emission.turbine_noise_declaration(
        {"rated": result},
        turbine="set",
        noise_control="none",
        measured_at="today",
        tonal=False,
    )
    assert declaration.reported_sound_power_levels_db == (
        result.reported_sound_power_level_db,
    )
    assert declaration.sound_power_levels_db == (result.sound_power_level_db,)


def test_a_room_beyond_seven_decibels_is_reported() -> None:
    levels, background = _levels()
    with pytest.warns(SoundPowerWarning, match="7 dB"):
        result = emission.turbine_sound_power(
            levels,
            surface_area_m2=100.0,
            background_levels_db=background,
            environmental_correction_db=7.5,
        )
    assert not result.conforms


def test_the_level_is_reported_to_the_whole_decibel_halves_up() -> None:
    levels = np.full(5, 90.0)
    result = emission.turbine_sound_power(
        levels,
        surface_area_m2=10.0**2.25,  # 10 lg S = 22,5 dB
        background_levels_db=None,
        environmental_correction_db=0.0,
    )
    assert result.sound_power_level_db == pytest.approx(112.5)
    assert result.reported_sound_power_level_db == 113.0


def test_a_half_a_hair_under_in_binary_still_rounds_up() -> None:
    """80,2 - 0,7 + 20 dB is 99,5 dB, and 99,499 999 999 999 99 in binary."""
    result = emission.turbine_sound_power(
        np.full(4, 80.2),
        surface_area_m2=100.0,
        background_levels_db=None,
        environmental_correction_db=0.7,
    )
    assert result.sound_power_level_db < 99.5
    assert result.sound_power_level_db == pytest.approx(99.5, abs=1e-12)
    assert result.reported_sound_power_level_db == 100.0


def test_the_arithmetic_average_of_the_note_of_8_3() -> None:
    levels = np.array([88.0, 89.0, 90.0, 91.0, 92.0])
    result = emission.turbine_sound_power(
        levels,
        surface_area_m2=100.0,
        background_levels_db=None,
        environmental_correction_db=1.0,
    )
    assert result.level_range_db == 4.0
    assert result.arithmetic_mean_allowed
    assert result.arithmetic_mean_db == pytest.approx(89.0)
    assert 0.0 < result.surface_pressure_level_db - result.arithmetic_mean_db <= 0.7


def test_the_arithmetic_average_at_a_range_of_exactly_five_decibels() -> None:
    """The NOTE of 8.3 applies when the range "does not exceed 5 dB"."""
    levels = np.array([90.0, 91.0, 93.0, 95.0])
    result = emission.turbine_sound_power(
        levels,
        surface_area_m2=100.0,
        background_levels_db=None,
        environmental_correction_db=0.0,
    )
    assert result.level_range_db == oracle.IEC61063_ARITHMETIC_RANGE_DB
    assert result.arithmetic_mean_allowed
    wider = emission.turbine_sound_power(
        np.array([90.0, 91.0, 93.0, 95.01]),
        surface_area_m2=100.0,
        background_levels_db=None,
        environmental_correction_db=0.0,
    )
    assert not wider.arithmetic_mean_allowed


def test_a_range_of_five_decibels_in_decimal_readings_is_within_the_note() -> None:
    """20,1 - 15,1 dB is 5,000 000 000 000 002 in binary: 5 dB, not above it."""
    result = emission.turbine_sound_power(
        np.array([15.1, 17.0, 18.0, 20.1]),
        surface_area_m2=100.0,
        background_levels_db=None,
        environmental_correction_db=0.0,
    )
    assert result.level_range_db > oracle.IEC61063_ARITHMETIC_RANGE_DB
    assert result.arithmetic_mean_allowed


def test_the_worst_case_of_the_note_of_8_3_is_seven_tenths_rounded() -> None:
    """Two levels 5 dB apart, the louder at 40,6 % of the positions: 0,707 dB.

    For a fixed range the energy average leads the arithmetic one most when
    the levels sit at the two ends of the range, so this is the largest
    departure the NOTE can meet; it prints it to one decimal.
    """
    worst = 0.0
    for louder in range(1, 1000):
        levels = np.r_[np.full(louder, 5.0), np.zeros(1000 - louder)]
        worst = max(worst, _energy_mean(levels) - float(np.mean(levels)))
    assert worst == pytest.approx(0.7067, abs=5e-4)
    assert round(worst, 1) == oracle.IEC61063_ARITHMETIC_DEVIATION_DB


def test_overhead_positions_and_their_effect() -> None:
    levels = np.array([90.0, 90.0, 90.0, 90.0, 93.0, 93.0])
    mask = np.array([False, False, False, False, True, True])
    result = emission.turbine_sound_power(
        levels,
        surface_area_m2=100.0,
        background_levels_db=None,
        environmental_correction_db=0.0,
        overhead_mask=mask,
    )
    effect = _energy_mean(levels) - 90.0
    assert result.overhead_effect_db == pytest.approx(effect)
    assert result.overhead_may_be_deleted is (effect <= 1.0)


def _overhead_effect(overhead_db: float) -> emission.TurbineSoundPowerResult:
    """Four positions at 80 dB and one overhead position."""
    return emission.turbine_sound_power(
        np.array([80.0, 80.0, 80.0, 80.0, overhead_db]),
        surface_area_m2=100.0,
        background_levels_db=None,
        environmental_correction_db=0.0,
        overhead_mask=np.array([False, False, False, False, True]),
    )


def _overhead_level(effect_db: float) -> float:
    """The overhead level that moves four at 80 dB by ``effect_db``.

    The closed form, 80 + 10 lg(5 x 10^(effect/10) - 4) dB.
    """
    return 80.0 + 10.0 * math.log10(5.0 * 10.0 ** (effect_db / 10.0) - 4.0)


def test_overhead_positions_moving_the_level_by_exactly_1_0_db_may_go() -> None:
    """The NOTE of 7.2.2: "not ... by more than 1,0 dB", so 1,0 dB itself is in.

    The effect is the difference of two energy means near 80 dB, so at 1,0 dB
    it comes out a unit or two of their last place either side of it, which
    side depending on the machine; it is judged on the limit either way, and
    a micro-decibel past it is past.
    """
    limit = oracle.IEC61063_OVERHEAD_EFFECT_DB
    at_limit = _overhead_effect(_overhead_level(limit))
    assert at_limit.overhead_effect_db == pytest.approx(limit, abs=1e-12)
    assert at_limit.overhead_may_be_deleted is True
    past = _overhead_effect(_overhead_level(limit + 1e-6))
    assert past.overhead_effect_db == pytest.approx(limit + 1e-6, abs=1e-12)
    assert past.overhead_may_be_deleted is False


@pytest.mark.parametrize("steps", range(-8, 9))
def test_the_overhead_verdict_does_not_turn_on_the_last_bits(steps: int) -> None:
    """Every overhead level a few floating-point steps round 1,0 dB is on it."""
    level = _overhead_level(oracle.IEC61063_OVERHEAD_EFFECT_DB)
    for _ in range(abs(steps)):
        level = float(np.nextafter(level, np.inf if steps > 0 else -np.inf))
    assert _overhead_effect(level).overhead_may_be_deleted is True


def test_determination_refuses_fewer_than_four_positions() -> None:
    levels = [90.0, 91.0, 92.0]
    with pytest.raises(ValueError, match="at least 4"):
        emission.turbine_sound_power(
            levels,
            surface_area_m2=100.0,
            background_levels_db=None,
            environmental_correction_db=0.0,
        )


def test_determination_refuses_a_background_of_another_length() -> None:
    levels, background = _levels()
    with pytest.raises(ValueError, match="background_levels_db"):
        emission.turbine_sound_power(
            levels,
            surface_area_m2=100.0,
            background_levels_db=background[:-1],
            environmental_correction_db=0.0,
        )


def test_result_arrays_are_read_only_and_not_the_callers() -> None:
    levels, background = _levels()
    result = emission.turbine_sound_power(
        levels,
        surface_area_m2=100.0,
        background_levels_db=background,
        environmental_correction_db=0.0,
    )
    levels[0] = 0.0
    assert result.pressure_levels_db[0] == 88.0
    with pytest.raises(ValueError, match="read-only"):
        result.corrected_levels_db[0] = 1.0


# --- The report, clauses 9 and 10 -------------------------------------------


def _result(offset: float) -> emission.TurbineSoundPowerResult:
    levels, background = _levels()
    return emission.turbine_sound_power(
        levels + offset,
        surface_area_m2=410.1,
        background_levels_db=background + offset,
        environmental_correction_db=2.0,
    )


def test_the_report_of_clause_10() -> None:
    declaration = emission.turbine_noise_declaration(
        {"50 % rated load": _result(-2.0), "100 % rated load": _result(0.0)},
        turbine="Three-casing set, 60 MW",
        noise_control="none",
        measured_at="2026-09-25 10:30",
        tonal=True,
    )
    assert declaration.operating_conditions == ("50 % rated load", "100 % rated load")
    assert declaration.reported_sound_power_levels_db == (
        _result(-2.0).reported_sound_power_level_db,
        _result(0.0).reported_sound_power_level_db,
    )
    assert declaration.sound_power_levels_db == (
        _result(-2.0).sound_power_level_db,
        _result(0.0).sound_power_level_db,
    )
    assert declaration.loudest_condition == "100 % rated load"
    assert declaration.standard_deviation_db == oracle.IEC61063_TABLE_1_DB["tonal"]
    assert "full conformity" in declaration.statement
    assert "1 pW" in declaration.statement


def _uniform(level_db: float) -> emission.TurbineSoundPowerResult:
    """Six equal levels over 100 m², outdoors: L_WA = level + 20 dB exactly."""
    return emission.turbine_sound_power(
        np.full(6, level_db),
        surface_area_m2=100.0,
        background_levels_db=None,
        environmental_correction_db=0.0,
    )


def test_the_loudest_condition_is_found_before_rounding() -> None:
    """6.2 looks for the noisiest load, 9.4 g only rounds what is reported.

    105,6 dB and 106,4 dB both report as 106 dB; the 75 % load is still the
    louder of the two, though the 100 % load is listed first.
    """
    declaration = emission.turbine_noise_declaration(
        {"100 % load": _uniform(85.6), "75 % load": _uniform(86.4)},
        turbine="set",
        noise_control="none",
        measured_at="today",
        tonal=False,
    )
    assert declaration.reported_sound_power_levels_db == (106.0, 106.0)
    assert declaration.sound_power_levels_db == pytest.approx((105.6, 106.4), abs=1e-9)
    assert declaration.loudest_condition == "75 % load"
    ax = declaration.plot()
    assert [bar.get_height() for bar in ax.patches] == [106.0, 106.0]
    assert ax.get_title().endswith("75 % load")
    plt.close("all")


def test_an_exact_tie_names_the_first_condition_listed() -> None:
    declaration = emission.turbine_noise_declaration(
        {"50 % load": _uniform(86.0), "100 % load": _uniform(86.0)},
        turbine="set",
        noise_control="none",
        measured_at="today",
        tonal=False,
    )
    assert declaration.loudest_condition == "50 % load"


def test_the_reported_levels_round_half_up() -> None:
    """9.4 g: to the nearest whole decibel, a half going up."""
    declaration = emission.turbine_noise_declaration(
        {"a": _uniform(85.5), "b": _uniform(86.49)},
        turbine="set",
        noise_control="none",
        measured_at="today",
        tonal=False,
    )
    assert declaration.reported_sound_power_levels_db == (106.0, 106.0)
    assert declaration.loudest_condition == "b"


def test_the_report_carries_the_corrected_levels_and_the_surface_level() -> None:
    """Clause 10 c) and d): the levels after Table 2, and Equation (2) with K."""
    levels, _ = _levels()
    declaration = emission.turbine_noise_declaration(
        {"rated": _result(0.0)},
        turbine="set",
        noise_control="none",
        measured_at="today",
        tonal=False,
    )
    # Table 2 at 12, 7, 4, 9,3, 20 and 5,6 dB takes 0, 1, 2, 0,5, 0 and 1 dB.
    corrected = levels - np.array([0.0, 1.0, 2.0, 0.5, 0.0, 1.0])
    np.testing.assert_allclose(declaration.position_levels_db[0], corrected, atol=1e-12)
    assert declaration.surface_pressure_levels_db[0] == pytest.approx(
        _energy_mean(corrected) - 2.0, abs=1e-12
    )


def test_table_1_broadband() -> None:
    declaration = emission.turbine_noise_declaration(
        {"rated": _result(0.0)},
        turbine="set",
        noise_control="none",
        measured_at="today",
        tonal=False,
    )
    assert declaration.standard_deviation_db == oracle.IEC61063_TABLE_1_DB["broadband"]


def test_the_report_refuses_an_upper_limit() -> None:
    levels, background = _levels()
    background[0] = levels[0] - 1.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SoundPowerWarning)
        upper = emission.turbine_sound_power(
            levels,
            surface_area_m2=100.0,
            background_levels_db=background,
            environmental_correction_db=0.0,
        )
    determinations = {"rated": upper}
    with pytest.raises(ValueError, match="full conformity"):
        emission.turbine_noise_declaration(
            determinations,
            turbine="set",
            noise_control="none",
            measured_at="today",
            tonal=False,
        )


def test_the_report_refuses_an_empty_description() -> None:
    determinations = {"rated": _result(0.0)}
    with pytest.raises(ValueError, match="turbine"):
        emission.turbine_noise_declaration(
            determinations,
            turbine=" ",
            noise_control="none",
            measured_at="today",
            tonal=False,
        )


# --- The figures -------------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_layout_draws_every_key_position_with_its_number(language: str) -> None:
    array = _large_array()
    ax = array.plot(language=language)
    numbers = sorted(text.get_text() for text in ax.texts if text.get_text().isdigit())
    assert numbers == ["1", "2", "3", "4", "5"]
    plt.close("all")


def test_the_elevation_shows_the_near_side_and_the_top() -> None:
    """Both elevations of Figure 2 are seen from the side of key position 4."""
    array = _large_array()
    ax = array.plot(view="elevation")
    numbers = sorted(text.get_text() for text in ax.texts if text.get_text().isdigit())
    assert numbers == ["1", "3", "4", "5"]
    plt.close("all")


def test_the_layout_refuses_an_unknown_view() -> None:
    surface = emission.turbine_measurement_surface(LARGE_SET)
    with pytest.raises(ValueError, match="view"):
        surface.plot(view="section")  # type: ignore[arg-type]


def test_figure_a3_draws_the_limit_and_the_room() -> None:
    correction = emission.turbine_environmental_correction(
        400.0, absorption_area_m2=2000.0
    )
    ax = emission.check_turbine_test_environment(correction).plot()
    ys = [line.get_ydata() for line in ax.lines]
    assert any(np.allclose(y, 7.0) for y in ys)
    assert any(
        np.allclose(y, correction.environmental_correction_db) and len(y) == 1
        for y in ys
    )
    assert ax.get_xscale() == "log"
    plt.close("all")


@pytest.mark.parametrize(
    ("language", "labels"),
    [
        ("en", ["0.5", "1", "5", "10", "50", "100", "300"]),
        ("es", ["0,5", "1", "5", "10", "50", "100", "300"]),
    ],
)
def test_figure_a3_labels_its_axis_as_the_figure_does(
    language: str, labels: list[str]
) -> None:
    correction = emission.turbine_environmental_correction(
        400.0, absorption_area_m2=2000.0
    )
    ax = correction.plot(language=language)
    ax.figure.canvas.draw()
    shown = [tick.get_text() for tick in ax.get_xticklabels() if tick.get_text()]
    assert shown == labels
    plt.close("all")


def test_the_determination_draws_one_bar_per_position() -> None:
    result = _result(0.0)
    ax = result.plot()
    assert len(ax.patches) == 6
    heights = sorted(bar.get_height() for bar in ax.patches)
    np.testing.assert_allclose(heights, sorted(result.corrected_levels_db))
    assert ax.get_xlim() == (0.5, 6.5)
    plt.close("all")


def test_the_determination_names_the_key_positions_it_is_given() -> None:
    """With the array's labels the axis numbers only the key bars, as Figure 2."""
    labels = ("1", "", "2", "5", "4", "")
    ax = _result(0.0).plot(position_labels=labels)
    ax.figure.canvas.draw()
    ticks = [
        (tick.get_loc(), tick.label1.get_text()) for tick in ax.xaxis.get_major_ticks()
    ]
    assert ticks == [(1.0, "1"), (3.0, "2"), (4.0, "5"), (5.0, "4")]
    plt.close("all")


def test_the_determination_refuses_labels_of_another_length() -> None:
    result = _result(0.0)
    with pytest.raises(ValueError, match="position_labels"):
        result.plot(position_labels=("1", "2"))


def test_the_report_draws_one_bar_per_condition() -> None:
    declaration = emission.turbine_noise_declaration(
        {"25 %": _result(-6.0), "100 %": _result(0.0)},
        turbine="set",
        noise_control="none",
        measured_at="today",
        tonal=False,
    )
    ax = declaration.plot(language="es")
    assert [bar.get_height() for bar in ax.patches] == list(
        declaration.reported_sound_power_levels_db
    )
    assert ax.get_title().endswith("condición más ruidosa, 100 %")
    ax.figure.canvas.draw()
    assert not any(line.get_visible() for line in ax.get_xgridlines())
    plt.close("all")
