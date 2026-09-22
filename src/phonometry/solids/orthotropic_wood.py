#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Wood, which is not the same material in two directions.

Every other solid this library holds is isotropic: one Young's modulus, one
Poisson ratio, one speed, and the material behaves the same whichever way the
wave runs through it. That is a good description of steel and a poor one of
wood. A spruce plate is stiff along the grain and limp across it, by a factor
of sixteen in the rows below, and an instrument maker chooses the wood and
cuts the plate precisely because of that difference. Averaging it away leaves
a number that describes no direction at all.

So this catalogue does not hold a modulus. It holds the four plate stiffnesses
that a thin orthotropic plate actually has, as Rossing tabulates them for the
two woods a stringed instrument is made of:

  D1  along the grain
  D2  across the grain
  D3  the twisting stiffness
  D4  the coupling term between the two in-plane directions

They are stiffnesses of a plate, not moduli of a material: the page prints
them in megapascals and they are held in pascals, but they already carry the
plate's thickness inside them, which is why they are not interchangeable with
:attr:`~phonometry.solids.SolidMaterial.youngs_modulus_pa`. A caller who wants
the isotropic reading of a wood will find fir and spruce in the solids
catalogue, from three other books, and should not expect the two to agree:
they are not measuring the same thing.

The page is printed the other way round
---------------------------------------
Rossing sets the woods as the columns and the properties as the rows, which is
the natural way to print two materials and six properties. Every catalogue in
this library is keyed by the thing described, so the table is turned when it is
read: a wood is a row here. Nothing else is changed.

What the asterisks mean
-----------------------
Two of maple's four stiffnesses carry an asterisk, and the table's own footnote
calls the asterisked values "intelligent guesses in the absence of experimental
data". They are served, because the page prints them as numbers and a reader
who wants the author's best estimate should have it, but
:attr:`OrthotropicWood.is_estimated` answers for them so that a caller who
wants measurements can tell the two apart without reading the footnote.

Where the rows live
-------------------
In ``solids/data/rossing-2014-table-15-5.json``, read at import through the
package-data reader in ``phonometry._internal``, the same as every other
catalogue here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING

from .._internal.catalogue import CatalogueRow, read_table, take

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_ORTHOTROPIC_WOOD",
    "OrthotropicWood",
    "orthotropic_wood_named",
]


@dataclass(frozen=True, slots=True)
class OrthotropicWood(CatalogueRow):
    """One wood's plate stiffnesses, as a page printed them.

    :ivar density_kg_m3: Density, in kg/m3.
    :ivar plate_stiffness_d1_pa: Plate stiffness along the grain, in pascals.
    :ivar plate_stiffness_d2_pa: Plate stiffness across the grain, in pascals.
    :ivar plate_stiffness_d3_pa: Twisting stiffness, in pascals.
    :ivar plate_stiffness_d4_pa: The in-plane coupling term, in pascals.
    :ivar relative_scaling_factor: The fourth root of D1 over D3, which the
        page prints as a scaling factor between the two woods. Dimensionless.
    :ivar estimated: Fields the page marks as the author's estimate rather
        than a measurement. :meth:`is_estimated` reads it.
    """

    density_kg_m3: float | None = None
    plate_stiffness_d1_pa: float | None = None
    plate_stiffness_d2_pa: float | None = None
    plate_stiffness_d3_pa: float | None = None
    plate_stiffness_d4_pa: float | None = None
    relative_scaling_factor: float | None = None
    estimated: frozenset[str] = field(default_factory=frozenset)

    def is_estimated(self, field_name: str) -> bool:
        """Whether the page marked this field as an estimate.

        :param field_name: The attribute name, as ``plate_stiffness_d2_pa``.
        :return: ``True`` when the page's own footnote calls the value a guess
            rather than a measurement.
        """
        return field_name in self.estimated


#: The published tables this catalogue reads, in the order it reads them.
_TABLES = ("rossing-2014-table-15-5",)

#: The row fields that arrive as a list and are held as a set.
_SETS = ("estimated",)


def _load() -> dict[str, OrthotropicWood]:
    """Every row of every packaged table, keyed by table and row."""
    out: dict[str, OrthotropicWood] = {}
    for table in _TABLES:
        citation, rows = read_table("phonometry.solids", f"{table}.json")
        for row in rows:
            out[f"{table}/{row['key']}"] = OrthotropicWood(
                source=citation, table=table, **take(row, frozen=_SETS)
            )
    return out


#: The orthotropic woods this library has read from a published page, keyed
#: ``"<table>/<row>"``. Each row names the page it was read on.
PUBLISHED_ORTHOTROPIC_WOOD: Mapping[str, OrthotropicWood] = MappingProxyType(_load())


def orthotropic_wood_named(name: str) -> tuple[OrthotropicWood, ...]:
    """Every row whose printed name contains *name*, case insensitively.

    :param name: Part of a wood's name, as the page prints it.
    :return: The matching rows, in the order the tables list them. Empty when
        nothing matches, which is not an error.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in PUBLISHED_ORTHOTROPIC_WOOD.values()
        if wanted in row.name.casefold()
    )
