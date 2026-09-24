#  Copyright (c) 2026. Jose Manuel Requena Plens
"""metrology domain of phonometry (see module docstrings).

Narrowed in 4.0 to the transverse metrology: calibration, GUM uncertainty,
data qualification, the ISO 1683 reference values every level is counted
from, the conformance rule IEC TC 29 grades every instrument by, and the
IEC 60942 verdict on the sound calibrator every calibration starts from. The filter banks and weightings moved to
:mod:`phonometry.filters`, the general signal analysis to
:mod:`phonometry.signals` and the IEC 61043 intensity-instrument class check
to :mod:`phonometry.emission.intensity_compliance`, which is what it verifies.
"""

from __future__ import annotations

from .calibration import CalibrationWarning, sensitivity
from .conformance import ConformanceVerification, verify_conformance
from .data_qualification import (
    LevelCrossingResult,
    PeakStatisticsResult,
    StationarityTestResult,
    TrendTestResult,
    level_crossing_rate,
    peak_statistics,
    stationarity_test,
    trend_test,
)
from .reference_values import ISO1683_REFERENCE_VALUES, ReferenceValue
from .sound_calibrator import (
    ABBREVIATED_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT,
    ABBREVIATED_LEVEL_REDUCTIONS_DB,
    CALIBRATOR_CLASSES,
    CALIBRATOR_REQUIREMENTS,
    DISTORTION_ACCEPTANCE_LIMITS_PERCENT,
    DISTORTION_MAX_UNCERTAINTY_PERCENT,
    ENVIRONMENTAL_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT,
    ENVIRONMENTAL_FREQUENCY_MAX_UNCERTAINTY_PERCENT,
    ENVIRONMENTAL_LEVEL_ACCEPTANCE_LIMITS_DB,
    ENVIRONMENTAL_LEVEL_MAX_UNCERTAINTY_DB,
    FIELD_IMMUNITY_ACCEPTANCE_LIMITS_DB,
    FIELD_IMMUNITY_MAX_UNCERTAINTY_DB,
    FLUCTUATION_ACCEPTANCE_LIMITS_DB,
    FLUCTUATION_MAX_UNCERTAINTY_DB,
    FREQUENCY_ACCEPTANCE_LIMITS_PERCENT,
    FREQUENCY_MAX_UNCERTAINTY_PERCENT,
    LEVEL_ACCEPTANCE_LIMITS_DB,
    LEVEL_MAX_UNCERTAINTY_DB,
    SUPPLY_VOLTAGE_ACCEPTANCE_LIMITS_DB,
    SUPPLY_VOLTAGE_MAX_UNCERTAINTY_DB,
    CalibratorTableRow,
    SoundCalibratorMeasurements,
    SoundCalibratorRequirement,
    SoundCalibratorVerification,
    verify_sound_calibrator,
)
from .uncertainty import (
    MonteCarloResult,
    Quantity,
    UncertaintyResult,
    UncertaintyWarning,
    combine_uncertainty,
    coverage_factor,
    expanded_uncertainty,
    monte_carlo,
    rectangular,
    triangular,
    u_shaped,
)

__all__ = [
    "ABBREVIATED_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT",
    "ABBREVIATED_LEVEL_REDUCTIONS_DB",
    "CALIBRATOR_CLASSES",
    "CALIBRATOR_REQUIREMENTS",
    "DISTORTION_ACCEPTANCE_LIMITS_PERCENT",
    "DISTORTION_MAX_UNCERTAINTY_PERCENT",
    "ENVIRONMENTAL_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT",
    "ENVIRONMENTAL_FREQUENCY_MAX_UNCERTAINTY_PERCENT",
    "ENVIRONMENTAL_LEVEL_ACCEPTANCE_LIMITS_DB",
    "ENVIRONMENTAL_LEVEL_MAX_UNCERTAINTY_DB",
    "FIELD_IMMUNITY_ACCEPTANCE_LIMITS_DB",
    "FIELD_IMMUNITY_MAX_UNCERTAINTY_DB",
    "FLUCTUATION_ACCEPTANCE_LIMITS_DB",
    "FLUCTUATION_MAX_UNCERTAINTY_DB",
    "FREQUENCY_ACCEPTANCE_LIMITS_PERCENT",
    "FREQUENCY_MAX_UNCERTAINTY_PERCENT",
    "ISO1683_REFERENCE_VALUES",
    "LEVEL_ACCEPTANCE_LIMITS_DB",
    "LEVEL_MAX_UNCERTAINTY_DB",
    "SUPPLY_VOLTAGE_ACCEPTANCE_LIMITS_DB",
    "SUPPLY_VOLTAGE_MAX_UNCERTAINTY_DB",
    "CalibrationWarning",
    "CalibratorTableRow",
    "ConformanceVerification",
    "LevelCrossingResult",
    "MonteCarloResult",
    "PeakStatisticsResult",
    "Quantity",
    "ReferenceValue",
    "SoundCalibratorMeasurements",
    "SoundCalibratorRequirement",
    "SoundCalibratorVerification",
    "StationarityTestResult",
    "TrendTestResult",
    "UncertaintyResult",
    "UncertaintyWarning",
    "combine_uncertainty",
    "coverage_factor",
    "expanded_uncertainty",
    "level_crossing_rate",
    "monte_carlo",
    "peak_statistics",
    "rectangular",
    "sensitivity",
    "stationarity_test",
    "trend_test",
    "triangular",
    "u_shaped",
    "verify_conformance",
    "verify_sound_calibrator",
]
