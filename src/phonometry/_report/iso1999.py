#  Copyright (c) 2026. Jose M. Requena-Plens
"""ISO 1999:2013 noise-induced hearing-loss prediction fiches (reportlab renderer).

Renders the two occupational-hearing-loss result types of
:mod:`phonometry.hearing.noise_induced_hearing_loss` to one-page PDFs laid out
like a statistical hearing-damage prediction sheet. Both quantities are
population estimates over the six ISO 1999 audiometric frequencies (500 Hz to
6000 Hz), not clinical measurements, so the fiches read as predictions:

* :class:`~phonometry.hearing.noise_induced_hearing_loss.NiptsResult` renders
  the noise-induced permanent threshold shift (NIPTS, clause 6.3): a
  per-audiometric-frequency table of the median ``N50`` (Formula 2/3) and the
  NIPTS at the chosen population fractile (Formula 4/5) beside the result's own
  spectrum plot, the boxed representative shift averaged over the 2/3/4 kHz
  hearing-handicap set, and the exposure conditions (``L_EX,8h``, exposure
  years, fractile); ``verbose=True`` adds the upper/lower spread columns
  (``du``/``dl``, Formulae 6/7);
* :class:`~phonometry.hearing.noise_induced_hearing_loss.HtlanResult` renders
  the hearing threshold level associated with age and noise (HTLAN, clause 6.1):
  a per-audiometric-frequency table of the age component ``H`` (HTLA, database
  A = ISO 7029), the noise component ``N`` (NIPTS) and the combined threshold
  ``H' = H + N - H*N/120`` (Formula 1) beside the plot, the boxed representative
  threshold averaged over the 2/3/4 kHz set, and the listener/exposure
  conditions; ``verbose=True`` adds the compression term ``H*N/120``.

A metadata ``requirement`` (a maximum acceptable representative value in dB)
adds a PASS/FAIL verdict; without it the fiche prints no verdict, since neither
quantity carries a normative limit of its own. The quantity-independent
skeleton lives in :mod:`._layout`; this module holds the ISO 1999 specifics.
reportlab, matplotlib and svglib are soft dependencies imported lazily
(reportlab and svglib ship in the ``phonometry[report]`` extra, matplotlib in
``phonometry[plot]``); each is guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any, List, Tuple

import numpy as np

from ._i18n import decimal_comma, format_number, t
from ._layout import (
    _ACCENT_HEX,
    _REPORTLAB_HINT,
    analysis_cell_styles,
    build_document,
    display_round,
    document_styles,
    footer_flow,
    fmt_num,
    grid_table,
    render_figure_drawing,
    result_box,
    stacked_table,
    two_panel_body,
    verdict_flow,
)
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..hearing.noise_induced_hearing_loss import HtlanResult, NiptsResult

#: The 2/3/4 kHz hearing-handicap audiometric set, in hertz. The mean threshold
#: shift over these three frequencies is the descriptor most occupational
#: schemes use as a single hearing-damage index.
_HANDICAP_SET: Tuple[float, float, float] = (2000.0, 3000.0, 4000.0)

#: The compression-term denominator of the HTLAN Formula (1).
_HTLAN_DENOM = 120.0


def _fmt_db(value: float, language: str = "en") -> str:
    """A threshold shift or level rounded to one decimal place."""
    return format_number(display_round(float(value)), language, decimals=1)


def _fmt_freq(value: float, language: str = "en") -> str:
    """An audiometric frequency in hertz, as an integer (500 ... 6000)."""
    return format_number(round(float(value)), language, decimals=0)


def _esc(value: str | None) -> str | None:
    """HTML-escape an optional free-text metadata value."""
    return html.escape(value) if value else None


def _handicap_indices(frequencies: np.ndarray) -> List[int]:
    """Indices of the 2/3/4 kHz hearing-handicap frequencies present in the set."""
    return [
        i
        for i, f in enumerate(frequencies)
        if any(abs(float(f) - h) < 1e-6 for h in _HANDICAP_SET)
    ]


def _representative(
    frequencies: np.ndarray, values: np.ndarray
) -> Tuple[bool, float, float]:
    """Return the representative shift/level and whether it is the 2/3/4 kHz mean.

    When all three hearing-handicap frequencies are present the representative
    value is their arithmetic mean and the flag is ``True``; otherwise it falls
    back to the peak value across the available frequencies (flag ``False``),
    reported together with its frequency.
    """
    vals = np.asarray(values, dtype=np.float64)
    idx = _handicap_indices(frequencies)
    if len(idx) == 3:
        return True, float(vals[idx].mean()), 0.0
    peak = int(np.argmax(vals))
    return False, float(vals[peak]), float(frequencies[peak])


def _fractile_phrase(fractile: float, language: str = "en") -> str:
    """A short gloss of the population fractile for the exposure conditions."""
    q = decimal_comma(f"{fractile:g}", language)
    if abs(fractile - 0.5) < 1e-9:
        return t("Population fractile Q = {q} (median)", language).format(q=q)
    return t("Population fractile Q = {q}", language).format(q=q)


# --------------------------------------------------------------------------- #
# NIPTS fiche.
# --------------------------------------------------------------------------- #
def _nipts_metadata_pairs(
    metadata: ReportMetadata | None, language: str = "en"
) -> List[Tuple[str, str]]:
    """The (label, value) header-grid pairs of a NIPTS/HTLAN fiche."""
    if metadata is None:
        return []
    specs: List[Tuple[str, str | None]] = [
        (t("Company", language), _esc(metadata.client)),
        (t("Worker(s) / group", language), _esc(metadata.specimen)),
        (t("Workplace", language), _esc(metadata.test_room)),
        (t("Date of assessment", language), _esc(metadata.test_date)),
    ]
    return [(label, value) for label, value in specs if value]


def _nipts_table(
    result: "NiptsResult", verbose: bool = False, language: str = "en"
) -> Any:
    """The per-audiometric-frequency NIPTS table (median and fractile value)."""
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph

    header_style, label_style, value_style = analysis_cell_styles("iso1999n")

    headers = [
        t("Frequency [Hz]", language),
        "N<sub>50</sub> [dB]",
        t("NIPTS [dB]", language),
    ]
    widths = [24.0, 21.0, 21.0]
    if verbose:
        headers += ["d<sub>u</sub> [dB]", "d<sub>l</sub> [dB]"]
        widths = [22.0, 18.0, 18.0, 19.0, 19.0]

    data: List[List[Any]] = [[Paragraph(h, header_style) for h in headers]]
    for i, freq in enumerate(result.frequencies):
        row = [
            Paragraph(_fmt_freq(float(freq), language), label_style),
            Paragraph(_fmt_db(float(result.median[i]), language), value_style),
            Paragraph(_fmt_db(float(result.value[i]), language), value_style),
        ]
        if verbose:
            row += [
                Paragraph(_fmt_db(float(result.spread_upper[i]), language), value_style),
                Paragraph(_fmt_db(float(result.spread_lower[i]), language), value_style),
            ]
        data.append(row)

    return stacked_table(data, [w * mm for w in widths])


def _nipts_statement(result: "NiptsResult", language: str = "en") -> Tuple[str, List[str]]:
    """The boxed representative NIPTS statement and the exposure-condition terms."""
    is_handicap, value, freq = _representative(result.frequencies, result.value)
    if is_handicap:
        statement = t(
            "Predicted NIPTS averaged over 2/3/4 kHz = <b>{value} dB</b>",
            language,
        ).format(value=_fmt_db(value, language))
    else:
        statement = t(
            "Predicted peak NIPTS = <b>{value} dB</b> at {freq} Hz",
            language,
        ).format(value=_fmt_db(value, language), freq=_fmt_freq(freq, language))
    extended = [
        t("Noise exposure L<sub>EX,8h</sub> = {lex} dB", language).format(
            lex=decimal_comma(f"{result.l_ex:g}", language)
        ),
        t("Exposure duration = {years} years", language).format(
            years=decimal_comma(f"{result.years:g}", language)
        ),
        _fractile_phrase(result.fractile, language),
    ]
    return statement, extended


def _nipts_verdict(
    result: "NiptsResult", requirement: float, language: str = "en"
) -> Tuple[str, bool]:
    """Verdict text and PASS flag: the representative NIPTS at or below a maximum.

    The requirement is read as the maximum acceptable representative NIPTS (a
    lower shift is better); the comparison uses the displayed one-decimal value,
    so the printed number can never contradict the verdict.
    """
    _, value, _ = _representative(result.frequencies, result.value)
    passed = display_round(value) <= requirement + 1e-9
    text = t(
        "representative NIPTS = {value} dB, maximum {req} dB",
        language,
    ).format(value=_fmt_db(value, language), req=fmt_num(requirement, language))
    return text, passed


def render_nipts_report(
    result: "NiptsResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render a NIPTS prediction fiche to a PDF at ``path`` (ISO 1999:2013, 6.3).

    :param result: A
        :class:`~phonometry.hearing.noise_induced_hearing_loss.NiptsResult`.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata` supplying the header
        identity (``client`` is the company, ``specimen`` the worker(s)/group,
        ``test_room`` the workplace) and, via ``requirement``, a maximum
        acceptable representative NIPTS that adds a PASS/FAIL verdict.
    :param verbose: When True, the table adds the upper/lower spread columns.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab, matplotlib or svglib is not installed.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title = t("Noise-induced hearing loss prediction", language)
    basis = t(
        "Statistical prediction of the noise-induced permanent threshold shift "
        "of a noise-exposed population per ISO 1999:2013 (clause 6.3).",
        language,
    )

    flow: List[Any] = [
        Paragraph(title, title_style),
        Paragraph(basis, basis_style),
    ]

    header_pairs = _nipts_metadata_pairs(metadata, language)
    if header_pairs:
        flow.append(Spacer(1, 3))
        flow.append(grid_table(header_pairs))
    flow.append(Spacer(1, 8))

    left_cell = [
        Paragraph(t("Threshold shift by frequency", language), caption_style),
        _nipts_table(result, verbose, language),
    ]
    left_width = 96.0 if verbose else 66.0
    plot_drawing = render_figure_drawing(
        result.plot, (174.0 - left_width) * mm, y_top=None,
        figsize=(5.4, 4.6), language=language,
    )
    flow.append(
        two_panel_body(
            left_cell, plot_drawing,
            left_width_mm=left_width, plot_width_mm=174.0 - left_width,
        )
    )
    flow.append(Spacer(1, 8))

    statement, extended = _nipts_statement(result, language)
    flow.append(result_box(statement, styles, accent, extended))
    if metadata is not None and metadata.requirement is not None:
        text, passed = _nipts_verdict(result, metadata.requirement, language)
        flow.extend(verdict_flow(text, passed, styles, language))

    flow.extend(_prediction_notes(caption_style, language))
    flow.extend(footer_flow(metadata, language))

    return build_document(path, flow, title)


# --------------------------------------------------------------------------- #
# HTLAN fiche.
# --------------------------------------------------------------------------- #
def _htlan_table(
    result: "HtlanResult", verbose: bool = False, language: str = "en"
) -> Any:
    """The per-audiometric-frequency HTLAN table (age, noise and combined)."""
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph

    header_style, label_style, value_style = analysis_cell_styles("iso1999h")

    headers = [
        t("Frequency [Hz]", language),
        "H [dB]",
        "N [dB]",
        "H&#8242; [dB]",
    ]
    widths = [22.0, 17.0, 17.0, 18.0]
    if verbose:
        headers.insert(3, "H&#183;N/120 [dB]")
        widths = [20.0, 16.0, 16.0, 20.0, 20.0]

    data: List[List[Any]] = [[Paragraph(h, header_style) for h in headers]]
    for i, freq in enumerate(result.frequencies):
        h = float(result.htla[i])
        n = float(result.nipts[i])
        row = [
            Paragraph(_fmt_freq(float(freq), language), label_style),
            Paragraph(_fmt_db(h, language), value_style),
            Paragraph(_fmt_db(n, language), value_style),
        ]
        if verbose:
            row.append(Paragraph(_fmt_db(h * n / _HTLAN_DENOM, language), value_style))
        row.append(Paragraph(_fmt_db(float(result.threshold[i]), language), value_style))
        data.append(row)

    return stacked_table(data, [w * mm for w in widths])


def _htlan_statement(result: "HtlanResult", language: str = "en") -> Tuple[str, List[str]]:
    """The boxed representative HTLAN statement and the listener/exposure terms."""
    is_handicap, value, freq = _representative(result.frequencies, result.threshold)
    if is_handicap:
        statement = t(
            "Predicted hearing threshold level (age and noise) averaged over "
            "2/3/4 kHz = <b>{value} dB HL</b>",
            language,
        ).format(value=_fmt_db(value, language))
    else:
        statement = t(
            "Predicted peak hearing threshold level (age and noise) = "
            "<b>{value} dB HL</b> at {freq} Hz",
            language,
        ).format(value=_fmt_db(value, language), freq=_fmt_freq(freq, language))
    sex = t(result.sex, language)
    extended = [
        t("Listener: {sex}, age {age} years", language).format(
            sex=sex, age=decimal_comma(f"{result.age:g}", language)
        ),
        t("Noise exposure L<sub>EX,8h</sub> = {lex} dB over {years} years", language).format(
            lex=decimal_comma(f"{result.l_ex:g}", language),
            years=decimal_comma(f"{result.years:g}", language),
        ),
        _fractile_phrase(result.fractile, language),
    ]
    return statement, extended


def _htlan_verdict(
    result: "HtlanResult", requirement: float, language: str = "en"
) -> Tuple[str, bool]:
    """Verdict text and PASS flag: the representative HTLAN at or below a maximum."""
    _, value, _ = _representative(result.frequencies, result.threshold)
    passed = display_round(value) <= requirement + 1e-9
    text = t(
        "representative HTLAN = {value} dB HL, maximum {req} dB HL",
        language,
    ).format(value=_fmt_db(value, language), req=fmt_num(requirement, language))
    return text, passed


def render_htlan_report(
    result: "HtlanResult",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an HTLAN prediction fiche to a PDF at ``path`` (ISO 1999:2013, 6.1).

    :param result: A
        :class:`~phonometry.hearing.noise_induced_hearing_loss.HtlanResult`.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata` supplying the header
        identity and, via ``requirement``, a maximum acceptable representative
        HTLAN that adds a PASS/FAIL verdict.
    :param verbose: When True, the table adds the compression term ``H*N/120``.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab, matplotlib or svglib is not installed.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, Spacer
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc
    accent = colors.HexColor(_ACCENT_HEX)

    styles, title_style, basis_style, caption_style = document_styles(accent)
    title = t("Hearing threshold level prediction (age and noise)", language)
    basis = t(
        "Statistical prediction of the hearing threshold level associated with "
        "age and noise per ISO 1999:2013 (clause 6.1).",
        language,
    )

    flow: List[Any] = [
        Paragraph(title, title_style),
        Paragraph(basis, basis_style),
    ]

    header_pairs = _nipts_metadata_pairs(metadata, language)
    if header_pairs:
        flow.append(Spacer(1, 3))
        flow.append(grid_table(header_pairs))
    flow.append(Spacer(1, 8))

    left_cell = [
        Paragraph(t("Threshold level by frequency", language), caption_style),
        _htlan_table(result, verbose, language),
    ]
    left_width = 92.0 if verbose else 74.0
    plot_drawing = render_figure_drawing(
        result.plot, (174.0 - left_width) * mm, y_top=None,
        figsize=(5.4, 4.6), language=language,
    )
    flow.append(
        two_panel_body(
            left_cell, plot_drawing,
            left_width_mm=left_width, plot_width_mm=174.0 - left_width,
        )
    )
    flow.append(Spacer(1, 8))

    statement, extended = _htlan_statement(result, language)
    flow.append(result_box(statement, styles, accent, extended))
    if metadata is not None and metadata.requirement is not None:
        text, passed = _htlan_verdict(result, metadata.requirement, language)
        flow.extend(verdict_flow(text, passed, styles, language))

    flow.extend(_prediction_notes(caption_style, language))
    flow.extend(footer_flow(metadata, language))

    return build_document(path, flow, title)


def _prediction_notes(caption_style: Any, language: str = "en") -> List[Any]:
    """The shared statistical-prediction notes of the ISO 1999 fiches."""
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph

    from ._layout import _MUTED_HEX

    note_style = ParagraphStyle(
        "iso1999_notes", parent=getSampleStyleSheet()["Normal"],
        fontSize=7.5, leading=10, textColor=colors.HexColor(_MUTED_HEX),
        spaceBefore=6,
    )
    return [
        Paragraph(
            t(
                "These values are a statistical prediction for a noise-exposed "
                "population (ISO 1999:2013), not a clinical diagnosis or a "
                "measured audiogram of any individual.",
                language,
            ),
            note_style,
        ),
        Paragraph(
            t(
                "The population fractile Q is the fraction of the noise-exposed "
                "population predicted to show a smaller threshold shift, so a "
                "higher fractile is a more-susceptible individual "
                "(ISO 1999:2013, 6.3.2).",
                language,
            ),
            note_style,
        ),
    ]
