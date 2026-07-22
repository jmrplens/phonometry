#  Copyright (c) 2026. Jose M. Requena-Plens
"""EN 29052-1 / ISO 9052-1 dynamic-stiffness fiche (reportlab renderer).

Renders a
:class:`~phonometry.materials.dynamic_stiffness.DynamicStiffnessResult` to a
one-page PDF laid out like an accredited dynamic-stiffness test report
(EN 29052-1:1992, identical to ISO 9052-1:1989):

* a title and the standard-basis line;
* an optional metadata header block (client, specimen, the total mass per unit
  area ``m't`` used during the test, the loaded specimen thickness ``d``, test
  facility, date, climate ...), built from the supplied :class:`ReportMetadata`
  and covering the Clause 9 b)/d) reporting items;
* a two-panel body with a compact metrics table on the left (the resonant
  frequency ``fr``, the apparent dynamic stiffness ``s't`` of Formula 4, the
  enclosed-gas term ``s'a`` of Formula 7 when it applies, the installed dynamic
  stiffness ``s'`` of Clause 8.2 and the supported-floor natural frequency
  ``f0`` of Formula 2) beside the ``f0(s')`` design curve on the right, drawn by
  the result's own ``plot(ax=...)`` so the curve is native to the library;
* a boxed apparent dynamic stiffness ``s't`` with the installed ``s'`` and the
  resonant frequency ``fr`` alongside;
* a footer identity/disclaimer block.

EN 29052-1 is a characterisation, so this fiche carries no pass/fail verdict.
Clause 9 requires every dynamic stiffness per unit area to be stated in
meganewtons per cubic metre to the nearest meganewton per cubic metre, so the
stiffness values are rounded to the nearest MN/m3; the frequencies are shown to
0,1 Hz.

The quantity-independent skeleton lives in :mod:`._layout`; this module only
holds the EN 29052-1 specifics. reportlab, matplotlib and svglib are soft
dependencies imported lazily (reportlab and svglib ship in the
``phonometry[report]`` extra, matplotlib in ``phonometry[plot]``); each is
guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any, List, Tuple

import numpy as np

from ._i18n import format_number, t
from ._layout import (
    _ACCENT_HEX,
    _REPORTLAB_HINT,
    build_document,
    document_styles,
    fmt_meta,
    fmt_num,
    footer_flow,
    grid_table,
    metrics_table,
    render_figure_drawing,
    result_box,
    two_panel_body,
)
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..materials.dynamic_stiffness import DynamicStiffnessResult


def _mn(value: float, language: str = "en") -> str:
    """Dynamic stiffness in MN/m3 to the nearest MN/m3 (Clause 9)."""
    return format_number(value / 1e6, language, decimals=0)


def _hz(value: float, language: str = "en") -> str:
    """A frequency to 0,1 Hz."""
    return format_number(value, language, decimals=1)


def _metadata_pairs(
    metadata: ReportMetadata, language: str = "en"
) -> List[Tuple[str, str]]:
    """Build the ordered (label, value) pairs of the dynamic-stiffness header grid.

    Only fields that are set are returned. The applicable fields are the generic
    identity fields plus the total mass per unit area ``m't`` used during the
    test (``mass_per_area``, kg/m2), the loaded specimen thickness ``d``
    (``thickness``, stored in metres and printed in millimetres, Clause 9 b))
    and the environmental conditions (Clause 9 d)). The frequency-range/room
    fields of the other fiches do not apply here.
    """
    specs: List[Tuple[str, str | None]] = [
        (t("Client", language), metadata.client),
        (t("Manufacturer", language), metadata.manufacturer),
        (t("Description", language), metadata.specimen),
        (t("Total mass per area m&#8242;<sub>t</sub> [kg/m<super>2</super>]", language),
         fmt_meta(metadata.mass_per_area, language)
         if metadata.mass_per_area is not None else None),
        (t("Thickness under load d [mm]", language),
         fmt_meta(metadata.thickness * 1e3, language)
         if metadata.thickness is not None else None),
        (t("Test facility", language), metadata.test_room),
        (t("Date of test", language), metadata.test_date),
        (t("Temperature [&#176;C]", language),
         fmt_meta(metadata.temperature, language)
         if metadata.temperature is not None else None),
        (t("Relative humidity [%]", language),
         fmt_meta(metadata.relative_humidity, language)
         if metadata.relative_humidity is not None else None),
    ]
    # The formatted values are label-safe; the free-text values are XML-escaped
    # so a stray '&' or '<' cannot break reportlab's Paragraph parser.
    return [
        (label, html.escape(str(value)))
        for label, value in specs
        if value is not None
    ]


def _metric_rows(
    result: "DynamicStiffnessResult", language: str = "en"
) -> List[Tuple[str, str]]:
    """The scalar results shown in the left-hand metrics table.

    The resonant frequency and the natural frequency are printed to 0,1 Hz; the
    dynamic stiffnesses to the nearest MN/m3 (Clause 9). The enclosed-gas term
    ``s'a`` is shown only when it is non-zero (an air-permeable material in the
    intermediate/low airflow-resistivity regime); the installed ``s'`` shows an
    em dash and the natural frequency is omitted when the method cannot resolve
    ``s'`` (a non-finite result, Clause 8.2 c)).
    """
    resolved = bool(np.isfinite(result.dynamic_stiffness))
    rows: List[Tuple[str, str]] = [
        (t("Resonant frequency f<sub>r</sub> [Hz]", language),
         _hz(result.resonant_frequency, language)),
        (t("Apparent dynamic stiffness s&#8242;<sub>t</sub> [MN/m<super>3</super>]",
           language),
         _mn(result.apparent_stiffness, language)),
    ]
    if result.gas_stiffness > 0.0:
        rows.append(
            (t("Enclosed-gas stiffness s&#8242;<sub>a</sub> [MN/m<super>3</super>]",
               language),
             _mn(result.gas_stiffness, language))
        )
    rows.append(
        (t("Dynamic stiffness s&#8242; [MN/m<super>3</super>]", language),
         _mn(result.dynamic_stiffness, language) if resolved else "&#8212;")
    )
    rows.append(
        (t("Supported-floor mass m&#8242; [kg/m<super>2</super>]", language),
         fmt_num(result.floor_mass_per_area, language))
    )
    if resolved and np.isfinite(result.natural_frequency):
        rows.append(
            (t("Natural frequency f<sub>0</sub> [Hz]", language),
             _hz(result.natural_frequency, language))
        )
    return rows


def _statement(result: "DynamicStiffnessResult", language: str = "en") -> str:
    """The boxed apparent dynamic stiffness ``s't`` (Formula 4)."""
    return t(
        "Apparent dynamic stiffness s&#8242;<sub>t</sub> = "
        "<b>{value} MN/m<super>3</super></b>", language
    ).format(value=_mn(result.apparent_stiffness, language))


def _extended_terms(
    result: "DynamicStiffnessResult", language: str = "en"
) -> List[str]:
    """The installed ``s'`` and the test resonance ``fr`` shown beside the box."""
    resolved = bool(np.isfinite(result.dynamic_stiffness))
    s_installed = (
        f"{_mn(result.dynamic_stiffness, language)} MN/m<super>3</super>"
        if resolved else "&#8212;"
    )
    terms = [
        t("Dynamic stiffness s&#8242; = {value}", language).format(value=s_installed),
        t("Resonant frequency f<sub>r</sub> = {value} Hz", language).format(
            value=_hz(result.resonant_frequency, language)
        ),
    ]
    if resolved and np.isfinite(result.natural_frequency):
        terms.append(
            t("Natural frequency f<sub>0</sub> = {value} Hz", language).format(
                value=_hz(result.natural_frequency, language)
            )
        )
    return terms


def _basis_line(metadata: ReportMetadata | None, language: str = "en") -> str:
    """The standard-basis line, naming the measurement standard when supplied."""
    measurement_standard = (
        metadata.measurement_standard if metadata is not None else None
    )
    if measurement_standard:
        return t(
            "{standard} resonance measurement of the apparent dynamic stiffness "
            "per unit area of a resilient layer used under a floating floor per "
            "EN 29052-1:1992 (ISO 9052-1:1989).",
            language,
        ).format(standard=html.escape(measurement_standard))
    return t(
        "Resonance measurement of the apparent dynamic stiffness per unit area "
        "of a resilient layer used under a floating floor per EN 29052-1:1992 "
        "(ISO 9052-1:1989).",
        language,
    )


def render_dynamic_stiffness_report(
    result: "DynamicStiffnessResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an EN 29052-1 dynamic-stiffness fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.materials.dynamic_stiffness.DynamicStiffnessResult`
        carrying the apparent, enclosed-gas and installed dynamic stiffnesses,
        the test resonance ``fr`` and the supported-floor natural frequency
        ``f0``.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        body-and-disclaimer fiche. The ``requirement`` field is ignored
        (EN 29052-1 is a characterisation, so there is no verdict).
    :param verbose: Accepted for a uniform ``.report()`` signature; the
        dynamic-stiffness fiche has a single body layout, so it has no effect.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    del verbose  # uniform signature; the dynamic-stiffness fiche has one layout
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title = t("Dynamic stiffness of resilient materials", language)

    flow: List[Any] = [
        Paragraph(title, title_style),
        Paragraph(_basis_line(metadata, language), basis_style),
    ]

    if metadata is not None and not metadata.is_empty():
        header_pairs = _metadata_pairs(metadata, language)
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(header_pairs))
    flow.append(Spacer(1, 8))

    left_cell = [
        Paragraph(t("Dynamic-stiffness results", language), caption_style),
        metrics_table(_metric_rows(result, language)),
    ]
    # Non-band plot (the f0(s') design curve): self-scaling axis.
    plot_drawing = render_figure_drawing(
        result.plot, 116 * mm, y_top=None, language=language
    )
    flow.append(two_panel_body(left_cell, plot_drawing))
    flow.append(Spacer(1, 8))

    flow.append(
        result_box(
            _statement(result, language),
            styles,
            accent,
            extended=_extended_terms(result, language),
        )
    )
    flow.extend(footer_flow(metadata, language))

    return build_document(path, flow, title)
