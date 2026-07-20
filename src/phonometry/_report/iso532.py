#  Copyright (c) 2026. Jose M. Requena-Plens
"""ISO 532-1 Zwicker loudness fiche (reportlab renderer).

Renders a
:class:`~phonometry.psychoacoustics.loudness_zwicker.ZwickerLoudness` to a
one-page PDF laid out like an accredited loudness report:

* a title and the standard-basis line (measurement standard + ISO 532-1);
* an optional metadata header block (client, signal, laboratory ...), rendered
  only for the fields supplied on the :class:`ReportMetadata`;
* a two-panel body with a compact metrics table on the left (total loudness N,
  loudness level LN, and the N5/N10 percentiles for a time-varying result) and
  the specific-loudness pattern N'(z) on the right, drawn by the result's own
  ``plot(ax=...)`` so the curve is native to the library;
* a boxed single-number result ``N = X sone (LN = Y phon)``;
* an optional verdict row when a maximum-loudness requirement is supplied;
* a footer identity/disclaimer block.

This is a non-band fiche: the plot self-scales (``y_top=None``) rather than
using the fixed dB axis of the insulation fiches. The quantity-independent
skeleton lives in :mod:`._layout`; this module only holds the ISO 532-1
specifics. reportlab, matplotlib and svglib are soft dependencies imported
lazily (reportlab and svglib ship in the ``phonometry[report]`` extra,
matplotlib in ``phonometry[plot]``); each is guarded with an actionable
:class:`ImportError`.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any, List, Tuple

from ._layout import (
    _ACCENT_HEX,
    _REPORTLAB_HINT,
    build_document,
    document_styles,
    fmt_num,
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
    from ..psychoacoustics.loudness_zwicker import ZwickerLoudness


def _metadata_pairs(metadata: ReportMetadata) -> List[Tuple[str, str]]:
    """Build the ordered (label, value) pairs of the loudness header grid.

    Only fields that are set are returned. Loudness is a signal metric, so the
    room/climate fields of the insulation fiche do not apply; only the generic
    identity fields are used.
    """
    specs: List[Tuple[str, str | None]] = [
        ("Client", metadata.client),
        ("Signal", metadata.specimen),
        ("Manufacturer", metadata.manufacturer),
        ("Test room", metadata.test_room),
        ("Date of test", metadata.test_date),
    ]
    return [
        (label, html.escape(str(value)))
        for label, value in specs
        if value is not None
    ]


def _metric_rows(result: "ZwickerLoudness") -> List[Tuple[str, str]]:
    """The scalar loudness results shown in the left-hand metrics table."""
    rows = [
        ("Total loudness N [sone]", fmt_num(result.loudness)),
        ("Loudness level L<sub>N</sub> [phon]", fmt_num(result.loudness_level)),
    ]
    if result.n5 is not None:
        rows.append(("N<sub>5</sub> [sone]", fmt_num(result.n5)))
    if result.n10 is not None:
        rows.append(("N<sub>10</sub> [sone]", fmt_num(result.n10)))
    return rows


def _statement(result: "ZwickerLoudness") -> str:
    """The boxed single-number statement ``N = X sone (LN = Y phon)``."""
    return (
        f"N = <b>{result.loudness:.1f} sone</b> &nbsp; "
        f"(L<sub>N</sub> = {result.loudness_level:.1f} phon)"
    )


def _verdict(result: "ZwickerLoudness", requirement: float) -> Tuple[str, bool]:
    """Verdict text and PASS flag: loudness passes at or below the requirement.

    The requirement is read as a maximum permitted loudness in sone (a lower
    loudness is better), so the sign rule is the opposite of the airborne one.
    """
    passed = float(result.loudness) <= requirement
    text = (
        f"N = {result.loudness:.1f} sone, required &#8804; "
        f"{fmt_num(requirement)} sone"
    )
    return text, passed


def render_iso532_report(
    result: "ZwickerLoudness",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
) -> str:
    """Render an ISO 532-1 Zwicker loudness fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.psychoacoustics.loudness_zwicker.ZwickerLoudness`
        carrying the total loudness, loudness level and specific-loudness
        pattern (and the N5/N10 percentiles for a time-varying result).
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        prediction fiche (body + result + disclaimer, no test metadata). A
        supplied ``requirement`` is read as the maximum permitted loudness in
        sone.
    :param verbose: Accepted for a uniform ``.report()`` signature; the
        loudness fiche has a single body layout, so it has no effect.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    del verbose  # uniform signature; the loudness fiche has one body layout
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title = "Loudness rating"

    measurement_standard = (
        metadata.measurement_standard if metadata is not None else None
    )
    if measurement_standard:
        basis = (
            f"{html.escape(measurement_standard)} loudness. Rating per "
            "ISO 532-1:2017 (Zwicker method)."
        )
    else:
        basis = "Loudness rating per ISO 532-1:2017 (Zwicker method)."

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

    left_cell = [
        Paragraph("Loudness results", caption_style),
        metrics_table(_metric_rows(result)),
    ]
    # Non-band plot (specific loudness N' over Bark): self-scaling axis.
    plot_drawing = render_figure_drawing(result.plot, 116 * mm, y_top=None)
    flow.append(two_panel_body(left_cell, plot_drawing))
    flow.append(Spacer(1, 8))

    flow.append(result_box(_statement(result), styles, accent))
    if metadata is not None and metadata.requirement is not None:
        text, passed = _verdict(result, metadata.requirement)
        flow.extend(verdict_flow(text, passed, styles))
    flow.extend(footer_flow(metadata))

    return build_document(path, flow, title)
