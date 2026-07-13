#  Copyright (c) 2026. Jose M. Requena-Plens
"""underwater domain of phonometry (see module docstrings)."""

from __future__ import annotations

from .acoustics import (
    UNDERWATER_REFERENCE_EXPOSURE,
    UNDERWATER_REFERENCE_PRESSURE,
    in_air_to_underwater_spl,
    peak_sound_pressure_level,
    sound_exposure_level,
    sound_pressure_level,
    underwater_to_in_air_spl,
)
from .numerical_propagation import (
    NormalModeResult,
    ParabolicEquationResult,
    RayTraceResult,
    normal_modes,
    parabolic_equation,
    ray_trace,
)
from .ocean_ambient_noise import (
    AmbientNoiseResult,
    ocean_ambient_noise,
    thermal_noise_spectrum,
    wind_noise_spectrum,
)
from .pile_driving_noise import (
    PileStrikeResult,
    cumulative_sel,
    cumulative_sel_identical,
    pile_strike_metrics,
    single_strike_sel,
)
from .propagation import (
    TransmissionLossResult,
    seawater_absorption,
    spreading_loss,
    transmission_loss,
)
from .seabed_reflection import (
    BottomLossResult,
    bottom_reflection_loss,
    critical_angle,
    reflection_coefficient,
)
from .ship_radiated_noise import (
    ShipSourceLevelResult,
    hydrophone_depths,
    monopole_source_level,
    radiated_noise_level,
    source_level_uncertainty,
)
from .ship_traffic_noise import (
    ShipTrafficSpectrum,
    VESSEL_CLASSES,
    ship_source_spectrum,
)
from .sonar_equation import (
    SonarEquationResult,
    active_sonar_equation,
    passive_sonar_equation,
)
from .sound_speed import (
    SoundSpeedProfile,
    depth_to_pressure,
    sea_water_sound_speed,
    sound_speed_profile,
)

__all__ = [
    "AmbientNoiseResult",
    "BottomLossResult",
    "NormalModeResult",
    "ParabolicEquationResult",
    "PileStrikeResult",
    "RayTraceResult",
    "ShipSourceLevelResult",
    "ShipTrafficSpectrum",
    "SonarEquationResult",
    "SoundSpeedProfile",
    "TransmissionLossResult",
    "UNDERWATER_REFERENCE_EXPOSURE",
    "UNDERWATER_REFERENCE_PRESSURE",
    "VESSEL_CLASSES",
    "active_sonar_equation",
    "bottom_reflection_loss",
    "critical_angle",
    "cumulative_sel",
    "cumulative_sel_identical",
    "depth_to_pressure",
    "hydrophone_depths",
    "in_air_to_underwater_spl",
    "monopole_source_level",
    "normal_modes",
    "ocean_ambient_noise",
    "parabolic_equation",
    "passive_sonar_equation",
    "peak_sound_pressure_level",
    "pile_strike_metrics",
    "radiated_noise_level",
    "ray_trace",
    "reflection_coefficient",
    "sea_water_sound_speed",
    "seawater_absorption",
    "ship_source_spectrum",
    "single_strike_sel",
    "sound_exposure_level",
    "sound_pressure_level",
    "sound_speed_profile",
    "source_level_uncertainty",
    "spreading_loss",
    "thermal_noise_spectrum",
    "transmission_loss",
    "underwater_to_in_air_spl",
    "wind_noise_spectrum",
]
