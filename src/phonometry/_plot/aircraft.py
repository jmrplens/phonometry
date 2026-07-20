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
    format_frequency_axis,
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

#: English and Spanish text for every fixed label/title/legend drawn by this
#: module's renderers.  English entries are byte-for-byte the original strings.
_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "win_10db": "10 dB-down window",
        "time_s": "Time [s]",
        "level_pndb": "Level [PNdB]",
        "sae_band": "SAE band",
        "puretone_midband": "Pure-tone mid-band (ISO 9613-1)",
        "freq_hz": "Frequency [Hz]",
        "atten_db": "Attenuation [dB]",
        "aircraft_abs_title": "Aircraft atmospheric absorption (SAE ARP 5534)",
        "tabulated": "Tabulated",
        "slant_distance": "Slant distance [m]",
        "event_level": "Event level [dB]",
        "npd_title": "Noise-power-distance curve (ECAC Doc 29)",
        "segment_index": "Segment index",
        "segment_metric": "Segment {metric} [dB]",
        "flyover_title": "Single-event segment contributions (ECAC Doc 29)",
        "polar_angle": "Polar angle θ [°]  (0° forward → 180° rearward)",
        "source_level_60m": "Source level at 60 m [dB]",
        "hemisphere_title": "Rotorcraft noise hemisphere directivity (ECAC Doc 32)",
        "contour_title": "Aircraft noise contour (ECAC Doc 29)",
        "airspeed": "Airspeed $V_A$",
        "ground_speed": "Ground speed $V_g$",
        "speed_ms": "Speed [m/s]",
        "path_angle": "Path angle $\\gamma$",
        "bank_angle": "Bank angle $\\Phi$",
        "angle_deg": "Angle [°]",
        "kinematics_title": "Rotorcraft flight-path kinematics (ECAC Doc 32)",
        "recorded_time": "Recorded time [s]",
        "a_level": "A-weighted level [dB(A)]",
        "rotor_event_title": "Rotorcraft flyover time history (ECAC Doc 32)",
        "rotor_contour_title": "Rotorcraft noise contour (ECAC Doc 32)",
        "terrain_profile": "Terrain profile",
        "mean_ground_plane": "Mean ground plane",
        "section_distance": "Section distance [m]",
        "height_m": "Height [m]",
        "mgp_title": "Mean ground plane (NORAH2 guidance Eq. 36-40)",
        "line_of_sight": "Line of sight",
        "diffracted_path": "Diffracted path",
        "diffraction_edges": "Diffraction edges",
        "screening_title": "Terrain screening (ECAC Doc 32 / NORAH2 guidance)",
    },
    "es": {
        "win_10db": "Ventana 10 dB por debajo",
        "time_s": "Tiempo [s]",
        "level_pndb": "Nivel [PNdB]",
        "sae_band": "Banda SAE",
        "puretone_midband": "Banda media de tono puro (ISO 9613-1)",
        "freq_hz": "Frecuencia [Hz]",
        "atten_db": "Atenuación [dB]",
        "aircraft_abs_title": "Absorción atmosférica de aeronaves (SAE ARP 5534)",
        "tabulated": "Tabulados",
        "slant_distance": "Distancia oblicua [m]",
        "event_level": "Nivel del evento [dB]",
        "npd_title": "Curva ruido-potencia-distancia (ECAC Doc 29)",
        "segment_index": "Índice de segmento",
        "segment_metric": "{metric} por segmento [dB]",
        "flyover_title": "Contribuciones por segmento de un evento único (ECAC Doc 29)",
        "polar_angle": "Ángulo polar θ [°]  (0° adelante → 180° atrás)",
        "source_level_60m": "Nivel de fuente a 60 m [dB]",
        "hemisphere_title": "Directividad del hemisferio de ruido de rotorcraft (ECAC Doc 32)",
        "contour_title": "Curvas de ruido de aeronaves (ECAC Doc 29)",
        "airspeed": "Velocidad del aire $V_A$",
        "ground_speed": "Velocidad respecto al suelo $V_g$",
        "speed_ms": "Velocidad [m/s]",
        "path_angle": "Ángulo de trayectoria $\\gamma$",
        "bank_angle": "Ángulo de alabeo $\\Phi$",
        "angle_deg": "Ángulo [°]",
        "kinematics_title": "Cinemática de la trayectoria de rotorcraft (ECAC Doc 32)",
        "recorded_time": "Tiempo registrado [s]",
        "a_level": "Nivel ponderado A [dB(A)]",
        "rotor_event_title": "Historia temporal de sobrevuelo de rotorcraft (ECAC Doc 32)",
        "rotor_contour_title": "Curvas de ruido de rotorcraft (ECAC Doc 32)",
        "terrain_profile": "Perfil del terreno",
        "mean_ground_plane": "Plano medio del suelo",
        "section_distance": "Distancia de la sección [m]",
        "height_m": "Altura [m]",
        "mgp_title": "Plano medio del suelo (guía NORAH2 Ec. 36-40)",
        "line_of_sight": "Línea de visión",
        "diffracted_path": "Trayectoria difractada",
        "diffraction_edges": "Bordes de difracción",
        "screening_title": "Apantallamiento por terreno (ECAC Doc 32 / guía NORAH2)",
    },
}


def _t(key: str, language: str) -> str:
    """Localised fixed string for ``key`` (English is the byte-identical default)."""
    return _STRINGS[language][key]


def plot_epnl(result: "EPNLResult", ax: Axes | None = None, *, language: str = "en",
              **kwargs: Any) -> Axes:
    """PNL and PNLT time histories with PNLTM and the 10 dB-down window.

    The perceived noise level and its tone-corrected counterpart are drawn
    against time; the maximum ``PNLTM`` is marked and the 10 dB-down integration
    band (records ``kF``..``kL``) is shaded, annotated with the EPNL.

    :param result: An :class:`~phonometry.aircraft_noise.EPNLResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the PNLT ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma, format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    t = np.asarray(result.times, dtype=np.float64)
    kf, kl = result.band_limits
    # Draw the shaded window first and below the curves (zorder=0), and use a
    # pale fill colour directly rather than a low alpha: the PDF vector backend
    # (svglib) does not preserve alpha, so a translucent fill would render solid
    # and hide the PNL/PNLT traces. A light face keeps both curves readable.
    ax.axvspan(t[kf], t[kl], facecolor="#d7eccb", edgecolor="none", zorder=0,
               label=_t("win_10db", language))
    ax.plot(t, np.asarray(result.pnl), color=_C_MUTED, lw=1.0, ls="--", label="PNL")
    ax.plot(t, np.asarray(result.pnlt), **{"color": _C_PRIMARY, "lw": 1.4, "label": "PNLT", **kwargs})
    km = int(np.argmax(np.asarray(result.pnlt)))
    ax.plot([t[km]], [result.pnltm], "o", color=_C_REFERENCE,
            label=f"PNLTM = {format_number(result.pnltm, language)} PNdB")
    ax.set_xlabel(_t("time_s", language))
    ax.set_ylabel(_t("level_pndb", language))
    ax.set_title(
        f"ICAO EPNL = {format_number(result.epnl, language)} EPNdB "
        f"(D = {decimal_comma(f'{result.duration_correction:+.1f}', language)} dB)"
    )
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax

def plot_aircraft_band_attenuation(
    result: "AircraftBandAttenuation", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """One-third-octave-band and pure-tone mid-band attenuation versus frequency.

    :param result: An
        :class:`~phonometry.aircraft_atmospheric_absorption.AircraftBandAttenuation`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the band-attenuation ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequency, dtype=np.float64)
    label = f"{_t('sae_band', language)} ({format_number(result.path_length, language, decimals=0)} m)"
    ax.plot(f, np.asarray(result.band_attenuation),
            **{"color": _C_PRIMARY, "lw": 1.6, "marker": "o", "ms": 3, "label": label, **kwargs})
    ax.plot(f, np.asarray(result.midband_attenuation), color=_C_SECONDARY, lw=1.0, ls="--",
            label=_t("puretone_midband", language))
    ax.set_xscale("log")
    ax.set_xlabel(_t("freq_hz", language))
    ax.set_ylabel(_t("atten_db", language))
    ax.set_title(_t("aircraft_abs_title", language))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper left", fontsize="small")
    format_frequency_axis(ax, float(f.min()), float(f.max()))
    localize_axes(ax, language)
    return ax

def plot_npd_level(result: "NpdLevelResult", ax: Axes | None = None, *, language: str = "en",
                   **kwargs: Any) -> Axes:
    """NPD event level versus slant distance (log axis), with the tabulated nodes.

    :param result: An :class:`~phonometry.airport_noise.NpdLevelResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the interpolated-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    d = np.asarray(result.distance, dtype=np.float64)
    lvl = np.asarray(result.level, dtype=np.float64)
    td = np.asarray(result.table_distances, dtype=np.float64)
    tl = np.asarray(result.table_levels, dtype=np.float64)
    label = f"NPD (P = {decimal_comma(f'{result.power:g}', language)})"
    ax.plot(d, lvl, **{"color": _C_PRIMARY, "lw": 1.6, "label": label, **kwargs})
    ax.plot(td, tl, "o", color=_C_REFERENCE, ms=4, label=_t("tabulated", language))
    ax.set_xscale("log")
    ax.set_xlabel(_t("slant_distance", language))
    ax.set_ylabel(_t("event_level", language))
    ax.set_title(_t("npd_title", language))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax

def plot_flyover(result: "FlyoverResult", ax: Axes | None = None, *, language: str = "en",
                 **kwargs: Any) -> Axes:
    """Per-segment contributions to a single-event level (ECAC Doc 29).

    Bars show each flight-path segment's event level; the dashed line marks the
    energy-summed total (SEL) or the maximum (LAmax).

    :param result: A :class:`~phonometry.airport_noise.FlyoverResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the bar call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

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
                   label=f"Total {metric} = {format_number(result.level, language)} dB")
    ax.set_xlabel(_t("segment_index", language))
    ax.set_ylabel(_t("segment_metric", language).format(metric=metric))
    ax.set_title(_t("flyover_title", language))
    ax.grid(True, axis="y", alpha=0.3)
    if np.isfinite(result.level):
        ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax

def plot_rotorcraft_hemisphere(
    result: "RotorcraftHemisphere", ax: Axes | None = None, *, band: float | None = None,
    language: str = "en", **kwargs: Any) -> Axes:
    """Fore-aft directivity section of a rotorcraft noise hemisphere (ECAC Doc 32).

    Plots the source level versus polar angle θ (0° forward → 180° rearward) in the
    vertical plane (azimuth φ = 0) for a single one-third-octave band.

    :param result: A :class:`~phonometry.aircraft.rotorcraft_noise.RotorcraftHemisphere`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param band: Band centre frequency to plot, in Hz (default: the loudest band).
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``plot``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes
    from ..aircraft.rotorcraft_noise import hemisphere_source_level

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    theta = np.linspace(float(result.polar[0]), float(result.polar[-1]), 181)
    grid = np.array([hemisphere_source_level(result, 0.0, t) for t in theta])
    idx = int(np.argmin(np.abs(freqs - band))) if band is not None else int(
        np.nanargmax(np.nansum(10.0 ** (grid / 10.0), axis=0)))
    ax.plot(theta, grid[:, idx], **{"color": _C_PRIMARY, "lw": 1.8,
            "label": f"{format_number(freqs[idx], language, decimals=0)} Hz (φ = 0°)", **kwargs})
    ax.set_xlabel(_t("polar_angle", language))
    ax.set_ylabel(_t("source_level_60m", language))
    ax.set_title(_t("hemisphere_title", language))
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax

def plot_noise_contour(result: "NoiseContourResult", ax: Axes | None = None, *,
                       language: str = "en", **kwargs: Any) -> Axes:
    """Filled single-event noise contours over the ground plane (ECAC Doc 29).

    :param result: A :class:`~phonometry.airport_noise.NoiseContourResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``contourf``.
    :return: The axes.
    """
    from .._i18n import localize_axes

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
    ax.set_title(_t("contour_title", language))
    ax.set_aspect("equal", adjustable="box")
    localize_axes(ax, language)
    return ax


def plot_flight_path_kinematics(
    result: "FlightPathKinematics", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any) -> Axes:
    """Speed and angle profiles of a rotorcraft track (ECAC Doc 32).

    The ground speed and airspeed share the left axis; the path and bank
    angles share a right-hand axis.

    :param result: A
        :class:`~phonometry.aircraft.rotorcraft_noise.FlightPathKinematics`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the speed ``plot`` calls.
    :return: The (left) axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    t = np.asarray(result.times, dtype=np.float64)
    ax.plot(t, result.airspeed, **{"color": _C_PRIMARY, "lw": 1.8,
            "label": _t("airspeed", language), **kwargs})
    ax.plot(t, result.ground_speed, **{"color": _C_SECONDARY, "lw": 1.4,
            "ls": "--", "label": _t("ground_speed", language), **kwargs})
    ax.set_xlabel(_t("time_s", language))
    ax.set_ylabel(_t("speed_ms", language))
    ax2 = ax.twinx()
    ax2.plot(t, result.path_angle, color=_C_TERTIARY, lw=1.4,
             label=_t("path_angle", language))
    ax2.plot(t, result.bank_angle, color=_C_MUTED, lw=1.4, ls=":",
             label=_t("bank_angle", language))
    ax2.set_ylabel(_t("angle_deg", language))
    lines = [*ax.get_lines(), *ax2.get_lines()]
    ax.legend(lines, [str(ln.get_label()) for ln in lines],
              loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.set_title(_t("kinematics_title", language))
    ax.grid(True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_rotorcraft_event(
    result: "RotorcraftEventResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any) -> Axes:
    """A-weighted level time history of a rotorcraft event (ECAC Doc 32).

    Draws ``L_A(t)`` at recorded time, marks ``LASmax``, shades the 10 dB-down
    window and annotates the integrated metrics.

    :param result: A
        :class:`~phonometry.aircraft.rotorcraft_noise.RotorcraftEventResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``plot``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    t = np.asarray(result.times, dtype=np.float64)
    la = np.asarray(result.a_levels, dtype=np.float64)
    label = f"$L_A(t)$  (SEL {format_number(result.sel, language)} dB(A)"
    if np.isfinite(result.epnl):
        label += f", EPNL {format_number(result.epnl, language)} EPNdB"
    label += ")"
    ax.plot(t, la, **{"color": _C_PRIMARY, "lw": 1.6, "label": label, **kwargs})
    k = int(np.argmax(la))
    ax.plot(t[k], la[k], "o", color=_C_SECONDARY, ms=5,
            label=f"$L_{{ASmax}}$ = {format_number(result.la_max, language)} dB(A)")
    window = la >= result.la_max - 10.0
    if np.any(window):
        idx = np.nonzero(window)[0]
        ax.axvspan(t[idx[0]], t[idx[-1]], color=_C_PRIMARY, alpha=0.08,
                   label=_t("win_10db", language))
    ax.set_xlabel(_t("recorded_time", language))
    ax.set_ylabel(_t("a_level", language))
    ax.set_title(_t("rotor_event_title", language))
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_rotorcraft_noise_contour(
    result: "RotorcraftNoiseContourResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any) -> Axes:
    """Filled rotorcraft single-event noise contours over the ground plane.

    :param result: A
        :class:`~phonometry.aircraft.rotorcraft_noise.RotorcraftNoiseContourResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``contourf``.
    :return: The axes.
    """
    from .._i18n import localize_axes

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
    ax.set_title(_t("rotor_contour_title", language))
    ax.set_aspect("equal", adjustable="box")
    localize_axes(ax, language)
    return ax


def plot_mean_ground_plane(
    result: "MeanGroundPlaneResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any) -> Axes:
    """Terrain section with its fitted mean ground plane (ECAC Doc 32 guidance).

    :param result: A
        :class:`~phonometry.aircraft.rotorcraft_noise.MeanGroundPlaneResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the terrain ``plot``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    d = np.asarray(result.distances, dtype=np.float64)
    z = np.asarray(result.heights, dtype=np.float64)
    ax.plot(d, z, **{"color": _C_PRIMARY, "lw": 1.8, "label": _t("terrain_profile", language),
            **kwargs})
    ax.fill_between(d, z, z.min() - 0.05 * np.ptp(z) - 0.5, color=_C_PRIMARY,
                    alpha=0.08)
    ax.plot(d, result.height(d), color=_C_SECONDARY, lw=1.6, ls="--",
            label=f"{_t('mean_ground_plane', language)} (a = {format_number(result.slope, language, decimals=3)})")
    ax.set_xlabel(_t("section_distance", language))
    ax.set_ylabel(_t("height_m", language))
    ax.set_title(_t("mgp_title", language))
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_terrain_screening(
    result: "TerrainScreeningResult", ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any) -> Axes:
    """Terrain screening section: profile, line of sight and diffracted path.

    :param result: A
        :class:`~phonometry.aircraft.rotorcraft_noise.TerrainScreeningResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the terrain ``plot``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    d = np.asarray(result.distances, dtype=np.float64)
    z = np.asarray(result.heights, dtype=np.float64)
    src, rcv = result.source, result.receiver
    ax.plot(d, z, **{"color": _C_MUTED, "lw": 1.8, "label": _t("terrain_profile", language),
            **kwargs})
    floor = min(z.min(), src[1], rcv[1]) - 0.05 * max(np.ptp(z), 1.0) - 0.5
    ax.fill_between(d, z, floor, color=_C_MUTED, alpha=0.12)
    ax.plot([src[0], rcv[0]], [src[1], rcv[1]], color=_C_REFERENCE, lw=1.2,
            ls=":", label=_t("line_of_sight", language))
    if result.screened and result.diffraction_points.size:
        pts = np.vstack([[src[0], src[1]], result.diffraction_points,
                         [rcv[0], rcv[1]]])
        ax.plot(pts[:, 0], pts[:, 1], color=_C_PRIMARY, lw=1.8,
                label=f"{_t('diffracted_path', language)} (δ = {format_number(result.path_difference, language, decimals=2)} m)")
        ax.plot(result.diffraction_points[:, 0], result.diffraction_points[:, 1],
                "v", color=_C_SECONDARY, ms=6, label=_t("diffraction_edges", language))
    ax.plot(*src, "o", color=_C_PRIMARY, ms=7)
    ax.annotate("S", src, textcoords="offset points", xytext=(0, 8),
                ha="center", fontsize=10)
    ax.plot(*rcv, "s", color=_C_SECONDARY, ms=6)
    ax.annotate("R", rcv, textcoords="offset points", xytext=(0, 8),
                ha="center", fontsize=10)
    ax.set_xlabel(_t("section_distance", language))
    ax.set_ylabel(_t("height_m", language))
    ax.set_title(_t("screening_title", language))
    ax.grid(True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    localize_axes(ax, language)
    return ax
