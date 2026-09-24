#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Wood, which is not the same material in two directions.

Every other solid this library holds is isotropic: one Young's modulus, one
Poisson ratio, one speed, and the material behaves the same whichever way the
wave runs through it. That is a good description of steel and a poor one of
wood. A spruce plate is stiff along the grain and limp across it, by a factor
of thirteen in the rows below, and an instrument maker chooses the wood and
cuts the plate precisely because of that difference. Averaging it away leaves
a number that describes no direction at all.

So this catalogue does not hold a modulus. It holds the four elastic
constants of a thin orthotropic plate, as Rossing tabulates them for the two
woods a stringed instrument is made of, and as his equation (15.86) defines
them, with :math:`\mu = 1 - \nu_{xy}\nu_{yx}`:

  D1 = Ex / 12 mu            along the grain
  D2 = nu_xy Ey / 6 mu       the coupling between the two directions
  D3 = Ey / 12 mu            across the grain
  D4 = Gxy / 3               the twisting stiffness

They are in pascals, the page prints them in megapascals, but they are not
moduli: D1 is the along-grain modulus divided by twelve (and by mu), so it is
not interchangeable with
:attr:`~phonometry.solids.SolidMaterial.youngs_modulus_pa`, and the plate's
thickness is not inside any of them: it enters the modal frequencies
separately, through Rossing's equation (15.87). A caller who wants the
isotropic reading of a wood will find fir and spruce in the solids catalogue,
from three other books, and should not expect the two to agree: they are not
measuring the same thing.

The page is printed the other way round
---------------------------------------
Rossing sets the woods as the columns and the properties as the rows, which is
the natural way to print two materials and six properties. Every catalogue in
this library is keyed by the thing described, so the table is turned when it is
read: a wood is a row here. Nothing else is changed.

What the asterisks mean
-----------------------
Two of maple's four constants carry an asterisk, and the table's caption
calls the asterisked values "intelligent guesses in the absence of
experimental data". They are served, because the page prints them as numbers
and a reader who wants the author's best estimate should have it, but each
holds ``"estimated"`` in :attr:`OrthotropicWood.basis`, and
:meth:`~phonometry.io.CatalogueRow.basis_of` answers for them, so that a
caller who wants measurements can tell the two apart without reading the
caption.

Where the rows live
-------------------
In ``solids/data/rossing-2014-table-15-5.json``, read at import through the
package-data reader in ``phonometry._internal``, the same as every other
catalogue here.
"""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True, kw_only=True)
class OrthotropicWood(CatalogueRow):
    """One wood's plate stiffnesses, as a page printed them.

    A constant the caption calls an intelligent guess holds ``"estimated"``
    in :attr:`~phonometry.io.CatalogueRow.basis`, which
    :meth:`~phonometry.io.CatalogueRow.basis_of` reads.

    :ivar density_kg_m3: Density, in kg/m3.
    :ivar plate_stiffness_d1_pa: D1 = Ex/12mu, along the grain, in pascals.
    :ivar plate_stiffness_d2_pa: D2 = nu_xy Ey/6mu, the Poisson coupling
        between the two directions, in pascals.
    :ivar plate_stiffness_d3_pa: D3 = Ey/12mu, across the grain, in pascals.
    :ivar plate_stiffness_d4_pa: D4 = Gxy/3, the twisting stiffness, in
        pascals: the only term of the plate's energy a pure twisting mode
        involves.
    :ivar relative_scaling_factor: The fourth root of D1 over D3, which the
        page prints for each wood: how much wider across the grain a plate of
        this wood behaves than it is, if its flexural vibrations are read as
        those of an equivalent isotropic plate. Rossing puts it at "almost
        double the relative width" for a violin's spruce front plate. It
        scales one wood's two directions, not one wood against the other.
        Dimensionless.
    """

    density_kg_m3: float | None = None
    plate_stiffness_d1_pa: float | None = None
    plate_stiffness_d2_pa: float | None = None
    plate_stiffness_d3_pa: float | None = None
    plate_stiffness_d4_pa: float | None = None
    relative_scaling_factor: float | None = None


#: The published tables this catalogue reads, in the order it reads them.
_TABLES = ("rossing-2014-table-15-5",)


def _load() -> dict[str, OrthotropicWood]:
    """Every row of every packaged table, keyed by table and row."""
    out: dict[str, OrthotropicWood] = {}
    for table in _TABLES:
        citation, rows = read_table("phonometry.solids", f"{table}.json")
        for row in rows:
            out[f"{table}/{row['key']}"] = OrthotropicWood(
                source=citation, table=table, **take(row)
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
