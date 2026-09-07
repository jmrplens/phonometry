#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Effects of vibration on structures (DIN 4150-3:1999-02).

A pile driver, a passing tram or a blast puts vibration into the ground, and
the question the neighbours ask is whether the building will crack. DIN 4150-3
answers it the way an engineering practice can afford to: not with a stress
calculation, but with **guideline values** (*Anhaltswerte*) for one measured
quantity, the peak particle velocity, drawn from a large body of measurements
on real buildings. Keep under them and damage of the kind the standard defines
has not been observed; exceed them and it does not follow that damage occurs,
only that the cheap check no longer settles the question and Clauses 4.2 to
4.4 have to be done properly.

**What is measured** (5.1). At the foundation, the largest of the three
components :math:`v_x`, :math:`v_y`, :math:`v_z` of the particle velocity, as
a peak, each treated on its own; the standard calls it
:math:`|v_i|_\mathrm{max}` and then writes it :math:`v_i`. In the topmost
floor plane, the larger of the two horizontal components, measured at the
outside wall, which is the building's horizontal answer to the foundation
excitation rather than a new excitation.

**Short-term vibration** (Clause 5) is vibration that does not occur often
enough for resonance to build up in the structure. Table 1 gives its
guideline values by building class, and at the foundation they depend on
frequency: a building tolerates a fast wiggle better than a slow one, so the
value rises from 1 Hz to 100 Hz. Between the printed frequencies the
guideline is read off Bild 1, which joins the corner values by straight lines
on a linear frequency axis; above 100 Hz the 100 Hz value may be used. In the
topmost floor plane one value covers all frequencies.

**Long-term vibration** (Clause 6, *Dauererschütterungen*) is the opposite
case: often enough for the structure to respond at its own frequencies. Table
3 drops to a single value per class in the topmost floor plane, roughly a
quarter of the short-term one, and prints no frequency dependence at all.

**Buried pipelines** (5.3) are judged on their own Table 2 by pipe material,
measured on the pipe, and long-term vibration halves those values (6.3).

Three sizing rules travel with the tables and are here because a reader who
has the tables needs them in the same breath:

* Ceilings and floors (5.2) are separately covered by a vertical
  :math:`v_z \leq 20` mm/s at the point of largest vibration, usually mid-span.
* Massive engineering structures such as reinforced-concrete abutments and
  block foundations may take twice the row 1 values of Table 1 (5.1).
* The lowest horizontal natural frequency of a building of five storeys or
  more is roughly :math:`f_i \approx 10/n` with :math:`n` the storey count
  (6.4), which is the estimate that tells you whether the topmost floor plane
  will be excited at all.

Clause 6.2 turns a measured velocity into a bending stress for a beam or a
one-way slab vibrating in one mode, which is the bridge from this guideline
check to the stress calculation of 4.2:

.. math::

   \hat{\sigma}_\mathrm{max} = 1{,}73
   \left(E_\mathrm{dyn} \, \varrho \,
   \frac{G_\mathrm{ges}}{G_\mathrm{balken}}\right)^{0,5}
   k_n \, \hat{v}_\mathrm{max} \tag{1}

The guideline values are not limits in the legal sense and not an acceptance
specification. They are where experience says the question stops being worth
asking.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from ..._internal.types import as_float_or_array
from ..._internal.validation import (
    require_choice,
    require_non_negative,
    require_positive,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

#: The three building classes of Table 1, in the order the rows are printed:
#: commercial and industrial buildings (row 1), dwellings and buildings of
#: like construction or use (row 2), and buildings that suit neither and are
#: worth preserving, such as listed ones (row 3).
BuildingClass = Literal["commercial", "residential", "sensitive"]

#: Where the velocity was measured: at the foundation, or in the topmost
#: floor plane (horizontal, at the outside wall).
MeasurementLocation = Literal["foundation", "top_floor"]

#: How often the vibration occurs, in the sense of Clauses 5 and 6.
VibrationDuration = Literal["short_term", "long_term"]

BUILDING_CLASSES: tuple[str, ...] = ("commercial", "residential", "sensitive")

#: The frequencies Table 1 prints its foundation guideline values at, in
#: hertz. They are the ends of the three bands of the table, so the value at
#: 10 Hz closes the first band and opens the second.
FOUNDATION_FREQUENCIES_HZ: tuple[float, ...] = (1.0, 10.0, 50.0, 100.0)

#: Table 1, foundation columns: the guideline peak velocity in millimetres
#: per second at each frequency of :data:`FOUNDATION_FREQUENCIES_HZ`. The
#: table prints a band as a range ("20 bis 40"), and Bild 1 shows what the
#: range means: a straight line from the value at the start of the band to
#: the value at its end, on a linear frequency axis.
SHORT_TERM_FOUNDATION_MM_S: dict[str, tuple[float, ...]] = {
    "commercial": (20.0, 20.0, 40.0, 50.0),
    "residential": (5.0, 5.0, 15.0, 20.0),
    "sensitive": (3.0, 3.0, 8.0, 10.0),
}

#: Table 1, last column: the guideline peak velocity in the topmost floor
#: plane, horizontal, at all frequencies, in millimetres per second.
SHORT_TERM_TOP_FLOOR_MM_S: dict[str, float] = {
    "commercial": 40.0,
    "residential": 15.0,
    "sensitive": 8.0,
}

#: Table 3: the long-term guideline peak velocity in the topmost floor plane,
#: horizontal, at all frequencies, in millimetres per second. Table 3 has no
#: foundation column, because a structure responding at its own frequencies
#: is judged where it responds.
LONG_TERM_TOP_FLOOR_MM_S: dict[str, float] = {
    "commercial": 10.0,
    "residential": 5.0,
    "sensitive": 2.5,
}

#: Clause 5.2: the vertical peak velocity below which short-term vibration is
#: not expected to reduce the serviceability of a ceiling or floor, in
#: millimetres per second, measured where the vibration is largest.
FLOOR_VERTICAL_MM_S: float = 20.0

#: Clause 5.1: massive engineering structures (reinforced-concrete abutments,
#: block foundations) may raise the row 1 values of Table 1 by up to this
#: factor, provided no danger arises from soil-mechanical effects. The clause
#: says "up to", so this is a ceiling on the allowance rather than a value the
#: structure is entitled to, and it is a sentence of Clause 5 naming Table 1,
#: so it does not reach the long-term values of Table 3.
MASSIVE_STRUCTURE_FACTOR: float = 2.0

#: The pipe materials of Table 2, in the order the rows are printed.
PipelineMaterial = Literal[
    "welded_steel", "concrete_or_flanged_metal", "masonry_or_plastic"
]

PIPELINE_MATERIALS: tuple[str, ...] = (
    "welded_steel",
    "concrete_or_flanged_metal",
    "masonry_or_plastic",
)

#: Table 2: the guideline peak velocity on a buried pipeline, in millimetres
#: per second, by pipe material. Row 2 covers vitrified clay, concrete,
#: reinforced and prestressed concrete, and metal with or without flanges.
PIPELINE_MM_S: dict[str, float] = {
    "welded_steel": 100.0,
    "concrete_or_flanged_metal": 80.0,
    "masonry_or_plastic": 50.0,
}

#: Clause 6.3: without further evidence, Table 2 may be used for long-term
#: vibration reduced by this factor.
PIPELINE_LONG_TERM_FACTOR: float = 0.5

#: Clause 6.2: the constant of Formula (1), which is the slenderness ratio
#: ``y_max / i`` of a full rectangular section.
BENDING_STRESS_CONSTANT: float = 1.73

#: Clause 6.4: the numerator of the storey estimate ``f_i ~ 10 / n``, in
#: hertz. It applies to buildings from about five storeys up.
STOREY_FREQUENCY_NUMERATOR_HZ: float = 10.0

#: Clause 6.4: the storey count from which the estimate is offered.
STOREY_FREQUENCY_MIN_STOREYS: int = 5


def guideline_velocity(
    building_class: BuildingClass | str,
    frequency: ArrayLike | None = None,
    *,
    location: MeasurementLocation | str = "foundation",
    duration: VibrationDuration | str = "short_term",
    massive_structure: bool = False,
) -> np.ndarray | float:
    r"""The guideline peak velocity of Table 1 or Table 3, in mm/s.

    At the foundation for short-term vibration the guideline is a function of
    frequency, read off Bild 1: constant below 10 Hz, then two straight
    segments joining the corner values of Table 1 on a linear frequency axis,
    and constant again above 100 Hz, since 5.1 allows the 100 Hz value to be
    used for anything faster. Everywhere else Table 1 and Table 3 print one
    number for all frequencies, and *frequency* is then not needed.

    :param building_class: One of :data:`BUILDING_CLASSES`.
    :param frequency: Frequency of the dominant component, in hertz (scalar
        or array). Required for the short-term foundation case and ignored
        otherwise.
    :param location: ``"foundation"`` (default) or ``"top_floor"``.
    :param duration: ``"short_term"`` (Table 1, default) or ``"long_term"``
        (Table 3).
    :param massive_structure: Raise the row 1 values by
        :data:`MASSIVE_STRUCTURE_FACTOR`, which is the most 5.1 allows a
        massive engineering structure. The allowance is written for row 1 of
        Table 1 alone, so it applies to the commercial class and to short-term
        vibration, and is refused anywhere else.
    :return: The guideline peak velocity, in millimetres per second; a float
        unless *frequency* was an array.
    :raises ValueError: If a name is not one of its choices, if the
        short-term foundation case is asked for without a frequency, if a
        frequency is not positive and finite, or if *massive_structure* is
        asked for outside row 1 of Table 1.
    """
    cls = require_choice(str(building_class), "building_class", BUILDING_CLASSES)
    where = require_choice(str(location), "location", ("foundation", "top_floor"))
    when = require_choice(str(duration), "duration", ("short_term", "long_term"))
    factor = 1.0
    if massive_structure:
        if cls != "commercial":
            msg = (
                "'massive_structure' applies to the commercial row of Table 1; "
                f"got building_class={cls!r}."
            )
            raise ValueError(msg)
        if when != "short_term":
            # The allowance is a sentence of Clause 5, which is short-term
            # vibration, and it names Table 1. Table 3 belongs to Clause 6 and
            # the standard says nothing about raising it.
            msg = (
                "'massive_structure' is the Clause 5.1 allowance on Table 1; "
                "Table 3 carries no such allowance, so it cannot be applied "
                "with duration='long_term'."
            )
            raise ValueError(msg)
        factor = MASSIVE_STRUCTURE_FACTOR
    if when == "long_term":
        if where != "top_floor":
            msg = (
                "Table 3 gives long-term guideline values in the topmost floor "
                "plane only; got location='foundation'."
            )
            raise ValueError(msg)
        return LONG_TERM_TOP_FLOOR_MM_S[cls]
    if where == "top_floor":
        return factor * SHORT_TERM_TOP_FLOOR_MM_S[cls]
    if frequency is None:
        msg = (
            "The short-term foundation guideline of Table 1 depends on "
            "frequency; 'frequency' is required."
        )
        raise ValueError(msg)
    f = np.asarray(frequency, dtype=np.float64)
    if np.any(f <= 0.0) or not np.all(np.isfinite(f)):
        msg = "'frequency' must be positive and finite."
        raise ValueError(msg)
    values = np.interp(
        f,
        FOUNDATION_FREQUENCIES_HZ,
        SHORT_TERM_FOUNDATION_MM_S[cls],
    )
    return as_float_or_array(factor * values)


def pipeline_guideline_velocity(
    material: PipelineMaterial | str,
    *,
    duration: VibrationDuration | str = "short_term",
) -> float:
    """The guideline peak velocity on a buried pipeline (Table 2), in mm/s.

    Measured on the pipe itself; a substitute measurement at the ground
    surface above it only estimates the value (5.3, D.1). Long-term vibration
    halves the table, which is what 6.3 allows without further evidence.

    :param material: One of :data:`PIPELINE_MATERIALS`.
    :param duration: ``"short_term"`` (default) or ``"long_term"``.
    :return: The guideline peak velocity, in millimetres per second.
    :raises ValueError: If a name is not one of its choices.
    """
    pipe = require_choice(str(material), "material", PIPELINE_MATERIALS)
    when = require_choice(str(duration), "duration", ("short_term", "long_term"))
    value = PIPELINE_MM_S[pipe]
    return value * PIPELINE_LONG_TERM_FACTOR if when == "long_term" else value


@dataclass(frozen=True)
class DamageAssessment:
    """One measured velocity against the guideline value it is judged by.

    :ivar velocity_mm_s: The measured peak velocity, in millimetres per
        second: the largest of the three components at the foundation, or the
        larger of the two horizontal components in the topmost floor plane.
    :ivar guideline_mm_s: The guideline value it is compared with.
    :ivar building_class: The row of Table 1 or Table 3 that was used.
    :ivar location: Where the velocity was measured.
    :ivar duration: Which clause the guideline came from.
    :ivar frequency_hz: The frequency the guideline was read at, or ``None``
        where the guideline does not depend on frequency.
    """

    velocity_mm_s: float
    guideline_mm_s: float
    building_class: str
    location: str
    duration: str
    frequency_hz: float | None

    @property
    def ratio(self) -> float:
        """The measured velocity as a fraction of the guideline value."""
        return float(self.velocity_mm_s / self.guideline_mm_s)

    @property
    def within_guideline(self) -> bool:
        """Whether the measured velocity keeps to the guideline value.

        True is the whole of what the standard promises: damage of the kind
        4.5 defines has not, in the experience the tables are drawn from, been
        observed. False is not the converse, and 5.1 says so: exceeding a
        guideline value does not mean damage occurs, it means the question
        has to be answered by 4.2 to 4.4 instead.
        """
        return bool(self.velocity_mm_s <= self.guideline_mm_s)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw Bild 1 with this measurement on it.

        The three foundation curves of Table 1 against frequency, and the
        measured velocity as a point, so the margin is read rather than
        computed.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_damage_assessment`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_damage_assessment

        check_language(language)
        return plot_damage_assessment(self, ax=ax, language=language, **kwargs)


def assess_building_vibration(
    velocity_mm_s: float,
    *,
    building_class: BuildingClass | str,
    frequency_hz: float | None = None,
    location: MeasurementLocation | str = "foundation",
    duration: VibrationDuration | str = "short_term",
    massive_structure: bool = False,
) -> DamageAssessment:
    """Compare one measured peak velocity with its guideline value.

    :param velocity_mm_s: The measured peak velocity, in millimetres per
        second; see :class:`DamageAssessment` for which component it is. Zero
        is accepted and keeps to every guideline value.
    :param building_class: One of :data:`BUILDING_CLASSES`.
    :param frequency_hz: Frequency of the dominant component, in hertz.
        Required for the short-term foundation case.
    :param location: ``"foundation"`` (default) or ``"top_floor"``.
    :param duration: ``"short_term"`` (default) or ``"long_term"``.
    :param massive_structure: See :func:`guideline_velocity`.
    :return: The comparison, as a :class:`DamageAssessment`.
    :raises ValueError: If the velocity is negative or not finite, or for any
        reason :func:`guideline_velocity` raises.
    """
    # Non-negative rather than positive: a foundation that did not move is a
    # measurement like any other, and it keeps to every guideline value there
    # is. Refusing it would refuse the easiest case the standard covers.
    v = require_non_negative(velocity_mm_s, "velocity_mm_s")
    guideline = guideline_velocity(
        building_class,
        frequency_hz,
        location=location,
        duration=duration,
        massive_structure=massive_structure,
    )
    return DamageAssessment(
        velocity_mm_s=v,
        guideline_mm_s=float(guideline),
        building_class=str(building_class),
        location=str(location),
        duration=str(duration),
        frequency_hz=None if frequency_hz is None else float(frequency_hz),
    )


def storey_fundamental_frequency(storeys: int) -> float:
    """The rough lowest horizontal natural frequency of a building (6.4).

    ``f_i ~ 10 / n``, offered for buildings from about five storeys up. It is
    a rough estimate and the standard says so; its use is to tell whether the
    excitation is anywhere near the frequency at which the topmost floor
    plane will answer.

    :param storeys: The number of storeys ``n``.
    :return: The estimated lowest horizontal natural frequency, in hertz.
    :raises ValueError: If the storey count is not a positive integer.
    """
    # ValueError rather than TypeError, so every argument this module refuses
    # raises the same class.
    if isinstance(storeys, bool) or not isinstance(storeys, (int, np.integer)):
        msg = "'storeys' must be an integer."
        raise ValueError(msg)  # noqa: TRY004
    n = int(storeys)
    if n < 1:
        msg = f"'storeys' must be at least 1; got {n}."
        raise ValueError(msg)
    return STOREY_FREQUENCY_NUMERATOR_HZ / n


def bending_stress(
    peak_velocity_m_s: ArrayLike,
    *,
    dynamic_modulus_pa: float,
    density_kg_m3: float,
    load_ratio: float = 1.0,
    mode_factor: float = 1.0,
) -> np.ndarray | float:
    r"""Peak bending stress from a peak velocity, Formula (1) of 6.2.

    For a beam or a one-way slab of full rectangular section, constant
    stiffness and uniform mass, vibrating in one mode, the peak bending
    stress follows from the peak velocity alone:

    .. math::

       \hat{\sigma}_\mathrm{max} = 1{,}73
       \left(E_\mathrm{dyn} \, \varrho \,
       \frac{G_\mathrm{ges}}{G_\mathrm{balken}}\right)^{0,5}
       k_n \, \hat{v}_\mathrm{max}

    The system dimensions do not enter, which is the point of the formula: a
    velocity measured where the amplitude is largest is enough. The mode
    factor :math:`k_n` lies between 1 and 1,3 in the technically important
    cases, so it moves the answer by less than a third.

    :param peak_velocity_m_s: Peak velocity over the beam length, in metres
        per second (scalar or array). Note the unit: the guideline tables are
        in millimetres per second and this formula is not.
    :param dynamic_modulus_pa: Dynamic modulus of elasticity
        :math:`E_\mathrm{dyn}`, in pascals.
    :param density_kg_m3: Material density :math:`\varrho`, in kilograms per
        cubic metre.
    :param load_ratio: The load coefficient
        :math:`G_\mathrm{ges}/G_\mathrm{balken}`, the beam's own weight plus
        any uniformly distributed load it carries over its own weight. 1 for
        a beam carrying nothing else.
    :param mode_factor: The mode coefficient :math:`k_n`, dimensionless.
    :return: The peak bending stress, in pascals; a float unless the velocity
        was an array.
    :raises ValueError: If a material property, the load ratio or the mode
        factor is not positive and finite, or a velocity is negative.
    """
    e_dyn = require_positive(dynamic_modulus_pa, "dynamic_modulus_pa")
    rho = require_positive(density_kg_m3, "density_kg_m3")
    ratio = require_positive(load_ratio, "load_ratio")
    k_n = require_positive(mode_factor, "mode_factor")
    v = np.asarray(peak_velocity_m_s, dtype=np.float64)
    if np.any(v < 0.0) or not np.all(np.isfinite(v)):
        msg = "'peak_velocity_m_s' must be non-negative and finite."
        raise ValueError(msg)
    sigma = BENDING_STRESS_CONSTANT * math.sqrt(e_dyn * rho * ratio) * k_n * v
    return as_float_or_array(sigma)


def foundation_guideline_curve(
    building_class: BuildingClass | str,
    frequency: ArrayLike | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Bild 1 as two arrays: frequency and guideline velocity.

    The corner points of Table 1 by default, which is the polyline Bild 1
    draws; pass *frequency* to sample the same polyline elsewhere.

    :param building_class: One of :data:`BUILDING_CLASSES`.
    :param frequency: Frequencies to sample at, in hertz, or ``None`` for the
        four corners of Table 1.
    :return: ``(frequency_hz, guideline_mm_s)``.
    :raises ValueError: If the class is not one of the three, or a frequency
        is not positive and finite.
    """
    cls = require_choice(str(building_class), "building_class", BUILDING_CLASSES)
    if frequency is None:
        f = np.asarray(FOUNDATION_FREQUENCIES_HZ, dtype=np.float64)
    else:
        f = np.atleast_1d(np.asarray(frequency, dtype=np.float64))
    values = np.atleast_1d(
        np.asarray(guideline_velocity(cls, f, location="foundation"), dtype=np.float64)
    )
    return f, values
