#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the underwater domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _LEGEND_UPPER_RIGHT,
    _new_axes,
    _new_axes_column,
    format_frequency_axis,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..underwater.numerical_propagation import (
        NormalModeResult,
        ParabolicEquationResult,
        RayTraceResult,
    )
    from ..underwater.ocean_ambient_noise import AmbientNoiseResult
    from ..underwater.pile_driving_noise import PileStrikeResult
    from ..underwater.propagation import TransmissionLossResult
    from ..underwater.seabed_reflection import BottomLossResult, SeabedReflection
    from ..underwater.ship_radiated_noise import ShipSourceLevelResult
    from ..underwater.ship_traffic_noise import ShipTrafficSpectrum
    from ..underwater.sonar_equation import SonarEquationResult
    from ..underwater.sound_speed import SoundSpeedProfile

#: Spanish translations of the fixed strings rendered by the underwater
#: ``.plot()`` renderers, keyed by their verbatim English text.  ``_t``
#: returns the English key unchanged for any language other than ``"es"``,
#: so the English output is byte-for-byte identical to the pre-i18n
#: renderers.
_STRINGS: dict[str, str] = {
    "Source level Ls": "Nivel de fuente Ls",
    "Radiated noise level": "Nivel de ruido radiado",
    "Frequency [Hz]": "Frecuencia [Hz]",
    "Level [dB re 1 µPa·m]": "Nivel [dB re 1 µPa·m]",
    "Surface correction ΔL": "Corrección de superficie ΔL",
    "Surface correction ΔL [dB]": "Corrección de superficie ΔL [dB]",
    "ISO 17208-2 equivalent monopole source level": "Nivel de fuente monopolar equivalente ISO 17208-2",
    "Peak": "Pico",
    "Pressure [Pa]": "Presión [Pa]",
    "Time [s]": "Tiempo [s]",
    "ISO 18406 pile strike": "Golpe de pilote ISO 18406",
    "Cumulative energy": "Energía acumulada",
    "Cumulative energy (norm.)": "Energía acumulada (norm.)",
    "90 % pulse duration": "Duración del pulso al 90 %",
    "Sound speed [m/s]": "Velocidad del sonido [m/s]",
    "Depth [m]": "Profundidad [m]",
    "Sea-water sound-speed profile": "Perfil de velocidad del sonido en agua de mar",
    "Total TL": "TL total",
    "Spreading": "Divergencia",
    "Absorption": "Absorción",
    "Range [m]": "Distancia [m]",
    "Transmission loss [dB]": "Pérdida por transmisión [dB]",
    "Underwater transmission loss": "Pérdida por transmisión submarina",
    "Signal excess": "Exceso de señal",
    "Detection limit (SE = 0)": "Límite de detección (SE = 0)",
    "Figure of merit": "Cifra de mérito",
    "Signal excess [dB]": "Exceso de señal [dB]",
    "Sonar equation": "Ecuación del sonar",
    "Bottom loss": "Pérdida en el fondo",
    "Critical angle": "Ángulo crítico",
    "Grazing angle [°]": "Ángulo rasante [°]",
    "Bottom loss [dB]": "Pérdida en el fondo [dB]",
    "Seabed reflection loss": "Pérdida por reflexión en el fondo marino",
    "Reflection coefficient magnitude": "Módulo del coeficiente de reflexión",
    "Seabed reflection coefficient": "Coeficiente de reflexión del fondo marino",
    "Total": "Total",
    "Wind": "Viento",
    "Thermal": "Térmico",
    "Shipping": "Tráfico marítimo",
    "Spectrum level [dB re 1 µPa²/Hz]": "Nivel espectral [dB re 1 µPa²/Hz]",
    "Ocean ambient noise": "Ruido ambiental oceánico",
    "Source spectral density [dB re 1 µPa²/Hz at 1 m]": "Densidad espectral de la fuente [dB re 1 µPa²/Hz a 1 m]",
    "Ship traffic source level": "Nivel de fuente del tráfico marítimo",
    "modes": "modos",
    "Range [km]": "Distancia [km]",
    "Normal-mode transmission loss": "Pérdida por transmisión por modos normales",
    "Source": "Fuente",
    "Ray trace": "Trazado de rayos",
    "Parabolic-equation transmission loss": "Pérdida por transmisión por ecuación parabólica",
}


def _t(text: str, language: str = "en") -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    return _STRINGS.get(text, text) if language == "es" else text


def plot_ship_source_level(
    result: ShipSourceLevelResult, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Radiated noise level, source level and the ΔL surface correction.

    Draws the input RNL and the equivalent monopole source level ``Ls`` versus
    frequency, with the Lloyd's-mirror correction ``ΔL`` on a twin axis.

    :param result: A
        :class:`~phonometry.ship_radiated_noise.ShipSourceLevelResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the source-level ``semilogx`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    rnl = np.asarray(result.radiated_noise_level, dtype=np.float64)
    ls = np.asarray(result.source_level, dtype=np.float64)
    dl = np.asarray(result.surface_correction, dtype=np.float64)

    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Source level Ls", language))
    ax.semilogx(freqs, ls, "o-", **kwargs)
    ax.semilogx(freqs, rnl, "s--", color=_C_REFERENCE, label=_t("Radiated noise level", language))
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("Level [dB re 1 µPa·m]", language))
    ax.grid(True, which="both", alpha=0.3)
    ax.set_axisbelow(True)

    twin = ax.twinx()
    twin.semilogx(freqs, dl, ":", color=_C_TERTIARY, label=_t("Surface correction ΔL", language))
    twin.set_ylabel(_t("Surface correction ΔL [dB]", language))
    # After twinx() (it re-initialises the shared x-axis with the default log
    # locator) so the octave-band labelling is not reset back to 10^n ticks.
    format_frequency_axis(ax, float(freqs.min()), float(freqs.max()))

    lines, labels = ax.get_legend_handles_labels()
    tlines, tlabels = twin.get_legend_handles_labels()
    ax.legend(lines + tlines, labels + tlabels, loc="best", fontsize="small")
    ax.set_title(
        f"{_t('ISO 17208-2 equivalent monopole source level', language)} "
        f"(d_s = {format_number(result.source_depth, language)} m, "
        f"c = {format_number(result.sound_speed, language, decimals=0)} m/s)"
    )
    localize_axes(ax, language)
    return ax

def plot_pile_strike(
    result: PileStrikeResult, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes | np.ndarray:
    """Pile-strike pressure waveform and its cumulative energy.

    Two stacked panels: the pressure waveform with the peak marked on top, and
    the normalised cumulative energy with the 5 %/95 % pulse-duration bounds
    below. With ``ax`` given, only the waveform panel is drawn on it.

    :param result: A :class:`~phonometry.pile_driving_noise.PileStrikeResult`.
    :param ax: Existing axes for the waveform panel, or ``None`` for a fresh
        two-panel figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the waveform ``plot`` call.
    :return: The waveform axes (``ax`` given) or the array of two axes.
    """
    from .._i18n import format_number, localize_axes

    pressure = np.asarray(result.pressure, dtype=np.float64)
    fs = float(result.fs)
    t = np.arange(pressure.size) / fs
    energy = np.cumsum(pressure**2)
    total = float(energy[-1]) if energy.size else 0.0
    cum = energy / total if total > 0.0 else energy
    peak_idx = int(np.argmax(np.abs(pressure)))
    color = kwargs.pop("color", _C_PRIMARY)

    def _waveform(axw: Axes) -> None:
        axw.plot(t, pressure, color=color, lw=0.8, **kwargs)
        axw.plot([t[peak_idx]], [pressure[peak_idx]], "o", color=_C_REFERENCE,
                 label=f"{_t('Peak', language)} ({format_number(result.peak_spl, language, decimals=0)} dB re 1 µPa)")
        axw.set_ylabel(_t("Pressure [Pa]", language))
        axw.grid(True, alpha=0.3)
        axw.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _waveform(ax)
        ax.set_xlabel(_t("Time [s]", language))
        ax.set_title(f"{_t('ISO 18406 pile strike', language)} (SEL_ss = {format_number(result.single_strike_sel, language, decimals=0)} dB)")
        localize_axes(ax, language)
        return ax

    axes = _new_axes_column(2, sharex=True, figsize=(8.0, 6.0))
    _waveform(axes[0])
    axes[0].set_title(
        f"{_t('ISO 18406 pile strike', language)} (SEL_ss = {format_number(result.single_strike_sel, language, decimals=0)} dB re 1 µPa²·s)"
    )
    axes[1].plot(t, cum, color=_C_TERTIARY, label=_t("Cumulative energy", language))
    for frac in (0.05, 0.95):
        axes[1].axhline(frac, color=_C_MUTED, ls="--", lw=0.8)
    axes[1].set_ylabel(_t("Cumulative energy (norm.)", language))
    axes[1].set_xlabel(_t("Time [s]", language))
    axes[1].set_title(f"{_t('90 % pulse duration', language)} = {format_number(result.pulse_duration * 1e3, language, decimals=0)} ms")
    axes[1].grid(True, alpha=0.3)
    localize_axes(axes[0], language)
    localize_axes(axes[1], language)
    return axes

def plot_sound_speed_profile(
    result: SoundSpeedProfile, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Sound-speed profile: speed vs depth, with depth increasing downward.

    :param result: A :class:`~phonometry.underwater_sound_speed.SoundSpeedProfile`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the profile ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    depth = np.asarray(result.depth, dtype=np.float64)
    speed = np.asarray(result.sound_speed, dtype=np.float64)
    label = f"{result.model} c(z)"
    ax.plot(speed, depth, **{"color": _C_PRIMARY, "lw": 1.4, "label": label, **kwargs})
    if not ax.yaxis_inverted():
        ax.invert_yaxis()
    ax.set_xlabel(_t("Sound speed [m/s]", language))
    ax.set_ylabel(_t("Depth [m]", language))
    ax.set_title(_t("Sea-water sound-speed profile", language))
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower left", fontsize="small")
    localize_axes(ax, language)
    return ax

def plot_transmission_loss(
    result: TransmissionLossResult, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Transmission loss versus range, with spreading and absorption split out.

    Loss increases downward (the usual TL convention).

    :param result: A :class:`~phonometry.underwater_propagation.TransmissionLossResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the total-TL ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    r = np.asarray(result.range_m, dtype=np.float64)
    label = f"{_t('Total TL', language)} ({decimal_comma(f'{result.frequency / 1000.0:.3g}', language)} kHz)"
    ax.plot(r, np.asarray(result.tl), **{"color": _C_PRIMARY, "lw": 1.6, "label": label, **kwargs})
    ax.plot(r, np.asarray(result.spreading), color=_C_MUTED, lw=1.0, ls="--",
            label=f"{_t('Spreading', language)} ({result.law})")
    ax.plot(r, np.asarray(result.absorption), color=_C_SECONDARY, lw=1.0, ls=":",
            label=f"{_t('Absorption', language)} ({decimal_comma(f'{result.absorption_coefficient:.3g}', language)} dB/km)")
    ax.set_xlabel(_t("Range [m]", language))
    ax.set_ylabel(_t("Transmission loss [dB]", language))
    ax.set_title(f"{_t('Underwater transmission loss', language)} ({result.model})")
    if not ax.yaxis_inverted():
        ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize="small")
    localize_axes(ax, language)
    return ax

def plot_sonar_equation(
    result: SonarEquationResult, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Signal excess versus transmission loss, with the detection limit (SE = 0).

    :param result: A :class:`~phonometry.sonar_equation.SonarEquationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the signal-excess ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    tl = np.asarray(result.transmission_loss, dtype=np.float64)
    se = np.asarray(result.signal_excess, dtype=np.float64)
    order = np.argsort(tl)
    label = f"{_t('Signal excess', language)} ({result.mode})"
    ax.plot(tl[order], se[order], **{"color": _C_PRIMARY, "lw": 1.6, "label": label, **kwargs})
    ax.axhline(0.0, color=_C_REFERENCE, ls="--", lw=1.0, label=_t("Detection limit (SE = 0)", language))
    ax.axvline(result.figure_of_merit, color=_C_MUTED, ls=":", lw=1.0,
               label=f"{_t('Figure of merit', language)} = {format_number(result.figure_of_merit, language)} dB")
    ax.set_xlabel(_t("Transmission loss [dB]", language))
    ax.set_ylabel(_t("Signal excess [dB]", language))
    ax.set_title(_t("Sonar equation", language))
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax

def plot_bottom_loss(
    result: BottomLossResult, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Bottom reflection loss versus grazing angle, marking the critical angle.

    :param result: A :class:`~phonometry.seabed_reflection.BottomLossResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the bottom-loss ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    phi = np.asarray(result.grazing_angle, dtype=np.float64)
    loss = np.asarray(result.reflection_loss, dtype=np.float64)
    ax.plot(phi, loss, **{"color": _C_PRIMARY, "lw": 1.6, "label": _t("Bottom loss", language), **kwargs})
    if result.critical_angle is not None:
        ax.axvline(result.critical_angle, color=_C_REFERENCE, ls="--", lw=1.0,
                   label=f"{_t('Critical angle', language)} = {format_number(result.critical_angle, language)}°")
    ax.set_xlabel(_t("Grazing angle [°]", language))
    ax.set_ylabel(_t("Bottom loss [dB]", language))
    ax.set_title(_t("Seabed reflection loss", language))
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax

def plot_seabed_reflection(
    result: SeabedReflection, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Seabed reflection-coefficient magnitude versus grazing angle.

    Draws ``|R|`` on a linear grazing-angle axis, marking the critical angle
    when the sediment is faster than the water.

    :param result: A :class:`~phonometry.seabed_reflection.SeabedReflection`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the magnitude ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    phi = np.asarray(result.grazing_angle, dtype=np.float64)
    magnitude = np.asarray(result.magnitude, dtype=np.float64)
    ax.plot(phi, magnitude, **{"color": _C_PRIMARY, "lw": 1.6, "label": "$|R|$", **kwargs})
    if result.critical_angle is not None:
        ax.axvline(result.critical_angle, color=_C_REFERENCE, ls="--", lw=1.0,
                   label=f"{_t('Critical angle', language)} = {format_number(result.critical_angle, language)}°")
    ax.set_xlabel(_t("Grazing angle [°]", language))
    ax.set_xlim(0.0, 90.0)
    ax.set_ylabel(f"{_t('Reflection coefficient magnitude', language)} $|R|$")
    ax.set_title(_t("Seabed reflection coefficient", language))
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax

def plot_ambient_noise(
    result: AmbientNoiseResult, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Composite ambient-noise spectrum and its components versus frequency.

    :param result: An :class:`~phonometry.ocean_ambient_noise.AmbientNoiseResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the composite-level ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequency, dtype=np.float64)
    label = f"{_t('Total', language)} ({format_number(result.wind_speed_knots, language)} kn)"
    ax.plot(f, np.asarray(result.spectrum_level),
            **{"color": _C_PRIMARY, "lw": 1.8, "label": label, **kwargs})
    ax.plot(f, np.asarray(result.wind), color=_C_SECONDARY, lw=1.0, ls="--", label=_t("Wind", language))
    ax.plot(f, np.asarray(result.thermal), color=_C_TERTIARY, lw=1.0, ls=":", label=_t("Thermal", language))
    if result.shipping is not None:
        ax.plot(f, np.asarray(result.shipping), color=_C_REFERENCE, lw=1.0, ls="-.",
                label=_t("Shipping", language))
    ax.set_xscale("log")
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("Spectrum level [dB re 1 µPa²/Hz]", language))
    ax.set_title(_t("Ocean ambient noise", language))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    format_frequency_axis(ax, float(f.min()), float(f.max()))
    localize_axes(ax, language)
    return ax

def plot_ship_traffic_spectrum(
    result: ShipTrafficSpectrum, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Predicted ship source spectral-density level versus frequency.

    :param result: A :class:`~phonometry.ship_traffic_noise.ShipTrafficSpectrum`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the source-PSD ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequency, dtype=np.float64)
    psd = np.asarray(result.source_psd, dtype=np.float64)
    if result.vessel_class is not None:
        label = f"{result.model} ({result.vessel_class})"
    else:
        label = result.model
    ax.plot(f, psd, **{"color": _C_PRIMARY, "lw": 1.6, "label": label, **kwargs})
    ax.set_xscale("log")
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("Source spectral density [dB re 1 µPa²/Hz at 1 m]", language))
    ax.set_title(_t("Ship traffic source level", language))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    format_frequency_axis(ax, float(f.min()), float(f.max()))
    localize_axes(ax, language)
    return ax

def plot_normal_modes(
    result: NormalModeResult, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Normal-mode transmission loss versus range (loss increasing downward).

    :param result: A :class:`~phonometry.numerical_propagation.NormalModeResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the transmission-loss ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    r = np.asarray(result.ranges, dtype=np.float64)
    tl = np.asarray(result.transmission_loss, dtype=np.float64)
    label = f"{result.wavenumbers.size} {_t('modes', language)} ({format_number(result.frequency, language, decimals=0)} Hz)"
    ax.plot(r / 1000.0, tl, **{"color": _C_PRIMARY, "lw": 1.2, "label": label, **kwargs})
    ax.set_xlabel(_t("Range [km]", language))
    ax.set_ylabel(_t("Transmission loss [dB]", language))
    ax.set_title(_t("Normal-mode transmission loss", language))
    if not ax.yaxis_inverted():
        ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize="small")
    localize_axes(ax, language)
    return ax

def plot_ray_trace(result: RayTraceResult, ax: Axes | None = None, *, language: str = "en",
                   **kwargs: Any) -> Axes:
    """Ray paths through the water column (depth increasing downward).

    :param result: A :class:`~phonometry.numerical_propagation.RayTraceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to each ray ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    r = np.asarray(result.ranges, dtype=np.float64)
    z = np.asarray(result.depths, dtype=np.float64)
    for i in range(r.shape[0]):
        ax.plot(r[i] / 1000.0, z[i], **{"color": _C_PRIMARY, "lw": 0.7, "alpha": 0.7, **kwargs})
    ax.plot([0.0], [result.source_depth], "o", color=_C_REFERENCE, label=_t("Source", language))
    ax.set_xlabel(_t("Range [km]", language))
    ax.set_ylabel(_t("Depth [m]", language))
    ax.set_title(_t("Ray trace", language))
    if not ax.yaxis_inverted():
        ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize="small")
    localize_axes(ax, language)
    return ax

def plot_parabolic_equation(
    result: ParabolicEquationResult, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Parabolic-equation transmission-loss field (range x depth).

    :param result: A
        :class:`~phonometry.numerical_propagation.ParabolicEquationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``imshow``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    r = np.asarray(result.ranges, dtype=np.float64) / 1000.0
    z = np.asarray(result.depths, dtype=np.float64)
    tl = np.asarray(result.transmission_loss, dtype=np.float64)
    finite = tl[np.isfinite(tl)]
    vmax = float(np.percentile(finite, 95)) if finite.size else 100.0
    # The zero-range column is infinite (1/√r); clip non-finite samples to vmax
    # so imshow does not render them as a spurious stripe.
    tl = np.where(np.isfinite(tl), tl, vmax)
    # imshow renders the field as a single raster image (no per-cell vector
    # quads), which avoids moiré and keeps the figure light.
    img = ax.imshow(
        tl,
        **{
            "cmap": "viridis_r",
            "vmin": vmax - 50.0,
            "vmax": vmax,
            "aspect": "auto",
            "origin": "upper",
            "interpolation": "bilinear",
            "extent": (float(r[0]), float(r[-1]), float(z[-1]), float(z[0])),
            **kwargs,
        },
    )
    ax.figure.colorbar(img, ax=ax, label=_t("Transmission loss [dB]", language))
    ax.set_xlabel(_t("Range [km]", language))
    ax.set_ylabel(_t("Depth [m]", language))
    ax.set_title(_t("Parabolic-equation transmission loss", language))
    localize_axes(ax, language)
    return ax
