#  Copyright (c) 2026. Jose M. Requena-Plens
"""environmental domain of phonometry (see module docstrings)."""

from __future__ import annotations

from .air_absorption import (
    AtmosphericAbsorptionWarning,
    air_attenuation,
    air_attenuation_m,
)
from .impulse_prominence import (
    ImpulseProminenceResult,
    ImpulseProminenceWarning,
    impulse_adjustment,
    impulse_prominence,
    predicted_prominence,
    rating_level,
)
from .outdoor_propagation import (
    Barrier,
    DEFAULT_FREQUENCIES,
    OutdoorAttenuation,
    atmospheric_absorption,
    barrier_attenuation,
    directivity_omega,
    geometric_divergence,
    ground_attenuation,
    ground_attenuation_alternative,
    meteorological_correction,
    outdoor_propagation_attenuation,
    predicted_receiver_level,
)
from .wind_turbine_noise import (
    WindTurbineNoiseWarning,
    WindTurbineTonalityResult,
    apparent_sound_power_level,
    slant_distance,
    wind_turbine_tonality,
)

from .rating import (
    composite_rating_level,
    lden,
    ldn,
)

from .measurement import (
    EnvironmentalMeasurementWarning,
    RepeatedMeasurementResult,
    ResidualCorrectionResult,
    TonalAssessmentResult,
    assess_tonal_audibility,
    combined_standard_uncertainty,
    critical_bandwidth,
    expanded_uncertainty,
    gaussian_residual_level,
    residual_correction_uncertainty,
    residual_sound_correction,
    tonal_adjustment,
    tonal_adjustment_from_mean_audibility,
    tonal_audibility,
    tonal_seeking_survey,
    uncertainty_from_repeated_measurements,
)

__all__ = [
    "EnvironmentalMeasurementWarning",
    "RepeatedMeasurementResult",
    "ResidualCorrectionResult",
    "TonalAssessmentResult",
    "assess_tonal_audibility",
    "combined_standard_uncertainty",
    "critical_bandwidth",
    "expanded_uncertainty",
    "gaussian_residual_level",
    "residual_correction_uncertainty",
    "residual_sound_correction",
    "tonal_adjustment",
    "tonal_adjustment_from_mean_audibility",
    "tonal_audibility",
    "tonal_seeking_survey",
    "uncertainty_from_repeated_measurements",

    "composite_rating_level",
    "lden",
    "ldn",

    "AtmosphericAbsorptionWarning",
    "Barrier",
    "DEFAULT_FREQUENCIES",
    "ImpulseProminenceResult",
    "ImpulseProminenceWarning",
    "OutdoorAttenuation",
    "WindTurbineNoiseWarning",
    "WindTurbineTonalityResult",
    "air_attenuation",
    "air_attenuation_m",
    "apparent_sound_power_level",
    "atmospheric_absorption",
    "barrier_attenuation",
    "directivity_omega",
    "geometric_divergence",
    "ground_attenuation",
    "ground_attenuation_alternative",
    "impulse_adjustment",
    "impulse_prominence",
    "meteorological_correction",
    "outdoor_propagation_attenuation",
    "predicted_prominence",
    "predicted_receiver_level",
    "rating_level",
    "slant_distance",
    "wind_turbine_tonality",
]
