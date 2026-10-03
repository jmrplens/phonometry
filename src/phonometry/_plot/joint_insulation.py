#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the sound insulation of joints (lazy imports from result .plot()).

The results of :mod:`phonometry.building.measurement.joint_insulation`
(ISO 10140-1:2021 Annex J): the sound reduction index of a joint per metre
with the maximum of its test arrangement (the diagram of Figure J.7), a
variable slit against its gap width (Figures J.8 and J.9), and the checks on
the test element and on the gap widths of J.4. Lines of the page's own ink
(the maximum of the arrangement, the measured index, the minimal gap width)
are drawn with :func:`.common.theme_line`, so they keep 3:1 against the page
in the dark theme as in the light one. The Spanish terms are those of UNE-EN ISO 10140-1:
*índice de reducción acústica de juntas*, *anchura de la rendija*.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _band_axis,
    _new_axes,
    place_legend_clear,
    style_default,
    theme_fill,
    theme_line,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..building.measurement.joint_insulation import (
        GapWidthCheck,
        JointGapSeries,
        JointGapSeriesCheck,
        JointOpenBandRating,
        JointTestElementCheck,
        LabJointInsulationResult,
    )

#: Title of the joint figure.
_JOINT_TITLE = "Sound reduction index of a joint (ISO 10140-1 Annex J)"
#: Ordinate of the per-band joint figures.
_JOINT_LABEL = r"Sound reduction index of joints $R_\mathrm{s}$ [dB]"
#: Title of the gap-width figure (Figure J.8).
_SERIES_TITLE = "Variable slit against its gap width (ISO 10140-1 J.4)"
#: Title of the octave-band figure (Figure J.9).
_OCTAVES_TITLE = "Slit in octave bands at each gap width (ISO 10140-1 Figure J.9)"
#: Title of the check on the gap widths of J.4.
_WIDTHS_TITLE = "Gap widths of a variable slit (ISO 10140-1 J.4)"
#: The spread J.2.2 lets the gap readings take, in mm.
_GAP_SPREAD_MM = 0.3
#: Emphasis of the lines drawn in the page's own ink: the maximum of the
#: arrangement and the minimal gap width read as firmly as the axis labels,
#: the measured index as a quieter companion of the corrected one.
_INK_QUIET_FIRM = 0.67
_INK_QUIET_SOFT = 0.4
#: Abscissa of the gap-width figure.
_GAP_LABEL = r"Gap width $b$ [mm]"
#: Abscissa of the octave-band figure (Figure J.9).
_OCTAVE_LABEL = "Octave band [Hz]"
#: Ordinate of the gap-series figure and legend of its single numbers.
_SINGLE_NUMBER_LABEL = "single number [dB]"
#: Abscissa of the test-element check, and legend of its values.
_VALUE_BOUND_LABEL = "Value / bound"
#: Legend of the band J.2.2 lets a gap reading take about each target. It
#: reads the same in Spanish, so the table below has no entry for it.
_TOLERANCE_LABEL = "±{value} mm (J.2.2)"
#: The single numbers a series is plotted by, with their mathtext symbols.
_SERIES_SYMBOLS = {
    "r_s_w": r"$R_\mathrm{s,w}$",
    "r_s_w_c": r"$R_\mathrm{s,w} + C$",
    "r_s_w_ctr": r"$R_\mathrm{s,Atr} = R_\mathrm{s,w} + C_\mathrm{tr}$",
}

#: Spanish translations of the fixed strings, keyed by their English text.
_STRINGS: dict[str, str] = {
    _JOINT_TITLE: "Índice de reducción acústica de una junta (ISO 10140-1 Anexo J)",
    _JOINT_LABEL: r"Índice de reducción acústica de juntas $R_\mathrm{s}$ [dB]",
    _SERIES_TITLE: "Rendija variable frente a su anchura (ISO 10140-1 J.4)",
    _OCTAVES_TITLE: (
        "Rendija en bandas de octava a cada anchura (ISO 10140-1 Figura J.9)"
    ),
    _WIDTHS_TITLE: "Anchuras de una rendija variable (ISO 10140-1 J.4)",
    _GAP_LABEL: r"Anchura de la rendija $b$ [mm]",
    "Frequency [Hz]": "Frecuencia [Hz]",
    _OCTAVE_LABEL: "Banda de octava [Hz]",
    _SINGLE_NUMBER_LABEL: "magnitud global [dB]",
    "corrected": "corregido",
    "measured": "medido",
    "sealed joint": "junta sellada",
    "minimum value": "valor mínimo",
    "shifted reference (ISO 717-1)": "referencia desplazada (ISO 717-1)",
    "no rating (bands missing)": "sin índice (faltan bandas)",
    "measurements": "mediciones",
    "working range": "intervalo de trabajo",
    "Single numbers with the indicative bands open (ISO 10140-1 J.1)": (
        "Magnitudes globales con las bandas indicativas abiertas (ISO 10140-1 J.1)"
    ),
    "open bands: {bands} Hz": "bandas abiertas: {bands} Hz",
    "unbounded": "sin cota",
    "Joint test element (ISO 10140-1 J.2)": (
        "Elemento de ensayo de la junta (ISO 10140-1 J.2)"
    ),
    _VALUE_BOUND_LABEL: "Valor / límite",
    "length": "longitud",
    "width": "anchura",
    "required": "exigido",
    "bound": "límite",
    "Gap width along the joint (ISO 10140-1 J.2.2)": (
        "Anchura de la rendija a lo largo de la junta (ISO 10140-1 J.2.2)"
    ),
    "Reading": "Lectura",
    "readings": "lecturas",
    "average b = {value} mm": "media b = {value} mm",
    "{value} mm from the smallest reading": "{value} mm desde la lectura menor",
    "closed and sealed": "cerrada y sellada",
    "measured widths": "anchuras medidas",
    "conforms": "conforme",
    "does not conform": "no conforme",
}


def _t(text: str, language: str = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


def _num(value: float, language: str, decimals: int = 1) -> str:
    """A number with the language's decimal separator and a true minus."""
    from .._i18n import format_number

    return format_number(value, language, decimals=decimals)


def _int(value: float, language: str) -> str:
    """A whole number of decibels with a true minus sign."""
    return _num(float(value), language, decimals=0)


def _signed(value: float, language: str) -> str:
    """An adaptation term with its sign: ``+1``, ``0``, ``−4``."""
    text = _int(value, language)
    return f"+{text}" if value > 0 else text


def _verdict(*, passes: bool, language: str) -> str:
    """``conforms`` or ``does not conform``, localised."""
    return _t("conforms" if passes else "does not conform", language)


def _rating_headline(result: LabJointInsulationResult, language: str) -> str:
    """``Rs,w (C; Ctr) = 49 (−1; −4) dB``, in brackets when J.1 puts it there."""
    rating = result.rating
    if rating is None:
        return _t("no rating (bands missing)", language)
    text = (
        rf"$R_\mathrm{{s,w}}$ ($C$; $C_\mathrm{{tr}}$) = {_int(rating.rating, language)} "
        f"({_int(rating.c, language)}; {_int(rating.ctr, language)}) dB"
    )
    return f"({text})" if result.bracketed else text


def plot_lab_joint_insulation(
    result: LabJointInsulationResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The sound reduction index of a joint per band (ISO 10140-1:2021 Figure J.7).

    The corrected index :math:`R_\mathrm{s}`, with its minimum values marked,
    over the measured :math:`R_\mathrm{s}'` and the maximum of the arrangement
    :math:`R_\mathrm{s,max}`, and the shifted ISO 717-1 reference curve over
    the rating range 100 Hz to 3 150 Hz.

    :param result: A
        :class:`~phonometry.building.measurement.joint_insulation.LabJointInsulationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the :math:`R_\mathrm{s}` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies_hz, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)
    ink = ax.xaxis.label.get_color()
    ax.plot(
        positions,
        result.r_s_max_db,
        "s--",
        color=theme_line(ink, ax, quiet=_INK_QUIET_FIRM),
        lw=1.2,
        ms=4,
        label=rf"$R_\mathrm{{s,max}}$ ({_t('sealed joint', language)})",
    )
    ax.plot(
        positions,
        result.r_s_measured_db,
        ":",
        color=theme_line(ink, ax, quiet=_INK_QUIET_SOFT),
        lw=1.4,
        label=rf"$R_\mathrm{{s}}'$ ({_t('measured', language)})",
    )
    rating = result.rating
    if rating is not None and rating.shifted_reference is not None:
        core = [
            int(np.argmin(np.abs(freqs - f))) for f in np.asarray(rating.band_centers)
        ]
        ax.plot(
            positions[core],
            rating.shifted_reference,
            "-",
            color=_C_REFERENCE,
            lw=1.2,
            label=_t("shifted reference (ISO 717-1)", language),
        )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("label", rf"$R_\mathrm{{s}}$ ({_t('corrected', language)})")
    ax.plot(positions, result.r_s_db, **kwargs)
    minimum = np.asarray(result.minimum_value, dtype=bool)
    if bool(np.any(minimum)):
        ax.plot(
            positions[minimum],
            np.asarray(result.r_s_db)[minimum],
            "^",
            ls="",
            ms=10,
            mfc="none",
            mec=_C_SECONDARY,
            mew=1.6,
            label=rf"$\geq$ {_t('minimum value', language)}",
        )
    ax.set_ylabel(_t(_JOINT_LABEL, language))
    ax.set_title(f"{_t(_JOINT_TITLE, language)}\n{_rating_headline(result, language)}")
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="lower right", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_joint_open_band_rating(
    result: JointOpenBandRating,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The single numbers rated with the indicative bands taken as open (J.1).

    One bar per single number the rating bounds, each labelled with its
    value, so an adaptation term of a decibel or two reads beside an
    :math:`R_\mathrm{s,w}` fifty times taller, and a term of 0 dB shows its
    0 where the bar has no height; an unbounded one is named on the axis and
    left without a bar or a value.

    :param result: A
        :class:`~phonometry.building.measurement.joint_insulation.JointOpenBandRating`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``bar`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    terms = (
        (r"$R_\mathrm{s,w}$", result.r_s_w_db),
        (r"$C$", result.c_db),
        (r"$C_\mathrm{tr}$", result.ctr_db),
        (r"$C_{100-5000}$", result.c_100_5000_db),
        (r"$C_\mathrm{tr,100-5000}$", result.ctr_100_5000_db),
    )
    labels = [
        name if value is not None else f"{name}\n({_t('unbounded', language)})"
        for name, value in terms
    ]
    values = [0.0 if value is None else float(value) for _, value in terms]
    positions = np.arange(len(terms), dtype=np.float64)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t(_SINGLE_NUMBER_LABEL, language))
    bars = ax.bar(positions, values, width=0.6, **kwargs)
    texts = [
        ""
        if value is None
        else (_int(value, language) if k == 0 else _signed(value, language))
        for k, (_, value) in enumerate(terms)
    ]
    ax.bar_label(bars, labels=texts, padding=2, fontsize="small")
    ax.margins(y=0.15)
    ax.axhline(0.0, color=_C_MUTED, lw=1.0)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel(_t(_SINGLE_NUMBER_LABEL, language))
    bands = ", ".join(_num(f, language, decimals=0) for f in result.open_frequencies_hz)
    ax.set_title(
        f"{_t('Single numbers with the indicative bands open (ISO 10140-1 J.1)', language)}"
        f"\n{_t('open bands: {bands} Hz', language, bands=bands)}"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_joint_test_element_check(
    result: JointTestElementCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The length and width of a joint as fractions of their bounds (J.2.1, J.2.2).

    The length is drawn over its lower bound (1 m, or 5,0 m for a window or
    door gap) and the width over its upper bound of 50 mm, so both read
    against the one line at 1.

    :param result: A
        :class:`~phonometry.building.measurement.joint_insulation.JointTestElementCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``barh`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    length_bound = 5.0 if result.window_or_door_gap else 1.0
    ratios = [result.joint_length_m / length_bound, result.joint_width_mm / 50.0]
    # The value and the bound on separate lines: written as one inequality
    # the label would read "62.0 mm ≤ 50 mm" on a joint that fails.
    required = _t("required", language)
    relation = "≥" if result.window_or_door_gap else ">"
    names = [
        f"{_t('length', language)} {_num(result.joint_length_m, language, 2)} m\n"
        f"{required} {relation} {_num(length_bound, language, 1)} m",
        f"{_t('width', language)} {_num(result.joint_width_mm, language, 1)} mm\n"
        f"{required} ≤ {_num(50.0, language, 0)} mm",
    ]
    oks = [result.length_ok, result.width_ok]
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t(_VALUE_BOUND_LABEL, language))
    bars = ax.barh(np.arange(2.0), ratios, height=0.5, **kwargs)
    for bar, ok in zip(bars, oks, strict=True):
        if not ok:
            bar.set_hatch("//")
            bar.set_edgecolor(_C_SECONDARY)
    ax.axvline(1.0, color=_C_REFERENCE, ls="--", lw=1.4, label=_t("bound", language))
    ax.set_yticks(np.arange(2.0))
    ax.set_yticklabels(names)
    ax.set_xlim(0.0, 1.25 * max(1.0, *ratios))
    ax.set_xlabel(_t(_VALUE_BOUND_LABEL, language))
    ax.set_title(
        f"{_t('Joint test element (ISO 10140-1 J.2)', language)}: "
        f"{_verdict(passes=result.passes, language=language)}"
    )
    ax.grid(visible=True, axis="x", alpha=0.3)
    ax.legend(loc="lower right", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_gap_width_check(
    result: GapWidthCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The gap widths read along a joint with their average (J.2.2).

    The readings in the order given, their average (the gap width ``b``) and
    the 0,3 mm the readings may span, laid from the smallest one.

    :param result: A
        :class:`~phonometry.building.measurement.joint_insulation.GapWidthCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the readings ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    readings = np.asarray(result.readings_mm, dtype=np.float64)
    positions = np.arange(1, readings.size + 1, dtype=np.float64)
    low = float(np.min(readings))
    ax.axhspan(
        low,
        low + _GAP_SPREAD_MM,
        color=theme_fill(_C_TERTIARY, ax),
        lw=0,
        zorder=0,
        label=_t(
            "{value} mm from the smallest reading",
            language,
            value=_num(_GAP_SPREAD_MM, language, 1),
        ),
    )
    ax.axhline(
        result.gap_width_mm,
        color=_C_REFERENCE,
        ls="--",
        lw=1.2,
        label=_t(
            "average b = {value} mm",
            language,
            value=_num(result.gap_width_mm, language, 2),
        ),
    )
    style_default(kwargs, "color", _C_PRIMARY if result.passes else _C_SECONDARY)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("label", _t("readings", language))
    ax.plot(positions, readings, **kwargs)
    ax.set_xticks(positions)
    ax.set_xlabel(_t("Reading", language))
    ax.set_ylabel(_t(_GAP_LABEL, language))
    span = max(float(np.max(readings)) - low, _GAP_SPREAD_MM)
    ax.set_ylim(low - 0.6 * span, low + 1.8 * span)
    ax.set_title(
        f"{_t('Gap width along the joint (ISO 10140-1 J.2.2)', language)}: "
        f"{_verdict(passes=result.passes, language=language)}"
    )
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc="upper left", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_joint_gap_series(
    result: JointGapSeries,
    ax: Axes | None = None,
    language: str = "en",
    *,
    quantity: Literal["r_s_w", "r_s_w_c", "r_s_w_ctr"] = "r_s_w_ctr",
    **kwargs: Any,
) -> Axes:
    r"""A single number of a variable slit against its gap width (Figure J.8).

    The measured widths as open circles on the line through them, the
    working range from :math:`b_\mathrm{n}` to :math:`b_\mathrm{n} + 3` mm
    shaded, and :math:`b_\mathrm{min}` marked when the series carries it.

    :param result: A
        :class:`~phonometry.building.measurement.joint_insulation.JointGapSeries`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param quantity: ``"r_s_w"``, ``"r_s_w_c"`` or ``"r_s_w_ctr"`` (default).
    :param kwargs: Forwarded to the single-number ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    widths = np.asarray(result.gap_widths_mm, dtype=np.float64)
    values = result.single_number(quantity)
    low, high = result.working_range_mm
    ax.axvspan(
        low,
        high,
        color=theme_fill(_C_TERTIARY, ax),
        lw=0,
        zorder=0,
        label=rf"{_t('working range', language)} $\Delta b$ = "
        f"{_num(high - low, language, 0)} mm",
    )
    ax.axvline(
        low,
        color=_C_REFERENCE,
        ls="--",
        lw=1.2,
        label=rf"$b_\mathrm{{n}}$ = {_num(low, language, 1)} mm",
    )
    ax.axvline(
        high,
        color=_C_REFERENCE,
        ls=":",
        lw=1.4,
        label=rf"$b_\mathrm{{n}} + 3$ = {_num(high, language, 1)} mm",
    )
    if result.minimum_gap_mm is not None:
        ax.axvline(
            result.minimum_gap_mm,
            color=theme_line(ax.xaxis.label.get_color(), ax, quiet=_INK_QUIET_FIRM),
            ls="-.",
            lw=1.2,
            label=rf"$b_\mathrm{{min}}$ = {_num(result.minimum_gap_mm, language, 1)} mm",
        )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "markerfacecolor", "none")
    kwargs.setdefault(
        "label", f"{_SERIES_SYMBOLS[quantity]} ({_t('measurements', language)})"
    )
    ax.plot(widths, values, **kwargs)
    span = max(widths[-1], high) - min(widths[0], low, result.minimum_gap_mm or low)
    ax.set_xlim(
        min(widths[0], low, result.minimum_gap_mm or low) - 0.08 * span,
        max(widths[-1], high) + 0.08 * span,
    )
    ax.set_xlabel(_t(_GAP_LABEL, language))
    ax.set_ylabel(f"{_SERIES_SYMBOLS[quantity]} [dB]")
    ax.set_title(_t(_SERIES_TITLE, language))
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc="upper right", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_joint_gap_octaves(
    result: JointGapSeries,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The sound reduction index of a slit in octave bands at each gap width (Figure J.9).

    One curve per gap width, and above them the closed and sealed element
    (:math:`b = 0`) as :math:`R_\mathrm{s,max}`, which J.5.1 says Figure J.9
    also gives: the octave values of each distinct maximum the results carry,
    usually the one sealed measurement of the arrangement.

    :param result: A
        :class:`~phonometry.building.measurement.joint_insulation.JointGapSeries`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to every gap-width ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes
    from ..building.measurement.floor_covering_improvement import (
        improvement_octave_bands,
    )

    ax = ax if ax is not None else _new_axes()
    octaves = [r.octave_bands() for r in result.results]
    centres = octaves[0][0]
    positions = _band_axis(ax, centres, xlabel=_OCTAVE_LABEL, language=language)
    ax.set_xlabel(_t(_OCTAVE_LABEL, language))
    sealed: list[np.ndarray] = []
    for r in result.results:
        maximum = np.asarray(r.r_s_max_db, dtype=np.float64)
        if not any(np.array_equal(maximum, seen) for seen in sealed):
            sealed.append(maximum)
    ink = theme_line(ax.xaxis.label.get_color(), ax, quiet=1.0)
    for k, maximum in enumerate(sealed):
        freqs, values = improvement_octave_bands(
            maximum, result.results[0].frequencies_hz
        )
        index = [int(np.argmin(np.abs(centres - f))) for f in freqs]
        ax.plot(
            positions[index],
            values,
            "s-",
            color=ink,
            lw=1.6,
            ms=5,
            label=(
                rf"$b$ = 0, $R_\mathrm{{s,max}}$ ({_t('closed and sealed', language)})"
                if k == 0
                else "_nolegend_"
            ),
        )
    cmap_colors = _width_colours(len(octaves))
    for width, (freqs, values), colour in zip(
        result.gap_widths_mm, octaves, cmap_colors, strict=True
    ):
        per_line = dict(kwargs)
        style_default(per_line, "color", colour)
        per_line.setdefault("marker", "o")
        per_line.setdefault("label", f"$b$ = {_num(float(width), language, 1)} mm")
        index = [int(np.argmin(np.abs(centres - f))) for f in freqs]
        ax.plot(positions[index], values, **per_line)
    ax.set_ylabel(_t(_JOINT_LABEL, language))
    ax.set_title(_t(_OCTAVES_TITLE, language))
    ax.grid(visible=True, alpha=0.3)
    # Outside the axes: the curves fan out over the whole panel, the sealed
    # one across the top and the widest gaps along the bottom, so no corner
    # inside is free of measured points.
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        borderaxespad=0.0,
        fontsize="small",
    )
    localize_axes(ax, language)
    return ax


def plot_joint_gap_series_check(
    result: JointGapSeriesCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The gap widths measured against the three widths of J.4.

    :math:`b_\mathrm{min}` (when named), :math:`b_\mathrm{n}` and
    :math:`b_\mathrm{n} + 3` drawn as in Figure J.8, each with the 0,3 mm a
    measured width may lie from it shaded, and the measured widths as points
    on one line.

    :param result: A
        :class:`~phonometry.building.measurement.joint_insulation.JointGapSeriesCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-widths ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    nominal = result.nominal_gap_mm
    tolerance = result.tolerance_mm
    targets: list[tuple[float, str, str, Any]] = []
    if result.minimum_gap_mm is not None:
        targets.append(
            (
                result.minimum_gap_mm,
                "-.",
                rf"$b_\mathrm{{min}}$ = {_num(result.minimum_gap_mm, language, 1)} mm",
                theme_line(ax.xaxis.label.get_color(), ax, quiet=_INK_QUIET_FIRM),
            )
        )
    targets.append(
        (
            nominal,
            "--",
            rf"$b_\mathrm{{n}}$ = {_num(nominal, language, 1)} mm",
            _C_REFERENCE,
        )
    )
    end = nominal + 3.0
    targets.append(
        (
            end,
            ":",
            rf"$b_\mathrm{{n}} + 3$ = {_num(end, language, 1)} mm",
            _C_REFERENCE,
        )
    )
    fill = theme_fill(_C_TERTIARY, ax)
    for k, (width, style, label, colour) in enumerate(targets):
        ax.axvspan(
            width - tolerance,
            width + tolerance,
            color=fill,
            lw=0,
            zorder=0,
            label=(
                _t(_TOLERANCE_LABEL, language, value=_num(tolerance, language, 1))
                if k == 0
                else "_nolegend_"
            ),
        )
        ax.axvline(width, color=colour, ls=style, lw=1.3, label=label)
    widths = np.asarray(result.gap_widths_mm, dtype=np.float64)
    style_default(kwargs, "color", _C_PRIMARY if result.passes else _C_SECONDARY)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "linestyle", "")
    kwargs.setdefault("label", _t("measured widths", language))
    ax.plot(widths, np.zeros_like(widths), **kwargs)
    every = [*widths.tolist(), *(w for w, _, _, _ in targets)]
    span = max(max(every) - min(every), 1.0)
    ax.set_xlim(min(every) - 0.12 * span, max(every) + 0.12 * span)
    ax.set_ylim(-1.0, 1.0)
    ax.set_yticks([])
    ax.set_xlabel(_t(_GAP_LABEL, language))
    ax.set_title(
        f"{_t(_WIDTHS_TITLE, language)}: "
        f"{_verdict(passes=result.passes, language=language)}"
    )
    ax.grid(visible=True, axis="x", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def _width_colours(count: int) -> list[Any]:
    """One colour per gap width, from the narrowest (dark) to the widest."""
    from matplotlib import colormaps

    cmap = colormaps["viridis"]
    if count == 1:
        return [cmap(0.15)]
    return [cmap(0.1 + 0.75 * k / (count - 1)) for k in range(count)]
