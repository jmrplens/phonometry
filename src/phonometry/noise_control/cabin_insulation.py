#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What a cabin keeps out, measured in the room it stands in (ISO 11957).

An enclosure keeps noise in; a **cabin** keeps it out. ISO 11957:1996 measures
the second, and it measures it as one subtraction: put the cabin in a sound
field, measure the level in the room and the level inside the empty cabin, and
take the difference band by band.

.. math::

   D_p = (L_p)_{\text{room}} - (L_p)_{\text{cabin}}

That is Equation (1) in the laboratory. Equation (2) is the same arithmetic
**in situ**, where the room need not be diffuse, and the answer carries a prime
to say so: :math:`D'_p`. Equation (3) is the A-weighted difference
:math:`D'_{pA}`, and the standard defines it only for the third of its three
methods, the one that drives the room with the noise that is actually there.
There is no unprimed :math:`D_{pA}` in this document, and
:func:`cabin_insulation` refuses to compute one.

The three methods
-----------------

* **laboratory**, clause 6, in a reverberation room to ISO 3741, with at least
  two loudspeaker positions;
* **in situ with a loudspeaker**, 7.2.1, in any room at all, where the number
  of source positions is not fixed in advance but read off the spread of the
  answer itself (:func:`check_source_positions`);
* **in situ with the actual noise**, 7.2.2, where the machinery of the
  workplace is the source, which is the only method that yields
  :math:`D'_{pA}`.

Only results from the same method may be compared, which is why the method is
a field of :class:`CabinInsulationResult` and not a remark in a docstring.

What is here and what is not
----------------------------

Every equation of clauses 6 to 9 is implemented, plus the numeric acceptance
rules the clauses state: the source-position criterion of 7.2.1, the flatness
of the driving spectrum of 6.4, the clearance of 6.2, the background margins,
and the volume ratio clause 10 attaches its uncertainty to. The single-number
rating of clause 8 is handed to :func:`phonometry.building.weighted_rating`,
which is ISO 717-1 with :math:`D_p` written where that standard writes
:math:`R`, and the background correction is handed to
:func:`phonometry.emission.reverberation_background_correction`, which is the
ISO 3741 the clauses point at.

The leak ratio of definition 3.14 and the seal ratio of its note are printed
word for word as in ISO 11546, so they are imported from
:mod:`phonometry.noise_control.enclosure_insulation` rather than written twice.
The scope is tighter here: ISO 11546 only prefers a leak ratio under 2 %, while
clause 1 of ISO 11957 makes it a condition of applicability.

Instrumentation, mounting, the ten operations of every movable part and the
report template are procedure, and procedure is not arithmetic. The one piece
of clause 11 that computes is the rounding of 11.4 e), which is
:meth:`CabinInsulationResult.rounded`.

The document prints no worked example, so the tests are anchored on the
algebraic identities of the subtraction, on the printed thresholds, and on the
identity that makes :func:`estimated_cabin_noise_insulation` agree with its own
inputs.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from .._internal.levels_math import energy_mean, energy_sum
from .._internal.validation import (
    require_choice,
    require_finite,
    require_finite_array,
    require_finite_matrix,
    require_positive,
)
from .._internal.warnings import PhonometryWarning
from ..emission._shared import _a_weighting_corrections
from ..emission.sound_power_reverberation import reverberation_background_correction
from ._insulation_shared import (
    _THIRD_OCTAVE,
    MANDATORY_BAND_RANGE_HZ,
    PREFERRED_BAND_RANGE_HZ,
    _band_fraction,
    _check_band_range,
    _rating_bands,
    _require_rating_bands,
    leak_ratio,
    seal_ratio,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "BAND_FLATNESS_LIMIT_DB",
    "DEFAULT_BAND_FLATNESS_LIMIT_DB",
    "INCREASED_UNCERTAINTY_BAND_RANGE_HZ",
    "INTERNAL_NOISE_CENTRE_HEIGHT_M",
    "INTERNAL_NOISE_CENTRE_TOLERANCE_M",
    "INTERNAL_NOISE_CORRECTION_WINDOW_DB",
    "IN_SITU_EXCESS_STANDARD_DEVIATION_DB",
    "LOW_BAND_CLEARANCE_M",
    "LOW_BAND_CLEARANCE_RANGE_HZ",
    "MANDATORY_BAND_RANGE_HZ",
    "MAX_LEAK_RATIO",
    "MAX_MICROPHONE_TO_CABIN_M",
    "MAX_SOURCE_POSITIONS_IN_SITU",
    "MIN_FIXED_MICROPHONE_POSITIONS",
    "MIN_LOUDSPEAKER_POSITIONS",
    "MIN_LOUDSPEAKER_SEPARATION_M",
    "MIN_MICROPHONE_HEIGHT_M",
    "MIN_ROOM_TO_CABIN_VOLUME_RATIO",
    "MIN_SIGNAL_TO_BACKGROUND_DB",
    "MIN_SOURCE_POSITIONS_IN_SITU",
    "MIN_SOURCE_TO_CABIN_M",
    "MIN_SOURCE_TO_MICROPHONE_IN_SITU_M",
    "MIN_SOURCE_TO_MICROPHONE_M",
    "OPERATOR_PATH_INCLINATION_DEG",
    "OPERATOR_SPHERE_RADIUS_M",
    "PREFERRED_BAND_RANGE_HZ",
    "PREFERRED_SIGNAL_TO_BACKGROUND_DB",
    "STATED_UNCERTAINTY_BAND_RANGE_HZ",
    "WALL_CLEARANCE_FACTOR",
    "BandFlatnessCheck",
    "CabinInsulationResult",
    "CabinInsulationWarning",
    "CabinUncertainty",
    "SourcePositionCheck",
    "WeightedCabinInsulation",
    "cabin_insulation",
    "check_band_flatness",
    "check_source_positions",
    "estimated_cabin_noise_insulation",
    "internal_noise_level",
    "leak_ratio",
    "minimum_cabin_clearance_m",
    "seal_ratio",
    "uncertainty_conditions",
    "weighted_cabin_insulation",
]

#: Clause 1: the methods hold for a cabin whose openings are at most this
#: fraction of its interior surface. ISO 11546 only prefers the same 2 %;
#: here it is a condition of applicability.
MAX_LEAK_RATIO: float = 0.02

#: 6.2: above the low-frequency range the cabin stands half a wavelength from
#: the walls, the ceiling and any diffusing element, so the factor is a half.
WALL_CLEARANCE_FACTOR: float = 0.5

#: 6.2: in the low-frequency range the clearance is a flat distance instead.
LOW_BAND_CLEARANCE_M: float = 2.0

#: 6.2: the range that flat distance belongs to, in hertz.
LOW_BAND_CLEARANCE_RANGE_HZ: tuple[float, float] = (50.0, 80.0)

#: 6.4 and 7.2.1: the least distance between two loudspeaker positions.
MIN_LOUDSPEAKER_SEPARATION_M: float = 3.0

#: 6.4 and 7.2.1: the least distance from a loudspeaker to the cabin.
MIN_SOURCE_TO_CABIN_M: float = 2.0

#: 6.4: the least distance from a loudspeaker to a microphone, in the
#: laboratory.
MIN_SOURCE_TO_MICROPHONE_M: float = 2.0

#: 7.4: the same distance in situ, where the standard asks for more.
MIN_SOURCE_TO_MICROPHONE_IN_SITU_M: float = 3.0

#: 7.4: in a large room with a short reverberation time, no microphone should
#: stand further than this from the outside of the cabin.
MAX_MICROPHONE_TO_CABIN_M: float = 5.0

#: 6.5.1: the least height of a microphone inside the cabin above the floor.
MIN_MICROPHONE_HEIGHT_M: float = 1.0

#: 6.5.2 and 6.7: the radius of the sphere or circle around the operator's
#: head, and around the middle of a cabin with no defined operator position.
#: ISO 11821 5.5.1 prints the same sphere for a screen, and
#: :mod:`phonometry.noise_control.screen_in_situ` re-exports this rather than
#: printing the number twice.
OPERATOR_SPHERE_RADIUS_M: float = 0.3

#: 6.5.2 and 6.7: the inclination of a rotating microphone path.
OPERATOR_PATH_INCLINATION_DEG: float = 45.0

#: 6.7: the height of the centre of that sphere when the cabin has no defined
#: operator position, and the tolerance on it.
INTERNAL_NOISE_CENTRE_HEIGHT_M: float = 1.55
INTERNAL_NOISE_CENTRE_TOLERANCE_M: float = 0.075

#: 6.4, 6.5.1 and 7.4: the fewest fixed microphone positions. In situ 7.4
#: fixes the number at exactly six rather than at least six.
MIN_FIXED_MICROPHONE_POSITIONS: int = 6

#: 6.4: the fewest loudspeaker positions in the laboratory.
MIN_LOUDSPEAKER_POSITIONS: int = 2

#: 7.2.1: the fewest and the most source positions in situ.
MIN_SOURCE_POSITIONS_IN_SITU: int = 3
MAX_SOURCE_POSITIONS_IN_SITU: int = 6

#: 6.4 and 7.2.1: the most the three one-third-octave levels inside one octave
#: may differ, by octave centre frequency in hertz. Bands above those listed
#: take :data:`DEFAULT_BAND_FLATNESS_LIMIT_DB`; the standard prints no limit
#: below 125 Hz.
BAND_FLATNESS_LIMIT_DB: dict[float, float] = {125.0: 6.0, 250.0: 5.0}

#: 6.4 and 7.2.1: the limit in every octave above 250 Hz.
DEFAULT_BAND_FLATNESS_LIMIT_DB: float = 4.0

#: 6.4 and 7.2.1: the margin the level inside the cabin keeps over the
#: background, and the margin the standard would rather have.
MIN_SIGNAL_TO_BACKGROUND_DB: float = 6.0
PREFERRED_SIGNAL_TO_BACKGROUND_DB: float = 12.0

#: 6.7: the internal noise level is corrected for the background only inside
#: this window. Below it the measurement does not stand; above it the
#: correction is not worth making.
INTERNAL_NOISE_CORRECTION_WINDOW_DB: tuple[float, float] = (6.0, 10.0)

#: Clause 10: the uncertainty of ISO 3741 carries over only when the room is
#: at least this many times the volume of the cabin.
MIN_ROOM_TO_CABIN_VOLUME_RATIO: float = 20.0

#: Clause 10: the band range that statement covers, in hertz.
STATED_UNCERTAINTY_BAND_RANGE_HZ: tuple[float, float] = (250.0, 10000.0)

#: Clause 10: the range where an increased uncertainty is expected, in hertz.
INCREASED_UNCERTAINTY_BAND_RANGE_HZ: tuple[float, float] = (50.0, 200.0)

#: Clause 10: what the loudspeaker method in situ adds to the standard
#: deviation of the laboratory method.
IN_SITU_EXCESS_STANDARD_DEVIATION_DB: float = 2.0

CabinMethod = Literal["laboratory", "in-situ-loudspeaker", "in-situ-actual-noise"]
_METHODS: tuple[str, ...] = (
    "laboratory",
    "in-situ-loudspeaker",
    "in-situ-actual-noise",
)
_IN_SITU_METHODS: tuple[str, ...] = ("in-situ-loudspeaker", "in-situ-actual-noise")
_ACTUAL_NOISE = "in-situ-actual-noise"

#: The nominal one-third-octave centre frequencies of each nominal octave, in
#: hertz. A band is named by the standard or it is not a band: reading the
#: octave off the nearest centre instead would have accepted 220 Hz, 250 Hz and
#: 280 Hz as the three thirds of the 250 Hz octave, and none of the two outer
#: ones is a band anybody measured.
_THIRDS_OF_OCTAVE_HZ: dict[float, tuple[float, float, float]] = {
    31.5: (25.0, 31.5, 40.0),
    63.0: (50.0, 63.0, 80.0),
    125.0: (100.0, 125.0, 160.0),
    250.0: (200.0, 250.0, 315.0),
    500.0: (400.0, 500.0, 630.0),
    1000.0: (800.0, 1000.0, 1250.0),
    2000.0: (1600.0, 2000.0, 2500.0),
    4000.0: (3150.0, 4000.0, 5000.0),
    8000.0: (6300.0, 8000.0, 10000.0),
    16000.0: (12500.0, 16000.0, 20000.0),
}

#: How far a given frequency may sit from a nominal centre and still be that
#: band, as a relative tolerance. The slack has to be relative because what it
#: absorbs is relative: a nominal name is the exact base-ten centre rounded,
#: and the roundest of them, 160 Hz against 158,49 Hz, is 0,95 % away. Two
#: adjacent one-third-octave bands are 26 % apart, so 2 % accepts either
#: spelling of the same band and can never reach the next one.
_NOMINAL_CENTRE_TOLERANCE = 0.02

#: The three one-third-octave bands inside one octave.
_THIRDS_PER_OCTAVE = 3

#: The lowest octave the flatness rule of 6.4 names, in hertz.
_LOWEST_FLATNESS_OCTAVE_HZ = 125.0

#: The default speed of sound the clearance of 6.2 is read at, in m/s.
_SPEED_OF_SOUND_M_S = 343.0


class CabinInsulationWarning(PhonometryWarning):
    """The measurement is outside a condition ISO 11957 states."""


def _corrected(
    levels: NDArray[np.float64],
    background_levels: ArrayLike | None,
    frequencies: NDArray[np.float64] | None,
    where: str,
) -> NDArray[np.float64]:
    """Take the background off a spectrum, 6.4 by way of ISO 3741."""
    if background_levels is None:
        return levels
    if frequencies is None:
        msg = (
            f"The background correction of ISO 3741 is read band by band, so "
            f"'frequencies' is needed alongside '{where}_background_levels'."
        )
        raise ValueError(msg)
    background = require_finite_array(background_levels, f"{where}_background_levels")
    if background.shape != levels.shape:
        msg = f"'{where}_background_levels' must match '{where}_levels' band for band."
        raise ValueError(msg)
    margin = levels - background
    if float(np.min(margin)) < MIN_SIGNAL_TO_BACKGROUND_DB:
        msg = (
            f"ISO 11957 asks for at least {MIN_SIGNAL_TO_BACKGROUND_DB:g} dB over "
            f"the background in the {where}, and preferably more than "
            f"{PREFERRED_SIGNAL_TO_BACKGROUND_DB:g} dB; the smallest margin is "
            f"{float(np.min(margin)):.1f} dB."
        )
        warnings.warn(msg, CabinInsulationWarning, stacklevel=3)
    return levels - reverberation_background_correction(levels, background, frequencies)


@dataclass(frozen=True)
class CabinInsulationResult:
    r"""The sound pressure insulation of a cabin, band by band.

    :ivar frequencies: Nominal band centre frequencies, in hertz, or ``None``
        when the levels were given without them.
    :ivar room_levels: :math:`(L_p)_{\text{room}}`, in decibels, after any
        background correction.
    :ivar cabin_levels: :math:`(L_p)_{\text{cabin}}`, in decibels, after any
        background correction.
    :ivar insulation: :math:`D_p` or :math:`D'_p` per band, in decibels.
    :ivar apparent: Whether the answer carries the prime of 3.6, which it does
        for both in-situ methods.
    :ivar a_weighted_insulation: :math:`D'_{pA}` of Equation (3), in decibels,
        or ``None``. Defined only for the actual-noise method.
    :ivar internal_noise_level: :math:`L_{pA}` of 6.7, in decibels, or ``None``
        when the cabin has no integral source.
    :ivar method: ``"laboratory"``, ``"in-situ-loudspeaker"`` or
        ``"in-situ-actual-noise"``.
    :ivar band_fraction: 3 for one-third octaves, 1 for octaves.
    """

    frequencies: NDArray[np.float64] | None
    room_levels: NDArray[np.float64]
    cabin_levels: NDArray[np.float64]
    insulation: NDArray[np.float64]
    apparent: bool
    a_weighted_insulation: float | None
    internal_noise_level: float | None
    method: str
    band_fraction: int

    @property
    def symbol(self) -> str:
        r"""The symbol clause 12 reports this as, ``"D_p"`` or ``"D'_p"``."""
        return "D'_p" if self.apparent else "D_p"

    def rounded(self) -> NDArray[np.int_]:
        """The band values as 11.4 e) reports them, to the nearest decibel."""
        return np.asarray(np.rint(self.insulation), dtype=np.int_)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the two levels and the difference between them.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.noise_control.plot_cabin_insulation`.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from .._i18n import check_language
        from .._plot.noise_control import plot_cabin_insulation

        check_language(language)
        return plot_cabin_insulation(self, ax=ax, language=language, **kwargs)


@dataclass(frozen=True)
class WeightedCabinInsulation:
    r"""The single-number rating of a cabin, clause 8 by way of ISO 717-1.

    :ivar rating: :math:`D_{p,w}` or :math:`D'_{p,w}`, in decibels.
    :ivar c: The spectrum adaptation term :math:`C`, in decibels.
    :ivar ctr: The spectrum adaptation term :math:`C_{tr}`, in decibels.
    :ivar unfavourable_sum: The sum of unfavourable deviations at the shift
        the rating was read at, in decibels.
    :ivar band_centres_hz: The bands the rating was read over, in hertz.
    :ivar apparent: Whether the rating carries the prime of 3.9.
    """

    rating: int
    c: int
    ctr: int
    unfavourable_sum: float
    band_centres_hz: NDArray[np.float64]
    apparent: bool


@dataclass(frozen=True)
class SourcePositionCheck:
    r"""Whether enough loudspeaker positions were used, 7.2.1.

    :ivar positions_used: :math:`N`, the number of source positions measured.
    :ivar max_octave_spread_db: The largest difference in :math:`D'_p` between
        any two positions, over the octave bands, in decibels.
    :ivar required_positions: The fewest positions that spread calls for, never
        below :data:`MIN_SOURCE_POSITIONS_IN_SITU`.
    :ivar satisfied: Whether ``positions_used`` reaches that number.
    :ivar exceeds_maximum: Whether the spread runs past
        :data:`MAX_SOURCE_POSITIONS_IN_SITU`, which 7.2.1 says shall be stated
        in the report.
    """

    positions_used: int
    max_octave_spread_db: float
    required_positions: int
    satisfied: bool
    exceeds_maximum: bool


@dataclass(frozen=True)
class BandFlatnessCheck:
    r"""How flat the driving spectrum is inside each octave, 6.4 and 7.2.1.

    :ivar octave_centres_hz: The octave centre frequencies read, in hertz.
    :ivar spread_db: The difference between the loudest and the quietest of the
        three one-third-octave bands in each, in decibels.
    :ivar limit_db: What 6.4 allows in each, in decibels, and ``nan`` in the
        octaves below 125 Hz, for which the clause prints no limit.
    :ivar satisfied: Whether each octave meets its limit. An octave with no
        printed limit is reported as satisfied.
    """

    octave_centres_hz: NDArray[np.float64]
    spread_db: NDArray[np.float64]
    limit_db: NDArray[np.float64]
    satisfied: NDArray[np.bool_]

    @property
    def all_satisfied(self) -> bool:
        """Whether every octave with a printed limit meets it."""
        return bool(np.all(self.satisfied))


@dataclass(frozen=True)
class CabinUncertainty:
    r"""What clause 10 will and will not say about a measurement.

    :ivar method: The method the statement is about.
    :ivar volume_ratio: :math:`V_{\text{room}} / V_{\text{cabin}}`.
    :ivar ratio_satisfied: Whether that ratio reaches
        :data:`MIN_ROOM_TO_CABIN_VOLUME_RATIO`.
    :ivar stateable: Whether clause 10 offers any figure at all. It does not
        for the actual-noise method, which it sends to ISO 4871 instead.
    :ivar stated_band_range_hz: The range the statement covers, in hertz, or
        ``None`` when nothing is stateable.
    :ivar increased_uncertainty_band_range_hz: The range where a larger
        uncertainty is expected, in hertz, or ``None``.
    :ivar excess_standard_deviation_db: What this method adds to the standard
        deviation of the laboratory one, in decibels, or ``None``.
    """

    method: str
    volume_ratio: float
    ratio_satisfied: bool
    stateable: bool
    stated_band_range_hz: tuple[float, float] | None
    increased_uncertainty_band_range_hz: tuple[float, float] | None
    excess_standard_deviation_db: float | None


def cabin_insulation(
    room_levels: ArrayLike,
    cabin_levels: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    method: CabinMethod = "laboratory",
    band_fraction: int = 3,
    room_background_levels: ArrayLike | None = None,
    cabin_background_levels: ArrayLike | None = None,
    a_weighted_room_level: float | None = None,
    a_weighted_cabin_level: float | None = None,
    internal_noise_level: float | None = None,
) -> CabinInsulationResult:
    r"""Sound pressure insulation of a cabin, Equations (1), (2) and (3).

    One function for the three equations, because the three are the same
    subtraction and what separates them is the method, not the arithmetic:

    .. math::

       D_p = (L_p)_{\text{room}} - (L_p)_{\text{cabin}}

    in the laboratory, the same in situ under the name :math:`D'_p`, and the
    A-weighted difference :math:`D'_{pA} = (L_{pA})_{\text{room}} -
    (L_{pA})_{\text{cabin}}` when the source is the noise of the workplace.
    Definition 3.7 ties that last one to the actual-noise method alone, so an
    A-weighted pair given under another method is refused rather than quietly
    renamed.

    Where a background spectrum is supplied it is taken off first, by the
    ISO 3741 correction 6.4 asks for, and a margin under
    :data:`MIN_SIGNAL_TO_BACKGROUND_DB` is reported.

    :param room_levels: :math:`(L_p)_{\text{room}}` per band, in decibels.
    :param cabin_levels: :math:`(L_p)_{\text{cabin}}` per band, in decibels.
    :param frequencies: Nominal band centres, in hertz.
    :param method: ``"laboratory"`` (default), ``"in-situ-loudspeaker"`` or
        ``"in-situ-actual-noise"``.
    :param band_fraction: 3 for one-third octaves (default), 1 for octaves.
    :param room_background_levels: Background in the room per band, in
        decibels, for the correction of 7.2.2.
    :param cabin_background_levels: Background inside the cabin per band, in
        decibels, for the correction of 6.4.
    :param a_weighted_room_level: :math:`(L_{pA})_{\text{room}}`, in decibels.
    :param a_weighted_cabin_level: :math:`(L_{pA})_{\text{cabin}}`, in decibels.
    :param internal_noise_level: :math:`L_{pA}` of 6.7, in decibels, carried
        into the result because 11.4 reports it beside the insulation.
    :return: The insulation, as a :class:`CabinInsulationResult`.
    :raises ValueError: For spectra that do not match, an unknown method or
        band fraction, or an A-weighted pair under a method that does not
        define one.
    """
    room = require_finite_array(room_levels, "room_levels")
    cabin = require_finite_array(cabin_levels, "cabin_levels")
    if room.shape != cabin.shape:
        msg = "'room_levels' and 'cabin_levels' must match band for band."
        raise ValueError(msg)
    freqs: NDArray[np.float64] | None = None
    if frequencies is not None:
        freqs = require_finite_array(frequencies, "frequencies")
        if freqs.shape != room.shape:
            msg = "'frequencies' must match the spectra band for band."
            raise ValueError(msg)
        if np.any(freqs <= 0.0):
            msg = "'frequencies' must be positive."
            raise ValueError(msg)
    fraction = _band_fraction(band_fraction)
    how = require_choice(str(method), "method", _METHODS)
    _check_band_range(
        freqs, fraction, standard="ISO 11957", category=CabinInsulationWarning
    )
    room = _corrected(room, room_background_levels, freqs, "room")
    cabin = _corrected(cabin, cabin_background_levels, freqs, "cabin")
    weighted: float | None = None
    if a_weighted_room_level is not None or a_weighted_cabin_level is not None:
        if a_weighted_room_level is None or a_weighted_cabin_level is None:
            msg = (
                "Equation (3) is a difference, so give both "
                "'a_weighted_room_level' and 'a_weighted_cabin_level' or "
                "neither."
            )
            raise ValueError(msg)
        if how != _ACTUAL_NOISE:
            msg = (
                "ISO 11957 defines the A-weighted insulation D'_pA only for "
                "the actual environmental noise (definition 3.7 and Equation "
                f"(3)); method is {how!r}."
            )
            raise ValueError(msg)
        weighted = require_finite(
            a_weighted_room_level, "a_weighted_room_level"
        ) - require_finite(a_weighted_cabin_level, "a_weighted_cabin_level")
    return CabinInsulationResult(
        frequencies=freqs,
        room_levels=room,
        cabin_levels=cabin,
        insulation=np.asarray(room - cabin, dtype=np.float64),
        apparent=how in _IN_SITU_METHODS,
        a_weighted_insulation=weighted,
        internal_noise_level=(
            None
            if internal_noise_level is None
            else require_finite(internal_noise_level, "internal_noise_level")
        ),
        method=how,
        band_fraction=fraction,
    )


def weighted_cabin_insulation(
    insulation: ArrayLike,
    *,
    apparent: bool = False,
    band_fraction: int = 3,
) -> WeightedCabinInsulation:
    r"""The single-number rating of a cabin, clause 8.

    ISO 717-1 with :math:`D_p` or :math:`D'_p` written where that standard
    writes the sound reduction index: the reference curve, the shift and the
    adaptation terms come from :func:`phonometry.building.weighted_rating`, and
    what is done here is the trim to the rating bands and the prime.

    Clause 4 calls this the preferred single number and then warns against
    reading too much into it, because what a cabin is worth depends on the
    spectrum it stands in. :func:`estimated_cabin_noise_insulation` is the
    answer to that objection.

    :param insulation: :math:`D_p` or :math:`D'_p` over the 16 one-third-octave
        rating bands or the 5 octave ones, in decibels.
    :param apparent: Whether the spectrum is the in-situ one, which decides
        whether the rating is :math:`D_{p,w}` or :math:`D'_{p,w}`.
    :param band_fraction: 3 for one-third octaves (default), 1 for octaves.
    :return: The rating, as a :class:`WeightedCabinInsulation`.
    :raises ValueError: For a spectrum that is not the rating bands.
    """
    from ..building import weighted_rating

    values = require_finite_array(insulation, "insulation")
    fraction = _band_fraction(band_fraction)
    bands, band_set = _rating_bands(fraction)
    _require_rating_bands(values, bands)
    result = weighted_rating(values, band_set)
    return WeightedCabinInsulation(
        rating=int(result.rating),
        c=int(result.c),
        ctr=int(result.ctr),
        unfavourable_sum=float(result.unfavourable_sum),
        band_centres_hz=bands,
        apparent=bool(apparent),
    )


def estimated_cabin_noise_insulation(
    spectrum_levels: ArrayLike,
    insulation: ArrayLike,
    *,
    frequencies: ArrayLike,
) -> float:
    r"""What a cabin is worth against a stated spectrum, Annex A.

    Both formulas of the annex, which differ only in whether :math:`D_p` or
    :math:`D'_p` is substituted:

    .. math::

       D_{pA,e} = L_A - 10 \lg \sum_i 10^{0,1 (L_i - A_i - D_{pi})}

    with :math:`L_A = 10 \lg \sum_i 10^{0,1 (L_i - A_i)}` the A-weighted total
    of the assumed spectrum. The sign of :math:`A_i` is the trap: the annex
    prints an attenuation, positive where the weighting takes level away, while
    this library's band corrections are the correction itself, so
    :math:`A_i = -C_k`. Both terms are built here from the same table, so the
    total and the sum cannot disagree, and an insulation of zero returns
    exactly zero.

    The annex assumes a diffuse field and says so; in situ it will usually not
    be, and nothing here is corrected for flanking through the floor.

    :param spectrum_levels: :math:`L_i`, the assumed noise spectrum per band,
        in decibels.
    :param insulation: :math:`D_{pi}` or :math:`D'_{pi}` per band, in decibels.
    :param frequencies: Nominal band centres, in hertz.
    :return: :math:`D_{pA,e}` or :math:`D'_{pA,e}`, in decibels.
    :raises ValueError: For inputs that do not match band for band.
    """
    levels = require_finite_array(spectrum_levels, "spectrum_levels")
    loss = require_finite_array(insulation, "insulation")
    freqs = require_finite_array(frequencies, "frequencies")
    if levels.shape != loss.shape or levels.shape != freqs.shape:
        msg = (
            "'spectrum_levels', 'insulation' and 'frequencies' must match "
            "band for band."
        )
        raise ValueError(msg)
    corrections = _a_weighting_corrections(freqs)
    outside = energy_sum(levels + corrections)
    inside = energy_sum(levels + corrections - loss)
    return float(outside - inside)


def internal_noise_level(
    levels: ArrayLike,
    *,
    background_level: float | None = None,
) -> float:
    r"""The noise a cabin makes on its own, :math:`L_{pA}` of 6.7.

    The A-weighted levels measured at the three positions on the 0,3 m sphere,
    or over the inclined circular path, averaged on a mean-square basis with
    the external sources switched off.

    The background rule of 6.7 is not the one of 6.4. The margin over the
    background must reach :data:`MIN_SIGNAL_TO_BACKGROUND_DB`, and the
    correction is made **only** while the margin stays inside
    :data:`INTERNAL_NOISE_CORRECTION_WINDOW_DB`: past the top of that window
    the correction is under a tenth of a decibel and the clause does not ask
    for it. The correction itself is the :math:`K_1` of ISO 3741,
    :math:`-10 \lg (1 - 10^{-0,1 \Delta L})`, applied to the A-weighted total
    rather than band by band, which is what makes it a separate line here from
    :func:`phonometry.emission.reverberation_background_correction`.

    :param levels: The A-weighted levels at the microphone positions, in
        decibels.
    :param background_level: The A-weighted background inside the cabin with
        the integral sources switched off, in decibels.
    :return: :math:`L_{pA}`, in decibels.
    :raises ValueError: For an empty or non-finite set of levels.
    """
    values = require_finite_array(levels, "levels")
    if values.size == 0:
        msg = "'levels' must hold at least one microphone position."
        raise ValueError(msg)
    mean = float(energy_mean(values))
    if background_level is None:
        return mean
    lower, upper = INTERNAL_NOISE_CORRECTION_WINDOW_DB
    margin = mean - require_finite(background_level, "background_level")
    if margin < lower:
        msg = (
            f"ISO 11957 6.7 asks for at least {lower:g} dB over the background "
            f"inside the cabin, and preferably more than "
            f"{PREFERRED_SIGNAL_TO_BACKGROUND_DB:g} dB; the margin is "
            f"{margin:.1f} dB, so L_pA is an upper bound."
        )
        warnings.warn(msg, CabinInsulationWarning, stacklevel=2)
        return mean
    if margin > upper:
        return mean
    return mean + 10.0 * float(np.log10(1.0 - 10.0 ** (-0.1 * margin)))


def check_source_positions(
    insulation_by_position: ArrayLike,
) -> SourcePositionCheck:
    r"""Were there enough loudspeaker positions? 7.2.1.

    The only acceptance criterion in the document that is read off the answer
    rather than fixed in advance: the number of source positions shall be at
    least the largest difference, in decibels, between the :math:`D'_p` of any
    two positions, **in octave bands**. Three positions to begin with, six at
    most, and a spread past six goes in the report.

    The clause says octave bands, and it says so because the spread of a
    one-third-octave answer is the wider one. A one-third-octave measurement is
    therefore folded to octaves at the level, by energy-summing the room and
    the cabin spectra, before the difference is formed; folding the difference
    itself is not the same number, so this function takes the octave-band
    :math:`D'_p` already formed and does not pretend to do that conversion.

    :param insulation_by_position: :math:`D'_p` in octave bands, one row per
        source position and one column per band, in decibels.
    :return: The verdict, as a :class:`SourcePositionCheck`.
    :raises ValueError: For fewer than :data:`MIN_SOURCE_POSITIONS_IN_SITU`
        positions, or an array that is not rectangular.
    """
    values = require_finite_matrix(insulation_by_position, "insulation_by_position")
    positions = int(values.shape[0])
    if positions < MIN_SOURCE_POSITIONS_IN_SITU:
        msg = (
            f"ISO 11957 7.2.1 starts from {MIN_SOURCE_POSITIONS_IN_SITU} source "
            f"positions; got {positions}."
        )
        raise ValueError(msg)
    spread = float(np.max(np.max(values, axis=0) - np.min(values, axis=0)))
    required = max(
        MIN_SOURCE_POSITIONS_IN_SITU,
        min(MAX_SOURCE_POSITIONS_IN_SITU, int(np.ceil(spread))),
    )
    return SourcePositionCheck(
        positions_used=positions,
        max_octave_spread_db=spread,
        required_positions=required,
        satisfied=positions >= required,
        exceeds_maximum=spread > MAX_SOURCE_POSITIONS_IN_SITU,
    )


def _nominal_third(frequency: float) -> tuple[float, int]:
    """The octave a nominal one-third-octave band belongs to, and its place.

    :param frequency: The band centre as given, in hertz.
    :return: The nominal octave centre in hertz, and which of its three thirds
        this is, counted from the lowest.
    :raises ValueError: For a frequency that names no one-third-octave band.
    """
    for centre, thirds in _THIRDS_OF_OCTAVE_HZ.items():
        for index, third in enumerate(thirds):
            if math.isclose(frequency, third, rel_tol=_NOMINAL_CENTRE_TOLERANCE):
                return centre, index
    msg = (
        f"{frequency:g} Hz is not a nominal one-third-octave centre "
        "frequency of any octave band."
    )
    raise ValueError(msg)


def check_band_flatness(
    third_octave_levels: ArrayLike,
    *,
    frequencies: ArrayLike,
) -> BandFlatnessCheck:
    r"""Is the driving spectrum flat enough inside each octave? 6.4 and 7.2.1.

    An octave-band measurement only means what the standard says it means if
    the sound that produced it was spread evenly across the octave. The clause
    puts a number on that: the three one-third-octave levels inside one octave
    shall not differ by more than 6 dB in the octave of 125 Hz, 5 dB in the one
    of 250 Hz and 4 dB in the bands of higher frequencies. Nothing is printed
    for the octaves below 125 Hz, so nothing is claimed for them here.

    :param third_octave_levels: The one-third-octave levels of the sound in the
        room, in decibels.
    :param frequencies: Their nominal centre frequencies, in hertz.
    :return: One row per octave, as a :class:`BandFlatnessCheck`.
    :raises ValueError: For inputs that do not match, a frequency that names no
        one-third-octave band, a band given twice, or an octave that is not
        covered by its three bands.
    """
    levels = require_finite_array(third_octave_levels, "third_octave_levels")
    freqs = require_finite_array(frequencies, "frequencies")
    if levels.shape != freqs.shape:
        msg = "'third_octave_levels' and 'frequencies' must match band for band."
        raise ValueError(msg)
    if np.any(freqs <= 0.0):
        msg = "'frequencies' must be positive."
        raise ValueError(msg)
    groups: dict[float, dict[int, float]] = {}
    for frequency, level in zip(freqs.tolist(), levels.tolist(), strict=True):
        centre, place = _nominal_third(float(frequency))
        band = groups.setdefault(centre, {})
        if place in band:
            msg = f"{frequency:g} Hz is given twice."
            raise ValueError(msg)
        band[place] = float(level)
    centres: list[float] = []
    spreads: list[float] = []
    limits: list[float] = []
    for centre in sorted(groups):
        members = list(groups[centre].values())
        if len(members) != _THIRDS_PER_OCTAVE:
            msg = (
                f"The flatness of the {centre:g} Hz octave is read over its "
                f"{_THIRDS_PER_OCTAVE} one-third-octave bands; got "
                f"{len(members)}."
            )
            raise ValueError(msg)
        centres.append(centre)
        spreads.append(max(members) - min(members))
        if centre < _LOWEST_FLATNESS_OCTAVE_HZ:
            limits.append(float("nan"))
        else:
            limits.append(
                BAND_FLATNESS_LIMIT_DB.get(centre, DEFAULT_BAND_FLATNESS_LIMIT_DB)
            )
    spread = np.asarray(spreads, dtype=np.float64)
    limit = np.asarray(limits, dtype=np.float64)
    satisfied = np.isnan(limit) | (spread <= limit)
    return BandFlatnessCheck(
        octave_centres_hz=np.asarray(centres, dtype=np.float64),
        spread_db=spread,
        limit_db=limit,
        satisfied=np.asarray(satisfied, dtype=np.bool_),
    )


def minimum_cabin_clearance_m(
    lowest_band_frequency_hz: float,
    *,
    speed_of_sound: float = _SPEED_OF_SOUND_M_S,
) -> float:
    r"""How far the cabin stands from the room, 6.2.

    Half a wavelength at the centre of the lowest band of interest, between the
    cabin and the walls, the ceiling and any diffusing element alike. Below
    100 Hz the clause stops computing and fixes a flat
    :data:`LOW_BAND_CLEARANCE_M`, which at 50 Hz is less than the half
    wavelength the rule above it would have asked for: the low-frequency
    sentence relaxes the requirement rather than tightening it, and it is
    written here exactly as printed.

    :param lowest_band_frequency_hz: The centre frequency of the lowest band of
        interest, in hertz.
    :param speed_of_sound: Speed of sound in the room, in metres per second.
    :return: The least clearance, in metres.
    :raises ValueError: For a non-positive frequency or speed.
    """
    frequency = require_positive(lowest_band_frequency_hz, "lowest_band_frequency_hz")
    celerity = require_positive(speed_of_sound, "speed_of_sound")
    low, high = LOW_BAND_CLEARANCE_RANGE_HZ
    preferred_low, preferred_high = PREFERRED_BAND_RANGE_HZ[_THIRD_OCTAVE]
    if frequency < preferred_low or frequency > preferred_high:
        msg = (
            f"ISO 11957 6.2 covers {preferred_low:g} Hz to {preferred_high:g} Hz; "
            f"{frequency:g} Hz is outside it."
        )
        warnings.warn(msg, CabinInsulationWarning, stacklevel=2)
    if low <= frequency <= high:
        return LOW_BAND_CLEARANCE_M
    return WALL_CLEARANCE_FACTOR * celerity / frequency


def uncertainty_conditions(
    *,
    room_volume_m3: float,
    cabin_volume_m3: float,
    method: CabinMethod = "laboratory",
) -> CabinUncertainty:
    r"""What clause 10 is willing to say about this measurement.

    In the laboratory the uncertainty of ISO 3741 carries over from 250 Hz to
    10 kHz, but only while the room is at least
    :data:`MIN_ROOM_TO_CABIN_VOLUME_RATIO` times the volume of the cabin; below
    that ratio, and from 50 Hz to 200 Hz in any case, a larger uncertainty is
    expected. The loudspeaker method in situ adds about
    :data:`IN_SITU_EXCESS_STANDARD_DEVIATION_DB` to the standard deviation. For
    the actual-noise method the clause states nothing at all and sends a
    declared value to ISO 4871.

    :param room_volume_m3: :math:`V_{\text{room}}`, in cubic metres.
    :param cabin_volume_m3: :math:`V_{\text{cabin}}`, in cubic metres.
    :param method: ``"laboratory"`` (default), ``"in-situ-loudspeaker"`` or
        ``"in-situ-actual-noise"``.
    :return: The statement, as a :class:`CabinUncertainty`.
    :raises ValueError: For a non-positive volume or an unknown method.
    """
    room = require_positive(room_volume_m3, "room_volume_m3")
    cabin = require_positive(cabin_volume_m3, "cabin_volume_m3")
    how = require_choice(str(method), "method", _METHODS)
    ratio = room / cabin
    satisfied = ratio >= MIN_ROOM_TO_CABIN_VOLUME_RATIO
    if how == _ACTUAL_NOISE:
        # Clause 10 states no uncertainty for this method at all, so the
        # volume ratio it attaches its statement to has nothing to qualify:
        # warning about it would report a condition on a number nobody gets.
        return CabinUncertainty(
            method=how,
            volume_ratio=ratio,
            ratio_satisfied=satisfied,
            stateable=False,
            stated_band_range_hz=None,
            increased_uncertainty_band_range_hz=None,
            excess_standard_deviation_db=None,
        )
    if not satisfied:
        msg = (
            f"ISO 11957 clause 10 states its uncertainty for a room at least "
            f"{MIN_ROOM_TO_CABIN_VOLUME_RATIO:g} times the volume of the cabin; "
            f"the ratio is {ratio:.1f}."
        )
        warnings.warn(msg, CabinInsulationWarning, stacklevel=2)
    excess = (
        IN_SITU_EXCESS_STANDARD_DEVIATION_DB if how == "in-situ-loudspeaker" else 0.0
    )
    return CabinUncertainty(
        method=how,
        volume_ratio=ratio,
        ratio_satisfied=satisfied,
        stateable=True,
        stated_band_range_hz=STATED_UNCERTAINTY_BAND_RANGE_HZ,
        increased_uncertainty_band_range_hz=INCREASED_UNCERTAINTY_BAND_RANGE_HZ,
        excess_standard_deviation_db=excess,
    )
