#  Copyright (c) 2026. Jose M. Requena-Plens
"""Room-noise rating fiche (reportlab renderer, ANSI/ASA S12.2-2019).

Renders the two room-noise ratings of ANSI/ASA S12.2-2019 to a one-page PDF
laid out like a room-noise assessment report:

* a :class:`~phonometry.room.room_noise.NCResult` (Noise Criteria, Table 1,
  tangency method): the NC rating and the governing octave band; and
* a :class:`~phonometry.room.room_noise.RCResult` (Room Criteria Mark II,
  Annex D): the RC rating and its spectral-quality tag (neutral / rumble /
  hiss).

Both fiches share the same skeleton:

* a title and the standard-basis line (measurement standard + the ANSI/ASA
  S12.2-2019 rating method);
* an optional metadata header block (client, room, description, room volume,
  floor area, instrumentation, climate ...), rendered only for the fields
  supplied on the :class:`ReportMetadata`;
* a two-panel body with the measured octave-band levels on the left and the
  measured spectrum against the NC/RC curve family on the right, drawn by the
  result's own ``plot(ax=...)`` so the curve is native to the library;
* a boxed single-number rating (``NC-nn`` with the governing band, or
  ``RC-nn(tag)`` with the mid-frequency average and the spectral quality);
* an optional verdict row when a target rating is supplied (a lower rating is
  better, so the room passes at or below the target);
* a footer identity/disclaimer block.

With ``verbose=True`` the left table gains the evaluation columns: the per-band
NC contour value that the tangency method reads (NC fiche), or the reference
RC Mark II curve and the measured deviation from it (RC fiche).

The quantity-independent skeleton lives in :mod:`._layout`; this module only
holds the ANSI/ASA S12.2 specifics. reportlab, matplotlib and svglib are soft
dependencies imported lazily (reportlab and svglib ship in the
``phonometry[report]`` extra, matplotlib in ``phonometry[plot]``); each is
guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

import html
import math
from typing import TYPE_CHECKING, Any, List, Tuple

import numpy as np

from ._i18n import format_number, t
from ._layout import (
    _ACCENT_HEX,
    _LIGHT_HEX,
    _REPORTLAB_HINT,
    build_document,
    document_styles,
    escaped_pairs,
    fmt_meta,
    footer_flow,
    grid_table,
    render_figure_drawing,
    result_box,
    two_panel_body,
    verdict_flow,
)
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..room.room_noise import NCResult, RCResult

#: Shared title for both room-noise rating fiches.
_TITLE = "Room noise rating"


def _thead_style() -> Any:
    """The shared white-on-accent table-header paragraph style (7.4 pt)."""
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    return ParagraphStyle(
        "ansis122_thead",
        parent=getSampleStyleSheet()["Normal"],
        fontSize=7.4,
        textColor=colors.white,
        alignment=1,
        leading=8.6,
    )


def _metadata_pairs(
    metadata: ReportMetadata, language: str = "en"
) -> List[Tuple[str, str]]:
    """Build the ordered (label, value) pairs of the room-noise header grid.

    Only fields that are set are returned, so empty rows never appear. A
    room-noise assessment characterises a single enclosure, so the single-room
    ``room_volume`` and floor ``area`` fields are used rather than the
    source/receiving transmission pair.
    """

    def num(value: float | None) -> str | None:
        return fmt_meta(value, language) if value is not None else None

    specs: List[Tuple[str, str | None]] = [
        (t("Client", language), metadata.client),
        (t("Room", language), metadata.test_room),
        (t("Description", language), metadata.specimen),
        (t("Room volume V [m<super>3</super>]", language), num(metadata.room_volume)),
        (t("Floor area S [m<super>2</super>]", language), num(metadata.area)),
        (t("Instrumentation", language), metadata.instrumentation),
        (t("Temperature [&#176;C]", language), num(metadata.temperature)),
        (t("Relative humidity [%]", language), num(metadata.relative_humidity)),
        (t("Ambient pressure [kPa]", language), num(metadata.pressure)),
        (t("Date of test", language), metadata.test_date),
    ]
    return escaped_pairs(specs)


def _band_labels() -> List[str]:
    """Nominal octave-band labels (16 ... 8000 Hz), aligned with the levels."""
    from ..room.room_noise import OCTAVE_BANDS

    return [f"{f:g}" for f in np.asarray(OCTAVE_BANDS, dtype=np.float64)]


def _level_cell(level: float, language: str, decimals: int = 1) -> str:
    """One octave-band level cell, or an em dash when the band is absent."""
    if not math.isfinite(level):
        return "—"
    return format_number(float(level), language, decimals=decimals)


def _value_table(
    columns: List[Tuple[str, List[str]]],
    col_widths: List[Any],
    language: str = "en",
) -> Any:
    """Assemble the left-hand octave-band table with the accredited styling.

    ``columns`` is an ordered list of ``(header_markup, cell_strings)`` pairs;
    every cell list has one entry per octave band. Accent header row with a
    rule below it, zebra body striping, centred cells and the light box, the
    look shared with the other fiches. Called only after the renderer has
    imported reportlab.
    """
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle

    accent = colors.HexColor(_ACCENT_HEX)
    light = colors.HexColor(_LIGHT_HEX)
    head = _thead_style()

    n_data = len(columns[0][1])
    rows: List[List[Any]] = [[Paragraph(header, head) for header, _ in columns]]
    for i in range(n_data):
        rows.append([cells[i] for _, cells in columns])

    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), accent),
                ("FONTSIZE", (0, 1), (-1, -1), 7.6),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light]),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, accent),
                ("TOPPADDING", (0, 0), (-1, -1), 2.4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
                ("BOX", (0, 0), (-1, -1), 0.5, accent),
            ]
        )
    )
    return table


def _nc_contour_column(levels: np.ndarray, language: str) -> List[str]:
    """Per-band NC contour value read by the tangency method (verbose NC).

    For each band the NC index whose Table 1 curve passes through the measured
    level is found by interpolation, exactly as
    :func:`~phonometry.room.room_noise.noise_criterion` does; the rating is the
    maximum of these values. A band with no measured level shows an em dash.
    """
    from ..room.room_noise import NC_CURVES, NC_INDICES

    cells: List[str] = []
    for k, level in enumerate(levels):
        if not math.isfinite(level):
            cells.append("—")
            continue
        contour = float(
            np.interp(
                level,
                NC_CURVES[:, k],
                NC_INDICES,
                left=float(NC_INDICES[0]) - 1.0,
                right=float(NC_INDICES[-1]) + 1.0,
            )
        )
        cells.append(format_number(contour, language, decimals=1))
    return cells


def _nc_left_cell(
    result: "NCResult", verbose: bool, caption_style: Any, language: str
) -> Tuple[List[Any], List[Any]]:
    """The NC fiche left cell (caption + table) and its two-panel column widths."""
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph

    labels = _band_labels()
    levels = np.asarray(result.levels, dtype=np.float64)
    level_cells = [_level_cell(v, language) for v in levels]

    columns: List[Tuple[str, List[str]]] = [
        (t("Frequency f [Hz]", language), labels),
        ("L<sub>p</sub> [dB]", level_cells),
    ]
    if verbose:
        columns.append(("NC", _nc_contour_column(levels, language)))
        col_widths = [17 * mm, 18 * mm, 17 * mm]
        left_width, plot_width = 56.0, 118.0
    else:
        col_widths = [22 * mm, 22 * mm]
        left_width, plot_width = 50.0, 124.0

    caption = t("Octave-band sound pressure levels", language)
    left_cell = [
        Paragraph(caption, caption_style),
        _value_table(columns, col_widths, language),
    ]
    return left_cell, [left_width, plot_width]


def _rc_left_cell(
    result: "RCResult", verbose: bool, caption_style: Any, language: str
) -> Tuple[List[Any], List[Any]]:
    """The RC fiche left cell (caption + table) and its two-panel column widths."""
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph

    labels = _band_labels()
    levels = np.asarray(result.levels, dtype=np.float64)
    reference = np.asarray(result.reference_curve, dtype=np.float64)
    level_cells = [_level_cell(v, language) for v in levels]

    columns: List[Tuple[str, List[str]]] = [
        (t("Frequency f [Hz]", language), labels),
        ("L<sub>p</sub> [dB]", level_cells),
    ]
    if verbose:
        ref_cells = [_level_cell(v, language, decimals=0) for v in reference]
        dev_cells = [
            _level_cell(lvl - ref, language) for lvl, ref in zip(levels, reference)
        ]
        columns.append((t("Ref. [dB]", language), ref_cells))
        columns.append((t("Dev. [dB]", language), dev_cells))
        col_widths = [13 * mm, 15 * mm, 15 * mm, 15 * mm]
        left_width, plot_width = 62.0, 112.0
    else:
        col_widths = [22 * mm, 22 * mm]
        left_width, plot_width = 50.0, 124.0

    caption = t("Octave-band sound pressure levels", language)
    left_cell = [
        Paragraph(caption, caption_style),
        _value_table(columns, col_widths, language),
    ]
    return left_cell, [left_width, plot_width]


def _rating_label(value: float) -> str:
    """Format a rating value as an integer when whole, else one decimal."""
    rounded = round(value, 1)
    return f"{int(rounded)}" if float(rounded).is_integer() else f"{rounded:g}"


def _nc_statement_terms(result: "NCResult", language: str) -> Tuple[str, List[str]]:
    """The boxed ``NC-nn`` statement and the governing-band extended term."""
    value = _rating_label(float(result.rating))
    statement = f"NC-<b>{value}</b>"
    extended = [
        t("Governing band: {value} Hz", language).format(
            value=f"{float(result.governing_frequency):g}"
        ),
        t("Rated by the tangency method (ANSI/ASA S12.2-2019).", language),
    ]
    return statement, extended


#: Spectral-quality descriptor for each RC Mark II tag (clause D.3).
_RC_QUALITY = {
    "N": "neutral",
    "R": "rumble",
    "H": "hiss",
    "RH": "rumble and hiss",
}


def _rc_statement_terms(result: "RCResult", language: str) -> Tuple[str, List[str]]:
    """The boxed ``RC-nn(tag)`` statement and its RC extended terms."""
    statement = f"RC-<b>{result.rating}</b>({result.classification})"
    quality = _RC_QUALITY.get(result.classification, "neutral")
    extended = [
        t("Mid-frequency average L<sub>MF</sub> = {value} dB", language).format(
            value=format_number(result.lmf, language, decimals=1)
        ),
        t("Spectral quality: {value}", language).format(value=t(quality, language)),
    ]
    return statement, extended


def _verdict(
    symbol: str, rating: float, requirement: float, language: str
) -> Tuple[str, bool]:
    """Verdict text and PASS flag: a room-noise rating passes at or below target.

    A lower NC or RC rating is quieter, so the room complies when its rating is
    at or below the supplied target.
    """
    passed = float(rating) <= requirement
    text = t("{symbol} {value}, required &#8804; {req}", language).format(
        symbol=symbol,
        value=_rating_label(float(rating)),
        req=format_number(requirement, language, decimals=0),
    )
    return text, passed


def _render_room_noise(
    result: "NCResult | RCResult",
    path: str,
    *,
    basis_template: str,
    left_builder: Any,
    statement_builder: Any,
    symbol: str,
    metadata: ReportMetadata | None,
    verbose: bool,
    language: str,
) -> str:
    """Render a room-noise rating fiche, shared by the NC and RC renderers."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title = t(_TITLE, language)

    measurement_standard = (
        metadata.measurement_standard if metadata is not None else None
    )
    if measurement_standard:
        basis = t(
            "{standard} octave-band measurement of room noise. " + basis_template,
            language,
        ).format(standard=html.escape(measurement_standard))
    else:
        basis = t(basis_template, language)

    flow: List[Any] = [
        Paragraph(title, title_style),
        Paragraph(basis, basis_style),
    ]

    if metadata is not None and not metadata.is_empty():
        header_pairs = _metadata_pairs(metadata, language)
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(header_pairs))
    flow.append(Spacer(1, 8))

    left_cell, (left_width, plot_width) = left_builder(
        result, verbose, caption_style, language
    )
    plot_drawing = render_figure_drawing(
        result.plot, (plot_width - 2.0) * mm, y_top=None, language=language
    )
    flow.append(
        two_panel_body(
            left_cell,
            plot_drawing,
            left_width_mm=left_width,
            plot_width_mm=plot_width,
        )
    )
    flow.append(Spacer(1, 8))

    statement, extended = statement_builder(result, language)
    flow.append(result_box(statement, styles, accent, extended))

    if metadata is not None and metadata.requirement is not None:
        text, passed = _verdict(
            symbol, float(result.rating), metadata.requirement, language
        )
        flow.extend(verdict_flow(text, passed, styles, language))
    flow.extend(footer_flow(metadata, language))

    return build_document(path, flow, title)


def render_nc_report(
    result: "NCResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render a Noise Criteria (NC) assessment fiche to a PDF at ``path``.

    :param result: An :class:`~phonometry.room.room_noise.NCResult`.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a bare
        assessment fiche (body + result + disclaimer, no header). A supplied
        ``requirement`` is read as the maximum acceptable NC rating.
    :param verbose: When ``True``, the left table adds the per-band NC contour
        value read by the tangency method.
    :param language: Fiche language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    return _render_room_noise(
        result,
        path,
        basis_template=(
            "Noise Criteria (NC) rating by the tangency method (ANSI/ASA S12.2-2019)."
        ),
        left_builder=_nc_left_cell,
        statement_builder=_nc_statement_terms,
        symbol="NC",
        metadata=metadata,
        verbose=verbose,
        language=language,
    )


def render_rc_report(
    result: "RCResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render a Room Criteria Mark II (RC) assessment fiche to a PDF at ``path``.

    :param result: An :class:`~phonometry.room.room_noise.RCResult`.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a bare
        assessment fiche (body + result + disclaimer, no header). A supplied
        ``requirement`` is read as the maximum acceptable RC rating.
    :param verbose: When ``True``, the left table adds the reference RC Mark II
        curve and the measured deviation from it.
    :param language: Fiche language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    return _render_room_noise(
        result,
        path,
        basis_template=(
            "Room Criteria Mark II (RC) rating (ANSI/ASA S12.2-2019, Annex D)."
        ),
        left_builder=_rc_left_cell,
        statement_builder=_rc_statement_terms,
        symbol="RC",
        metadata=metadata,
        verbose=verbose,
        language=language,
    )
