#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Corrections for the free-field response of a sound level meter.

IEC 62585:2012 prints two worked uncertainty budgets of a correction measured
with a comparison coupler, at 1 kHz (Table I.2) and at 8 kHz (Table I.3), the
exact one-twelfth-octave frequencies of one decade (Table H.1), and the maximum
expanded uncertainty each of clauses 9 to 14 permits. The rows below
reproduce each from the library, and check the four measurement models
against the text they are derived from: readings built by Formulas (D.1) to
(D.4), (E.1) to (E.3B) and (F.1) to (F.3) from known responses have to give
back the correction those responses define, and the adjustment value of Annex
A has to be the Delta L = L1 - L4 of Figure A.1 for a response whose fit is
known in closed form.

Oracle: BS EN 62585:2012, the English text of EN 62585:2012, which is
IEC 62585:2012 unchanged: clause 6 on printed folio 10 (PDF page 12), clauses
9 to 14 on folios 13 to 16 (PDF pages 15 to 18), Table H.1 on folio 35 (PDF
page 37), Table I.2 on folio 38 (PDF page 40) and Table I.3 on folio 39 (PDF
page 41).

Three printed defects sit in this oracle and are recorded in
``docs/ERRATA.md``. Table I.2 prints k = 2,11 beside its own 29,98 effective
degrees of freedom, for which the Student factor at 95 % is 2,04; the rows pin
the factor and the expanded uncertainty the page's own numbers give. Table H.1 prints the exponent of index
31 as 31/80 beside the value of 10^(31/40). Formulas (E.4) to (E.6) exchange
the two readings in the coupler that Figure E.1 defines, which the derivation
row of Annex E checks with the figure's labels.
"""

from __future__ import annotations

import math

import numpy as np
import reference_data as ref

from phonometry import metrology

from ..registry import Outcome, count, numeric, register

_IEC62585 = "Free-field corrections of a sound level meter (IEC 62585)"

#: Exact base-ten counterparts of the nominal frequencies the maxima name.
_EXACT_OF_NOMINAL = {
    63.0: 63.0957344480193,
    4000.0: 3981.0717055349724,
    5000.0: 5011.872336272725,
    8000.0: 7943.282347242815,
    10000.0: 10000.0,
}

#: A synthetic meter and reference at four frequencies, from which the
#: derivation rows build their readings: the free-field and pressure responses
#: of the meter and of the reference, the free-field level during each of the
#: first two measurements, and the pressure on each on the source.
_F = np.array([125.0, 1000.0, 4000.0, 8000.0])
_SLM_FREE = np.array([0.05, 0.0, -0.4, -1.1])
_SLM_PRESSURE = np.array([0.02, 0.0, -0.9, -2.4])
_RM_FREE = np.array([0.0, 0.08, 0.95, 2.6])
_RM_PRESSURE = np.array([0.0, 0.0, 0.1, 0.2])
_FIELD_1 = 94.0 + np.array([0.0, 0.01, -0.02, 0.03])
_FIELD_2 = 94.0
_ON_SLM = 94.0 + np.array([0.0, 0.02, 0.05, 0.1])
_ON_RM = 94.0


def _budget_i2() -> metrology.CorrectionUncertaintyBudget:
    return metrology.correction_uncertainty_budget(
        ref.IEC62585_TABLE_I2_VALUES_DB,
        repeatability_dof=ref.IEC62585_REPEATABILITY_DOF,
        frequency_hz=1000.0,
    )


def _budget_i3() -> metrology.CorrectionUncertaintyBudget:
    return metrology.correction_uncertainty_budget(
        ref.IEC62585_TABLE_I3_VALUES_DB,
        repeatability_dof=ref.IEC62585_REPEATABILITY_DOF,
        frequency_hz=8000.0,
    )


@register(
    _IEC62585,
    "IEC 62585:2012 Table I.2",
    "Standard uncertainty of each of the 15 components at 1 kHz",
)
def _chk_i2_components() -> Outcome:
    """Each value over its Table I.1 divisor, to the four decimals printed."""
    budget = _budget_i2()
    matching = sum(
        1
        for key, printed in ref.IEC62585_TABLE_I2_STANDARD_DB.items()
        if math.isclose(
            round(
                float(budget.standard_uncertainties_db[budget.descriptors.index(key)]),
                4,
            ),
            printed,
            abs_tol=1e-12,
        )
    )
    return count(
        matching,
        len(ref.IEC62585_TABLE_I2_STANDARD_DB),
        subject="components of Table I.2",
    )


@register(
    _IEC62585,
    "IEC 62585:2012 Table I.2",
    "Combined standard uncertainty of the correction at 1 kHz",
)
def _chk_i2_combined() -> Outcome:
    """The 15 components in quadrature, printed 0,059 0 dB."""
    return numeric(
        ref.IEC62585_TABLE_I2_COMBINED_DB,
        _budget_i2().combined_uncertainty_db,
        0.00005,
        unit="dB",
        places=4,
    )


@register(
    _IEC62585,
    "IEC 62585:2012 Table I.2",
    "Welch-Satterthwaite effective degrees of freedom at 1 kHz",
)
def _chk_i2_dof() -> Outcome:
    """Only the repeatability (a15, 2 degrees of freedom) is finite."""
    return numeric(
        ref.IEC62585_TABLE_I2_EFFECTIVE_DOF,
        _budget_i2().effective_dof,
        0.005,
        places=2,
    )


@register(
    _IEC62585,
    "IEC 62585:2012 Table I.2, clause 5",
    "Coverage factor for 95 % at the 29,98 degrees of freedom the table prints",
)
def _chk_i2_coverage() -> Outcome:
    """The Student factor at the page's own degrees of freedom.

    The table prints k = 2,11, the factor for about 17 degrees of freedom; at
    the 29,98 it prints beside it the factor is 2,04 (docs/ERRATA.md). The
    row pins the value that follows from the page's own numbers.
    """
    return numeric(
        2.04,
        _budget_i2().coverage_factor,
        0.005,
        places=3,
        expected_label="2.04 (printed 2,11, an erratum)",
    )


@register(
    _IEC62585,
    "IEC 62585:2012 Table I.2, clause 5",
    "Expanded uncertainty of the correction at 1 kHz, to the printed guard digit",
)
def _chk_i2_expanded() -> Outcome:
    """2,042 times 0,05903 dB is 0,1206 dB, that is 0,12(1).

    The table prints 0,12(4), which follows from its misprinted k = 2,11
    (docs/ERRATA.md). The row pins the value the page's own numbers give to
    the guard digit the table prints, so it tells the two apart: 2,11 times
    0,05903 dB is 0,1246 dB.
    """
    return numeric(
        ref.IEC62585_TABLE_I2_EXPANDED_DB,
        _budget_i2().expanded_uncertainty_db,
        0.0005,
        unit="dB",
        places=4,
        expected_label="0.121 dB (printed 0,12(4), an erratum)",
    )


@register(
    _IEC62585,
    "IEC 62585:2012 Table I.3",
    "Standard uncertainty of the four components that change at 8 kHz",
)
def _chk_i3_components() -> Outcome:
    """a7, a11, a12 and a15, to the four decimals printed."""
    budget = _budget_i3()
    matching = sum(
        1
        for key, printed in ref.IEC62585_TABLE_I3_STANDARD_DB.items()
        if math.isclose(
            round(
                float(budget.standard_uncertainties_db[budget.descriptors.index(key)]),
                4,
            ),
            printed,
            abs_tol=1e-12,
        )
    )
    return count(
        matching,
        len(ref.IEC62585_TABLE_I3_STANDARD_DB),
        subject="changed components of Table I.3",
    )


@register(
    _IEC62585,
    "IEC 62585:2012 Table I.3",
    "Combined standard uncertainty of the correction at 8 kHz",
)
def _chk_i3_combined() -> Outcome:
    """Printed 0,140 dB."""
    return numeric(
        ref.IEC62585_TABLE_I3_COMBINED_DB,
        _budget_i3().combined_uncertainty_db,
        0.0005,
        unit="dB",
        places=4,
    )


@register(
    _IEC62585,
    "IEC 62585:2012 Table I.3",
    "Coverage factor at 8 kHz, more than 30 effective degrees of freedom",
)
def _chk_i3_coverage() -> Outcome:
    """Printed k = 2; 59 degrees of freedom give 2,001."""
    return numeric(
        ref.IEC62585_TABLE_I3_K, _budget_i3().coverage_factor, 0.005, places=3
    )


@register(
    _IEC62585,
    "IEC 62585:2012 Table I.3",
    "Expanded uncertainty of the correction at 8 kHz",
)
def _chk_i3_expanded() -> Outcome:
    """Printed 0,28 dB."""
    return numeric(
        ref.IEC62585_TABLE_I3_EXPANDED_DB,
        _budget_i3().expanded_uncertainty_db,
        0.005,
        unit="dB",
        places=3,
    )


@register(
    _IEC62585,
    "IEC 62585:2012 Formula (H.1), Table H.1",
    "Exact one-twelfth-octave frequencies from 1 kHz to 10 kHz",
)
def _chk_table_h1() -> Outcome:
    """The 41 values of the decade, to the seven significant digits printed."""
    computed = metrology.exact_frequencies(1000.0, 10000.0)
    printed = ref.IEC62585_TABLE_H1_KHZ
    matching = (
        sum(
            1
            for value, expected in zip(computed / 1000.0, printed, strict=True)
            if math.isclose(round(float(value), 6), expected, abs_tol=1e-12)
        )
        if computed.size == len(printed)
        else 0
    )
    return count(matching, len(printed), subject="frequencies of Table H.1")


@register(
    _IEC62585,
    "IEC 62585:2012 clauses 9 to 14",
    "Maximum permitted expanded uncertainty either side of each boundary",
)
def _chk_maxima() -> Outcome:
    """Each printed maximum at the nominal frequency and its exact one."""
    matching = 0
    for clause, nominal, printed in ref.IEC62585_MAXIMA:
        frequencies = [nominal, _EXACT_OF_NOMINAL[nominal]]
        maxima = metrology.maximum_expanded_uncertainty(frequencies, clause=clause)
        matching += bool(np.allclose(maxima, printed, rtol=0.0, atol=1e-12))
    return count(
        matching, len(ref.IEC62585_MAXIMA), subject="printed maxima of clauses 9 to 14"
    )


@register(
    _IEC62585,
    "IEC 62585:2012 clause 6",
    "Static-pressure component below 97 kPa, up to and above 3 kHz",
)
def _chk_static_pressure() -> Outcome:
    """0,15 dB and 0,25 dB, expanded with k = 2, as the budget states them."""
    matching = 0
    for frequency, expanded in ref.IEC62585_STATIC_PRESSURE_EXPANDED_DB:
        budget = metrology.correction_uncertainty_budget(
            ref.IEC62585_TABLE_I2_VALUES_DB,
            repeatability_dof=ref.IEC62585_REPEATABILITY_DOF,
            frequency_hz=frequency,
            static_pressure_kpa=ref.IEC62585_STATIC_PRESSURE_LIMIT_KPA - 1.0,
        )
        matching += budget.descriptors[-1] == "static pressure" and math.isclose(
            float(budget.values_db[-1]), expanded, abs_tol=1e-12
        )
    return count(
        matching,
        len(ref.IEC62585_STATIC_PRESSURE_EXPANDED_DB),
        subject="clause 6 components",
    )


@register(
    _IEC62585,
    "IEC 62585:2012 Formulas (D.1) to (D.7)",
    "A calibrator's correction from readings built by (D.1) to (D.4)",
)
def _chk_formula_d7() -> Outcome:
    """Formula (D.7) gives back the free-field less the pressure response."""
    result = metrology.sound_calibrator_correction(
        _F,
        _FIELD_1 + _SLM_FREE,
        _FIELD_2 + _RM_FREE,
        _ON_SLM + _SLM_PRESSURE,
        _ON_RM + _RM_PRESSURE,
        reference_free_field_correction_db=_RM_FREE - _RM_PRESSURE,
        free_field_level_difference_db=_FIELD_1 - _FIELD_2,
        calibrator_level_difference_db=_ON_SLM - _ON_RM,
    )
    error = float(np.max(np.abs(result.correction_db - (_SLM_FREE - _SLM_PRESSURE))))
    return numeric(0.0, error, 1e-12, unit="dB", places=12)


@register(
    _IEC62585,
    "IEC 62585:2012 Formulas (E.1) to (E.6), Figure E.1",
    "A coupler's correction from readings built by (E.1) to (E.3B)",
)
def _chk_formula_e6() -> Outcome:
    """With Figure E.1's labels: L_ind3a is the reference, L_ind3b the meter.

    Formula (E.6) as printed exchanges the two and comes out
    2(dL_P,SLM - dL_P,RM) away (docs/ERRATA.md), the deviations of the two
    channels' indications from the coupler level; the library names the
    readings by what each is of.
    """
    result = metrology.comparison_coupler_correction(
        _F,
        _FIELD_1 + _SLM_FREE,
        _FIELD_2 + _RM_FREE,
        _ON_SLM + _SLM_PRESSURE,
        _ON_RM + _RM_PRESSURE,
        reference_free_field_correction_db=_RM_FREE - _RM_PRESSURE,
        free_field_level_difference_db=_FIELD_1 - _FIELD_2,
        coupler_level_difference_db=_ON_SLM - _ON_RM,
    )
    error = float(np.max(np.abs(result.correction_db - (_SLM_FREE - _SLM_PRESSURE))))
    return numeric(0.0, error, 1e-12, unit="dB", places=12)


@register(
    _IEC62585,
    "IEC 62585:2012 Formulas (F.1) to (F.13)",
    "An actuator's normalised correction from readings built by (F.1) to (F.3)",
)
def _chk_formula_f13() -> Outcome:
    """Formula (F.13), each term normalised at 1 kHz by (F.5) to (F.12)."""
    sensitivity = -26.0 + np.array([0.0, 0.0, 0.1, 0.3])
    gain = np.array([0.0, 0.01, 0.02, -0.05])
    actuator = 94.0 + np.array([0.0, 0.0, 0.01, 0.0])
    slm_actuator = np.array([0.1, 0.0, -0.7, -1.9])
    result = metrology.electrostatic_actuator_correction(
        _F,
        _FIELD_1 + _SLM_FREE,
        _FIELD_2 + sensitivity + gain,
        actuator + slm_actuator,
        reference_sensitivity_level_db=sensitivity,
        reference_channel_gain_db=gain,
        actuator_level_db=actuator,
        free_field_level_difference_db=_FIELD_1 - _FIELD_2,
    )
    absolute = _SLM_FREE - slm_actuator
    error = float(np.max(np.abs(result.correction_db - (absolute - absolute[1]))))
    return numeric(0.0, error, 1e-12, unit="dB", places=12)


@register(
    _IEC62585,
    "IEC 62585:2012 Annex A, Figure A.1",
    "Adjustment value of a response whose fit is known in closed form",
)
def _chk_annex_a() -> Outcome:
    """Delta L = L1 - L4, added to what the adjusted meter reads.

    With equal weights the fit moves the sensitivity by minus the mean
    deviation: deviations of +0,2, +0,1 and -0,6 dB give s = +0,1 dB, so a
    meter reading 93,7 dB on a 94,0 dB calibrator before the adjustment reads
    L4 = 93,8 dB after it, and Delta L = +0,2 dB.
    """
    result = metrology.adjustment_value(
        [125.0, 1000.0, 8000.0],
        [94.2, 94.1, 93.4],
        93.7,
        calibrator_level_db=94.0,
    )
    return numeric(
        0.2,
        result.adjustment_db,
        1e-12,
        unit="dB",
        places=3,
        expected_label="0.2 dB (closed form)",
    )
