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

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .._internal.catalogue import read_table, take
from .elastic import youngs_modulus_from_plate_speed

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_SOLIDS",
    "SolidMaterial",
]


@dataclass(frozen=True, kw_only=True)
class SolidMaterial:
    """One row of a published materials table, with what the cell said.

    :ivar name: The material as the table names it, attribution stripped.
    :ivar longitudinal_speed_m_s: Quasi-longitudinal phase velocity ``c_L``,
        in m/s. Hopkins' footnote a states these "can be used as estimates for
        beams or plates", so the column is the plate speed for the purposes of
        :func:`~phonometry.solids.youngs_modulus_from_plate_speed`.
    :ivar poisson_ratio: Poisson's ratio ``nu``.
    :ivar thickness_critical_frequency_product_m_hz: The ``h.f_c`` column, in
        m Hz, computed by the book for the 343 m/s its heading states.
    :ivar density_kg_m3: Density ``rho``, in kg/m3, or ``None`` when the table
        prints a range instead of a value. The range is then in :attr:`ranges`.
    :ivar loss_factor: Internal loss factor for bending waves ``eta_int``, or
        ``None`` when the table prints a dash, a range or an upper bound.
    :ivar estimated: The fields the page marks with its "Estimate" footnote.
        Reading one of these as a measurement is the mistake this catalogue
        exists to prevent.
    :ivar ranges: ``(low, high)`` for each field the table prints as an
        interval rather than a value.
    :ivar bounded_above: Fields the table prints as ``<= x``, with ``x`` in
        :attr:`ranges` as ``(0.0, x)``.
    :ivar attributed_to: Per-field credit, for the rows whose columns the book
        takes from different authors.
    :ivar note: What the table says about this row beyond its numbers.
    :ivar source: Document, table and PDF pages.
    """

    name: str
    source: str
    longitudinal_speed_m_s: float
    poisson_ratio: float
    thickness_critical_frequency_product_m_hz: float
    density_kg_m3: float | None = None
    loss_factor: float | None = None
    estimated: frozenset[str] = frozenset()
    ranges: Mapping[str, tuple[float, float]] = field(default_factory=dict)
    bounded_above: frozenset[str] = frozenset()
    attributed_to: Mapping[str, str] = field(default_factory=dict)
    note: str = ""

    def youngs_modulus_pa(self) -> float:
        """Young's modulus from the printed speed and density, in pascals.

        The table prints a wave speed and a density and no modulus, and the
        functions this library hands a solid to want the modulus, so the
        inversion happens here rather than in the caller's head. It is
        :func:`~phonometry.solids.youngs_modulus_from_plate_speed` on this
        row's own numbers.

        :return: Young's modulus ``E``, in pascals.
        :raises ValueError: for a row whose density the table printed as a
            range, because there is then no density to invert with.
        """
        if self.density_kg_m3 is None:
            low, high = self.ranges["density_kg_m3"]
            msg = (
                f"{self.name!r} has no single density: the table prints "
                f"{low:g} to {high:g} kg/m3, so a modulus follows only from a "
                "density you choose and can defend"
            )
            raise ValueError(msg)
        return youngs_modulus_from_plate_speed(
            self.longitudinal_speed_m_s,
            density_kg_m3=self.density_kg_m3,
            poisson_ratio=self.poisson_ratio,
        )

    def is_estimate(self, field_name: str) -> bool:
        """Whether the page marks this field as an estimate rather than a value.

        :param field_name: One of the numeric field names of this class.
        :return: ``True`` when the table carries its "Estimate" footnote there.
        """
        return field_name in self.estimated


_SOURCE, _ROWS = read_table("phonometry.solids", "hopkins-2007-table-a2.json")

#: Every row of Hopkins **Table A2**, in the order the page prints them,
#: read from ``solids/data/hopkins-2007-table-a2.json``. The two pages are
#: landscape and carry no printed folio of their own, which is why the citation
#: names the folios either side rather than inventing one. Two rows carry the
#: same material name at two densities, which is how the page prints them, so
#: the keys tell them apart by density rather than by a name the book does not
#: use.
PUBLISHED_SOLIDS: Mapping[str, SolidMaterial] = {
    row["key"]: SolidMaterial(
        source=_SOURCE,
        **take(row, frozen=("estimated", "bounded_above")),
    )
    for row in _ROWS
}
