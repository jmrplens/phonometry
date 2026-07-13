#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the electroacoustics domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_PRIMARY,
    _C_SECONDARY,
    _C_TERTIARY,
    _LEGEND_UPPER_RIGHT,
    _format_freq,
    _new_axes,
    _new_axes_column,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from ..electroacoustics.distortion import HarmonicDistortionResult
    from ..electroacoustics.frequency_response import FrequencyResponseResult

def plot_harmonic_distortion(
    result: "HarmonicDistortionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Harmonic amplitude spectrum with the harmonics marked and THD annotated.

    Draws the fundamental and its harmonics as a stem-style amplitude spectrum
    in dB relative to the fundamental, annotated with the THD (both
    conventions) and SINAD.

    :param result: A :class:`~phonometry.distortion.HarmonicDistortionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the marker ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    amps = np.asarray(result.harmonic_amplitudes, dtype=np.float64)
    tiny = np.finfo(np.float64).tiny
    ref = amps[0] if amps.size and amps[0] > 0.0 else 1.0
    levels_db = 20.0 * np.log10(np.maximum(amps, tiny) / ref)
    orders = np.arange(1, amps.size + 1)

    ax.vlines(orders, -160.0, levels_db, color=_C_PRIMARY, lw=1.5)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Harmonics")
    ax.plot(orders, levels_db, "o", **kwargs)
    for order, level in zip(orders, levels_db):
        if level > -160.0:
            ax.annotate(
                f"{order}",
                (order, level),
                textcoords="offset points",
                xytext=(0, 5),
                ha="center",
                fontsize="x-small",
            )
    ax.set_xlabel("Harmonic order n  (f = n·f₁)")
    ax.set_ylabel("Level re fundamental [dB]")
    ax.set_xticks(orders)
    ax.set_ylim(bottom=-160.0, top=10.0)
    ax.set_title(
        f"IEC 60268-3 THD = {result.thd_f * 100.0:.3g}% (F), "
        f"{result.thd_r * 100.0:.3g}% (R); SINAD = {result.sinad_db:.1f} dB "
        f"(f₁ = {_format_freq(result.fundamental)}Hz)"
    )
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    return ax

def plot_frequency_response(
    result: "FrequencyResponseResult", ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Bode magnitude / phase and coherence of an estimated frequency response.

    Three stacked panels: the magnitude in dB, the phase in degrees and the
    ordinary coherence ``γ²``. With ``ax`` given, only the magnitude panel is
    drawn on it.

    :param result: A
        :class:`~phonometry.frequency_response.FrequencyResponseResult`.
    :param ax: Existing axes for the magnitude panel, or ``None`` for a fresh
        three-panel figure.
    :param kwargs: Forwarded to the magnitude ``plot`` call.
    :return: The magnitude-panel axes (``ax`` given) or the array of three axes.
    """
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    mag = np.asarray(result.magnitude_db, dtype=np.float64)
    phase_deg = np.degrees(np.asarray(result.phase, dtype=np.float64))
    coh = np.asarray(result.coherence, dtype=np.float64)
    pos = freqs > 0.0
    color = kwargs.pop("color", _C_PRIMARY)

    def _magnitude(axm: Axes) -> None:
        kwargs.setdefault("label", f"|H| ({result.estimator})")
        axm.semilogx(freqs[pos], mag[pos], color=color, **kwargs)
        axm.set_ylabel("Magnitude [dB]")
        axm.grid(True, which="both", alpha=0.3)
        axm.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _magnitude(ax)
        ax.set_xlabel("Frequency [Hz]")
        ax.set_title(f"Frequency response ({result.estimator})")
        return ax

    axes = _new_axes_column(3, sharex=True, figsize=(8.0, 8.0))
    _magnitude(axes[0])
    axes[0].set_title(f"Frequency response ({result.estimator}) and coherence")
    axes[1].semilogx(freqs[pos], phase_deg[pos], color=_C_SECONDARY)
    axes[1].set_ylabel("Phase [deg]")
    axes[1].grid(True, which="both", alpha=0.3)
    axes[2].semilogx(freqs[pos], coh[pos], color=_C_TERTIARY)
    axes[2].set_ylabel(r"Coherence $\gamma^2$")
    axes[2].set_xlabel("Frequency [Hz]")
    axes[2].set_ylim(0.0, 1.05)
    axes[2].grid(True, which="both", alpha=0.3)
    return axes
