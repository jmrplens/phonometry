#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Reading a published table out of a data file, and the row every table holds.

A catalogue row is data, not code. Keeping the rows in JSON beside the module
that publishes them means a new table is a new file rather than a longer
literal, means one row per record in a diff, and means the provenance gate can
read the citation without importing anything.

The document is one published table: a ``source`` in the grammar
``scripts/check_published_sources.py`` enforces, an ``about`` paragraph saying
what the page is and how it was read, and ``rows``. Every row carries a ``key``
unique within the file, and the rest of its fields are named exactly as the
dataclass that will hold them, so a typo in the data is a ``TypeError`` at
import and not a silently missing column. The reader is strict about the text
itself too: a ``NaN`` or an ``Infinity``, which only CPython's reader accepts,
a name written twice in one object, which JSON resolves by keeping the last,
and a ``/`` in a row key, which separates the table from the row in every
catalogue, are each refused by name before any row is built.

:class:`CatalogueRow` is what every such dataclass inherits: the name, the
citation and the hedges a printed cell can carry instead of a number. A page
prints a range, or a ``~``, or three values from three studies, or a word, and
a catalogue that flattened any of those into a float would be claiming a
measurement the page does not make. The hedges are the same across the
catalogues because the pages are: a range in a table of solids is a range in
a table of porous materials. A row checks itself when it is built, whoever
builds it: a data file, a loader or a caller writing one by hand.

There are two ways to build one. The constructor is literal: the row holds
what it is given, checked and frozen, and nothing more.
:meth:`CatalogueRow.from_printed` is the one path that also works out what
follows from the cells a page prints (a modulus from a speed and a density,
an area in square metres from the page's square feet) and says so in the
row. Every packaged loader builds its rows through it, so a row read from a
data file and a row a caller builds from the same cells are the same row.

A row a caller reads from a catalogue file of their own carries a
:class:`Provenance`: what kind of document the cells were read from, which
version of it, when it was consulted and, for a test report, the laboratory
and the report number. The file names every cell by the field it fills,
either in the unit the field is named for or in another unit of the same
kind (``thickness_m`` for ``thickness_mm``, ``flow_resistivity_kpa_s_m2``
for ``flow_resistivity_pa_s_m2``), and :meth:`CatalogueRow.from_printed`
converts such a figure on its digits and records it in
:attr:`CatalogueRow.converted`, whether the figure is a value, an end of a
range or one of several readings.

The reader of the packaged tables stays private, and so does the reader of a
caller's file, which lives in :mod:`phonometry.io`. :class:`CatalogueRow`,
:class:`BandedRow`, :class:`Provenance`, :class:`CatalogueIssue`,
:class:`CatalogueError`, :data:`CATALOGUE_BASES` and
:data:`PROVENANCE_KINDS` are public, from :mod:`phonometry.io`, because every
catalogue of the library hands out rows built on them, and a caller has to be
able to name the type of what it holds and catch what the constructor
raises. They are defined here and not there because the domain packages that
publish the rows import them, and :mod:`phonometry.io` importing a domain
would close a cycle.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import math
import numbers
import re
import types
import typing
import unicodedata
import weakref
from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field, fields
from decimal import Decimal
from fractions import Fraction
from itertools import chain
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar, Literal, NamedTuple, NoReturn, Self

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

    from numpy.typing import ArrayLike, NDArray

_REQUIRED = ("source", "about", "rows")

#: Everything a packaged table may hold at its top level: the three every
#: table needs, the printed legends two tables carry (``conventions``) and the
#: hedge the two fluid tables put on the whole table (``validity``).
_PACKAGED_KEYS = frozenset({*_REQUIRED, "conventions", "validity"})

#: What a source can say a value is, and nothing else: a test result it
#: gives (``"measured"``), a value, bound or class declared under a product
#: standard or a CE marking (``"declared"``), a figure it worked out itself,
#: by a standard's model, a program or a formula (``"calculated"``), its own
#: estimate (``"estimated"``), or the result of an extended application of a
#: test (``"extended"``). A source that does not say is left without an
#: entry rather than given one of these.
CATALOGUE_BASES: tuple[str, ...] = (
    "measured",
    "declared",
    "calculated",
    "estimated",
    "extended",
)


#: What kind of document a catalogue's cells were read from: a
#: manufacturer's data sheet, a declaration of performance under a product
#: standard, a laboratory's test report, a measurement of one's own, a
#: calculation note, a book or a paper, or something else. The kind decides
#: how a refusal names the document ("the datasheet prints an upper bound
#: of ...") and how the citation of every row is composed from it.
PROVENANCE_KINDS: tuple[str, ...] = (
    "datasheet",
    "declaration_of_performance",
    "test_report",
    "measurement",
    "calculation",
    "publication",
    "other",
)

#: How a sentence names each kind of document as its subject.
_NOUNS: Mapping[str, str] = MappingProxyType(
    {
        "datasheet": "the datasheet",
        "declaration_of_performance": "the declaration of performance",
        "test_report": "the test report",
        "measurement": "the measurement record",
        "calculation": "the calculation note",
        "publication": "the source",
        "other": "the source",
    }
)

#: The subject of a sentence about a row that carries no provenance, which is
#: every packaged row: each cites a page of a book or a standard.
_PAGE = "the page"


@dataclass(frozen=True, kw_only=True)
class CatalogueIssue:
    """One thing wrong with a catalogue, or worth a second look, and where.

    A reader of a catalogue file collects every one of these before it
    builds a single row, so one pass over a file shows everything that has
    to change in it. A :class:`CatalogueError` carries the errors; a note
    rides on the catalogue that was read, in ``Catalogue.notes``.

    :ivar file: The file, as the caller named it; empty for a row built in
        Python.
    :ivar location: Where in the file: a JSON pointer (RFC 6901) such as
        ``"/rows/1/porosity"``; ``"<Python>"`` for a row built in Python.
    :ivar row_key: The key of the row, when the issue sits in one.
    :ivar field: The field of the row, when the issue is about one cell.
    :ivar message: What is wrong and, where it helps, what to write instead.
    :ivar severity: ``"error"``, which stops the read, or ``"note"``, which
        is kept and read past.
    """

    file: str
    location: str
    row_key: str = ""
    field: str = ""
    message: str
    severity: Literal["error", "note"] = "error"

    def __str__(self) -> str:
        """The issue as one line: file, place, row and message."""
        head = ": ".join(part for part in (self.file, self.location) if part)
        if self.row_key:
            head = f"{head} (row {self.row_key!r})" if head else f"row {self.row_key!r}"
        return f"{head}: {self.message}" if head else self.message


class CatalogueError(ValueError):
    """A catalogue that does not say what a reader needs to trust it.

    Raised for a table document that is missing what every table needs (a
    citation, an ``about``, rows, a key per row) or that holds what JSON
    does not (a ``NaN``, a name written twice in one object), and for a row
    that breaks the contract every row is held to when it is built: a
    numeric cell holding text or a ``NaN``, a hedge naming a field the row
    does not have, a bound with no printed end, a density below zero. A
    :class:`ValueError`, because the data is wrong and not the call, whether
    it came from a file or from a caller building a row by hand.

    :attr:`issues` holds the problems found, each a :class:`CatalogueIssue`
    naming where it is. A reader of a catalogue file raises one error for
    the whole file, with every problem of form in it and the first rule of
    the row contract each row breaks; a row built in Python raises one with
    a single issue, located at ``"<Python>"``.
    """

    #: The problems found, in the order they stand in the document.
    issues: tuple[CatalogueIssue, ...]

    def __init__(
        self,
        message: str,
        *,
        issues: tuple[CatalogueIssue, ...] = (),
        field: str = "",
    ) -> None:
        super().__init__(message)
        self.issues = issues or (
            CatalogueIssue(file="", location="<Python>", field=field, message=message),
        )


def _reject(filename: str, what: str) -> NoReturn:
    """Name the file and the defect, because the caller cannot see either."""
    msg = f"{filename}: {what}"
    issue = CatalogueIssue(file=filename, location="", message=what)
    raise CatalogueError(msg, issues=(issue,))


#: A date as ISO 8601 writes it at the precision it is printed with: a year,
#: a month or a day.
_PRINTED_DATE = re.compile(r"\d{4}(-\d{2}(-\d{2})?)?")

#: A calendar day as ISO 8601 writes it.
_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")

#: A SHA-256 digest in hexadecimal.
_DIGEST = re.compile(r"[0-9a-fA-F]{64}")


def _date_is_valid(text: str) -> bool:
    """Whether *text* is a year, a year and month, or a calendar day."""
    if not _PRINTED_DATE.fullmatch(text):
        return False
    padded = text + "-01" * (2 - text.count("-"))
    try:
        datetime.date.fromisoformat(padded)
    except ValueError:
        return False
    return True


@dataclass(frozen=True, kw_only=True)
class Provenance:
    """Which document a catalogue's cells were read from, and how.

    A book's table is cited by its page, and the citation of every packaged
    row says all there is to say. A manufacturer's data sheet is not a book:
    it is revised without notice, the same product has several of them, and
    what it prints may be a laboratory's result, a value declared under a
    product standard or a figure from a calculation. So a row read from a
    caller's catalogue file carries this, and its :attr:`CatalogueRow.source`
    is composed from it: for a ``"publication"`` the document as it is cited,
    and for every other kind the document, its publisher, its version, the
    page and the table, the report and the laboratory, and the day it was
    consulted.

    :ivar kind: One of :data:`PROVENANCE_KINDS`.
    :ivar document: The document's title as it prints it.
    :ivar version: The revision the document prints (``"Rev. 4"``), or
        ``None`` when it prints none, which is a different answer from a
        version nobody wrote down.
    :ivar consulted: The day the document was read, as ``YYYY-MM-DD``: a
        data sheet changes under the same title.
    :ivar publisher: Who issues the document.
    :ivar issued: When the document says it was issued, as ``YYYY``,
        ``YYYY-MM`` or ``YYYY-MM-DD``, at the precision it prints.
    :ivar url: Where the document was found. Never opened by this library.
    :ivar sha256: The digest of the file that was read, in hexadecimal, so
        that the copy can be told apart from a later revision. Never checked
        against anything by this library.
    :ivar page: The page the cells are on.
    :ivar printed_table: The label of the table on the page, as it prints it
        (``"Table 2"``).
    :ivar laboratory: The laboratory that made the measurement.
    :ivar accreditation: The laboratory's accreditation, as printed.
    :ivar report: The number of the test report.
    :ivar test_date: When the test was made, as printed.
    :ivar test_standard: The standard the test followed, as printed
        (``"ISO 9053-1:2018"``).
    :ivar field_test_standards: Field to the standard a document cites for
        that property alone, when it names a different one for each; it
        takes precedence over :attr:`test_standard` for that field.
    """

    kind: str
    document: str
    version: str | None
    consulted: str
    publisher: str = ""
    issued: str = ""
    url: str = ""
    sha256: str = ""
    page: str = ""
    printed_table: str = ""
    laboratory: str = ""
    accreditation: str = ""
    report: str = ""
    test_date: str = ""
    test_standard: str = ""
    field_test_standards: Mapping[str, str] = field(default_factory=dict)

    # A mapping field makes the record unhashable; saying so here gives the
    # refusal the class's name instead of the mapping's.
    __hash__ = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Check each field and freeze the per-field standards.

        :raises CatalogueError: naming the field, for a kind outside
            :data:`PROVENANCE_KINDS`, an empty document, a version that is
            empty text rather than ``None``, a date that is not one, a digest
            that is not SHA-256 in hexadecimal, or a field that is not text.
        """
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name == "field_test_standards":
                self._freeze_standards(value)
            elif item.name == "version":
                if value is not None and not (isinstance(value, str) and value.strip()):
                    self._refuse(
                        "version",
                        f"holds {_quote(value)}; write the version the document "
                        "prints, or None when it prints none",
                    )
            elif not isinstance(value, str):
                self._refuse(item.name, f"holds {_quote(value)}, which is not text")
        self._check_values()

    def _check_values(self) -> None:
        """The checks that read what the text fields say."""
        if self.kind not in PROVENANCE_KINDS:
            self._refuse(
                "kind",
                f"is {self.kind!r}, which is not one of {', '.join(PROVENANCE_KINDS)}",
            )
        if not self.document.strip():
            self._refuse("document", "is empty; a provenance names its document")
        if not (_DAY.fullmatch(self.consulted) and _date_is_valid(self.consulted)):
            self._refuse(
                "consulted",
                f"is {self.consulted!r}; write the day the document was read "
                "as YYYY-MM-DD",
            )
        if self.issued and not _date_is_valid(self.issued):
            self._refuse(
                "issued",
                f"is {self.issued!r}; write it as YYYY, YYYY-MM or YYYY-MM-DD, "
                "at the precision the document prints",
            )
        if self.sha256 and not _DIGEST.fullmatch(self.sha256):
            self._refuse(
                "sha256", f"is {_quote(self.sha256)}, which is not a SHA-256 digest"
            )

    def _freeze_standards(self, value: object) -> None:
        """Hold the per-field standards as a read-only mapping of text."""
        if not isinstance(value, Mapping):
            self._refuse(
                "field_test_standards", f"holds {_quote(value)}, not a mapping"
            )
        for key, standard in value.items():
            if not (
                isinstance(key, str) and isinstance(standard, str) and standard.strip()
            ):
                self._refuse(
                    "field_test_standards",
                    f"maps {_quote(key)} to {_quote(standard)}; each field names "
                    "the standard as text",
                )
        object.__setattr__(self, "field_test_standards", MappingProxyType(dict(value)))

    @staticmethod
    def _refuse(field_name: str, what: str) -> NoReturn:
        msg = f"the provenance's {field_name} {what}"
        raise CatalogueError(msg, field=field_name)

    @property
    def noun(self) -> str:
        """The document as the subject of a sentence: ``"the datasheet"``."""
        return _NOUNS[self.kind]

    def test_standard_of(self, field_name: str) -> str:
        """The standard the test of one field followed, as printed.

        :param field_name: A field of the row.
        :return: The field's own entry in :attr:`field_test_standards`, else
            :attr:`test_standard`, else the empty string.
        """
        return self.field_test_standards.get(field_name, self.test_standard)

    def cited(self) -> str:
        """The citation every row read with this provenance carries as its source.

        A publication is cited as its document is, because a book's citation
        already names its edition and its page. Every other document is
        cited by its title, its publisher, the version it prints (or that it
        prints none), the page and the table, the report and the laboratory,
        and the day it was consulted, because each of those can change under
        the same title.
        """
        if self.kind == "publication":
            return self.document
        text = self.document
        if self.publisher:
            text += f" ({self.publisher})"
        text += (
            f", {self.version}" if self.version is not None else ", no version printed"
        )
        if self.page:
            text += f", p. {self.page}"
        if self.printed_table:
            text += f", {self.printed_table}"
        if self.report:
            text += f"; report {self.report}"
            if self.laboratory:
                text += f" ({self.laboratory})"
        elif self.laboratory:
            text += f"; laboratory {self.laboratory}"
        return f"{text}; consulted {self.consulted}"


# ---------------------------------------------------------------------------
# Reading a table: strict JSON, then the shape every packaged table has
# ---------------------------------------------------------------------------
class _Repeated(dict[str, Any]):
    """An object whose text names one member twice, with the names it repeats.

    JSON keeps the last of two members with one name and says nothing, so a
    row that typed a density twice would publish whichever came second. The
    reader marks the object instead of refusing on the spot, because at that
    point it does not yet know which row the object belongs to.
    """

    repeated: tuple[str, ...] = ()


class _Constant:
    """A ``NaN`` or an infinity in the text, kept only long enough to be found."""

    __slots__ = ("token",)

    def __init__(self, token: str) -> None:
        self.token = token


def _flaws(node: object, path: str, root: str) -> Iterator[str]:
    """What is wrong with *node* and everything under it, each with its path.

    :param node: A decoded value.
    :param path: Where *node* sits under the object the walk started from,
        empty for that object itself.
    :param root: What that object is called in a message, for a flaw at its
        own level: ``"the row"`` or ``"the document"``.
    """
    if isinstance(node, _Constant):
        yield (
            f"{path} is {node.token}, which is not JSON and not a number any "
            "page prints"
        )
    elif isinstance(node, dict):
        if isinstance(node, _Repeated):
            names = ", ".join(repr(name) for name in node.repeated)
            yield f"{path or root} names {names} twice, and JSON keeps only the last"
        for key, value in node.items():
            yield from _flaws(value, f"{path}.{key}" if path else key, root)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _flaws(value, f"{path}[{index}]", root)


def _refuse_flaws(document: object, label: str) -> NoReturn:
    """Refuse a document that holds a marked flaw, naming the row it sits in."""
    rows = document.get("rows") if isinstance(document, dict) else None
    for row in rows if isinstance(rows, list) else ():
        for flaw in _flaws(row, "", "the row"):
            key = row.get("key") if isinstance(row, dict) else None
            _reject(label, f"row {key!r}: {flaw}")
    for flaw in _flaws(document, "", "the document"):
        _reject(label, flaw)
    _reject(label, "the text holds something JSON does not")  # pragma: no cover


def decode_marked(text: str, *, figures: bool) -> tuple[object, bool]:
    """The document *text* holds, with what JSON does not have marked.

    CPython's reader accepts a ``NaN`` and an infinity, which JSON does not
    have, and keeps the last of two members that share a name. Here each
    becomes a marker the caller finds by walking the document: a
    :class:`_Constant` in place of the token, and a :class:`_Repeated` for
    the object that repeats a name. A reader of a packaged table refuses on
    the first; a reader of a caller's file reports every one of them with
    where it is.

    :param text: The file's text.
    :param figures: Decode every number as a :class:`PrintedNumber`, which
        keeps the digits it was written with, instead of as a float or an
        integer.
    :return: The decoded document, and whether any marker was placed.
    :raises json.JSONDecodeError: for text that is not JSON.
    :raises RecursionError: for text nested past what the decoder follows.
    """
    flagged: list[object] = []

    def members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        obj = dict(pairs)
        if len(obj) == len(pairs):
            return obj
        seen: set[str] = set()
        twice: dict[str, None] = {}
        for name, _ in pairs:
            if name in seen:
                twice[name] = None
            seen.add(name)
        marked = _Repeated(obj)
        marked.repeated = tuple(twice)
        flagged.append(marked)
        return marked

    def constant(token: str) -> _Constant:
        marked = _Constant(token)
        flagged.append(marked)
        return marked

    number = PrintedNumber if figures else None
    document = json.loads(
        text,
        parse_constant=constant,
        object_pairs_hook=members,
        parse_float=number,
        parse_int=number,
    )
    return document, bool(flagged)


def _strict_json(text: str, label: str) -> object:
    """The document *text* holds, refusing what only CPython's reader accepts.

    :param text: The file's text.
    :param label: What names the file in a refusal.
    :return: The decoded document.
    :raises CatalogueError: for text that is not JSON, for a ``NaN`` or an
        infinity, and for a name written twice in one object.
    """
    try:
        document, flagged = decode_marked(text, figures=False)
    except json.JSONDecodeError as error:
        msg = f"{label}: this is not JSON ({error})"
        issue = CatalogueIssue(
            file=label,
            location=f"line {error.lineno}, column {error.colno}",
            message=f"this is not JSON ({error.msg})",
        )
        raise CatalogueError(msg, issues=(issue,)) from error
    if flagged:
        _refuse_flaws(document, label)
    return document


def _check_packaged_rows(rows: object, label: str) -> None:
    """The rows of a packaged table, each an object with a key of its own."""
    if not isinstance(rows, list) or not rows:
        _reject(label, "a published table with no rows publishes nothing")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            _reject(label, f"every row is a JSON object, and one is {row!r}")
        key = row.get("key")
        if key is None:
            _reject(label, "every row needs a key of its own")
        if not isinstance(key, str):
            _reject(label, f"the key {key!r} is not text")
        if "/" in key:
            _reject(
                label,
                f"row {key!r}: a row key holds no '/', which separates the table "
                "from the row in every catalogue's keys",
            )
        if key in seen:
            _reject(label, f"two rows share the key {key!r}")
        seen.add(key)


def parse_packaged(text: str, label: str) -> dict[str, Any]:
    """One packaged table from its text, checked before any row is built.

    The shared reader of the packaged data files: JSON as a browser reads it,
    with no ``NaN``, no infinity and no name written twice in one object;
    the three top-level keys every table needs, and nothing at the top level
    but those, the printed ``conventions`` and a fluid table's
    ``validity``; and rows that are objects, each with a key of its own that
    holds no ``/``. What a row's fields mean is left to the dataclass that
    holds it, because the loader chooses that and a fluid table has none.

    :param text: The file's text.
    :param label: What names the file in a refusal, its file name.
    :return: The decoded document.
    :raises CatalogueError: naming the file, and the row when there is one,
        for any of the above.
    """
    document = _strict_json(text, label)
    if not isinstance(document, dict):
        _reject(label, "a published table is one JSON object")
    for key in _REQUIRED:
        if key not in document:
            _reject(label, f"a published table needs a top-level {key!r}")
    for key in document:
        if key not in _PACKAGED_KEYS:
            allowed = ", ".join(repr(name) for name in sorted(_PACKAGED_KEYS))
            _reject(
                label,
                f"a published table has no top-level {key!r}; it holds {allowed}",
            )
    _check_packaged_rows(document["rows"], label)
    return document


def read_packaged(package: str, filename: str) -> dict[str, Any]:
    """The whole of one published table from a package's ``data`` directory.

    For a loader that needs more of the document than its rows, as the fluid
    tables need the ``validity`` they put on the whole table; the text goes
    through :func:`parse_packaged` like every other packaged table.

    :param package: The package that owns the data, as ``phonometry.solids``.
        The file is read from its ``data`` subpackage.
    :param filename: The file name inside ``data``, including the extension.
    :return: The decoded document.
    :raises CatalogueError: for anything :func:`parse_packaged` refuses.
    """
    from importlib.resources import files

    text = (files(f"{package}.data") / filename).read_text(encoding="utf-8")
    return parse_packaged(text, filename)


def read_table(package: str, filename: str) -> tuple[str, tuple[dict[str, Any], ...]]:
    """Read one published table from a package's ``data`` directory.

    :param package: The package that owns the data, as ``phonometry.solids``.
        The file is read from its ``data`` subpackage.
    :param filename: The file name inside ``data``, including the extension.
    :return: The citation every row of the file shares, and the rows in the
        order the file lists them, each a plain dictionary ready to be passed
        to the dataclass that holds it.
    :raises CatalogueError: for anything :func:`parse_packaged` refuses: a
        missing or unknown top-level key, no rows, two rows sharing a key, a
        ``/`` in a key, a ``NaN`` or a name written twice.
    """
    document = read_packaged(package, filename)
    return document["source"], tuple(document["rows"])


def take(row: Mapping[str, Any]) -> dict[str, Any]:
    """The row as constructor keywords: everything but the ``key``.

    Nothing is converted here. A data file writes a set of field names as a
    list and an interval as a two-item list, because JSON has neither sets
    nor tuples, and the row freezes each field into the type its annotation
    names when it is built.

    :param row: One row as :func:`read_table` returned it.
    :return: The remaining fields, ready to pass to
        :meth:`CatalogueRow.from_printed`.
    """
    return {name: value for name, value in row.items() if name != "key"}


# ---------------------------------------------------------------------------
# The row contract: what a row is checked for and frozen into when it is built
# ---------------------------------------------------------------------------
#: One field's check: it takes the value and where the value sits, for the
#: message, and returns the value as the row keeps it (frozen, for a set or a
#: mapping) or raises :class:`CatalogueError`.
type _Check = Callable[[object, str], object]

#: The two spellings of a union a resolved annotation can come back as.
_UNIONS = (typing.Union, types.UnionType)

#: The kinds of field that hold a number.
_NUMERIC = frozenset({"number", "whole"})

#: The one empty mapping every row holds for a hedge it does not use. Nothing
#: can reach the dict behind it, so sharing it is sharing nothing.
_NOTHING: Mapping[str, Any] = MappingProxyType({})

#: How much of a refused value a message quotes.
_QUOTED = 80

#: The words a hedge may use in place of a field name: the whole row, and,
#: for a credit, the whole table.
_ROW_WORDS: Mapping[str, frozenset[str]] = MappingProxyType(
    {"basis": frozenset({"row"}), "attributed_to": frozenset({"row", "table"})}
)

#: The hedges that say what a numeric cell holds instead of a value: a word,
#: why this library leaves it empty, several readings with no single one. A
#: value beside any of them would be served while the hedge says there is
#: none, and ``misprinted`` on a number says the same.
_HOLDS_NOTHING = ("unquantified", "not_derivable", "reported")

#: The unit suffixes of the quantities that cannot be negative: a density, a
#: mass per area, a mass, a molar mass, a speed, a pressure or modulus, a flow
#: resistivity, a specific flow resistance, a stiffness per area, a length in
#: millimetres, micrometres or metres, an area, a thickness-frequency product
#: and a count per centimetre. Named by the unit the field carries, which is a
#: physical limit and not a guard on how large a value may be. A refusal names
#: the suffix rather than a unit, because a field named for a compound unit
#: (``surface_density_g_m2``) ends in a shorter one (``_m2``) that is not its
#: own.
_NOT_NEGATIVE = (
    "_kg_m3",
    "_kg_m2",
    "_kg",
    "_kg_mol",
    "_m_s",
    "_pa",
    "_pa_s_m2",
    "_pa_s_m",
    "_n_m3",
    "_mm",
    "_um",
    "_m",
    "_m2",
    "_m_hz",
    "_per_cm",
)

#: The unit suffixes of quantities that can be negative, and which a shorter
#: suffix above would otherwise claim: a Celsius temperature, a decay rate
#: per metre (Attenborough's porosity profiles), and a level in decibels.
#: The longest suffix a field name ends in decides.
_SIGNED = ("_c", "_per_m", "_db")

#: The per-cent fields that are a share of a whole, and so run from 0 to 100.
#: Not every ``_percent``: a water content on a dry basis passes 100.
_SHARES = frozenset(
    {"shot_content_percent", "binder_content_percent", "adhered_area_percent"}
)


def _quote(value: object) -> str:
    """*value* as a message quotes it: its ``repr``, cut at a readable length."""
    text = repr(value)
    return text if len(text) <= _QUOTED else f"{text[: _QUOTED - 3]}..."


def _refuse(where: str, value: object, what: str) -> NoReturn:
    """Refuse *value* at *where* for not being *what* the field holds."""
    msg = f"{where} holds {_quote(value)}, which is not {what}"
    raise CatalogueError(msg)


def _text(value: object, where: str) -> object:
    if not isinstance(value, str):
        _refuse(where, value, "text")
    return value


def _flag(value: object, where: str) -> object:
    if not isinstance(value, bool):
        _refuse(where, value, "True or False")
    return value


def _whole(value: object, where: str) -> object:
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        _refuse(where, value, "a whole number")
    return value


#: What a numeric cell has to be, in the words every refusal of one uses.
_FINITE = "a finite number"


def _real(value: object, where: str) -> object:
    # ``float`` and ``int`` are what a data file holds, and checking them by
    # type first spares every packaged cell the slower abstract check.
    exact = type(value) is float or type(value) is int
    if not exact and (isinstance(value, bool) or not isinstance(value, numbers.Real)):
        _refuse(where, value, _FINITE)
    try:
        finite = math.isfinite(typing.cast("float", value))
    except OverflowError:
        finite = False
    if not finite:
        _refuse(where, value, _FINITE)
    return value


def _provenance(value: object, where: str) -> object:
    if not isinstance(value, Provenance):
        _refuse(where, value, "a Provenance")
    return value


def _names(value: object, where: str) -> frozenset[str]:
    if isinstance(value, frozenset) and all(type(item) is str for item in value):
        return value
    if isinstance(value, (list, tuple, AbstractSet)) and not isinstance(value, str):
        return frozenset(
            typing.cast("str", _text(item, f"{where}[{index}]"))
            for index, item in enumerate(value)
        )
    _refuse(where, value, "a set of field names")


def _optional(check: _Check) -> _Check:
    def optional(value: object, where: str) -> object:
        return None if value is None else check(value, where)

    return optional


def _fixed(checks: tuple[_Check, ...]) -> _Check:
    def fixed(value: object, where: str) -> object:
        if not isinstance(value, (list, tuple)) or len(value) != len(checks):
            _refuse(where, value, f"a list of {len(checks)}")
        return tuple(
            check(item, f"{where}[{index}]")
            for index, (check, item) in enumerate(zip(checks, value, strict=True))
        )

    return fixed


def _any_length(check: _Check) -> _Check:
    def any_length(value: object, where: str) -> object:
        if not isinstance(value, (list, tuple)):
            _refuse(where, value, "a list")
        return tuple(
            check(item, f"{where}[{index}]") for index, item in enumerate(value)
        )

    return any_length


def _either(scalar: _Check, sequence: _Check) -> _Check:
    def either(value: object, where: str) -> object:
        if isinstance(value, (list, tuple)):
            return sequence(value, where)
        return scalar(value, where)

    return either


def _mapping_of(check: _Check) -> _Check:
    def mapping(value: object, where: str) -> object:
        if type(value) is dict or type(value) is MappingProxyType:
            if not value:
                return _NOTHING
        elif not isinstance(value, Mapping):
            _refuse(where, value, "a mapping")
        return MappingProxyType(
            {
                _text(key, f"{where} key"): check(item, f"{where}[{key!r}]")
                for key, item in value.items()
            }
        )

    return mapping


def _leaf(hint: object) -> _Check | None:
    """The check for a plain value annotated *hint*, if it is one."""
    if hint is str:
        return _text
    if hint is bool:
        return _flag
    if hint is int:
        return _whole
    if hint is float:
        return _real
    return None


def _tuple_check(args: tuple[object, ...]) -> _Check | None:
    """The check for ``tuple[...]`` over *args*, fixed or of any length."""
    if args[1:] == (Ellipsis,):
        item = _value_check(args[0])
        return None if item is None else _any_length(item)
    items = tuple(_value_check(arg) for arg in args)
    if not items or any(item is None for item in items):
        return None
    return _fixed(typing.cast("tuple[_Check, ...]", items))


def _union_check(args: tuple[object, ...]) -> _Check | None:
    """The check for a union: at most one plain value and one tuple, or None."""
    members = [arg for arg in args if arg is not type(None)]
    sequences = [arg for arg in members if typing.get_origin(arg) is tuple]
    scalars = [arg for arg in members if typing.get_origin(arg) is not tuple]
    if len(sequences) > 1 or len(scalars) > 1:
        return None
    scalar = _leaf(scalars[0]) if scalars else None
    sequence = _tuple_check(typing.get_args(sequences[0])) if sequences else None
    if (scalars and scalar is None) or (sequences and sequence is None):
        return None
    if scalar is not None and sequence is not None:
        check = _either(scalar, sequence)
    else:
        check = typing.cast("_Check", scalar or sequence)
    return _optional(check) if len(members) < len(args) else check


def _value_check(hint: object) -> _Check | None:
    """The check for a value held inside a mapping or a tuple."""
    leaf = _leaf(hint)
    if leaf is not None:
        return leaf
    origin = typing.get_origin(hint)
    if origin is tuple:
        return _tuple_check(typing.get_args(hint))
    if origin in _UNIONS:
        return _union_check(typing.get_args(hint))
    return None


def _field_check(hint: object) -> tuple[str, _Check] | None:
    """What kind of field *hint* annotates, and the check its value gets.

    The kinds are ``"number"`` (``float | None``), ``"whole"``
    (``int | None``), ``"flag"`` (``bool``), ``"text"`` (``str``), ``"set"``
    (``frozenset[str]``), ``"mapping"`` (``Mapping[str, ...]`` of plain
    values and tuples of them) and ``"provenance"`` (``Provenance | None``).
    ``Optional[float]`` is ``float | None``, and on Python 3.14 the same
    object. Anything else answers ``None``, a bare ``float`` or ``int``
    included: every quantity of a row may be missing, because the pages
    print different columns, and a row that could not say so would have no
    answer for :meth:`CatalogueRow.why_missing` to give.
    """
    if hint is bool:
        return "flag", _flag
    if hint is str:
        return "text", _text
    origin, args = typing.get_origin(hint), typing.get_args(hint)
    if origin in _UNIONS and set(args) == {Provenance, type(None)}:
        return "provenance", _optional(_provenance)
    if origin is frozenset and args == (str,):
        return "set", _names
    if origin is Mapping and args[:1] == (str,):
        check = _value_check(args[-1])
        return None if check is None else ("mapping", _mapping_of(check))
    if origin not in _UNIONS or type(None) not in args:
        return None
    members = {arg for arg in args if arg is not type(None)}
    for kind, plain, leaf in (("number", float, _real), ("whole", int, _whole)):
        if members == {plain}:
            return kind, _optional(leaf)
    return None


def _limit(field_name: str) -> tuple[float, float | None, str] | None:
    """The physical bounds of a numeric field, from its name, if it has any."""
    if field_name == "porosity":
        return 0.0, 1.0, "a porosity is a fraction from 0 to 1"
    if field_name in _SHARES:
        return 0.0, 100.0, "a share of a whole runs from 0 to 100 per cent"
    suffix = max(
        (s for s in (*_NOT_NEGATIVE, *_SIGNED) if field_name.endswith(s)),
        key=len,
        default="",
    )
    if suffix in _NOT_NEGATIVE:
        return 0.0, None, f"a quantity whose name ends in {suffix} is never negative"
    return None


class _Shape(NamedTuple):
    """What the contract needs to know about one row class, worked out once."""

    #: Every field in declaration order, with the check its value gets.
    checks: tuple[tuple[str, _Check], ...]
    #: The fields that hold a number, an ``int`` included.
    numeric: frozenset[str]
    #: The fields that hold a value of any kind: numbers, flags and text.
    values: frozenset[str]
    #: What a hedge that may name text may name: the numbers and the text
    #: fields, but not the citation or the table the row was read from, which
    #: are not cells of the page.
    cells: frozenset[str]
    #: The fields that hold text.
    texts: frozenset[str]
    #: ``(field, low, high, why)`` for each numeric field with a physical limit.
    limits: tuple[tuple[str, float, float | None, str], ...]
    #: Every other name a numeric field is taken under, in another unit.
    spellings: _Spellings
    #: The hedges of the class, whose keys may name a field in another unit.
    hedges: frozenset[str]
    #: Every field by the kind the contract gives it: ``"number"``,
    #: ``"whole"``, ``"flag"``, ``"text"``, ``"set"``, ``"mapping"`` or
    #: ``"provenance"``.
    kinds: Mapping[str, str]


#: The shape of every row class built so far. Weakly keyed, so a caller's
#: subclass is not kept alive by having been built once.
_SHAPES: weakref.WeakKeyDictionary[type, _Shape] = weakref.WeakKeyDictionary()


def _shape(cls: type) -> _Shape:
    """The shape of *cls*, classified the first time a row of it is built.

    The classification is cached per class, which is what keeps the check of
    the packaged rows at import to a single pass over their values.
    """
    shape = _SHAPES.get(cls)
    if shape is None:
        shape = _SHAPES[cls] = _classify(cls)
    return shape


def _classify(cls: type) -> _Shape:
    """Classify every field of *cls* from its resolved annotations.

    ``typing.get_type_hints`` resolves each annotation in the module that
    wrote it, and the catalogue modules import ``Mapping`` for the type
    checker only, so it is supplied here.

    :raises TypeError: for an annotation that does not resolve, or that no
        check exists for, naming the class and the field: a field the
        contract cannot classify would reach every caller unchecked.
    """
    try:
        hints = typing.get_type_hints(cls, localns={"Mapping": Mapping})
    except (NameError, SyntaxError, TypeError) as error:
        msg = (
            f"{cls.__qualname__}: an annotation does not resolve ({error}); a "
            "catalogue row's annotations have to resolve at run time"
        )
        raise TypeError(msg) from error
    checks: list[tuple[str, _Check]] = []
    kinds: dict[str, str] = {}
    for item in fields(cls):
        classified = _field_check(hints[item.name])
        if classified is None:
            msg = (
                f"{cls.__qualname__}.{item.name} is annotated "
                f"{hints[item.name]!r}, which a catalogue row cannot check: a "
                "field is float | None, int | None, bool, str, frozenset[str] "
                "or a Mapping[str, ...] of those, and a quantity is never a "
                "bare float or int, because every cell of a row may be missing"
            )
            raise TypeError(msg)
        kinds[item.name], check = classified
        checks.append((item.name, check))
    numeric = frozenset(name for name, kind in kinds.items() if kind in _NUMERIC)
    texts = frozenset(name for name, kind in kinds.items() if kind == "text")
    flags = frozenset(name for name, kind in kinds.items() if kind == "flag")
    limits = tuple(
        (name, *bounds) for name in sorted(numeric) if (bounds := _limit(name))
    )
    values = numeric | texts | flags
    cells = (numeric | texts) - {"source", "table"}
    return _Shape(
        tuple(checks),
        numeric,
        values,
        cells,
        texts,
        limits,
        _spellings(cls, numeric),
        frozenset((*cls._number_hedges, *cls._value_hedges)),  # type: ignore[attr-defined]
        MappingProxyType(kinds),
    )


# ---------------------------------------------------------------------------
# Building a row from the cells a page prints: a figure in another unit
# converted exactly, and what follows from the cells worked out and marked
# ---------------------------------------------------------------------------
class UnitAlias(NamedTuple):
    """A unit a page prints a field in that is not the one the row holds.

    A table set in feet prints an absorption area in square feet, and the row
    holds square metres, because a field named ``_m2`` holds square metres or
    it lies. The cells name the page's figure after the field, with this
    suffix in place of the row's own (``absorption_area_125_ft2`` for
    ``absorption_area_125_m2``), and :meth:`CatalogueRow.from_printed`
    converts it and records the figure and its unit in
    :attr:`CatalogueRow.converted`. A row class lists the aliases only it
    takes in its ``_unit_aliases``; the ones every row takes, another unit
    of the same kind as the one a field is named for, come from the unit
    families of this module.
    """

    #: The suffix the figure is written under, as ``"_ft2"``.
    suffix: str
    #: The suffix of the field that holds the value, as ``"_m2"``.
    target: str
    #: One of the page's unit in the row's, exactly.
    factor: Fraction
    #: The unit as :attr:`CatalogueRow.converted` records it beside the
    #: figure, as ``"sabins"``.
    unit: str
    #: Text fields the row has to fill for the figure to mean anything: an
    #: area per unit of volume says what it is per in ``per``, whose default
    #: is a person.
    requires: tuple[str, ...] = ()
    #: What the page's zero is in the row's unit, added after the factor: a
    #: temperature in kelvin is one in degrees Celsius less 273.15. Zero for
    #: every unit that shares its zero with the row's. A difference, such as
    #: a plus-or-minus, takes the factor alone.
    offset: Fraction = Fraction(0)


class _Unit(NamedTuple):
    """One unit of a family, as a figure written in it is converted."""

    #: The kind of quantity: a figure converts only within its family.
    family: str
    #: One of this unit in the family's first unit, exactly.
    factor: Fraction
    #: How :attr:`CatalogueRow.converted` records the unit beside a figure.
    spelling: str
    #: The family's first unit at this unit's zero.
    offset: Fraction = Fraction(0)


def _power(exponent: int) -> Fraction:
    """Ten to *exponent*, exactly."""
    return Fraction(10) ** exponent


#: The units a catalogue file may write a field in besides the one the field
#: is named for, by the suffix a field name ends in. A figure converts only
#: to a field of the same family with the same root: ``thickness_m`` fills
#: ``thickness_mm``, ``viscous_length_mm`` fills ``viscous_length_um``, and
#: ``surface_density_kg_m2`` fills a resistive sheet's
#: ``surface_density_g_m2``. ``_mpa`` is megapascal, as the library already
#: spells it, and ``_n_mm2`` the spelling elastomer data sheets print for the
#: same unit.
_UNITS: Mapping[str, _Unit] = MappingProxyType(
    {
        "_um": _Unit("length", _power(-6), "µm"),
        "_mm": _Unit("length", _power(-3), "mm"),
        "_cm": _Unit("length", _power(-2), "cm"),
        "_m": _Unit("length", Fraction(1), "m"),
        "_g_m2": _Unit("mass per area", _power(-3), "g/m2"),
        "_kg_m2": _Unit("mass per area", Fraction(1), "kg/m2"),
        "_g_cm3": _Unit("density", _power(3), "g/cm3"),
        "_kg_m3": _Unit("density", Fraction(1), "kg/m3"),
        "_pa": _Unit("pressure", Fraction(1), "Pa"),
        "_kpa": _Unit("pressure", _power(3), "kPa"),
        "_mpa": _Unit("pressure", _power(6), "MPa"),
        "_n_mm2": _Unit("pressure", _power(6), "N/mm2"),
        "_gpa": _Unit("pressure", _power(9), "GPa"),
        "_n_m3": _Unit("stiffness per area", Fraction(1), "N/m3"),
        "_mn_m3": _Unit("stiffness per area", _power(6), "MN/m3"),
        "_pa_s_m2": _Unit("flow resistivity", Fraction(1), "Pa s/m2"),
        "_kpa_s_m2": _Unit("flow resistivity", _power(3), "kPa s/m2"),
        "_c": _Unit("temperature", Fraction(1), "°C"),
        "_k": _Unit("temperature", Fraction(1), "K", Fraction(-27315, 100)),
    }
)

#: The units the library's fields are named in that belong to no family and
#: end in the suffix of one. The suffix of a name is its longest match
#: against every unit, so these are found before the shorter one inside them:
#: a specific flow resistance in Pa s/m does not end in metres, a decay rate
#: per metre is not a length, and a count per centimetre is not one either.
#: Without them ``specific_flow_resistance_pa_s_mm`` would read as a root
#: ``specific_flow_resistance_pa_s`` in millimetres and be divided by a
#: thousand, and a rate per millimetre would be scaled the wrong way.
_COMPOUND_UNITS = ("_pa_s_m", "_per_m", "_per_cm", "_m_s", "_m_hz")

#: The words a unit is spelled with in a name, and the word of a rate. A
#: field of a caller's own class whose root holds one is in a compound unit:
#: ``dynamic_stiffness_n_m`` is in N/m and ``thermal_conductivity_w_m_k`` in
#: W/(m K), and the family of their last word is not their unit. A written
#: name that ends in them is a name in some unit, which a refusal says.
_UNIT_WORDS = frozenset(
    {
        # length, area and volume
        *("um", "mm", "cm", "dm", "m", "km", "in", "inch", "inches", "ft"),
        *("feet", "yd", "mil", "m2", "m3", "mm2", "mm3", "cm2", "cm3"),
        *("ft2", "ft3", "in2", "in3"),
        # mass and amount
        *("mg", "g", "kg", "t", "lb", "lbs", "oz", "mol"),
        # time and frequency
        *("s", "ms", "min", "h", "hz", "khz"),
        # force, pressure, energy and power
        *("n", "kn", "mn", "kgf", "lbf", "pa", "kpa", "mpa", "gpa", "hpa"),
        *("bar", "mbar", "psi", "psf", "atm", "j", "kj", "w", "kw"),
        # temperature, angle, level and ratio
        *("k", "c", "f", "degc", "degf", "deg", "rad", "db", "percent", "pct"),
        # the units of airflow and absorption, and the word of a rate
        *("rayl", "rayls", "sabin", "sabins", "per"),
    }
)

#: How the unit of a field that a class's own aliases fill is spelled beside
#: a figure, for a unit no family holds.
_TARGET_SPELLINGS: Mapping[str, str] = MappingProxyType({"_m2": "m2"})


def unit_suffix(name: str, extra: tuple[str, ...] = ()) -> str:
    """The unit a field name ends in, by the longest match, or ``""``.

    :param name: A field name, or a name a catalogue file writes.
    :param extra: Suffixes a row class adds to the families, from its own
        ``_unit_aliases``.
    :return: The suffix, with its leading underscore, or the empty string
        for a name that ends in none of them.
    """
    return max(
        (
            suffix
            for suffix in chain(_UNITS, _COMPOUND_UNITS, extra)
            if name.endswith(suffix) and len(name) > len(suffix)
        ),
        key=len,
        default="",
    )


def unit_stem(name: str) -> str:
    """*name* without the words of the unit it ends in, or ``""``.

    ``thickness_mm`` gives ``thickness`` and ``dynamic_stiffness_n_m3``
    gives ``dynamic_stiffness``; a name that ends in no unit word, or is
    nothing else, gives the empty string.
    """
    words = name.split("_")
    end = len(words)
    while end > 1 and words[end - 1] in _UNIT_WORDS:
        end -= 1
    return "_".join(words[:end]) if end < len(words) else ""


def is_unit_spelling(text: str) -> bool:
    """Whether every word of *text* is one a unit is spelled with."""
    return bool(text) and all(word in _UNIT_WORDS for word in text.split("_"))


def _introduced_by(cls: type, name: str) -> type | None:
    """The class of *cls*'s hierarchy that first declares the field *name*."""
    for klass in reversed(cls.__mro__):
        if name in vars(klass).get("__dataclass_fields__", {}):
            return klass
    return None


def _takes_family_units(cls: type, name: str, root: str, unit: _Unit) -> bool:
    """Whether the field *name* of *cls* takes the other units of its family.

    Every field a class of this library declares was read for the unit its
    name carries, and a test lists them family by family. A field of a
    caller's own class takes them only when its name leaves no doubt: a
    root with no unit and no rate in it, and never a temperature, whose name
    cannot say whether it is a temperature or a difference of two, which
    moves by the factor alone.
    """
    introduced = _introduced_by(cls, name)
    if introduced is not None and introduced.__module__.startswith("phonometry."):
        return True
    return unit.family != "temperature" and not any(
        word in _UNIT_WORDS for word in root.split("_")
    )


class _Spellings(NamedTuple):
    """Every other name a row class takes a numeric field under."""

    #: Written name to the field it fills and the alias that converts it.
    aliases: Mapping[str, tuple[str, UnitAlias]]
    #: Written names two fields of one family and root could both take, to
    #: the fields: refused, because the name does not say which.
    ambiguous: Mapping[str, tuple[str, ...]]
    #: Every name in either, for the one look a row without them takes.
    written: frozenset[str]
    #: Field to how its own unit is spelled beside a figure, for every field
    #: that takes another unit.
    units: Mapping[str, str]


def _family_aliases(
    cls: type, numeric: frozenset[str], extra: tuple[str, ...], units: dict[str, str]
) -> dict[str, list[tuple[str, UnitAlias]]]:
    """Every written name the unit families give the numeric fields.

    Records in *units* how the unit of each field they apply to is spelled.
    """
    members: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for name in sorted(numeric):
        suffix = unit_suffix(name, extra)
        unit = _UNITS.get(suffix)
        if unit is None:
            continue
        root = name.removesuffix(suffix)
        if _takes_family_units(cls, name, root, unit):
            members.setdefault((root, unit.family), []).append((name, suffix))
            units[name] = unit.spelling
    found: dict[str, list[tuple[str, UnitAlias]]] = {}
    for (root, family), group in members.items():
        for written_suffix, written in _UNITS.items():
            if written.family != family:
                continue
            for name, suffix in group:
                own = _UNITS[suffix]
                alias = UnitAlias(
                    written_suffix,
                    suffix,
                    written.factor / own.factor,
                    written.spelling,
                    offset=(written.offset - own.offset) / own.factor,
                )
                found.setdefault(f"{root}{written_suffix}", []).append((name, alias))
    return found


def _spellings(cls: type, numeric: frozenset[str]) -> _Spellings:
    """The written names a row class takes besides its field names.

    A name that is a field of the class is never converted, a name two
    fields could take is ambiguous, and a class's own ``_unit_aliases``
    (the sabins of a table set in feet) join the families for the fields
    that class and its bases declare, not for a field a subclass adds.
    """
    own: tuple[UnitAlias, ...] = getattr(cls, "_unit_aliases", ())
    extra = tuple(chain.from_iterable((alias.suffix, alias.target) for alias in own))
    units: dict[str, str] = {}
    found = _family_aliases(cls, numeric, extra, units)
    owner = next(
        (klass for klass in cls.__mro__ if "_unit_aliases" in vars(klass)), cls
    )
    for alias in own:
        for name in numeric:
            introduced = _introduced_by(cls, name)
            if unit_suffix(name, extra) == alias.target and (
                introduced is not None and issubclass(owner, introduced)
            ):
                written = f"{name.removesuffix(alias.target)}{alias.suffix}"
                found.setdefault(written, []).append((name, alias))
                units.setdefault(name, _TARGET_SPELLINGS.get(alias.target, ""))
    names = frozenset(item.name for item in fields(cls))
    aliases = {
        written: targets[0]
        for written, targets in found.items()
        if written not in names and len(targets) == 1
    }
    ambiguous = {
        written: tuple(name for name, _ in targets)
        for written, targets in found.items()
        if written not in names and len(targets) > 1
    }
    return _Spellings(
        MappingProxyType(aliases),
        MappingProxyType(ambiguous),
        frozenset(aliases) | frozenset(ambiguous),
        MappingProxyType(units),
    )


def spellings(cls: type[CatalogueRow]) -> _Spellings:
    """Every other name *cls* takes a numeric field under, worked out once."""
    return _shape(cls).spellings


def field_kinds(cls: type[CatalogueRow]) -> Mapping[str, str]:
    """Every field of *cls* by the kind the row contract gives it.

    :raises TypeError: for a field whose annotation the contract cannot
        classify, the first time the class is looked at.
    """
    return _shape(cls).kinds


def convert_figure(
    figure: str, factor: Fraction, offset: Fraction = Fraction(0)
) -> float:
    """The page's *figure* in the row's unit, rounded to a float once.

    The figure is read as the decimal it is, multiplied by the exact factor
    and moved by the exact offset, and only the result is rounded.
    Multiplying two floats rounds the figure, the factor and the product:
    11.5 sabins times the 0.09290304 m2 of a square foot comes out as
    1.0683849600000002 that way, where the product of the two decimals is
    1.06838496 exactly, and the float it rounds to here is the one ``repr``
    writes as 1.06838496.

    :param figure: The number as the page prints it, in digits: ``"11.5"``,
        ``"3e5"``.
    :param factor: One of the page's unit in the row's, exactly.
    :param offset: The page's zero in the row's unit, exactly; zero for a
        unit that shares its zero with the row's.
    :return: The float nearest the exact result.
    :raises OverflowError: for a result too large for a float.
    """
    return float(Fraction(figure) * factor + offset)


class PrintedNumber(Decimal):
    """A number as a catalogue file's text writes it, digits and all.

    A reader decodes every number of a file into one of these, so that a
    figure written in another unit is converted from the digits it was
    written with, trailing zeros and exponent included, and
    :attr:`CatalogueRow.converted` records them as they were written.
    """

    __slots__ = ("text",)

    text: str

    def __new__(cls, text: str) -> Self:
        """The number *text* writes, keeping *text*."""
        number = super().__new__(cls, text)
        number.text = text
        return number


def _figure(value: object, where: str) -> str:
    """The digits of a figure a cell holds, for :func:`convert_figure`.

    A float is written by its shortest ``repr``, the fewest digits that
    read back as the same number. Those are the page's digits unless the
    text wrote trailing zeros or an exponent (``"11.50"`` comes back as
    ``11.5``, ``"3e5"`` as ``300000.0``). A :class:`~decimal.Decimal` keeps
    the digits it was read with, trailing zeros included, and a
    :class:`PrintedNumber` the very text it was read from, so a reader that
    must record the figure as printed passes one.

    :raises CatalogueError: for a value that is not a finite number.
    """
    if isinstance(value, Decimal):
        if not value.is_finite():
            _refuse(where, value, _FINITE)
        return value.text if isinstance(value, PrintedNumber) else str(value)
    _real(value, where)
    if isinstance(value, numbers.Integral):
        return str(int(value))
    return repr(float(typing.cast("float", value)))


#: The two ends of an interval.
_PAIR = 2

#: The hedges whose entries are numbers of the cell they are keyed by, and
#: so are converted with it: the ends of a range, the readings of a list and
#: a plus-or-minus, which is a difference and takes the factor alone.
_NUMBER_HEDGES = ("ranges", "reported", "uncertainty")


def _names_an_alias(
    cells: Mapping[str, Any], hedges: frozenset[str], names: _Spellings
) -> bool:
    """Whether any cell or any hedge key is written under another name.

    Every packaged row is built through here and almost none writes another
    unit, so the answer is sought with set operations before any loop.
    """
    wanted = names.written
    if not wanted:
        return False
    if not wanted.isdisjoint(cells):
        return True
    for hedge in hedges.intersection(cells):
        held = cells[hedge]
        if (
            held
            and isinstance(held, (Mapping, list, tuple, AbstractSet))
            and any(isinstance(key, str) and key in wanted for key in held)
        ):
            return True
    return False


class _Resolution:
    """One row's cells with every name written in another unit resolved.

    A figure is a value, an end of a range, one of several readings or a
    plus-or-minus, and a unit is allowed wherever the field is named: as a
    cell and as the key of a hedge. Every number of one cell is written in
    one unit, so that :attr:`CatalogueRow.converted` can say which figure
    the page printed; the words of a hedge (a bound, a basis, a credit) may
    name the cell either way.
    """

    def __init__(
        self, cls: type[CatalogueRow], cells: Mapping[str, Any], names: _Spellings
    ) -> None:
        self._cls = cls
        self._cells = cells
        self._names = names
        self._label = repr(cells.get("name"))
        self._fields = frozenset(item.name for item in fields(cls))
        self._numeric = _shape(cls).numeric
        self._resolved = dict(cells)
        self._given = self._renamed_mapping("converted", cells.get("converted") or {})
        self._converted: dict[str, tuple[str, str]] = dict(self._given)
        #: Field to the name its numbers are written under, and the alias.
        self._spoken: dict[str, tuple[str, UnitAlias | None]] = {}
        #: Field to the alias figure of its value, of its range, of its list.
        self._figures: dict[str, dict[str, str]] = {}
        #: Field to the name its value was given under, for "given twice".
        self._claimed: dict[str, str] = {}

    def run(self) -> dict[str, Any]:
        """The resolved cells, ready for the constructor."""
        hedges = (*self._cls._number_hedges, *self._cls._value_hedges)
        for hedge in hedges:
            if hedge in self._cells and hedge != "converted":
                self._resolved[hedge] = self._rename(hedge, self._cells[hedge])
        self._resolve_values()
        self._record()
        if self._converted:
            self._resolved["converted"] = self._converted
        return self._resolved

    # -- names ---------------------------------------------------------------
    def _fail(self, what: str, field_name: str = "") -> NoReturn:
        msg = f"{self._label}: {what}"
        raise CatalogueError(msg, field=field_name)

    def _target(self, written: str) -> tuple[str, UnitAlias | None]:
        """The field *written* names, and the alias it is written under."""
        if written in self._fields:
            return written, None
        choices = self._names.ambiguous.get(written)
        if choices is not None:
            self._fail(
                f"{written} could be {_joined(list(choices))}, which share a root "
                "and a kind of unit; write the field's own name"
            )
        found = self._names.aliases.get(written)
        if found is None:
            return written, None
        return found

    def _rename(self, hedge: str, held: object) -> object:
        """A hedge with its keys named by field, its numbers converted."""
        if isinstance(held, Mapping):
            return self._renamed_mapping(hedge, held)
        if isinstance(held, (list, tuple, AbstractSet)) and not isinstance(held, str):
            renamed: list[object] = []
            for written in held:
                target = (
                    self._target(written)[0] if isinstance(written, str) else written
                )
                if target in renamed:
                    self._fail(f"{hedge} names {target} twice, under two units", target)
                renamed.append(target)
            return renamed
        return held

    def _renamed_mapping(self, hedge: str, held: Mapping[Any, Any]) -> dict[Any, Any]:
        renamed: dict[Any, Any] = {}
        where: dict[Any, str] = {}
        for written, entry in held.items():
            target, alias = (
                self._target(written) if isinstance(written, str) else (written, None)
            )
            if target in renamed:
                self._fail(
                    f"{hedge} gives {target} twice, as {where[target]} and as {written}",
                    target,
                )
            where[target] = written
            if hedge in _NUMBER_HEDGES:
                entry = self._numbers(hedge, written, target, alias, entry)
            renamed[target] = entry
        return renamed

    # -- numbers -------------------------------------------------------------
    def _speak(self, target: str, written: str, alias: UnitAlias | None) -> None:
        """Hold every number of *target* to one unit."""
        before = self._spoken.setdefault(target, (written, alias))
        if before[1] != alias:
            self._fail(
                f"the numbers of {target} are written as {before[0]} and as "
                f"{written}; write every number of one cell in one unit",
                target,
            )

    def _convert(
        self, value: object, alias: UnitAlias, where: str, *, difference: bool = False
    ) -> tuple[float, str]:
        """One figure in the row's unit, and its digits."""
        try:
            figure = _figure(value, where)
        except CatalogueError as error:
            self._fail(str(error))
        offset = Fraction(0) if difference else alias.offset
        try:
            return convert_figure(figure, alias.factor, offset), figure
        except OverflowError:
            self._fail(f"{where} holds {figure}, which is too large to convert")

    def _numbers(
        self,
        hedge: str,
        written: str,
        target: str,
        alias: UnitAlias | None,
        entry: object,
    ) -> object:
        """The numbers of a range, a list or a plus-or-minus, converted."""
        if alias is None:
            if entry is not None:
                self._speak(target, written, None)
            return entry
        self._speak(target, written, alias)
        where = f"{hedge}[{written!r}]"
        if hedge == "uncertainty":
            return self._convert(entry, alias, where, difference=True)[0]
        if hedge == "ranges":
            return self._range(entry, alias, where, target)
        return self._readings(entry, alias, where, target)

    def _range(
        self, entry: object, alias: UnitAlias, where: str, target: str
    ) -> tuple[float | None, float | None]:
        if not isinstance(entry, (list, tuple)) or len(entry) != _PAIR:
            self._fail(f"{where} holds {_quote(entry)}, which is not a list of 2")
        ends: list[float | None] = []
        digits: list[str | None] = []
        for index, end in enumerate(entry):
            if end is None:
                ends.append(None)
                digits.append(None)
            else:
                value, figure = self._convert(end, alias, f"{where}[{index}]")
                ends.append(value)
                digits.append(figure)
        self._figures.setdefault(target, {})["range"] = "|".join(
            figure or "" for figure in digits
        )
        return ends[0], ends[1]

    def _readings(
        self, entry: object, alias: UnitAlias, where: str, target: str
    ) -> tuple[float | tuple[float, float], ...]:
        if not isinstance(entry, (list, tuple)):
            self._fail(f"{where} holds {_quote(entry)}, which is not a list")
        readings: list[float | tuple[float, float]] = []
        spoken: list[str] = []
        for index, reading in enumerate(entry):
            at = f"{where}[{index}]"
            if isinstance(reading, (list, tuple)):
                if len(reading) != _PAIR:
                    self._fail(
                        f"{at} holds {_quote(reading)}, which is not a list of 2"
                    )
                low, low_figure = self._convert(reading[0], alias, f"{at}[0]")
                high, high_figure = self._convert(reading[1], alias, f"{at}[1]")
                readings.append((low, high))
                spoken.append(f"{low_figure} to {high_figure}")
            else:
                value, figure = self._convert(reading, alias, at)
                readings.append(value)
                spoken.append(figure)
        self._figures.setdefault(target, {})["list"] = ", ".join(spoken)
        return tuple(readings)

    def _resolve_values(self) -> None:
        """Every value written under another name, converted into its field."""
        for written, value in self._cells.items():
            if written in self._fields:
                if value is not None and written in self._numeric:
                    self._speak(written, written, None)
                continue
            target, alias = self._target(written)
            if alias is None:
                continue
            if (
                target in self._cells
                or target in self._given
                or target in self._claimed
            ):
                other = self._claimed.get(target, target)
                self._fail(f"{written} and {other} are one cell, given twice", target)
            self._claimed[target] = written
            del self._resolved[written]
            if value is None:
                continue
            self._speak(target, written, alias)
            number, figure = self._convert(value, alias, written)
            self._resolved[target] = number
            self._figures.setdefault(target, {})["value"] = figure

    def _record(self) -> None:
        """Record the page's figure and unit of every cell written in another."""
        for target, (written, alias) in self._spoken.items():
            if alias is None:
                continue
            if target in self._given:
                self._fail(
                    f"converted is given for {target}, whose figure is also written "
                    f"as {written}; write the figure under {written}, or the value "
                    "in the field's own unit with converted beside it, not both",
                    target,
                )
            missing = next(
                (need for need in alias.requires if not self._cells.get(need)), None
            )
            if missing is not None:
                self._fail(
                    f"a figure in {alias.unit} ({written}) needs {missing} written "
                    "beside it, to say what it is of",
                    target,
                )
            figure = self._spoken_figure(target)
            if not figure:
                self._fail(
                    f"{written} gives a plus-or-minus in {alias.unit} and no value, "
                    "range or list for it to go with",
                    target,
                )
            self._converted[target] = (figure, alias.unit)

    def _spoken_figure(self, target: str) -> str:
        """The figure the page prints for a cell: its value, its range or its list."""
        figures = self._figures.get(target, {})
        if "value" in figures:
            return figures["value"]
        if "range" in figures:
            low, high = figures["range"].split("|")
            bounds = self._resolved.get("bounded_above") or ()
            if target in bounds and high:
                return high
            if target in (self._resolved.get("bounded_below") or ()) and low:
                return low
            return f"{low} to {high}" if low and high else low or high
        return figures.get("list", "")


def _resolve_units(cls: type[CatalogueRow], cells: dict[str, Any]) -> dict[str, Any]:
    """*cells* with every figure written under a unit alias converted.

    A figure is converted wherever the field is named: as a value, and as
    the key of a hedge, whose numbers (the ends of a range, the readings of
    a list, a plus-or-minus) are converted with it. A name that is neither a
    field nor an alias of one is left for the constructor, which refuses it
    as the unknown keyword it is.

    :raises CatalogueError: naming the row and the cell, for a figure that
        is not a finite number, for a cell given both under its own name and
        under an alias, for the numbers of one cell written in two units,
        for a name two fields could take, and for an alias whose figure
        needs a text field the row leaves empty.
    """
    shape = _shape(cls)
    if not _names_an_alias(cells, shape.hedges, shape.spellings):
        return cells
    return _Resolution(cls, cells, shape.spellings).run()


def _joined(items: Sequence[str]) -> str:
    """``a``, ``a and b`` or ``a, b and c``, for a list that is not empty."""
    *head, last = items
    return f"{', '.join(head)} and {last}" if head else last


def _bases_named(words: Sequence[str], bases: Sequence[str]) -> str:
    """Which basis each printed cell a derived value rests on has.

    Written only when they are not all one, so that a modulus worked out
    from a speed and a density the source gives as they are and a Poisson
    ratio it marks as an estimate does not read as a figure of one kind.
    Each cell is named in *words*, as the rest of the text names it.
    """
    pairs = list(zip(words, bases, strict=True))
    stated = [f"{cell} ({basis})" for cell, basis in pairs if basis]
    unstated = [cell for cell, basis in pairs if not basis]
    text = f"it rests on {_joined(stated)}"
    if unstated:
        text += f" and on {_joined(unstated)}, whose basis the source does not state"
    return text


class Completion:
    """One row's cells as the completion of its class fills them in.

    :meth:`CatalogueRow.from_printed` builds the row from the printed cells
    first, so that every cell is checked before any arithmetic reads it,
    and then hands one of these to the class's ``_complete`` hook. The hook
    reads a cell with :meth:`get`, which sees what it has filled so far, and
    fills one with :meth:`fill`, naming the cells the value is worked out
    from. What it filled becomes the row's values, and how, its
    :attr:`~CatalogueRow.derived`.
    """

    __slots__ = ("_filled", "_how", "_inputs", "_row", "_said")

    def __init__(self, row: CatalogueRow) -> None:
        self._row = row
        self._said = frozenset(
            chain(
                row.ranges,
                row.reported,
                row.unquantified,
                row.not_derivable,
                row.misprinted,
            )
        )
        self._filled: dict[str, float] = {}
        self._how: dict[str, str] = {}
        self._inputs: dict[str, tuple[str, ...]] = {}

    def get(self, field_name: str) -> float | None:
        """A field's value, as the row holds it or as filled so far."""
        if field_name in self._filled:
            return self._filled[field_name]
        return typing.cast("float | None", getattr(self._row, field_name))

    def is_hedged(self, field_name: str) -> bool:
        """Whether the row says something about a field other than a value.

        A range, several readings, a word, a reason it is left empty, or a
        misprint: each is the page's answer for that cell, and none of them
        is a number arithmetic can take.
        """
        return field_name in self._said

    def fill(
        self,
        field_name: str,
        work: Callable[[], float],
        how: str,
        *,
        inputs: tuple[str, ...],
    ) -> None:
        """Hold what *work* gives in a cell the page leaves empty, and say how.

        Nothing is filled over a cell that holds a value, and nothing over a
        cell the row says something else about. Bies prints a modulus of 18
        to 30 GPa for normal concrete and a speed beside it, and a single
        modulus worked back out of that speed would sit next to the interval
        contradicting it. Bies leaves the speed of his aluminium honeycomb
        panels blank on purpose, and ``not_derivable`` says why; a word or a
        list the page printed has answered the cell already; and a value
        worked out around a misprint would put the book's mistake back into
        the arithmetic through the side door.

        *work* runs only for a cell that is filled. When the cells it reads
        are outside what its arithmetic takes (a Poisson ratio of 0.7 for
        the speed in an unbounded solid, or a modulus and a shear modulus
        that no isotropic solid has together), the row is refused rather
        than handed a value that would be wrong, and the refusal names the
        printed cells the value would have rested on. A row whose cells are
        not meant to give that value says so in ``not_derivable``, and then
        nothing is worked out.

        :param field_name: The field to fill.
        :param work: Works the value out from the cells of the row.
        :param how: The cells it comes from, in words, for
            :attr:`~CatalogueRow.derived`: ``"from the modulus and the
            density"``.
        :param inputs: The fields the value is worked out from, printed or
            filled, which is how :meth:`derived` finds the basis of every
            printed cell the value rests on.
        :raises CatalogueError: naming the row, the field and the printed
            cells with their values, when *work* refuses them with a
            ``ValueError`` or cannot divide by them.
        """
        if self.get(field_name) is not None or field_name in self._said:
            return
        try:
            value = work()
        except CatalogueError:
            raise
        except (ValueError, ArithmeticError) as error:
            printed = self._printed_under(inputs)
            cells = _joined([f"{cell} = {self.get(cell)!r}" for cell in printed])
            msg = (
                f"{self._row.name!r}: {field_name} cannot be worked out {how} "
                f"({cells}): {error}; a row whose cells are not meant to give "
                "it says why in not_derivable"
            )
            raise CatalogueError(msg) from error
        self._filled[field_name] = value
        self._how[field_name] = how
        self._inputs[field_name] = inputs

    def filled(self) -> dict[str, float]:
        """Every value filled, by field."""
        return dict(self._filled)

    def derived(self) -> dict[str, str]:
        """How each filled value was reached, naming the bases when they mix.

        The printed cells a value rests on are followed back through the
        filled ones, so a bar speed worked out from a modulus that was
        itself worked out from a Poisson ratio rests on that ratio. When
        their :meth:`~CatalogueRow.basis_of` is not one for all of them, a
        source not saying counting as an answer of its own, the text names
        the basis of each.
        """
        texts: dict[str, str] = {}
        for field_name, how in self._how.items():
            cells = self._rests_on(field_name)
            bases = [self._row.basis_of(cell) for cell in cells]
            if len(set(bases)) > 1:
                how = f"{how}; {_bases_named(self._words(cells), bases)}"
            texts[field_name] = how
        return texts

    def _words(self, cells: Sequence[str]) -> list[str]:
        """How the row's class names each of *cells* in a derived text.

        :raises CatalogueError: for a cell the class gives no words for, so
            that a field name never reaches a text written for a reader.
        """
        words = type(self._row)._cell_words
        missing = [cell for cell in cells if cell not in words]
        if missing:
            msg = (
                f"{type(self._row).__name__} names no words for {_joined(missing)} "
                "in _cell_words, and a derived text rests on them"
            )
            raise CatalogueError(msg)
        return [words[cell] for cell in cells]

    def _rests_on(self, field_name: str) -> tuple[str, ...]:
        """The printed cells a field rests on, following filled ones back."""
        inputs = self._inputs.get(field_name)
        if inputs is None:
            return (field_name,)
        return self._printed_under(inputs)

    def _printed_under(self, inputs: tuple[str, ...]) -> tuple[str, ...]:
        """The printed cells under *inputs*, following filled ones back."""
        return tuple(
            dict.fromkeys(cell for name in inputs for cell in self._rests_on(name))
        )


def _holds_nothing(value: object) -> bool:
    """Whether a field holds nothing: ``None``, no text, an empty hedge."""
    if value is None:
        return True
    if isinstance(value, (str, Mapping, AbstractSet, tuple)):
        return len(value) == 0
    return False


def _left_empty(item: dataclasses.Field[Any], value: object) -> bool:
    """Whether a field holds nothing, and nothing is also its default.

    Only such a field can be left out of the keywords that build the row
    again. A text field whose default says something, as the ``per`` of an
    area per unit says a person, holds an answer of its own when it holds no
    text, and building the row without it would put the default back.
    """
    if not _holds_nothing(value):
        return False
    if item.default is not dataclasses.MISSING:
        return bool(value == item.default)
    if item.default_factory is not dataclasses.MISSING:
        return bool(value == item.default_factory())
    return False


def _spell(entry: float | tuple[float, float], digits: str = "g") -> str:
    """One listed value or interval, the way the page would read it aloud."""
    if isinstance(entry, tuple):
        low, high = entry
        return f"{format(low, digits)} to {format(high, digits)}"
    return format(entry, digits)


@dataclass(frozen=True, kw_only=True)
class CatalogueRow:
    """One row of a published table, with what each cell said.

    The quantities are the subclass's business; this holds what surrounds
    them. A numeric field of the subclass is ``None`` whenever the page had
    something other than a single number there, and the hedges below say
    what: an interval in :attr:`ranges`, a list of values in
    :attr:`reported`, a word in :attr:`unquantified`. :meth:`why_missing`
    reads them back in the page's own terms, so a caller who gets ``None``
    is not left to guess whether the material has no such property, whether
    the book left the cell empty, or whether it printed three numbers.

    Every row of every published catalogue is one of these, a frozen and
    keyword-only dataclass. A subclass written to hold a quantity no
    catalogue of the library publishes is the same, and it leaves out
    ``slots=True``: on the Python 3.13 releases that predate the fix, a
    slotted dataclass that calls ``super()`` without arguments, as a
    ``__post_init__`` does, raises :class:`TypeError` when it is built.

    **A row checks itself when it is built**, whoever builds it, and refuses
    with :class:`CatalogueError` rather than holding a cell nothing
    downstream can read. The check is the same for a packaged row, a row a
    reader builds from a file and a row written by hand:

    1. :attr:`name` and :attr:`source` are text that is not empty, and so is
       every text a hedge holds: :meth:`why_missing` hands a
       :attr:`misprinted` or :attr:`not_derivable` text back as it is, and
       an empty one would answer as a cell that is not missing at all.
    2. A numeric field holds ``None`` or a finite number, never a ``bool``, a
       text or a ``NaN``; an ``int`` field a whole number; a ``bool`` field
       ``True`` or ``False``; a text field text.
    3. A set of field names (:attr:`approximate` and the bounds) is frozen
       into a ``frozenset``, whatever it was written as.
    4. Every mapping is frozen, all the way down: its pairs into tuples.
    5. Every key of a hedge names a numeric field of the row. :attr:`basis`
       and :attr:`attributed_to` also take the ``"row"``, and a credit the
       ``"table"``; :attr:`derived`, :attr:`carried` and :attr:`misprinted`
       may name a text field too (but not :attr:`source` or :attr:`table`,
       which are not cells of the page), because a page misprints a name or
       gives a description by reference to another row.
    6. :attr:`bounded_above` and :attr:`bounded_below` name only fields that
       have a range.
    7. A range's ends are finite, the low one no higher than the high one,
       and the end the page printed is there; an interval among the
       readings of :attr:`reported` runs from low to high as well.
    8. A list in :attr:`reported` holds at least one reading, and its
       readings are finite; an :attr:`uncertainty` is finite and not below
       zero.
    9. A field in :attr:`unquantified`, :attr:`not_derivable` or
       :attr:`reported`, or a numeric field in :attr:`misprinted`, holds no
       value; a field in :attr:`converted` or :attr:`carried` holds
       something: a value, a range or a list.
    10. :attr:`basis` holds only the words of :data:`CATALOGUE_BASES`.
    11. A quantity whose unit cannot be negative is not: a field ending in
        ``_kg_m3``, ``_kg_m2``, ``_kg``, ``_kg_mol``, ``_m_s``, ``_pa``,
        ``_pa_s_m2``, ``_pa_s_m``, ``_n_m3``, ``_mm``, ``_um``, ``_m``,
        ``_m2``, ``_m_hz`` or ``_per_cm``, in its value, its range and its
        readings. A ``porosity`` runs from 0 to 1, and the per-cent fields
        that are a share of a whole (``shot_content_percent``,
        ``binder_content_percent`` and ``adhered_area_percent``) from 0 to
        100.
        Nothing else is bounded: a Celsius temperature, a decay rate per
        metre and a level in decibels can be negative, and a size is never
        a reason to refuse a number.

    **Two ways to build a row.** ``Cls(...)`` is literal: the row holds what
    it is given, checked and frozen, and nothing is worked out.
    :meth:`from_printed` takes the cells the page prints, converts a figure
    written in a unit the class takes as an alias of its own, builds the
    row, fills what its class knows how to work out from those cells, and
    marks each filled value in :attr:`derived`. It is the one path that
    derives anything, and every packaged catalogue is built through it. To
    change a cell and have what follows from it follow again, change it in
    :meth:`printed_fields` and build again with :meth:`from_printed`:
    ``dataclasses.replace`` copies the derived values as they were, which
    then no longer follow from the cell that changed.

    The fields are told apart by their resolved annotations, once per
    class, so a subclass annotates each of its own fields as one of
    ``float | None`` (``Optional[float]`` is the same annotation),
    ``int | None``, ``bool``, ``str``, ``frozenset[str]`` or
    ``Mapping[str, ...]`` of those; any other annotation, a bare ``float``
    or ``int`` included, raises :class:`TypeError` the first time the class
    is built, rather than letting a field through unchecked.

    :ivar name: The material as the table names it, attribution stripped.
    :ivar variant: Which specimen or condition this row is, when the page
        prints several under one name: ``"chemically pure"``, ``"direction
        x"``, ``"0.68 mm diameter"``. Empty when the page prints one.
    :ivar source: Document, table, PDF page and printed folio.
    :ivar table: The data file this row was read from, without the
        extension, which is also the first half of its key in the catalogue
        that holds it.
    :ivar basis: What the source says a value is: a field name, or ``"row"``
        for the whole row, to one of :data:`CATALOGUE_BASES`. Hopkins marks
        most of his Poisson ratios "Estimate", and those cells hold
        ``"estimated"``; a datasheet that declares a class under a product
        standard would hold ``"declared"``. A field with no entry takes the
        row's, and a row with neither is one whose source does not say,
        which is a different answer from any of the five. :meth:`basis_of`
        reads it. Independent of :attr:`derived`: this is what the source
        claims for a cell, that is what this library computed.
    :ivar approximate: Fields the page prints with a ``~``. Not an estimate
        and not an interval: a number the author rounded on purpose.
    :ivar derived: Field to how it was computed, for the ones this library
        worked out from the cells the page did print. A derived value is never
        stored as if it had been read, and on every row the library builds it
        follows again from the row's own cells: :meth:`from_printed` writes
        it, and nothing else in the library does. One a caller passes to the
        literal constructor is the caller's word, which the row keeps and
        :meth:`printed_fields` leaves out with its value, as it leaves out
        every derived one. When the printed cells a value rests on do not all
        have one :attr:`basis`, the text names the basis of each, so a
        modulus worked out from a plate speed and a Poisson ratio Hopkins
        marks as an estimate says it rests on that estimate. A value
        converted from the unit the page prints is not derived
        (:attr:`converted` holds it), and neither is one the page gives by
        reference to another of its rows (:attr:`carried` does).
    :ivar converted: Field to ``(figure, unit)``, the page's figure and the
        unit it is in, for a value this row holds in a unit the page does
        not use. Ver and Beranek print their damping materials in degrees
        Fahrenheit and pounds per square inch, and the row holds degrees
        Celsius and pascals, so ``("3e5", "psi")`` sits beside a modulus in
        pascals. The figure is kept as the page writes it, so the cell can
        always be read back in the page's own terms. The unit is the one the
        page prints with the figure or over its column. Long prints the
        figures of his musician bare, and the sabins recorded for them are a
        reading of the table, which is set in inches and pounds and names
        sabins on the next row; that row's note says so. A figure written in
        another unit of the same kind as the field's (``thickness_m`` for
        ``thickness_mm``, ``flow_resistivity_kpa_s_m2`` for
        ``flow_resistivity_pa_s_m2``) is converted by :meth:`from_printed`
        and recorded here, whether it is a value, the end of a range or one
        of several readings; for a range the figure is the printed end of a
        bound, or both ends as ``"5 to 10"``, and for readings the list as
        the page gives it. A packaged table transcribed in the base unit
        with only its SI prefix changed, such as the megapascals of Rossing
        Table 15.5, holds no entry here, and the table's ``about`` says so.
    :ivar carried: Field to where the page gives it from, for a value the
        page gives by reference to another of its rows rather than on this
        one: a cell left blank under a block whose first row prints the
        figure, as in Ver and Beranek Table 8.7, or a description that reads
        "Parecido al anterior" and prints no row number, as three rows of
        Harris Chapter 32 do, which refers to the row above it. The value is
        the page's, and this says which of its rows gives it.
    :ivar ranges: ``(low, high)`` for each field the page prints as an
        interval rather than a value. One end is ``None`` only for a bound
        whose open side the quantity has no limit on; the end the page prints
        is always a number, and a two-sided interval has two.
    :ivar bounded_above: The subset of :attr:`ranges` the page prints as
        ``< x`` or ``<= x``, where the low end is a floor and not a
        measurement.
    :ivar bounded_below: The subset of :attr:`ranges` the page prints as
        ``> x`` or ``>= x``, where the high end is the ceiling the quantity
        cannot pass and not a measurement: Cox gives an aerogel a porosity of
        ``>0.75``, and the 1 beside it is what a porosity is, not what anybody
        measured. A quantity with no such ceiling leaves that end ``None``
        rather than borrowing a number for it: ASHRAE prints ``>45`` for a
        duct wall whose radiated sound the background swamped, and a
        transmission loss has no value it cannot pass, so the open end is
        empty. It is never an infinity, which is not a number the page has
        and not a token JSON can carry.
    :ivar reported: Field to the values the page lists for it, for a cell that
        prints several with no single one: ``"25, 207, 230"`` or ``"96,
        200-450"``, readings from as many studies. Each entry is a number or
        a ``(low, high)`` pair. Not a range, because the page did not print
        one, and not variants, because the page does not say which is which.
    :ivar unquantified: Field to what the page printed in place of a number,
        for a cell that is neither empty nor numeric: ``"Varies with
        frequency"``, ``"model"``, ``"…"`` for a row of dots. What the page
        printed, and never a sentence about why the number is missing:
        :meth:`why_missing` composes that sentence around it, so a caller and
        a published table both get the cell as it reads on the page.
    :ivar uncertainty: Field to the plus-or-minus the page prints beside the
        value, in the same unit. Cox prints an effective flow resistivity of
        ``(540 +/- 92) x 10^3``, and two of his rows print an uncertainty as
        large as the value itself. What the interval means is not stated on
        the page, so it is not stated here either: it is the number the page
        prints beside the value and nothing more.
    :ivar misprinted: Field to what the page prints there and why it cannot be
        that, for a cell whose defect is confirmed and registered in
        ``docs/ERRATA.md``. The number is not served, because a catalogue that
        handed it over would put a value its own registry calls wrong behind
        every calculation downstream; it is not dropped either, because a
        reader reproducing the book needs to see what the book says. This is
        the narrowest of the hedges and the one that costs most to claim: a
        cell earns it only when the defect follows from the page itself or
        from something as settled as the molar mass of a named molecule, and
        never from one book disagreeing with another.
    :ivar not_derivable: Field to why this library leaves it empty although
        the arithmetic would reach it. Bies leaves the speed of his aluminium
        honeycomb panels blank, and the modulus and the density beside it are
        effective ones, so ``sqrt(E/rho)`` would put a one-dimensional speed
        on a panel that has none. A row says so here, and nothing fills the
        cell afterwards.
    :ivar attributed_to: Credit for a cell the book takes from someone else.
        Keyed by field name, or by ``"row"`` or ``"table"`` when the credit
        covers all of one.
    :ivar group: The heading of the block this row sits under, when the table
        prints its rows in named groups: Cox files each material under
        ``"Fibrous materials"``, ``"Cellular materials"``,
        ``"Granular materials"`` or ``"Other"``. Empty for a table that prints
        one list.
    :ivar note: What the page says about this row beyond its numbers.
    :ivar provenance: The document the row was read from, for a row read
        from a caller's catalogue file: its kind, version, the day it was
        consulted, the laboratory and the report. ``None`` on every packaged
        row, whose :attr:`source` cites a page. A refusal names the document
        by its kind (``"the datasheet prints an upper bound of ..."``), where
        a row without one says ``"the page"``; and the fields of its
        ``field_test_standards`` are fields of the row.
    """

    #: The hedges whose keys name a numeric field: what the page printed in
    #: place of a number or beside it, what the source claims it is, and who
    #: it is credited to (these two also take the ``"row"``, and a credit the
    #: ``"table"``). A subclass with a hedge of its own extends it, as
    #: :class:`~phonometry.solids.SolidMaterial` does with ``borrowed``.
    _number_hedges: ClassVar[tuple[str, ...]] = (
        "approximate",
        "converted",
        "ranges",
        "bounded_above",
        "bounded_below",
        "reported",
        "unquantified",
        "uncertainty",
        "not_derivable",
        "basis",
        "attributed_to",
    )
    #: The hedges whose keys may name a text field as well as a numeric one,
    #: because a page prints them there: Harris prints a misspelt material
    #: name, and three of his descriptions give their row by reference to the
    #: one above.
    _value_hedges: ClassVar[tuple[str, ...]] = ("derived", "carried", "misprinted")
    #: The units :meth:`from_printed` takes a figure in besides the one a
    #: field is named for, converted exactly and recorded in
    #: :attr:`converted`. A class whose pages print another unit lists it, as
    #: :class:`~phonometry.materials.AbsorptionAreaSpectrum` lists the
    #: sabins of a table set in feet.
    _unit_aliases: ClassVar[tuple[UnitAlias, ...]] = ()
    #: How a derived text names each printed cell a value can rest on, in
    #: the words the rest of the text uses ("the plate speed", not the field
    #: name). A class whose :meth:`_complete` fills a value lists every cell
    #: it passes as an input; a derived text resting on a cell with no words
    #: refuses to be written.
    _cell_words: ClassVar[Mapping[str, str]] = MappingProxyType({})

    name: str
    source: str
    table: str = ""
    variant: str = ""
    basis: Mapping[str, str] = field(default_factory=dict)
    approximate: frozenset[str] = frozenset()
    derived: Mapping[str, str] = field(default_factory=dict)
    converted: Mapping[str, tuple[str, str]] = field(default_factory=dict)
    carried: Mapping[str, str] = field(default_factory=dict)
    ranges: Mapping[str, tuple[float | None, float | None]] = field(
        default_factory=dict
    )
    bounded_above: frozenset[str] = frozenset()
    bounded_below: frozenset[str] = frozenset()
    reported: Mapping[str, tuple[float | tuple[float, float], ...]] = field(
        default_factory=dict
    )
    unquantified: Mapping[str, str] = field(default_factory=dict)
    uncertainty: Mapping[str, float] = field(default_factory=dict)
    not_derivable: Mapping[str, str] = field(default_factory=dict)
    misprinted: Mapping[str, str] = field(default_factory=dict)
    attributed_to: Mapping[str, str] = field(default_factory=dict)
    group: str = ""
    note: str = ""
    provenance: Provenance | None = None

    def __post_init__(self) -> None:
        """Hold the row to the contract every row is held to, and freeze it.

        ``frozen=True`` refuses to rebind a field and says nothing about what
        the field points at, so a set left a list, or a mapping left a dict,
        would be editable in place while the row around it was not. The
        catalogue is one object shared by every caller, and provenance one of
        them can rewrite is worth less than none. The eleven rules the class
        docstring lists run here, the field checks first, so the first
        broken one is the one named.

        :raises CatalogueError: naming the row, the field and what it holds,
            for the first rule the row breaks.
        :raises TypeError: for a subclass field whose annotation the contract
            cannot classify.
        """
        shape = _shape(type(self))
        try:
            for field_name, check in shape.checks:
                value = getattr(self, field_name)
                kept = check(value, field_name)
                if kept is not value:
                    object.__setattr__(self, field_name, kept)
        except CatalogueError as error:
            msg = f"{self.name!r}: {error}"
            raise CatalogueError(msg, field=field_name) from None
        self._check_name_and_source()
        self._check_hedge_keys(shape)
        self._check_test_standards(shape)
        self._check_hedge_texts()
        self._check_bounds_have_ranges()
        self._check_range_ends()
        self._check_reported()
        self._check_uncertainty()
        self._check_cells_that_hold_nothing(shape)
        self._check_cells_that_hold_something(shape)
        self._check_basis()
        self._check_limits(shape)

    def _check_name_and_source(self) -> None:
        """Refuse a row with no name or no citation.

        A row is found by its name and trusted for its source, and a row
        with neither is a number nobody can look up or check.

        :raises CatalogueError: naming the one that is empty.
        """
        for field_name in ("name", "source"):
            if not getattr(self, field_name).strip():
                msg = (
                    f"a catalogue row needs a name and a source, and the row "
                    f"{self.name!r} from {self.source!r} has no {field_name}"
                )
                raise CatalogueError(msg, field=field_name)

    def _check_hedge_keys(self, shape: _Shape) -> None:
        """Refuse a hedge keyed by a name that is not a field of this row.

        A hedge on a misspelt field hedges nothing: the cell it meant keeps
        answering as a plain number, and the hedge is never read.

        :raises CatalogueError: naming the hedge, the key and the class.
        """
        for hedges, allowed, what in (
            (self._number_hedges, shape.numeric, "a numeric field"),
            (self._value_hedges, shape.cells, "a field"),
        ):
            for hedge in hedges:
                keys = getattr(self, hedge)
                if not keys:
                    continue
                words = _ROW_WORDS.get(hedge, frozenset())
                for key in keys:
                    if key not in allowed and key not in words:
                        msg = (
                            f"{self.name!r}: {hedge} names {key!r}, which is not "
                            f"{what} of {type(self).__name__}"
                        )
                        raise CatalogueError(msg, field=hedge)

    def _check_test_standards(self, shape: _Shape) -> None:
        """Refuse a per-field test standard keyed by a name that is no field.

        A standard cited for a misspelt field is cited for nothing, and the
        field it meant falls back to the document's own.

        :raises CatalogueError: naming the key and the class.
        """
        if self.provenance is None:
            return
        for key in self.provenance.field_test_standards:
            if key not in shape.numeric:
                msg = (
                    f"{self.name!r}: the provenance's field_test_standards names "
                    f"{key!r}, which is not a numeric field of "
                    f"{type(self).__name__}"
                )
                raise CatalogueError(msg, field="provenance")

    def _check_hedge_texts(self) -> None:
        """Refuse a hedge whose text says nothing.

        :meth:`why_missing` hands a :attr:`misprinted` or
        :attr:`not_derivable` text back as it is, so an empty one answers
        ``""``, which is the answer of a cell that holds its value, and hides
        the defect the hedge was written to record. An empty word, credit,
        source row or printed figure says as little. :attr:`basis` is left
        to :meth:`_check_basis`, whose five words already leave out the
        empty one.

        :raises CatalogueError: naming the hedge and the field.
        """
        for hedge in (*self._number_hedges, *self._value_hedges):
            held = getattr(self, hedge)
            if hedge == "basis" or not held or not isinstance(held, Mapping):
                continue
            for key, value in held.items():
                texts = value if isinstance(value, tuple) else (value,)
                if any(isinstance(text, str) and not text.strip() for text in texts):
                    msg = (
                        f"{self.name!r}: {hedge} holds no text for {key!r}; a "
                        "hedge that says nothing reads as a cell with nothing "
                        "to explain"
                    )
                    raise CatalogueError(msg, field=hedge)

    def _check_bounds_have_ranges(self) -> None:
        """Refuse a bound on a field that has no range to bound.

        A bound is a range the page prints one end of, and the end is what
        :attr:`ranges` holds; a bound without it has no number at all.

        :raises CatalogueError: naming the bound and the field.
        """
        for hedge in ("bounded_above", "bounded_below"):
            for key in getattr(self, hedge):
                if key not in self.ranges:
                    msg = (
                        f"{self.name!r}: {hedge} names {key!r}, which has no "
                        "range; a bound is a range the page prints one end of"
                    )
                    raise CatalogueError(msg, field=hedge)

    def _check_reported(self) -> None:
        """Refuse an empty list of readings, or a reading interval backwards.

        A list with nothing in it is not several values: :meth:`why_missing`
        would say the page lists nothing, and a ``converted`` or ``carried``
        cell would count it as something to describe. An interval among the
        readings is an interval like any other, and one stored high to low
        reads back as a reading nobody printed.

        :raises CatalogueError: naming the field, and the interval.
        """
        for field_name, entries in self.reported.items():
            if not entries:
                msg = (
                    f"{self.name!r}: reported lists nothing for {field_name!r}; "
                    "a list of readings holds at least one"
                )
                raise CatalogueError(msg, field=field_name)
            for entry in entries:
                if isinstance(entry, tuple) and entry[0] > entry[1]:
                    msg = (
                        f"{self.name!r}: a reading of {field_name!r} runs from "
                        f"{entry[0]!r} down to {entry[1]!r}; the low end comes "
                        "first"
                    )
                    raise CatalogueError(msg, field=field_name)

    def _check_uncertainty(self) -> None:
        """Refuse a plus-or-minus below zero.

        :raises CatalogueError: naming the field and the value.
        """
        for key, spread in self.uncertainty.items():
            if spread < 0:
                msg = (
                    f"{self.name!r}: the uncertainty of {key!r} is {spread!r}, "
                    "and a plus-or-minus is never below zero"
                )
                raise CatalogueError(msg, field=key)

    def _check_cells_that_hold_nothing(self, shape: _Shape) -> None:
        """Refuse a value beside a hedge that says there is none to serve.

        A value is served before any hedge is read, so a number beside
        ``misprinted`` would go on being handed out while the row calls it
        wrong, and one beside a word or a list would contradict the cell the
        page printed.

        :raises CatalogueError: naming the field, its value and the hedge.
        """
        hedged = [
            (hedge, key) for hedge in _HOLDS_NOTHING for key in getattr(self, hedge)
        ]
        hedged += [
            ("misprinted", key) for key in self.misprinted if key in shape.numeric
        ]
        for hedge, key in hedged:
            value = getattr(self, key)
            if value is not None:
                msg = (
                    f"{self.name!r}: {key} holds {_quote(value)}, and {hedge} "
                    "says the page has no value to serve there"
                )
                raise CatalogueError(msg, field=key)

    def _check_cells_that_hold_something(self, shape: _Shape) -> None:
        """Refuse a conversion or a carried cell with nothing behind it.

        ``converted`` says what the page printed for the value the row
        holds, and ``carried`` which row the page gives it from; with no
        value, range or list beside them there is nothing they describe.

        :raises CatalogueError: naming the hedge and the field.
        """
        for hedge in ("converted", "carried"):
            for key in getattr(self, hedge):
                value = getattr(self, key)
                if key in shape.texts:
                    held = bool(value)
                else:
                    held = (
                        value is not None or key in self.ranges or key in self.reported
                    )
                if not held:
                    msg = (
                        f"{self.name!r}: {hedge} names {key!r}, which holds "
                        "nothing: no value, no range and no list"
                    )
                    raise CatalogueError(msg, field=key)

    def _readings(self, field_name: str) -> Iterator[tuple[str, float]]:
        """Every number the row holds for one field, with what it is."""
        value = getattr(self, field_name)
        if value is not None:
            yield field_name, value
        for end in self.ranges.get(field_name, ()):
            if end is not None:
                yield f"an end of the range of {field_name}", end
        for entry in self.reported.get(field_name, ()):
            for number in entry if isinstance(entry, tuple) else (entry,):
                yield f"a reading of {field_name}", number

    def _check_limits(self, shape: _Shape) -> None:
        """Refuse a number outside what its quantity can physically be.

        :raises CatalogueError: naming the field, the number and the limit.
        """
        for field_name, low, high, why in shape.limits:
            for what, number in self._readings(field_name):
                if number < low or (high is not None and number > high):
                    msg = f"{self.name!r}: {what} is {number!r}, and {why}"
                    raise CatalogueError(msg, field=field_name)

    def _check_basis(self) -> None:
        """Refuse a basis outside :data:`CATALOGUE_BASES`.

        The catalogue page and every reader of :meth:`basis_of` act on these
        five words only, so any other one would reach them as a claim nobody
        can read, and a misspelt ``"estimate"`` would publish an estimate as
        a printed number.

        :raises CatalogueError: naming the field and the word.
        """
        for field_name, basis in self.basis.items():
            if basis not in CATALOGUE_BASES:
                msg = (
                    f"{self.name!r}: the basis of {field_name!r} is {basis!r}, "
                    f"which is not one of {', '.join(CATALOGUE_BASES)}"
                )
                raise CatalogueError(msg, field="basis")

    def _check_range_ends(self) -> None:
        """Refuse a range missing the end the page printed.

        The open side of a bound may be empty, because a quantity with no
        ceiling has nothing to put there. The printed side never may: a bound
        whose own number is missing would read back as a cell the page left
        blank, which is the one thing this class exists to tell apart.

        Nor may the ends run backwards: a range printed low to high and
        stored high to low reads back as an interval nobody printed.

        :raises CatalogueError: when a bound has no printed end, when a
            two-sided interval is missing either of them, or when its low end
            is above its high one.
        """
        for field_name, (low, high) in self.ranges.items():
            if field_name in self.bounded_above:
                missing = high is None
            elif field_name in self.bounded_below:
                missing = low is None
            else:
                missing = low is None or high is None
            if missing:
                msg = (
                    f"{self.name!r}: the range of {field_name!r} is missing an end "
                    "the page prints; only the open side of a bound may be empty"
                )
                raise CatalogueError(msg, field=field_name)
            if low is not None and high is not None and low > high:
                msg = (
                    f"{self.name!r}: the range of {field_name!r} runs from "
                    f"{low!r} down to {high!r}; the low end comes first"
                )
                raise CatalogueError(msg, field=field_name)

    @classmethod
    def from_printed(cls, **cells: Any) -> Self:
        """A row built from the cells its page prints, completed and marked.

        The one path that works anything out. The cells are what the page
        prints, under the field names of the class and with the hedges each
        cell carries, as a data file writes them. A figure written in another
        unit of the same kind as its field (``thickness_m`` for
        ``thickness_mm``, ``flow_resistivity_kpa_s_m2`` for
        ``flow_resistivity_pa_s_m2``), or in a unit the class takes as an
        alias of its own (an
        :class:`~phonometry.materials.AbsorptionAreaSpectrum` takes
        ``absorption_area_125_ft2`` for ``absorption_area_125_m2``), is
        converted on its digits with an exact factor and rounded once,
        whether it is a value or stands as the key of a hedge (the ends of a
        range, the readings of a list and a plus-or-minus convert with it),
        and :attr:`converted` records the figure and its unit. Every number
        of one cell is written in one unit. The row is then
        built and held to the contract the class docstring lists, so every
        cell is checked before any arithmetic reads it. Last, the class
        fills what follows from those cells (a modulus from a plate speed, a
        density and a Poisson ratio), never over a cell that holds a value
        or one the row says something else about, and :attr:`derived` says
        how each filled value was reached and, when the cells it rests on
        do not share one :attr:`basis`, the basis of each. Cells the
        arithmetic cannot take are refused rather than turned into a value
        that would be wrong: a modulus of 1 GPa and a shear modulus of
        0.1 GPa give a Poisson ratio of 4, which no isotropic solid has, and
        a row whose cells are not meant to give a value says so in
        :attr:`not_derivable`, which keeps the arithmetic from running.

        ``Cls(...)`` stays literal: it holds what it is given and works
        nothing out. To change a cell of a row and have what follows from
        it follow again, change it in :meth:`printed_fields` and build again
        here; ``dataclasses.replace`` would copy the derived values as they
        were::

            cells = row.printed_fields()
            cells["density_kg_m3"] = 2400.0
            row = type(row).from_printed(**cells)

        :param cells: The printed cells, as keywords of the class.
        :return: The row, with what follows from its cells filled in.
        :raises CatalogueError: for a cell the contract refuses; for a
            ``derived`` among the cells, which is this method's to write; for
            a figure under a unit alias that is not a finite number, or that
            names a cell given under its own name or under another alias as
            well; for the numbers of one cell written in two units, a name
            two fields of one kind could both take, or a figure whose text
            field saying what it is of is empty; and for printed cells a
            value that follows from them cannot be worked out of, naming the
            value and the cells.
        :raises TypeError: for a name that is neither a field of the class
            nor a unit alias of one.
        """
        if "derived" in cells:
            msg = (
                f"{cells.get('name')!r}: derived is what from_printed works out "
                "from the printed cells, and is not one of them; pass the cells "
                "the page prints, as printed_fields() gives them"
            )
            raise CatalogueError(msg)
        row = cls(**_resolve_units(cls, cells))
        if cls._complete is CatalogueRow._complete:
            return row
        completion = Completion(row)
        row._complete(completion)
        filled: dict[str, Any] = completion.filled()
        if not filled:
            return row
        filled["derived"] = completion.derived()
        return dataclasses.replace(row, **filled)

    def _complete(self, cells: Completion) -> None:
        """Fill what follows from this row's printed cells; the base fills nothing.

        The hook :meth:`from_printed` calls on the row it has built from the
        printed cells. A class whose cells over-determine one another reads
        them with :meth:`Completion.get` and fills with
        :meth:`Completion.fill`, naming the fields each value is worked out
        from.

        :param cells: The row's cells as the completion fills them in.
        """

    def printed_fields(self) -> dict[str, Any]:
        """The cells the page prints, as :meth:`from_printed` takes them.

        Every field, the name, the citation, the table and every hedge
        included, except the values this library derived, :attr:`derived`
        itself, and a field left at a default that holds nothing (a quantity
        the page leaves out, an empty text or hedge). A text field whose
        default says something is kept even when it holds no text: the
        ``per`` of an area per unit is a person unless the row says
        otherwise, and a row that leaves it empty has said otherwise. A
        value converted from the page's unit and one the page gives by
        reference to another of its rows are the page's, so they stay, with
        :attr:`converted` and :attr:`carried` beside them.

        For every row :meth:`from_printed` builds, and so for every packaged
        one, ``type(row).from_printed(**row.printed_fields())`` is the row
        again, and changing a cell before building it again is how a row is
        edited without carrying a derived value that no longer follows from
        it. A ``derived`` passed to the literal constructor is the caller's
        own; it is left out here with its value, like every derived one, so
        building again gives back only what the class works out.

        :return: A new dictionary of constructor keywords. The values are
            the ones the row holds, frozen as the row holds them.
        """
        return {
            item.name: value
            for item in fields(self)
            if item.name != "derived"
            and item.name not in self.derived
            and not _left_empty(item, value := getattr(self, item.name))
        }

    def is_approximate(self, field_name: str) -> bool:
        """Whether the page prints this field with a ``~``.

        :param field_name: One of the numeric field names of this class.
        :return: ``True`` when the page rounded the cell on purpose.
        """
        return field_name in self.approximate

    def is_derived(self, field_name: str) -> bool:
        """Whether this library computed this field instead of reading it.

        :param field_name: One of the numeric field names of this class.
        :return: ``True`` when the page did not print it and the value follows
            from cells that it did. :attr:`derived` says how. A value the
            page prints in another unit, or gives by reference to another of
            its rows, answers ``False``: the number is the page's, and
            :attr:`converted` or :attr:`carried` says so.
        """
        return field_name in self.derived

    def basis_of(self, field_name: str) -> str:
        """What the source says this field is, one of :data:`CATALOGUE_BASES`.

        The five are ``measured``, ``declared``, ``calculated``, ``estimated``
        and ``extended``.

        :param field_name: One of the field names of this class.
        :return: The field's own entry in :attr:`basis`, else the row's, else
            the empty string, which means the source does not say.
        """
        return self.basis.get(field_name, self.basis.get("row", ""))

    def printed(self, field_name: str, *, wanted_by: str = "the caller") -> float:
        """One quantity this page prints, or a refusal that says what it had.

        Every quantity of a row is optional, because the pages print different
        columns, so a caller passing one into a function that requires a float
        has to narrow it. Doing it here beats an assertion at each call site:
        the refusal names the field, who wanted it and what the page had in
        that cell, which is the difference between a cell the book left empty
        and a cell holding the word "model".

        :param field_name: The quantity wanted.
        :param wanted_by: What wants it, named in the message.
        :return: The value, as a float.
        :raises ValueError: when the page did not print a number there.
        """
        value = getattr(self, field_name)
        if value is None:
            msg = (
                f"{self.name!r} has no {field_name}, which {wanted_by!r} needs: "
                f"{self.why_missing(field_name)} ({self.source})."
            )
            raise ValueError(msg)
        return float(value)

    def why_missing(self, field_name: str) -> str:
        """Why this field is ``None``, in the page's own terms.

        A catalogue that answers ``None`` and stops is asking the caller to
        guess whether the material has no such property, whether the book
        measured it and printed a dash, or whether the cell holds something
        that is not a number. Each of those is a different answer.

        The sentence names the document by its kind: ``"the datasheet"``,
        ``"the test report"``, and ``"the page"`` for a row with no
        :attr:`provenance`, which is every packaged one. For a cell the row
        holds in another unit than the page's, a bound, a range or a list
        quotes the page's figure and unit first and the row's value after
        it: ``"the datasheet prints a lower bound of 5 kPa s/m2 (5000 Pa
        s/m2) and no value"``, never a figure the page does not print.

        :param field_name: One of the numeric field names of this class.
        :return: What the page had in that cell, or the empty string when the
            field is not missing at all. A field the page has no column for
            and this library cannot derive, because the cells it would need
            are themselves a range, answers that it does not follow.
        :raises AttributeError: for a name this class does not have, because a
            misspelt field would otherwise answer as if the cell were empty.
        """
        if getattr(self, field_name) is not None:
            return ""
        subject = _PAGE if self.provenance is None else self.provenance.noun
        if field_name in self.misprinted:
            return self.misprinted[field_name]
        if field_name in self.unquantified:
            return (
                f"{subject} prints “{self.unquantified[field_name]}” "
                f"where the number would be"
            )
        if field_name in self.not_derivable:
            return self.not_derivable[field_name]
        # A value converted from the page's figure is quoted in full after
        # it, where six digits would round what the conversion kept.
        digits = ".15g" if field_name in self.converted else "g"
        if field_name in self.ranges:
            low, high = self.ranges[field_name]
            if high is not None and field_name in self.bounded_above:
                shown = self._as_printed(field_name, format(high, digits))
                return f"{subject} prints an upper bound of {shown} and no value"
            if low is not None and field_name in self.bounded_below:
                shown = self._as_printed(field_name, format(low, digits))
                return f"{subject} prints a lower bound of {shown} and no value"
            if low is not None and high is not None:
                spelled = f"{format(low, digits)} to {format(high, digits)}"
                shown = self._as_printed(field_name, spelled)
                return f"{subject} prints {shown} and no value"
        if field_name in self.reported:
            listed = ", ".join(
                _spell(entry, digits) for entry in self.reported[field_name]
            )
            shown = self._as_printed(field_name, listed)
            return f"{subject} lists {shown} and no single value"
        return (
            f"{subject} does not give it, and it does not follow from the cells "
            "that it does"
        )

    def _as_printed(self, field_name: str, held: str) -> str:
        """*held*, or the page's figure and unit with *held* after it.

        A cell the row holds in another unit than the page's is quoted in
        the page's terms first, because a refusal that put the converted
        number after "prints" would say the page prints a figure it does
        not.
        """
        if field_name not in self.converted:
            return held
        figure, unit = self.converted[field_name]
        own = _shape(type(self)).spellings.units.get(field_name, "")
        return f"{figure} {unit} ({held} {own})" if own else f"{figure} {unit} ({held})"

    def _catalogue_notes(self) -> tuple[str, ...]:
        """What a reader of a catalogue file should note about this row.

        The hook a catalogue reader calls on every row it builds, for what
        only the row's own class can judge: a rating a data sheet prints
        beside the bands it is worked out from, and which does not follow
        from them, or a value off the grid its standard rounds to. A note is
        kept beside the catalogue and never changes the row. The base class
        notes nothing.

        :return: One sentence per note, each naming the cells it is about.
        """
        return ()


@dataclass(frozen=True, kw_only=True)
class BandedRow(CatalogueRow):
    """One row of a table that prints its quantity once per frequency band.

    The catalogues of this library that hold a spectrum read off a page keep
    one field per band rather than an array, because every hedge
    of :class:`CatalogueRow` is keyed by field name and a cell the page left
    empty has to say so the way any other cell does. What they then need is
    the same three things: which bands this row filled, the row as a spectrum,
    and a lookup that refuses rather than answering zero for a band the page
    did not print. That is what this holds.

    A subclass declares the bands its tables can print and how its band fields
    are spelled, and defines the reading method under the name its own domain
    uses, because ``row.transmission_loss_db(500)`` reads better than a generic
    verb and says what comes back. :meth:`values_at` reads the row at a whole
    array of frequencies, for a function that takes one value per band by
    position.
    """

    #: The band centre frequencies a table of this quantity can print, in
    #: hertz. A table prints a subset.
    _bands_hz: ClassVar[tuple[int, ...]] = ()
    #: How many of these bands make an octave: 1 for octave bands, 3 for
    #: one-third octave bands. :meth:`values_at` reads a frequency as a band
    #: within a sixth of the spacing between bands.
    _bands_per_octave: ClassVar[int] = 1
    #: The band field for a centre frequency is this, the frequency, and
    #: :attr:`_band_suffix`: ``"absorption_coefficient_"`` and ``""`` give
    #: ``absorption_coefficient_500``.
    _band_prefix: ClassVar[str] = ""
    _band_suffix: ClassVar[str] = ""
    #: What these tables call their bands, for the wording of a refusal.
    _band_kind: ClassVar[str] = "octave"
    #: What the tables are of, for the wording of a refusal.
    _table_kind: ClassVar[str] = "published"

    @classmethod
    def _band_field(cls, band_hz: int) -> str:
        """The field name that holds one band of this row."""
        return f"{cls._band_prefix}{band_hz}{cls._band_suffix}"

    def bands(self) -> tuple[int, ...]:
        """The bands this row prints a value for, in hertz."""
        return tuple(
            band
            for band in self._bands_hz
            if getattr(self, self._band_field(band)) is not None
        )

    def spectrum(self) -> dict[int, float]:
        """The row as ``{band_hz: value}`` over the bands it prints.

        A band the page left empty, or printed as something other than a
        number, is left out rather than filled with a zero;
        :meth:`~CatalogueRow.why_missing` on that band's field says which it
        was.
        """
        return {
            band: float(getattr(self, self._band_field(band))) for band in self.bands()
        }

    def _not_a_band(self, frequency: float) -> str:
        """The start of a refusal for a frequency that is none of the bands."""
        return (
            f"{frequency:g} Hz is not {self._band_kind} band that "
            f"{self._table_kind} tables print"
        )

    def _in_band(self, band_hz: int) -> float:
        """One band of this row, or a refusal that says what the page had.

        :param band_hz: A centre frequency from the bands this class declares.
        :return: The printed value, as a float.
        :raises ValueError: when the page has no number in that band, naming
            the row, the band and what the cell held instead; or when
            *band_hz* is not a band these tables print.
        """
        if band_hz not in self._bands_hz:
            msg = f"{self._not_a_band(band_hz)}; the bands are {self._bands_hz}"
            raise ValueError(msg)
        return self.printed(
            self._band_field(band_hz), wanted_by=f"the {band_hz} Hz band"
        )

    def values_at(self, frequencies_hz: ArrayLike) -> NDArray[np.float64]:
        """The row's value at each of *frequencies_hz*, or a refusal.

        The adapter for a function that takes one value per band by position
        (the absorption of a surface in a reverberation formula, the
        transmission loss of a panel at the frequencies an enclosure model
        asks for), because an array handed over by position cannot say
        which band is missing and a row can. Each frequency is read as the
        band of these tables whose centre is nearest on a logarithmic scale,
        and matches it when it lies within a sixth of the spacing between
        bands: a sixth of an octave for octave bands, an eighteenth for
        one-third octave bands. That takes the nominal centre, the exact
        base-ten one and the exact base-two one alike (160 Hz, 158.49 Hz and
        157.49 Hz are one band) and never reaches the next band. A band the
        row does not print is refused, as :meth:`~CatalogueRow.printed`
        refuses it, with what the page had there; it is never read as zero
        and never filled from its neighbours.

        :param frequencies_hz: Band centre frequencies, in hertz, of any
            shape.
        :return: A new array of the same shape, one value per frequency.
        :raises ValueError: for a frequency that is not finite and positive,
            for one that matches none of the bands, naming the nearest, and
            for a band this row does not print, naming the row, the band and
            what the page had in that cell.
        """
        wanted = np.asarray(frequencies_hz, dtype=np.float64)
        flat = wanted.reshape(-1)
        if not (np.all(np.isfinite(flat)) and np.all(flat > 0.0)):
            msg = (
                f"frequencies_hz holds {_quote(flat.tolist())}, and a band "
                "centre is a finite frequency above zero"
            )
            raise ValueError(msg)
        if flat.size == 0:
            return np.empty(wanted.shape, dtype=np.float64)
        centres = np.asarray(self._bands_hz, dtype=np.float64)
        octaves = np.abs(np.log2(flat[:, np.newaxis] / centres))
        nearest = np.argmin(octaves, axis=1)
        reach = 1.0 / (6.0 * self._bands_per_octave)
        off = octaves[np.arange(flat.size), nearest] > reach
        if np.any(off):
            first = int(np.argmax(off))
            band = self._bands_hz[int(nearest[first])]
            msg = (
                f"{self._not_a_band(float(flat[first]))}: the nearest is {band} "
                "Hz, and a frequency reads as a band within a sixth of the "
                "spacing between bands"
            )
            raise ValueError(msg)
        bands = [self._bands_hz[int(index)] for index in nearest]
        values = {band: self._in_band(band) for band in dict.fromkeys(bands)}
        return np.array([values[band] for band in bands], dtype=np.float64).reshape(
            wanted.shape
        )


def rows_to_search[R: CatalogueRow](
    catalogue: object,
    published: Mapping[str, R],
    row_type: type[R],
    lookup: str,
) -> tuple[R, ...]:
    """The rows a ``*_named`` lookup reads, in the order the mapping holds them.

    Every lookup of a published catalogue takes ``catalogue=``, the rows to
    search in place of its own ``PUBLISHED_*``, which is *published* when the
    caller gives none. A caller's catalogue is any mapping of key to row: what
    :func:`phonometry.io.read_catalogue` returns, a published catalogue joined
    with one by ``|``, or a plain dictionary. Every row in it has to be a
    *row_type*, a subclass of the caller's own included. A row of another
    class is refused rather than skipped, because a lookup that skipped it
    would leave it out of the answer under the very name asked for, and
    nothing would say so.

    :param catalogue: What the caller passed as ``catalogue=``, or ``None``.
    :param published: The lookup's own published catalogue.
    :param row_type: The class the lookup answers with.
    :param lookup: The lookup's name, for the refusal.
    :return: The rows to match, every one a *row_type*.
    :raises TypeError: for a *catalogue* that is not a mapping, and for one
        that holds a row of another class, naming its key.
    """
    if catalogue is None:
        return tuple(published.values())
    if not isinstance(catalogue, Mapping):
        msg = (
            f"{lookup} takes catalogue= as a mapping of key to row, such as "
            f"what io.read_catalogue returns; got {type(catalogue).__name__}"
        )
        raise TypeError(msg)
    for key, row in catalogue.items():
        if not isinstance(row, row_type):
            msg = (
                f"catalogue= holds a row of class {type(row).__name__} under "
                f"{key!r}, and {lookup} reads {row_type.__name__} rows"
            )
            raise TypeError(msg)
    return tuple(catalogue.values())


def search_text(text: str) -> str:
    """*text* as every ``*_named`` lookup compares it: one form, no case.

    One word can reach a lookup in two Unicode forms: ``"linóleo"`` typed
    with the accented letter as one character, or pasted from a document that
    stores it as the plain letter followed by a combining accent. The two
    print the same and :meth:`str.casefold` keeps them apart, so a lookup that
    only folded case would answer the second with nothing. Every lookup
    passes both the name asked for and the text of each row through here:
    canonical decomposition, case folding and canonical composition, which is
    Unicode's canonical caseless match, so a name matches whichever form
    either side arrives in.

    :param text: A name asked for, or the text of a row.
    :return: *text* in the one form the lookups compare.
    """
    decomposed = unicodedata.normalize("NFD", text)
    return unicodedata.normalize("NFC", decomposed.casefold())
