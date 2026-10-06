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

Oracle: IEC 61094-5:2016 (Edition 2.0, English-French): Table A.1 on printed
folio 15 (PDF page 17), Annex C on folio 18 (PDF page 20), D.2 on folio 19
(PDF page 21), Table D.1 on folio 20 (PDF page 22) and its continuation and
D.3 on folio 21 (PDF page 23). BS EN 61094-8:2012, the English text of
EN 61094-8:2012 which is IEC 61094-8:2012 unchanged: Table 1 on folio 12 (PDF
page 14), Table 2 on folio 17 (PDF page 19), B.1 on folio 23 (PDF page 25),
B.2 on folios 24 and 25 (PDF pages 26 and 27) and B.6 on folio 28 (PDF page
30). BS EN 61094-2:2009 Formula (3) on folio 10 (PDF page 12) and E.4 on folio
35 (PDF page 37); BS EN 61094-1:2001 6.2.2 on page 9 (PDF page 11).

Four printed defects sit in this oracle and are recorded in
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
formula and its first zero.
"""

from __future__ import annotations

import math

import numpy as np
import reference_data as ref

from phonometry import metrology
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
