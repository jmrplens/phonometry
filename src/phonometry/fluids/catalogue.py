#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fluid states read from a printed page.

A density and a speed of sound stand behind every level this library computes,
and most of them are computed: :func:`~phonometry.fluids.air`,
:func:`~phonometry.fluids.ideal_gas` and :func:`~phonometry.fluids.sea_water`
take the conditions that were measured and return the state that follows. A
few are not. Some books print a table of fluids the way they print a table of
solids, a density and a speed of sound at a stated temperature, and those are
read rather than derived. This is where they live.

The distinction is carried in :attr:`~phonometry.fluids.Fluid.model`, which
every state already uses to say what produced it. A computed state names the
closed form, the annex or the fit; a state from here names the table, with its
PDF page and its printed folio, because the table is what produced it and a
reader checking the number needs the page rather than the name of an equation
that was never used. The citation lives once, in the data file beside the
rows, the same shape the solid and porous catalogues use.

Not every named air in this library is here
-------------------------------------------
Four more sit elsewhere in the tree, each beside the model or the standard
that fixes it, and they disagree: the absorber models propagate through
343 m/s at 1,205 kg/m3, the airflow-resistance annex through 345,87 at 1,186,
EN/ISO 12354 through 340 at 1,29, and the acoustic solver defaults to 343 at
1,2. None of them is wrong. Each is the air its own document assumes, and
substituting one for another would change a number that document prints, which
is why each stays with the clause that prints it rather than being gathered
here.

Gathering them would also invert the dependency this package exists at the
bottom of: ``fluids`` is part of the transverse toolbox precisely so that any
domain may import it, and a catalogue here that imported ``materials``,
``building`` and ``simulation`` to reach them would make the medium depend on
three of the domains that stand on it. The comparison a reader wants is a
documentation artefact, and it is built as one: the published-catalogues page
of the site lists all of them side by side, gathered by a script that is free
to see the whole tree.

Gases are the other half, and they are not states
-------------------------------------------------
A book that prints a table of gases prints something different from a table of
fluids: not a density and a speed of sound, which a gas only has once a
temperature and a pressure are named, but the ratio of specific heats and the
molar mass, which close the ideal-gas state at any temperature and pressure.
So the gases live in a
catalogue of their own, :data:`PUBLISHED_GASES`, and reach a state through
:meth:`Gas.ideal_state`, which is :func:`~phonometry.fluids.ideal_gas` with the
citation carried along. Air appears in both, and it should: Bies prints it once
as a state at 20 degC and once as a pair of constants, and those are two
different readings of the same gas.

What it is not
--------------
It is not a table of fluid properties to look values up in. Air at 23 degC and
50 per cent relative humidity is :func:`~phonometry.fluids.air`, which computes
it from the conditions that were measured; sea water is
:func:`~phonometry.fluids.sea_water`. Use a row here to reproduce a book's own
number.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from .._internal.catalogue import (
    CatalogueError,
    CatalogueRow,
    read_packaged,
    read_table,
    rows_to_search,
    take,
)
from ._state import Fluid
from .gas import ideal_gas

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_FLUIDS",
    "PUBLISHED_GASES",
    "Gas",
    "gases_named",
]

#: The package whose ``data`` directory holds every table this module reads.
_PACKAGE = "phonometry.fluids"

#: The table of fluid states this catalogue reads from a data file. One file
#: per published table, in ``fluids/data``, each citing its own page.
_FLUID_TABLES = ("bies-2017-table-c1-fluids", "norton-karczub-2003-appendix-4bc")

#: The tables of gas constants, read from the same directory and the same
#: way. A gas table prints what a gas is rather than what one sample of it
#: was doing, so it is a catalogue of its own and not more states.
_GAS_TABLES = ("bies-2017-table-c2", "hopkins-2007-table-a1")


def _transcribed() -> dict[str, Fluid]:
    """The states read from a published table, keyed by table and row.

    A row of a fluid table prints a temperature, a density and a speed of
    sound, which is a state and not a model, so it becomes a
    :class:`~phonometry.fluids.Fluid` whose ``model`` names the table, with
    its page, rather than a closed form that was never used. The pressure is
    the one atmosphere every such table assumes without printing it.

    A :class:`~phonometry.fluids.Fluid` is a physical state and has no note
    of its own, so what the row's note says about the page follows the
    table's hedge in the state's ``validity``: a caller who reads the four
    hydrogen and oxygen states of Norton & Karczub learns there that the
    page prints one density at two temperatures, where a note left in the
    data file would have reached nobody.
    """
    states: dict[str, Fluid] = {}
    for table in _FLUID_TABLES:
        document = read_packaged(_PACKAGE, f"{table}.json")
        source, rows = document["source"], document["rows"]
        about = _table_validity(document, f"{table}.json")
        for row in rows:
            # Only what the row prints. A table that gives the ratio of
            # specific heats fixes it; one that does not leaves the state
            # refusing to answer for it, rather than this library supplying a
            # value the page never printed.
            properties = {
                "speed_of_sound": row["speed_of_sound_m_s"],
                "density": row["density_kg_m3"],
            }
            if "heat_capacity_ratio" in row:
                properties["heat_capacity_ratio"] = row["heat_capacity_ratio"]
            note = row.get("note", "")
            states[f"{table}/{row['key']}"] = Fluid(
                temperature_c=row["temperature_c"],
                static_pressure_pa=_ONE_ATMOSPHERE_PA,
                composition={},
                model=f"{row['name']} as printed in {source}",
                validity=f"{about} {note}" if note else about,
                properties=properties,
            )
    return states


#: The pressure a table of fluid properties assumes when it prints a density
#: and a temperature and no pressure at all.
_ONE_ATMOSPHERE_PA = 101325.0


def _table_validity(document: Mapping[str, object], filename: str) -> str:
    """The hedge a book puts on a whole table, read from the table's own file.

    What a book says about a table belongs with any number a reader takes off
    it, and it is different for every book: Bies calls Table C.1
    representative only, Norton & Karczub say their appendix was collated from
    several sources without saying which row came from which. That sentence
    used to be a constant in this module, which meant the second table to
    arrive would have carried the first book's hedge, so it now lives in the
    data file beside the rows it qualifies.

    :param document: The table as :func:`read_packaged` decoded it.
    :param filename: The file it came from, named in a refusal.
    :raises CatalogueError: for a fluid table with no ``validity`` text.
    """
    validity = document.get("validity")
    if not isinstance(validity, str):  # pragma: no cover - a malformed file
        msg = f"{filename}: a fluid table needs a top-level 'validity' that is text"
        raise CatalogueError(msg)
    return validity


#: The fluid states this library has read from a published page, keyed
#: ``"<table>/<row>"``. Each names its page, with the PDF page and the printed
#: folio, in its :attr:`~phonometry.fluids.Fluid.model`, and the citation
#: itself lives once, in ``fluids/data/``.
#:
#: The four airs that sit elsewhere in the tree, each beside the model or the
#: standard that fixes it, are deliberately not gathered here: see the module
#: docstring, and the published-catalogues page of the documentation, which
#: lists them all side by side.
PUBLISHED_FLUIDS: Mapping[str, Fluid] = MappingProxyType(_transcribed())


@dataclass(frozen=True, kw_only=True)
class Gas(CatalogueRow):
    """One gas of a published table: the two numbers that close its state.

    A table of gases does not print a density and a speed of sound, because a
    gas does not have one: it has whichever the temperature and the pressure
    give it. What it prints instead is the pair that fixes the whole family,
    the ratio of specific heats and the molar mass, and
    :meth:`ideal_state` walks from that pair to the ideal-gas state at
    whichever temperature and pressure the caller asks for.
    That is the difference between this catalogue and
    :data:`PUBLISHED_FLUIDS`, which holds states: a row there is one condition
    a book measured, a row here is every condition its two constants close under
    the ideal-gas relations.

    The hedges of :class:`~phonometry.io.CatalogueRow` apply
    unchanged. A cell printed as an interval is a range and not a value, which
    is what saturated steam is in the table this reads first.

    :ivar molar_mass_kg_mol: Molar mass ``M``, in kg/mol, as the page prints
        it. The gas tables print kg/mol rather than g/mol, so the number in
        the cell is 0,028 97 for air.
    :ivar heat_capacity_ratio: Ratio of specific heats ``gamma``, which is
        ``c_p/c_v`` and therefore above 1 for every gas.
    """

    molar_mass_kg_mol: float | None = None
    heat_capacity_ratio: float | None = None

    def ideal_state(
        self,
        *,
        temperature_c: float,
        static_pressure_pa: float | None = None,
    ) -> Fluid:
        """The gas at one state, through the ideal-gas closure.

        :param temperature_c: Temperature ``t``, in degrees Celsius.
        :param static_pressure_pa: Static pressure ``p``, in pascals. Omitted
            means one standard atmosphere, and
            :func:`~phonometry.fluids.ideal_gas` says so with a warning.
        :return: The :class:`~phonometry.fluids.Fluid` the two printed
            constants give at that state, carrying this row's citation in its
            model so the state can be traced back to the page.
        :raises ValueError: when the page did not print both constants, naming
            the one it left out and what the cell held instead.
        """
        state = ideal_gas(
            temperature_c=temperature_c,
            heat_capacity_ratio=self.printed(
                "heat_capacity_ratio", wanted_by="the ideal-gas closure"
            ),
            molar_mass_kg_mol=self.printed(
                "molar_mass_kg_mol", wanted_by="the ideal-gas closure"
            ),
            static_pressure_pa=static_pressure_pa,
        )
        return Fluid(
            temperature_c=state.temperature_c,
            static_pressure_pa=state.static_pressure_pa,
            composition=state.composition,
            model=f"{state.model}, for {self.name} as printed in {self.source}",
            validity=state.validity,
            properties=dict(state.properties),
        )


def _gases() -> dict[str, Gas]:
    """Every row of every packaged gas table, keyed by table and row.

    The key names the table for the same reason the other catalogues do: two
    books print air, and they do not print the same molar mass for it.
    """
    rows: dict[str, Gas] = {}
    for table in _GAS_TABLES:
        source, records = read_table(_PACKAGE, f"{table}.json")
        for record in records:
            rows[f"{table}/{record['key']}"] = Gas.from_printed(
                table=table, source=source, **take(record)
            )
    return rows


#: The gases this library has read from a published page, keyed
#: ``"<table>/<row>"``. Each row carries the two constants that close the
#: ideal-gas state, so ``PUBLISHED_GASES["bies-2017-table-c2/methane"]`` plus a
#: temperature is a :class:`~phonometry.fluids.Fluid` for methane, cited.
#: One file per published table in ``fluids/data/``.
PUBLISHED_GASES: Mapping[str, Gas] = MappingProxyType(_gases())


def gases_named(
    name: str, *, catalogue: Mapping[str, Gas] | None = None
) -> tuple[Gas, ...]:
    """Every published row for a gas name, across the tables.

    Two books printing one gas is worth having, because the pair they print is
    not always the same pair: for carbon dioxide one of them gives 1,30 and
    the other 1,33. That is 2,3 per cent on the ratio and, since the speed of
    sound goes as its square root, 1,2 per cent on the speed, which a reader
    deserves to see both sides of rather than whichever this library happened
    to load first.

    :param name: The gas as a table names it, matched without regard to case
        and ignoring a parenthesis the page adds: ``"air"`` answers with the
        row Hopkins prints as ``"Air (dry)"``.
    :param catalogue: The rows to search in place of :data:`PUBLISHED_GASES`: a
        catalogue of your own that :func:`phonometry.io.read_catalogue`
        returns, ``PUBLISHED_GASES | mine`` to search both at once, or any
        mapping of key to row (Default: ``None``, which searches
        :data:`PUBLISHED_GASES`).
    :return: The rows whose :attr:`Gas.name` matches, in the order the tables
        are read, which is empty when no page names it.
    :raises TypeError: for a *catalogue* that is not a mapping, or that holds a
        row that is not a :class:`Gas`, naming its key.
    """
    wanted = _plain(name)
    return tuple(
        row
        for row in rows_to_search(catalogue, PUBLISHED_GASES, Gas, "gases_named")
        if _plain(row.name) == wanted
    )


def _plain(name: str) -> str:
    """A gas name with its case and its parenthetical qualifier dropped."""
    return name.split("(")[0].strip().casefold()
