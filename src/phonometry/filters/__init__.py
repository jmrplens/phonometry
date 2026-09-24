#  Copyright (c) 2026. Jose Manuel Requena Plens
"""filters domain of phonometry (see module docstrings)."""

from __future__ import annotations

from .compliance import (
    FilterComplianceResult,
    class_limits,
    verify_filter_class,
)
from .core import (
    BlockProcessing,
    FilterBankWarning,
    FilterDesign,
    LevelCalibration,
    OctaveFilterBank,
    OctaveFilterResult,
    ResponsePlot,
    octave_filter,
)
from .equalizer import EQResponseResult, EQSection, ParametricEQ, parametric_eq
from .frequencies import (
    nominal_frequencies,
    normalized_frequencies,
)
from .periodic_tests import (
    PERIODIC_TEST_ATTENUATION_LIMITS_DB,
    FilterPeriodicMeasurements,
    FilterPeriodicVerification,
    PeriodicTestClause,
    periodic_test_frequencies,
    verify_filter_periodic,
)
from .time_invariance import (
    TimeInvarianceResult,
    swept_band_level,
    swept_level_uncertainty,
    verify_time_invariance,
)
from .weighting import (
    TimeWeightedEnvelope,
    TimeWeighting,
    WeightingFilter,
    linkwitz_riley,
    time_weighting,
    weighting_filter,
)
from .weighting_compliance import (
    WeightingComplianceResult,
    verify_weighting_class,
    weighting_class_limits,
)

__all__ = [
    "PERIODIC_TEST_ATTENUATION_LIMITS_DB",
    "BlockProcessing",
    "EQResponseResult",
    "EQSection",
    "FilterBankWarning",
    "FilterComplianceResult",
    "FilterDesign",
    "FilterPeriodicMeasurements",
    "FilterPeriodicVerification",
    "LevelCalibration",
    "OctaveFilterBank",
    "OctaveFilterResult",
    "ParametricEQ",
    "PeriodicTestClause",
    "ResponsePlot",
    "TimeInvarianceResult",
    "TimeWeightedEnvelope",
    "TimeWeighting",
    "WeightingComplianceResult",
    "WeightingFilter",
    "class_limits",
    "linkwitz_riley",
    "nominal_frequencies",
    "normalized_frequencies",
    "octave_filter",
    "parametric_eq",
    "periodic_test_frequencies",
    "swept_band_level",
    "swept_level_uncertainty",
    "time_weighting",
    "verify_filter_class",
    "verify_filter_periodic",
    "verify_time_invariance",
    "verify_weighting_class",
    "weighting_class_limits",
    "weighting_filter",
]
