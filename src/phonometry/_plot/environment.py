#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the environmental domain (lazy imports from result .plot())."""

from __future__ import annotations

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
    _new_axes,
    _plot_two_runs,
    format_frequency_axis,
    place_legend_clear,
    style_default,
    styled,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..environment.assessment.impulsive_sound import ImpulseProminenceResult
    from ..environment.assessment.measurement import TonalAssessmentResult
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
    "Pass-bys": "Pasadas",
    "Regression line": "Recta de regresión",
    "Window of clause 9.3 for the reference speed": (
        "Ventana del apartado 9.3 para la velocidad de referencia"
    ),
    "ISO 11819-1 regression": "Regresión ISO 11819-1",
    "ISO 11819-1 statistical pass-by": "Paso estadístico ISO 11819-1",
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
        color=_C_PRIMARY_LIGHT,
        alpha=0.25,
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
            f"{format_number(result.vehicle_sound_level_db, language)} dB, "
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
            f"{format_number(regression.vehicle_sound_level_db, language)} dB",
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
        f"{format_number(result.index_db, language)} dB"
    )
    ax.grid(visible=True, which="major", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax
