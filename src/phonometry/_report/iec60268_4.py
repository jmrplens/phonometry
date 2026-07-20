#  Copyright (c) 2026. Jose M. Requena-Plens
"""IEC 60268-4 microphone-characteristics fiche (reportlab renderer).

Renders a
:class:`~phonometry.electroacoustics.microphone.MicrophoneCharacteristics` to a
one-page PDF laid out like a microphone rated-characteristics data sheet,
following IEC 60268-4:2014:

* a title and the standard-basis line (IEC 60268-4, graphs to IEC 60263:1982);
* an optional metadata header (client, manufacturer, model, room conditions);
* a rated-characteristics table (free-field sensitivity in mV/Pa and its level
  re 1 V/Pa, impedances, equivalent noise level, signal-to-noise ratio,
  overload sound pressure level, directivity index, powering) beside the
  free-field frequency response, the response drawn with a shaded tolerance
  band, the reference-frequency marker and the effective-frequency-range
  markers, to the IEC 60263 25 dB-per-decade scale proportion (clause 2);
* a full-width row of the directional-pattern, the inherent-noise-spectrum and
  the distortion-against-level panels for the data supplied, the polar diagram
  to the IEC 60263 25 dB reference-circle convention (clause 3);
* a boxed sensitivity / effective-range result;
* an optional equivalent-noise verdict when a requirement is supplied; and
* a footer identity/disclaimer block.

The quantity-independent skeleton (metadata grid, table, result box, verdict
styling, footer, document build) lives in :mod:`._layout`, and the graph
helpers shared with the loudspeaker fiche (figure-to-vector conversion, the
frequency-axis formatter, the IEC 60263 polar drawing, the metadata pairs) in
:mod:`.iec60268_5`; this module holds the IEC 60268-4 specifics (labels, the
rated-characteristics table and the microphone characteristic graphs).
reportlab, matplotlib and svglib are soft dependencies imported lazily
(reportlab and svglib ship in the ``phonometry[report]`` extra, matplotlib in
``phonometry[plot]``); each is guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple, cast

import numpy as np

from ._i18n import format_number, t
from ._layout import (
    _ACCENT_HEX,
    _REPORTLAB_HINT,
    build_document,
    document_styles,
    fmt_num,
    footer_flow,
    grid_table,
    metrics_table,
    result_box,
    two_panel_body,
    verdict_flow,
)
from .iec60268_5 import (
    _DB_PER_DECADE,
    _OHM,
    _draw_polar,
    _drawing_from_figure,
    _format_freq_axis,
    _freq,
    _metadata_pairs,
    _range_text,
)
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..electroacoustics.microphone import MicrophoneCharacteristics

#: Ordinate span of the free-field response plot, in dB. One 25 dB span keeps
#: the IEC 60263 25 dB-per-decade grid on whole gridlines and suits the small
#: deviations of a microphone response around its 0 dB reference.
_RESPONSE_SPAN_DB = 25.0


def _basis(metadata: ReportMetadata | None, language: str = "en") -> str:
    """The standard-basis line: IEC 60268-4 with the IEC 60263 graph convention."""
    import html

    standard = metadata.measurement_standard if metadata is not None else None
    if standard:
        return t(
            "{standard} measurement of microphone rated characteristics per "
            "IEC 60268-4:2014; frequency and polar graphs to IEC 60263:1982.",
            language,
        ).format(standard=html.escape(standard))
    return t(
        "Microphone rated characteristics per IEC 60268-4:2014; "
        "frequency and polar graphs to IEC 60263:1982.",
        language,
    )


def _db_1(value: float, language: str = "en") -> str:
    """A level rounded to one decimal, locale-formatted."""
    return format_number(value, language, decimals=1)


def _noise_rows(
    result: "MicrophoneCharacteristics", language: str = "en"
) -> List[Tuple[str, str]]:
    """The equivalent-noise and signal-to-noise table rows, when known."""
    rows: List[Tuple[str, str]] = []
    noise = result.equivalent_noise_level_db
    snr = result.signal_to_noise_ratio_db
    if noise is not None:
        rows.append(
            (
                t("Equivalent noise level", language),
                f"{_db_1(noise, language)} dB({result.noise_weighting})",
            )
        )
    if snr is not None:
        rows.append(
            (
                t("Signal-to-noise ratio", language),
                f"{_db_1(snr, language)} dB({result.noise_weighting})",
            )
        )
    return rows


def _rated_rows(
    result: "MicrophoneCharacteristics", language: str = "en"
) -> List[Tuple[str, str]]:
    """The rated-characteristics table rows (only the quantities that exist)."""
    import html

    rows: List[Tuple[str, str]] = [
        (
            t("Free-field sensitivity", language),
            f"{_db_1(result.sensitivity_mv_per_pa, language)} mV/Pa",
        ),
        (
            t("Level re 1 V/Pa [dB]", language),
            _db_1(result.sensitivity_level_db, language),
        ),
        (
            t("Effective frequency range", language),
            _range_text(*result.effective_range, language=language),
        ),
    ]
    if result.rated_impedance is not None:
        rows.append(
            (
                t("Rated impedance", language),
                f"{fmt_num(result.rated_impedance, language)} {_OHM}",
            )
        )
    if result.minimum_load_impedance is not None:
        rows.append(
            (
                t("Min. load impedance", language),
                f"{fmt_num(result.minimum_load_impedance, language)} {_OHM}",
            )
        )
    rows.extend(_noise_rows(result, language))
    if result.max_spl_db is not None:
        rows.append(
            (
                t("Max. SPL ({thd} % THD)", language).format(
                    thd=fmt_num(result.max_spl_thd_percent, language)
                ),
                f"{_db_1(result.max_spl_db, language)} dB",
            )
        )
    if result.directivity_index_db is not None:
        label = t("Directivity index", language)
        if result.polar_frequency is not None:
            label = t("Directivity index at {freq} Hz", language).format(
                freq=_freq(result.polar_frequency, language)
            )
        rows.append((label, f"{_db_1(result.directivity_index_db, language)} dB"))
    if result.powering is not None:
        rows.append((t("Powering", language), html.escape(result.powering)))
    if result.supply_current_ma is not None:
        rows.append(
            (
                t("Supply current [mA]", language),
                fmt_num(result.supply_current_ma, language),
            )
        )
    return rows


# --------------------------------------------------------------------------- #
# IEC 60263 characteristic graphs
# --------------------------------------------------------------------------- #
def _response_drawing(
    result: "MicrophoneCharacteristics", target_width: float, language: str = "en"
) -> Any:
    """Free-field response with the tolerance band and effective-range markers.

    Plotted to the IEC 60263 clause 2 proportion: one frequency decade equals
    25 dB on the ordinate (:data:`.iec60268_5._DB_PER_DECADE`).
    """
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    f = result.frequencies
    rel = result.response_db
    tol = result.tolerance_db

    fig = Figure(figsize=(5.6, 4.2))
    FigureCanvasAgg(fig)
    ax = fig.subplots()

    top = float(np.ceil((max(float(np.max(rel)), tol) + 2.0) / 5.0) * 5.0)
    bottom = top - _RESPONSE_SPAN_DB
    # The PDF vector backend (svglib) does not preserve alpha, so a translucent
    # fill would render as a solid block that hides the response curve. Draw a
    # pale opaque tolerance band below the curves (zorder=0) instead.
    ax.axhspan(-tol, tol, facecolor="#d3e2f2", edgecolor="none", zorder=0,
               label=t("Tolerance ±{tol} dB", language).format(
                   tol=fmt_num(tol, language)))
    ax.axhline(0.0, color="#1f4e79", lw=0.8, ls="--")
    ax.axvline(result.reference_frequency, color="#555555", lw=0.8, ls=":",
               label=t("Reference frequency", language))
    ax.semilogx(f, rel, color="#1f4e79", lw=1.4,
                label=t("Free-field response", language))
    lo, hi = result.effective_range
    for edge in (lo, hi):
        ax.axvline(edge, color="#1b6e2f", lw=0.9, ls="-.")
    ax.plot([], [], color="#1b6e2f", lw=0.9, ls="-.",
            label=t("Effective range", language))

    ax.set_xlim(float(np.min(f)), float(np.max(f)))
    ax.set_ylim(bottom, top)
    ax.set_xlabel(t("Frequency [Hz]", language))
    ax.set_ylabel(t("Relative response [dB]", language))
    ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.6)
    _format_freq_axis(ax)
    decades = np.log10(float(np.max(f)) / float(np.min(f)))
    ax.set_box_aspect(_RESPONSE_SPAN_DB / (_DB_PER_DECADE * decades))
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2,
              frameon=False, fontsize=7.5)
    fig.tight_layout()
    return _drawing_from_figure(fig, target_width, language)


def _secondary_drawing(
    result: "MicrophoneCharacteristics", target_width: float, language: str = "en"
) -> Any | None:
    """Directional-pattern, noise-spectrum and distortion panels for the data."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    noise_f = result.noise_frequencies
    noise_db = result.noise_band_levels_db
    thd_spl = result.distortion_spl_db
    thd_pct = result.distortion_thd_percent
    has_polar = result.polar_angles_deg is not None
    has_noise = noise_f is not None and noise_db is not None
    has_thd = thd_spl is not None and thd_pct is not None
    panels = int(has_polar) + int(has_noise) + int(has_thd)
    if panels == 0:
        return None

    fig = Figure(figsize=(5.6 * panels / 2.4 + 0.8, 2.35))
    FigureCanvasAgg(fig)
    idx = 1

    if has_polar:
        ax = fig.add_subplot(1, panels, idx, projection="polar")
        # _draw_polar only reads the polar_* attributes, which the microphone
        # result shares field-for-field with the loudspeaker one.
        _draw_polar(ax, cast("Any", result), language)
        idx += 1

    if noise_f is not None and noise_db is not None:
        ax = fig.add_subplot(1, panels, idx)
        ax.semilogx(noise_f, noise_db, color="#1f4e79", lw=1.3)
        ax.set_xlabel(t("Frequency [Hz]", language))
        ax.set_ylabel(t("Band level [dB]", language))
        ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.6)
        ax.set_title(t("Inherent noise spectrum", language), fontsize=8.5)
        _format_freq_axis(ax)
        idx += 1

    if thd_spl is not None and thd_pct is not None:
        ax = fig.add_subplot(1, panels, idx)
        ax.plot(thd_spl, thd_pct, color="#1f4e79", lw=1.3)
        ax.axhline(result.max_spl_thd_percent, color="#a11a1a", lw=0.8, ls=":",
                   label=t("{thd} % limit", language).format(
                       thd=fmt_num(result.max_spl_thd_percent, language)))
        if result.max_spl_db is not None:
            ax.axvline(result.max_spl_db, color="#555555", lw=0.8, ls="--",
                       label=t("Max. SPL", language))
        ax.set_xlabel(t("Sound pressure level [dB]", language))
        ax.set_ylabel(t("THD [%]", language))
        ax.set_ylim(bottom=0.0)
        ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.6)
        ax.set_title(t("Total harmonic distortion", language), fontsize=8.5)
        ax.legend(loc="upper left", fontsize=6.5, frameon=False)
        idx += 1

    fig.tight_layout()
    return _drawing_from_figure(fig, target_width, language)


def _statement(result: "MicrophoneCharacteristics", language: str = "en") -> str:
    """The boxed headline: free-field sensitivity and effective range."""
    return t(
        "Free-field sensitivity <b>{mv} mV/Pa</b> ({level} dB re 1 V/Pa at "
        "{freq} Hz); effective frequency range <b>{range}</b> (±{tol} dB)",
        language,
    ).format(
        mv=_db_1(result.sensitivity_mv_per_pa, language),
        level=_db_1(result.sensitivity_level_db, language),
        freq=_freq(result.reference_frequency, language),
        range=_range_text(*result.effective_range, language=language),
        tol=fmt_num(result.tolerance_db, language),
    )


def _verdict(
    result: "MicrophoneCharacteristics", requirement: float, language: str = "en"
) -> Tuple[str, bool] | None:
    """Noise verdict: the equivalent noise level must not exceed the requirement."""
    level = result.equivalent_noise_level_db
    if level is None:
        return None
    passed = level <= requirement
    text = t(
        "Equivalent noise level {level} dB({w}), required &#8804; {req} dB({w})",
        language,
    ).format(
        level=_db_1(level, language),
        w=result.noise_weighting,
        req=fmt_num(requirement, language),
    )
    return text, passed


def render_iec60268_4_report(
    result: "MicrophoneCharacteristics",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    language: str = "en",
) -> str:
    """Render an IEC 60268-4 microphone-characteristics fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.electroacoustics.microphone.MicrophoneCharacteristics`.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata` supplying the header
        identity and, through ``requirement``, a maximum permitted equivalent
        noise level the verdict row compares against.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab (or, for the figures, matplotlib) is not
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
    title = t("Microphone characteristics", language)

    flow: List[Any] = [
        Paragraph(title, title_style),
        Paragraph(_basis(metadata, language), basis_style),
    ]

    if metadata is not None and not metadata.is_empty():
        pairs = _metadata_pairs(metadata, language)
        if pairs:
            flow.append(Spacer(1, 3))
            flow.append(grid_table(pairs))
    flow.append(Spacer(1, 8))

    left_cell = [
        Paragraph(t("Rated characteristics", language), caption_style),
        metrics_table(_rated_rows(result, language), col_widths=[35 * mm, 21 * mm]),
    ]
    response = _response_drawing(result, 116 * mm, language)
    flow.append(two_panel_body(left_cell, response))

    secondary = _secondary_drawing(result, 174 * mm, language)
    if secondary is not None:
        flow.append(Spacer(1, 6))
        flow.append(secondary)
    flow.append(Spacer(1, 8))

    flow.append(result_box(_statement(result, language), styles, accent))
    if metadata is not None and metadata.requirement is not None:
        verdict = _verdict(result, metadata.requirement, language)
        if verdict is not None:
            flow.extend(verdict_flow(verdict[0], verdict[1], styles, language))
    flow.extend(footer_flow(metadata, language))

    return build_document(path, flow, title)
