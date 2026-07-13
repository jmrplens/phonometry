#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the emission domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_TERTIARY,
    _band_axis,
    _bar_width,
    _freq_axis,
    _hatch_invalid,
    _new_axes,
    _plot_band_level_bars,
    _sound_power_designation,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from ..emission.vibration_sound_power import VibrationSoundPowerResult
    from ..emission.intensity import IntensityResult
    from ..emission.sound_power import SoundPowerResult
    from ..emission.sound_power_intensity import SoundPowerIntensityResult
    from ..emission.sound_power_reverberation import ReverberationSoundPowerResult

def plot_sound_power(
    result: (
        "SoundPowerResult | ReverberationSoundPowerResult"
        " | SoundPowerIntensityResult | Any"
    ),
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes:
    """Sound power level spectrum with the A-weighted total annotated.

    Works for :class:`~phonometry.sound_power.SoundPowerResult`,
    :class:`~phonometry.sound_power_reverberation.ReverberationSoundPowerResult`
    and :class:`~phonometry.sound_power_intensity.SoundPowerIntensityResult`;
    for the intensity (scanning) variant the bands where the net power is
    non-positive (``negative_band``) are hatched and greyed as unusable.

    :param result: A sound-power result object exposing
        ``sound_power_level``, ``sound_power_level_a`` and (optionally)
        ``frequencies`` and ``negative_band``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the band :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    lw = np.asarray(result.sound_power_level, dtype=np.float64)
    n = lw.size
    freqs = getattr(result, "frequencies", None)
    if freqs is None:
        positions = _band_axis(
            ax, [f"Band {i + 1}" for i in range(n)], xlabel="Band"
        )
    else:
        positions = _band_axis(ax, np.asarray(freqs, dtype=np.float64))

    # ``negative_band`` (ISO 9614-2) and ``not_applicable_band`` (ISO 9614-3)
    # both flag bands whose net power is non-positive and therefore unusable.
    negative = getattr(result, "negative_band", None)
    if negative is None:
        negative = getattr(result, "not_applicable_band", None)
    neg = (
        np.asarray(negative, dtype=bool)
        if negative is not None
        else np.zeros(n, dtype=bool)
    )
    colors = [_C_MUTED if b else _C_PRIMARY for b in neg]
    kwargs.setdefault("color", colors)
    bars = ax.bar(positions, np.nan_to_num(lw), **kwargs)
    _hatch_invalid(bars, neg)

    ax.set_ylabel("Sound power level LW [dB]")
    designation = _sound_power_designation(result)
    lwa = float(result.sound_power_level_a)
    if np.isfinite(lwa):
        ax.set_title(f"{designation} sound power spectrum  (LWA = {lwa:.1f} dB(A))")
    else:
        ax.set_title(f"{designation} sound power spectrum")
    if np.any(neg):
        ax.plot([], [], color=_C_MUTED, marker="s", ls="", label="Non-positive band")
    if np.any(neg) or "label" in kwargs:
        ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax

def plot_intensity(
    result: IntensityResult, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Pressure vs intensity level per band with the pressure-intensity index.

    Draws Lp and LI per band and, on a twin axis, the per-band
    pressure-intensity index ``Lp - LI`` (the reactivity indicator); the
    total index is annotated in the title.

    :param result: An :class:`~phonometry.intensity.IntensityResult` with
        per-band data (obtained by requesting a band ``fraction``).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the pressure-level curve ``plot`` call.
    :return: The axes.
    :raises ValueError: If the result carries no per-band data.
    """
    if result.frequency is None:
        raise ValueError(
            "plot() needs per-band intensity data; call sound_intensity(...) "
            "with a 'fraction' to obtain it."
        )
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequency, dtype=np.float64)
    lp = np.asarray(result.pressure_level, dtype=np.float64)
    li = np.asarray(result.intensity_level, dtype=np.float64)
    index = np.asarray(result.pressure_intensity_index, dtype=np.float64)

    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Pressure level Lp")
    ax.plot(freqs, lp, "o-", **kwargs)
    ax.plot(freqs, li, "s--", color=_C_REFERENCE, label="Intensity level LI")
    _freq_axis(ax, freqs)
    ax.set_ylabel("Level [dB]")
    ax.grid(True, which="both", alpha=0.3)

    twin = ax.twinx()
    twin.bar(
        freqs,
        index,
        width=_bar_width(freqs),
        color=_C_TERTIARY,
        alpha=0.25,
        label="δpI = Lp - LI",
    )
    twin.set_ylabel("Pressure-intensity index δpI [dB]")

    lines, labels = ax.get_legend_handles_labels()
    tlines, tlabels = twin.get_legend_handles_labels()
    ax.legend(lines + tlines, labels + tlabels, loc="best", fontsize="small")
    ax.set_title(
        "ISO 9614 Lp vs LI  "
        f"(total δpI = {result.total_pressure_intensity_index:.1f} dB)"
    )
    return ax

def plot_vibration_sound_power(
    result: "VibrationSoundPowerResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Radiated sound power level per band (ISO/TS 7849).

    :param result: A :class:`~phonometry.vibration_sound_power.VibrationSoundPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the bar ``plot``.
    :return: The axes.
    """
    return _plot_band_level_bars(
        ax, result.sound_power_level, result.frequencies, result.total_level,
        ylabel=r"Sound power level $L_W$ [dB re 1 pW]",
        title="ISO/TS 7849 sound power from surface vibration", **kwargs,
    )
