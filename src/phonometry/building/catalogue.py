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
hedge of :class:`~phonometry._internal.catalogue.CatalogueRow` works on a band
the way it works on any other field, so a band the page leaves empty says so
through :meth:`~phonometry._internal.catalogue.CatalogueRow.why_missing`
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
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from .._internal.catalogue import CatalogueRow, read_table, take

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
class TransmissionLossSpectrum(CatalogueRow):
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

    def bands(self) -> tuple[int, ...]:
        """The octave bands this row prints a transmission loss for, in hertz."""
        return tuple(
            band
            for band in TRANSMISSION_LOSS_BANDS_HZ
            if getattr(self, f"transmission_loss_{band}_db") is not None
        )

    def spectrum(self) -> dict[int, float]:
        """The row as ``{band_hz: transmission_loss_db}`` over the bands it prints.

        A band the page left empty is left out rather than filled with a
        zero, which in decibels would read as a partition that transmits
        everything.
        """
        return {
            band: float(getattr(self, f"transmission_loss_{band}_db"))
            for band in self.bands()
        }

    def transmission_loss_db(self, band_hz: int) -> float:
        """The loss in one band, or a refusal that says what the page had.

        :param band_hz: An octave-band centre frequency from
            :data:`TRANSMISSION_LOSS_BANDS_HZ`.
        :return: The printed transmission loss, in decibels.
        :raises ValueError: when the page has no number in that band, naming
            the row, the band and what the cell held instead; or when
            *band_hz* is not a band these tables print.
        """
        if band_hz not in TRANSMISSION_LOSS_BANDS_HZ:
            msg = (
                f"{band_hz} Hz is not an octave band a transmission loss table "
                f"prints; the bands are {TRANSMISSION_LOSS_BANDS_HZ}"
            )
            raise ValueError(msg)
        return self.printed(
            f"transmission_loss_{band_hz}_db", wanted_by=f"the {band_hz} Hz band"
        )


#: The hedges these tables spell as a set rather than a mapping.
_SETS = ("approximate", "bounded_above", "bounded_below")

#: The published tables this catalogue reads, one data file per table.
_TABLES = ("bies-2017-table-7-6",)


def _load() -> dict[str, TransmissionLossSpectrum]:
    """Every row of every packaged table, keyed ``"<table>/<row>"``."""
    rows: dict[str, TransmissionLossSpectrum] = {}
    for table in _TABLES:
        source, records = read_table("phonometry.building", f"{table}.json")
        for record in records:
            key = f"{table}/{record['key']}"
            rows[key] = TransmissionLossSpectrum(
                table=table, source=source, **take(record, frozen=_SETS)
            )
    return rows


#: Every transmission loss row this library has read from a published page,
#: keyed ``"<table>/<row>"``. One file per published table in
#: ``building/data/``, each citing its own page. A construction is described
#: rather than named, and two rows of one description are told apart by the
#: thickness and the surface density beside them, which is why the key carries
#: the thickness and why :func:`transmission_loss_named` answers with every
#: match.
PUBLISHED_TRANSMISSION_LOSS: Mapping[str, TransmissionLossSpectrum] = MappingProxyType(
    _load()
)


def transmission_loss_named(name: str) -> tuple[TransmissionLossSpectrum, ...]:
    """Every published row whose printed description contains *name*.

    :param name: A fragment of the printed description, matched without case.
    :return: The rows whose description contains it, in the order the tables
        are read, which is empty when no page has one. It matches the printed
        description and nothing else: ``"door"`` answers with the ten rows
        that carry the word, and not with the hollow flush panel or the solid
        hardwood, which the page describes without it. The caller reads the
        thickness and the surface density to pick the row they mean.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in PUBLISHED_TRANSMISSION_LOSS.values()
        if wanted in row.name.casefold()
    )
