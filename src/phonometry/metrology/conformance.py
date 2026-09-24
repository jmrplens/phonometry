#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The conformance rule of IEC TC 29: a deviation, its limits and its uncertainty.

The instrument standards IEC technical committee 29 has written since 2013
decide conformance the same way, and say so in the same sentence. IEC
60942:2017 (sound calibrators) prints it in 5.1.15, A.1.2 and B.1.3, IEC
61672-1:2013 (sound level meters) in 5.1.21, IEC 61672-3:2013 in 4.1 and IEC
61260-2 and -3:2016 (band filters) in their introductions: conformance to a
performance specification is demonstrated when **both** of the following hold,

(a) the measured deviation from the design goal does not exceed the applicable
    acceptance limits, **and**
(b) the actual expanded uncertainty of the measurement, for a coverage
    probability of 95 %, does not exceed the maximum-permitted uncertainty
    the standard prints for that test.

Two things set this rule apart from the older one, which ISO 8041-1:2017 still
uses (13.1 and 14.1) and :func:`phonometry.vibration.verify_weighting`
implements: the uncertainty is not added to the deviation, and the limits are
inclusive. Annex D of IEC 60942 (Figure D.1) shows where the first comes
from: the tolerance limits are not stated, but lie outside the acceptance
limits by a guard band equal to the maximum-permitted uncertainty "for a 95 %
coverage interval". The guard band is what keeps a laboratory whose
uncertainty is no larger than that maximum from passing an instrument outside
its tolerance, and it does so at that coverage, not with certainty: it lowers
the risk of a false acceptance without removing it. The same annex settles
the second in so many words: "a measured
deviation equal to a limit of an acceptance interval demonstrates conformance
to a specification, providing also that the uncertainty of the measurement
from the laboratory performing a test does not exceed the specified
maximum-permitted uncertainty". The uncertainty criterion is inclusive too:
example 7 of IEC 60942 Table E.1 has an actual uncertainty of 0,15 dB against
a maximum of 0,15 dB and conforms.

With two criteria there are four outcomes, and the standards number them the
same way (IEC 60942 E.2.2, IEC 61672-1 C.2.2):

1. deviation within the limits and uncertainty within the maximum: conformance;
2. deviation within the limits but uncertainty above the maximum:
   non-conformance, because the measurement cannot demonstrate anything;
3. deviation outside the limits with an acceptable uncertainty:
   non-conformance;
4. both criteria failed.

:attr:`ConformanceVerification.outcome` is that number and
:attr:`ConformanceVerification.reason` the wording the "Reasons" column of
Table E.1 and Table C.1 gives it, so the eighteen printed examples of the two
tables are reproduced to the letter as well as to the verdict.

The limits may be symmetric, as IEC 60942 writes them (an acceptance limit on
the *absolute* deviation), or asymmetric, as IEC 61672-1 writes most of its own
(+1,0 dB; -1,2 dB in Table C.1). A symmetric limit is given as one number and
an asymmetric pair as ``(lower, upper)``. One end of the pair may be open: the
stop band of IEC 61260-1:2014 Table 1 prints a minimum relative attenuation
and a maximum of :math:`+\infty` ("+70; +∞"), and that is an acceptance
interval with no upper limit, given as ``(70.0, math.inf)``. An interval open
at both ends bounds nothing and is refused.

A deviation that reaches a limit through floating-point arithmetic, such as a
measured 0,2 dB plus a correction of 0,1 dB against a limit of 0,3 dB, sums
to 0,300 000 000 000 000 04 and would be turned away by its last bit. Both
comparisons therefore accept a value within one part in :math:`10^9` of its
bound, which is nine orders of magnitude below any resolution these standards
report a deviation at.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .._internal.validation import require_finite

if TYPE_CHECKING:
    from matplotlib.axes import Axes

__all__ = [
    "ConformanceVerification",
    "verify_conformance",
]

#: Relative slack of the two comparisons, so that a deviation that lands on a
#: limit through floating-point arithmetic is still on it (see the module
#: docstring). One part in a thousand million.
_BOUNDARY_REL_TOL = 1e-9

#: Absolute slack of the two comparisons, for a bound of zero, where a
#: relative tolerance vanishes.
_BOUNDARY_ABS_TOL = 1e-12

#: The four outcomes of IEC 60942:2017 E.2.2 and IEC 61672-1:2013 C.2.2, keyed
#: by (deviation within the limits, uncertainty within the maximum), each with
#: the wording the "Reasons for conformance or non-conformance" column of
#: Tables E.1 and C.1 prints for it.
_OUTCOMES: dict[tuple[bool, bool], tuple[int, str]] = {
    (True, True): (
        1,
        "Deviation within acceptance limits AND uncertainty within maximum-permitted",
    ),
    (True, False): (
        2,
        "Deviation within acceptance limits BUT uncertainty exceeds maximum-permitted",
    ),
    (False, True): (3, "Deviation exceeds acceptance limits"),
    (False, False): (
        4,
        "Deviation exceeds acceptance limits AND uncertainty exceeds maximum-permitted",
    ),
}


def _at_most(value: float, bound: float) -> bool:
    """Whether ``value`` is at or below ``bound``, a last-bit excess forgiven."""
    return value <= bound or math.isclose(
        value, bound, rel_tol=_BOUNDARY_REL_TOL, abs_tol=_BOUNDARY_ABS_TOL
    )


def _open_limit(value: float, name: str, side: float) -> float:
    """An acceptance limit, finite or open on its own side.

    The lower limit may be ``-inf`` and the upper one ``+inf``, which is how a
    table writes an interval bounded on one side only; the other infinity, or
    a NaN, bounds nothing and is refused.

    :param value: The limit.
    :param name: Its field name, for the message.
    :param side: ``-1.0`` for the lower limit, ``+1.0`` for the upper one.
    :raises ValueError: for a NaN or an infinity on the wrong side.
    """
    limit = float(value)
    if math.isinf(limit) and math.copysign(1.0, limit) == side:
        return limit
    return require_finite(limit, name)


@dataclass(frozen=True)
class ConformanceVerification:
    """One measured deviation judged by the conformance rule of IEC TC 29.

    The verdict is derived from the fields rather than stored beside them, so
    a result cannot say it conforms over numbers that do not. All five
    numbers are in the one unit the specification is written in, which
    :attr:`unit` names for the figure.

    :ivar deviation: The measured deviation from the design goal, signed.
    :ivar uncertainty: The actual expanded uncertainty of that measurement,
        for a coverage probability of 95 %, as the testing laboratory
        calculated it.
    :ivar lower_limit: The lower acceptance limit, inclusive, or ``-inf``
        for an interval with no lower limit.
    :ivar upper_limit: The upper acceptance limit, inclusive, or ``+inf``
        for an interval with no upper limit (the stop band of IEC
        61260-1:2014 Table 1).
    :ivar max_uncertainty: The maximum-permitted expanded uncertainty the
        standard prints for the test, inclusive.
    :ivar unit: The unit of the five numbers, a label for the figure
        (``"dB"`` by default, ``"%"`` for a frequency or a distortion).
    """

    deviation: float
    uncertainty: float
    lower_limit: float
    upper_limit: float
    max_uncertainty: float
    unit: str = "dB"

    def __post_init__(self) -> None:
        """Refuse numbers the rule cannot be read on.

        :raises ValueError: if a number is not finite (a limit may be infinite
            on its own side only), if the lower limit is above the upper one,
            if both limits are open, if the uncertainty is negative or if the
            maximum-permitted uncertainty is not positive.
        """
        for name in ("deviation", "uncertainty", "max_uncertainty"):
            object.__setattr__(self, name, require_finite(getattr(self, name), name))
        object.__setattr__(
            self, "lower_limit", _open_limit(self.lower_limit, "lower_limit", -1.0)
        )
        object.__setattr__(
            self, "upper_limit", _open_limit(self.upper_limit, "upper_limit", 1.0)
        )
        if math.isinf(self.lower_limit) and math.isinf(self.upper_limit):
            msg = (
                "'lower_limit' and 'upper_limit' are both open: an acceptance "
                "interval needs at least one limit."
            )
            raise ValueError(msg)
        if self.lower_limit > self.upper_limit:
            msg = (
                f"'lower_limit' ({self.lower_limit:g}) must not be above "
                f"'upper_limit' ({self.upper_limit:g})."
            )
            raise ValueError(msg)
        if self.uncertainty < 0.0:
            msg = "'uncertainty' must be non-negative: it is an expanded uncertainty."
            raise ValueError(msg)
        if self.max_uncertainty <= 0.0:
            msg = "'max_uncertainty' must be positive."
            raise ValueError(msg)

    @property
    def deviation_within_limits(self) -> bool:
        """Criterion (a): the deviation lies inside the acceptance limits.

        Both limits belong to the acceptance interval (IEC 60942:2017 Annex D).
        """
        return _at_most(self.lower_limit, self.deviation) and _at_most(
            self.deviation, self.upper_limit
        )

    @property
    def uncertainty_within_maximum(self) -> bool:
        """Criterion (b): the uncertainty does not exceed the maximum permitted."""
        return _at_most(self.uncertainty, self.max_uncertainty)

    @property
    def passes(self) -> bool:
        """Whether the measurement demonstrates conformance: (a) AND (b).

        A deviation inside its limits measured with too large an uncertainty
        does not pass. It is not a failure of the instrument; it is a
        measurement that "shall not be used to demonstrate conformance"
        (IEC 60942:2017 5.1.16), which :attr:`outcome` tells apart.
        """
        return self.deviation_within_limits and self.uncertainty_within_maximum

    @property
    def outcome(self) -> int:
        """The outcome number of IEC 60942:2017 E.2.2 and IEC 61672-1:2013 C.2.2.

        ``1`` conforms; ``2`` the uncertainty exceeds its maximum; ``3`` the
        deviation exceeds its limits; ``4`` both.
        """
        key = (self.deviation_within_limits, self.uncertainty_within_maximum)
        return _OUTCOMES[key][0]

    @property
    def reason(self) -> str:
        """Why the measurement does or does not conform, as Table E.1 words it."""
        key = (self.deviation_within_limits, self.uncertainty_within_maximum)
        return _OUTCOMES[key][1]

    @property
    def share_of_acceptance_limit(self) -> float:
        """How much of its acceptance limit the deviation uses, as a fraction.

        Read on the side the deviation lies: a deviation of -0,6 dB against
        limits of +1,0 dB and -1,2 dB uses 0,5 of the lower one. Above 1 the
        deviation is outside the limits. A deviation on the far side of a
        limit of zero (a negative distortion against ``(0, 3)``) has no finite
        share and reads as infinity. An open side is never used up: on it the
        share is zero while the deviation is inside the interval and infinity
        once it is not (a stop-band attenuation of 40 dB against
        ``(70, +inf)``).
        """
        bound = self.upper_limit if self.deviation >= 0.0 else self.lower_limit
        if math.isinf(bound):
            return 0.0 if self.deviation_within_limits else math.inf
        if abs(bound) > _BOUNDARY_ABS_TOL:
            return self.deviation / bound
        return 0.0 if self.deviation_within_limits else math.inf

    @property
    def share_of_max_uncertainty(self) -> float:
        """The actual uncertainty over the maximum permitted. Above 1 it fails."""
        return self.uncertainty / self.max_uncertainty

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        An object is always true, so ``if verify_conformance(...):`` would
        pass every instrument whatever it measured. The verdict is
        :attr:`passes`.

        :raises TypeError: Always.
        """
        msg = (
            "a ConformanceVerification has no truth value; read its '.passes' "
            "for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the deviation, its uncertainty and the limits, as Figure E.1 does.

        The acceptance limits are the two horizontal lines, the measured
        deviation the marker (a diamond when it conforms, a cross when it does
        not), the actual uncertainty the error bar and the maximum-permitted
        one the shaded band behind it.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.metrology.plot_conformance_verification`.
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_conformance_verification

        check_language(language)
        return plot_conformance_verification(self, ax, language=language, **kwargs)


def _limits(acceptance_limits: float | tuple[float, float]) -> tuple[float, float]:
    """The ``(lower, upper)`` pair of a symmetric limit or of an explicit pair.

    A pair may leave one end open, ``-inf`` below or ``+inf`` above; a
    symmetric limit is always finite.

    :raises ValueError: for a negative symmetric limit or a pair that is not
        two numbers.
    """
    if isinstance(acceptance_limits, tuple | list):
        try:
            lower, upper = acceptance_limits
        except ValueError:
            msg = "'acceptance_limits' must be one number or a (lower, upper) pair."
            raise ValueError(msg) from None
        return (
            _open_limit(lower, "acceptance_limits", -1.0),
            _open_limit(upper, "acceptance_limits", 1.0),
        )
    limit = require_finite(float(acceptance_limits), "acceptance_limits")
    if limit < 0.0:
        msg = (
            "'acceptance_limits' must be non-negative when it is one number: it "
            "bounds the absolute deviation."
        )
        raise ValueError(msg)
    return -limit, limit


def verify_conformance(
    deviation: float,
    *,
    uncertainty: float,
    acceptance_limits: float | tuple[float, float],
    max_uncertainty: float,
    unit: str = "dB",
) -> ConformanceVerification:
    """Verify one measured deviation by the conformance rule of IEC TC 29.

    Conformance to a performance specification is demonstrated when the
    measured deviation from the design goal does not exceed the acceptance
    limits AND the actual expanded uncertainty does not exceed the
    maximum-permitted uncertainty, both limits inclusive (IEC 60942:2017
    5.1.15 and Annex D; IEC 61672-1:2013 5.1.21). The rule reproduces every
    verdict of IEC 60942:2017 Table E.1 and IEC 61672-1:2013 Table C.1.

    It is the rule, not a standard: the limits and the maximum uncertainty are
    what the standard prints for the test at hand, read off its own tables.
    :func:`phonometry.metrology.verify_sound_calibrator` does that for IEC
    60942.

    :param deviation: The measured deviation from the design goal, signed, in
        the unit of the specification. A standard that grades the absolute
        deviation, as IEC 60942 does, is served by passing the deviation as
        measured and a symmetric limit.
    :param uncertainty: The actual expanded uncertainty of the measurement for
        a coverage probability of 95 %, in the same unit.
    :param acceptance_limits: One non-negative number for symmetric limits
        (``0.25`` is +/-0,25), or a ``(lower, upper)`` pair such as
        ``(-1.2, 1.0)``. Both limits belong to the acceptance interval. One
        end of a pair may be open, ``(70.0, math.inf)`` for a minimum with no
        maximum, as IEC 61260-1:2014 Table 1 writes its stop band.
    :param max_uncertainty: The maximum-permitted expanded uncertainty for a
        coverage probability of 95 %, in the same unit.
    :param unit: The unit of the numbers, used to label the figure
        (default ``"dB"``).
    :return: The :class:`ConformanceVerification`, whose ``passes`` is the
        verdict and whose ``outcome`` and ``reason`` say which of the four
        outcomes it is.
    :raises ValueError: for a non-finite number (bar a limit open on its own
        side), a negative symmetric limit, a lower limit above the upper one,
        a pair open at both ends, a negative uncertainty or a
        maximum-permitted uncertainty that is not positive.
    """
    lower, upper = _limits(acceptance_limits)
    return ConformanceVerification(
        deviation=float(deviation),
        uncertainty=float(uncertainty),
        lower_limit=lower,
        upper_limit=upper,
        max_uncertainty=float(max_uncertainty),
        unit=str(unit),
    )
