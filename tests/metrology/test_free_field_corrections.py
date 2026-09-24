#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 62585:2012: corrections for the free-field response of a sound level meter.

The oracle is the printed page of BS EN 62585:2012 (EN 62585:2012, which is
IEC 62585:2012 unchanged): the budgets of Tables I.2 and I.3 on folios 38 and
39 (PDF pages 40 and 41), the exact frequencies of Table H.1 on folio 35 (PDF
page 37) and the maxima of clauses 9 to 14 on folios 13 to 16. The printed
values are in ``tests/reference_data``. The four measurement models print no
worked example, so they are checked against the equations they come from:
readings built from known responses by Formulas (D.1) to (D.4), (E.1) to
(E.3B) and (F.1) to (F.3) have to give back the correction those responses
define.
"""

from __future__ import annotations

import dataclasses
import math
import types

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref
from scipy.stats import t as student

from phonometry import metrology
from phonometry.metrology import free_field_corrections as ffc

#: The exact one-third-octave frequencies from 63 Hz to 16 kHz.
_THIRDS = metrology.exact_frequencies(63.0, 16000.0, fraction=3)

#: Exact base-ten counterparts of the nominal frequencies the maxima name.
_EXACT = {
    63.0: 63.0957344480193,
    4000.0: 3981.0717055349724,
    5000.0: 5011.872336272725,
    8000.0: 7943.282347242815,
    10000.0: 10000.0,
}


def _budget_i2(**kwargs: object) -> metrology.CorrectionUncertaintyBudget:
    return metrology.correction_uncertainty_budget(
        ref.IEC62585_TABLE_I2_VALUES_DB,
        repeatability_dof=ref.IEC62585_REPEATABILITY_DOF,
        frequency_hz=1000.0,
        **kwargs,  # type: ignore[arg-type]
    )


def _budget_i3(**kwargs: object) -> metrology.CorrectionUncertaintyBudget:
    return metrology.correction_uncertainty_budget(
        ref.IEC62585_TABLE_I3_VALUES_DB,
        repeatability_dof=ref.IEC62585_REPEATABILITY_DOF,
        frequency_hz=8000.0,
        **kwargs,  # type: ignore[arg-type]
    )


# --------------------------------------------------------------------------
# Tables I.1 to I.3: the uncertainty budget
# --------------------------------------------------------------------------
def test_table_i1_holds_the_fifteen_components_in_order() -> None:
    assert tuple(metrology.IEC62585_TABLE_I1) == tuple(f"a{i}" for i in range(1, 16))
    assert isinstance(metrology.IEC62585_TABLE_I1, types.MappingProxyType)
    row = metrology.IEC62585_TABLE_I1["a7"]
    assert (row.symbol, row.distribution, row.divisor) == ("C_FF,RM", "normal", 2.0)
    assert metrology.IEC62585_TABLE_I1["a15"].divisor == 1.0
    rectangular = [
        key
        for key, row in metrology.IEC62585_TABLE_I1.items()
        if row.distribution == "rectangular"
    ]
    assert rectangular == [f"a{i}" for i in (*range(1, 7), *range(8, 15))]
    assert metrology.IEC62585_TABLE_I1["a1"].divisor == pytest.approx(math.sqrt(3.0))


def test_table_i1_rows_are_frozen() -> None:
    row = metrology.IEC62585_TABLE_I1["a1"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.divisor = 1.0  # type: ignore[misc]


@pytest.mark.parametrize("key", sorted(ref.IEC62585_TABLE_I2_STANDARD_DB))
def test_table_i2_standard_uncertainties_round_to_the_page(key: str) -> None:
    budget = _budget_i2()
    index = budget.descriptors.index(key)
    printed = ref.IEC62585_TABLE_I2_STANDARD_DB[key]
    assert round(float(budget.standard_uncertainties_db[index]), 4) == pytest.approx(
        printed, abs=1e-12
    )


def test_table_i2_combined_uncertainty_and_dof_reproduce() -> None:
    budget = _budget_i2()
    assert round(budget.combined_uncertainty_db, 4) == pytest.approx(
        ref.IEC62585_TABLE_I2_COMBINED_DB, abs=1e-12
    )
    assert round(budget.effective_dof, 2) == pytest.approx(
        ref.IEC62585_TABLE_I2_EFFECTIVE_DOF, abs=1e-9
    )


def test_table_i2_coverage_factor_follows_from_its_own_dof() -> None:
    """The erratum: 29,98 degrees of freedom give k = 2,04, not 2,11."""
    budget = _budget_i2()
    assert budget.coverage_factor == pytest.approx(
        student.ppf(0.975, ref.IEC62585_TABLE_I2_EFFECTIVE_DOF), abs=2e-4
    )
    assert round(budget.coverage_factor, 2) == pytest.approx(2.04, abs=1e-12)
    assert round(budget.coverage_factor, 2) != ref.IEC62585_TABLE_I2_PRINTED_K
    # 2,11 is the Student factor for about 17 degrees of freedom.
    assert round(float(student.ppf(0.975, 17)), 2) == pytest.approx(
        ref.IEC62585_TABLE_I2_PRINTED_K, abs=1e-12
    )
    # 2,042 times 0,05903 dB is 0,1206 dB: 0,12(1) to the printed guard digit.
    assert round(budget.expanded_uncertainty_db, 3) == pytest.approx(
        ref.IEC62585_TABLE_I2_EXPANDED_DB, abs=1e-12
    )
    # The printed guard digit, 0,12(4), follows from the printed k instead.
    printed = ref.IEC62585_TABLE_I2_PRINTED_K * ref.IEC62585_TABLE_I2_COMBINED_DB
    assert round(printed, 3) == pytest.approx(
        ref.IEC62585_TABLE_I2_PRINTED_EXPANDED_DB, abs=1e-12
    )


def test_table_i3_reproduces() -> None:
    budget = _budget_i3()
    assert round(budget.combined_uncertainty_db, 3) == pytest.approx(
        ref.IEC62585_TABLE_I3_COMBINED_DB, abs=1e-12
    )
    assert budget.effective_dof > ref.IEC62585_TABLE_I3_DOF_ABOVE
    assert round(budget.coverage_factor, 2) == pytest.approx(
        ref.IEC62585_TABLE_I3_K, abs=1e-12
    )
    assert round(budget.expanded_uncertainty_db, 2) == pytest.approx(
        ref.IEC62585_TABLE_I3_EXPANDED_DB, abs=1e-12
    )
    for key, printed in ref.IEC62585_TABLE_I3_STANDARD_DB.items():
        index = budget.descriptors.index(key)
        assert round(float(budget.standard_uncertainties_db[index]), 4) == (
            pytest.approx(printed, abs=1e-12)
        )


def test_budget_is_combine_uncertainty_with_unit_sensitivities() -> None:
    budget = _budget_i2(correction_db=0.42)
    assert budget.correction_db == pytest.approx(0.42)
    assert np.allclose(np.abs(budget.uncertainty.sensitivities), 1.0, atol=1e-9)
    assert np.allclose(
        budget.uncertainty.contributions, budget.standard_uncertainties_db, atol=1e-12
    )
    quadrature = math.sqrt(float(np.sum(budget.standard_uncertainties_db**2)))
    assert budget.combined_uncertainty_db == pytest.approx(quadrature, rel=1e-9)
    welch = budget.combined_uncertainty_db**4 / (
        ref.IEC62585_TABLE_I2_VALUES_DB["a15"] ** 4 / ref.IEC62585_REPEATABILITY_DOF
    )
    assert budget.effective_dof == pytest.approx(welch, rel=1e-9)


def test_budget_with_every_dof_infinite_takes_the_normal_factor() -> None:
    budget = metrology.correction_uncertainty_budget(
        ref.IEC62585_TABLE_I2_VALUES_DB, repeatability_dof=math.inf, frequency_hz=1e3
    )
    assert math.isinf(budget.effective_dof)
    assert budget.coverage_factor == pytest.approx(1.959964, abs=1e-6)


@pytest.mark.parametrize(
    ("frequency_hz", "expanded_db"), ref.IEC62585_STATIC_PRESSURE_EXPANDED_DB
)
def test_static_pressure_below_97_kpa_adds_the_clause_6_component(
    frequency_hz: float, expanded_db: float
) -> None:
    values = ref.IEC62585_TABLE_I2_VALUES_DB
    low = metrology.correction_uncertainty_budget(
        values,
        repeatability_dof=2,
        frequency_hz=frequency_hz,
        static_pressure_kpa=95.0,
    )
    assert low.descriptors[-1] == "static pressure"
    assert low.values_db[-1] == pytest.approx(expanded_db)
    assert low.divisors[-1] == pytest.approx(2.0)
    assert low.standard_uncertainties_db[-1] == pytest.approx(expanded_db / 2.0)
    normal = metrology.correction_uncertainty_budget(
        values,
        repeatability_dof=2,
        frequency_hz=frequency_hz,
        static_pressure_kpa=ref.IEC62585_STATIC_PRESSURE_LIMIT_KPA,
    )
    assert len(normal.descriptors) == len(metrology.IEC62585_TABLE_I1)


@pytest.mark.parametrize("pressure_kpa", [79.9, 105.1])
def test_static_pressure_outside_clause_6_is_refused(pressure_kpa: float) -> None:
    values = ref.IEC62585_TABLE_I2_VALUES_DB
    with pytest.raises(ValueError, match="static_pressure_kpa"):
        metrology.correction_uncertainty_budget(
            values,
            repeatability_dof=2,
            frequency_hz=1e3,
            static_pressure_kpa=pressure_kpa,
        )


def test_additional_components_enter_the_budget() -> None:
    extra = metrology.Quantity(0.0, 0.02, name="actuator drive")
    budget = _budget_i2(additional_components=[extra])
    assert budget.descriptors[-1] == "actuator drive"
    base = _budget_i2()
    assert budget.combined_uncertainty_db == pytest.approx(
        math.hypot(base.combined_uncertainty_db, 0.02), rel=1e-9
    )


def test_budget_needs_all_fifteen_components() -> None:
    values = dict(ref.IEC62585_TABLE_I2_VALUES_DB)
    del values["a13"]
    with pytest.raises(ValueError, match="values_db"):
        metrology.correction_uncertainty_budget(
            values, repeatability_dof=2, frequency_hz=1e3
        )


def test_budget_refuses_an_unknown_component() -> None:
    values = {**ref.IEC62585_TABLE_I2_VALUES_DB, "a16": 0.01}
    with pytest.raises(ValueError, match="values_db"):
        metrology.correction_uncertainty_budget(
            values, repeatability_dof=2, frequency_hz=1e3
        )


def test_budget_refuses_a_negative_value() -> None:
    values = {**ref.IEC62585_TABLE_I2_VALUES_DB, "a5": -0.05}
    with pytest.raises(ValueError, match="a5"):
        metrology.correction_uncertainty_budget(
            values, repeatability_dof=2, frequency_hz=1e3
        )


@pytest.mark.parametrize("dof", [0.0, -1.0, math.nan])
def test_budget_refuses_degrees_of_freedom_that_are_not_positive(dof: float) -> None:
    values = ref.IEC62585_TABLE_I2_VALUES_DB
    with pytest.raises(ValueError, match="repeatability_dof"):
        metrology.correction_uncertainty_budget(
            values, repeatability_dof=dof, frequency_hz=1e3
        )


def test_budget_refuses_a_combination_its_columns_do_not_give() -> None:
    budget = _budget_i2()
    doubled = budget.values_db * 2.0
    with pytest.raises(ValueError, match="'uncertainty' must be the combination"):
        dataclasses.replace(budget, values_db=doubled)


def test_budget_refuses_column_dofs_that_are_not_positive() -> None:
    budget = _budget_i2()
    dofs = np.where(np.isfinite(budget.dofs), 0.0, budget.dofs)
    with pytest.raises(ValueError, match="'dofs' must be positive"):
        dataclasses.replace(budget, dofs=dofs)


def test_budget_columns_are_read_only() -> None:
    budget = _budget_i2()
    with pytest.raises(ValueError, match="read-only"):
        budget.values_db[0] = 1.0


# --------------------------------------------------------------------------
# Annex H: the exact frequencies
# --------------------------------------------------------------------------
def test_table_h1_reproduces_to_seven_significant_digits() -> None:
    frequencies = metrology.exact_frequencies(1000.0, 10000.0)
    assert frequencies.size == len(ref.IEC62585_TABLE_H1_KHZ)
    assert np.array_equal(np.round(frequencies / 1000.0, 6), ref.IEC62585_TABLE_H1_KHZ)


def test_exact_octaves_and_thirds() -> None:
    octaves = metrology.exact_frequencies(63.0, 16000.0, fraction=1)
    assert octaves.size == 9
    assert octaves[4] == pytest.approx(1000.0)
    assert octaves[0] == pytest.approx(_EXACT[63.0])
    assert _THIRDS.size == 25
    assert np.allclose(np.diff(np.log10(_THIRDS)), 0.1)


def test_exact_frequencies_can_be_empty_and_are_read_only() -> None:
    assert metrology.exact_frequencies(1001.0, 1050.0).size == 0
    frequencies = metrology.exact_frequencies(1000.0, 2000.0)
    with pytest.raises(ValueError, match="read-only"):
        frequencies[0] = 1.0


def test_exact_frequencies_refuse_limits_in_the_wrong_order() -> None:
    with pytest.raises(ValueError, match="highest_hz"):
        metrology.exact_frequencies(2000.0, 1000.0)


@pytest.mark.parametrize("fraction", [0, 2.5, -3])
def test_exact_frequencies_refuse_a_designator_that_is_not_whole(
    fraction: float,
) -> None:
    with pytest.raises(ValueError, match="fraction"):
        metrology.exact_frequencies(100.0, 1000.0, fraction=fraction)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Clauses 9 to 14: the maxima and the verdict
# --------------------------------------------------------------------------
@pytest.mark.parametrize(("clause", "nominal_hz", "maximum_db"), ref.IEC62585_MAXIMA)
def test_maxima_of_clauses_9_to_14(
    clause: int, nominal_hz: float, maximum_db: float
) -> None:
    """At the nominal frequency and at its exact base-ten counterpart."""
    frequencies = sorted({nominal_hz, _EXACT[nominal_hz]})
    maxima = metrology.maximum_expanded_uncertainty(frequencies, clause=clause)
    assert np.allclose(maxima, maximum_db, atol=1e-12)


def test_a_frequency_within_two_percent_of_a_boundary_is_read_as_it() -> None:
    """4,05 kHz is "4 kHz" to 2 %: up to and including 4 kHz, not above."""
    near = metrology.maximum_expanded_uncertainty([4050.0, 4100.0], clause=12)
    assert np.allclose(near, [0.25, 0.35], rtol=0.0, atol=1e-12)


def test_clause_10_states_no_maximum_below_63_hz() -> None:
    with pytest.raises(ValueError, match="63 Hz"):
        metrology.maximum_expanded_uncertainty([50.0], clause=10)


@pytest.mark.parametrize("clause", [8, 15, "12", True, 12.5])
def test_only_clauses_9_to_14_state_a_maximum(clause: object) -> None:
    with pytest.raises(ValueError, match="clause"):
        metrology.maximum_expanded_uncertainty([1000.0], clause=clause)  # type: ignore[arg-type]


def test_a_numpy_integer_clause_is_accepted() -> None:
    maxima = metrology.maximum_expanded_uncertainty([1000.0], clause=np.int64(12))  # type: ignore[arg-type]
    assert maxima[0] == pytest.approx(0.25)


def test_verdict_is_inclusive_at_the_maximum() -> None:
    frequencies = [1000.0, 8000.0, 12500.0]
    verdict = metrology.verify_correction_uncertainty(
        frequencies, [0.25, 0.35, 0.50], clause=12
    )
    assert verdict.passes
    assert np.all(verdict.uncertainty_passes)
    assert np.allclose(verdict.margin_db, 0.0)
    assert verdict.failing_frequencies_hz.size == 0
    assert verdict.range_passes is None


def test_verdict_forgives_a_maximum_reached_through_arithmetic() -> None:
    """0,1 + 0,2 is 0,300 000 000 000 000 04 in binary: on 0,30 dB, not above."""
    reached = 0.1 + 0.2
    verdict = metrology.verify_correction_uncertainty([5000.0], [reached], clause=11)
    assert reached > verdict.maximum_uncertainty_db[0]
    assert verdict.passes
    spread = 0.05 * 7
    ranged = metrology.verify_correction_uncertainty(
        [8000.0], [0.2], clause=12, correction_range_db=[spread]
    )
    assert spread > ranged.maximum_uncertainty_db[0]
    assert ranged.passes


def test_verdict_derives_its_maximum_from_the_clause() -> None:
    verdict = metrology.CorrectionUncertaintyVerification(
        clause=12, frequencies_hz=[1000.0, 10000.0], expanded_uncertainty_db=[0.3, 0.3]
    )
    assert np.allclose(verdict.maximum_uncertainty_db, [0.25, 0.5])
    assert np.array_equal(verdict.failing_frequencies_hz, [1000.0])
    assert "maximum_uncertainty_db" not in {
        field.name for field in dataclasses.fields(verdict)
    }


def test_verdict_of_clause_10_refuses_a_frequency_below_63_hz() -> None:
    with pytest.raises(ValueError, match="63 Hz"):
        metrology.CorrectionUncertaintyVerification(
            clause=10, frequencies_hz=[50.0], expanded_uncertainty_db=[0.1]
        )


def test_verdict_fails_above_the_maximum() -> None:
    verdict = metrology.verify_correction_uncertainty(
        [1000.0, 8000.0], [0.24, 0.36], clause=13
    )
    assert not verdict.passes
    assert np.array_equal(verdict.failing_frequencies_hz, [8000.0])
    assert verdict.subject == "a comparison coupler"


def test_verdict_judges_the_range_over_the_microphones() -> None:
    verdict = metrology.verify_correction_uncertainty(
        [1000.0, 8000.0], 0.2, clause=12, correction_range_db=[0.1, 0.4]
    )
    assert np.array_equal(verdict.uncertainty_passes, [True, True])
    assert np.array_equal(verdict.range_passes, [True, False])
    assert not verdict.passes


def test_range_belongs_to_clauses_12_to_14() -> None:
    with pytest.raises(ValueError, match="range"):
        metrology.verify_correction_uncertainty(
            [1000.0], [0.2], clause=9, correction_range_db=[0.1]
        )


def test_verdict_has_no_truth_value() -> None:
    verdict = metrology.verify_correction_uncertainty([1000.0], [0.1], clause=11)
    with pytest.raises(TypeError, match="passes"):
        bool(verdict)


def test_verdict_refuses_a_negative_uncertainty() -> None:
    with pytest.raises(ValueError, match="expanded_uncertainty_db"):
        metrology.verify_correction_uncertainty([1000.0], [-0.1], clause=11)


def test_verdict_refuses_columns_of_another_length() -> None:
    with pytest.raises(ValueError, match="coverage_factor"):
        metrology.verify_correction_uncertainty(
            [1000.0, 2000.0], 0.1, clause=11, coverage_factor=[2.0, 2.0, 2.0]
        )


def test_verdict_from_the_budgets_of_annex_i() -> None:
    """Tables I.2 and I.3 are within the maxima of clause 13."""
    budgets = (_budget_i2(), _budget_i3())
    verdict = metrology.verify_correction_uncertainty(
        [b.frequency_hz for b in budgets],
        [b.expanded_uncertainty_db for b in budgets],
        clause=13,
        coverage_factor=[b.coverage_factor for b in budgets],
    )
    assert verdict.passes
    assert np.allclose(verdict.maximum_uncertainty_db, [0.25, 0.35])


# --------------------------------------------------------------------------
# Annex A: the adjustment value
# --------------------------------------------------------------------------
_A_FREQUENCIES = np.array([125.0, 1000.0, 8000.0])
_A_DEVIATION = np.array([0.2, 0.1, -0.6])


def test_equal_weights_take_the_mean_deviation() -> None:
    result = metrology.adjustment_value(
        _A_FREQUENCIES, 94.0 + _A_DEVIATION, 93.9, calibrator_level_db=94.0
    )
    s = -float(np.mean(_A_DEVIATION))
    assert result.sensitivity_adjustment_db == pytest.approx(s)
    assert np.allclose(result.adjusted_deviation_db, _A_DEVIATION + s)
    assert result.calibrator_indicated_level_db == pytest.approx(93.9 + s)
    assert result.adjustment_db == pytest.approx(94.0 - (93.9 + s))
    assert result.check_frequency_offset_db == pytest.approx(0.1 + s)
    assert result.free_field_indicated_level_db == pytest.approx(94.0 + 0.1 + s)
    assert result.pressure_indicated_level_db is None
    assert result.pressure_to_free_field_correction_db is None


def test_adjustment_value_is_l1_less_l4() -> None:
    """ΔL = L1 - L4, added to what the adjusted meter reads on the calibrator."""
    result = metrology.adjustment_value(
        _A_FREQUENCIES, 94.0 + _A_DEVIATION, 93.7, calibrator_level_db=94.0
    )
    # s = +0,1 dB, so L4 = 93,7 + 0,1 = 93,8 dB and ΔL = 94,0 - 93,8 = +0,2 dB.
    assert result.sensitivity_adjustment_db == pytest.approx(0.1, abs=1e-12)
    assert result.calibrator_indicated_level_db == pytest.approx(93.8, abs=1e-12)
    assert result.adjustment_db == pytest.approx(0.2, abs=1e-12)
    assert result.adjustment_db > 0.0
    assert result.calibrator_indicated_level_db + result.adjustment_db == (
        pytest.approx(result.calibrator_level_db, abs=1e-12)
    )


def test_a_nominal_check_frequency_finds_its_exact_counterpart() -> None:
    """250 Hz is the exact one-third-octave 251,19 Hz, to within 2 %."""
    result = metrology.adjustment_value(
        _THIRDS,
        94.0,
        94.0,
        calibrator_level_db=94.0,
        check_frequency_hz=250.0,
    )
    assert result.check_frequency_offset_db == pytest.approx(0.0, abs=1e-12)
    actuator = metrology.electrostatic_actuator_correction(
        _THIRDS,
        94.0 + 0.01 * np.arange(_THIRDS.size),
        94.0,
        94.0,
        reference_sensitivity_level_db=-26.0,
        check_frequency_hz=250.0,
    )
    exact = float(_THIRDS[np.argmin(np.abs(_THIRDS - 250.0))])
    assert actuator.check_frequency_hz == pytest.approx(exact)
    assert exact == pytest.approx(251.188643, abs=1e-6)
    assert actuator.correction_db[_THIRDS == exact][0] == 0.0


def test_tolerances_weigh_the_fit() -> None:
    tolerance = np.array([1.0, 0.7, np.inf])
    result = metrology.adjustment_value(
        _A_FREQUENCIES,
        94.0 + _A_DEVIATION,
        94.0,
        calibrator_level_db=94.0,
        tolerance_db=tolerance,
    )
    weights = np.array([1.0, 1.0 / 0.49, 0.0])
    expected = -float(np.sum(weights * _A_DEVIATION) / np.sum(weights))
    assert result.sensitivity_adjustment_db == pytest.approx(expected)
    assert result.weights.sum() == pytest.approx(1.0)
    assert result.weights[2] == 0.0


def test_the_incident_level_carries_a_field_below_the_calibrator_level() -> None:
    result = metrology.adjustment_value(
        _A_FREQUENCIES,
        90.0 + _A_DEVIATION,
        93.9,
        calibrator_level_db=94.0,
        incident_level_db=90.0,
    )
    assert np.allclose(result.free_field_deviation_db, _A_DEVIATION)


def test_pressure_response_gives_l3_and_the_pressure_correction() -> None:
    pressure = 94.0 + np.array([0.2, 0.05, -1.5])
    result = metrology.adjustment_value(
        _A_FREQUENCIES,
        94.0 + _A_DEVIATION,
        93.9,
        calibrator_level_db=94.0,
        pressure_indicated_level_db=pressure,
    )
    s = result.sensitivity_adjustment_db
    assert result.pressure_indicated_level_db == pytest.approx(94.05 + s)
    assert np.allclose(
        result.pressure_to_free_field_correction_db, -(pressure - 94.0 + s)
    )


def test_adjustment_needs_the_check_frequency_among_the_frequencies() -> None:
    with pytest.raises(ValueError, match="check_frequency_hz"):
        metrology.adjustment_value(
            [125.0, 8000.0], [94.0, 93.0], 94.0, calibrator_level_db=94.0
        )


@pytest.mark.parametrize("tolerance", [[1.0, 0.0, 1.0], [1.0, np.nan, 1.0], [-1.0]])
def test_adjustment_refuses_a_tolerance_that_is_not_positive(
    tolerance: list[float],
) -> None:
    with pytest.raises(ValueError, match="tolerance_db"):
        metrology.adjustment_value(
            _A_FREQUENCIES,
            94.0 + _A_DEVIATION,
            94.0,
            calibrator_level_db=94.0,
            tolerance_db=tolerance,
        )


def test_adjustment_refuses_a_tolerance_infinite_everywhere() -> None:
    with pytest.raises(ValueError, match="finite at one frequency"):
        metrology.adjustment_value(
            _A_FREQUENCIES,
            94.0 + _A_DEVIATION,
            94.0,
            calibrator_level_db=94.0,
            tolerance_db=np.inf,
        )


def test_adjustment_value_columns_are_read_only() -> None:
    result = metrology.adjustment_value(
        _A_FREQUENCIES, 94.0 + _A_DEVIATION, 94.0, calibrator_level_db=94.0
    )
    with pytest.raises(ValueError, match="read-only"):
        result.free_field_deviation_db[0] = 0.0


# --------------------------------------------------------------------------
# Annexes D, E and F: readings built from known responses give them back
# --------------------------------------------------------------------------
_F = np.array([125.0, 1000.0, 4000.0, 8000.0])
_SLM_FREE = np.array([0.05, 0.0, -0.4, -1.1])  # Delta L_F,SLM
_SLM_PRESSURE = np.array([0.02, 0.0, -0.9, -2.4])  # Delta L_P,SLM
_RM_FREE = np.array([0.0, 0.08, 0.95, 2.6])  # Delta L_F,RM
_RM_PRESSURE = np.array([0.0, 0.0, 0.1, 0.2])  # Delta L_P,RM
_FIELD_1 = 94.0 + np.array([0.0, 0.01, -0.02, 0.03])  # L_p,F1
_FIELD_2 = 94.0  # L_p,F2
_ON_SLM = 94.0 + np.array([0.0, 0.02, 0.05, 0.1])  # pressure on the meter
_ON_RM = 94.0  # pressure on the reference

#: What the two free-field and two pressure responses define as the answer.
_TRUE_CORRECTION = _SLM_FREE - _SLM_PRESSURE
_REFERENCE_CORRECTION = _RM_FREE - _RM_PRESSURE


def test_formula_d7_returns_the_correction_the_responses_define() -> None:
    result = metrology.sound_calibrator_correction(
        _F,
        _FIELD_1 + _SLM_FREE,  # (D.1)
        _FIELD_2 + _RM_FREE,  # (D.2)
        _ON_SLM + _SLM_PRESSURE,  # (D.3)
        _ON_RM + _RM_PRESSURE,  # (D.4)
        reference_free_field_correction_db=_REFERENCE_CORRECTION,
        free_field_level_difference_db=_FIELD_1 - _FIELD_2,
        calibrator_level_difference_db=_ON_SLM - _ON_RM,
    )
    assert np.allclose(result.correction_db, _TRUE_CORRECTION, atol=1e-12)
    assert (result.formula, result.clause, result.determinations) == ("D.7", 12, 1)
    assert np.allclose(result.range_db, 0.0)


def test_formula_e6_returns_the_correction_with_figure_e1_labels() -> None:
    """(E.3A) L_ind3a = L_p,P1 + dL_P,RM and (E.3B) L_ind3b = L_p,P2 + dL_P,SLM."""
    ind3a = _ON_RM + _RM_PRESSURE
    ind3b = _ON_SLM + _SLM_PRESSURE
    ind1 = _FIELD_1 + _SLM_FREE
    ind2 = _FIELD_2 + _RM_FREE
    result = metrology.comparison_coupler_correction(
        _F,
        ind1,
        ind2,
        ind3b,
        ind3a,
        reference_free_field_correction_db=_REFERENCE_CORRECTION,
        free_field_level_difference_db=_FIELD_1 - _FIELD_2,
        coupler_level_difference_db=_ON_SLM - _ON_RM,
    )
    assert np.allclose(result.correction_db, _TRUE_CORRECTION, atol=1e-12)
    assert (result.formula, result.clause) == ("E.6", 13)
    # (E.6) as printed, read with Figure E.1's labels, is off by twice the
    # difference of the two pressure responses (the erratum).
    printed = (
        (ind1 - ind3a)
        - (ind2 - ind3b)
        - (_FIELD_1 - _FIELD_2)
        + (_ON_RM - _ON_SLM)
        + _REFERENCE_CORRECTION
    )
    assert np.allclose(
        printed - _TRUE_CORRECTION, 2.0 * (_SLM_PRESSURE - _RM_PRESSURE), atol=1e-12
    )


def test_formula_f13_returns_the_normalised_correction() -> None:
    sensitivity = -26.0 + np.array([0.0, 0.0, 0.1, 0.3])  # S_RM, dB re 1 V/Pa
    gain = np.array([0.0, 0.01, 0.02, -0.05])  # G_RC
    actuator = 94.0 + np.array([0.0, 0.0, 0.01, 0.0])  # L_EA
    slm_actuator = np.array([0.1, 0.0, -0.7, -1.9])  # Delta L_EA,SLM
    result = metrology.electrostatic_actuator_correction(
        _F,
        _FIELD_1 + _SLM_FREE,  # (F.1)
        _FIELD_2 + sensitivity + gain,  # (F.2), Delta L_F,RM = S_RM + G_RC
        actuator + slm_actuator,  # (F.3)
        reference_sensitivity_level_db=sensitivity,
        reference_channel_gain_db=gain,
        actuator_level_db=actuator,
        free_field_level_difference_db=_FIELD_1 - _FIELD_2,
    )
    absolute = _SLM_FREE - slm_actuator
    assert np.allclose(result.correction_db, absolute - absolute[1], atol=1e-12)
    assert result.correction_db[1] == 0.0
    assert result.check_frequency_hz == 1000.0
    assert (result.formula, result.clause) == ("F.13", 14)


def test_the_actuator_needs_its_normalisation_frequency() -> None:
    with pytest.raises(ValueError, match="check_frequency_hz"):
        metrology.electrostatic_actuator_correction(
            [125.0, 8000.0],
            0.0,
            0.0,
            0.0,
            reference_sensitivity_level_db=-26.0,
        )


def test_determinations_are_averaged_and_their_range_kept() -> None:
    slm_free = 94.0 + np.vstack([_SLM_FREE + offset for offset in (0.0, 0.03, -0.02)])
    result = metrology.sound_calibrator_correction(
        _F,
        slm_free,
        94.0 + _RM_FREE,
        94.0 + _SLM_PRESSURE,
        94.0 + _RM_PRESSURE,
        reference_free_field_correction_db=_REFERENCE_CORRECTION,
    )
    assert result.determinations == 3
    assert np.allclose(result.correction_db, _TRUE_CORRECTION + 0.01 / 3.0)
    assert np.allclose(result.range_db, 0.05)
    with pytest.raises(ValueError, match="read-only"):
        result.corrections_db[0, 0] = 0.0


def _three_microphones_on_three_calibrators(
    **kwargs: object,
) -> metrology.FreeFieldCorrection:
    """Nine determinations of identical microphones on calibrators that load
    them 0, 0,15 and 0,30 dB apart (D.2 step 6, one row per combination).
    """
    loading = np.tile([0.0, 0.15, 0.30], 3)[:, None]
    return metrology.sound_calibrator_correction(
        _F,
        94.0 + np.tile(_SLM_FREE, (9, 1)),
        94.0 + _RM_FREE,
        94.0 + _SLM_PRESSURE + loading,
        94.0 + _RM_PRESSURE,
        reference_free_field_correction_db=_REFERENCE_CORRECTION,
        **kwargs,  # type: ignore[arg-type]
    )


def test_the_range_is_taken_over_the_microphones() -> None:
    """Clause 12: the range of three microphones, not of the calibrators."""
    grouped = _three_microphones_on_three_calibrators(
        microphones=[1, 1, 1, 2, 2, 2, 3, 3, 3]
    )
    assert (grouped.determinations, grouped.microphone_count) == (9, 3)
    assert grouped.microphone_corrections_db.shape == (3, _F.size)
    assert np.allclose(grouped.range_db, 0.0, atol=1e-12)
    assert np.allclose(grouped.correction_db, _TRUE_CORRECTION - 0.15)
    assert grouped.microphones == (1, 1, 1, 2, 2, 2, 3, 3, 3)
    verdict = metrology.verify_correction_uncertainty(
        grouped.frequencies_hz,
        0.2,
        clause=grouped.clause,
        correction_range_db=grouped.range_db,
    )
    assert verdict.passes
    # Without the grouping every determination is a microphone of its own.
    ungrouped = _three_microphones_on_three_calibrators()
    assert ungrouped.microphone_count == 9
    assert np.allclose(ungrouped.range_db, 0.30)


def test_microphones_need_one_label_per_determination() -> None:
    with pytest.raises(ValueError, match="one label per determination"):
        _three_microphones_on_three_calibrators(microphones=[1, 2, 3])


def test_microphones_are_labels_not_a_string() -> None:
    with pytest.raises(ValueError, match="single string"):
        _three_microphones_on_three_calibrators(microphones="111222333")


def test_determinations_must_agree_in_number() -> None:
    three = np.zeros((3, _F.size))
    two = np.zeros((2, _F.size))
    with pytest.raises(ValueError, match="determinations"):
        metrology.comparison_coupler_correction(
            _F, three, two, 0.0, 0.0, reference_free_field_correction_db=0.0
        )


def test_readings_need_one_column_per_frequency() -> None:
    too_long = np.zeros(_F.size + 1)
    with pytest.raises(ValueError, match="slm_calibrator_level_db"):
        metrology.sound_calibrator_correction(
            _F, 0.0, 0.0, too_long, 0.0, reference_free_field_correction_db=0.0
        )


def test_readings_must_be_finite() -> None:
    with pytest.raises(ValueError, match="reference_coupler_level_db"):
        metrology.comparison_coupler_correction(
            _F,
            0.0,
            0.0,
            0.0,
            [0.0, np.nan, 0.0, 0.0],
            reference_free_field_correction_db=0.0,
        )


_ZEROS = np.zeros(_F.size)


def test_correction_result_refuses_an_unknown_source() -> None:
    with pytest.raises(ValueError, match="source"):
        ffc.FreeFieldCorrection(
            frequencies_hz=_F,
            corrections_db=_ZEROS,
            reference_correction_db=_ZEROS,
            source="pistonphone",
        )


def test_only_an_actuator_is_normalised() -> None:
    with pytest.raises(ValueError, match="check_frequency_hz"):
        ffc.FreeFieldCorrection(
            frequencies_hz=_F,
            corrections_db=_ZEROS,
            reference_correction_db=_ZEROS,
            source="sound_calibrator",
            check_frequency_hz=1000.0,
        )


# --------------------------------------------------------------------------
# .plot()
# --------------------------------------------------------------------------
def _correction() -> metrology.FreeFieldCorrection:
    return metrology.sound_calibrator_correction(
        _F,
        94.0 + np.vstack([_SLM_FREE, _SLM_FREE + 0.04]),
        94.0 + _RM_FREE,
        94.0 + _SLM_PRESSURE,
        94.0 + _RM_PRESSURE,
        reference_free_field_correction_db=_REFERENCE_CORRECTION,
    )


@pytest.mark.parametrize("language", ["en", "es"])
def test_every_result_plots(language: str) -> None:
    adjustment = metrology.adjustment_value(
        _A_FREQUENCIES,
        94.0 + _A_DEVIATION,
        94.0,
        calibrator_level_db=94.0,
        tolerance_db=[1.0, 0.7, np.inf],
        pressure_indicated_level_db=94.0 + _A_DEVIATION - 0.1,
    )
    actuator = metrology.electrostatic_actuator_correction(
        _F, 94.0 + _SLM_FREE, 94.0, 94.0, reference_sensitivity_level_db=-26.0
    )
    verdict = metrology.verify_correction_uncertainty(
        _F, [0.1, 0.2, 0.3, 0.4], clause=12, correction_range_db=[0.1, 0.1, 0.1, 0.5]
    )
    for result in (adjustment, _correction(), actuator, _budget_i2(), verdict):
        ax = result.plot(language=language)
        assert ax.get_title()
        plt.close("all")


def test_spanish_labels_are_translated() -> None:
    ax = _budget_i2().plot(language="es")
    labels = [tick.get_text() for tick in ax.get_yticklabels()]
    assert "a15: Repetibilidad" in labels
    assert "Presupuesto de incertidumbre" in ax.get_title()
    plt.close("all")
    ax = _correction().plot(language="es")
    assert ax.get_ylabel() == "Corrección [dB]"
    plt.close("all")


def test_verification_plot_marks_what_exceeds() -> None:
    verdict = metrology.verify_correction_uncertainty(
        _F, [0.1, 0.2, 0.2, 0.6], clause=12
    )
    ax = verdict.plot()
    assert "exceeds the maximum at 1 of 4" in ax.get_title()
    labels = ax.get_legend_handles_labels()[1]
    assert "Exceeds the maximum" in labels
    plt.close("all")


def test_verification_plot_says_so_when_everything_passes() -> None:
    verdict = metrology.verify_correction_uncertainty([1000.0], [0.1], clause=9)
    ax = verdict.plot()
    assert "within the maximum" in ax.get_title()
    plt.close("all")


def test_budget_plot_marks_the_statistical_component() -> None:
    ax = _budget_i2().plot()
    labels = ax.get_legend().get_texts()
    assert any("Type A" in text.get_text() for text in labels)
    plt.close("all")
    ax = metrology.correction_uncertainty_budget(
        ref.IEC62585_TABLE_I2_VALUES_DB, repeatability_dof=math.inf, frequency_hz=1e3
    ).plot()
    labels = ax.get_legend().get_texts()
    assert not any("Type A" in text.get_text() for text in labels)
    assert "∞" in ax.get_title()
    plt.close("all")
