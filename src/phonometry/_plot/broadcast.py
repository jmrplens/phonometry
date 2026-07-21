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

#: Spanish translations of the fixed strings rendered by the broadcast
#: ``.plot()`` renderer, keyed by their verbatim English text. ``_t``
#: returns the English key unchanged for any language other than ``"es"``,
#: so the English output is byte-for-byte identical to the pre-i18n
#: renderer.
_STRINGS: dict[str, str] = {
    "Momentary (400 ms)": "Momentánea (400 ms)",
    "Short-term (3 s)": "Corto plazo (3 s)",
    "Time [s]": "Tiempo [s]",
    "Loudness [LUFS]": "Sonoridad [LUFS]",
    "Programme loudness (EBU R 128)": "Sonoridad de programa (EBU R 128)",
    "Integrated": "Integrada",
}


def _t(text: str, language: str = "en") -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    return _STRINGS.get(text, text) if language == "es" else text


def plot_program_loudness(
    result: "ProgramLoudnessResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes:
    """EBU Mode loudness over time (ITU-R BS.1770-5 / EBU R 128).

    Draws the momentary (400 ms) and short-term (3 s) loudness series, the
    integrated (programme) loudness as a horizontal line and the loudness
    range as a shaded band between its 10th and 95th percentile edges.

    :param result: A :class:`~phonometry.broadcast.ProgramLoudnessResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the short-term ``plot``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    if math.isfinite(result.lra_low) and math.isfinite(result.lra_high):
        lra = format_number(result.loudness_range, language, decimals=1)
        # Pale opaque tint of _C_SECONDARY (the 15 % composite over white):
        # the report pipeline renders through svglib, which drops alpha, so a
        # translucent fill would come out saturated and hide the curves.
        ax.axhspan(
            result.lra_low,
            result.lra_high,
            facecolor="#ffecdb",
            edgecolor="none",
            zorder=0,
            label=f"LRA {lra} LU",
        )
    if result.momentary.size:
        ax.plot(
            result.momentary_time,
            result.momentary,
            color=_C_MUTED,
            linewidth=1.0,
            label=_t("Momentary (400 ms)", language),
        )
    if result.short_term.size:
        kwargs.setdefault("color", _C_PRIMARY)
        kwargs.setdefault("linewidth", 2.0)
        kwargs.setdefault("label", _t("Short-term (3 s)", language))
        ax.plot(
            result.short_term_time,
            result.short_term,
            **kwargs,
        )
    if math.isfinite(result.integrated):
        integ = format_number(result.integrated, language, decimals=1)
        ax.axhline(
            result.integrated,
            color=_C_REFERENCE,
            linestyle="--",
            linewidth=1.6,
            label=f"{_t('Integrated', language)} {integ} LUFS",
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
    ax.set_xlabel(_t("Time [s]", language))
    ax.set_ylabel(_t("Loudness [LUFS]", language))
    ax.set_title(_t("Programme loudness (EBU R 128)", language))
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize=9)
    localize_axes(ax, language)
    return ax
