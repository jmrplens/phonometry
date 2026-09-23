#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The three numbers a panel needs before its transmission loss can be sketched.

A single panel does not attenuate sound the way the mass law says it does. The
mass law is a straight line rising six decibels an octave, and a real panel
leaves it twice: once at the bottom, where the panel is stiff and resonant
rather than limp, and once near the coincidence frequency, where a bending
wave in the panel and a sound wave in the air travel at the same speed along
the surface and the panel stops resisting at all. Between those two departures
the curve flattens into a plateau.

The plateau method is the cheap way to draw that shape. Rather than solving
the plate model, it places the plateau from three numbers that depend only on
what the panel is made of: how much mass a millimetre of it brings, how high
the plateau sits, and how wide it is in frequency. Norton & Karczub draw the
mass law first, then "the coincidence region is approximated by a horizontal
line whose height is obtained from Table 3.1"; the plateau starts where that
line meets the mass law, at a frequency A, ends at B, which the frequency
ratio places relative to A, and above B the curve rises at 10 dB per octave.
This module holds those three numbers, for the eight materials the table
lists, and :func:`phonometry.building.plateau_transmission_loss` draws the
curve from them: its ``building.PLATEAU_MATERIALS`` is built from the rows
here, so the table is typed once.

Why the first column is not a density
-------------------------------------
:attr:`PlateauMaterial.surface_density_per_mm_kg_m2` is kilograms per square
metre per millimetre of thickness, which is the material's density divided by
a thousand. Aluminium's 2.66 is 2660 kg/m3. It is held in the unit the page
prints rather than converted to a density, because the method is applied with
it in that form: multiply by the thickness in millimetres and the surface
density of the panel falls out. Converting it would make a caller divide by a
thousand again at the point of use, and a catalogue that stores a quantity in
a unit nobody uses it in has made the reader's work harder to look tidier.

What this is not
----------------
It is not a transmission loss spectrum. One of the three numbers is a
transmission loss, :attr:`PlateauMaterial.coincidence_height_db`, the level of
the plateau in decibels, and it holds only over the plateau and only as the
method's approximation to it. The measured and tabulated insulation of real
constructions lives in
:data:`~phonometry.building.PUBLISHED_TRANSMISSION_LOSS`, and the duct walls
in :data:`~phonometry.noise_control.PUBLISHED_DUCT_TRANSMISSION_LOSS`.

Where the rows live
-------------------
In ``solids/data/norton-karczub-2003-table-3-1.json``, read at import through
the package-data reader in ``phonometry._internal``, the same as every other
catalogue here.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from .._internal.catalogue import CatalogueRow, read_table, take

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_PLATEAU_DATA",
    "PlateauMaterial",
    "plateau_material_named",
]


@dataclass(frozen=True, kw_only=True)
class PlateauMaterial(CatalogueRow):
    """One material's plateau-method constants, as a page printed them.

    :ivar surface_density_per_mm_kg_m2: The mass a square metre of this
        material brings per millimetre of thickness, in kg/m2 per mm. It is
        the density divided by a thousand and is held as the page prints it;
        see the module docstring for why.
    :ivar coincidence_height_db: The height of the plateau, in decibels: the
        transmission loss the method gives the panel over the coincidence
        region, drawn as a horizontal line. It depends on the material and
        not on the thickness, which moves the plateau along the frequency
        axis and leaves its level where it is.
    :ivar plateau_frequency_ratio: The ratio of the two frequencies that bound
        the plateau, which the page writes B/A: A where the plateau meets the
        mass law, B where the curve starts to rise again. Dimensionless.
    """

    surface_density_per_mm_kg_m2: float | None = None
    coincidence_height_db: float | None = None
    plateau_frequency_ratio: float | None = None


#: The published tables this catalogue reads, in the order it reads them.
_TABLES = ("norton-karczub-2003-table-3-1",)


def _load() -> dict[str, PlateauMaterial]:
    """Every row of every packaged table, keyed by table and row."""
    out: dict[str, PlateauMaterial] = {}
    for table in _TABLES:
        citation, rows = read_table("phonometry.solids", f"{table}.json")
        for row in rows:
            out[f"{table}/{row['key']}"] = PlateauMaterial(
                source=citation, table=table, **take(row)
            )
    return out


#: The plateau-method constants this library has read from a published page,
#: keyed ``"<table>/<row>"``. Each row names the page it was read on.
PUBLISHED_PLATEAU_DATA: Mapping[str, PlateauMaterial] = MappingProxyType(_load())


def plateau_material_named(name: str) -> tuple[PlateauMaterial, ...]:
    """Every row whose printed name contains *name*, case insensitively.

    :param name: Part of a material name, as the page prints it.
    :return: The matching rows, in the order the tables list them. Empty when
        nothing matches, which is not an error: a caller asking whether a
        material is tabulated gets an empty answer rather than an exception.
    """
    wanted = name.casefold()
    return tuple(
        row for row in PUBLISHED_PLATEAU_DATA.values() if wanted in row.name.casefold()
    )
