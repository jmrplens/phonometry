#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the electroacoustics domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_PRIMARY,
    _C_SECONDARY,
    _C_TERTIARY,
    _LEGEND_UPPER_RIGHT,
    _format_freq,
    _new_axes,
    _new_axes_column,
    format_frequency_axis,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from ..electroacoustics.distortion import HarmonicDistortionResult
    from ..electroacoustics.frequency_response import FrequencyResponseResult
    from ..electroacoustics.piston import RadiatingPistonResult
    from ..electroacoustics.swept_sine import SweptSineDistortionResult

#: Shared frequency-axis label of the electroacoustics renderers.
_FREQ_LABEL = "Frequency [Hz]"

_STRINGS = {
    "freq": {"en": "Frequency [Hz]", "es": "Frecuencia [Hz]"},
    "magnitude": {"en": "Magnitude [dB]", "es": "Magnitud [dB]"},
    "phase": {"en": "Phase [deg]", "es": "Fase [grados]"},
    "coherence": {"en": r"Coherence $\gamma^2$", "es": r"Coherencia $\gamma^2$"},
    "harmonic_order": {"en": "Harmonic order n  (f = n·f₁)",
                       "es": "Orden del armónico n  (f = n·f₁)"},
    "level_re_fund": {"en": "Level re fundamental [dB]",
                      "es": "Nivel respecto al fundamental [dB]"},
    "harmonics": {"en": "Harmonics", "es": "Armónicos"},
    "fr_title": {"en": "Frequency response", "es": "Respuesta en frecuencia"},
    "and_coherence": {"en": " and coherence", "es": " y coherencia"},
    "thd_pct": {"en": "THD [%]", "es": "THD [%]"},
    "excitation_freq": {"en": "Excitation frequency [Hz]",
                        "es": "Frecuencia de excitación [Hz]"},
    "swept_thd_title": {"en": "Swept-sine THD (Farina / Novak)",
                        "es": "THD de barrido sinusoidal (Farina / Novak)"},
    "harmonic_resp_title_with_method": {
        "en": "Harmonic frequency responses ({method} sweep)",
        "es": "Respuestas en frecuencia de los armónicos (barrido {method})"},
    "piston_resistance": {"en": r"$R_1$ (resistance)",
                          "es": r"$R_1$ (resistencia)"},
    "piston_reactance": {"en": r"$X_1$ (reactance)",
                         "es": r"$X_1$ (reactancia)"},
    "piston_ylabel": {"en": r"Normalized radiation impedance $Z_r / \rho c S$",
                      "es": r"Impedancia de radiación normalizada $Z_r / \rho c S$"},
    "piston_title": {"en": "Baffled circular piston radiation impedance",
                     "es": "Impedancia de radiación de un pistón circular con pantalla"},
}


def _t(key: str, language: str, **fmt: Any) -> str:
    """Return the localised fixed string for *key* (optionally ``str.format``ed)."""
    text = _STRINGS[key][language]
    return text.format(**fmt) if fmt else text


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
    kwargs.setdefault("label", _t("harmonics", language))
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
    ax.set_xlabel(_t("harmonic_order", language))
    ax.set_ylabel(_t("level_re_fund", language))
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
        axm.set_ylabel(_t("magnitude", language))
        axm.grid(True, which="both", alpha=0.3)
        axm.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    fmin, fmax = float(freqs[pos].min()), float(freqs[pos].max())
    if ax is not None:
        _magnitude(ax)
        ax.set_xlabel(_t("freq", language))
        ax.set_title(f"{_t('fr_title', language)} ({result.estimator})")
        format_frequency_axis(ax, fmin, fmax)
        localize_axes(ax, language)
        return ax

    axes = _new_axes_column(3, sharex=True, figsize=(8.0, 8.0))
    _magnitude(axes[0])
    axes[0].set_title(
        f"{_t('fr_title', language)} ({result.estimator})"
        f"{_t('and_coherence', language)}"
    )
    axes[1].semilogx(freqs[pos], phase_deg[pos], color=_C_SECONDARY)
    axes[1].set_ylabel(_t("phase", language))
    axes[1].grid(True, which="both", alpha=0.3)
    axes[2].semilogx(freqs[pos], coh[pos], color=_C_TERTIARY)
    axes[2].set_ylabel(_t("coherence", language))
    axes[2].set_xlabel(_t("freq", language))
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
        axt.set_ylabel(_t("thd_pct", language))
        axt.grid(True, which="both", alpha=0.3)
        axt.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _thd_panel(ax)
        ax.set_xlabel(_t("excitation_freq", language))
        ax.set_title(_t("swept_thd_title", language))
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
    axes[0].set_ylabel(_t("magnitude", language))
    axes[0].set_xlabel(_t("freq", language))
    axes[0].set_title(
        _t("harmonic_resp_title_with_method", language, method=result.method)
    )
    axes[0].grid(True, which="both", alpha=0.3)
    axes[0].legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    format_frequency_axis(axes[0])
    localize_axes(axes[0], language)
    _thd_panel(axes[1])
    axes[1].set_xlabel(_t("excitation_freq", language))
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
    kwargs.setdefault("label", _t("piston_resistance", language))
    ax.semilogx(ka, np.asarray(result.resistance), lw=1.8, **kwargs)
    ax.semilogx(ka, np.asarray(result.reactance), color=_C_SECONDARY, lw=1.8,
                ls="--", label=_t("piston_reactance", language))
    ax.axhline(1.0, color=_C_TERTIARY, ls=":", lw=1.0,
               label=r"$R_1 \to 1$ ($ka \gg 1$)")
    ax.set_xlabel(r"$ka$")
    ax.set_ylabel(_t("piston_ylabel", language))
    ax.set_title(_t("piston_title", language))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax
