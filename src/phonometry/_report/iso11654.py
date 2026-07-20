#  Copyright (c) 2026. Jose M. Requena-Plens
"""ISO 11654 sound-absorption rating fiche (reportlab renderer).

Renders a
:class:`~phonometry.materials.absorption_rating.AbsorptionRatingResult` to a
one-page PDF laid out like an accredited absorption test report (a reverberation
room measurement per ISO 354 rated per ISO 11654):

* a title and the standard-basis line (measurement standard + ISO 11654 rating);
* an optional metadata header block (client, specimen, sample area, mounting,
  room conditions ...), rendered only for the fields supplied on the
  :class:`ReportMetadata`;
* a two-panel body with the octave-band ``alpha_p`` table on the left and the
  practical-versus-shifted-reference curve on the right, drawn by the result's
  own ``plot(ax=...)`` so the curve is native to the library;
* a boxed single-number result ``alpha_w = X (shape) dB`` with the absorption
  class and applied shift alongside;
* an optional verdict row when a minimum ``alpha_w`` requirement is supplied;
* a footer identity/disclaimer block.

With ``verbose=True`` the table adds the ISO 11654 evaluation columns (practical
coefficient, shifted reference, unfavourable deviation).

The quantity-independent skeleton lives in :mod:`._layout`; this module only
holds the ISO 11654 specifics. reportlab, matplotlib and svglib are soft
dependencies imported lazily (reportlab and svglib ship in the
``phonometry[report]`` extra, matplotlib in ``phonometry[plot]``); each is
guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any, List, Tuple

import numpy as np

from ._layout import (
    _ACCENT_HEX,
    _LIGHT_HEX,
    _REPORTLAB_HINT,
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
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..materials.absorption_rating import AbsorptionRatingResult

#: Threshold below which an unfavourable deviation is shown as an em dash.
_DEVIATION_EPS = 0.005


def _metadata_pairs(metadata: ReportMetadata) -> List[Tuple[str, str]]:
    """Build the ordered (label, value) pairs of the absorption header grid.

    Only fields that are set are returned, so empty rows never appear. The
    reverberation-room climate is reported with the single-value temperature,
    humidity and pressure fields; the insulation-only room-pair fields do not
    apply to an absorption measurement.
    """

    def num(value: float | None) -> str | None:
        return fmt_num(value) if value is not None else None

    specs: List[Tuple[str, str | None]] = [
        ("Client", metadata.client),
        ("Manufacturer", metadata.manufacturer),
        ("Description", metadata.specimen),
        ("Sample area S [m<super>2</super>]", num(metadata.area)),
        ("Mounted by", metadata.mounted_by),
        ("Mounting", metadata.mounting),
        ("Test room", metadata.test_room),
        ("Date of test", metadata.test_date),
        ("Temperature [&#176;C]", num(metadata.temperature)),
        ("Relative humidity [%]", num(metadata.relative_humidity)),
        ("Ambient pressure [kPa]", num(metadata.pressure)),
    ]
    # Values are user-supplied free text; escape XML specials so a '&' or '<'
    # cannot break reportlab's Paragraph parser. Labels carry intentional markup.
    return [
        (label, html.escape(str(value)))
        for label, value in specs
        if value is not None
    ]


def _value_table(
    centers: np.ndarray,
    measured: np.ndarray,
    shifted: np.ndarray,
    deviations: np.ndarray,
    verbose: bool,
) -> Any:
    """Build the left-hand octave-band absorption table (accredited or evaluation).

    Called only after :func:`render_iso11654_report` has imported reportlab.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle

    styles = getSampleStyleSheet()
    accent = colors.HexColor(_ACCENT_HEX)
    light = colors.HexColor(_LIGHT_HEX)

    head_style = ParagraphStyle(
        "iso11654_thead", parent=styles["Normal"], fontSize=7.2,
        textColor=colors.white, alignment=1, leading=8.5,
    )

    if verbose:
        header = [
            Paragraph("f [Hz]", head_style),
            Paragraph("Practical &#945;<sub>p</sub>", head_style),
            Paragraph("Shifted ref.", head_style),
            Paragraph("Unfav. dev.", head_style),
        ]
        col_widths = [15 * mm, 20 * mm, 17 * mm, 18 * mm]
    else:
        header = [
            Paragraph("Frequency f [Hz]", head_style),
            Paragraph("&#945;<sub>p</sub>", head_style),
        ]
        col_widths = [28 * mm, 28 * mm]

    def d2(value: float) -> str:
        # Two decimals, period separator (English fiche), matching the 0,05 grid.
        return f"{value:.2f}"

    rows: List[List[Any]] = [header]
    for fk, m, r_, d in zip(centers, measured, shifted, deviations):
        if verbose:
            rows.append(
                [
                    f"{int(round(fk))}",
                    d2(m),
                    d2(r_),
                    d2(d) if d > _DEVIATION_EPS else "—",
                ]
            )
        else:
            rows.append([f"{int(round(fk))}", d2(m)])

    n_data = len(centers)
    style_cmds: List[Any] = [
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, n_data), [colors.white, light]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, accent),
        ("TOPPADDING", (0, 0), (-1, -1), 3.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0),
        ("BOX", (0, 0), (-1, -1), 0.5, accent),
    ]
    if verbose:
        rows.append(["", "", "sum", d2(float(deviations.sum()))])
        style_cmds += [
            ("LINEABOVE", (0, -1), (-1, -1), 0.6, accent),
            ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 7.5),
        ]

    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))
    return table


def _statement(result: "AbsorptionRatingResult") -> str:
    """The boxed single-number statement ``alpha_w = X (shape)``."""
    value = f"{result.alpha_w:.2f}"
    if result.shape_indicator:
        value = f"{value} ({result.shape_indicator})"
    return f"&#945;<sub>w</sub> = <b>{value}</b>"


def _extended_terms(result: "AbsorptionRatingResult") -> List[str]:
    """The absorption class, shape indicator and applied shift shown by the box."""
    terms = [f"Absorption class: {html.escape(result.absorption_class)}"]
    if result.shape_indicator:
        terms.append(f"Shape indicator: {result.shape_indicator}")
    terms.append(f"Applied shift: {result.shift:.2f}")
    return terms


def _verdict(result: "AbsorptionRatingResult", requirement: float) -> Tuple[str, bool]:
    """Verdict text and PASS flag: absorption passes at or above the requirement."""
    passed = float(result.alpha_w) >= requirement
    text = (
        f"&#945;<sub>w</sub> = {result.alpha_w:.2f}, required &#8805; "
        f"{requirement:.2f}"
    )
    return text, passed


def render_iso11654_report(
    result: "AbsorptionRatingResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
) -> str:
    """Render an ISO 11654 absorption-rating fiche to a PDF at ``path``.

    :param result: An
        :class:`~phonometry.materials.absorption_rating.AbsorptionRatingResult`
        carrying the octave-band ``band_centers``, ``measured`` practical
        coefficients and the fitted ``shifted_reference`` curve.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        prediction fiche (body + result + disclaimer, no test metadata). A
        supplied ``requirement`` is read as the minimum ``alpha_w``.
    :param verbose: When ``True``, the left table adds the ISO 11654 evaluation
        columns (practical coefficient, shifted reference, unfavourable
        deviation); otherwise the accredited two-column ``f | alpha_p`` table.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    centers = np.asarray(result.band_centers, dtype=np.float64)
    measured = np.asarray(result.measured, dtype=np.float64)
    shifted = np.asarray(result.shifted_reference, dtype=np.float64)
    if not centers.shape == measured.shape == shifted.shape:
        raise ValueError(
            "render_iso11654_report() needs 'band_centers', 'measured' and "
            "'shifted_reference' of equal length."
        )
    # Unfavourable deviation: measured practical coefficient below the curve.
    deviations = np.maximum(shifted - measured, 0.0)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title = "Sound absorption rating"

    measurement_standard = (
        metadata.measurement_standard if metadata is not None else None
    )
    if measurement_standard:
        basis = (
            f"{html.escape(measurement_standard)} laboratory measurement of sound "
            "absorption. Rating per ISO 11654:1997."
        )
    else:
        basis = "Sound absorption rating per ISO 11654:1997."

    flow: List[Any] = [
        Paragraph(title, title_style),
        Paragraph(basis, basis_style),
    ]

    if metadata is not None and not metadata.is_empty():
        header_pairs = _metadata_pairs(metadata)
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(header_pairs))
    flow.append(Spacer(1, 8))

    value_table = _value_table(centers, measured, shifted, deviations, verbose)
    left_cell = [
        Paragraph("Octave-band &#945;<sub>p</sub>", caption_style),
        value_table,
    ]
    plot_drawing = render_figure_drawing(
        result.plot, 116 * mm, y_top=1.0, expand_step=None
    )
    flow.append(two_panel_body(left_cell, plot_drawing))
    flow.append(Spacer(1, 8))

    flow.append(result_box(_statement(result), styles, accent, _extended_terms(result)))
    if metadata is not None and metadata.requirement is not None:
        text, passed = _verdict(result, metadata.requirement)
        flow.extend(verdict_flow(text, passed, styles))
    flow.extend(footer_flow(metadata))

    return build_document(path, flow, title)
