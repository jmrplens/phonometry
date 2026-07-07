#  Copyright (c) 2020. Jose M. Requena-Plens
"""
Octave-Band and Fractional Octave-Band filter for signals in the time domain.
Implementation according to ANSI s1.11-2004 and IEC 61260-1-2014.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple, overload, Literal

import numpy as np

from .calibration import CalibrationWarning, calculate_sensitivity
from .environmental import composite_rating_level, lden, ldn
from .compliance import verify_filter_class
from .core import OctaveFilterBank
from .frequencies import getansifrequencies, normalizedfreq
from .intensity import (
    FieldIndicators,
    IntensityResult,
    dynamic_capability_index,
    field_indicators,
    sound_intensity,
)
from .levels import laeq, lc_peak, leq, lex_8h, ln_levels, sel, sound_exposure
from .loudness import ZwickerLoudness, loudness_zwicker, loudness_zwicker_from_spectrum
from .loudness_contours import equal_loudness_contour, hearing_threshold, loudness_level
from .sharpness import sharpness_din, sharpness_din_from_specific
from .sti import STIResult, sti_from_impulse_response, stipa, stipa_signal
from .tonality import ToneAssessment, prominence_ratio, tone_to_noise_ratio
from .parametric_filters import (
    TimeWeighting,
    WeightingFilter,
    linkwitz_riley,
    time_weighting,
    weighting_filter,
)
from .insulation import (
    AirborneInsulationResult,
    ImpactInsulationResult,
    ImpactRatingResult,
    WeightedRatingResult,
    airborne_insulation,
    energy_average_level,
    impact_insulation,
    weighted_impact_rating,
    weighted_rating,
)
from .open_plan import OpenPlanResult, open_plan_metrics
from .sound_power import (
    SoundPowerResult,
    SoundPowerWarning,
    background_noise_correction,
    environmental_correction,
    measurement_positions,
    sound_power_pressure,
)
from .sound_power_reverberation import (
    ReverberationSoundPowerResult,
    sound_power_comparison,
    sound_power_reverberation,
)
from .sound_power_intensity import (
    SoundPowerIntensityResult,
    sound_power_intensity,
)
from .room_acoustics import RoomAcousticsResult, decay_curve, room_parameters
from .sound_absorption import (
    AbsorptionWarning,
    absorption_area,
    absorption_coefficient,
    attenuation_from_alpha,
)
from .room_ir import (
    impulse_response,
    inverse_filter,
    mls_impulse_response,
    mls_signal,
    sweep_signal,
)
from ._version import __version__

# Public methods
__all__ = [
    "__version__",
    "octavefilter",
    "getansifrequencies",
    "normalizedfreq",
    "OctaveFilterBank",
    "WeightingFilter",
    "weighting_filter",
    "time_weighting",
    "TimeWeighting",
    "linkwitz_riley",
    "calculate_sensitivity",
    "leq",
    "laeq",
    "ln_levels",
    "lc_peak",
    "sel",
    "sound_exposure",
    "lex_8h",
    "loudness_zwicker",
    "loudness_zwicker_from_spectrum",
    "ZwickerLoudness",
    "sharpness_din",
    "sharpness_din_from_specific",
    "equal_loudness_contour",
    "loudness_level",
    "hearing_threshold",
    "tone_to_noise_ratio",
    "prominence_ratio",
    "ToneAssessment",
    "sound_intensity",
    "IntensityResult",
    "field_indicators",
    "FieldIndicators",
    "dynamic_capability_index",
    "sti_from_impulse_response",
    "stipa",
    "stipa_signal",
    "STIResult",
    "sweep_signal",
    "inverse_filter",
    "impulse_response",
    "mls_signal",
    "mls_impulse_response",
    "room_parameters",
    "decay_curve",
    "RoomAcousticsResult",
    "absorption_area",
    "absorption_coefficient",
    "attenuation_from_alpha",
    "AbsorptionWarning",
    "open_plan_metrics",
    "OpenPlanResult",
    "sound_power_pressure",
    "measurement_positions",
    "background_noise_correction",
    "environmental_correction",
    "SoundPowerResult",
    "SoundPowerWarning",
    "sound_power_reverberation",
    "sound_power_comparison",
    "ReverberationSoundPowerResult",
    "sound_power_intensity",
    "SoundPowerIntensityResult",
    "airborne_insulation",
    "AirborneInsulationResult",
    "impact_insulation",
    "ImpactInsulationResult",
    "weighted_rating",
    "WeightedRatingResult",
    "weighted_impact_rating",
    "ImpactRatingResult",
    "energy_average_level",
    "lden",
    "ldn",
    "composite_rating_level",
    "CalibrationWarning",
    "verify_filter_class",
]


@lru_cache(maxsize=32)
def _cached_filter_bank(
    fs: int,
    fraction: float,
    order: int,
    limits: Tuple[float, ...] | None,
    filter_type: str,
    ripple: float,
    attenuation: float,
    calibration_factor: float,
    dbfs: bool,
) -> OctaveFilterBank:
    """Design (or reuse) a stateless filter bank for octavefilter()."""
    return OctaveFilterBank(
        fs=fs,
        fraction=fraction,
        order=order,
        limits=list(limits) if limits is not None else None,
        filter_type=filter_type,
        ripple=ripple,
        attenuation=attenuation,
        calibration_factor=calibration_factor,
        dbfs=dbfs,
    )


@overload
def octavefilter(
    x: List[float] | np.ndarray,  # NOSONAR - public API
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    show: bool = False,
    sigbands: Literal[False] = False,
    plot_file: str | None = None,
    detrend: bool = True,
    filter_type: str = "butter",
    ripple: float = 0.1,
    attenuation: float = 72.0,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    mode: str = "rms",
    nominal: Literal[False] = False,
) -> Tuple[np.ndarray, List[float]]: ...


@overload
def octavefilter(
    x: List[float] | np.ndarray,  # NOSONAR - public API
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    show: bool = False,
    sigbands: Literal[True] = True,
    plot_file: str | None = None,
    detrend: bool = True,
    filter_type: str = "butter",
    ripple: float = 0.1,
    attenuation: float = 72.0,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    mode: str = "rms",
    nominal: Literal[False] = False,
) -> Tuple[np.ndarray, List[float], List[np.ndarray]]: ...


@overload
def octavefilter(
    x: List[float] | np.ndarray,  # NOSONAR - public API
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    show: bool = False,
    sigbands: Literal[False] = False,
    plot_file: str | None = None,
    detrend: bool = True,
    filter_type: str = "butter",
    ripple: float = 0.1,
    attenuation: float = 72.0,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    mode: str = "rms",
    nominal: Literal[True] = ...,
) -> Tuple[np.ndarray, List[str]]: ...


@overload
def octavefilter(
    x: List[float] | np.ndarray,  # NOSONAR - public API
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    show: bool = False,
    sigbands: Literal[True] = True,
    plot_file: str | None = None,
    detrend: bool = True,
    filter_type: str = "butter",
    ripple: float = 0.1,
    attenuation: float = 72.0,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    mode: str = "rms",
    nominal: Literal[True] = ...,
) -> Tuple[np.ndarray, List[str], List[np.ndarray]]: ...


def octavefilter(
    x: List[float] | np.ndarray,  # NOSONAR - public API
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    show: bool = False,
    sigbands: bool = False,
    plot_file: str | None = None,
    detrend: bool = True,
    filter_type: str = "butter",
    ripple: float = 0.1,
    attenuation: float = 72.0,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    mode: str = "rms",
    nominal: bool = False,
) -> Tuple[np.ndarray, List[float]] | Tuple[np.ndarray, List[str]] | Tuple[np.ndarray, List[float], List[np.ndarray]] | Tuple[np.ndarray, List[str], List[np.ndarray]]:
    """
    Filter a signal with octave or fractional octave filter bank.

    This method uses a filter bank with Second-Order Sections (SOS) coefficients.
    To obtain the correct coefficients, automatic subsampling is applied to the
    signal in each filtered band.

    Multichannel support: If x is 2D (channels, samples), each channel is filtered.

    :param x: Input signal (1D array or 2D array [channels, samples]).
    :type x: Union[List[float], np.ndarray]
    :param fs: Sample rate in Hz.
    :type fs: int
    :param fraction: Bandwidth 'b'. Examples: 1/3-octave b=3, 1-octave b=1, 2/3-octave b=1.5. Default: 1.
    :type fraction: float
    :param order: Order of the filter. Default: 6.
    :type order: int
    :param limits: Minimum and maximum limit frequencies [f_min, f_max]. Default [12, 20000].
    :type limits: Optional[List[float]]
    :param show: If True, plot and show the filter response.
    :type show: bool
    :param sigbands: If True, also return the signal in the time domain divided into bands.
    :type sigbands: bool
    :param plot_file: Path to save the filter response plot.
    :type plot_file: Optional[str]
    :param detrend: If True, remove DC offset before filtering. Default: True.
    :type detrend: bool
    :param filter_type: Type of filter ('butter', 'cheby1', 'cheby2', 'ellip', 'bessel').
        Default: 'butter' (the only type that meets IEC 61260-1 class 1 with the
        default parameters).
    :param ripple: Passband ripple in dB (for cheby1, ellip). Default: 0.1.
    :param attenuation: Stopband attenuation in dB (for cheby2, ellip). Default: 72.0.
        For ``cheby2`` scipy pins the deep-stopband floor at exactly this value,
        so it must be >= 70 dB to clear the IEC 61260-1 class 1 limit (matches
        :class:`OctaveFilterBank`).
    :param calibration_factor: Calibration factor for SPL calculation. Default: 1.0.
    :param dbfs: If True, return results in dBFS. Default: False.
    :param mode: 'rms' or 'peak'. Default: 'rms'.
    :param nominal: If True, return IEC 61260-1 nominal frequency labels (List[str]) instead of exact floats.
    :return: A tuple containing (SPL_array, Frequencies_list) or (SPL_array, Frequencies_list, signals).
        When *nominal=True*, the frequency list contains ``List[str]`` labels instead of floats.
    :rtype: Union[Tuple[np.ndarray, List[float]], Tuple[np.ndarray, List[str]],
        Tuple[np.ndarray, List[float], List[np.ndarray]],
        Tuple[np.ndarray, List[str], List[np.ndarray]]]
    """
    
    if show or plot_file:
        # Plotting has side effects: bypass the cache.
        filter_bank = OctaveFilterBank(
            fs=fs,
            fraction=fraction,
            order=order,
            limits=limits,
            filter_type=filter_type,
            ripple=ripple,
            attenuation=attenuation,
            show=show,
            plot_file=plot_file,
            calibration_factor=calibration_factor,
            dbfs=dbfs,
        )
    else:
        # The bank is immutable in non-stateful mode: reuse the design.
        # Pass limits through as-is (tuple for hashability); the bank
        # constructor is the single place that validates them and owns
        # the default when None.
        limits_key = tuple(map(float, limits)) if limits is not None else None
        filter_bank = _cached_filter_bank(
            fs, fraction, order, limits_key, filter_type,
            ripple, attenuation, calibration_factor, dbfs,
        )

    return filter_bank.filter(x, sigbands=sigbands, mode=mode, detrend=detrend, nominal=nominal)  # type: ignore[call-overload,no-any-return]
