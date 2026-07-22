#  Copyright (c) 2026. Jose M. Requena-Plens
"""ISO 10140 laboratory sound-insulation test report (reportlab renderer).

Renders a
:class:`~phonometry.building.lab_insulation.LabAirborneInsulationResult`
(laboratory airborne, ISO 10140-2:2010) or
:class:`~phonometry.building.lab_insulation.LabImpactInsulationResult`
(laboratory impact, ISO 10140-3:2010) to the one-page laboratory test report
each standard's Clause 6 prescribes, laid out like the accredited laboratory
reports rated per ISO 717:

* a title and the standard-basis line naming the laboratory standard, the
  reported quantity and the ISO 717 rating part;
* an optional metadata header block (client, specimen description, mounting,
  room volumes, climatic conditions ...), rendered only for the fields
  supplied on the :class:`ReportMetadata`; the grid is shared with the
  laboratory :mod:`.iso717` fiche (both describe a specimen in a test suite);
* a two-panel body with the one-third-octave table on the left (the quantity
  to one decimal place) and the measured curve versus the shifted ISO 717
  reference on the right, drawn by the rating's own ``plot(ax=...)`` so the
  curve is native to the library;
* a boxed single-number laboratory rating ``Rw (C; Ctr)`` (ISO 717-1) or
  ``Ln,w (CI)`` (ISO 717-2);
* the statement that the evaluation is based on laboratory measurement results
  obtained by a precision method (in the qualified suite flanking transmission
  is suppressed, so the *direct* R / Ln is reported, not the field R' / L'n);
* an optional verdict row when a requirement is supplied (airborne passes at
  or above it, impact at or below it);
* a footer identity/disclaimer block.

With ``verbose=True`` the table annexes the per-band equivalent sound
absorption area ``A = 0,16 V / T`` (ISO 10140-4:2010, Formula (5)) beside the
reported quantity, the normalization datum the laboratory report carries. The
quantity-independent skeleton lives in :mod:`._layout` and the header grid is
shared with :mod:`.iso717`; this module only holds the ISO 10140 specifics.
reportlab, matplotlib and svglib are soft dependencies imported lazily
(reportlab and svglib ship in the ``phonometry[report]`` extra, matplotlib in
``phonometry[plot]``); each is guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Sequence, Tuple, cast

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
    from ..building.lab_insulation import (
        LabAirborneInsulationResult,
        LabImpactInsulationResult,
    )

#: Per-quantity fixed labels: title, basis line, the quantity symbol used in
#: the table header, the rating symbol of the boxed result, the plot y-axis
#: label (mathtext) and the laboratory-method statement.
_SPECS: dict[str, dict[str, str]] = {
    "r": {
        "title": "Laboratory airborne sound insulation of a building element",
        "basis": (
            "Sound reduction index R measured in accordance with "
            "ISO 10140-2:2010 in a laboratory suppressing flanking "
            "transmission. Rating per ISO 717-1:2020."
        ),
        "symbol": "R",
        "rating_symbol": "R<sub>w</sub>",
        "ylabel": "$R$ [dB]",
        "statement": (
            "Evaluation based on laboratory measurement results obtained by a "
            "precision method (flanking transmission suppressed)."
        ),
    },
    "l_n": {
        "title": "Laboratory impact sound insulation of floors",
        "basis": (
            "Normalized impact sound pressure level L<sub>n</sub> measured in "
            "accordance with ISO 10140-3:2010 using the tapping machine. "
            "Rating per ISO 717-2:2020."
        ),
        "symbol": "L<sub>n</sub>",
        "rating_symbol": "L<sub>n,w</sub>",
        "ylabel": "$L_{n}$ [dB]",
        "statement": (
            "Evaluation based on laboratory measurement results obtained by a "
            "precision method with the standard tapping machine."
        ),
    },
}


def _statement(
    rating: "WeightedRatingResult | ImpactRatingResult", rating_symbol: str
) -> str:
    """The boxed laboratory single-number statement with its adaptation terms."""
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


def _table(
    centers: np.ndarray,
    columns: Sequence[Tuple[str, np.ndarray, int]],
    language: str,
) -> Any:
    """Build the left-hand band table.

    ``columns`` are ordered ``(header markup, values, decimals)`` triples
    following the frequency column; one column for the recommended-form table
    (``f | value``), more for the verbose (absorption-area) table. Called only
    after :func:`render_iso10140_report` has imported reportlab.
    """
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph

    head_style = band_table_header_style()

    if len(columns) == 1:
        header = [
            Paragraph(t("Frequency f [Hz]", language), head_style),
            Paragraph(columns[0][0], head_style),
        ]
        col_widths = [28 * mm, 28 * mm]
    else:
        header = [Paragraph(t("f [Hz]", language), head_style)] + [
            Paragraph(markup, head_style) for markup, _, _ in columns
        ]
        col_widths = [12 * mm] + [22 * mm for _ in columns]

    rows: List[List[Any]] = [header]
    for k, fk in enumerate(centers):
        row: List[Any] = [f"{int(round(fk))}"]
        for _, values, decimals in columns:
            row.append(format_number(float(values[k]), language, decimals=decimals))
        rows.append(row)

    return band_table(rows, col_widths, len(centers))


def _verdict(
    rating: "WeightedRatingResult | ImpactRatingResult",
    rating_symbol: str,
    requirement: float,
    language: str,
) -> Tuple[str, bool]:
    """Return the verdict text and PASS flag for a supplied requirement.

    Airborne laboratory ratings pass at or above the requirement; impact
    ratings pass at or below it (a lower impact level is better).
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


def render_iso10140_report(
    result: "LabAirborneInsulationResult | LabImpactInsulationResult",
    rating: "WeightedRatingResult | ImpactRatingResult",
    path: str,
    *,
    quantity: str,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an ISO 10140 laboratory sound-insulation test report to a PDF.

    :param result: The laboratory result
        (:class:`~phonometry.building.lab_insulation.LabAirborneInsulationResult`
        or
        :class:`~phonometry.building.lab_insulation.LabImpactInsulationResult`)
        carrying the per-band quantity and the equivalent absorption area.
    :param rating: The ISO 717 rating of the reported quantity (the result's
        own ``rating``); its ``plot`` draws the fiche curve.
    :param path: Destination path of the PDF file.
    :param quantity: ``"r"`` (airborne) or ``"l_n"`` (impact); validated by
        the caller.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        lightweight fiche (body, rating, statement and disclaimer).
    :param verbose: When ``True``, the left table annexes the per-band
        equivalent absorption area beside the reported quantity.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is
        not installed.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    spec = _SPECS[quantity]
    impact = rating.quantity == "impact"
    curve = np.asarray(getattr(result, quantity), dtype=np.float64)
    centers = np.asarray(rating.band_centers, dtype=np.float64)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title = t(spec["title"], language)
    flow: List[Any] = [
        Paragraph(title, title_style),
        Paragraph(t(spec["basis"], language), basis_style),
    ]

    # Metadata header block (only the supplied fields); same grid as the
    # laboratory ISO 717 fiche, both describe a specimen in a test suite.
    if metadata is not None and not metadata.is_empty():
        identity, conditions = _metadata_pairs(metadata, language)
        header_pairs = identity + conditions
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(header_pairs))
    flow.append(Spacer(1, 8))

    # Left panel: the recommended-form table (f | value) or the verbose
    # absorption-area column; right panel: the rating's own
    # measured-versus-shifted-reference curve.
    value_header = t("{vh} [dB]", language).format(vh=spec["symbol"])
    if verbose:
        absorption = np.asarray(result.absorption, dtype=np.float64)
        columns: List[Tuple[str, np.ndarray, int]] = [
            (t("A [m<super>2</super>]", language), absorption, 1),
            (value_header, curve, 1),
        ]
        caption = t("Per-band quantity and absorption area", language)
    else:
        columns = [(value_header, curve, 1)]
        # ISO 717-1/-2 Clause 4.4 requires stating whether the rating came
        # from one-third-octave or octave bands; the caption declares the set.
        caption_key = (
            "Octave-band {vh} [dB]"
            if centers.size == 5
            else "One-third-octave {vh} [dB]"
        )
        caption = t(caption_key, language).format(vh=spec["symbol"])
    value_table = _table(centers, columns, language)
    left_cell = [Paragraph(caption, caption_style), value_table]

    def _plot(ax: Any = None, language: str = language) -> Any:
        axes = rating.plot(ax=ax, language=language)
        axes.set_ylabel(t(spec["ylabel"], language))
        return axes

    y_top = _Y_TOP_IMPACT if impact else _Y_TOP_AIRBORNE
    plot_drawing = render_figure_drawing(
        _plot, 116 * mm, y_top=y_top, expand_step=10.0, language=language
    )
    flow.append(two_panel_body(left_cell, plot_drawing))
    flow.append(Spacer(1, 8))

    # Boxed laboratory rating, the laboratory-method statement, optional
    # verdict row and the footer.
    flow.append(
        result_box(
            _statement(rating, spec["rating_symbol"]), styles, accent
        )
    )
    statement_style = ParagraphStyle(
        "iso10140_statement", parent=styles["Normal"], fontSize=8.5,
        textColor=colors.HexColor(_MUTED_HEX), spaceBefore=4,
    )
    flow.append(Paragraph(t(spec["statement"], language), statement_style))
    if metadata is not None and metadata.requirement is not None:
        text, passed = _verdict(
            rating, spec["rating_symbol"], metadata.requirement, language
        )
        flow.extend(verdict_flow(text, passed, styles, language))
    flow.extend(footer_flow(metadata, language))

    return build_document(path, flow, title)
