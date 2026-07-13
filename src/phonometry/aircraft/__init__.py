#  Copyright (c) 2026. Jose M. Requena-Plens
"""aircraft domain of phonometry (see module docstrings)."""

from __future__ import annotations

from .aircraft_noise import (
    EPNLResult,
    NOY_BANDS,
    effective_perceived_noise_level,
    epnl_from_pnlt,
    perceived_noise_level,
    perceived_noisiness,
    tone_correction,
)
from .airport_noise import (
    FlyoverResult,
    NoiseContourResult,
    NpdLevelResult,
    duration_correction,
    engine_installation_correction,
    event_level,
    impedance_adjustment,
    lateral_attenuation,
    noise_contour,
    noise_fraction,
    npd_curve,
    npd_level,
    start_of_roll_directivity,
)
from .atmospheric_absorption import AircraftBandAttenuation, sae_band_attenuation
from .rotorcraft_noise import (
    RotorcraftHemisphere,
    atmospheric_adjustment,
    ground_effect_adjustment,
    hemisphere_source_level,
    spherical_spreading_adjustment,
)

__all__ = [
    "AircraftBandAttenuation",
    "EPNLResult",
    "FlyoverResult",
    "NOY_BANDS",
    "NoiseContourResult",
    "NpdLevelResult",
    "RotorcraftHemisphere",
    "atmospheric_adjustment",
    "duration_correction",
    "effective_perceived_noise_level",
    "engine_installation_correction",
    "epnl_from_pnlt",
    "event_level",
    "ground_effect_adjustment",
    "hemisphere_source_level",
    "impedance_adjustment",
    "lateral_attenuation",
    "noise_contour",
    "noise_fraction",
    "npd_curve",
    "npd_level",
    "perceived_noise_level",
    "perceived_noisiness",
    "sae_band_attenuation",
    "spherical_spreading_adjustment",
    "start_of_roll_directivity",
    "tone_correction",
]
