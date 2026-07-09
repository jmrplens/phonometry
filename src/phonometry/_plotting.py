#  Copyright (c) 2026. Jose M. Requena-Plens

"""One-line canonical figures for the library's result objects.

Every public result dataclass exposes a thin ``plot(ax=None, **kwargs)``
method that delegates to a rendering function in this module, reproducing
the essence of its documentation figure in a single call::

    res = room_parameters(ir, fs)
    res.plot()

matplotlib is a *soft* dependency: importing :mod:`phonometry` and running
any computation works without it, and only calling ``.plot()`` (or the
functions here) requires it.  The import is therefore performed lazily and
raises a clear :class:`ImportError` with installation guidance when the
package is missing, mirroring :func:`phonometry.filter_design._showfilter`.

The functions are pure renderers: they never call ``plt.show``; when ``ax``
is ``None`` they create a fresh figure and axes, and they always *return*
the :class:`~matplotlib.axes.Axes` (or an array of axes for multi-panel
figures) so the plot can be composed into a larger layout.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from .intensity import IntensityResult
    from .loudness import ZwickerLoudness
    from .loudness_ecma import EcmaLoudness
    from .loudness_moore_glasberg import MooreGlasbergLoudness
    from .loudness_moore_glasberg_time import MooreGlasbergTimeVaryingLoudness
    from .room_acoustics import DecayCurve, RoomAcousticsResult
    from .room_ir import ImpulseResponseResult
    from .tonality_ecma import EcmaTonality
    from .roughness_ecma import EcmaRoughness
    from .sii import SIIResult
    from .sti import STIResult

_INSTALL_HINT = (
    "Plotting requires matplotlib. Install it with: pip install phonometry[plot]"
)

#: Nominal octave-band centres used by the STI computation (125 Hz - 8 kHz).
_STI_BAND_CENTERS = (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0)


def _import_pyplot() -> Any:
    """Import :mod:`matplotlib.pyplot` lazily with an actionable error."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        raise ImportError(_INSTALL_HINT) from exc
    return plt


def _new_axes() -> Axes:
    """Create a single fresh figure + axes and return the axes."""
    plt = _import_pyplot()
    _fig, ax = plt.subplots()
    return cast("Axes", ax)


def _new_axes_column(n: int, **kwargs: Any) -> np.ndarray:
    """Create a stacked column of ``n`` axes and return them as an array."""
    plt = _import_pyplot()
    _fig, axes = plt.subplots(n, 1, **kwargs)
    result: np.ndarray = np.atleast_1d(axes)
    return result


def _freq_axis(ax: Axes, freqs: np.ndarray) -> None:
    """Configure a logarithmic frequency x-axis labelled with band centres."""
    ax.set_xscale("log")
    ax.set_xticks(list(freqs))
    ax.set_xticklabels([_format_freq(f) for f in freqs], rotation=45, ha="right")
    ax.set_xlabel("Frequency [Hz]")


def _format_freq(f: float) -> str:
    """Short human label for a band centre frequency."""
    if f >= 1000.0:
        text = f"{f / 1000.0:g}k"
    else:
        text = f"{f:g}"
    return text


# ---------------------------------------------------------------------------
# Zwicker loudness (ISO 532-1)
# ---------------------------------------------------------------------------


def plot_zwicker_loudness(
    result: ZwickerLoudness, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Specific loudness N'(z) over the Bark scale (ISO 532-1).

    When the result carries the time-varying loudness trace
    (``time`` / ``loudness_vs_time``) *and* ``ax`` is ``None``, a second
    panel with loudness vs time is added and an array of two axes is
    returned; otherwise (a stationary result, or an ``ax`` was supplied) a
    single axes is returned.

    :param result: A :class:`~phonometry.loudness.ZwickerLoudness`.
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

    kwargs.setdefault("color", "#1f77b4")
    ax_specific.plot(bark, specific, **kwargs)
    ax_specific.fill_between(bark, specific, color="#1f77b4", alpha=0.25)
    ax_specific.set_xlabel("Critical-band rate z [Bark]")
    ax_specific.set_ylabel("Specific loudness N' [sone/Bark]")
    ax_specific.set_xlim(0.0, bark[-1])
    ax_specific.set_ylim(bottom=0.0)
    ax_specific.set_title(
        f"Loudness N = {result.loudness:.2f} sone ({result.loudness_level:.1f} phon)"
    )
    ax_specific.grid(True, alpha=0.3)

    if not time_varying:
        return ax_specific

    ax_time = cast("Axes", axes[1])
    time = np.asarray(result.time, dtype=np.float64)
    lvt = np.asarray(result.loudness_vs_time, dtype=np.float64)
    ax_time.plot(time, lvt, color="#2ca02c", label="N(t)")
    if result.n5 is not None:
        ax_time.axhline(
            result.n5, color="#d62728", ls="--", lw=1, label=f"N5={result.n5:.2f}"
        )
    if result.n10 is not None:
        ax_time.axhline(
            result.n10, color="#ff7f0e", ls=":", lw=1, label=f"N10={result.n10:.2f}"
        )
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Loudness N [sone]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.grid(True, alpha=0.3)
    ax_time.legend(loc="best", fontsize="small")
    return axes


# ---------------------------------------------------------------------------
# ECMA-418-2 Sottek loudness
# ---------------------------------------------------------------------------


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

    kwargs.setdefault("color", "#1f77b4")
    ax_specific.plot(bark, specific, **kwargs)
    ax_specific.fill_between(bark, specific, color="#1f77b4", alpha=0.25)
    ax_specific.set_xlabel("Critical-band rate z [Bark_HMS]")
    ax_specific.set_ylabel("Specific loudness N' [sone_HMS/Bark_HMS]")
    ax_specific.set_xlim(0.0, bark[-1])
    ax_specific.set_ylim(bottom=0.0)
    ax_specific.set_title(f"Loudness N = {result.loudness:.2f} sone_HMS")
    ax_specific.grid(True, alpha=0.3)

    if not two_panel:
        return ax_specific

    ax_time = cast("Axes", axes[1])
    time = np.asarray(result.time, dtype=np.float64)
    lvt = np.asarray(result.loudness_vs_time, dtype=np.float64)
    ax_time.plot(time, lvt, color="#2ca02c", label="N(l)")
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Loudness N [sone_HMS]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.grid(True, alpha=0.3)
    ax_time.legend(loc="best", fontsize="small")
    return axes


# ---------------------------------------------------------------------------
# ISO 532-2 Moore-Glasberg loudness
# ---------------------------------------------------------------------------


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

    kwargs.setdefault("color", "#1f77b4")
    ax.plot(erb_number, specific, **kwargs)
    ax.fill_between(erb_number, specific, color="#1f77b4", alpha=0.25)
    ax.set_xlabel("ERB number [Cam]")
    ax.set_ylabel("Specific loudness N' [sone/Cam]")
    ax.set_xlim(erb_number[0], erb_number[-1])
    ax.set_ylim(bottom=0.0)
    ax.set_title(
        f"Loudness N = {result.loudness:.2f} sone ({result.loudness_level:.1f} phon)"
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

    ax.plot(time, stl, color="#aec7e8", lw=1.0, label="Short-term loudness")
    kwargs.setdefault("color", "#1f77b4")
    kwargs.setdefault("lw", 1.8)
    ax.plot(time, ltl, label="Long-term loudness", **kwargs)
    ax.axhline(result.n_max, color="#d62728", ls="--", lw=1.0, alpha=0.7)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Loudness [sone]")
    if time.size:
        ax.set_xlim(time[0], time[-1])
    ax.set_ylim(bottom=0.0)
    ax.set_title(
        f"Peak long-term loudness N = {result.n_max:.2f} sone "
        f"({result.loudness_level_max:.1f} phon)"
    )
    ax.legend(loc="best")
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

    kwargs.setdefault("color", "#d62728")
    ax_specific.plot(bark, specific, **kwargs)
    ax_specific.fill_between(bark, specific, color="#d62728", alpha=0.25)
    ax_specific.set_xlabel("Critical-band rate z [Bark_HMS]")
    ax_specific.set_ylabel("Specific tonality T' [tu_HMS]")
    ax_specific.set_xlim(0.0, bark[-1])
    ax_specific.set_ylim(bottom=0.0)
    ax_specific.set_title(f"Tonality T = {result.tonality:.2f} tu_HMS")
    ax_specific.grid(True, alpha=0.3)

    if not two_panel:
        return ax_specific

    ax_time = cast("Axes", axes[1])
    time = np.asarray(result.time, dtype=np.float64)
    tvt = np.asarray(result.tonality_vs_time, dtype=np.float64)
    ax_time.plot(time, tvt, color="#9467bd", label="T(l)")
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Tonality T [tu_HMS]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.grid(True, alpha=0.3)
    ax_time.legend(loc="best", fontsize="small")
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
    time = np.asarray(result.time, dtype=np.float64)
    rvt = np.asarray(result.roughness_vs_time, dtype=np.float64)
    two_panel = ax is None

    if two_panel:
        axes = _new_axes_column(2, figsize=(7.0, 6.0))
        ax_time = cast("Axes", axes[0])
    else:
        ax_time = cast("Axes", ax)

    kwargs.setdefault("color", "#8c564b")
    ax_time.plot(time, rvt, **kwargs)
    ax_time.fill_between(time, rvt, color="#8c564b", alpha=0.25)
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Roughness R [asper]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.set_title(f"Roughness R = {result.roughness:.2f} asper")
    ax_time.grid(True, alpha=0.3)

    if not two_panel:
        return ax_time

    ax_heat = cast("Axes", axes[1])
    bark = np.asarray(result.bark, dtype=np.float64)
    spec = np.asarray(result.specific_roughness_vs_time, dtype=np.float64)
    if time.size >= 2 and spec.size:
        mesh = ax_heat.pcolormesh(time, bark, spec.T, cmap="magma", shading="auto")
        ax_heat.figure.colorbar(mesh, ax=ax_heat, label="R' [asper/Bark_HMS]")
    ax_heat.set_xlabel("Time [s]")
    ax_heat.set_ylabel("Critical-band rate z [Bark_HMS]")
    return axes


# ---------------------------------------------------------------------------
# Speech transmission index (IEC 60268-16)
# ---------------------------------------------------------------------------


def plot_sti(result: STIResult, ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Per-band modulation transfer index bars with the STI and rating.

    :param result: A :class:`~phonometry.sti.STIResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    mti = np.asarray(result.mti, dtype=np.float64)
    positions = np.arange(mti.size)
    kwargs.setdefault("color", "#1f77b4")
    ax.bar(positions, mti, **kwargs)
    ax.set_xticks(positions)
    if mti.size == len(_STI_BAND_CENTERS):
        ax.set_xticklabels([_format_freq(f) for f in _STI_BAND_CENTERS])
        ax.set_xlabel("Octave band [Hz]")
    else:
        ax.set_xlabel("Octave band")
    ax.set_ylabel("Modulation transfer index MTI")
    ax.set_ylim(0.0, 1.0)
    ax.set_title(f"STI = {result.sti:.2f}  (rating {result.rating})")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


def plot_sii(result: "SIIResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Per-band audibility and its importance-weighted contribution to the SII.

    :param result: A :class:`~phonometry.sii.SIIResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the weighted-contribution :meth:`bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    audibility = np.asarray(result.band_audibility, dtype=np.float64)
    contribution = audibility * np.asarray(result.band_importance, dtype=np.float64)
    positions = np.arange(freqs.size)
    ax.bar(positions, audibility, color="#c6dbef", label="Band audibility $A_i$")
    kwargs.setdefault("color", "#1f77b4")
    ax.bar(positions, contribution / contribution.max(), width=0.5,
           label=r"Importance-weighted $I_i A_i$ (scaled)", **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels([_format_freq(f) for f in freqs], rotation=45, ha="right")
    ax.set_xlabel("One-third-octave band [Hz]")
    ax.set_ylabel("Band audibility")
    ax.set_ylim(0.0, 1.0)
    ax.set_title(f"SII = {result.sii:.3f}")
    ax.legend(loc="upper right", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Weighted single-number ratings (ISO 717-1 / ISO 717-2)
# ---------------------------------------------------------------------------


def _plot_rating(
    band_centers: np.ndarray,
    measured: np.ndarray,
    reference: np.ndarray,
    *,
    impact: bool,
    rating: int,
    unfavourable_sum: float,
    title: str,
    ylabel: str,
    ax: Axes | None,
    **kwargs: Any,
) -> Axes:
    """Shared renderer for airborne and impact rating figures.

    Draws the measured curve against the shifted reference and shades the
    unfavourable deviations: where the reference exceeds the measurement
    for airborne insulation (higher is better) and where the measurement
    exceeds the reference for impact sound (lower is better).  Extra
    keyword arguments style the measured curve (its primary artist).
    """
    ax = ax if ax is not None else _new_axes()
    kwargs.setdefault("color", "#1f77b4")
    kwargs.setdefault("label", "Measured")
    ax.plot(band_centers, measured, "o-", **kwargs)
    ax.plot(band_centers, reference, "s--", color="#d62728", label="Shifted reference")
    unfavourable = _unfavourable_mask(measured, reference, impact)
    ax.fill_between(
        band_centers,
        measured,
        reference,
        where=unfavourable.tolist(),
        color="#ff7f0e",
        alpha=0.4,
        label="Unfavourable deviations",
        interpolate=True,
    )
    _freq_axis(ax, band_centers)
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title} = {rating} dB  (Sigma unfav. = {unfavourable_sum:.1f} dB)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    return ax


def _unfavourable_mask(
    measured: np.ndarray, reference: np.ndarray, impact: bool
) -> np.ndarray:
    """Bands whose deviation is unfavourable.

    Airborne (ISO 717-1, higher is better): the reference exceeds the
    measurement.  Impact (ISO 717-2, lower is better): the measurement
    exceeds the reference (the opposite sign).
    """
    if impact:
        return np.asarray(measured > reference)
    return np.asarray(measured < reference)


def plot_weighted_rating(result: Any, ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Airborne rating curve vs shifted reference (ISO 717-1)."""
    _require_rating_curve(result)
    return _plot_rating(
        np.asarray(result.band_centers, dtype=np.float64),
        np.asarray(result.measured, dtype=np.float64),
        np.asarray(result.shifted_reference, dtype=np.float64),
        impact=False,
        rating=result.rating,
        unfavourable_sum=result.unfavourable_sum,
        title=f"Rw (C={result.c:+d}; Ctr={result.ctr:+d})",
        ylabel="Sound reduction index [dB]",
        ax=ax,
        **kwargs,
    )


def plot_impact_rating(result: Any, ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Impact rating curve vs shifted reference (ISO 717-2).

    The drawn shifted-reference curve is the normatively honest ``ref -
    shift``; for octave-band data the rating is that curve read at 500 Hz
    *minus 5 dB* (Clause 4.3.2), so the plot marks the 500 Hz read value on
    the (undistorted) curve and annotates the -5 dB reduction rather than
    pulling the curve down to the rating.
    """
    _require_rating_curve(result)
    band_centers = np.asarray(result.band_centers, dtype=np.float64)
    reference = np.asarray(result.shifted_reference, dtype=np.float64)
    ax = _plot_rating(
        band_centers,
        np.asarray(result.measured, dtype=np.float64),
        reference,
        impact=True,
        rating=result.rating,
        unfavourable_sum=result.unfavourable_sum,
        # The rated quantity depends on the input (Ln,w, L'n,w or L'nT,w);
        # the dataclass does not carry which, so the figure uses the neutral
        # "Impact rating" label rather than hard-coding one specific symbol.
        title=f"Impact rating (CI={result.ci:+d})",
        ylabel="Impact sound pressure level [dB]",
        ax=ax,
        **kwargs,
    )
    _annotate_impact_500(ax, band_centers, reference, int(result.rating))
    return ax


def plot_weighted_absorption(result: Any, ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Practical absorption curve vs the shifted reference (ISO 11654:1997).

    Draws the practical coefficients ``alpha_p`` against the shifted reference
    curve and shades the unfavourable deviations (measured below the shifted
    reference, Clause 4.2), reusing :func:`_unfavourable_mask` and the shared
    frequency axis. Extra keyword arguments style the measured curve.
    """
    ax = ax if ax is not None else _new_axes()
    band_centers = np.asarray(result.band_centers, dtype=np.float64)
    measured = np.asarray(result.measured, dtype=np.float64)
    reference = np.asarray(result.shifted_reference, dtype=np.float64)
    kwargs.setdefault("color", "#1f77b4")
    kwargs.setdefault("label", "Practical alpha_p")
    ax.plot(band_centers, measured, "o-", **kwargs)
    ax.plot(band_centers, reference, "s--", color="#d62728", label="Shifted reference")
    unfavourable = _unfavourable_mask(measured, reference, impact=False)
    ax.fill_between(
        band_centers,
        measured,
        reference,
        where=unfavourable.tolist(),
        color="#ff7f0e",
        alpha=0.4,
        label="Unfavourable deviations",
        interpolate=True,
    )
    _freq_axis(ax, band_centers)
    ax.set_ylabel("Sound absorption coefficient")
    ax.set_ylim(0.0, 1.05)
    ax.set_title(
        f"alpha_w = {result.rating_label}  (class {result.absorption_class}, "
        f"Sigma unfav. = {result.unfavourable_sum:.2f})"
    )
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    return ax


def _annotate_impact_500(
    ax: Axes, band_centers: np.ndarray, reference: np.ndarray, rating: int
) -> None:
    """Mark the 500 Hz read value on the reference curve and, when the
    octave-band -5 dB reduction applies (ISO 717-2 Clause 4.3.2), annotate
    the rating as ``read - 5 dB`` so the figure stays normatively truthful.
    """
    if band_centers.size == 0:
        return
    idx = int(np.argmin(np.abs(band_centers - 500.0)))
    read_value = float(reference[idx])
    ax.plot(
        [band_centers[idx]],
        [read_value],
        marker="D",
        ls="",
        color="#d62728",
        ms=9,
        mfc="none",
        mew=1.6,
        zorder=5,
        label=f"500 Hz read = {read_value:.0f} dB",
    )
    offset = rating - read_value
    if abs(offset) >= 0.5:  # octave-band -5 dB rule (Clause 4.3.2)
        ax.annotate(
            f"rating = {rating} dB = {read_value:.0f} - 5 dB (octave rule)",
            xy=(band_centers[idx], read_value),
            xytext=(0.0, -32.0),
            textcoords="offset points",
            ha="center",
            fontsize="small",
            arrowprops={"arrowstyle": "->", "color": "#555555"},
        )
    ax.legend(loc="best", fontsize="small")


def _require_rating_curve(result: Any) -> None:
    if (
        result.band_centers is None
        or result.measured is None
        or result.shifted_reference is None
    ):
        raise ValueError(
            "This rating result carries no band curve to plot (it was "
            "constructed without measured/reference data)."
        )


def plot_facade_insulation(
    result: Any, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-band façade sound-insulation profile (ISO 16283-3).

    Draws the standardized level difference ``D2m,nT`` first, then the
    other available quantities (``D2m``, ``D2m,n``, ``R'``) against
    frequency. Works for
    :class:`~phonometry.insulation.FacadeInsulationResult`.

    :param result: A façade result exposing ``d_2m``, ``d_2m_nt``,
        ``d_2m_n``, ``r_prime`` and (optionally) ``frequencies``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    dnt = np.asarray(result.d_2m_nt, dtype=np.float64)
    n = dnt.size
    freqs = getattr(result, "frequencies", None)
    if freqs is None:
        x = np.arange(n, dtype=np.float64)
        ax.set_xticks(x)
        ax.set_xticklabels([f"Band {i + 1}" for i in range(n)],
                           rotation=45, ha="right")
        ax.set_xlabel("Band")
    else:
        x = np.asarray(freqs, dtype=np.float64)
        _freq_axis(ax, x)

    # D2m,nT first so it is lines[0]; other quantities follow when present.
    curves = [("$D_{2m,nT}$", dnt)]
    curves.append(("$D_{2m}$", np.asarray(result.d_2m, dtype=np.float64)))
    if result.d_2m_n is not None:
        curves.append(("$D_{2m,n}$", np.asarray(result.d_2m_n, dtype=np.float64)))
    if result.r_prime is not None:
        curves.append(("$R'$", np.asarray(result.r_prime, dtype=np.float64)))
    for label, y in curves:
        ax.plot(x, y, "o-", label=label, **kwargs)

    ax.set_ylabel("Level difference / reduction index [dB]")
    ax.set_title("Façade sound insulation (ISO 16283-3)")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Room acoustics (ISO 3382)
# ---------------------------------------------------------------------------


def plot_room_acoustics(
    result: RoomAcousticsResult, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Per-band decay times (EDT/T20/T30) and clarity (C50/C80).

    The first panel shows the three decay times as grouped bars per band,
    invalid bands (failing the ISO 3382 evaluation-range criterion) hatched
    and greyed; the second panel shows C50 and C80.  When ``ax`` is given
    the two series are drawn on that single axes (times only) so the plot
    can be composed.

    :param result: A :class:`~phonometry.room_acoustics.RoomAcousticsResult`.
    :param ax: Existing axes for a single-panel (decay-times only) plot, or
        ``None`` to create the full two-panel figure.
    :return: The axes, or an array of two axes for the default figure.
    """
    freq = result.frequency
    n = np.asarray(result.t30, dtype=np.float64).size
    if freq is None:
        centers = np.arange(n, dtype=np.float64)
        labels = ["Broadband"] * n
        use_freq_axis = False
    else:
        centers = np.asarray(freq, dtype=np.float64)
        labels = [_format_freq(f) for f in centers]
        use_freq_axis = True

    positions = np.arange(n, dtype=np.float64)
    single = ax is not None
    if ax is not None:
        ax_times = ax
    else:
        axes = _new_axes_column(2, figsize=(7.5, 6.0), sharex=True)
        ax_times = cast("Axes", axes[0])

    _draw_decay_times(ax_times, positions, result, **kwargs)
    ax_times.set_ylabel("Reverberation time [s]")
    ax_times.set_title("Decay times and clarity")
    ax_times.set_xticks(positions)
    ax_times.set_xticklabels(labels, rotation=45, ha="right")
    ax_times.grid(True, axis="y", alpha=0.3)
    ax_times.legend(loc="best", fontsize="small")

    if single:
        if use_freq_axis:
            ax_times.set_xlabel("Frequency [Hz]")
        return ax_times

    ax_clarity = cast("Axes", axes[1])
    ax_clarity.plot(
        positions,
        np.asarray(result.c50, dtype=np.float64),
        "o-",
        color="#2ca02c",
        label="C50",
    )
    ax_clarity.plot(
        positions,
        np.asarray(result.c80, dtype=np.float64),
        "s--",
        color="#9467bd",
        label="C80",
    )
    ax_clarity.set_ylabel("Clarity [dB]")
    ax_clarity.set_xticks(positions)
    ax_clarity.set_xticklabels(labels, rotation=45, ha="right")
    ax_clarity.set_xlabel("Frequency [Hz]" if use_freq_axis else "Band")
    ax_clarity.grid(True, alpha=0.3)
    ax_clarity.legend(loc="best", fontsize="small")
    return axes


def _draw_decay_times(
    ax: Axes, positions: np.ndarray, result: RoomAcousticsResult, **kwargs: Any
) -> None:
    """Grouped EDT/T20/T30 bars, invalid bands hatched and greyed."""
    width = 0.27
    series = (
        ("EDT", result.edt, result.edt_valid, -width, "#1f77b4"),
        ("T20", result.t20, result.t20_valid, 0.0, "#ff7f0e"),
        ("T30", result.t30, result.t30_valid, width, "#2ca02c"),
    )
    for label, values, valid, offset, color in series:
        vals = np.asarray(values, dtype=np.float64)
        valid_arr = np.asarray(valid, dtype=bool)
        colors = [color if v else "#bbbbbb" for v in valid_arr]
        hatches = np.where(valid_arr, "", "//")
        # Merge per-series defaults with the user kwargs (user wins) freshly
        # each iteration so an overriding label/color is not frozen by the
        # first band group.
        bar_kwargs = {"color": colors, "label": label, **kwargs}
        bars = ax.bar(
            positions + offset,
            np.nan_to_num(vals),
            width=width,
            **bar_kwargs,
        )
        for bar, hatch in zip(bars, hatches, strict=True):
            if hatch:
                bar.set_hatch(hatch)
                bar.set_edgecolor("#555555")


# ---------------------------------------------------------------------------
# Sound power (ISO 3744 / ISO 3741 / ISO 9614-2)
# ---------------------------------------------------------------------------


def plot_sound_power(result: Any, ax: Axes | None = None, **kwargs: Any) -> Axes:
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
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    lw = np.asarray(result.sound_power_level, dtype=np.float64)
    n = lw.size
    # Band bars are drawn on evenly spaced categorical positions (a linear
    # frequency-band axis) so they stay legible; the tick labels carry the
    # band centres when available.
    positions = np.arange(n, dtype=np.float64)
    freqs = getattr(result, "frequencies", None)
    if freqs is None:
        labels = [f"Band {i + 1}" for i in range(n)]
        xlabel = "Band"
    else:
        labels = [_format_freq(f) for f in np.asarray(freqs, dtype=np.float64)]
        xlabel = "Frequency [Hz]"

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
    colors = ["#bbbbbb" if b else "#1f77b4" for b in neg]
    kwargs.setdefault("color", colors)
    bars = ax.bar(positions, np.nan_to_num(lw), **kwargs)
    for bar, is_neg in zip(bars, neg, strict=True):
        if is_neg:
            bar.set_hatch("//")
            bar.set_edgecolor("#555555")

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Sound power level LW [dB]")
    lwa = float(result.sound_power_level_a)
    if np.isfinite(lwa):
        ax.set_title(f"Sound power spectrum  (LWA = {lwa:.1f} dB(A))")
    else:
        ax.set_title("Sound power spectrum")
    if np.any(neg):
        ax.plot([], [], color="#bbbbbb", marker="s", ls="", label="Non-positive band")
        ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Sound intensity (ISO 9614 / IEC 61043)
# ---------------------------------------------------------------------------


def _bar_width(positions: np.ndarray, k: float = 0.2) -> np.ndarray:
    """Per-bar widths for a *logarithmic* frequency axis.

    A constant linear width makes high-frequency bars almost invisible on
    a log axis (a 25 Hz-wide bar spans a third of an octave at 100 Hz but
    a thousandth of one at 10 kHz).  Scaling each width with its own centre
    frequency (``width_i = k * f_i``, the fractional-band style) keeps the
    *drawn* (log-space) width visually constant across the whole spectrum,
    so ``get_width() / f`` is the same constant ``k`` for every band.
    """
    return k * np.asarray(positions, dtype=np.float64)


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

    kwargs.setdefault("color", "#1f77b4")
    kwargs.setdefault("label", "Pressure level Lp")
    ax.plot(freqs, lp, "o-", **kwargs)
    ax.plot(freqs, li, "s--", color="#d62728", label="Intensity level LI")
    _freq_axis(ax, freqs)
    ax.set_ylabel("Level [dB]")
    ax.grid(True, which="both", alpha=0.3)

    twin = ax.twinx()
    twin.bar(
        freqs,
        index,
        width=_bar_width(freqs),
        color="#2ca02c",
        alpha=0.25,
        label="δpI = Lp - LI",
    )
    twin.set_ylabel("Pressure-intensity index δpI [dB]")

    lines, labels = ax.get_legend_handles_labels()
    tlines, tlabels = twin.get_legend_handles_labels()
    ax.legend(lines + tlines, labels + tlabels, loc="best", fontsize="small")
    ax.set_title(
        f"Lp vs LI  (total δpI = {result.total_pressure_intensity_index:.1f} dB)"
    )
    return ax


# ---------------------------------------------------------------------------
# Schroeder decay curve (ISO 3382)
# ---------------------------------------------------------------------------


def plot_decay_curve(
    result: DecayCurve, ax: Axes | None = None, fits: bool = True, **kwargs: Any
) -> Axes:
    """Schroeder decay curve with optional straight T-fit overlays.

    :param result: A :class:`~phonometry.room_acoustics.DecayCurve`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param fits: Overlay the EDT (0..-10 dB), T20 (-5..-25 dB) and T30
        (-5..-35 dB) straight-line fits computed from the curve's own data.
    :param kwargs: Forwarded to the decay-curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    time = np.asarray(result.time, dtype=np.float64)
    level = np.asarray(result.level, dtype=np.float64)
    kwargs.setdefault("color", "#1f77b4")
    kwargs.setdefault("label", "Schroeder decay")
    ax.plot(time, level, **kwargs)

    if fits:
        for label, lo, hi, style in (
            ("EDT", 0.0, -10.0, "-"),
            ("T20", -5.0, -25.0, "--"),
            ("T30", -5.0, -35.0, "-."),
        ):
            fit = _fit_segment(time, level, lo, hi)
            if fit is not None:
                ax.plot(time, fit, style, lw=1, alpha=0.8, label=f"{label} fit")

    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Level re steady state [dB]")
    ax.set_ylim(top=3.0)
    ax.set_xlim(left=0.0, right=float(time[-1]) if time.size else None)
    band = result.band
    title = "Schroeder decay curve"
    if band is not None:
        title += f"  ({_format_freq(float(band))} Hz band)"
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    return ax


def _fit_segment(
    time: np.ndarray, level: np.ndarray, lo: float, hi: float
) -> np.ndarray | None:
    """Least-squares straight line over ``hi <= level <= lo``, over full time."""
    mask = (level <= lo) & (level >= hi) & np.isfinite(level)
    if int(np.count_nonzero(mask)) < 2:
        return None
    slope, intercept = np.polyfit(time[mask], level[mask], 1)
    return np.asarray(slope * time + intercept, dtype=np.float64)


# ---------------------------------------------------------------------------
# Impulse-response acquisition (ISO 18233)
# ---------------------------------------------------------------------------


def _time_axis(n: int, fs: int | None) -> tuple[np.ndarray, str]:
    """Sample times in seconds when ``fs`` is known, else sample index."""
    if fs:
        return np.arange(n) / float(fs), "Time [s]"
    return np.arange(n, dtype=np.float64), "Sample"


def plot_impulse_response(
    result: "ImpulseResponseResult", ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Impulse-response waveform and its log-magnitude / Schroeder decay.

    Two stacked panels: the (peak-normalised) time-domain waveform on top and,
    below it, the log-magnitude envelope in dB with the Schroeder
    backward-integrated energy-decay curve overlaid. With ``ax`` given, only
    the decay panel is drawn on it.

    :param result: An :class:`~phonometry.room_ir.ImpulseResponseResult`.
    :param ax: Existing axes for the decay panel, or ``None`` for a fresh
        two-panel figure.
    :param kwargs: Forwarded to the waveform / envelope ``plot`` calls.
    :return: The decay-panel axes (``ax`` given) or the array of two axes.
    """
    h = np.asarray(result.ir, dtype=np.float64)
    n = h.shape[-1]
    time, xlabel = _time_axis(n, result.fs)
    peak = float(np.max(np.abs(h)))
    tiny = np.finfo(np.float64).tiny
    norm = peak if peak > 0.0 else 1.0
    env_db = 20.0 * np.log10(np.maximum(np.abs(h), tiny) / norm)
    # Schroeder backward integration of the squared IR (broadband).
    energy = np.cumsum(h[::-1] ** 2)[::-1]
    total = float(energy[0]) if energy.size else 0.0
    edc_db = 10.0 * np.log10(np.maximum(energy, tiny) / (total if total > 0.0 else 1.0))

    color = kwargs.pop("color", "#1f77b4")

    def _decay(axd: Axes) -> None:
        axd.plot(time, env_db, color="#9ecae1", lw=0.8, label="Log-magnitude envelope")
        axd.plot(time, edc_db, color="#d62728", lw=1.8, label="Schroeder decay")
        axd.set_xlabel(xlabel)
        axd.set_ylabel("Level re peak [dB]")
        axd.set_ylim(bottom=-80.0, top=5.0)
        axd.set_xlim(left=float(time[0]) if n else 0.0,
                     right=float(time[-1]) if n else None)
        axd.grid(True, alpha=0.3)
        axd.legend(loc="upper right", fontsize="small")

    if ax is not None:
        _decay(ax)
        ax.set_title(f"Impulse response ({result.method})")
        return ax

    axes = _new_axes_column(2, sharex=True, figsize=(8.0, 6.0))
    axes[0].plot(time, h / norm, color=color, lw=0.8, **kwargs)
    axes[0].set_ylabel("Amplitude (norm.)")
    axes[0].set_title(f"Impulse response ({result.method})")
    axes[0].grid(True, alpha=0.3)
    _decay(axes[1])
    return axes


def plot_excitation(
    signal: "np.ndarray | Any",
    fs: int,
    *,
    kind: str = "sweep",
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes | np.ndarray:
    """Plot an ISO 18233 excitation signal (sweep or MLS).

    A documented helper for the raw arrays returned by
    :func:`~phonometry.sweep_signal` and :func:`~phonometry.mls_signal`, which
    stay plain :class:`numpy.ndarray` (they are meant for playback). For a
    swept sine the waveform and its spectrogram are drawn; for an MLS the first
    samples of the bipolar sequence and its (flat) magnitude spectrum.

    :param signal: The excitation samples (1D array-like).
    :param fs: Sample rate in Hz (for the time and frequency axes).
    :param kind: ``"sweep"`` (default) or ``"mls"``.
    :param ax: Existing axes for the top (time-domain) panel, or ``None`` for a
        fresh two-panel figure.
    :param kwargs: Forwarded to the time-domain ``plot`` call.
    :return: The time-domain axes (``ax`` given) or the array of two axes.
    """
    x = np.asarray(signal, dtype=np.float64)
    n = x.shape[-1]
    t = np.arange(n) / float(fs)
    color = kwargs.pop("color", "#1f77b4")

    two_panel = ax is None
    if two_panel:
        axes = _new_axes_column(2, figsize=(8.0, 6.0))
        ax_time = cast("Axes", axes[0])
    else:
        ax_time = cast("Axes", ax)

    if kind == "mls":
        show = min(n, 120)
        ax_time.step(np.arange(show), x[:show], where="mid", color=color, **kwargs)
        ax_time.set_xlabel("Sample")
        ax_time.set_ylabel("Amplitude")
        ax_time.set_ylim(-1.4, 1.4)
        ax_time.set_title(f"MLS excitation (first {show} of {n} samples)")
        ax_time.grid(True, alpha=0.3)
        if not two_panel:
            return ax_time
        spec = np.abs(np.fft.rfft(x))
        freqs = np.fft.rfftfreq(n, d=1.0 / fs)
        ax_f = axes[1]
        ax_f.semilogx(freqs[1:], 20.0 * np.log10(spec[1:] / np.median(spec[1:])),
                      color="#d62728", lw=0.8)
        ax_f.set_xlabel("Frequency [Hz]")
        ax_f.set_ylabel("Magnitude [dB]")
        ax_f.set_title("Magnitude spectrum (flat)")
        ax_f.grid(True, which="both", alpha=0.3)
        return axes

    # Swept sine.
    ax_time.plot(t, x, color=color, lw=0.6, **kwargs)
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Amplitude")
    ax_time.set_title("Exponential sine sweep")
    ax_time.grid(True, alpha=0.3)
    if not two_panel:
        return ax_time
    ax_s = axes[1]
    nperseg = max(256, min(2048, n // 16))
    ax_s.specgram(x, NFFT=nperseg, Fs=fs, noverlap=nperseg // 2, cmap="magma")
    ax_s.set_xlabel("Time [s]")
    ax_s.set_ylabel("Frequency [Hz]")
    ax_s.set_title("Spectrogram (exponential frequency rise)")
    return axes


# ---------------------------------------------------------------------------
# Surface scattering & diffusion (ISO 17497)
# ---------------------------------------------------------------------------


def plot_scattering_coefficient(
    result: Any, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Random-incidence scattering coefficient ``s`` versus frequency.

    :param result: A :class:`~phonometry.scattering_diffusion.ScatteringResult`
        exposing ``frequencies`` and ``scattering``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    s = np.asarray(result.scattering, dtype=np.float64)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("color", "#1f77b4")
    ax.plot(freqs, s, **kwargs)
    _freq_axis(ax, freqs)
    ax.set_ylabel("Scattering coefficient s")
    # s is normally in [0, 1], but edge effects (Clause 6.3.2) can push it above
    # 1 and those values are kept, not clipped; grow the top so they stay visible.
    top = max(1.05, float(np.nanmax(s)) * 1.05) if s.size else 1.05
    ax.set_ylim(0.0, top)
    ax.set_title("Random-incidence scattering coefficient (ISO 17497-1)")
    ax.grid(True, alpha=0.3)
    return ax


def plot_diffusion_polar(
    result: Any, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Polar reflected-level response with the diffusion coefficient annotated.

    :param result: A :class:`~phonometry.scattering_diffusion.DiffusionResult`
        exposing ``angles`` (degrees), ``levels`` (dB) and ``coefficient``.
    :param ax: Existing (ideally polar) axes, or ``None`` to create a polar one.
    :return: The polar axes.
    """
    if ax is None:
        plt = _import_pyplot()
        _fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
    angles = np.radians(np.asarray(result.angles, dtype=np.float64))
    levels = np.asarray(result.levels, dtype=np.float64)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("color", "#1f77b4")
    ax.plot(angles, levels, **kwargs)
    ax.fill(angles, levels, alpha=0.15, color=kwargs["color"])
    ax.set_title(
        f"Diffusion coefficient d = {float(result.coefficient):.2f} "
        "(ISO 17497-2)"
    )
    return cast("Axes", ax)


def plot_insitu_absorption(
    result: Any, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """In-situ one-third-octave absorption spectrum ``alpha(f)``.

    :param result: An
        :class:`~phonometry.road_absorption.InsituAbsorptionResult` exposing
        ``frequencies`` and ``absorption``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    alpha = np.asarray(result.absorption, dtype=np.float64)
    positions = np.arange(freqs.size, dtype=np.float64)
    kwargs.setdefault("color", "#1f77b4")
    ax.bar(positions, np.nan_to_num(alpha), **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels([_format_freq(f) for f in freqs], rotation=45, ha="right")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Absorption coefficient")
    ax.set_ylim(0.0, 1.0)
    ax.set_title("In-situ road-surface absorption (ISO 13472-1)")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Human vibration (ISO 8041-1 / ISO 2631 / ISO 5349 / Directive 2002/44/EC)
# ---------------------------------------------------------------------------


def plot_vibration_weighting(
    result: Any, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Frequency-weighting factor (dB) versus frequency (ISO 8041-1).

    :param result: A
        :class:`~phonometry.human_vibration.WeightingResponse` exposing
        ``name``, ``frequencies`` and ``magnitude_db``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    mag_db = np.asarray(result.magnitude_db, dtype=np.float64)
    kwargs.setdefault("color", "#1f77b4")
    ax.semilogx(freqs, mag_db, **kwargs)
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Weighting factor [dB]")
    ax.set_title(f"Frequency weighting {result.name} (ISO 8041-1)")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_weighted_spectrum(
    result: Any, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Unweighted vs weighted one-third-octave acceleration spectrum.

    Draws the measured band accelerations and, overlaid, the weighted band
    contributions ``W_i*a_i``; the overall ``a_w`` is annotated in the title.

    :param result: A
        :class:`~phonometry.human_vibration.WeightedSpectrum` exposing
        ``frequencies``, ``band_accelerations``, ``weighted``, ``overall`` and
        ``weighting_name``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    raw = np.asarray(result.band_accelerations, dtype=np.float64)
    weighted = np.asarray(result.weighted, dtype=np.float64)
    positions = np.arange(freqs.size, dtype=np.float64)
    width = 0.4
    # The weighted bars are the primary artist; forward user kwargs there.
    kwargs.setdefault("color", "#1f77b4")
    ax.bar(
        positions - width / 2, raw, width, color="#bbbbbb", label="Unweighted $a_i$"
    )
    ax.bar(
        positions + width / 2,
        weighted,
        width,
        label=f"Weighted $W_i a_i$ ({result.weighting_name})",
        **kwargs,
    )
    ax.set_xticks(positions)
    ax.set_xticklabels([_format_freq(f) for f in freqs], rotation=45, ha="right")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel(r"r.m.s. acceleration [m/s$^2$]")
    ax.set_title(
        f"Weighted acceleration spectrum  ($a_w$ = {float(result.overall):.3f} "
        r"m/s$^2$)"
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


def plot_daily_exposure(
    result: Any, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Partial daily exposures against the EAV / ELV (Directive 2002/44/EC).

    Draws one bar per operation (its partial exposure ``A_i(8)``), a combined
    ``A(8)`` bar, and the exposure action and limit value as horizontal lines.

    :param result: A
        :class:`~phonometry.human_vibration.DailyVibrationExposure` exposing
        ``labels``, ``partials``, ``a8`` and ``assessment``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    partials = np.asarray(result.partials, dtype=np.float64)
    labels = [*result.labels, "A(8)"]
    values = [*partials.tolist(), float(result.a8)]
    positions = np.arange(len(values), dtype=np.float64)
    colors = ["#bbbbbb"] * partials.size + ["#1f77b4"]
    kwargs.setdefault("color", colors)
    ax.bar(positions, values, **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel(r"Vibration exposure A(8) [m/s$^2$]")

    assessment = result.assessment
    eav = float(assessment.action_value)
    elv = float(assessment.limit_value)
    ax.axhline(eav, color="#ff7f0e", ls="--", label=f"EAV = {eav:g}")
    ax.axhline(elv, color="#d62728", ls="--", label=f"ELV = {elv:g}")
    top = max(elv, float(np.max(values))) * 1.15
    ax.set_ylim(0.0, top)
    kind = str(assessment.kind).upper()
    ax.set_title(
        f"Daily {kind} exposure  (A(8) = {float(result.a8):.2f} "
        rf"m/s$^2$, {assessment.zone})"
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax
