#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Periodic tests of band filters (IEC 61260-3:2016): test frequencies and verdict.

IEC 61260-3:2016 is the short list of tests a laboratory runs on a working
octave-band or fractional-octave-band filter every year or two, to show that
it still meets the class it was built to under IEC 61260-1:2014. This module
gives two things for it.

**The test frequencies of Clause 13.** The relative attenuation of three
filters of the set is measured at 15 normalized frequencies, an abbreviation
of the Table 1 mask of IEC 61260-1 (13.3, NOTE 1). Formula (1) carries the
octave-band frequency parameters :math:`R_k` of its Table 1 (:math:`G^0`,
:math:`G^{1/8}`, :math:`G^{1/4}`, :math:`G^{3/8}`, :math:`G`, :math:`G^2`,
:math:`G^3`, :math:`G^4`) to a bandwidth designator :math:`1/b`,

.. math::

   \Omega_k = 1 + \frac{G^{1/(2b)} - 1}{G^{1/2} - 1}\,(R_k - 1),
   \qquad k = 0, 1, \ldots, 7,

and Formula (2) mirrors them below the mid-band, :math:`\Omega_{-k} =
1/\Omega_k`, with the same acceptance limits. For octave bands
:math:`\Omega_k = R_k` (NOTE 2). :func:`periodic_test_frequencies` returns
the 15, for any :math:`b`; Annex C prints them for one-third-octave filters
to five decimals, and they are reproduced there to the last digit. It is the
same mapping as Formula (9) of IEC 61260-1 that
:func:`phonometry.filters.class_limits` uses for its breakpoints.

**The verdict on a laboratory's results.** :func:`verify_filter_periodic`
grades what a laboratory measured, clause by clause, by the conformance rule
of IEC TC 29 that IEC 61260-3 5.1 states
(:func:`phonometry.metrology.verify_conformance`): the measured deviation
within the acceptance limit **and** the actual expanded uncertainty within the
maximum permitted by Annex B of IEC 61260-1:2014, both inclusive. The clauses
it grades are the ones that are a measured deviation with such a pair:

* **10.2**, the relative attenuation at the exact mid-band frequency of every
  filter of the set: :math:`\pm 0.4` dB (class 1) or :math:`\pm 0.6` dB
  (class 2), with the Annex B maximum for a relative attenuation of 2 dB or
  less, 0.20 dB;
* **10.3**, the alternative for time-invariant filters: the deviation of the
  time-averaged output of an exponential sweep from Formula (17) of
  IEC 61260-1, within the same limits (10.3.6), with the Annex B maximum for
  time-invariant operation, 0.20 dB (9.2.3);
* **11.7**, the level linearity deviation of three filters over the linear
  operating range: the limits of IEC 61260-1 5.13.3 (:math:`\pm 0.5` dB or
  :math:`\pm 0.6` dB) down to 40 dB below the upper boundary and of 5.13.4
  (:math:`\pm 0.7` dB or :math:`\pm 0.9` dB) further down, with the Annex B
  maxima 0.20 dB and 0.35 dB on either side of those 40 dB;
* **11.9**, the level linearity on every other level range, 30 dB below its
  upper boundary: 5.13.3, 0.20 dB;
* **13**, the relative attenuation of the same three filters at the 15 test
  frequencies against Table 1 of IEC 61260-3, with the Annex B maxima 0.20 dB,
  0.30 dB and 0.50 dB for a relative attenuation up to 2 dB, up to 40 dB and
  above 40 dB.

A stop-band row of Table 1 prints a minimum and :math:`+\infty` ("+70; +∞"),
an acceptance interval with no upper limit, which is how it is judged.

**What 5.3 makes unusable.** A result whose actual uncertainty exceeds the
maximum permitted "shall not be used to evaluate conformance to this standard
for periodic testing" (5.3). Such a result is neither a pass nor, by itself, a
failure of the filter; :attr:`FilterPeriodicVerification.unusable` lists them
and the verdict does not pass while any is left.

**What a pass here is, and is not.** It is a verdict on the numbers put in.
The checks that are not a deviation with a maximum-permitted uncertainty are
the laboratory's own record: the instruction manual and markings of Clause 4,
the preliminary inspection of Clause 6, the power supply of Clause 7, the
environmental conditions of Clause 8, the overload indications of 11.5 and
11.8, and the self-generated noise of Clause 12, which compares the output
with the input short-circuited against the lower limit the manual states and
has no maximum-permitted uncertainty in Annex B. And even a filter that
passes every periodic test supports no general conclusion about the
specifications of IEC 61260-1 unless the model's pattern approval under
IEC 61260-2 is publicly available (1.5): the statement the verdict writes is
the one Clause 14 k) or l) prescribes for the case at hand.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.frozen import read_only
from .._internal.validation import is_class_designation, require_positive
from ..metrology.conformance import ConformanceVerification, verify_conformance
from .compliance import _map_breakpoint

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes

__all__ = [
    "PERIODIC_TEST_ATTENUATION_LIMITS_DB",
    "FilterPeriodicMeasurements",
    "FilterPeriodicVerification",
    "PeriodicTestClause",
    "periodic_test_frequencies",
    "verify_filter_periodic",
]

#: IEC 61260-3:2016 Table 1: the frequency parameter :math:`R_k = G^{x_k}` as
#: its exponent :math:`x_k`, for ``k = 0 .. 7``.
_FREQUENCY_PARAMETER_EXPONENTS: tuple[float, ...] = (
    0.0,
    1.0 / 8.0,
    1.0 / 4.0,
    3.0 / 8.0,
    1.0,
    2.0,
    3.0,
    4.0,
)

#: The number of test frequencies of Clause 13, ``k = -7 .. 7`` (C.1).
_TEST_FREQUENCY_COUNT = 2 * (len(_FREQUENCY_PARAMETER_EXPONENTS) - 1) + 1

#: IEC 61260-3:2016 Table 1 (printed p. 13): the minimum and maximum
#: acceptance limits on relative attenuation, dB, for ``|k| = 0 .. 7``, per
#: class; the stop-band maximum is printed as "+∞".
PERIODIC_TEST_ATTENUATION_LIMITS_DB: Mapping[int, tuple[tuple[float, float], ...]] = (
    MappingProxyType(
        {
            1: (
                (-0.4, 0.4),
                (-0.4, 0.5),
                (-0.4, 0.7),
                (-0.4, 1.4),
                (16.6, math.inf),
                (40.5, math.inf),
                (60.0, math.inf),
                (70.0, math.inf),
            ),
            2: (
                (-0.6, 0.6),
                (-0.6, 0.7),
                (-0.6, 0.9),
                (-0.6, 1.7),
                (15.6, math.inf),
                (39.5, math.inf),
                (54.0, math.inf),
                (60.0, math.inf),
            ),
        }
    )
)

#: IEC 61260-3:2016 10.2.2 and 10.3.6: the acceptance limits on the relative
#: attenuation at the mid-band frequency and on the swept output, +/- dB.
_MIDBAND_LIMITS_DB: dict[int, float] = {1: 0.4, 2: 0.6}

#: IEC 61260-1:2014 5.13.3 and 5.13.4: the acceptance limits on the level
#: linearity deviation, +/- dB, down to 40 dB below the upper boundary of the
#: linear operating range and further down.
_LINEARITY_LIMITS_DB: dict[int, tuple[float, float]] = {1: (0.5, 0.7), 2: (0.6, 0.9)}

#: IEC 61260-1:2014 5.13.3: the depth below the upper boundary, dB, at which
#: the level linearity limits and their Annex B maxima change.
_LINEARITY_SPLIT_DB = 40.0

#: IEC 61260-3:2016 11.9: the depth below the upper boundary of each other
#: level range at which its linearity is tested, dB.
_RANGE_TEST_DEPTH_DB = 30.0

#: IEC 61260-1:2014 Table B.1: the maximum-permitted expanded uncertainty of a
#: relative attenuation, dB, for DeltaA <= 2 dB, 2 dB < DeltaA <= 40 dB and
#: DeltaA > 40 dB.
_ATTENUATION_MAX_UNCERTAINTY_DB = (0.20, 0.30, 0.50)

#: IEC 61260-1:2014 Table B.1: the relative attenuations, dB, at which the
#: maximum-permitted uncertainty of a relative attenuation steps up.
_ATTENUATION_UNCERTAINTY_STEPS_DB = (2.0, 40.0)

#: IEC 61260-1:2014 Table B.1: the maximum-permitted expanded uncertainty of
#: a level linearity deviation, dB, within and beyond 40 dB of the upper
#: boundary.
_LINEARITY_MAX_UNCERTAINTY_DB = (0.20, 0.35)

#: IEC 61260-1:2014 Table B.1: the maximum-permitted expanded uncertainty of
#: the time-invariant operation test, dB, which 9.2.3 of IEC 61260-3 applies
#: to the swept test of 10.3.
_TIME_INVARIANCE_MAX_UNCERTAINTY_DB = 0.20

#: The classes IEC 61260-1:2014 and IEC 61260-3:2016 define.
_CLASSES = (1, 2)

#: The outcome number of IEC 61260-1:2014 C.2.2 for a deviation outside its
#: limits measured with an acceptable uncertainty.
_OUTCOME_DEVIATION_EXCEEDS = 3

#: A matrix: one row of results per tested filter.
_MATRIX_RANK = 2

#: One kilohertz, where a filter label switches to the "kHz" form.
_HZ_PER_KHZ = 1000.0

#: The clause groups a complete periodic test grades: 10 (10.2 or 10.3), 11.7
#: and 13. 11.9 applies only to a filter with more than one level range.
_REQUIRED = ("10", "11.7", "13")

#: What each graded clause is, as its heading in IEC 61260-3:2016 reads.
_CLAUSE_TITLES: dict[str, str] = {
    "10.2": "Relative attenuation at the mid-band frequency",
    "10.3": "Effective bandwidth deviation (exponential sweep)",
    "11.7": "Level linearity on the reference level range",
    "11.9": "Level linearity on the other level ranges",
    "13": "Relative attenuation at the test frequencies",
}


def periodic_test_frequencies(fraction: float) -> np.ndarray:
    r"""The 15 normalized test frequencies of IEC 61260-3:2016 Clause 13.

    :math:`\Omega_k` for ``k = -7, -6, ..., 7``, by Formula (1) for
    :math:`k \ge 0` and Formula (2), :math:`\Omega_{-k} = 1/\Omega_k`, below
    the mid-band. Multiply by a filter's exact mid-band frequency for the
    test frequencies in hertz (C.2). 13.4 drops the ones below 0.5 times the
    lowest mid-band frequency of the set or above 1.5 times the highest.

    :param fraction: The bandwidth designator denominator ``b`` (1 for
        octave, 3 for one-third-octave bands, any positive value).
    :return: A read-only array of the 15 normalized frequencies, ascending,
        index ``k + 7``; ``PERIODIC_TEST_ATTENUATION_LIMITS_DB[c][abs(k)]``
        are their acceptance limits.
    :raises ValueError: for a ``fraction`` that is not positive.
    """
    b = require_positive(fraction, "fraction")
    upper = np.array(
        [_map_breakpoint(x, b) for x in _FREQUENCY_PARAMETER_EXPONENTS],
        dtype=np.float64,
    )
    return read_only(np.concatenate([1.0 / upper[:0:-1], upper]))


def _sequence(values: Sequence[float] | None, name: str) -> tuple[float, ...] | None:
    """A sequence of finite numbers as a tuple, or ``None`` when not given."""
    if values is None:
        return None
    try:
        arr = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError):
        msg = f"'{name}' must be a sequence of numbers."
        raise ValueError(msg) from None
    if arr.ndim != 1 or arr.size == 0:
        msg = f"'{name}' must be a non-empty one-dimensional sequence."
        raise ValueError(msg)
    if not np.all(np.isfinite(arr)):
        msg = f"'{name}' must hold finite values."
        raise ValueError(msg)
    return tuple(float(v) for v in arr)


def _rows(
    values: Sequence[Sequence[float]] | None, name: str
) -> tuple[tuple[float, ...], ...] | None:
    """Clause 13 results: one row of 15 per tested filter, NaN where not applied."""
    if values is None:
        return None
    try:
        arr = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError):
        msg = f"'{name}' must be rows of numbers."
        raise ValueError(msg) from None
    if arr.ndim == 1:
        arr = arr[np.newaxis, :]
    if (
        arr.ndim != _MATRIX_RANK
        or arr.shape[1] != _TEST_FREQUENCY_COUNT
        or arr.shape[0] == 0
    ):
        msg = (
            f"'{name}' must hold one row of {_TEST_FREQUENCY_COUNT} values per "
            f"tested filter, k = -7 .. 7; got shape {arr.shape}."
        )
        raise ValueError(msg)
    if np.any(np.isinf(arr)):
        msg = f"'{name}' must hold finite values, or NaN where 13.4 drops a frequency."
        raise ValueError(msg)
    return tuple(tuple(float(v) for v in row) for row in arr)


@dataclass(frozen=True)
class FilterPeriodicMeasurements:
    r"""What a laboratory measured in the periodic tests of IEC 61260-3:2016.

    Every result comes with the actual expanded uncertainty the laboratory
    calculated for it, for a coverage probability of 95 % (5.2), in the same
    position of a sequence of the same length. A clause left at ``None`` was
    not measured. Everything is in decibels.

    :ivar midband_attenuations_db: 10.2: the relative attenuation at the
        exact mid-band frequency of every filter of the set.
    :ivar midband_uncertainties_db: Their uncertainties.
    :ivar bandwidth_deviations_db: 10.3: for a time-invariant filter, the
        deviation of every filter's time-averaged output of an exponential
        sweep from :math:`L_\mathrm{c}` of IEC 61260-1 Formula (17).
    :ivar bandwidth_uncertainties_db: Their uncertainties.
    :ivar set_midband_frequencies_hz: Optional labels for the 10.2 and 10.3
        results: the exact mid-band frequency of each filter, in order.
    :ivar linearity_deviations_db: 11.7: the level linearity deviations of
        the three selected filters on the reference level range, at every
        level measured.
    :ivar linearity_levels_below_upper_db: For each of them, how far below
        the upper boundary of the linear operating range the input level was
        (:math:`L_\mathrm{u} - L`, negative above it), which decides between
        the limits of 5.13.3 and 5.13.4 and the maxima of Annex B.
    :ivar linearity_uncertainties_db: Their uncertainties.
    :ivar range_linearity_deviations_db: 11.9: the level linearity deviation
        30 dB below the upper boundary of every other level range.
    :ivar range_linearity_uncertainties_db: Their uncertainties.
    :ivar relative_attenuations_db: 13: for each of the three selected
        filters, a row of 15 relative attenuations at the test frequencies of
        :func:`periodic_test_frequencies`, ``k = -7 .. 7``, NaN where 13.4
        drops the frequency.
    :ivar relative_attenuation_uncertainties_db: The same shape, NaN in the
        same places.
    :ivar tested_midband_frequencies_hz: Optional labels for the 11.7 and 13
        results: the exact mid-band frequency of each selected filter.
    """

    midband_attenuations_db: Sequence[float] | None = None
    midband_uncertainties_db: Sequence[float] | None = None
    bandwidth_deviations_db: Sequence[float] | None = None
    bandwidth_uncertainties_db: Sequence[float] | None = None
    set_midband_frequencies_hz: Sequence[float] | None = None
    linearity_deviations_db: Sequence[float] | None = None
    linearity_levels_below_upper_db: Sequence[float] | None = None
    linearity_uncertainties_db: Sequence[float] | None = None
    range_linearity_deviations_db: Sequence[float] | None = None
    range_linearity_uncertainties_db: Sequence[float] | None = None
    relative_attenuations_db: Sequence[Sequence[float]] | None = None
    relative_attenuation_uncertainties_db: Sequence[Sequence[float]] | None = None
    tested_midband_frequencies_hz: Sequence[float] | None = None

    def __post_init__(self) -> None:
        """Freeze every sequence and refuse results the rule cannot be read on.

        :raises ValueError: if a result comes without its uncertainty or the
            other way round, if their lengths differ, if a value is not
            finite (NaN is allowed only where 13.4 drops a test frequency,
            and then in both rows) or if an uncertainty is negative.
        """
        for name in (
            "midband_attenuations_db",
            "midband_uncertainties_db",
            "bandwidth_deviations_db",
            "bandwidth_uncertainties_db",
            "set_midband_frequencies_hz",
            "linearity_deviations_db",
            "linearity_levels_below_upper_db",
            "linearity_uncertainties_db",
            "range_linearity_deviations_db",
            "range_linearity_uncertainties_db",
            "tested_midband_frequencies_hz",
        ):
            object.__setattr__(self, name, _sequence(getattr(self, name), name))
        for name in (
            "relative_attenuations_db",
            "relative_attenuation_uncertainties_db",
        ):
            object.__setattr__(self, name, _rows(getattr(self, name), name))
        self._check_group(
            "10.2", ("midband_attenuations_db", "midband_uncertainties_db")
        )
        self._check_group(
            "10.3", ("bandwidth_deviations_db", "bandwidth_uncertainties_db")
        )
        self._check_group(
            "11.7",
            (
                "linearity_deviations_db",
                "linearity_levels_below_upper_db",
                "linearity_uncertainties_db",
            ),
        )
        self._check_group(
            "11.9",
            ("range_linearity_deviations_db", "range_linearity_uncertainties_db"),
        )
        self._check_group(
            "13",
            ("relative_attenuations_db", "relative_attenuation_uncertainties_db"),
        )
        self._check_labels()
        self._check_clause_13()

    def _check_group(self, clause: str, names: tuple[str, ...]) -> None:
        """All fields of one clause are given together, with one length."""
        given = [getattr(self, n) is not None for n in names]
        if any(given) and not all(given):
            missing = [n for n, g in zip(names, given, strict=True) if not g]
            msg = (
                f"clause {clause} needs {', '.join(repr(n) for n in names)} "
                f"together; missing {missing}."
            )
            raise ValueError(msg)
        if not all(given):
            return
        lengths = {len(getattr(self, n)) for n in names}
        if len(lengths) != 1:
            msg = (
                f"clause {clause}: {', '.join(repr(n) for n in names)} must have "
                f"the same length; got {[len(getattr(self, n)) for n in names]}."
            )
            raise ValueError(msg)
        uncertainty = next(n for n in names if "uncertaint" in n)
        values = np.asarray(getattr(self, uncertainty), dtype=np.float64)
        if np.any(values[~np.isnan(values)] < 0.0):
            msg = f"'{uncertainty}' must be non-negative: they are expanded uncertainties."
            raise ValueError(msg)

    def _check_labels(self) -> None:
        """The optional frequency labels, when given, match their results."""
        pairs = (
            (
                "set_midband_frequencies_hz",
                ("midband_attenuations_db", "bandwidth_deviations_db"),
            ),
            (
                "tested_midband_frequencies_hz",
                ("relative_attenuations_db",),
            ),
        )
        for label_name, result_names in pairs:
            labels = getattr(self, label_name)
            if labels is None:
                continue
            if any(f <= 0.0 for f in labels):
                msg = f"'{label_name}' must hold positive frequencies."
                raise ValueError(msg)
            for result_name in result_names:
                results = getattr(self, result_name)
                if results is not None and len(results) != len(labels):
                    msg = (
                        f"'{label_name}' labels {len(labels)} filters but "
                        f"'{result_name}' holds {len(results)}."
                    )
                    raise ValueError(msg)

    def _check_clause_13(self) -> None:
        """The NaN where 13.4 drops a frequency are the same in both rows."""
        values = self.relative_attenuations_db
        uncertainties = self.relative_attenuation_uncertainties_db
        if values is None or uncertainties is None:
            return
        v = np.asarray(values, dtype=np.float64)
        u = np.asarray(uncertainties, dtype=np.float64)
        if not np.array_equal(np.isnan(v), np.isnan(u)):
            msg = (
                "'relative_attenuations_db' and "
                "'relative_attenuation_uncertainties_db' must leave the same test "
                "frequencies out (NaN), those 13.4 drops."
            )
            raise ValueError(msg)
        if np.all(np.isnan(v)):
            msg = "'relative_attenuations_db' holds no measured value."
            raise ValueError(msg)


@dataclass(frozen=True)
class PeriodicTestClause:
    r"""The verdict on one clause of IEC 61260-3:2016.

    :ivar clause: The clause, ``"10.2"``, ``"10.3"``, ``"11.7"``, ``"11.9"``
        or ``"13"``.
    :ivar title: What the clause tests.
    :ivar labels: What each result is (the filter, the level or the test
        frequency it belongs to), in the order given.
    :ivar verifications: One
        :class:`~phonometry.metrology.ConformanceVerification` per result.
    :ivar normalized_frequencies: Clause 13 only: the :math:`\Omega_k` of each
        result, which its figure is drawn against; ``None`` otherwise.
    """

    clause: str
    title: str
    labels: tuple[str, ...]
    verifications: tuple[ConformanceVerification, ...]
    normalized_frequencies: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        """One label per result, and at least one result.

        :raises ValueError: if the labels and the results differ in number or
            there is no result.
        """
        if not self.verifications:
            msg = f"clause {self.clause} carries no result."
            raise ValueError(msg)
        if len(self.labels) != len(self.verifications):
            msg = (
                f"clause {self.clause}: {len(self.labels)} labels for "
                f"{len(self.verifications)} results."
            )
            raise ValueError(msg)
        if self.normalized_frequencies is not None and len(
            self.normalized_frequencies
        ) != len(self.verifications):
            msg = f"clause {self.clause}: one normalized frequency per result."
            raise ValueError(msg)

    @property
    def passes(self) -> bool:
        """Whether every result of the clause demonstrates conformance (5.1)."""
        return all(v.passes for v in self.verifications)

    @property
    def unusable(self) -> tuple[str, ...]:
        """The results whose uncertainty exceeds the maximum permitted (5.3)."""
        return tuple(
            label
            for label, v in zip(self.labels, self.verifications, strict=True)
            if not v.uncertainty_within_maximum
        )

    @property
    def failed(self) -> tuple[str, ...]:
        """The results whose deviation exceeds its acceptance limits.

        Only those measured with an acceptable uncertainty: a result that is
        also :attr:`unusable` shows nothing about the filter (5.3).
        """
        return tuple(
            label
            for label, v in zip(self.labels, self.verifications, strict=True)
            if v.outcome == _OUTCOME_DEVIATION_EXCEEDS
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a PeriodicTestClause has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw every result of the clause against its limits.

        Clauses 10 and 11 are drawn as IEC 61260-1:2014 Figure C.1 draws its
        examples: the limits, the deviation, its uncertainty and the
        maximum-permitted band. Clause 13, whose limits run from a few tenths
        of a decibel to 70 dB, is drawn as each result's margin to its nearer
        limit against the test frequency: at or above zero it conforms.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the verdict markers.
        """
        from .._i18n import check_language
        from .._plot.filters import plot_periodic_clause

        check_language(language)
        return plot_periodic_clause(self, ax=ax, language=language, **kwargs)


@dataclass(frozen=True)
class FilterPeriodicVerification:
    """The IEC 61260-3:2016 verdict on the periodic tests of a band filter.

    :ivar filter_class: The class the filter was tested as, 1 or 2.
    :ivar pattern_approval_public: Whether evidence is publicly available
        that the model passed the pattern evaluation of IEC 61260-2 (14 c).
    :ivar measurements: The record the verdict was reached on.
    :ivar clauses: One :class:`PeriodicTestClause` per clause measured, in
        the order of the standard.
    """

    filter_class: int
    pattern_approval_public: bool
    measurements: FilterPeriodicMeasurements
    clauses: tuple[PeriodicTestClause, ...]

    @property
    def missing(self) -> tuple[str, ...]:
        """The clauses a complete periodic test grades that were not measured.

        ``"10"`` (10.2 or 10.3), ``"11.7"`` and ``"13"``; 11.9 applies only to
        a filter with more than one level range and is never missing.
        """
        present = {c.clause for c in self.clauses}
        if "10.3" in present:
            present.add("10")
        if "10.2" in present:
            present.add("10")
        return tuple(clause for clause in _REQUIRED if clause not in present)

    @property
    def unusable(self) -> tuple[tuple[str, str], ...]:
        """``(clause, result)`` for every result 5.3 forbids using."""
        return tuple((c.clause, label) for c in self.clauses for label in c.unusable)

    @property
    def failed(self) -> tuple[tuple[str, str], ...]:
        """``(clause, result)`` for every result outside its acceptance limits."""
        return tuple((c.clause, label) for c in self.clauses for label in c.failed)

    @property
    def passes(self) -> bool:
        """Whether the filter completed the periodic tests successfully.

        Every clause a complete test grades was measured, and every result
        demonstrates conformance: no deviation outside its limits and no
        uncertainty above its maximum.
        """
        return (
            bool(self.clauses)
            and not self.missing
            and all(c.passes for c in self.clauses)
        )

    @property
    def statement(self) -> str:
        """The statement IEC 61260-3:2016 Clause 14 prescribes for the result.

        14 m) when a result exceeds its acceptance limits, followed by the
        tests that did not complete and why; the 5.3 notice when results
        cannot be used; a notice naming the clauses not measured; and
        otherwise 14 k) with a public pattern approval or 14 l) without one,
        which carries the caveat of 1.5: without it no general conclusion
        about IEC 61260-1 can be drawn.
        """
        y = self.filter_class
        if self.failed:
            reasons = "; ".join(
                f"{clause} ({label}): measured deviation exceeds the acceptance limits"
                for clause, label in self.failed
            )
            return (
                f"The filter submitted for periodic testing did not successfully "
                f"complete the class {y} tests of IEC 61260-3. The filter did not "
                f"conform to the class {y} specifications of IEC 61260-1:2014. "
                f"Tests not successfully completed: {reasons}."
            )
        if self.unusable:
            clauses = ", ".join(sorted({clause for clause, _ in self.unusable}))
            return (
                f"The results of clause {clauses} cannot be used to evaluate "
                "conformance for periodic testing: their actual expanded "
                "uncertainty exceeds the maximum permitted by IEC 61260-1:2014 "
                "Annex B (IEC 61260-3:2016, 5.3)."
            )
        if self.missing:
            return (
                "The periodic tests of IEC 61260-3 are incomplete: clause "
                f"{', '.join(self.missing)} was not measured, and no test shall "
                "be omitted unless the filter lacks the feature it tests (9.1.1)."
            )
        head = (
            "The filter submitted for testing successfully completed the periodic "
            "tests of IEC 61260-3, for the environmental conditions under which "
            "the tests were performed."
        )
        if self.pattern_approval_public:
            return (
                f"{head} As evidence was publicly available, from an independent "
                "testing organization responsible for approving the results of "
                "pattern-evaluation tests performed in accordance with "
                "IEC 61260-2, to demonstrate that the model of filter fully "
                f"conformed to the class {y} specifications in IEC 61260-1:2014 "
                f"the filter submitted for testing conforms to the class {y} "
                "specifications of IEC 61260-1:2014."
            )
        return (
            f"{head} However, no general statement or conclusion can be made about "
            "conformance of the filter to the full specifications of "
            "IEC 61260-1:2014 because (a) evidence was not publicly available, "
            "from an independent testing organization responsible for pattern "
            "approvals, to demonstrate that the model of filter fully conformed "
            f"to the class {y} specifications in IEC 61260-1:2014 and (b) because "
            "the periodic tests of IEC 61260-3 cover only a limited subset of the "
            "specifications in IEC 61260-1:2014."
        )

    def clause(self, clause: str) -> PeriodicTestClause:
        """The verdict on one clause.

        :param clause: ``"10.2"``, ``"10.3"``, ``"11.7"``, ``"11.9"`` or
            ``"13"``.
        :return: Its :class:`PeriodicTestClause`.
        :raises KeyError: when that clause was not measured.
        """
        for item in self.clauses:
            if item.clause == clause:
                return item
        msg = f"clause {clause!r} was not measured; measured: {[c.clause for c in self.clauses]}"
        raise KeyError(msg)

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a FilterPeriodicVerification has no truth value; read its '.passes' "
            "for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw every result's margin to its acceptance limits, clause by clause.

        One marker per result, grouped by clause: the distance from the
        deviation to its nearer acceptance limit, with the actual uncertainty
        as its error bar; a result at or above zero lies within its limits.
        A result drawn hollow is one 5.3 forbids using.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the verdict markers.
        """
        from .._i18n import check_language
        from .._plot.filters import plot_periodic_verification

        check_language(language)
        return plot_periodic_verification(self, ax=ax, language=language, **kwargs)


def _attenuation_max_uncertainty_db(relative_attenuation_db: float) -> float:
    """IEC 61260-1:2014 Table B.1: the maximum for a relative attenuation."""
    low, high = _ATTENUATION_UNCERTAINTY_STEPS_DB
    small, middle, large = _ATTENUATION_MAX_UNCERTAINTY_DB
    if relative_attenuation_db <= low:
        return small
    if relative_attenuation_db <= high:
        return middle
    return large


def _hz_label(frequency_hz: float) -> str:
    """``1 kHz`` or ``125.9 Hz``: a filter named by its mid-band frequency."""
    if frequency_hz >= _HZ_PER_KHZ:
        return f"{frequency_hz / _HZ_PER_KHZ:g} kHz"
    return f"{frequency_hz:g} Hz"


def _filter_labels(frequencies: Sequence[float] | None, count: int) -> list[str]:
    """One label per filter: its mid-band frequency, or its position."""
    if frequencies is None:
        return [f"filter {n}" for n in range(1, count + 1)]
    return [_hz_label(f) for f in frequencies]


def _clause_10(
    clause: str,
    deviations: Sequence[float],
    uncertainties: Sequence[float],
    labels: list[str],
    filter_class: int,
    max_uncertainty: float,
) -> PeriodicTestClause:
    """10.2 or 10.3: one result per filter, +/-0.4 dB or +/-0.6 dB."""
    limit = _MIDBAND_LIMITS_DB[filter_class]
    return PeriodicTestClause(
        clause=clause,
        title=_CLAUSE_TITLES[clause],
        labels=tuple(labels),
        verifications=tuple(
            verify_conformance(
                d,
                uncertainty=u,
                acceptance_limits=limit,
                max_uncertainty=max_uncertainty,
            )
            for d, u in zip(deviations, uncertainties, strict=True)
        ),
    )


def _clause_11_7(
    m: FilterPeriodicMeasurements, filter_class: int
) -> PeriodicTestClause:
    """11.7: the limits and maxima switch 40 dB below the upper boundary."""
    near, far = _LINEARITY_LIMITS_DB[filter_class]
    near_u, far_u = _LINEARITY_MAX_UNCERTAINTY_DB
    deviations = m.linearity_deviations_db or ()
    depths = m.linearity_levels_below_upper_db or ()
    uncertainties = m.linearity_uncertainties_db or ()
    verifications = []
    labels = []
    for d, depth, u in zip(deviations, depths, uncertainties, strict=True):
        beyond = depth > _LINEARITY_SPLIT_DB
        verifications.append(
            verify_conformance(
                d,
                uncertainty=u,
                acceptance_limits=far if beyond else near,
                max_uncertainty=far_u if beyond else near_u,
            )
        )
        labels.append(f"{depth:g} dB below the upper boundary")
    return PeriodicTestClause(
        clause="11.7",
        title=_CLAUSE_TITLES["11.7"],
        labels=tuple(labels),
        verifications=tuple(verifications),
    )


def _clause_11_9(
    m: FilterPeriodicMeasurements, filter_class: int
) -> PeriodicTestClause:
    """11.9: 30 dB below the upper boundary of every other range, 5.13.3."""
    near, _ = _LINEARITY_LIMITS_DB[filter_class]
    near_u, _ = _LINEARITY_MAX_UNCERTAINTY_DB
    deviations = m.range_linearity_deviations_db or ()
    uncertainties = m.range_linearity_uncertainties_db or ()
    return PeriodicTestClause(
        clause="11.9",
        title=_CLAUSE_TITLES["11.9"],
        labels=tuple(
            f"level range {n}, {_RANGE_TEST_DEPTH_DB:g} dB below its upper boundary"
            for n in range(1, len(deviations) + 1)
        ),
        verifications=tuple(
            verify_conformance(
                d, uncertainty=u, acceptance_limits=near, max_uncertainty=near_u
            )
            for d, u in zip(deviations, uncertainties, strict=True)
        ),
    )


def _clause_13(
    m: FilterPeriodicMeasurements, filter_class: int, fraction: float
) -> PeriodicTestClause:
    """13: Table 1 at the 15 test frequencies, the maximum by the attenuation."""
    omega = periodic_test_frequencies(fraction)
    limits = PERIODIC_TEST_ATTENUATION_LIMITS_DB[filter_class]
    rows = m.relative_attenuations_db or ()
    rows_u = m.relative_attenuation_uncertainties_db or ()
    names = _filter_labels(m.tested_midband_frequencies_hz, len(rows))
    verifications = []
    labels = []
    omegas = []
    half = len(_FREQUENCY_PARAMETER_EXPONENTS) - 1
    for name, row, row_u in zip(names, rows, rows_u, strict=True):
        for position, (value, u) in enumerate(zip(row, row_u, strict=True)):
            if math.isnan(value):
                continue
            k = position - half
            verifications.append(
                verify_conformance(
                    value,
                    uncertainty=u,
                    acceptance_limits=limits[abs(k)],
                    max_uncertainty=_attenuation_max_uncertainty_db(value),
                )
            )
            labels.append(f"{name}, k = {k}")
            omegas.append(float(omega[position]))
    return PeriodicTestClause(
        clause="13",
        title=_CLAUSE_TITLES["13"],
        labels=tuple(labels),
        verifications=tuple(verifications),
        normalized_frequencies=tuple(omegas),
    )


def verify_filter_periodic(
    filter_class: int,
    measurements: FilterPeriodicMeasurements,
    *,
    fraction: float,
    pattern_approval_public: bool = False,
) -> FilterPeriodicVerification:
    """Grade the periodic tests of a band filter, IEC 61260-3:2016.

    Each clause measured is judged result by result by the conformance rule
    of IEC TC 29 (5.1), with the acceptance limits the clause sets and the
    maximum-permitted uncertainties of IEC 61260-1:2014 Annex B; see the
    module docstring for which clause reads which. The verdict passes when
    every clause a complete test grades was measured (10.2 or 10.3, 11.7 and
    13) and every result conforms, and its :attr:`~FilterPeriodicVerification.statement`
    is the text Clause 14 prescribes for the case.

    :param filter_class: The class the filter is tested as, 1 or 2.
    :param measurements: The laboratory's results and uncertainties.
    :param fraction: The bandwidth designator denominator ``b`` of the
        filters of Clause 13 (1 for octave, 3 for one-third-octave bands),
        which places their test frequencies.
    :param pattern_approval_public: Whether evidence is publicly available,
        from an independent testing organization, that the model passed the
        pattern evaluation of IEC 61260-2. Without it a passing filter still
        supports no general conclusion about IEC 61260-1 (1.5), and the
        statement says so.
    :return: A :class:`FilterPeriodicVerification`.
    :raises ValueError: for a class other than 1 or 2, a ``fraction`` that is
        not positive, or a record with nothing measured.
    """
    if not is_class_designation(filter_class, _CLASSES):
        msg = f"'filter_class' must be 1 or 2 (IEC 61260-1:2014); got {filter_class!r}."
        raise ValueError(msg)
    fraction = require_positive(fraction, "fraction")
    cls = int(filter_class)
    m = measurements
    clauses: list[PeriodicTestClause] = []
    if m.midband_attenuations_db is not None and m.midband_uncertainties_db is not None:
        clauses.append(
            _clause_10(
                "10.2",
                m.midband_attenuations_db,
                m.midband_uncertainties_db,
                _filter_labels(
                    m.set_midband_frequencies_hz, len(m.midband_attenuations_db)
                ),
                cls,
                _ATTENUATION_MAX_UNCERTAINTY_DB[0],
            )
        )
    if (
        m.bandwidth_deviations_db is not None
        and m.bandwidth_uncertainties_db is not None
    ):
        clauses.append(
            _clause_10(
                "10.3",
                m.bandwidth_deviations_db,
                m.bandwidth_uncertainties_db,
                _filter_labels(
                    m.set_midband_frequencies_hz, len(m.bandwidth_deviations_db)
                ),
                cls,
                _TIME_INVARIANCE_MAX_UNCERTAINTY_DB,
            )
        )
    if m.linearity_deviations_db is not None:
        clauses.append(_clause_11_7(m, cls))
    if m.range_linearity_deviations_db is not None:
        clauses.append(_clause_11_9(m, cls))
    if m.relative_attenuations_db is not None:
        clauses.append(_clause_13(m, cls, fraction))
    if not clauses:
        msg = "'measurements' holds no result to grade."
        raise ValueError(msg)
    return FilterPeriodicVerification(
        filter_class=cls,
        pattern_approval_public=bool(pattern_approval_public),
        measurements=m,
        clauses=tuple(clauses),
    )
