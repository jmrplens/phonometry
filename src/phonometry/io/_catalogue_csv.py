#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A catalogue as a spreadsheet saves it: a CSV file and its JSON header.

Data sheets are typed into spreadsheets, and a spreadsheet saves a CSV file.
A catalogue CSV holds one table, one row per line under a first line that
names the columns. Its header is the catalogue's JSON document without its
rows, in a file beside it named as the CSV file with ``.phonometry.json``
after it, and it declares how the cells are written::

    "csv": {"delimiter": ";", "decimal": ","}

The delimiter is ``","``, ``";"`` or a tab; the decimal mark ``"."`` or
``","``, and a decimal comma never sits between commas. Nothing about the
dialect is guessed from the file. When every number that fails is written
with the other decimal mark, or the first line splits at another delimiter,
the refusal says which one to declare.

**The columns.** ``key``; the fields of the row class, as text, as flags and
as numbers, each in its own unit or in another of the same kind, as in a
JSON document; ``basis``, the entry of the row as a whole, where an empty
cell takes the document's; ``provenance.page``, ``provenance.printed_table``,
``provenance.laboratory``, ``provenance.accreditation``,
``provenance.report``, ``provenance.test_date`` and
``provenance.test_standard``, which narrow the document's provenance for
the row; and any number of columns of the caller's own, named ``x-...``,
kept as text. A column is named once, and a name the reader does not know is
refused with the name most like it.

**The cells.** A numeric cell holds one thing, in a closed grammar:

=====================  ==================================================
Cell                   Meaning
=====================  ==================================================
(empty)                The document prints nothing there.
``0.85``               A value.
``~0.85``              A value, approximate.
``<=30``, ``<30``      An upper bound and no value (``≤30`` too).
``>=5``, ``>5``        A lower bound and no value (``≥5`` too).
``0.30..0.50``         A range and no value; ``~`` may stand before it.
``0.85±0.05``          A value and its plus-or-minus (``0.85+/-0.05`` too).
``[AFr5]``             What the document prints where the number would be.
``true``, ``false``    A flag, and only in a column of flags.
=====================  ==================================================

A number is written with the declared decimal mark and never with a
thousands separator; its minus sign may be U+2212. What one cell cannot say
is written in a JSON document instead: several readings, a misprint, a cell
carried from another row, a figure converted from a unit no family holds, a
credit, a basis or a test standard for one cell, a bound or a range with a
plus-or-minus, and an approximate bound. A text where a number goes is
refused, and never read as a word, a ``NaN`` or a zero: a word goes between
brackets.

The file is UTF-8, with or without the byte order mark a spreadsheet writes
when it saves "CSV UTF-8". A text that starts with ``=``, ``+``, ``-``,
``@``, a tab or a carriage return is written after an apostrophe, so that a
spreadsheet opening the file does not run it as a formula, and the reader
takes the apostrophe off again; a text that starts with an apostrophe of its
own keeps it. Every problem is placed at its line and its column, lettered
as a spreadsheet letters them.
"""

from __future__ import annotations

import csv
import dataclasses
import errno
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, NamedTuple

from .._internal.catalogue import (
    _NOUNS,
    CatalogueError,
    CatalogueIssue,
    PrintedNumber,
)
from ._catalogue import (
    _EXTRA,
    _FORBIDDEN,
    _KEY,
    _MAX_BYTES,
    _MAX_ROWS,
    _ROW_PROVENANCE,
    _SHOWN,
    _UNSAFE,
    _WORD,
    CATALOGUE_SCHEMA,
    CSV_HEADER_TAIL,
    _closest,
    _decode,
    _finish,
    _Issues,
    _pointer,
    _quote,
    _Reader,
    _refusal,
    _scalar,
    _size_refusal,
    _text_of,
)
from ._sidecar import SIDECAR_SCHEMA

if TYPE_CHECKING:
    import os

    from .._internal.catalogue import CatalogueRow
    from ._catalogue import Catalogue, _Names

#: The delimiters and the decimal marks a header may declare.
_DELIMITERS = (",", ";", "\t")
_DECIMALS = (".", ",")
#: The largest header read, checked on disk before a byte is read.
_MAX_HEADER = 64 * 1024
#: A text the writer writes after an apostrophe: one a spreadsheet would run
#: as a formula, or one that already reads as such an escape.
_NEEDS_APOSTROPHE = re.compile(r"'*[=+\-@\t\r]")
#: A text the reader takes the first apostrophe off: an escaped one.
_ESCAPED = re.compile(r"'+[=+\-@\t\r]")
#: The spaces a thousands separator is written with.
_SPACES = " \u00a0\u2009\u202f"
#: What a refusal calls each decimal mark.
_MARKS: Mapping[str, str] = MappingProxyType({".": "point", ",": "comma"})
#: A number with either decimal mark, as a refused cell may write it.
_FIGURE = r"[-+\u2212]?[0-9]+(?:[.,][0-9]+)?"
#: The hedges a row writes as lists of fields, and so points at by index.
_LISTED = ("approximate", "bounded_above", "bounded_below")
#: What a bound's sign says of it.
_BOUNDS: Mapping[str, str] = MappingProxyType(
    {"<=": "above", "<": "above", ">=": "below", ">": "below"}
)
#: The provenance a row narrows in a column of its own, each spelled as the
#: column is: every field a row may narrow but the standards of single
#: fields, which only a JSON document writes.
_PROVENANCE_COLUMNS: Mapping[str, str] = MappingProxyType(
    {
        f"provenance.{name}": name
        for name in _ROW_PROVENANCE
        if name != "field_test_standards"
    }
)
#: The names a first line uses besides the fields of the row class.
_OWN_COLUMNS = frozenset({"key", "basis", *_PROVENANCE_COLUMNS})
#: The hedges a CSV writes in the cell, not in a column of their own.
_IN_THE_CELL: Mapping[str, str] = MappingProxyType(
    {
        "approximate": "an approximate value in its own cell, as ~0.85",
        "ranges": "a range in its own cell, as 0.30..0.50, and a bound as <=30 or >=5",
        "bounded_above": "an upper bound in its own cell, as <=30",
        "bounded_below": "a lower bound in its own cell, as >=5",
        "uncertainty": "a plus-or-minus in its own cell, as 0.85±0.05",
        "unquantified": (
            "what the document prints in place of a number in its own cell, "
            "between brackets, as [AFr5]"
        ),
    }
)
#: How a JSON document writes what a CSV cell cannot hold.
_IN_JSON: Mapping[str, str] = MappingProxyType(
    {
        "reported": '"reported": {"<field>": [0.30, 0.35]}',
        "misprinted": '"misprinted": {"<field>": "why the value is wrong"}',
        "not_derivable": '"not_derivable": {"<field>": "why"}',
        "carried": '"carried": {"<field>": "from the row above"}',
        "converted": (
            '"converted": {"<field>": ["3e5", "psi"]} beside the value (a CSV '
            "names a column for the unit instead, as thickness_cm)"
        ),
        "borrowed": '"borrowed": {"<field>": "<material>"}',
        "attributed_to": '"attributed_to": {"<field>": "<who>"}',
        "basis": '"basis": {"<field>": "measured"}',
        "field_test_standards": (
            '"provenance": {"field_test_standards": {"<field>": "<standard>"}}'
        ),
    }
)


def _letters(index: int) -> str:
    """The letters a spreadsheet names a column by, from ``A`` for the first."""
    letters = ""
    number = index + 1
    while number:
        number, rest = divmod(number - 1, 26)
        letters = chr(ord("A") + rest) + letters
    return letters


def _in_json(name: str, subject: str = "") -> str:
    """Why a CSV cell cannot hold *name*, and how a JSON document writes it."""
    return (
        f"{subject or name} is written only in a JSON catalogue, as "
        f"{_IN_JSON[name]}; a CSV cell holds one value, bound, range or word"
    )


def _unescape(text: str) -> str:
    """A text cell as the row holds it: the formula guard taken off."""
    return text[1:] if _ESCAPED.match(text) else text


def _escape(text: str) -> str:
    """A text as a CSV cell writes it, so no spreadsheet runs it as a formula."""
    return f"'{text}" if _NEEDS_APOSTROPHE.match(text) else text


# ---------------------------------------------------------------------------
# The dialect
# ---------------------------------------------------------------------------
class _Dialect(NamedTuple):
    """How a CSV file writes its cells, as its header declares it."""

    delimiter: str
    decimal: str


def _dialect_problems(held: object) -> list[tuple[str, str]]:
    """What is wrong with the ``csv`` object of a header, each at its pointer."""
    if not isinstance(held, Mapping):
        return [
            (
                "/csv",
                f"holds {_quote(held)}, not an object; declare the dialect as "
                '"csv": {"delimiter": ";", "decimal": ","}',
            )
        ]
    problems = [
        (
            _pointer("csv", key),
            f"the dialect has no {key!r}; it declares a delimiter and a decimal mark",
        )
        for key in held
        if key not in ("delimiter", "decimal")
    ]
    for key, allowed, said in (
        ("delimiter", _DELIMITERS, '",", ";" or a tab, "\\t"'),
        ("decimal", _DECIMALS, '"." or ","'),
    ):
        if key not in held:
            problems.append(("/csv", f"needs {key!r}: {said}"))
        elif not (isinstance(held[key], str) and held[key] in allowed):
            problems.append(
                (_pointer("csv", key), f"is {_quote(held[key])}; it is {said}")
            )
    if not problems and held["delimiter"] == held["decimal"] == ",":
        problems.append(
            (
                "/csv",
                'declares "decimal": "," beside "delimiter": ","; a decimal '
                'comma needs another delimiter, ";" as a spreadsheet uses beside '
                "it, or a tab",
            )
        )
    return problems


def check_dialect(delimiter: str, decimal: str) -> _Dialect:
    """The dialect :func:`~phonometry.io.write_catalogue` is asked to write.

    :raises ValueError: for a delimiter or a decimal mark a catalogue CSV
        does not take, and for a decimal comma between commas.
    """
    if delimiter not in _DELIMITERS:
        msg = (
            f"delimiter={delimiter!r}: a catalogue CSV is delimited by ',', ';' or "
            "a tab, '\\t'"
        )
        raise ValueError(msg)
    if decimal not in _DECIMALS:
        msg = f"decimal={decimal!r}: a catalogue CSV's decimal mark is '.' or ','"
        raise ValueError(msg)
    if delimiter == decimal:
        msg = (
            "decimal=',' with delimiter=',': a decimal comma needs another "
            "delimiter, ';' as a spreadsheet uses beside it, or a tab"
        )
        raise ValueError(msg)
    return _Dialect(delimiter, decimal)


# ---------------------------------------------------------------------------
# A cell
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _Cell:
    """What one numeric cell says, in the grammar of the module docstring."""

    value: PrintedNumber | None = None
    low: PrintedNumber | None = None
    high: PrintedNumber | None = None
    #: ``"above"`` or ``"below"`` for a bound, empty otherwise.
    bound: str = ""
    approximate: bool = False
    uncertainty: PrintedNumber | None = None
    word: str | None = None
    #: Whether a number of the cell is written with the declared decimal mark.
    marked: bool = False


@dataclass(frozen=True)
class _Bad:
    """Why a numeric cell says nothing the grammar reads."""

    message: str
    #: Whether the cell reads under the other decimal mark, which is what
    #: a refusal proposing the other dialect counts.
    foreign: bool = False


def _number(decimal: str) -> str:
    """A number as a cell writes it with the decimal mark *decimal*."""
    return rf"[-+\u2212]?[0-9]+(?:{re.escape(decimal)}[0-9]+)?(?:[eE][-+]?[0-9]+)?"


def _figure(token: str, decimal: str) -> PrintedNumber:
    """A number of a cell as a JSON document writes it, digits and all."""
    text = token.replace("\u2212", "-").removeprefix("+")
    return PrintedNumber(text.replace(decimal, ".") if decimal != "." else text)


def _grammar(text: str, decimal: str) -> _Cell | _Bad | None:
    """What *text* says in the grammar of a cell, or ``None`` when nothing."""
    body = (
        text.replace("\u2212", "-")
        .replace("\u2264", "<=")
        .replace("\u2265", ">=")
        .replace("\u00b1", "+/-")
    )
    approximate = body.startswith("~")
    if approximate:
        body = body[1:].lstrip()
    number = _number(decimal)
    spread = rf"(?:\s*\+/-\s*({number}))?"
    found = re.fullmatch(rf"(<=|>=|<|>)\s*({number}){spread}", body)
    if found is not None:
        sign, end, plus = found.groups()
        if approximate:
            return _Bad(
                f"{_quote(text)} is an approximate bound, which a CSV cell does "
                "not write; write the row in a JSON catalogue, with the field in "
                '"approximate" beside its "ranges"'
            )
        if plus is not None:
            return _Bad(
                f"{_quote(text)} is a bound with a plus-or-minus, which a CSV "
                "cell does not write; write the row in a JSON catalogue, with "
                '"uncertainty" beside its "ranges"'
            )
        figure = _figure(end, decimal)
        side = _BOUNDS[sign]
        return _Cell(
            low=figure if side == "below" else None,
            high=figure if side == "above" else None,
            bound=side,
            marked=decimal in end,
        )
    found = re.fullmatch(rf"({number})\s*\.\.\s*({number}){spread}", body)
    if found is not None:
        low, high, plus = found.groups()
        if plus is not None:
            return _Bad(
                f"{_quote(text)} is a range with a plus-or-minus, which a CSV "
                "cell does not write; write the row in a JSON catalogue, with "
                '"uncertainty" beside its "ranges"'
            )
        return _Cell(
            low=_figure(low, decimal),
            high=_figure(high, decimal),
            approximate=approximate,
            marked=decimal in low or decimal in high,
        )
    found = re.fullmatch(rf"({number}){spread}", body)
    if found is not None:
        value, plus = found.groups()
        return _Cell(
            value=_figure(value, decimal),
            uncertainty=None if plus is None else _figure(plus, decimal),
            approximate=approximate,
            marked=decimal in value or (plus is not None and decimal in plus),
        )
    return None


def _cell(cell: str, dialect: _Dialect, noun: str) -> _Cell | _Bad | None:
    """What a numeric cell says, ``None`` for an empty one, or why it says nothing."""
    text = cell.strip()
    if not text:
        return None
    unsafe = _UNSAFE.search(text)
    if unsafe is not None:
        return _Bad(
            f"{_quote(text)} holds the character U+{ord(unsafe.group()):04X}; a "
            "catalogue's cell holds no control character but the tab and the line "
            "feed, and no mark that reorders text"
        )
    if text.startswith("["):
        if len(text) > 1 and text.endswith("]"):
            word = text[1:-1]
            if word.strip():
                return _Cell(word=word)
            return _Bad(
                f"{_quote(text)} holds no word; leave the cell empty where {noun} "
                "prints nothing"
            )
        return _Bad(
            f"{_quote(text)} opens a bracket it does not close; write what {noun} "
            "prints where the number would be between brackets, as [AFr5]"
        )
    lowered = text.lower()
    if lowered in ("true", "false"):
        return _Bad(f"{_quote(text)} is a flag, and the column holds numbers")
    if lowered.lstrip("+-\u2212") in ("nan", "inf", "infinity"):
        return _Bad(
            f"{_quote(text)} is not a finite number; leave the cell empty where "
            f"{noun} prints nothing"
        )
    return _grammar(text, dialect.decimal) or _diagnose(text, dialect, noun)


def _thousands(text: str, declared: str) -> _Bad | None:
    """Why *text*, a number with a thousands separator, is refused, if it is one.

    A separator that stands more than once, or before a fraction written
    with the other mark, can only separate thousands. One that stands once
    in a whole number could be the other decimal mark as well, and is only
    called ambiguous.
    """
    found = re.fullmatch(
        r"(?P<lead>~?\s*[-+\u2212]?)(?P<whole>[1-9][0-9]{0,2}(?P<sep>[.,])[0-9]{3}"
        r"(?:(?P=sep)[0-9]{3})*)(?:(?P<dec>[.,])(?P<fraction>[0-9]+))?",
        text,
    )
    if found is None or found["dec"] == found["sep"]:
        return None
    sep, dec = found["sep"], found["dec"]
    lead = re.sub(r"\s+", "", found["lead"])
    digits = found["whole"].replace(sep, "")
    if dec is not None:
        if dec != declared:
            return _Bad(
                f"{_quote(text)} separates thousands with a {_MARKS[sep]} and "
                f"writes a decimal {_MARKS[dec]}, where the header declares "
                f'"decimal": {json.dumps(declared)}; a catalogue never reads a '
                "thousands separator: write the number without it, and declare "
                f'"decimal": {json.dumps(dec)} if the file writes decimal '
                f"{_MARKS[dec]}s",
                foreign=True,
            )
        plain = f"{lead}{digits}{dec}{found['fraction']}"
    elif sep != declared and found["whole"].count(sep) == 1:
        return _Bad(
            f"{_quote(text)} is ambiguous: the header declares "
            f'"decimal": {json.dumps(declared)}, so the {_MARKS[sep]} can only '
            "separate thousands, and a catalogue never reads a thousands "
            f"separator; write {lead}{digits}, or declare "
            f'"decimal": {json.dumps(sep)} if the file writes decimal '
            f"{_MARKS[sep]}s"
        )
    elif found["whole"].count(sep) == 1:
        return None
    else:
        plain = f"{lead}{digits}"
    return _Bad(
        f"{_quote(text)} separates thousands with a {_MARKS[sep]}, which a "
        f"catalogue never reads; write {plain}"
    )


def _diagnose(text: str, dialect: _Dialect, noun: str) -> _Bad:
    """Why *text* is not a cell, in the terms most likely to mend it."""
    declared = dialect.decimal
    other = "," if declared == "." else "."
    said = f'"decimal": {json.dumps(declared)}'
    grouped = _thousands(text, declared)
    if grouped is not None:
        return grouped
    if isinstance(_grammar(text, other), _Cell):
        return _Bad(
            f"{_quote(text)} writes a decimal {_MARKS[other]}, and the header "
            f"declares {said}",
            foreign=True,
        )
    if re.fullmatch(
        rf"~?\s*[-+\u2212]?[0-9]{{1,3}}(?:[{_SPACES}][0-9]{{3}})+(?:[.,][0-9]+)?", text
    ):
        return _Bad(
            f"{_quote(text)} separates thousands with a space, which a catalogue "
            "never reads; write the number without it"
        )
    marks = f", each number with the decimal mark the header declares, {said}"
    found = re.fullmatch(rf"(~?)\s*({_FIGURE})\s*\+-\s*({_FIGURE})", text)
    if found is not None:
        approximate, value, spread = found.groups()
        return _Bad(
            f"{_quote(text)} writes a plus-or-minus as '+-'; write "
            f"{approximate}{value}\u00b1{spread}, or {approximate}{value}+/-{spread}"
            + (marks if other in value + spread else "")
        )
    found = re.fullmatch(
        rf"(~?)\s*({_FIGURE})\s*[-\u2010-\u2013\u2212]\s*({_FIGURE})", text
    )
    if found is not None:
        approximate, low, high = found.groups()
        return _Bad(
            f"{_quote(text)} is a range written with a dash, which reads as the "
            "minus sign of a negative number; a CSV cell writes a range with two "
            f"points, as {approximate}{low}..{high}"
            + (marks if other in low + high else "")
        )
    found = re.fullmatch(
        rf"(?:~|<=|>=|<|>|\u2264|\u2265)?\s*{_FIGURE}\s*"
        r"([A-Za-z\u00b5\u03bc\u00b0%][^\[\]]*)",
        text,
    )
    if found is not None:
        return _Bad(
            f"{_quote(text)} writes {_quote(found[1])} after the number; a cell "
            "holds the number alone, and a unit goes in the column's name, as "
            "thickness_cm"
        )
    separators = r"\s*[;/|]\s*|\s+" + (r"|\s*,\s*" if declared == "." else "")
    parts = [part for part in re.split(separators, text) if part]
    if len(parts) > 1 and all(
        re.fullmatch(_number(declared), part) is not None for part in parts
    ):
        return _Bad(
            f"{_quote(text)} holds several numbers; "
            + _in_json("reported", "a list of readings with no single value")
        )
    printable = len(text) <= _WORD and text.isprintable()
    shown = f"as [{text}]" if printable else "between brackets"
    return _Bad(
        f"{_quote(text)} is not a number; if {noun} prints this text where the "
        f"number would be, write it {shown}"
    )


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _Column:
    """One column, as the first line names it and the reader reads it."""

    name: str
    letters: str
    #: ``"key"``, ``"text"``, ``"flag"``, ``"number"``, ``"basis"``,
    #: ``"provenance"``, ``"extra"``, or ``"skip"`` for a column refused.
    role: str
    #: The field a text, flag or number fills; the provenance field a
    #: provenance column narrows.
    target: str = ""


@dataclass
class _Record:
    """Where one row of the document stands in the CSV file."""

    line: int
    #: What the row writes, by the name the document pass meets it under,
    #: to the column that holds it.
    members: dict[str, int] = field(default_factory=dict)
    #: The fields a row lists in a hedge, in order, to the pointers' indices.
    lists: dict[str, list[str]] = field(default_factory=dict)
    #: The field each column fills, for an issue about a field.
    fields: dict[str, int] = field(default_factory=dict)


class _Sheet:
    """A CSV file read into the rows of a document, with every place kept.

    The rows are handed to the same pass as a JSON document's, with every
    cell as the member a JSON row would write, and each issue that pass
    finds at a pointer into a row is placed back at the line and the column
    the cell came from.
    """

    def __init__(self, label: str, header_label: str, noun: str) -> None:
        self.label = label
        self.header_label = header_label
        self.noun = noun
        self.columns: list[_Column] = []
        self.records: list[_Record] = []
        self.first = 1
        #: The numbers read with the declared decimal mark, and the cells
        #: refused for being written with the other one.
        self.marked = 0
        self.foreign = 0
        self.issues: _Issues = _Issues(label, self.place)

    # -- places --------------------------------------------------------------
    def place(self, location: str, field_name: str) -> tuple[str, str, int]:
        """The file, the place and the rank of an issue found at *location*."""
        if location.startswith("line "):
            line = location.removeprefix("line ").partition(",")[0]
            return self.label, location, int(line)
        head, index, *rest = [
            part.replace("~1", "/").replace("~0", "~")
            for part in location.split("/")[1:]
        ] + ["", ""]
        if head != "rows" or not index.isdigit() or int(index) >= len(self.records):
            return self.header_label, location, 0
        record = self.records[int(index)]
        column = self.column_of(record, [part for part in rest if part], field_name)
        where = f"line {record.line}"
        if column is not None:
            named = self.columns[column]
            where += f", column {named.letters} ({named.name})"
        return self.label, where, record.line

    @staticmethod
    def column_of(record: _Record, rest: list[str], field_name: str) -> int | None:
        """The column a pointer into a row names, or the one its field fills."""
        if rest and rest[0] in record.members:
            return record.members[rest[0]]
        if len(rest) > 1:
            hedge, entry = rest[0], rest[1]
            if hedge in _LISTED and entry.isdigit():
                listed = record.lists.get(hedge, [])
                if int(entry) < len(listed):
                    return record.members.get(listed[int(entry)])
            elif hedge == "provenance":
                return record.members.get(f"provenance.{entry}")
            elif entry in record.members:
                return record.members[entry]
        return record.fields.get(field_name)

    # -- the header ------------------------------------------------------------
    def document(self, document: object, text: str, reader: _Reader) -> object:
        """The document the pass reads: the header, with the file's lines as rows."""
        if not isinstance(document, Mapping):
            return document
        merged = {
            key: value for key, value in document.items() if key not in ("rows", "csv")
        }
        if "rows" in document:
            self.issues.error(
                "/rows",
                f"holds rows, and the rows of a catalogue CSV are the lines of "
                f"{self.label}; its header holds none",
            )
        if "csv" not in document:
            self.issues.error(
                "",
                "declares no dialect: the header of a catalogue CSV says how its "
                'cells are written, as "csv": {"delimiter": ";", "decimal": ","}',
            )
            return merged
        problems = _dialect_problems(document["csv"])
        for where, message in problems:
            self.issues.error(where, message)
        if not problems:
            held = document["csv"]
            rows = self.read(text, _Dialect(held["delimiter"], held["decimal"]), reader)
            if rows:
                merged["rows"] = rows
        return merged

    # -- the lines -------------------------------------------------------------
    def read(
        self, text: str, dialect: _Dialect, reader: _Reader
    ) -> list[dict[str, Any]] | None:
        """Every line of the file as the row a JSON document would write."""
        lines = csv.reader(
            StringIO(text, newline=""), delimiter=dialect.delimiter, strict=True
        )
        records: list[tuple[int, list[str]]] = []
        end = 0
        try:
            for cells in lines:
                records.append((end + 1, cells))
                end = lines.line_num
        except csv.Error as error:
            self.issues.error(
                f"line {lines.line_num}",
                f"cannot be split into cells ({error}); a cell that holds the "
                "delimiter, a line break or a quote is written between quotes, "
                "with each quote in it doubled",
            )
            return None
        if not records:
            self.issues.error(
                "line 1",
                "the file is empty: its first line names the columns, and each "
                "line after it is a row",
            )
            return None
        self.first, names = records[0]
        if not self.head(names, dialect, reader):
            return None
        body = [
            (line, cells)
            for line, cells in records[1:]
            if any(cell.strip() for cell in cells)
        ]
        if not body:
            self.issues.error(
                f"line {self.first}",
                "names the columns, and no row follows; a catalogue holds at least one",
            )
            return None
        if len(body) > _MAX_ROWS:
            self.issues.error(
                f"line {self.first}",
                f"heads {len(body)} rows, and a catalogue holds at most {_MAX_ROWS}",
            )
            return None
        rows: list[dict[str, Any]] = []
        for line, cells in body:
            if len(cells) != len(self.columns):
                self.issues.error(
                    f"line {line}",
                    f"holds {len(cells)} cells, and the first line names "
                    f"{len(self.columns)} columns; every line holds a cell for "
                    "each column, empty or not",
                )
                continue
            rows.append(self.row(len(rows), line, cells, dialect, reader))
        if self.foreign and not self.marked:
            other = "," if dialect.decimal == "." else "."
            self.issues.error(
                "/csv/decimal",
                f"is {json.dumps(dialect.decimal)}, and every number of "
                f"{self.label} with a fraction is written with "
                f'{json.dumps(other)}; declare "decimal": {json.dumps(other)} '
                "if that is the file's decimal mark",
            )
        return rows

    def head(self, names: list[str], dialect: _Dialect, reader: _Reader) -> bool:
        """The columns the first line names; whether the rows can be read."""
        if len(names) == 1:
            for other in _DELIMITERS:
                parts = names[0].split(other)
                if other != dialect.delimiter and len(parts) > 1 and "key" in parts:
                    self.issues.error(
                        "/csv/delimiter",
                        f"is {json.dumps(dialect.delimiter)}, and the first line "
                        f"of {self.label} is one column that splits into "
                        f"{len(parts)} at {json.dumps(other)}; declare "
                        f'"delimiter": {json.dumps(other)}',
                    )
                    return False
        seen: dict[str, str] = {}
        self.columns = [
            self.column(name, index, reader, seen) for index, name in enumerate(names)
        ]
        where = f"line {self.first}"
        roles = {column.role for column in self.columns}
        if "key" not in roles:
            self.issues.error(
                where, "names no 'key' column, and every row needs a key of its own"
            )
            return False
        filled = {column.target for column in self.columns if column.role != "skip"}
        missing = [name for name in reader.required if name not in filled]
        for name in missing:
            self.issues.error(
                where,
                f"names no column that holds {name!r}, which every "
                f"{reader.row_type.__name__} row needs",
                field_name=name,
            )
        return not missing

    def column(
        self, name: str, index: int, reader: _Reader, seen: dict[str, str]
    ) -> _Column:
        """One column of the first line, with its role, or refused and skipped."""
        letters = _letters(index)
        where = f"line {self.first}, column {letters}"
        role, target, problem = self.role(name, reader)
        if not name.strip():
            problem = "has no name; name the column for what it holds, or delete it"
        elif _UNSAFE.search(name):
            problem = (
                f"is named {_quote(name)}, with a control character or a mark "
                "that reorders text"
            )
        elif name in seen:
            problem = (
                f"is named {name!r}, as column {seen[name]} is; a column is named once"
            )
        seen.setdefault(name, letters)
        if problem:
            self.issues.error(where, problem, field_name=name)
            return _Column(name, letters, "skip")
        return _Column(name, letters, role, target)

    @staticmethod
    def role(name: str, reader: _Reader) -> tuple[str, str, str]:
        """What a column named *name* holds: role, target, and why not."""
        names = reader.names
        if name in ("key", "basis"):
            return name, name, ""
        if name in _PROVENANCE_COLUMNS:
            return "provenance", _PROVENANCE_COLUMNS[name], ""
        if name.startswith("x-"):
            if _EXTRA.fullmatch(name):
                return "extra", name, ""
            return (
                "",
                "",
                (
                    f"{name!r} is not a column name: after 'x-' come letters, "
                    "digits and ._+- characters"
                ),
            )
        if name == "provenance.field_test_standards":
            return "", "", _in_json("field_test_standards")
        if name.startswith("provenance.") or name == "provenance":
            close = (
                _closest(name, frozenset(_PROVENANCE_COLUMNS)) if "." in name else ""
            )
            hint = f"; did you mean {close!r}?" if close else ""
            return (
                "",
                "",
                (
                    "a row narrows its provenance in the columns "
                    f"{', '.join(_PROVENANCE_COLUMNS)}{hint}"
                ),
            )
        if name.startswith("basis.") and name.removeprefix("basis.") in names.kinds:
            return "", "", _in_json("basis", "a basis for one cell")
        if name in _FORBIDDEN:
            return "", "", _FORBIDDEN[name]
        if name in _IN_THE_CELL:
            return (
                "",
                "",
                f"a CSV writes {_IN_THE_CELL[name]}, and has no {name} column",
            )
        if name in _IN_JSON:
            return "", "", _in_json(name)
        kind = names.kinds.get(name, "")
        if kind in ("number", "whole"):
            return "number", name, ""
        if kind in ("flag", "text"):
            return kind, name, ""
        if kind:
            return (
                "",
                "",
                (
                    f"{name} holds a set or a mapping, which only a JSON catalogue writes"
                ),
            )
        if name in names.spellings.aliases:
            return "number", names.spellings.aliases[name][0], ""
        return "", "", _Sheet.unknown(name, names)

    @staticmethod
    def unknown(name: str, names: _Names) -> str:
        """Why a column no row class knows is refused, with the name it means.

        A spreadsheet's ``Name`` or ``Key`` is told the name it spells in
        other letters; any other is told the name most like it.
        """
        values = frozenset(
            field_name
            for field_name, field_kind in names.kinds.items()
            if field_kind in ("number", "whole", "text", "flag")
        ) - {"source", "table"}
        folded = {
            known.casefold(): known
            for known in (*_OWN_COLUMNS, *values, *names.spellings.aliases)
        }
        close = folded.get(name.casefold(), "") or _closest(name, _OWN_COLUMNS)
        if close:
            return f"no column {name!r}; did you mean {close!r}?"
        return names.resolve(name, values, frozenset())[1]

    # -- a row -----------------------------------------------------------------
    def row(
        self,
        index: int,
        line: int,
        cells: list[str],
        dialect: _Dialect,
        reader: _Reader,
    ) -> dict[str, Any]:
        """One line as the row a JSON document would write."""
        record = _Record(line)
        for number, column in enumerate(self.columns):
            if column.role in ("text", "flag", "number"):
                record.fields.setdefault(column.target, number)
        self.records.append(record)
        key = next(
            (
                cell
                for column, cell in zip(self.columns, cells, strict=True)
                if column.role == "key"
            ),
            "",
        )
        held: dict[str, Any] = {}
        for number, (column, cell) in enumerate(zip(self.columns, cells, strict=True)):
            if column.role == "skip":
                continue
            problem = self.take(held, record, number, column, cell, dialect)
            if problem is not None:
                self.issues.error(
                    _pointer("rows", index, column.name),
                    problem.message,
                    row_key=key if _KEY.fullmatch(key) else "",
                    field_name=column.target,
                )
                reader.failed.add(index)
        return held

    def take(
        self,
        held: dict[str, Any],
        record: _Record,
        number: int,
        column: _Column,
        cell: str,
        dialect: _Dialect,
    ) -> _Bad | None:
        """Put one cell into the row, or say why it cannot go there.

        A cell that says something is recorded as the column's, so that an
        issue the document pass finds in it is placed back in that column.
        """
        role, name = column.role, column.name
        if role == "number":
            return self.take_number(held, record, number, column, cell, dialect)
        problem = None
        if role in ("flag", "basis"):
            word = cell.strip()
            if not word:
                return None
            if role == "basis":
                held["basis"] = {"row": word}
            elif word.lower() in ("true", "false"):
                held[name] = word.lower() == "true"
            else:
                problem = _Bad(
                    f"{_quote(word)} is not a flag: a flag is true or false, and "
                    "nothing else"
                )
        else:
            text = cell if role == "key" else _unescape(cell.replace("\r\n", "\n"))
            if not text:
                return None
            if role == "provenance":
                held.setdefault("provenance", {})[column.target] = text
            else:
                held[name] = text
        record.members[name] = number
        if role in ("text", "flag"):
            record.fields[column.target] = number
        return problem

    def take_number(
        self,
        held: dict[str, Any],
        record: _Record,
        number: int,
        column: _Column,
        cell: str,
        dialect: _Dialect,
    ) -> _Bad | None:
        """Put one numeric cell into the row, as the hedges a JSON row writes."""
        read = _cell(cell, dialect, self.noun)
        if read is None:
            return None
        record.members[column.name] = number
        record.fields[column.target] = number
        if isinstance(read, _Bad):
            self.foreign += read.foreign
            return read
        name = column.name
        self.marked += read.marked
        if read.word is not None:
            held.setdefault("unquantified", {})[name] = read.word
        if read.value is not None:
            held[name] = read.value
        if read.uncertainty is not None:
            held.setdefault("uncertainty", {})[name] = read.uncertainty
        if read.low is not None or read.high is not None:
            held.setdefault("ranges", {})[name] = [read.low, read.high]
        listed = [f"bounded_{read.bound}"] if read.bound else []
        if read.approximate:
            listed.append("approximate")
        for hedge in listed:
            record.lists[hedge] = held.setdefault(hedge, [])
            record.lists[hedge].append(name)
        return None


def read_sheet(
    path: Path, header_path: str | os.PathLike[str] | None, row_type: type[CatalogueRow]
) -> Catalogue[Any]:
    """The catalogue a CSV file and its JSON header hold, or one refusal of it.

    :raises CatalogueError: for a file past 16 MiB or a header past 64 KiB,
        text that is not UTF-8, a header that is not JSON or is a calibration
        sidecar, and every problem the two hold.
    :raises FileNotFoundError: for a header that is not there.
    """
    label = path.name
    header = (
        Path(header_path)
        if header_path is not None
        else path.with_name(path.name + CSV_HEADER_TAIL)
    )
    header_label = header.name
    size = path.stat().st_size
    if size > _MAX_BYTES:
        raise _size_refusal(label, size)
    try:
        header_size = header.stat().st_size
    except FileNotFoundError as error:
        msg = (
            f"{label} is read with its JSON header, {header_label}, beside it, "
            "and there is none; write the header there, or name it with "
            "header_path="
        )
        raise FileNotFoundError(errno.ENOENT, msg, str(header)) from error
    if header_size > _MAX_HEADER:
        message = (
            f"is {header_size} bytes, and the header of a catalogue CSV is at "
            f"most {_MAX_HEADER} bytes (64 KiB)"
        )
        raise _refusal(header_label, "", message)
    head = header.read_bytes()
    raw = path.read_bytes()
    document = _decode(_text_of(head, header_label, "UTF-8"), header_label)
    if isinstance(document, Mapping) and document.get("schema") == SIDECAR_SCHEMA:
        message = (
            "is the calibration sidecar of an audio file, not the header of a "
            f"catalogue CSV, whose schema is {CATALOGUE_SCHEMA!r}"
        )
        raise _refusal(header_label, "/schema", message)
    text = _text_of(raw, label, "CSV UTF-8")
    sheet = _Sheet(label, header_label, _noun(document))
    reader = _Reader(row_type, sheet.issues, sheet=True)
    header_read = reader.document(sheet.document(document, text, reader))
    return _finish(
        reader,
        header_read,
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(head).hexdigest(),
    )


def _noun(document: object) -> str:
    """The subject a refusal names the header's document by."""
    provenance = document.get("provenance") if isinstance(document, Mapping) else None
    kind = provenance.get("kind") if isinstance(provenance, Mapping) else None
    return _NOUNS.get(kind, "the document") if isinstance(kind, str) else "the document"


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------
@dataclass
class _Pieces:
    """Everything a row writes about one numeric cell, before it is one cell."""

    value: object = None
    #: The listed hedges that name the cell, each with its index in the list.
    listed: dict[str, int] = field(default_factory=dict)
    ends: list[object] | None = None
    spread: object = None
    word: str | None = None


def _number_text(value: object, decimal: str) -> str:
    """A number as a cell writes it, with the decimal mark *decimal*."""
    text = str(_scalar(value))
    return text.replace(".", decimal) if decimal != "." else text


def _numeric_cell(
    name: str, pieces: _Pieces, decimal: str
) -> str | tuple[tuple[object, ...], str]:
    """The cell of one numeric field, or the pointer and the reason it has none."""
    approximate = "~" if "approximate" in pieces.listed else ""
    bound = next(
        (
            hedge.removeprefix("bounded_")
            for hedge in pieces.listed
            if hedge.startswith("bounded_")
        ),
        "",
    )
    if pieces.word is not None:
        if pieces.value is not None or pieces.ends is not None or pieces.listed:
            return ("unquantified", name), (
                "a word beside a value, a range or a mark on the cell is "
                "written only in a JSON catalogue"
            )
        return f"[{pieces.word}]"
    if pieces.ends is not None:
        if pieces.value is not None:
            return ("ranges", name), (
                "a value beside a range is written only in a JSON catalogue: a "
                "CSV cell holds one or the other"
            )
        if pieces.spread is not None:
            return ("uncertainty", name), (
                "a plus-or-minus on a range or a bound is written only in a "
                "JSON catalogue"
            )
        low, high = pieces.ends
        if bound:
            if approximate:
                return ("approximate", pieces.listed["approximate"]), (
                    "an approximate bound is written only in a JSON catalogue"
                )
            end, other = (high, low) if bound == "above" else (low, high)
            if other is not None:
                return ("ranges", name), (
                    "a bound with its other end printed too is written only in "
                    "a JSON catalogue: a CSV cell writes <=30 or >=5 alone"
                )
            sign = "<=" if bound == "above" else ">="
            return f"{sign}{_number_text(end, decimal)}"
        if low is None or high is None:
            return ("ranges", name), (
                "a range with an open end and no bound is written only in a JSON "
                "catalogue"
            )
        return (
            f"{approximate}{_number_text(low, decimal)}..{_number_text(high, decimal)}"
        )
    if pieces.value is None:
        return (next(iter(pieces.listed), "uncertainty"), name), (
            "a mark on a cell with no value is written only in a JSON catalogue"
        )
    text = f"{approximate}{_number_text(pieces.value, decimal)}"
    if pieces.spread is not None:
        text += f"\u00b1{_number_text(pieces.spread, decimal)}"
    return text


class _SheetRow:
    """One row of a document as the cells of a CSV line."""

    def __init__(
        self, index: int, held: Mapping[str, Any], names: _Names, label: str
    ) -> None:
        self.index = index
        self.key = str(held["key"])
        self.label = label
        self.names = names
        self.cells: dict[str, str] = {}
        self.pieces: dict[str, _Pieces] = {}
        self.trouble: list[CatalogueIssue] = []
        defaults = {
            item.name: item.default
            for item in dataclasses.fields(names.row_type)
            if isinstance(item.default, str)
        }
        for member, value in held.items():
            self.member(member, value, defaults)

    def refuse(
        self, parts: tuple[object, ...], message: str, field_name: str = ""
    ) -> None:
        self.trouble.append(
            CatalogueIssue(
                file=self.label,
                location=_pointer("rows", self.index, *parts),
                row_key=self.key,
                field=field_name,
                message=message,
            )
        )

    def pieces_of(self, name: str) -> _Pieces:
        return self.pieces.setdefault(name, _Pieces())

    def member(self, member: str, value: object, defaults: Mapping[str, str]) -> None:
        """One member of a JSON row, into its cell or refused."""
        names = self.names
        kind = names.kinds.get(member, "")
        if member == "key":
            self.cells["key"] = self.key
        elif member.startswith("x-") or kind == "text":
            if value == "" and defaults.get(member):
                self.refuse(
                    (member,),
                    f"{member} is empty where its default is {defaults[member]!r}, "
                    "and an empty CSV cell reads as the default; an empty text "
                    "is written only in a JSON catalogue",
                    member,
                )
            else:
                self.cells[member] = _escape(str(value))
        elif kind == "flag":
            self.cells[member] = "true" if value else "false"
        elif kind in ("number", "whole") or member in names.spellings.aliases:
            self.pieces_of(member).value = value
        elif member in _LISTED and isinstance(value, (list, tuple)):
            for position, name in enumerate(value):
                self.pieces_of(name).listed[member] = position
        elif isinstance(value, Mapping):
            self.mapping(member, value)
        else:
            self.refuse(
                (member,),
                f"{member} holds a set or a mapping, which only a JSON catalogue writes",
                member,
            )

    def mapping(self, member: str, value: Mapping[str, Any]) -> None:
        """A member of a JSON row that maps fields to what it says of them."""
        if member == "ranges":
            for name, ends in value.items():
                self.pieces_of(name).ends = list(ends)
        elif member == "uncertainty":
            for name, spread in value.items():
                self.pieces_of(name).spread = spread
        elif member == "unquantified":
            for name, word in value.items():
                self.pieces_of(name).word = word
        elif member == "basis":
            self.basis(value)
        elif member == "provenance":
            for entry, text in value.items():
                if entry == "field_test_standards":
                    self.refuse(("provenance", entry), _in_json(entry))
                else:
                    self.cells[f"provenance.{entry}"] = _escape(str(text))
        elif member in _IN_JSON:
            for entry in value:
                self.refuse((member, entry), _in_json(member), str(entry))
        else:
            self.refuse(
                (member,),
                f"{member} holds a set or a mapping, which only a JSON catalogue writes",
                member,
            )

    def basis(self, value: Mapping[str, str]) -> None:
        for entry, word in value.items():
            if entry == "row":
                self.cells["basis"] = word
            else:
                self.refuse(
                    ("basis", entry), _in_json("basis", "a basis for one cell"), entry
                )

    def finish(self, decimal: str) -> None:
        """Every numeric cell written, or refused with its pointer."""
        for name, pieces in self.pieces.items():
            cell = _numeric_cell(name, pieces, decimal)
            if isinstance(cell, str):
                self.cells[name] = cell
            else:
                parts, message = cell
                self.refuse(parts, message, name)


def _column_order(names: _Names, rows: list[_SheetRow]) -> list[str]:
    """The columns of every row, in the order a person reads a row class."""
    fields = [item.name for item in dataclasses.fields(names.row_type)]
    order = {name: index for index, name in enumerate(fields)}
    seen: dict[str, int] = {}
    for row in rows:
        for column in row.cells:
            seen.setdefault(column, len(seen))
    provenance = list(_PROVENANCE_COLUMNS)

    def rank(column: str) -> tuple[int, int, int, int]:
        if column == "key":
            return (0, 0, 0, 0)
        if column == "basis":
            return (2, 0, 0, 0)
        if column in order:
            return (1, order[column], 0, 0)
        if column in names.spellings.aliases:
            return (1, order[names.spellings.aliases[column][0]], 1, seen[column])
        if column in _PROVENANCE_COLUMNS:
            return (3, provenance.index(column), 0, 0)
        return (4, seen[column], 0, 0)

    return sorted(seen, key=rank)


def sheet_texts(
    document: Mapping[str, Any], names: _Names, dialect: _Dialect, label: str
) -> tuple[str, dict[str, Any]]:
    """A document as a CSV file's text and its header.

    :return: The CSV text, with a byte order mark and a line break after
        every line, and the header document.
    :raises CatalogueError: for every cell a CSV file cannot hold, each at
        the pointer the JSON document writes it at, all at once.
    """
    rows = [
        _SheetRow(index, held, names, label)
        for index, held in enumerate(document["rows"])
    ]
    for row in rows:
        row.finish(dialect.decimal)
    trouble = [issue for row in rows for issue in row.trouble]
    if trouble:
        count = len(trouble)
        plural = "s" if count != 1 else ""
        lines = [
            f"{label}: {count} thing{plural} a CSV file cannot hold, and nothing "
            "was written; write the catalogue as JSON, or leave those rows out",
            *(str(issue) for issue in trouble[:_SHOWN]),
        ]
        if count > _SHOWN:
            lines.append(f"... and {count - _SHOWN} more, in the error's issues")
        raise CatalogueError("\n".join(lines), issues=tuple(trouble))
    columns = _column_order(names, rows)
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=dialect.delimiter, lineterminator="\r\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row.cells.get(column, "") for column in columns])
    declared = {"delimiter": dialect.delimiter, "decimal": dialect.decimal}
    header: dict[str, Any] = {}
    for key, value in document.items():
        if key == "rows":
            continue
        if key == "phonometry_version":
            header["csv"] = declared
        header[key] = value
    header.setdefault("csv", declared)
    return "\ufeff" + buffer.getvalue(), header
