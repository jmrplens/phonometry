#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the hearing domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_SECONDARY_LIGHT,
    _LEGEND_UPPER_RIGHT,
    _STI_BAND_CENTERS,
    _band_axis,
    _fractile_band,
    _freq_axis,
    _new_axes,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from ..hearing.occupational_exposure import ExposureResult
    from ..hearing.threshold import AgeThresholdResult
    from ..hearing.noise_induced_hearing_loss import HtlanResult, NiptsResult
    from ..hearing.sii import SIIResult
    from ..hearing.sti import STIResult
    from ..hearing.objective_intelligibility import STOIResult

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
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(positions, mti, **kwargs)
    if mti.size == len(_STI_BAND_CENTERS):
        _band_axis(ax, np.asarray(_STI_BAND_CENTERS))
    else:
        ax.set_xticks(positions)
        ax.set_xlabel("Band")
    ax.set_ylabel("Modulation transfer index MTI")
    ax.set_ylim(0.0, 1.0)
    ax.set_title(f"IEC 60268-16 STI = {result.sti:.2f}  (rating {result.rating})")
    ax.grid(True, axis="y", alpha=0.3)
    return ax

def plot_stoi(result: "STOIResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Intermediate intelligibility that averages to the STOI/ESTOI index.

    For STOI the intermediate measure decomposes per one-third-octave band, so
    the mean correlation per band is drawn as bars; for ESTOI, whose index
    mixes the bands, the spectral correlation per analysis segment is drawn as
    a line.

    :param result: A :class:`~phonometry.hearing.objective_intelligibility.STOIResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the underlying :meth:`bar`/:meth:`plot`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    name = "ESTOI" if result.extended else "STOI"
    if result.band_scores is not None:
        freqs = np.asarray(result.band_frequencies, dtype=np.float64)
        scores = np.asarray(result.band_scores, dtype=np.float64)
        positions = np.arange(scores.size)
        kwargs.setdefault("color", _C_PRIMARY)
        ax.bar(positions, scores, **kwargs)
        ax.set_xticks(positions)
        ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
        ax.set_xlabel("One-third-octave band [Hz]")
        ax.set_ylabel("Mean intermediate correlation")
    else:
        scores = np.asarray(result.segment_scores, dtype=np.float64)
        kwargs.setdefault("color", _C_PRIMARY)
        ax.plot(np.arange(scores.size), scores, **kwargs)
        ax.set_xlabel("Analysis segment")
        ax.set_ylabel("Spectral correlation $d_m$")
    # The intermediate correlations are cosine-similarity quantities in
    # [-1, 1] (unlike the [0, 1] ratios of plot_sti/plot_sii), so keep room
    # for anti-correlated bands rather than clipping them at zero.
    ax.set_ylim(-1.0, 1.0)
    ax.set_title(f"{name} = {result.value:.3f}")
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
    positions = _band_axis(ax, freqs)
    ax.bar(positions, audibility, color=_C_PRIMARY_LIGHT,
           label="Band audibility $A_i$")
    kwargs.setdefault("color", _C_PRIMARY)
    # A fully masked speech signal (SII = 0) has an all-zero contribution;
    # keep the zero bars rather than dividing 0/0 into NaN.
    peak = float(contribution.max()) if contribution.size else 0.0
    scaled = contribution / peak if peak > 0.0 else contribution
    ax.bar(positions, scaled, width=0.5,
           label=r"Importance-weighted $I_i A_i$ (scaled)", **kwargs)
    ax.set_ylabel("Band audibility")
    ax.set_ylim(0.0, 1.0)
    ax.set_title(f"ANSI S3.5 SII = {result.sii:.3f}")
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax

def plot_age_threshold(
    result: "AgeThresholdResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Median age-related hearing threshold with the 10-90 % fractile band.

    :param result: An :class:`~phonometry.hearing.AgeThresholdResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the median line ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    median = np.asarray(result.median, dtype=np.float64)
    su = np.asarray(result.spread_upper, dtype=np.float64)
    sl = np.asarray(result.spread_lower, dtype=np.float64)

    _fractile_band(ax, freqs, median, sl, su, color=_C_PRIMARY_LIGHT)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.plot(freqs, median, "o-", label="Median", **kwargs)
    if abs(result.fractile - 0.5) > 1e-9:
        ax.plot(freqs, np.asarray(result.threshold, dtype=np.float64), "s--",
                color=_C_REFERENCE, label=f"Fractile {result.fractile:g}")
    _freq_axis(ax, freqs)
    ax.set_ylabel("Threshold deviation from age 18 [dB]")
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    ax.set_title(f"ISO 7029 hearing threshold — {result.sex}, age {result.age:g}")
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax

def plot_nipts(
    result: "NiptsResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Median NIPTS spectrum with the 10-90 % fractile band (ISO 1999).

    :param result: A :class:`~phonometry.noise_induced_hearing_loss.NiptsResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the median line ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    median = np.asarray(result.median, dtype=np.float64)
    du = np.asarray(result.spread_upper, dtype=np.float64)
    dl = np.asarray(result.spread_lower, dtype=np.float64)

    _fractile_band(ax, freqs, median, dl, du, color=_C_SECONDARY_LIGHT, floor=0.0)
    kwargs.setdefault("color", _C_SECONDARY)
    ax.plot(freqs, median, "o-", label="Median $N_{50}$", **kwargs)
    if abs(result.fractile - 0.5) > 1e-9:
        ax.plot(freqs, np.asarray(result.value, dtype=np.float64), "s--",
                color=_C_REFERENCE, label=f"Fractile {result.fractile:g}")
    _freq_axis(ax, freqs)
    ax.set_ylabel("NIPTS [dB]")
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    ax.set_title(
        f"ISO 1999 NIPTS — $L_{{EX,8h}}$ = {result.l_ex:g} dB, "
        f"{result.years:g} yr"
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax

def plot_htlan(
    result: "HtlanResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Age, noise and combined hearing threshold components (ISO 1999, 6.1).

    :param result: A :class:`~phonometry.noise_induced_hearing_loss.HtlanResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the combined-threshold line ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    ax.plot(freqs, np.asarray(result.htla, dtype=np.float64), "o-",
            color=_C_PRIMARY, label="Age (HTLA, ISO 7029)")
    ax.plot(freqs, np.asarray(result.nipts, dtype=np.float64), "^-",
            color=_C_SECONDARY, label="Noise (NIPTS)")
    kwargs.setdefault("color", _C_REFERENCE)
    ax.plot(freqs, np.asarray(result.threshold, dtype=np.float64), "s--",
            label="Age + noise (HTLAN)", **kwargs)
    _freq_axis(ax, freqs)
    ax.set_ylabel("Hearing threshold level [dB]")
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    ax.set_title(
        f"ISO 1999 HTLAN — {result.sex}, age {result.age:g}, "
        f"{result.l_ex:g} dB / {result.years:g} yr"
    )
    ax.legend(loc="lower left", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax

def plot_occupational_exposure(
    result: "ExposureResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-task contributions to the daily exposure level (ISO 9612).

    One bar per task (its contribution to ``LEX,8h``), with the combined
    ``LEX,8h`` and the one-sided upper limit ``LEX,8h + U`` as horizontal
    lines.

    :param result: An
        :class:`~phonometry.occupational_exposure.ExposureResult` from the
        task-based strategy (the one that carries per-task contributions).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the task :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    :raises ValueError: If the result carries no per-task contributions.
    """
    if not result.tasks:
        raise ValueError(
            "plot() needs per-task contributions; only task_based_exposure() "
            "results carry them (the job/full-day strategies do not)."
        )
    ax = ax if ax is not None else _new_axes()
    contributions = [t.lex_8h_contribution for t in result.tasks]
    labels = [t.label for t in result.tasks]
    positions = np.arange(len(contributions), dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(positions, contributions, **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45, ha="right")

    ax.axhline(result.lex_8h, color=_C_REFERENCE, ls="--",
               label=f"$L_{{EX,8h}}$ = {result.lex_8h:.1f} dB")
    ax.axhline(result.upper_limit, color=_C_MUTED, ls=":",
               label=f"$L_{{EX,8h}} + U$ = {result.upper_limit:.1f} dB")
    top = max(result.upper_limit, max(contributions))
    bottom = min(0.0, min(contributions))
    ax.set_ylim(bottom * 1.12 if bottom < 0.0 else 0.0, top * 1.12)
    ax.set_ylabel("A-weighted level [dB]")
    ax.set_title(
        f"ISO 9612 daily noise exposure — $L_{{EX,8h}}$ = "
        f"{result.lex_8h:.1f} dB (U = {result.expanded_uncertainty:.1f} dB)"
    )
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax
