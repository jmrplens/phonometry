#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the hearing domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_EDGE,
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _LEGEND_UPPER_RIGHT,
    _band_axis,
    _fractile_band,
    _freq_axis,
    _new_axes,
    style_default,
    theme_fill,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..hearing.active_noise_reduction import (
        ActiveInsertionLossResult,
        AnrLinearityResult,
        AnrTotalAttenuationResult,
    )
    from ..hearing.hearing_protectors import (
        AssumedProtectionResult,
        HMLRatingResult,
        ProtectedLevelResult,
        SNRRatingResult,
    )
    from ..hearing.noise_induced_hearing_loss import HtlanResult, NiptsResult
    from ..hearing.occupational_exposure import ExposureResult
    from ..hearing.real_ear_attenuation import (
        AttenuationDifferenceResult,
        RealEarAttenuationResult,
        ReatSoundFieldCheck,
    )
    from ..hearing.threshold import AgeThresholdResult

# Tolerance under which the requested population fractile counts as the
# median (0.5), so the separate fractile curve, which would duplicate the
# median line, is skipped.
_MEDIAN_FRACTILE_EPS = 1e-9

#: Spanish translations of the fixed strings rendered by the hearing
#: ``.plot()`` renderers, keyed by their verbatim English text. ``_t``
#: returns the English key unchanged for any language other than ``"es"``,
#: so the English output is byte-for-byte identical to the pre-i18n
#: renderers.
#: Labels the renderers repeat; the Spanish table is keyed by the same
#: constants, so a label is written once.
_FREQ_LABEL = "Frequency [Hz]"
_ATTENUATION_LABEL = "Sound attenuation [dB]"
_BAND_LEVEL_LABEL = "A-weighted band level [dB]"
_REDUCTION_LABEL = "Predicted noise level reduction [dB]"
_C_MINUS_A_LABEL = "$L_{p,C} - L_{p,A}$ [dB]"
_SUBJECT_LABEL = "Test subject"
_SPREAD_LABEL = r"$\pm s_f$"
_HML_TITLE = "ISO 4869-2 HML method: $H$ = {h}, $M$ = {m}, $L$ = {l} dB"
#: The curve of Formulae (16) and (17) carries its own label rather than a
#: slice of the title: deriving one from the other by splitting on the
#: punctuation breaks the moment a translation punctuates differently.
_HML_CURVE_LABEL = "$PNR$ from $H$ = {h}, $M$ = {m}, $L$ = {l} dB"
_NIPTS_LABEL = "NIPTS [dB]"
_FRACTILE_LABEL = "Fractile {v}"
_REAT_TITLE = "ISO 4869-1 mean attenuation: {n} subjects"
_U95_LABEL = r"$\pm U_{95}$"
_DIFFERENCE_TITLE = "ISO 4869-1 Annex B: significant at {bands}"
_DIFFERENCE_NONE_TITLE = "ISO 4869-1 Annex B: no significant difference"
_CRITERION_LABEL = "criterion $\\sqrt{U_{95,1}^2 + U_{95,2}^2}$"
_DIFFERENCE_AXIS_LABEL = "Difference [dB]"
_FIELD_TITLE = "ISO 4869-1 sound field (4.2.2): {verdict}"
_FIELD_AXIS_LABEL = "Level deviation [dB]"
_AIL_LABEL = "Active insertion loss [dB]"
_AIL_TITLE = "ISO 4869-6 active insertion loss: {n} subjects"
_ANR_TITLE = (
    "ISO 4869-6 total attenuation: $H$ = {h}, $M$ = {m}, $L$ = {l}, $SNR$ = {snr} dB"
)
_EXTERNAL_LEVEL_LABEL = "External A-weighted level [dB]"
_STEP_LABEL = "Step at the ear, 125 Hz octave [dB]"
_LINEARITY_TITLE = "ISO 4869-6 linear operation: up to {level} dB"

_STRINGS: dict[str, str] = {
    _FREQ_LABEL: "Frecuencia [Hz]",
    _ATTENUATION_LABEL: "Atenuación acústica [dB]",
    _BAND_LEVEL_LABEL: "Nivel de banda ponderado A [dB]",
    _REDUCTION_LABEL: "Reducción prevista del nivel de ruido [dB]",
    _C_MINUS_A_LABEL: _C_MINUS_A_LABEL,
    _SUBJECT_LABEL: "Sujeto de ensayo",
    "mean attenuation $m_f$": r"atenuación media $m_f$",
    _SPREAD_LABEL: _SPREAD_LABEL,
    "assumed protection $APV_{{f{x}}}$": "protección supuesta $APV_{{f{x}}}$",
    "ISO 4869-2 assumed protection values: {x} % performance": "ISO 4869-2 valores de protección supuesta: rendimiento del {x} %",
    _HML_TITLE: "ISO 4869-2 método HML: $H$ = {h}, $M$ = {m}, $L$ = {l} dB",
    _HML_CURVE_LABEL: "$PNR$ a partir de $H$ = {h}, $M$ = {m}, $L$ = {l} dB",
    "ISO 4869-2 single number rating: $SNR$ = {snr} dB": "ISO 4869-2 índice de número único: $SNR$ = {snr} dB",
    "ISO 4869-2 octave-band method: $L'_{{p,A{x}}}$ = {level} dB": "ISO 4869-2 método por bandas de octava: $L'_{{p,A{x}}}$ = {level} dB",
    "per subject": "por sujeto",
    "reference noises (Table 2)": "ruidos de referencia (Tabla 2)",
    "protected band level": "nivel de banda protegido",
    r"$H$, $M$, $L$ anchors": r"anclas $H$, $M$, $L$",
    "Median": "Mediana",
    "Median $N_{50}$": "Mediana $N_{50}$",
    "Threshold deviation from age 18 [dB]": "Desviación del umbral respecto a 18 años [dB]",
    _NIPTS_LABEL: _NIPTS_LABEL,
    "Age (HTLA, ISO 7029)": "Edad (HTLA, ISO 7029)",
    "Noise (NIPTS)": "Ruido (NIPTS)",
    "Age + noise (HTLAN)": "Edad + ruido (HTLAN)",
    "Hearing threshold level [dB]": "Nivel del umbral de audición [dB]",
    "A-weighted level [dB]": "Nivel ponderado A [dB]",
    _FRACTILE_LABEL: "Fractil {v}",
    "male": "hombre",
    "female": "mujer",
    "ISO 7029 hearing threshold: {sex}, age {age}": "ISO 7029 umbral de audición: {sex}, edad {age}",
    r"ISO 1999 NIPTS: $L_\mathrm{{EX,8h}}$ = {lex} dB, {years} yr": r"ISO 1999 NIPTS: $L_\mathrm{{EX,8h}}$ = {lex} dB, {years} años",
    "ISO 1999 HTLAN: {sex}, age {age}, {lex} dB / {years} yr": "ISO 1999 HTLAN: {sex}, edad {age}, {lex} dB / {years} años",
    r"ISO 9612 daily noise exposure: $L_\mathrm{{EX,8h}}$ = {lex} dB ($U$ = {u} dB)": r"ISO 9612 exposición diaria al ruido: $L_\mathrm{{EX,8h}}$ = {lex} dB "
    r"($U$ = {u} dB)",
    _REAT_TITLE: "ISO 4869-1 atenuación media: {n} sujetos",
    "individual attenuation": "atenuación individual",
    "mean attenuation $m$": "atenuación media $m$",
    _U95_LABEL: _U95_LABEL,
    _DIFFERENCE_TITLE: "ISO 4869-1 Anexo B: significativa en {bands}",
    _DIFFERENCE_NONE_TITLE: "ISO 4869-1 Anexo B: ninguna diferencia significativa",
    "difference of the means $|m_1 - m_2|$": "diferencia de las medias $|m_1 - m_2|$",
    _CRITERION_LABEL: "criterio $\\sqrt{U_{95,1}^2 + U_{95,2}^2}$",
    "significant": "significativa",
    _DIFFERENCE_AXIS_LABEL: "Diferencia [dB]",
    _FIELD_TITLE: "ISO 4869-1 campo sonoro (4.2.2): {verdict}",
    "qualifies": "cumple",
    "does not qualify": "no cumple",
    "a) met, b) not judged": "a) cumple, b) sin evaluar",
    "largest position deviation": "mayor desviación de posición",
    r"$\pm$2.5 dB limit": r"límite de $\pm$2,5 dB",
    "difference between right and left": "diferencia entre derecha e izquierda",
    "3 dB limit": "límite de 3 dB",
    "rotation variation": "variación en rotación",
    "Table 1 limit": "límite de la Tabla 1",
    _FIELD_AXIS_LABEL: "Desviación del nivel [dB]",
    _AIL_LABEL: "Pérdida por inserción activa [dB]",
    _AIL_TITLE: "ISO 4869-6 pérdida por inserción activa: {n} sujetos",
    _ANR_TITLE: "ISO 4869-6 atenuación total: $H$ = {h}, $M$ = {m}, $L$ = {l}, $SNR$ = {snr} dB",
    _EXTERNAL_LEVEL_LABEL: "Nivel exterior ponderado A [dB]",
    _STEP_LABEL: "Paso en el oído, octava de 125 Hz [dB]",
    _LINEARITY_TITLE: "ISO 4869-6 funcionamiento lineal: hasta {level} dB",
    "lower-value ear, per subject": "oído de menor pérdida por inserción, por sujeto",
    "mean active insertion loss": "pérdida por inserción activa media",
    "passive (REAT), interpolated": "pasiva (REAT), interpolada",
    "active insertion loss": "pérdida por inserción activa",
    "total, one-third octaves": "total, tercios de octava",
    "total, octaves (Formula (1))": "total, octavas (Fórmula (1))",
    "$APV_{f84}$": "$APV_{f84}$",
    r"5 dB $\pm$ 1 dB": r"5 dB $\pm$ 1 dB",
    "each ear": "cada oído",
    "median over the ears": "mediana de los oídos",
    "highest linear level": "nivel lineal más alto",
}


def _t(text: str, language: str = "en") -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    return _STRINGS.get(text, text) if language == "es" else text


def plot_age_threshold(
    result: AgeThresholdResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
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

    _fractile_band(ax, freqs, median, sl, su, color=_C_PRIMARY, language=language)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Median", language))
    ax.plot(freqs, median, "o-", **kwargs)
    if abs(result.fractile - 0.5) > _MEDIAN_FRACTILE_EPS:
        ax.plot(
            freqs,
            np.asarray(result.threshold, dtype=np.float64),
            "s--",
            color=_C_REFERENCE,
            label=_t(_FRACTILE_LABEL, language).format(
                v=decimal_comma(f"{result.fractile:g}", language)
            ),
        )
    _freq_axis(ax, freqs, language=language)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Threshold deviation from age 18 [dB]", language))
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    ax.set_title(
        _t("ISO 7029 hearing threshold: {sex}, age {age}", language).format(
            sex=_t(result.sex, language), age=decimal_comma(f"{result.age:g}", language)
        )
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_nipts(
    result: NiptsResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Median NIPTS spectrum with the 10-90 % fractile band (ISO 1999).

    :param result: A :class:`~phonometry.hearing.noise_induced_hearing_loss.NiptsResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the median line ``plot``.
    :return: The axes.
    """
    from .._i18n import decimal_comma, fmt_minus, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    median = np.asarray(result.median, dtype=np.float64)
    du = np.asarray(result.spread_upper, dtype=np.float64)
    dl = np.asarray(result.spread_lower, dtype=np.float64)

    _fractile_band(
        ax,
        freqs,
        median,
        dl,
        du,
        color=_C_SECONDARY,
        floor=0.0,
        language=language,
    )
    style_default(kwargs, "color", _C_SECONDARY)
    kwargs.setdefault("label", _t("Median $N_{50}$", language))
    ax.plot(freqs, median, "o-", **kwargs)
    if abs(result.fractile - 0.5) > _MEDIAN_FRACTILE_EPS:
        ax.plot(
            freqs,
            np.asarray(result.value, dtype=np.float64),
            "s--",
            color=_C_REFERENCE,
            label=_t(_FRACTILE_LABEL, language).format(
                v=decimal_comma(f"{result.fractile:g}", language)
            ),
        )
    _freq_axis(ax, freqs, language=language)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(_NIPTS_LABEL, language))
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    # l_ex carries no lower bound (only a domain warning), so sign it with
    # fmt_minus: an ASCII hyphen here would be shorter than the U+2212 the
    # axis ticks beside it already draw. The duration is validated positive.
    ax.set_title(
        _t(
            r"ISO 1999 NIPTS: $L_\mathrm{{EX,8h}}$ = {lex} dB, {years} yr", language
        ).format(
            lex=decimal_comma(fmt_minus(result.l_ex, "g"), language),
            years=decimal_comma(f"{result.years:g}", language),
        )
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_htlan(
    result: HtlanResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Age, noise and combined hearing threshold components (ISO 1999, 6.1).

    :param result: A :class:`~phonometry.hearing.noise_induced_hearing_loss.HtlanResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the combined-threshold line ``plot``.
    :return: The axes.
    """
    from .._i18n import decimal_comma, fmt_minus, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    ax.plot(
        freqs,
        np.asarray(result.htla, dtype=np.float64),
        "o-",
        color=_C_PRIMARY,
        label=_t("Age (HTLA, ISO 7029)", language),
    )
    ax.plot(
        freqs,
        np.asarray(result.nipts, dtype=np.float64),
        "^-",
        color=_C_SECONDARY,
        label=_t("Noise (NIPTS)", language),
    )
    style_default(kwargs, "color", _C_REFERENCE)
    kwargs.setdefault("label", _t("Age + noise (HTLAN)", language))
    ax.plot(freqs, np.asarray(result.threshold, dtype=np.float64), "s--", **kwargs)
    _freq_axis(ax, freqs, language=language)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Hearing threshold level [dB]", language))
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    ax.set_title(
        _t("ISO 1999 HTLAN: {sex}, age {age}, {lex} dB / {years} yr", language).format(
            sex=_t(result.sex, language),
            age=decimal_comma(f"{result.age:g}", language),
            lex=decimal_comma(fmt_minus(result.l_ex, "g"), language),
            years=decimal_comma(f"{result.years:g}", language),
        )
    )
    ax.legend(loc="lower left", fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_occupational_exposure(
    result: ExposureResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-task contributions to the daily exposure level (ISO 9612).

    One bar per task (its contribution to ``LEX,8h``), with the combined
    ``LEX,8h`` and the one-sided upper limit ``LEX,8h + U`` as horizontal
    lines.

    :param result: An
        :class:`~phonometry.hearing.occupational_exposure.ExposureResult` from the
        task-based strategy (the one that carries per-task contributions).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the task :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    :raises ValueError: If the result carries no per-task contributions.
    """
    from .._i18n import format_number, localize_axes

    if not result.tasks:
        msg = (
            "plot() needs per-task contributions; only task_based_exposure() "
            "results carry them (the job/full-day strategies do not)."
        )
        raise ValueError(msg)
    ax = ax if ax is not None else _new_axes()
    contributions = [t.lex_8h_contribution for t in result.tasks]
    labels = [t.label for t in result.tasks]
    positions = np.arange(len(contributions), dtype=np.float64)
    style_default(kwargs, "color", _C_PRIMARY)
    ax.bar(positions, contributions, **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45, ha="right")

    ax.axhline(
        result.lex_8h,
        color=_C_REFERENCE,
        ls="--",
        label=r"$L_\mathrm{EX,8h}$ = "
        + format_number(result.lex_8h, language, decimals=1)
        + " dB",
    )
    ax.axhline(
        result.upper_limit,
        color=_C_MUTED,
        ls=":",
        label=r"$L_\mathrm{EX,8h} + U$ = "
        + format_number(result.upper_limit, language, decimals=1)
        + " dB",
    )
    top = max(result.upper_limit, max(contributions))
    bottom = min(0.0, min(contributions))
    ax.set_ylim(bottom * 1.12 if bottom < 0.0 else 0.0, top * 1.12)
    ax.set_ylabel(_t("A-weighted level [dB]", language))
    ax.set_title(
        _t(
            r"ISO 9612 daily noise exposure: $L_\mathrm{{EX,8h}}$ = {lex} dB ($U$ = {u} dB)",
            language,
        ).format(
            lex=format_number(result.lex_8h, language, decimals=1),
            u=format_number(result.expanded_uncertainty, language, decimals=1),
        )
    )
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    # localize_axes leaves the categorical task-label axis (a FuncFormatter) alone.
    localize_axes(ax, language)
    return ax


def plot_assumed_protection(
    result: AssumedProtectionResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Assumed protection values against the distribution they came from.

    Draws the mean attenuation with its standard deviation shaded either side,
    and the assumed protection value on top, so the gap Formula (1) opens
    between the two is the picture. Works for
    :class:`~phonometry.hearing.hearing_protectors.AssumedProtectionResult`.

    :param result: An assumed-protection result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``APV`` curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    mean = np.asarray(result.mean_attenuation, dtype=np.float64)
    spread = np.asarray(result.standard_deviation, dtype=np.float64)
    _freq_axis(ax, freqs, language=language)
    ax.fill_between(
        freqs,
        mean - spread,
        mean + spread,
        color=theme_fill(_C_PRIMARY, ax),
        zorder=0,
        label=_t(_SPREAD_LABEL, language),
    )
    ax.plot(
        freqs,
        mean,
        "-o",
        color=_C_PRIMARY,
        lw=2.0,
        ms=4,
        zorder=3,
        label=_t("mean attenuation $m_f$", language),
    )
    apv_kwargs = dict(kwargs)
    apv_kwargs.setdefault(
        "label",
        _t("assumed protection $APV_{{f{x}}}$", language).format(x=result.performance),
    )
    style_default(apv_kwargs, "color", _C_SECONDARY)
    style_default(apv_kwargs, "linewidth", 2.4)
    ax.plot(
        freqs,
        np.asarray(result.apv, dtype=np.float64),
        "--s",
        ms=4,
        zorder=4,
        **apv_kwargs,
    )
    ax.set_ylabel(_t(_ATTENUATION_LABEL, language))
    ax.set_title(
        _t("ISO 4869-2 assumed protection values: {x} % performance", language).format(
            x=result.performance
        )
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_hml_rating(
    result: HMLRatingResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The ``HML`` two-segment line, over the reference noises behind it.

    Draws the predicted noise level reduction Formulas (16) and (17) give as a
    function of ``LpC - LpA``, with the three anchors marked and the eight
    reference noises of Table 2 scattered at their own differences. Works for
    :class:`~phonometry.hearing.hearing_protectors.HMLRatingResult`.

    :param result: An ``HML`` rating result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``PNR`` curve.
    :return: The axes.
    """
    from .._i18n import localize_axes
    from ..hearing.hearing_protectors import HML_REFERENCE_C_MINUS_A

    ax = ax if ax is not None else _new_axes()
    high, medium, low = result.reported
    # The published triple is what the two segments are built from, so the
    # drawn line is the one a user of the rating would apply.
    left = np.linspace(-4.0, 2.0, 2)
    right = np.linspace(2.0, 12.0, 2)
    curve_kwargs = dict(kwargs)
    style_default(curve_kwargs, "color", _C_PRIMARY)
    style_default(curve_kwargs, "linewidth", 2.4)
    curve_kwargs.setdefault(
        "label", _t(_HML_CURVE_LABEL, language).format(h=high, m=medium, l=low)
    )
    ax.plot(left, medium - (high - medium) / 4.0 * (left - 2.0), **curve_kwargs)
    # The two segments are one line with a corner, so the second takes every
    # option the first did. Only the label is dropped, to keep one legend
    # entry for what the reader sees as a single curve.
    right_kwargs = {k: v for k, v in curve_kwargs.items() if k != "label"}
    ax.plot(right, medium - (medium - low) / 8.0 * (right - 2.0), **right_kwargs)
    ax.plot(
        [-2.0, 2.0, 10.0],
        [high, medium, low],
        "o",
        color=_C_SECONDARY,
        ms=7,
        zorder=4,
        label=_t(r"$H$, $M$, $L$ anchors", language),
    )
    differences = np.asarray(HML_REFERENCE_C_MINUS_A, dtype=np.float64)
    ax.plot(
        np.repeat(differences, result.predicted_reduction.shape[0]),
        result.predicted_reduction.T.reshape(-1),
        ".",
        color=_C_MUTED,
        ms=3,
        alpha=0.55,
        zorder=1,
        label=_t("reference noises (Table 2)", language),
    )
    ax.set_xlabel(_t(_C_MINUS_A_LABEL, language))
    ax.set_ylabel(_t(_REDUCTION_LABEL, language))
    ax.set_title(_t(_HML_TITLE, language).format(h=high, m=medium, l=low))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_snr_rating(
    result: SNRRatingResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The per-subject ratings the single number was reduced from.

    Draws ``SNRj`` for each test subject as a bar with the mean and the
    reported single number across them, so the spread Formula (19) subtracts
    is visible. Works for
    :class:`~phonometry.hearing.hearing_protectors.SNRRatingResult`.

    :param result: An ``SNR`` rating result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the per-subject bars.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    per_subject = np.asarray(result.subject_snr, dtype=np.float64)
    positions = np.arange(1, per_subject.size + 1)
    bar_kwargs = dict(kwargs)
    style_default(bar_kwargs, "color", _C_PRIMARY)
    bar_kwargs.setdefault("label", _t("per subject", language))
    ax.bar(positions, per_subject, width=0.7, zorder=2, **bar_kwargs)
    ax.axhline(
        result.mean,
        color=_C_SECONDARY,
        ls="--",
        lw=1.6,
        zorder=3,
        label=f"$SNR_m$ = {result.mean:.1f} dB",
    )
    ax.axhline(
        result.reported,
        color=_C_REFERENCE,
        ls="-",
        lw=1.8,
        zorder=3,
        label=f"$SNR_{{{result.performance}}}$ = {result.reported} dB",
    )
    ax.set_xticks(positions)
    ax.set_xlabel(_t(_SUBJECT_LABEL, language))
    ax.set_ylabel(_t(_REDUCTION_LABEL, language))
    ax.set_title(
        _t("ISO 4869-2 single number rating: $SNR$ = {snr} dB", language).format(
            snr=result.reported
        )
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_protected_level(
    result: ProtectedLevelResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The A-weighted band levels the protector leaves at the ear.

    Only the octave-band method sees a spectrum, so this draws its per-band
    result with the total marked. Works for
    :class:`~phonometry.hearing.hearing_protectors.ProtectedLevelResult`.

    :param result: An octave-band protected-level result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the band bars.
    :return: The axes.
    :raises ValueError: for an ``HML`` or ``SNR`` result, which carries no
        spectrum.
    """
    from .._i18n import localize_axes

    if result.band_levels is None or result.frequencies is None:
        msg = (
            f"The {result.method} method has no spectrum to draw: it answers "
            "from the C- and A-weighted levels alone. Only the octave-band "
            "method carries per-band results."
        )
        raise ValueError(msg)
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    positions = np.arange(freqs.size)
    bar_kwargs = dict(kwargs)
    style_default(bar_kwargs, "color", _C_PRIMARY)
    bar_kwargs.setdefault("label", _t("protected band level", language))
    ax.bar(
        positions,
        np.asarray(result.band_levels, dtype=np.float64),
        width=0.7,
        **bar_kwargs,
    )
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(_BAND_LEVEL_LABEL, language))
    performance = result.performance if result.performance is not None else ""
    ax.set_title(
        _t(
            "ISO 4869-2 octave-band method: $L'_{{p,A{x}}}$ = {level} dB", language
        ).format(x=performance, level=result.reported_level)
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


#: IEC 60263, which Clause 6 l) of ISO 4869-1 calls up for the mean
#: attenuation graph: 50 dB on the vertical axis spans one decade on the
#: horizontal one.
_DB_PER_DECADE = 50.0

#: How far the frequency axis runs past the outermost test signal, as a
#: factor, so the end markers are not cut by the frame.
_FREQUENCY_MARGIN = 1.25


def plot_real_ear_attenuation(
    result: RealEarAttenuationResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The mean attenuation of a protector, drawn as ISO 4869-1 Clause 6 l) asks.

    Increasing attenuation points downwards. The individual attenuations are
    drawn faint behind the mean and the expanded uncertainty as bars on it.
    On a figure this creates, the box is shaped so that 50 dB spans one
    decade of frequency (IEC 60263); axes handed in keep their own shape.
    Works for :class:`~phonometry.hearing.real_ear_attenuation.RealEarAttenuationResult`.

    :param result: A real-ear attenuation result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the mean curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    created = ax is None
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    grid = np.asarray(result.attenuation_db, dtype=np.float64)
    mean = np.asarray(result.mean_db, dtype=np.float64)
    expanded = np.asarray(result.expanded_uncertainty_db, dtype=np.float64)
    for index, row in enumerate(grid):
        ax.plot(
            freqs,
            row,
            "-",
            color=_C_MUTED,
            lw=0.8,
            alpha=0.5,
            zorder=1,
            label=_t("individual attenuation", language) if index == 0 else None,
        )
    ax.errorbar(
        freqs,
        mean,
        yerr=expanded,
        fmt="none",
        ecolor=_C_SECONDARY,
        elinewidth=2.0,
        capsize=4,
        zorder=4,
        label=_t(_U95_LABEL, language),
    )
    mean_kwargs = dict(kwargs)
    style_default(mean_kwargs, "color", _C_PRIMARY)
    style_default(mean_kwargs, "linewidth", 2.2)
    mean_kwargs.setdefault("label", _t("mean attenuation $m$", language))
    ax.plot(freqs, mean, "-o", ms=4, zorder=3, **mean_kwargs)
    _freq_axis(ax, freqs, language=language)
    ax.set_xlim(freqs.min() / _FREQUENCY_MARGIN, freqs.max() * _FREQUENCY_MARGIN)
    ax.set_ylabel(_t(_ATTENUATION_LABEL, language))
    ax.invert_yaxis()
    if created:
        low, high = sorted(ax.get_ylim())
        left, right = ax.get_xlim()
        decades = float(np.log10(right / left))
        ax.set_box_aspect(((high - low) / _DB_PER_DECADE) / decades)
    ax.set_title(_t(_REAT_TITLE, language).format(n=result.subjects))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_attenuation_difference(
    result: AttenuationDifferenceResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""Each band's difference of the means against the criterion of Annex B.

    The difference is drawn as a bar and the criterion
    :math:`\sqrt{U_{95,1}^2 + U_{95,2}^2}` as a marked line over it; a bar
    that rises past its marker is a significant difference, hatched and named
    in the legend. Works for
    :class:`~phonometry.hearing.real_ear_attenuation.AttenuationDifferenceResult`.

    :param result: An attenuation difference result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the difference bars.
    :return: The axes.
    """
    from matplotlib.patches import Patch

    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    positions = np.arange(freqs.size)
    bar_kwargs = dict(kwargs)
    style_default(bar_kwargs, "color", _C_PRIMARY)
    bar_kwargs.setdefault(
        "label", _t("difference of the means $|m_1 - m_2|$", language)
    )
    bars = ax.bar(
        positions,
        np.asarray(result.difference_db, dtype=np.float64),
        width=0.6,
        zorder=2,
        **bar_kwargs,
    )
    significant = np.asarray(result.significant, dtype=bool)
    for bar, flagged in zip(bars, significant, strict=True):
        if flagged:
            bar.set_hatch("//")
            bar.set_edgecolor(_C_REFERENCE)
    ax.plot(
        positions,
        np.asarray(result.criterion_db, dtype=np.float64),
        "_",
        color=_C_REFERENCE,
        ms=22,
        mew=2.4,
        zorder=4,
        label=_t(_CRITERION_LABEL, language),
    )
    _band_axis(ax, freqs, xlabel=None, language=language)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(_DIFFERENCE_AXIS_LABEL, language))
    handles, labels = ax.get_legend_handles_labels()
    if np.any(significant):
        bands = ", ".join(
            f"{decimal_comma(f'{f:g}', language)} Hz" for f in freqs[significant]
        )
        title = _t(_DIFFERENCE_TITLE, language).format(bands=bands)
        handles.append(
            Patch(
                facecolor=bars[0].get_facecolor(),
                edgecolor=_C_REFERENCE,
                hatch="//",
            )
        )
        labels.append(_t("significant", language))
    else:
        title = _t(_DIFFERENCE_NONE_TITLE, language)
    ax.set_title(title)
    ax.legend(handles, labels, loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_reat_sound_field(
    result: ReatSoundFieldCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The three sound-field conditions of ISO 4869-1 4.2.2, each on its limit.

    Draws, per test signal, the largest deviation of the six positions from
    the reference point against ±2,5 dB, the absolute difference between the
    right and left positions against 3 dB and, from 500 Hz up, the variation
    a rotated directional microphone saw against the limit Table 1 gives it.
    A check without the rotation is titled as meeting a) only, since b) was
    not judged. Works for
    :class:`~phonometry.hearing.real_ear_attenuation.ReatSoundFieldCheck`.

    :param result: A sound-field check.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the position deviation curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    deviation = np.asarray(result.position_deviation_db, dtype=np.float64)
    worst = deviation[np.argmax(np.abs(deviation), axis=0), np.arange(freqs.size)]
    position_kwargs = dict(kwargs)
    style_default(position_kwargs, "color", _C_PRIMARY)
    style_default(position_kwargs, "linewidth", 2.0)
    position_kwargs.setdefault("label", _t("largest position deviation", language))
    ax.plot(freqs, worst, "-o", ms=4, zorder=3, **position_kwargs)
    for limit in (-2.5, 2.5):
        ax.axhline(
            limit,
            color=_C_PRIMARY,
            ls="--",
            lw=1.0,
            zorder=1,
            label=_t(r"$\pm$2.5 dB limit", language) if limit > 0 else None,
        )
    ax.plot(
        freqs,
        np.asarray(result.left_right_difference_db, dtype=np.float64),
        "-s",
        color=_C_SECONDARY,
        ms=4,
        zorder=3,
        label=_t("difference between right and left", language),
    )
    ax.axhline(
        3.0,
        color=_C_SECONDARY,
        ls=":",
        lw=1.2,
        zorder=1,
        label=_t("3 dB limit", language),
    )
    if result.allowable_variation_db is not None:
        judged = np.isfinite(result.rotation_variation_db)
        ax.plot(
            freqs[judged],
            np.asarray(result.rotation_variation_db, dtype=np.float64)[judged],
            "-^",
            color=_C_TERTIARY,
            ms=5,
            zorder=3,
            label=_t("rotation variation", language),
        )
        ax.axhline(
            result.allowable_variation_db,
            color=_C_TERTIARY,
            ls="-.",
            lw=1.2,
            zorder=1,
            label=_t("Table 1 limit", language),
        )
    _freq_axis(ax, freqs, language=language)
    ax.set_ylabel(_t(_FIELD_AXIS_LABEL, language))
    position_met = bool(np.all(result.uniform) and np.all(result.balanced))
    if result.passes:
        verdict = "qualifies"
    elif position_met and not result.directionality_judged:
        verdict = "a) met, b) not judged"
    else:
        verdict = "does not qualify"
    ax.set_title(_t(_FIELD_TITLE, language).format(verdict=_t(verdict, language)))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_active_insertion_loss(
    result: ActiveInsertionLossResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The mean active insertion loss of an ANR earmuff, ISO 4869-6 Annex A.

    The lower-ear value of every subject is drawn faint behind the mean, and
    the expanded uncertainty of the mean as bars on it. A value below zero is
    a band where the circuit adds sound, and the zero line is drawn so it
    reads that way. Works for
    :class:`~phonometry.hearing.active_noise_reduction.ActiveInsertionLossResult`.

    :param result: An active insertion loss result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the mean curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    grid = np.asarray(result.insertion_loss_db, dtype=np.float64)
    mean = np.asarray(result.mean_db, dtype=np.float64)
    for index, row in enumerate(grid):
        ax.plot(
            freqs,
            row,
            "-",
            color=_C_MUTED,
            lw=0.8,
            alpha=0.5,
            zorder=1,
            label=_t("lower-value ear, per subject", language) if index == 0 else None,
        )
    ax.errorbar(
        freqs,
        mean,
        yerr=np.asarray(result.expanded_uncertainty_db, dtype=np.float64),
        fmt="none",
        ecolor=_C_SECONDARY,
        elinewidth=2.0,
        capsize=4,
        zorder=4,
        label=_t(_U95_LABEL, language),
    )
    mean_kwargs = dict(kwargs)
    style_default(mean_kwargs, "color", _C_PRIMARY)
    style_default(mean_kwargs, "linewidth", 2.2)
    mean_kwargs.setdefault("label", _t("mean active insertion loss", language))
    ax.plot(freqs, mean, "-o", ms=4, zorder=3, **mean_kwargs)
    ax.axhline(0.0, color=_C_EDGE, lw=0.8, zorder=0)
    _freq_axis(ax, freqs, language=language)
    ax.set_ylabel(_t(_AIL_LABEL, language))
    ax.set_title(_t(_AIL_TITLE, language).format(n=result.subjects))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_anr_total_attenuation(
    result: AnrTotalAttenuationResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The passive, active and total attenuation of an ANR earmuff, 5.5.

    Draws, averaged over the subjects in one-third-octave bands, the passive
    attenuation as interpolated in 5.5 a), the lower-ear active insertion loss
    of 5.5 b) and their sum; then the octave-band totals of Formula (1) and
    the assumed protection value at 84 % they reduce to. Works for
    :class:`~phonometry.hearing.active_noise_reduction.AnrTotalAttenuationResult`.

    :param result: A total attenuation result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the mean total attenuation curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    thirds = np.asarray(result.third_octave_frequencies, dtype=np.float64)
    octaves = np.asarray(result.frequencies, dtype=np.float64)
    ax.plot(
        thirds,
        np.mean(result.reat_third_octave_db, axis=0),
        "--",
        color=_C_MUTED,
        lw=1.6,
        zorder=2,
        label=_t("passive (REAT), interpolated", language),
    )
    ax.plot(
        thirds,
        np.mean(result.insertion_loss_db, axis=0),
        ":",
        color=_C_SECONDARY,
        lw=1.8,
        zorder=2,
        label=_t("active insertion loss", language),
    )
    total_kwargs = dict(kwargs)
    style_default(total_kwargs, "color", _C_PRIMARY)
    style_default(total_kwargs, "linewidth", 2.2)
    total_kwargs.setdefault("label", _t("total, one-third octaves", language))
    ax.plot(
        thirds,
        np.mean(result.total_third_octave_db, axis=0),
        "-",
        zorder=3,
        **total_kwargs,
    )
    ax.plot(
        octaves,
        np.asarray(result.assumed_protection.mean_attenuation, dtype=np.float64),
        "o",
        color=_C_PRIMARY,
        ms=6,
        zorder=4,
        label=_t("total, octaves (Formula (1))", language),
    )
    ax.plot(
        octaves,
        np.asarray(result.assumed_protection.apv, dtype=np.float64),
        "s",
        color=_C_REFERENCE,
        ms=6,
        zorder=4,
        label=_t("$APV_{f84}$", language),
    )
    ax.axhline(0.0, color=_C_EDGE, lw=0.8, zorder=0)
    _freq_axis(ax, octaves, language=language)
    ax.set_xlim(thirds.min() / 1.12, thirds.max() * 1.12)
    ax.set_ylabel(_t(_ATTENUATION_LABEL, language))
    high, medium, low = result.hml.reported
    ax.set_title(
        _t(_ANR_TITLE, language).format(
            h=high, m=medium, l=low, snr=result.snr.reported
        )
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_anr_linearity(
    result: AnrLinearityResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Every step at the ear against the 5 dB ± 1 dB of ISO 4869-6 5.4.4.

    Each ear's step is drawn at the external level it ends on, the median over
    the ears as a line, and the tolerance as a band; the highest level up to
    which every step stays inside it is marked. Works for
    :class:`~phonometry.hearing.active_noise_reduction.AnrLinearityResult`.

    :param result: A linearity result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the median step curve.
    :return: The axes.
    """
    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    external = np.asarray(result.external_levels_db, dtype=np.float64)
    upper_ends = external[1:]
    steps = np.diff(external)
    increments = np.asarray(result.increments_db, dtype=np.float64)
    ax.fill_between(
        upper_ends,
        steps - 1.0,
        steps + 1.0,
        color=theme_fill(_C_TERTIARY, ax),
        zorder=0,
        label=_t(r"5 dB $\pm$ 1 dB", language),
    )
    ax.plot(
        np.repeat(upper_ends[None, :], increments.shape[0], axis=0).ravel(),
        increments.ravel(),
        ".",
        color=_C_MUTED,
        ms=4,
        alpha=0.6,
        zorder=2,
        label=_t("each ear", language),
    )
    median_kwargs = dict(kwargs)
    style_default(median_kwargs, "color", _C_PRIMARY)
    style_default(median_kwargs, "linewidth", 2.0)
    median_kwargs.setdefault("label", _t("median over the ears", language))
    ax.plot(
        upper_ends, np.median(increments, axis=0), "-o", ms=4, zorder=3, **median_kwargs
    )
    ax.axvline(
        result.maximum_linear_level_db,
        color=_C_REFERENCE,
        ls="--",
        lw=1.4,
        zorder=1,
        label=_t("highest linear level", language),
    )
    ax.set_xlabel(_t(_EXTERNAL_LEVEL_LABEL, language))
    ax.set_ylabel(_t(_STEP_LABEL, language))
    ax.set_title(
        _t(_LINEARITY_TITLE, language).format(
            level=decimal_comma(f"{result.maximum_linear_level_db:g}", language)
        )
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax
