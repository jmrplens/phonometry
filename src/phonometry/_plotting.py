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

    from .absorption_rating import AbsorptionRatingResult
    from .absorption_uncertainty import AbsorptionUncertaintyResult
    from .airflow_resistance import StaticAirflowResult
    from .building_prediction import AirbornePredictionResult, ImpactPredictionResult
    from .building_uncertainty import BandUncertainty
    from .facade_prediction import FacadePredictionResult, RadiatedPowerResult
    from .flanking_transmission import VibrationReductionResult
    from .floor_covering_improvement import FloorCoveringImprovementResult
    from .reverberation_prediction import ReverberationModelResult
    from .dynamic_stiffness import DynamicStiffnessResult
    from .installed_structure_borne import InstalledSourceResult
    from .mechanical_mobility import MobilityResult
    from .structure_borne_power import StructureBornePowerResult
    from .transfer_stiffness import TransferStiffnessResult
    from .vibration_sound_power import VibrationSoundPowerResult
    from .impedance_tube import ImpedanceTubeResult
    from .insulation import (
        AirborneInsulationResult,
        FacadeInsulationResult,
        ImpactInsulationResult,
        ImpactRatingResult,
        WeightedRatingResult,
    )
    from .intensity import IntensityResult
    from .loudness_zwicker import ZwickerLoudness
    from .loudness_ecma import EcmaLoudness
    from .loudness_moore_glasberg import MooreGlasbergLoudness
    from .loudness_moore_glasberg_time import MooreGlasbergTimeVaryingLoudness
    from .occupational_exposure import ExposureResult
    from .open_plan import OpenPlanResult
    from .outdoor_propagation import OutdoorAttenuation
    from .road_absorption import InsituAbsorptionResult
    from .room_acoustics import DecayCurve, RoomAcousticsResult
    from .room_ir import ImpulseResponseResult
    from .hearing import AgeThresholdResult
    from .enclosed_space_absorption import ReverberationResult
    from .human_vibration import (
        DailyVibrationExposure,
        WeightedSpectrum,
        WeightingResponse,
    )
    from .noise_induced_hearing_loss import HtlanResult, NiptsResult
    from .multiple_shock_vibration import MultipleShockResult
    from .environmental_measurement import TonalAssessmentResult
    from .impulse_prominence import ImpulseProminenceResult
    from .room_noise import NCResult, RCResult
    from .scattering_diffusion import DiffusionResult, ScatteringResult
    from .sound_power import SoundPowerResult
    from .sound_power_intensity import SoundPowerIntensityResult
    from .sound_power_reverberation import ReverberationSoundPowerResult
    from .tonality_ecma import EcmaTonality
    from .roughness_ecma import EcmaRoughness
    from .sii import SIIResult
    from .sti import STIResult
    from .uncertainty import MonteCarloResult, UncertaintyResult

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


def plot_zwicker_loudness(
    result: ZwickerLoudness, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Specific loudness N'(z) over the Bark scale (ISO 532-1).

    When the result carries the time-varying loudness trace
    (``time`` / ``loudness_vs_time``) *and* ``ax`` is ``None``, a second
    panel with loudness vs time is added and an array of two axes is
    returned; otherwise (a stationary result, or an ``ax`` was supplied) a
    single axes is returned.

    :param result: A :class:`~phonometry.loudness_zwicker.ZwickerLoudness`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the specific-loudness line ``plot`` call.
    :return: The axes, or an array of two axes for time-varying input.
    """
    specific = np.asarray(result.specific, dtype=np.float64)
    bark = np.arange(1, specific.size + 1) * 0.1
    time_varying = (
        result.time is not None and result.loudness_vs_time is not None and ax is None
    )

    if time_varying:
        axes = _new_axes_column(2, figsize=(7.0, 6.0))
        ax_specific = cast("Axes", axes[0])
    else:
        ax_specific = ax if ax is not None else _new_axes()

    kwargs.setdefault("color", _C_PRIMARY)
    ax_specific.plot(bark, specific, **kwargs)
    ax_specific.fill_between(bark, specific, color=kwargs["color"], alpha=0.25)
    ax_specific.set_xlabel("Critical-band rate z [Bark]")
    ax_specific.set_ylabel("Specific loudness N' [sone/Bark]")
    ax_specific.set_xlim(0.0, bark[-1])
    ax_specific.set_ylim(bottom=0.0)
    ax_specific.set_title(
        f"ISO 532-1 loudness N = {result.loudness:.2f} sone "
        f"({result.loudness_level:.1f} phon)"
    )
    ax_specific.grid(True, alpha=0.3)

    if not time_varying:
        return ax_specific

    ax_time = cast("Axes", axes[1])
    time = np.asarray(result.time, dtype=np.float64)
    lvt = np.asarray(result.loudness_vs_time, dtype=np.float64)
    ax_time.plot(time, lvt, color=_C_TERTIARY, label="N(t)")
    if result.n5 is not None:
        ax_time.axhline(
            result.n5, color=_C_REFERENCE, ls="--", lw=1, label=f"N5={result.n5:.2f}"
        )
    if result.n10 is not None:
        ax_time.axhline(
            result.n10, color=_C_SECONDARY, ls=":", lw=1, label=f"N10={result.n10:.2f}"
        )
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Loudness N [sone]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.grid(True, alpha=0.3)
    ax_time.legend(loc="best", fontsize="small")
    return axes


# ---------------------------------------------------------------------------
# ECMA-418-2 Sottek loudness
# ---------------------------------------------------------------------------


def plot_ecma_loudness(
    result: EcmaLoudness, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Average specific loudness N'(z) and time-dependent loudness N(l).

    When ``ax`` is ``None`` a two-panel figure is drawn (specific loudness
    over the critical-band-rate scale and loudness vs time) and an array of
    two axes is returned; when ``ax`` is supplied only the specific-loudness
    panel is drawn on it and that single axes is returned.

    :param result: An :class:`~phonometry.loudness_ecma.EcmaLoudness`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the specific-loudness line ``plot`` call.
    :return: The axes, or an array of two axes.
    """
    specific = np.asarray(result.specific_loudness, dtype=np.float64)
    bark = np.asarray(result.bark, dtype=np.float64)
    two_panel = ax is None

    if two_panel:
        axes = _new_axes_column(2, figsize=(7.0, 6.0))
        ax_specific = cast("Axes", axes[0])
    else:
        ax_specific = cast("Axes", ax)

    kwargs.setdefault("color", _C_PRIMARY)
    ax_specific.plot(bark, specific, **kwargs)
    ax_specific.fill_between(bark, specific, color=kwargs["color"], alpha=0.25)
    ax_specific.set_xlabel("Critical-band rate z [Bark_HMS]")
    ax_specific.set_ylabel("Specific loudness N' [sone_HMS/Bark_HMS]")
    ax_specific.set_xlim(0.0, bark[-1])
    ax_specific.set_ylim(bottom=0.0)
    ax_specific.set_title(f"ECMA-418-2 loudness N = {result.loudness:.2f} sone_HMS")
    ax_specific.grid(True, alpha=0.3)

    if not two_panel:
        return ax_specific

    ax_time = cast("Axes", axes[1])
    time = np.asarray(result.time, dtype=np.float64)
    lvt = np.asarray(result.loudness_vs_time, dtype=np.float64)
    ax_time.plot(time, lvt, color=_C_TERTIARY, label="N(l)")
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Loudness N [sone_HMS]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.grid(True, alpha=0.3)
    ax_time.legend(loc="best", fontsize="small")
    return axes


# ---------------------------------------------------------------------------
# ISO 532-2 Moore-Glasberg loudness
# ---------------------------------------------------------------------------


def plot_moore_glasberg_loudness(
    result: MooreGlasbergLoudness, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Specific loudness N'(i) over the ERB-number (Cam) scale (ISO 532-2).

    :param result: A
        :class:`~phonometry.loudness_moore_glasberg.MooreGlasbergLoudness`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the specific-loudness line ``plot`` call.
    :return: The axes.
    """
    specific = np.asarray(result.specific, dtype=np.float64)
    erb_number = np.asarray(result.erb_number, dtype=np.float64)
    ax = ax if ax is not None else _new_axes()

    kwargs.setdefault("color", _C_PRIMARY)
    ax.plot(erb_number, specific, **kwargs)
    ax.fill_between(erb_number, specific, color=kwargs["color"], alpha=0.25)
    ax.set_xlabel("ERB number [Cam]")
    ax.set_ylabel("Specific loudness N' [sone/Cam]")
    ax.set_xlim(erb_number[0], erb_number[-1])
    ax.set_ylim(bottom=0.0)
    ax.set_title(
        f"ISO 532-2 loudness N = {result.loudness:.2f} sone "
        f"({result.loudness_level:.1f} phon)"
    )
    ax.grid(True, alpha=0.3)
    return ax


def plot_moore_glasberg_time_loudness(
    result: MooreGlasbergTimeVaryingLoudness, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Short-term and long-term loudness against time (ISO 532-3).

    :param result: A
        :class:`~phonometry.loudness_moore_glasberg_time.MooreGlasbergTimeVaryingLoudness`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the long-term-loudness line ``plot`` call.
    :return: The axes.
    """
    time = np.asarray(result.time, dtype=np.float64)
    stl = np.asarray(result.short_term_loudness, dtype=np.float64)
    ltl = np.asarray(result.long_term_loudness, dtype=np.float64)
    ax = ax if ax is not None else _new_axes()

    ax.plot(time, stl, color=_C_PRIMARY_LIGHT, lw=1.0, label="Short-term loudness")
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("lw", 1.8)
    ax.plot(time, ltl, label="Long-term loudness", **kwargs)
    ax.axhline(result.n_max, color=_C_REFERENCE, ls="--", lw=1.0, alpha=0.7)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Loudness [sone]")
    if time.size:
        ax.set_xlim(time[0], time[-1])
    ax.set_ylim(bottom=0.0)
    ax.set_title(
        f"ISO 532-3 peak long-term loudness N = {result.n_max:.2f} sone "
        f"({result.loudness_level_max:.1f} phon)"
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax


def plot_ecma_tonality(
    result: EcmaTonality, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Average specific tonality T'(z) and time-dependent tonality T(l).

    When ``ax`` is ``None`` a two-panel figure is drawn (specific tonality over
    the critical-band-rate scale and tonality vs time) and an array of two axes
    is returned; when ``ax`` is supplied only the specific-tonality panel is
    drawn on it and that single axes is returned.

    :param result: An :class:`~phonometry.tonality_ecma.EcmaTonality`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the specific-tonality line ``plot`` call.
    :return: The axes, or an array of two axes.
    """
    specific = np.asarray(result.specific_tonality, dtype=np.float64)
    bark = np.asarray(result.bark, dtype=np.float64)
    two_panel = ax is None

    if two_panel:
        axes = _new_axes_column(2, figsize=(7.0, 6.0))
        ax_specific = cast("Axes", axes[0])
    else:
        ax_specific = cast("Axes", ax)

    # Tonality's per-metric identity color is red across the documentation
    # figures (roughness is brown); kept literal on purpose, see the module
    # color-constant note.
    kwargs.setdefault("color", "#d62728")
    ax_specific.plot(bark, specific, **kwargs)
    ax_specific.fill_between(bark, specific, color=kwargs["color"], alpha=0.25)
    ax_specific.set_xlabel("Critical-band rate z [Bark_HMS]")
    ax_specific.set_ylabel("Specific tonality T' [tu_HMS]")
    ax_specific.set_xlim(0.0, bark[-1])
    ax_specific.set_ylim(bottom=0.0)
    ax_specific.set_title(f"ECMA-418-2 tonality T = {result.tonality:.2f} tu_HMS")
    ax_specific.grid(True, alpha=0.3)

    if not two_panel:
        return ax_specific

    ax_time = cast("Axes", axes[1])
    time = np.asarray(result.time, dtype=np.float64)
    tvt = np.asarray(result.tonality_vs_time, dtype=np.float64)
    ax_time.plot(time, tvt, color=_C_QUATERNARY, label="T(l)")
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Tonality T [tu_HMS]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.grid(True, alpha=0.3)
    ax_time.legend(loc="best", fontsize="small")
    return axes


def plot_ecma_roughness(
    result: EcmaRoughness, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Time-dependent roughness R(l50) and a specific-roughness heatmap.

    When ``ax`` is ``None`` a two-panel figure is drawn (roughness vs time and
    a specific-roughness R'(l50, z) heatmap over the critical-band-rate scale)
    and an array of two axes is returned; when ``ax`` is supplied only the
    time-dependent roughness is drawn on it and that single axes is returned.

    :param result: An :class:`~phonometry.roughness_ecma.EcmaRoughness`.
    :param ax: Existing axes to draw on, or ``None`` to create a figure.
    :param kwargs: Forwarded to the roughness-vs-time line ``plot`` call.
    :return: The axes, or an array of two axes.
    """
    time = np.asarray(result.time, dtype=np.float64)
    rvt = np.asarray(result.roughness_vs_time, dtype=np.float64)
    two_panel = ax is None

    if two_panel:
        axes = _new_axes_column(2, figsize=(7.0, 6.0))
        ax_time = cast("Axes", axes[0])
    else:
        ax_time = cast("Axes", ax)

    # Roughness's per-metric identity color is brown across the documentation
    # figures (tonality is red); kept literal on purpose, see the module
    # color-constant note.
    kwargs.setdefault("color", "#8c564b")
    ax_time.plot(time, rvt, **kwargs)
    ax_time.fill_between(time, rvt, color=kwargs["color"], alpha=0.25)
    ax_time.set_xlabel("Time [s]")
    ax_time.set_ylabel("Roughness R [asper]")
    ax_time.set_ylim(bottom=0.0)
    ax_time.set_title(f"ECMA-418-2 roughness R = {result.roughness:.2f} asper")
    ax_time.grid(True, alpha=0.3)

    if not two_panel:
        return ax_time

    ax_heat = cast("Axes", axes[1])
    bark = np.asarray(result.bark, dtype=np.float64)
    spec = np.asarray(result.specific_roughness_vs_time, dtype=np.float64)
    if time.size >= 2 and spec.size:
        mesh = ax_heat.pcolormesh(time, bark, spec.T, cmap="magma", shading="auto")
        ax_heat.figure.colorbar(mesh, ax=ax_heat, label="R' [asper/Bark_HMS]")
    ax_heat.set_xlabel("Time [s]")
    ax_heat.set_ylabel("Critical-band rate z [Bark_HMS]")
    return axes


# ---------------------------------------------------------------------------
# Speech transmission index (IEC 60268-16)
# ---------------------------------------------------------------------------


def plot_sti(result: STIResult, ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Per-band modulation transfer index bars with the STI and rating.

    :param result: A :class:`~phonometry.sti.STIResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    mti = np.asarray(result.mti, dtype=np.float64)
    positions = np.arange(mti.size)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(positions, mti, **kwargs)
    if mti.size == len(_STI_BAND_CENTERS):
        _band_axis(ax, np.asarray(_STI_BAND_CENTERS))
    else:
        ax.set_xticks(positions)
        ax.set_xlabel("Band")
    ax.set_ylabel("Modulation transfer index MTI")
    ax.set_ylim(0.0, 1.0)
    ax.set_title(f"IEC 60268-16 STI = {result.sti:.2f}  (rating {result.rating})")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


def plot_sii(result: "SIIResult", ax: Axes | None = None, **kwargs: Any) -> Axes:
    """Per-band audibility and its importance-weighted contribution to the SII.

    :param result: A :class:`~phonometry.sii.SIIResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the weighted-contribution :meth:`bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    audibility = np.asarray(result.band_audibility, dtype=np.float64)
    contribution = audibility * np.asarray(result.band_importance, dtype=np.float64)
    positions = _band_axis(ax, freqs)
    ax.bar(positions, audibility, color=_C_PRIMARY_LIGHT,
           label="Band audibility $A_i$")
    kwargs.setdefault("color", _C_PRIMARY)
    # A fully masked speech signal (SII = 0) has an all-zero contribution;
    # keep the zero bars rather than dividing 0/0 into NaN.
    peak = float(contribution.max()) if contribution.size else 0.0
    scaled = contribution / peak if peak > 0.0 else contribution
    ax.bar(positions, scaled, width=0.5,
           label=r"Importance-weighted $I_i A_i$ (scaled)", **kwargs)
    ax.set_ylabel("Band audibility")
    ax.set_ylim(0.0, 1.0)
    ax.set_title(f"ANSI S3.5 SII = {result.sii:.3f}")
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


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


def plot_weighted_rating(
    result: "WeightedRatingResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Airborne rating curve vs shifted reference (ISO 717-1).

    :param result: A :class:`~phonometry.insulation.WeightedRatingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    _require_rating_curve(result)
    return _plot_rating(
        np.asarray(result.band_centers, dtype=np.float64),
        np.asarray(result.measured, dtype=np.float64),
        np.asarray(result.shifted_reference, dtype=np.float64),
        impact=False,
        title=(
            f"ISO 717-1 Rw (C={result.c:+d}; Ctr={result.ctr:+d}) = "
            f"{result.rating} dB  (Sigma unfav. = {result.unfavourable_sum:.1f} dB)"
        ),
        ylabel="Sound reduction index [dB]",
        ax=ax,
        **kwargs,
    )


def plot_impact_rating(
    result: "ImpactRatingResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Impact rating curve vs shifted reference (ISO 717-2).

    The drawn shifted-reference curve is the normatively honest ``ref -
    shift``; for octave-band data the rating is that curve read at 500 Hz
    *minus 5 dB* (Clause 4.3.2), so the plot marks the 500 Hz read value on
    the (undistorted) curve and annotates the -5 dB reduction rather than
    pulling the curve down to the rating.

    :param result: An :class:`~phonometry.insulation.ImpactRatingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    _require_rating_curve(result)
    band_centers = np.asarray(result.band_centers, dtype=np.float64)
    reference = np.asarray(result.shifted_reference, dtype=np.float64)
    ax = _plot_rating(
        band_centers,
        np.asarray(result.measured, dtype=np.float64),
        reference,
        impact=True,
        # The rated quantity depends on the input (Ln,w, L'n,w or L'nT,w);
        # the dataclass does not carry which, so the figure uses the neutral
        # "impact rating" label rather than hard-coding one specific symbol.
        title=(
            f"ISO 717-2 impact rating (CI={result.ci:+d}) = {result.rating} dB"
            f"  (Sigma unfav. = {result.unfavourable_sum:.1f} dB)"
        ),
        ylabel="Impact sound pressure level [dB]",
        ax=ax,
        **kwargs,
    )
    _annotate_impact_500(ax, band_centers, reference, int(result.rating))
    return ax


def plot_weighted_absorption(
    result: "AbsorptionRatingResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Practical absorption curve vs the shifted reference (ISO 11654:1997).

    Draws the practical coefficients ``alpha_p`` against the shifted reference
    curve and shades the unfavourable deviations (measured below the shifted
    reference, Clause 4.2) through the shared rating renderer.

    :param result: An
        :class:`~phonometry.absorption_rating.AbsorptionRatingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    return _plot_rating(
        np.asarray(result.band_centers, dtype=np.float64),
        np.asarray(result.measured, dtype=np.float64),
        np.asarray(result.shifted_reference, dtype=np.float64),
        impact=False,
        title=(
            f"ISO 11654 alpha_w = {result.rating_label}  "
            f"(class {result.absorption_class}, "
            f"Sigma unfav. = {result.unfavourable_sum:.2f})"
        ),
        ylabel="Sound absorption coefficient",
        measured_label="Practical alpha_p",
        ylim=(0.0, 1.05),
        ax=ax,
        **kwargs,
    )


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


def plot_facade_insulation(
    result: "FacadeInsulationResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-band façade sound-insulation profile (ISO 16283-3).

    Draws the standardized level difference ``D2m,nT`` first, then the
    other available quantities (``D2m``, ``D2m,n``, ``R'``) against
    frequency. Works for
    :class:`~phonometry.insulation.FacadeInsulationResult`.

    :param result: A façade result exposing ``d_2m``, ``d_2m_nt``,
        ``d_2m_n``, ``r_prime`` and (optionally) ``frequencies``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the primary ``D2m,nT`` curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    dnt = np.asarray(result.d_2m_nt, dtype=np.float64)
    n = dnt.size
    x = _facade_x_axis(ax, getattr(result, "frequencies", None), n)

    # D2m,nT first so it is lines[0]; other quantities follow when present.
    curves = [("$D_{2m,nT}$", dnt)]
    curves.append(("$D_{2m}$", np.asarray(result.d_2m, dtype=np.float64)))
    if result.d_2m_n is not None:
        curves.append(("$D_{2m,n}$", np.asarray(result.d_2m_n, dtype=np.float64)))
    if result.r_prime is not None:
        curves.append(("$R'$", np.asarray(result.r_prime, dtype=np.float64)))
    # Forward user kwargs to the primary D2m,nT curve only, so styling kwargs
    # (label=, color=) neither collide with the per-curve labels nor make the
    # companion curves indistinguishable.
    for index, (label, y) in enumerate(curves):
        opts: dict[str, Any] = {"label": label}
        if index == 0:
            opts.update(kwargs)
        ax.plot(x, y, "o-", **opts)

    ax.set_ylabel("Level difference / reduction index [dB]")
    ax.set_title("Façade sound insulation (ISO 16283-3)")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax


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


def plot_facade_prediction(
    result: "FacadePredictionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Predicted façade insulation profile (EN 12354-3:2000).

    Draws the per-element partial indices ``Rp = -10 lg τ`` as thin dashed
    lines, then the façade apparent reduction ``R'`` and the standardized
    level difference ``D2m,nT`` as bold curves, against frequency. Works for
    :class:`~phonometry.facade_prediction.FacadePredictionResult`.

    :param result: A façade prediction result exposing ``r_prime``,
        ``d_2m_nt``, ``element_r`` and (optionally) ``frequencies``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the primary ``R'`` curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    r_prime = np.asarray(result.r_prime, dtype=np.float64)
    n = r_prime.size
    x = _facade_x_axis(ax, result.frequencies, n)

    for name, rp in result.element_r.items():
        ax.plot(x, np.asarray(rp, dtype=np.float64), "--", lw=0.9, alpha=0.6, label=name)

    opts: dict[str, Any] = {"label": "$R'$", "color": "black", "lw": 2.0}
    opts.update(kwargs)
    ax.plot(x, r_prime, "o-", **opts)
    ax.plot(
        x,
        np.asarray(result.d_2m_nt, dtype=np.float64),
        "s-",
        color="tab:blue",
        lw=2.0,
        label="$D_{2m,nT}$",
    )

    ax.set_ylabel("Reduction index / level difference [dB]")
    ax.set_title("Façade insulation prediction (EN 12354-3)")
    ax.legend(loc="best", fontsize="small", ncol=2)
    ax.grid(True, alpha=0.3)
    return ax


def plot_radiated_power(
    result: "RadiatedPowerResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Radiated sound power level ``LW`` per band (EN 12354-4:2000).

    Draws the segment radiated power level as bars, annotating the A-weighted
    single number when available. Works for
    :class:`~phonometry.facade_prediction.RadiatedPowerResult`.

    :param result: A :class:`~phonometry.facade_prediction.RadiatedPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the ``bar`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    l_w = np.asarray(result.l_w, dtype=np.float64)
    n = l_w.size
    positions = np.arange(n, dtype=np.float64)
    if result.frequencies is None:
        labels = [f"Band {i + 1}" for i in range(n)]
    else:
        labels = [_format_freq(f) for f in np.asarray(result.frequencies, dtype=np.float64)]

    opts: dict[str, Any] = {"color": "tab:red", "alpha": 0.8, "label": "$L_W$"}
    opts.update(kwargs)
    ax.bar(positions, l_w, **opts)
    _band_axis(ax, labels, xlabel="Frequency [Hz]")

    if result.l_w_dba is not None:
        ax.axhline(
            result.l_w_dba,
            color="black",
            ls="--",
            lw=1.2,
            label=f"$L_{{WA}}$ = {result.l_w_dba:.1f} dB(A)",
        )
    ax.set_ylabel("Radiated sound power level [dB]")
    ax.set_title("Radiated sound power (EN 12354-4)")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Room acoustics (ISO 3382)
# ---------------------------------------------------------------------------


def plot_room_acoustics(
    result: RoomAcousticsResult, ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Per-band decay times (EDT/T20/T30) and clarity (C50/C80).

    The first panel shows the three decay times as grouped bars per band,
    invalid bands (failing the ISO 3382 evaluation-range criterion) hatched
    and greyed; the second panel shows C50 and C80.  When ``ax`` is given
    the two series are drawn on that single axes (times only) so the plot
    can be composed.

    :param result: A :class:`~phonometry.room_acoustics.RoomAcousticsResult`.
    :param ax: Existing axes for a single-panel (decay-times only) plot, or
        ``None`` to create the full two-panel figure.
    :return: The axes, or an array of two axes for the default figure.
    """
    freq = result.frequency
    n = np.asarray(result.t30, dtype=np.float64).size
    if freq is None:
        centers = np.arange(n, dtype=np.float64)
        labels = ["Broadband"] * n
        use_freq_axis = False
    else:
        centers = np.asarray(freq, dtype=np.float64)
        labels = [_format_freq(f) for f in centers]
        use_freq_axis = True

    positions = np.arange(n, dtype=np.float64)
    single = ax is not None
    if ax is not None:
        ax_times = ax
    else:
        axes = _new_axes_column(2, figsize=(7.5, 6.0), sharex=True)
        ax_times = cast("Axes", axes[0])

    _draw_decay_times(ax_times, positions, result, **kwargs)
    ax_times.set_ylabel("Reverberation time [s]")
    ax_times.set_title("ISO 3382 decay times and clarity")
    _band_axis(ax_times, labels, xlabel=None)
    ax_times.grid(True, axis="y", alpha=0.3)
    ax_times.legend(loc="best", fontsize="small")

    if single:
        if use_freq_axis:
            ax_times.set_xlabel("Frequency [Hz]")
        return ax_times

    ax_clarity = cast("Axes", axes[1])
    ax_clarity.plot(
        positions,
        np.asarray(result.c50, dtype=np.float64),
        "o-",
        color=_C_TERTIARY,
        label="C50",
    )
    ax_clarity.plot(
        positions,
        np.asarray(result.c80, dtype=np.float64),
        "s--",
        color=_C_QUATERNARY,
        label="C80",
    )
    ax_clarity.set_ylabel("Clarity [dB]")
    _band_axis(
        ax_clarity, labels, xlabel="Frequency [Hz]" if use_freq_axis else "Band"
    )
    ax_clarity.grid(True, alpha=0.3)
    ax_clarity.legend(loc="best", fontsize="small")
    return axes


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


def plot_sound_power(
    result: (
        "SoundPowerResult | ReverberationSoundPowerResult"
        " | SoundPowerIntensityResult | Any"
    ),
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes:
    """Sound power level spectrum with the A-weighted total annotated.

    Works for :class:`~phonometry.sound_power.SoundPowerResult`,
    :class:`~phonometry.sound_power_reverberation.ReverberationSoundPowerResult`
    and :class:`~phonometry.sound_power_intensity.SoundPowerIntensityResult`;
    for the intensity (scanning) variant the bands where the net power is
    non-positive (``negative_band``) are hatched and greyed as unusable.

    :param result: A sound-power result object exposing
        ``sound_power_level``, ``sound_power_level_a`` and (optionally)
        ``frequencies`` and ``negative_band``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the band :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    lw = np.asarray(result.sound_power_level, dtype=np.float64)
    n = lw.size
    freqs = getattr(result, "frequencies", None)
    if freqs is None:
        positions = _band_axis(
            ax, [f"Band {i + 1}" for i in range(n)], xlabel="Band"
        )
    else:
        positions = _band_axis(ax, np.asarray(freqs, dtype=np.float64))

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
    kwargs.setdefault("color", colors)
    bars = ax.bar(positions, np.nan_to_num(lw), **kwargs)
    _hatch_invalid(bars, neg)

    ax.set_ylabel("Sound power level LW [dB]")
    designation = _sound_power_designation(result)
    lwa = float(result.sound_power_level_a)
    if np.isfinite(lwa):
        ax.set_title(f"{designation} sound power spectrum  (LWA = {lwa:.1f} dB(A))")
    else:
        ax.set_title(f"{designation} sound power spectrum")
    if np.any(neg):
        ax.plot([], [], color=_C_MUTED, marker="s", ls="", label="Non-positive band")
    if np.any(neg) or "label" in kwargs:
        ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


def _sound_power_designation(result: Any) -> str:
    """The standard designation matching a sound-power result's method.

    Distinguishes the reverberation-room (ISO 3741) and intensity (ISO 9614)
    determinations by their result types; the enveloping-surface pressure
    methods (:class:`~phonometry.sound_power.SoundPowerResult` and any other
    duck-typed result) fall back to ISO 3744/3746.
    """
    from .sound_power_intensity import SoundPowerIntensityResult
    from .sound_power_reverberation import ReverberationSoundPowerResult

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


def plot_intensity(
    result: IntensityResult, ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Pressure vs intensity level per band with the pressure-intensity index.

    Draws Lp and LI per band and, on a twin axis, the per-band
    pressure-intensity index ``Lp - LI`` (the reactivity indicator); the
    total index is annotated in the title.

    :param result: An :class:`~phonometry.intensity.IntensityResult` with
        per-band data (obtained by requesting a band ``fraction``).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the pressure-level curve ``plot`` call.
    :return: The axes.
    :raises ValueError: If the result carries no per-band data.
    """
    if result.frequency is None:
        raise ValueError(
            "plot() needs per-band intensity data; call sound_intensity(...) "
            "with a 'fraction' to obtain it."
        )
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequency, dtype=np.float64)
    lp = np.asarray(result.pressure_level, dtype=np.float64)
    li = np.asarray(result.intensity_level, dtype=np.float64)
    index = np.asarray(result.pressure_intensity_index, dtype=np.float64)

    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Pressure level Lp")
    ax.plot(freqs, lp, "o-", **kwargs)
    ax.plot(freqs, li, "s--", color=_C_REFERENCE, label="Intensity level LI")
    _freq_axis(ax, freqs)
    ax.set_ylabel("Level [dB]")
    ax.grid(True, which="both", alpha=0.3)

    twin = ax.twinx()
    twin.bar(
        freqs,
        index,
        width=_bar_width(freqs),
        color=_C_TERTIARY,
        alpha=0.25,
        label="δpI = Lp - LI",
    )
    twin.set_ylabel("Pressure-intensity index δpI [dB]")

    lines, labels = ax.get_legend_handles_labels()
    tlines, tlabels = twin.get_legend_handles_labels()
    ax.legend(lines + tlines, labels + tlabels, loc="best", fontsize="small")
    ax.set_title(
        "ISO 9614 Lp vs LI  "
        f"(total δpI = {result.total_pressure_intensity_index:.1f} dB)"
    )
    return ax


# ---------------------------------------------------------------------------
# Schroeder decay curve (ISO 3382)
# ---------------------------------------------------------------------------


def plot_decay_curve(
    result: DecayCurve, ax: Axes | None = None, fits: bool = True, **kwargs: Any
) -> Axes:
    """Schroeder decay curve with optional straight T-fit overlays.

    :param result: A :class:`~phonometry.room_acoustics.DecayCurve`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param fits: Overlay the EDT (0..-10 dB), T20 (-5..-25 dB) and T30
        (-5..-35 dB) straight-line fits computed from the curve's own data.
    :param kwargs: Forwarded to the decay-curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    time = np.asarray(result.time, dtype=np.float64)
    level = np.asarray(result.level, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Schroeder decay")
    ax.plot(time, level, **kwargs)

    if fits:
        for label, lo, hi, style in (
            ("EDT", 0.0, -10.0, "-"),
            ("T20", -5.0, -25.0, "--"),
            ("T30", -5.0, -35.0, "-."),
        ):
            fit = _fit_segment(time, level, lo, hi)
            if fit is not None:
                ax.plot(time, fit, style, lw=1, alpha=0.8, label=f"{label} fit")

    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Level re steady state [dB]")
    ax.set_ylim(top=3.0)
    ax.set_xlim(left=0.0, right=float(time[-1]) if time.size else None)
    band = result.band
    title = "ISO 3382 Schroeder decay curve"
    if band is not None:
        title += f"  ({_format_freq(float(band))} Hz band)"
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    return ax


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


def plot_impulse_response(
    result: "ImpulseResponseResult", ax: Axes | None = None, **kwargs: Any
) -> Axes | np.ndarray:
    """Impulse-response waveform and its log-magnitude / Schroeder decay.

    Two stacked panels: the (peak-normalised) time-domain waveform on top and,
    below it, the log-magnitude envelope in dB with the Schroeder
    backward-integrated energy-decay curve overlaid. With ``ax`` given, only
    the decay panel is drawn on it.

    :param result: An :class:`~phonometry.room_ir.ImpulseResponseResult`.
    :param ax: Existing axes for the decay panel, or ``None`` for a fresh
        two-panel figure.
    :param kwargs: Forwarded to the waveform / envelope ``plot`` calls.
    :return: The decay-panel axes (``ax`` given) or the array of two axes.
    """
    h = np.asarray(result.ir, dtype=np.float64)
    n = h.shape[-1]
    if n == 0:
        raise ValueError("impulse response is empty; nothing to plot.")
    time, xlabel = _time_axis(n, result.fs)
    peak = float(np.max(np.abs(h)))
    tiny = np.finfo(np.float64).tiny
    norm = peak if peak > 0.0 else 1.0
    env_db = 20.0 * np.log10(np.maximum(np.abs(h), tiny) / norm)
    # Schroeder backward integration of the squared IR (broadband).
    energy = np.cumsum(h[::-1] ** 2)[::-1]
    total = float(energy[0]) if energy.size else 0.0
    edc_db = 10.0 * np.log10(np.maximum(energy, tiny) / (total if total > 0.0 else 1.0))

    color = kwargs.pop("color", _C_PRIMARY)

    def _decay(axd: Axes) -> None:
        axd.plot(time, env_db, color=_C_PRIMARY_LIGHT, lw=0.8,
                 label="Log-magnitude envelope")
        axd.plot(time, edc_db, color=_C_REFERENCE, lw=1.8, label="Schroeder decay")
        axd.set_xlabel(xlabel)
        axd.set_ylabel("Level re peak [dB]")
        axd.set_ylim(bottom=-80.0, top=5.0)
        axd.set_xlim(left=float(time[0]) if n else 0.0,
                     right=float(time[-1]) if n else None)
        axd.grid(True, alpha=0.3)
        axd.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _decay(ax)
        ax.set_title(f"ISO 18233 impulse response ({result.method})")
        return ax

    axes = _new_axes_column(2, sharex=True, figsize=(8.0, 6.0))
    axes[0].plot(time, h / norm, color=color, lw=0.8, **kwargs)
    axes[0].set_ylabel("Amplitude (norm.)")
    axes[0].set_title(f"ISO 18233 impulse response ({result.method})")
    axes[0].grid(True, alpha=0.3)
    _decay(axes[1])
    return axes


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


def plot_vibration_reduction(
    result: "VibrationReductionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Vibration reduction index ``Kij`` versus frequency (ISO 10848).

    Draws the per-band ``Kij`` and, when available, a dashed line at the
    single-number mean ``K̄ij`` (200-1250 Hz, Annex A). Falls back to a
    band-index axis when the result carries no frequencies.

    :param result: A
        :class:`~phonometry.flanking_transmission.VibrationReductionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the ``Kij`` curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    k_ij = np.asarray(result.k_ij, dtype=np.float64)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "$K_{ij}$")
    if result.frequencies is not None:
        freqs = np.asarray(result.frequencies, dtype=np.float64)
        ax.plot(freqs, k_ij, **kwargs)
        _freq_axis(ax, freqs)
    else:
        ax.plot(np.arange(k_ij.size), k_ij, **kwargs)
        ax.set_xlabel("Band index")
    if result.single_number is not None:
        ax.axhline(
            result.single_number,
            color=_C_REFERENCE,
            ls="--",
            lw=1.0,
            label=rf"$\overline{{K}}_{{ij}}$ = {result.single_number:.1f} dB",
        )
    ax.set_ylabel("Vibration reduction index $K_{ij}$ [dB]")
    ax.set_title("Vibration reduction index (ISO 10848)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    return ax


def plot_scattering_coefficient(
    result: "ScatteringResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Random-incidence scattering coefficient ``s`` versus frequency.

    :param result: A :class:`~phonometry.scattering_diffusion.ScatteringResult`
        exposing ``frequencies`` and ``scattering``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the coefficient curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    s = np.asarray(result.scattering, dtype=np.float64)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("color", _C_PRIMARY)
    ax.plot(freqs, s, **kwargs)
    _freq_axis(ax, freqs)
    ax.set_ylabel("Scattering coefficient s")
    # s is normally in [0, 1], but edge effects (Clause 6.3.2) can push it above
    # 1 and those values are kept, not clipped; grow the top so they stay visible.
    top = max(1.05, float(np.nanmax(s)) * 1.05) if s.size else 1.05
    ax.set_ylim(0.0, top)
    ax.set_title("Random-incidence scattering coefficient (ISO 17497-1)")
    ax.grid(True, alpha=0.3)
    return ax


def plot_diffusion_polar(
    result: "DiffusionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Polar reflected-level response with the diffusion coefficient annotated.

    :param result: A :class:`~phonometry.scattering_diffusion.DiffusionResult`
        exposing ``angles`` (degrees), ``levels`` (dB) and ``coefficient``.
    :param ax: Existing (ideally polar) axes, or ``None`` to create a polar one.
    :param kwargs: Forwarded to the reflected-level curve ``plot`` call.
    :return: The polar axes.
    """
    if ax is None:
        plt = _import_pyplot()
        _fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
    angles = np.radians(np.asarray(result.angles, dtype=np.float64))
    levels = np.asarray(result.levels, dtype=np.float64)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("color", _C_PRIMARY)
    ax.plot(angles, levels, **kwargs)
    ax.fill(angles, levels, alpha=0.15, color=kwargs["color"])
    ax.set_title(
        f"Diffusion coefficient d = {float(result.coefficient):.2f} "
        "(ISO 17497-2)"
    )
    return cast("Axes", ax)


def plot_insitu_absorption(
    result: "InsituAbsorptionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """In-situ one-third-octave absorption spectrum ``alpha(f)``.

    :param result: An
        :class:`~phonometry.road_absorption.InsituAbsorptionResult` exposing
        ``frequencies`` and ``absorption``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the absorption :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    alpha = np.asarray(result.absorption, dtype=np.float64)
    positions = _band_axis(ax, freqs)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(positions, np.nan_to_num(alpha), **kwargs)
    ax.set_ylabel("Absorption coefficient")
    ax.set_ylim(0.0, 1.0)
    ax.set_title("In-situ road-surface absorption (ISO 13472-1)")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Human vibration (ISO 8041-1 / ISO 2631 / ISO 5349 / Directive 2002/44/EC)
# ---------------------------------------------------------------------------


def plot_vibration_weighting(
    result: "WeightingResponse", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Frequency-weighting factor (dB) versus frequency (ISO 8041-1).

    :param result: A
        :class:`~phonometry.human_vibration.WeightingResponse` exposing
        ``name``, ``frequencies`` and ``magnitude_db``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the weighting curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    mag_db = np.asarray(result.magnitude_db, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.semilogx(freqs, mag_db, **kwargs)
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Weighting factor [dB]")
    ax.set_title(f"Frequency weighting {result.name} (ISO 8041-1)")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_weighted_spectrum(
    result: "WeightedSpectrum", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Unweighted vs weighted one-third-octave acceleration spectrum.

    Draws the measured band accelerations and, overlaid, the weighted band
    contributions ``W_i*a_i``; the overall ``a_w`` is annotated in the title.

    :param result: A
        :class:`~phonometry.human_vibration.WeightedSpectrum` exposing
        ``frequencies``, ``band_accelerations``, ``weighted``, ``overall`` and
        ``weighting_name``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the weighted (primary) bars.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    raw = np.asarray(result.band_accelerations, dtype=np.float64)
    weighted = np.asarray(result.weighted, dtype=np.float64)
    positions = _band_axis(ax, freqs)
    width = 0.4
    # The weighted bars are the primary artist; forward user kwargs there.
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(
        positions - width / 2, raw, width, color=_C_MUTED, label="Unweighted $a_i$"
    )
    ax.bar(
        positions + width / 2,
        weighted,
        width,
        label=f"Weighted $W_i a_i$ ({result.weighting_name})",
        **kwargs,
    )
    ax.set_ylabel(r"r.m.s. acceleration [m/s$^2$]")
    # Wh is the hand-arm weighting of ISO 5349-1; the others (Wk, Wd, Wm...)
    # are the whole-body weightings of ISO 2631.
    designation = "ISO 5349-1" if str(result.weighting_name) == "Wh" else "ISO 2631"
    ax.set_title(
        f"{designation} weighted acceleration spectrum  "
        f"($a_w$ = {float(result.overall):.3f} " r"m/s$^2$)"
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


def plot_daily_exposure(
    result: "DailyVibrationExposure", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Partial daily exposures against the EAV / ELV (Directive 2002/44/EC).

    Draws one bar per operation (its partial exposure ``A_i(8)``), a combined
    ``A(8)`` bar, and the exposure action and limit value as horizontal lines.

    :param result: A
        :class:`~phonometry.human_vibration.DailyVibrationExposure` exposing
        ``labels``, ``partials``, ``a8`` and ``assessment``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the exposure :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    partials = np.asarray(result.partials, dtype=np.float64)
    labels = [*result.labels, "A(8)"]
    values = [*partials.tolist(), float(result.a8)]
    positions = np.arange(len(values), dtype=np.float64)
    colors = [_C_MUTED] * partials.size + [_C_PRIMARY]
    kwargs.setdefault("color", colors)
    ax.bar(positions, values, **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel(r"Vibration exposure A(8) [m/s$^2$]")

    assessment = result.assessment
    eav = float(assessment.action_value)
    elv = float(assessment.limit_value)
    ax.axhline(eav, color=_C_SECONDARY, ls="--", label=f"EAV = {eav:g}")
    ax.axhline(elv, color=_C_REFERENCE, ls="--", label=f"ELV = {elv:g}")
    top = max(elv, float(np.max(values))) * 1.15
    ax.set_ylim(0.0, top)
    kind = str(assessment.kind).upper()
    ax.set_title(
        f"Directive 2002/44/EC daily {kind} exposure  "
        f"(A(8) = {float(result.a8):.2f} " rf"m/s$^2$, {assessment.zone})"
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Room-noise criteria (ANSI/ASA S12.2-2019)
# ---------------------------------------------------------------------------


def plot_noise_criterion(
    result: "NCResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Measured spectrum against the NC curve family (ANSI/ASA S12.2-2019).

    :param result: A :class:`~phonometry.room_noise.NCResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the measured-spectrum :meth:`plot`.
    :return: The axes.
    """
    from .room_noise import NC_CURVES, NC_INDICES, OCTAVE_BANDS

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    levels = np.asarray(result.levels, dtype=np.float64)
    for row, idx in zip(NC_CURVES, NC_INDICES):
        ax.plot(OCTAVE_BANDS, row, color=_C_MUTED, lw=0.8, zorder=1)
        ax.annotate(
            f"{idx:.0f}", (OCTAVE_BANDS[-1], row[-1]),
            fontsize="x-small", color=_C_MUTED, va="center",
        )
    valid = ~np.isnan(levels)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Measured")
    ax.plot(freqs[valid], levels[valid], "o-", zorder=3, **kwargs)
    # Nearest *valid* band rather than float equality against the stored
    # value; the marker sits on that band so its x and y stay paired.
    candidates = np.flatnonzero(valid)
    if candidates.size:
        governing = int(
            candidates[
                np.argmin(np.abs(freqs[candidates] - result.governing_frequency))
            ]
        )
        ax.plot(
            [freqs[governing]],
            [levels[governing]],
            "D", color=_C_REFERENCE, zorder=4,
            label=f"Governing band ({_format_freq(result.governing_frequency)})",
        )
    _freq_axis(ax, OCTAVE_BANDS)
    ax.set_ylabel("Octave-band SPL [dB]")
    ax.set_title(
        f"ANSI/ASA S12.2 NC-{result.rating:g} "
        f"({_format_freq(result.governing_frequency)})"
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_room_criterion(
    result: "RCResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Measured spectrum against the reference RC Mark II curve (Annex D).

    Shades the rumble tolerance (reference + 5 dB below 500 Hz) and the hiss
    tolerance (reference + 3 dB at and above 1000 Hz).

    :param result: A :class:`~phonometry.room_noise.RCResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the measured-spectrum :meth:`plot`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    levels = np.asarray(result.levels, dtype=np.float64)
    reference = np.asarray(result.reference_curve, dtype=np.float64)
    valid = ~np.isnan(levels)

    ax.plot(freqs, reference, "s--", color=_C_MUTED,
            label=f"Reference RC-{result.rating}")
    low = freqs <= 500.0
    high = freqs >= 1000.0
    ax.fill_between(freqs[low], reference[low], reference[low] + 5.0,
                    color=_C_SECONDARY_LIGHT, alpha=0.35,
                    label="Rumble tolerance (+5 dB)")
    ax.fill_between(freqs[high], reference[high], reference[high] + 3.0,
                    color=_C_PRIMARY_LIGHT, alpha=0.45,
                    label="Hiss tolerance (+3 dB)")
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", "Measured")
    ax.plot(freqs[valid], levels[valid], "o-", zorder=3, **kwargs)
    _freq_axis(ax, freqs)
    ax.set_ylabel("Octave-band SPL [dB]")
    ax.set_title(f"ANSI/ASA S12.2 {result.label}")
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Age-related hearing threshold (ISO 7029)
# ---------------------------------------------------------------------------


def plot_age_threshold(
    result: "AgeThresholdResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Median age-related hearing threshold with the 10-90 % fractile band.

    :param result: An :class:`~phonometry.hearing.AgeThresholdResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the median line ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    median = np.asarray(result.median, dtype=np.float64)
    su = np.asarray(result.spread_upper, dtype=np.float64)
    sl = np.asarray(result.spread_lower, dtype=np.float64)

    _fractile_band(ax, freqs, median, sl, su, color=_C_PRIMARY_LIGHT)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.plot(freqs, median, "o-", label="Median", **kwargs)
    if abs(result.fractile - 0.5) > 1e-9:
        ax.plot(freqs, np.asarray(result.threshold, dtype=np.float64), "s--",
                color=_C_REFERENCE, label=f"Fractile {result.fractile:g}")
    _freq_axis(ax, freqs)
    ax.set_ylabel("Threshold deviation from age 18 [dB]")
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    ax.set_title(f"ISO 7029 hearing threshold — {result.sex}, age {result.age:g}")
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Noise-induced hearing loss (ISO 1999)
# ---------------------------------------------------------------------------


def plot_nipts(
    result: "NiptsResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Median NIPTS spectrum with the 10-90 % fractile band (ISO 1999).

    :param result: A :class:`~phonometry.noise_induced_hearing_loss.NiptsResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the median line ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    median = np.asarray(result.median, dtype=np.float64)
    du = np.asarray(result.spread_upper, dtype=np.float64)
    dl = np.asarray(result.spread_lower, dtype=np.float64)

    _fractile_band(ax, freqs, median, dl, du, color=_C_SECONDARY_LIGHT, floor=0.0)
    kwargs.setdefault("color", _C_SECONDARY)
    ax.plot(freqs, median, "o-", label="Median $N_{50}$", **kwargs)
    if abs(result.fractile - 0.5) > 1e-9:
        ax.plot(freqs, np.asarray(result.value, dtype=np.float64), "s--",
                color=_C_REFERENCE, label=f"Fractile {result.fractile:g}")
    _freq_axis(ax, freqs)
    ax.set_ylabel("NIPTS [dB]")
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    ax.set_title(
        f"ISO 1999 NIPTS — $L_{{EX,8h}}$ = {result.l_ex:g} dB, "
        f"{result.years:g} yr"
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_htlan(
    result: "HtlanResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Age, noise and combined hearing threshold components (ISO 1999, 6.1).

    :param result: A :class:`~phonometry.noise_induced_hearing_loss.HtlanResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the combined-threshold line ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    ax.plot(freqs, np.asarray(result.htla, dtype=np.float64), "o-",
            color=_C_PRIMARY, label="Age (HTLA, ISO 7029)")
    ax.plot(freqs, np.asarray(result.nipts, dtype=np.float64), "^-",
            color=_C_SECONDARY, label="Noise (NIPTS)")
    kwargs.setdefault("color", _C_REFERENCE)
    ax.plot(freqs, np.asarray(result.threshold, dtype=np.float64), "s--",
            label="Age + noise (HTLAN)", **kwargs)
    _freq_axis(ax, freqs)
    ax.set_ylabel("Hearing threshold level [dB]")
    ax.invert_yaxis()  # audiogram convention: worse hearing downward
    ax.set_title(
        f"ISO 1999 HTLAN — {result.sex}, age {result.age:g}, "
        f"{result.l_ex:g} dB / {result.years:g} yr"
    )
    ax.legend(loc="lower left", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Impulsive-sound prominence (NT ACOU 112)
# ---------------------------------------------------------------------------


def plot_impulse_prominence(
    result: "ImpulseProminenceResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Adjustment curve ``KI(P)`` with the candidate impulses marked.

    :param result: An :class:`~phonometry.impulse_prominence.ImpulseProminenceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the impulses ``scatter``.
    :return: The axes.
    """
    from .impulse_prominence import ADJUSTMENT_THRESHOLD, impulse_adjustment

    ax = ax if ax is not None else _new_axes()
    per = np.asarray(result.per_impulse, dtype=np.float64)
    per_max = float(per.max()) if per.size else 0.0
    p_max = max(per_max, result.prominence, 15.0) + 1.0
    grid = np.linspace(0.0, p_max, 200)
    ax.plot(grid, impulse_adjustment(grid), color=_C_PRIMARY,
            label=r"$K_I = 1.8\,(P-5)$")
    ax.axvline(ADJUSTMENT_THRESHOLD, color=_C_MUTED, ls=":",
               label=f"threshold $P = {ADJUSTMENT_THRESHOLD:g}$")

    kwargs.setdefault("color", _C_PRIMARY_LIGHT)
    kwargs.setdefault("zorder", 3)
    ax.scatter(per, impulse_adjustment(per), label="Impulses", **kwargs)
    ax.scatter([result.prominence], [result.adjustment], color=_C_REFERENCE,
               zorder=4, s=90, marker="*",
               label=f"Governing  P = {result.prominence:.2f},  "
                     f"$K_I$ = {result.adjustment:.1f} dB")
    ax.set_xlabel("Predicted prominence $P$")
    ax.set_ylabel("Adjustment $K_I$ [dB]")
    ax.set_title("NT ACOU 112 — impulse adjustment to $L_{Aeq}$")
    ax.set_ylim(bottom=0.0)
    ax.legend(loc="upper left", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax


def plot_tonal_adjustment(
    result: "TonalAssessmentResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Tonal adjustment curve ``Kt(ΔLta)`` with the assessed tone marked.

    :param result: A
        :class:`~phonometry.environmental_measurement.TonalAssessmentResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the assessed-tone ``scatter``.
    :return: The axes.
    """
    from .environmental_measurement import tonal_adjustment

    ax = ax if ax is not None else _new_axes()
    top = max(result.audibility, 12.0) + 1.0
    grid = np.linspace(0.0, top, 200)
    curve = np.array([tonal_adjustment(d) for d in grid], dtype=np.float64)
    ax.plot(grid, curve, color=_C_PRIMARY, label=r"$K_t(\Delta L_{ta})$")
    ax.axvline(4.0, color=_C_MUTED, ls=":", label=r"knees $\Delta L_{ta}=4,\,10$ dB")
    ax.axvline(10.0, color=_C_MUTED, ls=":")

    kwargs.setdefault("color", _C_REFERENCE)
    kwargs.setdefault("zorder", 4)
    kwargs.setdefault("s", 90)
    kwargs.setdefault("marker", "*")
    ax.scatter([result.audibility], [result.adjustment],
               label=rf"$\Delta L_{{ta}}$ = {result.audibility:.1f} dB,  "
                     rf"$K_t$ = {result.adjustment:.1f} dB", **kwargs)
    ax.set_xlabel(r"Tonal audibility $\Delta L_{ta}$ [dB]")
    ax.set_ylabel("Tonal adjustment $K_t$ [dB]")
    ax.set_title("ISO 1996-2 tonal adjustment")
    ax.set_ylim(bottom=0.0)
    ax.legend(loc="upper left", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax


def plot_enclosed_space_absorption(
    result: "ReverberationResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Reverberation time over the octave bands (EN 12354-6).

    :param result: A :class:`~phonometry.enclosed_space_absorption.ReverberationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the reverberation-time ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    rt = np.asarray(result.reverberation_time, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    ax.plot(freq, rt, **kwargs)
    _freq_axis(ax, freq)
    ax.set_ylabel("Reverberation time $T$ [s]")
    ax.set_title("EN 12354-6 reverberation time")
    ax.set_ylim(bottom=0.0)
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_reverberation_models(
    result: "ReverberationModelResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Reverberation time by five statistical models over the bands.

    Draws the Sabine, Eyring, Millington-Sette, Fitzroy and Arau-Puchades
    curves, with Arau-Puchades emphasised as the recommended model for a
    non-uniform absorption distribution.

    :param result: A
        :class:`~phonometry.reverberation_prediction.ReverberationModelResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to every curve ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    styles = (
        ("Sabine", result.sabine, _C_SECONDARY, "s", 1.4),
        ("Eyring", result.eyring, _C_TERTIARY, "^", 1.4),
        ("Millington-Sette", result.millington_sette, _C_QUATERNARY, "v", 1.4),
        ("Fitzroy", result.fitzroy, _C_MUTED, "D", 1.4),
        ("Arau-Puchades", result.arau_puchades, _C_PRIMARY, "o", 2.4),
    )
    for label, curve, color, marker, lw in styles:
        ax.plot(
            freq,
            np.asarray(curve, dtype=np.float64),
            color=color,
            marker=marker,
            lw=lw,
            label=label,
            **kwargs,
        )
    _freq_axis(ax, freq)
    ax.set_ylabel("Reverberation time $T$ [s]")
    ax.set_title(
        f"Reverberation-time models — $V$ = {result.volume:.0f} m³, "
        f"$S$ = {result.surface_area:.0f} m²"
    )
    ax.set_ylim(bottom=0.0)
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_dynamic_stiffness(
    result: "DynamicStiffnessResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Floating-floor natural frequency ``f0(s')`` with the design point marked.

    :param result: A
        :class:`~phonometry.dynamic_stiffness.DynamicStiffnessResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the design-point ``scatter``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    m = result.floor_mass_per_area
    s_mn = result.dynamic_stiffness / 1e6
    grid = np.logspace(np.log10(max(s_mn * 0.2, 1e-2)), np.log10(s_mn * 5.0), 240)
    f0 = np.sqrt(grid * 1e6 / m) / (2.0 * np.pi)
    ax.plot(grid, f0, color=_C_PRIMARY,
            label=rf"$f_0 = \frac{{1}}{{2\pi}}\sqrt{{s'/m'}}$,  $m'$ = {m:g} kg/m²")
    ax.axhline(result.natural_frequency, color=_C_MUTED, ls=":", lw=0.8)
    ax.plot([s_mn, s_mn], [0.0, result.natural_frequency], color=_C_MUTED, ls=":", lw=0.8)

    kwargs.setdefault("color", _C_REFERENCE)
    kwargs.setdefault("zorder", 5)
    kwargs.setdefault("s", 80)
    ax.scatter([s_mn], [result.natural_frequency],
               label=f"$s'$ = {s_mn:.2f} MN/m³,  $f_0$ = {result.natural_frequency:.1f} Hz",
               **kwargs)
    ax.set_xscale("log")
    ax.set_xlabel("Dynamic stiffness per unit area $s'$ [MN/m³]")
    ax.set_ylabel("Natural frequency $f_0$ [Hz]")
    ax.set_title("EN 29052-1 floating-floor resonance")
    ax.set_ylim(bottom=0.0)
    ax.legend(loc="upper left", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_mobility(
    result: "MobilityResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Mobility magnitude ``|Y(f)|`` on log-log axes (ISO 7626-1).

    :param result: A :class:`~phonometry.mechanical_mobility.MobilityResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the magnitude ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    mag = np.asarray(result.magnitude, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    label = "driving-point mobility" if result.driving_point else "transfer mobility"
    ax.loglog(freq, mag, label=label, **kwargs)
    # Mark the mobility peak (a resonance for a driving-point FRF).
    peak = int(np.argmax(mag))
    ax.plot(freq[peak], mag[peak], "o", color=_C_REFERENCE, zorder=5,
            label=f"peak at {freq[peak]:.1f} Hz")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Mobility $|Y|$ [m/(N·s)]")
    ax.set_title("ISO 7626-1 mechanical mobility")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_transfer_stiffness(
    result: "TransferStiffnessResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Dynamic transfer stiffness level ``L_k(f)`` on a log-frequency axis.

    :param result: A :class:`~phonometry.transfer_stiffness.TransferStiffnessResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the level ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    level = np.asarray(result.level, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.semilogx(freq, level, label=r"$L_k = 20\,\lg(|k_{2,1}|/k_0)$", **kwargs)
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel(r"Transfer stiffness level $L_k$ [dB re 1 N/m]")
    ax.set_title("ISO 10846 dynamic transfer stiffness")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


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


def plot_vibration_sound_power(
    result: "VibrationSoundPowerResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Radiated sound power level per band (ISO/TS 7849).

    :param result: A :class:`~phonometry.vibration_sound_power.VibrationSoundPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the bar ``plot``.
    :return: The axes.
    """
    return _plot_band_level_bars(
        ax, result.sound_power_level, result.frequencies, result.total_level,
        ylabel=r"Sound power level $L_W$ [dB re 1 pW]",
        title="ISO/TS 7849 sound power from surface vibration", **kwargs,
    )


def plot_structure_borne_power(
    result: "StructureBornePowerResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Characteristic structure-borne sound power level per band (EN 15657).

    :param result: A :class:`~phonometry.structure_borne_power.StructureBornePowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the bar ``plot``.
    :return: The axes.
    """
    return _plot_band_level_bars(
        ax, result.power_level, result.frequencies, result.total_level,
        ylabel=r"Structure-borne power level $L_{Ws}$ [dB re 1 pW]",
        title="EN 15657 characteristic structure-borne sound power", **kwargs,
    )


def plot_installed_structure_borne(
    result: "InstalledSourceResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-path and total normalised structure-borne SPL (EN 12354-5).

    :param result: An :class:`~phonometry.installed_structure_borne.InstalledSourceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the total-level ``plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    paths = np.atleast_2d(np.asarray(result.path_levels, dtype=np.float64))
    total = np.atleast_1d(np.asarray(result.total_level, dtype=np.float64))
    n_bands = total.size
    if result.frequencies is not None:
        x = np.asarray(result.frequencies, dtype=np.float64)
        ax.set_xscale("log")
        ax.set_xlabel("Frequency [Hz]")
    else:
        x = np.arange(1, n_bands + 1, dtype=np.float64)
        ax.set_xlabel("Band")
    for k, path in enumerate(paths):
        ax.plot(x, path, color=_C_MUTED, lw=1.0, ls=":", marker=".",
                label="paths" if k == 0 else None)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("lw", 2.2)
    ax.plot(x, total, label=r"total $L_{n,s}$", **kwargs)
    ax.set_ylabel(r"Normalised SPL $L_{n,s}$ [dB]")
    ax.set_title("EN 12354-5 installed structure-borne sound")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_multiple_shock(
    result: "MultipleShockResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Injury-probability curve ``P(R)`` with this assessment's ``R`` marked.

    :param result: A :class:`~phonometry.multiple_shock_vibration.MultipleShockResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the ``R`` marker ``scatter``.
    :return: The axes.
    """
    from .multiple_shock_vibration import injury_probability

    ax = ax if ax is not None else _new_axes()
    r10, r50, r90 = result.risk_thresholds
    r_max = max(result.risk, r90) * 1.3
    grid = np.linspace(0.0, r_max, 240)
    prob = np.asarray(injury_probability(grid, sex=result.sex), dtype=np.float64)
    ax.plot(grid, 100.0 * prob, color=_C_PRIMARY,
            label=r"$\Pi(R) = 1 - e^{-(R/\alpha)^{\beta}}$")
    for level, r_val in zip((10, 50, 90), (r10, r50, r90)):
        ax.axhline(level, color=_C_MUTED, ls=":", lw=0.8)
        ax.plot([r_val, r_val], [0.0, level], color=_C_MUTED, ls=":", lw=0.8)

    kwargs.setdefault("color", _C_REFERENCE)
    kwargs.setdefault("zorder", 4)
    kwargs.setdefault("s", 90)
    ax.scatter([result.risk], [100.0 * result.probability],
               label=f"$R$ = {result.risk:.2f},  $\\Pi$ = "
                     f"{100.0 * result.probability:.0f} %", **kwargs)
    ax.set_xlabel("Stress variable $R$")
    ax.set_ylabel("Probability of lumbar injury [%]")
    ax.set_title(f"ISO 2631-5 injury probability — {result.sex}")
    ax.set_xlim(left=0.0)
    ax.set_ylim(0.0, 100.0)
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Measurement uncertainty budget (GUM)
# ---------------------------------------------------------------------------


def plot_uncertainty_budget(
    result: "UncertaintyResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Bar chart of each input's contribution to the combined uncertainty.

    :param result: An :class:`~phonometry.uncertainty.UncertaintyResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to :meth:`barh`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    contributions = np.asarray(result.contributions, dtype=np.float64)
    names = list(result.names) or [f"x{i + 1}" for i in range(contributions.size)]
    positions = np.arange(contributions.size)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.barh(positions, contributions, **kwargs)
    ax.axvline(result.combined_uncertainty, color=_C_REFERENCE, ls="--",
               label=f"$u_c$ = {result.combined_uncertainty:.3g}")
    ax.set_yticks(positions)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel("Contribution to combined uncertainty $|c_i|\\,u(x_i)$")
    ax.set_title(f"GUM uncertainty budget — y = {result.value:.4g}")
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(True, axis="x", alpha=0.3)
    return ax


def plot_monte_carlo(
    result: "MonteCarloResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Histogram of the Monte Carlo output with the coverage interval marked.

    :param result: A :class:`~phonometry.uncertainty.MonteCarloResult`
        obtained with ``keep_samples=True`` (the histogram needs the raw
        output sample).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.hist`.
    :return: The axes.
    :raises ValueError: If the result carries no output samples.
    """
    if result.samples is None:
        raise ValueError(
            "plot() needs the Monte Carlo output samples; call "
            "monte_carlo(..., keep_samples=True) to retain them."
        )
    ax = ax if ax is not None else _new_axes()
    samples = np.asarray(result.samples, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY_LIGHT)
    kwargs.setdefault("bins", 120)
    kwargs.setdefault("density", True)
    ax.hist(samples, **kwargs)
    low, high = result.interval
    ax.axvspan(low, high, color=_C_PRIMARY, alpha=0.12,
               label=f"{100.0 * result.coverage:g} % coverage interval")
    ax.axvline(result.value, color=_C_REFERENCE, ls="--",
               label=f"y = {result.value:.4g}")
    ax.set_xlabel("Output quantity y")
    ax.set_ylabel("Probability density")
    ax.set_title(
        "Monte Carlo distribution (GUM Supplement 1) — "
        f"u(y) = {result.standard_uncertainty:.3g}"
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Open-plan offices (ISO 3382-3)
# ---------------------------------------------------------------------------


def plot_open_plan(
    result: "OpenPlanResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Spatial decay of speech with the distraction/privacy distances marked.

    Redraws the Clause 6.2 regression line ``Lp,A,S(r) = Lp,A,S,4m -
    D2,S lg(r/4)/lg 2`` over the 2 m to 16 m fitting range (extended to
    reach ``rP`` when it lies further out) and marks the distraction
    distance ``rD`` and the privacy distance ``rP`` from the STI regression.

    :param result: An :class:`~phonometry.open_plan.OpenPlanResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the decay-line ``plot`` call.
    :return: The axes.
    :raises ValueError: If the spatial-decay regression is undefined
        (``d2s`` / ``lp_as_4m`` are NaN).
    """
    if not (np.isfinite(result.d2s) and np.isfinite(result.lp_as_4m)):
        raise ValueError(
            "plot() needs the spatial-decay regression; this result's d2s / "
            "lp_as_4m are NaN (fewer than two positions in the 2 m to 16 m "
            "range)."
        )
    ax = ax if ax is not None else _new_axes()
    import matplotlib.ticker as mticker

    r_max = 16.0
    for marker in (result.rd, result.rp):
        if np.isfinite(marker):
            r_max = max(r_max, 1.15 * marker)
    r = np.geomspace(2.0, r_max, 200)
    level = result.lp_as_4m - result.d2s * np.log2(r / 4.0)

    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault(
        "label", rf"$D_{{2,S}}$ = {result.d2s:.1f} dB per doubling"
    )
    ax.plot(r, level, **kwargs)
    ax.plot([4.0], [result.lp_as_4m], "o", color=_C_PRIMARY, ms=7,
            label=rf"$L_{{p,A,S,4m}}$ = {result.lp_as_4m:.1f} dB")
    if np.isfinite(result.rd):
        ax.axvline(result.rd, color=_C_SECONDARY, ls="--",
                   label=rf"$r_D$ = {result.rd:.1f} m (STI 0.50)")
    if np.isfinite(result.rp):
        ax.axvline(result.rp, color=_C_REFERENCE, ls=":",
                   label=rf"$r_P$ = {result.rp:.1f} m (STI 0.20)")

    ax.set_xscale("log", base=2)
    ticks = [float(2**k) for k in range(1, int(np.ceil(np.log2(r_max))) + 1)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.set_xlabel("Distance from the sound source [m]")
    ax.set_ylabel("A-weighted SPL of speech [dB]")
    ax.set_title("ISO 3382-3 spatial decay of speech")
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Outdoor sound propagation (ISO 9613-2)
# ---------------------------------------------------------------------------


def plot_outdoor_attenuation(
    result: "OutdoorAttenuation", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Stacked per-band attenuation terms with the total overlaid (ISO 9613-2).

    The divergence, atmospheric, ground and barrier terms are stacked per
    octave band on separate positive and negative baselines (the ground
    effect can be a net *gain*), and the total attenuation ``A`` is drawn
    as the primary marker line on top.

    :param result: An
        :class:`~phonometry.outdoor_propagation.OutdoorAttenuation`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the total-attenuation ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    positions = _band_axis(ax, freqs)
    n = freqs.size

    # Separate positive and negative cumulative baselines so a negative term
    # stacks below zero instead of being drawn on top of the previous bars;
    # the signed heights sum to a_total.
    pos_bottom = np.zeros(n)
    neg_bottom = np.zeros(n)
    terms = (
        (result.a_div, _C_PRIMARY, "$A_{div}$ — divergence"),
        (result.a_atm, _C_TERTIARY, "$A_{atm}$ — atmospheric"),
        (result.a_gr, _C_QUATERNARY, "$A_{gr}$ — ground"),
        (result.a_bar, _C_SECONDARY, "$A_{bar}$ — barrier"),
    )
    for values, color, label in terms:
        term = np.asarray(values, dtype=np.float64)
        bottom = np.where(term >= 0.0, pos_bottom, neg_bottom)
        ax.bar(positions, term, bottom=bottom, color=color, label=label)
        pos_bottom += np.maximum(term, 0.0)
        neg_bottom += np.minimum(term, 0.0)

    kwargs.setdefault("color", _C_REFERENCE)
    kwargs.setdefault("marker", "D")
    kwargs.setdefault("label", "$A$ — total")
    ax.plot(positions, np.asarray(result.a_total, dtype=np.float64),
            zorder=4, **kwargs)
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.set_ylabel("Attenuation A [dB]")
    ax.set_title("ISO 9613-2 attenuation breakdown")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Impedance tube (ISO 10534-2)
# ---------------------------------------------------------------------------


def plot_impedance_tube(
    result: "ImpedanceTubeResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Normal-incidence absorption spectrum with |r| overlaid (ISO 10534-2).

    Draws the absorption coefficient ``alpha(f)`` as the primary curve and
    the magnitude of the reflection factor ``|r|(f)`` as a muted companion
    (both are dimensionless and share the 0..1 axis).

    :param result: An :class:`~phonometry.impedance_tube.ImpedanceTubeResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the absorption-curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequency, dtype=np.float64)
    alpha = np.asarray(result.absorption, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", r"Absorption $\alpha$")
    ax.plot(freqs, alpha, **kwargs)
    ax.plot(freqs, np.abs(np.asarray(result.reflection, dtype=np.complex128)),
            ls="--", color=_C_MUTED, label="Reflection factor $|r|$")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Coefficient")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("ISO 10534-2 normal-incidence absorption")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Occupational noise exposure (ISO 9612)
# ---------------------------------------------------------------------------


def plot_occupational_exposure(
    result: "ExposureResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-task contributions to the daily exposure level (ISO 9612).

    One bar per task (its contribution to ``LEX,8h``), with the combined
    ``LEX,8h`` and the one-sided upper limit ``LEX,8h + U`` as horizontal
    lines.

    :param result: An
        :class:`~phonometry.occupational_exposure.ExposureResult` from the
        task-based strategy (the one that carries per-task contributions).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the task :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    :raises ValueError: If the result carries no per-task contributions.
    """
    if not result.tasks:
        raise ValueError(
            "plot() needs per-task contributions; only task_based_exposure() "
            "results carry them (the job/full-day strategies do not)."
        )
    ax = ax if ax is not None else _new_axes()
    contributions = [t.lex_8h_contribution for t in result.tasks]
    labels = [t.label for t in result.tasks]
    positions = np.arange(len(contributions), dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(positions, contributions, **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45, ha="right")

    ax.axhline(result.lex_8h, color=_C_REFERENCE, ls="--",
               label=f"$L_{{EX,8h}}$ = {result.lex_8h:.1f} dB")
    ax.axhline(result.upper_limit, color=_C_MUTED, ls=":",
               label=f"$L_{{EX,8h}} + U$ = {result.upper_limit:.1f} dB")
    top = max(result.upper_limit, max(contributions))
    bottom = min(0.0, min(contributions))
    ax.set_ylim(bottom * 1.12 if bottom < 0.0 else 0.0, top * 1.12)
    ax.set_ylabel("A-weighted level [dB]")
    ax.set_title(
        f"ISO 9612 daily noise exposure — $L_{{EX,8h}}$ = "
        f"{result.lex_8h:.1f} dB (U = {result.expanded_uncertainty:.1f} dB)"
    )
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Static airflow resistance (ISO 9053-1)
# ---------------------------------------------------------------------------


def plot_static_airflow(
    result: "StaticAirflowResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Fitted pressure-drop curve with the evaluation point (ISO 9053-1).

    Draws the clause 7.5 through-origin fit ``dp = a u + b u**2`` over twice
    the evaluation range and marks the reference evaluation point.

    :param result: A
        :class:`~phonometry.airflow_resistance.StaticAirflowResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the fitted-curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    u_eval = float(result.evaluation_velocity)
    u = np.linspace(0.0, 2.0 * u_eval, 200)
    dp = result.linear_coefficient * u + result.quadratic_coefficient * u**2

    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", r"Fit $\Delta p = a\,u + b\,u^2$")
    # Millimetres per second keep the clause 7.5 reference (0.5 mm/s) legible.
    ax.plot(u * 1e3, dp, **kwargs)
    ax.plot([u_eval * 1e3], [result.pressure_drop], "D", color=_C_REFERENCE,
            ms=7, label=f"Evaluation point (u = {u_eval * 1e3:g} mm/s)")
    ax.set_xlabel("Linear airflow velocity u [mm/s]")
    ax.set_ylabel(r"Pressure difference $\Delta p$ [Pa]")
    ax.set_title(
        "ISO 9053-1 static airflow resistance — "
        f"$R_s$ = {result.specific_resistance:.3g} Pa s/m"
    )
    ax.legend(loc="upper left", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Building performance prediction (EN 12354-1 / EN 12354-2)
# ---------------------------------------------------------------------------


def plot_airborne_prediction(
    result: "AirbornePredictionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-path shares of the transmitted energy (EN 12354-1).

    One bar per transmission path (direct plus flanking), sorted by its
    share of the total transmitted sound energy, largest first.

    :param result: An
        :class:`~phonometry.building_prediction.AirbornePredictionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the path :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    contribs = sorted(result.paths, key=lambda c: c.fraction, reverse=True)
    shares = [100.0 * c.fraction for c in contribs]
    positions = np.arange(len(shares), dtype=np.float64)
    kwargs.setdefault(
        "color", [_C_PRIMARY if c.kind == "Dd" else _C_MUTED for c in contribs]
    )
    ax.bar(positions, shares, **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels([c.label for c in contribs], rotation=45, ha="right")
    ax.set_xlabel("Transmission path")
    ax.set_ylabel("Share of transmitted energy [%]")
    ax.set_title(
        f"EN 12354-1 flanking prediction — R'w = {result.r_prime_w:.1f} dB "
        f"(RDd,w = {result.r_direct_w:.1f} dB)"
    )
    ax.grid(True, axis="y", alpha=0.3)
    return ax


def plot_impact_prediction(
    result: "ImpactPredictionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Terms of the apparent impact-level prediction (EN 12354-2).

    Bars for the Formula 21 terms — the bare-floor equivalent level, the
    covering improvement, the flanking correction — and the resulting
    apparent level ``L'n,w = Ln,w,eq - DLw + K``.

    :param result: An
        :class:`~phonometry.building_prediction.ImpactPredictionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the term :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    labels = ("$L_{n,w,eq}$", r"$-\Delta L_w$", "$+K$", "$L'_{n,w}$")
    values = (
        result.ln_w_eq,
        -result.delta_l_w,
        result.k_correction,
        result.l_prime_n_w,
    )
    positions = np.arange(len(values), dtype=np.float64)
    kwargs.setdefault("color", [_C_MUTED, _C_TERTIARY, _C_SECONDARY, _C_PRIMARY])
    ax.bar(positions, values, **kwargs)
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Level / correction [dB]")
    ax.set_title(
        f"EN 12354-2 impact prediction — L'n,w = {result.l_prime_n_w:.1f} dB"
    )
    ax.grid(True, axis="y", alpha=0.3)
    return ax


# ---------------------------------------------------------------------------
# Field sound insulation spectra (ISO 16283-1 / ISO 16283-2)
# ---------------------------------------------------------------------------


def plot_airborne_insulation(
    result: "AirborneInsulationResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-band airborne insulation quantities (ISO 16283-1).

    Draws the standardized level difference ``DnT`` first (the primary
    curve), then the level difference ``D`` and, when available, the
    apparent sound reduction index ``R'``.

    :param result: An :class:`~phonometry.insulation.AirborneInsulationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the primary ``DnT`` curve ``plot`` call.
    :return: The axes.
    """
    curves = [
        ("$D_{nT}$", np.asarray(result.dnt, dtype=np.float64)),
        ("$D$", np.asarray(result.d, dtype=np.float64)),
    ]
    if result.r_prime is not None:
        curves.append(("$R'$", np.asarray(result.r_prime, dtype=np.float64)))
    return _plot_insulation_bands(
        curves,
        ylabel="Level difference / reduction index [dB]",
        title="Airborne sound insulation (ISO 16283-1)",
        ax=ax,
        **kwargs,
    )


def plot_impact_insulation(
    result: "ImpactInsulationResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-band impact sound pressure levels (ISO 16283-2).

    Draws the standardized level ``L'nT`` first (the primary curve) and,
    when available, the normalized level ``L'n``.

    :param result: An :class:`~phonometry.insulation.ImpactInsulationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the primary ``L'nT`` curve ``plot`` call.
    :return: The axes.
    """
    curves = [("$L'_{nT}$", np.asarray(result.l_n_t, dtype=np.float64))]
    if result.l_n is not None:
        curves.append(("$L'_n$", np.asarray(result.l_n, dtype=np.float64)))
    return _plot_insulation_bands(
        curves,
        ylabel="Impact sound pressure level [dB]",
        title="Impact sound insulation (ISO 16283-2)",
        ax=ax,
        **kwargs,
    )


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


def plot_band_uncertainty(
    result: "BandUncertainty", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Per-band standard uncertainty of an insulation quantity (ISO 12999-1).

    :param result: A
        :class:`~phonometry.building_uncertainty.BandUncertainty`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the uncertainty curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs, u = result.to_arrays()
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    ax.plot(freqs, u, **kwargs)
    _freq_axis(ax, freqs)
    ax.set_ylabel("Standard uncertainty u [dB]")
    ax.set_ylim(bottom=0.0)
    quantity = "sigma_R95 upper limit" if result.upper_limit else "u"
    ax.set_title(
        f"ISO 12999-1 band uncertainty ({quantity}) — "
        f"{result.measurand}, situation {result.situation}"
    )
    ax.grid(True, which="both", alpha=0.3)
    return ax


_ABSORPTION_QUANTITY_LABELS: Final = {
    "absorption_coefficient": "Sound absorption coefficient alpha_s",
    "equivalent_area": "Equivalent absorption area A_T [m2]",
    "practical_coefficient": "Practical absorption coefficient alpha_p",
}


def plot_absorption_uncertainty(
    result: "AbsorptionUncertaintyResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Absorption quantity with its expanded-uncertainty ribbon (ISO 12999-2).

    Draws the per-band quantity (``alpha_s``, ``A_T`` or ``alpha_p``) as a curve
    with a shaded ``±U`` band using the exact expanded uncertainty ``U = k·u``.

    :param result: An
        :class:`~phonometry.absorption_uncertainty.AbsorptionUncertaintyResult`
        for a band quantity (single-number results have no spectrum to plot).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the value-curve ``plot`` call.
    :return: The axes.
    :raises ValueError: The result is a single-number quantity (no bands).
    """
    if result.frequencies.size == 0:
        raise ValueError(
            "plot() needs a per-band result; single-number quantities "
            "(alpha_w, DLalpha) have no spectrum to plot."
        )
    ax = ax if ax is not None else _new_axes()
    freqs = result.frequencies
    value = result.values
    u_expanded = result.expanded_uncertainty
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    ax.fill_between(
        freqs,
        value - u_expanded,
        value + u_expanded,
        color=_C_PRIMARY_LIGHT,
        alpha=0.5,
        label=f"+/-U (k = {result.coverage_factor:g})",
    )
    ax.plot(freqs, value, **kwargs)
    _freq_axis(ax, freqs)
    ylabel = _ABSORPTION_QUANTITY_LABELS.get(result.quantity, "Value")
    ax.set_ylabel(ylabel)
    if result.quantity != "equivalent_area":
        ax.set_ylim(0.0, 1.05)
    sigma = "sigma_R" if result.condition == "reproducibility" else "sigma_r"
    ax.set_title(
        f"ISO 12999-2 absorption uncertainty ({sigma}) — {result.condition}"
    )
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    return ax


def plot_floor_covering_improvement(
    result: "FloorCoveringImprovementResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Impact-sound improvement spectrum ΔL of a floor covering (ISO 16251-1).

    :param result: A
        :class:`~phonometry.floor_covering_improvement.FloorCoveringImprovementResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the improvement-curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs, dl = result.frequencies, result.improvement
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    ax.plot(freqs, dl, **kwargs)
    # Mark bands at the limit of measurement (reported as > delta-L).
    if result.limited.size and bool(np.any(result.limited)):
        ax.plot(
            freqs[result.limited], dl[result.limited], ls="", marker="v",
            color=_C_SECONDARY, ms=9, mfc="none", mew=1.6, zorder=5,
            label="limit of measurement (> delta-L)",
        )
    _freq_axis(ax, freqs)
    ax.set_ylabel("Improvement of impact sound insulation delta-L [dB]")
    ax.set_ylim(bottom=0.0)
    title = "ISO 16251-1 Floor-Covering Impact Sound Improvement"
    if result.delta_lw is not None:
        title += f"  (delta-Lw = {result.delta_lw} dB)"
    ax.set_title(title)
    ax.grid(True, which="both", alpha=0.3)
    if ax.get_legend_handles_labels()[0]:
        ax.legend()
    return ax
