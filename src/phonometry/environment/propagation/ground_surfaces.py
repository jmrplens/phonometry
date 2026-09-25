#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Ground surfaces as the pages that print them print them.

Every outdoor propagation model in this package asks the ground how resistive
it is, and nobody measures that: a prediction over a pasture takes the flow
resistivity of a pasture from a table. This is that table, or rather the three
of them this library reads, with the page each row came off attached to it.

What a ground row is
--------------------
An **effective** flow resistivity, which is not the flow resistivity of the
material under your feet. It is the single number that makes a
semi-infinite, locally reacting, rigid-framed ground model reproduce a
measured excess attenuation, so it carries the model it was fitted with. Cox
and D'Antonio say so explicitly and mark each row with the fit it belongs to,
which is why a surface there is several rows: the same grass fitted with the
Delany and Bazley model, with the semi-phenomenological model and with the
variable-porosity model is three numbers, and averaging them would be an
average of three different quantities.

Why the numbers spread the way they do
--------------------------------------
Bies, Hansen and Howard gather theirs from four sources and print the spread
as they found it, warning on the facing page that "there are great variations
in flow resistivity measured data from different sources". Grass runs from
100 to 300 kPa s/m2 in one row of that table; the same grass is 4 to 850
kPa s/m2 across the fits Cox tabulates. A row is a place to start, not a
measurement of your site.

The classes are a different thing
---------------------------------
Bies's second table is not measured ground at all: it is the eight classes
A to H the propagation models define, with the ground factor G that ISO
9613-2 and NMPB-2008 take and the representative resistivity Harmonoise
assigns each class. Class H is water, and its resistivity is an acoustically
hard stand-in rather than anything anybody measured. Those rows carry
:attr:`GroundSurface.harmonoise_class` and the two ground factors; a model
that wants a class takes the class, and a model that wants a resistivity
takes the resistivity.

Where the rows live
-------------------
In ``propagation/data/*.json``, one file per published table, read at import
through the package-data reader in ``phonometry._internal``. The citation is
written once, in the file that holds the rows it belongs to.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from ..._internal.catalogue import CatalogueRow, read_table, rows_to_search, take

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_GROUND",
    "GroundSurface",
    "ground_surfaces_named",
]


@dataclass(frozen=True, kw_only=True)
class GroundSurface(CatalogueRow):
    """One ground surface as one table prints it.

    Every quantity is optional, because the three tables print three different
    sets of columns, and a quantity the page did not print answers ``None``
    with :meth:`~phonometry.io.CatalogueRow.why_missing`
    saying what the cell held instead.

    :ivar flow_resistivity_pa_s_m2: Effective flow resistivity ``R_1`` or
        ``sigma_e``, in Pa s/m2. Bies prints it in kPa s/m2 and Cox in
        rayl/m, which is this unit under another name; the conversion is
        pinned in the data file's ``about``.
    :ivar porosity: Open porosity, where the fit that produced the resistivity
        also produced one, as the fraction of the volume that is open, from 0
        to 1. Cox's Table 6.7 prints six of its porosities as 26.9 to 58.1 in
        a column that prints a fraction on every other row and states no
        unit; a porosity of 36.5 is not a porosity, so those six cells are
        empty, and :meth:`~phonometry.io.CatalogueRow.why_missing` quotes the
        figure the page prints.
    :ivar water_content_percent: Water content of the specimen, per cent, for
        the sands Cox tabulates wet and dry. The resistivity of a sand is not
        monotonic in it, which is the point of printing it.
    :ivar porosity_decay_rate_per_m: The rate ``zeta`` at which porosity falls
        with depth in the variable-porosity model, in 1/m. It is negative for
        several surfaces, which is what the page prints.
    :ivar iso_9613_ground_factor: The ground factor ``G`` of ISO 9613-2 for a
        ground class: 0 for hard ground, 1 for porous ground.
    :ivar nmpb_ground_factor: The ground factor ``G`` of NMPB-2008 for the
        same class, which is not always the ISO one: two of the eight classes
        differ.
    :ivar harmonoise_class: The class letter, ``"A"`` to ``"H"``, for a row of
        the class table, and the empty string for a measured surface.
    """

    flow_resistivity_pa_s_m2: float | None = None
    porosity: float | None = None
    water_content_percent: float | None = None
    porosity_decay_rate_per_m: float | None = None
    iso_9613_ground_factor: float | None = None
    nmpb_ground_factor: float | None = None
    harmonoise_class: str = ""


# ---------------------------------------------------------------------------
# Rules for this catalogue, and why
#
# 1. A row is what one page prints about one surface. The same surface in
#    another book is another row, because the two were fitted with different
#    models and are not the same quantity.
# 2. A table enters only after its page has been read as an image, and its
#    file carries the document, the table, the PDF page and the printed folio.
# 3. Values are stored in Pa s/m2. Both books print something else, and the
#    conversion is pinned by an assertion against the printed digits.
# 4. What the page printed instead of a number is kept as the page printed it,
#    including the cell Cox prints with two decimal points in it.
# ---------------------------------------------------------------------------

#: The published tables this catalogue reads.
_TABLES = (
    "bies-2017-table-5-1",
    "bies-2017-table-5-2",
    "cox-2017-table-6-7",
)


def _transcribed() -> dict[str, GroundSurface]:
    """Every row of every table, keyed ``"<table>/<row>"``."""
    rows: dict[str, GroundSurface] = {}
    for table in _TABLES:
        source, published = read_table(
            "phonometry.environment.propagation", f"{table}.json"
        )
        for row in published:
            rows[f"{table}/{row['key']}"] = GroundSurface.from_printed(
                source=source, table=table, **take(row)
            )
    return rows


#: Every ground surface this library has read off a published page, keyed
#: ``"<table>/<row>"``: ``"bies-2017-table-5-1/sugar_snow"`` is that snow as
#: Bies prints it and ``"cox-2017-table-6-7/lawn_delany_bazley"`` is a lawn as
#: Cox prints it under one of his three fits. One file per published table in
#: ``environment/propagation/data/``, each citing its own page.
#:
#: The key names the table because the same surface is in more than one of
#: them with more than one number, and the difference is the model each was
#: fitted with rather than the ground. Use :func:`ground_surfaces_named` to
#: gather every reading of one name.
PUBLISHED_GROUND: Mapping[str, GroundSurface] = MappingProxyType(_transcribed())


def ground_surfaces_named(
    name: str, *, catalogue: Mapping[str, GroundSurface] | None = None
) -> tuple[GroundSurface, ...]:
    """Every published row for a surface name, across the tables.

    :param name: The surface as a table prints it, matched without regard to
        case.
    :param catalogue: The rows to search in place of :data:`PUBLISHED_GROUND`:
        a catalogue of your own that :func:`phonometry.io.read_catalogue`
        returns, ``PUBLISHED_GROUND | mine`` to search both at once, or any
        mapping of key to row (Default: ``None``, which searches
        :data:`PUBLISHED_GROUND`).
    :return: The rows whose :attr:`GroundSurface.name` matches, in the order
        the tables are read, which is empty when no page names it.
    :raises TypeError: for a *catalogue* that is not a mapping, or that holds a
        row that is not a :class:`GroundSurface`, naming its key.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in rows_to_search(
            catalogue, PUBLISHED_GROUND, GroundSurface, "ground_surfaces_named"
        )
        if row.name.casefold() == wanted
    )
