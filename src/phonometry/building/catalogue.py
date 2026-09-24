#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Transmission loss as the books print it, one row per construction.

A partition's transmission loss is not a property of a material. It is what
one wall, built one way and mounted one way, did in one laboratory, and the
number changes with the studs, the ties, the sealing of the joints and the
size of the specimen. The models of :mod:`phonometry.building.prediction`
compute it from mass, stiffness and geometry; this module holds what was
measured, so that a prediction has something published to sit beside.

Why a catalogue of measurements is worth keeping
------------------------------------------------
The mass law gives a straight line. A real partition departs from it at the
critical frequency, at the mass-air-mass resonance of a double leaf and
wherever a stud shorts the two leaves together, and the size of those
departures is what a table like this shows and no formula in the book
reproduces. Two rows of the same brick wall, same mass and same thickness,
differ by 15 dB at 500 Hz and by 9 at 4 kHz because one is tied with strips
and the other with expanded metal, which is the whole argument for resilient
connections and is in the table rather than in the theory.

What the row carries
--------------------
Each octave band is a field of its own, ``transmission_loss_500_db`` and so
on, with the band's centre frequency in hertz and the unit in the name. Every
hedge of :class:`~phonometry.io.CatalogueRow` works on a band
the way it works on any other field, so a band the page leaves empty says so
through :meth:`~phonometry.io.CatalogueRow.why_missing`
rather than answering zero. The thickness and the surface density the page
prints beside the description are fields of their own, because they are what a
reader compares two constructions by, and because the mass law needs the
second one.

What the numbers are worth
--------------------------
Bies calls his values "representative" and says only that they come from tests
published "by manufacturers and testing laboratories", without naming a
measurement standard, a mounting or a source for any row; that sentence is
quoted in full in the ``about`` of the data file. The qualifier the book does
give is "field incidence", which is the transmission loss of a diffuse field
over the range of angles a laboratory measures, and is what its own theory
computes. So a row here is a published measurement of a construction of that
description, useful for a sanity check and for an order of magnitude, and it
is not a specification of any wall anybody will build.

ASHRAE says as little and says it plainly: its nine machine equipment room
constructions are "compiled from controlled laboratory tests and represent a
condition typically superior to that found in field installations, because the
in situ acoustical performance of any wall, floor, or ceiling is adversely
affected by flanking paths, holes, penetrations, and other anomalies". No
laboratory, standard or reference is named for any of them either. Those rows
are here and the duct walls of the same chapter are not, because a duct wall is
measured in two directions that are different numbers and is indexed by the
duct's cross section, length and sheet gauge; it is published from
:mod:`phonometry.noise_control.duct_walls`.

Rossing's Table 11.4 is the same kind of row with fewer bands: twenty-three
common partitions, six octaves from 125 Hz to 4 kHz and a sound transmission
class, with no source, laboratory or standard named for any of them.

Tables that print a rating and nothing else
-------------------------------------------
Chapter 31 of the Spanish edition of Harris prints seven tables of sound
transmission class alone, with no frequency band anywhere: stud walls in six
conditions, concrete block walls of two weights, block walls under six
plasterboard mountings, doors unsealed and sealed, exterior doors, sealed
windows and floor-ceiling systems. Each is a row of this catalogue with every
band empty, and the rating in :attr:`TransmissionLossSpectrum.sound_transmission_class`.
A caller after a spectrum reads the band fields and finds ``None``;
:meth:`TransmissionLossSpectrum.transmission_loss_db` then refuses with the
row and the band, because the page printed nothing there.

Most of those tables print one construction under several conditions, as
columns: the plasterboard layers and the cavity absorbent of Table 31.2, the
sealing of the doors of Table 31.6. A column is a row here, the construction
is its :attr:`~phonometry.io.CatalogueRow.name` and the
column its :attr:`~phonometry.io.CatalogueRow.variant`,
composed from the printed headings above the cell. The window table is
printed the other way round, with the ratings as rows and the glazings as
cells, and is turned so that a row is a window. A row the page leaves blank
is a configuration it does not rate and has no row.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from .._internal.catalogue import BandedRow, read_table, take

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_TRANSMISSION_LOSS",
    "TRANSMISSION_LOSS_BANDS_HZ",
    "TransmissionLossSpectrum",
    "transmission_loss_named",
]

#: The octave-band centre frequencies a published transmission loss table can
#: print, in hertz. A table prints a subset; the field for a band it does not
#: print stays ``None`` on every row of it.
TRANSMISSION_LOSS_BANDS_HZ: tuple[int, ...] = (
    63,
    125,
    250,
    500,
    1000,
    2000,
    4000,
    8000,
)


@dataclass(frozen=True, kw_only=True)
class TransmissionLossSpectrum(BandedRow):
    """One construction of a published table, with its loss in each band.

    :ivar transmission_loss_63_db: Airborne sound transmission loss in the
        63 Hz octave band, in decibels, as printed.
    :ivar transmission_loss_125_db: The same in the 125 Hz band.
    :ivar transmission_loss_250_db: The same in the 250 Hz band.
    :ivar transmission_loss_500_db: The same in the 500 Hz band.
    :ivar transmission_loss_1000_db: The same in the 1 kHz band.
    :ivar transmission_loss_2000_db: The same in the 2 kHz band.
    :ivar transmission_loss_4000_db: The same in the 4 kHz band.
    :ivar transmission_loss_8000_db: The same in the 8 kHz band.
    :ivar thickness_mm: The overall thickness of the construction, in
        millimetres, as the page prints it beside the description. It is the
        assembly's thickness and not a leaf's: a double wall prints the pair
        and the cavity together.
    :ivar surface_density_kg_m2: The mass per unit area, in kilograms per
        square metre, as printed. This is what the mass law takes, and what
        two rows of the same description are told apart by.
    :ivar sound_transmission_class: The single-number rating the page prints
        beside the spectrum, where it prints one. It is not a band value and
        it does not follow from the ones beside it: an STC is computed from
        third-octave data, so a table that prints octave bands and an STC is
        printing two readings of one measurement and this catalogue keeps
        both. Empty for a page that rates nothing.
    :ivar block_mass_kg: The mass of one masonry block, in kilograms, where a
        page prints it beside the rating. It is a mass per block and not per
        square metre, so it is not a surface density and is not comparable
        with :attr:`surface_density_kg_m2`: Harris Table 31.3 tells its
        lightweight and normal-weight walls of one thickness apart by it.
    :ivar refers_to_row: The row this row's printed description refers to
        instead of repeating itself, named by the number the table prints.
        Harris Table 31.9 prints three floors once and the rows after them as
        "Igual que 8"; the printed text is kept whole in
        :attr:`~phonometry.io.CatalogueRow.name`, and this is
        the row it inherits from, resolved as
        ``PUBLISHED_TRANSMISSION_LOSS[f"{row.table}/{row.refers_to_row}"]``.
        Empty when the description stands on its own.
    """

    transmission_loss_63_db: float | None = None
    transmission_loss_125_db: float | None = None
    transmission_loss_250_db: float | None = None
    transmission_loss_500_db: float | None = None
    transmission_loss_1000_db: float | None = None
    transmission_loss_2000_db: float | None = None
    transmission_loss_4000_db: float | None = None
    transmission_loss_8000_db: float | None = None
    thickness_mm: float | None = None
    surface_density_kg_m2: float | None = None
    sound_transmission_class: float | None = None
    block_mass_kg: float | None = None
    refers_to_row: str = ""

    _bands_hz: ClassVar[tuple[int, ...]] = TRANSMISSION_LOSS_BANDS_HZ
    _band_prefix: ClassVar[str] = "transmission_loss_"
    _band_suffix: ClassVar[str] = "_db"
    _band_kind: ClassVar[str] = "an octave"
    _table_kind: ClassVar[str] = "transmission loss"

    def transmission_loss_db(self, band_hz: int) -> float:
        """The loss in one band, or a refusal that says what the page had.

        :param band_hz: An octave-band centre frequency from
            :data:`TRANSMISSION_LOSS_BANDS_HZ`.
        :return: The printed transmission loss, in decibels.
        :raises ValueError: when the page has no number in that band, naming
            the row, the band and what the cell held instead; or when
            *band_hz* is not a band these tables print.
        """
        return self._in_band(band_hz)


#: The published tables this catalogue reads, one data file per table.
_TABLES = (
    "bies-2017-table-7-6",
    "ashrae-2019-table-40",
    "rossing-2014-table-11-4",
    "harris-1995-table-31-2",
    "harris-1995-table-31-3",
    "harris-1995-table-31-5",
    "harris-1995-table-31-6",
    "harris-1995-table-31-7",
    "harris-1995-table-31-8",
    "harris-1995-table-31-9",
)


def _load() -> dict[str, TransmissionLossSpectrum]:
    """Every row of every packaged table, keyed ``"<table>/<row>"``."""
    rows: dict[str, TransmissionLossSpectrum] = {}
    for table in _TABLES:
        source, records = read_table("phonometry.building", f"{table}.json")
        for record in records:
            key = f"{table}/{record['key']}"
            rows[key] = TransmissionLossSpectrum.from_printed(
                table=table, source=source, **take(record)
            )
    return rows


#: Every transmission loss row this library has read from a published page,
#: keyed ``"<table>/<row>"``. One file per published table in
#: ``building/data/``, each citing its own page. A construction is described
#: rather than named, and two rows of one description are told apart by the
#: thickness and the surface density beside them, which is why the key carries
#: the thickness and why :func:`transmission_loss_named` answers with every
#: match. The second table is the nine machine equipment room walls, floors and
#: ceilings of ASHRAE Chapter 49, which are a partition measured the way any
#: partition is and belong here rather than beside the duct walls of the same
#: chapter. Rossing's Table 11.4 adds twenty-three spectra in six bands, and
#: seven tables of Harris Chapter 31 add a hundred and twenty-nine ratings with
#: no band at all.
PUBLISHED_TRANSMISSION_LOSS: Mapping[str, TransmissionLossSpectrum] = MappingProxyType(
    _load()
)


def transmission_loss_named(name: str) -> tuple[TransmissionLossSpectrum, ...]:
    """Every published row whose printed description contains *name*.

    :param name: A fragment of the printed description, matched without case.
    :return: The rows whose description contains it, in the order the tables
        are read, which is empty when no page has one. It matches the printed
        description and nothing else, in the language the page is set in:
        ``"door"`` answers with the rows that carry the word, and not with
        Bies's hollow flush panel or solid hardwood, which the page describes
        without it, nor with the doors of the Spanish edition of Harris, which
        are ``"puerta"``. The caller reads the thickness, the surface density
        and the variant to pick the row they mean.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in PUBLISHED_TRANSMISSION_LOSS.values()
        if wanted in row.name.casefold()
    )
