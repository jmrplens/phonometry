#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What a road surface adds to the noise of the traffic on it (ISO 11819-1:1997).

A road surface is not a source, but it changes how loud every tyre on it is,
and the Statistical Pass-By (SPB) method is how that change is measured. A
microphone stands 7,5 m from the centre of the lane and 1,2 m above it, and for
each vehicle that passes on its own, the maximum A-weighted level with time
weighting F and the speed are written down, together with the vehicle's
category: cars (1), dual-axle heavy vehicles (2a) or multi-axle heavy vehicles
(2b). Other vehicles are not used (clause 4).

**9.1 and 9.2, the vehicle sound level.** For each category the levels are
regressed on the logarithm of the speed by least squares,

.. math::

   L_{\mathrm{AFmax}} = a + b \lg \frac{v}{1\ \mathrm{km/h}},

and the ordinate of that line at the reference speed of Table 1 is the vehicle
sound level :math:`L_\mathrm{veh}` of the category (:func:`pass_by_regression`).
The reference speed depends on the road speed category of 3.3 (low, medium,
high) and is the same for the two heavy categories.

**9.5, the index.** The three vehicle sound levels are added on an energy basis,
each weighted by the proportion :math:`W_x` of its category in a standard mix
and the heavy ones by the ratio of the car reference speed to their own:

.. math::

   \mathrm{SPBI} = 10 \lg \left[ W_1 \, 10^{L_1/10}
     + W_{2a} \frac{v_1}{v_{2a}} 10^{L_{2a}/10}
     + W_{2b} \frac{v_1}{v_{2b}} 10^{L_{2b}/10} \right]

(:func:`statistical_pass_by_index`). The index is for comparing surfaces, not
for predicting a traffic noise level (9.5 NOTE), and the comparison clause 10
has in mind is a difference from a reference surface, of which Annex D gives an
example built from seven dense bituminous surfaces
(:func:`normalized_reference_levels`, :data:`SPB_NORMALIZED_REFERENCE_DB`).

**The rounding chain.** 9.2 ends "All levels shall be calculated to two decimal
places and rounded to one decimal place", and 9.5 defines the levels the index
adds as "the Vehicle Sound Levels ... according to 9.2". The index is therefore
the index of the three vehicle sound levels rounded to one decimal, the ones a
report prints, which is what lets anyone recompute it from the report: 7.4 asks
for "the sound levels Lveh and the SPBI calculated from them", and 9.5 says the
mandatory reporting of every :math:`L_\mathrm{veh}` allows the index to be
recalculated with other weighting factors. The regressions are carried at full
precision, each level is rounded once, and the index is rounded once when it is
reported (the ``reported_`` properties); both roundings are half up, a
convention of this module, since 9.2 gives no rule for a level on the half.
"Two decimal places" is read as the least precision of the calculation, not as
a first rounding: rounded to 0,01 dB and then to 0,1 dB, 79,946 dB would print
80,0 dB. Temperature-corrected levels and a reference given as levels enter
their indices rounded the same way.

The example of Annex E is reproduced by this chain: its levels 78,5, 81,1 and
83,8 dB give 79,946 dB, printed 79,9 dB. Carried at full precision from the
coefficients Annex E prints, the same levels are 78,546, 81,114 and 83,838 dB,
and their index, 79,985 dB, would print 80,0 dB
(:attr:`StatisticalPassByResult.full_precision_index_db`). The printed
coefficients are rounded too, so the page alone does not prove which chain the
example was computed with: over every line that agrees with the intercept,
slope, mean level, mean speed and vehicle sound level Annex E prints, to their
last printed digit, the full-precision index spans 79,948 dB to 79,996 dB, and
only the corner below 79,95 dB would also print 79,9 dB.

**9.3 and 7.3, as warnings.** The regression is only used to normalize to the
reference speed if that speed lies within one standard deviation of the
measured mean speed for the heavy vehicles and one and a half for the cars. The
mean and the standard deviation are those of :math:`\lg v`, the variable the
line is fitted in; the speed printed in Annex E is marked "converted from the
logarithm of speed", and the mean it prints is :math:`10^{\overline{\lg v}}`.
For surface classification, 7.3 asks for at least 100 cars, 30 vehicles of each
heavy category and 80 heavy vehicles in all. Both conditions are judged, kept
on the result and, when they fail, emitted as
:class:`StatisticalPassByWarning` rather than raised: a before-and-after study
(6.6) is still an SPB measurement.

**9.4, temperature.** The vehicle sound levels should be corrected to an air
temperature of 20 °C, and the standard says a suitable method is under
consideration. None is implemented here: temperature-corrected levels are an
input (``corrected_vehicle_sound_levels_db``), and the index is then computed
for both. Clause 13 lists the corrected levels and index as optional report
items (26 and 28) beside the mandatory uncorrected ones (25 and 27).

**9.6, the random errors.** Table 2 gives the spread expected of individual
vehicles about :math:`L_\mathrm{veh}` and the 95 % confidence interval that
spread leaves on it for 100 cars and 40 heavy vehicles of each type
(:data:`SPB_VEHICLE_STANDARD_DEVIATIONS_DB`, :data:`SPB_CONFIDENCE_INTERVALS_DB`).
A regression also returns the confidence interval of its own line at the
reference speed, from the Student distribution with :math:`n - 2` degrees of
freedom, and the result combines the three into an interval on the index with
the sensitivity of the index to each level. The standard says the index error
"will be a combination of these errors according to the chosen weighting
factors" and gives no formula; the combination here assumes the three
categories independent.

Read from BS EN ISO 11819-1:2001, which is identical to ISO 11819-1:1997 (its
national foreword).
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.frozen import read_only
from ..._internal.validation import (
    require_choice,
    require_finite,
    require_finite_array,
    require_positive_array,
)
from ..._internal.warnings import PhonometryWarning

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "SPB_ANNEX_D_SURFACES_DB",
    "SPB_CONFIDENCE_INTERVALS_DB",
    "SPB_MINIMUM_VEHICLE_COUNTS",
    "SPB_NORMALIZED_REFERENCE_DB",
    "SPB_REFERENCE_AIR_TEMPERATURE_C",
    "SPB_REFERENCE_SPEEDS_KMH",
    "SPB_ROAD_SPEED_CATEGORIES",
    "SPB_SPEED_WINDOW_STANDARD_DEVIATIONS",
    "SPB_VEHICLE_CATEGORIES",
    "SPB_VEHICLE_STANDARD_DEVIATIONS_DB",
    "SPB_WEIGHTING_FACTORS",
    "PassByRegression",
    "StatisticalPassByResult",
    "StatisticalPassByWarning",
    "normalized_reference_levels",
    "pass_by_regression",
    "statistical_pass_by",
    "statistical_pass_by_index",
]


class StatisticalPassByWarning(PhonometryWarning):
    """A pass-by data set falls short of a condition ISO 11819-1 states."""


#: 3.4 and clause 4: the three vehicle categories the method uses, cars (1),
#: dual-axle heavy vehicles (2a) and multi-axle heavy vehicles (2b). The other
#: categories of Annex A (other light vehicles, motorcycles) are not used.
SPB_VEHICLE_CATEGORIES: tuple[str, ...] = ("1", "2a", "2b")

#: 3.3: the three road speed categories, in the order Table 1 prints them.
SPB_ROAD_SPEED_CATEGORIES: tuple[str, ...] = ("low", "medium", "high")

#: Table 1: the reference speed of each vehicle category in each road speed
#: category, in kilometres per hour.
SPB_REFERENCE_SPEEDS_KMH: Mapping[str, Mapping[str, float]] = MappingProxyType(
    {
        "low": MappingProxyType({"1": 50.0, "2a": 50.0, "2b": 50.0}),
        "medium": MappingProxyType({"1": 80.0, "2a": 70.0, "2b": 70.0}),
        "high": MappingProxyType({"1": 110.0, "2a": 85.0, "2b": 85.0}),
    }
)

#: Table 1: the weighting factor :math:`W_x` of each vehicle category in each
#: road speed category, the assumed proportion of the category in the traffic.
#: Each column adds up to 1.
SPB_WEIGHTING_FACTORS: Mapping[str, Mapping[str, float]] = MappingProxyType(
    {
        "low": MappingProxyType({"1": 0.900, "2a": 0.075, "2b": 0.025}),
        "medium": MappingProxyType({"1": 0.800, "2a": 0.100, "2b": 0.100}),
        "high": MappingProxyType({"1": 0.700, "2a": 0.075, "2b": 0.225}),
    }
)

#: 7.3: the fewest vehicles to be measured for surface classification, by
#: category, with ``"2"`` for the two heavy categories together.
SPB_MINIMUM_VEHICLE_COUNTS: Mapping[str, int] = MappingProxyType(
    {"1": 100, "2a": 30, "2b": 30, "2": 80}
)

#: 9.3: how many standard deviations of the measured speed the reference speed
#: may lie from the measured mean speed, one and a half for cars and one for
#: the heavy vehicles.
SPB_SPEED_WINDOW_STANDARD_DEVIATIONS: Mapping[str, float] = MappingProxyType(
    {"1": 1.5, "2a": 1.0, "2b": 1.0}
)

#: Table 2: the standard deviation of individual vehicles about
#: :math:`L_\mathrm{veh}`, with the speed effect removed, expected for the
#: "medium" and "high" road speed categories, in decibels.
SPB_VEHICLE_STANDARD_DEVIATIONS_DB: Mapping[str, float] = MappingProxyType(
    {"1": 1.5, "2a": 2.0, "2b": 2.0}
)

#: Table 2: the 95 % confidence interval around :math:`L_\mathrm{veh}` those
#: standard deviations leave, in decibels, for 100 cars and 40 heavy vehicles
#: of each type (the NOTE under the table).
SPB_CONFIDENCE_INTERVALS_DB: Mapping[str, float] = MappingProxyType(
    {"1": 0.3, "2a": 0.7, "2b": 0.7}
)

#: 9.4: the air temperature the vehicle sound levels should be corrected to,
#: in degrees Celsius. The standard gives no correction method.
SPB_REFERENCE_AIR_TEMPERATURE_C: float = 20.0

#: Annex D, the table printed as "Table E.1": the vehicle sound levels, in
#: decibels, of the seven dense surfaces a normalized reference case for the
#: medium speed range was built from. A1 to A4 are asphalt concrete (2, 4, 10
#: and 5 years old, maximum chippings 12, 14, 11 and 16 mm) and B1 to B3 stone
#: mastic asphalt (4, 3 and 7 years, 12, 14 and 16 mm). An example, not a
#: reference the standard sets.
SPB_ANNEX_D_SURFACES_DB: Mapping[str, Mapping[str, float]] = MappingProxyType(
    {
        "A1": MappingProxyType({"1": 76.6, "2a": 81.1, "2b": 84.1}),
        "A2": MappingProxyType({"1": 75.9, "2a": 80.0, "2b": 83.0}),
        "A3": MappingProxyType({"1": 76.4, "2a": 81.8, "2b": 84.0}),
        "A4": MappingProxyType({"1": 77.2, "2a": 81.5, "2b": 84.9}),
        "B1": MappingProxyType({"1": 76.1, "2a": 81.0, "2b": 84.4}),
        "B2": MappingProxyType({"1": 76.4, "2a": 80.4, "2b": 83.3}),
        "B3": MappingProxyType({"1": 76.4, "2a": 81.0, "2b": 84.1}),
    }
)

#: Annex D: the "Average surface (Normalized reference case)" row, the vehicle
#: sound levels of the example's fictitious reference surface for the medium
#: speed range, in decibels.
SPB_NORMALIZED_REFERENCE_DB: Mapping[str, float] = MappingProxyType(
    {"1": 76.4, "2a": 81.0, "2b": 84.0}
)

#: The fewest pass-bys a regression line can be fitted through and still leave
#: a residual standard deviation, which divides by ``n - 2``.
_MIN_PASS_BYS = 3

#: The coverage of the confidence intervals computed from the data, the one
#: Table 2 prints.
_CONFIDENCE_LEVEL = 0.95

#: How far the weighting factors may add up away from 1 before they are not
#: proportions any more.
_WEIGHT_SUM_TOLERANCE = 1e-9

#: The heavy vehicles, which 7.3 also counts together.
_HEAVY_CATEGORIES: tuple[str, ...] = ("2a", "2b")


def _round_tenth(value: float) -> float:
    """Round a level to the one decimal place of 9.2.

    A level on the half goes up. That is a convention of this module: 9.2 says
    only "rounded to one decimal place" and gives no rule for the half.
    """
    return math.floor(value * 10.0 + 0.5) / 10.0


def _reported_levels(levels_db: Mapping[str, float]) -> dict[str, float]:
    """Three vehicle sound levels as 9.2 reports them, to one decimal."""
    return {key: _round_tenth(value) for key, value in levels_db.items()}


def _road_category(road_speed_category: str) -> str:
    return require_choice(
        road_speed_category, "road_speed_category", SPB_ROAD_SPEED_CATEGORIES
    )


def _vehicle_category(vehicle_category: object) -> str:
    key = str(vehicle_category).strip().lower()
    if key not in SPB_VEHICLE_CATEGORIES:
        msg = (
            f"vehicle category {vehicle_category!r} is not one ISO 11819-1 uses; "
            "the method measures cars ('1'), dual-axle heavy vehicles ('2a') and "
            "multi-axle heavy vehicles ('2b') only (clause 4)."
        )
        raise ValueError(msg)
    return key


def _per_category(values: Mapping[str, float], name: str) -> dict[str, float]:
    """Read a mapping holding exactly one finite value per vehicle category."""
    keys = {_vehicle_category(key) for key in values}
    if keys != set(SPB_VEHICLE_CATEGORIES) or len(values) != len(keys):
        msg = f"'{name}' must hold one value for each of '1', '2a' and '2b'."
        raise ValueError(msg)
    return {
        _vehicle_category(key): require_finite(float(value), f"{name}[{key!r}]")
        for key, value in values.items()
    }


def _weights(
    weighting_factors: Mapping[str, float] | None, road_speed_category: str
) -> dict[str, float]:
    if weighting_factors is None:
        return dict(SPB_WEIGHTING_FACTORS[road_speed_category])
    weights = _per_category(weighting_factors, "weighting_factors")
    if any(w < 0.0 for w in weights.values()):
        msg = "'weighting_factors' must not be negative."
        raise ValueError(msg)
    total = sum(weights.values())
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=_WEIGHT_SUM_TOLERANCE):
        msg = (
            "'weighting_factors' are proportions of the traffic and must add up "
            f"to 1 (9.5); these add up to {total:g}."
        )
        raise ValueError(msg)
    return weights


def _index_terms(
    levels_db: Mapping[str, float], weights: Mapping[str, float], road: str
) -> dict[str, float]:
    """The three energy terms of the 9.5 sum, by vehicle category."""
    speeds = SPB_REFERENCE_SPEEDS_KMH[road]
    car_speed = speeds["1"]
    return {
        key: weights[key] * (car_speed / speeds[key]) * 10.0 ** (levels_db[key] / 10.0)
        for key in SPB_VEHICLE_CATEGORIES
    }


def statistical_pass_by_index(
    vehicle_sound_levels_db: Mapping[str, float],
    *,
    road_speed_category: str,
    weighting_factors: Mapping[str, float] | None = None,
) -> float:
    r"""The Statistical Pass-By Index of three vehicle sound levels, 9.5.

    .. math::

       \mathrm{SPBI} = 10 \lg \left[ W_1 \, 10^{L_1/10}
         + W_{2a} \frac{v_1}{v_{2a}} 10^{L_{2a}/10}
         + W_{2b} \frac{v_1}{v_{2b}} 10^{L_{2b}/10} \right]

    with the reference speeds and the weighting factors of Table 1 for the road
    speed category. The heavy terms carry the ratio of the car reference speed
    to their own because a vehicle that goes slower is heard for longer: the
    ratio weights each category by the time its vehicles take to pass, so that
    a difference in SPBI between two surfaces is the difference in equivalent
    level for the reference speeds and proportions of Table 1 (9.5). The index
    itself is not an equivalent level of traffic noise (9.5 NOTE).

    Whatever levels are handed in are used as they are. Handed the three levels
    a report prints to one decimal, this is the index a third party computes
    from the report, which 9.5 anticipates, and the index
    :func:`statistical_pass_by` reports, which rounds its levels that way
    before calling this.

    :param vehicle_sound_levels_db: :math:`L_\mathrm{veh}` of cars, dual-axle
        and multi-axle heavy vehicles, in decibels, keyed ``"1"``, ``"2a"``
        and ``"2b"``.
    :param road_speed_category: ``"low"``, ``"medium"`` or ``"high"`` (3.3),
        which picks the reference speeds and the weighting factors of Table 1.
    :param weighting_factors: Other proportions of the three categories, keyed
        the same way, for the nationally adapted calculations 9.5 allows (the
        report then has to state them). They must add up to 1. Table 1 when
        omitted.
    :return: The index, in decibels, unrounded.
    :raises ValueError: For a road speed category the standard does not define,
        a level missing, unknown or not finite, or weighting factors that are
        negative or do not add up to 1.
    """
    road = _road_category(road_speed_category)
    levels = _per_category(vehicle_sound_levels_db, "vehicle_sound_levels_db")
    weights = _weights(weighting_factors, road)
    return float(10.0 * math.log10(sum(_index_terms(levels, weights, road).values())))


@dataclass(frozen=True)
class PassByRegression:
    r"""The regression line of one vehicle category and what 9.2 reads off it.

    The line is :math:`L = a + b \lg(v / 1\ \mathrm{km/h})`, fitted by least
    squares to the pass-bys of one category (9.1). Clause 13 item 29 asks for
    the slope and the intercept, the average and the standard deviation of the
    speeds and the standard deviation of the residuals. The spread of the
    speeds is given here as the standard deviation of :math:`\lg v`, in
    decades, and not in km/h: the line is fitted in :math:`\lg v` and 9.3 is
    judged in it, and the standard gives no conversion. Annex E prints a
    spread in km/h "converted from the logarithm of speed" without saying how,
    and its three values do not agree with the slopes, correlations and level
    spreads printed beside them (the errata registry has the arithmetic).

    :param vehicle_category: ``"1"``, ``"2a"`` or ``"2b"``.
    :param road_speed_category: ``"low"``, ``"medium"`` or ``"high"``.
    :param speeds_kmh: The measured speed of each pass-by, in km/h, read-only.
    :param max_levels_db: The maximum A-weighted level of each pass-by, time
        weighting F, in decibels, read-only.
    :param reference_speed_kmh: The Table 1 reference speed of the category,
        in km/h.
    :param intercept_db: :math:`a`, the ordinate of the line at 1 km/h, in
        decibels.
    :param slope_db_per_decade: :math:`b`, in decibels per decade of speed.
    :param correlation: The correlation coefficient of level and
        :math:`\lg v`.
    :param level_standard_deviation_db: The standard deviation of the measured
        levels, in decibels.
    :param residual_standard_deviation_db: The standard deviation of the levels
        about the line, :math:`\sqrt{\sum e_i^2 / (n - 2)}`, in decibels: the
        spread with the speed effect removed that Table 2 describes.
    :param lg_speed_standard_deviation: The standard deviation of
        :math:`\lg(v / 1\ \mathrm{km/h})`, in decades.
    """

    vehicle_category: str
    road_speed_category: str
    speeds_kmh: NDArray[np.float64]
    max_levels_db: NDArray[np.float64]
    reference_speed_kmh: float
    intercept_db: float
    slope_db_per_decade: float
    correlation: float
    level_standard_deviation_db: float
    residual_standard_deviation_db: float
    lg_speed_standard_deviation: float

    @property
    def vehicle_count(self) -> int:
        """How many pass-bys the line was fitted through."""
        return int(self.speeds_kmh.size)

    @property
    def mean_level_db(self) -> float:
        """The mean of the measured levels, in decibels."""
        return float(np.mean(self.max_levels_db))

    @property
    def mean_speed_kmh(self) -> float:
        r"""The mean speed :math:`10^{\overline{\lg v}}`, in km/h.

        The mean of the variable the line is fitted in, converted back, as
        Annex E prints it ("value converted from the logarithm of speed"). The
        line passes through it at :attr:`mean_level_db`.
        """
        return float(10.0 ** np.mean(np.log10(self.speeds_kmh)))

    @property
    def vehicle_sound_level_db(self) -> float:
        r""":math:`L_\mathrm{veh}`, the line at the reference speed, unrounded (9.2)."""
        return float(
            self.intercept_db
            + self.slope_db_per_decade * math.log10(self.reference_speed_kmh)
        )

    @property
    def reported_vehicle_sound_level_db(self) -> float:
        r""":math:`L_\mathrm{veh}` rounded to one decimal, as 9.2 has it reported."""
        return _round_tenth(self.vehicle_sound_level_db)

    @property
    def speed_window_kmh(self) -> tuple[float, float]:
        r"""The speeds the reference speed must lie between, 9.3, in km/h.

        :math:`10^{\overline{\lg v} \pm k s}` with :math:`s` the standard
        deviation of :math:`\lg v` and :math:`k` 1,5 for cars and 1 for heavy
        vehicles (:data:`SPB_SPEED_WINDOW_STANDARD_DEVIATIONS`).
        """
        centre = float(np.mean(np.log10(self.speeds_kmh)))
        half = (
            SPB_SPEED_WINDOW_STANDARD_DEVIATIONS[self.vehicle_category]
            * self.lg_speed_standard_deviation
        )
        return float(10.0 ** (centre - half)), float(10.0 ** (centre + half))

    @property
    def reference_speed_in_window(self) -> bool:
        """Whether the reference speed lies inside :attr:`speed_window_kmh` (9.3)."""
        low, high = self.speed_window_kmh
        return low <= self.reference_speed_kmh <= high

    @property
    def meets_minimum_count(self) -> bool:
        """Whether the category has the vehicles 7.3 asks for classification."""
        return self.vehicle_count >= SPB_MINIMUM_VEHICLE_COUNTS[self.vehicle_category]

    @property
    def confidence_interval_db(self) -> float:
        r"""Half-width of the 95 % confidence interval of the line at the reference speed.

        .. math::

           t_{0,975;\,n-2} \, s_e \sqrt{\frac{1}{n}
           + \frac{(\lg v_\mathrm{ref} - \overline{\lg v})^2}{\sum (\lg v_i
           - \overline{\lg v})^2}}

        the textbook interval of a least-squares line, in decibels. It is the
        measured counterpart of the 0,3 dB and 0,7 dB Table 2 expects, and it
        widens as the reference speed moves away from the mean speed.
        """
        from scipy.stats import t

        n = self.vehicle_count
        logs = np.log10(self.speeds_kmh)
        centre = float(np.mean(logs))
        sxx = float(np.sum((logs - centre) ** 2))
        offset = math.log10(self.reference_speed_kmh) - centre
        quantile = float(t.ppf(0.5 + _CONFIDENCE_LEVEL / 2.0, n - 2))
        return float(
            quantile
            * self.residual_standard_deviation_db
            * math.sqrt(1.0 / n + offset**2 / sxx)
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Draw the pass-bys, the fitted line, the 9.3 window and :math:`L_\mathrm{veh}`.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the fitted line.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_pass_by_regression

        check_language(language)
        return plot_pass_by_regression(self, ax, language=language, **kwargs)


def _fit(
    speeds_kmh: ArrayLike,
    max_levels_db: ArrayLike,
    vehicle_category: str,
    road_speed_category: str,
) -> PassByRegression:
    """The least-squares line of 9.1 and the statistics clause 13 reports."""
    speeds = require_positive_array(speeds_kmh, "speeds_kmh")
    levels = require_finite_array(max_levels_db, "max_levels_db")
    if speeds.ndim != 1 or levels.ndim != 1 or speeds.size != levels.size:
        msg = (
            "'speeds_kmh' and 'max_levels_db' must be one-dimensional and hold "
            "one value per pass-by each."
        )
        raise ValueError(msg)
    if speeds.size < _MIN_PASS_BYS:
        msg = (
            f"a regression line needs at least {_MIN_PASS_BYS} pass-bys; "
            f"category {vehicle_category!r} has {speeds.size}."
        )
        raise ValueError(msg)
    logs = np.log10(speeds)
    x_mean = float(np.mean(logs))
    y_mean = float(np.mean(levels))
    dx = logs - x_mean
    dy = levels - y_mean
    sxx = float(np.sum(dx * dx))
    syy = float(np.sum(dy * dy))
    sxy = float(np.sum(dx * dy))
    if not sxx > 0.0:
        msg = (
            f"the pass-bys of category {vehicle_category!r} all have the same "
            "speed, so no line can be fitted through them."
        )
        raise ValueError(msg)
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    n = speeds.size
    residual_sum = max(syy - slope * sxy, 0.0)
    correlation = sxy / math.sqrt(sxx * syy) if syy > 0.0 else 0.0
    return PassByRegression(
        vehicle_category=vehicle_category,
        road_speed_category=road_speed_category,
        speeds_kmh=read_only(np.array(speeds, dtype=np.float64)),
        max_levels_db=read_only(np.array(levels, dtype=np.float64)),
        reference_speed_kmh=SPB_REFERENCE_SPEEDS_KMH[road_speed_category][
            vehicle_category
        ],
        intercept_db=float(intercept),
        slope_db_per_decade=float(slope),
        correlation=float(correlation),
        level_standard_deviation_db=math.sqrt(syy / (n - 1)),
        residual_standard_deviation_db=math.sqrt(residual_sum / (n - 2)),
        lg_speed_standard_deviation=math.sqrt(sxx / (n - 1)),
    )


def _warn_regression(regression: PassByRegression, stacklevel: int) -> None:
    """Emit the 7.3 and 9.3 warnings a regression earns."""
    category = regression.vehicle_category
    if not regression.meets_minimum_count:
        warnings.warn(
            f"ISO 11819-1 7.3 asks for at least "
            f"{SPB_MINIMUM_VEHICLE_COUNTS[category]} vehicles of category "
            f"{category!r} for surface classification; "
            f"{regression.vehicle_count} were measured.",
            StatisticalPassByWarning,
            stacklevel=stacklevel,
        )
    if not regression.reference_speed_in_window:
        low, high = regression.speed_window_kmh
        k = SPB_SPEED_WINDOW_STANDARD_DEVIATIONS[category]
        warnings.warn(
            f"ISO 11819-1 9.3: the reference speed "
            f"{regression.reference_speed_kmh:g} km/h of category {category!r} "
            f"lies outside {k:g} standard deviation(s) of the measured mean speed, "
            f"{low:.1f} km/h to {high:.1f} km/h, so the regression should not be "
            "used to normalize to it.",
            StatisticalPassByWarning,
            stacklevel=stacklevel,
        )


def pass_by_regression(
    speeds_kmh: ArrayLike,
    max_levels_db: ArrayLike,
    *,
    vehicle_category: str,
    road_speed_category: str,
) -> PassByRegression:
    r"""Fit the level of one vehicle category against the logarithm of speed, 9.1 and 9.2.

    The maximum A-weighted levels are regressed on
    :math:`\lg(v / 1\ \mathrm{km/h})` by least squares, and the ordinate of the
    line at the Table 1 reference speed is the vehicle sound level
    :math:`L_\mathrm{veh}` of the category
    (:attr:`PassByRegression.vehicle_sound_level_db`).

    Two conditions are judged on the way and emitted as
    :class:`StatisticalPassByWarning` when they fail: the 7.3 minimum number of
    vehicles of the category for surface classification, and the 9.3 window the
    reference speed has to lie in for the line to be used at it. Both verdicts
    stay on the result.

    :param speeds_kmh: The speed of each pass-by, in km/h, measured as the
        vehicle midpoint passes the microphone (8.4).
    :param max_levels_db: The maximum A-weighted sound pressure level of each
        pass-by, time weighting F, in decibels, in the same order.
    :param vehicle_category: ``"1"`` (cars), ``"2a"`` (dual-axle heavy
        vehicles) or ``"2b"`` (multi-axle heavy vehicles).
    :param road_speed_category: ``"low"``, ``"medium"`` or ``"high"`` (3.3),
        which picks the reference speed.
    :return: The line and its statistics, as a :class:`PassByRegression`.
    :raises ValueError: For an unknown category, a speed that is not positive,
        a level that is not finite, inputs that do not match pass-by for
        pass-by, fewer than three pass-bys, or pass-bys all at one speed.
    """
    road = _road_category(road_speed_category)
    category = _vehicle_category(vehicle_category)
    regression = _fit(speeds_kmh, max_levels_db, category, road)
    _warn_regression(regression, stacklevel=3)
    return regression


@dataclass(frozen=True)
class StatisticalPassByResult:
    r"""The vehicle sound levels and the index of one road surface (ISO 11819-1).

    :param road_speed_category: ``"low"``, ``"medium"`` or ``"high"``.
    :param regressions: The :class:`PassByRegression` of each vehicle category,
        keyed ``"1"``, ``"2a"`` and ``"2b"``.
    :param weighting_factors: The :math:`W_x` the index was computed with.
    :param vehicle_sound_levels_db: :math:`L_\mathrm{veh}` of each category,
        uncorrected for temperature and unrounded, in decibels.
    :param index_db: The SPBI of those levels as 9.2 reports them, rounded to
        one decimal (:attr:`reported_vehicle_sound_levels_db`), in decibels.
        The index itself is not rounded; :attr:`reported_index_db` is.
    :param corrected_vehicle_sound_levels_db: The temperature-corrected levels
        the caller supplied (9.4), as supplied, or ``None``.
    :param corrected_index_db: The SPBI of the corrected levels rounded to one
        decimal, or ``None``.
    :param reference_index_db: The SPBI of the reference surface (clause 10):
        the index supplied, or that of the levels supplied rounded to one
        decimal; ``None`` when no reference was given.
    """

    road_speed_category: str
    regressions: Mapping[str, PassByRegression]
    weighting_factors: Mapping[str, float]
    vehicle_sound_levels_db: Mapping[str, float]
    index_db: float
    corrected_vehicle_sound_levels_db: Mapping[str, float] | None = None
    corrected_index_db: float | None = None
    reference_index_db: float | None = None

    @property
    def reference_speeds_kmh(self) -> Mapping[str, float]:
        """The Table 1 reference speeds the levels are normalized to, in km/h."""
        return SPB_REFERENCE_SPEEDS_KMH[self.road_speed_category]

    @property
    def heavy_vehicle_count(self) -> int:
        """Dual-axle and multi-axle heavy vehicles together, as 7.3 counts them."""
        return sum(self.regressions[key].vehicle_count for key in _HEAVY_CATEGORIES)

    @property
    def meets_minimum_counts(self) -> bool:
        """Whether every count of 7.3 is met, the heavy vehicles together included."""
        return (
            all(reg.meets_minimum_count for reg in self.regressions.values())
            and self.heavy_vehicle_count >= SPB_MINIMUM_VEHICLE_COUNTS["2"]
        )

    @property
    def reference_speeds_in_window(self) -> bool:
        """Whether every reference speed lies inside its 9.3 window."""
        return all(reg.reference_speed_in_window for reg in self.regressions.values())

    @property
    def reported_vehicle_sound_levels_db(self) -> Mapping[str, float]:
        r""":math:`L_\mathrm{veh}` of each category rounded to one decimal (9.2).

        The levels the index is computed from, and the ones a report prints.
        """
        return MappingProxyType(_reported_levels(self.vehicle_sound_levels_db))

    @property
    def reported_corrected_vehicle_sound_levels_db(self) -> Mapping[str, float] | None:
        """The temperature-corrected levels rounded to one decimal, or ``None``."""
        if self.corrected_vehicle_sound_levels_db is None:
            return None
        return MappingProxyType(
            _reported_levels(self.corrected_vehicle_sound_levels_db)
        )

    @property
    def reported_index_db(self) -> float:
        """The SPBI rounded to one decimal (9.2)."""
        return _round_tenth(self.index_db)

    @property
    def full_precision_index_db(self) -> float:
        r"""The SPBI of the unrounded :math:`L_\mathrm{veh}`, in decibels.

        Not the index the standard reports, which adds the levels of 9.2 as
        they are reported, to one decimal (:attr:`index_db`). The two never
        differ by more than 0,05 dB, the most a level moves when it is rounded,
        but that can be enough to move the reported digit: for the lines Annex
        E prints, this is 79,985 dB, which would print 80,0 dB, where the annex
        prints 79,9 dB.
        """
        return statistical_pass_by_index(
            self.vehicle_sound_levels_db,
            road_speed_category=self.road_speed_category,
            weighting_factors=self.weighting_factors,
        )

    @property
    def reported_corrected_index_db(self) -> float | None:
        """The temperature-corrected SPBI rounded to one decimal, or ``None``."""
        if self.corrected_index_db is None:
            return None
        return _round_tenth(self.corrected_index_db)

    @property
    def difference_db(self) -> float | None:
        """The SPBI less that of the reference surface, in decibels, or ``None``.

        Positive for a surface louder than the reference. Unrounded; 9.5 says
        that in many cases the main use of the index is this difference.
        """
        if self.reference_index_db is None:
            return None
        return self.index_db - self.reference_index_db

    @property
    def corrected_difference_db(self) -> float | None:
        """The temperature-corrected SPBI less the reference one, or ``None``."""
        if self.reference_index_db is None or self.corrected_index_db is None:
            return None
        return self.corrected_index_db - self.reference_index_db

    @property
    def index_confidence_interval_db(self) -> float:
        r"""Half-width of the 95 % interval the three line intervals leave on the index.

        .. math::

           \sqrt{\sum_x \left( c_x \, \Delta_x \right)^2}, \qquad
           c_x = \frac{\partial \mathrm{SPBI}}{\partial L_x}
               = \frac{W'_x \, 10^{L_x/10}}{\sum_y W'_y \, 10^{L_y/10}}

        with :math:`W'_x` the weighting factor times the speed ratio of 9.5,
        :math:`L_x` the reported levels the index adds and :math:`\Delta_x`
        each category's :attr:`PassByRegression.confidence_interval_db`. The
        three categories are measured on different vehicles and are taken as
        independent.
        """
        terms = _index_terms(
            self.reported_vehicle_sound_levels_db,
            self.weighting_factors,
            self.road_speed_category,
        )
        total = sum(terms.values())
        return float(
            math.sqrt(
                sum(
                    (terms[key] / total * self.regressions[key].confidence_interval_db)
                    ** 2
                    for key in SPB_VEHICLE_CATEGORIES
                )
            )
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Draw the three clouds of pass-bys, their lines and :math:`L_\mathrm{veh}`.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the three fitted lines.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_statistical_pass_by

        check_language(language)
        return plot_statistical_pass_by(self, ax, language=language, **kwargs)


def statistical_pass_by(
    vehicle_categories: ArrayLike,
    speeds_kmh: ArrayLike,
    max_levels_db: ArrayLike,
    *,
    road_speed_category: str,
    corrected_vehicle_sound_levels_db: Mapping[str, float] | None = None,
    reference_db: float | Mapping[str, float] | None = None,
    weighting_factors: Mapping[str, float] | None = None,
) -> StatisticalPassByResult:
    r"""The Statistical Pass-By method of ISO 11819-1 from a list of pass-bys.

    One row per vehicle that passed on its own: its category, its speed and its
    maximum A-weighted level. The rows are split by category, a line is fitted
    through each (:func:`pass_by_regression`), and each line is read at its
    Table 1 reference speed. The three vehicle sound levels are rounded to one
    decimal, as 9.2 has them reported, and combined into the index
    (:func:`statistical_pass_by_index`), so that the index is the one anyone
    recomputes from the reported levels (9.5). The unrounded levels and their
    index stay on the result (:attr:`StatisticalPassByResult.full_precision_index_db`).

    The 7.3 counts (the two heavy categories together included) and the 9.3
    speed windows are judged, kept on the result and emitted as
    :class:`StatisticalPassByWarning` when they fail.

    :param vehicle_categories: The category of each pass-by, ``"1"``, ``"2a"``
        or ``"2b"``.
    :param speeds_kmh: The speed of each pass-by, in km/h.
    :param max_levels_db: The maximum A-weighted level of each pass-by, time
        weighting F, in decibels.
    :param road_speed_category: ``"low"``, ``"medium"`` or ``"high"`` (3.3).
    :param corrected_vehicle_sound_levels_db: Vehicle sound levels corrected to
        :data:`SPB_REFERENCE_AIR_TEMPERATURE_C` by a method of the caller's
        choosing, keyed by category, for which the index is also computed,
        from the levels rounded to one decimal. 9.4 gives no method. To correct
        each pass-by instead, which 9.4 prefers, correct ``max_levels_db`` and
        call this again.
    :param reference_db: The reference surface of clause 10: either its SPBI in
        decibels, used as given, or its three vehicle sound levels keyed by
        category (for instance :data:`SPB_NORMALIZED_REFERENCE_DB`), whose
        index is then computed from the levels rounded to one decimal, with
        the same weighting factors.
    :param weighting_factors: Other proportions of the three categories (9.5);
        Table 1 when omitted.
    :return: The regressions, the levels and the index, as a
        :class:`StatisticalPassByResult`.
    :raises ValueError: For a category the method does not use, rows that do
        not match, a category with fewer than three pass-bys or all at one
        speed, or invalid weighting factors or levels.
    """
    road = _road_category(road_speed_category)
    labels = np.asarray(vehicle_categories, dtype=object).ravel()
    speeds = np.asarray(speeds_kmh, dtype=np.float64)
    levels = np.asarray(max_levels_db, dtype=np.float64)
    if (
        speeds.ndim != 1
        or levels.ndim != 1
        or not (labels.size == speeds.size == levels.size)
    ):
        msg = (
            "'vehicle_categories', 'speeds_kmh' and 'max_levels_db' must be "
            "one-dimensional and hold one value per pass-by each."
        )
        raise ValueError(msg)
    keys = np.array([_vehicle_category(label) for label in labels], dtype=object)
    weights = _weights(weighting_factors, road)
    regressions: dict[str, PassByRegression] = {}
    for category in SPB_VEHICLE_CATEGORIES:
        rows = keys == category
        regressions[category] = _fit(speeds[rows], levels[rows], category, road)
        _warn_regression(regressions[category], stacklevel=3)
    heavy = sum(regressions[key].vehicle_count for key in _HEAVY_CATEGORIES)
    if heavy < SPB_MINIMUM_VEHICLE_COUNTS["2"]:
        warnings.warn(
            f"ISO 11819-1 7.3 asks for at least {SPB_MINIMUM_VEHICLE_COUNTS['2']} "
            f"heavy vehicles (2a and 2b together) for surface classification; "
            f"{heavy} were measured.",
            StatisticalPassByWarning,
            stacklevel=2,
        )
    vehicle_levels = {
        key: regressions[key].vehicle_sound_level_db for key in SPB_VEHICLE_CATEGORIES
    }
    index = statistical_pass_by_index(
        _reported_levels(vehicle_levels),
        road_speed_category=road,
        weighting_factors=weights,
    )
    corrected_levels: Mapping[str, float] | None = None
    corrected_index: float | None = None
    if corrected_vehicle_sound_levels_db is not None:
        corrected_levels = MappingProxyType(
            _per_category(
                corrected_vehicle_sound_levels_db, "corrected_vehicle_sound_levels_db"
            )
        )
        corrected_index = statistical_pass_by_index(
            _reported_levels(corrected_levels),
            road_speed_category=road,
            weighting_factors=weights,
        )
    reference_index: float | None = None
    if reference_db is not None:
        if isinstance(reference_db, Mapping):
            reference_levels = _per_category(reference_db, "reference_db")
            reference_index = statistical_pass_by_index(
                _reported_levels(reference_levels),
                road_speed_category=road,
                weighting_factors=weights,
            )
        else:
            reference_index = require_finite(float(reference_db), "reference_db")
    return StatisticalPassByResult(
        road_speed_category=road,
        regressions=MappingProxyType(regressions),
        weighting_factors=MappingProxyType(weights),
        vehicle_sound_levels_db=MappingProxyType(vehicle_levels),
        index_db=index,
        corrected_vehicle_sound_levels_db=corrected_levels,
        corrected_index_db=corrected_index,
        reference_index_db=reference_index,
    )


def normalized_reference_levels(
    surface_levels_db: Mapping[str, Mapping[str, float]],
) -> Mapping[str, float]:
    r"""The vehicle sound levels of a normalized reference surface, 10.2 and Annex D.

    The normalized reference case is a fictitious surface whose
    :math:`L_\mathrm{veh}` are set by convention, "for instance ... the
    average results of a great number of SPB measurements" on dense asphalt
    surfaces. Annex D builds one from seven surfaces
    (:data:`SPB_ANNEX_D_SURFACES_DB`) and prints the average of each column,
    which is what this returns: the arithmetic mean, category by category.

    The energetic mean would print the same row there (76,4, 81,0 and 84,0 dB
    either way), so the page does not decide between the two; the arithmetic
    mean is the plain reading of "average" for levels that are already
    averages.

    :param surface_levels_db: The vehicle sound levels of each surface, in
        decibels, as a mapping from a surface label to a mapping keyed ``"1"``,
        ``"2a"`` and ``"2b"``.
    :return: The mean level of each category, in decibels, unrounded.
    :raises ValueError: For no surfaces, or a surface without exactly the three
        categories.
    """
    if not surface_levels_db:
        msg = "'surface_levels_db' must hold at least one surface."
        raise ValueError(msg)
    rows = [
        _per_category(levels, f"surface_levels_db[{label!r}]")
        for label, levels in surface_levels_db.items()
    ]
    return MappingProxyType(
        {
            key: float(np.mean([row[key] for row in rows]))
            for key in SPB_VEHICLE_CATEGORIES
        }
    )
