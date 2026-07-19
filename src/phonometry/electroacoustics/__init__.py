#  Copyright (c) 2026. Jose M. Requena-Plens
"""electroacoustics domain of phonometry (see module docstrings)."""

from __future__ import annotations

from .distortion import (
    HarmonicDistortionResult,
    ModulationDistortionResult,
    difference_frequency_distortion,
    dynamic_intermodulation_distortion,
    dynamic_range,
    harmonic_analysis,
    harmonic_distortion,
    idle_channel_noise,
    itu_r_468_weighting,
    modulation_distortion,
    sinad,
    thd,
    thd_plus_noise,
    total_difference_frequency_distortion,
    weighted_thd,
)
from .frequency_response import FrequencyResponseResult, coherence, transfer_function
from .swept_sine import (
    SweptSineDistortionResult,
    swept_sine_distortion,
    synchronized_sweep_signal,
)

__all__ = [
    "FrequencyResponseResult",
    "HarmonicDistortionResult",
    "ModulationDistortionResult",
    "SweptSineDistortionResult",
    "coherence",
    "difference_frequency_distortion",
    "dynamic_intermodulation_distortion",
    "dynamic_range",
    "harmonic_analysis",
    "harmonic_distortion",
    "idle_channel_noise",
    "itu_r_468_weighting",
    "modulation_distortion",
    "sinad",
    "swept_sine_distortion",
    "synchronized_sweep_signal",
    "thd",
    "thd_plus_noise",
    "total_difference_frequency_distortion",
    "transfer_function",
    "weighted_thd",
]
