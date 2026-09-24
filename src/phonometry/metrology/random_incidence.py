#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Random-incidence and diffuse-field sensitivity of a sound level meter
(IEC 61183:1994).

A sound level meter is calibrated for sound arriving from one direction, its
reference direction, and most of the sound it is used on arrives from all of
them. IEC 61183 gives the two ways of finding what the instrument reads in
such a field. The free-field method of clause 4 and Annex A rotates the
instrument in an anechoic room, measures what it indicates for each direction
of incidence, and weights each reading by the solid angle it stands for; the
diffuse-field method of clause 5 and Annex B compares the instrument with a
reference instrument in a reverberation room.

**The free-field method.** The random-incidence sensitivity level is the
free-field sensitivity level for the reference direction less the directivity
of the instrument, Formulas (1) and (A.6):

.. math::

   G_\mathrm{RI} = G_\mathrm{F} - 10\lg\gamma,
   \qquad G_\mathrm{F} = L_\mathrm{rd} - L_\mathrm{o}

where :math:`L_\mathrm{rd}` is what the instrument indicates for a plane wave
from the reference direction and :math:`L_\mathrm{o}` the level of that wave
without the instrument. The directivity factor :math:`\gamma` of Formula (2)
is :math:`4\pi` over the integral, across the sphere, of what the instrument
indicates relative to :math:`L_\mathrm{rd}`; Formula (3) writes the direction
as the angle :math:`\phi` from the reference direction and the angle
:math:`\alpha` about it:

.. math::

   \gamma = \frac{4\pi}{\displaystyle\int_0^{2\pi}\!\!\int_0^{\pi}
   10^{-0{,}1[L_\mathrm{rd} - L(\phi,\alpha)]}\,
   |\sin\phi|\,\mathrm{d}\alpha\,\mathrm{d}\phi}

and in practice the sum of Formula (4) over ``m`` angles :math:`\phi_i` in
steps :math:`\Delta\phi = 2\pi/m` and ``n`` planes :math:`\alpha_j` in steps
:math:`\Delta\alpha = \pi/n`, each reading weighted by the share of the sphere
its element covers, Formula (5). Integrated, Formulas (6) and (7) give

.. math::

   K(\phi_i) = \left|\frac{\Delta\alpha}{4\pi}
   \left[\cos\left(\phi_i - \frac{\Delta\phi}{2}\right)
   - \cos\left(\phi_i + \frac{\Delta\phi}{2}\right)\right]\right|,
   \qquad
   K(0) = K(\pi) = \frac{2\Delta\alpha}{4\pi}
   \left[1 - \cos\frac{\Delta\phi}{2}\right]

:func:`adjustment_factors` evaluates them for any angular step that divides
the half circle and any number of planes. Two planes at right angles,
:math:`\Delta\alpha = \pi/2`, are Formulas (A.1) and (A.2) of Annex A, whose
factors for 10° steps Table A.1 prints; four planes at 45°, which NOTE 2 of
A.6 asks for when the reference direction is not normal to the diaphragm,
halve them.

The directivity factor then follows by one of three routes, each a function
here returning a :class:`DirectivityFactor`:

* :func:`directivity_factor`, two (or four) planes, Formula (A.3);
* :func:`axisymmetric_directivity_factor`, one plane for an instrument with
  rotational symmetry about its reference direction, Formula (A.4);
* :func:`equal_area_directivity_factor`, the 38 directions of equal-area
  elements of the note to A.1.8, Formula (A.5), at the directions
  :func:`equal_area_incidence_angles` gives.

:func:`random_incidence_sensitivity` applies Formula (1) band by band and
returns a :class:`RandomIncidenceSensitivity`.

**The diffuse-field method.** The instrument and a reference instrument are
placed in turn at the same positions in a diffuse field, and the difference of
what they indicate, Formula (8), is added to the diffuse-field sensitivity
level of the reference, known in one of three ways: Formula (9) for a
reference calibrated by clause 4, Formula (10) for one calibrated in a free
field with its directivity factor known, and Formula (11) for one calibrated
in a pressure field with the difference between its diffuse-field and
pressure sensitivity levels known. :func:`diffuse_field_sensitivity` takes
any of the three and returns a :class:`DiffuseFieldSensitivity`. Table B.1
prints both the directivity factor and that difference for a type LS2aP/LS2F
laboratory standard microphone, one of the two types Annex B
recommends for the reference (the other is LS2bP);
:data:`IEC61183_TABLE_B1` holds it and supplies them by default.

Two readings the text leaves to the implementer
-----------------------------------------------

**The two poles of Formula (A.3).** Both sums of (A.3) run from 0° to 350°,
and the paragraph under it notes that the readings at 0° and 180° are the same
in the two planes and "have only to be taken into account once". They have to
be *measured* once; they are *counted* in both sums. Each plane's pole factor
of Formula (A.2) covers half of the polar cap, so the 72 factors of Table A.1
sum to exactly one only with the poles in both sums, and an omnidirectional
instrument then has :math:`\gamma = 1`. Counted once, the factors sum to
0,998097: the sum of (A.3) loses the second plane's two pole terms, and
:math:`10\lg\gamma` comes out high by

.. math::

   -10\lg\left(1 - \gamma\,K(0)\left[10^{-0{,}1[L_\mathrm{rd} - L(0°)]}
   + 10^{-0{,}1[L_\mathrm{rd} - L(180°)]}\right]\right)

which is 0,008 dB (0,19 % on :math:`\gamma`) for an omnidirectional
instrument and grows with the directivity: about 0,02 dB at
:math:`10\lg\gamma = 7` dB when little arrives from behind. This module does
not make that error.

**The angles of the equal-area elements.** The note to A.1.8 prints the 38
directions to 0,1° without saying how they were placed. Each is the direction
that halves its element's area in polar angle: the cap about each pole takes
1/38 of the sphere, and the nine rings between them 4/38 each, split into
four elements by the two planes. That construction reproduces the note's
list of 20 angles to the 0,1° it is printed to, except two: 77,9° and its
mirror 282,1° break the list's own symmetry about 90° (77,9° + 102,2° is
180,1°, where all the other pairs sum to 180,0°), the construction gives 77,85°
and 282,15°, and the two are recorded in ``docs/ERRATA.md``.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.frozen import read_only
from .._internal.validation import (
    require_count,
    require_finite,
    require_finite_array,
    require_finite_matrix,
    require_positive_array,
)
from .._internal.warnings import PhonometryWarning

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "IEC61183_TABLE_B1",
    "DiffuseFieldSensitivity",
    "DirectivityFactor",
    "RandomIncidenceSensitivity",
    "ReferenceMicrophoneRow",
    "SphereDivisionWarning",
    "adjustment_factors",
    "axisymmetric_directivity_factor",
    "diffuse_field_sensitivity",
    "directivity_factor",
    "equal_area_directivity_factor",
    "equal_area_incidence_angles",
    "largest_element_fraction",
    "random_incidence_sensitivity",
]


class SphereDivisionWarning(PhonometryWarning):
    """The angular step divides the sphere into elements that are too large.

    Emitted when the largest element of the sphere a set of incidence angles
    divides it into is more than 3 % of its surface, the limit A.1.6 of
    IEC 61183:1994 sets for a reading to stand for the directions around it.
    """


#: A.1.6: "The largest element should be no more than 3 % of the total
#: surface area of the sphere."
_LARGEST_ELEMENT_LIMIT = 0.03

#: The planes Formulas (A.1) to (A.3) are written for: the X-Y and X-Z planes
#: of Figure A.1, :math:`\Delta\alpha = \pi/2`.
_ANNEX_A_PLANES = 2

#: The fewest steps a half circle can be divided into and still have an
#: interior direction between the two poles.
_MIN_HALF_CIRCLE_STEPS = 2

#: The note to A.1.8: "If the sphere is divided into 38 elements of equal
#: area".
_EQUAL_AREA_ELEMENTS = 38

#: The rings between the two polar caps in that division: 36 elements, four to
#: a ring, one in each quadrant the two planes cut.
_EQUAL_AREA_RINGS = 9

#: The elements the two planes cut each ring into.
_ELEMENTS_PER_RING = 4

#: Readings in the horizontal (X-Y) plane of the equal-area set: both poles and
#: two for each ring. The vertical (X-Z) plane takes the other 18.
_EQUAL_AREA_HORIZONTAL = 2 + 2 * _EQUAL_AREA_RINGS

#: How far a frequency may sit from a preferred frequency of Table B.1 and
#: still be read as it: an exact base-ten one-third-octave midband frequency
#: is within 1 % of its nominal value (16 000 Hz against 15 849 Hz), and
#: adjacent preferred frequencies are 25 % apart.
_NOMINAL_FREQUENCY_TOLERANCE = 0.02

#: How far a step may sit from dividing 180° exactly, relative, before it is
#: read as not dividing it: the step a caller computes as ``180 / 18``.
_STEP_TOLERANCE = 1e-9

#: The views :meth:`DirectivityFactor.plot` draws.
_DIRECTIVITY_VIEWS = ("response", "weights")

#: The views :meth:`RandomIncidenceSensitivity.plot` draws.
_SENSITIVITY_VIEWS = ("levels", "correction")

#: The routes of clause 5, named by how the reference instrument was
#: calibrated: Formulas (9), (10) and (11), in that order.
_ROUTES = ("random_incidence", "free_field", "pressure")

#: The formulas a :class:`DirectivityFactor` can come from: two or more planes,
#: one plane under rotational symmetry, and 38 equal-area elements.
_FORMULAS = ("A.3", "A.4", "A.5")


@dataclass(frozen=True)
class ReferenceMicrophoneRow:
    r"""One row of IEC 61183:1994 Table B.1.

    The characteristics of a type LS2aP/LS2F laboratory standard microphone
    (IEC 61094-1), one of the two types Annex B recommends for the
    reference of the diffuse-field method, at one preferred frequency. The
    table rounds both to 0,05 dB, determined with pure tones, with a
    measurement uncertainty of ±0,03 dB (B.5).

    :ivar directivity_index_db: :math:`10\lg\gamma` of the microphone, in dB:
        the directivity factor Formula (10) takes as :math:`\gamma_\mathrm{ref}`.
    :ivar diffuse_pressure_difference_db: :math:`\Delta_\mathrm{DP}`, its
        diffuse-field sensitivity level less its pressure sensitivity level, in
        dB, which Formula (11) adds to a pressure calibration.
    """

    directivity_index_db: float
    diffuse_pressure_difference_db: float


def _table_b1(
    rows: dict[float, tuple[float, float]],
) -> Mapping[float, ReferenceMicrophoneRow]:
    return MappingProxyType(
        {
            frequency: ReferenceMicrophoneRow(
                directivity_index_db=index, diffuse_pressure_difference_db=difference
            )
            for frequency, (index, difference) in rows.items()
        }
    )


#: The preferred one-third-octave frequencies from 25 Hz to 800 Hz, which
#: Table B.1 prints as one row, "25 to 800", at 0,00 dB in both columns.
_TABLE_B1_LOW_ROW_HZ = (
    25.0, 31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0,
    160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0,
)  # fmt: skip

#: IEC 61183:1994 Table B.1, "Characteristics of a type LS2aP/LS2F
#: microphone", keyed by preferred frequency in Hz: ``10 lg gamma`` and
#: ``Delta_DP``, both in dB. The row the table prints as "25 to 800" is given
#: here at each preferred frequency it covers. Read from BS EN 61183:1995,
#: which is IEC 1183:1994 unchanged.
IEC61183_TABLE_B1: Mapping[float, ReferenceMicrophoneRow] = _table_b1(
    {
        **dict.fromkeys(_TABLE_B1_LOW_ROW_HZ, (0.00, 0.00)),
        1000.0: (0.05, 0.00),
        1250.0: (0.10, 0.00),
        1600.0: (0.20, 0.05),
        2000.0: (0.20, 0.10),
        2500.0: (0.35, 0.10),
        3150.0: (0.65, 0.15),
        4000.0: (0.85, 0.25),
        5000.0: (1.25, 0.40),
        6300.0: (1.80, 0.65),
        8000.0: (2.45, 1.20),
        10000.0: (3.30, 1.90),
        12500.0: (4.30, 2.70),
        16000.0: (5.30, 3.05),
        20000.0: (6.70, 2.20),
    }
)


# ---------------------------------------------------------------------------
# Formulas (5) to (7), (A.1) and (A.2): the adjustment factors
# ---------------------------------------------------------------------------


def _half_circle_steps(step_deg: float) -> int:
    """How many steps of ``step_deg`` make the half circle from 0° to 180°.

    :raises ValueError: if the step is not finite and positive, does not divide
        180° into a whole number of steps, or is more than 90°.
    """
    step = require_finite(step_deg, "step_deg")
    msg = (
        "'step_deg' must divide 180° into a whole number of steps, at least "
        f"two, so that both poles and a direction between them are measured; "
        f"got {step_deg!r}."
    )
    if not step > 0.0:
        raise ValueError(msg)
    steps = 180.0 / step
    whole = round(steps)
    if whole < _MIN_HALF_CIRCLE_STEPS or not math.isclose(
        steps, whole, rel_tol=_STEP_TOLERANCE
    ):
        raise ValueError(msg)
    return int(whole)


def _weights(half_steps: int, planes: int) -> NDArray[np.float64]:
    r"""Formulas (6) and (7) for ``2 half_steps`` angles and ``planes`` planes.

    Written through the identities :math:`\cos(a - b) - \cos(a + b) = 2\sin a
    \sin b` and :math:`1 - \cos x = 2\sin^2(x/2)`, which are the printed
    differences without the cancellation of two nearly equal cosines at a
    fine step.
    """
    count = 2 * half_steps
    step = math.pi / half_steps
    delta_alpha = math.pi / planes
    # phi and 360° - phi lie on the same ring and take the same factor; the
    # angle is folded onto the half circle first so that they take it to the
    # last bit, rather than through two sines of different angles.
    index = np.arange(count)
    phi = np.minimum(index, count - index).astype(np.float64) * step
    weights = (
        delta_alpha / (4.0 * math.pi) * 2.0 * np.abs(np.sin(phi)) * math.sin(step / 2.0)
    )
    pole = 2.0 * delta_alpha / (4.0 * math.pi) * 2.0 * math.sin(step / 4.0) ** 2
    weights[0] = pole
    weights[half_steps] = pole
    return weights


def _largest_element(half_steps: int, planes: int) -> float:
    r"""The largest element of the division, as a fraction of the sphere.

    The two planes of Annex A cut every ring between the poles into four
    elements of :math:`K(\phi)` each and leave each polar cap whole, so the
    cap is the pole factor of every plane together. One plane under
    rotational symmetry stands for those same two, and is judged on their
    division.
    """
    ring = _weights(half_steps, max(planes, _ANNEX_A_PLANES))
    cap = math.sin(math.pi / half_steps / 4.0) ** 2
    return max(float(np.max(ring[1:half_steps])), cap)


def _warn_if_coarse(largest: float, stacklevel: int) -> None:
    if largest > _LARGEST_ELEMENT_LIMIT:
        warnings.warn(
            f"The largest element of the sphere is {100.0 * largest:.2f} % of "
            "its surface, above the 3 % IEC 61183 A.1.6 sets for one reading to "
            "stand for the directions around it; measure at a finer angular step.",
            SphereDivisionWarning,
            stacklevel=stacklevel,
        )


def adjustment_factors(step_deg: float, *, planes: int = 2) -> NDArray[np.float64]:
    r"""Adjustment factors :math:`K(\phi)` for one plane of measurements
    (IEC 61183:1994, Formulas (6), (7), (A.1) and (A.2)).

    The share of the sphere each reading stands for, at the angles
    :math:`\phi = 0, \Delta\phi, \ldots, 360° - \Delta\phi` from the
    reference direction, for measurements in ``planes`` planes through the
    reference direction at equal angles :math:`\Delta\alpha = 180°/n` apart:

    .. math::

       K(\phi) = \frac{\Delta\alpha}{4\pi}\, 2\,|\sin\phi|
       \sin\frac{\Delta\phi}{2},
       \qquad
       K(0) = K(180°) = \frac{2\Delta\alpha}{4\pi}
       \left[1 - \cos\frac{\Delta\phi}{2}\right]

    the first being Formula (6) with the difference of cosines written as a
    product. With the two planes of Annex A this is :math:`(1/8)[\cos(\phi -
    \Delta\phi/2) - \cos(\phi + \Delta\phi/2)]` and :math:`(1/4)[1 -
    \cos(\Delta\phi/2)]`, Formulas (A.1) and (A.2), which Table A.1 prints
    for 10° steps; with the four planes of NOTE 2 of A.6 every factor is
    halved, and with one plane, the rotationally symmetric instrument of
    Formula (A.4), doubled.

    The factors of all the planes together sum to one: the pole factor of each
    of the :math:`n` planes covers :math:`1/n` of the polar cap (half of it in
    the two planes of Annex A), so the pole readings enter every plane's sum
    (see the module notes).

    :param step_deg: The angular step :math:`\Delta\phi` in degrees. It has to
        divide 180° into a whole number of steps, at least two, so that both
        poles are measured.
    :param planes: The number of planes :math:`n` the measurements are made
        in (Default: 2, the X-Y and X-Z planes of Annex A).
    :return: The ``360 / step_deg`` factors, read-only, the first at 0°.
    :raises ValueError: for a step that does not divide 180°, or a number of
        planes that is not a whole number of at least one.
    :warns SphereDivisionWarning: when the largest element is more than 3 %
        of the sphere (A.1.6), which the 15° step, and every coarser one that
        divides 180°, gives in two planes.
    """
    half_steps = _half_circle_steps(step_deg)
    count = require_count(planes, "planes")
    _warn_if_coarse(_largest_element(half_steps, count), stacklevel=3)
    return read_only(_weights(half_steps, count))


def largest_element_fraction(step_deg: float, *, planes: int = 2) -> float:
    r"""The largest element a set of incidence angles divides the sphere into,
    as a fraction of its surface (IEC 61183:1994, A.1.6 and A.1.7).

    The planes cut each ring between the poles into :math:`2n` elements of
    :math:`K(\phi)` each, the largest at the direction nearest 90°, and leave
    the cap about each pole whole, :math:`\sin^2(\Delta\phi/4)` of the sphere.
    A.1.6 asks for the largest to be no more than 3 %; with the two planes of
    Annex A and 10° steps it is the element at 90°, 2,18 %, the
    "approximately 2,2 %" of A.1.7. One plane measured under rotational
    symmetry stands for the same two planes and is judged on their division.

    :param step_deg: The angular step :math:`\Delta\phi` in degrees, dividing
        180° into a whole number of steps, at least two.
    :param planes: The number of planes (Default: 2).
    :return: The fraction, between 0 and 1.
    :raises ValueError: as :func:`adjustment_factors`.
    """
    return _largest_element(
        _half_circle_steps(step_deg), require_count(planes, "planes")
    )


def equal_area_incidence_angles() -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    r"""The 38 directions of equal-area elements (IEC 61183:1994, note to
    A.1.8).

    The sphere is divided into 38 elements of equal area: a cap about each
    pole, and nine rings of four elements between them, cut by the horizontal
    (X-Y) and vertical (X-Z) planes. Each direction is the one that halves its
    element's area in polar angle, so the ``k``-th ring from the reference
    direction is at

    .. math::

       \phi_k = \arccos\left(1 - \frac{4k - 1}{19}\right),
       \qquad k = 1, \ldots, 9

    which is 32,6°, 50,8°, 65,1°, 77,8° and 90° up to grazing incidence. The
    note prints the same angles to 0,1°, except 77,9° and its mirror 282,1°,
    which are errata (see the module notes).

    :return: ``(horizontal, vertical)`` in degrees, read-only. The horizontal
        plane holds both poles and runs 0°, :math:`\phi_1, \ldots, \phi_9`,
        180°, :math:`360° - \phi_9, \ldots, 360° - \phi_1`: 20 directions in
        the order the note prints them. The vertical plane holds the same
        without the poles: 18.
    """
    k = np.arange(1, _EQUAL_AREA_RINGS + 1, dtype=np.float64)
    fraction = (_ELEMENTS_PER_RING * k - 1.0) / _EQUAL_AREA_ELEMENTS
    rings = np.degrees(np.arccos(1.0 - 2.0 * fraction))
    mirror = 360.0 - rings[::-1]
    horizontal = np.concatenate(([0.0], rings, [180.0], mirror))
    vertical = np.concatenate((rings, mirror))
    return read_only(horizontal), read_only(vertical)


# ---------------------------------------------------------------------------
# Formulas (A.3) to (A.5): the directivity factor
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DirectivityFactor:
    r"""The directivity factor of a sound level meter at one frequency
    (IEC 61183:1994, Formulas (A.3) to (A.5)).

    .. math::

       \gamma = \left(\sum K\, 10^{-0{,}1[L_\mathrm{rd} - L]}\right)^{-1}

    over every reading, each weighted by the share of the sphere it stands
    for. The readings are held flat, one entry per reading, with the plane
    each was taken in.

    :ivar incidence_angles_deg: :math:`\phi` of each reading from the
        reference direction, in degrees.
    :ivar plane_angles_deg: :math:`\alpha` of the plane of each reading, in
        degrees: 0 for the X-Y plane (``h`` in Annex A), 90 for the X-Z plane
        (``v``), and :math:`180°\,j/n` for plane :math:`j = 0, \ldots, n - 1`
        of ``n``.
    :ivar levels_db: :math:`L(\phi)`, the level the instrument indicates for
        each direction, in dB.
    :ivar weights: :math:`K` of each reading, dimensionless; they sum to one.
    :ivar reference_level_db: :math:`L_\mathrm{rd}`, in dB.
    :ivar gamma: :math:`\gamma`, dimensionless.
    :ivar largest_element_fraction: the largest element of the division, as a
        fraction of the sphere between 0 and 1 (A.1.6). For one plane under
        rotational symmetry it is the largest element of the two-plane
        division that plane stands for, each of whose readings weighs two
        elements.
    :ivar formula: the formula applied: ``"A.3"`` (planes), ``"A.4"``
        (one plane, rotational symmetry) or ``"A.5"`` (38 equal-area
        elements).
    """

    incidence_angles_deg: NDArray[np.float64]
    plane_angles_deg: NDArray[np.float64]
    levels_db: NDArray[np.float64]
    weights: NDArray[np.float64]
    reference_level_db: float
    gamma: float
    largest_element_fraction: float
    formula: str

    def __post_init__(self) -> None:
        r"""Refuse columns that disagree or a value out of its range, and
        publish the columns read-only.

        :raises ValueError: if the per-reading columns differ in length, a
            value is not finite, :math:`\gamma` is not positive, the largest
            element is not a fraction of the sphere, or the formula is not one
            of the three.
        """
        if self.formula not in _FORMULAS:
            msg = (
                f"DirectivityFactor: 'formula' must be one of {_FORMULAS}; "
                f"got {self.formula!r}."
            )
            raise ValueError(msg)
        columns = ("incidence_angles_deg", "plane_angles_deg", "levels_db", "weights")
        arrays = {
            name: np.array(getattr(self, name), dtype=np.float64) for name in columns
        }
        shapes = {name: array.shape for name, array in arrays.items()}
        if len(set(shapes.values())) != 1 or np.ndim(arrays["levels_db"]) != 1:
            msg = (
                "DirectivityFactor: 'incidence_angles_deg', 'plane_angles_deg', "
                "'levels_db' and 'weights' must be 1-D arrays of the same length; "
                f"got {shapes}."
            )
            raise ValueError(msg)
        for name, array in arrays.items():
            if not np.all(np.isfinite(array)):
                msg = f"DirectivityFactor: '{name}' must contain only finite values."
                raise ValueError(msg)
            object.__setattr__(self, name, read_only(array))
        require_finite(self.reference_level_db, "reference_level_db")
        if not (math.isfinite(self.gamma) and self.gamma > 0.0):
            msg = f"DirectivityFactor: 'gamma' must be positive and finite; got {self.gamma!r}."
            raise ValueError(msg)
        largest = self.largest_element_fraction
        if not (math.isfinite(largest) and 0.0 < largest <= 1.0):
            msg = (
                "DirectivityFactor: 'largest_element_fraction' must be a fraction "
                f"of the sphere, above 0 and at most 1; got {largest!r}."
            )
            raise ValueError(msg)

    @property
    def directivity_index_db(self) -> float:
        r""":math:`10\lg\gamma`, in dB: what Formula (1) subtracts from
        :math:`G_\mathrm{F}`, and what Table B.1 tabulates.
        """
        return 10.0 * math.log10(self.gamma)

    @property
    def relative_levels_db(self) -> NDArray[np.float64]:
        r""":math:`L(\phi) - L_\mathrm{rd}` of each reading, in dB."""
        return self.levels_db - self.reference_level_db

    def plot(
        self,
        ax: Axes | None = None,
        *,
        view: str = "response",
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        r"""Plot the directional response or the weight of each reading.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
            The ``"response"`` view needs a polar axes.
        :param view: ``"response"`` (default) draws :math:`L(\phi) -
            L_\mathrm{rd}` on a polar axes, one curve per plane, with
            :math:`10\lg\gamma` in the title; ``"weights"`` draws the factor
            :math:`K(\phi)` of each reading against its angle, in per cent of
            the sphere.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the curve of the first plane.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        :raises ValueError: if ``view`` is not one of the two names above, or
            ``ax`` is not polar for the response.
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_directivity_factor

        if view not in _DIRECTIVITY_VIEWS:
            msg = f"Unknown view {view!r}; use one of {_DIRECTIVITY_VIEWS}."
            raise ValueError(msg)
        return plot_directivity_factor(
            self, ax=ax, view=view, language=check_language(language), **kwargs
        )


def _reference_level(value: float | None, first_reading: float) -> float:
    r"""``L_rd``: the caller's, or the reading taken at 0° in the first plane.

    A.4.4 measures :math:`L_\mathrm{rd}` with the instrument aligned on the
    reference direction, before the rotation of A.4.5 starts from that same
    position, so without a separate reading it is the first one.
    """
    if value is None:
        return first_reading
    return require_finite(value, "reference_level_db")


def _gamma(
    levels: NDArray[np.float64], weights: NDArray[np.float64], lrd: float
) -> float:
    """Formulas (A.3) to (A.5): the reciprocal of the weighted energy sum."""
    return 1.0 / float(np.sum(weights * 10.0 ** (0.1 * (levels - lrd))))


def _plane_readings(
    levels: NDArray[np.float64], weights: NDArray[np.float64]
) -> tuple[NDArray[np.float64], ...]:
    """Unroll a ``(planes, m)`` grid of readings into flat columns.

    :return: The incidence angles, the plane angles, the levels and the
        weights of every reading, plane after plane.
    """
    planes, count = levels.shape
    step = 360.0 / count
    angles = np.tile(np.arange(count, dtype=np.float64) * step, planes)
    plane_angles = np.repeat(
        np.arange(planes, dtype=np.float64) * 180.0 / planes, count
    )
    grid = np.broadcast_to(weights, levels.shape).ravel()
    return angles, plane_angles, levels.ravel(), grid


def _from_planes(
    levels: NDArray[np.float64],
    reference_level_db: float | None,
    formula: str,
) -> DirectivityFactor:
    """Formula (A.3) or (A.4) on a ``(planes, m)`` grid of readings.

    One row is the rotationally symmetric instrument of Formula (A.4), whose
    factors are those of one plane; two or more rows are Formula (A.3).

    :warns SphereDivisionWarning: when the step leaves an element larger than
        3 % of the sphere (A.1.6).
    """
    planes = levels.shape[0]
    half_steps = _plane_count(levels.shape[1], "levels_db")
    largest = _largest_element(half_steps, planes)
    _warn_if_coarse(largest, stacklevel=4)
    angles, plane_angles, flat, weights = _plane_readings(
        levels, _weights(half_steps, planes)
    )
    lrd = _reference_level(reference_level_db, float(levels[0, 0]))
    return DirectivityFactor(
        incidence_angles_deg=angles,
        plane_angles_deg=plane_angles,
        levels_db=flat,
        weights=weights,
        reference_level_db=lrd,
        gamma=_gamma(flat, weights, lrd),
        largest_element_fraction=largest,
        formula=formula,
    )


def _plane_count(count: int, name: str) -> int:
    """The half-circle steps of ``count`` readings round the full circle.

    :raises ValueError: for an odd count, which misses the pole at 180°, or
        fewer than four readings.
    """
    if count % 2 or count < 2 * _MIN_HALF_CIRCLE_STEPS:
        msg = (
            f"'{name}' must hold an even number of readings round the full "
            "circle, at least four, at equal steps from the reference "
            f"direction, so that 0° and 180° are both among them; got {count}."
        )
        raise ValueError(msg)
    return count // 2


def directivity_factor(
    levels_db: ArrayLike, *, reference_level_db: float | None = None
) -> DirectivityFactor:
    r"""Directivity factor from readings in two or more planes
    (IEC 61183:1994, Formula (A.3)).

    .. math::

       \gamma = \left(\sum_{\phi = 0}^{350} K(\phi)\,
       10^{-0{,}1[L_\mathrm{rd} - L(\phi,\mathrm{h})]}
       + \sum_{\phi = 0}^{350} K(\phi)\,
       10^{-0{,}1[L_\mathrm{rd} - L(\phi,\mathrm{v})]}\right)^{-1}

    for the 10° steps and two planes of A.4.5 and A.4.6, with the factors of
    Table A.1. The angular step is read off the number of readings in a
    plane, and the factors are :func:`adjustment_factors` for that step and
    that number of planes: four planes, as NOTE 2 of A.6 asks for when the
    reference direction is not normal to the diaphragm, take half the factors
    of Table A.1.

    The readings at 0° and 180° are the same in every plane, and A.4.7 says
    they have only to be taken into account once. They are measured once and
    enter every plane's sum here, which is what makes the factors sum to one
    and an omnidirectional instrument read :math:`\gamma = 1`; counted once,
    :math:`10\lg\gamma` would come out 0,008 dB high for an omnidirectional
    instrument and more for a directional one (see the module notes).

    :param levels_db: :math:`L(\phi)` in dB, one row per plane (the first the
        X-Y plane, ``h``; the second the X-Z plane, ``v``), each at
        :math:`\phi = 0, \Delta\phi, \ldots, 360° - \Delta\phi` from the
        reference direction: shape ``(2, 36)`` for Annex A. An instrument
        measured in one plane under rotational symmetry goes to
        :func:`axisymmetric_directivity_factor`.
    :param reference_level_db: :math:`L_\mathrm{rd}` in dB (Default: None,
        the reading at 0° in the first plane, which A.4.4 takes in the same
        position).
    :return: The :class:`DirectivityFactor`.
    :raises ValueError: for fewer than two planes, an odd number of readings
        in a plane or fewer than four, or a value that is not finite.
    :warns SphereDivisionWarning: when the step leaves an element larger than
        3 % of the sphere (A.1.6).
    """
    levels = require_finite_matrix(levels_db, "levels_db")
    if levels.shape[0] < _ANNEX_A_PLANES:
        msg = (
            "'levels_db' must hold one row per plane, at least two; an "
            "instrument with rotational symmetry measured in one plane goes to "
            f"axisymmetric_directivity_factor. Got shape {levels.shape}."
        )
        raise ValueError(msg)
    return _from_planes(levels, reference_level_db, "A.3")


def axisymmetric_directivity_factor(
    levels_db: ArrayLike, *, reference_level_db: float | None = None
) -> DirectivityFactor:
    r"""Directivity factor of an instrument with rotational symmetry, from one
    plane (IEC 61183:1994, Formula (A.4)).

    .. math::

       \gamma = \left(2\sum_{\phi = 0}^{350} K(\phi)\,
       10^{-0{,}1[L_\mathrm{rd} - L(\phi,\mathrm{h})]}\right)^{-1}

    NOTE 1 of A.4.7: when the instrument is rotationally symmetric about its
    reference direction, the X-Z plane repeats the X-Y plane and one rotation
    (A.4.5) is enough. This is Formula (A.3) with the two planes equal, and
    the factor 2 makes the weights those of :func:`adjustment_factors` with
    one plane.

    :param levels_db: :math:`L(\phi,\mathrm{h})` in dB, one plane at
        :math:`\phi = 0, \Delta\phi, \ldots, 360° - \Delta\phi`: 36 readings
        for Annex A.
    :param reference_level_db: :math:`L_\mathrm{rd}` in dB (Default: None,
        the reading at 0°).
    :return: The :class:`DirectivityFactor`.
    :raises ValueError: for readings in more than one plane, an odd number of
        readings or fewer than four, or a value that is not finite.
    :warns SphereDivisionWarning: when the step leaves an element larger than
        3 % of the sphere in the two-plane division the one plane stands for.
    """
    levels = require_finite_matrix(levels_db, "levels_db")
    if levels.shape[0] != 1:
        msg = (
            "'levels_db' must be the readings of one plane; readings in several "
            f"planes go to directivity_factor. Got shape {levels.shape}."
        )
        raise ValueError(msg)
    return _from_planes(levels, reference_level_db, "A.4")


def equal_area_directivity_factor(
    horizontal_levels_db: ArrayLike,
    vertical_levels_db: ArrayLike,
    *,
    reference_level_db: float | None = None,
) -> DirectivityFactor:
    r"""Directivity factor from 38 equal-area elements (IEC 61183:1994,
    Formula (A.5)).

    .. math::

       \gamma = \left(\sum_{n = 1}^{38} \frac{1}{38}\,
       10^{-0{,}1[L_\mathrm{rd} - L(n)]}\right)^{-1}

    NOTE 2 of A.4.7: with the directions of the note to A.1.8, every element
    is 1/38 of the sphere (2,6 %) and every reading weighs the same.

    :param horizontal_levels_db: :math:`L(n)` in the horizontal (X-Y) plane,
        in dB, 20 readings at the directions of
        :func:`equal_area_incidence_angles`, in the order the note prints them
        (0°, 32,6°, ..., 180°, ..., 327,4°).
    :param vertical_levels_db: :math:`L(n)` in the vertical (X-Z) plane, in
        dB, 18 readings at the same directions without 0° and 180°.
    :param reference_level_db: :math:`L_\mathrm{rd}` in dB (Default: None,
        the horizontal reading at 0°).
    :return: The :class:`DirectivityFactor`.
    :raises ValueError: for readings not 20 and 18, or a value that is not
        finite.
    """
    horizontal = require_finite_array(horizontal_levels_db, "horizontal_levels_db")
    vertical = require_finite_array(vertical_levels_db, "vertical_levels_db")
    vertical_count = _EQUAL_AREA_ELEMENTS - _EQUAL_AREA_HORIZONTAL
    if horizontal.size != _EQUAL_AREA_HORIZONTAL or vertical.size != vertical_count:
        msg = (
            "'horizontal_levels_db' and 'vertical_levels_db' must hold the 20 "
            "and 18 readings of the 38 equal-area elements of IEC 61183; got "
            f"{horizontal.size} and {vertical.size}."
        )
        raise ValueError(msg)
    h_angles, v_angles = equal_area_incidence_angles()
    levels = np.concatenate((horizontal, vertical))
    weights = np.full(levels.size, 1.0 / _EQUAL_AREA_ELEMENTS)
    lrd = _reference_level(reference_level_db, float(horizontal[0]))
    return DirectivityFactor(
        incidence_angles_deg=np.concatenate((h_angles, v_angles)),
        plane_angles_deg=np.concatenate(
            (np.zeros(horizontal.size), np.full(vertical.size, 90.0))
        ),
        levels_db=levels,
        weights=weights,
        reference_level_db=lrd,
        gamma=_gamma(levels, weights, lrd),
        largest_element_fraction=1.0 / _EQUAL_AREA_ELEMENTS,
        formula="A.5",
    )


# ---------------------------------------------------------------------------
# Formulas (1) and (A.6): the random-incidence sensitivity level
# ---------------------------------------------------------------------------


def _band_column(
    values: ArrayLike, name: str, frequencies: NDArray[np.float64]
) -> NDArray[np.float64]:
    """A finite column of one value per band, a scalar spread over all of them.

    :raises ValueError: if it is neither a scalar nor one value per frequency.
    """
    column = require_finite_array(values, name)
    if column.size == 1:
        return np.full(frequencies.size, float(column[0]))
    if column.size != frequencies.size:
        msg = (
            f"'{name}' must hold one value per frequency ({frequencies.size}) or "
            f"a single value; got {column.size}."
        )
        raise ValueError(msg)
    return column


def _frequency_axis(frequencies_hz: ArrayLike) -> NDArray[np.float64]:
    """Positive, finite and strictly increasing frequencies.

    :raises ValueError: for anything else.
    """
    frequencies = require_positive_array(frequencies_hz, "frequencies_hz")
    if np.any(np.diff(frequencies) <= 0.0):
        msg = "'frequencies_hz' must be strictly increasing."
        raise ValueError(msg)
    return frequencies


@dataclass(frozen=True)
class RandomIncidenceSensitivity:
    r"""The random-incidence sensitivity level of a sound level meter, band by
    band (IEC 61183:1994, Formulas (1) and (A.6)).

    :math:`G_\mathrm{RI} = G_\mathrm{F} - 10\lg\gamma` at each frequency.

    :ivar frequencies_hz: the preferred frequencies, in Hz.
    :ivar free_field_level_db: :math:`G_\mathrm{F} = L_\mathrm{rd} -
        L_\mathrm{o}`, the free-field sensitivity level for the reference
        direction, in dB.
    :ivar directivity_index_db: :math:`10\lg\gamma`, in dB.
    :ivar random_incidence_level_db: :math:`G_\mathrm{RI}`, in dB.
    """

    frequencies_hz: NDArray[np.float64]
    free_field_level_db: NDArray[np.float64]
    directivity_index_db: NDArray[np.float64]
    random_incidence_level_db: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Refuse columns that disagree, and publish them read-only.

        :raises ValueError: if the columns differ in length, a value is not
            finite, or the frequencies are not positive and increasing.
        """
        columns = (
            "frequencies_hz",
            "free_field_level_db",
            "directivity_index_db",
            "random_incidence_level_db",
        )
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        for name in columns[1:]:
            column = require_finite_array(getattr(self, name), name)
            if column.size != frequencies.size:
                msg = (
                    f"RandomIncidenceSensitivity: '{name}' must hold one value per "
                    f"frequency ({frequencies.size}); got {column.size}."
                )
                raise ValueError(msg)
            object.__setattr__(self, name, read_only(column.copy()))

    @property
    def correction_db(self) -> NDArray[np.float64]:
        r""":math:`G_\mathrm{RI} - G_\mathrm{F} = -10\lg\gamma` at each
        frequency, in dB: what the instrument reads in a random-incidence
        field relative to a plane wave from its reference direction.
        """
        return self.random_incidence_level_db - self.free_field_level_db

    def plot(
        self,
        ax: Axes | None = None,
        *,
        view: str = "levels",
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        r"""Plot the sensitivity levels or the correction against frequency.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param view: ``"levels"`` (default) draws :math:`G_\mathrm{F}` and
            :math:`G_\mathrm{RI}`; ``"correction"`` draws :math:`G_\mathrm{RI}
            - G_\mathrm{F} = -10\lg\gamma`.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the first curve drawn.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        :raises ValueError: if ``view`` is not one of the two names above.
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_random_incidence_sensitivity

        if view not in _SENSITIVITY_VIEWS:
            msg = f"Unknown view {view!r}; use one of {_SENSITIVITY_VIEWS}."
            raise ValueError(msg)
        return plot_random_incidence_sensitivity(
            self, ax=ax, view=view, language=check_language(language), **kwargs
        )


def random_incidence_sensitivity(
    frequencies_hz: ArrayLike,
    free_field_level_db: ArrayLike,
    directivity_index_db: ArrayLike,
) -> RandomIncidenceSensitivity:
    r"""Random-incidence sensitivity level from the free-field sensitivity
    level and the directivity factor (IEC 61183:1994, Formulas (1) and (A.6)).

    .. math::

       G_\mathrm{RI} = G_\mathrm{F} - 10\lg\gamma

    at each frequency. :math:`G_\mathrm{F} = L_\mathrm{rd} - L_\mathrm{o}`
    depends on the individual instrument and :math:`\gamma` only on its
    dimensions and geometry, so one model's directivity factors serve every
    instrument of that model (4.2).

    :param frequencies_hz: The preferred frequencies, in Hz, increasing.
    :param free_field_level_db: :math:`G_\mathrm{F}` at each frequency, in dB
        (A.3).
    :param directivity_index_db: :math:`10\lg\gamma` at each frequency, in dB:
        :attr:`DirectivityFactor.directivity_index_db` of the readings at that
        frequency.
    :return: The :class:`RandomIncidenceSensitivity`.
    :raises ValueError: for columns of different lengths, a value that is not
        finite, or frequencies that are not positive and increasing.
    """
    frequencies = _frequency_axis(frequencies_hz)
    free_field = _band_column(free_field_level_db, "free_field_level_db", frequencies)
    index = _band_column(directivity_index_db, "directivity_index_db", frequencies)
    return RandomIncidenceSensitivity(
        frequencies_hz=frequencies,
        free_field_level_db=free_field,
        directivity_index_db=index,
        random_incidence_level_db=free_field - index,
    )


# ---------------------------------------------------------------------------
# Formulas (8) to (11): the diffuse-field sensitivity level
# ---------------------------------------------------------------------------


def _table_b1_column(
    frequencies: NDArray[np.float64], field: str, name: str
) -> NDArray[np.float64]:
    """One column of Table B.1 at the given frequencies.

    :raises ValueError: for a frequency that is not a preferred frequency of
        the table, from 25 Hz to 20 kHz.
    """
    keys = np.array(sorted(IEC61183_TABLE_B1), dtype=np.float64)
    values = np.empty(frequencies.size)
    for index, frequency in enumerate(frequencies):
        nearest = keys[np.argmin(np.abs(np.log(keys / frequency)))]
        if not math.isclose(frequency, nearest, rel_tol=_NOMINAL_FREQUENCY_TOLERANCE):
            msg = (
                f"{frequency:g} Hz is not a preferred frequency of IEC 61183 "
                "Table B.1, which prints the LS2aP/LS2F microphone from 25 Hz to "
                f"20 kHz; pass '{name}' for it."
            )
            raise ValueError(msg)
        values[index] = getattr(IEC61183_TABLE_B1[float(nearest)], field)
    return values


@dataclass(frozen=True)
class DiffuseFieldSensitivity:
    r"""The diffuse-field sensitivity level of a sound level meter, by
    comparison with a reference instrument (IEC 61183:1994, clause 5).

    .. math::

       \Delta G_\mathrm{D} = L_\mathrm{D} - L_\mathrm{D,ref},
       \qquad
       G_\mathrm{D} = \Delta G_\mathrm{D} + G_\mathrm{D,ref}

    where the diffuse-field sensitivity level of the reference,
    :math:`G_\mathrm{D,ref}`, is its calibrated sensitivity level plus a
    correction that depends on how it was calibrated: none for a
    random-incidence calibration, Formula (9); :math:`-10\lg\gamma_\mathrm{ref}`
    for a free-field calibration, Formula (10); :math:`+\Delta_\mathrm{DP}`
    for a pressure calibration, Formula (11).

    :ivar frequencies_hz: the band centres, in Hz.
    :ivar indicated_level_db: :math:`L_\mathrm{D}`, what the instrument under
        test indicates, in dB.
    :ivar reference_indicated_level_db: :math:`L_\mathrm{D,ref}`, what the
        reference instrument indicates at the same positions, in dB.
    :ivar reference_sensitivity_level_db: the reference's calibrated
        sensitivity level, in dB: :math:`G_\mathrm{RI,ref}`,
        :math:`G_\mathrm{F,ref}` or :math:`G_\mathrm{P,ref}`.
    :ivar reference_correction_db: what turns that into the reference's
        diffuse-field sensitivity level, in dB: 0, :math:`-10\lg
        \gamma_\mathrm{ref}` or :math:`\Delta_\mathrm{DP}`.
    :ivar route: ``"random_incidence"`` (Formula (9)), ``"free_field"``
        (Formula (10)) or ``"pressure"`` (Formula (11)).
    """

    frequencies_hz: NDArray[np.float64]
    indicated_level_db: NDArray[np.float64]
    reference_indicated_level_db: NDArray[np.float64]
    reference_sensitivity_level_db: NDArray[np.float64]
    reference_correction_db: NDArray[np.float64]
    route: str

    def __post_init__(self) -> None:
        """Refuse columns that disagree or an unknown route, and publish the
        columns read-only.

        :raises ValueError: if the columns differ in length, a value is not
            finite, the frequencies are not positive and increasing, or the
            route is not one of the three.
        """
        if self.route not in _ROUTES:
            msg = (
                f"DiffuseFieldSensitivity: 'route' must be one of {_ROUTES}; "
                f"got {self.route!r}."
            )
            raise ValueError(msg)
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        for name in (
            "indicated_level_db",
            "reference_indicated_level_db",
            "reference_sensitivity_level_db",
            "reference_correction_db",
        ):
            column = require_finite_array(getattr(self, name), name)
            if column.size != frequencies.size:
                msg = (
                    f"DiffuseFieldSensitivity: '{name}' must hold one value per "
                    f"frequency ({frequencies.size}); got {column.size}."
                )
                raise ValueError(msg)
            object.__setattr__(self, name, read_only(column.copy()))

    @property
    def level_difference_db(self) -> NDArray[np.float64]:
        r""":math:`\Delta G_\mathrm{D} = L_\mathrm{D} - L_\mathrm{D,ref}`, in dB
        (Formula (8)).
        """
        return self.indicated_level_db - self.reference_indicated_level_db

    @property
    def reference_diffuse_field_level_db(self) -> NDArray[np.float64]:
        r""":math:`G_\mathrm{D,ref}`, the diffuse-field sensitivity level of the
        reference instrument, in dB.
        """
        return self.reference_sensitivity_level_db + self.reference_correction_db

    @property
    def diffuse_field_level_db(self) -> NDArray[np.float64]:
        r""":math:`G_\mathrm{D}`, the diffuse-field sensitivity level of the
        instrument under test, in dB (Formulas (9) to (11)).
        """
        return self.level_difference_db + self.reference_diffuse_field_level_db

    def plot(
        self,
        ax: Axes | None = None,
        *,
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        r"""Plot :math:`G_\mathrm{D}`, :math:`\Delta G_\mathrm{D}` and
        :math:`G_\mathrm{D,ref}` against frequency.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the :math:`G_\mathrm{D}` curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_diffuse_field_sensitivity

        return plot_diffuse_field_sensitivity(
            self, ax=ax, language=check_language(language), **kwargs
        )


def diffuse_field_sensitivity(
    frequencies_hz: ArrayLike,
    indicated_level_db: ArrayLike,
    reference_indicated_level_db: ArrayLike,
    *,
    reference_random_incidence_level_db: ArrayLike | None = None,
    reference_free_field_level_db: ArrayLike | None = None,
    reference_directivity_index_db: ArrayLike | None = None,
    reference_pressure_level_db: ArrayLike | None = None,
    reference_diffuse_pressure_difference_db: ArrayLike | None = None,
) -> DiffuseFieldSensitivity:
    r"""Diffuse-field sensitivity level by comparison with a reference sound
    level meter (IEC 61183:1994, Formulas (8) to (11)).

    .. math::

       \Delta G_\mathrm{D} = L_\mathrm{D} - L_\mathrm{D,ref} \tag{8}

    and then, by the calibration the reference instrument has,

    .. math::

       G_\mathrm{D} = \Delta G_\mathrm{D} + G_\mathrm{RI,ref} \tag{9}

    .. math::

       G_\mathrm{D} = \Delta G_\mathrm{D} + G_\mathrm{F,ref}
       - 10\lg\gamma_\mathrm{ref} \tag{10}

    .. math::

       G_\mathrm{D} = \Delta G_\mathrm{D} + (G_\mathrm{P,ref}
       + \Delta_\mathrm{DP}) \tag{11}

    Exactly one of ``reference_random_incidence_level_db``,
    ``reference_free_field_level_db`` and ``reference_pressure_level_db``
    selects the formula. For Formulas (10) and (11), the directivity factor
    and the diffuse-to-pressure difference of the reference default to Table
    B.1, the type LS2aP/LS2F microphone, one of the two types Annex B
    recommends for the reference, at each preferred
    frequency from 25 Hz to 20 kHz.

    :param frequencies_hz: The band centres, in Hz, increasing.
    :param indicated_level_db: :math:`L_\mathrm{D}`, what the instrument under
        test indicates in the diffuse field, in dB, one per band.
    :param reference_indicated_level_db: :math:`L_\mathrm{D,ref}`, what the
        reference instrument indicates at the same positions, in dB.
    :param reference_random_incidence_level_db: :math:`G_\mathrm{RI,ref}` in
        dB, for a reference calibrated by clause 4 (Formula (9)).
    :param reference_free_field_level_db: :math:`G_\mathrm{F,ref}` in dB, for a
        reference calibrated in a free field (Formula (10)).
    :param reference_directivity_index_db: :math:`10\lg\gamma_\mathrm{ref}` in
        dB, with Formula (10) only (Default: None, Table B.1).
    :param reference_pressure_level_db: :math:`G_\mathrm{P,ref}` in dB, for a
        reference calibrated in a pressure field (Formula (11)).
    :param reference_diffuse_pressure_difference_db: :math:`\Delta_\mathrm{DP}`
        in dB, with Formula (11) only (Default: None, Table B.1).
    :return: The :class:`DiffuseFieldSensitivity`.
    :raises ValueError: if not exactly one reference calibration is given, a
        correction is given for a formula that does not take it, a column does
        not hold one value per band (or a single value), or a default is asked
        of Table B.1 at a frequency it does not print.
    """
    frequencies = _frequency_axis(frequencies_hz)
    given = {
        "random_incidence": reference_random_incidence_level_db,
        "free_field": reference_free_field_level_db,
        "pressure": reference_pressure_level_db,
    }
    chosen = [(route, value) for route, value in given.items() if value is not None]
    if len(chosen) != 1:
        msg = (
            "Give exactly one calibration of the reference instrument: "
            "'reference_random_incidence_level_db' (Formula (9)), "
            "'reference_free_field_level_db' (Formula (10)) or "
            "'reference_pressure_level_db' (Formula (11)); got "
            f"{[route for route, _ in chosen] or 'none'}."
        )
        raise ValueError(msg)
    route, reference_sensitivity = chosen[0]
    stray = {
        "reference_directivity_index_db": (
            reference_directivity_index_db,
            "free_field",
        ),
        "reference_diffuse_pressure_difference_db": (
            reference_diffuse_pressure_difference_db,
            "pressure",
        ),
    }
    for name, (value, owner) in stray.items():
        if value is not None and route != owner:
            msg = f"'{name}' belongs to the {owner} route, not to the {route} route."
            raise ValueError(msg)
    sensitivity_name = f"reference_{route}_level_db"
    sensitivity = _band_column(reference_sensitivity, sensitivity_name, frequencies)
    if route == "random_incidence":
        correction = np.zeros(frequencies.size)
    elif route == "free_field":
        name = "reference_directivity_index_db"
        correction = -(
            _table_b1_column(frequencies, "directivity_index_db", name)
            if reference_directivity_index_db is None
            else _band_column(reference_directivity_index_db, name, frequencies)
        )
    else:
        name = "reference_diffuse_pressure_difference_db"
        correction = (
            _table_b1_column(frequencies, "diffuse_pressure_difference_db", name)
            if reference_diffuse_pressure_difference_db is None
            else _band_column(
                reference_diffuse_pressure_difference_db, name, frequencies
            )
        )
    return DiffuseFieldSensitivity(
        frequencies_hz=frequencies,
        indicated_level_db=_band_column(
            indicated_level_db, "indicated_level_db", frequencies
        ),
        reference_indicated_level_db=_band_column(
            reference_indicated_level_db, "reference_indicated_level_db", frequencies
        ),
        reference_sensitivity_level_db=sensitivity,
        reference_correction_db=correction,
        route=route,
    )
