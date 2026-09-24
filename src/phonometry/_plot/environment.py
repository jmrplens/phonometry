#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the environmental domain (lazy imports from result .plot())."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, cast

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _LEGEND_UPPER_LEFT,
    _LEGEND_UPPER_RIGHT,
    _band_axis,
    _field_cmap,
    _freq_axis,
    _import_pyplot,
    _new_axes,
    _plot_two_runs,
    format_frequency_axis,
    place_legend_clear,
    style_default,
    styled,
    theme_fill,
    theme_line,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from ..environment.assessment.exposure_distribution import SelDistribution
    from ..environment.assessment.impulsive_sound import ImpulseProminenceResult
    from ..environment.assessment.measurement import TonalAssessmentResult
    from ..environment.assessment.soundscape import (
        MethodASummary,
        MethodBSummary,
        PleasantnessEventfulness,
        SoundscapeCorrelation,
        SourceRanking,
    )
    from ..environment.assessment.soundscape_binaural import BinauralIndicators
    from ..environment.assessment.spain import (
        ActivityAssessment,
        TonalCorrectionResult,
    )
    from ..environment.propagation.air_absorption import AtmosphericAttenuation
    from ..environment.propagation.barrier_in_situ import (
        MeasuredBarrierInsertionLoss,
    )
    from ..environment.propagation.ground_barriers import (
        BarrierInsertionLoss,
        SphericalGroundResult,
    )
    from ..environment.propagation.noise_reducing_devices import RoadDeviceRating
    from ..environment.propagation.outdoor_propagation import OutdoorAttenuation
    from ..environment.propagation.refraction import (
        AtmosphericPEResult,
        AtmosphericRayResult,
        EffectiveSoundSpeedProfile,
    )
    from ..environment.sources.cnossos_rail import RailwayEmissionResult
    from ..environment.sources.cnossos_road import RoadEmissionResult
    from ..environment.sources.statistical_pass_by import (
        PassByRegression,
        StatisticalPassByResult,
    )
    from ..environment.sources.wind_turbine import WindTurbineTonalityResult

#: Spanish translations of the fixed strings rendered by the environmental
#: ``.plot()`` renderers, keyed by their verbatim English text.  ``_t``
#: returns the English key unchanged for any language other than ``"es"``,
#: so the English output is byte-for-byte identical to the pre-i18n
#: renderers.
#: Axis labels the renderers repeat; the Spanish table is keyed by the same
#: constants, so a label is written once.
_FREQ_LABEL = "Frequency [Hz]"
_HEIGHT_LABEL = "Height [m]"
_RANGE_LABEL = "Range [m]"
_TOTAL_A_LABEL = "$A$, total"
_FREE_FIELD_LABEL = "Level re free field [dB]"
#: The y label three barrier plots share, named once so the translation
#: table and the axes cannot drift apart.
_INSERTION_LOSS_LABEL = "Insertion loss [dB]"
_LT_LABEL = "$L_\\mathrm{t}$ [dB]"
#: The abscissa of the three ISO 13474 views: the level ``x`` the density and
#: the exceedance are functions of.
_SEL_X_LABEL = "Single-event sound exposure level $x$ [dB]"
#: Axis labels and legend names of the two ISO 11819-1 renderers, the names
#: keyed by vehicle category, written once so the table and the axes agree.
_SPB_SPEED_LABEL = "Vehicle speed [km/h]"
_SPB_LEVEL_LABEL = "Maximum level $L_\\mathrm{AFmax}$ [dB]"
_SPB_CATEGORY_LABELS: dict[str, str] = {
    "1": "Cars (1)",
    "2a": "Dual-axle heavy (2a)",
    "2b": "Multi-axle heavy (2b)",
}

_STRINGS: dict[str, str] = {
    "Narrowband spectrum": "Espectro de banda estrecha",
    "Critical band": "Banda crítica",
    "Masking level": "Nivel de enmascaramiento",
    "Tone": "Tono",
    _FREQ_LABEL: "Frecuencia [Hz]",
    "Level [dB]": "Nivel [dB]",
    "IEC 61400-11 tonal audibility": "Audibilidad tonal IEC 61400-11",
    "threshold": "umbral",
    "Impulses": "Impulsos",
    "Governing": "Determinante",
    "Predicted prominence $P$": "Prominencia prevista $P$",
    "Adjustment $K_\\mathrm{I}$ [dB]": "Ajuste $K_\\mathrm{I}$ [dB]",
    # The decimal lives inside the mathematics, out of reach of the automatic
    # comma pass, so the Spanish value carries it already converted; the braces
    # keep mathtext from spacing the comma as the punctuation mark it is.
    r"$K_\mathrm{I} = 1.8\,(P-5)$": r"$K_\mathrm{I} = 1{,}8\,(P-5)$",
    "NT ACOU 112: impulse adjustment to $L_\\mathrm{Aeq}$": "NT ACOU 112: ajuste por impulsos a $L_\\mathrm{Aeq}$",
    "knees $\\Delta L_\\mathrm{ta}=4,\\,10$ dB": "codos $\\Delta L_\\mathrm{ta}=4,\\,10$ dB",
    "Tonal audibility $\\Delta L_\\mathrm{ta}$ [dB]": "Audibilidad tonal $\\Delta L_\\mathrm{ta}$ [dB]",
    "Tonal adjustment $K_\\mathrm{t}$ [dB]": "Ajuste tonal $K_\\mathrm{t}$ [dB]",
    "ISO 1996-2 tonal adjustment": "Ajuste tonal ISO 1996-2",
    r"$A_{\mathrm{div}}$, divergence": r"$A_{\mathrm{div}}$, divergencia",
    r"$A_{\mathrm{atm}}$, atmospheric": r"$A_{\mathrm{atm}}$, atmosférica",
    r"$A_{\mathrm{gr}}$, ground": r"$A_{\mathrm{gr}}$, suelo",
    r"$A_{\mathrm{bar}}$, barrier": r"$A_{\mathrm{bar}}$, barrera",
    _TOTAL_A_LABEL: _TOTAL_A_LABEL,
    "Attenuation $A$ [dB]": "Atenuación $A$ [dB]",
    "ISO 9613-2 attenuation breakdown": "Desglose de atenuación ISO 9613-2",
    "CNOSSOS-EU railway source line power": (
        "Potencia de la línea fuente ferroviaria CNOSSOS-EU"
    ),
    "Both heights": "Ambas alturas",
    "Source A (0,5 m)": "Fuente A (0,5 m)",
    "Source B (4,0 m)": "Fuente B (4,0 m)",
    "Excess attenuation $\\Delta L$": "Atenuación en exceso $\\Delta L$",
    "Free field (0 dB)": "Campo libre (0 dB)",
    "Hard-ground limit (+6 dB)": "Límite de suelo duro (+6 dB)",
    _FREE_FIELD_LABEL: "Nivel re campo libre [dB]",
    "Spherical-wave ground effect (Weyl-Van der Pol)": "Efecto de suelo de onda esférica (Weyl-Van der Pol)",
    "Insertion loss": "Pérdida por inserción",
    "exact": "exacto",
    "ground": "suelo",
    "Grazing limit (5 dB)": "Límite rasante (5 dB)",
    _INSERTION_LOSS_LABEL: "Pérdida por inserción [dB]",
    "Sound pressure level [dB]": "Nivel de presión acústica [dB]",
    "Band": "Banda",
    "Barrier insertion loss": "Pérdida por inserción de barrera",
    "Receiver level before the barrier": "Nivel en el receptor antes de la barrera",
    "Receiver level after the barrier": "Nivel en el receptor después de la barrera",
    "Measured insertion loss $D_{IL}$": "Pérdida por inserción medida $D_{IL}$",
    "Measured insertion loss $D'_{IL}$": "Pérdida por inserción medida $D'_{IL}$",
    "A barrier measured where it stands": "Una barrera medida donde está",
    "Effective sound speed [m/s]": "Velocidad efectiva del sonido [m/s]",
    _HEIGHT_LABEL: "Altura [m]",
    _RANGE_LABEL: "Distancia [m]",
    "Effective sound-speed profile": "Perfil de velocidad efectiva del sonido",
    "Source": "Fuente",
    "Atmospheric ray paths": "Trayectorias de rayos atmosféricos",
    "GFPE relative sound level": "Nivel sonoro relativo GFPE",
    r"Attenuation coefficient $\alpha$ [dB/km]": r"Coeficiente de atenuación $\alpha$ [dB/km]",
    "ISO 9613-1 atmospheric attenuation": "Atenuación atmosférica ISO 9613-1",
    "Band level": "Nivel de banda",
    "$L_\\mathrm{t}$ vs neighbour mean": "$L_\\mathrm{t}$ frente a la media de contiguas",
    "Band level [dB]": "Nivel de banda [dB]",
    _LT_LABEL: _LT_LABEL,
    "RD 1367/2007 tonal correction $K_\\mathrm{{t}}$ = {kt} dB": "Corrección tonal $K_\\mathrm{{t}}$ = {kt} dB (RD 1367/2007)",
    "max $L_{Keq,Ti}$": "máx. $L_{Keq,Ti}$",
    "$L_{Keq,x}$ (daily)": "$L_{Keq,x}$ (diario)",
    "$L_{K,x}$ (annual)": "$L_{K,x}$ (anual)",
    "limit + 5 dB": "límite + 5 dB",
    "limit + 3 dB": "límite + 3 dB",
    "limit": "límite",
    "Day": "Día",
    "Evening": "Tarde",
    "Night": "Noche",
    "Corrected level [dB]": "Nivel corregido [dB]",
    "RD 1367/2007 assessment vs limit values": "Evaluación RD 1367/2007 frente a los valores límite",
    "Total line": "Línea total",
    "Light vehicles (1)": "Vehículos ligeros (1)",
    "Medium heavy vehicles (2)": "Vehículos pesados medios (2)",
    "Heavy vehicles (3)": "Vehículos pesados (3)",
    "Mopeds (4a)": "Ciclomotores (4a)",
    "Motorcycles (4b)": "Motocicletas (4b)",
    "CNOSSOS-EU road source line power": "Potencia de la línea fuente viaria CNOSSOS-EU",
    # ISO 11819-1, the statistical pass-by of a road surface.
    _SPB_CATEGORY_LABELS["1"]: "Turismos (1)",
    _SPB_CATEGORY_LABELS["2a"]: "Pesados de dos ejes (2a)",
    _SPB_CATEGORY_LABELS["2b"]: "Pesados de más de dos ejes (2b)",
    _SPB_SPEED_LABEL: "Velocidad del vehículo [km/h]",
    _SPB_LEVEL_LABEL: "Nivel máximo $L_\\mathrm{AFmax}$ [dB]",
    "Pass-bys": "Pasos",
    "Regression line": "Recta de regresión",
    "Window of clause 9.3 for the reference speed": (
        "Ventana del apartado 9.3 para la velocidad de referencia"
    ),
    "ISO 11819-1 regression": "Regresión ISO 11819-1",
    "ISO 11819-1 statistical pass-by": "Paso estadístico ISO 11819-1",
    _SEL_X_LABEL: "Nivel de exposición sonora de un suceso $x$ [dB]",
    r"Class density $\rho(x)$ [1/dB]": r"Densidad de las clases $\rho(x)$ [1/dB]",
    r"Continuous density $\rho^{*}(x)$ [1/dB]": r"Densidad continua $\rho^{*}(x)$ [1/dB]",
    r"Probability of exceeding $x$": r"Probabilidad de superar $x$",
    "ISO 13474: the classes before the turbulent spread": (
        "ISO 13474: las clases antes de la dispersión turbulenta"
    ),
    "ISO 13474: continuous density": "ISO 13474: densidad continua",
    "ISO 13474: exceedance of the sound exposure level": (
        "ISO 13474: superación del nivel de exposición sonora"
    ),
    "long-term level": "nivel a largo plazo",
}


def _t(text: str, language: str = "en") -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    return _STRINGS.get(text, text) if language == "es" else text


def plot_atmospheric_attenuation(
    result: AtmosphericAttenuation,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Pure-tone atmospheric attenuation coefficient vs frequency (ISO 9613-1).

    Draws ``alpha`` in dB/km (the Table 1 unit, i.e. the stored dB/m ``x 1000``)
    on a logarithmic frequency axis for the result's atmospheric conditions, the
    classic ISO 9613-1:1993 curve: the ``f^2`` low-frequency rise and the
    humidity-dependent relaxation roll-off.

    :param result: An
        :class:`~phonometry.environment.propagation.air_absorption.AtmosphericAttenuation`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``alpha`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma, fmt_minus, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    alpha_km = np.asarray(result.attenuation_coefficient, dtype=np.float64) * 1000.0
    # ISO 9613-1 is tabulated down to -20 degC, so the reading really can be
    # negative: fmt_minus signs it typographically without touching the hyphen
    # of an exponent that ":g" may emit.
    t_str = decimal_comma(fmt_minus(result.temperature_c, "g"), language)
    rh_str = decimal_comma(f"{result.relative_humidity_percent:g}", language)
    rh_unit = "% HR" if language == "es" else "% RH"
    label = f"{t_str} °C, {rh_str} {rh_unit}"
    # dB/km is already a logarithmic quantity, so the ordinate stays linear;
    # only the frequency axis is logarithmic (semilogx + format_frequency_axis).
    ax.semilogx(
        freqs, alpha_km, **styled(kwargs, color=_C_PRIMARY, lw=1.8, label=label)
    )
    fmin, fmax = float(freqs.min()), float(freqs.max())
    ax.set_xlim(fmin, fmax)
    format_frequency_axis(ax, fmin, fmax, language=language)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(r"Attenuation coefficient $\alpha$ [dB/km]", language))
    ax.set_title(_t("ISO 9613-1 atmospheric attenuation", language))
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_LEFT, fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_wind_turbine_tonality(
    result: WindTurbineTonalityResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Narrowband spectrum with the critical band, masking level and the tone.

    :param result: A :class:`~phonometry.environment.sources.wind_turbine.WindTurbineTonalityResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the spectrum ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes
    from ..environment.sources.wind_turbine import _critical_band_edges

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    levels = np.asarray(result.levels, dtype=np.float64)
    fc = result.tone_frequency
    lo, hi = _critical_band_edges(fc)
    ax.plot(
        freqs,
        levels,
        **styled(
            kwargs, color=_C_PRIMARY, lw=1.0, label=_t("Narrowband spectrum", language)
        ),
    )
    ax.axvspan(
        lo, hi, color=_C_TERTIARY, alpha=0.12, label=_t("Critical band", language)
    )
    ax.axhline(
        result.masking_level,
        color=_C_MUTED,
        ls="--",
        lw=1.0,
        label=f"{_t('Masking level', language)} ({format_number(result.masking_level, language)} dB)",
    )
    ax.plot(
        [fc],
        [result.tone_level],
        "o",
        color=_C_REFERENCE,
        label=f"{_t('Tone', language)} ({format_number(result.tone_level, language)} dB)",
    )
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Level [dB]", language))
    ax.set_title(
        f"{_t('IEC 61400-11 tonal audibility', language)} $\\Delta L_\\mathrm{{a}}$ = {format_number(result.tonal_audibility, language)} dB"
    )
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_impulse_prominence(
    result: ImpulseProminenceResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Adjustment curve ``KI(P)`` with the candidate impulses marked.

    :param result: An :class:`~phonometry.environment.assessment.impulsive_sound.ImpulseProminenceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the impulses ``scatter``.
    :return: The axes.
    """
    from .._i18n import decimal_comma, format_number, localize_axes
    from ..environment.assessment.impulsive_sound import (
        ADJUSTMENT_THRESHOLD,
        impulse_adjustment,
    )

    ax = ax if ax is not None else _new_axes()
    per = np.asarray(result.per_impulse, dtype=np.float64)
    per_max = float(per.max()) if per.size else 0.0
    p_max = max(per_max, result.prominence, 15.0) + 1.0
    grid = np.linspace(0.0, p_max, 200)
    ax.plot(
        grid,
        impulse_adjustment(grid),
        color=_C_PRIMARY,
        label=_t(r"$K_\mathrm{I} = 1.8\,(P-5)$", language),
    )
    ax.axvline(
        ADJUSTMENT_THRESHOLD,
        color=_C_MUTED,
        ls=":",
        label=f"{_t('threshold', language)} $P = {decimal_comma(f'{ADJUSTMENT_THRESHOLD:g}', language)}$",
    )

    style_default(kwargs, "color", _C_PRIMARY_LIGHT)
    kwargs.setdefault("zorder", 3)
    kwargs.setdefault("label", _t("Impulses", language))
    ax.scatter(per, impulse_adjustment(per), **kwargs)
    ax.scatter(
        [result.prominence],
        [result.adjustment],
        color=_C_REFERENCE,
        zorder=4,
        s=90,
        marker="*",
        label=f"{_t('Governing', language)}  $P$ = {format_number(result.prominence, language, decimals=2)},  "
        f"$K_\\mathrm{{I}}$ = {format_number(result.adjustment, language)} dB",
    )
    ax.set_xlabel(_t("Predicted prominence $P$", language))
    ax.set_ylabel(_t("Adjustment $K_\\mathrm{I}$ [dB]", language))
    ax.set_title(_t("NT ACOU 112: impulse adjustment to $L_\\mathrm{Aeq}$", language))
    ax.set_ylim(bottom=0.0)
    ax.legend(loc=_LEGEND_UPPER_LEFT, fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_tonal_adjustment(
    result: TonalAssessmentResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Tonal adjustment curve ``Kt(ΔLta)`` with the assessed tone marked.

    :param result: A
        :class:`~phonometry.environment.assessment.measurement.TonalAssessmentResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the assessed-tone ``scatter``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes
    from ..environment.assessment.measurement import tonal_adjustment

    ax = ax if ax is not None else _new_axes()
    top = max(result.audibility, 12.0) + 1.0
    grid = np.linspace(0.0, top, 200)
    curve = np.array([tonal_adjustment(d) for d in grid], dtype=np.float64)
    ax.plot(
        grid, curve, color=_C_PRIMARY, label=r"$K_\mathrm{t}(\Delta L_\mathrm{ta})$"
    )
    ax.axvline(
        4.0,
        color=_C_MUTED,
        ls=":",
        label=_t("knees $\\Delta L_\\mathrm{ta}=4,\\,10$ dB", language),
    )
    ax.axvline(10.0, color=_C_MUTED, ls=":")

    style_default(kwargs, "color", _C_REFERENCE)
    kwargs.setdefault("zorder", 4)
    kwargs.setdefault("s", 90)
    kwargs.setdefault("marker", "*")
    kwargs.setdefault(
        "label",
        rf"$\Delta L_\mathrm{{ta}}$ = {format_number(result.audibility, language)} dB,  "
        rf"$K_\mathrm{{t}}$ = {format_number(result.adjustment, language)} dB",
    )
    ax.scatter([result.audibility], [result.adjustment], **kwargs)
    ax.set_xlabel(_t("Tonal audibility $\\Delta L_\\mathrm{ta}$ [dB]", language))
    ax.set_ylabel(_t("Tonal adjustment $K_\\mathrm{t}$ [dB]", language))
    ax.set_title(_t("ISO 1996-2 tonal adjustment", language))
    ax.set_ylim(bottom=0.0)
    ax.legend(loc=_LEGEND_UPPER_LEFT, fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_outdoor_attenuation(
    result: OutdoorAttenuation,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Stacked per-band attenuation terms with the total overlaid (ISO 9613-2).

    The divergence, atmospheric, ground and barrier terms are stacked per
    octave band on separate positive and negative baselines (the ground
    effect can be a net *gain*), and the total attenuation ``A`` is drawn
    as the primary marker line on top.

    :param result: An
        :class:`~phonometry.environment.propagation.outdoor_propagation.OutdoorAttenuation`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the total-attenuation ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)
    n = freqs.size

    # Separate positive and negative cumulative baselines so a negative term
    # stacks below zero instead of being drawn on top of the previous bars;
    # the signed heights sum to a_total.
    pos_bottom = np.zeros(n)
    neg_bottom = np.zeros(n)
    terms = (
        (result.a_div, _C_PRIMARY, _t(r"$A_{\mathrm{div}}$, divergence", language)),
        (result.a_atm, _C_TERTIARY, _t(r"$A_{\mathrm{atm}}$, atmospheric", language)),
        (result.a_gr, _C_QUATERNARY, _t(r"$A_{\mathrm{gr}}$, ground", language)),
        (result.a_bar, _C_SECONDARY, _t(r"$A_{\mathrm{bar}}$, barrier", language)),
    )
    for values, color, label in terms:
        term = np.asarray(values, dtype=np.float64)
        bottom = np.where(term >= 0.0, pos_bottom, neg_bottom)
        ax.bar(positions, term, bottom=bottom, color=color, label=label)
        pos_bottom += np.maximum(term, 0.0)
        neg_bottom += np.minimum(term, 0.0)

    style_default(kwargs, "color", _C_REFERENCE)
    kwargs.setdefault("marker", "D")
    kwargs.setdefault("label", _t(_TOTAL_A_LABEL, language))
    ax.plot(positions, np.asarray(result.a_total, dtype=np.float64), zorder=4, **kwargs)
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.set_ylabel(_t("Attenuation $A$ [dB]", language))
    ax.set_title(_t("ISO 9613-2 attenuation breakdown", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_cnossos_rail_emission(
    result: RailwayEmissionResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-metre railway source-line power of the two equivalent source heights.

    Draws the energy-summed line power of the track as bars over the eight
    CNOSSOS-EU octave bands, with source A (0,5 m) and source B (4,0 m) overlaid
    as marker lines, so the bands where the roof and pantograph sources matter
    are read directly off the chart.

    :param result: A
        :class:`~phonometry.environment.sources.cnossos_rail.RailwayEmissionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the total-line-power ``bar`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)

    style_default(kwargs, "color", _C_PRIMARY_LIGHT)
    kwargs.setdefault("label", _t("Both heights", language))
    # A silent source carries -inf, which no axis can hold; masking it leaves
    # the band out of the drawing instead of collapsing the whole scale.
    total = np.asarray(result.total_line_power, dtype=np.float64)
    ax.bar(positions, np.where(np.isfinite(total), total, np.nan), **kwargs)

    styles = (
        (_C_PRIMARY, "o", "Source A (0,5 m)"),
        (_C_SECONDARY, "s", "Source B (4,0 m)"),
    )
    for row, (color, marker, label) in zip(
        np.asarray(result.line_power, dtype=np.float64), styles, strict=True
    ):
        ax.plot(
            positions,
            np.where(np.isfinite(row), row, np.nan),
            color=color,
            marker=marker,
            lw=1.2,
            ms=4,
            zorder=4,
            label=_t(label, language),
        )
    # Pure symbol notation, identical in every language, so it is set directly
    # rather than routed through the translation table.
    ax.set_ylabel(r"$L^{\prime}_{W,\mathrm{eq,line}}$ [dB re 1 pW/m]")
    ax.set_title(_t("CNOSSOS-EU railway source line power", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_spherical_ground(
    result: SphericalGroundResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Excess attenuation (level re free field) of the spherical-wave ground effect.

    Draws the relative sound level ``dL`` versus frequency with the ``+6 dB``
    hard-ground enhancement ceiling and the ``0 dB`` free-field reference, so the
    ground-effect dip and any surface-wave enhancement are both visible.

    :param result: A
        :class:`~phonometry.environment.propagation.ground_barriers.SphericalGroundResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``dL`` ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    d_l = np.asarray(result.excess_attenuation, dtype=np.float64)
    ax.plot(
        freqs,
        d_l,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.4,
            marker="o",
            ms=3.0,
            label=_t("Excess attenuation $\\Delta L$", language),
        ),
    )
    ax.axhline(0.0, color=_C_MUTED, lw=0.8, label=_t("Free field (0 dB)", language))
    ax.axhline(
        6.0,
        color=_C_REFERENCE,
        ls="--",
        lw=0.9,
        label=_t("Hard-ground limit (+6 dB)", language),
    )
    _freq_axis(ax, freqs, language=language)
    ax.set_ylabel(_t(_FREE_FIELD_LABEL, language))
    ax.set_title(_t("Spherical-wave ground effect (Weyl-Van der Pol)", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


#: Drawn name of each barrier model, keyed by the API token: the token itself
#: is snake_case, and an underscore outside mathematics is drawn as a literal
#: low line.  "Kurze-Anderson" is a compound of two surnames and is deliberately
#: absent from the translation table, so ``_t`` returns it unchanged.
_BARRIER_METHOD_LABELS: dict[str, str] = {
    "kurze_anderson": "Kurze-Anderson",
    "exact": "exact",
}


def plot_barrier_insertion_loss(
    result: BarrierInsertionLoss,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Barrier insertion loss versus frequency.

    :param result: A
        :class:`~phonometry.environment.propagation.ground_barriers.BarrierInsertionLoss`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the insertion-loss ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    il = np.asarray(result.insertion_loss, dtype=np.float64)
    ground_frag = f", {_t('ground', language)}" if result.ground else ""
    method_label = _t(
        _BARRIER_METHOD_LABELS.get(result.method, result.method), language
    )
    label = f"{_t('Insertion loss', language)} ({method_label}{ground_frag})"
    ax.plot(
        freqs,
        il,
        **styled(kwargs, color=_C_SECONDARY, lw=1.4, marker="s", ms=3.0, label=label),
    )
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.axhline(
        5.0, color=_C_MUTED, ls=":", lw=0.9, label=_t("Grazing limit (5 dB)", language)
    )
    _freq_axis(ax, freqs, language=language)
    ax.set_ylabel(_t(_INSERTION_LOSS_LABEL, language))
    ax.set_title(_t("Barrier insertion loss", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_sound_speed_profile(
    profile: EffectiveSoundSpeedProfile,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Effective sound-speed profile ``c_eff(z)`` (height on the vertical axis).

    :param profile: An
        :class:`~phonometry.environment.propagation.refraction.EffectiveSoundSpeedProfile`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the profile ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    z = np.asarray(profile.heights, dtype=np.float64)
    c = np.asarray(profile.sound_speeds, dtype=np.float64)
    label = profile.description or r"$c_\mathrm{eff}(z)$"
    ax.plot(c, z, **styled(kwargs, color=_C_PRIMARY, lw=1.4, label=label))
    ax.set_xlabel(_t("Effective sound speed [m/s]", language))
    ax.set_ylabel(_t(_HEIGHT_LABEL, language))
    ax.set_title(_t("Effective sound-speed profile", language))
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_atmospheric_rays(
    result: AtmosphericRayResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Curved sound-ray paths over the ground (height on the vertical axis).

    :param result: An
        :class:`~phonometry.environment.propagation.refraction.AtmosphericRayResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to each ray ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    r = np.asarray(result.ranges, dtype=np.float64)
    z = np.asarray(result.heights, dtype=np.float64)
    for i in range(r.shape[0]):
        ax.plot(r[i], z[i], **styled(kwargs, color=_C_PRIMARY, lw=0.7, alpha=0.7))
    ax.plot(
        [0.0],
        [result.source_height],
        "o",
        color=_C_REFERENCE,
        label=_t("Source", language),
    )
    ax.axhline(0.0, color=_C_MUTED, lw=1.0)
    ax.set_xlabel(_t(_RANGE_LABEL, language))
    ax.set_ylabel(_t(_HEIGHT_LABEL, language))
    ax.set_ylim(bottom=0.0)
    ax.set_title(_t("Atmospheric ray paths", language))
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_atmospheric_pe(
    result: AtmosphericPEResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Parabolic-equation relative-level field over the range-height plane.

    The field is drawn as a single raster image (``imshow``): per-cell vector
    quads are avoided so the figure stays light and free of moire (the repo's
    pcolormesh-in-SVG policy).  The default diverging colormap follows the
    axes background so the centre of the scale blends into the page --
    ``RdBu_r`` on a light background, the black-centred
    ``phonometry_field_dark`` on a dark one -- and ``cmap`` overrides it.

    :param result: An
        :class:`~phonometry.environment.propagation.refraction.AtmosphericPEResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``imshow``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

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
            "cmap": _field_cmap(ax),
            "vmin": -30.0,
            "vmax": vmax,
            "aspect": "auto",
            "origin": "lower",
            "interpolation": "bilinear",
            "extent": (float(r[0]), float(r[-1]), float(z[0]), float(z[-1])),
            **kwargs,
        },
    )
    cbar = ax.figure.colorbar(img, ax=ax, label=_t(_FREE_FIELD_LABEL, language))
    localize_axes(cbar.ax, language)
    ax.plot(
        [0.0],
        [result.source_height],
        "o",
        color="k",
        ms=4.0,
        label=_t("Source", language),
    )
    ax.set_xlabel(_t(_RANGE_LABEL, language))
    ax.set_ylabel(_t(_HEIGHT_LABEL, language))
    ax.set_title(
        f"{_t('GFPE relative sound level', language)} ({format_number(result.frequency, language, decimals=0)} Hz)"
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_tonal_correction_rd1367(
    result: TonalCorrectionResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """One-third-octave spectrum with the RD 1367/2007 emergence ``Lt`` per band.

    The band levels are drawn as bars on the left axis and the emergence
    ``Lt = Lf - Ls`` (the band level above the arithmetic mean of its two
    neighbours) on a twin right axis, with the band that governs ``Kt``
    highlighted.

    :param result: A
        :class:`~phonometry.environment.assessment.spain.TonalCorrectionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the band-level ``bar`` call.
    :return: The axes (the left, band-level axes).
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    levels = np.asarray(result.levels, dtype=np.float64)
    lt = np.asarray(result.differences, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)

    style_default(kwargs, "color", _C_PRIMARY_LIGHT)
    kwargs.setdefault("label", _t("Band level", language))
    ax.bar(positions, levels, width=0.72, **kwargs)
    ax.set_ylabel(_t("Band level [dB]", language))

    twin = ax.twinx()
    twin.plot(
        positions,
        lt,
        "o-",
        color=_C_SECONDARY,
        ms=4.0,
        label=_t("$L_\\mathrm{t}$ vs neighbour mean", language),
    )
    if result.governing_frequency is not None:
        index = int(np.argmin(np.abs(freqs - result.governing_frequency)))
        twin.plot(
            [positions[index]], [lt[index]], "*", color=_C_REFERENCE, ms=14.0, zorder=5
        )
    twin.set_ylabel(_t(_LT_LABEL, language))
    twin.axhline(0.0, color=_C_MUTED, lw=0.8)

    ax.set_title(
        _t(
            "RD 1367/2007 tonal correction $K_\\mathrm{{t}}$ = {kt} dB", language
        ).format(kt=format_number(result.correction, language, decimals=0))
    )
    handles, labels = ax.get_legend_handles_labels()
    extra_handles, extra_labels = twin.get_legend_handles_labels()
    ax.legend(
        handles + extra_handles,
        labels + extra_labels,
        loc=_LEGEND_UPPER_LEFT,
        fontsize="small",
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    localize_axes(twin, language)
    return ax


def plot_activity_assessment(
    result: ActivityAssessment,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-period RD 1367/2007 indices against their limit values.

    For every assessed evaluation period the three indices of Article 25.1 b
    are drawn as grouped bars (the largest measured ``LKeq,Ti``, the daily
    ``LKeq,x`` and the annual ``LK,x``) with their own limits marked on each
    group: the table limit plus 5 dB, plus 3 dB and the limit itself. A bar
    that exceeds its own limit is outlined in the exceedance colour.

    :param result: An
        :class:`~phonometry.environment.assessment.spain.ActivityAssessment`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``LKeq,x`` ``bar`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    periods = list(result.periods)
    labels = [_t(p.period.capitalize(), language) for p in periods]
    positions = _band_axis(ax, labels, xlabel=None, language=language)

    step = 0.28
    width = 0.24
    series = (
        (
            [p.max_phase_level for p in periods],
            [p.phase_limit for p in periods],
            [p.phase_pass for p in periods],
            _C_PRIMARY_LIGHT,
            _t("max $L_{Keq,Ti}$", language),
            _t("limit + 5 dB", language),
            -step,
            ":",
            False,
        ),
        (
            [float(p.reported_level) for p in periods],
            [p.daily_limit for p in periods],
            [p.daily_pass for p in periods],
            _C_PRIMARY,
            _t("$L_{Keq,x}$ (daily)", language),
            _t("limit + 3 dB", language),
            0.0,
            "--",
            True,
        ),
        (
            [
                float(p.reported_long_term)
                if p.reported_long_term is not None
                else np.nan
                for p in periods
            ],
            [p.limit for p in periods],
            [p.long_term_pass for p in periods],
            _C_TERTIARY,
            _t("$L_{K,x}$ (annual)", language),
            _t("limit", language),
            step,
            "-",
            False,
        ),
    )
    for (
        values,
        limits,
        verdicts,
        colour,
        label,
        limit_label,
        offset,
        dash,
        takes_kwargs,
    ) in series:
        # matplotlib types the dash style as a Literal; the series table above
        # carries it as a plain str, so narrow it back for the hlines call.
        style = cast("Any", dash)
        opts: dict[str, Any] = {"color": colour, "label": label}
        if takes_kwargs:
            # The caller's bar kwargs apply to the daily LKeq,x series, the one
            # the fiche and the guides treat as the headline result.
            opts.update(kwargs)
        bars = ax.bar(positions + offset, values, width=width, **opts)
        for bar, ok in zip(bars, verdicts, strict=True):
            if ok is False:
                bar.set_edgecolor(_C_REFERENCE)
                bar.set_linewidth(1.6)
        for index, limit in enumerate(limits):
            ax.hlines(
                limit,
                positions[index] + offset - 0.62 * width,
                positions[index] + offset + 0.62 * width,
                colors=_C_REFERENCE,
                linestyles=style,
                linewidth=1.5,
                label=limit_label if index == 0 else "_nolegend_",
                zorder=4,
            )

    # The categorical axis here carries two or three period names, not a band
    # sequence, so the 45-degree band-axis rotation is not needed.
    ax.set_xticklabels(labels, rotation=0, ha="center")
    ax.set_xlim(positions[0] - 0.5 - step, positions[-1] + 0.5 + step)

    ax.set_ylabel(_t("Corrected level [dB]", language))
    ax.set_title(_t("RD 1367/2007 assessment vs limit values", language))
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small", ncol=2)
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


#: Localised legend labels of the five CNOSSOS-EU road vehicle categories,
#: keyed by the Table [2.2.a] category code.
_ROAD_CATEGORY_LABELS: dict[str, str] = {
    "1": "Light vehicles (1)",
    "2": "Medium heavy vehicles (2)",
    "3": "Heavy vehicles (3)",
    "4a": "Mopeds (4a)",
    "4b": "Motorcycles (4b)",
}


#: Colour and marker of each road vehicle category, keyed by the category code
#: rather than by row position, so a category keeps its appearance whichever
#: subset of the five is present in the traffic mix.
_ROAD_CATEGORY_STYLE: dict[str, tuple[str, str]] = {
    "1": (_C_PRIMARY, "o"),
    "2": (_C_TERTIARY, "s"),
    "3": (_C_REFERENCE, "D"),
    "4a": (_C_SECONDARY, "^"),
    "4b": (_C_QUATERNARY, "v"),
}


def plot_cnossos_road_emission(
    result: RoadEmissionResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-metre road source-line power with its vehicle-category breakdown.

    Draws the energy-summed line power ``L'_W,eq,line,i`` of the traffic mix as
    bars over the eight CNOSSOS-EU octave bands, with the contribution of each
    vehicle category overlaid as a marker line, so the band where a category
    governs the source is read directly off the chart.

    :param result: A
        :class:`~phonometry.environment.sources.cnossos_road.RoadEmissionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the total-line-power ``bar`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)

    style_default(kwargs, "color", _C_PRIMARY_LIGHT)
    kwargs.setdefault("label", _t("Total line", language))
    # An empty category carries -inf, which no axis can hold; masking it leaves
    # the band out of the drawing instead of collapsing the whole scale.
    total = np.asarray(result.total_line_power, dtype=np.float64)
    ax.bar(positions, np.where(np.isfinite(total), total, np.nan), **kwargs)

    for row, category in zip(
        np.asarray(result.line_power, dtype=np.float64), result.categories, strict=True
    ):
        color, marker = _ROAD_CATEGORY_STYLE[category.value]
        ax.plot(
            positions,
            np.where(np.isfinite(row), row, np.nan),
            color=color,
            marker=marker,
            lw=1.2,
            ms=4,
            zorder=4,
            label=_t(_ROAD_CATEGORY_LABELS[category.value], language),
        )
    # Pure symbol notation, identical in every language, so it is set directly
    # rather than routed through the translation table.
    ax.set_ylabel(r"$L^{\prime}_{W,\mathrm{eq,line}}$ [dB re 1 pW/m]")
    ax.set_title(_t("CNOSSOS-EU road source line power", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_road_device_rating(
    result: RoadDeviceRating,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The per-band performance of a road device against the spectrum weighting it.

    The eighteen one-third octave bands of EN 1793-3 carry two things at
    once: what the device does in each of them, drawn as bars on the left
    axis, and how much each band counts, drawn as the normalised traffic
    noise spectrum on a right axis. The single number in the title is what
    the two of them come to.

    :param result: A
        :class:`~phonometry.environment.propagation.noise_reducing_devices.RoadDeviceRating`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the per-band ``bar`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.bands_hz, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)
    absorbing = result.quantity == "absorption"

    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault(
        "label",
        _t(r"$\alpha_\mathrm{S}$, absorption coefficient", language)
        if absorbing
        else _t(r"$R$, sound reduction index [dB]", language),
    )
    ax.bar(positions, np.asarray(result.values, dtype=np.float64), **kwargs)
    ax.set_ylabel(
        _t("Sound absorption coefficient", language)
        if absorbing
        else _t("Sound reduction index [dB]", language)
    )

    spectrum = ax.twinx()
    spectrum.plot(
        positions,
        np.asarray(result.weights, dtype=np.float64),
        color=_C_SECONDARY,
        marker="o",
        lw=1.6,
        label=_t(r"$L_i$, normalised traffic noise [dB]", language),
    )
    spectrum.set_ylabel(_t(r"$L_i$ [dB]", language), color=_C_SECONDARY)
    spectrum.tick_params(axis="y", labelcolor=_C_SECONDARY)

    symbol = r"$DL_\alpha$" if absorbing else r"$DL_R$"
    ax.set_title(
        _t(f"{symbol} = {result.reported} dB, category {result.category}", language)
    )
    handles, labels = ax.get_legend_handles_labels()
    extra = spectrum.get_legend_handles_labels()
    legend = ax.legend(handles + extra[0], labels + extra[1], fontsize="small")
    place_legend_clear(legend, spectrum)
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    localize_axes(spectrum, language)
    return ax


def plot_barrier_in_situ(
    result: MeasuredBarrierInsertionLoss,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The two receiver spectra of ISO 10847 and the insertion loss between them.

    The reference position does not appear as a curve: its whole job is to
    normalise the two receiver spectra against each other, and it has already
    done that by the time the result exists.

    :param result: A
        :class:`~phonometry.environment.propagation.barrier_in_situ.MeasuredBarrierInsertionLoss`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the insertion-loss ``Axes.plot``.
    :return: The axes.
    """
    symbol = (
        "Measured insertion loss $D_{IL}$"
        if result.method == "direct"
        else "Measured insertion loss $D'_{IL}$"
    )
    return _plot_two_runs(
        ax,
        None if result.frequencies is None else np.asarray(result.frequencies),
        np.asarray(result.receiver_before_db, dtype=np.float64),
        np.asarray(result.receiver_after_db, dtype=np.float64),
        np.asarray(result.insertion_loss_db, dtype=np.float64),
        labels=(
            _t("Receiver level before the barrier", language),
            _t("Receiver level after the barrier", language),
            _t(symbol, language),
        ),
        ylabel=_t("Sound pressure level [dB]", language),
        difference_label=_t(_INSERTION_LOSS_LABEL, language),
        frequency_label=_t(_FREQ_LABEL, language),
        band_label=_t("Band", language),
        title=_t("A barrier measured where it stands", language),
        language=language,
        kwargs=kwargs,
    )


#: Colour and marker of each ISO 11819-1 vehicle category: the CNOSSOS-EU
#: pairs of the nearest categories, so a car looks the same on both pages.
_SPB_CATEGORY_STYLE: dict[str, tuple[str, str]] = {
    "1": (_C_PRIMARY, "o"),
    "2a": (_C_TERTIARY, "s"),
    "2b": (_C_REFERENCE, "D"),
}

#: Round speeds the speed axis is labelled at, in km/h.
_SPB_SPEED_TICKS_KMH: tuple[float, ...] = (
    30.0,
    40.0,
    50.0,
    60.0,
    70.0,
    80.0,
    90.0,
    100.0,
    110.0,
    120.0,
    140.0,
    160.0,
)

#: How far past the drawn speeds the speed axis reaches, as a ratio.
_SPB_AXIS_MARGIN = 1.08


def _spb_speed_axis(ax: Axes, speeds_kmh: list[float], language: str) -> None:
    """A logarithmic speed axis, the one the regression of 9.1 is a line on."""
    import matplotlib.ticker as mticker

    from .._i18n import format_number

    low = min(speeds_kmh) / _SPB_AXIS_MARGIN
    high = max(speeds_kmh) * _SPB_AXIS_MARGIN
    ax.set_xscale("log")
    ax.set_xlim(low, high)
    ticks = [tick for tick in _SPB_SPEED_TICKS_KMH if low <= tick <= high]
    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(
            lambda value, _pos: format_number(value, language, decimals=0)
        )
    )
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.set_xlabel(_t(_SPB_SPEED_LABEL, language))
    ax.set_ylabel(_t(_SPB_LEVEL_LABEL, language))


def _spb_line(
    regression: PassByRegression, low: float, high: float
) -> tuple[np.ndarray, np.ndarray]:
    """The fitted line between two speeds, as the arrays to draw."""
    speeds = np.geomspace(low, high, 32)
    levels = regression.intercept_db + regression.slope_db_per_decade * np.log10(speeds)
    return speeds, levels


def plot_pass_by_regression(
    result: PassByRegression,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """One category of pass-bys against speed, the line through them and ``L_veh``.

    The pass-bys are drawn against the logarithm of speed, the axis on which
    ISO 11819-1 9.1 fits its line, so the regression is straight. The band is
    the 9.3 window the reference speed has to fall in, and the diamond is the
    vehicle sound level read off the line at the Table 1 reference speed.

    :param result: A
        :class:`~phonometry.environment.sources.statistical_pass_by.PassByRegression`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the fitted line.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    color, marker = _SPB_CATEGORY_STYLE[result.vehicle_category]
    speeds = np.asarray(result.speeds_kmh, dtype=np.float64)
    levels = np.asarray(result.max_levels_db, dtype=np.float64)
    low, high = result.speed_window_kmh
    ax.axvspan(
        low,
        high,
        color=theme_fill(_C_PRIMARY, ax),
        label=_t("Window of clause 9.3 for the reference speed", language),
    )
    ax.plot(
        speeds,
        levels,
        linestyle="none",
        marker=marker,
        ms=4,
        color=color,
        alpha=0.55,
        label=f"{_t('Pass-bys', language)} ($n$ = {result.vehicle_count})",
    )
    span = [float(speeds.min()), float(speeds.max()), result.reference_speed_kmh]
    line_x, line_y = _spb_line(result, min(span), max(span))
    ax.plot(
        line_x,
        line_y,
        **styled(
            kwargs,
            color=color,
            lw=1.8,
            label=_t("Regression line", language),
        ),
    )
    ax.plot(
        [result.reference_speed_kmh],
        [result.vehicle_sound_level_db],
        linestyle="none",
        marker="D",
        ms=8,
        color=_C_SECONDARY,
        zorder=5,
        label=(
            r"$L_\mathrm{veh}$ = "
            f"{format_number(result.reported_vehicle_sound_level_db, language)} dB, "
            f"{format_number(result.reference_speed_kmh, language, decimals=0)} km/h"
        ),
    )
    _spb_speed_axis(ax, [*span, low, high], language)
    ax.set_title(
        f"{_t('ISO 11819-1 regression', language)}: "
        f"{_t(_SPB_CATEGORY_LABELS[result.vehicle_category], language)}"
    )
    ax.grid(visible=True, which="major", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_statistical_pass_by(
    result: StatisticalPassByResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The three clouds of pass-bys of a surface, their lines and the index.

    Cars, dual-axle and multi-axle heavy vehicles are drawn against the
    logarithm of speed, each with the line ISO 11819-1 9.1 fits through it and
    a diamond where the line crosses the category's reference speed, which is
    the vehicle sound level 9.2 reads. The title carries the index those three
    levels make.

    :param result: A
        :class:`~phonometry.environment.sources.statistical_pass_by.StatisticalPassByResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the three fitted lines.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    extent: list[float] = []
    for category, regression in result.regressions.items():
        color, marker = _SPB_CATEGORY_STYLE[category]
        speeds = np.asarray(regression.speeds_kmh, dtype=np.float64)
        levels = np.asarray(regression.max_levels_db, dtype=np.float64)
        ax.plot(
            speeds,
            levels,
            linestyle="none",
            marker=marker,
            ms=3.5,
            color=color,
            alpha=0.35,
        )
        span = [
            float(speeds.min()),
            float(speeds.max()),
            regression.reference_speed_kmh,
        ]
        extent.extend(span)
        line_x, line_y = _spb_line(regression, min(span), max(span))
        line_kwargs = styled(kwargs, color=color, lw=1.8)
        line_kwargs.setdefault(
            "label",
            f"{_t(_SPB_CATEGORY_LABELS[category], language)}: "
            r"$L_\mathrm{veh}$ = "
            f"{format_number(regression.reported_vehicle_sound_level_db, language)} dB",
        )
        ax.plot(line_x, line_y, **line_kwargs)
        ax.plot(
            [regression.reference_speed_kmh],
            [regression.vehicle_sound_level_db],
            linestyle="none",
            marker="D",
            ms=8,
            markeredgecolor=_C_SECONDARY,
            markerfacecolor=color,
            zorder=5,
        )
    _spb_speed_axis(ax, extent, language)
    ax.set_title(
        f"{_t('ISO 11819-1 statistical pass-by', language)}: SPBI = "
        f"{format_number(result.reported_index_db, language)} dB"
    )
    ax.grid(visible=True, which="major", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


#: The exceedance levels Figure A.3 of ISO 13474 prints beside its curve, in
#: per cent of events.
_SEL_FIGURE_PERCENTS = (95.0, 50.0, 10.0, 5.0, 1.0)

#: Standard deviations of the turbulent spread drawn either side of the
#: classes, so every Gaussian is plotted out to where it no longer shows.
_SEL_SPREAD_MARGIN = 4.0


def plot_sel_distribution(
    result: SelDistribution,
    ax: Axes | None = None,
    *,
    view: str = "density",
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The ISO 13474 distribution as its class density, density or exceedance.

    ``"classes"`` draws the step density :math:`\rho(x)` over the class
    boundaries (Annex A Figure A.1); ``"density"`` the continuous density
    :math:`\rho^{*}(x)` with the long-term level of Equation (A.4) marked
    (Figure A.2); ``"exceedance"`` the probability of exceeding ``x`` with the
    95, 50, 10, 5 and 1 per cent exceedance levels marked (Figure A.3).

    :param result: A
        :class:`~phonometry.environment.assessment.exposure_distribution.SelDistribution`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param view: ``"classes"``, ``"density"`` or ``"exceedance"``.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the primary artist (the step outline or the
        curve).
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    lower = np.asarray(result.lower_bounds_db, dtype=np.float64)
    upper = np.asarray(result.upper_bounds_db, dtype=np.float64)
    if view == "classes":
        edges = np.concatenate((lower, upper[-1:]))
        ax.stairs(
            np.asarray(result.class_densities_per_db, dtype=np.float64),
            edges,
            **styled(kwargs, color=_C_PRIMARY, lw=1.4),
        )
        ax.set_ylabel(_t(r"Class density $\rho(x)$ [1/dB]", language))
        ax.set_title(_t("ISO 13474: the classes before the turbulent spread", language))
    else:
        margin = _SEL_SPREAD_MARGIN * result.sigma_db
        x = np.linspace(
            float(lower[0]) - result.level_shift_db - margin,
            float(upper[-1]) + margin,
            801,
        )
        long_term = result.distribution_long_term_level_db
        # The long-term level is a reference on the level axis, not a series:
        # drawn in the page's own ink, dimmed, so it reads on both themes and
        # does not compete with the curve for colour. It is the level taken
        # over the spread distribution, which Figure A.3 names LT2 beside the
        # LT1 of Equation (7); both print 37,0 dB, so the label names which.
        ink = theme_line(ax.xaxis.label.get_color(), ax, quiet=0.8)
        lt_label = (
            f"LT2 ({_t('long-term level', language)}) "
            f"{format_number(long_term, language)} dB"
        )
        if view == "density":
            ax.plot(
                x,
                np.asarray(result.density(x)),
                **styled(kwargs, color=_C_PRIMARY, lw=1.8),
            )
            ax.axvline(long_term, color=ink, ls="--", lw=1.2, label=lt_label)
            ax.set_ylabel(_t(r"Continuous density $\rho^{*}(x)$ [1/dB]", language))
            sigma = format_number(result.sigma_db, language)
            ax.set_title(
                f"{_t('ISO 13474: continuous density', language)}, "
                f"$\\sigma$ = {sigma} dB"
            )
        else:
            ax.plot(
                x,
                np.asarray(result.exceedance(x)),
                **styled(kwargs, color=_C_PRIMARY, lw=1.8),
            )
            levels = np.asarray(result.exceedance_level(_SEL_FIGURE_PERCENTS))
            markers = (_C_SECONDARY, _C_TERTIARY, _C_QUATERNARY, _C_REFERENCE, _C_MUTED)
            for percent, level, color in zip(
                _SEL_FIGURE_PERCENTS, levels, markers, strict=True
            ):
                ax.plot(
                    [float(level)],
                    [percent / 100.0],
                    "o",
                    color=color,
                    ms=6,
                    label=(
                        f"$L_{{{percent:.0f}}}$ = "
                        f"{format_number(float(level), language)} dB"
                    ),
                )
            ax.axvline(long_term, color=ink, ls="--", lw=1.2, label=lt_label)
            ax.set_ylabel(_t(r"Probability of exceeding $x$", language))
            ax.set_ylim(0.0, 1.05)
            ax.set_title(
                _t("ISO 13474: exceedance of the sound exposure level", language)
            )
        ax.set_xlim(float(x[0]), float(x[-1]))
        legend = ax.legend(fontsize="small")
        place_legend_clear(legend)
    ax.set_xlabel(_t(_SEL_X_LABEL, language))
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


# ---------------------------------------------------------------------------
# ISO/TS 12913: soundscape questionnaires and binaural analysis
# ---------------------------------------------------------------------------

#: The eight attributes of Figure A.1 of ISO/TS 12913-3, as (label, angle in
#: degrees from the pleasantness axis, drawn solid): the two main dimensions
#: solid, the two rotated by 45 degrees dashed, as the figure draws them.
_PAQ_AXES: tuple[tuple[str, float, bool], ...] = (
    ("PLEASANT", 0.0, True),
    ("VIBRANT", 45.0, False),
    ("EVENTFUL", 90.0, True),
    ("CHAOTIC", 135.0, False),
    ("ANNOYING", 180.0, True),
    ("MONOTONOUS", 225.0, False),
    ("UNEVENTFUL", 270.0, True),
    ("CALM", 315.0, False),
)

#: Marker shapes, one per round of the site colours, so that a study with
#: more sites than colours still tells every site apart.
_SITE_MARKERS = ("o", "s", "^", "D")

#: How many item labels fit side by side under a column plot before they are
#: tilted to keep clear of each other.
_FLAT_ITEM_LABELS = 2

#: Site colours, cycled.
_SITE_COLORS = (
    _C_PRIMARY,
    _C_SECONDARY,
    _C_TERTIARY,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_MUTED,
)

#: The subject of each part of Method A, as Table A.1 of ISO/TS 12913-3 names
#: them, for the titles.
_METHOD_A_SUBJECTS: dict[int, str] = {
    1: "sound source identification",
    2: "perceived affective quality",
    3: "assessment of the surrounding sound environment",
    4: "appropriateness of the surrounding sound environment",
}

#: The symbols of Table D.1 as mathematics, for the tick labels.
_TABLE_D1_SYMBOLS: dict[str, str] = {
    "LAeq,T": r"$L_{\mathrm{Aeq},T}$",
    "LCeq,T": r"$L_{\mathrm{Ceq},T}$",
    "LAF5,T": r"$L_{\mathrm{AF5},T}$",
    "LAF95,T": r"$L_{\mathrm{AF95},T}$",
    "N5": "$N_5$",
    "Naverage": r"$N_\mathrm{average}$",
    "Nrmc": r"$N_\mathrm{rmc}$",
    "N95": "$N_{95}$",
    "T": "$T$",
    "R10": "$R_{10}$",
    "R50": "$R_{50}$",
    "F10": "$F_{10}$",
    "F50": "$F_{50}$",
}

#: The axis label of each row of Table D.1, shorter than its parameter name.
_TABLE_D1_AXES: dict[str, str] = {
    "sound_pressure_level": "Level",
    "loudness": "Loudness",
    "sharpness": "Sharpness",
    "tonality": "Tonality",
    "roughness": "Roughness",
    "fluctuation_strength": "Fluctuation strength",
}

#: The Spanish of the soundscape renderers. The attributes are the words of
#: the English questionnaire of ISO/TS 12913-2 Figure C.4; the Spanish figure
#: renders them descriptively, not as a validated translation of the
#: questionnaire.
_SOUNDSCAPE_STRINGS_ES: dict[str, str] = {
    "PLEASANT": "AGRADABLE",
    "VIBRANT": "VIBRANTE",
    "EVENTFUL": "CON ACTIVIDAD",
    "CHAOTIC": "CAÓTICO",
    "ANNOYING": "MOLESTO",
    "MONOTONOUS": "MONÓTONO",
    "UNEVENTFUL": "SIN ACTIVIDAD",
    "CALM": "TRANQUILO",
    "pleasant": "agradable",
    "chaotic": "caótico",
    "vibrant": "vibrante",
    "uneventful": "sin actividad",
    "calm": "tranquilo",
    "annoying": "molesto",
    "eventful": "con actividad",
    "monotonous": "monótono",
    _METHOD_A_SUBJECTS[1]: "identificación de fuentes sonoras",
    _METHOD_A_SUBJECTS[2]: "calidad afectiva percibida",
    _METHOD_A_SUBJECTS[3]: "valoración del entorno sonoro circundante",
    _METHOD_A_SUBJECTS[4]: "adecuación del entorno sonoro circundante",
    "Traffic noise": "Ruido de tráfico",
    "Other noise": "Otros ruidos",
    "Sounds from human beings": "Sonidos de personas",
    "Natural sounds": "Sonidos naturales",
    "Noise": "Ruido",
    "loud": "ruidoso",
    "unpleasant": "desagradable",
    "appropriate": "adecuado",
    "visit again": "volver",
    "all": "todas",
    "Pleasantness $P$": "Agradabilidad $P$",
    "Eventfulness $E$": "Actividad $E$",
    r"Pleasantness $P/(4+\sqrt{32})$": r"Agradabilidad $P/(4+\sqrt{32})$",
    r"Eventfulness $E/(4+\sqrt{32})$": r"Actividad $E/(4+\sqrt{32})$",
    "ISO/TS 12913-3 Figure A.1: pleasantness and eventfulness": (
        "ISO/TS 12913-3 Figura A.1: agradabilidad y actividad"
    ),
    "Scale value (Table A.1)": "Valor de escala (Tabla A.1)",
    "Scale value (Table B.1)": "Valor de escala (Tabla B.1)",
    "median, range": "mediana, recorrido",
    "Method A, part": "Método A, parte",
    "Method B, part 1": "Método B, parte 1",
    "mean": "media",
    "{level} % confidence interval": "intervalo de confianza del {level} %",
    "Rank (1 = most noticeable)": "Rango (1 = la más perceptible)",
    "Method B, part 2: source ranking": "Método B, parte 2: orden de las fuentes",
    "Formula": "Fórmula",
    "rank of $x$": "rango de $x$",
    "rank of $y$": "rango de $y$",
    "left ear": "oído izquierdo",
    "right ear": "oído derecho",
    "representative (higher of the two ears)": "representativo (el mayor de los dos oídos)",
    "ISO/TS 12913-3 Table D.1": "ISO/TS 12913-3 Tabla D.1",
    "Sound pressure level": "Nivel de presión acústica",
    "Loudness (time-variant loudness)": "Sonoridad (variable en el tiempo)",
    "Psychoacoustic tonality": "Tonalidad psicoacústica",
    "Roughness": "Aspereza",
    "Level": "Nivel",
    "Loudness": "Sonoridad",
    "Sharpness": "Agudeza",
    "Tonality": "Tonalidad",
    "Fluctuation strength": "Intensidad de fluctuación",
}
_STRINGS.update(_SOUNDSCAPE_STRINGS_ES)


#: Where an attribute label stops sitting on its axis and goes beside it: the
#: cosine (or sine) of 60 degrees, so the diagonal labels sit off both axes.
_LABEL_SLANT = 0.5

#: The half-width and half-height of the Figure A.1 axes, in arrow lengths:
#: room past the tips for a label written across (a word, "AGRADABLE") and for
#: one written above or below (a line).
_FIGURE_A1_WIDTH = 2.0
_FIGURE_A1_HEIGHT = 1.55

#: The size, in inches, of a figure the Figure A.1 renderer creates itself.
_FIGURE_A1_SIZE_IN = (7.0, 7.0)

#: Line height of a label, as a multiple of its font size.
_LINE_HEIGHT = 1.25

#: Space kept between the axis label and a legend under it, in points.
_LEGEND_GAP_PT = 4.0


def _under_x_axis_pt() -> float:
    """Depth of the tick marks, tick labels and axis label under the axes,
    in points, from the current style.
    """
    import matplotlib as mpl
    from matplotlib.font_manager import FontProperties

    rc = mpl.rcParams

    def size(value: float | str) -> float:
        return float(FontProperties(size=value).get_size_in_points())

    tick = max(float(rc["xtick.major.size"]), 0.0) + float(rc["xtick.major.pad"])
    return (
        tick
        + _LINE_HEIGHT * size(rc["xtick.labelsize"])
        + float(rc["axes.labelpad"])
        + _LINE_HEIGHT * size(rc["axes.labelsize"])
        + _LEGEND_GAP_PT
    )


def _sign_of(value: float) -> float:
    """-1, 0 or 1 by the side of the label axis a value falls on."""
    if value > _LABEL_SLANT:
        return 1.0
    if value < -_LABEL_SLANT:
        return -1.0
    return 0.0


#: The four questions of Figure C.7, as an axis can hold them.
_METHOD_B_SHORT: dict[str, str] = {
    "How loud is it here?": "loud",
    "How unpleasant is it here?": "unpleasant",
    "How appropriate is the sound to the surrounding?": "appropriate",
    "How often would you like to visit this place again?": "visit again",
}


def _item_label(item: str, language: str) -> str:
    """An item as drawn: without the examples in brackets, translated."""
    short = _METHOD_B_SHORT.get(item, item.split(" (e.g.", 1)[0].strip())
    return _t(short, language)


def _site_label(site: str, language: str) -> str:
    """A site as drawn: the one unnamed site of a study is translated."""
    return _t(site, language) if site == "all" else site


def _first_or_fixed(
    kwargs: dict[str, Any], *, first: bool, **base: Any
) -> dict[str, Any]:
    """The caller's style for the first series, the renderer's for the rest."""
    return styled(kwargs, **base) if first else dict(base)


def plot_method_a_summary(
    result: MethodASummary,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Median and range of each Method A item per site (ISO/TS 12913-3 A.2).

    Each item is a column; each site a marker at the median with a vertical
    bar over the range, offset beside the other sites.

    :param result: A
        :class:`~phonometry.environment.assessment.soundscape.MethodASummary`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the median markers of the first site.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    items = np.arange(len(result.items), dtype=np.float64)
    n_sites = len(result.sites)
    width = 0.6 / max(n_sites, 1)
    for k, site in enumerate(result.sites):
        offset = (k - 0.5 * (n_sites - 1)) * width
        color = _SITE_COLORS[k % len(_SITE_COLORS)]
        x = items + offset
        ax.vlines(
            x,
            result.minima[k],
            result.maxima[k],
            color=theme_line(color, ax, quiet=0.55),
            lw=2.0,
        )
        style = _first_or_fixed(
            kwargs,
            first=k == 0,
            color=color,
            marker="o",
            ls="none",
            ms=7,
            label=_site_label(site, language),
        )
        ax.plot(x, result.medians[k], **style)
    tilted = len(result.items) > _FLAT_ITEM_LABELS
    ax.set_xticks(items)
    ax.set_xticklabels(
        [_item_label(item, language) for item in result.items],
        rotation=30 if tilted else 0,
        ha="right" if tilted else "center",
    )
    ax.set_xlim(-0.6, len(result.items) - 0.4)
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_ylabel(_t("Scale value (Table A.1)", language))
    # Two lines: the longest subject, part 4, runs past a default figure on
    # one line with the method and the statistics in front of it.
    subject = _t(_METHOD_A_SUBJECTS[result.part], language)
    ax.set_title(
        f"ISO/TS 12913-3, {_t('Method A, part', language)} {result.part} "
        f"({_t('median, range', language)})\n{subject[:1].upper()}{subject[1:]}"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    legend = ax.legend(fontsize="small")
    place_legend_clear(legend)
    localize_axes(ax, language)
    return ax


#: The loudness variability ratio of ISO/TS 12913-3 D.2, as the binaural
#: result keys it.
_N5_N95 = "N5/N95"


def _toward(value: float, positive: str, negative: str) -> str:
    """Where a label past an arrow tip anchors, away from the centre.

    :param value: The cosine (for the horizontal anchor) or sine (for the
        vertical one) of the arrow's angle.
    :param positive: The anchor when the arrow points that way clearly.
    :param negative: The anchor when it points the other way clearly.
    :return: ``positive``, ``negative`` or ``"center"`` for an arrow closer to
        the other axis.
    """
    if value > _LABEL_SLANT:
        return positive
    if value < -_LABEL_SLANT:
        return negative
    return "center"


def _draw_attribute_axes(ax: Axes, reach: float, language: str) -> None:
    """The eight attribute arrows of Figure A.1, named past their tips."""
    ink = theme_line(ax.xaxis.label.get_color(), ax, quiet=0.7)
    for label, angle, solid in _PAQ_AXES:
        rad = math.radians(angle)
        end = (reach * math.cos(rad), reach * math.sin(rad))
        ax.annotate(
            "",
            xy=end,
            xytext=(0.0, 0.0),
            arrowprops={
                "arrowstyle": "-|>",
                "color": ink,
                "lw": 1.0,
                "ls": "-" if solid else "--",
                "shrinkA": 0.0,
                "shrinkB": 0.0,
            },
        )
        cos, sin = math.cos(rad), math.sin(rad)
        ax.annotate(
            _t(label, language),
            end,
            xytext=(4.0 * _sign_of(cos), 4.0 * _sign_of(sin)),
            textcoords="offset points",
            ha=_toward(cos, "left", "right"),
            va=_toward(sin, "bottom", "top"),
            fontsize="small",
            color=ink,
        )


def _draw_respondents(ax: Axes, result: PleasantnessEventfulness, scale: float) -> None:
    """Every respondent, faintly, in the colour of their site."""
    respondent_sites = np.asarray(result.respondent_sites, dtype=object)
    for k, site in enumerate(result.sites):
        own = respondent_sites == site
        ax.plot(
            result.respondent_pleasantness[own] * scale,
            result.respondent_eventfulness[own] * scale,
            ".",
            color=theme_line(_SITE_COLORS[k % len(_SITE_COLORS)], ax, quiet=0.6),
            ms=3,
        )


def plot_pleasantness_eventfulness(
    result: PleasantnessEventfulness,
    ax: Axes | None = None,
    *,
    normalized: bool = True,
    respondents: bool = False,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The sites on the two-dimensional model of ISO/TS 12913-3 Figure A.1.

    Pleasantness on the horizontal axis, eventfulness on the vertical one,
    the four main attribute axes solid and the four rotated ones dashed, as
    the figure draws them, and each site a point of its own, named in a
    legend under the axes. The attribute names sit past the arrow tips, where
    no site can fall, since the coordinates end at the tips. A figure the
    renderer creates itself is square, with room for the legend, and laid out
    by the constrained layout so the legend stays on the canvas; on axes the
    caller passes, the caller lays the figure out (``plt.tight_layout()``).

    :param result: A
        :class:`~phonometry.environment.assessment.soundscape.PleasantnessEventfulness`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param normalized: Coordinates divided by :math:`4 + \sqrt{32}` (default)
        or raw.
    :param respondents: Also draw every respondent, faintly.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the site markers.
    :return: The axes.
    """
    from matplotlib.transforms import offset_copy

    from .._i18n import localize_axes
    from ..environment.assessment.soundscape import PLEASANTNESS_EVENTFULNESS_RANGE

    own_figure = None
    if ax is None:
        # Square, for the square model, and tall enough for a legend of a few
        # dozen sites under it; the layout engine keeps that legend on the
        # canvas for a plain savefig() or plt.show().
        own_figure = _import_pyplot().figure(
            figsize=_FIGURE_A1_SIZE_IN, layout="constrained"
        )
        ax = own_figure.add_subplot()
    scale = 1.0 / PLEASANTNESS_EVENTFULNESS_RANGE if normalized else 1.0
    reach = PLEASANTNESS_EVENTFULNESS_RANGE * scale
    _draw_attribute_axes(ax, reach, language)
    if respondents:
        _draw_respondents(ax, result, scale)
    # Each site a marker of its own, named in a legend under the axes: sites
    # of one study sit close together, and names written beside the points
    # would run into each other and across the attribute arrows.
    x = result.pleasantness * scale
    y = result.eventfulness * scale
    for k, (site, xs, ys) in enumerate(zip(result.sites, x, y, strict=True)):
        ax.plot(
            [float(xs)],
            [float(ys)],
            **styled(
                kwargs,
                color=_SITE_COLORS[k % len(_SITE_COLORS)],
                marker=_SITE_MARKERS[(k // len(_SITE_COLORS)) % len(_SITE_MARKERS)],
                ls="none",
                ms=8,
                label=_site_label(site, language),
            ),
        )
    # The legend hangs a fixed distance under the axes, the depth of the tick
    # labels and the axis label, in points: an offset in axes fractions would
    # move with the axes height, which the layout engine is still choosing,
    # and a tall legend of many sites would then be laid out off the canvas.
    placement: dict[str, Any] = {
        "loc": "upper center",
        "bbox_to_anchor": (0.5, 0.0),
        "bbox_transform": offset_copy(
            ax.transAxes,
            fig=cast("Figure", ax.get_figure(root=True)),
            y=-_under_x_axis_pt(),
            units="points",
        ),
    }
    legend = ax.legend(
        ncol=min(3, max(1, len(result.sites))),
        fontsize="small",
        frameon=False,
        **placement,
    )
    legend.set_in_layout(True)
    # The labels sit past the arrow tips, as in Figure A.1. Across the page
    # they need the room of a word ("AGRADABLE", "MONOTONOUS"), up and down
    # only that of a line, so the horizontal limits reach further.
    ax.set_xlim(-_FIGURE_A1_WIDTH * reach, _FIGURE_A1_WIDTH * reach)
    ax.set_ylim(-_FIGURE_A1_HEIGHT * reach, _FIGURE_A1_HEIGHT * reach)
    ax.set_aspect("equal")
    if normalized:
        ax.set_xlabel(_t(r"Pleasantness $P/(4+\sqrt{32})$", language))
        ax.set_ylabel(_t(r"Eventfulness $E/(4+\sqrt{32})$", language))
    else:
        ax.set_xlabel(_t("Pleasantness $P$", language))
        ax.set_ylabel(_t("Eventfulness $E$", language))
    ax.set_title(
        _t("ISO/TS 12913-3 Figure A.1: pleasantness and eventfulness", language)
    )
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    if own_figure is not None:
        # The constrained layout of an equal-aspect axes with a tall legend
        # under it settles on its second pass; the first, taken here, keeps
        # the caller's first savefig() or show() from drawing the unsettled
        # one, with the legend and the title past the canvas.
        own_figure.draw_without_rendering()
    return ax


def plot_soundscape_correlation(
    result: SoundscapeCorrelation,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The pairs of a correlation, as ranks for Spearman, with the coefficient.

    :param result: A
        :class:`~phonometry.environment.assessment.soundscape.SoundscapeCorrelation`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the markers.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    spearman = result.method == "spearman"
    if spearman and result.x_ranks is not None and result.y_ranks is not None:
        x, y = result.x_ranks, result.y_ranks
        ax.set_xlabel(_t("rank of $x$", language))
        ax.set_ylabel(_t("rank of $y$", language))
    else:
        x, y = result.x, result.y
        ax.set_xlabel("$x$")
        ax.set_ylabel("$y$")
    ax.plot(x, y, **styled(kwargs, color=_C_PRIMARY, marker="o", ls="none", ms=6))
    # The symbols of the page: r_spearman in Formulas (A.3) and (A.4), plain r
    # for Pearson's coefficient in B.3.
    symbol = r"$r_\mathrm{spearman}$" if spearman else "Pearson $r$"
    ax.set_title(
        f"{symbol} = {format_number(result.coefficient, language, decimals=3)}, "
        f"$p$ = {format_number(result.p_value, language, decimals=3)} "
        f"({_t('Formula', language)} {result.formula}, $n$ = {result.n})"
    )
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_method_b_summary(
    result: MethodBSummary,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Mean and confidence interval of each Method B scale per site.

    :param result: A
        :class:`~phonometry.environment.assessment.soundscape.MethodBSummary`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the mean markers of the first site.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    items = np.arange(len(result.items), dtype=np.float64)
    n_sites = len(result.sites)
    width = 0.6 / max(n_sites, 1)
    for k, site in enumerate(result.sites):
        offset = (k - 0.5 * (n_sites - 1)) * width
        color = _SITE_COLORS[k % len(_SITE_COLORS)]
        x = items + offset
        ax.vlines(
            x,
            result.confidence_lower[k],
            result.confidence_upper[k],
            color=theme_line(color, ax, quiet=0.55),
            lw=2.0,
        )
        style = _first_or_fixed(
            kwargs,
            first=k == 0,
            color=color,
            marker="s",
            ls="none",
            ms=7,
            label=_site_label(site, language),
        )
        ax.plot(x, result.means[k], **style)
    ax.set_xticks(items)
    ax.set_xticklabels([_item_label(item, language) for item in result.items])
    ax.set_xlim(-0.6, len(result.items) - 0.4)
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_ylabel(_t("Scale value (Table B.1)", language))
    level = format_number(100.0 * result.confidence_level, language, decimals=0)
    # The level goes where each language puts it: "95 % confidence interval",
    # "intervalo de confianza del 95 %".
    interval = _t("{level} % confidence interval", language).format(level=level)
    ax.set_title(
        f"ISO/TS 12913-3, {_t('Method B, part 1', language)}: {_t('mean', language)}, "
        f"{interval}"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    legend = ax.legend(fontsize="small")
    place_legend_clear(legend)
    localize_axes(ax, language)
    return ax


def plot_source_ranking(
    result: SourceRanking,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Median rank of each recognised sound source per site, with its range.

    :param result: A
        :class:`~phonometry.environment.assessment.soundscape.SourceRanking`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the bars of the first site.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    rows = np.arange(len(result.sources), dtype=np.float64)
    n_sites = len(result.sites)
    height = 0.8 / max(n_sites, 1)
    ink = theme_line(ax.xaxis.label.get_color(), ax, quiet=0.7)
    for k, site in enumerate(result.sites):
        offset = (k - 0.5 * (n_sites - 1)) * height
        medians = np.nan_to_num(result.median_ranks[k], nan=0.0)
        style = _first_or_fixed(
            kwargs,
            first=k == 0,
            color=_SITE_COLORS[k % len(_SITE_COLORS)],
            height=height,
            label=_site_label(site, language),
        )
        ax.barh(rows + offset, medians, **style)
        ax.hlines(
            rows + offset,
            np.nan_to_num(result.lowest_ranks[k], nan=0.0),
            np.nan_to_num(result.highest_ranks[k], nan=0.0),
            colors=[ink],
            lw=1.2,
        )
    ax.set_yticks(rows)
    ax.set_yticklabels(list(result.sources))
    ax.invert_yaxis()
    ax.set_xlim(0.0, 8.5)
    ax.set_xlabel(_t("Rank (1 = most noticeable)", language))
    ax.set_title(f"ISO/TS 12913-3, {_t('Method B, part 2: source ranking', language)}")
    ax.grid(visible=True, axis="x", alpha=0.3)
    legend = ax.legend(fontsize="small")
    place_legend_clear(legend)
    localize_axes(ax, language)
    return ax


def plot_binaural_indicators(
    result: BinauralIndicators,
    ax: Axes | None = None,
    *,
    parameter: str,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """One row of ISO/TS 12913-3 Table D.1 at both ears.

    Each metric of the row is a pair of bars, left and right ear, with the
    representative value of D.2, the higher of the two, marked across them.

    :param result: A
        :class:`~phonometry.environment.assessment.soundscape_binaural.BinauralIndicators`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param parameter: The row of Table D.1 to draw.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the left-ear bars.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes
    from ..environment.assessment.soundscape_binaural import BINAURAL_PARAMETERS

    ax = ax if ax is not None else _new_axes()
    row = BINAURAL_PARAMETERS[parameter]
    # The ratio N5/N95 has no unit and a scale of its own, so it is named in
    # the title rather than drawn beside four loudnesses in sone.
    metrics = [
        result.metrics[s] for s in row.metrics if s in result.metrics and s != _N5_N95
    ]
    x = np.arange(len(metrics), dtype=np.float64)
    left = np.asarray([m.left for m in metrics])
    right = np.asarray([m.right for m in metrics])
    width = 0.38
    ax.bar(
        x - 0.5 * width,
        left,
        **styled(kwargs, color=_C_PRIMARY, width=width, label=_t("left ear", language)),
    )
    ax.bar(
        x + 0.5 * width,
        right,
        color=_C_SECONDARY,
        width=width,
        label=_t("right ear", language),
    )
    ink = theme_line(ax.xaxis.label.get_color(), ax, quiet=0.85)
    ax.hlines(
        [m.representative for m in metrics],
        x - width,
        x + width,
        colors=[ink],
        lw=2.0,
        label=_t("representative (higher of the two ears)", language),
    )
    ax.set_xticks(x)
    ax.set_xticklabels([_TABLE_D1_SYMBOLS.get(m.symbol, m.symbol) for m in metrics])
    unit = metrics[0].unit if metrics else ""
    ax.set_ylabel(f"{_t(_TABLE_D1_AXES[parameter], language)} [{unit}]")
    if parameter == "sound_pressure_level" and metrics:
        low = float(min(left.min(), right.min()))
        ax.set_ylim(max(0.0, 10.0 * math.floor(low / 10.0) - 10.0), None)
    title = f"{_t('ISO/TS 12913-3 Table D.1', language)}: {_t(row.parameter, language)}"
    if _N5_N95 in result.metrics and parameter == "loudness":
        ratio = result.metrics[_N5_N95]
        title += (
            f"\n$N_5/N_{{95}}$ = {format_number(ratio.left, language, decimals=2)} "
            f"({_t('left ear', language)}), "
            f"{format_number(ratio.right, language, decimals=2)} "
            f"({_t('right ear', language)})"
        )
    ax.set_title(title)
    # Horizontal rules only: a vertical one would run through the middle of
    # every pair of bars, where the tick of each metric sits.
    ax.grid(visible=False, axis="x")
    ax.grid(visible=True, axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    legend = ax.legend(fontsize="small")
    place_legend_clear(legend)
    localize_axes(ax, language)
    return ax
