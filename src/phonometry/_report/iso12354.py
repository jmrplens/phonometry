#  Copyright (c) 2026. Jose M. Requena-Plens
"""EN/ISO 12354-1/-2 predicted building sound-insulation fiche (reportlab).

Renders a
:class:`~phonometry.building.building_prediction.AirbornePredictionResult`
(predicted apparent sound reduction index ``R'`` between rooms, EN/ISO 12354-1)
or an
:class:`~phonometry.building.building_prediction.ImpactPredictionResult`
(predicted apparent normalized impact sound pressure level ``L'n``, EN/ISO
12354-2) to a one-page **prediction** report. Unlike the measurement fiches
(:mod:`.iso10140`, :mod:`.iso16283`, :mod:`.iso15186`), the reported result is
an *estimate* of the in-situ performance computed from the laboratory
performance of the building elements plus the flanking transmission across the
junctions (the simplified single-number model, EN 12354-1 Clause 4.4 airborne /
EN 12354-2 Clause 4.3 impact); the sheet states this explicitly and is clearly
labelled a prediction, never a measurement.

The simplified model works directly on the elements' single-number ratings and
returns the apparent weighted rating (``R'w`` / ``L'n,w``) without an
intermediate one-third-octave spectrum, so this fiche has no per-band
measured-versus-shifted-reference curve to draw and therefore does not reuse the
per-band :func:`._insulation_fiche.render_insulation_fiche` skeleton. It reuses
the same quantity-independent building blocks that skeleton is itself built on
(:mod:`._layout`: the title/basis styles, the metadata header grid, a compact
left-hand metrics table beside the result's own vector plot in a two-panel body,
the boxed single number, the optional requirement verdict and the footer), the
layout the EPNL prediction fiche (:mod:`.annex16_epnl`) also uses.

reportlab, matplotlib and svglib are soft dependencies imported lazily
(reportlab and svglib ship in the ``phonometry[report]`` extra, matplotlib in
``phonometry[plot]``); each is guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple

from ._i18n import format_number, t
from ._layout import (
    _ACCENT_HEX,
    _MUTED_HEX,
    _REPORTLAB_HINT,
    build_document,
    display_round,
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
from .iso717 import _metadata_pairs
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..building.building_prediction import (
        AirbornePredictionResult,
        ImpactPredictionResult,
    )

#: Model standard deviation of the simplified single-number prediction, stated
#: for reference in the method statement (EN 12354-1:2000 Clause 5, EN 12354-2
#: Clause 6): about 2 dB.
_MODEL_SD_DB = 2


def _prediction_verdict(
    rating: float,
    requirement: float,
    rating_symbol: str,
    *,
    is_impact: bool,
    language: str,
) -> Tuple[str, bool]:
    """Verdict text and PASS flag for a predicted rating against a requirement.

    Airborne insulation passes at or above the requirement; impact level passes
    at or below it (a lower impact level is better). The comparison is on the
    displayed integer rating so a printed number can never contradict the
    verdict at the boundary.
    """
    value = display_round(rating, 0)
    req_text = fmt_num(requirement, language)
    if is_impact:
        passed = value <= requirement
        template = t("{sym} = {rating} dB, required &#8804; {req} dB", language)
    else:
        passed = value >= requirement
        template = t("{sym} = {rating} dB, required &#8805; {req} dB", language)
    text = template.format(
        sym=rating_symbol,
        rating=format_number(value, language, decimals=0),
        req=req_text,
    )
    return text, passed


def _render_prediction_fiche(
    *,
    result: Any,
    path: str,
    title_key: str,
    basis_key: str,
    rating_value: float,
    rating_symbol: str,
    left_caption_key: str,
    metric_rows: List[Tuple[str, str]],
    is_impact: bool,
    metadata: ReportMetadata | None,
    language: str,
) -> str:
    """Render a predicted-insulation fiche to a PDF at ``path``.

    Shared body of both prediction fiches: title and prediction-basis line, an
    optional metadata header, a two-panel body (the left-hand model-term metrics
    table beside the result's own plot), the boxed single-number rating, the
    prediction statement, an optional requirement verdict and the footer.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title_text = t(title_key, language)
    flow: List[Any] = [
        Paragraph(title_text, title_style),
        Paragraph(t(basis_key, language), basis_style),
    ]

    # Metadata header grid (the same room/element grid the insulation fiches
    # share; only the supplied fields render).
    if metadata is not None and not metadata.is_empty():
        identity, conditions = _metadata_pairs(metadata, language)
        header_pairs = identity + conditions
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(header_pairs))
    flow.append(Spacer(1, 8))

    # Two-panel body: the model-term metrics table on the left, the result's own
    # vector plot (self-scaling bar chart) on the right.
    left_cell = [
        Paragraph(t(left_caption_key, language), caption_style),
        metrics_table(metric_rows, col_widths=[34 * mm, 22 * mm]),
    ]
    plot_drawing = render_figure_drawing(
        result.plot, 116 * mm, y_top=None, figsize=(6.4, 5.8), language=language
    )
    flow.append(two_panel_body(left_cell, plot_drawing))
    flow.append(Spacer(1, 8))

    # Boxed single-number predicted rating (an integer dB, as ISO 717 rates).
    rating_text = format_number(display_round(rating_value, 0), language, decimals=0)
    flow.append(
        result_box(f"{rating_symbol} = <b>{rating_text} dB</b>", styles, accent)
    )

    statement_style = ParagraphStyle(
        "prediction_statement", parent=styles["Normal"], fontSize=8.5,
        textColor=colors.HexColor(_MUTED_HEX), spaceBefore=4,
    )
    flow.append(
        Paragraph(
            t(
                "Predicted (estimated) result computed from the building "
                "elements' performance by the EN/ISO 12354 simplified "
                "single-number model; it is not a measurement. The reported "
                "standard deviation of the model is about {sd} dB.", language
            ).format(sd=_MODEL_SD_DB),
            statement_style,
        )
    )

    if metadata is not None and metadata.requirement is not None:
        text, passed = _prediction_verdict(
            rating_value, float(metadata.requirement), rating_symbol,
            is_impact=is_impact, language=language,
        )
        flow.extend(verdict_flow(text, passed, styles, language))

    flow.extend(footer_flow(metadata, language))

    return build_document(path, flow, title_text)


def render_iso12354_airborne_report(
    result: "AirbornePredictionResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render a predicted apparent airborne insulation fiche (EN/ISO 12354-1).

    :param result: The
        :class:`~phonometry.building.building_prediction.AirbornePredictionResult`
        carrying the predicted apparent weighted index ``R'w``, the direct-path
        index ``RDd,w`` and the per-path contributions.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        lightweight fiche (body, rating, statement and disclaimer).
    :param verbose: When ``True``, the left table lists every transmission path
        (direct and flanking) with its share of the transmitted energy; when
        ``False`` it lists only the direct path and each flanking path's
        weighted index.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    metric_rows: List[Tuple[str, str]] = []
    for contribution in result.paths:
        value = fmt_num(contribution.r_w, language)
        if verbose:
            share = format_number(
                100.0 * contribution.fraction, language, decimals=1
            )
            value = f"{value} &#183; {share}%"
        metric_rows.append((contribution.label, value))

    caption_key = (
        "Path R<sub>ij,w</sub> [dB] and energy share"
        if verbose
        else "Transmission paths R<sub>ij,w</sub> [dB]"
    )
    return _render_prediction_fiche(
        result=result,
        path=path,
        title_key="Predicted airborne sound insulation between rooms",
        basis_key=(
            "Predicted apparent sound reduction index R&#8242; "
            "(direct and flanking transmission) estimated in accordance with "
            "EN/ISO 12354-1:2000 (simplified single-number model, Clause 4.4). "
            "This is a prediction from element data, not a measurement. "
            "R&#8242;<sub>w</sub> per ISO 717-1."
        ),
        rating_value=result.r_prime_w,
        rating_symbol="R&#8242;<sub>w</sub>",
        left_caption_key=caption_key,
        metric_rows=metric_rows,
        is_impact=False,
        metadata=metadata,
        language=language,
    )


def render_iso12354_impact_report(
    result: "ImpactPredictionResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render a predicted apparent impact insulation fiche (EN/ISO 12354-2).

    :param result: The
        :class:`~phonometry.building.building_prediction.ImpactPredictionResult`
        carrying the predicted apparent weighted level ``L'n,w`` and the
        Formula (21) terms (the bare-floor equivalent level ``Ln,w,eq``, the
        covering improvement ``ΔLw`` and the flanking correction ``K``).
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        lightweight fiche (body, rating, statement and disclaimer).
    :param verbose: Accepted for a uniform ``.report()`` signature; the impact
        fiche has a single body layout, so it has no effect.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    del verbose  # uniform signature; the impact fiche has one body layout
    metric_rows: List[Tuple[str, str]] = [
        (
            t("Bare-floor level L<sub>n,w,eq</sub>", language),
            fmt_num(result.ln_w_eq, language),
        ),
        (
            t("Covering improvement &#916;L<sub>w</sub>", language),
            fmt_num(result.delta_l_w, language),
        ),
        (
            t("Flanking correction K", language),
            fmt_num(result.k_correction, language),
        ),
    ]
    return _render_prediction_fiche(
        result=result,
        path=path,
        title_key="Predicted impact sound insulation of floors",
        basis_key=(
            "Predicted apparent normalized impact sound pressure level "
            "L&#8242;<sub>n</sub> (bare floor, covering and flanking) estimated "
            "in accordance with EN/ISO 12354-2:2000 (simplified single-number "
            "model, Clause 4.3). This is a prediction from element data, not a "
            "measurement. L&#8242;<sub>n,w</sub> per ISO 717-2."
        ),
        rating_value=result.l_prime_n_w,
        rating_symbol="L&#8242;<sub>n,w</sub>",
        left_caption_key="Impact level prediction - Formula (21) terms [dB]",
        metric_rows=metric_rows,
        is_impact=True,
        metadata=metadata,
        language=language,
    )
