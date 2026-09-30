#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Normalized diffusion coefficients as a book computes them, one row per angle.

A diffusion coefficient says how even a surface's polar response is, and a
scattering coefficient says how much energy left the specular direction. A
surface can score high on one and low on the other, which is why ISO 17497 is
two documents and why this subpackage keeps two catalogues.
:mod:`.measured_scattering` holds what a turntable measured; this holds what a
boundary element model computed, and the difference is not a detail of
provenance. Nobody built these surfaces.

Why keep a table of predictions at all
---------------------------------------
Because the table is a designer's argument, and the argument is in the
numbers. It walks one semicylinder up to twelve, and the diffusion coefficient
at 1 kHz goes from 0.93 to 0.22: a single device and an array of the same
device are not the same surface, however identical the cross-section. It walks
a set of semiellipses from 1 cm deep to 30 cm, and at 5 kHz the coefficient
goes from 0.02 to 0.65. Neither of those follows from a formula in the book,
and a reader with a measurement of one diffuser has nothing to compare it
against without something like this.

The angle is a row, not a column
---------------------------------
The page prints three lines per surface, headed 0, 57 and Random, so a surface
is three rows here and :attr:`~phonometry.io.CatalogueRow.variant`
says which. The first two carry :attr:`NormalizedDiffusionSpectrum.angle_of_incidence_deg`;
the random one has none to carry, because it is an arithmetic mean over ten
angles and belongs to no single one, and asking it for the field gets that
sentence rather than a number.

What the numbers are worth
--------------------------
They are a two-dimensional prediction of a thin panel with an open back, as
the book's own Section 5.2.5 says, so they stand for single-plane devices such
as semicircular arcs and not for a two-dimensional array of anything. The
random incidence row is an arithmetic average over ten angles without Paris's
formulation, which a measurement to ISO 17497-2 would apply, so it is not the
same average a laboratory would report. Both facts are quoted in the ``about``
of the data file, in the book's words.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from ..._internal.catalogue import (
    BandedRow,
    read_table,
    rows_to_search,
    search_text,
    take,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "DIFFUSION_BANDS_HZ",
    "PUBLISHED_DIFFUSION",
    "NormalizedDiffusionSpectrum",
    "diffusion_named",
]

#: The one-third octave centre frequencies a published diffusion coefficient
#: table can print, in hertz. A table prints a subset; the field for a band it
#: does not print stays ``None`` on every row of it.
DIFFUSION_BANDS_HZ: tuple[int, ...] = (
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
class NormalizedDiffusionSpectrum(BandedRow):
    """One surface at one angle of incidence, with its coefficient in each band.

    :ivar diffusion_coefficient_100: Normalized diffusion coefficient in the
        100 Hz one-third octave band, dimensionless, as printed.
    :ivar diffusion_coefficient_125: The same in the 125 Hz band.
    :ivar diffusion_coefficient_160: The same in the 160 Hz band.
    :ivar diffusion_coefficient_200: The same in the 200 Hz band.
    :ivar diffusion_coefficient_250: The same in the 250 Hz band.
    :ivar diffusion_coefficient_315: The same in the 315 Hz band.
    :ivar diffusion_coefficient_400: The same in the 400 Hz band.
    :ivar diffusion_coefficient_500: The same in the 500 Hz band.
    :ivar diffusion_coefficient_630: The same in the 630 Hz band.
    :ivar diffusion_coefficient_800: The same in the 800 Hz band.
    :ivar diffusion_coefficient_1000: The same in the 1 kHz band.
    :ivar diffusion_coefficient_1250: The same in the 1.25 kHz band.
    :ivar diffusion_coefficient_1600: The same in the 1.6 kHz band.
    :ivar diffusion_coefficient_2000: The same in the 2 kHz band.
    :ivar diffusion_coefficient_2500: The same in the 2.5 kHz band.
    :ivar diffusion_coefficient_3150: The same in the 3.15 kHz band.
    :ivar diffusion_coefficient_4000: The same in the 4 kHz band.
    :ivar diffusion_coefficient_5000: The same in the 5 kHz band.
    :ivar angle_of_incidence_deg: The angle the row was computed at, in
        degrees from the normal, as the page heads its line. ``None`` on a
        random incidence row, which is a mean over ten angles and is not one
        of them; :meth:`~phonometry.io.CatalogueRow.why_missing`
        says so rather than leaving the caller to guess at a zero.
    """

    diffusion_coefficient_100: float | None = None
    diffusion_coefficient_125: float | None = None
    diffusion_coefficient_160: float | None = None
    diffusion_coefficient_200: float | None = None
    diffusion_coefficient_250: float | None = None
    diffusion_coefficient_315: float | None = None
    diffusion_coefficient_400: float | None = None
    diffusion_coefficient_500: float | None = None
    diffusion_coefficient_630: float | None = None
    diffusion_coefficient_800: float | None = None
    diffusion_coefficient_1000: float | None = None
    diffusion_coefficient_1250: float | None = None
    diffusion_coefficient_1600: float | None = None
    diffusion_coefficient_2000: float | None = None
    diffusion_coefficient_2500: float | None = None
    diffusion_coefficient_3150: float | None = None
    diffusion_coefficient_4000: float | None = None
    diffusion_coefficient_5000: float | None = None
    angle_of_incidence_deg: float | None = None

    _bands_hz: ClassVar[tuple[int, ...]] = DIFFUSION_BANDS_HZ
    _band_prefix: ClassVar[str] = "diffusion_coefficient_"
    _band_kind: ClassVar[str] = "a one-third octave"
    _bands_per_octave: ClassVar[int] = 3
    _table_kind: ClassVar[str] = "diffusion coefficient"

    def diffusion_coefficient(self, band_hz: int) -> float:
        """The coefficient in one band, or a refusal that says what the page had.

        :param band_hz: A one-third octave centre frequency from
            :data:`DIFFUSION_BANDS_HZ`.
        :return: The printed normalized diffusion coefficient, dimensionless.
        :raises ValueError: when the page has no number in that band, naming
            the row, the band and what the cell held instead; or when
            *band_hz* is not a band these tables print.
        """
        return self._in_band(band_hz)


#: The published tables this catalogue reads, one data file per table.
_TABLES = ("cox-2017-appendix-b",)


def _load() -> dict[str, NormalizedDiffusionSpectrum]:
    """Every row of every packaged table, keyed ``"<table>/<row>"``."""
    rows: dict[str, NormalizedDiffusionSpectrum] = {}
    for table in _TABLES:
        source, records = read_table("phonometry.materials.diffusers", f"{table}.json")
        for record in records:
            key = f"{table}/{record['key']}"
            rows[key] = NormalizedDiffusionSpectrum.from_printed(
                table=table, source=source, **take(record)
            )
    return rows


#: Every normalized diffusion coefficient this library has read from a
#: published page, keyed ``"<table>/<row>"``. One file per published table in
#: ``materials/diffusers/data/``, each citing its own page. A surface is three
#: rows, one per angle of incidence, and the key carries which.
PUBLISHED_DIFFUSION: Mapping[str, NormalizedDiffusionSpectrum] = MappingProxyType(
    _load()
)


def diffusion_named(
    name: str, *, catalogue: Mapping[str, NormalizedDiffusionSpectrum] | None = None
) -> tuple[NormalizedDiffusionSpectrum, ...]:
    """Every row whose description or section heading contains *name*.

    :param name: A fragment of the printed description or of the numbered
        heading above it, matched without case. The heading is where the
        geometry is, so ``"semiellipse"`` and ``"Schroeder"`` find their
        sections and ``"6 periods"`` finds the rows that say so.
    :param catalogue: The rows to search in place of
        :data:`PUBLISHED_DIFFUSION`: a catalogue of your own that
        :func:`phonometry.io.read_catalogue` returns, ``PUBLISHED_DIFFUSION |
        mine`` to search both at once, or any mapping of key to row (Default:
        ``None``, which searches :data:`PUBLISHED_DIFFUSION`).
    :return: The rows that match, in catalogue order, which is empty when no
        row has one. A surface answers with its three angles.
    :raises TypeError: for a *catalogue* that is not a mapping, or that holds a
        row that is not a :class:`NormalizedDiffusionSpectrum`, naming its key.
    """
    wanted = search_text(name)
    return tuple(
        row
        for row in rows_to_search(
            catalogue,
            PUBLISHED_DIFFUSION,
            NormalizedDiffusionSpectrum,
            "diffusion_named",
        )
        if wanted in search_text(row.name) or wanted in search_text(row.group)
    )
