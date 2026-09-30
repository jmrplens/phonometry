#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for induction-loop systems (lazy imports from result .plot()).

The results of :mod:`phonometry.electroacoustics.induction_loop` (IEC
60118-4:2014 with its Amendment 1:2017) and of
:mod:`phonometry.electroacoustics.induction_loop_components` (IEC
62489-1:2010 with its Amendment 1:2014). The Spanish labels follow UNE-EN
60118-4:2016: *intensidad del campo magnético*, *telebobina*, *volumen de
campo magnético útil*, *relación señal-ruido de referencia*.
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
    style_default,
    styled,
    theme_fill,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..electroacoustics.induction_loop import (
        AmplifierOverloadVerification,
        BackgroundNoiseAssessment,
        FieldStrengthReading,
        InductionLoopVerification,
        LoopRequirement,
    )
    from ..electroacoustics.induction_loop_components import (
        AgcCharacteristic,
        AmplifierFrequencyResponse,
        LoopField,
        LoopImpedance,
        MaximumOutputCurrent,
        NeckLoopCharacteristics,
        NeckLoopVerification,
        QuadraturePhaseError,
    )

#: Shared axis label of the frequency panels.
_FREQUENCY = "Frequency [Hz]"
#: Shared ordinate of the field strength level panels.
_LEVEL = "Field strength level [dB re 400 mA/m]"
#: Shared ordinate of the responses normalized to 1 kHz.
_RESPONSE = "Response re 1 kHz [dB]"
#: Legend entry of the 0 dB reference.
_REFERENCE = "Reference, 400 mA/m"
#: Legend entry of an amplifier's output current curve.
_OUTPUT_CURRENT = "Output current"
#: Legend entry of the tolerance band of the response panels; it reads the
#: same in Spanish.
_PLUS_MINUS_3_DB = "±3 dB"

#: Spanish translations of the fixed strings, keyed by their English text.
#: The terms are those of UNE-EN 60118-4:2016.
_STRINGS: dict[str, str] = {
    _FREQUENCY: "Frecuencia [Hz]",
    _LEVEL: "Nivel de intensidad del campo magnético [dB ref. 400 mA/m]",
    _RESPONSE: "Respuesta ref. 1 kHz [dB]",
    _REFERENCE: "Referencia, 400 mA/m",
    "Position": "Posición",
    "Tolerance ±3 dB": "Tolerancia ±3 dB",
    "Field strength of the loop": "Intensidad del campo magnético del bucle",
    "{component} component": "Componente {component}",
    "Magnitude": "Módulo",
    "Loop impedance": "Impedancia del bucle",
    "Impedance [{ohm}]": "Impedancia [{ohm}]",
    "Resistance": "Resistencia",
    "Corner frequency {freq} Hz": "Frecuencia de corte {freq} Hz",
    "Amplifier frequency response": "Respuesta en frecuencia del amplificador",
    _OUTPUT_CURRENT: "Corriente de salida",
    "Output/input characteristic": "Característica salida/entrada",
    "Input level [dB]": "Nivel de entrada [dB]",
    "Output level re rated maximum current [dB]": (
        "Nivel de salida ref. corriente máxima asignada [dB]"
    ),
    "AGC range {range} dB ({recommended} dB recommended)": (
        "Rango del AGC {range} dB ({recommended} dB recomendados)"
    ),
    "3 dB below the highest output": "3 dB por debajo de la salida máxima",
    "Quadrature network phase error": "Error de fase de la red en cuadratura",
    "Deviation from 90° [°]": "Desviación respecto a 90° [°]",
    "Phase error": "Error de fase",
    "Maximum {dev}° at {freq} Hz": "Máximo {dev}° a {freq} Hz",
    "Band judged, 100 Hz to 5 kHz": "Banda evaluada, de 100 Hz a 5 kHz",
    "Neck loop on the test jig": "Bucle de cuello en el maniquí de ensayo",
    "Response": "Respuesta",
    _PLUS_MINUS_3_DB: _PLUS_MINUS_3_DB,
    "3 dB from the response at 1 kHz": "3 dB respecto a la respuesta a 1 kHz",
    "Neck loop, draft type {type}": "Bucle de cuello, tipo {type} del borrador",
    "Share of the limit [%]": "Fracción del límite [%]",
    "DC resistance": "Resistencia en continua",
    "Input voltage for 400 mA/m": "Tensión de entrada para 400 mA/m",
    "Upper limit of the type": "Límite superior del tipo",
    "Lower limit of the type": "Límite inferior del tipo",
    "Field strength meter, {weighting}-weighted": (
        "Medidor de intensidad de campo, ponderación {weighting}"
    ),
    "Time [s]": "Tiempo [s]",
    "Level (F)": "Nivel (F)",
    "Maximum {level} dB": "Máximo {level} dB",
    "Magnetic background noise": "Ruido magnético de fondo",
    "Measurement point": "Punto de medición",
    "A-weighted noise level [dB re 400 mA/m]": (
        "Nivel de ruido con ponderación A [dB ref. 400 mA/m]"
    ),
    "Noise level": "Nivel de ruido",
    "Ideal (SNR 47 dB)": "Ideal (señal-ruido 47 dB)",
    "Recommended minimum (SNR 32 dB)": "Mínimo recomendado (señal-ruido 32 dB)",
    "Short periods only (SNR 22 dB)": "Solo periodos cortos (señal-ruido 22 dB)",
    "Reference SNR {snr} dB: {category}": "Relación señal-ruido de referencia {snr} dB: {category}",
    "ideal": "ideal",
    "acceptable": "aceptable",
    "tolerable_for_short_periods": "tolerable durante periodos cortos",
    "below_tolerable": "por debajo de lo tolerable",
    "Judged value": "Valor evaluado",
    "Value [dB]": "Valor [dB]",
    "Measured": "Medido",
    "Lower limit": "Límite inferior",
    "Upper limit": "Límite superior",
    "Worst margin [dB]": "Margen mínimo [dB]",
    "Margin": "Margen",
    "IEC 60118-4, clause {clause}: {verdict}": "IEC 60118-4, capítulo {clause}: {verdict}",
    "{name} ({clause}): {verdict}": "{name} (apartado {clause}): {verdict}",
    "{name}\n{clause}": "{name}\napartado {clause}",
    "Overload test, {freq} Hz programme limit": (
        "Ensayo de sobrecarga, límite del programa {freq} Hz"
    ),
    "Loop voltage [V]": "Tensión en el bucle [V]",
    "Loop voltage": "Tensión en el bucle",
    "Compliance voltage": "Tensión de cumplimiento",
    "Table 4 frequency": "Frecuencia de la tabla 4",
    "Voltage judged by 10.3.3": "Tensión que juzga el 10.3.3",
    "Voltage doubled": "Tensión duplicada",
    "Maximum output current (5.4.7)": "Corriente de salida máxima (5.4.7)",
    "Load current [A]": "Corriente en la carga [A]",
    "Total harmonic distortion [%]": "Distorsión armónica total [%]",
    "Distortion": "Distorsión",
    "Rated THD {thd} %": "THD asignada {thd} %",
    "Maximum current {current} A": "Corriente máxima {current} A",
}

#: The verdict words, English and Spanish, keyed by whether the check passes.
_VERDICTS: dict[bool, tuple[str, str]] = {
    True: ("pass", "cumple"),
    False: ("fail", "no cumple"),
}

#: The requirement names, as the figures print them.
_REQUIREMENT_NAMES: dict[str, tuple[str, str]] = {
    "field_strength": ("Field strength", "Intensidad de campo"),
    "frequency_response": ("Frequency response", "Respuesta en frecuencia"),
    "system_noise": ("System noise", "Ruido del sistema"),
    "field_strength_range": ("Range ±6 dB", "Intervalo ±6 dB"),
    "field_strength_reached": ("400 mA/m reached", "400 mA/m alcanzados"),
    "standing_area": ("Standing area ≤ +8 dB", "Zona de pie ≤ +8 dB"),
}

#: The Unicode ohm sign, for the impedance axis.
_OHM = "Ω"

#: The factor the overload sweep's frequency axis extends beyond its ends.
_SWEEP_MARGIN = 1.15

#: The top of the neck-loop verdict's axis, as a multiple of its tallest bar
#: or limit: the space above them holds the legend.
_NECK_LOOP_HEADROOM = 1.3

#: The room left below the 47 dB line and above the 22 dB line of the
#: background noise panel, in dB; the upper one holds the legend.
_NOISE_PAD_BELOW_DB = 3.0
_NOISE_PAD_ABOVE_DB = 12.0


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


def _requirement_name(name: str, language: str) -> str:
    """The printed name of a requirement."""
    english, spanish = _REQUIREMENT_NAMES.get(name, (name, name))
    return spanish if language == "es" else english


def _position_axis(result: LoopField) -> tuple[np.ndarray, str]:
    """The coordinate that varies most among the points, and its name."""
    spans = {
        name: float(np.ptp(values)) if values.size else 0.0
        for name, values in (("x", result.x_m), ("y", result.y_m), ("z", result.z_m))
    }
    name = max(spans, key=lambda key: spans[key])
    return np.ravel(getattr(result, f"{name}_m")), name


def plot_loop_field(
    result: LoopField,
    ax: Axes | None = None,
    *,
    component: str = "z",
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The field strength level of a loop along its points.

    :param result: A :class:`~phonometry.electroacoustics.induction_loop_components.LoopField`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param component: The component to draw.
    :param language: Label language.
    :param kwargs: Forwarded to the level curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    position, axis_name = _position_axis(result)
    level = np.ravel(result.level_db(component))
    order = np.argsort(position)
    label = (
        _t("Magnitude", language)
        if component == "magnitude"
        else _t("{component} component", language, component=f"$H_{component}$")
    )
    ax.plot(
        position[order],
        level[order],
        **styled(kwargs, color=_C_PRIMARY, lw=1.6, label=label),
    )
    ax.axhline(0.0, color=_C_REFERENCE, lw=1.0, ls="--", label=_t(_REFERENCE, language))
    ax.axhspan(
        -3.0,
        3.0,
        color=theme_fill(_C_PRIMARY, ax),
        zorder=0,
        lw=0,
        label=_t("Tolerance ±3 dB", language),
    )
    ax.set_xlabel(f"{_t('Position', language)} ${axis_name}$ [m]")
    ax.set_ylabel(_t(_LEVEL, language))
    ax.set_title(_t("Field strength of the loop", language))
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_loop_impedance(
    result: LoopImpedance,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The magnitude of a loop's impedance against frequency.

    :param result: A :class:`~phonometry.electroacoustics.induction_loop_components.LoopImpedance`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the impedance curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    ax.plot(
        result.frequencies_hz,
        result.impedance_ohm,
        **styled(kwargs, color=_C_PRIMARY, lw=1.6, marker="o", ms=3, label="$|Z|$"),
    )
    ax.axhline(
        result.resistance_ohm,
        color=_C_MUTED,
        lw=1.0,
        ls="--",
        label=_t("Resistance", language),
    )
    corner = result.corner_frequency_hz
    lo, hi = float(result.frequencies_hz[0]), float(result.frequencies_hz[-1])
    if lo <= corner <= hi:
        ax.axvline(
            corner,
            color=_C_SECONDARY,
            lw=1.0,
            ls=":",
            label=_t(
                "Corner frequency {freq} Hz", language, freq=_num(corner, language, 0)
            ),
        )
    ax.set_xscale("log")
    format_frequency_axis(ax, lo, hi, language=language)
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel(_t(_FREQUENCY, language))
    ax.set_ylabel(_t("Impedance [{ohm}]", language, ohm=_OHM))
    ax.set_title(_t("Loop impedance", language))
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def _response_panel(
    ax: Axes,
    frequencies: np.ndarray,
    response: np.ndarray,
    kwargs: dict[str, Any],
    label: str,
    language: str,
) -> None:
    """A response against frequency with the 0 dB line and the ±3 dB band."""
    ax.plot(
        frequencies,
        response,
        **styled(kwargs, color=_C_PRIMARY, lw=1.6, marker="o", ms=3, label=label),
    )
    ax.axhline(0.0, color=_C_EDGE, lw=0.8)
    ax.axhspan(
        -3.0,
        3.0,
        color=theme_fill(_C_PRIMARY, ax),
        zorder=0,
        lw=0,
        label=_t(_PLUS_MINUS_3_DB, language),
    )
    ax.set_xscale("log")
    format_frequency_axis(
        ax, float(frequencies[0]), float(frequencies[-1]), language=language
    )
    ax.set_xlabel(_t(_FREQUENCY, language))
    ax.set_ylabel(_t(_RESPONSE, language))
    ax.grid(visible=True, which="both", alpha=0.3)


def plot_amplifier_frequency_response(
    result: AmplifierFrequencyResponse,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """An amplifier's current response into its load, 0 dB at 1 kHz.

    :param result: An :class:`~phonometry.electroacoustics.induction_loop_components.AmplifierFrequencyResponse`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the response curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    _response_panel(
        ax,
        result.frequencies_hz,
        result.response_db,
        kwargs,
        _t(_OUTPUT_CURRENT, language),
        language,
    )
    ax.set_title(_t("Amplifier frequency response", language))
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_agc_characteristic(
    result: AgcCharacteristic,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Output level against input level, with the AGC range shaded.

    :param result: An :class:`~phonometry.electroacoustics.induction_loop_components.AgcCharacteristic`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the characteristic's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    ax.plot(
        result.source_emf_db,
        result.output_level_db,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.6,
            marker="o",
            ms=3,
            label=_t(_OUTPUT_CURRENT, language),
        ),
    )
    top = float(
        np.interp(result.agc_range_end_db, result.source_emf_db, result.output_level_db)
    )
    ax.axvspan(
        result.agc_range_start_db,
        result.agc_range_end_db,
        color=theme_fill(_C_PRIMARY, ax),
        zorder=0,
        lw=0,
        label=_t(
            "AGC range {range} dB ({recommended} dB recommended)",
            language,
            range=_num(result.agc_range_db, language),
            recommended=_num(result.recommended_range_db, language, 0),
        ),
    )
    ax.axhline(
        top - 3.0,
        color=_C_SECONDARY,
        lw=1.0,
        ls="--",
        label=_t("3 dB below the highest output", language),
    )
    ax.set_xlabel(_t("Input level [dB]", language))
    ax.set_ylabel(_t("Output level re rated maximum current [dB]", language))
    ax.set_title(_t("Output/input characteristic", language))
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_quadrature_phase_error(
    result: QuadraturePhaseError,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The deviation from 90 degrees between two loop currents.

    :param result: A :class:`~phonometry.electroacoustics.induction_loop_components.QuadraturePhaseError`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the deviation curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    ax.plot(
        result.frequencies_hz,
        result.deviation_deg,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.6,
            marker="o",
            ms=3,
            label=_t("Phase error", language),
        ),
    )
    ax.plot(
        [result.max_deviation_frequency_hz],
        [result.max_deviation_deg],
        ls="none",
        marker="D",
        ms=6,
        color=_C_REFERENCE,
        label=_t(
            "Maximum {dev}° at {freq} Hz",
            language,
            dev=_num(result.max_deviation_deg, language),
            freq=_num(result.max_deviation_frequency_hz, language, 0),
        ),
    )
    ax.axvspan(
        100.0,
        5000.0,
        color=theme_fill(_C_PRIMARY, ax),
        zorder=0,
        lw=0,
        label=_t("Band judged, 100 Hz to 5 kHz", language),
    )
    ax.set_xscale("log")
    format_frequency_axis(
        ax,
        float(result.frequencies_hz[0]),
        float(result.frequencies_hz[-1]),
        language=language,
    )
    ax.set_xlabel(_t(_FREQUENCY, language))
    ax.set_ylabel(_t("Deviation from 90° [°]", language))
    ax.set_title(_t("Quadrature network phase error", language))
    ax.set_ylim(bottom=0.0)
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_neck_loop_characteristics(
    result: NeckLoopCharacteristics,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """A neck loop's frequency response on the jig, 0 dB at 1 kHz.

    :param result: A :class:`~phonometry.electroacoustics.induction_loop_components.NeckLoopCharacteristics`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the response curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    _response_panel(
        ax,
        result.frequencies_hz,
        result.response_db,
        kwargs,
        _t("Response", language),
        language,
    )
    for k, frequency in enumerate(result.frequencies_3db_hz):
        ax.axvline(
            frequency,
            color=_C_SECONDARY,
            lw=1.0,
            ls=":",
            label=_t("3 dB from the response at 1 kHz", language) if k == 0 else None,
        )
    ax.set_title(_t("Neck loop on the test jig", language))
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_neck_loop_verification(
    result: NeckLoopVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """A neck loop's two values as shares of their draft limits.

    Each bar carries its own limits: the input voltage an upper one, the DC
    resistance of type 1 both, and that of type 2 only the lower one it has,
    so a bar above an upper limit or below a lower one is outside its type.

    :param result: A :class:`~phonometry.electroacoustics.induction_loop_components.NeckLoopVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the bars' ``Axes.bar``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    limits = result.limits
    bounded = math.isfinite(limits.max_dc_resistance_ohm)
    scale = limits.max_dc_resistance_ohm if bounded else limits.min_dc_resistance_ohm
    shares = [
        100.0 * result.dc_resistance_ohm / scale,
        100.0 * result.input_voltage_v / limits.max_input_voltage_v,
    ]
    colours = [
        _C_TERTIARY if result.resistance_passes else _C_REFERENCE,
        _C_TERTIARY if result.voltage_passes else _C_REFERENCE,
    ]
    labels = [_t("DC resistance", language), _t("Input voltage for 400 mA/m", language)]
    ax.bar(
        np.arange(2),
        shares,
        **styled(kwargs, color=colours, edgecolor=_C_EDGE, width=0.55, zorder=3),
    )
    # (bar, share of the limit, is it an upper limit)
    marks = [(1, 100.0, True)]
    if bounded:
        marks += [
            (0, 100.0, True),
            (0, 100.0 * limits.min_dc_resistance_ohm / scale, False),
        ]
    else:
        marks.append((0, 100.0, False))
    labelled: set[bool] = set()
    for bar, share, upper in sorted(marks, key=lambda mark: not mark[2]):
        text = "Upper limit of the type" if upper else "Lower limit of the type"
        ax.plot(
            [bar - 0.36, bar + 0.36],
            [share, share],
            color=_C_REFERENCE,
            lw=1.4,
            ls="--" if upper else ":",
            zorder=4,
            label=None if upper in labelled else _t(text, language),
        )
        labelled.add(upper)
    ax.set_xticks(np.arange(2))
    ax.set_xticklabels(labels, fontsize=8)
    # Room above the bars and their limits for the legend.
    ax.set_ylim(0.0, _NECK_LOOP_HEADROOM * max(100.0, *shares))
    ax.set_ylabel(_t("Share of the limit [%]", language))
    ax.set_title(
        f"{_t('Neck loop, draft type {type}', language, type=result.neck_loop_type)}: "
        f"{_verdict(passes=result.passes, language=language)}"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_field_strength_reading(
    result: FieldStrengthReading,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The meter's time-weighted level against time.

    :param result: A :class:`~phonometry.electroacoustics.induction_loop.FieldStrengthReading`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the level curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    finite = np.isfinite(result.levels_db)
    ax.plot(
        result.times_s[finite],
        result.levels_db[finite],
        **styled(kwargs, color=_C_PRIMARY, lw=1.2, label=_t("Level (F)", language)),
    )
    ax.axhline(0.0, color=_C_REFERENCE, lw=1.0, ls="--", label=_t(_REFERENCE, language))
    # The maximum as a point where it occurs: a line at its level would lie on
    # the reference whenever the level was set right, and vanish into it.
    peak = int(np.argmax(np.where(finite, result.levels_db, -np.inf)))
    ax.plot(
        [result.times_s[peak]],
        [result.maximum_db],
        ls="none",
        marker="D",
        ms=6,
        color=_C_SECONDARY,
        zorder=4,
        label=_t(
            "Maximum {level} dB", language, level=_num(result.maximum_db, language)
        ),
    )
    ax.set_xlabel(_t("Time [s]", language))
    ax.set_ylabel(_t(_LEVEL, language))
    ax.set_title(
        _t(
            "Field strength meter, {weighting}-weighted",
            language,
            weighting=result.weighting,
        )
    )
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_background_noise(
    result: BackgroundNoiseAssessment,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The noise at each point against the lines of 7.2.

    :param result: A :class:`~phonometry.electroacoustics.induction_loop.BackgroundNoiseAssessment`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the noise levels' ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    points = np.arange(1, result.noise_levels_db.size + 1)
    ax.plot(
        points,
        result.noise_levels_db,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.2,
            marker="o",
            ms=5,
            label=_t("Noise level", language),
        ),
    )
    for level, text, colour, style in (
        (-47.0, "Ideal (SNR 47 dB)", _C_TERTIARY, "-"),
        (-32.0, "Recommended minimum (SNR 32 dB)", _C_SECONDARY, "--"),
        (-22.0, "Short periods only (SNR 22 dB)", _C_REFERENCE, ":"),
    ):
        ax.axhline(level, color=colour, lw=1.0, ls=style, label=_t(text, language))
    # Room above the 22 dB line for the legend, and below the 47 dB one.
    ax.set_ylim(
        min(float(np.min(result.noise_levels_db)), -47.0) - _NOISE_PAD_BELOW_DB,
        max(float(np.max(result.noise_levels_db)), -22.0) + _NOISE_PAD_ABOVE_DB,
    )
    ax.set_xticks(points)
    ax.set_xlabel(_t("Measurement point", language))
    ax.set_ylabel(_t("A-weighted noise level [dB re 400 mA/m]", language))
    ax.set_title(
        _t(
            "Reference SNR {snr} dB: {category}",
            language,
            snr=_num(result.reference_signal_to_noise_ratio_db, language),
            category=_t(result.category, language).replace("_", " "),
        )
    )
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_loop_requirement(
    result: LoopRequirement,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Each judged value of one requirement against its limits.

    :param result: A :class:`~phonometry.electroacoustics.induction_loop.LoopRequirement`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the values' ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    index = np.arange(1, len(result.values_db) + 1)
    values = np.asarray(result.values_db)
    ax.plot(
        index,
        values,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.0,
            marker="o",
            ms=4,
            label=_t("Measured", language),
        ),
    )
    lower = np.asarray(result.lower_db)
    upper = np.asarray(result.upper_db)
    if np.any(np.isfinite(lower)):
        ax.step(
            index,
            lower,
            where="mid",
            color=_C_REFERENCE,
            lw=1.0,
            ls="--",
            label=_t("Lower limit", language),
        )
    if np.any(np.isfinite(upper)):
        ax.step(
            index,
            upper,
            where="mid",
            color=_C_REFERENCE,
            lw=1.0,
            ls="-",
            label=_t("Upper limit", language),
        )
    failing = np.asarray([m < 0.0 for m in result.margins_db])
    if np.any(failing):
        ax.plot(
            index[failing],
            values[failing],
            ls="none",
            marker="x",
            ms=8,
            color=_C_REFERENCE,
        )
    ax.set_xlabel(_t("Judged value", language))
    ax.set_ylabel(_t("Value [dB]", language))
    ax.set_title(
        _t(
            "{name} ({clause}): {verdict}",
            language,
            name=_requirement_name(result.name, language),
            clause=result.clause,
            verdict=_verdict(passes=result.passes, language=language),
        )
    )
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_induction_loop_verification(
    result: InductionLoopVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The worst margin of every requirement, as bars.

    :param result: An :class:`~phonometry.electroacoustics.induction_loop.InductionLoopVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the bars' ``Axes.bar``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    margins = [r.worst_margin_db for r in result.requirements]
    colours = [_C_TERTIARY if r.passes else _C_REFERENCE for r in result.requirements]
    positions = np.arange(len(margins))
    style_default(kwargs, "label", _t("Margin", language))
    ax.bar(
        positions,
        margins,
        **styled(kwargs, color=colours, edgecolor=_C_EDGE, width=0.6, zorder=3),
    )
    ax.axhline(0.0, color=_C_EDGE, lw=1.0)
    ax.set_xticks(positions)
    ax.set_xticklabels(
        [
            _t(
                "{name}\n{clause}",
                language,
                name=_requirement_name(r.name, language),
                clause=r.clause,
            )
            for r in result.requirements
        ],
        fontsize=8,
    )
    ax.set_ylabel(_t("Worst margin [dB]", language))
    ax.set_title(
        _t(
            "IEC 60118-4, clause {clause}: {verdict}",
            language,
            clause=result.clause,
            verdict=_verdict(passes=result.passes, language=language),
        )
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_amplifier_overload(
    result: AmplifierOverloadVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The loop voltage along the overload sweep against the compliance voltage.

    :param result: An :class:`~phonometry.electroacoustics.induction_loop.AmplifierOverloadVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the voltage curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    ax.plot(
        result.frequencies_hz,
        result.voltage_v,
        **styled(kwargs, color=_C_PRIMARY, lw=1.6, label=_t("Loop voltage", language)),
    )
    ax.axhline(
        result.compliance_voltage_v,
        color=_C_REFERENCE,
        lw=1.0,
        ls="--",
        label=_t("Compliance voltage", language),
    )
    ax.axvline(
        result.programme.test_frequency_hz,
        color=_C_SECONDARY,
        lw=1.0,
        ls=":",
        label=_t("Table 4 frequency", language),
    )
    ax.plot(
        [result.programme.test_frequency_hz],
        [result.test_frequency_voltage_v],
        ls="none",
        marker="D",
        ms=6,
        color=_C_TERTIARY if result.passes else _C_REFERENCE,
        zorder=4,
        label=_t("Voltage judged by 10.3.3", language),
    )
    if math.isfinite(result.doubling_frequency_hz):
        ax.axvline(
            result.doubling_frequency_hz,
            color=_C_MUTED,
            lw=1.0,
            ls="-.",
            label=_t("Voltage doubled", language),
        )
    ax.set_xscale("log")
    # A margin either side, so the Table 4 frequency, where the sweep often
    # ends, is not drawn on the frame.
    lo = float(result.frequencies_hz[0]) / _SWEEP_MARGIN
    hi = float(result.frequencies_hz[-1]) * _SWEEP_MARGIN
    ax.set_xlim(lo, hi)
    format_frequency_axis(ax, lo, hi, language=language)
    ax.set_xlabel(_t(_FREQUENCY, language))
    ax.set_ylabel(_t("Loop voltage [V]", language))
    ax.set_title(
        _t(
            "Overload test, {freq} Hz programme limit",
            language,
            freq=_num(result.programme.power_bandwidth_limit_hz, language, 0),
        )
        + f": {_verdict(passes=result.passes, language=language)}"
    )
    ax.set_ylim(bottom=0.0)
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_maximum_output_current(
    result: MaximumOutputCurrent,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The distortion against the load current, with the rated THD and the maximum.

    :param result: A :class:`~phonometry.electroacoustics.induction_loop_components.MaximumOutputCurrent`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language.
    :param kwargs: Forwarded to the distortion curve's ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    ax.plot(
        result.load_current_a,
        result.thd_percent,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.6,
            marker="o",
            ms=3,
            label=_t("Distortion", language),
        ),
    )
    ax.axhline(
        result.rated_thd_percent,
        color=_C_REFERENCE,
        lw=1.0,
        ls="--",
        label=_t(
            "Rated THD {thd} %",
            language,
            thd=_num(result.rated_thd_percent, language),
        ),
    )
    ax.axvline(
        result.maximum_current_a,
        color=_C_SECONDARY,
        lw=1.0,
        ls=":",
        label=_t(
            "Maximum current {current} A",
            language,
            current=_num(result.maximum_current_a, language, 2),
        ),
    )
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel(_t("Load current [A]", language))
    ax.set_ylabel(_t("Total harmonic distortion [%]", language))
    ax.set_title(_t("Maximum output current (5.4.7)", language))
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax
