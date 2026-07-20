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

#: EN/ES text for every fixed label, title and legend of this module. The
#: English entries are byte-for-byte the historical strings; ``_t`` returns
#: them unchanged for ``language="en"``.
_STRINGS: dict[str, dict[str, str]] = {
    "freq_hz": {"en": "Frequency [Hz]", "es": "Frecuencia [Hz]"},
    "band": {"en": "Band", "es": "Banda"},
    "mti": {
        "en": "Modulation transfer index MTI",
        "es": "Índice de transferencia de modulación MTI",
    },
    "third_octave_band": {
        "en": "One-third-octave band [Hz]",
        "es": "Banda de tercio de octava [Hz]",
    },
    "mean_corr": {
        "en": "Mean intermediate correlation",
        "es": "Correlación intermedia media",
    },
    "spectral_corr": {
        "en": r"Spectral correlation $d_m$",
        "es": r"Correlación espectral $d_m$",
    },
    "analysis_segment": {"en": "Analysis segment", "es": "Segmento de análisis"},
    "band_audibility": {"en": "Band audibility", "es": "Audibilidad de banda"},
    "band_audibility_ai": {
        "en": r"Band audibility $A_i$",
        "es": r"Audibilidad de banda $A_i$",
    },
    "importance_weighted": {
        "en": r"Importance-weighted $I_i A_i$ (scaled)",
        "es": r"$I_i A_i$ ponderada por importancia (escalada)",
    },
    "median": {"en": "Median", "es": "Mediana"},
    "median_n50": {"en": r"Median $N_{50}$", "es": r"Mediana $N_{50}$"},
    "threshold_dev_18": {
        "en": "Threshold deviation from age 18 [dB]",
        "es": "Desviación del umbral respecto a 18 años [dB]",
    },
    "nipts_db": {"en": "NIPTS [dB]", "es": "NIPTS [dB]"},
    "htla_age": {"en": "Age (HTLA, ISO 7029)", "es": "Edad (HTLA, ISO 7029)"},
    "noise_nipts": {"en": "Noise (NIPTS)", "es": "Ruido (NIPTS)"},
    "age_noise_htlan": {
        "en": "Age + noise (HTLAN)",
        "es": "Edad + ruido (HTLAN)",
    },
    "htl_level": {
        "en": "Hearing threshold level [dB]",
        "es": "Nivel del umbral de audición [dB]",
    },
    "a_weighted_level": {
        "en": "A-weighted level [dB]",
        "es": "Nivel ponderado A [dB]",
    },
    # Templates (``.format`` fields hold already-localised numbers).
    "sti_title": {
        "en": "IEC 60268-16 STI = {sti}  (rating {rating})",
        "es": "IEC 60268-16 STI = {sti}  (calificación {rating})",
    },
    "stoi_title": {"en": "{name} = {v}", "es": "{name} = {v}"},
    "sii_title": {"en": "ANSI S3.5 SII = {sii}", "es": "ANSI S3.5 SII = {sii}"},
    "fractile": {"en": "Fractile {v}", "es": "Fractil {v}"},
    "iso7029_title": {
        "en": "ISO 7029 hearing threshold — {sex}, age {age}",
        "es": "ISO 7029 umbral de audición — {sex}, edad {age}",
    },
    "nipts_title": {
        "en": "ISO 1999 NIPTS — $L_{{EX,8h}}$ = {lex} dB, {years} yr",
        "es": "ISO 1999 NIPTS — $L_{{EX,8h}}$ = {lex} dB, {years} años",
    },
    "htlan_title": {
        "en": "ISO 1999 HTLAN — {sex}, age {age}, {lex} dB / {years} yr",
        "es": "ISO 1999 HTLAN — {sex}, edad {age}, {lex} dB / {years} años",
    },
    "occupational_title": {
        "en": ("ISO 9612 daily noise exposure — $L_{{EX,8h}}$ = "
               "{lex} dB (U = {u} dB)"),
        "es": ("ISO 9612 exposición diaria al ruido — $L_{{EX,8h}}$ = "
               "{lex} dB (U = {u} dB)"),
    },
}


def _t(key: str, language: str) -> str:
    """Look up the localised text for ``key`` (falls back to English)."""
    entry = _STRINGS[key]
    return entry.get(language, entry["en"])


def plot_sti(
    result: STIResult, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-band modulation transfer index bars with the STI and rating.

    :param result: A :class:`~phonometry.sti.STIResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    mti = np.asarray(result.mti, dtype=np.float64)
    positions = np.arange(mti.size)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(positions, mti, **kwargs)
    banded = mti.size == len(_STI_BAND_CENTERS)
    if banded:
        _band_axis(ax, np.asarray(_STI_BAND_CENTERS))
        ax.set_xlabel(_t("freq_hz", language))
    else:
        ax.set_xticks(positions)
        ax.set_xlabel(_t("band", language))
    ax.set_ylabel(_t("mti", language))
    ax.set_ylim(0.0, 1.0)
    ax.set_title(_t("sti_title", language).format(
        sti=format_number(result.sti, language, decimals=2), rating=result.rating,
    ))
    ax.grid(True, axis="y", alpha=0.3)
    # localize_axes leaves the categorical band axis (a FuncFormatter) alone.
    localize_axes(ax, language)
    return ax


def plot_stoi(
    result: "STOIResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Intermediate intelligibility that averages to the STOI/ESTOI index.

    For STOI the intermediate measure decomposes per one-third-octave band, so
    the mean correlation per band is drawn as bars; for ESTOI, whose index
    mixes the bands, the spectral correlation per analysis segment is drawn as
    a line.

    :param result: A :class:`~phonometry.hearing.objective_intelligibility.STOIResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the underlying :meth:`bar`/:meth:`plot`.
    :return: The axes.
    """
    from .._i18n import decimal_comma, format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    name = "ESTOI" if result.extended else "STOI"
    banded = result.band_scores is not None
    if banded:
        freqs = np.asarray(result.band_frequencies, dtype=np.float64)
        scores = np.asarray(result.band_scores, dtype=np.float64)
        positions = np.arange(scores.size)
        kwargs.setdefault("color", _C_PRIMARY)
        ax.bar(positions, scores, **kwargs)
        ax.set_xticks(positions)
        ax.set_xticklabels([decimal_comma(f"{f:g}", language) for f in freqs],
                           rotation=45, ha="right")
        ax.set_xlabel(_t("third_octave_band", language))
        ax.set_ylabel(_t("mean_corr", language))
    else:
        scores = np.asarray(result.segment_scores, dtype=np.float64)
        kwargs.setdefault("color", _C_PRIMARY)
        ax.plot(np.arange(scores.size), scores, **kwargs)
        ax.set_xlabel(_t("analysis_segment", language))
        ax.set_ylabel(_t("spectral_corr", language))
    # The intermediate correlations are cosine-similarity quantities in
    # [-1, 1] (unlike the [0, 1] ratios of plot_sti/plot_sii), so keep room
    # for anti-correlated bands rather than clipping them at zero.
    ax.set_ylim(-1.0, 1.0)
    ax.set_title(_t("stoi_title", language).format(
        name=name, v=format_number(result.value, language, decimals=3),
    ))
    ax.grid(True, axis="y", alpha=0.3)
    # localize_axes leaves the categorical band labels (a FuncFormatter) alone,
    # so the comma-localized labels set above survive.
    localize_axes(ax, language)
    return ax


def plot_sii(
    result: "SIIResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-band audibility and its importance-weighted contribution to the SII.

    :param result: A :class:`~phonometry.sii.SIIResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the weighted-contribution :meth:`bar`.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    audibility = np.asarray(result.band_audibility, dtype=np.float64)
    contribution = audibility * np.asarray(result.band_importance, dtype=np.float64)
    positions = _band_axis(ax, freqs)
    ax.set_xlabel(_t("freq_hz", language))
    ax.bar(positions, audibility, color=_C_PRIMARY_LIGHT,
           label=_t("band_audibility_ai", language))
    kwargs.setdefault("color", _C_PRIMARY)
    # A fully masked speech signal (SII = 0) has an all-zero contribution;
    # keep the zero bars rather than dividing 0/0 into NaN.
    peak = float(contribution.max()) if contribution.size else 0.0
    scaled = contribution / peak if peak > 0.0 else contribution
    ax.bar(positions, scaled, width=0.5,
           label=_t("importance_weighted", language), **kwargs)
    ax.set_ylabel(_t("band_audibility", language))
    ax.set_ylim(0.0, 1.0)
    ax.set_title(_t("sii_title", language).format(
        sii=format_number(result.sii, language, decimals=3),
    ))
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    # localize_axes leaves the categorical band axis (a FuncFormatter) alone.
    localize_axes(ax, language)
    return ax


def plot_age_threshold(
    result: "AgeThresholdResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Median age-related hearing threshold with the 10-90 % fractile band.

    :param result: An :class:`~phonometry.hearing.AgeThresholdResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the median line ``plot``.
    :return: The axes.
    """
    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    median = np.asarray(result.median, dtype=np.float64)
    su = np.asarray(result.spread_upper, dtype=np.float64)
    sl = np.asarray(result.spread_lower, dtype=np.float64)

    _fractile_band(ax, freqs, median, sl, su, color=_C_PRIMARY_LIGHT)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.plot(freqs, median, "o-", label=_t("median", language), **kwargs)
    if abs(result.fractile - 0.5) > 1e-9:
        ax.plot(freqs, np.asarray(result.threshold, dtype=np.float64), "s--",
                color=_C_REFERENCE, label=_t("fractile", language).format(
                    v=decimal_comma(f"{result.fractile:g}", language)))
    _freq_axis(ax, freqs)
    ax.set_xlabel(_t("freq_hz", language))
    ax.set_ylabel(_t("threshold_dev_18", language))
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    ax.set_title(_t("iso7029_title", language).format(
        sex=result.sex, age=decimal_comma(f"{result.age:g}", language)))
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_nipts(
    result: "NiptsResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Median NIPTS spectrum with the 10-90 % fractile band (ISO 1999).

    :param result: A :class:`~phonometry.noise_induced_hearing_loss.NiptsResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the median line ``plot``.
    :return: The axes.
    """
    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    median = np.asarray(result.median, dtype=np.float64)
    du = np.asarray(result.spread_upper, dtype=np.float64)
    dl = np.asarray(result.spread_lower, dtype=np.float64)

    _fractile_band(ax, freqs, median, dl, du, color=_C_SECONDARY_LIGHT, floor=0.0)
    kwargs.setdefault("color", _C_SECONDARY)
    ax.plot(freqs, median, "o-", label=_t("median_n50", language), **kwargs)
    if abs(result.fractile - 0.5) > 1e-9:
        ax.plot(freqs, np.asarray(result.value, dtype=np.float64), "s--",
                color=_C_REFERENCE, label=_t("fractile", language).format(
                    v=decimal_comma(f"{result.fractile:g}", language)))
    _freq_axis(ax, freqs)
    ax.set_xlabel(_t("freq_hz", language))
    ax.set_ylabel(_t("nipts_db", language))
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    ax.set_title(_t("nipts_title", language).format(
        lex=decimal_comma(f"{result.l_ex:g}", language),
        years=decimal_comma(f"{result.years:g}", language)))
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_htlan(
    result: "HtlanResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Age, noise and combined hearing threshold components (ISO 1999, 6.1).

    :param result: A :class:`~phonometry.noise_induced_hearing_loss.HtlanResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the combined-threshold line ``plot``.
    :return: The axes.
    """
    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    ax.plot(freqs, np.asarray(result.htla, dtype=np.float64), "o-",
            color=_C_PRIMARY, label=_t("htla_age", language))
    ax.plot(freqs, np.asarray(result.nipts, dtype=np.float64), "^-",
            color=_C_SECONDARY, label=_t("noise_nipts", language))
    kwargs.setdefault("color", _C_REFERENCE)
    ax.plot(freqs, np.asarray(result.threshold, dtype=np.float64), "s--",
            label=_t("age_noise_htlan", language), **kwargs)
    _freq_axis(ax, freqs)
    ax.set_xlabel(_t("freq_hz", language))
    ax.set_ylabel(_t("htl_level", language))
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    ax.set_title(_t("htlan_title", language).format(
        sex=result.sex, age=decimal_comma(f"{result.age:g}", language),
        lex=decimal_comma(f"{result.l_ex:g}", language),
        years=decimal_comma(f"{result.years:g}", language)))
    ax.legend(loc="lower left", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_occupational_exposure(
    result: "ExposureResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-task contributions to the daily exposure level (ISO 9612).

    One bar per task (its contribution to ``LEX,8h``), with the combined
    ``LEX,8h`` and the one-sided upper limit ``LEX,8h + U`` as horizontal
    lines.

    :param result: An
        :class:`~phonometry.occupational_exposure.ExposureResult` from the
        task-based strategy (the one that carries per-task contributions).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the task :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    :raises ValueError: If the result carries no per-task contributions.
    """
    from .._i18n import format_number, localize_axes

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
               label="$L_{EX,8h}$ = "
                     + format_number(result.lex_8h, language, decimals=1) + " dB")
    ax.axhline(result.upper_limit, color=_C_MUTED, ls=":",
               label="$L_{EX,8h} + U$ = "
                     + format_number(result.upper_limit, language, decimals=1)
                     + " dB")
    top = max(result.upper_limit, max(contributions))
    bottom = min(0.0, min(contributions))
    ax.set_ylim(bottom * 1.12 if bottom < 0.0 else 0.0, top * 1.12)
    ax.set_ylabel(_t("a_weighted_level", language))
    ax.set_title(_t("occupational_title", language).format(
        lex=format_number(result.lex_8h, language, decimals=1),
        u=format_number(result.expanded_uncertainty, language, decimals=1)))
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    # localize_axes leaves the categorical task-label axis (a FuncFormatter) alone.
    localize_axes(ax, language)
    return ax
