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

#: Spanish translations of the fixed strings rendered by the vibration
#: ``.plot()`` renderers, keyed by their verbatim English text. ``_t``
#: returns the English key unchanged for any language other than ``"es"``,
#: so the English output is byte-for-byte identical to the pre-i18n
#: renderers.
_STRINGS: dict[str, str] = {
    "Frequency [Hz]": "Frecuencia [Hz]",
    "Weighting factor [dB]": "Factor de ponderación [dB]",
    "Unweighted $a_i$": "Sin ponderar $a_i$",
    "r.m.s. acceleration [m/s$^2$]": "Aceleración eficaz [m/s$^2$]",
    "Vibration exposure A(8) [m/s$^2$]": "Exposición a vibración A(8) [m/s$^2$]",
    "driving-point mobility": "movilidad en punto de excitación",
    "transfer mobility": "movilidad de transferencia",
    "Mobility $|Y|$ [m/(N·s)]": "Movilidad $|Y|$ [m/(N·s)]",
    "Transfer stiffness level $L_k$ [dB re 1 N/m]": "Nivel de rigidez de transferencia $L_k$ [dB re 1 N/m]",
    r"Radiation efficiency $\sigma$": r"Eficiencia de radiación $\sigma$",
    "Stress variable $R$": "Variable de tensión $R$",
    "Probability of lumbar injury [%]": "Probabilidad de lesión lumbar [%]",
    "ISO 7626-1 mechanical mobility": "ISO 7626-1 movilidad mecánica",
    "ISO 10846 dynamic transfer stiffness": "ISO 10846 rigidez dinámica de transferencia",
    "Plate radiation efficiency (Leppington / Maidanik)": "Eficiencia de radiación de placa (Leppington / Maidanik)",
    "Frequency weighting {name} (ISO 8041-1)": "Ponderación en frecuencia {name} (ISO 8041-1)",
    "Weighted $W_i a_i$ ({name})": "Ponderada $W_i a_i$ ({name})",
    "{designation} weighted acceleration spectrum  ($a_w$ = {aw} m/s$^2$)": "{designation} espectro de aceleración ponderada  ($a_w$ = {aw} m/s$^2$)",
    "Directive 2002/44/EC daily {kind} exposure  (A(8) = {a8} m/s$^2$, {zone})": "Directiva 2002/44/CE exposición diaria {kind}  (A(8) = {a8} m/s$^2$, {zone})",
    "peak at {v} Hz": "máximo en {v} Hz",
    "ISO 2631-5 injury probability — {sex}": "ISO 2631-5 probabilidad de lesión — {sex}",
    r"$R$ = {r},  $\Pi$ = {p} %": r"$R$ = {r},  $\Pi$ = {p} %",
}


def _t(text: str, language: str = "en") -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    return _STRINGS.get(text, text) if language == "es" else text


def plot_vibration_weighting(
    result: "WeightingResponse", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Frequency-weighting factor (dB) versus frequency (ISO 8041-1).

    :param result: A
        :class:`~phonometry.human_vibration.WeightingResponse` exposing
        ``name``, ``frequencies`` and ``magnitude_db``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the weighting curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    mag_db = np.asarray(result.magnitude_db, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.semilogx(freqs, mag_db, **kwargs)
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("Weighting factor [dB]", language))
    ax.set_title(_t("Frequency weighting {name} (ISO 8041-1)", language).format(name=result.name))
    ax.grid(True, which="both", alpha=0.3)
    format_frequency_axis(ax, float(freqs.min()), float(freqs.max()))
    localize_axes(ax, language)
    return ax


def plot_weighted_spectrum(
    result: "WeightedSpectrum", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Unweighted vs weighted one-third-octave acceleration spectrum.

    Draws the measured band accelerations and, overlaid, the weighted band
    contributions ``W_i*a_i``; the overall ``a_w`` is annotated in the title.

    :param result: A
        :class:`~phonometry.human_vibration.WeightedSpectrum` exposing
        ``frequencies``, ``band_accelerations``, ``weighted``, ``overall`` and
        ``weighting_name``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the weighted (primary) bars.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    raw = np.asarray(result.band_accelerations, dtype=np.float64)
    weighted = np.asarray(result.weighted, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)
    ax.set_xlabel(_t("Frequency [Hz]", language))
    width = 0.4
    # The weighted bars are the primary artist; forward user kwargs there.
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(
        positions - width / 2, raw, width, color=_C_MUTED,
        label=_t("Unweighted $a_i$", language),
    )
    ax.bar(
        positions + width / 2,
        weighted,
        width,
        label=_t("Weighted $W_i a_i$ ({name})", language).format(name=result.weighting_name),
        **kwargs,
    )
    ax.set_ylabel(_t("r.m.s. acceleration [m/s$^2$]", language))
    # Wh is the hand-arm weighting of ISO 5349-1; the others (Wk, Wd, Wm...)
    # are the whole-body weightings of ISO 2631.
    designation = "ISO 5349-1" if str(result.weighting_name) == "Wh" else "ISO 2631"
    ax.set_title(_t("{designation} weighted acceleration spectrum  ($a_w$ = {aw} m/s$^2$)", language).format(
        designation=designation,
        aw=format_number(float(result.overall), language, decimals=3),
    ))
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    # localize_axes leaves the categorical band axis (a FuncFormatter) alone.
    localize_axes(ax, language)
    return ax


def plot_daily_exposure(
    result: "DailyVibrationExposure", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Partial daily exposures against the EAV / ELV (Directive 2002/44/EC).

    Draws one bar per operation (its partial exposure ``A_i(8)``), a combined
    ``A(8)`` bar, and the exposure action and limit value as horizontal lines.

    :param result: A
        :class:`~phonometry.human_vibration.DailyVibrationExposure` exposing
        ``labels``, ``partials``, ``a8`` and ``assessment``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the exposure :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import decimal_comma, format_number, localize_axes

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
    ax.set_ylabel(_t("Vibration exposure A(8) [m/s$^2$]", language))

    assessment = result.assessment
    eav = float(assessment.action_value)
    elv = float(assessment.limit_value)
    ax.axhline(eav, color=_C_SECONDARY, ls="--",
               label="EAV = " + decimal_comma(f"{eav:g}", language))
    ax.axhline(elv, color=_C_REFERENCE, ls="--",
               label="ELV = " + decimal_comma(f"{elv:g}", language))
    top = max(elv, float(np.max(values))) * 1.15
    ax.set_ylim(0.0, top)
    kind = str(assessment.kind).upper()
    ax.set_title(_t("Directive 2002/44/EC daily {kind} exposure  (A(8) = {a8} m/s$^2$, {zone})", language).format(
        kind=kind, a8=format_number(float(result.a8), language, decimals=2),
        zone=assessment.zone,
    ))
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    # localize_axes leaves the categorical operation-label axis (a FuncFormatter) alone.
    localize_axes(ax, language)
    return ax


def plot_mobility(
    result: "MobilityResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Mobility magnitude ``|Y(f)|`` on log-log axes (ISO 7626-1).

    :param result: A :class:`~phonometry.mechanical_mobility.MobilityResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the magnitude ``plot``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    mag = np.asarray(result.magnitude, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    label = (_t("driving-point mobility", language) if result.driving_point
             else _t("transfer mobility", language))
    ax.loglog(freq, mag, label=label, **kwargs)
    # Mark the mobility peak (a resonance for a driving-point FRF).
    peak = int(np.argmax(mag))
    ax.plot(freq[peak], mag[peak], "o", color=_C_REFERENCE, zorder=5,
            label=_t("peak at {v} Hz", language).format(
                v=format_number(freq[peak], language, decimals=1)))
    format_frequency_axis(ax, float(freq.min()), float(freq.max()))
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("Mobility $|Y|$ [m/(N·s)]", language))
    ax.set_title(_t("ISO 7626-1 mechanical mobility", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_transfer_stiffness(
    result: "TransferStiffnessResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any,
) -> Axes:
    """Dynamic transfer stiffness level ``L_k(f)`` on a log-frequency axis.

    :param result: A :class:`~phonometry.transfer_stiffness.TransferStiffnessResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the level ``plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    level = np.asarray(result.level, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.semilogx(freq, level, label=r"$L_k = 20\,\lg(|k_{2,1}|/k_0)$", **kwargs)
    format_frequency_axis(ax, float(freq.min()), float(freq.max()))
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("Transfer stiffness level $L_k$ [dB re 1 N/m]", language))
    ax.set_title(_t("ISO 10846 dynamic transfer stiffness", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_radiation_efficiency(
    result: "RadiationEfficiencyResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any,
) -> Axes:
    """Radiation efficiency ``sigma(f)`` on log-log axes (Hopkins 2.9.4).

    :param result: A
        :class:`~phonometry.vibration.radiation_efficiency.RadiationEfficiencyResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``sigma`` curve ``plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

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
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t(r"Radiation efficiency $\sigma$", language))
    ax.set_title(_t("Plate radiation efficiency (Leppington / Maidanik)", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_multiple_shock(
    result: "MultipleShockResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Injury-probability curve ``P(R)`` with this assessment's ``R`` marked.

    :param result: A :class:`~phonometry.multiple_shock_vibration.MultipleShockResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``R`` marker ``scatter``.
    :return: The axes.
    """
    from ..vibration.multiple_shock_vibration import injury_probability
    from .._i18n import format_number, localize_axes

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
               label=_t(r"$R$ = {r},  $\Pi$ = {p} %", language).format(
                   r=format_number(result.risk, language, decimals=2),
                   p=format_number(100.0 * result.probability, language, decimals=0)),
               **kwargs)
    ax.set_xlabel(_t("Stress variable $R$", language))
    ax.set_ylabel(_t("Probability of lumbar injury [%]", language))
    ax.set_title(_t("ISO 2631-5 injury probability — {sex}", language).format(sex=result.sex))
    ax.set_xlim(left=0.0)
    ax.set_ylim(0.0, 100.0)
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(True, alpha=0.3)
    localize_axes(ax, language)
    return ax
