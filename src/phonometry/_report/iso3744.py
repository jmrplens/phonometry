#  Copyright (c) 2026. Jose M. Requena-Plens
"""Sound power determination fiche (reportlab renderer, ISO 3744 / ISO 3745).

Renders a :class:`~phonometry.emission.sound_power.SoundPowerResult`
(enveloping-surface pressure method, ISO 3744:2010 engineering grade 2 or
ISO 3746:2010 survey grade 3) or a
:class:`~phonometry.emission.sound_power.PrecisionSoundPowerResult`
(precision method in an anechoic or hemi-anechoic room, ISO 3745:2012 grade 1)
to a one-page PDF laid out like a sound-power test sheet:

* a title and the standard-basis line naming the applied method and accuracy
  grade;
* an optional metadata header grid (client, noise source, test environment,
  instrumentation, climate, date), rendered only for the fields supplied on
  the :class:`ReportMetadata`;
* a full-width per-band table (nominal octave/one-third-octave frequency, the
  surface sound-pressure level ``Lp`` and the band sound-power level ``LW``),
  grouped by octave for a one-third-octave set; with ``verbose=True`` the table
  adds the energy-averaged level ``Lp'`` and the applied corrections (the
  background ``K1`` and environmental ``K2`` for the ISO 3744/3746 surface
  method);
* the sound-power spectrum ``LW(f)`` drawn by the result's own ``plot(ax=...)``
  (band axis with nominal labels), so the chart is native to the library;
* a boxed single-number result, the A-weighted sound power level ``LWA``
  (dB re 1 pW) with the total ``LW``, the expanded uncertainty ``U`` and the
  measurement surface area ``S`` alongside;
* an optional verdict row when a declared limit is supplied via the metadata
  ``requirement`` (a sound-power emission passes at or below the limit);
* a short measurement-basis strip stating the correction model and the applied
  ``K1``/``K2`` (surface method) or ``C1``/``C2``/``C3`` (precision method),
  and a footer identity/disclaimer block.

Like the room-acoustics and exposure fiches this uses a stacked layout (the
per-band table spans the full content width, the spectrum sits below it as a
landscape bar chart). The quantity-independent skeleton lives in
:mod:`._layout`; this module only holds the sound-power specifics. reportlab,
matplotlib and svglib are soft dependencies imported lazily (reportlab and
svglib ship in the ``phonometry[report]`` extra, matplotlib in
``phonometry[plot]``); each is guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

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
    footer_flow,
    grid_table,
    measurement_basis_style,
    render_figure_drawing,
    result_box,
    verdict_flow,
)
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..emission.sound_power import (
        PrecisionSoundPowerResult,
        SoundPowerResult,
    )

#: Reference sound power for the sound power level, 1 pW = 10^-12 W.
_POWER_REFERENCE = "1 pW"


def _is_precision(result: Any) -> bool:
    """Return ``True`` for an ISO 3745 precision result, ``False`` for ISO 3744.

    The precision result carries the meteorological corrections ``c1``/``c2``/
    ``c3`` (and no environmental ``K2``); the surface-pressure result carries
    the per-band ``environmental_correction`` (``K2``) and a ``grade``. The
    duck-typed check keeps this module free of a module-level import of the
    domain classes (the render layer imports them only under TYPE_CHECKING).
    """
    return hasattr(result, "c1") and hasattr(result, "c2") and hasattr(result, "c3")


def _method(result: Any, language: str = "en") -> Tuple[str, str]:
    """Return ``(standard, grade_phrase)`` for the applied determination method.

    ISO 3744:2010 is the engineering method (accuracy grade 2), ISO 3746:2010
    the survey method (grade 3) and ISO 3745:2012 the precision method
    (grade 1). The surface result distinguishes engineering from survey by its
    ``grade`` attribute.
    """
    if _is_precision(result):
        return "ISO 3745:2012", t("precision method, accuracy grade 1", language)
    if getattr(result, "grade", "engineering") == "survey":
        return "ISO 3746:2010", t("survey method, accuracy grade 3", language)
    return "ISO 3744:2010", t("engineering method, accuracy grade 2", language)


def _basis(result: Any, language: str = "en") -> str:
    """The standard-basis line naming the method, the surface and the grade."""
    standard, grade_phrase = _method(result, language)
    if _is_precision(result):
        return t(
            "Determination of the sound power level from sound pressure over an "
            "enveloping measurement surface in an anechoic or hemi-anechoic "
            "room ({standard}, {grade}).",
            language,
        ).format(standard=standard, grade=grade_phrase)
    return t(
        "Determination of the sound power level from sound pressure over an "
        "enveloping measurement surface ({standard}, {grade}).",
        language,
    ).format(standard=standard, grade=grade_phrase)


def _metadata_pairs(
    metadata: ReportMetadata, language: str = "en"
) -> List[Tuple[str, str]]:
    """Build the ordered (label, value) pairs of the sound-power header grid.

    Only supplied fields are returned. ``specimen`` names the noise source and
    ``test_room`` the test environment; the measurement surface area ``S`` is
    the result's own computed value, so it is shown in the result box and the
    basis strip rather than trusted from the metadata.
    """
    specs: List[Tuple[str, str | None]] = [
        (t("Client", language), metadata.client),
        (t("Noise source", language), metadata.specimen),
        (t("Test environment", language), metadata.test_room),
        (t("Instrumentation", language), metadata.instrumentation),
        (t("Temperature [&#176;C]", language), _num(metadata.temperature, language)),
        (
            t("Relative humidity [%]", language),
            _num(metadata.relative_humidity, language),
        ),
        (t("Ambient pressure [kPa]", language), _num(metadata.pressure, language)),
        (t("Date of test", language), metadata.test_date),
    ]
    return escaped_pairs(specs)


def _num(value: float | None, language: str = "en") -> str | None:
    """Round-trip a client-supplied metadata number, or ``None`` when unset."""
    from ._layout import fmt_meta

    return fmt_meta(value, language) if value is not None else None


def _band_labels(frequencies: np.ndarray | None, n: int) -> Tuple[List[str], int]:
    """Return the nominal band labels and the band fraction (1, 3 or 0).

    A per-band result is labelled by its nominal octave/one-third-octave
    mid-band frequency (IEC 61260), not the exact base-ten centre, matching the
    band axis of the embedded spectrum. A result without band frequencies
    (a directly measured broadband level) is labelled ``Band 1``, ``Band 2``,
    ... and reports fraction ``0`` (no octave grouping).
    """
    if frequencies is None:
        return [f"Band {i + 1}" for i in range(n)], 0
    from ..metrology.frequencies import _infer_band_fraction, _nominal_freq_for_band

    freqs = np.asarray(frequencies, dtype=np.float64)
    fraction = _infer_band_fraction(freqs) if freqs.size >= 2 else 1
    labels = [f"{_nominal_freq_for_band(f, float(fraction)):g}" for f in freqs]
    return labels, fraction


def _d1(value: float, language: str = "en") -> str:
    """One decimal place, locale-aware separator; em dash when not finite."""
    if not math.isfinite(float(value)):
        return "—"
    return format_number(float(value), language, decimals=1)


def _value_table(result: Any, verbose: bool, language: str = "en") -> Any:
    """Build the full-width per-band table (nominal frequency, Lp, LW).

    ``verbose`` adds the energy-averaged level ``Lp'`` and, for the ISO 3744/
    3746 surface method, the background ``K1`` and environmental ``K2``
    corrections. A one-third-octave set is grouped by octave with a thin rule
    after every triplet. Called only after the renderer has imported reportlab.
    """
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle

    accent = colors.HexColor(_ACCENT_HEX)
    light = colors.HexColor(_LIGHT_HEX)
    thin = colors.HexColor("#c9d4e0")
    styles = getSampleStyleSheet()
    head_style = ParagraphStyle(
        "iso3744_thead", parent=styles["Normal"], fontSize=7.6,
        textColor=colors.white, alignment=1, leading=9.0,
    )

    lw = np.asarray(result.sound_power_level, dtype=np.float64)
    lp = np.asarray(result.surface_pressure_level, dtype=np.float64)
    lp_mean = np.asarray(result.mean_pressure_level, dtype=np.float64)
    n = lw.size
    labels, fraction = _band_labels(getattr(result, "frequencies", None), n)

    precision = _is_precision(result)
    if verbose and not precision:
        k1 = np.asarray(result.background_correction, dtype=np.float64)
        k2 = np.asarray(result.environmental_correction, dtype=np.float64)
        header = [
            t("f [Hz]", language),
            "L'<sub>p</sub> [dB]",
            "K<sub>1</sub> [dB]",
            "K<sub>2</sub> [dB]",
            "L<sub>p</sub> [dB]",
            "L<sub>W</sub> [dB]",
        ]
        widths = [30.0, 29.0, 29.0, 29.0, 29.0, 28.0]
        rows_data = [
            [labels[i], _d1(lp_mean[i], language), _d1(k1[i], language),
             _d1(k2[i], language), _d1(lp[i], language), _d1(lw[i], language)]
            for i in range(n)
        ]
    elif verbose and precision:
        header = [
            t("f [Hz]", language),
            "L'<sub>p</sub> [dB]",
            "L<sub>p</sub> [dB]",
            "L<sub>W</sub> [dB]",
        ]
        widths = [45.0, 43.0, 43.0, 43.0]
        rows_data = [
            [labels[i], _d1(lp_mean[i], language), _d1(lp[i], language),
             _d1(lw[i], language)]
            for i in range(n)
        ]
    else:
        header = [
            t("f [Hz]", language),
            "L<sub>p</sub> [dB]",
            "L<sub>W</sub> [dB]",
        ]
        widths = [58.0, 58.0, 58.0]
        rows_data = [
            [labels[i], _d1(lp[i], language), _d1(lw[i], language)]
            for i in range(n)
        ]

    rows: List[List[Any]] = [[Paragraph(h, head_style) for h in header]]
    rows.extend(rows_data)

    style_cmds: List[Any] = [
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, accent),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
        ("BOX", (0, 0), (-1, -1), 0.5, accent),
    ]
    # A one-third-octave set groups by octave (a thin rule after every triplet),
    # as accredited sound-power tables print it; an octave set has no triplets.
    if fraction == 3:
        for triplet_end in range(3, n, 3):
            style_cmds.append(
                ("LINEBELOW", (0, triplet_end), (-1, triplet_end), 0.4, thin)
            )
    table = Table(rows, colWidths=[w * mm for w in widths], repeatRows=1)
    table.setStyle(TableStyle(style_cmds))
    table.hAlign = "CENTER"
    return table


def _total_power_level(result: Any) -> float:
    """Energy sum of the band sound-power levels, ``10 lg(sum 10^(LW/10))`` dB."""
    lw = np.asarray(result.sound_power_level, dtype=np.float64)
    finite = lw[np.isfinite(lw)]
    if finite.size == 0:
        return float("nan")
    return float(10.0 * np.log10(np.sum(10.0 ** (finite / 10.0))))


def _statement(result: Any, language: str = "en") -> Tuple[str, List[str]]:
    """The boxed sound-power result and its extended terms.

    Boxes the A-weighted sound power level ``LWA`` when it is defined (band
    frequencies were supplied); otherwise the energy-summed total ``LW``. The
    extended terms carry the total ``LW``, the expanded uncertainty ``U`` and
    the measurement surface area ``S``.
    """
    lwa = float(result.sound_power_level_a)
    total = _total_power_level(result)
    surface = float(result.surface_area)
    uncertainty = float(result.uncertainty)

    extended: List[str] = []
    if math.isfinite(lwa):
        statement = t(
            "Sound power level L<sub>WA</sub> = <b>{lwa} dB(A)</b> re {ref}",
            language,
        ).format(lwa=_d1(lwa, language), ref=_POWER_REFERENCE)
        if math.isfinite(total):
            extended.append(
                t("Total L<sub>W</sub> = {value} dB re {ref}", language).format(
                    value=_d1(total, language), ref=_POWER_REFERENCE
                )
            )
    else:
        statement = t(
            "Sound power level L<sub>W</sub> = <b>{value} dB</b> re {ref}",
            language,
        ).format(value=_d1(total, language), ref=_POWER_REFERENCE)
    extended.append(
        t("Expanded uncertainty U = {value} dB", language).format(
            value=_d1(uncertainty, language)
        )
    )
    extended.append(
        t("Measurement surface S = {value} m<super>2</super>", language).format(
            value=format_number(surface, language, decimals=2)
        )
    )
    return statement, extended


def _headline_level(result: Any) -> float:
    """The single number the verdict compares: ``LWA`` if defined, else total ``LW``."""
    lwa = float(result.sound_power_level_a)
    return lwa if math.isfinite(lwa) else _total_power_level(result)


def _verdict(result: Any, requirement: float, language: str = "en") -> Tuple[str, bool]:
    """Verdict text and PASS flag against a declared sound-power limit.

    A sound-power emission is a quantity where less is better, so the source
    passes when its A-weighted level (or total ``LW`` when no band frequencies
    were supplied) is at or below the declared limit. The comparison uses the
    displayed (one-decimal) value so the printed number cannot contradict the
    verdict at the boundary.
    """
    from ._layout import display_round

    value = _headline_level(result)
    weighted = math.isfinite(float(result.sound_power_level_a))
    passed = math.isfinite(value) and display_round(value) <= requirement
    if weighted:
        text = t(
            "L<sub>WA</sub> = {value} dB(A), declared limit &#8804; {req} dB(A)",
            language,
        ).format(
            value=_d1(value, language),
            req=format_number(requirement, language, decimals=1),
        )
    else:
        text = t(
            "L<sub>W</sub> = {value} dB, declared limit &#8804; {req} dB",
            language,
        ).format(
            value=_d1(value, language),
            req=format_number(requirement, language, decimals=1),
        )
    return text, passed


def _range_str(values: np.ndarray, language: str = "en") -> str:
    """Format a per-band correction as a single value or a ``a to b`` range."""
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return "—"
    lo, hi = float(np.min(arr)), float(np.max(arr))
    if abs(hi - lo) < 0.05:
        return f"{format_number(lo, language, decimals=1)}"
    return t("{lo} to {hi}", language).format(
        lo=format_number(lo, language, decimals=1),
        hi=format_number(hi, language, decimals=1),
    )


def _corrections_strip(result: Any, language: str = "en") -> str:
    """The applied-corrections line for the basis strip (K1/K2 or C1/C2/C3)."""
    if _is_precision(result):
        return t(
            "L<sub>W</sub> = L<sub>p</sub> + 10 lg(S/S<sub>0</sub>) + C1 + C2 + "
            "C3, S<sub>0</sub> = 1 m<super>2</super> (ISO 3745:2012 Eq. 14/15). "
            "Applied meteorological corrections C1 = {c1} dB, C2 = {c2} dB, "
            "C3 = {c3} dB.",
            language,
        ).format(
            c1=format_number(float(result.c1), language, decimals=2),
            c2=format_number(float(result.c2), language, decimals=2),
            c3=_range_str(np.atleast_1d(np.asarray(result.c3, dtype=np.float64)), language),
        )
    return t(
        "Surface level L<sub>p</sub> is the energy average over the microphone "
        "positions corrected for background noise (K1, ISO 3744:2010 Eq. 16) "
        "and the test environment (K2, Eq. A.2); L<sub>W</sub> = L<sub>p</sub> "
        "+ 10 lg(S/S<sub>0</sub>), S<sub>0</sub> = 1 m<super>2</super> "
        "(Eq. 18). Applied corrections K1 = {k1} dB, K2 = {k2} dB.",
        language,
    ).format(
        k1=_range_str(np.asarray(result.background_correction, dtype=np.float64), language),
        k2=_range_str(np.asarray(result.environmental_correction, dtype=np.float64), language),
    )


def _fraction_caption(result: Any, language: str = "en") -> str:
    """The caption declaring the analysis band set above the table."""
    freqs = getattr(result, "frequencies", None)
    n = np.asarray(result.sound_power_level, dtype=np.float64).size
    if freqs is None:
        return t("Sound power levels per band", language)
    _, fraction = _band_labels(freqs, n)
    if fraction == 1:
        return t("Octave-band sound power levels", language)
    return t("One-third-octave-band sound power levels", language)


def render_sound_power_report(
    result: "SoundPowerResult | PrecisionSoundPowerResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render a sound-power determination fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.emission.sound_power.SoundPowerResult`
        (ISO 3744/3746 enveloping-surface pressure method) or a
        :class:`~phonometry.emission.sound_power.PrecisionSoundPowerResult`
        (ISO 3745 precision method) carrying the per-band ``sound_power_level``,
        ``surface_pressure_level`` and A-weighted total.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a bare
        fiche (body + result + disclaimer, no header). A supplied
        ``requirement`` is read as the declared A-weighted sound-power limit.
    :param verbose: When ``True`` the per-band table adds the energy-averaged
        level ``Lp'`` and the applied corrections (``K1``/``K2`` for the
        surface method).
    :param language: Fiche language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figure, matplotlib) is not
        installed.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title = t("Sound power determination", language)

    flow: List[Any] = [
        Paragraph(title, title_style),
        Paragraph(_basis(result, language), basis_style),
    ]

    if metadata is not None and not metadata.is_empty():
        header_pairs = _metadata_pairs(metadata, language)
        if header_pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(header_pairs))
    flow.append(Spacer(1, 8))

    flow.append(Paragraph(_fraction_caption(result, language), caption_style))
    flow.append(_value_table(result, verbose, language))
    flow.append(Spacer(1, 8))

    # Landscape sound-power spectrum drawn by the result's own single-panel
    # plot(ax=...); the band axis carries nominal labels (not base-ten log).
    flow.append(
        render_figure_drawing(
            result.plot, 174 * mm, y_top=None, figsize=(9.2, 3.4),
            language=language,
        )
    )
    flow.append(Spacer(1, 8))

    statement, extended = _statement(result, language)
    flow.append(result_box(statement, styles, accent, extended))
    if metadata is not None and metadata.requirement is not None:
        text, passed = _verdict(result, metadata.requirement, language)
        flow.extend(verdict_flow(text, passed, styles, language))

    flow.append(
        Paragraph(_corrections_strip(result, language), measurement_basis_style())
    )
    flow.append(
        Paragraph(
            t(
                "The A-weighted sound power level L<sub>WA</sub> combines the "
                "band levels with the A-weighting band corrections of "
                "ISO 3744:2010 Annex E (Tables E.1/E.2, Eq. E.1). Levels are "
                "referenced to the reference sound power 1 pW.",
                language,
            ),
            measurement_basis_style(),
        )
    )
    flow.extend(footer_flow(metadata, language))

    return build_document(path, flow, title)
