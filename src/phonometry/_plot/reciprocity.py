#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the reciprocity calibration of IEC 61094-2 and IEC
61094-3 (lazy imports from result ``.plot()``).
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes

    from ..metrology.reciprocity_calibration import (
        ReciprocityCalibration,
        ReciprocityUncertaintyBudget,
    )
    from ..metrology.reciprocity_coupler import (
        CapillaryTubeImpedance,
        CouplerCheck,
        CouplerParameterUncertainty,
        CouplerTransferImpedance,
        HeatConductionCorrection,
        WaveMotionCorrection,
    )
    from ..metrology.reciprocity_free_field import (
        AcousticCentre,
        FreeFieldArrangementCheck,
        FreeFieldParameterUncertainty,
        ReciprocityAirAttenuation,
    )

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _new_axes,
    format_frequency_axis,
    place_legend_clear,
    style_default,
    theme_fill,
)

_FREQUENCY_LABEL = "Frequency [Hz]"
_CORRECTION_LABEL = "Correction [dB]"
_UNCERTAINTY_LABEL = r"Standard uncertainty $u_i$ [dB]"
_MICROPHONE_LABEL = "Microphone {n}"
_VALUE_RE_LIMIT = "Value re its limit"
_CAPILLARY_TUBES = "Capillary tubes"
#: Table 1 of IEC 61094-2 prints "ground shield" where that of IEC 61094-3
#: prints "shield"; the legend gives both one short name.
_RECEIVER_SHIELD = "Receiver shield"
_TRANSMITTER_SHIELD = "Transmitter shield"
#: The capillary tube impedance of Formula (B.1) of IEC 61094-2, whose symbols
#: and unit read the same in Spanish.
_RE_CAPILLARY_LABEL = r"Re $Z_\mathrm{a,C}$"
_IM_CAPILLARY_LABEL = r"Im $Z_\mathrm{a,C}$"
_CAPILLARY_AXIS_LABEL = r"$Z_\mathrm{a,C}$ [GPa·s/m³]"
#: The attenuation of IEC 61094-3 B.2 and its classical and rotational part.
_ALPHA_TOTAL_LABEL = r"$\alpha$, total"
_ALPHA_CLASSICAL_LABEL = r"$\alpha_\mathrm{cl} + \alpha_\mathrm{rot}$"
#: The ordinate of the inverse-distance law of IEC 61094-3 6.5.
_INVERSE_PRESSURE_LABEL = r"$1/(|p|\,\mathrm{e}^{\alpha r})$ [1/Pa]"

#: The colour, line style and marker of microphones 1, 2 and 3.
_MICROPHONE_STYLES = (
    (_C_PRIMARY, "-", "o"),
    (_C_SECONDARY, "--", "s"),
    (_C_TERTIARY, "-.", "^"),
)

#: The colours the components of a budget cycle through.
_CYCLE = (_C_SECONDARY, _C_TERTIARY, _C_QUATERNARY, _C_MUTED, _C_REFERENCE)

_CALIBRATION_TITLES = MappingProxyType(
    {
        "pressure": "Pressure sensitivity by reciprocity (IEC 61094-2)",
        "free_field": "Free-field sensitivity by reciprocity (IEC 61094-3)",
    }
)
_BUDGET_TITLES = MappingProxyType(
    {
        "pressure": "Pressure reciprocity budget (IEC 61094-2 Table 1)",
        "free_field": "Free-field reciprocity budget (IEC 61094-3 Table 1)",
    }
)

_COUPLER_TITLES = MappingProxyType(
    {
        "plane_wave": r"Corrections to $Z_{\mathrm{a},12}$, plane-wave coupler (IEC 61094-2)",
        "large_volume": r"Corrections to $Z_{\mathrm{a},12}$, large-volume coupler (IEC 61094-2)",
    }
)
_PARAMETER_TITLES = MappingProxyType(
    {
        "pressure": r"Uncertainty from $Z_\mathrm{{a}}$, microphone {n} (IEC 61094-2 7.5)",
        "free_field": r"Uncertainty from $Z_\mathrm{{a}}$, microphone {n} (IEC 61094-3 7.8)",
    }
)
_ATTENUATION_TITLE = "Air attenuation (IEC 61094-3 Annex B): {t} °C, {p} kPa, {h} %"

#: The short tick and legend name of each component of Table 1 of both parts.
_COMPONENT_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "series_impedance": "Series impedance",
        "voltage_ratio": "Voltage ratio",
        "cross_talk": "Cross-talk",
        "noise": "Noise",
        "distortion": "Distortion",
        "frequency": "Frequency",
        "reflections": "Reflections",
        "receiver_ground_shield": _RECEIVER_SHIELD,
        "transmitter_ground_shield": _TRANSMITTER_SHIELD,
        "receiver_shield": _RECEIVER_SHIELD,
        "transmitter_shield": _TRANSMITTER_SHIELD,
        "coupler_length": "Coupler length",
        "coupler_diameter": "Coupler diameter",
        "coupler_volume": "Coupler volume",
        "coupler_surface_area": "Coupler surface area",
        "leakage": "Leakage",
        "capillary_tube_dimensions": _CAPILLARY_TUBES,
        "static_pressure": "Static pressure",
        "temperature": "Temperature",
        "relative_humidity": "Relative humidity",
        "distance": "Distance",
        "standing_waves": "Standing waves",
        "air_attenuation": "Air attenuation",
        "acoustic_centres": "Acoustic centres",
        "front_cavity_depth": "Front cavity depth",
        "front_cavity_volume": "Front cavity volume",
        "equivalent_volume": "Equivalent volume",
        "resonance_frequency": "Resonance frequency",
        "loss_factor": "Loss factor",
        "diaphragm_compliance": "Diaphragm compliance",
        "diaphragm_mass": "Diaphragm mass",
        "diaphragm_resistance": "Diaphragm resistance",
        "front_cavity_thread": "Front cavity thread",
        "polarizing_voltage": "Polarizing voltage",
        "heat_conduction_theory": "Heat conduction theory",
        "excess_volume": "Excess volume",
        "viscosity_losses": "Viscosity losses",
        "radial_wave_motion": "Radial wave motion",
        "plane_wave_deviation": "Deviation from plane waves",
        "mathematical_manipulations": "Mathematical manipulations",
        "rounding": "Rounding",
        "repeatability": "Repeatability",
        "static_pressure_corrections": "Static pressure corrections",
        "temperature_corrections": "Temperature corrections",
    }
)

#: Spanish translations of the fixed strings, keyed by their English text.
_STRINGS: Mapping[str, str] = MappingProxyType(
    {
        _FREQUENCY_LABEL: "Frecuencia [Hz]",
        _CORRECTION_LABEL: "Corrección [dB]",
        _UNCERTAINTY_LABEL: r"Incertidumbre típica $u_i$ [dB]",
        "Sensitivity level [dB re 1 V/Pa]": "Nivel de sensibilidad [dB re 1 V/Pa]",
        _MICROPHONE_LABEL: "Micrófono {n}",
        r"$\pm U$, expanded uncertainty, {low} dB to {high} dB": r"$\pm U$, incertidumbre expandida, de {low} dB a {high} dB",
        r"$\pm U$, expanded uncertainty, {low} dB": r"$\pm U$, incertidumbre expandida, {low} dB",
        _CALIBRATION_TITLES[
            "pressure"
        ]: "Sensibilidad en presión por reciprocidad (IEC 61094-2)",
        _CALIBRATION_TITLES[
            "free_field"
        ]: "Sensibilidad en campo libre por reciprocidad (IEC 61094-3)",
        _BUDGET_TITLES[
            "pressure"
        ]: "Balance de incertidumbre en presión (IEC 61094-2, tabla 1)",
        _BUDGET_TITLES[
            "free_field"
        ]: "Balance de incertidumbre en campo libre (IEC 61094-3, tabla 1)",
        r"Expanded uncertainty $U$ ($k$ = {k})": r"Incertidumbre expandida $U$ ($k$ = {k})",
        r"Combined standard uncertainty $u_\mathrm{c}$": r"Incertidumbre típica combinada $u_\mathrm{c}$",
        "Uncertainty [dB]": "Incertidumbre [dB]",
        r"$20\lg|\Delta_\mathrm{H}|$, apparent increase of the volume": r"$20\lg|\Delta_\mathrm{H}|$, aumento aparente del volumen",
        r"Heat conduction (IEC 61094-2 A.2): $R$ = {r}, $l$ = {l} mm": r"Conducción térmica (IEC 61094-2, A.2): $R$ = {r}, $l$ = {l} mm",
        _RE_CAPILLARY_LABEL: _RE_CAPILLARY_LABEL,
        _IM_CAPILLARY_LABEL: _IM_CAPILLARY_LABEL,
        _CAPILLARY_AXIS_LABEL: _CAPILLARY_AXIS_LABEL,
        r"Capillary tube (IEC 61094-2 Annex B): $l_\mathrm{{C}}$ = {l} mm, $a_\mathrm{{t}}$ = {a} mm": r"Tubo capilar (IEC 61094-2, anexo B): $l_\mathrm{{C}}$ = {l} mm, $a_\mathrm{{t}}$ = {a} mm",
        "Heat conduction": "Conducción térmica",
        _CAPILLARY_TUBES: "Tubos capilares",
        "Both": "Ambas",
        "Change of $|Z_{\\mathrm{a},12}|$ [dB]": "Cambio de $|Z_{\\mathrm{a},12}|$ [dB]",
        _COUPLER_TITLES[
            "plane_wave"
        ]: r"Correcciones de $Z_{\mathrm{a},12}$, acoplador de onda plana (IEC 61094-2)",
        _COUPLER_TITLES[
            "large_volume"
        ]: r"Correcciones de $Z_{\mathrm{a},12}$, acoplador de gran volumen (IEC 61094-2)",
        "Wave-motion correction": "Corrección por movimiento ondulatorio",
        "Rows of Table C.3": "Filas de la tabla C.3",
        "Large-volume coupler, LS1P microphones (IEC 61094-2 Table C.3)": "Acoplador de gran volumen, micrófonos LS1P (IEC 61094-2, tabla C.3)",
        _VALUE_RE_LIMIT: "Valor respecto a su límite",
        "Limit": "Límite",
        r"$\omega\rho a^2/(100\eta)$ at the lowest frequency (A.3)": r"$\omega\rho a^2/(100\eta)$ a la frecuencia más baja (A.3)",
        r"$X/5$ at the lowest frequency (A.2)": r"$X/5$ a la frecuencia más baja (A.2)",
        r"$f_\mathrm{min}/(20$ Hz$)$, advisory (A.2)": r"$f_\mathrm{min}/(20$ Hz$)$, orientativo (A.2)",
        r"$R/0.5$, recommended at least 1 (C.2)": r"$R/0{,}5$, recomendado al menos 1 (C.2)",
        r"$0.75/R$, recommended at least 1 (C.2)": r"$0{,}75/R$, recomendado al menos 1 (C.2)",
        "Coupler check (IEC 61094-2): {verdict}": "Comprobación del acoplador (IEC 61094-2): {verdict}",
        "the formulas hold": "las fórmulas son válidas",
        "the formulas do not hold": "las fórmulas no son válidas",
        _PARAMETER_TITLES[
            "pressure"
        ]: r"Incertidumbre debida a $Z_\mathrm{{a}}$, micrófono {n} (IEC 61094-2, 7.5)",
        _PARAMETER_TITLES[
            "free_field"
        ]: r"Incertidumbre debida a $Z_\mathrm{{a}}$, micrófono {n} (IEC 61094-3, 7.8)",
        _ALPHA_TOTAL_LABEL: _ALPHA_TOTAL_LABEL,
        _ALPHA_CLASSICAL_LABEL: _ALPHA_CLASSICAL_LABEL,
        r"$\alpha_\mathrm{vib,O}$, oxygen": r"$\alpha_\mathrm{vib,O}$, oxígeno",
        r"$\alpha_\mathrm{vib,N}$, nitrogen": r"$\alpha_\mathrm{vib,N}$, nitrógeno",
        "Attenuation [dB/m]": "Atenuación [dB/m]",
        _ATTENUATION_TITLE: "Atenuación en el aire (IEC 61094-3, anexo B): {t} °C, {p} kPa, {h} %",
        "Inverse of the pressure corrected for attenuation": "Inversa de la presión corregida por la atenuación",
        "Least-squares line": "Recta de mínimos cuadrados",
        "Acoustic centre, {x} mm": "Centro acústico, {x} mm",
        "Distance from the reference point [m]": "Distancia al punto de referencia [m]",
        _INVERSE_PRESSURE_LABEL: _INVERSE_PRESSURE_LABEL,
        "Acoustic centre from the inverse-distance law (IEC 61094-3 6.5)": "Centro acústico por la ley $1/r$ (IEC 61094-3, apartado 6.5)",
        "Distance between the diaphragms": "Distancia entre los diafragmas",
        "Supporting cylinder": "Cilindro de soporte",
        "Ten nominal diameters (7.3)": "Diez diámetros nominales (apartado 7.3)",
        "Twenty diameters (6.4)": "Veinte diámetros (apartado 6.4)",
        "Distance or length [m]": "Distancia o longitud [m]",
        "Support": "Soporte",
        "distance under ten diameters": "distancia inferior a diez diámetros",
        "support under twenty diameters": "soporte inferior a veinte diámetros",
        "conditions outside the B.2 accuracy domain": "condiciones fuera del dominio de exactitud de B.2",
        "Annex A range, 150 mm to 500 mm": "Intervalo del anexo A, de 150 mm a 500 mm",
        "Distance [m]": "Distancia [m]",
        "Pair {pair}": "Par {pair}",
        "Free-field arrangement (IEC 61094-3): {verdict}": "Disposición en campo libre (IEC 61094-3): {verdict}",
        "as recommended": "conforme a lo recomendado",
        "not as recommended": "no conforme a lo recomendado",
        "Series impedance": "Impedancia en serie",
        "Voltage ratio": "Relación de tensiones",
        "Cross-talk": "Diafonía",
        "Noise": "Ruido",
        "Distortion": "Distorsión",
        "Frequency": "Frecuencia",
        "Reflections": "Reflexiones",
        _RECEIVER_SHIELD: "Blindaje del receptor",
        _TRANSMITTER_SHIELD: "Blindaje del emisor",
        "Coupler length": "Longitud del acoplador",
        "Coupler diameter": "Diámetro del acoplador",
        "Coupler volume": "Volumen del acoplador",
        "Coupler surface area": "Superficie del acoplador",
        "Leakage": "Fugas",
        "Static pressure": "Presión estática",
        "Temperature": "Temperatura",
        "Relative humidity": "Humedad relativa",
        "Distance": "Distancia",
        "Standing waves": "Ondas estacionarias",
        "Air attenuation": "Atenuación del aire",
        "Acoustic centres": "Centros acústicos",
        "Front cavity depth": "Profundidad de la cavidad frontal",
        "Front cavity volume": "Volumen de la cavidad frontal",
        "Equivalent volume": "Volumen equivalente",
        "Resonance frequency": "Frecuencia de resonancia",
        "Loss factor": "Factor de pérdidas",
        "Diaphragm compliance": "Compliancia del diafragma",
        "Diaphragm mass": "Masa del diafragma",
        "Diaphragm resistance": "Resistencia del diafragma",
        "Front cavity thread": "Rosca de la cavidad frontal",
        "Polarizing voltage": "Tensión de polarización",
        "Heat conduction theory": "Teoría de la conducción térmica",
        "Excess volume": "Volumen en exceso",
        "Viscosity losses": "Pérdidas por viscosidad",
        "Radial wave motion": "Movimiento ondulatorio radial",
        "Deviation from plane waves": "Desviación de las ondas planas",
        "Mathematical manipulations": "Manipulaciones matemáticas",
        "Rounding": "Redondeo",
        "Repeatability": "Repetibilidad",
        "Static pressure corrections": "Correcciones de presión estática",
        "Temperature corrections": "Correcciones de temperatura",
    }
)


def _t(text: str, language: str = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


def _component_label(name: str, language: str) -> str:
    """The legend name of a component: its short name, or its own name."""
    label = _COMPONENT_LABELS.get(name)
    return name if label is None else _t(label, language)


def _frequency_axes(ax: Axes, language: str, ylabel: str, title: str) -> None:
    """The common dressing of a frequency plot."""
    from .._i18n import localize_axes

    ax.set_xscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t(_FREQUENCY_LABEL, language))
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)


def _band_label(uncertainty: np.ndarray, language: str) -> str:
    """The legend entry of the uncertainty band, with the range of U.

    A band of a few hundredths of a decibel is narrower than the curves on an
    axis of several decibels, so the entry says how wide it is.
    """
    from .._i18n import format_number

    low = format_number(float(np.min(uncertainty)), language, decimals=3)
    high = format_number(float(np.max(uncertainty)), language, decimals=3)
    if low == high:
        return _t(r"$\pm U$, expanded uncertainty, {low} dB", language, low=low)
    return _t(
        r"$\pm U$, expanded uncertainty, {low} dB to {high} dB",
        language,
        low=low,
        high=high,
    )


def plot_reciprocity_calibration(
    result: ReciprocityCalibration,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The sensitivity level of each microphone of a reciprocity calibration.

    :param result: A
        :class:`~phonometry.metrology.reciprocity_calibration.ReciprocityCalibration`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the curve of microphone 1.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    frequencies = np.asarray(result.frequencies_hz, dtype=np.float64)
    levels = np.asarray(result.sensitivity_level_db, dtype=np.float64)
    band_label = None
    if result.expanded_uncertainty_db is not None:
        band_label = _band_label(
            np.asarray(result.expanded_uncertainty_db, dtype=np.float64), language
        )
    first_colour, first_style, first_marker = _MICROPHONE_STYLES[0]
    style_default(kwargs, "color", first_colour)
    style_default(kwargs, "lw", 1.6)
    style_default(kwargs, "ls", first_style)
    style_default(kwargs, "marker", first_marker)
    style_default(kwargs, "ms", 3.5)
    kwargs.setdefault("label", _t(_MICROPHONE_LABEL, language, n=1))
    for index, level in enumerate(levels):
        colour, style, marker = _MICROPHONE_STYLES[index]
        number = index + 1
        if result.expanded_uncertainty_db is not None:
            uncertainty = np.asarray(result.expanded_uncertainty_db, dtype=np.float64)
            ax.fill_between(
                frequencies,
                level - uncertainty,
                level + uncertainty,
                color=theme_fill(colour, ax),
                lw=0.0,
                label=band_label if index == 0 else None,
            )
        if index == 0:
            ax.plot(frequencies, level, **kwargs)
        else:
            ax.plot(
                frequencies,
                level,
                color=colour,
                lw=1.2,
                ls=style,
                marker=marker,
                ms=3.5,
                mfc="none",
                label=_t(_MICROPHONE_LABEL, language, n=number),
            )
    _frequency_axes(
        ax,
        language,
        _t("Sensitivity level [dB re 1 V/Pa]", language),
        _t(_CALIBRATION_TITLES[result.field], language),
    )
    return ax


def plot_reciprocity_budget(
    result: ReciprocityUncertaintyBudget,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The components of a reciprocity budget and its expanded uncertainty
    against frequency.

    :param result: A
        :class:`~phonometry.metrology.reciprocity_calibration.ReciprocityUncertaintyBudget`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the expanded-uncertainty curve.
    :return: The axes.
    """
    from .._i18n import format_number

    ax = ax if ax is not None else _new_axes()
    frequencies = np.asarray(result.frequencies_hz, dtype=np.float64)
    for index, (name, values) in enumerate(
        zip(result.names, result.standard_uncertainties_db, strict=True)
    ):
        ax.plot(
            frequencies,
            values,
            color=_CYCLE[index % len(_CYCLE)],
            lw=0.9,
            ls=("-", "--", "-.", ":")[index // len(_CYCLE) % 4],
            label=_component_label(name, language),
        )
    ax.plot(
        frequencies,
        result.combined_uncertainty_db,
        color=_C_PRIMARY,
        lw=1.2,
        ls="--",
        label=_t(r"Combined standard uncertainty $u_\mathrm{c}$", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.8)
    kwargs.setdefault(
        "label",
        _t(
            r"Expanded uncertainty $U$ ($k$ = {k})",
            language,
            k=format_number(result.coverage_factor, language, decimals=0),
        ),
    )
    ax.plot(frequencies, result.expanded_uncertainty_db, **kwargs)
    ax.set_ylim(bottom=0.0)
    _frequency_axes(
        ax,
        language,
        _t("Uncertainty [dB]", language),
        _t(_BUDGET_TITLES[result.field], language),
    )
    return ax


def plot_heat_conduction_correction(
    result: HeatConductionCorrection,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r""":math:`20\lg|\Delta_\mathrm{H}|` against frequency.

    :param result: A
        :class:`~phonometry.metrology.reciprocity_coupler.HeatConductionCorrection`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the curve.
    :return: The axes.
    """
    from .._i18n import format_number

    ax = ax if ax is not None else _new_axes()
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    kwargs.setdefault(
        "label",
        _t(r"$20\lg|\Delta_\mathrm{H}|$, apparent increase of the volume", language),
    )
    ax.plot(result.frequencies_hz, result.correction_db, **kwargs)
    ax.set_ylim(bottom=0.0)
    _frequency_axes(
        ax,
        language,
        _t(_CORRECTION_LABEL, language),
        _t(
            r"Heat conduction (IEC 61094-2 A.2): $R$ = {r}, $l$ = {l} mm",
            language,
            r=format_number(result.length_to_diameter_ratio, language, decimals=3),
            l=format_number(1000.0 * result.volume_to_surface_m, language, decimals=3),
        ),
    )
    return ax


def plot_capillary_tube_impedance(
    result: CapillaryTubeImpedance,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The real and imaginary parts of the input impedance of a capillary tube,
    in GPa·s/m³.

    :param result: A
        :class:`~phonometry.metrology.reciprocity_coupler.CapillaryTubeImpedance`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the real-part curve.
    :return: The axes.
    """
    from .._i18n import format_number

    ax = ax if ax is not None else _new_axes()
    impedance = np.asarray(result.impedance_pa_s_m3) / 1e9
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    kwargs.setdefault("label", _t(_RE_CAPILLARY_LABEL, language))
    ax.plot(result.frequencies_hz, impedance.real, **kwargs)
    ax.plot(
        result.frequencies_hz,
        impedance.imag,
        color=_C_SECONDARY,
        lw=1.2,
        ls="--",
        label=_t(_IM_CAPILLARY_LABEL, language),
    )
    _frequency_axes(
        ax,
        language,
        _t(_CAPILLARY_AXIS_LABEL, language),
        _t(
            r"Capillary tube (IEC 61094-2 Annex B): $l_\mathrm{{C}}$ = {l} mm, $a_\mathrm{{t}}$ = {a} mm",
            language,
            l=format_number(1000.0 * result.length_m, language, decimals=1),
            a=format_number(1000.0 * result.radius_m, language, decimals=4),
        ),
    )
    return ax


def plot_coupler_transfer_impedance(
    result: CouplerTransferImpedance,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The heat-conduction and capillary corrections of a coupler, in dB.

    :param result: A
        :class:`~phonometry.metrology.reciprocity_coupler.CouplerTransferImpedance`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the heat-conduction curve.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    frequencies = result.frequencies_hz
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 3.0)
    kwargs.setdefault("label", _t("Heat conduction", language))
    ax.plot(frequencies, result.heat_conduction_correction_db, **kwargs)
    ax.plot(
        frequencies,
        result.capillary_correction_db,
        color=_C_SECONDARY,
        lw=1.2,
        ls="--",
        marker="s",
        ms=3.0,
        mfc="none",
        label=_t(_CAPILLARY_TUBES, language),
    )
    ax.plot(
        frequencies,
        result.heat_conduction_correction_db + result.capillary_correction_db,
        color=_C_TERTIARY,
        lw=1.0,
        ls=":",
        label=_t("Both", language),
    )
    _frequency_axes(
        ax,
        language,
        _t("Change of $|Z_{\\mathrm{a},12}|$ [dB]", language),
        _t(_COUPLER_TITLES[result.coupler], language),
    )
    return ax


def plot_wave_motion_correction(
    result: WaveMotionCorrection,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The wave-motion correction of the large-volume coupler, with the rows of
    Table C.3.

    :param result: A
        :class:`~phonometry.metrology.reciprocity_coupler.WaveMotionCorrection`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the correction curve.
    :return: The axes.
    """
    from ..metrology.reciprocity_coupler import IEC61094_2_TABLE_C3

    ax = ax if ax is not None else _new_axes()
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    kwargs.setdefault("label", _t("Wave-motion correction", language))
    ax.plot(result.frequencies_hz, result.correction_db, **kwargs)
    printed = np.array(sorted(IEC61094_2_TABLE_C3), dtype=np.float64)
    ax.plot(
        printed * result.speed_of_sound_ratio,
        [IEC61094_2_TABLE_C3[f] for f in printed],
        color=_C_REFERENCE,
        ls="none",
        marker="s",
        ms=5.0,
        mfc="none",
        label=_t("Rows of Table C.3", language),
    )
    _frequency_axes(
        ax,
        language,
        _t(_CORRECTION_LABEL, language),
        _t("Large-volume coupler, LS1P microphones (IEC 61094-2 Table C.3)", language),
    )
    return ax


def _margin_bars(
    ax: Axes,
    labels: list[str],
    values: list[float],
    language: str,
    kwargs: dict[str, Any],
) -> None:
    """Horizontal bars of value re limit, with the limit at 1."""
    import matplotlib.ticker as mticker

    from .._i18n import decimal_comma, localize_axes

    positions = np.arange(len(values))
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t(_VALUE_RE_LIMIT, language))
    ax.barh(positions, values, **kwargs)
    ax.axvline(1.0, color=_C_REFERENCE, ls="--", lw=1.2, label=_t("Limit", language))
    ax.set_yticks(positions)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xscale("log")
    # The margins sit within a decade or two of 1, which the default log axis
    # labels 10^0 and 2 x 10^0; written plainly they read as the ratios they are.
    for axis_formatter in (ax.xaxis.set_major_formatter, ax.xaxis.set_minor_formatter):
        axis_formatter(
            mticker.FuncFormatter(
                lambda value, _pos: decimal_comma(f"{value:g}", language)
            )
        )
    ax.xaxis.set_minor_locator(mticker.LogLocator(base=10.0, subs=(2.0, 5.0)))
    ax.set_xlabel(_t(_VALUE_RE_LIMIT, language))
    ax.grid(visible=True, axis="x", which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)


def plot_coupler_check(
    result: CouplerCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Each condition of a coupler check as its value re its limit.

    :param result: A :class:`~phonometry.metrology.reciprocity_coupler.CouplerCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.barh`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    labels: list[str] = []
    values: list[float] = []
    if result.broadband_margin is not None:
        labels.append(
            _t(r"$\omega\rho a^2/(100\eta)$ at the lowest frequency (A.3)", language)
        )
        values.append(result.broadband_margin)
    if result.approximation_valid is not None and result.lowest_x is not None:
        # X > 5 binds Formula (A.2) only; the full solution has no such limit.
        labels.append(_t(r"$X/5$ at the lowest frequency (A.2)", language))
        values.append(result.lowest_x / 5.0)
    if result.full_solution_advised is not None:
        labels.append(_t(r"$f_\mathrm{min}/(20$ Hz$)$, advisory (A.2)", language))
        values.append(result.lowest_frequency_hz / 20.0)
    if result.ratio_recommended is not None:
        ratio = result.length_to_diameter_ratio
        labels.append(_t(r"$R/0.5$, recommended at least 1 (C.2)", language))
        values.append(ratio / 0.5)
        labels.append(_t(r"$0.75/R$, recommended at least 1 (C.2)", language))
        values.append(0.75 / ratio)
    _margin_bars(ax, labels, values, language, kwargs)
    verdict = "the formulas hold" if result.passes else "the formulas do not hold"
    ax.set_title(
        _t(
            "Coupler check (IEC 61094-2): {verdict}",
            language,
            verdict=_t(verdict, language),
        )
    )
    return ax


def plot_parameter_uncertainty(
    result: CouplerParameterUncertainty | FreeFieldParameterUncertainty,
    ax: Axes | None = None,
    *,
    language: str = "en",
    field: str = "pressure",
    **kwargs: Any,
) -> Axes:
    """Each uncertainty component of the acoustic transfer impedance against
    frequency.

    :param result: A
        :class:`~phonometry.metrology.reciprocity_coupler.CouplerParameterUncertainty`
        or
        :class:`~phonometry.metrology.reciprocity_free_field.FreeFieldParameterUncertainty`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param field: ``"pressure"`` or ``"free_field"``, for the title.
    :param kwargs: Forwarded to the first component's curve.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    frequencies = result.frequencies_hz
    names = list(result.components_db)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    if names:
        kwargs.setdefault("label", _component_label(names[0], language))
    for index, (name, values) in enumerate(result.components_db.items()):
        colour = (_C_PRIMARY, *_CYCLE)[index % (len(_CYCLE) + 1)]
        style = ("-", "--", "-.", ":")[index // (len(_CYCLE) + 1) % 4]
        if index == 0:
            ax.plot(frequencies, values, **kwargs)
        else:
            ax.plot(
                frequencies,
                values,
                color=colour,
                lw=1.1,
                ls=style,
                label=_component_label(name, language),
            )
    ax.set_ylim(bottom=0.0)
    _frequency_axes(
        ax,
        language,
        _t(_UNCERTAINTY_LABEL, language),
        _t(_PARAMETER_TITLES[field], language, n=result.microphone),
    )
    return ax


def plot_air_attenuation(
    result: ReciprocityAirAttenuation,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The attenuation of sound in air and its three parts, in dB/m.

    :param result: A
        :class:`~phonometry.metrology.reciprocity_free_field.ReciprocityAirAttenuation`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the total-attenuation curve.
    :return: The axes.
    """
    from .._i18n import format_number

    ax = ax if ax is not None else _new_axes()
    frequencies = result.frequencies_hz
    to_db = result.attenuation_db_per_m / result.attenuation_np_per_m
    for values, colour, style, label in (
        (
            result.classical_np_per_m,
            _C_SECONDARY,
            "--",
            _ALPHA_CLASSICAL_LABEL,
        ),
        (result.oxygen_np_per_m, _C_TERTIARY, "-.", r"$\alpha_\mathrm{vib,O}$, oxygen"),
        (
            result.nitrogen_np_per_m,
            _C_QUATERNARY,
            ":",
            r"$\alpha_\mathrm{vib,N}$, nitrogen",
        ),
    ):
        ax.plot(
            frequencies,
            values * to_db,
            color=colour,
            lw=1.1,
            ls=style,
            label=_t(label, language),
        )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.7)
    kwargs.setdefault("label", _t(_ALPHA_TOTAL_LABEL, language))
    ax.plot(frequencies, result.attenuation_db_per_m, **kwargs)
    ax.set_yscale("log")
    _frequency_axes(
        ax,
        language,
        _t("Attenuation [dB/m]", language),
        _t(
            _ATTENUATION_TITLE,
            language,
            t=format_number(result.temperature_c, language, decimals=1),
            p=format_number(result.static_pressure_pa / 1000.0, language, decimals=1),
            h=format_number(result.relative_humidity_percent, language, decimals=0),
        ),
    )
    return ax


def plot_acoustic_centre(
    result: AcousticCentre,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The inverse of the measured pressure against distance, the fitted line
    and the acoustic centre where it crosses the axis.

    :param result: An
        :class:`~phonometry.metrology.reciprocity_free_field.AcousticCentre`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the fitted line.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    distances = result.distances_m
    position = result.position_m
    span = np.linspace(min(position, 0.0), float(distances.max()) * 1.05, 50)
    ax.plot(
        distances,
        result.inverse_readings,
        color=_C_SECONDARY,
        ls="none",
        marker="o",
        ms=5.0,
        label=_t("Inverse of the pressure corrected for attenuation", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.4)
    kwargs.setdefault("label", _t("Least-squares line", language))
    ax.plot(span, result.slope * span + result.intercept, **kwargs)
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.plot(
        [position],
        [0.0],
        color=_C_REFERENCE,
        ls="none",
        marker="D",
        ms=6.0,
        label=_t(
            "Acoustic centre, {x} mm",
            language,
            x=format_number(1000.0 * position, language, decimals=1),
        ),
    )
    ax.set_xlabel(_t("Distance from the reference point [m]", language))
    ax.set_ylabel(_t(_INVERSE_PRESSURE_LABEL, language))
    ax.set_title(
        _t("Acoustic centre from the inverse-distance law (IEC 61094-3 6.5)", language)
    )
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_free_field_arrangement(
    result: FreeFieldArrangementCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Every condition of a free-field arrangement check: each distance against
    ten nominal diameters and the range of Annex A, the supporting cylinder
    against twenty diameters when its length is known, and the conditions that
    fail named in the title.

    :param result: A
        :class:`~phonometry.metrology.reciprocity_free_field.FreeFieldArrangementCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.barh` of the
        distances.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    distances = np.asarray(result.diaphragm_distances_m, dtype=np.float64)
    positions = np.arange(distances.size, dtype=np.float64)
    diameter = result.microphone_diameter_m
    ax.axvspan(
        0.150,
        0.500,
        color=theme_fill(_C_TERTIARY, ax),
        lw=0.0,
        label=_t("Annex A range, 150 mm to 500 mm", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Distance between the diaphragms", language))
    ax.barh(positions, distances, height=0.5, **kwargs)
    # Each limit is drawn across the rows it applies to only.
    ax.vlines(
        10.0 * diameter,
        positions[0] - 0.4,
        positions[-1] + 0.4,
        color=_C_REFERENCE,
        ls="--",
        lw=1.2,
        label=_t("Ten nominal diameters (7.3)", language),
    )
    pairs = ("12", "23", "31")
    labels = [
        _t(
            "Pair {pair}",
            language,
            pair=pairs[index] if distances.size == len(pairs) else str(index + 1),
        )
        for index in range(distances.size)
    ]
    ticks: list[float] = [float(p) for p in positions]
    longest = float(distances.max())
    if result.support_length_m is not None:
        row = float(distances.size)
        ax.barh(
            [row],
            [result.support_length_m],
            height=0.5,
            color=_C_SECONDARY,
            label=_t("Supporting cylinder", language),
        )
        ax.vlines(
            20.0 * diameter,
            row - 0.4,
            row + 0.4,
            color=_C_QUATERNARY,
            ls=":",
            lw=1.6,
            label=_t("Twenty diameters (6.4)", language),
        )
        ticks.append(row)
        labels.append(_t("Support", language))
        longest = max(longest, result.support_length_m, 20.0 * diameter)
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(0.0, max(0.55, 1.1 * longest))
    ax.set_xlabel(_t("Distance or length [m]", language))
    ax.set_title(_arrangement_title(result, language))
    ax.grid(visible=True, axis="x", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def _arrangement_title(result: FreeFieldArrangementCheck, language: str) -> str:
    """The verdict, and on a second line the conditions that fail it."""
    verdict = "as recommended" if result.passes else "not as recommended"
    title = _t(
        "Free-field arrangement (IEC 61094-3): {verdict}",
        language,
        verdict=_t(verdict, language),
    )
    failing = [
        _t(reason, language)
        for reason, failed in (
            ("distance under ten diameters", not result.distances_ok),
            ("support under twenty diameters", result.support_ok is False),
            (
                "conditions outside the B.2 accuracy domain",
                not result.attenuation_accuracy,
            ),
        )
        if failed
    ]
    return title if not failing else title + "\n" + "; ".join(failing)
