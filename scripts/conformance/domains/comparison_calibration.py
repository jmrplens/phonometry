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

The phase of the sensitivity (IEC 61094-5 5.1.1, IEC 61094-8 5.1), the
effect of different acoustic impedances (IEC 61094-5 7.4 and 7.5) and the
time-selective processing of IEC 61094-8 Annex B print no worked example:
their rows check the phase form of (C.1) to (C.3) and of the monitor ratios,
the circuits of IEC 61094-2 Formula (3) and of the "Microphone impedance"
row of Table D.1, with the lumped impedance of IEC 61094-2 E.4 and the
equivalent volume of IEC 61094-1 6.2.2 (its kappa_r of 1,40) evaluated
independently of the ``ReciprocityMicrophone`` the volumes come from, and
the data simulated with and without a reflection that 8.6 suggests. Formula
(B.10), the 120 Hz and 8 ms and the 30 Hz of B.2.2, the order of magnitude
of B.6.1 and the 0,005 dB semi-range of the impedance row are the printed
numbers they are anchored on.

Two parts of IEC 61094-5 send the reader to the literature, and the rows
follow the literature to its printed numbers. 6.5 refers microphones of
different diameters to its reference [1], Barham, Barrera-Figueroa and
Avison, Metrologia 51 (2014) 129, whose model, with the inputs of its
Table 1, is the origin of Table A.1: the rows reproduce every row of the
table from those inputs, and check that the correction at twice the
separation, the change A.2 names, is the model at twice the distance, with
that change reported beside the approximately 10 % A.2 observed. The
"Microphone impedance"
row of Table D.1 and 7.4 refer the air between two microphones to its
reference [2], Jarvis, NPL Report CIRA(EXT) 010 (1996), whose Appendix B
prints a circuit, its parameters, the volume of its coupler and two graphs
of the error it causes: the rows check the series impedance against the
printed ratio, the volume, and the extremes and the ends of the graphs. 6.7
prints no criterion for the validation of a jig or a coupler; its row checks
the library's reading, agreement within the root-sum-square of the two
expanded uncertainties, on its own definition, with the validation on a grid
of its own. Two calibrations that share a component are correlated through
it, and the GUM prints what that does: the covariance of two estimates of a
common quantity (F.1.2.3, Formula (F.2)) and, for items calibrated against
the same standard, the correlation coefficients of its Example 2, which the
rows reproduce; with the budget of Table D.1 the reference's row cancels in
the difference of two calibrations against the same LS2P.

Oracle: IEC 61094-5:2016 (Edition 2.0, English-French): Table A.1 on printed
folio 15 (PDF page 17), Annex C on folio 18 (PDF page 20), D.2 on folio 19
(PDF page 21), Table D.1 on folio 20 (PDF page 22) and its continuation and
D.3 on folio 21 (PDF page 23). BS EN 61094-8:2012, the English text of
EN 61094-8:2012 which is IEC 61094-8:2012 unchanged: Table 1 on folio 12 (PDF
page 14), Table 2 on folio 17 (PDF page 19), B.1 on folio 23 (PDF page 25),
B.2 on folios 24 and 25 (PDF pages 26 and 27) and B.6 on folio 28 (PDF page
30). BS EN 61094-2:2009 Formula (3) on folio 10 (PDF page 12) and E.4 on folio
35 (PDF page 37); BS EN 61094-1:2001 6.2.2 on page 9 (PDF page 11). 6.5
of IEC 61094-5 on folios 9 and 10 (PDF pages 11 and 12), 6.7 on folio 10
(PDF page 12), A.2 on folio 14 (PDF page 16). Barham et al. (2014): Formulas (1) to (5) and Tables 1 and 2 on page
135 (PDF page 8 of the IOPscience download). Jarvis (1996): Appendix B on
folios 25 to 27 (PDF pages 28 to 30 of the NPL scan). ISO/IEC Guide 98-3:2008
(JCGM 100:2008): 5.2.2 on page 21 (PDF page 33), F.1.2.3 and Formula (F.2)
on page 62 (PDF page 74) and its Example 2 on page 63 (PDF page 75).

Six printed defects sit in this oracle and are recorded in
``docs/ERRATA.md``. D.3 of IEC 61094-5 states a combined standard uncertainty
of 0,040 dB and an expanded one of 0,08 dB, where the root-sum-square of the
eight components Table D.1 prints is 0,0437 dB and twice it 0,087 dB, and the
rows pin the values the page's own components give. B.2.1 of IEC 61094-8, on
folio 25, refers to "Equation B.2" for a requirement on the frequency range
that only (B.3), the integral over frequency, carries, and says the frequency
increment "will determine the time domain resolution" where B.2.2 on the same
page has it set the length of the impulse response; the rows use (B.3) and
the length, 1/Δf, as B.2.2 does. Formula (B.10) is the spectrum of a pulse of
duration 2b where the text calls b the duration, and the rows follow the
formula and its first zero. Formulas (1) to (5) of Barham et al. (2014), with
the inputs of its Table 1, do not give its Table 2: the rows read the radial
sensitivity of Formula (4) less 1 and the annulus of Formula (2) from the
overall radius, which give it. In the published scan of Appendix B of
Jarvis (1996) the mass term of the first microphone has lost its imaginary
unit; the rows give it one, as the second microphone's has and as the
printed graphs need.
"""

from __future__ import annotations

import math

import numpy as np
import reference_data as ref

from phonometry import metrology
from phonometry.fluids import Fluid
from phonometry.metrology import comparison_calibration as cc

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


def _ws3_model(
    frequencies: list[float], gas: Fluid | None = None
) -> metrology.DiameterSoundFieldCorrection:
    """The model of [1] with Barham et al. (2014) Table 1, in the units the
    library takes, at the reference air of clause 4 or in the gas given.
    """
    table = ref.BARHAM_2014_TABLE_1
    return metrology.diameter_sound_field_correction(
        frequencies,
        reference_radius_m=table["ls2_front_cavity_radius_mm"] / 1000.0,
        test_diaphragm_radius_m=table["ws3_diaphragm_radius_mm"] / 1000.0,
        test_outer_radius_m=table["ws3_overall_radius_mm"] / 1000.0,
        separation_m=table["diaphragm_separation_mm"] / 1000.0,
        reference_resonance_frequency_hz=1000.0 * table["ls2_resonance_frequency_khz"],
        test_resonance_frequency_hz=1000.0 * table["ws3_resonance_frequency_khz"],
        gas=gas,
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 6.5, Table A.1; Barham et al. (2014) Formulas (1) to (5), Tables 1 and 2",
    "Correction of a WS3 microphone by the model of [1] from the inputs of its Table 1, 14 frequencies",
)
def _chk_diameter_model_table_a1() -> Outcome:
    """6.5 refers microphones of different diameters to "a theoretical model
    [...] given in the literature (for example [1])", from which Table A.1
    was calculated: Table 2 of [1] prints the same column "calculated with
    input data from table 1". The model with those inputs, at 344,8 m/s
    (the paper prints no speed of sound), to the thousandth of a decibel the
    tables print. It is the model read with the radial sensitivity of
    Formula (4) less 1 and the annulus of Formula (2) from the overall
    radius; as printed it does not give the table (docs/ERRATA.md).
    """
    printed = {1000.0 * khz: value for khz, value in ref.IEC61094_5_TABLE_A1_DB.items()}
    gas = Fluid(
        temperature_c=21.0,
        static_pressure_pa=101325.0,
        composition={},
        model="the speed of sound of the reproduction",
        validity="this row",
        properties={"speed_of_sound": ref.BARHAM_2014_SPEED_OF_SOUND},
    )
    result = _ws3_model(list(printed), gas=gas)
    matching = sum(
        1
        for value, computed in zip(printed.values(), result.correction_db, strict=True)
        if abs(float(computed) - value) <= 0.0005
    )
    return count(matching, len(printed), subject="corrections of Table A.1")


@register(
    _IEC61094,
    "IEC 61094-5:2016 6.5, Table A.1 and its NOTE; Barham et al. (2014) Table 1",
    "Largest deviation of the model at the reference air of clause 4 from Table A.1, against a tenth of the 10 % its NOTE allows",
)
def _chk_diameter_model_reference_air() -> Outcome:
    """At 23,0 °C, 101,325 kPa and 50 % the speed of sound of the
    IEC 61094-2 Annex F air is 345,87 m/s; the model is then within
    0,0093 dB of every row of Table A.1, at 20 kHz, inside 0,014 dB, a tenth
    of the expanded uncertainty the NOTE gives the largest correction.
    """
    printed = {1000.0 * khz: value for khz, value in ref.IEC61094_5_TABLE_A1_DB.items()}
    result = _ws3_model(list(printed))
    worst = float(
        np.max(
            np.abs(np.asarray(result.correction_db) - np.array(list(printed.values())))
        )
    )
    limit = 0.1 * ref.IEC61094_5_TABLE_A1_RELATIVE_EXPANDED * 1.443
    return numeric(
        0.0,
        worst,
        limit,
        unit="dB",
        places=4,
        expected_label="Table A.1, within 0.0144 dB (a tenth of 10 % of 1.443 dB)",
        computed_label=f"max deviation {worst:.4f} dB",
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 A.2, Table A.1 NOTE; Barham et al. (2014) Formulas (1) to (5)",
    "Correction at twice the separation, the change A.2 names, against the model evaluated at twice the distance, 14 frequencies",
)
def _chk_diameter_doubling() -> Outcome:
    """A.2: "The expanded uncertainty on the corrections is estimated to be
    10 % of their value (in dB) which is approximately the change observed
    by doubling the distance between the microphones." The correction the
    result carries at twice the separation has to be the model evaluated at
    1,0 mm, to the rounding of the arithmetic. The change it gives is
    reported beside A.2's figure, not judged against it: A.2's 10 % is a
    change observed, approximately, and by the model the change is 5,4 % to
    6,3 % of each correction, of that order and smaller.
    """
    printed = {1000.0 * khz: value for khz, value in ref.IEC61094_5_TABLE_A1_DB.items()}
    frequencies = list(printed)
    result = _ws3_model(frequencies)
    table = ref.BARHAM_2014_TABLE_1
    doubled = metrology.diameter_sound_field_correction(
        frequencies,
        reference_radius_m=table["ls2_front_cavity_radius_mm"] / 1000.0,
        test_diaphragm_radius_m=table["ws3_diaphragm_radius_mm"] / 1000.0,
        test_outer_radius_m=table["ws3_overall_radius_mm"] / 1000.0,
        separation_m=2.0 * table["diaphragm_separation_mm"] / 1000.0,
        reference_resonance_frequency_hz=1000.0 * table["ls2_resonance_frequency_khz"],
        test_resonance_frequency_hz=1000.0 * table["ws3_resonance_frequency_khz"],
    )
    worst = float(
        np.max(
            np.abs(
                np.asarray(result.doubled_separation_correction_db)
                - np.asarray(doubled.correction_db)
            )
        )
    )
    share = np.asarray(result.separation_change_db) / np.abs(result.correction_db)
    observed = 100.0 * ref.IEC61094_5_TABLE_A1_RELATIVE_EXPANDED
    return numeric(
        0.0,
        worst,
        1e-12,
        unit="dB",
        places=12,
        expected_label="the model at L = 1.0 mm, every row",
        computed_label=(
            f"max deviation {worst:.12f} dB; the change is {100.0 * share.min():.1f} % "
            f"to {100.0 * share.max():.1f} % of each correction, where A.2 observed "
            f"approximately {observed:g} %"
        ),
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
        monitor=metrology.MonitorReadings(
            reference_level_db=field_ref - 12.5,
            test_level_db=field_test - 12.5,
        ),
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


# ---------------------------------------------------------------------------
# The phase of the sensitivity (IEC 61094-5 5.1.1, IEC 61094-8 5.1)
# ---------------------------------------------------------------------------

#: The phases of the reference and the test microphone, in degrees, at the
#: five frequencies of the derivation rows.
_PHI_REF = np.array([-0.4, -1.5, -3.1, -6.4, -14.0])
_PHI_TEST = np.array([-0.9, -2.8, -5.7, -11.9, -25.5])


@register(
    _IEC61094,
    "IEC 61094-5:2016 5.1.1, Formulas (C.1) to (C.3)",
    "Phase of the test microphone through the interchange, whatever the channel phase shifts (one inverting) and field asymmetry",
)
def _chk_annex_c_phase() -> Outcome:
    """The phase form of (C.1) and (C.2): channels shifting by +4° and -7°, a
    source 65° later after the interchange and a field 2° later at position
    A than at B give back the test microphone's phase; so do channels
    shifting by 180° and 0°, whose readings, reported within ±180°, fall
    either side of half a turn and differ by more than it. Neither part
    prints the phase form; the sensitivity "(both modulus and phase)" of
    5.1.1 is the complex ratio (C.3) is written for.
    """
    at_a, at_b = 1.5, -0.5
    source_1, source_2 = 25.0, -40.0
    worst = 0.0
    for shift_1, shift_2 in ((4.0, -7.0), (180.0, 0.0)):
        first = cc._wrapped_deg(
            (_PHI_REF + shift_1 + source_1 + at_a)
            - (_PHI_TEST + shift_2 + source_1 + at_b)
        )
        second = cc._wrapped_deg(
            (_PHI_TEST + shift_1 + source_2 + at_a)
            - (_PHI_REF + shift_2 + source_2 + at_b)
        )
        result = metrology.simultaneous_comparison(
            _F,
            _L_REF,
            _L_REF - _L_TEST,
            _L_TEST - _L_REF,
            phase=metrology.SimultaneousComparisonPhase(
                reference_sensitivity_phase_deg=_PHI_REF,
                channel_phase_difference_deg=first,
                interchanged_channel_phase_difference_deg=second,
            ),
        )
        phase = np.asarray(result.sensitivity_phase_deg, dtype=np.float64)
        worst = max(worst, float(np.max(np.abs(phase - _PHI_TEST))))
    return numeric(
        0.0,
        worst,
        1e-9,
        unit="deg",
        places=6,
        expected_label="the test microphone's phase at all 5 frequencies, both channel pairs",
        computed_label=f"max deviation {worst:.9f} deg",
    )


@register(
    _IEC61094,
    "IEC 61094-8:2012 5.1, A.2",
    "Monitor phases cancel a source that drifts in phase between the two measurements",
)
def _chk_monitor_phase() -> Outcome:
    """The quotient of the two ratios to the monitor written for the phases:
    a source whose phase moves by up to 20° between the reference and the
    test microphone gives the test microphone's phase regardless.
    """
    field_1 = np.array([10.0, 20.0, -30.0, 45.0, 90.0])
    field_2 = field_1 + np.array([3.0, -5.0, 8.0, 12.0, -20.0])
    result = metrology.sequential_comparison(
        _F,
        _L_REF,
        _L_REF + 94.0,
        _L_TEST + 94.0,
        monitor=metrology.MonitorReadings(
            reference_level_db=94.0 - 12.5,
            test_level_db=94.0 - 12.5,
            reference_phase_deg=50.0 + field_1,
            test_phase_deg=50.0 + field_2,
        ),
        field="free_field",
        phase=metrology.SequentialComparisonPhase(
            reference_sensitivity_phase_deg=_PHI_REF,
            reference_output_phase_deg=_PHI_REF + field_1,
            test_output_phase_deg=_PHI_TEST + field_2,
        ),
    )
    phase = np.asarray(result.sensitivity_phase_deg, dtype=np.float64)
    worst = float(np.max(np.abs(phase - _PHI_TEST)))
    return numeric(
        0.0,
        worst,
        1e-9,
        unit="deg",
        places=6,
        expected_label="the test microphone's phase at all 5 frequencies",
        computed_label=f"max deviation {worst:.9f} deg",
    )


# ---------------------------------------------------------------------------
# Different acoustic impedances (IEC 61094-5 7.4, 7.5)
# ---------------------------------------------------------------------------

#: One-third octaves from 1 kHz to 20 kHz.
_F_HIGH = np.array([1000.0, 2000.0, 4000.0, 8000.0, 10000.0, 16000.0, 20000.0])


def _microphone(
    volume_m3: float, resonance_hz: float, loss: float
) -> metrology.ReciprocityMicrophone:
    """A microphone of the lumped impedance of IEC 61094-2 E.4, by the model
    the reciprocity calibration owns. Its front cavity, that of an LS2aP in
    Table C.1, does not enter the equivalent volume.
    """
    _, b, _, d, _, _ = ref.IEC61094_2_TABLE_C1_MM["LS2aP"]
    return metrology.ReciprocityMicrophone(
        equivalent_volume_m3=volume_m3,
        resonance_frequency_hz=resonance_hz,
        loss_factor=loss,
        front_cavity_volume_m3=34e-9,
        front_cavity_depth_m=d / 1000.0,
        front_cavity_diameter_m=b / 1000.0,
    )


def _lumped_volume(volume_m3: float, resonance_hz: float, loss: float) -> np.ndarray:
    return _microphone(volume_m3, resonance_hz, loss).complex_equivalent_volume_m3(
        _F_HIGH
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 Table D.1 (Microphone impedance)",
    "A semi-range of 0,005 dB of the impedance effect as a standard uncertainty",
)
def _chk_impedance_semi_range() -> Outcome:
    """Table D.1: "At 2 kHz, the semi-range of this component is 0,005 dB
    with a rectangular distribution. This is equivalent to a standard
    uncertainty of 0,005/sqrt(3) dB = 0,003 dB": a pressure ratio of
    0,005 dB, as the library carries it, to the three decimals printed.
    """
    stated, divisor = ref.IEC61094_5_TABLE_D1_STATED["impedance"]
    ratio = cc.ImpedancePressureRatio(
        frequencies_hz=np.array([2000.0]),
        ratio=np.array([10.0 ** (stated / 20.0)]),
        coupling="series",
        coupling_equivalent_volume_m3=np.array([1e-6]),
    )
    computed = float(ratio.standard_uncertainty_db[0])
    return numeric(
        ref.IEC61094_5_TABLE_D1_STANDARD_DB["impedance"],
        round(computed, 3),
        1e-12,
        unit="dB",
        places=3,
        expected_label=f"0.003 dB ({stated:g}/{divisor:.4f}, printed)",
    )


@register(
    _IEC61094,
    "IEC 61094-2:2009 Formula (3); IEC 61094-5:2016 7.4",
    "Pressure ratio of a substitution in a closed coupler against the admittance sums of Formula (3), 7 frequencies",
)
def _chk_coupler_ratio() -> Outcome:
    """A WS2F-like microphone of 30 mm³, 16 kHz and loss factor 0,5 takes the
    place of an LS2P-like one of 10 mm³, 22 kHz and 1,1 in a coupler whose
    gas and monitor load it with 458 mm³: the ratio of the pressures is the
    ratio of the two sums of Formula (3), with each equivalent volume turned
    into an impedance by IEC 61094-1 6.2.2 and the lumped parameters of
    IEC 61094-2 E.4 evaluated here independently. Every frequency lies below
    1,3 times both resonances, the range E.4 finds the representation "of
    sufficient accuracy" in.
    """
    kappa_p = ref.IEC61094_1_KAPPA_REFERENCE * 101325.0
    omega = 2.0 * np.pi * _F_HIGH

    def impedance(volume: float, resonance: float, loss: float) -> np.ndarray:
        compliance = volume / kappa_p
        mass = 1.0 / ((2.0 * np.pi * resonance) ** 2 * compliance)
        resistance = loss / (2.0 * np.pi * resonance * compliance)
        reactance = omega * mass - 1.0 / (omega * compliance)
        return np.asarray(resistance + 1j * reactance, dtype=np.complex128)

    load = 458e-9
    gas = 1j * omega * load / kappa_p
    expected = (gas + 1.0 / impedance(10e-9, 22000.0, 1.1)) / (
        gas + 1.0 / impedance(30e-9, 16000.0, 0.5)
    )
    result = metrology.impedance_pressure_ratio(
        _F_HIGH,
        reference_equivalent_volume_m3=_lumped_volume(10e-9, 22000.0, 1.1),
        test_equivalent_volume_m3=_lumped_volume(30e-9, 16000.0, 0.5),
        coupling_equivalent_volume_m3=load,
    )
    worst = float(np.max(np.abs(np.asarray(result.ratio) / expected - 1.0)))
    return numeric(
        0.0,
        worst,
        1e-12,
        places=12,
        expected_label="the ratio of the two sums of Formula (3) at all 7 frequencies",
        computed_label=f"max relative deviation {worst:.12f}",
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 Table D.1 (Microphone impedance), 7.4",
    "Pressure on each microphone behind the air between them, in series, 7 frequencies",
)
def _chk_series_ratio() -> Outcome:
    """Table D.1: "The acoustical impedance of the microphone acts in series
    with that of the air in the space between the two microphones", and the
    microphones "therefore see slightly different pressures"; read as a
    divider, which the row does not print, each diaphragm takes
    p0 Z_a/(Z_a + Z_x), and the ratio of the two is the library's, for an
    air mass of 40 kg/m⁴ with 0,2 MPa·s/m³ of loss.
    """
    kappa_p = ref.IEC61094_1_KAPPA_REFERENCE * 101325.0
    omega = 2.0 * np.pi * _F_HIGH
    reference = _lumped_volume(10e-9, 22000.0, 1.1)
    test = _lumped_volume(25e-9, 16000.0, 0.8)
    series = 2.0e5 + 1j * omega * 40.0
    z_ref = kappa_p / (1j * omega * reference)
    z_test = kappa_p / (1j * omega * test)
    expected = (z_test / (z_test + series)) / (z_ref / (z_ref + series))
    result = metrology.impedance_pressure_ratio(
        _F_HIGH,
        reference_equivalent_volume_m3=reference,
        test_equivalent_volume_m3=test,
        coupling_impedance_pa_s_m3=series,
    )
    worst = float(np.max(np.abs(np.asarray(result.ratio) / expected - 1.0)))
    return numeric(
        0.0,
        worst,
        1e-12,
        places=12,
        expected_label="p0 Z_a/(Z_a + Z_x) for each microphone, at all 7 frequencies",
        computed_label=f"max relative deviation {worst:.12f}",
    )


@register(
    _IEC61094,
    "IEC 61094-2:2009 E.4; IEC 61094-1:2000 6.2.2",
    "Lumped equivalent volume: no imaginary impedance at the resonance, and the loss factor r_a 2 pi f0 c_a",
)
def _chk_lumped_volume() -> Outcome:
    """E.4: "The resonance frequency is the frequency at which the imaginary
    part of the acoustic impedance Z_a is zero", and d = r_a 2 pi f0 c_a with
    V_eq = c_a kappa_r p_s,r; the equivalent volume a ReciprocityMicrophone
    gives at the resonance, turned into Z_a by 6.2.2 with its kappa_r = 1,40,
    has to show both, for 10 mm³, 22 kHz and d = 1,1.
    """
    kappa_p = ref.IEC61094_1_KAPPA_REFERENCE * 101325.0
    resonance, loss = 22000.0, 1.1
    volume = _microphone(10e-9, resonance, loss).complex_equivalent_volume_m3(
        [resonance]
    )[0]
    impedance = kappa_p / (1j * 2.0 * np.pi * resonance * volume)
    compliance = 10e-9 / kappa_p
    matching = int(abs(impedance.imag) <= 1e-9 * abs(impedance.real))
    matching += int(
        math.isclose(impedance.real * 2.0 * np.pi * resonance * compliance, loss)
    )
    return count(matching, 2, subject="relations of E.4")


def _jarvis_impedance(
    omega: np.ndarray, parameters: tuple[float, float, float]
) -> np.ndarray:
    """Z_m = r + i w m + 1/(i w c), Appendix B, folio 25, with the imaginary
    unit on the mass term of both microphones (docs/ERRATA.md).
    """
    resistance, compliance, mass = parameters
    return np.asarray(
        resistance + 1j * omega * mass + 1.0 / (1j * omega * compliance),
        dtype=np.complex128,
    )


def _jarvis_library_ratio(frequencies: np.ndarray) -> np.ndarray:
    """P_test/P_ref through the library: the series impedance of the air and
    the divider of impedance_pressure_ratio, the LS2P the reference.
    """
    density, kappa, pressure = ref.JARVIS_1996_AIR
    length, radius = ref.JARVIS_1996_TUBE
    gas = Fluid(
        temperature_c=23.0,
        static_pressure_pa=pressure,
        composition={},
        model="Jarvis (1996) Appendix B",
        validity="this row",
        properties={"density": density, "heat_capacity_ratio": kappa},
    )
    omega = 2.0 * np.pi * frequencies
    kappa_p = ref.IEC61094_1_KAPPA_REFERENCE * 101325.0
    series = metrology.air_gap_series_impedance_pa_s_m3(
        frequencies, gap_length_m=length, gap_radius_m=radius, gas=gas
    )
    result = metrology.impedance_pressure_ratio(
        frequencies,
        reference_equivalent_volume_m3=kappa_p
        / (1j * omega * _jarvis_impedance(omega, ref.JARVIS_1996_LS2P)),
        test_equivalent_volume_m3=kappa_p
        / (1j * omega * _jarvis_impedance(omega, ref.JARVIS_1996_WS2P)),
        coupling_impedance_pa_s_m3=series,
    )
    return np.asarray(result.ratio, dtype=np.complex128)


#: Appendix B, folio 27: "f = 100, 200 .. 20000 Hz".
_F_JARVIS = np.arange(100.0, 20000.0 + 50.0, 100.0)


@register(
    _IEC61094,
    "IEC 61094-5:2016 Table D.1 (Microphone impedance), 7.4; Jarvis (1996) NPL CIRA(EXT) 010 Appendix B",
    "Ratio of the pressures on an LS2P and a high sensitivity WS2P in the coupler of [2], against the ladder it prints, 200 frequencies",
)
def _chk_jarvis_ratio() -> Outcome:
    """Appendix B, folio 26: R = Z_s1 Z_m1 Z_o2 (Z_L + Z_m2) /
    (Z_o1 (Z_L + Z_m1) Z_s2 Z_m2) with Z_s = Z_c (Z_L + Z_m)/(Z_c + Z_L +
    Z_m), Z_o = Z_L + Z_s, Z_c = kappa p0/(i w v/2) and Z_L = (rho (L/4)/(pi
    r^2)) i w/3, evaluated here as printed with the values of folio 25, is
    P1/P2, the reciprocal of the library's R_P for the WS2P re the LS2P.
    """
    density, kappa, pressure = ref.JARVIS_1996_AIR
    length, radius = ref.JARVIS_1996_TUBE
    omega = 2.0 * np.pi * _F_JARVIS
    volume = math.pi * radius**2 * length
    zc = kappa * pressure / (1j * omega * volume / 2.0)
    zl = (density * (length / 4.0) / (math.pi * radius**2)) * 1j * omega / 3.0
    zm1 = _jarvis_impedance(omega, ref.JARVIS_1996_LS2P)
    zm2 = _jarvis_impedance(omega, ref.JARVIS_1996_WS2P)
    zs1 = zc * (zl + zm1) / (zc + zl + zm1)
    zs2 = zc * (zl + zm2) / (zc + zl + zm2)
    printed = (
        zs1 * zm1 / ((zl + zs1) * (zl + zm1)) * (zl + zs2) * (zl + zm2) / (zs2 * zm2)
    )
    worst = float(np.max(np.abs(printed * _jarvis_library_ratio(_F_JARVIS) - 1.0)))
    return numeric(
        0.0,
        worst,
        1e-12,
        places=12,
        expected_label="P1/P2 of Appendix B at all 200 frequencies",
        computed_label=f"max relative deviation {worst:.12f}",
    )


@register(
    _IEC61094,
    "Jarvis (1996) NPL CIRA(EXT) 010 Appendix B, folio 26",
    "Volume of the coupler of the example, v = pi r^2 L",
)
def _chk_jarvis_volume() -> Outcome:
    """The compliance of the series impedance is that of half of v, the
    volume the folio prints as 2.534e-7 m^3, to the four figures printed;
    recovered from the impedance the library returns at 1 Hz by solving
    Z_x = Z_L + Z_L Z_c/(Z_L + Z_c) for Z_c.
    """
    density, kappa, pressure = ref.JARVIS_1996_AIR
    length, radius = ref.JARVIS_1996_TUBE
    gas = Fluid(
        temperature_c=23.0,
        static_pressure_pa=pressure,
        composition={},
        model="Jarvis (1996) Appendix B",
        validity="this row",
        properties={"density": density, "heat_capacity_ratio": kappa},
    )
    frequency = 1.0
    omega = 2.0 * math.pi * frequency
    series = complex(
        metrology.air_gap_series_impedance_pa_s_m3(
            [frequency], gap_length_m=length, gap_radius_m=radius, gas=gas
        )[0]
    )
    mass = 1j * omega * density * length / (12.0 * math.pi * radius**2)
    # Z_x = Z_L + Z_L Z_c/(Z_L + Z_c), solved for Z_c and Z_c = kappa p0/(i w v/2).
    parallel = series - mass
    compliance = parallel * mass / (mass - parallel)
    volume = 2.0 * kappa * pressure / (1j * omega * compliance)
    return numeric(
        ref.JARVIS_1996_VOLUME_M3,
        volume.real,
        0.0005e-7,
        unit="m³",
        places=11,
        expected_label="2.534e-7 m³ as printed (+/-0.0005e-7 m³, its last digit)",
        computed_label=f"{volume.real:.5e} m³",
    )


@register(
    _IEC61094,
    "Jarvis (1996) NPL CIRA(EXT) 010 Appendix B, graph on folio 27",
    "Dip and value at 20 kHz of the error in level, and peak and value at 20 kHz of the error in phase, read off the printed graphs",
)
def _chk_jarvis_graph() -> Outcome:
    """The two graphs of x = 20 lg|R| and arg R from 100 Hz to 20 kHz: a dip
    of about -0,0065 dB near 7 kHz, about 0,025 dB at 20 kHz, a phase peak
    of about 0,16 degrees near 12,5 kHz and about 0,09 degrees at 20 kHz,
    each within its graph reading (half a thousandth of a decibel, a
    thousandth at 20 kHz, a hundredth of a degree, and a third of an octave
    in frequency). The phase at 20 kHz is what tells the mass term with its
    imaginary unit from the one the scan shows: read without it, the circuit
    ends at 0,117 degrees.
    """
    ratio = 1.0 / _jarvis_library_ratio(_F_JARVIS)
    level = 20.0 * np.log10(np.abs(ratio))
    phase = np.degrees(np.angle(ratio))
    dip, dip_hz = ref.JARVIS_1996_GRAPH_DIP
    peak, peak_hz = ref.JARVIS_1996_GRAPH_PHASE_PEAK
    lowest = int(np.argmin(level))
    highest = int(np.argmax(phase))
    third = 2.0 ** (1.0 / 6.0)
    checks = (
        abs(level[lowest] - dip) <= 0.0005,
        dip_hz / third <= _F_JARVIS[lowest] <= dip_hz * third,
        abs(level[-1] - ref.JARVIS_1996_GRAPH_AT_20KHZ_DB) <= 0.001,
        abs(phase[highest] - peak) <= 0.01,
        peak_hz / third <= _F_JARVIS[highest] <= peak_hz * third,
        abs(phase[-1] - ref.JARVIS_1996_GRAPH_PHASE_AT_20KHZ_DEG) <= 0.01,
    )
    return count(sum(checks), len(checks), subject="readings of the graphs")


# ---------------------------------------------------------------------------
# The validation of a jig or a coupler (IEC 61094-5 6.7)
# ---------------------------------------------------------------------------


@register(
    _IEC61094,
    "IEC 61094-5:2016 6.7",
    "A jig validated against a reciprocity calibration on a grid of its own: agreement within the root-sum-square of the two expanded uncertainties, 5 frequencies",
)
def _chk_validation() -> Outcome:
    """6.7 asks for the validation "by comparison" and prints no criterion;
    the library reads it as |L_cal - L_val| <= sqrt(U_cal^2 + U_val^2). A
    jig 0,03 dB to 0,15 dB off a reciprocity calibration, with 0,08 dB and
    0,06 dB of expanded uncertainty (0,1 dB for the difference), agrees at
    the three frequencies within 0,1 dB, the one exactly on it included, and
    not at the other two, whatever the binary rounding of the difference.
    The reciprocity calibration runs on a grid of its own, with frequencies
    between and beyond the jig's at other levels and uncertainties, so each
    jig frequency has to meet its own.
    """
    from phonometry.metrology.reciprocity_calibration import ReciprocityCalibration

    offsets = np.array([0.03, -0.1, 0.1 + 1e-9, 0.15, 0.0])
    jig_level = _L_TEST + offsets
    half = _L_REF - jig_level
    jig = metrology.simultaneous_comparison(
        _F, _L_REF, half, -half, expanded_uncertainty_db=0.08
    )
    grid = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0, 16000.0])
    shared = np.isin(grid, _F)
    reciprocity_level = np.full(grid.size, -30.0)
    reciprocity_level[shared] = _L_TEST
    reference_level = np.full(grid.size, -38.0)
    sensitivities = np.vstack(
        [
            10.0 ** (reference_level / 20.0),
            10.0 ** (reciprocity_level / 20.0),
            10.0 ** (reference_level / 20.0),
        ]
    ).astype(np.complex128)
    reciprocity = ReciprocityCalibration(
        frequencies_hz=grid,
        sensitivity_v_per_pa=sensitivities,
        products_v2_per_pa2=np.vstack(
            [
                sensitivities[0] * sensitivities[1],
                sensitivities[1] * sensitivities[2],
                sensitivities[2] * sensitivities[0],
            ]
        ),
        field="pressure",
        method="three_microphones",
        corrections_db={},
        expanded_uncertainty_db=np.where(shared, 0.06, 0.5),
    )
    result = metrology.verify_jig_or_coupler(jig, reciprocity, microphone=1)
    expected = [True, True, False, False, True]
    matching = sum(
        1
        for got, want in zip(result.agrees.tolist(), expected, strict=True)
        if got == want
    )
    matching += int(not result.passes)
    return count(matching, len(expected) + 1, subject="verdicts")


@register(
    _IEC61094,
    "IEC 61094-5:2016 6.7; ISO/IEC Guide 98-3 F.1.2.3, Example 2",
    "Correlation of two calibrations against the same standard of 10^-4, for comparisons of 100, 10 and 1 x 10^-6, as printed",
)
def _chk_validation_correlation() -> Outcome:
    """Example 2 of F.1.2.3: resistors calibrated against the same standard
    share its uncertainty, u(R_i, R_j) = u^2(R_S), and with u(R_S)/R_S =
    10^-4 the correlation coefficient is about 0,5, 0,990 and 1,000 for
    comparisons of 100, 10 and 1 x 10^-6. In levels each calibration
    carries sqrt(u(alpha)^2 + (u(R_S)/R_S)^2) and the two share u(R_S)/R_S,
    all scaled by the same 20/ln 10 dB per neper; the verification's
    correlation coefficient has to give the printed values to the decimals
    printed.
    """
    scale = 20.0 / math.log(10.0)
    standard = ref.GUM_F123_EXAMPLE_2_STANDARD_RELATIVE
    matching = 0
    for comparison, (printed, decimals) in ref.GUM_F123_EXAMPLE_2_CORRELATION.items():
        expanded = 2.0 * scale * math.hypot(comparison, standard)
        result = cc.JigCouplerVerification(
            frequencies_hz=np.array([1000.0]),
            calibration_level_db=np.array([-26.3]),
            calibration_uncertainty_db=np.array([expanded]),
            validation_level_db=np.array([-26.3]),
            validation_uncertainty_db=np.array([expanded]),
            validation="comparison",
            unvalidated_frequencies_hz=np.array([]),
            shared_standard_uncertainty_db=scale * standard,
        )
        coefficient = round(float(result.correlation_coefficient[0]), decimals)
        matching += int(math.isclose(coefficient, printed, abs_tol=1e-12))
    return count(
        matching, len(ref.GUM_F123_EXAMPLE_2_CORRELATION), subject="coefficients"
    )


@register(
    _IEC61094,
    "IEC 61094-5:2016 6.7, Table D.1; ISO/IEC Guide 98-3 5.2.2",
    "Expanded uncertainty of the difference of two calibrations against the same LS2P, each with the budget of Table D.1",
)
def _chk_validation_shared_reference() -> Outcome:
    """Two calibrations against the same reference, each with the eight rows
    of Table D.1, share its first row, 0,025 dB; it cancels in their
    difference, which carries 2 sqrt(2 x 0,001 282) = 0,1013 dB from the
    other seven, where the root-sum-square of the two expanded uncertainties
    gives 0,1235 dB. The expected value is built from the seven rows alone,
    the common quantity taken out as an input of its own (F.1.2.4); the
    library gets the two expanded uncertainties of the budget and the shared
    row, at every frequency of the grid.
    """
    components = ref.IEC61094_5_TABLE_D1_STANDARD_DB
    own = math.sqrt(
        sum(value**2 for key, value in components.items() if key != "reference")
    )
    expected = 2.0 * math.sqrt(2.0) * own
    half = _L_REF - _L_TEST
    jig = metrology.simultaneous_comparison(
        _F,
        _L_REF,
        half,
        -half,
        expanded_uncertainty_db=_budget_d1().expanded_uncertainty_db,
    )
    result = metrology.verify_jig_or_coupler(
        jig, jig, shared_standard_uncertainty_db=components["reference"]
    )
    computed = result.expanded_uncertainty_db
    worst = float(computed[np.argmax(np.abs(computed - expected))])
    return numeric(
        expected,
        worst,
        1e-9,
        unit="dB",
        places=9,
        expected_label=(
            f"{expected:.9f} dB, the reference row cancelling "
            "(0.123515181 dB as independent)"
        ),
        computed_label=f"{worst:.9f} dB at the worst of {computed.size} frequencies",
    )


# ---------------------------------------------------------------------------
# Time-selective processing (IEC 61094-8 Annex B)
# ---------------------------------------------------------------------------


@register(
    _IEC61094,
    "IEC 61094-8:2012 B.6.1, Formula (B.10)",
    "Spectrum of a rectangular pulse of a = 10 V and b = 2,5 µs at 6 frequencies, as printed",
)
def _chk_pulse_spectrum() -> Outcome:
    """X(f) = 2ab sin(2 pi f b)/(2 pi f b) evaluated as printed, against the
    pulse of duration 2b the library reads it as (docs/ERRATA.md).
    """
    amplitude, half = 10.0, 2.5e-6
    frequencies = np.array([1.0e3, 2.0e4, 5.0e4, 1.0e5, 1.5e5, 3.3e5])
    argument = 2.0 * np.pi * frequencies * half
    printed = 2.0 * amplitude * half * np.sin(argument) / argument
    pulse = metrology.rectangular_pulse(2.0 * half, amplitude_v=amplitude)
    worst = float(np.max(np.abs(pulse.spectrum_at(frequencies) - printed)))
    return numeric(
        0.0,
        worst / (2.0 * amplitude * half),
        1e-12,
        places=12,
        expected_label="Formula (B.10) at all 6 frequencies",
        computed_label=f"max deviation {worst / (2.0 * amplitude * half):.12f} of 2ab",
    )


@register(
    _IEC61094,
    "IEC 61094-8:2012 B.6.1",
    "First zero of the pulse spectrum, f = 1/(2b), for b = 2,5 µs",
)
def _chk_pulse_first_zero() -> Outcome:
    """B.6.1: "The first zero in the spectrum is at f = 1/(2b)", 200 kHz."""
    pulse = metrology.rectangular_pulse(5e-6)
    return numeric(1.0 / (2.0 * 2.5e-6), pulse.first_zero_hz, 1e-6, unit="Hz", places=3)


@register(
    _IEC61094,
    "IEC 61094-8:2012 B.6.1",
    "Half-duration b for a first zero an order of magnitude above 20 kHz, 'just a few microseconds'",
)
def _chk_pulse_duration() -> Outcome:
    """A first zero ten times 20 kHz, 200 kHz, asks for 2b = 5 µs."""
    duration = metrology.rectangular_pulse_duration_s(
        20000.0, zero_ratio=ref.IEC61094_8_B61_ZERO_RATIO
    )
    return numeric(
        2.5,
        1e6 * metrology.rectangular_pulse(duration).half_duration_s,
        1e-9,
        unit="µs",
        places=3,
        expected_label="2.5 µs ('just a few microseconds')",
    )


@register(
    _IEC61094,
    "IEC 61094-8:2012 B.2.2",
    "Length of the impulse response of a 120 Hz step, against the 8 ms of the primary reflections",
)
def _chk_stepped_sine_small_room() -> Outcome:
    """B.2.2: "the length of the impulse response will be the inverse of the
    size of the frequency step", and 120 Hz is enough "because the primary
    reflections all occur before 8 ms": the impulse response of a 120 Hz step
    lasts 1/120 Hz = 8,333 ms, past them.
    """
    step, arrival = ref.IEC61094_8_B22_SMALL_ROOM
    frequencies = np.arange(0.0, 24000.0 + step / 2.0, step)
    impulse = metrology.stepped_sine_impulse_response(
        frequencies, np.ones(frequencies.size)
    )
    matching = int(math.isclose(impulse.duration_s, 1.0 / step, rel_tol=1e-12))
    matching += int(impulse.duration_s > arrival)
    return count(
        matching,
        2,
        subject="conditions of B.2.2",
        expected_label="1/120 Hz = 8.333 ms, past the 8 ms printed",
    )


@register(
    _IEC61094,
    "IEC 61094-8:2012 B.2.2",
    "Length of the impulse response of the 30 Hz step of a large free-field room",
)
def _chk_stepped_sine_large_room() -> Outcome:
    """B.2.2: "a frequency resolution of approximately 30 Hz is appropriate",
    an impulse response of 33,3 ms.
    """
    step = ref.IEC61094_8_B22_LARGE_ROOM_STEP_HZ
    frequencies = np.arange(0.0, 24000.0 + step / 2.0, step)
    impulse = metrology.stepped_sine_impulse_response(
        frequencies, np.ones(frequencies.size)
    )
    return numeric(
        1000.0 / step, 1000.0 * impulse.duration_s, 1e-9, unit="ms", places=3
    )


@register(
    _IEC61094,
    "IEC 61094-8:2012 B.2.1, Formulas (B.2) and (B.3); 8.6",
    "A reflection removed by the time window, on data simulated with and without it, 6 frequencies",
)
def _chk_time_selective() -> Outcome:
    """8.6: "a target response can be simulated with and without the
    influence of reflections and the time selective procedure applied to
    each". A stepped-sine response of a direct sound at 3,01 ms and a
    reflection of 0,3 at 6,5 ms, taken to the time domain by (B.3), windowed
    from 2,5 ms to 6 ms and taken back by (B.2), against the direct sound
    alone, e^(-j 2 pi f 3,01 ms), whose phase is not a whole number of half
    turns at any of the frequencies, so a transform of the wrong sign fails.
    """
    step = 50.0
    frequencies = np.arange(0.0, 100000.0 + step / 2.0, step)
    worst = 0.0
    for gain in (0.0, 0.3):
        response = np.exp(-2j * np.pi * frequencies * 0.00301) + gain * np.exp(
            -2j * np.pi * frequencies * 0.0065
        )
        impulse = metrology.stepped_sine_impulse_response(frequencies, response)
        windowed = metrology.time_selective_response(
            impulse.impulse_response,
            impulse.sample_rate_hz,
            window_start_s=0.0025,
            window_end_s=0.006,
        )
        probe = np.array([500.0, 1000.0, 2000.0, 5000.0, 10000.0, 20000.0])
        direct = np.exp(-2j * np.pi * probe * 0.00301)
        worst = max(worst, float(np.max(np.abs(windowed.response_at(probe) - direct))))
    return numeric(
        0.0,
        worst,
        1e-4,
        places=6,
        expected_label="the direct sound alone, with and without the reflection",
        computed_label=f"max deviation {worst:.6f} of the direct sound",
    )


@register(
    _IEC61094,
    "IEC 61094-8:2012 Formula (B.1), B.1.3 a)",
    "The longest window for a reflected path of 2,2 m at 1 m puts that path on the boundary of the region",
)
def _chk_reflection_window() -> Outcome:
    """tau = (L - d)/c, and the region of Formula (B.1) for it has the major
    diameter A = d + tau c = L, at 23 °C.
    """
    window = metrology.reflection_free_window_s(1.0, 2.2)
    region = metrology.free_field_region(1.0, window)
    return numeric(2.2, region.major_axis_m, 1e-12, unit="m", places=6)
