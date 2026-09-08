#  Copyright (c) 2026. Jose Manuel Requena Plens
"""hearing domain of phonometry (see module docstrings).

Narrowed in 4.0 to hearing conservation: audiometric thresholds, noise-induced
hearing loss and occupational exposure. Speech intelligibility (STI, SII, STOI)
moved to :mod:`phonometry.speech`, which evaluates a transmission channel
rather than an ear.
"""

from __future__ import annotations

from .hearing_protectors import (
    HML_REFERENCE_C_MINUS_A,
    HML_REFERENCE_D,
    HML_REFERENCE_NOISES,
    PINK_NOISE_A_WEIGHTED,
    PROTECTION_PERFORMANCES,
    PROTECTOR_A_WEIGHTING,
    PROTECTOR_OCTAVE_BANDS,
    AssumedProtectionResult,
    HMLRatingResult,
    ProtectedLevelResult,
    SNRRatingResult,
    assumed_protection_value,
    hml_protected_level,
    hml_rating,
    octave_band_protected_level,
    snr_protected_level,
    snr_rating,
)
from .noise_induced_hearing_loss import (
    HtlanResult,
    NiptsResult,
    NoiseInducedHearingLossWarning,
    combine_age_and_noise,
    htlan,
    nipts,
)
from .occupational_exposure import (
    COVERAGE_FACTOR,
    INSTRUMENT_U2,
    ExposureResult,
    OccupationalExposureWarning,
    Task,
    TaskContribution,
    full_day_exposure,
    job_based_exposure,
    minimum_cumulative_duration_hours,
    table_c4_contribution,
    task_based_exposure,
)
from .threshold import (
    AUDIOMETRIC_FREQUENCIES,
    EARPHONE_COUPLERS,
    EARPHONES,
    FIELDS,
    RETSPL_FREQUENCIES_HZ,
    SEXES,
    AgeThresholdResult,
    age_threshold,
    earphone_reference_level,
    hearing_level_to_coupler_spl,
    reference_threshold,
)

__all__ = [
    "age_threshold",
    "AgeThresholdResult",
    "assumed_protection_value",
    "AssumedProtectionResult",
    "AUDIOMETRIC_FREQUENCIES",
    "combine_age_and_noise",
    "COVERAGE_FACTOR",
    "EARPHONE_COUPLERS",
    "earphone_reference_level",
    "EARPHONES",
    "ExposureResult",
    "FIELDS",
    "full_day_exposure",
    "hearing_level_to_coupler_spl",
    "hml_protected_level",
    "hml_rating",
    "HML_REFERENCE_C_MINUS_A",
    "HML_REFERENCE_D",
    "HML_REFERENCE_NOISES",
    "HMLRatingResult",
    "htlan",
    "HtlanResult",
    "INSTRUMENT_U2",
    "job_based_exposure",
    "minimum_cumulative_duration_hours",
    "nipts",
    "NiptsResult",
    "NoiseInducedHearingLossWarning",
    "OccupationalExposureWarning",
    "octave_band_protected_level",
    "PINK_NOISE_A_WEIGHTED",
    "ProtectedLevelResult",
    "PROTECTION_PERFORMANCES",
    "PROTECTOR_A_WEIGHTING",
    "PROTECTOR_OCTAVE_BANDS",
    "reference_threshold",
    "RETSPL_FREQUENCIES_HZ",
    "SEXES",
    "snr_protected_level",
    "snr_rating",
    "SNRRatingResult",
    "table_c4_contribution",
    "Task",
    "task_based_exposure",
    "TaskContribution",
]
