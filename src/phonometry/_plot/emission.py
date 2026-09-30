#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the emission domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

import numpy as np

from .common import (
    _C_EDGE,
    _C_MUTED,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _band_axis,
    _bar_width,
    _format_freq,
    _freq_axis,
    _hatch_invalid,
    _new_axes,
    _plot_band_level_bars,
    _sound_power_designation,
    format_frequency_axis,
    place_legend_clear,
    style_default,
    theme_fill,
    theme_line,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.axes import Axes
    from matplotlib.container import BarContainer
    from matplotlib.patches import Rectangle

    from ..emission.intensity import FieldIndicators, IntensityResult
    from ..emission.intensity_compliance import (
        IntensityInstrumentComplianceResult,
    )
    from ..emission.sound_power import SoundEnergyResult, SoundPowerResult
    from ..emission.sound_power_anechoic import PrecisionSoundPowerResult
    from ..emission.sound_power_hard_walled import (
        HardWalledRoomCheck,
        HardWalledSoundPowerResult,
        SourceLocationPlan,
    )
    from ..emission.sound_power_high_frequency import HighFrequencySoundPowerResult
    from ..emission.sound_power_in_duct import InDuctSoundPowerResult
    from ..emission.sound_power_in_situ import InSituSoundPowerResult
    from ..emission.sound_power_intensity import (
        PrecisionIntensityResult,
        SoundPowerIntensityResult,
    )
    from ..emission.sound_power_intensity_points import (
        DiscretePointIntensityResult,
    )
    from ..emission.sound_power_reverberation import (
        ReverberationSoundEnergyResult,
        ReverberationSoundPowerResult,
    )
    from ..emission.sound_power_special_room import (
        SpecialRoomReverberationCheck,
        SpecialRoomSoundPowerResult,
        SpecialRoomSuitabilityCheck,
        SpecialRoomSurfaceCheck,
    )
    from ..emission.turbine_noise import (
        TurbineMeasurementSurface,
        TurbineMicrophoneArray,
        TurbineNoiseDeclaration,
        TurbineSoundPowerResult,
    )
    from ..emission.vibration_sound_power import VibrationSoundPowerResult
    from ..emission.workstation import EmissionPressureResult

#: Shared frequency-axis label of the spectral renderers.
_FREQ_LABEL = "Frequency [Hz]"
#: Y-axis label of the residual-index plots (identical in both languages,
#: the symbol carries the meaning).
_LABEL_RESIDUAL_INDEX = r"$\delta_{pI0}$ [dB]"
#: Fewest frequency bands that make a per-band ISO 9614-1 indicators result
#: drawable as a curve: a size-1 array after ``atleast_1d`` is the
#: scalar/overall form of ``field_indicators`` (1D per-position input), which
#: ``plot()`` rejects as carrying no per-band data.
_MIN_BANDS = 2

#: Axis labels drawn by more than one renderer here. They are named rather
#: than repeated because the English text is also the key into ``_STRINGS``,
#: so a typo in one copy would silently fall back to English for that plot
#: alone, which is the kind of defect a reader sees and a test does not.
_YLABEL_LW = "Sound power level $L_W$ [dB]"
_YLABEL_LW_ABSOLUTE = r"Sound power level $L_W$ [dB re 1 pW]"
_YLABEL_LJ = "Sound energy level $L_J$ [dB]"

#: Spanish translations of the fixed labels/titles/legends rendered by the
#: emission-domain ``.plot()`` renderers, keyed by their verbatim English
#: text. ``_t`` returns the English key unchanged for any language other
#: than ``"es"``, so the English output is byte-for-byte identical to the
#: pre-i18n renderers.
#: Labels the high-frequency sound power plots share, named once so the
#: translation table and the axes cannot drift apart.
_LEVEL_LABEL = "Level [dB]"
_SOUND_POWER_LABEL = "Sound power $L_W$"
_MEAN_ROOM_LEVEL_LABEL = r"Mean room level $\overline{L_p}$"

#: Axis labels of the ISO 3743 renderers, named for the same reason.
_SPREAD_LABEL = "Spread between orientations [dB]"
_SM_LABEL = r"Standard deviation $s_\mathrm{M}$ [dB]"
_T_NOMINAL_LABEL = r"$T/T_\mathrm{nom}$"
_ALPHA_LABEL = r"Absorption coefficient $\alpha$"
_DIFFERENCE_LABEL = "Power level difference [dB]"
#: Words and symbols of the ISO 3743 renderers written more than once.
_DIRECT_METHOD = "direct method"
_NOT_QUALIFIED = "not qualified"
_LWA_SYMBOL = "$L_{W\\mathrm{A}}$"
#: Legend corner of the ISO 3743 renderers whose curves leave it free.
_LEGEND_LOWER_RIGHT: Final = "lower right"
#: Text coordinates of an annotation placed a few points from its anchor.
_OFFSET_POINTS: Final = "offset points"
#: Title of the IEC 61063 position plot, the same in both languages.
_IEC_61063_TITLE = r"IEC 61063: $L_{{W\mathrm{{A}}}}$ = {power} dB re 1 pW"
#: Legend of a band the standard makes an upper bound: the source under test's
#: own background margin fell short (ISO 3743-1 8.1.3, ISO 3747 8.1).
_UPPER_BOUND_LABEL = "Upper bound: source margin below 6 dB"
#: Axis of a survey plot that adds the A-weighted row as a bar of its own.
_A_BAND_LABEL = "Frequency [Hz]; A: A-weighted level"

_STRINGS: dict[str, str] = {
    "Band": "Banda",
    _YLABEL_LW: "Nivel de potencia acústica $L_W$ [dB]",
    _YLABEL_LJ: "Nivel de energía acústica $L_J$ [dB]",
    "sound power spectrum": "espectro de potencia acústica",
    "sound energy spectrum": "espectro de energía acústica",
    "In situ sound power spectrum (ISO 3747)": "Espectro de potencia acústica in situ (ISO 3747)",
    "In situ sound energy spectrum (ISO 3747)": "Espectro de energía acústica in situ (ISO 3747)",
    _UPPER_BOUND_LABEL: "Cota superior: margen de la fuente inferior a 6 dB",
    "Background requirement (8.1) not shown to be met": "Requisito de ruido de fondo (apartado 8.1) no demostrado",
    "Background requirement (4.5) not shown to be met": "Requisito de ruido de fondo (apartado 4.5) no demostrado",
    "Background requirement (9.8) not shown to be met": "Requisito de ruido de fondo (apartado 9.8) no demostrado",
    "Non-positive band": "Banda no positiva",
    "Pressure level $L_p$": "Nivel de presión $L_p$",
    "Intensity level $L_I$": "Nivel de intensidad $L_I$",
    _LEVEL_LABEL: "Nivel [dB]",
    r"Pressure-intensity index $\delta_{pI}$ [dB]": r"Índice presión-intensidad $\delta_{pI}$ [dB]",
    _YLABEL_LW_ABSOLUTE: "Nivel de potencia acústica $L_W$ [dB re 1 pW]",
    "ISO/TS 7849 sound power from surface vibration": "Potencia acústica por vibración superficial ISO/TS 7849",
    "$F_2$ (surface pressure-intensity)": "$F_2$ (presión-intensidad superficial)",
    "$F_3$ (negative partial power)": "$F_3$ (potencia parcial negativa)",
    r"Dynamic capability $L_\mathrm{d}$": r"Capacidad dinámica $L_\mathrm{d}$",
    "$F_4$ (non-uniformity)": "$F_4$ (no uniformidad)",
    "$F_1$ (temporal variability)": "$F_1$ (variabilidad temporal)",
    "$F_1$ limit (Table B.3)": "Límite de $F_1$ (tabla B.3)",
    "Indicator [dB]": "Indicador [dB]",
    "Field non-uniformity $F_4$": "No uniformidad del campo $F_4$",
    "Dimensionless indicators $F_1$, $F_4$": "Indicadores adimensionales $F_1$, $F_4$",
    "ISO 9614-1 field indicators": "Indicadores de campo ISO 9614-1",
    "Class {cls} pass region": "Región de aceptación clase {cls}",
    "Class 1 minimum": "Mínimo clase 1",
    "Class 2 minimum": "Mínimo clase 2",
    r"Measured $\delta_{pI0}$": r"$\delta_{pI0}$ medido",
    "Below the class {cls} minimum": "Bajo el mínimo de clase {cls}",
    _LABEL_RESIDUAL_INDEX: _LABEL_RESIDUAL_INDEX,
    "IEC 61043 Table 2: {device}, {spacing} mm separation": "Tabla 2 de IEC 61043: {device}, separación de {spacing} mm",
    "probe": "sonda",
    "processor": "procesador",
    "complete instrument": "instrumento completo",
    "Frequency [Hz]": "Frecuencia [Hz]",
    "Measured $L'_p$": "$L'_p$ medido",
    "Background $K_1$": "Fondo $K_1$",
    "Room $K_3$": "Sala $K_3$",
    "Emission $L_p$": "$L_p$ de emisión",
    "Sound pressure level [dB]": "Nivel de presión sonora [dB]",
    "Emission sound pressure level at the work station ({std})": "Nivel de presión sonora de emisión en el puesto de trabajo ({std})",
    "upper bound: the background is too close": "cota superior: el fondo está demasiado cerca",
    "grade 2 (engineering)": "grado 2 (ingeniería)",
    "grade 3 (survey)": "grado 3 (control)",
    _SOUND_POWER_LABEL: "Potencia acústica $L_W$",
    _MEAN_ROOM_LEVEL_LABEL: r"Nivel medio en la sala $\overline{L_p}$",
    "Frequency [kHz]": "Frecuencia [kHz]",
    "Tone below the reporting range": "Tono fuera del intervalo a informar",
    "10 dB below the highest tone": "10 dB bajo el tono más alto",
    "ISO 9295 sound power in the 16 kHz octave, {method}": "Potencia acústica ISO 9295 en la octava de 16 kHz, {method}",
    "ISO 9295 tonal sound power, {method}": "Potencia acústica tonal ISO 9295, {method}",
    _DIRECT_METHOD: "método directo",
    "reference source": "fuente de referencia",
    "comparison method": "método de comparación",
    "Expanded uncertainty $U$": "Incertidumbre expandida $U$",
    _SPREAD_LABEL: "Dispersión entre orientaciones [dB]",
    "Largest spread between orientations": "Mayor dispersión entre orientaciones",
    r"Table 3 limit $\sigma_{R0}$": r"Límite de la tabla 3 $\sigma_{R0}$",
    "Spread above the limit": "Dispersión por encima del límite",
    "ISO 3743-1 room qualification: {verdict}": "Cualificación de la sala ISO 3743-1: {verdict}",
    "qualified": "cualificada",
    _NOT_QUALIFIED: "no cualificada",
    _SM_LABEL: r"Desviación típica $s_\mathrm{M}$ [dB]",
    "Survey standard deviation": "Desviación típica del sondeo",
    "{standard} source locations, {mics} microphone positions": "{standard}: ubicaciones de la fuente, {mics} posiciones de micrófono",
    "Table 2: one location up to 2.5 dB": "Tabla 2: una ubicación hasta 2,5 dB",
    "N over a bar: source locations (Table 2)": "N sobre una barra: ubicaciones de la fuente (Tabla 2)",
    "N over a bar: source locations (Table 3)": "N sobre una barra: ubicaciones de la fuente (Tabla 3)",
    _A_BAND_LABEL: "Frecuencia [Hz]; A: nivel ponderado A",
    "Table 2: two locations up to 4.0 dB": "Tabla 2: dos ubicaciones hasta 4,0 dB",
    "N+2: two more locations in another room": "N+2: dos ubicaciones más en otra sala",
    "Table 3: 2.3 dB, narrow-band components (9.5)": "Tabla 3: 2,3 dB, componentes de banda estrecha (apartado 9.5)",
    "Table 3: 4 dB, discrete tone (9.5)": "Tabla 3: 4 dB, tono discreto (apartado 9.5)",
    _T_NOMINAL_LABEL: r"$T/T_\mathrm{nom}$",
    r"Measured $T/T_\mathrm{nom}$": r"$T/T_\mathrm{nom}$ medido",
    "Ideal ratio $R$": "Relación ideal $R$",
    "Limiting curves": "Curvas límite",
    "Outside the limiting curves": "Fuera de las curvas límite",
    r"ISO 3743-2 reverberation time, $T_\mathrm{{nom}}$ = {tnom} s: {verdict}": r"Tiempo de reverberación ISO 3743-2, $T_\mathrm{{nom}}$ = {tnom} s: {verdict}",
    _ALPHA_LABEL: r"Coeficiente de absorción $\alpha$",
    "Wall or ceiling {n}": "Pared o techo {n}",
    "0.5 to 1.5 times the mean": "0,5 a 1,5 veces la media",
    "Floor": "Suelo",
    "Floor limit 0.06": "Límite del suelo 0,06",
    "ISO 3743-2 surface treatment (6.4): {verdict}": "Tratamiento de superficies ISO 3743-2 (apartado 6.4): {verdict}",
    "complies": "cumple",
    "does not comply": "no cumple",
    "Outside 6.4": "Fuera del apartado 6.4",
    _DIFFERENCE_LABEL: "Diferencia de nivel de potencia [dB]",
    "Table 1 limits": "Límites de la tabla 1",
    "Beyond Table 1": "Fuera de la tabla 1",
    "ISO 3743-2 room suitability (6.7): {verdict}": "Idoneidad de la sala ISO 3743-2 (apartado 6.7): {verdict}",
    "suitable": "idónea",
    "not suitable": "no idónea",
    "Measurement surface": "Superficie de medición",
    "Additional positions": "Posiciones adicionales",
    "Overhead positions": "Posiciones superiores",
    "Key positions": "Posiciones clave",
    "Along the shaft $x$ [m]": "A lo largo del eje $x$ [m]",
    "Across the shaft $y$ [m]": "Transversal al eje $y$ [m]",
    "Height $z$ [m]": "Altura $z$ [m]",
    "IEC 61063 plan, $S$ = {area} m²": "Planta IEC 61063, $S$ = {area} m²",
    "IEC 61063 elevation, $S$ = {area} m²": "Alzado IEC 61063, $S$ = {area} m²",
    "7 dB limit (A.3.3)": "Límite de 7 dB (A.3.3)",
    "This room, $K$ = {k} dB": "Esta sala, $K$ = {k} dB",
    "Reference source, $K$ = {k} dB": "Fuente de referencia, $K$ = {k} dB",
    "Environmental correction $K$ [dB]": "Corrección ambiental $K$ [dB]",
    "IEC 61063 Figure A.3": "Figura A.3 de IEC 61063",
    "qualifies": "apta",
    "does not qualify": "no apta",
    r"Corrected level $L_{p\mathrm{A}i}$": r"Nivel corregido $L_{p\mathrm{A}i}$",
    "Background": "Ruido de fondo",
    "Energy average": "Promedio energético",
    "Surface level {level} dB": "Nivel en la superficie {level} dB",
    "Overhead position": "Posición superior",
    "Upper limit: background within 3 dB": "Límite superior (fondo < 3 dB)",
    "Microphone position (key positions numbered)": "Posición de micrófono (posiciones clave numeradas)",
    "Microphone position, in the order given": "Posición de micrófono, en el orden dado",
    "A-weighted sound pressure level [dB]": "Nivel de presión sonora ponderado A [dB]",
    _IEC_61063_TITLE: _IEC_61063_TITLE,
    "Table 1: ±{sigma} dB": "Tabla 1: ±{sigma} dB",
    "A-weighted sound power level [dB re 1 pW]": "Nivel de potencia acústica ponderado A [dB re 1 pW]",
    "IEC 61063 report: loudest at {condition}": "Informe IEC 61063: condición más ruidosa, {condition}",
}


def _t(text: str, language: str = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


def plot_emission_pressure(
    result: EmissionPressureResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The reading, the two corrections taken off it, and what is left.

    A waterfall, because that is the shape of the arithmetic: ISO 11201/11202/
    11204 all print :math:`L_p = L'_p - K_1 - K_3`, and a reader wants to see
    which of the two corrections did the work. The measured bar and the
    emission bar stand on the axis; the two correction bars float between them,
    each starting where the previous one ended.

    A determination whose background margin fell below the grade's minimum is
    hatched, since the level drawn is an upper bound and the figure has to say
    so as plainly as the report does.

    :param result: An
        :class:`~phonometry.emission.workstation.EmissionPressureResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    :raises ValueError: If the result carries per-band arrays rather than the
        single overall level this figure draws.
    """
    from matplotlib.patches import Patch

    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    values = [
        float(np.asarray(result.measured_level_db).reshape(-1)[0]),
        float(np.asarray(result.background_correction_db).reshape(-1)[0]),
        float(np.asarray(result.local_correction_db).reshape(-1)[0]),
        float(np.asarray(result.level_db).reshape(-1)[0]),
    ]
    if np.asarray(result.level_db).size != 1:
        msg = (
            "plot_emission_pressure draws one determination; this result holds "
            f"{np.asarray(result.level_db).size} bands. Pass a single level."
        )
        raise ValueError(msg)

    measured, k1, k3, level = values
    # The two corrections hang from where the previous step left off, so the
    # bars read as one subtraction rather than as four unrelated numbers.
    after_k1 = measured - k1
    bottoms = [0.0, after_k1, level, 0.0]
    heights = [measured, k1, k3, level]
    colours = [_C_PRIMARY, _C_SECONDARY, _C_TERTIARY, _C_PRIMARY]
    labels = [
        _t("Measured $L'_p$", language),
        _t("Background $K_1$", language),
        _t("Room $K_3$", language),
        _t("Emission $L_p$", language),
    ]
    # The three names this figure positions itself are refused rather than
    # silently overridden, because a bar chart whose bottoms come from the
    # caller is not this figure any more. Everything the caller may reasonably
    # want, colour included, goes through setdefault so a kwarg wins.
    fixed = {"x", "height", "bottom"} & set(kwargs)
    if fixed:
        msg = (
            f"plot_emission_pressure positions its own bars; "
            f"{', '.join(sorted(fixed))} cannot be overridden."
        )
        raise TypeError(msg)
    kwargs.setdefault("width", 0.62)
    style_default(kwargs, "color", colours)
    kwargs.setdefault("edgecolor", _C_EDGE)
    bars = ax.bar(range(len(heights)), heights, bottom=bottoms, **kwargs)
    if result.upper_bound:
        _hatch_invalid(bars, np.array([True, False, False, True]))

    for index, (bar, value) in enumerate(zip(bars, heights, strict=True)):
        # A correction is written with its sign, because the figure is about
        # what came off; a level is written as the level it is.
        shown = (
            f"-{format_number(value, language, decimals=1)}"
            if index in (1, 2)
            else format_number(value, language, decimals=1)
        )
        ax.annotate(
            shown,
            xy=(bar.get_x() + bar.get_width() / 2.0, bar.get_y() + bar.get_height()),
            xytext=(0, 4),
            textcoords=_OFFSET_POINTS,
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_ylabel(_t("Sound pressure level [dB]", language))
    ax.set_title(
        _t(
            "Emission sound pressure level at the work station ({std})",
            language,
            std=result.standard,
        )
    )
    grade = _t(
        "grade 2 (engineering)"
        if result.grade == "engineering"
        else "grade 3 (survey)",
        language,
    )
    handles: list[Any] = [Patch(facecolor=_C_MUTED, edgecolor=_C_EDGE, label=grade)]
    if result.upper_bound:
        handles.append(
            Patch(
                facecolor=_C_PRIMARY,
                edgecolor=_C_EDGE,
                hatch="///",
                label=_t("upper bound: the background is too close", language),
            )
        )
    ax.legend(handles=handles, loc="upper right", fontsize=8)
    localize_axes(ax, language)
    return ax


def plot_sound_power(
    result: (
        SoundPowerResult
        | PrecisionSoundPowerResult
        | ReverberationSoundPowerResult
        | SoundPowerIntensityResult
        | PrecisionIntensityResult
        | DiscretePointIntensityResult
        | InDuctSoundPowerResult
    ),
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Sound power level spectrum with the A-weighted total annotated.

    Works for :class:`~phonometry.emission.sound_power.SoundPowerResult`,
    :class:`~phonometry.emission.sound_power_anechoic.PrecisionSoundPowerResult`,
    :class:`~phonometry.emission.sound_power_reverberation.ReverberationSoundPowerResult`,
    the two intensity-scanning results,
    :class:`~phonometry.emission.sound_power_intensity.SoundPowerIntensityResult`
    and
    :class:`~phonometry.emission.sound_power_intensity.PrecisionIntensityResult`,
    the discrete-point one,
    :class:`~phonometry.emission.sound_power_intensity_points.DiscretePointIntensityResult`,
    and the in-duct one,
    :class:`~phonometry.emission.sound_power_in_duct.InDuctSoundPowerResult`;
    for the three intensity variants the bands where the net power is
    non-positive (``negative_band`` / ``not_applicable_band``) are hatched and
    greyed as unusable.

    :param result: One of the seven sound-power results named above.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the band :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    lw = np.asarray(result.sound_power_level, dtype=np.float64)
    n = lw.size
    freqs = getattr(result, "frequencies", None)
    if freqs is None:
        positions = _band_axis(
            ax,
            [f"{_t('Band', language)} {i + 1}" for i in range(n)],
            xlabel=_t("Band", language),
            language=language,
        )
    else:
        positions = _band_axis(
            ax, np.asarray(freqs, dtype=np.float64), language=language
        )

    # ``negative_band`` (ISO 9614-2) and ``not_applicable_band`` (ISO 9614-3)
    # both flag bands whose net power is non-positive and therefore unusable.
    negative = getattr(result, "negative_band", None)
    if negative is None:
        negative = getattr(result, "not_applicable_band", None)
    neg = (
        np.asarray(negative, dtype=bool)
        if negative is not None
        else np.zeros(n, dtype=bool)
    )
    colors = [_C_MUTED if b else _C_PRIMARY for b in neg]
    style_default(kwargs, "color", colors)
    bars = ax.bar(positions, np.nan_to_num(lw), **kwargs)
    _hatch_invalid(bars, neg)

    ax.set_ylabel(_t(_YLABEL_LW, language))
    designation = _sound_power_designation(result)
    lwa = float(result.sound_power_level_a)
    if np.isfinite(lwa):
        ax.set_title(
            f"{designation} {_t('sound power spectrum', language)}  "
            "($L_{{W\\mathrm{{A}}}}$ = "
            f"{format_number(lwa, language, decimals=1)} dB(A))"
        )
    else:
        ax.set_title(f"{designation} {_t('sound power spectrum', language)}")
    if np.any(neg):
        ax.plot(
            [],
            [],
            color=_C_MUTED,
            marker="s",
            ls="",
            label=_t("Non-positive band", language),
        )
    if np.any(neg) or "label" in kwargs:
        ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_sound_energy(
    result: SoundEnergyResult | ReverberationSoundEnergyResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""Sound energy level spectrum with the A-weighted total annotated.

    The sound energy counterpart of :func:`plot_sound_power`, for the two
    single-event determinations,
    :class:`~phonometry.emission.sound_power.SoundEnergyResult` (ISO 3744
    clause 8.3 / ISO 3746 clause 8.4) and
    :class:`~phonometry.emission.sound_power_reverberation.ReverberationSoundEnergyResult`
    (ISO 3741 clause 9.2): one bar per band of :math:`L_J`, the standard the
    result came from in the title and :math:`L_{J\mathrm{A}}` beside it when
    the band centres were supplied. Neither determination flags an
    undeterminable band, so nothing is hatched.

    :param result: One of the two sound-energy results named above.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the band :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    lj = np.asarray(result.sound_energy_level, dtype=np.float64)
    freqs = result.frequencies
    if freqs is None:
        positions = _band_axis(
            ax,
            [f"{_t('Band', language)} {i + 1}" for i in range(lj.size)],
            xlabel=_t("Band", language),
            language=language,
        )
    else:
        positions = _band_axis(
            ax, np.asarray(freqs, dtype=np.float64), language=language
        )
    style_default(kwargs, "color", _C_PRIMARY)
    ax.bar(positions, lj, **kwargs)

    ax.set_ylabel(_t("Sound energy level $L_J$ [dB]", language))
    designation = _sound_power_designation(result)
    lja = float(result.sound_energy_level_a)
    title = f"{designation} {_t('sound energy spectrum', language)}"
    if np.isfinite(lja):
        title += (
            "  ($L_{J\\mathrm{A}}$ = "
            f"{format_number(lja, language, decimals=1)} dB(A))"
        )
    ax.set_title(title)
    if "label" in kwargs:
        ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_in_situ_sound_power(
    result: InSituSoundPowerResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """In situ sound power (or energy) spectrum with the A-weighted total.

    One bar per octave band of ``LW``, or of ``LJ`` when the result is an
    energy determination. A band where the source under test's background
    margin fell below the 6 dB of ISO 3747:2010 clause 8.1 is hatched as the
    upper bound that clause makes it; a band that fails 8.1 otherwise (the
    reference source's margin, or no background measured) is cross-hatched,
    since its level is no bound either way. The report has to say both.

    :param result: An
        :class:`~phonometry.emission.sound_power_in_situ.InSituSoundPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the band :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    energy = result.quantity == "energy"
    levels = np.asarray(
        result.sound_energy_level if energy else result.sound_power_level,
        dtype=np.float64,
    )
    total = float(result.sound_energy_level_a if energy else result.sound_power_level_a)
    positions = _band_axis(
        ax, np.asarray(result.frequencies, dtype=np.float64), language=language
    )
    style_default(kwargs, "color", _C_PRIMARY)
    bars = ax.bar(positions, np.nan_to_num(levels), **kwargs)
    handles = _mark_background(
        bars,
        not_met=~np.asarray(result.background_requirement_met, dtype=bool),
        upper=np.asarray(result.upper_bound, dtype=bool),
        labels=(
            _t(_UPPER_BOUND_LABEL, language),
            _t("Background requirement (8.1) not shown to be met", language),
        ),
    )

    if energy:
        ax.set_ylabel(_t(_YLABEL_LJ, language))
        title = _t("In situ sound energy spectrum (ISO 3747)", language)
        symbol = "$L_{J\\mathrm{A}}$"
    else:
        ax.set_ylabel(_t(_YLABEL_LW, language))
        title = _t("In situ sound power spectrum (ISO 3747)", language)
        symbol = _LWA_SYMBOL
    if np.isfinite(total):
        title += f"  ({symbol} = {format_number(total, language, decimals=1)} dB(A))"
    ax.set_title(title)
    if handles or "label" in kwargs:
        ax.legend(handles=handles or None, loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_high_frequency_sound_power(
    result: HighFrequencySoundPowerResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""ISO 9295 band levels, with the mean room level they came from.

    Broadband noise is one bar of :math:`L_W` per one-third octave band, with
    :math:`\overline{L_p}` beside it, so that the gap between the two reads
    as the room term of Formula (6) plus :math:`C_1` and :math:`C_2` (or the
    reference-source term of Formula (8) plus :math:`C_2`).
    A tonal determination is one stem per tone on a frequency axis in
    kilohertz, with the line 10 dB below the highest tone: clause 13 c)
    reports every tone above it, and the tones below it are drawn muted.

    :param result: A
        :class:`~phonometry.emission.sound_power_high_frequency.HighFrequencySoundPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the :math:`L_W` bars (broadband) or stem
        markers (tonal).
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    levels = np.asarray(result.sound_power_level, dtype=np.float64)
    mean = np.asarray(result.mean_pressure_level, dtype=np.float64)
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    method = _t(
        _DIRECT_METHOD if result.method == "direct" else "reference source",
        language,
    )
    if result.tonal:
        khz = freqs / 1000.0
        reported = np.asarray(result.within_10_db_of_maximum, dtype=bool)
        floor = float(np.min(np.concatenate([levels, mean]))) - 10.0
        colours = [_C_PRIMARY if keep else _C_MUTED for keep in reported]
        ax.vlines(khz, floor, levels, colors=colours, linewidth=2.0)
        style_default(kwargs, "color", colours)
        kwargs.setdefault("zorder", 3)
        kwargs.setdefault("label", _t(_SOUND_POWER_LABEL, language))
        ax.scatter(khz, levels, **kwargs)
        ax.scatter(
            khz,
            mean,
            marker="_",
            s=160,
            color=_C_SECONDARY,
            zorder=3,
            label=_t(_MEAN_ROOM_LEVEL_LABEL, language),
        )
        threshold = float(np.max(levels)) - 10.0
        ax.axhline(
            threshold,
            color=_C_REFERENCE,
            linestyle="--",
            linewidth=1.0,
            label=_t("10 dB below the highest tone", language),
        )
        if not np.all(reported):
            ax.scatter(
                [],
                [],
                color=_C_MUTED,
                label=_t("Tone below the reporting range", language),
            )
        ax.set_ylim(bottom=floor)
        span = max(float(np.ptp(khz)), 1.0)
        ax.set_xlim(float(np.min(khz)) - 0.1 * span, float(np.max(khz)) + 0.1 * span)
        ax.set_xlabel(_t("Frequency [kHz]", language))
        ax.set_title(
            _t("ISO 9295 tonal sound power, {method}", language, method=method)
        )
    else:
        positions = _band_axis(ax, freqs, language=language)
        style_default(kwargs, "color", _C_PRIMARY)
        kwargs.setdefault("label", _t(_SOUND_POWER_LABEL, language))
        kwargs.setdefault("width", 0.6)
        ax.bar(positions, levels, **kwargs)
        ax.plot(
            positions,
            mean,
            marker="o",
            linestyle="",
            color=_C_SECONDARY,
            label=_t(_MEAN_ROOM_LEVEL_LABEL, language),
        )
        low = float(np.min(np.concatenate([levels, mean])))
        ax.set_ylim(bottom=low - 10.0)
        ax.set_title(
            _t(
                "ISO 9295 sound power in the 16 kHz octave, {method}",
                language,
                method=method,
            )
        )
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_intensity(
    result: IntensityResult, ax: Axes | None = None, language: str = "en", **kwargs: Any
) -> Axes:
    """Pressure vs intensity level per band with the pressure-intensity index.

    Draws Lp and LI per band and, on a twin axis, the per-band
    pressure-intensity index ``Lp - LI`` (the reactivity indicator); the
    total index is annotated in the title.

    :param result: An :class:`~phonometry.emission.intensity.IntensityResult` with
        per-band data (obtained by requesting a band ``fraction``).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the pressure-level curve ``plot`` call.
    :return: The axes.
    :raises ValueError: If the result carries no per-band data.
    """
    from .._i18n import format_number, localize_axes

    if result.frequencies is None:
        msg = (
            "plot() needs per-band intensity data; call sound_intensity(...) "
            "with a 'fraction' to obtain it."
        )
        raise ValueError(msg)
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    lp = np.asarray(result.pressure_level, dtype=np.float64)
    li = np.asarray(result.intensity_level, dtype=np.float64)
    index = np.asarray(result.pressure_intensity_index, dtype=np.float64)

    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Pressure level $L_p$", language))
    ax.plot(freqs, lp, "o-", **kwargs)
    ax.plot(
        freqs,
        li,
        "s--",
        color=_C_REFERENCE,
        label=_t("Intensity level $L_I$", language),
    )
    _freq_axis(ax, freqs, language=language)
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.grid(visible=True, which="both", alpha=0.3)

    twin = ax.twinx()
    twin.bar(
        freqs,
        index,
        width=_bar_width(freqs),
        color=_C_TERTIARY,
        alpha=0.25,
        label=r"$\delta_{pI} = L_p - L_I$",
    )
    twin.set_ylabel(_t(r"Pressure-intensity index $\delta_{pI}$ [dB]", language))

    lines, labels = ax.get_legend_handles_labels()
    tlines, tlabels = twin.get_legend_handles_labels()
    legend = ax.legend(lines + tlines, labels + tlabels, fontsize="small")
    place_legend_clear(legend, twin)
    ax.set_title(
        "ISO 9614 $L_p$ vs $L_I$  "
        r"(total $\delta_{pI}$ = "
        f"{format_number(result.total_pressure_intensity_index, language, decimals=1)}"
        " dB)"
    )
    localize_axes(ax, language)
    localize_axes(twin, language)
    return ax


def plot_field_indicators(
    result: FieldIndicators,
    ax: Axes | None = None,
    *,
    dynamic_capability: float | np.ndarray | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-band ISO 9614-1 field indicators against the dynamic capability.

    Draws F2 (surface pressure-intensity) and F3 (negative partial power)
    per band, the optional dynamic capability index ``Ld`` as the
    criterion-1 reference line (the measurement arrangement is adequate
    where ``Ld > F2``) and, on a twin axis, the dimensionless field
    non-uniformity F4. When the result carries the temporal variability
    indicator F1 (that is, ``temporal_intensity`` was supplied), it is
    drawn on the same twin axis beside F4, together with the Table B.3
    limit of 0,6 that F1 must stay under.

    :param result: A :class:`~phonometry.emission.intensity.FieldIndicators`
        with per-band data (2D input to
        :func:`~phonometry.emission.intensity.field_indicators`).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param dynamic_capability: Optional ``Ld`` in dB (scalar or per band).
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the F2 curve ``plot`` call.
    :return: The axes.
    :raises ValueError: If the result carries no per-band data.
    """
    from .._i18n import localize_axes

    f2 = np.atleast_1d(np.asarray(result.f2, dtype=np.float64))
    if result.frequencies is None or f2.size < _MIN_BANDS:
        msg = (
            "plot() needs per-band indicators; call field_indicators(...) with "
            "2D (positions, bands) arrays and 'frequencies'."
        )
        raise ValueError(msg)
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    f3 = np.atleast_1d(np.asarray(result.f3, dtype=np.float64))
    f4 = np.atleast_1d(np.asarray(result.f4, dtype=np.float64))

    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t("$F_2$ (surface pressure-intensity)", language))
    ax.plot(freqs, f2, "o-", **kwargs)
    ax.plot(
        freqs,
        f3,
        "s--",
        color=_C_REFERENCE,
        label=_t("$F_3$ (negative partial power)", language),
    )
    if dynamic_capability is not None:
        ld = np.broadcast_to(
            np.asarray(dynamic_capability, dtype=np.float64), freqs.shape
        )
        ax.plot(
            freqs,
            ld,
            ls=":",
            lw=1.8,
            color=_C_MUTED,
            drawstyle="steps-mid",
            label=_t(r"Dynamic capability $L_\mathrm{d}$", language),
        )
    _freq_axis(ax, freqs, language=language)
    ax.set_ylabel(_t("Indicator [dB]", language))
    ax.grid(visible=True, which="both", alpha=0.3)

    twin = ax.twinx()
    twin.bar(
        freqs,
        f4,
        width=_bar_width(freqs),
        color=_C_TERTIARY,
        alpha=0.25,
        label=_t("$F_4$ (non-uniformity)", language),
    )
    twin.set_ylabel(_t("Field non-uniformity $F_4$", language))
    if result.f1 is not None:
        # F1 is dimensionless like F4, so it shares the twin axis; the
        # Table B.3 threshold above which the field is not stationary enough
        # is drawn alongside it.
        from ..emission.intensity import TEMPORAL_VARIABILITY_LIMIT

        f1 = np.broadcast_to(np.asarray(result.f1, dtype=np.float64), freqs.shape)
        twin.plot(
            freqs,
            f1,
            "^-",
            color=_C_SECONDARY,
            lw=1.4,
            label=_t("$F_1$ (temporal variability)", language),
        )
        twin.axhline(
            TEMPORAL_VARIABILITY_LIMIT,
            ls="-.",
            lw=1.0,
            color=_C_SECONDARY,
            label=_t("$F_1$ limit (Table B.3)", language),
        )
        twin.set_ylabel(_t("Dimensionless indicators $F_1$, $F_4$", language))

    lines, labels = ax.get_legend_handles_labels()
    tlines, tlabels = twin.get_legend_handles_labels()
    legend = ax.legend(lines + tlines, labels + tlabels, fontsize="small")
    place_legend_clear(legend, twin)
    ax.set_title(_t("ISO 9614-1 field indicators", language))
    localize_axes(ax, language)
    localize_axes(twin, language)
    return ax


def plot_vibration_sound_power(
    result: VibrationSoundPowerResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Radiated sound power level per band (ISO/TS 7849).

    :param result: A :class:`~phonometry.emission.vibration_sound_power.VibrationSoundPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the bar ``plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = _plot_band_level_bars(
        ax,
        result.sound_power_level,
        result.frequencies,
        result.total_level,
        ylabel=_t(_YLABEL_LW_ABSOLUTE, language),
        title=_t("ISO/TS 7849 sound power from surface vibration", language),
        language=language,
        **kwargs,
    )
    localize_axes(ax, language)
    return ax


_DEVICE_LABELS = {
    "probe": "probe",
    "processor": "processor",
    "instrument": "complete instrument",
}


def plot_intensity_class(
    result: IntensityInstrumentComplianceResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Measured pressure-residual intensity index over the IEC 61043 masks.

    Draws the measured ``delta_pI0`` per one-third-octave band against the
    Table 2 class 1 and class 2 *minima* for the device kind, already rescaled
    to the microphone separation in use. Because the requirement is a floor,
    the pass region of the reference class (the achieved class, or class 2 when
    the chain complies with neither) lies *above* its mask and is shaded,
    following the same convention as :func:`plot_filter_class`.

    The bands that cost the chain the *next* class up are ringed: for a class 2
    chain those are the bands under the class 1 minimum, and for a chain that
    meets no class those are the bands under the class 2 minimum. A class 1
    chain clears everything, so nothing is ringed.

    :param result: An
        :class:`~phonometry.emission.intensity_compliance.IntensityInstrumentComplianceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    measured = np.asarray(result.residual_index, dtype=np.float64)
    class1 = np.asarray(result.limit_class1, dtype=np.float64)
    class2 = np.asarray(result.limit_class2, dtype=np.float64)
    cls = result.reference_class()
    mask = class1 if cls == 1 else class2

    y_bot = float(np.floor(min(measured.min(), class2.min()) - 2.0))
    y_top = float(np.ceil(max(measured.max(), class1.max()) + 3.0))

    # Opaque, because the fiche renders this plot through svglib, which drops
    # alpha: a translucent fill would come out as a solid block over the
    # measured curve. theme_fill mixes the page towards the hue instead, so the
    # region reads the same way on either background.
    ax.fill_between(
        freqs,
        mask,
        y_top,
        step="mid",
        facecolor=theme_fill(_C_TERTIARY, ax),
        edgecolor="none",
        zorder=0,
        label=_t("Class {cls} pass region", language, cls=cls),
    )
    # Both Table 2 masks in the same amber, class 1 solid and class 2 dashed,
    # as the published intensity-analyser displays draw them.
    ax.plot(
        freqs,
        class1,
        drawstyle="steps-mid",
        color=_C_SECONDARY,
        lw=1.3,
        label=_t("Class 1 minimum", language),
    )
    ax.plot(
        freqs,
        class2,
        drawstyle="steps-mid",
        color=_C_SECONDARY,
        lw=1.3,
        ls="--",
        label=_t("Class 2 minimum", language),
    )

    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 3.0)
    kwargs.setdefault("drawstyle", "steps-mid")
    kwargs.setdefault("label", _t(r"Measured $\delta_{pI0}$", language))
    ax.plot(freqs, measured, **kwargs)

    # Ring the bands that block the next class up: class 1 for a class 2 chain,
    # class 2 for a chain that meets neither. A class 1 chain has none.
    marked_cls = 1 if result.overall_class == 2 else 2  # noqa: PLR2004
    marked_mask = class1 if marked_cls == 1 else class2
    failing = (
        np.zeros(freqs.shape, dtype=bool)
        if result.overall_class == 1
        else measured < marked_mask - 1e-9
    )
    if np.any(failing):
        ax.plot(
            freqs[failing],
            measured[failing],
            ls="",
            marker="o",
            ms=6.0,
            mfc="none",
            mew=1.6,
            color=_C_REFERENCE,
            label=_t("Below the class {cls} minimum", language, cls=marked_cls),
        )

    format_frequency_axis(ax, float(freqs.min()), float(freqs.max()), language=language)
    ax.set_xlim(float(freqs.min()) / 1.15, float(freqs.max()) * 1.15)
    ax.set_ylim(y_bot, y_top)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(_LABEL_RESIDUAL_INDEX, language))
    ax.set_title(
        _t(
            "IEC 61043 Table 2: {device}, {spacing} mm separation",
            language,
            device=_t(_DEVICE_LABELS[result.device], language),
            # ``:g`` prints the separation exactly as the chain was verified
            # with (a 6.35 mm quarter-inch spacer stays 6.35, which a fixed
            # one-decimal format would round away); only its decimal separator
            # needs localising, and ``spacing`` is validated positive, so the
            # sign never enters.
            spacing=decimal_comma(f"{result.spacing * 1000.0:g}", language),
        )
    )
    ax.legend(loc=_LEGEND_LOWER_RIGHT, fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def _mark_background(
    bars: BarContainer,
    *,
    not_met: np.ndarray,
    upper: np.ndarray,
    labels: tuple[str, str],
) -> list[Rectangle]:
    """Hatch the bands that fail the background requirement, and say why.

    A band the standard makes an upper bound (the source under test's margin
    fell short, the reference source's did not) is hatched ``//``; any other
    band that fails the requirement, a short reference margin or no
    background measured at all, is cross-hatched ``xx``, since its level is
    no bound either way. The first bar of each group carries the legend
    label itself rather than a free-standing proxy patch: a caller that
    rebuilds the legend from the axes (the report fiches do) then still
    finds both entries.

    :param labels: ``(upper-bound legend, requirement-not-met legend)``,
        already translated.
    :return: The labelled bars, in that order, for the legend.
    """
    failing = np.asarray(not_met, dtype=bool)
    bound = np.asarray(upper, dtype=bool) & failing
    handles: list[Rectangle] = []
    for mask, hatch, label in (
        (bound, "//", labels[0]),
        (failing & ~bound, "xx", labels[1]),
    ):
        marked = np.flatnonzero(mask)
        for index in marked:
            bars[int(index)].set_hatch(hatch)
            bars[int(index)].set_edgecolor(_C_EDGE)
        if marked.size:
            bars[int(marked[0])].set_label(label)
            handles.append(bars[int(marked[0])])
    return handles


def _plot_determined_spectrum(
    ax: Axes,
    *,
    levels: np.ndarray,
    frequencies: np.ndarray,
    not_met: np.ndarray,
    upper_bound: np.ndarray,
    expanded: np.ndarray,
    total: float,
    labels: tuple[str, str, str, str, str],
    language: str,
    kwargs: dict[str, Any],
) -> Axes:
    """The bar spectrum the ISO 3743 determinations share.

    One bar per octave band, hatched where the band is an upper bound and
    cross-hatched where it fails the background requirement otherwise, the
    expanded uncertainty as an error bar where it is finite, and the
    A-weighted total on the second line of the title.

    :param labels: ``(y label, title, total symbol, upper-bound legend,
        requirement-not-met legend)``, already translated.
    """
    from .._i18n import format_number, localize_axes

    ylabel, title, symbol, upper_label, not_met_label = labels
    positions = _band_axis(ax, frequencies, language=language)
    style_default(kwargs, "color", _C_PRIMARY)
    bars = ax.bar(positions, np.nan_to_num(levels), **kwargs)
    background = _mark_background(
        bars,
        not_met=not_met,
        upper=upper_bound,
        labels=(upper_label, not_met_label),
    )
    handles: list[Any] = []
    with_u = np.isfinite(expanded) & np.isfinite(levels)
    if np.any(with_u):
        handles.append(
            ax.errorbar(
                positions[with_u],
                levels[with_u],
                yerr=expanded[with_u],
                fmt="none",
                ecolor=theme_line(ax.xaxis.label.get_color(), ax, quiet=0.8),
                elinewidth=1.0,
                capsize=3.0,
                label=_t("Expanded uncertainty $U$", language),
            )
        )
    handles.extend(background)
    ax.set_ylabel(ylabel)
    if np.isfinite(total):
        # The total takes a line of its own: with the method named, one line
        # runs past the edge of a default-size figure.
        title += f"\n{symbol} = {format_number(total, language, decimals=1)} dB(A)"
    ax.set_title(title)
    if "label" in kwargs:
        handles.insert(0, bars)
    if handles:
        ax.legend(handles=handles, loc=_LEGEND_LOWER_RIGHT, fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_hard_walled_sound_power(
    result: HardWalledSoundPowerResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""Sound power (or energy) spectrum in a hard-walled test room.

    One bar per octave band of ``LW``, or of ``LJ`` for an energy
    determination. A band where the source under test's background margin
    fell below the 6 dB of ISO 3743-1:2010 4.5 is hatched as the upper bound
    8.1.3 makes it; a band that fails 4.5 otherwise (the reference source's
    margin, or no background measured) is cross-hatched, since the capped
    :math:`K_{1(\mathrm{RSS})}` lowers its level. The expanded uncertainty is
    drawn where ``sigma_omc`` was supplied.

    :param result: A
        :class:`~phonometry.emission.sound_power_hard_walled.HardWalledSoundPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the band :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    energy = result.quantity == "energy"
    return _plot_determined_spectrum(
        ax,
        levels=np.asarray(
            result.sound_energy_level if energy else result.sound_power_level,
            dtype=np.float64,
        ),
        frequencies=np.asarray(result.frequencies, dtype=np.float64),
        not_met=~np.asarray(result.background_requirement_met, dtype=bool),
        upper_bound=np.asarray(result.upper_bound, dtype=bool),
        expanded=np.asarray(result.expanded_uncertainty, dtype=np.float64),
        total=float(
            result.sound_energy_level_a if energy else result.sound_power_level_a
        ),
        labels=(
            _t(_YLABEL_LJ if energy else _YLABEL_LW, language),
            "ISO 3743-1 "
            + _t(
                "sound energy spectrum" if energy else "sound power spectrum", language
            ),
            "$L_{J\\mathrm{A}}$" if energy else _LWA_SYMBOL,
            _t(_UPPER_BOUND_LABEL, language),
            _t("Background requirement (4.5) not shown to be met", language),
        ),
        language=language,
        kwargs=kwargs,
    )


def plot_special_room_sound_power(
    result: SpecialRoomSoundPowerResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Sound power spectrum in a special reverberation test room.

    One bar per octave band of ``LW`` by the direct or the comparison method
    of ISO 3743-2:2018, a band whose background requirement is not shown to
    be met (a margin below the 4 dB of 9.8, or no background measured)
    cross-hatched and named as such, which is all 9.8 says of it, and the
    expanded uncertainty drawn where ``sigma_omc`` was supplied. The title
    carries the Annex F total.

    :param result: A
        :class:`~phonometry.emission.sound_power_special_room.SpecialRoomSoundPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the band :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    method = _t(
        _DIRECT_METHOD if result.method == "direct" else "comparison method",
        language,
    )
    return _plot_determined_spectrum(
        ax,
        levels=np.asarray(result.sound_power_level, dtype=np.float64),
        frequencies=np.asarray(result.frequencies, dtype=np.float64),
        not_met=~np.asarray(result.background_requirement_met, dtype=bool),
        upper_bound=np.zeros(result.frequencies.shape, dtype=bool),
        expanded=np.asarray(result.expanded_uncertainty, dtype=np.float64),
        total=float(result.sound_power_level_a),
        labels=(
            _t(_YLABEL_LW, language),
            f"ISO 3743-2 {_t('sound power spectrum', language)}, {method}",
            _LWA_SYMBOL,
            _t(_UPPER_BOUND_LABEL, language),
            _t("Background requirement (9.8) not shown to be met", language),
        ),
        language=language,
        kwargs=kwargs,
    )


def plot_hard_walled_room_check(
    result: HardWalledRoomCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The spread between the orientations of 4.4 against Table 3.

    One bar per octave band for the largest difference between the mean
    levels of any two orientations of the directional source, and a short
    horizontal mark at the Table 3 standard deviation of reproducibility it may
    not exceed; a bar over its mark is drawn in the failure colour. The legend
    keys each colour by a bar that carries it, so a failing first band does
    not lend its colour to the passing ones. The title gives the verdict on
    every criterion evaluated (4.2, 4.3 and 4.4).

    :param result: A
        :class:`~phonometry.emission.sound_power_hard_walled.HardWalledRoomCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the spread bars.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    spread = np.asarray(result.level_range_db, dtype=np.float64)
    limit = np.asarray(result.limit_db, dtype=np.float64)
    ok = np.asarray(result.band_adequate, dtype=bool)
    positions = _band_axis(ax, freqs, language=language)
    style_default(
        kwargs, "color", [_C_PRIMARY if good else _C_REFERENCE for good in ok]
    )
    label = kwargs.pop("label", _t("Largest spread between orientations", language))
    bars = ax.bar(positions, spread, **kwargs)
    marks = ax.hlines(
        limit,
        positions - 0.4,
        positions + 0.4,
        colors=_C_SECONDARY,
        lw=2.2,
        label=_t(r"Table 3 limit $\sigma_{R0}$", language),
    )
    # A bar container hands the legend the colour of its first bar, which is
    # the failure colour whenever the lowest band fails; key each colour by a
    # bar that carries it instead.
    handles: list[Any] = []
    passing, failing = np.flatnonzero(ok), np.flatnonzero(~ok)
    if passing.size:
        bars[int(passing[0])].set_label(label)
        handles.append(bars[int(passing[0])])
    handles.append(marks)
    if failing.size:
        bars[int(failing[0])].set_label(_t("Spread above the limit", language))
        handles.append(bars[int(failing[0])])
    ax.set_ylim(0.0, 1.3 * float(max(np.max(spread), np.max(limit))))
    ax.set_ylabel(_t(_SPREAD_LABEL, language))
    verdict = _t("qualified" if result.passes else _NOT_QUALIFIED, language)
    ax.set_title(
        _t("ISO 3743-1 room qualification: {verdict}", language, verdict=verdict)
    )
    ax.legend(handles=handles, loc="upper left", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_source_location_plan(
    result: SourceLocationPlan,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The survey standard deviation per band against the class limits of the
    table, with the number of source locations over each bar.

    ISO 3743-1:2010 Table 2 draws its lines at 2,5 dB and 4,0 dB, and a band
    above the second sends two more locations to another room, written
    ``2+2``; ISO 3743-2:2018 Table 3 draws them at 2,3 dB and 4 dB and adds
    the A-weighted row as a bar of its own when it was surveyed.

    :param result: A
        :class:`~phonometry.emission.sound_power_hard_walled.SourceLocationPlan`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the standard-deviation bars.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    s_m = [float(v) for v in result.standard_deviation_db]
    counts = [
        f"{int(n)}+{int(extra)}" if extra else f"{int(n)}"
        for n, extra in zip(
            result.source_locations, result.additional_room_locations, strict=True
        )
    ]
    ticks: list[str] = [_format_freq(float(f), language) for f in result.frequencies]
    with_a = bool(np.isfinite(result.a_weighted_standard_deviation_db))
    if with_a:
        ticks.append("A")
        s_m.append(float(result.a_weighted_standard_deviation_db))
        counts.append(f"{int(result.a_weighted_source_locations)}")
    positions = _band_axis(ax, ticks, language=language)
    if with_a:
        ax.set_xlabel(_t(_A_BAND_LABEL, language))
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Survey standard deviation", language))
    bars = ax.bar(positions, s_m, **kwargs)
    part_1 = result.standard == "ISO 3743-1:2010"
    # Each limit line carries its own legend entry: what the table does at it.
    limits = (
        (
            (2.5, "--", "Table 2: one location up to 2.5 dB"),
            (4.0, ":", "Table 2: two locations up to 4.0 dB"),
        )
        if part_1
        else (
            (2.3, "--", "Table 3: 2.3 dB, narrow-band components (9.5)"),
            (4.0, ":", "Table 3: 4 dB, discrete tone (9.5)"),
        )
    )
    for value, style, label in limits:
        ax.axhline(
            value, color=_C_SECONDARY, ls=style, lw=1.2, label=_t(label, language)
        )
    # The figures over the bars need their key: the number of source
    # locations the table gives, and "N+2" for the second room of Table 2.
    ax.plot(
        [],
        [],
        ls="none",
        marker="$N$",
        ms=8.0,
        color=ax.xaxis.label.get_color(),
        label=_t(
            "N over a bar: source locations (Table 2)"
            if part_1
            else "N over a bar: source locations (Table 3)",
            language,
        ),
    )
    if any(int(extra) for extra in result.additional_room_locations):
        ax.plot(
            [],
            [],
            ls="none",
            marker="$+2$",
            ms=11.0,
            color=ax.xaxis.label.get_color(),
            label=_t("N+2: two more locations in another room", language),
        )
    for bar, text in zip(bars, counts, strict=True):
        ax.annotate(
            text,
            (bar.get_x() + bar.get_width() / 2.0, bar.get_height()),
            xytext=(0.0, 3.0),
            textcoords=_OFFSET_POINTS,
            ha="center",
            va="bottom",
            fontsize="small",
        )
    ax.set_ylim(0.0, 1.3 * max(*s_m, 4.0))
    ax.set_ylabel(_t(_SM_LABEL, language))
    ax.set_title(
        _t(
            "{standard} source locations, {mics} microphone positions",
            language,
            standard=result.standard,
            mics=result.microphone_positions,
        )
    )
    ax.legend(loc="upper left", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_special_room_reverberation(
    result: SpecialRoomReverberationCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The measured :math:`T/T_\mathrm{nom}` within the limiting curves of
    ISO 3743-2:2018 6.3, laid out as Figure B.3.

    The shaded band runs from :math:`0{,}9\,R` to :math:`1{,}1\,R` (0,8 and 1,2
    above the 6,3 kHz band, as the text of 6.3 says; Figure B.3 widens it at
    6,3 kHz already), the dotted curve is the ideal ratio :math:`R`, and a band
    outside the limits is ringed. The title gives :math:`T_\mathrm{nom}` and
    the verdict of 6.2, 6.3 and 6.6 together.

    :param result: A
        :class:`~phonometry.emission.sound_power_special_room.SpecialRoomReverberationCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured curve.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    r = np.asarray(result.reverberation_parameter, dtype=np.float64)
    lower = np.asarray(result.lower_limit, dtype=np.float64) * r
    upper = np.asarray(result.upper_limit, dtype=np.float64) * r
    measured = np.asarray(result.ratio_to_nominal, dtype=np.float64)
    ax.fill_between(
        freqs,
        lower,
        upper,
        facecolor=theme_fill(_C_TERTIARY, ax),
        edgecolor="none",
        zorder=0,
        label=_t("Limiting curves", language),
    )
    ax.plot(freqs, lower, color=_C_TERTIARY, lw=1.0)
    ax.plot(freqs, upper, color=_C_TERTIARY, lw=1.0)
    ax.plot(
        freqs,
        r,
        color=theme_line(ax.xaxis.label.get_color(), ax, quiet=0.7),
        ls=":",
        lw=1.2,
        label=_t("Ideal ratio $R$", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 3.0)
    kwargs.setdefault("label", _t(r"Measured $T/T_\mathrm{nom}$", language))
    ax.plot(freqs, measured, **kwargs)
    outside = ~np.asarray(result.band_within, dtype=bool)
    if np.any(outside):
        ax.plot(
            freqs[outside],
            measured[outside],
            ls="",
            marker="o",
            ms=7.0,
            mfc="none",
            mew=1.6,
            color=_C_REFERENCE,
            label=_t("Outside the limiting curves", language),
        )
    format_frequency_axis(ax, float(freqs.min()), float(freqs.max()), language=language)
    ax.set_xlim(float(freqs.min()) / 1.15, float(freqs.max()) * 1.15)
    ax.set_ylim(0.0, 1.15 * float(max(np.max(upper), np.max(measured))))
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(_T_NOMINAL_LABEL, language))
    ax.set_title(
        _t(
            r"ISO 3743-2 reverberation time, $T_\mathrm{{nom}}$ = {tnom} s: {verdict}",
            language,
            tnom=format_number(
                result.nominal_reverberation_time_s, language, decimals=2
            ),
            verdict=_t("qualified" if result.passes else _NOT_QUALIFIED, language),
        )
    )
    ax.legend(loc="upper right", fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_special_room_surfaces(
    result: SpecialRoomSurfaceCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The absorption of each wall and of the ceiling within 0,5 to 1,5 times
    their mean, and the floor against its 0,06 (ISO 3743-2:2018 6.4).

    A coefficient outside either criterion is ringed, the verdict is in the
    title, and the legend goes where it covers the fewest points, with head
    room above the curves for it.

    :param result: A
        :class:`~phonometry.emission.sound_power_special_room.SpecialRoomSurfaceCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to every wall and ceiling curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    mean = np.asarray(result.mean_absorption, dtype=np.float64)
    floor = np.asarray(result.floor_absorption, dtype=np.float64)
    ax.fill_between(
        freqs,
        0.5 * mean,
        1.5 * mean,
        facecolor=theme_fill(_C_TERTIARY, ax),
        edgecolor="none",
        zorder=0,
        label=_t("0.5 to 1.5 times the mean", language),
    )
    palette = (_C_PRIMARY, _C_QUATERNARY, _C_PRIMARY_LIGHT, _C_TERTIARY, _C_MUTED)
    surfaces = np.asarray(result.surface_absorption, dtype=np.float64)
    for index, alpha in enumerate(surfaces):
        style = dict(kwargs)
        style_default(style, "color", palette[index % len(palette)])
        style_default(style, "lw", 1.4)
        style.setdefault("marker", "o")
        style_default(style, "ms", 3.0)
        style.setdefault("label", _t("Wall or ceiling {n}", language, n=index + 1))
        ax.plot(freqs, alpha, **style)
    ax.plot(
        freqs,
        floor,
        color=_C_SECONDARY,
        ls="--",
        lw=1.4,
        marker="s",
        ms=3.0,
        label=_t("Floor", language),
    )
    ax.axhline(
        0.06, color=_C_REFERENCE, ls=":", lw=1.2, label=_t("Floor limit 0.06", language)
    )
    out_x = [
        *np.broadcast_to(freqs, surfaces.shape)[~result.surface_within],
        *freqs[~result.floor_reflective],
    ]
    out_y = [*surfaces[~result.surface_within], *floor[~result.floor_reflective]]
    if out_x:
        ax.plot(
            out_x,
            out_y,
            ls="",
            marker="o",
            ms=8.0,
            mfc="none",
            mew=1.6,
            color=_C_REFERENCE,
            label=_t("Outside 6.4", language),
        )
    format_frequency_axis(ax, float(freqs.min()), float(freqs.max()), language=language)
    ax.set_xlim(float(freqs.min()) / 1.15, float(freqs.max()) * 1.15)
    # Head room above the curves: the legend has one row per surface.
    top = float(max(np.max(surfaces), np.max(floor), np.max(1.5 * mean), 0.06))
    ax.set_ylim(0.0, 2.0 * top)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(_ALPHA_LABEL, language))
    ax.set_title(
        _t(
            "ISO 3743-2 surface treatment (6.4): {verdict}",
            language,
            verdict=_t("complies" if result.passes else "does not comply", language),
        )
    )
    place_legend_clear(ax.legend(fontsize="small", ncol=2))
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_special_room_suitability(
    result: SpecialRoomSuitabilityCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The difference between a reference source determined in the room and
    its calibration, within the ± Table 1 limits of ISO 3743-2:2018 6.7.

    :param result: A
        :class:`~phonometry.emission.sound_power_special_room.SpecialRoomSuitabilityCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the difference bars.
    :return: The axes.
    """
    from matplotlib.patches import Patch

    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    difference = np.asarray(result.difference_db, dtype=np.float64)
    limit = np.asarray(result.limit_db, dtype=np.float64)
    ok = np.asarray(result.band_within, dtype=bool)
    positions = _band_axis(ax, freqs, language=language)
    style_default(
        kwargs, "color", [_C_PRIMARY if good else _C_REFERENCE for good in ok]
    )
    ax.bar(positions, difference, **kwargs)
    ax.hlines(
        np.concatenate([limit, -limit]),
        np.concatenate([positions, positions]) - 0.4,
        np.concatenate([positions, positions]) + 0.4,
        colors=_C_SECONDARY,
        lw=2.2,
        label=_t("Table 1 limits", language),
    )
    ax.axhline(0.0, color=_C_EDGE, lw=0.8)
    handles, _ = ax.get_legend_handles_labels()
    if not np.all(ok):
        handles.append(
            Patch(facecolor=_C_REFERENCE, label=_t("Beyond Table 1", language))
        )
    bound = 1.3 * float(max(np.max(np.abs(difference)), np.max(limit)))
    ax.set_ylim(-bound, bound)
    ax.set_ylabel(_t(_DIFFERENCE_LABEL, language))
    verdict = _t("suitable" if result.passes else "not suitable", language)
    ax.set_title(
        _t("ISO 3743-2 room suitability (6.7): {verdict}", language, verdict=verdict)
    )
    ax.legend(handles=handles, loc=_LEGEND_LOWER_RIGHT, fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


# ---------------------------------------------------------------------------
# Steam turbine sets (IEC 61063)
# ---------------------------------------------------------------------------

#: Label of the dashed outline every turbine layout draws.
_TURBINE_SURFACE_LABEL = "Measurement surface"
#: The horizontal extent of Figure A.3, in A/S: from 0,5 to 300.
_FIGURE_A3_RATIO_RANGE = (0.5, 300.0)
#: The A/S values Figure A.3 labels on its axis.
_FIGURE_A3_RATIO_TICKS = (0.5, 1.0, 5.0, 10.0, 50.0, 100.0, 300.0)
#: Where Figure A.3 turns from dashed to solid: the qualification of A.3.3.
_FIGURE_A3_QUALIFIED_RATIO = 1.0
#: The environmental correction A.3.3 allows at most, in dB.
_TURBINE_K_LIMIT_DB = 7.0


def _turbine_outline(
    surface: TurbineMeasurementSurface, view: str
) -> tuple[np.ndarray, np.ndarray]:
    """The closed outline of the measurement surface in plan or elevation."""
    edges = np.asarray(surface.x_edges_m)
    upper_x = np.repeat(edges, 2)[1:-1]
    if view == "plan":
        half = np.asarray(surface.widths_m) / 2.0
        upper_y = np.repeat(half, 2)
        xs = np.concatenate(
            ([edges[0]], upper_x, [edges[-1]], upper_x[::-1], [edges[0]])
        )
        ys = np.concatenate(([0.0], upper_y, [0.0], -upper_y[::-1], [0.0]))
        return xs, ys
    heights = np.asarray(surface.heights_m)
    xs = np.concatenate(([edges[0]], upper_x, [edges[-1]]))
    zs = np.concatenate(([0.0], np.repeat(heights, 2), [0.0]))
    return xs, zs


def _turbine_boxes(surface: TurbineMeasurementSurface, ax: Axes, view: str) -> None:
    """Shade each reference box and write its label inside it."""
    from matplotlib.patches import Rectangle

    d = float(surface.measurement_distance_m)
    edges = np.asarray(surface.x_edges_m)
    box_fill = theme_fill(_C_MUTED, ax)
    for i, box in enumerate(surface.reference_boxes):
        x0 = float(edges[i]) + (d if i == 0 else 0.0)
        if view == "plan":
            rect = Rectangle((x0, -box.width_m / 2.0), box.length_m, box.width_m)
            # Off the shaft line, where the overhead positions stand in plan.
            centre = -box.width_m / 4.0
            across = box.width_m / 2.0
        else:
            rect = Rectangle((x0, 0.0), box.length_m, box.height_m)
            # Above the row of microphones round the sides, which the
            # elevation draws across every box.
            centre = 0.72 * box.height_m
            across = box.height_m
        rect.set_facecolor(box_fill)
        rect.set_edgecolor(_C_EDGE)
        rect.set_linewidth(1.0)
        ax.add_patch(rect)
        if box.label:
            ax.text(
                x0 + box.length_m / 2.0,
                centre,
                box.label,
                ha="center",
                va="center",
                fontsize=8,
                rotation=90 if box.length_m < 0.6 * across else 0,
            )


def _turbine_positions(
    array: TurbineMicrophoneArray, ax: Axes, view: str, language: str
) -> None:
    """Draw the key positions as numbered crosses and the others as circles."""
    positions = np.asarray(array.positions_m)
    overhead = np.asarray(array.overhead_mask, dtype=bool)
    key = np.asarray(array.key_mask, dtype=bool)
    if view == "plan":
        px, py = positions[:, 0], positions[:, 1]
        shown = np.ones(len(positions), dtype=bool)
    else:
        # The elevation is seen from the side of key position 4, as both
        # elevations of Figure 2 are: the far side would stand on the same
        # points and add nothing.
        px, py = positions[:, 0], positions[:, 2]
        shown = overhead | (positions[:, 1] <= 0.0)
    side = shown & ~key & ~overhead
    top = shown & ~key & overhead
    ax.plot(
        px[side],
        py[side],
        linestyle="none",
        marker="o",
        ms=5.0,
        mfc="none",
        mec=_C_PRIMARY,
        label=_t("Additional positions", language),
    )
    if np.any(top):
        ax.plot(
            px[top],
            py[top],
            linestyle="none",
            marker="o",
            ms=5.0,
            mfc="none",
            mec=_C_SECONDARY,
            label=_t("Overhead positions", language),
        )
    marked = shown & key
    ax.plot(
        px[marked],
        py[marked],
        linestyle="none",
        marker="x",
        ms=8.0,
        mew=2.0,
        color=_C_REFERENCE,
        label=_t("Key positions", language),
    )
    labels = np.asarray(array.labels)[marked]
    for x, y, label in zip(px[marked], py[marked], labels, strict=True):
        ax.annotate(
            str(label),
            xy=(x, y),
            xytext=(5, 5),
            textcoords=_OFFSET_POINTS,
            fontsize=9,
            fontweight="bold",
            color=_C_REFERENCE,
        )


def plot_turbine_layout(
    surface: TurbineMeasurementSurface,
    array: TurbineMicrophoneArray | None,
    ax: Axes | None = None,
    *,
    view: str = "plan",
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The reference boxes, the measurement surface and the positions on it.

    Figure 2 of IEC 61063 in plan or in elevation: each reference box as a
    shaded rectangle with its label, the measurement surface 1 m out as a
    dashed outline, and, when an array is given, the key positions as crosses
    with their number and the additional ones as circles, the overhead ones in
    a second colour. The elevation shows the near side only, the side of key
    position 4, as both elevations of the figure do, with the reflecting
    plane beneath.

    :param surface: A
        :class:`~phonometry.emission.turbine_noise.TurbineMeasurementSurface`.
    :param array: A
        :class:`~phonometry.emission.turbine_noise.TurbineMicrophoneArray`, or
        ``None`` for the surface alone.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param view: ``"plan"`` or ``"elevation"``.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the outline of the measurement surface.
    :return: The axes.
    :raises ValueError: for a view that is neither.
    """
    from .._i18n import format_number, localize_axes

    if view not in ("plan", "elevation"):
        msg = f"view must be 'plan' or 'elevation'; got {view!r}."
        raise ValueError(msg)
    ax = ax if ax is not None else _new_axes()
    _turbine_boxes(surface, ax, view)
    xs, ys = _turbine_outline(surface, view)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "linestyle", "--")
    style_default(kwargs, "linewidth", 1.4)
    kwargs.setdefault("label", _t(_TURBINE_SURFACE_LABEL, language))
    ax.plot(xs, ys, **kwargs)
    if view == "elevation":
        # The reflecting plane, in the page's own ink.
        ax.axhline(0.0, color=ax.xaxis.label.get_color(), linewidth=2.0)
    if array is not None:
        _turbine_positions(array, ax, view, language)
    # Metres on both axes at one scale, the frame fitted to the surface with a
    # margin for the position numbers and a band above it for the legend.
    length = float(np.asarray(surface.x_edges_m)[-1])
    band = max(3.5, 0.15 * length)
    ax.set_xlim(-1.0, length + 1.0)
    if view == "plan":
        half = float(surface.max_width_m) / 2.0
        ax.set_ylim(-half - 1.0, half + band)
    else:
        ax.set_ylim(-0.5, float(surface.max_height_m) + band)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(_t("Along the shaft $x$ [m]", language))
    ax.set_ylabel(
        _t("Across the shaft $y$ [m]", language)
        if view == "plan"
        else _t("Height $z$ [m]", language)
    )
    area = format_number(float(surface.area_m2), language, decimals=1)
    title = (
        "IEC 61063 plan, $S$ = {area} m²"
        if view == "plan"
        else "IEC 61063 elevation, $S$ = {area} m²"
    )
    ax.set_title(_t(title, language, area=area))
    legend = ax.legend(fontsize="small", ncols=2)
    place_legend_clear(legend)
    localize_axes(ax, language)
    return ax


def plot_turbine_environmental_correction(
    correction_db: float,
    ratio: float | None,
    *,
    passes: bool | None,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""Figure A.3 of IEC 61063 with one test environment on it.

    The curve :math:`K = 10 \lg[1 + 4/(A/S)]` over the range the figure
    prints, 0,5 to 300, dashed where :math:`A/S < 1` as the figure draws it,
    the 7 dB of A.3.3 as a limit line, and the environment as a point, or as
    a horizontal line when its :math:`K` came from a reference source and
    carries no :math:`A/S`.

    :param correction_db: :math:`K` of the environment, in dB.
    :param ratio: Its :math:`A/S`, or ``None``.
    :param passes: The verdict of the check, for the title, or ``None``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the solid part of the curve.
    :return: The axes.
    """
    from matplotlib.ticker import FixedLocator, FuncFormatter, LogLocator, NullFormatter

    from .._i18n import decimal_comma, format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    low, high = _FIGURE_A3_RATIO_RANGE
    grid = np.geomspace(low, high, 400)
    curve = 10.0 * np.log10(1.0 + 4.0 / grid)
    qualified = grid >= _FIGURE_A3_QUALIFIED_RATIO
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "linewidth", 1.8)
    kwargs.setdefault("label", r"$K = 10\,\lg[1 + 4/(A/S)]$")
    (line,) = ax.plot(grid[qualified], curve[qualified], **kwargs)
    below = np.append(grid[~qualified], _FIGURE_A3_QUALIFIED_RATIO)
    ax.plot(
        below,
        10.0 * np.log10(1.0 + 4.0 / below),
        color=line.get_color(),
        linewidth=line.get_linewidth(),
        linestyle="--",
    )
    ax.axhline(
        _TURBINE_K_LIMIT_DB,
        color=_C_REFERENCE,
        linestyle=":",
        linewidth=1.4,
        label=_t("7 dB limit (A.3.3)", language),
    )
    shown = format_number(correction_db, language, decimals=2)
    if ratio is not None:
        ax.plot(
            [ratio],
            [correction_db],
            linestyle="none",
            marker="o",
            ms=8.0,
            color=_C_SECONDARY,
            label=_t("This room, $K$ = {k} dB", language, k=shown),
        )
    else:
        ax.axhline(
            correction_db,
            color=_C_SECONDARY,
            linestyle="-.",
            linewidth=1.4,
            label=_t("Reference source, $K$ = {k} dB", language, k=shown),
        )
    ax.set_xscale("log")
    # The default log axis writes only 10^0, 10^1 and 10^2, and a reader could
    # not place an A/S of 7 on it. The figure labels 0,5, 1, 5, 10, 50, 100
    # and 300, written plainly; the other decades' steps stay as grid lines.
    ax.xaxis.set_major_locator(FixedLocator(_FIGURE_A3_RATIO_TICKS))
    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda value, _pos: decimal_comma(f"{value:g}", language))
    )
    ax.xaxis.set_minor_locator(
        LogLocator(base=10.0, subs=(2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0))
    )
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(low, high)
    ax.set_ylim(0.0, 10.0)
    ax.set_xlabel("$A/S$")
    ax.set_ylabel(_t("Environmental correction $K$ [dB]", language))
    title = _t("IEC 61063 Figure A.3", language)
    if passes is not None:
        verdict = _t("qualifies" if passes else "does not qualify", language)
        title = f"{title}: {verdict}"
    ax.set_title(title)
    ax.grid(visible=True, which="both", alpha=0.3)
    legend = ax.legend(fontsize="small")
    place_legend_clear(legend)
    localize_axes(ax, language)
    return ax


def plot_turbine_sound_power(
    result: TurbineSoundPowerResult,
    ax: Axes | None = None,
    *,
    position_labels: Sequence[str] | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The level at each position after Table 2, and the surface level.

    One bar per microphone position of the corrected A-weighted level, the
    overhead positions in the second colour; the background at each position
    as a grey mark; the energy average of the positions as a dashed line and
    the surface sound pressure level of Equation (2), :math:`K` subtracted,
    as a solid one. A position whose background was less than 3 dB below is
    hatched, since the determination is then an upper limit.

    The bars stand in the order the levels were given. With the labels of the
    array the levels were measured on, the axis names only the key positions,
    with the numbers Figure 2 gives them; without them it counts the bars from
    1, which is not the numbering of the figure.

    :param result: A
        :class:`~phonometry.emission.turbine_noise.TurbineSoundPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param position_labels: One label per position, ``"1"`` to ``"5"`` for the
        key positions and ``""`` for the others
        (:attr:`~phonometry.emission.turbine_noise.TurbineMicrophoneArray.labels`),
        or ``None``.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the position :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    :raises ValueError: if ``position_labels`` does not have one entry per
        position.
    """
    from matplotlib.patches import Patch
    from matplotlib.ticker import FixedLocator, MaxNLocator

    from .._i18n import format_number, localize_axes

    corrected = np.asarray(result.corrected_levels_db, dtype=np.float64)
    names = None if position_labels is None else tuple(str(n) for n in position_labels)
    if names is not None and len(names) != corrected.size:
        msg = (
            f"position_labels must have one entry per position ({corrected.size}); "
            f"got {len(names)}."
        )
        raise ValueError(msg)
    ax = ax if ax is not None else _new_axes()
    positions = np.arange(1, corrected.size + 1)
    overhead = (
        np.zeros(corrected.size, dtype=bool)
        if result.overhead_mask is None
        else np.asarray(result.overhead_mask, dtype=bool)
    )
    colours = [_C_SECONDARY if top else _C_PRIMARY for top in overhead]
    style_default(kwargs, "color", colours)
    kwargs.setdefault("edgecolor", _C_EDGE)
    kwargs.setdefault("width", 0.8)
    kwargs.setdefault("label", _t(r"Corrected level $L_{p\mathrm{A}i}$", language))
    bars = ax.bar(positions, corrected, **kwargs)
    limited = result.limited_positions
    if limited is not None:
        _hatch_invalid(bars, np.asarray(limited, dtype=bool))
    floor = float(np.min(corrected))
    if result.background_levels_db is not None:
        background = np.asarray(result.background_levels_db, dtype=np.float64)
        floor = min(floor, float(np.min(background)))
        ax.plot(
            positions,
            background,
            linestyle="none",
            marker="_",
            ms=10.0,
            mew=2.0,
            color=_C_MUTED,
            label=_t("Background", language),
        )
    energy = float(
        result.surface_pressure_level_db + result.environmental_correction_db
    )
    ax.axhline(
        energy,
        color=theme_line(ax.xaxis.label.get_color(), ax, quiet=0.7),
        linestyle="--",
        linewidth=1.2,
        label=_t("Energy average", language),
    )
    level = format_number(result.surface_pressure_level_db, language, decimals=1)
    ax.axhline(
        float(result.surface_pressure_level_db),
        color=_C_REFERENCE,
        linewidth=1.6,
        label=_t("Surface level {level} dB", language, level=level),
    )
    top = max(float(np.max(corrected)), energy)
    ax.set_ylim(np.floor(floor / 5.0) * 5.0 - 5.0, top + 6.0)
    ax.set_xlim(0.5, corrected.size + 0.5)
    keys = [] if names is None else [(i + 1, n) for i, n in enumerate(names) if n]
    if keys:
        # Only the key positions carry a number in Figure 2; every other bar
        # keeps an unlabelled tick.
        ax.xaxis.set_major_locator(FixedLocator([float(i) for i, _ in keys]))
        ax.set_xticklabels([n for _, n in keys])
        ax.xaxis.set_minor_locator(FixedLocator([float(i) for i in positions]))
        ax.set_xlabel(_t("Microphone position (key positions numbered)", language))
    else:
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, steps=[1, 2, 5, 10]))
        ax.set_xlabel(_t("Microphone position, in the order given", language))
    ax.set_ylabel(_t("A-weighted sound pressure level [dB]", language))
    power = format_number(result.sound_power_level_db, language, decimals=1)
    ax.set_title(
        _t(
            _IEC_61063_TITLE,
            language,
            power=power,
        )
    )
    # The positions are categories: no vertical grid line through the bars.
    ax.grid(visible=False, axis="x")
    ax.grid(visible=True, axis="y", alpha=0.3)
    handles, labels = ax.get_legend_handles_labels()
    if np.any(overhead):
        handles.append(Patch(facecolor=_C_SECONDARY, edgecolor=_C_EDGE))
        labels.append(_t("Overhead position", language))
    if result.upper_limit:
        handles.append(Patch(facecolor=_C_PRIMARY, edgecolor=_C_EDGE, hatch="//"))
        labels.append(_t("Upper limit: background within 3 dB", language))
    legend = ax.legend(handles, labels, fontsize="small", ncols=2)
    place_legend_clear(legend)
    localize_axes(ax, language)
    return ax


def plot_turbine_noise_declaration(
    declaration: TurbineNoiseDeclaration,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The reported sound power level of each operating condition.

    One bar per condition of the whole-decibel :math:`L_{WA}` of the report,
    with the standard deviation of Table 1 as an error bar, and the loudest
    condition named in the title (6.2 suggests repeating the measurement
    under every typical sustained load to find it).

    :param declaration: A
        :class:`~phonometry.emission.turbine_noise.TurbineNoiseDeclaration`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    levels = np.asarray(declaration.reported_sound_power_levels_db, dtype=np.float64)
    sigma = float(declaration.standard_deviation_db)
    x = np.arange(levels.size)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("edgecolor", _C_EDGE)
    kwargs.setdefault("width", 0.6)
    kwargs.setdefault("label", r"$L_{W\mathrm{A}}$")
    bars = ax.bar(x, levels, **kwargs)
    spread = format_number(sigma, language, decimals=0)
    ax.errorbar(
        x,
        levels,
        yerr=sigma,
        fmt="none",
        ecolor=theme_line(ax.xaxis.label.get_color(), ax, quiet=0.8),
        capsize=5.0,
        label=_t("Table 1: ±{sigma} dB", language, sigma=spread),
    )
    for bar, value in zip(bars, levels, strict=True):
        # On a chip of the axes' own colour, so no grid line runs through
        # the digits.
        ax.annotate(
            format_number(value, language, decimals=0),
            xy=(bar.get_x() + bar.get_width() / 2.0, value + sigma),
            xytext=(0, 4),
            textcoords=_OFFSET_POINTS,
            ha="center",
            va="bottom",
            fontsize=9,
            bbox={
                "boxstyle": "round,pad=0.15",
                "facecolor": ax.get_facecolor(),
                "edgecolor": "none",
            },
        )
    ax.set_xticks(x)
    ax.set_xticklabels(declaration.operating_conditions)
    ax.set_ylim(
        float(np.min(levels)) - 3.0 * sigma, float(np.max(levels)) + 3.0 * sigma
    )
    ax.set_ylabel(_t("A-weighted sound power level [dB re 1 pW]", language))
    ax.set_title(
        _t(
            "IEC 61063 report: loudest at {condition}",
            language,
            condition=declaration.loudest_condition,
        )
    )
    # The conditions are categories: no vertical grid line through the bars
    # and the values written over them.
    ax.grid(visible=False, axis="x")
    ax.grid(visible=True, axis="y", alpha=0.3)
    legend = ax.legend(fontsize="small")
    place_legend_clear(legend)
    localize_axes(ax, language)
    return ax
