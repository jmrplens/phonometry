#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the audiometric test methods (lazy imports from result .plot()).

ISO 8253-1 (the test room, the threshold rules and their uncertainty),
ISO 8253-2 (the sound field) and ISO 4869-3 (the earmuff on its test
fixture).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _new_axes,
    format_frequency_axis,
    place_legend_clear,
    style_default,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..hearing.audiometry import (
        AmbientNoiseCheck,
        AscendingThresholdResult,
        AudiogramCautions,
        AudiometricUncertaintyBudget,
        AutomaticThresholdResult,
        BracketingThresholdResult,
        RetestAgreementCheck,
        SweepThresholdResult,
    )
    from ..hearing.earmuff_insertion_loss import (
        EarmuffInsertionLossResult,
        FixtureIsolationCheck,
        InsertionLossUncertaintyBudget,
        PlaneProgressiveWaveCheck,
    )
    from ..hearing.sound_field_audiometry import (
        DiffuseSoundFieldCheck,
        FreeSoundFieldCheck,
    )

#: Clause 6 of ISO 4869-3 draws an insertion loss on IEC 60263's scale:
#: 50 dB on the vertical axis per decade of frequency.
_DB_PER_DECADE = 50.0
#: The frequency axis runs this factor past the outer bands.
_FREQUENCY_MARGIN = 1.15
#: ISO 8253-2 5.2 b) limits the right-left difference of a free field above
#: this frequency.
_FREE_FIELD_SPLIT_HZ = 4000.0
#: ISO 8253-1 6.2.3.2 Step 3: the agreement a repeat measurement is held to,
#: and the change that sends the test back to further frequencies.
_RETEST_AGREEMENT_DB = 5.0
_RETEST_DISAGREEMENT_DB = 10.0
#: ISO 8253-1 6.2.3.2: the hearing level from which cross-hearing calls for
#: caution.
_CROSS_HEARING_LEVEL_DB = 40.0

_FREQ_LABEL = "Frequency [Hz]"
_LEVEL_LABEL = "Sound pressure level [dB]"
_HEARING_LEVEL_LABEL = "Hearing level [dB]"
_DEVIATION_LABEL = "Level deviation [dB]"
_UNCERTAINTY_LABEL = "Standard uncertainty [dB]"
_IL_LABEL = "Insertion loss [dB]"
_ISOLATION_LABEL = "Acoustic isolation [dB]"
_PRESENTATION_LABEL = "Presentation"
_REVERSAL_LABEL = "Reversal"
_ROOM_TITLE = "ISO {standard} test room, {presentation}: {verdict}"
_ASCENDING_TITLE = "ISO 8253-1 ascending method: {outcome}"
_BRACKETING_TITLE = "ISO 8253-1 bracketing method: threshold {level} dB"
_AUTOMATIC_TITLE = "ISO 8253-1 automatic recording: threshold {level} dB"
_SWEEP_TITLE = "ISO 8253-1 sweep-frequency audiometry"
_RETEST_TITLE = "ISO 8253-1 repeat at {frequency} Hz: {verdict}"
_CAUTIONS_TITLE = "ISO 8253-1 audiogram: {verdict}"
_BUDGET_TITLE = "ISO 8253-1 Annex A: $u$ = {u} dB, $U$ = {big_u} dB"
_IL_BUDGET_TITLE = "ISO 4869-3 Annex B: $u$ = {u} dB, $U$ = {big_u} dB"
_DIFFUSE_TITLE = "{standard} diffuse field: {verdict}"
_RANDOM_INCIDENCE_TITLE = "{standard} random-incidence field: {verdict}"
_FREE_TITLE = "ISO 8253-2 {field} field: {verdict}"
_IL_TITLE = "ISO 4869-3 insertion loss: {n} fittings"
_PLANE_TITLE = "ISO 4869-3 plane progressive wave: {verdict}"
_ISOLATION_TITLE = "ISO 4869-3 fixture isolation: {verdict}"
_THRESHOLD_LABEL = "threshold {level} dB"
#: Words the renderers write more than once, and the presentation of
#: ISO 8253-2, which is also its name in a figure.
_SOUND_FIELD = "sound field"
_QUALIFIES = "qualifies"
_NOT_QUALIFY = "does not qualify"
_RIGHT_LEFT_LABEL = "difference between right and left"
_THREE_DB_LIMIT_LABEL = "3 dB limit"
_PM_U_LABEL = r"$\pm U$"

_STRINGS: dict[str, str] = {
    _FREQ_LABEL: "Frecuencia [Hz]",
    _LEVEL_LABEL: "Nivel de presión sonora [dB]",
    _HEARING_LEVEL_LABEL: "Nivel de audición [dB]",
    _DEVIATION_LABEL: "Desviación del nivel [dB]",
    _UNCERTAINTY_LABEL: "Incertidumbre típica [dB]",
    _IL_LABEL: "Pérdida por inserción [dB]",
    _ISOLATION_LABEL: "Aislamiento acústico [dB]",
    _PRESENTATION_LABEL: "Presentación",
    _REVERSAL_LABEL: "Inversión",
    _ROOM_TITLE: "ISO {standard} sala de ensayo, {presentation}: {verdict}",
    _ASCENDING_TITLE: "ISO 8253-1 método ascendente: {outcome}",
    _BRACKETING_TITLE: "ISO 8253-1 método de horquillado: umbral {level} dB",
    _AUTOMATIC_TITLE: "ISO 8253-1 registro automático: umbral {level} dB",
    _SWEEP_TITLE: "ISO 8253-1 audiometría de barrido en frecuencia",
    _RETEST_TITLE: "ISO 8253-1 repetición a {frequency} Hz: {verdict}",
    _CAUTIONS_TITLE: "ISO 8253-1 audiograma: {verdict}",
    _BUDGET_TITLE: "ISO 8253-1 anexo A: $u$ = {u} dB, $U$ = {big_u} dB",
    _IL_BUDGET_TITLE: "ISO 4869-3 anexo B: $u$ = {u} dB, $U$ = {big_u} dB",
    _DIFFUSE_TITLE: "{standard} campo difuso: {verdict}",
    _RANDOM_INCIDENCE_TITLE: "{standard} campo de incidencia aleatoria: {verdict}",
    _FREE_TITLE: "ISO 8253-2 campo {field}: {verdict}",
    _IL_TITLE: "ISO 4869-3 pérdida por inserción: {n} colocaciones",
    _PLANE_TITLE: "ISO 4869-3 onda plana progresiva: {verdict}",
    _ISOLATION_TITLE: "ISO 4869-3 aislamiento del montaje: {verdict}",
    _THRESHOLD_LABEL: "umbral {level} dB",
    "air conduction": "vía aérea",
    "bone conduction": "vía ósea",
    _SOUND_FIELD: "campo sonoro",
    "free": "libre",
    "quasi-free": "cuasi libre",
    _QUALIFIES: "cumple",
    _NOT_QUALIFY: "no cumple",
    "not judged in every band": "bandas sin evaluar",
    "measured ambient level": "nivel ambiental medido",
    "maximum permissible level": "nivel máximo admisible",
    "exceeds the limit": "supera el límite",
    "threshold {level} dB": "umbral {level} dB",
    "not yet determined": "aún sin determinar",
    "series exhausted": "serie agotada",
    "presentations": "presentaciones",
    "response": "respuesta",
    "no response": "sin respuesta",
    "end of an ascent": "fin de un ascenso",
    "ascent response level": "nivel de respuesta en ascenso",
    "ascents": "ascensos",
    "descents": "descensos",
    "mean of the ascents": "media de los ascensos",
    "mean of the descents": "media de los descensos",
    "tracing": "trazo",
    "ignored reversal": "inversión descartada",
    "mean of the peaks": "media de los picos",
    "mean of the valleys": "media de los valles",
    "reversals": "inversiones",
    "running threshold": "umbral móvil",
    "threshold at the frequency": "umbral en la frecuencia",
    "contribution $u_i$": "contribución $u_i$",
    "combined $u$": "combinada $u$",
    "largest position deviation": "mayor desviación de posición",
    "largest lateral deviation": "mayor desviación lateral",
    r"$\pm$2.5 dB limit": r"límite de $\pm$2,5 dB",
    "lateral tolerance": "tolerancia lateral",
    _RIGHT_LEFT_LABEL: "diferencia entre derecha e izquierda",
    _THREE_DB_LIMIT_LABEL: "límite de 3 dB",
    "directional variation": "variación direccional",
    "Table 1 limit": "límite de la Tabla 1",
    "deviation from the inverse distance law": "desviación de la ley de la inversa de la distancia",
    r"$\pm$1 dB limit": r"límite de $\pm$1 dB",
    "insertion loss per fitting": "pérdida por inserción por colocación",
    "mean insertion loss": "pérdida por inserción media",
    _PM_U_LABEL: _PM_U_LABEL,
    "difference between the end faces": "diferencia entre las caras",
    "2 dB limit": "límite de 2 dB",
    "facing the source less facing away": "hacia la fuente menos de espaldas",
    "10 dB minimum": "mínimo de 10 dB",
    "acoustic isolation": "aislamiento acústico",
    "least isolation (5.1.4)": "aislamiento mínimo (5.1.4)",
    "below the requirement": "por debajo del requisito",
    "band outside the field": "banda fuera del campo",
    "usable from {low} Hz to {high} Hz": "utilizable de {low} Hz a {high} Hz",
    "hearing threshold level": "nivel de umbral de audición",
    "first measurement": "primera medida",
    "repeat": "repetición",
    "agreement to 5 dB": "concordancia de 5 dB",
    "agrees": "concuerda",
    "does not agree": "no concuerda",
    "retest further frequencies": "repetir las demás frecuencias",
    "Measurement": "Medida",
    "air conduction level": "nivel por vía aérea",
    "bone conduction level": "nivel por vía ósea",
    "cross-hearing caution (40 dB)": "precaución por audición cruzada (40 dB)",
    "vibrotactile threshold": "umbral vibrotáctil",
    "calls for caution": "pide precaución",
    "no level calls for caution": "ningún nivel pide precaución",
    "cross-hearing caution": "precaución por audición cruzada",
    "vibrotactile caution": "precaución vibrotáctil",
    "cross-hearing and vibrotactile caution": "precaución por audición cruzada y vibrotáctil",
    "supra-aural": "supraaural",
    "ER-3A": "ER-3A",
    "HDA 200": "HDA 200",
    "own attenuation": "atenuación propia",
}

_PRESENTATION_NAMES = {
    "air": "air conduction",
    "bone": "bone conduction",
    _SOUND_FIELD: _SOUND_FIELD,
}


def _t(text: str, language: str = "en") -> str:
    """Localise a fixed string; English is returned verbatim."""
    return _STRINGS.get(text, text) if language == "es" else text


def _number(value: float, language: str, spec: str = ".1f") -> str:
    """A number formatted for a label, with the locale's decimal separator.

    :param value: The number.
    :param language: ``"en"`` or ``"es"``.
    :param spec: The format specification.
    :return: The formatted text.
    """
    from .._i18n import decimal_comma, fmt_minus

    return decimal_comma(fmt_minus(value, spec), language)


def _finish(ax: Axes, language: str, *, headroom: float = 0.0) -> Axes:
    """Grid, legend and localised ticks, the same on every renderer here.

    :param ax: The axes.
    :param language: ``"en"`` or ``"es"``.
    :param headroom: How much to extend the vertical axis above the data, as
        a fraction of its span, to leave the legend a clear place.
    :return: The axes.
    """
    from .._i18n import localize_axes

    if headroom > 0.0:
        # On an inverted axis the span is negative, so the same step extends
        # the top of the panel either way.
        low, high = ax.get_ylim()
        ax.set_ylim(low, high + headroom * (high - low))
    place_legend_clear(ax.legend(fontsize="small"))
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def _log_frequency_axis(ax: Axes, freqs: np.ndarray, language: str) -> None:
    """A logarithmic frequency axis over the bands, labelled with centres.

    :param ax: The axes.
    :param freqs: The band centres, in hertz.
    :param language: ``"en"`` or ``"es"``.
    """
    ax.set_xscale("log")
    ax.set_xlim(freqs.min() / _FREQUENCY_MARGIN, freqs.max() * _FREQUENCY_MARGIN)
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t(_FREQ_LABEL, language))


def plot_ambient_noise(
    result: AmbientNoiseCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The measured ambient spectrum against the maximum permissible levels.

    Draws the limits of ISO 8253-1 Table 2 or 4, or of ISO 8253-2 Table 2, as
    a dashed line with the adjustments of the check applied, the measured
    one-third-octave levels over them, and a cross on every band that exceeds
    its limit. Works for
    :class:`~phonometry.hearing.audiometry.AmbientNoiseCheck`.

    :param result: An ambient noise check.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured spectrum.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    levels = np.asarray(result.levels_db, dtype=np.float64)
    ax.plot(
        freqs,
        np.asarray(result.limits_db, dtype=np.float64),
        "--",
        color=_C_REFERENCE,
        lw=1.6,
        zorder=2,
        label=_t("maximum permissible level", language),
    )
    measured = dict(kwargs)
    style_default(measured, "color", _C_PRIMARY)
    style_default(measured, "linewidth", 2.0)
    measured.setdefault("label", _t("measured ambient level", language))
    ax.plot(freqs, levels, "-o", ms=4, zorder=3, **measured)
    over = ~np.asarray(result.within, dtype=bool)
    if np.any(over):
        ax.plot(
            freqs[over],
            levels[over],
            "x",
            color=_C_REFERENCE,
            ms=9,
            mew=2.0,
            zorder=4,
            label=_t("exceeds the limit", language),
        )
    _log_frequency_axis(ax, freqs, language)
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    standard = "8253-2" if result.presentation == _SOUND_FIELD else "8253-1"
    verdict = _QUALIFIES if result.passes else _NOT_QUALIFY
    presentation = _t(_PRESENTATION_NAMES[result.presentation], language)
    if result.earphone is not None:
        presentation = f"{presentation} ({_t(result.earphone, language)})"
    ax.set_title(
        _t(_ROOM_TITLE, language).format(
            standard=standard,
            presentation=presentation,
            verdict=_t(verdict, language),
        )
    )
    return _finish(ax, language)


def plot_ascending_threshold(
    result: AscendingThresholdResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The presentations of the ascending method and the threshold they give.

    With the presentation sequence, draws the level of every tone in order,
    filled where it drew a response and open where it did not, with the end
    of each ascent ringed; with the ascents alone, draws the response level of
    each. The threshold, once determined, is a horizontal line. Works for
    :class:`~phonometry.hearing.audiometry.AscendingThresholdResult`.

    :param result: An ascending method result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the presentation staircase.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    line = dict(kwargs)
    style_default(line, "color", _C_PRIMARY)
    style_default(line, "linewidth", 1.4)
    if result.presentation_levels_db is not None and result.responses is not None:
        levels = np.asarray(result.presentation_levels_db, dtype=np.float64)
        heard = np.asarray(result.responses, dtype=bool)
        steps = np.arange(1, levels.size + 1)
        line.setdefault("label", _t("presentations", language))
        ax.plot(steps, levels, "-", zorder=2, **line)
        ax.plot(
            steps[heard],
            levels[heard],
            "o",
            color=_C_PRIMARY,
            ms=7,
            zorder=3,
            label=_t("response", language),
        )
        ax.plot(
            steps[~heard],
            levels[~heard],
            "o",
            mfc="none",
            mec=_C_PRIMARY,
            ms=7,
            zorder=3,
            label=_t("no response", language),
        )
        ends = np.zeros(levels.size, dtype=bool)
        ends[1:] = heard[1:] & ~heard[:-1]
        ax.plot(
            steps[ends],
            levels[ends],
            "o",
            mfc="none",
            mec=_C_SECONDARY,
            mew=2.0,
            ms=13,
            zorder=4,
            label=_t("end of an ascent", language),
        )
        ax.set_xlabel(_t(_PRESENTATION_LABEL, language))
        span = steps
    else:
        ascents = np.asarray(result.ascent_levels_db, dtype=np.float64)
        span = np.arange(1, ascents.size + 1)
        line.setdefault("label", _t("ascent response level", language))
        ax.plot(span, ascents, "-o", zorder=3, **line)
        ax.set_xlabel(_t("ascents", language).capitalize())
    if result.determined:
        level = _number(result.threshold_db, language, "g")
        ax.axhline(
            result.threshold_db,
            color=_C_REFERENCE,
            ls="--",
            lw=1.4,
            zorder=1,
            label=_t(_THRESHOLD_LABEL, language).format(level=level),
        )
        outcome = _t(_THRESHOLD_LABEL, language).format(level=level)
    elif result.series_exhausted:
        outcome = _t("series exhausted", language)
    else:
        outcome = _t("not yet determined", language)
    if span.size:
        ax.set_xticks(span)
    ax.set_ylabel(_t(_HEARING_LEVEL_LABEL, language))
    ax.set_title(_t(_ASCENDING_TITLE, language).format(outcome=outcome))
    return _finish(ax, language, headroom=0.35)


def plot_bracketing_threshold(
    result: BracketingThresholdResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The lowest response levels of the ascents and descents, and the threshold.

    Works for :class:`~phonometry.hearing.audiometry.BracketingThresholdResult`.

    :param result: A bracketing method result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ascents' line.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    ups = np.asarray(result.ascent_levels_db, dtype=np.float64)
    downs = np.asarray(result.descent_levels_db, dtype=np.float64)
    ascent = dict(kwargs)
    style_default(ascent, "color", _C_PRIMARY)
    style_default(ascent, "linewidth", 1.6)
    ascent.setdefault("label", _t("ascents", language))
    ax.plot(np.arange(1, ups.size + 1), ups, "-^", ms=8, zorder=3, **ascent)
    ax.plot(
        np.arange(1, downs.size + 1),
        downs,
        "-v",
        color=_C_SECONDARY,
        lw=1.6,
        ms=8,
        zorder=3,
        label=_t("descents", language),
    )
    ax.axhline(
        result.ascent_mean_db,
        color=_C_PRIMARY,
        ls=":",
        lw=1.2,
        label=_t("mean of the ascents", language),
    )
    ax.axhline(
        result.descent_mean_db,
        color=_C_SECONDARY,
        ls=":",
        lw=1.2,
        label=_t("mean of the descents", language),
    )
    level = _number(result.threshold_db, language, "g")
    ax.axhline(
        result.threshold_db,
        color=_C_REFERENCE,
        ls="--",
        lw=1.6,
        label=_t(_THRESHOLD_LABEL, language).format(level=level),
    )
    ax.set_xticks(np.arange(1, max(ups.size, downs.size) + 1))
    ax.set_xlabel(
        _t("ascents", language).capitalize() + " / " + _t("descents", language)
    )
    ax.set_ylabel(_t(_HEARING_LEVEL_LABEL, language))
    ax.set_title(_t(_BRACKETING_TITLE, language).format(level=level))
    ax.margins(y=0.15)
    return _finish(ax, language, headroom=0.5)


def plot_automatic_threshold(
    result: AutomaticThresholdResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The tracing through its reversals, the averages and the threshold.

    The reversals 6.3.5 a) ignores are drawn grey. Works for
    :class:`~phonometry.hearing.audiometry.AutomaticThresholdResult`.

    :param result: An automatic recording result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the tracing.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    levels = np.asarray(result.reversal_levels_db, dtype=np.float64)
    kept = np.asarray(result.retained, dtype=bool)
    steps = np.arange(1, levels.size + 1)
    trace = dict(kwargs)
    style_default(trace, "color", _C_PRIMARY)
    style_default(trace, "linewidth", 1.6)
    trace.setdefault("label", _t("tracing", language))
    ax.plot(steps, levels, "-", zorder=2, **trace)
    ax.plot(steps[kept], levels[kept], "o", color=_C_PRIMARY, ms=5, zorder=3)
    ax.plot(
        steps[~kept],
        levels[~kept],
        "o",
        color=_C_MUTED,
        ms=7,
        zorder=4,
        label=_t("ignored reversal", language),
    )
    ax.axhline(
        float(np.mean(result.peaks_db)),
        color=_C_SECONDARY,
        ls=":",
        lw=1.2,
        label=_t("mean of the peaks", language),
    )
    ax.axhline(
        float(np.mean(result.valleys_db)),
        color=_C_TERTIARY,
        ls=":",
        lw=1.2,
        label=_t("mean of the valleys", language),
    )
    level = _number(result.threshold_db, language, "g")
    ax.axhline(
        result.threshold_db,
        color=_C_REFERENCE,
        ls="--",
        lw=1.6,
        label=_t(_THRESHOLD_LABEL, language).format(level=level),
    )
    ax.set_xticks(steps)
    ax.set_xlabel(_t(_REVERSAL_LABEL, language))
    ax.set_ylabel(_t(_HEARING_LEVEL_LABEL, language))
    ax.set_title(_t(_AUTOMATIC_TITLE, language).format(level=level))
    return _finish(ax, language, headroom=0.45)


def plot_sweep_threshold(
    result: SweepThresholdResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The sweep tracing, its running threshold and the thresholds found.

    Hearing level grows downwards, as on an audiogram. Works for
    :class:`~phonometry.hearing.audiometry.SweepThresholdResult`.

    :param result: A sweep-frequency result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the running threshold.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    reversal_f = np.asarray(result.reversal_frequencies, dtype=np.float64)
    ax.plot(
        reversal_f,
        np.asarray(result.reversal_levels_db, dtype=np.float64),
        "-",
        color=_C_MUTED,
        lw=1.0,
        zorder=1,
        label=_t("tracing", language),
    )
    running = dict(kwargs)
    style_default(running, "color", _C_PRIMARY)
    style_default(running, "linewidth", 2.0)
    running.setdefault("label", _t("running threshold", language))
    ax.plot(
        np.asarray(result.running_frequencies, dtype=np.float64),
        np.asarray(result.running_threshold_db, dtype=np.float64),
        "-",
        zorder=2,
        **running,
    )
    ax.plot(
        np.asarray(result.frequencies, dtype=np.float64),
        np.asarray(result.threshold_db, dtype=np.float64),
        "s",
        color=_C_REFERENCE,
        ms=7,
        zorder=3,
        label=_t("threshold at the frequency", language),
    )
    everything = np.concatenate([reversal_f, np.asarray(result.frequencies)])
    _log_frequency_axis(ax, everything, language)
    ax.set_ylabel(_t(_HEARING_LEVEL_LABEL, language))
    ax.invert_yaxis()
    ax.set_title(_t(_SWEEP_TITLE, language))
    return _finish(ax, language)


def plot_retest_agreement(
    result: RetestAgreementCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The first and the repeat measurement, and the 5 dB either side.

    Draws the two hearing threshold levels side by side over a band 5 dB
    either side of the first, the agreement ISO 8253-1 6.2.3.2 Step 3 asks
    for. Works for
    :class:`~phonometry.hearing.audiometry.RetestAgreementCheck`.

    :param result: A retest agreement check.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the two measurements' markers.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    first = float(result.first_db)
    ax.axhspan(
        first - _RETEST_AGREEMENT_DB,
        first + _RETEST_AGREEMENT_DB,
        color=_C_SECONDARY,
        alpha=0.15,
        zorder=1,
        label=_t("agreement to 5 dB", language),
    )
    marks = dict(kwargs)
    style_default(marks, "color", _C_PRIMARY)
    style_default(marks, "linewidth", 1.4)
    marks.setdefault("label", _t("hearing threshold level", language))
    ax.plot([0, 1], [first, float(result.repeat_db)], "-o", ms=9, zorder=3, **marks)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([_t("first measurement", language), _t("repeat", language)])
    ax.set_xlim(-0.5, 1.5)
    low = min(first, float(result.repeat_db)) - _RETEST_DISAGREEMENT_DB
    high = max(first, float(result.repeat_db)) + _RETEST_DISAGREEMENT_DB
    ax.set_ylim(low, high)
    ax.set_xlabel(_t("Measurement", language))
    ax.set_ylabel(_t(_HEARING_LEVEL_LABEL, language))
    if result.passes:
        verdict = "agrees"
    elif result.retest_further_frequencies:
        verdict = "retest further frequencies"
    else:
        verdict = "does not agree"
    ax.set_title(
        _t(_RETEST_TITLE, language).format(
            frequency=_number(result.frequency_hz, language, "g"),
            verdict=_t(verdict, language),
        )
    )
    return _finish(ax, language, headroom=0.35)


def plot_audiogram_cautions(
    result: AudiogramCautions,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """An audiogram with the levels ISO 8253-1 asks to treat with caution.

    Hearing level grows downwards, as on an audiogram. The air-conduction
    levels are drawn against the 40 dB of cross-hearing (6.2.3.2), the
    bone-conduction levels against the average vibrotactile threshold of 8.4
    where it gives one, and every level flagged by either rule is crossed.
    Works for :class:`~phonometry.hearing.audiometry.AudiogramCautions`.

    :param result: The cautions of an audiogram.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the air-conduction curve.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    flagged_f: list[np.ndarray] = []
    flagged_l: list[np.ndarray] = []
    if result.air_conduction_db is not None:
        air = np.asarray(result.air_conduction_db, dtype=np.float64)
        curve = dict(kwargs)
        style_default(curve, "color", _C_PRIMARY)
        style_default(curve, "linewidth", 2.0)
        curve.setdefault("label", _t("air conduction level", language))
        ax.plot(freqs, air, "-o", ms=6, zorder=3, **curve)
        ax.axhline(
            _CROSS_HEARING_LEVEL_DB,
            color=_C_PRIMARY,
            ls=":",
            lw=1.2,
            zorder=1,
            label=_t("cross-hearing caution (40 dB)", language),
        )
        flagged_f.append(freqs[result.cross_hearing])
        flagged_l.append(air[result.cross_hearing])
    if result.bone_conduction_db is not None:
        bone = np.asarray(result.bone_conduction_db, dtype=np.float64)
        ax.plot(
            freqs,
            bone,
            "--s",
            color=_C_TERTIARY,
            lw=1.6,
            ms=6,
            zorder=3,
            label=_t("bone conduction level", language),
        )
        tactile = np.asarray(result.vibrotactile_levels_db, dtype=np.float64)
        given = np.isfinite(tactile)
        if np.any(given):
            ax.plot(
                freqs[given],
                tactile[given],
                "_",
                color=_C_TERTIARY,
                ms=18,
                mew=2.0,
                zorder=2,
                label=_t("vibrotactile threshold", language),
            )
        flagged_f.append(freqs[result.vibrotactile])
        flagged_l.append(bone[result.vibrotactile])
    cross_f = np.concatenate(flagged_f)
    if cross_f.size:
        ax.plot(
            cross_f,
            np.concatenate(flagged_l),
            "x",
            color=_C_REFERENCE,
            ms=11,
            mew=2.0,
            zorder=4,
            label=_t("calls for caution", language),
        )
    _log_frequency_axis(ax, freqs, language)
    ax.set_ylabel(_t(_HEARING_LEVEL_LABEL, language))
    ax.invert_yaxis()
    hearing = bool(np.any(result.cross_hearing))
    tactile_flag = bool(np.any(result.vibrotactile))
    if hearing and tactile_flag:
        verdict = "cross-hearing and vibrotactile caution"
    elif hearing:
        verdict = "cross-hearing caution"
    elif tactile_flag:
        verdict = "vibrotactile caution"
    else:
        verdict = "no level calls for caution"
    ax.set_title(_t(_CAUTIONS_TITLE, language).format(verdict=_t(verdict, language)))
    return _finish(ax, language, headroom=0.35)


def _plot_budget(
    ax: Axes,
    labels: list[str],
    values: tuple[float, ...],
    combined: float,
    title: str,
    language: str,
    kwargs: dict[str, Any],
) -> Axes:
    """Bars of an uncertainty budget's components, with the combined value.

    :param ax: The axes.
    :param labels: The symbols of the components, as mathtext.
    :param values: Their standard uncertainties, in dB.
    :param combined: The combined standard uncertainty, in dB.
    :param title: The title, already localised and formatted.
    :param language: ``"en"`` or ``"es"``.
    :param kwargs: Forwarded to the bars.
    :return: The axes.
    """
    positions = np.arange(len(values), dtype=np.float64)
    bars = dict(kwargs)
    style_default(bars, "color", _C_PRIMARY)
    bars.setdefault("label", _t("contribution $u_i$", language))
    ax.bar(positions, values, width=0.6, zorder=2, **bars)
    ax.axhline(
        combined,
        color=_C_REFERENCE,
        ls="--",
        lw=1.6,
        zorder=3,
        label=_t("combined $u$", language),
    )
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel(_t(_UNCERTAINTY_LABEL, language))
    ax.set_ylim(0.0, combined * 1.25)
    ax.set_title(title)
    return _finish(ax, language)


def plot_audiometric_uncertainty(
    result: AudiometricUncertaintyBudget,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The eight contributions of Table A.1 as bars, the combined value on top.

    The title gives :math:`u` to 0,1 dB and :math:`U` to the nearest full
    decibel, as A.6 reports it.

    Works for :class:`~phonometry.hearing.audiometry.AudiometricUncertaintyBudget`.

    :param result: An audiometric uncertainty budget.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the contribution bars.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    labels = [
        r"$L'_\mathrm{HT}$",
        r"$\delta_\mathrm{eq}$",
        r"$\delta_\mathrm{tr}$",
        r"$\delta_\mathrm{n}$",
        r"$\delta_\mathrm{m}$",
        r"$\delta_\mathrm{te}$",
        r"$\delta_\mathrm{su}$",
        r"$\delta_\mathrm{pr}$",
    ]
    # A.6 reports the expanded uncertainty rounded to the nearest full
    # decibel, as Table A.2 prints it (U = 10 dB for u = 4,9 dB).
    title = _t(_BUDGET_TITLE, language).format(
        u=_number(result.combined_db, language),
        big_u=_number(result.expanded_db, language, ".0f"),
    )
    return _plot_budget(
        ax, labels, result.components_db, result.combined_db, title, language, kwargs
    )


def plot_insertion_loss_uncertainty(
    result: InsertionLossUncertaintyBudget,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The five contributions of Table B.1 as bars, the combined value on top.

    Works for
    :class:`~phonometry.hearing.earmuff_insertion_loss.InsertionLossUncertaintyBudget`.

    :param result: An insertion loss uncertainty budget.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the contribution bars.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    labels = [
        r"$L_\mathrm{open}$",
        r"$L_\mathrm{occl}$",
        r"$\delta_1$",
        r"$\delta_2$",
        r"$\delta_3$",
    ]
    title = _t(_IL_BUDGET_TITLE, language).format(
        u=_number(result.combined_db, language),
        big_u=_number(result.expanded_db, language),
    )
    return _plot_budget(
        ax, labels, result.components_db, result.combined_db, title, language, kwargs
    )


def plot_diffuse_sound_field(
    result: DiffuseSoundFieldCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The two conditions of a diffuse field, each against its limit.

    Draws, per band, the largest deviation of the six positions from the
    reference point against ±2,5 dB, the difference between the right and
    left positions against 3 dB and, from 500 Hz up, the variation the
    directional microphone read against the limit Table 1 gives it. Works for
    :class:`~phonometry.hearing.sound_field_audiometry.DiffuseSoundFieldCheck`.

    :param result: A diffuse-field check.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the position deviation curve.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    deviation = np.asarray(result.position_deviation_db, dtype=np.float64)
    worst = deviation[np.argmax(np.abs(deviation), axis=0), np.arange(freqs.size)]
    position = dict(kwargs)
    style_default(position, "color", _C_PRIMARY)
    style_default(position, "linewidth", 2.0)
    position.setdefault("label", _t("largest position deviation", language))
    ax.plot(freqs, worst, "-o", ms=4, zorder=3, **position)
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
        label=_t(_RIGHT_LEFT_LABEL, language),
    )
    ax.axhline(
        3.0,
        color=_C_SECONDARY,
        ls=":",
        lw=1.2,
        zorder=1,
        label=_t(_THREE_DB_LIMIT_LABEL, language),
    )
    variation = np.asarray(result.directional_variation_db, dtype=np.float64)
    allowed = np.asarray(result.allowable_variation_db, dtype=np.float64)
    read = np.isfinite(variation)
    if np.any(read):
        ax.plot(
            freqs[read],
            variation[read],
            "-^",
            color=_C_TERTIARY,
            ms=5,
            zorder=3,
            label=_t("directional variation", language),
        )
        limited = np.isfinite(allowed)
        ax.plot(
            freqs[limited],
            allowed[limited],
            "_",
            color=_C_TERTIARY,
            ms=16,
            mew=2.0,
            zorder=2,
            label=_t("Table 1 limit", language),
        )
    _log_frequency_axis(ax, freqs, language)
    ax.set_ylabel(_t(_DEVIATION_LABEL, language))
    if result.passes:
        verdict = _QUALIFIES
    elif (
        np.all(result.uniform)
        and np.all(result.balanced)
        and not result.directionality_judged
    ):
        verdict = "not judged in every band"
    else:
        verdict = _NOT_QUALIFY
    # ISO 4869-3 calls the same field a random-incidence field (5.2.2). The
    # title names the standard and leaves the clause to the text, as the
    # free-field title does: a clause number such as 5.3 would otherwise sit
    # where a decimal is expected.
    title = (
        _RANDOM_INCIDENCE_TITLE
        if result.standard.startswith("ISO 4869-3")
        else _DIFFUSE_TITLE
    )
    designation = " ".join(result.standard.split()[:2])
    ax.set_title(
        _t(title, language).format(standard=designation, verdict=_t(verdict, language))
    )
    return _finish(ax, language, headroom=0.45)


def plot_free_sound_field(
    result: FreeSoundFieldCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The lateral and axial conditions of a free or quasi-free field.

    Draws, per band, the largest lateral deviation against its tolerance, the
    deviation of the axial difference from the inverse distance law against
    ±1 dB and, for a free field above 4 kHz, the right-left difference against
    3 dB. A band that fails a requirement is crossed on that requirement's
    curve. Works for
    :class:`~phonometry.hearing.sound_field_audiometry.FreeSoundFieldCheck`.

    :param result: A free or quasi-free field check.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the lateral deviation curve.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    deviation = np.asarray(result.lateral_deviation_db, dtype=np.float64)
    worst = deviation[np.argmax(np.abs(deviation), axis=0), np.arange(freqs.size)]
    lateral = dict(kwargs)
    style_default(lateral, "color", _C_PRIMARY)
    style_default(lateral, "linewidth", 2.0)
    lateral.setdefault("label", _t("largest lateral deviation", language))
    ax.plot(freqs, worst, "-o", ms=4, zorder=3, **lateral)
    tolerance = np.asarray(result.lateral_tolerance_db, dtype=np.float64)
    ax.step(
        freqs,
        tolerance,
        where="mid",
        color=_C_PRIMARY,
        ls="--",
        lw=1.0,
        zorder=1,
        label=_t("lateral tolerance", language),
    )
    ax.step(freqs, -tolerance, where="mid", color=_C_PRIMARY, ls="--", lw=1.0, zorder=1)
    ax.plot(
        freqs,
        np.asarray(result.inverse_distance_deviation_db, dtype=np.float64),
        "-s",
        color=_C_TERTIARY,
        ms=4,
        zorder=3,
        label=_t("deviation from the inverse distance law", language),
    )
    for limit in (-1.0, 1.0):
        ax.axhline(
            limit,
            color=_C_TERTIARY,
            ls=":",
            lw=1.2,
            zorder=1,
            label=_t(r"$\pm$1 dB limit", language) if limit > 0 else None,
        )
    axial = np.asarray(result.inverse_distance_deviation_db, dtype=np.float64)
    difference = np.asarray(result.left_right_difference_db, dtype=np.float64)
    if result.field == "free":
        high = freqs > _FREE_FIELD_SPLIT_HZ
        if np.any(high):
            ax.plot(
                freqs[high],
                difference[high],
                "-D",
                color=_C_SECONDARY,
                ms=4,
                zorder=3,
                label=_t(_RIGHT_LEFT_LABEL, language),
            )
            ax.plot(
                freqs[high],
                np.full(int(np.sum(high)), 3.0),
                "-.",
                color=_C_SECONDARY,
                lw=1.0,
                zorder=1,
                label=_t(_THREE_DB_LIMIT_LABEL, language),
            )
    # Each failing band is crossed on the curve of the requirement it fails,
    # so a cross never sits on a value inside its own tolerance.
    crossed = [
        (freqs[~result.uniform], worst[~result.uniform]),
        (
            freqs[~result.follows_inverse_distance_law],
            axial[~result.follows_inverse_distance_law],
        ),
        (freqs[~result.balanced], difference[~result.balanced]),
    ]
    cross_f = np.concatenate([f for f, _ in crossed])
    if cross_f.size:
        ax.plot(
            cross_f,
            np.concatenate([level for _, level in crossed]),
            "x",
            color=_C_REFERENCE,
            ms=9,
            mew=2.0,
            zorder=4,
            label=_t("band outside the field", language),
        )
    _log_frequency_axis(ax, freqs, language)
    ax.set_ylabel(_t(_DEVIATION_LABEL, language))
    ax.set_title(
        _t(_FREE_TITLE, language).format(
            field=_t(result.field, language),
            verdict=_free_field_verdict(result, language),
        )
    )
    return _finish(ax, language, headroom=0.6)


def _free_field_verdict(result: FreeSoundFieldCheck, language: str) -> str:
    """The verdict a free or quasi-free field's title states.

    A quasi-free field that meets its requirements over an unbroken run of the
    bands up to the top one is usable there (ISO 8253-2 5.4), and the title
    says from where; otherwise it qualifies or it does not.

    :param result: The check.
    :param language: ``"en"`` or ``"es"``.
    :return: The localised verdict.
    """
    from .._i18n import decimal_comma

    if result.passes:
        return _t(_QUALIFIES, language)
    compliant = np.asarray(result.compliant, dtype=bool)
    usable = result.distance_adequate and compliant[-1]
    if result.field == "quasi-free" and usable:
        first = int(compliant.size - np.argmin(compliant[::-1]))
        if np.all(compliant[first:]):
            low = decimal_comma(f"{float(result.frequencies[first]):g}", language)
            high = decimal_comma(f"{float(result.frequencies[-1]):g}", language)
            return _t("usable from {low} Hz to {high} Hz", language).format(
                low=low, high=high
            )
    return _t(_NOT_QUALIFY, language)


def plot_earmuff_insertion_loss(
    result: EarmuffInsertionLossResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The insertion loss of an earmuff, drawn as ISO 4869-3 Clause 6 asks.

    Increasing insertion loss points downwards and 50 dB span one decade of
    frequency (IEC 60263). Clause 6 asks both of every graph, so the axes'
    box takes that aspect whether this creates them or they are passed in.
    Each fitting is drawn faint behind the mean, and the expanded uncertainty
    as bars on it. Works for
    :class:`~phonometry.hearing.earmuff_insertion_loss.EarmuffInsertionLossResult`.

    :param result: An insertion loss result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the mean insertion loss curve.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    for index, row in enumerate(
        np.asarray(result.repetition_insertion_loss_db, dtype=np.float64)
    ):
        ax.plot(
            freqs,
            row,
            "-",
            color=_C_MUTED,
            lw=0.8,
            alpha=0.6,
            zorder=1,
            label=_t("insertion loss per fitting", language) if index == 0 else None,
        )
    mean = np.asarray(result.insertion_loss_db, dtype=np.float64)
    ax.errorbar(
        freqs,
        mean,
        yerr=np.asarray(result.expanded_uncertainty_db, dtype=np.float64),
        fmt="none",
        ecolor=_C_SECONDARY,
        elinewidth=1.6,
        capsize=3,
        zorder=4,
        label=_t(_PM_U_LABEL, language),
    )
    curve = dict(kwargs)
    style_default(curve, "color", _C_PRIMARY)
    style_default(curve, "linewidth", 2.2)
    curve.setdefault("label", _t("mean insertion loss", language))
    ax.plot(freqs, mean, "-o", ms=4, zorder=3, **curve)
    _log_frequency_axis(ax, freqs, language)
    ax.set_ylabel(_t(_IL_LABEL, language))
    ax.invert_yaxis()
    low, high = sorted(ax.get_ylim())
    left, right = ax.get_xlim()
    decades = float(np.log10(right / left))
    ax.set_box_aspect(((high - low) / _DB_PER_DECADE) / decades)
    ax.set_title(_t(_IL_TITLE, language).format(n=result.repetitions))
    return _finish(ax, language)


def plot_plane_progressive_wave(
    result: PlaneProgressiveWaveCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The two conditions of a plane progressive wave, each on its limit.

    Works for
    :class:`~phonometry.hearing.earmuff_insertion_loss.PlaneProgressiveWaveCheck`.

    :param result: A plane progressive wave check.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the end-face difference curve.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    faces = dict(kwargs)
    style_default(faces, "color", _C_PRIMARY)
    style_default(faces, "linewidth", 2.0)
    faces.setdefault("label", _t("difference between the end faces", language))
    ax.plot(
        freqs,
        np.asarray(result.end_face_difference_db, dtype=np.float64),
        "-o",
        ms=4,
        zorder=3,
        **faces,
    )
    ax.axhline(
        2.0,
        color=_C_PRIMARY,
        ls="--",
        lw=1.0,
        zorder=1,
        label=_t("2 dB limit", language),
    )
    margin = np.asarray(result.front_to_back_db, dtype=np.float64)
    read = np.isfinite(margin)
    if np.any(read):
        ax.plot(
            freqs[read],
            margin[read],
            "-^",
            color=_C_TERTIARY,
            ms=5,
            zorder=3,
            label=_t("facing the source less facing away", language),
        )
        ax.axhline(
            10.0,
            color=_C_TERTIARY,
            ls=":",
            lw=1.2,
            zorder=1,
            label=_t("10 dB minimum", language),
        )
    _log_frequency_axis(ax, freqs, language)
    ax.set_ylabel(_t(_DEVIATION_LABEL, language))
    verdict = _QUALIFIES if result.passes else _NOT_QUALIFY
    ax.set_title(_t(_PLANE_TITLE, language).format(verdict=_t(verdict, language)))
    return _finish(ax, language)


def plot_fixture_isolation(
    result: FixtureIsolationCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The fixture's acoustic isolation against the least 5.1.4 asks.

    Works for
    :class:`~phonometry.hearing.earmuff_insertion_loss.FixtureIsolationCheck`.

    :param result: A fixture isolation check.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the isolation curve.
    :return: The axes.
    """
    from .._i18n import check_language

    check_language(language)
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    required = np.asarray(result.required_db, dtype=np.float64)
    ax.step(
        freqs,
        required,
        where="mid",
        color=_C_REFERENCE,
        ls="--",
        lw=1.6,
        zorder=2,
        label=_t("least isolation (5.1.4)", language),
    )
    curve = dict(kwargs)
    style_default(curve, "color", _C_PRIMARY)
    style_default(curve, "linewidth", 2.0)
    curve.setdefault("label", _t("acoustic isolation", language))
    isolation = np.asarray(result.isolation_db, dtype=np.float64)
    ax.plot(freqs, isolation, "-o", ms=4, zorder=3, **curve)
    short = ~np.asarray(result.sufficient, dtype=bool)
    if np.any(short):
        ax.plot(
            freqs[short],
            isolation[short],
            "x",
            color=_C_REFERENCE,
            ms=9,
            mew=2.0,
            zorder=4,
            label=_t("below the requirement", language),
        )
    _log_frequency_axis(ax, freqs, language)
    ax.set_ylabel(_t(_ISOLATION_LABEL, language))
    verdict = _QUALIFIES if result.passes else _NOT_QUALIFY
    ax.set_title(_t(_ISOLATION_TITLE, language).format(verdict=_t(verdict, language)))
    return _finish(ax, language)
