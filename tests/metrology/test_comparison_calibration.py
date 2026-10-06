#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 61094-5:2016 and IEC 61094-8:2012: microphone calibration by comparison.

The oracle is the printed page: IEC 61094-5:2016 Table A.1 on folio 15 (PDF
page 17), Annex C on folio 18 (PDF page 20) and Annex D on folios 19 to 21
(PDF pages 21 to 23); BS EN 61094-8:2012 Table 1 on folio 12 (PDF page 14),
Table 2 on folio 17 (PDF page 19) and B.1 on folio 23 (PDF page 25). The
printed values are in ``tests/reference_data``. The measurement models print
no worked example, so they are checked against the equations they come from:
readings built from known sensitivities, gains and fields by Formulas (C.1)
and (C.2), or by the monitor ratios of IEC 61094-8 A.2, have to give back the
sensitivity those quantities define.
"""

from __future__ import annotations

import dataclasses
import math
import re
import types

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref

from phonometry import fluids, metrology
from phonometry.metrology import comparison_calibration as cc
from phonometry.metrology import random_incidence

_F = np.array([250.0, 1000.0, 2000.0, 4000.0, 8000.0])

#: A reference and a test microphone, sensitivity levels in dB re 1 V/Pa.
_L_REF = np.array([-38.02, -38.00, -37.98, -37.95, -38.10])
_L_TEST = np.array([-26.40, -26.35, -26.30, -26.10, -25.80])


def _d1_budget(**kwargs: object) -> metrology.ComparisonUncertaintyBudget:
    return metrology.comparison_uncertainty_budget(
        ref.IEC61094_5_TABLE_D1_STANDARD_DB,
        frequency_hz=2000.0,
        **kwargs,  # type: ignore[arg-type]
    )


def _interchange_readings(
    gain_1: float = 0.7, gain_2: float = -1.3, asymmetry: float = 0.04
) -> tuple[np.ndarray, np.ndarray]:
    """Formulas (C.1) and (C.2) for the reference as microphone 1.

    Two channels of different gain, a source that drifts between the two
    configurations and a field that is not the same at the two positions:
    none of it may reach the result.
    """
    level_1 = 94.0 + 0.2 * np.log10(_F / 1000.0)
    level_2 = level_1 + 0.3
    at_a = asymmetry
    at_b = -asymmetry / 2.0
    first = (_L_REF + gain_1 + level_1 + at_a) - (_L_TEST + gain_2 + level_1 + at_b)
    second = (_L_TEST + gain_1 + level_2 + at_a) - (_L_REF + gain_2 + level_2 + at_b)
    return first, second


# --------------------------------------------------------------------------
# The printed tables
# --------------------------------------------------------------------------
def test_table_a1_is_the_printed_table() -> None:
    table = metrology.IEC61094_5_TABLE_A1
    assert isinstance(table, types.MappingProxyType)
    printed = {1000.0 * khz: value for khz, value in ref.IEC61094_5_TABLE_A1_DB.items()}
    assert tuple(table) == tuple(printed)
    for frequency, value in printed.items():
        assert table[frequency] == pytest.approx(value, abs=1e-12)


def test_table_d1_standard_uncertainties_follow_from_their_stated_values() -> None:
    """Each of the seven rows that state a value: the semi-range or expanded
    value over its divisor, rounded to the three decimals the table prints.
    """
    table = metrology.IEC61094_5_TABLE_D1
    assert tuple(table) == tuple(ref.IEC61094_5_TABLE_D1_STANDARD_DB)
    assert len(ref.IEC61094_5_TABLE_D1_STATED) == 7
    for key, (stated, divisor) in ref.IEC61094_5_TABLE_D1_STATED.items():
        row = table[key]
        assert row.stated_db == pytest.approx(stated, rel=1e-12)
        assert row.divisor == pytest.approx(divisor, rel=1e-12)
        printed = ref.IEC61094_5_TABLE_D1_STANDARD_DB[key]
        assert row.standard_uncertainty_db == pytest.approx(printed, abs=1e-12)
        assert round(stated / divisor, 3) == pytest.approx(printed, abs=1e-12)


def test_table_d1_repeatability_is_printed_as_a_standard_uncertainty() -> None:
    """The repeatability row states no value, only the standard uncertainty in
    its column.
    """
    row = metrology.IEC61094_5_TABLE_D1["repeatability"]
    assert row.stated_db is None
    assert row.divisor is None
    printed = ref.IEC61094_5_TABLE_D1_STANDARD_DB["repeatability"]
    assert row.standard_uncertainty_db == pytest.approx(printed, abs=1e-12)


def test_table_1_and_table_2_of_61094_8_are_the_printed_tables() -> None:
    assert tuple(metrology.IEC61094_8_TABLE_1) == tuple(ref.IEC61094_8_TABLE_1_DB)
    for key, (at_1k, at_10k) in ref.IEC61094_8_TABLE_1_DB.items():
        row = metrology.IEC61094_8_TABLE_1[key]
        assert row.expanded_uncertainty_1khz_db == pytest.approx(at_1k, abs=1e-12)
        assert row.expanded_uncertainty_10khz_db == pytest.approx(at_10k, abs=1e-12)
    text = {
        key: (row.microphone_types, row.method, row.references)
        for key, row in metrology.IEC61094_8_TABLE_1.items()
    }
    assert text == ref.IEC61094_8_TABLE_1_TEXT
    table = metrology.IEC61094_8_TABLE_2
    assert tuple(table) == tuple(ref.IEC61094_8_TABLE_2_SOURCES)
    assert {key: row.component for key, row in table.items()} == (
        ref.IEC61094_8_TABLE_2_SOURCES
    )
    assert {key: row.subclauses for key, row in table.items()} == (
        ref.IEC61094_8_TABLE_2_SUBCLAUSES
    )
    assert all(row.standard_uncertainty_db is None for row in table.values())


def test_published_tables_are_immutable() -> None:
    for table in (
        metrology.IEC61094_5_TABLE_A1,
        metrology.IEC61094_5_TABLE_D1,
        metrology.IEC61094_8_TABLE_1,
        metrology.IEC61094_8_TABLE_2,
    ):
        assert isinstance(table, types.MappingProxyType)
    row = metrology.IEC61094_5_TABLE_D1["drift"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.stated_db = 0.0  # type: ignore[misc]


# --------------------------------------------------------------------------
# Annex D: the budget
# --------------------------------------------------------------------------
def test_d3_combines_the_printed_column_to_0_0437_not_0_040() -> None:
    """D.3: the root-sum-square of Table D.1 is 0,0437 dB; the page prints
    0,040 dB and 0,08 dB, an erratum.
    """
    budget = _d1_budget()
    assert budget.combined_uncertainty_db == pytest.approx(
        ref.IEC61094_5_D3_COMBINED_DB, abs=5e-5
    )
    assert budget.expanded_uncertainty_db == pytest.approx(
        ref.IEC61094_5_D3_EXPANDED_DB, abs=5e-4
    )
    assert budget.coverage_factor == 2.0
    gap = budget.combined_uncertainty_db - ref.IEC61094_5_D3_PRINTED_COMBINED_DB
    assert gap > 0.003


def test_d3_linear_and_logarithmic_combination_are_essentially_the_same() -> None:
    """The strict calculation of D.3 is 0,043 614 dB, 0,000 055 dB below the
    root-sum-square in decibels: essentially the same, and not the same.
    """
    budget = _d1_budget()
    assert budget.linear_combined_uncertainty_db == pytest.approx(
        ref.IEC61094_5_D3_LINEAR_COMBINED_DB, abs=1e-6
    )
    assert budget.linear_combined_uncertainty_db < budget.combined_uncertainty_db
    difference = budget.linear_combined_uncertainty_db - budget.combined_uncertainty_db
    assert abs(difference) < 1e-4


def test_budget_takes_quantities_and_additional_components() -> None:
    jig = metrology.jig_diameter_correction([8000.0])
    budget = metrology.comparison_uncertainty_budget(
        {
            "reference": metrology.rectangular(0.0, 0.03),
            "repeatability": 0.02,
        },
        frequency_hz=8000.0,
        additional_components=[
            metrology.Quantity(
                0.0, float(jig.standard_uncertainty_db[0]), name="WS3 diameter"
            )
        ],
    )
    assert budget.names == ("reference", "repeatability", "WS3 diameter")
    assert budget.components[0] == "Sensitivity of reference microphone"
    expected = math.hypot(0.03 / math.sqrt(3.0), 0.02, 0.05 * 0.235)
    assert budget.combined_uncertainty_db == pytest.approx(expected, rel=1e-12)
    assert budget.standard == "IEC 61094-5:2016"


def test_free_field_budget_takes_table_2_keys() -> None:
    budget = metrology.comparison_uncertainty_budget(
        {"reference": 0.1, "free_field": 0.05, "positioning": 0.03},
        frequency_hz=4000.0,
        field="free_field",
    )
    assert budget.names == ("reference", "positioning", "free_field")
    assert budget.standard == "IEC 61094-8:2012"
    assert budget.expanded_uncertainty_db == pytest.approx(
        2.0 * math.sqrt(0.1**2 + 0.05**2 + 0.03**2), rel=1e-12
    )


def test_budget_refuses_a_component_of_the_other_table() -> None:
    components = {"drift": 0.017}
    with pytest.raises(ValueError, match=r"not components of IEC 61094-8"):
        metrology.comparison_uncertainty_budget(
            components, frequency_hz=1000.0, field="free_field"
        )


def test_budget_refuses_an_unnamed_additional_component() -> None:
    extra = [metrology.Quantity(0.0, 0.01)]
    with pytest.raises(ValueError, match=r"needs a name of its own"):
        metrology.comparison_uncertainty_budget(
            {"reference": 0.025}, frequency_hz=1000.0, additional_components=extra
        )


def test_budget_refuses_a_negative_uncertainty() -> None:
    components = {"reference": -0.01}
    with pytest.raises(
        ValueError, match=r"'reference' must be finite and non-negative"
    ):
        metrology.comparison_uncertainty_budget(components, frequency_hz=1000.0)


def test_budget_refuses_no_component() -> None:
    with pytest.raises(ValueError, match=r"at least one component"):
        metrology.comparison_uncertainty_budget({}, frequency_hz=1000.0)


def test_budget_refuses_a_combination_its_columns_do_not_give() -> None:
    budget = _d1_budget()
    wrong = budget.standard_uncertainties_db * 2.0
    with pytest.raises(ValueError, match=r"root-sum-square"):
        dataclasses.replace(budget, standard_uncertainties_db=wrong)


# --------------------------------------------------------------------------
# Annex C and D.2: simultaneous excitation
# --------------------------------------------------------------------------
def test_interchange_cancels_channel_gains_source_drift_and_asymmetry() -> None:
    first, second = _interchange_readings()
    result = metrology.simultaneous_comparison(_F, _L_REF, first, second)
    np.testing.assert_allclose(result.sensitivity_level_db, _L_TEST, atol=1e-12)
    assert result.excitation == "simultaneous"
    assert result.standard == "IEC 61094-5:2016"


def test_d2_in_linear_form_is_the_level_form() -> None:
    """M_test = M_ref R_V / R_P, D.2, against the level model."""
    m_ref = 10.0 ** (_L_REF / 20.0)
    r_v = np.array([3.9, 3.95, 4.0, 4.1, 4.3])
    r_p = np.array([1.001, 1.0, 0.999, 1.002, 1.01])
    first = np.zeros(_F.size)
    second = 2.0 * 20.0 * np.log10(r_v)
    result = metrology.simultaneous_comparison(
        _F,
        _L_REF,
        first,
        second,
        pressure_level_difference_db=20.0 * np.log10(r_p),
    )
    np.testing.assert_allclose(
        result.sensitivity_mv_per_pa, 1000.0 * m_ref * r_v / r_p, rtol=1e-12
    )


def test_repeats_are_averaged_and_counted() -> None:
    first, second = _interchange_readings()
    noise = np.array([[0.004], [-0.002], [-0.002]])
    result = metrology.simultaneous_comparison(
        _F, _L_REF, first + noise, second - noise
    )
    assert result.determinations == 3
    np.testing.assert_allclose(result.sensitivity_level_db, _L_TEST, atol=1e-12)


def test_pressure_calibration_refuses_to_skip_the_interchange() -> None:
    first, _ = _interchange_readings()
    with pytest.raises(ValueError, match=r"IEC 61094-5 5\.1\.2"):
        metrology.simultaneous_comparison(_F, _L_REF, first)


def test_free_field_simultaneous_without_interchange_reads_the_difference() -> None:
    difference = _L_REF - _L_TEST
    result = metrology.simultaneous_comparison(
        _F, _L_REF, difference, field="free_field"
    )
    np.testing.assert_allclose(result.sensitivity_level_db, _L_TEST, atol=1e-12)
    assert result.standard == "IEC 61094-8:2012"


def test_repeats_that_disagree_in_number_are_refused() -> None:
    first, second = _interchange_readings()
    rows_first = np.vstack([first, first])
    rows_second = np.vstack([second, second, second])
    with pytest.raises(ValueError, match=r"same number of determinations"):
        metrology.simultaneous_comparison(_F, _L_REF, rows_first, rows_second)


# --------------------------------------------------------------------------
# Sequential excitation and the monitor microphone
# --------------------------------------------------------------------------
def test_monitor_ratio_cancels_a_drifting_source() -> None:
    """IEC 61094-8 A.2: the quotient of the two ratios to the monitor."""
    field_ref = 94.0 + np.array([0.0, 0.1, -0.1, 0.05, 0.2])
    field_test = field_ref + np.array([0.3, -0.2, 0.15, 0.4, -0.35])
    monitor_gain = -12.5
    result = metrology.sequential_comparison(
        _F,
        _L_REF,
        _L_REF + field_ref,
        _L_TEST + field_test,
        monitor=metrology.MonitorReadings(
            reference_level_db=monitor_gain + field_ref,
            test_level_db=monitor_gain + field_test,
        ),
        field="free_field",
    )
    np.testing.assert_allclose(result.sensitivity_level_db, _L_TEST, atol=1e-12)
    assert result.excitation == "sequential"


def test_without_a_monitor_the_readings_are_differenced() -> None:
    result = metrology.sequential_comparison(_F, _L_REF, _L_REF + 90.0, _L_TEST + 90.0)
    np.testing.assert_allclose(result.sensitivity_level_db, _L_TEST, atol=1e-12)


def test_monitor_levels_disagreeing_in_determinations_are_refused() -> None:
    monitor = metrology.MonitorReadings(
        reference_level_db=np.full((2, _F.size), 80.0),
        test_level_db=np.full((3, _F.size), 80.0),
    )
    with pytest.raises(ValueError, match=r"same number of determinations"):
        metrology.sequential_comparison(
            _F,
            _L_REF,
            _L_REF + 94.0,
            _L_TEST + 94.0,
            monitor=monitor,
        )


# --------------------------------------------------------------------------
# Corrections
# --------------------------------------------------------------------------
def test_environmental_correction_is_first_order_in_each_condition() -> None:
    env = metrology.environmental_sensitivity_correction(
        _F,
        static_pressure_kpa=97.0,
        temperature_c=26.0,
        relative_humidity_percent=40.0,
        static_pressure_coefficient_db_per_kpa=[-0.005, -0.005, -0.006, -0.008, 0.01],
        temperature_coefficient_db_per_k=0.003,
        humidity_coefficient_db_per_percent=0.0001,
    )
    pressure = np.array([-0.005, -0.005, -0.006, -0.008, 0.01]) * (97.0 - 101.325)
    np.testing.assert_allclose(env.static_pressure_term_db, pressure, rtol=1e-12)
    np.testing.assert_allclose(env.temperature_term_db, 0.009, rtol=1e-12)
    np.testing.assert_allclose(env.humidity_term_db, -0.001, rtol=1e-12)
    np.testing.assert_allclose(env.correction_db, pressure + 0.008, rtol=1e-12)
    temperature, pressure_kpa, humidity = ref.IEC61094_REFERENCE_CONDITIONS
    assert env.reference_temperature_c == temperature
    assert env.reference_static_pressure_kpa == pressure_kpa
    assert env.reference_relative_humidity_percent == humidity


def test_environmental_corrections_go_on_the_reference_and_off_the_result() -> None:
    first, second = _interchange_readings()
    reference_env = metrology.environmental_sensitivity_correction(
        _F,
        static_pressure_kpa=99.0,
        temperature_c=21.0,
        relative_humidity_percent=45.0,
        static_pressure_coefficient_db_per_kpa=-0.006,
        temperature_coefficient_db_per_k=0.002,
    )
    test_env = metrology.environmental_sensitivity_correction(
        _F,
        static_pressure_kpa=99.0,
        temperature_c=21.0,
        relative_humidity_percent=45.0,
        static_pressure_coefficient_db_per_kpa=-0.012,
        temperature_coefficient_db_per_k=-0.004,
    )
    result = metrology.simultaneous_comparison(
        _F,
        _L_REF,
        first,
        second,
        reference_environment=reference_env,
        test_environment=test_env,
    )
    expected = _L_TEST + reference_env.correction_db - test_env.correction_db
    np.testing.assert_allclose(result.sensitivity_level_db, expected, atol=1e-12)
    assert tuple(result.corrections_db) == (
        "reference environment",
        "reference conditions",
    )


def test_environmental_correction_at_other_frequencies_is_refused() -> None:
    first, second = _interchange_readings()
    env = metrology.environmental_sensitivity_correction(
        [1000.0, 2000.0],
        static_pressure_kpa=99.0,
        temperature_c=21.0,
        relative_humidity_percent=45.0,
        static_pressure_coefficient_db_per_kpa=-0.006,
        temperature_coefficient_db_per_k=0.002,
    )
    with pytest.raises(ValueError, match=r"'reference_environment' was made at 2"):
        metrology.simultaneous_comparison(
            _F, _L_REF, first, second, reference_environment=env
        )


def _compare(excitation: str, **kwargs: object) -> metrology.ComparisonCalibration:
    """A calibration of the test microphone at ``_F`` by either excitation."""
    if excitation == "simultaneous":
        first, second = _interchange_readings()
        return metrology.simultaneous_comparison(
            _F,
            _L_REF,
            first,
            second,
            **kwargs,  # type: ignore[arg-type]
        )
    return metrology.sequential_comparison(
        _F,
        _L_REF,
        _L_REF + 94.0,
        _L_TEST + 94.0,
        **kwargs,  # type: ignore[arg-type]
    )


@pytest.mark.parametrize("excitation", ["simultaneous", "sequential"])
@pytest.mark.parametrize("name", ["reference_environment", "test_environment"])
def test_environmental_correction_at_as_many_other_frequencies_is_refused(
    excitation: str, name: str
) -> None:
    # As many frequencies as the calibration, one of them different: 10 kHz
    # where the calibration has 8 kHz. A check on the count alone applies the
    # 10 kHz coefficient at 8 kHz and moves the result by 0,5 dB in silence.
    env = metrology.environmental_sensitivity_correction(
        [250.0, 1000.0, 2000.0, 4000.0, 10000.0],
        static_pressure_kpa=96.325,
        temperature_c=23.0,
        relative_humidity_percent=50.0,
        static_pressure_coefficient_db_per_kpa=[-0.005, -0.005, -0.006, -0.008, 0.1],
        temperature_coefficient_db_per_k=0.0,
    )
    with pytest.raises(
        ValueError,
        match=rf"'{name}' was made at 10000 Hz where the calibration has 8000 Hz",
    ):
        _compare(excitation, **{name: env})


def test_environmental_correction_at_the_same_frequencies_is_taken() -> None:
    env = metrology.environmental_sensitivity_correction(
        [250.0, 1000.0, 2000.0, 4000.0, 8000.0],
        static_pressure_kpa=99.0,
        temperature_c=21.0,
        relative_humidity_percent=45.0,
        static_pressure_coefficient_db_per_kpa=-0.006,
        temperature_coefficient_db_per_k=0.002,
    )
    result = _compare("sequential", reference_environment=env)
    np.testing.assert_allclose(
        result.sensitivity_level_db, _L_TEST + env.correction_db, atol=1e-12
    )


#: The nominal one-third-octave midband frequencies from 25 Hz to 20 kHz
#: (IEC 61260-1), and the exact base-ten frequencies they label. The two agree
#: at 100 Hz, 1 kHz and 10 kHz; everywhere else they are between 0.15 % (63,
#: 630 and 6300 Hz) and 0.95 % (160 Hz, 1600 Hz and 16 kHz) apart.
_NOMINAL_THIRDS = (
    25.0, 31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0,
    250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0,
    2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0, 10000.0, 12500.0, 16000.0,
    20000.0,
)  # fmt: skip
_EXACT_THIRDS = metrology.exact_frequencies(25.0, 20000.0, fraction=3)


def test_nominal_and_exact_thirds_are_as_far_apart_as_stated() -> None:
    apart = np.abs(np.asarray(_NOMINAL_THIRDS) / _EXACT_THIRDS - 1.0)
    agree = apart < 1e-12
    closest, widest = np.min(apart[~agree]), np.max(apart)

    def bands(offset: float) -> list[float]:
        return [
            nominal
            for nominal, off in zip(_NOMINAL_THIRDS, apart, strict=True)
            if math.isclose(off, offset, rel_tol=1e-9)
        ]

    assert [f for f, same in zip(_NOMINAL_THIRDS, agree, strict=True) if same] == [
        100.0,
        1000.0,
        10000.0,
    ]
    assert 100.0 * closest == pytest.approx(0.15, abs=0.005)
    assert bands(closest) == [63.0, 630.0, 6300.0]
    assert 100.0 * widest == pytest.approx(0.95, abs=0.005)
    assert bands(widest) == [160.0, 1600.0, 16000.0]


def _environment_at(
    frequencies_hz: np.ndarray,
) -> cc.EnvironmentalSensitivityCorrection:
    return metrology.environmental_sensitivity_correction(
        frequencies_hz,
        static_pressure_kpa=99.0,
        temperature_c=21.0,
        relative_humidity_percent=45.0,
        static_pressure_coefficient_db_per_kpa=-0.006,
        temperature_coefficient_db_per_k=0.002,
    )


def _compare_on_thirds(
    env: cc.EnvironmentalSensitivityCorrection,
) -> metrology.ComparisonCalibration:
    """A calibration at the exact one-third-octave frequencies."""
    level = np.full(_EXACT_THIRDS.size, -38.0)
    return metrology.sequential_comparison(
        _EXACT_THIRDS, level, level + 94.0, level + 106.0, reference_environment=env
    )


@pytest.mark.parametrize(
    "band",
    [
        index
        for index, nominal in enumerate(_NOMINAL_THIRDS)
        if not math.isclose(nominal, _EXACT_THIRDS[index], rel_tol=1e-12)
    ],
    ids=lambda index: f"{_NOMINAL_THIRDS[index]:g}Hz",
)
def test_environmental_correction_at_a_nominal_frequency_is_refused(band: int) -> None:
    # A correction labelled with the nominal 3150 Hz where the calibration is
    # at the exact 3162.28 Hz is 0.4 % off, and 630 Hz against 630.96 Hz only
    # 0.15 %: a tolerance loose enough to let either through applies one
    # frequency's coefficient at another.
    made = _EXACT_THIRDS.copy()
    made[band] = _NOMINAL_THIRDS[band]
    env = _environment_at(made)
    message = re.escape(
        f"'reference_environment' was made at {_NOMINAL_THIRDS[band]:g} Hz "
        f"where the calibration has {_EXACT_THIRDS[band]:g} Hz"
    )
    with pytest.raises(ValueError, match=message):
        _compare_on_thirds(env)


def test_environmental_correction_off_by_rounding_alone_is_taken() -> None:
    # The same exact frequencies after arithmetic that moved them in the last
    # digits are the same frequencies.
    env = _environment_at(_EXACT_THIRDS * (1.0 + 1e-12))
    result = _compare_on_thirds(env)
    np.testing.assert_allclose(
        result.sensitivity_level_db, -26.0 + env.correction_db, atol=1e-12
    )


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("temperature_c", -300.0, r"'temperature_c' must be finite and above"),
        ("temperature_c", -273.15, r"'temperature_c' must be finite and above"),
        (
            "reference_temperature_c",
            -300.0,
            r"'reference_temperature_c' must be finite and above",
        ),
        (
            "relative_humidity_percent",
            150.0,
            r"'relative_humidity_percent' must be between 0 and 100",
        ),
        (
            "relative_humidity_percent",
            -5.0,
            r"'relative_humidity_percent' must be between 0 and 100",
        ),
        (
            "reference_relative_humidity_percent",
            100.5,
            r"'reference_relative_humidity_percent' must be between 0 and 100",
        ),
        (
            "reference_relative_humidity_percent",
            math.nan,
            r"'reference_relative_humidity_percent' must be between 0 and 100",
        ),
    ],
)
def test_environmental_correction_refuses_conditions_that_are_no_state_of_air(
    name: str, value: float, message: str
) -> None:
    conditions: dict[str, float] = {
        "temperature_c": 21.0,
        "relative_humidity_percent": 45.0,
    }
    conditions[name] = value
    with pytest.raises(ValueError, match=message):
        metrology.environmental_sensitivity_correction(
            _F,
            static_pressure_kpa=99.0,
            static_pressure_coefficient_db_per_kpa=-0.006,
            temperature_coefficient_db_per_k=0.002,
            humidity_coefficient_db_per_percent=0.001,
            **conditions,  # type: ignore[arg-type]
        )


def test_environmental_correction_takes_dry_and_saturated_air() -> None:
    env = metrology.environmental_sensitivity_correction(
        _F,
        static_pressure_kpa=101.325,
        temperature_c=23.0,
        relative_humidity_percent=100.0,
        reference_relative_humidity_percent=0.0,
        static_pressure_coefficient_db_per_kpa=0.0,
        temperature_coefficient_db_per_k=0.0,
        humidity_coefficient_db_per_percent=0.001,
    )
    np.testing.assert_allclose(env.correction_db, 0.1, rtol=1e-12)


@pytest.mark.parametrize("excitation", ["simultaneous", "sequential"])
def test_an_unknown_field_is_named_before_the_free_field_difference(
    excitation: str,
) -> None:
    with pytest.raises(ValueError, match=r"'field' must be one of"):
        _compare(excitation, field="freefield", reference_free_field_difference_db=0.1)


def test_free_field_difference_is_added_to_a_pressure_calibrated_reference() -> None:
    difference = np.array([0.0, 0.08, 0.2, 0.85, 2.45])
    result = metrology.sequential_comparison(
        _F,
        _L_REF,
        _L_REF + difference + 94.0,
        _L_TEST + 94.0,
        field="free_field",
        reference_free_field_difference_db=difference,
    )
    np.testing.assert_allclose(result.sensitivity_level_db, _L_TEST, atol=1e-12)


def test_free_field_difference_on_a_pressure_calibration_is_refused() -> None:
    first, second = _interchange_readings()
    with pytest.raises(ValueError, match=r"IEC 61094-8 Table 1"):
        metrology.simultaneous_comparison(
            _F, _L_REF, first, second, reference_free_field_difference_db=0.1
        )


def test_a_correction_named_twice_is_refused() -> None:
    first, second = _interchange_readings()
    env = metrology.environmental_sensitivity_correction(
        _F,
        static_pressure_kpa=99.0,
        temperature_c=21.0,
        relative_humidity_percent=45.0,
        static_pressure_coefficient_db_per_kpa=-0.006,
        temperature_coefficient_db_per_k=0.002,
    )
    named = {"reference environment": 0.01}
    with pytest.raises(ValueError, match=r"repeats the correction"):
        metrology.simultaneous_comparison(
            _F,
            _L_REF,
            first,
            second,
            reference_environment=env,
            corrections_db=named,
        )


def test_jig_correction_reads_table_a1_at_exact_frequencies() -> None:
    exact = 1000.0 * 10.0 ** (np.array([3, 6, 9, 12]) / 10.0)  # 1995 Hz ... 15849 Hz
    jig = metrology.jig_diameter_correction(exact)
    np.testing.assert_allclose(jig.correction_db, [-0.015, -0.059, -0.235, -0.933])
    np.testing.assert_allclose(
        jig.expanded_uncertainty_db,
        ref.IEC61094_5_TABLE_A1_RELATIVE_EXPANDED
        * np.array([0.015, 0.059, 0.235, 0.933]),
    )
    np.testing.assert_allclose(
        jig.standard_uncertainty_db, jig.expanded_uncertainty_db / 2
    )


def test_jig_correction_defaults_to_the_fourteen_rows() -> None:
    jig = metrology.jig_diameter_correction()
    assert jig.frequencies_hz.size == 14
    assert jig.correction_db[-1] == pytest.approx(-1.443, abs=1e-12)


def test_jig_correction_refuses_a_frequency_it_does_not_print() -> None:
    frequencies = [500.0]
    with pytest.raises(ValueError, match=r"not a frequency of IEC 61094-5 Table A.1"):
        metrology.jig_diameter_correction(frequencies)


def test_jig_correction_enters_as_a_named_correction() -> None:
    first, second = _interchange_readings()
    frequencies = np.array([1000.0, 2000.0, 4000.0, 8000.0])
    keep = slice(1, None)
    jig = metrology.jig_diameter_correction(frequencies)
    result = metrology.simultaneous_comparison(
        frequencies,
        _L_REF[keep],
        first[keep],
        second[keep],
        corrections_db={"WS3 in the jig (Table A.1)": jig.correction_db},
    )
    np.testing.assert_allclose(
        result.sensitivity_level_db, _L_TEST[keep] + jig.correction_db, atol=1e-12
    )


# --------------------------------------------------------------------------
# IEC 61094-8 B.1: the effective free-field region
# --------------------------------------------------------------------------
def test_region_major_axis_is_d_plus_tau_c_with_annex_f_air() -> None:
    region = metrology.free_field_region(1.2, 0.004, temperature_c=21.0)
    c = fluids.air(
        temperature_c=21.0, static_pressure_pa=101325.0, relative_humidity_percent=50.0
    ).speed_of_sound
    assert region.speed_of_sound == pytest.approx(c, rel=1e-12)
    assert region.major_axis_m == pytest.approx(1.2 + 0.004 * c, rel=1e-12)
    assert region.rod_clearance_m == pytest.approx(0.004 * c / 2.0, rel=1e-12)


def test_a_reflector_at_the_semi_minor_axis_arrives_at_the_end_of_the_window() -> None:
    """A plane parallel to the axis at distance b reflects by its image source
    along a path of length sqrt(d**2 + 4 b**2), which is A.
    """
    region = metrology.FreeFieldRegion(1.0, 0.005, 343.0)
    b = region.semi_minor_axis_m
    reflected = math.hypot(region.source_distance_m, 2.0 * b)
    assert reflected == pytest.approx(region.major_axis_m, rel=1e-12)
    delay = (reflected - region.source_distance_m) / region.speed_of_sound
    assert delay == pytest.approx(region.window_time_s, rel=1e-12)


def test_region_refuses_a_window_that_is_not_positive() -> None:
    with pytest.raises(ValueError, match=r"window_time_s"):
        metrology.free_field_region(1.0, 0.0)


# --------------------------------------------------------------------------
# The results and their validation
# --------------------------------------------------------------------------
def test_results_publish_read_only_columns() -> None:
    first, second = _interchange_readings()
    result = metrology.simultaneous_comparison(
        _F, _L_REF, first, second, expanded_uncertainty_db=0.09
    )
    for column in (
        result.frequencies_hz,
        result.reference_sensitivity_level_db,
        result.output_level_differences_db,
        result.expanded_uncertainty_db,
    ):
        assert column is not None
        assert not column.flags.writeable
    assert isinstance(result.corrections_db, types.MappingProxyType)
    jig = metrology.jig_diameter_correction()
    assert not jig.correction_db.flags.writeable


def test_calibration_refuses_a_negative_uncertainty() -> None:
    first, second = _interchange_readings()
    with pytest.raises(
        ValueError, match=r"'expanded_uncertainty_db' must be non-negative"
    ):
        metrology.simultaneous_comparison(
            _F, _L_REF, first, second, expanded_uncertainty_db=-0.1
        )


def test_calibration_refuses_an_unknown_field() -> None:
    first, second = _interchange_readings()
    with pytest.raises(ValueError, match=r"'field' must be one of"):
        metrology.simultaneous_comparison(_F, _L_REF, first, second, field="diffuse")


def test_environmental_correction_needs_the_coefficients_of_the_microphone() -> None:
    with pytest.raises(TypeError, match=r"temperature_coefficient_db_per_k"):
        metrology.environmental_sensitivity_correction(  # type: ignore[call-arg]
            _F,
            static_pressure_kpa=99.0,
            temperature_c=21.0,
            relative_humidity_percent=45.0,
            static_pressure_coefficient_db_per_kpa=-0.006,
        )


# --------------------------------------------------------------------------
# IEC 61183 clause 5 computes through the same model
# --------------------------------------------------------------------------
def test_iec61183_diffuse_field_comparison_uses_the_shared_model() -> None:
    assert random_incidence._compared_level_db is cc._compared_level_db
    assert (
        random_incidence._output_level_difference_db is cc._output_level_difference_db
    )
    result = metrology.diffuse_field_sensitivity(
        [1000.0, 2000.0],
        [94.3, 94.6],
        [94.0, 94.1],
        reference_random_incidence_level_db=[-26.0, -26.2],
    )
    expected = metrology.sequential_comparison(
        [1000.0, 2000.0], [-26.0, -26.2], [94.0, 94.1], [94.3, 94.6]
    )
    np.testing.assert_allclose(
        result.diffuse_field_level_db, expected.sensitivity_level_db, atol=1e-12
    )


# --------------------------------------------------------------------------
# What each figure says
# --------------------------------------------------------------------------
def test_calibration_plot_draws_the_band_and_both_levels() -> None:
    first, second = _interchange_readings()
    result = metrology.simultaneous_comparison(
        _F, _L_REF, first, second, expanded_uncertainty_db=0.09
    )
    fig, ax = plt.subplots()
    result.plot(ax)
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels == [
        r"$L_\mathrm{test} \pm U$ ($k$ = 2)",
        r"$L_\mathrm{test}$, microphone under test",
        r"$L_\mathrm{ref}$, reference microphone",
    ]
    assert "IEC 61094-5" in ax.get_title()
    np.testing.assert_allclose(ax.get_lines()[0].get_ydata(), _L_TEST, atol=1e-12)
    plt.close(fig)
    fig, ax = plt.subplots()
    metrology.simultaneous_comparison(
        _F, _L_REF, _L_REF - _L_TEST, field="free_field"
    ).plot(ax, language="es")
    assert ax.get_title() == "Sensibilidad en campo libre por comparación (IEC 61094-8)"
    assert len(ax.collections) == 0
    plt.close(fig)


def test_free_field_plot_draws_the_reference_free_field_level() -> None:
    """Against a pressure-calibrated reference, the dashed curve is the level
    the free field compared the test microphone with: the reference's
    pressure level plus its free-field difference.
    """
    difference = np.array([0.0, 0.05, 0.12, 0.3, 0.7])
    result = metrology.sequential_comparison(
        _F,
        _L_REF,
        _L_REF + difference + 74.0,
        _L_TEST + 74.0,
        field="free_field",
        reference_free_field_difference_db=difference,
    )
    fig, ax = plt.subplots()
    result.plot(ax)
    reference = ax.get_lines()[1]
    np.testing.assert_allclose(reference.get_ydata(), _L_REF + difference, atol=1e-12)
    assert reference.get_label() == "Reference microphone, free-field level"
    plt.close(fig)
    fig, ax = plt.subplots()
    result.plot(ax, language="es")
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels[-1] == "Micrófono de referencia, nivel en campo libre"
    plt.close(fig)


def test_budget_plot_names_the_components_and_the_expanded_uncertainty() -> None:
    fig, ax = plt.subplots()
    _d1_budget().plot(ax)
    ticks = [label.get_text() for label in ax.get_yticklabels()]
    assert ticks[0] == "Reference microphone"
    assert ticks[6] == "Drift of the reference"
    assert "$U$ = 0.087 dB" in ax.get_title()
    assert "Table D.1" in ax.get_title()
    plt.close(fig)
    fig, ax = plt.subplots()
    _d1_budget().plot(ax, language="es")
    assert "$U$ = 0,087 dB" in ax.get_title()
    assert ax.get_yticklabels()[0].get_text() == "Micrófono de referencia"
    plt.close(fig)


def test_environmental_plot_draws_three_terms_and_the_total() -> None:
    env = metrology.environmental_sensitivity_correction(
        _F,
        static_pressure_kpa=97.0,
        temperature_c=26.0,
        relative_humidity_percent=40.0,
        static_pressure_coefficient_db_per_kpa=-0.005,
        temperature_coefficient_db_per_k=0.003,
    )
    fig, ax = plt.subplots()
    env.plot(ax)
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels[-1] == r"$C_\mathrm{env}$, total"
    assert len(labels) == 4
    assert "97.000 kPa" in ax.get_title()
    np.testing.assert_allclose(ax.get_lines()[-1].get_ydata(), env.correction_db)
    plt.close(fig)


def test_jig_plot_draws_the_table_and_its_band() -> None:
    fig, ax = plt.subplots()
    metrology.jig_diameter_correction().plot(ax, language="es")
    assert "tabla A.1" in ax.get_title()
    assert len(ax.collections) == 1
    plt.close(fig)


def test_region_plot_draws_figure_b1() -> None:
    region = metrology.FreeFieldRegion(1.0, 0.005, 343.0)
    fig, ax = plt.subplots()
    region.plot(ax)
    boundary = ax.get_lines()[0]
    x = np.asarray(boundary.get_xdata())
    y = np.asarray(boundary.get_ydata())
    assert x.max() == pytest.approx(region.major_axis_m / 2.0, rel=1e-9)
    assert y.max() == pytest.approx(region.semi_minor_axis_m, rel=1e-3)
    assert "B.1" in ax.get_title()
    plt.close(fig)


@pytest.mark.parametrize("language", ["en", "es"])
def test_region_plot_on_its_own_figure_keeps_its_legend_and_title(
    language: str,
) -> None:
    """Without axes the renderer makes a figure wide enough for the legend
    beside the axes and the two-line title.
    """
    ax = metrology.free_field_region(1.0, 0.005).plot(language=language)
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()  # type: ignore[attr-defined]
    page = fig.bbox
    for artist in (ax.get_legend(), ax.title):
        box = artist.get_window_extent(renderer)
        assert box.x0 >= page.x0
        assert box.x1 <= page.x1
        assert box.y0 >= page.y0
        assert box.y1 <= page.y1
    plt.close(fig)
