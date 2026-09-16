#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the noise_control domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_SECONDARY_LIGHT,
    _C_TERTIARY,
    _new_axes,
    _plot_two_runs,
    format_frequency_axis,
    style_default,
    theme_fill,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..noise_control.cabin_insulation import CabinInsulationResult
    from ..noise_control.duct_modes import DuctModeResult
    from ..noise_control.duct_path import DuctPathResult
    from ..noise_control.enclosure_insulation import EnclosureInsulationResult
    from ..noise_control.enclosures import EnclosureResult
    from ..noise_control.hvac import HvacSpectrumResult
    from ..noise_control.room_to_room import RoomToRoomResult
    from ..noise_control.screen_in_situ import ScreenInSituResult
    from ..noise_control.silencer_in_situ import SilencerInSituResult
    from ..noise_control.silencer_measurement import OperatingLine
    from ..noise_control.silencers import ReactiveSilencerResult

_FREQ_LABEL = "Frequency [Hz]"
_LEVEL_LABEL = "Level [dB]"
_TL_LABEL = "Transmission loss"
_ATTENUATION_LABEL = "Attenuation [dB]"

#: Spanish translations of the fixed labels/titles/legends rendered by the
#: noise-control ``.plot()`` renderers, keyed by their verbatim English
#: text. ``_t`` returns the English key unchanged for any language other
#: than ``"es"``, so the English output is byte-for-byte identical to the
#: pre-i18n renderers.
_STRINGS: dict[str, str] = {
    "Frequency [Hz]": "Frecuencia [Hz]",
    "Least-squares fit": "Ajuste por mínimos cuadrados",
    "Measured points": "Puntos medidos",
    "Duty (flow rate or total pressure loss)": "Régimen (caudal o pérdida de presión total)",
    "Operating line (ISO 5135 5.5.2)": "Recta de servicio (ISO 5135 5.5.2)",
    "worst point": "peor punto",
    "Extrapolated": "Extrapolado",
    "dB/decade": "dB/década",
    "Band": "Banda",
    _TL_LABEL: "Pérdida por transmisión",
    "Insertion loss": "Pérdida por inserción",
    "Resonance": "Resonancia",
    "Loss [dB]": "Pérdida [dB]",
    "Reactive silencer": "Silenciador reactivo",
    "Sound power level [dB re 1 pW]": "Nivel de potencia acústica [dB re 1 pW]",
    _ATTENUATION_LABEL: "Atenuación [dB]",
    "Panel $R$": "$R$ del panel",
    "Interior correction $C$": "Corrección interior $C$",
    "Insertion loss ($R - C$)": "Pérdida por inserción ($R - C$)",
    _LEVEL_LABEL: "Nivel [dB]",
    "Machine enclosure insertion loss": "Pérdida por inserción de encapsulado de máquina",
    "Sound power level [dB]": "Nivel de potencia acústica [dB]",
    "Received level": "Nivel recibido",
    "Source": "Fuente",
    "Duct-borne noise path": "Trayecto de ruido por conductos",
    "Mode order ($p$, $q$)": "Orden del modo ($p$, $q$)",
    "Cut-on frequency [Hz]": "Frecuencia de corte [Hz]",
    "No flow": "Sin flujo",
    "Plane waves only": "Solo ondas planas",
    "Duct higher-order-mode cut-on": "Corte de modos superiores del conducto",
    "Source room": "Recinto emisor",
    "Receiving room": "Recinto receptor",
    "Noise reduction": "Reducción de ruido",
    "Loss and noise reduction [dB]": "Pérdida y reducción de ruido [dB]",
    "Room-to-room transmission": "Transmisión entre recintos",
    "Without the enclosure": "Sin el encapsulado",
    "With the enclosure": "Con el encapsulado",
    "Enclosure insulation": "Aislamiento del encapsulado",
    "In the room": "En la sala",
    "Inside the cabin": "Dentro de la cabina",
    "Cabin insulation": "Aislamiento de la cabina",
    "Insulation [dB]": "Aislamiento [dB]",
    "Sound pressure level [dB]": "Nivel de presión acústica [dB]",
    "Level difference $D_{tps}$": "Diferencia de niveles $D_{tps}$",
    "Level difference $D_{ips}$": "Diferencia de niveles $D_{ips}$",
    "Transmission loss $D_{ts}$": "Pérdida por transmisión $D_{ts}$",
    "Insertion loss $D_{is}$": "Pérdida por inserción $D_{is}$",
    "A silencer measured where it stands": "Un silenciador medido donde está",
    "Level and loss [dB]": "Nivel y pérdida [dB]",
    "Unscreened level $L_{p1}$": "Nivel sin apantallar $L_{p1}$",
    "Screened level $L_{p2}$": "Nivel apantallado $L_{p2}$",
    "Attenuation $D_p$": "Atenuación $D_p$",
    "A screen measured where it stands": "Una pantalla medida donde está",
}


def _t(text: str, language: str = "en") -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    return _STRINGS.get(text, text) if language == "es" else text


def plot_reactive_silencer(
    result: ReactiveSilencerResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
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
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t(_TL_LABEL, language))
    style_default(kwargs, "lw", 1.8)
    ax.plot(f, np.asarray(result.transmission_loss), **kwargs)
    if result.insertion_loss is not None:
        ax.plot(
            f,
            np.asarray(result.insertion_loss),
            color=_C_SECONDARY,
            lw=1.4,
            ls="--",
            label=_t("Insertion loss", language),
        )
    if result.resonances is not None:
        labeled = False
        for fr in np.atleast_1d(np.asarray(result.resonances)):
            if f.min() <= fr <= f.max():
                ax.axvline(
                    fr,
                    color=_C_TERTIARY,
                    ls=":",
                    lw=1.0,
                    label=_t("Resonance", language) if not labeled else None,
                )
                labeled = True
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Loss [dB]", language))
    ax.set_title(f"{_t('Reactive silencer', language)}: {result.kind}")
    ax.grid(visible=True, which="both", alpha=0.3)
    format_frequency_axis(ax, language=language)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_hvac_spectrum(
    result: HvacSpectrumResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
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
    style_default(kwargs, "color", _C_SECONDARY if is_power else _C_PRIMARY)
    kwargs.setdefault("label", result.label)
    style_default(kwargs, "lw", 1.8)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 3)
    ax.plot(f, np.asarray(result.values), **kwargs)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(
        _t("Sound power level [dB re 1 pW]", language)
        if is_power
        else _t(_ATTENUATION_LABEL, language)
    )
    ax.set_title(result.label)
    ax.grid(visible=True, which="both", alpha=0.3)
    format_frequency_axis(ax, language=language)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


#: Colours cycled over the intermediate spectra of a duct-path cascade. They are
#: mid-tone on purpose: a sequential colormap puts its ends at near-black and
#: near-yellow, which one theme or the other loses against its background, and
#: these lines are supporting detail behind the received level and the criterion
#: curve, so they have to stay legible in both.
_CASCADE_COLOURS: tuple[str, ...] = (
    _C_SECONDARY,
    _C_TERTIARY,
    _C_QUATERNARY,
    _C_MUTED,
    "#17becf",
    _C_SECONDARY_LIGHT,
)

#: Line styles the cascade steps through each time the colour cycle wraps, so a
#: long path stays readable past six elements.
_CASCADE_STYLES: tuple[str, ...] = ("-", "--", ":")

#: Longest element name carried into the cascade legend before it is elided; the
#: full description belongs in the table, not in a corner of the chart.
_LEGEND_CHARS = 30

#: The largest number of cascade series (duct-path elements plus the source)
#: that still get individual legend entries; past it the per-element labels are
#: suppressed so the legend does not drown the chart.
_LEGEND_MAX_SERIES = 10

#: The largest series count whose legend still fits in a single column; above
#: it the cascade legend wraps to two columns.
_LEGEND_SINGLE_COLUMN_MAX = 4


def _cascade_series(result: DuctPathResult) -> list[tuple[str, np.ndarray]]:
    """The labelled spectra of a duct path, from the source to the receiver."""
    if result.contributions:
        return [(name, np.asarray(values)) for name, values in result.contributions]
    series: list[tuple[str, np.ndarray]] = [
        (result.source_label, np.asarray(result.source_level))
    ]
    series += [(stage.label, np.asarray(stage.level)) for stage in result.stages]
    return series


def plot_duct_path(
    result: DuctPathResult, ax: Axes | None = None, language: str = "en", **kwargs: Any
) -> Axes:
    """Cascade of a duct-borne noise path against the room-criterion curve.

    One faint line per element shows where the octave-band spectrum stands
    after that element, from the source at the top to the received level, which
    is drawn thick; the design criterion curve, when the path declares one, is
    overlaid as a dashed reference.

    :param result: A
        :class:`~phonometry.noise_control.duct_path.DuctPathResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the received-level ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import decimal_comma, fmt_minus, localize_axes

    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequencies, dtype=np.float64)
    series = _cascade_series(result)
    for position, (name, values) in enumerate(series):
        colour = _CASCADE_COLOURS[position % len(_CASCADE_COLOURS)]
        style = _CASCADE_STYLES[
            (position // len(_CASCADE_COLOURS)) % len(_CASCADE_STYLES)
        ]
        label = (
            name if len(name) <= _LEGEND_CHARS else name[: _LEGEND_CHARS - 1] + "\u2026"
        )
        ax.semilogx(
            f,
            values,
            ls=style,
            color=colour,
            lw=1.1,
            alpha=0.85,
            label=label if len(series) <= _LEGEND_MAX_SERIES else None,
        )
    curve = result.criterion_curve
    if curve is not None and result.target is not None:
        target = decimal_comma(fmt_minus(result.target, "g"), language)
        ax.semilogx(
            f,
            curve,
            ls="--",
            color=_C_REFERENCE,
            lw=1.5,
            label=f"{result.criterion} {target}",
        )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Received level", language))
    style_default(kwargs, "lw", 2.4)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 4)
    ax.semilogx(f, np.asarray(result.received_level), **kwargs)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.set_title(f"{_t('Duct-borne noise path', language)}: {result.label}")
    ax.grid(visible=True, which="both", alpha=0.3)
    format_frequency_axis(ax, language=language)
    ax.legend(
        loc="upper right",
        fontsize="xx-small",
        ncol=2 if len(series) > _LEGEND_SINGLE_COLUMN_MAX else 1,
        framealpha=0.85,
    )
    localize_axes(ax, language)
    return ax


def plot_room_to_room(
    result: RoomToRoomResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Source-room level, received level and criterion curve of a partition.

    The two reverberant spectra bracket the design criterion curve on the left
    axis; the transmission loss of the partition and the noise reduction it
    actually delivers share a twin axis on the right, which is where the point
    of Equation (4.101) shows: the two are not the same number.

    :param result: A
        :class:`~phonometry.noise_control.room_to_room.RoomToRoomResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the received-level ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import decimal_comma, fmt_minus, localize_axes

    ax = ax if ax is not None else _new_axes()
    f = np.asarray(result.frequencies, dtype=np.float64)
    ax.semilogx(
        f,
        np.asarray(result.source_level),
        color=_C_SECONDARY,
        lw=1.6,
        ls="--",
        marker="s",
        ms=4,
        label=_t("Source room", language),
    )
    curve = result.criterion_curve
    if curve is not None and result.target is not None:
        target = decimal_comma(fmt_minus(result.target, "g"), language)
        ax.semilogx(
            f,
            curve,
            ls=":",
            color=_C_REFERENCE,
            lw=1.5,
            label=f"{result.criterion} {target}",
        )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Receiving room", language))
    style_default(kwargs, "lw", 2.4)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 4)
    ax.semilogx(f, np.asarray(result.received_level), **kwargs)
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.set_title(f"{_t('Room-to-room transmission', language)}: {result.label}")
    ax.grid(visible=True, which="both", alpha=0.3)

    twin = ax.twinx()
    twin.plot(
        f,
        np.asarray(result.transmission_loss),
        color=_C_MUTED,
        lw=1.2,
        ls="--",
        label=_t(_TL_LABEL, language),
    )
    twin.plot(
        f,
        np.asarray(result.noise_reduction),
        color=_C_TERTIARY,
        lw=1.5,
        ls="-.",
        marker="^",
        ms=3,
        label=_t("Noise reduction", language),
    )
    twin.set_ylabel(_t("Loss and noise reduction [dB]", language), color=_C_TERTIARY)
    twin.tick_params(axis="y", labelcolor=_C_TERTIARY)
    twin.grid(visible=False)
    handles, labels = ax.get_legend_handles_labels()
    extra_handles, extra_labels = twin.get_legend_handles_labels()
    ax.legend(
        handles + extra_handles,
        labels + extra_labels,
        loc="best",
        fontsize="small",
        framealpha=0.85,
        ncol=2,
    )
    # The twin axis resets the shared log-frequency formatting, so the ticks are
    # set last and on both axes.
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    format_frequency_axis(ax, language=language)
    format_frequency_axis(twin, language=language)
    localize_axes(ax, language)
    localize_axes(twin, language)
    return ax


def plot_duct_modes(
    result: DuctModeResult, ax: Axes | None = None, language: str = "en", **kwargs: Any
) -> Axes:
    """Cut-on frequency of each higher-order duct mode, with and without flow.

    The still-air cut-on of every mode is drawn beside the value the mean flow
    shifts it to, and the band below the first cut-on -- where the duct carries
    plane waves only, and where the plane-wave methods of the library are valid
    -- is shaded.

    :param result: A
        :class:`~phonometry.noise_control.duct_modes.DuctModeResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the with-flow ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    x = np.arange(len(result.modes), dtype=np.float64)
    ax.axhspan(
        0.0,
        result.plane_wave_limit,
        color=theme_fill(_C_PRIMARY, ax),
        zorder=0,
        label=_t("Plane waves only", language),
    )
    ax.plot(
        x,
        np.asarray(result.cut_on_no_flow),
        ls="--",
        color=_C_MUTED,
        marker="s",
        ms=4,
        lw=1.3,
        label=_t("No flow", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault(
        "label", f"$M$ = {format_number(result.mach, language, decimals=3)}"
    )
    style_default(kwargs, "lw", 1.8)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 5)
    ax.plot(x, np.asarray(result.cut_on), **kwargs)
    ax.set_xticks(x)
    ax.set_xticklabels([f"({p}, {q})" for p, q in result.modes])
    ax.set_xlabel(_t("Mode order ($p$, $q$)", language))
    ax.set_ylabel(_t("Cut-on frequency [Hz]", language))
    ax.set_title(f"{_t('Duct higher-order-mode cut-on', language)}: {result.label}")
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_enclosure(
    result: EnclosureResult, ax: Axes | None = None, language: str = "en", **kwargs: Any
) -> Axes:
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
    ax.plot(
        x,
        np.asarray(result.panel_transmission_loss),
        color=_C_REFERENCE,
        lw=1.3,
        ls="--",
        marker="s",
        ms=3,
        label=_t("Panel $R$", language),
    )
    ax.plot(
        x,
        np.asarray(result.correction),
        color=_C_TERTIARY,
        lw=1.3,
        ls=":",
        marker="^",
        ms=3,
        label=_t("Interior correction $C$", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Insertion loss ($R - C$)", language))
    style_default(kwargs, "lw", 1.9)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 3)
    ax.plot(x, np.asarray(result.insertion_loss), **kwargs)
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.set_title(_t("Machine enclosure insertion loss", language))
    ax.grid(visible=True, which="both", alpha=0.3)
    if continuous:
        ax.set_xlabel(_t(_FREQ_LABEL, language))
        format_frequency_axis(ax, language=language)
    else:
        ax.set_xlabel(_t("Band", language))
        ax.set_xticks(x)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_operating_line(
    result: OperatingLine,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The ISO 5135 5.5.2 fit: the test points and the line through them.

    The duty runs on a logarithmic axis, because that is the variable the
    least-squares fit is made in. The measured points are drawn as they were
    given, the fitted line spans the whole range 5.5.2 allows it to be read
    over, and the part of that range which is extrapolation rather than
    interpolation is shaded, because clause 8 k) requires a report to say
    which of its values were not measured directly.

    :param result: An
        :class:`~phonometry.noise_control.silencer_measurement.OperatingLine`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``Axes.plot`` for the fitted line.
    :return: The axes.
    """
    import matplotlib.ticker as mticker

    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    low, high = result.valid_range
    span = np.geomspace(low, high, 128)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.8)
    kwargs.setdefault(
        "label",
        _t("Least-squares fit", language)
        + " ("
        + decimal_comma(f"{result.slope:.1f}", language)
        + f" {_t('dB/decade', language)})",
    )
    ax.plot(span, result.slope * np.log10(span) + result.intercept, **kwargs)
    ax.plot(
        np.asarray(result.duty),
        np.asarray(result.levels),
        linestyle="none",
        marker="o",
        ms=5,
        color=_C_SECONDARY,
        label=_t("Measured points", language),
    )
    wash = theme_fill(_C_MUTED, ax)
    for index, (lower, upper) in enumerate(
        ((low, result.smallest_duty), (result.largest_duty, high))
    ):
        ax.axvspan(
            lower,
            upper,
            color=wash,
            zorder=0,
            label=_t("Extrapolated", language) if index == 0 else None,
        )
    ax.set_xscale("log")
    # The duty spans a decade or two of a flow rate in m3/s or a pressure in
    # Pa, and the default log axis labels that 10^-1 rather than 0,1, which
    # reads as an exponent and not as a duty. Ticks at 1, 2 and 5 of each
    # decade, written plainly, give a reader the numbers the test points were
    # actually taken at.
    ax.xaxis.set_major_locator(mticker.LogLocator(base=10.0, subs=(1.0, 2.0, 5.0)))
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda value, _pos: decimal_comma(f"{value:g}", language))
    )
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.set_xlabel(_t("Duty (flow rate or total pressure loss)", language))
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.set_title(
        _t("Operating line (ISO 5135 5.5.2)", language)
        + f" - {_t('worst point', language)} "
        + decimal_comma(f"{result.maximum_deviation:.2f}", language)
        + " dB"
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="upper left", fontsize="small")
    localize_axes(ax, language)
    return ax


_INSULATION_LABEL = "Insulation [dB]"
_PRESSURE_LEVEL_LABEL = "Sound pressure level [dB]"
_POWER_LEVEL_LABEL = "Sound power level [dB]"
#: The symbol each quantity of ISO 11546 is reported under.
_ENCLOSURE_SYMBOLS = {
    "sound_power": "$D_W$",
    "sound_pressure": "$D_p$",
    "reciprocity": "$D_{pr}$",
}


def plot_enclosure_insulation(
    result: EnclosureInsulationResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The two runs of ISO 11546 and the insulation between them.

    :param result: An
        :class:`~phonometry.noise_control.enclosure_insulation.EnclosureInsulationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the insulation ``Axes.plot``.
    :return: The axes.
    """
    level_label = (
        _POWER_LEVEL_LABEL
        if result.quantity == "sound_power"
        else _PRESSURE_LEVEL_LABEL
    )
    return _plot_two_runs(
        ax,
        None if result.frequencies is None else np.asarray(result.frequencies),
        np.asarray(result.level_without, dtype=np.float64),
        np.asarray(result.level_with, dtype=np.float64),
        np.asarray(result.insulation, dtype=np.float64),
        labels=(
            _t("Without the enclosure", language),
            _t("With the enclosure", language),
            _ENCLOSURE_SYMBOLS[result.quantity],
        ),
        ylabel=_t(level_label, language),
        difference_label=_t(_INSULATION_LABEL, language),
        frequency_label=_t(_FREQ_LABEL, language),
        band_label=_t("Band", language),
        title=_t("Enclosure insulation", language),
        language=language,
        kwargs=kwargs,
    )


def plot_cabin_insulation(
    result: CabinInsulationResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The room, the inside of the cabin and the insulation between them.

    :param result: A
        :class:`~phonometry.noise_control.cabin_insulation.CabinInsulationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the insulation ``Axes.plot``.
    :return: The axes.
    """
    symbol = "$D'_p$" if result.apparent else "$D_p$"
    return _plot_two_runs(
        ax,
        None if result.frequencies is None else np.asarray(result.frequencies),
        np.asarray(result.room_levels, dtype=np.float64),
        np.asarray(result.cabin_levels, dtype=np.float64),
        np.asarray(result.insulation, dtype=np.float64),
        labels=(
            _t("In the room", language),
            _t("Inside the cabin", language),
            symbol,
        ),
        ylabel=_t(_PRESSURE_LEVEL_LABEL, language),
        difference_label=_t(_INSULATION_LABEL, language),
        frequency_label=_t(_FREQ_LABEL, language),
        band_label=_t("Band", language),
        title=_t("Cabin insulation", language),
        language=language,
        kwargs=kwargs,
    )


def plot_silencer_in_situ(
    result: SilencerInSituResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The level difference of ISO 11820 and the loss it becomes.

    :param result: A
        :class:`~phonometry.noise_control.silencer_in_situ.SilencerInSituResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the loss ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    difference = np.asarray(result.level_difference_db, dtype=np.float64)
    loss = np.asarray(result.loss_db, dtype=np.float64)
    continuous = result.frequencies is not None
    x = (
        np.asarray(result.frequencies, dtype=np.float64)
        if continuous
        else np.arange(difference.size, dtype=np.float64)
    )
    transmission = result.quantity == "transmission"
    difference_label = _t(
        "Level difference $D_{tps}$" if transmission else "Level difference $D_{ips}$",
        language,
    )
    loss_label = _t(
        "Transmission loss $D_{ts}$" if transmission else "Insertion loss $D_{is}$",
        language,
    )
    ax.fill_between(
        x, difference, loss, color=theme_fill(_C_TERTIARY, ax), lw=0.0, zorder=1
    )
    ax.plot(
        x,
        difference,
        color=_C_SECONDARY,
        lw=1.5,
        ls="--",
        marker="s",
        ms=3,
        label=difference_label,
        zorder=3,
    )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 2.0)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 3.5)
    style_default(kwargs, "label", loss_label)
    kwargs.setdefault("zorder", 4)
    ax.plot(x, loss, **kwargs)
    ax.set_ylabel(_t("Level and loss [dB]", language))
    ax.set_title(_t("A silencer measured where it stands", language))
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small", framealpha=1.0)
    if continuous:
        ax.set_xlabel(_t(_FREQ_LABEL, language))
        format_frequency_axis(ax, language=language)
    else:
        ax.set_xlabel(_t("Band", language))
        ax.set_xticks(x)
    localize_axes(ax, language)
    return ax


def plot_screen_in_situ(
    result: ScreenInSituResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The two levels of ISO 11821 and the attenuation between them.

    :param result: A
        :class:`~phonometry.noise_control.screen_in_situ.ScreenInSituResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the attenuation ``Axes.plot``.
    :return: The axes.
    """
    return _plot_two_runs(
        ax,
        None if result.frequencies is None else np.asarray(result.frequencies),
        np.asarray(result.unscreened_levels_db, dtype=np.float64),
        np.asarray(result.screened_levels_db, dtype=np.float64),
        np.asarray(result.attenuation_db, dtype=np.float64),
        labels=(
            _t("Unscreened level $L_{p1}$", language),
            _t("Screened level $L_{p2}$", language),
            _t("Attenuation $D_p$", language),
        ),
        ylabel=_t(_PRESSURE_LEVEL_LABEL, language),
        difference_label=_t(_ATTENUATION_LABEL, language),
        frequency_label=_t(_FREQ_LABEL, language),
        band_label=_t("Band", language),
        title=_t("A screen measured where it stands", language),
        language=language,
        kwargs=kwargs,
    )
