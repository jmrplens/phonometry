#  Copyright (c) 2026. Jose Manuel Requena Plens
"""How a record of the library shows itself in IPython and Jupyter (private).

A result of the library is a frozen dataclass, and its ``repr`` is the one
:mod:`dataclasses` writes: every field, and every array as numpy prints it,
in full up to a thousand values and cut short with ``...`` above that. That
is the right ``repr``, since it says what the record holds, and the wrong
thing to look at in a notebook, which displays the last expression of a cell
whole: a record of a few arrays of some hundred values prints as pages of
numbers.

Every public record therefore inherits :class:`RichDisplay`, through
:class:`~phonometry._internal.frozen.OwnsArrays` when it can hold an array,
which answers the two questions IPython asks of an object it displays:
``_repr_html_``, a table that Jupyter, JupyterLab, VS Code and Colab render,
and ``_repr_pretty_``, the same table in plain text for the IPython terminal.
``repr()`` and ``print()`` are left as they were. A named tuple, which cannot
take a base, defines the two methods in its body as calls to
:func:`record_html` and :func:`record_pretty`.

The table reads the record's fields and, on a verdict, ``passes``, which is a
property and may read others of the record; the display itself calls no other
property, draws no plot and runs no other computation of the record's own. A
scalar is printed; the unit of a field is read from the end of its name
(``levels_db`` is in decibels, ``wind_speed_m_s`` in metres per second), and
a name that ends in no unit gets none; an array is one line, its shape, its
type and the range of its values, never the values; a record held in a field
is a table of its own, folded, one level down; a tuple, a list or a mapping
is summarised. A record with a ``passes`` verdict shows it as PASS or FAIL in
its title. Everything is bounded: the frames of the largest simulation are
one row of a few hundred bytes, the whole of the largest result a few
kilobytes, and an array of hours of samples is not read at all: the range of
an array is read only up to :data:`RANGE_LIMIT` values, a table stops at
:data:`MAX_ROWS` rows and expands at most :data:`MAX_NESTED` records, a
string stops at :data:`MAX_TEXT` characters and a whole value at
:data:`MAX_VALUE`. Every text that reaches the HTML is escaped.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import enum
import html
import itertools
import os
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Iterable

#: An array is summarised by the range of its values only up to this many
#: values: about 130 MB of float64, read in a few tens of milliseconds. Above
#: it the summary gives the shape and the type alone, so that displaying the
#: frames of a long simulation, or a recording held on disk, reads nothing.
RANGE_LIMIT = 1 << 24

#: The rows one table shows; the largest public record has 54 fields.
MAX_ROWS = 80

#: The records held in fields that one table expands into tables of their own.
MAX_NESTED = 4

#: The characters of a string shown before it is cut.
MAX_TEXT = 72

#: The characters of a whole value, a string or a summary, shown before it is
#: cut: a row is at most one line of a notebook.
MAX_VALUE = 160

#: The items of a short tuple, list or mapping shown one by one.
MAX_INLINE = 6

#: How many levels of records held in fields are expanded below the record
#: displayed; a record further down is named, not expanded.
MAX_DEPTH = 1

#: The field names that are a unit on their own: a sampling rate, in hertz.
_NAMED_UNITS: Mapping[str, str] = MappingProxyType({"fs": "Hz"})

#: The units a name can end in, keyed by the words that spell them. A suffix
#: of several words is read first, so ``wind_speed_m_s`` is in m/s and not in
#: seconds, and ``decay_rates_db_per_m`` in dB/m and not in metres.
_UNITS: Mapping[str, str] = MappingProxyType(
    {
        # Levels.
        "db": "dB",
        "dba": "dB(A)",
        # Frequency.
        "hz": "Hz",
        "khz": "kHz",
        "m_hz": "m\N{MIDDLE DOT}Hz",
        # A sampling rate (``signal_fs``), in hertz.
        "fs": "Hz",
        # Length, area and volume.
        "m": "m",
        "mm": "mm",
        "um": "\N{MICRO SIGN}m",
        "ft": "ft",
        "m2": "m\N{SUPERSCRIPT TWO}",
        "mm2": "mm\N{SUPERSCRIPT TWO}",
        "m3": "m\N{SUPERSCRIPT THREE}",
        "mm3": "mm\N{SUPERSCRIPT THREE}",
        # Time.
        "s": "s",
        "seconds": "s",
        "ms": "ms",
        "hours": "h",
        "days": "d",
        "period_min": "min",
        # Angle.
        "deg": "\N{DEGREE SIGN}",
        "rad": "rad",
        # Pressure, mass and density.
        "pa": "Pa",
        "kpa": "kPa",
        "inhg": "inHg",
        "kg": "kg",
        "lb": "lb",
        "kg_m2": "kg/m\N{SUPERSCRIPT TWO}",
        "g_m2": "g/m\N{SUPERSCRIPT TWO}",
        "kg_m3": "kg/m\N{SUPERSCRIPT THREE}",
        "kg_mol": "kg/mol",
        "per_mm_kg_m2": "kg/m\N{SUPERSCRIPT TWO} per mm",
        "n_m3": "N/m\N{SUPERSCRIPT THREE}",
        "pa_s_m": "Pa\N{MIDDLE DOT}s/m",
        "pa_s_m2": "Pa\N{MIDDLE DOT}s/m\N{SUPERSCRIPT TWO}",
        "pa_s_m3": "Pa\N{MIDDLE DOT}s/m\N{SUPERSCRIPT THREE}",
        "kpa_s_m2": "kPa\N{MIDDLE DOT}s/m\N{SUPERSCRIPT TWO}",
        # Speed and acceleration.
        "m_s": "m/s",
        "mm_s": "mm/s",
        "m_s2": "m/s\N{SUPERSCRIPT TWO}",
        "rad_s": "rad/s",
        "kmh": "km/h",
        "kt": "kt",
        "knots": "kn",
        "mm_h": "mm/h",
        "ft_per_min": "ft/min",
        # Rates and gradients.
        "per_m": "1/m",
        "per_m2": "1/m\N{SUPERSCRIPT TWO}",
        "per_cm": "1/cm",
        "per_s": "1/s",
        "per_db": "1/dB",
        "per_mm_s": "s/mm",
        "db_s": "dB/s",
        "db_per_s": "dB/s",
        "db_per_m": "dB/m",
        "db_per_100m": "dB/100 m",
        "db_per_k": "dB/K",
        "db_per_kpa": "dB/kPa",
        "db_per_percent": "dB/%",
        "db_per_decade": "dB/decade",
        "db_per_wavelength": "dB/\N{GREEK SMALL LETTER LAMDA}",
        "np_per_m": "Np/m",
        "np_per_rad": "Np/rad",
        # Electrical quantities.
        "v": "V",
        "ma": "mA",
        "ohm": "\N{OHM SIGN}",
        "a_per_m": "A/m",
        "v_per_pa": "V/Pa",
        "mv_per_pa": "mV/Pa",
        "v2_per_pa2": "V\N{SUPERSCRIPT TWO}/Pa\N{SUPERSCRIPT TWO}",
        # Power.
        "hp": "hp",
        # A ratio.
        "percent": "%",
    }
)

#: The one-letter units, which a name also ends in when it is a symbol with a
#: subscript: ``alpha_s`` is the Sabine absorption coefficient, ``c_s`` a
#: wave speed and ``r_tr_s`` a sound reduction index, none of them in
#: seconds. One of these is a unit only after a word that is not a symbol.
_LETTER_UNITS = frozenset({"m", "s", "v"})

#: The one-letter units that are one only where a word of the name says the
#: quantity, each with the words that say it: ``temperature_c`` is in degrees
#: Celsius and ``delta_rw_c`` is the spectrum adaptation term C,
#: ``load_current_a`` is in amperes and ``sound_power_level_a`` is A-weighted,
#: ``inductance_h`` is in henries and ``curing_time_h`` in hours, and
#: ``subject_h`` is :math:`H_j` of ISO 4869-2.
_QUALIFIED_UNITS: Mapping[str, tuple[tuple[frozenset[str], str], ...]] = (
    MappingProxyType(
        {
            "c": ((frozenset({"temperature", "temperatures"}), "\N{DEGREE SIGN}C"),),
            "k": ((frozenset({"temperature", "temperatures"}), "K"),),
            "a": ((frozenset({"current", "currents"}), "A"),),
            "h": (
                (frozenset({"inductance"}), "H"),
                (frozenset({"time", "times"}), "h"),
            ),
        }
    )
)

#: The coordinates, after which a one-letter unit is one: ``x_m`` is in metres.
_COORDINATES = frozenset({"x", "y", "z"})

#: Names that end in a unit and are a symbol all the same: ``subject_m`` is
#: :math:`M_j` of ISO 4869-2 for each subject, in decibels.
_SYMBOLS = frozenset({"subject_m"})

#: The Greek letters a symbol is spelt with in a name.
_GREEK = frozenset(
    {
        "alpha",
        "beta",
        "gamma",
        "delta",
        "epsilon",
        "zeta",
        "eta",
        "theta",
        "kappa",
        "lambda",
        "mu",
        "nu",
        "xi",
        "rho",
        "sigma",
        "tau",
        "phi",
        "chi",
        "psi",
        "omega",
    }
)

#: The shortest word that is not a subscript (``tr``, ``ij``, ``2m`` are).
_WORD = 3

#: The longest suffix :data:`_UNITS` spells, in words.
_LONGEST = max(len(key.split("_")) for key in _UNITS)

#: Each outcome a title can show, with its colour: white on green, on red and
#: on grey, which read on the light and the dark themes of every notebook
#: front end.
_OUTCOMES: tuple[tuple[str, str], ...] = (
    ("PASS", "#1a7f37"),
    ("FAIL", "#cf222e"),
    ("no verdict", "#6e7781"),
)

#: Left-aligned cells: JupyterLab aligns the cells of an HTML table right.
_CELL = "text-align:left;vertical-align:top"


class Printer(Protocol):
    """The part of IPython's ``RepresentationPrinter`` a record writes to."""

    def text(self, obj: str) -> None:
        """Write *obj* as it is."""


@dataclasses.dataclass(frozen=True)
class _Row:
    """One field of a record, as the table shows it."""

    name: str
    value: str
    unit: str
    #: The record the field holds, when it is to be expanded below the row.
    nested: object = None


def unit_of(name: str) -> str:
    """The unit a field's name ends in, or ``""`` when it ends in none.

    The longest suffix in :data:`_UNITS` that leaves at least one word before
    it wins. A one-letter unit (:data:`_LETTER_UNITS`) counts only after a
    coordinate (``x_m``), or after a word of three letters or more that is
    not a Greek letter and when the word right before it is neither a single
    letter nor a Greek letter: a name such as ``alpha_s``, ``c_s`` or
    ``r_tr_s`` is a symbol and its subscript, not a quantity in seconds.
    Four more letters are a unit only where the name says their quantity
    (:data:`_QUALIFIED_UNITS`), and the names in :data:`_SYMBOLS` have none.

    :param name: The name of a field.
    :return: The unit's symbol, or an empty string.
    """
    if name in _NAMED_UNITS:
        return _NAMED_UNITS[name]
    if name in _SYMBOLS:
        return ""
    words = name.lower().split("_")
    if len(words) == 1:  # a unit needs a word before it
        return ""
    for count in range(min(_LONGEST, len(words) - 1), 1, -1):
        unit = _UNITS.get("_".join(words[-count:]))
        if unit is not None:
            return unit
    last, stem = words[-1], words[:-1]
    qualified = _QUALIFIED_UNITS.get(last)
    if qualified is not None:
        return next(
            (unit for quantities, unit in qualified if quantities.intersection(stem)),
            "",
        )
    if last in _LETTER_UNITS and _is_symbol(stem):
        return ""
    return _UNITS.get(last, "")


def _is_symbol(stem: list[str]) -> bool:
    """Whether the words before a one-letter unit spell a symbol."""
    if len(stem) == 1 and stem[0] in _COORDINATES:
        return False
    before = stem[-1]
    if len(before) == 1 or before in _GREEK:
        return True
    return not any(len(word) >= _WORD and word not in _GREEK for word in stem)


def verdict_of(record: object) -> str | None:
    """``"PASS"`` or ``"FAIL"`` for a record with a ``passes`` verdict.

    ``None`` for a record that has no ``passes``; ``"no verdict"`` when it
    holds no truth value, or when reading it raises, which a display must
    not: the exception is the record's to raise where the verdict is used.
    """
    if not hasattr(type(record), "passes") and "passes" not in _field_names(record):
        return None
    try:
        outcome = record.passes  # type: ignore[attr-defined]
    except Exception:  # a display never raises; where the verdict is read, it does
        return "no verdict"
    if isinstance(outcome, bool | np.bool_):
        return "PASS" if outcome else "FAIL"
    return "no verdict"


def _field_names(record: object) -> tuple[str, ...]:
    if dataclasses.is_dataclass(record) and not isinstance(record, type):
        return tuple(field.name for field in dataclasses.fields(record))
    names = getattr(type(record), "_fields", None)
    if isinstance(record, tuple) and isinstance(names, tuple):
        return names
    return ()


def _is_record(value: object) -> bool:
    """Whether *value* is a dataclass instance or a named tuple."""
    if dataclasses.is_dataclass(value):
        return not isinstance(value, type)
    return isinstance(value, tuple) and isinstance(
        getattr(type(value), "_fields", None), tuple
    )


def _fields(record: object) -> list[tuple[str, object]]:
    """The public fields of a record, in their order, read as attributes."""
    return [
        (name, getattr(record, name, None))
        for name in _field_names(record)
        if not name.startswith("_")
    ]


def _cut(text: str, limit: int = MAX_TEXT) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "\N{HORIZONTAL ELLIPSIS}"


def _number(value: float) -> str:
    """A number in at most five significant figures, for a range.

    Five keep a band centre of 19 952.6 Hz positional (``19953``) where four
    would print it as ``1.995e+04``.
    """
    return format(value, ".5g")


def _scalar(value: object) -> str | None:
    """The text of a scalar, or ``None`` when *value* is not one."""
    if value is None:
        return "None"
    if isinstance(value, enum.Enum):
        return f"{type(value).__name__}.{value.name}"
    if isinstance(value, bool | np.bool_):
        return str(bool(value))
    if isinstance(value, int | np.integer):
        return str(int(value))
    if isinstance(value, float | np.floating):
        return format(float(value), ".6g")
    if isinstance(value, complex | np.complexfloating):
        return format(complex(value), ".6g")
    if isinstance(value, str):
        return repr(_cut(value))
    if isinstance(value, bytes):
        return f"{len(value)} bytes"
    if isinstance(value, dt.date | dt.time | dt.timedelta):
        return str(value)
    if isinstance(value, os.PathLike):
        return _cut(os.fsdecode(value))
    if isinstance(value, np.ndarray) and value.ndim == 0:
        return _scalar(value.item())
    return None


def _shape(shape: tuple[int, ...]) -> str:
    return "\N{MULTIPLICATION SIGN}".join(str(n) for n in shape)


def _real_range(values: np.ndarray) -> str:
    """The range of a real array, NaN set aside and said."""
    low = np.fmin.reduce(values, axis=None)
    if np.isnan(low):
        return "all NaN"
    high = np.fmax.reduce(values, axis=None)
    text = f"{_number(float(low))} to {_number(float(high))}"
    if np.isnan(np.min(values)):
        text += ", with NaN"
    return text


def _magnitude_range(values: np.ndarray) -> str:
    """The range of the magnitude of a complex array, a block at a time.

    ``np.abs`` of the whole array would allocate a second array of its size.
    """
    flat = values.reshape(-1)
    block = 1 << 20
    lows: list[float] = []
    highs: list[float] = []
    for start in range(0, flat.size, block):
        magnitude = np.abs(flat[start : start + block])
        lows.append(float(np.fmin.reduce(magnitude)))
        highs.append(float(np.fmax.reduce(magnitude)))
    return "|z| " + _real_range(np.array([min(lows), max(highs)]))


def array_summary(values: np.ndarray) -> str:
    """One line for an array: its shape, its type and the range of its values.

    :param values: The array, of any shape and type.
    :return: The summary, without a single value of the array but its
        extremes (and, for a boolean array, how many are true).
    """
    head = f"array {_shape(values.shape)} {values.dtype}"
    if values.size == 0:
        return f"{head}, empty"
    kind = values.dtype.kind
    if kind not in "biufc":
        return head
    if values.size > RANGE_LIMIT:
        return f"{head}, range not read above {RANGE_LIMIT} values"
    if kind == "b":
        return f"{head}, {np.count_nonzero(values)} true"
    if kind in "iu":
        return f"{head}, {values.min()} to {values.max()}"
    if kind == "f":
        return f"{head}, {_real_range(values)}"
    return f"{head}, {_magnitude_range(values)}"


def _sequence_summary(values: Sequence[object]) -> str:
    """One line for a tuple or a list, short ones item by item."""
    kind = type(values).__name__ if type(values) in {tuple, list} else "sequence"
    if not values:
        return f"empty {kind}"
    if len(values) <= MAX_INLINE:
        texts = [_scalar(item) for item in values]
        if all(text is not None for text in texts):
            return "(" + ", ".join(text for text in texts if text is not None) + ")"
    count = len(values)
    if all(
        isinstance(item, int | float | np.integer | np.floating)
        and not isinstance(item, bool | np.bool_)
        for item in values
    ):
        if count > RANGE_LIMIT:
            return f"{kind} of {count} numbers"
        return f"{kind} of {count} numbers, {_real_range(np.asarray(values, float))}"
    if all(isinstance(item, str) for item in values):
        shown = ", ".join(repr(_cut(str(item))) for item in values[:3])
        return f"{kind} of {count} strings: {shown}, \N{HORIZONTAL ELLIPSIS}"
    first = values[0]
    if all(type(item) is type(first) for item in values):
        name = type(first).__name__
        if isinstance(first, np.ndarray):
            return f"{kind} of {count} arrays, the first {array_summary(first)}"
        return f"{kind} of {count} {name}"
    return f"{kind} of {count} items"


def _set_summary(values: set[object] | frozenset[object]) -> str:
    """One line for a set, its first members in the order of their text."""
    kind = type(values).__name__ if type(values) in {set, frozenset} else "set"
    if not values:
        return f"empty {kind}"
    shown = sorted(_cut(str(item)) for item in itertools.islice(values, MAX_INLINE))
    more = ", \N{HORIZONTAL ELLIPSIS}" if len(values) > MAX_INLINE else ""
    return f"{kind} of {len(values)}: {', '.join(shown)}{more}"


def _mapping_summary(values: Mapping[object, object]) -> str:
    """One line for a mapping, a short one entry by entry."""
    count = len(values)
    if count == 0:
        return "empty mapping"
    if count <= MAX_INLINE:
        pairs = [(_cut(str(key)), _scalar(item)) for key, item in values.items()]
        if all(text is not None for _, text in pairs):
            return "{" + ", ".join(f"{key}: {text}" for key, text in pairs) + "}"
    keys = ", ".join(_cut(str(key)) for key in itertools.islice(values, MAX_INLINE))
    more = ", \N{HORIZONTAL ELLIPSIS}" if count > MAX_INLINE else ""
    return f"mapping of {count} entries: {keys}{more}"


def _title(record: object) -> str:
    """A record's class, and its verdict when it has one."""
    name = type(record).__name__
    verdict = verdict_of(record)
    return name if verdict is None else f"{name}: {verdict}"


def _value(value: object) -> str:
    """The one-line text of a field's value."""
    scalar = _scalar(value)
    if scalar is not None:
        return scalar
    if _is_record(value):
        return f"{_title(value)} ({len(_fields(value))} fields)"
    if isinstance(value, np.ndarray):
        return array_summary(value)
    if isinstance(value, Mapping):
        return _mapping_summary(value)
    if isinstance(value, tuple | list):
        return _sequence_summary(value)
    if isinstance(value, set | frozenset):
        return _set_summary(value)
    if callable(value):
        return f"callable {getattr(value, '__qualname__', type(value).__name__)}"
    return f"{type(value).__name__} object"


def _rows(record: object, *, depth: int) -> tuple[list[_Row], int]:
    """The rows of a record's table, and how many fields were left out."""
    fields = _fields(record)
    rows: list[_Row] = []
    expanded = 0
    for name, value in fields[:MAX_ROWS]:
        nested = None
        if _is_record(value) and depth < MAX_DEPTH and expanded < MAX_NESTED:
            nested = value
            expanded += 1
        unit = "" if value is None else unit_of(name)
        rows.append(_Row(name, _cut(_value(value), MAX_VALUE), unit, nested))
    return rows, max(0, len(fields) - MAX_ROWS)


def _methods(record: object) -> list[str]:
    """The figure and the fiche a record can draw, by name."""
    return [
        f"{name}()"
        for name in ("plot", "report")
        if callable(getattr(type(record), name, None))
    ]


def _badge(verdict: str) -> str:
    colour = next(shade for label, shade in _OUTCOMES if label == verdict)
    return (
        f'<span style="background:{colour};color:#ffffff;border-radius:3px;'
        f'padding:0 6px;margin-left:6px;font-weight:bold">{verdict}</span>'
    )


def _html_table(record: object, *, depth: int) -> str:
    rows, left_out = _rows(record, depth=depth)
    verdict = verdict_of(record)
    caption = f"<strong>{html.escape(type(record).__name__)}</strong>"
    if verdict is not None:
        caption += _badge(verdict)
    parts = [
        '<table style="border-collapse:collapse;margin:0">',
        f'<caption style="caption-side:top;text-align:left;padding:2px 0">'
        f"{caption}</caption>",
        "<thead><tr>"
        + "".join(f'<th style="{_CELL}">{label}</th>' for label in _HEADER)
        + "</tr></thead>",
        "<tbody>",
    ]
    for row in rows:
        value = html.escape(row.value)
        if row.nested is not None:
            value = (
                f"<details><summary>{value}</summary>"
                f"{_html_table(row.nested, depth=depth + 1)}</details>"
            )
        parts.append(
            f'<tr><td style="{_CELL}"><code>{html.escape(row.name)}</code></td>'
            f'<td style="{_CELL}">{value}</td>'
            f'<td style="{_CELL}">{html.escape(row.unit)}</td></tr>'
        )
    if left_out:
        parts.append(
            f'<tr><td style="{_CELL}" colspan="3">'
            f"\N{HORIZONTAL ELLIPSIS} {left_out} more fields</td></tr>"
        )
    parts.append("</tbody></table>")
    return "".join(parts)


#: The column headings of a record's table.
_HEADER = ("field", "value", "unit")


def record_html(record: object) -> str:
    """The HTML a notebook shows for *record*: a table of its fields.

    The fragment is well-formed XML, under one ``<div>``, so a front end that
    sanitises HTML (JupyterLab with an untrusted notebook, a viewer of saved
    notebooks) still renders the table, and every text in it is escaped.

    :param record: A dataclass instance or a named tuple.
    :return: The fragment.
    """
    parts = ['<div class="phonometry-record">', _html_table(record, depth=0)]
    methods = _methods(record)
    if methods:
        parts.append(
            '<div style="font-size:smaller;opacity:0.8;padding-top:2px">'
            f"{html.escape(' and '.join(methods))}</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def _text_lines(rows: Iterable[_Row]) -> list[str]:
    rows = list(rows)
    name_width = max((len(row.name) for row in rows), default=0)
    value_width = max((len(row.value) for row in rows if row.unit), default=0)
    lines = []
    for row in rows:
        line = f"  {row.name.ljust(name_width)}  "
        line += f"{row.value.ljust(value_width)}  {row.unit}" if row.unit else row.value
        lines.append(line.rstrip())
    return lines


def record_text(record: object) -> str:
    """The plain text IPython shows for *record*, the table of the HTML.

    A record held in a field is one line here, its class and its verdict.

    :param record: A dataclass instance or a named tuple.
    :return: The text, one field per line under the record's title.
    """
    rows, left_out = _rows(record, depth=MAX_DEPTH)
    lines = [_title(record), *_text_lines(rows)]
    if left_out:
        lines.append(f"  \N{HORIZONTAL ELLIPSIS} {left_out} more fields")
    methods = _methods(record)
    if methods:
        lines.append(" and ".join(methods))
    return "\n".join(lines)


def record_pretty(record: object, printer: Printer, cycle: object) -> None:
    """Write :func:`record_text` to IPython's pretty printer.

    :param record: A dataclass instance or a named tuple.
    :param printer: IPython's pretty printer.
    :param cycle: Whether the record is reached again inside itself, which a
        frozen record never is; its class name alone is written then.
    """
    printer.text(f"{type(record).__name__}(...)" if cycle else record_text(record))


class RichDisplay:
    """A public record that shows itself as a table in IPython and Jupyter.

    Inherited by every public record of the library, directly or through
    :class:`~phonometry._internal.frozen.OwnsArrays`. A named tuple, which
    takes no base, defines the two methods in its body, each a call to
    :func:`record_html` or :func:`record_pretty`. Neither method computes
    anything of the record's own: each reads its fields, and the ``passes``
    of a verdict.

    IPython's pretty printer walks the class's bases in order and, in each,
    takes a ``_repr_pretty_`` or a ``__repr__`` of the class's own, whichever
    it meets first. :mod:`dataclasses` writes a ``__repr__`` into every
    record class, which a ``_repr_pretty_`` inherited from this base would
    come after, so each subclass is given the method in its own namespace as
    it is created; ``repr()`` keeps the dataclass's.
    """

    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Put :meth:`_repr_pretty_` in the subclass's own namespace."""
        super().__init_subclass__(**kwargs)
        if "_repr_pretty_" not in vars(cls):
            type.__setattr__(cls, "_repr_pretty_", RichDisplay._repr_pretty_)

    def _repr_html_(self) -> str:
        """The table Jupyter, JupyterLab, VS Code and Colab render."""
        return record_html(self)

    def _repr_pretty_(self, printer: Printer, cycle: object) -> None:
        """The table in plain text, for the IPython terminal."""
        record_pretty(self, printer, cycle)
