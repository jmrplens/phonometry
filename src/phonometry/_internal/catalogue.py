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
import and not a silently missing column.

:class:`CatalogueRow` is what every such dataclass inherits: the name, the
citation and the hedges a printed cell can carry instead of a number. A page
prints a range, or a ``~``, or three values from three studies, or a word, and
a catalogue that flattened any of those into a float would be claiming a
measurement the page does not make. The hedges are the same across the
catalogues because the pages are: a range in a table of solids is a range in
a table of porous materials.

The reader stays private. :class:`CatalogueRow`, :class:`BandedRow`,
:class:`CatalogueError` and :data:`CATALOGUE_BASES` are public, from
:mod:`phonometry.io`, because every catalogue of the library hands out rows
built on them, and a caller has to be able to name the type of what it holds
and catch what the constructor raises. They are defined here and not there
because the domain packages that publish the rows import them, and
:mod:`phonometry.io` importing a domain would close a cycle.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from collections.abc import Mapping

_REQUIRED = ("source", "about", "rows")

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

#: The mappings every row holds and does not own, frozen at construction.
_MAPPINGS = (
    "basis",
    "derived",
    "converted",
    "carried",
    "ranges",
    "reported",
    "unquantified",
    "uncertainty",
    "not_derivable",
    "misprinted",
    "attributed_to",
)


class CatalogueError(ValueError):
    """A catalogue that does not say what a reader needs to trust it.

    Raised for a table document that is missing what every table needs (a
    citation, an ``about``, rows, a key per row) and for a row whose cells
    contradict each other, such as a bound with no printed end. A
    :class:`ValueError`, because the data is wrong and not the call.
    """


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
    converted = fields.get("converted")
    if converted is not None:
        fields["converted"] = {name: tuple(pair) for name, pair in converted.items()}
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

    Every row of every published catalogue is one of these, a frozen and
    keyword-only dataclass. A subclass written to hold a quantity no
    catalogue of the library publishes is the same, and it leaves out
    ``slots=True``: on Python 3.13 a slotted dataclass that calls ``super()``
    without arguments, as a ``__post_init__`` does, raises :class:`TypeError`
    when it is built.

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
        stored as if it had been read, and it always follows again from the
        row's own cells. A value converted from the unit the page prints is
        not derived (:attr:`converted` holds it), and neither is one the page
        carries from another row (:attr:`carried` does).
    :ivar converted: Field to ``(figure, unit)``, the number and the unit the
        page prints, for a value this row holds in another unit. Ver and
        Beranek print their damping materials in degrees Fahrenheit and
        pounds per square inch, and the row holds degrees Celsius and
        pascals, so ``("3e5", "psi")`` sits beside a modulus in pascals. The
        figure is kept as the page writes it, so the cell can always be read
        back in the page's own terms.
    :ivar carried: Field to where the page carries it from, for a cell the
        page leaves blank because the value is printed once for a block of
        rows: a figure on the first row of a group, or "Parecido al
        anterior". The value is the page's, and this says which of its rows
        prints it.
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
    """

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
        self._check_range_ends()

    def _check_range_ends(self) -> None:
        """Refuse a range missing the end the page printed.

        The open side of a bound may be empty, because a quantity with no
        ceiling has nothing to put there. The printed side never may: a bound
        whose own number is missing would read back as a cell the page left
        blank, which is the one thing this class exists to tell apart.

        :raises CatalogueError: when a bound has no printed end, or when a
            two-sided interval is missing either of them.
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
                raise CatalogueError(msg)

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
            page prints in another unit, or prints on another row and leaves
            blank on this one, answers ``False``: the number is the page's,
            and :attr:`converted` or :attr:`carried` says so.
        """
        return field_name in self.derived

    def basis_of(self, field_name: str) -> str:
        """What the source says this field is: measured, declared, estimated.

        :param field_name: One of the field names of this class.
        :return: The field's own entry in :attr:`basis`, else the row's, else
            the empty string, which means the source does not say. Otherwise
            one of :data:`CATALOGUE_BASES`.
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
        if field_name in self.misprinted:
            return self.misprinted[field_name]
        if field_name in self.unquantified:
            return (
                f"the page prints “{self.unquantified[field_name]}” "
                f"where the number would be"
            )
        if field_name in self.not_derivable:
            return self.not_derivable[field_name]
        if field_name in self.ranges:
            low, high = self.ranges[field_name]
            if high is not None and field_name in self.bounded_above:
                return f"the page prints an upper bound of {high:g} and no value"
            if low is not None and field_name in self.bounded_below:
                return f"the page prints a lower bound of {low:g} and no value"
            if low is not None and high is not None:
                return f"the page prints {low:g} to {high:g} and no value"
        if field_name in self.reported:
            listed = ", ".join(_spell(entry) for entry in self.reported[field_name])
            return f"the page lists {listed} and no single value"
        return "the page does not give it, and it does not follow from the cells that it does"


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
    verb and says what comes back.
    """

    #: The band centre frequencies a table of this quantity can print, in
    #: hertz. A table prints a subset.
    _bands_hz: ClassVar[tuple[int, ...]] = ()
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

    def _in_band(self, band_hz: int) -> float:
        """One band of this row, or a refusal that says what the page had.

        :param band_hz: A centre frequency from the bands this class declares.
        :return: The printed value, as a float.
        :raises ValueError: when the page has no number in that band, naming
            the row, the band and what the cell held instead; or when
            *band_hz* is not a band these tables print.
        """
        if band_hz not in self._bands_hz:
            msg = (
                f"{band_hz} Hz is not {self._band_kind} band a "
                f"{self._table_kind} table prints; the bands are {self._bands_hz}"
            )
            raise ValueError(msg)
        return self.printed(
            self._band_field(band_hz), wanted_by=f"the {band_hz} Hz band"
        )
