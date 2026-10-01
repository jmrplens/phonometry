#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Airborne noise of a steam turbine set and its driven machinery:
IEC 61063:1991 (EN 61063:1996).

IEC 61063 is a noise test code. It takes the survey method of ISO 3746 and
fixes, for one family of machines, what that method leaves open: the shape of
the measurement surface around a turbine, generator and exciter standing on
their operating floor, the microphone positions on it, how the background and
the room are corrected, and what the report says. The text read here is the
English one of BS EN 61063:1996, which reproduces IEC 1063:1991 without
modification; every clause, table and figure below was read on the printed
page, cited as PDF page and printed folio.

**The measurement surface** (clause 7.1, printed folio 7, PDF page 13). The
turbine set is enclosed by several *reference boxes* in juxtaposition, one per
part (turbine casings, gear, generator, exciter), terminating on the
reflecting plane. The measurement surface is made of right parallelepipeds
parallel to them at the measurement distance :math:`d = 1` m, and its area is
Equation (1),

.. math::

   S = 2\,h_\mathrm{max}\,b_\mathrm{max}
       + \sum_{i=1}^{Z} l_i\,(2 h_i + b_i) \tag{Eq. 1}

with :math:`l_i`, :math:`b_i` and :math:`h_i` the length, width and height of
the :math:`i`-th of the :math:`Z` parallelepipeds, dimensioned on the
measurement surface as Figure 2 draws them. The sum is the tops and the long
sides; :math:`2 h_\mathrm{max} b_\mathrm{max}` stands for every transverse
face, the two ends and the steps between neighbouring boxes. It is exact when
each cross-section contains the next one out towards both ends, as in both
drawings of Figure 2, and :attr:`TurbineMeasurementSurface.enveloping_area_m2`
gives the exact area of the stepped surface for the case it is not.

**The microphone positions** (clause 7.2, Figure 2). Five *key* positions are
prescribed: 1 and 5 at the centres of the two ends, 2 and 4 on the two long
sides and 3 overhead, the last three in the plane between the turbine and the
driven machinery. *Additional* positions follow at equal distances from the
key positions, close enough that "there is at least one measurement section
at each casing" (7.2.2): round the sides from 1 through 2, 5 and 4, and over
the set from 1 up the front end, across the top through 3 and down the rear
end to 5, as the plan and the elevation of Figure 2 draw them. Each of the two
paths is divided on its own, so the stations round the sides and those
overhead need not stand in the same transverse sections, as the drawings of
Figure 2 happen to put them; the text asks only for equal distances. The
overhead positions may be left out when a preliminary investigation shows
they move the sound power level by no more than 1,0 dB (NOTE of 7.2.2).

**The background correction** (clause 8.1, Table 2, printed folio 8, PDF page
14) is a stepped table applied at each microphone position, not the
closed form :math:`-10 \lg(1 - 10^{-0.1 \Delta L})` of ISO 3746:2010
Equation (12), which is applied to the surface-averaged level:

====================  ==============
Difference, dB        Correction, dB
====================  ==============
3                     3
4                     2
5                     2
6                     1
7                     1
8                     1
9                     0,5
10                    0,5
> 10                  0,0
====================  ==============

The background shall be at least 3 dB below the level with the source
operating (4.2); below that no valid measurement can be made, and the result
is only an indication of the upper limit (NOTE of 4.2).

**The environmental correction** :math:`K` (clause 8.2, Annex A). Figure A.3
(printed folio 12, PDF page 18) prints the curve and its formula,

.. math::

   K = 10 \lg\left[1 + \frac{4}{A/S}\right] \tag{Figure A.3}

with the equivalent absorption area :math:`A = 0{,}16\,V/T` of the room from
its reverberation time (A.3.1); A.3.2 obtains :math:`K = L_W - L_{Wr}` from a
calibrated reference sound source instead. :math:`K` shall not exceed 7 dB
(8.3 and A.3.3), which A.3.3 restates as :math:`A/S \ge 1`.

**The surface sound pressure level and the sound power level** (clauses 8.3
and 8.4, printed folio 9, PDF page 15):

.. math::

   \overline{L_{p\mathrm{A}}} = 10 \lg\left[\frac{1}{N}
       \sum_{i=1}^{N} 10^{0.1 L_{p\mathrm{A}i}}\right] - K \tag{Eq. 2}

   L_{W\mathrm{A}} = \overline{L_{p\mathrm{A}}}
       + 10 \lg\frac{S}{S_0}, \qquad S_0 = 1\ \mathrm{m}^2 \tag{Eq. 3}

**The report** (clauses 9 and 10, printed folios 9 and 10). The sound power
level is recorded rounded to the nearest whole decibel (9.4 g), and the report
states that it was obtained in full conformity with the standard and is
expressed in decibels above 1 pW, with at least the six items of clause 10.
The standard deviations of Table 1 (printed folio 4, PDF page 10), 5 dB for a
source with prominent discrete tones and 4 dB for a broadband one, are the
uncertainty the survey method tends to stay within.

The standard prints no worked example. Every function here is anchored in the
closed forms above and in the numbers the standard fixes: the nine cells of
Table 2, the two of Table 1, the 1 m of 7.1, the 7 dB of A.3.3, the 6 m/s of
4.3, the 3 dB of 4.2, the 1,0 dB of 7.2.2 and the 5 dB and 0,7 dB of the NOTE
of 8.3.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Literal

import numpy as np

from .._internal.frozen import read_only
from .._internal.levels_math import energy_mean
from .._internal.validation import (
    require_count,
    require_finite,
    require_finite_array,
    require_finite_fields,
    require_positive,
)
from ._shared import _S0, SoundPowerWarning

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

__all__ = [
    "TurbineEnvironmentalCorrection",
    "TurbineMeasurementSurface",
    "TurbineMicrophoneArray",
    "TurbineNoiseDeclaration",
    "TurbineReferenceBox",
    "TurbineSoundPowerResult",
    "TurbineTestEnvironmentCheck",
    "check_turbine_test_environment",
    "turbine_background_correction",
    "turbine_environmental_correction",
    "turbine_measurement_surface",
    "turbine_microphone_positions",
    "turbine_noise_declaration",
    "turbine_reference_source_correction",
    "turbine_sound_power",
]

#: The measurement distance ``d`` between the reference boxes and the
#: measurement surface, in metres: "The measurement distance (d) is 1 m"
#: (clause 7.1, printed folio 7).
_MEASUREMENT_DISTANCE_M = 1.0

#: Table 2 (printed folio 8, PDF page 14): the correction to subtract, in dB,
#: keyed by the difference between the level with the source operating and
#: the background level alone, in whole decibels. The row "> 10" is
#: :data:`_TABLE_2_ABOVE_DB`.
_TABLE_2: Mapping[int, float] = MappingProxyType(
    {3: 3.0, 4: 2.0, 5: 2.0, 6: 1.0, 7: 1.0, 8: 1.0, 9: 0.5, 10: 0.5}
)
#: The last row of Table 2: a difference above 10 dB takes no correction.
_TABLE_2_ABOVE_DB = 0.0
#: The background criterion of 4.2, in dB: the background "should be at least
#: 3 dB below" the level with the source operating, and the first row of
#: Table 2.
_BACKGROUND_CRITERION_DB = 3.0

#: The largest environmental correction the standard allows, in dB: "the
#: maximum allowable value of K is 7 dB" (8.3), "K shall not exceed 7 dB"
#: (A.3.3, printed folio 12).
_K_LIMIT_DB = 7.0
#: The factor of Figure A.3's formula, ``K = 10 lg[1 + 4/(A/S)]``.
_FOUR = 4.0
#: The Sabine constant of A.3.1, ``A = 0,16 (V/T)``, in seconds per metre.
_SABINE = 0.16

#: The machine length above which A.3.2 adds two reference-source positions,
#: in metres (NOTE of A.3.2, printed folio 12).
_LONG_MACHINE_M = 10.0
#: Reference-source determinations for a machine up to that length (one in the
#: middle of each longitudinal side) and above it (two more, at each end).
_SHORT_MACHINE_DETERMINATIONS = 2
_LONG_MACHINE_DETERMINATIONS = 4
#: The name of the A.3.2 route, as
#: :attr:`TurbineEnvironmentalCorrection.method` records it.
_REFERENCE_SOURCE: Final = "reference source"

#: The outdoor wind limit of 4.3, in metres per second: "the wind speed shall
#: be less than 6 m/s".
_WIND_LIMIT_M_S = 6.0
#: The wind speed above which 4.3 asks for a windscreen, in metres per second.
_WINDSCREEN_ABOVE_M_S = 1.0

#: The NOTE of 7.2.2: overhead positions may be deleted when their exclusion
#: moves the sound power level by no more than this, in dB.
_OVERHEAD_EFFECT_LIMIT_DB = 1.0

#: A limit reached through floating-point arithmetic is on the limit, in dB.
#: The limits of 4.2, 7.2.2, 8.3 and A.3.3 are judged on computed quantities:
#: a background 32,3 - 29,3 dB below is 2,999 999 999 999 996 in binary and
#: must still read as 3 dB, the mean of two reference-source readings, 85,4
#: and 89,2 dB, less 80,3 dB is 7,000 000 000 000 014 and must still read as
#: 7 dB, and overhead positions that move the level by 1,0 dB come out of the
#: difference of two energy means near 80 dB a unit or two of their last
#: place either side of 1,0, which side depending on the machine.
_BOUNDARY_SLACK_DB = 1e-9

#: Decimals a level is cut to before it is rounded half up: far below any
#: level a meter reads, far above the binary error of a decimal level, so a
#: difference of 20,4 - 14,9 dB, 5,499 999 999 999 998 in binary, still
#: rounds to 6 as the 5,5 dB it is.
_BINARY_SLACK_DECIMALS = 9

#: The NOTE of 8.3: a simple arithmetic average may be used when the range of
#: the position levels does not exceed this, in dB.
_ARITHMETIC_RANGE_DB = 5.0

#: Table 1 (printed folio 4, PDF page 10): the standard deviation of the
#: A-weighted sound power level by the survey method, in dB, for a source with
#: prominent discrete tones and for one whose sound is uniformly distributed
#: in frequency.
_TABLE_1: Mapping[bool, float] = MappingProxyType({True: 5.0, False: 4.0})

#: The fewest positions a determination may rest on: the five key positions
#: of Figure 2, less the overhead one once 7.2.2 lets it be deleted.
_MIN_POSITIONS = 4

#: A position has three coordinates, ``(x, y, z)``, one row per position.
_COORDINATES = 3
_MATRIX = 2

#: Tolerance, in metres, for placing a point on the outline of the surface:
#: the coordinates are sums of the box dimensions, so they agree to rounding.
_GEOMETRY_TOLERANCE_M = 1e-9

#: The statement clause 10 requires the report to contain.
_CONFORMITY_STATEMENT = (
    "The A-weighted sound power level has been obtained in full conformity "
    "with the procedures of IEC 61063:1991 and is expressed in decibels "
    "above 1 pW (10^-12 W)."
)


def _round_half_up(value: float) -> int:
    """Round to the nearest whole number, halves upwards (4.5 to 5).

    The value is first cut to nine decimals, so a half that comes out a hair
    under it in binary still rounds up.
    """
    return math.floor(round(value, _BINARY_SLACK_DECIMALS) + 0.5)


def _below_criterion(level_difference_db: ArrayLike) -> np.ndarray:
    """Which background level differences are less than 3 dB (4.2)."""
    difference = np.asarray(level_difference_db, dtype=np.float64)
    return np.asarray(
        difference < _BACKGROUND_CRITERION_DB - _BOUNDARY_SLACK_DB, dtype=bool
    )


def _within_k_limit(k: float) -> bool:
    """Whether an environmental correction does not exceed 7 dB (8.3, A.3.3)."""
    return k <= _K_LIMIT_DB + _BOUNDARY_SLACK_DB


# ---------------------------------------------------------------------------
# The measurement surface (clause 7.1, Equation (1))
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TurbineReferenceBox:
    """One reference box of a turbine set (clause 7.1).

    The smallest rectangular box that just encloses one part of the set, its
    lagging and any noise control screen or enclosure included, and
    terminates on the reflecting plane (3.5 and 7.1). The boxes of a set stand
    in juxtaposition along its shaft, in the order they are passed, each
    centred on the shaft line. A set whose boxes are flush on one long side
    and step only on the other, as Figure 2 a draws it, is modelled as if
    every box were centred: Equation (1) does not change, but beside a
    narrower box the positions of each long side stand half the difference in
    width across from where the drawing puts them.

    :ivar length_m: Length along the shaft, in metres.
    :ivar width_m: Width across the shaft, in metres.
    :ivar height_m: Height above the reflecting plane, in metres.
    :ivar label: What the box encloses, for the figure (``"LP turbine"``).
    :raises ValueError: if a dimension is not a positive finite number.
    """

    length_m: float
    width_m: float
    height_m: float
    label: str = ""

    def __post_init__(self) -> None:
        """Refuse a box with no extent in one of its three directions."""
        for name in ("length_m", "width_m", "height_m"):
            require_positive(getattr(self, name), name)


@dataclass(frozen=True)
class TurbineMeasurementSurface:
    r"""The measurement surface of a turbine set and its area (clause 7.1).

    Built by :func:`turbine_measurement_surface`. The parallelepipeds are the
    reference boxes grown by the measurement distance on every side except the
    floor: 1 m wider on each side, 1 m taller, and 1 m longer at each end of
    the set.

    :ivar reference_boxes: The reference boxes, in order along the shaft.
    :ivar lengths_m: :math:`l_i` of each parallelepiped of the measurement
        surface, in metres.
    :ivar widths_m: :math:`b_i`, in metres.
    :ivar heights_m: :math:`h_i`, in metres.
    :ivar area_m2: :math:`S` of Equation (1), in square metres.
    :ivar measurement_distance_m: :math:`d`, 1 m (7.1).
    """

    reference_boxes: tuple[TurbineReferenceBox, ...]
    lengths_m: np.ndarray
    widths_m: np.ndarray
    heights_m: np.ndarray
    area_m2: float
    measurement_distance_m: float = _MEASUREMENT_DISTANCE_M

    def __post_init__(self) -> None:
        """Refuse parallelepipeds that disagree in number or are not positive.

        :raises ValueError: if the three dimension arrays and the reference
            boxes do not have one entry each per parallelepiped, or a
            dimension or the area is not positive and finite.
        """
        count = len(self.reference_boxes)
        for name in ("lengths_m", "widths_m", "heights_m"):
            values = np.asarray(getattr(self, name))
            if values.shape != (count,):
                msg = (
                    f"TurbineMeasurementSurface: '{name}' must hold one value "
                    f"per reference box ({count}); got shape {values.shape}."
                )
                raise ValueError(msg)
            if count == 0 or not np.all(np.isfinite(values)) or np.any(values <= 0.0):
                msg = (
                    f"TurbineMeasurementSurface: '{name}' must be positive and finite."
                )
                raise ValueError(msg)
        require_positive(self.area_m2, "area_m2")

    @property
    def x_edges_m(self) -> np.ndarray:
        """Where each parallelepiped starts and ends along the shaft, in metres.

        :return: ``Z + 1`` abscissae from the front end of the measurement
            surface (0) to its rear end.
        """
        return np.concatenate(([0.0], np.cumsum(self.lengths_m)))

    @property
    def max_height_m(self) -> float:
        r""":math:`h_\mathrm{max}` of Equation (1), in metres."""
        return float(np.max(self.heights_m))

    @property
    def max_width_m(self) -> float:
        r""":math:`b_\mathrm{max}` of Equation (1), in metres."""
        return float(np.max(self.widths_m))

    @property
    def enveloping_area_m2(self) -> float:
        r"""The exact area of the stepped surface, in square metres.

        The tops, the long sides and the two ends of the parallelepipeds, and
        at each step the part of either cross-section the other does not
        cover. Equation (1) counts every transverse face together as
        :math:`2 h_\mathrm{max} b_\mathrm{max}`, which is exactly their area
        when the cross-sections shrink from one largest section towards both
        ends, each containing the next, as in both drawings of Figure 2.
        Otherwise it can err either way: it counts too much when the tallest
        and the widest parallelepipeds are different ones, and too little when
        a small section stands between two large ones.

        :return: The area of the surface as drawn, in square metres.
        """
        lengths = np.asarray(self.lengths_m)
        widths = np.asarray(self.widths_m)
        heights = np.asarray(self.heights_m)
        area = float(np.sum(lengths * (2.0 * heights + widths)))
        area += float(widths[0] * heights[0] + widths[-1] * heights[-1])
        for i in range(len(lengths) - 1):
            common = min(widths[i], widths[i + 1]) * min(heights[i], heights[i + 1])
            area += float(
                widths[i] * heights[i] + widths[i + 1] * heights[i + 1] - 2.0 * common
            )
        return area

    def plot(
        self,
        ax: Axes | None = None,
        *,
        view: Literal["plan", "elevation"] = "plan",
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        """Draw the reference boxes and the measurement surface around them.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param view: ``"plan"`` (default), seen from above, or
            ``"elevation"``, seen from the side.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the outline of the measurement surface.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_turbine_layout

        check_language(language)
        return plot_turbine_layout(
            self, None, ax=ax, view=view, language=language, **kwargs
        )


def turbine_measurement_surface(
    reference_boxes: Sequence[TurbineReferenceBox],
) -> TurbineMeasurementSurface:
    r"""Measurement surface of a turbine set and its area :math:`S` (Equation (1)).

    The parallelepipeds of the measurement surface are the reference boxes
    spaced out by the measurement distance :math:`d = 1` m (7.1): each is
    :math:`2d` wider and :math:`d` taller than its box, and the first and the
    last are :math:`d` longer, at the two ends of the set. Then

    .. math::

       S = 2\,h_\mathrm{max}\,b_\mathrm{max} + \sum_{i=1}^{Z} l_i\,(2 h_i + b_i).

    A single box gives the enveloping parallelepiped of ISO 3746,
    :math:`l b + 2 l h + 2 b h`.

    :param reference_boxes: The reference boxes in order along the shaft, from
        the turbine end (Figure 2): one :class:`TurbineReferenceBox` per part.
    :return: The surface, its parallelepipeds and its area.
    :raises ValueError: if no box is given or an entry is not a
        :class:`TurbineReferenceBox`.
    """
    boxes = tuple(reference_boxes)
    if not boxes:
        msg = "turbine_measurement_surface: at least one reference box is needed."
        raise ValueError(msg)
    for box in boxes:
        if not isinstance(box, TurbineReferenceBox):
            msg = (
                "turbine_measurement_surface: every entry must be a "
                f"TurbineReferenceBox; got {type(box).__name__}."
            )
            raise ValueError(msg)
    d = _MEASUREMENT_DISTANCE_M
    lengths = np.array([box.length_m for box in boxes], dtype=np.float64)
    lengths[0] += d
    lengths[-1] += d
    widths = np.array([box.width_m + 2.0 * d for box in boxes], dtype=np.float64)
    heights = np.array([box.height_m + d for box in boxes], dtype=np.float64)
    area = 2.0 * float(np.max(heights)) * float(np.max(widths))
    area += float(np.sum(lengths * (2.0 * heights + widths)))
    return TurbineMeasurementSurface(
        reference_boxes=boxes,
        lengths_m=read_only(lengths),
        widths_m=read_only(widths),
        heights_m=read_only(heights),
        area_m2=area,
    )


# ---------------------------------------------------------------------------
# The microphone positions (clause 7.2, Figure 2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TurbineMicrophoneArray:
    """The key and additional microphone positions of Figure 2 (clause 7.2).

    Built by :func:`turbine_microphone_positions`. Coordinates are in metres:
    ``x`` along the shaft from the front end of the measurement surface, ``y``
    across it from the shaft line (key position 2 on the positive side) and
    ``z`` above the reflecting plane. The positions run once round the surface
    at the microphone height, from key position 1 through 2, 5 and 4 back
    towards 1, and then along the overhead line in the vertical plane of the
    shaft: up the front end above key position 1, across the top through 3
    and down the rear end towards 5.

    :ivar surface: The measurement surface the positions lie on.
    :ivar positions_m: One row ``(x, y, z)`` per position, in metres.
    :ivar labels: ``"1"`` to ``"5"`` for the key positions, ``""`` for the
        additional ones.
    :ivar overhead_mask: Which positions are on the overhead line, the ends
        above the row round the sides and the top of the surface.
    :ivar microphone_height_m: Height of the positions round the sides, in
        metres.
    :ivar spacing_m: The largest distance allowed between neighbours, in
        metres.
    :ivar turbine_boxes: How many of the reference boxes enclose the turbine;
        key positions 2, 3 and 4 stand in the plane that follows them.
    :ivar positions_per_box: Positions on one long side within the length of
        each parallelepiped (the other side mirrors them).
    """

    surface: TurbineMeasurementSurface
    positions_m: np.ndarray
    labels: tuple[str, ...]
    overhead_mask: np.ndarray
    microphone_height_m: float
    spacing_m: float
    turbine_boxes: int
    positions_per_box: tuple[int, ...]

    def __post_init__(self) -> None:
        """Refuse positions, labels and masks that disagree in number.

        :raises ValueError: if ``positions_m`` is not ``(N, 3)``, if
            ``labels`` or ``overhead_mask`` does not have ``N`` entries, or if
            ``positions_per_box`` does not have one entry per parallelepiped.
        """
        positions = np.asarray(self.positions_m)
        if positions.ndim != _MATRIX or positions.shape[1] != _COORDINATES:
            msg = (
                "TurbineMicrophoneArray: 'positions_m' must be (N, 3); got "
                f"shape {positions.shape}."
            )
            raise ValueError(msg)
        count = positions.shape[0]
        if len(self.labels) != count or np.asarray(self.overhead_mask).shape != (
            count,
        ):
            msg = (
                "TurbineMicrophoneArray: 'labels' and 'overhead_mask' must have "
                f"one entry per position ({count})."
            )
            raise ValueError(msg)
        if len(self.positions_per_box) != len(self.surface.lengths_m):
            msg = (
                "TurbineMicrophoneArray: 'positions_per_box' must have one entry "
                "per parallelepiped."
            )
            raise ValueError(msg)
        require_finite_fields(self, "positions_m")

    @property
    def count(self) -> int:
        """Number of positions, key and additional, overhead included."""
        return int(np.asarray(self.positions_m).shape[0])

    @property
    def key_mask(self) -> np.ndarray:
        """Which positions are the five key positions of Figure 2."""
        return np.array([label != "" for label in self.labels], dtype=bool)

    @property
    def every_box_sampled(self) -> bool:
        """Whether every parallelepiped has a position on its long sides (7.2.2).

        7.2.2 asks for "at least one measurement section at each casing". The
        library knows the reference boxes, not the casings inside them, so it
        judges each parallelepiped: where one box holds several casings (the
        HP and IP turbines of Figure 2 b), whether each of them is reached is
        read from :attr:`positions_m`.
        """
        return min(self.positions_per_box) >= 1

    def plot(
        self,
        ax: Axes | None = None,
        *,
        view: Literal["plan", "elevation"] = "plan",
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        """Draw the positions on the measurement surface, as Figure 2 does.

        Key positions are crosses with their number, additional ones circles.
        In elevation only the near side is drawn, the side of key position 4
        as in both elevations of Figure 2, with the overhead line.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param view: ``"plan"`` (default) or ``"elevation"``.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the outline of the measurement surface.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_turbine_layout

        check_language(language)
        return plot_turbine_layout(
            self.surface, self, ax=ax, view=view, language=language, **kwargs
        )


def _outline(edges: np.ndarray, levels: np.ndarray, base: float) -> np.ndarray:
    """One half of the outline of the surface, from end to end.

    In plan (``levels`` the half widths, ``base`` 0) it runs from the centre
    of the front end out to the corner, along the long side with every step,
    and back in to the centre of the rear end. In elevation (``levels`` the
    heights, ``base`` the microphone height) it runs from key position 1 up
    the front end, across the top with every step, and down the rear end to
    key position 5.
    """
    points = [(float(edges[0]), base)]
    for i, level in enumerate(levels):
        points.extend(((edges[i], level), (edges[i + 1], level)))
    points.append((float(edges[-1]), base))
    return np.array(points, dtype=np.float64)


def _arc_lengths(polyline: np.ndarray) -> np.ndarray:
    """Cumulative length along a polyline, from its first vertex."""
    steps = np.hypot(*np.diff(polyline, axis=0).T)
    return np.concatenate(([0.0], np.cumsum(steps)))


def _point_at(polyline: np.ndarray, lengths: np.ndarray, s: float) -> np.ndarray:
    """The point a distance ``s`` along a polyline."""
    index = int(np.searchsorted(lengths, s, side="right") - 1)
    index = min(max(index, 0), len(polyline) - 2)
    span = lengths[index + 1] - lengths[index]
    fraction = 0.0 if span <= 0.0 else (s - lengths[index]) / span
    start = np.asarray(polyline[index], dtype=np.float64)
    return start + fraction * (
        np.asarray(polyline[index + 1], dtype=np.float64) - start
    )


def _distance_along(
    polyline: np.ndarray, lengths: np.ndarray, point: np.ndarray
) -> float:
    """How far along a polyline a point on it lies.

    :raises ValueError: if the point is not on the polyline.
    """
    for i in range(len(polyline) - 1):
        start, end = polyline[i], polyline[i + 1]
        span = float(lengths[i + 1] - lengths[i])
        if span <= 0.0:
            continue
        direction = (end - start) / span
        offset = point - start
        along = float(np.dot(offset, direction))
        across = float(np.hypot(*(offset - along * direction)))
        inside = -_GEOMETRY_TOLERANCE_M <= along <= span + _GEOMETRY_TOLERANCE_M
        if across <= _GEOMETRY_TOLERANCE_M and inside:
            return float(lengths[i]) + min(max(along, 0.0), span)
    msg = "A key position does not lie on the outline of the measurement surface."
    raise ValueError(msg)


def _divisions(length: float, spacing: float) -> int:
    """The fewest equal intervals of a run that are no longer than ``spacing``."""
    return max(1, math.ceil(length / spacing - 1e-12))


def _coupling_corner(
    surface: TurbineMeasurementSurface, coupling: int
) -> tuple[float, float, float]:
    """Where key positions 2, 3 and 4 stand: ``x``, half-width and height (Figure 2).

    The plane between the turbine and the driven machinery, at the outer
    corner of the wider (or taller) of the two parallelepipeds that meet
    there; a set in a single box has that plane at mid-length.
    """
    parts = len(surface.lengths_m)
    edges = surface.x_edges_m
    widths = surface.widths_m
    heights = surface.heights_m
    if parts == 1:
        return float(edges[1]) / 2.0, float(widths[0]) / 2.0, float(heights[0])
    if coupling >= parts:
        msg = (
            f"turbine_microphone_positions: 'turbine_boxes' ({coupling}) must "
            f"leave at least one of the {parts} boxes for the driven machinery."
        )
        raise ValueError(msg)
    return (
        float(edges[coupling]),
        max(float(widths[coupling - 1]), float(widths[coupling])) / 2.0,
        max(float(heights[coupling - 1]), float(heights[coupling])),
    )


def turbine_microphone_positions(
    surface: TurbineMeasurementSurface,
    *,
    microphone_height_m: float,
    spacing_m: float,
    turbine_boxes: int = 1,
    include_overhead: bool = True,
) -> TurbineMicrophoneArray:
    """Key and additional microphone positions on the measurement surface (7.2).

    The five key positions follow Figure 2. Position 1 is the centre of the
    front end and 5 the centre of the rear end; 2 and 4 are on the two long
    sides and 3 is overhead, all three in the plane between the turbine and
    the driven machinery, at the outer corner of the wider (or taller) of the
    two parallelepipeds that meet there, as both drawings of Figure 2 place
    them. A set in a single box has that plane at mid-length.

    The additional positions are "arranged at equal distances" beginning at the
    key positions (7.2.2). They lie on two paths. One runs round the sides at
    the microphone height, 1 to 2, 2 to 5, 5 to 4 and 4 to 1, as the plans of
    Figure 2 draw it. The other, the overhead line, runs in the vertical plane
    of the shaft from 1 up the front end, across the top and its steps to 3,
    and on to the rear end and down it to 5, as the elevations draw it with a
    position on the front end above key position 1. Each run between two key
    positions is divided into the fewest equal intervals no longer than
    ``spacing_m``, and a position stands at each division. The two paths are
    divided each on its own, so their stations need not line up in the
    transverse sections the drawings of Figure 2 show; 7.2.2 asks only for
    equal distances. The distance has to be short enough to put "at least one
    measurement section at each casing"; the library judges it per
    parallelepiped, and when a spacing leaves one with no position on its
    long sides a :class:`~phonometry.emission.SoundPowerWarning` is emitted
    and :attr:`TurbineMicrophoneArray.every_box_sampled` is ``False``.

    Figure 2 draws the positions round the sides on one horizontal row
    without dimensioning its height, so the height is the caller's, and it has
    to lie on the sides of every parallelepiped.

    :param surface: The measurement surface, from
        :func:`turbine_measurement_surface`.
    :param microphone_height_m: Height of the row round the sides, in metres,
        above the reflecting plane and no higher than the lowest
        parallelepiped.
    :param spacing_m: The largest distance between neighbouring positions
        along the path, in metres.
    :param turbine_boxes: How many reference boxes, from the front, enclose
        the turbine (1 for Figure 2 a, 2 for Figure 2 b, where the HP and IP
        casings share one box and the LP turbine has its own). Ignored for a
        set in a single box.
    :param include_overhead: ``False`` leaves the overhead line out, key
        position 3 with it, as the NOTE of 7.2.2 allows once a preliminary
        investigation has shown the overhead positions move the sound power
        level by no more than 1,0 dB (see
        :attr:`TurbineSoundPowerResult.overhead_effect_db`).
    :return: The positions, their labels and the overhead mask.
    :raises ValueError: for a height outside the sides, a non-positive
        spacing, or a ``turbine_boxes`` that leaves no driven machinery.
    """
    if not isinstance(surface, TurbineMeasurementSurface):
        msg = "turbine_microphone_positions: 'surface' must be a TurbineMeasurementSurface."
        raise ValueError(msg)
    height = require_positive(microphone_height_m, "microphone_height_m")
    spacing = require_positive(spacing_m, "spacing_m")
    if height > float(np.min(surface.heights_m)):
        msg = (
            f"turbine_microphone_positions: 'microphone_height_m' ({height:g} m) "
            "must not exceed the lowest parallelepiped of the measurement surface "
            f"({float(np.min(surface.heights_m)):g} m)."
        )
        raise ValueError(msg)
    parts = len(surface.lengths_m)
    edges = surface.x_edges_m
    widths = np.asarray(surface.widths_m)
    heights = np.asarray(surface.heights_m)
    coupling = require_count(turbine_boxes, "turbine_boxes")
    x_key, y_key, z_key = _coupling_corner(surface, coupling)

    def runs(line: np.ndarray, key: np.ndarray) -> tuple[list[np.ndarray], ...]:
        """The division points from the front end to ``key`` and on to the rear."""
        lengths = _arc_lengths(line)
        s_key = _distance_along(line, lengths, key)

        def run(start: float, stop: float) -> list[np.ndarray]:
            n = _divisions(stop - start, spacing)
            return [
                _point_at(line, lengths, start + (stop - start) * k / n)
                for k in range(1, n)
            ]

        return run(0.0, s_key), run(s_key, float(lengths[-1]))

    run_a, run_b = runs(  # key 1 to key 2, key 2 to key 5
        _outline(edges, widths / 2.0, 0.0), np.array([x_key, y_key])
    )
    key_2 = np.array([x_key, y_key])
    rows: list[tuple[float, float, float]] = []
    labels: list[str] = []
    overhead: list[bool] = []

    def add(x: float, y: float, z: float, label: str, *, top: bool = False) -> None:
        rows.append((float(x), float(y), float(z)))
        labels.append(label)
        overhead.append(top)

    add(0.0, 0.0, height, "1")
    for point in run_a:
        add(point[0], point[1], height, "")
    add(key_2[0], key_2[1], height, "2")
    for point in run_b:
        add(point[0], point[1], height, "")
    add(float(edges[-1]), 0.0, height, "5")
    for point in reversed(run_b):
        add(point[0], -point[1], height, "")
    add(key_2[0], -key_2[1], height, "4")
    for point in reversed(run_a):
        add(point[0], -point[1], height, "")

    if include_overhead:
        front, rear = runs(  # key 1 to key 3, key 3 to key 5
            _outline(edges, heights, height), np.array([x_key, z_key])
        )
        for point in front:
            add(point[0], 0.0, point[1], "", top=True)
        add(x_key, 0.0, z_key, "3", top=True)
        for point in rear:
            add(point[0], 0.0, point[1], "", top=True)

    positions = np.array(rows, dtype=np.float64)
    side = (positions[:, 1] > _GEOMETRY_TOLERANCE_M) & ~np.array(overhead)
    per_box = tuple(
        int(
            np.count_nonzero(
                side
                & (positions[:, 0] >= edges[i] - _GEOMETRY_TOLERANCE_M)
                & (positions[:, 0] <= edges[i + 1] + _GEOMETRY_TOLERANCE_M)
                & np.isclose(
                    positions[:, 1], widths[i] / 2.0, atol=_GEOMETRY_TOLERANCE_M
                )
            )
        )
        for i in range(parts)
    )
    array = TurbineMicrophoneArray(
        surface=surface,
        positions_m=read_only(positions),
        labels=tuple(labels),
        overhead_mask=read_only(np.array(overhead, dtype=bool)),
        microphone_height_m=height,
        spacing_m=spacing,
        turbine_boxes=coupling,
        positions_per_box=per_box,
    )
    if not array.every_box_sampled:
        empty = [str(i + 1) for i, n in enumerate(per_box) if n == 0]
        warnings.warn(
            f"A spacing of {spacing:g} m leaves parallelepiped(s) {', '.join(empty)} "
            "with no position on their long sides; IEC 61063 7.2.2 asks for at "
            "least one measurement section at each casing of the set.",
            SoundPowerWarning,
            stacklevel=2,
        )
    return array


# ---------------------------------------------------------------------------
# The corrections (clause 8.1 Table 2, clause 8.2 and Annex A)
# ---------------------------------------------------------------------------


def turbine_background_correction(level_difference_db: ArrayLike) -> float | np.ndarray:
    r"""Correction for background noise of Table 2 (clause 8.1).

    The correction to subtract from the level measured with the source
    operating, read from the stepped Table 2 of IEC 61063 at the difference
    between that level and the background level alone: 3 dB at a difference
    of 3 dB, 2 dB at 4 and 5 dB, 1 dB at 6 to 8 dB, 0,5 dB at 9 and 10 dB and
    0,0 dB above 10 dB.

    The last row is read first, on the difference as measured: any difference
    above 10 dB is "> 10" and takes no correction, 10,2 dB as much as 11 dB.
    Between 3 and 10 dB the table is indexed in whole decibels, so the
    difference is rounded to the nearest one (halves upwards) before it is
    read; 9,5 dB up to 10 dB takes the 0,5 dB of the row 10. That is how the
    library reads the stepped table of ISO/TS 7849-1, whose open row is also
    judged before the rounding. Table 2 prints nothing below 3 dB, the
    criterion of 4.2, where "a valid measurement of the machine under test
    cannot be made": there the 3 dB of the first row is returned. The level
    it leaves is still an upper limit, because the exact correction for a
    smaller difference is larger, which is how the NOTE of 4.2 lets such a
    result be used, and it is the value ISO 3746:2010 8.3.3 prints for the
    same case. :func:`turbine_sound_power` marks such a determination as an
    upper limit.

    This is not the :math:`K_{1\mathrm{A}} = -10 \lg(1 - 10^{-0.1 \Delta L})`
    of ISO 3746:2010 Equation (12). The steps depart from it by a few tenths
    of a decibel either way, and they are applied position by position rather
    than to the surface-averaged level.

    :param level_difference_db: The level with the source operating less the
        background level, at each position, in dB (scalar or 1-D array).
    :return: The correction to subtract, in dB: a ``float`` for a scalar, an
        array for an array.
    :raises ValueError: if a difference is not finite.
    """
    scalar = np.ndim(level_difference_db) == 0
    difference = require_finite_array(level_difference_db, "level_difference_db")
    first_row = _TABLE_2[int(_BACKGROUND_CRITERION_DB)]
    last_row = max(_TABLE_2)

    def row(raw: float) -> float:
        # The open row "> 10" is judged on the difference as measured, before
        # rounding: 10,3 dB is above 10 dB, and Table 2 prints 0,0 for it.
        if raw > last_row + _BOUNDARY_SLACK_DB:
            return _TABLE_2_ABOVE_DB
        if raw < _BACKGROUND_CRITERION_DB - _BOUNDARY_SLACK_DB:
            return first_row
        return _TABLE_2[_round_half_up(raw)]

    correction = np.array([row(float(raw)) for raw in difference], dtype=np.float64)
    return float(correction[0]) if scalar else correction


@dataclass(frozen=True)
class TurbineEnvironmentalCorrection:
    """The environmental correction ``K`` of a test room (clause 8.2, Annex A).

    Built by :func:`turbine_environmental_correction` (A.3.1, Figure A.3) or
    by :func:`turbine_reference_source_correction` (A.3.2).

    :ivar environmental_correction_db: :math:`K`, in dB.
    :ivar method: ``"absorption"`` (A.3.1) or ``"reference source"`` (A.3.2).
    :ivar surface_area_m2: :math:`S` (A.3.1), in square metres, or ``None``.
    :ivar absorption_area_m2: :math:`A` (A.3.1), in square metres, or ``None``.
    :ivar reference_levels_db: The determinations of the reference source's
        sound power level :math:`L_W` (A.3.2), in dB, or ``None``.
    :ivar calibrated_level_db: :math:`L_{Wr}` (A.3.2), in dB, or ``None``.
    """

    environmental_correction_db: float
    method: Literal["absorption", "reference source"]
    surface_area_m2: float | None = None
    absorption_area_m2: float | None = None
    reference_levels_db: np.ndarray | None = None
    calibrated_level_db: float | None = None

    def __post_init__(self) -> None:
        """Refuse a correction without the data of the route it names.

        :raises ValueError: if ``method`` is neither route, if the route's
            inputs are missing, or if a value is not finite.
        """
        if self.method not in ("absorption", _REFERENCE_SOURCE):
            msg = (
                "TurbineEnvironmentalCorrection: 'method' must be 'absorption' or "
                f"'reference source'; got {self.method!r}."
            )
            raise ValueError(msg)
        if self.method == "absorption" and (
            self.surface_area_m2 is None or self.absorption_area_m2 is None
        ):
            msg = (
                "TurbineEnvironmentalCorrection: the absorption route needs "
                "'surface_area_m2' and 'absorption_area_m2'."
            )
            raise ValueError(msg)
        if self.method == _REFERENCE_SOURCE and (
            self.reference_levels_db is None or self.calibrated_level_db is None
        ):
            msg = (
                "TurbineEnvironmentalCorrection: the reference-source route needs "
                "'reference_levels_db' and 'calibrated_level_db'."
            )
            raise ValueError(msg)
        require_finite_fields(
            self,
            "environmental_correction_db",
            "surface_area_m2",
            "absorption_area_m2",
            "reference_levels_db",
            "calibrated_level_db",
        )

    @property
    def ratio(self) -> float | None:
        """:math:`A/S`, the abscissa of Figure A.3, or ``None`` (A.3.2)."""
        if self.surface_area_m2 is None or self.absorption_area_m2 is None:
            return None
        return self.absorption_area_m2 / self.surface_area_m2

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw Figure A.3 with this room on it.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the curve of Figure A.3.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_turbine_environmental_correction

        check_language(language)
        return plot_turbine_environmental_correction(
            self.environmental_correction_db,
            self.ratio,
            passes=None,
            ax=ax,
            language=language,
            **kwargs,
        )


def turbine_environmental_correction(
    surface_area_m2: float,
    *,
    absorption_area_m2: float | None = None,
    volume_m3: float | None = None,
    reverberation_time_s: float | None = None,
) -> TurbineEnvironmentalCorrection:
    r"""Environmental correction :math:`K` from the room absorption (A.3.1).

    Figure A.3 prints the curve and its formula,

    .. math::

       K = 10 \lg\left[1 + \frac{4}{A/S}\right],

    with :math:`A` the equivalent sound absorption area of the room, either
    given or from its reverberation time, :math:`A = 0{,}16\,V/T` (A.3.1),
    and :math:`S` the area of the measurement surface from Equation (1). It is
    the :math:`K_2` of ISO 3744 and ISO 3746. The result is not refused above
    the 7 dB the standard allows; :func:`check_turbine_test_environment` is
    the judgement, and :func:`turbine_sound_power` warns.

    :param surface_area_m2: :math:`S`, in square metres.
    :param absorption_area_m2: :math:`A`, in square metres; or give
        ``volume_m3`` and ``reverberation_time_s`` instead.
    :param volume_m3: :math:`V` of the test room, in cubic metres.
    :param reverberation_time_s: :math:`T` of the test room with A-weighting
        on the receiving system, in seconds.
    :return: The correction and the room data it came from.
    :raises ValueError: unless exactly one of the two routes to :math:`A` is
        given whole, or for a non-positive input.
    """
    area = require_positive(surface_area_m2, "surface_area_m2")
    by_room = (volume_m3, reverberation_time_s)
    if absorption_area_m2 is not None and any(v is not None for v in by_room):
        msg = (
            "turbine_environmental_correction: give 'absorption_area_m2' or "
            "'volume_m3' with 'reverberation_time_s', not both."
        )
        raise ValueError(msg)
    if absorption_area_m2 is not None:
        absorption = require_positive(absorption_area_m2, "absorption_area_m2")
    elif volume_m3 is not None and reverberation_time_s is not None:
        volume = require_positive(volume_m3, "volume_m3")
        time = require_positive(reverberation_time_s, "reverberation_time_s")
        absorption = _SABINE * volume / time
    else:
        msg = (
            "turbine_environmental_correction: give 'absorption_area_m2', or "
            "'volume_m3' and 'reverberation_time_s' together (A.3.1)."
        )
        raise ValueError(msg)
    k = 10.0 * math.log10(1.0 + _FOUR / (absorption / area))
    return TurbineEnvironmentalCorrection(
        environmental_correction_db=k,
        method="absorption",
        surface_area_m2=area,
        absorption_area_m2=absorption,
    )


def turbine_reference_source_correction(
    sound_power_levels_db: ArrayLike,
    *,
    calibrated_level_db: float,
    machine_length_m: float,
) -> TurbineEnvironmentalCorrection:
    """Environmental correction :math:`K = L_W - L_{Wr}` from a reference source (A.3.2).

    :math:`L_{Wr}` is the calibrated sound power level of the reference sound
    source, determined in a free field over a reflecting plane
    (:math:`K = 0`), and :math:`L_W` the sound power level the same source
    shows in the test room by the survey method of ISO 3746 with :math:`K`
    taken as zero, on a measurement surface 1 m from it. By the NOTE of A.3.2,
    :math:`L_W` is the mean of two determinations, the source standing in the
    middle of each longitudinal side of the turbine set; a machine longer than
    10 m takes two more, with the source at each end. The NOTE says "mean
    value" and does not say which mean; the library takes the arithmetic mean
    of the determinations.

    :param sound_power_levels_db: The determinations of :math:`L_W`, in dB:
        two for a machine up to 10 m long, four above.
    :param calibrated_level_db: :math:`L_{Wr}`, in dB re 1 pW.
    :param machine_length_m: Length of the machine under test, in metres,
        which sets how many determinations are needed.
    :return: The correction and the determinations it came from.
    :raises ValueError: for the wrong number of determinations or a
        non-finite level.
    """
    levels = require_finite_array(sound_power_levels_db, "sound_power_levels_db")
    reference = require_finite(calibrated_level_db, "calibrated_level_db")
    length = require_positive(machine_length_m, "machine_length_m")
    expected = (
        _LONG_MACHINE_DETERMINATIONS
        if length > _LONG_MACHINE_M
        else _SHORT_MACHINE_DETERMINATIONS
    )
    if levels.ndim != 1 or levels.size != expected:
        msg = (
            f"turbine_reference_source_correction: a machine {length:g} m long "
            f"needs {expected} determinations of the reference source (NOTE of "
            f"A.3.2); got {levels.size}."
        )
        raise ValueError(msg)
    k = float(np.mean(levels)) - reference
    return TurbineEnvironmentalCorrection(
        environmental_correction_db=k,
        method=_REFERENCE_SOURCE,
        reference_levels_db=read_only(levels.copy()),
        calibrated_level_db=reference,
    )


@dataclass(frozen=True)
class TurbineTestEnvironmentCheck:
    r"""Whether the test environment qualifies for IEC 61063 (A.3.3, 4.3).

    Built by :func:`check_turbine_test_environment`.

    :ivar environmental_correction_db: :math:`K`, in dB.
    :ivar ratio: :math:`A/S`, when the correction came from the room
        absorption, else ``None``.
    :ivar correction_ok: :math:`K \le 7` dB (A.3.3).
    :ivar wind_speed_m_s: The wind speed outdoors, in m/s, or ``None``.
    :ivar wind_ok: The wind speed is below 6 m/s (4.3), or ``None`` indoors.
    :ivar windscreen_advised: The wind is above 1 m/s, where 4.3 asks for a
        windscreen.
    """

    environmental_correction_db: float
    ratio: float | None
    correction_ok: bool
    wind_speed_m_s: float | None = None
    wind_ok: bool | None = None
    windscreen_advised: bool = False

    @property
    def passes(self) -> bool:
        """The verdict: the environment qualifies for measurements to the standard."""
        return self.correction_ok and self.wind_ok is not False

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a TurbineTestEnvironmentCheck has no truth value; read '.passes' "
            "or '.correction_ok' and '.wind_ok'"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw Figure A.3 with the 7 dB limit and this environment on it.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the curve of Figure A.3.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_turbine_environmental_correction

        check_language(language)
        return plot_turbine_environmental_correction(
            self.environmental_correction_db,
            self.ratio,
            passes=self.passes,
            ax=ax,
            language=language,
            **kwargs,
        )


def check_turbine_test_environment(
    correction: TurbineEnvironmentalCorrection | None = None,
    *,
    environmental_correction_db: float | None = None,
    wind_speed_m_s: float | None = None,
) -> TurbineTestEnvironmentCheck:
    r"""Is the test environment good enough for the standard (A.3.3, 4.3)?

    A room qualifies when its environmental correction does not exceed 7 dB,
    "K ≤ 7" (A.3.3), which the clause restates as :math:`A/S \ge 1`; the two
    agree to the whole decibel (the formula of Figure A.3 gives
    :math:`10 \lg 5 = 6{,}99` dB at :math:`A/S = 1`). Outdoors, and in very
    large or open workspaces, :math:`K` is taken as zero (A.4), and
    measurements outdoors need a wind speed below 6 m/s, with a windscreen
    above 1 m/s (4.3).

    :param correction: The environmental correction, from
        :func:`turbine_environmental_correction` or
        :func:`turbine_reference_source_correction`; or give
        ``environmental_correction_db`` instead.
    :param environmental_correction_db: :math:`K` in dB, when it was found
        some other way, ``0.0`` outdoors (A.4).
    :param wind_speed_m_s: The wind speed for a measurement outdoors, in
        metres per second; ``None`` indoors.
    :return: The conditions and the verdict.
    :raises ValueError: unless exactly one of ``correction`` and
        ``environmental_correction_db`` is given, for a non-finite correction
        or for a negative wind speed.
    """
    if (correction is None) == (environmental_correction_db is None):
        msg = (
            "check_turbine_test_environment: give 'correction' or "
            "'environmental_correction_db', one of the two."
        )
        raise ValueError(msg)
    if environmental_correction_db is not None:
        k = require_finite(environmental_correction_db, "environmental_correction_db")
        ratio = None
    elif isinstance(correction, TurbineEnvironmentalCorrection):
        k = correction.environmental_correction_db
        ratio = correction.ratio
    else:
        msg = (
            "check_turbine_test_environment: 'correction' must be a "
            "TurbineEnvironmentalCorrection; pass a bare K as "
            "'environmental_correction_db'."
        )
        raise ValueError(msg)
    wind_ok: bool | None = None
    advised = False
    wind: float | None = None
    if wind_speed_m_s is not None:
        wind = float(wind_speed_m_s)
        if not math.isfinite(wind) or wind < 0.0:
            msg = (
                "check_turbine_test_environment: 'wind_speed_m_s' must be non-negative."
            )
            raise ValueError(msg)
        wind_ok = wind < _WIND_LIMIT_M_S
        advised = wind > _WINDSCREEN_ABOVE_M_S
    return TurbineTestEnvironmentCheck(
        environmental_correction_db=k,
        ratio=ratio,
        correction_ok=_within_k_limit(k),
        wind_speed_m_s=wind,
        wind_ok=wind_ok,
        windscreen_advised=advised,
    )


# ---------------------------------------------------------------------------
# The surface sound pressure level and the sound power level (8.3, 8.4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TurbineSoundPowerResult:
    r"""A-weighted surface sound pressure level and sound power level (8.3, 8.4).

    Built by :func:`turbine_sound_power`.

    :ivar pressure_levels_db: :math:`L_{p\mathrm{A}i}` measured with the
        turbine set operating, one per position, in dB re 20 µPa.
    :ivar background_levels_db: The background level at each position, in
        dB, or ``None`` when it was not determined.
    :ivar background_corrections_db: The correction of Table 2 at each
        position, in dB (zero where no background was given).
    :ivar corrected_levels_db: The levels after 8.1, in dB.
    :ivar environmental_correction_db: :math:`K`, in dB.
    :ivar surface_area_m2: :math:`S`, in square metres.
    :ivar surface_pressure_level_db: :math:`\overline{L_{p\mathrm{A}}}` of
        Equation (2), :math:`K` subtracted, in dB re 20 µPa.
    :ivar sound_power_level_db: :math:`L_{W\mathrm{A}}` of Equation (3), in
        dB re 1 pW.
    :ivar overhead_mask: Which positions are overhead, or ``None``.
    """

    pressure_levels_db: np.ndarray
    background_levels_db: np.ndarray | None
    background_corrections_db: np.ndarray
    corrected_levels_db: np.ndarray
    environmental_correction_db: float
    surface_area_m2: float
    surface_pressure_level_db: float
    sound_power_level_db: float
    overhead_mask: np.ndarray | None = field(default=None)

    def __post_init__(self) -> None:
        """Refuse per-position arrays that disagree and values that are not finite.

        :raises ValueError: if a per-position array has another length than
            ``pressure_levels_db``, or a level, the correction or the area is
            not finite.
        """
        count = np.asarray(self.pressure_levels_db).shape
        for name in (
            "background_levels_db",
            "background_corrections_db",
            "corrected_levels_db",
            "overhead_mask",
        ):
            value = getattr(self, name)
            if value is not None and np.asarray(value).shape != count:
                msg = (
                    f"TurbineSoundPowerResult: '{name}' must have one entry per "
                    f"position ({count[0] if count else 0})."
                )
                raise ValueError(msg)
        require_finite_fields(
            self,
            "pressure_levels_db",
            "background_levels_db",
            "background_corrections_db",
            "corrected_levels_db",
            "environmental_correction_db",
            "surface_area_m2",
            "surface_pressure_level_db",
            "sound_power_level_db",
        )

    @property
    def level_differences_db(self) -> np.ndarray | None:
        """The level with the source operating less the background, per position."""
        if self.background_levels_db is None:
            return None
        difference = np.asarray(self.pressure_levels_db, dtype=np.float64) - np.asarray(
            self.background_levels_db, dtype=np.float64
        )
        return np.asarray(difference, dtype=np.float64)

    @property
    def limited_positions(self) -> np.ndarray | None:
        """Per position, whether its background was less than 3 dB below (4.2).

        :return: One boolean per position, ``True`` where the position makes
            the determination an upper limit, or ``None`` without a
            background.
        """
        differences = self.level_differences_db
        return None if differences is None else _below_criterion(differences)

    @property
    def upper_limit(self) -> bool:
        """Whether a position's background was less than 3 dB below (4.2).

        Then no valid measurement could be made, and the result is only an
        indication of the upper limit of the sound power level.
        """
        limited = self.limited_positions
        return limited is not None and bool(np.any(limited))

    @property
    def reported_sound_power_level_db(self) -> float:
        r""":math:`L_{W\mathrm{A}}` rounded to the nearest whole decibel (9.4 g)."""
        return float(_round_half_up(self.sound_power_level_db))

    @property
    def level_range_db(self) -> float:
        """The range of the corrected position levels, in dB."""
        levels = np.asarray(self.corrected_levels_db)
        return float(np.max(levels) - np.min(levels))

    @property
    def arithmetic_mean_db(self) -> float:
        """The plain average of the corrected position levels, :math:`K` subtracted.

        The NOTE of 8.3 allows it in place of Equation (2) when
        :attr:`level_range_db` does not exceed 5 dB, and says it "should not
        differ by more than 0,7 dB" from Equation (2). It is never above the
        energy average, and within a 5 dB range it trails it by at most
        0,707 dB (two levels 5 dB apart, the louder at 41 % of the positions),
        the NOTE's 0,7 dB to its one decimal.
        """
        return (
            float(np.mean(self.corrected_levels_db)) - self.environmental_correction_db
        )

    @property
    def arithmetic_mean_allowed(self) -> bool:
        """Whether the range of the position levels is within 5 dB (NOTE of 8.3)."""
        return self.level_range_db <= _ARITHMETIC_RANGE_DB + _BOUNDARY_SLACK_DB

    @property
    def overhead_effect_db(self) -> float | None:
        r"""How much the overhead positions move :math:`L_{W\mathrm{A}}`, in dB.

        The sound power level from every position less the one without the
        overhead positions, on the same surface. The NOTE of 7.2.2 lets the
        overhead positions be deleted when this is within 1,0 dB. ``None``
        without an overhead mask, or when every position or none is overhead.
        """
        if self.overhead_mask is None:
            return None
        mask = np.asarray(self.overhead_mask, dtype=bool)
        if not np.any(mask) or np.all(mask):
            return None
        without = energy_mean(np.asarray(self.corrected_levels_db)[~mask])
        with_all = energy_mean(np.asarray(self.corrected_levels_db))
        return float(with_all - without)

    @property
    def overhead_may_be_deleted(self) -> bool | None:
        """Whether the overhead positions move the level by no more than 1,0 dB."""
        effect = self.overhead_effect_db
        if effect is None:
            return None
        return abs(effect) <= _OVERHEAD_EFFECT_LIMIT_DB + _BOUNDARY_SLACK_DB

    @property
    def conforms(self) -> bool:
        """Whether the determination is in full conformity with the standard.

        Every background at least 3 dB below (4.2) and :math:`K` within 7 dB
        (8.3). Only such a determination can carry the statement of clause 10.
        """
        return not self.upper_limit and _within_k_limit(
            self.environmental_correction_db
        )

    def plot(
        self,
        ax: Axes | None = None,
        *,
        position_labels: Sequence[str] | None = None,
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        """Draw the corrected level at each position with the surface level.

        The bars stand in the order the levels were given. Pass the
        :attr:`TurbineMicrophoneArray.labels` of the array they were measured
        on and the axis names the key positions as Figure 2 numbers them;
        without them it counts the bars from 1.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param position_labels: One label per position, ``"1"`` to ``"5"`` for
            the key positions and ``""`` for the others, or ``None``.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the bars of the corrected levels.
        :return: The axes.
        :raises ValueError: if ``position_labels`` does not have one entry per
            position.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_turbine_sound_power

        check_language(language)
        return plot_turbine_sound_power(
            self, ax=ax, position_labels=position_labels, language=language, **kwargs
        )


def turbine_sound_power(
    pressure_levels_db: ArrayLike,
    *,
    surface_area_m2: float,
    background_levels_db: ArrayLike | None,
    environmental_correction_db: float,
    overhead_mask: ArrayLike | None = None,
) -> TurbineSoundPowerResult:
    r"""Surface sound pressure level and sound power level of a turbine set (8.1 to 8.4).

    Each position's level is first corrected for the background by Table 2
    (8.1, :func:`turbine_background_correction`); the corrected levels are
    energy-averaged and the environmental correction subtracted, Equation (2),

    .. math::

       \overline{L_{p\mathrm{A}}} = 10 \lg\left[\frac{1}{N}
           \sum_{i=1}^{N} 10^{0.1 L_{p\mathrm{A}i}}\right] - K,

    and the surface term closes it, Equation (3),
    :math:`L_{W\mathrm{A}} = \overline{L_{p\mathrm{A}}} + 10 \lg(S/S_0)`.

    A background less than 3 dB below at any position makes the result an
    upper limit (4.2) and a :math:`K` above 7 dB puts the room outside the
    standard (8.3); both emit a :class:`~phonometry.emission.SoundPowerWarning`
    and leave :attr:`TurbineSoundPowerResult.conforms` ``False``.

    :param pressure_levels_db: :math:`L_{p\mathrm{A}i}` with the turbine set
        operating, one per position, in dB re 20 µPa: at least the four key
        positions that remain once the overhead one is deleted.
    :param surface_area_m2: :math:`S`, from :func:`turbine_measurement_surface`,
        in square metres.
    :param background_levels_db: The A-weighted background level at each
        position, in dB. It is often impossible to measure with the turbine
        stopped, and NOTE 1 of 8.1 allows it to be evaluated by computation
        instead. ``None`` states that no background was determined, and no
        correction is applied.
    :param environmental_correction_db: :math:`K`, in dB: from
        :func:`turbine_environmental_correction` or
        :func:`turbine_reference_source_correction`, or ``0.0`` outdoors
        (A.4).
    :param overhead_mask: Which positions are overhead
        (:attr:`TurbineMicrophoneArray.overhead_mask`), for the effect of
        deleting them (NOTE of 7.2.2); ``None`` if not needed.
    :return: The per-position levels, the surface level and the sound power
        level.
    :raises ValueError: for fewer than four positions, arrays of different
        lengths or non-finite values.
    """
    levels = require_finite_array(pressure_levels_db, "pressure_levels_db")
    if levels.ndim != 1 or levels.size < _MIN_POSITIONS:
        msg = (
            "turbine_sound_power: 'pressure_levels_db' must hold one level per "
            f"position, at least {_MIN_POSITIONS} (the key positions of Figure 2 "
            f"less the overhead one); got shape {levels.shape}."
        )
        raise ValueError(msg)
    area = require_positive(surface_area_m2, "surface_area_m2")
    k = require_finite(environmental_correction_db, "environmental_correction_db")
    background: np.ndarray | None = None
    corrections = np.zeros_like(levels)
    if background_levels_db is not None:
        background = require_finite_array(background_levels_db, "background_levels_db")
        if background.shape != levels.shape:
            msg = (
                "turbine_sound_power: 'background_levels_db' must have one level "
                f"per position ({levels.size}); got shape {background.shape}."
            )
            raise ValueError(msg)
        corrections = np.asarray(turbine_background_correction(levels - background))
        if np.any(_below_criterion(levels - background)):
            warnings.warn(
                "The background is less than 3 dB below the level with the turbine "
                "set operating at one or more positions; no valid measurement can "
                "be made and the result is only an upper limit (IEC 61063, 4.2).",
                SoundPowerWarning,
                stacklevel=2,
            )
    mask: np.ndarray | None = None
    if overhead_mask is not None:
        mask = np.asarray(overhead_mask, dtype=bool)
        if mask.shape != levels.shape:
            msg = (
                "turbine_sound_power: 'overhead_mask' must have one entry per "
                f"position ({levels.size}); got shape {mask.shape}."
            )
            raise ValueError(msg)
        mask = read_only(mask.copy())
    if not _within_k_limit(k):
        warnings.warn(
            f"An environmental correction of {k:.1f} dB exceeds the 7 dB "
            "IEC 61063 allows (8.3, A.3.3); the room cannot be used for "
            "measurements to the standard.",
            SoundPowerWarning,
            stacklevel=2,
        )
    corrected = levels - corrections
    surface_level = energy_mean(corrected) - k
    power = surface_level + 10.0 * math.log10(area / _S0)
    return TurbineSoundPowerResult(
        pressure_levels_db=read_only(levels.copy()),
        background_levels_db=None
        if background is None
        else read_only(background.copy()),
        background_corrections_db=read_only(corrections),
        corrected_levels_db=read_only(corrected),
        environmental_correction_db=k,
        surface_area_m2=area,
        surface_pressure_level_db=float(surface_level),
        sound_power_level_db=float(power),
        overhead_mask=mask,
    )


# ---------------------------------------------------------------------------
# The report (clauses 9 and 10, Table 1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TurbineNoiseDeclaration:
    """The minimum report of clause 10, one row per operating condition.

    Built by :func:`turbine_noise_declaration`.

    :ivar turbine: Description of the turbine set under test, clause 10 a).
    :ivar noise_control: The noise control screens and enclosures fitted,
        clause 10 a) (and 1.1.5).
    :ivar measured_at: Date and time of the measurements, clause 10 f).
    :ivar tonal: Whether the sound contains prominent discrete tones, which
        selects the row of Table 1.
    :ivar operating_conditions: The operating conditions, clause 10 b).
    :ivar position_levels_db: The A-weighted levels at each position,
        corrected for the background, per condition, clause 10 c).
    :ivar surface_pressure_levels_db: The A-weighted surface sound pressure
        level per condition, clause 10 d), in dB re 20 µPa.
    :ivar sound_power_levels_db: The A-weighted sound power level per
        condition as determined by Equation (3), in dB re 1 pW; clause 10 e)
        reports it as :attr:`reported_sound_power_levels_db`.
    """

    turbine: str
    noise_control: str
    measured_at: str
    tonal: bool
    operating_conditions: tuple[str, ...]
    position_levels_db: tuple[np.ndarray, ...]
    surface_pressure_levels_db: tuple[float, ...]
    sound_power_levels_db: tuple[float, ...]

    def __post_init__(self) -> None:
        """Refuse a report whose rows disagree in number.

        :raises ValueError: if the per-condition tuples do not have one entry
            per operating condition, or there is none.
        """
        count = len(self.operating_conditions)
        if count == 0:
            msg = "TurbineNoiseDeclaration: at least one operating condition is needed."
            raise ValueError(msg)
        for name in (
            "position_levels_db",
            "surface_pressure_levels_db",
            "sound_power_levels_db",
        ):
            if len(getattr(self, name)) != count:
                msg = (
                    f"TurbineNoiseDeclaration: '{name}' must have one entry per "
                    f"operating condition ({count})."
                )
                raise ValueError(msg)
        require_finite_fields(
            self, "surface_pressure_levels_db", "sound_power_levels_db"
        )

    @property
    def statement(self) -> str:
        """The statement clause 10 requires the report to contain."""
        return _CONFORMITY_STATEMENT

    @property
    def standard_deviation_db(self) -> float:
        """The standard deviation of Table 1 for this kind of sound, in dB.

        5 dB for a source with prominent discrete tones, 4 dB for a
        broadband one: the uncertainty measurements to the survey method tend
        to stay within (1.2).
        """
        return _TABLE_1[self.tonal]

    @property
    def reported_sound_power_levels_db(self) -> tuple[float, ...]:
        """The sound power levels rounded to the nearest whole decibel (9.4 g).

        What clause 10 e) reports, in dB re 1 pW, one per operating condition.
        """
        return tuple(
            float(_round_half_up(level)) for level in self.sound_power_levels_db
        )

    @property
    def loudest_condition(self) -> str:
        """The operating condition with the highest sound power level (6.2).

        Found on the levels before the rounding of 9.4 g, so two conditions
        that report the same whole decibel are still told apart; on an exact
        tie it is the first condition listed.
        """
        index = int(np.argmax(self.sound_power_levels_db))
        return self.operating_conditions[index]

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the sound power level of each operating condition.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the bars.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_turbine_noise_declaration

        check_language(language)
        return plot_turbine_noise_declaration(self, ax=ax, language=language, **kwargs)


def turbine_noise_declaration(
    determinations: Mapping[str, TurbineSoundPowerResult],
    *,
    turbine: str,
    noise_control: str,
    measured_at: str,
    tonal: bool,
) -> TurbineNoiseDeclaration:
    """The minimum report of clause 10 for one or more operating conditions.

    Clause 10 asks the report to state that the A-weighted sound power level
    "has been obtained in full conformity with the procedures of this
    standard" and is expressed in decibels above 1 pW, and to give at least:
    a) the turbine, with its noise control screens and enclosures; b) the
    operating conditions; c) the A-weighted levels at each position, corrected
    for the background; d) the A-weighted surface sound pressure level(s);
    e) the A-weighted sound power level(s); f) the date and time of the
    measurements. 6.2 suggests repeating the measurement under every typical
    sustained load, 25 %, 50 %, 75 % and 100 % of the rated load, to find the
    noisiest, so a report may carry several conditions. The report keeps each
    sound power level as determined, finds the noisiest condition on it, and
    rounds it to the nearest whole decibel where it is reported (9.4 g).

    A determination that is not in full conformity (an upper limit, or a
    :math:`K` above 7 dB) cannot carry the statement, and is refused.

    :param determinations: One :class:`TurbineSoundPowerResult` per operating
        condition, keyed by its description (``"100 % rated load"``).
    :param turbine: Description of the turbine set, clause 10 a).
    :param noise_control: The noise control screens and enclosures fitted, or
        ``"none"``, clause 10 a).
    :param measured_at: Date and time of the measurements, clause 10 f).
    :param tonal: Whether the sound contains prominent discrete tones (Table
        1).
    :return: The report.
    :raises ValueError: for no determination, a determination that does not
        conform, or an empty description.
    """
    if not determinations:
        msg = "turbine_noise_declaration: at least one determination is needed."
        raise ValueError(msg)
    for name, text in (
        ("turbine", turbine),
        ("noise_control", noise_control),
        ("measured_at", measured_at),
    ):
        if not isinstance(text, str) or not text.strip():
            msg = (
                f"turbine_noise_declaration: '{name}' must be a non-empty description."
            )
            raise ValueError(msg)
    conditions: list[str] = []
    levels: list[np.ndarray] = []
    surface: list[float] = []
    power: list[float] = []
    for condition, result in determinations.items():
        if not isinstance(result, TurbineSoundPowerResult):
            msg = (
                f"turbine_noise_declaration: the determination for {condition!r} "
                "must be a TurbineSoundPowerResult."
            )
            raise ValueError(msg)
        if not result.conforms:
            reason = (
                "its background is less than 3 dB below at some position (4.2)"
                if result.upper_limit
                else "its environmental correction exceeds 7 dB (8.3)"
            )
            msg = (
                f"turbine_noise_declaration: the determination for {condition!r} is "
                f"not in full conformity with IEC 61063: {reason}."
            )
            raise ValueError(msg)
        conditions.append(str(condition))
        levels.append(read_only(np.array(result.corrected_levels_db, dtype=np.float64)))
        surface.append(result.surface_pressure_level_db)
        power.append(result.sound_power_level_db)
    return TurbineNoiseDeclaration(
        turbine=turbine,
        noise_control=noise_control,
        measured_at=measured_at,
        tonal=bool(tonal),
        operating_conditions=tuple(conditions),
        position_levels_db=tuple(levels),
        surface_pressure_levels_db=tuple(surface),
        sound_power_levels_db=tuple(power),
    )
