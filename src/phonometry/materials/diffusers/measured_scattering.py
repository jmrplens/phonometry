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
Every hedge of :class:`~phonometry._internal.catalogue.CatalogueRow` is keyed
by field name, so a band the page leaves empty says so through
:meth:`~phonometry._internal.catalogue.CatalogueRow.why_missing` rather than
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
:attr:`~phonometry._internal.catalogue.CatalogueRow.group` carries that
heading and :func:`scattering_named` matches on either.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from ..._internal.catalogue import BandedRow, read_table, take

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_SCATTERING",
    "SCATTERING_BANDS_HZ",
    "ScatteringCoefficientSpectrum",
    "scattering_named",
]

#: The one-third octave centre frequencies a published scattering table can
#: print, in hertz. A table prints a subset; the field for a band it does not
#: print stays ``None`` on every row of it.
SCATTERING_BANDS_HZ: tuple[int, ...] = (
    100,
    125,
    160,
    200,
    250,
    315,
    400,
    500,
    630,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
    3150,
    4000,
    5000,
)


@dataclass(frozen=True, kw_only=True)
class ScatteringCoefficientSpectrum(BandedRow):
    """One surface of a published table, with its coefficient in each band.

    The geometry is part of :attr:`~CatalogueRow.name`, as the page prints
    it, and the family it belongs to is
    :attr:`~CatalogueRow.group`: pulling ``h`` and ``L`` into fields would
    mean deciding what the height of a randomly arranged array of blocks is,
    and the pages do not agree on which letters they use.

    :ivar scattering_coefficient_100: Random incidence scattering
        coefficient in the 100 Hz one-third octave band, dimensionless, as
        printed.
    :ivar scattering_coefficient_125: The same in the 125 Hz band.
    :ivar scattering_coefficient_160: The same in the 160 Hz band.
    :ivar scattering_coefficient_200: The same in the 200 Hz band.
    :ivar scattering_coefficient_250: The same in the 250 Hz band.
    :ivar scattering_coefficient_315: The same in the 315 Hz band.
    :ivar scattering_coefficient_400: The same in the 400 Hz band.
    :ivar scattering_coefficient_500: The same in the 500 Hz band.
    :ivar scattering_coefficient_630: The same in the 630 Hz band.
    :ivar scattering_coefficient_800: The same in the 800 Hz band.
    :ivar scattering_coefficient_1000: The same in the 1 kHz band.
    :ivar scattering_coefficient_1250: The same in the 1.25 kHz band.
    :ivar scattering_coefficient_1600: The same in the 1.6 kHz band.
    :ivar scattering_coefficient_2000: The same in the 2 kHz band.
    :ivar scattering_coefficient_2500: The same in the 2.5 kHz band.
    :ivar scattering_coefficient_3150: The same in the 3.15 kHz band.
    :ivar scattering_coefficient_4000: The same in the 4 kHz band.
    :ivar scattering_coefficient_5000: The same in the 5 kHz band.
    """

    scattering_coefficient_100: float | None = None
    scattering_coefficient_125: float | None = None
    scattering_coefficient_160: float | None = None
    scattering_coefficient_200: float | None = None
    scattering_coefficient_250: float | None = None
    scattering_coefficient_315: float | None = None
    scattering_coefficient_400: float | None = None
    scattering_coefficient_500: float | None = None
    scattering_coefficient_630: float | None = None
    scattering_coefficient_800: float | None = None
    scattering_coefficient_1000: float | None = None
    scattering_coefficient_1250: float | None = None
    scattering_coefficient_1600: float | None = None
    scattering_coefficient_2000: float | None = None
    scattering_coefficient_2500: float | None = None
    scattering_coefficient_3150: float | None = None
    scattering_coefficient_4000: float | None = None
    scattering_coefficient_5000: float | None = None

    _bands_hz: ClassVar[tuple[int, ...]] = SCATTERING_BANDS_HZ
    _band_prefix: ClassVar[str] = "scattering_coefficient_"
    _band_kind: ClassVar[str] = "a one-third octave"
    _table_kind: ClassVar[str] = "scattering"

    def scattering_coefficient(self, band_hz: int) -> float:
        """The coefficient in one band, or a refusal that says what the page had.

        :param band_hz: A one-third octave centre frequency from
            :data:`SCATTERING_BANDS_HZ`.
        :return: The printed scattering coefficient, dimensionless.
        :raises ValueError: when the page has no number in that band, naming
            the row, the band and what the cell held instead; or when
            *band_hz* is not a band these tables print.
        """
        return self._in_band(band_hz)


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
