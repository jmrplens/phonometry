#  Copyright (c) 2026. Jose M. Requena-Plens
"""metrology domain of phonometry (see module docstrings)."""

from __future__ import annotations

from .calibration import CalibrationWarning, calculate_sensitivity, sensitivity
from .compliance import (
    class_limits,
    verify_aircraft_noise_system,
    verify_filter_class,
    verify_weighting_class,
    weighting_class_limits,
)
from .core import FilterBankWarning, OctaveFilterBank, octave_filter, octavefilter
from .correlation import (
    AlignedImpulseResponseResult,
    CorrelationResult,
    TimeDelayResult,
    align_impulse_responses,
    correlation,
    correlation_random_error,
    impulse_response_delay,
    time_delay,
)
from .envelope import EnvelopeResult, envelope
from .frequencies import (
    getansifrequencies,
    nominal_frequencies,
    normalized_frequencies,
    normalizedfreq,
)
from .levels import laeq, lc_peak, leq, lex_8h, ln_levels, sel, sound_exposure
from .parametric_filters import (
    TimeWeighting,
    WeightingFilter,
    linkwitz_riley,
    time_weighting,
    weighting_filter,
)
from .phase import (
    PhaseDecompositionResult,
    excess_phase,
    group_delay,
    minimum_phase,
    phase_decomposition,
)
from .signals import noise_signal
from .spectra import (
    CoherentOutputSpectrumResult,
    CrossSpectralDensityResult,
    SpectralDensityResult,
    coherent_output_spectrum,
    cross_spectral_density,
    fractional_octave_smoothing,
    power_spectral_density,
    resolution_bias_error,
)
from .uncertainty import (
    MonteCarloResult,
    Quantity,
    UncertaintyResult,
    UncertaintyWarning,
    combine_uncertainty,
    monte_carlo,
    rectangular,
    triangular,
    u_shaped,
)

__all__ = [
    "AlignedImpulseResponseResult",
    "CalibrationWarning",
    "CoherentOutputSpectrumResult",
    "CorrelationResult",
    "CrossSpectralDensityResult",
    "EnvelopeResult",
    "FilterBankWarning",
    "MonteCarloResult",
    "OctaveFilterBank",
    "PhaseDecompositionResult",
    "Quantity",
    "SpectralDensityResult",
    "TimeDelayResult",
    "TimeWeighting",
    "UncertaintyResult",
    "UncertaintyWarning",
    "WeightingFilter",
    "align_impulse_responses",
    "calculate_sensitivity",
    "class_limits",
    "coherent_output_spectrum",
    "combine_uncertainty",
    "correlation",
    "correlation_random_error",
    "cross_spectral_density",
    "envelope",
    "excess_phase",
    "fractional_octave_smoothing",
    "getansifrequencies",
    "group_delay",
    "impulse_response_delay",
    "laeq",
    "lc_peak",
    "leq",
    "lex_8h",
    "linkwitz_riley",
    "ln_levels",
    "minimum_phase",
    "monte_carlo",
    "noise_signal",
    "nominal_frequencies",
    "normalized_frequencies",
    "normalizedfreq",
    "octave_filter",
    "octavefilter",
    "phase_decomposition",
    "power_spectral_density",
    "rectangular",
    "resolution_bias_error",
    "sel",
    "sensitivity",
    "sound_exposure",
    "time_delay",
    "time_weighting",
    "triangular",
    "u_shaped",
    "verify_aircraft_noise_system",
    "verify_filter_class",
    "verify_weighting_class",
    "weighting_class_limits",
    "weighting_filter",
]
