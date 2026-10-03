#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Figures for the reciprocity calibration guide (IEC 61094-2, IEC 61094-3).

Each example is the one the guide builds in its code, with the same
microphones, coupler, conditions and readings, so the figure shows what the
reader's own run gives. The readings are synthetic: electrical transfer
impedances built by Formula (2) of IEC 61094-2, or Formula (D.1) of IEC
61094-3, from sensitivities the page knows.
"""

from typing import TYPE_CHECKING, TypedDict

import matplotlib.pyplot as plt
import numpy as np

from .i18n import _LANG
from .theme import save_figure

if TYPE_CHECKING:
    from phonometry.metrology import (
        CouplerTransferImpedance,
        ReciprocityCalibration,
        ReciprocityMicrophone,
        ReciprocityUncertaintyBudget,
    )


class _Conditions(TypedDict):
    """The environmental conditions every calibration function takes."""

    temperature_c: float
    static_pressure_pa: float
    relative_humidity_percent: float


#: The calibration conditions of the pressure example.
_PRESSURE_CONDITIONS: _Conditions = {
    "temperature_c": 22.4,
    "static_pressure_pa": 100200.0,
    "relative_humidity_percent": 46.0,
}
#: The reference conditions of clause 4, at which Tables B.1 and B.2 are
#: printed.
_REFERENCE_CONDITIONS: _Conditions = {
    "temperature_c": 23.0,
    "static_pressure_pa": 101325.0,
    "relative_humidity_percent": 50.0,
}
#: And of the free-field one.
_FREE_FIELD_CONDITIONS: _Conditions = {
    "temperature_c": 23.1,
    "static_pressure_pa": 101100.0,
    "relative_humidity_percent": 52.0,
}
_PAIRS = ((0, 1), (1, 2), (2, 0))


def _ls1p_microphones() -> "tuple[ReciprocityMicrophone, ...]":
    """Three LS1P microphones with the front cavity of Table C.1."""
    from phonometry import metrology

    return tuple(
        metrology.ReciprocityMicrophone(
            equivalent_volume_m3=volume,
            resonance_frequency_hz=resonance,
            loss_factor=loss,
            front_cavity_volume_m3=0.534e-6,
            front_cavity_depth_m=1.95e-3,
            front_cavity_diameter_m=18.6e-3,
        )
        for volume, resonance, loss in (
            (148e-9, 8200.0, 1.05),
            (141e-9, 8350.0, 1.00),
            (152e-9, 8050.0, 1.10),
        )
    )


def _pressure_example() -> (
    "tuple[ReciprocityCalibration, list[CouplerTransferImpedance]]"
):
    """The guide's triad of LS1P microphones in the plane-wave coupler."""
    from phonometry import metrology

    f = metrology.exact_frequencies(20, 10000, fraction=3)
    mics = _ls1p_microphones()
    coupler = metrology.PlaneWaveCoupler(
        length_m=7.5e-3,
        diameter_m=18.6e-3,
        capillary=metrology.CapillaryTube(length_m=0.05, radius_m=0.2e-3, count=2),
    )
    za = [
        metrology.coupler_transfer_impedance(
            f, coupler, mics[i], mics[j], **_PRESSURE_CONDITIONS
        )
        for i, j in _PAIRS
    ]
    true = [
        m0 * m.complex_equivalent_volume_m3(f) / m.equivalent_volume_m3
        for m0, m in zip((0.0496, 0.0473, 0.0512), mics, strict=True)
    ]
    ze = [
        true[i] * true[j] * z.transfer_impedance_pa_s_m3
        for (i, j), z in zip(_PAIRS, za, strict=True)
    ]
    budget = _pressure_budget(f, coupler, mics)
    calibration = metrology.pressure_reciprocity(
        f, ze, za, expanded_uncertainty_db=budget.expanded_uncertainty_db
    )
    return calibration, za


def _pressure_budget(
    f: np.ndarray, coupler: object, mics: "tuple[ReciprocityMicrophone, ...]"
) -> "ReciprocityUncertaintyBudget":
    """The guide's budget of the pressure calibration of microphone 1."""
    from phonometry import metrology

    parameters = metrology.coupler_parameter_uncertainty(
        f,
        coupler,  # type: ignore[arg-type]
        mics,
        metrology.CouplerInputUncertainties(
            u_coupler_length_m=3e-6,
            u_coupler_diameter_m=3e-6,
            u_capillary_radius_m=2e-6,
            u_static_pressure_pa=10.0,
            u_temperature_k=0.05,
            u_relative_humidity_percent=2.0,
            u_front_cavity_depth_m=3e-6,
            u_front_cavity_volume_m3=1e-9,
            u_equivalent_volume_m3=1e-9,
            u_resonance_frequency_hz=50.0,
            u_loss_factor=0.03,
        ),
        **_PRESSURE_CONDITIONS,
    )
    x = f / 10000.0
    return metrology.reciprocity_uncertainty_budget(
        f,
        {
            **parameters.components_db,
            "series_impedance": 0.002,
            "voltage_ratio": 0.003,
            "cross_talk": 0.001 + 0.004 * x**2,
            "polarizing_voltage": 0.0025,
            "radial_wave_motion": 0.03 * x**2,
            "heat_conduction_theory": 0.002,
            "repeatability": 0.004,
            "rounding": 0.0006,
        },
    )


def _free_field_example() -> "ReciprocityCalibration":
    """The guide's triad of LS2aP microphones 0,25 m apart in a free field."""
    from phonometry import metrology

    f = metrology.exact_frequencies(1000, 40000, fraction=3)
    ratio = f / 23000.0
    true = [m0 / (1.0 - ratio**2 + 1.3j * ratio) for m0 in (0.0128, 0.0124, 0.0131)]
    centre = 4.5e-3 / (1.0 + (f / 30000.0) ** 2)
    distances = (0.25, 0.25, 0.25)
    ze = [
        metrology.free_field_transfer_impedance(
            f,
            true[i],
            true[j],
            diaphragm_distance_m=d,
            acoustic_centres_m=(centre, centre),
            **_FREE_FIELD_CONDITIONS,
        )
        for (i, j), d in zip(_PAIRS, distances, strict=True)
    ]
    budget = _free_field_budget(f, distances, centre)
    return metrology.free_field_reciprocity(
        f,
        ze,
        diaphragm_distances_m=distances,
        acoustic_centres_m=(centre, centre, centre),
        expanded_uncertainty_db=budget.expanded_uncertainty_db,
        **_FREE_FIELD_CONDITIONS,
    )


def _free_field_budget(
    f: np.ndarray, distances: tuple[float, ...], centre: np.ndarray
) -> "ReciprocityUncertaintyBudget":
    """The guide's budget of the free-field calibration of microphone 1."""
    from phonometry import metrology

    parameters = metrology.free_field_parameter_uncertainty(
        f,
        metrology.FreeFieldInputUncertainties(
            u_distance_m=0.1e-3,
            u_acoustic_centre_m=0.5e-3,
            u_static_pressure_pa=20.0,
            u_temperature_k=0.1,
            u_relative_humidity_percent=2.0,
            u_air_attenuation_ratio=0.1 / np.sqrt(3.0),
        ),
        diaphragm_distances_m=distances,
        acoustic_centres_m=(centre, centre, centre),
        **_FREE_FIELD_CONDITIONS,
    )
    x = f / 40000.0
    return metrology.reciprocity_uncertainty_budget(
        f,
        {
            **parameters.components_db,
            "series_impedance": 0.002,
            "voltage_ratio": 0.003,
            "cross_talk": 0.002 + 0.01 * x,
            "noise": 0.005,
            "reflections": 0.01 + 0.02 * x,
            "polarizing_voltage": 0.0025,
            "repeatability": 0.01,
        },
        field="free_field",
    )


def generate_reciprocity_pressure(output_dir: str) -> None:
    """IEC 61094-2: three LS1P microphones and the coupler corrections."""
    print("Generating reciprocity_pressure...")
    calibration, za = _pressure_example()
    fig, (ax_cal, ax_corr) = plt.subplots(1, 2, figsize=(13.5, 5.6))
    calibration.plot(ax_cal, language=_LANG)
    za[0].plot(ax_corr, language=_LANG)
    fig.tight_layout()
    save_figure(output_dir, "reciprocity_pressure.svg")
    plt.close()


def generate_reciprocity_coupler_physics(output_dir: str) -> None:
    """IEC 61094-2 Annexes A and B: heat conduction and a capillary tube."""
    from phonometry import fluids, metrology

    print("Generating reciprocity_coupler_physics...")
    f = metrology.exact_frequencies(1, 10000, fraction=3)
    mics = _ls1p_microphones()[:2]
    # The LS1P coupler of Table C.2: E, C and the bores of length F.
    coupler = metrology.LargeVolumeCoupler(
        length_m=12.55e-3, diameter_m=42.88e-3, port_length_m=0.80e-3
    )
    heat = metrology.heat_conduction_correction(
        f[f >= 2.0],
        volume_m3=coupler.closed_volume_m3(mics),
        surface_area_m2=coupler.closed_surface_m2(mics),
        length_to_diameter_ratio=coupler.length_m / coupler.diameter_m,
        gas=fluids.air(**_PRESSURE_CONDITIONS),
    )
    # The tube of Tables B.1 and B.2 at the conditions they are printed for,
    # on a grid fine enough to draw each resonance.
    tube = metrology.capillary_tube_impedance(
        np.geomspace(20.0, 20000.0, 1500),
        length_m=0.05,
        radius_m=1.0 / 6000.0,
        gas=fluids.air(**_REFERENCE_CONDITIONS),
    )
    fig, (ax_heat, ax_tube) = plt.subplots(1, 2, figsize=(13.5, 5.6))
    heat.plot(ax_heat, language=_LANG)
    tube.plot(ax_tube, language=_LANG)
    fig.tight_layout()
    save_figure(output_dir, "reciprocity_coupler_physics.svg")
    plt.close()


def generate_reciprocity_free_field(output_dir: str) -> None:
    """IEC 61094-3: three LS2aP microphones and the attenuation in air."""
    from phonometry import metrology

    print("Generating reciprocity_free_field...")
    calibration = _free_field_example()
    attenuation = metrology.reciprocity_air_attenuation(
        metrology.exact_frequencies(1000, 50000, fraction=3), **_FREE_FIELD_CONDITIONS
    )
    fig, (ax_cal, ax_air) = plt.subplots(1, 2, figsize=(13.5, 5.6))
    calibration.plot(ax_cal, language=_LANG)
    attenuation.plot(ax_air, language=_LANG)
    fig.tight_layout()
    save_figure(output_dir, "reciprocity_free_field.svg")
    plt.close()


def generate_reciprocity_budgets(output_dir: str) -> None:
    """The two budgets of the guide, microphone 1 of each triad."""
    from phonometry import metrology

    print("Generating reciprocity_budgets...")
    f = metrology.exact_frequencies(20, 10000, fraction=3)
    coupler = metrology.PlaneWaveCoupler(
        length_m=7.5e-3,
        diameter_m=18.6e-3,
        capillary=metrology.CapillaryTube(length_m=0.05, radius_m=0.2e-3, count=2),
    )
    pressure = _pressure_budget(f, coupler, _ls1p_microphones())
    ff = metrology.exact_frequencies(1000, 40000, fraction=3)
    free_field = _free_field_budget(
        ff, (0.25, 0.25, 0.25), 4.5e-3 / (1.0 + (ff / 30000.0) ** 2)
    )
    fig, (ax_p, ax_f) = plt.subplots(1, 2, figsize=(14.5, 8.2))
    pressure.plot(ax_p, language=_LANG)
    free_field.plot(ax_f, language=_LANG)
    for ax in (ax_p, ax_f):
        # Twenty components do not fit beside the curves: the legend goes
        # under the panel, where it covers nothing.
        ax.legend(
            fontsize="x-small",
            ncols=3,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.12),
        )
    fig.tight_layout()
    save_figure(output_dir, "reciprocity_budgets.svg")
    plt.close()


def generate_reciprocity_acoustic_centre(output_dir: str) -> None:
    """IEC 61094-3 6.5: the acoustic centre from the inverse-distance law."""
    from phonometry import metrology

    print("Generating reciprocity_acoustic_centre...")
    distances = np.array([0.15, 0.20, 0.25, 0.30, 0.40, 0.50])
    alpha = metrology.reciprocity_air_attenuation(
        [10000.0], **_FREE_FIELD_CONDITIONS
    ).attenuation_np_per_m[0]
    pressures = 0.85 * np.exp(-alpha * distances) / (distances - 2.4e-3)
    centre = metrology.acoustic_centre(distances, pressures, attenuation_np_per_m=alpha)
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    centre.plot(ax, language=_LANG)
    fig.tight_layout()
    save_figure(output_dir, "reciprocity_acoustic_centre.svg")
    plt.close()
