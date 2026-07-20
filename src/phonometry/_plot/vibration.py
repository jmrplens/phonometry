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

#: EN/ES text for every fixed label, title and legend of this module. The
#: English entries are byte-for-byte the historical strings; ``_t`` returns
#: them unchanged for ``language="en"``.
_STRINGS: dict[str, dict[str, str]] = {
    "freq_hz": {"en": "Frequency [Hz]", "es": "Frecuencia [Hz]"},
    "weighting_factor": {
        "en": "Weighting factor [dB]",
        "es": "Factor de ponderación [dB]",
    },
    "unweighted_ai": {"en": r"Unweighted $a_i$", "es": r"Sin ponderar $a_i$"},
    "rms_accel": {
        "en": r"r.m.s. acceleration [m/s$^2$]",
        "es": r"Aceleración eficaz [m/s$^2$]",
    },
    "vib_exposure_a8": {
        "en": r"Vibration exposure A(8) [m/s$^2$]",
        "es": r"Exposición a vibración A(8) [m/s$^2$]",
    },
    "mobility_driving_point": {
        "en": "driving-point mobility",
        "es": "movilidad en punto de excitación",
    },
    "mobility_transfer": {
        "en": "transfer mobility",
        "es": "movilidad de transferencia",
    },
    "mobility_y": {
        "en": r"Mobility $|Y|$ [m/(N·s)]",
        "es": r"Movilidad $|Y|$ [m/(N·s)]",
    },
    "transfer_stiffness_level": {
        "en": r"Transfer stiffness level $L_k$ [dB re 1 N/m]",
        "es": r"Nivel de rigidez de transferencia $L_k$ [dB re 1 N/m]",
    },
    "radiation_efficiency": {
        "en": r"Radiation efficiency $\sigma$",
        "es": r"Eficiencia de radiación $\sigma$",
    },
    "stress_variable": {
        "en": r"Stress variable $R$",
        "es": r"Variable de tensión $R$",
    },
    "lumbar_injury_prob": {
        "en": "Probability of lumbar injury [%]",
        "es": "Probabilidad de lesión lumbar [%]",
    },
    "mobility_title": {
        "en": "ISO 7626-1 mechanical mobility",
        "es": "ISO 7626-1 movilidad mecánica",
    },
    "transfer_stiffness_title": {
        "en": "ISO 10846 dynamic transfer stiffness",
        "es": "ISO 10846 rigidez dinámica de transferencia",
    },
    "radiation_title": {
        "en": "Plate radiation efficiency (Leppington / Maidanik)",
        "es": "Eficiencia de radiación de placa (Leppington / Maidanik)",
    },
    # Templates (``.format`` fields hold already-localised numbers / data).
    "vib_weighting_title": {
        "en": "Frequency weighting {name} (ISO 8041-1)",
        "es": "Ponderación en frecuencia {name} (ISO 8041-1)",
    },
    "weighted_wia": {
        "en": r"Weighted $W_i a_i$ ({name})",
        "es": r"Ponderada $W_i a_i$ ({name})",
    },
    "weighted_spectrum_title": {
        "en": "{designation} weighted acceleration spectrum  ($a_w$ = {aw} m/s$^2$)",
        "es": "{designation} espectro de aceleración ponderada  ($a_w$ = {aw} m/s$^2$)",
    },
    "daily_exposure_title": {
        "en": ("Directive 2002/44/EC daily {kind} exposure  "
               "(A(8) = {a8} m/s$^2$, {zone})"),
        "es": ("Directiva 2002/44/CE exposición diaria {kind}  "
               "(A(8) = {a8} m/s$^2$, {zone})"),
    },
    "mobility_peak": {"en": "peak at {v} Hz", "es": "máximo en {v} Hz"},
    "injury_title": {
        "en": "ISO 2631-5 injury probability — {sex}",
        "es": "ISO 2631-5 probabilidad de lesión — {sex}",
    },
    "injury_marker": {
        "en": r"$R$ = {r},  $\Pi$ = {p} %",
        "es": r"$R$ = {r},  $\Pi$ = {p} %",
    },
}


def _t(key: str, language: str) -> str:
    """Look up the localised text for ``key`` (falls back to English)."""
    entry = _STRINGS[key]
    return entry.get(language, entry["en"])


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
    ax.set_xlabel(_t("freq_hz", language))
    ax.set_ylabel(_t("weighting_factor", language))
    ax.set_title(_t("vib_weighting_title", language).format(name=result.name))
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
    ax.set_xlabel(_t("freq_hz", language))
    width = 0.4
    # The weighted bars are the primary artist; forward user kwargs there.
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(
        positions - width / 2, raw, width, color=_C_MUTED,
        label=_t("unweighted_ai", language),
    )
    ax.bar(
        positions + width / 2,
        weighted,
        width,
        label=_t("weighted_wia", language).format(name=result.weighting_name),
        **kwargs,
    )
    ax.set_ylabel(_t("rms_accel", language))
    # Wh is the hand-arm weighting of ISO 5349-1; the others (Wk, Wd, Wm...)
    # are the whole-body weightings of ISO 2631.
    designation = "ISO 5349-1" if str(result.weighting_name) == "Wh" else "ISO 2631"
    ax.set_title(_t("weighted_spectrum_title", language).format(
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
    ax.set_ylabel(_t("vib_exposure_a8", language))

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
    ax.set_title(_t("daily_exposure_title", language).format(
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
    label = (_t("mobility_driving_point", language) if result.driving_point
             else _t("mobility_transfer", language))
    ax.loglog(freq, mag, label=label, **kwargs)
    # Mark the mobility peak (a resonance for a driving-point FRF).
    peak = int(np.argmax(mag))
    ax.plot(freq[peak], mag[peak], "o", color=_C_REFERENCE, zorder=5,
            label=_t("mobility_peak", language).format(
                v=format_number(freq[peak], language, decimals=1)))
    format_frequency_axis(ax, float(freq.min()), float(freq.max()))
    ax.set_xlabel(_t("freq_hz", language))
    ax.set_ylabel(_t("mobility_y", language))
    ax.set_title(_t("mobility_title", language))
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
    ax.set_xlabel(_t("freq_hz", language))
    ax.set_ylabel(_t("transfer_stiffness_level", language))
    ax.set_title(_t("transfer_stiffness_title", language))
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
    ax.set_xlabel(_t("freq_hz", language))
    ax.set_ylabel(_t("radiation_efficiency", language))
    ax.set_title(_t("radiation_title", language))
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
               label=_t("injury_marker", language).format(
                   r=format_number(result.risk, language, decimals=2),
                   p=format_number(100.0 * result.probability, language, decimals=0)),
               **kwargs)
    ax.set_xlabel(_t("stress_variable", language))
    ax.set_ylabel(_t("lumbar_injury_prob", language))
    ax.set_title(_t("injury_title", language).format(sex=result.sex))
    ax.set_xlim(left=0.0)
    ax.set_ylim(0.0, 100.0)
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(True, alpha=0.3)
    localize_axes(ax, language)
    return ax
