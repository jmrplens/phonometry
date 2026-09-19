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

What it is not
--------------
It is not a table of fluid properties to look values up in. Air at 23 degC and
50 per cent relative humidity is :func:`~phonometry.fluids.air`, which computes
it from the conditions that were measured; sea water is
:func:`~phonometry.fluids.sea_water`. Use a row here to reproduce a book's own
number.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from .._internal.catalogue import read_table
from ._state import Fluid

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_FLUIDS",
]

#: The table of fluid states this catalogue reads from a data file. One file
#: per published table, in ``fluids/data``, each citing its own page.
_TABLES = ("bies-2017-table-c1-fluids",)


def _transcribed() -> dict[str, Fluid]:
    """The states read from a published table, keyed by table and row.

    A row of a fluid table prints a temperature, a density and a speed of
    sound, which is a state and not a model, so it becomes a
    :class:`~phonometry.fluids.Fluid` whose ``model`` names the table, with
    its page, rather than a closed form that was never used. The pressure is
    the one atmosphere every such table assumes without printing it.
    """
    states: dict[str, Fluid] = {}
    for table in _TABLES:
        source, rows = read_table("phonometry.fluids", f"{table}.json")
        for row in rows:
            states[f"{table}/{row['key']}"] = Fluid(
                temperature_c=row["temperature_c"],
                static_pressure_pa=_ONE_ATMOSPHERE_PA,
                composition={},
                model=f"{row['name']} as printed in {source}",
                validity=_REPRESENTATIVE_ONLY,
                properties={
                    "speed_of_sound": row["speed_of_sound_m_s"],
                    "density": row["density_kg_m3"],
                },
            )
    return states


#: The pressure a table of fluid properties assumes when it prints a density
#: and a temperature and no pressure at all.
_ONE_ATMOSPHERE_PA = 101325.0

#: What Bies says about the whole of Table C.1, carried into the validity of
#: every state read from it, because a reader who takes a density off it
#: should get the book's own hedge with the number.
_REPRESENTATIVE_ONLY = (
    "Bies 5e says of Table C.1 that its values 'should be used with caution "
    "and should be considered as representative only'."
)


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
