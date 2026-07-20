#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the noise_control domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _new_axes,
    format_frequency_axis,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..noise_control.enclosures import EnclosureResult
    from ..noise_control.hvac import HvacSpectrumResult
    from ..noise_control.silencers import ReactiveSilencerResult

_FREQ_LABEL = "Frequency [Hz]"

#: English -> {language: string} lookup for the fixed labels/titles/legends of
#: the noise-control renderers. English ids map to themselves so ``_t(key,
#: "en")`` returns the verbatim original string.
_STRINGS: dict[str, dict[str, str]] = {
    "Frequency [Hz]": {"en": "Frequency [Hz]", "es": "Frecuencia [Hz]"},
    "Band": {"en": "Band", "es": "Banda"},
    "Transmission loss": {"en": "Transmission loss", "es": "Pérdida por transmisión"},
    "Insertion loss": {"en": "Insertion loss", "es": "Pérdida por inserción"},
    "Resonance": {"en": "Resonance", "es": "Resonancia"},
    "Loss [dB]": {"en": "Loss [dB]", "es": "Pérdida [dB]"},
    "Reactive silencer": {"en": "Reactive silencer", "es": "Silenciador reactivo"},
    "Sound power level [dB re 1 pW]": {
        "en": "Sound power level [dB re 1 pW]",
        "es": "Nivel de potencia acústica [dB re 1 pW]",
    },
    "Attenuation [dB]": {"en": "Attenuation [dB]", "es": "Atenuación [dB]"},
    "Panel R": {"en": "Panel R", "es": "R del panel"},
    "Interior correction C": {
        "en": "Interior correction C",
        "es": "Corrección interior C",
    },
    "Insertion loss (R - C)": {
        "en": "Insertion loss (R - C)",
        "es": "Pérdida por inserción (R - C)",
    },
    "Level [dB]": {"en": "Level [dB]", "es": "Nivel [dB]"},
    "Machine enclosure insertion loss": {
        "en": "Machine enclosure insertion loss",
        "es": "Pérdida por inserción de encapsulado de máquina",
    },
}


def _t(key: str, language: str) -> str:
    """Look up the localised string for ``key`` (falls back to ``key``)."""
    return _STRINGS.get(key, {}).get(language, key)


def plot_reactive_silencer(
    result: "ReactiveSilencerResult", ax: "Axes | None" = None,
    language: str = "en", **kwargs: Any
) -> "Axes":
    """Transmission (and insertion) loss of a reactive silencer over frequency.

    :param result: A
        :class:`~phonometry.noise_control.silencers.ReactiveSilencerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the transmission-loss ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequencies, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Transmission loss", language))
    kwargs.setdefault("lw", 1.8)
    ax.plot(f, np.asarray(result.transmission_loss), **kwargs)
    if result.insertion_loss is not None:
        ax.plot(f, np.asarray(result.insertion_loss), color=_C_SECONDARY,
                lw=1.4, ls="--", label=_t("Insertion loss", language))
    if result.resonances is not None:
        labeled = False
        for fr in np.atleast_1d(np.asarray(result.resonances)):
            if f.min() <= fr <= f.max():
                ax.axvline(fr, color=_C_TERTIARY, ls=":", lw=1.0,
                           label=_t("Resonance", language) if not labeled else None)
                labeled = True
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Loss [dB]", language))
    ax.set_title(f"{_t('Reactive silencer', language)}: {result.kind}")
    ax.grid(True, which="both", alpha=0.3)
    format_frequency_axis(ax)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_hvac_spectrum(
    result: "HvacSpectrumResult", ax: "Axes | None" = None, language: str = "en",
    **kwargs: Any
) -> "Axes":
    """Per-frequency HVAC attenuation or regenerated sound power level.

    :param result: A :class:`~phonometry.noise_control.hvac.HvacSpectrumResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequencies, dtype=np.float64)
    is_power = result.quantity == "sound_power_level"
    kwargs.setdefault("color", _C_SECONDARY if is_power else _C_PRIMARY)
    kwargs.setdefault("label", result.label)
    kwargs.setdefault("lw", 1.8)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("ms", 3)
    ax.plot(f, np.asarray(result.values), **kwargs)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(
        _t("Sound power level [dB re 1 pW]", language) if is_power
        else _t("Attenuation [dB]", language)
    )
    ax.set_title(result.label)
    ax.grid(True, which="both", alpha=0.3)
    format_frequency_axis(ax)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_enclosure(
    result: "EnclosureResult", ax: "Axes | None" = None, language: str = "en",
    **kwargs: Any
) -> "Axes":
    """Panel R, interior correction C and net insertion loss of an enclosure.

    :param result: An
        :class:`~phonometry.noise_control.enclosures.EnclosureResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the insertion-loss ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    n = np.asarray(result.insertion_loss).size
    if result.frequencies is not None:
        x = np.asarray(result.frequencies, dtype=np.float64)
        continuous = True
    else:
        x = np.arange(n, dtype=np.float64)
        continuous = False
    ax.plot(x, np.asarray(result.panel_transmission_loss), color=_C_REFERENCE,
            lw=1.3, ls="--", marker="s", ms=3, label=_t("Panel R", language))
    ax.plot(x, np.asarray(result.correction), color=_C_TERTIARY, lw=1.3,
            ls=":", marker="^", ms=3, label=_t("Interior correction C", language))
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Insertion loss (R - C)", language))
    kwargs.setdefault("lw", 1.9)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("ms", 3)
    ax.plot(x, np.asarray(result.insertion_loss), **kwargs)
    ax.set_ylabel(_t("Level [dB]", language))
    ax.set_title(_t("Machine enclosure insertion loss", language))
    ax.grid(True, which="both", alpha=0.3)
    if continuous:
        ax.set_xlabel(_t(_FREQ_LABEL, language))
        format_frequency_axis(ax)
    else:
        ax.set_xlabel(_t("Band", language))
        ax.set_xticks(x)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax
