#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the broadcast domain (lazy imports from result .plot())."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _LEGEND_UPPER_RIGHT,
    _new_axes,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..broadcast.program_loudness import ProgramLoudnessResult


def plot_program_loudness(
    result: "ProgramLoudnessResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """EBU Mode loudness over time (ITU-R BS.1770-5 / EBU R 128).

    Draws the momentary (400 ms) and short-term (3 s) loudness series, the
    integrated (programme) loudness as a horizontal line and the loudness
    range as a shaded band between its 10th and 95th percentile edges.

    :param result: A :class:`~phonometry.broadcast.ProgramLoudnessResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the short-term ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    if math.isfinite(result.lra_low) and math.isfinite(result.lra_high):
        ax.axhspan(
            result.lra_low,
            result.lra_high,
            color=_C_SECONDARY,
            alpha=0.15,
            label=f"LRA {result.loudness_range:.1f} LU",
        )
    if result.momentary.size:
        ax.plot(
            result.momentary_time,
            result.momentary,
            color=_C_MUTED,
            linewidth=1.0,
            label="Momentary (400 ms)",
        )
    if result.short_term.size:
        kwargs.setdefault("color", _C_PRIMARY)
        kwargs.setdefault("linewidth", 2.0)
        kwargs.setdefault("label", "Short-term (3 s)")
        ax.plot(
            result.short_term_time,
            result.short_term,
            **kwargs,
        )
    if math.isfinite(result.integrated):
        ax.axhline(
            result.integrated,
            color=_C_REFERENCE,
            linestyle="--",
            linewidth=1.6,
            label=f"Integrated {result.integrated:.1f} LUFS",
        )
    finite = np.concatenate(
        [
            result.momentary[np.isfinite(result.momentary)],
            result.short_term[np.isfinite(result.short_term)],
        ]
    )
    if finite.size:
        low = float(np.min(finite))
        high = float(np.max(finite))
        ax.set_ylim(low - 5.0, high + 5.0)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Loudness [LUFS]")
    ax.set_title("Programme loudness (EBU R 128)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize=9)
    return ax
