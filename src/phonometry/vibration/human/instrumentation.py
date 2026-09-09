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
(Table 4). Table 5 prints five rows across them and they carry three
distinct limit pairs, because the two skirts share theirs and so do the two
tails: inside the central region the magnitude may differ by ``+12 %`` /
``−11 %``; in the two skirts by ``+26 %`` / ``−21 %``; beyond the outermost
pair the standard stops
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

**The band does not widen; the measurement does.** Two sentences of the
standard talk about expanded uncertainty and they are not the same sentence.
5.6.6 (printed folio 14) says the Table 5 limits already "include the
applicable maximum expanded uncertainties of measurement", which is why
:func:`weighting_tolerance_percent` returns the printed numbers and never
adds to them. 13.1 (folio 42) and 14.1 (folio 48) say something else, word
for word in both: compliance is demonstrated when the measured deviation,
"extended by the actual expanded uncertainty of measurement of the testing
laboratory", does not exceed those limits. That second rule is about the
laboratory's own uncertainty, it moves the deviation rather than the band,
and it is what ``expanded_uncertainty_percent`` does in
:func:`verify_weighting`.

**Phase is graded on a slope, not on an angle.** Footnote a of Table 5 limits
the phase criterion to instruments reporting a parameter not based on r.m.s.
values, and 5.6.6 explains why the criterion is not the phase error itself:
a constant group delay is a large phase error that changes no measured
quantity. Formula (6) (folio 15) turns a pair of adjacent phase errors into
the characteristic phase deviation the table actually grades, and
:func:`verify_phase_response` is that comparison.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.validation import (
    require_choice,
    require_equal_shapes,
    require_finite_array,
    require_positive_array,
)
from .exposure import (
    WEIGHTING_NAMES,
    HumanVibrationWarning,
    band_limiting_factors,
    frequency_weighting,
    weighting_factors,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

#: Table 4: the four transition frequencies, in hertz, that key the tolerance
#: regions of Table 5 to a weighting. The standard prints them as powers
#: ``10**(k/10)``, so they are built that way here rather than from the
#: What the three entry points that take a frequency vector refuse it for.
#: One text, so a caller matching on it matches all three.
_FREQUENCIES_MSG = "'frequencies' must be positive and finite."

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

#: Table 1: the nominal frequency range of each weighting, in hertz, as the
#: ``(lower, upper)`` pair the column prints. These are the nominal values
#: printed in the table (``8 to 1 000``, ``0,5 to 80``, ``1 to 80``,
#: ``0,1 to 0,5``), not the exact one-third-octave centres ``10**(k/10)``
#: that Annex B tabulates the response at, and they are deliberately kept
#: that way: 5.7, 5.10, 12.11 and the Table 15 test grids all read "for all
#: frequencies in the appropriate nominal frequency range", so the range is
#: an interval named by round numbers rather than a band centre. The nominal
#: 8 Hz that opens the hand-transmitted range is the band centred on
#: ``10**(9/10) = 7,943`` Hz, which is why the printed lower bound is 8 and
#: the first Annex B row inside it is not.
NOMINAL_FREQUENCY_RANGE_HZ: dict[str, tuple[float, float]] = {
    "Wb": (0.5, 80.0),
    "Wc": (0.5, 80.0),
    "Wd": (0.5, 80.0),
    "We": (0.5, 80.0),
    "Wf": (0.1, 0.5),
    "Wh": (8.0, 1000.0),
    "Wj": (0.5, 80.0),
    "Wk": (0.5, 80.0),
    "Wm": (1.0, 80.0),
}

#: The coverage factor the expanded uncertainty of a conformance measurement
#: is calculated with. 13.1 (folio 42) and 14.1 (folio 48) both print
#: ``k = 2``; 12.1 (folio 28) prints "a coverage factor of no less than 2",
#: so 2 is the floor for pattern evaluation and the exact value for the other
#: two clauses. It carries the number of its standard because it is not the
#: only coverage factor the library publishes:
#: :data:`phonometry.hearing.COVERAGE_FACTOR` is the 1,65 of ISO 9612, and a
#: bare ``COVERAGE_FACTOR`` in a second domain would read as the same number.
ISO8041_COVERAGE_FACTOR = 2.0

#: The maximum expanded uncertainty of measurement, in per cent, that each
#: test clause permits a testing laboratory. 12.1 (folio 28) says what the
#: table is for: "Testing laboratories shall not perform tests to demonstrate
#: conformance to the specifications of this document if their actual expanded
#: uncertainties of measurement exceed the maximum permitted values."
#:
#: The keys are clause numbers of ISO 8041-1:2017. Two clauses print two
#: different figures, one for the reference measurement range and one for the
#: additional ranges, and carry two keys rather than one number that would be
#: wrong on one of them. Clauses absent from the table are the ones that print
#: no figure; 12.20.2 is deliberately absent because the uncertainties it
#: prints are ``0,5 °C`` and ``10 %`` relative humidity, which are
#: uncertainties of the environmental conditions rather than of a deviation
#: from a design goal.
MAX_EXPANDED_UNCERTAINTY_PERCENT: dict[str, float] = {
    "12.7": 2.0,  # folio 29, indication at the reference frequency
    "12.10.1": 2.0,  # folio 31, electrical amplitude linearity
    "12.10.2": 3.0,  # folio 32, mechanical linearity, reference range
    "12.10.2 additional ranges": 4.0,  # folio 33, the other ranges
    "12.11.2": 4.5,  # folio 34, mechanical frequency response
    "12.11.3": 3.0,  # folio 35, electrical frequency response
    "12.11.4": 5.0,  # folio 35, the overall response that combines them
    "12.13": 3.0,  # folio 36, signal-burst response
    "12.14": 2.0,  # folio 36, overload indication
    "12.18": 0.01,  # folio 37, timing facilities
    "13.9": 2.0,  # folio 44, indication, one-off instrument
    "13.11": 4.0,  # folio 46, linearity and frequency response, one-off
    "13.14": 2.0,  # folio 47, overload indication, one-off
    "13.15": 0.01,  # folio 47, timing facilities, one-off
    "14.9": 5.0,  # folio 51, linearity and frequency response, periodic
}

#: Table 2: how far the indication itself may sit from the true value at the
#: reference frequency, in per cent. The low-frequency whole-body case (Wf)
#: is allowed the wider one.
INDICATION_TOLERANCE_PERCENT = 4.0
LOW_FREQUENCY_INDICATION_TOLERANCE_PERCENT = 5.0

#: The weighting whose application is low-frequency whole-body vibration, and
#: which therefore takes the wider indication tolerance of Table 2.
LOW_FREQUENCY_WEIGHTING = "Wf"

#: Table 2, second row (folio 12): the indicated frequency-weighted value and
#: the indicated band-limiting value multiplied by the appropriate weighting
#: factor may differ by 3 %, for a steady sinusoid at the reference frequency
#: and reference vibration value. 12.7 (folio 30) repeats the identity as the
#: test procedure. See :func:`band_limited_weighting_factor` for which factor
#: makes the row satisfiable.
WEIGHTING_CONSISTENCY_TOLERANCE_PERCENT = 3.0

#: Table 2, third row (folio 12): the running r.m.s. indication and the linear
#: time-averaged r.m.s. value, both with the band-limiting weighting, may
#: differ by 2 % over any measurement time. Part 1 only: the Table 2 of
#: ISO 8041-2 (folio 8) has two rows rather than three, because its 5.13
#: declares the running r.m.s. "Not applicable for PVEM".
RUNNING_RMS_CONSISTENCY_TOLERANCE_PERCENT = 2.0


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
        msg = _FREQUENCIES_MSG
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
        msg = _FREQUENCIES_MSG
        raise ValueError(msg)
    ft1, ft2, ft3, ft4 = TRANSITION_FREQUENCIES_HZ[weighting]
    limits = np.full(f.shape, TAIL_TOLERANCE_PERCENT[2], dtype=np.float64)
    limits[((f > ft1) & (f < ft2)) | ((f > ft3) & (f < ft4))] = SKIRT_TOLERANCE_PERCENT[
        2
    ]
    limits[(f >= ft2) & (f <= ft3)] = CENTRAL_TOLERANCE_PERCENT[2]
    return limits


def _checked_uncertainty(value: float | None, name: str) -> float:
    """Validate a laboratory expanded uncertainty and default it to zero.

    :param value: The uncertainty as the caller supplied it, or ``None``.
    :param name: The parameter name, for the error message.
    :return: The uncertainty as a float; ``0.0`` for ``None``.
    :raises ValueError: If it is negative or not finite. An uncertainty that
        is not a number is refused rather than dropped, because dropping it
        would hand back the verdict 13.1 says is not enough.
    """
    if value is None:
        return 0.0
    uncertainty = float(value)
    if not math.isfinite(uncertainty) or uncertainty < 0.0:
        msg = f"'{name}' must be non-negative and finite; got {value!r}."
        raise ValueError(msg)
    return uncertainty


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
    :ivar within_tolerance: Whether each frequency is inside its band, with
        the deviation extended by ``expanded_uncertainty_percent`` as 13.1
        and 14.1 require.
    :ivar expanded_uncertainty_percent: The testing laboratory's own expanded
        uncertainty, in per cent, that the verdict was reached with. ``0,0``
        when the caller supplied none, which compares the bare deviation.
    """

    weighting: str
    frequencies_hz: NDArray[np.float64]
    measured: NDArray[np.float64]
    design: NDArray[np.float64]
    deviation_percent: NDArray[np.float64]
    within_tolerance: NDArray[np.bool_]
    expanded_uncertainty_percent: float = 0.0

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
    name: str,
    frequencies: ArrayLike,
    measured_factors: ArrayLike,
    *,
    expanded_uncertainty_percent: float | None = None,
) -> WeightingVerification:
    """Check a measured weighting response against ISO 8041-1 Tables 4 and 5.

    The acceptance test is the one Annex B is written in: the deviation
    ``(measured / design - 1) * 100`` at each frequency has to sit between the
    lower and upper limits of the region that frequency falls in.

    **Where the laboratory's uncertainty goes.** 13.1 (folio 42) and 14.1
    (folio 48) print the same sentence: compliance is demonstrated when the
    result of a measurement of a deviation from a design goal, "extended by
    the actual expanded uncertainty of measurement of the testing laboratory",
    does not exceed the specified tolerance limits, the uncertainty being
    calculated with the coverage factor ``k = 2``
    (:data:`ISO8041_COVERAGE_FACTOR`). So the comparison is
    ``deviation + U <= upper`` and ``deviation - U >= lower``: the band stays
    where Table 5 prints it and the measurement is what widens. That is not in
    conflict with 5.6.6 (folio 14), which says the Table 5 limits already
    include the applicable *maximum permitted* expanded uncertainties: the
    band is not widened by either sentence, and what 13.1 adds is the
    laboratory's *actual* uncertainty, which is its own number and is bounded
    by :data:`MAX_EXPANDED_UNCERTAINTY_PERCENT`.

    :param name: One of :data:`~phonometry.vibration.WEIGHTING_NAMES`.
    :param frequencies: The frequencies the response was measured at, in
        hertz.
    :param measured_factors: The measured weighting factors, linear and not in
        decibels, one per frequency.
    :param expanded_uncertainty_percent: The testing laboratory's actual
        expanded uncertainty of the deviation measurement, in per cent and
        already expanded with ``k = 2``. ``None`` (the default) compares the
        bare deviation, which is the right reading only for a measurement
        whose uncertainty has been shown to be negligible.
    :return: The verdict, as a :class:`WeightingVerification`.
    :raises ValueError: If the weighting is not one of the nine, if the two
        arrays do not have the same shape, if a frequency is not positive and
        finite, if a measured factor is negative or not finite, or if the
        expanded uncertainty is negative or not finite.
    """
    weighting = require_choice(str(name), "name", WEIGHTING_NAMES)
    uncertainty = _checked_uncertainty(
        expanded_uncertainty_percent, "expanded_uncertainty_percent"
    )
    f = np.atleast_1d(np.asarray(frequencies, dtype=np.float64))
    measured = np.atleast_1d(np.asarray(measured_factors, dtype=np.float64))
    require_equal_shapes(
        "verify_weighting",
        {"frequencies": f.shape, "measured_factors": measured.shape},
        quantity="frequency",
    )
    if not np.all(np.isfinite(f) & (f > 0.0)):
        msg = _FREQUENCIES_MSG
        raise ValueError(msg)
    if not np.all(np.isfinite(measured) & (measured >= 0.0)):
        msg = "'measured_factors' must be non-negative and finite."
        raise ValueError(msg)

    design = np.atleast_1d(np.asarray(weighting_factors(weighting, f), np.float64))
    deviation = (measured / design - 1.0) * 100.0
    upper, lower = weighting_tolerance_percent(weighting, f)
    # The -100 % of the two tails is the absence of a lower limit rather than
    # a wide one, so it is the one place the laboratory's uncertainty must not
    # be subtracted: a response of exactly zero deviates by -100 % and still
    # conforms, and -100 - U would reject it for being measured carefully.
    unconstrained = lower <= UNCONSTRAINED_BELOW
    within = (deviation + uncertainty <= upper) & (
        unconstrained | (deviation - uncertainty >= lower)
    )
    return WeightingVerification(
        weighting=weighting,
        frequencies_hz=f,
        measured=measured,
        design=design,
        deviation_percent=deviation,
        within_tolerance=np.asarray(within, dtype=np.bool_),
        expanded_uncertainty_percent=uncertainty,
    )


#: How many frequencies Formula (6) needs to produce anything: it is written
#: on the pair ``f(n)``, ``f(n+1)``.
_FORMULA_6_FREQUENCIES = 2


def _require_a_pair_of_ascending_frequencies(
    frequencies_hz: NDArray[np.float64], owner: str
) -> None:
    """Require what Formula (6) needs: two frequencies, and an order.

    :param frequencies_hz: The already validated frequencies, in hertz.
    :param owner: Name of the entry point, for the error message.
    :raises ValueError: If there is only one frequency, or if two of them are
        equal or out of order. The formula divides by ``f(n+1) - f(n)``, so an
        unordered grid is not a grid it can be evaluated on, and sorting one
        silently would pair up phase errors the caller never measured together.
    """
    if frequencies_hz.size < _FORMULA_6_FREQUENCIES:
        msg = (
            f"{owner}: 'frequencies_hz' must hold at least two frequencies; "
            f"Formula (6) is about a pair of adjacent bands, and got "
            f"{frequencies_hz.size}."
        )
        raise ValueError(msg)
    if not np.all(np.diff(frequencies_hz) > 0.0):
        msg = (
            f"{owner}: 'frequencies_hz' must increase strictly, because "
            f"Formula (6) divides by the difference between adjacent ones."
        )
        raise ValueError(msg)


#: The widest step 12.11.1 allows a frequency-response test to be made in, as
#: a ratio: "in steps of not more than one-third octave across the frequency
#: ranges specified in Table 15" (folio 33). The one-third octave of Formula
#: (B.1) is a ratio of ``10 ** (1 / 10)``.
_WIDEST_STEP_RATIO = 10.0 ** (1.0 / 10.0)

#: Slack on that ratio, so a grid built from the printed decimals rather than
#: from the exponents is not refused for its last digit.
_STEP_RATIO_SLACK = 1e-6


def _require_a_third_octave_grid(
    frequencies_hz: NDArray[np.float64], owner: str
) -> None:
    """Require the grid 12.11.1 prints, because the design is rebuilt on it.

    The design-goal phase runs off one continuous branch, and it is recovered
    from the principal value by following it frequency to frequency. That
    recovery needs the steps the standard already asks for: on a coarser grid
    a step of more than half a turn is indistinguishable from the next branch,
    the whole design lands 360 degrees away, and Formula (6) turns that offset
    on a widely spaced pair into a few degrees, which can sit inside the
    tolerance. The failure is silent and it can go either way, so it is
    refused rather than warned about.

    :param frequencies_hz: The already validated ascending frequencies, in
        hertz.
    :param owner: Name of the entry point, for the error message.
    :raises ValueError: If two adjacent frequencies are more than one third of
        an octave apart.
    """
    ratios = frequencies_hz[1:] / frequencies_hz[:-1]
    worst = float(np.max(ratios))
    if worst > _WIDEST_STEP_RATIO * (1.0 + _STEP_RATIO_SLACK):
        msg = (
            f"{owner}: 'frequencies_hz' steps by a ratio of up to {worst:.4g}, "
            f"and ISO 8041-1:2017 12.11.1 asks for steps of not more than one "
            f"third of an octave ({_WIDEST_STEP_RATIO:.4g}). The design-goal "
            f"phase is rebuilt on the grid it is given, and on a coarser one "
            f"it can land a whole turn away without the verdict noticing."
        )
        raise ValueError(msg)


def characteristic_phase_deviation(
    frequencies_hz: ArrayLike, phase_deviation_deg: ArrayLike
) -> NDArray[np.float64]:
    r"""The characteristic phase deviation of ISO 8041-1 Formula (6).

    5.6.6 (printed folio 14) says why the phase error itself is not the
    criterion: "the errors in measurement due to errors in the phase response
    are dependent on the rate of change in phase error with frequency, rather
    than the absolute phase error itself". Formula (6) (folio 15) is that rate,
    printed inside absolute-value bars:

    .. math::

        \Delta\varphi_0 = \left\lvert
        \frac{f_n \, \Delta\varphi_{n+1} - f_{n+1} \, \Delta\varphi_n}
             {f_{n+1} - f_n} \right\rvert

    The normative Annex H closes the two questions the clause leaves open.
    Formula (H.3) (folio 93) prints the same quantity with the two products
    exchanged, which is the same number inside the bars both formulae carry,
    and it says where the number belongs: "This allows the calculation of
    Δφ0(f_n) at each frequency f_n except for the highest frequency". So ``N``
    frequencies give ``N - 1`` values, each attributed to the lower frequency
    of its pair, and that is what decides which Table 5 region grades a pair
    that straddles a transition frequency: the region of ``f_n``.

    Two closed forms say what the quantity measures. A constant phase error of
    ``c`` degrees gives ``|c|`` at every pair, so an offset is graded at face
    value. A phase error proportional to frequency, which is a constant group
    delay, gives exactly zero, and NOTE 1 of H.2.1 is that reading: a constant
    group delay "would probably far exceed the tolerances on phase deviation,
    but would influence neither the vibration parameters to be measured nor
    the characteristic phase deviation values".

    :param frequencies_hz: The frequencies the phase errors belong to, in
        hertz, strictly ascending. H.2.1 asks for them "preferably in steps of
        one-third octaves", which is the grid Annex B tabulates.
    :param phase_deviation_deg: The phase error at each frequency, in degrees,
        measured minus design goal.
    :return: One value per adjacent pair, in degrees, attributed to the lower
        frequency of the pair, so of length one less than the input.
    :raises ValueError: If the two arrays do not have the same shape, if a
        frequency is not positive and finite, if a phase deviation is not
        finite, or if there are fewer than two frequencies or they do not
        strictly ascend.
    """
    f = require_positive_array(frequencies_hz, "frequencies_hz")
    deviation = require_finite_array(phase_deviation_deg, "phase_deviation_deg")
    require_equal_shapes(
        "characteristic_phase_deviation",
        {"frequencies_hz": f.shape, "phase_deviation_deg": deviation.shape},
        quantity="frequency",
    )
    _require_a_pair_of_ascending_frequencies(f, "characteristic_phase_deviation")
    lower, upper = f[:-1], f[1:]
    characteristic = np.abs(
        (lower * deviation[1:] - upper * deviation[:-1]) / (upper - lower)
    )
    return np.asarray(characteristic, dtype=np.float64)


#: Where NOTE 2 of H.2.1 stops vouching for Formula (H.4): it "is an
#: approximation to numerical results and applies to small Δφ0 values only
#: (< 30°)".
_PEAK_APPROXIMATION_LIMIT_DEG = 30.0

#: The coefficient Formula (H.4) prints in front of the sine.
_PEAK_DEVIATION_COEFFICIENT = 0.48


def peak_deviation_percent(characteristic_phase_deviation_deg: ArrayLike) -> float:
    r"""The peak-value deviation a phase response costs (Formula (H.4)).

    Annex H is normative, and (H.4) (folio 93) is the only worked number in
    the whole phase argument:

    .. math::

        \Delta P_{\max} \approx \pm \max\{0{,}48 \sin \Delta\varphi_0(f_n)\}
        \times 100 \, \%

    followed by "For the maximum characteristic phase deviations of 12°, the
    maximum peak value deviation is approximately 10 %". The maximum is inside
    the printed formula, so this returns one number for a whole response
    rather than one per frequency: ``ΔP_max`` is what the worst pair costs.

    NOTE 2 of H.2.1 fences the approximation twice, and both fences matter to
    a reader of the returned number. It "applies to small Δφ0 values only
    (< 30°)", which is why a larger value is passed on with a warning rather
    than silently. And it is a worst case: "Depending on the signal waveform,
    the actual peak value deviation will normally be smaller than ΔP_max
    which is a worst-case estimate, combining the amplitudes and zero phase
    angles of two frequency components in the most unfavourable manner."

    :param characteristic_phase_deviation_deg: One or more characteristic
        phase deviations, in degrees, as
        :func:`characteristic_phase_deviation` returns them.
    :return: The likely maximum peak-value deviation, in per cent. The
        printed ``±`` is the sign of the deviation, not part of the size, so
        the number returned is the magnitude.
    :raises ValueError: If a value is negative or not finite. Formula (6)
        prints the quantity inside absolute-value bars, so a negative one is
        not a characteristic phase deviation and is refused rather than
        folded.
    :raises UserWarning: :class:`~phonometry.vibration.HumanVibrationWarning`
        when a value exceeds the 30 degrees NOTE 2 limits the approximation to.
    """
    deviations = require_finite_array(
        characteristic_phase_deviation_deg, "characteristic_phase_deviation_deg"
    )
    if np.any(deviations < 0.0):
        msg = (
            "'characteristic_phase_deviation_deg' must be non-negative: "
            "Formula (6) prints the quantity inside absolute-value bars."
        )
        raise ValueError(msg)
    worst = float(np.max(deviations))
    if worst >= _SINE_ORDERING_LIMIT_DEG:
        # Past a quarter turn the sine stops ranking pairs, so the maximum
        # inside the printed formula no longer picks the worst one, and past a
        # half turn it goes negative and the returned "magnitude" changes sign.
        # Neither is a peak-value deviation, and NOTE 2 stopped vouching for
        # the approximation four times further back, so this is refused rather
        # than handed over with a warning.
        msg = (
            f"'characteristic_phase_deviation_deg' reaches {worst:.4g} "
            f"degrees, and Formula (H.4) only ranks pairs below "
            f"{_SINE_ORDERING_LIMIT_DEG:g}: its sine is not monotonic past a "
            f"quarter turn and is negative past a half turn, so the maximum "
            f"it prints stops meaning the worst pair. ISO 8041-1:2017 H.2.1 "
            f"NOTE 2 limits it to below "
            f"{_PEAK_APPROXIMATION_LIMIT_DEG:g} degrees in any case."
        )
        raise ValueError(msg)
    if worst >= _PEAK_APPROXIMATION_LIMIT_DEG:
        warnings.warn(
            f"Formula (H.4) is an approximation for characteristic phase "
            f"deviations below {_PEAK_APPROXIMATION_LIMIT_DEG:g} degrees "
            f"(ISO 8041-1:2017, H.2.1, NOTE 2); the largest supplied is "
            f"{worst:.4g} degrees.",
            HumanVibrationWarning,
            stacklevel=2,
        )
    peak = np.max(np.sin(np.radians(deviations)))
    return float(_PEAK_DEVIATION_COEFFICIENT * peak * 100.0)


def _design_phase_deg(
    name: str, frequencies_hz: NDArray[np.float64]
) -> NDArray[np.float64]:
    """The design-goal phase along ascending frequencies, in degrees.

    Formula (H.1) (folio 92) defines the design goal as the argument of
    ``H(s)`` of Formula (5), and says "Values for the phase angle φ are
    included in Tables B.1 to B.9". Those tables print one continuous branch,
    running down from close to ``+180`` degrees at the lowest frequency of
    each table and past ``-180`` at the highest, so the branch is followed
    here rather than the principal value: with it, all 318 printed phase cells
    of Tables B.1 to B.9 are reproduced within their print rounding.

    :param name: One of :data:`~phonometry.vibration.WEIGHTING_NAMES`.
    :param frequencies_hz: Strictly ascending frequencies, in hertz.
    :return: The design-goal phase, in degrees, on the printed branch.
    """
    response = frequency_weighting(name, frequencies_hz).response
    return np.degrees(np.unwrap(np.angle(response))).astype(np.float64)


#: Where Formula (H.4) stops ordering pairs at all. Its sine rises to a
#: quarter turn, falls back to zero at a half turn and is negative beyond, so
#: the maximum the formula prints stops picking the worst pair there and the
#: number stops being a magnitude. Well outside the 30 degrees NOTE 2 vouches
#: for, and refused rather than warned about.
_SINE_ORDERING_LIMIT_DEG = 90.0

#: How close to a half turn every phase error has to sit before the verdict
#: says the measurement looks inverted rather than wrong, in degrees.
_INVERSION_TOLERANCE_DEG = 1.0


def _warn_if_inverted(deviation_deg: NDArray[np.float64]) -> None:
    """Say when a phase error is a polarity, not a phase response.

    An inverted measurement sits half a turn from the design goal at every
    frequency, and Formula (6) grades that constant offset as 180 degrees, so
    it fails the criterion loudly and for the wrong reason. H.2.3.4 k) says
    what the reason is, and that this is not the test for it, so the verdict
    says so rather than letting the number speak for a diagnosis it cannot
    make. A wrapped measurement is not detected here and cannot be: on a
    one-third-octave grid a wrap and the delay ramp of H.2.3.4 n), which the
    criterion is invariant to, are the same jump.

    :param deviation_deg: The phase error at each frequency, in degrees.
    :raises UserWarning: :class:`~phonometry.vibration.HumanVibrationWarning`
        when every one of them is half a turn.
    """
    if np.allclose(
        np.abs(deviation_deg), 180.0, atol=_INVERSION_TOLERANCE_DEG, rtol=0.0
    ):
        warnings.warn(
            "Every phase error is half a turn, which is signal inversion: "
            "ISO 8041-1:2017 H.2.3.4 k) says the characteristic phase "
            "deviation criterion is not applicable to it and that polarity "
            "has its own test.",
            HumanVibrationWarning,
            stacklevel=3,
        )


@dataclass(frozen=True)
class PhaseVerification:
    """One measured phase response against the ISO 8041-1 Table 5 phase band.

    :ivar weighting: The weighting the response was measured for.
    :ivar frequencies_hz: The frequencies it was measured at.
    :ivar measured_phase_deg: The measured phase, as supplied.
    :ivar design_phase_deg: The design-goal phase of Formula (H.1) at the same
        frequencies, on the branch Tables B.1 to B.9 print.
    :ivar deviation_deg: The phase error, measured minus design, in degrees.
    :ivar characteristic_frequencies_hz: The frequencies the characteristic
        phase deviations are attributed to, which are all but the highest
        (H.2.1, Formula (H.3)).
    :ivar characteristic_deviation_deg: The characteristic phase deviation of
        Formula (6) at each of those, in degrees.
    :ivar tolerance_deg: The Table 5 limit at each of those, in degrees,
        infinite in the two tails.
    :ivar within_tolerance: Whether each characteristic phase deviation is
        inside its limit.
    """

    weighting: str
    frequencies_hz: NDArray[np.float64]
    measured_phase_deg: NDArray[np.float64]
    design_phase_deg: NDArray[np.float64]
    deviation_deg: NDArray[np.float64]
    characteristic_frequencies_hz: NDArray[np.float64]
    characteristic_deviation_deg: NDArray[np.float64]
    tolerance_deg: NDArray[np.float64]
    within_tolerance: NDArray[np.bool_]

    @property
    def passes(self) -> bool:
        """Whether every characteristic phase deviation sits inside Table 5.

        True says the phase response meets the criterion of footnote a of
        Table 5, which is the one an instrument reporting peak, MTVV or VDV is
        held to. An r.m.s.-only instrument is not graded on phase at all, and
        this is not a verdict on its magnitude response.
        """
        return bool(np.all(self.within_tolerance))

    @property
    def failing_frequencies_hz(self) -> NDArray[np.float64]:
        """The frequencies whose characteristic phase deviation is too large."""
        return np.asarray(
            self.characteristic_frequencies_hz[~self.within_tolerance],
            dtype=np.float64,
        )

    @property
    def peak_deviation_percent(self) -> float:
        """What this phase response costs a peak reading (Formula (H.4)).

        The worst case over the measured range, which is where the maximum in
        the printed formula is taken.
        """
        return peak_deviation_percent(self.characteristic_deviation_deg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the characteristic phase deviation inside the Table 5 band.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_phase_verification`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_phase_verification

        check_language(language)
        return plot_phase_verification(self, ax, language=language, **kwargs)


def verify_phase_response(
    name: str, frequencies_hz: ArrayLike, measured_phase_deg: ArrayLike
) -> PhaseVerification:
    """Check a measured phase response against the ISO 8041-1 Table 5 band.

    Table 5 (folio 15) prints a characteristic phase deviation limit beside
    every magnitude limit: ``±6°`` in the central region, ``±12°`` in the two
    skirts and ``±∞`` in the two tails. The quantity those grade is not the
    phase error but Formula (6) of it, which is why this is a separate entry
    point from :func:`verify_weighting` rather than a third array inside it:
    footnote a of the table applies the phase criterion only to instruments
    "that provide measurement parameters that are not based on r.m.s. values",
    so an r.m.s.-only meter is never handed this verdict.

    The design goal comes from Formula (H.1), which is the argument of the
    same ``H(s)`` :func:`~phonometry.vibration.frequency_weighting` evaluates,
    and it is put on the branch Tables B.1 to B.9 print, so the measurement
    has to arrive on a continuous branch too. That is not a convenience: the
    two invariances the standard prints for this criterion hold on the
    continuous phase error and on no other. A constant phase error of ``c``
    degrees is graded as ``c``; a constant group delay, which is a phase error
    proportional to frequency, is graded as zero, and H.2.3.4 n) is explicit
    that "any remaining constant delay time (except 180°) does not influence
    the result at all". Fold the error into a half turn either side of zero
    and the second one stops being true, which is why nothing is folded here.
    H.2.3.4 g) to m) is the standard's own reconstruction of that continuous
    curve from wrapped phase-meter readings, and it belongs before this call:
    on a one-third-octave grid a wrap and a delay ramp are the same jump, so
    no check here could tell a measurement still carrying its wraps from the
    delay the criterion is meant to ignore.

    **What a polarity error looks like here, and why it is not this test.**
    H.2.3.4 k) (folio 99) says a half-turn shift of every component "leaves
    the wave form of the signal unchanged, but would create catastrophic
    results attempting to apply the characteristic phase deviation (CPD)
    criterion", and that the criterion "is not applicable to signal inversion.
    Signal inversion is a unique form of signal processing which needs its own
    test procedure, the polarity test". An inverted measurement therefore
    fails this check with a 180-degree deviation everywhere, and is warned
    about, because the verdict is real but the diagnosis is a polarity test
    this function does not perform.

    :param name: One of :data:`~phonometry.vibration.WEIGHTING_NAMES`.
    :param frequencies_hz: The frequencies the phase was measured at, in
        hertz, strictly ascending and at least two of them.
    :param measured_phase_deg: The measured phase at each frequency, in
        degrees, on the continuous branch Tables B.1 to B.9 print.
    :return: The verdict, as a :class:`PhaseVerification`.
    :raises ValueError: If the weighting is not one of the nine, if the two
        arrays do not have the same shape, if a frequency is not positive and
        finite, if a phase is not finite, or if there are fewer than two
        frequencies or they do not strictly ascend.
    :raises UserWarning: :class:`~phonometry.vibration.HumanVibrationWarning`
        when every phase error is a half turn, which is an inverted signal
        rather than a phase response the criterion can grade.
    """
    weighting = require_choice(str(name), "name", WEIGHTING_NAMES)
    f = require_positive_array(frequencies_hz, "frequencies_hz")
    measured = require_finite_array(measured_phase_deg, "measured_phase_deg")
    require_equal_shapes(
        "verify_phase_response",
        {"frequencies_hz": f.shape, "measured_phase_deg": measured.shape},
        quantity="frequency",
    )
    _require_a_pair_of_ascending_frequencies(f, "verify_phase_response")
    _require_a_third_octave_grid(f, "verify_phase_response")

    design = _design_phase_deg(weighting, f)
    deviation = np.asarray(measured - design, dtype=np.float64)
    _warn_if_inverted(deviation)
    characteristic = characteristic_phase_deviation(f, deviation)
    tolerance = phase_tolerance_degrees(weighting, f[:-1])
    return PhaseVerification(
        weighting=weighting,
        frequencies_hz=f,
        measured_phase_deg=measured,
        design_phase_deg=design,
        deviation_deg=deviation,
        characteristic_frequencies_hz=np.asarray(f[:-1], dtype=np.float64),
        characteristic_deviation_deg=characteristic,
        tolerance_deg=tolerance,
        within_tolerance=np.asarray(characteristic <= tolerance, dtype=np.bool_),
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


def band_limited_weighting_factor(name: str) -> float:
    r"""The factor that makes the second row of Table 2 satisfiable.

    Table 2 (folio 12) allows 3 % between "the indicated value of any
    frequency-weighted measurement quantity" and "the indicated value of the
    corresponding band-limiting measurement multiplied by the appropriate
    weighting factor", and 12.7 (folio 30) turns it into a procedure: with the
    input adjusted so that the meter indicates the reference vibration value
    *with band-limiting frequency weighting*, the frequency-weighted
    indication "shall equal the indicated band-limited weighted vibration
    value multiplied by the appropriate weighting factor (see Table 1)".

    That test fixes the input at ``a_ref / |H_BL(f_ref)|``, so the weighted
    indication is ``a_ref |H(f_ref)| / |H_BL(f_ref)|``: the factor that makes
    the identity true is the **ratio** of the two responses at the reference
    frequency, which is what this function returns.

    ==========  ==================  ===================
    Weighting   This ratio          Table 1 prints
    ==========  ==================  ===================
    ``Wb``      0,812 819           0,812 6
    ``Wc``      0,514 617           0,514 5
    ``Wd``      0,126 120           0,126 1
    ``We``      0,062 891           0,062 87
    ``Wf``      0,418 982           0,388 8
    ``Wh``      0,202 025           0,202 0
    ``Wj``      1,018 841           1,019
    ``Wk``      0,772 066           0,771 8
    ``Wm``      0,336 336           0,336 2
    ==========  ==================  ===================

    For eight of the nine the distinction is academic: their band-limiting
    weighting is between 0,999 68 and 0,999 97 at their reference frequency,
    so the printed Table 1 factor is the same number to 0,03 %, against a
    tolerance of 3 %. For ``Wf`` it is not. Its reference frequency,
    2,5 rad/s = 0,397 887 Hz, sits inside its own band-limiting skirt (0,08 Hz
    and 0,63 Hz corners, Table 3): the band-limiting weighting is 0,928 078
    there and the overall weighting 0,388 848, values Table B.5 prints as
    0,927 9 and 0,388 4 at the neighbouring 0,398 1 Hz band centre. Reading
    "the appropriate weighting factor" as the 0,388 8 of Table 1 makes a
    *conforming* ``Wf`` meter miss the row by 7,75 %, more than twice the
    tolerance; reading it as the ratio 0,418 982 makes the row true by
    construction. The standard does not define the phrase, and the "(see
    Table 1)" of 12.7 points at the reading that cannot be satisfied; the
    ambiguity is registered in ``docs/ERRATA.md``.

    :param name: One of :data:`~phonometry.vibration.WEIGHTING_NAMES`.
    :return: ``|H(f_ref)| / |H_BL(f_ref)|``, dimensionless.
    :raises ValueError: If the weighting is not one of the nine.
    """
    weighting = require_choice(str(name), "name", WEIGHTING_NAMES)
    frequencies = [REFERENCE_FREQUENCY_HZ[weighting]]
    overall = float(np.asarray(weighting_factors(weighting, frequencies))[0])
    band_limited = float(np.asarray(band_limiting_factors(weighting, frequencies))[0])
    return overall / band_limited


# ---------------------------------------------------------------------------
# Running r.m.s. time weighting: the decay of Tables 10 and 11 (5.13).
# ---------------------------------------------------------------------------
#: The fraction of the initial indicated value the decay is timed down to
#: (5.13, folio 20: "the time at which the indicated value is less than 10 %
#: of the initial value").
_DECAY_FRACTION = 0.1

#: Tables 10 and 11 (folios 20 and 21): the time the indicated running r.m.s.
#: value takes to fall to 10 % of its initial value after a steady reference
#: sinusoid is suddenly shut off, in seconds. One row per printed time
#: constant, ``(integration time, printed time, printed tolerance)``.
RUNNING_RMS_DECAY_TIME_S: dict[str, tuple[tuple[float, float, float], ...]] = {
    "linear": ((0.125, 0.124, 0.005), (1.0, 0.99, 0.05), (8.0, 7.92, 0.2)),
    "exponential": ((0.125, 0.58, 0.03), (1.0, 4.61, 0.25), (8.0, 36.8, 2.0)),
}

#: Table 11 (folio 21): the equivalent decay rate of the exponential average,
#: in decibels per second, as ``(integration time, lower, upper)``. Table 10
#: prints no such column, so this is the exponential average alone.
#:
#: The rate band is not the reciprocal of the time band. The closed-form rate
#: is ``20 lg(e) / (2 tau) = 4,3429 / tau`` dB/s, and the printed limits sit
#: at 0,875 to 0,892 and 1,128 to 1,151 times it, while the printed times map
#: to narrower intervals around ``2 tau ln 10``. The time column is the one
#: that binds; the rate column is the looser statement of the same decay.
RUNNING_RMS_DECAY_RATE_DB_PER_S: tuple[tuple[float, float, float], ...] = (
    (0.125, 31.0, 40.0),
    (1.0, 3.8, 4.9),
    (8.0, 0.48, 0.62),
)


def running_rms_decay_time(integration_time_s: float, *, method: str) -> float:
    r"""When the running r.m.s. falls to 10 % after the signal is shut off.

    5.13 (folio 20) applies a steady sinusoid at the reference frequency for
    at least 5 time constants (linear averaging) or 20 (exponential), shuts it
    off, and times the decay "from the start of the decay to the time at
    which the indicated value is less than 10 % of the initial value".

    Both averages have a closed form. The linear average of Eq. (2) keeps the
    last ``tau`` seconds of the record, so a time ``t`` after the cut its
    window still holds ``(tau - t) / tau`` of the original mean square and the
    indicated value falls as :math:`\sqrt{(\tau - t)/\tau}`, reaching 10 % at
    ``t = 0,99 tau``. The exponential average of Eq. (3) decays in power as
    :math:`e^{-t/\tau}`, so the indication falls as :math:`e^{-t/2\tau}` and
    reaches 10 % at :math:`t = 2\tau\ln 10 = 4,605\,2\,\tau`.

    Both land inside the printed bands of :data:`RUNNING_RMS_DECAY_TIME_S`
    for the three time constants the standard tabulates.

    :param integration_time_s: The averaging time ``tau``, in seconds (> 0).
    :param method: ``"linear"`` (Table 10) or ``"exponential"`` (Table 11),
        the two averages of :func:`~phonometry.vibration.running_rms`.
    :return: The time to 10 % of the initial indicated value, in seconds.
    :raises ValueError: If ``method`` is neither average, or the integration
        time is not positive and finite.
    """
    averaging = require_choice(str(method), "method", ("linear", "exponential"))
    tau = float(integration_time_s)
    if not math.isfinite(tau) or tau <= 0.0:
        msg = "'integration_time_s' must be positive and finite."
        raise ValueError(msg)
    if averaging == "linear":
        return (1.0 - _DECAY_FRACTION**2) * tau
    return -2.0 * math.log(_DECAY_FRACTION) * tau


def verify_running_rms_decay(
    measured_time_s: float, *, integration_time_s: float, method: str
) -> bool:
    """Check a measured decay time against Table 10 or Table 11.

    The verdict is one printed row: the measured time to 10 % of the initial
    value has to sit inside the printed interval for that time constant and
    that average. The rate column of Table 11 is deliberately not the
    criterion, for the reason :data:`RUNNING_RMS_DECAY_RATE_DB_PER_S`
    explains.

    Only the three time constants the two tables print can be checked, so an
    instrument averaging over any other time is refused rather than judged
    against a band the standard does not give.

    :param measured_time_s: The measured time to 10 % of the initial
        indicated value, in seconds (> 0).
    :param integration_time_s: The averaging time it was measured at, which
        has to be one of the printed 0,125 s, 1 s and 8 s. Keyword-only, and
        so is the method: two times in seconds side by side are the kind of
        pair a positional call gets the wrong way round in silence.
    :param method: ``"linear"`` (Table 10) or ``"exponential"`` (Table 11).
    :return: Whether the measurement is inside the printed interval.
    :raises ValueError: If ``method`` is neither average, if the measured time
        is not positive and finite, or if the integration time is not one of
        the three printed time constants.
    """
    averaging = require_choice(str(method), "method", ("linear", "exponential"))
    measured = float(measured_time_s)
    if not math.isfinite(measured) or measured <= 0.0:
        msg = "'measured_time_s' must be positive and finite."
        raise ValueError(msg)
    tau = float(integration_time_s)
    for printed_tau, printed_time, tolerance in RUNNING_RMS_DECAY_TIME_S[averaging]:
        if math.isclose(tau, printed_tau, rel_tol=1e-9, abs_tol=0.0):
            return abs(measured - printed_time) <= tolerance
    printed = ", ".join(f"{row[0]:g}" for row in RUNNING_RMS_DECAY_TIME_S[averaging])
    msg = (
        f"'integration_time_s' must be one of the time constants Tables 10 "
        f"and 11 print ({printed} s); {tau:g} s has no printed decay band."
    )
    raise ValueError(msg)
