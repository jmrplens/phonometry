#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Dynamic stiffness of resilient materials under floating floors (EN 29052-1:1992).

A floating floor is a heavy floating slab resting on a resilient layer; the
combination is a mass-spring system whose natural frequency governs the impact
and airborne improvement of the floor. EN 29052-1 (identical to ISO 9052-1:1989)
measures the **dynamic stiffness per unit area** ``s'`` of the resilient layer
from the resonance of a standard load plate on a 200 mm x 200 mm specimen.

The dynamic stiffness per unit area is the ratio of a dynamic force per area to
the resulting change in thickness (Formula 1):

.. math::

   s' = \frac{F/S}{\Delta d} \qquad [\text{N/m}^3]

The resiliently supported floor is a mass-spring resonator; its natural
frequency (Formula 2) and, in the laboratory arrangement, the measured resonant
frequency (Formula 3) are:

.. math::

   f_0 = \frac{1}{2\pi} \sqrt{\frac{s'}{m'}}
   \qquad \text{(installed floor)}

   f_\mathrm{r} = \frac{1}{2\pi} \sqrt{\frac{s'_\mathrm{t}}{m'_\mathrm{t}}}
   \qquad \text{(test arrangement)}

so the *apparent* dynamic stiffness follows from the resonance (Formula 4):

.. math::

   s'_\mathrm{t} = 4 \pi^2 m'_\mathrm{t} f_\mathrm{r}^2

With an air-permeable resilient material the enclosed gas adds a parallel
stiffness (Formula 7), from the isothermal compression of the pore air:

.. math::

   s'_\mathrm{a} = \frac{p_0}{d\,\epsilon}

(:math:`s'_\mathrm{a} = 111/d` MN/m3 for :math:`p_0 = 0.1` MPa,
:math:`\epsilon = 0.9` and ``d`` in mm, the standard's worked NOTE). The
dynamic stiffness of the installed material is then obtained by airflow
resistivity ``r`` (clause 8.2):

.. math::

   s' = s'_\mathrm{t}, \qquad
   r \ge 100~\text{kPa}\cdot\text{s/m}^2 \tag{Formula 5}

   s' = s'_\mathrm{t} + s'_\mathrm{a}, \qquad
   10 \le r < 100~\text{kPa}\cdot\text{s/m}^2 \tag{Formula 6}

For :math:`r < 10` kPa.s/m2, ``s'a`` follows Formula 7; the method only
applies when :math:`s'_\mathrm{t} \gg s'_\mathrm{a}`, otherwise ``s'`` cannot be resolved.

This module is the resilient-layer characterisation feeding the floating-floor
term of the EN 12354-2 impact model
(:mod:`phonometry.building.prediction.simplified_model`). It does **not** feed
ISO 16251-1 (:mod:`phonometry.building.measurement.floor_covering_improvement`), whose
scope is limited to soft, locally-reacting floor coverings; floating floors
are explicitly excluded there.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

    from ..._report.metadata import ReportMetadata


from ..._internal.catalogue import CatalogueError, CatalogueRow, read_table, take
from ..._internal.types import as_float_or_array
from ..._internal.validation import check_engine, require_non_negative, require_positive
from ..._internal.warnings import PhonometryWarning

# ---------------------------------------------------------------------------
# Constants.
# ---------------------------------------------------------------------------

#: Atmospheric pressure ``p0`` used by EN 29052-1 for the enclosed-gas term
#: (clause 8.2 NOTE: ``p0 = 0,1 MPa``), in pascals. The standard rounds one
#: atmosphere to 0,1 MPa; pass the true 101 325 Pa explicitly if preferred.
STANDARD_ATMOSPHERIC_PRESSURE = 1.0e5

#: Airflow-resistivity thresholds of clause 8.2, in kPa.s/m2.
_HIGH_RESISTIVITY = 100.0
_LOW_RESISTIVITY = 10.0

#: ``2*pi`` and ``4*pi**2`` for the resonance relations.
_TWO_PI = 2.0 * np.pi
_FOUR_PI_SQ = 4.0 * np.pi**2

#: Pascal seconds per square metre in one kilopascal second per square metre.
#: A catalogue row holds a flow resistivity in the first and clause 8.2 states
#: its thresholds in the second; dividing by it moves a resistivity across
#: without moving it across either threshold (see
#: :meth:`ResilientLayer.natural_frequency`).
_PA_PER_KPA = 1000.0


class DynamicStiffnessWarning(PhonometryWarning):
    """Advisory when the enclosed-gas term makes ``s'`` unresolvable (clause 8.2)."""


# ---------------------------------------------------------------------------
# Resonance relations (clauses 3, 8.1).
# ---------------------------------------------------------------------------


def apparent_dynamic_stiffness(
    resonant_frequency_hz: ArrayLike, total_mass_per_area_kg_m2: float
) -> np.ndarray | float:
    r"""Apparent dynamic stiffness per unit area ``s't`` (Formula 4).

    Inverts the test resonance :math:`f_\mathrm{r} = (1/2\pi)\sqrt{s'_\mathrm{t}/m'_\mathrm{t}}` to
    :math:`s'_\mathrm{t} = 4 \pi^2 m'_\mathrm{t} f_\mathrm{r}^2`.

    :param resonant_frequency_hz: Extrapolated resonant frequency ``fr``, in
        hertz (scalar or array).
    :param total_mass_per_area_kg_m2: Total mass per unit area used during the
        test ``m't``, in kg/m2 (the load plate plus fittings over the 0,04 m2
        specimen; the standard's plate gives
        :math:`m'_\mathrm{t} = 8~\text{kg} / 0.04~\text{m}^2 = 200` kg/m2).
    :return: The apparent dynamic stiffness per unit area ``s't``, in N/m3
        (numerically MN/m3 when divided by 1e6).
    """
    total_mass_per_area_kg_m2 = require_positive(
        total_mass_per_area_kg_m2, "total_mass_per_area_kg_m2"
    )
    fr = np.asarray(resonant_frequency_hz, dtype=np.float64)
    if np.any(fr <= 0.0):
        msg = "'resonant_frequency_hz' must be positive."
        raise ValueError(msg)
    return as_float_or_array(_FOUR_PI_SQ * total_mass_per_area_kg_m2 * fr**2)


def enclosed_gas_stiffness(
    thickness_m: ArrayLike,
    porosity: float,
    *,
    atmospheric_pressure_pa: float = STANDARD_ATMOSPHERIC_PRESSURE,
) -> np.ndarray | float:
    r"""Enclosed-gas dynamic stiffness per unit area ``s'a`` (Formula 7).

    The isothermal compression of the pore air adds a stiffness in parallel
    with the material's structure: :math:`s'_\mathrm{a} = p_0 / (d\,\epsilon)`.

    :param thickness_m: Thickness ``d`` of the specimen under the static load,
        in metres (scalar or array).
    :param porosity: Porosity ``epsilon`` of the specimen (0-1).
    :param atmospheric_pressure_pa: Atmospheric pressure ``p0``, in pascals
        (default :data:`STANDARD_ATMOSPHERIC_PRESSURE`, the standard's 0,1 MPa).
    :return: The enclosed-gas dynamic stiffness per unit area ``s'a``, in N/m3.

    .. note::
        With the standard's :math:`p_0 = 0.1` MPa and :math:`\epsilon = 0.9`
        this reduces to :math:`s'_\mathrm{a} = 111/d` MN/m3 for ``d`` in millimetres
        (clause 8.2 NOTE).
    """
    atmospheric_pressure_pa = require_positive(
        atmospheric_pressure_pa, "atmospheric_pressure_pa"
    )
    if not 0.0 < porosity <= 1.0:
        msg = "'porosity' must be in the range (0, 1]."
        raise ValueError(msg)
    d = np.asarray(thickness_m, dtype=np.float64)
    if np.any(d <= 0.0):
        msg = "'thickness_m' must be positive."
        raise ValueError(msg)
    return as_float_or_array(atmospheric_pressure_pa / (d * porosity))


def installed_dynamic_stiffness(
    apparent_stiffness_n_m3: float,
    *,
    airflow_resistivity_kpa_s_m2: float,
    gas_stiffness_n_m3: float | None = None,
) -> float:
    r"""Dynamic stiffness per unit area ``s'`` of the installed material (clause 8.2).

    Combines the apparent stiffness with the enclosed-gas term according to the
    lateral airflow resistivity ``r``:

    * :math:`r \ge 100` kPa.s/m2 -> :math:`s' = s'_\mathrm{t}` (Formula 5);
    * :math:`10 \le r < 100` kPa.s/m2 -> :math:`s' = s'_\mathrm{t} + s'_\mathrm{a}`
      (Formula 6);
    * :math:`r < 10` kPa.s/m2 -> the standard only requires the qualitative
      criterion :math:`s'_\mathrm{t} \gg s'_\mathrm{a}` (clause 8.2). This implementation
      applies its own engineering threshold: ``s'a`` below 10 % of ``s't`` is treated as
      negligible and :math:`s' = s'_\mathrm{t}` (a :class:`DynamicStiffnessWarning` is
      emitted; clause 8.2 requires the error caused by disregarding ``s'a`` to
      be stated in the test report); above it the result is ``nan``, as the
      method cannot resolve ``s'``.

    The airflow resistivity is in kilopascal seconds per square metre, the
    unit clause 8.2 states its thresholds in, and it is asked for by name
    because the flow resistivities this library holds elsewhere
    (:attr:`~phonometry.materials.PorousMaterial.flow_resistivity_pa_s_m2`) are
    in pascal seconds per square metre, a thousand times smaller a unit.

    :param apparent_stiffness_n_m3: Apparent dynamic stiffness ``s't``, in
        N/m3.
    :param airflow_resistivity_kpa_s_m2: Lateral airflow resistivity ``r``, in
        kPa.s/m2 (ISO 9053).
    :param gas_stiffness_n_m3: Enclosed-gas dynamic stiffness ``s'a``, in N/m3
        (see :func:`enclosed_gas_stiffness`). Required below 100 kPa.s/m2,
        where Formula 6 adds it and case c) weighs it against ``s't``; above,
        Formula 5 does not use it.
    :return: The installed dynamic stiffness per unit area ``s'``, in N/m3
        (``nan`` when the method cannot resolve it).
    :raises ValueError: for a non-positive ``s't`` or ``r``, a negative
        ``s'a``, or no ``s'a`` below 100 kPa.s/m2, where an absent gas term
        is not a zero one.
    """
    apparent_stiffness_n_m3 = require_positive(
        apparent_stiffness_n_m3, "apparent_stiffness_n_m3"
    )
    # Written so that a NaN fails it too: an infinite resistivity is the
    # non-porous limit and is allowed, a NaN is no resistivity at all.
    if not airflow_resistivity_kpa_s_m2 > 0.0:
        msg = "'airflow_resistivity_kpa_s_m2' must be positive."
        raise ValueError(msg)
    if gas_stiffness_n_m3 is not None:
        gas_stiffness_n_m3 = require_non_negative(
            gas_stiffness_n_m3, "gas_stiffness_n_m3"
        )
    if airflow_resistivity_kpa_s_m2 >= _HIGH_RESISTIVITY:
        return apparent_stiffness_n_m3
    if gas_stiffness_n_m3 is None:
        msg = (
            "'gas_stiffness_n_m3' is required below 100 kPa.s/m2: clause 8.2 "
            "adds the enclosed-gas stiffness s'a to s't between 10 and 100 "
            "kPa.s/m2 and weighs it against s't below 10; pass the s'a of "
            "Formula 7, from enclosed_gas_stiffness()."
        )
        raise ValueError(msg)
    if airflow_resistivity_kpa_s_m2 >= _LOW_RESISTIVITY:
        return apparent_stiffness_n_m3 + gas_stiffness_n_m3
    # r < 10 kPa.s/m2: the enclosed gas is only negligible for a firm structure.
    if gas_stiffness_n_m3 > 0.1 * apparent_stiffness_n_m3:
        warnings.warn(
            "for airflow resistivity below 10 kPa.s/m2 with a non-negligible "
            "enclosed-gas stiffness, EN 29052-1 cannot resolve s' (clause 8.2); "
            "returning nan.",
            DynamicStiffnessWarning,
            stacklevel=2,
        )
        return float("nan")
    warnings.warn(
        "airflow resistivity below 10 kPa.s/m2: s' is taken as s't with the "
        "enclosed-gas term disregarded; EN 29052-1 requires the reason and "
        "the estimated error caused by disregarding s'a to be stated in the "
        "test report (clause 8.2).",
        DynamicStiffnessWarning,
        stacklevel=2,
    )
    return apparent_stiffness_n_m3


def natural_frequency(
    dynamic_stiffness_n_m3: ArrayLike, mass_per_area_kg_m2: float
) -> np.ndarray | float:
    r"""Natural frequency ``f0`` of the resiliently supported floor (Formula 2).

    :math:`f_0 = (1/2\pi)\sqrt{s'/m'}`.

    :param dynamic_stiffness_n_m3: Dynamic stiffness per unit area ``s'`` of
        the installed layer, in N/m3 (scalar or array). The apparent ``s't``
        of a test specimen is not it; :func:`installed_dynamic_stiffness`
        turns one into the other.
    :param mass_per_area_kg_m2: Mass per unit area of the supported floor
        ``m'``, in kg/m2.
    :return: The natural frequency ``f0``, in hertz.
    """
    mass_per_area_kg_m2 = require_positive(mass_per_area_kg_m2, "mass_per_area_kg_m2")
    s = np.asarray(dynamic_stiffness_n_m3, dtype=np.float64)
    if np.any(s <= 0.0):
        msg = "'dynamic_stiffness_n_m3' must be positive."
        raise ValueError(msg)
    return as_float_or_array(np.sqrt(s / mass_per_area_kg_m2) / _TWO_PI)


# ---------------------------------------------------------------------------
# Published resilient layers
#
# Source and authorship. Hopkins, C. (2007). "Sound insulation",
# Butterworth-Heinemann, ISBN 978-0-7506-6526-1, listed in
# docs/reference/bibliography.md. The book is not redistributed with this
# library and no page of it is reproduced here.
#
# Contents. One table, Table A3, of the four the book's appendix prints. Its
# three data columns are transcribed row by row into
# materials/resilient/data/hopkins-2007-table-a3.json, and the stiffness is
# held in the N/m3 the functions above take rather than the printed MN/m3, so
# what is stored is the argument list rather than the printed table.
#
# Holdings from this one source, counted so the statement below is about what
# is actually here: Table A3 entire (fifteen rows, three columns) here;
# Table A4 entire (four rows, two columns) in
# building/prediction/masonry_cavity_wall.py, where it has shipped since before
# this table existed; and Table A2 as an oracle of the coincidence frequency,
# in tests/reference_data/building.py, which is test data and ships in no
# wheel. Three of the four tables of one appendix, two of them whole.
#
# Basis. Each row is a measured property of a named specimen, cited to the
# document, table, PDF page and printed folio it was read on, and credited in
# `attributed_to` wherever the book credits it to someone else. Two of the
# three tables above are short enough that taking the columns a function needs
# takes the table, and that is stated rather than stepped around: what is taken
# is a list of measured facts, in this library's units and keyed by this
# library's spelling, and no prose, figure, derivation or arrangement of the
# appendix comes with it. This repository's MIT licence covers the code, not
# the values, which remain the author's to describe.
#
# Removal policy. Withdrawing this table costs no capability: every function
# here takes `s'` as an explicit argument and none of them defaults to a
# published layer, which the test suite asserts. Requests go through the
# contact in SECURITY.md.
#
# Admission rule for a row that is not here yet:
#
# 1. A row enters only when a published function consumes it. No caller, no
#    row: that is the brake that stops this growing into the material database
#    this library does not ship.
# 2. A row enters only after its page has been read as a rendered image, and it
#    carries document, table, PDF page and printed folio, plus `attributed_to`
#    wherever the book credits the number to someone else.
# 3. Values are stored in library units. The printed unit is stated in the
#    data file's `about` and the conversion is pinned by an assertion against
#    `tests/reference_data`, never left as a comment.
# 4. A row whose table already ships anywhere in the tree does not ship twice;
#    where it overlaps, it is tied to the existing constant by an explicit
#    consistency assertion.
# 5. One key, one dimension, one spelling. A quantity that appears in two
#    dimensions gets two field names: the stiffness per unit area here is N/m3
#    and the per-tie stiffness of Table A4 is N/m, and they are two names. The
#    installed s' and the apparent s't of EN 29052-1 share a dimension and are
#    two quantities, so they are two names as well.
# 6. The copyright decision is reopened by how much of one source is here,
#    not by how many of its tables are touched: when the rows from a single
#    source stop being the arguments a published function takes and start
#    being a collection worth consulting for its own sake, the next form is a
#    data directory with its own provenance statement, and that is a different
#    piece of work. Hopkins is at three tables and the answer above is the
#    reopened decision, not the original one.
# ---------------------------------------------------------------------------

#: What :meth:`ResilientLayer.natural_frequency` is, in a refusal.
_FORMULA_2 = "the natural frequency of EN 29052-1 Formula 2"


@dataclass(frozen=True, kw_only=True)
class ResilientLayer(CatalogueRow):
    """A resilient layer under a floating floor, as its source prints it.

    A row of a catalogue like every other (:class:`~phonometry.io.CatalogueRow`):
    every quantity is optional, because a source prints some columns and not
    others, and a cell that holds something other than a number, such as the
    bound ``s' <= 9 MN/m3`` a product declaration prints, is held by the row's
    hedges rather than turned into one.

    EN 29052-1 names two stiffnesses per unit area, and they are two fields
    here. The test measures the apparent stiffness ``s't`` of a specimen whose
    pore air escapes at its sides (Formula 4); clause 8.2 turns it into the
    stiffness ``s'`` of the installed layer, whose pore air cannot, by way of
    the lateral airflow resistivity ``r`` and the enclosed-gas stiffness
    ``s'a``. Formula 2 takes ``s'``. A source that prints ``s'`` fills
    :attr:`dynamic_stiffness_n_m3`, which is what Hopkins Table A3 does. A test
    report gives ``s't`` and ``s'a``, and ``s'`` only "if possible" (clause
    9 e)); one that leaves ``s'`` out, like a sheet that gives ``s't`` alone,
    fills :attr:`apparent_dynamic_stiffness_n_m3`, and :meth:`natural_frequency`
    then needs ``r``, and below 100 kPa.s/m2 the report's ``s'a``, to go on.

    :ivar dynamic_stiffness_n_m3: ``s'``, the dynamic stiffness per unit area
        of the installed layer (clause 8.2), in N/m3.
    :ivar apparent_dynamic_stiffness_n_m3: ``s't``, the apparent dynamic
        stiffness per unit area of the test specimen (Formula 4), in N/m3. Not
        ``s'``: for an air-permeable layer the two differ by the enclosed-gas
        term ``s'a``, which "often forms a significant percentage of ``s'``"
        (Hopkins 2007, printed p. 360).
    :ivar density_kg_m3: Specimen density, in kg/m3.
    :ivar thickness_mm: Nominal uncompressed thickness, in millimetres.
    """

    dynamic_stiffness_n_m3: float | None = None
    apparent_dynamic_stiffness_n_m3: float | None = None
    density_kg_m3: float | None = None
    thickness_mm: float | None = None

    def natural_frequency(
        self,
        mass_per_area_kg_m2: float,
        *,
        airflow_resistivity_pa_s_m2: float | None = None,
        gas_stiffness_n_m3: float | None = None,
    ) -> float:
        r"""``f0`` of a floor of this mass per unit area on this layer.

        :math:`f_0 = (1/2\pi)\sqrt{s'/m'}` (Formula 2), through the module's
        :func:`natural_frequency`.

        A row that gives ``s'`` is used as it is, and the two keywords are
        refused, because nothing would read them. A row that gives only the
        apparent ``s't`` goes through :func:`installed_dynamic_stiffness`
        first, which is clause 8.2: ``s' = s't`` at or above 100 kPa.s/m2,
        ``s' = s't + s'a`` from 10 up to 100, and below 10 ``s' = s't`` only
        while ``s'a`` is negligible (``nan``, with a
        :class:`DynamicStiffnessWarning`, when it is not).

        The resistivity is taken in pascal seconds per square metre, the unit
        every flow resistivity of this library's catalogues is held in, and
        divided by a thousand for the kilopascal thresholds of clause 8.2.
        The division is correctly rounded and never decreases as its input
        grows, so it carries no resistivity across either threshold: exactly
        100 000 or 10 000 Pa.s/m2 lands on 100 or 10, and the largest float
        below either lands below it. The formula chosen is always the one the
        resistivity passed picks.

        :param mass_per_area_kg_m2: Mass per unit area of the supported floor
            ``m'``, in kg/m2.
        :param airflow_resistivity_pa_s_m2: Lateral airflow resistivity ``r``
            of the layer (ISO 9053), in Pa.s/m2, for a row that gives only
            ``s't``.
        :param gas_stiffness_n_m3: Enclosed-gas stiffness ``s'a`` of the layer
            (Formula 7, :func:`enclosed_gas_stiffness`), in N/m3, for a row
            that gives only ``s't`` and a resistivity below 100 kPa.s/m2.
        :return: The natural frequency ``f0``, in hertz.
        :raises CatalogueError: for a row that gives only ``s't`` when no
            resistivity is passed, saying that ``s't`` is not ``s'`` and what
            to pass; and for a row with no value of either stiffness whose
            ``s't`` cell holds something else, such as a declared bound, which
            it names.
        :raises ValueError: for a row that gives neither stiffness, naming
            what its source had in the ``s'`` cell; for a row that gives
            ``s'`` when either keyword is passed; for a resistivity below
            100 kPa.s/m2 with no ``s'a``; and for a non-positive mass or
            resistivity.
        """
        mass_per_area_kg_m2 = require_positive(
            mass_per_area_kg_m2, "mass_per_area_kg_m2"
        )
        apparent = self.apparent_dynamic_stiffness_n_m3
        if self.dynamic_stiffness_n_m3 is None and apparent is not None:
            stiffness = self._installed(
                apparent, airflow_resistivity_pa_s_m2, gas_stiffness_n_m3
            )
            if math.isnan(stiffness):
                return float("nan")
        else:
            if self.dynamic_stiffness_n_m3 is not None and (
                airflow_resistivity_pa_s_m2 is not None
                or gas_stiffness_n_m3 is not None
            ):
                msg = (
                    f"{self.name!r} gives the dynamic stiffness s' of the "
                    "installed layer, which Formula 2 takes as it is; "
                    "airflow_resistivity_pa_s_m2 and gas_stiffness_n_m3 are for "
                    "a row that gives only the apparent s't, and nothing would "
                    "read them here."
                )
                raise ValueError(msg)
            self._refuse_a_hedged_apparent_stiffness()
            stiffness = self.printed("dynamic_stiffness_n_m3", wanted_by=_FORMULA_2)
        return float(natural_frequency(stiffness, mass_per_area_kg_m2))

    def _refuse_a_hedged_apparent_stiffness(self) -> None:
        """Refuse a row whose only stiffness cell holds something but a value.

        A row with a value of neither stiffness is refused by
        :meth:`~phonometry.io.CatalogueRow.printed` for ``s'``, the quantity
        Formula 2 takes. When the page has nothing in the ``s'`` cell and
        something other than a number in the ``s't`` cell, such as the bound
        a product declaration prints, that refusal would say the page gives
        no stiffness at all; this one names the ``s't`` cell and what it
        holds instead, and says why no keyword turns it into ``s'``.

        :raises CatalogueError: for such a row.
        """
        installed = "dynamic_stiffness_n_m3"
        field_name = "apparent_dynamic_stiffness_n_m3"
        if self._holds_a_hedge(installed) or not self._holds_a_hedge(field_name):
            return
        msg = (
            f"{self.name!r} gives no value of the apparent dynamic stiffness "
            f"s't that {_FORMULA_2} would take through clause 8.2, "
            f"and no dynamic stiffness s' either: for {field_name}, "
            f"{self.why_missing(field_name)}. s't is not s', and what that cell "
            "holds is not a value of either, so no airflow_resistivity_pa_s_m2 "
            f"or gas_stiffness_n_m3 can turn it into s' ({self.source})."
        )
        raise CatalogueError(msg)

    def _holds_a_hedge(self, field_name: str) -> bool:
        """Whether the page has something other than a value in this cell."""
        return any(
            field_name in hedge
            for hedge in (
                self.ranges,
                self.reported,
                self.unquantified,
                self.not_derivable,
                self.misprinted,
            )
        )

    def _installed(
        self,
        apparent: float,
        airflow_resistivity_pa_s_m2: float | None,
        gas_stiffness_n_m3: float | None,
    ) -> float:
        """``s'`` from this row's ``s't`` by clause 8.2, or a refusal.

        :raises CatalogueError: when no resistivity is passed.
        :raises ValueError: for a non-positive resistivity, and from
            :func:`installed_dynamic_stiffness`.
        """
        if airflow_resistivity_pa_s_m2 is None:
            msg = (
                f"{self.name!r} gives the apparent dynamic stiffness s't of a "
                f"test specimen, {apparent / 1e6:g} MN/m3, and not the dynamic "
                "stiffness s' of the installed layer that "
                f"{_FORMULA_2} takes. EN 29052-1 clause 8.2 gives s' from s't by "
                "the lateral airflow resistivity r: pass "
                "airflow_resistivity_pa_s_m2 and, below 100 kPa.s/m2 "
                "(100000 Pa.s/m2), gas_stiffness_n_m3, the enclosed-gas "
                f"stiffness s'a of Formula 7 ({self.source})."
            )
            raise CatalogueError(msg)
        # Written so that a NaN fails it too.
        if not airflow_resistivity_pa_s_m2 > 0.0:
            msg = "'airflow_resistivity_pa_s_m2' must be positive."
            raise ValueError(msg)
        return installed_dynamic_stiffness(
            apparent,
            airflow_resistivity_kpa_s_m2=airflow_resistivity_pa_s_m2 / _PA_PER_KPA,
            gas_stiffness_n_m3=gas_stiffness_n_m3,
        )


#: The row fields the data files write as a list and the row holds as a set.
_SETS = ("approximate", "bounded_above", "bounded_below")

#: The published tables this catalogue reads.
_TABLES = ("hopkins-2007-table-a3",)


def _load() -> dict[str, ResilientLayer]:
    """Every row of every packaged table, keyed by table and row."""
    out: dict[str, ResilientLayer] = {}
    for table in _TABLES:
        citation, rows = read_table("phonometry.materials.resilient", f"{table}.json")
        for row in rows:
            out[f"{table}/{row['key']}"] = ResilientLayer(
                source=citation, table=table, **take(row, frozen=_SETS)
            )
    return out


#: The resilient layers this library has read from a page, keyed
#: ``"<table>/<row>"``: fifteen from Hopkins (2007) Table A3, PDF page 637
#: (printed p. 610), in ``materials/resilient/data/hopkins-2007-table-a3.json``,
#: whose caption states they were measured according to ISO 9052-1, the
#: standard this module implements as EN 29052-1. The column heading prints
#: ``s'``, which the book's List of symbols defines as the dynamic stiffness
#: per unit area of the installed material, so every row fills
#: :attr:`ResilientLayer.dynamic_stiffness_n_m3` and none fills the apparent
#: ``s't``. The book prints ``s'`` in MN/m3, the density in kg/m3 and the
#: thickness in mm; the stiffness is held in N/m3 and the other two as
#: printed, and the conversion is asserted against the printed digits in
#: tests/materials/resilient/test_dynamic_stiffness.py.
#:
#: Eleven rows are the author's own measurements; the four rebond-foam rows
#: the book credits to Hopkins and Hall (2006), which is what their
#: :attr:`~phonometry.io.CatalogueRow.attributed_to` carries for the whole row.
#: Four rock-wool rows and four glass-wool rows differ only by density and
#: thickness, which is why the row half of each key is
#: ``<material>_<density in kg/m3>_<thickness in mm>``: the printed table
#: separates them by position under a name it prints once, and a key has to
#: say which specimen it is.
#:
#: These are **measured specimens, not declared product values**. A floating
#: floor is designed with the manufacturer's ``s'`` declared to EN 29052-1;
#: these rows are the order of magnitude for when there is none, in the sense
#: :data:`~phonometry.noise_control.ROOM_ABSORPTION_ESTIMATES` is for when
#: nobody measured an absorption coefficient.
PUBLISHED_RESILIENT_LAYERS: Mapping[str, ResilientLayer] = MappingProxyType(_load())


def resilient_layer(layer: str | ResilientLayer) -> ResilientLayer:
    """Look up a published resilient layer, or pass one through.

    :param layer: A key of :data:`PUBLISHED_RESILIENT_LAYERS`, spelled
        ``"<table>/<row>"`` like every catalogue key, as
        ``"hopkins-2007-table-a3/mineral_wool_rock_60_30"``, or a
        :class:`ResilientLayer` already in hand, such as one built from a
        product's test report.
    :return: The :class:`ResilientLayer`.
    :raises ValueError: for an unknown layer name, listing the keys there are.
    """
    if isinstance(layer, ResilientLayer):
        return layer
    try:
        return PUBLISHED_RESILIENT_LAYERS[layer]
    except KeyError:
        options = ", ".join(sorted(PUBLISHED_RESILIENT_LAYERS))
        msg = f"Unknown resilient layer {layer!r}; choose one of {options}."
        raise ValueError(msg) from None


# ---------------------------------------------------------------------------
# Bundled measurement result.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DynamicStiffnessResult:
    """Dynamic stiffness of a resilient layer and the floating-floor resonance.

    :ivar apparent_stiffness: Apparent dynamic stiffness ``s't``, in N/m3.
    :ivar gas_stiffness: Enclosed-gas dynamic stiffness ``s'a``, in N/m3.
    :ivar dynamic_stiffness: Installed dynamic stiffness ``s'``, in N/m3.
    :ivar resonant_frequency: Measured test resonant frequency ``fr``, in hertz.
    :ivar floor_mass_per_area: Supported-floor mass per unit area ``m'``, kg/m2.
    :ivar natural_frequency: Installed-floor natural frequency ``f0``, in hertz.
    """

    apparent_stiffness: float
    gas_stiffness: float
    dynamic_stiffness: float
    resonant_frequency: float
    floor_mass_per_area: float
    natural_frequency: float

    def __post_init__(self) -> None:
        """Reject the quantities the method can never leave undetermined.

        The one producer, :func:`floating_floor_resonance`, computes the
        apparent stiffness from a positive resonance and load mass and pins
        the floor mass positive, so a non-finite (or non-positive) value in
        those fields is never the library's own output, and the fiche prints
        them unconditionally: a NaN ``apparent_stiffness`` becomes the BOXED
        headline ``s't = nan MN/m3`` and a NaN ``resonant_frequency`` prints
        ``fr = nan Hz``, both on a fully rendered accredited page.

        :attr:`dynamic_stiffness` and :attr:`natural_frequency` are left
        alone on purpose: EN 29052-1 clause 8.2 c) cannot resolve ``s'`` for
        an airy specimen below 10 kPa.s/m2, the producer then hands back NaN
        for both, and the fiche prints the em dash and omits ``f0`` for
        exactly that state. Refusing it here would refuse the library's own
        output.

        :raises ValueError: if a determined quantity is not positive and
            finite (the enclosed-gas term may be zero).
        """
        require_positive(self.apparent_stiffness, "apparent_stiffness")
        require_non_negative(self.gas_stiffness, "gas_stiffness")
        require_positive(self.resonant_frequency, "resonant_frequency")
        require_positive(self.floor_mass_per_area, "floor_mass_per_area")

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot ``f0(s')`` with this design point marked.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.materials import plot_dynamic_stiffness

        check_language(language)
        return plot_dynamic_stiffness(self, ax=ax, language=language, **kwargs)

    def report(
        self,
        path: str,
        *,
        metadata: ReportMetadata | None = None,
        engine: str = "reportlab",
        verbose: bool = False,
        language: str = "en",
    ) -> str:
        """Render an EN 29052-1 dynamic-stiffness test-report fiche to a PDF.

        Writes a one-page accredited dynamic-stiffness report (EN 29052-1:1992,
        identical to ISO 9052-1:1989): the standard-basis line, an optional
        metadata header block (client, specimen, the total mass per unit area
        ``m't`` used during the test, the loaded specimen thickness ``d``, test
        facility, date, climate ...), a two-panel body with a compact metrics
        table (the resonant frequency ``fr``, the apparent dynamic stiffness
        ``s't`` of Formula 4, the enclosed-gas term ``s'a`` of Formula 7 when it
        applies, the installed dynamic stiffness ``s'`` of Clause 8.2 and the
        supported-floor natural frequency ``f0`` of Formula 2) beside the
        ``f0(s')`` design curve, a boxed apparent dynamic stiffness ``s't`` with
        the installed ``s'`` and the resonance ``fr`` alongside, and a footer
        with the fixed disclaimer. EN 29052-1 is a characterisation, so there is
        no pass/fail verdict.

        Clause 9 requires every dynamic stiffness per unit area to be stated in
        meganewtons per cubic metre to the nearest meganewton per cubic metre,
        so the stiffness values are rounded to the nearest MN/m3; the
        frequencies are shown to 0,1 Hz.

        :param path: Destination path of the PDF file.
        :param metadata: Optional :class:`~phonometry.ReportMetadata`; ``None``
            produces a body-and-disclaimer fiche. The applicable descriptive
            fields are ``client``, ``manufacturer``, ``specimen``,
            ``mass_per_area`` (the total mass per unit area ``m't``),
            ``thickness`` (the loaded specimen thickness ``d``, in metres, shown
            in millimetres), ``test_room``,
            ``test_date``, ``temperature_c``, ``relative_humidity_percent``,
            ``measurement_standard``, ``laboratory``, ``operator``,
            ``report_id`` and ``notes``. The ``requirement`` field is ignored
            (EN 29052-1 has no verdict).
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: Accepted for a uniform ``.report()`` signature; the
            dynamic-stiffness fiche has a single body layout, so it has no
            effect.
        :param language: Fiche language: ``"en"`` (default, English, decimal
            point) or ``"es"`` (Spanish, decimal comma).
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` is not ``"reportlab"``.
        :raises ImportError: If reportlab or matplotlib is not installed. The
            fiche always embeds the ``f0(s')`` design curve, so both are
            required (``pip install "phonometry[report,plot]"``).
        """
        from ..._i18n import check_language

        check_language(language)
        check_engine(engine)
        from ..._report.iso9052 import render_dynamic_stiffness_report

        return render_dynamic_stiffness_report(
            self, path, metadata=metadata, verbose=verbose, language=language
        )


def floating_floor_resonance(
    resonant_frequency_hz: float,
    total_mass_per_area_kg_m2: float,
    floor_mass_per_area_kg_m2: float,
    *,
    airflow_resistivity_kpa_s_m2: float = float("inf"),
    thickness_m: float | None = None,
    porosity: float | None = None,
    atmospheric_pressure_pa: float = STANDARD_ATMOSPHERIC_PRESSURE,
) -> DynamicStiffnessResult:
    r"""Full EN 29052-1 chain: measured resonance -> installed ``s'`` and ``f0``.

    Chains the apparent dynamic stiffness (Formula 4), the enclosed-gas term
    (Formula 7, when ``thickness_m`` and ``porosity`` are given), the airflow
    resistivity combination (clause 8.2) and the installed-floor natural
    frequency (Formula 2).

    :param resonant_frequency_hz: Measured resonant frequency ``fr``, in hertz.
    :param total_mass_per_area_kg_m2: Test total mass per unit area ``m't``,
        in kg/m2.
    :param floor_mass_per_area_kg_m2: Supported-floor mass per unit area
        ``m'``, in kg/m2.
    :param airflow_resistivity_kpa_s_m2: Lateral airflow resistivity ``r``, in
        kPa.s/m2 (default ``inf`` -> the high-resistivity case
        :math:`s' = s'_\mathrm{t}`).
    :param thickness_m: Specimen thickness ``d`` under load, in metres.
        Required together with ``porosity`` for the enclosed-gas term, which
        applies when :math:`r < 100` kPa.s/m2. That condition is on the
        *value* of ``airflow_resistivity_kpa_s_m2`` rather than on a literal,
        so a signature cannot state it: it is checked here and raises.
    :param porosity: Specimen porosity ``epsilon``, required with
        ``thickness_m`` (see above).
    :param atmospheric_pressure_pa: Atmospheric pressure ``p0``, in pascals.
    :return: The :class:`DynamicStiffnessResult`.
    """
    s_apparent = float(
        apparent_dynamic_stiffness(resonant_frequency_hz, total_mass_per_area_kg_m2)
    )
    s_gas = 0.0
    if airflow_resistivity_kpa_s_m2 < _HIGH_RESISTIVITY:
        if thickness_m is None or porosity is None:
            msg = (
                "'thickness_m' and 'porosity' are required for the enclosed-gas "
                "term when airflow_resistivity_kpa_s_m2 < 100 kPa.s/m2."
            )
            raise ValueError(msg)
        s_gas = float(
            enclosed_gas_stiffness(
                thickness_m, porosity, atmospheric_pressure_pa=atmospheric_pressure_pa
            )
        )
    s_installed = installed_dynamic_stiffness(
        s_apparent,
        airflow_resistivity_kpa_s_m2=airflow_resistivity_kpa_s_m2,
        gas_stiffness_n_m3=s_gas,
    )
    f0 = (
        float(natural_frequency(s_installed, floor_mass_per_area_kg_m2))
        if np.isfinite(s_installed)
        else float("nan")
    )
    return DynamicStiffnessResult(
        apparent_stiffness=s_apparent,
        gas_stiffness=s_gas,
        dynamic_stiffness=s_installed,
        resonant_frequency=float(resonant_frequency_hz),
        floor_mass_per_area=float(floor_mass_per_area_kg_m2),
        natural_frequency=f0,
    )
