#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Impact insulation as a handbook prints it, one row per floor-ceiling.

The impact insulation class is a single number for a whole assembly. It is not
a property of the slab, and it is not a property of the covering: it is what a
tapping machine did on one floor built one way, with one ceiling under it, and
it moves by fifty-five points between a bare concrete slab, which these pages
rate 25, and the same slab under a wool carpet, which they rate 80. The models
of :mod:`phonometry.building.prediction` compute the improvement a covering
gives; this module holds what was measured on floors that exist, so a
prediction has something published to sit beside.

Two quantities, and never both on one row
-----------------------------------------
Tables 32.1 to 32.7 print :attr:`ImpactInsulation.impact_insulation_class`,
the IIC of a whole floor-ceiling assembly. Table 32.8 prints
:attr:`ImpactInsulation.impact_insulation_class_improvement`, the delta-IIC a
surface treatment adds to a hard massive floor. They are different quantities
and no row of this catalogue carries both: one is a rating, the other is a
difference between two ratings, and a caller who added the second to the first
would be adding a difference to an absolute with nothing in the arithmetic to
say so. Both are dimensionless.

There is no spectrum here
-------------------------
The IIC is a single-number rating and these pages print no frequency band at
all: no impact sound pressure level per octave, none per third octave, and no
reference curve. A caller after a band-by-band impact level will not find one
in this catalogue, and nothing here can be turned into one.

How a row is identified
-----------------------
The page numbers its constructions 1 to 38 straight through the seven tables,
with a letter where a construction is printed as two lettered rows, and that
printed number is the key of the row: ``"harris-1995-tables-32-1-to-32-8/34A"``
is the row the page calls 34A. It has to be, because about a dozen descriptions
are printed in full and refer to another row rather than repeating the
structural floor: "Igual que 1 salvo que...", "Mismo suelo estructural que el
18". The printed text is kept whole in :attr:`~.CatalogueRow.name`, the row it
points at is in :attr:`ImpactInsulation.refers_to_row`, and resolving it is one
lookup: ``PUBLISHED_IMPACT_INSULATION[f"{row.table}/{row.refers_to_row}"]``.
Table 32.8 numbers nothing, so its six rows are keyed by a slug of the printed
treatment. A lettered pair is two rows and not one row in two conditions, which
is why no row of this catalogue fills
:attr:`~phonometry._internal.catalogue.CatalogueRow.variant`: 34A and 34B are
each printed with a description and a rating of their own.

Where the rows live
-------------------
In ``building/data/harris-1995-tables-32-1-to-32-8.json``, read at import
through the package-data reader in ``phonometry._internal``, the same as every
other catalogue here.

What the page got wrong
-----------------------
These tables print every dimension twice, in SI and in US customary units, and
nineteen of the three hundred and twenty pairs are not each other: row 9 gives
16 in as 30,8 cm where the other eighteen 16 in of these tables are 40,6 cm,
row 31 gives 2 in as 10,1 cm, row 38 gives 44 oz/yd2 as 1,99 kg/m2 where 28 and
30 give it as 1,5. They are registered as one entry in ``docs/ERRATA.md`` and
nothing here quietly repairs them: the printed description is kept whole and
the seventeen rows that carry one mark the cell in
:attr:`~phonometry._internal.catalogue.CatalogueRow.misprinted`. One of the
nineteen reaches a quantity rather than prose, which is why
:attr:`ImpactInsulation.layer_density_kg_m3` is empty on row 35A.

What it is not
--------------
It is not a specification and it is not a prediction. The chapter says the
tables hold "datos de mediciones" collected from a 1967 report prepared for the
Federal Housing Administration by the National Bureau of Standards, and Table
32.8 credits a 1963 paper by Zeller; each row carries the one that covers its
table in :attr:`~phonometry._internal.catalogue.CatalogueRow.attributed_to`,
because a row read on its own would otherwise answer the same source for both.
No laboratory, no test standard and no uncertainty is named for any row. Table
32.8 carries a footnote of its own worth reading before its numbers are used
anywhere: over wood-joist floors the improvement may be substantially smaller
than the one printed.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from .._internal.catalogue import CatalogueRow, read_table, take

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_IMPACT_INSULATION",
    "ImpactInsulation",
    "impact_insulation_named",
]


@dataclass(frozen=True, kw_only=True)
class ImpactInsulation(CatalogueRow):
    """One floor-ceiling construction or surface treatment, as printed.

    The name, the citation and the hedges a cell can carry instead of a number
    are the ones every catalogue row has. What this class adds is that its two
    quantities are never both filled: a row is a rating or an improvement on a
    rating, and which one it is says which table it came from.

    :ivar impact_insulation_class: The IIC of the whole floor-ceiling assembly
        this row describes, dimensionless. Filled by Tables 32.1 to 32.7, and
        never on a row that gives an improvement. Two rows print no class at
        all and leave it empty, which
        :meth:`~phonometry._internal.catalogue.CatalogueRow.why_missing` says.
    :ivar impact_insulation_class_improvement: The delta-IIC an elastic surface
        treatment adds over a hard massive structural floor, dimensionless.
        Filled by Table 32.8 alone. It is a difference between two ratings and
        not a rating, so it is not comparable with
        :attr:`impact_insulation_class` and is not to be added to one from
        another row: the page gives the improvement over the floor it was
        measured on, and its own footnote says that over wood joists it may be
        substantially smaller.
    :ivar refers_to_row: The row this row's printed description refers to
        instead of repeating the structural floor, named by the number the
        table prints in its own column. Empty when the description stands on
        its own. The description itself is printed in full and is kept whole in
        :attr:`~phonometry._internal.catalogue.CatalogueRow.name`; this is only
        the thing it inherits.
    :ivar has_section_drawing: Whether the "Esquema" cell of this row holds a
        drawing of the section. That cell prints no text of any kind, so there
        is nothing to transcribe and nothing else is recorded about it. The
        rows that only refer to another one carry no drawing.
    :ivar layer_density_kg_m3: A mass density the running description buries,
        in kilograms per cubic metre, lifted out so it can be read without
        parsing prose. Three rows print one and it is the density of one layer,
        which is why the field says layer and not slab: on row 5 it is a
        semi-rigid polyurethane foam, on row 35A a compressed paper-pulp board
        and only on row 37A the structural concrete. Which layer is named by
        the row's :attr:`~phonometry._internal.catalogue.CatalogueRow.note`, and
        it is never a density of the assembly. Row 35A serves none, because the
        page prints that one cell twice and the two printings disagree;
        :meth:`~phonometry._internal.catalogue.CatalogueRow.why_missing` hands
        back both.
    """

    impact_insulation_class: float | None = None
    impact_insulation_class_improvement: float | None = None
    refers_to_row: str = ""
    has_section_drawing: bool = False
    layer_density_kg_m3: float | None = None


#: The hedges these tables spell as a set rather than a mapping.
_SETS = ("approximate", "bounded_above", "bounded_below")

#: The published tables this catalogue reads, one data file per book.
_TABLES = ("harris-1995-tables-32-1-to-32-8",)


def _load() -> dict[str, ImpactInsulation]:
    """Every row of every packaged table, keyed ``"<table>/<row>"``."""
    rows: dict[str, ImpactInsulation] = {}
    for table in _TABLES:
        source, records = read_table("phonometry.building", f"{table}.json")
        for record in records:
            key = f"{table}/{record['key']}"
            rows[key] = ImpactInsulation(
                table=table, source=source, **take(record, frozen=_SETS)
            )
    return rows


#: Forty-eight rows of measured impact insulation, keyed ``"<table>/<row>"``,
#: where the second half is the number the page prints beside the construction.
#: Read from ``building/data/harris-1995-tables-32-1-to-32-8.json``: Harris 3e
#: Tables 32.1 to 32.8, PDF pages 750 to 757 (printed pp. 32.8 to 32.15),
#: forty-two floor-ceiling constructions with their impact insulation class and
#: six elastic surface treatments with the improvement each one adds over a
#: hard massive floor.
PUBLISHED_IMPACT_INSULATION: Mapping[str, ImpactInsulation] = MappingProxyType(_load())


def impact_insulation_named(name: str) -> tuple[ImpactInsulation, ...]:
    """Every published row whose printed description contains *name*.

    :param name: A fragment of the printed description, matched without case.
        The descriptions are in the language the page is set in, and they are
        the only thing matched: there is no short name for a construction the
        page describes in a paragraph.
    :return: The matching rows, in catalogue order. Empty when none match. A
        tuple and not one row, because a description is not a name and several
        constructions share most of their words.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in PUBLISHED_IMPACT_INSULATION.values()
        if wanted in row.name.casefold()
    )
