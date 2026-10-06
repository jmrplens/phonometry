#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Primary calibration of laboratory standard microphones by reciprocity.

IEC 61094-2:2009 prints three tables for testing a program: Gerber's
temperature transfer function E_V (Table A.1) and the real and imaginary parts
of the input impedance of six capillary tubes at the reference conditions
(Tables B.1 and B.2). It prints the coupler dimensions of Tables C.1 and C.2,
the wave-motion corrections of Table C.3, the lowest frequency of its
broad-band solution for two couplers (A.3) and its uncertainty components
(Table 1). IEC 61094-3:2016 prints the attenuation of sound in air at nine
conditions (Table B.1) and its own uncertainty components (Table 1). The rows
below reproduce each from the library. Neither part prints a worked
calibration, so the reciprocity chain is checked against the formulas it
comes from: electrical transfer impedances built by Formula (2) of the first
part, or written out by Formula (D.1) of the second, from known sensitivities
have to give those sensitivities back; and the corrected transfer impedance
of each coupler is checked against Formulas (3), (A.1) and (4), (A.3) to
(A.5) written out here, with E_V read from Table A.1.

Oracle: BS EN 61094-2:2009, the English text of EN 61094-2:2009 which is IEC
61094-2:2009 unchanged: Table 1 on printed folio 19 (PDF page 21), Table A.1
on folio 21 (PDF page 23), A.3 on folio 22 (PDF page 24), Tables B.1 and B.2
on folios 24 and 25 (PDF pages 26 and 27), Tables C.1, C.2 and C.3 on folios
28 to 30 (PDF pages 30 to 32), Table F.2 on folio 41 (PDF page 43). IEC
61094-3:2016 (Edition 2.0, 2016-06, English-French) with its corrigendum
IEC 61094-3:2016/COR1:2016: Formulas (7) to (9) on folios 11 and 12 (PDF
pages 13 and 14), Table 1 on folios 17 and 18 (PDF pages 19 and 20), B.2 on
folios 20 and 21 (PDF pages 22 and 23) and Table B.1 on folio 22 (PDF page
24).

Two printed defects in IEC 61094-3 are recorded in ``docs/ERRATA.md`` and
reached by these rows: Step 1 of B.2 prints the last coefficient of the
saturation vapour pressure as 6,3343 184 5e3 where Table F.2 of IEC 61094-2,
which it refers to, prints 6,343 164 5e3; and Formulas (8) and (9) drop the
factor -j that Formula (7) carries.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import reference_data as ref

from phonometry import fluids, metrology
from phonometry.environment.propagation.air_absorption import air_attenuation

from ..registry import Outcome, count, numeric, record, register, residue_text

_IEC61094 = "Microphone calibration by reciprocity (IEC 61094-2, IEC 61094-3)"

_CONDITIONS = {
    "temperature_c": ref.IEC61094_RECIPROCITY_REFERENCE_CONDITIONS[0],
    "static_pressure_pa": ref.IEC61094_RECIPROCITY_REFERENCE_CONDITIONS[1],
    "relative_humidity_percent": ref.IEC61094_RECIPROCITY_REFERENCE_CONDITIONS[2],
}

#: The tables print "0,1667" for a radius that is 1/6 mm (tests/reference_data).
_SIXTH_MM = 1.0 / 6.0

_F = np.array([31.5, 125.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0, 10000.0])


def _air() -> fluids.Fluid:
    return fluids.air(**_CONDITIONS)


def _microphones() -> tuple[metrology.ReciprocityMicrophone, ...]:
    """Three LS1P-like microphones, front cavities of Table C.1."""
    a, b, c, d, _, _ = ref.IEC61094_2_TABLE_C1_MM["LS1P"]
    return tuple(
        metrology.ReciprocityMicrophone(
            equivalent_volume_m3=volume,
            resonance_frequency_hz=resonance,
            loss_factor=loss,
            front_cavity_volume_m3=0.534e-6,
            front_cavity_depth_m=d / 1000.0,
            front_cavity_diameter_m=b / 1000.0,
        )
        for volume, resonance, loss in (
            (144e-9, 8200.0, 1.05),
            (140e-9, 8300.0, 1.0),
            (150e-9, 8000.0, 1.1),
        )
    )


def _plane_wave() -> metrology.PlaneWaveCoupler:
    """The LS1P plane-wave coupler of Table C.1, 7,5 mm long, two tubes."""
    diameter = ref.IEC61094_2_TABLE_C1_MM["LS1P"][2] / 1000.0
    return metrology.PlaneWaveCoupler(
        length_m=7.5e-3,
        diameter_m=diameter,
        capillary=metrology.CapillaryTube(
            length_m=0.05, radius_m=_SIXTH_MM / 1000.0, count=2
        ),
    )


def _large_volume() -> metrology.LargeVolumeCoupler:
    """The LS1P large-volume coupler of Table C.2, with the bores of length F."""
    _, _, c, _, e, f = ref.IEC61094_2_TABLE_C2_MM["LS1P"]
    return metrology.LargeVolumeCoupler(
        length_m=e / 1000.0, diameter_m=c / 1000.0, port_length_m=f / 1000.0
    )


def _equivalent_volume(mic: metrology.ReciprocityMicrophone, f: float) -> complex:
    """V_e of Annex E written out: V_eq / (1 - (f/f0)**2 + j d f/f0)."""
    ratio = f / mic.resonance_frequency_hz
    return mic.equivalent_volume_m3 / (1.0 - ratio**2 + 1j * mic.loss_factor * ratio)


def _reference_stiffness() -> float:
    """kappa_r p_s,r of Formula (3), at the reference conditions of clause 4."""
    return float(_air().heat_capacity_ratio * _CONDITIONS["static_pressure_pa"])


def _true(frequencies: np.ndarray) -> np.ndarray:
    """Pressure sensitivities of LS1P size, in V/Pa."""
    return np.array(
        [
            s * m.complex_equivalent_volume_m3(frequencies) / m.equivalent_volume_m3
            for s, m in zip((-0.050, -0.048, -0.052), _microphones(), strict=True)
        ]
    )


def _worst_relative(computed: np.ndarray, true: np.ndarray) -> float:
    """The largest relative deviation, up to the common sign reciprocity
    leaves open.
    """
    sign = np.sign((computed.reshape(-1)[0] / true.reshape(-1)[0]).real)
    return float(np.max(np.abs(computed / (sign * true) - 1.0)))


# ---------------------------------------------------------------------------
# IEC 61094-2 Annex A
# ---------------------------------------------------------------------------


@register(
    _IEC61094,
    "IEC 61094-2:2009 Table A.1",
    "Gerber's E_V by the full solution, 96 entries at R = 0,2, 0,5 and 1, X = 1 to 800",
)
def _chk_table_a1() -> Outcome:
    """The real and imaginary parts at 16 values of X and three ratios, to the
    0,000 01 the annex states for them.
    """
    worst = 0.0
    for x, row in ref.IEC61094_2_TABLE_A1.items():
        for ratio, (real, imag) in zip(
            ref.IEC61094_2_TABLE_A1_RATIOS, row, strict=True
        ):
            value = complex(metrology.temperature_transfer_function(ratio, x)[()])
            worst = max(worst, abs(value.real - real), abs(value.imag - imag))
    return numeric(
        0.0,
        worst,
        1e-5,
        places=7,
        expected_label="all 96 entries within the stated 0.00001",
        computed_label=f"max deviation {worst:.7f}",
    )


@register(
    _IEC61094,
    "IEC 61094-2:2009 Formula (A.2)",
    "Modulus of the approximation against Table A.1 where A.2 states 0,01 %, X > 5",
)
def _chk_approximation() -> Outcome:
    """The three-term series, at the 33 entries with X above 5."""
    worst = 0.0
    for x, row in ref.IEC61094_2_TABLE_A1.items():
        if not x > 5.0:
            continue
        for ratio, (real, imag) in zip(
            ref.IEC61094_2_TABLE_A1_RATIOS, row, strict=True
        ):
            value = complex(
                metrology.temperature_transfer_function(
                    ratio, x, method="approximation"
                )[()]
            )
            worst = max(worst, abs(abs(value) / abs(complex(real, imag)) - 1.0))
    return numeric(
        0.0,
        worst,
        1e-4,
        places=7,
        expected_label="within 0.01 % at every entry",
        computed_label=f"max relative deviation {worst:.7f}",
    )


@register(
    _IEC61094,
    "IEC 61094-2:2009 A.3",
    "Lowest whole frequency at which check_coupler holds Formulas (A.3) and (A.4) valid, LS1P and LS2aP plane-wave couplers of Table C.1",
)
def _chk_a3() -> Outcome:
    """omega rho a**2 > 100 eta holds from 2,83 Hz and 11,34 Hz, which A.3
    prints as "higher than 3 Hz and 12 Hz": the first whole frequency at which
    the library's check holds the broad-band solution valid.
    """
    computed = {}
    for kind in ref.IEC61094_2_A3_LOWEST_HZ:
        _, b, c, d, _, _ = ref.IEC61094_2_TABLE_C1_MM[kind]
        coupler = metrology.PlaneWaveCoupler(length_m=5e-3, diameter_m=c / 1000.0)
        mic = dataclasses.replace(
            _microphones()[0],
            front_cavity_depth_m=d / 1000.0,
            front_cavity_diameter_m=b / 1000.0,
        )
        computed[kind] = next(
            float(f)
            for f in range(1, 50)
            if metrology.check_coupler(
                [float(f)], coupler, (mic, mic), **_CONDITIONS
            ).broadband_valid
        )
    return record(dict(ref.IEC61094_2_A3_LOWEST_HZ), computed, unit="Hz")


# ---------------------------------------------------------------------------
# IEC 61094-2 Annex B
# ---------------------------------------------------------------------------


def _capillary_deviation(part: str) -> tuple[float, float]:
    """The largest deviation from Table B.1 (real) or B.2 (imaginary) over all
    186 entries, and over the 72 at 20 Hz to 250 Hz.
    """
    frequencies = np.array([row[0] for row in ref.IEC61094_2_TABLE_B])
    printed = np.array(
        [[complex(re, im) for re, im in row[1]] for row in ref.IEC61094_2_TABLE_B]
    )
    low = frequencies <= 250.0
    worst = worst_low = 0.0
    for column, (length, radius) in enumerate(ref.IEC61094_2_TABLE_B_TUBES):
        radius_mm = _SIXTH_MM if math.isclose(radius, 0.1667) else radius
        tube = metrology.capillary_tube_impedance(
            frequencies,
            length_m=length / 1000.0,
            radius_m=radius_mm / 1000.0,
            gas=_air(),
        )
        computed = tube.impedance_pa_s_m3 / 1e9
        values = computed.real if part == "real" else computed.imag
        expected = (
            printed[:, column].real if part == "real" else printed[:, column].imag
        )
        deviation = np.abs(values - expected)
        worst = max(worst, float(deviation.max()))
        worst_low = max(worst_low, float(deviation[low].max()))
    return worst, worst_low


@register(
    _IEC61094,
    "IEC 61094-2:2009 Table B.1",
    "Real part of the input impedance of six open capillary tubes, 20 Hz to 20 kHz, 186 entries",
)
def _chk_table_b1() -> Outcome:
    """Within 0,002 GPa s/m3 everywhere, and the 72 entries from 20 Hz to
    250 Hz within 0,000 51, a hair over the printed half-unit. The table was
    not computed with Annex F air to the fifth figure, and near the tube
    resonances the residue reaches 0,0011 in the real part.
    """
    worst, worst_low = _capillary_deviation("real")
    return numeric(
        0.0,
        worst,
        0.002,
        unit="GPa·s/m³",
        places=4,
        expected_label="all 186 entries within 0.002 GPa·s/m³",
        computed_label=f"max deviation {worst:.4f} (20 Hz to 250 Hz: {worst_low:.4f})",
    )


@register(
    _IEC61094,
    "IEC 61094-2:2009 Table B.2",
    "Imaginary part of the input impedance of six open capillary tubes, 20 Hz to 20 kHz, 186 entries",
)
def _chk_table_b2() -> Outcome:
    """Within 0,002 GPa s/m3 everywhere; the residue reaches 0,0018 at the
    resonances and 0,0007 from 20 Hz to 250 Hz, beyond the printed half-unit:
    the imaginary part is reproduced to the 0,002 of the real one, not to its
    last printed figure.
    """
    worst, worst_low = _capillary_deviation("imag")
    return numeric(
        0.0,
        worst,
        0.002,
        unit="GPa·s/m³",
        places=4,
        expected_label="all 186 entries within 0.002 GPa·s/m³",
        computed_label=f"max deviation {worst:.4f} (20 Hz to 250 Hz: {worst_low:.4f})",
    )


# ---------------------------------------------------------------------------
# IEC 61094-2 Annex C and Table 1
# ---------------------------------------------------------------------------


@register(
    _IEC61094,
    "IEC 61094-2:2009 Table C.1",
    "Nominal dimensions of the plane-wave couplers of LS1P, LS2aP and LS2bP microphones",
)
def _chk_table_c1() -> Outcome:
    """Eighteen cells: A, B, C, D and the two ends of E for three types."""
    matching = 0
    for kind, (a, b, c, d, e_min, e_max) in ref.IEC61094_2_TABLE_C1_MM.items():
        row = metrology.IEC61094_2_TABLE_C1[kind]
        computed = (
            row.microphone_diameter_mm,
            row.front_cavity_diameter_mm,
            row.coupler_diameter_mm,
            row.front_cavity_depth_mm,
            *(row.coupler_length_range_mm or (math.nan, math.nan)),
        )
        matching += sum(
            math.isclose(x, y)
            for x, y in zip(computed, (a, b, c, d, e_min, e_max), strict=True)
        )
    return count(matching, 18, subject="cells of Table C.1")


@register(
    _IEC61094,
    "IEC 61094-2:2009 Table C.2",
    "Nominal dimensions and tolerance of the large-volume couplers of LS1P, LS2aP and LS2bP microphones",
)
def _chk_table_c2() -> Outcome:
    """Eighteen cells, A to F for three types, and the ± 0,03 mm on C, E, F."""
    matching = 0
    for kind, (a, b, c, d, e, f) in ref.IEC61094_2_TABLE_C2_MM.items():
        row = metrology.IEC61094_2_TABLE_C2[kind]
        computed = (
            row.microphone_diameter_mm,
            row.front_cavity_diameter_mm,
            row.coupler_diameter_mm,
            row.front_cavity_depth_mm,
            row.coupler_length_mm or math.nan,
            row.port_length_mm or math.nan,
        )
        matching += sum(
            math.isclose(x, y)
            for x, y in zip(computed, (a, b, c, d, e, f), strict=True)
        )
        matching += math.isclose(
            row.tolerance_mm or math.nan, ref.IEC61094_2_TABLE_C2_TOLERANCE_MM
        )
    return count(matching, 21, subject="cells of Table C.2")


@register(
    _IEC61094,
    "IEC 61094-2:2009 Table C.3",
    "Wave-motion corrections of the air-filled large-volume coupler for LS1P microphones",
)
def _chk_table_c3() -> Outcome:
    """The six rows, from 0 dB up to 800 Hz to -0,087 dB at 2,5 kHz."""
    frequencies = sorted(ref.IEC61094_2_TABLE_C3_DB)
    correction = metrology.large_volume_wave_motion_correction(frequencies)
    matching = sum(
        math.isclose(float(value), ref.IEC61094_2_TABLE_C3_DB[f], abs_tol=1e-12)
        for f, value in zip(frequencies, correction.correction_db, strict=True)
    )
    return count(matching, len(frequencies), subject="rows of Table C.3")


@register(
    _IEC61094,
    "IEC 61094-2:2009 Table 1",
    "The 35 uncertainty components and the subclauses each is referred to",
)
def _chk_table_1_part_2() -> Outcome:
    """Each measured quantity as printed, with its subclauses."""
    rows = [
        (row.component, row.subclauses) for row in metrology.IEC61094_2_TABLE_1.values()
    ]
    matching = sum(
        1
        for got, printed in zip(rows, ref.IEC61094_2_TABLE_1_TEXT, strict=False)
        if got == printed
    )
    return count(
        matching if len(rows) == len(ref.IEC61094_2_TABLE_1_TEXT) else 0,
        len(ref.IEC61094_2_TABLE_1_TEXT),
        subject="rows of Table 1",
    )


# ---------------------------------------------------------------------------
# IEC 61094-2 clause 5: the chain
# ---------------------------------------------------------------------------


def _pressure_triad(
    coupler: metrology.PlaneWaveCoupler | metrology.LargeVolumeCoupler,
) -> tuple[list[np.ndarray], list[metrology.CouplerTransferImpedance], np.ndarray]:
    mics = _microphones()
    true = _true(_F)
    pairs = ((0, 1), (1, 2), (2, 0))
    acoustic = [
        metrology.coupler_transfer_impedance(
            _F, coupler, mics[i], mics[j], **_CONDITIONS
        )
        for i, j in pairs
    ]
    electrical = [
        true[i] * true[j] * z.transfer_impedance_pa_s_m3
        for (i, j), z in zip(pairs, acoustic, strict=True)
    ]
    return electrical, acoustic, true


@register(
    _IEC61094,
    "IEC 61094-2:2009 Formulas (2) and (7)",
    "Three LS1P microphones through the plane-wave coupler give their sensitivities back",
)
def _chk_formula_7() -> Outcome:
    """Electrical transfer impedances built by Formula (2) from known complex
    sensitivities and the corrected acoustic transfer impedance of the
    plane-wave coupler, 31,5 Hz to 10 kHz.
    """
    electrical, acoustic, true = _pressure_triad(_plane_wave())
    result = metrology.pressure_reciprocity(_F, electrical, acoustic)
    worst = _worst_relative(result.sensitivity_v_per_pa, true)
    return numeric(
        0.0,
        worst,
        1e-12,
        places=12,
        expected_label="the three sensitivities at all 8 frequencies",
        computed_label=f"max relative deviation {residue_text(worst, spec='.2e')}",
    )


@register(
    _IEC61094,
    "IEC 61094-2:2009 Formula (8)",
    "Two microphones and the ratio from an auxiliary source give their sensitivities back",
)
def _chk_formula_8() -> Outcome:
    """The pair 1-2 in the large-volume coupler, with M1/M2 as the source
    measures it.
    """
    electrical, acoustic, true = _pressure_triad(_large_volume())
    result = metrology.pressure_reciprocity_pair(
        _F, electrical[0], acoustic[0], true[0] / true[1]
    )
    worst = _worst_relative(result.sensitivity_v_per_pa, true[:2])
    return numeric(
        0.0,
        worst,
        1e-12,
        places=12,
        expected_label="both sensitivities at all 8 frequencies",
        computed_label=f"max relative deviation {residue_text(worst, spec='.2e')}",
    )


@register(
    _IEC61094,
    "IEC 61094-2:2009 Formula (4)",
    "The lossless plane-wave line at 20 Hz is the compliance of its gas (stiffness rho c^2), the excess front-cavity volumes and the equivalent volumes",
)
def _chk_formula_3_4() -> Outcome:
    """Formula (4) with no losses at 20 Hz against the compliances it tends
    to: the gas of the line with the stiffness rho c**2 of its wave impedance
    Z_a,0 = rho c/S_0, the excess volumes of the front cavities (kappa p_s)
    and the two equivalent volumes (kappa_r p_s,r). It is not Formula (3) as
    printed, which holds the gas by kappa p_s: for the air of Annex F rho c0**2
    and kappa p_s differ by 3,4e-4, 30 times this tolerance.
    """
    mics = _microphones()
    coupler = metrology.PlaneWaveCoupler(length_m=7.5e-3, diameter_m=18.6e-3)
    z = metrology.coupler_transfer_impedance(
        [20.0], coupler, mics[0], mics[1], **_CONDITIONS
    )
    gas = _air()
    area = math.pi * 0.0093**2
    depth = mics[0].front_cavity_depth_m
    kappa_r = gas.heat_capacity_ratio
    compliance = (
        area * (7.5e-3 + 2 * depth) / (gas.density * gas.speed_of_sound**2)
        + 2
        * (mics[0].front_cavity_volume_m3 - area * depth)
        / (gas.heat_capacity_ratio * _CONDITIONS["static_pressure_pa"])
        + (_equivalent_volume(mics[0], 20.0) + _equivalent_volume(mics[1], 20.0))
        / (kappa_r * _CONDITIONS["static_pressure_pa"])
    )
    expected = 1.0 / (2j * math.pi * 20.0 * compliance)
    deviation = abs(complex(z.adiabatic_impedance_pa_s_m3[0]) / expected - 1.0)
    return numeric(
        0.0,
        deviation,
        1e-5,
        places=8,
        expected_label="the compliances of the line, rho c**2, to (k l0)**2",
        computed_label=f"relative deviation {deviation:.2e}",
    )


@register(
    _IEC61094,
    "IEC 61094-2:2009 Formula (A.1)",
    "Heat-conduction factor from isothermal (kappa) to adiabatic (1) in the large-volume coupler of Table C.2",
)
def _chk_formula_a1() -> Outcome:
    """At 0,01 Hz the cavity is isothermal and Delta_H = kappa; at 1 MHz it is
    adiabatic and Delta_H = 1.
    """
    coupler = _large_volume()
    heat = metrology.heat_conduction_correction(
        [0.01, 1.0e6],
        volume_m3=coupler.cavity_volume_m3,
        surface_area_m2=coupler.cavity_surface_m2,
        length_to_diameter_ratio=coupler.length_m / coupler.diameter_m,
        gas=_air(),
    )
    kappa = _air().heat_capacity_ratio
    low = abs(complex(heat.volume_factor[0])) / kappa - 1.0
    high = abs(complex(heat.volume_factor[1])) - 1.0
    worst = max(abs(low), abs(high))
    return numeric(
        0.0,
        worst,
        2e-3,
        places=5,
        expected_label="kappa at 0.01 Hz, 1 at 1 MHz",
        computed_label=f"max relative deviation {residue_text(worst, spec='.2e')}",
    )


@register(
    _IEC61094,
    "IEC 61094-2:2009 Formulas (3) and (A.1) with Table A.1",
    "Heat-conducting transfer impedance of a large-volume coupler of R = 0,5 at the X = 2 and X = 20 of Table A.1, at 23 °C and at 20 °C, 95 kPa",
)
def _chk_large_volume_heat() -> Outcome:
    """Z''_a,12 against Formula (3) with Delta_H = kappa/(1 + (kappa - 1) E_V)
    and E_V read from Table A.1, the gas held by kappa p_s and the
    microphones by kappa_r p_s,r. The volume and the surface are the cavity's,
    the two bores' and the two front cavities' written out.
    """
    mics = _microphones()[:2]
    coupler = metrology.LargeVolumeCoupler(
        length_m=10e-3, diameter_m=20e-3, port_length_m=0.4e-3
    )
    b, d, port = 18.6e-3, 1.95e-3, 0.4e-3
    volume = math.pi * 0.02**2 / 4.0 * 0.01 + 2 * (
        0.534e-6 + math.pi * b**2 / 4.0 * port
    )
    surface = math.pi * 0.02 * 0.02 + 2 * math.pi * b * (d + port)
    worst = 0.0
    for conditions in (
        _CONDITIONS,
        {
            "temperature_c": 20.0,
            "static_pressure_pa": 95000.0,
            "relative_humidity_percent": 60.0,
        },
    ):
        gas = fluids.air(**conditions)
        kappa = gas.heat_capacity_ratio
        for x in (2.0, 20.0):
            frequency = x * kappa * gas.thermal_diffusivity / (volume / surface) ** 2
            real, imag = ref.IEC61094_2_TABLE_A1[x][1]
            delta_h = kappa / (1.0 + (kappa - 1.0) * complex(real, imag))
            expected = 1.0 / (
                2j
                * math.pi
                * frequency
                * (
                    delta_h * volume / (kappa * conditions["static_pressure_pa"])
                    + sum(_equivalent_volume(m, frequency) for m in mics)
                    / _reference_stiffness()
                )
            )
            z = metrology.coupler_transfer_impedance(
                [frequency], coupler, *mics, **conditions
            )
            worst = max(
                worst,
                abs(complex(z.heat_conducting_impedance_pa_s_m3[0]) / expected - 1.0),
            )
    return numeric(
        0.0,
        worst,
        1e-5,
        places=8,
        expected_label="Formula (3) with Table A.1, within its 0.00001",
        computed_label=f"max relative deviation {residue_text(worst, spec='.2e')}",
    )


@register(
    _IEC61094,
    "IEC 61094-2:2009 Formulas (4) and (A.3) to (A.5)",
    "Heat-conducting and viscous transfer impedance of the LS1P plane-wave coupler at 250 Hz, 1 kHz and 8 kHz",
)
def _chk_plane_wave_losses() -> Outcome:
    """Z''_a,12 against Formula (4) with gamma of (A.3), Z_a,0 of (A.4) and
    1/Z_a,h of (A.5) added to each microphone admittance, written out as A.3
    prints them, each microphone in parallel with the excess volume of its
    front cavity (7.3.3.1).
    """
    mics = _microphones()[:2]
    coupler = metrology.PlaneWaveCoupler(length_m=7.5e-3, diameter_m=18.6e-3)
    gas = _air()
    rho, c, kappa = gas.density, gas.speed_of_sound, gas.heat_capacity_ratio
    a = 18.6e-3 / 2.0
    s0 = math.pi * a**2
    l0 = 7.5e-3 + 2 * mics[0].front_cavity_depth_m
    worst = 0.0
    for frequency in (250.0, 1000.0, 8000.0):
        omega = 2.0 * math.pi * frequency
        loss = (1.0 - 1.0j) / math.sqrt(2.0) / a
        viscous = math.sqrt(gas.viscosity / (omega * rho))
        thermal = (kappa - 1.0) * math.sqrt(gas.thermal_diffusivity / omega)
        gamma = 1j * omega / c * (1.0 + loss * (viscous + thermal))
        z0 = rho * c / s0 * (1.0 + loss * (viscous - thermal))
        end = (
            s0 / (rho * c) * (1.0 + 1.0j) / math.sqrt(2.0) * (kappa - 1.0) / c
        ) * math.sqrt(gas.thermal_diffusivity * omega)
        y1, y2 = (
            1j * omega * _equivalent_volume(m, frequency) / _reference_stiffness()
            + 1j
            * omega
            * (m.front_cavity_volume_m3 - s0 * m.front_cavity_depth_m)
            / (kappa * _CONDITIONS["static_pressure_pa"])
            + end
            for m in mics
        )
        inverse = (
            (z0 * y1 + z0 * y2) * np.cosh(gamma * l0)
            + (1.0 + z0**2 * y1 * y2) * np.sinh(gamma * l0)
        ) / z0
        z = metrology.coupler_transfer_impedance(
            [frequency], coupler, *mics, **_CONDITIONS
        )
        worst = max(
            worst, abs(complex(z.heat_conducting_impedance_pa_s_m3[0]) * inverse - 1.0)
        )
    return numeric(
        0.0,
        worst,
        1e-12,
        places=12,
        expected_label="Formulas (4), (A.3), (A.4) and (A.5) at 3 frequencies",
        computed_label=f"max relative deviation {residue_text(worst, spec='.2e')}",
    )


# ---------------------------------------------------------------------------
# IEC 61094-3
# ---------------------------------------------------------------------------


def _table_b1_part_3() -> tuple[np.ndarray, np.ndarray]:
    frequencies = 1000.0 * np.array(sorted(ref.IEC61094_3_TABLE_B1))
    values = np.array([ref.IEC61094_3_TABLE_B1[f / 1000.0] for f in frequencies])
    return frequencies, values


@register(
    _IEC61094,
    "IEC 61094-3:2016 Table B.1",
    "Attenuation of sound pressure in air by ISO 9613-1, 1 kHz to 50 kHz at nine conditions, 162 entries",
)
def _chk_table_b1_part_3() -> Outcome:
    """The table says it was "calculated according to ISO 9613-1"; the
    library's ISO 9613-1 at the nominal frequencies gives each entry to the
    fourth decimal it prints.
    """
    import warnings

    from phonometry.environment import AtmosphericAbsorptionWarning

    frequencies, values = _table_b1_part_3()
    matching = 0
    for column, (temperature, humidity) in enumerate(
        ref.IEC61094_3_TABLE_B1_CONDITIONS
    ):
        with warnings.catch_warnings():
            # Table B.1 goes to 50 kHz, past the 10 kHz of ISO 9613-1's own
            # table; the formula is what the standard used.
            warnings.simplefilter("ignore", AtmosphericAbsorptionWarning)
            alpha = air_attenuation(
                frequencies,
                temperature_c=temperature,
                relative_humidity_percent=humidity,
            )
        matching += int(np.sum(np.abs(np.round(alpha, 4) - values[:, column]) < 1e-9))
    return count(matching, values.size, subject="entries of Table B.1")


@register(
    _IEC61094,
    "IEC 61094-3:2016 B.2",
    "Attenuation by the five steps of B.2 against Table B.1, within the ±10 % B.2 states",
)
def _chk_b2() -> Outcome:
    """The procedure the calibration uses adjusts ISO 9613-1 to the quantities
    of IEC 61094-2; over the 162 entries it stays within 1,1 % of the table,
    whose smallest entries are themselves rounded by up to 1 %.
    """
    frequencies, values = _table_b1_part_3()
    worst = 0.0
    for column, (temperature, humidity) in enumerate(
        ref.IEC61094_3_TABLE_B1_CONDITIONS
    ):
        attenuation = metrology.reciprocity_air_attenuation(
            frequencies,
            temperature_c=temperature,
            static_pressure_pa=101325.0,
            relative_humidity_percent=humidity,
        )
        worst = max(
            worst,
            float(
                np.max(
                    np.abs(attenuation.attenuation_db_per_m / values[:, column] - 1.0)
                )
            ),
        )
    return numeric(
        0.0,
        worst,
        0.10,
        places=4,
        expected_label="within ±10 % of all 162 entries",
        computed_label=f"max relative deviation {worst:.4f}",
    )


@register(
    _IEC61094,
    "IEC 61094-3:2016 B.2 Step 1 vs IEC 61094-2:2009 Table F.2",
    "Water vapour mole fraction at 23 °C, 101,325 kPa, 50 % with the saturation pressure of Table F.2",
)
def _chk_step_1() -> Outcome:
    """Step 1 refers to F.2 of IEC 61094-2 and prints its last coefficient as
    6,3343 184 5e3 where Table F.2 prints 6,343 164 5e3 (docs/ERRATA.md); with
    the latter the mole fraction is that of Annex F.
    """
    attenuation = metrology.reciprocity_air_attenuation([1000.0], **_CONDITIONS)
    expected = float(_air().composition["water_vapour_mole_fraction"])
    return numeric(
        expected,
        attenuation.water_vapour_mole_fraction,
        1e-12,
        rel=True,
        places=8,
        expected_label=f"{expected:.8f}, the x_w of IEC 61094-2 Annex F",
    )


def _free_field_true() -> np.ndarray:
    frequencies = 1000.0 * np.array([1.0, 2.0, 4.0, 8.0, 16.0, 20.0])
    return np.array(
        [
            -0.050 * np.exp(0.1j - 0.02j * frequencies / 1000.0),
            -0.049 * np.exp(0.05j - 0.03j * frequencies / 1000.0),
            -0.051 * np.exp(0.2j - 0.025j * frequencies / 1000.0),
        ]
    )


_FF = 1000.0 * np.array([1.0, 2.0, 4.0, 8.0, 16.0, 20.0])
_DISTANCES = (0.30, 0.25, 0.20)
_CENTRES = (0.009, 0.0085, 0.0095)


def _free_field_electrical(true: np.ndarray) -> list[np.ndarray]:
    """Formula (D.1) written out, U2/i1 = j rho f/(2 d) M1 M2 e^(-jkd)
    e^(-alpha d_m), with d between the acoustic centres, d_m between the
    diaphragms and k = omega/c0 without dispersion.
    """
    air = _air()
    alpha = metrology.reciprocity_air_attenuation(
        _FF, **_CONDITIONS
    ).attenuation_np_per_m
    k = 2.0 * math.pi * _FF / air.speed_of_sound
    pairs = ((0, 1), (1, 2), (2, 0))
    electrical = []
    for n, (i, j) in enumerate(pairs):
        d = _DISTANCES[n] - _CENTRES[i] - _CENTRES[j]
        electrical.append(
            1j
            * air.density
            * _FF
            / (2.0 * d)
            * true[i]
            * true[j]
            * np.exp(-1j * k * d)
            * np.exp(-alpha * _DISTANCES[n])
        )
    return electrical


@register(
    _IEC61094,
    "IEC 61094-3:2016 Formulas (7), (8) and (D.1)",
    "Three microphones at 0,20 m to 0,30 m give their complex free-field sensitivities back",
)
def _chk_formula_8_free_field() -> Outcome:
    """Electrical transfer impedances written out by Formula (D.1), with the
    acoustic centres 8,5 mm to 9,5 mm in front of the diaphragms, 1 kHz to
    20 kHz. Formula (8) as printed drops the factor -j of Formula (7) and would
    turn every phase by 45 degrees (docs/ERRATA.md).
    """
    true = _free_field_true()
    result = metrology.free_field_reciprocity(
        _FF,
        _free_field_electrical(true),
        diaphragm_distances_m=_DISTANCES,
        acoustic_centres_m=_CENTRES,
        dispersion=False,
        **_CONDITIONS,
    )
    worst = _worst_relative(result.sensitivity_v_per_pa, true)
    return numeric(
        0.0,
        worst,
        1e-12,
        places=12,
        expected_label="the three complex sensitivities at all 6 frequencies",
        computed_label=f"max relative deviation {residue_text(worst, spec='.2e')}",
    )


@register(
    _IEC61094,
    "IEC 61094-3:2016 Formula (9)",
    "Two microphones and the ratio from an auxiliary source give their complex sensitivities back, as COR1 makes the formula",
)
def _chk_formula_9_free_field() -> Outcome:
    """COR1 makes Formula (9) the complex sensitivity."""
    true = _free_field_true()
    result = metrology.free_field_reciprocity_pair(
        _FF,
        _free_field_electrical(true)[0],
        true[0] / true[1],
        diaphragm_distance_m=_DISTANCES[0],
        acoustic_centres_m=_CENTRES[:2],
        dispersion=False,
        **_CONDITIONS,
    )
    worst = _worst_relative(result.sensitivity_v_per_pa, true[:2])
    return numeric(
        0.0,
        worst,
        1e-12,
        places=12,
        expected_label="both complex sensitivities at all 6 frequencies",
        computed_label=f"max relative deviation {residue_text(worst, spec='.2e')}",
    )


@register(
    _IEC61094,
    "IEC 61094-3:2016 6.5",
    "Acoustic centre where the inverse of the pressure, corrected for attenuation, crosses the axis",
)
def _chk_acoustic_centre() -> Outcome:
    """A source whose pressure falls as exp(-alpha r)/(r - 4 mm), measured at
    150 mm to 500 mm with alpha = 0,05 Np/m.
    """
    distances = np.array([0.15, 0.2, 0.3, 0.4, 0.5])
    alpha = 0.05
    pressures = np.exp(-alpha * distances) / (distances - 0.004)
    centre = metrology.acoustic_centre(distances, pressures, attenuation_np_per_m=alpha)
    return numeric(4.0, 1000.0 * centre.position_m, 1e-9, unit="mm", places=6)


@register(
    _IEC61094,
    "IEC 61094-3:2016 Table 1",
    "The 23 uncertainty components and the subclauses each is referred to",
)
def _chk_table_1_part_3() -> Outcome:
    """Each measured quantity as printed, with its subclauses."""
    rows = [
        (row.component, row.subclauses) for row in metrology.IEC61094_3_TABLE_1.values()
    ]
    matching = sum(
        1
        for got, printed in zip(rows, ref.IEC61094_3_TABLE_1_TEXT, strict=False)
        if got == printed
    )
    return count(
        matching if len(rows) == len(ref.IEC61094_3_TABLE_1_TEXT) else 0,
        len(ref.IEC61094_3_TABLE_1_TEXT),
        subject="rows of Table 1",
    )
