#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for headphones and the programme signal (lazy imports from result .plot()).

The results of :mod:`phonometry.electroacoustics.headphones` (IEC
60268-7:2010) and of :mod:`phonometry.electroacoustics.programme_signal` (IEC
60268-1:1985 Clause 7). The Spanish labels follow the UNE-EN 60268 series:
*auricular*, *señal de programa simulado*, *impedancia asignada*, *tensión
característica*, *simulador de oído*, *atenuación de diafonía*.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_EDGE,
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _new_axes,
    format_frequency_axis,
    place_legend_clear,
    styled,
    theme_fill,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..electroacoustics.headphones import (
        CouplerFrequencyResponse,
        CrosstalkAttenuation,
        EarCanalFrequencyResponse,
        EarCanalMicrophoneVerification,
        FieldComparisonResponse,
        LimitingTestSignalCheck,
        ProgrammeCharacteristicVoltage,
        ProtectionVoltage,
        RatedImpedanceVerification,
    )
    from ..electroacoustics.programme_signal import ProgrammeSignalCheck

#: Shared axis label of the frequency panels.
_FREQUENCY = "Frequency [Hz]"
#: Shared ordinate of the coupler levels.
_SPL = "Sound pressure level [dB re 20 µPa]"
#: Shared ordinate of the responses referred to the reference band.
_RESPONSE = "Response re {freq} Hz [dB]"
#: Shared legend entry of the mean over the test persons.
_MEAN_OF_PERSONS = "Mean of {n} persons"
#: Shared legend entry of the spread between the test persons.
_STANDARD_DEVIATION = "Standard deviation"

#: Spanish translations of the fixed strings, keyed by their English text.
_STRINGS: dict[str, str] = {
    _FREQUENCY: "Frecuencia [Hz]",
    _SPL: "Nivel de presión acústica [dB ref. 20 µPa]",
    _RESPONSE: "Respuesta ref. {freq} Hz [dB]",
    "Relative level [dB]": "Nivel relativo [dB]",
    "Table II": "Tabla II",
    "Table II tolerance": "Tolerancia de la tabla II",
    "Band levels, referred": "Niveles de banda, referidos",
    "Simulated programme signal (IEC 60268-1): {verdict}": (
        "Señal de programa simulado (IEC 60268-1): {verdict}"
    ),
    "Clipped programme signal, peak/RMS {ratio}: {verdict}": (
        "Señal de programa recortada, pico/eficaz {ratio}: {verdict}"
    ),
    "Impedance [{ohm}]": "Impedancia [{ohm}]",
    "Impedance modulus": "Módulo de la impedancia",
    "Rated impedance {rated} {ohm}": "Impedancia asignada {rated} {ohm}",
    "80 % of the rated impedance": "80 % de la impedancia asignada",
    "Rated frequency range": "Rango de frecuencias asignado",
    "Rated impedance (8.2.1): {verdict}": "Impedancia asignada (8.2.1): {verdict}",
    "Lowest modulus in range {value} {ohm}": "Módulo mínimo en el rango {value} {ohm}",
    "Band level at the characteristic voltage": "Nivel de banda a la tensión característica",
    "Band level at that e.m.f.": "Nivel de banda a esa f.e.m.",
    "Power sum {level} dB": "Suma energética {level} dB",
    "Programme signal characteristic voltage (8.3.4) {voltage} V": (
        "Tensión característica con señal de programa (8.3.4) {voltage} V"
    ),
    "Corrected programme signal characteristic voltage (8.3.5) {voltage} V": (
        "Tensión característica corregida con señal de programa (8.3.5) {voltage} V"
    ),
    "Programme signal e.m.f. for 94 dB, A-weighted only: {voltage} V": (
        "F.e.m. con señal de programa para 94 dB, solo ponderada A: {voltage} V"
    ),
    "Programme signal e.m.f. for 94 dB, free-field compensated only: {voltage} V": (
        "F.e.m. con señal de programa para 94 dB, solo compensada en campo libre: "
        "{voltage} V"
    ),
    "A-weighted, free-field compensated band level [dB re 20 µPa]": (
        "Nivel de banda ponderado A y compensado en campo libre [dB ref. 20 µPa]"
    ),
    "A-weighted band level [dB re 20 µPa]": "Nivel de banda ponderado A [dB ref. 20 µPa]",
    "Free-field compensated band level [dB re 20 µPa]": (
        "Nivel de banda compensado en campo libre [dB ref. 20 µPa]"
    ),
    "Source e.m.f. [V]": "F.e.m. de la fuente [V]",
    "Sensitivity change [dB]": "Variación de la sensibilidad [dB]",
    "Sensitivity change": "Variación de la sensibilidad",
    "1 dB change": "Variación de 1 dB",
    "Protection voltage {voltage} V": "Tensión de protección {voltage} V",
    "Protective device (8.3.6)": "Dispositivo de protección (8.3.6)",
    "Protective device (8.3.6): not operated": (
        "Dispositivo de protección (8.3.6): no actúa"
    ),
    "Coupler response": "Respuesta en el acoplador",
    "Rated range": "Rango asignado",
    "Coupler or ear simulator frequency response (8.6.2)": (
        "Respuesta en frecuencia en acoplador o simulador de oído (8.6.2)"
    ),
    "Crosstalk attenuation [dB]": "Atenuación de diafonía [dB]",
    "Crosstalk attenuation": "Atenuación de diafonía",
    "Crosstalk attenuation (8.12), minimum {value} dB": (
        "Atenuación de diafonía (apartado 8.12), mínimo {value} dB"
    ),
    _MEAN_OF_PERSONS: "Media de {n} sujetos",
    _STANDARD_DEVIATION: "Desviación típica",
    "Free-field comparison frequency response (8.6.3)": (
        "Respuesta en frecuencia por comparación en campo libre (8.6.3)"
    ),
    "Diffuse-field comparison frequency response (8.6.4)": (
        "Respuesta en frecuencia por comparación en campo difuso (8.6.4)"
    ),
    "Test persons": "Sujetos de ensayo",
    "Ear canal frequency response, Formula (1) (8.6.5)": (
        "Respuesta en frecuencia en el conducto auditivo, fórmula (1) (8.6.5)"
    ),
    "Share of the limit [%]": "Fracción del límite [%]",
    "Limit": "Límite",
    "Entrance area": "Área en la entrada",
    "Area ratio": "Relación de áreas",
    "Volume": "Volumen",
    "Neighbouring bands": "Bandas contiguas",
    "Sealed entrance": "Entrada sellada",
    "(minimum)": "(mínimo)",
    "Within its limit": "Dentro de su límite",
    "Outside its limit": "Fuera de su límite",
    "Item e) is a minimum": "El apartado e) es un mínimo",
    "Ear canal microphone (Annex B): {verdict}": (
        "Micrófono en el conducto auditivo (anexo B): {verdict}"
    ),
}

#: The verdict words, English and Spanish, keyed by whether the check passes.
_VERDICTS: dict[bool, tuple[str, str]] = {
    True: ("pass", "cumple"),
    False: ("fail", "no cumple"),
}

#: The Unicode ohm sign, for the impedance axis.
_OHM = "Ω"

#: The length of 50 dB on the axis of 8.6.2.2 c), in decades of frequency.
_DB_PER_DECADE = 50.0

#: The top of the Annex B verdict's axis, as a multiple of its tallest bar or
#: limit: the space above them holds the legend.
_HEADROOM = 1.3

#: The least span of the response axis at 50 dB to the decade, in dB, so the
#: box of a two-decade panel does not flatten to a strip; the coupler's own
#: plot keeps 60 dB over its three decades.
_MIN_RESPONSE_SPAN_DB = 40.0


def _t(text: str, language: str = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


def _num(value: float, language: str, decimals: int = 1) -> str:
    """A number with the language's decimal separator and a true minus."""
    from .._i18n import format_number

    return format_number(value, language, decimals=decimals)


def _verdict(*, passes: bool, language: str) -> str:
    """The verdict word."""
    english, spanish = _VERDICTS[passes]
    return spanish if language == "es" else english


def _draw_programme_check(
    check: ProgrammeSignalCheck, ax: Axes, language: str, kwargs: dict[str, Any]
) -> None:
    """The referred band levels inside Table II's tolerances, without a title."""
    from .._i18n import localize_axes

    f = check.frequencies_hz
    table = check.relative_levels_db
    ax.fill_between(
        f,
        table - check.tolerance_minus_db,
        table + check.tolerance_plus_db,
        color=theme_fill(_C_PRIMARY, ax),
        lw=0,
        zorder=0,
        label=_t("Table II tolerance", language),
    )
    ax.plot(f, table, color=_C_EDGE, lw=1.0, ls="--", label=_t("Table II", language))
    ax.plot(
        f,
        check.band_levels_db + check.offset_db,
        **styled(
            kwargs,
            color=_C_SECONDARY,
            lw=1.6,
            marker="o",
            ms=3.5,
            label=_t("Band levels, referred", language),
        ),
    )
    format_frequency_axis(ax, float(f[0]) / 1.2, float(f[-1]) * 1.2, language=language)
    ax.set_xlabel(_t(_FREQUENCY, language))
    ax.set_ylabel(_t("Relative level [dB]", language))
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)


def plot_programme_signal_check(
    check: ProgrammeSignalCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Band levels, referred by the check's offset, inside Table II of IEC 60268-1.

    :param check: A :class:`~phonometry.electroacoustics.programme_signal.ProgrammeSignalCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the band levels' ``Axes.plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    _draw_programme_check(check, ax, language, kwargs)
    ax.set_title(
        _t(
            "Simulated programme signal (IEC 60268-1): {verdict}",
            language,
            verdict=_verdict(passes=check.passes, language=language),
        )
    )
    return ax


def plot_limiting_test_signal_check(
    check: LimitingTestSignalCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The clipped programme signal of IEC 60268-7 8.3.2: spectrum and peak ratio.

    :param check: A :class:`~phonometry.electroacoustics.headphones.LimitingTestSignalCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the band levels' ``Axes.plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    _draw_programme_check(check.spectrum, ax, language, kwargs)
    ax.set_title(
        _t(
            "Clipped programme signal, peak/RMS {ratio}: {verdict}",
            language,
            ratio=_num(check.peak_to_rms, language, 2),
            verdict=_verdict(passes=check.passes, language=language),
        )
    )
    return ax


def plot_rated_impedance(
    result: RatedImpedanceVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The modulus of a headphone's impedance with its rated value and 80 % of it.

    :param result: A :class:`~phonometry.electroacoustics.headphones.RatedImpedanceVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the impedance curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    f = result.frequencies_hz
    lower, upper = result.rated_frequency_range_hz
    ax.axvspan(
        lower,
        upper,
        color=theme_fill(_C_TERTIARY, ax),
        lw=0,
        zorder=0,
        label=_t("Rated frequency range", language),
    )
    ax.plot(
        f,
        result.impedance_ohm,
        **styled(
            kwargs, color=_C_PRIMARY, lw=1.6, label=_t("Impedance modulus", language)
        ),
    )
    ax.axhline(
        result.rated_impedance_ohm,
        color=_C_EDGE,
        lw=1.0,
        ls="--",
        label=_t(
            "Rated impedance {rated} {ohm}",
            language,
            rated=_num(result.rated_impedance_ohm, language, 0),
            ohm=_OHM,
        ),
    )
    ax.axhline(
        result.limit_ohm,
        color=_C_REFERENCE,
        lw=1.0,
        ls=":",
        label=_t("80 % of the rated impedance", language),
    )
    ax.plot(
        [result.minimum_frequency_hz],
        [result.minimum_ohm],
        ls="none",
        marker="o",
        ms=6,
        mfc="none",
        color=_C_REFERENCE,
        label=_t(
            "Lowest modulus in range {value} {ohm}",
            language,
            value=_num(result.minimum_ohm, language, 1),
            ohm=_OHM,
        ),
    )
    ax.set_xscale("log")
    format_frequency_axis(ax, float(f[0]), float(f[-1]), language=language)
    ax.set_ylim(0.0, 1.35 * float(np.max(result.impedance_ohm)))
    ax.set_xlabel(_t(_FREQUENCY, language))
    ax.set_ylabel(_t("Impedance [{ohm}]", language, ohm=_OHM))
    ax.set_title(
        _t(
            "Rated impedance (8.2.1): {verdict}",
            language,
            verdict=_verdict(passes=result.passes, language=language),
        )
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_programme_characteristic_voltage(
    result: ProgrammeCharacteristicVoltage,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The band levels at the characteristic voltage, whose power sum is 94 dB.

    :param result: A :class:`~phonometry.electroacoustics.headphones.ProgrammeCharacteristicVoltage`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the bars' ``Axes.bar``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    levels = result.band_levels_at_characteristic_db
    positions = np.arange(levels.size)
    floor = 10.0 * math.floor((float(np.min(levels)) - 5.0) / 10.0)
    # One correction alone gives an e.m.f. for 94 dB that the standard does
    # not name a characteristic voltage; the bars and the title say which.
    partial = result.a_weighted != result.free_field_compensated
    ax.bar(
        positions,
        levels - floor,
        bottom=floor,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            edgecolor=_C_EDGE,
            width=0.7,
            zorder=3,
            label=_t(
                "Band level at that e.m.f."
                if partial
                else "Band level at the characteristic voltage",
                language,
            ),
        ),
    )
    total = 10.0 * math.log10(float(np.sum(10.0 ** (levels / 10.0))))
    ax.axhline(
        total,
        color=_C_REFERENCE,
        lw=1.2,
        ls="--",
        label=_t("Power sum {level} dB", language, level=_num(total, language, 1)),
    )
    from .common import _format_freq

    step = max(1, levels.size // 12)
    ax.set_xticks(positions[::step])
    ax.set_xticklabels(
        [_format_freq(f, language) for f in result.frequencies_hz[::step]],
        rotation=45,
        ha="right",
    )
    ax.set_ylim(floor, total + 8.0)
    ax.set_xlabel(_t(_FREQUENCY, language))
    if result.a_weighted and result.free_field_compensated:
        ylabel = "A-weighted, free-field compensated band level [dB re 20 µPa]"
    elif result.a_weighted:
        ylabel = "A-weighted band level [dB re 20 µPa]"
    elif result.free_field_compensated:
        ylabel = "Free-field compensated band level [dB re 20 µPa]"
    else:
        ylabel = _SPL
    ax.set_ylabel(_t(ylabel, language))
    # Only the uncorrected (8.3.4) and the fully corrected (8.3.5) voltages are
    # characteristics of the standard; one correction alone is named as such.
    if result.a_weighted and result.free_field_compensated:
        title = "Corrected programme signal characteristic voltage (8.3.5) {voltage} V"
    elif result.a_weighted:
        title = "Programme signal e.m.f. for 94 dB, A-weighted only: {voltage} V"
    elif result.free_field_compensated:
        title = "Programme signal e.m.f. for 94 dB, free-field compensated only: {voltage} V"
    else:
        title = "Programme signal characteristic voltage (8.3.4) {voltage} V"
    ax.set_title(
        _t(title, language, voltage=_num(result.characteristic_voltage_v, language, 3))
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def _plain_log_ticks(ax: Axes, values: np.ndarray, language: str) -> None:
    """Label a logarithmic voltage axis at 1, 2 and 5 per decade, as plain numbers."""
    import matplotlib.ticker as mticker

    lowest, highest = float(np.min(values)), float(np.max(values))
    first, last = math.floor(math.log10(lowest)), math.ceil(math.log10(highest))
    ticks = [
        mantissa * 10.0**exponent
        for exponent in range(first, last + 1)
        for mantissa in (1.0, 2.0, 5.0)
        if lowest / 1.05 <= mantissa * 10.0**exponent <= highest * 1.05
    ]

    def _label(value: float, _: object) -> str:
        return _num(value, language, max(0, -math.floor(math.log10(value))))

    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_label))
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())


def plot_protection_voltage(
    result: ProtectionVoltage,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The change of sensitivity against the e.m.f., with the 1 dB line of 8.3.6.2 b).

    :param result: A :class:`~phonometry.electroacoustics.headphones.ProtectionVoltage`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the sensitivity curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    change = result.sensitivity_change_db
    ax.plot(
        result.source_emf_v,
        change,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.6,
            marker="o",
            ms=3.5,
            label=_t("Sensitivity change", language),
        ),
    )
    sign = -1.0 if float(np.min(change)) < -float(np.max(change)) else 1.0
    ax.axhline(
        sign * 1.0,
        color=_C_REFERENCE,
        lw=1.0,
        ls="--",
        label=_t("1 dB change", language),
    )
    voltage = result.protection_voltage_v
    if voltage is not None:
        ax.axvline(
            voltage,
            color=_C_SECONDARY,
            lw=1.0,
            ls=":",
            label=_t(
                "Protection voltage {voltage} V",
                language,
                voltage=_num(voltage, language, 2),
            ),
        )
        title = _t("Protective device (8.3.6)", language)
    else:
        title = _t("Protective device (8.3.6): not operated", language)
    ax.set_xscale("log")
    _plain_log_ticks(ax, result.source_emf_v, language)
    ax.set_xlabel(_t("Source e.m.f. [V]", language))
    ax.set_ylabel(_t("Sensitivity change [dB]", language))
    ax.set_title(title)
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_coupler_frequency_response(
    result: CouplerFrequencyResponse,
    ax: Axes | None = None,
    *,
    language: str = "en",
    iec_scale: bool = True,
    **kwargs: Any,
) -> Axes:
    """The coupler level against frequency, 50 dB to the length of a decade.

    :param result: A :class:`~phonometry.electroacoustics.headphones.CouplerFrequencyResponse`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param iec_scale: Fix the aspect of 8.6.2.2 c).
    :param kwargs: Forwarded to the response curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    f = result.frequencies_hz
    if result.rated_frequency_range_hz is not None:
        for index, edge in enumerate(result.rated_frequency_range_hz):
            ax.axvline(
                edge,
                color=_C_TERTIARY,
                lw=1.0,
                ls="--",
                label=_t("Rated range", language) if index == 0 else None,
            )
    ax.plot(
        f,
        result.sound_pressure_level_db,
        **styled(
            kwargs, color=_C_PRIMARY, lw=1.6, label=_t("Coupler response", language)
        ),
    )
    ax.set_xscale("log")
    lo, hi = float(f[0]), float(f[-1])
    if result.rated_frequency_range_hz is not None:
        # A little room either side, so a rated limit on the end of the sweep
        # stays visible.
        lo = min(lo, result.rated_frequency_range_hz[0]) / 1.15
        hi = max(hi, result.rated_frequency_range_hz[1]) * 1.15
    ax.set_xlim(lo, hi)
    # Room above the curve for the legend, and at least 60 dB of axis so the
    # box of 50 dB to a decade does not flatten to a strip.
    levels = result.sound_pressure_level_db
    top = 10.0 * math.ceil((float(np.max(levels)) + 15.0) / 10.0)
    bottom = top - max(60.0, 10.0 * math.ceil((top - float(np.min(levels))) / 10.0))
    ax.set_ylim(bottom, top)
    format_frequency_axis(ax, lo, hi, language=language)
    if iec_scale:
        # One decade of the log axis is one unit of its scaled coordinate, so
        # an aspect of 1/50 draws 50 dB the length of a decade.
        ax.set_aspect(1.0 / _DB_PER_DECADE, adjustable="box")
    ax.set_xlabel(_t(_FREQUENCY, language))
    ax.set_ylabel(_t(_SPL, language))
    ax.set_title(_t("Coupler or ear simulator frequency response (8.6.2)", language))
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_crosstalk_attenuation(
    result: CrosstalkAttenuation,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The crosstalk attenuation of 8.12 against frequency.

    :param result: A :class:`~phonometry.electroacoustics.headphones.CrosstalkAttenuation`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the attenuation curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    f = result.frequencies_hz
    ax.plot(
        f,
        result.attenuation_db,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.6,
            label=_t("Crosstalk attenuation", language),
        ),
    )
    ax.set_xscale("log")
    format_frequency_axis(ax, float(f[0]), float(f[-1]), language=language)
    ax.set_xlabel(_t(_FREQUENCY, language))
    ax.set_ylabel(_t("Crosstalk attenuation [dB]", language))
    ax.set_title(
        _t(
            "Crosstalk attenuation (8.12), minimum {value} dB",
            language,
            value=_num(result.minimum_db, language, 1),
        )
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def _response_limits(lowest: float, highest: float) -> tuple[float, float]:
    """A response axis of at least :data:`_MIN_RESPONSE_SPAN_DB` round the data."""
    span = max(
        _MIN_RESPONSE_SPAN_DB, 10.0 * math.ceil((highest - lowest + 10.0) / 10.0)
    )
    bottom = 5.0 * round((0.5 * (lowest + highest) - 0.5 * span) / 5.0)
    return bottom, bottom + span


def _band_ticks(ax: Axes, frequencies: np.ndarray, language: str) -> None:
    """Label a bar axis with every other band centre."""
    from .common import _format_freq

    positions = np.arange(frequencies.size)
    step = max(1, frequencies.size // 12)
    ax.set_xticks(positions[::step])
    ax.set_xticklabels(
        [_format_freq(f, language) for f in frequencies[::step]],
        rotation=45,
        ha="right",
    )


def plot_field_comparison_response(
    result: FieldComparisonResponse,
    ax: Axes | None = None,
    *,
    language: str = "en",
    iec_scale: bool = True,
    **kwargs: Any,
) -> Axes:
    """The mean comparison response as bars, with each band's standard deviation.

    :param result: A :class:`~phonometry.electroacoustics.headphones.FieldComparisonResponse`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param iec_scale: Draw 50 dB the length of a decade of the bands, the
        preferred scale of 8.6.3.2 e) and 8.6.4.2 e).
    :param kwargs: Forwarded to the bars' ``Axes.bar``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = np.arange(result.frequencies_hz.size)
    mean = result.mean_db
    spread = result.standard_deviation_db
    ax.bar(
        positions,
        mean,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            edgecolor=_C_EDGE,
            width=0.7,
            zorder=3,
            label=_t(_MEAN_OF_PERSONS, language, n=result.persons),
        ),
    )
    ax.errorbar(
        positions,
        mean,
        yerr=spread,
        fmt="none",
        ecolor=_C_REFERENCE,
        elinewidth=1.0,
        capsize=2.5,
        zorder=4,
        label=_t(_STANDARD_DEVIATION, language),
    )
    ax.axhline(0.0, color=_C_MUTED, lw=0.8, zorder=2)
    _band_ticks(ax, result.frequencies_hz, language)
    f = result.frequencies_hz
    if iec_scale:
        ax.set_ylim(
            *_response_limits(
                float(np.min(mean - spread)), float(np.max(mean + spread))
            )
        )
        if f.size > 1:
            # The bars stand one position apart, so a decade of the bands is
            # (bands - 1) / decades positions, and 50 dB has that length.
            per_decade = (f.size - 1) / math.log10(float(f[-1]) / float(f[0]))
            ax.set_aspect(per_decade / _DB_PER_DECADE, adjustable="box")
    else:
        reach = float(np.max(np.abs(mean) + spread))
        ax.set_ylim(-1.5 * reach - 1.0, 1.5 * reach + 1.0)
    ax.set_xlabel(_t(_FREQUENCY, language))
    ax.set_ylabel(
        _t(_RESPONSE, language, freq=_num(result.reference_frequency_hz, language, 0))
    )
    title = (
        "Free-field comparison frequency response (8.6.3)"
        if result.field == "free"
        else "Diffuse-field comparison frequency response (8.6.4)"
    )
    ax.set_title(_t(title, language))
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_ear_canal_frequency_response(
    result: EarCanalFrequencyResponse,
    ax: Axes | None = None,
    *,
    language: str = "en",
    iec_scale: bool = True,
    **kwargs: Any,
) -> Axes:
    """Each person's Formula (1), their mean and the standard deviation about it.

    :param result: A :class:`~phonometry.electroacoustics.headphones.EarCanalFrequencyResponse`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param iec_scale: Draw 50 dB the length of a decade, the preferred scale of
        8.6.5.2 h).
    :param kwargs: Forwarded to the mean response's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    f = result.frequencies_hz
    mean = result.mean_db
    spread = result.standard_deviation_db
    ax.fill_between(
        f,
        mean - spread,
        mean + spread,
        color=theme_fill(_C_PRIMARY, ax),
        lw=0,
        zorder=0,
        label=_t(_STANDARD_DEVIATION, language),
    )
    for index, person in enumerate(result.response_db):
        ax.plot(
            f,
            person,
            color=_C_MUTED,
            lw=0.7,
            alpha=0.7,
            zorder=1,
            label=_t("Test persons", language) if index == 0 else None,
        )
    ax.plot(
        f,
        mean,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.8,
            marker="o",
            ms=3.5,
            zorder=3,
            label=_t(_MEAN_OF_PERSONS, language, n=result.persons),
        ),
    )
    ax.axhline(0.0, color=_C_EDGE, lw=0.8, ls="--", zorder=2)
    ax.set_xscale("log")
    format_frequency_axis(ax, float(f[0]), float(f[-1]), language=language)
    if iec_scale:
        responses = result.response_db
        ax.set_ylim(
            *_response_limits(
                float(min(np.min(responses), np.min(mean - spread))),
                float(max(np.max(responses), np.max(mean + spread))),
            )
        )
        ax.set_aspect(1.0 / _DB_PER_DECADE, adjustable="box")
    ax.set_xlabel(_t(_FREQUENCY, language))
    ax.set_ylabel(
        _t(_RESPONSE, language, freq=_num(result.reference_frequency_hz, language, 0))
    )
    ax.set_title(_t("Ear canal frequency response, Formula (1) (8.6.5)", language))
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_ear_canal_microphone(
    result: EarCanalMicrophoneVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The five measurable items of Annex B as shares of their limits.

    Items a) to d) are upper limits, so a bar above 100 % fails; item e) is a
    lower limit, so its bar fails below 100 %. The figure says so: item e)'s
    bar is hatched and labelled as a minimum, and the legend keys the colour of
    a bar within its limit and of one outside it.

    :param result: A :class:`~phonometry.electroacoustics.headphones.EarCanalMicrophoneVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the bars' ``Axes.bar``.
    :return: The axes.
    """
    from matplotlib.patches import Patch

    from .._i18n import localize_axes
    from ..electroacoustics import headphones as hp

    ax = ax if ax is not None else _new_axes()
    shares = [
        100.0 * result.entrance_area_mm2 / hp._MAX_ENTRANCE_AREA_MM2,
        100.0 * result.area_ratio / hp._MAX_CANAL_AREA_RATIO,
        100.0 * result.volume_mm3 / hp._MAX_VOLUME_MM3,
        100.0 * result.neighbour_difference_db / hp._MAX_NEIGHBOUR_DIFFERENCE_DB,
        100.0 * result.sealed_attenuation_db / hp._MIN_SEALED_ATTENUATION_DB,
    ]
    verdicts = result.requirements
    colours = [_C_TERTIARY if verdicts[key] else _C_REFERENCE for key in "abcde"]
    names = [
        "Entrance area",
        "Area ratio",
        "Volume",
        "Neighbouring bands",
        "Sealed entrance",
    ]
    positions = np.arange(len(shares))
    bars = ax.bar(
        positions,
        shares,
        **styled(kwargs, color=colours, edgecolor=_C_EDGE, width=0.55, zorder=3),
    )
    # Item e) is the one lower limit: hatched, so its bar reads the other way.
    bars.patches[-1].set_hatch("//")
    limit = ax.axhline(
        100.0,
        color=_C_REFERENCE,
        lw=1.2,
        ls="--",
        zorder=4,
        label=_t("Limit", language),
    )
    ax.set_xticks(positions)
    ax.set_xticklabels(
        [
            f"{key})\n{_t(name, language)}"
            + (f"\n{_t('(minimum)', language)}" if key == "e" else "")
            for key, name in zip("abcde", names, strict=True)
        ],
        fontsize=8,
    )
    handles: list[Any] = [limit]
    for passes, colour, text in (
        (True, _C_TERTIARY, "Within its limit"),
        (False, _C_REFERENCE, "Outside its limit"),
    ):
        if passes in verdicts.values():
            handles.append(
                Patch(facecolor=colour, edgecolor=_C_EDGE, label=_t(text, language))
            )
    handles.append(
        Patch(
            facecolor="none",
            edgecolor=_C_EDGE,
            hatch="//",
            label=_t("Item e) is a minimum", language),
        )
    )
    ax.set_ylim(0.0, _HEADROOM * max(100.0, *shares))
    ax.set_ylabel(_t("Share of the limit [%]", language))
    ax.set_title(
        _t(
            "Ear canal microphone (Annex B): {verdict}",
            language,
            verdict=_verdict(passes=result.passes, language=language),
        )
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(handles=handles, fontsize="small"))
    localize_axes(ax, language)
    return ax
