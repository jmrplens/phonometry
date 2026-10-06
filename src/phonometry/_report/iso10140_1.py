#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The two expression-of-results forms of ISO 10140-1:2021 (reportlab renderer).

ISO 10140-1 prints a form for two of its products and lets the user copy it:

* Figure H.4, the laboratory reduction of impact sound by a floor covering on
  a reference floor
  (:class:`~phonometry.building.measurement.lab_improvement.LabFloorCoveringImprovementResult`):
  the header of the product, the specimen and the climate, the table of
  ``Ln,0`` and ``ΔL`` beside the ``ΔL`` diagram with the frequency range of the
  ISO 717-2 rating marked, the rating ``ΔLw``, ``CIΔ`` and ``CI,r,50-2500``
  and the statement that the result comes from an artificial source on a
  specified reference floor;
* Figure J.7, the sound reduction index of joints
  (:class:`~phonometry.building.measurement.joint_insulation.LabJointInsulationResult`):
  the header with the test length, the separation wall, the test noise and the
  maximum joint sound reduction index, the table of ``Rs`` from 100 Hz to
  5 000 Hz beside its diagram and the evaluation according to ISO 717-1,
  ``Rs,w (C; Ctr)``, ``C100-5000`` and ``Ctr,100-5000``.

Both are laid out by the same skeleton as every other sound-insulation sheet,
:func:`._insulation_fiche.compose_insulation_fiche`; this module only prepares
the fields of each form. ``CI,r,50-2500`` of Figure H.4 cannot be formed,
because ISO 717-2:2020 Table 4 gives the reference floors from 100 Hz only
(recorded in the errata registry), and the sheet says so in its place.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

import numpy as np

from ._i18n import format_number, t
from ._insulation_fiche import (
    BandTable,
    Column,
    FichePlot,
    ResultBlock,
    compose_insulation_fiche,
    requirement_verdict,
    single_number_statement,
)
from ._layout import _REPORTLAB_HINT, fmt_meta, fmt_num

if TYPE_CHECKING:
    from collections.abc import Callable

    from matplotlib.axes import Axes

    from ..building.measurement.joint_insulation import LabJointInsulationResult
    from ..building.measurement.lab_improvement import (
        LabFloorCoveringImprovementResult,
    )
    from .metadata import ReportMetadata

#: The type of reference floor, as the Figure H.4 header names it.
_FLOOR_NAMES = {
    "heavyweight": "Heavyweight reference floor (ISO 10140-5:2021 C.2)",
    "lightweight_1": "Lightweight reference floor No 1 (ISO 10140-5:2021 C.3)",
    "lightweight_2": "Lightweight reference floor No 2 (ISO 10140-5:2021 C.3)",
    "lightweight_3": "Lightweight reference floor No 3 (ISO 10140-5:2021 C.3)",
}

#: The weighted reduction and its adaptation term on each reference floor:
#: ``ΔLw`` with ``CI,Δ`` on the heavyweight floor (H.1, H.5 h)), ``ΔLt,n,w``
#: with ``CIΔ,tn`` on a lightweight one (ISO 717-2:2020 6.2, A.2.3).
_FLOOR_SYMBOLS = {
    "heavyweight": ("&#916;L<sub>w</sub>", "C<sub>I,&#916;</sub>"),
    "lightweight_1": ("&#916;L<sub>t,1,w</sub>", "C<sub>I&#916;,t1</sub>"),
    "lightweight_2": ("&#916;L<sub>t,2,w</sub>", "C<sub>I&#916;,t2</sub>"),
    "lightweight_3": ("&#916;L<sub>t,3,w</sub>", "C<sub>I&#916;,t3</sub>"),
}

#: The fixed range of the ``ΔL`` diagram of Figure H.4, in dB; a curve beyond
#: it widens the axis to the next 10 dB.
_DELTA_L_RANGE_DB = (-10.0, 50.0)

#: The fixed range of the ``Rs`` diagram of Figure J.7, in dB; a curve beyond
#: it widens the axis to the next 10 dB.
_RS_RANGE_DB = (30.0, 80.0)

#: Size of the diagram panel, in inches: shorter than the default portrait
#: panel, because both forms carry a longer header than the other sheets.
_PANEL_INCHES = (5.8, 4.0)

#: Column widths of the Figure H.4 table, in mm: ``f``, ``Ln,0``, ``ΔL`` and,
#: verbose, ``Ln``.
_FLOOR_COLUMNS_MM = (11.0, 17.0, 17.0)
_FLOOR_VERBOSE_COLUMNS_MM = (11.0, 15.0, 15.0, 15.0)

#: Column widths of the verbose Figure J.7 table, in mm: ``f``, ``R's``,
#: ``Rs,max`` and ``Rs``.
_JOINT_VERBOSE_COLUMNS_MM = (11.0, 14.0, 14.0, 17.0)


def _signed(value: int) -> str:
    """An adaptation term with its sign, as the boxed statements print them."""
    return f"{value:+d}"


def _pairs(specs: list[tuple[str, str | None]]) -> list[tuple[str, str]]:
    """The header pairs that are set; free text is escaped, numbers are not."""
    return [(label, value) for label, value in specs if value is not None]


def _text(value: str | None) -> str | None:
    """User-supplied free text, escaped for reportlab's paragraph parser."""
    return None if value is None else html.escape(value)


def _number(value: float | None, language: str) -> str | None:
    """A header number printed as the caller wrote it."""
    return None if value is None else fmt_meta(value, language)


def _pin_range(axes: Axes, values: np.ndarray, printed: tuple[float, float]) -> None:
    """Set the printed range of a form's diagram, widened to the next 10 dB.

    The forms print their diagram over a fixed range; a curve beyond it
    widens the axis to the next multiple of 10 dB rather than leaving the
    page.
    """
    low, high = printed
    finite = values[np.isfinite(values)]
    axes.set_ylim(
        min(low, 10.0 * np.floor(float(np.min(finite)) / 10.0)),
        max(high, 10.0 * np.ceil(float(np.max(finite)) / 10.0)),
    )


# --- Figure H.4 --------------------------------------------------------------


def _floor_header(
    result: LabFloorCoveringImprovementResult,
    metadata: ReportMetadata | None,
    language: str,
) -> list[tuple[str, str]]:
    """The header fields of Figure H.4, in the order the form prints them."""
    md = metadata
    temperature = None
    humidity = None
    if md is not None:
        temperature = (
            md.source_temperature_c
            if md.source_temperature_c is not None
            else md.temperature_c
        )
        humidity = (
            md.source_relative_humidity_percent
            if md.source_relative_humidity_percent is not None
            else md.relative_humidity_percent
        )
    return _pairs(
        [
            (t("Manufacturer", language), _text(md.manufacturer if md else None)),
            (
                t("Product identification", language),
                _text(md.product if md else None),
            ),
            (t("Client", language), _text(md.client if md else None)),
            (
                t("Test room identification", language),
                _text(md.test_room if md else None),
            ),
            (
                t("Test specimen mounted by", language),
                _text(md.mounted_by if md else None),
            ),
            (t("Date of test", language), _text(md.test_date if md else None)),
            (
                t(
                    "Description of test facility, test specimen and test arrangement",
                    language,
                ),
                _text(md.specimen if md else None),
            ),
            (
                t("Type of reference floor", language),
                t(_FLOOR_NAMES[result.reference_floor], language),
            ),
            (
                t(
                    "Mass of test specimen per unit area [kg/m<super>2</super>]",
                    language,
                ),
                _number(md.mass_per_area if md else None, language),
            ),
            (
                t("Curing time [h]", language),
                _number(md.curing_time_h if md else None, language),
            ),
            (
                t("Air temp. in the source room [&#176;C]", language),
                _number(temperature, language),
            ),
            (
                t("Air humidity in the source room [%]", language),
                _number(humidity, language),
            ),
            (
                t("Receiving room volume [m<super>3</super>]", language),
                _number(md.receiving_volume if md else None, language),
            ),
        ]
    )


def _floor_box(
    result: LabFloorCoveringImprovementResult, language: str
) -> tuple[str, list[str]]:
    """The rating of Figure H.4 and the two floor ratings H.5 i) asks for."""
    symbol, term = _FLOOR_SYMBOLS[result.reference_floor]
    box = (
        f"{symbol} = <b>{result.delta_lw_db} dB</b>; "
        f"{term} = <b>{_signed(int(result.ci_delta_db or 0))} dB</b>"
    )
    extended: list[str] = []
    reference = result.reference_rating
    if reference is not None:
        extended.append(
            f"L<sub>n,r,w</sub> (C<sub>I,r</sub>) = {reference.rating} "
            f"({_signed(reference.ci)}) dB"
        )
    bare = result.bare_rating
    if bare is not None:
        extended.append(
            f"L<sub>n,0,w</sub> (C<sub>I,0</sub>) = {bare.rating} ({_signed(bare.ci)}) dB"
        )
    extended.append(
        t(
            "C<sub>I,r,50-2500</sub>: not formed, ISO 717-2 Table 4 starts at 100 Hz",
            language,
        )
    )
    return box, extended


def render_floor_covering_form(
    result: LabFloorCoveringImprovementResult,
    path: str,
    *,
    metadata: ReportMetadata | None,
    verbose: bool,
    language: str,
) -> str:
    """Render the form of ISO 10140-1:2021 Figure H.4 to a PDF.

    :param result: The floor-covering improvement, with its ISO 717-2 rating
        (checked by the caller).
    :param path: Destination path of the PDF file.
    :param metadata: The header fields; ``product`` and ``curing_time_h``
        fill the product identification and curing time rows.
    :param verbose: When ``True``, the table also shows ``Ln`` with the
        covering.
    :param language: ``"en"`` or ``"es"``.
    :return: The written ``path``.
    :raises ImportError: If reportlab or matplotlib is not installed.
    """
    _require_reportlab()
    freqs = np.asarray(result.frequencies_hz, dtype=np.float64)
    columns: list[Column] = [
        (t("L<sub>n,0</sub> [dB]", language), np.asarray(result.l_n0_db), 1),
    ]
    if verbose:
        columns.append(
            (t("L<sub>n</sub> [dB]", language), np.asarray(result.l_n_db), 1)
        )
    columns.append((t("&#916;L [dB]", language), np.asarray(result.improvement_db), 1))
    widths_mm = _FLOOR_VERBOSE_COLUMNS_MM if verbose else _FLOOR_COLUMNS_MM

    def _plot(ax: Axes | None = None, language: str = language) -> Axes:
        axes = result.plot(ax=ax, language=language, rating_range=True)
        values = np.asarray(result.improvement_db, dtype=np.float64)
        _pin_range(axes, values, _DELTA_L_RANGE_DB)
        return axes

    box, extended = _floor_box(result, language)
    verdict = None
    if metadata is not None and metadata.requirement is not None:
        symbol, _ = _FLOOR_SYMBOLS[result.reference_floor]
        passed = float(result.delta_lw_db or 0) >= metadata.requirement
        text = t("{sym} = {rating} dB, required &#8805; {req} dB", language).format(
            sym=symbol,
            rating=result.delta_lw_db,
            req=fmt_num(metadata.requirement, language),
        )
        verdict = (text, passed)
    return _compose(
        path,
        title=t("Reduction of impact sound pressure level", language),
        basis=t(
            "In accordance with ISO 10140 (all parts): laboratory measurements "
            "of the reduction of transmitted impact sound by floor coverings on "
            "a heavyweight or lightweight reference floor (ISO 10140-1:2021 "
            "Figure H.4). Rating in accordance with ISO 717-2:2020.",
            language,
        ),
        header=_floor_header(result, metadata, language),
        table=BandTable(
            centers=freqs,
            columns=columns,
            caption=t("One-third-octave L<sub>n,0</sub> and &#916;L", language),
            col_widths=_widths(widths_mm),
            compact=True,
        ),
        draw=_plot,
        result=ResultBlock(
            box=box,
            statement=t(
                "These results are based on a test performed with an artificial "
                "source under laboratory conditions (engineering method) with "
                "specified reference floor.",
                language,
            ),
            extended=extended or None,
            verdict=verdict,
        ),
        metadata=metadata,
        language=language,
    )


# --- Figure J.7 --------------------------------------------------------------


def _joint_cells(result: LabJointInsulationResult, language: str) -> list[str]:
    """``Rs`` per band, as the table of Figure J.7 prints it.

    A minimum value carries ``≥``, and one set to the maximum of the
    arrangement is also put in brackets, as J.1 writes "(Rs ≥ 50,4 dB)".
    """
    cells: list[str] = []
    for value, regime in zip(result.r_s_db, result.regime, strict=True):
        number = format_number(float(value), language, decimals=1)
        if regime == "maximum":
            cells.append(f"(≥ {number})")
        elif regime == "limit":
            cells.append(f"≥ {number}")
        else:
            cells.append(number)
    return cells


def _joint_header(
    result: LabJointInsulationResult,
    metadata: ReportMetadata | None,
    language: str,
) -> list[tuple[str, str]]:
    """The header fields of Figure J.7, in the order the form prints them."""
    md = metadata
    volumes = None
    climate = None
    if md is not None:
        rooms = [
            fmt_meta(v, language)
            for v in (md.source_volume, md.receiving_volume)
            if v is not None
        ]
        volumes = " / ".join(rooms) if rooms else None
        climate = _joint_climate(md, language)
    maximum = None
    if result.max_rating is not None:
        rating = result.max_rating
        maximum = (
            f"R<sub>s,max,w</sub> (C; C<sub>tr</sub>) = {rating.rating} "
            f"({_signed(rating.c)}; {_signed(rating.ctr)}) dB"
        )
    length = (
        None
        if result.joint_length_m is None
        else fmt_meta(result.joint_length_m, language)
    )
    return _pairs(
        [
            (t("Client", language), _text(md.client if md else None)),
            (
                t("Description of the test specimen", language),
                _text(md.specimen if md else None),
            ),
            (t("Date of test", language), _text(md.test_date if md else None)),
            (t("Test length l [m]", language), length),
            (
                t("Separation wall", language),
                _text(md.separating_element if md else None),
            ),
            (t("Test noise", language), _text(md.test_signal if md else None)),
            (t("Volumes of the test rooms [m<super>3</super>]", language), volumes),
            (t("Maximum joint sound reduction index", language), maximum),
            (t("Mounting conditions", language), _text(md.mounting if md else None)),
            (t("Climate in the test rooms", language), climate),
        ]
    )


def _room_climate(
    temperature: float | None, humidity: float | None, language: str
) -> str | None:
    """``20.5 °C, 47 %`` for one room, or ``None`` when neither is known."""
    parts = []
    if temperature is not None:
        parts.append(f"{fmt_meta(temperature, language)} &#176;C")
    if humidity is not None:
        parts.append(f"{fmt_meta(humidity, language)} %")
    return ", ".join(parts) if parts else None


def _joint_climate(md: ReportMetadata, language: str) -> str | None:
    """The climate in both test rooms, as the row of Figure J.7 asks.

    The per-room fields when given, the single ``temperature_c`` and
    ``relative_humidity_percent`` otherwise, which then hold for both rooms;
    the same rule as the ISO 717 sheets. Two rooms in the same climate are
    printed once.
    """
    per_room_t = (
        md.source_temperature_c is not None or md.receiving_temperature_c is not None
    )
    per_room_rh = (
        md.source_relative_humidity_percent is not None
        or md.receiving_relative_humidity_percent is not None
    )
    source = _room_climate(
        md.source_temperature_c if per_room_t else md.temperature_c,
        md.source_relative_humidity_percent
        if per_room_rh
        else md.relative_humidity_percent,
        language,
    )
    receiving = _room_climate(
        md.receiving_temperature_c if per_room_t else md.temperature_c,
        md.receiving_relative_humidity_percent
        if per_room_rh
        else md.relative_humidity_percent,
        language,
    )
    if source == receiving:
        return source
    rooms = []
    if source is not None:
        rooms.append(t("source room {climate}", language).format(climate=source))
    if receiving is not None:
        rooms.append(t("receiving room {climate}", language).format(climate=receiving))
    return " / ".join(rooms)


def _open_term(value: int | None, language: str) -> str:
    """An open-band adaptation term with its sign, or *unbounded*."""
    return t("unbounded", language) if value is None else f"{_signed(value)} dB"


def _joint_box(
    result: LabJointInsulationResult, language: str
) -> tuple[str, list[str]]:
    """The evaluation of Figure J.7, bracketed when J.1 says so."""
    rating = result.rating
    if rating is None:  # checked by the caller; kept for the type checker
        msg = "The Figure J.7 form needs the ISO 717-1 rating."
        raise ValueError(msg)
    # J.1: "the single number ratings shall also be presented in brackets",
    # every one the form prints, the enlarged-range terms included.
    box = single_number_statement(rating, "R<sub>s,w</sub>")
    if result.bracketed:
        box = f"({box})"
    extended: list[str] = []
    if result.c_100_5000_db is not None and result.ctr_100_5000_db is not None:
        wide = (
            f"C<sub>100-5000</sub> = {_signed(result.c_100_5000_db)} dB; "
            f"C<sub>tr,100-5000</sub> = {_signed(result.ctr_100_5000_db)} dB"
        )
        extended.append(f"({wide})" if result.bracketed else wide)
    opened = result.open_band_rating
    if result.bracketed and opened is not None:
        if opened.r_s_w_db is None or opened.c_db is None or opened.ctr_db is None:
            extended.append(
                t(
                    "In brackets: with the indicative bands taken as "
                    "infinitely high the rating is unbounded (J.1)",
                    language,
                )
            )
        else:
            # The open-band value of every single number the form prints, so
            # the one that moved by more than 1 dB is there to see.
            wide_open = ""
            if result.c_100_5000_db is not None:
                wide_open = (
                    f"; C<sub>100-5000</sub> = "
                    f"{_open_term(opened.c_100_5000_db, language)}; "
                    f"C<sub>tr,100-5000</sub> = "
                    f"{_open_term(opened.ctr_100_5000_db, language)}"
                )
            extended.append(
                t(
                    "In brackets: with the indicative bands taken as "
                    "infinitely high, R<sub>s,w</sub> (C; C<sub>tr</sub>) = "
                    "{rating} ({c}; {ctr}) dB{extended} (J.1)",
                    language,
                ).format(
                    rating=opened.r_s_w_db,
                    c=_signed(opened.c_db),
                    ctr=_signed(opened.ctr_db),
                    extended=wide_open,
                )
            )
    return box, extended


def render_joint_form(
    result: LabJointInsulationResult,
    path: str,
    *,
    metadata: ReportMetadata | None,
    verbose: bool,
    language: str,
) -> str:
    """Render the form of ISO 10140-1:2021 Figure J.7 to a PDF.

    :param result: The joint result, with its ISO 717-1 rating (checked by
        the caller).
    :param path: Destination path of the PDF file.
    :param metadata: The header fields; ``separating_element`` and
        ``test_signal`` fill the separation wall and test noise rows.
    :param verbose: When ``True``, the table also shows ``R's`` and
        ``Rs,max``.
    :param language: ``"en"`` or ``"es"``.
    :return: The written ``path``.
    :raises ImportError: If reportlab or matplotlib is not installed.
    """
    _require_reportlab()
    freqs = np.asarray(result.frequencies_hz, dtype=np.float64)
    cells = _joint_cells(result, language)
    header = t("R<sub>s</sub> [dB]", language)
    if verbose:
        columns: list[Column] = [
            (
                t("R&#8242;<sub>s</sub> [dB]", language),
                np.asarray(result.r_s_measured_db),
                1,
            ),
            (t("R<sub>s,max</sub> [dB]", language), np.asarray(result.r_s_max_db), 1),
            (header, cells, 1),
        ]
        widths: list[float] | None = _widths(_JOINT_VERBOSE_COLUMNS_MM)
    else:
        columns = [(header, cells, 1)]
        widths = None

    def _plot(ax: Axes | None = None, language: str = language) -> Axes:
        axes = result.plot(ax=ax, language=language)
        values = np.concatenate(
            [
                np.asarray(result.r_s_db, dtype=np.float64),
                np.asarray(result.r_s_measured_db, dtype=np.float64),
                np.asarray(result.r_s_max_db, dtype=np.float64),
            ]
        )
        _pin_range(axes, values, _RS_RANGE_DB)
        return axes

    rating = result.rating
    verdict = None
    if rating is not None and metadata is not None and metadata.requirement is not None:
        verdict = requirement_verdict(
            rating, "R<sub>s,w</sub>", metadata.requirement, language
        )
    statement = t(
        "Evaluation according to ISO 717-1 (in one-third octave bands). A value "
        "after &#8805; is a minimum value; one in brackets is limited by the "
        "maximum sound reduction index of the test arrangement R<sub>s,max</sub> "
        "(ISO 10140-1:2021 J.1).",
        language,
    )
    box, extended = _joint_box(result, language)
    return _compose(
        path,
        title=t("Sound reduction index of joints according to ISO 10140-1", language),
        basis=t(
            "Determination of sound reduction index of joints per metre, "
            "R<sub>s</sub>, by ISO 10140-1:2021 Annex J (Formulae (J.1) and "
            "(J.2)). Rating in accordance with ISO 717-1:2020.",
            language,
        ),
        header=_joint_header(result, metadata, language),
        table=BandTable(
            centers=freqs,
            columns=columns,
            caption=t("Sound reduction index of joints R<sub>s</sub>", language),
            col_widths=widths,
            compact=True,
        ),
        draw=_plot,
        result=ResultBlock(
            box=box,
            statement=statement,
            extended=extended or None,
            verdict=verdict,
        ),
        metadata=metadata,
        language=language,
    )


def _require_reportlab() -> None:
    """Raise the actionable hint before anything imports reportlab.

    :raises ImportError: If reportlab is not installed.
    """
    try:
        import reportlab  # noqa: F401
    except ImportError as exc:
        raise ImportError(_REPORTLAB_HINT) from exc


def _widths(widths_mm: tuple[float, ...]) -> list[float]:
    """Column widths in points from millimetres (reportlab imported lazily)."""
    from reportlab.lib.units import mm

    return [w * mm for w in widths_mm]


def _compose(
    path: str,
    *,
    title: str,
    basis: str,
    header: list[tuple[str, str]],
    table: BandTable,
    draw: Callable[..., Axes],
    result: ResultBlock,
    metadata: ReportMetadata | None,
    language: str,
) -> str:
    """Hand one form to the shared sound-insulation skeleton."""
    return compose_insulation_fiche(
        path,
        title=title,
        basis=basis,
        header_pairs=header,
        table=table,
        plot=FichePlot(draw=draw, y_top=None, figsize=_PANEL_INCHES),
        result=result,
        metadata=metadata,
        language=language,
    )
