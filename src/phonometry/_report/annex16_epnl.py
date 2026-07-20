#  Copyright (c) 2026. Jose M. Requena-Plens
"""ICAO Annex 16 EPNL aircraft-noise-certification fiche (reportlab renderer).

Renders an :class:`~phonometry.aircraft.aircraft_noise.EPNLResult` to a
one-page PDF laid out like an aircraft-noise-certification data sheet:

* a title and the standard-basis line (measurement standard + ICAO Annex 16
  Vol. I Appendix 2);
* an optional TCDSN-style metadata header block (aircraft, manufacturer / type
  certificate holder, applicant, measurement point ...), rendered only for the
  fields supplied on the :class:`ReportMetadata`;
* a compact metrics table of the informational intermediate quantities (the
  peak PNLTM, the duration correction ``D``, the 10 dB-down record window and,
  when it is non-zero, the bandsharing adjustment);
* a full-width, landscape PNLT-versus-time plot drawn by the result's own
  ``plot(ax=...)`` (the PNL and PNLT traces, the marked PNLTM and the shaded
  10 dB-down integration window);
* a boxed single-number result ``EPNL = X EPNdB``;
* a Level | Limit | Margin verdict row when a certification limit is supplied
  (``metadata.requirement``); the EPNL passes at or below it;
* a static reference-conditions strip (25 C, 70 % RH, sea level, zero wind,
  ISA); and
* a footer identity/disclaimer block, plus a line stating the fiche is a
  computational result and not an official State noise certificate.

Like :mod:`.broadcast` this uses a stacked layout rather than the narrow
two-panel one: the PNLT-versus-time trace is landscape and reads best full
width. The quantity-independent skeleton lives in :mod:`._layout`; this module
only holds the Annex 16 specifics. reportlab, matplotlib and svglib are soft
dependencies imported lazily (reportlab and svglib ship in the
``phonometry[report]`` extra, matplotlib in ``phonometry[plot]``); each is
guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any, List, Tuple

from ._layout import (
    _ACCENT_HEX,
    _MUTED_HEX,
    _REPORTLAB_HINT,
    build_document,
    compliance_table,
    document_styles,
    fmt_num,
    footer_flow,
    grid_table,
    metrics_table,
    render_figure_drawing,
    result_box,
)
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..aircraft.aircraft_noise import EPNLResult

#: Static reference atmosphere of ICAO Annex 16 Vol. I Appendix 2 (the
#: conditions the certification EPNL is referred to). This is an informational
#: strip, never a claim of measured atmospherics.
_REFERENCE_CONDITIONS = (
    "Reference conditions: 25 &#176;C, 70% relative humidity, sea level, zero "
    "wind, ISA (ICAO Annex 16 Vol I App. 2)."
)

#: Footer note distinguishing the computational result from a State certificate.
_CERTIFICATE_DISCLAIMER = (
    "This is a computational EPNL result per ICAO Annex 16 Vol I Appendix 2; it "
    "is not an official State noise certificate (e.g. EASA Form 45)."
)


def _metadata_pairs(metadata: ReportMetadata) -> List[Tuple[str, str]]:
    """Build the ordered (label, value) pairs of the certification header grid.

    Only fields that are set are returned. EPNL is an aircraft-flyover metric,
    so the room/climate fields of the insulation fiche do not apply; the
    generic identity fields are relabelled to the certification vocabulary
    (aircraft, type-certificate holder, applicant, measurement point).
    """
    specs: List[Tuple[str, str | None]] = [
        ("Aircraft", metadata.specimen),
        ("Manufacturer / TC holder", metadata.manufacturer),
        ("Applicant", metadata.client),
        ("Measurement point", metadata.test_room),
        ("Date of test", metadata.test_date),
    ]
    return [
        (label, html.escape(str(value)))
        for label, value in specs
        if value is not None
    ]


def _metric_rows(result: "EPNLResult") -> List[Tuple[str, str]]:
    """The intermediate EPNL quantities shown in the left-hand metrics table.

    These are informational: PNLTM, the duration correction ``D``, the 10
    dB-down integration window (records, 1-based for display) and, only when it
    is non-zero, the bandsharing adjustment.
    """
    k_first, k_last = result.band_limits
    rows = [
        ("PNLTM [PNdB]", fmt_num(result.pnltm)),
        ("Duration correction D [dB]", fmt_num(result.duration_correction)),
        ("10 dB-down window (records)", f"{k_first + 1}&#8211;{k_last + 1}"),
    ]
    if result.bandsharing_adjustment != 0.0:
        rows.append(
            ("Bandsharing adjustment [dB]", fmt_num(result.bandsharing_adjustment))
        )
    return rows


def _statement(result: "EPNLResult") -> str:
    """The boxed single-number statement ``EPNL = X EPNdB``."""
    return f"EPNL = <b>{result.epnl:.1f} EPNdB</b>"


def _verdict_rows(result: "EPNLResult", limit: float) -> List[Tuple[str, str, str, str]]:
    """The Level | Limit | Margin compliance row for a supplied EPNL limit.

    The EPNL passes at or below the certification limit; the limit cell also
    carries the signed margin ``limit - EPNL`` (positive when compliant).
    """
    margin = limit - float(result.epnl)
    status = "pass" if float(result.epnl) <= limit else "fail"
    return [
        (
            "EPNL [EPNdB]",
            f"{result.epnl:.1f}",
            f"&#8804; {fmt_num(limit)} (margin {margin:+.1f})",
            status,
        )
    ]


def render_annex16_epnl_report(
    result: "EPNLResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
) -> str:
    """Render an ICAO Annex 16 EPNL certification fiche to a PDF at ``path``.

    :param result: An
        :class:`~phonometry.aircraft.aircraft_noise.EPNLResult` carrying the
        PNL/PNLT time histories, the peak PNLTM, the duration correction, the
        bandsharing adjustment, the EPNL and the 10 dB-down window.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        prediction fiche (metrics + plot + result, no header and no verdict). A
        supplied ``requirement`` is read as the certification EPNL limit in
        EPNdB (the EPNL passes at or below it).
    :param verbose: Accepted for a uniform ``.report()`` signature; the EPNL
        fiche has a single stacked body layout, so it has no effect.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    del verbose  # uniform signature; the fiche has one stacked body layout
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title = "Aircraft noise certification - EPNL result"

    measurement_standard = (
        metadata.measurement_standard if metadata is not None else None
    )
    if measurement_standard:
        basis = (
            f"{html.escape(measurement_standard)}. Effective Perceived Noise "
            "Level per ICAO Annex 16, Volume I, Appendix 2."
        )
    else:
        basis = (
            "Effective Perceived Noise Level (EPNL) per ICAO Annex 16, "
            "Volume I, Appendix 2."
        )

    muted_strip_style = ParagraphStyle(
        "fiche_reference_conditions", parent=getSampleStyleSheet()["Normal"],
        fontSize=7.5, leading=10, textColor=colors.HexColor(_MUTED_HEX),
        spaceBefore=2,
    )

    flow: List[Any] = [
        Paragraph(title, title_style),
        Paragraph(basis, basis_style),
    ]

    if metadata is not None and not metadata.is_empty():
        header_pairs = _metadata_pairs(metadata)
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(header_pairs))
    flow.append(Paragraph(_REFERENCE_CONDITIONS, muted_strip_style))
    flow.append(Spacer(1, 8))

    flow.append(Paragraph("Intermediate quantities", caption_style))
    flow.append(metrics_table(_metric_rows(result), col_widths=[48 * mm, 26 * mm]))
    flow.append(Spacer(1, 8))

    # Full-width, landscape PNLT-vs-time plot (self-scaling axis).
    plot_drawing = render_figure_drawing(
        result.plot, 174 * mm, y_top=None, figsize=(9.2, 4.2)
    )
    flow.append(plot_drawing)
    flow.append(Spacer(1, 8))

    flow.append(result_box(_statement(result), styles, accent))

    limit = (
        float(metadata.requirement)
        if metadata is not None and metadata.requirement is not None
        else None
    )
    if limit is not None:
        flow.append(Spacer(1, 6))
        flow.append(Paragraph("Certification limit", caption_style))
        flow.append(compliance_table(_verdict_rows(result, limit)))

    flow.extend(footer_flow(metadata))

    disclaimer_style = ParagraphStyle(
        "fiche_certificate_disclaimer", parent=getSampleStyleSheet()["Normal"],
        fontSize=7.5, leading=10, textColor=colors.HexColor(_MUTED_HEX),
        spaceBefore=2,
    )
    flow.append(Paragraph(_CERTIFICATE_DISCLAIMER, disclaimer_style))

    return build_document(path, flow, title)
