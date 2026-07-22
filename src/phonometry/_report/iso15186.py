#  Copyright (c) 2026. Jose M. Requena-Plens
"""ISO 15186-1 intensity sound-insulation test report (reportlab renderer).

Renders a
:class:`~phonometry.building.intensity_insulation.IntensityReductionResult`
(laboratory sound insulation measured with sound intensity, ISO 15186-1:2000)
to the one-page laboratory test report of the standard's Clause 8, laid out
like the accredited laboratory reports rated per ISO 717-1. The reported
quantity is the intensity sound reduction index ``RI`` (Clause 3.8,
Formula (7)); its single-number rating ``RI,w`` is the ordinary ISO 717-1
airborne rating evaluated on the intensity spectrum, so the shared two-panel
skeleton (title and basis line, optional metadata header, per-band table
beside the measured-versus-shifted-reference curve, boxed single-number
rating, method statement, optional verdict, footer) of :mod:`._insulation_fiche`
is reused unchanged. This module only holds the ISO 15186 specifics: the fixed
labels, the intensity-method statement and the verbose table that annexes the
Kc-modified index ``RI,M`` (Clause 3.10, Formula (9)) beside ``RI``.

reportlab, matplotlib and svglib are soft dependencies imported lazily by the
shared renderer (reportlab and svglib ship in the ``phonometry[report]``
extra, matplotlib in ``phonometry[plot]``); each is guarded with an actionable
:class:`ImportError`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Sequence, Tuple

import numpy as np

from ._i18n import t
from ._insulation_fiche import Column, render_insulation_fiche
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..building.insulation import WeightedRatingResult
    from ..building.intensity_insulation import IntensityReductionResult

#: Fixed labels for the intensity sound reduction index fiche: title, basis
#: line, the quantity symbol used in the table header, the rating symbol of the
#: boxed result, the plot y-axis label (mathtext) and the method statement.
_SPEC: dict[str, str] = {
    "title": "Laboratory sound insulation by sound intensity",
    "basis": (
        "Intensity sound reduction index R<sub>I</sub> measured in "
        "accordance with ISO 15186-1:2000 (transmitted sound power measured "
        "directly with an intensity probe). Rating per ISO 717-1:2020."
    ),
    "symbol": "R<sub>I</sub>",
    "rating_symbol": "R<sub>I,w</sub>",
    "ylabel": "$R_I$ [dB]",
    "statement": (
        "Evaluation based on laboratory measurement results obtained by the "
        "sound-intensity method (transmitted sound power measured directly "
        "over the measurement surface)."
    ),
}


def render_iso15186_report(
    result: "IntensityReductionResult",
    rating: "WeightedRatingResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an ISO 15186-1 intensity sound-insulation test report to a PDF.

    :param result: The intensity result
        (:class:`~phonometry.building.intensity_insulation.IntensityReductionResult`)
        carrying the per-band intensity sound reduction index ``RI`` and,
        optionally, the Kc-modified index ``RI,M``.
    :param rating: The ISO 717-1 rating of the reported ``RI`` (the result's
        own ``rating``); its ``plot`` draws the fiche curve.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        lightweight fiche (body, rating, statement and disclaimer).
    :param verbose: When ``True`` and the modified index ``RI,M`` is present,
        the left table annexes ``RI,M`` beside the reported ``RI``.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is
        not installed.
    """
    modified = result.r_i_modified

    def build_columns(
        value_header: str, curve: np.ndarray, verbose: bool, language: str
    ) -> Tuple[Sequence[Column], str, Any]:
        """The table: ``f | RI`` or, verbose with Kc, ``f | RI | RI,M``."""
        from reportlab.lib.units import mm

        if verbose and modified is not None:
            columns: List[Column] = [
                (value_header, curve, 1),
                (
                    t("R<sub>I,M</sub> [dB]", language),
                    np.asarray(modified, dtype=np.float64),
                    1,
                ),
            ]
            caption = t("Per-band index and Kc-modified index", language)
            col_widths = [12 * mm] + [22 * mm for _ in columns]
            return columns, caption, col_widths
        # ISO 717-1 Clause 4.4 requires stating whether the rating came from
        # one-third-octave or octave bands; the caption declares the set.
        caption_key = (
            "Octave-band {vh} [dB]"
            if np.asarray(rating.band_centers).size == 5
            else "One-third-octave {vh} [dB]"
        )
        caption = t(caption_key, language).format(vh=_SPEC["symbol"])
        return [(value_header, curve, 1)], caption, None

    return render_insulation_fiche(
        result, rating, path,
        spec=_SPEC,
        is_impact=False,
        curve_attr="r_i",
        build_columns=build_columns,
        metadata=metadata,
        verbose=verbose,
        language=language,
    )
