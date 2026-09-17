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

So every row carries what the cell actually said: :attr:`SolidMaterial.estimated`
names the fields the page marks as estimates, :attr:`SolidMaterial.ranges`
carries the seven cells printed as an interval (two densities, two speeds and
three loss factors), :attr:`SolidMaterial.bounded_above` names the two of those
loss factors the page prints as an upper bound rather than a band, and :attr:`SolidMaterial.attributed_to` carries the per-cell credit for
the rows whose columns come from different authors. A field the table leaves
empty is ``None`` and not a guess.

What it is not
--------------
It is not a specification. Block densities vary by manufacturer, boards vary
by batch, and Hopkins says as much by printing ranges where a range is what is
known. Use a row to reproduce a worked example, to sanity-check a measurement,
or to get an order of magnitude; use a measurement for anything that has to be
right.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .elastic import youngs_modulus_from_plate_speed

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_SOLIDS",
    "SolidMaterial",
]

#: The source every row of this catalogue shares. Both pages are landscape and
#: neither prints a folio of its own, which is what the fourth folio spelling
#: of the provenance gate is for: it names the folios either side rather than
#: inventing one.
_TABLE_A2 = (
    "Hopkins (2007) Table A2, PDF pages 635-636 "
    "(no printed folio; between folios 607 and 610)"
)


@dataclass(frozen=True)
class SolidMaterial:
    """One row of a published materials table, with what the cell said.

    :ivar name: The material as the table names it, attribution stripped.
    :ivar longitudinal_speed_m_s: Quasi-longitudinal phase velocity ``c_L``,
        in m/s. Hopkins' footnote a states these "can be used as estimates for
        beams or plates", so the column is the plate speed for the purposes of
        :func:`~phonometry.solids.youngs_modulus_from_plate_speed`.
    :ivar poisson_ratio: Poisson's ratio ``nu``.
    :ivar thickness_critical_frequency_product_m_hz: The ``h.f_c`` column, in
        m Hz, computed by the book for the 343 m/s its heading states.
    :ivar density_kg_m3: Density ``rho``, in kg/m3, or ``None`` when the table
        prints a range instead of a value. The range is then in :attr:`ranges`.
    :ivar loss_factor: Internal loss factor for bending waves ``eta_int``, or
        ``None`` when the table prints a dash, a range or an upper bound.
    :ivar estimated: The fields the page marks with its "Estimate" footnote.
        Reading one of these as a measurement is the mistake this catalogue
        exists to prevent.
    :ivar ranges: ``(low, high)`` for each field the table prints as an
        interval rather than a value.
    :ivar bounded_above: Fields the table prints as ``<= x``, with ``x`` in
        :attr:`ranges` as ``(0.0, x)``.
    :ivar attributed_to: Per-field credit, for the rows whose columns the book
        takes from different authors.
    :ivar note: What the table says about this row beyond its numbers.
    :ivar source: Document, table and PDF pages.
    """

    name: str
    longitudinal_speed_m_s: float
    poisson_ratio: float
    thickness_critical_frequency_product_m_hz: float
    density_kg_m3: float | None = None
    loss_factor: float | None = None
    estimated: frozenset[str] = frozenset()
    ranges: Mapping[str, tuple[float, float]] = field(default_factory=dict)
    bounded_above: frozenset[str] = frozenset()
    attributed_to: Mapping[str, str] = field(default_factory=dict)
    note: str = ""
    source: str = _TABLE_A2

    def youngs_modulus_pa(self) -> float:
        """Young's modulus from the printed speed and density, in pascals.

        The table prints a wave speed and a density and no modulus, and the
        functions this library hands a solid to want the modulus, so the
        inversion happens here rather than in the caller's head. It is
        :func:`~phonometry.solids.youngs_modulus_from_plate_speed` on this
        row's own numbers.

        :return: Young's modulus ``E``, in pascals.
        :raises ValueError: for a row whose density the table printed as a
            range, because there is then no density to invert with.
        """
        if self.density_kg_m3 is None:
            low, high = self.ranges["density_kg_m3"]
            msg = (
                f"{self.name!r} has no single density: the table prints "
                f"{low:g} to {high:g} kg/m3, so a modulus follows only from a "
                "density you choose and can defend"
            )
            raise ValueError(msg)
        return youngs_modulus_from_plate_speed(
            self.longitudinal_speed_m_s,
            density_kg_m3=self.density_kg_m3,
            poisson_ratio=self.poisson_ratio,
        )

    def is_estimate(self, field_name: str) -> bool:
        """Whether the page marks this field as an estimate rather than a value.

        :param field_name: One of the numeric field names of this class.
        :return: ``True`` when the table carries its "Estimate" footnote there.
        """
        return field_name in self.estimated


#: Shorthand for the footnote that marks a cell "Estimate": it lands on the
#: same two fields in almost every row, so naming the pair once keeps the
#: table below readable and keeps the two spellings from drifting apart.
_NU_ETA = frozenset({"poisson_ratio", "loss_factor"})
_NU = frozenset({"poisson_ratio"})


def _row(
    name: str,
    speed: float,
    nu: float,
    hfc: float,
    *,
    density: float | None = None,
    eta: float | None = None,
    estimated: frozenset[str] = frozenset(),
    ranges: Mapping[str, tuple[float, float]] | None = None,
    bounded_above: frozenset[str] = frozenset(),
    attributed_to: Mapping[str, str] | None = None,
    note: str = "",
) -> SolidMaterial:
    """One row, in the column order the page prints, to keep the table legible."""
    return SolidMaterial(
        name=name,
        longitudinal_speed_m_s=speed,
        poisson_ratio=nu,
        thickness_critical_frequency_product_m_hz=hfc,
        density_kg_m3=density,
        loss_factor=eta,
        estimated=estimated,
        ranges=dict(ranges or {}),
        bounded_above=bounded_above,
        attributed_to=dict(attributed_to or {}),
        note=note,
    )


#: Every row of Hopkins Table A2, in the order it prints them: Hopkins (2007)
#: Table A2, PDF pages 635-636, which are landscape and carry no printed folio
#: of their own, sitting between folios 607 and 610. Two rows carry the same
#: material name at two densities, which is how the page prints them, so the
#: keys distinguish them by density rather than inventing a name.
PUBLISHED_SOLIDS: Mapping[str, SolidMaterial] = {
    "aircrete": _row(
        "Aircrete/Autoclaved Aerated Concrete (AAC) blocks (solid) connected "
        "with mortar or thin joint compound",
        1900.0,
        0.2,
        34.1,
        eta=0.0125,
        estimated=_NU,
        ranges={
            "density_kg_m3": (400.0, 800.0),
            "longitudinal_speed_m_s": (1600.0, 2300.0),
        },
        attributed_to={"row": "Hopkins"},
        note=(
            "the table prints the speed as 1900 with a typical range of 1600 "
            "to 2300 m/s, and the density only as a range"
        ),
    ),
    "aluminium": _row(
        "Aluminium",
        5100.0,
        0.34,
        12.7,
        density=2700.0,
        bounded_above=frozenset({"loss_factor"}),
        ranges={"loss_factor": (0.0, 0.001)},
        attributed_to={"row": "Heckl, 1981"},
    ),
    "brick": _row(
        "Bricks (solid) connected with mortar",
        2700.0,
        0.2,
        24.0,
        eta=0.01,
        estimated=_NU_ETA,
        ranges={"density_kg_m3": (1500.0, 2000.0)},
        attributed_to={"row": "Hopkins"},
    ),
    "calcium_silicate_block": _row(
        "Calcium-silicate blocks (solid) connected with thin joint compound",
        2500.0,
        0.2,
        25.9,
        density=1800.0,
        eta=0.01,
        estimated=_NU,
        attributed_to={"row": "Schmitz et al., 1999"},
    ),
    "chipboard": _row(
        "Chipboard",
        2200.0,
        0.3,
        29.5,
        density=760.0,
        eta=0.01,
        estimated=_NU_ETA,
        attributed_to={"row": "Hopkins"},
    ),
    "clinker_concrete_block_1030": _row(
        "Clinker concrete blocks (solid) connected with mortar",
        1850.0,
        0.2,
        35.1,
        density=1030.0,
        eta=0.01,
        estimated=_NU_ETA,
        attributed_to={"row": "Rindel, 1994"},
    ),
    "clinker_concrete_block_1720": _row(
        "Clinker concrete blocks (solid) connected with mortar",
        2200.0,
        0.2,
        29.5,
        density=1720.0,
        eta=0.01,
        estimated=_NU_ETA,
        attributed_to={"row": "Rindel, 1994"},
    ),
    "clinker_concrete_slab": _row(
        "Clinker concrete slabs",
        1910.0,
        0.2,
        34.0,
        density=1725.0,
        eta=0.01,
        estimated=_NU_ETA,
        attributed_to={"row": "Rindel, 1994"},
    ),
    "concrete_cast_in_situ": _row(
        "Concrete, cast in situ",
        3800.0,
        0.2,
        17.1,
        density=2200.0,
        eta=0.005,
        estimated=_NU_ETA,
        attributed_to={"row": "Hopkins"},
    ),
    "dense_aggregate_block": _row(
        "Dense aggregate blocks (solid) connected with mortar",
        3200.0,
        0.2,
        20.3,
        density=2000.0,
        eta=0.01,
        estimated=_NU_ETA,
        attributed_to={"row": "Hopkins"},
    ),
    "expanded_clay_block": _row(
        "Expanded clay blocks (solid) connected with mortar",
        2300.0,
        0.2,
        28.2,
        density=800.0,
        eta=0.007,
        estimated=_NU_ETA,
        attributed_to={"row": "Hopkins"},
    ),
    "glass": _row(
        "Glass",
        5200.0,
        0.24,
        12.5,
        density=2500.0,
        ranges={"loss_factor": (0.003, 0.006)},
        attributed_to={"row": "Hopkins"},
    ),
    "lightweight_aggregate_block": _row(
        "Lightweight aggregate blocks (solid) connected with mortar",
        2200.0,
        0.2,
        29.5,
        density=1400.0,
        eta=0.01,
        estimated=_NU_ETA,
        attributed_to={"row": "Hopkins"},
    ),
    "mdf": _row(
        "Medium Density Fibreboard (MDF)",
        2560.0,
        0.3,
        25.3,
        density=760.0,
        eta=0.01,
        estimated=_NU_ETA,
        attributed_to={"row": "Hopkins"},
    ),
    "mortar": _row(
        "Mortar",
        2450.0,
        0.2,
        26.5,
        density=1600.0,
        eta=0.013,
        attributed_to={"row": "Maysenholder and Horvatic, 1998"},
    ),
    "osb": _row(
        "Oriented Strand Board (OSB)",
        2570.0,
        0.3,
        25.2,
        density=590.0,
        eta=0.01,
        estimated=_NU_ETA,
        ranges={"longitudinal_speed_m_s": (2200.0, 3500.0)},
        attributed_to={"row": "Hopkins"},
        note=(
            "usually orthotropic, with 2200 to 3500 m/s depending on the "
            "direction; the quoted speed is the effective one"
        ),
    ),
    "perspex": _row(
        "Perspex, plexiglass",
        2350.0,
        0.3,
        27.6,
        density=1250.0,
        estimated=_NU,
        attributed_to={"row": "Hopkins"},
    ),
    "plaster_gypsum": _row(
        "Plaster, gypsum based",
        1610.0,
        0.2,
        40.3,
        density=650.0,
        eta=0.012,
        estimated=_NU_ETA,
        attributed_to={"row": "Hopkins"},
    ),
    "plasterboard_natural_gypsum": _row(
        "Plasterboard, natural gypsum",
        1490.0,
        0.3,
        43.5,
        density=860.0,
        eta=0.0141,
        estimated=_NU,
        attributed_to={"row": "Hopkins, 1999"},
    ),
    "plasterboard_flue_gas_gypsum": _row(
        "Plasterboard, combination of flue gas gypsum and natural gypsum",
        1810.0,
        0.3,
        35.8,
        density=680.0,
        eta=0.0125,
        estimated=_NU,
        attributed_to={"row": "Hopkins, 1999"},
    ),
    "plasterboard_glass_fibre": _row(
        "Plasterboard, gypsum with glass fibre and other additives",
        2010.0,
        0.3,
        32.3,
        density=800.0,
        estimated=_NU,
        attributed_to={"row": "Hopkins"},
    ),
    "plywood_birch": _row(
        "Plywood (Birch)",
        3850.0,
        0.3,
        16.8,
        density=710.0,
        eta=0.016,
        estimated=_NU,
        attributed_to={"row": "Hopkins"},
    ),
    "sand_cement_screed": _row(
        "Sand-cement screed",
        3250.0,
        0.2,
        20.0,
        density=2000.0,
        eta=0.01,
        estimated=_NU,
        attributed_to={"row": "Hopkins"},
    ),
    "steel": _row(
        "Steel",
        5270.0,
        0.28,
        12.3,
        density=7800.0,
        bounded_above=frozenset({"loss_factor"}),
        ranges={"loss_factor": (0.0, 0.0001)},
        attributed_to={
            "longitudinal_speed_m_s": "Fahy, 1985",
            "poisson_ratio": "Fahy, 1985",
            "loss_factor": "Heckl, 1981",
        },
    ),
    "timber_softwood": _row(
        "Timber (soft wood) used for joists, studs or battens",
        5000.0,
        0.3,
        13.0,
        density=440.0,
        estimated=_NU,
        attributed_to={"row": "Hopkins"},
    ),
}
