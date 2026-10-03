#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Shared renderer for the sound-insulation test-report fiches.

The field (ISO 16283, :mod:`.iso16283`) and laboratory (ISO 10140,
:mod:`.iso10140`) sound-insulation reports are the same one-page sheet: a title
and standard-basis line, an optional metadata header, a two-panel body with the
per-band table on the left and the measured-versus-shifted-ISO 717-reference
curve on the right, a boxed single-number rating, a method statement, an
optional requirement verdict and a footer. Only the fixed text (titles, basis
lines, symbols, the method statement) and the left-hand table content differ
between the two. This module holds the common skeleton so both renderers call
it, parameterised by their differences; the quantity-independent flowable
helpers still live in :mod:`._layout`.

reportlab, matplotlib and svglib are soft dependencies imported lazily
(reportlab and svglib ship in the ``phonometry[report]`` extra, matplotlib in
``phonometry[plot]``); each is guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

import numpy as np

from .._internal.validation import require_equal_shapes
from ._i18n import format_number, t
from ._layout import (
    _ACCENT_HEX,
    _MUTED_HEX,
    _REPORTLAB_HINT,
    band_table,
    band_table_header_style,
    build_document,
    document_styles,
    fmt_num,
    footer_flow,
    grid_table,
    render_figure_drawing,
    result_box,
    two_panel_body,
    verdict_flow,
)
from .iso717 import _Y_TOP_AIRBORNE, _Y_TOP_IMPACT, _metadata_pairs

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from matplotlib.axes import Axes
    from reportlab.platypus import Table

    from ..building.measurement.insulation import (
        ImpactRatingResult,
        WeightedRatingResult,
    )
    from .metadata import ReportMetadata

#: Cell padding, font size and leading of a compact band table, in points
#: (the regular table pads 2,6 pt and sets 8 pt type).
_COMPACT_PADDING_PT = 0.8
_COMPACT_FONT_PT = 7.4
_COMPACT_LEADING_PT = 8.6

#: A per-band table column: header markup, values and decimal places. The
#: values are numbers formatted to that many decimals in the fiche language,
#: or cells already written as text (a minimum value printed with its sign).
Column = tuple[str, "np.ndarray | Sequence[str]", int]


#: Builder of the left-hand table content for one report: given the reported
#: quantity's value header (already translated), its per-band curve, the
#: verbose flag and the language, it returns the ordered columns following the
#: frequency column, the panel caption and either explicit column widths (for
#: the multi-column verbose table) or ``None`` (the two-column ``f | value``
#: form, whose widths are fixed here).
class ColumnsBuilder(Protocol):
    """The call shape of a columns builder.

    A ``Callable[...]`` alias cannot say that a parameter is keyword-only, and
    ``verbose`` is one: it is a flag, and a flag is written by name. So the
    shape is declared as a protocol instead of an alias.
    """

    def __call__(
        self,
        value_header: str,
        curve: np.ndarray,
        *,
        verbose: bool,
        language: str,
    ) -> tuple[Sequence[Column], str, list[float] | None]:
        """Build the columns that follow the frequency column."""
        ...


def single_number_statement(
    rating: WeightedRatingResult | ImpactRatingResult, rating_symbol: str
) -> str:
    """The boxed single-number statement with its adaptation terms.

    Airborne ratings print ``Xw (C; Ctr)``; impact ratings ``Xw (CI)``. The
    adaptation terms carry an explicit sign (the style of the accredited
    reports the fiche mirrors).
    """
    if rating.quantity == "impact":
        # The tag proves the class: only ImpactRatingResult carries "impact".
        impact = rating
        return (
            f"{rating_symbol} (C<sub>I</sub>) = "
            f"<b>{impact.rating} ({impact.ci:+d}) dB</b>"
        )
    airborne = rating
    return (
        f"{rating_symbol} (C; C<sub>tr</sub>) = "
        f"<b>{airborne.rating} ({airborne.c:+d}; {airborne.ctr:+d}) dB</b>"
    )


def requirement_verdict(
    rating: WeightedRatingResult | ImpactRatingResult,
    rating_symbol: str,
    requirement: float,
    language: str,
) -> tuple[str, bool]:
    """Return the verdict text and PASS flag for a supplied requirement.

    Airborne ratings pass at or above the requirement; impact ratings pass at
    or below it (a lower impact level is better).
    """
    value = float(rating.rating)
    req_text = fmt_num(requirement, language)
    if rating.quantity == "impact":
        passed = value <= requirement
        text = t("{sym} = {rating} dB, required &#8804; {req} dB", language)
    else:
        passed = value >= requirement
        text = t("{sym} = {rating} dB, required &#8805; {req} dB", language)
    return (
        text.format(sym=rating_symbol, rating=rating.rating, req=req_text),
        passed,
    )


def band_value_table(
    centers: np.ndarray,
    columns: Sequence[Column],
    language: str,
    col_widths: list[float] | None = None,
    *,
    compact: bool = False,
) -> Table:
    """Build the left-hand per-band table.

    A single column following the frequency column is the recommended-form
    ``f | value`` table (fixed 28 mm columns, a ``Frequency f [Hz]`` heading);
    more columns are the verbose table (a compact ``f [Hz]`` heading and the
    ``col_widths`` supplied by the caller). Called only after the renderer has
    imported reportlab.
    """
    from reportlab.lib.units import mm

    from ._layout import fiche_paragraph

    head_style = band_table_header_style()

    widths: list[float] | None
    if len(columns) == 1:
        header = [
            fiche_paragraph(t("Frequency f [Hz]", language), head_style),
            fiche_paragraph(columns[0][0], head_style),
        ]
        widths = [28 * mm, 28 * mm]
    else:
        header = [fiche_paragraph(t("f [Hz]", language), head_style)] + [
            fiche_paragraph(markup, head_style) for markup, _, _ in columns
        ]
        widths = col_widths

    rows: list[list[Any]] = [header]
    for k, fk in enumerate(centers):
        row: list[Any] = [f"{round(fk)}"]
        for _, values, decimals in columns:
            cell = values[k]
            row.append(
                cell
                if isinstance(cell, str)
                else format_number(float(cell), language, decimals=decimals)
            )
        rows.append(row)

    extra = None
    if compact:
        # Tighter rows: a form that tabulates 50 Hz to 5000 Hz under a long
        # header still has to come to one page.
        extra = [
            ("FONTSIZE", (0, 1), (-1, -1), _COMPACT_FONT_PT),
            ("LEADING", (0, 1), (-1, -1), _COMPACT_LEADING_PT),
            ("TOPPADDING", (0, 1), (-1, -1), _COMPACT_PADDING_PT),
            ("BOTTOMPADDING", (0, 1), (-1, -1), _COMPACT_PADDING_PT),
        ]
    return band_table(rows, widths, len(centers), extra, band_centres=centers)


def iso717_columns_builder(
    rating: WeightedRatingResult | ImpactRatingResult,
    *,
    is_impact: bool,
    symbol: str,
    band_set: str = "One-third-octave",
) -> ColumnsBuilder:
    """Build the left-table callback shared by the ISO 717-rated fiches.

    The default table is the two-column ``f | value`` form (caption
    ``{band_set} {symbol} [dB]``, either ``One-third-octave`` or
    ``Octave-band``); ``verbose`` shows the ISO 717 evaluation per band (the
    reported quantity, the shifted Table 3 reference and the unfavourable
    deviation), read from the rating so no extra per-band data is needed on the
    result. The unfavourable deviation is the reference above the measurement
    for a level difference or reduction index (more is better) and the
    measurement above the reference for an impact level (less is better),
    exactly as the ISO 717 rating forms it.
    """

    def build(
        value_header: str, curve: np.ndarray, *, verbose: bool, language: str
    ) -> tuple[Sequence[Column], str, Any]:
        from reportlab.lib.units import mm

        if not verbose:
            caption = t(f"{band_set} {{vh}} [dB]", language).format(vh=symbol)
            return [(value_header, curve, 1)], caption, None

        measured = np.asarray(rating.measured, dtype=np.float64)
        shifted = np.asarray(rating.shifted_reference, dtype=np.float64)
        if is_impact:
            deviation = np.maximum(measured - shifted, 0.0)
        else:
            deviation = np.maximum(shifted - measured, 0.0)
        columns: list[Column] = [
            (value_header, curve, 1),
            (t("Shifted ref. [dB]", language), shifted, 1),
            (t("Unfav. dev. [dB]", language), deviation, 1),
        ]
        col_widths = [10 * mm, 16 * mm, 15 * mm, 15 * mm]
        caption = t("ISO 717 evaluation per band", language)
        return columns, caption, col_widths

    return build


def render_insulation_fiche(
    result: object,
    rating: WeightedRatingResult | ImpactRatingResult,
    path: str,
    *,
    spec: dict[str, str],
    is_impact: bool,
    curve_attr: str,
    build_columns: ColumnsBuilder,
    metadata: ReportMetadata | None,
    verbose: bool,
    language: str,
) -> str:
    """Render a sound-insulation test-report fiche to a PDF at ``path``.

    :param result: The per-band result carrying the reported curve
        (``curve_attr``) and, for the verbose table, the report-specific
        per-band content the ``build_columns`` callback reads.
    :param rating: The ISO 717 rating of the reported quantity; its ``plot``
        draws the fiche curve and it must carry the per-band ``band_centers``,
        ``measured`` and ``shifted_reference`` arrays.
    :param path: Destination path of the PDF file.
    :param spec: Fixed English labels for the reported quantity, with keys
        ``title``, ``basis``, ``symbol``, ``rating_symbol``, ``ylabel`` and
        ``statement`` (the natural-language ones are translated here).
    :param is_impact: ``True`` for an impact quantity (ISO 717-2), ``False``
        for an airborne one (ISO 717-1); it selects the plot's y-axis top and
        is checked against ``rating.quantity``.
    :param curve_attr: Attribute name of the reported per-band curve on
        ``result`` (e.g. ``"dnt"``, ``"r"``, ``"l_n"``).
    :param build_columns: Callback that builds the left-hand table content.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        lightweight fiche (body, rating, statement and disclaimer).
    :param verbose: When ``True``, the left table uses the report-specific
        verbose columns instead of the two-column ``f | value`` form.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ValueError: If ``rating.quantity`` does not match ``is_impact``, or
        the rating is missing its per-band ``band_centers`` / ``measured`` /
        ``shifted_reference`` arrays, or those disagree in shape with the
        reported curve (all three, a manually constructed rating).
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    # The columns callback imports reportlab before the page is composed, so
    # the actionable hint is raised here, ahead of it.
    try:
        import reportlab  # noqa: F401
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc

    # Guard a manually constructed rating: its quantity must match the reported
    # result, and it must carry the per-band arrays the table and plot consume
    # (np.asarray(None) would otherwise yield a 0-d array and crash the table).
    if rating.quantity != ("impact" if is_impact else "airborne"):
        msg = "The ISO 717 rating quantity does not match the reported result."
        raise ValueError(msg)
    if (
        rating.band_centers is None
        or rating.measured is None
        or rating.shifted_reference is None
    ):
        msg = (
            "The report needs the ISO 717 per-band rating data ('band_centers', "
            "'measured' and 'shifted_reference') on the rating."
        )
        raise ValueError(msg)

    rating_symbol = spec["rating_symbol"]
    curve = np.asarray(getattr(result, curve_attr), dtype=np.float64)
    centers = np.asarray(rating.band_centers, dtype=np.float64)
    measured = np.asarray(rating.measured, dtype=np.float64)
    shifted = np.asarray(rating.shifted_reference, dtype=np.float64)
    require_equal_shapes(
        f"{type(result).__name__}.report",
        {
            curve_attr: curve.shape,
            "rating.band_centers": centers.shape,
            "rating.measured": measured.shape,
            "rating.shifted_reference": shifted.shape,
        },
        "band",
    )

    # Metadata header block (only the supplied fields; the same grid the two
    # sound-insulation families share, both describing rooms and a specimen).
    header_pairs: list[tuple[str, str]] = []
    if metadata is not None and not metadata.is_empty():
        identity, conditions = _metadata_pairs(metadata, language)
        header_pairs = identity + conditions

    # Left panel: the report-specific table content; right panel: the rating's
    # own measured-versus-shifted-reference curve.
    value_header = t("{vh} [dB]", language).format(vh=spec["symbol"])
    columns, caption, col_widths = build_columns(
        value_header, curve, verbose=verbose, language=language
    )

    def _plot(ax: Axes | None = None, language: str = language) -> Axes:
        axes = rating.plot(ax=ax, language=language)
        axes.set_ylabel(t(spec["ylabel"], language))
        return axes

    verdict: tuple[str, bool] | None = None
    if metadata is not None and metadata.requirement is not None:
        verdict = requirement_verdict(
            rating, rating_symbol, metadata.requirement, language
        )
    return compose_insulation_fiche(
        path,
        title=t(spec["title"], language),
        basis=t(spec["basis"], language),
        header_pairs=header_pairs,
        table=BandTable(
            centers=centers, columns=columns, caption=caption, col_widths=col_widths
        ),
        plot=FichePlot(
            draw=_plot,
            y_top=_Y_TOP_IMPACT if is_impact else _Y_TOP_AIRBORNE,
            expand_step=10.0,
        ),
        result=ResultBlock(
            box=single_number_statement(rating, rating_symbol),
            statement=t(spec["statement"], language),
            verdict=verdict,
        ),
        metadata=metadata,
        language=language,
    )


@dataclass(frozen=True)
class BandTable:
    """The left panel of a band fiche: the per-band table and its caption.

    :ivar centers: Band centre frequencies, in Hz, one table row each.
    :ivar columns: The columns after the frequency column.
    :ivar caption: The caption above the table (already translated).
    :ivar col_widths: Explicit column widths for a multi-column table, or
        ``None`` for the two-column ``f | value`` form.
    :ivar compact: Set the rows tighter, for a table of 50 Hz to 5000 Hz
        under a long header.
    """

    centers: np.ndarray
    columns: Sequence[Column]
    caption: str
    col_widths: list[float] | None = None
    compact: bool = False


@dataclass(frozen=True)
class FichePlot:
    """The right panel of a band fiche: the result's own plot and its axis.

    :ivar draw: Called with ``ax=`` and ``language=``; draws the plot.
    :ivar y_top: Fixed top of a 0-based y-axis, or ``None`` to keep the
        plot's own limits (see :func:`._layout.render_figure_drawing`).
    :ivar expand_step: Raise ``y_top`` to the next multiple of this step when
        the data exceeds it, or ``None``.
    :ivar figsize: Matplotlib figure size ``(width, height)`` in inches, or
        ``None`` for the default portrait panel; a form whose header grid is
        long draws a shorter panel to keep to one page.
    """

    draw: Callable[..., Axes]
    y_top: float | None
    expand_step: float | None = None
    figsize: tuple[float, float] | None = None


@dataclass(frozen=True)
class ResultBlock:
    """The block under the two panels of a band fiche: what the test found.

    :ivar box: The boxed single-number statement.
    :ivar statement: The method statement under the box (translated).
    :ivar extended: Further terms printed beside the boxed statement, or
        ``None``.
    :ivar verdict: ``(text, passed)`` of a requirement verdict, or ``None``.
    """

    box: str
    statement: str
    extended: list[str] | None = None
    verdict: tuple[str, bool] | None = None


def compose_insulation_fiche(
    path: str,
    *,
    title: str,
    basis: str,
    header_pairs: list[tuple[str, str]],
    table: BandTable,
    plot: FichePlot,
    result: ResultBlock,
    metadata: ReportMetadata | None,
    language: str,
    left_width_mm: float = 56.0,
    plot_width_mm: float = 118.0,
) -> str:
    """Lay out and write a one-page band fiche from its prepared parts.

    The skeleton every sound-insulation sheet shares: the title and basis
    line, the header grid, the per-band table beside the plot, the boxed
    single numbers (with an optional column of further terms), the method
    statement, the optional verdict and the footer. :func:`render_insulation_fiche`
    prepares the parts from an ISO 717 rating; the forms of ISO 10140-1
    (Figures H.4 and J.7) prepare their own, so all of them print the same way.

    :param path: Destination path of the PDF file.
    :param title: The title (translated).
    :param basis: The standard-basis line (translated).
    :param header_pairs: The ``(label, value)`` pairs of the header grid; an
        empty list leaves it out.
    :param table: The per-band table of the left panel.
    :param plot: The plot of the right panel.
    :param result: The boxed single numbers with any further terms beside
        them, the method statement and the optional verdict, under the two
        panels.
    :param metadata: The metadata whose identity block the footer prints.
    :param language: ``"en"`` or ``"es"``.
    :param left_width_mm: Width of the table panel, in mm.
    :param plot_width_mm: Width of the plot panel, in mm (the two sum to the
        174 mm content width).
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import Spacer

        from ._layout import fiche_paragraph
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    flow: list[Any] = [
        fiche_paragraph(title, title_style),
        fiche_paragraph(basis, basis_style),
    ]
    if header_pairs:
        flow.extend([Spacer(1, 3), grid_table(header_pairs)])
    flow.append(Spacer(1, 8))

    value_table = band_value_table(
        table.centers,
        table.columns,
        language,
        table.col_widths,
        compact=table.compact,
    )
    left_cell = [fiche_paragraph(table.caption, caption_style), value_table]
    plot_drawing = render_figure_drawing(
        plot.draw,
        (plot_width_mm - 2.0) * mm,
        y_top=plot.y_top,
        expand_step=plot.expand_step,
        figsize=plot.figsize,
        language=language,
    )
    flow.extend(
        [
            two_panel_body(
                left_cell,
                plot_drawing,
                left_width_mm=left_width_mm,
                plot_width_mm=plot_width_mm,
            ),
            Spacer(1, 8),
            result_box(result.box, styles, accent, result.extended),
        ]
    )
    statement_style = ParagraphStyle(
        "insulation_statement",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.HexColor(_MUTED_HEX),
        spaceBefore=4,
    )
    flow.append(fiche_paragraph(result.statement, statement_style))
    if result.verdict is not None:
        text, passed = result.verdict
        flow.extend(
            verdict_flow(text=text, passed=passed, styles=styles, language=language)
        )
    flow.extend(footer_flow(metadata, language))

    return build_document(path, flow, title)
