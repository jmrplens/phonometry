#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the emission domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_TERTIARY,
    _band_axis,
    _bar_width,
    _freq_axis,
    _hatch_invalid,
    _new_axes,
    _plot_band_level_bars,
    _sound_power_designation,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from ..emission.vibration_sound_power import VibrationSoundPowerResult
    from ..emission.intensity import IntensityResult
    from ..emission.sound_power import SoundPowerResult
    from ..emission.sound_power_intensity import SoundPowerIntensityResult
    from ..emission.sound_power_reverberation import ReverberationSoundPowerResult

#: English -> {language: string} lookup for the fixed labels/titles/legends of
#: the emission-domain renderers. English ids map to themselves so ``_t(key,
#: "en")`` returns the verbatim original string.
_STRINGS: dict[str, dict[str, str]] = {
    "Band": {"en": "Band", "es": "Banda"},
    "Sound power level LW [dB]": {
        "en": "Sound power level LW [dB]",
        "es": "Nivel de potencia acústica LW [dB]",
    },
    "sound power spectrum": {
        "en": "sound power spectrum",
        "es": "espectro de potencia acústica",
    },
    "Non-positive band": {"en": "Non-positive band", "es": "Banda no positiva"},
    "Pressure level Lp": {"en": "Pressure level Lp", "es": "Nivel de presión Lp"},
    "Intensity level LI": {
        "en": "Intensity level LI",
        "es": "Nivel de intensidad LI",
    },
    "Level [dB]": {"en": "Level [dB]", "es": "Nivel [dB]"},
    "Pressure-intensity index δpI [dB]": {
        "en": "Pressure-intensity index δpI [dB]",
        "es": "Índice presión-intensidad δpI [dB]",
    },
    r"Sound power level $L_W$ [dB re 1 pW]": {
        "en": r"Sound power level $L_W$ [dB re 1 pW]",
        "es": r"Nivel de potencia acústica $L_W$ [dB re 1 pW]",
    },
    "ISO/TS 7849 sound power from surface vibration": {
        "en": "ISO/TS 7849 sound power from surface vibration",
        "es": "Potencia sonora por vibración superficial ISO/TS 7849",
    },
}


def _t(key: str, language: str) -> str:
    """Look up the localised string for ``key`` (falls back to ``key``)."""
    return _STRINGS.get(key, {}).get(language, key)


def plot_sound_power(
    result: (
        "SoundPowerResult | ReverberationSoundPowerResult"
        " | SoundPowerIntensityResult | Any"
    ),
    ax: Axes | None = None,
    language: str = "en",
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
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the band :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    lw = np.asarray(result.sound_power_level, dtype=np.float64)
    n = lw.size
    freqs = getattr(result, "frequencies", None)
    if freqs is None:
        positions = _band_axis(
            ax, [f"{_t('Band', language)} {i + 1}" for i in range(n)],
            xlabel=_t("Band", language)
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

    ax.set_ylabel(_t("Sound power level LW [dB]", language))
    designation = _sound_power_designation(result)
    lwa = float(result.sound_power_level_a)
    if np.isfinite(lwa):
        ax.set_title(
            f"{designation} {_t('sound power spectrum', language)}  "
            f"(LWA = {format_number(lwa, language, decimals=1)} dB(A))"
        )
    else:
        ax.set_title(f"{designation} {_t('sound power spectrum', language)}")
    if np.any(neg):
        ax.plot([], [], color=_C_MUTED, marker="s", ls="",
                label=_t("Non-positive band", language))
    if np.any(neg) or "label" in kwargs:
        ax.legend(loc="best", fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_intensity(
    result: IntensityResult, ax: Axes | None = None, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Pressure vs intensity level per band with the pressure-intensity index.

    Draws Lp and LI per band and, on a twin axis, the per-band
    pressure-intensity index ``Lp - LI`` (the reactivity indicator); the
    total index is annotated in the title.

    :param result: An :class:`~phonometry.intensity.IntensityResult` with
        per-band data (obtained by requesting a band ``fraction``).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the pressure-level curve ``plot`` call.
    :return: The axes.
    :raises ValueError: If the result carries no per-band data.
    """
    from .._i18n import format_number, localize_axes

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
    kwargs.setdefault("label", _t("Pressure level Lp", language))
    ax.plot(freqs, lp, "o-", **kwargs)
    ax.plot(freqs, li, "s--", color=_C_REFERENCE, label=_t("Intensity level LI", language))
    _freq_axis(ax, freqs)
    ax.set_ylabel(_t("Level [dB]", language))
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
    twin.set_ylabel(_t("Pressure-intensity index δpI [dB]", language))

    lines, labels = ax.get_legend_handles_labels()
    tlines, tlabels = twin.get_legend_handles_labels()
    ax.legend(lines + tlines, labels + tlabels, loc="best", fontsize="small")
    ax.set_title(
        "ISO 9614 Lp vs LI  "
        f"(total δpI = {format_number(result.total_pressure_intensity_index, language, decimals=1)} dB)"
    )
    localize_axes(ax, language)
    return ax


def plot_vibration_sound_power(
    result: "VibrationSoundPowerResult", ax: Axes | None = None,
    language: str = "en", **kwargs: Any
) -> Axes:
    """Radiated sound power level per band (ISO/TS 7849).

    :param result: A :class:`~phonometry.vibration_sound_power.VibrationSoundPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the bar ``plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = _plot_band_level_bars(
        ax, result.sound_power_level, result.frequencies, result.total_level,
        ylabel=_t(r"Sound power level $L_W$ [dB re 1 pW]", language),
        title=_t("ISO/TS 7849 sound power from surface vibration", language),
        **kwargs,
    )
    localize_axes(ax, language)
    return ax
