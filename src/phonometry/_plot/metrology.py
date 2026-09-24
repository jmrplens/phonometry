#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the metrology domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..metrology.conformance import ConformanceVerification
    from ..metrology.data_qualification import (
        LevelCrossingResult,
        PeakStatisticsResult,
        StationarityTestResult,
        TrendTestResult,
    )
    from ..metrology.random_incidence import (
        DiffuseFieldSensitivity,
        DirectivityFactor,
        RandomIncidenceSensitivity,
    )
    from ..metrology.sound_calibrator import (
        SoundCalibratorRequirement,
        SoundCalibratorVerification,
    )
    from ..metrology.uncertainty import MonteCarloResult, UncertaintyResult

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _LEGEND_UPPER_RIGHT,
    _import_pyplot,
    _new_axes,
    format_frequency_axis,
    style_default,
    theme_fill,
)

#: Legend label of the Rice peak-height curve, parameterised by the
#: irregularity factor ``r`` (Bendat & Piersol 5.5.4); the same in both
#: languages.
_RICE_CURVE_LABEL = "Rice ($r$ = {r})"

#: Spanish translations of the fixed strings rendered by the metrology
#: ``.plot()`` renderers, keyed by their verbatim English text. ``_t``
#: returns the English key unchanged for any language other than ``"es"``,
#: so the English output is byte-for-byte identical to the pre-i18n
#: renderers.
#: The legend entry of the acceptance limits in the conformity plots, named
#: once so the translation table and the axes cannot drift apart.
_ACCEPTANCE_LABEL = "Acceptance limit"

_STRINGS: dict[str, str] = {
    r"Contribution to combined uncertainty $|c_i|\,u(x_i)$": r"Contribución a la incertidumbre combinada $|c_i|\,u(x_i)$",
    "GUM uncertainty budget: $y$ = {value}": "Presupuesto de incertidumbre (GUM): $y$ = {value}",
    "{pct} % coverage interval": "Intervalo de cobertura {pct} %",
    "Output quantity $y$": "Magnitud de salida $y$",
    "Probability density": "Densidad de probabilidad",
    "Monte Carlo distribution (GUM Supplement 1): $u(y)$ = {uy}": "Distribución de Monte Carlo (GUM Suplemento 1): $u(y)$ = {uy}",
    "Sample": "Muestra",
    "Segment mean square": "Media cuadrática por segmento",
    "Segment RMS": "RMS por segmento",
    "Segment mean": "Media por segmento",
    "Segment variance": "Varianza por segmento",
    "Sequence median": "Mediana de la secuencia",
    "Segment index": "Índice de segmento",
    "Sample index": "Índice de muestra",
    "Sequence value": "Valor de la secuencia",
    "Trend test (Bendat & Piersol 4.5.2)": "Test de tendencia (Bendat y Piersol 4.5.2)",
    "no trend": "sin tendencia",
    "trend": "tendencia",
    "Stationarity test (Bendat & Piersol 10.3.1.1)": "Test de estacionariedad (Bendat y Piersol 10.3.1.1)",
    "stationary": "estacionario",
    "nonstationary": "no estacionario",
    "Reverse arrangements $A$ = {a}, accept ({lo}, {hi}]: {verdict}": "Inversiones de orden $A$ = {a}, aceptación ({lo}, {hi}]: {verdict}",
    "Runs $r$ = {r}, accept ({lo}, {hi}]: {verdict}": "Rachas $r$ = {r}, aceptación ({lo}, {hi}]: {verdict}",
    "Measured rate": "Tasa medida",
    "Rice expectation (Eq. 5.196)": "Expectativa de Rice (Ec. 5.196)",
    "Level $a$ [signal units]": "Nivel $a$ [unidades de la señal]",
    "Crossings per second [1/s]": "Cruces por segundo [1/s]",
    "Level-crossing rate (Bendat & Piersol 5.5.1)": "Tasa de cruces por nivel (Bendat y Piersol 5.5.1)",
    "Empirical peak exceedance": "Excedencia empírica de picos",
    _RICE_CURVE_LABEL: _RICE_CURVE_LABEL,
    "Rayleigh limit ($r$ = 1)": "Límite de Rayleigh ($r$ = 1)",
    "Gaussian limit ($r$ = 0)": "Límite gaussiano ($r$ = 0)",
    r"Standardized peak height $z = a/\sigma_x$": r"Altura de pico estandarizada $z = a/\sigma_x$",
    "Prob[peak > $z$]": "Prob[pico > $z$]",
    "Peak-height distribution (Bendat & Piersol 5.5.4)": "Distribución de alturas de pico (Bendat y Piersol 5.5.4)",
    "Upper acceptance limit": "Límite de aceptación superior",
    "Lower acceptance limit": "Límite de aceptación inferior",
    "Acceptance limits": "Límites de aceptación",
    _ACCEPTANCE_LABEL: "Límite de aceptación",
    "Conforms": "Conforme",
    "Does not conform": "No conforme",
    "Actual uncertainty": "Incertidumbre real",
    "Maximum-permitted uncertainty": "Incertidumbre máxima permitida",
    "Deviation from design goal [{unit}]": "Desviación respecto al objetivo de diseño [{unit}]",
    "Short-term level fluctuation [{unit}]": "Fluctuación del nivel a corto plazo [{unit}]",
    "Total distortion + noise [{unit}]": "Distorsión total + ruido [{unit}]",
    "Measurement": "Medida",
    "conforms": "conforme",
    "does not conform": "no conforme",
    "Conformance rule of IEC TC 29: {verdict}": "Regla de conformidad del IEC TC 29: {verdict}",
    "Sound calibrator (IEC 60942:2017): {verdict}\nclass {cls} at {freq} Hz": "Calibrador acústico (IEC 60942:2017): {verdict}\nclase {cls} a {freq} Hz",
    "Deviation / acceptance limit": "Desviación / límite de aceptación",
    "Uncertainty / maximum permitted": "Incertidumbre / máxima permitida",
    "Share of the allowance used [%]": "Parte del margen consumida [%]",
    "Past its allowance": "Supera su margen",
    "Whole allowance (100 %)": "Margen completo (100 %)",
    "Generated level": "Nivel generado",
    "Short-term fluctuation": "Fluctuación a corto plazo",
    "Frequency": "Frecuencia",
    "Total distortion + noise": "Distorsión total + ruido",
    "Supply voltage": "Tensión de alimentación",
    "Environmental level": "Nivel en condiciones ambientales",
    "Level in the reference band": "Nivel en la banda de referencia",
    "Environmental frequency": "Frecuencia en condiciones ambientales",
    "Field immunity": "Inmunidad a campos",
    # IEC 61183: random-incidence and diffuse-field sensitivity.
    r"Directional response: $10\,\lg\gamma$ = {di} dB": r"Respuesta direccional: $10\,\lg\gamma$ = {di} dB",
    r"X-Y plane (h), $\alpha$ = 0°": r"Plano X-Y (h), $\alpha$ = 0°",
    r"X-Z plane (v), $\alpha$ = 90°": r"Plano X-Z (v), $\alpha$ = 90°",
    r"Plane $\alpha$ = {alpha}°": r"Plano $\alpha$ = {alpha}°",
    "One plane, rotational symmetry": "Un plano, simetría de revolución",
    r"Weights of the readings: largest element {pct} % of the sphere": r"Pesos de las lecturas: elemento mayor {pct} % de la esfera",
    r"$K(\phi)$ in each plane": r"$K(\phi)$ en cada plano",
    r"$2K(\phi)$, one plane for two": r"$2K(\phi)$, un plano por dos",
    "1/38 for every direction": "1/38 en cada dirección",
    r"Angle of incidence $\phi$ [°]": r"Ángulo de incidencia $\phi$ [°]",
    "Weight [% of the sphere]": "Peso [% de la esfera]",
    r"$G_\mathrm{F}$, free field, reference direction": r"$G_\mathrm{F}$, campo libre, dirección de referencia",
    r"$G_\mathrm{RI}$, random incidence": r"$G_\mathrm{RI}$, incidencia aleatoria",
    r"$G_\mathrm{RI} - G_\mathrm{F} = -10\,\lg\gamma$": r"$G_\mathrm{RI} - G_\mathrm{F} = -10\,\lg\gamma$",
    "Sensitivity level [dB]": "Nivel de sensibilidad [dB]",
    "Correction [dB]": "Corrección [dB]",
    "Random-incidence sensitivity level (IEC 61183)": "Nivel de sensibilidad en incidencia aleatoria (IEC 61183)",
    "Random-incidence correction (IEC 61183)": "Corrección de incidencia aleatoria (IEC 61183)",
    "Frequency [Hz]": "Frecuencia [Hz]",
    r"$G_\mathrm{D}$, instrument under test": r"$G_\mathrm{D}$, instrumento en ensayo",
    r"$G_\mathrm{D,ref}$, reference, Formula (9)": r"$G_\mathrm{D,ref}$, referencia, fórmula (9)",
    r"$G_\mathrm{D,ref}$, reference, Formula (10)": r"$G_\mathrm{D,ref}$, referencia, fórmula (10)",
    r"$G_\mathrm{D,ref}$, reference, Formula (11)": r"$G_\mathrm{D,ref}$, referencia, fórmula (11)",
    r"$\Delta G_\mathrm{D} = L_\mathrm{D} - L_\mathrm{D,ref}$": r"$\Delta G_\mathrm{D} = L_\mathrm{D} - L_\mathrm{D,ref}$",
    "Diffuse-field sensitivity level (IEC 61183)": "Nivel de sensibilidad en campo difuso (IEC 61183)",
}


def _t(text: str, language: str = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


def plot_uncertainty_budget(
    result: UncertaintyResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Bar chart of each input's contribution to the combined uncertainty.

    :param result: An :class:`~phonometry.metrology.uncertainty.UncertaintyResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to :meth:`barh`.
    :return: The axes.
    """
    # The y-axis carries categorical input names (a FixedFormatter), so
    # localize_axes is intentionally not applied here: it would overwrite
    # those labels with comma-formatted tick numbers.
    from .._i18n import decimal_comma, fmt_minus

    ax = ax if ax is not None else _new_axes()
    contributions = np.asarray(result.contributions, dtype=np.float64)
    # The fallback must read exactly like the names combine_uncertainty
    # fills in (``x1``, ``x2``, ...), so a hand-built result and a library
    # one label the same bars the same way.
    names = list(result.names) or [f"x{i + 1}" for i in range(contributions.size)]
    positions = np.arange(contributions.size)
    style_default(kwargs, "color", _C_PRIMARY)
    ax.barh(positions, contributions, **kwargs)
    uc = decimal_comma(f"{result.combined_uncertainty:.3g}", language)
    ax.axvline(
        result.combined_uncertainty,
        color=_C_REFERENCE,
        ls="--",
        label=f"$u_\\mathrm{{c}}$ = {uc}",
    )
    ax.set_yticks(positions)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel(_t(r"Contribution to combined uncertainty $|c_i|\,u(x_i)$", language))
    value = decimal_comma(fmt_minus(result.value, ".4g"), language)
    ax.set_title(_t("GUM uncertainty budget: $y$ = {value}", language, value=value))
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(visible=True, axis="x", alpha=0.3)
    return ax


def plot_monte_carlo(
    result: MonteCarloResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Histogram of the Monte Carlo output with the coverage interval marked.

    :param result: A :class:`~phonometry.metrology.uncertainty.MonteCarloResult`
        obtained with ``keep_samples=True`` (the histogram needs the raw
        output sample).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.hist`.
    :return: The axes.
    :raises ValueError: If the result carries no output samples.
    """
    from .._i18n import decimal_comma, fmt_minus, localize_axes

    if result.samples is None:
        msg = (
            "plot() needs the Monte Carlo output samples; call "
            "monte_carlo(..., keep_samples=True) to retain them."
        )
        raise ValueError(msg)
    ax = ax if ax is not None else _new_axes()
    samples = np.asarray(result.samples, dtype=np.float64)
    style_default(kwargs, "color", _C_PRIMARY_LIGHT)
    kwargs.setdefault("bins", 120)
    kwargs.setdefault("density", True)
    ax.hist(samples, **kwargs)
    low, high = result.interval
    pct = decimal_comma(f"{100.0 * result.coverage:g}", language)
    ax.axvspan(
        low,
        high,
        color=_C_PRIMARY,
        alpha=0.12,
        label=_t("{pct} % coverage interval", language, pct=pct),
    )
    value = decimal_comma(fmt_minus(result.value, ".4g"), language)
    ax.axvline(result.value, color=_C_REFERENCE, ls="--", label=f"$y$ = {value}")
    ax.set_xlabel(_t("Output quantity $y$", language))
    ax.set_ylabel(_t("Probability density", language))
    uy = decimal_comma(f"{result.standard_uncertainty:.3g}", language)
    ax.set_title(
        _t(
            "Monte Carlo distribution (GUM Supplement 1): $u(y)$ = {uy}",
            language,
            uy=uy,
        )
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


_SEGMENT_LABELS = {
    "mean_square": "Segment mean square",
    "rms": "Segment RMS",
    "mean": "Segment mean",
    "variance": "Segment variance",
}


def _trend_verdict_label(
    method: str,
    count: int,
    bounds: tuple[int, int],
    verdict: str,
    language: str,
) -> str:
    """Legend label naming the count, acceptance region and verdict.

    Shared by :func:`plot_trend_test` and :func:`plot_stationarity_test`,
    which draw the same reverse-arrangement / runs statistic against their
    own acceptance region.
    """
    template = (
        "Reverse arrangements $A$ = {a}, accept ({lo}, {hi}]: {verdict}"
        if method == "reverse_arrangements"
        else "Runs $r$ = {r}, accept ({lo}, {hi}]: {verdict}"
    )
    return _t(
        template,
        language,
        a=count,
        r=count,
        lo=bounds[0],
        hi=bounds[1],
        verdict=verdict,
    )


def _draw_sequence_median(ax: Axes, median: float, language: str) -> None:
    """Draw the runs-classification median as a dashed reference line."""
    ax.axhline(
        median,
        color=_C_REFERENCE,
        linestyle="--",
        lw=1.2,
        label=_t("Sequence median", language),
    )


def plot_trend_test(
    result: TrendTestResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Tested sequence against its sample index with the trend-test verdict.

    Draws the sequence of observations ``result.values`` against a plain
    sample index (1 to ``n``) and states the test outcome in the legend:
    the reverse-arrangement count ``A`` (or the run count ``r``), the B&P
    Table A.6 acceptance region and whether the no-trend hypothesis is
    accepted. For the runs test the sequence median is drawn as the
    reference line that classifies each value.

    :param result: A
        :class:`~phonometry.metrology.data_qualification.TrendTestResult`.
    :param ax: Existing axes, or ``None`` for a fresh figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the sequence line.
    :return: The axes.
    """
    from .._i18n import localize_axes

    if ax is None:
        ax = _new_axes()
        ax.set_title(_t("Trend test (Bendat & Piersol 4.5.2)", language))
    verdict = _t("no trend" if result.trend_free else "trend", language)
    label = _trend_verdict_label(
        result.method, result.statistic, result.bounds, verdict, language
    )
    index = np.arange(1, result.n + 1)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.2)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 4.5)
    kwargs.setdefault("label", label)
    ax.plot(index, result.values, **kwargs)
    if result.method == "runs" and result.median is not None:
        # The runs test classifies each value against the median of the
        # *original* sequence (before values equal to it were discarded),
        # so draw that persisted classification median, not a median
        # recomputed on the filtered result.values.
        _draw_sequence_median(ax, result.median, language)
    ax.set_xlabel(_t("Sample index", language))
    ax.set_ylabel(_t("Sequence value", language))
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_stationarity_test(
    result: StationarityTestResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Segment-statistic sequence with the trend-test verdict.

    :param result: A
        :class:`~phonometry.metrology.data_qualification.StationarityTestResult`.
    :param ax: Existing axes, or ``None`` for a fresh figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the segment-value line.
    :return: The axes.
    """
    from .._i18n import localize_axes

    if ax is None:
        ax = _new_axes()
        ax.set_title(_t("Stationarity test (Bendat & Piersol 10.3.1.1)", language))
    verdict = _t("stationary" if result.stationary else "nonstationary", language)
    label = _trend_verdict_label(
        result.method, result.count, result.bounds, verdict, language
    )
    index = np.arange(1, result.n_segments + 1)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.2)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 4.5)
    kwargs.setdefault("label", label)
    ax.plot(index, result.segment_values, **kwargs)
    if result.method == "runs":
        _draw_sequence_median(ax, float(np.median(result.segment_values)), language)
    ax.set_xlabel(_t("Segment index", language))
    ax.set_ylabel(_t(_SEGMENT_LABELS[result.statistic], language))
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_level_crossing_rate(
    result: LevelCrossingResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Measured level-crossing rates against the Rice curve.

    :param result: A
        :class:`~phonometry.metrology.data_qualification.LevelCrossingResult`.
    :param ax: Existing axes, or ``None`` for a fresh figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-rate markers.
    :return: The axes.
    """
    from .._i18n import localize_axes

    if ax is None:
        ax = _new_axes()
        ax.set_title(_t("Level-crossing rate (Bendat & Piersol 5.5.1)", language))
    order = np.argsort(result.levels)
    ax.plot(
        result.levels[order],
        result.rice_rates[order],
        color=_C_REFERENCE,
        lw=1.4,
        label=_t("Rice expectation (Eq. 5.196)", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "ms", 6.0)
    kwargs.setdefault("label", _t("Measured rate", language))
    ax.plot(
        result.levels,
        result.rates,
        "o",
        **kwargs,
    )
    ax.set_yscale("log")
    ax.set_xlabel(_t("Level $a$ [signal units]", language))
    ax.set_ylabel(_t("Crossings per second [1/s]", language))
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_peak_statistics(
    result: PeakStatisticsResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Empirical peak exceedance against the Rice closed forms.

    :param result: A
        :class:`~phonometry.metrology.data_qualification.PeakStatisticsResult`.
    :param ax: Existing axes, or ``None`` for a fresh figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the empirical exceedance line.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes
    from ..metrology.data_qualification import _rice_peak_exceedance

    if ax is None:
        ax = _new_axes()
        ax.set_title(_t("Peak-height distribution (Bendat & Piersol 5.5.4)", language))
    peaks = result.peak_values
    if peaks.size == 0:
        msg = "The record has no local maxima to plot."
        raise ValueError(msg)
    exceedance = 1.0 - np.arange(1, peaks.size + 1) / peaks.size
    z = np.linspace(float(peaks[0]), float(peaks[-1]), 400)
    ax.plot(
        z,
        _rice_peak_exceedance(z, 1.0),
        color=_C_MUTED,
        lw=1.0,
        linestyle="--",
        label=_t("Rayleigh limit ($r$ = 1)", language),
    )
    ax.plot(
        z,
        _rice_peak_exceedance(z, 0.0),
        color=_C_MUTED,
        lw=1.0,
        linestyle=":",
        label=_t("Gaussian limit ($r$ = 0)", language),
    )
    ax.plot(
        z,
        result.peak_exceedance(z),
        color=_C_REFERENCE,
        lw=1.5,
        label=_t(
            _RICE_CURVE_LABEL,
            language,
            r=format_number(
                result.irregularity_factor, language, decimals=3, trim=True
            ),
        ),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.2)
    kwargs.setdefault("label", _t("Empirical peak exceedance", language))
    ax.plot(
        peaks,
        exceedance,
        drawstyle="steps-post",
        **kwargs,
    )
    floor = max(1.0 / peaks.size, 1e-6)
    ax.set_yscale("log")
    ax.set_ylim(bottom=floor)
    ax.set_xlabel(_t(r"Standardized peak height $z = a/\sigma_x$", language))
    ax.set_ylabel(_t("Prob[peak > $z$]", language))
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax


# --------------------------------------------------------------------------
# The conformance rule of IEC TC 29 and the IEC 60942 sound calibrator
# --------------------------------------------------------------------------

#: The requirement names of :data:`phonometry.metrology.CALIBRATOR_REQUIREMENTS`
#: as the figures word them.
_REQUIREMENT_LABELS: dict[str, str] = {
    "level": "Generated level",
    "fluctuation": "Short-term fluctuation",
    "frequency": "Frequency",
    "distortion": "Total distortion + noise",
    "supply_voltage": "Supply voltage",
    "environmental_level": "Environmental level",
    "environmental_level_in_band": "Level in the reference band",
    "environmental_frequency": "Environmental frequency",
    "field_immunity": "Field immunity",
}

#: The requirements whose measured value is a magnitude with a maximum, not a
#: deviation from a design goal, and the quantity their vertical axis names:
#: IEC 60942:2017 bounds |max or min - mean| of the level (5.3.3) and prints a
#: maximum total distortion + noise (Table 7), so neither has a lower limit.
_MAGNITUDE_AXIS_LABELS: dict[str, str] = {
    "fluctuation": "Short-term level fluctuation [{unit}]",
    "distortion": "Total distortion + noise [{unit}]",
}

#: Half the width of the band a maximum-permitted uncertainty is drawn as, in
#: units of the measurement axis, where one measurement takes one unit.
_BAND_HALF_WIDTH = 0.14

#: The share of an allowance at which a bar crosses its limit, in per cent.
_FULL_SHARE = 100.0


def _verdict_word(*, passes: bool, language: str) -> str:
    """``conforms`` or ``does not conform``, localised."""
    return _t("conforms" if passes else "does not conform", language)


def _draw_limits(
    ax: Axes,
    verifications: tuple[ConformanceVerification, ...],
    positions: np.ndarray,
    language: str,
    *,
    one_sided: bool,
) -> None:
    """The acceptance limits: two lines when shared, short bars when not.

    A one-sided requirement, a magnitude with a maximum, has only the upper
    one: its lower bound of zero is not a limit the standard prints.
    """
    lowers = {v.lower_limit for v in verifications}
    uppers = {v.upper_limit for v in verifications}
    if one_sided and len(uppers) == 1:
        ax.axhline(
            next(iter(uppers)),
            color=_C_SECONDARY,
            lw=2.2,
            label=_t(_ACCEPTANCE_LABEL, language),
        )
        return
    if one_sided:
        for k, (x, v) in enumerate(zip(positions, verifications, strict=True)):
            ax.hlines(
                v.upper_limit,
                x - 0.4,
                x + 0.4,
                color=_C_SECONDARY,
                lw=2.2,
                label=_t(_ACCEPTANCE_LABEL, language) if k == 0 else "_nolegend_",
            )
        return
    if len(lowers) == 1 and len(uppers) == 1:
        ax.axhline(
            next(iter(uppers)),
            color=_C_SECONDARY,
            lw=2.2,
            label=_t("Upper acceptance limit", language),
        )
        ax.axhline(
            next(iter(lowers)),
            color=_C_SECONDARY,
            lw=2.2,
            ls="--",
            label=_t("Lower acceptance limit", language),
        )
        return
    for k, (x, v) in enumerate(zip(positions, verifications, strict=True)):
        ax.hlines(
            [v.lower_limit, v.upper_limit],
            x - 0.4,
            x + 0.4,
            color=_C_SECONDARY,
            lw=2.2,
            label=_t("Acceptance limits", language) if k == 0 else "_nolegend_",
        )


def _draw_uncertainties(
    ax: Axes,
    verifications: tuple[ConformanceVerification, ...],
    positions: np.ndarray,
    language: str,
) -> None:
    """The shaded maximum-permitted band and the actual-uncertainty error bar."""
    band = theme_fill(_C_MUTED, ax)
    for k, (x, v) in enumerate(zip(positions, verifications, strict=True)):
        ax.bar(
            x,
            2.0 * v.max_uncertainty,
            bottom=v.deviation - v.max_uncertainty,
            width=2.0 * _BAND_HALF_WIDTH,
            color=band,
            zorder=1,
            label=(
                _t("Maximum-permitted uncertainty", language)
                if k == 0
                else "_nolegend_"
            ),
        )
        ax.errorbar(
            x,
            v.deviation,
            yerr=v.uncertainty,
            fmt="none",
            ecolor=_C_PRIMARY,
            elinewidth=1.6,
            capsize=5,
            zorder=3,
            label=_t("Actual uncertainty", language) if k == 0 else "_nolegend_",
        )


def _draw_verdicts(
    ax: Axes,
    verifications: tuple[ConformanceVerification, ...],
    positions: np.ndarray,
    language: str,
    kwargs: dict[str, Any],
) -> None:
    """A diamond where a measurement conforms and a cross where it does not."""
    shown: set[bool] = set()
    user_label = "label" in kwargs
    for k, (x, v) in enumerate(zip(positions, verifications, strict=True)):
        style = dict(kwargs)
        if v.passes:
            style_default(style, "color", _C_TERTIARY)
            style.setdefault("marker", "D")
            style_default(style, "markersize", 8)
        else:
            style_default(style, "color", _C_REFERENCE)
            style.setdefault("marker", "X")
            style_default(style, "markersize", 10)
        if user_label:
            if k > 0:
                style["label"] = "_nolegend_"
        elif v.passes in shown:
            style["label"] = "_nolegend_"
        else:
            style["label"] = _t(
                "Conforms" if v.passes else "Does not conform", language
            )
            shown.add(v.passes)
        style_default(style, "linestyle", "none")
        ax.plot([x], [v.deviation], zorder=4, **style)


def _draw_conformance(
    ax: Axes,
    verifications: tuple[ConformanceVerification, ...],
    language: str,
    kwargs: dict[str, Any],
    *,
    magnitude_axis_label: str | None = None,
) -> None:
    """The picture of Figure E.1: limits, band, error bar and verdict marker.

    One measurement per unit of the horizontal axis, starting at 1. A
    ``magnitude_axis_label`` marks a one-sided requirement, a magnitude with a
    maximum, and names its vertical axis in place of the deviation from a
    design goal.
    """
    positions = np.arange(1, len(verifications) + 1, dtype=float)
    _draw_limits(
        ax,
        verifications,
        positions,
        language,
        one_sided=magnitude_axis_label is not None,
    )
    _draw_uncertainties(ax, verifications, positions, language)
    _draw_verdicts(ax, verifications, positions, language, kwargs)
    reach = [max(v.uncertainty, v.max_uncertainty) for v in verifications]
    low = min(
        min(v.lower_limit, v.deviation - r)
        for v, r in zip(verifications, reach, strict=True)
    )
    high = max(
        max(v.upper_limit, v.deviation + r)
        for v, r in zip(verifications, reach, strict=True)
    )
    pad = 0.15 * (high - low)
    ax.set_ylim(low - pad, high + 2.6 * pad)
    ax.set_xlim(0.4, len(verifications) + 0.6)
    ax.set_xticks(positions)
    ax.set_xticklabels([str(k) for k in range(1, len(verifications) + 1)])
    unit = verifications[0].unit
    axis_label = magnitude_axis_label or "Deviation from design goal [{unit}]"
    ax.set_ylabel(_t(axis_label, language, unit=unit))
    ax.grid(visible=True, axis="y", alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small", ncols=2)


def plot_conformance_verification(
    result: ConformanceVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """One measured deviation read by the conformance rule of IEC TC 29.

    Drawn the way Figure E.1 of IEC 60942:2017 and Figure C.1 of IEC
    61672-1:2013 draw their examples: the acceptance limits as heavy lines,
    the deviation as a diamond when it conforms and a cross when it does not,
    the actual uncertainty as the error bar and the maximum-permitted one as
    the shaded band behind it.

    :param result: A
        :class:`~phonometry.metrology.conformance.ConformanceVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the verdict marker.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    _draw_conformance(ax, (result,), language, kwargs)
    ax.set_xticks([])
    ax.set_title(
        _t(
            "Conformance rule of IEC TC 29: {verdict}",
            language,
            verdict=_verdict_word(passes=result.passes, language=language),
        )
    )
    localize_axes(ax, language)
    return ax


def _requirement_label(name: str, clause: str, language: str) -> str:
    """``Generated level (§5.3.2)``, localised; the section sign keeps the
    clause number a reference, not a decimal, in the Spanish figures.
    """
    return f"{_t(_REQUIREMENT_LABELS[name], language)} (§{clause})"


def plot_sound_calibrator_requirement(
    result: SoundCalibratorRequirement,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Every measurement of one IEC 60942 requirement against its limits.

    The same picture as :func:`plot_conformance_verification`, one
    measurement per position, with the limits and the maximum-permitted
    uncertainty the class and the nominal frequency select.

    :param result: A
        :class:`~phonometry.metrology.sound_calibrator.SoundCalibratorRequirement`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the verdict markers.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    _draw_conformance(
        ax,
        result.verifications,
        language,
        kwargs,
        magnitude_axis_label=_MAGNITUDE_AXIS_LABELS.get(result.name),
    )
    ax.set_xlabel(_t("Measurement", language))
    verdict = _verdict_word(passes=result.passes, language=language)
    ax.set_title(
        f"{_requirement_label(result.name, result.clause, language)}: {verdict}"
    )
    localize_axes(ax, language)
    return ax


def _allowance_shares(
    result: SoundCalibratorVerification, language: str
) -> tuple[list[str], list[float], list[float], list[ConformanceVerification]]:
    """One label, the two shares in per cent and the verdict, per measurement."""
    labels: list[str] = []
    deviation_share: list[float] = []
    uncertainty_share: list[float] = []
    verdicts: list[ConformanceVerification] = []
    for requirement in result.requirements:
        base = _requirement_label(requirement.name, requirement.clause, language)
        count = len(requirement.verifications)
        for k, v in enumerate(requirement.verifications, start=1):
            labels.append(f"{base} #{k}" if count > 1 else base)
            deviation_share.append(_FULL_SHARE * abs(v.share_of_acceptance_limit))
            uncertainty_share.append(_FULL_SHARE * v.share_of_max_uncertainty)
            verdicts.append(v)
    return labels, deviation_share, uncertainty_share, verdicts


#: The gap between the x label and a legend set below it, in points.
_LEGEND_GAP_PT = 4.0

#: The height of one line of text as a multiple of its font size, generous
#: enough for descenders and for the mathtext of a unit.
_LINE_HEIGHT = 1.3


def _depth_below_axes_pt(ax: Axes) -> float:
    """How far below the axes the tick labels and the x label reach, in points.

    Read from the font sizes and paddings the axis was built with, not from a
    draw, so a legend placed this far down clears the x label whatever the
    height of the figure.
    """
    import matplotlib as mpl

    tick = ax.xaxis.get_major_ticks()[0]
    # The pad a caller set with tick_params, or the one the style gives.
    pad = ax.xaxis.get_tick_params(which="major").get(
        "pad", mpl.rcParams["xtick.major.pad"]
    )
    return (
        tick.get_tick_padding()
        + float(pad)
        + _LINE_HEIGHT * tick.label1.get_fontproperties().get_size_in_points()
        + ax.xaxis.labelpad
        + _LINE_HEIGHT * ax.xaxis.label.get_fontproperties().get_size_in_points()
        + _LEGEND_GAP_PT
    )


def plot_sound_calibrator_verification(
    result: SoundCalibratorVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """How much of each allowance every measurement of a calibrator uses.

    One pair of horizontal bars per measurement: the deviation as a share of
    the acceptance limit on its side, and the actual uncertainty as a share
    of the maximum permitted. A measurement demonstrates conformance when
    both bars stop at or before the dashed 100 % line; a bar whose criterion
    fails is drawn in red, and the legend names both the line and the red.

    :param result: A
        :class:`~phonometry.metrology.sound_calibrator.SoundCalibratorVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the deviation bars.
    :return: The axes.
    :raises ValueError: when no requirement was measured.
    """
    from matplotlib.patches import Patch
    from matplotlib.transforms import ScaledTranslation

    from .._i18n import format_number, localize_axes

    labels, deviation_share, uncertainty_share, verdicts = _allowance_shares(
        result, language
    )
    if not labels:
        msg = "plot() needs at least one measured requirement to draw."
        raise ValueError(msg)
    if ax is None:
        # One row per measurement, and room on the left for the requirement
        # names, which are the whole point of the axis.
        _fig, ax = _import_pyplot().subplots(
            figsize=(9.0, 1.6 + 0.42 * len(labels)), layout="constrained"
        )
    finite = [d for d in deviation_share if np.isfinite(d)]
    ceiling = max([*finite, *uncertainty_share, _FULL_SHARE])
    deviation_share = [d if np.isfinite(d) else 1.1 * ceiling for d in deviation_share]
    y = np.arange(len(labels), dtype=float)
    height = 0.38
    caller_colour = "color" in kwargs or "c" in kwargs
    style = dict(kwargs)
    style_default(style, "color", _C_PRIMARY)
    style.setdefault("label", _t("Deviation / acceptance limit", language))
    bars = ax.barh(y - height / 2, deviation_share, height=height, **style)
    spread = ax.barh(
        y + height / 2,
        uncertainty_share,
        height=height,
        color=_C_SECONDARY,
        label=_t("Uncertainty / maximum permitted", language),
    )
    # The colour follows the verdict, not the share: a deviation that lands on
    # its limit through floating-point arithmetic reads a share a few parts in
    # 10**16 above 100 % and still conforms, and must not be drawn as a failure.
    past = [
        *(
            (bar, v.deviation_within_limits)
            for bar, v in zip(bars, verdicts, strict=True)
            if not caller_colour
        ),
        *(
            (bar, v.uncertainty_within_maximum)
            for bar, v in zip(spread, verdicts, strict=True)
        ),
    ]
    for bar, within in past:
        if not within:
            bar.set_facecolor(_C_REFERENCE)
    full = ax.axvline(
        _FULL_SHARE,
        color=_C_MUTED,
        lw=1.4,
        ls="--",
        label=_t("Whole allowance (100 %)", language),
    )
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(0.0, 1.25 * ceiling)
    ax.set_xlabel(_t("Share of the allowance used [%]", language))
    freq = format_number(result.nominal_frequency_hz, language, decimals=1, trim=True)
    ax.set_title(
        _t(
            "Sound calibrator (IEC 60942:2017): {verdict}\nclass {cls} at {freq} Hz",
            language,
            cls=result.calibrator_class,
            freq=freq,
            verdict=_verdict_word(passes=result.passes, language=language),
        )
    )
    ax.grid(visible=True, axis="x", alpha=0.3)
    handles: list[Any] = [bars, spread]
    if any(not within for _bar, within in past):
        handles.append(
            Patch(facecolor=_C_REFERENCE, label=_t("Past its allowance", language))
        )
    handles.append(full)
    # Below the x label, where no bar can be: inside the axes the legend would
    # sit on whichever requirement happened to be drawn last. The offset is in
    # points, so it clears the label on a figure of one row as on one of
    # twenty.
    below = ScaledTranslation(
        0.0, -_depth_below_axes_pt(ax) / 72.0, ax.figure.dpi_scale_trans
    )
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.0),
        bbox_transform=ax.transAxes + below,
        ncols=2,
        fontsize="small",
        frameon=False,
    )
    localize_axes(ax, language)
    return ax


# ---------------------------------------------------------------------------
# IEC 61183: random-incidence and diffuse-field sensitivity of a sound level
# meter
# ---------------------------------------------------------------------------

#: The colours of the planes of a directivity measurement, in plane order.
_PLANE_COLOURS = (_C_PRIMARY, _C_SECONDARY, _C_TERTIARY, _C_QUATERNARY)

#: The two planes of Annex A, which the legend names by their axes.
_ANNEX_A_PLANES = 2

#: The curve label of the weights view, by the formula the result applied.
_WEIGHT_LABELS = {
    "A.3": r"$K(\phi)$ in each plane",
    "A.4": r"$2K(\phi)$, one plane for two",
    "A.5": "1/38 for every direction",
}

#: The reference-term label of the diffuse-field plot, by route.
_DIFFUSE_REFERENCE_LABELS = {
    "random_incidence": r"$G_\mathrm{D,ref}$, reference, Formula (9)",
    "free_field": r"$G_\mathrm{D,ref}$, reference, Formula (10)",
    "pressure": r"$G_\mathrm{D,ref}$, reference, Formula (11)",
}

#: The smallest radial span of the polar response, in dB below and above the
#: reference level, so a nearly omnidirectional instrument reads as a circle
#: rather than as noise magnified to fill the plot.
_POLAR_FLOOR_DB = -5.0
_POLAR_CEILING_DB = 1.0

#: The legend of the polar response sits below the disc, clear of the angle
#: labels round its rim.
_POLAR_LEGEND_ANCHOR = (0.5, -0.2)

#: The top of the weights view over the largest weight.
_WEIGHTS_HEADROOM = 1.35

#: How far past the outermost radial label the polar range reaches, in radial
#: steps, so the frame circle clears that label.
_POLAR_FRAME_MARGIN = 0.8


def _plane_label(result: DirectivityFactor, plane_angle: float, language: str) -> str:
    """The legend entry of one plane of a directivity measurement."""
    from .._i18n import format_number

    if result.formula == "A.4":
        return _t("One plane, rotational symmetry", language)
    if np.unique(result.plane_angles_deg).size == _ANNEX_A_PLANES:
        if abs(plane_angle) < 1.0:
            return _t(r"X-Y plane (h), $\alpha$ = 0°", language)
        return _t(r"X-Z plane (v), $\alpha$ = 90°", language)
    alpha = format_number(plane_angle, language, decimals=1, trim=True)
    return _t(r"Plane $\alpha$ = {alpha}°", language, alpha=alpha)


def _new_polar() -> Axes:
    """A fresh figure with one polar axes."""
    from typing import cast

    plt = _import_pyplot()
    _fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
    return cast("Axes", ax)


def _plot_directivity_response(
    result: DirectivityFactor, ax: Axes | None, language: str, **kwargs: Any
) -> Axes:
    r"""Polar :math:`L(\phi) - L_\mathrm{rd}`, one closed curve per plane."""
    from matplotlib.ticker import MaxNLocator

    from .._i18n import format_number, localize_axes
    from .electroacoustics import _sign_theta_labels

    if ax is not None and getattr(ax, "name", None) != "polar":
        msg = (
            "'ax' must be a polar axes (subplot_kw={'projection': 'polar'}) for "
            "the response view; pass ax=None to create one."
        )
        raise ValueError(msg)
    ax = ax if ax is not None else _new_polar()
    polar: Any = ax
    polar.set_theta_zero_location("N")
    polar.set_theta_direction(-1)
    _sign_theta_labels(polar)
    relative = np.asarray(result.relative_levels_db, dtype=np.float64)
    angles = np.asarray(result.incidence_angles_deg, dtype=np.float64)
    planes = np.asarray(result.plane_angles_deg, dtype=np.float64)
    for index, plane in enumerate(np.unique(planes)):
        mask = np.isclose(planes, plane)
        order = np.argsort(angles[mask])
        theta = np.radians(angles[mask][order])
        level = relative[mask][order]
        style: dict[str, Any] = dict(kwargs) if index == 0 else {}
        style_default(style, "color", _PLANE_COLOURS[index % len(_PLANE_COLOURS)])
        style_default(style, "lw", 1.5)
        style_default(style, "marker", "o")
        style_default(style, "ms", 2.5)
        style.setdefault("label", _plane_label(result, float(plane), language))
        ax.plot(np.append(theta, theta[0]), np.append(level, level[0]), **style)
    low = min(_POLAR_FLOOR_DB, float(np.floor(relative.min())) - 1.0)
    top = max(0.0, float(np.ceil(relative.max())))
    locator = MaxNLocator(nbins=6, steps=[1, 2, 2.5, 5, 10])
    ticks = np.asarray(locator.tick_values(low, top), dtype=np.float64)
    ticks = ticks[(ticks >= low) & (ticks <= top)]
    step = float(ticks[1] - ticks[0]) if ticks.size > 1 else 1.0
    # The frame of a polar axes is a circle drawn at the top of the radial
    # range, and the outermost radial label sits on its own ray just inside
    # it: the range reaches a fraction of a step past that label, so the
    # frame does not run through it.
    high = max(_POLAR_CEILING_DB, float(ticks[-1]) + _POLAR_FRAME_MARGIN * step)
    ax.set_ylim(low, high)
    ax.set_yticks(ticks)
    ax.tick_params(axis="both", labelsize="x-small")
    ax.grid(visible=True, ls=":", lw=0.4, alpha=0.7)
    di = format_number(result.directivity_index_db, language, decimals=2)
    ax.set_title(
        _t(r"Directional response: $10\,\lg\gamma$ = {di} dB", language, di=di)
    )
    ax.legend(
        loc="lower center",
        bbox_to_anchor=_POLAR_LEGEND_ANCHOR,
        ncol=2,
        fontsize="small",
    )
    localize_axes(ax, language)
    return ax


def _plot_directivity_weights(
    result: DirectivityFactor, ax: Axes | None, language: str, **kwargs: Any
) -> Axes:
    """The weight of each reading of the first plane, in per cent of the sphere."""
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    angles = np.asarray(result.incidence_angles_deg, dtype=np.float64)
    planes = np.asarray(result.plane_angles_deg, dtype=np.float64)
    weights = np.asarray(result.weights, dtype=np.float64)
    first = np.isclose(planes, planes[0])
    order = np.argsort(angles[first])
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.2)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 3.0)
    kwargs.setdefault("label", _t(_WEIGHT_LABELS[result.formula], language))
    ax.plot(angles[first][order], 100.0 * weights[first][order], **kwargs)
    ax.set_xlim(0.0, 360.0)
    ax.set_xticks(np.arange(0.0, 361.0, 45.0))
    # Headroom over the two humps at 90° and 270°, so the legend at the top
    # centre sits over the dip at 180° and covers no reading.
    ax.set_ylim(0.0, _WEIGHTS_HEADROOM * 100.0 * float(np.max(weights)))
    ax.set_xlabel(_t(r"Angle of incidence $\phi$ [°]", language))
    ax.set_ylabel(_t("Weight [% of the sphere]", language))
    pct = format_number(100.0 * result.largest_element, language, decimals=2)
    ax.set_title(
        _t(
            r"Weights of the readings: largest element {pct} % of the sphere",
            language,
            pct=pct,
        )
    )
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc="upper center", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_directivity_factor(
    result: DirectivityFactor,
    ax: Axes | None = None,
    *,
    view: str = "response",
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The directional response or the weights of an IEC 61183 measurement.

    :param result: A
        :class:`~phonometry.metrology.random_incidence.DirectivityFactor`.
    :param ax: Existing axes, or ``None`` to create a figure; the response
        view needs a polar axes.
    :param view: ``"response"`` (polar :math:`L(\phi) - L_\mathrm{rd}`, one
        curve per plane) or ``"weights"`` (the factor of each reading of the
        first plane against its angle).
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the curve of the first plane.
    :return: The axes.
    :raises ValueError: if ``ax`` is not polar for the response view.
    """
    if view == "weights":
        return _plot_directivity_weights(result, ax, language, **kwargs)
    return _plot_directivity_response(result, ax, language, **kwargs)


def plot_random_incidence_sensitivity(
    result: RandomIncidenceSensitivity,
    ax: Axes | None = None,
    *,
    view: str = "levels",
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The IEC 61183 random-incidence sensitivity level against frequency.

    :param result: A
        :class:`~phonometry.metrology.random_incidence.RandomIncidenceSensitivity`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param view: ``"levels"`` (:math:`G_\mathrm{F}` and
        :math:`G_\mathrm{RI}`) or ``"correction"`` (their difference,
        :math:`-10\lg\gamma`).
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the first curve drawn.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    frequencies = np.asarray(result.frequencies_hz, dtype=np.float64)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.5)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 3.0)
    if view == "correction":
        kwargs.setdefault(
            "label", _t(r"$G_\mathrm{RI} - G_\mathrm{F} = -10\,\lg\gamma$", language)
        )
        ax.plot(frequencies, result.correction_db, **kwargs)
        ax.axhline(0.0, color=_C_MUTED, lw=0.8, ls="--")
        ax.set_ylabel(_t("Correction [dB]", language))
        ax.set_title(_t("Random-incidence correction (IEC 61183)", language))
    else:
        kwargs.setdefault(
            "label", _t(r"$G_\mathrm{F}$, free field, reference direction", language)
        )
        ax.plot(frequencies, result.free_field_level_db, **kwargs)
        ax.plot(
            frequencies,
            result.random_incidence_level_db,
            color=_C_REFERENCE,
            lw=1.5,
            marker="s",
            ms=3.0,
            label=_t(r"$G_\mathrm{RI}$, random incidence", language),
        )
        ax.set_ylabel(_t("Sensitivity level [dB]", language))
        ax.set_title(_t("Random-incidence sensitivity level (IEC 61183)", language))
    ax.set_xscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="lower left", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_diffuse_field_sensitivity(
    result: DiffuseFieldSensitivity,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The IEC 61183 diffuse-field sensitivity level against frequency.

    Draws :math:`G_\mathrm{D}` of the instrument under test, the
    diffuse-field sensitivity level of the reference it was compared with,
    and the difference of Formula (8) that joins them.

    :param result: A
        :class:`~phonometry.metrology.random_incidence.DiffuseFieldSensitivity`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the :math:`G_\mathrm{D}` curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    frequencies = np.asarray(result.frequencies_hz, dtype=np.float64)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.5)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 3.0)
    kwargs.setdefault("label", _t(r"$G_\mathrm{D}$, instrument under test", language))
    ax.plot(frequencies, result.diffuse_field_level_db, **kwargs)
    ax.plot(
        frequencies,
        result.reference_diffuse_field_level_db,
        color=_C_SECONDARY,
        lw=1.2,
        ls="--",
        marker="s",
        ms=3.0,
        label=_t(_DIFFUSE_REFERENCE_LABELS[result.route], language),
    )
    ax.plot(
        frequencies,
        result.level_difference_db,
        color=_C_TERTIARY,
        lw=1.2,
        ls=":",
        marker="^",
        ms=3.0,
        label=_t(r"$\Delta G_\mathrm{D} = L_\mathrm{D} - L_\mathrm{D,ref}$", language),
    )
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.set_xscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("Sensitivity level [dB]", language))
    ax.set_title(_t("Diffuse-field sensitivity level (IEC 61183)", language))
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="lower left", fontsize="small")
    localize_axes(ax, language)
    return ax
