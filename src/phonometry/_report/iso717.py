#  Copyright (c) 2026. Jose M. Requena-Plens
"""ISO 717 sound-insulation rating fiche (reportlab renderer).

Renders a :class:`~phonometry.building.insulation.WeightedRatingResult`
(airborne, ISO 717-1) or
:class:`~phonometry.building.insulation.ImpactRatingResult` (impact,
ISO 717-2) to a one-page PDF laid out like an accredited-laboratory test
report (modelled on ISO 10140-2 / ISO 16283 lab reports rated per ISO 717):

* a title and the standard-basis line (measurement standard + ISO 717 rating);
* an optional metadata header block (client, specimen, room conditions ...),
  rendered only for the fields supplied on the :class:`ReportMetadata`;
* a two-panel body with the one-third-octave table on the left and the
  measured-versus-shifted-reference curve on the right, drawn by the result's
  own ``plot(ax=...)`` so the curve is native to the library;
* a boxed single-number result ``Rw (C; Ctr) = X (a; b) dB`` (airborne) or
  ``Ln,w (CI) = X (y) dB`` (impact);
* an optional verdict row when a requirement is supplied;
* a footer identity/disclaimer block.

With ``verbose=True`` the table uses the ISO 717 Annex C columns instead
(frequency, measured value, shifted reference, unfavourable deviation).

reportlab, matplotlib and svglib are soft dependencies imported lazily here
(reportlab and svglib ship in the ``phonometry[report]`` extra, matplotlib in
``phonometry[plot]``); each is guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

import html
import math
import os
import tempfile
from typing import TYPE_CHECKING, Any, List, Tuple, cast

import numpy as np

from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..building.insulation import ImpactRatingResult, WeightedRatingResult

#: Installation hints for the two soft dependencies of the report.
_REPORTLAB_HINT = (
    "Rendering a report requires reportlab. Install it with: "
    "pip install phonometry[report]"
)
_MATPLOTLIB_HINT = (
    "Rendering the report figure requires matplotlib. Install it with: "
    "pip install phonometry[plot]"
)
_SVGLIB_HINT = (
    "Embedding the report figure as vector graphics requires svglib. Install "
    "it with: pip install phonometry[report]"
)

#: Accent and light shades used for the header row and the zebra striping,
#: matching the validated Annex C fiche prototype.
_ACCENT_HEX = "#1f4e79"
_LIGHT_HEX = "#eef2f7"
_MUTED_HEX = "#555555"
_VERDICT_OK_HEX = "#1b6e2f"
_VERDICT_BAD_HEX = "#a11a1a"

#: Maximum sum of unfavourable deviations quoted in the statement (ISO 717-1
#: Clause 4.4 / ISO 717-2 Clause 4.3): 32,0 dB for the 16 one-third-octave
#: bands, 10,0 dB for the 5 octave bands.
_MAX_UNFAVOURABLE_THIRD = 32.0
_MAX_UNFAVOURABLE_OCTAVE = 10.0

#: Threshold below which an unfavourable deviation is shown as an em dash.
_DEVIATION_EPS = 0.05

#: Fixed disclaimer always printed in the footer of the fiche.
_DISCLAIMER = "The results relate only to the tested specimen."


def _render_figure_drawing(
    result: "WeightedRatingResult | ImpactRatingResult",
    target_width: float,
) -> Any:
    """Draw the result's ISO 717 plot as a scaled, vector reportlab Drawing.

    The plot is saved to SVG with the text rasterised to vector paths
    (``svg.fonttype='path'``) and converted with svglib, so the figure stays
    crisp at any zoom/print resolution. ``target_width`` is in points.
    """
    try:
        import matplotlib
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        raise ImportError(_MATPLOTLIB_HINT) from exc
    try:
        from svglib.svglib import svg2rlg
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        raise ImportError(_SVGLIB_HINT) from exc

    svg_fd, svg_path = tempfile.mkstemp(suffix=".svg")
    os.close(svg_fd)
    try:
        fig = Figure(figsize=(5.8, 6.4))
        FigureCanvasAgg(fig)
        ax = fig.subplots()
        result.plot(ax=ax)
        # The fiche states Rw/Ln,w (C; Ctr) in the boxed result, so the plot's
        # own title would only duplicate it at a large size.
        ax.set_title("")
        # Fixed 0-based y-axis like accredited reports (expanded if the data
        # exceeds the default top), so fiches are visually comparable.
        default_top = 80.0 if result.quantity == "impact" else 60.0
        _, data_top = ax.get_ylim()
        ax.set_ylim(0.0, max(default_top, float(np.ceil(data_top / 10.0) * 10.0)))
        # Move the legend above the axes, as the reference reports do.
        handles, labels = ax.get_legend_handles_labels()
        existing = ax.get_legend()
        if existing is not None:
            existing.remove()
        if handles:
            ax.legend(
                handles, labels, loc="lower left",
                bbox_to_anchor=(0.0, 1.005), ncol=len(handles),
                frameon=False, fontsize=8, handlelength=1.6, columnspacing=1.2,
            )
        fig.tight_layout()
        with matplotlib.rc_context({"svg.fonttype": "path"}):
            fig.savefig(svg_path, format="svg")
        drawing = svg2rlg(svg_path)
    finally:
        if os.path.exists(svg_path):
            os.remove(svg_path)
    if drawing is None or not drawing.width:
        raise ValueError("Could not convert the report plot to vector graphics.")
    scale = target_width / drawing.width
    drawing.scale(scale, scale)
    drawing.width = drawing.width * scale
    drawing.height = drawing.height * scale
    drawing.hAlign = "CENTER"
    return drawing


def _labels(
    result: "WeightedRatingResult | ImpactRatingResult",
) -> Tuple[str, str, str, str]:
    """Return ``(title, rating_part, statement, value_header)`` for the quantity."""
    if result.quantity == "impact":
        impact = cast("ImpactRatingResult", result)
        title = "Impact sound insulation rating"
        rating_part = "ISO 717-2"
        statement = (
            f"L<sub>n,w</sub> (C<sub>I</sub>) = "
            f"<b>{impact.rating} ({impact.ci:+d}) dB</b>"
        )
        value_header = "L<sub>n</sub>"
    else:
        airborne = cast("WeightedRatingResult", result)
        title = "Airborne sound insulation rating"
        rating_part = "ISO 717-1"
        statement = (
            f"R<sub>w</sub> (C; C<sub>tr</sub>) = "
            f"<b>{airborne.rating} ({airborne.c:+d}; {airborne.ctr:+d}) dB</b>"
        )
        value_header = "R"
    return title, rating_part, statement, value_header


def _fmt_num(value: float) -> str:
    """Format a number with up to one decimal, dropping a trailing ``.0``.

    The fiche is English, so the decimal separator is a period (matching
    accredited English lab reports such as the Salford reference).
    """
    text = f"{float(value):.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _metadata_pairs(
    metadata: ReportMetadata,
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Build the two ordered (label, value) groups of the header grid.

    Only fields that are set are returned, so empty rows never appear.
    """

    def group(specs: List[Tuple[str, str | None]]) -> List[Tuple[str, str]]:
        # Values are user-supplied free text; escape XML specials so a '&' or
        # '<' cannot break reportlab's Paragraph parser. Labels are fixed and
        # carry intentional markup (e.g. <super>), so they are left as-is.
        return [
            (label, html.escape(str(value)))
            for label, value in specs
            if value is not None
        ]

    identity = group(
        [
            ("Client", metadata.client),
            ("Mounted by", metadata.mounted_by),
            (
                "Sample area S [m<super>2</super>]",
                _fmt_num(metadata.area) if metadata.area is not None else None,
            ),
            ("Manufacturer", metadata.manufacturer),
            ("Description", metadata.specimen),
            ("Test room", metadata.test_room),
            ("Date of test", metadata.test_date),
        ]
    )
    def num(value: float | None) -> str | None:
        return _fmt_num(value) if value is not None else None

    # Per-room temperature/humidity when supplied; otherwise a single value.
    per_room_t = (
        metadata.source_temperature is not None
        or metadata.receiving_temperature is not None
    )
    per_room_rh = (
        metadata.source_relative_humidity is not None
        or metadata.receiving_relative_humidity is not None
    )
    conditions = group(
        [
            ("Source room volume [m<super>3</super>]", num(metadata.source_volume)),
            ("Source room temp. [&#176;C]", num(metadata.source_temperature)),
            ("Source room humidity [%]", num(metadata.source_relative_humidity)),
            (
                "Receiving room volume [m<super>3</super>]",
                num(metadata.receiving_volume),
            ),
            ("Receiving room temp. [&#176;C]", num(metadata.receiving_temperature)),
            (
                "Receiving room humidity [%]",
                num(metadata.receiving_relative_humidity),
            ),
            (
                "Temperature [&#176;C]",
                None if per_room_t else num(metadata.temperature),
            ),
            (
                "Relative humidity [%]",
                None if per_room_rh else num(metadata.relative_humidity),
            ),
            ("Ambient pressure [kPa]", num(metadata.pressure)),
            (
                "Mass per unit area [kg/m<super>2</super>]",
                num(metadata.mass_per_area),
            ),
            ("Mounting", metadata.mounting),
        ]
    )
    return identity, conditions


def _grid_table(pairs: List[Tuple[str, str]]) -> Any:
    """Lay an ordered list of (label, value) pairs into a two-column grid.

    Each grid row holds up to two label/value pairs (four table cells:
    ``label | value | label | value``); a trailing single pair is padded.
    Called only after :func:`render_iso717_report` has imported reportlab.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle

    styles = getSampleStyleSheet()
    accent = colors.HexColor(_ACCENT_HEX)
    label_style = ParagraphStyle(
        "iso717_meta_label", parent=styles["Normal"], fontSize=8,
        textColor=colors.HexColor(_MUTED_HEX),
    )
    value_style = ParagraphStyle(
        "iso717_meta_value", parent=styles["Normal"], fontSize=8.5,
        textColor=colors.black,
    )

    rows: List[List[Any]] = []
    for i in range(0, len(pairs), 2):
        left = pairs[i]
        right = pairs[i + 1] if i + 1 < len(pairs) else ("", "")
        rows.append(
            [
                Paragraph(f"{left[0]}:", label_style) if left[0] else "",
                Paragraph(left[1], value_style),
                Paragraph(f"{right[0]}:", label_style) if right[0] else "",
                Paragraph(right[1], value_style) if right[0] else "",
            ]
        )
    table = Table(
        rows,
        colWidths=[36 * mm, 51 * mm, 36 * mm, 51 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 1.2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, accent),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, accent),
            ]
        )
    )
    return table


def _value_table(
    centers: np.ndarray,
    measured: np.ndarray,
    shifted: np.ndarray,
    deviations: np.ndarray,
    value_header: str,
    verbose: bool,
) -> Any:
    """Build the left-hand one-third-octave table (accredited or Annex C).

    Called only after :func:`render_iso717_report` has imported reportlab.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle

    styles = getSampleStyleSheet()
    accent = colors.HexColor(_ACCENT_HEX)
    light = colors.HexColor(_LIGHT_HEX)
    thin = colors.HexColor("#c9d4e0")

    head_style = ParagraphStyle(
        "iso717_thead", parent=styles["Normal"], fontSize=7.2,
        textColor=colors.white, alignment=1, leading=8.5,
    )

    if verbose:
        header = [
            Paragraph("f [Hz]", head_style),
            Paragraph(f"Measured {value_header} [dB]", head_style),
            Paragraph("Shifted ref. [dB]", head_style),
            Paragraph("Unfav. dev. [dB]", head_style),
        ]
        col_widths = [15 * mm, 19 * mm, 18 * mm, 18 * mm]
    else:
        header = [
            Paragraph("Frequency f [Hz]", head_style),
            Paragraph(f"{value_header} [dB]", head_style),
        ]
        col_widths = [28 * mm, 28 * mm]

    def d1(value: float) -> str:
        # One decimal, period separator (English fiche), matching _fmt_num.
        return f"{value:.1f}"

    rows: List[List[Any]] = [header]
    for fk, m, r_, d in zip(centers, measured, shifted, deviations):
        if verbose:
            rows.append(
                [
                    f"{int(round(fk))}",
                    d1(m),
                    f"{r_:.0f}",
                    d1(d) if d > _DEVIATION_EPS else "—",
                ]
            )
        else:
            rows.append([f"{int(round(fk))}", d1(m)])

    n_data = len(centers)
    style_cmds: List[Any] = [
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, n_data), [colors.white, light]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, accent),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("BOX", (0, 0), (-1, -1), 0.5, accent),
    ]
    # Thin rule after every third-octave triplet, grouping the table by octave
    # exactly as the accredited reference report does.
    for triplet_end in range(3, n_data, 3):
        style_cmds.append(
            ("LINEBELOW", (0, triplet_end), (-1, triplet_end), 0.4, thin)
        )
    if verbose:
        rows.append(["", "", "sum", d1(float(deviations.sum()))])
        style_cmds += [
            ("LINEABOVE", (0, -1), (-1, -1), 0.6, accent),
            ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 7.5),
        ]

    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))
    return table


def _verdict(
    result: "WeightedRatingResult | ImpactRatingResult", requirement: float
) -> Tuple[str, bool]:
    """Return the verdict text and a PASS flag for a supplied requirement.

    Airborne ratings pass when the rating meets or exceeds the requirement;
    impact ratings pass when the rating is at or below it (lower is better).
    """
    rating = float(result.rating)
    req_text = _fmt_num(requirement)
    if result.quantity == "impact":
        passed = rating <= requirement
        text = (
            f"L<sub>n,w</sub> = {result.rating} dB, required &#8804; "
            f"{req_text} dB"
        )
    else:
        passed = rating >= requirement
        text = (
            f"R<sub>w</sub> = {result.rating} dB, required &#8805; "
            f"{req_text} dB"
        )
    return text, passed


def _footer_flow(metadata: ReportMetadata | None) -> List[Any]:
    """Build the footer identity block plus the always-present disclaimer.

    Called only after :func:`render_iso717_report` has imported reportlab.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, Spacer

    styles = getSampleStyleSheet()
    muted = colors.HexColor(_MUTED_HEX)

    ident_style = ParagraphStyle(
        "iso717_footer", parent=styles["Normal"], fontSize=8.5, leading=12,
    )
    sign_style = ParagraphStyle(
        "iso717_sign", parent=styles["Normal"], fontSize=8.5, leading=16,
    )
    disclaimer_style = ParagraphStyle(
        "iso717_disclaimer", parent=styles["Normal"], fontSize=8,
        textColor=muted, leading=11,
    )

    flow: List[Any] = [Spacer(1, 8)]
    lines: List[str] = []
    if metadata is not None:
        if metadata.laboratory:
            lines.append(f"<b>Laboratory:</b> {html.escape(metadata.laboratory)}")
        if metadata.report_id:
            lines.append(f"<b>Report no.:</b> {html.escape(metadata.report_id)}")
        if metadata.test_date:
            lines.append(f"<b>Date:</b> {html.escape(metadata.test_date)}")
        if metadata.notes:
            lines.append(f"<b>Notes:</b> {html.escape(metadata.notes)}")
    for line in lines:
        flow.append(Paragraph(line, ident_style))

    operator = metadata.operator if metadata is not None else None
    if operator:
        flow.append(
            Paragraph(
                f"Operator: {html.escape(operator)} &nbsp;&nbsp; "
                "Signature: ______________________________",
                sign_style,
            )
        )
    elif lines:
        flow.append(
            Paragraph(
                "Signature: ______________________________", sign_style
            )
        )

    flow.append(Spacer(1, 4))
    flow.append(
        Paragraph(
            f"<font color='{_ACCENT_HEX}'>&#9632;</font> {_DISCLAIMER}",
            disclaimer_style,
        )
    )
    flow.append(
        Paragraph(
            "<font size=7 color='#888888'>Generated by phonometry.</font>",
            disclaimer_style,
        )
    )
    return flow


def _result_box(
    statement: str,
    result: "WeightedRatingResult | ImpactRatingResult",
    styles: Any,
    accent: Any,
) -> Any:
    """The boxed single-number result, with extended terms when carried.

    Called only after :func:`render_iso717_report` has imported reportlab.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle

    result_style = ParagraphStyle(
        "iso717_result", parent=styles["Normal"], fontSize=13, leading=17,
        textColor=accent,
    )
    extended = _extended_terms(result)
    box_cells: List[Any] = [Paragraph(statement, result_style)]
    box_widths = [174 * mm]
    if extended:
        ext_style = ParagraphStyle(
            "iso717_ext", parent=styles["Normal"], fontSize=8.5, leading=12,
        )
        box_cells = [
            Paragraph(statement, result_style),
            Paragraph("<br/>".join(extended), ext_style),
        ]
        box_widths = [104 * mm, 70 * mm]
    box = Table([box_cells], colWidths=box_widths)
    box.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.0, accent),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(_LIGHT_HEX)),
            ]
        )
    )
    return box


def _verdict_flow(
    result: "WeightedRatingResult | ImpactRatingResult",
    metadata: ReportMetadata | None,
    styles: Any,
) -> List[Any]:
    """The optional PASS/FAIL verdict paragraph when a requirement is given.

    Called only after :func:`render_iso717_report` has imported reportlab.
    """
    if metadata is None or metadata.requirement is None:
        return []
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph

    text, passed = _verdict(result, metadata.requirement)
    badge = "PASS" if passed else "FAIL"
    badge_hex = _VERDICT_OK_HEX if passed else _VERDICT_BAD_HEX
    verdict_style = ParagraphStyle(
        "iso717_verdict", parent=styles["Normal"], fontSize=10, leading=14,
        spaceBefore=4,
    )
    return [
        Paragraph(
            f"Result vs requirement: {text} &#8594; "
            f"<b><font color='{badge_hex}'>{badge}</font></b>",
            verdict_style,
        )
    ]


def render_iso717_report(
    result: "WeightedRatingResult | ImpactRatingResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
) -> str:
    """Render an ISO 717 accredited-laboratory rating fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.building.insulation.WeightedRatingResult`
        (airborne, ISO 717-1) or
        :class:`~phonometry.building.insulation.ImpactRatingResult` (impact,
        ISO 717-2) carrying the per-band ``band_centers``, ``measured`` and
        ``shifted_reference`` curves.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        prediction fiche (body + result + disclaimer, no test metadata).
    :param verbose: When ``True``, the left table uses the ISO 717 Annex C
        columns (f, measured, shifted reference, unfavourable deviation);
        otherwise the accredited two-column ``f | value`` table.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    centers = result.band_centers
    measured = result.measured
    shifted = result.shifted_reference
    if centers is None or measured is None or shifted is None:
        raise ValueError(
            "render_iso717_report() needs 'band_centers', 'measured' and "
            "'shifted_reference' on the result."
        )
    centers = np.asarray(centers, dtype=np.float64)
    measured = np.asarray(measured, dtype=np.float64)
    shifted = np.asarray(shifted, dtype=np.float64)
    if not centers.shape == measured.shape == shifted.shape:
        raise ValueError(
            "render_iso717_report() needs 'band_centers', 'measured' and "
            "'shifted_reference' of equal length."
        )

    # Unfavourable deviation: reference above measurement (airborne) or
    # measurement above the reference (impact, the opposite sign).
    if result.quantity == "impact":
        deviations = np.maximum(measured - shifted, 0.0)
    else:
        deviations = np.maximum(shifted - measured, 0.0)

    title, rating_part, statement, value_header = _labels(result)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "iso717_title", parent=styles["Title"], fontSize=16, textColor=accent,
        spaceAfter=1, alignment=0,
    )
    basis_style = ParagraphStyle(
        "iso717_basis", parent=styles["Normal"], fontSize=9.5,
        textColor=colors.HexColor(_MUTED_HEX), spaceAfter=2,
    )
    caption_style = ParagraphStyle(
        "iso717_caption", parent=styles["Normal"], fontSize=8,
        textColor=accent, spaceAfter=3,
    )

    measurement_standard = (
        metadata.measurement_standard if metadata is not None else None
    )
    if measurement_standard:
        basis = (
            f"{html.escape(measurement_standard)} laboratory measurement of sound "
            f"insulation. Rating per {rating_part}:2020."
        )
    else:
        basis = f"Sound insulation rating per {rating_part}:2020."

    flow: List[Any] = [
        Paragraph(title, title_style),
        Paragraph(basis, basis_style),
    ]

    # Metadata header block (only the supplied fields).
    if metadata is not None and not metadata.is_empty():
        identity, conditions = _metadata_pairs(metadata)
        header_pairs = identity + conditions
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(_grid_table(header_pairs))
    flow.append(Spacer(1, 8))

    # Two-panel body: the one-third-octave table on the left (~70 mm), the
    # vector plot on the right filling the rest of the content width.
    value_table = _value_table(
        centers, measured, shifted, deviations, value_header, verbose
    )
    left_cell = [
        Paragraph(f"One-third-octave {value_header} [dB]", caption_style),
        value_table,
    ]
    plot_drawing = _render_figure_drawing(result, 116 * mm)
    body_table = Table(
        [[left_cell, plot_drawing]],
        colWidths=[56 * mm, 118 * mm],
    )
    body_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (-1, 0), (-1, 0), 0),
            ]
        )
    )
    flow.append(body_table)
    flow.append(Spacer(1, 8))

    # Boxed single-number result, optional verdict row, footer.
    flow.append(_result_box(statement, result, styles, accent))
    flow.extend(_verdict_flow(result, metadata, styles))
    flow.extend(_footer_flow(metadata))

    doc_kwargs = {
        "pagesize": A4,
        "leftMargin": 18 * mm,
        "rightMargin": 18 * mm,
        "topMargin": 15 * mm,
        "bottomMargin": 14 * mm,
        "title": title,
    }
    # invariant=1 drops the embedded timestamp for a reproducible PDF; the
    # guard tolerates reportlab builds that do not accept the keyword.
    try:
        doc = SimpleDocTemplate(path, invariant=1, **doc_kwargs)
    except TypeError:  # pragma: no cover - older reportlab
        doc = SimpleDocTemplate(path, **doc_kwargs)
    doc.build(flow)

    return str(path)


def _extended_terms(
    result: "WeightedRatingResult | ImpactRatingResult",
) -> List[str]:
    """Return the extended spectrum-adaptation terms the result carries, if any.

    The core rating results do not hold the enlarged-range terms, so this is
    normally empty; it only lists terms that are genuinely present on the
    object (never fabricated).
    """
    terms: List[str] = []
    airborne_specs = [
        ("c_50_3150", "C<sub>50-3150</sub>"),
        ("c_50_5000", "C<sub>50-5000</sub>"),
        ("c_100_5000", "C<sub>100-5000</sub>"),
        ("ctr_50_3150", "C<sub>tr,50-3150</sub>"),
        ("ctr_50_5000", "C<sub>tr,50-5000</sub>"),
        ("ctr_100_5000", "C<sub>tr,100-5000</sub>"),
    ]
    impact_specs = [("ci_50_2500", "C<sub>I,50-2500</sub>")]
    specs = impact_specs if result.quantity == "impact" else airborne_specs
    for attr, label in specs:
        value = getattr(result, attr, None)
        if value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            continue
        if not math.isfinite(number):  # pragma: no cover - defensive
            continue
        terms.append(f"{label} = {number:+.0f} dB")
    return terms
