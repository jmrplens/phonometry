#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What a barrier by the road is worth, measured (ISO 10847:1997).

:mod:`phonometry.environment.propagation.ground_barriers` predicts what a
barrier will do from its geometry. This is the measurement, and its scope
paragraph is worth reading before the equations:

    It does not make it possible to compare insertion loss values of an
    equivalent barrier on a different site.

An insertion loss measured here belongs to that barrier, on that site, under
those meteorological conditions. What it may be used for is comparing
different barriers on the **same** site by the direct method, and what it is
not for is a product specification. The intrinsic quantities, the sound
reduction index and the absorption coefficient, are outside the scope
altogether.

Two methods, one subtraction
----------------------------

The quantity is the level at a receiver position before the barrier existed
less the level after, with everything else unchanged. Nothing else is
unchanged, of course, so the standard puts a second microphone at a
**reference position** where the barrier does not reach, and normalises by
what it heard:

.. math::

   D_{IL} = \left(L_{\text{ref},A} - L_{\text{ref},B}\right)
          - \left(L_{r,A} - L_{r,B}\right)

That is the **direct method**, 8.2.1, and it needs a barrier that has not been
built yet or can be taken down. Where it cannot, the **indirect method** of
8.2.2 measures the "before" pair at a substitute site judged equivalent, and
adds a correction for the kind of receiver position: 0 dB in a hemi free
field, 6 dB against a facade, which is the pressure doubling at a large hard
surface.

The algebra of the two is the same whenever the receiver is of the same kind
in both campaigns, which is what the NOTE to 8.2.2 recommends, and
:func:`measured_insertion_loss_indirect` reduces to
:func:`measured_insertion_loss_direct` exactly there.

What the standard will not let you correct
------------------------------------------

Three times over. 6.3.2: "no attempt shall be made to adjust measured sound
pressure levels based on the temperature data". 6.3.3: the same for humidity.
The remedy for both is equivalence rather than arithmetic, and the clauses
say what equivalence means: the same wind class and vector components within
2 m/s, average temperatures within 10 °C, the same cloud cover class, and no
measurement at all above 5 m/s of wind.

The background is the one correction it does allow, from a **stepped table**
of two rows, and the table is not the one ISO 11820 prints and not the formula
ISO 11821 prints. Three standards on the same subject, three different rules;
they are three separate implementations here and share nothing.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from ..._internal.validation import (
    require_choice,
    require_finite,
    require_finite_array,
    require_positive,
    require_positive_array,
)
from ..._internal.warnings import PhonometryWarning

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "ISO10847_BACKGROUND_CORRECTIONS_DB",
    "CLOSE_SOURCE_DISTANCE_M",
    "CLOUD_COVER_CLASSES",
    "EQUIVALENT_SECTOR_DEG",
    "EQUIVALENT_SURROUNDINGS_RADIUS_M",
    "HEMI_FREE_FIELD_DISTANCE_FACTOR",
    "HEMI_FREE_FIELD_DISTANCE_M",
    "LINE_SOURCE_DIVERGENCE_DB",
    "LONG_DISTANCE_M",
    "MAXIMUM_WIND_SPEED_M_S",
    "ISO10847_MINIMUM_BACKGROUND_MARGIN_DB",
    "MINIMUM_RECEIVER_HEIGHT_M",
    "MINIMUM_REPETITIONS",
    "ISO10847_OCTAVE_BAND_EXTENDED_RANGE_HZ",
    "ISO10847_OCTAVE_BAND_RANGE_HZ",
    "POINT_SOURCE_DIVERGENCE_DB",
    "ISO10847_PREFERRED_BACKGROUND_MARGIN_DB",
    "RECEIVER_CORRECTIONS_DB",
    "REFERENCE_ELEVATION_INCREMENT_DEG",
    "REFERENCE_MICROPHONE_CLEARANCE_M",
    "SHORT_DISTANCE_RATIO",
    "TEMPERATURE_TOLERANCE_C",
    "ISO10847_THIRD_OCTAVE_BAND_EXTENDED_RANGE_HZ",
    "ISO10847_THIRD_OCTAVE_BAND_RANGE_HZ",
    "WIND_CLASSES",
    "WIND_VECTOR_TOLERANCE_M_S",
    "BarrierInSituWarning",
    "MeasuredBarrierInsertionLoss",
    "barrier_background_correction_db",
    "hemi_free_field_distance_m",
    "is_short_distance",
    "measured_insertion_loss_direct",
    "measured_insertion_loss_indirect",
    "reference_microphone_height_m",
    "wind_class",
]

#: Table 3 (6.4): the correction to **add** to the measured level, in
#: decibels, keyed by the difference between the level with the source and the
#: level without it. The column reads "correction to be made to", so the
#: printed values are negative and are added rather than subtracted; the table
#: of ISO 11820 reads the other way round and the two must not share a helper.
ISO10847_BACKGROUND_CORRECTIONS_DB: Mapping[int, float] = MappingProxyType(
    {
        4: -2.0,
        5: -2.0,
        6: -1.0,
        7: -1.0,
        8: -1.0,
        9: -1.0,
    }
)

#: 6.4: under this margin the results are not valid, and this is the margin
#: the clause would rather have.
ISO10847_MINIMUM_BACKGROUND_MARGIN_DB: float = 4.0
ISO10847_PREFERRED_BACKGROUND_MARGIN_DB: float = 10.0

#: Table 1: the wind classes and the vector component of the wind velocity,
#: in metres per second, that each covers. The upwind class exists only over
#: short distances. Its printed interval is "+ 1 to - 5"; read as "- 1 to
#: - 5", because the two rows above it are "+ 1 to + 5" and "- 1 to + 1" and
#: an upwind class starting at +1 m/s would sit inside the downwind one (see
#: the errata).
WIND_CLASSES: Mapping[str, Mapping[str, tuple[float, float]]] = MappingProxyType(
    {
        "all": MappingProxyType(
            {
                "downwind": (1.0, 5.0),
                "calm": (-1.0, 1.0),
            }
        ),
        "short": MappingProxyType(
            {
                "downwind": (1.0, 5.0),
                "calm": (-1.0, 1.0),
                "upwind": (-5.0, -1.0),
            }
        ),
    }
)

#: 6.3.1: no measurement is made above this average wind velocity, in metres
#: per second, whatever its direction.
MAXIMUM_WIND_SPEED_M_S: float = 5.0

#: 6.3.1: the vector components of the average wind velocity may not differ by
#: more than this between the two campaigns, in metres per second.
WIND_VECTOR_TOLERANCE_M_S: float = 2.0

#: 6.3.1: the ratio above which the geometry counts as a short distance, so
#: that the upwind class of Table 1 becomes available.
SHORT_DISTANCE_RATIO: float = 0.1

#: 6.3.2: the two campaigns are made with average temperatures within this
#: many degrees Celsius of each other. No level is adjusted for the
#: difference.
TEMPERATURE_TOLERANCE_C: float = 10.0

#: Table 2 (6.3.4): the four classes of cloud cover, as the table describes
#: them. The two campaigns are made in the same class.
CLOUD_COVER_CLASSES: Mapping[int, str] = MappingProxyType(
    {
        1: (
            "heavily overcast day or night, 80 % cloud cover or more for 100 % of "
            "the measurement time"
        ),
        2: (
            "moderately overcast day or night, 50 % to 80 % cloud cover for at "
            "least 80 % of the measurement time"
        ),
        3: (
            "lightly overcast or sunny day or night, either continuous sun or "
            "less than 50 % cloud cover for at least 80 % of the measurement time"
        ),
        4: "clear night",
    }
)

#: 6.2: the terrain, the obstructions and the ground of a substitute site
#: match the real one inside this sector, in degrees on either side of the
#: line from the receiver towards the source.
EQUIVALENT_SECTOR_DEG: float = 60.0

#: 6.2: and inside this radius, in metres, behind and to the side of the major
#: receiver positions.
EQUIVALENT_SURROUNDINGS_RADIUS_M: float = 30.0

#: 7.2.2: the reference microphone stands at least this far above the top edge
#: of the barrier, in metres.
REFERENCE_MICROPHONE_CLEARANCE_M: float = 1.5

#: 7.2.2 NOTE: where the near end of the source region is closer than this to
#: the barrier, in metres, the reference microphone may be raised further,
#: until its elevation angle exceeds the barrier's by
#: :data:`REFERENCE_ELEVATION_INCREMENT_DEG`. It is never lowered under
#: :data:`REFERENCE_MICROPHONE_CLEARANCE_M` to get there.
CLOSE_SOURCE_DISTANCE_M: float = 15.0
REFERENCE_ELEVATION_INCREMENT_DEG: float = 10.0

#: 8.1.2 a): a receiver stands in a hemi free field while it is this far from
#: any vertical reflecting surface, in metres, or this many times its own
#: distance to the barrier, whichever is shorter.
HEMI_FREE_FIELD_DISTANCE_M: float = 30.0
HEMI_FREE_FIELD_DISTANCE_FACTOR: float = 2.0

#: 8.1.2 NOTE: the least height of a receiver position, in metres.
MINIMUM_RECEIVER_HEIGHT_M: float = 1.2

#: 8.2.2: the correction for the kind of receiver position, in decibels. The
#: 6 dB is the pressure doubling at a large hard surface.
RECEIVER_CORRECTIONS_DB: Mapping[str, float] = MappingProxyType(
    {
        "hemi_free_field": 0.0,
        "reflecting_surface": 6.0,
    }
)

#: 8.1.4: the fewest repetitions, and the source-receiver distance in metres
#: past which more may be needed.
MINIMUM_REPETITIONS: int = 3
LONG_DISTANCE_M: float = 250.0

#: 8.1.3: the band range the measurement covers, and the extension it
#: recommends where higher frequencies matter.
ISO10847_OCTAVE_BAND_RANGE_HZ: tuple[float, float] = (63.0, 4000.0)
ISO10847_OCTAVE_BAND_EXTENDED_RANGE_HZ: tuple[float, float] = (63.0, 8000.0)
ISO10847_THIRD_OCTAVE_BAND_RANGE_HZ: tuple[float, float] = (50.0, 5000.0)
ISO10847_THIRD_OCTAVE_BAND_EXTENDED_RANGE_HZ: tuple[float, float] = (50.0, 10000.0)

#: Definition 3.10: in the far field a point source falls this much per
#: doubling of distance, and an incoherent line source this much, both without
#: ground attenuation.
POINT_SOURCE_DIVERGENCE_DB: float = 6.0
LINE_SOURCE_DIVERGENCE_DB: float = 3.0

ReceiverType = Literal["hemi_free_field", "reflecting_surface"]
_RECEIVER_TYPES: tuple[str, ...] = ("hemi_free_field", "reflecting_surface")


class BarrierInSituWarning(PhonometryWarning):
    """The measurement is outside a condition ISO 10847 states."""


def barrier_background_correction_db(
    level_difference_db: ArrayLike,
) -> NDArray[np.float64]:
    r"""The background correction of Table 3, in decibels to add.

    The table has two rows and no formula: 2 dB comes off at a margin of 4 or
    5 dB, 1 dB at 6, 7, 8 or 9, and nothing at 10 or more, which is the margin
    6.4 asks for in the first place. Under 4 dB "the measurement results are
    not valid", and that is a refusal.

    The sign is the trap. This column reads "correction to be **made to** the
    measured sound pressure level", so its values are printed negative and are
    **added**; Table 1 of ISO 11820 reads "correction to be **subtracted**"
    and prints the same physical thing positive. The two tables also disagree
    numerically at a margin of 9 dB, where ISO 11820 takes off 0,5 dB and this
    one takes off 1. They are two tables and they stay two tables.

    :param level_difference_db: The difference between the level measured with
        the source and the level without it, in decibels.
    :return: The correction to add, in decibels, which is zero or negative.
    :raises ValueError: For a margin under
        :data:`ISO10847_MINIMUM_BACKGROUND_MARGIN_DB`, which 6.4 calls invalid.
    """
    margin = require_finite_array(level_difference_db, "level_difference_db")
    if float(np.min(margin)) < ISO10847_MINIMUM_BACKGROUND_MARGIN_DB:
        msg = (
            f"ISO 10847 6.4 calls the results invalid under "
            f"{ISO10847_MINIMUM_BACKGROUND_MARGIN_DB:g} dB over the background; the "
            f"smallest margin is {float(np.min(margin)):.1f} dB."
        )
        raise ValueError(msg)
    rows = np.floor(margin).astype(int)
    highest = max(ISO10847_BACKGROUND_CORRECTIONS_DB)
    return np.asarray(
        [
            0.0 if row > highest else ISO10847_BACKGROUND_CORRECTIONS_DB[row]
            for row in rows.tolist()
        ],
        dtype=np.float64,
    )


def is_short_distance(
    *,
    source_height_m: float,
    receiver_height_m: float,
    barrier_height_m: float,
    source_to_barrier_m: float,
    barrier_to_receiver_m: float,
) -> tuple[bool, bool]:
    r"""Whether the geometry counts as a short distance, 6.3.1.

    The clause prints one condition for the "before" campaign and two for the
    "after" one, all against the same ratio of 0,1:

    .. math::

       \frac{H_s + H_R}{d_1 + d_2} > 0,1, \qquad
       \frac{H_s + H}{d_1} > 0,1, \qquad
       \frac{H + H_R}{d_2} > 0,1

    The "after" pair must both hold. What hangs on the answer is Table 1: the
    upwind class exists only over short distances, so a long-distance
    measurement may be made downwind or calm and not into the wind at all.

    The inequalities are strict, so a ratio of exactly 0,1 is not a short
    distance.

    :param source_height_m: :math:`H_s`, in metres.
    :param receiver_height_m: :math:`H_R`, in metres.
    :param barrier_height_m: :math:`H`, in metres.
    :param source_to_barrier_m: :math:`d_1`, in metres.
    :param barrier_to_receiver_m: :math:`d_2`, in metres.
    :return: Whether the "before" and the "after" geometry each count as a
        short distance.
    :raises ValueError: For a non-positive height or distance.
    """
    source = require_positive(source_height_m, "source_height_m")
    receiver = require_positive(receiver_height_m, "receiver_height_m")
    barrier = require_positive(barrier_height_m, "barrier_height_m")
    first = require_positive(source_to_barrier_m, "source_to_barrier_m")
    second = require_positive(barrier_to_receiver_m, "barrier_to_receiver_m")
    before = (source + receiver) / (first + second) > SHORT_DISTANCE_RATIO
    after = ((source + barrier) / first > SHORT_DISTANCE_RATIO) and (
        (barrier + receiver) / second > SHORT_DISTANCE_RATIO
    )
    return before, after


def wind_class(
    vector_component_m_s: float, *, short_distance: bool = False
) -> str | None:
    r"""The wind class of Table 1, from the vector component of the velocity.

    The component is the projection of the average wind velocity on the line
    from the source to the receiver, in metres per second: positive downwind,
    negative upwind. Over all distances the table has a downwind class and a
    calm one; over short distances it adds an upwind class, whose interval is
    printed "+ 1 to - 5" and read here as -1 to -5 (see the errata).

    The calm class carries a footnote of its own over all distances: it counts
    "only with the case of temperature inversion".

    Above :data:`MAXIMUM_WIND_SPEED_M_S` in absolute value no measurement is
    made at all, which is a refusal rather than a class.

    :param vector_component_m_s: The vector component, in metres per second.
    :param short_distance: Whether the geometry is a short distance in the
        sense of :func:`is_short_distance`.
    :return: The class name, or ``None`` where the component falls in no class
        the table prints, which over long distances is any upwind component.
    :raises ValueError: For a component that is not finite, or past
        :data:`MAXIMUM_WIND_SPEED_M_S` in absolute value.
    """
    component = require_finite(vector_component_m_s, "vector_component_m_s")
    if abs(component) > MAXIMUM_WIND_SPEED_M_S:
        msg = (
            f"ISO 10847 6.3.1 makes no measurement above "
            f"{MAXIMUM_WIND_SPEED_M_S:g} m/s whatever the direction; the "
            f"component is {component:g} m/s."
        )
        raise ValueError(msg)
    table = WIND_CLASSES["short" if short_distance else "all"]
    for name, (low, high) in table.items():
        if low <= component <= high:
            return name
    return None


def reference_microphone_height_m(
    barrier_height_m: float, *, source_to_barrier_m: float | None = None
) -> float:
    r"""How high the reference microphone stands, 7.2.2.

    At least :data:`REFERENCE_MICROPHONE_CLEARANCE_M` above the top edge of
    the barrier, on a vertical plane through it, so that what it hears is the
    source and not the barrier. For a barrier whose top is not a straight
    edge, a berm or a cupped profile, the clearance is measured from its
    highest point. The clause words the clearance with "shall" (printed folio
    9, PDF page 13), and no geometry takes the microphone under it.

    The NOTE adds a preference for a source that stands close. Where the near
    end of the source region is under :data:`CLOSE_SOURCE_DISTANCE_M` from
    the barrier, the microphone "may be raised as high as possible" until the
    elevation angle from that end exceeds the angle to the barrier top by
    :data:`REFERENCE_ELEVATION_INCREMENT_DEG`:

    .. math::

       h = \max\left(H + 1{,}5\ \mathrm{m},\;
       d \tan\left(\arctan\frac{H}{d} + 10^\circ\right)\right)

    The NOTE only ever raises the microphone, so the height is the higher of
    the two. Which one governs depends on the geometry: a 4 m barrier 10 m
    from the source takes the angle, 6,20 m against 5,5 m, while a 3 m barrier
    5 m from the source takes the clearance, because its 10 degrees are
    reached at 4,34 m and the clause asks for 4,5 m. The angle form is the
    NOTE's own words; the height it implies is derived here rather than
    printed.

    Once the barrier top stands 80 degrees or more above the near end of the
    source region, no height reaches the increment at all, and the tangent
    would turn negative. The microphone then keeps the clearance and a
    :class:`BarrierInSituWarning` says that the NOTE could not be followed.
    That is how this module treats a NOTE, as with the one to 8.2.2: a
    preference it cannot meet is reported, and the clause it hangs from is
    enforced.

    :param barrier_height_m: :math:`H`, the barrier height above the ground at
        the microphone, in metres.
    :param source_to_barrier_m: :math:`d`, the distance from the near end of
        the source region to the barrier, in metres. Omit it for the plain
        clearance rule.
    :return: The microphone height above the ground, in metres.
    :raises ValueError: For a non-positive height or distance.
    """
    barrier = require_positive(barrier_height_m, "barrier_height_m")
    clearance = barrier + REFERENCE_MICROPHONE_CLEARANCE_M
    if source_to_barrier_m is None:
        return clearance
    distance = require_positive(source_to_barrier_m, "source_to_barrier_m")
    if distance >= CLOSE_SOURCE_DISTANCE_M:
        return clearance
    to_the_top = math.atan(barrier / distance)
    elevation = to_the_top + math.radians(REFERENCE_ELEVATION_INCREMENT_DEG)
    if elevation >= math.pi / 2.0:
        msg = (
            "The NOTE to ISO 10847 7.2.2 raises the reference microphone "
            f"{REFERENCE_ELEVATION_INCREMENT_DEG:g} degrees above the barrier "
            f"top, but that top already stands {math.degrees(to_the_top):.1f} "
            "degrees above the near end of the source region, so no height "
            "reaches it; the microphone keeps the "
            f"{REFERENCE_MICROPHONE_CLEARANCE_M:g} m clearance of 7.2.2."
        )
        warnings.warn(msg, BarrierInSituWarning, stacklevel=2)
        return clearance
    return max(clearance, distance * math.tan(elevation))


def hemi_free_field_distance_m(barrier_to_receiver_m: float) -> float:
    r"""How far a receiver stands from a reflecting surface, 8.1.2 a).

    :math:`\min(30\ \text{m}, 2 d)` with :math:`d` the distance from the
    barrier to the receiver: the clause says 30 m "or twice the
    barrier-receiver distance, **whichever is shorter**", so a receiver close
    behind the barrier needs less clearance rather than more. The two rules
    cross at 15 m.

    :param barrier_to_receiver_m: :math:`d`, in metres.
    :return: The least distance to any vertical reflecting surface, in metres.
    :raises ValueError: For a non-positive distance.
    """
    distance = require_positive(barrier_to_receiver_m, "barrier_to_receiver_m")
    return min(HEMI_FREE_FIELD_DISTANCE_M, HEMI_FREE_FIELD_DISTANCE_FACTOR * distance)


@dataclass(frozen=True)
class MeasuredBarrierInsertionLoss:
    r"""The insertion loss of a barrier as measured, ISO 10847 clause 8.2.

    :ivar frequencies: Nominal band centres, in hertz, or ``None`` where the
        measurement is an A-weighted level.
    :ivar reference_before_db: :math:`L_{\text{ref},B}` per band.
    :ivar reference_after_db: :math:`L_{\text{ref},A}` per band.
    :ivar receiver_before_db: :math:`L_{r,B}` per band.
    :ivar receiver_after_db: :math:`L_{r,A}` per band.
    :ivar insertion_loss_db: :math:`D_{IL}` or :math:`D'_{IL}` per band, in
        decibels.
    :ivar method: ``"direct"`` or ``"indirect"``.
    :ivar receiver_correction_before_db: :math:`C_r`, in decibels, zero for
        the direct method.
    :ivar receiver_correction_after_db: :math:`C'_r`, in decibels, zero for
        the direct method.
    """

    frequencies: NDArray[np.float64] | None
    reference_before_db: NDArray[np.float64]
    reference_after_db: NDArray[np.float64]
    receiver_before_db: NDArray[np.float64]
    receiver_after_db: NDArray[np.float64]
    insertion_loss_db: NDArray[np.float64]
    method: str
    receiver_correction_before_db: float
    receiver_correction_after_db: float

    @property
    def symbol(self) -> str:
        """The symbol clause 8.2 reports this as, ``"D_IL"`` or ``"D'_IL"``."""
        return "D_IL" if self.method == "direct" else "D'_IL"

    def rounded(self) -> NDArray[np.int_]:
        """The values as clause 10 c) reports them, to the nearest decibel."""
        return np.asarray(np.rint(self.insertion_loss_db), dtype=np.int_)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the four levels and the insertion loss they give.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.environment.plot_barrier_in_situ`.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_barrier_in_situ

        check_language(language)
        return plot_barrier_in_situ(self, ax=ax, language=language, **kwargs)


def _four_levels(
    reference_before_db: ArrayLike,
    reference_after_db: ArrayLike,
    receiver_before_db: ArrayLike,
    receiver_after_db: ArrayLike,
    frequencies: ArrayLike | None,
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64] | None,
]:
    """The four spectra and their band centres, checked against each other."""
    names = (
        "reference_before_db",
        "reference_after_db",
        "receiver_before_db",
        "receiver_after_db",
    )
    values = [
        require_finite_array(data, name)
        for data, name in zip(
            (
                reference_before_db,
                reference_after_db,
                receiver_before_db,
                receiver_after_db,
            ),
            names,
            strict=True,
        )
    ]
    if len({value.shape for value in values}) != 1:
        msg = "The four level arrays must match band for band."
        raise ValueError(msg)
    freqs: NDArray[np.float64] | None = None
    if frequencies is not None:
        freqs = require_positive_array(frequencies, "frequencies")
        if freqs.shape != values[0].shape:
            msg = "'frequencies' must match the levels band for band."
            raise ValueError(msg)
    return values[0], values[1], values[2], values[3], freqs


def measured_insertion_loss_direct(
    reference_before_db: ArrayLike,
    reference_after_db: ArrayLike,
    receiver_before_db: ArrayLike,
    receiver_after_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> MeasuredBarrierInsertionLoss:
    r"""The insertion loss by the direct method, 8.2.1.

    .. math::

       D_{IL} = \left(L_{\text{ref},A} - L_{\text{ref},B}\right)
              - \left(L_{r,A} - L_{r,B}\right)

    The reference term is the source normalisation: whatever the source did
    differently between the two campaigns, the reference microphone heard it
    too, and subtracting it leaves the barrier. A uniform change of source
    output therefore leaves the answer alone, which is the property the whole
    arrangement exists for.

    The method holds only where the barrier had not been built yet or could be
    taken down, and 4.1 adds the condition that makes the subtraction mean
    anything: **the same reference and receiver positions in both campaigns**.

    :param reference_before_db: :math:`L_{\text{ref},B}` per band, in decibels.
    :param reference_after_db: :math:`L_{\text{ref},A}` per band, in decibels.
    :param receiver_before_db: :math:`L_{r,B}` per band, in decibels.
    :param receiver_after_db: :math:`L_{r,A}` per band, in decibels.
    :param frequencies: Nominal band centres, in hertz.
    :return: The insertion loss, as a :class:`MeasuredBarrierInsertionLoss`.
    :raises ValueError: For levels that do not match band for band, or a band
        centre that is not strictly positive.
    """
    ref_b, ref_a, rec_b, rec_a, freqs = _four_levels(
        reference_before_db,
        reference_after_db,
        receiver_before_db,
        receiver_after_db,
        frequencies,
    )
    loss = (ref_a - ref_b) - (rec_a - rec_b)
    return MeasuredBarrierInsertionLoss(
        frequencies=freqs,
        reference_before_db=ref_b,
        reference_after_db=ref_a,
        receiver_before_db=rec_b,
        receiver_after_db=rec_a,
        insertion_loss_db=np.asarray(loss, dtype=np.float64),
        method="direct",
        receiver_correction_before_db=0.0,
        receiver_correction_after_db=0.0,
    )


def measured_insertion_loss_indirect(
    reference_before_db: ArrayLike,
    reference_after_db: ArrayLike,
    receiver_before_db: ArrayLike,
    receiver_after_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    receiver_type_before: ReceiverType = "hemi_free_field",
    receiver_type_after: ReceiverType = "hemi_free_field",
) -> MeasuredBarrierInsertionLoss:
    r"""The insertion loss by the indirect method, 8.2.2.

    .. math::

       \Delta L_B = L_{\text{ref},B} - \left(L_{r,B} - C_r\right), \qquad
       \Delta L_A = L_{\text{ref},A} - \left(L_{r,A} - C'_r\right), \qquad
       D'_{IL} = \Delta L_A - \Delta L_B

    The "before" pair comes from a substitute site judged equivalent in
    terrain, ground and source, which is what makes this an estimate rather
    than a determination: 8.2.2 says so itself.

    :math:`C_r` and :math:`C'_r` correct for the kind of receiver position:
    0 dB in a hemi free field, 6 dB for a microphone against a facade, where
    the pressure doubles. The clause attaches the unprimed symbol to the
    "before" equation and the primed one to the "after", and then defines the
    two by receiver type rather than by campaign, which taken literally would
    force one type on each campaign. The NOTE settles it, by preferring
    receiver positions "where corrections :math:`C_r` and :math:`C'_r` are
    essentially the same", so the type is asked for once per campaign here
    (see the errata).

    Where the two types agree, the correction cancels and this returns exactly
    what :func:`measured_insertion_loss_direct` returns on the same four
    levels. Where they differ, the answer moves by 6 dB, which is why the NOTE
    exists.

    :param reference_before_db: :math:`L_{\text{ref},B}` per band, at the
        substitute site, in decibels.
    :param reference_after_db: :math:`L_{\text{ref},A}` per band, in decibels.
    :param receiver_before_db: :math:`L_{r,B}` per band, at the substitute
        site, in decibels.
    :param receiver_after_db: :math:`L_{r,A}` per band, in decibels.
    :param frequencies: Nominal band centres, in hertz.
    :param receiver_type_before: ``"hemi_free_field"`` (default) or
        ``"reflecting_surface"``, for the substitute site.
    :param receiver_type_after: The same for the barrier site.
    :return: The insertion loss, as a :class:`MeasuredBarrierInsertionLoss`.
    :raises ValueError: For levels that do not match band for band, a band
        centre that is not strictly positive, or an unknown receiver type.
    """
    ref_b, ref_a, rec_b, rec_a, freqs = _four_levels(
        reference_before_db,
        reference_after_db,
        receiver_before_db,
        receiver_after_db,
        frequencies,
    )
    before_type = require_choice(
        str(receiver_type_before), "receiver_type_before", _RECEIVER_TYPES
    )
    after_type = require_choice(
        str(receiver_type_after), "receiver_type_after", _RECEIVER_TYPES
    )
    correction_before = RECEIVER_CORRECTIONS_DB[before_type]
    correction_after = RECEIVER_CORRECTIONS_DB[after_type]
    if before_type != after_type:
        msg = (
            "The NOTE to ISO 10847 8.2.2 prefers receiver positions whose "
            "corrections are essentially the same; these two differ by "
            f"{abs(correction_after - correction_before):g} dB, which moves "
            "the answer by that much."
        )
        warnings.warn(msg, BarrierInSituWarning, stacklevel=2)
    delta_before = ref_b - (rec_b - correction_before)
    delta_after = ref_a - (rec_a - correction_after)
    return MeasuredBarrierInsertionLoss(
        frequencies=freqs,
        reference_before_db=ref_b,
        reference_after_db=ref_a,
        receiver_before_db=rec_b,
        receiver_after_db=rec_a,
        insertion_loss_db=np.asarray(delta_after - delta_before, dtype=np.float64),
        method="indirect",
        receiver_correction_before_db=correction_before,
        receiver_correction_after_db=correction_after,
    )
