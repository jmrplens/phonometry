#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 61094-3:2016 with COR1:2016: primary free-field calibration by
reciprocity.

The printed oracle is Table B.1 on folio 22 (PDF page 24), in
``tests/reference_data``. The text says it was computed by ISO 9613-1, and the
library's ISO 9613-1 reproduces it; the procedure of B.2 that the calibration
uses is held to the ±10 % B.2 states for it. The reciprocity chain prints no
worked example: electrical transfer impedances written out by Formula (D.1)
here, not computed by the library, from known sensitivities have to give them
back through Formula (8).
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import reference_data as ref

from phonometry import fluids, metrology
from phonometry.environment.propagation.air_absorption import air_attenuation

_CONDITIONS = {
    "temperature_c": 23.0,
    "static_pressure_pa": 101325.0,
    "relative_humidity_percent": 50.0,
}
_F = np.array([1000.0, 2000.0, 4000.0, 8000.0, 16000.0, 20000.0])
_DISTANCES = (0.30, 0.25, 0.20)
_CENTRES = (0.009, 0.0085, 0.0095)
_TRUE = np.array(
    [
        -0.050 * np.exp(0.1j - 0.02j * _F / 1000.0),
        -0.049 * np.exp(0.05j - 0.03j * _F / 1000.0),
        -0.051 * np.exp(0.2j - 0.025j * _F / 1000.0),
    ]
)


_PAIRS = ((0, 1), (1, 2), (2, 0))


def _medium() -> tuple[float, np.ndarray, np.ndarray]:
    """rho, k = omega/c0 without dispersion and alpha, at the conditions."""
    air = fluids.air(**_CONDITIONS)
    alpha = metrology.reciprocity_air_attenuation(
        _F, **_CONDITIONS
    ).attenuation_np_per_m
    return air.density, 2.0 * math.pi * _F / air.speed_of_sound, alpha


def _formula_d1(
    first: np.ndarray, second: np.ndarray, diaphragms: float, centres: float
) -> np.ndarray:
    """Formula (D.1) written out: U2/i1 = j rho f/(2 d) M1 M2 e^(-jkd)
    e^(-alpha d_m), with d between the acoustic centres and d_m between the
    diaphragms.
    """
    rho, k, alpha = _medium()
    return (
        1j
        * rho
        * _F
        / (2.0 * centres)
        * first
        * second
        * np.exp(-1j * k * centres)
        * np.exp(-alpha * diaphragms)
    )


def _electrical(
    sensitivities: np.ndarray = _TRUE,
    centres: tuple[float, float, float] = _CENTRES,
) -> list[np.ndarray]:
    return [
        _formula_d1(
            sensitivities[i],
            sensitivities[j],
            _DISTANCES[n],
            _DISTANCES[n] - centres[i] - centres[j],
        )
        for n, (i, j) in enumerate(_PAIRS)
    ]


# ---------------------------------------------------------------------------
# Annex B
# ---------------------------------------------------------------------------


def _table_b1() -> tuple[np.ndarray, np.ndarray]:
    frequencies = 1000.0 * np.array(sorted(ref.IEC61094_3_TABLE_B1))
    values = np.array([ref.IEC61094_3_TABLE_B1[f / 1000.0] for f in frequencies])
    return frequencies, values


@pytest.mark.filterwarnings(
    "ignore::phonometry.environment.AtmosphericAbsorptionWarning"
)
def test_table_b1_is_iso_9613_1() -> None:
    """All 162 entries, to half a unit of the fourth decimal, as the text says
    they were computed. Above 10 kHz ISO 9613-1 warns it is past its own
    table, and Table B.1 goes to 50 kHz regardless.
    """
    frequencies, values = _table_b1()
    for column, (temperature, humidity) in enumerate(
        ref.IEC61094_3_TABLE_B1_CONDITIONS
    ):
        alpha = air_attenuation(
            frequencies, temperature_c=temperature, relative_humidity_percent=humidity
        )
        np.testing.assert_allclose(alpha, values[:, column], atol=5.01e-5)


@pytest.mark.filterwarnings(
    "ignore::phonometry.environment.AtmosphericAbsorptionWarning"
)
def test_annex_b_procedure_is_within_its_stated_accuracy_of_table_b1() -> None:
    """B.2: "estimated to be ±10 %". The adjusted constants of the procedure
    put it within 0,8 % of ISO 9613-1 at every condition of the table.
    """
    frequencies, values = _table_b1()
    for column, (temperature, humidity) in enumerate(
        ref.IEC61094_3_TABLE_B1_CONDITIONS
    ):
        attenuation = metrology.reciprocity_air_attenuation(
            frequencies,
            temperature_c=temperature,
            static_pressure_pa=101325.0,
            relative_humidity_percent=humidity,
        )
        relative = attenuation.attenuation_db_per_m / values[:, column] - 1.0
        assert np.all(np.abs(relative) < 0.10)
        iso = air_attenuation(
            frequencies, temperature_c=temperature, relative_humidity_percent=humidity
        )
        assert np.all(np.abs(attenuation.attenuation_db_per_m / iso - 1.0) < 0.008)
        assert np.all(attenuation.within_stated_accuracy)


def test_step_1_uses_the_saturation_pressure_of_iec_61094_2() -> None:
    """The water vapour mole fraction is that of Annex F of IEC 61094-2."""
    attenuation = metrology.reciprocity_air_attenuation(_F, **_CONDITIONS)
    air = fluids.air(**_CONDITIONS)
    assert attenuation.water_vapour_mole_fraction == pytest.approx(
        air.composition["water_vapour_mole_fraction"], rel=1e-12
    )


def test_dispersion_is_a_few_parts_in_a_hundred_thousand() -> None:
    """IEC 61094-2 F.3 NOTE: less than the 3e-4 uncertainty of c0."""
    attenuation = metrology.reciprocity_air_attenuation(_F, **_CONDITIONS)
    relative = attenuation.dispersive_speed_of_sound / attenuation.speed_of_sound - 1.0
    assert np.all(relative > 0.0)
    assert np.all(relative < 3e-4)
    assert np.all(np.diff(relative) > 0.0)


@pytest.mark.filterwarnings(
    "ignore::phonometry.environment.AtmosphericAbsorptionWarning",
    "ignore::phonometry.fluids.FluidWarning",
)
def test_annex_b_procedure_follows_iso_9613_1_across_its_accuracy_domain() -> None:
    """Wherever B.2 states its accuracy (-20 °C to 50 °C, x_w of 0,5e-3 to
    50e-3), the procedure stays within 1 % of ISO 9613-1, whose temperature
    dependence its relaxation frequencies follow.
    """
    frequencies = np.array([1000.0, 2000.0, 5000.0, 10000.0, 20000.0, 50000.0])
    checked = 0
    for temperature in (-20.0, 0.0, 20.0, 35.0, 50.0):
        for humidity in (10.0, 25.0, 50.0, 90.0):
            attenuation = metrology.reciprocity_air_attenuation(
                frequencies,
                temperature_c=temperature,
                static_pressure_pa=101325.0,
                relative_humidity_percent=humidity,
            )
            inside = attenuation.within_stated_accuracy
            iso = air_attenuation(
                frequencies,
                temperature_c=temperature,
                relative_humidity_percent=humidity,
            )
            relative = attenuation.attenuation_db_per_m / iso - 1.0
            assert np.all(np.abs(relative[inside]) < 0.01)
            checked += int(np.sum(inside))
    assert checked > 60


def test_accuracy_domain_excludes_a_frequency_too_high_for_the_pressure() -> None:
    attenuation = metrology.reciprocity_air_attenuation([1000.0, 2.0e6], **_CONDITIONS)
    assert attenuation.within_stated_accuracy.tolist() == [True, False]


# ---------------------------------------------------------------------------
# Clause 5
# ---------------------------------------------------------------------------


def test_three_microphones_give_their_sensitivities_back() -> None:
    """Formula (D.1) forward, Formula (8) with the factor -j of (7) back."""
    calibration = metrology.free_field_reciprocity(
        _F,
        _electrical(),
        diaphragm_distances_m=_DISTANCES,
        acoustic_centres_m=_CENTRES,
        dispersion=False,
        **_CONDITIONS,
    )
    sign = np.sign((calibration.sensitivity_v_per_pa[0, 0] / _TRUE[0, 0]).real)
    np.testing.assert_allclose(
        calibration.sensitivity_v_per_pa, sign * _TRUE, rtol=1e-12
    )
    assert calibration.field == "free_field"
    assert calibration.standard == "IEC 61094-3:2016+COR1:2016"


def test_the_printed_formula_8_is_45_degrees_off() -> None:
    """Formula (8) as printed, without the factor -j of (7), written out from
    the electrical transfer impedances: its square is j times the library's,
    so its phase is 45 degrees off.
    """
    z12, z23, z31 = _electrical()
    calibration = metrology.free_field_reciprocity(
        _F,
        [z12, z23, z31],
        diaphragm_distances_m=_DISTANCES,
        acoustic_centres_m=_CENTRES,
        dispersion=False,
        **_CONDITIONS,
    )
    rho, k, alpha = _medium()
    dm12, dm23, dm31 = _DISTANCES
    x1, x2, x3 = _CENTRES
    d12, d23, d31 = dm12 - x1 - x2, dm23 - x2 - x3, dm31 - x3 - x1
    printed_square = (
        2.0
        / (rho * _F)
        * d12
        * d31
        / d23
        * z12
        * z31
        / z23
        * np.exp(1j * k * (d12 + d31 - d23))
        * np.exp(alpha * (dm12 + dm31 - dm23))
    )
    turned = np.degrees(
        np.angle(printed_square / calibration.sensitivity_v_per_pa[0] ** 2)
    )
    np.testing.assert_allclose(turned, 90.0, atol=1e-9)


def test_two_microphones_and_a_source_give_their_sensitivities_back() -> None:
    """Formula (9), complex since COR1."""
    electrical = _electrical()
    calibration = metrology.free_field_reciprocity_pair(
        _F,
        electrical[0],
        _TRUE[0] / _TRUE[1],
        diaphragm_distance_m=_DISTANCES[0],
        acoustic_centres_m=_CENTRES[:2],
        dispersion=False,
        **_CONDITIONS,
    )
    sign = np.sign((calibration.sensitivity_v_per_pa[0, 0] / _TRUE[0, 0]).real)
    np.testing.assert_allclose(
        calibration.sensitivity_v_per_pa, sign * _TRUE[:2], rtol=1e-12
    )


def test_transfer_impedance_is_formula_6_at_the_receiver() -> None:
    """(D.1) is U2/i1 = M2 p0 with p0 the spherical wave of Formula (6): its
    amplitude and phase over the distance d between the acoustic centres, its
    attenuation over the distance d_m between the diaphragms (Formula (7)).
    """
    air = fluids.air(**_CONDITIONS)
    attenuation = metrology.reciprocity_air_attenuation(_F, **_CONDITIONS)
    d_m = 0.2
    d = d_m - 0.009 - 0.0085
    k = 2.0 * math.pi * _F / attenuation.speed_of_sound
    p0 = (
        1j
        * air.density
        * _F
        / (2.0 * d)
        * _TRUE[0]
        * np.exp(-1j * k * d)
        * np.exp(-attenuation.attenuation_np_per_m * d_m)
    )
    computed = metrology.free_field_transfer_impedance(
        _F,
        _TRUE[0],
        _TRUE[1],
        diaphragm_distance_m=d_m,
        acoustic_centres_m=(0.009, 0.0085),
        dispersion=False,
        **_CONDITIONS,
    )
    np.testing.assert_allclose(computed, _TRUE[1] * p0, rtol=1e-12)


def test_dispersion_turns_the_phase_and_leaves_the_modulus() -> None:
    """IEC 61094-2 F.3 NOTE: the wave number with the dispersive speed of
    sound, a few parts in 1e5 of k d.
    """
    plain = metrology.free_field_transfer_impedance(
        _F,
        _TRUE[0],
        _TRUE[1],
        diaphragm_distance_m=0.2,
        dispersion=False,
        **_CONDITIONS,
    )
    dispersive = metrology.free_field_transfer_impedance(
        _F, _TRUE[0], _TRUE[1], diaphragm_distance_m=0.2, **_CONDITIONS
    )
    attenuation = metrology.reciprocity_air_attenuation(_F, **_CONDITIONS)
    k0 = 2.0 * math.pi * _F / attenuation.speed_of_sound
    k = 2.0 * math.pi * _F / attenuation.dispersive_speed_of_sound
    np.testing.assert_allclose(np.abs(dispersive), np.abs(plain), rtol=1e-12)
    np.testing.assert_allclose(
        np.angle(dispersive / plain), -(k - k0) * 0.2, atol=1e-12
    )


def test_acoustic_centres_that_meet_are_refused() -> None:
    electrical = _electrical()
    with pytest.raises(ValueError, match="acoustic centres leave no distance"):
        metrology.free_field_reciprocity(
            _F,
            electrical,
            diaphragm_distances_m=_DISTANCES,
            acoustic_centres_m=(0.15, 0.15, 0.0),
            **_CONDITIONS,
        )


def test_free_field_reciprocity_needs_three_pairs() -> None:
    electrical = _electrical()
    with pytest.raises(ValueError, match="Three pairs"):
        metrology.free_field_reciprocity(
            _F, electrical[:2], diaphragm_distances_m=_DISTANCES, **_CONDITIONS
        )


# ---------------------------------------------------------------------------
# Clause 6.5: the acoustic centre
# ---------------------------------------------------------------------------


def test_acoustic_centre_is_where_the_inverse_pressure_vanishes() -> None:
    distances = np.array([0.15, 0.2, 0.3, 0.4, 0.5])
    pressures = 1.0 / (distances - 0.008)
    centre = metrology.acoustic_centre(distances, pressures)
    assert centre.position_m == pytest.approx(0.008, abs=1e-12)


def test_acoustic_centre_corrects_for_the_attenuation() -> None:
    distances = np.array([0.15, 0.2, 0.3, 0.4, 0.5])
    alpha = 0.05
    pressures = np.exp(-alpha * distances) / (distances - 0.004)
    centre = metrology.acoustic_centre(distances, pressures, attenuation_np_per_m=alpha)
    assert centre.position_m == pytest.approx(0.004, abs=1e-12)
    uncorrected = metrology.acoustic_centre(distances, pressures)
    assert abs(uncorrected.position_m - 0.004) > 1e-4


def test_acoustic_centre_needs_three_distances() -> None:
    with pytest.raises(ValueError, match="three distances"):
        metrology.acoustic_centre([0.2, 0.3], [5.0, 3.3])


# ---------------------------------------------------------------------------
# Clauses 6.4 and 7.3
# ---------------------------------------------------------------------------


def test_arrangement_holds_the_distance_to_ten_diameters() -> None:
    check = metrology.check_free_field_arrangement(
        _F,
        diaphragm_distances_m=_DISTANCES,
        microphone_diameter_m=23.77e-3,
        support_length_m=0.5,
        **_CONDITIONS,
    )
    assert check.distances_ok is False
    assert check.support_ok is True
    assert check.annex_a_range is True
    assert not check.passes


def test_arrangement_holds_the_support_to_twenty_diameters() -> None:
    check = metrology.check_free_field_arrangement(
        _F,
        diaphragm_distances_m=(0.2, 0.25, 0.3),
        microphone_diameter_m=13.2e-3,
        support_length_m=0.2,
        **_CONDITIONS,
    )
    assert check.distances_ok is True
    assert check.support_ok is False
    assert not check.passes


def test_arrangement_check_has_no_truth_value() -> None:
    check = metrology.check_free_field_arrangement(
        _F, diaphragm_distances_m=(0.2,), microphone_diameter_m=13.2e-3, **_CONDITIONS
    )
    assert check.passes
    with pytest.raises(TypeError, match="passes"):
        bool(check)


# ---------------------------------------------------------------------------
# Clause 7.8
# ---------------------------------------------------------------------------


def test_distance_component_is_the_closed_form() -> None:
    """|M1|**2 goes as d12 d31 / d23 times the attenuation: moving each distance
    by u changes 20 lg|M1| by 10 lg(1 + u/d) plus 10 lg e times alpha u.
    """
    u = 1e-4
    result = metrology.free_field_parameter_uncertainty(
        _F,
        metrology.FreeFieldInputUncertainties(u_distance_m=u),
        diaphragm_distances_m=_DISTANCES,
        **_CONDITIONS,
    )
    alpha = metrology.reciprocity_air_attenuation(
        _F, **_CONDITIONS
    ).attenuation_np_per_m
    terms = [
        sign * (10.0 * np.log10(1.0 + u / d) + 10.0 * np.log10(math.e) * alpha * u)
        for sign, d in zip((1.0, -1.0, 1.0), _DISTANCES, strict=True)
    ]
    expected = np.sqrt(sum(t**2 for t in terms))
    np.testing.assert_allclose(result.components_db["distance"], expected, rtol=1e-9)


def test_free_field_components_are_named_by_table_1() -> None:
    result = metrology.free_field_parameter_uncertainty(
        _F,
        metrology.FreeFieldInputUncertainties(
            u_acoustic_centre_m=0.5e-3,
            u_temperature_k=0.1,
            u_static_pressure_pa=20.0,
            u_relative_humidity_percent=2.0,
            u_air_attenuation_ratio=0.1 / math.sqrt(3.0),
        ),
        diaphragm_distances_m=_DISTANCES,
        acoustic_centres_m=_CENTRES,
        **_CONDITIONS,
    )
    assert set(result.components_db) == {
        "acoustic_centres",
        "temperature",
        "static_pressure",
        "relative_humidity",
        "air_attenuation",
    }
    assert set(result.components_db) <= set(metrology.IEC61094_3_TABLE_1)
    budget = metrology.reciprocity_uncertainty_budget(
        _F, result.components_db, field="free_field"
    )
    assert np.all(budget.expanded_uncertainty_db > 0.0)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("u_distance_m", -1e-4, "'u_distance_m' must be non-negative"),
        ("u_air_attenuation_ratio", float("nan"), "'u_air_attenuation_ratio' must"),
        ("u_acoustic_centre_m", [1e-3, -1e-3], "'u_acoustic_centre_m' must be"),
        ("u_acoustic_centre_m", [[1e-3]], "'u_acoustic_centre_m' must be"),
    ],
)
def test_input_uncertainties_refuse_what_is_not_a_standard_uncertainty(
    field: str, value: object, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        metrology.FreeFieldInputUncertainties(**{field: value})  # type: ignore[arg-type]


def test_acoustic_centre_uncertainty_is_held_read_only_and_per_frequency() -> None:
    column = np.array([0.2e-3, 0.5e-3, 1.0e-3])
    uncertainties = metrology.FreeFieldInputUncertainties(u_acoustic_centre_m=column)
    column[0] = 9.0
    held = np.asarray(uncertainties.u_acoustic_centre_m)
    assert held[0] == pytest.approx(0.2e-3)
    with pytest.raises(ValueError, match="read-only"):
        held[0] = 1.0
    result = metrology.free_field_parameter_uncertainty(
        _F[:3],
        uncertainties,
        diaphragm_distances_m=_DISTANCES,
        acoustic_centres_m=_CENTRES,
        **_CONDITIONS,
    )
    assert result.components_db["acoustic_centres"].shape == (3,)
    with pytest.raises(ValueError, match="one value per frequency"):
        metrology.free_field_parameter_uncertainty(
            _F[:2],
            uncertainties,
            diaphragm_distances_m=_DISTANCES,
            **_CONDITIONS,
        )
