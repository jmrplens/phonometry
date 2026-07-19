#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the room domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_SECONDARY_LIGHT,
    _C_TERTIARY,
    _LEGEND_UPPER_RIGHT,
    _band_axis,
    _draw_decay_times,
    _fit_segment,
    _format_freq,
    _freq_axis,
    _new_axes,
    _new_axes_column,
    _time_axis,
    format_frequency_axis,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from ..room.reverberation_prediction import ReverberationModelResult
    from ..room.open_plan import OpenPlanResult
    from ..room.room_acoustics import DecayCurve, RoomAcousticsResult
    from ..room.room_ir import ImpulseResponseResult
    from ..room.enclosed_space_absorption import ReverberationResult
    from ..room.room_noise import NCResult, RCResult

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
    ax_times.set_title("ISO 3382 decay times and clarity")
    _band_axis(ax_times, labels, xlabel=None)
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
        color=_C_TERTIARY,
        label="C50",
    )
    ax_clarity.plot(
        positions,
        np.asarray(result.c80, dtype=np.float64),
        "s--",
        color=_C_QUATERNARY,
        label="C80",
    )
    ax_clarity.set_ylabel("Clarity [dB]")
    _band_axis(
        ax_clarity, labels, xlabel="Frequency [Hz]" if use_freq_axis else "Band"
    )
    ax_clarity.grid(True, alpha=0.3)
    ax_clarity.legend(loc="best", fontsize="small")
    return axes

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
    kwargs.setdefault("color", _C_PRIMARY)
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
    title = "ISO 3382 Schroeder decay curve"
    if band is not None:
        title += f"  ({_format_freq(float(band))} Hz band)"
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    return ax

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
    if n == 0:
        raise ValueError("impulse response is empty; nothing to plot.")
    time, xlabel = _time_axis(n, result.fs)
    peak = float(np.max(np.abs(h)))
    tiny = np.finfo(np.float64).tiny
    norm = peak if peak > 0.0 else 1.0
    env_db = 20.0 * np.log10(np.maximum(np.abs(h), tiny) / norm)
    # Schroeder backward integration of the squared IR (broadband).
    energy = np.cumsum(h[::-1] ** 2)[::-1]
    total = float(energy[0]) if energy.size else 0.0
    edc_db = 10.0 * np.log10(np.maximum(energy, tiny) / (total if total > 0.0 else 1.0))

    color = kwargs.pop("color", _C_PRIMARY)

    def _decay(axd: Axes) -> None:
        axd.plot(time, env_db, color=_C_PRIMARY_LIGHT, lw=0.8,
                 label="Log-magnitude envelope")
        axd.plot(time, edc_db, color=_C_REFERENCE, lw=1.8, label="Schroeder decay")
        axd.set_xlabel(xlabel)
        axd.set_ylabel("Level re peak [dB]")
        axd.set_ylim(bottom=-80.0, top=5.0)
        axd.set_xlim(left=float(time[0]) if n else 0.0,
                     right=float(time[-1]) if n else None)
        axd.grid(True, alpha=0.3)
        axd.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _decay(ax)
        ax.set_title(f"ISO 18233 impulse response ({result.method})")
        return ax

    axes = _new_axes_column(2, sharex=True, figsize=(8.0, 6.0))
    axes[0].plot(time, h / norm, color=color, lw=0.8, **kwargs)
    axes[0].set_ylabel("Amplitude (norm.)")
    axes[0].set_title(f"ISO 18233 impulse response ({result.method})")
    axes[0].grid(True, alpha=0.3)
    _decay(axes[1])
    return axes

def plot_noise_criterion(
    result: "NCResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Measured spectrum against the NC curve family (ANSI/ASA S12.2-2019).

    :param result: A :class:`~phonometry.room_noise.NCResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the measured-spectrum :meth:`plot`.
    :return: The axes.
    """
    from ..room.room_noise import NC_CURVES, NC_INDICES, OCTAVE_BANDS

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    levels = np.asarray(result.levels, dtype=np.float64)
    for row, idx in zip(NC_CURVES, NC_INDICES):
        ax.plot(OCTAVE_BANDS, row, color=_C_MUTED, lw=0.8, zorder=1)
        ax.annotate(
            f"{idx:.0f}", (OCTAVE_BANDS[-1], row[-1]),
            fontsize="x-small", color=_C_MUTED, va="center",
        )
    valid = ~np.isnan(levels)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Measured")
    ax.plot(freqs[valid], levels[valid], "o-", zorder=3, **kwargs)
    # Nearest *valid* band rather than float equality against the stored
    # value; the marker sits on that band so its x and y stay paired.
    candidates = np.flatnonzero(valid)
    if candidates.size:
        governing = int(
            candidates[
                np.argmin(np.abs(freqs[candidates] - result.governing_frequency))
            ]
        )
        ax.plot(
            [freqs[governing]],
            [levels[governing]],
            "D", color=_C_REFERENCE, zorder=4,
            label=f"Governing band ({_format_freq(result.governing_frequency)})",
        )
    _freq_axis(ax, OCTAVE_BANDS)
    ax.set_ylabel("Octave-band SPL [dB]")
    ax.set_title(
        f"ANSI/ASA S12.2 NC-{result.rating:g} "
        f"({_format_freq(result.governing_frequency)})"
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax

def plot_room_criterion(
    result: "RCResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Measured spectrum against the reference RC Mark II curve (Annex D).

    Shades the rumble tolerance (reference + 5 dB below 500 Hz) and the hiss
    tolerance (reference + 3 dB at and above 1000 Hz).

    :param result: A :class:`~phonometry.room_noise.RCResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the measured-spectrum :meth:`plot`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    levels = np.asarray(result.levels, dtype=np.float64)
    reference = np.asarray(result.reference_curve, dtype=np.float64)
    valid = ~np.isnan(levels)

    ax.plot(freqs, reference, "s--", color=_C_MUTED,
            label=f"Reference RC-{result.rating}")
    low = freqs <= 500.0
    high = freqs >= 1000.0
    ax.fill_between(freqs[low], reference[low], reference[low] + 5.0,
                    color=_C_SECONDARY_LIGHT, alpha=0.35,
                    label="Rumble tolerance (+5 dB)")
    ax.fill_between(freqs[high], reference[high], reference[high] + 3.0,
                    color=_C_PRIMARY_LIGHT, alpha=0.45,
                    label="Hiss tolerance (+3 dB)")
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Measured")
    ax.plot(freqs[valid], levels[valid], "o-", zorder=3, **kwargs)
    _freq_axis(ax, freqs)
    ax.set_ylabel("Octave-band SPL [dB]")
    ax.set_title(f"ANSI/ASA S12.2 {result.label}")
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax

def plot_enclosed_space_absorption(
    result: "ReverberationResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Reverberation time over the octave bands (EN 12354-6).

    :param result: A :class:`~phonometry.enclosed_space_absorption.ReverberationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the reverberation-time ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    rt = np.asarray(result.reverberation_time, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    ax.plot(freq, rt, **kwargs)
    _freq_axis(ax, freq)
    ax.set_ylabel("Reverberation time $T$ [s]")
    ax.set_title("EN 12354-6 reverberation time")
    ax.set_ylim(bottom=0.0)
    ax.grid(True, which="both", alpha=0.3)
    return ax

def plot_reverberation_models(
    result: "ReverberationModelResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Reverberation time by five statistical models over the bands.

    Draws the Sabine, Eyring, Millington-Sette, Fitzroy and Arau-Puchades
    curves, with Arau-Puchades emphasised as the recommended model for a
    non-uniform absorption distribution.

    :param result: A
        :class:`~phonometry.reverberation_prediction.ReverberationModelResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to every curve ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    styles = (
        ("Sabine", result.sabine, _C_SECONDARY, "s", 1.4),
        ("Eyring", result.eyring, _C_TERTIARY, "^", 1.4),
        ("Millington-Sette", result.millington_sette, _C_QUATERNARY, "v", 1.4),
        ("Fitzroy", result.fitzroy, _C_MUTED, "D", 1.4),
        ("Arau-Puchades", result.arau_puchades, _C_PRIMARY, "o", 2.4),
    )
    for label, curve, color, marker, lw in styles:
        ax.plot(
            freq,
            np.asarray(curve, dtype=np.float64),
            color=color,
            marker=marker,
            lw=lw,
            label=label,
            **kwargs,
        )
    _freq_axis(ax, freq)
    ax.set_ylabel("Reverberation time $T$ [s]")
    ax.set_title(
        f"Reverberation-time models — $V$ = {result.volume:.0f} m³, "
        f"$S$ = {result.surface_area:.0f} m²"
    )
    ax.set_ylim(bottom=0.0)
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax

def plot_open_plan(
    result: "OpenPlanResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Spatial decay of speech with the distraction/privacy distances marked.

    Redraws the Clause 6.2 regression line ``Lp,A,S(r) = Lp,A,S,4m -
    D2,S lg(r/4)/lg 2`` over the 2 m to 16 m fitting range (extended to
    reach ``rP`` when it lies further out) and marks the distraction
    distance ``rD`` and the privacy distance ``rP`` from the STI regression.

    :param result: An :class:`~phonometry.open_plan.OpenPlanResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the decay-line ``plot`` call.
    :return: The axes.
    :raises ValueError: If the spatial-decay regression is undefined
        (``d2s`` / ``lp_as_4m`` are NaN).
    """
    if not (np.isfinite(result.d2s) and np.isfinite(result.lp_as_4m)):
        raise ValueError(
            "plot() needs the spatial-decay regression; this result's d2s / "
            "lp_as_4m are NaN (fewer than two positions in the 2 m to 16 m "
            "range)."
        )
    ax = ax if ax is not None else _new_axes()
    import matplotlib.ticker as mticker

    r_max = 16.0
    for marker in (result.rd, result.rp):
        if np.isfinite(marker):
            r_max = max(r_max, 1.15 * marker)
    r = np.geomspace(2.0, r_max, 200)
    level = result.lp_as_4m - result.d2s * np.log2(r / 4.0)

    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault(
        "label", rf"$D_{{2,S}}$ = {result.d2s:.1f} dB per doubling"
    )
    ax.plot(r, level, **kwargs)
    ax.plot([4.0], [result.lp_as_4m], "o", color=_C_PRIMARY, ms=7,
            label=rf"$L_{{p,A,S,4m}}$ = {result.lp_as_4m:.1f} dB")
    if np.isfinite(result.rd):
        ax.axvline(result.rd, color=_C_SECONDARY, ls="--",
                   label=rf"$r_D$ = {result.rd:.1f} m (STI 0.50)")
    if np.isfinite(result.rp):
        ax.axvline(result.rp, color=_C_REFERENCE, ls=":",
                   label=rf"$r_P$ = {result.rp:.1f} m (STI 0.20)")

    ax.set_xscale("log", base=2)
    ticks = [float(2**k) for k in range(1, int(np.ceil(np.log2(r_max))) + 1)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.set_xlabel("Distance from the sound source [m]")
    ax.set_ylabel("A-weighted SPL of speech [dB]")
    ax.set_title("ISO 3382-3 spatial decay of speech")
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


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
    if n == 0:
        raise ValueError("excitation signal is empty; nothing to plot.")
    t = np.arange(n) / float(fs)
    color = kwargs.pop("color", _C_PRIMARY)

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
        ax_time.set_title(
            f"ISO 18233 MLS excitation (first {show} of {n} samples)"
        )
        ax_time.grid(True, alpha=0.3)
        if not two_panel:
            return ax_time
        spec = np.abs(np.fft.rfft(x))
        freqs = np.fft.rfftfreq(n, d=1.0 / fs)
        ax_f = axes[1]
        ac = spec[1:]
        denom = float(np.median(ac)) if ac.size else 1.0
        ax_f.semilogx(freqs[1:], 20.0 * np.log10(
                      np.maximum(ac, 1e-10) / (denom if denom > 0.0 else 1.0)),
                      color=_C_REFERENCE, lw=0.8)
        ax_f.set_xlabel("Frequency [Hz]")
        ax_f.set_ylabel("Magnitude [dB]")
        ax_f.set_title("Magnitude spectrum (flat)")
        ax_f.grid(True, which="both", alpha=0.3)
        format_frequency_axis(ax_f, float(freqs[1]), float(freqs[-1]))
        return axes

    # Swept sine.
    ax_time.plot(t, x, color=color, lw=0.6, **kwargs)
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Amplitude")
    ax_time.set_title("ISO 18233 exponential sine sweep")
    ax_time.grid(True, alpha=0.3)
    if not two_panel:
        return ax_time
    ax_s = axes[1]
    nperseg = min(n, max(256, min(2048, n // 16)))
    ax_s.specgram(x, NFFT=nperseg, Fs=fs, noverlap=nperseg // 2, cmap="magma")
    ax_s.set_xlabel("Time [s]")
    ax_s.set_ylabel("Frequency [Hz]")
    ax_s.set_title("Spectrogram (exponential frequency rise)")
    return axes
