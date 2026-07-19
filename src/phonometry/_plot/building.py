#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the building domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _annotate_impact_500,
    _band_axis,
    _facade_x_axis,
    _format_freq,
    _freq_axis,
    _new_axes,
    _plot_band_level_bars,
    _plot_insulation_bands,
    _plot_rating,
    _require_rating_curve,
    format_frequency_axis,
)

if TYPE_CHECKING:
    from ..building.insulation import (
        AirborneInsulationResult,
        FacadeInsulationResult,
        ImpactInsulationResult,
        ImpactRatingResult,
        WeightedRatingResult,
    )
    from matplotlib.axes import Axes
    from ..building.building_prediction import AirbornePredictionResult, ImpactPredictionResult
    from ..building.building_uncertainty import BandUncertainty
    from ..building.facade_prediction import FacadePredictionResult, RadiatedPowerResult
    from ..building.flanking_transmission import VibrationReductionResult
    from ..building.floor_covering_improvement import FloorCoveringImprovementResult
    from ..building.installed_structure_borne import InstalledSourceResult
    from ..building.structure_borne_power import StructureBornePowerResult

def plot_weighted_rating(
    result: "WeightedRatingResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Airborne rating curve vs shifted reference (ISO 717-1).

    :param result: A :class:`~phonometry.insulation.WeightedRatingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    _require_rating_curve(result)
    return _plot_rating(
        np.asarray(result.band_centers, dtype=np.float64),
        np.asarray(result.measured, dtype=np.float64),
        np.asarray(result.shifted_reference, dtype=np.float64),
        impact=False,
        title=(
            f"ISO 717-1 Rw (C={result.c:+d}; Ctr={result.ctr:+d}) = "
            f"{result.rating} dB  (Sigma unfav. = {result.unfavourable_sum:.1f} dB)"
        ),
        ylabel="Sound reduction index [dB]",
        ax=ax,
        **kwargs,
    )

def plot_impact_rating(
    result: "ImpactRatingResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Impact rating curve vs shifted reference (ISO 717-2).

    The drawn shifted-reference curve is the normatively honest ``ref -
    shift``; for octave-band data the rating is that curve read at 500 Hz
    *minus 5 dB* (Clause 4.3.2), so the plot marks the 500 Hz read value on
    the (undistorted) curve and annotates the -5 dB reduction rather than
    pulling the curve down to the rating.

    :param result: An :class:`~phonometry.insulation.ImpactRatingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    _require_rating_curve(result)
    band_centers = np.asarray(result.band_centers, dtype=np.float64)
    reference = np.asarray(result.shifted_reference, dtype=np.float64)
    ax = _plot_rating(
        band_centers,
        np.asarray(result.measured, dtype=np.float64),
        reference,
        impact=True,
        # The rated quantity depends on the input (Ln,w, L'n,w or L'nT,w);
        # the dataclass does not carry which, so the figure uses the neutral
        # "impact rating" label rather than hard-coding one specific symbol.
        title=(
            f"ISO 717-2 impact rating (CI={result.ci:+d}) = {result.rating} dB"
            f"  (Sigma unfav. = {result.unfavourable_sum:.1f} dB)"
        ),
        ylabel="Impact sound pressure level [dB]",
        ax=ax,
        **kwargs,
    )
    _annotate_impact_500(ax, band_centers, reference, int(result.rating))
    return ax

def plot_facade_insulation(
    result: "FacadeInsulationResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-band façade sound-insulation profile (ISO 16283-3).

    Draws the standardized level difference ``D2m,nT`` first, then the
    other available quantities (``D2m``, ``D2m,n``, ``R'``) against
    frequency. Works for
    :class:`~phonometry.insulation.FacadeInsulationResult`.

    :param result: A façade result exposing ``d_2m``, ``d_2m_nt``,
        ``d_2m_n``, ``r_prime`` and (optionally) ``frequencies``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the primary ``D2m,nT`` curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    dnt = np.asarray(result.d_2m_nt, dtype=np.float64)
    n = dnt.size
    x = _facade_x_axis(ax, getattr(result, "frequencies", None), n)

    # D2m,nT first so it is lines[0]; other quantities follow when present.
    curves = [("$D_{2m,nT}$", dnt)]
    curves.append(("$D_{2m}$", np.asarray(result.d_2m, dtype=np.float64)))
    if result.d_2m_n is not None:
        curves.append(("$D_{2m,n}$", np.asarray(result.d_2m_n, dtype=np.float64)))
    if result.r_prime is not None:
        curves.append(("$R'$", np.asarray(result.r_prime, dtype=np.float64)))
    # Forward user kwargs to the primary D2m,nT curve only, so styling kwargs
    # (label=, color=) neither collide with the per-curve labels nor make the
    # companion curves indistinguishable.
    for index, (label, y) in enumerate(curves):
        opts: dict[str, Any] = {"label": label}
        if index == 0:
            opts.update(kwargs)
        ax.plot(x, y, "o-", **opts)

    ax.set_ylabel("Level difference / reduction index [dB]")
    ax.set_title("Façade sound insulation (ISO 16283-3)")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax

def plot_facade_prediction(
    result: "FacadePredictionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Predicted façade insulation profile (EN 12354-3:2000).

    Draws the per-element partial indices ``Rp = -10 lg τ`` as thin dashed
    lines, then the façade apparent reduction ``R'`` and the standardized
    level difference ``D2m,nT`` as bold curves, against frequency. Works for
    :class:`~phonometry.facade_prediction.FacadePredictionResult`.

    :param result: A façade prediction result exposing ``r_prime``,
        ``d_2m_nt``, ``element_r`` and (optionally) ``frequencies``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the primary ``R'`` curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    r_prime = np.asarray(result.r_prime, dtype=np.float64)
    n = r_prime.size
    x = _facade_x_axis(ax, result.frequencies, n)

    for name, rp in result.element_r.items():
        ax.plot(x, np.asarray(rp, dtype=np.float64), "--", lw=0.9, alpha=0.6, label=name)

    opts: dict[str, Any] = {"label": "$R'$", "color": "black", "lw": 2.0}
    opts.update(kwargs)
    ax.plot(x, r_prime, "o-", **opts)
    ax.plot(
        x,
        np.asarray(result.d_2m_nt, dtype=np.float64),
        "s-",
        color="tab:blue",
        lw=2.0,
        label="$D_{2m,nT}$",
    )

    ax.set_ylabel("Reduction index / level difference [dB]")
    ax.set_title("Façade insulation prediction (EN 12354-3)")
    ax.legend(loc="best", fontsize="small", ncol=2)
    ax.grid(True, alpha=0.3)
    return ax

def plot_radiated_power(
    result: "RadiatedPowerResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Radiated sound power level ``LW`` per band (EN 12354-4:2000).

    Draws the segment radiated power level as bars, annotating the A-weighted
    single number when available. Works for
    :class:`~phonometry.facade_prediction.RadiatedPowerResult`.

    :param result: A :class:`~phonometry.facade_prediction.RadiatedPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the ``bar`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    l_w = np.asarray(result.l_w, dtype=np.float64)
    n = l_w.size
    positions = np.arange(n, dtype=np.float64)
    if result.frequencies is None:
        labels = [f"Band {i + 1}" for i in range(n)]
    else:
        labels = [_format_freq(f) for f in np.asarray(result.frequencies, dtype=np.float64)]

    opts: dict[str, Any] = {"color": "tab:red", "alpha": 0.8, "label": "$L_W$"}
    opts.update(kwargs)
    ax.bar(positions, l_w, **opts)
    _band_axis(ax, labels, xlabel="Frequency [Hz]")

    if result.l_w_dba is not None:
        ax.axhline(
            result.l_w_dba,
            color="black",
            ls="--",
            lw=1.2,
            label=f"$L_{{WA}}$ = {result.l_w_dba:.1f} dB(A)",
        )
    ax.set_ylabel("Radiated sound power level [dB]")
    ax.set_title("Radiated sound power (EN 12354-4)")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax

def plot_vibration_reduction(
    result: "VibrationReductionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Vibration reduction index ``Kij`` versus frequency (ISO 10848).

    Draws the per-band ``Kij`` and, when available, a dashed line at the
    single-number mean ``K̄ij`` (200-1250 Hz, Annex A). Falls back to a
    band-index axis when the result carries no frequencies.

    :param result: A
        :class:`~phonometry.flanking_transmission.VibrationReductionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the ``Kij`` curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    k_ij = np.asarray(result.k_ij, dtype=np.float64)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "$K_{ij}$")
    if result.frequencies is not None:
        freqs = np.asarray(result.frequencies, dtype=np.float64)
        ax.plot(freqs, k_ij, **kwargs)
        _freq_axis(ax, freqs)
    else:
        ax.plot(np.arange(k_ij.size), k_ij, **kwargs)
        ax.set_xlabel("Band index")
    if result.single_number is not None:
        ax.axhline(
            result.single_number,
            color=_C_REFERENCE,
            ls="--",
            lw=1.0,
            label=rf"$\overline{{K}}_{{ij}}$ = {result.single_number:.1f} dB",
        )
    ax.set_ylabel("Vibration reduction index $K_{ij}$ [dB]")
    ax.set_title("Vibration reduction index (ISO 10848)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    return ax

def plot_structure_borne_power(
    result: "StructureBornePowerResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Characteristic structure-borne sound power level per band (EN 15657).

    :param result: A :class:`~phonometry.structure_borne_power.StructureBornePowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the bar ``plot``.
    :return: The axes.
    """
    return _plot_band_level_bars(
        ax, result.power_level, result.frequencies, result.total_level,
        ylabel=r"Structure-borne power level $L_{Ws}$ [dB re 1 pW]",
        title="EN 15657 characteristic structure-borne sound power", **kwargs,
    )

def plot_installed_structure_borne(
    result: "InstalledSourceResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-path and total normalised structure-borne SPL (EN 12354-5).

    :param result: An :class:`~phonometry.installed_structure_borne.InstalledSourceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the total-level ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    paths = np.atleast_2d(np.asarray(result.path_levels, dtype=np.float64))
    total = np.atleast_1d(np.asarray(result.total_level, dtype=np.float64))
    n_bands = total.size
    if result.frequencies is not None:
        x = np.asarray(result.frequencies, dtype=np.float64)
        ax.set_xscale("log")
        ax.set_xlabel("Frequency [Hz]")
    else:
        x = np.arange(1, n_bands + 1, dtype=np.float64)
        ax.set_xlabel("Band")
    for k, path in enumerate(paths):
        ax.plot(x, path, color=_C_MUTED, lw=1.0, ls=":", marker=".",
                label="paths" if k == 0 else None)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("lw", 2.2)
    ax.plot(x, total, label=r"total $L_{n,s}$", **kwargs)
    ax.set_ylabel(r"Normalised SPL $L_{n,s}$ [dB]")
    ax.set_title("EN 12354-5 installed structure-borne sound")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    if result.frequencies is not None:
        format_frequency_axis(ax, float(x.min()), float(x.max()))
    return ax

def plot_airborne_prediction(
    result: "AirbornePredictionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-path shares of the transmitted energy (EN 12354-1).

    One bar per transmission path (direct plus flanking), sorted by its
    share of the total transmitted sound energy, largest first.

    :param result: An
        :class:`~phonometry.building_prediction.AirbornePredictionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the path :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    contribs = sorted(result.paths, key=lambda c: c.fraction, reverse=True)
    shares = [100.0 * c.fraction for c in contribs]
    positions = np.arange(len(shares), dtype=np.float64)
    kwargs.setdefault(
        "color", [_C_PRIMARY if c.kind == "Dd" else _C_MUTED for c in contribs]
    )
    ax.bar(positions, shares, **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels([c.label for c in contribs], rotation=45, ha="right")
    ax.set_xlabel("Transmission path")
    ax.set_ylabel("Share of transmitted energy [%]")
    ax.set_title(
        f"EN 12354-1 flanking prediction — R'w = {result.r_prime_w:.1f} dB "
        f"(RDd,w = {result.r_direct_w:.1f} dB)"
    )
    ax.grid(True, axis="y", alpha=0.3)
    return ax

def plot_impact_prediction(
    result: "ImpactPredictionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Terms of the apparent impact-level prediction (EN 12354-2).

    Bars for the Formula 21 terms — the bare-floor equivalent level, the
    covering improvement, the flanking correction — and the resulting
    apparent level ``L'n,w = Ln,w,eq - DLw + K``.

    :param result: An
        :class:`~phonometry.building_prediction.ImpactPredictionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the term :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    labels = ("$L_{n,w,eq}$", r"$-\Delta L_w$", "$+K$", "$L'_{n,w}$")
    values = (
        result.ln_w_eq,
        -result.delta_l_w,
        result.k_correction,
        result.l_prime_n_w,
    )
    positions = np.arange(len(values), dtype=np.float64)
    kwargs.setdefault("color", [_C_MUTED, _C_TERTIARY, _C_SECONDARY, _C_PRIMARY])
    ax.bar(positions, values, **kwargs)
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Level / correction [dB]")
    ax.set_title(
        f"EN 12354-2 impact prediction — L'n,w = {result.l_prime_n_w:.1f} dB"
    )
    ax.grid(True, axis="y", alpha=0.3)
    return ax

def plot_airborne_insulation(
    result: "AirborneInsulationResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-band airborne insulation quantities (ISO 16283-1).

    Draws the standardized level difference ``DnT`` first (the primary
    curve), then the level difference ``D`` and, when available, the
    apparent sound reduction index ``R'``.

    :param result: An :class:`~phonometry.insulation.AirborneInsulationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the primary ``DnT`` curve ``plot`` call.
    :return: The axes.
    """
    curves = [
        ("$D_{nT}$", np.asarray(result.dnt, dtype=np.float64)),
        ("$D$", np.asarray(result.d, dtype=np.float64)),
    ]
    if result.r_prime is not None:
        curves.append(("$R'$", np.asarray(result.r_prime, dtype=np.float64)))
    return _plot_insulation_bands(
        curves,
        ylabel="Level difference / reduction index [dB]",
        title="Airborne sound insulation (ISO 16283-1)",
        ax=ax,
        **kwargs,
    )

def plot_impact_insulation(
    result: "ImpactInsulationResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-band impact sound pressure levels (ISO 16283-2).

    Draws the standardized level ``L'nT`` first (the primary curve) and,
    when available, the normalized level ``L'n``.

    :param result: An :class:`~phonometry.insulation.ImpactInsulationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the primary ``L'nT`` curve ``plot`` call.
    :return: The axes.
    """
    curves = [("$L'_{nT}$", np.asarray(result.l_n_t, dtype=np.float64))]
    if result.l_n is not None:
        curves.append(("$L'_n$", np.asarray(result.l_n, dtype=np.float64)))
    return _plot_insulation_bands(
        curves,
        ylabel="Impact sound pressure level [dB]",
        title="Impact sound insulation (ISO 16283-2)",
        ax=ax,
        **kwargs,
    )

def plot_band_uncertainty(
    result: "BandUncertainty", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-band standard uncertainty of an insulation quantity (ISO 12999-1).

    :param result: A
        :class:`~phonometry.building_uncertainty.BandUncertainty`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the uncertainty curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs, u = result.to_arrays()
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    ax.plot(freqs, u, **kwargs)
    _freq_axis(ax, freqs)
    ax.set_ylabel("Standard uncertainty u [dB]")
    ax.set_ylim(bottom=0.0)
    quantity = "sigma_R95 upper limit" if result.upper_limit else "u"
    ax.set_title(
        f"ISO 12999-1 band uncertainty ({quantity}) — "
        f"{result.measurand}, situation {result.situation}"
    )
    ax.grid(True, which="both", alpha=0.3)
    return ax

def plot_floor_covering_improvement(
    result: "FloorCoveringImprovementResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Impact-sound improvement spectrum ΔL of a floor covering (ISO 16251-1).

    :param result: A
        :class:`~phonometry.floor_covering_improvement.FloorCoveringImprovementResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the improvement-curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs, dl = result.frequencies, result.improvement
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    ax.plot(freqs, dl, **kwargs)
    # Mark bands at the limit of measurement (reported as > delta-L).
    if result.limited.size and bool(np.any(result.limited)):
        ax.plot(
            freqs[result.limited], dl[result.limited], ls="", marker="v",
            color=_C_SECONDARY, ms=9, mfc="none", mew=1.6, zorder=5,
            label="limit of measurement (> delta-L)",
        )
    _freq_axis(ax, freqs)
    ax.set_ylabel("Improvement of impact sound insulation delta-L [dB]")
    ax.set_ylim(bottom=0.0)
    title = "ISO 16251-1 Floor-Covering Impact Sound Improvement"
    if result.delta_lw is not None:
        title += f"  (delta-Lw = {result.delta_lw} dB)"
    ax.set_title(title)
    ax.grid(True, which="both", alpha=0.3)
    if ax.get_legend_handles_labels()[0]:
        ax.legend()
    return ax
