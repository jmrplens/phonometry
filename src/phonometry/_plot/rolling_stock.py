#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers of railway rolling stock noise and its reference track.

ISO 3095 (the pass-by record, the tests of three runs, the stationary mesh,
Annexes A, C, E and G and the reference track verdict), EN 15610 (the rail
roughness spectrum) and EN 15461 (the track decay rates). Every renderer is
reached lazily from a result's ``.plot()``.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _new_axes,
    place_legend_clear,
    style_pop,
    styled,
    theme_fill,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes

    from ..environment.sources.acoustic_roughness import AcousticRoughnessSpectrum
    from ..environment.sources.rolling_stock_noise import (
        AdjacentVehicleNeutrality,
        PassByMeasurement,
        PassByUncertainty,
        ReferenceTrackCheck,
        RiseSpeedResult,
        RollingStockTestResult,
        RoughnessComparability,
        SmallRoughnessDeviation,
        StationaryTestResult,
    )
    from ..environment.sources.track_decay import TrackDecayRate

#: Axis labels the renderers share, named once so the table and the axes agree.
_WAVELENGTH_LABEL = r"Wavelength $\lambda$ [cm]"
_ROUGHNESS_LABEL = r"Roughness level $L_r$ [dB re 1 µm]"
_DECAY_LABEL = "Track decay rate [dB/m]"
_FREQUENCY_LABEL = "Frequency [Hz]"
_TIME_LABEL = "Time [s]"
_LEVEL_LABEL = "A-weighted level [dB]"
_POSITION_LABEL = "Position"

_STRINGS: dict[str, str] = {
    _WAVELENGTH_LABEL: r"Longitud de onda $\lambda$ [cm]",
    _ROUGHNESS_LABEL: r"Nivel de rugosidad $L_r$ [dB re 1 µm]",
    _DECAY_LABEL: "Tasa de decaimiento de la vía [dB/m]",
    _FREQUENCY_LABEL: "Frecuencia [Hz]",
    _TIME_LABEL: "Tiempo [s]",
    _LEVEL_LABEL: "Nivel ponderado A [dB]",
    _POSITION_LABEL: "Posición",
    "Measured": "Medida",
    "Limit": "Límite",
    "Lower limit": "Límite inferior",
    "Unsuitable band": "Banda no apta",
    "EN 15610 acoustic rail roughness": "Rugosidad acústica del carril EN 15610",
    "EN 15461 vertical track decay rate": "Tasa de decaimiento vertical de la vía EN 15461",
    "EN 15461 lateral track decay rate": "Tasa de decaimiento lateral de la vía EN 15461",
    "Measurement interval $T$": "Intervalo de medición $T$",
    "ISO 3095 pass-by": "Paso ISO 3095",
    "Runs": "Pasadas",
    "Rounded mean": "Media redondeada",
    "Result": "Resultado",
    "Spread above 3 dB": "Dispersión mayor de 3 dB",
    "Unit level": "Nivel de la unidad",
    "Mean over the sets": "Media de las series",
    "ISO 3095 stationary test": "Ensayo a vehículo parado ISO 3095",
    "Slopes rising 10 dB": "Pendientes que suben 10 dB",
    "ISO 3095 Annex A rise speed": "Velocidad de subida ISO 3095 anexo A",
    "no slope rises 10 dB": "ninguna pendiente sube 10 dB",
    "With the adjacent vehicle": "Con el vehículo contiguo",
    "Units under test": "Unidades en ensayo",
    "Neutral": "Neutro",
    "Not neutral": "No neutro",
    "Allowance of 2 dB": "Margen de 2 dB",
    "ISO 3095 6.3.4 acoustic neutrality": "Neutralidad acústica ISO 3095 6.3.4",
    "Measured spectrum": "Espectro medido",
    "Revised spectrum": "Espectro revisado",
    "Roughness correction": "Corrección por rugosidad",
    "Correction [dB]": "Corrección [dB]",
    "ISO 3095 Annex C": "ISO 3095 anexo C",
    "Annex C": "anexo C",
    "accepted": "aceptada",
    "not accepted": "no aceptada",
    "Situation 1": "Situación 1",
    "Situation 2": "Situación 2",
    "Maximum envelope": "Envolvente máxima",
    "Minimum envelope": "Envolvente mínima",
    "ISO 3095 Annex E": "ISO 3095 anexo E",
    # "apartado" keeps the clause number's dot through the decimal comma.
    "Reference track, ISO 3095 6.2": "Vía de referencia, ISO 3095 apartado 6.2",
    "passes": "cumple",
    "fails": "no cumple",
    "Vertical": "Vertical",
    "Lateral": "Lateral",
    "Share of the variance": "Fracción de la varianza",
    "ISO 3095 Annex G uncertainty": "Incertidumbre ISO 3095 anexo G",
    "constant speed": "velocidad constante",
    "starting, maximum level": "arranque, nivel máximo",
    "starting, averaged level": "arranque, nivel promediado",
    "braking": "frenado",
    "ISO 3095 test": "Ensayo ISO 3095",
}

#: The words a test method is titled with, keyed by its identifier.
_METHOD_TITLES: dict[str, str] = {
    "constant_speed": "constant speed",
    "acceleration_maximum": "starting, maximum level",
    "acceleration_averaged": "starting, averaged level",
    "braking": "braking",
}

#: The wavelengths, in centimetres, the roughness axis is labelled at.
_WAVELENGTH_TICKS_CM = (40.0, 20.0, 10.0, 5.0, 2.5, 1.0, 0.5, 0.25)

#: The decay-rate axis EN 15461 9.2 prescribes, in dB/m.
_DECAY_AXIS_DB_PER_M = (0.01, 100.0)

#: ISO 3095 9.3: the largest spread of the runs of one position, in decibels.
_MAXIMUM_SPREAD_DB = 3.0

#: The R10 preferred numbers, the mantissas of the nominal band frequencies.
_R10 = (1.0, 1.25, 1.6, 2.0, 2.5, 3.15, 4.0, 5.0, 6.3, 8.0)


def _t(text: str, language: str = "en") -> str:
    """Localise a fixed string; English is returned verbatim."""
    return _STRINGS.get(text, text) if language == "es" else text


def _roughness_axis(ax: Axes, wavelengths_m: list[float], language: str) -> None:
    """A logarithmic wavelength axis in centimetres, longest on the left."""
    import matplotlib.ticker as mticker

    centimetres = [100.0 * w for w in wavelengths_m]
    low, high = min(centimetres) / 1.15, max(centimetres) * 1.15
    ax.set_xscale("log")
    ax.set_xlim(high, low)
    ticks = [t for t in _WAVELENGTH_TICKS_CM if low <= t <= high]
    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
    separator = "," if language == "es" else "."
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda value, _pos: f"{value:g}".replace(".", separator))
    )
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.set_xlabel(_t(_WAVELENGTH_LABEL, language))
    ax.set_ylabel(_t(_ROUGHNESS_LABEL, language))


def _draw_roughness_limit(
    ax: Axes, limit_db: Mapping[float, float], language: str
) -> None:
    wavelengths = sorted(limit_db, reverse=True)
    ax.plot(
        [100.0 * w for w in wavelengths],
        [limit_db[w] for w in wavelengths],
        color=_C_REFERENCE,
        lw=1.6,
        ls="--",
        marker="s",
        ms=3.5,
        label=_t("Limit", language),
    )


def plot_roughness_spectrum(
    spectrum: AcousticRoughnessSpectrum,
    ax: Axes | None = None,
    *,
    limit_db: Mapping[float, float] | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """A rail roughness spectrum against decreasing wavelength, EN 15610 clause 9.

    :param spectrum: The spectrum.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param limit_db: A limit to draw with it, nominal wavelength in metres to
        level.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the spectrum line.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    wavelengths = [float(w) for w in spectrum.wavelengths_m]
    ax.plot(
        [100.0 * w for w in wavelengths],
        spectrum.levels_db,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.8,
            marker="o",
            ms=3.5,
            label=_t("Measured", language),
        ),
    )
    if limit_db is not None:
        _draw_roughness_limit(ax, limit_db, language)
        wavelengths += [float(w) for w in limit_db]
    _roughness_axis(ax, wavelengths, language)
    ax.set_title(_t("EN 15610 acoustic rail roughness", language))
    ax.grid(visible=True, which="major", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def _band_positions(frequencies_hz: list[float]) -> dict[int, float]:
    """Equidistant positions of one-third octave bands, keyed by band index."""
    bands = sorted({round(10.0 * math.log10(f)) for f in frequencies_hz})
    return {band: float(i) for i, band in enumerate(bands)}


def _nominal_frequency(band: int) -> float:
    """The nominal frequency of base-ten band ``band``, from the R10 series."""
    mantissa = band % 10
    exponent = band // 10
    value = _R10[mantissa]
    return value * 10.0**exponent if exponent >= 0 else value / 10.0 ** (-exponent)


def _band_label(band: int, language: str) -> str:
    from .common import _format_freq

    return _format_freq(_nominal_frequency(band), language)


def _band_axis(ax: Axes, positions: dict[int, float], language: str) -> None:
    ax.set_xticks(list(positions.values()))
    ax.set_xticklabels(
        [_band_label(b, language) for b in positions], rotation=45, ha="right"
    )
    ax.set_xlabel(_t(_FREQUENCY_LABEL, language))


def _draw_decay(
    ax: Axes,
    rates: TrackDecayRate,
    positions: dict[int, float],
    language: str,
    kwargs: dict[str, Any],
    *,
    label: str,
    color: str,
) -> None:
    x = [positions[round(10.0 * math.log10(f))] for f in rates.frequencies_hz]
    ax.plot(
        x,
        rates.decay_rates_db_per_m,
        **styled(kwargs, color=color, lw=1.8, marker="o", ms=3.5, label=label),
    )
    unsuitable = ~np.asarray(rates.suitable)
    if np.any(unsuitable):
        ax.plot(
            np.asarray(x)[unsuitable],
            rates.decay_rates_db_per_m[unsuitable],
            linestyle="none",
            marker="x",
            ms=8,
            color=_C_SECONDARY,
            label=_t("Unsuitable band", language),
        )


def _draw_decay_limit(
    ax: Axes,
    limit: Mapping[float, float],
    positions: dict[int, float],
    label: str,
    color: str,
) -> None:
    frequencies = sorted(limit)
    ax.plot(
        [positions[round(10.0 * math.log10(f))] for f in frequencies],
        [limit[f] for f in frequencies],
        color=color,
        lw=1.4,
        ls="--",
        label=label,
    )


def _decay_axis(ax: Axes, positions: dict[int, float], language: str) -> None:
    ax.set_yscale("log")
    ax.set_ylim(*_DECAY_AXIS_DB_PER_M)
    _band_axis(ax, positions, language)
    ax.set_ylabel(_t(_DECAY_LABEL, language))


def plot_track_decay_rate(
    rates: TrackDecayRate,
    ax: Axes | None = None,
    *,
    limit_db_per_m: Mapping[float, float] | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Track decay rates on the logarithmic axis of EN 15461 9.2.

    :param rates: The decay rates.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param limit_db_per_m: A lower limit, nominal frequency to rate.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the rate line.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    frequencies = [float(f) for f in rates.frequencies_hz]
    if limit_db_per_m is not None:
        frequencies += [float(f) for f in limit_db_per_m]
    positions = _band_positions(frequencies)
    _draw_decay(
        ax,
        rates,
        positions,
        language,
        kwargs,
        label=_t("Measured", language),
        color=_C_PRIMARY,
    )
    if limit_db_per_m is not None:
        _draw_decay_limit(
            ax, limit_db_per_m, positions, _t("Lower limit", language), _C_REFERENCE
        )
    _decay_axis(ax, positions, language)
    ax.set_title(_t(f"EN 15461 {rates.direction} track decay rate", language))
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_pass_by_measurement(
    result: PassByMeasurement,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The level history of a pass-by with its measurement interval, as ISO 3095 Figure 7.

    :param result: The pass-by record.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the level history.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    ax.axvspan(
        result.start_s,
        result.end_s,
        color=theme_fill(_C_PRIMARY, ax),
        label=_t("Measurement interval $T$", language),
    )
    ax.plot(
        result.times_s,
        result.levels_db,
        **styled(kwargs, color=_C_PRIMARY, lw=1.4, label=r"$L_{p\mathrm{AF}}(t)$"),
    )
    ax.hlines(
        result.equivalent_level_db,
        result.start_s,
        result.end_s,
        color=_C_SECONDARY,
        lw=2.0,
        label=(
            r"$L_{p\mathrm{Aeq},T}$ = "
            f"{format_number(result.equivalent_level_db, language)} dB"
        ),
    )
    inside = (result.times_s >= result.start_s) & (result.times_s <= result.end_s)
    if np.any(inside):
        peak = int(np.flatnonzero(inside)[np.argmax(result.levels_db[inside])])
        ax.plot(
            [result.times_s[peak]],
            [result.max_level_db],
            linestyle="none",
            marker="v",
            ms=8,
            color=_C_REFERENCE,
            label=(
                r"$L_{p\mathrm{AFmax}}$ = "
                f"{format_number(result.max_level_db, language)} dB"
            ),
        )
    ax.set_xlabel(_t(_TIME_LABEL, language))
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.set_title(_t("ISO 3095 pass-by", language))
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_stationary_test(
    result: StationaryTestResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The mean level of every position of a stationary mesh and the unit level.

    :param result: The stationary test.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the position bars.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = np.arange(result.levels_db.shape[1]) + 1
    means = 10.0 * np.log10(np.mean(10.0 ** (result.levels_db / 10.0), axis=0))
    ax.bar(
        positions,
        means,
        width=0.7,
        **styled(kwargs, color=_C_PRIMARY, label=_t("Mean over the sets", language)),
    )
    ax.axhline(
        result.reported_level_db,
        color=_C_SECONDARY,
        lw=2.0,
        label=(
            f"{_t('Unit level', language)}: "
            f"{format_number(result.reported_level_db, language, decimals=0)} dB"
        ),
    )
    low = float(np.min(result.levels_db)) - 5.0
    high = float(np.max(result.levels_db)) + 4.0
    ax.set_ylim(low, high)
    ax.set_xticks(positions)
    ax.set_xlabel(_t(_POSITION_LABEL, language))
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.set_title(_t("ISO 3095 stationary test", language))
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_rolling_stock_test(
    result: RollingStockTestResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Every run of a test of three runs, each position's rounded mean and the result.

    :param result: The test.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the mean markers.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes
    from ..environment.sources._shared import _TOLERANCE

    ax = ax if ax is not None else _new_axes()
    x = np.arange(len(result.positions), dtype=np.float64)
    spreads = result.spreads_db
    for i, position in enumerate(result.positions):
        runs = result.samples_db[position]
        ax.plot(
            np.full(len(runs), x[i]),
            runs,
            linestyle="none",
            marker="o",
            ms=5,
            color=_C_MUTED,
            label=_t("Runs", language) if i == 0 else None,
        )
        if spreads[position] > _MAXIMUM_SPREAD_DB + _TOLERANCE:
            ax.plot(
                [x[i]],
                [max(runs) + 0.6],
                linestyle="none",
                marker="x",
                ms=8,
                color=_C_REFERENCE,
                label=_t("Spread above 3 dB", language),
            )
    reported = result.reported_levels_db
    ax.plot(
        x,
        [reported[p] for p in result.positions],
        **styled(
            kwargs,
            linestyle="none",
            marker="D",
            ms=8,
            color=_C_PRIMARY,
            label=_t("Rounded mean", language),
        ),
    )
    ax.axhline(
        result.final_level_db,
        color=_C_SECONDARY,
        lw=1.6,
        ls="--",
        label=(
            f"{_t('Result', language)}: "
            f"{format_number(result.final_level_db, language, decimals=0)} dB"
        ),
    )
    ax.set_xticks(x)
    ax.set_xticklabels(list(result.positions))
    ax.set_xlim(-0.6, len(result.positions) - 0.4)
    ax.set_xlabel(_t(_POSITION_LABEL, language))
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.set_title(
        f"{_t('ISO 3095 test', language)}: "
        f"{_t(_METHOD_TITLES[result.method], language)}"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_rise_speed(
    result: RiseSpeedResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """A level history with the slopes that rise 10 dB and the steepest rise, Annex A.

    :param result: The rise speed result.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the level history.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    ax.plot(
        result.times_s,
        result.levels_db,
        **styled(kwargs, color=_C_PRIMARY, lw=1.4, label=r"$L_{p\mathrm{AF}}(t)$"),
    )
    for i, (start, stop) in enumerate(result.slopes):
        ax.plot(
            result.times_s[start : stop + 1],
            result.levels_db[start : stop + 1],
            color=_C_SECONDARY,
            lw=2.6,
            label=_t("Slopes rising 10 dB", language) if i == 0 else None,
        )
    speed = result.rise_speed_db_per_s
    title = _t("ISO 3095 Annex A rise speed", language)
    if speed is None:
        title += f": {_t('no slope rises 10 dB', language)}"
    else:
        title += f": $s$ = {format_number(speed, language, decimals=0)} dB/s"
    ax.set_xlabel(_t(_TIME_LABEL, language))
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.set_title(title)
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_adjacent_neutrality(
    result: AdjacentVehicleNeutrality,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The two pass-by levels of 6.3.4 and the 2 dB the adjacent vehicle may add.

    :param result: The neutrality verdict.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the bars.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    levels = [result.unit_level_db, result.with_adjacent_level_db]
    # Each level is written under its bar, not over it: the allowance line
    # runs 2 dB above the first bar, which is where the second one ends in
    # the very case the plot exists to show.
    labels = [
        f"{_t(name, language)}\n{format_number(level, language)} dB"
        for name, level in zip(
            ("Units under test", "With the adjacent vehicle"), levels, strict=True
        )
    ]
    ax.bar(
        [0.0, 1.0],
        levels,
        width=0.55,
        **styled(
            kwargs, color=[_C_PRIMARY, _C_TERTIARY if result.passes else _C_REFERENCE]
        ),
    )
    ax.axhline(
        result.unit_level_db + 2.0,
        color=_C_SECONDARY,
        lw=1.6,
        ls="--",
        label=_t("Allowance of 2 dB", language),
    )
    ax.set_xticks([0.0, 1.0])
    ax.set_xticklabels(labels)
    ax.set_ylim(min(levels) - 6.0, max(levels) + 4.0)
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    verdict = _t("Neutral", language) if result.passes else _t("Not neutral", language)
    ax.set_title(
        f"{_t('ISO 3095 6.3.4 acoustic neutrality', language)}: {verdict} "
        f"(+{format_number(result.difference_db, language)} dB)"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_small_roughness_deviation(
    result: SmallRoughnessDeviation,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The measured and revised noise spectra of ISO 3095 Annex C, and the correction.

    :param result: The Annex C verdict.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured spectrum.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = _band_positions([float(f) for f in result.frequencies_hz])
    x = [positions[round(10.0 * math.log10(f))] for f in result.frequencies_hz]
    ax.plot(
        x,
        result.noise_levels_db,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.8,
            marker="o",
            ms=3.5,
            label=_t("Measured spectrum", language),
        ),
    )
    ax.plot(
        x,
        result.revised_noise_levels_db,
        color=_C_SECONDARY,
        lw=1.6,
        ls="--",
        marker="s",
        ms=3.0,
        label=_t("Revised spectrum", language),
    )
    _band_axis(ax, positions, language)
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    verdict = (
        _t("accepted", language) if result.passes else _t("not accepted", language)
    )
    ax.set_title(
        f"{_t('ISO 3095 Annex C', language)}: "
        rf"$\Delta L_{{p\mathrm{{Aeq}},T_p}}$ = {format_number(result.impact_db, language, decimals=2)} dB, "
        f"{verdict}"
    )
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_roughness_comparability(
    result: RoughnessComparability,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The two roughness spectra of Annex E and their envelopes, as Figure E.1.

    :param result: The Annex E comparison.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the maximum envelope.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    upper = result.envelope_max
    lower = result.envelope_min
    centimetres = 100.0 * np.asarray(upper.wavelengths_m)
    ax.fill_between(
        centimetres,
        lower.levels_db,
        upper.levels_db,
        color=theme_fill(_C_QUATERNARY, ax),
    )
    ax.plot(
        centimetres,
        upper.levels_db,
        **styled(
            kwargs, color=_C_QUATERNARY, lw=2.2, label=_t("Maximum envelope", language)
        ),
    )
    ax.plot(
        centimetres,
        lower.levels_db,
        color=_C_TERTIARY,
        lw=2.2,
        label=_t("Minimum envelope", language),
    )
    for spectrum, label, color in (
        (result.roughness_1, "Situation 1", _C_PRIMARY),
        (result.roughness_2, "Situation 2", _C_SECONDARY),
    ):
        ax.plot(
            100.0 * np.asarray(spectrum.wavelengths_m),
            spectrum.levels_db,
            color=color,
            lw=1.0,
            marker="o",
            ms=2.5,
            label=_t(label, language),
        )
    _roughness_axis(ax, [float(w) for w in upper.wavelengths_m], language)
    ax.set_title(
        f"{_t('ISO 3095 Annex E', language)}: "
        rf"$\Delta L_{{p\mathrm{{Aeq}},T_p}}$ = {format_number(result.bound_db, language, decimals=2)} dB"
    )
    ax.grid(visible=True, which="major", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def _first_series_label(first_label: str | None, index: int, label: str) -> str:
    """The caller's ``label`` for the first series drawn, the series' own otherwise."""
    return first_label if (first_label is not None and index == 0) else label


def _draw_reference_roughness(
    ax: Axes,
    result: ReferenceTrackCheck,
    kwargs: dict[str, Any],
    first_label: str | None,
    language: str,
) -> None:
    """The measured roughness spectra against the limit of Figure 2."""
    colors = (_C_PRIMARY, _C_TERTIARY, _C_QUATERNARY, _C_MUTED)
    wavelengths: list[float] = [float(w) for w in result.roughness_limit_db]
    numbered = len(result.roughness) > 1
    for i, spectrum in enumerate(result.roughness):
        wavelengths += [float(w) for w in spectrum.wavelengths_m]
        label = _t("Measured", language) + (f" {i + 1}" if numbered else "")
        ax.plot(
            100.0 * np.asarray(spectrum.wavelengths_m),
            spectrum.levels_db,
            **styled(
                kwargs,
                color=colors[i % len(colors)],
                lw=1.6,
                marker="o",
                ms=3.0,
                label=_first_series_label(first_label, i, label),
            ),
        )
    _draw_roughness_limit(ax, result.roughness_limit_db, language)
    _roughness_axis(ax, wavelengths, language)


def _decay_set_labels(result: ReferenceTrackCheck, language: str) -> list[str]:
    """The legend label of each set of decay rates, in order.

    Sets are numbered within their direction, and only when a direction has
    more than one, so one set of each reads "Vertical" and "Lateral".
    """
    sets = {
        d: sum(1 for r in result.decay_rates if r.direction == d)
        for d in ("vertical", "lateral")
    }
    seen = dict.fromkeys(sets, 0)
    labels: list[str] = []
    for rates in result.decay_rates:
        seen[rates.direction] += 1
        label = _t(rates.direction.capitalize(), language)
        if sets[rates.direction] > 1:
            label += f" {seen[rates.direction]}"
        labels.append(label)
    return labels


def _draw_reference_decay(
    ax: Axes,
    result: ReferenceTrackCheck,
    kwargs: dict[str, Any],
    first_label: str | None,
    language: str,
) -> None:
    """The decay rates of every set against the lower limits of Figure 3."""
    frequencies = [
        float(f) for limit in result.decay_limits_db_per_m.values() for f in limit
    ]
    frequencies += [
        float(f) for rates in result.decay_rates for f in rates.frequencies_hz
    ]
    positions = _band_positions(frequencies)
    labels = _decay_set_labels(result, language)
    for i, (rates, label) in enumerate(zip(result.decay_rates, labels, strict=True)):
        _draw_decay(
            ax,
            rates,
            positions,
            language,
            kwargs,
            label=_first_series_label(first_label, i, label),
            color=_C_PRIMARY if rates.direction == "vertical" else _C_TERTIARY,
        )
    for direction, color in (("vertical", _C_REFERENCE), ("lateral", _C_SECONDARY)):
        direction_limit = result.decay_limits_db_per_m.get(direction)
        if direction_limit:
            label = f"{_t('Lower limit', language)}, {_t(direction.capitalize(), language).lower()}"
            _draw_decay_limit(ax, direction_limit, positions, label, color)
    _decay_axis(ax, positions, language)


def _reference_track_title(
    result: ReferenceTrackCheck, panel: str, language: str
) -> str:
    """The verdict, and the Annex C effect it rests on when the roughness is drawn."""
    from .._i18n import format_number

    verdict = _t("passes", language) if result.passes else _t("fails", language)
    title = f"{_t('Reference track, ISO 3095 6.2', language)}: {verdict}"
    if panel == "roughness" and result.small_deviations is not None:
        # The roughness drawn exceeds the limit and the verdict rests on
        # Annex C, which the curves alone do not show.
        impact = format_number(result.small_deviations.impact_db, language, decimals=2)
        title += f" ({_t('Annex C', language)}, $\\Delta L$ = {impact} dB)"
    return title


def plot_reference_track(
    result: ReferenceTrackCheck,
    ax: Axes | None = None,
    *,
    panel: str = "roughness",
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The measured roughness against Figure 2, or the decay rates against Figure 3.

    :param result: The reference track verdict.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param panel: ``"roughness"`` or ``"decay"``.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured spectra.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    first_label = style_pop(kwargs, "label", None)
    if panel == "roughness":
        _draw_reference_roughness(ax, result, kwargs, first_label, language)
    else:
        _draw_reference_decay(ax, result, kwargs, first_label, language)
    ax.set_title(_reference_track_title(result, panel, language))
    ax.grid(visible=True, which="major", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_pass_by_uncertainty(
    result: PassByUncertainty,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Each input's share of the variance of the result, largest first, as Figure G.1.

    :param result: The budget.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the bars.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    ratios = sorted(result.variance_ratios.items(), key=lambda item: -item[1])
    x = np.arange(len(ratios), dtype=np.float64)
    ax.bar(x, [r for _, r in ratios], width=0.6, **styled(kwargs, color=_C_QUATERNARY))
    ax.set_xticks(x)
    ax.set_xticklabels(
        [name for name, _ in ratios], rotation=60, ha="right", fontsize="small"
    )
    ax.set_ylabel(_t("Share of the variance", language))
    ax.set_title(
        f"{_t('ISO 3095 Annex G uncertainty', language)}: "
        rf"$u_\mathrm{{c}}$ = {format_number(result.combined_uncertainty_db, language, decimals=2)} dB, "
        rf"$U$ = {format_number(result.expanded_uncertainty_db, language, decimals=2)} dB"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax
