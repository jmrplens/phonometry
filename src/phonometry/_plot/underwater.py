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
    _LABEL_DEPTH_M,
    _LABEL_RANGE_KM,
    _LABEL_TL_DB,
    _LEGEND_UPPER_RIGHT,
    _new_axes,
    _new_axes_column,
    format_frequency_axis,
)

if TYPE_CHECKING:
    from ..underwater.numerical_propagation import (
        NormalModeResult,
        ParabolicEquationResult,
        RayTraceResult,
    )
    from matplotlib.axes import Axes
    from ..underwater.ship_radiated_noise import ShipSourceLevelResult
    from ..underwater.pile_driving_noise import PileStrikeResult
    from ..underwater.sound_speed import SoundSpeedProfile
    from ..underwater.propagation import TransmissionLossResult
    from ..underwater.sonar_equation import SonarEquationResult
    from ..underwater.seabed_reflection import BottomLossResult
    from ..underwater.ocean_ambient_noise import AmbientNoiseResult
    from ..underwater.ship_traffic_noise import ShipTrafficSpectrum

def plot_ship_source_level(
    result: "ShipSourceLevelResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Radiated noise level, source level and the ΔL surface correction.

    Draws the input RNL and the equivalent monopole source level ``Ls`` versus
    frequency, with the Lloyd's-mirror correction ``ΔL`` on a twin axis.

    :param result: A
        :class:`~phonometry.ship_radiated_noise.ShipSourceLevelResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the source-level ``semilogx`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    rnl = np.asarray(result.radiated_noise_level, dtype=np.float64)
    ls = np.asarray(result.source_level, dtype=np.float64)
    dl = np.asarray(result.surface_correction, dtype=np.float64)

    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Source level Ls")
    ax.semilogx(freqs, ls, "o-", **kwargs)
    ax.semilogx(freqs, rnl, "s--", color=_C_REFERENCE, label="Radiated noise level")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Level [dB re 1 µPa·m]")
    ax.grid(True, which="both", alpha=0.3)
    ax.set_axisbelow(True)

    twin = ax.twinx()
    twin.semilogx(freqs, dl, ":", color=_C_TERTIARY, label="Surface correction ΔL")
    twin.set_ylabel("Surface correction ΔL [dB]")
    # After twinx() (it re-initialises the shared x-axis with the default log
    # locator) so the octave-band labelling is not reset back to 10^n ticks.
    format_frequency_axis(ax, float(freqs.min()), float(freqs.max()))

    lines, labels = ax.get_legend_handles_labels()
    tlines, tlabels = twin.get_legend_handles_labels()
    ax.legend(lines + tlines, labels + tlabels, loc="best", fontsize="small")
    ax.set_title(
        "ISO 17208-2 equivalent monopole source level "
        f"(d_s = {result.source_depth:.1f} m, c = {result.sound_speed:.0f} m/s)"
    )
    return ax

def plot_pile_strike(
    result: "PileStrikeResult", ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Pile-strike pressure waveform and its cumulative energy.

    Two stacked panels: the pressure waveform with the peak marked on top, and
    the normalised cumulative energy with the 5 %/95 % pulse-duration bounds
    below. With ``ax`` given, only the waveform panel is drawn on it.

    :param result: A :class:`~phonometry.pile_driving_noise.PileStrikeResult`.
    :param ax: Existing axes for the waveform panel, or ``None`` for a fresh
        two-panel figure.
    :param kwargs: Forwarded to the waveform ``plot`` call.
    :return: The waveform axes (``ax`` given) or the array of two axes.
    """
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
                 label=f"Peak ({result.peak_spl:.0f} dB re 1 µPa)")
        axw.set_ylabel("Pressure [Pa]")
        axw.grid(True, alpha=0.3)
        axw.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _waveform(ax)
        ax.set_xlabel("Time [s]")
        ax.set_title(f"ISO 18406 pile strike (SEL_ss = {result.single_strike_sel:.0f} dB)")
        return ax

    axes = _new_axes_column(2, sharex=True, figsize=(8.0, 6.0))
    _waveform(axes[0])
    axes[0].set_title(
        f"ISO 18406 pile strike (SEL_ss = {result.single_strike_sel:.0f} dB re 1 µPa²·s)"
    )
    axes[1].plot(t, cum, color=_C_TERTIARY, label="Cumulative energy")
    for frac in (0.05, 0.95):
        axes[1].axhline(frac, color=_C_MUTED, ls="--", lw=0.8)
    axes[1].set_ylabel("Cumulative energy (norm.)")
    axes[1].set_xlabel("Time [s]")
    axes[1].set_title(f"90 % pulse duration = {result.pulse_duration * 1e3:.0f} ms")
    axes[1].grid(True, alpha=0.3)
    return axes

def plot_sound_speed_profile(
    result: "SoundSpeedProfile", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Sound-speed profile: speed vs depth, with depth increasing downward.

    :param result: A :class:`~phonometry.underwater_sound_speed.SoundSpeedProfile`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the profile ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    depth = np.asarray(result.depth, dtype=np.float64)
    speed = np.asarray(result.sound_speed, dtype=np.float64)
    label = f"{result.model} c(z)"
    ax.plot(speed, depth, **{"color": _C_PRIMARY, "lw": 1.4, "label": label, **kwargs})
    if not ax.yaxis_inverted():
        ax.invert_yaxis()
    ax.set_xlabel("Sound speed [m/s]")
    ax.set_ylabel(_LABEL_DEPTH_M)
    ax.set_title("Sea-water sound-speed profile")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower left", fontsize="small")
    return ax

def plot_transmission_loss(
    result: "TransmissionLossResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Transmission loss versus range, with spreading and absorption split out.

    Loss increases downward (the usual TL convention).

    :param result: A :class:`~phonometry.underwater_propagation.TransmissionLossResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the total-TL ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    r = np.asarray(result.range_m, dtype=np.float64)
    label = f"Total TL ({result.frequency / 1000.0:.3g} kHz)"
    ax.plot(r, np.asarray(result.tl), **{"color": _C_PRIMARY, "lw": 1.6, "label": label, **kwargs})
    ax.plot(r, np.asarray(result.spreading), color=_C_MUTED, lw=1.0, ls="--",
            label=f"Spreading ({result.law})")
    ax.plot(r, np.asarray(result.absorption), color=_C_SECONDARY, lw=1.0, ls=":",
            label=f"Absorption ({result.absorption_coefficient:.3g} dB/km)")
    ax.set_xlabel("Range [m]")
    ax.set_ylabel(_LABEL_TL_DB)
    ax.set_title(f"Underwater transmission loss ({result.model})")
    if not ax.yaxis_inverted():
        ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize="small")
    return ax

def plot_sonar_equation(
    result: "SonarEquationResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Signal excess versus transmission loss, with the detection limit (SE = 0).

    :param result: A :class:`~phonometry.sonar_equation.SonarEquationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the signal-excess ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    tl = np.asarray(result.transmission_loss, dtype=np.float64)
    se = np.asarray(result.signal_excess, dtype=np.float64)
    order = np.argsort(tl)
    label = f"Signal excess ({result.mode})"
    ax.plot(tl[order], se[order], **{"color": _C_PRIMARY, "lw": 1.6, "label": label, **kwargs})
    ax.axhline(0.0, color=_C_REFERENCE, ls="--", lw=1.0, label="Detection limit (SE = 0)")
    ax.axvline(result.figure_of_merit, color=_C_MUTED, ls=":", lw=1.0,
               label=f"Figure of merit = {result.figure_of_merit:.1f} dB")
    ax.set_xlabel(_LABEL_TL_DB)
    ax.set_ylabel("Signal excess [dB]")
    ax.set_title("Sonar equation")
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    return ax

def plot_bottom_loss(
    result: "BottomLossResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Bottom reflection loss versus grazing angle, marking the critical angle.

    :param result: A :class:`~phonometry.seabed_reflection.BottomLossResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the bottom-loss ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    phi = np.asarray(result.grazing_angle, dtype=np.float64)
    loss = np.asarray(result.reflection_loss, dtype=np.float64)
    ax.plot(phi, loss, **{"color": _C_PRIMARY, "lw": 1.6, "label": "Bottom loss", **kwargs})
    if result.critical_angle is not None:
        ax.axvline(result.critical_angle, color=_C_REFERENCE, ls="--", lw=1.0,
                   label=f"Critical angle = {result.critical_angle:.1f}°")
    ax.set_xlabel("Grazing angle [°]")
    ax.set_ylabel("Bottom loss [dB]")
    ax.set_title("Seabed reflection loss")
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    return ax

def plot_ambient_noise(
    result: "AmbientNoiseResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Composite ambient-noise spectrum and its components versus frequency.

    :param result: An :class:`~phonometry.ocean_ambient_noise.AmbientNoiseResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the composite-level ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequency, dtype=np.float64)
    label = f"Total ({result.wind_speed_knots:.1f} kn)"
    ax.plot(f, np.asarray(result.spectrum_level),
            **{"color": _C_PRIMARY, "lw": 1.8, "label": label, **kwargs})
    ax.plot(f, np.asarray(result.wind), color=_C_SECONDARY, lw=1.0, ls="--", label="Wind")
    ax.plot(f, np.asarray(result.thermal), color=_C_TERTIARY, lw=1.0, ls=":", label="Thermal")
    if result.shipping is not None:
        ax.plot(f, np.asarray(result.shipping), color=_C_REFERENCE, lw=1.0, ls="-.",
                label="Shipping")
    ax.set_xscale("log")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Spectrum level [dB re 1 µPa²/Hz]")
    ax.set_title("Ocean ambient noise")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    format_frequency_axis(ax, float(f.min()), float(f.max()))
    return ax

def plot_ship_traffic_spectrum(
    result: "ShipTrafficSpectrum", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Predicted ship source spectral-density level versus frequency.

    :param result: A :class:`~phonometry.ship_traffic_noise.ShipTrafficSpectrum`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the source-PSD ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequency, dtype=np.float64)
    psd = np.asarray(result.source_psd, dtype=np.float64)
    if result.vessel_class is not None:
        label = f"{result.model} ({result.vessel_class})"
    else:
        label = result.model
    ax.plot(f, psd, **{"color": _C_PRIMARY, "lw": 1.6, "label": label, **kwargs})
    ax.set_xscale("log")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Source spectral density [dB re 1 µPa²/Hz at 1 m]")
    ax.set_title("Ship traffic source level")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    format_frequency_axis(ax, float(f.min()), float(f.max()))
    return ax

def plot_normal_modes(
    result: "NormalModeResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Normal-mode transmission loss versus range (loss increasing downward).

    :param result: A :class:`~phonometry.numerical_propagation.NormalModeResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the transmission-loss ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    r = np.asarray(result.ranges, dtype=np.float64)
    tl = np.asarray(result.transmission_loss, dtype=np.float64)
    label = f"{result.wavenumbers.size} modes ({result.frequency:.0f} Hz)"
    ax.plot(r / 1000.0, tl, **{"color": _C_PRIMARY, "lw": 1.2, "label": label, **kwargs})
    ax.set_xlabel(_LABEL_RANGE_KM)
    ax.set_ylabel(_LABEL_TL_DB)
    ax.set_title("Normal-mode transmission loss")
    if not ax.yaxis_inverted():
        ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize="small")
    return ax

def plot_ray_trace(result: "RayTraceResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Ray paths through the water column (depth increasing downward).

    :param result: A :class:`~phonometry.numerical_propagation.RayTraceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to each ray ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    r = np.asarray(result.ranges, dtype=np.float64)
    z = np.asarray(result.depths, dtype=np.float64)
    for i in range(r.shape[0]):
        ax.plot(r[i] / 1000.0, z[i], **{"color": _C_PRIMARY, "lw": 0.7, "alpha": 0.7, **kwargs})
    ax.plot([0.0], [result.source_depth], "o", color=_C_REFERENCE, label="Source")
    ax.set_xlabel(_LABEL_RANGE_KM)
    ax.set_ylabel(_LABEL_DEPTH_M)
    ax.set_title("Ray trace")
    if not ax.yaxis_inverted():
        ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize="small")
    return ax

def plot_parabolic_equation(
    result: "ParabolicEquationResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Parabolic-equation transmission-loss field (range x depth).

    :param result: A
        :class:`~phonometry.numerical_propagation.ParabolicEquationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to ``imshow``.
    :return: The axes.
    """
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
    ax.figure.colorbar(img, ax=ax, label=_LABEL_TL_DB)
    ax.set_xlabel(_LABEL_RANGE_KM)
    ax.set_ylabel(_LABEL_DEPTH_M)
    ax.set_title("Parabolic-equation transmission loss")
    return ax
