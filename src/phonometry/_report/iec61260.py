#  Copyright (c) 2026. Jose M. Requena-Plens
"""IEC 61260-1 filter-class-compliance fiche (reportlab renderer).

Renders a
:class:`~phonometry.metrology.compliance.FilterComplianceResult` to a one-page
PDF laid out like an accredited electroacoustic type-test report:

* a title and the standard-basis line (measurement standard + the IEC 61260
  edition whose Table 1 the bank was checked against);
* an optional metadata header block (client, instrument, laboratory ...),
  rendered only for the fields supplied on the :class:`ReportMetadata`, plus a
  short caption noting the bandwidth designator and sampling rate;
* a two-panel body with a compact per-band classification table on the left
  (mid-band frequency, achieved class and the binding margin to the overall
  class) and the mask-overlay plot on the right, drawn by the result's own
  ``plot(ax=...)`` so the curve is native to the library;
* a boxed class-compliance result (``Class n - COMPLIES`` with the binding
  margin, or a non-compliance statement);
* an optional verdict row when a required class is supplied; and
* a footer identity/disclaimer block.

The quantity-independent skeleton lives in :mod:`._layout`; this module only
holds the IEC 61260 specifics. reportlab, matplotlib and svglib are soft
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
    document_styles,
    footer_flow,
    grid_table,
    metrics_table,
    render_figure_drawing,
    result_box,
    two_panel_body,
    verdict_flow,
)
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..metrology.compliance import FilterComplianceResult


def _available_classes(result: "FilterComplianceResult") -> List[int]:
    """The performance classes carried by the per-band verdict dictionaries."""
    band = result.bands[0]
    prefix, suffix = "margin_class", "_db"
    return sorted(
        int(key[len(prefix):-len(suffix)])
        for key in band
        if key.startswith(prefix) and key.endswith(suffix)
    )


def _reference_class(result: "FilterComplianceResult") -> int:
    """The class the binding margin is measured against (achieved, else loosest)."""
    if result.overall_class is not None:
        return result.overall_class
    return max(_available_classes(result))


def _binding_margin(result: "FilterComplianceResult", cls: int) -> float:
    """Smallest per-band margin to class ``cls`` (the binding margin)."""
    key = f"margin_class{cls}_db"
    return min(float(band[key]) for band in result.bands)


def _basis(metadata: ReportMetadata | None, edition: str) -> str:
    """The standard-basis line for the fiche."""
    table = (
        "IEC 61260-1:2014, Table 1"
        if edition == "2014"
        else "IEC 61260:1995 / ANSI S1.11-2004, Table 1"
    )
    measurement_standard = (
        metadata.measurement_standard if metadata is not None else None
    )
    if measurement_standard:
        return (
            f"{html.escape(measurement_standard)} type test. Conformance to "
            f"{table}."
        )
    return f"Conformance to {table}."


def _metadata_pairs(metadata: ReportMetadata) -> List[Tuple[str, str]]:
    """Build the ordered (label, value) pairs of the header grid.

    Only fields that are set are returned. A filter bank is an instrument, so
    the room/climate fields of the insulation fiche do not apply; the specimen
    field labels the tested filter or analyser.
    """
    specs: List[Tuple[str, str | None]] = [
        ("Client", metadata.client),
        ("Filter / instrument", metadata.specimen),
        ("Manufacturer", metadata.manufacturer),
        ("Test facility", metadata.test_room),
        ("Date of test", metadata.test_date),
    ]
    return [
        (label, html.escape(str(value)))
        for label, value in specs
        if value is not None
    ]


def _fraction_label(fraction: int) -> str:
    """Human bandwidth-designator label (``1/1-octave``, ``1/3-octave``, ...)."""
    return "1/1-octave" if fraction == 1 else f"1/{fraction}-octave"


def _metric_rows(result: "FilterComplianceResult") -> List[Tuple[str, str]]:
    """Per-band rows: mid-band frequency vs achieved class and binding margin."""
    cls = _reference_class(result)
    key = f"margin_class{cls}_db"
    rows: List[Tuple[str, str]] = []
    for band in result.bands:
        band_class = band["class"]
        class_text = "none" if band_class is None else f"Class {band_class}"
        margin = float(band[key])
        rows.append(
            (f"{float(band['freq']):.0f} Hz", f"{class_text} ({margin:+.2f} dB)")
        )
    return rows


def _statement(result: "FilterComplianceResult") -> str:
    """The boxed class-compliance statement with the binding margin."""
    if result.overall_class is not None:
        margin = _binding_margin(result, result.overall_class)
        return (
            f"Class <b>{result.overall_class}</b> - COMPLIES &nbsp; "
            f"(margin {margin:+.2f} dB)"
        )
    classes = "/".join(str(c) for c in _available_classes(result))
    margin = _binding_margin(result, _reference_class(result))
    return (
        f"<b>Does not comply</b> with class {classes} &nbsp; "
        f"(closest margin {margin:+.2f} dB)"
    )


def _verdict(result: "FilterComplianceResult", required_class: int) -> Tuple[str, bool]:
    """Verdict text and PASS flag against a required class.

    A bank meets a required class ``N`` when it achieves a class at least as
    strict, i.e. an overall class index of ``N`` or lower (class 0 is the
    strictest).
    """
    passed = (
        result.overall_class is not None and result.overall_class <= required_class
    )
    achieved = "none" if result.overall_class is None else str(result.overall_class)
    text = f"Achieved class {achieved}, required class {required_class}"
    return text, passed


def render_iec61260_report(
    result: "FilterComplianceResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
) -> str:
    """Render an IEC 61260-1 filter-class-compliance fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.metrology.compliance.FilterComplianceResult`
        carrying the per-band verdicts and the data to redraw the binding
        band's relative attenuation.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        prediction fiche (body + result + disclaimer, no test metadata). A
        supplied ``required_class`` drives the verdict row.
    :param verbose: Accepted for a uniform ``.report()`` signature; the
        filter-compliance fiche has a single body layout, so it has no effect.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    del verbose  # uniform signature; the fiche has one two-panel body layout
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title = "Filter class compliance"

    flow: List[Any] = [
        Paragraph(title, title_style),
        Paragraph(_basis(metadata, result.edition), basis_style),
    ]

    if metadata is not None and not metadata.is_empty():
        header_pairs = _metadata_pairs(metadata)
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(header_pairs))

    # Measurement-basis strip: the bandwidth designator and sampling rate, plus
    # the reference-attenuation convention the margins are read against.
    basis_strip_style = ParagraphStyle(
        "fiche_iec61260_basis", parent=getSampleStyleSheet()["Normal"],
        fontSize=7.5, leading=10, textColor=colors.HexColor(_MUTED_HEX),
        spaceBefore=6,
    )
    flow.append(
        Paragraph(
            f"{_fraction_label(result.fraction)} bank, sampling rate "
            f"f<sub>s</sub> = {result.fs:.0f} Hz; relative attenuation "
            "referenced to the mid-band level (IEC 61260-1 Formula 8).",
            basis_strip_style,
        )
    )
    flow.append(Spacer(1, 8))

    # Two-panel body: the per-band classification table on the left, the
    # mask-overlay plot (self-scaling dB axis) on the right.
    left_cell = [
        Paragraph("Per-band classification", caption_style),
        metrics_table(_metric_rows(result)),
    ]
    plot_drawing = render_figure_drawing(result.plot, 116 * mm, y_top=None)
    flow.append(two_panel_body(left_cell, plot_drawing))
    flow.append(Spacer(1, 8))

    flow.append(result_box(_statement(result), styles, accent))
    if metadata is not None and metadata.required_class is not None:
        text, passed = _verdict(result, metadata.required_class)
        flow.extend(verdict_flow(text, passed, styles))
    flow.extend(footer_flow(metadata))

    return build_document(path, flow, title)
