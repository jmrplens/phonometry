#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Porous specimens as the pages that print them have them.

The five-parameter models of :mod:`~phonometry.materials.absorbers.porous`
take a flow resistivity, a porosity, a tortuosity and two characteristic
lengths, and a caller who has not characterised a specimen to ISO 9053 and
ISO 10534-2 has nowhere to get them. They get them here, from a book, with
the page the row came off attached to it.

What it is careful about
------------------------
A parameter table is a set of numbers someone fed a model, not a set of
measurements of a material, and the books say so in different ways. Allard and
Atalla print thirty-odd such rows across nineteen tables, every one of them
the input to a worked example, and one of the rows prints the word ``model``
in three of its cells because the quantity there is frequency dependent and no
single number stands for it. A catalogue that turned that word into a float
would be inventing a tortuosity nobody published, so
:attr:`~phonometry.io.CatalogueRow.unquantified` carries the word instead and
:meth:`~phonometry.io.CatalogueRow.why_missing` hands it back.

The same applies to the elastic constants. Table 6.1 prints a complex shear
modulus, ``220(1 + j0.1)`` N/cm2, and Table 11.8 prints the same specimen as a
Young's modulus of 4,4 MPa with a structural loss factor of 0,1; they agree,
because ``E / (2(1 + nu))`` is the real part of the first. A row therefore
stores the real modulus and the loss factor separately, which is the form the
poroelastic models take them in, and :meth:`PorousMaterial.frame_constants`
puts the complex number back together.

Two kinds of row
----------------
A **specimen** row is one sample, with every parameter a model needs beside
it: Allard and Atalla's tables are all of this kind, and a row of one of them
reproduces the worked example it belongs to. A **compiled** row is one
quantity over a class of material, gathered by its book from the literature:
Cox and D'Antonio compile a flow resistivity, a fibre diameter, a porosity,
two characteristic lengths and a tortuosity, and Mechel compiles a porosity
and the fibre data of three product groups. Almost every compiled cell is an
interval, because there is no such thing as the porosity of mineral wool,
only the range the measurements fall in, and a row that answered with the
midpoint of that range would be inventing a measurement.

The two kinds sit in one catalogue because they answer one question between
them: :func:`porous_materials_named` asks a name of every book at once, and a
specimen that falls outside the range its class is compiled in is worth
knowing about. What tells them apart is what a row holds: a specimen carries
several quantities, a compiled row carries one, and the compiled one carries
it as a range.

Where the rows live
-------------------
In ``absorbers/data/*.json``, one file per published table, read at import
through the package-data reader in ``phonometry._internal``. The citation is
written once, in the file that holds the rows it belongs to, and the
provenance gate reads it from there.

What it is not
--------------
It is not a material database. Every row here is a parameter set from a worked
example of a book, which is what makes it reproducible and also what makes it
specific: the foam of one figure is that foam, not foam. Use a row to
reproduce the example it belongs to, to sanity-check an implementation, or to
get an order of magnitude; characterise a specimen for anything that has to be
right.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from ..._internal.catalogue import CatalogueRow, read_table, take
from .porous import (
    PUBLISHED_AIR,
    delany_bazley,
    johnson_champoux_allard,
    miki,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from numpy.typing import ArrayLike

    from ..._internal.catalogue import Completion
    from ...fluids import Fluid
    from .porous import PorousMediumResult

__all__ = [
    "PUBLISHED_POROUS",
    "PorousMaterial",
    "porous_materials_named",
]

#: Micrometres per metre. The characteristic lengths are stored in the unit
#: their tables print and converted here, in one place, to the metres the
#: models take. The conversion divides rather than multiplying by 1e-6,
#: because 1e6 is exact in binary floating point and 1e-6 is not: dividing
#: returns the same double the literal ``90e-6`` parses to, which is what
#: keeps every figure and every printed digit where it was.
_MICROMETRES_PER_METRE = 1e6

#: How a field this library computed is described in
#: :attr:`~phonometry.io.CatalogueRow.derived`. The wording
#: names the cells it came from, so a reader of a derived number can go back
#: to the ones that were read, and
#: :meth:`~phonometry.io.CatalogueRow.from_printed` adds the basis of each
#: when they are not all one.
_FROM_E_NU = "from the Young's modulus and the Poisson ratio"
_FROM_N_NU = "from the shear modulus and the Poisson ratio"


@dataclass(frozen=True, kw_only=True)
class PorousMaterial(CatalogueRow):
    """One row of a published table of porous-material parameters.

    Every quantity is optional, because no two tables print the same columns:
    a chapter on the Biot theory prints a shear modulus and no characteristic
    length, a chapter on the transfer matrix prints both lengths and a Young's
    modulus, and the one anisotropic table prints two flow resistivities and
    no elastic constant the isotropic models can take. A field is ``None``
    when the page had nothing to put there, and
    :meth:`~phonometry.io.CatalogueRow.why_missing` says what
    it had instead.

    The name, the citation, the variant and the hedges a cell can carry
    instead of a number are the ones every catalogue row has.

    :ivar flow_resistivity_pa_s_m2: Airflow resistivity ``sigma``, in Pa s/m2.
        The books print it as N s/m4, N m-4 s or rayl/m, which are three
        spellings of the same unit.
    :ivar porosity: Open porosity ``phi``.
    :ivar tortuosity: Tortuosity ``alpha_inf``.
    :ivar viscous_length_um: Viscous characteristic length ``Lambda``, in
        micrometres, the unit the tables print it in. The ``viscous_length``
        parameter of
        :func:`~phonometry.materials.absorbers.johnson_champoux_allard` is in
        **metres**, so this field is not passed to it directly:
        :meth:`medium` makes the conversion, once, and a caller who assembles
        the argument list by hand divides by a million first.
    :ivar thermal_length_um: Thermal characteristic length ``Lambda'``, in
        micrometres. Metres at the model's ``thermal_length``, as above.
    :ivar thermal_permeability_m2: Static thermal permeability ``q'_0``, in
        m2, which two of the tables print beside the thermal length.
    :ivar fibre_diameter_um: Fibre diameter ``d``, in micrometres, for the
        materials a table describes by the fibre rather than by the pore.
    :ivar fibre_diameter_distribution_parameter: The parameter of the Poisson
        distribution Mechel fits to a measured spread of fibre diameters,
        referred to a diameter class one micrometre wide. Dimensionless: the
        micrometre in the column heading belongs to the class width, which is
        stated in the file's ``about`` because the value means nothing
        without it.
    :ivar shot_content_percent: Shot content, per cent **by weight**, of
        particles above the diameter the table's own heading names.
    :ivar binder_content_percent: Organic binder content, per cent by weight.
    :ivar frame_density_kg_m3: Frame density ``rho_1``, in kg/m3, the mass of
        the skeleton per unit volume of material and not the density of the
        material the skeleton is made of.
    :ivar thickness_mm: Layer thickness ``h`` of the specimen as tabulated, in
        millimetres. It is the thickness of the layer the table describes and
        not a property of the material: the same material appears in other
        tables of the same book at other thicknesses.
    :ivar youngs_modulus_pa: In-vacuo Young's modulus ``E`` of the frame, in
        pascals.
    :ivar shear_modulus_pa: In-vacuo shear modulus ``N``, in pascals, **real**.
        A page that prints it complex, as ``N(1 + j eta)``, has printed this
        and :attr:`structural_loss_factor`.
    :ivar poisson_ratio: Frame Poisson ratio ``nu``.
    :ivar structural_loss_factor: Structural loss factor ``eta_s`` of the
        frame, the imaginary part of the complex modulus over its real part.
    """

    flow_resistivity_pa_s_m2: float | None = None
    porosity: float | None = None
    tortuosity: float | None = None
    viscous_length_um: float | None = None
    thermal_length_um: float | None = None
    thermal_permeability_m2: float | None = None
    fibre_diameter_um: float | None = None
    fibre_diameter_distribution_parameter: float | None = None
    shot_content_percent: float | None = None
    binder_content_percent: float | None = None
    frame_density_kg_m3: float | None = None
    thickness_mm: float | None = None
    youngs_modulus_pa: float | None = None
    shear_modulus_pa: float | None = None
    poisson_ratio: float | None = None
    structural_loss_factor: float | None = None

    def _complete(self, cells: Completion) -> None:
        """Fill the one elastic constant that follows from the other two.

        Every book prints the frame elasticity in the form its own chapter
        needs: the Biot chapters print a shear modulus because the Biot
        equations take one, and the transfer matrix chapters print a Young's
        modulus because a plate does. With a Poisson ratio beside it, either
        gives the other through ``E = 2 N (1 + nu)``, so a reader who needs
        the other one does not have to do it in their head. Nothing else is
        derived: the five parameters of the equivalent fluid are independent
        and a page that leaves one out has left it out.

        A field the row can already say something about is left alone, and
        so is everything when the Poisson ratio is one. A page that printed a
        modulus as an interval, or printed a word where the number would go,
        has not printed a number, and a scalar worked back out of the other
        two constants would sit beside that interval contradicting it: the
        field would say one number and the row would say the book gave none.

        :param cells: The row's cells as the completion fills them in.
        """
        nu = cells.get("poisson_ratio")
        if nu is None or cells.is_hedged("poisson_ratio"):
            return
        modulus = cells.get("youngs_modulus_pa")
        shear = cells.get("shear_modulus_pa")
        if shear is None and modulus is not None:
            cells.fill(
                "shear_modulus_pa",
                lambda: modulus / (2.0 * (1.0 + nu)),
                _FROM_E_NU,
                inputs=("youngs_modulus_pa", "poisson_ratio"),
            )
        elif modulus is None and shear is not None:
            cells.fill(
                "youngs_modulus_pa",
                lambda: 2.0 * shear * (1.0 + nu),
                _FROM_N_NU,
                inputs=("shear_modulus_pa", "poisson_ratio"),
            )

    def frame_constants(self) -> tuple[complex, float]:
        """The in-vacuo frame constants ``(N, nu)`` the source prints.

        The complex shear modulus and the Poisson ratio are what
        :func:`~phonometry.materials.biot_waves`,
        :func:`~phonometry.materials.frame_quarter_wave_resonance` and
        :class:`~phonometry.materials.PoroelasticLayer` take together, and a
        table that prints one prints the other, so they are asked for together
        and a specimen characterised as a rigid frame alone says so here
        rather than handing out a ``None`` that fails further down.

        The shear modulus comes back complex, ``N(1 + j eta_s)``, which is the
        form the page prints and the models take, rebuilt from the real
        modulus and the loss factor the row stores separately. A row whose
        page printed a Young's modulus instead has had its shear modulus
        derived through the Poisson ratio, and
        :attr:`~phonometry.io.CatalogueRow.derived` says so.

        The loss factor is asked for like the other two. A row whose page
        prints the moduli and no loss factor is refused rather than handed
        a frame with ``eta_s = 0``: a lossless frame is a claim about the
        material, and a cell the page left empty is not a zero. Every
        published row that prints both moduli prints the loss factor too.

        :return: ``(shear_modulus_pa, poisson_ratio)``, the first complex.
        :raises ValueError: when the source prints no elastic constants, or
            prints them without a structural loss factor, in which case the
            message says what the page had in that cell instead.
        """
        if self.shear_modulus_pa is None or self.poisson_ratio is None:
            msg = (
                f"{self.name!r} is published without frame elastic constants "
                f"({self.source}); the poroelastic models need a shear modulus "
                "and a Poisson ratio, so pass them explicitly."
            )
            raise ValueError(msg)
        loss = self.printed("structural_loss_factor", wanted_by="frame_constants")
        return complex(
            self.shear_modulus_pa, self.shear_modulus_pa * loss
        ), self.poisson_ratio

    def medium(
        self,
        frequency: ArrayLike,
        *,
        model: str = "johnson_champoux_allard",
        fluid: Fluid = PUBLISHED_AIR,
    ) -> PorousMediumResult:
        """The equivalent fluid of this specimen.

        The characteristic lengths are stored in the micrometres the tables
        print and converted, here and once, to the metres
        :func:`~phonometry.materials.absorbers.johnson_champoux_allard` takes.

        :param frequency: Frequency vector ``f``, in hertz.
        :param model: ``"johnson_champoux_allard"`` (Default),
            ``"delany_bazley"`` or ``"miki"``. The last two read the flow
            resistivity alone, so they describe a coarser specimen than the
            one the other four parameters pin.
        :param fluid: The medium, a :class:`~phonometry.fluids.Fluid`
            (Default: :data:`~phonometry.materials.absorbers.PUBLISHED_AIR`).
        :return: A
            :class:`~phonometry.materials.absorbers.PorousMediumResult`.
        :raises ValueError: for an unknown model name, or when the page does
            not print a parameter the model needs, in which case the message
            says what the page had there instead.
        """
        if model not in {"johnson_champoux_allard", "delany_bazley", "miki"}:
            msg = (
                f"'model' must be one of 'johnson_champoux_allard', "
                f"'delany_bazley' or 'miki'; got {model!r}."
            )
            raise ValueError(msg)
        sigma = self.printed("flow_resistivity_pa_s_m2", wanted_by=model)
        if model == "delany_bazley":
            return delany_bazley(frequency, sigma, fluid=fluid)
        if model == "miki":
            return miki(frequency, sigma, fluid=fluid)
        return johnson_champoux_allard(
            frequency,
            sigma,
            porosity=self.printed("porosity", wanted_by=model),
            tortuosity=self.printed("tortuosity", wanted_by=model),
            viscous_length=self.printed("viscous_length_um", wanted_by=model)
            / _MICROMETRES_PER_METRE,
            thermal_length=self.printed("thermal_length_um", wanted_by=model)
            / _MICROMETRES_PER_METRE,
            fluid=fluid,
        )


# ---------------------------------------------------------------------------
# Provenance
#
# Source and authorship. Allard, J. F., & Atalla, N. (2009). "Propagation of
# sound in porous media: Modelling sound absorbing materials" (2nd ed.),
# Wiley, ISBN 978-0-470-74661-5, listed in docs/reference/bibliography.md. The
# book is not redistributed with this library and no page of it is reproduced
# here.
#
# Contents. The porous rows of nineteen parameter tables spread over eight
# chapters. Each is the input to one worked example of the book, transcribed
# cell by cell from the rendered page and converted into the units this
# library computes in, so what is stored is neither the printed table nor a
# facsimile of it. Every table prints rows this catalogue does not hold: the
# plates, the septa and the impervious screens, which are not porous
# materials, and the transversally isotropic rigidity parameters, which the
# isotropic models here do not take. Each file's ``about`` says which of its
# page's rows are absent and why.
#
# Basis. The parameters are physical constants of a specimen, cited per table
# to the document, the table, the PDF page and the printed folio they were
# read on. No compilation is reproduced, whole or in substantial part. This
# repository's MIT licence covers the code, not the values, which remain the
# authors' to describe.
#
# Removal policy. Withdrawing a table costs no capability: every model in this
# package takes its parameters as explicit arguments and none of them defaults
# to a published specimen, which the test suite asserts. Requests go through
# the contact in SECURITY.md.
#
# Admission rule for a table that is not here yet:
#
# 1. A table enters whole or not at all, rows in the order the page prints
#    them, and every row carries the hedge its cell did.
# 2. A table enters only after its page has been read as a rendered image, and
#    its file carries the document, the table, the PDF page and the printed
#    folio, plus ``attributed_to`` wherever the book credits a number to
#    someone else.
# 3. Values are stored in library units. The printed unit is stated in the
#    file's ``about`` and every conversion is pinned by an assertion against
#    the printed digits, never left as a comment.
# 4. One key, one dimension, one spelling. A quantity that appears in two
#    dimensions gets two field names.
# 5. A number this library worked out is marked ``derived`` and never stored
#    as if it had been read.
# ---------------------------------------------------------------------------

#: The published tables this catalogue reads, in the order the book prints
#: them.
_TABLES = (
    "allard-2009-table-6-1",
    "allard-2009-table-7-1",
    "allard-2009-table-8-1",
    "allard-2009-table-9-1",
    "allard-2009-table-10-1",
    "allard-2009-table-11-2",
    "allard-2009-table-11-3",
    "allard-2009-table-11-4",
    "allard-2009-table-11-5",
    "allard-2009-table-11-6",
    "allard-2009-table-11-7",
    "allard-2009-table-11-8",
    "allard-2009-table-11-9",
    "allard-2009-table-12-1",
    "allard-2009-table-12-2",
    "allard-2009-table-12-4",
    "allard-2009-table-12-5",
    "allard-2009-table-13-1",
    "allard-2009-table-13-2",
    # The compiled tables: one quantity each, over classes of material rather
    # than over specimens, which is why almost every cell of them is a range.
    "cox-2017-table-6-2",
    "cox-2017-table-6-3",
    "cox-2017-table-6-5",
    "cox-2017-table-6-8",
    "cox-2017-table-6-9",
    "mechel-2008-section-g1-table-1",
    "mechel-2008-section-g11-table-1",
)


def _load() -> dict[str, PorousMaterial]:
    """Every row of every packaged table, keyed by table and row.

    The key names the table because a book prints the same foam in four
    chapters and the same glass wool in two, sometimes with a column the other
    page left out. A flat name would have to pick one of them silently.
    """
    rows: dict[str, PorousMaterial] = {}
    for table in _TABLES:
        source, records = read_table("phonometry.materials.absorbers", f"{table}.json")
        for record in records:
            rows[f"{table}/{record['key']}"] = PorousMaterial.from_printed(
                table=table, source=source, **take(record)
            )
    return rows


#: Every porous specimen this library has read from a published page, keyed
#: ``"<table>/<row>"``: ``"allard-2009-table-6-1/domisol_coffrage"`` is the
#: glass wool of the Biot worked example and
#: ``"allard-2009-table-11-8/glass_wool"`` is the same specimen as the
#: transfer matrix chapter prints it, with a Young's modulus in place of the
#: shear modulus and a thickness the other page does not give. One file per
#: published table in ``materials/absorbers/data/``, each citing its own page.
#: Use :func:`porous_materials_named` to gather every reading of one name.
PUBLISHED_POROUS: Mapping[str, PorousMaterial] = MappingProxyType(_load())


def porous_materials_named(name: str) -> tuple[PorousMaterial, ...]:
    """Every published row for a specimen name, across the tables.

    Comparing two printings of one specimen is the point of holding both, and
    it has to be a deliberate act: a lookup that returned one row for "Foam"
    would be choosing between published parameter sets on the caller's behalf,
    and one of these books prints five different foams under that name. Across
    the books it also puts a measured specimen beside the range its class is
    compiled in: "Mineral wool" answers with Allard's specimen and with the
    two ranges Cox compiles for it.

    :param name: The specimen name as a table prints it, matched without
        regard to case: ``"Foam"``, ``"foam"``.
    :return: The rows whose :attr:`PorousMaterial.name` matches, in the order
        the tables are read, which is empty when no page names it.
    """
    wanted = name.casefold()
    return tuple(
        row for row in PUBLISHED_POROUS.values() if row.name.casefold() == wanted
    )
