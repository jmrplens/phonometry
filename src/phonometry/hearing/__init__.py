#  Copyright (c) 2026. Jose M. Requena-Plens
"""hearing domain of phonometry (see module docstrings)."""

from __future__ import annotations

from .noise_induced_hearing_loss import HtlanResult, NiptsResult, htlan, nipts
from .occupational_exposure import (
    COVERAGE_FACTOR,
    ExposureResult,
    INSTRUMENT_U2,
    OccupationalExposureWarning,
    Task,
    TaskContribution,
    full_day_exposure,
    job_based_exposure,
    minimum_cumulative_duration_hours,
    table_c4_contribution,
    task_based_exposure,
)
from .objective_intelligibility import STOIResult, stoi
from .sii import (
    SIIResult,
    StandardSpeechSpectrum,
    speech_intelligibility_index,
    standard_speech_spectra,
    standard_speech_spectrum,
)
from .sti import STIResult, STIWarning, sti_from_impulse_response, stipa, stipa_signal

from .threshold import (
    AUDIOMETRIC_FREQUENCIES,
    AgeThresholdResult,
    FIELDS,
    SEXES,
    age_threshold,
    reference_threshold,
)

__all__ = [
    "AUDIOMETRIC_FREQUENCIES",
    "AgeThresholdResult",
    "FIELDS",
    "SEXES",
    "age_threshold",
    "reference_threshold",

    "COVERAGE_FACTOR",
    "ExposureResult",
    "HtlanResult",
    "INSTRUMENT_U2",
    "NiptsResult",
    "OccupationalExposureWarning",
    "SIIResult",
    "STIResult",
    "STIWarning",
    "STOIResult",
    "StandardSpeechSpectrum",
    "Task",
    "TaskContribution",
    "full_day_exposure",
    "htlan",
    "job_based_exposure",
    "minimum_cumulative_duration_hours",
    "nipts",
    "speech_intelligibility_index",
    "standard_speech_spectra",
    "standard_speech_spectrum",
    "sti_from_impulse_response",
    "stipa",
    "stipa_signal",
    "stoi",
    "table_c4_contribution",
    "task_based_exposure",
]
