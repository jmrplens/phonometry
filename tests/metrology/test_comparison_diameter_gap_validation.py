#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 61094-5:2016 6.5, 6.7 and Table D.1: microphones of different
diameters, the air between two microphones in a coupler, and the validation
of a jig or a coupler.

6.5 refers the correction for microphones of different diameters to its
reference [1], Barham, Barrera-Figueroa and Avison, Metrologia 51 (2014)
129, whose Table 2 (page 135, PDF page 8 of the downloaded file) is Table A.1
of the part. The model is checked against those printed corrections, and its
closed form against a numerical quadrature of Formula (5). Table D.1 and 7.4
refer the air between two microphones to reference [2], Jarvis, NPL Report
CIRA(EXT) 010 (1996), whose Appendix B (folios 25 to 27, PDF pages 28 to 30)
prints a circuit, its parameters and the graph of the error it causes: the
series impedance is checked against the ratio Appendix B prints, evaluated
here independently, and against the extremes of the printed graph. 6.7 prints
no criterion, so the validation is checked against its definition, and its
shared part against the GUM: the covariance of two estimates through a
common quantity (JCGM 100:2008 F.1.2.3, Formula (F.2)), worked by hand on
the budget of Table D.1, and the correlation coefficients F.1.2.3 Example 2
prints for two items calibrated against the same standard. The printed
values are read from ``tests/reference_data``.
"""

from __future__ import annotations

import math

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref
from scipy import integrate, special

from phonometry import metrology
from phonometry.fluids import Fluid
from phonometry.metrology import comparison_calibration as cc

#: Barham et al. (2014) Table 1, the inputs for an LS2 reference and a WS3
#: test microphone, in SI units.
_TABLE_1 = ref.BARHAM_2014_TABLE_1
_WS3 = {
    "reference_radius_m": _TABLE_1["ls2_front_cavity_radius_mm"] / 1000.0,
    "test_diaphragm_radius_m": _TABLE_1["ws3_diaphragm_radius_mm"] / 1000.0,
    "test_outer_radius_m": _TABLE_1["ws3_overall_radius_mm"] / 1000.0,
    "separation_m": _TABLE_1["diaphragm_separation_mm"] / 1000.0,
    "reference_resonance_frequency_hz": 1000.0
    * _TABLE_1["ls2_resonance_frequency_khz"],
    "test_resonance_frequency_hz": 1000.0 * _TABLE_1["ws3_resonance_frequency_khz"],
}

#: IEC 61094-5:2016 Table A.1 (folio 15), keyed in Hz, in dB.
_TABLE_A1 = {1000.0 * khz: value for khz, value in ref.IEC61094_5_TABLE_A1_DB.items()}
_F_A1 = np.array(sorted(_TABLE_A1))
_PRINTED_A1 = np.array([_TABLE_A1[f] for f in _F_A1])


def _sound(speed_of_sound: float) -> Fluid:
    """A gas of a given speed of sound at the reference static pressure."""
    return Fluid(
        temperature_c=23.0,
        static_pressure_pa=101325.0,
        composition={},
        model="test",
        validity="test",
        properties={"speed_of_sound": speed_of_sound},
    )


#: Jarvis (1996) Appendix B, folio 25: the density, the ratio of specific
#: heats and the static pressure "taken to be".
_RHO, _KAPPA, _P0 = ref.JARVIS_1996_AIR
_JARVIS_AIR = Fluid(
    temperature_c=23.0,
    static_pressure_pa=_P0,
    composition={},
    model="Jarvis 1996, Appendix B",
    validity="test",
    properties={"density": _RHO, "heat_capacity_ratio": _KAPPA},
)

#: Appendix B, folio 25: an LS2P (r1, c1, m1) and a high sensitivity WS2P
#: (r2, c2, m2), N s m^-5, N^-1 m^5 and kg m^-4.
_LS2P = ref.JARVIS_1996_LS2P
_WS2P = ref.JARVIS_1996_WS2P

#: Appendix B, folio 26: the tube of the coupler, L = .002 m and r = 1.27e-2/2 m.
_LENGTH, _RADIUS = ref.JARVIS_1996_TUBE
_GAP = {"gap_length_m": _LENGTH, "gap_radius_m": _RADIUS}

#: IEC 61094-1:2000 6.2.2, kappa_r p_s,r with kappa_r = 1,40: what turns an
#: impedance into an equivalent volume.
_KAPPA_P = ref.IEC61094_1_KAPPA_REFERENCE * 101325.0


def _impedance(omega: np.ndarray, parameters: tuple[float, float, float]) -> np.ndarray:
    """Z_m = r + i w m + 1/(i w c), Appendix B, folio 25."""
    resistance, compliance, mass = parameters
    return resistance + 1j * omega * mass + 1.0 / (1j * omega * compliance)


def _jarvis_ratio(frequencies: np.ndarray) -> np.ndarray:
    """R = P1/P2 exactly as Appendix B prints it on folio 26, the ladder of
    Z_s, Z_o, Z_L and Z_c, with no reduction to an equivalent circuit.
    """
    omega = 2.0 * np.pi * frequencies
    v = math.pi * _RADIUS**2 * _LENGTH
    zc = _KAPPA * _P0 / (1j * omega * v / 2.0)
    zl = (_RHO * (_LENGTH / 4.0) / (math.pi * _RADIUS**2)) * 1j * omega / 3.0
    zm1 = _impedance(omega, _LS2P)
    zm2 = _impedance(omega, _WS2P)
    zs1 = zc * (zl + zm1) / (zc + zl + zm1)
    zs2 = zc * (zl + zm2) / (zc + zl + zm2)
    zo1 = zl + zs1
    zo2 = zl + zs2
    return zs1 * zm1 / (zo1 * (zl + zm1)) * zo2 * (zl + zm2) / (zs2 * zm2)


def _library_ratio(frequencies: np.ndarray) -> cc.ImpedancePressureRatio:
    """The same coupler through the library: the series impedance of the air
    and the divider of impedance_pressure_ratio, the LS2P the reference.
    """
    omega = 2.0 * np.pi * frequencies
    series = metrology.air_gap_series_impedance_pa_s_m3(
        frequencies, gas=_JARVIS_AIR, **_GAP
    )
    return metrology.impedance_pressure_ratio(
        frequencies,
        reference_equivalent_volume_m3=_KAPPA_P
        / (1j * omega * _impedance(omega, _LS2P)),
        test_equivalent_volume_m3=_KAPPA_P / (1j * omega * _impedance(omega, _WS2P)),
        coupling_impedance_pa_s_m3=series,
    )


# ---------------------------------------------------------------------------
# 6.5: microphones of different diameters
# ---------------------------------------------------------------------------


def test_barham_table_2_is_table_a1() -> None:
    """Barham et al. (2014) Table 2, its calculated column, is Table A.1 of
    the part row by row: the two transcriptions agree.
    """
    assert ref.BARHAM_2014_TABLE_2_CALCULATED_DB == _TABLE_A1


def test_model_reproduces_every_row_of_table_a1_at_its_speed_of_sound() -> None:
    """At 344,8 m/s every correction of Table A.1 to the thousandth of a
    decibel the table prints. The paper prints no speed of sound.
    """
    printed = ref.BARHAM_2014_TABLE_2_CALCULATED_DB
    frequencies = np.array(sorted(printed))
    result = metrology.diameter_sound_field_correction(
        frequencies, gas=_sound(ref.BARHAM_2014_SPEED_OF_SOUND), **_WS3
    )
    expected = np.array([printed[f] for f in frequencies])
    assert np.max(np.abs(result.correction_db - expected)) <= 0.0005


def test_model_at_the_reference_air_is_within_a_hundredth_of_table_a1() -> None:
    """At the reference air of clause 4, within 0,01 dB of every row, far
    inside the 10 % expanded uncertainty of the NOTE to Table A.1.
    """
    result = metrology.diameter_sound_field_correction(_F_A1, **_WS3)
    deviation = np.abs(result.correction_db - _PRINTED_A1)
    assert result.speed_of_sound == pytest.approx(345.87, abs=0.01)
    assert np.max(deviation) < 0.01
    assert np.all(deviation < 0.1 * np.abs(_PRINTED_A1))


def _quadrature_ratio(frequency: float, speed: float, modes: int = 120) -> complex:
    """Formula (5) by numerical quadrature of the series of Formula (3), with
    the radial sensitivity J0(K r) - J0(K R) and the annulus from the outer
    radius: an evaluation independent of the library's Lommel integrals.
    """
    a = _WS3["reference_radius_m"]
    b = _WS3["test_diaphragm_radius_m"]
    outer = _WS3["test_outer_radius_m"]
    length = _WS3["separation_m"]
    roots = np.concatenate(([0.0], special.jn_zeros(1, modes)))
    weights = np.empty_like(roots)
    weights[0] = 1.0 - (outer / a) ** 2
    weights[1:] = [
        integrate.quad(lambda r, k=k: special.j0(k * r / a) * r, outer, a)[0]
        * 2.0
        / (a**2 * special.j0(k) ** 2)
        for k in roots[1:]
    ]
    omega = 2.0 * math.pi * frequency
    mu = np.sqrt((roots / a) ** 2 - (omega / speed) ** 2 + 0j)
    amplitude = weights / (mu * np.sinh(mu * length))

    def pressure(r: float, z: float) -> complex:
        return complex(np.sum(amplitude * np.cosh(mu * z) * special.j0(roots * r / a)))

    def average(radius: float, resonance: float, z: float) -> complex:
        k = 2.404825557695773 * (frequency / resonance) / radius

        def weight(r: float) -> float:
            return float(special.j0(k * r) - special.j0(k * radius))

        real = integrate.quad(
            lambda r: weight(r) * pressure(r, z).real * r, 0.0, radius, limit=200
        )[0]
        imag = integrate.quad(
            lambda r: weight(r) * pressure(r, z).imag * r, 0.0, radius, limit=200
        )[0]
        norm = integrate.quad(lambda r: weight(r) * r, 0.0, radius)[0]
        return complex(real, imag) / norm

    reference = average(a, _WS3["reference_resonance_frequency_hz"], 0.0)
    test = average(b, _WS3["test_resonance_frequency_hz"], length)
    return test / reference


@pytest.mark.parametrize("frequency", [2000.0, 16000.0])
def test_closed_form_matches_a_quadrature_of_formula_5(frequency: float) -> None:
    """The library's closed form against the integral of Formula (5) taken
    numerically over the same truncated series.
    """
    expected = _quadrature_ratio(frequency, 345.0)
    computed = metrology.diameter_sound_field_correction(
        [frequency], gas=_sound(345.0), **_WS3
    ).ratio[0]
    assert abs(computed / expected - 1.0) < 1e-6


def test_doubled_separation_is_the_model_at_twice_the_distance() -> None:
    """The second ratio is the model with the separation doubled, and the
    change between the two is the magnitude of their difference.
    """
    single = metrology.diameter_sound_field_correction(_F_A1, **_WS3)
    doubled = metrology.diameter_sound_field_correction(
        _F_A1, **{**_WS3, "separation_m": 2.0 * _WS3["separation_m"]}
    )
    np.testing.assert_allclose(
        single.doubled_separation_correction_db, doubled.correction_db, rtol=1e-12
    )
    np.testing.assert_allclose(
        single.separation_change_db,
        np.abs(doubled.correction_db - single.correction_db),
        rtol=1e-12,
    )
    # A regression pin of the model's own output, not a value any source
    # prints: by the model the change on doubling is 6,3 % of the correction
    # at 1 kHz and 5,4 % at 20 kHz, where A.2 observed "approximately" 10 %.
    share = single.separation_change_db / np.abs(single.correction_db)
    assert share[0] == pytest.approx(0.0630, abs=5e-4)
    assert share[-1] == pytest.approx(0.0536, abs=5e-4)


def test_correction_vanishes_at_low_frequency() -> None:
    """Far below the radial modes the gap is a uniform pressure."""
    result = metrology.diameter_sound_field_correction([20.0, 100.0], **_WS3)
    assert np.all(np.abs(result.correction_db) < 1e-4)
    assert np.all(np.abs(result.phase_difference_deg) < 1e-3)


def test_result_arrays_are_read_only() -> None:
    result = metrology.diameter_sound_field_correction(_F_A1, **_WS3)
    for name in ("frequencies_hz", "ratio", "doubled_separation_ratio"):
        assert not getattr(result, name).flags.writeable


@pytest.mark.parametrize(
    ("changes", "match"),
    [
        ({"test_outer_radius_m": _WS3["reference_radius_m"]}, "fit inside"),
        ({"test_diaphragm_radius_m": 3.0e-3}, "fit inside"),
        ({"separation_m": 0.0}, "separation_m"),
        ({"reference_resonance_frequency_hz": 20000.0}, "reference_resonance"),
        ({"test_resonance_frequency_hz": 16000.0}, "test_resonance"),
    ],
)
def test_diameter_correction_refusals(changes: dict[str, float], match: str) -> None:
    arguments = {**_WS3, **changes}
    with pytest.raises(ValueError, match=match):
        metrology.diameter_sound_field_correction(_F_A1, **arguments)


def test_half_wave_gap_returns_the_finite_ratio() -> None:
    """At c/2L the plane mode of a gap closed at both ends resonates without
    loss; the pressures grow without bound but their ratio does not, and the
    plane mode then gives R_P = -1. A 10 mm gap, its first half-wave
    resonance at 17,25 kHz, below both resonance frequencies.
    """
    speed = 345.0
    separation = 0.01
    half_wave = speed / (2.0 * separation)
    resonances = {
        "reference_resonance_frequency_hz": 1.0e6,
        "test_resonance_frequency_hz": 1.0e6,
    }
    arguments = {**_WS3, **resonances, "separation_m": separation}
    result = metrology.diameter_sound_field_correction(
        [0.999 * half_wave, half_wave, 1.001 * half_wave],
        gas=_sound(speed),
        **arguments,
    )
    assert np.all(np.isfinite(result.ratio))
    assert result.ratio[1] == pytest.approx(-1.0, abs=1e-9)


def test_mode_exactly_at_its_cut_off_is_refused() -> None:
    """A frequency whose wavenumber squared underflows puts the plane mode
    exactly at its cut-off, mu = 0, where the lossless model has no finite
    pressure.
    """
    with pytest.raises(ValueError, match="exactly at its cut-off"):
        metrology.diameter_sound_field_correction([1e-170], **_WS3)


def test_gas_at_another_pressure_is_refused() -> None:
    gas = Fluid(
        temperature_c=23.0,
        static_pressure_pa=90000.0,
        composition={},
        model="test",
        validity="test",
        properties={"speed_of_sound": 345.0},
    )
    with pytest.raises(ValueError, match="'gas' holds at"):
        metrology.diameter_sound_field_correction(_F_A1, gas=gas, **_WS3)


def test_diameter_plot_draws_both_corrections() -> None:
    result = metrology.diameter_sound_field_correction(_F_A1, **_WS3)
    ax = result.plot(language="es")
    lines = {line.get_label(): line for line in ax.get_lines()}
    correction = lines[r"Corrección, $-20\lg|R_P|$"]
    np.testing.assert_allclose(correction.get_ydata(), result.correction_db)
    doubled = next(line for label, line in lines.items() if "2L" in label)
    np.testing.assert_allclose(
        doubled.get_ydata(), result.doubled_separation_correction_db
    )
    assert "Micrófonos de distinto diámetro" in ax.get_title()
    assert "4,650" in ax.get_title()
    plt.close(ax.figure)


# ---------------------------------------------------------------------------
# Table D.1 and 7.4: the air between two microphones (Jarvis 1996)
# ---------------------------------------------------------------------------


def test_series_impedance_gives_the_ratio_appendix_b_prints() -> None:
    """The divider with the series impedance is Appendix B's ladder exactly:
    the library's R_P, the WS2P re the LS2P, is the inverse of the printed
    R = P1/P2 at every frequency of its graph.
    """
    frequencies = np.arange(100.0, 20000.0 + 1.0, 100.0)
    ratio = _library_ratio(frequencies)
    np.testing.assert_allclose(
        1.0 / np.asarray(ratio.ratio), _jarvis_ratio(frequencies), rtol=1e-12
    )


def test_error_matches_the_printed_graph() -> None:
    """Folio 27: the error in the sensitivity level, 20 lg|R|, dips to about
    -0,0065 dB near 7 kHz and reaches about 0,025 dB at 20 kHz; the error in
    phase peaks at about 0,16 degrees near 12,5 kHz and ends at about
    0,09 degrees at 20 kHz, where the mass term read without its imaginary
    unit would end at 0,117 degrees.
    """
    frequencies = np.arange(100.0, 20000.0 + 1.0, 100.0)
    ratio = _library_ratio(frequencies)
    error = -np.asarray(ratio.level_difference_db)
    phase = -np.asarray(ratio.phase_difference_deg)
    dip, dip_hz = ref.JARVIS_1996_GRAPH_DIP
    peak_deg, peak_hz = ref.JARVIS_1996_GRAPH_PHASE_PEAK
    lowest = int(np.argmin(error))
    assert error[lowest] == pytest.approx(dip, abs=0.0005)
    assert dip_hz - 1000.0 <= frequencies[lowest] <= dip_hz + 1000.0
    assert error[-1] == pytest.approx(ref.JARVIS_1996_GRAPH_AT_20KHZ_DB, abs=0.001)
    peak = int(np.argmax(phase))
    assert phase[peak] == pytest.approx(peak_deg, abs=0.01)
    assert peak_hz - 1500.0 <= frequencies[peak] <= peak_hz + 1500.0
    assert phase[-1] == pytest.approx(
        ref.JARVIS_1996_GRAPH_PHASE_AT_20KHZ_DEG, abs=0.01
    )


def test_series_impedance_closed_form() -> None:
    """Z_x = Z_L + Z_L Z_c/(Z_L + Z_c) with the compliance of half the
    volume and a third of the mass of a quarter of the length.
    """
    frequencies = np.array([1000.0, 10000.0])
    omega = 2.0 * np.pi * frequencies
    volume = math.pi * _RADIUS**2 * _LENGTH
    assert volume == pytest.approx(ref.JARVIS_1996_VOLUME_M3, abs=0.0005e-7)
    zc = _KAPPA * _P0 / (1j * omega * volume / 2.0)
    zl = 1j * omega * _RHO * _LENGTH / (12.0 * math.pi * _RADIUS**2)
    expected = zl + zl * zc / (zl + zc)
    computed = metrology.air_gap_series_impedance_pa_s_m3(
        frequencies, gas=_JARVIS_AIR, **_GAP
    )
    np.testing.assert_allclose(computed, expected, rtol=1e-12)
    assert not computed.flags.writeable


def test_series_impedance_defaults_to_the_reference_air() -> None:
    """Without a gas, the IEC 61094-2 Annex F air at the reference conditions
    of clause 4.
    """
    from phonometry.fluids import air

    reference = air(
        temperature_c=23.0, static_pressure_pa=101325.0, relative_humidity_percent=50.0
    )
    air_gas = Fluid(
        temperature_c=23.0,
        static_pressure_pa=101325.0,
        composition={},
        model="test",
        validity="test",
        properties={
            "density": reference.density,
            "heat_capacity_ratio": reference.heat_capacity_ratio,
        },
    )
    np.testing.assert_allclose(
        metrology.air_gap_series_impedance_pa_s_m3([2000.0], **_GAP),
        metrology.air_gap_series_impedance_pa_s_m3([2000.0], gas=air_gas, **_GAP),
        rtol=1e-12,
    )


@pytest.mark.parametrize(
    ("changes", "match"),
    [({"gap_length_m": 0.0}, "gap_length_m"), ({"gap_radius_m": -1.0}, "gap_radius_m")],
)
def test_series_impedance_refusals(changes: dict[str, float], match: str) -> None:
    arguments = {**_GAP, **changes}
    with pytest.raises(ValueError, match=match):
        metrology.air_gap_series_impedance_pa_s_m3([1000.0], **arguments)


# ---------------------------------------------------------------------------
# 6.7: the validation of a jig or a coupler
# ---------------------------------------------------------------------------

_F_VAL = np.array([1000.0, 2000.0, 4000.0, 8000.0])


def _comparison(
    level_db: np.ndarray,
    uncertainty_db: float | np.ndarray,
    frequencies: np.ndarray = _F_VAL,
) -> cc.ComparisonCalibration:
    """A pressure calibration whose sensitivity level is ``level_db``: the
    reference at -38 dB and the two readings of the interchange.
    """
    half = -38.0 - np.asarray(level_db)
    return metrology.simultaneous_comparison(
        frequencies, -38.0, half, -half, expanded_uncertainty_db=uncertainty_db
    )


def _reciprocity(
    frequencies: np.ndarray,
    level_db: float | np.ndarray,
    uncertainty_db: float | np.ndarray,
    field: str = "pressure",
) -> metrology.ReciprocityCalibration:
    """A three-microphone reciprocity calibration whose second microphone has
    ``level_db``, one value or one per frequency.
    """
    from phonometry.metrology.reciprocity_calibration import ReciprocityCalibration

    count = frequencies.size
    levels = np.vstack(
        [
            np.full(count, -38.2),
            np.broadcast_to(np.asarray(level_db, dtype=np.float64), (count,)),
            np.full(count, -37.9),
        ]
    )
    sensitivities = 10.0 ** (levels / 20.0)
    products = np.vstack(
        [
            sensitivities[0] * sensitivities[1],
            sensitivities[1] * sensitivities[2],
            sensitivities[2] * sensitivities[0],
        ]
    )
    return ReciprocityCalibration(
        frequencies_hz=frequencies,
        sensitivity_v_per_pa=sensitivities.astype(np.complex128),
        products_v2_per_pa2=products.astype(np.complex128),
        field=field,
        method="three_microphones",
        corrections_db={},
        expanded_uncertainty_db=uncertainty_db,
    )


def test_agreement_is_within_the_root_sum_square() -> None:
    """|Delta| <= sqrt(U1^2 + U2^2): 0,1 dB apart with 0,06 dB and 0,08 dB
    is on the limit and agrees; 0,11 dB apart does not.
    """
    jig = _comparison(np.array([-26.3, -26.3, -26.3, -26.3]), 0.06)
    other = _comparison(np.array([-26.4, -26.41, -26.3, -26.3]), 0.08)
    result = metrology.verify_jig_or_coupler(jig, other)
    np.testing.assert_allclose(result.expanded_uncertainty_db, 0.1, rtol=1e-12)
    np.testing.assert_allclose(result.difference_db, [0.1, 0.11, 0.0, 0.0], atol=1e-12)
    assert result.agrees.tolist() == [True, False, True, True]
    assert result.failing_frequencies_hz.tolist() == [2000.0]
    assert not result.passes
    assert result.validation == "comparison"
    np.testing.assert_allclose(
        result.normalised_difference, [1.0, 1.1, 0.0, 0.0], atol=1e-9
    )


def test_settling_decides_a_difference_on_the_limit() -> None:
    """-26,9 dB against -27,0 dB is 0,1 dB apart, but the subtraction lands a
    few units in the last place above the 0,1 dB root-sum-square of 0,08 dB
    and 0,06 dB: only the settling to a nanodecibel keeps it on the limit.
    """
    on_the_limit = cc.JigCouplerVerification(
        frequencies_hz=np.array([1000.0, 2000.0]),
        calibration_level_db=np.array([-26.9, -26.9]),
        calibration_uncertainty_db=np.array([0.08, 0.08]),
        validation_level_db=np.array([-27.0, -27.0 - 1e-6]),
        validation_uncertainty_db=np.array([0.06, 0.06]),
        validation="comparison",
        unvalidated_frequencies_hz=np.array([]),
    )
    raw = np.abs(on_the_limit.difference_db)
    assert raw[0] > on_the_limit.expanded_uncertainty_db[0]
    assert on_the_limit.agrees.tolist() == [True, False]


def test_validation_pairs_each_frequency_with_its_own() -> None:
    """The jig at 1, 2, 4 and 8 kHz against a calibration at 0,5, 1, 2 and
    4 kHz, every level and uncertainty its own: each jig frequency meets the
    validation at the same frequency, not at the same position, and 8 kHz is
    left unvalidated.
    """
    jig = _comparison(
        np.array([-26.30, -26.25, -26.05, -26.10]), np.array([0.07, 0.08, 0.09, 0.10])
    )
    grid = np.array([500.0, 1000.0, 2000.0, 4000.0])
    other_level = np.array([-30.0, -26.32, -26.21, -26.16])
    other_uncertainty = np.array([0.5, 0.04, 0.05, 0.06])
    other = _comparison(other_level, other_uncertainty, frequencies=grid)
    result = metrology.verify_jig_or_coupler(jig, other)
    assert result.frequencies_hz.tolist() == [1000.0, 2000.0, 4000.0]
    np.testing.assert_allclose(result.validation_level_db, other_level[1:], atol=1e-9)
    np.testing.assert_allclose(
        result.validation_uncertainty_db, other_uncertainty[1:], rtol=1e-12
    )
    np.testing.assert_allclose(result.calibration_uncertainty_db, [0.07, 0.08, 0.09])
    np.testing.assert_allclose(result.difference_db, [0.02, -0.04, 0.11], atol=1e-9)
    assert result.unvalidated_frequencies_hz.tolist() == [8000.0]
    assert result.agrees.tolist() == [True, True, False]


def test_validation_frequency_within_the_tolerance_is_the_same() -> None:
    """A validation frequency off by 5e-10 of itself is the same frequency;
    one off by 1e-8 is another, and leaves the jig's unvalidated.
    """
    jig = _comparison(np.full(4, -26.3), 0.08)
    grid = np.array([1000.0 * (1.0 + 5e-10), 2000.0, 4000.0 * (1.0 + 1e-8)])
    reciprocity = _reciprocity(grid, np.array([-26.31, -26.32, -26.33]), 0.04)
    result = metrology.verify_jig_or_coupler(jig, reciprocity, microphone=1)
    assert result.frequencies_hz.tolist() == [1000.0, 2000.0]
    np.testing.assert_allclose(result.validation_level_db, [-26.31, -26.32], atol=1e-9)
    assert result.unvalidated_frequencies_hz.tolist() == [4000.0, 8000.0]


def test_validation_against_a_reciprocity_calibration() -> None:
    """A laboratory standard microphone: the jig against its reciprocity
    calibration, the microphone picked by its index; the frequencies the
    reciprocity calibration does not hold stay unvalidated.
    """
    jig = _comparison(np.full(4, -26.3), 0.08)
    reciprocity = _reciprocity(np.array([1000.0, 2000.0, 4000.0]), -26.32, 0.04)
    result = metrology.verify_jig_or_coupler(jig, reciprocity, microphone=1)
    assert result.validation == "reciprocity"
    assert result.frequencies_hz.tolist() == [1000.0, 2000.0, 4000.0]
    assert result.unvalidated_frequencies_hz.tolist() == [8000.0]
    np.testing.assert_allclose(result.difference_db, 0.02, atol=1e-9)
    assert result.passes


def test_verification_has_no_truth_value() -> None:
    jig = _comparison(np.full(4, -26.3), 0.08)
    result = metrology.verify_jig_or_coupler(jig, _comparison(np.full(4, -26.3), 0.08))
    with pytest.raises(TypeError, match="no truth value"):
        bool(result)


def test_validation_needs_the_microphone_of_a_reciprocity_calibration() -> None:
    jig = _comparison(np.full(4, -26.3), 0.08)
    reciprocity = _reciprocity(_F_VAL, -26.32, 0.04)
    with pytest.raises(ValueError, match="'microphone'"):
        metrology.verify_jig_or_coupler(jig, reciprocity)


def test_validation_refuses_a_microphone_out_of_range() -> None:
    jig = _comparison(np.full(4, -26.3), 0.08)
    reciprocity = _reciprocity(_F_VAL, -26.32, 0.04)
    with pytest.raises(ValueError, match="one of the 3 microphones"):
        metrology.verify_jig_or_coupler(jig, reciprocity, microphone=3)


def test_validation_refuses_a_microphone_for_a_comparison() -> None:
    jig = _comparison(np.full(4, -26.3), 0.08)
    other = _comparison(np.full(4, -26.3), 0.08)
    with pytest.raises(ValueError, match="only picks a microphone"):
        metrology.verify_jig_or_coupler(jig, other, microphone=0)


def test_validation_refuses_a_free_field_reciprocity_calibration() -> None:
    jig = _comparison(np.full(4, -26.3), 0.08)
    free = _reciprocity(_F_VAL, -26.32, 0.04, field="free_field")
    with pytest.raises(ValueError, match="pressure calibration too"):
        metrology.verify_jig_or_coupler(jig, free, microphone=1)


def test_validation_refuses_a_free_field_calibration() -> None:
    free = metrology.sequential_comparison(
        _F_VAL, -38.0, 94.0, 105.7, field="free_field", expanded_uncertainty_db=0.1
    )
    other = _comparison(np.full(4, -26.3), 0.08)
    with pytest.raises(ValueError, match="free-field one"):
        metrology.verify_jig_or_coupler(free, other)


def test_validation_needs_both_uncertainties() -> None:
    jig = metrology.simultaneous_comparison(_F_VAL, -38.0, 5.85, -5.85)
    other = _comparison(np.full(4, -26.3), 0.08)
    with pytest.raises(ValueError, match="'calibration' must carry"):
        metrology.verify_jig_or_coupler(jig, other)


def test_validation_refuses_a_validation_without_uncertainty() -> None:
    jig = _comparison(np.full(4, -26.3), 0.08)
    other = metrology.simultaneous_comparison(_F_VAL, -38.0, 5.85, -5.85)
    with pytest.raises(ValueError, match="'validation' must carry"):
        metrology.verify_jig_or_coupler(jig, other)


def test_validation_needs_a_shared_frequency() -> None:
    jig = _comparison(np.full(4, -26.3), 0.08)
    elsewhere = _reciprocity(np.array([500.0, 630.0]), -26.32, 0.04)
    with pytest.raises(ValueError, match="share no frequency"):
        metrology.verify_jig_or_coupler(jig, elsewhere, microphone=1)


def test_validation_refuses_anything_else() -> None:
    jig = _comparison(np.full(4, -26.3), 0.08)
    with pytest.raises(TypeError, match="ReciprocityCalibration"):
        metrology.verify_jig_or_coupler(jig, np.full(4, -26.3))  # type: ignore[arg-type]


def test_validation_refuses_a_calibration_that_is_not_a_comparison() -> None:
    other = _comparison(np.full(4, -26.3), 0.08)
    with pytest.raises(
        TypeError, match="'calibration' must be a ComparisonCalibration"
    ):
        metrology.verify_jig_or_coupler(np.full(4, -26.3), other)  # type: ignore[arg-type]


def test_verification_refuses_a_negative_uncertainty() -> None:
    with pytest.raises(
        ValueError, match="'calibration_uncertainty_db' must be non-negative"
    ):
        cc.JigCouplerVerification(
            frequencies_hz=np.array([1000.0]),
            calibration_level_db=np.array([-26.3]),
            calibration_uncertainty_db=np.array([-0.1]),
            validation_level_db=np.array([-26.3]),
            validation_uncertainty_db=np.array([0.06]),
            validation="comparison",
            unvalidated_frequencies_hz=np.array([]),
        )


def test_verification_refuses_two_zero_uncertainties() -> None:
    with pytest.raises(ValueError, match="above 0 dB"):
        cc.JigCouplerVerification(
            frequencies_hz=np.array([1000.0]),
            calibration_level_db=np.array([-26.3]),
            calibration_uncertainty_db=np.array([0.0]),
            validation_level_db=np.array([-26.3]),
            validation_uncertainty_db=np.array([0.0]),
            validation="comparison",
            unvalidated_frequencies_hz=np.array([]),
        )


#: Table D.1 at 2 kHz, by hand: the eight rows sum to 0,001 907 dB^2, so each
#: calibration of the budget has U = 2 sqrt(0,001 907) = 0,087 338 dB. Two
#: against the same reference share its row, 0,025 dB; the other seven sum
#: to 0,001 907 - 0,000 625 = 0,001 282 dB^2, and the difference of the two
#: carries U = 2 sqrt(2 x 0,001 282) = 0,101 272 dB rather than the
#: 2 sqrt(2 x 0,001 907) = 0,123 515 dB of two independent calibrations.
_D1_EXPANDED_DB = 0.0873384222435922
_D1_DIFFERENCE_SHARED_DB = 0.1012719112093773
_D1_DIFFERENCE_INDEPENDENT_DB = 0.1235151812531561
#: r = 0,000 625/0,001 907 (JCGM 100:2008 Formula (14)).
_D1_CORRELATION = 0.3277399056109072


def test_shared_reference_cancels_in_the_difference() -> None:
    """Two calibrations with the budget of Table D.1 against the same LS2P:
    its row, 0,025 dB, cancels in the difference, 0,101 272 dB where the
    root-sum-square gives 0,123 515 dB, worked by hand above.
    """
    jig = _comparison(np.full(4, -26.3), _D1_EXPANDED_DB)
    coupler = _comparison(np.full(4, -26.31), _D1_EXPANDED_DB)
    independent = metrology.verify_jig_or_coupler(jig, coupler)
    shared = metrology.verify_jig_or_coupler(
        jig, coupler, shared_standard_uncertainty_db=0.025
    )
    np.testing.assert_allclose(
        independent.expanded_uncertainty_db, _D1_DIFFERENCE_INDEPENDENT_DB, rtol=1e-12
    )
    np.testing.assert_allclose(
        shared.expanded_uncertainty_db, _D1_DIFFERENCE_SHARED_DB, rtol=1e-12
    )
    np.testing.assert_allclose(
        shared.correlation_coefficient, _D1_CORRELATION, rtol=1e-12
    )
    np.testing.assert_allclose(independent.correlation_coefficient, 0.0, atol=0.0)
    np.testing.assert_allclose(shared.shared_standard_uncertainty_db, 0.025)
    np.testing.assert_allclose(shared.difference_db, independent.difference_db)


def test_shared_part_is_the_gum_law_for_correlated_inputs() -> None:
    """u_Delta^2 = u_cal^2 + u_val^2 - 2 u_sh^2 at each frequency (JCGM 100:2008
    5.2.2 with the covariance u_sh^2 of F.1.2.3), every column its own, on
    the k = 2 of 7.9; the shared part follows the calibration's frequencies
    and the one the validation does not cover drops out with it.
    """
    u_cal = np.array([0.08, 0.09, 0.10, 0.12])
    u_val = np.array([0.06, 0.05, 0.07])
    u_sh = np.array([0.01, 0.02, 0.025, 0.04])
    jig = _comparison(np.full(4, -26.3), u_cal)
    reciprocity = _reciprocity(np.array([1000.0, 2000.0, 4000.0]), -26.32, u_val)
    result = metrology.verify_jig_or_coupler(
        jig, reciprocity, microphone=1, shared_standard_uncertainty_db=u_sh
    )
    standard = np.sqrt((u_cal[:3] / 2) ** 2 + (u_val / 2) ** 2 - 2 * u_sh[:3] ** 2)
    np.testing.assert_allclose(result.expanded_uncertainty_db, 2 * standard, rtol=1e-12)
    np.testing.assert_allclose(result.shared_standard_uncertainty_db, u_sh[:3])
    np.testing.assert_allclose(
        result.correlation_coefficient,
        u_sh[:3] ** 2 / ((u_cal[:3] / 2) * (u_val / 2)),
        rtol=1e-12,
    )
    assert result.unvalidated_frequencies_hz.tolist() == [8000.0]


@pytest.mark.parametrize(
    ("validated", "kept"),
    [
        (np.array([2000.0, 4000.0, 8000.0]), [1, 2, 3]),
        (np.array([1000.0, 4000.0, 8000.0]), [0, 2, 3]),
    ],
    ids=["first-uncovered", "middle-uncovered"],
)
def test_shared_part_follows_the_frequencies_the_validation_covers(
    validated: np.ndarray, kept: list[int]
) -> None:
    """A shared part given per frequency of the calibration stays with its
    own frequency when the one the validation leaves out is the first or
    one in the middle, not the last: u_Delta^2 = u_cal^2 + u_val^2 -
    2 u_sh^2 with the u_sh of each frequency validated.
    """
    u_cal = np.array([0.08, 0.09, 0.10, 0.12])
    u_val = np.array([0.06, 0.07, 0.09])
    u_sh = np.array([0.01, 0.02, 0.03, 0.04])
    jig = _comparison(np.full(4, -26.3), u_cal)
    other = _comparison(np.full(3, -26.32), u_val, validated)
    result = metrology.verify_jig_or_coupler(
        jig, other, shared_standard_uncertainty_db=u_sh
    )
    np.testing.assert_allclose(result.shared_standard_uncertainty_db, u_sh[kept])
    standard = np.sqrt((u_cal[kept] / 2) ** 2 + (u_val / 2) ** 2 - 2 * u_sh[kept] ** 2)
    np.testing.assert_allclose(result.expanded_uncertainty_db, 2 * standard, rtol=1e-12)
    uncovered = np.delete(_F_VAL, kept)
    assert result.unvalidated_frequencies_hz.tolist() == uncovered.tolist()


def test_correlation_is_zero_where_a_calibration_carries_no_uncertainty() -> None:
    """At a frequency where one calibration carries 0 dB nothing can be
    shared, and the correlation coefficient is 0 there, not a division by
    zero; elsewhere it is (k u_sh)^2/(U_cal U_val) = 0,04^2/(0,08 x 0,06).
    """
    result = cc.JigCouplerVerification(
        frequencies_hz=np.array([1000.0, 2000.0]),
        calibration_level_db=np.array([-26.3, -26.3]),
        calibration_uncertainty_db=np.array([0.0, 0.08]),
        validation_level_db=np.array([-26.3, -26.3]),
        validation_uncertainty_db=np.array([0.06, 0.06]),
        validation="comparison",
        unvalidated_frequencies_hz=np.array([]),
        shared_standard_uncertainty_db=np.array([0.0, 0.02]),
    )
    coefficient = result.correlation_coefficient
    assert not np.any(np.isnan(coefficient))
    np.testing.assert_allclose(coefficient, [0.0, 0.04**2 / (0.08 * 0.06)], rtol=1e-12)


def test_shared_part_tightens_the_verdict() -> None:
    """0,11 dB apart agrees within the 0,124 dB of two independent Table D.1
    calibrations, and not within the 0,101 dB left once the reference they
    share is taken out.
    """
    jig = _comparison(np.full(4, -26.3), _D1_EXPANDED_DB)
    coupler = _comparison(np.array([-26.41, -26.3, -26.3, -26.3]), _D1_EXPANDED_DB)
    independent = metrology.verify_jig_or_coupler(jig, coupler)
    shared = metrology.verify_jig_or_coupler(
        jig, coupler, shared_standard_uncertainty_db=0.025
    )
    assert independent.passes
    assert shared.agrees.tolist() == [False, True, True, True]
    assert not shared.passes
    np.testing.assert_allclose(
        shared.normalised_difference[0], 0.11 / _D1_DIFFERENCE_SHARED_DB, rtol=1e-9
    )


def test_no_shared_part_is_the_root_sum_square_to_the_last_bit() -> None:
    """The default, and 0 dB given explicitly, leave every existing verdict
    as it was: the root-sum-square of the two, bit for bit.
    """
    jig = _comparison(
        np.array([-26.3, -26.31, -26.29, -26.3]), np.array([0.07, 0.08, 0.09, 0.1])
    )
    other = _comparison(np.full(4, -26.33), np.array([0.06, 0.05, 0.04, 0.03]))
    default = metrology.verify_jig_or_coupler(jig, other)
    explicit = metrology.verify_jig_or_coupler(
        jig, other, shared_standard_uncertainty_db=0.0
    )
    rss = np.hypot(
        default.calibration_uncertainty_db, default.validation_uncertainty_db
    )
    assert np.array_equal(default.expanded_uncertainty_db, rss)
    assert np.array_equal(explicit.expanded_uncertainty_db, rss)
    assert default.shared_standard_uncertainty_db.tolist() == [0.0] * 4


def test_shared_part_as_large_as_one_uncertainty_is_allowed() -> None:
    """u_sh = 0,03 dB is all of the 0,06 dB calibration (k = 2): the
    difference keeps the rest of the other, sqrt(0,08^2 - 0,06^2) =
    0,052 915 dB, and r = 0,000 9/(0,04 x 0,03) = 0,75.
    """
    jig = _comparison(np.full(4, -26.3), 0.06)
    other = _comparison(np.full(4, -26.33), 0.08)
    result = metrology.verify_jig_or_coupler(
        jig, other, shared_standard_uncertainty_db=0.03
    )
    np.testing.assert_allclose(
        result.expanded_uncertainty_db, 0.0529150262212918, rtol=1e-12
    )
    np.testing.assert_allclose(result.correlation_coefficient, 0.75, rtol=1e-12)


def test_shared_part_within_a_nanodecibel_of_the_whole_is_the_whole() -> None:
    """A shared part computed a few units in the last place above U/2 is the
    whole of it, not a refusal, and leaves nothing of it in the difference.
    """
    jig = _comparison(np.full(4, -26.3), 0.06)
    other = _comparison(np.full(4, -26.33), 0.08)
    result = metrology.verify_jig_or_coupler(
        jig, other, shared_standard_uncertainty_db=0.03 * (1.0 + 1e-15)
    )
    np.testing.assert_allclose(
        result.expanded_uncertainty_db, 0.0529150262212918, rtol=1e-9
    )


def test_gum_example_2_correlation_of_two_items_against_one_standard() -> None:
    """JCGM 100:2008 F.1.2.3 Example 2: against a standard of relative
    standard uncertainty 10^-4, comparisons of 100, 10 and 1 x 10^-6 give
    r ~ 0,5, 0,990 and 1,000, to the decimals printed. In levels each
    calibration carries sqrt(u(alpha)^2 + (u(R_S)/R_S)^2) and they share
    u(R_S)/R_S, all scaled by the same 20/ln 10 dB per neper.
    """
    scale = 20.0 / math.log(10.0)
    standard = ref.GUM_F123_EXAMPLE_2_STANDARD_RELATIVE
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
        assert round(float(result.correlation_coefficient[0]), decimals) == printed
        np.testing.assert_allclose(
            result.expanded_uncertainty_db,
            2.0 * scale * math.sqrt(2.0) * comparison,
            rtol=1e-9,
        )


def test_verification_publishes_the_shared_part_read_only() -> None:
    result = cc.JigCouplerVerification(
        frequencies_hz=np.array([1000.0, 2000.0]),
        calibration_level_db=np.array([-26.3, -26.3]),
        calibration_uncertainty_db=np.array([0.08, 0.08]),
        validation_level_db=np.array([-26.3, -26.3]),
        validation_uncertainty_db=np.array([0.06, 0.06]),
        validation="comparison",
        unvalidated_frequencies_hz=np.array([]),
        shared_standard_uncertainty_db=0.02,
    )
    assert result.shared_standard_uncertainty_db.tolist() == [0.02, 0.02]
    assert not result.shared_standard_uncertainty_db.flags.writeable


@pytest.mark.parametrize(
    ("shared", "match"),
    [
        (0.031, "'shared_standard_uncertainty_db' cannot exceed"),
        (np.array([0.01, 0.01, 0.01, 0.041]), r"cannot exceed .* \[8000\.0\] Hz"),
        (-0.01, "'shared_standard_uncertainty_db' must be non-negative"),
        (
            np.array([0.01, 0.01]),
            "'shared_standard_uncertainty_db' must hold one value",
        ),
    ],
)
def test_validation_refuses_a_shared_part_it_cannot_hold(
    shared: float | np.ndarray, match: str
) -> None:
    """Larger than the 0,06 dB calibration's standard uncertainty (0,03 dB)
    or, at 8 kHz, the 0,08 dB one's (0,04 dB); negative; or neither one
    value nor one per frequency of the calibration.
    """
    jig = _comparison(np.full(4, -26.3), np.array([0.06, 0.06, 0.06, 0.1]))
    other = _comparison(np.full(4, -26.33), 0.08)
    with pytest.raises(ValueError, match=match):
        metrology.verify_jig_or_coupler(
            jig, other, shared_standard_uncertainty_db=shared
        )


def test_verification_refuses_two_uncertainties_all_shared() -> None:
    """Two calibrations of 0,08 dB that share all of it leave their
    difference no uncertainty to be judged against.
    """
    with pytest.raises(ValueError, match="above 0 dB"):
        cc.JigCouplerVerification(
            frequencies_hz=np.array([1000.0]),
            calibration_level_db=np.array([-26.3]),
            calibration_uncertainty_db=np.array([0.08]),
            validation_level_db=np.array([-26.3]),
            validation_uncertainty_db=np.array([0.08]),
            validation="comparison",
            unvalidated_frequencies_hz=np.array([]),
            shared_standard_uncertainty_db=0.04,
        )


def test_verification_refuses_a_negative_shared_part() -> None:
    with pytest.raises(
        ValueError, match="'shared_standard_uncertainty_db' must be non-negative"
    ):
        cc.JigCouplerVerification(
            frequencies_hz=np.array([1000.0]),
            calibration_level_db=np.array([-26.3]),
            calibration_uncertainty_db=np.array([0.08]),
            validation_level_db=np.array([-26.3]),
            validation_uncertainty_db=np.array([0.06]),
            validation="comparison",
            unvalidated_frequencies_hz=np.array([]),
            shared_standard_uncertainty_db=-0.01,
        )


def test_verification_plot_draws_the_independent_band_dotted() -> None:
    """With a shared part the band is the narrower one and its label says
    so; the root-sum-square the two would have as independent calibrations
    is drawn dotted around it, once in the legend.
    """
    jig = _comparison(np.full(4, -26.3), _D1_EXPANDED_DB)
    coupler = _comparison(np.array([-26.41, -26.3, -26.3, -26.3]), _D1_EXPANDED_DB)
    result = metrology.verify_jig_or_coupler(
        jig, coupler, shared_standard_uncertainty_db=0.025
    )
    ax = result.plot()
    (band,) = ax.collections
    assert "u_\\mathrm{sh}" in band.get_label()
    vertices = band.get_paths()[0].vertices
    edges = np.unique(vertices[np.isclose(vertices[:, 0], 1000.0), 1].round(12))
    np.testing.assert_allclose(
        edges, [-_D1_DIFFERENCE_SHARED_DB, _D1_DIFFERENCE_SHARED_DB]
    )
    dotted = [line for line in ax.get_lines() if line.get_linestyle() == ":"]
    assert len(dotted) == 2
    np.testing.assert_allclose(
        sorted(float(line.get_ydata()[0]) for line in dotted),
        [-_D1_DIFFERENCE_INDEPENDENT_DB, _D1_DIFFERENCE_INDEPENDENT_DB],
    )
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert sum("if independent" in label for label in labels) == 1
    plt.close(ax.figure)


def test_verification_plot_in_spanish_names_the_independent_band() -> None:
    jig = _comparison(np.full(4, -26.3), _D1_EXPANDED_DB)
    coupler = _comparison(np.full(4, -26.31), _D1_EXPANDED_DB)
    result = metrology.verify_jig_or_coupler(
        jig, coupler, shared_standard_uncertainty_db=0.025
    )
    ax = result.plot(language="es")
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert any("si fueran independientes" in label for label in labels)
    plt.close(ax.figure)


def test_verification_plot_marks_the_disagreements() -> None:
    jig = _comparison(np.array([-26.3, -26.3, -26.3, -26.3]), 0.06)
    other = _comparison(np.array([-26.4, -26.41, -26.3, -26.3]), 0.08)
    result = metrology.verify_jig_or_coupler(jig, other)
    ax = result.plot()
    lines = {line.get_label(): line for line in ax.get_lines()}
    np.testing.assert_allclose(
        lines[r"$\Delta = L_\mathrm{cal} - L_\mathrm{val}$"].get_ydata(),
        result.difference_db,
    )
    failing = lines[r"$|\Delta| > U_\Delta$"]
    np.testing.assert_allclose(failing.get_xdata(), [2000.0])
    assert "IEC 61094-5 6.7" in ax.get_title()
    (band,) = ax.collections
    vertices = band.get_paths()[0].vertices
    for frequency, uncertainty in zip(
        result.frequencies_hz, result.expanded_uncertainty_db, strict=True
    ):
        edges = np.unique(vertices[np.isclose(vertices[:, 0], frequency), 1].round(12))
        np.testing.assert_allclose(edges, [-uncertainty, uncertainty])
    assert not any(line.get_linestyle() in ("--", ":") for line in ax.get_lines())
    assert "u_\\mathrm{sh}" not in band.get_label()
    plt.close(ax.figure)


def test_verification_plot_draws_the_uncovered_frequencies() -> None:
    """Against a reciprocity calibration that stops at 4 kHz: the subtitle
    names the reciprocity calibration and 8 kHz is drawn dashed.
    """
    jig = _comparison(np.full(4, -26.3), 0.08)
    reciprocity = _reciprocity(np.array([1000.0, 2000.0, 4000.0]), -26.32, 0.04)
    result = metrology.verify_jig_or_coupler(jig, reciprocity, microphone=1)
    ax = result.plot()
    assert "Against a reciprocity calibration" in ax.get_title()
    dashed = [line for line in ax.get_lines() if line.get_linestyle() == "--"]
    assert [line.get_xdata()[0] for line in dashed] == [8000.0]
    assert dashed[0].get_label() == "Not covered by the validation"
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert "Not covered by the validation" in labels
    plt.close(ax.figure)
