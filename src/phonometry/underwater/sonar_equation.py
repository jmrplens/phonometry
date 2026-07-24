#  Copyright (c) 2026. Jose M. Requena-Plens
"""
The sonar equation (passive and active), in decibels.

Combines the sonar performance terms -- source level ``SL``, transmission loss
``TL``, noise level ``NL``, directivity index ``DI``, detection threshold ``DT``,
target strength ``TS`` and reverberation level ``RL`` -- into the signal excess
``SE``, the signal-to-noise ratio and the figure of merit (the maximum allowable
transmission loss at the detection limit ``SE = 0``):

* :func:`passive_sonar_equation` -- ``SE = SL − TL − (NL − DI) − DT``.
* :func:`active_sonar_equation` -- monostatic, noise-limited
  ``SE = SL − 2·TL + TS − (NL − DI) − DT`` or, when a reverberation level is
  given, reverberation-limited ``SE = SL − 2·TL + TS − RL − DT``.

All quantities are in dB (levels re a plane wave of 1 µPa rms; the terms are
spectrum levels, i.e. referred to a 1 Hz band). Source: Urick, *Principles of
Underwater Sound*, via Etter (2003), Table 10.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import NDArray


def _finite(value: float, name: str) -> float:
    scalar = float(value)
    if not np.isfinite(scalar):
        raise ValueError(f"'{name}' must be a finite number.")
    return scalar


def _finite_array(values: NDArray[np.float64] | list[float] | float, name: str) -> NDArray[np.float64]:
    arr = np.atleast_1d(np.asarray(values, dtype=np.float64))
    if arr.size == 0 or not np.all(np.isfinite(arr)):
        raise ValueError(f"'{name}' must be finite and non-empty.")
    return arr


@dataclass(frozen=True)
class SonarEquationResult:
    """Sonar-equation solution.

    :ivar mode: ``"passive"`` or ``"active"``.
    :ivar signal_excess: Signal excess ``SE`` per transmission loss, in dB
        (detection when ``SE >= 0``).
    :ivar snr: Signal-to-noise (or signal-to-reverberation) ratio, in dB
        (``SE + DT``).
    :ivar figure_of_merit: Maximum allowable (one-way) transmission loss at the
        detection limit ``SE = 0``, in dB.
    :ivar transmission_loss: The transmission-loss values, in dB.
    :ivar source_level: Source level ``SL``, in dB.
    :ivar noise_level: Background noise level ``NL`` input, in dB. The masking
        term is ``NL − DI``, except when ``reverberation_limited`` is true, where
        the reverberation level ``RL`` masks instead.
    :ivar directivity_index: Receiver directivity index ``DI``, in dB.
    :ivar detection_threshold: Detection threshold ``DT``, in dB.
    :ivar target_strength: Target strength ``TS``, in dB (``None`` for passive).
    :ivar reverberation_limited: Whether the active case is reverberation-limited.
    """

    mode: str
    signal_excess: NDArray[np.float64]
    snr: NDArray[np.float64]
    figure_of_merit: float
    transmission_loss: NDArray[np.float64]
    source_level: float
    noise_level: float
    directivity_index: float
    detection_threshold: float
    target_strength: float | None
    reverberation_limited: bool

    def plot(self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any) -> Axes:
        """Plot signal excess versus transmission loss with the detection limit."""
        from .._i18n import check_language
        from .._plot.underwater import plot_sonar_equation

        return plot_sonar_equation(self, ax=ax, language=check_language(language), **kwargs)


def passive_sonar_equation(
    source_level: float,
    transmission_loss: NDArray[np.float64] | list[float] | float,
    noise_level: float,
    *,
    directivity_index: float = 0.0,
    detection_threshold: float = 0.0,
) -> SonarEquationResult:
    """Passive sonar equation ``SE = SL − TL − (NL − DI) − DT``.

    :param source_level: Source level ``SL`` (of the target), in dB.
    :param transmission_loss: One-way transmission loss ``TL``, in dB (scalar or
        array).
    :param noise_level: Background noise level ``NL``, in dB.
    :param directivity_index: Receiver directivity index ``DI``, in dB.
    :param detection_threshold: Detection threshold ``DT``, in dB.
    :return: A :class:`SonarEquationResult`.
    :raises ValueError: If an input is not finite.
    """
    sl = _finite(source_level, "source_level")
    nl = _finite(noise_level, "noise_level")
    di = _finite(directivity_index, "directivity_index")
    dt = _finite(detection_threshold, "detection_threshold")
    tl = _finite_array(transmission_loss, "transmission_loss")
    masking = nl - di
    snr = sl - tl - masking
    signal_excess = snr - dt
    fom = sl - masking - dt
    return SonarEquationResult(
        mode="passive",
        signal_excess=signal_excess,
        snr=snr,
        figure_of_merit=float(fom),
        transmission_loss=tl,
        source_level=sl,
        noise_level=nl,
        directivity_index=di,
        detection_threshold=dt,
        target_strength=None,
        reverberation_limited=False,
    )


def active_sonar_equation(
    source_level: float,
    transmission_loss: NDArray[np.float64] | list[float] | float,
    target_strength: float,
    noise_level: float,
    *,
    directivity_index: float = 0.0,
    detection_threshold: float = 0.0,
    reverberation_level: float | None = None,
) -> SonarEquationResult:
    """Monostatic active sonar equation with a two-way transmission loss.

    Noise-limited: ``SE = SL − 2·TL + TS − (NL − DI) − DT``. When
    ``reverberation_level`` is given, reverberation-limited:
    ``SE = SL − 2·TL + TS − RL − DT`` (``DI`` does not apply to reverberation).

    :param source_level: Source level ``SL``, in dB.
    :param transmission_loss: One-way transmission loss ``TL``, in dB (scalar or
        array); the equation applies ``2·TL``.
    :param target_strength: Target strength ``TS``, in dB.
    :param noise_level: Background noise level ``NL``, in dB.
    :param directivity_index: Receiver directivity index ``DI``, in dB.
    :param detection_threshold: Detection threshold ``DT``, in dB.
    :param reverberation_level: Reverberation level ``RL`` in dB; when given, the
        case is reverberation-limited.
    :return: A :class:`SonarEquationResult`.
    :raises ValueError: If an input is not finite.
    """
    sl = _finite(source_level, "source_level")
    ts = _finite(target_strength, "target_strength")
    nl = _finite(noise_level, "noise_level")
    di = _finite(directivity_index, "directivity_index")
    dt = _finite(detection_threshold, "detection_threshold")
    tl = _finite_array(transmission_loss, "transmission_loss")
    if reverberation_level is not None:
        masking = _finite(reverberation_level, "reverberation_level")
        reverb = True
    else:
        masking = nl - di
        reverb = False
    snr = sl - 2.0 * tl + ts - masking
    signal_excess = snr - dt
    fom = 0.5 * (sl + ts - masking - dt)
    return SonarEquationResult(
        mode="active",
        signal_excess=signal_excess,
        snr=snr,
        figure_of_merit=float(fom),
        transmission_loss=tl,
        source_level=sl,
        noise_level=nl,
        directivity_index=di,
        detection_threshold=dt,
        target_strength=ts,
        reverberation_limited=reverb,
    )
