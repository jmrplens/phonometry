#  Copyright (c) 2026. Jose M. Requena-Plens
"""ISO 717 Annex C sound-insulation rating fiche (reportlab renderer).

Renders a :class:`~phonometry.building.insulation.WeightedRatingResult`
(airborne, ISO 717-1) or
:class:`~phonometry.building.insulation.ImpactRatingResult` (impact,
ISO 717-2) to a one-page PDF that reproduces the ISO 717 Annex C layout:

* a header and the standard reference line;
* the single-number statement ``Rw (C; Ctr) = X (a; b) dB`` (airborne) or
  ``Ln,w (CI) = X (a) dB`` (impact);
* the measured-versus-shifted-reference plot, drawn by the result's own
  ``plot(ax=...)`` so the curve is native to the library;
* the Annex C Table C.1 evaluation table (frequency, measured value, shifted
  reference, unfavourable deviation) with the sum of unfavourable deviations
  at the foot;
* a statement-of-results paragraph.

reportlab and matplotlib are soft dependencies imported lazily here; both are
guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING, Any, Tuple, cast

import numpy as np

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

#: Maximum sum of unfavourable deviations quoted in the statement (ISO 717-1
#: Clause 4.4 / ISO 717-2 Clause 4.3): 32,0 dB for the 16 one-third-octave
#: bands, 10,0 dB for the 5 octave bands.
_MAX_UNFAVOURABLE_THIRD = 32.0
_MAX_UNFAVOURABLE_OCTAVE = 10.0

#: Threshold below which an unfavourable deviation is shown as an em dash.
_DEVIATION_EPS = 0.05


def _import_reportlab() -> Any:
    """Import the reportlab names lazily with an actionable error."""
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
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        raise ImportError(_REPORTLAB_HINT) from exc
    return {
        "colors": colors,
        "A4": A4,
        "ParagraphStyle": ParagraphStyle,
        "getSampleStyleSheet": getSampleStyleSheet,
        "mm": mm,
        "Paragraph": Paragraph,
        "SimpleDocTemplate": SimpleDocTemplate,
        "Spacer": Spacer,
        "Table": Table,
        "TableStyle": TableStyle,
    }


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
        fig = Figure(figsize=(6.8, 2.8))
        FigureCanvasAgg(fig)
        ax = fig.subplots()
        result.plot(ax=ax)
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
    """Return ``(title, subtitle, statement, value_header)`` for the quantity."""
    if result.quantity == "impact":
        impact = cast("ImpactRatingResult", result)
        title = "Impact sound insulation rating"
        subtitle = (
            "Weighted normalized impact sound pressure level "
            "L<sub>n,w</sub> and spectrum adaptation term. Evaluation per "
            "ISO 717-2:2020, Clause 4 and Annex C."
        )
        statement = (
            f"L<sub>n,w</sub> (C<sub>I</sub>) = "
            f"<b>{impact.rating} ({impact.ci:+d}) dB</b>"
        )
        value_header = "Ln\ndB"
    else:
        airborne = cast("WeightedRatingResult", result)
        title = "Airborne sound insulation rating"
        subtitle = (
            "Weighted sound reduction index R<sub>w</sub> and spectrum "
            "adaptation terms. Evaluation per ISO 717-1:2020, Clause 4 and "
            "Annex C."
        )
        statement = (
            f"R<sub>w</sub> (C; C<sub>tr</sub>) = "
            f"<b>{airborne.rating} ({airborne.c:+d}; {airborne.ctr:+d}) dB</b>"
        )
        value_header = "R\ndB"
    return title, subtitle, statement, value_header


def _summary_paragraph(
    result: "WeightedRatingResult | ImpactRatingResult", limit: float
) -> str:
    """Statement-of-results text, worded for airborne or impact sound."""
    limit_text = f"{limit:.1f}".replace(".", ",")
    if result.quantity == "impact":
        return (
            "Statement of results: the weighted impact rating and the spectrum "
            "adaptation term are determined by shifting the ISO 717-2 reference "
            "curve against the one-third-octave spectrum until the sum of "
            "unfavourable deviations (measurement above the reference) is as "
            "large as possible but not greater than "
            f"{limit_text} dB; L<sub>n,w</sub> is the shifted reference value "
            "at 500 Hz (octave-band ratings are further reduced by 5 dB, "
            "Clause 4.3.2). Generated by phonometry."
        )
    return (
        "Statement of results: the weighted sound reduction index and the "
        "spectrum adaptation terms are determined by shifting the ISO 717-1 "
        "reference curve against the one-third-octave spectrum until the sum of "
        "unfavourable deviations is as large as possible but not greater than "
        f"{limit_text} dB; R<sub>w</sub> is the shifted reference value at "
        "500 Hz. Generated by phonometry."
    )


def render_iso717_report(
    result: "WeightedRatingResult | ImpactRatingResult", path: str
) -> str:
    """Render an ISO 717 Annex C rating fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.building.insulation.WeightedRatingResult`
        (airborne, ISO 717-1) or
        :class:`~phonometry.building.insulation.ImpactRatingResult` (impact,
        ISO 717-2) carrying the per-band ``band_centers``, ``measured`` and
        ``shifted_reference`` curves.
    :param path: Destination path of the PDF file.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    rl = _import_reportlab()
    colors = rl["colors"]
    mm = rl["mm"]
    accent = colors.HexColor(_ACCENT_HEX)
    light = colors.HexColor(_LIGHT_HEX)

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

    limit = (
        _MAX_UNFAVOURABLE_THIRD
        if measured.size == 16
        else _MAX_UNFAVOURABLE_OCTAVE
    )
    # Unfavourable deviation: reference above measurement (airborne) or
    # measurement above the reference (impact, the opposite sign).
    if result.quantity == "impact":
        deviations = np.maximum(measured - shifted, 0.0)
    else:
        deviations = np.maximum(shifted - measured, 0.0)

    title, subtitle, statement, value_header = _labels(result)

    styles = rl["getSampleStyleSheet"]()
    ParagraphStyle = rl["ParagraphStyle"]
    title_style = ParagraphStyle(
        "iso717_title", parent=styles["Title"], fontSize=17, textColor=accent,
        spaceAfter=2, alignment=0,
    )
    subtitle_style = ParagraphStyle(
        "iso717_sub", parent=styles["Normal"], fontSize=9.5,
        textColor=colors.HexColor(_MUTED_HEX),
    )
    heading_style = ParagraphStyle(
        "iso717_h2", parent=styles["Heading2"], fontSize=11, textColor=accent,
        spaceBefore=8, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "iso717_body", parent=styles["Normal"], fontSize=9, leading=12,
    )
    # A generous leading and trailing space keep the statement line clear of
    # the following paragraph (the prototype overlapped them).
    statement_style = ParagraphStyle(
        "iso717_result", parent=styles["Normal"], fontSize=12, leading=15,
        textColor=accent, spaceBefore=2, spaceAfter=6,
    )

    Paragraph = rl["Paragraph"]
    Spacer = rl["Spacer"]
    limit_text = f"{limit:.1f}".replace(".", ",")

    flow = [
        Paragraph(title, title_style),
        Paragraph(subtitle, subtitle_style),
        Spacer(1, 6),
        Paragraph(statement, statement_style),
        Paragraph(
            f"Sum of unfavourable deviations = "
            f"{deviations.sum():.1f} dB (limit {limit_text} dB).",
            body_style,
        ),
        Spacer(1, 8),
    ]

    # Vector plot (svglib) so the curve stays crisp at any resolution.
    flow.append(_render_figure_drawing(result, 165 * mm))
    flow.append(Spacer(1, 4))

    annex = "ISO 717-2" if result.quantity == "impact" else "ISO 717-1"
    flow.append(
        Paragraph(
            f"Evaluation table ({annex} Annex C, Table C.1 layout)",
            heading_style,
        )
    )
    rows = [
        [
            "Frequency\nHz",
            value_header,
            "Reference (shifted)\ndB",
            "Unfav. deviation\ndB",
        ]
    ]
    for fk, m, r_, d in zip(centers, measured, shifted, deviations):
        rows.append(
            [
                f"{int(round(fk))}",
                f"{m:.1f}",
                f"{r_:.0f}",
                f"{d:.1f}" if d > _DEVIATION_EPS else "—",
            ]
        )
    rows.append(["", "", "sum", f"{deviations.sum():.1f}"])

    Table = rl["Table"]
    TableStyle = rl["TableStyle"]
    tbl = Table(
        rows,
        colWidths=[34 * mm, 26 * mm, 44 * mm, 40 * mm],
        repeatRows=1,
    )
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), accent),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, light]),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, accent),
                ("LINEABOVE", (0, -1), (-1, -1), 0.6, accent),
                ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
                ("TOPPADDING", (0, 0), (-1, -1), 1.6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
            ]
        )
    )
    flow.append(tbl)
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(_summary_paragraph(result, limit), body_style))

    doc_kwargs = dict(
        pagesize=rl["A4"],
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=14 * mm,
        title=title,
    )
    # invariant=1 drops the embedded timestamp for a reproducible PDF; the
    # guard tolerates reportlab builds that do not accept the keyword.
    try:
        doc = rl["SimpleDocTemplate"](path, invariant=1, **doc_kwargs)
    except TypeError:  # pragma: no cover - older reportlab
        doc = rl["SimpleDocTemplate"](path, **doc_kwargs)
    doc.build(flow)

    return str(path)
