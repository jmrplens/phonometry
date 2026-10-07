#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The noise a railway vehicle emits, measured by ISO 3095:2013.

ISO 3095 is the type test of rolling stock: how a train, a locomotive or a
wagon is measured so that two units measured on two tracks can be compared.
It has four tests and one condition that makes the constant-speed test
comparable at all, the track.

**Clause 5, standing still.** Microphones 7,5 m from the track centreline and
1,2 m high stand opposite the middle of equal areas 3 m to 5 m long along both
sides of every car, plus two at 30° on a 7,5 m half circle off each end of
the unit, only off the ends with a cab for a trailer unit (5.5.1.1). The
level :math:`L^i_{p\mathrm{Aeq},T}` of every position, over at least 20 s, is
energy averaged weighted by the length :math:`l_i` each position stands for,
:math:`(\pi/2) \times 7{,}5` m for the end positions
(:data:`STATIONARY_END_POSITION_LENGTH_M`):

.. math::

   \langle L_{p\mathrm{Aeq},T} \rangle_\mathrm{unit} = 10 \lg \left(
   \sum_{i=1}^{n} \frac{l_i}{l_\mathrm{tot}} 10^{L^i_{p\mathrm{Aeq},T}/10}
   \right), \qquad l_\mathrm{tot} = \sum_{i=1}^{n} l_i

(Formulae 1 and 2, :func:`stationary_unit_level`; Formula 3 is the same over
one car). The result is the mean of three such sets rounded to the nearest
integer decibel (5.8.1, :func:`stationary_test`).

**Clause 6, at constant speed.** The pass-by level
:math:`L_{p\mathrm{Aeq},T_p}` is the A-weighted equivalent level over the
pass-by time :math:`T_p` of the unit, from its front to its rear for a fixed
formation (6.6.3, :func:`pass_by_measurement`), at 7,5 m and 1,2 m, or 25 m
and 3,5 m at 200 km/h and above. Three runs per speed and side give a mean
rounded to the integer; the louder side is the result (6.7.1,
:func:`rolling_stock_test`). The test speeds are 80 km/h and the maximum
speed, or the maximum alone up to 80 km/h (6.6.2, :func:`type_test_speeds`).
The 2005 edition also defined the **transit exposure level**, the energy of
a whole train's passage normalised to its pass-by time,

.. math::

   \mathrm{TEL} = 10 \lg \left( \frac{1}{T_p} \int_0^T
   \frac{p_\mathrm{A}^2(t)}{p_0^2}\,\mathrm{d}t \right)
   = L_{p\mathrm{Aeq},T} + 10 \lg \frac{T}{T_p}

(ISO 3095:2005, 3.14, Formulae 8 and 10, :func:`transit_exposure_level`). The
2013 edition dropped it; its Annex B.4 keeps the same form, with the pass-by
time of half the unit, for a single trailer at the end of a train
(Formula B.1).

**Clauses 7 and 8, starting and braking.** Starting is measured two ways:
the maximum :math:`L_{p\mathrm{AFmax}}` at 7,5 m at a cross section 10 m ahead
of the unit and at further positions along a long unit
(:func:`acceleration_test_positions`), or :math:`L_{p\mathrm{Aeq},T}` at
25 m over the passage of the unit. Braking from 30 km/h is measured by
:math:`L_{p\mathrm{AFmax}}` opposite the first car at standstill. Each takes
three runs per position, averages them, rounds to the integer and keeps the
highest (7.5.4, 7.6.4, 8.7). Three runs are valid when they are no more than
3 dB apart (9.3).

**6.2, the reference track.** A constant-speed result is comparable only on
a track whose rail roughness is below the limit of Figure 2 and whose decay
rates are above the limits of Figure 3, both printed as numbers on the page
(:data:`REFERENCE_TRACK_ROUGHNESS_LIMIT_DB`,
:data:`REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M`). The roughness is measured by
EN 15610 (:mod:`~phonometry.environment.sources.acoustic_roughness`) and the
decay rates by EN 15461 (:mod:`~phonometry.environment.sources.track_decay`);
:func:`check_reference_track` brings the two together with the curve radius
and gradient of 6.2.2. A track whose roughness exceeds the limit in a few
bands can still be accepted by Annex C when the exceedance changes the
pass-by level by no more than 1 dB (:func:`check_small_roughness_deviations`),
and Annex E bounds how much two tracks' roughness could change a pass-by level
(:func:`roughness_comparability`).

**The rest.** Annex A characterises impulsive noise by the fastest rise of
:math:`L_{p\mathrm{AF}}(t)` (:func:`impulsiveness_rise_speed`); 6.3.4 accepts
a vehicle next to the unit under test when it adds no more than 2 dB
(:func:`check_adjacent_vehicle_neutrality`); Annex D.4.2 corrects for a
steady background (:func:`background_level_increase`); and Annex G sums an
uncertainty budget whose example, Table G.2, is the numerical oracle of this
module (:func:`pass_by_uncertainty`).

**Roundings.** 5.8.1, 6.7.1, 7.5.4, 7.6.4 and 8.7 round to the nearest integer
decibel and 6.3.4 to one decimal, without a rule for a value on the half; a
half goes up here, a convention of this module, and so does a mean that binary
arithmetic lands a hair under it (runs of 70,1 dB, 70,3 dB and 71,1 dB average
to 70,5 dB and give 71 dB).

Read from ISO 3095:2013 (third edition) and, for the transit exposure level,
BS EN ISO 3095:2005 (second edition).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.frozen import OwnsArrays, read_only
from ..._internal.validation import (
    require_1d_signal,
    require_choice,
    require_finite,
    require_finite_array,
    require_non_negative,
    require_positive,
    require_positive_array,
)
from ...io._resolve import SignalInput, resolve_fs, resolve_samples
from ...metrology.reference_values import ISO1683_REFERENCE_VALUES
from ._shared import _TOLERANCE
from .acoustic_roughness import (
    _MINIMUM_FILTERED_TOTAL_M,
    AcousticRoughnessSpectrum,
    _band_edges,
    _band_of_wavelength,
    _nominal_wavelength_m,
    average_roughness_spectra,
    redistributed_band_energies,
)
from .track_decay import TRACK_DECAY_DIRECTIONS, TrackDecayRate

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Callable, Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

    from ...metrology.uncertainty import Quantity

__all__ = [
    "PREFERRED_PASS_BY_SPEEDS_KMH",
    "REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M",
    "REFERENCE_TRACK_ROUGHNESS_LIMIT_DB",
    "ROLLING_STOCK_TEST_METHODS",
    "STATIONARY_END_POSITION_LENGTH_M",
    "AdjacentVehicleNeutrality",
    "PassByMeasurement",
    "PassByUncertainty",
    "ReferenceTrackCheck",
    "RiseSpeedResult",
    "RollingStockTestResult",
    "RoughnessComparability",
    "SmallRoughnessDeviation",
    "StationaryTestResult",
    "TrackCondition",
    "acceleration_test_positions",
    "background_level_increase",
    "check_adjacent_vehicle_neutrality",
    "check_reference_track",
    "check_small_roughness_deviations",
    "impulsiveness_rise_speed",
    "minimum_curve_radius",
    "pass_by_measurement",
    "pass_by_time",
    "pass_by_uncertainty",
    "rolling_stock_test",
    "roughness_comparability",
    "stationary_test",
    "stationary_unit_level",
    "transit_exposure_level",
    "type_test_speeds",
]

#: 6.2.5 and Figure 2: the default upper limit of the one-third octave band
#: acoustic rail roughness level, dB re 1 µm, keyed by nominal wavelength in
#: metres, from 0,4 m to 3,15 mm. Figure 2 prints each level beside its point;
#: its axis labels the 3,15 cm, 1,25 cm, 0,63 cm and 0,315 cm bands as 3.2,
#: 1.3, 0.6 and 0.3. The same 22 values are the "2007 TSI limit" of the EN
#: 15610:2009 Annex B.9.2 listing.
REFERENCE_TRACK_ROUGHNESS_LIMIT_DB: Mapping[float, float] = MappingProxyType(
    {
        0.4: 17.1,
        0.315: 15.0,
        0.25: 13.0,
        0.2: 11.0,
        0.16: 9.0,
        0.125: 7.0,
        0.1: 4.9,
        0.08: 2.9,
        0.063: 0.9,
        0.05: -1.1,
        0.04: -3.2,
        0.0315: -5.0,
        0.025: -5.6,
        0.02: -6.2,
        0.016: -6.8,
        0.0125: -7.4,
        0.01: -8.0,
        0.008: -8.6,
        0.0063: -9.2,
        0.005: -9.8,
        0.004: -10.4,
        0.00315: -11.0,
    }
)

#: 6.2.6 and Figure 3: the default lower limits of the track decay rate, in
#: dB/m, keyed by direction and then by nominal one-third octave band
#: frequency in hertz, from 250 Hz to 5 000 Hz. Figure 3 prints them in a
#: table beside the curves; below 250 Hz it sets no limit.
REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M: Mapping[str, Mapping[float, float]] = (
    MappingProxyType(
        {
            "vertical": MappingProxyType(
                {
                    250.0: 2.00,
                    315.0: 2.00,
                    400.0: 6.00,
                    500.0: 6.00,
                    630.0: 6.00,
                    800.0: 2.19,
                    1000.0: 0.80,
                    1250.0: 0.80,
                    1600.0: 0.80,
                    2000.0: 0.80,
                    2500.0: 0.80,
                    3150.0: 0.80,
                    4000.0: 0.80,
                    5000.0: 0.80,
                }
            ),
            "lateral": MappingProxyType(
                {
                    250.0: 2.04,
                    315.0: 1.38,
                    400.0: 0.94,
                    500.0: 0.64,
                    630.0: 0.43,
                    800.0: 0.29,
                    1000.0: 0.20,
                    1250.0: 0.20,
                    1600.0: 0.32,
                    2000.0: 0.50,
                    2500.0: 0.50,
                    3150.0: 0.50,
                    4000.0: 0.50,
                    5000.0: 0.50,
                }
            ),
        }
    )
)

#: 6.6.2: the preferred speeds of additional and monitoring tests, in km/h, as
#: printed (there is no 180 km/h).
PREFERRED_PASS_BY_SPEEDS_KMH: tuple[float, ...] = (
    20.0,
    40.0,
    60.0,
    80.0,
    100.0,
    120.0,
    140.0,
    160.0,
    200.0,
    250.0,
    300.0,
    320.0,
    350.0,
)

#: 5.8.1: the length :math:`(\pi/2) \times 7{,}5` m an end position of the
#: stationary mesh stands for in Formula 1, in metres.
STATIONARY_END_POSITION_LENGTH_M: float = math.pi / 2.0 * 7.5

#: The tests whose result is the highest of the rounded means of three runs
#: per position: constant speed (6.7.1), starting by the maximum level method
#: (7.5.4) and by the averaged level method (7.6.4), and braking (8.7).
ROLLING_STOCK_TEST_METHODS: tuple[str, ...] = (
    "constant_speed",
    "acceleration_maximum",
    "acceleration_averaged",
    "braking",
)

#: 3.11: the reference sound pressure in air, from the published ISO 1683 table.
_P0_PA = ISO1683_REFERENCE_VALUES["gas"]["sound_pressure"].value

#: 5.7, 6.6.1, 7.5.3, 7.6.3 and 8.6: the fewest valid runs per position.
_MINIMUM_RUNS = 3

#: 9.3: the largest spread of the runs of one position, in decibels.
_MAXIMUM_SPREAD_DB = 3.0

#: 6.3.4: the most an adjacent vehicle may add to the pass-by level, in
#: decibels, judged on levels rounded to one decimal.
_NEUTRALITY_ALLOWANCE_DB = 2.0

#: Annex C.3: the largest change of the pass-by level a roughness exceedance
#: may make, in decibels.
_SMALL_DEVIATION_DB = 1.0

#: Annex A: the rise a slope of :math:`L_{p\mathrm{AF}}(t)` has to make, in
#: decibels, to count.
_IMPULSIVE_RISE_DB = 10.0

#: D.4.2: the smallest excess over the background the correction is used for.
_BACKGROUND_EXCESS_DB = 3.0

#: 6.6.3: the drop the record must show at either end, in decibels.
_RECORD_MARGIN_DB = 10.0

#: 7.5.1.1: the front measurement cross section lies this far ahead of the
#: unit, and a centre position this far ahead of its middle, in metres.
_AHEAD_M = 10.0

#: 7.5.1.1: the longest unit measured at one position, and the longest spacing
#: of the positions along a longer one, in metres.
_MAXIMUM_SPACING_M = 50.0

#: 6.6.2: the speed that splits the two cases of type-test speeds, in km/h.
_TYPE_TEST_SPEED_KMH = 80.0

#: 6.2.2: the minimum curve radius, in metres, by the highest speed it
#: covers, in km/h; above the last, 5 000 m.
_CURVE_RADII_M: tuple[tuple[float, float], ...] = ((70.0, 1000.0), (120.0, 3000.0))
_HIGH_SPEED_CURVE_RADIUS_M = 5000.0

#: 6.2.2: the steepest gradient where powered units are tested, 5:1 000.
_MAXIMUM_GRADIENT_RATIO = 5.0 / 1000.0

#: 6.2.5: the speed up to which the roughness is needed from 0,003 m to
#: 0,10 m; above it, to 0,25 m.
_WAVELENGTH_RANGE_SPEED_KMH = 190.0
_SHORTEST_WAVELENGTH_M = 0.003
_LONGEST_WAVELENGTH_M = (0.10, 0.25)

#: The detail of a requirement nothing was given to judge.
_NO_SPECTRUM = "no spectrum given"

#: Annex G.5: the coverage factor for about 95 %.
_COVERAGE_FACTOR = 2.0

#: Formula E.4: the differences of each situation from the minimum and the
#: maximum envelope, two situations.
_FORMULA_E4_TERMS = 4

#: The default interval of the stored level history, in seconds.
_HISTORY_INTERVAL_S = 0.01

#: IEC 61672-1: the time constant of time weighting F, in seconds.
_F_TIME_CONSTANT_S = 0.125


def _round_half_up(value: float, decimals: int = 0) -> float:
    """Round a level the way this module reports it: a half goes up.

    The standard rounds to the nearest integer (or one decimal) and gives no
    rule for a value on the half; going up is a convention of this module. A
    value within :data:`_TOLERANCE` under the half is on it: the mean of 70,1,
    70,3 and 71,1 dB is 70,5 dB, which binary arithmetic lands a hair under.
    """
    scale = 10.0**decimals
    return math.floor((value + _TOLERANCE) * scale + 0.5) / scale


def _energy_sum_db(levels_db: NDArray[np.float64]) -> float:
    """The energy sum of band levels, in decibels."""
    return float(10.0 * np.log10(np.sum(10.0 ** (levels_db / 10.0))))


# ---------------------------------------------------------------------------
# Speeds, times and positions
# ---------------------------------------------------------------------------


def type_test_speeds(max_speed_kmh: float) -> tuple[float, ...]:
    r"""The speeds a unit is type tested at, 6.6.2.

    Above 80 km/h, at 80 km/h and at the maximum speed; at or below it, at
    the maximum speed alone. Further tests are run at the preferred speeds of
    :data:`PREFERRED_PASS_BY_SPEEDS_KMH`.

    :param max_speed_kmh: The maximum speed :math:`v_\mathrm{max}` of the
        unit, in km/h.
    :return: The type-test speeds, in km/h, slowest first.
    :raises ValueError: For a speed that is not positive.
    """
    vmax = require_positive(max_speed_kmh, "max_speed_kmh")
    speeds = [vmax]
    if vmax > _TYPE_TEST_SPEED_KMH:
        speeds.insert(0, _TYPE_TEST_SPEED_KMH)
    return tuple(speeds)


def minimum_curve_radius(speed_kmh: float) -> float:
    """The smallest radius of curvature the test track may have, 6.2.2.

    1 000 m for tests up to 70 km/h, 3 000 m above 70 km/h and up to
    120 km/h, 5 000 m above 120 km/h.

    :param speed_kmh: The test speed, in km/h.
    :return: The minimum radius, in metres.
    :raises ValueError: For a speed that is not positive.
    """
    speed = require_positive(speed_kmh, "speed_kmh")
    for limit_kmh, radius_m in _CURVE_RADII_M:
        if speed <= limit_kmh:
            return radius_m
    return _HIGH_SPEED_CURVE_RADIUS_M


def pass_by_time(unit_length_m: float, *, speed_kmh: float) -> float:
    r"""The time :math:`T_p = l/v` a unit takes to pass a point, in seconds.

    ISO 3095:2005 3.14 defines it for a whole train as its overall length
    divided by its speed. For the single trailer unit of Annex B.4 the
    pass-by time of Formula B.1 is that of half the unit, so pass half its
    length.

    :param unit_length_m: The length of the unit or train, over buffers, in
        metres.
    :param speed_kmh: Its speed, in km/h.
    :return: :math:`T_p`, in seconds.
    :raises ValueError: For a length or speed that is not positive.
    """
    length = require_positive(unit_length_m, "unit_length_m")
    speed = require_positive(speed_kmh, "speed_kmh")
    return length / (speed / 3.6)


def transit_exposure_level(
    equivalent_level_db: float, *, measurement_time_s: float, pass_by_time_s: float
) -> float:
    r"""The transit exposure level of a train, ISO 3095:2005 3.14.

    .. math::

       \mathrm{TEL} = L_{p\mathrm{Aeq},T} + 10 \lg \frac{T}{T_p}

    (Formula 10): the energy of the whole passage, measured over a time
    :math:`T` that runs from 10 dB below the level at the front to 10 dB below
    the level at the rear, spread over the pass-by time :math:`T_p` alone. It
    is Formula 9's :math:`\mathrm{SEL} + 10 \lg (T_0/T_p)` written with the
    equivalent level.

    :param equivalent_level_db: :math:`L_{p\mathrm{Aeq},T}` over the
        measurement time, in dB.
    :param measurement_time_s: :math:`T`, in seconds.
    :param pass_by_time_s: :math:`T_p`, in seconds (:func:`pass_by_time`).
    :return: TEL, in dB.
    :raises ValueError: For a level that is not finite or times that are not
        positive.
    """
    level = require_finite(equivalent_level_db, "equivalent_level_db")
    duration = require_positive(measurement_time_s, "measurement_time_s")
    passing = require_positive(pass_by_time_s, "pass_by_time_s")
    return level + 10.0 * math.log10(duration / passing)


def acceleration_test_positions(unit_length_m: float) -> NDArray[np.float64]:
    """Where the microphones of the maximum level starting test stand, 7.5.1.1.

    One at the front cross section, 10 m ahead of the front of the unit. A
    unit longer than 50 m also has one 10 m ahead of its middle, and when
    those two are more than 50 m apart the gap is split into equal spacings of
    no more than 50 m (Figure 10: a 108 m unit has positions 10 m ahead of it
    and 17 m and 44 m behind its front).

    :param unit_length_m: The length :math:`l` of the unit, in metres.
    :return: The positions, in metres behind the front of the unit at
        standstill, the front cross section first at -10 m; read-only.
    :raises ValueError: For a length that is not positive.
    """
    length = require_positive(unit_length_m, "unit_length_m")
    if length <= _MAXIMUM_SPACING_M * (1.0 + _TOLERANCE):
        return read_only(np.array([-_AHEAD_M]))
    gap = length / 2.0
    spacings = math.ceil(gap / _MAXIMUM_SPACING_M - _TOLERANCE)
    return read_only(-_AHEAD_M + np.arange(spacings + 1) * gap / spacings)


# ---------------------------------------------------------------------------
# The pass-by record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PassByMeasurement(OwnsArrays):
    r"""The levels of one pass-by record, 6.5 and 6.6.3.

    :param times_s: The times of the stored level history, in seconds from the
        start of the record.
    :param levels_db: :math:`L_{p\mathrm{AF}}(t)`, the A-weighted level with
        time weighting F, at ``times_s``, in dB.
    :param start_s: :math:`T_1`, the start of the measurement time interval.
    :param end_s: :math:`T_2`, its end, in seconds.
    :param equivalent_level_db: :math:`L_{p\mathrm{Aeq},T}` over
        :math:`T_1` to :math:`T_2`, in dB; the pass-by level
        :math:`L_{p\mathrm{Aeq},T_p}` when the interval is the pass-by time.
    :param max_level_db: :math:`L_{p\mathrm{AFmax}}` within the interval, in dB.
    :param front_level_db: :math:`L_{p\mathrm{AF}}` when the front of the
        train is opposite the microphone, in dB.
    :param rear_level_db: :math:`L_{p\mathrm{AF}}` when its rear is, in dB.
    :param record_start_level_db: :math:`L_{p\mathrm{AF}}` at the start of the
        record, in dB.
    :param record_end_level_db: :math:`L_{p\mathrm{AF}}` at its end, in dB.
    :param pass_by_time_s: :math:`T_p`, in seconds, when given.
    """

    times_s: NDArray[np.float64]
    levels_db: NDArray[np.float64]
    start_s: float
    end_s: float
    equivalent_level_db: float
    max_level_db: float
    front_level_db: float
    rear_level_db: float
    record_start_level_db: float
    record_end_level_db: float
    pass_by_time_s: float | None = None

    def __post_init__(self) -> None:
        """Hold the history read-only."""
        object.__setattr__(
            self, "times_s", read_only(np.asarray(self.times_s, dtype=np.float64))
        )
        object.__setattr__(
            self, "levels_db", read_only(np.asarray(self.levels_db, dtype=np.float64))
        )

    @property
    def measurement_time_s(self) -> float:
        """:math:`T = T_2 - T_1`, in seconds."""
        return self.end_s - self.start_s

    @property
    def exposure_level_db(self) -> float:
        r"""The single event level :math:`L_{p\mathrm{Aeq},T} + 10 \lg (T/T_0)`, :math:`T_0 = 1` s (2005, Formula 7)."""
        return self.equivalent_level_db + 10.0 * math.log10(self.measurement_time_s)

    @property
    def normalized_level_db(self) -> float | None:
        r"""The energy of the interval spread over :math:`T_p`, in dB; ``None`` without it.

        :math:`10 \lg \bigl( \frac{1}{T_p} \int_T p_\mathrm{A}^2 / p_0^2 \, \mathrm{d}t
        \bigr)`: the transit exposure level of ISO 3095:2005 3.14 for a whole
        train, and the :math:`L_{p\mathrm{Aeq},T_p}` of Formula B.1 for a single
        trailer unit, whose :math:`T_p` is that of half the unit.
        """
        if self.pass_by_time_s is None:
            return None
        return transit_exposure_level(
            self.equivalent_level_db,
            measurement_time_s=self.measurement_time_s,
            pass_by_time_s=self.pass_by_time_s,
        )

    @property
    def start_margin_db(self) -> float:
        """How far the record starts below the level at the front, in dB (6.6.3)."""
        return self.front_level_db - self.record_start_level_db

    @property
    def end_margin_db(self) -> float:
        """How far the record ends below the level at the rear, in dB (6.6.3)."""
        return self.rear_level_db - self.record_end_level_db

    @property
    def recording_interval_sufficient(self) -> bool:
        """Whether the record starts and ends at least 10 dB down, 6.6.3."""
        return bool(
            self.start_margin_db >= _RECORD_MARGIN_DB - _TOLERANCE
            and self.end_margin_db >= _RECORD_MARGIN_DB - _TOLERANCE
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the level history with the measurement interval, as Figure 7 does.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the level history line.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.rolling_stock import plot_pass_by_measurement

        check_language(language)
        return plot_pass_by_measurement(self, ax, language=language, **kwargs)


def _index(time_s: float, fs: float, size: int, name: str) -> int:
    """The sample of a time inside the record."""
    moment = require_non_negative(time_s, name)
    index = int(round(moment * fs))
    if index > size:
        msg = f"'{name}' is {moment:g} s, past the end of the {size / fs:g} s record."
        raise ValueError(msg)
    return index


def pass_by_measurement(
    signal: SignalInput,
    fs: float | None = None,
    *,
    start_s: float,
    end_s: float,
    pass_by_time_s: float | None = None,
    front_passing_s: float | None = None,
    rear_passing_s: float | None = None,
    history_interval_s: float = _HISTORY_INTERVAL_S,
) -> PassByMeasurement:
    r"""The pass-by quantities of one record, 6.5 and 6.6.3.

    The record is A-weighted (IEC 61672-1) and the equivalent level

    .. math::

       L_{p\mathrm{Aeq},T} = 10 \lg \left( \frac{1}{T} \int_{T_1}^{T_2}
       \frac{p_\mathrm{A}^2(t)}{p_0^2}\,\mathrm{d}t \right)

    is taken over the measurement interval (3.14); it is the pass-by level
    :math:`L_{p\mathrm{Aeq},T_p}` when the interval is the unit's pass-by
    time, from its front to its rear for a fixed formation, from the centre of
    the first unit under test to the centre of the last within a train
    (6.6.3). :math:`L_{p\mathrm{AF}}(t)` is the A-weighted level with time
    weighting F, whose integrator starts from the mean square of the first
    125 ms so the record's start does not read as an onset; its maximum
    within the interval is :math:`L_{p\mathrm{AFmax}}` (3.13). Given the
    pass-by time :math:`T_p`, the result also carries the energy of the
    interval spread over it, the transit exposure level of ISO 3095:2005
    (:attr:`PassByMeasurement.normalized_level_db`).

    6.6.3 asks that the record start at least 10 dB below the level when the
    front of the train is opposite the microphone and end 10 dB below the
    level at its rear; the result keeps both margins.

    :param signal: The sound pressure record in pascals, unweighted, one
        channel, or a mono :class:`phonometry.io.Signal`, whose calibration is
        applied.
    :param fs: The sampling rate, in hertz; a Signal brings its own.
    :param start_s: :math:`T_1`, in seconds from the start of the record.
    :param end_s: :math:`T_2`, in seconds.
    :param pass_by_time_s: :math:`T_p`, in seconds, to normalise the interval
        to (:func:`pass_by_time`).
    :param front_passing_s: When the front of the train is opposite the
        microphone, in seconds; ``start_s`` when omitted, as for a fixed
        formation.
    :param rear_passing_s: When its rear is; ``end_s`` when omitted.
    :param history_interval_s: The interval the level history is stored at,
        in seconds.
    :return: The levels of the record.
    :raises ValueError: For a record of more than one channel, an empty
        record, an interval that is empty or runs past the record, or times
        that are negative.
    """
    rate = resolve_fs(signal, fs, name="signal")
    samples = require_1d_signal(resolve_samples(signal, name="signal"), "'signal'")
    rate = require_positive(float(rate), "fs")
    if samples.size == 0:
        msg = "'signal' holds no sample."
        raise ValueError(msg)
    first = _index(start_s, rate, samples.size, "start_s")
    last = _index(end_s, rate, samples.size, "end_s")
    if last <= first:
        msg = "'end_s' must come after 'start_s' by at least one sample."
        raise ValueError(msg)
    from ...filters.weighting import time_weighting, weighting_filter

    weighted = np.asarray(
        weighting_filter(samples, round(rate), curve="A"), dtype=np.float64
    )
    window = min(weighted.size, max(1, round(_F_TIME_CONSTANT_S * rate)))
    warm_start = float(np.mean(weighted[:window] ** 2))
    mean_square = np.asarray(
        time_weighting(weighted, round(rate), mode="fast", initial_state=warm_start),
        dtype=np.float64,
    )
    floor = np.finfo(np.float64).tiny

    def level(value: float) -> float:
        return float(10.0 * np.log10(max(value, floor) / _P0_PA**2))

    front = _index(
        start_s if front_passing_s is None else front_passing_s,
        rate,
        samples.size,
        "front_passing_s",
    )
    rear = _index(
        end_s if rear_passing_s is None else rear_passing_s,
        rate,
        samples.size,
        "rear_passing_s",
    )
    step = max(
        1, round(require_positive(history_interval_s, "history_interval_s") * rate)
    )
    history = np.arange(0, mean_square.size, step)
    tp = (
        None
        if pass_by_time_s is None
        else require_positive(pass_by_time_s, "pass_by_time_s")
    )
    return PassByMeasurement(
        times_s=history / rate,
        levels_db=10.0 * np.log10(np.maximum(mean_square[history], floor) / _P0_PA**2),
        start_s=first / rate,
        end_s=last / rate,
        equivalent_level_db=level(float(np.mean(weighted[first:last] ** 2))),
        max_level_db=level(float(np.max(mean_square[first:last]))),
        front_level_db=level(float(mean_square[min(front, mean_square.size - 1)])),
        rear_level_db=level(float(mean_square[min(rear, mean_square.size - 1)])),
        record_start_level_db=level(float(mean_square[0])),
        record_end_level_db=level(float(mean_square[-1])),
        pass_by_time_s=tp,
    )


# ---------------------------------------------------------------------------
# The stationary test and the tests of three runs
# ---------------------------------------------------------------------------


def stationary_unit_level(levels_db: ArrayLike, lengths_m: ArrayLike) -> float:
    r"""The length-weighted energy average of a stationary mesh, Formulae 1 to 3.

    .. math::

       \langle L_{p\mathrm{Aeq},T} \rangle = 10 \lg \left( \sum_{i=1}^{n}
       \frac{l_i}{l_\mathrm{tot}} 10^{L^i_{p\mathrm{Aeq},T}/10} \right)

    over the positions of the whole unit (Formula 1) or of one car (Formula
    3). The mesh is the whole one of 5.5.1.1 before any reduction: an omitted
    position takes the level of the equivalent one measured (5.5.1.2), and an
    end position stands for :data:`STATIONARY_END_POSITION_LENGTH_M`.

    :param levels_db: :math:`L^i_{p\mathrm{Aeq},T}` of each position, in dB.
    :param lengths_m: The length :math:`l_i` each position stands for, in
        metres.
    :return: The average, in dB, unrounded.
    :raises ValueError: For levels that are not finite, lengths that are not
        positive, or arrays of different lengths.
    """
    levels = require_finite_array(levels_db, "levels_db")
    lengths = require_positive_array(lengths_m, "lengths_m")
    if levels.size != lengths.size:
        msg = "'levels_db' and 'lengths_m' need one value per position each."
        raise ValueError(msg)
    weights = lengths / np.sum(lengths)
    return float(10.0 * np.log10(np.sum(weights * 10.0 ** (levels / 10.0))))


def _spread(values: NDArray[np.float64]) -> float:
    return float(np.max(values) - np.min(values))


@dataclass(frozen=True)
class StationaryTestResult(OwnsArrays):
    r"""The stationary test of a unit, 5.8.1.

    :param levels_db: :math:`L^i_{p\mathrm{Aeq},T}`, one row per set of
        measurements (one sample at every position) and one column per
        position, in dB.
    :param lengths_m: The length each position stands for, in metres.
    """

    levels_db: NDArray[np.float64]
    lengths_m: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Check the shapes and hold both arrays read-only.

        :raises ValueError: For fewer than three sets, a length per position
            missing, levels that are not finite or lengths that are not
            positive.
        """
        levels = np.atleast_2d(np.asarray(self.levels_db, dtype=np.float64))
        lengths = require_positive_array(self.lengths_m, "lengths_m")
        if levels.ndim != 2 or levels.shape[1] != lengths.size:  # noqa: PLR2004
            msg = "'levels_db' needs one row per set and one column per position."
            raise ValueError(msg)
        if not np.all(np.isfinite(levels)):
            msg = "'levels_db' must be finite."
            raise ValueError(msg)
        if levels.shape[0] < _MINIMUM_RUNS:
            msg = f"5.7 asks for at least {_MINIMUM_RUNS} sets; got {levels.shape[0]}."
            raise ValueError(msg)
        object.__setattr__(self, "levels_db", read_only(levels))
        object.__setattr__(self, "lengths_m", read_only(lengths))

    @property
    def set_levels_db(self) -> NDArray[np.float64]:
        r""":math:`\langle L_{p\mathrm{Aeq},T} \rangle_\mathrm{unit}` of each set, Formula 1, in dB."""
        return np.array(
            [stationary_unit_level(row, self.lengths_m) for row in self.levels_db]
        )

    @property
    def mean_level_db(self) -> float:
        """The arithmetic mean of the set levels, in dB, unrounded."""
        return float(np.mean(self.set_levels_db))

    @property
    def reported_level_db(self) -> float:
        """The test result: the mean rounded to the nearest integer decibel (5.8.1)."""
        return _round_half_up(self.mean_level_db)

    @property
    def position_spreads_db(self) -> NDArray[np.float64]:
        """The spread of the samples of each position across the sets, in dB (9.3)."""
        return np.ptp(self.levels_db, axis=0)

    @property
    def valid(self) -> bool:
        """Whether every position's samples lie within 3 dB of each other (5.7, 9.3)."""
        return bool(np.all(self.position_spreads_db <= _MAXIMUM_SPREAD_DB + _TOLERANCE))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the level of every position and the unit level.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the position bars.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.rolling_stock import plot_stationary_test

        check_language(language)
        return plot_stationary_test(self, ax, language=language, **kwargs)


def stationary_test(levels_db: ArrayLike, lengths_m: ArrayLike) -> StationaryTestResult:
    r"""The stationary test of a unit from its measured mesh, 5.7 and 5.8.1.

    Each set gives the unit level of Formula 1, and the result is the mean of
    the sets rounded to the nearest integer decibel
    (:attr:`StationaryTestResult.reported_level_db`). The samples of a
    position are valid when they are no more than 3 dB apart (9.3).

    :param levels_db: One row per set, one column per position of the whole
        mesh of 5.5.1.1 at 1,2 m, in dB; at least three sets.
    :param lengths_m: The length each position stands for, in metres.
    :return: The test.
    :raises ValueError: See :class:`StationaryTestResult`.
    """
    return StationaryTestResult(
        levels_db=np.asarray(levels_db, dtype=np.float64),
        lengths_m=np.asarray(lengths_m, dtype=np.float64),
    )


@dataclass(frozen=True)
class RollingStockTestResult:
    r"""A test decided by the highest rounded mean of three runs per position.

    :param method: One of :data:`ROLLING_STOCK_TEST_METHODS`.
    :param samples_db: The runs of each position, in dB, keyed by the
        position's name: :math:`L_{p\mathrm{Aeq},T_p}` at constant speed,
        :math:`L_{p\mathrm{AFmax}}` when starting (maximum level method) and
        braking, :math:`L_{p\mathrm{Aeq},T}` when starting (averaged level
        method).
    """

    method: str
    samples_db: Mapping[str, tuple[float, ...]]

    def __post_init__(self) -> None:
        """Check the method and the runs, and freeze them.

        :raises ValueError: For an unknown method, no position, fewer than
            three runs at a position, or a run that is not finite.
        """
        require_choice(self.method, "method", ROLLING_STOCK_TEST_METHODS)
        if not self.samples_db:
            msg = "'samples_db' holds no position."
            raise ValueError(msg)
        frozen: dict[str, tuple[float, ...]] = {}
        for position, runs in self.samples_db.items():
            values = require_finite_array(runs, f"samples_db[{position!r}]")
            if values.size < _MINIMUM_RUNS:
                msg = (
                    f"position {position!r} has {values.size} runs; the test "
                    f"asks for at least {_MINIMUM_RUNS}."
                )
                raise ValueError(msg)
            frozen[str(position)] = tuple(float(v) for v in values)
        object.__setattr__(self, "samples_db", MappingProxyType(frozen))

    @property
    def positions(self) -> tuple[str, ...]:
        """The positions, in the order given."""
        return tuple(self.samples_db)

    @property
    def mean_levels_db(self) -> Mapping[str, float]:
        """The arithmetic mean of each position's runs, in dB, unrounded."""
        return MappingProxyType(
            {p: float(np.mean(v)) for p, v in self.samples_db.items()}
        )

    @property
    def reported_levels_db(self) -> Mapping[str, float]:
        """Each position's mean rounded to the nearest integer decibel."""
        return MappingProxyType(
            {p: _round_half_up(v) for p, v in self.mean_levels_db.items()}
        )

    @property
    def spreads_db(self) -> Mapping[str, float]:
        """The spread of each position's runs, in dB (9.3)."""
        return MappingProxyType(
            {p: _spread(np.asarray(v)) for p, v in self.samples_db.items()}
        )

    @property
    def valid(self) -> bool:
        """Whether every position's runs lie within 3 dB of each other (9.3).

        When they do not, 9.3 asks for more runs; braking with squeal may
        not get there, and 8.7 NOTE 1 then reports the runs without a mean.
        """
        return all(
            s <= _MAXIMUM_SPREAD_DB + _TOLERANCE for s in self.spreads_db.values()
        )

    @property
    def governing_position(self) -> str:
        """The position whose rounded mean is the result, the first on a tie."""
        reported = self.reported_levels_db
        return max(
            self.positions, key=lambda p: (reported[p], -self.positions.index(p))
        )

    @property
    def final_level_db(self) -> float:
        """The test result: the highest rounded mean (6.7.1, 7.5.4, 7.6.4, 8.7)."""
        return self.reported_levels_db[self.governing_position]

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw every run, each position's rounded mean and the result.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the mean markers.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.rolling_stock import plot_rolling_stock_test

        check_language(language)
        return plot_rolling_stock_test(self, ax, language=language, **kwargs)


def rolling_stock_test(
    samples_db: Mapping[str, ArrayLike], *, method: str = "constant_speed"
) -> RollingStockTestResult:
    """The result of a constant-speed, starting or braking test, 6.7.1, 7.5.4, 7.6.4, 8.7.

    Each position's runs are averaged arithmetically and rounded to the
    nearest integer decibel, and the result is the highest of those: the
    louder side at constant speed and in the averaged level method, the
    loudest position in the maximum level method and in braking. A speed
    normalisation, when one is required, goes on the runs before this
    (6.7.1).

    :param samples_db: The runs of each position, in dB, keyed by a name
        for the position (``"left"``, ``"right"``, ``"front, direction 1"``).
    :param method: One of :data:`ROLLING_STOCK_TEST_METHODS`.
    :return: The test.
    :raises ValueError: See :class:`RollingStockTestResult`.
    """
    return RollingStockTestResult(
        method=method,
        samples_db={
            p: tuple(np.atleast_1d(np.asarray(v, dtype=np.float64)))
            for p, v in samples_db.items()
        },
    )


# ---------------------------------------------------------------------------
# Annex A, D and 6.3.4
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RiseSpeedResult(OwnsArrays):
    r"""The impulsive character of a level history, Annex A.

    :param times_s: The times of the history, in seconds.
    :param levels_db: :math:`L_{p\mathrm{AF}}(t)`, in dB.
    :param slopes: The first and last sample of every slope that rises
        without a break by at least 10 dB.
    :param rise_speeds_db_per_s: The steepest rise :math:`s_j` of each slope,
        in dB/s (Formula A.1).
    """

    times_s: NDArray[np.float64]
    levels_db: NDArray[np.float64]
    slopes: tuple[tuple[int, int], ...]
    rise_speeds_db_per_s: tuple[float, ...]

    def __post_init__(self) -> None:
        """Hold the history read-only and the slopes and speeds as tuples."""
        object.__setattr__(
            self, "times_s", read_only(np.asarray(self.times_s, dtype=np.float64))
        )
        object.__setattr__(
            self, "levels_db", read_only(np.asarray(self.levels_db, dtype=np.float64))
        )
        object.__setattr__(
            self,
            "slopes",
            tuple((int(start), int(stop)) for start, stop in self.slopes),
        )
        object.__setattr__(
            self,
            "rise_speeds_db_per_s",
            tuple(float(s) for s in self.rise_speeds_db_per_s),
        )

    @property
    def rise_speed_db_per_s(self) -> float | None:
        r"""The rise speed :math:`s = \max(s_j)`, in dB/s; ``None`` when no slope rises 10 dB."""
        return max(self.rise_speeds_db_per_s) if self.rise_speeds_db_per_s else None

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the history with the slopes that count and the steepest rise.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the history line.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.rolling_stock import plot_rise_speed

        check_language(language)
        return plot_rise_speed(self, ax, language=language, **kwargs)


def impulsiveness_rise_speed(
    times_s: ArrayLike, levels_db: ArrayLike
) -> RiseSpeedResult:
    r"""The rise speed that characterises impulsive noise, Annex A.

    The rising slopes of :math:`L_{p\mathrm{AF}}(t)` are the stretches where
    it increases from one sample to the next without a break; only those that
    rise by 10 dB or more count. Each gives its steepest rise

    .. math::

       s_j = \max \left[ \frac{\mathrm{d}L_{p\mathrm{AF}}(t)}{\mathrm{d}t}
       \right]\ \mathrm{dB/s}

    (Formula A.1), taken here as the largest difference quotient between
    neighbouring samples, and the result is the largest of them,
    :math:`s = \max(s_j)`. The history should be sampled finely enough for the
    derivative to mean something; :func:`pass_by_measurement` stores it every
    10 ms.

    :param times_s: The sample times, in seconds, increasing.
    :param levels_db: :math:`L_{p\mathrm{AF}}(t)`, in dB.
    :return: The slopes and their rise speeds.
    :raises ValueError: For arrays of different lengths, fewer than two
        samples, or times that do not increase.
    """
    times = require_finite_array(times_s, "times_s")
    levels = require_finite_array(levels_db, "levels_db")
    minimum_samples = 2
    if times.size != levels.size or times.size < minimum_samples:
        msg = "'times_s' and 'levels_db' need one value per sample each, at least two."
        raise ValueError(msg)
    steps = np.diff(times)
    if np.any(steps <= 0.0):
        msg = "'times_s' must increase."
        raise ValueError(msg)
    rises = np.diff(levels)
    slopes: list[tuple[int, int]] = []
    speeds: list[float] = []
    index = 0
    while index < rises.size:
        if rises[index] <= 0.0:
            index += 1
            continue
        start = index
        while index < rises.size and rises[index] > 0.0:
            index += 1
        # The slope runs from sample ``start`` to sample ``index``.
        if levels[index] - levels[start] >= _IMPULSIVE_RISE_DB - _TOLERANCE:
            slopes.append((start, index))
            speeds.append(float(np.max(rises[start:index] / steps[start:index])))
    return RiseSpeedResult(
        times_s=times,
        levels_db=levels,
        slopes=tuple(slopes),
        rise_speeds_db_per_s=tuple(speeds),
    )


def background_level_increase(
    measured_level_db: ArrayLike, background_level_db: ArrayLike
) -> float | NDArray[np.float64]:
    r"""How much a steady background raises a measured level, Formula D.1.

    .. math::

       \Delta L = L_\mathrm{meas} - 10 \lg \left( 10^{L_\mathrm{meas}/10}
       - 10^{L_\mathrm{bg}/10} \right)

    The informative procedure of Annex D.4.2 for sites that cannot meet the
    10 dB margin of 5.2.3, 6.1.3, 7.2.3 and 8.1.3; it is used only when the
    level stands more than 3 dB above the background, and band by band for a
    spectrum.

    :param measured_level_db: :math:`L_\mathrm{meas}`, the level measured with
        the unit, in dB; one value or one per band.
    :param background_level_db: :math:`L_\mathrm{bg}`, the background alone,
        in dB.
    :return: :math:`\Delta L`, in dB, as one value or one per band.
    :raises ValueError: For levels that are not finite, of different lengths,
        or no more than 3 dB above the background.
    """
    measured = require_finite_array(measured_level_db, "measured_level_db")
    background = require_finite_array(background_level_db, "background_level_db")
    if measured.size != background.size:
        msg = "'measured_level_db' and 'background_level_db' need one value per band each."
        raise ValueError(msg)
    if np.any(measured - background <= _BACKGROUND_EXCESS_DB + _TOLERANCE):
        msg = (
            "D.4.2 applies the correction only where the level stands more than "
            "3 dB above the background."
        )
        raise ValueError(msg)
    increase = measured - 10.0 * np.log10(
        10.0 ** (measured / 10.0) - 10.0 ** (background / 10.0)
    )
    return float(increase[0]) if np.ndim(measured_level_db) == 0 else increase


@dataclass(frozen=True)
class AdjacentVehicleNeutrality:
    r"""Whether a vehicle next to the unit under test is acoustically neutral, 6.3.4.

    :param with_adjacent_level_db: :math:`L_{p\mathrm{Aeq},T_{p1}}`, over the
        units under test and the adjacent vehicle together, in dB.
    :param unit_level_db: :math:`L_{p\mathrm{Aeq},T_p}`, over the units under
        test alone, in dB.
    """

    with_adjacent_level_db: float
    unit_level_db: float

    def __post_init__(self) -> None:
        """Check that both levels are finite.

        :raises ValueError: For a level that is not finite.
        """
        require_finite(self.with_adjacent_level_db, "with_adjacent_level_db")
        require_finite(self.unit_level_db, "unit_level_db")

    @property
    def difference_db(self) -> float:
        """How much the adjacent vehicle adds, from the levels rounded to one decimal, in dB."""
        tenths = round(_round_half_up(self.with_adjacent_level_db, 1) * 10) - round(
            _round_half_up(self.unit_level_db, 1) * 10
        )
        return tenths / 10.0

    @property
    def passes(self) -> bool:
        """Whether the adjacent vehicle adds no more than 2,0 dB."""
        tenths = round(_round_half_up(self.with_adjacent_level_db, 1) * 10) - round(
            _round_half_up(self.unit_level_db, 1) * 10
        )
        return tenths <= round(_NEUTRALITY_ALLOWANCE_DB * 10)

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "an AdjacentVehicleNeutrality has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the two levels and the 2 dB the adjacent vehicle may add.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the bars.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.rolling_stock import plot_adjacent_neutrality

        check_language(language)
        return plot_adjacent_neutrality(self, ax, language=language, **kwargs)


def check_adjacent_vehicle_neutrality(
    with_adjacent_level_db: float, unit_level_db: float
) -> AdjacentVehicleNeutrality:
    r"""Is the vehicle next to the unit under test acoustically neutral? 6.3.4.

    It is when it is of the same class as the unit, or when the pass-by level
    over the units under test and the adjacent vehicle,
    :math:`L_{p\mathrm{Aeq},T_{p1}}`, is no more than 2,0 dB above the level
    over the units alone, :math:`L_{p\mathrm{Aeq},T_p}`, both rounded to one
    decimal for the comparison (Figure 5). This is the second test; it is
    made at least once for each tested speed.

    :param with_adjacent_level_db: :math:`L_{p\mathrm{Aeq},T_{p1}}`, in dB.
    :param unit_level_db: :math:`L_{p\mathrm{Aeq},T_p}`, in dB.
    :return: The verdict.
    :raises ValueError: For a level that is not finite.
    """
    return AdjacentVehicleNeutrality(
        with_adjacent_level_db=float(with_adjacent_level_db),
        unit_level_db=float(unit_level_db),
    )


# ---------------------------------------------------------------------------
# Annexes C and E: the roughness seen from the noise
# ---------------------------------------------------------------------------


def _frequency_bands(
    frequencies_hz: ArrayLike,
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Nominal band frequencies and their base-ten band indices."""
    frequencies = require_positive_array(frequencies_hz, "frequencies_hz")
    bands = np.round(10.0 * np.log10(frequencies)).astype(np.int64)
    if np.any(np.diff(bands) <= 0):
        msg = "'frequencies_hz' must name distinct one-third octave bands in increasing order."
        raise ValueError(msg)
    return frequencies, bands


def _roughness_in_frequency(
    levels_db: NDArray[np.float64],
    wavelength_bands: tuple[int, ...],
    speed_m_s: float,
    frequency_bands: NDArray[np.int64],
) -> NDArray[np.float64]:
    r"""Wavelength band roughness carried onto frequency bands, as energies.

    Each band of wavelength becomes the band of frequency :math:`f = v/\lambda`
    and its energy is shared among the normalised one-third octave bands by
    :func:`~phonometry.environment.sources.acoustic_roughness.redistributed_band_energies`.
    """
    lower, upper = _band_edges(np.asarray(wavelength_bands))
    target_lower, target_upper = _band_edges(frequency_bands)
    return redistributed_band_energies(
        speed_m_s * lower,
        speed_m_s * upper,
        10.0 ** (levels_db / 10.0),
        target_lower,
        target_upper,
    )


def _level_difference(
    numerator: NDArray[np.float64], denominator: NDArray[np.float64]
) -> NDArray[np.float64]:
    r""":math:`10 \lg (E_1/E_2)` per band, zero where a band holds no roughness."""
    difference = np.zeros_like(numerator)
    held = (numerator > 0.0) & (denominator > 0.0)
    difference[held] = 10.0 * np.log10(numerator[held] / denominator[held])
    return difference


def _limit_levels(
    spectrum: AcousticRoughnessSpectrum, limit_db: Mapping[float, float]
) -> NDArray[np.float64]:
    """The limit at each band of a spectrum, NaN where the limit sets none."""
    limit = {_band_of_wavelength(float(w)): float(v) for w, v in limit_db.items()}
    return np.array([limit.get(band, np.nan) for band in spectrum.bands])


def _just_compliant_levels(
    roughness: AcousticRoughnessSpectrum, limit_db: Mapping[float, float]
) -> NDArray[np.float64]:
    """Formula C.1: the measured roughness held down to the limit, band by band.

    Where the limit sets no value the measured level stands.
    """
    limit = _limit_levels(roughness, limit_db)
    return np.where(
        np.isnan(limit), roughness.levels_db, np.fmin(roughness.levels_db, limit)
    )


@dataclass(frozen=True)
class SmallRoughnessDeviation(OwnsArrays):
    r"""The acceptance of small roughness exceedances by their effect on the noise, Annex C.

    :param speed_kmh: The train speed of the pass-by, in km/h.
    :param roughness: The quadratically averaged measured roughness.
    :param limit_db: The upper limit the roughness was held down to, nominal
        wavelength in metres to level, held as a read-only copy.
    :param corrected_roughness_levels_db: The just-compliant spectrum of
        Formula C.1, band by band with ``roughness``, in dB re 1 µm.
    :param frequencies_hz: The nominal one-third octave bands of the noise
        spectrum, in hertz.
    :param roughness_correction_db: :math:`\Delta L_{r,\mathrm{rail}}(f)` of
        Formula C.2, in dB.
    :param noise_levels_db: The measured A-weighted spectrum
        :math:`L^\mathrm{measured}_{p\mathrm{Aeq},T_p}(f)`, in dB.
    """

    speed_kmh: float
    roughness: AcousticRoughnessSpectrum
    limit_db: Mapping[float, float]
    corrected_roughness_levels_db: NDArray[np.float64]
    frequencies_hz: NDArray[np.float64]
    roughness_correction_db: NDArray[np.float64]
    noise_levels_db: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Hold the arrays read-only and the limit as a read-only copy.

        The verdict records the limit it was judged against, so the corrected
        spectrum has to be the one Formula C.1 makes of that limit.

        :raises ValueError: For a limit with a wavelength that is not positive
            or two in one one-third octave band, or a corrected spectrum that
            is not Formula C.1 of ``roughness`` and ``limit_db``.
        """
        limit = _frozen_roughness_limit(self.limit_db, "limit_db")
        object.__setattr__(self, "limit_db", limit)
        for name in (
            "corrected_roughness_levels_db",
            "frequencies_hz",
            "roughness_correction_db",
            "noise_levels_db",
        ):
            object.__setattr__(
                self, name, read_only(np.asarray(getattr(self, name), dtype=np.float64))
            )
        expected = _just_compliant_levels(self.roughness, limit)
        corrected = self.corrected_roughness_levels_db
        # Written so that a NaN in the corrected spectrum fails the check too.
        if corrected.shape != expected.shape or not np.all(
            np.abs(corrected - expected) <= _TOLERANCE
        ):
            msg = (
                "'corrected_roughness_levels_db' is not Formula C.1 of 'roughness' "
                "held down to 'limit_db'."
            )
            raise ValueError(msg)

    @property
    def revised_noise_levels_db(self) -> NDArray[np.float64]:
        r""":math:`L^\mathrm{revised}_{p\mathrm{Aeq},T_p}(f)` of Formula C.3, in dB."""
        return np.asarray(self.noise_levels_db - self.roughness_correction_db)

    @property
    def impact_db(self) -> float:
        r""":math:`\Delta L_{p\mathrm{Aeq},T_p}` of Formula C.4, in dB.

        The energy sum of the measured spectrum less that of the revised one:
        an upper bound on what the exceedance added to the pass-by level.
        """
        return _energy_sum_db(self.noise_levels_db) - _energy_sum_db(
            self.revised_noise_levels_db
        )

    @property
    def exceeded(self) -> bool:
        """Whether the measured roughness exceeds the limit in any band at all."""
        return bool(
            np.any(
                self.roughness.levels_db
                > self.corrected_roughness_levels_db + _TOLERANCE
            )
        )

    @property
    def passes(self) -> bool:
        """Whether the effect is at most 1 dB, C.3."""
        return self.impact_db <= _SMALL_DEVIATION_DB + _TOLERANCE

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a SmallRoughnessDeviation has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the measured and revised noise spectra and the correction.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the measured spectrum.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.rolling_stock import plot_small_roughness_deviation

        check_language(language)
        return plot_small_roughness_deviation(self, ax, language=language, **kwargs)


def _noise_spectrum(
    noise_levels_db: ArrayLike, frequencies_hz: ArrayLike
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.int64]]:
    noise = require_finite_array(noise_levels_db, "noise_levels_db")
    frequencies, bands = _frequency_bands(frequencies_hz)
    if noise.size != frequencies.size:
        msg = "'noise_levels_db' and 'frequencies_hz' need one value per band each."
        raise ValueError(msg)
    return noise, frequencies, bands


def check_small_roughness_deviations(
    roughness: AcousticRoughnessSpectrum,
    noise_levels_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    speed_kmh: float,
    limit_db: Mapping[float, float] = REFERENCE_TRACK_ROUGHNESS_LIMIT_DB,
) -> SmallRoughnessDeviation:
    r"""May a track whose roughness exceeds the limit still be used? Annex C.

    **Step 1 (C.2.1).** The just-compliant spectrum is the measured one held
    down to the limit, :math:`\min[L^\mathrm{measured}(\lambda),
    L^\mathrm{limit}(\lambda)]` (Formula C.1); where the limit sets no value
    the measured level stands.

    **Step 2 (C.2.2).** Both spectra are carried from wavelength to frequency
    at the train speed, :math:`f = v/\lambda`, and the energy of each band is
    shared among the normalised one-third octave bands in proportion to the
    width it covers (:func:`~phonometry.environment.sources.acoustic_roughness.redistributed_band_energies`,
    the Annex C algorithm of EN 15610 adapted to bands of unequal width). The
    correction is :math:`\Delta L_{r,\mathrm{rail}}(f) = L^\mathrm{measured}(f) -
    L^\mathrm{corrected}(f)` (Formula C.2), zero where no roughness band reaches.

    **Step 3 (C.2.3).** The revised noise spectrum is the measured one less
    the correction (Formula C.3), and the effect is the energy sum of the
    measured spectrum less that of the revised one (Formula C.4). The track is
    compliant when that is at most 1 dB (C.3), judged for one pass-by at each
    speed.

    :param roughness: The measured roughness of the test section, the spectra
        of its rails quadratically averaged
        (:func:`~phonometry.environment.sources.acoustic_roughness.average_roughness_spectra`).
    :param noise_levels_db: The A-weighted one-third octave spectrum of the
        pass-by, :math:`L_{p\mathrm{Aeq},T_p}(f)`, in dB.
    :param frequencies_hz: Its nominal band frequencies, in hertz.
    :param speed_kmh: The train speed, in km/h.
    :param limit_db: The upper limit, nominal wavelength in metres to level;
        Figure 2 by default. The verdict records it, and
        :func:`check_reference_track` takes the verdict only when it judges
        the track against the same limit (6.2.5 and C.2.1).
    :return: The verdict, the limit it was judged against and every
        intermediate spectrum.
    :raises ValueError: For a speed that is not positive, a noise spectrum
        that does not match its bands, or a limit with a wavelength that is
        not positive or two in one one-third octave band.
    """
    speed = require_positive(speed_kmh, "speed_kmh")
    noise, frequencies, bands = _noise_spectrum(noise_levels_db, frequencies_hz)
    limit = _frozen_roughness_limit(limit_db, "limit_db")
    corrected = _just_compliant_levels(roughness, limit)
    speed_m_s = speed / 3.6
    measured_energy = _roughness_in_frequency(
        roughness.levels_db, roughness.bands, speed_m_s, bands
    )
    corrected_energy = _roughness_in_frequency(
        corrected, roughness.bands, speed_m_s, bands
    )
    return SmallRoughnessDeviation(
        speed_kmh=speed,
        roughness=roughness,
        limit_db=limit,
        corrected_roughness_levels_db=corrected,
        frequencies_hz=frequencies,
        roughness_correction_db=_level_difference(measured_energy, corrected_energy),
        noise_levels_db=noise,
    )


@dataclass(frozen=True)
class RoughnessComparability(OwnsArrays):
    r"""How much two tracks' roughness could change a pass-by level, Annex E.

    :param speed_kmh: The train speed, in km/h.
    :param roughness_1: The measured roughness of test situation 1.
    :param roughness_2: That of test situation 2.
    :param frequencies_hz: The nominal bands of the two noise spectra, in hertz.
    :param noise_levels_1_db: The A-weighted pass-by spectrum of situation 1, in dB.
    :param noise_levels_2_db: That of situation 2, in dB.
    :param level_differences_db: :math:`\Delta L^{\mathrm{min},1}`,
        :math:`\Delta L^{\mathrm{max},1}`, :math:`\Delta L^{\mathrm{min},2}` and
        :math:`\Delta L^{\mathrm{max},2}` of Formula E.4, in dB, in that order.
    """

    speed_kmh: float
    roughness_1: AcousticRoughnessSpectrum
    roughness_2: AcousticRoughnessSpectrum
    frequencies_hz: NDArray[np.float64]
    noise_levels_1_db: NDArray[np.float64]
    noise_levels_2_db: NDArray[np.float64]
    level_differences_db: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        """Hold the arrays read-only and the four differences as a tuple.

        :raises ValueError: For other than four differences.
        """
        for name in ("frequencies_hz", "noise_levels_1_db", "noise_levels_2_db"):
            object.__setattr__(
                self, name, read_only(np.asarray(getattr(self, name), dtype=np.float64))
            )
        differences = tuple(float(d) for d in self.level_differences_db)
        if len(differences) != _FORMULA_E4_TERMS:
            msg = (
                "'level_differences_db' holds the four differences of Formula "
                f"E.4; got {len(differences)}."
            )
            raise ValueError(msg)
        object.__setattr__(self, "level_differences_db", differences)

    @property
    def envelope_min(self) -> AcousticRoughnessSpectrum:
        """The minimum envelope of the two roughness spectra, Formula E.1."""
        return _envelope(self.roughness_1, self.roughness_2, np.fmin)

    @property
    def envelope_max(self) -> AcousticRoughnessSpectrum:
        """The maximum envelope of the two roughness spectra, Formula E.1."""
        return _envelope(self.roughness_1, self.roughness_2, np.fmax)

    @property
    def bound_db(self) -> float:
        r""":math:`\Delta L_{p\mathrm{Aeq},T_p}` of Formula E.5, in dB.

        The largest magnitude of the four differences: the most the roughness
        difference between the two situations could change the pass-by level.
        """
        return max(abs(d) for d in self.level_differences_db)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the two roughness spectra and their envelopes, as Figure E.1.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the maximum envelope.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.rolling_stock import plot_roughness_comparability

        check_language(language)
        return plot_roughness_comparability(self, ax, language=language, **kwargs)


def _common(
    first: AcousticRoughnessSpectrum, second: AcousticRoughnessSpectrum
) -> tuple[list[int], NDArray[np.float64], NDArray[np.float64]]:
    """The bands two spectra share, and each one's levels there."""
    bands = sorted(set(first.bands) & set(second.bands))
    if not bands:
        msg = "the two roughness spectra have no band in common."
        raise ValueError(msg)
    one = dict(zip(first.bands, first.levels_db, strict=True))
    two = dict(zip(second.bands, second.levels_db, strict=True))
    return bands, np.array([one[b] for b in bands]), np.array([two[b] for b in bands])


def _envelope(
    first: AcousticRoughnessSpectrum,
    second: AcousticRoughnessSpectrum,
    pick: Callable[[NDArray[np.float64], NDArray[np.float64]], NDArray[np.float64]],
) -> AcousticRoughnessSpectrum:
    bands, one, two = _common(first, second)
    return AcousticRoughnessSpectrum(
        wavelengths_m=np.array([_nominal_wavelength_m(b) for b in bands]),
        levels_db=pick(one, two),
    )


def roughness_comparability(
    roughness_1: AcousticRoughnessSpectrum,
    roughness_2: AcousticRoughnessSpectrum,
    noise_levels_1_db: ArrayLike,
    noise_levels_2_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    speed_kmh: float,
) -> RoughnessComparability:
    r"""Bound how much the roughness of two tracks could change a pass-by level, Annex E.

    **E.2.1.** The minimum and maximum envelopes of the two measured roughness
    spectra are taken band by band (Formula E.1). **E.2.2.** The two measured
    spectra and the two envelopes are carried to frequency at the train speed
    as in Annex C, and each measured spectrum gets two correcting spectra, its
    difference from each envelope (Formula E.2). **E.2.3.** Each situation's
    noise spectrum is revised by its two corrections (Formula E.3), the
    energy-summed difference of measured and revised gives
    :math:`\Delta L^{\mathrm{min},i} \ge 0` and
    :math:`\Delta L^{\mathrm{max},i} \le 0` (Formula E.4), and the bound is
    the largest of their magnitudes (Formula E.5). It is an approximate bound
    for roughness alone, not a prediction (E.1).

    :param roughness_1: The measured roughness of test situation 1.
    :param roughness_2: That of test situation 2.
    :param noise_levels_1_db: The A-weighted pass-by spectrum measured in
        situation 1, in dB.
    :param noise_levels_2_db: That of situation 2, in dB.
    :param frequencies_hz: The nominal bands of both noise spectra, in hertz.
    :param speed_kmh: The train speed of both pass-bys, in km/h.
    :return: The four differences and the bound.
    :raises ValueError: For spectra with no band in common, a speed that is
        not positive, or noise spectra that do not match their bands.
    """
    speed = require_positive(speed_kmh, "speed_kmh")
    noise_1, frequencies, bands = _noise_spectrum(noise_levels_1_db, frequencies_hz)
    noise_2, _, _ = _noise_spectrum(noise_levels_2_db, frequencies_hz)
    common, one, two = _common(roughness_1, roughness_2)
    speed_m_s = speed / 3.6
    band_tuple = tuple(common)
    in_frequency = {
        name: _roughness_in_frequency(levels, band_tuple, speed_m_s, bands)
        for name, levels in (
            ("1", one),
            ("2", two),
            ("min", np.fmin(one, two)),
            ("max", np.fmax(one, two)),
        )
    }
    differences: list[float] = []
    for situation, noise in (("1", noise_1), ("2", noise_2)):
        for envelope in ("min", "max"):
            correction = _level_difference(
                in_frequency[situation], in_frequency[envelope]
            )
            differences.append(
                _energy_sum_db(noise) - _energy_sum_db(noise - correction)
            )
    return RoughnessComparability(
        speed_kmh=speed,
        roughness_1=roughness_1,
        roughness_2=roughness_2,
        frequencies_hz=frequencies,
        noise_levels_1_db=noise_1,
        noise_levels_2_db=noise_2,
        level_differences_db=(
            differences[0],
            differences[1],
            differences[2],
            differences[3],
        ),
    )


# ---------------------------------------------------------------------------
# 6.2: the reference track
# ---------------------------------------------------------------------------


#: Where the length a line analysed by digital filters needs is written.
_FILTERED_LENGTH_CLAUSE = "EN 15610 7.4.3"


@dataclass(frozen=True)
class TrackCondition:
    """One requirement of the reference track and whether it holds.

    :param clause: Where the requirement is written (``"6.2.5"``).
    :param requirement: What it asks, in words.
    :param holds: Whether it holds; ``None`` when the input to judge it was not
        given.
    :param detail: The numbers it was judged on.
    """

    clause: str
    requirement: str
    holds: bool | None
    detail: str


@dataclass(frozen=True)
class ReferenceTrackCheck:
    """The verdict on a test track against the reference conditions of ISO 3095 6.2.

    :param speed_kmh: The test speed the track was judged for, in km/h.
    :param roughness: The roughness spectra of the rails, one per rail or
        line, each already averaged over its records.
    :param decay_rates: The decay rates, vertical and lateral, of each set of
        measurements.
    :param conditions: Every requirement judged, in the order of the clause.
    :param roughness_limit_db: The roughness limit judged against, held as a
        read-only copy.
    :param decay_limits_db_per_m: The decay-rate limits judged against, held
        as read-only copies.
    :param small_deviations: The Annex C verdict the roughness limit was
        judged by, when the roughness exceeds the limit and one was given;
        ``None`` otherwise.
    """

    speed_kmh: float
    roughness: tuple[AcousticRoughnessSpectrum, ...]
    decay_rates: tuple[TrackDecayRate, ...]
    conditions: tuple[TrackCondition, ...]
    roughness_limit_db: Mapping[float, float]
    decay_limits_db_per_m: Mapping[str, Mapping[float, float]]
    small_deviations: SmallRoughnessDeviation | None = None

    def __post_init__(self) -> None:
        """Hold the sequences as tuples and the limits as read-only copies.

        The verdict shares no mapping with its caller, so the limits it
        reports and draws stay the ones its conditions were judged against.

        :raises ValueError: For what :func:`check_reference_track` refuses:
            decay limits that leave out a direction, limits with a band that
            is not positive or two keys in one one-third octave band, or an
            Annex C verdict of another speed, of another roughness or against
            another roughness limit.
        """
        object.__setattr__(self, "roughness", tuple(self.roughness))
        object.__setattr__(self, "decay_rates", tuple(self.decay_rates))
        object.__setattr__(self, "conditions", tuple(self.conditions))
        object.__setattr__(
            self, "roughness_limit_db", _frozen_roughness_limit(self.roughness_limit_db)
        )
        object.__setattr__(
            self,
            "decay_limits_db_per_m",
            _frozen_decay_limits(self.decay_limits_db_per_m),
        )
        if self.small_deviations is not None:
            _require_annex_c_of_this_track(
                self.small_deviations,
                self.roughness,
                self.speed_kmh,
                self.roughness_limit_db,
            )

    @property
    def passes(self) -> bool:
        """Whether every requirement judged holds and none was left unjudged for want of data.

        The curve radius and the gradient are judged only when given; the
        roughness and both decay rates are always required, and so is the
        length of a line analysed by EN 15610 Method B.
        """
        return all(
            c.holds is True for c in self.conditions if c.holds is not None
        ) and all(
            c.holds is not None
            for c in self.conditions
            if c.clause in {"6.2.5", "6.2.6", _FILTERED_LENGTH_CLAUSE}
        )

    @property
    def failed(self) -> tuple[TrackCondition, ...]:
        """The requirements that do not hold."""
        return tuple(c for c in self.conditions if c.holds is False)

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a ReferenceTrackCheck has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self,
        ax: Axes | None = None,
        *,
        panel: str = "roughness",
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        """Draw the roughness spectra against Figure 2, or the decay rates against Figure 3.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param panel: ``"roughness"`` or ``"decay"``.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the measured spectra.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.rolling_stock import plot_reference_track

        check_language(language)
        require_choice(panel, "panel", ("roughness", "decay"))
        return plot_reference_track(self, ax, panel=panel, language=language, **kwargs)


def _frequency_band(frequency_hz: float) -> int:
    """The index of the one-third octave band a nominal frequency names."""
    return round(10.0 * math.log10(frequency_hz))


def _bands_named_twice(
    keys: NDArray[np.float64], band_of: Callable[[float], int], unit: str
) -> list[str]:
    """Each set of limit keys that fall in one one-third octave band, in words.

    A limit is read band by band, so of two keys in one band only one would
    be applied, and the verdict would hold a limit it did not judge against.
    """
    groups: dict[int, list[float]] = {}
    for key in keys.tolist():
        groups.setdefault(band_of(key), []).append(key)
    return [
        " and ".join(f"{key:g} {unit}" for key in group)
        + " in one one-third octave band"
        for group in groups.values()
        if len(group) > 1
    ]


def _frozen_roughness_limit(
    limit_db: Mapping[float, float], name: str = "roughness_limit_db"
) -> Mapping[float, float]:
    """A read-only copy of a roughness limit, nominal wavelength to level.

    :raises ValueError: For a wavelength that is not positive, or two that
        fall in one one-third octave band.
    """
    limit = {float(w): float(v) for w, v in limit_db.items()}
    if limit:
        wavelengths = require_positive_array(list(limit), name)
        problems = _bands_named_twice(wavelengths, _band_of_wavelength, "m")
        if problems:
            msg = f"'{name}' has " + "; ".join(problems) + "."
            raise ValueError(msg)
    return MappingProxyType(limit)


def _frozen_decay_limits(
    limits: Mapping[str, Mapping[float, float]],
) -> Mapping[str, Mapping[float, float]]:
    """A read-only copy of decay-rate limits, direction to band to rate.

    :raises ValueError: Unless the limits give at least one band for each
        direction of :data:`TRACK_DECAY_DIRECTIONS` and for no other, every
        band at a positive frequency and no two in one one-third octave band.
    """
    given = {str(direction) for direction in limits}
    problems = [
        f"no limit for the {d} direction"
        for d in TRACK_DECAY_DIRECTIONS
        if d not in given
    ]
    problems += [
        f"no band in the {d} limit"
        for d in TRACK_DECAY_DIRECTIONS
        if d in given and not limits[d]
    ]
    problems += [
        f"an unknown direction {d!r}"
        for d in sorted(given - set(TRACK_DECAY_DIRECTIONS))
    ]
    if not problems:
        problems = [
            f"{shared} of the {d} limit"
            for d in TRACK_DECAY_DIRECTIONS
            for shared in _bands_named_twice(
                require_positive_array(list(limits[d]), "decay_limits_db_per_m"),
                _frequency_band,
                "Hz",
            )
        ]
    if problems:
        msg = "'decay_limits_db_per_m' has " + "; ".join(problems) + "."
        raise ValueError(msg)
    return MappingProxyType(
        {
            str(direction): MappingProxyType(
                {float(f): float(v) for f, v in limit.items()}
            )
            for direction, limit in limits.items()
        }
    )


def _same_spectrum(
    first: AcousticRoughnessSpectrum, second: AcousticRoughnessSpectrum
) -> bool:
    """Whether two roughness spectra hold the same bands at the same levels."""
    return first.bands == second.bands and bool(
        np.all(np.abs(first.levels_db - second.levels_db) <= _TOLERANCE)
    )


def _same_limit(first: Mapping[float, float], second: Mapping[float, float]) -> bool:
    """Whether two roughness limits set the same level in the same bands.

    Written so that a NaN level never compares equal to anything.
    """
    one = {_band_of_wavelength(w): level for w, level in first.items()}
    two = {_band_of_wavelength(w): level for w, level in second.items()}
    return one.keys() == two.keys() and all(
        abs(one[band] - two[band]) <= _TOLERANCE for band in one
    )


def _require_annex_c_of_this_track(
    small_deviations: SmallRoughnessDeviation,
    roughness: Sequence[AcousticRoughnessSpectrum],
    speed: float,
    limit_db: Mapping[float, float],
) -> None:
    """Refuse an Annex C verdict of another speed, another roughness or another limit.

    C.3 examines the compliance at each speed, C.2.1 takes the quadratic
    average of the measured spectra, and Formula C.1 holds them down to the
    limit 6.2.5 judges them against, so the verdict has to be the one of
    this speed, of the average of these spectra and of this limit.

    :raises ValueError: For a verdict of another speed, another roughness or
        another limit.
    """
    if not math.isclose(small_deviations.speed_kmh, speed, rel_tol=_TOLERANCE):
        msg = (
            f"'small_deviations' was judged at {small_deviations.speed_kmh:g} km/h "
            f"and the track at {speed:g} km/h; C.3 examines each speed on its own."
        )
        raise ValueError(msg)
    try:
        average: AcousticRoughnessSpectrum | None = average_roughness_spectra(roughness)
    except ValueError:
        average = None
    if average is None or not _same_spectrum(small_deviations.roughness, average):
        msg = (
            "'small_deviations' was judged on another roughness; C.2.1 takes the "
            "quadratic average of the spectra judged here (average_roughness_spectra)."
        )
        raise ValueError(msg)
    if not _same_limit(small_deviations.limit_db, limit_db):
        msg = (
            "'small_deviations' was judged against another roughness limit; "
            "Formula C.1 holds the roughness down to the limit 6.2.5 judges it "
            "against ('roughness_limit_db')."
        )
        raise ValueError(msg)


def _roughness_conditions(
    roughness: Sequence[AcousticRoughnessSpectrum],
    speed: float,
    limit_db: Mapping[float, float],
    small_deviations: SmallRoughnessDeviation | None,
) -> tuple[list[TrackCondition], bool]:
    """The two requirements of 6.2.5, the wavelength range and the limit.

    The flag says whether the limit was judged through Annex C.
    """
    longest = _LONGEST_WAVELENGTH_M[0 if speed <= _WAVELENGTH_RANGE_SPEED_KMH else 1]
    required = set(
        range(
            _band_of_wavelength(longest),
            _band_of_wavelength(_SHORTEST_WAVELENGTH_M) + 1,
        )
    )
    coverage_requirement = (
        f"roughness measured from {_SHORTEST_WAVELENGTH_M:g} m to {longest:g} m"
    )
    limit_requirement = "roughness at or below the limit of Figure 2"
    if not roughness:
        return [
            TrackCondition(
                clause="6.2.5",
                requirement=coverage_requirement,
                holds=None,
                detail=_NO_SPECTRUM,
            ),
            TrackCondition(
                clause="6.2.5",
                requirement=limit_requirement,
                holds=None,
                detail=_NO_SPECTRUM,
            ),
        ], False
    missing = sorted({b for s in roughness for b in required - set(s.bands)})
    coverage = TrackCondition(
        clause="6.2.5",
        requirement=coverage_requirement,
        holds=not missing,
        detail="every band present"
        if not missing
        else "missing " + ", ".join(f"{_nominal_wavelength_m(b):g} m" for b in missing),
    )
    worst = -math.inf
    worst_band: int | None = None
    for spectrum in roughness:
        excess = spectrum.levels_db - _limit_levels(spectrum, limit_db)
        if np.any(np.isfinite(excess)):
            index = int(np.nanargmax(excess))
            if excess[index] > worst:
                worst, worst_band = float(excess[index]), spectrum.bands[index]
    if worst_band is None:
        return [
            coverage,
            TrackCondition(
                clause="6.2.5",
                requirement=limit_requirement,
                holds=False,
                detail="no band the limit covers",
            ),
        ], False
    where = f"{_nominal_wavelength_m(worst_band):g} m"
    if worst <= _TOLERANCE:
        within = TrackCondition(
            clause="6.2.5",
            requirement=limit_requirement,
            holds=True,
            detail=f"closest to the limit {worst:+.1f} dB at {where}",
        )
    elif small_deviations is not None:
        within = TrackCondition(
            clause="6.2.5",
            requirement=f"{limit_requirement}, or accepted by Annex C",
            holds=small_deviations.passes,
            detail=(
                f"exceeds by {worst:.1f} dB at {where}; "
                f"Annex C effect {small_deviations.impact_db:.2f} dB"
            ),
        )
    else:
        within = TrackCondition(
            clause="6.2.5",
            requirement=limit_requirement,
            holds=False,
            detail=f"exceeds by {worst:.1f} dB at {where}",
        )
    through_annex_c = worst > _TOLERANCE and small_deviations is not None
    return [coverage, within], through_annex_c


def _filtered_length_condition(
    roughness: Sequence[AcousticRoughnessSpectrum],
) -> TrackCondition | None:
    """The length EN 15610 7.4.3 asks of every line analysed by digital filters.

    ``None`` when no spectrum says it came from Method B.
    """
    filtered = [s for s in roughness if s.method == "B"]
    if not filtered:
        return None
    requirement = (
        f"at least {_MINIMUM_FILTERED_TOTAL_M:g} m of record analysed by digital "
        "filtering on every line, once 2 m are discarded at either end"
    )
    lengths = [s.record_length_m for s in filtered]
    if any(length is None for length in lengths):
        return TrackCondition(
            clause=_FILTERED_LENGTH_CLAUSE,
            requirement=requirement,
            holds=None,
            detail="a Method B spectrum without its record length",
        )
    shortest = min(length for length in lengths if length is not None)
    return TrackCondition(
        clause=_FILTERED_LENGTH_CLAUSE,
        requirement=requirement,
        holds=shortest >= _MINIMUM_FILTERED_TOTAL_M * (1.0 - _TOLERANCE),
        detail=f"{shortest:g} m on the shortest line",
    )


def _decay_condition(
    direction: str,
    spectra: Sequence[TrackDecayRate],
    limit: Mapping[float, float],
) -> TrackCondition:
    """The 6.2.6 requirement of one direction."""
    requirement = f"{direction} decay rate at or above the limit of Figure 3"
    if not spectra:
        return TrackCondition(
            clause="6.2.6", requirement=requirement, holds=None, detail=_NO_SPECTRUM
        )
    floors = {_frequency_band(f): (float(f), float(v)) for f, v in limit.items()}
    worst = math.inf
    worst_frequency = math.nan
    missing: set[float] = set()
    for spectrum in spectra:
        bands = [_frequency_band(f) for f in spectrum.frequencies_hz]
        rates = dict(zip(bands, spectrum.decay_rates_db_per_m, strict=True))
        for band, (nominal, floor) in floors.items():
            if band not in rates:
                missing.add(nominal)
                continue
            margin = float(rates[band]) - floor
            if margin < worst:
                worst, worst_frequency = margin, nominal
    if missing:
        return TrackCondition(
            clause="6.2.6",
            requirement=requirement,
            holds=False,
            detail="missing bands " + ", ".join(f"{f:.0f} Hz" for f in sorted(missing)),
        )
    return TrackCondition(
        clause="6.2.6",
        requirement=requirement,
        holds=worst >= -_TOLERANCE,
        detail=f"smallest margin {worst:+.2f} dB/m at {worst_frequency:.0f} Hz",
    )


def _decay_conditions(
    decay_rates: Sequence[TrackDecayRate], limits: Mapping[str, Mapping[float, float]]
) -> list[TrackCondition]:
    """The requirements of 6.2.6 and, with the grid known, of EN 15461 6.7 and 7."""
    conditions = [
        _decay_condition(
            direction,
            [d for d in decay_rates if d.direction == direction],
            limits[direction],
        )
        for direction in TRACK_DECAY_DIRECTIONS
    ]
    known = [d for d in decay_rates if d.minimum_measurable_db_per_m is not None]
    if known:
        unsuitable = sum(int(np.sum(~d.suitable)) for d in known)
        conditions.append(
            TrackCondition(
                clause="EN 15461 7",
                requirement="every decay rate at least twice the floor of Formula 2",
                holds=unsuitable == 0,
                detail=f"{unsuitable} band(s) unsuitable",
            )
        )
        short = [d for d in known if d.far_field_sufficient is False]
        conditions.append(
            TrackCondition(
                clause="EN 15461 6.7",
                requirement="farthest response at least 10 dB below the direct one in every band",
                holds=not short,
                detail=f"{len(short)} set(s) short of 10 dB",
            )
        )
    return conditions


def check_reference_track(
    roughness: Sequence[AcousticRoughnessSpectrum],
    decay_rates: Sequence[TrackDecayRate],
    *,
    speed_kmh: float,
    curve_radius_m: float | None = None,
    track_gradient_ratio: float | None = None,
    small_deviations: SmallRoughnessDeviation | None = None,
    roughness_limit_db: Mapping[float, float] = REFERENCE_TRACK_ROUGHNESS_LIMIT_DB,
    decay_limits_db_per_m: Mapping[
        str, Mapping[float, float]
    ] = REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M,
) -> ReferenceTrackCheck:
    """Is this track a reference track for a constant-speed type test? 6.2.

    **6.2.5.** The roughness of every rail (every line, when 6.4.3 of EN 15610
    asks for three) must cover at least 0,003 m to 0,10 m up to 190 km/h and
    0,003 m to 0,25 m above, and must not exceed the limit of Figure 2 in any
    band (EN 15610 clause 8). A small exceedance is accepted when Annex C
    finds its effect on the pass-by level at most 1 dB: pass the result of
    :func:`check_small_roughness_deviations` for the speed. A line analysed
    by the digital filters of EN 15610 Method B
    (:func:`~phonometry.environment.sources.acoustic_roughness.filtered_roughness_spectrum`)
    must also have at least 15 m of record analysed once 2 m are discarded
    at either end of each record (EN 15610 7.4.3), judged on the record
    length its average carries.

    **6.2.6.** The vertical and the lateral decay rates of every set of
    measurements must be at least the limits of Figure 3 in every band from
    250 Hz to 5 000 Hz (EN 15461 clause 8). When the rates come with their
    grid, clause 7 and 6.7 of EN 15461 are judged too: every rate at least
    twice the floor of Formula 2, and the farthest response 10 dB below the
    direct one.

    **6.2.2.** When given, the curve radius must be at least
    :func:`minimum_curve_radius` of the speed, and the gradient at most 5:1 000
    (the gradient applies where powered units are tested).

    :param roughness: The roughness spectra, one per rail or line, each the
        average of its records (EN 15610 7.6).
    :param decay_rates: The decay rates, vertical and lateral, of every set.
    :param speed_kmh: The test speed, in km/h.
    :param curve_radius_m: The radius of curvature of the track, in metres;
        not judged when omitted.
    :param track_gradient_ratio: The gradient, rise over length (5:1 000 is
        0,005); not judged when omitted.
    :param small_deviations: The Annex C verdict of this speed, computed on the
        quadratic average of ``roughness``
        (:func:`~phonometry.environment.sources.acoustic_roughness.average_roughness_spectra`,
        C.2.1) against ``roughness_limit_db`` (Formula C.1), which accepts a
        roughness exceedance whose effect is small.
    :param roughness_limit_db: The roughness limit; Figure 2 by default.
    :param decay_limits_db_per_m: The decay-rate limits, a band-to-rate
        mapping for each of the two directions; Figure 3 by default.
    :return: The verdict, with every requirement and its numbers.
    :raises ValueError: For a speed that is not positive, a radius or
        gradient that is not a valid number, decay limits that leave out a
        direction, limits with a band that is not positive or two keys in one
        one-third octave band, or an Annex C verdict of another speed, of
        another roughness or against another roughness limit.
    """
    speed = require_positive(speed_kmh, "speed_kmh")
    roughness_limit = _frozen_roughness_limit(roughness_limit_db)
    decay_limits = _frozen_decay_limits(decay_limits_db_per_m)
    if small_deviations is not None:
        _require_annex_c_of_this_track(
            small_deviations, roughness, speed, roughness_limit
        )
    conditions, through_annex_c = _roughness_conditions(
        roughness, speed, roughness_limit, small_deviations
    )
    filtered_length = _filtered_length_condition(roughness)
    if filtered_length is not None:
        conditions.append(filtered_length)
    conditions += _decay_conditions(decay_rates, decay_limits)
    if curve_radius_m is not None:
        radius = require_positive(curve_radius_m, "curve_radius_m")
        needed = minimum_curve_radius(speed)
        conditions.append(
            TrackCondition(
                clause="6.2.2",
                requirement=f"curve radius at least {needed:.0f} m at {speed:g} km/h",
                holds=radius >= needed,
                detail=f"{radius:g} m",
            )
        )
    if track_gradient_ratio is not None:
        gradient = abs(require_finite(track_gradient_ratio, "track_gradient_ratio"))
        conditions.append(
            TrackCondition(
                clause="6.2.2",
                requirement="gradient at most 5:1 000 where powered units are tested",
                holds=gradient <= _MAXIMUM_GRADIENT_RATIO + _TOLERANCE,
                detail=f"{gradient * 1000.0:g}:1 000",
            )
        )
    return ReferenceTrackCheck(
        speed_kmh=speed,
        roughness=tuple(roughness),
        decay_rates=tuple(decay_rates),
        conditions=tuple(conditions),
        roughness_limit_db=roughness_limit,
        decay_limits_db_per_m=decay_limits,
        small_deviations=small_deviations if through_annex_c else None,
    )


# ---------------------------------------------------------------------------
# Annex G: the uncertainty
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PassByUncertainty:
    r"""An uncertainty budget of a rolling stock noise result, Annex G.

    The measurand is the reading plus uncorrelated corrections,
    :math:`Y = \sum X_i` (Formula G.1), so every sensitivity coefficient is 1
    (Formula G.4).

    :param reading_db: The reading :math:`L_p`, in dB.
    :param names: The name of each input quantity.
    :param corrections_db: The mean value correction :math:`\Delta L_p` of
        each input, in dB (0 for a symmetric interval).
    :param standard_uncertainties_db: Its standard uncertainty
        :math:`u(x_i)`, in dB.
    :param coverage_factor: :math:`k`, 2 by G.5.
    """

    reading_db: float
    names: tuple[str, ...]
    corrections_db: tuple[float, ...]
    standard_uncertainties_db: tuple[float, ...]
    coverage_factor: float = _COVERAGE_FACTOR

    def __post_init__(self) -> None:
        """Check every input has one name, correction and uncertainty; hold them as tuples.

        :raises ValueError: For lists of different lengths, no input, two
            inputs of the same name, a negative uncertainty, or a value that
            is not finite.
        """
        require_finite(self.reading_db, "reading_db")
        names = tuple(str(name) for name in self.names)
        corrections = tuple(float(c) for c in self.corrections_db)
        uncertainties = tuple(float(u) for u in self.standard_uncertainties_db)
        count = len(names)
        if count == 0 or not count == len(corrections) == len(uncertainties):
            msg = "every input quantity needs one name, one correction and one uncertainty."
            raise ValueError(msg)
        repeated = sorted({name for name in names if names.count(name) > 1})
        if repeated:
            msg = (
                "every input quantity needs a name of its own, as each has its "
                f"own share of the variance; repeated: {', '.join(repeated)}."
            )
            raise ValueError(msg)
        for u in uncertainties:
            require_non_negative(u, "standard_uncertainties_db")
        require_finite_array(corrections, "corrections_db")
        require_positive(self.coverage_factor, "coverage_factor")
        object.__setattr__(self, "names", names)
        object.__setattr__(self, "corrections_db", corrections)
        object.__setattr__(self, "standard_uncertainties_db", uncertainties)

    @property
    def level_db(self) -> float:
        """The result :math:`y`, the reading plus every mean value correction, in dB."""
        return self.reading_db + sum(self.corrections_db)

    @property
    def combined_uncertainty_db(self) -> float:
        r""":math:`u_\mathrm{c}(y) = \sqrt{\sum u^2(x_i)}`, Formula G.5, in dB."""
        return math.sqrt(sum(u * u for u in self.standard_uncertainties_db))

    @property
    def expanded_uncertainty_db(self) -> float:
        r""":math:`U = k\,u_\mathrm{c}(y)`, Formula G.6, in dB."""
        return self.coverage_factor * self.combined_uncertainty_db

    @property
    def variance_ratios(self) -> Mapping[str, float]:
        """Each input's share of the variance of the result, as Figure G.1 draws it."""
        total = self.combined_uncertainty_db**2
        return MappingProxyType(
            {
                name: (u * u / total if total > 0.0 else 0.0)
                for name, u in zip(
                    self.names, self.standard_uncertainties_db, strict=True
                )
            }
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw each input's share of the variance, largest first, as Figure G.1.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the bars.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.rolling_stock import plot_pass_by_uncertainty

        check_language(language)
        return plot_pass_by_uncertainty(self, ax, language=language, **kwargs)


def _input_names(inputs: Sequence[Quantity]) -> tuple[str, ...]:
    """The name of each input: its own, or its place for one without a name.

    The name by place, ``x1`` for the first input, is primed until no input
    was given it, so a name the user wrote once is never reported repeated.
    """
    taken = {q.name for q in inputs if q.name}
    names: list[str] = []
    for index, quantity in enumerate(inputs):
        name = quantity.name
        if not name:
            name = f"x{index + 1}"
            while name in taken:
                name += "'"
            taken.add(name)
        names.append(name)
    return tuple(names)


def pass_by_uncertainty(
    reading_db: float,
    inputs: Sequence[Quantity],
    *,
    coverage_factor: float = _COVERAGE_FACTOR,
) -> PassByUncertainty:
    r"""The uncertainty of a rolling stock noise result, Annex G.

    The standard uncertainties of the input quantities combine as

    .. math::

       u_\mathrm{c}(y) = \sqrt{\sum_{i=1}^{N} u^2(x_i)}, \qquad U = k\,u_\mathrm{c}(y),
       \qquad k = 2

    (Formulae G.5 and G.6), and their mean value corrections, which Table G.1
    gives for the unsymmetrical ranges, are added to the reading. An input
    known only by its limits :math:`\pm a` has :math:`u = a/\sqrt{3}` (Formula
    G.2): build it with :func:`phonometry.metrology.rectangular`.

    :param reading_db: The reading :math:`L_p`, in dB.
    :param inputs: The input quantities as :class:`phonometry.metrology.Quantity`
        objects, whose ``value`` is the mean value correction in dB and whose
        ``uncertainty`` is the standard uncertainty in dB. An input without a
        name is called by its place, ``x1``, ``x2``, ..., primed (``x1'``)
        when another input was given that name.
    :param coverage_factor: :math:`k`; 2 by G.5.
    :return: The budget.
    :raises ValueError: See :class:`PassByUncertainty`.
    """
    return PassByUncertainty(
        reading_db=float(reading_db),
        names=_input_names(inputs),
        corrections_db=tuple(float(q.value) for q in inputs),
        standard_uncertainties_db=tuple(float(q.uncertainty) for q in inputs),
        coverage_factor=float(coverage_factor),
    )
