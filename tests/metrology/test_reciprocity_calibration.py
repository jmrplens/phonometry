#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The sensitivities of a reciprocity calibration and its uncertainty budget
(IEC 61094-2:2009 5.7 and 7, IEC 61094-3:2016 5.7 and 7).

The components of Table 1 of both parts are checked against the printed
tables in ``tests/reference_data``; the triad and the budget against their
definitions.
"""

from __future__ import annotations

import numpy as np
import pytest
import reference_data as ref

from phonometry import metrology
from phonometry.metrology import reciprocity_calibration as rcal

_F = np.array([250.0, 1000.0, 4000.0])


@pytest.mark.parametrize(
    ("table", "printed"),
    [
        (metrology.IEC61094_2_TABLE_1, ref.IEC61094_2_TABLE_1_TEXT),
        (metrology.IEC61094_3_TABLE_1, ref.IEC61094_3_TABLE_1_TEXT),
    ],
    ids=["iec61094-2", "iec61094-3"],
)
def test_table_1_rows_are_the_printed_ones(
    table: dict[str, metrology.ReciprocityUncertaintyRow],
    printed: tuple[tuple[str, tuple[str, ...]], ...],
) -> None:
    assert [(row.component, row.subclauses) for row in table.values()] == list(printed)


def test_the_triad_solves_any_three_products() -> None:
    """Three smooth complex responses, as a calibration's are over frequency."""
    frequencies = np.linspace(0.0, 1.0, 9)
    true = np.array(
        [
            (0.05 + 0.01 * frequencies) * np.exp(-2.0j * frequencies + 0.3j),
            (0.04 - 0.01 * frequencies) * np.exp(-1.5j * frequencies - 2.0j),
            0.06 * np.exp(-3.0j * frequencies + 1.0j),
        ]
    )
    products = [true[0] * true[1], true[1] * true[2], true[2] * true[0]]
    solved = rcal._triad(products)
    sign = np.sign((solved[0, 0] / true[0, 0]).real)
    np.testing.assert_allclose(solved, sign * true, rtol=1e-12)
    np.testing.assert_allclose(solved[0] * solved[1], products[0], rtol=1e-12)


def test_the_root_is_continuous_and_starts_with_a_positive_real_part() -> None:
    phase = np.linspace(0.0, 6.0 * np.pi, 40)
    root = rcal._continuous_root(np.exp(1j * phase))
    assert root[0].real >= 0.0
    assert np.all(np.abs(np.diff(np.unwrap(np.angle(root)))) < 0.3)


def test_calibration_refuses_sensitivities_of_the_wrong_shape() -> None:
    with pytest.raises(ValueError, match="'sensitivity_v_per_pa' must have shape"):
        metrology.ReciprocityCalibration(
            frequencies_hz=_F,
            sensitivity_v_per_pa=np.ones((2, 3), dtype=complex),
            products_v2_per_pa2=np.ones((3, 3), dtype=complex),
            field="pressure",
            method="three_microphones",
            corrections_db={},
        )


def test_calibration_levels_phases_and_read_only_columns() -> None:
    sensitivities = np.array(
        [[0.05j, -0.05, 0.05], [0.04, 0.04, 0.04], [0.06, 0.06, 0.06]]
    )
    calibration = metrology.ReciprocityCalibration(
        frequencies_hz=_F,
        sensitivity_v_per_pa=sensitivities,
        products_v2_per_pa2=np.ones((3, 3), dtype=complex),
        field="free_field",
        method="three_microphones",
        corrections_db={"c": [0.1, 0.0, -0.1]},
        expanded_uncertainty_db=0.1,
    )
    np.testing.assert_allclose(calibration.phase_deg[0], [90.0, 180.0, 0.0])
    np.testing.assert_allclose(
        calibration.sensitivity_level_db[1],
        20.0 * np.log10(0.04) + np.array([0.1, 0.0, -0.1]),
    )
    np.testing.assert_allclose(calibration.expanded_uncertainty_db, [0.1, 0.1, 0.1])
    with pytest.raises(ValueError, match="read-only"):
        calibration.sensitivity_v_per_pa[0, 0] = 1.0


def test_budget_combines_in_quadrature_with_k_2() -> None:
    budget = metrology.reciprocity_uncertainty_budget(
        _F,
        {"voltage_ratio": 0.003, "coupler_length": [0.004, 0.004, 0.012]},
        additional_components_db={"leakage check": 0.0},
    )
    np.testing.assert_allclose(
        budget.combined_uncertainty_db,
        np.sqrt([0.003**2 + 0.004**2] * 2 + [0.003**2 + 0.012**2]),
    )
    np.testing.assert_allclose(
        budget.expanded_uncertainty_db, 2.0 * budget.combined_uncertainty_db
    )
    np.testing.assert_allclose(
        budget.linear_combined_uncertainty_db, budget.combined_uncertainty_db, rtol=1e-3
    )
    assert budget.names == ("voltage_ratio", "coupler_length", "leakage check")
    assert budget.components[:2] == ("Voltage ratio", "Coupler length")
    assert budget.standard == "IEC 61094-2:2009"


def test_budget_refuses_a_component_of_the_other_part() -> None:
    with pytest.raises(ValueError, match="are not components of Table 1"):
        metrology.reciprocity_uncertainty_budget(
            _F, {"coupler_length": 0.01}, field="free_field"
        )


def test_budget_refuses_an_additional_component_named_like_a_row() -> None:
    with pytest.raises(ValueError, match="name of a component"):
        metrology.reciprocity_uncertainty_budget(
            _F, {}, additional_components_db={"rounding": 0.001}
        )


def test_budget_refuses_no_component() -> None:
    with pytest.raises(ValueError, match="at least one"):
        metrology.reciprocity_uncertainty_budget(_F, {})


def test_budget_refuses_a_negative_uncertainty() -> None:
    with pytest.raises(ValueError, match="'standard_uncertainties_db' must be"):
        metrology.reciprocity_uncertainty_budget(_F, {"rounding": -0.001})


def test_tables_are_read_only() -> None:
    with pytest.raises(TypeError):
        metrology.IEC61094_2_TABLE_1["new"] = None  # type: ignore[index]


# ---------------------------------------------------------------------------
# What the shared columns and the results refuse
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("values", "fragment"),
    [
        ("abc", "'z' must be numeric"),
        ([1.0, 2.0], "'z' must hold one value per frequency"),
        ([1.0, np.nan, 1.0], "'z' must contain only finite values"),
        ([1.0, 0.0, 1.0], "'z' must not be zero"),
    ],
    ids=["not-numeric", "wrong-length", "not-finite", "zero"],
)
def test_a_complex_column_refuses(values: object, fragment: str) -> None:
    """The column every impedance and ratio of a calibration goes through."""
    with pytest.raises(ValueError, match=fragment):
        rcal._complex_column(values, "z", 3)  # type: ignore[arg-type]


def test_a_complex_column_spreads_a_single_value() -> None:
    np.testing.assert_array_equal(rcal._complex_column(2.0j, "z", 3), [2j, 2j, 2j])


def _calibration_fields() -> dict[str, object]:
    return {
        "frequencies_hz": _F,
        "sensitivity_v_per_pa": np.full((3, 3), 0.05, dtype=complex),
        "products_v2_per_pa2": np.ones((3, 3), dtype=complex),
        "field": "pressure",
        "method": "three_microphones",
        "corrections_db": {},
    }


def test_calibration_refuses_a_sensitivity_that_is_not_finite() -> None:
    fields = _calibration_fields()
    fields["sensitivity_v_per_pa"] = np.array(
        [[0.05, np.inf, 0.05], [0.04, 0.04, 0.04], [0.06, 0.06, 0.06]]
    )
    with pytest.raises(ValueError, match="'sensitivity_v_per_pa' must be finite"):
        metrology.ReciprocityCalibration(**fields)  # type: ignore[arg-type]


def test_calibration_refuses_a_negative_uncertainty() -> None:
    fields = _calibration_fields()
    fields["expanded_uncertainty_db"] = [0.03, -0.01, 0.03]
    with pytest.raises(ValueError, match="'expanded_uncertainty_db' must be"):
        metrology.ReciprocityCalibration(**fields)  # type: ignore[arg-type]


def test_calibration_of_a_pair_needs_one_product() -> None:
    fields = _calibration_fields()
    fields["method"] = "auxiliary_source"
    fields["sensitivity_v_per_pa"] = np.full((2, 3), 0.05, dtype=complex)
    with pytest.raises(ValueError, match="'products_v2_per_pa2' must have shape"):
        metrology.ReciprocityCalibration(**fields)  # type: ignore[arg-type]


def test_budget_refuses_names_and_components_that_disagree() -> None:
    matrix = np.full((2, 3), 0.01)
    with pytest.raises(ValueError, match="'names' and 'components' must hold"):
        metrology.ReciprocityUncertaintyBudget(
            frequencies_hz=_F,
            field="pressure",
            names=("rounding", "repeatability"),
            components=("Rounding error",),
            standard_uncertainties_db=matrix,
        )


def test_budget_refuses_a_matrix_of_the_wrong_shape() -> None:
    matrix = np.full((1, 2), 0.01)
    with pytest.raises(ValueError, match="'standard_uncertainties_db' must have shape"):
        metrology.ReciprocityUncertaintyBudget(
            frequencies_hz=_F,
            field="pressure",
            names=("rounding",),
            components=("Rounding error",),
            standard_uncertainties_db=matrix,
        )
