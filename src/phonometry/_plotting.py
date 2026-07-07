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
    from .room_acoustics import DecayCurve, RoomAcousticsResult
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
    return cast("np.ndarray", np.atleast_1d(axes))


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
    (``time`` / ``loudness_vs_time``) a second panel with loudness vs time
    is added and an array of two axes is returned; otherwise a single axes
    is returned.

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

    ax_specific.plot(bark, specific, color="#1f77b4", **kwargs)
    ax_specific.fill_between(bark, specific, color="#1f77b4", alpha=0.25)
    ax_specific.set_xlabel("Critical-band rate z [Bark]")
    ax_specific.set_ylabel("Specific loudness N' [sone/Bark]")
    ax_specific.set_xlim(0.0, bark[-1])
    ax_specific.set_ylim(bottom=0.0)
    ax_specific.set_title(
        f"Loudness N = {result.loudness:.2f} sone "
        f"({result.loudness_level:.1f} phon)"
    )
    ax_specific.grid(True, alpha=0.3)

    if not time_varying:
        return ax_specific

    ax_time = cast("Axes", axes[1])
    time = np.asarray(result.time, dtype=np.float64)
    lvt = np.asarray(result.loudness_vs_time, dtype=np.float64)
    ax_time.plot(time, lvt, color="#2ca02c", label="N(t)")
    if result.n5 is not None:
        ax_time.axhline(result.n5, color="#d62728", ls="--", lw=1, label=f"N5={result.n5:.2f}")
    if result.n10 is not None:
        ax_time.axhline(result.n10, color="#ff7f0e", ls=":", lw=1, label=f"N10={result.n10:.2f}")
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Loudness N [sone]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.grid(True, alpha=0.3)
    ax_time.legend(loc="best", fontsize="small")
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
    ax.bar(positions, mti, color="#1f77b4", **kwargs)
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
) -> Axes:
    """Shared renderer for airborne and impact rating figures.

    Draws the measured curve against the shifted reference and shades the
    unfavourable deviations: where the reference exceeds the measurement
    for airborne insulation (higher is better) and where the measurement
    exceeds the reference for impact sound (lower is better).
    """
    ax = ax if ax is not None else _new_axes()
    ax.plot(band_centers, measured, "o-", color="#1f77b4", label="Measured")
    ax.plot(
        band_centers, reference, "s--", color="#d62728", label="Shifted reference"
    )
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
    ax.set_title(
        f"{title} = {rating} dB  (Sigma unfav. = {unfavourable_sum:.1f} dB)"
    )
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


def plot_weighted_rating(
    result: Any, ax: Axes | None = None, **kwargs: Any
) -> Axes:
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
    """Impact rating curve vs shifted reference (ISO 717-2)."""
    _require_rating_curve(result)
    return _plot_rating(
        np.asarray(result.band_centers, dtype=np.float64),
        np.asarray(result.measured, dtype=np.float64),
        np.asarray(result.shifted_reference, dtype=np.float64),
        impact=True,
        rating=result.rating,
        unfavourable_sum=result.unfavourable_sum,
        title=f"Ln,w (CI={result.ci:+d})",
        ylabel="Impact sound pressure level [dB]",
        ax=ax,
        **kwargs,
    )


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
    ax_clarity.plot(positions, np.asarray(result.c50, dtype=np.float64), "o-",
                    color="#2ca02c", label="C50")
    ax_clarity.plot(positions, np.asarray(result.c80, dtype=np.float64), "s--",
                    color="#9467bd", label="C80")
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
        bars = ax.bar(
            positions + offset, np.nan_to_num(vals), width=width,
            color=colors, label=label, **kwargs,
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

    negative = getattr(result, "negative_band", None)
    neg = (
        np.asarray(negative, dtype=bool)
        if negative is not None
        else np.zeros(n, dtype=bool)
    )
    colors = ["#bbbbbb" if b else "#1f77b4" for b in neg]
    bars = ax.bar(positions, np.nan_to_num(lw), color=colors, **kwargs)
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
        ax.plot([], [], color="#bbbbbb", marker="s", ls="",
                label="Non-positive band")
        ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


def _bar_width(positions: np.ndarray) -> float:
    if positions.size > 1:
        return 0.8 * float(np.min(np.diff(np.sort(positions))))
    return 0.8


# ---------------------------------------------------------------------------
# Sound intensity (ISO 9614 / IEC 61043)
# ---------------------------------------------------------------------------


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

    ax.plot(freqs, lp, "o-", color="#1f77b4", label="Pressure level Lp", **kwargs)
    ax.plot(freqs, li, "s--", color="#d62728", label="Intensity level LI")
    _freq_axis(ax, freqs)
    ax.set_ylabel("Level [dB]")
    ax.grid(True, which="both", alpha=0.3)

    twin = ax.twinx()
    twin.bar(freqs, index, width=_bar_width(freqs), color="#2ca02c", alpha=0.25,
             label="δpI = Lp - LI")
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
    ax.plot(time, level, color="#1f77b4", label="Schroeder decay", **kwargs)

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
