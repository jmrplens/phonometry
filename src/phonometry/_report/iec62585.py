#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 62585 free-field-correction fiche (reportlab renderer).

Renders a
:class:`~phonometry.metrology.free_field_corrections.CorrectionUncertaintyVerification`
to a one-page PDF: the part of the documentation clause 15 of IEC 62585:2012
asks a laboratory to issue that the verdict carries, items n) and o), "the
corrections obtained as a result of the measurements, together with the actual
associated expanded uncertainties of measurement and the coverage factor" and
"a statement on whether the measured expanded uncertainties of measurement are
within the maximum permitted values". The section order is the one accredited
calibration certificates use: identification, the basis, the results, the
conformity statement and the signature block.

The page holds:

* a title and the standard-basis line (the clause and what it corrects for);
* an optional metadata header block, rendered only for the fields supplied on
  the :class:`ReportMetadata`;
* a measurement-basis strip stating the level of confidence, the inclusive
  reading of "shall not exceed", what clause 5 does with a measurement that
  exceeds a maximum and, for clauses 12 to 14 with a range, the second
  requirement on the microphone;
* a two-panel body with the per-frequency table on the left (exact frequency,
  correction, expanded uncertainty, coverage factor, maximum, range and the
  verdict) and the result's own plot on the right;
* the boxed statement and the verdict row; and
* a footer identity/disclaimer block.

The quantity-independent skeleton lives in :mod:`._layout`. reportlab,
matplotlib and svglib are soft dependencies imported lazily.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any

import numpy as np

from ._i18n import format_number, t
from ._layout import (
    _ACCENT_HEX,
    _REPORTLAB_HINT,
    band_table,
    band_table_header_style,
    build_document,
    document_styles,
    fiche_paragraph,
    footer_flow,
    grid_table,
    measurement_basis_style,
    render_figure_drawing,
    result_box,
    two_panel_body,
    verdict_flow,
)

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from ..metrology.free_field_corrections import (
        CorrectionUncertaintyVerification,
    )
    from .metadata import ReportMetadata

#: The clauses whose corrections are judged on their range over the
#: microphones as well.
_RANGE_CLAUSES = (12, 13, 14)

#: The widths of the two panels, in mm, which fill the 174 mm between the
#: margins of the page, and of the plot drawn in the second, which leaves the
#: cell's padding of about 2 mm on its left.
_TABLE_WIDTH_MM = 86.0
_PLOT_WIDTH_MM = 88.0
_DRAWING_WIDTH_MM = 86.0


def _basis(
    result: CorrectionUncertaintyVerification,
    metadata: ReportMetadata | None,
    language: str,
) -> str:
    """The standard-basis line for the fiche, naming what the clause corrects
    for in the words the verdict carries.
    """
    clause = t(
        "IEC 62585:2012, clause {n}: corrections for {subject}", language
    ).format(n=result.clause, subject=t(result.subject, language))
    measurement_standard = (
        metadata.measurement_standard if metadata is not None else None
    )
    if measurement_standard:
        return t("{standard}. {clause}.", language).format(
            standard=html.escape(measurement_standard), clause=clause
        )
    return f"{clause}."


def _metadata_pairs(metadata: ReportMetadata, language: str) -> list[tuple[str, str]]:
    """The ordered (label, value) pairs of the header grid.

    The item is a model of sound level meter with its source, so the specimen
    field names the meter and the room field the laboratory's facility.
    """
    specs: list[tuple[str, str | None]] = [
        (t("Client", language), metadata.client),
        (t("Sound level meter", language), metadata.specimen),
        (t("Manufacturer", language), metadata.manufacturer),
        (t("Test facility", language), metadata.test_room),
        (t("Date of test", language), metadata.test_date),
    ]
    return [
        (label, html.escape(str(value))) for label, value in specs if value is not None
    ]


def _cell(value: float | None, language: str, decimals: int) -> str:
    """A table cell, or an en dash where the value was not given."""
    if value is None:
        return "&#8211;"
    return format_number(value, language, decimals=decimals)


def _column(values: NDArray[np.float64] | None, index: int) -> float | None:
    """One entry of an optional per-frequency column."""
    return None if values is None else float(values[index])


def _rows(result: CorrectionUncertaintyVerification, language: str) -> list[list[Any]]:
    """Header plus per-frequency rows of the results table."""
    header_style = band_table_header_style()
    with_range = result.correction_range_db is not None
    labels = [
        "f [Hz]",
        "C [dB]",
        "U [dB]",
        "k",
        "U<sub>max</sub> [dB]",
    ]
    if with_range:
        labels.append("Range [dB]")
    labels.append("Verdict")
    header = [fiche_paragraph(t(label, language), header_style) for label in labels]
    rows: list[list[Any]] = [header]
    uncertainty_passes = np.asarray(result.uncertainty_passes)
    range_passes = result.range_passes
    for index, frequency in enumerate(np.asarray(result.frequencies_hz)):
        passed = bool(uncertainty_passes[index]) and (
            range_passes is None or bool(np.asarray(range_passes)[index])
        )
        row = [
            format_number(float(frequency), language, decimals=1),
            _cell(_column(result.correction_db, index), language, 2),
            format_number(
                float(result.expanded_uncertainty_db[index]), language, decimals=3
            ),
            _cell(_column(result.coverage_factor, index), language, 2),
            format_number(
                float(result.maximum_uncertainty_db[index]), language, decimals=2
            ),
        ]
        if with_range:
            row.append(_cell(_column(result.correction_range_db, index), language, 3))
        row.append(t("within" if passed else "exceeds", language))
        rows.append(row)
    return rows


def _basis_strip(result: CorrectionUncertaintyVerification, language: str) -> str:
    """The measurement-basis line: confidence level, reading, consequence."""
    text = t(
        "Expanded uncertainties at a level of confidence of 95 % (clause 5) "
        "against the maximum of clause {n} at each frequency; a value equal to "
        "its maximum does not exceed it, and a measurement that exceeds one is "
        "not used for the corrections of the manual.",
        language,
    ).format(n=result.clause)
    if result.correction_range_db is not None:
        text += " " + t(
            "The range of the corrections over the microphones is judged against "
            "the same maximum (clause {n}).",
            language,
        ).format(n=result.clause)
    return text


def _statement(
    result: CorrectionUncertaintyVerification, language: str
) -> tuple[str, list[str]]:
    """The boxed statement and the extended terms beside it."""
    failures = int(result.failing_frequencies_hz.size)
    count = int(np.asarray(result.frequencies_hz).size)
    if failures:
        statement = t(
            "<b>Exceeds</b> the maximum permitted values of clause {n} at {k} of "
            "{m} frequencies",
            language,
        ).format(n=result.clause, k=failures, m=count)
    else:
        statement = t(
            "Within the maximum permitted values of clause {n} at all {m} frequencies",
            language,
        ).format(n=result.clause, m=count)
    ratio = float(
        np.max(
            np.asarray(result.expanded_uncertainty_db)
            / np.asarray(result.maximum_uncertainty_db)
        )
    )
    extended = [
        t("Largest U / U<sub>max</sub>: {ratio}", language).format(
            ratio=format_number(ratio, language, decimals=2)
        ),
    ]
    if result.coverage_factor is not None:
        factors = np.asarray(result.coverage_factor)
        extended.append(
            t("Coverage factor k from {low} to {high}", language).format(
                low=format_number(float(factors.min()), language, decimals=2),
                high=format_number(float(factors.max()), language, decimals=2),
            )
        )
    if result.clause in _RANGE_CLAUSES and result.correction_range_db is None:
        extended.append(t("Range over the microphones not judged", language))
    return statement, extended


def render_iec62585_report(
    result: CorrectionUncertaintyVerification,
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an IEC 62585 free-field-correction fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.metrology.free_field_corrections.CorrectionUncertaintyVerification`.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a bare
        fiche (body, result and disclaimer only).
    :param verbose: Accepted for a uniform ``.report()`` signature; the fiche
        has a single body layout, so it has no effect.
    :param language: Fiche language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    del verbose  # uniform signature; the fiche has one two-panel body layout
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, _caption_style = document_styles(accent)
    title = t("Free-field corrections of a sound level meter", language)
    flow: list[Any] = [
        fiche_paragraph(title, title_style),
        fiche_paragraph(_basis(result, metadata, language), basis_style),
    ]
    if metadata is not None and not metadata.is_empty():
        header_pairs = _metadata_pairs(metadata, language)
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(header_pairs))

    strip_style = measurement_basis_style()
    flow.append(fiche_paragraph(_basis_strip(result, language), strip_style))
    flow.append(Spacer(1, 8))

    rows = _rows(result, language)
    with_range = result.correction_range_db is not None
    widths = (
        [14 * mm, 10 * mm, 10 * mm, 8 * mm, 12 * mm, 15 * mm, 15 * mm]
        if with_range
        else [16 * mm, 13 * mm, 13 * mm, 10 * mm, 14 * mm, 18 * mm]
    )
    # Two dozen one-third-octave rows and the plot beside them fill the sheet;
    # a tighter row keeps the Spanish fiche, whose basis strip runs longer, on
    # its one page.
    compact = [
        ("TOPPADDING", (0, 1), (-1, -1), 1.6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 1.6),
    ]
    left_cell = band_table(rows, widths, len(rows) - 1, compact, band_centres=None)
    # The two panels share the 174 mm the page's margins leave: the table
    # (84 mm and its padding) and the plot, whose legend the drawing's width
    # includes, so that it ends at the right margin and not past it.
    plot_drawing = render_figure_drawing(
        result.plot,
        _DRAWING_WIDTH_MM * mm,
        y_top=None,
        language=language,
    )
    flow.append(
        two_panel_body(
            left_cell,
            plot_drawing,
            left_width_mm=_TABLE_WIDTH_MM,
            plot_width_mm=_PLOT_WIDTH_MM,
        )
    )
    flow.append(Spacer(1, 8))

    statement, extended = _statement(result, language)
    flow.append(result_box(statement, styles, accent, extended))
    text = t(
        "Actual expanded uncertainties against the maximum permitted by clause {n}",
        language,
    ).format(n=result.clause)
    flow.extend(
        verdict_flow(text=text, passed=result.passes, styles=styles, language=language)
    )
    flow.extend(footer_flow(metadata, language))
    return build_document(path, flow, title)
