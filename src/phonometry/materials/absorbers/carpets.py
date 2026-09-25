#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Carpets, rated by their noise reduction coefficient and described by their pile.

A carpet is the one absorber most rooms already have, and what it absorbs
depends less on the fibre than on how much pile there is and what it is laid
on: the chapter's own text says the type of fibre, nylon or wool, has no
significant effect on the absorption. Two tables of Harris say so side by side: carpets on bare concrete and
carpets on a hair pad, with the pile's weight, height, surface and fibre
beside a single number, the noise reduction coefficient: 0.25 to 0.55 on
concrete, 0.40 to 0.70 on the pad.

What the number is
------------------
The noise reduction coefficient, :attr:`Carpet.noise_reduction_coefficient`, is
the arithmetic mean of the sound absorption coefficients at 250, 500, 1000 and
2000 Hz rounded to the nearest 0.05. It is one number for four bands, so no
band can be recovered from it, and a carpet rated 0.50 may absorb very little
at 125 Hz. The measured absorption of materials band by band is in
:data:`~phonometry.materials.absorbers.PUBLISHED_ABSORPTION`.

What the page got wrong
-----------------------
The pile weight is printed twice, in kg/m2 and in oz/yd2, and five of the
eleven pairs of Table 30.2 are not each other. Three follow from the imperial
half at 0.035 kg/m2 per oz/yd2 instead of the 0.033906 of the definition, one
follows at neither, and one has lost a digit of its imperial half to a decimal
comma. They are registered in ``docs/ERRATA.md``; the four whose kilograms are
in doubt serve no pile weight and say why, and the fifth serves its kilograms,
which Table 30.3 confirms.

Where the rows live
-------------------
In ``materials/absorbers/data/harris-1995-table-30-2.json`` and
``-30-3.json``, read at import through the package-data reader in
``phonometry._internal``, the same as every other catalogue here.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from ..._internal.catalogue import CatalogueRow, read_table, rows_to_search, take

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_CARPETS",
    "Carpet",
    "carpets_named",
]


@dataclass(frozen=True, kw_only=True)
class Carpet(CatalogueRow):
    """One carpet as a page printed it: its pile, what it is laid on, and its NRC.

    The :attr:`~phonometry.io.CatalogueRow.name` is the
    construction the page prints, woven, knitted or knotted, and the
    :attr:`~phonometry.io.CatalogueRow.variant` is the pile
    surface and the fibre, which is what tells two rows of one construction
    apart.

    :ivar pile_weight_kg_m2: The weight of the pile, in kg/m2, as the page
        prints its SI half.
    :ivar pile_height_mm: The height of the pile, in millimetres.
    :ivar pile_surface: Whether the pile is cut or looped, in the page's words.
    :ivar fibre: The fibre, in the page's words.
    :ivar mounting: What the carpet is laid on, which is what separates the two
        tables and raises the rating.
    :ivar noise_reduction_coefficient: The NRC, dimensionless.
    """

    pile_weight_kg_m2: float | None = None
    pile_height_mm: float | None = None
    pile_surface: str = ""
    fibre: str = ""
    mounting: str = ""
    noise_reduction_coefficient: float | None = None


#: The published tables this catalogue reads, in the order the page prints
#: them.
_TABLES = ("harris-1995-table-30-2", "harris-1995-table-30-3")


def _load() -> dict[str, Carpet]:
    """Every row of every packaged table, keyed by table and row."""
    out: dict[str, Carpet] = {}
    for table in _TABLES:
        citation, rows = read_table("phonometry.materials.absorbers", f"{table}.json")
        for row in rows:
            out[f"{table}/{row['key']}"] = Carpet.from_printed(
                source=citation, table=table, **take(row)
            )
    return out


#: The carpets this library has read from a page, keyed ``"<table>/<row>"``:
#: Harris 3e Table 30.2, PDF page 704 (printed p. 30.22), eleven carpets on bare
#: concrete, and Table 30.3, PDF pages 704-705 (printed pp. 30.22-30.23), eight
#: on a hair pad.
PUBLISHED_CARPETS: Mapping[str, Carpet] = MappingProxyType(_load())


def carpets_named(
    name: str, *, catalogue: Mapping[str, Carpet] | None = None
) -> tuple[Carpet, ...]:
    """Every published carpet whose construction, surface or fibre contains *name*.

    :param name: Part of what the page prints, in Spanish, matched without
        regard to case: ``"nylon"`` answers with every nylon carpet of both
        tables, and ``"de nudo"`` with every knotted one.
    :param catalogue: The rows to search in place of :data:`PUBLISHED_CARPETS`:
        a catalogue of your own that :func:`phonometry.io.read_catalogue`
        returns, ``PUBLISHED_CARPETS | mine`` to search both at once, or any
        mapping of key to row (Default: ``None``, which searches
        :data:`PUBLISHED_CARPETS`).
    :return: The matching rows, in the order the tables list them. Empty when
        nothing matches, which is not an error.
    :raises TypeError: for a *catalogue* that is not a mapping, or that holds a
        row that is not a :class:`Carpet`, naming its key.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in rows_to_search(catalogue, PUBLISHED_CARPETS, Carpet, "carpets_named")
        if wanted in f"{row.name} {row.pile_surface} {row.fibre}".casefold()
    )
