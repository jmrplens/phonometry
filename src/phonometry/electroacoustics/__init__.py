#  Copyright (c) 2026. Jose M. Requena-Plens
"""electroacoustics domain of phonometry (see module docstrings)."""

from __future__ import annotations

from .distortion import (
    HarmonicDistortionResult,
    difference_frequency_distortion,
    dynamic_intermodulation_distortion,
    harmonic_analysis,
    harmonic_distortion,
    modulation_distortion,
    sinad,
    thd,
    thd_plus_noise,
    total_difference_frequency_distortion,
    weighted_thd,
)
from .frequency_response import FrequencyResponseResult, coherence, transfer_function

__all__ = [
    "FrequencyResponseResult",
    "HarmonicDistortionResult",
    "coherence",
    "difference_frequency_distortion",
    "dynamic_intermodulation_distortion",
    "harmonic_analysis",
    "harmonic_distortion",
    "modulation_distortion",
    "sinad",
    "thd",
    "thd_plus_noise",
    "total_difference_frequency_distortion",
    "transfer_function",
    "weighted_thd",
]
