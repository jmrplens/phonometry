#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What each figure of the reciprocity calibration draws (IEC 61094-2 and
IEC 61094-3): the curves and bars carry the result's numbers, the limits are
where the standard puts them, and the labels follow the language.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import fluids, metrology

if TYPE_CHECKING:
    from collections.abc import Iterator

    from matplotlib.axes import Axes

_CONDITIONS = {
    "temperature_c": 23.0,
    "static_pressure_pa": 101325.0,
    "relative_humidity_percent": 50.0,
}
_F = np.array([250.0, 1000.0, 4000.0])
_MICS = tuple(
    metrology.ReciprocityMicrophone(
        equivalent_volume_m3=volume,
        resonance_frequency_hz=resonance,
        loss_factor=1.0,
        front_cavity_volume_m3=0.534e-6,
        front_cavity_depth_m=1.95e-3,
        front_cavity_diameter_m=18.6e-3,
    )
    for volume, resonance in ((144e-9, 8200.0), (140e-9, 8300.0), (150e-9, 8000.0))
)
_PLANE = metrology.PlaneWaveCoupler(
    length_m=7.5e-3,
    diameter_m=18.6e-3,
    capillary=metrology.CapillaryTube(length_m=0.05, radius_m=1.0 / 6000.0, count=2),
)
_LARGE = metrology.LargeVolumeCoupler(
    length_m=12.55e-3, diameter_m=42.88e-3, port_length_m=0.80e-3
)


@pytest.fixture
def ax() -> Iterator[Axes]:
    fig, axes = plt.subplots()
    yield axes
    plt.close(fig)


def _legend(ax: Axes) -> list[str]:
    legend = ax.get_legend()
    assert legend is not None
    return [text.get_text() for text in legend.get_texts()]


def _calibration(uncertainty: object = None) -> metrology.ReciprocityCalibration:
    true = [
        -0.05 * m.complex_equivalent_volume_m3(_F) / m.equivalent_volume_m3
        for m in _MICS
    ]
    pairs = ((0, 1), (1, 2), (2, 0))
    za = [
        metrology.coupler_transfer_impedance(
            _F, _PLANE, _MICS[i], _MICS[j], **_CONDITIONS
        )
        for i, j in pairs
    ]
    ze = [
        true[i] * true[j] * z.transfer_impedance_pa_s_m3
        for (i, j), z in zip(pairs, za, strict=True)
    ]
    return metrology.pressure_reciprocity(
        _F, ze, za, expanded_uncertainty_db=uncertainty
    )


def test_calibration_draws_each_level_and_says_how_wide_the_band_is(ax: Axes) -> None:
    result = _calibration([0.015, 0.02, 0.064])
    result.plot(ax)
    for line, level in zip(ax.get_lines(), result.sensitivity_level_db, strict=True):
        np.testing.assert_allclose(line.get_ydata(), level)
    assert len(ax.collections) == 3
    assert _legend(ax)[0] == r"$\pm U$, expanded uncertainty, 0.015 dB to 0.064 dB"
    assert ax.get_title() == "Pressure sensitivity by reciprocity (IEC 61094-2)"


def test_calibration_without_uncertainty_draws_no_band_and_speaks_spanish(
    ax: Axes,
) -> None:
    _calibration().plot(ax, language="es")
    assert len(ax.collections) == 0
    assert _legend(ax) == ["Micrófono 1", "Micrófono 2", "Micrófono 3"]
    assert ax.get_ylabel() == "Nivel de sensibilidad [dB re 1 V/Pa]"


def test_budget_draws_its_components_and_the_expanded_uncertainty(ax: Axes) -> None:
    budget = metrology.reciprocity_uncertainty_budget(
        _F, {"voltage_ratio": 0.003, "repeatability": [0.005, 0.004, 0.008]}
    )
    budget.plot(ax, language="es")
    lines = ax.get_lines()
    np.testing.assert_allclose(lines[0].get_ydata(), [0.003] * 3)
    np.testing.assert_allclose(lines[2].get_ydata(), budget.combined_uncertainty_db)
    np.testing.assert_allclose(lines[3].get_ydata(), budget.expanded_uncertainty_db)
    assert _legend(ax)[:2] == ["Relación de tensiones", "Repetibilidad"]
    assert _legend(ax)[-1] == r"Incertidumbre expandida $U$ ($k$ = 2)"


def test_heat_conduction_draws_the_correction_with_r_and_l(ax: Axes) -> None:
    heat = metrology.heat_conduction_correction(
        [20.0, 100.0, 500.0],
        volume_m3=19.2e-6,
        surface_area_m2=4.6e-3,
        length_to_diameter_ratio=0.29,
        gas=fluids.air(**_CONDITIONS),
    )
    heat.plot(ax, language="es")
    np.testing.assert_allclose(ax.get_lines()[0].get_ydata(), heat.correction_db)
    assert "$R$ = 0,290" in ax.get_title()
    assert "$l$ = 4,174 mm" in ax.get_title()


def test_capillary_tube_draws_both_parts_in_gpa_s_per_m3(ax: Axes) -> None:
    tube = metrology.capillary_tube_impedance(
        [20.0, 1000.0],
        length_m=0.05,
        radius_m=1.0 / 6000.0,
        gas=fluids.air(**_CONDITIONS),
    )
    tube.plot(ax)
    lines = ax.get_lines()
    np.testing.assert_allclose(lines[1].get_ydata(), tube.impedance_pa_s_m3.real / 1e9)
    np.testing.assert_allclose(lines[2].get_ydata(), tube.impedance_pa_s_m3.imag / 1e9)
    assert "50.0 mm" in ax.get_title()


@pytest.mark.parametrize(
    ("coupler", "title"),
    [
        (
            _PLANE,
            "Correcciones de $Z_{\\mathrm{a},12}$, acoplador de onda plana (IEC 61094-2)",
        ),
        (
            _LARGE,
            "Correcciones de $Z_{\\mathrm{a},12}$, acoplador de gran volumen (IEC 61094-2)",
        ),
    ],
    ids=["plane_wave", "large_volume"],
)
def test_transfer_impedance_draws_the_two_corrections_and_their_sum(
    ax: Axes,
    coupler: metrology.PlaneWaveCoupler | metrology.LargeVolumeCoupler,
    title: str,
) -> None:
    z = metrology.coupler_transfer_impedance(
        _F, coupler, _MICS[0], _MICS[1], **_CONDITIONS
    )
    z.plot(ax, language="es")
    lines = ax.get_lines()
    np.testing.assert_allclose(lines[1].get_ydata(), z.heat_conduction_correction_db)
    np.testing.assert_allclose(lines[2].get_ydata(), z.capillary_correction_db)
    np.testing.assert_allclose(
        lines[3].get_ydata(),
        z.heat_conduction_correction_db + z.capillary_correction_db,
    )
    assert ax.get_title() == title


def test_wave_motion_draws_table_c3_on_the_scaled_frequencies(ax: Axes) -> None:
    correction = metrology.large_volume_wave_motion_correction(
        [3780.0, 9450.0], speed_of_sound_ratio=3.78
    )
    correction.plot(ax)
    rows = ax.get_lines()[2]
    np.testing.assert_allclose(
        rows.get_xdata(),
        3.78 * np.array([800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0]),
    )
    np.testing.assert_allclose(ax.get_lines()[1].get_ydata(), correction.correction_db)


def _bars(ax: Axes) -> tuple[list[float], list[str]]:
    widths = [patch.get_width() for patch in ax.containers[0]]
    ticks = [label.get_text() for label in ax.get_yticklabels()]
    return widths, ticks


def test_plane_wave_check_draws_its_margins_with_a_decimal_point(ax: Axes) -> None:
    check = metrology.check_coupler([20.0, 1000.0], _PLANE, _MICS, **_CONDITIONS)
    check.plot(ax)
    widths, ticks = _bars(ax)
    assert check.broadband_margin is not None
    ratio = check.length_to_diameter_ratio
    np.testing.assert_allclose(
        widths, [check.broadband_margin, ratio / 0.5, 0.75 / ratio]
    )
    assert ticks[1] == "$R/0.5$, recommended at least 1 (C.2)"
    assert ticks[2] == "$0.75/R$, recommended at least 1 (C.2)"
    ax.figure.canvas.draw()
    assert not any("times" in label.get_text() for label in ax.get_xticklabels())


def test_plane_wave_check_in_spanish_writes_a_decimal_comma(ax: Axes) -> None:
    metrology.check_coupler([20.0, 1000.0], _PLANE, _MICS, **_CONDITIONS).plot(
        ax, language="es"
    )
    _, ticks = _bars(ax)
    assert ticks[1] == "$R/0{,}5$, recomendado al menos 1 (C.2)"
    assert (
        ax.get_title()
        == "Comprobación del acoplador (IEC 61094-2): las fórmulas son válidas"
    )


def test_large_volume_check_with_the_full_solution_draws_no_x_bar(ax: Axes) -> None:
    """X > 5 binds the approximation (A.2) only."""
    metrology.check_coupler([2.0, 1000.0], _LARGE, _MICS, **_CONDITIONS).plot(ax)
    assert len(ax.containers[0]) == 0


def test_large_volume_check_with_the_approximation_draws_x_and_20_hz(ax: Axes) -> None:
    check = metrology.check_coupler(
        [10.0, 1000.0],
        _LARGE,
        _MICS,
        **_CONDITIONS,
        heat_conduction_method="approximation",
    )
    check.plot(ax)
    widths, ticks = _bars(ax)
    assert check.lowest_x is not None
    np.testing.assert_allclose(widths, [check.lowest_x / 5.0, 10.0 / 20.0])
    assert ticks[0] == "$X/5$ at the lowest frequency (A.2)"
    assert "advisory" in ticks[1]


@pytest.mark.parametrize("field", ["pressure", "free_field"])
def test_parameter_uncertainty_draws_each_component(ax: Axes, field: str) -> None:
    if field == "pressure":
        result: (
            metrology.CouplerParameterUncertainty
            | metrology.FreeFieldParameterUncertainty
        ) = metrology.coupler_parameter_uncertainty(
            _F,
            _PLANE,
            _MICS,
            metrology.CouplerInputUncertainties(
                u_coupler_length_m=5e-6, u_loss_factor=0.03
            ),
            **_CONDITIONS,
        )
    else:
        result = metrology.free_field_parameter_uncertainty(
            [1000.0, 4000.0],
            metrology.FreeFieldInputUncertainties(
                u_distance_m=1e-4, u_temperature_k=0.1
            ),
            diaphragm_distances_m=(0.2, 0.25, 0.3),
            **_CONDITIONS,
        )
    result.plot(ax, language="es")
    for line, values in zip(ax.get_lines(), result.components_db.values(), strict=True):
        np.testing.assert_allclose(line.get_ydata(), values)
    part = "IEC 61094-2, 7.5" if field == "pressure" else "IEC 61094-3, 7.8"
    assert (
        ax.get_title()
        == f"Incertidumbre debida a $Z_\\mathrm{{a}}$, micrófono 1 ({part})"
    )


def test_air_attenuation_draws_its_three_parts_and_the_total(ax: Axes) -> None:
    attenuation = metrology.reciprocity_air_attenuation(
        [1000.0, 10000.0, 40000.0], **_CONDITIONS
    )
    attenuation.plot(ax, language="es")
    lines = ax.get_lines()
    to_db = attenuation.attenuation_db_per_m / attenuation.attenuation_np_per_m
    np.testing.assert_allclose(
        lines[0].get_ydata(), attenuation.classical_np_per_m * to_db
    )
    np.testing.assert_allclose(
        lines[1].get_ydata(), attenuation.oxygen_np_per_m * to_db
    )
    np.testing.assert_allclose(
        lines[2].get_ydata(), attenuation.nitrogen_np_per_m * to_db
    )
    np.testing.assert_allclose(lines[3].get_ydata(), attenuation.attenuation_db_per_m)
    assert ax.get_title() == (
        "Atenuación en el aire (IEC 61094-3, anexo B): 23,0 °C, 101,3 kPa, 50 %"
    )


def test_acoustic_centre_draws_the_corrected_readings_and_the_centre(ax: Axes) -> None:
    distances = np.array([0.15, 0.2, 0.3, 0.4])
    alpha = 0.05
    centre = metrology.acoustic_centre(
        distances,
        np.exp(-alpha * distances) / (distances - 0.008),
        attenuation_np_per_m=alpha,
    )
    centre.plot(ax)
    lines = ax.get_lines()
    np.testing.assert_allclose(lines[0].get_ydata(), centre.inverse_readings)
    np.testing.assert_allclose(lines[-1].get_xdata(), [centre.position_m])
    assert ax.get_ylabel() == r"$1/(|p|\,\mathrm{e}^{\alpha r})$ [1/Pa]"
    assert _legend(ax)[0] == "Inverse of the pressure corrected for attenuation"
    assert _legend(ax)[-1] == "Acoustic centre, 8.0 mm"


def test_arrangement_draws_the_support_and_names_what_fails(ax: Axes) -> None:
    check = metrology.check_free_field_arrangement(
        [1000.0, 20000.0],
        diaphragm_distances_m=(0.25, 0.25, 0.25),
        microphone_diameter_m=13.2e-3,
        support_length_m=0.1,
        **_CONDITIONS,
    )
    check.plot(ax)
    widths = [patch.get_width() for patch in ax.containers[0]]
    support = [patch.get_width() for patch in ax.containers[1]]
    np.testing.assert_allclose(widths, [0.25, 0.25, 0.25])
    np.testing.assert_allclose(support, [0.1])
    assert ax.get_title() == (
        "Free-field arrangement (IEC 61094-3): not as recommended\n"
        "support under twenty diameters"
    )
    assert [label.get_text() for label in ax.get_yticklabels()][-1] == "Support"


def test_arrangement_in_spanish_names_the_b2_domain(ax: Axes) -> None:
    check = metrology.check_free_field_arrangement(
        [20.0, 1000.0],
        diaphragm_distances_m=(0.2,),
        microphone_diameter_m=13.2e-3,
        **_CONDITIONS,
    )
    check.plot(ax, language="es")
    assert check.attenuation_accuracy is False
    assert ax.get_title().endswith("condiciones fuera del dominio de exactitud de B.2")
    assert len(ax.containers) == 1


def test_arrangement_that_passes_has_a_one_line_title(ax: Axes) -> None:
    check = metrology.check_free_field_arrangement(
        [1000.0, 20000.0],
        diaphragm_distances_m=(0.25,),
        microphone_diameter_m=13.2e-3,
        support_length_m=0.3,
        **_CONDITIONS,
    )
    dataclasses.replace(check).plot(ax)
    assert ax.get_title() == "Free-field arrangement (IEC 61094-3): as recommended"
