#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for wind turbine sound at a receptor (IEC TS 61400-11-2:2024).

Lazy imports from the results' ``.plot()`` methods in
:mod:`~phonometry.environment.assessment.wind_turbine_receptor` and
:mod:`~phonometry.environment.assessment.wind_turbine_modulation`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _band_axis,
    _new_axes,
    format_frequency_axis,
    place_legend_clear,
    styled,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.lines import Line2D
    from numpy.typing import ArrayLike

    from ..environment.assessment.wind_turbine_modulation import (
        BinnedModulation,
        ModulationBlock,
        ModulationPeriod,
    )
    from ..environment.assessment.wind_turbine_receptor import (
        BinnedSoundLevels,
        LowFrequencyLevel,
        PredictedReceptorLevel,
        SoundEmergence,
        SoundRelevantTurbines,
        ToneSearchLimit,
        TurbineSoundLevels,
        WindShearProfile,
        WindTurbineRatingLevel,
    )

#: Axis labels, the block title and the legend entry the renderers repeat,
#: written once so the table and the axes cannot drift apart.
_WIND_SPEED_LABEL = "Wind speed [m/s]"
_LEVEL_LABEL = "Level [dB]"
_DEPTH_LABEL = "Modulation depth [dB]"
_FREQ_LABEL = "Frequency [Hz]"
_TIME_LABEL = "Time [s]"
_PREDICTED_LEVEL_LABEL = "Predicted level [dB]"
_SPEED_CLASS_LABEL = "Wind speed class"
_BLOCK_TITLE = "IEC TS 61400-11-2 10 s block"
_DETRENDED_LABEL = "Detrended series"

#: Spanish translations of the fixed strings, keyed by their English text.
_STRINGS: dict[str, str] = {
    _WIND_SPEED_LABEL: "Velocidad del viento [m/s]",
    _LEVEL_LABEL: "Nivel [dB]",
    _DEPTH_LABEL: "Profundidad de modulación [dB]",
    _FREQ_LABEL: "Frecuencia [Hz]",
    "Modulation frequency [Hz]": "Frecuencia de modulación [Hz]",
    "Power spectrum $S_{xx}$": "Espectro de potencia $S_{xx}$",
    "Lines in the inverse transform": "Líneas de la transformada inversa",
    "Other lines": "Otras líneas",
    "Range of the fundamental": "Rango de la fundamental",
    "Estimated harmonics": "Armónicos estimados",
    "Prominence": "Prominencia",
    "Prominence-failed block": "Bloque sin prominencia",
    _BLOCK_TITLE: "Bloque de 10 s IEC TS 61400-11-2",
    _TIME_LABEL: "Tiempo [s]",
    _DETRENDED_LABEL: "Serie sin tendencia",
    "Reconstructed series": "Serie reconstruida",
    "10 s modulation depth": "Profundidad de modulación de 10 s",
    "Invalid 10 s block": "Bloque de 10 s no válido",
    "10 min AM rating": "Valoración AM de 10 min",
    "Not rated (fewer than 30 valid blocks)": "Sin valorar (menos de 30 bloques válidos)",
    "Mean AM rating of the worst band [dB]": "Valoración AM media de la peor banda [dB]",
    "All directions": "Todas las direcciones",
    "Sector": "Sector",
    "Height [m]": "Altura [m]",
    "Power law": "Ley potencial",
    "Logarithmic profile": "Perfil logarítmico",
    "Measured": "Medida",
    "Wind shear exponent": "Exponente de cizalladura",
    "Interval levels": "Niveles por periodo",
    "Bin average": "Promedio del intervalo",
    "Total": "Total",
    "Background": "Fondo",
    "Turbine": "Aerogenerador",
    "Background within 3 dB": "Fondo a menos de 3 dB",
    "Turbine level at the receptor": "Nivel del aerogenerador en el receptor",
    _PREDICTED_LEVEL_LABEL: "Nivel previsto [dB]",
    "Receptor total": "Total en el receptor",
    "Sound relevant": "Relevante para el sonido",
    "Not relevant": "No relevante",
    "Total less 1 dB": "Total menos 1 dB",
    "Outdoor": "Exterior",
    "Indoor": "Interior",
    "Low frequency sound": "Sonido de baja frecuencia",
    "Emergence $E$ [dB]": "Emergencia $E$ [dB]",
    _SPEED_CLASS_LABEL: "Clase de velocidad del viento",
    "Adjustment [dB]": "Ajuste [dB]",
    "Applied (the most severe, A.1)": "Aplicado (el más severo, A.1)",
    "Energy sum of the loudest": "Suma energética de los más ruidosos",
    "Band": "Banda",
    "to": "a",
    "Tonal": "Tonal",
    "Amplitude modulation": "Modulación de amplitud",
    "Impulsive": "Impulsivo",
    "Rating level": "Nivel de evaluación",
    "Attenuation over the distance [dB]": "Atenuación en la distancia [dB]",
    "Band attenuation": "Atenuación por banda",
    "Upper search frequency": "Frecuencia superior de búsqueda",
}


def _t(text: str, language: str = "en") -> str:
    """Localise a fixed string; English is returned verbatim."""
    return _STRINGS.get(text, text) if language == "es" else text


def _num(value: float, language: str, decimals: int = 1, *, trim: bool = False) -> str:
    from .._i18n import format_number

    return format_number(value, language, decimals=decimals, trim=trim)


#: One colour per direction sector, enough for the twelve 30° sectors that
#: 10.1 calls usual and 13.7 tabulates: the tab10 hues less its grey and its
#: red, which the grey level keys and the red ring of a bin within 3 dB of its
#: background wear, and four hues of tab20b and Dark2. Every pair is at least
#: 15 apart in CIEDE2000 and every hue at least 16 from that grey and that
#: red, and each clears 2:1 on the light page and on the dark one. In this
#: order neighbouring sectors, 330° and 0° included, are at least 26 apart,
#: and 21 under simulated protanopia and deuteranopia, and the first four,
#: all that four sectors or fewer take, clear 3:1 on both pages. Narrower
#: sectors past the twelfth take the colours again.
_SECTOR_COLOURS: tuple[str, ...] = (
    "#1f77b4",
    "#a6761d",
    "#9467bd",
    "#2ca02c",
    "#5254a3",
    "#637939",
    "#bcbd22",
    "#8c564b",
    "#e377c2",
    "#7b4173",
    "#ff7f0e",
    "#17becf",
)


def _direction_groups(
    directions: ArrayLike | None, count: int, language: str
) -> list[tuple[str, np.ndarray, str | None]]:
    """Name, member mask and colour of each direction sector, in increasing order.

    One group of every point, "All directions", when binned by wind speed
    alone; it takes the axes' next colour, so its colour is ``None``.
    """
    if directions is None:
        return [(_t("All directions", language), np.ones(count, dtype=bool), None)]
    sectors = np.asarray(directions)
    return [
        (
            f"{_t('Sector', language)} {_num(value, language, 3, trim=True)}°",
            np.isclose(sectors, value),
            _SECTOR_COLOURS[index % len(_SECTOR_COLOURS)],
        )
        for index, value in enumerate(sorted(set(sectors.tolist())))
    ]


def _colour_default(colour: str | None) -> dict[str, str]:
    """The ``color`` default of a group's line, none when the axes pick it."""
    return {} if colour is None else {"color": colour}


def plot_modulation_block(
    result: ModulationBlock,
    ax: Axes | None = None,
    *,
    kind: str = "spectrum",
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The block's power spectrum (Figure 1 of the TS) or its two series.

    :param result: A :class:`~phonometry.environment.assessment.wind_turbine_modulation.ModulationBlock`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kind: ``"spectrum"`` or ``"series"``.
    :param language: ``"en"`` or ``"es"``.
    :param kwargs: Forwarded to the primary artist.
    :return: The axes.
    """
    from .._i18n import localize_axes

    if kind not in ("spectrum", "series"):
        msg = f"'kind' must be 'spectrum' or 'series'; got {kind!r}."
        raise ValueError(msg)
    ax = ax if ax is not None else _new_axes()
    if kind == "series":
        _draw_block_series(result, ax, language, kwargs)
    else:
        _draw_block_spectrum(result, ax, language, kwargs)
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def _draw_block_spectrum(
    result: ModulationBlock, ax: Axes, language: str, kwargs: dict[str, Any]
) -> None:
    freqs = np.asarray(result.frequencies_hz)
    spectrum = np.asarray(result.power_spectrum)
    included = set(
        np.round(np.asarray(result.included_frequencies_hz) * 10).astype(int)
    )
    mask = np.array([round(f * 10) in included for f in freqs])
    width = 0.07
    if mask.any():
        ax.bar(
            freqs[~mask],
            spectrum[~mask],
            width=width,
            color="none",
            edgecolor=_C_MUTED,
            label=_t("Other lines", language),
        )
        ax.bar(
            freqs[mask],
            spectrum[mask],
            width=width,
            **styled(
                kwargs,
                color=_C_PRIMARY,
                label=_t("Lines in the inverse transform", language),
            ),
        )
    else:
        ax.bar(
            freqs,
            spectrum,
            width=width,
            **styled(
                kwargs, color=_C_MUTED, label=_t("Prominence-failed block", language)
            ),
        )
    low, high = result.modulation_frequency_range_hz
    ax.axvline(
        low,
        color=_C_MUTED,
        ls=":",
        lw=1.0,
        label=_t("Range of the fundamental", language),
    )
    ax.axvline(high, color=_C_MUTED, ls=":", lw=1.0)
    title = _t(_BLOCK_TITLE, language)
    if result.fundamental_frequency_hz is not None:
        f0 = result.fundamental_frequency_hz
        # A prominence-failed block is not analysed further (13.6.2.3 e)), so
        # its harmonics are never estimated and none is drawn.
        estimates = (
            [n * f0 for n in (2, 3) if n * f0 <= float(freqs[-1])]
            if result.valid
            else []
        )
        for i, f in enumerate(estimates):
            ax.axvline(
                f,
                color=_C_TERTIARY,
                ls="--",
                lw=1.0,
                label=_t("Estimated harmonics", language) if i == 0 else None,
            )
        prominence = result.prominence
        if prominence is not None and np.isfinite(prominence):
            title += (
                f": $f_0$ = {_num(f0, language)} Hz, "
                f"{_t('Prominence', language).lower()} {_num(prominence, language, 2)}"
            )
    ax.set_xlim(0.0, float(freqs[-1]) + 0.1)
    ax.set_xlabel(_t("Modulation frequency [Hz]", language))
    ax.set_ylabel(_t("Power spectrum $S_{xx}$", language))
    ax.set_title(title)


def _draw_block_series(
    result: ModulationBlock, ax: Axes, language: str, kwargs: dict[str, Any]
) -> None:
    time_s = np.arange(np.asarray(result.detrended_db).size) * 0.1
    reconstructed = np.asarray(result.reconstructed_db)
    if reconstructed.size:
        ax.plot(
            time_s,
            result.detrended_db,
            color=_C_MUTED,
            lw=1.0,
            label=_t(_DETRENDED_LABEL, language),
        )
        ax.plot(
            time_s,
            reconstructed,
            **styled(
                kwargs,
                color=_C_PRIMARY,
                lw=1.5,
                label=_t("Reconstructed series", language),
            ),
        )
        upper = float(np.percentile(reconstructed, 95.0))
        lower = float(np.percentile(reconstructed, 5.0))
        ax.axhline(upper, color=_C_REFERENCE, ls="--", lw=1.0, label="$L_5$, $L_{95}$")
        ax.axhline(lower, color=_C_REFERENCE, ls="--", lw=1.0)
    else:
        ax.plot(
            time_s,
            result.detrended_db,
            **styled(
                kwargs, color=_C_MUTED, lw=1.0, label=_t(_DETRENDED_LABEL, language)
            ),
        )
    title = _t(_BLOCK_TITLE, language)
    if result.modulation_depth_db is not None:
        title += (
            f": $L_5 - L_{{95}}$ = {_num(result.modulation_depth_db, language, 2)} dB"
        )
    ax.set_xlabel(_t(_TIME_LABEL, language))
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.set_title(title)


def plot_modulation_period(
    result: ModulationPeriod,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The 10 s depths through the period and the 10 min rating."""
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    depths = np.asarray(result.modulation_depths_db)
    start_s = np.arange(depths.size) * 10.0 + 5.0
    valid = np.isfinite(depths)
    ax.plot(
        start_s[valid],
        depths[valid],
        **styled(
            kwargs,
            color=_C_PRIMARY,
            ls="none",
            marker="o",
            ms=4,
            label=_t("10 s modulation depth", language),
        ),
    )
    if (~valid).any():
        ax.plot(
            start_s[~valid],
            np.zeros(int((~valid).sum())),
            color=_C_MUTED,
            ls="none",
            marker="x",
            ms=4,
            zorder=3,
            label=_t("Invalid 10 s block", language),
        )
    if result.rated:
        ax.axhline(
            result.rating_db,
            color=_C_REFERENCE,
            lw=1.5,
            label=f"{_t('10 min AM rating', language)} = {_num(result.rating_db, language, 2)} dB",
        )
    else:
        ax.axhline(
            0.0,
            color=_C_REFERENCE,
            lw=1.5,
            label=_t("Not rated (fewer than 30 valid blocks)", language),
        )
    ax.set_xlim(0.0, 600.0)
    # Headroom above the highest depth, so the legend has a clear strip.
    top = max(float(depths[valid].max()) if valid.any() else 0.0, result.rating_db, 1.0)
    ax.set_ylim(-0.05 * top, 1.45 * top)
    ax.set_xlabel(_t(_TIME_LABEL, language))
    ax.set_ylabel(_t(_DEPTH_LABEL, language))
    ax.set_title(f"n = {result.valid_blocks}/60")
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_binned_modulation(
    result: BinnedModulation,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The worst band's mean rating per bin against wind speed.

    Each point is drawn as the number of the band its bin selected, on a chip
    that masks the line under it, and the legend names the frequency range of
    each band drawn.
    """
    from matplotlib.lines import Line2D

    from .._i18n import localize_axes
    from ..environment.assessment.wind_turbine_modulation import (
        AM_FREQUENCY_BANDS_HZ,
    )
    from .geometry._draft import _chip

    ax = ax if ax is not None else _new_axes()
    speeds = np.asarray(result.wind_speeds_m_s)
    ratings = np.asarray(result.selected_ratings_db)
    bands = np.asarray(result.selected_bands)
    groups = _direction_groups(result.wind_directions_deg, speeds.size, language)
    for name, members, colour in groups:
        order = np.argsort(speeds[members])
        x = speeds[members][order]
        y = ratings[members][order]
        (line,) = ax.plot(
            x, y, **styled(kwargs, lw=1.5, label=name, **_colour_default(colour))
        )
        for xi, yi, band in zip(x, y, bands[members][order], strict=True):
            ax.annotate(
                str(int(band)),
                (xi, yi),
                ha="center",
                va="center",
                fontsize="medium",
                color=line.get_color(),
                bbox=_chip(ax, 0.25),
                zorder=4,
            )
    # Room at the ends for the chips drawn on the first and last points.
    ax.margins(x=0.06, y=0.1)
    handles, labels = ax.get_legend_handles_labels()
    for band in sorted({int(b) for b in bands}):
        centres = AM_FREQUENCY_BANDS_HZ[band]
        handles.append(
            Line2D([], [], ls="none", marker=f"${band}$", ms=7, color=_C_MUTED)
        )
        labels.append(
            f"{_t('Band', language)} {band}: {_num(centres[0], language, 0)} Hz "
            f"{_t('to', language)} {_num(centres[-1], language, 0)} Hz"
        )
    ax.set_xlabel(_t(_WIND_SPEED_LABEL, language))
    ax.set_ylabel(_t("Mean AM rating of the worst band [dB]", language))
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(handles, labels, fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_wind_shear_profile(
    result: WindShearProfile,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The power-law profile through the two measured points."""
    from .._i18n import localize_axes
    from ..environment.assessment.wind_turbine_receptor import (
        REFERENCE_ROUGHNESS_LENGTH_M,
        logarithmic_wind_speed,
    )

    ax = ax if ax is not None else _new_axes()
    low, high = result.heights_m
    top = 1.25 * high
    heights = np.linspace(1.0, top, 200)
    ax.plot(
        np.asarray(result.speed_at(heights)),
        heights,
        **styled(kwargs, color=_C_PRIMARY, lw=1.5, label=_t("Power law", language)),
    )
    log_speeds = np.array(
        [
            float(
                logarithmic_wind_speed(
                    result.speeds_m_s[0], height_m=float(h), reference_height_m=low
                )
            )
            for h in heights
        ]
    )
    ax.plot(
        log_speeds,
        heights,
        color=_C_MUTED,
        ls="--",
        lw=1.2,
        label=(
            f"{_t('Logarithmic profile', language)}, $z_0$ = "
            f"{_num(REFERENCE_ROUGHNESS_LENGTH_M, language, 2)} m"
        ),
    )
    ax.plot(
        result.speeds_m_s,
        result.heights_m,
        color=_C_REFERENCE,
        ls="none",
        marker="o",
        label=_t("Measured", language),
    )
    ax.set_ylim(0.0, top)
    ax.set_xlim(left=0.0)
    ax.set_xlabel(_t(_WIND_SPEED_LABEL, language))
    ax.set_ylabel(_t("Height [m]", language))
    ax.set_title(
        f"{_t('Wind shear exponent', language)} $\\alpha$ = {_num(result.shear_exponent, language, 2)}"
    )
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_binned_sound_levels(
    result: BinnedSoundLevels,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The interval levels against wind speed with the bin averages over them."""
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    ax.plot(
        result.interval_wind_speeds_m_s,
        result.interval_levels_db,
        color=_C_MUTED,
        ls="none",
        marker=".",
        ms=3,
        alpha=0.6,
        label=_t("Interval levels", language),
    )
    errors = np.nan_to_num(np.asarray(result.combined_uncertainty_db), nan=0.0)
    ax.errorbar(
        result.wind_speeds_m_s,
        result.mean_levels_db,
        yerr=errors,
        capsize=3,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            lw=1.5,
            ls="none",
            marker="s",
            ms=5,
            label=_t("Bin average", language),
        ),
    )
    ax.set_xlabel(_t(_WIND_SPEED_LABEL, language))
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_turbine_sound_levels(
    result: TurbineSoundLevels,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Total, background and turbine level per bin."""
    from .._i18n import localize_axes
    from ..environment.assessment.wind_turbine_receptor import (
        BackgroundCorrectionRegime,
    )

    ax = ax if ax is not None else _new_axes()
    x = (
        np.arange(np.asarray(result.total_levels_db).size, dtype=np.float64) + 1.0
        if result.wind_speeds_m_s is None
        else np.asarray(result.wind_speeds_m_s)
    )
    if result.wind_directions_deg is None:
        _draw_turbine_levels(ax, result, x, language, kwargs)
        keys: list[Line2D] = []
    else:
        keys = _draw_turbine_levels_by_sector(ax, result, x, language, kwargs)
    handles, labels = ax.get_legend_handles_labels()
    handles += keys
    labels += [str(key.get_label()) for key in keys]
    near = np.array(
        [regime is BackgroundCorrectionRegime.THREE_DB for regime in result.regimes]
    )
    if near.any():
        (ring,) = ax.plot(
            x[near],
            np.asarray(result.turbine_levels_db)[near],
            color=_C_REFERENCE,
            ls="none",
            marker="o",
            mfc="none",
            ms=10,
            label=_t("Background within 3 dB", language),
        )
        handles.append(ring)
        labels.append(str(ring.get_label()))
    ax.set_xlabel(
        _t(_SPEED_CLASS_LABEL, language)
        if result.wind_speeds_m_s is None
        else _t(_WIND_SPEED_LABEL, language)
    )
    ax.set_ylabel(_t(_LEVEL_LABEL, language))
    ax.set_title(_t("Turbine level at the receptor", language))
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(handles, labels, fontsize="small"))
    localize_axes(ax, language)
    return ax


def _draw_turbine_levels(
    ax: Axes,
    result: TurbineSoundLevels,
    x: np.ndarray,
    language: str,
    kwargs: dict[str, Any],
) -> None:
    """Total, background and turbine level as three lines over every bin."""
    ax.plot(
        x,
        result.total_levels_db,
        color=_C_SECONDARY,
        marker="^",
        lw=1.0,
        label=_t("Total", language),
    )
    ax.plot(
        x,
        result.background_levels_db,
        color=_C_MUTED,
        marker="v",
        lw=1.0,
        label=_t("Background", language),
    )
    ax.plot(
        x,
        result.turbine_levels_db,
        **styled(
            kwargs, color=_C_PRIMARY, marker="o", lw=1.8, label=_t("Turbine", language)
        ),
    )


def _draw_turbine_levels_by_sector(
    ax: Axes,
    result: TurbineSoundLevels,
    x: np.ndarray,
    language: str,
    kwargs: dict[str, Any],
) -> list[Line2D]:
    """The three levels of each direction sector apart, in the sector's colour.

    A line joins only the bins of one sector, in wind speed order, so that two
    sectors of the same wind speed classes are never joined into one zigzag.
    The sector lines carry the sector names; the keys returned, drawn nowhere,
    name each level by its line style and marker for the legend.
    """
    from matplotlib.lines import Line2D

    total = np.asarray(result.total_levels_db)
    background = np.asarray(result.background_levels_db)
    turbine = np.asarray(result.turbine_levels_db)
    for name, members, sector_colour in _direction_groups(
        result.wind_directions_deg, x.size, language
    ):
        order = np.argsort(x[members], kind="stable")
        xs = x[members][order]
        (line,) = ax.plot(
            xs,
            turbine[members][order],
            **styled(
                kwargs, marker="o", lw=1.8, label=name, **_colour_default(sector_colour)
            ),
        )
        colour = line.get_color()
        ax.plot(xs, total[members][order], color=colour, marker="^", ls="--", lw=1.0)
        ax.plot(
            xs, background[members][order], color=colour, marker="v", ls=":", lw=1.0
        )
    return [
        Line2D(
            [],
            [],
            color=_C_MUTED,
            marker=marker,
            ls=style,
            lw=width,
            label=_t(label, language),
        )
        for label, marker, style, width in (
            ("Total", "^", "--", 1.0),
            ("Background", "v", ":", 1.0),
            ("Turbine", "o", "-", 1.8),
        )
    ]


def plot_predicted_receptor_level(
    result: PredictedReceptorLevel,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Each turbine's predicted level and the total with its uncertainty."""
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    levels = np.asarray(result.turbine_levels_db)
    positions = np.arange(levels.size, dtype=np.float64) + 1.0
    ax.bar(
        positions,
        levels,
        **styled(kwargs, color=_C_PRIMARY, label=_t("Turbine", language)),
    )
    total = result.level_db
    u = result.combined_uncertainty_db
    ax.axhline(
        total,
        color=_C_REFERENCE,
        lw=1.5,
        label=f"{_t('Receptor total', language)} = {_num(total, language)} ± {_num(u, language)} dB",
    )
    ax.axhspan(total - u, total + u, color=_C_REFERENCE, alpha=0.12)
    ax.set_xticks(positions)
    ax.set_xlabel(_t("Turbine", language))
    ax.set_ylabel(_t(_PREDICTED_LEVEL_LABEL, language))
    # Room above the bars and the total for the legend's four lines.
    ax.set_ylim(min(float(levels.min()), total - u) - 10.0, total + u + 12.0)
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_sound_relevant_turbines(
    result: SoundRelevantTurbines,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The turbines' levels, loudest first, the sound relevant ones marked.

    The turbines are numbered from 1 on the axis (input position + 1), so the
    0-based :attr:`SoundRelevantTurbines.indices` read one less. The line over
    the bars is the energy sum of the loudest turbines taken together, one
    more at each step: the relevant ones are those up to where it first
    reaches the total less 1 dB (9.3.2.3).
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    levels = np.asarray(result.predicted_levels_db)
    order = np.argsort(-levels, kind="stable")
    positions = np.arange(levels.size, dtype=np.float64) + 1.0
    relevant = np.asarray(result.relevant)[order]
    ax.bar(
        positions[relevant],
        levels[order][relevant],
        **styled(kwargs, color=_C_PRIMARY, label=_t("Sound relevant", language)),
    )
    if (~relevant).any():
        ax.bar(
            positions[~relevant],
            levels[order][~relevant],
            color=_C_MUTED,
            label=_t("Not relevant", language),
        )
    ax.axhline(
        result.total_level_db,
        color=_C_REFERENCE,
        lw=1.2,
        label=f"{_t('Total', language)} = {_num(result.total_level_db, language)} dB",
    )
    ax.axhline(
        result.total_level_db - 1.0,
        color=_C_REFERENCE,
        ls="--",
        lw=1.0,
        label=_t("Total less 1 dB", language),
    )
    running = 10.0 * np.log10(np.cumsum(10.0 ** (levels[order] / 10.0)))
    ax.plot(
        positions,
        running,
        color=_C_TERTIARY,
        marker="D",
        ms=5,
        lw=1.4,
        zorder=4,
        label=_t("Energy sum of the loudest", language),
    )
    ax.set_xticks(positions)
    ax.set_xticklabels([str(int(i) + 1) for i in order])
    ax.set_xlabel(_t("Turbine", language))
    ax.set_ylabel(_t(_PREDICTED_LEVEL_LABEL, language))
    # Room above the bars and the two lines for the legend.
    ax.set_ylim(float(levels.min()) - 10.0, result.total_level_db + 12.0)
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_low_frequency_level(
    result: LowFrequencyLevel,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The outdoor and indoor band levels of Equation (C.1)."""
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = _band_axis(ax, np.asarray(result.frequencies_hz), language=language)
    ax.plot(
        positions,
        result.outdoor_levels_db,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            marker="o",
            lw=1.5,
            label=f"{_t('Outdoor', language)}: {_num(result.outdoor_level_db, language)} dB",
        ),
    )
    if result.indoor_levels_db is not None and result.indoor_level_db is not None:
        ax.plot(
            positions,
            result.indoor_levels_db,
            color=_C_SECONDARY,
            marker="s",
            lw=1.5,
            label=f"{_t('Indoor', language)}: {_num(result.indoor_level_db, language)} dB",
        )
    weighted = "A" if result.a_weighted else "Z"
    ax.set_ylabel(f"$L_{{p{weighted},\\mathrm{{LF}}}}$ [dB]")
    ax.set_title(_t("Low frequency sound", language))
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_sound_emergence(
    result: SoundEmergence,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The emergence of each wind speed class."""
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    emergence = np.asarray(result.emergence_db)
    if result.wind_speeds_m_s is None:
        x = np.arange(emergence.size, dtype=np.float64) + 1.0
        xlabel = _t(_SPEED_CLASS_LABEL, language)
    else:
        x = np.asarray(result.wind_speeds_m_s)
        xlabel = _t(_WIND_SPEED_LABEL, language)
    ax.bar(
        x,
        emergence,
        width=0.6,
        **styled(kwargs, color=_C_PRIMARY, label="$E(j)$"),
    )
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(_t("Emergence $E$ [dB]", language))
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_wind_turbine_rating_level(
    result: WindTurbineRatingLevel,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The three candidate adjustments, the governing one outlined."""
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    names = ("tonal", "amplitude_modulation", "impulsive")
    labels = [
        _t(text, language) for text in ("Tonal", "Amplitude modulation", "Impulsive")
    ]
    values = [result.adjustments_db[name] for name in names]
    positions = np.arange(3, dtype=np.float64)
    bars = ax.bar(positions, values, width=0.6, **styled(kwargs, color=_C_PRIMARY))
    if result.governing is not None:
        governing = bars[names.index(result.governing)]
        governing.set_edgecolor(_C_REFERENCE)
        governing.set_hatch("//")
        governing.set_label(_t("Applied (the most severe, A.1)", language))
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel(_t("Adjustment [dB]", language))
    ax.set_ylim(0.0, max(max(values), 1.0) * 1.35)
    ax.set_title(
        f"$L_\\mathrm{{r}}$ = {_num(result.equivalent_level_db, language)} + "
        f"{_num(max(values), language)} = {_num(result.rating_level_db, language)} dB"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    if result.governing is not None:
        place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_tone_search_limit(
    result: ToneSearchLimit,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The ISO 9613-1 band attenuation over the distance, the 20 dB line."""
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    ax.plot(
        result.frequencies_hz,
        result.attenuation_db,
        **styled(
            kwargs,
            color=_C_PRIMARY,
            marker="o",
            ms=3,
            lw=1.5,
            label=_t("Band attenuation", language),
        ),
    )
    ax.axhline(20.0, color=_C_REFERENCE, ls="--", lw=1.0, label="20 dB")
    ax.axvline(
        result.upper_frequency_hz,
        color=_C_TERTIARY,
        lw=1.2,
        label=f"{_t('Upper search frequency', language)}: {_num(result.upper_frequency_hz / 1000.0, language, 2)} kHz",
    )
    ax.set_yscale("log")
    format_frequency_axis(ax, language=language)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Attenuation over the distance [dB]", language))
    ax.set_title(
        f"{_num(result.distance_m, language, 0)} m, {_num(result.temperature_c, language, 0)} °C, "
        f"{_num(result.relative_humidity_percent, language, 0)} %"
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax
