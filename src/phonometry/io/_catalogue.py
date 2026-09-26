#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Catalogue files: a caller's own table of materials, read and written.

The library publishes the tables of its books and standards and nothing a
manufacturer prints: a data sheet is revised without notice, its terms of use
rarely allow copying it, and the value a project needs is the one on the
sheet the project was specified against. So a caller keeps their own, in a
file, and this module reads it into rows of the same classes every
``PUBLISHED_*`` catalogue hands out, built through
:meth:`CatalogueRow.from_printed` like the packaged ones, and writes one back.
Nothing a file holds is kept anywhere but in the objects handed back.

**The document, schema version 1.** One JSON object, UTF-8, with a closed
set of top-level keys:

======================  ======================================================
Key                     Meaning
======================  ======================================================
``schema``              ``"phonometry-catalogue"``; anything else is refused.
``schema_version``      An integer; this layout is ``1``. A newer one is
                        refused with "upgrade phonometry", as the calibration
                        sidecar does.
``catalogue``           The catalogue's name, the first half of every key:
                        up to 64 of ``a-z``, ``0-9``, ``.``, ``_`` and ``-``,
                        and never a name with a four-digit year followed by a
                        word (``acme-2026-rev4``), which is the form of the
                        packaged tables' names.
``row_type``            The name of the row class, compared with the class the
                        caller passes and never imported.
``about``               What the document is, how it was read and in which
                        units it prints.
``provenance``          A :class:`Provenance`: ``kind``, ``document``,
                        ``version`` (text or ``null``) and ``consulted`` are
                        required.
``basis``               Optional: the basis of every row that does not give
                        its own, one of :data:`CATALOGUE_BASES`.
``conventions``         Optional: the notes and legends the document prints
                        for the whole table, as a list of texts.
``rows``                A list of rows, at least one.
``phonometry_version``  Optional: the version that wrote the file. Never
                        read.
======================  ======================================================

A row is an object with a ``key`` of its own, a ``name``, and its cells named
as the fields of the row class, or in another unit of the same kind
(``thickness_m`` for ``thickness_mm``), which is converted on its digits and
recorded in :attr:`CatalogueRow.converted`. The hedges are written as the
packaged tables write them. A row may narrow the provenance to its own page,
table, laboratory, report, test date and standards, and may carry columns of
its own named ``x-...``, which :attr:`Catalogue.extras` keeps as text. A row
never writes ``derived``, ``table``, ``source`` or ``estimated``: the first
three are the library's to write, and an estimate is a ``basis``.

The problems in a document are raised together in one
:class:`CatalogueError`, each with its place in the file as a JSON pointer:
every problem of form the pass over the document finds (a text where a
number goes, a field the row class does not have, a unit no family holds),
and, for each row the pass finds nothing wrong with, the first rule of the
row contract it breaks. A cell worth a second look is kept and noted
in :attr:`Catalogue.notes` instead, and one :class:`CatalogueWarning` says
how many there are.

The file never runs anything: only :mod:`json` reads it, the row class is the
caller's argument and the class name the file writes is only compared with
it. A file is at most 16 MiB and 50 000 rows, nested at most six levels,
and its text holds no control character but the tab and the line feed and no
mark that reorders what a reader sees.
"""

from __future__ import annotations

import dataclasses
import datetime
import difflib
import hashlib
import json
import math
import numbers
import os
import re
import secrets
import unicodedata
import warnings
from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, NoReturn

from .._internal.catalogue import (
    CATALOGUE_BASES,
    CatalogueError,
    CatalogueIssue,
    CatalogueRow,
    PrintedNumber,
    Provenance,
    _Constant,
    _Repeated,
    convert_figure,
    decode_marked,
    field_kinds,
    is_unit_spelling,
    read_packaged,
    spellings,
    unit_stem,
)
from .._internal.warnings import PhonometryWarning

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from .._internal.catalogue import UnitAlias

#: The schema identifier and the layout version this module reads and writes.
CATALOGUE_SCHEMA = "phonometry-catalogue"
CATALOGUE_SCHEMA_VERSION = 1

#: The largest file read, checked on disk before a byte is read.
_MAX_BYTES = 16 * 1024 * 1024
#: The most rows one document holds.
_MAX_ROWS = 50_000
#: How deep the containers of a document nest: the document, its rows, a
#: row, a hedge, an entry, an interval inside a list of readings.
_MAX_DEPTH = 6
#: The longest ``about`` or ``note``.
_MAX_PROSE = 20_000
#: The longest of every other text, a convention among them.
_MAX_TEXT = 2_000
#: How many issues a refusal lists before it counts the rest.
_SHOWN = 20
#: How many notes the warning quotes.
_NOTES_SHOWN = 5
#: How many names a message quotes before it counts the rest.
_NAMES_SHOWN = 3
#: The longest a word a page prints in place of a number is expected to be;
#: a longer one reads as a sentence.
_WORD = 32
#: How much of a value a message quotes.
_QUOTED = 80
#: The ends of an interval, and the parts of a converted record.
_PAIR = 2
#: The longest list of scalars the writer keeps on one line.
_INLINE = 72

#: A catalogue's name, which is the first half of every key it holds.
_NAME = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")
#: The names the packaged tables use: a four-digit year and a word after it.
#: Reserved wide, so that no packaged table added later can take a name a
#: caller's file already uses, and checked without reading any packaged table.
_RESERVED = re.compile(r"[a-z0-9][a-z0-9._-]*-[0-9]{4}-[a-z]")
#: A row's key: no ``/``, which separates the catalogue from the row, and no
#: space. A leading underscore is allowed, as a packaged key has one.
_KEY = re.compile(r"[A-Za-z0-9_][A-Za-z0-9._+-]{0,127}")
#: A column of the caller's own.
_EXTRA = re.compile(r"x-[A-Za-z0-9_][A-Za-z0-9._+-]{0,125}")
#: A number as JSON writes one.
_JSON_NUMBER = re.compile(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?")
#: What no text of a catalogue may hold: the control characters but the tab
#: and the line feed, and the marks that reorder what a reader sees (a
#: "Trojan source" text shows one thing and holds another).
_UNSAFE = re.compile(r"[\x00-\x08\x0b-\x1f\u202a-\u202e\u2066-\u2069]")

_TOP_REQUIRED = (
    "schema",
    "schema_version",
    "catalogue",
    "row_type",
    "about",
    "provenance",
    "rows",
)
_TOP_KEYS = frozenset({*_TOP_REQUIRED, "basis", "conventions", "phonometry_version"})
_PROVENANCE_FIELDS = tuple(item.name for item in dataclasses.fields(Provenance))
_PROVENANCE_REQUIRED = ("kind", "document", "version", "consulted")
#: What a row may narrow of its document's provenance: where on the document
#: its cells are and who tested them, never which document it is.
_ROW_PROVENANCE = (
    "page",
    "printed_table",
    "laboratory",
    "accreditation",
    "report",
    "test_date",
    "test_standard",
    "field_test_standards",
)
#: What a row never writes, and why.
_FORBIDDEN: Mapping[str, str] = MappingProxyType(
    {
        "derived": (
            "derived is what the library works out from the printed cells when "
            "it reads them; write the cells the page prints"
        ),
        "table": "the catalogue's name is the table of every row it holds",
        "source": (
            "the source of every row is composed from the provenance; a row "
            "narrows it in its own provenance"
        ),
        "estimated": 'an estimate is a basis: write "basis": {"<field>": "estimated"}',
    }
)
#: The texts that may run to paragraphs.
_PROSE = frozenset({"about", "note"})
#: The hedges whose entries are texts.
_TEXT_HEDGES = frozenset(
    {
        "unquantified",
        "not_derivable",
        "misprinted",
        "carried",
        "attributed_to",
        "borrowed",
    }
)
#: The words a hedge may use in place of a field.
_HEDGE_WORDS: Mapping[str, frozenset[str]] = MappingProxyType(
    {"basis": frozenset({"row"}), "attributed_to": frozenset({"row", "table"})}
)


class CatalogueWarning(PhonometryWarning):
    """A catalogue file was read, and some of its cells are worth a second look.

    Emitted once per document by :func:`read_catalogue` and
    :func:`parse_catalogue` when :attr:`Catalogue.notes` is not empty, with
    the count and the first notes. A note never changes a row: a value
    measured with no report or laboratory named for it, or a word in place of
    a number long enough to be a sentence, is kept as the file writes it.
    """


def _quote(value: object) -> str:
    text = repr(value)
    return text if len(text) <= _QUOTED else f"{text[: _QUOTED - 3]}..."


def _listed(names: Sequence[str]) -> str:
    """The first names of a list, quoted, and how many more there are."""
    quoted = ", ".join(repr(name) for name in names[:_NAMES_SHOWN])
    more = len(names) - _NAMES_SHOWN
    return f"{quoted} and {more} more" if more > 0 else quoted


# ---------------------------------------------------------------------------
# The catalogue
# ---------------------------------------------------------------------------
class _Joined(Mapping[str, CatalogueRow]):
    """Two catalogues read as one, which never lets one row replace another.

    What ``|`` gives between a :class:`Catalogue` and any other mapping of
    rows. It is read-only and joins again with ``|`` under the same rule, so
    ``(PUBLISHED_POROUS | mine) | theirs`` refuses a shared key at every
    step, where a plain ``dict`` would keep the last row under it and say
    nothing.
    """

    __slots__ = ("_rows",)

    def __init__(
        self, left: Mapping[str, CatalogueRow], right: Mapping[str, CatalogueRow]
    ) -> None:
        shared = [key for key in right if key in left]
        if shared:
            verb = "is" if len(shared) == 1 else "are"
            msg = (
                f"{_listed(shared)} {verb} in both catalogues, and joining "
                "catalogues with | never lets one row replace another; leave "
                "the row out of one of them first"
            )
            raise CatalogueError(msg)
        self._rows: Mapping[str, CatalogueRow] = MappingProxyType({**left, **right})

    def __getitem__(self, key: str) -> CatalogueRow:
        """The row under *key*, from whichever side holds it."""
        return self._rows[key]

    def __iter__(self) -> Iterator[str]:
        """The keys, the left side's first."""
        return iter(self._rows)

    def __len__(self) -> int:
        """How many rows the two sides hold together."""
        return len(self._rows)

    def __or__(self, other: object) -> Mapping[str, CatalogueRow]:
        """This and *other* as one, refusing a key both hold."""
        if not isinstance(other, Mapping):
            return NotImplemented
        return _Joined(self, other)

    def __ror__(self, other: object) -> Mapping[str, CatalogueRow]:
        """*other* and this as one, refusing a key both hold."""
        if not isinstance(other, Mapping):
            return NotImplemented
        return _Joined(other, self)

    def __repr__(self) -> str:
        """How many rows, not the rows themselves."""
        return f"<{len(self._rows)} catalogue rows joined with |>"


@dataclass(frozen=True, kw_only=True, eq=False, repr=False)
class Catalogue[R: CatalogueRow](Mapping[str, R]):
    """A caller's catalogue: rows of one class, keyed as the packaged ones are.

    What :func:`read_catalogue` and :func:`parse_catalogue` return. It is a
    read-only mapping from ``"<name>/<key>"`` to a row, so it goes wherever a
    ``PUBLISHED_*`` catalogue goes, and a row's :attr:`CatalogueRow.table` is
    the catalogue's name. ``PUBLISHED_POROUS | mine`` reads both as one and
    refuses a key both hold rather than letting one row replace the other;
    a caller's catalogue can never take a name of the packaged form, so the
    keys of the two never meet.

    Two catalogues are equal when they hold the same rows under the same
    keys, as any two mappings are.

    :ivar name: The catalogue's name, the first half of every key.
    :ivar row_type: The class every row is.
    :ivar about: What the document is and how it was read.
    :ivar provenance: The document the rows were read from. A row that
        narrows it holds its own in :attr:`CatalogueRow.provenance`.
    :ivar rows: The rows, by key, read-only, in the order of the document.
    :ivar extras: The caller's own ``x-...`` columns, by row key and column,
        as text: a number keeps the digits it was written with.
    :ivar conventions: The notes and legends the document prints for the
        whole table.
    :ivar notes: What is worth a second look, each a
        :class:`CatalogueIssue` of severity ``"note"``.
    :ivar schema_version: The version of the layout the document was written
        in.
    :ivar file_sha256: The SHA-256 of the bytes read, in hexadecimal, so
        that a report can cite exactly which file its values came from;
        empty for a document handed over as a mapping, which has no bytes.
    """

    name: str
    row_type: type[R]
    about: str
    provenance: Provenance
    rows: Mapping[str, R]
    extras: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    conventions: tuple[str, ...] = ()
    notes: tuple[CatalogueIssue, ...] = ()
    schema_version: int = CATALOGUE_SCHEMA_VERSION
    file_sha256: str = ""

    def __post_init__(self) -> None:
        """Freeze what the catalogue holds, and hold its rows to one class.

        :raises TypeError: for a row that is not a *row_type*.
        """
        for key, row in self.rows.items():
            if not isinstance(row, self.row_type):
                msg = (
                    f"the catalogue holds a {type(row).__name__} under {key!r}, "
                    f"and its rows are {self.row_type.__name__}"
                )
                raise TypeError(msg)
        extras = {
            key: MappingProxyType(dict(cells)) for key, cells in self.extras.items()
        }
        object.__setattr__(self, "rows", MappingProxyType(dict(self.rows)))
        object.__setattr__(self, "extras", MappingProxyType(extras))
        object.__setattr__(self, "conventions", tuple(self.conventions))
        object.__setattr__(self, "notes", tuple(self.notes))

    def __getitem__(self, key: str) -> R:
        """The row under ``"<name>/<key>"``."""
        return self.rows[key]

    def __iter__(self) -> Iterator[str]:
        """The keys, in the order of the document."""
        return iter(self.rows)

    def __len__(self) -> int:
        """How many rows the catalogue holds."""
        return len(self.rows)

    def __or__(self, other: object) -> Mapping[str, CatalogueRow]:
        """This and *other* as one read-only mapping, refusing a shared key."""
        if not isinstance(other, Mapping):
            return NotImplemented
        return _Joined(self, other)

    def __ror__(self, other: object) -> Mapping[str, CatalogueRow]:
        """*other* and this as one read-only mapping, refusing a shared key.

        What ``PUBLISHED_POROUS | mine`` reaches, since a published mapping
        does not know how to join a catalogue.
        """
        if not isinstance(other, Mapping):
            return NotImplemented
        return _Joined(other, self)

    def __repr__(self) -> str:
        """The name, the row class and the counts, not the rows themselves."""
        return (
            f"Catalogue(name={self.name!r}, row_type={self.row_type.__name__}, "
            f"rows={len(self.rows)}, notes={len(self.notes)})"
        )


# ---------------------------------------------------------------------------
# Reading: numbers and names
# ---------------------------------------------------------------------------
def _pointer(*parts: object) -> str:
    """A JSON pointer (RFC 6901) to the member *parts* name."""
    return "".join(
        "/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )


def _is_number(value: object) -> bool:
    """Whether *value* is a finite number a document may hold, never a ``bool``."""
    if isinstance(value, bool):
        return False
    if isinstance(value, PrintedNumber):
        return math.isfinite(float(value.text))
    if isinstance(value, numbers.Real):
        return math.isfinite(float(value))
    return False


def _plain(value: object) -> object:
    """A number as the row holds it: an ``int`` or a ``float``.

    A number decoded from text is an ``int`` when the text writes one and a
    ``float`` otherwise, which is what the reader of a packaged table gives
    for the same text; anything else is left as it is.
    """
    if isinstance(value, PrintedNumber):
        text = value.text
        return float(text) if any(mark in text for mark in ".eE") else int(text)
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        return value
    if isinstance(value, numbers.Integral):
        return int(value)
    return float(value)


def _what_it_is(value: object) -> str:
    """How a refusal names a value that is not the number a cell wants."""
    if isinstance(value, str):
        hint = (
            "; JSON numbers use a decimal point"
            if re.fullmatch(r"\s*[-+]?[0-9]+,[0-9]+\s*", value)
            else ""
        )
        return f"the text {_quote(value)}{hint}"
    if isinstance(value, bool):
        return f"{str(value).lower()}, which is a flag"
    if isinstance(value, Mapping):
        return "an object"
    if isinstance(value, (list, tuple)):
        return "a list"
    if value is None:
        return "null"
    if isinstance(value, (_Constant, PrintedNumber, numbers.Real)):
        written = value.token if isinstance(value, _Constant) else _number_text(value)
        if isinstance(value, _Constant) or not _is_number(value):
            return f"{written}, which is not a finite number"
        return f"the number {written}"
    return _quote(value)


def _number_text(value: object) -> str:
    """A number as the document writes it."""
    return value.text if isinstance(value, PrintedNumber) else repr(_plain(value))


def _reserved_message(name: str) -> str:
    """The refusal of a reserved name, with a free one in its place."""
    parts = name.split("-")
    year = next(
        (
            index
            for index, part in enumerate(parts[:-1])
            if re.fullmatch(r"[0-9]{4}", part) and parts[index + 1][:1].isalpha()
        ),
        None,
    )
    suggestion = ""
    if year is not None:
        moved = "-".join([*parts[:year], *parts[year + 1 :], parts[year]])
        suggestion = f"; move the year to the end, as {moved!r}"
    return (
        f"{name!r} has the form of a packaged table's name, a four-digit year "
        "followed by a word, which is reserved so that no table the library "
        f"adds can ever share a key with your catalogue{suggestion}"
    )


def _name_problem(name: object) -> str:
    """Why *name* cannot name a catalogue, or ``""``."""
    if not isinstance(name, str) or not _NAME.fullmatch(name):
        return (
            f"{_quote(name)} is not a catalogue name: up to 64 lower-case "
            "letters, digits, dots, hyphens and underscores, starting with a "
            "letter or a digit"
        )
    if _RESERVED.match(name):
        return _reserved_message(name)
    return ""


# ---------------------------------------------------------------------------
# Reading: the pass over a document
# ---------------------------------------------------------------------------
#: The entry of a hedge that failed its check, and was reported.
_INVALID = object()


class _Row:
    """One row as the document pass left it, ready to be built."""

    __slots__ = ("cells", "extras", "index", "key", "narrowed", "where")

    def __init__(self, index: int, key: str) -> None:
        self.index = index
        self.key = key
        self.cells: dict[str, Any] = {}
        self.extras: dict[str, str] = {}
        self.narrowed: dict[str, Any] = {}
        #: Field to where the document writes it, for a refusal of the contract.
        self.where: dict[str, str] = {}


@dataclass
class _Header:
    """The document's own keys, as the pass read them."""

    name: str = ""
    about: str = ""
    basis: str = ""
    conventions: tuple[str, ...] = ()
    provenance: Provenance | None = None
    rows: list[_Row] = field(default_factory=list)


class _Issues:
    """Every issue found in one document, with the file it is in."""

    def __init__(self, label: str) -> None:
        self.label = label
        self.found: list[CatalogueIssue] = []

    def error(
        self, location: str, message: str, *, row_key: str = "", field_name: str = ""
    ) -> None:
        self.found.append(
            CatalogueIssue(
                file=self.label,
                location=location,
                row_key=row_key,
                field=field_name,
                message=message,
            )
        )

    def refuse(self) -> NoReturn:
        """One error for the whole document, with every issue in it."""
        count = len(self.found)
        lines = [str(issue) for issue in self.found[:_SHOWN]]
        if count > _SHOWN:
            lines.append(f"... and {count - _SHOWN} more, in the error's issues")
        plural = "s" if count != 1 else ""
        head = f"{self.label}: {count} problem{plural}, and no row was read"
        msg = "\n".join([head, *lines])
        raise CatalogueError(msg, issues=tuple(self.found))


class _Names:
    """What a row class calls its cells, and how a wrong name is answered."""

    def __init__(self, row_type: type[CatalogueRow]) -> None:
        self.row_type = row_type
        self.kinds = field_kinds(row_type)
        self.spellings = spellings(row_type)
        self.numeric = frozenset(
            name for name, kind in self.kinds.items() if kind in ("number", "whole")
        )
        texts = frozenset(name for name, kind in self.kinds.items() if kind == "text")
        self.cells = (self.numeric | texts) - {"source", "table"}
        self.hedges = frozenset((*row_type._number_hedges, *row_type._value_hedges))

    def resolve(
        self, written: str, allowed: frozenset[str], words: frozenset[str]
    ) -> tuple[str | None, str]:
        """The field *written* names among *allowed*, or why it names none."""
        if written in allowed or written in words:
            return written, ""
        found = self.spellings.aliases.get(written)
        if found is not None and found[0] in allowed:
            return found[0], ""
        choices = self.spellings.ambiguous.get(written)
        if choices is not None:
            return None, (
                f"{written!r} could be {' or '.join(map(repr, choices))}, which "
                "share a root and a kind of unit; write the field's own name"
            )
        return None, self.no_such_field(written, allowed)

    def no_such_field(self, written: str, allowed: frozenset[str]) -> str:
        """Why *written* is not a field, with the name most like it."""
        unit = self.unit_hint(written, allowed)
        if unit:
            return unit
        cls = self.row_type.__name__
        if written in self.kinds:
            return f"{written!r} is a field of {cls} that cannot be named here"
        close = _closest(written, self.names_for(allowed))
        head = f"no field {written!r} on {cls}"
        return f"{head}; did you mean {close!r}?" if close else head

    def names_for(self, fields: frozenset[str]) -> frozenset[str]:
        """*fields*, and every other name they are taken under."""
        return fields | {
            name
            for name, (target, _) in self.spellings.aliases.items()
            if target in fields
        }

    def unit_hint(self, written: str, allowed: frozenset[str]) -> str:
        """A refusal naming every unit a field is taken in, for a wrong unit.

        Only when the difference is the unit alone: the written name is a
        field's root followed by words a unit is spelled with, and no other
        field is a close match. ``fibre_diameter_distribution_paramter`` is a
        misspelt field, not a fibre diameter in a unit called
        ``distribution_paramter``.
        """
        root, target = "", ""
        for name in allowed & self.numeric:
            stem = unit_stem(name)
            if stem and written.startswith(f"{stem}_") and len(stem) > len(root):
                root, target = stem, name
        written_unit = written.removeprefix(f"{root}_")
        if not root or not is_unit_spelling(written_unit):
            return ""
        others = self.names_for(allowed) - self.names_for(frozenset({target}))
        if _closest(written, others):
            return ""
        own = self.spellings.units.get(target, "")
        options = [f"{target} ({own})" if own else target]
        options += sorted(
            f"{other} ({alias.unit})"
            for other, (field_name, alias) in self.spellings.aliases.items()
            if field_name == target
        )
        choices = (
            f"{', '.join(options[:-1])} or {options[-1]}"
            if len(options) > 1
            else options[0]
        )
        return f"{written_unit!r} is not a unit this reader converts; write {choices}"


def _closest(written: str, names: frozenset[str]) -> str:
    """The name most like *written*, if one is close enough to be meant."""
    close = difflib.get_close_matches(written, sorted(names), n=1, cutoff=0.8)
    return close[0] if close else ""


class _Reader:
    """The pass over one document that finds every problem of form.

    It checks the document's own keys, the name, the provenance, and every
    row: its key, every cell against the field it fills, every hedge against
    the fields it names, the unit a figure is written in. Each problem is
    kept with the pointer to it, and only the rows it finds nothing wrong
    with go on to be built, for the row contract to check.
    """

    def __init__(self, row_type: type[CatalogueRow], issues: _Issues) -> None:
        self.row_type = row_type
        self.issues = issues
        self.names = _Names(row_type)
        self.required = tuple(
            item.name
            for item in dataclasses.fields(row_type)
            if item.default is dataclasses.MISSING
            and item.default_factory is dataclasses.MISSING
            and item.name != "source"
        )

    def error(
        self, location: str, message: str, *, row_key: str = "", field_name: str = ""
    ) -> None:
        self.issues.error(location, message, row_key=row_key, field_name=field_name)

    # -- the whole text ------------------------------------------------------
    def hygiene(self, node: object, where: str, depth: int) -> None:
        """What JSON does not hold, text no reader should see, and depth."""
        if isinstance(node, (Mapping, list, tuple)) and depth > _MAX_DEPTH:
            self.error(
                where or "/",
                f"is nested {depth} levels deep, and a catalogue nests at most "
                f"{_MAX_DEPTH}",
            )
            return
        if isinstance(node, _Constant):
            self.error(
                where, f"{node.token} is not JSON and not a number any page prints"
            )
        elif isinstance(node, Mapping):
            if isinstance(node, _Repeated):
                named = ", ".join(repr(name) for name in node.repeated)
                self.error(
                    where or "/", f"names {named} twice, and JSON keeps only the last"
                )
            for key, value in node.items():
                at = f"{where}{_pointer(key)}"
                if not isinstance(key, str):
                    self.error(
                        where or "/", f"has the key {_quote(key)}, which is not text"
                    )
                    continue
                self.unsafe(key, at)
                self.hygiene(value, at, depth + 1)
        elif isinstance(node, (list, tuple)):
            for index, value in enumerate(node):
                self.hygiene(value, f"{where}{_pointer(index)}", depth + 1)
        elif isinstance(node, str):
            self.unsafe(node, where)

    def unsafe(self, text: str, where: str) -> None:
        found = _UNSAFE.search(text)
        if found is not None:
            self.error(
                where,
                f"holds the character U+{ord(found.group()):04X} in "
                f"{_quote(text)}; a catalogue's text holds no control character "
                "but the tab and the line feed, and no mark that reorders it",
            )

    def text(
        self, value: object, where: str, *, prose: bool = False, row_key: str = ""
    ) -> str | None:
        """A text, normalised to NFC and held to its length."""
        if not isinstance(value, str):
            self.error(
                where, f"expected text, got {_what_it_is(value)}", row_key=row_key
            )
            return None
        limit = _MAX_PROSE if prose else _MAX_TEXT
        if len(value) > limit:
            self.error(
                where,
                f"holds {len(value)} characters, and a text here holds at most {limit}",
                row_key=row_key,
            )
            return None
        return unicodedata.normalize("NFC", value)

    # -- the document --------------------------------------------------------
    def document(self, document: object) -> _Header | None:
        """The document's own keys, checked; ``None`` when reading stops here."""
        if not isinstance(document, Mapping):
            self.error("", "a catalogue document is one JSON object")
            return None
        self.hygiene(document, "", 1)
        for key in document:
            if isinstance(key, str) and key not in _TOP_KEYS:
                self.unknown_key(_pointer(key), key, _TOP_KEYS, "a catalogue document")
        for key in _TOP_REQUIRED:
            if key not in document:
                self.error("", f"a catalogue document needs a top-level {key!r}")
        if not self.schema(document):
            return None
        header = _Header()
        self.header(document, header)
        return header

    def schema(self, document: Mapping[str, Any]) -> bool:
        """Whether the document is one this version reads."""
        if "schema" in document and document["schema"] != CATALOGUE_SCHEMA:
            self.error(
                "/schema",
                f"is {_quote(document['schema'])}, not {CATALOGUE_SCHEMA!r}; "
                "refusing to guess at what the document means",
            )
            return False
        if "schema_version" not in document:
            return False
        version = document["schema_version"]
        whole = _plain(version) if _is_number(version) else None
        if not isinstance(whole, int):
            self.error("/schema_version", f"is {_quote(version)}, not a whole number")
            return False
        if whole > CATALOGUE_SCHEMA_VERSION:
            self.error(
                "/schema_version",
                f"{whole} is newer than the version {CATALOGUE_SCHEMA_VERSION} "
                "this phonometry reads; upgrade phonometry",
            )
            return False
        if whole < 1:
            self.error("/schema_version", f"is {whole}, and the first version is 1")
            return False
        return True

    def header(self, document: Mapping[str, Any], header: _Header) -> None:
        if "catalogue" in document:
            problem = _name_problem(document["catalogue"])
            if problem:
                self.error("/catalogue", problem)
            else:
                header.name = document["catalogue"]
        if "row_type" in document and document["row_type"] != self.row_type.__name__:
            self.error(
                "/row_type",
                f"{_quote(document['row_type'])} in the file, but row_type="
                f"{self.row_type.__name__} was asked for",
            )
        if "about" in document:
            about = self.text(document["about"], "/about", prose=True)
            if about is not None and not about.strip():
                self.error(
                    "/about", "is empty; say what the document is and how it was read"
                )
            header.about = about or ""
        basis = document.get("basis")
        if basis is not None and basis not in CATALOGUE_BASES:
            self.error(
                "/basis",
                f"is {_quote(basis)}, which is not one of {', '.join(CATALOGUE_BASES)}",
            )
        elif basis is not None:
            header.basis = basis
        header.conventions = self.conventions(document.get("conventions", []))
        version = document.get("phonometry_version")
        if version is not None and not isinstance(version, str):
            self.error("/phonometry_version", f"is {_quote(version)}, not text")
        if "provenance" in document:
            header.provenance = self.provenance(document["provenance"])
        if "rows" in document:
            header.rows = self.rows(document["rows"])

    def conventions(self, held: object) -> tuple[str, ...]:
        if not isinstance(held, (list, tuple)):
            self.error("/conventions", f"holds {_quote(held)}, not a list of texts")
            return ()
        found = [
            self.text(text, _pointer("conventions", index))
            for index, text in enumerate(held)
        ]
        return tuple(text for text in found if text is not None)

    def provenance(self, held: object) -> Provenance | None:
        if not isinstance(held, Mapping):
            self.error("/provenance", f"holds {_quote(held)}, not an object")
            return None
        values: dict[str, Any] = {}
        failed = False
        for key, value in held.items():
            where = _pointer("provenance", key)
            if key not in _PROVENANCE_FIELDS:
                self.unknown_key(where, key, _PROVENANCE_FIELDS, "a provenance")
                failed = True
            elif key == "field_test_standards":
                values[key] = self.test_standards(value, where)
            elif key == "version" and value is None:
                values[key] = None
            else:
                kept = self.text(value, where)
                failed = failed or kept is None
                values[key] = kept
        for key in _PROVENANCE_REQUIRED:
            if key not in held:
                extra = (
                    "; write null for one that prints none" if key == "version" else ""
                )
                self.error("/provenance", f"needs {key!r}{extra}")
                failed = True
        if failed:
            return None
        try:
            return Provenance(**values)
        except CatalogueError as error:
            issue = error.issues[0]
            self.error(_pointer("provenance", issue.field), issue.message)
        return None

    def test_standards(self, held: object, where: str) -> dict[str, str]:
        if not isinstance(held, Mapping):
            self.error(where, f"holds {_quote(held)}, not an object")
            return {}
        found: dict[str, str] = {}
        for written, standard in held.items():
            at = f"{where}{_pointer(written)}"
            if not isinstance(written, str):
                continue
            target, why = self.names.resolve(written, self.names.numeric, frozenset())
            if target is None:
                self.error(at, why)
                continue
            text = self.text(standard, at)
            if text is not None:
                found[target] = text
        return found

    def rows(self, held: object) -> list[_Row]:
        if not isinstance(held, (list, tuple)) or not held:
            self.error("/rows", "a catalogue holds a list of rows, at least one")
            return []
        if len(held) > _MAX_ROWS:
            self.error(
                "/rows",
                f"holds {len(held)} rows, and a catalogue holds at most {_MAX_ROWS}",
            )
            return []
        seen: dict[str, int] = {}
        found = [self.row(index, row, seen) for index, row in enumerate(held)]
        return [row for row in found if row is not None]

    def unknown_key(
        self, where: str, key: str, allowed: Sequence[str] | frozenset[str], what: str
    ) -> None:
        close = _closest(key, frozenset(allowed))
        hint = f"; did you mean {close!r}?" if close else ""
        self.error(where, f"{what} has no {key!r}{hint}")

    # -- a row ---------------------------------------------------------------
    def row(self, index: int, held: object, seen: dict[str, int]) -> _Row | None:
        at = _pointer("rows", index)
        if not isinstance(held, Mapping):
            self.error(at, f"holds {_quote(held)}, and a row is a JSON object")
            return None
        before = len(self.issues.found)
        key = self.row_key(held.get("key"), at, seen, index)
        read = _Row(index, key or "")
        for name, value in held.items():
            if isinstance(name, str) and name != "key":
                self.cell(read, name, value, f"{at}{_pointer(name)}")
        for name in self.required:
            if name not in held:
                self.error(
                    at,
                    f"every {self.row_type.__name__} row needs {name!r}",
                    row_key=read.key,
                    field_name=name,
                )
        if key is None or len(self.issues.found) > before:
            return None
        return read

    def row_key(
        self, key: object, at: str, seen: dict[str, int], index: int
    ) -> str | None:
        if key is None:
            self.error(at, "every row needs a key of its own")
            return None
        if not isinstance(key, str) or not _KEY.fullmatch(key):
            self.error(
                f"{at}/key",
                f"is {_quote(key)}; a key is up to 128 letters, digits and ._+- "
                "characters, starting with a letter, a digit or an underscore, "
                "with no '/', ':' or space",
            )
            return None
        if key in seen:
            self.error(
                f"{at}/key",
                f"{key!r} is the key of row {seen[key]} too; every row has a key "
                "of its own",
                row_key=key,
            )
            return None
        seen[key] = index
        return key

    def cell(self, read: _Row, name: str, value: object, where: str) -> None:
        """One member of a row, sent to the check its name calls for."""
        names = self.names
        if name.startswith("x-"):
            self.own_column(read, name, value, where)
        elif name in _FORBIDDEN:
            self.error(where, _FORBIDDEN[name], row_key=read.key, field_name=name)
        elif name == "provenance":
            self.narrowed(read, value, where)
        elif name in names.hedges:
            read.where[name] = where
            kept = self.hedge(read, name, value, where)
            if kept is not _INVALID:
                read.cells[name] = kept
        elif name in names.kinds:
            read.where[name] = where
            kept = self.value(read, name, value, where)
            if kept is not _INVALID:
                read.cells[name] = kept
        elif name in names.spellings.aliases:
            target = names.spellings.aliases[name][0]
            read.where[target] = where
            if value is None or _is_number(value):
                read.cells[name] = value
            else:
                self.expected_number(read, value, where, target)
        else:
            _, why = names.resolve(name, frozenset(names.kinds), frozenset())
            self.error(where, why, row_key=read.key, field_name=name)

    def expected_number(
        self, read: _Row, value: object, where: str, field_name: str = ""
    ) -> None:
        self.error(
            where,
            f"expected a number, got {_what_it_is(value)}",
            row_key=read.key,
            field_name=field_name,
        )

    def value(self, read: _Row, name: str, value: object, where: str) -> object:
        """A cell named as its field, checked against the field's kind."""
        kind = self.names.kinds[name]
        if kind in ("number", "whole") and value is None:
            return None
        if kind == "number":
            if _is_number(value):
                return _plain(value)
            self.expected_number(read, value, where, name)
            return _INVALID
        if kind == "whole":
            whole = _plain(value) if _is_number(value) else None
            if isinstance(whole, int):
                return whole
            what = f"expected a whole number, got {_what_it_is(value)}"
        elif kind == "flag":
            if isinstance(value, bool):
                return value
            what = f"expected true or false, got {_what_it_is(value)}"
        elif kind == "text":
            kept = self.text(value, where, prose=name in _PROSE, row_key=read.key)
            return _INVALID if kept is None else kept
        elif kind == "provenance":
            what = "a file writes a provenance only as the row's own provenance"
        else:
            return _plain_tree(value)
        self.error(where, what, row_key=read.key, field_name=name)
        return _INVALID

    def own_column(self, read: _Row, name: str, value: object, where: str) -> None:
        if not _EXTRA.fullmatch(name):
            self.error(
                where,
                f"{name!r} is not a column name: after 'x-' come letters, digits "
                "and ._+- characters",
                row_key=read.key,
            )
            return
        if isinstance(value, str):
            kept = self.text(value, where, row_key=read.key)
            if kept is not None:
                read.extras[name] = kept
        elif _is_number(value):
            read.extras[name] = _number_text(value)
        else:
            self.error(
                where,
                f"holds {_what_it_is(value)}; a column of your own holds text or "
                "a number",
                row_key=read.key,
            )

    def narrowed(self, read: _Row, held: object, where: str) -> None:
        if not isinstance(held, Mapping):
            self.error(where, f"holds {_quote(held)}, not an object", row_key=read.key)
            return
        for key, value in held.items():
            at = f"{where}{_pointer(key)}"
            if key in _PROVENANCE_FIELDS and key not in _ROW_PROVENANCE:
                self.error(
                    at,
                    f"a row cannot change the document's {key}: another document "
                    "is another catalogue file",
                    row_key=read.key,
                )
            elif key not in _ROW_PROVENANCE:
                self.unknown_key(at, key, _ROW_PROVENANCE, "a row's provenance")
            elif key == "field_test_standards":
                read.narrowed[key] = self.test_standards(value, at)
            else:
                kept = self.text(value, at, row_key=read.key)
                if kept is not None:
                    read.narrowed[key] = kept

    # -- hedges --------------------------------------------------------------
    def hedge(self, read: _Row, hedge: str, held: object, where: str) -> object:
        """A hedge: its keys resolved to fields, its entries checked."""
        names = self.names
        numeric_only = hedge in self.row_type._number_hedges
        allowed = names.numeric if numeric_only else names.cells
        words = _HEDGE_WORDS.get(hedge, frozenset())
        if names.kinds[hedge] == "set":
            if not isinstance(held, (list, tuple)):
                self.error(
                    where,
                    f"holds {_quote(held)}, not a list of fields",
                    row_key=read.key,
                )
                return _INVALID
            for index, written in enumerate(held):
                self.named(read, written, f"{where}{_pointer(index)}", allowed, words)
            return list(held)
        if not isinstance(held, Mapping):
            self.error(where, f"holds {_quote(held)}, not an object", row_key=read.key)
            return _INVALID
        kept: dict[str, object] = {}
        for written, entry in held.items():
            at = f"{where}{_pointer(written)}"
            target = self.named(read, written, at, allowed, words)
            if target is None:
                continue
            read.where.setdefault(target, at)
            checked = self.entry(read, hedge, entry, at, alias=written != target)
            if checked is not _INVALID:
                kept[written] = checked
        return kept

    def named(
        self,
        read: _Row,
        written: object,
        where: str,
        allowed: frozenset[str],
        words: frozenset[str],
    ) -> str | None:
        if not isinstance(written, str):
            self.error(
                where, f"names {_quote(written)}, which is not text", row_key=read.key
            )
            return None
        target, why = self.names.resolve(written, allowed, words)
        if target is None:
            self.error(where, why, row_key=read.key, field_name=written)
        return target

    def entry(
        self, read: _Row, hedge: str, entry: object, at: str, *, alias: bool
    ) -> object:
        """One entry of a hedge, in the shape the hedge takes."""
        if hedge == "ranges":
            return self.pair(read, entry, at, alias=alias, open_ends=True)
        if hedge == "reported":
            return self.readings(read, entry, at, alias=alias)
        if hedge == "uncertainty":
            return self.number(read, entry, at, alias=alias)
        if hedge == "converted":
            if (
                isinstance(entry, (list, tuple))
                and len(entry) == _PAIR
                and all(isinstance(part, str) and part.strip() for part in entry)
            ):
                return [unicodedata.normalize("NFC", part) for part in entry]
            self.error(
                at,
                f"holds {_quote(entry)}; converted gives the page's figure and "
                'its unit as two texts, as ["5", "kPa s/m2"]',
                row_key=read.key,
            )
            return _INVALID
        if hedge == "basis":
            if entry in CATALOGUE_BASES:
                return entry
            self.error(
                at,
                f"is {_quote(entry)}, which is not one of {', '.join(CATALOGUE_BASES)}",
                row_key=read.key,
            )
            return _INVALID
        if hedge in _TEXT_HEDGES:
            kept = self.text(entry, at, row_key=read.key)
            return _INVALID if kept is None else kept
        return _plain_tree(entry)

    def number(self, read: _Row, entry: object, at: str, *, alias: bool) -> object:
        if _is_number(entry):
            return entry if alias else _plain(entry)
        self.expected_number(read, entry, at)
        return _INVALID

    def pair(
        self, read: _Row, entry: object, at: str, *, alias: bool, open_ends: bool
    ) -> object:
        if not isinstance(entry, (list, tuple)) or len(entry) != _PAIR:
            open_side = ", null for an open one" if open_ends else ""
            self.error(
                at,
                f"holds {_quote(entry)}; an interval is a list of two ends{open_side}",
                row_key=read.key,
            )
            return _INVALID
        ends: list[object] = []
        for index, end in enumerate(entry):
            if end is None and open_ends:
                ends.append(None)
                continue
            checked = self.number(read, end, f"{at}{_pointer(index)}", alias=alias)
            if checked is _INVALID:
                return _INVALID
            ends.append(checked)
        return ends

    def readings(self, read: _Row, entry: object, at: str, *, alias: bool) -> object:
        if not isinstance(entry, (list, tuple)) or not entry:
            self.error(
                at,
                f"holds {_quote(entry)}; a list of readings holds at least one",
                row_key=read.key,
            )
            return _INVALID
        found: list[object] = []
        for index, reading in enumerate(entry):
            where = f"{at}{_pointer(index)}"
            if isinstance(reading, (list, tuple)):
                checked = self.pair(read, reading, where, alias=alias, open_ends=False)
            else:
                checked = self.number(read, reading, where, alias=alias)
            if checked is _INVALID:
                return _INVALID
            found.append(checked)
        return found


def _plain_tree(value: object) -> object:
    """A caller's own set or mapping field, its numbers made plain."""
    if isinstance(value, Mapping):
        return {key: _plain_tree(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_tree(item) for item in value]
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    return _plain(value)


# ---------------------------------------------------------------------------
# Reading: building the rows
# ---------------------------------------------------------------------------
def _check_row_type(row_type: object) -> type[CatalogueRow]:
    """*row_type* as a row class, or a :class:`TypeError` saying what it is.

    :raises TypeError: for anything but a subclass of :class:`CatalogueRow`,
        with a word of its own for a :class:`~phonometry.fluids.Fluid`, and
        for a class with a field the row contract cannot classify.
    """
    if isinstance(row_type, type) and issubclass(row_type, CatalogueRow):
        field_kinds(row_type)
        return row_type
    from ..fluids import Fluid

    if isinstance(row_type, type) and issubclass(row_type, Fluid):
        msg = (
            "row_type=Fluid: a Fluid is the state of a medium, not a catalogue "
            "row, and it keeps no name or source; build one directly, or take "
            "one from Gas.ideal_state()"
        )
        raise TypeError(msg)
    msg = (
        f"row_type is {_quote(row_type)}; a catalogue holds rows of a subclass of "
        "phonometry.io.CatalogueRow, such as materials.PorousMaterial"
    )
    raise TypeError(msg)


def _build(
    reader: _Reader, header: _Header, provenance: Provenance
) -> tuple[dict[str, CatalogueRow], dict[str, dict[str, str]]]:
    """Every row of a document that passed, built through ``from_printed``."""
    rows: dict[str, CatalogueRow] = {}
    extras: dict[str, dict[str, str]] = {}
    for read in header.rows:
        row = _build_row(reader, header, provenance, read)
        if row is not None:
            key = f"{header.name}/{read.key}"
            rows[key] = row
            if read.extras:
                extras[key] = read.extras
    return rows, extras


def _build_row(
    reader: _Reader, header: _Header, provenance: Provenance, read: _Row
) -> CatalogueRow | None:
    at = _pointer("rows", read.index)
    if read.narrowed:
        narrowed = dict(read.narrowed)
        if "field_test_standards" in narrowed:
            narrowed["field_test_standards"] = {
                **provenance.field_test_standards,
                **narrowed["field_test_standards"],
            }
        try:
            provenance = dataclasses.replace(provenance, **narrowed)
        except CatalogueError as error:
            issue = error.issues[0]
            where = f"{at}/provenance{_pointer(issue.field) if issue.field else ''}"
            reader.error(where, issue.message, row_key=read.key)
            return None
    cells = dict(read.cells)
    if header.basis:
        basis = dict(cells.get("basis") or {})
        basis.setdefault("row", header.basis)
        cells["basis"] = basis
    cells.update(source=provenance.cited(), table=header.name, provenance=provenance)
    try:
        return reader.row_type.from_printed(**cells)
    except CatalogueError as error:
        for issue in error.issues:
            reader.error(
                read.where.get(issue.field, at),
                issue.message,
                row_key=read.key,
                field_name=issue.field,
            )
    return None


def _notes(rows: Mapping[str, CatalogueRow], label: str) -> tuple[CatalogueIssue, ...]:
    """What is worth a second look in the rows read, without changing any."""
    notes: list[CatalogueIssue] = []
    for index, (key, row) in enumerate(rows.items()):
        found: list[tuple[str, str]] = []
        provenance = row.provenance
        measured = "measured" in row.basis.values()
        if (
            measured
            and provenance is not None
            and not (provenance.report or provenance.laboratory)
        ):
            found.append(
                (
                    "",
                    "the basis is measured, and the provenance names neither a "
                    "report nor a laboratory the measurement came from",
                )
            )
        found += [
            (
                name,
                f"unquantified holds {len(word)} characters for {name!r}, which "
                "reads as a sentence: what a page prints in place of a number is "
                "a word or a code, and a sentence goes in not_derivable or in "
                "the note",
            )
            for name, word in row.unquantified.items()
            if len(word) > _WORD
        ]
        found += [("", message) for message in row._catalogue_notes()]
        notes += [
            CatalogueIssue(
                file=label,
                location=_pointer("rows", index),
                row_key=key.partition("/")[2],
                field=name,
                message=message,
                severity="note",
            )
            for name, message in found
        ]
    return tuple(notes)


def _read(
    document: object, row_type: type[CatalogueRow], label: str, digest: str
) -> Catalogue[Any]:
    """The catalogue *document* holds, the problems in it refused at once.

    The rows the document pass found nothing wrong with are built even when
    other rows or other keys hold problems, so that the one refusal also
    names what the row contract finds in them. A row that breaks the
    contract is named once, for the first rule it breaks.
    """
    issues = _Issues(label)
    reader = _Reader(row_type, issues)
    header = reader.document(document)
    if header is None or header.provenance is None:
        issues.refuse()
    rows, extras = _build(reader, header, header.provenance)
    if issues.found:
        issues.found.sort(key=_row_order)
        issues.refuse()
    return Catalogue(
        name=header.name,
        row_type=row_type,
        about=header.about,
        provenance=header.provenance,
        rows=rows,
        extras=extras,
        conventions=header.conventions,
        notes=_notes(rows, label),
        schema_version=CATALOGUE_SCHEMA_VERSION,
        file_sha256=digest,
    )


def _row_order(issue: CatalogueIssue) -> int:
    """Where an issue stands: the document's own keys first, then each row.

    Issues of one place keep the order they were found in.
    """
    head, _, rest = issue.location.removeprefix("/").partition("/")
    index = rest.partition("/")[0]
    return int(index) + 1 if head == "rows" and index.isdigit() else 0


def _refusal(label: str, location: str, message: str) -> CatalogueError:
    """An error about the whole document, before any of it is read."""
    issue = CatalogueIssue(file=label, location=location, message=message)
    head = ": ".join(part for part in (label, location) if part)
    return CatalogueError(f"{head}: {message}", issues=(issue,))


def _decode(text: str, label: str) -> object:
    """The document a text holds, or a refusal of text that is not JSON."""
    try:
        document, _ = decode_marked(text, figures=True)
    except json.JSONDecodeError as error:
        location = f"line {error.lineno}, column {error.colno}"
        raise _refusal(label, location, f"this is not JSON: {error.msg}") from None
    except RecursionError:
        message = (
            "the text nests deeper than a reader follows, and a catalogue nests "
            f"at most {_MAX_DEPTH} levels"
        )
        raise _refusal(label, "", message) from None
    return document


def _size_refusal(label: str, size: int) -> CatalogueError:
    message = (
        f"is {size} bytes, and a catalogue file is at most {_MAX_BYTES} bytes (16 MiB)"
    )
    return _refusal(label, "", message)


def _warn(catalogue: Catalogue[Any], label: str) -> None:
    """One warning for every note on the catalogue, quoting the first."""
    notes = catalogue.notes
    if not notes:
        return
    shown = [f"  {note}" for note in notes[:_NOTES_SHOWN]]
    if len(notes) > _NOTES_SHOWN:
        shown.append(f"  ... and {len(notes) - _NOTES_SHOWN} more, in Catalogue.notes")
    count = len(notes)
    plural = "s" if count != 1 else ""
    head = (
        f"{label}: {count} note{plural} on this catalogue, in Catalogue.notes; "
        "the rows hold what the document writes"
    )
    warnings.warn("\n".join([head, *shown]), CatalogueWarning, stacklevel=3)


def _json_path(path: str | os.PathLike[str], what: str) -> Path:
    """*path* as a :class:`~pathlib.Path`, if it names a JSON document.

    :raises ValueError: for a name that does not end in ``.json``, in any
        case, since Windows and spreadsheets write ``.JSON`` too.
    """
    target = Path(path)
    if target.suffix.lower() != ".json":
        msg = (
            f"{what} a catalogue document in JSON, whose file name ends in "
            f".json, and {target.name!r} does not"
        )
        raise ValueError(msg)
    return target


def read_catalogue[R: CatalogueRow](
    path: str | os.PathLike[str], *, row_type: type[R]
) -> Catalogue[R]:
    """Read a catalogue of your own from a JSON file into rows of *row_type*.

    The file holds one table: a header with the document's provenance, and
    rows whose cells are named as the fields of *row_type* or in another unit
    of the same kind (the module docstring lays it out). Every row is built
    through :meth:`CatalogueRow.from_printed`, so a row read from a file and
    a packaged row with the same cells are the same row, and
    :meth:`~CatalogueRow.printed`, :meth:`~CatalogueRow.why_missing` and every
    method of the class behave alike on both. Every row carries the
    document's :class:`Provenance`, narrowed by the row where it narrows it,
    and a :attr:`~CatalogueRow.source` composed from it.

    The problems in the file are raised together in one
    :class:`CatalogueError`, each issue with the JSON pointer to it: every
    problem of form, and the first rule of the row contract each row breaks.
    The class named in the file is only compared with *row_type*, and nothing
    the file names is ever imported.

    :param path: The file, whose name ends in ``.json`` (in any case).
    :param row_type: The class of every row, a subclass of
        :class:`CatalogueRow` such as ``materials.PorousMaterial``.
    :return: The catalogue, keyed ``"<catalogue>/<key>"``.
    :raises CatalogueError: for a file larger than 16 MiB, text that is not
        UTF-8 or not JSON, and the problems the document holds, all at once:
        every problem of form, and the first rule of the row contract each
        row breaks.
    :raises TypeError: for a *row_type* that is not a catalogue row class.
    :raises ValueError: for a name that does not end in ``.json``.
    :raises OSError: as the file system raises it, untouched.
    :warns CatalogueWarning: once, when the catalogue carries notes.
    """
    cls = _check_row_type(row_type)
    target = _json_path(path, "read_catalogue reads")
    label = target.name
    size = target.stat().st_size
    if size > _MAX_BYTES:
        raise _size_refusal(label, size)
    raw = target.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        message = f"is not UTF-8 text (byte {error.start}); save it as UTF-8"
        raise _refusal(label, "", message) from None
    document = _decode(text.removeprefix("\ufeff"), label)
    catalogue = _read(document, cls, label, hashlib.sha256(raw).hexdigest())
    _warn(catalogue, label)
    return catalogue


def parse_catalogue[R: CatalogueRow](
    document: str | Mapping[str, Any],
    *,
    row_type: type[R],
    label: str = "<document>",
) -> Catalogue[R]:
    """Read a catalogue from JSON text, or from a mapping already in memory.

    The same reading as :func:`read_catalogue`, for a document that is not a
    file: text built in a notebook, a spreadsheet turned into a dictionary, a
    test. A mapping has no printed digits, so a figure written in another
    unit is converted from the ``repr`` of its float; a ``NaN`` is refused as
    it is from text, but two members of one name cannot be told apart once a
    dictionary has merged them.

    :param document: JSON text, or a mapping of the same shape.
    :param row_type: The class of every row, a subclass of
        :class:`CatalogueRow`.
    :param label: What names the document in every issue.
    :return: The catalogue, keyed ``"<catalogue>/<key>"``. Its
        :attr:`~Catalogue.file_sha256` is the SHA-256 of the text's UTF-8
        bytes, or empty for a mapping.
    :raises CatalogueError: for everything :func:`read_catalogue` refuses.
    :raises TypeError: for a *row_type* that is not a catalogue row class, and
        for a *document* that is neither text nor a mapping.
    :warns CatalogueWarning: once, when the catalogue carries notes.
    """
    cls = _check_row_type(row_type)
    if isinstance(document, str):
        encoded = document.encode("utf-8")
        if len(encoded) > _MAX_BYTES:
            raise _size_refusal(label, len(encoded))
        decoded = _decode(document, label)
        digest = hashlib.sha256(encoded).hexdigest()
    elif isinstance(document, Mapping):
        decoded, digest = document, ""
    else:
        msg = (
            f"document is a {type(document).__name__}; parse_catalogue reads "
            "JSON text or a mapping, and read_catalogue reads a file"
        )
        raise TypeError(msg)
    catalogue = _read(decoded, cls, label, digest)
    _warn(catalogue, label)
    return catalogue


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------
class _Raw:
    """A number written with the digits it was read with."""

    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        self.text = text


def _scalar(value: object) -> str | None:
    """*value* as JSON text, if it is a scalar."""
    if isinstance(value, _Raw):
        return value.text
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, numbers.Integral):
        return str(int(value))
    if isinstance(value, numbers.Real):
        return float.__repr__(float(value))
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    return None


def _dumps(value: object, depth: int = 0) -> str:
    """*value* as indented JSON, a list of scalars kept on one line."""
    scalar = _scalar(value)
    if scalar is not None:
        return scalar
    pad = "  " * (depth + 1)
    close = "  " * depth
    if isinstance(value, Mapping):
        if not value:
            return "{}"
        members = [
            f"{pad}{json.dumps(str(key), ensure_ascii=False)}: {_dumps(item, depth + 1)}"
            for key, item in value.items()
        ]
        return "{\n" + ",\n".join(members) + f"\n{close}}}"
    items = list(value) if isinstance(value, (list, tuple)) else []
    if not items:
        return "[]"
    flat = [_scalar(item) for item in items]
    if all(text is not None for text in flat):
        line = "[" + ", ".join(str(text) for text in flat) + "]"
        if len(line) <= _INLINE:
            return line
    inner = ",\n".join(f"{pad}{_dumps(item, depth + 1)}" for item in items)
    return f"[\n{inner}\n{close}]"


def _same_float(one: float, other: object) -> bool:
    """Whether two numbers are the same double, bit for bit."""
    if not isinstance(other, numbers.Real):
        return False
    return float(one).hex() == float(other).hex()


def _renamed(
    cells: dict[str, Any], old: str, new: str, value: object
) -> dict[str, Any]:
    """*cells* with *old* replaced by *new*, in the same place."""
    return {
        (new if key == old else key): (value if key == old else item)
        for key, item in cells.items()
    }


class _Writer:
    """Rows of one class, as the document that reads back into the same rows."""

    def __init__(self, rows: Mapping[str, object]) -> None:
        values = list(rows.values())
        self.row_type = self.check_types(values)
        self.rows: Mapping[str, CatalogueRow] = rows  # type: ignore[assignment]
        self.names = _Names(self.row_type)

    @staticmethod
    def check_types(values: Sequence[object]) -> type[CatalogueRow]:
        if not values:
            msg = "a catalogue with no rows says nothing, and there is nothing to write"
            raise CatalogueError(msg)
        first = type(values[0])
        if not issubclass(first, CatalogueRow):
            what = (
                "Fluid states, which are not catalogue rows and keep no name or source"
                if first.__name__ == "Fluid"
                else first.__name__
            )
            msg = f"the mapping holds {what}, and a catalogue file holds catalogue rows"
            raise TypeError(msg)
        other = next((type(row) for row in values if type(row) is not first), None)
        if other is not None:
            msg = (
                f"the mapping holds {first.__name__} and {other.__name__} rows, "
                "and a catalogue file holds rows of one class; write each class "
                "to a file of its own"
            )
            raise TypeError(msg)
        return first

    def check_keys(self) -> None:
        seen: dict[str, str] = {}
        for key in self.rows:
            short = str(key).rpartition("/")[2]
            if not _KEY.fullmatch(short):
                msg = (
                    f"the row {key!r} has the key {short!r}, which a catalogue "
                    "file cannot hold: up to 128 letters, digits and ._+- "
                    "characters, with no space"
                )
                raise CatalogueError(msg)
            if short in seen:
                msg = (
                    f"the rows {seen[short]!r} and {key!r} would both be {short!r} "
                    "in one catalogue file"
                )
                raise CatalogueError(msg)
            seen[short] = str(key)

    def shared(self, attribute: str) -> list[str]:
        """The values of one field across the rows, each once."""
        return list(
            dict.fromkeys(getattr(row, attribute) for row in self.rows.values())
        )

    # -- the header ----------------------------------------------------------
    def packaged(self) -> tuple[Provenance, dict[str, Any] | None]:
        """The provenance of a table of the library's own, and the table."""
        tables = self.shared("table")
        if len(tables) != 1:
            msg = (
                f"the rows come from {len(tables)} tables ({_listed(tables)}), and "
                "a catalogue file holds one: filter them first, as "
                f"{{k: r for k, r in rows.items() if r.table == {tables[0]!r}}}"
            )
            raise CatalogueError(msg)
        sources = self.shared("source")
        if len(sources) != 1:
            msg = (
                f"the rows of {tables[0]!r} cite {len(sources)} sources, and a "
                "catalogue file cites one document; pass provenance= for it"
            )
            raise CatalogueError(msg)
        provenance = Provenance(
            kind="publication",
            document=sources[0],
            version=None,
            consulted=datetime.datetime.now(tz=datetime.UTC).date().isoformat(),
        )
        return provenance, _packaged_table(next(iter(self.rows.values())))

    def document_provenance(self) -> Provenance:
        """The provenance every row shares, less what the rows narrow."""
        held = [row.provenance for row in self.rows.values()]
        first = held[0]
        whole = [name for name in _PROVENANCE_FIELDS if name not in _ROW_PROVENANCE]
        if first is None or any(
            provenance is None
            or any(getattr(provenance, name) != getattr(first, name) for name in whole)
            for provenance in held
        ):
            msg = (
                "the rows were not all read from one document, and a catalogue "
                "file holds one; write each document's rows to a file of its own"
            )
            raise CatalogueError(msg)
        common: dict[str, Any] = {}
        for name in _ROW_PROVENANCE:
            if name == "field_test_standards":
                continue
            shared = all(
                provenance is not None
                and getattr(provenance, name) == getattr(first, name)
                for provenance in held
            )
            common[name] = getattr(first, name) if shared else ""
        # A row narrows the standards of a document field by field, so the
        # document keeps every one all its rows cite alike.
        common["field_test_standards"] = {
            field_name: standard
            for field_name, standard in first.field_test_standards.items()
            if all(
                provenance is not None
                and provenance.field_test_standards.get(field_name) == standard
                for provenance in held
            )
        }
        return dataclasses.replace(first, **common)

    # -- a row ---------------------------------------------------------------
    def row(
        self,
        key: str,
        row: CatalogueRow,
        document: Provenance,
        extras: Mapping[str, str],
    ) -> dict[str, Any]:
        """One row as the document writes it: its cells, never a derived one."""
        cells = row.printed_fields()
        out: dict[str, Any] = {"key": key.rpartition("/")[2], "name": cells.pop("name")}
        for name in ("variant", "group"):
            if name in cells:
                out[name] = cells.pop(name)
        converted = dict(cells.pop("converted", {}))
        note = cells.pop("note", None)
        for name in ("source", "table", "provenance"):
            cells.pop(name, None)
        hedges = self.names.hedges
        out.update(
            (name, _plain_value(value))
            for name, value in cells.items()
            if name not in hedges
        )
        out.update(
            (name, _plain_value(value))
            for name, value in cells.items()
            if name in hedges
        )
        records: dict[str, list[str]] = {}
        for name, (figure, unit) in converted.items():
            written = self.as_alias(out, row, name, figure, unit)
            if written is None:
                records[name] = [figure, unit]
            else:
                out = written
        if records:
            out["converted"] = records
        if note is not None:
            out["note"] = note
        narrowed = _narrowed(row.provenance, document)
        if narrowed:
            out["provenance"] = narrowed
        out.update(extras)
        return out

    def as_alias(
        self, out: dict[str, Any], row: CatalogueRow, name: str, figure: str, unit: str
    ) -> dict[str, Any] | None:
        """The row with a converted cell under its alias, if it reads back exactly.

        The cell is its value (with its plus-or-minus), its range or its
        list, each written as the page's figures under the name of the unit
        they are in. When any number of the cell would not convert back to
        the same float, the whole cell stays in the field's own unit with
        its ``converted`` record beside it: every number of one cell is
        written in one unit.
        """
        found = next(
            (
                (written, alias)
                for written, (target, alias) in self.names.spellings.aliases.items()
                if target == name and alias.unit == unit
            ),
            None,
        )
        if found is None:
            return None
        written, alias = found
        pieces = _alias_pieces(row, name, figure, alias)
        if pieces is None:
            return None
        for part, entry in pieces.items():
            if part == "value":
                out = _renamed(out, name, written, entry)
            else:
                out = {**out, part: _renamed(out[part], name, written, entry)}
        return out


def _plain_value(value: object) -> object:
    """A field as JSON holds it: a set sorted, a mapping a dict, a tuple a list."""
    if isinstance(value, (frozenset, set)):
        return sorted(value)
    if isinstance(value, Mapping):
        return {key: _plain_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain_value(item) for item in value]
    return value


def _narrowed(provenance: Provenance | None, document: Provenance) -> dict[str, Any]:
    """What a row's provenance says that its document's does not.

    The standards of single fields are narrowed one by one, as the reader
    reads them: a row writes the ones its document does not cite alike.
    """
    if provenance is None:
        return {}
    found: dict[str, Any] = {}
    for name in _ROW_PROVENANCE:
        value = getattr(provenance, name)
        if name == "field_test_standards":
            own = {
                field_name: standard
                for field_name, standard in value.items()
                if document.field_test_standards.get(field_name) != standard
            }
            if own:
                found[name] = own
        elif value != getattr(document, name):
            found[name] = value
    return found


def _exact(figure: str, alias: UnitAlias, held: object) -> _Raw | None:
    """*figure* as written, if it converts to exactly the number *held*."""
    if not _JSON_NUMBER.fullmatch(figure):
        return None
    if not _same_float(convert_figure(figure, alias.factor, alias.offset), held):
        return None
    return _Raw(figure)


def _alias_pieces(
    row: CatalogueRow, name: str, figure: str, alias: UnitAlias
) -> dict[str, object] | None:
    """Every number of a converted cell as the page's figure, or ``None``.

    :return: The value (and its plus-or-minus), the range or the list, each
        keyed by the part of the row it goes in, when every figure converts
        back to the float the row holds.
    """
    value = getattr(row, name)
    ranged, listed = name in row.ranges, name in row.reported
    if value is not None:
        raw = None if ranged or listed else _exact(figure, alias, value)
        if raw is None:
            return None
        pieces: dict[str, object] = {"value": raw}
        spread = row.uncertainty.get(name)
        if spread is not None:
            text = _spread_figure(spread, alias)
            if text is None:
                return None
            pieces["uncertainty"] = _Raw(text)
        return pieces
    if name in row.uncertainty or ranged == listed:
        return None
    if ranged:
        ends = _range_pieces(row, name, figure, alias)
        return None if ends is None else {"ranges": ends}
    entries = row.reported[name]
    spoken = figure.split(", ")
    if len(spoken) != len(entries):
        return None
    readings: list[object] = []
    for text, entry in zip(spoken, entries, strict=True):
        if isinstance(entry, tuple):
            parts = text.split(" to ")
            if len(parts) != _PAIR:
                return None
            pair = [
                _exact(part, alias, end) for part, end in zip(parts, entry, strict=True)
            ]
            if None in pair:
                return None
            readings.append(pair)
        else:
            raw = _exact(text, alias, entry)
            if raw is None:
                return None
            readings.append(raw)
    return {"reported": readings}


def _range_pieces(
    row: CatalogueRow, name: str, figure: str, alias: UnitAlias
) -> list[object] | None:
    """The ends of a converted range as the page's figures, or ``None``."""
    low, high = row.ranges[name]
    if name in row.bounded_above:
        spoken: list[str | None] = [None, figure]
    elif name in row.bounded_below:
        spoken = [figure, None]
    else:
        parts = figure.split(" to ")
        if len(parts) != _PAIR:
            return None
        spoken = [parts[0], parts[1]]
    ends: list[object] = []
    for text, end in zip(spoken, (low, high), strict=True):
        if text is None:
            if end is not None:
                return None
            ends.append(None)
            continue
        raw = _exact(text, alias, end)
        if raw is None:
            return None
        ends.append(raw)
    return ends


def _spread_figure(spread: float, alias: UnitAlias) -> str | None:
    """A plus-or-minus in the alias's unit that converts back exactly."""
    text = float.__repr__(float(Fraction(spread) / alias.factor))
    if _same_float(convert_figure(text, alias.factor), spread):
        return text
    return None


def _packaged_table(row: CatalogueRow) -> dict[str, Any] | None:
    """The packaged table a row was read from, for its about and legends.

    Found beside the module of the row's class, and only for a table name of
    the packaged form, so no name a row carries can reach another file.
    """
    from importlib.resources import files

    table = row.table
    if not (_RESERVED.match(table) and _NAME_CHARS.fullmatch(table)) or ".." in table:
        return None
    for cls in type(row).__mro__:
        module = getattr(cls, "__module__", "")
        if not module.startswith("phonometry.") or module.startswith(
            "phonometry._internal"
        ):
            continue
        package = module.rpartition(".")[0]
        try:
            resource = files(f"{package}.data") / f"{table}.json"
        except ModuleNotFoundError:
            continue
        if resource.is_file():
            return read_packaged(package, f"{table}.json")
    return None


#: The characters a packaged table's name is made of.
_NAME_CHARS = re.compile(r"[a-z0-9][a-z0-9._-]*")


def _write_atomic(target: Path, text: str, *, overwrite: bool) -> None:
    """Write *text* to *target* through a file beside it, renamed into place.

    :raises FileExistsError: for a file already there without *overwrite*,
        and for a symbolic link at the name, which is never followed.
    """
    if target.is_symlink():
        msg = f"{target} is a symbolic link, and write_catalogue does not write through one"
        raise FileExistsError(msg)
    if target.exists() and not overwrite:
        msg = f"{target} exists; pass overwrite=True to replace it"
        raise FileExistsError(msg)
    temporary = target.with_name(f".{target.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(target)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _document(
    writer: _Writer,
    rows: Mapping[str, object],
    catalogue: str | None,
    about: str | None,
    provenance: Provenance | None,
) -> dict[str, Any]:
    """The document :func:`write_catalogue` writes."""
    from .._version import __version__

    conventions: tuple[str, ...] = ()
    extras: Mapping[str, Mapping[str, str]] = {}
    told = about
    if isinstance(rows, Catalogue):
        name = catalogue or rows.name
        told = about if about is not None else rows.about
        document_provenance = provenance or rows.provenance
        conventions = rows.conventions
        extras = rows.extras
    elif all(row.provenance is None for row in writer.rows.values()):
        default, table = writer.packaged()
        if catalogue is None:
            msg = (
                "catalogue= is required to write a table of the library's own: "
                "the table's own name has the packaged form, which a file of "
                "yours cannot take"
            )
            raise TypeError(msg)
        name = catalogue
        document_provenance = provenance or default
        if told is None and table is not None:
            told = table["about"]
        conventions = tuple(table.get("conventions", ())) if table is not None else ()
    else:
        document_provenance = provenance or writer.document_provenance()
        tables = writer.shared("table")
        name = catalogue or (tables[0] if len(tables) == 1 else "")
    if not name:
        msg = "catalogue= is required: the rows do not share a catalogue's name"
        raise TypeError(msg)
    if told is None:
        msg = "about= is required: the rows bring no text saying what the document is"
        raise TypeError(msg)
    problem = _name_problem(name)
    if problem:
        msg = f"catalogue={name!r}: {problem}"
        raise CatalogueError(msg)
    writer.check_keys()
    document: dict[str, Any] = {
        "schema": CATALOGUE_SCHEMA,
        "schema_version": CATALOGUE_SCHEMA_VERSION,
        "catalogue": name,
        "row_type": writer.row_type.__name__,
        "about": told,
        "provenance": _provenance_object(document_provenance),
    }
    if conventions:
        document["conventions"] = list(conventions)
    document["phonometry_version"] = __version__
    document["rows"] = [
        writer.row(key, row, document_provenance, extras.get(key, {}))
        for key, row in writer.rows.items()
    ]
    return document


def _provenance_object(provenance: Provenance) -> dict[str, Any]:
    """A provenance as the document writes it: every field, in order."""
    return {
        item.name: _plain_value(getattr(provenance, item.name))
        for item in dataclasses.fields(provenance)
    }


def write_catalogue(
    rows: Mapping[str, CatalogueRow],
    path: str | os.PathLike[str],
    *,
    catalogue: str | None = None,
    about: str | None = None,
    provenance: Provenance | None = None,
    overwrite: bool = False,
) -> tuple[Path, ...]:
    """Write rows as a catalogue file that reads back into the same rows.

    The document :func:`read_catalogue` reads, written so that reading it
    gives rows equal to these, field for field: the cells each row's page
    prints, as :meth:`CatalogueRow.printed_fields` gives them, and never a
    derived value, which the reader works out again. A value converted from
    another unit is written in that unit, under the name that carries it,
    when that reads back to the same float, and otherwise in the field's own
    unit with its ``converted`` record beside it, as the degrees Fahrenheit
    and the psi of a damping table are.

    A :class:`Catalogue` brings its name, its ``about``, its provenance, its
    legends and its ``x-...`` columns. A table of the library's own (a
    ``PUBLISHED_*`` catalogue filtered by ``row.table``) needs a *catalogue*
    name that is not of the packaged form, and takes the table's ``about``
    and legends, with a provenance that cites the publication as the rows do
    and records the day of the export as the day it was consulted: the
    edition is in the citation already, and the copy consulted is the
    library's on that day. Pass *provenance* for a file that has to come out
    the same every day.

    The file is written beside its final name and renamed into place, so a
    reader never finds half of it.

    :param rows: A :class:`Catalogue`, or a mapping of rows of one class.
    :param path: Where to write, a name ending in ``.json`` (in any case).
    :param catalogue: The catalogue's name. Required for a table of the
        library's own, and for rows of yours that do not share one.
    :param about: What the document is; required when the rows bring none.
    :param provenance: The document the rows were read from, in place of the
        one they bring.
    :param overwrite: Replace a file already at *path*.
    :return: The paths written.
    :raises CatalogueError: for no rows, rows from more than one table or
        document, a key a file cannot hold, or a name that is reserved or
        malformed.
    :raises TypeError: for rows that are not catalogue rows of one class
        (fluid states among them), or a *catalogue* or *about* the rows
        need and do not bring.
    :raises ValueError: for a name that does not end in ``.json``.
    :raises FileExistsError: for a file at *path* without *overwrite*, and
        for a symbolic link at *path*.
    """
    target = _json_path(path, "write_catalogue writes")
    if not isinstance(rows, Mapping):
        msg = f"rows is a {type(rows).__name__}, and write_catalogue takes a mapping of rows"
        raise TypeError(msg)
    writer = _Writer(rows)
    document = _document(writer, rows, catalogue, about, provenance)
    _write_atomic(target, _dumps(document) + "\n", overwrite=overwrite)
    return (target,)
