#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ISO 10846 dynamic-transfer-stiffness fiche (reportlab renderer).

Renders a
:class:`~phonometry.vibration.structural.transfer_stiffness.TransferStiffnessResult` to a
one-page PDF laid out like a dynamic-transfer-stiffness characterisation report
for a resilient element (a vibration isolator, mount, bellows or hose) per
ISO 10846-1:2008 (the transfer-stiffness definition, 3.7), determined by either
the direct method (ISO 10846-2:2008) or the indirect blocking-mass method
(ISO 10846-3:2002):

* a title and the standard-basis line naming the determination method;
* an optional metadata header grid (client, manufacturer, the tested element,
  test facility, instrumentation, date, temperature);
* a two-panel body with a compact table of the FRF's characteristic points on
  the left (the method, the blocking mass for the indirect method, the frequency
  range, the low-frequency stiffness plateau ``|k2,1|``, its level ``L_k`` and
  the low-frequency loss factor ``eta``) beside the transfer-stiffness level
  spectrum ``L_k(f)`` drawn by the result's own ``plot(ax=...)``, with the
  lines that fail an adequacy condition drawn apart;
* the one-third-octave band levels ``L_k,av`` the test report of ISO 10846-2
  (9 m), which clause 10 requires) and ISO 10846-3 (10 j)) asks for, the
  squared-magnitude averages of the valid lines, or a note when no band holds
  the five lines an average needs;
* a boxed representative value, the low-frequency dynamic-transfer-stiffness
  level ``L_k`` (the plateau that characterises the element below its internal
  resonances), with the stiffness magnitude and the method alongside; and
* a footer identity/disclaimer block.

The characteristic points are read at the lowest *valid* line: a line the
result marks as failing an adequacy condition is excluded from the evaluation
by the part itself, so it cannot be the headline either. The fiche carries no
pass/fail verdict (a transfer-stiffness determination is a characterisation).
The shared FRF skeleton lives in :mod:`._frf_fiche`; this module only holds
the transfer-stiffness specifics.
reportlab, matplotlib and svglib are soft dependencies imported lazily (reportlab
and svglib ship in the ``phonometry[report]`` extra, matplotlib in
``phonometry[plot]``); each is guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

import numpy as np

from ._frf_fiche import frequency_range, frf_metadata_pairs, render_frf_fiche
from ._i18n import format_number, t

if TYPE_CHECKING:
    from ..vibration.structural.transfer_stiffness import (
        BandAveragedStiffness,
        TransferStiffnessResult,
    )
    from .metadata import ReportMetadata

#: Bands per row of the band-level table: twelve columns of about 12 mm
#: beside a 26 mm label column fill the 174 mm content width.
_BANDS_PER_ROW = 12
_LABEL_COLUMN_MM = 26.0
_CONTENT_WIDTH_MM = 174.0


def _is_indirect(result: TransferStiffnessResult) -> bool:
    """Return ``True`` for the indirect (blocking-mass) method (ISO 10846-3)."""
    return result.blocking_mass is not None


def _method(result: TransferStiffnessResult, language: str = "en") -> str:
    """The determination-method phrase naming the ISO 10846 part."""
    if _is_indirect(result):
        return t("indirect blocking-mass method (ISO 10846-3:2002)", language)
    return t("direct method (ISO 10846-2:2008)", language)


def _basis(result: TransferStiffnessResult, language: str = "en") -> str:
    """The standard-basis line naming the determination method."""
    return t(
        "Determination of the dynamic transfer stiffness k<sub>2,1</sub> of a "
        "resilient element by the {method} (ISO 10846-1:2008, 3.7).",
        language,
    ).format(method=_method(result, language))


def _reference_index(result: TransferStiffnessResult) -> int:
    """Index of the lowest line that enters the evaluation.

    With no validity flags every line does. An indirect determination marks
    the lines with ``|T| > 0.1`` as not valid, and those sit at the bottom of
    the sweep, below and around the mass-spring resonance: reading the plateau
    there printed the inflated stiffness of the resonance region as the
    element's headline value.

    :raises ValueError: when the result marks every line as not valid.
    """
    freq = np.asarray(result.frequencies, dtype=np.float64)
    if result.valid is None:
        return int(np.argmin(freq))
    valid = np.asarray(result.valid, dtype=bool)
    if not np.any(valid):
        msg = (
            "TransferStiffnessResult.report: no line meets the adequacy "
            "conditions of its part, so the fiche has no value to report."
        )
        raise ValueError(msg)
    candidates = np.flatnonzero(valid)
    return int(candidates[np.argmin(freq[candidates])])


def _low_frequency_values(
    result: TransferStiffnessResult,
) -> tuple[float, float, float, float]:
    """Return the lowest valid frequency and the ``|k2,1|``, ``L_k`` and ``eta`` there.

    The low-frequency point characterises the element below its internal
    resonances: the transfer stiffness there is the plateau reported as the
    headline value, and ISO 10846-1 (3.8) defines the loss factor only in the
    low-frequency range where inertial forces in the element are negligible.
    See :func:`_reference_index` for why the point is the lowest *valid* line.
    """
    freq = np.asarray(result.frequencies, dtype=np.float64)
    index = _reference_index(result)
    magnitude = float(np.asarray(result.magnitude, dtype=np.float64)[index])
    level = float(np.asarray(result.levels, dtype=np.float64)[index])
    # Reuse the result's own loss-factor property (eta = Im/Re, ISO 10846-1 3.8)
    # rather than recomputing it, so the fiche shares the single definition and
    # its validation (a purely imaginary stiffness is rejected there).
    eta = float(np.asarray(result.loss_factor, dtype=np.float64)[index])
    return float(freq[index]), magnitude, level, eta


def _mn(value: float, language: str = "en") -> str:
    """A stiffness magnitude in MN/m, to two decimals."""
    return format_number(value / 1e6, language, decimals=2)


def _metric_rows(
    result: TransferStiffnessResult, language: str = "en"
) -> list[tuple[str, str]]:
    """The characteristic points shown in the left-hand table.

    The determination method, the blocking mass (indirect method only), the
    measured frequency range, and the low-frequency stiffness plateau: its
    magnitude ``|k2,1|`` (MN/m), its level ``L_k`` (dB re 1 N/m) and the loss
    factor ``eta`` there.
    """
    _, magnitude, level, eta = _low_frequency_values(result)
    rows: list[tuple[str, str]] = [
        (t("Method", language), _method(result, language)),
    ]
    blocking_mass = result.blocking_mass
    if blocking_mass is not None:
        rows.append(
            (
                t("Blocking mass m<sub>2</sub> [kg]", language),
                format_number(float(blocking_mass), language, decimals=1),
            )
        )
    rows.extend(
        [
            (
                t("Frequency range f [Hz]", language),
                frequency_range(
                    np.asarray(result.frequencies, dtype=np.float64), language
                ),
            ),
            (
                t("Low-frequency |k<sub>2,1</sub>| [MN/m]", language),
                _mn(magnitude, language),
            ),
            (
                t("Low-frequency L<sub>k</sub> [dB re 1 N/m]", language),
                format_number(level, language, decimals=1),
            ),
            (
                t("Loss factor &#951; (low frequency)", language),
                format_number(eta, language, decimals=3),
            ),
        ]
    )
    return rows


def _statement(result: TransferStiffnessResult, language: str = "en") -> str:
    """The boxed representative value: the low-frequency transfer-stiffness level."""
    _, _, level, _ = _low_frequency_values(result)
    return t(
        "Low-frequency dynamic transfer stiffness level "
        "L<sub>k</sub> = <b>{value} dB re 1 N/m</b>",
        language,
    ).format(value=format_number(level, language, decimals=1))


def _extended_terms(result: TransferStiffnessResult, language: str = "en") -> list[str]:
    """The stiffness magnitude, the method and the loss factor shown beside the box."""
    freq, magnitude, _, eta = _low_frequency_values(result)
    return [
        t(
            "Low-frequency stiffness |k<sub>2,1</sub>| = {value} MN/m at {freq} Hz",
            language,
        ).format(
            value=_mn(magnitude, language),
            freq=format_number(freq, language, decimals=1, trim=True),
        ),
        t("Method: {method}", language).format(method=_method(result, language)),
        t("Loss factor &#951; = {value} (low frequency)", language).format(
            value=format_number(eta, language, decimals=3)
        ),
    ]


def _band_levels(result: TransferStiffnessResult) -> BandAveragedStiffness:
    """The band averages of the valid lines, their short-band warning muted.

    The fiche marks a band of fewer than five lines itself, in its own cell,
    so the warning would only repeat on the console what the page prints.
    """
    from ..vibration.structural.transfer_stiffness import TransferStiffnessWarning

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", TransferStiffnessWarning)
        return result.band_average()


def _band_level_flow(
    result: TransferStiffnessResult, language: str = "en"
) -> list[Any]:
    """The clause 10 band-level table, twelve bands a row, or a note.

    A band holding one to four valid lines has no level; its cell prints
    ``n = 3`` (the count), so the page says why the value is missing. When
    no band holds five lines the table would be all such cells, and a single
    sentence says so instead.
    """
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Spacer

    from ..filters.frequencies import _format_nominal_freq
    from ._i18n import decimal_comma
    from ._layout import band_table_header_style, fiche_paragraph, stacked_table

    styles = getSampleStyleSheet()
    caption = ParagraphStyle(
        "fiche_band_caption", parent=styles["Normal"], fontSize=8.5, leading=11
    )
    header_style = band_table_header_style()
    cell_style = ParagraphStyle(
        "fiche_band_cell",
        parent=styles["Normal"],
        fontSize=7.4,
        leading=8.8,
        alignment=1,
    )
    bands = _band_levels(result)
    if not np.any(bands.determined):
        return [
            fiche_paragraph(
                t(
                    "One-third-octave band levels: none determined, since no band "
                    "holds the five valid lines a band average needs "
                    "(ISO 10846, n &#8805; 5).",
                    language,
                ),
                caption,
            )
        ]
    flow: list[Any] = [
        fiche_paragraph(
            t(
                "One-third-octave band levels L<sub>k,av</sub> [dB re 1 N/m], "
                "squared-magnitude averages of the valid lines (n &#8805; 5)",
                language,
            ),
            caption,
        ),
        Spacer(1, 2),
    ]
    nominal = np.asarray(bands.nominal_frequencies, dtype=np.float64)
    levels = np.asarray(bands.levels, dtype=np.float64)
    counts = np.asarray(bands.line_counts)
    determined = np.asarray(bands.determined, dtype=bool)
    band_mm = (_CONTENT_WIDTH_MM - _LABEL_COLUMN_MM) / _BANDS_PER_ROW
    for start in range(0, nominal.size, _BANDS_PER_ROW):
        chunk = slice(start, start + _BANDS_PER_ROW)
        header = [t("f [Hz]", language)] + [
            decimal_comma(_format_nominal_freq(float(f)), language)
            for f in nominal[chunk]
        ]
        values = [t("L<sub>k,av</sub> [dB]", language)] + [
            format_number(float(level), language, decimals=1) if ok else f"n = {int(n)}"
            for level, n, ok in zip(
                levels[chunk], counts[chunk], determined[chunk], strict=True
            )
        ]
        widths = [_LABEL_COLUMN_MM * mm] + [band_mm * mm] * (len(header) - 1)
        table = stacked_table(
            [
                [fiche_paragraph(cell, header_style) for cell in header],
                [fiche_paragraph(cell, cell_style) for cell in values],
            ],
            widths,
        )
        # A last, shorter row of bands lines up under the first, column for
        # column, instead of centring itself on the page.
        table.hAlign = "LEFT"
        flow.append(table)
        flow.append(Spacer(1, 3))
    return flow


def render_transfer_stiffness_report(
    result: TransferStiffnessResult,
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an ISO 10846 dynamic-transfer-stiffness fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.vibration.structural.transfer_stiffness.TransferStiffnessResult`
        carrying the complex ``k2,1(f)`` and, for the indirect method, the
        blocking mass used.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        body-and-disclaimer fiche. The ``requirement`` field is ignored (a
        transfer-stiffness determination is a characterisation, so there is no
        verdict).
    :param verbose: Accepted for a uniform ``.report()`` signature; the
        transfer-stiffness fiche has a single body layout, so it has no effect.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab or matplotlib is not installed. The fiche
        always embeds the ``L_k(f)`` spectrum, so both are required
        (``pip install "phonometry[report,plot]"``).
    """
    del verbose  # uniform signature; the transfer-stiffness fiche has one layout
    header_pairs = (
        frf_metadata_pairs(metadata, [], language)
        if metadata is not None and not metadata.is_empty()
        else []
    )
    return render_frf_fiche(
        result,
        path,
        title=t("Dynamic transfer stiffness of a resilient element", language),
        basis=_basis(result, language),
        caption=t("Transfer-stiffness characteristics", language),
        header_pairs=header_pairs,
        metric_rows=_metric_rows(result, language),
        statement=_statement(result, language),
        extended=_extended_terms(result, language),
        metadata=metadata,
        language=language,
        after_body=lambda: _band_level_flow(result, language),
    )
