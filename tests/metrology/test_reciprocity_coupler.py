#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 61094-2:2009: primary pressure calibration by reciprocity in a coupler.

The oracle is the printed page, in ``tests/reference_data``: Table A.1 on
folio 21 (PDF page 23), A.3 on folio 22, Tables B.1 and B.2 on folios 24 and
25, Tables C.1 to C.3 on folios 28 to 30. The reciprocity chain prints no
worked example, so it is checked against the equations it comes from:
electrical transfer impedances built by Formula (2) from known sensitivities
and the computed acoustic transfer impedances have to give the sensitivities
back.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest
import reference_data as ref

from phonometry import fluids, metrology
from phonometry.metrology import reciprocity_coupler as rc

_CONDITIONS = {
    "temperature_c": 23.0,
    "static_pressure_pa": 101325.0,
    "relative_humidity_percent": 50.0,
}
_F = np.array([20.0, 63.0, 250.0, 1000.0, 2000.0, 4000.0, 8000.0, 10000.0])


def _air() -> fluids.Fluid:
    return fluids.air(**_CONDITIONS)


def _mic(
    volume: float = 144e-9, resonance: float = 8200.0, loss: float = 1.05
) -> metrology.ReciprocityMicrophone:
    """An LS1P-like microphone in the plane-wave coupler of Table C.1."""
    return metrology.ReciprocityMicrophone(
        equivalent_volume_m3=volume,
        resonance_frequency_hz=resonance,
        loss_factor=loss,
        front_cavity_volume_m3=0.534e-6,
        front_cavity_depth_m=1.95e-3,
        front_cavity_diameter_m=18.6e-3,
    )


_MICS = (_mic(), _mic(140e-9, 8300.0, 1.0), _mic(150e-9, 8000.0, 1.1))
_TUBES = metrology.CapillaryTube(length_m=0.05, radius_m=1.0 / 6000.0, count=2)
_PLANE = metrology.PlaneWaveCoupler(
    length_m=7.5e-3, diameter_m=18.6e-3, capillary=_TUBES
)
#: The LS1P coupler of Table C.2: E, C and the bores of length F.
_LARGE = metrology.LargeVolumeCoupler(
    length_m=12.55e-3,
    diameter_m=42.88e-3,
    port_length_m=0.80e-3,
    capillary=metrology.CapillaryTube(length_m=0.1, radius_m=0.2e-3, count=2),
)
#: The reference conditions of clause 4, where kappa_r p_s,r is taken.
_REFERENCE_STIFFNESS = fluids.air(**_CONDITIONS).heat_capacity_ratio * 101325.0


def _equivalent_volume(mic: metrology.ReciprocityMicrophone, f: float) -> complex:
    """V_e of Annex E written out: V_eq / (1 - (f/f0)**2 + j d f/f0)."""
    ratio = f / mic.resonance_frequency_hz
    return mic.equivalent_volume_m3 / (1.0 - ratio**2 + 1j * mic.loss_factor * ratio)


def _true_sensitivities(frequencies: np.ndarray) -> np.ndarray:
    """Three pressure sensitivities of LS1P size, in V/Pa."""
    scale = (-0.050, -0.048, -0.052)
    return np.array(
        [
            s * m.complex_equivalent_volume_m3(frequencies) / m.equivalent_volume_m3
            for s, m in zip(scale, _MICS, strict=True)
        ]
    )


def _triad(
    coupler: metrology.PlaneWaveCoupler | metrology.LargeVolumeCoupler,
    frequencies: np.ndarray = _F,
) -> tuple[list[np.ndarray], list[metrology.CouplerTransferImpedance], np.ndarray]:
    true = _true_sensitivities(frequencies)
    pairs = ((0, 1), (1, 2), (2, 0))
    acoustic = [
        metrology.coupler_transfer_impedance(
            frequencies, coupler, _MICS[i], _MICS[j], **_CONDITIONS
        )
        for i, j in pairs
    ]
    electrical = [
        true[i] * true[j] * z.transfer_impedance_pa_s_m3
        for (i, j), z in zip(pairs, acoustic, strict=True)
    ]
    return electrical, acoustic, true


# ---------------------------------------------------------------------------
# Annex A: heat conduction
# ---------------------------------------------------------------------------


def test_full_solution_reproduces_every_entry_of_table_a1() -> None:
    """The 96 entries, to the 0,000 01 A.2 states for them."""
    worst = 0.0
    for x, row in ref.IEC61094_2_TABLE_A1.items():
        for ratio, (real, imag) in zip(
            ref.IEC61094_2_TABLE_A1_RATIOS, row, strict=True
        ):
            value = complex(metrology.temperature_transfer_function(ratio, x))
            worst = max(worst, abs(value.real - real), abs(value.imag - imag))
    assert worst <= 1e-5


def test_approximation_is_accurate_where_the_annex_says() -> None:
    """Formula (A.2): modulus to 0,01 % for 0,125 < R < 8 and X > 5."""
    for x, row in ref.IEC61094_2_TABLE_A1.items():
        if not x > 5.0:
            continue
        for ratio, (real, imag) in zip(
            ref.IEC61094_2_TABLE_A1_RATIOS, row, strict=True
        ):
            value = complex(
                metrology.temperature_transfer_function(
                    ratio, x, method="approximation"
                )
            )
            assert abs(abs(value) / abs(complex(real, imag)) - 1.0) < 1e-4


def test_approximation_departs_below_its_domain() -> None:
    """At R = 0,2 and X = 1 the three-term series is 0,24 % off the table."""
    value = complex(
        metrology.temperature_transfer_function(0.2, 1.0, method="approximation")
    )
    assert abs(value - complex(0.72127, 0.24038)) > 1e-3


def test_full_solution_tends_to_the_boundary_layer() -> None:
    """At large X both forms agree with 1 - S."""
    exact = metrology.temperature_transfer_function(0.5, [1e4, 1e5])
    approximate = metrology.temperature_transfer_function(
        0.5, [1e4, 1e5], method="approximation"
    )
    np.testing.assert_allclose(exact, approximate, atol=1e-8)


def test_volume_factor_runs_from_isothermal_to_adiabatic() -> None:
    """Formula (A.1): 1 for E_V = 1 and kappa for E_V = 0."""
    heat = metrology.heat_conduction_correction(
        [0.01, 1e6],
        volume_m3=1e-6,
        surface_area_m2=6e-4,
        length_to_diameter_ratio=0.5,
        gas=_air(),
    )
    kappa = _air().heat_capacity_ratio
    assert abs(heat.volume_factor[0]) == pytest.approx(kappa, rel=2e-2)
    assert abs(heat.volume_factor[1]) == pytest.approx(1.0, abs=1e-3)
    assert np.all(np.diff(heat.correction_db) < 0.0)


@pytest.mark.parametrize("x", [0.0, -1.0, float("nan")])
def test_temperature_transfer_refuses_a_parameter_that_is_not_positive(
    x: float,
) -> None:
    with pytest.raises(ValueError, match="'x' must be positive"):
        metrology.temperature_transfer_function(0.5, x)


def test_temperature_transfer_refuses_an_unknown_method() -> None:
    with pytest.raises(ValueError, match="'method' must be"):
        metrology.temperature_transfer_function(0.5, 10.0, method="gerber")


@pytest.mark.parametrize(
    ("kind", "printed"), sorted(ref.IEC61094_2_A3_LOWEST_HZ.items())
)
def test_broadband_validity_is_the_frequency_a3_prints(
    kind: str, printed: float
) -> None:
    """A.3: omega rho a**2 > 100 eta above 3 Hz (LS1P) and 12 Hz (LS2aP).

    The printed frequencies are the bounds rounded up: 2,83 Hz and 11,34 Hz.
    """
    gas = _air()
    radius = ref.IEC61094_2_TABLE_C1_MM[kind][2] / 2000.0
    lowest = 100.0 * gas.viscosity / (2.0 * math.pi * gas.density * radius**2)
    assert math.ceil(lowest) == printed


# ---------------------------------------------------------------------------
# Annex B: capillary tubes
# ---------------------------------------------------------------------------


def _tube_table() -> tuple[np.ndarray, np.ndarray]:
    frequencies = np.array([row[0] for row in ref.IEC61094_2_TABLE_B])
    values = np.array(
        [[complex(re, im) for re, im in row[1]] for row in ref.IEC61094_2_TABLE_B]
    )
    return frequencies, values


def _tube(length_mm: float, radius_mm: float, frequencies: np.ndarray) -> np.ndarray:
    radius = 1.0 / 6000.0 if math.isclose(radius_mm, 0.1667) else radius_mm / 1000.0
    tube = metrology.capillary_tube_impedance(
        frequencies, length_m=length_mm / 1000.0, radius_m=radius, gas=_air()
    )
    return tube.impedance_pa_s_m3 / 1e9


def test_capillary_impedance_reproduces_tables_b1_and_b2() -> None:
    """All 186 complex entries within 0,002 GPa s/m3.

    The tables were not computed with Annex F air to the fifth figure: the low
    frequencies agree to the printed rounding, the resonances to 0,0018.
    """
    frequencies, printed = _tube_table()
    for column, (length, radius) in enumerate(ref.IEC61094_2_TABLE_B_TUBES):
        computed = _tube(length, radius, frequencies)
        np.testing.assert_allclose(computed.real, printed[:, column].real, atol=2e-3)
        np.testing.assert_allclose(computed.imag, printed[:, column].imag, atol=2e-3)
        low = frequencies <= 250.0
        np.testing.assert_allclose(
            computed[low].real, printed[low, column].real, atol=5.1e-4
        )


def test_the_printed_radius_0_1667_mm_is_one_sixth_of_a_millimetre() -> None:
    """At 20 Hz the 50 mm tube prints 3,015; 0,1667 mm gives 3,013, 1/6 mm 3,015."""
    exact = metrology.capillary_tube_impedance(
        [20.0], length_m=0.05, radius_m=1.0 / 6000.0, gas=_air()
    )
    rounded = metrology.capillary_tube_impedance(
        [20.0], length_m=0.05, radius_m=0.1667e-3, gas=_air()
    )
    assert round(exact.impedance_pa_s_m3[0].real / 1e9, 3) == pytest.approx(3.015)
    assert round(rounded.impedance_pa_s_m3[0].real / 1e9, 3) == pytest.approx(3.013)


def test_capillary_impedance_tends_to_poiseuille() -> None:
    """At low frequency the real part is 8 eta l / (pi a**4)."""
    gas = _air()
    tube = metrology.capillary_tube_impedance(
        [0.1], length_m=0.1, radius_m=0.25e-3, gas=gas
    )
    poiseuille = 8.0 * gas.viscosity * 0.1 / (math.pi * 0.25e-3**4)
    assert tube.impedance_pa_s_m3[0].real == pytest.approx(poiseuille, rel=1e-4)


# ---------------------------------------------------------------------------
# Annex C: couplers and wave motion
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("kind", ["LS1P", "LS2aP", "LS2bP"])
def test_coupler_dimensions_are_tables_c1_and_c2(kind: str) -> None:
    plane = metrology.IEC61094_2_TABLE_C1[kind]
    large = metrology.IEC61094_2_TABLE_C2[kind]
    a, b, c, d, e_min, e_max = ref.IEC61094_2_TABLE_C1_MM[kind]
    assert (
        plane.microphone_diameter_mm,
        plane.front_cavity_diameter_mm,
        plane.coupler_diameter_mm,
        plane.front_cavity_depth_mm,
        plane.coupler_length_range_mm,
    ) == (a, b, c, d, (e_min, e_max))
    a, b, c, d, e, f = ref.IEC61094_2_TABLE_C2_MM[kind]
    assert (
        large.microphone_diameter_mm,
        large.front_cavity_diameter_mm,
        large.coupler_diameter_mm,
        large.front_cavity_depth_mm,
        large.coupler_length_mm,
        large.port_length_mm,
        large.tolerance_mm,
    ) == (a, b, c, d, e, f, ref.IEC61094_2_TABLE_C2_TOLERANCE_MM)


def test_wave_motion_correction_reads_table_c3() -> None:
    frequencies = np.array(sorted(ref.IEC61094_2_TABLE_C3_DB))
    correction = metrology.large_volume_wave_motion_correction(frequencies)
    np.testing.assert_array_equal(
        correction.correction_db, [ref.IEC61094_2_TABLE_C3_DB[f] for f in frequencies]
    )
    assert not np.any(correction.interpolated)


def test_wave_motion_correction_is_nil_up_to_800_hz_and_interpolates() -> None:
    correction = metrology.large_volume_wave_motion_correction([100.0, 500.0, 1100.0])
    assert correction.correction_db[0] == pytest.approx(0.0)
    assert correction.correction_db[1] == pytest.approx(0.0)
    assert -0.013 < correction.correction_db[2] < -0.002
    assert correction.interpolated.tolist() == [False, False, True]


def test_wave_motion_correction_scales_the_frequency_for_another_gas() -> None:
    """C.3: in hydrogen the frequency scale is multiplied by the speed ratio."""
    correction = metrology.large_volume_wave_motion_correction(
        [3780.0, 9450.0], speed_of_sound_ratio=3.78
    )
    np.testing.assert_allclose(correction.correction_db, [-0.002, -0.087])


def test_wave_motion_correction_refuses_above_the_table() -> None:
    with pytest.raises(ValueError, match="2500 Hz"):
        metrology.large_volume_wave_motion_correction([3150.0])


# ---------------------------------------------------------------------------
# Annex E: the microphone
# ---------------------------------------------------------------------------


def test_microphone_lumped_parameters_follow_annex_e() -> None:
    """E.4: (2 pi f0)**2 = 1/(m c), Veq = c kappa_r p_r, d = r 2 pi f0 c."""
    mic = _MICS[0]
    omega = 2.0 * math.pi * mic.resonance_frequency_hz
    assert omega**2 * mic.mass_kg_m4 * mic.compliance_m3_per_pa == pytest.approx(1.0)
    assert mic.resistance_pa_s_m3 * omega * mic.compliance_m3_per_pa == pytest.approx(
        mic.loss_factor
    )
    kappa_r = fluids.air(**_CONDITIONS).heat_capacity_ratio
    assert mic.compliance_m3_per_pa * kappa_r * 101325.0 == pytest.approx(
        mic.equivalent_volume_m3
    )
    impedance = mic.acoustic_impedance_pa_s_m3([mic.resonance_frequency_hz])
    assert impedance[0].imag == pytest.approx(0.0, abs=1e-6 * abs(impedance[0]))
    assert impedance[0].real == pytest.approx(mic.resistance_pa_s_m3)


def test_acoustic_impedance_from_the_admittance_inverts_formula_e1() -> None:
    mic = _MICS[0]
    frequencies = np.array([500.0, 5000.0])
    za = mic.acoustic_impedance_pa_s_m3(frequencies)
    sensitivity = np.array([-0.05 + 0.001j, -0.049 - 0.01j])
    blocked = 1.0 / (1.0j * 2.0 * math.pi * frequencies * 60e-12)
    admittance = 1.0 / (blocked - sensitivity**2 * za)
    np.testing.assert_allclose(
        metrology.microphone_acoustic_impedance(admittance, blocked, sensitivity),
        za,
        rtol=1e-12,
    )


def test_microphone_refuses_a_negative_loss_factor() -> None:
    with pytest.raises(ValueError, match="'loss_factor' must be non-negative"):
        dataclasses.replace(_MICS[0], loss_factor=-0.1)


# ---------------------------------------------------------------------------
# Clause 5: the transfer impedance and the sensitivities
# ---------------------------------------------------------------------------


def test_large_volume_coupler_is_formula_3_at_low_frequency() -> None:
    """Without heat conduction, the compliances of the gas and the two
    microphones in parallel.
    """
    z = metrology.coupler_transfer_impedance(
        [50.0], _LARGE, _MICS[0], _MICS[1], **_CONDITIONS
    )
    gas = _air()
    bores = 2 * math.pi * 0.0186**2 / 4.0 * 0.80e-3
    volume = (
        math.pi * 0.04288**2 / 4.0 * 0.01255
        + bores
        + 2 * _MICS[0].front_cavity_volume_m3
    )
    kappa_r = fluids.air(**_CONDITIONS).heat_capacity_ratio
    admittance = (
        2j
        * math.pi
        * 50.0
        * (
            volume / (gas.heat_capacity_ratio * 101325.0)
            + (
                _MICS[0].complex_equivalent_volume_m3([50.0])[0]
                + _MICS[1].complex_equivalent_volume_m3([50.0])[0]
            )
            / (kappa_r * 101325.0)
        )
    )
    assert z.adiabatic_impedance_pa_s_m3[0] == pytest.approx(
        1.0 / admittance, rel=1e-12
    )
    assert z.heat_conduction is not None
    assert z.heat_conduction_correction_db[0] < 0.0


def test_plane_wave_coupler_is_a_compliance_at_low_frequency() -> None:
    """Formula (4) lossless tends to Formula (3) when the line is short.

    The line's gas has the stiffness rho c**2 of its wave impedance, the excess
    volumes of the front cavities kappa p_s; for Annex F air the two differ by
    4e-4, so each is taken where the formula takes it.
    """
    plane = dataclasses.replace(_PLANE, capillary=None)
    z = metrology.coupler_transfer_impedance(
        [20.0], plane, _MICS[0], _MICS[1], **_CONDITIONS
    )
    gas = _air()
    area = math.pi * 0.0093**2
    depth = _MICS[0].front_cavity_depth_m
    line = area * (7.5e-3 + 2 * depth)
    excess = 2 * (_MICS[0].front_cavity_volume_m3 - area * depth)
    kappa_r = fluids.air(**_CONDITIONS).heat_capacity_ratio
    compliance = (
        line / (gas.density * gas.speed_of_sound**2)
        + excess / (gas.heat_capacity_ratio * 101325.0)
        + (
            _MICS[0].complex_equivalent_volume_m3([20.0])[0]
            + _MICS[1].complex_equivalent_volume_m3([20.0])[0]
        )
        / (kappa_r * 101325.0)
    )
    expected = 1.0 / (2j * math.pi * 20.0 * compliance)
    assert z.adiabatic_impedance_pa_s_m3[0] == pytest.approx(expected, rel=1e-5)
    np.testing.assert_array_equal(z.capillary_correction, [1.0])


def test_the_bores_of_figure_c2_add_to_the_volume_and_the_surface() -> None:
    """Figure C.2: each microphone face sits F back from the cavity, through a
    bore of the front-cavity diameter B.
    """
    pair = (_MICS[0], _MICS[1])
    b, d, f = 18.6e-3, 1.95e-3, 0.80e-3
    cylinder = math.pi * 0.04288**2 / 4.0 * 0.01255
    closed = math.pi * 0.04288 * (0.01255 + 0.04288 / 2.0)
    assert _LARGE.closed_volume_m3(pair) == pytest.approx(
        cylinder + 2 * (math.pi * b**2 / 4.0 * f + 0.534e-6), rel=1e-14
    )
    assert _LARGE.closed_surface_m2(pair) == pytest.approx(
        closed + 2 * math.pi * b * (d + f), rel=1e-14
    )
    flush = dataclasses.replace(_LARGE, port_length_m=0.0)
    assert flush.closed_volume_m3(pair) == pytest.approx(
        cylinder + 2 * 0.534e-6, rel=1e-14
    )


def test_the_bores_of_table_c2_move_each_sensitivity_by_a_tenth_of_a_decibel() -> None:
    """The two bores of the LS1P coupler are 2,4 % of its cavity."""
    flush = dataclasses.replace(_LARGE, capillary=None, port_length_m=0.0)
    bored = dataclasses.replace(_LARGE, capillary=None)
    change = [
        20.0
        * np.log10(
            abs(
                metrology.coupler_transfer_impedance(
                    [250.0], coupler, _MICS[0], _MICS[1], **_CONDITIONS
                ).transfer_impedance_pa_s_m3[0]
            )
        )
        for coupler in (flush, bored)
    ]
    assert change[0] - change[1] == pytest.approx(0.19, abs=0.005)


def test_large_volume_coupler_refuses_a_negative_port() -> None:
    with pytest.raises(ValueError, match="'port_length_m' must be"):
        metrology.LargeVolumeCoupler(
            length_m=12.55e-3, diameter_m=42.88e-3, port_length_m=-1e-4
        )


@pytest.mark.parametrize(
    "conditions",
    [
        _CONDITIONS,
        {
            "temperature_c": 20.0,
            "static_pressure_pa": 95000.0,
            "relative_humidity_percent": 60.0,
        },
    ],
    ids=["reference", "20C-95kPa"],
)
@pytest.mark.parametrize("x", [2.0, 20.0])
def test_large_volume_heat_conduction_is_formulas_3_and_a1_with_table_a1(
    conditions: dict[str, float], x: float
) -> None:
    """Formula (3) with Delta_H of Formula (A.1) and E_V read from Table A.1.

    A coupler of R = 0,5 closed by two microphones, at the frequency where the
    X of A.2 is a printed one. The gas is held by kappa p_s at the conditions
    and the microphones by kappa_r p_s,r at the reference ones, as Formula (3)
    prints them; away from the reference conditions the two differ.
    """
    coupler = metrology.LargeVolumeCoupler(
        length_m=10e-3, diameter_m=20e-3, port_length_m=0.4e-3
    )
    pair = (_MICS[0], _MICS[1])
    gas = fluids.air(**conditions)
    b, d, f_port = 18.6e-3, 1.95e-3, 0.4e-3
    volume = math.pi * 0.02**2 / 4.0 * 0.01 + 2 * (
        0.534e-6 + math.pi * b**2 / 4.0 * f_port
    )
    surface = math.pi * 0.02 * (0.01 + 0.01) + 2 * math.pi * b * (d + f_port)
    kappa = gas.heat_capacity_ratio
    frequency = x * kappa * gas.thermal_diffusivity / (volume / surface) ** 2
    real, imag = ref.IEC61094_2_TABLE_A1[x][1]
    delta_h = kappa / (1.0 + (kappa - 1.0) * complex(real, imag))
    microphones = sum(_equivalent_volume(m, frequency) for m in pair)
    expected = 1.0 / (
        2j
        * math.pi
        * frequency
        * (
            delta_h * volume / (kappa * conditions["static_pressure_pa"])
            + microphones / _REFERENCE_STIFFNESS
        )
    )
    z = metrology.coupler_transfer_impedance([frequency], coupler, *pair, **conditions)
    assert z.heat_conducting_impedance_pa_s_m3[0] == pytest.approx(expected, rel=1e-5)


@pytest.mark.parametrize("frequency", [250.0, 1000.0, 8000.0])
def test_plane_wave_heat_conduction_is_formulas_4_and_a3_to_a5(
    frequency: float,
) -> None:
    """Formula (4) with the propagation coefficient (A.3), the wave impedance
    (A.4) and the end admittance (A.5) added to each microphone admittance,
    written out as A.3 prints them, with the excess volume of each front
    cavity in parallel with its microphone (7.3.3.1).
    """
    gas = _air()
    coupler = dataclasses.replace(_PLANE, capillary=None)
    rho, c, kappa = gas.density, gas.speed_of_sound, gas.heat_capacity_ratio
    eta, alpha_t = gas.viscosity, gas.thermal_diffusivity
    omega = 2.0 * math.pi * frequency
    a = 18.6e-3 / 2.0
    s0 = math.pi * a**2
    loss = (1.0 - 1.0j) / math.sqrt(2.0) / a
    viscous = math.sqrt(eta / (omega * rho))
    thermal = (kappa - 1.0) * math.sqrt(alpha_t / omega)
    gamma = 1j * omega / c * (1.0 + loss * (viscous + thermal))
    z0 = rho * c / s0 * (1.0 + loss * (viscous - thermal))
    end = (
        s0 / (rho * c) * (1.0 + 1.0j) / math.sqrt(2.0) * (kappa - 1.0) / c
    ) * math.sqrt(alpha_t * omega)

    def admittance(mic: metrology.ReciprocityMicrophone) -> complex:
        microphone = (
            1j * omega * _equivalent_volume(mic, frequency) / _REFERENCE_STIFFNESS
        )
        excess = (
            1j
            * omega
            * (mic.front_cavity_volume_m3 - s0 * mic.front_cavity_depth_m)
            / (kappa * 101325.0)
        )
        return microphone + excess + end

    y1, y2 = admittance(_MICS[0]), admittance(_MICS[1])
    l0 = 7.5e-3 + 2 * 1.95e-3
    inverse = (
        (z0 * y1 + z0 * y2) * np.cosh(gamma * l0)
        + (1.0 + z0**2 * y1 * y2) * np.sinh(gamma * l0)
    ) / z0
    z = metrology.coupler_transfer_impedance(
        [frequency], coupler, _MICS[0], _MICS[1], **_CONDITIONS
    )
    assert z.heat_conducting_impedance_pa_s_m3[0] == pytest.approx(
        1.0 / inverse, rel=1e-12
    )


def test_transfer_impedance_does_not_depend_on_which_microphone_transmits() -> None:
    forward = metrology.coupler_transfer_impedance(
        _F, _PLANE, _MICS[0], _MICS[2], **_CONDITIONS
    )
    backward = metrology.coupler_transfer_impedance(
        _F, _PLANE, _MICS[2], _MICS[0], **_CONDITIONS
    )
    np.testing.assert_allclose(
        forward.transfer_impedance_pa_s_m3,
        backward.transfer_impedance_pa_s_m3,
        rtol=1e-12,
    )


def test_capillary_correction_is_formula_6() -> None:
    z = metrology.coupler_transfer_impedance(
        _F, _PLANE, _MICS[0], _MICS[1], **_CONDITIONS
    )
    tube = metrology.capillary_tube_impedance(
        _F, length_m=_TUBES.length_m, radius_m=_TUBES.radius_m, gas=_air()
    )
    expected = 1.0 + 2 * z.heat_conducting_impedance_pa_s_m3 / tube.impedance_pa_s_m3
    np.testing.assert_allclose(z.capillary_correction, expected, rtol=1e-12)
    np.testing.assert_allclose(
        z.transfer_impedance_pa_s_m3,
        z.heat_conducting_impedance_pa_s_m3 / expected,
        rtol=1e-12,
    )


@pytest.mark.parametrize(
    "coupler", [_PLANE, _LARGE], ids=["plane_wave", "large_volume"]
)
def test_three_microphones_give_their_sensitivities_back(
    coupler: metrology.PlaneWaveCoupler | metrology.LargeVolumeCoupler,
) -> None:
    """Formula (2) forward, Formula (7) back: the sensitivities, up to a common
    sign that no reciprocity measurement can fix.
    """
    electrical, acoustic, true = _triad(coupler)
    calibration = metrology.pressure_reciprocity(_F, electrical, acoustic)
    sign = np.sign((calibration.sensitivity_v_per_pa[0, 0] / true[0, 0]).real)
    np.testing.assert_allclose(
        calibration.sensitivity_v_per_pa, sign * true, rtol=1e-12
    )
    assert calibration.method == "three_microphones"
    assert calibration.standard == "IEC 61094-2:2009"
    assert calibration.sensitivity_v_per_pa[0, 0].real >= 0.0


def test_two_microphones_and_a_source_give_their_sensitivities_back() -> None:
    """Formula (8), with the ratio measured against the auxiliary source."""
    electrical, acoustic, true = _triad(_PLANE)
    calibration = metrology.pressure_reciprocity_pair(
        _F, electrical[0], acoustic[0], true[0] / true[1]
    )
    sign = np.sign((calibration.sensitivity_v_per_pa[0, 0] / true[0, 0]).real)
    np.testing.assert_allclose(
        calibration.sensitivity_v_per_pa, sign * true[:2], rtol=1e-12
    )
    assert calibration.microphones == 2


def test_numbers_and_results_give_the_same_calibration() -> None:
    electrical, acoustic, _ = _triad(_PLANE)
    from_results = metrology.pressure_reciprocity(_F, electrical, acoustic)
    from_numbers = metrology.pressure_reciprocity(
        _F, electrical, [z.transfer_impedance_pa_s_m3 for z in acoustic]
    )
    np.testing.assert_array_equal(
        from_results.sensitivity_v_per_pa, from_numbers.sensitivity_v_per_pa
    )


def test_wave_motion_correction_is_added_to_every_level() -> None:
    frequencies = np.array([500.0, 1000.0, 2000.0])
    electrical, acoustic, _ = _triad(_LARGE, frequencies)
    correction = metrology.large_volume_wave_motion_correction(frequencies)
    plain = metrology.pressure_reciprocity(frequencies, electrical, acoustic)
    corrected = metrology.pressure_reciprocity(
        frequencies,
        electrical,
        acoustic,
        corrections_db={"wave motion": correction.correction_db},
    )
    np.testing.assert_allclose(
        corrected.sensitivity_level_db - plain.sensitivity_level_db,
        np.tile(correction.correction_db, (3, 1)),
    )


def test_pressure_reciprocity_needs_three_pairs() -> None:
    electrical, acoustic, _ = _triad(_PLANE)
    with pytest.raises(ValueError, match="Three pairs"):
        metrology.pressure_reciprocity(_F, electrical[:2], acoustic[:2])


def test_pressure_reciprocity_refuses_a_result_at_other_frequencies() -> None:
    electrical, acoustic, _ = _triad(_PLANE)
    other = metrology.coupler_transfer_impedance(
        _F[:3], _PLANE, _MICS[0], _MICS[1], **_CONDITIONS
    )
    with pytest.raises(
        ValueError, match=r"'acoustic_transfer_impedances\[12\]' was computed at"
    ):
        metrology.pressure_reciprocity(_F, electrical, [other, *acoustic[1:]])


def test_pressure_reciprocity_refuses_as_many_frequencies_that_are_others() -> None:
    """The same number of points is not the same frequencies: an impedance of
    other ones would divide each electrical impedance by the wrong value.
    """
    electrical, acoustic, _ = _triad(_PLANE)
    other = metrology.coupler_transfer_impedance(
        _F * 1.5, _PLANE, _MICS[0], _MICS[1], **_CONDITIONS
    )
    with pytest.raises(ValueError, match="computed at other frequencies"):
        metrology.pressure_reciprocity(_F, electrical, [other, *acoustic[1:]])


def test_pressure_reciprocity_pair_refuses_as_many_frequencies_that_are_others() -> (
    None
):
    electrical, _, _ = _triad(_PLANE)
    other = metrology.coupler_transfer_impedance(
        _F * 1.5, _PLANE, _MICS[0], _MICS[1], **_CONDITIONS
    )
    with pytest.raises(ValueError, match="computed at other frequencies"):
        metrology.pressure_reciprocity_pair(_F, electrical[0], other, 1.0)


def test_a_gas_at_another_static_pressure_is_refused() -> None:
    """A fluid's density and speed of sound hold at its own pressure; the
    stiffness of the gas is taken at the calibration's, so the two must agree.
    """
    gas = fluids.air(
        temperature_c=23.0, static_pressure_pa=101325.0, relative_humidity_percent=50.0
    )
    with pytest.raises(ValueError, match="'gas' holds at 101325 Pa"):
        metrology.coupler_transfer_impedance(
            _F,
            _PLANE,
            _MICS[0],
            _MICS[1],
            temperature_c=23.0,
            static_pressure_pa=95000.0,
            relative_humidity_percent=50.0,
            gas=gas,
        )


def test_check_coupler_refuses_a_gas_at_another_static_pressure() -> None:
    gas = fluids.air(
        temperature_c=23.0, static_pressure_pa=101325.0, relative_humidity_percent=50.0
    )
    with pytest.raises(ValueError, match="'gas' holds at 101325 Pa"):
        metrology.check_coupler(
            _F,
            _PLANE,
            _MICS,
            temperature_c=23.0,
            static_pressure_pa=95000.0,
            relative_humidity_percent=50.0,
            gas=gas,
        )


def test_another_gas_changes_the_transfer_impedance() -> None:
    """7.3.2.1: the coupler may be filled with hydrogen or helium."""
    helium = fluids.Fluid(
        temperature_c=23.0,
        static_pressure_pa=101325.0,
        composition={},
        model="test helium",
        validity="",
        properties={
            "density": 0.1645,
            "speed_of_sound": 1007.0,
            "heat_capacity_ratio": 1.667,
            "viscosity": 1.99e-5,
            "thermal_diffusivity": 1.8e-4,
        },
    )
    air = metrology.coupler_transfer_impedance(
        [5000.0], _PLANE, _MICS[0], _MICS[1], **_CONDITIONS
    )
    gas = metrology.coupler_transfer_impedance(
        [5000.0], _PLANE, _MICS[0], _MICS[1], **_CONDITIONS, gas=helium
    )
    assert abs(gas.transfer_impedance_pa_s_m3[0]) != pytest.approx(
        abs(air.transfer_impedance_pa_s_m3[0]), rel=1e-3
    )


# ---------------------------------------------------------------------------
# What the formulas require
# ---------------------------------------------------------------------------


def test_plane_wave_check_reports_the_recommended_ratio_without_failing() -> None:
    """C.2: l0/D of 0,5 to 0,75, with l0 between the diaphragms (5.4)."""
    check = metrology.check_coupler(_F, _PLANE, _MICS, **_CONDITIONS)
    assert check.length_to_diameter_ratio == pytest.approx((7.5 + 2 * 1.95) / 18.6)
    assert check.ratio_recommended is True
    short = dataclasses.replace(_PLANE, length_m=2.0e-3)
    short_check = metrology.check_coupler(_F, short, _MICS, **_CONDITIONS)
    assert short_check.ratio_recommended is False
    assert short_check.broadband_valid is True
    assert short_check.passes


def test_plane_wave_check_fails_below_the_broadband_range() -> None:
    check = metrology.check_coupler([1.0, 10.0], _PLANE, _MICS, **_CONDITIONS)
    assert check.broadband_valid is False
    assert not check.passes


def test_large_volume_check_advises_the_full_solution_below_20_hz() -> None:
    """A.2: below 20 Hz the full solution "shall be used, or the corresponding
    uncertainty component shall be increased accordingly": advice, with the
    approximation itself still within its R and X.
    """
    check = metrology.check_coupler(
        [10.0, 100.0],
        _LARGE,
        _MICS,
        **_CONDITIONS,
        heat_conduction_method="approximation",
    )
    assert check.lowest_x is not None
    assert check.lowest_x > 5.0
    assert check.approximation_valid is True
    assert check.full_solution_advised is True
    assert check.passes
    above = metrology.check_coupler(
        [20.0, 100.0],
        _LARGE,
        _MICS,
        **_CONDITIONS,
        heat_conduction_method="approximation",
    )
    assert above.full_solution_advised is False
    exact = metrology.check_coupler([10.0, 100.0], _LARGE, _MICS, **_CONDITIONS)
    assert exact.approximation_valid is None
    assert exact.full_solution_advised is None
    assert exact.passes


def test_large_volume_check_holds_the_approximation_to_x_above_5() -> None:
    """A.2 states the accuracy of (A.2) for X > 5, which fails at 2 Hz."""
    check = metrology.check_coupler(
        [2.0, 100.0],
        _LARGE,
        _MICS,
        **_CONDITIONS,
        heat_conduction_method="approximation",
    )
    assert check.approximation_valid is False
    assert not check.passes


def test_check_coupler_needs_two_microphones() -> None:
    one = _MICS[:1]
    with pytest.raises(ValueError, match="closed by two microphones"):
        metrology.check_coupler(_F, _PLANE, one, **_CONDITIONS)


@pytest.mark.parametrize(
    ("kind", "below_hz", "above_hz"),
    [("LS1P", 2.8, 2.9), ("LS2aP", 11.3, 11.4)],
)
def test_check_holds_formulas_a3_and_a4_to_their_bound(
    kind: str, below_hz: float, above_hz: float
) -> None:
    """omega rho a**2 > 100 eta at 2,83 Hz and 11,34 Hz in the couplers of
    Table C.1, which A.3 prints rounded up as 3 Hz and 12 Hz.
    """
    _, b, c, d, _, _ = ref.IEC61094_2_TABLE_C1_MM[kind]
    coupler = metrology.PlaneWaveCoupler(length_m=5e-3, diameter_m=c / 1000.0)
    mic = dataclasses.replace(
        _MICS[0], front_cavity_depth_m=d / 1000.0, front_cavity_diameter_m=b / 1000.0
    )
    low = metrology.check_coupler([below_hz], coupler, (mic, mic), **_CONDITIONS)
    high = metrology.check_coupler([above_hz], coupler, (mic, mic), **_CONDITIONS)
    assert low.broadband_valid is False
    assert high.broadband_valid is True


def test_check_reads_the_annex_f_domain() -> None:
    with pytest.warns(fluids.FluidWarning, match="outside the domain"):
        check = metrology.check_coupler(
            _F,
            _PLANE,
            _MICS,
            temperature_c=30.0,
            static_pressure_pa=101325.0,
            relative_humidity_percent=50.0,
        )
    assert check.conditions_valid is False
    assert not check.passes


def test_coupler_check_has_no_truth_value() -> None:
    check = metrology.check_coupler(_F, _PLANE, _MICS, **_CONDITIONS)
    with pytest.raises(TypeError, match="passes"):
        bool(check)


# ---------------------------------------------------------------------------
# Clause 7.5: one parameter at a time
# ---------------------------------------------------------------------------


def test_parameter_uncertainty_returns_one_component_per_parameter() -> None:
    result = metrology.coupler_parameter_uncertainty(
        _F,
        _PLANE,
        _MICS,
        metrology.CouplerInputUncertainties(
            u_coupler_length_m=5e-6,
            u_temperature_k=0.05,
            u_capillary_radius_m=1e-6,
            u_equivalent_volume_m3=1e-9,
        ),
        **_CONDITIONS,
    )
    assert set(result.components_db) == {
        "coupler_length",
        "temperature",
        "capillary_tube_dimensions",
        "equivalent_volume",
    }
    assert set(result.components_db) <= set(metrology.IEC61094_2_TABLE_1)
    for values in result.components_db.values():
        assert np.all(values >= 0.0)
        assert np.any(values > 0.0)


def test_parameter_uncertainty_of_the_length_is_the_level_change() -> None:
    """The component is the change of 20 lg|M1| by Formula (7)."""
    u = 5e-6
    result = metrology.coupler_parameter_uncertainty(
        _F,
        _PLANE,
        _MICS,
        metrology.CouplerInputUncertainties(u_coupler_length_m=u),
        **_CONDITIONS,
    )
    electrical, acoustic, _ = _triad(_PLANE)
    longer = dataclasses.replace(_PLANE, length_m=_PLANE.length_m + u)
    moved = [
        metrology.coupler_transfer_impedance(
            _F, longer, _MICS[i], _MICS[j], **_CONDITIONS
        )
        for i, j in ((0, 1), (1, 2), (2, 0))
    ]
    nominal = metrology.pressure_reciprocity(_F, electrical, acoustic)
    changed = metrology.pressure_reciprocity(_F, electrical, moved)
    np.testing.assert_allclose(
        result.components_db["coupler_length"],
        np.abs(changed.sensitivity_level_db[0] - nominal.sensitivity_level_db[0]),
        atol=1e-12,
    )


def test_parameter_uncertainty_refuses_the_volume_of_a_plane_wave_coupler() -> None:
    uncertainties = metrology.CouplerInputUncertainties(u_coupler_volume_m3=1e-9)
    with pytest.raises(ValueError, match="plane-wave coupler"):
        metrology.coupler_parameter_uncertainty(
            _F, _PLANE, _MICS, uncertainties, **_CONDITIONS
        )


def test_parameter_uncertainty_refuses_tubes_the_coupler_does_not_have() -> None:
    plane = dataclasses.replace(_PLANE, capillary=None)
    uncertainties = metrology.CouplerInputUncertainties(u_capillary_length_m=1e-4)
    with pytest.raises(ValueError, match="no capillary tubes"):
        metrology.coupler_parameter_uncertainty(
            _F, plane, _MICS, uncertainties, **_CONDITIONS
        )


def test_parameter_uncertainty_follows_the_gas_of_the_coupler() -> None:
    """7.3.2.1 allows another gas: the components follow it, as the impedance does."""
    uncertainties = metrology.CouplerInputUncertainties(u_coupler_length_m=1e-5)
    in_air = metrology.coupler_parameter_uncertainty(
        _F, _PLANE, _MICS, uncertainties, **_CONDITIONS
    )
    same_air = metrology.coupler_parameter_uncertainty(
        _F, _PLANE, _MICS, uncertainties, **_CONDITIONS, gas=_air()
    )
    warmer = fluids.air(
        temperature_c=40.0,
        static_pressure_pa=_CONDITIONS["static_pressure_pa"],
        relative_humidity_percent=_CONDITIONS["relative_humidity_percent"],
    )
    other_gas = metrology.coupler_parameter_uncertainty(
        _F, _PLANE, _MICS, uncertainties, **_CONDITIONS, gas=warmer
    )
    key = "coupler_length"
    np.testing.assert_allclose(
        same_air.components_db[key], in_air.components_db[key], rtol=1e-12
    )
    assert not np.allclose(
        other_gas.components_db[key], in_air.components_db[key], rtol=1e-6
    )


@pytest.mark.parametrize(
    "uncertainties",
    [
        metrology.CouplerInputUncertainties(u_static_pressure_pa=50.0),
        metrology.CouplerInputUncertainties(u_temperature_k=0.1),
        metrology.CouplerInputUncertainties(u_relative_humidity_percent=2.0),
    ],
    ids=["static-pressure", "temperature", "humidity"],
)
def test_parameter_uncertainty_refuses_conditions_a_given_gas_ignores(
    uncertainties: metrology.CouplerInputUncertainties,
) -> None:
    gas = _air()
    with pytest.raises(ValueError, match="cannot move them"):
        metrology.coupler_parameter_uncertainty(
            _F, _PLANE, _MICS, uncertainties, **_CONDITIONS, gas=gas
        )


def test_parameter_uncertainty_refuses_a_fourth_microphone() -> None:
    uncertainties = metrology.CouplerInputUncertainties()
    with pytest.raises(ValueError, match="'microphone' must be"):
        metrology.coupler_parameter_uncertainty(
            _F, _PLANE, _MICS, uncertainties, **_CONDITIONS, microphone=4
        )


@pytest.mark.parametrize("value", [-1e-6, float("nan"), float("inf")])
def test_input_uncertainties_refuse_what_is_not_a_standard_uncertainty(
    value: float,
) -> None:
    with pytest.raises(ValueError, match="'u_temperature_k' must be non-negative"):
        metrology.CouplerInputUncertainties(u_temperature_k=value)


def test_input_uncertainties_are_keyword_only_and_default_to_zero() -> None:
    nothing = metrology.CouplerInputUncertainties()
    assert all(
        getattr(nothing, item.name) == 0.0 for item in dataclasses.fields(nothing)
    )
    with pytest.raises(TypeError):
        metrology.CouplerInputUncertainties(5e-6)  # type: ignore[call-arg]
    result = metrology.coupler_parameter_uncertainty(
        _F, _PLANE, _MICS, nothing, **_CONDITIONS
    )
    assert dict(result.components_db) == {}


def test_large_volume_parameters_move_the_volume_and_the_surface() -> None:
    result = metrology.coupler_parameter_uncertainty(
        [100.0, 500.0],
        _LARGE,
        _MICS,
        metrology.CouplerInputUncertainties(
            u_coupler_volume_m3=1e-9, u_coupler_surface_area_m2=1e-6
        ),
        **_CONDITIONS,
    )
    assert np.all(result.components_db["coupler_volume"] > 0.0)
    assert np.all(result.components_db["coupler_surface_area"] > 0.0)


def test_published_tables_are_read_only() -> None:
    with pytest.raises(TypeError):
        rc.IEC61094_2_TABLE_C3[800.0] = 1.0  # type: ignore[index]
    z = metrology.coupler_transfer_impedance(
        _F, _PLANE, _MICS[0], _MICS[1], **_CONDITIONS
    )
    with pytest.raises(ValueError, match="read-only"):
        z.capillary_correction[0] = 2.0
