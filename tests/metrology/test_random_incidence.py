#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 61183:1994: random-incidence and diffuse-field sensitivity levels.

The oracle is the printed page of BS EN 61183:1995 (EN 61183:1994, which is
IEC 1183:1994 unchanged): Table A.1 on folio 10 (PDF page 14), A.1.6 on folio
8, A.1.7 on folio 9, the note to A.1.8 on folio 10 and Table B.1 on folio 14
(PDF page 18). The printed values are in ``tests/reference_data``; what the
invariants and the closed forms say is derived here and says so.
"""

from __future__ import annotations

import dataclasses
import math
import types
import warnings

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref

from phonometry import metrology
from phonometry.metrology import random_incidence as ri

#: The ISO 266 preferred one-third-octave frequencies the first row covers.
_LOW_ROW_HZ = (
    25.0, 31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0,
    160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0,
)  # fmt: skip

#: The sum of the 72 factors of Table A.1 with the poles counted in one plane
#: only: one less the pole factor of Formula (A.2) twice, derived from the
#: formulas rather than printed.
_COUNTED_ONCE_SUM = 0.998097


def _omni(planes: int, per_plane: int, level: float = 94.0) -> np.ndarray:
    return np.full((planes, per_plane), level)


def _cardioid_levels(step_deg: float) -> np.ndarray:
    """One plane of an axisymmetric cardioid, whose exact gamma is 3."""
    phi = np.radians(np.arange(round(360.0 / step_deg)) * step_deg)
    pressure_squared = ((1.0 + np.cos(phi)) / 2.0) ** 2
    return 94.0 + 10.0 * np.log10(np.maximum(pressure_squared, 1e-30))


# --------------------------------------------------------------------------
# Table A.1 and the factors of Formulas (6), (7), (A.1) and (A.2)
# --------------------------------------------------------------------------
@pytest.mark.parametrize(("angles", "printed"), ref.IEC61183_TABLE_A1)
def test_every_angle_of_table_a1_takes_its_printed_factor(
    angles: tuple[int, ...], printed: float
) -> None:
    """All 36 angles of a plane round to the five decimals of their row."""
    factors = metrology.adjustment_factors(ref.IEC61183_TABLE_A1_STEP_DEG)
    for angle in angles:
        index = round(angle / ref.IEC61183_TABLE_A1_STEP_DEG)
        assert round(float(factors[index]), 5) == pytest.approx(printed, abs=1e-12)


def test_table_a1_covers_every_angle_of_a_plane_once() -> None:
    angles = sorted(a for row, _ in ref.IEC61183_TABLE_A1 for a in row)
    assert angles == list(range(0, 360, 10))


def test_factors_are_formulas_a1_and_a2_as_printed() -> None:
    """(A.1) and (A.2), written with the printed difference of cosines."""
    step = math.radians(10.0)
    factors = metrology.adjustment_factors(10.0)
    for index in range(1, 18):
        phi = index * step
        printed_form = (math.cos(phi - step / 2) - math.cos(phi + step / 2)) / 8.0
        assert factors[index] == pytest.approx(printed_form, rel=1e-12)
    assert factors[0] == pytest.approx((1.0 - math.cos(step / 2)) / 4.0, rel=1e-12)
    assert factors[18] == pytest.approx(factors[0], rel=1e-15)


def test_factors_are_symmetric_about_the_axis() -> None:
    factors = metrology.adjustment_factors(10.0)
    np.testing.assert_allclose(factors[1:], factors[1:][::-1], rtol=1e-15)


@pytest.mark.parametrize("step_deg", [10.0, 5.0, 15.0, 30.0, 45.0, 90.0, 2.0])
@pytest.mark.parametrize("planes", [1, 2, 3, 4])
def test_the_factors_of_every_plane_together_sum_to_one(
    step_deg: float, planes: int
) -> None:
    """With the poles counted in every plane's sum, the division is the sphere."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", metrology.SphereDivisionWarning)
        factors = metrology.adjustment_factors(step_deg, planes=planes)
    assert planes * float(np.sum(factors)) == pytest.approx(1.0, abs=1e-14)


def _counted_once_index_db(result: ri.DirectivityFactor) -> float:
    """10 lg gamma of Formula (A.3) with the second plane's poles left out."""
    second = np.isclose(result.plane_angles_deg, 90.0)
    pole = np.isclose(result.incidence_angles_deg % 180.0, 0.0)
    kept = ~(second & pole)
    energy = 10.0 ** (0.1 * (result.levels_db - result.reference_level_db))
    return -10.0 * math.log10(float(np.sum(result.weights[kept] * energy[kept])))


def test_counting_the_poles_once_leaves_an_omnidirectional_bias_of_0_008_db() -> None:
    """The paragraph under (A.3) says the pole readings are taken into account
    once. Read as *counted* once, the 72 factors sum to 0,998097 and an
    omnidirectional instrument's 10 lg gamma comes out 0,0083 dB high; the
    library counts them in both sums and that instrument reads exactly 0 dB.
    """
    factors = metrology.adjustment_factors(10.0)
    counted_once = 2.0 * float(np.sum(factors)) - factors[0] - factors[18]
    assert counted_once == pytest.approx(_COUNTED_ONCE_SUM, abs=5e-7)
    assert -10.0 * math.log10(counted_once) == pytest.approx(0.00827, abs=5e-6)
    omni = metrology.directivity_factor(_omni(2, 36))
    assert omni.directivity_index_db == pytest.approx(0.0, abs=1e-12)
    assert _counted_once_index_db(omni) == pytest.approx(0.00827, abs=5e-6)


def test_the_counted_once_bias_grows_with_the_directivity() -> None:
    """Dropping the second plane's poles removes K(0) [p(0) + p(180)] from the
    sum 1/gamma, so 10 lg gamma comes out high by
    -10 lg(1 - gamma K(0) [p(0) + p(180)]): more than the 0,008 dB of an
    omnidirectional instrument for a directional one. A cardioid squared twice
    over, with a floor 30 dB down, has 10 lg gamma near 7 dB and a bias near
    0,02 dB.
    """
    phi = np.radians(np.arange(36) * 10.0)
    plane = 94.0 + 10.0 * np.log10(((1.0 + np.cos(phi)) / 2.0) ** 4 * 0.999 + 0.001)
    result = metrology.directivity_factor(np.vstack((plane, plane)))
    bias = _counted_once_index_db(result) - result.directivity_index_db
    k0 = float(metrology.adjustment_factors(10.0)[0])
    rear = 10.0 ** (0.1 * (plane[18] - 94.0))
    expected = -10.0 * math.log10(1.0 - result.gamma * k0 * (1.0 + rear))
    assert bias == pytest.approx(expected, rel=1e-9)
    assert result.directivity_index_db == pytest.approx(7.0, abs=0.1)
    assert bias == pytest.approx(0.02, abs=0.002)


def test_four_planes_halve_table_a1() -> None:
    """NOTE 2 of A.6: four planes at 45° take half the values of Table A.1."""
    two = metrology.adjustment_factors(10.0)
    four = metrology.adjustment_factors(10.0, planes=4)
    np.testing.assert_allclose(four, two / 2.0, rtol=1e-14)


def test_one_plane_doubles_table_a1() -> None:
    """The 2 of Formula (A.4) is the factor of one plane, Delta alpha = pi."""
    np.testing.assert_allclose(
        metrology.adjustment_factors(10.0, planes=1),
        2.0 * metrology.adjustment_factors(10.0),
        rtol=1e-14,
    )


def test_adjustment_factors_are_read_only() -> None:
    factors = metrology.adjustment_factors(10.0)
    with pytest.raises(ValueError, match="read-only"):
        factors[0] = 1.0


@pytest.mark.parametrize("step_deg", [7.0, 0.0, -10.0, 120.0, 180.0, math.nan])
def test_a_step_that_does_not_divide_the_half_circle_is_refused(
    step_deg: float,
) -> None:
    with pytest.raises(ValueError, match="'step_deg' must"):
        metrology.adjustment_factors(step_deg)


@pytest.mark.parametrize("planes", [0, 1.5, True, "2"])
def test_a_number_of_planes_that_is_not_a_whole_number_is_refused(
    planes: object,
) -> None:
    with pytest.raises(ValueError, match="'planes' must be a whole number"):
        metrology.adjustment_factors(10.0, planes=planes)  # type: ignore[arg-type]


def test_a_step_computed_as_a_fraction_of_the_half_circle_is_accepted() -> None:
    factors = metrology.adjustment_factors(180.0 / 18.0)
    assert factors.size == 36


# --------------------------------------------------------------------------
# A.1.6 and A.1.7: the size of the largest element
# --------------------------------------------------------------------------
def test_the_largest_of_the_70_elements_of_10_degree_steps_is_2_2_percent() -> None:
    """A.1.7: 70 sub-areas, the largest approximately 2,2 %."""
    largest = metrology.largest_element_fraction(10.0)
    assert round(100.0 * largest, 1) == pytest.approx(ref.IEC61183_A17_LARGEST_PERCENT)
    assert largest == pytest.approx(metrology.adjustment_factors(10.0)[9], rel=1e-15)


def test_ten_degree_steps_in_two_planes_divide_the_sphere_into_70_elements() -> None:
    """A.1.7: each reading off the poles is one element; the two readings of a
    pole, one in each plane, together are its cap. 68 elements and 2 caps.
    """
    result = metrology.directivity_factor(_omni(2, 36))
    angles = result.incidence_angles_deg
    off_pole = ~np.isclose(angles % 180.0, 0.0)
    caps = [
        float(np.sum(result.weights[np.isclose(angles, pole)])) for pole in (0.0, 180.0)
    ]
    elements = [*result.weights[off_pole], *caps]
    assert len(elements) == ref.IEC61183_A17_SUB_AREAS
    assert math.fsum(elements) == pytest.approx(1.0, abs=1e-14)
    assert max(elements) == pytest.approx(result.largest_element_fraction, rel=1e-15)


def test_the_3_percent_criterion_falls_between_12_and_15_degree_steps() -> None:
    limit = ref.IEC61183_A16_LIMIT_PERCENT / 100.0
    assert metrology.largest_element_fraction(12.0) < limit
    assert metrology.largest_element_fraction(15.0) > limit


def test_a_coarse_step_warns_and_a_fine_one_does_not() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", metrology.SphereDivisionWarning)
        metrology.adjustment_factors(12.0)
        metrology.directivity_factor(_omni(2, 30))
    with pytest.warns(metrology.SphereDivisionWarning, match="3 %"):
        metrology.adjustment_factors(15.0)


def test_the_warning_points_at_the_caller() -> None:
    levels = _omni(2, 24)
    with pytest.warns(metrology.SphereDivisionWarning) as record:
        metrology.directivity_factor(levels)
    assert record[0].filename == __file__


def test_the_warning_of_the_factors_points_at_the_caller() -> None:
    with pytest.warns(metrology.SphereDivisionWarning) as record:
        metrology.adjustment_factors(15.0)
    assert record[0].filename == __file__


def test_four_planes_halve_the_ring_elements_but_not_the_caps() -> None:
    """At 90° steps the cap is the largest element, and more planes do not
    shrink it.
    """
    assert metrology.largest_element_fraction(15.0, planes=4) < 0.03
    cap = math.sin(math.radians(90.0) / 4.0) ** 2
    assert metrology.largest_element_fraction(90.0, planes=4) == pytest.approx(cap)


def test_one_plane_is_judged_on_the_two_plane_division() -> None:
    assert metrology.largest_element_fraction(10.0, planes=1) == pytest.approx(
        metrology.largest_element_fraction(10.0)
    )


# --------------------------------------------------------------------------
# Formulas (A.3) and (A.4)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("planes", [2, 4])
@pytest.mark.parametrize("per_plane", [36, 72, 12])
def test_an_omnidirectional_instrument_has_gamma_one(
    planes: int, per_plane: int
) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", metrology.SphereDivisionWarning)
        result = metrology.directivity_factor(_omni(planes, per_plane))
    assert result.gamma == pytest.approx(1.0, abs=1e-13)
    assert float(np.sum(result.weights)) == pytest.approx(1.0, abs=1e-13)


def test_a_uniform_offset_is_the_directivity_index() -> None:
    """Every reading 1 dB above L_rd reads 10 lg gamma = -1 dB."""
    levels = _omni(2, 36, 95.0)
    result = metrology.directivity_factor(levels, reference_level_db=94.0)
    assert result.directivity_index_db == pytest.approx(-1.0, abs=1e-12)


def test_the_reference_level_defaults_to_the_first_reading() -> None:
    levels = _omni(2, 36)
    levels[0, 0] = 93.0
    result = metrology.directivity_factor(levels)
    assert result.reference_level_db == pytest.approx(93.0)
    explicit = metrology.directivity_factor(levels, reference_level_db=93.0)
    assert explicit.gamma == pytest.approx(result.gamma, rel=1e-15)


def test_formula_a3_is_the_printed_double_sum() -> None:
    """(A.3) evaluated by hand on a pattern that differs between the planes."""
    rng = np.random.default_rng(61183)
    levels = 94.0 - rng.uniform(0.0, 8.0, size=(2, 36))
    levels[:, 0] = 94.0
    factors = metrology.adjustment_factors(10.0)
    total = sum(
        factors[i] * 10.0 ** (-0.1 * (94.0 - levels[plane, i]))
        for plane in (0, 1)
        for i in range(36)
    )
    result = metrology.directivity_factor(levels)
    assert result.gamma == pytest.approx(1.0 / total, rel=1e-13)


def test_formula_a4_is_formula_a3_with_equal_planes() -> None:
    rng = np.random.default_rng(1183)
    plane = 94.0 - rng.uniform(0.0, 6.0, size=36)
    plane[0] = 94.0
    symmetric = metrology.axisymmetric_directivity_factor(plane)
    both = metrology.directivity_factor(np.vstack((plane, plane)))
    assert symmetric.gamma == pytest.approx(both.gamma, rel=1e-13)
    assert symmetric.formula == "A.4"
    assert both.formula == "A.3"


@pytest.mark.parametrize(
    ("step_deg", "tolerance"), [(10.0, 1e-3), (5.0, 2e-4), (1.0, 1e-5)]
)
def test_the_sum_converges_to_the_integral_of_formula_3(
    step_deg: float, tolerance: float
) -> None:
    """A cardioid, |p|² = ((1 + cos phi)/2)², has gamma = 3 by Formula (3)."""
    result = metrology.axisymmetric_directivity_factor(_cardioid_levels(step_deg))
    assert result.gamma == pytest.approx(3.0, rel=tolerance)


def test_one_plane_goes_to_the_axisymmetric_function() -> None:
    levels = np.full(36, 94.0)
    with pytest.raises(ValueError, match="'levels_db' must hold one row per plane"):
        metrology.directivity_factor(levels)


def test_several_planes_go_to_the_plane_function() -> None:
    levels = _omni(2, 36)
    with pytest.raises(
        ValueError, match="'levels_db' must be the readings of one plane"
    ):
        metrology.axisymmetric_directivity_factor(levels)


@pytest.mark.parametrize("per_plane", [35, 2])
def test_a_plane_without_both_poles_is_refused(per_plane: int) -> None:
    levels = _omni(2, per_plane)
    with pytest.raises(ValueError, match="'levels_db' must hold an even number"):
        metrology.directivity_factor(levels)


def test_a_reading_that_is_not_finite_is_refused() -> None:
    levels = _omni(2, 36)
    levels[1, 5] = math.nan
    with pytest.raises(ValueError, match="'levels_db' must contain only finite values"):
        metrology.directivity_factor(levels)


def test_the_readings_are_held_flat_with_their_planes() -> None:
    result = metrology.directivity_factor(_omni(4, 36))
    assert result.levels_db.shape == (144,)
    np.testing.assert_array_equal(np.unique(result.plane_angles_deg), [0, 45, 90, 135])
    np.testing.assert_allclose(result.incidence_angles_deg[:36], np.arange(0, 360, 10))


def test_the_result_arrays_are_read_only_copies() -> None:
    levels = _omni(2, 36)
    result = metrology.directivity_factor(levels)
    levels[0, 3] = 0.0
    assert result.levels_db[3] == pytest.approx(94.0)
    for name in ("incidence_angles_deg", "plane_angles_deg", "levels_db", "weights"):
        assert not getattr(result, name).flags.writeable


def _directivity_fields(**changes: object) -> dict[str, object]:
    """The fields of a valid four-reading DirectivityFactor, with changes."""
    fields: dict[str, object] = {
        "incidence_angles_deg": np.arange(4) * 90.0,
        "plane_angles_deg": np.zeros(4),
        "levels_db": np.zeros(4),
        "weights": np.full(4, 0.25),
        "reference_level_db": 0.0,
        "gamma": 1.0,
        "largest_element_fraction": 0.3,
        "formula": "A.3",
    }
    fields.update(changes)
    return fields


def test_the_result_refuses_columns_of_different_lengths() -> None:
    fields = _directivity_fields(levels_db=np.zeros(2))
    with pytest.raises(
        ValueError, match="'weights' must be 1-D arrays of the same length"
    ):
        ri.DirectivityFactor(**fields)  # type: ignore[arg-type]


def test_the_result_refuses_a_gamma_that_is_not_positive() -> None:
    fields = _directivity_fields(gamma=0.0)
    with pytest.raises(ValueError, match="'gamma' must be positive"):
        ri.DirectivityFactor(**fields)  # type: ignore[arg-type]


def test_the_result_refuses_a_formula_it_does_not_draw() -> None:
    """The weights view labels its curve by the formula: an unknown one would
    reach it as a bare KeyError.
    """
    fields = _directivity_fields(formula="A.3 (sum)")
    with pytest.raises(ValueError, match="'formula' must be one of"):
        ri.DirectivityFactor(**fields)  # type: ignore[arg-type]


def test_the_result_refuses_a_reference_level_that_is_not_finite() -> None:
    fields = _directivity_fields(reference_level_db=math.nan)
    with pytest.raises(ValueError, match="'reference_level_db' must be finite"):
        ri.DirectivityFactor(**fields)  # type: ignore[arg-type]


@pytest.mark.parametrize("fraction", [-5.0, 0.0, 1.5, math.inf])
def test_the_result_refuses_a_largest_element_that_is_not_a_fraction(
    fraction: float,
) -> None:
    fields = _directivity_fields(largest_element_fraction=fraction)
    with pytest.raises(
        ValueError, match="'largest_element_fraction' must be a fraction"
    ):
        ri.DirectivityFactor(**fields)  # type: ignore[arg-type]


def test_the_result_accepts_a_whole_sphere_element() -> None:
    result = ri.DirectivityFactor(**_directivity_fields(largest_element_fraction=1.0))  # type: ignore[arg-type]
    assert result.largest_element_fraction == pytest.approx(1.0)


def test_the_relative_levels_are_the_readings_less_the_reference() -> None:
    """L(phi) - L_rd: a reading 3 dB below the reference is -3 dB."""
    levels = _omni(2, 36)
    levels[0, 9] = 91.0
    result = metrology.directivity_factor(levels, reference_level_db=94.0)
    assert result.relative_levels_db[0] == pytest.approx(0.0, abs=1e-12)
    assert result.relative_levels_db[9] == pytest.approx(-3.0, abs=1e-12)
    assert result.relative_levels_db[36 + 9] == pytest.approx(0.0, abs=1e-12)


# --------------------------------------------------------------------------
# Formula (A.5) and the directions of the note to A.1.8
# --------------------------------------------------------------------------
def test_the_equal_area_directions_are_the_printed_ones() -> None:
    """18 of the 20 printed horizontal angles, to the 0,1° they are printed
    to, and 16 of the 18 the vertical plane repeats without the poles: 34 of
    the 38 directions. The other four are the two errata, printed in both
    planes.
    """
    horizontal, vertical = metrology.equal_area_incidence_angles()
    printed = np.array(ref.IEC61183_EQUAL_AREA_HORIZONTAL_DEG)
    errata = np.isin(printed, list(ref.IEC61183_EQUAL_AREA_ERRATA_DEG))
    np.testing.assert_allclose(np.round(horizontal[~errata], 1), printed[~errata])
    poles = np.isclose(printed, 0.0) | np.isclose(printed, 180.0)
    printed_vertical = printed[~poles]
    vertical_errata = errata[~poles]
    assert vertical.size == printed_vertical.size
    np.testing.assert_allclose(
        np.round(vertical[~vertical_errata], 1), printed_vertical[~vertical_errata]
    )
    assert (
        int(np.count_nonzero(~errata)) + int(np.count_nonzero(~vertical_errata)) == 34
    )


def test_the_two_misprinted_angles_are_the_corrected_ones() -> None:
    horizontal, _ = metrology.equal_area_incidence_angles()
    printed = list(ref.IEC61183_EQUAL_AREA_HORIZONTAL_DEG)
    for wrong, right in ref.IEC61183_EQUAL_AREA_ERRATA_DEG.items():
        assert round(float(horizontal[printed.index(wrong)]), 1) == pytest.approx(right)


def test_the_printed_list_breaks_its_own_symmetry_at_one_ring() -> None:
    """Every pair about 90° sums to 180,0° except 77,9° + 102,2°."""
    printed = ref.IEC61183_EQUAL_AREA_HORIZONTAL_DEG[1:10]
    sums = [round(a + b, 1) for a, b in zip(printed, printed[::-1], strict=True)]
    assert sums.count(180.1) == 2
    assert all(s == pytest.approx(180.0) for s in sums if s != pytest.approx(180.1))


def test_the_equal_area_directions_halve_their_elements() -> None:
    """Each ring direction splits the ring's 4/38 of the sphere in two."""
    horizontal, _ = metrology.equal_area_incidence_angles()
    rings = horizontal[1:10]
    below = (1.0 - np.cos(np.radians(rings))) / 2.0
    np.testing.assert_allclose(below, (4.0 * np.arange(1, 10) - 1.0) / 38.0)


def test_equal_area_elements_are_2_6_percent() -> None:
    result = metrology.equal_area_directivity_factor(
        np.full(20, 90.0), np.full(18, 90.0)
    )
    assert round(100.0 * result.largest_element_fraction, 1) == pytest.approx(
        ref.IEC61183_EQUAL_AREA_ELEMENT_PERCENT
    )
    assert result.gamma == pytest.approx(1.0, abs=1e-13)
    assert result.formula == "A.5"


def test_equal_area_is_formula_a5() -> None:
    rng = np.random.default_rng(38)
    horizontal = 94.0 - rng.uniform(0.0, 5.0, size=20)
    vertical = 94.0 - rng.uniform(0.0, 5.0, size=18)
    result = metrology.equal_area_directivity_factor(
        horizontal, vertical, reference_level_db=94.0
    )
    total = np.sum(10.0 ** (-0.1 * (94.0 - np.concatenate((horizontal, vertical)))))
    assert result.gamma == pytest.approx(38.0 / total, rel=1e-13)


def test_equal_area_converges_on_the_cardioid() -> None:
    """Formula (A.5) on the cardioid lands near the exact 3 of Formula (3)."""
    horizontal, vertical = metrology.equal_area_incidence_angles()

    def level(angle: np.ndarray) -> np.ndarray:
        return 94.0 + 20.0 * np.log10((1.0 + np.cos(np.radians(angle))) / 2.0 + 1e-15)

    result = metrology.equal_area_directivity_factor(level(horizontal), level(vertical))
    assert result.gamma == pytest.approx(3.0, rel=0.02)


@pytest.mark.parametrize(("horizontal", "vertical"), [(18, 18), (19, 19), (21, 17)])
def test_equal_area_refuses_the_wrong_number_of_readings(
    horizontal: int, vertical: int
) -> None:
    """38 readings split other than 20 and 18 would sit at the wrong angles."""
    h_levels = np.full(horizontal, 90.0)
    v_levels = np.full(vertical, 90.0)
    with pytest.raises(
        ValueError, match="'horizontal_levels_db' and 'vertical_levels_db' must hold"
    ):
        metrology.equal_area_directivity_factor(h_levels, v_levels)


def test_equal_area_readings_keep_their_planes() -> None:
    result = metrology.equal_area_directivity_factor(
        np.full(20, 90.0), np.full(18, 90.0)
    )
    np.testing.assert_array_equal(result.plane_angles_deg[:20], np.zeros(20))
    np.testing.assert_array_equal(result.plane_angles_deg[20:], np.full(18, 90.0))
    horizontal, vertical = metrology.equal_area_incidence_angles()
    np.testing.assert_array_equal(
        result.incidence_angles_deg, np.concatenate((horizontal, vertical))
    )


# --------------------------------------------------------------------------
# Formulas (1) and (A.6)
# --------------------------------------------------------------------------
def test_random_incidence_is_free_field_less_the_directivity_index() -> None:
    result = metrology.random_incidence_sensitivity(
        [1000.0, 4000.0, 8000.0], [0.2, -0.1, -0.8], [0.05, 0.85, 2.45]
    )
    np.testing.assert_allclose(result.random_incidence_level_db, [0.15, -0.95, -3.25])
    np.testing.assert_allclose(result.correction_db, [-0.05, -0.85, -2.45])


def test_a_single_free_field_level_is_spread_over_the_bands() -> None:
    result = metrology.random_incidence_sensitivity([1000.0, 2000.0], 0.0, [0.1, 0.2])
    np.testing.assert_allclose(result.free_field_level_db, [0.0, 0.0])


def test_random_incidence_refuses_a_column_of_the_wrong_length() -> None:
    with pytest.raises(
        ValueError, match="'directivity_index_db' must hold one value per frequency"
    ):
        metrology.random_incidence_sensitivity([1000.0, 2000.0], 0.0, [0.1, 0.2, 0.3])


def test_random_incidence_refuses_frequencies_out_of_order() -> None:
    with pytest.raises(
        ValueError, match="'frequencies_hz' must be strictly increasing"
    ):
        metrology.random_incidence_sensitivity([2000.0, 1000.0], 0.0, 0.1)


def test_random_incidence_from_a_directivity_measurement() -> None:
    dirs = [
        metrology.axisymmetric_directivity_factor(_cardioid_levels(10.0)),
        metrology.directivity_factor(_omni(2, 36)),
    ]
    result = metrology.random_incidence_sensitivity(
        [1000.0, 2000.0], [0.0, 0.0], [d.directivity_index_db for d in dirs]
    )
    assert result.random_incidence_level_db[0] == pytest.approx(
        -10.0 * math.log10(dirs[0].gamma)
    )
    assert result.random_incidence_level_db[1] == pytest.approx(0.0, abs=1e-12)


def test_the_sensitivity_columns_are_read_only() -> None:
    result = metrology.random_incidence_sensitivity([1000.0], 0.0, 0.1)
    assert not result.random_incidence_level_db.flags.writeable
    assert not result.frequencies_hz.flags.writeable


# --------------------------------------------------------------------------
# Formulas (8) to (11) and Table B.1
# --------------------------------------------------------------------------
def test_table_b1_holds_every_printed_row() -> None:
    table = metrology.IEC61183_TABLE_B1
    printed = ref.IEC61183_TABLE_B1_PRINTED
    assert len(table) == len(_LOW_ROW_HZ) + len(printed) - 1
    for _label, lowest, highest, index, difference in printed:
        keys = [key for key in _LOW_ROW_HZ if lowest <= key <= highest] or [lowest]
        assert all(lowest <= key <= highest for key in keys)
        for key in keys:
            row = table[key]
            assert row.directivity_index_db == pytest.approx(index, abs=1e-12)
            assert row.diffuse_pressure_difference_db == pytest.approx(
                difference, abs=1e-12
            )


def test_table_b1_is_immutable() -> None:
    table = metrology.IEC61183_TABLE_B1
    assert isinstance(table, types.MappingProxyType)
    row = table[8000.0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.directivity_index_db = 0.0  # type: ignore[misc]


def test_formula_9_adds_the_random_incidence_level_of_the_reference() -> None:
    result = metrology.diffuse_field_sensitivity(
        [1000.0, 2000.0],
        [80.0, 81.0],
        [79.5, 80.2],
        reference_random_incidence_level_db=[-0.1, -0.3],
    )
    np.testing.assert_allclose(result.level_difference_db, [0.5, 0.8])
    np.testing.assert_allclose(result.diffuse_field_level_db, [0.4, 0.5])
    assert result.route == "random_incidence"


def test_formula_10_takes_the_directivity_of_table_b1_by_default() -> None:
    result = metrology.diffuse_field_sensitivity(
        [1000.0, 8000.0, 20000.0],
        [80.0, 80.0, 80.0],
        [80.0, 80.0, 80.0],
        reference_free_field_level_db=0.0,
    )
    np.testing.assert_allclose(result.reference_correction_db, [-0.05, -2.45, -6.70])
    np.testing.assert_allclose(result.diffuse_field_level_db, [-0.05, -2.45, -6.70])


def test_formula_10_with_a_known_directivity() -> None:
    result = metrology.diffuse_field_sensitivity(
        [1000.0],
        [80.0],
        [79.0],
        reference_free_field_level_db=[0.3],
        reference_directivity_index_db=[0.2],
    )
    np.testing.assert_allclose(result.diffuse_field_level_db, [1.1])


def test_formula_11_adds_the_diffuse_to_pressure_difference_of_table_b1() -> None:
    result = metrology.diffuse_field_sensitivity(
        [500.0, 8000.0, 16000.0],
        [70.0, 70.0, 70.0],
        [70.0, 70.0, 70.0],
        reference_pressure_level_db=-26.0,
    )
    np.testing.assert_allclose(result.reference_correction_db, [0.0, 1.20, 3.05])
    np.testing.assert_allclose(result.diffuse_field_level_db, [-26.0, -24.8, -22.95])


def test_table_b1_answers_an_exact_midband_frequency() -> None:
    """15 849 Hz is the base-ten midband of the 16 kHz band."""
    result = metrology.diffuse_field_sensitivity(
        [1000.0 * 10.0**1.2], [0.0], [0.0], reference_pressure_level_db=0.0
    )
    np.testing.assert_allclose(result.reference_correction_db, [3.05])


def test_table_b1_refuses_a_frequency_it_does_not_print() -> None:
    frequencies = [20.0, 1000.0]
    with pytest.raises(
        ValueError, match="pass 'reference_diffuse_pressure_difference_db' for it"
    ):
        metrology.diffuse_field_sensitivity(
            frequencies, 0.0, 0.0, reference_pressure_level_db=0.0
        )


def test_a_frequency_between_the_rows_is_refused() -> None:
    frequencies = [1100.0]
    with pytest.raises(
        ValueError, match="pass 'reference_directivity_index_db' for it"
    ):
        metrology.diffuse_field_sensitivity(
            frequencies, 0.0, 0.0, reference_free_field_level_db=0.0
        )


def test_exactly_one_reference_calibration_is_needed() -> None:
    frequencies = [1000.0]
    with pytest.raises(
        ValueError,
        match="Give exactly one calibration of the reference instrument: 'reference_random",
    ):
        metrology.diffuse_field_sensitivity(frequencies, 0.0, 0.0)


def test_two_reference_calibrations_are_refused() -> None:
    frequencies = [1000.0]
    with pytest.raises(
        ValueError,
        match="Give exactly one calibration of the reference instrument: 'reference_random",
    ):
        metrology.diffuse_field_sensitivity(
            frequencies,
            0.0,
            0.0,
            reference_random_incidence_level_db=0.0,
            reference_pressure_level_db=0.0,
        )


def test_a_correction_of_another_route_is_refused() -> None:
    frequencies = [1000.0]
    with pytest.raises(
        ValueError, match="'reference_directivity_index_db' belongs to the free_field"
    ):
        metrology.diffuse_field_sensitivity(
            frequencies,
            0.0,
            0.0,
            reference_pressure_level_db=0.0,
            reference_directivity_index_db=0.1,
        )


def test_the_diffuse_result_refuses_an_unknown_route() -> None:
    one = np.zeros(1)
    frequencies = np.ones(1)
    with pytest.raises(ValueError, match="'route' must be one of"):
        ri.DiffuseFieldSensitivity(
            frequencies_hz=frequencies,
            indicated_level_db=one,
            reference_indicated_level_db=one,
            reference_sensitivity_level_db=one,
            reference_correction_db=one,
            route="comparison",
        )


# --------------------------------------------------------------------------
# What the figures draw
# --------------------------------------------------------------------------
def _two_plane_result() -> ri.DirectivityFactor:
    phi = np.radians(np.arange(36) * 10.0)
    horizontal = 94.0 + 20.0 * np.log10(0.6 + 0.4 * np.cos(phi))
    vertical = 94.0 + 20.0 * np.log10(0.7 + 0.3 * np.cos(phi))
    return metrology.directivity_factor(np.vstack((horizontal, vertical)))


def test_the_response_is_one_closed_curve_per_plane() -> None:
    result = _two_plane_result()
    ax = result.plot()
    assert ax.name == "polar"
    lines = [line for line in ax.lines if line.get_label().startswith("X-")]
    assert len(lines) == 2
    for line, plane in zip(lines, (0.0, 90.0), strict=True):
        theta, radius = line.get_data()
        assert len(theta) == 37
        assert radius[0] == pytest.approx(radius[-1])
        mask = np.isclose(result.plane_angles_deg, plane)
        np.testing.assert_allclose(radius[:-1], result.relative_levels_db[mask])
    assert "10\\,\\lg\\gamma" in ax.get_title()
    plt.close("all")


def test_the_response_names_its_radial_unit() -> None:
    """The radius is L(phi) - L_rd in dB: the outermost label carries the unit."""
    ax = _two_plane_result().plot(language="es")
    ax.figure.canvas.draw()
    labels = [label.get_text() for label in ax.get_yticklabels()]
    assert labels[-1] == "0 dB"
    assert all("dB" not in label for label in labels[:-1])
    assert "−5" in labels
    plt.close("all")


def test_the_response_legend_stays_inside_its_own_figure() -> None:
    """The legend below the disc is the only key to the planes."""
    ax = _two_plane_result().plot()
    figure = ax.figure
    figure.canvas.draw()
    legend = ax.get_legend().get_window_extent()
    assert legend.y0 >= figure.bbox.y0
    assert legend.y1 <= figure.bbox.y1
    plt.close("all")


def test_the_equal_area_vertical_curve_runs_through_the_poles() -> None:
    """Formula (A.5) reads the poles in the horizontal plane only; the vertical
    curve borrows them rather than cutting a chord across each pole.
    """
    horizontal, vertical = metrology.equal_area_incidence_angles()

    def level(angle: np.ndarray) -> np.ndarray:
        return 94.0 + 20.0 * np.log10(0.55 + 0.45 * np.cos(np.radians(angle)))

    result = metrology.equal_area_directivity_factor(level(horizontal), level(vertical))
    ax = result.plot()
    curve = next(line for line in ax.lines if line.get_label().startswith("X-Z"))
    theta, radius = curve.get_data()
    degrees = np.degrees(theta[:-1])
    assert len(degrees) == 20
    for pole, index in ((0.0, 0), (180.0, 10)):
        at_pole = np.isclose(degrees, pole)
        assert radius[:-1][at_pole] == pytest.approx(result.relative_levels_db[index])
    plt.close("all")


def test_the_axisymmetric_weights_title_counts_two_elements_to_a_reading() -> None:
    """One plane weighs each reading 2K: the curve peaks at twice the largest
    element the title names.
    """
    result = metrology.axisymmetric_directivity_factor(_cardioid_levels(10.0))
    ax = result.plot(view="weights")
    _x, y = ax.lines[0].get_data()
    assert "two elements to a reading" in ax.get_title()
    assert "2.18 %" in ax.get_title()
    assert float(np.max(y)) == pytest.approx(
        2.0 * 100.0 * result.largest_element_fraction, rel=1e-12
    )
    plt.close("all")


def test_the_response_needs_a_polar_axes() -> None:
    result = _two_plane_result()
    _fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="polar"):
        result.plot(ax=ax)
    plt.close("all")


def test_the_weights_view_draws_table_a1_in_per_cent() -> None:
    ax = _two_plane_result().plot(view="weights")
    x, y = ax.lines[0].get_data()
    np.testing.assert_allclose(x, np.arange(0, 360, 10))
    np.testing.assert_allclose(y, 100.0 * metrology.adjustment_factors(10.0))
    assert "2.18 %" in ax.get_title()
    plt.close("all")


def test_an_unknown_view_is_refused() -> None:
    result = _two_plane_result()
    with pytest.raises(ValueError, match="Unknown view"):
        result.plot(view="sphere")


def test_the_axisymmetric_and_equal_area_legends_name_their_method() -> None:
    symmetric = metrology.axisymmetric_directivity_factor(_cardioid_levels(10.0))
    ax = symmetric.plot(language="es")
    assert "Un plano, simetría de revolución" in ax.get_legend_handles_labels()[1]
    plt.close("all")
    equal = metrology.equal_area_directivity_factor(
        np.full(20, 90.0), np.full(18, 90.0)
    )
    ax = equal.plot(view="weights")
    assert ax.get_legend_handles_labels()[1] == ["1/38 for every direction"]
    plt.close("all")


def test_four_planes_are_labelled_by_their_angle() -> None:
    result = metrology.directivity_factor(_omni(4, 36))
    labels = result.plot().get_legend_handles_labels()[1]
    assert labels[1] == r"Plane $\alpha$ = 45°"
    plt.close("all")


def test_the_sensitivity_views_draw_the_levels_and_the_correction() -> None:
    result = metrology.random_incidence_sensitivity(
        [1000.0, 4000.0, 8000.0], [0.2, -0.1, -0.8], [0.05, 0.85, 2.45]
    )
    ax = result.plot()
    np.testing.assert_allclose(ax.lines[0].get_ydata(), result.free_field_level_db)
    np.testing.assert_allclose(
        ax.lines[1].get_ydata(), result.random_incidence_level_db
    )
    plt.close("all")
    ax = result.plot(view="correction", language="es")
    np.testing.assert_allclose(ax.lines[0].get_ydata(), [-0.05, -0.85, -2.45])
    assert ax.get_ylabel() == "Corrección [dB]"
    plt.close("all")
    with pytest.raises(ValueError, match="Unknown view"):
        result.plot(view="polar")


@pytest.mark.parametrize(
    ("factory", "view"),
    [
        (_two_plane_result, "weights"),
        (
            lambda: metrology.random_incidence_sensitivity(
                [1000.0, 2000.0], 0.0, [0.05, 0.2]
            ),
            "correction",
        ),
    ],
)
def test_the_other_views_forward_style_to_their_first_curve(
    factory: object, view: str
) -> None:
    """The contract of tests/test_result_plots.py, on the views it does not reach."""
    result = factory()  # type: ignore[operator]
    ax = result.plot(view=view, c="red", lw=2, label="mine")
    assert ax.lines[0].get_linewidth() == pytest.approx(2.0)
    assert ax.lines[0].get_color() == "red"
    assert "mine" in ax.get_legend_handles_labels()[1]
    plt.close("all")


def test_the_diffuse_figure_draws_the_three_terms() -> None:
    result = metrology.diffuse_field_sensitivity(
        [1000.0, 8000.0], [80.0, 81.0], [79.5, 80.0], reference_pressure_level_db=-26.0
    )
    ax = result.plot()
    np.testing.assert_allclose(ax.lines[0].get_ydata(), result.diffuse_field_level_db)
    np.testing.assert_allclose(
        ax.lines[1].get_ydata(), result.reference_diffuse_field_level_db
    )
    np.testing.assert_allclose(ax.lines[2].get_ydata(), result.level_difference_db)
    assert "Formula (11)" in ax.get_legend_handles_labels()[1][1]
    plt.close("all")
