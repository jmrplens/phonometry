#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Calibration of working standard microphones by comparison.

IEC 61094-5:2016 prints the corrections of a WS3 microphone in the jig of
Figure A.4 (Table A.1) and a worked uncertainty budget at 2 kHz (Table D.1,
combined in D.3); IEC 61094-8:2012 prints the typical expanded uncertainty of
each way of calibrating the reference microphone (Table 1) and the typical
components of a free-field budget (Table 2). The rows below reproduce each from
the library, and check the measurement models against the text they are
derived from: readings built by Formulas (C.1) and (C.2), or by the monitor
ratios of IEC 61094-8 A.2, from known sensitivities, gains and fields have to
give back the sensitivity those quantities define, and the effective
free-field region of Formula (B.1) has to put a reflection from its boundary
at the end of the time window.

Oracle: IEC 61094-5:2016 (Edition 2.0, English-French): Table A.1 on printed
folio 15 (PDF page 17), Annex C on folio 18 (PDF page 20), D.2 on folio 19
(PDF page 21), Table D.1 on folio 20 (PDF page 22) and its continuation and
D.3 on folio 21 (PDF page 23). BS EN 61094-8:2012, the English text of
EN 61094-8:2012 which is IEC 61094-8:2012 unchanged: Table 1 on folio 12 (PDF
page 14), Table 2 on folio 17 (PDF page 19) and B.1 on folio 23 (PDF page 25).

One printed defect sits in this oracle and is recorded in ``docs/ERRATA.md``:
D.3 of IEC 61094-5 states a combined standard uncertainty of 0,040 dB and an
expanded one of 0,08 dB, where the root-sum-square of the eight components
Table D.1 prints is 0,0437 dB and twice it 0,087 dB. The rows pin the values
the page's own components give.
"""

from __future__ import annotations

import math

import numpy as np
import reference_data as ref

from phonometry import metrology

from ..registry import Outcome, count, numeric, register

_IEC61094 = "Microphone calibration by comparison (IEC 61094-5, IEC 61094-8)"

#: A reference and a test microphone, sensitivity levels in dB re 1 V/Pa, at
#: five frequencies, from which the derivation rows build their readings.
_F = np.array([250.0, 1000.0, 2000.0, 4000.0, 8000.0])
_L_REF = np.array([-38.02, -38.00, -37.98, -37.95, -38.10])
_L_TEST = np.array([-26.40, -26.35, -26.30, -26.10, -25.80])


def _budget_d1() -> metrology.ComparisonUncertaintyBudget:
    return metrology.comparison_uncertainty_budget(
        ref.IEC61094_5_TABLE_D1_STANDARD_DB, frequency_hz=2000.0
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 Table D.1",
    "Standard uncertainty at 2 kHz of the 7 components whose row states a value",
)
def _chk_d1_components() -> Outcome:
    """Each semi-range over the square root of 3 and the reference's expanded
    uncertainty over 2, to the three decimals the table prints. The eighth
    row, the repeatability, states no value and prints its standard
    uncertainty alone, so there is nothing to derive it from.
    """
    table = metrology.IEC61094_5_TABLE_D1
    matching = 0
    for key, (stated, divisor) in ref.IEC61094_5_TABLE_D1_STATED.items():
        row = table[key]
        printed = ref.IEC61094_5_TABLE_D1_STANDARD_DB[key]
        if row.stated_db is None or row.divisor is None:
            continue
        if (
            math.isclose(row.stated_db, stated, rel_tol=1e-12)
            and math.isclose(row.divisor, divisor, rel_tol=1e-12)
            and math.isclose(
                round(row.stated_db / row.divisor, 3), printed, abs_tol=1e-12
            )
        ):
            matching += 1
    return count(
        matching,
        len(ref.IEC61094_5_TABLE_D1_STATED),
        subject="components of Table D.1",
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 D.3",
    "Combined standard uncertainty of the example budget at 2 kHz",
)
def _chk_d3_combined() -> Outcome:
    """The root-sum-square of the printed column, 0,043 67 dB.

    D.3 prints 0,040 dB, which is not the root-sum-square of the eight
    components Table D.1 prints (docs/ERRATA.md); the row pins the value the
    page's own components give.
    """
    return numeric(
        ref.IEC61094_5_D3_COMBINED_DB,
        _budget_d1().combined_uncertainty_db,
        0.00005,
        unit="dB",
        places=4,
        expected_label="0.0437 dB (printed 0,040, an erratum)",
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 D.2, D.3",
    "Expanded uncertainty (k = 2) of the example budget at 2 kHz",
)
def _chk_d3_expanded() -> Outcome:
    """Twice 0,043 67 dB is 0,087 dB; D.3 prints 0,08 dB (docs/ERRATA.md)."""
    return numeric(
        ref.IEC61094_5_D3_EXPANDED_DB,
        _budget_d1().expanded_uncertainty_db,
        0.0005,
        unit="dB",
        places=3,
        expected_label="0.087 dB (printed 0,08, an erratum)",
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 D.3",
    "Combined standard uncertainty by the strict calculation in linear form",
)
def _chk_d3_linear() -> Outcome:
    """D.3: "a strict calculation would require each component to be converted
    from logarithmic to linear form before doing the combination but as the
    values are very small, the result would be essentially the same". The
    page prints no value for it; the printed column, each component taken to
    10**(u/20) - 1, combined in quadrature and taken back by 20 lg(1 + r),
    gives 0,043 614 dB, 0,000 055 dB below the combination in decibels.
    """
    return numeric(
        ref.IEC61094_5_D3_LINEAR_COMBINED_DB,
        _budget_d1().linear_combined_uncertainty_db,
        0.000001,
        unit="dB",
        places=6,
        expected_label="0.043614 dB (0.043669 dB in decibels)",
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 Table A.1",
    "Correction of a WS3 microphone against an LS2aP in the jig of Figure A.4, 14 frequencies",
)
def _chk_table_a1() -> Outcome:
    """Each of the 14 corrections from 1 kHz to 20 kHz, to the thousandth of a
    decibel the table prints.
    """
    printed = {1000.0 * khz: value for khz, value in ref.IEC61094_5_TABLE_A1_DB.items()}
    jig = metrology.jig_diameter_correction(list(printed))
    matching = sum(
        1
        for value, computed in zip(printed.values(), jig.correction_db, strict=True)
        if math.isclose(float(computed), value, abs_tol=1e-12)
    )
    return count(matching, len(printed), subject="corrections of Table A.1")


@register(
    _IEC61094,
    "IEC 61094-5:2016 Table A.1 NOTE",
    "Expanded uncertainty of the correction at 20 kHz, a tenth of its value",
)
def _chk_table_a1_uncertainty() -> Outcome:
    """A tenth of 1,443 dB."""
    jig = metrology.jig_diameter_correction([20000.0])
    return numeric(
        ref.IEC61094_5_TABLE_A1_RELATIVE_EXPANDED * 1.443,
        float(jig.expanded_uncertainty_db[0]),
        1e-12,
        unit="dB",
        places=4,
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 Formulas (C.1) to (C.3)",
    "Sensitivity level of the test microphone through the interchange, whatever the channel gains, source drift and field asymmetry",
)
def _chk_annex_c() -> Outcome:
    """Readings built by (C.1) and (C.2) with channel gains of +0,7 dB and
    -1,3 dB, a source 0,3 dB louder after the interchange and a field 0,06 dB
    stronger at position A than at B give back the test microphone's level.
    """
    level_1 = 94.0 + 0.2 * np.log10(_F / 1000.0)
    level_2 = level_1 + 0.3
    gain_1, gain_2, at_a, at_b = 0.7, -1.3, 0.04, -0.02
    first = (_L_REF + gain_1 + level_1 + at_a) - (_L_TEST + gain_2 + level_1 + at_b)
    second = (_L_TEST + gain_1 + level_2 + at_a) - (_L_REF + gain_2 + level_2 + at_b)
    result = metrology.simultaneous_comparison(_F, _L_REF, first, second)
    worst = float(np.max(np.abs(result.sensitivity_level_db - _L_TEST)))
    return numeric(
        0.0,
        worst,
        1e-9,
        unit="dB",
        places=6,
        expected_label="the test microphone's level at all 5 frequencies",
        computed_label=f"max deviation {worst:.9f} dB",
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 D.2",
    "M_test = M_ref x R_V / R_P in linear form against the level form",
)
def _chk_d2() -> Outcome:
    """The sensitivity in mV/Pa from the level model against the product of
    D.2, with R_V from 3,9 to 4,3 and R_P from 0,999 to 1,01.
    """
    m_ref = 10.0 ** (_L_REF / 20.0)
    r_v = np.array([3.9, 3.95, 4.0, 4.1, 4.3])
    r_p = np.array([1.001, 1.0, 0.999, 1.002, 1.01])
    result = metrology.simultaneous_comparison(
        _F,
        _L_REF,
        np.zeros(_F.size),
        2.0 * 20.0 * np.log10(r_v),
        pressure_level_difference_db=20.0 * np.log10(r_p),
    )
    expected = 1000.0 * m_ref * r_v / r_p
    worst = float(np.max(np.abs(result.sensitivity_mv_per_pa / expected - 1.0)))
    return numeric(
        0.0,
        worst,
        1e-12,
        places=12,
        expected_label="M_ref x R_V / R_P at all 5 frequencies",
        computed_label=f"max relative deviation {worst:.12f}",
    )


@register(
    _IEC61094,
    "IEC 61094-8:2012 A.2",
    "Monitor ratios cancel a source that drifts between the two measurements",
)
def _chk_monitor() -> Outcome:
    """The field changes by up to 0,4 dB between the reference and the test
    microphone; the quotient of the two ratios to the monitor gives the test
    microphone's level regardless.
    """
    field_ref = 94.0 + np.array([0.0, 0.1, -0.1, 0.05, 0.2])
    field_test = field_ref + np.array([0.3, -0.2, 0.15, 0.4, -0.35])
    result = metrology.sequential_comparison(
        _F,
        _L_REF,
        _L_REF + field_ref,
        _L_TEST + field_test,
        reference_monitor_level_db=field_ref - 12.5,
        test_monitor_level_db=field_test - 12.5,
        field="free_field",
    )
    worst = float(np.max(np.abs(result.sensitivity_level_db - _L_TEST)))
    return numeric(
        0.0,
        worst,
        1e-9,
        unit="dB",
        places=6,
        expected_label="the test microphone's level at all 5 frequencies",
        computed_label=f"max deviation {worst:.9f} dB",
    )


@register(
    _IEC61094,
    "IEC 61094-8:2012 Table 1",
    "Typical expanded uncertainty of the 5 reference calibration options at 1 kHz and 10 kHz",
)
def _chk_table_1() -> Outcome:
    """Ten cells, from 0,10 dB for primary free-field reciprocity at 10 kHz to
    0,6 dB for an electrostatic actuator, each counted only on the row whose
    microphone type, method and references are the printed ones.
    """
    matching = 0
    for key, (at_1k, at_10k) in ref.IEC61094_8_TABLE_1_DB.items():
        row = metrology.IEC61094_8_TABLE_1[key]
        if (row.microphone_types, row.method, row.references) != (
            ref.IEC61094_8_TABLE_1_TEXT[key]
        ):
            continue
        matching += math.isclose(row.expanded_uncertainty_1khz_db, at_1k)
        matching += math.isclose(row.expanded_uncertainty_10khz_db, at_10k)
    return count(
        matching, 2 * len(ref.IEC61094_8_TABLE_1_DB), subject="cells of Table 1"
    )


@register(
    _IEC61094,
    "IEC 61094-8:2012 Table 2",
    "Source of uncertainty and subclause references of the 12 typical components",
)
def _chk_table_2() -> Outcome:
    """Each component as printed and the subclauses the table refers it to."""
    matching = sum(
        1
        for key, subclauses in ref.IEC61094_8_TABLE_2_SUBCLAUSES.items()
        if metrology.IEC61094_8_TABLE_2[key].subclauses == subclauses
        and metrology.IEC61094_8_TABLE_2[key].component
        == ref.IEC61094_8_TABLE_2_SOURCES[key]
    )
    return count(
        matching, len(ref.IEC61094_8_TABLE_2_SUBCLAUSES), subject="rows of Table 2"
    )


@register(
    _IEC61094,
    "IEC 61094-8:2012 Formula (B.1), Figure B.1",
    "A reflection from the boundary of the effective free-field region arrives at the end of a 5 ms window",
)
def _chk_region() -> Outcome:
    """A plane parallel to the axis at the semi-minor axis of the spheroid
    reflects along the image path sqrt(d**2 + 4 b**2), which is A = d + tau c,
    so its reflection arrives tau after the direct sound, at 1 m and 23 °C.
    """
    region = metrology.free_field_region(1.0, 0.005)
    reflected = math.hypot(region.source_distance_m, 2.0 * region.semi_minor_axis_m)
    delay_ms = 1000.0 * (reflected - region.source_distance_m) / region.speed_of_sound
    return numeric(5.0, delay_ms, 1e-9, unit="ms", places=6)
