#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the free-field qualification and the reference sound
source (ISO 26101, ISO 3745 Annex A, ISO 6926); lazy imports from ``.plot()``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _band_axis,
    _new_axes,
    place_legend_clear,
    style_default,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..emission.free_field_qualification import (
        FreeFieldCheck,
        InverseSquareLawResult,
        SourceDirectionalityResult,
    )
    from ..emission.reference_sound_source import (
        ReferenceSoundSourceVerdict,
        ReferenceSourceCalibration,
        ReferenceSourceDriftResult,
    )

#: Labels shared by more than one renderer; the English text is also the key
#: into ``_STRINGS``.
_LEVEL_LABEL = "Level [dB]"
_DEVIATION_LABEL = r"Deviation $\Delta L_{pi}$ [dB]"
_RADIUS_LABEL = "Distance from the origin [m]"
_TABLE_A1_LABEL = "Table A.1 limit"
_KILO = 1000.0
#: The core frequency range of ISO 6926 5.4, in hertz.
_CORE_RANGE_HZ = (100.0, 10000.0)

_STRINGS: dict[str, str] = {
    _LEVEL_LABEL: "Nivel [dB]",
    _DEVIATION_LABEL: r"Desviación $\Delta L_{pi}$ [dB]",
    _RADIUS_LABEL: "Distancia al origen [m]",
    _TABLE_A1_LABEL: "Límite de la tabla A.1",
    "Qualified distance {radius} m": "Distancia cualificada {radius} m",
    "Traverse {n}": "Recorrido {n}",
    "Deviation from the inverse square law at {frequency} Hz ({room})": (
        "Desviación de la ley del cuadrado inverso a {frequency} Hz ({room})"
    ),
    "anechoic": "anecoica",
    "hemi-anechoic": "semianecoica",
    "Qualified distance [m]": "Distancia cualificada [m]",
    "Qualified distance per frequency": "Distancia cualificada por frecuencia",
    "Every requirement met": "Todos los requisitos cumplidos",
    "A requirement not met": "Algún requisito incumplido",
    "Maximum qualified radius": "Radio máximo cualificado",
    "Measurement radius": "Radio de medida",
    "ISO 3745 Annex A: {verdict}": "ISO 3745 anexo A: {verdict}",
    "full conformity": "conformidad plena",
    "not qualified": "no cualificada",
    "reduced range": "intervalo reducido",
    "requirements not judged": "requisitos sin juzgar",
    "Reduced range, {low} to {high}": "Intervalo reducido, de {low} a {high}",
    "Radius over the reduced range": "Radio en el intervalo reducido",
    "Largest level above the mean": "Mayor nivel sobre la media",
    "Largest level below the mean": "Mayor nivel bajo la media",
    "Table B.1 limit": "Límite de la tabla B.1",
    "Deviation from the mean [dB]": "Desviación respecto a la media [dB]",
    "Test source directionality ({room}): {verdict}": (
        "Directividad de la fuente de ensayo ({room}): {verdict}"
    ),
    "suitable": "apta",
    "not suitable": "no apta",
    "Sound power level $L_W$ [dB re 1 pW]": (
        "Nivel de potencia acústica $L_W$ [dB re 1 pW]"
    ),
    "One-third octave $L_W$": "$L_W$ en tercios de octava",
    "Expanded uncertainty $U$": "Incertidumbre expandida $U$",
    "Reference sound source calibration (ISO 6926)": (
        "Calibración de la fuente sonora de referencia (ISO 6926)"
    ),
    "Share of the limit": "Fracción del límite",
    "Repeatability $\\sigma_r$ / Table 1": "Repetibilidad $\\sigma_r$ / tabla 1",
    "Step to the adjacent band / its limit": ("Salto a la banda contigua / su límite"),
    "Directivity index / 6 dB": "Índice de directividad / 6 dB",
    "Supply variation / 0.3 dB": "Variación con la alimentación / 0,3 dB",
    "Range, 100 Hz to 10 kHz / 12 dB": "Rango, de 100 Hz a 10 kHz / 12 dB",
    "Range, extended bands / 16 dB": "Rango, bandas ampliadas / 16 dB",
    "Limit": "Límite",
    "Reference sound source (ISO 6926 clause 5): {verdict}": (
        "Fuente sonora de referencia (ISO 6926 apartado 5): {verdict}"
    ),
    "complies": "cumple",
    "does not comply": "no cumple",
    "not all judged": "no todo juzgado",
    "Change between checks [dB]": "Cambio entre comprobaciones [dB]",
    "Change": "Cambio",
    "2.83 times Table 1": "2,83 veces la tabla 1",
    "Drift (ISO 6926 5.6): {verdict}": "Deriva (ISO 6926 5.6): {verdict}",
    "no recalibration needed": "no requiere recalibración",
    "recalibration required": "requiere recalibración",
}


def _t(text: str, language: str = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


def _number(value: float, language: str, places: int = 2) -> str:
    text = f"{value:.{places}f}"
    return text.replace(".", ",") if language == "es" else text


def _hertz(value: float, language: str) -> str:
    """A band frequency as a label: ``125 Hz``, ``6.3 kHz`` (``6,3 kHz``)."""
    text = f"{value / _KILO:g} kHz" if value >= _KILO else f"{value:g} Hz"
    return text.replace(".", ",") if language == "es" else text


def _in_range(freqs: np.ndarray, low: float, high: float) -> np.ndarray:
    """The frequencies whose one-third octave band lies within ``low``-``high``.

    Nominal and exact mid-band frequencies differ by under 3 %, well inside
    the half band of 12 % either way.
    """
    edge = 10.0 ** (1.0 / 20.0)
    return np.asarray((freqs >= low / edge) & (freqs <= high * edge), dtype=bool)


def _check_failed(result: FreeFieldCheck) -> bool:
    """Whether a requirement the check judged is not met.

    A judged failure decides the verdict whatever the missing data would
    show, so it outranks "requirements not judged" in the title.
    """
    room_level = (
        not result.traverse_count_met
        or result.path_angles_met is False
        or result.reflecting_plane_met is False
        or result.path_targets_met is False
        or result.working_area_met is False
    )
    return bool(room_level or not np.all(result.band_met))


def _check_verdict(result: FreeFieldCheck) -> str:
    if result.passes:
        return "full conformity"
    if result.conforming_range_hz is not None and not result.not_judged:
        return "reduced range"
    if _check_failed(result) or not result.not_judged:
        return "not qualified"
    return "requirements not judged"


def _source_verdict(result: ReferenceSoundSourceVerdict) -> str:
    if result.passes:
        return "complies"
    failed = (
        result.stability_met is False
        or result.supply_met is False
        or not result.spectrum_met
        or result.directivity_met is False
    )
    if failed or not result.not_judged:
        return "does not comply"
    return "not all judged"


def plot_inverse_square_law(
    result: InverseSquareLawResult,
    ax: Axes | None = None,
    *,
    frequency_hz: float | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""Deviation from the inverse square law along each traverse at one frequency.

    One curve per traverse of :math:`\Delta L_{pi}` against the distance from
    the mathematical origin, the Table A.1 limits of the band as dashed lines
    and the distance to which the frequency is qualified on every traverse as
    a vertical line.

    :param result: An
        :class:`~phonometry.emission.free_field_qualification.InverseSquareLawResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param frequency_hz: The frequency to draw; ``None`` picks the one
        qualified to the shortest distance.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to every deviation curve.
    :return: The axes.
    :raises ValueError: if ``frequency_hz`` is not one of the test frequencies.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies_hz, dtype=np.float64)
    if frequency_hz is None:
        column = int(np.argmin(result.band_radius_m))
    else:
        matches = np.flatnonzero(np.isclose(freqs, float(frequency_hz)))
        if matches.size == 0:
            msg = f"'frequency_hz' {frequency_hz:g} is not one of the test frequencies."
            raise ValueError(msg)
        column = int(matches[0])
    # A.3.3 allows up to eight traverses, one hue each: the shared series
    # hues, then three more tab10 hues (red stays with the Table A.1 limit).
    colours = (
        _C_PRIMARY,
        _C_SECONDARY,
        _C_TERTIARY,
        _C_QUATERNARY,
        "#8c564b",
        "#17becf",
        "#e377c2",
        _C_MUTED,
    )
    markers = ("o", "s", "^", "v", "D", "P", "X", "*")
    drawn: list[np.ndarray] = []
    for index, (r, dev, name) in enumerate(
        zip(
            result.distances_m, result.deviations_db, result.traverse_names, strict=True
        )
    ):
        values = dev[:, column]
        keep = np.isfinite(values)
        order = np.argsort(r[keep])
        curve = dict(kwargs)
        style_default(curve, "color", colours[index % len(colours)])
        curve.setdefault("marker", markers[index % len(markers)])
        style_default(curve, "markersize", 3)
        style_default(curve, "linewidth", 1.2)
        curve.setdefault("label", name or _t("Traverse {n}", language, n=index + 1))
        ax.plot(r[keep][order], values[keep][order], **curve)
        drawn.append(values[keep])
    limit = float(result.tolerance_db[column])
    for sign in (1.0, -1.0):
        ax.axhline(
            sign * limit,
            color=_C_REFERENCE,
            linestyle="--",
            linewidth=1.0,
            label=_t(_TABLE_A1_LABEL, language) if sign > 0 else None,
        )
    radius = float(result.band_radius_m[column])
    ax.axvline(
        radius,
        color=_C_MUTED,
        linestyle=":",
        linewidth=1.2,
        label=_t(
            "Qualified distance {radius} m",
            language,
            radius=_number(radius, language),
        ),
    )
    ax.set_xlabel(_t(_RADIUS_LABEL, language))
    ax.set_ylabel(_t(_DEVIATION_LABEL, language))
    frequency = freqs[column]
    ax.set_title(
        _t(
            "Deviation from the inverse square law at {frequency} Hz ({room})",
            language,
            frequency=_number(frequency, language, 0),
            room=_t(result.room, language),
        )
    )
    # Up to eight traverses fill the panel from end to end, so the legend gets
    # a band of its own above the curves and the Table A.1 limits.
    values = np.concatenate(drawn)
    low = min(float(np.min(values)), -limit)
    high = max(float(np.max(values)), limit)
    span = high - low
    ax.set_ylim(low - 0.08 * span, high + 0.6 * span)
    ax.grid(visible=True, alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small", ncol=2))
    localize_axes(ax, language)
    return ax


def plot_free_field_check(
    result: FreeFieldCheck,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Qualified distance per frequency, with the radius the verdict judged.

    One bar per evaluated frequency, coloured by whether every per-band
    requirement is met within the maximum qualified radius, the A.2.4 radius
    as a solid line and the measurement radius, when one was given, as a
    dashed one. When only a reduced range conforms, its bands are shaded and
    the radius qualified over them drawn as its own line. The title states the
    verdict: full conformity, a reduced range, not qualified (a requirement
    judged and not met), or requirements not judged.

    :param result: A
        :class:`~phonometry.emission.free_field_qualification.FreeFieldCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the bars.
    :return: The axes.
    """
    from matplotlib.patches import Patch

    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies_hz, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)
    met = np.asarray(result.band_met, dtype=bool)
    colours = [_C_PRIMARY if ok else _C_MUTED for ok in met]
    bars = dict(kwargs)
    style_default(bars, "color", colours)
    bars.setdefault("width", 0.6)
    ax.bar(positions, result.band_radius_m, **bars)
    # Proxy patches carry the bar colours into the legend: an empty bar
    # container would take the style's cycle colour instead.
    handles: list[Any] = []
    if np.any(met):
        handles.append(
            Patch(facecolor=_C_PRIMARY, label=_t("Every requirement met", language))
        )
    if not np.all(met):
        handles.append(
            Patch(facecolor=_C_MUTED, label=_t("A requirement not met", language))
        )
    ax.axhline(
        result.maximum_qualified_radius_m,
        color=_C_REFERENCE,
        linewidth=1.4,
        label=_t("Maximum qualified radius", language),
    )
    if result.measurement_radius_m is not None:
        ax.axhline(
            result.measurement_radius_m,
            color=_C_TERTIARY,
            linestyle="--",
            linewidth=1.2,
            label=_t("Measurement radius", language),
        )
    top = float(np.max(result.band_radius_m))
    if result.conforming_range_hz is not None and not result.passes:
        low, high = result.conforming_range_hz
        inside = np.flatnonzero(_in_range(freqs, low, high))
        ax.axvspan(
            positions[inside[0]] - 0.45,
            positions[inside[-1]] + 0.45,
            color=_C_TERTIARY,
            alpha=0.12,
            zorder=0,
            label=_t(
                "Reduced range, {low} to {high}",
                language,
                low=_hertz(low, language),
                high=_hertz(high, language),
            ),
        )
        ax.axhline(
            result.conforming_radius_m,
            color=_C_SECONDARY,
            linestyle="-.",
            linewidth=1.2,
            label=_t("Radius over the reduced range", language),
        )
        top = max(top, float(result.conforming_radius_m))
    verdict = _check_verdict(result)
    ax.set_title(
        _t("ISO 3745 Annex A: {verdict}", language, verdict=_t(verdict, language))
    )
    ax.set_ylabel(_t("Qualified distance [m]", language))
    ax.set_ylim(bottom=0.0, top=1.4 * top)
    ax.grid(visible=True, axis="y", alpha=0.3)
    drawn, _ = ax.get_legend_handles_labels()
    place_legend_clear(ax.legend(handles=handles + drawn, fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_source_directionality(
    result: SourceDirectionalityResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Largest deviations from the mean level per band against Table B.1.

    :param result: A
        :class:`~phonometry.emission.free_field_qualification.SourceDirectionalityResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the upward deviation bars.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies_hz, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)
    up = dict(kwargs)
    style_default(up, "color", _C_PRIMARY)
    up.setdefault("width", 0.6)
    up.setdefault("label", _t("Largest level above the mean", language))
    ax.bar(positions, result.maximum_positive_deviation_db, **up)
    ax.bar(
        positions,
        result.maximum_negative_deviation_db,
        width=up["width"],
        color=_C_SECONDARY,
        label=_t("Largest level below the mean", language),
    )
    limit = np.asarray(result.tolerance_db, dtype=np.float64)
    edges = np.concatenate([positions - 0.5, [positions[-1] + 0.5]])
    ax.stairs(limit, edges, color=_C_REFERENCE, linestyle="--", linewidth=1.2,
              label=_t("Table B.1 limit", language))  # fmt: skip
    ax.stairs(-limit, edges, color=_C_REFERENCE, linestyle="--", linewidth=1.2)
    ax.axhline(0.0, color=_C_MUTED, linewidth=0.8)
    verdict = "suitable" if result.passes else "not suitable"
    ax.set_title(
        _t(
            "Test source directionality ({room}): {verdict}",
            language,
            room=_t(result.room, language),
            verdict=_t(verdict, language),
        )
    )
    ax.set_ylabel(_t("Deviation from the mean [dB]", language))
    top = 1.6 * float(np.max(limit))
    ax.set_ylim(-top, top)
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_reference_source_calibration(
    result: ReferenceSourceCalibration,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The calibrated one-third octave sound power levels with their uncertainty.

    :param result: A
        :class:`~phonometry.emission.reference_sound_source.ReferenceSourceCalibration`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the level bars.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies_hz, dtype=np.float64)
    levels = np.asarray(result.sound_power_level_db, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)
    bars = dict(kwargs)
    style_default(bars, "color", _C_PRIMARY)
    bars.setdefault("width", 0.6)
    bars.setdefault("label", _t("One-third octave $L_W$", language))
    ax.bar(positions, levels, **bars)
    uncertainty = np.asarray(result.expanded_uncertainty_db, dtype=np.float64)
    shown = np.isfinite(uncertainty)
    ax.errorbar(
        positions[shown],
        levels[shown],
        yerr=uncertainty[shown],
        fmt="none",
        ecolor=_C_REFERENCE,
        capsize=3,
        label=_t("Expanded uncertainty $U$", language),
    )
    low = float(np.nanmin(levels))
    ax.set_ylim(bottom=low - 10.0, top=float(np.nanmax(levels)) + 6.0)
    ax.set_ylabel(_t("Sound power level $L_W$ [dB re 1 pW]", language))
    ax.set_title(_t("Reference sound source calibration (ISO 6926)", language))
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_reference_sound_source(
    result: ReferenceSoundSourceVerdict,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Each requirement of ISO 6926 clause 5 as a share of its limit.

    A value at or below 1 meets the requirement. Per band: the repeatability
    standard deviation over Table 1, the variation over the declared supply
    range over 0,3 dB, the step to the adjacent band over its 3 dB (or 4 dB)
    and the directivity index over 6 dB. Over a range of bands, as a
    horizontal segment across them: the spread from 100 Hz to 10 kHz over
    12 dB and, when the range is extended, the spread over every band over
    16 dB. A requirement not judged is not drawn. The title puts a judged
    failure before a requirement not judged.

    :param result: A
        :class:`~phonometry.emission.reference_sound_source.ReferenceSoundSourceVerdict`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the step curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies_hz, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)
    step = dict(kwargs)
    style_default(step, "color", _C_SECONDARY)
    step.setdefault("marker", "s")
    step.setdefault("label", _t("Step to the adjacent band / its limit", language))
    shares = [result.adjacent_step_db / result.adjacent_limit_db]
    ax.plot(positions, shares[0], **step)
    if result.repeatability_db is not None:
        shares.append(result.repeatability_db / result.repeatability_limit_db)
        ax.plot(
            positions,
            shares[-1],
            marker="o",
            color=_C_PRIMARY,
            label=_t("Repeatability $\\sigma_r$ / Table 1", language),
        )
    if result.supply_variation_db is not None:
        shares.append(np.abs(result.supply_variation_db) / result.supply_limit_db)
        ax.plot(
            positions,
            shares[-1],
            marker="D",
            color="#17becf",
            label=_t("Supply variation / 0.3 dB", language),
        )
    if result.directivity_index_db is not None:
        shares.append(result.directivity_index_db / result.directivity_limit_db)
        ax.plot(
            positions,
            shares[-1],
            marker="^",
            color=_C_TERTIARY,
            label=_t("Directivity index / 6 dB", language),
        )
    core = np.flatnonzero(_in_range(freqs, *_CORE_RANGE_HZ))
    if core.size and np.isfinite(result.core_range_db):
        share = result.core_range_db / result.core_range_limit_db
        shares.append(np.array([share]))
        ax.hlines(
            share,
            positions[core[0]] - 0.4,
            positions[core[-1]] + 0.4,
            colors=_C_QUATERNARY,
            linewidth=2.2,
            label=_t("Range, 100 Hz to 10 kHz / 12 dB", language),
        )
    if np.isfinite(result.extended_range_db):
        share = result.extended_range_db / result.extended_range_limit_db
        shares.append(np.array([share]))
        ax.hlines(
            share,
            positions[0] - 0.4,
            positions[-1] + 0.4,
            colors="#8c564b",
            linestyles="-.",
            linewidth=2.0,
            label=_t("Range, extended bands / 16 dB", language),
        )
    ax.axhline(1.0, color=_C_REFERENCE, linestyle="--", label=_t("Limit", language))
    ax.set_title(
        _t(
            "Reference sound source (ISO 6926 clause 5): {verdict}",
            language,
            verdict=_t(_source_verdict(result), language),
        )
    )
    ax.set_ylabel(_t("Share of the limit", language))
    highest = max(1.0, max(float(np.nanmax(v)) for v in shares))
    ax.set_ylim(bottom=0.0, top=1.8 * highest)
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small", ncol=2))
    localize_axes(ax, language)
    return ax


def plot_reference_source_drift(
    result: ReferenceSourceDriftResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Change of each band between two checks against 2,83 times Table 1.

    :param result: A
        :class:`~phonometry.emission.reference_sound_source.ReferenceSourceDriftResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the change bars.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies_hz, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)
    bars = dict(kwargs)
    style_default(bars, "color", _C_PRIMARY)
    bars.setdefault("width", 0.6)
    bars.setdefault("label", _t("Change", language))
    ax.bar(positions, result.change_db, **bars)
    limit = np.asarray(result.limit_db, dtype=np.float64)
    edges = np.concatenate([positions - 0.5, [positions[-1] + 0.5]])
    ax.stairs(limit, edges, color=_C_REFERENCE, linestyle="--", linewidth=1.2,
              label=_t("2.83 times Table 1", language))  # fmt: skip
    ax.stairs(-limit, edges, color=_C_REFERENCE, linestyle="--", linewidth=1.2)
    ax.axhline(0.0, color=_C_MUTED, linewidth=0.8)
    verdict = "no recalibration needed" if result.passes else "recalibration required"
    ax.set_title(
        _t(
            "Drift (ISO 6926 5.6): {verdict}",
            language,
            verdict=_t(verdict, language),
        )
    )
    ax.set_ylabel(_t("Change between checks [dB]", language))
    top = 1.8 * max(float(np.max(limit)), float(np.max(np.abs(result.change_db))))
    ax.set_ylim(-top, top)
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax
