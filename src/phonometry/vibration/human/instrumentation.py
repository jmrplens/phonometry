#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Type-testing a human-vibration meter against ISO 8041-1:2017.

A sound level meter can be given a class: IEC 61672-1 prints design goals and
tolerance limits, and :func:`~phonometry.filters.verify_weighting_class`
turns a measured response into a verdict against them. A human-vibration
meter is checked the same way and by the same kind of table, and this module
is that check.

**What the standard grades.** ISO 8041-1 defines the nine frequency
weightings (:data:`~phonometry.vibration.WEIGHTING_NAMES`) as exact transfer
functions, and then says how far a real instrument may sit from them. The
allowance is not one number: it is a band that widens away from the middle of
the working range, keyed to four transition frequencies per weighting
(Table 4) and four tolerance regions between them (Table 5). Inside the
central region the magnitude may differ by ``+12 %`` / ``−11 %``; in the two
skirts by ``+26 %`` / ``−21 %``; beyond the outermost pair the standard stops
constraining the response from below altogether, which is what ``−100 %``
means in the printed table.

**What it does not grade.** A verdict here is about the *frequency weighting*,
which is one clause of a standard that also covers indication, linearity,
overload, temperature, humidity and electromagnetic susceptibility. Passing
this check is a necessary condition for conformity, never a certificate of
it: the rest are laboratory tests on hardware, not arithmetic.

**Tolerances are on the factor, not on the decibel.** The standard writes its
limits as percentages of the weighting factor, and this module keeps them
that way. ``+26 %`` is ``+2,0 dB`` to two decimals, but the percentage is
what the page prints and what the acceptance test in Annex B is written in.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.validation import require_choice, require_equal_shapes
from .exposure import WEIGHTING_NAMES, weighting_factors

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

#: Table 4: the four transition frequencies, in hertz, that key the tolerance
#: regions of Table 5 to a weighting. The standard prints them as powers
#: ``10**(k/10)``, so they are built that way here rather than from the
#: rounded decimals printed beside them: the exponents are the exact values
#: and the decimals are the courtesy.
_WHOLE_BODY_TRANSITIONS = (-6, -2, 18, 22)
_TRANSITION_EXPONENTS: dict[str, tuple[int, int, int, int]] = {
    "Wb": _WHOLE_BODY_TRANSITIONS,
    "Wc": _WHOLE_BODY_TRANSITIONS,
    "Wd": _WHOLE_BODY_TRANSITIONS,
    "We": _WHOLE_BODY_TRANSITIONS,
    "Wf": (-13, -9, -4, 0),
    "Wh": (6, 10, 29, 33),
    "Wj": _WHOLE_BODY_TRANSITIONS,
    "Wk": _WHOLE_BODY_TRANSITIONS,
    "Wm": (-3, 1, 18, 22),
}

#: Table 4 as frequencies in hertz, ``(ft1, ft2, ft3, ft4)`` per weighting.
TRANSITION_FREQUENCIES_HZ: dict[str, tuple[float, float, float, float]] = {
    name: (
        10.0 ** (exponents[0] / 10.0),
        10.0 ** (exponents[1] / 10.0),
        10.0 ** (exponents[2] / 10.0),
        10.0 ** (exponents[3] / 10.0),
    )
    for name, exponents in _TRANSITION_EXPONENTS.items()
}

#: The lower limit the standard writes as ``−100 %``: below the first
#: transition frequency and above the last one, no response is too small.
UNCONSTRAINED_BELOW = -100.0

#: Table 5, from the middle of the range outwards: the central region, the two
#: skirts around it, and the two tails. Each entry is
#: ``(upper %, lower %, characteristic phase deviation in degrees)``. The phase
#: tolerance applies only to instruments that provide a measurement parameter
#: not based on r.m.s. values, which is footnote a of the table.
CENTRAL_TOLERANCE_PERCENT = (12.0, -11.0, 6.0)
SKIRT_TOLERANCE_PERCENT = (26.0, -21.0, 12.0)
TAIL_TOLERANCE_PERCENT = (26.0, UNCONSTRAINED_BELOW, math.inf)

#: Table 1: the frequency at which each weighting is calibrated, in hertz. The
#: standard prints them in radians per second (100 rad/s for whole-body,
#: 500 rad/s for hand-transmitted, 2,5 rad/s for the low-frequency case), and
#: they are divided by 2 pi here rather than transcribed from the rounded
#: hertz beside them.
_REFERENCE_RAD_S: dict[str, float] = {
    "Wb": 100.0,
    "Wc": 100.0,
    "Wd": 100.0,
    "We": 100.0,
    "Wf": 2.5,
    "Wh": 500.0,
    "Wj": 100.0,
    "Wk": 100.0,
    "Wm": 100.0,
}
REFERENCE_FREQUENCY_HZ: dict[str, float] = {
    name: omega / (2.0 * math.pi) for name, omega in _REFERENCE_RAD_S.items()
}

#: Table 1: the r.m.s. acceleration the reference condition is defined at, in
#: metres per second squared. The weightings are not unity there, so the
#: indication a conforming meter shows is this value times the weighting
#: factor at the reference frequency.
REFERENCE_ACCELERATION_M_S2: dict[str, float] = {
    "Wb": 1.0,
    "Wc": 1.0,
    "Wd": 1.0,
    "We": 1.0,
    "Wf": 0.1,
    "Wh": 10.0,
    "Wj": 1.0,
    "Wk": 1.0,
    "Wm": 1.0,
}

#: Table 2: how far the indication itself may sit from the true value at the
#: reference frequency, in per cent. The low-frequency whole-body case (Wf)
#: is allowed the wider one.
INDICATION_TOLERANCE_PERCENT = 4.0
LOW_FREQUENCY_INDICATION_TOLERANCE_PERCENT = 5.0

#: The weighting whose application is low-frequency whole-body vibration, and
#: which therefore takes the wider indication tolerance of Table 2.
LOW_FREQUENCY_WEIGHTING = "Wf"


def indication_tolerance_percent(name: str) -> float:
    """The Table 2 indication tolerance at the reference frequency.

    :param name: One of :data:`~phonometry.vibration.WEIGHTING_NAMES`.
    :return: The permitted deviation of the indication, in per cent.
    :raises ValueError: If the weighting is not one of the nine.
    """
    weighting = require_choice(str(name), "name", WEIGHTING_NAMES)
    if weighting == LOW_FREQUENCY_WEIGHTING:
        return LOW_FREQUENCY_INDICATION_TOLERANCE_PERCENT
    return INDICATION_TOLERANCE_PERCENT


def weighting_tolerance_percent(
    name: str, frequencies: ArrayLike
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The Table 5 band around a weighting, region by region.

    :param name: One of :data:`~phonometry.vibration.WEIGHTING_NAMES`.
    :param frequencies: Frequencies at which the band is wanted, in hertz.
    :return: ``(upper, lower)`` percentages, elementwise. ``lower`` is
        :data:`UNCONSTRAINED_BELOW` outside the two outer transition
        frequencies, where the standard sets no lower limit at all.
    :raises ValueError: If the weighting is not one of the nine, or a
        frequency is not positive and finite.
    """
    weighting = require_choice(str(name), "name", WEIGHTING_NAMES)
    f = np.asarray(frequencies, dtype=np.float64)
    if f.size and not np.all(np.isfinite(f) & (f > 0.0)):
        msg = "'frequencies' must be positive and finite."
        raise ValueError(msg)
    ft1, ft2, ft3, ft4 = TRANSITION_FREQUENCIES_HZ[weighting]

    upper = np.full(f.shape, TAIL_TOLERANCE_PERCENT[0], dtype=np.float64)
    lower = np.full(f.shape, TAIL_TOLERANCE_PERCENT[1], dtype=np.float64)
    skirt = ((f > ft1) & (f < ft2)) | ((f > ft3) & (f < ft4))
    central = (f >= ft2) & (f <= ft3)
    upper[skirt], lower[skirt] = SKIRT_TOLERANCE_PERCENT[:2]
    upper[central], lower[central] = CENTRAL_TOLERANCE_PERCENT[:2]
    return upper, lower


def phase_tolerance_degrees(name: str, frequencies: ArrayLike) -> NDArray[np.float64]:
    """The Table 5 characteristic phase-deviation band, region by region.

    Footnote a of the table limits this to instruments that provide a
    measurement parameter not based on r.m.s. values, which is why it is a
    separate function rather than a third array beside the magnitudes: an
    r.m.s.-only meter is not graded on phase at all.

    :param name: One of :data:`~phonometry.vibration.WEIGHTING_NAMES`.
    :param frequencies: Frequencies at which the band is wanted, in hertz.
    :return: The permitted deviation, in degrees, infinite in the two tails.
    :raises ValueError: As for :func:`weighting_tolerance_percent`.
    """
    weighting = require_choice(str(name), "name", WEIGHTING_NAMES)
    f = np.asarray(frequencies, dtype=np.float64)
    if f.size and not np.all(np.isfinite(f) & (f > 0.0)):
        msg = "'frequencies' must be positive and finite."
        raise ValueError(msg)
    ft1, ft2, ft3, ft4 = TRANSITION_FREQUENCIES_HZ[weighting]
    limits = np.full(f.shape, TAIL_TOLERANCE_PERCENT[2], dtype=np.float64)
    limits[((f > ft1) & (f < ft2)) | ((f > ft3) & (f < ft4))] = SKIRT_TOLERANCE_PERCENT[
        2
    ]
    limits[(f >= ft2) & (f <= ft3)] = CENTRAL_TOLERANCE_PERCENT[2]
    return limits


@dataclass(frozen=True)
class WeightingVerification:
    """One measured weighting response against its ISO 8041-1 tolerances.

    :ivar weighting: The weighting the response was measured for.
    :ivar frequencies_hz: The frequencies it was measured at.
    :ivar measured: The measured weighting factors, as supplied.
    :ivar design: The design-goal factors of ISO 8041-1 Table 3 at the same
        frequencies.
    :ivar deviation_percent: ``(measured / design - 1) * 100`` elementwise,
        which is the quantity the standard's acceptance test is written in.
    :ivar within_tolerance: Whether each frequency is inside its band.
    """

    weighting: str
    frequencies_hz: NDArray[np.float64]
    measured: NDArray[np.float64]
    design: NDArray[np.float64]
    deviation_percent: NDArray[np.float64]
    within_tolerance: NDArray[np.bool_]

    @property
    def passes(self) -> bool:
        """Whether every measured frequency sits inside its band.

        True says the frequency weighting meets ISO 8041-1, and nothing more:
        the indication, linearity, overload and environmental tests of the
        same standard are hardware measurements this cannot stand in for.
        """
        return bool(np.all(self.within_tolerance))

    @property
    def failing_frequencies_hz(self) -> NDArray[np.float64]:
        """The frequencies whose deviation falls outside the band."""
        return np.asarray(self.frequencies_hz[~self.within_tolerance], dtype=np.float64)

    @property
    def worst_deviation_percent(self) -> float:
        """The largest deviation in magnitude, signed as it was measured."""
        if self.deviation_percent.size == 0:
            return 0.0
        worst = int(np.argmax(np.abs(self.deviation_percent)))
        return float(self.deviation_percent[worst])

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the measured response inside the tolerance band.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_weighting_verification`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_weighting_verification

        check_language(language)
        return plot_weighting_verification(self, ax, language=language, **kwargs)


def verify_weighting(
    name: str, frequencies: ArrayLike, measured_factors: ArrayLike
) -> WeightingVerification:
    """Check a measured weighting response against ISO 8041-1 Tables 4 and 5.

    The acceptance test is the one Annex B is written in: the deviation
    ``(measured / design - 1) * 100`` at each frequency has to sit between the
    lower and upper limits of the region that frequency falls in.

    :param name: One of :data:`~phonometry.vibration.WEIGHTING_NAMES`.
    :param frequencies: The frequencies the response was measured at, in
        hertz.
    :param measured_factors: The measured weighting factors, linear and not in
        decibels, one per frequency.
    :return: The verdict, as a :class:`WeightingVerification`.
    :raises ValueError: If the weighting is not one of the nine, if the two
        arrays do not have the same shape, if a frequency is not positive and
        finite, or if a measured factor is negative or not finite.
    """
    weighting = require_choice(str(name), "name", WEIGHTING_NAMES)
    f = np.atleast_1d(np.asarray(frequencies, dtype=np.float64))
    measured = np.atleast_1d(np.asarray(measured_factors, dtype=np.float64))
    require_equal_shapes(
        "verify_weighting",
        {"frequencies": f.shape, "measured_factors": measured.shape},
        quantity="frequency",
    )
    if not np.all(np.isfinite(f) & (f > 0.0)):
        msg = "'frequencies' must be positive and finite."
        raise ValueError(msg)
    if not np.all(np.isfinite(measured) & (measured >= 0.0)):
        msg = "'measured_factors' must be non-negative and finite."
        raise ValueError(msg)

    design = np.atleast_1d(np.asarray(weighting_factors(weighting, f), np.float64))
    deviation = (measured / design - 1.0) * 100.0
    upper, lower = weighting_tolerance_percent(weighting, f)
    # The lower limit of the two tails is -100 %, which admits every
    # non-negative factor, so the comparison there is satisfied by
    # construction rather than by a special case.
    within = (deviation <= upper) & (deviation >= lower)
    return WeightingVerification(
        weighting=weighting,
        frequencies_hz=f,
        measured=measured,
        design=design,
        deviation_percent=deviation,
        within_tolerance=np.asarray(within, dtype=np.bool_),
    )


def reference_indication(name: str) -> float:
    """The weighted indication a conforming meter shows at the reference.

    Table 1 pairs each application with a reference frequency and a reference
    r.m.s. acceleration, and the weightings are not unity there, so the
    expected indication is the product of the two.

    :param name: One of :data:`~phonometry.vibration.WEIGHTING_NAMES`.
    :return: The weighted acceleration, in metres per second squared.
    :raises ValueError: If the weighting is not one of the nine.
    """
    weighting = require_choice(str(name), "name", WEIGHTING_NAMES)
    factor = float(
        np.asarray(weighting_factors(weighting, [REFERENCE_FREQUENCY_HZ[weighting]]))[0]
    )
    return REFERENCE_ACCELERATION_M_S2[weighting] * factor
