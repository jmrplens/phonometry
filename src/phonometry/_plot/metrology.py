#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the metrology domain (lazy imports from result .plot())."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.axes import Axes
    from matplotlib.ticker import FuncFormatter
    from numpy.typing import NDArray

    from ..metrology.comparison_calibration import (
        ComparisonCalibration,
        ComparisonUncertaintyBudget,
        EnvironmentalSensitivityCorrection,
        FreeFieldRegion,
        JigDiameterCorrection,
    )
    from ..metrology.conformance import ConformanceVerification
    from ..metrology.data_qualification import (
        LevelCrossingResult,
        PeakStatisticsResult,
        StationarityTestResult,
        TrendTestResult,
    )
    from ..metrology.free_field_corrections import (
        AdjustmentValue,
        CorrectionUncertaintyBudget,
        CorrectionUncertaintyVerification,
        FreeFieldCorrection,
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
    from ..metrology.sound_level_meter import (
        SoundLevelMeterPeriodicRequirement,
        SoundLevelMeterPeriodicVerification,
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
    place_legend_clear,
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
#: Legend entry of the acceptance limits of several requirements at once.
_ACCEPTANCE_LIMITS_LABEL = "Acceptance limits"

#: Labels the IEC 61183 and IEC 62585 plots share with the translation table,
#: written once.
_RI_CORRECTION_LABEL = r"$G_\mathrm{RI} - G_\mathrm{F} = -10\,\lg\gamma$"
_SENSITIVITY_LEVEL_LABEL = "Sensitivity level [dB]"
_FREQUENCY_LABEL = "Frequency [Hz]"
_DIFFUSE_DEVIATION_LABEL = r"$\Delta G_\mathrm{D} = L_\mathrm{D} - L_\mathrm{D,ref}$"
_CORRECTION_AXIS_LABEL = "Correction [dB]"
_REFERENCE_MIC_LABEL = r"$C_\mathrm{FF,RM}$, reference microphone"

#: The axis of the uncertainty budgets of IEC 62585 Annex I, IEC 61094-5
#: Table D.1 and IEC 61094-8 Table 2, written once.
_STANDARD_UNCERTAINTY_LABEL = r"Standard uncertainty $u_i$ [dB]"

#: The legend entry of a periodic-test result IEC 61672-3:2013 4.3 forbids
#: using, and the title of one requirement's figure: the clause and its
#: verdict, then the clause's heading as it reads, on a line of its own so
#: that the longest heading fits the default figure in either language.
_SLM_UNUSABLE_LABEL = "Unusable (§4.3)"
_SLM_PERIODIC_TITLE = "IEC 61672-3 §{clause}: {verdict}\n{title}"

#: The verdict words a requirement's figure and the conformance figures read.
_CONFORMS = "conforms"
_DOES_NOT_CONFORM = "does not conform"

#: How the verdict figure names a graded clause the record does not hold: one
#: a complete test needs, one the declared features take out (8.1), and one
#: whose feature is neither declared nor shown.
_SLM_NOT_MEASURED = "not measured"
_SLM_NOT_APPLICABLE = "not applicable"
_SLM_NOT_DECLARED = "not declared"

#: The legend entry of the dashes the verdict figure draws for every result
#: of a clause, behind the one that decides it.
_SLM_EVERY_RESULT = "Every result of the clause"

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
    _ACCEPTANCE_LIMITS_LABEL: "Límites de aceptación",
    _ACCEPTANCE_LABEL: "Límite de aceptación",
    "Conforms": "Conforme",
    "Does not conform": "No conforme",
    "Actual uncertainty": "Incertidumbre real",
    "Maximum-permitted uncertainty": "Incertidumbre máxima permitida",
    "Deviation from design goal [{unit}]": "Desviación respecto al objetivo de diseño [{unit}]",
    "Short-term level fluctuation [{unit}]": "Fluctuación del nivel a corto plazo [{unit}]",
    "Total distortion + noise [{unit}]": "Distorsión total + ruido [{unit}]",
    "Measurement": "Medida",
    _CONFORMS: "conforme",
    _DOES_NOT_CONFORM: "no conforme",
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
    r"Weights: two elements to a reading, the largest {pct} % of the sphere": r"Pesos: dos elementos por lectura, el mayor {pct} % de la esfera",
    r"$K(\phi)$ in each plane": r"$K(\phi)$ en cada plano",
    r"$2K(\phi)$, one plane for two": r"$2K(\phi)$, un plano que vale por dos",
    "1/38 for every direction": "1/38 en cada dirección",
    r"Angle of incidence $\phi$ [°]": r"Ángulo de incidencia $\phi$ [°]",
    "Weight [% of the sphere]": "Peso [% de la esfera]",
    r"$G_\mathrm{F}$, free field, reference direction": r"$G_\mathrm{F}$, campo libre, dirección de referencia",
    r"$G_\mathrm{RI}$, random incidence": r"$G_\mathrm{RI}$, incidencia aleatoria",
    _RI_CORRECTION_LABEL: _RI_CORRECTION_LABEL,
    _SENSITIVITY_LEVEL_LABEL: "Nivel de sensibilidad [dB]",
    _CORRECTION_AXIS_LABEL: "Corrección [dB]",
    "Random-incidence sensitivity level (IEC 61183)": "Nivel de sensibilidad en incidencia aleatoria (IEC 61183)",
    "Random-incidence correction (IEC 61183)": "Corrección de incidencia aleatoria (IEC 61183)",
    _FREQUENCY_LABEL: "Frecuencia [Hz]",
    r"$G_\mathrm{D}$, instrument under test": r"$G_\mathrm{D}$, instrumento en ensayo",
    r"$G_\mathrm{D,ref}$, reference, Formula (9)": r"$G_\mathrm{D,ref}$, referencia, Fórmula (9)",
    r"$G_\mathrm{D,ref}$, reference, Formula (10)": r"$G_\mathrm{D,ref}$, referencia, Fórmula (10)",
    r"$G_\mathrm{D,ref}$, reference, Formula (11)": r"$G_\mathrm{D,ref}$, referencia, Fórmula (11)",
    _DIFFUSE_DEVIATION_LABEL: _DIFFUSE_DEVIATION_LABEL,
    "Diffuse-field sensitivity level (IEC 61183)": "Nivel de sensibilidad en campo difuso (IEC 61183)",
    # IEC 62585: corrections for the free-field response of a sound level meter.
    r"$C_\mathrm{FF,SLM}$, Formula (D.7)": r"$C_\mathrm{FF,SLM}$, Fórmula (D.7)",
    r"$C_\mathrm{FF,SLM}$, Formula (E.6)": r"$C_\mathrm{FF,SLM}$, Fórmula (E.6)",
    r"$C_\mathrm{N,FF,SLM}$, Formula (F.13)": r"$C_\mathrm{N,FF,SLM}$, Fórmula (F.13)",
    _REFERENCE_MIC_LABEL: r"$C_\mathrm{FF,RM}$, micrófono de referencia",
    r"$S_\mathrm{N,RM} + G_\mathrm{N,RC}$, reference channel": r"$S_\mathrm{N,RM} + G_\mathrm{N,RC}$, canal de referencia",
    "Free-field correction on a sound calibrator (IEC 62585)": "Corrección de campo libre con calibrador acústico (IEC 62585)",
    "Free-field correction in a comparison coupler (IEC 62585)": "Corrección de campo libre en acoplador de comparación (IEC 62585)",
    "Free-field correction on an electrostatic actuator (IEC 62585)": "Corrección de campo libre con actuador electrostático (IEC 62585)",
    "Gain of the meter": "Ganancia del sonómetro",
    "Gain of the reference channel": "Ganancia del canal de referencia",
    "Source to microphone distance": "Distancia de la fuente al micrófono",
    "Free progressive wave": "Onda progresiva libre",
    "Mountings": "Soportes",
    "Microphone diameters": "Diámetros de los micrófonos",
    "Rounding": "Redondeo",
    "Repeatability": "Repetibilidad",
    "Static pressure": "Presión estática",
    r"Tolerance $\pm t$ the fit weighs": r"Tolerancia $\pm t$ con que pondera el ajuste",
    "Free-field response, before the adjustment": "Respuesta en campo libre, antes del ajuste",
    "Free-field response, adjusted ($s$ = {s} dB)": "Respuesta en campo libre, ajustada ($s$ = {s} dB)",
    "Pressure response, adjusted": "Respuesta en campo de presión, ajustada",
    "Deviation from the incident level [dB]": "Desviación respecto del nivel incidente [dB]",
    r"Adjustment value $\Delta L = L_1 - L_4$ = {dl} dB (IEC 62585)": r"Valor de ajuste $\Delta L = L_1 - L_4$ = {dl} dB (IEC 62585)",
    "Range of the {n} determinations": "Intervalo de las {n} determinaciones",
    "{label}, mean": "{label}, media",
    r"$f_0$ = {f} Hz, where it is zero": r"$f_0$ = {f} Hz, donde es nula",
    _STANDARD_UNCERTAINTY_LABEL: r"Incertidumbre típica $u_i$ [dB]",
    "Uncertainty budget at {f} Hz (IEC 62585 Annex I)": "Presupuesto de incertidumbre a {f} Hz (IEC 62585, anexo I)",
    "Type B": "Tipo B",
    "Type A, from repeat measurements": "Tipo A, de medidas repetidas",
    "Maximum, clause {n}": "Máximo, apartado {n}",
    r"Expanded uncertainty $U$": r"Incertidumbre expandida $U$",
    "Range over the microphones": "Intervalo entre micrófonos",
    "Exceeds the maximum": "Supera el máximo",
    "Expanded uncertainty [dB]": "Incertidumbre expandida [dB]",
    "Expanded uncertainty, range [dB]": "Incertidumbre expandida, intervalo [dB]",
    "Clause {n}: exceeds the maximum at {k} of {m} frequencies (IEC 62585)": "Apartado {n}: supera el máximo en {k} de {m} frecuencias (IEC 62585)",
    "Clause {n}: within the maximum at every frequency (IEC 62585)": "Apartado {n}: dentro del máximo en todas las frecuencias (IEC 62585)",
    # IEC 61672-3: the periodic tests of a sound level meter.
    _SLM_UNUSABLE_LABEL: "No utilizable (§4.3)",
    _SLM_PERIODIC_TITLE: "IEC 61672-3 §{clause}: {verdict}\n{title}",
    "IEC 61672-3 periodic tests, class {cls}: {verdict}": "Ensayos periódicos IEC 61672-3, clase {cls}: {verdict}",
    "passed": "superados",
    "not passed": "no superados",
    "not usable (§4.3)": "no utilizable (§4.3)",
    "Result": "Resultado",
    "Acoustical signal tests of a frequency weighting": "Ponderación frecuencial con señales acústicas",
    "Electrical signal tests of frequency weightings": "Ponderaciones frecuenciales con señales eléctricas",
    "Frequency weightings at 1 kHz": "Ponderaciones frecuenciales a 1 kHz",
    "Time weightings at 1 kHz": "Ponderaciones temporales a 1 kHz",
    "Long-term stability": "Estabilidad a largo plazo",
    "Level linearity on the reference level range": "Linealidad de nivel en el rango de niveles de referencia",
    "Level linearity including the level range control": "Linealidad de nivel con el control de rango de niveles",
    "Toneburst response": "Respuesta a una ráfaga tonal",
    "C-weighted peak sound level": "Nivel de sonido con ponderación C de pico",
    "Overload indication": "Indicación de sobrecarga",
    "High-level stability": "Estabilidad a niveles elevados",
    "one cycle": "un ciclo",
    "positive half cycle": "semiciclo positivo",
    "negative half cycle": "semiciclo negativo",
    "final \u2212 initial": "final \u2212 inicial",
    "positive \u2212 negative": "positivo \u2212 negativo",
    "step {n}": "paso {n}",
    "{reading}, range {n}": "{reading}, rango {n}",
    _SLM_NOT_MEASURED: "no medido",
    _SLM_NOT_APPLICABLE: "no aplicable",
    _SLM_NOT_DECLARED: "no declarado",
    _SLM_EVERY_RESULT: "Cada resultado del apartado",
    "Clause": "Apartado",
    "{reading}, reference range": "{reading}, rango de referencia",
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
    return _t(_CONFORMS if passes else _DOES_NOT_CONFORM, language)


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
    one: its lower bound of zero is not a limit the standard prints. An open
    end of an interval (the ``+inf`` of a stop-band minimum) is no line at
    all.
    """
    lowers = {v.lower_limit for v in verifications}
    uppers = {v.upper_limit for v in verifications}
    if any(math.isinf(limit) for limit in lowers | uppers):
        _draw_open_limits(ax, verifications, positions, language)
        return
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
            label=_t(_ACCEPTANCE_LIMITS_LABEL, language) if k == 0 else "_nolegend_",
        )


def _draw_open_limits(
    ax: Axes,
    verifications: tuple[ConformanceVerification, ...],
    positions: np.ndarray,
    language: str,
) -> None:
    """Short bars at the finite limits of intervals open on one side.

    A stop-band row of IEC 61260-1:2014 Table 1 prints a minimum and
    ``+inf``; the open end bounds nothing and draws nothing. The legend names
    one limit when every bar is a single limit, and limits when any
    interval has both.
    """
    finite = [
        [lim for lim in (v.lower_limit, v.upper_limit) if math.isfinite(lim)]
        for v in verifications
    ]
    single = all(len(bars) == 1 for bars in finite)
    label = _t(_ACCEPTANCE_LABEL if single else _ACCEPTANCE_LIMITS_LABEL, language)
    for k, (x, bars) in enumerate(zip(positions, finite, strict=True)):
        ax.hlines(
            bars,
            x - 0.4,
            x + 0.4,
            color=_C_SECONDARY,
            lw=2.2,
            label=label if k == 0 else "_nolegend_",
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
    *,
    unusable_label: str | None = None,
    unusable: Sequence[bool] | None = None,
) -> None:
    """A diamond where a measurement conforms and a cross where it does not.

    With an ``unusable_label`` a measurement whose uncertainty exceeds its
    maximum is a hollow circle under that label instead: a standard that
    forbids using such a result (IEC 61260-3:2016 5.3) reads it as neither.
    ``unusable``, one flag per measurement, says which are when not every
    result over its maximum is (IEC 61672-3:2013 4.4).
    """
    shown: set[str] = set()
    user_label = "label" in kwargs
    flags = (
        [not v.uncertainty_within_maximum for v in verifications]
        if unusable is None
        else list(unusable)
    )
    for k, (x, v) in enumerate(zip(positions, verifications, strict=True)):
        style = dict(kwargs)
        if unusable_label is not None and flags[k]:
            key = unusable_label
            style_default(style, "color", _C_SECONDARY)
            style.setdefault("marker", "o")
            style_default(style, "markerfacecolor", "none")
            style_default(style, "markersize", 9)
        elif v.passes:
            key = _t("Conforms", language)
            style_default(style, "color", _C_TERTIARY)
            style.setdefault("marker", "D")
            style_default(style, "markersize", 8)
        else:
            key = _t("Does not conform", language)
            style_default(style, "color", _C_REFERENCE)
            style.setdefault("marker", "X")
            style_default(style, "markersize", 10)
        if user_label:
            if k > 0:
                style["label"] = "_nolegend_"
        elif key in shown:
            style["label"] = "_nolegend_"
        else:
            style["label"] = key
            shown.add(key)
        style_default(style, "linestyle", "none")
        ax.plot([x], [v.deviation], zorder=4, **style)


def _finite_or(limit: float, fallback: float) -> float:
    """*limit*, or *fallback* when the limit is an open end of the interval."""
    return limit if math.isfinite(limit) else fallback


def _draw_conformance(
    ax: Axes,
    verifications: tuple[ConformanceVerification, ...],
    language: str,
    kwargs: dict[str, Any],
    *,
    magnitude_axis_label: str | None = None,
    unusable_label: str | None = None,
    unusable: Sequence[bool] | None = None,
) -> None:
    """The picture of Figure E.1: limits, band, error bar and verdict marker.

    One measurement per unit of the horizontal axis, starting at 1. A
    ``magnitude_axis_label`` marks a one-sided requirement, a magnitude with a
    maximum, and names its vertical axis in place of the deviation from a
    design goal; an ``unusable_label`` draws a measurement whose uncertainty
    exceeds its maximum as unusable rather than as not conforming, or those
    of the ``unusable`` flags when they are given.
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
    _draw_verdicts(
        ax,
        verifications,
        positions,
        language,
        kwargs,
        unusable_label=unusable_label,
        unusable=unusable,
    )
    reach = [max(v.uncertainty, v.max_uncertainty) for v in verifications]
    # An open end of an interval is no extent of the axis: only the finite
    # limits and the deviations with their bands decide it.
    low = min(
        min(_finite_or(v.lower_limit, v.deviation), v.deviation - r)
        for v, r in zip(verifications, reach, strict=True)
    )
    high = max(
        max(_finite_or(v.upper_limit, v.deviation), v.deviation + r)
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
# IEC 61672-3: the periodic tests of a sound level meter
# ---------------------------------------------------------------------------

#: The differences of Clause 14 as the figures write them, in mathtext.
_SLM_DIFFERENCE_LABELS: dict[str, str] = {
    "LC - LA": r"$L_\mathrm{C} - L_\mathrm{A}$",
    "LZ - LA": r"$L_\mathrm{Z} - L_\mathrm{A}$",
    "LAS - LAF": r"$L_\mathrm{AS} - L_\mathrm{AF}$",
    "LAeq - LAF": r"$L_\mathrm{Aeq} - L_\mathrm{AF}$",
}

#: The one-result labels of Clauses 15, 20 and 21, whose hyphen the figure
#: draws as a minus sign.
_SLM_CHANGE_LABELS: dict[str, str] = {
    "final - initial": "final − initial",
    "positive - negative": "positive − negative",
}

#: The signals of the C-weighted peak test, which a tick label puts on a
#: line of their own above the frequency.
_SLM_PEAK_SIGNALS = ("one cycle", "positive half cycle", "negative half cycle")

#: More results than this and a requirement's tick labels stand on end.
_SLM_UPRIGHT_TICKS = 9


def _slm_label(label: str, language: str) -> str:
    """One result of a periodic test as its tick label reads.

    The differences of Clause 14 in mathtext, the signal of a C-weighted peak
    result on a line of its own, the words translated and the decimals
    localised.
    """
    from .._i18n import decimal_comma

    if label in _SLM_DIFFERENCE_LABELS:
        return _SLM_DIFFERENCE_LABELS[label]
    if label in _SLM_CHANGE_LABELS:
        return _t(_SLM_CHANGE_LABELS[label], language)
    word, _, number = label.partition(" ")
    if word == "step" and number.isdigit():
        return _t("step {n}", language, n=number)
    reading, _, where = label.partition(", ")
    if where == "reference range":
        # The reading of 17.4 on the reference level range.
        return _t("{reading}, reference range", language, reading=reading)
    reading, _, where = label.partition(", range ")
    if where.isdigit():
        # A subclause of Clause 17, whose point is not a decimal separator.
        return _t("{reading}, range {n}", language, reading=reading, n=where)
    signal, _, rest = label.partition(", ")
    if signal in _SLM_PEAK_SIGNALS:
        return f"{_t(signal, language)}\n{decimal_comma(rest, language)}"
    return decimal_comma(label, language)


def _slm_verdict(result: SoundLevelMeterPeriodicRequirement, language: str) -> str:
    """``conforms``, ``does not conform`` or ``not usable``, localised."""
    if result.failed:
        return _t(_DOES_NOT_CONFORM, language)
    if result.unusable:
        return _t("not usable (§4.3)", language)
    return _t(_CONFORMS, language)


def _slm_unusable_flags(result: SoundLevelMeterPeriodicRequirement) -> list[bool]:
    """One flag per result: whether 4.3 forbids using it (4.4 results are not)."""
    unusable = set(result.unusable)
    return [label in unusable for label in result.labels]


def plot_slm_periodic_requirement(
    result: SoundLevelMeterPeriodicRequirement,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """One requirement of IEC 61672-3:2013 against its acceptance limits.

    As IEC 61672-1:2013 Figure C.1: the limits, the deviation from the
    design goal, its uncertainty and the maximum-permitted band, one result
    per position and named under it. The electrical test of the frequency
    weightings, whose limits run from 0,7 dB to 16 dB, is drawn as each
    result's margin to its nearer limit instead. A result whose uncertainty
    exceeds its maximum is drawn hollow, as 4.3 forbids using it, unless 4.4
    makes it a result that did not conform. The title names the clause and
    its verdict, and under them the clause's heading.

    :param result: A
        :class:`~phonometry.metrology.sound_level_meter.SoundLevelMeterPeriodicRequirement`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the verdict markers.
    :return: The axes.
    """
    from .._i18n import localize_axes
    from .filters import _draw_margins, _margin_axis

    count = len(result.verifications)
    if ax is None:
        _fig, ax = _import_pyplot().subplots(
            figsize=(max(6.4, 1.0 + 0.42 * count), 4.8), layout="constrained"
        )
    unusable = _t(_SLM_UNUSABLE_LABEL, language)
    flags = _slm_unusable_flags(result)
    positions = np.arange(1, count + 1, dtype=float)
    if result.name == "electrical_weighting":
        _draw_margins(
            ax,
            positions,
            result.verifications,
            language,
            kwargs,
            set(),
            unusable_label=unusable,
            unusable=flags,
        )
        _margin_axis(ax, list(result.verifications), language)
        ax.set_xlim(0.4, count + 0.6)
        place_legend_clear(ax.legend(fontsize="small"))
    else:
        _draw_conformance(
            ax,
            result.verifications,
            language,
            kwargs,
            unusable_label=unusable,
            unusable=flags,
        )
    ax.set_xticks(positions)
    ax.set_xticklabels(
        [_slm_label(label, language) for label in result.labels],
        rotation=0 if count <= _SLM_UPRIGHT_TICKS else 90,
    )
    ax.set_xlabel(_t("Result", language))
    ax.set_title(
        _t(
            _SLM_PERIODIC_TITLE,
            language,
            clause=result.clause,
            title=_t(result.title, language),
            verdict=_slm_verdict(result, language),
        )
    )
    localize_axes(ax, language)
    return ax


#: The clauses of IEC 61672-3:2013 that grade a result, in the order of the
#: standard: the slots of the verdict figure.
_SLM_GRADED_CLAUSES = (
    "12",
    "13",
    "14.2",
    "14.3",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
)

#: The colour each kind of clause without results names itself in.
_SLM_ABSENT_COLORS = {
    _SLM_NOT_MEASURED: _C_REFERENCE,
    _SLM_NOT_DECLARED: _C_SECONDARY,
    _SLM_NOT_APPLICABLE: _C_MUTED,
}


def _slm_clause_slots(
    result: SoundLevelMeterPeriodicVerification,
) -> list[tuple[str, SoundLevelMeterPeriodicRequirement | None, str | None]]:
    """``(clause, requirement, status)`` for each graded clause the figure shows.

    Every clause the record holds with its requirement and no status, and
    every clause it does not hold with none and why: not measured when a
    complete test needs it, not applicable when the declared features take
    it out, and not declared when its feature is an open question (8.1). A
    clause the record does not hold and that is none of these is left out.
    """
    by_clause = {r.clause: r for r in result.requirements}
    missing = set(result.missing)
    not_applicable = {clause for clause, _ in result.not_applicable}
    slots: list[tuple[str, SoundLevelMeterPeriodicRequirement | None, str | None]] = []
    for clause in _SLM_GRADED_CLAUSES:
        if clause in by_clause:
            slots.append((clause, by_clause[clause], None))
        elif clause in missing:
            slots.append((clause, None, _SLM_NOT_MEASURED))
        elif clause in not_applicable:
            slots.append((clause, None, _SLM_NOT_APPLICABLE))
        elif result.undeclared:
            slots.append((clause, None, _SLM_NOT_DECLARED))
    return slots


def _slm_worst(result: SoundLevelMeterPeriodicRequirement) -> int:
    """The index of the result that stands for its clause in the verdict figure.

    The result that decides the clause: one that did not conform first (a
    result of 4.4 among them), then one 4.3 forbids using, then any other;
    of those, the one with the smallest margin to its nearer acceptance
    limit, which is the furthest past it when the margin is negative.
    """
    from .filters import _margin_db

    failed = set(result.failed)
    unusable = set(result.unusable)

    def rank(k: int) -> tuple[int, float]:
        label = result.labels[k]
        if label in failed:
            severity = 0
        elif label in unusable:
            severity = 1
        else:
            severity = 2
        return severity, _margin_db(result.verifications[k])

    return min(range(len(result.verifications)), key=rank)


def _draw_slm_slot(
    ax: Axes,
    x: float,
    result: SoundLevelMeterPeriodicRequirement,
    language: str,
    kwargs: dict[str, Any],
    shown: set[str],
) -> None:
    """One graded clause in one slot: every result as a dash, its worst on top.

    Every result's margin is a short blue dash at the slot, so a clause of
    dozens of steps takes no more room than a clause of one; the result
    that decides the clause (:func:`_slm_worst`) is drawn over them as the
    clause's verdict marker, with its uncertainty as error bar.
    """
    from .filters import _draw_margins, _margin_db

    margins = [_margin_db(v) for v in result.verifications]
    every = _t(_SLM_EVERY_RESULT, language)
    ax.plot(
        np.full(len(margins), x),
        margins,
        linestyle="none",
        marker="_",
        markersize=16,
        markeredgewidth=1.5,
        color=_C_PRIMARY,
        label="_nolegend_" if every in shown else every,
    )
    shown.add(every)
    k = _slm_worst(result)
    _draw_margins(
        ax,
        np.array([x]),
        (result.verifications[k],),
        language,
        kwargs,
        shown,
        unusable_label=_t(_SLM_UNUSABLE_LABEL, language),
        unusable=[_slm_unusable_flags(result)[k]],
    )


def _slm_tick_labels(
    ax: Axes,
    slots: list[tuple[str, SoundLevelMeterPeriodicRequirement | None, str | None]],
    language: str,
) -> None:
    """Each slot's clause under it, a failed check in red, a status on end.

    A clause the record does not hold names its status under the clause,
    stood on end and in its colour; a clause whose yes/no check failed (no
    overload during the C-weighted peak test, the latching of the overload
    indicator) has its name in red, as a check has no margin to draw.
    """
    ax.set_xticklabels(
        [
            f"§{clause}\n{_t(status, language)}" if status else f"§{clause}"
            for clause, _, status in slots
        ]
    )
    for tick, (_, requirement, status) in zip(ax.get_xticklabels(), slots, strict=True):
        if status:
            # Stood on end: a status is wider than a slot, and would run into
            # the next clause's name lying down.
            tick.set_color(_SLM_ABSENT_COLORS[status])
            tick.set_rotation(90)
        elif requirement is not None and any(
            not held for _, held in requirement.checks
        ):
            tick.set_color(_C_REFERENCE)


def plot_slm_periodic_verification(
    result: SoundLevelMeterPeriodicVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Every graded clause of the periodic tests at its margin, one slot each.

    One slot per clause, however many results it holds: each result's
    distance from its deviation to the nearer acceptance limit is a blue
    dash, and the result that decides the clause, the worst one, is drawn
    over them with its actual uncertainty as error bar, as a diamond when it
    conforms, a cross when it does not and hollow when 4.3 forbids using it;
    a result 4.4 lets the test proceed with is a cross wherever it lies. At
    or above the dashed zero line a result lies within its limits. A record
    with dozens of steps in Clause 16, as 16.3 takes over a linear operating
    range of 60 dB to 80 dB, keeps every clause's name legible; each
    requirement's own ``.plot()`` draws its results one by one. A clause
    whose yes/no check failed has its name in red, and a graded clause the
    record does not hold keeps an empty slot, named under it as not measured
    (in red: a complete test needs it), not declared (its feature is an open
    question, 8.1) or not applicable (the declared features take it out, in
    grey).

    :param result: A
        :class:`~phonometry.metrology.sound_level_meter.SoundLevelMeterPeriodicVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the verdict markers.
    :return: The axes.
    """
    from .filters import _margin_axis

    if ax is None:
        _fig, ax = _import_pyplot().subplots(figsize=(10.0, 5.2), layout="constrained")
    slots = _slm_clause_slots(result)
    shown: set[str] = set()
    for x, (_, requirement, _) in enumerate(slots, 1):
        if requirement is not None:
            _draw_slm_slot(ax, float(x), requirement, language, kwargs, shown)
    _margin_axis(
        ax, [v for _, r, _ in slots if r is not None for v in r.verifications], language
    )
    ax.set_xlim(0.5, len(slots) + 0.5)
    ax.set_xticks(np.arange(1, len(slots) + 1, dtype=np.float64))
    _slm_tick_labels(ax, slots, language)
    ax.set_xlabel(_t("Clause", language))
    verdict = _t("passed" if result.passes else "not passed", language)
    ax.set_title(
        _t(
            "IEC 61672-3 periodic tests, class {cls}: {verdict}",
            language,
            cls=result.meter_class,
            verdict=verdict,
        )
    )
    place_legend_clear(ax.legend(fontsize="small", ncols=2))
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

#: The directions every plane through the reference direction holds.
_POLES_DEG = (0.0, 180.0)

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
    """A fresh figure with one polar axes.

    The figure lays itself out with the legend under the disc inside it: a
    plain figure places the axes first and leaves the legend, anchored below
    the rim, hanging off the bottom edge.
    """
    from typing import cast

    plt = _import_pyplot()
    _fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, layout="constrained")
    return cast("Axes", ax)


def _plane_curve(
    angles: NDArray[np.float64],
    relative: NDArray[np.float64],
    planes: NDArray[np.float64],
    plane: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The readings of one plane in angle order, with both poles on it.

    The directions at 0° and 180° lie on every plane through the reference
    direction, and the 38 equal-area readings of Formula (A.5) take them in
    the horizontal plane only: a plane that lacks one borrows it from the
    plane that has it, so its curve runs through the pole rather than
    cutting a chord across it.
    """
    mask = np.isclose(planes, plane)
    theta = angles[mask]
    level = relative[mask]
    for pole in _POLES_DEG:
        if np.any(np.isclose(theta, pole)):
            continue
        shared = np.flatnonzero(np.isclose(angles, pole))
        if shared.size:
            theta = np.append(theta, pole)
            level = np.append(level, relative[shared[0]])
    order = np.argsort(theta)
    return theta[order], level[order]


def _radial_formatter(top: float, language: str) -> FuncFormatter:
    """Radial tick labels in dB: the numbers, with the unit on the outermost."""
    from matplotlib.ticker import FuncFormatter

    from .._i18n import format_number

    def _label(value: float, _pos: int | None = None) -> str:
        text = format_number(value, language, decimals=1, trim=True)
        return f"{text} dB" if math.isclose(value, top, abs_tol=1e-9) else text

    return FuncFormatter(_label)


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
        degrees, level = _plane_curve(angles, relative, planes, float(plane))
        theta = np.radians(degrees)
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
    # The radius is L(phi) - L_rd: the outermost label carries its unit, as
    # the piston directivity of the electroacoustics plots does.
    ax.yaxis.set_major_formatter(_radial_formatter(float(ticks[-1]), language))
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
    pct = format_number(100.0 * result.largest_element_fraction, language, decimals=2)
    # One plane under rotational symmetry weighs each reading 2K: it stands
    # for the same direction in both planes of Annex A, two elements of the
    # division the largest element is judged on.
    title = (
        r"Weights: two elements to a reading, the largest {pct} % of the sphere"
        if result.formula == "A.4"
        else r"Weights of the readings: largest element {pct} % of the sphere"
    )
    ax.set_title(_t(title, language, pct=pct))
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
        kwargs.setdefault("label", _t(_RI_CORRECTION_LABEL, language))
        ax.plot(frequencies, result.correction_db, **kwargs)
        ax.axhline(0.0, color=_C_MUTED, lw=0.8, ls="--")
        ax.set_ylabel(_t(_CORRECTION_AXIS_LABEL, language))
        ax.set_title(_t("Random-incidence correction (IEC 61183)", language))
    else:
        kwargs.setdefault(
            "label", _t(r"$G_\mathrm{F}$, free field, reference direction", language)
        )
        ax.plot(frequencies, result.free_field_level_db, **kwargs)
        # Open markers on a dashed line: up to about 1 kHz the correction is
        # nil and G_RI lies on G_F, which must stay visible underneath.
        ax.plot(
            frequencies,
            result.random_incidence_level_db,
            color=_C_REFERENCE,
            lw=1.5,
            ls="--",
            marker="s",
            ms=4.5,
            mfc="none",
            label=_t(r"$G_\mathrm{RI}$, random incidence", language),
        )
        ax.set_ylabel(_t(_SENSITIVITY_LEVEL_LABEL, language))
        ax.set_title(_t("Random-incidence sensitivity level (IEC 61183)", language))
    ax.set_xscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t(_FREQUENCY_LABEL, language))
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
    # Open markers on the other two: at low frequency the reference corrects
    # nothing and all three curves can lie on one another.
    ax.plot(
        frequencies,
        result.reference_diffuse_field_level_db,
        color=_C_SECONDARY,
        lw=1.2,
        ls="--",
        marker="s",
        ms=4.5,
        mfc="none",
        label=_t(_DIFFUSE_REFERENCE_LABELS[result.route], language),
    )
    ax.plot(
        frequencies,
        result.level_difference_db,
        color=_C_TERTIARY,
        lw=1.2,
        ls=":",
        marker="^",
        ms=6.0,
        mfc="none",
        label=_t(_DIFFUSE_DEVIATION_LABEL, language),
    )
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.set_xscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t(_FREQUENCY_LABEL, language))
    ax.set_ylabel(_t(_SENSITIVITY_LEVEL_LABEL, language))
    ax.set_title(_t("Diffuse-field sensitivity level (IEC 61183)", language))
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="lower left", fontsize="small")
    localize_axes(ax, language)
    return ax


# ---------------------------------------------------------------------------
# IEC 62585: corrections for the free-field response of a sound level meter
# ---------------------------------------------------------------------------

#: The curve label of a correction, by the source it was measured on.
_CORRECTION_LABELS = {
    "sound_calibrator": r"$C_\mathrm{FF,SLM}$, Formula (D.7)",
    "comparison_coupler": r"$C_\mathrm{FF,SLM}$, Formula (E.6)",
    "electrostatic_actuator": r"$C_\mathrm{N,FF,SLM}$, Formula (F.13)",
}

#: The label of what the reference contributes, by source.
_REFERENCE_TERM_LABELS = {
    "sound_calibrator": _REFERENCE_MIC_LABEL,
    "comparison_coupler": _REFERENCE_MIC_LABEL,
    "electrostatic_actuator": r"$S_\mathrm{N,RM} + G_\mathrm{N,RC}$, reference channel",
}

#: The title of a correction plot, by source.
_CORRECTION_TITLES = {
    "sound_calibrator": "Free-field correction on a sound calibrator (IEC 62585)",
    "comparison_coupler": "Free-field correction in a comparison coupler (IEC 62585)",
    "electrostatic_actuator": (
        "Free-field correction on an electrostatic actuator (IEC 62585)"
    ),
}

#: The tick label of each component of a budget, by descriptor: the symbol of
#: Table I.1 where it has one, its name where it does not.
_COMPONENT_LABELS = {
    "a1": r"$L_\mathrm{ind1}$",
    "a2": r"$L_\mathrm{ind2}$",
    "a3": r"$L_\mathrm{ind3a}$",
    "a4": r"$L_\mathrm{ind3b}$",
    "a5": r"$L_{p,\mathrm{F1}} - L_{p,\mathrm{F2}}$",
    "a6": r"$L_{p,\mathrm{P1}} - L_{p,\mathrm{P2}}$",
    "a7": r"$C_\mathrm{FF,RM}$",
    "a8": "Gain of the meter",
    "a9": "Gain of the reference channel",
    "a10": "Source to microphone distance",
    "a11": "Free progressive wave",
    "a12": "Mountings",
    "a13": "Microphone diameters",
    "a14": "Rounding",
    "a15": "Repeatability",
    "static pressure": "Static pressure",
}

#: How many points draw the stepped maximum of a clause across the axis.
_MAXIMUM_CURVE_POINTS = 400

#: Headroom over the largest value of the verification view.
_VERIFICATION_HEADROOM = 1.3


def plot_adjustment_value(
    result: AdjustmentValue,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The free-field deviation of a meter before and after its adjustment.

    Draws the deviation of the indication from the incident level as
    measured, the same after the sensitivity adjustment of the fit, the
    tolerance band the fit weighed it against where one was given, and the
    pressure response after the adjustment when it was measured: curves (2)
    and (3) of IEC 62585 Figure A.1 less the incident level (1).

    :param result: An
        :class:`~phonometry.metrology.free_field_corrections.AdjustmentValue`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the adjusted-response curve.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    frequencies = np.asarray(result.frequencies_hz, dtype=np.float64)
    if result.tolerance_db is not None:
        tolerance = np.asarray(result.tolerance_db, dtype=np.float64)
        bound = np.where(np.isfinite(tolerance), tolerance, np.nan)
        ax.fill_between(
            frequencies,
            -bound,
            bound,
            color=theme_fill(_C_PRIMARY, ax),
            lw=0.0,
            label=_t(r"Tolerance $\pm t$ the fit weighs", language),
        )
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.plot(
        frequencies,
        result.free_field_deviation_db,
        color=_C_MUTED,
        lw=1.0,
        ls="--",
        marker="o",
        ms=3.5,
        mfc="none",
        label=_t("Free-field response, before the adjustment", language),
    )
    adjustment = format_number(result.sensitivity_adjustment_db, language, decimals=2)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 3.5)
    kwargs.setdefault(
        "label",
        _t(
            "Free-field response, adjusted ($s$ = {s} dB)",
            language,
            s=adjustment,
        ),
    )
    ax.plot(frequencies, result.adjusted_deviation_db, **kwargs)
    correction = result.pressure_to_free_field_correction_db
    if correction is not None:
        ax.plot(
            frequencies,
            -np.asarray(correction, dtype=np.float64),
            color=_C_SECONDARY,
            lw=1.2,
            ls="-.",
            marker="s",
            ms=3.5,
            mfc="none",
            label=_t("Pressure response, adjusted", language),
        )
    check = format_number(result.check_frequency_hz, language, decimals=0)
    ax.axvline(
        result.check_frequency_hz,
        color=_C_REFERENCE,
        lw=1.0,
        ls=":",
        label=_t(r"$f_\mathrm{{R}}$ = {f} Hz", language, f=check),
    )
    ax.set_xscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t(_FREQUENCY_LABEL, language))
    ax.set_ylabel(_t("Deviation from the incident level [dB]", language))
    delta = format_number(result.adjustment_db, language, decimals=2)
    ax.set_title(
        _t(
            r"Adjustment value $\Delta L = L_1 - L_4$ = {dl} dB (IEC 62585)",
            language,
            dl=delta,
        )
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_free_field_correction(
    result: FreeFieldCorrection,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The IEC 62585 free-field correction of a meter against frequency.

    Draws the mean correction over the determinations, the band between the
    smallest and the largest when there are several, and what the reference
    microphone contributes to it.

    :param result: A
        :class:`~phonometry.metrology.free_field_corrections.FreeFieldCorrection`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the mean-correction curve.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    frequencies = np.asarray(result.frequencies_hz, dtype=np.float64)
    corrections = np.asarray(result.corrections_db, dtype=np.float64)
    count = result.determinations
    if count > 1:
        ax.fill_between(
            frequencies,
            corrections.min(axis=0),
            corrections.max(axis=0),
            color=theme_fill(_C_PRIMARY, ax),
            lw=0.0,
            label=_t("Range of the {n} determinations", language, n=count),
        )
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 3.5)
    label = _t(_CORRECTION_LABELS[result.source], language)
    if count > 1:
        label = _t("{label}, mean", language, label=label)
    kwargs.setdefault("label", label)
    ax.plot(frequencies, result.correction_db, **kwargs)
    ax.plot(
        frequencies,
        result.reference_correction_db,
        color=_C_SECONDARY,
        lw=1.2,
        ls="--",
        marker="s",
        ms=3.5,
        mfc="none",
        label=_t(_REFERENCE_TERM_LABELS[result.source], language),
    )
    if result.check_frequency_hz is not None:
        f0 = format_number(result.check_frequency_hz, language, decimals=0)
        ax.axvline(
            result.check_frequency_hz,
            color=_C_REFERENCE,
            lw=1.0,
            ls=":",
            label=_t(r"$f_0$ = {f} Hz, where it is zero", language, f=f0),
        )
    ax.set_xscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t(_FREQUENCY_LABEL, language))
    ax.set_ylabel(_t(_CORRECTION_AXIS_LABEL, language))
    ax.set_title(_t(_CORRECTION_TITLES[result.source], language))
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def _component_label(descriptor: str, language: str) -> str:
    """The tick label of one component: ``a7: C_FF,RM``, or its own name."""
    label = _COMPONENT_LABELS.get(descriptor)
    if label is None:
        return descriptor
    text = _t(label, language)
    return f"{descriptor}: {text}" if descriptor.startswith("a") else text


def plot_correction_budget(
    result: CorrectionUncertaintyBudget,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The standard uncertainty of each component of an IEC 62585 budget.

    One bar per component in the order of Table I.1, the statistical
    (Type A) ones apart in colour, with the combined standard uncertainty
    marked and the coverage factor and expanded uncertainty in the title.

    :param result: A
        :class:`~phonometry.metrology.free_field_corrections.CorrectionUncertaintyBudget`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.barh`.
    :return: The axes.
    """
    from matplotlib.patches import Patch

    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    values = np.asarray(result.standard_uncertainties_db, dtype=np.float64)
    statistical = np.isfinite(np.asarray(result.dofs, dtype=np.float64))
    positions = np.arange(values.size)
    colours = [_C_SECONDARY if flag else _C_PRIMARY for flag in statistical]
    style_default(kwargs, "color", colours)
    ax.barh(positions, values, **kwargs)
    uc = format_number(result.combined_uncertainty_db, language, decimals=4)
    combined = ax.axvline(
        result.combined_uncertainty_db,
        color=_C_REFERENCE,
        ls="--",
        lw=1.2,
        label=_t(r"$u_\mathrm{{c}}$ = {uc} dB", language, uc=uc),
    )
    ax.set_yticks(positions)
    ax.set_yticklabels(
        [_component_label(name, language) for name in result.descriptors]
    )
    ax.invert_yaxis()
    ax.set_xlim(0.0, 1.15 * max(float(values.max()), result.combined_uncertainty_db))
    ax.set_xlabel(_t(_STANDARD_UNCERTAINTY_LABEL, language))
    frequency = format_number(result.frequency_hz, language, decimals=0)
    dof = result.effective_dof
    nu = "∞" if math.isinf(dof) else format_number(dof, language, decimals=2)
    k = format_number(result.coverage_factor, language, decimals=2)
    expanded = format_number(result.expanded_uncertainty_db, language, decimals=3)
    ax.set_title(
        _t("Uncertainty budget at {f} Hz (IEC 62585 Annex I)", language, f=frequency)
        + "\n"
        + _t(
            r"$\nu_\mathrm{{eff}}$ = {nu}, $k$ = {k}, $U$ = {u} dB",
            language,
            nu=nu,
            k=k,
            u=expanded,
        )
    )
    handles: list[Any] = [Patch(color=_C_PRIMARY, label=_t("Type B", language))]
    if np.any(statistical):
        handles.append(
            Patch(
                color=_C_SECONDARY,
                label=_t("Type A, from repeat measurements", language),
            )
        )
    handles.append(combined)
    place_legend_clear(ax.legend(handles=handles, fontsize="small"))
    ax.grid(visible=True, axis="x", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_correction_uncertainty_verification(
    result: CorrectionUncertaintyVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The expanded uncertainties of a set of corrections against the
    maximum of their IEC 62585 clause.

    Draws the maximum permitted by the clause as a stepped line across the
    frequencies, the actual expanded uncertainty at each, the range of the
    corrections over the microphones when it was given, and a cross on every
    value that exceeds the maximum.

    :param result: A
        :class:`~phonometry.metrology.free_field_corrections.CorrectionUncertaintyVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the expanded-uncertainty curve.
    :return: The axes.
    """
    from .._i18n import localize_axes
    from ..metrology.free_field_corrections import maximum_expanded_uncertainty

    ax = ax if ax is not None else _new_axes()
    frequencies = np.asarray(result.frequencies_hz, dtype=np.float64)
    low, high = float(frequencies[0]), float(frequencies[-1])
    grid = (
        np.array([low])
        if math.isclose(low, high)
        else np.logspace(math.log10(low), math.log10(high), _MAXIMUM_CURVE_POINTS)
    )
    ax.plot(
        grid,
        maximum_expanded_uncertainty(grid, clause=result.clause),
        color=_C_REFERENCE,
        lw=1.5,
        label=_t("Maximum, clause {n}", language, n=result.clause),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.4)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 4.0)
    kwargs.setdefault("label", _t(r"Expanded uncertainty $U$", language))
    ax.plot(frequencies, result.expanded_uncertainty_db, **kwargs)
    tops = [
        float(np.max(result.maximum_uncertainty_db)),
        float(np.max(result.expanded_uncertainty_db)),
    ]
    failing = ~np.asarray(result.uncertainty_passes)
    if result.correction_range_db is not None:
        ranges = np.asarray(result.correction_range_db, dtype=np.float64)
        ax.plot(
            frequencies,
            ranges,
            color=_C_SECONDARY,
            lw=1.0,
            ls="--",
            marker="^",
            ms=4.5,
            mfc="none",
            label=_t("Range over the microphones", language),
        )
        tops.append(float(ranges.max()))
        range_failing = ~np.asarray(result.range_passes)
        if np.any(range_failing):
            ax.plot(
                frequencies[range_failing],
                ranges[range_failing],
                ls="none",
                marker="x",
                ms=8.0,
                mew=2.0,
                color=_C_REFERENCE,
            )
    if np.any(failing):
        ax.plot(
            frequencies[failing],
            np.asarray(result.expanded_uncertainty_db)[failing],
            ls="none",
            marker="x",
            ms=8.0,
            mew=2.0,
            color=_C_REFERENCE,
            label=_t("Exceeds the maximum", language),
        )
    ax.set_ylim(0.0, _VERIFICATION_HEADROOM * max(tops))
    ax.set_xscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t(_FREQUENCY_LABEL, language))
    # The range shares the axis: a spread of corrections, not an uncertainty.
    ylabel = (
        "Expanded uncertainty [dB]"
        if result.correction_range_db is None
        else "Expanded uncertainty, range [dB]"
    )
    ax.set_ylabel(_t(ylabel, language))
    failures = int(result.failing_frequencies_hz.size)
    if failures:
        title = _t(
            "Clause {n}: exceeds the maximum at {k} of {m} frequencies (IEC 62585)",
            language,
            n=result.clause,
            k=failures,
            m=frequencies.size,
        )
    else:
        title = _t(
            "Clause {n}: within the maximum at every frequency (IEC 62585)",
            language,
            n=result.clause,
        )
    ax.set_title(title)
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


# ---------------------------------------------------------------------------
# IEC 61094-5 and IEC 61094-8: microphone calibration by comparison
# ---------------------------------------------------------------------------

#: The title of a calibration, by field.
_COMPARISON_TITLES: dict[str, str] = {
    "pressure": "Pressure sensitivity by comparison (IEC 61094-5)",
    "free_field": "Free-field sensitivity by comparison (IEC 61094-8)",
}

#: The table a budget follows, named in its title, by field.
_COMPARISON_BUDGET_TITLES: dict[str, str] = {
    "pressure": "Uncertainty budget at {f} Hz (IEC 61094-5 Table D.1)",
    "free_field": "Uncertainty budget at {f} Hz (IEC 61094-8 Table 2)",
}

#: Short tick labels of the components of IEC 61094-5 Table D.1 and
#: IEC 61094-8 Table 2, by the key the budget takes them by.
_COMPARISON_COMPONENT_LABELS: dict[str, str] = {
    "reference": "Reference microphone",
    "capacitance": "Microphone capacitance",
    "non_linearity": "Non-linearity",
    "impedance": "Microphone impedance",
    "polarizing_voltage": "Polarizing voltage",
    "repeatability": "Repeatability",
    "drift": "Drift of the reference",
    "rounding": "Rounding",
    "source_stability": "Stability of the source",
    "positioning": "Positioning",
    "alignment": "Alignment",
    "free_field": "Free-field quality",
    "non_plane_wave": "Non-plane wave",
    "environment": "Environmental conditions",
}

#: The three terms of an environmental correction: label, colour, line style
#: and marker, in the order the result names them.
_ENVIRONMENT_TERMS: tuple[tuple[str, str, str, str], ...] = (
    (r"Static pressure, $\delta_p\,(p_s - p_{s,0})$", _C_SECONDARY, "--", "s"),
    (r"Temperature, $\delta_t\,(t - t_0)$", _C_TERTIARY, ":", "^"),
    (r"Humidity, $\delta_H\,(H - H_0)$", _C_QUATERNARY, "-.", "v"),
)

#: Labels the comparison plots share with the translation table, the same
#: in both languages: the band of the expanded uncertainty of a calibration,
#: the coverage line of a budget's title and the total environmental
#: correction.
_LEVEL_UNCERTAINTY_BAND_LABEL = r"$L_\mathrm{test} \pm U$ ($k$ = 2)"
_COVERAGE_TITLE_LINE = r"$k$ = {k}, $U$ = {u} dB"
_ENVIRONMENT_TOTAL_LABEL = r"$C_\mathrm{env}$, total"

#: Head-room above the tallest bar of a budget, as a fraction of it.
_COMPARISON_BUDGET_HEADROOM = 1.18

#: How far past the region the drawn rod runs, as a fraction of the major
#: axis, so that its end is visibly outside it.
_ROD_OVERHANG = 0.12

#: Points drawn along the boundary of the free-field region.
_ELLIPSE_POINTS = 361

#: The margin round the free-field region, as a multiple of its semi-axes.
_REGION_MARGIN = 1.15

#: The size of a figure the free-field region draws on its own, in inches:
#: wide enough for the legend beside the axes and the two-line title.
_REGION_FIGURE_SIZE_IN = (10.0, 6.0)


_STRINGS.update(
    {
        _COMPARISON_TITLES[
            "pressure"
        ]: "Sensibilidad en presión por comparación (IEC 61094-5)",
        _COMPARISON_TITLES[
            "free_field"
        ]: "Sensibilidad en campo libre por comparación (IEC 61094-8)",
        _COMPARISON_BUDGET_TITLES[
            "pressure"
        ]: "Balance de incertidumbre a {f} Hz (IEC 61094-5, tabla D.1)",
        _COMPARISON_BUDGET_TITLES[
            "free_field"
        ]: "Balance de incertidumbre a {f} Hz (IEC 61094-8, tabla 2)",
        r"$L_\mathrm{test}$, microphone under test": r"$L_\mathrm{test}$, micrófono en ensayo",
        r"$L_\mathrm{ref}$, reference microphone": r"$L_\mathrm{ref}$, micrófono de referencia",
        "Reference microphone, free-field level": "Micrófono de referencia, nivel en campo libre",
        _LEVEL_UNCERTAINTY_BAND_LABEL: _LEVEL_UNCERTAINTY_BAND_LABEL,
        "Sensitivity level [dB re 1 V/Pa]": "Nivel de sensibilidad [dB re 1 V/Pa]",
        "Reference microphone": "Micrófono de referencia",
        "Microphone capacitance": "Capacidad del micrófono",
        "Non-linearity": "No linealidad",
        "Microphone impedance": "Impedancia del micrófono",
        "Polarizing voltage": "Tensión de polarización",
        "Drift of the reference": "Deriva de la referencia",
        "Stability of the source": "Estabilidad de la fuente",
        "Positioning": "Posicionamiento",
        "Alignment": "Alineación",
        "Free-field quality": "Calidad del campo libre",
        "Non-plane wave": "Onda no plana",
        "Environmental conditions": "Condiciones ambientales",
        _COVERAGE_TITLE_LINE: _COVERAGE_TITLE_LINE,
        _ENVIRONMENT_TOTAL_LABEL: _ENVIRONMENT_TOTAL_LABEL,
        _ENVIRONMENT_TERMS[0][0]: r"Presión estática, $\delta_p\,(p_s - p_{s,0})$",
        _ENVIRONMENT_TERMS[1][0]: r"Temperatura, $\delta_t\,(t - t_0)$",
        _ENVIRONMENT_TERMS[2][0]: r"Humedad, $\delta_H\,(H - H_0)$",
        "Environmental correction: {p} kPa, {t} °C, {h} % re {p0} kPa, {t0} °C, {h0} %": "Corrección ambiental: {p} kPa, {t} °C, {h} % re {p0} kPa, {t0} °C, {h0} %",
        "Correction, Table A.1": "Corrección, tabla A.1",
        "Expanded uncertainty, 10 % of the correction": "Incertidumbre expandida, 10 % de la corrección",
        "WS3 microphone in the jig of Figure A.4 (IEC 61094-5 Table A.1)": "Micrófono WS3 en el soporte de la figura A.4 (IEC 61094-5, tabla A.1)",
        "Boundary of the effective free-field region": "Límite de la región de campo libre efectiva",
        "Sound source, F1": "Fuente sonora, F1",
        "Microphone, F2": "Micrófono, F2",
        "Direct path, $d$ = {d} m": "Trayecto directo, $d$ = {d} m",
        "Mounting rod": "Varilla de montaje",
        "Along the axis [m]": "A lo largo del eje [m]",
        "Across the axis [m]": "Transversal al eje [m]",
        r"Effective free-field region (IEC 61094-8 B.1): $A = d + \tau c$ = {a} m": r"Región de campo libre efectiva (IEC 61094-8, B.1): $A = d + \tau c$ = {a} m",
        r"$\tau$ = {tau} ms, $c$ = {c} m/s; clearance {b} m across, {r} m behind the microphone": r"$\tau$ = {tau} ms, $c$ = {c} m/s; holgura {b} m transversal, {r} m tras el micrófono",
    }
)


def plot_comparison_calibration(
    result: ComparisonCalibration,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The sensitivity level of a microphone calibrated by comparison.

    Draws :math:`L_\mathrm{test}` with its expanded uncertainty as a band when
    the calibration carries one, and the reference's level it was compared
    with: :math:`L_\mathrm{ref}` as given, or, for a free-field calibration
    against a pressure-calibrated reference, :math:`L_\mathrm{ref}` plus the
    reference's free-field to pressure difference, its free-field level.

    :param result: A
        :class:`~phonometry.metrology.comparison_calibration.ComparisonCalibration`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the :math:`L_\mathrm{test}` curve.
    :return: The axes.
    """
    from .._i18n import localize_axes
    from ..metrology.comparison_calibration import _FREE_FIELD_DIFFERENCE

    ax = ax if ax is not None else _new_axes()
    frequencies = np.asarray(result.frequencies_hz, dtype=np.float64)
    level = np.asarray(result.sensitivity_level_db, dtype=np.float64)
    if result.expanded_uncertainty_db is not None:
        uncertainty = np.asarray(result.expanded_uncertainty_db, dtype=np.float64)
        ax.fill_between(
            frequencies,
            level - uncertainty,
            level + uncertainty,
            color=theme_fill(_C_PRIMARY, ax),
            lw=0.0,
            label=_t(_LEVEL_UNCERTAINTY_BAND_LABEL, language),
        )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 3.5)
    kwargs.setdefault(
        "label", _t(r"$L_\mathrm{test}$, microphone under test", language)
    )
    ax.plot(frequencies, level, **kwargs)
    reference = np.asarray(result.reference_sensitivity_level_db, dtype=np.float64)
    reference_label = r"$L_\mathrm{ref}$, reference microphone"
    difference = result.corrections_db.get(_FREE_FIELD_DIFFERENCE)
    if difference is not None:
        # The level the free field compared the test microphone with, not the
        # pressure level the reference was calibrated at.
        reference = reference + np.asarray(difference, dtype=np.float64)
        reference_label = "Reference microphone, free-field level"
    ax.plot(
        frequencies,
        reference,
        color=_C_SECONDARY,
        lw=1.2,
        ls="--",
        marker="s",
        ms=4.0,
        mfc="none",
        label=_t(reference_label, language),
    )
    ax.set_xscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t(_FREQUENCY_LABEL, language))
    ax.set_ylabel(_t("Sensitivity level [dB re 1 V/Pa]", language))
    ax.set_title(_t(_COMPARISON_TITLES[result.field], language))
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_environmental_sensitivity_correction(
    result: EnvironmentalSensitivityCorrection,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The environmental correction of a sensitivity level and its three
    terms against frequency.

    :param result: An
        :class:`~phonometry.metrology.comparison_calibration.EnvironmentalSensitivityCorrection`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the :math:`C_\mathrm{env}` curve.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    frequencies = np.asarray(result.frequencies_hz, dtype=np.float64)
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    values = (
        result.static_pressure_term_db,
        result.temperature_term_db,
        result.humidity_term_db,
    )
    for (label, colour, style, marker), term in zip(
        _ENVIRONMENT_TERMS, values, strict=True
    ):
        ax.plot(
            frequencies,
            term,
            color=colour,
            lw=1.1,
            ls=style,
            marker=marker,
            ms=4.0,
            mfc="none",
            label=_t(label, language),
        )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.7)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 3.5)
    kwargs.setdefault("label", _t(_ENVIRONMENT_TOTAL_LABEL, language))
    ax.plot(frequencies, result.correction_db, **kwargs)
    ax.set_xscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t(_FREQUENCY_LABEL, language))
    ax.set_ylabel(_t(_CORRECTION_AXIS_LABEL, language))
    ax.set_title(
        _t(
            "Environmental correction: {p} kPa, {t} °C, {h} % re {p0} kPa, {t0} °C, {h0} %",
            language,
            p=format_number(result.static_pressure_kpa, language, decimals=3),
            t=format_number(result.temperature_c, language, decimals=1),
            h=format_number(result.relative_humidity_percent, language, decimals=0),
            p0=format_number(
                result.reference_static_pressure_kpa, language, decimals=3
            ),
            t0=format_number(result.reference_temperature_c, language, decimals=1),
            h0=format_number(
                result.reference_relative_humidity_percent, language, decimals=0
            ),
        )
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_jig_diameter_correction(
    result: JigDiameterCorrection,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The corrections of IEC 61094-5 Table A.1 with their expanded
    uncertainty.

    :param result: A
        :class:`~phonometry.metrology.comparison_calibration.JigDiameterCorrection`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the correction curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    frequencies = np.asarray(result.frequencies_hz, dtype=np.float64)
    correction = np.asarray(result.correction_db, dtype=np.float64)
    uncertainty = np.asarray(result.expanded_uncertainty_db, dtype=np.float64)
    ax.fill_between(
        frequencies,
        correction - uncertainty,
        correction + uncertainty,
        color=theme_fill(_C_PRIMARY, ax),
        lw=0.0,
        label=_t("Expanded uncertainty, 10 % of the correction", language),
    )
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 3.5)
    kwargs.setdefault("label", _t("Correction, Table A.1", language))
    ax.plot(frequencies, correction, **kwargs)
    ax.set_xscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t(_FREQUENCY_LABEL, language))
    ax.set_ylabel(_t(_CORRECTION_AXIS_LABEL, language))
    ax.set_title(
        _t("WS3 microphone in the jig of Figure A.4 (IEC 61094-5 Table A.1)", language)
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def _comparison_component_label(name: str, language: str) -> str:
    """The tick label of one component: its short name, or its own name."""
    label = _COMPARISON_COMPONENT_LABELS.get(name)
    return name if label is None else _t(label, language)


def plot_comparison_budget(
    result: ComparisonUncertaintyBudget,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The standard uncertainty of each component of a comparison budget.

    One bar per component in the order of its table, then the additional
    ones, with the combined standard uncertainty marked and the coverage
    factor and expanded uncertainty in the title.

    :param result: A
        :class:`~phonometry.metrology.comparison_calibration.ComparisonUncertaintyBudget`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.barh`.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    values = np.asarray(result.standard_uncertainties_db, dtype=np.float64)
    positions = np.arange(values.size)
    style_default(kwargs, "color", _C_PRIMARY)
    ax.barh(positions, values, **kwargs)
    uc = format_number(result.combined_uncertainty_db, language, decimals=4)
    combined = ax.axvline(
        result.combined_uncertainty_db,
        color=_C_REFERENCE,
        ls="--",
        lw=1.2,
        label=_t(r"$u_\mathrm{{c}}$ = {uc} dB", language, uc=uc),
    )
    ax.set_yticks(positions)
    ax.set_yticklabels(
        [_comparison_component_label(name, language) for name in result.names]
    )
    ax.invert_yaxis()
    top = max(float(values.max()), result.combined_uncertainty_db)
    ax.set_xlim(0.0, _COMPARISON_BUDGET_HEADROOM * top)
    ax.set_xlabel(_t(_STANDARD_UNCERTAINTY_LABEL, language))
    frequency = format_number(result.frequency_hz, language, decimals=0)
    k = format_number(result.coverage_factor, language, decimals=0)
    expanded = format_number(result.expanded_uncertainty_db, language, decimals=3)
    ax.set_title(
        _t(_COMPARISON_BUDGET_TITLES[result.field], language, f=frequency)
        + "\n"
        + _t(_COVERAGE_TITLE_LINE, language, k=k, u=expanded)
    )
    place_legend_clear(ax.legend(handles=[combined], fontsize="small"))
    ax.grid(visible=True, axis="x", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_free_field_region(
    result: FreeFieldRegion,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The effective free-field region of IEC 61094-8 B.1 in a plane through
    its axis, as Figure B.1 draws it.

    The ellipse with the source and the microphone at its foci, the direct
    path between them and the mounting rod behind the microphone, running out
    of the region.

    :param result: A
        :class:`~phonometry.metrology.comparison_calibration.FreeFieldRegion`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the boundary of the region.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    if ax is None:
        # The legend sits beside the axes and the title runs to two long
        # lines: a figure of its own is sized and laid out to keep both.
        _fig, ax = _import_pyplot().subplots(
            figsize=_REGION_FIGURE_SIZE_IN, layout="constrained"
        )
        # The equal aspect shrinks the axes inside the room the layout gave
        # them; held to the left, they keep the legend beside them in view.
        ax.set_anchor("W")
    half_major = result.major_axis_m / 2.0
    half_minor = result.semi_minor_axis_m
    half_distance = result.source_distance_m / 2.0
    angle = np.linspace(0.0, 2.0 * np.pi, _ELLIPSE_POINTS)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    kwargs.setdefault(
        "label", _t("Boundary of the effective free-field region", language)
    )
    ax.plot(half_major * np.cos(angle), half_minor * np.sin(angle), **kwargs)
    rod_end = half_major + _ROD_OVERHANG * result.major_axis_m
    ax.plot(
        [half_distance, rod_end],
        [0.0, 0.0],
        color=_C_MUTED,
        lw=4.0,
        solid_capstyle="butt",
        label=_t("Mounting rod", language),
    )
    distance = format_number(result.source_distance_m, language, decimals=2)
    ax.plot(
        [-half_distance, half_distance],
        [0.0, 0.0],
        color=_C_TERTIARY,
        lw=1.2,
        ls="--",
        label=_t("Direct path, $d$ = {d} m", language, d=distance),
    )
    ax.plot(
        [-half_distance],
        [0.0],
        ls="none",
        marker="s",
        ms=8.0,
        color=_C_SECONDARY,
        label=_t("Sound source, F1", language),
    )
    ax.plot(
        [half_distance],
        [0.0],
        ls="none",
        marker="o",
        ms=7.0,
        color=_C_REFERENCE,
        label=_t("Microphone, F2", language),
    )
    ax.set_ylim(-_REGION_MARGIN * half_minor, _REGION_MARGIN * half_minor)
    ax.set_xlim(
        -_REGION_MARGIN * half_major, rod_end + (_REGION_MARGIN - 1.0) * half_major
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(_t("Along the axis [m]", language))
    ax.set_ylabel(_t("Across the axis [m]", language))
    ax.set_title(
        _t(
            r"Effective free-field region (IEC 61094-8 B.1): $A = d + \tau c$ = {a} m",
            language,
            a=format_number(result.major_axis_m, language, decimals=2),
        )
        + "\n"
        + _t(
            r"$\tau$ = {tau} ms, $c$ = {c} m/s; clearance {b} m across, {r} m behind the microphone",
            language,
            tau=format_number(1000.0 * result.window_time_s, language, decimals=1),
            c=format_number(result.speed_of_sound, language, decimals=1),
            b=format_number(half_minor, language, decimals=2),
            r=format_number(result.rod_clearance_m, language, decimals=2),
        )
    )
    ax.grid(visible=True, alpha=0.3)
    # Beside the axes rather than on them: inside, a legend covers the region
    # it describes or the source and the microphone on its axis.
    ax.legend(fontsize="small", loc="center left", bbox_to_anchor=(1.02, 0.5))
    localize_axes(ax, language)
    return ax
