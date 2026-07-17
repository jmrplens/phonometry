#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the psychoacoustics domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import numpy as np

from .common import (
    _C_EDGE,
    _C_MUTED,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _new_axes,
    _new_axes_column,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from ..psychoacoustics.tone_audibility import ToneAudibilityResult
    from ..psychoacoustics.loudness_zwicker import ZwickerLoudness
    from ..psychoacoustics.loudness_ecma import EcmaLoudness
    from ..psychoacoustics.loudness_moore_glasberg import MooreGlasbergLoudness
    from ..psychoacoustics.loudness_moore_glasberg_time import MooreGlasbergTimeVaryingLoudness
    from ..psychoacoustics.tonality_ecma import EcmaTonality
    from ..psychoacoustics.roughness_ecma import EcmaRoughness
    from ..psychoacoustics.fluctuation_strength import FluctuationStrengthResult
    from ..psychoacoustics.fluctuation_strength_ecma import EcmaFluctuationStrength
    from ..psychoacoustics.psychoacoustic_annoyance import PsychoacousticAnnoyanceResult

def plot_zwicker_loudness(
    result: ZwickerLoudness, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Specific loudness N'(z) over the Bark scale (ISO 532-1).

    When the result carries the time-varying loudness trace
    (``time`` / ``loudness_vs_time``) *and* ``ax`` is ``None``, a second
    panel with loudness vs time is added and an array of two axes is
    returned; otherwise (a stationary result, or an ``ax`` was supplied) a
    single axes is returned.

    :param result: A :class:`~phonometry.loudness_zwicker.ZwickerLoudness`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the specific-loudness line ``plot`` call.
    :return: The axes, or an array of two axes for time-varying input.
    """
    specific = np.asarray(result.specific, dtype=np.float64)
    bark = np.arange(1, specific.size + 1) * 0.1
    time_varying = (
        result.time is not None and result.loudness_vs_time is not None and ax is None
    )

    if time_varying:
        axes = _new_axes_column(2, figsize=(7.0, 6.0))
        ax_specific = cast("Axes", axes[0])
    else:
        ax_specific = ax if ax is not None else _new_axes()

    kwargs.setdefault("color", _C_PRIMARY)
    ax_specific.plot(bark, specific, **kwargs)
    ax_specific.fill_between(bark, specific, color=kwargs["color"], alpha=0.25)
    ax_specific.set_xlabel("Critical-band rate z [Bark]")
    ax_specific.set_ylabel("Specific loudness N' [sone/Bark]")
    ax_specific.set_xlim(0.0, bark[-1])
    ax_specific.set_ylim(bottom=0.0)
    ax_specific.set_title(
        f"ISO 532-1 loudness N = {result.loudness:.2f} sone "
        f"({result.loudness_level:.1f} phon)"
    )
    ax_specific.grid(True, alpha=0.3)

    if not time_varying:
        return ax_specific

    ax_time = cast("Axes", axes[1])
    time = np.asarray(result.time, dtype=np.float64)
    lvt = np.asarray(result.loudness_vs_time, dtype=np.float64)
    ax_time.plot(time, lvt, color=_C_TERTIARY, label="N(t)")
    if result.n5 is not None:
        ax_time.axhline(
            result.n5, color=_C_REFERENCE, ls="--", lw=1, label=f"N5={result.n5:.2f}"
        )
    if result.n10 is not None:
        ax_time.axhline(
            result.n10, color=_C_SECONDARY, ls=":", lw=1, label=f"N10={result.n10:.2f}"
        )
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Loudness N [sone]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.grid(True, alpha=0.3)
    ax_time.legend(loc="best", fontsize="small")
    return axes

def plot_ecma_loudness(
    result: EcmaLoudness, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Average specific loudness N'(z) and time-dependent loudness N(l).

    When ``ax`` is ``None`` a two-panel figure is drawn (specific loudness
    over the critical-band-rate scale and loudness vs time) and an array of
    two axes is returned; when ``ax`` is supplied only the specific-loudness
    panel is drawn on it and that single axes is returned.

    :param result: An :class:`~phonometry.loudness_ecma.EcmaLoudness`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the specific-loudness line ``plot`` call.
    :return: The axes, or an array of two axes.
    """
    specific = np.asarray(result.specific_loudness, dtype=np.float64)
    bark = np.asarray(result.bark, dtype=np.float64)
    two_panel = ax is None

    if two_panel:
        axes = _new_axes_column(2, figsize=(7.0, 6.0))
        ax_specific = cast("Axes", axes[0])
    else:
        ax_specific = cast("Axes", ax)

    kwargs.setdefault("color", _C_PRIMARY)
    ax_specific.plot(bark, specific, **kwargs)
    ax_specific.fill_between(bark, specific, color=kwargs["color"], alpha=0.25)
    ax_specific.set_xlabel("Critical-band rate z [Bark_HMS]")
    ax_specific.set_ylabel("Specific loudness N' [sone_HMS/Bark_HMS]")
    ax_specific.set_xlim(0.0, bark[-1])
    ax_specific.set_ylim(bottom=0.0)
    ax_specific.set_title(f"ECMA-418-2 loudness N = {result.loudness:.2f} sone_HMS")
    ax_specific.grid(True, alpha=0.3)

    if not two_panel:
        return ax_specific

    ax_time = cast("Axes", axes[1])
    time = np.asarray(result.time, dtype=np.float64)
    lvt = np.asarray(result.loudness_vs_time, dtype=np.float64)
    ax_time.plot(time, lvt, color=_C_TERTIARY, label="N(l)")
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Loudness N [sone_HMS]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.grid(True, alpha=0.3)
    ax_time.legend(loc="best", fontsize="small")
    return axes

def plot_moore_glasberg_loudness(
    result: MooreGlasbergLoudness, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Specific loudness N'(i) over the ERB-number (Cam) scale (ISO 532-2).

    :param result: A
        :class:`~phonometry.loudness_moore_glasberg.MooreGlasbergLoudness`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the specific-loudness line ``plot`` call.
    :return: The axes.
    """
    specific = np.asarray(result.specific, dtype=np.float64)
    erb_number = np.asarray(result.erb_number, dtype=np.float64)
    ax = ax if ax is not None else _new_axes()

    kwargs.setdefault("color", _C_PRIMARY)
    ax.plot(erb_number, specific, **kwargs)
    ax.fill_between(erb_number, specific, color=kwargs["color"], alpha=0.25)
    ax.set_xlabel("ERB number [Cam]")
    ax.set_ylabel("Specific loudness N' [sone/Cam]")
    ax.set_xlim(erb_number[0], erb_number[-1])
    ax.set_ylim(bottom=0.0)
    ax.set_title(
        f"ISO 532-2 loudness N = {result.loudness:.2f} sone "
        f"({result.loudness_level:.1f} phon)"
    )
    ax.grid(True, alpha=0.3)
    return ax

def plot_moore_glasberg_time_loudness(
    result: MooreGlasbergTimeVaryingLoudness, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Short-term and long-term loudness against time (ISO 532-3).

    :param result: A
        :class:`~phonometry.loudness_moore_glasberg_time.MooreGlasbergTimeVaryingLoudness`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the long-term-loudness line ``plot`` call.
    :return: The axes.
    """
    time = np.asarray(result.time, dtype=np.float64)
    stl = np.asarray(result.short_term_loudness, dtype=np.float64)
    ltl = np.asarray(result.long_term_loudness, dtype=np.float64)
    ax = ax if ax is not None else _new_axes()

    ax.plot(time, stl, color=_C_PRIMARY_LIGHT, lw=1.0, label="Short-term loudness")
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("lw", 1.8)
    ax.plot(time, ltl, label="Long-term loudness", **kwargs)
    ax.axhline(result.n_max, color=_C_REFERENCE, ls="--", lw=1.0, alpha=0.7)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Loudness [sone]")
    if time.size:
        ax.set_xlim(time[0], time[-1])
    ax.set_ylim(bottom=0.0)
    ax.set_title(
        f"ISO 532-3 peak long-term loudness N = {result.n_max:.2f} sone "
        f"({result.loudness_level_max:.1f} phon)"
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax

def plot_ecma_tonality(
    result: EcmaTonality, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Average specific tonality T'(z) and time-dependent tonality T(l).

    When ``ax`` is ``None`` a two-panel figure is drawn (specific tonality over
    the critical-band-rate scale and tonality vs time) and an array of two axes
    is returned; when ``ax`` is supplied only the specific-tonality panel is
    drawn on it and that single axes is returned.

    :param result: An :class:`~phonometry.tonality_ecma.EcmaTonality`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the specific-tonality line ``plot`` call.
    :return: The axes, or an array of two axes.
    """
    specific = np.asarray(result.specific_tonality, dtype=np.float64)
    bark = np.asarray(result.bark, dtype=np.float64)
    two_panel = ax is None

    if two_panel:
        axes = _new_axes_column(2, figsize=(7.0, 6.0))
        ax_specific = cast("Axes", axes[0])
    else:
        ax_specific = cast("Axes", ax)

    # Tonality's per-metric identity color is red across the documentation
    # figures (roughness is brown); kept literal on purpose, see the module
    # color-constant note.
    kwargs.setdefault("color", "#d62728")
    ax_specific.plot(bark, specific, **kwargs)
    ax_specific.fill_between(bark, specific, color=kwargs["color"], alpha=0.25)
    ax_specific.set_xlabel("Critical-band rate z [Bark_HMS]")
    ax_specific.set_ylabel("Specific tonality T' [tu_HMS]")
    ax_specific.set_xlim(0.0, bark[-1])
    ax_specific.set_ylim(bottom=0.0)
    ax_specific.set_title(f"ECMA-418-2 tonality T = {result.tonality:.2f} tu_HMS")
    ax_specific.grid(True, alpha=0.3)

    if not two_panel:
        return ax_specific

    ax_time = cast("Axes", axes[1])
    time = np.asarray(result.time, dtype=np.float64)
    tvt = np.asarray(result.tonality_vs_time, dtype=np.float64)
    ax_time.plot(time, tvt, color=_C_QUATERNARY, label="T(l)")
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Tonality T [tu_HMS]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.grid(True, alpha=0.3)
    ax_time.legend(loc="best", fontsize="small")
    return axes

def _plot_hms_time_and_heatmap(
    time: np.ndarray,
    vs_time: np.ndarray,
    spec_vs_time: np.ndarray,
    bark: np.ndarray,
    ax: Axes | None,
    color: str,
    ylabel: str,
    title: str,
    heat_label: str,
    kwargs: dict[str, Any],
) -> Axes | np.ndarray:
    """Shared renderer for the HMS time-trace + specific-value heatmaps.

    Used by the ECMA-418-2 roughness and fluctuation-strength results: when
    ``ax`` is ``None`` a two-panel figure (time trace + heatmap over the
    critical-band-rate scale) is drawn and an array of two axes is returned;
    otherwise only the time trace is drawn on ``ax`` and it is returned.
    """
    two_panel = ax is None
    if two_panel:
        axes = _new_axes_column(2, figsize=(7.0, 6.0))
        ax_time = cast("Axes", axes[0])
    else:
        ax_time = cast("Axes", ax)

    if "c" not in kwargs:  # matplotlib alias; injecting "color" too would raise
        kwargs.setdefault("color", color)
    (line,) = ax_time.plot(time, vs_time, **kwargs)
    ax_time.fill_between(time, vs_time, color=line.get_color(), alpha=0.25)
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel(ylabel)
    ax_time.set_ylim(bottom=0.0)
    ax_time.set_title(title)
    ax_time.grid(True, alpha=0.3)

    if not two_panel:
        return ax_time

    ax_heat = cast("Axes", axes[1])
    if time.size >= 2 and spec_vs_time.size:
        mesh = ax_heat.pcolormesh(
            time, bark, spec_vs_time.T, cmap="magma", shading="auto"
        )
        ax_heat.figure.colorbar(mesh, ax=ax_heat, label=heat_label)
    ax_heat.set_xlabel("Time [s]")
    ax_heat.set_ylabel("Critical-band rate z [Bark_HMS]")
    return axes

def plot_ecma_roughness(
    result: EcmaRoughness, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Time-dependent roughness R(l50) and a specific-roughness heatmap.

    When ``ax`` is ``None`` a two-panel figure is drawn (roughness vs time and
    a specific-roughness R'(l50, z) heatmap over the critical-band-rate scale)
    and an array of two axes is returned; when ``ax`` is supplied only the
    time-dependent roughness is drawn on it and that single axes is returned.

    :param result: An :class:`~phonometry.roughness_ecma.EcmaRoughness`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the roughness-vs-time line ``plot`` call.
    :return: The axes, or an array of two axes.
    """
    # Roughness's per-metric identity color is brown across the documentation
    # figures (tonality is red); kept literal on purpose, see the module
    # color-constant note.
    return _plot_hms_time_and_heatmap(
        np.asarray(result.time, dtype=np.float64),
        np.asarray(result.roughness_vs_time, dtype=np.float64),
        np.asarray(result.specific_roughness_vs_time, dtype=np.float64),
        np.asarray(result.bark, dtype=np.float64),
        ax,
        "#8c564b",
        "Roughness R [asper]",
        f"ECMA-418-2 roughness R = {result.roughness:.2f} asper",
        "R' [asper/Bark_HMS]",
        kwargs,
    )

def plot_ecma_fluctuation_strength(
    result: EcmaFluctuationStrength, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Time-dependent fluctuation strength F(l50) and a specific heatmap.

    When ``ax`` is ``None`` a two-panel figure is drawn (fluctuation strength
    vs time and a specific-fluctuation-strength F'(l50, z) heatmap over the
    critical-band-rate scale) and an array of two axes is returned; when
    ``ax`` is supplied only the time-dependent fluctuation strength is drawn
    on it and that single axes is returned.

    :param result: An :class:`~phonometry.fluctuation_strength_ecma.
        EcmaFluctuationStrength`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the time-trace line ``plot`` call.
    :return: The axes, or an array of two axes.
    """
    # Fluctuation strength's per-metric identity color is teal across the
    # documentation figures (roughness is brown, tonality red); kept literal
    # on purpose, see the module color-constant note.
    return _plot_hms_time_and_heatmap(
        np.asarray(result.time, dtype=np.float64),
        np.asarray(result.fluctuation_strength_vs_time, dtype=np.float64),
        np.asarray(
            result.specific_fluctuation_strength_vs_time, dtype=np.float64
        ),
        np.asarray(result.bark, dtype=np.float64),
        ax,
        "#17becf",
        "Fluctuation strength F [vacil_HMS]",
        (
            "ECMA-418-2 fluctuation strength "
            f"F = {result.fluctuation_strength:.2f} vacil_HMS"
        ),
        "F' [vacil_HMS/Bark_HMS]",
        kwargs,
    )

def plot_fluctuation_strength(
    result: "FluctuationStrengthResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Specific fluctuation strength ``f(z)`` against critical-band rate.

    Draws the per-filter specific fluctuation strength over the Bark scale,
    annotated with the overall ``F`` in vacil.

    :param result: A
        :class:`~phonometry.fluctuation_strength.FluctuationStrengthResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    z = np.asarray(result.bark_axis, dtype=np.float64)
    spec = np.asarray(result.specific, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.plot(z, spec, **kwargs)
    ax.fill_between(z, spec, color=kwargs["color"], alpha=0.25)
    ax.set_xlabel("Critical-band rate z [Bark]")
    ax.set_ylabel(r"Specific fluctuation strength $f'(z)$ [vacil/Bark]")
    ax.set_title(f"Fluctuation strength F = {result.fluctuation_strength:.2f} vacil")
    ax.set_ylim(bottom=0.0)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    return ax

def plot_psychoacoustic_annoyance(
    result: "PsychoacousticAnnoyanceResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Psychoacoustic annoyance with its ``wS`` and ``wFR`` term contributions.

    Draws the PA value alongside the two loudness-weighted terms so the
    sharpness and fluctuation/roughness contributions are visible.

    :param result: A :class:`~phonometry.psychoacoustic_annoyance.
        PsychoacousticAnnoyanceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the bar ``bar`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    labels = ["PA", r"$w_S$", r"$w_{FR}$"]
    values = [result.annoyance, result.w_s, result.w_fr]
    colors = [_C_REFERENCE, _C_PRIMARY, _C_PRIMARY]
    positions = np.arange(len(labels))
    kwargs.setdefault("width", 0.6)
    kwargs.setdefault("color", colors)
    kwargs.setdefault("edgecolor", _C_EDGE)
    ax.bar(positions, values, **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Value")
    ax.set_title(
        f"Psychoacoustic annoyance PA = {result.annoyance:.1f} "
        f"(N5 = {result.n5:.1f} sone)"
    )
    ax.grid(True, axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    return ax

def plot_tone_audibility(
    result: "ToneAudibilityResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-tone audibility ``ΔL`` against tone frequency (ISO/PAS 20065).

    Draws one bar per tone with the decisive (most audible) tone emphasised and
    the ``ΔL = 0`` audibility threshold marked; tones above it are present.

    :param result: A :class:`~phonometry.tone_audibility.ToneAudibilityResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the bar ``bar`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.tone_frequencies, dtype=np.float64)
    delta = np.asarray(result.audibilities, dtype=np.float64)
    positions = np.arange(freqs.size)
    decisive = int(np.argmax(delta))
    colors = [_C_PRIMARY] * freqs.size
    colors[decisive] = _C_REFERENCE

    kwargs.setdefault("width", 0.7)
    bars = ax.bar(positions, delta, color=colors, edgecolor=_C_EDGE, **kwargs)
    bars[decisive].set_label(
        rf"decisive $\Delta L$ = {result.decisive_audibility:.1f} dB "
        rf"@ {result.decisive_frequency:g} Hz"
    )
    ax.axhline(0.0, color=_C_MUTED, ls="--", lw=1.0, label=r"threshold $\Delta L=0$ dB")
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.set_xlabel("Tone frequency [Hz]")
    ax.set_ylabel(r"Audibility $\Delta L$ [dB]")
    ax.set_title("ISO/PAS 20065 tonal audibility")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    return ax
