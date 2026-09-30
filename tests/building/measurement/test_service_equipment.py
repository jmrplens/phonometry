#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Tests for the service-equipment engineering method (ISO/DIS 16032:2023).

The draft prints no worked example. The oracles are the numbers it prints and
the closed forms it states:

* **Clause 9**, folio 10: a background 4 dB below gives a correction of
  2,2 dB, and below 4 dB the correction is held there.
* **Table A.1**, folio 12, as printed, with the C-weighting cells the library
  takes from IEC 61672-1:2013 Table 3 instead, pinned against the library's
  own copy of that table.
* **Table 2**, folio 10: the reproducibility standard deviations.
* **Formulae (1), (2), (3), (5), (6) and (8)** and the ladder of 7.4.1, checked
  against identities a reader can do by hand (a reverberation time equal to
  :math:`T_0`, a volume that makes :math:`0{,}16\,V/T = A_0`, a flat spectrum)
  and against values worked by hand where an identity would hide a reversed
  formula (an equivalent absorption area of 16 m² normalized to 10 m² gains
  :math:`10 \lg 1{,}6`).
"""

from __future__ import annotations

import dataclasses
import math
import types
from typing import TYPE_CHECKING

import matplotlib as mpl
import numpy as np
import pytest
from reference_data import service_equipment as ref

mpl.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.text import Annotation

from phonometry import building
from phonometry.filters.weighting_compliance import _WEIGHTING_TABLE3

if TYPE_CHECKING:
    from matplotlib.axes import Axes

THIRD = np.array([row[0] for row in ref.ISO16032_TABLE_A1_THIRD])
OCTAVE = np.array([row[0] for row in ref.ISO16032_TABLE_A1_OCTAVE])
RESTRICTED = THIRD[(THIRD >= 50.0) & (THIRD <= 5000.0)]


def _flat(level: float, freqs: np.ndarray = THIRD, readings: int = 3) -> np.ndarray:
    return np.full((readings, freqs.size), level)


def _energy_sum(levels: list[float] | np.ndarray) -> float:
    return 10.0 * math.log10(float(np.sum(10.0 ** (0.1 * np.asarray(levels)))))


# ---------------------------------------------------------------------------
# Printed tables
# ---------------------------------------------------------------------------


def test_a_weighting_is_table_a1_as_printed() -> None:
    """Every A-weighting cell of Table A.1, both band widths, is the print."""
    table = building.SERVICE_EQUIPMENT_WEIGHTING
    for f, a, _ in ref.ISO16032_TABLE_A1_THIRD:
        assert table["third"]["A"][f] == pytest.approx(a, abs=1e-12)
    for f, a, _ in ref.ISO16032_TABLE_A1_OCTAVE:
        assert table["octave"]["A"][f] == pytest.approx(a, abs=1e-12)


def test_octave_c_weighting_is_table_a1_as_printed() -> None:
    for f, _, c in ref.ISO16032_TABLE_A1_OCTAVE:
        assert building.SERVICE_EQUIPMENT_WEIGHTING["octave"]["C"][f] == pytest.approx(
            c, abs=1e-12
        )


def test_third_octave_c_weighting_departs_from_print_only_in_the_defect() -> None:
    """The C cells equal the print, except the ten registered in the errata."""
    table = building.SERVICE_EQUIPMENT_WEIGHTING["third"]["C"]
    differing = {
        f for f, _, c in ref.ISO16032_TABLE_A1_THIRD if abs(table[f] - c) > 1e-9
    }
    assert differing == set(ref.ISO16032_TABLE_A1_C_DEFECT_HZ)


def test_corrected_c_cells_are_iec_61672_1_table_3() -> None:
    iec = {row[0]: (row[1], row[2]) for row in _WEIGHTING_TABLE3}
    for weighting, column in (("A", 0), ("C", 1)):
        for f, value in building.SERVICE_EQUIPMENT_WEIGHTING["third"][
            weighting
        ].items():
            assert value == pytest.approx(iec[f][column], abs=1e-12)


def test_third_octave_c_agrees_with_the_octave_column_the_draft_prints() -> None:
    """The octave column is the internal evidence of the defect."""
    table = building.SERVICE_EQUIPMENT_WEIGHTING
    for f in (2000.0, 4000.0, 8000.0):
        assert table["third"]["C"][f] == table["octave"]["C"][f]


def test_reproducibility_is_table_2_as_printed() -> None:
    for thirds, octaves, sigma in ref.ISO16032_TABLE_2_BANDS:
        for f in thirds:
            assert building.SERVICE_EQUIPMENT_REPRODUCIBILITY["third"][f] == sigma
        for f in octaves:
            assert building.SERVICE_EQUIPMENT_REPRODUCIBILITY["octave"][f] == sigma
    assert len(building.SERVICE_EQUIPMENT_REPRODUCIBILITY["third"]) == THIRD.size
    assert len(building.SERVICE_EQUIPMENT_REPRODUCIBILITY["octave"]) == OCTAVE.size
    assert dict(building.SERVICE_EQUIPMENT_WEIGHTED_REPRODUCIBILITY) == dict(
        ref.ISO16032_TABLE_2_WEIGHTED
    )


def test_published_tables_refuse_writes() -> None:
    tables = (
        building.SERVICE_EQUIPMENT_WEIGHTING,
        building.SERVICE_EQUIPMENT_WEIGHTING["third"],
        building.SERVICE_EQUIPMENT_WEIGHTING["third"]["C"],
        building.SERVICE_EQUIPMENT_REPRODUCIBILITY["octave"],
        building.SERVICE_EQUIPMENT_WEIGHTED_REPRODUCIBILITY,
        building.SERVICE_EQUIPMENT_OPERATING_CONDITIONS,
        building.SERVICE_EQUIPMENT_OPERATING_CONDITIONS["lift"].parameters,
    )
    for table in tables:
        assert isinstance(table, types.MappingProxyType)
    condition = building.SERVICE_EQUIPMENT_OPERATING_CONDITIONS["water_tap"]
    with pytest.raises(dataclasses.FrozenInstanceError, match="clause"):
        condition.clause = "B.3"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Annex B
# ---------------------------------------------------------------------------


def test_operating_conditions_cover_annex_b() -> None:
    conditions = building.SERVICE_EQUIPMENT_OPERATING_CONDITIONS
    clauses = {c.clause for c in conditions.values()}
    assert clauses == {
        "B.2.2",
        "B.2.3",
        "B.2.4",
        "B.2.5",
        "B.2.6",
        "B.3",
        "B.4",
        "B.5",
        "B.6",
        "B.7",
        "B.8",
        "B.9",
        "B.10",
    }
    assert conditions["unknown_source"].clause == "B.10"


def test_rubbish_chute_is_a_maximum_level_only() -> None:
    chute = building.SERVICE_EQUIPMENT_OPERATING_CONDITIONS["rubbish_chute"]
    assert chute.maximum_level
    assert not chute.equivalent_level
    assert chute.equivalent_cycle is None
    assert dict(chute.parameters) == {
        "objects": 2.0,
        "tube_length_m": 0.1,
        "outer_diameter_m": 0.050,
        "wall_thickness_m": 0.003,
        "mass_per_length_kg_m": 0.7,
    }


def test_steady_equipment_integrates_about_30_s() -> None:
    conditions = building.SERVICE_EQUIPMENT_OPERATING_CONDITIONS
    for key in ("water_tap", "mechanical_ventilation", "heating", "cooling"):
        assert conditions[key].nominal_integration_time_s == 30.0
    for key in ("water_closet", "lift", "car_park_door", "filling_emptying"):
        assert conditions[key].nominal_integration_time_s is None
    assert conditions["lift"].parameters["repetitions_min"] == 3.0
    assert conditions["unknown_source"].parameters["period_s"] == 30.0


def test_only_the_temperature_mixers_run_through_the_temperature_range() -> None:
    """B.2.2 gives the temperature sweep and the three settings to three mixers.

    A mixer with independent hot and cold taps is opened hot, then cold, and
    fixed at its loudest position, with neither.
    """
    tap = building.SERVICE_EQUIPMENT_OPERATING_CONDITIONS["water_tap"]
    assert tap.maximum_cycle is not None
    assert tap.equivalent_cycle is not None
    for mixer in ("single-lever", "flow and temperature controls", "thermostatic"):
        assert mixer in tap.maximum_cycle
        assert mixer in tap.equivalent_cycle
    assert "open the hot tap fully, open the cold tap" in tap.maximum_cycle
    assert "both taps of a hot and cold mixer" in tap.equivalent_cycle
    assert dict(tap.parameters) == {"temperature_mixer_settings": 3.0}


def test_operating_condition_freezes_a_dict_of_parameters() -> None:
    condition = building.OperatingCondition(
        clause="B.9",
        equipment="test",
        maximum_level=True,
        equivalent_level=True,
        conditions="normal use",
        maximum_cycle=None,
        equivalent_cycle=None,
        nominal_integration_time_s=None,
        parameters={"x_m": 1.0},
    )
    assert isinstance(condition.parameters, types.MappingProxyType)


# ---------------------------------------------------------------------------
# Background (Clause 9)
# ---------------------------------------------------------------------------


def test_a_4_db_difference_gives_the_printed_2_2_db() -> None:
    difference, printed = ref.ISO16032_BACKGROUND_LIMIT_DB
    res = building.service_equipment_background_correction([50.0], [50.0 - difference])
    assert round(float(res.correction_db[0]), 1) == printed
    assert res.regime == ("corrected",)


def test_below_4_db_the_correction_is_held_at_2_2_db() -> None:
    res = building.service_equipment_background_correction(
        [50.0, 50.0, 50.0], [47.0, 50.0, 55.0]
    )
    np.testing.assert_allclose(res.correction_db, 2.2)
    assert res.regime == ("limited", "limited", "limited")
    assert res.influenced
    np.testing.assert_array_equal(res.limited, [True, True, True])


def test_ten_db_or_more_is_left_uncorrected() -> None:
    res = building.service_equipment_background_correction([50.0, 50.0], [40.0, 30.0])
    np.testing.assert_array_equal(res.correction_db, [0.0, 0.0])
    np.testing.assert_array_equal(res.corrected_db, [50.0, 50.0])
    assert res.regime == ("none", "none")
    assert not res.influenced


@pytest.mark.parametrize(
    ("measured", "background", "regime"),
    [
        (20.4, 10.4, "none"),  # 10,0 dB, 9,999 999 999 999 998 in binary
        (32.3, 28.3, "corrected"),  # 4,0 dB, 3,999 999 999 999 996 in binary
    ],
)
def test_the_clause_9_thresholds_hold_for_decimal_levels(
    measured: float, background: float, regime: str
) -> None:
    res = building.service_equipment_background_correction([measured], [background])
    assert res.regime == (regime,)
    assert not res.influenced
    if regime == "none":
        np.testing.assert_array_equal(res.correction_db, [0.0])
    else:
        assert float(res.correction_db[0]) == pytest.approx(2.2, abs=0.05)


def test_a_4_db_margin_in_decimal_levels_is_not_an_upper_limit() -> None:
    res = building.service_equipment_level(
        _flat(32.3), THIRD, quantity="eq", background_db=np.full(THIRD.size, 28.3)
    )
    assert res.background is not None
    assert set(res.background.regime) == {"corrected"}
    assert not res.upper_limit("A")
    assert not res.upper_limit("C")


def test_formula_8_is_the_energy_subtraction() -> None:
    l1 = np.array([50.0, 50.0, 50.0])
    l2 = np.array([46.0, 43.0, 40.1])
    res = building.service_equipment_background_correction(l1, l2)
    expected = 10.0 * np.log10(10.0 ** (0.1 * l1) - 10.0 ** (0.1 * l2))
    np.testing.assert_allclose(res.corrected_db, expected, atol=1e-12)
    np.testing.assert_allclose(res.difference_db, l1 - l2)


def test_background_correction_refuses_mismatched_bands() -> None:
    with pytest.raises(ValueError, match="background_db"):
        building.service_equipment_background_correction([50.0, 50.0], [40.0])


@pytest.mark.parametrize(
    "centres", [[100.0 + 1j], np.array([100.0 + 1j])], ids=["list", "array"]
)
def test_background_centres_are_refused_when_complex(centres: object) -> None:
    # The centres only label the plot, and a complex one is still refused by
    # name rather than cut to its real part.
    with pytest.raises(ValueError, match="frequencies_hz"):
        building.service_equipment_background_correction(
            [50.0],
            [40.0],
            frequencies_hz=centres,  # type: ignore[arg-type]
        )


def test_background_result_checks_its_own_bands() -> None:
    res = building.service_equipment_background_correction([50.0, 50.0], [40.0, 41.0])
    with pytest.raises(ValueError, match="one value per band"):
        dataclasses.replace(res, regime=("none",))


# ---------------------------------------------------------------------------
# The chain (Clauses 6 and 7)
# ---------------------------------------------------------------------------


def test_average_is_formula_1_rounded_to_one_decimal() -> None:
    readings = np.array([[40.0], [43.0], [46.0]])
    res = building.service_equipment_level(
        np.repeat(readings, THIRD.size, axis=1), THIRD, quantity="eq"
    )
    expected = 10.0 * math.log10((10**4.0 + 10**4.3 + 10**4.6) / 3.0)
    np.testing.assert_allclose(res.average_db, round(expected, 1))
    assert res.reading_count == 3


@pytest.mark.parametrize(
    ("level", "rounded"),
    [
        (40.05, 40.1),
        # Formula (1) returns 40,649 999 999 999 99 for three readings of
        # 40,65 dB: only the cut to nine decimals rounds it up.
        (40.65, 40.7),
    ],
)
def test_a_half_tenth_rounds_up(level: float, rounded: float) -> None:
    res = building.service_equipment_level(_flat(level), THIRD, quantity="eq")
    np.testing.assert_array_equal(res.average_db, np.full(THIRD.size, rounded))


def test_a_half_decibel_single_number_rounds_up() -> None:
    """A lone 1 000 Hz band at 44,5 dB sums to exactly 44,5 dB; 7.8 gives 45."""
    levels = np.full(THIRD.size, -200.0)
    levels[THIRD == 1000.0] = 44.5
    res = building.service_equipment_level(
        np.tile(levels, (3, 1)), THIRD, quantity="eq"
    )
    assert res.unrounded_ratings["LA,eq"] == pytest.approx(44.5, abs=1e-12)
    assert res.ratings["LA,eq"] == 45


def test_flat_spectrum_a_and_c_weighted_values() -> None:
    res = building.service_equipment_level(_flat(40.0), THIRD, quantity="Fmax")
    table = building.SERVICE_EQUIPMENT_WEIGHTING["third"]
    a = [40.0 + table["A"][f] for f in RESTRICTED]
    c = [40.0 + table["C"][f] for f in THIRD]
    assert res.unrounded_ratings["LA,Fmax"] == pytest.approx(_energy_sum(a), abs=1e-9)
    assert res.unrounded_ratings["LC,Fmax"] == pytest.approx(_energy_sum(c), abs=1e-9)
    # 51,000 4 dB and 53,550 7 dB, rounded to whole decibels by 7.8.
    assert res.ratings["LA,Fmax"] == 51
    assert res.ratings["LC,Fmax"] == 54
    assert set(res.ratings) == {"LA,Fmax", "LC,Fmax"}


def test_each_single_number_carries_its_table_2_deviation() -> None:
    res = building.service_equipment_level(
        _flat(40.0), THIRD, quantity="Smax", reverberation_time_s=np.full(27, 0.7)
    )
    assert dict(res.weighted_reproducibility_db) == {
        "LA,Smax": 0.8,
        "LA,Smax,nT": 0.8,
        "LC,Smax": 1.2,
        "LC,Smax,nT": 1.2,
    }
    assert isinstance(res.weighted_reproducibility_db, types.MappingProxyType)


def test_extended_a_range_adds_the_outer_bands() -> None:
    restricted = building.service_equipment_level(_flat(40.0), THIRD, quantity="eq")
    extended = building.service_equipment_level(
        _flat(40.0), THIRD, quantity="eq", a_weighting_range="extended"
    )
    assert extended.unrounded_ratings["LA,eq"] > restricted.unrounded_ratings["LA,eq"]


def test_restricted_bands_give_no_c_weighted_value() -> None:
    res = building.service_equipment_level(
        _flat(40.0, RESTRICTED), RESTRICTED, quantity="eq"
    )
    assert set(res.ratings) == {"LA,eq"}


def test_a_weighting_range_must_be_covered() -> None:
    freqs = RESTRICTED[1:]
    levels = _flat(40.0, freqs)
    with pytest.raises(ValueError, match="A-weighting range"):
        building.service_equipment_level(levels, freqs, quantity="eq")


def test_reverberation_time_equal_to_t0_leaves_the_levels() -> None:
    res = building.service_equipment_level(
        _flat(40.0),
        THIRD,
        quantity="Smax",
        reverberation_time_s=np.full(THIRD.size, 0.5),
    )
    assert res.standardized_db is not None
    np.testing.assert_allclose(res.standardized_db, res.corrected_db, atol=1e-12)
    assert res.ratings["LA,Smax,nT"] == res.ratings["LA,Smax"]


def test_formula_5_in_the_standardization_range_only() -> None:
    t = np.full(THIRD.size, 1.0)
    t[~((THIRD >= 50.0) & (THIRD <= 5000.0))] = np.nan
    res = building.service_equipment_level(
        _flat(40.0), THIRD, quantity="eq", reverberation_time_s=t
    )
    assert res.standardized_db is not None
    inside = res.standardizable
    np.testing.assert_allclose(
        res.standardized_db[inside], 40.0 - 10.0 * math.log10(2.0), atol=1e-12
    )
    np.testing.assert_allclose(res.standardized_db[~inside], 40.0, atol=1e-12)
    assert res.unstandardized_bands_hz == (25.0, 31.5, 40.0, 6300.0, 8000.0, 10000.0)


def test_formula_6_at_the_reference_absorption_leaves_the_levels() -> None:
    t = 0.8
    volume = 10.0 * t / 0.16
    res = building.service_equipment_level(
        _flat(40.0),
        THIRD,
        quantity="eq",
        reverberation_time_s=np.full(THIRD.size, t),
        volume_m3=volume,
    )
    assert res.normalized_db is not None
    np.testing.assert_allclose(res.normalized_db, res.corrected_db, atol=1e-12)
    assert {"LA,eq,n", "LC,eq,n", "LA,eq,nT", "LC,eq,nT"} <= set(res.ratings)


def test_formula_6_raises_a_room_more_absorbing_than_a0() -> None:
    """T = 0,5 s in 50 m³ is A = 16 m²: 10 lg 1,6 = 2,04 dB is added."""
    res = building.service_equipment_level(
        _flat(40.0),
        THIRD,
        quantity="eq",
        reverberation_time_s=np.full(THIRD.size, 0.5),
        volume_m3=50.0,
    )
    assert res.normalized_db is not None
    inside = res.standardizable
    np.testing.assert_allclose(
        res.normalized_db[inside], 40.0 + 10.0 * math.log10(1.6), atol=1e-12
    )
    np.testing.assert_allclose(res.normalized_db[~inside], 40.0, atol=1e-12)
    assert float(res.normalized_db[16]) == pytest.approx(42.0412, abs=5e-5)


def test_reference_reverberation_time_can_be_specified() -> None:
    res = building.service_equipment_level(
        _flat(40.0),
        THIRD,
        quantity="eq",
        reverberation_time_s=np.full(THIRD.size, 0.8),
        reference_reverberation_time_s=0.8,
    )
    assert res.standardized_db is not None
    np.testing.assert_allclose(res.standardized_db, 40.0, atol=1e-12)


def test_background_rows_are_energy_averaged() -> None:
    background = np.vstack((np.full(THIRD.size, 30.0), np.full(THIRD.size, 33.0)))
    res = building.service_equipment_level(
        _flat(40.0), THIRD, quantity="eq", background_db=background
    )
    assert res.background is not None
    expected = 10.0 * math.log10((10**3.0 + 10**3.3) / 2.0)
    np.testing.assert_allclose(res.background.background_db, expected)


def test_limited_band_makes_the_weighted_value_an_upper_limit() -> None:
    background = np.full(THIRD.size, 20.0)
    background[-1] = 39.0  # 10 000 Hz: in the C range, outside the restricted A range
    res = building.service_equipment_level(
        _flat(40.0), THIRD, quantity="eq", background_db=background
    )
    assert res.upper_limit("C")
    assert not res.upper_limit("A")
    background[10] = 39.0  # 250 Hz: in both
    res = building.service_equipment_level(
        _flat(40.0), THIRD, quantity="eq", background_db=background
    )
    assert res.upper_limit("A")


def test_upper_limit_names_a_weighting() -> None:
    res = building.service_equipment_level(_flat(40.0), THIRD, quantity="eq")
    assert not res.upper_limit("A")
    with pytest.raises(ValueError, match="weighting"):
        res.upper_limit("Z")


def test_octave_bands() -> None:
    res = building.service_equipment_level(
        _flat(40.0, OCTAVE), OCTAVE, quantity="eq", band="octave"
    )
    table = building.SERVICE_EQUIPMENT_WEIGHTING["octave"]
    a = [40.0 + table["A"][f] for f in OCTAVE if 63.0 <= f <= 4000.0]
    assert res.unrounded_ratings["LA,eq"] == pytest.approx(_energy_sum(a), abs=1e-9)
    assert "LC,eq" in res.ratings
    np.testing.assert_array_equal(
        res.reproducibility_db, [1.9, 1.9, 1.9, 1.5, 1.2, 1, 1, 1, 1]
    )


def test_octave_standardization_leaves_out_31_5_and_8000_hz() -> None:
    t = np.full(OCTAVE.size, 1.0)
    t[[0, -1]] = np.nan
    res = building.service_equipment_level(
        _flat(40.0, OCTAVE),
        OCTAVE,
        quantity="eq",
        band="octave",
        reverberation_time_s=t,
    )
    assert res.standardized_db is not None
    expected = np.full(OCTAVE.size, 40.0 - 10.0 * math.log10(2.0))
    expected[[0, -1]] = 40.0
    np.testing.assert_allclose(res.standardized_db, expected, atol=1e-12)
    assert res.unstandardized_bands_hz == (31.5, 8000.0)


def test_exact_centres_are_matched_to_nominal_bands() -> None:
    exact = 1000.0 * 10.0 ** (np.arange(-16, 11) / 10.0)
    res = building.service_equipment_level(_flat(40.0), exact, quantity="eq")
    np.testing.assert_array_equal(res.frequencies_hz, THIRD)


def test_a_single_reading_is_one_row() -> None:
    res = building.service_equipment_level(
        np.full(THIRD.size, 40.0), THIRD, quantity="eq"
    )
    assert res.readings_db.shape == (1, THIRD.size)


def test_volume_needs_a_reverberation_time() -> None:
    levels = _flat(40.0)
    with pytest.raises(ValueError, match="reverberation_time_s"):
        building.service_equipment_level(levels, THIRD, quantity="eq", volume_m3=50.0)


def test_reverberation_time_must_be_positive_in_the_range() -> None:
    t = np.full(THIRD.size, 0.5)
    t[10] = 0.0
    levels = _flat(40.0)
    with pytest.raises(ValueError, match="reverberation_time_s"):
        building.service_equipment_level(
            levels, THIRD, quantity="eq", reverberation_time_s=t
        )


@pytest.mark.parametrize(
    ("kwargs", "fragment"),
    [
        ({"quantity": "Imax"}, "quantity"),
        ({"quantity": "eq", "band": "sixth"}, "band"),
        ({"quantity": "eq", "a_weighting_range": "wide"}, "a_weighting_range"),
    ],
)
def test_choices_are_checked(kwargs: dict[str, str], fragment: str) -> None:
    levels = _flat(40.0)
    with pytest.raises(ValueError, match=fragment):
        building.service_equipment_level(levels, THIRD, **kwargs)  # type: ignore[arg-type]


def _level_inputs() -> dict[str, object]:
    return {
        "levels_db": _flat(40.0),
        "frequencies_hz": THIRD,
        "background_db": np.full(THIRD.size, 20.0),
        "reverberation_time_s": np.full(THIRD.size, 0.5),
        "volume_m3": 50.0,
    }


def _level_call(**overrides: object) -> building.ServiceEquipmentResult:
    kwargs = {**_level_inputs(), "quantity": "eq", **overrides}
    return building.service_equipment_level(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "name",
    ["levels_db", "frequencies_hz", "background_db", "reverberation_time_s"],
)
def test_a_complex_array_is_refused_not_cut_to_its_real_part(name: str) -> None:
    # np.asarray(z, dtype=float) keeps the real part with only a warning: a
    # spectrum of 40 + 1j dB would be rated as one of 40 dB.
    complex_value = np.asarray(_level_inputs()[name]) + 1j
    with pytest.raises(ValueError, match=name):
        _level_call(**{name: complex_value})


def test_levels_that_are_not_numbers_are_refused_by_name() -> None:
    with pytest.raises(ValueError, match="levels_db"):
        _level_call(levels_db=[["forty"] * THIRD.size] * 3)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("volume_m3", "50"),
        ("volume_m3", True),
        ("volume_m3", np.array([50.0])),
        ("volume_m3", 50.0 + 0j),
        ("volume_m3", np.array(1, dtype=bool)),
        ("volume_m3", np.array("50")),
        ("volume_m3", np.array(np.True_, dtype=object)),
        ("volume_m3", np.array("50", dtype=object)),
        ("volume_m3", [[50.0], [50.0, 50.0]]),
        ("reference_reverberation_time_s", "0.5"),
        ("reference_reverberation_time_s", np.array([0.5, 0.5])),
        ("reference_reverberation_time_s", np.array(1, dtype=bool)),
    ],
)
def test_the_volume_and_t0_are_one_positive_number(name: str, value: object) -> None:
    with pytest.raises(ValueError, match=name):
        _level_call(**{name: value})


@pytest.mark.parametrize("value", ["x", 1 + 1j, -1.0, 0.0, None])
def test_t0_is_refused_by_name_without_a_reverberation_time(value: object) -> None:
    # Formula (5) is never reached without a reverberation time; the T0 the
    # call names is still one positive number or a refusal.
    with pytest.raises(ValueError, match="reference_reverberation_time_s"):
        _level_call(
            reverberation_time_s=None,
            volume_m3=None,
            reference_reverberation_time_s=value,
        )


def test_a_volume_given_as_a_numpy_scalar_is_one_number() -> None:
    plain = _level_call(volume_m3=50.0)
    # A number held in an object array is still a number.
    for value in (np.float32(50.0), np.array(50.0), 50, np.array(50, dtype=object)):
        assert _level_call(volume_m3=value).ratings == plain.ratings


def test_a_centre_off_the_nominal_bands_is_refused() -> None:
    freqs = THIRD.copy()
    freqs[5] = 90.0
    levels = _flat(40.0)
    with pytest.raises(ValueError, match="nominal"):
        building.service_equipment_level(levels, freqs, quantity="eq")


def test_bands_must_increase() -> None:
    freqs = THIRD[::-1]
    levels = _flat(40.0)
    with pytest.raises(ValueError, match="increasing"):
        building.service_equipment_level(levels, freqs, quantity="eq")


def test_result_checks_its_band_arrays() -> None:
    res = building.service_equipment_level(_flat(40.0), THIRD, quantity="eq")
    short = res.average_db[:-1]
    with pytest.raises(ValueError, match="one value per band"):
        dataclasses.replace(res, average_db=short)


# ---------------------------------------------------------------------------
# Positions (7.2, 7.3, 7.4.1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("levels", "action", "following"),
    [
        ([35.1, 32.1, 34.0], "proceed", ()),  # 3,0 dB, inclusive
        ([35.2, 32.1, 34.0], "add_positions", (4, 5)),
        ([35.0, 32.1, 36.0, 35.2, 33.0, 37.9], "proceed", ()),  # 5,8 dB
        ([38.1, 32.1, 35.0, 37.0, 34.0, 36.0], "add_positions", (6, 7)),  # 6,0 dB
        ([35.0, 32.0, 36.0, 35.0, 34.0, 36.0, 35.0, 40.9, 33.0], "proceed", ()),
        ([35.0, 32.0, 36.0, 35.0, 34.0, 36.0, 35.0, 41.0, 33.0], "interrupt", ()),
        # Readings only widen the spread: from 9,0 dB no later stage passes.
        ([30.0, 33.0, 38.9], "add_positions", (4, 5)),
        ([30.0, 33.0, 39.0], "interrupt", ()),
        ([30.0, 33.0, 40.0], "interrupt", ()),
        ([30.0, 33.0, 34.0, 31.0, 32.0, 38.9], "add_positions", (6, 7)),
        ([30.0, 33.0, 34.0, 31.0, 32.0, 40.0], "interrupt", ()),
    ],
)
def test_the_ladder_of_7_4_1(
    levels: list[float], action: str, following: tuple[int, ...]
) -> None:
    check = building.check_position_spread(levels)
    assert check.action == action
    assert check.next_positions == following
    assert check.passes is (action == "proceed")


def test_the_corner_readings_give_the_standard_deviation() -> None:
    check = building.check_position_spread([35.0, 32.1, 36.0, 36.0, 33.0, 37.9])
    assert check.corner_standard_deviation_db == pytest.approx(
        np.std([35.0, 36.0], ddof=1)
    )
    single = building.check_position_spread([35.0, 34.0, 36.0])
    assert single.corner_standard_deviation_db is None


def test_spread_check_has_no_truth_value() -> None:
    check = building.check_position_spread([35.0, 34.0, 36.0])
    with pytest.raises(TypeError, match="passes"):
        bool(check)


def test_spread_check_needs_whole_stages() -> None:
    with pytest.raises(ValueError, match="3, 6 or 9"):
        building.check_position_spread([35.0, 34.0, 36.0, 35.0])


def _positions(**kwargs: object) -> building.ServiceEquipmentPositionCheck:
    base: dict[str, object] = {
        "room_dimensions_m": (5.0, 4.0, 2.6),
        "corner_position_m": (0.5, 0.5, 0.5),
        "room_positions_m": [(2.5, 2.0, 1.2), (4.0, 3.2, 1.5)],
        "source_positions_m": [(4.9, 0.2, 2.4)],
    }
    base.update(kwargs)
    return building.check_service_equipment_positions(**base)  # type: ignore[arg-type]


def test_positions_that_keep_every_distance() -> None:
    check = _positions()
    assert check.passes
    assert check.preferred_separation
    assert check.corner_wall_distances_m == (0.5, 0.5)
    assert check.source_distance_m == pytest.approx(
        math.dist((2.5, 2.0, 1.2), (4.9, 0.2, 2.4))
    )


def test_positions_closer_than_1_m_fail() -> None:
    check = _positions(room_positions_m=[(2.5, 2.0, 1.2), (3.0, 2.5, 1.2)])
    assert check.separation_m == pytest.approx(math.sqrt(0.5))
    assert not check.separation_ok
    assert not check.passes


def test_between_1_and_1_5_m_passes_but_is_not_preferred() -> None:
    check = _positions(room_positions_m=[(2.5, 2.0, 1.2), (3.7, 2.0, 1.2)])
    assert check.separation_ok
    assert not check.preferred_separation


def test_small_room_surface_distance() -> None:
    near = [(2.5, 2.0, 1.2), (4.6, 3.2, 1.5)]  # 0,40 m from the wall at x = 5 m
    assert not _positions(room_positions_m=near).surface_ok
    assert _positions(room_positions_m=near, small_room=True).surface_ok


def test_height_and_source_distance() -> None:
    assert not _positions(room_positions_m=[(2.5, 2.0, 2.1), (4.0, 3.2, 1.5)]).height_ok
    near_source = _positions(source_positions_m=[(3.5, 2.0, 1.2)])
    assert not near_source.source_ok
    assert _positions(source_positions_m=None).source_distance_m is None


def test_room_positions_at_least_0_5_m_high() -> None:
    assert _positions(room_positions_m=[(2.5, 2.0, 0.5), (4.0, 3.2, 1.5)]).height_ok
    low = _positions(room_positions_m=[(2.5, 2.0, 0.4), (4.0, 3.2, 1.5)])
    assert not low.height_ok
    assert not low.passes


def test_corner_height_from_0_5_m_to_1_5_m() -> None:
    assert _positions(corner_position_m=(0.5, 0.5, 1.5)).corner_height_ok
    assert not _positions(corner_position_m=(0.5, 0.5, 1.6)).corner_height_ok
    assert not _positions(corner_position_m=(0.5, 0.5, 0.4)).corner_height_ok


#: Each limit of 7.3, and the corner height of 7.2, met exactly and missed by
#: 0,01 m, in the 5 m by 4 m by 2,6 m room of :func:`_positions` (2,4 m high
#: for the ceiling). The separation is taken from the corner as well as
#: between the room positions, and the surface distance from the ceiling as
#: well as from the walls. Where decimal coordinates put the
#: limit a hair under itself in binary (4,0 - 3,7 = 0,299 999 999 999 999 8,
#: 2,3 - 1,3 = 0,999 999 999 999 999 8), the passing case uses them.
_LIMIT_CASES = [
    pytest.param(
        "surface_ok",
        {"room_positions_m": [(2.5, 2.0, 1.2), (4.5, 3.2, 1.5)]},
        True,
        id="0.50 m from a wall",
    ),
    pytest.param(
        "surface_ok",
        {"room_positions_m": [(2.5, 2.0, 1.2), (4.51, 3.2, 1.5)]},
        False,
        id="0.49 m from a wall",
    ),
    pytest.param(
        "surface_ok",
        {"room_positions_m": [(2.5, 2.0, 1.2), (4.0, 3.7, 1.5)], "small_room": True},
        True,
        id="0.30 m in a small room",
    ),
    pytest.param(
        "surface_ok",
        {"room_positions_m": [(2.5, 2.0, 1.2), (4.0, 3.71, 1.5)], "small_room": True},
        False,
        id="0.29 m in a small room",
    ),
    pytest.param(
        "surface_ok",
        {
            "room_dimensions_m": (5.0, 4.0, 2.4),
            "room_positions_m": [(2.5, 2.0, 1.2), (4.0, 3.2, 1.9)],
        },
        True,
        id="0.50 m from the ceiling",
    ),
    pytest.param(
        "surface_ok",
        {
            "room_dimensions_m": (5.0, 4.0, 2.4),
            "room_positions_m": [(2.5, 2.0, 1.2), (4.0, 3.2, 1.91)],
        },
        False,
        id="0.49 m from the ceiling",
    ),
    pytest.param(
        "separation_ok",
        {"room_positions_m": [(1.3, 2.0, 1.2), (2.3, 2.0, 1.2)]},
        True,
        id="1.00 m apart",
    ),
    pytest.param(
        "separation_ok",
        {"room_positions_m": [(1.3, 2.0, 1.2), (2.29, 2.0, 1.2)]},
        False,
        id="0.99 m apart",
    ),
    pytest.param(
        "separation_ok",
        {"room_positions_m": [(1.5, 0.5, 0.5), (4.0, 3.2, 1.5)]},
        True,
        id="room position 1.00 m from the corner",
    ),
    pytest.param(
        "separation_ok",
        {"room_positions_m": [(1.49, 0.5, 0.5), (4.0, 3.2, 1.5)]},
        False,
        id="room position 0.99 m from the corner",
    ),
    pytest.param(
        "preferred_separation",
        {"room_positions_m": [(1.3, 2.0, 1.2), (2.8, 2.0, 1.2)]},
        True,
        id="1.50 m apart, preferred",
    ),
    pytest.param(
        "preferred_separation",
        {"room_positions_m": [(1.3, 2.0, 1.2), (2.79, 2.0, 1.2)]},
        False,
        id="1.49 m apart, not preferred",
    ),
    pytest.param(
        "source_ok",
        {
            "room_positions_m": [(2.5, 2.3, 1.2), (4.0, 3.2, 1.5)],
            "source_positions_m": [(2.5, 0.8, 1.2)],
        },
        True,
        id="1.50 m from a source",
    ),
    pytest.param(
        "source_ok",
        {
            "room_positions_m": [(2.5, 2.3, 1.2), (4.0, 3.2, 1.5)],
            "source_positions_m": [(2.5, 0.81, 1.2)],
        },
        False,
        id="1.49 m from a source",
    ),
    pytest.param(
        "height_ok",
        {"room_positions_m": [(2.5, 2.0, 0.5), (4.0, 3.2, 1.5)]},
        True,
        id="room position 0.50 m high",
    ),
    pytest.param(
        "height_ok",
        {"room_positions_m": [(2.5, 2.0, 0.49), (4.0, 3.2, 1.5)]},
        False,
        id="room position 0.49 m high",
    ),
    pytest.param(
        "height_ok",
        {"room_positions_m": [(2.5, 2.0, 2.0), (4.0, 3.2, 1.5)]},
        True,
        id="room position 2.00 m high",
    ),
    pytest.param(
        "height_ok",
        {"room_positions_m": [(2.5, 2.0, 2.01), (4.0, 3.2, 1.5)]},
        False,
        id="room position 2.01 m high",
    ),
    pytest.param(
        "corner_height_ok",
        {"corner_position_m": (0.5, 0.5, 0.5)},
        True,
        id="corner 0.50 m high",
    ),
    pytest.param(
        "corner_height_ok",
        {"corner_position_m": (0.5, 0.5, 0.49)},
        False,
        id="corner 0.49 m high",
    ),
    pytest.param(
        "corner_height_ok",
        {"corner_position_m": (0.5, 0.5, 1.5)},
        True,
        id="corner 1.50 m high",
    ),
    pytest.param(
        "corner_height_ok",
        {"corner_position_m": (0.5, 0.5, 1.51)},
        False,
        id="corner 1.51 m high",
    ),
]


@pytest.mark.parametrize(("verdict", "kwargs", "expected"), _LIMIT_CASES)
def test_each_limit_of_7_2_and_7_3_at_its_boundary(
    verdict: str, kwargs: dict[str, object], *, expected: bool
) -> None:
    assert getattr(_positions(**kwargs), verdict) is expected


def test_the_corner_0_5_m_from_its_walls_is_preferred_not_required() -> None:
    """7.2 words the corner location as a preference; only its height is judged."""
    assert _positions().preferred_corner_wall_distance
    # Raised for furniture, the corner keeps its 0,5 m from the walls.
    assert _positions(corner_position_m=(0.5, 0.5, 1.0)).preferred_corner_wall_distance
    # The far corner of the room: 5,0 - 4,5 and 4,0 - 3,5.
    far = _positions(
        corner_position_m=(4.5, 3.5, 0.5),
        room_positions_m=[(1.5, 1.5, 1.2), (2.8, 2.5, 1.5)],
    )
    assert far.corner_wall_distances_m == pytest.approx((0.5, 0.5))
    assert far.preferred_corner_wall_distance
    for corner in (
        (1.5, 1.2, 0.5),
        (0.0, 0.0, 0.5),
        (0.5, 0.49, 0.5),
        (0.51, 0.5, 0.5),
    ):
        check = _positions(corner_position_m=corner)
        assert not check.preferred_corner_wall_distance
        assert check.passes


def test_a_position_outside_the_room_is_refused() -> None:
    with pytest.raises(ValueError, match="outside the room"):
        _positions(room_positions_m=[(5.5, 2.0, 1.2)])


def test_position_check_has_no_truth_value() -> None:
    check = _positions()
    with pytest.raises(TypeError, match="passes"):
        bool(check)


def test_loudest_corner() -> None:
    assert building.loudest_corner([60.0, 63.0, 62.0, 61.0]) == 1
    assert building.loudest_corner([60.0, 63.0, 62.0, 61.0], excluded=[1]) == 2
    assert building.loudest_corner([62.0, 60.0, 62.0]) == 0


def test_loudest_corner_needs_a_corner_left() -> None:
    with pytest.raises(ValueError, match="excluded"):
        building.loudest_corner([60.0, 61.0], excluded=[0, 1])
    with pytest.raises(ValueError, match="out of range"):
        building.loudest_corner([60.0, 61.0], excluded=[2])


@pytest.mark.parametrize(
    "excluded",
    [[1.7], [True], ["1"], [-1], 1, "1", [[1]]],
    ids=["1.7", "True", "'1'", "-1", "bare 1", "bare '1'", "nested"],
)
def test_an_excluded_corner_is_named_by_a_whole_index(excluded: object) -> None:
    # int() would read 1.7, True and '1' each as corner 1 and leave it out.
    with pytest.raises(ValueError, match="excluded"):
        building.loudest_corner([50.0, 52.0, 51.0, 49.0], excluded=excluded)  # type: ignore[arg-type]


def test_excluded_corners_as_numpy_indices() -> None:
    levels = [50.0, 52.0, 51.0, 49.0]
    assert building.loudest_corner(levels, excluded=np.array([1])) == 2  # type: ignore[arg-type]
    assert building.loudest_corner(levels, excluded=[np.int64(1), 2.0]) == 0  # type: ignore[list-item]


@pytest.mark.parametrize(
    ("kwargs", "name"),
    [
        ({"room_dimensions_m": np.array([5.0 + 1j, 4.0, 2.6])}, "room_dimensions_m"),
        ({"corner_position_m": np.array([0.5 + 1j, 0.5, 0.5])}, "corner_position_m"),
        ({"room_positions_m": [("2.5", "2.0", "x")]}, "room_positions_m"),
        ({"small_room": "no"}, "small_room"),
        ({"small_room": 0.3}, "small_room"),
    ],
)
def test_position_inputs_are_refused_by_name(
    kwargs: dict[str, object], name: str
) -> None:
    with pytest.raises(ValueError, match=name):
        _positions(**kwargs)


@pytest.mark.parametrize(
    "empty", [[], (), np.empty((0, 3))], ids=["[]", "()", "(0, 3)"]
)
def test_no_source_given_as_an_empty_list_or_array(empty: object) -> None:
    check = _positions(source_positions_m=empty)
    assert check.source_distance_m is None
    assert check.source_positions_m.shape == (0, 3)


@pytest.mark.parametrize(
    "empty", [[], (), np.empty((0, 3))], ids=["[]", "()", "(0, 3)"]
)
def test_no_room_position_is_refused_as_such(empty: object) -> None:
    with pytest.raises(ValueError, match="at least one reverberant-field position"):
        _positions(room_positions_m=empty)


def test_an_empty_corner_is_refused_as_one_position() -> None:
    with pytest.raises(
        ValueError, match=r"'corner_position_m' must be one \(x, y, z\)"
    ):
        _positions(corner_position_m=[])


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ((0.0, 1.7, 2.1), (1.0, 1.7, 1.5)),  # wall at x = 0
        ((5.0, 1.7, 2.1), (4.0, 1.7, 1.5)),  # wall at x = 5 m
        ((2.0, 0.05, 2.1), (2.0, 1.05, 1.5)),  # 5 cm off the wall at y = 0
        ((2.0, 4.0, 0.3), (2.0, 3.0, 1.5)),  # low on the wall at y = 4 m
    ],
)
def test_a_wall_source_gets_a_position_1_m_in_front_at_1_5_m(
    source: tuple[float, float, float], expected: tuple[float, float, float]
) -> None:
    position = building.additional_microphone_position(
        (5.0, 4.0, 2.6), source, mounting="wall"
    )
    np.testing.assert_allclose(position, expected, rtol=0.0, atol=1e-12)


def test_a_ceiling_source_gets_a_position_1_5_m_above_the_floor_below_it() -> None:
    position = building.additional_microphone_position(
        (5.0, 4.0, 2.6), (0.6, 3.0, 2.6), mounting="ceiling"
    )
    np.testing.assert_allclose(position, (0.6, 3.0, 1.5), rtol=0.0, atol=1e-12)


def test_the_additional_position_must_fit_in_the_room() -> None:
    low_room = (5.0, 4.0, 1.4)
    with pytest.raises(ValueError, match="falls outside the room"):
        building.additional_microphone_position(
            low_room, (2.0, 2.0, 1.4), mounting="ceiling"
        )


def test_the_additional_position_needs_a_source_in_the_room() -> None:
    with pytest.raises(ValueError, match="source_position_m"):
        building.additional_microphone_position(
            (5.0, 4.0, 2.6), (5.5, 2.0, 2.0), mounting="wall"
        )


def test_the_additional_position_names_the_mounting() -> None:
    with pytest.raises(ValueError, match="mounting"):
        building.additional_microphone_position(
            (5.0, 4.0, 2.6),
            (2.0, 2.0, 2.6),
            mounting="floor",  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Figures say what the method did
# ---------------------------------------------------------------------------


def _legend_texts(ax: Axes) -> list[str]:
    legend = ax.get_legend()
    assert legend is not None
    return [t.get_text() for t in legend.get_texts()]


def _chain() -> building.ServiceEquipmentResult:
    background = np.full(THIRD.size, 30.0)
    background[[2, 12]] = 38.5
    t = np.full(THIRD.size, 0.7)
    return building.service_equipment_level(
        _flat(40.0),
        THIRD,
        quantity="eq",
        background_db=background,
        reverberation_time_s=t,
    )


def test_level_figure_marks_limited_and_unstandardized_bands() -> None:
    fig, ax = plt.subplots()
    res = _chain()
    res.plot(ax=ax)
    labels = _legend_texts(ax)
    assert "upper limit (background)" in labels
    assert "not standardized (7.7)" in labels
    marks = next(
        line
        for line in ax.get_lines()
        if line.get_label() == "upper limit (background)"
    )
    assert np.asarray(marks.get_xdata()).size == 2
    assert "$L_\\mathrm{A,eq,nT}$" in ax.get_title()
    assert len(ax.patches) == 6
    plt.close(fig)


def test_level_figure_in_spanish() -> None:
    fig, ax = plt.subplots()
    _chain().plot(ax=ax, language="es")
    labels = _legend_texts(ax)
    assert "límite superior (ruido de fondo)" in labels
    assert ax.get_title().startswith("Nivel de los equipamientos")
    plt.close(fig)


def test_background_figure_without_centres_labels_the_band_index_in_spanish() -> None:
    fig, ax = plt.subplots()
    res = building.service_equipment_background_correction(
        [40.0, 40.0, 40.0], [28.0, 34.0, 38.0]
    )
    res.plot(ax=ax, language="es")
    assert ax.get_xlabel() == "Índice de banda"
    plt.close(fig)


def test_background_figure() -> None:
    fig, ax = plt.subplots()
    res = building.service_equipment_background_correction(
        [50.0, 50.0, 50.0], [35.0, 45.0, 48.0], frequencies_hz=[125.0, 250.0, 500.0]
    )
    res.plot(ax=ax)
    labels = _legend_texts(ax)
    assert labels[:3] == [
        "measured $L_1$",
        "background $L_2$",
        "corrected for background",
    ]
    assert "upper limit (background)" in labels
    plt.close(fig)


def test_spread_figure_names_the_next_positions() -> None:
    fig, ax = plt.subplots()
    building.check_position_spread([35.0, 31.0, 34.0]).plot(ax=ax, language="es")
    assert "añadir posiciones 4 y 5" in ax.get_title()
    assert [t.get_text() for t in ax.get_xticklabels()] == ["1", "2", "3"]
    plt.close(fig)


def test_position_figure_draws_the_room() -> None:
    fig, ax = plt.subplots()
    _positions().plot(ax=ax)
    labels = _legend_texts(ax)
    for label in ("room outline", "corner position", "sound source"):
        assert label in labels
    assert ax.get_title().endswith("requirements met")
    plt.close(fig)


def test_position_figure_numbers_the_corner_position_1() -> None:
    fig, ax = plt.subplots()
    _positions().plot(ax=ax)
    numbers = {
        t.get_text(): t.xy
        for t in ax.texts
        if isinstance(t, Annotation) and t.get_text().isdigit()
    }
    assert numbers == {"1": (0.5, 0.5), "2": (2.5, 2.0), "3": (4.0, 3.2)}
    plt.close(fig)


@pytest.mark.parametrize("dpi", [72, 100, 150])
@pytest.mark.parametrize(
    "room",
    [(5.0, 4.0, 2.6), (12.0, 4.0, 2.6), (5.0, 12.0, 2.6)],
    ids=["room", "corridor", "deep room"],
)
@pytest.mark.parametrize("language", ["en", "es"])
def test_position_figure_of_its_own_keeps_key_and_title_on_the_canvas(
    language: str, room: tuple[float, float, float], dpi: int
) -> None:
    with mpl.rc_context({"figure.dpi": dpi}):
        ax = _positions(
            room_dimensions_m=room,
            room_positions_m=[(2.5, 2.0, 1.2), (3.0, 2.5, 1.2)],
        ).plot(language=language)
        fig = ax.get_figure(root=True)
        assert fig is not None
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()  # type: ignore[attr-defined]
        canvas = fig.bbox
        legend = ax.get_legend()
        assert legend is not None
        for artist in (legend, ax.title, ax.xaxis.label, ax.yaxis.label):
            box = artist.get_window_extent(renderer)
            assert canvas.x0 <= box.x0
            assert box.x1 <= canvas.x1
            assert canvas.y0 <= box.y0
            assert box.y1 <= canvas.y1
        plt.close(fig)
