#  Copyright (c) 2026. Jose M. Requena-Plens
"""Shared reportlab building blocks for the accredited report fiches.

The per-standard renderers (:mod:`.iso717`, :mod:`.iso11654`, ...) all lay out
the same accredited-laboratory skeleton: a title and standard-basis line, an
optional metadata header grid, a two-panel body (value table beside the
result's own vector plot), a boxed single-number result, an optional verdict
row and a footer identity/disclaimer block. This module holds the pieces that
do not depend on the rated quantity, so each renderer only writes the parts
that are genuinely specific (the labels, the value table and the verdict rule).

reportlab, matplotlib and svglib are soft dependencies imported lazily by the
helpers that need them (reportlab and svglib ship in the ``phonometry[report]``
extra, matplotlib in ``phonometry[plot]``); each raises an actionable
:class:`ImportError`.
"""

from __future__ import annotations

import html
import os
import tempfile
from typing import Any, Callable, List, Tuple

import numpy as np

from ._i18n import format_number, t
from .metadata import ReportMetadata

#: Installation hints for the three soft dependencies of the report.
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
#: matching the validated accredited fiche prototype.
_ACCENT_HEX = "#1f4e79"
_LIGHT_HEX = "#eef2f7"
_MUTED_HEX = "#555555"
_VERDICT_OK_HEX = "#1b6e2f"
_VERDICT_BAD_HEX = "#a11a1a"


def fmt_num(value: float, language: str = "en") -> str:
    """Format a number with up to one decimal, dropping a trailing ``.0``.

    Delegates to :func:`phonometry._i18n.format_number`, so English keeps a
    period (matching accredited English lab reports such as the Salford
    reference) and ``language="es"`` uses a comma, as Spanish reports write
    numbers.
    """
    return format_number(value, language, decimals=1, trim=True)


def render_figure_drawing(
    plot_fn: Callable[..., Any],
    target_width: float,
    *,
    y_top: float | None,
    expand_step: float | None = None,
    figsize: Tuple[float, float] | None = None,
    language: str = "en",
) -> Any:
    """Draw a result's plot as a scaled, vector reportlab ``Drawing``.

    ``plot_fn`` is the result's own ``plot`` method; it is called with a fresh
    ``ax`` so the figure is native to the library. The plot is saved to SVG
    with the text rasterised to vector paths (``svg.fonttype='path'``) and
    converted with svglib, so it stays crisp at any zoom/print resolution.

    :param target_width: Target width in points.
    :param y_top: Fixed top of the 0-based y-axis (accredited reports keep a
        fixed axis so band fiches are visually comparable); pass ``None`` to
        leave the plot's own axis untouched (for non-band plots such as a
        specific-loudness pattern or a level-vs-time trace that self-scale).
    :param expand_step: When given, the top is raised to the next multiple of
        this step if the data exceeds ``y_top`` (used for dB axes); ``None``
        keeps ``y_top`` exactly (used for a 0..1 coefficient axis). Ignored
        when ``y_top`` is ``None``.
    :param figsize: Matplotlib figure size ``(width, height)`` in inches;
        ``None`` keeps the default portrait ``(5.8, 6.4)``. A landscape size
        (e.g. a wide, short time plot) is passed for a stacked full-width
        figure.
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
        fig = Figure(figsize=figsize if figsize is not None else (5.8, 6.4))
        FigureCanvasAgg(fig)
        ax = fig.subplots()
        plot_fn(ax=ax)
        # The fiche states the rating in the boxed result, so the plot's own
        # title would only duplicate it at a large size.
        ax.set_title("")
        # A fixed 0-based axis keeps band fiches comparable; y_top=None leaves
        # a self-scaling plot (specific loudness, level-vs-time) as its own.
        if y_top is not None:
            top = y_top
            if expand_step is not None:
                _, data_top = ax.get_ylim()
                top = max(top, float(np.ceil(data_top / expand_step) * expand_step))
            ax.set_ylim(0.0, top)
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
        # Localise the tick-label decimal separator for Spanish (a no-op for
        # English, so English figures are byte-for-byte unchanged). Imported
        # lazily like the matplotlib backend above.
        from .._i18n import localize_axes

        localize_axes(ax, language)
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


def grid_table(pairs: List[Tuple[str, str]]) -> Any:
    """Lay an ordered list of (label, value) pairs into a two-column grid.

    Each grid row holds up to two label/value pairs (four table cells:
    ``label | value | label | value``); a trailing single pair is padded.
    Called only after the renderer has imported reportlab.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle

    styles = getSampleStyleSheet()
    accent = colors.HexColor(_ACCENT_HEX)
    label_style = ParagraphStyle(
        "fiche_meta_label", parent=styles["Normal"], fontSize=8,
        textColor=colors.HexColor(_MUTED_HEX),
    )
    value_style = ParagraphStyle(
        "fiche_meta_value", parent=styles["Normal"], fontSize=8.5,
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
    table = Table(rows, colWidths=[36 * mm, 51 * mm, 36 * mm, 51 * mm])
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


def document_styles(accent: Any) -> Tuple[Any, Any, Any, Any]:
    """Return ``(stylesheet, title_style, basis_style, caption_style)``.

    The title (accent, 16 pt), the standard-basis line (muted, 9.5 pt) and the
    left-panel caption (accent, 8 pt) are identical across every fiche, so they
    are built once here. The base stylesheet is returned too, as the result box
    and verdict helpers take it. Called only after the renderer has imported
    reportlab.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "fiche_title", parent=styles["Title"], fontSize=16, textColor=accent,
        spaceAfter=1, alignment=0,
    )
    basis_style = ParagraphStyle(
        "fiche_basis", parent=styles["Normal"], fontSize=9.5,
        textColor=colors.HexColor(_MUTED_HEX), spaceAfter=2,
    )
    caption_style = ParagraphStyle(
        "fiche_caption", parent=styles["Normal"], fontSize=8,
        textColor=accent, spaceAfter=3,
    )
    return styles, title_style, basis_style, caption_style


def two_panel_body(left_cell: Any, plot_drawing: Any) -> Any:
    """Assemble the two-panel body: a left cell (~56 mm) beside the plot.

    Every fiche puts a table or metrics list on the left and the result's own
    vector plot on the right; the column widths and cell alignment are shared.
    Called only after the renderer has imported reportlab.
    """
    from reportlab.lib.units import mm
    from reportlab.platypus import Table, TableStyle

    body = Table([[left_cell, plot_drawing]], colWidths=[56 * mm, 118 * mm])
    body.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (-1, 0), (-1, 0), 0),
            ]
        )
    )
    return body


def metrics_table(rows: List[Tuple[str, str]], *, col_widths: Any = None) -> Any:
    """A compact two-column ``metric | value`` table for a non-band fiche.

    The band fiches put a frequency table on the left; the single-metric fiches
    (loudness, EPNL, programme loudness ...) put a short list of scalar results
    there instead. Same accredited styling (accent header rule, zebra rows).
    Called only after the renderer has imported reportlab.

    :param rows: Ordered ``(label, value)`` pairs; labels may carry markup.
    :param col_widths: Optional explicit column widths; defaults to 34/22 mm.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle

    styles = getSampleStyleSheet()
    accent = colors.HexColor(_ACCENT_HEX)
    light = colors.HexColor(_LIGHT_HEX)
    label_style = ParagraphStyle(
        "fiche_metric_label", parent=styles["Normal"], fontSize=8.5, leading=11,
    )
    value_style = ParagraphStyle(
        "fiche_metric_value", parent=styles["Normal"], fontSize=8.5, leading=11,
        alignment=2,
    )
    data = [
        [Paragraph(label, label_style), Paragraph(value, value_style)]
        for label, value in rows
    ]
    table = Table(data, colWidths=col_widths or [34 * mm, 22 * mm])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, light]),
                ("LINEABOVE", (0, 0), (-1, 0), 0.6, accent),
                ("LINEBELOW", (0, -1), (-1, -1), 0.6, accent),
                ("TOPPADDING", (0, 0), (-1, -1), 3.0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def compliance_table(
    rows: List[Tuple[str, str, str, str]],
    *,
    col_widths: Any = None,
    language: str = "en",
) -> Any:
    """A full-width 4-column ``metric | measured | target/limit | result`` table.

    The stacked-layout fiches (programme loudness, aircraft noise ...) check a
    result against several limits at once, so they need a wider compliance
    table than the two-column :func:`metrics_table`. Each row is a
    ``(metric_label, measured, limit, status)`` tuple where ``status`` is one
    of ``"pass"``, ``"fail"`` or ``"info"``: a pass renders a filled dot and
    ``PASS`` in green, a fail a dot and ``FAIL`` in red, and an informational
    row an en dash in muted grey (never green/red, as it carries no verdict).
    Same accredited styling as :func:`metrics_table` (accent header row, zebra
    body rows, thin box). Called only after the renderer has imported reportlab.

    :param rows: Ordered ``(metric, measured, limit, status)`` tuples; the
        metric/measured/limit strings may carry markup (they are formatted
        numbers, not user text).
    :param col_widths: Optional explicit column widths; defaults to
        ``[64, 36, 50, 24]`` mm (summing to the 174 mm content width).
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle

    styles = getSampleStyleSheet()
    accent = colors.HexColor(_ACCENT_HEX)
    light = colors.HexColor(_LIGHT_HEX)
    header_style = ParagraphStyle(
        "fiche_compliance_header", parent=styles["Normal"], fontSize=8.5,
        leading=11, textColor=colors.white,
    )
    cell_style = ParagraphStyle(
        "fiche_compliance_cell", parent=styles["Normal"], fontSize=8.5,
        leading=11,
    )
    result_style = ParagraphStyle(
        "fiche_compliance_result", parent=styles["Normal"], fontSize=8.5,
        leading=11,
    )

    def _result_markup(status: str) -> str:
        if status == "pass":
            return (
                f"<font color='{_VERDICT_OK_HEX}'>&#9679; "
                f"{t('PASS', language)}</font>"
            )
        if status == "fail":
            return (
                f"<font color='{_VERDICT_BAD_HEX}'>&#9679; "
                f"{t('FAIL', language)}</font>"
            )
        return f"<font color='{_MUTED_HEX}'>&#8211;</font>"

    data: List[List[Any]] = [
        [
            Paragraph(t("Metric", language), header_style),
            Paragraph(t("Measured", language), header_style),
            Paragraph(t("Target / Limit", language), header_style),
            Paragraph(t("Result", language), header_style),
        ]
    ]
    for metric, measured, limit, status in rows:
        data.append(
            [
                Paragraph(metric, cell_style),
                Paragraph(measured, cell_style),
                Paragraph(limit, cell_style),
                Paragraph(_result_markup(status), result_style),
            ]
        )
    table = Table(data, colWidths=col_widths or [64 * mm, 36 * mm, 50 * mm, 24 * mm])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, 0), accent),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light]),
                ("LINEABOVE", (0, 0), (-1, 0), 0.6, accent),
                ("LINEBELOW", (0, -1), (-1, -1), 0.6, accent),
                ("TOPPADDING", (0, 0), (-1, -1), 3.0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def result_box(
    statement: str,
    styles: Any,
    accent: Any,
    extended: List[str] | None = None,
) -> Any:
    """The boxed single-number result, with optional extended terms alongside.

    Called only after the renderer has imported reportlab.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle

    result_style = ParagraphStyle(
        "fiche_result", parent=styles["Normal"], fontSize=13, leading=17,
        textColor=accent,
    )
    box_cells: List[Any] = [Paragraph(statement, result_style)]
    box_widths = [174 * mm]
    if extended:
        ext_style = ParagraphStyle(
            "fiche_ext", parent=styles["Normal"], fontSize=8.5, leading=12,
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


def verdict_flow(
    text: str, passed: bool, styles: Any, language: str = "en"
) -> List[Any]:
    """The PASS/FAIL verdict paragraph for a precomputed comparison.

    Each renderer computes ``text`` (the requirement comparison) and ``passed``
    with its own sign rule; this only renders the shared badge styling.
    Called only after the renderer has imported reportlab.
    """
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph

    badge = t("PASS", language) if passed else t("FAIL", language)
    badge_hex = _VERDICT_OK_HEX if passed else _VERDICT_BAD_HEX
    verdict_style = ParagraphStyle(
        "fiche_verdict", parent=styles["Normal"], fontSize=10, leading=14,
        spaceBefore=4,
    )
    lead = t("Result vs requirement", language)
    return [
        Paragraph(
            f"{lead}: {text} &#8594; "
            f"<b><font color='{badge_hex}'>{badge}</font></b>",
            verdict_style,
        )
    ]


def footer_flow(
    metadata: ReportMetadata | None, language: str = "en"
) -> List[Any]:
    """Build the footer identity block plus the always-present disclaimer.

    Called only after the renderer has imported reportlab.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, Spacer

    styles = getSampleStyleSheet()
    muted = colors.HexColor(_MUTED_HEX)

    ident_style = ParagraphStyle(
        "fiche_footer", parent=styles["Normal"], fontSize=8.5, leading=12,
    )
    sign_style = ParagraphStyle(
        "fiche_sign", parent=styles["Normal"], fontSize=8.5, leading=16,
    )
    disclaimer_style = ParagraphStyle(
        "fiche_disclaimer", parent=styles["Normal"], fontSize=8,
        textColor=muted, leading=11,
    )

    signature = t("Signature", language)
    sign_blank = f"{signature}: ______________________________"

    flow: List[Any] = [Spacer(1, 8)]
    lines: List[str] = []
    if metadata is not None:
        if metadata.laboratory:
            lines.append(
                f"<b>{t('Laboratory', language)}:</b> "
                f"{html.escape(metadata.laboratory)}"
            )
        if metadata.report_id:
            lines.append(
                f"<b>{t('Report no.', language)}:</b> "
                f"{html.escape(metadata.report_id)}"
            )
        if metadata.test_date:
            lines.append(
                f"<b>{t('Date', language)}:</b> "
                f"{html.escape(metadata.test_date)}"
            )
        if metadata.notes:
            lines.append(
                f"<b>{t('Notes', language)}:</b> "
                f"{html.escape(metadata.notes)}"
            )
    for line in lines:
        flow.append(Paragraph(line, ident_style))

    operator = metadata.operator if metadata is not None else None
    if operator:
        flow.append(
            Paragraph(
                f"{t('Operator', language)}: {html.escape(operator)} "
                f"&nbsp;&nbsp; {sign_blank}",
                sign_style,
            )
        )
    elif lines:
        flow.append(Paragraph(sign_blank, sign_style))

    flow.append(Spacer(1, 4))
    flow.append(
        Paragraph(
            f"<font color='{_ACCENT_HEX}'>&#9632;</font> "
            f"{t('The results relate only to the tested specimen.', language)}",
            disclaimer_style,
        )
    )
    flow.append(
        Paragraph(
            f"<font size=7 color='#888888'>"
            f"{t('Generated by phonometry.', language)}</font>",
            disclaimer_style,
        )
    )
    return flow


def build_document(path: str, flow: List[Any], title: str) -> str:
    """Build the one-page A4 fiche ``flow`` into a reproducible PDF at ``path``.

    Called only after the renderer has imported reportlab.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate

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
