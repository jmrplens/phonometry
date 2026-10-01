#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 62489-1:2010 with Amendment 1:2014: the loop, its amplifier, the neck loop."""

from __future__ import annotations

import math
from types import MappingProxyType

import numpy as np
import pytest
import reference_data as ref

import phonometry as ph

ea = ph.electroacoustics
MU_0 = 4e-7 * math.pi


# ---------------------------------------------------------------------------
# The field of a rectangular loop
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("side", [0.75, 1.0, 5.0, 12.0])
def test_biot_savart_reproduces_the_e1_formula_for_a_square(side: float) -> None:
    field = ea.rectangular_loop_field(2.0, side, side, 0.0, 0.0, 0.0)
    expected = 2.0 * math.sqrt(2.0) * 2.0 / (math.pi * side)
    assert float(field.h_z_a_per_m) == pytest.approx(expected, rel=1e-12)
    assert ea.loop_centre_field(2.0, side) == pytest.approx(expected, rel=1e-12)


def test_e1_rectangle_approximation_against_the_exact_field() -> None:
    d1, d2 = 15.0, 10.0
    exact = float(ea.rectangular_loop_field(1.0, d1, d2, 0.0, 0.0, 0.0).h_z_a_per_m)
    approx = ea.loop_centre_field(1.0, d1, width_m=d2)
    ratio = math.sqrt((d1**2 + d2**2) / (2.0 * d1 * d2))
    assert exact / approx == pytest.approx(ratio, rel=1e-12)
    assert 20 * math.log10(ratio) == pytest.approx(0.35, abs=0.01)


def test_on_axis_field_matches_the_closed_form() -> None:
    a, b, z = 3.0, 2.0, 1.4
    field = ea.rectangular_loop_field(1.0, 2 * a, 2 * b, 0.0, 0.0, z)
    closed = (
        a
        * b
        / (math.pi * math.sqrt(a * a + b * b + z * z))
        * (1.0 / (a * a + z * z) + 1.0 / (b * b + z * z))
    )
    assert float(field.h_z_a_per_m) == pytest.approx(closed, rel=1e-12)
    assert float(field.h_x_a_per_m) == pytest.approx(0.0, abs=1e-15)


def test_far_on_axis_the_loop_is_a_dipole() -> None:
    length, width, z = 1.0, 0.5, 200.0
    field = ea.rectangular_loop_field(3.0, length, width, 0.0, 0.0, z, turns=2)
    moment = 2 * 3.0 * length * width
    assert float(field.h_z_a_per_m) == pytest.approx(
        moment / (2.0 * math.pi * z**3), rel=1e-4
    )


def test_field_is_symmetric_and_turns_scale_it() -> None:
    x = np.array([-2.0, -1.0, 1.0, 2.0])
    one = ea.rectangular_loop_field(1.0, 6.0, 4.0, x, 0.5, 1.2)
    three = ea.rectangular_loop_field(1.0, 6.0, 4.0, x, 0.5, 1.2, turns=3)
    np.testing.assert_allclose(one.h_z_a_per_m, one.h_z_a_per_m[::-1], rtol=1e-12)
    np.testing.assert_allclose(one.h_x_a_per_m, -one.h_x_a_per_m[::-1], rtol=1e-12)
    np.testing.assert_allclose(three.h_z_a_per_m, 3.0 * one.h_z_a_per_m, rtol=1e-12)


def test_null_line_lies_outside_the_perimeter() -> None:
    # Figure E.1: the vertical component vanishes a little outside the loop.
    x = np.linspace(2.9, 4.0, 2201)
    field = ea.rectangular_loop_field(1.0, 6.0, 6.0, x, 0.0, 0.6)
    crossing = x[np.flatnonzero(np.diff(np.sign(field.h_z_a_per_m)))[0]]
    assert 3.0 < crossing < 4.0


def test_field_levels_and_the_magnitude() -> None:
    field = ea.rectangular_loop_field(1.0, 5.0, 5.0, [0.0, 1.0], 0.0, 1.4)
    np.testing.assert_allclose(
        field.level_db("z"), 20 * np.log10(np.abs(field.h_z_a_per_m) / 0.4), rtol=1e-12
    )
    np.testing.assert_allclose(
        field.magnitude_a_per_m,
        np.sqrt(field.h_x_a_per_m**2 + field.h_y_a_per_m**2 + field.h_z_a_per_m**2),
    )


def test_field_arrays_are_read_only() -> None:
    field = ea.rectangular_loop_field(1.0, 5.0, 5.0, [0.0, 1.0], 0.0, 1.4)
    with pytest.raises(ValueError, match="read-only"):
        field.h_z_a_per_m[0] = 0.0


def test_point_on_the_conductor_is_refused() -> None:
    with pytest.raises(ValueError, match="conductor"):
        ea.rectangular_loop_field(1.0, 4.0, 2.0, 0.5, -1.0, 0.0)


def test_corner_of_the_loop_is_refused() -> None:
    with pytest.raises(ValueError, match="conductor"):
        ea.rectangular_loop_field(1.0, 4.0, 2.0, 2.0, 1.0, 0.0)


def test_coordinates_have_to_broadcast() -> None:
    with pytest.raises(ValueError, match="broadcast"):
        ea.rectangular_loop_field(1.0, 4.0, 2.0, [0.0, 1.0], [0.0, 1.0, 2.0], 1.0)


def _figure_e2_level(component: str, position_percent: float) -> float:
    """The level of Figure E.2 b): across the width, re the centre in the plane."""
    length, width, height = ref.IEC60118_4_FIGURE_E2B_LOOP
    y = position_percent / 100.0 * width - width / 2.0
    field = ea.rectangular_loop_field(1.0, length, width, 0.0, y, height)
    centre = ea.rectangular_loop_field(1.0, length, width, 0.0, 0.0, 0.0)
    value = field.h_z_a_per_m if component == "vertical" else field.h_y_a_per_m
    return 20.0 * math.log10(abs(float(value)) / float(centre.h_z_a_per_m))


@pytest.mark.parametrize(
    ("component", "position"), sorted(ref.IEC60118_4_FIGURE_E2B_DB)
)
def test_biot_savart_reproduces_the_curves_of_figure_e2_b(
    component: str, position: float
) -> None:
    printed = ref.IEC60118_4_FIGURE_E2B_DB[(component, position)]
    assert _figure_e2_level(component, position) == pytest.approx(printed, abs=0.5)


def test_figure_e2_vertical_curve_is_not_the_traverse_along_the_length() -> None:
    # Figure E.2 a) labels the vertical field along the 15-unit length; there
    # the vertical component at 5 % reads +1,8 dB where the printed curve,
    # the traverse across the width, reads below 0 dB.
    length, width, height = ref.IEC60118_4_FIGURE_E2B_LOOP
    along = ea.rectangular_loop_field(1.0, length, width, -0.45 * length, 0.0, height)
    centre = ea.rectangular_loop_field(1.0, length, width, 0.0, 0.0, 0.0)
    level = 20.0 * math.log10(float(along.h_z_a_per_m) / float(centre.h_z_a_per_m))
    assert level == pytest.approx(1.76, abs=0.01)
    assert _figure_e2_level("vertical", 5.0) < 0.0


# ---------------------------------------------------------------------------
# Current and dimensions (IEC 62489-1 5.4.10 and 5.4.11)
# ---------------------------------------------------------------------------


def test_loop_current_reaches_400_ma_per_m_at_1_4_m() -> None:
    current = ea.loop_current(10.0, 10.0)
    field = ea.rectangular_loop_field(current, 10.0, 10.0, 0.0, 0.0, 1.4)
    assert float(field.h_z_a_per_m) == pytest.approx(0.4, rel=1e-12)


def test_loop_current_default_height_is_the_one_of_5_4_10_2() -> None:
    assert ea.loop_current(8.0, 6.0) == pytest.approx(
        ea.loop_current(8.0, 6.0, height_m=ref.IEC62489_1_FIELD_HEIGHT_M)
    )


@pytest.mark.parametrize(
    ("length", "width", "turns"), [(20.0, 10.0, 1), (6.0, 2.0, 3), (30.0, 10.0, 1)]
)
def test_loop_current_of_a_rectangle_against_biot_savart(
    length: float, width: float, turns: int
) -> None:
    current = ea.loop_current(length, width, turns=turns)
    field = ea.rectangular_loop_field(
        current, length, width, 0.0, 0.0, 1.4, turns=turns
    )
    assert float(field.h_z_a_per_m) == pytest.approx(0.4, rel=1e-12)


def test_loop_current_divides_by_the_turns() -> None:
    assert ea.loop_current(8.0, 6.0, turns=4) == pytest.approx(
        ea.loop_current(8.0, 6.0) / 4.0, rel=1e-12
    )


@pytest.mark.parametrize("aspect", sorted(ref.IEC60118_4_FIGURE_H1_AT_10_M_A))
def test_loop_current_reproduces_figure_h1(aspect: float) -> None:
    printed = ref.IEC60118_4_FIGURE_H1_AT_10_M_A[aspect]
    assert ea.loop_current(10.0 * aspect, 10.0) == pytest.approx(printed, abs=0.03)


@pytest.mark.parametrize(("aspect", "turns"), [(1.0, 1), (3.0, 1), (3.0, 2)])
def test_loop_dimensions_against_biot_savart(aspect: float, turns: int) -> None:
    short, long = ea.loop_dimensions(5.0, aspect_ratio=aspect, turns=turns)
    field = ea.rectangular_loop_field(5.0, long, short, 0.0, 0.0, 1.4, turns=turns)
    assert float(field.h_z_a_per_m) == pytest.approx(0.4, rel=1e-9)


@pytest.mark.parametrize("aspect", [1.0, 3.0])
def test_loop_dimensions_invert_the_loop_current(aspect: float) -> None:
    short, long = ea.loop_dimensions(5.0, aspect_ratio=aspect)
    assert long == pytest.approx(aspect * short)
    assert ea.loop_current(long, short) == pytest.approx(5.0, rel=1e-9)


def test_loop_dimensions_take_the_larger_branch() -> None:
    short, _ = ea.loop_dimensions(4.0)
    smaller = 0.5 * short
    assert ea.loop_current(smaller, smaller) < 4.0


def test_loop_dimensions_refuse_an_unreachable_field() -> None:
    with pytest.raises(ValueError, match="any size"):
        ea.loop_dimensions(0.5)


def test_loop_dimensions_refuse_an_aspect_below_one() -> None:
    with pytest.raises(ValueError, match="aspect_ratio"):
        ea.loop_dimensions(5.0, aspect_ratio=0.5)


# ---------------------------------------------------------------------------
# The loop as a load (Annex B)
# ---------------------------------------------------------------------------


def _perimeter(dims: tuple[float, ...]) -> float:
    return math.pi * dims[0] if len(dims) == 1 else 2.0 * (dims[0] + dims[1])


@pytest.mark.parametrize(
    "row", ref.IEC62489_1_TABLE_B1, ids=[r[0] for r in ref.IEC62489_1_TABLE_B1]
)
def test_table_b1_resistance(row: tuple) -> None:
    _, dims, turns, _, area, resistance, *_ = row
    computed = ea.loop_resistance(_perimeter(dims), area, turns=turns)
    assert round(computed, 2) == pytest.approx(resistance)


def test_counter_loop_perimeter_is_misprinted() -> None:
    _, dims, turns, printed, area, resistance, *_ = ref.IEC62489_1_TABLE_B1[1]
    assert _perimeter(dims) == pytest.approx(1.6)
    assert printed == pytest.approx(1.5)
    assert round(ea.loop_resistance(printed, area, turns=turns), 2) != pytest.approx(
        resistance
    )


def test_copper_resistivity_and_its_temperature_coefficient() -> None:
    at_20 = ea.loop_resistance(1.0, 1.0)
    assert at_20 == pytest.approx(ref.IEC60028_COPPER_OHM_MM2_PER_M, rel=1e-12)
    at_25 = ea.loop_resistance(1.0, 1.0, conductor_temperature_c=25.0)
    assert at_25 / at_20 == pytest.approx(1.0 + 5.0 * ref.IEC60028_COPPER_ALPHA_PER_K)


def test_e3_resistance_of_a_square_loop() -> None:
    side, area_mm2 = 5.0, 1.5
    rho = ref.IEC60028_COPPER_OHM_MM2_PER_M * 1e-6
    assert ea.loop_resistance(4 * side, area_mm2) == pytest.approx(
        4 * rho * side / (area_mm2 * 1e-6), rel=1e-12
    )


@pytest.mark.parametrize(
    "row",
    [
        r
        for r in ref.IEC62489_1_TABLE_B1
        if r[0] in ref.IEC62489_1_TABLE_B1_INDUCTANCE_REPRODUCED
    ],
    ids=list(ref.IEC62489_1_TABLE_B1_INDUCTANCE_REPRODUCED),
)
def test_table_b1_inductance_without_the_internal_term(row: tuple) -> None:
    _, dims, turns, _, area, _, inductance, *_ = row
    computed = ea.rectangular_loop_inductance(
        dims[0], dims[1], area, turns=turns, internal_inductance=False
    )
    assert round(computed * 1e6) == pytest.approx(inductance)


def test_internal_term_adds_mu0_over_8_pi_per_metre_of_wire() -> None:
    external = ea.rectangular_loop_inductance(6.0, 8.0, 1.5, internal_inductance=False)
    total = ea.rectangular_loop_inductance(6.0, 8.0, 1.5)
    assert total - external == pytest.approx(MU_0 / (8 * math.pi) * 28.0, rel=1e-12)


def test_grover_square_is_formula_60() -> None:
    side, area = 5.0, 1.5
    radius = math.sqrt(area * 1e-6 / math.pi)
    formula_60 = MU_0 / math.pi * 2 * side * (math.log(side / radius) - 0.77401 + 0.25)
    assert ea.rectangular_loop_inductance(side, side, area) == pytest.approx(
        formula_60, rel=1e-6
    )


def test_inductance_refuses_a_thick_wire() -> None:
    with pytest.raises(ValueError, match="thin"):
        ea.rectangular_loop_inductance(0.01, 0.01, 10.0)


@pytest.mark.parametrize(
    "row", ref.IEC62489_1_TABLE_B1, ids=[r[0] for r in ref.IEC62489_1_TABLE_B1]
)
def test_table_b1_impedances_follow_from_its_rounded_r_and_l(row: tuple) -> None:
    *_, resistance, inductance, z2k, z5k = row
    # The printed R and L are rounded to 0,01 ohm and 1 microhenry; the
    # printed impedances lie within what that rounding allows, plus their own.
    corners = [
        ea.loop_impedance(resistance + dr, (inductance + dl) * 1e-6)
        for dr in (-0.005, 0.005)
        for dl in (-0.5, 0.5)
    ]
    for frequency, printed in ((2000.0, z2k), (5000.0, z5k)):
        values = [float(z.at(frequency)) for z in corners]
        assert min(values) - 0.005 <= printed <= max(values) + 0.005


def test_impedance_is_sqrt2_times_resistance_at_the_corner() -> None:
    z = ea.loop_impedance(0.69, 109e-6)
    corner = z.corner_frequency_hz
    assert corner == pytest.approx(0.69 / (2 * math.pi * 109e-6))
    assert float(z.at(corner)) / 0.69 == pytest.approx(math.sqrt(2.0))
    assert round(math.sqrt(2.0), 1) == pytest.approx(ref.IEC60118_4_E3_CORNER_FACTOR)


def test_drive_voltage_is_e3_u_h() -> None:
    z = ea.loop_impedance(0.69, 109e-6)
    expected = 3.0 * math.hypot(0.69, 2 * math.pi * 2000.0 * 109e-6)
    assert float(z.drive_voltage(3.0, 2000.0)) == pytest.approx(expected)


def test_impedance_default_frequencies_are_third_octaves() -> None:
    z = ea.loop_impedance(0.5, 50e-6)
    assert z.frequencies_hz[0] == pytest.approx(50.0)
    assert z.frequencies_hz[-1] == pytest.approx(10000.0)
    with pytest.raises(ValueError, match="read-only"):
        z.impedance_ohm[0] = 0.0


# ---------------------------------------------------------------------------
# The amplifier (clause 5)
# ---------------------------------------------------------------------------


def test_compliance_voltage_of_a_sine_is_its_rms() -> None:
    t = np.arange(4800) / 48000
    v = 10.0 * np.sin(2 * np.pi * 1000 * t)
    assert ea.compliance_voltage(v) == pytest.approx(10.0 / math.sqrt(2.0), rel=1e-9)


def test_compliance_voltage_averages_unequal_peaks() -> None:
    assert ea.compliance_voltage([0.0, 12.0, -8.0, 3.0]) == pytest.approx(
        10.0 / math.sqrt(2.0)
    )


def test_compliance_voltage_needs_both_polarities() -> None:
    with pytest.raises(ValueError, match="both ways"):
        ea.compliance_voltage([0.0, 1.0, 2.0])


def test_equivalent_input_noise_and_signal_to_noise_ratio() -> None:
    assert ea.equivalent_input_noise_voltage(0.1, 2.0, 1e-4) == pytest.approx(5e-6)
    assert ea.amplifier_signal_to_noise_ratio(5.0, 5e-4) == pytest.approx(80.0)


def test_standard_measuring_conditions_are_10_db_down() -> None:
    # 5.2.2: the output current reduced to -10 dB of the rated one.
    rated = 4.0
    standard = rated * 10 ** (ref.IEC62489_1_STANDARD_MEASURING_DB / 20)
    assert ea.amplifier_signal_to_noise_ratio(rated, standard) == pytest.approx(10.0)


def test_frequency_response_is_0_db_at_1_khz() -> None:
    response = ea.amplifier_frequency_response(
        [50.0, 100.0, 1000.0, 8000.0], [1.0, 1.9, 2.0, 1.5]
    )
    assert response.response_db[2] == pytest.approx(0.0)
    assert response.response_db[0] == pytest.approx(20 * math.log10(0.5))
    mid = float(response.at(math.sqrt(1000.0 * 8000.0)))
    assert mid == pytest.approx(0.5 * 20 * math.log10(0.75))


def test_frequency_response_needs_1_khz() -> None:
    with pytest.raises(ValueError, match="1000 Hz"):
        ea.amplifier_frequency_response([100.0, 2000.0], [1.0, 1.0])


def test_frequency_response_is_read_within_its_range() -> None:
    response = ea.amplifier_frequency_response([100.0, 1000.0], [1.0, 1.0])
    with pytest.raises(ValueError, match="outside"):
        response.at(5000.0)


@pytest.mark.parametrize("frequency", [math.nan, math.inf, -1000.0, 0.0])
def test_impedance_and_response_are_read_at_positive_finite_frequencies(
    frequency: float,
) -> None:
    impedance = ea.loop_impedance(0.69, 109e-6)
    response = ea.amplifier_frequency_response([100.0, 1000.0, 2000.0], [1.0, 1.0, 1.0])
    with pytest.raises(ValueError, match="'frequency_hz' must be positive and finite"):
        impedance.at(frequency)
    with pytest.raises(ValueError, match="'frequency_hz' must be positive and finite"):
        impedance.drive_voltage(1.0, [1000.0, frequency])
    with pytest.raises(ValueError, match="'frequency_hz' must be positive and finite"):
        response.at(frequency)


def test_impedance_is_read_at_frequencies_of_any_shape() -> None:
    impedance = ea.loop_impedance(0.69, 109e-6)
    grid = impedance.at([[1000.0, 2000.0], [4000.0, 8000.0]])
    assert grid.shape == (2, 2)
    assert grid[0, 0] == pytest.approx(float(impedance.at(1000.0)), rel=1e-15)
    with pytest.raises(ValueError, match="'frequency_hz' must be real"):
        impedance.at(np.array([1000.0 + 1.0j]))


def test_agc_range_of_a_characteristic_like_figure_a1() -> None:
    emf = [-60.0, -50.0, -40.0, -35.0, -30.0, -25.0, -20.0, -10.0, 0.0]
    out = [-33.0, -23.0, -13.0, -8.0, -3.0, -1.0, 0.0, 0.0, 0.0]
    agc = ea.agc_characteristic(emf, out)
    assert agc.agc_range_db == pytest.approx(30.0, abs=2e-3)
    assert agc.agc_range_end_db == pytest.approx(0.0)
    assert agc.agc_range_db < ref.IEC62489_1_AGC_RANGE_DB


def test_agc_range_of_a_compressor_is_its_ratio_times_3_db() -> None:
    # A compression ratio of 2 (Annex A) over the whole span: 3 dB of output
    # takes 6 dB of input.
    emf = np.arange(-60.0, 1.0, 2.0)
    out = emf / 2.0
    agc = ea.agc_characteristic(emf, out)
    assert agc.agc_range_db == pytest.approx(
        2.0 * ref.IEC62489_1_AGC_OUTPUT_CHANGE_DB, abs=2e-3
    )


def test_agc_range_handles_an_overshoot() -> None:
    emf = [-40.0, -30.0, -20.0, -10.0, 0.0]
    out = [-10.0, -1.0, 1.0, -2.5, -1.0]
    agc = ea.agc_characteristic(emf, out)
    # The overshoot to +1 dB and the dip to -2,5 dB cannot share a 3 dB
    # window: the widest one holds the overshoot and runs from where the
    # rising side reaches -2 dB (-31,11 dB) to where the falling side does
    # (-11,43 dB), wider than the 18,57 dB from +0,5 dB down to the top.
    assert agc.agc_range_start_db == pytest.approx(-40.0 + 8.0 / 0.9, abs=2e-3)
    assert agc.agc_range_end_db == pytest.approx(-20.0 + 3.0 / 0.35, abs=2e-3)
    assert agc.agc_range_db == pytest.approx(3.0 / 0.35 + 20.0 - 8.0 / 0.9, abs=3e-3)


def test_agc_characteristic_needs_ascending_input() -> None:
    emf = [0.0, -10.0]
    with pytest.raises(ValueError, match="ascending"):
        ea.agc_characteristic(emf, [0.0, 0.0])


def test_agc_range_ends_where_the_line_crosses_a_level_between_steps() -> None:
    # The widest window holds the 0 dB of the third step as its lowest value
    # and the 3 dB above it: it enters on the first segment where the line
    # rises through 0 dB (-23,33 dB) and leaves on the last where it rises
    # through 3 dB (-5 dB). Neither end is a step, and neither lies on any
    # grid of input levels.
    agc = ea.agc_characteristic([-30.0, -20.0, -10.0, 0.0], [-6.0, 3.0, 0.0, 6.0])
    assert agc.agc_range_start_db == pytest.approx(-30.0 + 60.0 / 9.0, abs=1e-12)
    assert agc.agc_range_end_db == pytest.approx(-5.0, abs=1e-12)
    assert agc.agc_range_db == pytest.approx(25.0 - 60.0 / 9.0, abs=1e-12)


def test_agc_range_keeps_a_window_whose_levels_differ_by_exactly_3_db() -> None:
    # 4,19 dB and 1,19 dB are 3 dB apart, but in floating point 1,19 + 3 is
    # 4,1899999999999995 and 4,19 - 3 is 1,1900000000000004: without the
    # tolerance neither step's 3 dB band holds the other, and the window
    # shrinks to the 30 dB from 10 dB onwards.
    emf = [0.0, 10.0, 20.0, 30.0, 40.0]
    out = [2.5, 1.19, 2.5, 4.19, 2.5]
    agc = ea.agc_characteristic(emf, out)
    assert agc.agc_range_db == pytest.approx(40.0, abs=1e-12)
    assert agc.agc_range_start_db == pytest.approx(0.0, abs=1e-12)
    assert agc.agc_range_end_db == pytest.approx(40.0, abs=1e-12)


def test_agc_range_ends_where_a_window_exactly_3_db_deep_meets_its_edges() -> None:
    # -1,4 dB less -4,4 dB is 3,0000000000000004 dB in floating point, while
    # -1,4 dB less 3 dB rounds to -4,4 dB, so the band below the -1,4 dB step
    # holds the window: it runs from the fall through -1,4 dB to the rise
    # back to it.
    emf = [-35.0, -30.0, -25.0, -20.0, -15.0]
    out = [0.0, -4.4, -1.4, -1.6, 2.0]
    agc = ea.agc_characteristic(emf, out)
    assert agc.agc_range_start_db == pytest.approx(-35.0 + 5.0 * 1.4 / 4.4, abs=1e-9)
    assert agc.agc_range_end_db == pytest.approx(-20.0 + 5.0 * 0.2 / 3.6, abs=1e-9)


def test_agc_range_does_not_grow_with_the_span_of_the_input() -> None:
    # An e.m.f. given in microvolts instead of decibels spans millions: the
    # search works on the steps, not on a grid across that span.
    agc = ea.agc_characteristic([0.0, 1.0e7], [0.0, 0.0])
    assert agc.agc_range_db == pytest.approx(1.0e7, rel=1e-15)
    many = ea.agc_characteristic(np.linspace(-1.0e6, 0.0, 20001), np.zeros(20001))
    assert many.agc_range_db == pytest.approx(1.0e6, rel=1e-15)


def test_quadrature_example_of_5_4_14_1() -> None:
    error = ea.quadrature_phase_error([100.0, 1000.0, 5000.0], [90.0, 85.0, 91.0])
    assert error.max_deviation_deg == pytest.approx(5.0)
    assert error.max_deviation_frequency_hz == pytest.approx(1000.0)
    angle = ref.IEC62489_1_QUADRATURE_EXAMPLE_DEG
    assert math.cos(math.radians(angle)) == pytest.approx(
        ref.IEC62489_1_QUADRATURE_EXAMPLE_COS, abs=5e-4
    )
    assert error.level_increase_db == pytest.approx(
        ref.IEC62489_1_QUADRATURE_EXAMPLE_DB, abs=0.01
    )
    # The decrease is 0,79 dB, not the 0,72 dB 5.4.14.1 prints for both.
    assert error.level_decrease_db == pytest.approx(-0.79, abs=0.005)


def test_quadrature_folds_either_loop_leading() -> None:
    error = ea.quadrature_phase_error([100.0, 1000.0, 4000.0], [-90.0, 270.0, -95.0])
    np.testing.assert_allclose(error.deviation_deg, [0.0, 0.0, 5.0], atol=1e-12)


def test_quadrature_ignores_frequencies_outside_100_hz_to_5_khz() -> None:
    error = ea.quadrature_phase_error([50.0, 1000.0, 8000.0], [60.0, 88.0, 120.0])
    assert error.max_deviation_deg == pytest.approx(2.0)


def test_quadrature_needs_a_frequency_in_the_band() -> None:
    with pytest.raises(ValueError, match="100 Hz to 5 kHz"):
        ea.quadrature_phase_error([50.0, 8000.0], [90.0, 90.0])


@pytest.mark.parametrize("phase", [0.0, 180.0, -180.0, 360.0])
def test_quadrature_in_phase_currents_cancel_where_they_subtract(phase: float) -> None:
    # A deviation of 90 degrees is the failure the characteristic detects: the
    # two fields add to twice one of them and cancel where they subtract.
    error = ea.quadrature_phase_error([1000.0], [phase])
    assert error.max_deviation_deg == pytest.approx(90.0)
    assert error.level_increase_db == pytest.approx(20 * math.log10(2.0), rel=1e-12)
    assert math.isinf(error.level_decrease_db)
    assert error.level_decrease_db < 0.0


def test_quadrature_decrease_near_90_degrees_is_accurate() -> None:
    # 20 lg(1 - sin 89,9999 degrees), from the series 1 - sin(90 - e) = e^2/2.
    error = ea.quadrature_phase_error([1000.0], [1.0e-4])
    e = math.radians(1.0e-4)
    assert error.level_decrease_db == pytest.approx(
        20 * math.log10(e * e / 2.0), abs=1e-6
    )


# ---------------------------------------------------------------------------
# The neck loop (clause 9, and the draft Annex D)
# ---------------------------------------------------------------------------


def test_neck_loop_characteristics() -> None:
    result = ea.neck_loop_characteristics(
        [100.0, 200.0, 1000.0, 5000.0, 8000.0],
        [-8.0, -2.0, 0.5, -1.0, -5.0],
        [31.6, 32.0, 32.4, 40.0, 50.0],
        input_voltage_v=1.0,
    )
    assert result.reference_input_voltage_v == pytest.approx(10 ** (-0.5 / 20))
    assert result.minimum_impedance_ohm == pytest.approx(32.0)
    assert len(result.frequencies_3db_hz) == 2
    low, high = result.frequencies_3db_hz
    assert 100.0 < low < 200.0
    assert 5000.0 < high < 8000.0


def test_neck_loop_minimum_impedance_rounds_half_up() -> None:
    result = ea.neck_loop_characteristics(
        [100.0, 1000.0, 5000.0],
        [0.0, 0.0, 0.0],
        [16.5, 20.0, 30.0],
        input_voltage_v=1.0,
    )
    assert result.minimum_impedance_ohm == pytest.approx(17.0)


def test_neck_loop_minimum_impedance_is_taken_over_100_hz_to_5_khz_only() -> None:
    # 9.2.1: the smallest magnitude "over the frequency range 100 Hz to 5 kHz";
    # the 20 ohm at 50 Hz is outside it.
    result = ea.neck_loop_characteristics(
        [50.0, 100.0, 1000.0, 5000.0, 8000.0],
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [20.0, 32.0, 33.0, 40.0, 50.0],
        input_voltage_v=1.0,
    )
    assert result.minimum_impedance_ohm == pytest.approx(32.0)


def test_neck_loop_takes_the_magnitude_of_a_complex_impedance() -> None:
    result = ea.neck_loop_characteristics(
        [100.0, 1000.0, 5000.0],
        [0.0, 0.0, 0.0],
        [3 + 4j, 8.0, 9.0],
        input_voltage_v=1.0,
    )
    assert result.minimum_impedance_ohm == pytest.approx(5.0)


def test_neck_loop_types_are_the_draft_ones() -> None:
    assert isinstance(ea.NECK_LOOP_TYPES, MappingProxyType)
    one = ea.NECK_LOOP_TYPES[1]
    tol = ref.IEC62489_1_A2_DRAFT_TYPE1_TOL_PERCENT / 100
    assert one.min_dc_resistance_ohm == pytest.approx(
        ref.IEC62489_1_A2_DRAFT_TYPE1_OHM * (1 - tol)
    )
    assert one.max_dc_resistance_ohm == pytest.approx(
        ref.IEC62489_1_A2_DRAFT_TYPE1_OHM * (1 + tol)
    )
    two = ea.NECK_LOOP_TYPES[2]
    assert two.min_dc_resistance_ohm == pytest.approx(
        ref.IEC62489_1_A2_DRAFT_TYPE2_MIN_OHM
    )
    assert math.isinf(two.max_dc_resistance_ohm)
    for kind in (one, two):
        assert kind.max_input_voltage_v == pytest.approx(
            ref.IEC62489_1_A2_DRAFT_MAX_INPUT_V
        )


@pytest.mark.parametrize(
    ("resistance", "voltage", "kind", "passes"),
    [
        (30.4, 1.06, 1, True),
        (33.6, 0.5, 1, True),
        (30.3, 1.0, 1, False),
        (32.0, 1.07, 1, False),
        (500.0, 1.0, 2, True),
        (31.9, 1.0, 2, False),
    ],
)
def test_verify_neck_loop(
    resistance: float,
    voltage: float,
    kind: int,
    passes: bool,  # noqa: FBT001
) -> None:
    assert (
        ea.verify_neck_loop(resistance, voltage, neck_loop_type=kind).passes is passes
    )


def test_neck_loop_verdict_has_no_truth_value() -> None:
    result = ea.verify_neck_loop(32.0, 1.0)
    with pytest.raises(TypeError, match="passes"):
        bool(result)


def test_neck_loop_refuses_an_unknown_type() -> None:
    with pytest.raises(ValueError, match="neck_loop_type"):
        ea.verify_neck_loop(32.0, 1.0, neck_loop_type=3)


@pytest.mark.parametrize("kind", [True, False, "1", 1.5, None])
def test_neck_loop_refuses_a_type_that_is_not_a_whole_number(kind: object) -> None:
    with pytest.raises(ValueError, match="'neck_loop_type' must be one of"):
        ea.verify_neck_loop(32.0, 1.0, neck_loop_type=kind)  # type: ignore[arg-type]


def test_neck_loop_takes_a_whole_numpy_type() -> None:
    assert (
        ea.verify_neck_loop(32.0, 1.0, neck_loop_type=np.int64(2)).neck_loop_type == 2
    )


def test_neck_loop_refuses_a_negative_real_impedance() -> None:
    with pytest.raises(ValueError, match="'impedance_ohm' must be strictly positive"):
        ea.neck_loop_characteristics(
            [100.0, 1000.0, 5000.0],
            [0.0, 0.0, 0.0],
            [-32.0, 32.0, 32.0],
            input_voltage_v=1.0,
        )
    with pytest.raises(ValueError, match="'impedance_ohm' must be numeric"):
        ea.neck_loop_characteristics(
            [100.0, 1000.0, 5000.0],
            [0.0, 0.0, 0.0],
            ["a", "b", "c"],
            input_voltage_v=1.0,
        )


def test_loop_field_refuses_complex_coordinates() -> None:
    with pytest.raises(ValueError, match="'x_m' must be real"):
        ea.rectangular_loop_field(1.0, 2.0, 2.0, np.array([0.1j]), 0.0, 0.5)


# ---------------------------------------------------------------------------
# The maximum (distortion-limited) output current (5.4.7)
# ---------------------------------------------------------------------------

_STEPS_V = [1.0, 2.0, 3.0, 4.0, 5.0]
_STEPS_THD = [0.1, 0.2, 0.5, 1.5, 3.0]


def test_maximum_output_current_is_read_where_the_thd_reaches_its_rating() -> None:
    # Between 3 V (0,5 %) and 4 V (1,5 %) across 0,5 ohm the distortion
    # passes 1 % half way: 3,5 V, so 7 A.
    result = ea.maximum_output_current(
        _STEPS_V, _STEPS_THD, load_resistance_ohm=0.5, rated_thd_percent=1.0
    )
    assert result.maximum_current_a == pytest.approx(7.0, rel=1e-12)
    np.testing.assert_allclose(result.load_current_a, np.array(_STEPS_V) / 0.5)


def test_maximum_output_current_at_a_step_that_equals_the_rating() -> None:
    result = ea.maximum_output_current(
        _STEPS_V, _STEPS_THD, load_resistance_ohm=2.0, rated_thd_percent=1.5
    )
    assert result.maximum_current_a == pytest.approx(2.0, rel=1e-12)


def test_maximum_output_current_needs_the_rating_to_be_reached() -> None:
    with pytest.raises(ValueError, match="never reaches"):
        ea.maximum_output_current(
            _STEPS_V, _STEPS_THD, load_resistance_ohm=1.0, rated_thd_percent=5.0
        )


def test_maximum_output_current_needs_a_first_step_below_the_rating() -> None:
    with pytest.raises(ValueError, match="first step"):
        ea.maximum_output_current(
            _STEPS_V, _STEPS_THD, load_resistance_ohm=1.0, rated_thd_percent=0.05
        )


def test_maximum_output_current_needs_ascending_steps() -> None:
    voltages = [1.0, 3.0, 2.0]
    distortion = [0.1, 0.5, 2.0]
    with pytest.raises(ValueError, match="ascending"):
        ea.maximum_output_current(
            voltages, distortion, load_resistance_ohm=1.0, rated_thd_percent=1.0
        )


@pytest.mark.parametrize(
    "distortion",
    [[-5.0, 5.0], [0.1, -0.2, 2.0], [0.1, 0.5, -1.5]],
    ids=["first-step", "middle-step", "last-step"],
)
def test_maximum_output_current_refuses_a_negative_distortion(
    distortion: list[float],
) -> None:
    voltages = [1.0, 2.0, 3.0][: len(distortion)]
    with pytest.raises(ValueError, match="'thd_percent' must be non-negative"):
        ea.maximum_output_current(
            voltages, distortion, load_resistance_ohm=1.0, rated_thd_percent=1.0
        )


def test_maximum_output_current_accepts_no_distortion_at_the_first_step() -> None:
    result = ea.maximum_output_current(
        [1.0, 2.0], [0.0, 2.0], load_resistance_ohm=1.0, rated_thd_percent=1.0
    )
    assert result.maximum_current_a == pytest.approx(1.5, rel=1e-12)


def test_maximum_output_current_arrays_are_read_only() -> None:
    result = ea.maximum_output_current(
        _STEPS_V, _STEPS_THD, load_resistance_ohm=0.5, rated_thd_percent=1.0
    )
    with pytest.raises(ValueError, match="read-only"):
        result.thd_percent[0] = 0.0


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "es"])
def test_every_result_plots(language: str) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    results = (
        ea.rectangular_loop_field(1.0, 10.0, 15.0, np.linspace(-7, 7, 57), 0.0, 1.2),
        ea.loop_impedance(0.69, 109e-6),
        ea.amplifier_frequency_response([50.0, 1000.0, 8000.0], [0.9, 1.0, 0.8]),
        ea.agc_characteristic([-40.0, -20.0, 0.0], [-20.0, -1.0, 0.0]),
        ea.quadrature_phase_error([100.0, 1000.0, 5000.0], [88.0, 90.0, 95.0]),
        ea.neck_loop_characteristics(
            [100.0, 1000.0, 5000.0],
            [-4.0, 0.0, -1.0],
            [32.0, 33.0, 40.0],
            input_voltage_v=1.0,
        ),
        ea.verify_neck_loop(32.0, 1.0),
        ea.maximum_output_current(
            _STEPS_V, _STEPS_THD, load_resistance_ohm=0.5, rated_thd_percent=1.0
        ),
    )
    for result in results:
        ax = result.plot(language=language)
        assert ax.get_title()
        plt.close("all")


def _segments(ax: object, bar: int) -> dict[str, float]:
    """The limit segments drawn over one bar, by their dash style."""
    found: dict[str, float] = {}
    for line in ax.lines:  # type: ignore[attr-defined]
        xs = line.get_xdata()
        if len(xs) == 2 and xs[0] < bar < xs[1]:
            found[line.get_linestyle()] = float(line.get_ydata()[0])
    return found


def test_neck_loop_plot_of_type_2_draws_its_floor_as_a_lower_limit() -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    ax = ea.verify_neck_loop(40.0, 0.9, neck_loop_type=2).plot()
    heights = [patch.get_height() for patch in ax.patches]
    assert heights == pytest.approx([125.0, 100.0 * 0.9 / 1.06])
    assert _segments(ax, 0) == {":": pytest.approx(100.0)}
    assert _segments(ax, 1) == {"--": pytest.approx(100.0)}
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert "Lower limit of the type" in labels
    plt.close("all")


def test_neck_loop_plot_of_type_1_draws_both_limits_of_the_resistance() -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    ax = ea.verify_neck_loop(32.4, 0.998, neck_loop_type=1).plot()
    assert ax.patches[0].get_height() == pytest.approx(100.0 * 32.4 / 33.6)
    assert _segments(ax, 0) == {
        "--": pytest.approx(100.0),
        ":": pytest.approx(100.0 * 30.4 / 33.6),
    }
    assert ax.get_title().endswith("pass")
    plt.close("all")


def test_maximum_output_current_plot_draws_the_steps_the_rating_and_the_current() -> (
    None
):
    plt = pytest.importorskip("matplotlib.pyplot")
    result = ea.maximum_output_current(
        _STEPS_V, _STEPS_THD, load_resistance_ohm=0.5, rated_thd_percent=1.0
    )
    ax = result.plot()
    np.testing.assert_array_equal(ax.lines[0].get_xdata(), result.load_current_a)
    np.testing.assert_array_equal(ax.lines[0].get_ydata(), result.thd_percent)
    assert tuple(ax.lines[1].get_ydata()) == (1.0, 1.0)
    assert tuple(ax.lines[2].get_xdata()) == (7.0, 7.0)
    plt.close("all")
