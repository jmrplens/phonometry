#  Copyright (c) 2026. Jose Manuel Requena Plens
"""metrology domain of phonometry (see module docstrings).

Narrowed in 4.0 to the transverse metrology: calibration, GUM uncertainty,
data qualification and the ISO 1683 reference values every level is counted
from. The filter banks and weightings moved to
:mod:`phonometry.filters`, the general signal analysis to
:mod:`phonometry.signals` and the IEC 61043 intensity-instrument class check
to :mod:`phonometry.emission.intensity_compliance`, which is what it verifies.
"""

from __future__ import annotations

from .calibration import CalibrationWarning, sensitivity
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
    "ISO1683_REFERENCE_VALUES",
    "CalibrationWarning",
    "LevelCrossingResult",
    "MonteCarloResult",
    "PeakStatisticsResult",
    "Quantity",
    "ReferenceValue",
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
]
