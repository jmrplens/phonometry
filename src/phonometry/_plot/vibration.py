#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the vibration domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _band_axis,
    _new_axes,
    format_frequency_axis,
)

if TYPE_CHECKING:
    from ..vibration.human_vibration import (
        DailyVibrationExposure,
        WeightedSpectrum,
        WeightingResponse,
    )
    from matplotlib.axes import Axes
    from ..vibration.mechanical_mobility import MobilityResult
    from ..vibration.transfer_stiffness import TransferStiffnessResult
    from ..vibration.multiple_shock_vibration import MultipleShockResult
    from ..vibration.radiation_efficiency import RadiationEfficiencyResult

def plot_vibration_weighting(
    result: "WeightingResponse", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Frequency-weighting factor (dB) versus frequency (ISO 8041-1).

    :param result: A
        :class:`~phonometry.human_vibration.WeightingResponse` exposing
        ``name``, ``frequencies`` and ``magnitude_db``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the weighting curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    mag_db = np.asarray(result.magnitude_db, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.semilogx(freqs, mag_db, **kwargs)
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Weighting factor [dB]")
    ax.set_title(f"Frequency weighting {result.name} (ISO 8041-1)")
    ax.grid(True, which="both", alpha=0.3)
    format_frequency_axis(ax, float(freqs.min()), float(freqs.max()))
    return ax

def plot_weighted_spectrum(
    result: "WeightedSpectrum", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Unweighted vs weighted one-third-octave acceleration spectrum.

    Draws the measured band accelerations and, overlaid, the weighted band
    contributions ``W_i*a_i``; the overall ``a_w`` is annotated in the title.

    :param result: A
        :class:`~phonometry.human_vibration.WeightedSpectrum` exposing
        ``frequencies``, ``band_accelerations``, ``weighted``, ``overall`` and
        ``weighting_name``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the weighted (primary) bars.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    raw = np.asarray(result.band_accelerations, dtype=np.float64)
    weighted = np.asarray(result.weighted, dtype=np.float64)
    positions = _band_axis(ax, freqs)
    width = 0.4
    # The weighted bars are the primary artist; forward user kwargs there.
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(
        positions - width / 2, raw, width, color=_C_MUTED, label="Unweighted $a_i$"
    )
    ax.bar(
        positions + width / 2,
        weighted,
        width,
        label=f"Weighted $W_i a_i$ ({result.weighting_name})",
        **kwargs,
    )
    ax.set_ylabel(r"r.m.s. acceleration [m/s$^2$]")
    # Wh is the hand-arm weighting of ISO 5349-1; the others (Wk, Wd, Wm...)
    # are the whole-body weightings of ISO 2631.
    designation = "ISO 5349-1" if str(result.weighting_name) == "Wh" else "ISO 2631"
    ax.set_title(
        f"{designation} weighted acceleration spectrum  "
        f"($a_w$ = {float(result.overall):.3f} " r"m/s$^2$)"
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax

def plot_daily_exposure(
    result: "DailyVibrationExposure", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Partial daily exposures against the EAV / ELV (Directive 2002/44/EC).

    Draws one bar per operation (its partial exposure ``A_i(8)``), a combined
    ``A(8)`` bar, and the exposure action and limit value as horizontal lines.

    :param result: A
        :class:`~phonometry.human_vibration.DailyVibrationExposure` exposing
        ``labels``, ``partials``, ``a8`` and ``assessment``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the exposure :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    partials = np.asarray(result.partials, dtype=np.float64)
    labels = [*result.labels, "A(8)"]
    values = [*partials.tolist(), float(result.a8)]
    positions = np.arange(len(values), dtype=np.float64)
    colors = [_C_MUTED] * partials.size + [_C_PRIMARY]
    kwargs.setdefault("color", colors)
    ax.bar(positions, values, **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel(r"Vibration exposure A(8) [m/s$^2$]")

    assessment = result.assessment
    eav = float(assessment.action_value)
    elv = float(assessment.limit_value)
    ax.axhline(eav, color=_C_SECONDARY, ls="--", label=f"EAV = {eav:g}")
    ax.axhline(elv, color=_C_REFERENCE, ls="--", label=f"ELV = {elv:g}")
    top = max(elv, float(np.max(values))) * 1.15
    ax.set_ylim(0.0, top)
    kind = str(assessment.kind).upper()
    ax.set_title(
        f"Directive 2002/44/EC daily {kind} exposure  "
        f"(A(8) = {float(result.a8):.2f} " rf"m/s$^2$, {assessment.zone})"
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax

def plot_mobility(
    result: "MobilityResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Mobility magnitude ``|Y(f)|`` on log-log axes (ISO 7626-1).

    :param result: A :class:`~phonometry.mechanical_mobility.MobilityResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the magnitude ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    mag = np.asarray(result.magnitude, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    label = "driving-point mobility" if result.driving_point else "transfer mobility"
    ax.loglog(freq, mag, label=label, **kwargs)
    # Mark the mobility peak (a resonance for a driving-point FRF).
    peak = int(np.argmax(mag))
    ax.plot(freq[peak], mag[peak], "o", color=_C_REFERENCE, zorder=5,
            label=f"peak at {freq[peak]:.1f} Hz")
    format_frequency_axis(ax, float(freq.min()), float(freq.max()))
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Mobility $|Y|$ [m/(N·s)]")
    ax.set_title("ISO 7626-1 mechanical mobility")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax

def plot_transfer_stiffness(
    result: "TransferStiffnessResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Dynamic transfer stiffness level ``L_k(f)`` on a log-frequency axis.

    :param result: A :class:`~phonometry.transfer_stiffness.TransferStiffnessResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the level ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    level = np.asarray(result.level, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.semilogx(freq, level, label=r"$L_k = 20\,\lg(|k_{2,1}|/k_0)$", **kwargs)
    format_frequency_axis(ax, float(freq.min()), float(freq.max()))
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel(r"Transfer stiffness level $L_k$ [dB re 1 N/m]")
    ax.set_title("ISO 10846 dynamic transfer stiffness")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax

def plot_radiation_efficiency(
    result: "RadiationEfficiencyResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Radiation efficiency ``sigma(f)`` on log-log axes (Hopkins 2.9.4).

    :param result: A
        :class:`~phonometry.vibration.radiation_efficiency.RadiationEfficiencyResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the ``sigma`` curve ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    sigma = np.asarray(result.radiation_efficiency, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("markersize", 3)
    ax.loglog(freq, sigma, label=r"$\sigma(f)$", **kwargs)
    ax.axhline(1.0, color=_C_MUTED, ls=":", lw=0.9, label=r"$\sigma = 1$")
    ax.axvline(
        result.critical_frequency,
        color=_C_REFERENCE,
        ls="--",
        lw=1.0,
        label=f"$f_c$ = {result.critical_frequency:.0f} Hz",
    )
    format_frequency_axis(ax, float(freq.min()), float(freq.max()))
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel(r"Radiation efficiency $\sigma$")
    ax.set_title("Plate radiation efficiency (Leppington / Maidanik)")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_multiple_shock(
    result: "MultipleShockResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Injury-probability curve ``P(R)`` with this assessment's ``R`` marked.

    :param result: A :class:`~phonometry.multiple_shock_vibration.MultipleShockResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the ``R`` marker ``scatter``.
    :return: The axes.
    """
    from ..vibration.multiple_shock_vibration import injury_probability

    ax = ax if ax is not None else _new_axes()
    r10, r50, r90 = result.risk_thresholds
    r_max = max(result.risk, r90) * 1.3
    grid = np.linspace(0.0, r_max, 240)
    prob = np.asarray(injury_probability(grid, sex=result.sex), dtype=np.float64)
    ax.plot(grid, 100.0 * prob, color=_C_PRIMARY,
            label=r"$\Pi(R) = 1 - e^{-(R/\alpha)^{\beta}}$")
    for level, r_val in zip((10, 50, 90), (r10, r50, r90)):
        ax.axhline(level, color=_C_MUTED, ls=":", lw=0.8)
        ax.plot([r_val, r_val], [0.0, level], color=_C_MUTED, ls=":", lw=0.8)

    kwargs.setdefault("color", _C_REFERENCE)
    kwargs.setdefault("zorder", 4)
    kwargs.setdefault("s", 90)
    ax.scatter([result.risk], [100.0 * result.probability],
               label=f"$R$ = {result.risk:.2f},  $\\Pi$ = "
                     f"{100.0 * result.probability:.0f} %", **kwargs)
    ax.set_xlabel("Stress variable $R$")
    ax.set_ylabel("Probability of lumbar injury [%]")
    ax.set_title(f"ISO 2631-5 injury probability — {result.sex}")
    ax.set_xlim(left=0.0)
    ax.set_ylim(0.0, 100.0)
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax
