#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Scattering coefficients a book computed, kept apart from the ones measured.

:mod:`.measured_scattering` holds what turntables measured under ISO 17497-1.
This holds the three tables of Cox & D'Antonio's Appendix C, which are
boundary element predictions of the correlation scattering coefficient, and
they are a separate catalogue for one reason: a row that says 0.45 because a
solver said so and a row that says 0.45 because a reverberation room said so
are not interchangeable, and a caller who mixes them without meaning to has no
way of finding out afterwards.

Three tables, three shapes
--------------------------
Table C.1 and Table C.2 are three-dimensional predictions of 3 m by 3 m
single-plane diffusers, at normal and at random incidence, over the one-third
octave bands from 250 Hz to 4 kHz; the angle is in the table's title, so every
row of one carries the same one. Table C.3 is two-dimensional, runs from
100 Hz to 5 kHz, and prints three lines per surface at 0, 56.9 and random
incidence, so there the angle is a field that varies inside the table. All
three are :class:`PredictedScatteringSpectrum`, and
:attr:`PredictedScatteringSpectrum.model` says which solver produced the row.

What the book says these are worth
-----------------------------------
More than usual, because the book spends a page on it. The correlation
scattering coefficient "interprets any absorption as being scattering", so the
formulation "needs to be revised for surfaces that partially absorb"; the
random incidence values of the two-dimensional table "tend to have raised
values at low frequencies"; and the coefficient "does not discriminate between
different diffusers in a consistent manner", because it reads a redirection as
a dispersion. Each of those is quoted in the ``about`` of the table it belongs
to, with the page. A row here is a modelling result to compare against, not a
specification.

The summary rows
----------------
Each group of Tables C.1 and C.2 closes with a row labelled ``"h/L = 20"`` or
``"h/L = 40"``, which cannot be read at face value: every surface of every
group has L = 20 cm and h between 2 and 10 cm, so the ratio is between 0.1 and
0.5. Read as a percentage they resolve, and three of the six carry exactly the
values of a row of their own group, which is how the reading was settled. The
book explains them nowhere. They are kept as rows, because they are rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from ..._internal.catalogue import read_table, take
from ._scattering import ScatteringBands

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_PREDICTED_SCATTERING",
    "PredictedScatteringSpectrum",
    "predicted_scattering_named",
]


@dataclass(frozen=True, kw_only=True)
class PredictedScatteringSpectrum(ScatteringBands):
    """One computed surface at one angle, band by band.

    The band fields and the reading method come from
    :class:`~phonometry.materials.diffusers._scattering.ScatteringBands`,
    which a measured row carries too, and the two classes are siblings rather
    than one inheriting from the other, so a caller narrowing on the type
    learns which kind of number they hold. The two fields below are what a
    prediction has and a measurement does not.

    The two three-dimensional tables start at 250 Hz, so their four lowest
    band fields are ``None`` on every row: the book says the coefficient
    below that "should be taken to be 0" and prints nothing, and filling
    those cells with zeros would put the book's advice into the data where
    nobody could tell it from a computed value.

    :ivar angle_of_incidence_deg: The angle the row was computed at, in
        degrees from the normal. ``None`` where the page prints a word
        instead of a number: "Random" on an average over angles, "All/any" on
        the plane surface that scatters nothing at any of them, and
        :meth:`~phonometry.io.CatalogueRow.why_missing` says
        which.
    :ivar model: The solver behind the row, as the table's own title and the
        section that describes it give it: a two-dimensional or a
        three-dimensional boundary element prediction. It is not a hedge and
        not a note: it is what separates these rows from the measured ones.
    """

    angle_of_incidence_deg: float | None = None
    model: str = ""


#: The hedges these tables spell as a set rather than a mapping.
_SETS = ("approximate", "bounded_above", "bounded_below")

#: The published tables this catalogue reads, one data file per table.
_TABLES = ("cox-2017-table-c1", "cox-2017-table-c2", "cox-2017-table-c3")


def _load() -> dict[str, PredictedScatteringSpectrum]:
    """Every row of every packaged table, keyed ``"<table>/<row>"``."""
    rows: dict[str, PredictedScatteringSpectrum] = {}
    for table in _TABLES:
        source, records = read_table("phonometry.materials.diffusers", f"{table}.json")
        for record in records:
            key = f"{table}/{record['key']}"
            rows[key] = PredictedScatteringSpectrum(
                table=table, source=source, **take(record, frozen=_SETS)
            )
    return rows


#: Every predicted scattering coefficient this library has read from a
#: published page, keyed ``"<table>/<row>"``. Three files in
#: ``materials/diffusers/data/``, one per printed table, each citing its own
#: pages. Kept apart from
#: :data:`~phonometry.materials.diffusers.PUBLISHED_SCATTERING`, which holds
#: the measured ones.
PUBLISHED_PREDICTED_SCATTERING: Mapping[str, PredictedScatteringSpectrum] = (
    MappingProxyType(_load())
)


def predicted_scattering_named(name: str) -> tuple[PredictedScatteringSpectrum, ...]:
    """Every predicted row whose description or heading contains *name*.

    :param name: A fragment of the printed description or of the heading above
        it, matched without case. The headings are where the topology is:
        ``"sinusoidal"``, ``"batten"``, ``"triangle"``, since a row of its own
        reads ``"h = 4 cm, L = 20 cm"``.
    :return: The rows that match, in the order the tables are read, which is
        empty when no table has one.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in PUBLISHED_PREDICTED_SCATTERING.values()
        if wanted in row.name.casefold() or wanted in row.group.casefold()
    )
