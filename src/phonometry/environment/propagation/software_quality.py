#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Quality assurance of software for outdoor sound: a program's results
against the certified ones, and the spread of level differences
(ISO 17534-1:2015).

ISO 17534-1 does not predict a level. It says how a program that implements
an outdoor calculation method (ISO 9613-2, CNOSSOS-EU, a national method)
shows that it implements it correctly, and how its user finds out what the
program's shortcuts cost. Four things in it are arithmetic, and this module
is those four:

* **The test-case comparison** of clause 7.1 and Annex B. A method's test
  cases print, for every band and for the total, a correct result and the
  limits a program's result has to fall inside; Table A.5 puts them at
  +/-0,05 dB round the result given to two decimals. The Test Case Results
  Comparison form (TRC form, Tables B.1 and B.2) lists each result beside its
  limits and answers "Result inside tolerances: yes/no".
  :func:`verify_calculation_results` fills that column and returns the
  verdict, :class:`CalculationVerification`.
* **The characteristic values of a set of level differences**, Annex C.
  Levels calculated twice at the same receiver points (in the reference
  configuration and in the faster "modified configuration" a noise map is
  actually computed with, 5.2.3 and 7.2) differ, and the standard describes
  the differences by two order statistics of a random sample of them: the
  0,1-quantile :math:`q_{0,1}` and the 0,9-quantile :math:`q_{0,9}`, so that
  80 % of the differences are expected between the two.
  :func:`level_difference_quantiles` sorts the sample, takes the ranking
  positions of :func:`ranking_positions` and returns
  :class:`LevelDifferenceQuantiles`, with the mean and the estimated standard
  deviation C.5 asks for beside them.
* **Where the sample is taken**, C.2 and C.3: a uniform sample of ``M`` of
  the ``N`` single points by the ordinal numbers
  :math:`\mathrm{IP}((i - 0{,}5) N / M)` (:func:`uniform_sample_indices`), or
  of points along sound contours of total length ``L`` at the chainages
  :math:`\mathrm{IP}((i - 0{,}5) L / M)` (:func:`contour_sample_chainages_m`),
  with the points closer than 2 m to a source or an obstacle left out first.
* **The precision of a method across programs**, 4.5.2 and A.3: with ``M``
  participants of a round robin calculating the same ``N`` receivers, the
  0,9-quantile of the ``N`` largest absolute deviations from the mean level
  at each receiver (:func:`round_robin_precision`,
  :class:`RoundRobinPrecision`).

The rest of the standard (the documentation a method has to have, the
declaration of conformity, the QA data format of Annex D) is a set of
requirements on documents, not a calculation, and is not attempted here.

Table C.1 and Formulas (C.1), (C.2): a table, two formulas and a seam
---------------------------------------------------------------------

Table C.1 prints the ranking positions for samples of 20 to 50 values, and in
every one of its 31 rows :math:`R(q_{0,9}) = N + 1 - R(q_{0,1})`: the table
leaves as many values below :math:`q_{0,1}` as above :math:`q_{0,9}`. For
:math:`N > 50` the standard gives two formulas instead,

.. math::

   R(q_{0,1}) = \mathrm{IP}\!\left(\frac{N + 4}{10}\right) \tag{C.1}

.. math::

   R(q_{0,9}) = \mathrm{IP}\!\left(\frac{9 N}{10}\right) + 1 \tag{C.2}

The two formulas do not treat the table alike. Formula (C.1) continues its
first column exactly: it reproduces all 31 rows, and it is not the rank
:math:`\mathrm{IP}(0{,}1 N) + 1` of the empirical 0,1-quantile, from which it
differs at 570 of the 950 sizes from 51 to 1000 (at ``N`` = 51 that rank is 6,
(C.1) gives 5). Formula (C.2) does not continue the second column: it
reproduces 16 of the 31 rows and gives one rank less for ``N`` = 21 to 25, 31
to 35 and 41 to 45, and at ``N`` = 51 it gives 46 where the symmetry of the
table would give 47. Written in the shape of (C.2), the symmetric rule would
read :math:`\mathrm{IP}((9N + 5)/10) + 1`. The break is in (C.2) alone, and
the pair is not one quantile rule: (C.1) is the table's rule and (C.2) is the
rank :math:`\mathrm{IP}(pN) + 1` of the empirical :math:`p`-quantile.

The standard states the formulas for :math:`N > 50` only, so nothing it prints
contradicts itself, and none of the pages read here says whether the seam is
deliberate or a slip. Annex C is taken from DIN 45687:2006-05, Annex F,
which prints the same table (Tables F.1 and F.2), the same two formulas ((F.1)
and (F.2)) and the same worked example. Its F.4 bases the ranks of the table on
VDI 3723 Blatt 1 (Table 6, column :math:`L_{x,90}`, for :math:`q_{0,1}`;
Table 5, column :math:`L_{x,10}`, for :math:`q_{0,9}`), and introduces the
formulas with "Falls die Anzahl der Stichproben N > 50 ist, gilt ergänzend zu
VDI 3723 Blatt 1 [15] mit ausreichender Übereinstimmung zu E VDI 2450 Blatt 5
[17]:" (printed folio 35): the formulas supplement VDI 3723 Blatt 1, the source
of the table, in sufficient agreement with E VDI 2450 Blatt 5, a draft on the
quantiles of air-pollutant measurements (item [17] of the bibliography,
folio 38). ISO 17534-1 drops both citations: its C.4 keeps only "based on
:math:`L_{x,90}` ... and :math:`L_{x,10}`", and the formulas are introduced by
"If the number of random samples N is >50, the following applies".

VDI 3723 Blatt 1:1993-05 bears the table out and stops where it stops. Its
Tables 5 and 6 (printed pages 7 and 8) give the ranking position ``k`` of the
10 % and the 90 % exceedance levels, :math:`L_{x,10}` and :math:`L_{x,90}`,
for samples of up to 50 values. From 20 to 50 values the column ``k`` of Table
6 is the first column of Table C.1 and the column ``k`` of Table 5 is its
second, row for row, so the symmetry of Table C.1 is already the guideline's.
The guideline gives no formula beyond them: "Die Werte in den Tabellen 4 bis 6
sind auf n = 50 begrenzt", since measurements with a larger sample are hardly
ever made, and for more than 50 values it points to VDI 2450 Blatt 5, a draft
(item [9] of its bibliography, printed page 13), rather than extend its own
rule (page 7). So Formulas (C.1) and (C.2) do not come from VDI 3723 Blatt 1:
DIN 45687 brings them in, in sufficient agreement with E VDI 2450 Blatt 5, and
only that draft could say whether (C.2) was meant to follow it rather than the
symmetry of the table; it has not been read here. A (C.2) that slipped from
the symmetric rule in the national standard and was carried into the
international one, and a (C.2) chosen to agree with E VDI 2450 Blatt 5 while
(C.1) kept the table's rule, both fit the pages that have been read. The seam
is therefore not recorded as an erratum, which needs a defect whose intended
reading the documents establish, and it is not corrected either.

What decides the behaviour is that both standards print (C.2) the same way.
:func:`ranking_positions` applies what they print: Table C.1 from 20 to 50
values, Formulas (C.1) and (C.2) above. A program that extended the symmetric
rule past 50 would report :math:`q_{0,9}` one rank higher than this one for
half of all sample sizes, which is exactly the disagreement between two
quality-assured implementations that ISO 17534-1 is written to prevent.

Three readings the text leaves to the implementer
-------------------------------------------------

**Ordinal numbers from zero.** C.2 numbers the ``N`` remaining single points
consecutively and takes the ordinal numbers
:math:`\mathrm{IP}((i - 0{,}5) N / M)`, ``i`` from 1 to ``M``. Counted from
zero, the ordinals run from :math:`\mathrm{IP}(N / 2M)` to at most ``N - 1``
for every ``N`` at least ``M``, and each sample point sits at the middle of
its ``M``-th of the list. Counted from one, the formula would ask for the
ordinal 0, which does not exist, whenever ``N`` is less than ``2M``. This
module counts from zero, which is also the index a Python array uses.

**Chainages in metres.** C.3 lays the contours out "by consecutive
kilometerage" and places the sample points "at the kilometerages"
:math:`\mathrm{IP}((i - 0{,}5) L / M)` (DIN 45687, F.3: "an den
Kilometrierungen"). A kilometerage is a chainage, a position counted along a
route, and the word names that position, not the unit it is counted in. Taken
in kilometres, the integer part would put every point of a contour shorter
than a kilometre at its start, so the chainage is read in metres, and each
point falls on a whole metre. Two points can share a metre only on contours
shorter than ``M`` metres, though not on all of them (19,5 m of contour still
give 20 points the metres 0 to 19), and a sample in which two do is refused
rather than returned with repeats.

**The sign and the spread of a difference.** A level difference is the
modified configuration's level minus the reference configuration's (the
level of the contour minus the single-point level, for C.3), so a positive
:math:`q_{0,9}` is a shortcut that overestimates. The "estimated standard
deviation" of C.5 is the sample standard deviation, with one degree of freedom
fewer than the sample has values.
"""

from __future__ import annotations

import math
import numbers
import warnings
from dataclasses import dataclass
from fractions import Fraction
from itertools import pairwise
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final

import numpy as np

from ..._internal.frozen import read_only
from ..._internal.validation import (
    require_count,
    require_finite_array,
    require_finite_matrix,
)
from ..._internal.warnings import PhonometryWarning

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "CERTIFIED_RESULT_TOLERANCE_DB",
    "MINIMUM_SAMPLE_SIZE",
    "RANKING_POSITIONS",
    "RECOMMENDED_SAMPLE_RATIO",
    "SAMPLE_CLEARANCE_M",
    "CalculationVerification",
    "LevelDifferenceQuantiles",
    "RoundRobinPrecision",
    "SoftwareQualityWarning",
    "contour_sample_chainages_m",
    "level_difference_quantiles",
    "ranking_positions",
    "round_robin_precision",
    "uniform_sample_indices",
    "verify_calculation_results",
]

#: Table A.5, footnote a: "The result values in frequency bands and for the
#: total level are considered to be correct if the deviation does not exceed
#: +/-0,05 dB." The half-width, in dB, of the interval a test case prints
#: round a correct result given to two decimals, as the limits of Table B.2
#: are (13,65 dB to 13,75 dB round 13,70 dB). A method-specific Technical
#: Report may widen it for a case with open issues (A.2).
#:
#: A.2 and 4.5.2 word the limits differently: they are "given to one decimal
#: place", and "in cases where the final result given to two decimal places is
#: x,x5, an interval of 0,1 is always included for rounding purposes" (13,65
#: gives 13,6 to 13,7, which is 13,65 +/- 0,05). 4.5.2 sends that interval to
#: "rounding aspects (see Table A.5)", and Table B.2 and every test case of
#: ISO/TR 17534-3 print the limits to two decimals at +/-0,05 dB, which is the
#: convention implemented here. :func:`verify_calculation_results` compares
#: with whatever limits it is given, so limits printed either way can be used.
CERTIFIED_RESULT_TOLERANCE_DB: Final = 0.05

#: C.2 and C.3: "The random sample size shall be at least 20." The first row
#: of Table C.1, below which no ranking position is given.
MINIMUM_SAMPLE_SIZE: Final = 20

#: C.2: "It is recommended to select a ratio of random samples to number of
#: single points of at least 1:100." A sample of fewer than one point in a
#: hundred is taken, with a :class:`SoftwareQualityWarning`.
RECOMMENDED_SAMPLE_RATIO: Final = 0.01

#: C.2 and C.3, in metres: receiver points, and sections of sound contours,
#: "having a horizontal distance of less than 2 m from sources and obstacles
#: are excluded" before the sample is drawn.
SAMPLE_CLEARANCE_M: Final = 2.0

#: Table C.1 of ISO 17534-1:2015, printed folio 20: for a sample of ``N``
#: values sorted in ascending order, the ranking positions
#: ``(R(q0,1), R(q0,9))`` of the 0,1-quantile and the 0,9-quantile, counted
#: from 1. The 31 rows from ``N`` = 20 to 50; above 50, Formulas (C.1) and
#: (C.2) apply (see the module docstring for why the two do not join).
RANKING_POSITIONS: Final[Mapping[int, tuple[int, int]]] = MappingProxyType(
    {
        20: (2, 19),
        21: (2, 20),
        22: (2, 21),
        23: (2, 22),
        24: (2, 23),
        25: (2, 24),
        26: (3, 24),
        27: (3, 25),
        28: (3, 26),
        29: (3, 27),
        30: (3, 28),
        31: (3, 29),
        32: (3, 30),
        33: (3, 31),
        34: (3, 32),
        35: (3, 33),
        36: (4, 33),
        37: (4, 34),
        38: (4, 35),
        39: (4, 36),
        40: (4, 37),
        41: (4, 38),
        42: (4, 39),
        43: (4, 40),
        44: (4, 41),
        45: (4, 42),
        46: (5, 42),
        47: (5, 43),
        48: (5, 44),
        49: (5, 45),
        50: (5, 46),
    }
)

#: Relative slack of the limit comparisons of :func:`verify_calculation_results`,
#: so that a result that lands on a limit through floating-point arithmetic
#: (13,65 formed as 13,70 - 0,05) is on it, which "does not exceed" includes.
_BOUNDARY_REL_TOL = 1e-9

#: Absolute slack of the same comparisons, for a limit of zero.
_BOUNDARY_ABS_TOL = 1e-12

#: The fewest participants a round robin can have: one participant has no
#: mean to deviate from.
_MIN_PARTICIPANTS = 2

#: The rank of a round robin's level matrix: receivers by participants.
_MATRIX_RANK = 2


class SoftwareQualityWarning(PhonometryWarning):
    """A sample for Annex C of ISO 17534-1 is thinner than C.2 recommends.

    Emitted by :func:`uniform_sample_indices` when fewer than one point in a
    hundred is drawn (:data:`RECOMMENDED_SAMPLE_RATIO`). The sample is still
    returned: the ratio is a recommendation, and the quantiles of a thinner
    sample are defined, only less representative of the map.
    """


# --------------------------------------------------------------------------- #
# Annex C.4: ranking positions and the characteristic values
# --------------------------------------------------------------------------- #
def ranking_positions(sample_size: int) -> tuple[int, int]:
    r"""Ranking positions of the 0,1- and 0,9-quantiles (ISO 17534-1 C.4).

    For a sample of ``N`` values sorted in ascending order, the positions,
    counted from 1, of the value taken as the 0,1-quantile and of the value
    taken as the 0,9-quantile. Table C.1 (:data:`RANKING_POSITIONS`) from 20 to
    50 values; above 50, Formulas (C.1) and (C.2),

    .. math::

       R(q_{0,1}) = \mathrm{IP}\!\left(\frac{N + 4}{10}\right), \qquad
       R(q_{0,9}) = \mathrm{IP}\!\left(\frac{9 N}{10}\right) + 1,

    with IP the integer part, evaluated here in integer arithmetic so that no
    rounding of ``9N/10`` can move a rank. The table leaves as many values
    below the one quantile as above the other. Formula (C.1) continues the
    table's first column, but Formula (C.2) does not continue its second: it
    leaves one more value above :math:`q_{0,9}` whenever the last digit of
    ``N`` is 1 to 5. ISO 17534-1 and DIN 45687, from which Annex C was taken,
    both print (C.2) this way, and neither says whether the seam is deliberate;
    the module docstring gives what the two documents do say, and why the
    function applies the print.

    :param sample_size: ``N``, the number of values in the sample, at least
        :data:`MINIMUM_SAMPLE_SIZE`.
    :return: ``(R(q0,1), R(q0,9))``.
    :raises ValueError: for a sample smaller than 20, which C.2 does not
        allow and Table C.1 does not cover, or a count that is not a whole
        number.
    """
    n = require_count(sample_size, "sample_size", minimum=MINIMUM_SAMPLE_SIZE)
    printed = RANKING_POSITIONS.get(n)
    if printed is not None:
        return printed
    return (n + 4) // 10, (9 * n) // 10 + 1


@dataclass(frozen=True)
class LevelDifferenceQuantiles:
    r"""The characteristic values of a sample of level differences
    (ISO 17534-1:2015, C.4 and C.5).

    Built by :func:`level_difference_quantiles`. Only the sorted sample is
    stored; the ranking positions, the two quantiles, the mean and the
    standard deviation are read from it, so they cannot disagree with it.

    :ivar sorted_differences_db: The sample of level differences, sorted in
        ascending order as C.4 sorts it, in dB. At least
        :data:`MINIMUM_SAMPLE_SIZE` values.
    """

    sorted_differences_db: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Keep a sorted, read-only copy of a sample C.4 can rank.

        :raises ValueError: for a sample that is not one-dimensional, holds a
            non-finite value, has fewer than 20 values or is not sorted in
            ascending order.
        """
        values = np.array(
            require_finite_array(self.sorted_differences_db, "sorted_differences_db"),
            dtype=np.float64,
        )
        if values.size < MINIMUM_SAMPLE_SIZE:
            msg = (
                "LevelDifferenceQuantiles: C.2 requires a random sample of at "
                f"least {MINIMUM_SAMPLE_SIZE} values; got {values.size}."
            )
            raise ValueError(msg)
        if np.any(np.diff(values) < 0.0):
            msg = (
                "LevelDifferenceQuantiles: 'sorted_differences_db' must be "
                "sorted in ascending order, as C.4 ranks it."
            )
            raise ValueError(msg)
        object.__setattr__(self, "sorted_differences_db", read_only(values))

    @property
    def sample_size(self) -> int:
        """``N``, the number of level differences in the sample."""
        return int(self.sorted_differences_db.size)

    @property
    def rank_q01(self) -> int:
        """:math:`R(q_{0,1})`, the ranking position of the 0,1-quantile."""
        return ranking_positions(self.sample_size)[0]

    @property
    def rank_q09(self) -> int:
        """:math:`R(q_{0,9})`, the ranking position of the 0,9-quantile."""
        return ranking_positions(self.sample_size)[1]

    @property
    def from_table(self) -> bool:
        """Whether the ranks were read from Table C.1 rather than (C.1), (C.2)."""
        return self.sample_size in RANKING_POSITIONS

    @property
    def q01_db(self) -> float:
        """:math:`q_{0,1}`, the value at rank :math:`R(q_{0,1})`, in dB.

        C.2, NOTE 2: 10 % of all the differences are expected below it.
        """
        return float(self.sorted_differences_db[self.rank_q01 - 1])

    @property
    def q09_db(self) -> float:
        """:math:`q_{0,9}`, the value at rank :math:`R(q_{0,9})`, in dB.

        C.2, NOTE 2: 10 % of all the differences are expected above it.
        """
        return float(self.sorted_differences_db[self.rank_q09 - 1])

    @property
    def mean_db(self) -> float:
        """The average of the difference group, in dB.

        C.5: the value "specified for considering a systematic deviation".
        """
        return float(np.mean(self.sorted_differences_db))

    @property
    def standard_deviation_db(self) -> float:
        """The estimated standard deviation of the difference group, in dB.

        C.5: the uncertainty to carry into an error-propagation calculation
        by ISO/IEC Guide 98-3. The sample standard deviation, with ``N - 1``
        degrees of freedom.
        """
        return float(np.std(self.sorted_differences_db, ddof=1))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the sorted sample by rank, with the two quantiles marked.

        Each difference is a point at its ranking position; the two ranks
        of C.4 and the values they pick are marked, and the band between
        :math:`q_{0,1}` and :math:`q_{0,9}` that holds the central 80 % is
        shaded.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the line of sample points.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_level_difference_quantiles

        return plot_level_difference_quantiles(
            self, ax=ax, language=check_language(language), **kwargs
        )


def level_difference_quantiles(
    level_differences_db: ArrayLike,
) -> LevelDifferenceQuantiles:
    r"""The 0,1- and 0,9-quantiles of a sample of level differences
    (ISO 17534-1:2015, C.4).

    The sample is sorted in ascending order and the values at the ranking
    positions of :func:`ranking_positions` are the two characteristic values:
    it "shall be expected that 10 % of all level differences in the
    calculation area are each below" :math:`q_{0,1}` "and above"
    :math:`q_{0,9}`. For a modified configuration judged against the
    reference configuration (5.2.3, 7.2), pass the modified configuration's
    levels minus the reference configuration's at the same sample points
    (:func:`uniform_sample_indices` chooses them).

    The worked example that follows Table C.1: the 25 differences it prints
    give :math:`R(q_{0,1}) = 2`, :math:`R(q_{0,9}) = 24`,
    :math:`q_{0,1} = -1` dB and :math:`q_{0,9} = 3` dB.

    :param level_differences_db: The sample of level differences, in dB, in
        any order; at least :data:`MINIMUM_SAMPLE_SIZE` values.
    :return: A :class:`LevelDifferenceQuantiles`.
    :raises ValueError: for fewer than 20 values, a non-finite value or an
        input that is not one-dimensional.
    """
    values = require_finite_array(level_differences_db, "level_differences_db")
    if values.size < MINIMUM_SAMPLE_SIZE:
        msg = (
            "C.2 of ISO 17534-1 requires a random sample of at least "
            f"{MINIMUM_SAMPLE_SIZE} level differences; got {values.size}."
        )
        raise ValueError(msg)
    return LevelDifferenceQuantiles(sorted_differences_db=np.sort(values))


# --------------------------------------------------------------------------- #
# Annex C.2 and C.3: where the sample is taken
# --------------------------------------------------------------------------- #
def uniform_sample_indices(
    point_count: int,
    sample_size: int,
    *,
    horizontal_clearances_m: ArrayLike | None = None,
) -> NDArray[np.intp]:
    r"""The single points of a uniform random sample (ISO 17534-1:2015, C.2).

    Of the ``N`` single points that remain once those closer than
    :data:`SAMPLE_CLEARANCE_M` to a source or an obstacle are left out, the
    sample of size ``M`` takes the points of ordinal number

    .. math::

       \mathrm{IP}\!\left((i - 0{,}5)\,\frac{N}{M}\right),
       \qquad i = 1, \ldots, M,

    counted from zero (the module docstring says why), evaluated in integer
    arithmetic as :math:`\lfloor (2i - 1) N / 2M \rfloor`. A sample of fewer
    than one point in a hundred is returned with a
    :class:`SoftwareQualityWarning`, the ratio C.2 recommends.

    :param point_count: How many single points there are (grid receivers,
        points along a street), before any is left out.
    :param sample_size: ``M``, the random sample size, at least
        :data:`MINIMUM_SAMPLE_SIZE` and at most the number of points that
        remain.
    :param horizontal_clearances_m: Optional, one value per point: its
        horizontal distance to the nearest source or obstacle, in metres. The
        points at less than 2 m are left out before numbering; without it,
        every point takes part.
    :return: The indices of the sampled points among the ``point_count``
        points, in increasing order.
    :raises ValueError: for a sample smaller than 20 or larger than the
        points that remain, or clearances that are not one finite,
        non-negative value per point.
    """
    count = require_count(point_count, "point_count")
    size = require_count(sample_size, "sample_size", minimum=MINIMUM_SAMPLE_SIZE)
    if horizontal_clearances_m is None:
        eligible = np.arange(count, dtype=np.intp)
    else:
        clearances = require_finite_array(
            horizontal_clearances_m, "horizontal_clearances_m"
        )
        if clearances.size != count:
            msg = (
                "'horizontal_clearances_m' must hold one distance per point; "
                f"got {clearances.size} for {count} points."
            )
            raise ValueError(msg)
        if np.any(clearances < 0.0):
            msg = "'horizontal_clearances_m' must not hold a negative distance."
            raise ValueError(msg)
        eligible = np.flatnonzero(clearances >= SAMPLE_CLEARANCE_M).astype(np.intp)
    remaining = int(eligible.size)
    if size > remaining:
        msg = (
            f"A sample of {size} cannot be drawn from {remaining} single points "
            f"at {SAMPLE_CLEARANCE_M:g} m or more from sources and obstacles."
        )
        raise ValueError(msg)
    if size < RECOMMENDED_SAMPLE_RATIO * remaining:
        warnings.warn(
            f"A sample of {size} from {remaining} single points is thinner "
            "than the ratio of at least 1:100 that C.2 of ISO 17534-1 "
            "recommends.",
            SoftwareQualityWarning,
            stacklevel=2,
        )
    i = np.arange(1, size + 1, dtype=np.int64)
    ordinals = ((2 * i - 1) * remaining) // (2 * size)
    return eligible[ordinals]


def contour_sample_chainages_m(
    total_length_m: float, sample_size: int
) -> NDArray[np.float64]:
    r"""Where the sample points sit on the sound contours (ISO 17534-1:2015, C.3).

    With the contours to be designated laid end to end (their sections within
    :data:`SAMPLE_CLEARANCE_M` of a source or an obstacle left out) to a total
    length ``L``, the ``M`` sample points sit at the chainages

    .. math::

       \mathrm{IP}\!\left((i - 0{,}5)\,\frac{L}{M}\right),
       \qquad i = 1, \ldots, M,

    read in metres, so that each point falls on a whole metre (the module
    docstring says why). The formula is evaluated exactly, in integer
    arithmetic on the decimal value of the length, as
    :math:`\lfloor (2i - 1) L / 2M \rfloor`: through a rounded quotient
    ``L/M``, a chainage that is a whole number of metres can come out a metre
    short (115 m for ``L`` = 184 m and ``M`` = 20, where ``L/M`` is 9,2), and
    through the binary fraction nearest a decimal length such as 22,4 m, so
    can one that the decimal length puts on a whole metre. The level of the
    contour there is compared with a single-point calculation at the same
    place, and the differences go to :func:`level_difference_quantiles`.

    :param total_length_m: ``L``, the length of the contours that remain, in
        metres, long enough that no two points share a whole metre, which is
        always so from ``sample_size`` metres on.
    :param sample_size: ``M``, at least :data:`MINIMUM_SAMPLE_SIZE`.
    :return: The ``M`` chainages, in metres, in increasing order.
    :raises ValueError: for a sample smaller than 20, a length that is not a
        finite, positive number (a string or a bool included), or contours so
        short that two points would fall on the same whole metre, which
        happens only below ``M`` metres.
    """
    size = require_count(sample_size, "sample_size", minimum=MINIMUM_SAMPLE_SIZE)
    # A string or a bool would convert through float() ("100" to 100.0, True
    # to 1.0) and be sampled as though it were a length.
    if isinstance(total_length_m, bool) or not isinstance(total_length_m, numbers.Real):
        msg = f"'total_length_m' must be a length in metres, got {total_length_m!r}."
        raise ValueError(msg)
    length = float(total_length_m)
    if not (math.isfinite(length) and length > 0.0):
        msg = f"'total_length_m' must be finite and positive, got {total_length_m!r}."
        raise ValueError(msg)
    # The shortest decimal that reads back as the length: what was written.
    numerator, denominator = Fraction(repr(length)).as_integer_ratio()
    chainages = [
        ((2 * i - 1) * numerator) // (2 * size * denominator)
        for i in range(1, size + 1)
    ]
    if any(later <= earlier for earlier, later in pairwise(chainages)):
        msg = (
            f"On contours {length:g} m long, two of the {size} sample points "
            "C.3 would place fall on the same whole metre."
        )
        raise ValueError(msg)
    return np.array(chainages, dtype=np.float64)


# --------------------------------------------------------------------------- #
# 4.5.2 and A.3: the precision of a method across programs
# --------------------------------------------------------------------------- #
def _level_matrix(levels_db: ArrayLike) -> NDArray[np.float64]:
    """A round robin's levels as a float64 matrix C.4 can rank, or a refusal.

    The shared matrix guard names ``levels_db`` when numpy cannot read it
    (ragged rows, strings) and refuses a complex matrix, which a plain
    ``float64`` cast would take with its imaginary part dropped. It reads a
    single row as a matrix of one row; a round robin is a table, so a
    one-dimensional input is refused here instead.

    :raises ValueError: for a matrix that is not two-dimensional, is not
        numeric, holds a complex or a non-finite value, has fewer than 20
        receivers or fewer than two participants.
    """
    levels = require_finite_matrix(levels_db, "levels_db")
    if np.ndim(levels_db) != _MATRIX_RANK:
        msg = (
            "RoundRobinPrecision: 'levels_db' must be a two-dimensional array "
            "of levels, one row per receiver and one column per participant."
        )
        raise ValueError(msg)
    receivers, participants = levels.shape
    if receivers < MINIMUM_SAMPLE_SIZE or participants < _MIN_PARTICIPANTS:
        msg = (
            f"RoundRobinPrecision: C.4 ranks at least {MINIMUM_SAMPLE_SIZE} "
            f"receivers and a mean needs at least {_MIN_PARTICIPANTS} "
            f"participants; got {receivers} receivers and {participants} "
            "participants."
        )
        raise ValueError(msg)
    return np.array(levels, dtype=np.float64)


@dataclass(frozen=True)
class RoundRobinPrecision:
    r"""The precision of a method in a round robin of programs
    (ISO 17534-1:2015, 4.5.2 and A.3, Example 1).

    ``M`` participants calculate the same ``N`` receivers with the same
    method. At receiver ``n`` the mean :math:`\bar L_n` is the arithmetic mean
    of the ``M`` levels, each participant deviates from it by
    :math:`dL_{n,m} = L_{n,m} - \bar L_n`, and :math:`|dL_n|_{\max}` is the
    largest of the ``M`` absolute deviations. "The result of such a round
    robin test is the quantile :math:`q_{0,9}` according to C.4 of the ``N``
    maximal absolute differences."

    Built by :func:`round_robin_precision`. Only the levels are stored;
    everything else is read from them.

    :ivar levels_db: :math:`L_{n,m}`, shape ``(N, M)``: one row per receiver,
        one column per participant, in dB.
    """

    levels_db: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Keep a read-only copy of a level matrix C.4 can rank.

        :raises ValueError: for a matrix that is not two-dimensional, is not
            numeric, holds a complex or a non-finite value, has fewer than 20
            receivers or fewer than two participants.
        """
        object.__setattr__(self, "levels_db", read_only(_level_matrix(self.levels_db)))

    @property
    def receivers(self) -> int:
        """``N``, the number of receiver positions."""
        return int(self.levels_db.shape[0])

    @property
    def participants(self) -> int:
        """``M``, the number of participants."""
        return int(self.levels_db.shape[1])

    @property
    def mean_levels_db(self) -> NDArray[np.float64]:
        r""":math:`\bar L_n`, the arithmetic mean at each receiver, in dB."""
        return np.mean(self.levels_db, axis=1)

    @property
    def deviations_db(self) -> NDArray[np.float64]:
        r""":math:`dL_{n,m} = L_{n,m} - \bar L_n`, shape ``(N, M)``, in dB."""
        return self.levels_db - self.mean_levels_db[:, None]

    @property
    def max_abs_deviations_db(self) -> NDArray[np.float64]:
        r""":math:`|dL_n|_{\max}`, the largest absolute deviation at each receiver, in dB."""
        return np.max(np.abs(self.deviations_db), axis=1)

    @property
    def rank_q09(self) -> int:
        r""":math:`R(q_{0,9})` for ``N`` receivers (:func:`ranking_positions`)."""
        return ranking_positions(self.receivers)[1]

    @property
    def q09_db(self) -> float:
        r""":math:`q_{0,9}` of the ``N`` values of :math:`|dL_n|_{\max}`, in dB.

        "A value showing up the precision of the calculation method applied
        with the different software applied" (A.3, Example 1).
        """
        ranked = np.sort(self.max_abs_deviations_db)
        return float(ranked[self.rank_q09 - 1])

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Draw the distribution of :math:`|dL_n|_{\max}`, as Figure A.3 does.

        A histogram of the largest absolute deviations with :math:`q_{0,9}`
        marked. Figure A.3 counts them in classes 0,1 dB wide; here the
        class width is the narrowest round one (0,05 dB, 0,1 dB, 0,2 dB and
        so on) that draws the widest deviation in at most 25 classes.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the histogram bars.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_round_robin_precision

        return plot_round_robin_precision(
            self, ax=ax, language=check_language(language), **kwargs
        )


def round_robin_precision(levels_db: ArrayLike) -> RoundRobinPrecision:
    r"""The precision of a method from a round robin of programs
    (ISO 17534-1:2015, 4.5.2 and A.3).

    :param levels_db: :math:`L_{n,m}`, the level each of ``M`` participants
        calculated at each of ``N`` receivers, in dB: shape ``(N, M)``, at
        least 20 receivers and two participants.
    :return: A :class:`RoundRobinPrecision`; its ``q09_db`` is the result of
        the round robin.
    :raises ValueError: for a matrix of the wrong shape, one that is not
        numeric, or one with a complex or a non-finite level.
    """
    return RoundRobinPrecision(levels_db=_level_matrix(levels_db))


# --------------------------------------------------------------------------- #
# 7.1 and Annex B: a program's results against the certified ones
# --------------------------------------------------------------------------- #
def _inside(value: float, lower: float, upper: float) -> bool:
    """Whether ``value`` does not exceed the interval, a last-bit excess forgiven."""
    return (
        lower <= value
        or math.isclose(
            value, lower, rel_tol=_BOUNDARY_REL_TOL, abs_tol=_BOUNDARY_ABS_TOL
        )
    ) and (
        value <= upper
        or math.isclose(
            value, upper, rel_tol=_BOUNDARY_REL_TOL, abs_tol=_BOUNDARY_ABS_TOL
        )
    )


@dataclass(frozen=True)
class CalculationVerification:
    r"""A program's results against the limits of the certified results: the
    TRC form of ISO 17534-1:2015 (clause 7.1, Tables B.1 and B.2).

    One row per result (a band or a total of a test case): the program's
    result, the lower and upper limits of the certified result, and whether
    the result is inside them, the "Result inside tolerances yes/no" column.
    A limit is included: a deviation that reaches the tolerance "does not
    exceed" it.

    :ivar results_db: The program's results, in dB, in the reference
        configuration.
    :ivar lower_limits_db: The lower limit of each certified result, in dB.
    :ivar upper_limits_db: The upper limit of each certified result, in dB.
    :ivar labels: A name for each row (``"63 Hz"``, ``"Total"``, ``"T03
        500 Hz"``).
    """

    results_db: NDArray[np.float64]
    lower_limits_db: NDArray[np.float64]
    upper_limits_db: NDArray[np.float64]
    labels: tuple[str, ...]

    def __post_init__(self) -> None:
        """Keep read-only copies of three columns of one length and their labels.

        :raises ValueError: for columns of different lengths, a non-finite
            value, a row whose lower limit is above its upper limit, or a
            label count that does not match.
        """
        columns = {}
        for name in ("results_db", "lower_limits_db", "upper_limits_db"):
            columns[name] = np.array(
                require_finite_array(getattr(self, name), name), dtype=np.float64
            )
        sizes = {name: column.size for name, column in columns.items()}
        if len(set(sizes.values())) != 1:
            msg = (
                "CalculationVerification: the results and the two limits must "
                f"have one value per row; got {sizes}."
            )
            raise ValueError(msg)
        if np.any(columns["lower_limits_db"] > columns["upper_limits_db"]):
            msg = (
                "CalculationVerification: every lower limit must be at or "
                "below its upper limit."
            )
            raise ValueError(msg)
        labels = tuple(str(label) for label in self.labels)
        if len(labels) != sizes["results_db"]:
            msg = (
                "CalculationVerification: 'labels' must name every row; got "
                f"{len(labels)} labels for {sizes['results_db']} rows."
            )
            raise ValueError(msg)
        for name, column in columns.items():
            object.__setattr__(self, name, read_only(column))
        object.__setattr__(self, "labels", labels)

    @property
    def inside(self) -> tuple[bool, ...]:
        """For each row, whether the result is inside its limits (yes/no)."""
        return tuple(
            _inside(float(value), float(lower), float(upper))
            for value, lower, upper in zip(
                self.results_db,
                self.lower_limits_db,
                self.upper_limits_db,
                strict=True,
            )
        )

    @property
    def passes(self) -> bool:
        """Whether every result is inside its limits: the verdict of the form."""
        return all(self.inside)

    @property
    def failing_labels(self) -> tuple[str, ...]:
        """The rows whose result is outside its limits, in order."""
        return tuple(
            label for label, ok in zip(self.labels, self.inside, strict=True) if not ok
        )

    @property
    def deviations_db(self) -> NDArray[np.float64]:
        """Each result minus the centre of its certified interval, in dB."""
        centres = 0.5 * (self.lower_limits_db + self.upper_limits_db)
        return self.results_db - centres

    @property
    def margins_db(self) -> NDArray[np.float64]:
        """How far each result is from the nearer limit, in dB.

        Positive inside the interval, zero on a limit, negative by the amount
        a result is outside.
        """
        return np.minimum(
            self.results_db - self.lower_limits_db,
            self.upper_limits_db - self.results_db,
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        An object is always true, so ``if verify_calculation_results(...):``
        would pass every program whatever it computed. The verdict is
        :attr:`passes`.

        :raises TypeError: Always.
        """
        msg = (
            "a CalculationVerification has no truth value; read its '.passes' "
            "for the verdict, or '.inside' row by row"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw each result against its certified interval, row by row.

        Every row is centred on its certified interval, so intervals a
        tenth of a decibel wide on levels tens of decibels apart can be read
        side by side: the shaded bar is the interval and the marker the
        program's deviation from its centre, a dot inside and a cross outside.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the line of result markers.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_calculation_verification

        return plot_calculation_verification(
            self, ax=ax, language=check_language(language), **kwargs
        )


def verify_calculation_results(
    results_db: ArrayLike,
    lower_limits_db: ArrayLike,
    upper_limits_db: ArrayLike,
    *,
    labels: Sequence[str] | None = None,
) -> CalculationVerification:
    r"""Is a program's result inside the limits of every certified result?
    (ISO 17534-1:2015, clause 7.1 and Annex B)

    The comparison a user makes with each new installation or update, and a
    producer declares in the TRC form of the declaration of conformity:
    every result a test case certifies, calculated by the program in its
    reference configuration, against the upper and lower limits the test case
    prints. A test case of ISO/TR 17534-3 prints a correct result to two
    decimals and, by Table A.5, a result is correct within
    :data:`CERTIFIED_RESULT_TOLERANCE_DB` of it, so its limits are the
    certified result minus and plus 0,05 dB. Table B.2 is the worked form:
    eight octave bands and a total of the test case "T XX", every result
    inside.

    :param results_db: The program's results, in dB, one per row.
    :param lower_limits_db: The lower limit of each certified result, in dB.
    :param upper_limits_db: The upper limit of each certified result, in dB.
    :param labels: A name for each row; by default ``"1"``, ``"2"``, and so
        on.
    :return: A :class:`CalculationVerification`, whose ``passes`` is the
        verdict and ``inside`` the column of the form.
    :raises ValueError: for columns of different lengths, a non-finite value
        or a lower limit above its upper limit.
    """
    results = require_finite_array(results_db, "results_db")
    names = (
        tuple(str(index + 1) for index in range(results.size))
        if labels is None
        else tuple(labels)
    )
    return CalculationVerification(
        results_db=results,
        lower_limits_db=require_finite_array(lower_limits_db, "lower_limits_db"),
        upper_limits_db=require_finite_array(upper_limits_db, "upper_limits_db"),
        labels=names,
    )
