#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Absorption coefficients as the books print them, one row per finish.

The other catalogues of this package hold what a material *is*: a flow
resistivity, a porosity, a modulus. This one holds what a surface *did* in a
reverberation room, band by band, which is a different kind of number. It is
not a property of the material but of a specimen, a mounting and a room, and
the books say so in their own ways: Bies calls his "Sabine absorption
coefficients for some commonly used materials", which names the method and
hedges the sample in one line. So a row here is a measurement somebody once
made, kept because it is what the room-acoustics formulas of this library
ask for and because no reader has a reverberation room to hand.

Two catalogues, because the same page prints two quantities
------------------------------------------------------------
A table of absorption coefficients usually carries a few rows that are not
coefficients at all. Bies prints an audience "per person seated" as
:math:`S\bar{\alpha}` in square metres, an absorption area, in the same
columns as the coefficients above it, and Long prints a musician with
instrument the same way, in figures that are sabins. A coefficient is
dimensionless and bounded by the surface it belongs to; an area per person
is a quantity in square metres that is added, not multiplied. Holding both
under one field name would put a number in square metres behind a name that
says otherwise, so they are two classes and two catalogues,
:data:`PUBLISHED_ABSORPTION` and :data:`PUBLISHED_ABSORPTION_AREAS`, and the
data file tells them apart by the fields each row carries.

The band is the field
---------------------
Each octave band is a field of its own, ``absorption_coefficient_125`` and so
on, with the band's centre frequency in hertz as the suffix. That is not the
tidiest shape for a spectrum and it is the right one for a catalogue: every
hedge of :class:`~phonometry.io.CatalogueRow` is keyed by
field name, so a cell the page prints as a range, or leaves empty, or prints
wrong, is handled the way the same cell is handled in every other catalogue,
and :meth:`~phonometry.io.CatalogueRow.why_missing` answers
for a band the way it answers for a modulus. :meth:`AbsorptionSpectrum.bands`
and :meth:`AbsorptionSpectrum.spectrum` give the row back as a spectrum for
the caller who wants one.

What the numbers are worth
--------------------------
A reverberation-room coefficient depends on the sample size, the mounting and
the room, which is why ISO 354 fixes all three and why a coefficient above 1
is common and not an error. Bies prints no mounting; Long prints the ASTM
C423 mounting on most rows and the same fibreglass board twice, on the
test-room floor and over a 400 mm airspace, with a different spectrum each
time, and :attr:`AbsorptionSpectrum.mounting` keeps that apart. The books
that print a thickness print it in the name. A row is therefore a
representative value for a finish of that description on that mount, useful
for a reverberation estimate and for a sanity check on a measurement, and
not a specification of any product. Where a page says more than that about
its numbers, the ``about`` of its data file quotes it.

Long sets his table in inches, pounds and ounces, and his two rows that are
areas are in sabins, square feet of perfect absorption: the air names its
sabins, and the musician prints bare figures that are read in the same unit,
as its note explains. The names keep the inches, because a name is what the
page prints; the areas are converted to square metres at load, because a
field named ``m2`` holds square metres or it lies, and each converted cell
keeps the page's figure and its unit.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar

from ..._internal.catalogue import BandedRow, read_table, take

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "ABSORPTION_BANDS_HZ",
    "PUBLISHED_ABSORPTION",
    "PUBLISHED_ABSORPTION_AREAS",
    "AbsorptionAreaSpectrum",
    "AbsorptionSpectrum",
    "absorption_named",
]

#: The octave-band centre frequencies an absorption table can print, in
#: hertz. A table prints a subset, six or seven of them; the field for a band
#: it does not print stays ``None`` on every row.
ABSORPTION_BANDS_HZ: tuple[int, ...] = (63, 125, 250, 500, 1000, 2000, 4000, 8000)


@dataclass(frozen=True, kw_only=True)
class AbsorptionSpectrum(BandedRow):
    """One finish of a published table, with its coefficient in each band.

    The hedges of :class:`~phonometry.io.CatalogueRow` apply
    to each band as to any other field, and the material's thickness,
    density or mounting are part of :attr:`name`, as the page prints them,
    because the books print them there and pulling them into fields would
    mean deciding what "heavy carpet on concrete" is a thickness of.

    :ivar absorption_coefficient_63: Sabine absorption coefficient in the
        63 Hz octave band, dimensionless, as printed.
    :ivar absorption_coefficient_125: The same in the 125 Hz band.
    :ivar absorption_coefficient_250: The same in the 250 Hz band.
    :ivar absorption_coefficient_500: The same in the 500 Hz band.
    :ivar absorption_coefficient_1000: The same in the 1 kHz band.
    :ivar absorption_coefficient_2000: The same in the 2 kHz band.
    :ivar absorption_coefficient_4000: The same in the 4 kHz band.
    :ivar absorption_coefficient_8000: The same in the 8 kHz band.
    :ivar mounting: The test mounting the page prints beside the row, as it
        prints it: ``"A"``, ``"E400"``, ``"F"``. Long prints one on most rows
        and says they are the mountings of ASTM C423, A being the specimen
        laid on the test-room surface, E400 the specimen over a 400 mm
        airspace and F the duct-liner fixture, and that "the airspace behind
        the material greatly affects the results", which is why the same
        board is two rows here when the page prints it on two mounts. Empty
        for a page that prints no mounting, which is not the same as
        mounting A.
    """

    absorption_coefficient_63: float | None = None
    absorption_coefficient_125: float | None = None
    absorption_coefficient_250: float | None = None
    absorption_coefficient_500: float | None = None
    absorption_coefficient_1000: float | None = None
    absorption_coefficient_2000: float | None = None
    absorption_coefficient_4000: float | None = None
    absorption_coefficient_8000: float | None = None
    mounting: str = ""

    _bands_hz: ClassVar[tuple[int, ...]] = ABSORPTION_BANDS_HZ
    _band_prefix: ClassVar[str] = "absorption_coefficient_"
    _band_kind: ClassVar[str] = "an octave"
    _table_kind: ClassVar[str] = "absorption"

    def absorption_coefficient(self, band_hz: int) -> float:
        """The coefficient in one band, or a refusal that says what the page had.

        :param band_hz: An octave-band centre frequency from
            :data:`ABSORPTION_BANDS_HZ`.
        :return: The printed coefficient, as a float.
        :raises ValueError: when the page has no number in that band, naming
            the row, the band and what the cell held instead; or when
            *band_hz* is not a band any absorption table prints.
        """
        return self._in_band(band_hz)


@dataclass(frozen=True, kw_only=True)
class AbsorptionAreaSpectrum(BandedRow):
    """One row a table prints as an absorption area rather than a coefficient.

    An audience, a chair, a person standing: things a book prices per unit in
    square metres of equivalent absorption, because they have no surface area
    a coefficient could multiply. The fields carry the unit in their name so
    that a number from here cannot be mistaken for a coefficient.

    :ivar absorption_area_63_m2: Equivalent absorption area in the 63 Hz
        octave band, in square metres per unit of :attr:`per`.
    :ivar absorption_area_125_m2: The same in the 125 Hz band.
    :ivar absorption_area_250_m2: The same in the 250 Hz band.
    :ivar absorption_area_500_m2: The same in the 500 Hz band.
    :ivar absorption_area_1000_m2: The same in the 1 kHz band.
    :ivar absorption_area_2000_m2: The same in the 2 kHz band.
    :ivar absorption_area_4000_m2: The same in the 4 kHz band.
    :ivar absorption_area_8000_m2: The same in the 8 kHz band.
    :ivar per: What one unit of the area belongs to, as the page says it:
        ``"person"`` for an audience row, ``"seat"`` for a chair, and a
        cubic metre of air for the one row Long prints as an absorption per
        volume, which is the air term of a Sabine sum by another name.
    """

    absorption_area_63_m2: float | None = None
    absorption_area_125_m2: float | None = None
    absorption_area_250_m2: float | None = None
    absorption_area_500_m2: float | None = None
    absorption_area_1000_m2: float | None = None
    absorption_area_2000_m2: float | None = None
    absorption_area_4000_m2: float | None = None
    absorption_area_8000_m2: float | None = None
    per: str = "person"

    _bands_hz: ClassVar[tuple[int, ...]] = ABSORPTION_BANDS_HZ
    _band_prefix: ClassVar[str] = "absorption_area_"
    _band_suffix: ClassVar[str] = "_m2"
    _band_kind: ClassVar[str] = "an octave"
    _table_kind: ClassVar[str] = "absorption"


#: The hedges these tables spell as a set rather than a mapping.
_SETS = ("approximate", "bounded_above", "bounded_below")

#: The published tables this catalogue reads, in the order the books print
#: them, one data file per table.
_TABLES = (
    "bies-2017-table-6-2",
    "long-2014-table-7-1",
    "cox-2017-appendix-a",
    "arau-1999-table-6-1",
    "everest-2001-appendix",
)

#: A square foot in square metres, exact since the 1959 definition of the
#: yard. Long's two absorption areas are in sabins, which in a table set in
#: inches and pounds are square feet of perfect absorption.
_SQUARE_FOOT_M2 = 0.09290304

#: A thousand cubic feet in cubic metres, exact for the same reason. Long
#: prints the absorption of air "per 1000 cubic feet".
_THOUSAND_CUBIC_FEET_M3 = 28.316846592

#: The imperial suffixes a data file may write an area field with, each with
#: the factor that takes the page's figure to the metric field and the unit
#: the figure is in, which :attr:`~phonometry.io.CatalogueRow.converted` keeps
#: beside it.
_IMPERIAL_AREAS = (
    (
        "_ft2_per_1000_ft3",
        _SQUARE_FOOT_M2 / _THOUSAND_CUBIC_FEET_M3,
        "sabins per 1000 ft3",
    ),
    ("_ft2", _SQUARE_FOOT_M2, "sabins"),
)


def _is_area(record: Mapping[str, object]) -> bool:
    """Whether a data-file row is an absorption area rather than a coefficient.

    The row says so by the fields it carries: an area row names its bands as
    ``absorption_area_<band>_m2`` and a coefficient row as
    ``absorption_coefficient_<band>``, and a row that carried both would be
    a defect the dataclass refuses at construction.
    """
    return any(key.startswith("absorption_area_") for key in record)


def _metric(fields: dict[str, Any]) -> dict[str, Any]:
    """The area fields of a row in square metres, converted where printed otherwise.

    A data file writes what the page prints, so a table set in feet writes
    ``absorption_area_125_ft2`` and the number beside it is the page's
    figure, in sabins. The row holds square metres, because every other row
    does and because a caller adding an audience to a room in metres cannot
    be handed square feet under a field that says ``m2``. The conversion is
    done here, once, and :attr:`~phonometry.io.CatalogueRow.converted` keeps
    the page's figure and its unit, so the page's own number is never more
    than a lookup away. It is not a derivation: the value is the page's, in
    another unit. The unit is the suffix the data file writes, and a page
    that prints its figures bare, as Long does for his musician, says in the
    row's note why they are sabins.
    """
    metric_fields = dict(fields)
    converted = dict(fields.get("converted", {}))
    for name, value in fields.items():
        for suffix, factor, unit in _IMPERIAL_AREAS:
            if name.startswith("absorption_area_") and name.endswith(suffix):
                metric = f"{name.removesuffix(suffix)}_m2"
                del metric_fields[name]
                metric_fields[metric] = value * factor
                converted[metric] = (repr(value), unit)
                break
    if converted:
        metric_fields["converted"] = converted
    return metric_fields


def _load() -> tuple[dict[str, AbsorptionSpectrum], dict[str, AbsorptionAreaSpectrum]]:
    """Every row of every packaged table, split by the quantity it holds."""
    coefficients: dict[str, AbsorptionSpectrum] = {}
    areas: dict[str, AbsorptionAreaSpectrum] = {}
    for table in _TABLES:
        source, records = read_table("phonometry.materials.absorbers", f"{table}.json")
        for record in records:
            key = f"{table}/{record['key']}"
            fields = take(record, frozen=_SETS)
            if _is_area(record):
                areas[key] = AbsorptionAreaSpectrum(
                    table=table, source=source, **_metric(fields)
                )
            else:
                coefficients[key] = AbsorptionSpectrum(
                    table=table, source=source, **fields
                )
    return coefficients, areas


_COEFFICIENTS, _AREAS = _load()

#: Every absorption coefficient row this library has read from a published
#: page, keyed ``"<table>/<row>"``. One file per published table in
#: ``materials/absorbers/data/``, each citing its own page. The same finish
#: appears in several books under names that differ by a word, which is why
#: :func:`absorption_named` exists and why no lookup here chooses between
#: them.
PUBLISHED_ABSORPTION: Mapping[str, AbsorptionSpectrum] = MappingProxyType(_COEFFICIENTS)

#: The rows the same pages print as an equivalent absorption area per person
#: or per seat, kept apart from the coefficients because they are added to a
#: room's absorption rather than multiplied by a surface. Read from the same
#: files in ``materials/absorbers/data/`` as the coefficients.
PUBLISHED_ABSORPTION_AREAS: Mapping[str, AbsorptionAreaSpectrum] = MappingProxyType(
    _AREAS
)


def absorption_named(name: str) -> tuple[AbsorptionSpectrum, ...]:
    """Every published coefficient row whose name contains *name*.

    A finish is described rather than named, and no two books describe one
    the same way, so this matches a fragment inside the printed name, without
    regard to case: ``"carpet"`` answers with every carpet of every table,
    and the caller reads the names to pick the one that is the carpet they
    mean. That is deliberate. A lookup that returned one row for "carpet"
    would be choosing a thickness, a backing and a floor on the caller's
    behalf.

    :param name: A fragment of the printed name, matched without case.
    :return: The rows whose :attr:`AbsorptionSpectrum.name` contains it, in
        the order the tables are read, which is empty when no page has one.
    """
    wanted = name.casefold()
    return tuple(
        row for row in PUBLISHED_ABSORPTION.values() if wanted in row.name.casefold()
    )
