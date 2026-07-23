#  Copyright (c) 2026. Jose M. Requena-Plens
"""ISO 15186-1 intensity sound-insulation test reports (reportlab renderer).

Renders the two ISO 15186-1:2000 sound-intensity insulation quantities of
:mod:`phonometry.building.intensity_insulation` to the one-page laboratory
test report of the standard's Clause 8, laid out like the accredited
laboratory reports rated per ISO 717-1:

* :class:`~phonometry.building.intensity_insulation.IntensityReductionResult`
  to the intensity sound reduction index ``RI`` (Clause 3.8, Formula (7)); its
  single-number rating ``RI,w`` is the ordinary ISO 717-1 airborne rating
  evaluated on the intensity spectrum. The verbose table annexes the
  Kc-modified index ``RI,M`` (Clause 3.10, Formula (9)) beside ``RI``.
* :class:`~phonometry.building.intensity_insulation.IntensityElementNormalizedResult`
  to the element-normalized level difference ``DI,n,e`` for small building
  elements (Clause 3.9, Formula (8)), rated ``DI,n,e,w`` by the same ISO 717-1
  airborne machinery; its verbose table shows the ISO 717 evaluation per band.

Both quantities are ISO 717-1-rated insulation curves, so the shared two-panel
skeleton (title and basis line, optional metadata header, per-band table
beside the measured-versus-shifted-reference curve, boxed single-number
rating, method statement, optional verdict, footer) of :mod:`._insulation_fiche`
is reused unchanged. This module only holds the ISO 15186 specifics: the fixed
labels and the intensity-method statements.

reportlab, matplotlib and svglib are soft dependencies imported lazily by the
shared renderer (reportlab and svglib ship in the ``phonometry[report]``
extra, matplotlib in ``phonometry[plot]``); each is guarded with an actionable
:class:`ImportError`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Sequence, Tuple

import numpy as np

from ._i18n import t
from ._insulation_fiche import (
    Column,
    iso717_columns_builder,
    render_insulation_fiche,
)
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..building.insulation import WeightedRatingResult
    from ..building.intensity_insulation import (
        IntensityElementNormalizedResult,
        IntensityReductionResult,
    )

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

        # ISO 717-1 Clause 4.4 requires stating whether the rating came from
        # one-third-octave or octave bands; both the plain and the verbose
        # caption declare the set (the verbose one also names the RI,M column).
        is_octave = np.asarray(rating.band_centers).size == 5
        if verbose and modified is not None:
            columns: List[Column] = [
                (value_header, curve, 1),
                (
                    t("R<sub>I,M</sub> [dB]", language),
                    np.asarray(modified, dtype=np.float64),
                    1,
                ),
            ]
            caption_key = (
                "Octave-band {vh} and Kc-modified index"
                if is_octave
                else "One-third-octave {vh} and Kc-modified index"
            )
            caption = t(caption_key, language).format(vh=_SPEC["symbol"])
            col_widths = [12 * mm] + [22 * mm for _ in columns]
            return columns, caption, col_widths
        caption_key = (
            "Octave-band {vh} [dB]"
            if is_octave
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


#: Fixed labels for the element-normalized level difference fiche. The quantity
#: ``DI,n,e`` (Clause 3.9, Formula (8)) is an ISO 717-1-rated level difference
#: for small building elements, so it feeds the shared skeleton exactly like
#: the reduction-index fiche above, differing only in these labels and its
#: intensity-method statement.
_DINE_SPEC: dict[str, str] = {
    "title": "Element sound insulation by sound intensity",
    "basis": (
        "Element-normalized level difference D<sub>I,n,e</sub> measured in "
        "accordance with ISO 15186-1:2000 (transmitted sound power measured "
        "directly with an intensity probe, normalized to the reference "
        "absorption area A<sub>0</sub> = 10 m<sup>2</sup>). Rating per "
        "ISO 717-1:2020."
    ),
    "symbol": "D<sub>I,n,e</sub>",
    "rating_symbol": "D<sub>I,n,e,w</sub>",
    "ylabel": "$D_{I,n,e}$ [dB]",
    "statement": (
        "Evaluation based on laboratory measurement results obtained by the "
        "sound-intensity method (transmitted sound power measured directly "
        "over the measurement surface enclosing the element)."
    ),
}


def render_iso15186_element_report(
    result: "IntensityElementNormalizedResult",
    rating: "WeightedRatingResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an ISO 15186-1 element-normalized insulation report to a PDF.

    :param result: The element result
        (:class:`~phonometry.building.intensity_insulation.IntensityElementNormalizedResult`)
        carrying the per-band element-normalized level difference ``DI,n,e``.
    :param rating: The ISO 717-1 rating of the reported ``DI,n,e`` (the
        result's own ``rating``); its ``plot`` draws the fiche curve.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        lightweight fiche (body, rating, statement and disclaimer).
    :param verbose: When ``True``, the left table shows the ISO 717 evaluation
        per band (the ``DI,n,e`` value, the shifted reference and the
        unfavourable deviation) instead of the two-column form.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    # ISO 717-1 Clause 4.4 requires the table caption to state the band set;
    # the rating carries 5 centres for octave bands, 16 for one-third octaves.
    band_set = (
        "Octave-band"
        if np.asarray(rating.band_centers).size == 5
        else "One-third-octave"
    )
    return render_insulation_fiche(
        result, rating, path,
        spec=_DINE_SPEC,
        is_impact=False,
        curve_attr="d_i_n_e",
        build_columns=iso717_columns_builder(
            rating, False, _DINE_SPEC["symbol"], band_set=band_set
        ),
        metadata=metadata,
        verbose=verbose,
        language=language,
    )
