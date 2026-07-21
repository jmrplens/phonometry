#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the electroacoustics domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_EDGE,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _LEGEND_UPPER_RIGHT,
    _format_freq,
    _import_pyplot,
    _new_axes,
    _new_axes_column,
    format_frequency_axis,
)

if TYPE_CHECKING:
    import numpy.typing as npt
    from matplotlib.axes import Axes

    from ..electroacoustics.distortion import HarmonicDistortionResult
    from ..electroacoustics.frequency_response import FrequencyResponseResult
    from ..electroacoustics.loudspeaker import LoudspeakerCharacteristics
    from ..electroacoustics.microphone import MicrophoneCharacteristics
    from ..electroacoustics.piston import RadiatingPistonResult
    from ..electroacoustics.swept_sine import SweptSineDistortionResult

#: Shared frequency-axis label of the electroacoustics renderers.
_FREQ_LABEL = "Frequency [Hz]"

#: Datasheet-panel palette shared by the IEC 60268-4/-5 ``.report()`` fiches and
#: the ``.plot()`` data sheets. The tolerance band is drawn as a *pale opaque*
#: fill, not a translucent one: the report's PDF vector backend (svglib) does
#: not preserve alpha, so a translucent fill would render as a solid block that
#: hides the response curve.
_C_TOL_BAND = _C_PRIMARY_LIGHT
#: Unicode ohm sign for the impedance-panel axis label.
_OHM_TEXT = "Ω"
#: IEC 60263 clause 3 polar reference-circle span, in dB (radius = 25 dB).
_POLAR_SPAN_DB = 25.0
#: Ordinate span of the loudspeaker on-axis response panel, in dB (a multiple of
#: 25 keeps the IEC 60263 25 dB-per-decade grid on whole gridlines).
_RESPONSE_SPAN_LSP = 50.0
#: Ordinate span of the microphone free-field response panel, in dB (one 25 dB
#: span suits the small deviations of a microphone response around 0 dB).
_RESPONSE_SPAN_MIC = 25.0

#: Spanish translations of the fixed strings rendered by the
#: electroacoustics ``.plot()`` renderers, keyed by their verbatim English
#: text. ``_t`` returns the English key unchanged for any language other
#: than ``"es"``, so the English output is byte-for-byte identical to the
#: pre-i18n renderers.
_STRINGS: dict[str, str] = {
    "Frequency [Hz]": "Frecuencia [Hz]",
    "Magnitude [dB]": "Magnitud [dB]",
    "Phase [deg]": "Fase [grados]",
    r"Coherence $\gamma^2$": r"Coherencia $\gamma^2$",
    "Harmonic order n  (f = n·f₁)": "Orden del armónico n  (f = n·f₁)",
    "Level re fundamental [dB]": "Nivel respecto al fundamental [dB]",
    "Harmonics": "Armónicos",
    "Frequency response": "Respuesta en frecuencia",
    " and coherence": " y coherencia",
    "THD [%]": "THD [%]",
    "Excitation frequency [Hz]": "Frecuencia de excitación [Hz]",
    "Swept-sine THD (Farina / Novak)": "THD de barrido sinusoidal (Farina / Novak)",
    "Harmonic frequency responses ({method} sweep)": "Respuestas en frecuencia de los armónicos (barrido {method})",
    "$R_1$ (resistance)": "$R_1$ (resistencia)",
    "$X_1$ (reactance)": "$X_1$ (reactancia)",
    r"Normalized radiation impedance $Z_r / \rho c S$": r"Impedancia de radiación normalizada $Z_r / \rho c S$",
    "Baffled circular piston radiation impedance": "Impedancia de radiación de un pistón circular con pantalla",
    # --- IEC 60268-4/-5 datasheet panels (shared by .report() and .plot()) ---
    "Sound pressure level [dB]": "Nivel de presión sonora [dB]",
    "On-axis response": "Respuesta en el eje",
    "Tolerance ±{tol} dB": "Tolerancia ±{tol} dB",
    "−10 dB reference": "Referencia −10 dB",
    "Effective range": "Rango efectivo",
    "Impedance |Z| [{ohm}]": "Impedancia |Z| [{ohm}]",
    "Impedance": "Impedancia",
    "Rated impedance": "Impedancia nominal",
    "80 % of rated": "80 % de la nominal",
    "Total harmonic distortion": "Distorsión armónica total",
    "Directional response": "Respuesta direccional",
    "Directional response at {freq} Hz": "Respuesta direccional a {freq} Hz",
    "Reference frequency": "Frecuencia de referencia",
    "Free-field response": "Respuesta en campo libre",
    "Relative response [dB]": "Respuesta relativa [dB]",
    "Band level [dB]": "Nivel de banda [dB]",
    "Inherent noise spectrum": "Espectro de ruido inherente",
    "{thd} % limit": "Límite del {thd} %",
    "Max. SPL": "SPL máx.",
    "Loudspeaker characteristics (IEC 60268-5)": "Características del altavoz (IEC 60268-5)",
    "Microphone characteristics (IEC 60268-4)": "Características del micrófono (IEC 60268-4)",
}


def _t(text: str, language: str = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


def plot_harmonic_distortion(
    result: "HarmonicDistortionResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes:
    """Harmonic amplitude spectrum with the harmonics marked and THD annotated.

    Draws the fundamental and its harmonics as a stem-style amplitude spectrum
    in dB relative to the fundamental, annotated with the THD (both
    conventions) and SINAD.

    :param result: A :class:`~phonometry.distortion.HarmonicDistortionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the marker ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma, format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    amps = np.asarray(result.harmonic_amplitudes, dtype=np.float64)
    tiny = np.finfo(np.float64).tiny
    ref = amps[0] if amps.size and amps[0] > 0.0 else 1.0
    levels_db = 20.0 * np.log10(np.maximum(amps, tiny) / ref)
    orders = np.arange(1, amps.size + 1)

    ax.vlines(orders, -160.0, levels_db, color=_C_PRIMARY, lw=1.5)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Harmonics", language))
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
    ax.set_xlabel(_t("Harmonic order n  (f = n·f₁)", language))
    ax.set_ylabel(_t("Level re fundamental [dB]", language))
    ax.set_xticks(orders)
    ax.set_ylim(bottom=-160.0, top=10.0)
    thd_f = decimal_comma(f"{result.thd_f * 100.0:.3g}", language)
    thd_r = decimal_comma(f"{result.thd_r * 100.0:.3g}", language)
    sinad = format_number(result.sinad_db, language, decimals=1)
    freq = decimal_comma(_format_freq(result.fundamental), language)
    ax.set_title(
        f"IEC 60268-3 THD = {thd_f}% (F), "
        f"{thd_r}% (R); SINAD = {sinad} dB "
        f"(f₁ = {freq}Hz)"
    )
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    localize_axes(ax, language)
    return ax

def plot_frequency_response(
    result: "FrequencyResponseResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes | np.ndarray:
    """Bode magnitude / phase and coherence of an estimated frequency response.

    Three stacked panels: the magnitude in dB, the phase in degrees and the
    ordinary coherence ``γ²``. With ``ax`` given, only the magnitude panel is
    drawn on it.

    :param result: A
        :class:`~phonometry.frequency_response.FrequencyResponseResult`.
    :param ax: Existing axes for the magnitude panel, or ``None`` for a fresh
        three-panel figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the magnitude ``plot`` call.
    :return: The magnitude-panel axes (``ax`` given) or the array of three axes.
    """
    from .._i18n import localize_axes

    freqs = np.asarray(result.frequencies, dtype=np.float64)
    mag = np.asarray(result.magnitude_db, dtype=np.float64)
    phase_deg = np.degrees(np.asarray(result.phase, dtype=np.float64))
    coh = np.asarray(result.coherence, dtype=np.float64)
    pos = freqs > 0.0
    color = kwargs.pop("color", _C_PRIMARY)

    def _magnitude(axm: Axes) -> None:
        kwargs.setdefault("label", f"|H| ({result.estimator})")
        axm.semilogx(freqs[pos], mag[pos], color=color, **kwargs)
        axm.set_ylabel(_t("Magnitude [dB]", language))
        axm.grid(True, which="both", alpha=0.3)
        axm.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    fmin, fmax = float(freqs[pos].min()), float(freqs[pos].max())
    if ax is not None:
        _magnitude(ax)
        ax.set_xlabel(_t("Frequency [Hz]", language))
        ax.set_title(f"{_t('Frequency response', language)} ({result.estimator})")
        format_frequency_axis(ax, fmin, fmax)
        localize_axes(ax, language)
        return ax

    axes = _new_axes_column(3, sharex=True, figsize=(8.0, 8.0))
    _magnitude(axes[0])
    axes[0].set_title(
        f"{_t('Frequency response', language)} ({result.estimator})"
        f"{_t(' and coherence', language)}"
    )
    axes[1].semilogx(freqs[pos], phase_deg[pos], color=_C_SECONDARY)
    axes[1].set_ylabel(_t("Phase [deg]", language))
    axes[1].grid(True, which="both", alpha=0.3)
    axes[2].semilogx(freqs[pos], coh[pos], color=_C_TERTIARY)
    axes[2].set_ylabel(_t(r"Coherence $\gamma^2$", language))
    axes[2].set_xlabel(_t("Frequency [Hz]", language))
    axes[2].set_ylim(0.0, 1.05)
    axes[2].grid(True, which="both", alpha=0.3)
    for axf in axes:
        format_frequency_axis(axf, fmin, fmax)
        localize_axes(axf, language)
    return axes


def plot_swept_sine_distortion(
    result: "SweptSineDistortionResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes | np.ndarray:
    """Harmonic frequency responses and THD(f) of a swept-sine measurement.

    Two stacked panels: the magnitudes of ``H1..HN`` in dB against their own
    frequency axes (each order drawn over its valid deconvolved band), and
    the total harmonic distortion in percent against the excitation
    frequency. With ``ax`` given, only the THD panel is drawn on it.

    :param result: A
        :class:`~phonometry.electroacoustics.swept_sine.SweptSineDistortionResult`.
    :param ax: Existing axes for the THD panel, or ``None`` for a fresh
        two-panel figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the THD ``plot`` call.
    :return: The THD axes (``ax`` given) or the array of two axes.
    """
    from .._i18n import localize_axes

    freqs = np.asarray(result.frequencies, dtype=np.float64)
    tiny = np.finfo(np.float64).tiny
    nyquist = result.fs / 2.0

    def _thd_panel(axt: Axes) -> None:
        kwargs.setdefault("color", _C_PRIMARY)
        kwargs.setdefault("label", "THD(f)")
        axt.loglog(
            result.thd_frequencies,
            100.0 * np.maximum(result.thd, tiny),
            **kwargs,
        )
        axt.set_ylabel(_t("THD [%]", language))
        axt.grid(True, which="both", alpha=0.3)
        axt.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _thd_panel(ax)
        ax.set_xlabel(_t("Excitation frequency [Hz]", language))
        ax.set_title(_t("Swept-sine THD (Farina / Novak)", language))
        format_frequency_axis(ax)
        localize_axes(ax, language)
        return ax

    axes = _new_axes_column(2, sharex=False, figsize=(8.0, 6.4))
    colors = (_C_PRIMARY, _C_SECONDARY, _C_TERTIARY)
    for k in range(result.n_harmonics):
        order = k + 1
        top = result.f2 if result.method == "farina" else order * result.f2
        band = (freqs >= order * result.f1) & (freqs <= min(top, nyquist))
        if not np.any(band):
            continue
        level = 20.0 * np.log10(
            np.maximum(np.abs(result.harmonic_responses[k][band]), tiny)
        )
        axes[0].semilogx(
            freqs[band],
            level,
            color=colors[k % len(colors)],
            ls="-" if k == 0 else "--",
            lw=1.6 if k == 0 else 1.2,
            label=f"$|H_{{{order}}}(f)|$",
        )
    axes[0].set_ylabel(_t("Magnitude [dB]", language))
    axes[0].set_xlabel(_t("Frequency [Hz]", language))
    axes[0].set_title(
        _t("Harmonic frequency responses ({method} sweep)", language, method=result.method)
    )
    axes[0].grid(True, which="both", alpha=0.3)
    axes[0].legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    format_frequency_axis(axes[0])
    localize_axes(axes[0], language)
    _thd_panel(axes[1])
    axes[1].set_xlabel(_t("Excitation frequency [Hz]", language))
    format_frequency_axis(axes[1])
    localize_axes(axes[1], language)
    return axes


def plot_piston_impedance(
    result: "RadiatingPistonResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes:
    """Normalized radiation resistance and reactance of a baffled piston.

    Draws the piston resistance ``R1(2ka)`` and reactance ``X1(2ka)`` against
    ``ka`` on a logarithmic ``ka`` axis (the classic Beranek & Mellow figure):
    ``R1`` rising to 1, ``X1`` peaking near ``ka ~ 0.5`` then decaying.

    :param result: A :class:`~phonometry.electroacoustics.piston.RadiatingPistonResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the resistance ``Axes.plot`` (its primary curve).
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    ka = np.asarray(result.ka, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", _t("$R_1$ (resistance)", language))
    ax.semilogx(ka, np.asarray(result.resistance), lw=1.8, **kwargs)
    ax.semilogx(ka, np.asarray(result.reactance), color=_C_SECONDARY, lw=1.8,
                ls="--", label=_t("$X_1$ (reactance)", language))
    ax.axhline(1.0, color=_C_TERTIARY, ls=":", lw=1.0,
               label=r"$R_1 \to 1$ ($ka \gg 1$)")
    ax.set_xlabel(r"$ka$")
    ax.set_ylabel(_t(r"Normalized radiation impedance $Z_r / \rho c S$", language))
    ax.set_title(_t("Baffled circular piston radiation impedance", language))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


# ---------------------------------------------------------------------------
# IEC 60268-4/-5 rated-characteristics data sheets
#
# The individual panel drawers below are the single source of truth for the
# loudspeaker (IEC 60268-5) and microphone (IEC 60268-4) characteristic
# graphs: the accredited ``.report()`` fiches (``phonometry._report``) and the
# public ``.plot()`` data sheets both compose them, so the two never diverge.
# Each drawer paints one panel onto a supplied axes, sets its own labels, grid,
# legend and (for the continuous-frequency panels) the 1k/2k-style major ticks,
# and leaves figure-level composition to the caller.
# ---------------------------------------------------------------------------


def _fmt_num(value: float, language: str) -> str:
    """A number with up to one decimal (locale separator), trailing ``.0`` dropped."""
    from .._i18n import format_number

    return format_number(value, language, decimals=1, trim=True)


def _freq_label(value: float, language: str) -> str:
    """A frequency rounded to the nearest hertz, locale-formatted."""
    from .._i18n import format_number

    return format_number(round(float(value)), language, decimals=0)


def _grid(ax: Axes) -> None:
    """The dotted both-scale grid the datasheet panels share."""
    ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.6)


def _draw_loudspeaker_response(
    result: "LoudspeakerCharacteristics", ax: Axes, *, language: str = "en"
) -> None:
    """On-axis SPL with the tolerance band, reference lines and range markers."""
    f = np.asarray(result.frequencies, dtype=np.float64)
    spl = np.asarray(result.spl_db, dtype=np.float64)
    ref = float(result.reference_level_db)
    tol = float(result.tolerance_db)
    top = float(np.ceil((max(float(np.max(spl)), ref + tol) + 2.0) / 5.0) * 5.0)
    ax.axhspan(ref - tol, ref + tol, facecolor=_C_TOL_BAND, edgecolor="none",
               zorder=0,
               label=_t("Tolerance ±{tol} dB", language, tol=_fmt_num(tol, language)))
    ax.axhline(ref, color=_C_EDGE, lw=0.8, ls="--")
    ax.axhline(ref - 10.0, color=_C_REFERENCE, lw=0.8, ls=":",
               label=_t("−10 dB reference", language))
    ax.semilogx(f, spl, color=_C_PRIMARY, lw=1.4,
                label=_t("On-axis response", language))
    lo, hi = result.effective_range
    for edge in (lo, hi):
        ax.axvline(edge, color=_C_TERTIARY, lw=0.9, ls="-.")
    ax.plot([], [], color=_C_TERTIARY, lw=0.9, ls="-.",
            label=_t("Effective range", language))
    ax.set_xlim(float(np.min(f)), float(np.max(f)))
    ax.set_ylim(top - _RESPONSE_SPAN_LSP, top)
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("Sound pressure level [dB]", language))
    ax.set_title(_t("On-axis response", language))
    _grid(ax)
    format_frequency_axis(ax, float(np.min(f)), float(np.max(f)))
    ax.legend(loc="lower center", fontsize="small", ncol=2, framealpha=0.85)


def _draw_impedance(
    result: "LoudspeakerCharacteristics", ax: Axes, *, language: str = "en"
) -> None:
    """Impedance modulus with the rated and 80 %-of-rated reference lines (16)."""
    ax.semilogx(result.impedance_frequencies, result.impedance_modulus,
                color=_C_PRIMARY, lw=1.3)
    ax.axhline(result.rated_impedance, color=_C_EDGE, lw=0.8, ls="--",
               label=_t("Rated impedance", language))
    ax.axhline(0.8 * result.rated_impedance, color=_C_REFERENCE, lw=0.8, ls=":",
               label=_t("80 % of rated", language))
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("Impedance |Z| [{ohm}]", language, ohm=_OHM_TEXT))
    ax.set_ylim(bottom=0.0)
    _grid(ax)
    ax.set_title(_t("Impedance", language))
    ax.legend(loc="upper right", fontsize="small")
    format_frequency_axis(ax)


def _draw_loudspeaker_thd(
    result: "LoudspeakerCharacteristics", ax: Axes, *, language: str = "en"
) -> None:
    """Total harmonic distortion against frequency, in percent (24.1)."""
    ax.semilogx(result.thd_frequencies, result.thd_percent, color=_C_PRIMARY, lw=1.3)
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("THD [%]", language))
    ax.set_ylim(bottom=0.0)
    _grid(ax)
    ax.set_title(_t("Total harmonic distortion", language))
    format_frequency_axis(ax)


def _draw_datasheet_polar(
    result: "LoudspeakerCharacteristics | MicrophoneCharacteristics",
    ax: Any, *, language: str = "en",
) -> None:
    """Polar directivity to the IEC 60263 clause 3 25 dB reference-circle scale."""
    angles = np.asarray(result.polar_angles_deg, dtype=np.float64)
    levels = np.clip(np.asarray(result.polar_db, dtype=np.float64), -_POLAR_SPAN_DB, 0.0)
    # Mirror a one-sided pattern about the reference axis for a full rose.
    if float(np.min(angles)) >= 0.0:
        angles = np.concatenate([-angles[::-1], angles])
        levels = np.concatenate([levels[::-1], levels])
    theta = np.radians(angles)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.plot(theta, levels, color=_C_PRIMARY, lw=1.3)
    ax.set_ylim(-_POLAR_SPAN_DB, 0.0)
    # Reference circle at 0 dB (relative level, IEC 60263 3.3); radial ticks
    # every 5 dB (multiple of 5 for a 25 dB radius, IEC 60263 3.2).
    ax.set_yticks([-20.0, -15.0, -10.0, -5.0, 0.0])
    ax.set_yticklabels(["-20", "", "-10", "", "0 dB"], fontsize="x-small")
    ax.tick_params(axis="x", labelsize="x-small")
    ax.grid(True, ls=":", lw=0.4, alpha=0.7)
    title = _t("Directional response", language)
    if result.polar_frequency is not None:
        title = _t("Directional response at {freq} Hz", language,
                   freq=_freq_label(result.polar_frequency, language))
    ax.set_title(title)


def _draw_microphone_response(
    result: "MicrophoneCharacteristics", ax: Axes, *, language: str = "en"
) -> None:
    """Free-field response with the tolerance band and reference markers (12)."""
    f = np.asarray(result.frequencies, dtype=np.float64)
    rel = np.asarray(result.response_db, dtype=np.float64)
    tol = float(result.tolerance_db)
    top = float(np.ceil((max(float(np.max(rel)), tol) + 2.0) / 5.0) * 5.0)
    ax.axhspan(-tol, tol, facecolor=_C_TOL_BAND, edgecolor="none", zorder=0,
               label=_t("Tolerance ±{tol} dB", language, tol=_fmt_num(tol, language)))
    ax.axhline(0.0, color=_C_EDGE, lw=0.8, ls="--")
    ax.axvline(result.reference_frequency, color=_C_SECONDARY, lw=0.8, ls=":",
               label=_t("Reference frequency", language))
    ax.semilogx(f, rel, color=_C_PRIMARY, lw=1.4,
                label=_t("Free-field response", language))
    lo, hi = result.effective_range
    for edge in (lo, hi):
        ax.axvline(edge, color=_C_TERTIARY, lw=0.9, ls="-.")
    ax.plot([], [], color=_C_TERTIARY, lw=0.9, ls="-.",
            label=_t("Effective range", language))
    ax.set_xlim(float(np.min(f)), float(np.max(f)))
    ax.set_ylim(top - _RESPONSE_SPAN_MIC, top)
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("Relative response [dB]", language))
    ax.set_title(_t("Free-field response", language))
    _grid(ax)
    format_frequency_axis(ax, float(np.min(f)), float(np.max(f)))
    ax.legend(loc="lower center", fontsize="small", ncol=2, framealpha=0.85)


def _draw_noise_spectrum(
    result: "MicrophoneCharacteristics", ax: Axes, *, language: str = "en"
) -> None:
    """Inherent-noise equivalent band-level spectrum (17.2 b)."""
    ax.semilogx(result.noise_frequencies, result.noise_band_levels_db,
                color=_C_PRIMARY, lw=1.3)
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_t("Band level [dB]", language))
    _grid(ax)
    ax.set_title(_t("Inherent noise spectrum", language))
    format_frequency_axis(ax)


def _draw_microphone_distortion(
    result: "MicrophoneCharacteristics", ax: Axes, *, language: str = "en"
) -> None:
    """Total harmonic distortion against sound pressure level (14.2/15.2)."""
    ax.plot(np.asarray(result.distortion_spl_db, dtype=np.float64),
            np.asarray(result.distortion_thd_percent, dtype=np.float64),
            color=_C_PRIMARY, lw=1.3)
    ax.axhline(result.max_spl_thd_percent, color=_C_REFERENCE, lw=0.8, ls=":",
               label=_t("{thd} % limit", language,
                        thd=_fmt_num(result.max_spl_thd_percent, language)))
    if result.max_spl_db is not None:
        ax.axvline(result.max_spl_db, color=_C_EDGE, lw=0.8, ls="--",
                   label=_t("Max. SPL", language))
    ax.set_xlabel(_t("Sound pressure level [dB]", language))
    ax.set_ylabel(_t("THD [%]", language))
    ax.set_ylim(bottom=0.0)
    _grid(ax)
    ax.set_title(_t("Total harmonic distortion", language))
    ax.legend(loc="upper left", fontsize="small")


def _datasheet(
    result: Any,
    response_drawer: Any,
    optional: "list[tuple[str, Any]]",
    title: str,
    language: str,
) -> "npt.NDArray[Any]":
    """Compose a rated-characteristics data sheet from its panel drawers.

    The response panel spans the full width of the top row; the optional panels
    flow into a two-column body below it, so a four-panel sheet is a wide
    response over a 2x2-style body with no cramped, overlapping axes. Each
    ``("polar" | "cart", drawer)`` entry is drawn on an axes created with its
    own projection. Returns the panel axes as an array (the sibling multi-panel
    ``.plot()`` return convention).
    """
    from matplotlib.gridspec import GridSpec

    from .._i18n import localize_axes

    plt = _import_pyplot()
    body_rows = (len(optional) + 1) // 2
    fig = plt.figure(figsize=(11.0, 3.6 + 3.0 * body_rows))
    gs = GridSpec(1 + body_rows, 2, figure=fig, hspace=0.6, wspace=0.28)
    response_drawer(result, fig.add_subplot(gs[0, :]), language=language)
    for i, (kind, drawer) in enumerate(optional):
        cell = fig.add_subplot(
            gs[1 + i // 2, i % 2],
            projection="polar" if kind == "polar" else None,
        )
        drawer(result, cell, language=language)
    fig.suptitle(title, fontweight="bold")
    for ax in fig.axes:
        localize_axes(ax, language)
    return np.asarray(fig.axes, dtype=object)


def plot_loudspeaker_characteristics(
    result: "LoudspeakerCharacteristics", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any,
) -> "Axes | npt.NDArray[Any]":
    """IEC 60268-5 loudspeaker rated-characteristics data sheet.

    A multi-panel figure: the on-axis SPL response with its tolerance band and
    effective-range markers, and, for the data supplied, the impedance modulus
    ``|Z|``, the total harmonic distortion against frequency and the polar
    directivity. With ``ax`` given only the on-axis response is drawn on it.

    :param result: A
        :class:`~phonometry.electroacoustics.loudspeaker.LoudspeakerCharacteristics`.
    :param ax: Existing axes for the on-axis response, or ``None`` for a fresh
        multi-panel data sheet.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Ignored placeholder kept for a uniform ``.plot()`` signature.
    :return: The response-panel axes (``ax`` given) or the array of panel axes.
    """
    from .._i18n import localize_axes

    del kwargs  # the panels are fixed datasheet artists; no primary override
    if ax is not None:
        _draw_loudspeaker_response(result, ax, language=language)
        localize_axes(ax, language)
        return ax

    optional: list[tuple[str, Any]] = []
    if result.impedance_frequencies is not None:
        optional.append(("cart", _draw_impedance))
    if result.thd_frequencies is not None:
        optional.append(("cart", _draw_loudspeaker_thd))
    if result.polar_angles_deg is not None:
        optional.append(("polar", _draw_datasheet_polar))
    return _datasheet(
        result, _draw_loudspeaker_response, optional,
        _t("Loudspeaker characteristics (IEC 60268-5)", language), language,
    )


def plot_microphone_characteristics(
    result: "MicrophoneCharacteristics", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any,
) -> "Axes | npt.NDArray[Any]":
    """IEC 60268-4 microphone rated-characteristics data sheet.

    A multi-panel figure: the free-field response with its tolerance band and
    effective-range markers, and, for the data supplied, the polar directional
    pattern, the inherent-noise band spectrum and the total harmonic distortion
    against sound pressure level. With ``ax`` given only the free-field response
    is drawn on it.

    :param result: A
        :class:`~phonometry.electroacoustics.microphone.MicrophoneCharacteristics`.
    :param ax: Existing axes for the free-field response, or ``None`` for a
        fresh multi-panel data sheet.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Ignored placeholder kept for a uniform ``.plot()`` signature.
    :return: The response-panel axes (``ax`` given) or the array of panel axes.
    """
    from .._i18n import localize_axes

    del kwargs
    if ax is not None:
        _draw_microphone_response(result, ax, language=language)
        localize_axes(ax, language)
        return ax

    optional: list[tuple[str, Any]] = []
    if result.polar_angles_deg is not None:
        optional.append(("polar", _draw_datasheet_polar))
    if result.noise_frequencies is not None:
        optional.append(("cart", _draw_noise_spectrum))
    if result.distortion_spl_db is not None:
        optional.append(("cart", _draw_microphone_distortion))
    return _datasheet(
        result, _draw_microphone_response, optional,
        _t("Microphone characteristics (IEC 60268-4)", language), language,
    )
