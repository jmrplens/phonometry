#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Thin resistive facings, and the resistance of one square metre of them.

A porous absorber is usually covered, and what covers it is a wire mesh, a
glass cloth or a sheet of sintered metal. The cover is thin enough that it
stores no sound and absorbs almost none by itself, and thin enough that what
it does to the layer behind it is settled by one number: the pressure drop
across it divided by the face velocity through it, which the chapter these
rows come from writes ``R_s = dp/v`` and calls the specific, or unit-area,
flow resistance.

Not the flow resistivity, which is the other catalogue
------------------------------------------------------
:data:`~phonometry.materials.absorbers.PUBLISHED_POROUS` holds a flow
**resistivity**, ``sigma``, in Pa s/m2: a property of a bulk material, per
metre of it, which has to be multiplied by a thickness before it means
anything. This catalogue holds a flow **resistance**, ``R_s``, in Pa s/m: a
property of a facing as supplied, already integrated through whatever
thickness it has, and there is no thickness to multiply by. The two are one
letter apart in most books and a factor of the thickness apart in every
calculation, so they are held under two field names that cannot be confused:
``flow_resistivity_pa_s_m2`` there and
:attr:`~ResistiveSheet.specific_flow_resistance_pa_s_m` here. A mesh of
24.6 Pa s/m is not a material of 24.6 Pa s/m2.

The unit has three spellings in the literature and they are all the same
thing: N s/m3, Pa s/m, and the mks rayl of an older tradition. The pages here
use the first and the third: TABLE 8.5 and TABLE 8.7 head their resistance
column ``N · s/m3``, and TABLE 8.6 heads its own "Flow Resistance, mks rayls
(N · s/m3)". Pa s/m is this library's spelling of that same unit, and it is
the one in the field name.

What the pages print twice, and what they print once
----------------------------------------------------
TABLE 8.5 prints every one of its quantities twice, but only three of the four
pairs are one quantity in two systems of units: the wire count in wires per
centimetre and wires per inch, the wire diameter in micrometres and mils, the
mass in kg/m2 and lb/ft2. The fourth pair prints the flow resistance in N s/m3
and again as a multiple of ``rho_0 c_0``, which is no unit at all. TABLE 8.7
prints its thickness and its mass in the two systems of units, and its flow
resistance the two ways TABLE 8.5 does. This catalogue keeps the SI
printing of each pair of units, so the numbers here are the page's own digits
rather than arithmetic on them, and that leaves the customary printing free to
check the SI one. It is how the first of the two defects these pages carry was
found: the finest wire mesh of TABLE 8.5 is printed as 0.31 kg/m2 beside
0.63 lb/ft2, when 0.31 kg/m2 is 0.063 lb/ft2 and the decimal point of the pound
cell is one place too far right, and the entry in ``docs/ERRATA.md`` argues it.
The row keeps the kilogramme cell, which the column above it and the weave of
the mesh both support, and its
:attr:`~phonometry.io.CatalogueRow.note` records the pound
cell. The note and not a hedge, because the defective cell is the restatement:
this catalogue holds no customary column, so there is no cell here to refuse.

TABLE 8.6 is the one that does not print everything twice. It prints its
surface density twice, and its weave and its flow resistance once each and in
one unit. The two surface densities disagree by about eleven per cent on all
thirteen rows, one wrong factor rather than thirteen slips, and the page does
not say which of the two columns carries it: the row holds the gramme per
square metre the page prints, in :attr:`~ResistiveSheet.surface_density_g_m2`,
and its note gives the ounce per square yard beside it, with the entry in
``docs/ERRATA.md`` that argues the pair. Thirteen of the twenty-nine flow
resistances published here therefore have no second printing to check them at
all, and nothing but the second reader stands behind them.

Where the rows live
-------------------
In ``absorbers/data/``, one file per printed table:
``ver-beranek-2006-table-8-5.json``, ``ver-beranek-2006-table-8-6.json`` and
``ver-beranek-2006-table-8-7.json``, read at import through the package-data
reader in ``phonometry._internal``, the same as every other catalogue here.
One file per published table is what makes a key mean something: a row of the
glass cloth table is keyed ``"ver-beranek-2006-table-8-6/glass_cloth_120"``,
and its :attr:`~phonometry.io.CatalogueRow.source` names that
table, that PDF page and that printed folio and nothing else.

What it is not
--------------
It is not a specification. These are commercial products, the cloths and the
sintered sheets named by their manufacturers' own codes and the wire meshes by
nothing but their mesh count, and the pages give no measurement method, no
laboratory and no standard for any of the three tables. What they do give is
two conditions, and each reaches the rows it belongs to: TABLE 8.7 prints its
flow resistance for "Air, 70°F", which is in the note of all eleven sintered
sheets and matters because the resistance of a facing follows the viscosity of
the air; and footnote a of TABLE 8.6 says its surface densities are "Averaged
over a large sample.", which is in the note of all thirteen cloths. The
running text adds the warning that matters most, about the two cloth tables:
the values "represent the linear part of the flow resistance, which is
appropriate for design use only if the particle velocity is low", and above
140 dB the resistance has to be measured as a function of face velocity
instead. The eleven sintered sheets are the exception the same page makes for
them, and a conditional one: backed by a honeycomb-partitioned air space they
"remain linear up to high sound pressure levels and for high-Mach-number
grazing flow", and their table prints a nonlinearity factor where the two
cloth tables print none.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from ..._internal.catalogue import CatalogueRow, read_table, take

__all__ = [
    "PUBLISHED_FLOW_RESISTANCE",
    "ResistiveSheet",
    "resistive_sheet_named",
]

#: The published tables this catalogue reads, in the order the book prints
#: them, one file per printed table.
_TABLES = (
    "ver-beranek-2006-table-8-5",
    "ver-beranek-2006-table-8-6",
    "ver-beranek-2006-table-8-7",
)


@dataclass(frozen=True, kw_only=True)
class ResistiveSheet(CatalogueRow):
    """One thin resistive facing, as its published table prints it.

    The name, the citation and the hedges a cell can carry instead of a
    number are the ones every catalogue row has. What varies here is which
    columns a row has at all: a wire mesh is described by how many wires it
    has to the centimetre and how thick they are, a glass cloth by its weave,
    and a sintered sheet by its thickness and how far from linear it goes, so
    no two of the three tables print the same columns and every quantity below
    is optional.

    :ivar specific_flow_resistance_pa_s_m: The resistance of unit area of the
        facing, ``R_s``, in pascal seconds per metre, which is the N s/m3 the
        three tables print and the mks rayls TABLE 8.6 also heads its column
        with. Per unit **area**, so unlike the flow resistivity of
        :data:`~phonometry.materials.absorbers.PUBLISHED_POROUS` it is not
        multiplied by a thickness.
    :ivar normalized_flow_resistance: The same resistance divided by the
        characteristic impedance of air, dimensionless, as two of the tables
        print it in a column of their own. Kept rather than recomputed
        because the two tables do not normalize by the same impedance:
        :meth:`reference_impedance_pa_s_m` recovers the one each row was
        divided by.
    :ivar wires_per_cm: Wires per centimetre of the woven mesh, as TABLE 8.5
        heads the column and prints it again as wires per inch beside it. One
        count and not two: the page says nothing about the two directions of
        the weave, where the glass cloth table prints a count for each.
    :ivar wire_diameter_um: Diameter of the wire, in micrometres.
    :ivar weave_construction: The weave of a glass cloth, as the page prints
        it and as text rather than as a number: two counts under one heading,
        "Construction, Ends × Picks", over a length the page never states.
        ``"60 × 58"``. Empty on a row from a table that prints no such column.
    :ivar thickness_mm: Thickness of the sintered sheet, in millimetres. It
        is a property of the sheet, not something the flow resistance is
        divided by: see the module docstring.
    :ivar mass_per_area_kg_m2: Mass per unit area, ``rho_s``, in kg/m2, as
        TABLE 8.5 and TABLE 8.7 head the column and print it. The chapter
        names it beside the flow resistance as the second thing that
        characterises a thin layer.
    :ivar surface_density_g_m2: The same quantity as TABLE 8.6 prints it,
        under its own heading, "Surface Density", in grammes per square metre
        and averaged over a large sample per its footnote a. A second name
        for one quantity because nothing here is converted and a cell printed
        in g/m2 is held in g/m2; no row has both, since no table prints both.
        Its second printing, in oz/yd2, disagrees with it: see the module
        docstring and ``docs/ERRATA.md``.
    :ivar nonlinearity_factor: How far the sintered sheet departs from a
        linear resistance: its table's footnote b defines it as the ratio of
        the flow resistances obtained at flow velocities of 500 and 20 cm/s.
        A facing at 1 would be linear; these run from 1.8 to 5.
    """

    specific_flow_resistance_pa_s_m: float | None = None
    normalized_flow_resistance: float | None = None
    wires_per_cm: float | None = None
    wire_diameter_um: float | None = None
    weave_construction: str = ""
    thickness_mm: float | None = None
    mass_per_area_kg_m2: float | None = None
    surface_density_g_m2: float | None = None
    nonlinearity_factor: float | None = None

    def reference_impedance_pa_s_m(self) -> float:
        """The impedance this row's own two resistance columns were divided by.

        Two of the three tables print the flow resistance twice, once in
        N s/m3 and once as a multiple of ``rho_0 c_0``, and neither says what
        they took ``rho_0 c_0`` to be. Dividing one column by the other gives
        it back, and it is worth asking for: the five wire mesh rows give 407
        to 421 Pa s/m, and the sintered metal rows give 400 except for the
        one block whose columns are 350 and 0.88, which gives 397.7. The two
        normalized columns are not on the same scale, and a caller comparing
        them without noticing would be out by two to five per cent, depending
        on which wire mesh row it is.

        It is not a property of the facing. It is a property of the page.

        :return: The characteristic impedance implied by the row, in Pa s/m.
        :raises ValueError: when the row has only one of the two columns,
            which is every row of the glass cloth table, naming what the page
            had instead.
        """
        resistance = self.printed(
            "specific_flow_resistance_pa_s_m",
            wanted_by="the impedance the two printed columns imply",
        )
        normalized = self.printed(
            "normalized_flow_resistance",
            wanted_by="the impedance the two printed columns imply",
        )
        return resistance / normalized


def _rows() -> dict[str, ResistiveSheet]:
    """Every facing of every table this catalogue reads."""
    out: dict[str, ResistiveSheet] = {}
    for filename in _TABLES:
        citation, rows = read_table(
            "phonometry.materials.absorbers", f"{filename}.json"
        )
        for row in rows:
            key = f"{filename}/{row['key']}"
            out[key] = ResistiveSheet(source=citation, table=filename, **take(row))
    return out


#: Twenty-nine thin resistive facings as their tables print them, keyed
#: ``"<table>/<facing>"``. Read from one file per printed table:
#: ``materials/absorbers/data/ver-beranek-2006-table-8-5.json``, Vér & Beranek
#: 2e TABLE 8.5, PDF page 266 (printed p. 262);
#: ``materials/absorbers/data/ver-beranek-2006-table-8-6.json``, Vér & Beranek
#: 2e TABLE 8.6, PDF page 267 (printed p. 263); and
#: ``materials/absorbers/data/ver-beranek-2006-table-8-7.json``, Vér & Beranek
#: 2e TABLE 8.7, PDF page 267 (printed p. 263). The resistance is per unit
#: area, in Pa s/m, and is not the per-metre flow resistivity of
#: :data:`PUBLISHED_POROUS`.
PUBLISHED_FLOW_RESISTANCE: MappingProxyType[str, ResistiveSheet] = MappingProxyType(
    _rows()
)


def resistive_sheet_named(name: str) -> tuple[ResistiveSheet, ...]:
    """Every facing a page labels *name*, matched whole and without case.

    Whole and not in part, unlike the other catalogues of this library, and
    the reason is what these pages use for names: a mesh count, a four-digit
    cloth number, a manufacturer's product code. A search that matched part
    of a name would answer ``"12"`` with the twelve-wire mesh, the cloth
    numbered 120, the cloth numbered 126 and the four sintered sheets FM 122,
    FM 125, FM 126 and FM 127, none of which has anything to do with any
    other.

    :param name: The label as its page prints it: ``"80"``, ``"1584"``,
        ``"FM 122"``.
    :return: The matching rows, in catalogue order. Empty when none match.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in PUBLISHED_FLOW_RESISTANCE.values()
        if row.name.casefold() == wanted
    )
