#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the environmental domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _LEGEND_UPPER_RIGHT,
    _band_axis,
    _freq_axis,
    _new_axes,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from ..environmental.outdoor_propagation import OutdoorAttenuation
    from ..environmental.ground_barriers import (
        BarrierInsertionLoss,
        SphericalGroundResult,
    )
    from ..environmental.atmospheric_refraction import (
        AtmosphericPEResult,
        AtmosphericRayResult,
        EffectiveSoundSpeedProfile,
    )
    from ..environmental.measurement import TonalAssessmentResult
    from ..environmental.impulse_prominence import ImpulseProminenceResult
    from ..environmental.wind_turbine_noise import WindTurbineTonalityResult

#: Axis labels shared by the atmospheric-refraction figures (height on the
#: vertical axis, horizontal range on the x-axis).
_LABEL_HEIGHT_M = "Height [m]"
_LABEL_RANGE_M = "Range [m]"


def plot_wind_turbine_tonality(
    result: "WindTurbineTonalityResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Narrowband spectrum with the critical band, masking level and the tone.

    :param result: A :class:`~phonometry.wind_turbine_noise.WindTurbineTonalityResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the spectrum ``plot`` call.
    :return: The axes.
    """
    from ..environmental.wind_turbine_noise import _critical_band_edges

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    levels = np.asarray(result.levels, dtype=np.float64)
    fc = result.tone_frequency
    lo, hi = _critical_band_edges(fc)
    ax.plot(freqs, levels, **{"color": _C_PRIMARY, "lw": 1.0, "label": "Narrowband spectrum", **kwargs})
    ax.axvspan(lo, hi, color=_C_TERTIARY, alpha=0.12, label="Critical band")
    ax.axhline(result.masking_level, color=_C_MUTED, ls="--", lw=1.0,
               label=f"Masking level ({result.masking_level:.1f} dB)")
    ax.plot([fc], [result.tone_level], "o", color=_C_REFERENCE,
            label=f"Tone ({result.tone_level:.1f} dB)")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Level [dB]")
    ax.set_title(f"IEC 61400-11 tonal audibility ΔLₐ = {result.tonal_audibility:.1f} dB")
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    return ax

def plot_impulse_prominence(
    result: "ImpulseProminenceResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Adjustment curve ``KI(P)`` with the candidate impulses marked.

    :param result: An :class:`~phonometry.impulse_prominence.ImpulseProminenceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the impulses ``scatter``.
    :return: The axes.
    """
    from ..environmental.impulse_prominence import ADJUSTMENT_THRESHOLD, impulse_adjustment

    ax = ax if ax is not None else _new_axes()
    per = np.asarray(result.per_impulse, dtype=np.float64)
    per_max = float(per.max()) if per.size else 0.0
    p_max = max(per_max, result.prominence, 15.0) + 1.0
    grid = np.linspace(0.0, p_max, 200)
    ax.plot(grid, impulse_adjustment(grid), color=_C_PRIMARY,
            label=r"$K_I = 1.8\,(P-5)$")
    ax.axvline(ADJUSTMENT_THRESHOLD, color=_C_MUTED, ls=":",
               label=f"threshold $P = {ADJUSTMENT_THRESHOLD:g}$")

    kwargs.setdefault("color", _C_PRIMARY_LIGHT)
    kwargs.setdefault("zorder", 3)
    ax.scatter(per, impulse_adjustment(per), label="Impulses", **kwargs)
    ax.scatter([result.prominence], [result.adjustment], color=_C_REFERENCE,
               zorder=4, s=90, marker="*",
               label=f"Governing  P = {result.prominence:.2f},  "
                     f"$K_I$ = {result.adjustment:.1f} dB")
    ax.set_xlabel("Predicted prominence $P$")
    ax.set_ylabel("Adjustment $K_I$ [dB]")
    ax.set_title("NT ACOU 112 — impulse adjustment to $L_{Aeq}$")
    ax.set_ylim(bottom=0.0)
    ax.legend(loc="upper left", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax

def plot_tonal_adjustment(
    result: "TonalAssessmentResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Tonal adjustment curve ``Kt(ΔLta)`` with the assessed tone marked.

    :param result: A
        :class:`~phonometry.environmental_measurement.TonalAssessmentResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the assessed-tone ``scatter``.
    :return: The axes.
    """
    from ..environmental.measurement import tonal_adjustment

    ax = ax if ax is not None else _new_axes()
    top = max(result.audibility, 12.0) + 1.0
    grid = np.linspace(0.0, top, 200)
    curve = np.array([tonal_adjustment(d) for d in grid], dtype=np.float64)
    ax.plot(grid, curve, color=_C_PRIMARY, label=r"$K_t(\Delta L_{ta})$")
    ax.axvline(4.0, color=_C_MUTED, ls=":", label=r"knees $\Delta L_{ta}=4,\,10$ dB")
    ax.axvline(10.0, color=_C_MUTED, ls=":")

    kwargs.setdefault("color", _C_REFERENCE)
    kwargs.setdefault("zorder", 4)
    kwargs.setdefault("s", 90)
    kwargs.setdefault("marker", "*")
    ax.scatter([result.audibility], [result.adjustment],
               label=rf"$\Delta L_{{ta}}$ = {result.audibility:.1f} dB,  "
                     rf"$K_t$ = {result.adjustment:.1f} dB", **kwargs)
    ax.set_xlabel(r"Tonal audibility $\Delta L_{ta}$ [dB]")
    ax.set_ylabel("Tonal adjustment $K_t$ [dB]")
    ax.set_title("ISO 1996-2 tonal adjustment")
    ax.set_ylim(bottom=0.0)
    ax.legend(loc="upper left", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax

def plot_outdoor_attenuation(
    result: "OutdoorAttenuation", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Stacked per-band attenuation terms with the total overlaid (ISO 9613-2).

    The divergence, atmospheric, ground and barrier terms are stacked per
    octave band on separate positive and negative baselines (the ground
    effect can be a net *gain*), and the total attenuation ``A`` is drawn
    as the primary marker line on top.

    :param result: An
        :class:`~phonometry.outdoor_propagation.OutdoorAttenuation`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the total-attenuation ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    positions = _band_axis(ax, freqs)
    n = freqs.size

    # Separate positive and negative cumulative baselines so a negative term
    # stacks below zero instead of being drawn on top of the previous bars;
    # the signed heights sum to a_total.
    pos_bottom = np.zeros(n)
    neg_bottom = np.zeros(n)
    terms = (
        (result.a_div, _C_PRIMARY, "$A_{div}$ — divergence"),
        (result.a_atm, _C_TERTIARY, "$A_{atm}$ — atmospheric"),
        (result.a_gr, _C_QUATERNARY, "$A_{gr}$ — ground"),
        (result.a_bar, _C_SECONDARY, "$A_{bar}$ — barrier"),
    )
    for values, color, label in terms:
        term = np.asarray(values, dtype=np.float64)
        bottom = np.where(term >= 0.0, pos_bottom, neg_bottom)
        ax.bar(positions, term, bottom=bottom, color=color, label=label)
        pos_bottom += np.maximum(term, 0.0)
        neg_bottom += np.minimum(term, 0.0)

    kwargs.setdefault("color", _C_REFERENCE)
    kwargs.setdefault("marker", "D")
    kwargs.setdefault("label", "$A$ — total")
    ax.plot(positions, np.asarray(result.a_total, dtype=np.float64),
            zorder=4, **kwargs)
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.set_ylabel("Attenuation A [dB]")
    ax.set_title("ISO 9613-2 attenuation breakdown")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


def plot_spherical_ground(
    result: "SphericalGroundResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Excess attenuation (level re free field) of the spherical-wave ground effect.

    Draws the relative sound level ``dL`` versus frequency with the ``+6 dB``
    hard-ground enhancement ceiling and the ``0 dB`` free-field reference, so the
    ground-effect dip and any surface-wave enhancement are both visible.

    :param result: A
        :class:`~phonometry.environmental.ground_barriers.SphericalGroundResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the ``dL`` ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    d_l = np.asarray(result.excess_attenuation, dtype=np.float64)
    ax.plot(freqs, d_l, **{"color": _C_PRIMARY, "lw": 1.4, "marker": "o",
                           "ms": 3.0, "label": "Excess attenuation $\\Delta L$",
                           **kwargs})
    ax.axhline(0.0, color=_C_MUTED, lw=0.8, label="Free field (0 dB)")
    ax.axhline(6.0, color=_C_REFERENCE, ls="--", lw=0.9,
               label="Hard-ground limit (+6 dB)")
    _freq_axis(ax, freqs)
    ax.set_ylabel("Level re free field [dB]")
    ax.set_title("Spherical-wave ground effect (Weyl-Van der Pol)")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_barrier_insertion_loss(
    result: "BarrierInsertionLoss", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Barrier insertion loss versus frequency.

    :param result: A
        :class:`~phonometry.environmental.ground_barriers.BarrierInsertionLoss`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the insertion-loss ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    il = np.asarray(result.insertion_loss, dtype=np.float64)
    label = f"Insertion loss ({result.method}{', ground' if result.ground else ''})"
    ax.plot(freqs, il, **{"color": _C_SECONDARY, "lw": 1.4, "marker": "s",
                          "ms": 3.0, "label": label, **kwargs})
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.axhline(5.0, color=_C_MUTED, ls=":", lw=0.9,
               label="Grazing limit (5 dB)")
    _freq_axis(ax, freqs)
    ax.set_ylabel("Insertion loss [dB]")
    ax.set_title("Barrier insertion loss")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_sound_speed_profile(
    profile: "EffectiveSoundSpeedProfile", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Effective sound-speed profile ``c_eff(z)`` (height on the vertical axis).

    :param profile: An
        :class:`~phonometry.environmental.atmospheric_refraction.EffectiveSoundSpeedProfile`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the profile ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    z = np.asarray(profile.heights, dtype=np.float64)
    c = np.asarray(profile.sound_speeds, dtype=np.float64)
    label = profile.description or "c_eff(z)"
    ax.plot(c, z, **{"color": _C_PRIMARY, "lw": 1.4, "label": label, **kwargs})
    ax.set_xlabel("Effective sound speed [m/s]")
    ax.set_ylabel(_LABEL_HEIGHT_M)
    ax.set_title("Effective sound-speed profile")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    return ax


def plot_atmospheric_rays(
    result: "AtmosphericRayResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Curved sound-ray paths over the ground (height on the vertical axis).

    :param result: An
        :class:`~phonometry.environmental.atmospheric_refraction.AtmosphericRayResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to each ray ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    r = np.asarray(result.ranges, dtype=np.float64)
    z = np.asarray(result.heights, dtype=np.float64)
    for i in range(r.shape[0]):
        ax.plot(r[i], z[i], **{"color": _C_PRIMARY, "lw": 0.7, "alpha": 0.7, **kwargs})
    ax.plot([0.0], [result.source_height], "o", color=_C_REFERENCE, label="Source")
    ax.axhline(0.0, color=_C_MUTED, lw=1.0)
    ax.set_xlabel(_LABEL_RANGE_M)
    ax.set_ylabel(_LABEL_HEIGHT_M)
    ax.set_ylim(bottom=0.0)
    ax.set_title("Atmospheric ray paths")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize="small")
    return ax


def plot_atmospheric_pe(
    result: "AtmosphericPEResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Parabolic-equation relative-level field over the range-height plane.

    The field is drawn as a single raster image (``imshow``): per-cell vector
    quads are avoided so the figure stays light and free of moire (the repo's
    pcolormesh-in-SVG policy).

    :param result: An
        :class:`~phonometry.environmental.atmospheric_refraction.AtmosphericPEResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to ``imshow``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    r = np.asarray(result.ranges, dtype=np.float64)
    z = np.asarray(result.heights, dtype=np.float64)
    dl = np.asarray(result.relative_level, dtype=np.float64)
    finite = dl[np.isfinite(dl)]
    vmax = float(np.percentile(finite, 99)) if finite.size else 6.0
    vmax = max(vmax, 6.0)
    dl = np.where(np.isfinite(dl), dl, np.nan)
    img = ax.imshow(
        dl,
        **{
            "cmap": "RdBu_r",
            "vmin": -30.0,
            "vmax": vmax,
            "aspect": "auto",
            "origin": "lower",
            "interpolation": "bilinear",
            "extent": (float(r[0]), float(r[-1]), float(z[0]), float(z[-1])),
            **kwargs,
        },
    )
    ax.figure.colorbar(img, ax=ax, label="Level re free field [dB]")
    ax.plot([0.0], [result.source_height], "o", color="k", ms=4.0, label="Source")
    ax.set_xlabel(_LABEL_RANGE_M)
    ax.set_ylabel(_LABEL_HEIGHT_M)
    ax.set_title(f"GFPE relative sound level ({result.frequency:.0f} Hz)")
    ax.legend(loc="upper right", fontsize="small")
    return ax
