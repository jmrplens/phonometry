#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The nonlinearity parameter of solids, as a handbook tabulates it.

The solid member of the family :data:`~phonometry.fluids.PUBLISHED_NONLINEARITY`
holds for liquids. In a solid the departure from linear elasticity is carried by
the third-order elastic constants, and Rossing writes the parameter for a
longitudinal wave along a pure-mode direction as

    beta = -(3 + K3 / K2)

with ``K2`` and ``K3`` the second- and third-order elastic coefficients of that
direction. The table gives it for eight solids at room temperature, each the
average over the three pure-mode directions of a cubic crystal.

Not the same number as B/A
--------------------------
The page's own comparison of the three states of matter gives this parameter
as ``gamma + 1`` for an ideal gas and ``B/A + 2`` for a liquid. So a solid's
``beta`` compares with a liquid's ``B/A + 2``, which is twice the coefficient
of nonlinearity ``1 + B/(2A)``, and not with the ``B/A`` of the fluids
catalogue: water's B/A of about 5 is a ``beta`` of about 7, next to the 5.6 of a
face-centred cubic metal here.

Five rows are structures, not materials
---------------------------------------
Zincblende, fluorite, face-centred cubic (metallic and inert-gas) and
body-centred cubic are crystal structures or bonding classes, and their value
is an average over the solids that share them. Only NaCl, fused silica and a
YBCO ceramic name a material. :attr:`SolidNonlinearity.bonding` carries the
bonding the page prints beside each.

Where the rows live
-------------------
In ``solids/data/rossing-2014-table-6-5.json``, read at import through the
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
    "PUBLISHED_SOLID_NONLINEARITY",
    "SolidNonlinearity",
    "solid_nonlinearity_named",
]


@dataclass(frozen=True, kw_only=True)
class SolidNonlinearity(CatalogueRow):
    """One solid's ultrasonic nonlinearity parameter, as a page printed it.

    :ivar nonlinearity_parameter: The page's ``beta_avg``, dimensionless:
        ``-(3 + K3/K2)`` averaged over the pure-mode directions [100], [110]
        and [111]. Comparable with ``B/A + 2`` of a liquid, not with ``B/A``.
    :ivar bonding: The bonding the page prints beside it, in its words:
        covalent, ionic, metallic, van der Waals or isotropic.
    """

    nonlinearity_parameter: float | None = None
    bonding: str = ""


#: The published tables this catalogue reads.
_TABLES = ("rossing-2014-table-6-5",)


def _load() -> dict[str, SolidNonlinearity]:
    """Every row of every packaged table, keyed by table and row."""
    out: dict[str, SolidNonlinearity] = {}
    for table in _TABLES:
        citation, rows = read_table("phonometry.solids", f"{table}.json")
        for row in rows:
            out[f"{table}/{row['key']}"] = SolidNonlinearity.from_printed(
                source=citation, table=table, **take(row)
            )
    return out


#: The nonlinearity parameters of solids this library has read from a page,
#: keyed ``"<table>/<row>"``: Rossing (2014) Table 6.5, PDF page 261 (printed
#: p. 244), eight solids at room temperature.
PUBLISHED_SOLID_NONLINEARITY: Mapping[str, SolidNonlinearity] = MappingProxyType(
    _load()
)


def solid_nonlinearity_named(name: str) -> tuple[SolidNonlinearity, ...]:
    """Every published solid whose printed name contains *name*.

    :param name: Part of the name as the page prints it, matched without
        regard to case: ``"fcc"`` answers with both face-centred cubic rows.
    :return: The matching rows, in the order the table lists them. Empty when
        nothing matches, which is not an error.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in PUBLISHED_SOLID_NONLINEARITY.values()
        if wanted in row.name.casefold()
    )
