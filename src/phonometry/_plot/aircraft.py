#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the aircraft domain (lazy imports from result .plot())."""

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
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from ..aircraft.aircraft_noise import EPNLResult
    from ..aircraft.atmospheric_absorption import AircraftBandAttenuation
    from ..aircraft.airport_noise import FlyoverResult, NoiseContourResult, NpdLevelResult
    from ..aircraft.rotorcraft_noise import (
        FlightPathKinematics,
        MeanGroundPlaneResult,
        RotorcraftEventResult,
        RotorcraftHemisphere,
        RotorcraftNoiseContourResult,
        TerrainScreeningResult,
    )

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

    :param result: A :class:`~phonometry.aircraft.rotorcraft_noise.RotorcraftHemisphere`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param band: Band centre frequency to plot, in Hz (default: the loudest band).
    :param kwargs: Forwarded to ``plot``.
    :return: The axes.
    """
    from ..aircraft.rotorcraft_noise import hemisphere_source_level

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


def plot_flight_path_kinematics(
    result: "FlightPathKinematics", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Speed and angle profiles of a rotorcraft track (ECAC Doc 32).

    The ground speed and airspeed share the left axis; the path and bank
    angles share a right-hand axis.

    :param result: A
        :class:`~phonometry.aircraft.rotorcraft_noise.FlightPathKinematics`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the speed ``plot`` calls.
    :return: The (left) axes.
    """
    ax = ax if ax is not None else _new_axes()
    t = np.asarray(result.times, dtype=np.float64)
    ax.plot(t, result.airspeed, **{"color": _C_PRIMARY, "lw": 1.8,
            "label": "Airspeed $V_A$", **kwargs})
    ax.plot(t, result.ground_speed, **{"color": _C_SECONDARY, "lw": 1.4,
            "ls": "--", "label": "Ground speed $V_g$", **kwargs})
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Speed [m/s]")
    ax2 = ax.twinx()
    ax2.plot(t, result.path_angle, color=_C_TERTIARY, lw=1.4,
             label="Path angle $\\gamma$")
    ax2.plot(t, result.bank_angle, color=_C_MUTED, lw=1.4, ls=":",
             label="Bank angle $\\Phi$")
    ax2.set_ylabel("Angle [°]")
    lines = [*ax.get_lines(), *ax2.get_lines()]
    ax.legend(lines, [str(ln.get_label()) for ln in lines],
              loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.set_title("Rotorcraft flight-path kinematics (ECAC Doc 32)")
    ax.grid(True, alpha=0.3)
    return ax


def plot_rotorcraft_event(
    result: "RotorcraftEventResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """A-weighted level time history of a rotorcraft event (ECAC Doc 32).

    Draws ``L_A(t)`` at recorded time, marks ``LASmax``, shades the 10 dB-down
    window and annotates the integrated metrics.

    :param result: A
        :class:`~phonometry.aircraft.rotorcraft_noise.RotorcraftEventResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    t = np.asarray(result.times, dtype=np.float64)
    la = np.asarray(result.a_levels, dtype=np.float64)
    label = f"$L_A(t)$  (SEL {result.sel:.1f} dB(A)"
    if np.isfinite(result.epnl):
        label += f", EPNL {result.epnl:.1f} EPNdB"
    label += ")"
    ax.plot(t, la, **{"color": _C_PRIMARY, "lw": 1.6, "label": label, **kwargs})
    k = int(np.argmax(la))
    ax.plot(t[k], la[k], "o", color=_C_SECONDARY, ms=5,
            label=f"$L_{{ASmax}}$ = {result.la_max:.1f} dB(A)")
    window = la >= result.la_max - 10.0
    if np.any(window):
        idx = np.nonzero(window)[0]
        ax.axvspan(t[idx[0]], t[idx[-1]], color=_C_PRIMARY, alpha=0.08,
                   label="10 dB-down window")
    ax.set_xlabel("Recorded time [s]")
    ax.set_ylabel("A-weighted level [dB(A)]")
    ax.set_title("Rotorcraft flyover time history (ECAC Doc 32)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    return ax


def plot_rotorcraft_noise_contour(
    result: "RotorcraftNoiseContourResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Filled rotorcraft single-event noise contours over the ground plane.

    :param result: A
        :class:`~phonometry.aircraft.rotorcraft_noise.RotorcraftNoiseContourResult`.
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
    masked = np.ma.masked_invalid(lvl)
    cf = ax.contourf(x, y, masked,
                     **{"levels": levels, "cmap": "viridis", "extend": "both", **kwargs})
    ax.contour(x, y, masked, levels=levels, colors="k", linewidths=0.4, alpha=0.5)
    metric = "SEL" if result.metric == "exposure" else "$L_{ASmax}$"
    ax.figure.colorbar(cf, ax=ax, label=f"{metric} [dB(A)]")
    ax.set_xlabel("x [km]")
    ax.set_ylabel("y [km]")
    ax.set_title("Rotorcraft noise contour (ECAC Doc 32)")
    ax.set_aspect("equal", adjustable="box")
    return ax


def plot_mean_ground_plane(
    result: "MeanGroundPlaneResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Terrain section with its fitted mean ground plane (ECAC Doc 32 guidance).

    :param result: A
        :class:`~phonometry.aircraft.rotorcraft_noise.MeanGroundPlaneResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the terrain ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    d = np.asarray(result.distances, dtype=np.float64)
    z = np.asarray(result.heights, dtype=np.float64)
    ax.plot(d, z, **{"color": _C_PRIMARY, "lw": 1.8, "label": "Terrain profile",
            **kwargs})
    ax.fill_between(d, z, z.min() - 0.05 * np.ptp(z) - 0.5, color=_C_PRIMARY,
                    alpha=0.08)
    ax.plot(d, result.height(d), color=_C_SECONDARY, lw=1.6, ls="--",
            label=f"Mean ground plane (a = {result.slope:.3f})")
    ax.set_xlabel("Section distance [m]")
    ax.set_ylabel("Height [m]")
    ax.set_title("Mean ground plane (NORAH2 guidance Eq. 36-40)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    return ax


def plot_terrain_screening(
    result: "TerrainScreeningResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Terrain screening section: profile, line of sight and diffracted path.

    :param result: A
        :class:`~phonometry.aircraft.rotorcraft_noise.TerrainScreeningResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the terrain ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    d = np.asarray(result.distances, dtype=np.float64)
    z = np.asarray(result.heights, dtype=np.float64)
    src, rcv = result.source, result.receiver
    ax.plot(d, z, **{"color": _C_MUTED, "lw": 1.8, "label": "Terrain profile",
            **kwargs})
    floor = min(z.min(), src[1], rcv[1]) - 0.05 * max(np.ptp(z), 1.0) - 0.5
    ax.fill_between(d, z, floor, color=_C_MUTED, alpha=0.12)
    ax.plot([src[0], rcv[0]], [src[1], rcv[1]], color=_C_REFERENCE, lw=1.2,
            ls=":", label="Line of sight")
    if result.screened and result.diffraction_points.size:
        pts = np.vstack([[src[0], src[1]], result.diffraction_points,
                         [rcv[0], rcv[1]]])
        ax.plot(pts[:, 0], pts[:, 1], color=_C_PRIMARY, lw=1.8,
                label=f"Diffracted path (δ = {result.path_difference:.2f} m)")
        ax.plot(result.diffraction_points[:, 0], result.diffraction_points[:, 1],
                "v", color=_C_SECONDARY, ms=6, label="Diffraction edges")
    ax.plot(*src, "o", color=_C_PRIMARY, ms=7)
    ax.annotate("S", src, textcoords="offset points", xytext=(0, 8),
                ha="center", fontsize=10)
    ax.plot(*rcv, "s", color=_C_SECONDARY, ms=6)
    ax.annotate("R", rcv, textcoords="offset points", xytext=(0, 8),
                ha="center", fontsize=10)
    ax.set_xlabel("Section distance [m]")
    ax.set_ylabel("Height [m]")
    ax.set_title("Terrain screening (ECAC Doc 32 / NORAH2 guidance)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    return ax
