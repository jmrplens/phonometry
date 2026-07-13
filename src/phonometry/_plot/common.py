#  Copyright (c) 2026. Jose M. Requena-Plens

"""One-line canonical figures for the library's result objects.

Every public result dataclass exposes a thin ``plot(ax=None, **kwargs)``
method that delegates to a rendering function in this module, reproducing
the essence of its documentation figure in a single call::

    res = room_parameters(ir, fs)
    res.plot()

matplotlib is a *soft* dependency: importing :mod:`phonometry` and running
any computation works without it, and only calling ``.plot()`` (or the
functions here) requires it.  The import is therefore performed lazily and
raises a clear :class:`ImportError` with installation guidance when the
package is missing, mirroring :func:`phonometry.filter_design._showfilter`.

The functions are pure renderers: they never call ``plt.show``; when ``ax``
is ``None`` they create a fresh figure and axes, and they always *return*
the :class:`~matplotlib.axes.Axes` (or an array of axes for multi-panel
figures) so the plot can be composed into a larger layout.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Sequence, cast

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.container import BarContainer

    from ..building.insulation import (
        ImpactRatingResult,
        WeightedRatingResult,
    )
    from ..room.room_acoustics import RoomAcousticsResult
    from ..distortion import HarmonicDistortionResult
    from ..frequency_response import FrequencyResponseResult
    from ..ship_radiated_noise import ShipSourceLevelResult
    from ..pile_driving_noise import PileStrikeResult
    from ..aircraft_noise import EPNLResult
    from ..underwater_sound_speed import SoundSpeedProfile
    from ..underwater_propagation import TransmissionLossResult
    from ..sonar_equation import SonarEquationResult
    from ..seabed_reflection import BottomLossResult
    from ..ocean_ambient_noise import AmbientNoiseResult
    from ..ship_traffic_noise import ShipTrafficSpectrum
    from ..numerical_propagation import (
        NormalModeResult,
        ParabolicEquationResult,
        RayTraceResult,
    )
    from ..aircraft_atmospheric_absorption import AircraftBandAttenuation
    from ..airport_noise import FlyoverResult, NoiseContourResult, NpdLevelResult
    from ..rotorcraft_noise import RotorcraftHemisphere

_INSTALL_HINT = (
    "Plotting requires matplotlib. Install it with: pip install phonometry[plot]"
)

#: Nominal octave-band centres used by the STI computation (125 Hz - 8 kHz).
_STI_BAND_CENTERS = (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0)

#: Default legend placement shared by the band-spectrum figures.
_LEGEND_UPPER_RIGHT: Final = "upper right"

# ---------------------------------------------------------------------------
# Shared artist colors (matplotlib "tab10" hues plus neutral greys).
#
# The measured/primary series is drawn in _C_PRIMARY, reference curves and
# limit lines in _C_REFERENCE, unfavourable/secondary annotations in
# _C_SECONDARY, and de-emphasised context (invalid bands, threshold guides,
# curve families, companion series) in the single neutral _C_MUTED.
#
# Two renderers keep a fixed per-metric identity color instead: ECMA-418-2
# tonality is red and roughness is brown across the documentation, so those
# literals live in their renderers with a comment, not here.
# ---------------------------------------------------------------------------
_C_PRIMARY: Final = "#1f77b4"
_C_PRIMARY_LIGHT: Final = "#aec7e8"
_C_REFERENCE: Final = "#d62728"
_C_SECONDARY: Final = "#ff7f0e"
_C_SECONDARY_LIGHT: Final = "#ffbb78"
_C_TERTIARY: Final = "#2ca02c"
_C_QUATERNARY: Final = "#9467bd"
_C_MUTED: Final = "#9e9e9e"
_C_EDGE: Final = "#555555"

#: Standard-normal quantile of 0.9 (the 10 % / 90 % fractile offset).
_Z90: Final = 1.2816

#: Common axis labels reused across the underwater-propagation plots.
_LABEL_DEPTH_M: Final = "Depth [m]"
_LABEL_TL_DB: Final = "Transmission loss [dB]"
_LABEL_RANGE_KM: Final = "Range [km]"


def _import_pyplot() -> Any:
    """Import :mod:`matplotlib.pyplot` lazily with an actionable error."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        raise ImportError(_INSTALL_HINT) from exc
    return plt


def _new_axes() -> Axes:
    """Create a single fresh figure + axes and return the axes."""
    plt = _import_pyplot()
    _fig, ax = plt.subplots()
    return cast("Axes", ax)


def _new_axes_column(n: int, **kwargs: Any) -> np.ndarray:
    """Create a stacked column of ``n`` axes and return them as an array."""
    plt = _import_pyplot()
    _fig, axes = plt.subplots(n, 1, **kwargs)
    result: np.ndarray = np.atleast_1d(axes)
    return result


def _freq_axis(ax: Axes, freqs: np.ndarray) -> None:
    """Configure a logarithmic frequency x-axis labelled with band centres."""
    import matplotlib.ticker as mticker

    ax.set_xscale("log")
    ax.set_xticks(list(freqs))
    ax.set_xticklabels([_format_freq(f) for f in freqs], rotation=45, ha="right")
    # Suppress the log-scale minor-tick labels (2x10^2, 3x10^2, ...) that would
    # otherwise collide with off-decade band centres such as 750 or 1500 Hz.
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.set_xlabel("Frequency [Hz]")


def _format_freq(f: float) -> str:
    """Short human label for a band centre frequency."""
    if f >= 1000.0:
        text = f"{f / 1000.0:g}k"
    else:
        text = f"{f:g}"
    return text


def _band_axis(
    ax: Axes,
    labels_or_freqs: "np.ndarray | Sequence[str] | Sequence[float]",
    *,
    xlabel: str | None = "Frequency [Hz]",
) -> np.ndarray:
    """Categorical band x-axis: evenly spaced positions labelled with centres.

    Band bars/curves are drawn on evenly spaced positions (a *linear* axis)
    so they stay legible; the tick labels carry the band centres (numeric
    input is shortened via :func:`_format_freq`) or the given strings.
    Returns the positions.  ``xlabel=None`` leaves the axis label untouched
    (e.g. a shared-x upper panel).
    """
    labels = [
        item if isinstance(item, str) else _format_freq(float(item))
        for item in list(labels_or_freqs)
    ]
    positions = np.arange(len(labels), dtype=np.float64)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    return positions


def _fractile_band(
    ax: Axes,
    freqs: np.ndarray,
    median: np.ndarray,
    spread_lower: np.ndarray,
    spread_upper: np.ndarray,
    *,
    color: str,
    floor: float | None = None,
) -> None:
    """Shade the 10-90 % fractile band around a median spectrum.

    The band spans ``median - z90*spread_lower`` to ``median +
    z90*spread_upper`` with the standard-normal :data:`_Z90` quantile;
    ``floor`` clamps the lower edge (e.g. NIPTS cannot be negative).
    """
    lower = median - _Z90 * spread_lower
    if floor is not None:
        lower = np.maximum(lower, floor)
    ax.fill_between(freqs, lower, median + _Z90 * spread_upper,
                    color=color, alpha=0.5, label="10-90 % fractile band")


def _hatch_invalid(bars: "BarContainer", mask: np.ndarray) -> None:
    """Hatch (and outline) the bars flagged invalid/unusable by ``mask``."""
    for bar, bad in zip(bars, np.asarray(mask, dtype=bool), strict=True):
        if bad:
            bar.set_hatch("//")
            bar.set_edgecolor(_C_EDGE)


# ---------------------------------------------------------------------------
# Zwicker loudness (ISO 532-1)
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# ECMA-418-2 Sottek loudness
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# ISO 532-2 Moore-Glasberg loudness
# ---------------------------------------------------------------------------














# ---------------------------------------------------------------------------
# Electroacoustics: distortion & frequency response (IEC 60268-3 / Bendat)
# ---------------------------------------------------------------------------


def plot_harmonic_distortion(
    result: "HarmonicDistortionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Harmonic amplitude spectrum with the harmonics marked and THD annotated.

    Draws the fundamental and its harmonics as a stem-style amplitude spectrum
    in dB relative to the fundamental, annotated with the THD (both
    conventions) and SINAD.

    :param result: A :class:`~phonometry.distortion.HarmonicDistortionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the marker ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    amps = np.asarray(result.harmonic_amplitudes, dtype=np.float64)
    tiny = np.finfo(np.float64).tiny
    ref = amps[0] if amps.size and amps[0] > 0.0 else 1.0
    levels_db = 20.0 * np.log10(np.maximum(amps, tiny) / ref)
    orders = np.arange(1, amps.size + 1)

    ax.vlines(orders, -160.0, levels_db, color=_C_PRIMARY, lw=1.5)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Harmonics")
    ax.plot(orders, levels_db, "o", **kwargs)
    for order, level in zip(orders, levels_db):
        if level > -160.0:
            ax.annotate(
                f"{order}",
                (order, level),
                textcoords="offset points",
                xytext=(0, 5),
                ha="center",
                fontsize="x-small",
            )
    ax.set_xlabel("Harmonic order n  (f = n·f₁)")
    ax.set_ylabel("Level re fundamental [dB]")
    ax.set_xticks(orders)
    ax.set_ylim(bottom=-160.0, top=10.0)
    ax.set_title(
        f"IEC 60268-3 THD = {result.thd_f * 100.0:.3g}% (F), "
        f"{result.thd_r * 100.0:.3g}% (R); SINAD = {result.sinad_db:.1f} dB "
        f"(f₁ = {_format_freq(result.fundamental)}Hz)"
    )
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    return ax


def plot_frequency_response(
    result: "FrequencyResponseResult", ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Bode magnitude / phase and coherence of an estimated frequency response.

    Three stacked panels: the magnitude in dB, the phase in degrees and the
    ordinary coherence ``γ²``. With ``ax`` given, only the magnitude panel is
    drawn on it.

    :param result: A
        :class:`~phonometry.frequency_response.FrequencyResponseResult`.
    :param ax: Existing axes for the magnitude panel, or ``None`` for a fresh
        three-panel figure.
    :param kwargs: Forwarded to the magnitude ``plot`` call.
    :return: The magnitude-panel axes (``ax`` given) or the array of three axes.
    """
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    mag = np.asarray(result.magnitude_db, dtype=np.float64)
    phase_deg = np.degrees(np.asarray(result.phase, dtype=np.float64))
    coh = np.asarray(result.coherence, dtype=np.float64)
    pos = freqs > 0.0
    color = kwargs.pop("color", _C_PRIMARY)

    def _magnitude(axm: Axes) -> None:
        kwargs.setdefault("label", f"|H| ({result.estimator})")
        axm.semilogx(freqs[pos], mag[pos], color=color, **kwargs)
        axm.set_ylabel("Magnitude [dB]")
        axm.grid(True, which="both", alpha=0.3)
        axm.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _magnitude(ax)
        ax.set_xlabel("Frequency [Hz]")
        ax.set_title(f"Frequency response ({result.estimator})")
        return ax

    axes = _new_axes_column(3, sharex=True, figsize=(8.0, 8.0))
    _magnitude(axes[0])
    axes[0].set_title(f"Frequency response ({result.estimator}) and coherence")
    axes[1].semilogx(freqs[pos], phase_deg[pos], color=_C_SECONDARY)
    axes[1].set_ylabel("Phase [deg]")
    axes[1].grid(True, which="both", alpha=0.3)
    axes[2].semilogx(freqs[pos], coh[pos], color=_C_TERTIARY)
    axes[2].set_ylabel(r"Coherence $\gamma^2$")
    axes[2].set_xlabel("Frequency [Hz]")
    axes[2].set_ylim(0.0, 1.05)
    axes[2].grid(True, which="both", alpha=0.3)
    return axes


# ---------------------------------------------------------------------------
# Underwater acoustics (ISO 17208 ship radiated noise, ISO 18406 pile driving)
# ---------------------------------------------------------------------------


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


def plot_epnl(result: "EPNLResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """PNL and PNLT time histories with PNLTM and the 10 dB-down window.

    The perceived noise level and its tone-corrected counterpart are drawn
    against time; the maximum ``PNLTM`` is marked and the 10 dB-down integration
    band (records ``kF``..``kL``) is shaded, annotated with the EPNL.

    :param result: An :class:`~phonometry.aircraft_noise.EPNLResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the PNLT ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    t = np.asarray(result.times, dtype=np.float64)
    kf, kl = result.band_limits
    ax.plot(t, np.asarray(result.pnl), color=_C_MUTED, lw=1.0, ls="--", label="PNL")
    ax.plot(t, np.asarray(result.pnlt), **{"color": _C_PRIMARY, "lw": 1.4, "label": "PNLT", **kwargs})
    ax.axvspan(t[kf], t[kl], color=_C_TERTIARY, alpha=0.15, label="10 dB-down window")
    km = int(np.argmax(np.asarray(result.pnlt)))
    ax.plot([t[km]], [result.pnltm], "o", color=_C_REFERENCE,
            label=f"PNLTM = {result.pnltm:.1f} PNdB")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Level [PNdB]")
    ax.set_title(f"ICAO EPNL = {result.epnl:.1f} EPNdB (D = {result.duration_correction:+.1f} dB)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    return ax




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


def plot_aircraft_band_attenuation(
    result: "AircraftBandAttenuation", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """One-third-octave-band and pure-tone mid-band attenuation versus frequency.

    :param result: An
        :class:`~phonometry.aircraft_atmospheric_absorption.AircraftBandAttenuation`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the band-attenuation ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequency, dtype=np.float64)
    label = f"SAE band ({result.path_length:.0f} m)"
    ax.plot(f, np.asarray(result.band_attenuation),
            **{"color": _C_PRIMARY, "lw": 1.6, "marker": "o", "ms": 3, "label": label, **kwargs})
    ax.plot(f, np.asarray(result.midband_attenuation), color=_C_SECONDARY, lw=1.0, ls="--",
            label="Pure-tone mid-band (ISO 9613-1)")
    ax.set_xscale("log")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Attenuation [dB]")
    ax.set_title("Aircraft atmospheric absorption (SAE ARP 5534)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper left", fontsize="small")
    return ax


def plot_npd_level(result: "NpdLevelResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """NPD event level versus slant distance (log axis), with the tabulated nodes.

    :param result: An :class:`~phonometry.airport_noise.NpdLevelResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the interpolated-curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    d = np.asarray(result.distance, dtype=np.float64)
    lvl = np.asarray(result.level, dtype=np.float64)
    td = np.asarray(result.table_distances, dtype=np.float64)
    tl = np.asarray(result.table_levels, dtype=np.float64)
    label = f"NPD (P = {result.power:g})"
    ax.plot(d, lvl, **{"color": _C_PRIMARY, "lw": 1.6, "label": label, **kwargs})
    ax.plot(td, tl, "o", color=_C_REFERENCE, ms=4, label="Tabulated")
    ax.set_xscale("log")
    ax.set_xlabel("Slant distance [m]")
    ax.set_ylabel("Event level [dB]")
    ax.set_title("Noise-power-distance curve (ECAC Doc 29)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    return ax


def plot_flyover(result: "FlyoverResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Per-segment contributions to a single-event level (ECAC Doc 29).

    Bars show each flight-path segment's event level; the dashed line marks the
    energy-summed total (SEL) or the maximum (LAmax).

    :param result: A :class:`~phonometry.airport_noise.FlyoverResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the bar call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    seg = np.asarray(result.segment_levels, dtype=np.float64)
    # Non-finite segment contributions (e.g. a fully-attenuated segment) are
    # dropped so Matplotlib does not choke on them.
    seg = np.where(np.isfinite(seg), seg, np.nan)
    idx = np.arange(seg.size)
    metric = "SEL" if result.metric == "exposure" else "LAmax"
    ax.bar(idx, seg, **{"color": _C_PRIMARY, "alpha": 0.85, **kwargs})
    if np.isfinite(result.level):
        ax.axhline(result.level, color=_C_REFERENCE, ls="--", lw=1.2,
                   label=f"Total {metric} = {result.level:.1f} dB")
    ax.set_xlabel("Segment index")
    ax.set_ylabel(f"Segment {metric} [dB]")
    ax.set_title("Single-event segment contributions (ECAC Doc 29)")
    ax.grid(True, axis="y", alpha=0.3)
    if np.isfinite(result.level):
        ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    return ax


def plot_rotorcraft_hemisphere(
    result: "RotorcraftHemisphere", ax: Axes | None = None, *, band: float | None = None,
    **kwargs: Any) -> Axes:
    """Fore-aft directivity section of a rotorcraft noise hemisphere (ECAC Doc 32).

    Plots the source level versus polar angle θ (0° forward → 180° rearward) in the
    vertical plane (azimuth φ = 0) for a single one-third-octave band.

    :param result: A :class:`~phonometry.rotorcraft_noise.RotorcraftHemisphere`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param band: Band centre frequency to plot, in Hz (default: the loudest band).
    :param kwargs: Forwarded to ``plot``.
    :return: The axes.
    """
    from ..rotorcraft_noise import hemisphere_source_level

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    theta = np.linspace(float(result.polar[0]), float(result.polar[-1]), 181)
    grid = np.array([hemisphere_source_level(result, 0.0, t) for t in theta])
    idx = int(np.argmin(np.abs(freqs - band))) if band is not None else int(
        np.nanargmax(np.nansum(10.0 ** (grid / 10.0), axis=0)))
    ax.plot(theta, grid[:, idx], **{"color": _C_PRIMARY, "lw": 1.8,
            "label": f"{freqs[idx]:.0f} Hz (φ = 0°)", **kwargs})
    ax.set_xlabel("Polar angle θ [°]  (0° forward → 180° rearward)")
    ax.set_ylabel("Source level at 60 m [dB]")
    ax.set_title("Rotorcraft noise hemisphere directivity (ECAC Doc 32)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    return ax


def plot_noise_contour(result: "NoiseContourResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Filled single-event noise contours over the ground plane (ECAC Doc 29).

    :param result: A :class:`~phonometry.airport_noise.NoiseContourResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to ``contourf``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    x = np.asarray(result.x, dtype=np.float64) / 1000.0
    y = np.asarray(result.y, dtype=np.float64) / 1000.0
    lvl = np.asarray(result.level, dtype=np.float64)
    finite = lvl[np.isfinite(lvl)]
    top = float(np.ceil(np.max(finite) / 5.0) * 5.0) if finite.size else 100.0
    levels = np.arange(top - 30.0, top + 0.1, 5.0)
    # Mask non-finite cells (e.g. degenerate paths) so they render blank.
    masked = np.ma.masked_invalid(lvl)
    cf = ax.contourf(x, y, masked, **{"levels": levels, "cmap": "viridis", "extend": "both", **kwargs})
    ax.contour(x, y, masked, levels=levels, colors="k", linewidths=0.4, alpha=0.5)
    ax.figure.colorbar(cf, ax=ax, label=f"{'SEL' if result.metric == 'exposure' else 'LAmax'} [dB]")
    ax.set_xlabel("x [km]")
    ax.set_ylabel("y [km]")
    ax.set_title("Aircraft noise contour (ECAC Doc 29)")
    ax.set_aspect("equal", adjustable="box")
    return ax


# ---------------------------------------------------------------------------
# Speech transmission index (IEC 60268-16)
# ---------------------------------------------------------------------------






# ---------------------------------------------------------------------------
# Weighted single-number ratings (ISO 717-1 / ISO 717-2)
# ---------------------------------------------------------------------------


def _plot_rating(
    band_centers: np.ndarray,
    measured: np.ndarray,
    reference: np.ndarray,
    *,
    impact: bool,
    title: str,
    ylabel: str,
    measured_label: str = "Measured",
    ylim: tuple[float, float] | None = None,
    ax: Axes | None,
    **kwargs: Any,
) -> Axes:
    """Shared renderer for the shifted-reference rating figures.

    Draws the measured curve against the shifted reference and shades the
    unfavourable deviations: where the reference exceeds the measurement
    for airborne insulation and absorption (higher is better) and where the
    measurement exceeds the reference for impact sound (lower is better).
    Extra keyword arguments style the measured curve (its primary artist).
    """
    ax = ax if ax is not None else _new_axes()
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", measured_label)
    ax.plot(band_centers, measured, "o-", **kwargs)
    ax.plot(band_centers, reference, "s--", color=_C_REFERENCE,
            label="Shifted reference")
    unfavourable = _unfavourable_mask(measured, reference, impact)
    ax.fill_between(
        band_centers,
        measured,
        reference,
        where=unfavourable.tolist(),
        color=_C_SECONDARY,
        alpha=0.4,
        label="Unfavourable deviations",
        interpolate=True,
    )
    _freq_axis(ax, band_centers)
    ax.set_ylabel(ylabel)
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.set_title(title)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    return ax


def _unfavourable_mask(
    measured: np.ndarray, reference: np.ndarray, impact: bool
) -> np.ndarray:
    """Bands whose deviation is unfavourable.

    Airborne (ISO 717-1, higher is better): the reference exceeds the
    measurement.  Impact (ISO 717-2, lower is better): the measurement
    exceeds the reference (the opposite sign).
    """
    if impact:
        return np.asarray(measured > reference)
    return np.asarray(measured < reference)








def _annotate_impact_500(
    ax: Axes, band_centers: np.ndarray, reference: np.ndarray, rating: int
) -> None:
    """Mark the 500 Hz read value on the reference curve and, when the
    octave-band -5 dB reduction applies (ISO 717-2 Clause 4.3.2), annotate
    the rating as ``read - 5 dB`` so the figure stays normatively truthful.
    """
    if band_centers.size == 0:
        return
    idx = int(np.argmin(np.abs(band_centers - 500.0)))
    read_value = float(reference[idx])
    ax.plot(
        [band_centers[idx]],
        [read_value],
        marker="D",
        ls="",
        color=_C_REFERENCE,
        ms=9,
        mfc="none",
        mew=1.6,
        zorder=5,
        label=f"500 Hz read = {read_value:.0f} dB",
    )
    offset = rating - read_value
    if abs(offset) >= 0.5:  # octave-band -5 dB rule (Clause 4.3.2)
        ax.annotate(
            f"rating = {rating} dB = {read_value:.0f} - 5 dB (octave rule)",
            xy=(band_centers[idx], read_value),
            xytext=(0.0, -32.0),
            textcoords="offset points",
            ha="center",
            fontsize="small",
            arrowprops={"arrowstyle": "->", "color": _C_EDGE},
        )
    ax.legend(loc="best", fontsize="small")


def _require_rating_curve(
    result: "WeightedRatingResult | ImpactRatingResult",
) -> None:
    if (
        result.band_centers is None
        or result.measured is None
        or result.shifted_reference is None
    ):
        raise ValueError(
            "This rating result carries no band curve to plot (it was "
            "constructed without measured/reference data)."
        )




def _facade_x_axis(ax: Axes, freqs: "np.ndarray | None", n: int) -> np.ndarray:
    """Frequency x-axis when centres are known, else a labelled band index."""
    if freqs is None:
        x = np.arange(n, dtype=np.float64)
        ax.set_xticks(x)
        ax.set_xticklabels([f"Band {i + 1}" for i in range(n)], rotation=45, ha="right")
        ax.set_xlabel("Band")
        return x
    x = np.asarray(freqs, dtype=np.float64)
    _freq_axis(ax, x)
    return x






# ---------------------------------------------------------------------------
# Room acoustics (ISO 3382)
# ---------------------------------------------------------------------------




def _draw_decay_times(
    ax: Axes, positions: np.ndarray, result: RoomAcousticsResult, **kwargs: Any
) -> None:
    """Grouped EDT/T20/T30 bars, invalid bands hatched and greyed."""
    width = 0.27
    series = (
        ("EDT", result.edt, result.edt_valid, -width, _C_PRIMARY),
        ("T20", result.t20, result.t20_valid, 0.0, _C_SECONDARY),
        ("T30", result.t30, result.t30_valid, width, _C_TERTIARY),
    )
    for label, values, valid, offset, color in series:
        vals = np.asarray(values, dtype=np.float64)
        valid_arr = np.asarray(valid, dtype=bool)
        colors = [color if v else _C_MUTED for v in valid_arr]
        # Merge per-series defaults with the user kwargs (user wins) freshly
        # each iteration so an overriding label/color is not frozen by the
        # first band group.
        bar_kwargs = {"color": colors, "label": label, **kwargs}
        bars = ax.bar(
            positions + offset,
            np.nan_to_num(vals),
            width=width,
            **bar_kwargs,
        )
        _hatch_invalid(bars, ~valid_arr)


# ---------------------------------------------------------------------------
# Sound power (ISO 3744 / ISO 3741 / ISO 9614-2)
# ---------------------------------------------------------------------------




def _sound_power_designation(result: Any) -> str:
    """The standard designation matching a sound-power result's method.

    Distinguishes the reverberation-room (ISO 3741) and intensity (ISO 9614)
    determinations by their result types; the enveloping-surface pressure
    methods (:class:`~phonometry.sound_power.SoundPowerResult` and any other
    duck-typed result) fall back to ISO 3744/3746.
    """
    from ..emission.sound_power_intensity import SoundPowerIntensityResult
    from ..emission.sound_power_reverberation import ReverberationSoundPowerResult

    if isinstance(result, ReverberationSoundPowerResult):
        return "ISO 3741"
    if isinstance(result, SoundPowerIntensityResult):
        return "ISO 9614"
    return "ISO 3744/3746"


# ---------------------------------------------------------------------------
# Sound intensity (ISO 9614 / IEC 61043)
# ---------------------------------------------------------------------------


def _bar_width(positions: np.ndarray, k: float = 0.2) -> np.ndarray:
    """Per-bar widths for a *logarithmic* frequency axis.

    A constant linear width makes high-frequency bars almost invisible on
    a log axis (a 25 Hz-wide bar spans a third of an octave at 100 Hz but
    a thousandth of one at 10 kHz).  Scaling each width with its own centre
    frequency (``width_i = k * f_i``, the fractional-band style) keeps the
    *drawn* (log-space) width visually constant across the whole spectrum,
    so ``get_width() / f`` is the same constant ``k`` for every band.
    """
    return k * np.asarray(positions, dtype=np.float64)




# ---------------------------------------------------------------------------
# Schroeder decay curve (ISO 3382)
# ---------------------------------------------------------------------------




def _fit_segment(
    time: np.ndarray, level: np.ndarray, lo: float, hi: float
) -> np.ndarray | None:
    """Least-squares straight line over ``hi <= level <= lo``, over full time."""
    mask = (level <= lo) & (level >= hi) & np.isfinite(level)
    if int(np.count_nonzero(mask)) < 2:
        return None
    slope, intercept = np.polyfit(time[mask], level[mask], 1)
    return np.asarray(slope * time + intercept, dtype=np.float64)


# ---------------------------------------------------------------------------
# Impulse-response acquisition (ISO 18233)
# ---------------------------------------------------------------------------


def _time_axis(n: int, fs: int | None) -> tuple[np.ndarray, str]:
    """Sample times in seconds when ``fs`` is known, else sample index."""
    if fs:
        return np.arange(n) / float(fs), "Time [s]"
    return np.arange(n, dtype=np.float64), "Sample"




def plot_excitation(
    signal: "np.ndarray | Any",
    fs: int,
    *,
    kind: str = "sweep",
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes | np.ndarray:
    """Plot an ISO 18233 excitation signal (sweep or MLS).

    A documented helper for the raw arrays returned by
    :func:`~phonometry.sweep_signal` and :func:`~phonometry.mls_signal`, which
    stay plain :class:`numpy.ndarray` (they are meant for playback). For a
    swept sine the waveform and its spectrogram are drawn; for an MLS the first
    samples of the bipolar sequence and its (flat) magnitude spectrum.

    :param signal: The excitation samples (1D array-like).
    :param fs: Sample rate in Hz (for the time and frequency axes).
    :param kind: ``"sweep"`` (default) or ``"mls"``.
    :param ax: Existing axes for the top (time-domain) panel, or ``None`` for a
        fresh two-panel figure.
    :param kwargs: Forwarded to the time-domain ``plot`` call.
    :return: The time-domain axes (``ax`` given) or the array of two axes.
    """
    x = np.asarray(signal, dtype=np.float64)
    n = x.shape[-1]
    if n == 0:
        raise ValueError("excitation signal is empty; nothing to plot.")
    t = np.arange(n) / float(fs)
    color = kwargs.pop("color", _C_PRIMARY)

    two_panel = ax is None
    if two_panel:
        axes = _new_axes_column(2, figsize=(8.0, 6.0))
        ax_time = cast("Axes", axes[0])
    else:
        ax_time = cast("Axes", ax)

    if kind == "mls":
        show = min(n, 120)
        ax_time.step(np.arange(show), x[:show], where="mid", color=color, **kwargs)
        ax_time.set_xlabel("Sample")
        ax_time.set_ylabel("Amplitude")
        ax_time.set_ylim(-1.4, 1.4)
        ax_time.set_title(
            f"ISO 18233 MLS excitation (first {show} of {n} samples)"
        )
        ax_time.grid(True, alpha=0.3)
        if not two_panel:
            return ax_time
        spec = np.abs(np.fft.rfft(x))
        freqs = np.fft.rfftfreq(n, d=1.0 / fs)
        ax_f = axes[1]
        ac = spec[1:]
        denom = float(np.median(ac)) if ac.size else 1.0
        ax_f.semilogx(freqs[1:], 20.0 * np.log10(
                      np.maximum(ac, 1e-10) / (denom if denom > 0.0 else 1.0)),
                      color=_C_REFERENCE, lw=0.8)
        ax_f.set_xlabel("Frequency [Hz]")
        ax_f.set_ylabel("Magnitude [dB]")
        ax_f.set_title("Magnitude spectrum (flat)")
        ax_f.grid(True, which="both", alpha=0.3)
        return axes

    # Swept sine.
    ax_time.plot(t, x, color=color, lw=0.6, **kwargs)
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Amplitude")
    ax_time.set_title("ISO 18233 exponential sine sweep")
    ax_time.grid(True, alpha=0.3)
    if not two_panel:
        return ax_time
    ax_s = axes[1]
    nperseg = min(n, max(256, min(2048, n // 16)))
    ax_s.specgram(x, NFFT=nperseg, Fs=fs, noverlap=nperseg // 2, cmap="magma")
    ax_s.set_xlabel("Time [s]")
    ax_s.set_ylabel("Frequency [Hz]")
    ax_s.set_title("Spectrogram (exponential frequency rise)")
    return axes


# ---------------------------------------------------------------------------
# Surface scattering & diffusion (ISO 17497)
# ---------------------------------------------------------------------------










# ---------------------------------------------------------------------------
# Human vibration (ISO 8041-1 / ISO 2631 / ISO 5349 / Directive 2002/44/EC)
# ---------------------------------------------------------------------------








# ---------------------------------------------------------------------------
# Room-noise criteria (ANSI/ASA S12.2-2019)
# ---------------------------------------------------------------------------






# ---------------------------------------------------------------------------
# Age-related hearing threshold (ISO 7029)
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Noise-induced hearing loss (ISO 1999)
# ---------------------------------------------------------------------------






# ---------------------------------------------------------------------------
# Impulsive-sound prominence (NT ACOU 112)
# ---------------------------------------------------------------------------


















def _plot_band_level_bars(
    ax: Axes | None,
    levels: np.ndarray,
    frequencies: np.ndarray | None,
    total_level: float,
    *,
    ylabel: str,
    title: str,
    **kwargs: Any,
) -> Axes:
    """Per-band level bar chart with a band-summed total line (shared helper)."""
    ax = ax if ax is not None else _new_axes()
    lw = np.asarray(levels, dtype=np.float64)
    n = lw.size
    if frequencies is not None:
        labels = [f"{f:g}" for f in np.asarray(frequencies)]
        ax.set_xlabel("Frequency [Hz]")
    else:
        labels = [str(i + 1) for i in range(n)]
        ax.set_xlabel("Band")
    positions = np.arange(n)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(positions, lw, width=0.7, edgecolor=_C_EDGE, linewidth=0.6, **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.axhline(total_level, color=_C_REFERENCE, ls="--", lw=1.2,
               label=f"total {total_level:.1f} dB")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax










# ---------------------------------------------------------------------------
# Measurement uncertainty budget (GUM)
# ---------------------------------------------------------------------------






# ---------------------------------------------------------------------------
# Open-plan offices (ISO 3382-3)
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Outdoor sound propagation (ISO 9613-2)
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Impedance tube (ISO 10534-2)
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Occupational noise exposure (ISO 9612)
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Static airflow resistance (ISO 9053-1)
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Building performance prediction (EN 12354-1 / EN 12354-2)
# ---------------------------------------------------------------------------






# ---------------------------------------------------------------------------
# Field sound insulation spectra (ISO 16283-1 / ISO 16283-2)
# ---------------------------------------------------------------------------






def _plot_insulation_bands(
    curves: "Sequence[tuple[str, np.ndarray]]",
    *,
    ylabel: str,
    title: str,
    ax: Axes | None,
    **kwargs: Any,
) -> Axes:
    """Shared per-band insulation renderer (measurement bands are index-only).

    The ISO 16283 results do not carry their band centres, so the curves are
    drawn over band indices; user kwargs style the first (primary) curve
    only, mirroring :func:`plot_facade_insulation`.
    """
    ax = ax if ax is not None else _new_axes()
    n = curves[0][1].size
    x = np.arange(n, dtype=np.float64)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Band {i + 1}" for i in range(n)],
                       rotation=45, ha="right")
    ax.set_xlabel("Band")
    for index, (label, y) in enumerate(curves):
        opts: dict[str, Any] = {"label": label}
        if index == 0:
            opts.update(kwargs)
        ax.plot(x, y, "o-", **opts)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Building-acoustics measurement uncertainty (ISO 12999-1)
# ---------------------------------------------------------------------------




_ABSORPTION_QUANTITY_LABELS: Final = {
    "absorption_coefficient": "Sound absorption coefficient alpha_s",
    "equivalent_area": "Equivalent absorption area A_T [m2]",
    "practical_coefficient": "Practical absorption coefficient alpha_p",
}




