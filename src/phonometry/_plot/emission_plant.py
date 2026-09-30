#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the ISO 8297 multisource-plant method (lazy imports from
the results' ``.plot()``).

Four figures: the plan of the contour round the plant area in the manner of
Figure 1 of the standard, the octave-band sound power beside the contour
average it was built from, the margin of every requirement the verdict
holds, and the parts of a plant against their sum.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_EDGE,
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _band_axis,
    _import_pyplot,
    _new_axes,
    place_legend_clear,
    style_default,
    theme_fill,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..emission.sound_power_plant import (
        PartialPlantContributions,
        PlantMeasurementCheck,
        PlantMeasurementContour,
        PlantSoundPowerResult,
    )

#: Labels named once so the translation table and the axes cannot drift
#: apart; the plan axes read the same in both languages.
_YLABEL_LEVEL = "Level [dB]"
_XLABEL_PLAN = "x [m]"
_YLABEL_PLAN = "y [m]"
_LABEL_LW = "Sound power level $L_W$"
_LABEL_MEAN = r"Contour average $\overline{L_p}$"
_LABEL_MEAN_STAR = r"Corrected average $\overline{L_p^*}$"

#: Spanish translations of the fixed text of these renderers, keyed by the
#: English text; English is returned verbatim.
_STRINGS: dict[str, str] = {
    _YLABEL_LEVEL: "Nivel [dB]",
    _LABEL_LW: "Nivel de potencia acústica $L_W$",
    _LABEL_MEAN: r"Media en el contorno $\overline{L_p}$",
    _LABEL_MEAN_STAR: r"Media corregida $\overline{L_p^*}$",
    "Plant area $S_\\mathrm{p}$": "Área de la planta $S_\\mathrm{p}$",
    "Measurement contour, $l$ = {length} m": "Contorno de medición, $l$ = {length} m",
    "Measurement position": "Posición de medición",
    "Omitted position": "Posición omitida",
    "Microphone direction": "Dirección del micrófono",
    "Measurement distance $d_i$": "Distancia de medición $d_i$",
    _XLABEL_PLAN: _XLABEL_PLAN,
    _YLABEL_PLAN: _YLABEL_PLAN,
    "ISO 8297 measurement contour, $N$ = {count}, $\\bar{{d}}$ = {mean} m, $h$ = {height} m": (
        "Contorno de medición ISO 8297, $N$ = {count}, $\\bar{{d}}$ = {mean} m, $h$ = {height} m"
    ),
    "ISO 8297 sound power of the plant": "Potencia acústica de la planta ISO 8297",
    "Margin to the limit [% of the limit]": "Margen hasta el límite [% del límite]",
    "Requirement met": "Requisito cumplido",
    "Requirement not met": "Requisito incumplido",
    "Advisory, to be reported": "Recomendación, a indicar en el informe",
    "ISO 8297 requirements: {verdict}": "Requisitos de ISO 8297: {verdict}",
    "met": "cumplidos",
    "not met": "incumplidos",
    # "§" marks the clause number, which the Spanish pass would otherwise
    # write with a decimal comma.
    "Parts of the plant and their sum, ISO 8297 §0.2 b)": (
        "Partes de la planta y su suma, ISO 8297 §0.2 b)"
    ),
    "Sum of the parts": "Suma de las partes",
}

#: What each requirement row is called on the chart, keyed by its ``key``.
_ROW_LABELS: dict[str, tuple[str, str]] = {
    "plant_dimension_min": ("Plant dimension, lower", "Dimensión de la planta, mínima"),
    "plant_dimension_max": ("Plant dimension, upper", "Dimensión de la planta, máxima"),
    "mean_distance_min": ("Mean distance, lower", "Distancia media, mínima"),
    "mean_distance_max": ("Mean distance, upper", "Distancia media, máxima"),
    "aspect_angle": ("Aspect angle", "Ángulo de visión"),
    "position_spacing": ("Position spacing", "Separación de posiciones"),
    "omitted_positions": ("Omitted positions", "Posiciones omitidas"),
    "microphone_height_min": (
        "Microphone height, 5 m floor",
        "Altura del micrófono, mínimo de 5 m",
    ),
    "microphone_height": (
        "Microphone height, prescribed",
        "Altura del micrófono, prescrita",
    ),
    "directional_microphone": ("Microphone 3 dB angle", "Ángulo a −3 dB del micrófono"),
    "background_margin": ("Background margin", "Margen sobre el fondo"),
    "background_margin_preferred": (
        "Background margin, preferred",
        "Margen sobre el fondo, preferente",
    ),
    "octave_bands": ("Octave bands measured", "Bandas de octava medidas"),
    "level_excess": ("Excess over the average", "Exceso sobre la media"),
    "measurement_time": ("Measurement time", "Tiempo de medición"),
    "integrated_reading": (
        "Integrated reading, range",
        "Lectura integrada, recorrido",
    ),
}


def _t(text: str, language: str = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


def _closed(vertices: np.ndarray) -> np.ndarray:
    """The polygon with its first vertex repeated at the end."""
    return np.vstack([vertices, vertices[:1]])


def plot_plant_contour(
    contour: PlantMeasurementContour,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The plan of an ISO 8297 contour: plant area, contour, positions.

    The plant area is filled and hatched, the contour drawn round it with its
    length in the legend, each measured position marked with a short arrow
    for the microphone's reference direction (9.4), a thin line to the
    nearest point of the plant perimeter (its :math:`d_i`), and any omitted
    position left hollow. The title carries :math:`N`, :math:`\bar{d}` and the
    height of 9.3.

    :param contour: A
        :class:`~phonometry.emission.sound_power_plant.PlantMeasurementContour`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the position markers.
    :return: The axes.
    """
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch, Polygon

    from .._i18n import format_number, localize_axes

    if ax is None:
        _fig, ax = _import_pyplot().subplots(figsize=(9.5, 5.6), layout="constrained")
    plant = contour.plant_outline_m
    ring = contour.contour_m
    fill = theme_fill(_C_SECONDARY, ax=ax)
    ax.add_patch(
        Polygon(
            plant,
            closed=True,
            facecolor=fill,
            edgecolor=_C_SECONDARY,
            hatch="xx",
            linewidth=1.6,
            zorder=2,
        )
    )
    closed = _closed(ring)
    ax.plot(closed[:, 0], closed[:, 1], color=_C_PRIMARY, linewidth=1.8, zorder=3)

    positions = contour.positions_m
    directions = contour.microphone_directions
    arrow = 0.35 * contour.position_spacing_m
    for point, direction, nearest in zip(
        positions, directions, contour.nearest_perimeter_points_m, strict=True
    ):
        ax.plot(
            [point[0], nearest[0]],
            [point[1], nearest[1]],
            color=_C_MUTED,
            linewidth=0.9,
            linestyle=":",
            zorder=2,
        )
        ax.annotate(
            "",
            xy=(point[0] + arrow * direction[0], point[1] + arrow * direction[1]),
            xytext=(point[0], point[1]),
            arrowprops={"arrowstyle": "-|>", "color": _C_TERTIARY, "lw": 1.3},
            zorder=4,
        )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "linestyle", "none")
    style_default(kwargs, "markersize", 6.5)
    style_default(kwargs, "markerfacecolor", "white")
    style_default(kwargs, "zorder", 5)
    style_default(kwargs, "label", _t("Measurement position", language))
    (markers,) = ax.plot(positions[:, 0], positions[:, 1], **kwargs)
    handles: list[Any] = [
        Patch(
            facecolor=fill,
            edgecolor=_C_SECONDARY,
            hatch="xx",
            label=_t("Plant area $S_\\mathrm{p}$", language),
        ),
        Line2D(
            [],
            [],
            color=_C_PRIMARY,
            linewidth=1.8,
            label=_t(
                "Measurement contour, $l$ = {length} m",
                language,
                length=format_number(contour.contour_length_m, language, decimals=0),
            ),
        ),
        markers,
        Line2D(
            [],
            [],
            color=_C_TERTIARY,
            marker=r"$\rightarrow$",
            linestyle="none",
            markersize=10,
            label=_t("Microphone direction", language),
        ),
        Line2D(
            [],
            [],
            color=_C_MUTED,
            linestyle=":",
            label=_t("Measurement distance $d_i$", language),
        ),
    ]
    if contour.omitted_positions:
        gone = contour.layout_positions_m[list(contour.omitted_positions)]
        ax.plot(
            gone[:, 0],
            gone[:, 1],
            linestyle="none",
            marker="x",
            color=_C_REFERENCE,
            markersize=7,
            zorder=5,
        )
        handles.append(
            Line2D(
                [],
                [],
                color=_C_REFERENCE,
                marker="x",
                linestyle="none",
                label=_t("Omitted position", language),
            )
        )
    # One metre is one metre in both directions: the plan is drawn to scale,
    # the limits growing to fill the axes rather than the axes shrinking.
    ax.set_aspect("equal", adjustable="datalim")
    ax.margins(0.06)
    ax.set_xlabel(_t(_XLABEL_PLAN, language))
    ax.set_ylabel(_t(_YLABEL_PLAN, language))
    ax.set_title(
        _t(
            "ISO 8297 measurement contour, $N$ = {count}, $\\bar{{d}}$ = {mean} m, $h$ = {height} m",
            language,
            count=positions.shape[0],
            mean=format_number(contour.mean_distance_m, language, decimals=1),
            height=format_number(
                contour.prescribed_microphone_height_m, language, decimals=1
            ),
        )
    )
    # Outside the plan, to its right: inside, any corner can fall on the plant
    # or on a position. On axes the caller passes, the caller lays the figure
    # out; on a figure made here the constrained layout keeps it on the canvas.
    ax.legend(
        handles=handles,
        fontsize="small",
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0.0,
    )
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_plant_sound_power(
    result: PlantSoundPowerResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The octave-band :math:`L_W` of a plant beside the contour average.

    One bar per band of :math:`L_W`, the energy average round the contour
    :math:`\overline{L_p}` as a line of markers, and, where 10.2 replaced a
    level, the corrected average :math:`\overline{L_p^*}` as a second one.
    The distance between the bars and the average is the sum of the four
    terms of 10.4 to 10.7. The A-weighted level is in the title.

    :param result: A
        :class:`~phonometry.emission.sound_power_plant.PlantSoundPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the band bars.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = _band_axis(ax, result.frequencies_hz, language=language)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "label", _t(_LABEL_LW, language))
    style_default(kwargs, "width", 0.6)
    style_default(kwargs, "zorder", 2)
    ax.bar(positions, result.sound_power_level_db, **kwargs)
    ax.plot(
        positions,
        result.mean_level_db,
        color=_C_SECONDARY,
        marker="o",
        linewidth=1.6,
        zorder=3,
        label=_t(_LABEL_MEAN, language),
    )
    if result.steps_2_3_applied:
        ax.plot(
            positions,
            result.corrected_mean_level_db,
            color=_C_TERTIARY,
            marker="s",
            linestyle="--",
            linewidth=1.4,
            zorder=3,
            label=_t(_LABEL_MEAN_STAR, language),
        )
    low = float(np.min(result.mean_level_db))
    high = float(np.max(result.sound_power_level_db))
    ax.set_ylim(low - 10.0, high + 12.0)
    ax.set_ylabel(_t(_YLABEL_LEVEL, language))
    total = format_number(result.a_weighted_sound_power_level_db, language, decimals=1)
    ax.set_title(
        f"{_t('ISO 8297 sound power of the plant', language)}"
        f" ($L_{{W\\mathrm{{A}}}}$ = {total} dB)"
    )
    legend = ax.legend(fontsize="small")
    place_legend_clear(legend)
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_plant_measurement_check(
    check: PlantMeasurementCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The margin of every requirement an ISO 8297 check holds.

    One horizontal bar per requirement, its length the distance of the
    measured value inside its limit as a percentage of the limit: to the
    right of zero the requirement holds, to the left it does not. Advisory
    requirements, which the report states rather than fails on, are hatched
    and end in a hollow mark, so a row met exactly, whose bar has no length,
    still shows which kind it is.

    :param check: A
        :class:`~phonometry.emission.sound_power_plant.PlantMeasurementCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the bars.
    :return: The axes.
    """
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    from .._i18n import localize_axes

    rows = check.requirements
    if ax is None:
        # Tall enough for one readable bar per requirement, and constrained so
        # the long row labels stay on the canvas.
        _fig, ax = _import_pyplot().subplots(
            figsize=(9.0, 1.8 + 0.42 * len(rows)), layout="constrained"
        )
    index = 0 if language == "en" else 1
    labels = [
        f"§{r.clause}  {_ROW_LABELS.get(r.key, (r.description, r.description))[index]}"
        for r in rows
    ]
    margins = np.array([100.0 * r.margin for r in rows], dtype=np.float64)
    shown = np.clip(margins, -100.0, 100.0)
    colors = [_C_TERTIARY if r.holds else _C_REFERENCE for r in rows]
    y = np.arange(len(rows), dtype=np.float64)[::-1]
    style_default(kwargs, "edgecolor", _C_EDGE)
    style_default(kwargs, "color", colors)
    style_default(kwargs, "height", 0.6)
    style_default(kwargs, "zorder", 2)
    bars = ax.barh(y, shown, **kwargs)
    advisory = np.array([row.advisory for row in rows], dtype=bool)
    for bar, row in zip(bars, rows, strict=True):
        if row.advisory:
            bar.set_hatch("//")
    # A requirement met exactly has a bar of no length; the mark at its end
    # keeps it on the chart, filled for a requirement and hollow for an
    # advisory one, since a bar of no length shows no hatch.
    firm = ~advisory
    if np.any(firm):
        ax.scatter(
            shown[firm],
            y[firm],
            c=[c for c, keep in zip(colors, firm, strict=True) if keep],
            edgecolors=_C_EDGE,
            s=22,
            zorder=4,
        )
    if np.any(advisory):
        ax.scatter(
            shown[advisory],
            y[advisory],
            facecolors="none",
            edgecolors=[c for c, keep in zip(colors, advisory, strict=True) if keep],
            linewidths=1.8,
            s=42,
            zorder=4,
        )
    ax.axvline(0.0, color=_C_EDGE, linewidth=1.2, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize="small")
    ax.set_xlim(-105.0, 105.0)
    ax.set_xlabel(_t("Margin to the limit [% of the limit]", language))
    verdict = _t("met", language) if check.passes else _t("not met", language)
    ax.set_title(_t("ISO 8297 requirements: {verdict}", language, verdict=verdict))
    # A label of the caller's names the bars themselves, ahead of the key.
    handles: list[Any] = [bars] if "label" in kwargs else []
    handles += [
        Patch(
            facecolor=_C_TERTIARY,
            edgecolor=_C_EDGE,
            label=_t("Requirement met", language),
        ),
        Patch(
            facecolor=_C_REFERENCE,
            edgecolor=_C_EDGE,
            label=_t("Requirement not met", language),
        ),
        (
            Patch(facecolor="white", edgecolor=_C_EDGE, hatch="//"),
            Line2D(
                [],
                [],
                linestyle="none",
                marker="o",
                markerfacecolor="none",
                markeredgecolor=_C_EDGE,
                markeredgewidth=1.4,
            ),
        ),
    ]
    labels = [h.get_label() for h in handles[:-1]]
    labels.append(_t("Advisory, to be reported", language))
    legend = ax.legend(handles, labels, fontsize="small")
    place_legend_clear(legend)
    ax.grid(visible=True, axis="x", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_partial_plant_contributions(
    result: PartialPlantContributions,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The octave-band :math:`L_W` of each part of a plant and of their sum.

    :param result: A
        :class:`~phonometry.emission.sound_power_plant.PartialPlantContributions`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the bars of the sum.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = _band_axis(ax, result.frequencies_hz, language=language)
    total_a = format_number(result.a_weighted_total_db, language, decimals=1)
    style_default(kwargs, "color", theme_fill(_C_PRIMARY, ax=ax))
    style_default(kwargs, "edgecolor", _C_PRIMARY)
    style_default(
        kwargs,
        "label",
        f"{_t('Sum of the parts', language)} ($L_{{W\\mathrm{{A}}}}$ = {total_a} dB)",
    )
    style_default(kwargs, "width", 0.7)
    style_default(kwargs, "zorder", 2)
    ax.bar(positions, result.total_level_db, **kwargs)
    cycle = (_C_SECONDARY, _C_TERTIARY, _C_REFERENCE, _C_MUTED)
    markers = ("o", "s", "^", "D")
    for i, (name, levels, total) in enumerate(
        zip(
            result.names,
            result.part_levels_db,
            result.a_weighted_part_levels_db,
            strict=True,
        )
    ):
        ax.plot(
            positions,
            levels,
            color=cycle[i % len(cycle)],
            marker=markers[i % len(markers)],
            linewidth=1.5,
            zorder=3,
            label=(
                f"{name} ($L_{{W\\mathrm{{A}}}}$ = "
                f"{format_number(float(total), language, decimals=1)} dB)"
            ),
        )
    low = float(np.min(result.part_levels_db))
    high = float(np.max(result.total_level_db))
    ax.set_ylim(low - 10.0, high + 12.0)
    ax.set_ylabel(_t(_YLABEL_LEVEL, language))
    ax.set_title(_t("Parts of the plant and their sum, ISO 8297 §0.2 b)", language))
    legend = ax.legend(fontsize="small")
    place_legend_clear(legend)
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax
