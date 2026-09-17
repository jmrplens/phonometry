#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Solid materials as one published table prints them.

A caller who needs a Young's modulus for plasterboard has two bad options and
one good one. They can type a number they half remember, or they can open a
book and copy a row by hand into their script, which is the same thing with
extra steps. The good one is to read the row from a catalogue that says which
page it came from, and that is what this module is.

What it is careful about
------------------------
A materials table is not a list of measurements. Hopkins Table A2 marks most
of its Poisson ratios and internal loss factors with a footnote that reads,
in full, "Estimate", and it prints some of its densities as a range rather
than a number, some of its loss factors as an upper bound, and one of its wave
speeds with a note that the material is orthotropic and the figure quoted is
an effective value. A catalogue that flattened all of that into floats would
be claiming twenty-five measured Poisson ratios where the page offers four.

So every row carries what the cell actually said: :attr:`SolidMaterial.estimated`
names the fields the page marks as estimates, :attr:`SolidMaterial.ranges`
carries the seven cells printed as an interval (two densities, two speeds and
three loss factors), :attr:`SolidMaterial.bounded_above` names the two of those
loss factors the page prints as an upper bound rather than a band, and
:attr:`SolidMaterial.attributed_to` carries the per-cell credit for the rows
whose columns come from different authors. A field the table leaves
empty is ``None`` and not a guess.

Where the rows live
-------------------
In ``solids/data/hopkins-2007-table-a2.json``, one record per material, read
at import through the package-data reader in ``phonometry._internal``. Rows are
data: keeping them in a file means a second table is a second file rather than
a longer literal, means a changed digit is one line of a diff, and means the
citation is written once, in the file that holds the rows it belongs to. The
provenance gate reads it from there too, so the comment above the constant and
the page it names cannot drift apart.

What it is not
--------------
It is not a specification. Block densities vary by manufacturer, boards vary
by batch, and Hopkins says as much by printing ranges where a range is what is
known. Use a row to reproduce a worked example, to sanity-check a measurement,
or to get an order of magnitude; use a measurement for anything that has to be
right.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from .._internal.catalogue import read_table, take
from .elastic import (
    beam_longitudinal_speed,
    bulk_longitudinal_speed,
    plate_longitudinal_speed,
    thickness_critical_frequency_product,
    youngs_modulus_from_beam_speed,
    youngs_modulus_from_plate_speed,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_SOLIDS",
    "SolidMaterial",
    "solids_named",
]


@dataclass(frozen=True, kw_only=True)
class SolidMaterial:
    """One row of a published materials table, with what the cell said.

    Every quantity is optional, because no two of the books this catalogue
    reads print the same columns: Hopkins gives a plate speed and no modulus,
    Mechel a modulus and no speed, Cremer both plus a shear modulus, Arau
    neither. A field is ``None`` when the page had nothing to put there, and
    :meth:`why_missing` says what it had instead.

    **The three longitudinal speeds are three fields**, because they are three
    different waves and the books do not agree on what to call them. Cremer's
    ``c_LII`` and Bies' ``sqrt(E/rho)`` are the bar speed; Hopkins'
    quasi-longitudinal is the plate speed; and the bulk speed is neither. At
    ``nu = 0.3`` the plate speed is 4.8 per cent above the bar speed and the
    bulk speed is 16 per cent above it, which is the figure Cremer prints
    under his Eq. (3.32) with the warning that it matters which one is meant.
    One field holding whichever the page happened to print is the mistake this
    catalogue exists to prevent, so there is no such field.

    **The loss factors are three fields** for the same reason. A flexural loss
    factor is measured in bending and a longitudinal one is not; an in-situ
    one is not a property of the material at all, but of a panel installed in
    a building, support and radiation included.

    :ivar name: The material as the table names it, attribution stripped.
    :ivar variant: Which specimen or condition this row is, when the page
        prints several under one name: ``"chemically pure"``, ``"single
        crystal"``, ``"13 C, 11 per cent bituminous content"``. Empty when the
        page prints one.
    :ivar source: Document, table, PDF page and printed folio.
    :ivar table: The data file this row was read from, without the
        extension, which is also the first half of its key in
        :data:`PUBLISHED_SOLIDS`.
    :ivar density_kg_m3: Density ``rho``, in kg/m3.
    :ivar youngs_modulus_pa: Young's modulus ``E``, in pascals.
    :ivar shear_modulus_pa: Shear modulus ``G``, in pascals.
    :ivar poisson_ratio: Poisson's ratio ``nu``.
    :ivar bar_longitudinal_speed_m_s: ``sqrt(E/rho)``, the quasi-longitudinal
        speed on a rod, in m/s.
    :ivar plate_longitudinal_speed_m_s: ``sqrt(E/(rho(1-nu^2)))``, the
        quasi-longitudinal speed on a plate, in m/s.
    :ivar bulk_longitudinal_speed_m_s: the pure longitudinal speed in an
        unbounded solid, in m/s.
    :ivar transverse_speed_m_s: ``sqrt(G/rho)``, the shear wave speed, in m/s.
    :ivar flexural_loss_factor: Internal loss factor measured in bending.
    :ivar longitudinal_loss_factor: Internal loss factor measured with
        longitudinal waves.
    :ivar in_situ_loss_factor: Loss factor of a panel of this material as
        installed, which combines the internal, support and radiation losses
        and is therefore not a material constant.
    :ivar thickness_critical_frequency_product_m_hz: The ``h.f_c`` column, in
        m Hz, a property of the material alone and the cheapest cross-check
        there is between books that share no other column.
    :ivar estimated: Fields the page marks as an estimate rather than a
        measurement. Reading one of these as a measurement is the mistake this
        catalogue exists to prevent.
    :ivar approximate: Fields the page prints with a ``~``. Not an estimate
        and not an interval: a number the author rounded on purpose.
    :ivar derived: Field to how it was computed, for the ones this library
        worked out from the cells the page did print. A derived value is never
        stored as if it had been read.
    :ivar borrowed: Field to the material it was taken from, for the cells a
        book fills from a similar material rather than leaving empty.
    :ivar ranges: ``(low, high)`` for each field the page prints as an
        interval rather than a value.
    :ivar bounded_above: The subset of :attr:`ranges` the page prints as
        ``< x`` or ``<= x``, where the low end is a floor and not a
        measurement.
    :ivar unquantified: Field to what the page said in place of a number, for
        a cell that is neither empty nor numeric: ``"varies with frequency"``.
    :ivar attributed_to: Credit for a cell the book takes from someone else.
        Keyed by field name, or by ``"row"`` or ``"table"`` when the credit
        covers all of one.
    :ivar note: What the page says about this row beyond its numbers.
    """

    name: str
    source: str
    table: str = ""
    variant: str = ""
    density_kg_m3: float | None = None
    youngs_modulus_pa: float | None = None
    shear_modulus_pa: float | None = None
    poisson_ratio: float | None = None
    bar_longitudinal_speed_m_s: float | None = None
    plate_longitudinal_speed_m_s: float | None = None
    bulk_longitudinal_speed_m_s: float | None = None
    transverse_speed_m_s: float | None = None
    flexural_loss_factor: float | None = None
    longitudinal_loss_factor: float | None = None
    in_situ_loss_factor: float | None = None
    thickness_critical_frequency_product_m_hz: float | None = None
    estimated: frozenset[str] = frozenset()
    approximate: frozenset[str] = frozenset()
    derived: Mapping[str, str] = field(default_factory=dict)
    borrowed: Mapping[str, str] = field(default_factory=dict)
    ranges: Mapping[str, tuple[float, float]] = field(default_factory=dict)
    bounded_above: frozenset[str] = frozenset()
    unquantified: Mapping[str, str] = field(default_factory=dict)
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
        for name in ("derived", "borrowed", "ranges", "unquantified", "attributed_to"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

    def is_estimate(self, field_name: str) -> bool:
        """Whether the page marks this field as an estimate rather than a value.

        :param field_name: One of the numeric field names of this class.
        :return: ``True`` when the page carries an estimate footnote there.
        """
        return field_name in self.estimated

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
            return self.unquantified[field_name]
        if field_name in self.ranges:
            low, high = self.ranges[field_name]
            if field_name in self.bounded_above:
                return f"the page prints an upper bound of {high:g} and no value"
            return f"the page prints {low:g} to {high:g} and no value"
        return "the page does not give it, and it does not follow from the cells that it does"


#: How a field this library computed is described in
#: :attr:`SolidMaterial.derived`. The wording names the cells it came from, so
#: a reader of a derived number can go back to the ones that were read.
_FROM_PLATE = "from the plate speed, the density and the Poisson ratio"
_FROM_BAR = "from the bar speed and the density"
_FROM_MODULUS = "from the modulus and the density"
_FROM_MODULUS_NU = "from the modulus, the density and the Poisson ratio"
_FROM_SHEAR = "from the shear modulus and the density"
_FROM_E_G = "from the modulus and the shear modulus"
_FROM_E_NU = "from the modulus and the Poisson ratio"
_PLATE_HFC = "from the plate speed, for the 343 m/s the heading assumes"

#: The one field name long enough to be worth a shorthand.
_HFC = "thickness_critical_frequency_product_m_hz"


def _fill(fields: dict[str, Any], name: str, value: float, how: str) -> None:
    """Record *value* under *name*, and that it was computed and not read."""
    fields[name] = value
    fields.setdefault("derived", {})
    fields["derived"] = {**fields["derived"], name: how}


def _elastic_constants(fields: dict[str, Any]) -> None:
    """Fill the modulus, the shear modulus and the Poisson ratio.

    Any two of them give the third, and a speed with a density gives the
    modulus, so a page that prints a speed and a density has printed a modulus
    without writing it down.
    """
    rho = fields.get("density_kg_m3")
    nu = fields.get("poisson_ratio")
    modulus = fields.get("youngs_modulus_pa")
    shear = fields.get("shear_modulus_pa")
    plate = fields.get("plate_longitudinal_speed_m_s")
    bar = fields.get("bar_longitudinal_speed_m_s")

    if modulus is None and rho is not None:
        if plate is not None and nu is not None:
            _fill(
                fields,
                "youngs_modulus_pa",
                youngs_modulus_from_plate_speed(
                    plate, density_kg_m3=rho, poisson_ratio=nu
                ),
                _FROM_PLATE,
            )
        elif bar is not None:
            _fill(
                fields,
                "youngs_modulus_pa",
                youngs_modulus_from_beam_speed(bar, density_kg_m3=rho),
                _FROM_BAR,
            )
        modulus = fields.get("youngs_modulus_pa")
    if nu is None and modulus is not None and shear is not None:
        _fill(fields, "poisson_ratio", modulus / (2.0 * shear) - 1.0, _FROM_E_G)
    elif shear is None and modulus is not None and nu is not None:
        _fill(fields, "shear_modulus_pa", modulus / (2.0 * (1.0 + nu)), _FROM_E_NU)


def _wave_speeds(fields: dict[str, Any]) -> None:
    """Fill the three longitudinal speeds and the transverse one.

    A page prints the wave its author needed and the reader needs another, so
    every row ends up carrying all four: the one that was read, and the ones
    that follow from the row's own cells.
    """
    rho = fields.get("density_kg_m3")
    nu = fields.get("poisson_ratio")
    modulus = fields.get("youngs_modulus_pa")
    shear = fields.get("shear_modulus_pa")

    if rho is not None and modulus is not None:
        if fields.get("bar_longitudinal_speed_m_s") is None:
            _fill(
                fields,
                "bar_longitudinal_speed_m_s",
                beam_longitudinal_speed(modulus, density_kg_m3=rho),
                _FROM_MODULUS,
            )
        if nu is not None and fields.get("plate_longitudinal_speed_m_s") is None:
            _fill(
                fields,
                "plate_longitudinal_speed_m_s",
                plate_longitudinal_speed(modulus, density_kg_m3=rho, poisson_ratio=nu),
                _FROM_MODULUS_NU,
            )
        if nu is not None and fields.get("bulk_longitudinal_speed_m_s") is None:
            _fill(
                fields,
                "bulk_longitudinal_speed_m_s",
                bulk_longitudinal_speed(modulus, density_kg_m3=rho, poisson_ratio=nu),
                _FROM_MODULUS_NU,
            )
    if (
        rho is not None
        and shear is not None
        and fields.get("transverse_speed_m_s") is None
    ):
        _fill(fields, "transverse_speed_m_s", math.sqrt(shear / rho), _FROM_SHEAR)


def _complete(fields: dict[str, Any]) -> dict[str, Any]:
    """Fill what follows from the cells the page printed.

    A materials table prints the columns its author needed, and the next
    reader needs others. Hopkins gives a plate speed and no modulus, Cremer a
    modulus and a bar speed and no plate speed, and comparing the two means
    converting one into the other. Doing it here, once, beats every caller
    doing it in their head, which is the conversion :mod:`phonometry.solids`
    was added for.

    Nothing is filled over a cell the page printed, and nothing is filled from
    a cell the page printed as a range: a modulus from the midpoint of a
    density the book declined to collapse would be a number nobody published.
    Every value filled here is named in :attr:`SolidMaterial.derived`.

    :param fields: One row as the data file wrote it.
    :return: The same row with the derivable quantities added.
    """
    _elastic_constants(fields)
    _wave_speeds(fields)
    plate = fields.get("plate_longitudinal_speed_m_s")
    if plate is not None and fields.get(_HFC) is None:
        _fill(fields, _HFC, thickness_critical_frequency_product(plate), _PLATE_HFC)
    return fields


#: The row fields the data files write as a list and the row holds as a set.
_SETS = ("estimated", "approximate", "bounded_above")

#: The published tables this catalogue reads, in the order a reader should
#: meet them: the one whose columns the library was built around first, then
#: the one that over-determines the elastic constants and so checks it.
_TABLES = (
    "hopkins-2007-table-a2",
    "cremer-2005-table-4-3",
)


def _load() -> dict[str, SolidMaterial]:
    """Every row of every packaged table, keyed by table and row.

    The key names the table because the catalogue holds several books and
    they do not agree. Hopkins and Cremer both print a row called Steel, at
    the same density, with plate speeds that differ by four per cent and
    Poisson ratios that differ by three. A flat ``"steel"`` would have to pick
    one of them silently, and picking silently between two published values is
    the thing a catalogue exists not to do.
    """
    rows: dict[str, SolidMaterial] = {}
    for table in _TABLES:
        source, records = read_table("phonometry.solids", f"{table}.json")
        for record in records:
            fields = _complete(take(record, frozen=_SETS))
            rows[f"{table}/{record['key']}"] = SolidMaterial(
                table=table, source=source, **fields
            )
    return rows


#: Every solid this library has read from a published page, keyed
#: ``"<table>/<row>"``: ``"hopkins-2007-table-a2/steel"`` and
#: ``"cremer-2005-table-4-3/steel"`` are two different published steels and
#: the key says which is which. The tables are
#: ``solids/data/hopkins-2007-table-a2.json``, Hopkins **Table A2** on PDF
#: pages 635-636, and ``solids/data/cremer-2005-table-4-3.json``, Cremer
#: **Table 4.3** on PDF page 201. Use :func:`solids_named` to gather every
#: book's reading of one material.
PUBLISHED_SOLIDS: Mapping[str, SolidMaterial] = MappingProxyType(_load())


def solids_named(name: str) -> tuple[SolidMaterial, ...]:
    """Every published row for a material, across the books.

    Comparing two books is the point of holding both, and it has to be a
    deliberate act: a lookup that returned one row for "steel" would be
    choosing between published values on the caller's behalf.

    :param name: The material name as a table prints it, matched without
        regard to case: ``"Steel"``, ``"steel"``.
    :return: The rows whose :attr:`SolidMaterial.name` matches, in the order
        the tables are read, which is empty when no page names it.
    """
    wanted = name.casefold()
    return tuple(
        row for row in PUBLISHED_SOLIDS.values() if row.name.casefold() == wanted
    )
