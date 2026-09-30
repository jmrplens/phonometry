#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the laboratory improvement of linings and floor coverings.

ISO 10140-1:2021 Annexes G and H, rated on the reference elements of
ISO 717-1:2020 Annex E and ISO 717-2:2020 Table 4.

Oracles:

- The reference curves band by band, typed from the printed pages
  (ISO 717-1:2020 Table E.1, ISO 717-2:2020 Table 4).
- The single numbers printed under every reference curve, integer and to one
  decimal place, which the published curves must reproduce through the ISO 717
  rating engine.
- A sloped improvement on every reference floor and a sloped lining on every
  standard element, rated by a rater written from the printed clauses of
  ISO 717-1 and ISO 717-2 and not by the library: a flat spectrum cannot tell
  the reference curves apart, nor C from Ctr. A second lining, with a
  resonance dip at 100 Hz and a coincidence dip at 4 000 Hz, rated the same
  way, gives every two of the nine lining terms different values on at least
  one element, so no two of them can be swapped unseen.
- ISO 717-2:2020 Annex C, Table C.2, end to end through the Annex H front end:
  ΔLw = 15 dB as printed, and CI,Δ = -9 dB from the Table 4 floor, where the
  print's own chain gives -8 dB (docs/ERRATA.md).
- The G.4 example: two measurements within 1 d may start 3 d after the end of
  construction; and the same bound reached by decimal inputs (2,1 d after
  6,3 d), which binary rounding would put a hair above it.
- Closed forms: a flat improvement shifts every rating one for one, to one
  decimal place as well, and a curve laid on the ISO 717-1 reference rates at
  the reference plus two.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest
import reference_data as ref

from phonometry import building
from phonometry.building.measurement.lab_improvement import (
    LabFloorCoveringImprovementResult,
    LabLiningImprovementResult,
)

#: The 16 rating bands, 100 Hz to 3150 Hz.
_CORE = [float(f) for f in ref.ISO717_2_REFERENCE_FLOOR_FREQ]
#: The 21 bands of ISO 717-1:2020 Table E.1, 50 Hz to 5000 Hz.
_TABLE_E1 = [50.0, 63.0, 80.0, *_CORE, 4000.0, 5000.0]
#: ISO 717-1 Table 3 airborne reference curve, 100 Hz to 3150 Hz.
_REF_AIRBORNE = np.array(
    [33, 36, 39, 42, 45, 48, 51, 52, 53, 54, 55, 56, 56, 56, 56, 56], dtype=float
)


def _curve(table: object, bands: list[float]) -> np.ndarray:
    return np.asarray([table[f] for f in bands], dtype=float)  # type: ignore[index]


# --- The published reference curves against their printed single numbers ---


@pytest.mark.parametrize("element", sorted(ref.ISO717_1_TABLE_E1_PRINTED))
@pytest.mark.parametrize("one_decimal", [False, True])
def test_table_e1_curves_reproduce_every_printed_term(
    element: str, *, one_decimal: bool
) -> None:
    """ISO 717-1:2020 Table E.1: Rw and all eight adaptation terms, both forms."""
    printed = ref.ISO717_1_TABLE_E1_PRINTED[element]
    curve = _curve(building.LINING_REFERENCE_ELEMENTS[element], _TABLE_E1)
    rated = building.weighted_rating_extended(curve, _TABLE_E1, one_decimal=one_decimal)
    column = 1 if one_decimal else 0
    for term, values in printed.items():
        assert getattr(rated, term) == pytest.approx(values[column], abs=1e-9), term


@pytest.mark.parametrize("floor", sorted(ref.ISO717_2_TABLE4_PRINTED))
@pytest.mark.parametrize("one_decimal", [False, True])
def test_table_4_curves_reproduce_their_printed_ratings(
    floor: str, *, one_decimal: bool
) -> None:
    """ISO 717-2:2020 Table 4: Ln,r,0,w and CI,r,0 of every floor, both forms."""
    (rating, rating_1dp), (ci, ci_1dp) = ref.ISO717_2_TABLE4_PRINTED[floor]
    curve = _curve(building.IMPACT_REFERENCE_FLOORS[floor], _CORE)
    rated = building.weighted_impact_rating_extended(curve, one_decimal=one_decimal)
    expected = (rating_1dp, ci_1dp) if one_decimal else (rating, ci)
    got = (rated.rating, rated.ci)
    assert got == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("element", sorted(ref.ISO717_1_TABLE_E1_CURVES))
def test_table_e1_curves_are_the_printed_bands(element: str) -> None:
    """ISO 717-1:2020 Table E.1, all 21 bands of each element as printed."""
    table = building.LINING_REFERENCE_ELEMENTS[element]
    assert tuple(table) == ref.ISO717_1_TABLE_E1_BANDS
    assert tuple(table.values()) == ref.ISO717_1_TABLE_E1_CURVES[element]


@pytest.mark.parametrize(
    ("floor", "column"),
    [
        ("heavyweight", "heavyweight"),
        ("lightweight_1", "lightweight_1_and_2"),
        ("lightweight_2", "lightweight_1_and_2"),
        ("lightweight_3", "lightweight_3"),
    ],
)
def test_table_4_curves_are_the_printed_bands(floor: str, column: str) -> None:
    """ISO 717-2:2020 Table 4, all 16 bands of each floor as printed."""
    table = building.IMPACT_REFERENCE_FLOORS[floor]
    assert tuple(table) == tuple(_CORE)
    assert tuple(table.values()) == ref.ISO717_2_TABLE4_CURVES[column]


def test_floors_one_and_two_share_the_printed_column() -> None:
    floors = building.IMPACT_REFERENCE_FLOORS
    assert floors["lightweight_1"] == floors["lightweight_2"]
    assert tuple(floors["heavyweight"]) == tuple(_CORE)


def test_reference_tables_refuse_writes() -> None:
    heavy = building.IMPACT_REFERENCE_FLOORS["heavyweight"]
    elements = building.LINING_REFERENCE_ELEMENTS
    with pytest.raises(TypeError, match=r"does not support item assignment"):
        heavy[100.0] = 0.0  # type: ignore[index]
    with pytest.raises(TypeError, match=r"does not support item assignment"):
        elements["heavy_wall"] = {}  # type: ignore[index]


# --- ISO 717-2 Clauses 5 and 6 on every floor --------------------------------


@pytest.mark.parametrize("floor", sorted(building.IMPACT_REFERENCE_FLOORS))
def test_flat_improvement_shifts_every_floor_one_for_one(floor: str) -> None:
    flat = np.full(16, 10.0)
    assert building.weighted_impact_improvement(flat, reference_floor=floor) == 10
    assert building.impact_improvement_adaptation_term(flat, reference_floor=floor) == 0
    assert (
        building.weighted_impact_improvement(np.zeros(16), reference_floor=floor) == 0
    )


@pytest.mark.parametrize("floor", sorted(building.IMPACT_REFERENCE_FLOORS))
def test_flat_improvement_to_one_decimal_is_exact(floor: str) -> None:
    """Both curves rated with the 0,1 dB shift: a flat 10 dB is 10,0 and 0,0.

    Rating only one of the two curves with the 0,1 dB shift would move ΔLw by
    up to half a decibel on every floor.
    """
    flat = np.full(16, 10.0)
    assert building.weighted_impact_improvement(
        flat, reference_floor=floor, one_decimal=True
    ) == pytest.approx(10.0, abs=1e-9)
    assert building.impact_improvement_adaptation_term(
        flat, reference_floor=floor, one_decimal=True
    ) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("floor", sorted(ref.ISO717_2_SLOPED_EXPECTED))
def test_sloped_improvement_is_rated_on_each_floor(floor: str) -> None:
    """ISO 717-2 Clauses 5 and 6 on a sloped ΔL, rated independently."""
    dl = np.asarray(ref.ISO717_2_SLOPED_DELTA_L)
    delta_lw, ci_delta, ln_r_w, ci_r = ref.ISO717_2_SLOPED_EXPECTED[floor]
    assert building.weighted_impact_improvement(dl, reference_floor=floor) == delta_lw
    assert (
        building.impact_improvement_adaptation_term(dl, reference_floor=floor)
        == ci_delta
    )
    bare = np.full(16, 80.0)
    res = building.lab_floor_covering_improvement(
        bare, bare - dl, _CORE, reference_floor=floor
    )
    assert (res.delta_lw_db, res.ci_delta_db) == (delta_lw, ci_delta)
    assert res.reference_rating is not None
    assert (res.reference_rating.rating, res.reference_rating.ci) == (ln_r_w, ci_r)


def test_one_decimal_improvement_keeps_the_tenth() -> None:
    """5.4 states ΔLw to one decimal with its uncertainty (EXAMPLE 18,9)."""
    dl = np.asarray(ref.ISO717_2_ANNEX_C2_DELTA_L)
    value = building.weighted_impact_improvement(dl, one_decimal=True)
    assert isinstance(value, float)
    assert abs(value - ref.ISO717_2_ANNEX_C2_DELTA_LW) <= 1.0
    assert round(value, 1) == pytest.approx(value, abs=1e-9)


@pytest.mark.parametrize("one_decimal", [False, True])
def test_a_band_mapping_is_rated_as_the_array_on_floor_no_3(
    *, one_decimal: bool
) -> None:
    """One key per band, given highest band first, is read band by band.

    ``ΔLt,3,w`` and ``CIΔ,t3`` of a mapping are those of the same 16 values
    as an array, integer and to one decimal place alike, and the integer pair
    is the one the independent rater gives for floor No 3.
    """
    dl = np.asarray(ref.ISO717_2_SLOPED_DELTA_L)
    by_band = dict(zip(reversed(_CORE), dl[::-1].tolist(), strict=True))
    rated = []
    for call in (
        building.weighted_impact_improvement,
        building.impact_improvement_adaptation_term,
    ):
        from_mapping = call(
            by_band, reference_floor="lightweight_3", one_decimal=one_decimal
        )
        from_array = call(dl, reference_floor="lightweight_3", one_decimal=one_decimal)
        assert type(from_mapping) is (float if one_decimal else int)
        assert from_mapping == pytest.approx(from_array, abs=1e-12)
        rated.append(from_mapping)
    delta_lw, ci_delta = rated
    expected = ref.ISO717_2_SLOPED_EXPECTED["lightweight_3"][:2]
    if one_decimal:
        assert round(delta_lw, 1) == pytest.approx(delta_lw, abs=1e-9)
        assert round(ci_delta, 1) == pytest.approx(ci_delta, abs=1e-9)
        assert abs(delta_lw - expected[0]) <= 1.0
        assert abs(ci_delta - expected[1]) <= 1.0
    else:
        assert tuple(rated) == expected


def test_unknown_reference_floor_is_refused() -> None:
    zeros = np.zeros(16)
    with pytest.raises(ValueError, match=r"reference_floor"):
        building.weighted_impact_improvement(zeros, reference_floor="concrete")  # type: ignore[call-overload]


# --- ISO 717-1 Annex D -------------------------------------------------------


@pytest.mark.parametrize("element", sorted(building.LINING_REFERENCE_ELEMENTS))
def test_flat_lining_improvement_shifts_every_term(element: str) -> None:
    rating = building.weighted_reduction_improvement(
        np.full(21, 10.0), _TABLE_E1, basic_element=element
    )
    terms = (
        rating.delta_rw,
        rating.delta_rw_c,
        rating.delta_rw_ctr,
        rating.delta_rw_c_50_3150,
        rating.delta_rw_c_50_5000,
        rating.delta_rw_c_100_5000,
        rating.delta_rw_ctr_50_3150,
        rating.delta_rw_ctr_50_5000,
        rating.delta_rw_ctr_100_5000,
    )
    assert terms == (10,) * 9


@pytest.mark.parametrize("element", sorted(building.LINING_REFERENCE_ELEMENTS))
def test_flat_lining_improvement_to_one_decimal_is_exact(element: str) -> None:
    """Both curves rated with the 0,1 dB shift: every term of a flat 10 dB is 10,0."""
    rating = building.weighted_reduction_improvement(
        np.full(21, 10.0), _TABLE_E1, basic_element=element, one_decimal=True
    )
    terms = (
        rating.delta_rw,
        rating.delta_rw_c,
        rating.delta_rw_ctr,
        rating.delta_rw_c_50_3150,
        rating.delta_rw_c_50_5000,
        rating.delta_rw_c_100_5000,
        rating.delta_rw_ctr_50_3150,
        rating.delta_rw_ctr_50_5000,
        rating.delta_rw_ctr_100_5000,
    )
    assert terms == pytest.approx((10.0,) * 9, abs=1e-9)


@pytest.mark.parametrize("element", sorted(ref.ISO717_1_SLOPED_EXPECTED))
def test_sloped_lining_is_rated_on_each_element(element: str) -> None:
    """ISO 717-1 Annex D on a sloped ΔR over 21 bands, rated independently."""
    rating = building.weighted_reduction_improvement(
        ref.ISO717_1_SLOPED_DELTA_R, _TABLE_E1, basic_element=element
    )
    terms = (
        rating.delta_rw,
        rating.delta_rw_c,
        rating.delta_rw_ctr,
        rating.delta_rw_c_50_3150,
        rating.delta_rw_c_50_5000,
        rating.delta_rw_c_100_5000,
        rating.delta_rw_ctr_50_3150,
        rating.delta_rw_ctr_50_5000,
        rating.delta_rw_ctr_100_5000,
    )
    assert terms == ref.ISO717_1_SLOPED_EXPECTED[element]


_NINE_TERMS = (
    "delta_rw",
    "delta_rw_c",
    "delta_rw_ctr",
    "delta_rw_c_50_3150",
    "delta_rw_c_50_5000",
    "delta_rw_c_100_5000",
    "delta_rw_ctr_50_3150",
    "delta_rw_ctr_50_5000",
    "delta_rw_ctr_100_5000",
)


@pytest.mark.parametrize("element", sorted(ref.ISO717_1_DIPPED_EXPECTED))
def test_dipped_lining_tells_every_term_apart(element: str) -> None:
    """ISO 717-1 Annex D on a ΔR with a resonance dip and a coincidence dip.

    The bands 50 Hz to 80 Hz and 4 000 Hz to 5 000 Hz that set the enlarged
    ranges apart weigh here, so a term wired to the wrong spectrum or range
    gives a number the independent rater did not.
    """
    rating = building.weighted_reduction_improvement(
        ref.ISO717_1_DIPPED_DELTA_R, _TABLE_E1, basic_element=element
    )
    terms = tuple(getattr(rating, name) for name in _NINE_TERMS)
    assert terms == ref.ISO717_1_DIPPED_EXPECTED[element]


def test_lining_oracles_tell_every_pair_of_terms_apart() -> None:
    """Between them the elements give every two of the nine terms a difference.

    Otherwise swapping those two terms in the rating would pass every test.
    """
    expected = ref.ISO717_1_DIPPED_EXPECTED.values()
    for i, j in itertools.combinations(range(len(_NINE_TERMS)), 2):
        assert any(row[i] != row[j] for row in expected), (
            _NINE_TERMS[i],
            _NINE_TERMS[j],
        )


def test_sloped_lining_direct_differences_formula_d2() -> None:
    """Formula (D.2) on two measured curves that are not parallel."""
    without = np.asarray(ref.ISO717_1_MEASURED_WALL_R)
    with_ = without + np.asarray(ref.ISO717_1_SLOPED_DELTA_R)
    res = building.lab_lining_improvement(without, with_, _TABLE_E1, basic_element=None)
    direct = (
        res.delta_rw_direct_db,
        res.delta_rw_c_direct_db,
        res.delta_rw_ctr_direct_db,
    )
    assert direct == ref.ISO717_1_MEASURED_WALL_DIRECT


def test_lining_rating_on_the_reference_shape() -> None:
    """Rref,with laid on the ISO 717-1 reference + 20 rates at 72 + 2 = 74 dB.

    The Table 3 curve shifted by +20 dB has no unfavourable deviation; the
    shift search then goes two more steps (16 bands x 2 dB = 32 dB), so
    Rw,with = 52 + 22 = 74 and ΔRw = 74 - 53 on the heavy wall.
    """
    without = _curve(building.LINING_REFERENCE_ELEMENTS["heavy_wall"], _CORE)
    delta = _REF_AIRBORNE + 20.0 - without
    rating = building.weighted_reduction_improvement(delta)
    assert rating.with_lining.rating == 74
    assert rating.delta_rw == 74 - 53
    assert rating.index == "heavy"
    light = building.weighted_reduction_improvement(
        np.zeros(16), basic_element="lightweight_wall"
    )
    assert (light.index, light.delta_rw, light.delta_rw_c_50_3150) == ("light", 0, None)


def test_lining_rating_refuses_bands_outside_table_e1() -> None:
    freqs = [*_CORE, 6300.0]
    delta = np.zeros(17)
    with pytest.raises(ValueError, match=r"Table E\.1"):
        building.weighted_reduction_improvement(delta, freqs)


def test_lining_rating_refuses_a_band_given_twice() -> None:
    freqs = [*_CORE, 3150.0]
    delta = np.zeros(17)
    with pytest.raises(ValueError, match=r"each given once"):
        building.weighted_reduction_improvement(delta, freqs)


def test_lining_rating_refuses_an_unknown_element() -> None:
    zeros = np.zeros(16)
    with pytest.raises(ValueError, match=r"basic_element"):
        building.weighted_reduction_improvement(zeros, basic_element="brick")  # type: ignore[arg-type]


# --- Annex G -----------------------------------------------------------------


def test_lab_lining_improvement_on_the_heavy_wall() -> None:
    freqs = [*_CORE, 4000.0, 5000.0]
    without = np.linspace(40.0, 65.0, 18)
    with_ = without + 10.0
    res = building.lab_lining_improvement(without, with_, freqs)
    np.testing.assert_allclose(res.delta_r_db, 10.0)
    assert res.rating is not None
    assert (res.rating.delta_rw, res.rating.delta_rw_c, res.rating.delta_rw_ctr) == (
        10,
        10,
        10,
    )
    assert (
        res.delta_rw_direct_db,
        res.delta_rw_c_direct_db,
        res.delta_rw_ctr_direct_db,
    ) == (10, 10, 10)
    centres, octaves = res.octave_bands()
    np.testing.assert_allclose(centres, [125, 250, 500, 1000, 2000, 4000])
    np.testing.assert_allclose(octaves, 10.0)


def test_other_basic_element_keeps_only_the_direct_difference() -> None:
    res = building.lab_lining_improvement(
        np.full(16, 40.0), np.full(16, 45.0), _CORE, basic_element=None
    )
    assert res.rating is None
    assert res.delta_rw_direct_db == 5


def test_lining_spectrum_without_rating_bands_has_no_rating() -> None:
    res = building.lab_lining_improvement([40, 41], [45, 47], [500, 630])
    assert (res.rating, res.delta_rw_direct_db) == (None, None)


def test_octave_formula_d1_averages_energy_not_decibels() -> None:
    """(D.1): -10 lg((10^-0 + 10^-1 + 10^-2)/3) for 0, 10 and 20 dB."""
    res = building.lab_lining_improvement(
        [40.0, 40.0, 40.0], [40.0, 50.0, 60.0], [100.0, 125.0, 160.0]
    )
    _, octaves = res.octave_bands()
    expected = -10.0 * np.log10((1.0 + 0.1 + 0.01) / 3.0)
    assert octaves[0] == pytest.approx(expected, abs=1e-12)


def test_lining_result_refuses_mismatched_columns() -> None:
    two_bands = np.array([100.0, 125.0])
    one_level = np.array([40.0])
    two_levels = np.array([45.0, 46.0])
    with pytest.raises(ValueError, match=r"LabLiningImprovementResult"):
        LabLiningImprovementResult(
            frequencies_hz=two_bands,
            r_without_db=one_level,
            r_with_db=two_levels,
            delta_r_db=two_levels,
            basic_element=None,
            rating=None,
            delta_rw_direct_db=None,
            delta_rw_c_direct_db=None,
            delta_rw_ctr_direct_db=None,
        )


def test_lab_lining_improvement_refuses_mismatched_inputs() -> None:
    three = [40.0, 41.0, 42.0]
    with pytest.raises(ValueError, match=r"lab_lining_improvement"):
        building.lab_lining_improvement(three, [45.0, 46.0], [100.0, 125.0, 160.0])


# --- G.4 curing --------------------------------------------------------------


def test_curing_example_of_g4_sits_on_the_bound() -> None:
    """Measurements within 1 d can start 3 d after the end of construction."""
    check = building.check_lining_curing(3.0, 1.0)
    assert (check.passes, check.cured, check.lag_within_third) == (True, False, True)
    assert check.earliest_start_days == pytest.approx(3.0)


def test_curing_one_day_early_fails() -> None:
    check = building.check_lining_curing(2.9, 1.0)
    assert not check.passes


@pytest.mark.parametrize(
    ("curing", "lag"), [(6.3, 2.1), (0.3, 0.1), (0.6, 0.2), (3.3, 1.1), (12.6, 4.2)]
)
def test_lag_of_one_third_on_decimal_inputs_sits_on_the_bound(
    curing: float, lag: float
) -> None:
    """3 x 2,1 is 6,300000000000001 in binary, still "one-third" of 6,3 d."""
    check = building.check_lining_curing(curing, lag)
    assert check.lag_within_third
    assert check.passes


def test_lag_just_over_one_third_fails() -> None:
    check = building.check_lining_curing(6.3, 2.1001)
    assert not check.lag_within_third
    assert not check.passes


def test_curing_period_reached_by_decimal_arithmetic_is_reached() -> None:
    """1,4 d / 0,1 is 13,999999999999998 in binary, and two weeks all the same."""
    check = building.check_lining_curing(1.4 / 0.1, 10.0)
    assert check.cured
    assert check.passes
    assert not building.check_lining_curing(13.99, 10.0).cured


def test_two_weeks_of_curing_frees_the_lag() -> None:
    assert building.check_lining_curing(14.0, 10.0).passes
    assert not building.check_lining_curing(
        14.0, 10.0, required_curing_days=28.0
    ).passes


def test_curing_verdict_has_no_truth_value() -> None:
    check = building.check_lining_curing(20.0, 1.0)
    with pytest.raises(TypeError, match=r"passes"):
        bool(check)


def test_curing_refuses_a_negative_time() -> None:
    with pytest.raises(ValueError, match=r"time_lag_days"):
        building.check_lining_curing(3.0, -1.0)


# --- Annex H -----------------------------------------------------------------


def test_annex_c2_example_through_the_annex_h_front_end() -> None:
    """ISO 717-2:2020 Table C.2 on the heavy floor: ΔLw = 15 dB as printed.

    CI,Δ = -9 dB is the value the Table 4 floor gives; the print's own chain
    implies -8 dB (docs/ERRATA.md, ISO 717-2:2020 Annex C, example C.2).
    """
    dl = np.asarray(ref.ISO717_2_ANNEX_C2_DELTA_L)
    bare = np.full(16, 75.0)
    res = building.lab_floor_covering_improvement(bare, bare - dl, _CORE)
    assert (res.delta_lw_db, res.ci_delta_db) == (
        ref.ISO717_2_ANNEX_C2_DELTA_LW,
        ref.ISO717_2_ANNEX_C2_CI_DELTA,
    )
    assert res.designation == "ΔLw"
    heavy = _curve(building.IMPACT_REFERENCE_FLOORS["heavyweight"], _CORE)
    assert res.reference_rating is not None
    assert (
        res.reference_rating.rating
        == building.weighted_impact_rating(heavy - dl).rating
    )
    assert res.bare_rating is not None
    assert res.bare_rating.rating == building.weighted_impact_rating(bare).rating


@pytest.mark.parametrize(
    ("floor", "designation"),
    [
        ("lightweight_1", "ΔLt,1,w"),
        ("lightweight_2", "ΔLt,2,w"),
        ("lightweight_3", "ΔLt,3,w"),
    ],
)
def test_lightweight_floors_are_rated_on_their_own_curve(
    floor: str, designation: str
) -> None:
    dl = np.linspace(2.0, 30.0, 18)
    bare = np.full(18, 70.0)
    freqs = [*_CORE, 4000.0, 5000.0]
    res = building.lab_floor_covering_improvement(
        bare, bare - dl, freqs, reference_floor=floor
    )
    assert res.designation == designation
    assert res.delta_lw_db == building.weighted_impact_improvement(
        dl[:16], reference_floor=floor
    )
    assert res.ci_delta_db == building.impact_improvement_adaptation_term(
        dl[:16], reference_floor=floor
    )


def test_octave_formula_h2() -> None:
    res = building.lab_floor_covering_improvement(
        [70.0, 70.0, 70.0], [70.0, 60.0, 50.0], [800.0, 1000.0, 1250.0]
    )
    centres, octaves = res.octave_bands()
    assert centres.tolist() == [1000.0]
    assert octaves[0] == pytest.approx(-10.0 * np.log10((1.0 + 0.1 + 0.01) / 3.0))
    assert res.delta_lw_db is None


def test_floor_covering_result_refuses_an_unknown_floor() -> None:
    one = np.array([1.0])
    band = np.array([500.0])
    with pytest.raises(ValueError, match=r"reference_floor"):
        LabFloorCoveringImprovementResult(
            frequencies_hz=band,
            l_n0_db=one,
            l_n_db=one,
            improvement_db=one,
            reference_floor="timber",
            delta_lw_db=None,
            ci_delta_db=None,
            reference_rating=None,
            bare_rating=None,
        )


def test_heavy_impact_improvement_is_formula_h3() -> None:
    res = building.heavy_impact_improvement(
        [80.0, 75.0, 70.0, 65.0], [78.0, 70.0, 62.0, 55.0], [63, 125, 250, 500]
    )
    np.testing.assert_allclose(res.improvement_db, [2.0, 5.0, 8.0, 10.0])


def test_heavy_impact_improvement_refuses_mismatched_inputs() -> None:
    two = [80.0, 75.0]
    with pytest.raises(ValueError, match=r"heavy_impact_improvement"):
        building.heavy_impact_improvement(two, [78.0], [63, 125])


# --- Figures -----------------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "es"])
def test_every_result_plots(language: str) -> None:
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    freqs = [*_CORE, 4000.0, 5000.0]
    lining = building.lab_lining_improvement(
        np.linspace(40.0, 65.0, 18), np.linspace(40.0, 65.0, 18) + 8.0, freqs
    )
    covering = building.lab_floor_covering_improvement(
        np.full(18, 70.0), np.full(18, 70.0) - np.linspace(2.0, 30.0, 18), freqs
    )
    heavy = building.heavy_impact_improvement([80.0, 75.0], [78.0, 70.0], [63, 125])
    assert lining.rating is not None
    for result in (
        lining,
        lining.rating,
        covering,
        heavy,
        building.check_lining_curing(3.0, 1.0),
        building.check_lining_curing(2.0, 1.0),
    ):
        ax = result.plot(language=language)
        assert ax.get_title()
        plt.close(ax.figure)


def _line(ax: object, label: str) -> np.ndarray:
    lines = [line for line in ax.get_lines() if line.get_label() == label]  # type: ignore[attr-defined]
    assert len(lines) == 1, label
    return np.asarray(lines[0].get_ydata(), dtype=float)


def test_covering_figure_draws_the_improvement_and_names_its_terms() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    dl = np.asarray(ref.ISO717_2_SLOPED_DELTA_L)
    bare = np.full(16, 80.0)
    res = building.lab_floor_covering_improvement(
        bare, bare - dl, _CORE, reference_floor="lightweight_3"
    )
    ax = res.plot()
    np.testing.assert_allclose(_line(ax, r"$\Delta L$"), res.improvement_db)
    title = ax.get_title()
    assert r"$\Delta L_\mathrm{t,3,w}$ = 11 dB" in title
    assert r"$C_{\mathrm{I}\Delta,\mathrm{t3}}$ = −3 dB" in title
    plt.close(ax.figure)
    heavy = building.lab_floor_covering_improvement(bare, bare - dl, _CORE)
    ax = heavy.plot()
    assert r"$C_{\mathrm{I},\Delta}$ = −10 dB" in ax.get_title()
    plt.close(ax.figure)


def test_heavy_impact_figure_draws_formula_h3() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    res = building.heavy_impact_improvement(
        [80.0, 75.0, 70.0, 65.0], [78.0, 70.0, 62.0, 55.0], [63, 125, 250, 500]
    )
    ax = res.plot()
    np.testing.assert_allclose(
        _line(ax, r"$\Delta L_\mathrm{r}$"), [2.0, 5.0, 8.0, 10.0]
    )
    plt.close(ax.figure)


def test_lining_rating_figure_draws_both_reference_curves() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    rating = building.weighted_reduction_improvement(
        ref.ISO717_1_SLOPED_DELTA_R, _TABLE_E1, basic_element="heavy_wall"
    )
    ax = rating.plot()
    ydata = sorted((line.get_ydata() for line in ax.get_lines()), key=np.sum)
    curve = np.asarray(ref.ISO717_1_TABLE_E1_CURVES["heavy_wall"])
    np.testing.assert_allclose(ydata[0], curve)
    np.testing.assert_allclose(ydata[1], curve + ref.ISO717_1_SLOPED_DELTA_R)
    assert r"$\Delta R_\mathrm{w,heavy}$ = 6 dB" in ax.get_title()
    plt.close(ax.figure)


def test_lining_figure_names_the_rating_it_drew() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    res = building.lab_lining_improvement(
        np.full(16, 40.0), np.full(16, 52.0), _CORE, basic_element="lightweight_wall"
    )
    ax = res.plot()
    assert r"\Delta R_\mathrm{w,light}$ = 12 dB" in ax.get_title()
    lines = [line for line in ax.get_lines() if line.get_label() == r"$\Delta R$"]
    np.testing.assert_allclose(lines[0].get_ydata(), 12.0)
    plt.close(ax.figure)
