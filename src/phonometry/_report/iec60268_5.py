#  Copyright (c) 2026. Jose M. Requena-Plens
"""IEC 60268-5 loudspeaker-characteristics fiche (reportlab renderer).

Renders a
:class:`~phonometry.electroacoustics.loudspeaker.LoudspeakerCharacteristics` to
a one-page PDF laid out like a loudspeaker rated-characteristics data sheet,
following IEC 60268-5:2003+A1:2007:

* a title and the standard-basis line (IEC 60268-5, graphs to IEC 60263:1982);
* an optional metadata header (client, manufacturer, model, room conditions);
* a rated-characteristics table beside the on-axis frequency response, the
  response drawn with a shaded tolerance band and the effective-frequency-range
  markers, to the IEC 60263 25 dB-per-decade scale proportion (clause 2);
* a full-width row of the impedance modulus, the total-harmonic-distortion and
  the polar-directivity panels for the data supplied, the polar diagram to the
  IEC 60263 25 dB reference-circle convention (clause 3);
* a boxed characteristic-sensitivity / effective-range result;
* an optional sensitivity verdict when a requirement is supplied; and
* a footer identity/disclaimer block.

The quantity-independent skeleton (metadata grid, table, result box, verdict
styling, footer, document build) lives in :mod:`._layout`; this module holds the
IEC 60268-5 specifics (labels, the rated-characteristics table and the
IEC 60263 characteristic graphs). reportlab, matplotlib and svglib are soft
dependencies imported lazily (reportlab and svglib ship in the
``phonometry[report]`` extra, matplotlib in ``phonometry[plot]``); each is
guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

import html
import os
import tempfile
from typing import TYPE_CHECKING, Any, List, Tuple

import numpy as np

from ._i18n import format_number, t
from ._layout import (
    _ACCENT_HEX,
    _MATPLOTLIB_HINT,
    _REPORTLAB_HINT,
    _SVGLIB_HINT,
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
from .metadata import ReportMetadata

if TYPE_CHECKING:
    from ..electroacoustics.loudspeaker import LoudspeakerCharacteristics

#: Ordinate span of the on-axis response plot, in dB. A multiple of 25 keeps the
#: IEC 60263 25 dB-per-decade grid on whole gridlines.
_RESPONSE_SPAN_DB = 50.0
#: IEC 60263 clause 2 scale proportion: one frequency decade equals this many
#: decibels on the ordinate (the "square" 25 dB-per-decade grid).
_DB_PER_DECADE = 25.0
#: IEC 60263 clause 3 polar reference-circle span, in dB (radius = 25 dB).
_POLAR_SPAN_DB = 25.0

_OHM = "&#937;"  # reportlab entity for the ohm sign
_OHM_TEXT = "Ω"  # unicode ohm for matplotlib labels


def _basis(metadata: ReportMetadata | None, language: str = "en") -> str:
    """The standard-basis line: IEC 60268-5 with the IEC 60263 graph convention."""
    standard = metadata.measurement_standard if metadata is not None else None
    if standard:
        return t(
            "{standard} measurement of loudspeaker rated characteristics per "
            "IEC 60268-5:2003+A1:2007; frequency and polar graphs to "
            "IEC 60263:1982.",
            language,
        ).format(standard=html.escape(standard))
    return t(
        "Loudspeaker rated characteristics per IEC 60268-5:2003+A1:2007; "
        "frequency and polar graphs to IEC 60263:1982.",
        language,
    )


def _metadata_pairs(
    metadata: ReportMetadata, language: str = "en"
) -> List[Tuple[str, str]]:
    """Ordered (label, value) header pairs for the supplied loudspeaker fields."""

    def num(value: float | None) -> str | None:
        return fmt_num(value, language) if value is not None else None

    specs: List[Tuple[str, str | None]] = [
        (t("Client", language), metadata.client),
        (t("Manufacturer", language), metadata.manufacturer),
        (t("Description", language), metadata.specimen),
        (t("Test room", language), metadata.test_room),
        (t("Mounting", language), metadata.mounting),
        (t("Date of test", language), metadata.test_date),
        (t("Temperature [&#176;C]", language), num(metadata.temperature)),
        (t("Relative humidity [%]", language), num(metadata.relative_humidity)),
        (t("Ambient pressure [kPa]", language), num(metadata.pressure)),
    ]
    return [(label, html.escape(str(value))) for label, value in specs if value is not None]


def _freq(value: float, language: str = "en") -> str:
    """A frequency rounded to the nearest hertz, locale-formatted."""
    return format_number(round(float(value)), language, decimals=0)


def _range_text(lo: float, hi: float, language: str = "en") -> str:
    """A frequency range ``lo - hi Hz`` with an en dash."""
    return f"{_freq(lo, language)}&#8211;{_freq(hi, language)} Hz"


def _rated_rows(
    result: "LoudspeakerCharacteristics", language: str = "en"
) -> List[Tuple[str, str]]:
    """The rated-characteristics table rows (only the quantities that exist)."""
    rows: List[Tuple[str, str]] = [
        (
            t("Rated impedance", language),
            f"{fmt_num(result.rated_impedance, language)} {_OHM}",
        ),
        (
            t("Characteristic sensitivity", language),
            f"{format_number(result.sensitivity_level_db, language, decimals=1)} dB",
        ),
        (
            t("Effective frequency range", language),
            _range_text(*result.effective_range, language=language),
        ),
    ]
    if result.rated_frequency_range is not None:
        rows.append(
            (
                t("Rated frequency range", language),
                _range_text(*result.rated_frequency_range, language=language),
            )
        )
    if result.resonance_frequency is not None:
        rows.append(
            (
                t("Resonance frequency", language),
                f"{_freq(result.resonance_frequency, language)} Hz",
            )
        )
    if result.rated_noise_power is not None:
        rows.append(
            (
                t("Rated noise power", language),
                f"{fmt_num(result.rated_noise_power, language)} W",
            )
        )
    if result.rated_sinusoidal_power is not None:
        rows.append(
            (
                t("Rated sinusoidal power", language),
                f"{fmt_num(result.rated_sinusoidal_power, language)} W",
            )
        )
    min_z = result.minimum_impedance
    if min_z is not None:
        rows.append(
            (
                t("Minimum impedance", language),
                f"{fmt_num(min_z, language)} {_OHM}",
            )
        )
    if result.directivity_index_db is not None:
        label = t("Directivity index", language)
        if result.polar_frequency is not None:
            label = t("Directivity index at {freq} Hz", language).format(
                freq=_freq(result.polar_frequency, language)
            )
        rows.append(
            (label, f"{format_number(result.directivity_index_db, language, decimals=1)} dB")
        )
    return rows


# --------------------------------------------------------------------------- #
# IEC 60263 characteristic graphs
# --------------------------------------------------------------------------- #
def _drawing_from_figure(fig: Any, target_width: float, language: str = "en") -> Any:
    """Convert a matplotlib figure to a scaled, vector reportlab ``Drawing``.

    Mirrors :func:`phonometry._report._layout.render_figure_drawing` (SVG with
    text rasterised to vector paths, converted by svglib) but keeps the caller's
    own multi-panel figure and axes untouched, so the IEC 60263 scale
    proportions set on each axes survive.
    """
    try:
        import matplotlib
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        raise ImportError(_MATPLOTLIB_HINT) from exc
    try:
        from svglib.svglib import svg2rlg
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        raise ImportError(_SVGLIB_HINT) from exc
    from .._i18n import localize_axes

    for ax in fig.axes:
        localize_axes(ax, language)
    svg_fd, svg_path = tempfile.mkstemp(suffix=".svg")
    os.close(svg_fd)
    try:
        with matplotlib.rc_context({"svg.fonttype": "path"}):
            fig.savefig(svg_path, format="svg", bbox_inches="tight")
        drawing = svg2rlg(svg_path)
    finally:
        if os.path.exists(svg_path):
            os.remove(svg_path)
    if drawing is None or not drawing.width:
        raise ValueError("Could not convert the report plot to vector graphics.")
    scale = target_width / drawing.width
    drawing.scale(scale, scale)
    drawing.width = drawing.width * scale
    drawing.height = drawing.height * scale
    drawing.hAlign = "CENTER"
    return drawing


def _response_drawing(
    result: "LoudspeakerCharacteristics", target_width: float, language: str = "en"
) -> Any:
    """On-axis response with the tolerance band and effective-range markers.

    Plotted to the IEC 60263 clause 2 proportion: one frequency decade equals
    25 dB on the ordinate (:data:`_DB_PER_DECADE`).
    """
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    f = result.frequencies
    spl = result.spl_db
    ref = result.reference_level_db
    tol = result.tolerance_db

    fig = Figure(figsize=(5.6, 4.2))
    FigureCanvasAgg(fig)
    ax = fig.subplots()

    top = float(np.ceil((max(float(np.max(spl)), ref + tol) + 2.0) / 5.0) * 5.0)
    bottom = top - _RESPONSE_SPAN_DB
    # The PDF vector backend (svglib) does not preserve alpha, so a translucent
    # fill would render as a solid block that hides the response curve. Draw a
    # pale opaque tolerance band below the curves (zorder=0) instead.
    ax.axhspan(ref - tol, ref + tol, facecolor="#d3e2f2", edgecolor="none",
               zorder=0, label=t("Tolerance ±{tol} dB", language).format(
                   tol=fmt_num(tol, language)))
    ax.axhline(ref, color="#1f4e79", lw=0.8, ls="--")
    ax.axhline(ref - 10.0, color="#a11a1a", lw=0.8, ls=":",
               label=t("−10 dB reference", language))
    ax.semilogx(f, spl, color="#1f4e79", lw=1.4,
                label=t("On-axis response", language))
    lo, hi = result.effective_range
    for edge in (lo, hi):
        ax.axvline(edge, color="#1b6e2f", lw=0.9, ls="-.")
    ax.plot([], [], color="#1b6e2f", lw=0.9, ls="-.",
            label=t("Effective range", language))

    ax.set_xlim(float(np.min(f)), float(np.max(f)))
    ax.set_ylim(bottom, top)
    ax.set_xlabel(t("Frequency [Hz]", language))
    ax.set_ylabel(t("Sound pressure level [dB]", language))
    ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.6)
    _format_freq_axis(ax)
    decades = np.log10(float(np.max(f)) / float(np.min(f)))
    ax.set_box_aspect(_RESPONSE_SPAN_DB / (_DB_PER_DECADE * decades))
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2,
              frameon=False, fontsize=7.5)
    fig.tight_layout()
    return _drawing_from_figure(fig, target_width, language)


def _format_freq_axis(ax: Any) -> None:
    """Label the log-frequency axis with plain hertz/kilohertz ticks."""
    from matplotlib.ticker import FuncFormatter

    def _fmt(x: float, _pos: int) -> str:
        if x >= 1000.0:
            return f"{x / 1000.0:g}k"
        return f"{x:g}"

    ax.xaxis.set_major_formatter(FuncFormatter(_fmt))
    ax.xaxis.set_minor_formatter(FuncFormatter(lambda x, p: ""))


def _secondary_drawing(
    result: "LoudspeakerCharacteristics", target_width: float, language: str = "en"
) -> Any | None:
    """Impedance, THD and polar-directivity panels for the data supplied."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    has_imp = result.impedance_frequencies is not None
    has_thd = result.thd_frequencies is not None
    has_polar = result.polar_angles_deg is not None
    panels = int(has_imp) + int(has_thd) + int(has_polar)
    if panels == 0:
        return None

    fig = Figure(figsize=(5.6 * panels / 2.4 + 0.8, 2.6))
    FigureCanvasAgg(fig)
    idx = 1

    if has_imp:
        ax = fig.add_subplot(1, panels, idx)
        ax.semilogx(result.impedance_frequencies, result.impedance_modulus,
                    color="#1f4e79", lw=1.3)
        ax.axhline(result.rated_impedance, color="#555555", lw=0.8, ls="--",
                   label=t("Rated impedance", language))
        ax.axhline(0.8 * result.rated_impedance, color="#a11a1a", lw=0.8, ls=":",
                   label=t("80 % of rated", language))
        ax.set_xlabel(t("Frequency [Hz]", language))
        ax.set_ylabel(t("Impedance |Z| [{ohm}]", language).format(ohm=_OHM_TEXT))
        ax.set_ylim(bottom=0.0)
        ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.6)
        ax.set_title(t("Impedance", language), fontsize=8.5)
        ax.legend(loc="upper right", fontsize=6.5, frameon=False)
        _format_freq_axis(ax)
        idx += 1

    if has_thd:
        ax = fig.add_subplot(1, panels, idx)
        ax.semilogx(result.thd_frequencies, result.thd_percent,
                    color="#1f4e79", lw=1.3)
        ax.set_xlabel(t("Frequency [Hz]", language))
        ax.set_ylabel(t("THD [%]", language))
        ax.set_ylim(bottom=0.0)
        ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.6)
        ax.set_title(t("Total harmonic distortion", language), fontsize=8.5)
        _format_freq_axis(ax)
        idx += 1

    if has_polar:
        ax = fig.add_subplot(1, panels, idx, projection="polar")
        _draw_polar(ax, result, language)
        idx += 1

    fig.tight_layout()
    return _drawing_from_figure(fig, target_width, language)


def _draw_polar(
    ax: Any, result: "LoudspeakerCharacteristics", language: str = "en"
) -> None:
    """Polar directivity to the IEC 60263 clause 3 25 dB reference-circle scale."""
    angles = np.asarray(result.polar_angles_deg, dtype=np.float64)
    levels = np.clip(np.asarray(result.polar_db, dtype=np.float64), -_POLAR_SPAN_DB, 0.0)
    # Mirror a one-sided pattern about the reference axis for a full rose.
    if float(np.min(angles)) >= 0.0:
        angles = np.concatenate([-angles[::-1], angles])
        levels = np.concatenate([levels[::-1], levels])
    theta = np.radians(angles)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.plot(theta, levels, color="#1f4e79", lw=1.3)
    ax.set_ylim(-_POLAR_SPAN_DB, 0.0)
    # Reference circle at 0 dB (relative level, IEC 60263 3.3); radial ticks
    # every 5 dB (multiple of 5 for a 25 dB radius, IEC 60263 3.2).
    ax.set_yticks([-20.0, -15.0, -10.0, -5.0, 0.0])
    ax.set_yticklabels(["-20", "", "-10", "", "0 dB"], fontsize=6.5)
    ax.tick_params(axis="x", labelsize=6.5)
    ax.grid(True, ls=":", lw=0.4, alpha=0.7)
    title = t("Directional response", language)
    if result.polar_frequency is not None:
        title = t("Directional response at {freq} Hz", language).format(
            freq=_freq(result.polar_frequency, language)
        )
    ax.set_title(title, fontsize=8.5)


def _statement(result: "LoudspeakerCharacteristics", language: str = "en") -> str:
    """The boxed headline: characteristic sensitivity and effective range."""
    return t(
        "Characteristic sensitivity <b>{level} dB</b> (1 W / 1 m); "
        "effective frequency range <b>{range}</b>",
        language,
    ).format(
        level=format_number(result.sensitivity_level_db, language, decimals=1),
        range=_range_text(*result.effective_range, language=language),
    )


def _verdict(
    result: "LoudspeakerCharacteristics", requirement: float, language: str = "en"
) -> Tuple[str, bool]:
    """Sensitivity verdict: the characteristic sensitivity level must reach it."""
    level = result.sensitivity_level_db
    passed = level >= requirement
    text = t(
        "Characteristic sensitivity {level} dB, required &#8805; {req} dB",
        language,
    ).format(
        level=format_number(level, language, decimals=1),
        req=fmt_num(requirement, language),
    )
    return text, passed


def render_iec60268_5_report(
    result: "LoudspeakerCharacteristics",
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    language: str = "en",
) -> str:
    """Render an IEC 60268-5 loudspeaker-characteristics fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.electroacoustics.loudspeaker.LoudspeakerCharacteristics`.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata` supplying the header
        identity and, through ``requirement``, a characteristic sensitivity
        level the verdict row compares against.
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
    title = t("Loudspeaker characteristics", language)

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
        metrics_table(_rated_rows(result, language), col_widths=[33 * mm, 23 * mm]),
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
        text, passed = _verdict(result, metadata.requirement, language)
        flow.extend(verdict_flow(text, passed, styles, language))
    flow.extend(footer_flow(metadata, language))

    return build_document(path, flow, title)
