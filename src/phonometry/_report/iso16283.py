#  Copyright (c) 2026. Jose M. Requena-Plens
"""ISO 16283 field sound-insulation test report (reportlab renderer).

Renders a :class:`~phonometry.building.insulation.AirborneInsulationResult`
(field airborne, ISO 16283-1:2014) or
:class:`~phonometry.building.insulation.ImpactInsulationResult` (field
impact, ISO 16283-2:2020) to the one-page field test report of each
standard's Clause 14, laid out like the recommended results form (ISO
16283-1 Annex B / ISO 16283-2 Annex C) and the accredited field reports
built on it:

* a title and the standard-basis line naming the field standard, the
  reported quantity and the ISO 717 rating part;
* an optional metadata header block (client, construction description,
  room volumes, partition area, climatic conditions ...), rendered only
  for the fields supplied on the :class:`ReportMetadata`;
* a two-panel body with the one-third-octave table on the left (the
  quantity to one decimal place, Clause 12) and the field curve versus the
  shifted ISO 717 reference on the right, drawn by the rating's own
  ``plot(ax=...)`` so the curve is native to the library;
* a boxed single-number field rating ``DnT,w (C; Ctr)`` / ``R'w (C; Ctr)``
  (ISO 717-1) or ``L'nT,w (CI)`` / ``L'n,w (CI)`` (ISO 717-2);
* the mandatory statement that the evaluation is based on field
  measurement results obtained by an engineering method (Clause 14 and the
  Annex forms print it verbatim);
* an optional verdict row when a requirement is supplied (airborne passes
  at or above it, impact at or below it);
* a footer identity/disclaimer block.

With ``verbose=True`` the table shows the measurement chain instead: the
energy-average source/receiving (or impact) levels and the receiving-room
reverberation time beside the reported quantity, the per-band content the
accredited field reports annex. The quantity-independent skeleton lives in
:mod:`._layout` and the header grid is shared with :mod:`.iso717` (the two
sound-insulation fiches describe the same rooms); this module only holds
the ISO 16283 specifics. reportlab, matplotlib and svglib are soft
dependencies imported lazily (reportlab and svglib ship in the
``phonometry[report]`` extra, matplotlib in ``phonometry[plot]``); each is
guarded with an actionable :class:`ImportError`.
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
    from ..building.insulation import (
        AirborneInsulationResult,
        ImpactInsulationResult,
        ImpactRatingResult,
        WeightedRatingResult,
    )

#: Per-quantity fixed labels: title, basis line, the quantity symbol used in
#: the table header, the rating symbol of the boxed result, the plot y-axis
#: label (mathtext) and the field-method statement each standard's results
#: form prints verbatim.
_SPECS: dict[str, dict[str, str]] = {
    "dnt": {
        "title": "Field airborne sound insulation between rooms",
        "basis": (
            "Standardized level difference D<sub>nT</sub> measured in "
            "accordance with ISO 16283-1:2014 (field measurement). "
            "Rating per ISO 717-1:2020."
        ),
        "symbol": "D<sub>nT</sub>",
        "rating_symbol": "D<sub>nT,w</sub>",
        "ylabel": "Standardized level difference $D_{nT}$ [dB]",
        "statement": (
            "Evaluation based on field measurement using results obtained "
            "by an engineering method."
        ),
    },
    "r_prime": {
        "title": "Field airborne sound insulation between rooms",
        "basis": (
            "Apparent sound reduction index R&#8242; measured in "
            "accordance with ISO 16283-1:2014 (field measurement). "
            "Rating per ISO 717-1:2020."
        ),
        "symbol": "R&#8242;",
        "rating_symbol": "R&#8242;<sub>w</sub>",
        "ylabel": "Apparent sound reduction index $R'$ [dB]",
        "statement": (
            "Evaluation based on field measurement using results obtained "
            "by an engineering method."
        ),
    },
    "l_n_t": {
        "title": "Field impact sound insulation of floors",
        "basis": (
            "Standardized impact sound pressure level L&#8242;<sub>nT</sub> "
            "measured in accordance with ISO 16283-2:2020 using the tapping "
            "machine. Rating per ISO 717-2:2020."
        ),
        "symbol": "L&#8242;<sub>nT</sub>",
        "rating_symbol": "L&#8242;<sub>nT,w</sub>",
        "ylabel": "Standardized impact sound pressure level $L'_{nT}$ [dB]",
        "statement": (
            "Evaluation based on field measurement results obtained by an "
            "engineering method."
        ),
    },
    "l_n": {
        "title": "Field impact sound insulation of floors",
        "basis": (
            "Normalized impact sound pressure level L&#8242;<sub>n</sub> "
            "measured in accordance with ISO 16283-2:2020 using the tapping "
            "machine. Rating per ISO 717-2:2020."
        ),
        "symbol": "L&#8242;<sub>n</sub>",
        "rating_symbol": "L&#8242;<sub>n,w</sub>",
        "ylabel": "Normalized impact sound pressure level $L'_{n}$ [dB]",
        "statement": (
            "Evaluation based on field measurement results obtained by an "
            "engineering method."
        ),
    },
}


def _statement(
    rating: "WeightedRatingResult | ImpactRatingResult", rating_symbol: str
) -> str:
    """The boxed field single-number statement with its adaptation terms."""
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
    """Build the left-hand one-third-octave table.

    ``columns`` are ordered ``(header markup, values, decimals)`` triples
    following the frequency column; two columns for the recommended-form
    table (``f | value``), more for the verbose measurement-chain table.
    Called only after :func:`render_iso16283_report` has imported reportlab.
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
        col_widths = [10 * mm] + [
            (10 if decimals == 2 else 12) * mm for _, _, decimals in columns
        ]
        # The reported quantity (last column) carries the longest header
        # (symbol plus unit), so give it room to render on one line; the
        # total stays within the left panel plus the figure's own margin.
        col_widths[-1] = 15 * mm

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

    Airborne field ratings pass at or above the requirement; impact ratings
    pass at or below it (a lower impact level is better).
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


def render_iso16283_report(
    result: "AirborneInsulationResult | ImpactInsulationResult",
    rating: "WeightedRatingResult | ImpactRatingResult",
    path: str,
    *,
    quantity: str,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an ISO 16283 field sound-insulation test report to a PDF.

    :param result: The field result
        (:class:`~phonometry.building.insulation.AirborneInsulationResult`
        or :class:`~phonometry.building.insulation.ImpactInsulationResult`)
        carrying the per-band quantities and, when built by the measurement
        functions, the per-band chain (levels and reverberation times).
    :param rating: The ISO 717 rating of the reported 16-band quantity,
        already evaluated by the caller
        (:meth:`~phonometry.building.insulation.AirborneInsulationResult.report`
        validates and computes it); its ``plot`` draws the fiche curve.
    :param path: Destination path of the PDF file.
    :param quantity: ``"dnt"``, ``"r_prime"``, ``"l_n_t"`` or ``"l_n"``
        (validated by the caller).
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        lightweight fiche (body, rating, statement and disclaimer).
    :param verbose: When ``True``, the left table shows the per-band
        measurement chain (levels, reverberation time, quantity) instead of
        the two-column recommended form.
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

    # Metadata header block (only the supplied fields; same grid as the
    # laboratory ISO 717 fiche, both describe rooms and a separating element).
    if metadata is not None and not metadata.is_empty():
        identity, conditions = _metadata_pairs(metadata, language)
        header_pairs = identity + conditions
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(header_pairs))
    flow.append(Spacer(1, 8))

    # Left panel: the recommended-form table (f | value, Clause 12 one
    # decimal) or the verbose measurement-chain columns; right panel: the
    # rating's own measured-versus-shifted-reference curve.
    value_header = t("{vh} [dB]", language).format(vh=spec["symbol"])
    if verbose:
        if impact:
            impact_result = cast("ImpactInsulationResult", result)
            chain: List[Tuple[str, np.ndarray, int]] = [
                ("L<sub>i</sub> [dB]",
                 np.asarray(impact_result.li, dtype=np.float64), 1),
                ("T [s]", np.asarray(impact_result.t2, dtype=np.float64), 2),
            ]
        else:
            airborne_result = cast("AirborneInsulationResult", result)
            chain = [
                ("L<sub>1</sub> [dB]",
                 np.asarray(airborne_result.l1, dtype=np.float64), 1),
                ("L<sub>2</sub> [dB]",
                 np.asarray(airborne_result.l2, dtype=np.float64), 1),
                ("T [s]", np.asarray(airborne_result.t2, dtype=np.float64), 2),
            ]
        columns = chain + [(value_header, curve, 1)]
        caption = t("Per-band measurement chain", language)
    else:
        columns = [(value_header, curve, 1)]
        caption = t("One-third-octave {vh} [dB]", language).format(
            vh=spec["symbol"]
        )
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

    # Boxed field rating, the mandatory field-method statement, optional
    # verdict row and the footer.
    flow.append(
        result_box(
            _statement(rating, spec["rating_symbol"]), styles, accent
        )
    )
    statement_style = ParagraphStyle(
        "iso16283_statement", parent=styles["Normal"], fontSize=8.5,
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
