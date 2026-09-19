#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Reading a published table out of a data file (private).

A catalogue row is data, not code. Keeping the rows in JSON beside the module
that publishes them means a new table is a new file rather than a longer
literal, means one row per record in a diff, and means the provenance gate can
read the citation without importing anything.

The document is one published table: a ``source`` in the grammar
``scripts/check_published_sources.py`` enforces, an ``about`` paragraph saying
what the page is and how it was read, and ``rows``. Every row carries a ``key``
unique within the file, and the rest of its fields are named exactly as the
dataclass that will hold them, so a typo in the data is a ``TypeError`` at
import and not a silently missing column.

:class:`CatalogueRow` is what every such dataclass inherits: the name, the
citation and the hedges a printed cell can carry instead of a number. A page
prints a range, or a ``~``, or three values from three studies, or a word, and
a catalogue that flattened any of those into a float would be claiming a
measurement the page does not make. The hedges are the same across the
catalogues because the pages are: a range in a table of solids is a range in
a table of porous materials.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

_REQUIRED = ("source", "about", "rows")

#: The mappings every row holds and does not own, frozen at construction.
_MAPPINGS = (
    "derived",
    "ranges",
    "reported",
    "unquantified",
    "not_derivable",
    "attributed_to",
)


class CatalogueError(ValueError):
    """A packaged table that does not say what the reader needs to trust it."""


def _reject(filename: str, what: str) -> None:
    """Name the file and the defect, because the caller cannot see either."""
    msg = f"{filename}: {what}"
    raise CatalogueError(msg)


def read_table(package: str, filename: str) -> tuple[str, tuple[dict[str, Any], ...]]:
    """Read one published table from a package's ``data`` directory.

    :param package: The package that owns the data, as ``phonometry.solids``.
        The file is read from its ``data`` subpackage.
    :param filename: The file name inside ``data``, including the extension.
    :return: The citation every row of the file shares, and the rows in the
        order the file lists them, each a plain dictionary ready to be passed
        to the dataclass that holds it.
    :raises CatalogueError: when the document is missing a top-level key, when
        ``rows`` is empty, or when two rows share a key.
    """
    from importlib.resources import files

    text = (files(f"{package}.data") / filename).read_text(encoding="utf-8")
    document = json.loads(text)
    for key in _REQUIRED:
        if key not in document:
            _reject(filename, f"a published table needs a top-level {key!r}")
    rows = document["rows"]
    if not rows:
        _reject(filename, "a published table with no rows publishes nothing")
    seen: set[str] = set()
    for row in rows:
        key = row.get("key")
        if key is None:
            _reject(filename, "every row needs a key of its own")
        if key in seen:
            _reject(filename, f"two rows share the key {key!r}")
        seen.add(key)
    return document["source"], tuple(rows)


def take(row: Mapping[str, Any], *, frozen: tuple[str, ...] = ()) -> dict[str, Any]:
    """The row as constructor keywords: no ``key``, and the named sets frozen.

    :param row: One row as :func:`read_table` returned it.
    :param frozen: Fields the JSON lists but the dataclass holds as a
        ``frozenset``, because a set has no order and a list implies one.
    :return: The remaining fields, ready to splat into the dataclass.
    """
    fields = {name: value for name, value in row.items() if name != "key"}
    for name in frozen:
        if name in fields:
            fields[name] = frozenset(fields[name])
    ranges = fields.get("ranges")
    if ranges is not None:
        fields["ranges"] = {name: tuple(pair) for name, pair in ranges.items()}
    reported = fields.get("reported")
    if reported is not None:
        fields["reported"] = {
            name: tuple(
                tuple(entry) if isinstance(entry, list) else entry for entry in entries
            )
            for name, entries in reported.items()
        }
    return fields


def _spell(entry: float | tuple[float, float]) -> str:
    """One listed value or interval, the way the page would read it aloud."""
    if isinstance(entry, tuple):
        low, high = entry
        return f"{low:g} to {high:g}"
    return f"{entry:g}"


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

    :ivar name: The material as the table names it, attribution stripped.
    :ivar variant: Which specimen or condition this row is, when the page
        prints several under one name: ``"chemically pure"``, ``"direction
        x"``, ``"0.68 mm diameter"``. Empty when the page prints one.
    :ivar source: Document, table, PDF page and printed folio.
    :ivar table: The data file this row was read from, without the
        extension, which is also the first half of its key in the catalogue
        that holds it.
    :ivar approximate: Fields the page prints with a ``~``. Not an estimate
        and not an interval: a number the author rounded on purpose.
    :ivar derived: Field to how it was computed, for the ones this library
        worked out from the cells the page did print. A derived value is never
        stored as if it had been read.
    :ivar ranges: ``(low, high)`` for each field the page prints as an
        interval rather than a value.
    :ivar bounded_above: The subset of :attr:`ranges` the page prints as
        ``< x`` or ``<= x``, where the low end is a floor and not a
        measurement.
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
    :ivar not_derivable: Field to why this library leaves it empty although
        the arithmetic would reach it. Bies leaves the speed of his aluminium
        honeycomb panels blank, and the modulus and the density beside it are
        effective ones, so ``sqrt(E/rho)`` would put a one-dimensional speed
        on a panel that has none. A row says so here, and nothing fills the
        cell afterwards.
    :ivar attributed_to: Credit for a cell the book takes from someone else.
        Keyed by field name, or by ``"row"`` or ``"table"`` when the credit
        covers all of one.
    :ivar note: What the page says about this row beyond its numbers.
    """

    name: str
    source: str
    table: str = ""
    variant: str = ""
    approximate: frozenset[str] = frozenset()
    derived: Mapping[str, str] = field(default_factory=dict)
    ranges: Mapping[str, tuple[float, float]] = field(default_factory=dict)
    bounded_above: frozenset[str] = frozenset()
    reported: Mapping[str, tuple[float | tuple[float, float], ...]] = field(
        default_factory=dict
    )
    unquantified: Mapping[str, str] = field(default_factory=dict)
    not_derivable: Mapping[str, str] = field(default_factory=dict)
    attributed_to: Mapping[str, str] = field(default_factory=dict)
    note: str = ""

    def __post_init__(self) -> None:
        """Freeze the mappings the dataclass holds but does not own.

        ``frozen=True`` refuses to rebind a field and says nothing about what
        the field points at, so a shared row's mappings were editable in place
        while the row around them was not. The catalogue is one object shared
        by every caller, and provenance one of them can rewrite is worth less
        than none.
        """
        for name in _MAPPINGS:
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

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
            from cells that it did. :attr:`derived` says how.
        """
        return field_name in self.derived

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
        if field_name in self.unquantified:
            return (
                f"the page prints “{self.unquantified[field_name]}” "
                f"where the number would be"
            )
        if field_name in self.not_derivable:
            return self.not_derivable[field_name]
        if field_name in self.ranges:
            low, high = self.ranges[field_name]
            if field_name in self.bounded_above:
                return f"the page prints an upper bound of {high:g} and no value"
            return f"the page prints {low:g} to {high:g} and no value"
        if field_name in self.reported:
            listed = ", ".join(_spell(entry) for entry in self.reported[field_name])
            return f"the page lists {listed} and no single value"
        return "the page does not give it, and it does not follow from the cells that it does"
