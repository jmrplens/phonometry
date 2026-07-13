#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Radiated underwater sound from percussive pile driving (ISO 18406:2017).

Percussive pile driving radiates a train of impulsive acoustic pulses, one per
hammer strike. ISO 18406 characterises them with:

* :func:`single_strike_sel` -- the single-strike sound exposure level
  ``SEL_ss`` of one pulse (Formulae 3-4), reusing the 1 µPa²·s reference.
* :func:`cumulative_sel` / :func:`cumulative_sel_identical` -- the cumulative
  sound exposure level over N strikes (Formulae 8-9); for N identical strikes
  ``SEL_cum = SEL_ss + 10·lg(N)``.
* :func:`pile_strike_metrics` -- a :class:`PileStrikeResult` bundling the
  single-strike SEL, the peak sound pressure level, the SPL/Leq and the
  90 %-energy pulse duration for one recorded strike, with a ``.plot()``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from .acoustics import (
    _positive,
    _validate_pressure,
    peak_sound_pressure_level,
    sound_exposure_level,
    sound_pressure_level,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import NDArray

#: Lower/upper cumulative-energy fractions defining the 90 % pulse duration.
_ENERGY_LOW = 0.05
_ENERGY_HIGH = 0.95


def single_strike_sel(pressure: "NDArray[np.float64] | list[float]", fs: float) -> float:
    """Single-strike sound exposure level ``SEL_ss`` (ISO 18406 Formulae 3-4).

    The sound exposure level of one hammer-strike pulse, integrated over the
    pulse, in dB re 1 µPa²·s.

    :param pressure: Sound-pressure time series of one strike (1-D), in Pa.
    :param fs: Sample rate, in Hz.
    :return: Single-strike SEL, in dB re 1 µPa²·s.
    :raises ValueError: If the inputs are invalid.
    """
    return sound_exposure_level(pressure, fs)


def cumulative_sel(single_sels: "NDArray[np.float64] | list[float]") -> float:
    """Cumulative sound exposure level over N strikes (ISO 18406 Formulae 8-9).

    ``SEL_cum = 10·lg(Σₙ 10^(SELₙ/10))`` -- the energy sum of the per-strike
    single-strike SELs.

    :param single_sels: Per-strike single-strike SELs, in dB re 1 µPa²·s.
    :return: Cumulative SEL, in dB re 1 µPa²·s.
    :raises ValueError: If the sequence is empty or non-finite.
    """
    sels = np.asarray(single_sels, dtype=np.float64)
    if sels.ndim != 1 or sels.size < 1:
        raise ValueError("'single_sels' must be a non-empty 1-D sequence.")
    if not np.all(np.isfinite(sels)):
        raise ValueError("'single_sels' must be finite.")
    return float(10.0 * np.log10(np.sum(10.0 ** (sels / 10.0))))


def cumulative_sel_identical(sel_ss: float, n_strikes: int) -> float:
    """Cumulative SEL of ``n_strikes`` identical strikes: ``SEL_ss + 10·lg(N)``.

    :param sel_ss: Single-strike SEL, in dB re 1 µPa²·s.
    :param n_strikes: Number of (identical) strikes, ``N ≥ 1``.
    :return: Cumulative SEL, in dB re 1 µPa²·s.
    :raises ValueError: If ``n_strikes`` is not a whole number ``≥ 1``.
    """
    n_float = float(n_strikes)
    if not n_float.is_integer():
        raise ValueError("'n_strikes' must be a whole number of strikes.")
    n = int(n_float)
    if n < 1:
        raise ValueError("'n_strikes' must be at least 1.")
    if not np.isfinite(sel_ss):
        raise ValueError("'sel_ss' must be finite.")
    return float(float(sel_ss) + 10.0 * np.log10(n))


def _pulse_duration(pressure: "NDArray[np.float64]", fs: float) -> float:
    """90 %-energy pulse duration: the time between the 5 % and 95 % energy points."""
    energy = np.cumsum(pressure**2)
    total = float(energy[-1])
    if total <= 0.0:
        return 0.0
    cum = energy / total
    lo = int(np.searchsorted(cum, _ENERGY_LOW))
    hi = int(np.searchsorted(cum, _ENERGY_HIGH))
    return float((hi - lo) / fs)


@dataclass(frozen=True)
class PileStrikeResult:
    """Per-strike pile-driving metrics (ISO 18406).

    :ivar single_strike_sel: Single-strike SEL, in dB re 1 µPa²·s.
    :ivar peak_spl: Zero-to-peak sound pressure level, in dB re 1 µPa.
    :ivar spl: Sound pressure level (Leq over the record), in dB re 1 µPa.
    :ivar pulse_duration: 90 %-energy pulse duration, in s.
    :ivar pressure: The strike pressure waveform, in Pa.
    :ivar fs: Sample rate, in Hz.
    """

    single_strike_sel: float
    peak_spl: float
    spl: float
    pulse_duration: float
    pressure: "NDArray[np.float64]"
    fs: float

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes | NDArray[Any]":
        """Plot the strike waveform and its cumulative energy."""
        from .._plot.underwater import plot_pile_strike

        return plot_pile_strike(self, ax=ax, **kwargs)


def pile_strike_metrics(
    pressure: "NDArray[np.float64] | list[float]", fs: float
) -> PileStrikeResult:
    """Full per-strike pile-driving metrics (ISO 18406).

    Bundles the single-strike SEL, the peak sound pressure level, the SPL/Leq
    and the 90 %-energy pulse duration of one recorded hammer strike.

    :param pressure: Sound-pressure time series of one strike (1-D), in Pa.
    :param fs: Sample rate, in Hz.
    :return: A :class:`PileStrikeResult`.
    :raises ValueError: If the inputs are invalid.
    """
    sig = _validate_pressure(pressure, min_samples=2)
    fs_v = _positive(fs, "fs")
    return PileStrikeResult(
        single_strike_sel=sound_exposure_level(sig, fs_v),
        peak_spl=peak_sound_pressure_level(sig),
        spl=sound_pressure_level(sig),
        pulse_duration=_pulse_duration(sig, fs_v),
        pressure=sig,
        fs=fs_v,
    )
