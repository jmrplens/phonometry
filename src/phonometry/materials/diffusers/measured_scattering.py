#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Scattering coefficients as the books print them, one row per surface.

A geometric room acoustics model asks for one number per surface per band,
the scattering coefficient, and has no way of working it out. The rest of
this subpackage computes it: :mod:`.reverberation_room_scattering` runs the
ISO 17497-1 procedure on four reverberation times, and :mod:`.design`
predicts a polar response from a well sequence. This module holds what other
people measured, so that a modeller who has neither a turntable nor a
boundary element solver has somewhere to start, and so that a measurement
made here has published values to sit beside.

Scattering is not diffusion, and both live here
------------------------------------------------
ISO 17497 is two documents and two quantities. Part 1 measures the
*scattering coefficient*, the fraction of reflected energy that leaves the
specular direction, from four reverberation times in a room with a turning
table; it says nothing about where that energy goes. Part 2 measures the
*diffusion coefficient*, how even the polar response is, and a surface can
score high on one and low on the other. A catalogue that put them in one
field would let a caller pass a diffusion coefficient to a model that wants
a scattering coefficient, which is a silent error, so they are two classes
and two catalogues: :data:`PUBLISHED_SCATTERING` here, and the diffusion
coefficients of ISO 17497-2 where they belong.

The band is the field
---------------------
These tables are set in one-third octave bands, so each band is a field of
its own, ``scattering_coefficient_1000`` and so on, with the band's centre
frequency in hertz as the suffix and no unit because the quantity has none.
Every hedge of :class:`~phonometry.io.CatalogueRow` is keyed
by field name, so a band the page leaves empty says so through
:meth:`~phonometry.io.CatalogueRow.why_missing` rather than
answering zero, and a zero here would read as a perfectly specular surface.
:meth:`ScatteringCoefficientSpectrum.bands` and
:meth:`~ScatteringCoefficientSpectrum.spectrum` hand the row back as a
spectrum for the caller who wants one.

What the numbers are worth
--------------------------
A row is a surface of that description, measured once, by one team, in one
room. Cox prints no uncertainty and no laboratory, and the spread between
teams is not small: the same battens, 10 cm high and 10 cm wide on a 20 cm
period, appear twice in Appendix D, credited to two different papers, and
read 0.28 and 0.44 at 630 Hz. Nothing is wrong with either; that is how wide
the method is. A coefficient above one is likewise not an error but what the
formula gave, since ISO 17497-1 derives it from a ratio of reverberation
times and puts no ceiling on the result.

The surfaces are described, not named. A row reads ``"h = w = 10 cm,
L = 2h"`` and means nothing without the group heading above it, so
:attr:`~phonometry.io.CatalogueRow.group` carries that
heading and :func:`scattering_named` matches on either.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from ..._internal.catalogue import read_table, take
from ._scattering import SCATTERING_BANDS_HZ, ScatteringBands

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_SCATTERING",
    "SCATTERING_BANDS_HZ",
    "ScatteringCoefficientSpectrum",
    "scattering_named",
]


@dataclass(frozen=True, kw_only=True)
class ScatteringCoefficientSpectrum(ScatteringBands):
    """One measured surface of a published table, band by band.

    The geometry is part of :attr:`~CatalogueRow.name`, as the page prints
    it, and the family it belongs to is :attr:`~CatalogueRow.group`: pulling
    ``h`` and ``L`` into fields would mean deciding what the height of a
    randomly arranged array of blocks is, and the pages do not agree on which
    letters they use.

    The band fields and the reading method come from
    :class:`~phonometry.materials.diffusers._scattering.ScatteringBands`,
    which a computed row carries too. What this class says, and what its name
    is for, is that the numbers were measured. It does not inherit from the
    predicted class and the predicted class does not inherit from it, so a
    caller narrowing on the type gets a straight answer.
    """


#: The hedges these tables spell as a set rather than a mapping.
_SETS = ("approximate", "bounded_above", "bounded_below")

#: The published tables this catalogue reads, one data file per table.
_TABLES = ("cox-2017-appendix-d",)


def _load() -> dict[str, ScatteringCoefficientSpectrum]:
    """Every row of every packaged table, keyed ``"<table>/<row>"``."""
    rows: dict[str, ScatteringCoefficientSpectrum] = {}
    for table in _TABLES:
        source, records = read_table("phonometry.materials.diffusers", f"{table}.json")
        for record in records:
            key = f"{table}/{record['key']}"
            rows[key] = ScatteringCoefficientSpectrum(
                table=table, source=source, **take(record, frozen=_SETS)
            )
    return rows


#: Every scattering coefficient this library has read from a published page,
#: keyed ``"<table>/<row>"``. One file per published table in
#: ``materials/diffusers/data/``, each citing its own page. A surface is
#: described rather than named, and the description alone does not identify a
#: row: the key carries whatever the page prints beside it that does, which
#: for one pair of rows is the paper the measurement is credited to and for
#: another is the folio the row sits on.
PUBLISHED_SCATTERING: Mapping[str, ScatteringCoefficientSpectrum] = MappingProxyType(
    _load()
)


def scattering_named(name: str) -> tuple[ScatteringCoefficientSpectrum, ...]:
    """Every published row whose description or group contains *name*.

    :param name: A fragment of the printed description or of the group
        heading above it, matched without case. The headings are where the
        useful words are: ``"pyramid"``, ``"vegetation"``, ``"batten"``, since
        a row of its own reads ``"h = w = 10 cm, L = 2h"``.
    :return: The rows that match, in the order the tables are read, which is
        empty when no page has one.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in PUBLISHED_SCATTERING.values()
        if wanted in row.name.casefold() or wanted in row.group.casefold()
    )
