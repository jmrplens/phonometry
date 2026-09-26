#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The nonlinearity parameter B/A of liquids, as a handbook tabulates it.

Sound in a fluid is linear only in the limit of a vanishing amplitude. At a
finite one the pressure is not proportional to the change in density, and the
first term of the departure is what B/A measures. Expanding the adiabatic
pressure in the condensation ``s = (rho - rho0) / rho0`` gives
``p - p0 = A s + (B/2) s**2 + ...``, with ``A = rho0 (dp/drho)_s``, which is
``rho0 c0**2``, and ``B = rho0**2 (d2p/drho2)_s``: Rossing's equations (8.7) to
(8.9). B/A is the ratio of those two, dimensionless. It sets how fast a finite wave steepens towards a shock, how
strongly two beams generate their sum and difference frequencies, and with it
the output of a parametric array; the coefficient of nonlinearity is
``1 + B/(2A)``. In the rows below water sits between 4.2 and 6.2, the organic
liquids mostly between 6 and 12, the liquid metals between 2.7 and 7.8, and
air, for comparison, is 0.4 because an ideal gas has ``B/A = gamma - 1``.

What the rows are
-----------------
Each row is one published value: a substance, the temperature it was measured
at, the value, and the paper it comes from. Three of Rossing's tables print a
reference beside every value and the fourth credits one paper in its caption,
and that is not decoration: at 30 °C water
prints four values between 5.18 and 5.38 from four papers, and toluene prints
5.6 at 20 °C from one paper and 8.929 at 30 °C from another. A caller who
wants "the" B/A of a liquid has to choose, and the row carries in
:attr:`~phonometry.io.CatalogueRow.attributed_to` the full
reference the chapter's list gives for that number, so that the choice can be
made on the paper and not on the digits. Where the page prints a
plus-or-minus beside the value it is in
:attr:`~phonometry.io.CatalogueRow.uncertainty`.

Table 8.2 is the only one that prints a pressure, from 0.1 to 50 MPa, and its
rows carry it; the other three say "at atmospheric pressure" in the caption and
print no number, so their rows hold none rather than a 101 325 Pa the page did
not write. For six of the liquefied gases of Table 8.4 the caption cannot be
right: they are above their normal boiling point, liquid only under a pressure
the page does not give, and their rows say so.

What it is not
--------------
It is not a model. Nothing here interpolates between two temperatures or
between two papers, and no function in this library computes B/A from a sound
speed yet; a caller who needs a value at 25 °C where the table prints 20 and 30
has to decide how, and between which references.

Where the rows live
-------------------
In ``fluids/data/rossing-2014-table-8-1.json`` to ``-8-4.json``, one file per
printed table, read at import through the package-data reader in
``phonometry._internal``, the same as every other catalogue here.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from .._internal.catalogue import (
    CatalogueRow,
    read_table,
    rows_to_search,
    search_text,
    take,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_NONLINEARITY",
    "NonlinearityParameter",
    "nonlinearity_named",
]


@dataclass(frozen=True, kw_only=True)
class NonlinearityParameter(CatalogueRow):
    """One published value of B/A, with the conditions it was measured at.

    :ivar b_over_a: The nonlinearity parameter B/A. Dimensionless.
    :ivar temperature_c: The temperature the value was measured at, in degrees
        Celsius. Table 8.2 prints it in kelvin and it is converted at 273.15 K
        exactly; the liquefied gases of Table 8.4 are far below zero and are
        held as the negative temperatures the page prints.
    :ivar static_pressure_pa: The static pressure the value was measured at, in
        pascals, on the rows of the one table that prints it. Empty on every
        other row, whose caption says atmospheric pressure without a number.
    :ivar year: The year the page prints beside the value, on the rows of the
        one table that prints one; it is the year of the row's reference. Six
        rows print a year their reference contradicts and serve none.
    """

    b_over_a: float | None = None
    temperature_c: float | None = None
    static_pressure_pa: float | None = None
    year: int | None = None


#: The published tables this catalogue reads, in the order the page prints
#: them.
_TABLES = (
    "rossing-2014-table-8-1",
    "rossing-2014-table-8-2",
    "rossing-2014-table-8-3",
    "rossing-2014-table-8-4",
)


def _load() -> dict[str, NonlinearityParameter]:
    """Every row of every packaged table, keyed by table and row."""
    out: dict[str, NonlinearityParameter] = {}
    for table in _TABLES:
        citation, rows = read_table("phonometry.fluids", f"{table}.json")
        for row in rows:
            out[f"{table}/{row['key']}"] = NonlinearityParameter.from_printed(
                source=citation, table=table, **take(row)
            )
    return out


#: Every published value of B/A this library has read from a page, keyed
#: ``"<table>/<row>"``: Rossing (2014) Tables 8.1 and 8.2, PDF page 284
#: (printed p. 268), and Tables 8.3 and 8.4, PDF page 285 (printed p. 269).
#: Each row names its page, and the paper its value comes from.
PUBLISHED_NONLINEARITY: Mapping[str, NonlinearityParameter] = MappingProxyType(_load())


def nonlinearity_named(
    name: str, *, catalogue: Mapping[str, NonlinearityParameter] | None = None
) -> tuple[NonlinearityParameter, ...]:
    """Every value whose substance name contains *name*.

    :param name: Part of a substance's name as the page prints it, matched
        without regard to case: ``"water"`` answers with every row of Tables 8.1
        and 8.2 and with the sea water of Table 8.4.
    :param catalogue: The rows to search in place of
        :data:`PUBLISHED_NONLINEARITY`: a catalogue of your own that
        :func:`phonometry.io.read_catalogue` returns, ``PUBLISHED_NONLINEARITY
        | mine`` to search both at once, or any mapping of key to row (Default:
        ``None``, which searches :data:`PUBLISHED_NONLINEARITY`).
    :return: The matching rows, in catalogue order. Empty when nothing
        matches, which is not an error.
    :raises TypeError: for a *catalogue* that is not a mapping, or that holds a
        row that is not a :class:`NonlinearityParameter`, naming its key.
    """
    wanted = search_text(name)
    return tuple(
        row
        for row in rows_to_search(
            catalogue,
            PUBLISHED_NONLINEARITY,
            NonlinearityParameter,
            "nonlinearity_named",
        )
        if wanted in search_text(row.name)
    )
