#  Copyright (c) 2026. Jose M. Requena-Plens
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

from typing import TYPE_CHECKING, Any, Callable, List, Sequence, Tuple, cast

import numpy as np

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
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..building.insulation import ImpactRatingResult, WeightedRatingResult

#: A per-band table column: header markup, values and decimal places.
Column = Tuple[str, np.ndarray, int]

#: Builder of the left-hand table content for one report: given the reported
#: quantity's value header (already translated), its per-band curve, the
#: verbose flag and the language, it returns the ordered columns following the
#: frequency column, the panel caption and either explicit column widths (for
#: the multi-column verbose table) or ``None`` (the two-column ``f | value``
#: form, whose widths are fixed here).
ColumnsBuilder = Callable[
    [str, np.ndarray, bool, str], Tuple[Sequence[Column], str, Any]
]


def single_number_statement(
    rating: "WeightedRatingResult | ImpactRatingResult", rating_symbol: str
) -> str:
    """The boxed single-number statement with its adaptation terms.

    Airborne ratings print ``Xw (C; Ctr)``; impact ratings ``Xw (CI)``. The
    adaptation terms carry an explicit sign (the style of the accredited
    reports the fiche mirrors).
    """
    if rating.quantity == "impact":
        impact = cast("ImpactRatingResult", rating)
        return (
            f"{rating_symbol} (C<sub>I</sub>) = "
            f"<b>{impact.rating} ({impact.ci:+d}) dB</b>"
        )
    airborne = cast("WeightedRatingResult", rating)
    return (
        f"{rating_symbol} (C; C<sub>tr</sub>) = "
        f"<b>{airborne.rating} ({airborne.c:+d}; {airborne.ctr:+d}) dB</b>"
    )


def requirement_verdict(
    rating: "WeightedRatingResult | ImpactRatingResult",
    rating_symbol: str,
    requirement: float,
    language: str,
) -> Tuple[str, bool]:
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
    col_widths: Any = None,
) -> Any:
    """Build the left-hand per-band table.

    A single column following the frequency column is the recommended-form
    ``f | value`` table (fixed 28 mm columns, a ``Frequency f [Hz]`` heading);
    more columns are the verbose table (a compact ``f [Hz]`` heading and the
    ``col_widths`` supplied by the caller). Called only after the renderer has
    imported reportlab.
    """
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph

    head_style = band_table_header_style()

    if len(columns) == 1:
        header = [
            Paragraph(t("Frequency f [Hz]", language), head_style),
            Paragraph(columns[0][0], head_style),
        ]
        widths = [28 * mm, 28 * mm]
    else:
        header = [Paragraph(t("f [Hz]", language), head_style)] + [
            Paragraph(markup, head_style) for markup, _, _ in columns
        ]
        widths = col_widths

    rows: List[List[Any]] = [header]
    for k, fk in enumerate(centers):
        row: List[Any] = [f"{int(round(fk))}"]
        for _, values, decimals in columns:
            row.append(format_number(float(values[k]), language, decimals=decimals))
        rows.append(row)

    return band_table(rows, widths, len(centers))


def render_insulation_fiche(
    result: Any,
    rating: "WeightedRatingResult | ImpactRatingResult",
    path: str,
    *,
    is_impact: bool,
    curve_attr: str,
    title: str,
    basis: str,
    symbol: str,
    rating_symbol: str,
    ylabel: str,
    method_statement: str,
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
    :param is_impact: ``True`` for an impact quantity (ISO 717-2), ``False``
        for an airborne one (ISO 717-1); it selects the plot's y-axis top and
        is checked against ``rating.quantity``.
    :param curve_attr: Attribute name of the reported per-band curve on
        ``result`` (e.g. ``"dnt"``, ``"r"``, ``"l_n"``).
    :param title: Fixed English title (translated here).
    :param basis: Fixed English standard-basis line (translated here).
    :param symbol: The reported quantity's markup symbol for the table header.
    :param rating_symbol: The single-number rating symbol for the boxed result
        and the verdict row.
    :param ylabel: The plot y-axis label (mathtext, translated here).
    :param method_statement: Fixed English method statement (translated here).
    :param build_columns: Callback that builds the left-hand table content.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        lightweight fiche (body, rating, statement and disclaimer).
    :param verbose: When ``True``, the left table uses the report-specific
        verbose columns instead of the two-column ``f | value`` form.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ValueError: If ``rating.quantity`` does not match ``is_impact`` or
        the rating is missing its per-band ``band_centers`` / ``measured`` /
        ``shifted_reference`` arrays (a manually constructed rating).
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    # Guard a manually constructed rating: its quantity must match the reported
    # result, and it must carry the per-band arrays the table and plot consume
    # (np.asarray(None) would otherwise yield a 0-d array and crash the table).
    if rating.quantity != ("impact" if is_impact else "airborne"):
        raise ValueError(
            "The ISO 717 rating quantity does not match the reported result."
        )
    if (
        rating.band_centers is None
        or rating.measured is None
        or rating.shifted_reference is None
    ):
        raise ValueError(
            "The report needs the ISO 717 per-band rating data ('band_centers', "
            "'measured' and 'shifted_reference') on the rating."
        )

    curve = np.asarray(getattr(result, curve_attr), dtype=np.float64)
    centers = np.asarray(rating.band_centers, dtype=np.float64)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title_text = t(title, language)
    flow: List[Any] = [
        Paragraph(title_text, title_style),
        Paragraph(t(basis, language), basis_style),
    ]

    # Metadata header block (only the supplied fields; the same grid the two
    # sound-insulation families share, both describing rooms and a specimen).
    if metadata is not None and not metadata.is_empty():
        identity, conditions = _metadata_pairs(metadata, language)
        header_pairs = identity + conditions
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(header_pairs))
    flow.append(Spacer(1, 8))

    # Left panel: the report-specific table content; right panel: the rating's
    # own measured-versus-shifted-reference curve.
    value_header = t("{vh} [dB]", language).format(vh=symbol)
    columns, caption, col_widths = build_columns(
        value_header, curve, verbose, language
    )
    value_table = band_value_table(centers, columns, language, col_widths)
    left_cell = [Paragraph(caption, caption_style), value_table]

    def _plot(ax: Any = None, language: str = language) -> Any:
        axes = rating.plot(ax=ax, language=language)
        axes.set_ylabel(t(ylabel, language))
        return axes

    y_top = _Y_TOP_IMPACT if is_impact else _Y_TOP_AIRBORNE
    plot_drawing = render_figure_drawing(
        _plot, 116 * mm, y_top=y_top, expand_step=10.0, language=language
    )
    flow.append(two_panel_body(left_cell, plot_drawing))
    flow.append(Spacer(1, 8))

    # Boxed single-number rating, the method statement, optional verdict row
    # and the footer.
    flow.append(
        result_box(single_number_statement(rating, rating_symbol), styles, accent)
    )
    statement_style = ParagraphStyle(
        "insulation_statement", parent=styles["Normal"], fontSize=8.5,
        textColor=colors.HexColor(_MUTED_HEX), spaceBefore=4,
    )
    flow.append(Paragraph(t(method_statement, language), statement_style))
    if metadata is not None and metadata.requirement is not None:
        text, passed = requirement_verdict(
            rating, rating_symbol, metadata.requirement, language
        )
        flow.extend(verdict_flow(text, passed, styles, language))
    flow.extend(footer_flow(metadata, language))

    return build_document(path, flow, title_text)
