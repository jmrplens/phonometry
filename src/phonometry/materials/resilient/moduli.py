#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The dynamic modulus of resilient materials, as a textbook tabulates it.

A floating floor is a mass on a spring, and the spring is a layer of mineral
wool, foam or cork. What a designer needs of that layer is its dynamic
stiffness per unit area ``s'``, which :mod:`phonometry.materials.resilient`
measures by EN 29052-1 and which :data:`PUBLISHED_RESILIENT_LAYERS` holds for
fifteen measured specimens of known thickness. A table of materials cannot
give ``s'``, because ``s'`` belongs to a layer of one thickness; what it can
give is the modulus the layer is made of, from which

.. math::

   s' = \frac{E_\mathrm{dyn}}{d}

for a layer of thickness ``d``. This module holds those moduli.

A modulus under a load
----------------------
The dynamic modulus of a fibrous or cellular layer is not a constant of the
material. It rises with the static load the layer carries, because the fibres
or the cell walls are pressed together, and the table says so in its heading:
every value is measured under a static load of about 2 kPa, which is on every
row as :attr:`ResilientMaterial.static_load_pa`. The text above the table puts
numbers on it: rock wool of 150 to 175 kg/m3 is about 0.3 MPa at 2 kPa, about
20 per cent lower at 1 kPa and about 30 per cent higher at 4 kPa. A screed of
50 mm of concrete is about 1.2 kPa; a caller with a much heavier or lighter
floor is outside the condition these numbers were measured in.

The page prints every modulus as a range and all but one density as a range,
and they are held as ranges: a floor built on "rock wool" could sit anywhere in
them, and the catalogue does not pick a point.

Where the rows live
-------------------
In ``materials/resilient/data/vigran-2008-table-8-3.json``, read at import
through the package-data reader in ``phonometry._internal``, the same as every
other catalogue in this library.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from ..._internal.catalogue import CatalogueRow, read_table, take

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_RESILIENT_MODULI",
    "ResilientMaterial",
    "resilient_moduli_named",
]


@dataclass(frozen=True, kw_only=True)
class ResilientMaterial(CatalogueRow):
    """One resilient material's dynamic modulus, as a page printed it.

    :ivar density_kg_m3: Density, in kg/m3. Printed as a range on most rows,
        which :attr:`~phonometry.io.CatalogueRow.ranges`
        holds.
    :ivar dynamic_youngs_modulus_pa: The dynamic modulus of elasticity of the
        material under :attr:`static_load_pa`, in pascals. Printed as a range on
        every row. Divided by a layer's thickness it is that layer's dynamic
        stiffness per unit area ``s'``.
    :ivar static_load_pa: The static load the modulus was measured under, in
        pascals. The page prints it once, in the heading, as about 2 kPa.
    """

    density_kg_m3: float | None = None
    dynamic_youngs_modulus_pa: float | None = None
    static_load_pa: float | None = None


#: The published tables this catalogue reads.
_TABLES = ("vigran-2008-table-8-3",)


def _load() -> dict[str, ResilientMaterial]:
    """Every row of every packaged table, keyed by table and row."""
    out: dict[str, ResilientMaterial] = {}
    for table in _TABLES:
        citation, rows = read_table("phonometry.materials.resilient", f"{table}.json")
        for row in rows:
            out[f"{table}/{row['key']}"] = ResilientMaterial(
                source=citation, table=table, **take(row)
            )
    return out


#: The dynamic moduli of resilient materials this library has read from a
#: page, keyed ``"<table>/<row>"``: Vigran (2008) Table 8.3, PDF page 339
#: (printed p. 318), six materials under a static load of about 2 kPa.
PUBLISHED_RESILIENT_MODULI: Mapping[str, ResilientMaterial] = MappingProxyType(_load())


def resilient_moduli_named(name: str) -> tuple[ResilientMaterial, ...]:
    """Every published resilient material whose name contains *name*.

    :param name: Part of a material name as the page prints it, matched without
        regard to case: ``"rock wool"`` answers with both of Vigran's rock
        wools, which only their densities tell apart.
    :return: The matching rows, in the order the table lists them. Empty when
        nothing matches, which is not an error.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in PUBLISHED_RESILIENT_MODULI.values()
        if wanted in row.name.casefold()
    )
