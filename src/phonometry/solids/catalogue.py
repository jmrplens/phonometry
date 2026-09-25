#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Solid materials as one published table prints them.

A caller who needs a Young's modulus for plasterboard has two bad options and
one good one. They can type a number they half remember, or they can open a
book and copy a row by hand into their script, which is the same thing with
extra steps. The good one is to read the row from a catalogue that says which
page it came from, and that is what this module is.

What it is careful about
------------------------
A materials table is not a list of measurements. Hopkins Table A2 marks most
of its Poisson ratios and internal loss factors with a footnote that reads,
in full, "Estimate", and it prints some of its densities as a range rather
than a number, some of its loss factors as an upper bound, and one of its wave
speeds with a note that the material is orthotropic and the figure quoted is
an effective value. A catalogue that flattened all of that into floats would
be claiming twenty-five measured Poisson ratios where the page offers four.

So every row carries what the cell actually said: :attr:`SolidMaterial.basis`
holds ``"estimated"`` for each field the page marks as an estimate, which
:meth:`~phonometry.io.CatalogueRow.basis_of` reads back,
:attr:`SolidMaterial.ranges` carries the seven cells printed as an interval
(two densities, two speeds and three loss factors),
:attr:`SolidMaterial.bounded_above` names the two of those loss factors the
page prints as an upper bound rather than a band, and
:attr:`SolidMaterial.attributed_to` carries the per-cell credit for the rows
whose columns come from different authors. A field the table leaves
empty is ``None`` and not a guess.

Where the rows live
-------------------
In ``solids/data/hopkins-2007-table-a2.json``, one record per material, read
at import through the package-data reader in ``phonometry._internal``. Rows are
data: keeping them in a file means a second table is a second file rather than
a longer literal, means a changed digit is one line of a diff, and means the
citation is written once, in the file that holds the rows it belongs to. The
provenance gate reads it from there too, so the comment above the constant and
the page it names cannot drift apart.

What it is not
--------------
It is not a specification. Block densities vary by manufacturer, boards vary
by batch, and Hopkins says as much by printing ranges where a range is what is
known. Use a row to reproduce a worked example, to sanity-check a measurement,
or to get an order of magnitude; use a measurement for anything that has to be
right.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from .._internal.catalogue import CatalogueRow, read_table, rows_to_search, take
from .elastic import (
    beam_longitudinal_speed,
    bulk_longitudinal_speed,
    plate_longitudinal_speed,
    thickness_critical_frequency_product,
    youngs_modulus_from_beam_speed,
    youngs_modulus_from_plate_speed,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .._internal.catalogue import Completion

__all__ = [
    "PUBLISHED_SOLIDS",
    "SolidMaterial",
    "solids_named",
]


@dataclass(frozen=True, kw_only=True)
class SolidMaterial(CatalogueRow):
    """One row of a published materials table, with what the cell said.

    Every quantity is optional, because no two of the books this catalogue
    reads print the same columns: Hopkins gives a plate speed and no modulus,
    Mechel a modulus and no speed, Cremer both plus a shear modulus, Arau
    neither. A field is ``None`` when the page had nothing to put there, and
    :meth:`why_missing` says what it had instead.

    **The three longitudinal speeds are three fields**, and a fourth holds the
    one a page prints without saying which it is. They are three different
    waves and the books do not agree on what to call them. Cremer's
    ``c_LII`` and Bies' ``sqrt(E/rho)`` are the bar speed; Hopkins'
    quasi-longitudinal is the plate speed; and the bulk speed is neither. At
    ``nu = 0.3`` the plate speed is 4.8 per cent above the bar speed and the
    bulk speed is 16 per cent above it, which is the figure Cremer prints
    under his Eq. (3.32) with the warning that it matters which one is meant.
    One field holding whichever the page happened to print is the mistake this
    catalogue exists to prevent, so there is no field that means "whichever
    one the page happened to print". :attr:`longitudinal_speed_m_s` is not
    that: it means the page printed a longitudinal speed and said nothing
    about which, which is a statement about the source rather than a shrug
    about the wave.

    **The loss factors are four fields** for the same reason. A flexural loss
    factor is measured in bending and a longitudinal one is not; an in-situ
    one is not a property of the material at all, but of a panel installed in
    a building, support and radiation included; and a page that prints one
    without saying which it is has said something weaker than any of the
    three, which is what :attr:`loss_factor` holds.

    The name, the citation, the variant and the hedges a cell can carry
    instead of a number (``basis``, ``ranges``, ``reported``,
    ``unquantified``, ``approximate``, ``derived``, ``converted``,
    ``carried``, ``attributed_to``) are the ones every catalogue row has;
    one is this catalogue's own and is described below. A cell the page
    marks as an estimate holds ``"estimated"`` in
    :attr:`SolidMaterial.basis`, and ``row.basis_of(field) == "estimated"``
    is the question to ask before reading it as a measurement, which is the
    mistake this catalogue exists to prevent.

    :ivar density_kg_m3: Density ``rho``, in kg/m3.
    :ivar youngs_modulus_pa: Young's modulus ``E``, in pascals.
    :ivar shear_modulus_pa: Shear modulus ``G``, in pascals.
    :ivar poisson_ratio: Poisson's ratio ``nu``.
    :ivar longitudinal_speed_m_s: A longitudinal speed for a page that prints
        one and does not say which of the three it is. Long's Table 12.1
        does, with no modulus and no Poisson ratio beside it, so there is
        nothing on the page to settle it and nothing here that guesses.
    :ivar bar_longitudinal_speed_m_s: ``sqrt(E/rho)``, the quasi-longitudinal
        speed on a rod, in m/s.
    :ivar plate_longitudinal_speed_m_s: ``sqrt(E/(rho(1-nu^2)))``, the
        quasi-longitudinal speed on a plate, in m/s.
    :ivar bulk_longitudinal_speed_m_s: the pure longitudinal speed in an
        unbounded solid, in m/s.
    :ivar transverse_speed_m_s: ``sqrt(G/rho)``, the shear wave speed, in m/s.
    :ivar loss_factor: Internal loss factor for a page that prints one and does
        not say which wave it was measured with. Mechel, Long and Arau all do.
        It is a separate field from the two below rather than a guess at which
        of them it is.
    :ivar flexural_loss_factor: Internal loss factor measured in bending.
    :ivar longitudinal_loss_factor: Internal loss factor measured with
        longitudinal waves.
    :ivar in_situ_loss_factor: Loss factor of a panel of this material as
        installed, which combines the internal, support and radiation losses
        and is therefore not a material constant.
    :ivar thickness_critical_frequency_product_m_hz: The ``h.f_c`` column, in
        m Hz, a property of the material alone and the cheapest cross-check
        there is between books that share no other column.
    :ivar borrowed: Field to the material it was taken from, for the cells a
        book fills from a similar material rather than leaving empty. A
        hedge like the shared ones: its keys name numeric fields of this
        class, and it is frozen when the row is built.
    """

    _number_hedges: ClassVar[tuple[str, ...]] = (
        *CatalogueRow._number_hedges,
        "borrowed",
    )

    density_kg_m3: float | None = None
    youngs_modulus_pa: float | None = None
    shear_modulus_pa: float | None = None
    poisson_ratio: float | None = None
    longitudinal_speed_m_s: float | None = None
    bar_longitudinal_speed_m_s: float | None = None
    plate_longitudinal_speed_m_s: float | None = None
    bulk_longitudinal_speed_m_s: float | None = None
    transverse_speed_m_s: float | None = None
    loss_factor: float | None = None
    flexural_loss_factor: float | None = None
    longitudinal_loss_factor: float | None = None
    in_situ_loss_factor: float | None = None
    thickness_critical_frequency_product_m_hz: float | None = None
    borrowed: Mapping[str, str] = field(default_factory=dict)

    _cell_words: ClassVar[Mapping[str, str]] = MappingProxyType(
        {
            "density_kg_m3": "the density",
            "poisson_ratio": "the Poisson ratio",
            "youngs_modulus_pa": "the modulus",
            "shear_modulus_pa": "the shear modulus",
            "plate_longitudinal_speed_m_s": "the plate speed",
            "bar_longitudinal_speed_m_s": "the bar speed",
            "bulk_longitudinal_speed_m_s": "the bulk speed",
            "transverse_speed_m_s": "the transverse speed",
        }
    )

    def _complete(self, cells: Completion) -> None:
        """Fill what follows from the cells the page printed.

        A materials table prints the columns its author needed, and the next
        reader needs others. Hopkins gives a plate speed and no modulus,
        Cremer a modulus and a bar speed and no plate speed, and comparing the
        two means converting one into the other. Doing it here, once, beats
        every caller doing it in their head, which is the conversion
        :mod:`phonometry.solids` was added for.

        Nothing is filled over a cell the page printed, or over one the row
        says something else about: a modulus beside the 18 to 30 GPa Bies
        prints for normal concrete would contradict the interval, and the
        speed Bies leaves blank for his aluminium honeycomb panels stays
        blank, because a one-dimensional speed means nothing in a honeycomb
        and :attr:`~phonometry.io.CatalogueRow.not_derivable` says so. Every
        value filled here is named in
        :attr:`~phonometry.io.CatalogueRow.derived`, with the cells it comes
        from.

        :param cells: The row's cells as the completion fills them in.
        """
        _elastic_constants(cells)
        _wave_speeds(cells)
        plate = cells.get(_PLATE)
        if plate is not None and cells.get(_HFC) is None:
            cells.fill(
                _HFC,
                lambda: thickness_critical_frequency_product(plate),
                _PLATE_HFC,
                inputs=(_PLATE,),
            )


#: How a field this library computed is described in
#: :attr:`SolidMaterial.derived`. The wording names the cells it came from, so
#: a reader of a derived number can go back to the ones that were read, and
#: :meth:`~phonometry.io.CatalogueRow.from_printed` adds the basis of each
#: printed cell it rests on when they are not all one.
_FROM_PLATE = "from the plate speed, the density and the Poisson ratio"
_FROM_BAR = "from the bar speed and the density"
_FROM_MODULUS = "from the modulus and the density"
_FROM_MODULUS_NU = "from the modulus, the density and the Poisson ratio"
_FROM_SHEAR = "from the shear modulus and the density"
_FROM_E_G = "from the modulus and the shear modulus"
_FROM_E_NU = "from the modulus and the Poisson ratio"
_PLATE_HFC = "from the plate speed, for the 343 m/s the heading assumes"

#: The field names the completion reads, as shorthands.
_HFC = "thickness_critical_frequency_product_m_hz"
_RHO = "density_kg_m3"
_NU = "poisson_ratio"
_E = "youngs_modulus_pa"
_G = "shear_modulus_pa"
_PLATE = "plate_longitudinal_speed_m_s"
_BAR = "bar_longitudinal_speed_m_s"
_BULK = "bulk_longitudinal_speed_m_s"
_TRANSVERSE = "transverse_speed_m_s"


def _elastic_constants(cells: Completion) -> None:
    """Fill the modulus, the shear modulus and the Poisson ratio.

    Any two of them give the third, and a speed with a density gives the
    modulus, so a page that prints a speed and a density has printed a modulus
    without writing it down.
    """
    rho = cells.get(_RHO)
    nu = cells.get(_NU)
    modulus = cells.get(_E)
    shear = cells.get(_G)
    plate = cells.get(_PLATE)
    bar = cells.get(_BAR)

    if modulus is None and rho is not None:
        if plate is not None and nu is not None:
            cells.fill(
                _E,
                lambda: youngs_modulus_from_plate_speed(
                    plate, density_kg_m3=rho, poisson_ratio=nu
                ),
                _FROM_PLATE,
                inputs=(_PLATE, _RHO, _NU),
            )
        elif bar is not None:
            cells.fill(
                _E,
                lambda: youngs_modulus_from_beam_speed(bar, density_kg_m3=rho),
                _FROM_BAR,
                inputs=(_BAR, _RHO),
            )
        modulus = cells.get(_E)
    if nu is None and modulus is not None and shear is not None:
        cells.fill(
            _NU,
            lambda: _poisson_ratio_from_moduli(modulus, shear),
            _FROM_E_G,
            inputs=(_E, _G),
        )
    elif shear is None and modulus is not None and nu is not None:
        cells.fill(
            _G, lambda: modulus / (2.0 * (1.0 + nu)), _FROM_E_NU, inputs=(_E, _NU)
        )


#: The Poisson ratio of an isotropic solid lies between these: at -1 its bulk
#: modulus is zero, and at 0.5 it is incompressible.
_ISOTROPIC_POISSON_LOW = -1.0
_ISOTROPIC_POISSON_HIGH = 0.5


def _poisson_ratio_from_moduli(modulus: float, shear: float) -> float:
    """``nu = E / (2 G) - 1``, refused where no isotropic solid has it.

    A modulus and a shear modulus that give a Poisson ratio outside -1 to 0.5
    are not the two moduli of one isotropic solid: the page printed them for
    different directions of an orthotropic material, or one of them is wrong.
    Either way the ratio they give is not the material's.

    :raises ValueError: for a ratio outside -1 to 0.5.
    """
    nu = modulus / (2.0 * shear) - 1.0
    if not _ISOTROPIC_POISSON_LOW < nu <= _ISOTROPIC_POISSON_HIGH:
        msg = (
            f"they give {nu:g}, and the Poisson ratio of an isotropic solid "
            f"lies between {_ISOTROPIC_POISSON_LOW:g} and "
            f"{_ISOTROPIC_POISSON_HIGH:g}"
        )
        raise ValueError(msg)
    return nu


def _wave_speeds(cells: Completion) -> None:
    """Fill the three longitudinal speeds and the transverse one.

    A page prints the wave its author needed and the reader needs another, so
    every row ends up carrying all four: the one that was read, and the ones
    that follow from the row's own cells.
    """
    rho = cells.get(_RHO)
    nu = cells.get(_NU)
    modulus = cells.get(_E)
    shear = cells.get(_G)

    if rho is not None and modulus is not None:
        if cells.get(_BAR) is None:
            cells.fill(
                _BAR,
                lambda: beam_longitudinal_speed(modulus, density_kg_m3=rho),
                _FROM_MODULUS,
                inputs=(_E, _RHO),
            )
        if nu is not None and cells.get(_PLATE) is None:
            cells.fill(
                _PLATE,
                lambda: plate_longitudinal_speed(
                    modulus, density_kg_m3=rho, poisson_ratio=nu
                ),
                _FROM_MODULUS_NU,
                inputs=(_E, _RHO, _NU),
            )
        if nu is not None and cells.get(_BULK) is None:
            cells.fill(
                _BULK,
                lambda: bulk_longitudinal_speed(
                    modulus, density_kg_m3=rho, poisson_ratio=nu
                ),
                _FROM_MODULUS_NU,
                inputs=(_E, _RHO, _NU),
            )
    if rho is not None and shear is not None and cells.get(_TRANSVERSE) is None:
        cells.fill(
            _TRANSVERSE,
            lambda: math.sqrt(shear / rho),
            _FROM_SHEAR,
            inputs=(_G, _RHO),
        )


#: The published tables this catalogue reads, in the order a reader should
#: meet them: the one whose columns the library was built around first, then
#: the one that over-determines the elastic constants and so checks it.
_TABLES = (
    "hopkins-2007-table-a2",
    "cremer-2005-table-4-3",
    "mechel-2008-table-3",
    "bies-2017-table-c1",
    "long-2014-table-12-1",
    "arau-1999-table-4-1",
    "norton-karczub-2003-appendix-4a",
    "norton-karczub-2003-table-6-1",
    "vigran-2008-table-3-1",
)


def _load() -> dict[str, SolidMaterial]:
    """Every row of every packaged table, keyed by table and row.

    The key names the table because the catalogue holds several books and
    they do not agree. Hopkins and Cremer both print a row called Steel, at
    the same density, with plate speeds that differ by four per cent and
    Poisson ratios that differ by three. A flat ``"steel"`` would have to pick
    one of them silently, and picking silently between two published values is
    the thing a catalogue exists not to do.
    """
    rows: dict[str, SolidMaterial] = {}
    for table in _TABLES:
        source, records = read_table("phonometry.solids", f"{table}.json")
        for record in records:
            rows[f"{table}/{record['key']}"] = SolidMaterial.from_printed(
                table=table, source=source, **take(record)
            )
    return rows


#: Every solid this library has read from a published page, keyed
#: ``"<table>/<row>"``: ``"hopkins-2007-table-a2/steel"`` and
#: ``"cremer-2005-table-4-3/steel"`` are two different published steels and
#: the key says which is which. The tables are
#: ``solids/data/hopkins-2007-table-a2.json``, Hopkins **Table A2** on PDF
#: pages 635-636, ``solids/data/cremer-2005-table-4-3.json``, Cremer
#: **Table 4.3** on PDF page 201, and ``solids/data/mechel-2008-table-3.json``,
#: Mechel **Table 3** on PDF pages 544-545, and
#: ``solids/data/bies-2017-table-c1.json``, Bies **Table C.1** on PDF pages
#: 747-750, and ``solids/data/long-2014-table-12-1.json``, Long **Table 12.1**
#: on PDF page 487, and ``solids/data/arau-1999-table-4-1.json``,
#: Arau-Puchades **Table 4.1** on PDF page 129. Use :func:`solids_named` to
#: gather every book's reading of one material.
PUBLISHED_SOLIDS: Mapping[str, SolidMaterial] = MappingProxyType(_load())


def solids_named(
    name: str, *, catalogue: Mapping[str, SolidMaterial] | None = None
) -> tuple[SolidMaterial, ...]:
    """Every published row for a material, across the books.

    Comparing two books is the point of holding both, and it has to be a
    deliberate act: a lookup that returned one row for "steel" would be
    choosing between published values on the caller's behalf.

    :param name: The material name as a table prints it, matched without
        regard to case: ``"Steel"``, ``"steel"``.
    :param catalogue: The rows to search in place of :data:`PUBLISHED_SOLIDS`:
        a catalogue of your own that :func:`phonometry.io.read_catalogue`
        returns, ``PUBLISHED_SOLIDS | mine`` to search both at once, or any
        mapping of key to row (Default: ``None``, which searches
        :data:`PUBLISHED_SOLIDS`).
    :return: The rows whose :attr:`SolidMaterial.name` matches, in the order
        the tables are read, which is empty when no page names it.
    :raises TypeError: for a *catalogue* that is not a mapping, or that holds a
        row that is not a :class:`SolidMaterial`, naming its key.
    """
    wanted = name.casefold()
    return tuple(
        row
        for row in rows_to_search(
            catalogue, PUBLISHED_SOLIDS, SolidMaterial, "solids_named"
        )
        if row.name.casefold() == wanted
    )
