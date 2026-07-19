#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the noise_control domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _new_axes,
    format_frequency_axis,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..noise_control.enclosures import EnclosureResult
    from ..noise_control.hvac import HvacSpectrumResult
    from ..noise_control.silencers import ReactiveSilencerResult

_FREQ_LABEL = "Frequency [Hz]"


def plot_reactive_silencer(
    result: "ReactiveSilencerResult", ax: "Axes | None" = None, **kwargs: Any
) -> "Axes":
    """Transmission (and insertion) loss of a reactive silencer over frequency.

    :param result: A
        :class:`~phonometry.noise_control.silencers.ReactiveSilencerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the transmission-loss ``Axes.plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequencies, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Transmission loss")
    ax.plot(f, np.asarray(result.transmission_loss), lw=1.8, **kwargs)
    if result.insertion_loss is not None:
        ax.plot(f, np.asarray(result.insertion_loss), color=_C_SECONDARY,
                lw=1.4, ls="--", label="Insertion loss")
    if result.resonances is not None:
        for i, fr in enumerate(np.atleast_1d(np.asarray(result.resonances))):
            if f.min() <= fr <= f.max():
                ax.axvline(fr, color=_C_TERTIARY, ls=":", lw=1.0,
                           label="Resonance" if i == 0 else None)
    ax.set_xlabel(_FREQ_LABEL)
    ax.set_ylabel("Loss [dB]")
    ax.set_title(f"Reactive silencer: {result.kind}")
    ax.grid(True, which="both", alpha=0.3)
    format_frequency_axis(ax)
    ax.legend(loc="best", fontsize="small")
    return ax


def plot_hvac_spectrum(
    result: "HvacSpectrumResult", ax: "Axes | None" = None, **kwargs: Any
) -> "Axes":
    """Per-frequency HVAC attenuation or regenerated sound power level.

    :param result: A :class:`~phonometry.noise_control.hvac.HvacSpectrumResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to ``Axes.plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequencies, dtype=np.float64)
    is_power = result.quantity == "sound_power_level"
    kwargs.setdefault("color", _C_SECONDARY if is_power else _C_PRIMARY)
    kwargs.setdefault("label", result.label)
    ax.plot(f, np.asarray(result.values), lw=1.8, marker="o", ms=3, **kwargs)
    ax.set_xlabel(_FREQ_LABEL)
    ax.set_ylabel(
        "Sound power level [dB re 1 pW]" if is_power else "Attenuation [dB]"
    )
    ax.set_title(result.label)
    ax.grid(True, which="both", alpha=0.3)
    format_frequency_axis(ax)
    ax.legend(loc="best", fontsize="small")
    return ax


def plot_enclosure(
    result: "EnclosureResult", ax: "Axes | None" = None, **kwargs: Any
) -> "Axes":
    """Panel R, interior correction C and net insertion loss of an enclosure.

    :param result: An
        :class:`~phonometry.noise_control.enclosures.EnclosureResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the insertion-loss ``Axes.plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    n = np.asarray(result.insertion_loss).size
    if result.frequencies is not None:
        x = np.asarray(result.frequencies, dtype=np.float64)
        continuous = True
    else:
        x = np.arange(n, dtype=np.float64)
        continuous = False
    ax.plot(x, np.asarray(result.panel_transmission_loss), color=_C_REFERENCE,
            lw=1.3, ls="--", marker="s", ms=3, label="Panel R")
    ax.plot(x, np.asarray(result.correction), color=_C_TERTIARY, lw=1.3,
            ls=":", marker="^", ms=3, label="Interior correction C")
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Insertion loss (R - C)")
    ax.plot(x, np.asarray(result.insertion_loss), lw=1.9, marker="o", ms=3,
            **kwargs)
    ax.set_ylabel("Level [dB]")
    ax.set_title("Machine enclosure insertion loss")
    ax.grid(True, which="both", alpha=0.3)
    if continuous:
        ax.set_xlabel(_FREQ_LABEL)
        format_frequency_axis(ax)
    else:
        ax.set_xlabel("Band")
        ax.set_xticks(x)
    ax.legend(loc="best", fontsize="small")
    return ax
