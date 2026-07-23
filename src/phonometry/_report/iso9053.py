#  Copyright (c) 2026. Jose M. Requena-Plens
"""ISO 9053-1:2018 static-method airflow-resistance fiche (reportlab renderer).

Renders a
:class:`~phonometry.materials.airflow_resistance.StaticAirflowResult` to a
one-page PDF laid out like an accredited airflow-resistance test report
(ISO 9053-1:2018, static/direct airflow method):

* a title and the standard-basis line;
* an optional metadata header block (client, manufacturer, specimen, the
  specimen thickness ``d``, test facility, date, climate ...), built from the
  supplied :class:`ReportMetadata`;
* a two-panel body with a compact metrics table on the left (the evaluation
  velocity, the fitted pressure difference, the airflow resistance ``R``, the
  specific airflow resistance ``R_s``, the airflow resistivity ``sigma`` when a
  thickness is available, and the through-origin fit coefficients ``a`` and
  ``b``) beside the fitted ``dp(u)`` curve on the right, drawn by the result's
  own ``plot(ax=...)`` so the curve is native to the library;
* a boxed specific airflow resistance ``R_s`` with the airflow resistance ``R``
  and the airflow resistivity ``sigma`` alongside;
* a footer identity/disclaimer block.

ISO 9053-1 is a material characterisation, so this fiche carries no pass/fail
verdict. The clause 7.5 stepwise procedure fits the pressure difference against
the linear airflow velocity with a through-origin second-order regression
``dp = a*u + b*u**2`` and evaluates the resistances at the reference velocity
``u = 0.5 mm/s``; the linear coefficient ``a`` is the zero-velocity specific
airflow resistance. All resistance quantities are printed to the nearest whole
Pa*s unit and the evaluation velocity to 0,1 mm/s.

The quantity-independent skeleton lives in :mod:`._layout`; this module only
holds the ISO 9053-1 specifics. reportlab, matplotlib and svglib are soft
dependencies imported lazily (reportlab and svglib ship in the
``phonometry[report]`` extra, matplotlib in ``phonometry[plot]``); each is
guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any, List, Tuple

from ._i18n import format_number, t
from ._layout import (
    _ACCENT_HEX,
    _REPORTLAB_HINT,
    build_document,
    document_styles,
    fmt_meta,
    footer_flow,
    grid_table,
    metrics_table,
    render_figure_drawing,
    result_box,
    two_panel_body,
)
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..materials.airflow_resistance import StaticAirflowResult


def _pas(value: float, language: str = "en") -> str:
    """A resistance quantity to the nearest whole Pa*s unit."""
    return format_number(value, language, decimals=0)


def _mm_s(value_m_s: float, language: str = "en") -> str:
    """A linear airflow velocity (stored in m/s) printed in mm/s to 0,1 mm/s."""
    return format_number(value_m_s * 1e3, language, decimals=1, trim=True)


def _pa(value: float, language: str = "en") -> str:
    """A pressure difference to 0,1 Pa."""
    return format_number(value, language, decimals=1, trim=True)


def _metadata_pairs(
    metadata: ReportMetadata, language: str = "en"
) -> List[Tuple[str, str]]:
    """Build the ordered (label, value) pairs of the airflow-resistance header grid.

    Only fields that are set are returned. The applicable fields are the generic
    identity fields plus the specimen thickness ``d`` in the flow direction
    (``thickness``, stored in metres and printed in millimetres) and the
    environmental conditions.
    """
    specs: List[Tuple[str, str | None]] = [
        (t("Client", language), metadata.client),
        (t("Manufacturer", language), metadata.manufacturer),
        (t("Description", language), metadata.specimen),
        (t("Thickness d [mm]", language),
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
    result: "StaticAirflowResult", language: str = "en"
) -> List[Tuple[str, str]]:
    """The scalar results shown in the left-hand metrics table.

    The evaluation velocity is shown in mm/s, the fitted pressure difference in
    Pa, and the resistance quantities to the nearest whole Pa*s unit. The
    airflow resistivity ``sigma`` is shown only when the result carries a
    thickness. The through-origin fit coefficients ``a`` (the zero-velocity
    specific airflow resistance) and ``b`` close the table.
    """
    rows: List[Tuple[str, str]] = [
        (t("Evaluation velocity u [mm/s]", language),
         _mm_s(result.evaluation_velocity, language)),
        (t("Fitted pressure difference &#916;p [Pa]", language),
         _pa(result.pressure_drop, language)),
        (t("Airflow resistance R [Pa&#183;s/m<super>3</super>]", language),
         _pas(result.resistance, language)),
        (t("Specific airflow resistance R<sub>s</sub> [Pa&#183;s/m]", language),
         _pas(result.specific_resistance, language)),
    ]
    if result.resistivity is not None:
        rows.append(
            (t("Airflow resistivity &#963; [Pa&#183;s/m<super>2</super>]", language),
             _pas(result.resistivity, language))
        )
    rows.append(
        (t("Zero-velocity resistance a [Pa&#183;s/m]", language),
         _pas(result.linear_coefficient, language))
    )
    rows.append(
        (t("Quadratic coefficient b [Pa&#183;s<super>2</super>/m<super>2</super>]",
           language),
         _pas(result.quadratic_coefficient, language))
    )
    return rows


def _statement(result: "StaticAirflowResult", language: str = "en") -> str:
    """The boxed specific airflow resistance ``R_s`` (clause 7.5)."""
    return t(
        "Specific airflow resistance R<sub>s</sub> = "
        "<b>{value} Pa&#183;s/m</b>", language
    ).format(value=_pas(result.specific_resistance, language))


def _extended_terms(
    result: "StaticAirflowResult", language: str = "en"
) -> List[str]:
    """The airflow resistance ``R``, resistivity ``sigma`` and evaluation velocity."""
    terms = [
        t("Airflow resistance R = {value} Pa&#183;s/m<super>3</super>", language).format(
            value=_pas(result.resistance, language)
        ),
    ]
    if result.resistivity is not None:
        terms.append(
            t("Airflow resistivity &#963; = {value} Pa&#183;s/m<super>2</super>",
              language).format(value=_pas(result.resistivity, language))
        )
    terms.append(
        t("Evaluated at u = {value} mm/s", language).format(
            value=_mm_s(result.evaluation_velocity, language)
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
            "{standard} static-method determination of the airflow resistance "
            "of a porous material by a steady unidirectional (DC) flow per "
            "ISO 9053-1:2018.",
            language,
        ).format(standard=html.escape(measurement_standard))
    return t(
        "Static-method determination of the airflow resistance of a porous "
        "material by a steady unidirectional (DC) flow per ISO 9053-1:2018.",
        language,
    )


def render_static_airflow_report(
    result: "StaticAirflowResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an ISO 9053-1 static airflow-resistance fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.materials.airflow_resistance.StaticAirflowResult`
        carrying the airflow resistance ``R``, the specific airflow resistance
        ``R_s``, the airflow resistivity ``sigma`` (when a thickness was
        supplied), the through-origin fit coefficients and the evaluation
        point.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        body-and-disclaimer fiche. The ``requirement`` field is ignored
        (ISO 9053-1 is a characterisation, so there is no verdict).
    :param verbose: Accepted for a uniform ``.report()`` signature; the
        airflow-resistance fiche has a single body layout, so it has no effect.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab or matplotlib is not installed. The fiche
        always embeds the fitted ``dp(u)`` curve, so both are required
        (``pip install "phonometry[report,plot]"``).
    """
    del verbose  # uniform signature; the airflow-resistance fiche has one layout
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title = t("Airflow resistance of porous materials", language)

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
        Paragraph(t("Static airflow-resistance results", language), caption_style),
        metrics_table(_metric_rows(result, language)),
    ]
    # Non-band plot (the fitted dp(u) curve): self-scaling axis.
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
