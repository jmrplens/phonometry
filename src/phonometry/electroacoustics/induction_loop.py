#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Audio-frequency induction-loop systems for hearing aids: the performance of an installed system.

IEC 60118-4:2014 (read in BS EN 60118-4:2015), with its Amendment 1:2017
(read in the Spanish UNE-EN IEC 60118-4:2016/A1:2018, whose text replaces
clauses 9 and 10), says what field an induction loop has to produce for a
hearing aid switched to its telecoil, and how an installer shows that it
does. The loop's components, the amplifier, the loop as a load and the neck
loop, are the subject of IEC 62489-1 and of
:mod:`phonometry.electroacoustics.induction_loop_components`.

The reference and the level
---------------------------

Everything is a level in decibels referred to a magnetic field strength of
400 mA/m (3.1), :data:`REFERENCE_FIELD_STRENGTH_A_PER_M`:
:math:`L = 20\lg(H / 0{,}4\ \mathrm{A/m})` (:func:`field_strength_level`).
A long-term average of -12 dB, 100 mA/m, at the telecoil gives the same
acoustic output from the hearing aid as a sound pressure level of 70 dB at
its microphone (4.3). The meter is either a true-RMS meter with the 125 ms
"F" averaging of a sound level meter or a peak programme meter (6.1); in case
of doubt the true-RMS one is definitive, and it is the one
:func:`field_strength_meter` implements, flat or A-weighted.

The requirements
----------------

For a system covering a room, the useful magnetic field volume is where the
requirements are met (8.4). They are:

* the field strength, 8.2.7 and 8.4.3: the maximum field, measured with a
  1 kHz sine (or the equivalent combi signal) and the RMS meter, is 400 mA/m
  at one point at least of the useful magnetic field volume (8.2.1), and
  every selected point is within plus or minus 3 dB of it;
* the frequency response, 8.3.7: within plus or minus 3 dB of the response at
  1 kHz from 100 Hz to 5 000 Hz, measured at least at 100 Hz, 1 kHz and 5 kHz;
* the magnetic noise with the system switched on and every input muted, 10.4.7
  (10.2.7 before Amendment 1): if the reference signal-to-noise ratio of the
  site (7.2) is above 47 dB, no point above -47 dB; below 47 dB, no point
  more than 1 dB above its level with the system switched off. Neither
  sentence covers a ratio of exactly 47 dB; the 1 dB rule is applied there
  (see ``docs/ERRATA.md``).

:func:`verify_induction_loop_system` judges the three. The magnetic background
noise of the site, 7.2, is a recommendation, not a requirement, and
:func:`assess_background_noise` classes it: a reference signal-to-noise ratio
above 47 dB is the ideal, 32 dB the recommended minimum below which the
shortfall "shall be reported and agreed with the system operator", and 22 dB
tolerable for short periods when the noise has no significant undesirable
tonal quality or is mostly at low frequencies.

Small systems
-------------

For a disabled refuge or call point and for a counter, Amendment 1 rewrites
clause 9. The field is measured at fixed points (Figures 2 and 3), six at
heights of 1,2 m and 1,7 m for a refuge and three at 1,2 m, 1,45 m and 1,7 m
for a counter (:func:`small_volume_measurement_points`), or, by contract, at
representative points spread through a useful magnetic field volume which, at
the minimum, meets the requirements at one position at least at each of the
heights of 9.2 or 9.3 (9.4). At every point the level shall be within plus or
minus 6 dB of 400 mA/m and meet 8.3.7, at one point at least it shall reach
0 dB, and nowhere where people are expected to stand shall it exceed +8 dB
(9.5, :func:`verify_small_volume_system`).

Two informative passages disagree with 9.5 and are not followed: Annex A.4
allows "up to, but not greater than, +12 dB" at 1,45 m for a counter, and
calls a counter's requirement "less stringent" than a refuge's, where 9.5
applies the same limits to both (see ``docs/ERRATA.md``).

Commissioning and the amplifier
-------------------------------

Amendment 1 replaces the 1,6 kHz overload test with one tied to the programme
(10.3, Table 4, :data:`OVERLOAD_TEST_FREQUENCIES`): with a 1 kHz sine giving a
field 7 dB below the required one, the frequency is raised at constant input
until the loop voltage doubles or the frequency of Table 4 is reached,
whichever is higher, and no clipping may appear at the frequency of Table 4
(10.3.3). One of the three ways the
amendment offers to detect clipping is the comparison of the loop voltage
with the amplifier's compliance voltage of IEC 62489-1, and that one is
computable from the loop's impedance: :func:`verify_amplifier_overload`.

The metal in a building lowers the field inside the loop, more at high
frequencies (Annex F), which is why 8.3.3 recommends starting the frequency
response survey at 5 kHz. Annex F gives no model of the loss: the correction
is the frequency response the installer measures and equalizes, and the
overload test above is what checks that the amplifier can afford it.

Test signals
------------

The pink noise of 6.4, band-limited by third-order Butterworth filters at
75 Hz and 6,5 kHz with a crest factor of 4 (:func:`loop_test_noise`, also the
signal of IEC 62489-1 5.4.8.2 b), and the combi signal of 6.6 and Table 2,
1 kHz tone bursts of at least 1 s interleaved with at least four times as
much of that noise 6 dB lower (:func:`combi_signal`). 6.4 NOTE 2 prints the
theoretical responses of the band-limiting filters as -0,8 dB at 100 Hz and
-0,7 dB at 5 kHz; they are -0,71 dB and -0,82 dB, the other way round
(:func:`band_limit_response`, ``docs/ERRATA.md``).
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy import optimize, signal

from .._internal.boundary import settled
from .._internal.display import RichDisplay
from .._internal.frozen import OwnsArrays, read_only
from .._internal.validation import (
    _as_float64,
    is_at_most,
    require_choice,
    require_count,
    require_finite,
    require_finite_array,
    require_positive,
    require_positive_array,
)
from .induction_loop_components import _reference_index

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

    from .induction_loop_components import AmplifierFrequencyResponse, LoopImpedance

__all__ = [
    "OVERLOAD_TEST_FREQUENCIES",
    "REFERENCE_FIELD_STRENGTH_A_PER_M",
    "AmplifierOverloadVerification",
    "BackgroundNoiseAssessment",
    "FieldStrengthReading",
    "InductionLoopVerification",
    "LoopRequirement",
    "OverloadTestFrequency",
    "assess_background_noise",
    "band_limit_response",
    "combi_signal",
    "field_strength",
    "field_strength_level",
    "field_strength_meter",
    "loop_test_noise",
    "magnetic_flux_density",
    "small_volume_measurement_points",
    "telecoil_response",
    "verify_amplifier_overload",
    "verify_induction_loop_system",
    "verify_small_volume_system",
]

#: The reference magnetic field strength of IEC 60118-4:2014 3.1, in amperes
#: per metre: 400 mA/m is 0 dB, and every level of the standard is referred to
#: it.
REFERENCE_FIELD_STRENGTH_A_PER_M = 0.4

#: The magnetic constant, in henries per metre (IEC 60118-4:2014 E.6 writes
#: it as 4 pi times 10 to the -7 H/m).
_MU_0 = 4.0e-7 * math.pi

#: The window around the specified field strength every selected point of the
#: useful magnetic field volume has to fall in, in dB (8.4.3).
_FIELD_TOLERANCE_DB = 3.0

#: The match within which a measured height is taken as one of the heights of
#: 9.2 and 9.3, in metres: a height typed as 1.2000000001 is still 1,2 m.
_HEIGHT_MATCH_M = 1.0e-6

#: The window around the response at 1 kHz the frequency response has to fall
#: in, in dB (8.3.7).
_RESPONSE_TOLERANCE_DB = 3.0

#: The frequency range of 8.3.7, in hertz.
_RESPONSE_BAND_HZ = (100.0, 5000.0)

#: The frequencies 8.3.3 and 8.3.4 require the response at, as a minimum.
_REQUIRED_RESPONSE_FREQUENCIES_HZ = (100.0, 1000.0, 5000.0)

#: The rank of a set of responses, one row per point and one column per
#: frequency.
_POINTS_BY_FREQUENCIES = 2

#: Relative tolerance within which a frequency is taken as one of the named
#: ones above, so that 1000 typed as 999.9999999 still counts.
_FREQUENCY_MATCH_RTOL = 1.0e-6

#: The reference signal-to-noise ratios of 7.2, in dB: above 47 the ideal, 32
#: the recommended minimum, 22 tolerable for short periods when the noise is
#: not tonal or is mostly at low frequencies.
_SNR_IDEAL_DB = 47.0
_SNR_MINIMUM_DB = 32.0
_SNR_SHORT_PERIODS_DB = 22.0

#: The classes :func:`assess_background_noise` puts a site in, best first.
_NOISE_CATEGORIES = (
    "ideal",
    "acceptable",
    "tolerable_for_short_periods",
    "below_tolerable",
)

#: The ceiling 10.4.7 sets on the noise with the system on, where the site's
#: reference signal-to-noise ratio is above 47 dB, in dB re 400 mA/m.
_SYSTEM_NOISE_CEILING_DB = -47.0

#: The rise 10.4.7 allows over the noise with the system off otherwise, in dB.
_SYSTEM_NOISE_RISE_DB = 1.0

#: The window around 400 mA/m every measurement point of a small-volume system
#: has to fall in, in dB (9.5 as amended).
_SMALL_VOLUME_RANGE_DB = 6.0

#: The level no point where people are expected to stand may exceed, in dB re
#: 400 mA/m (9.5 as amended).
_STANDING_AREA_MAX_DB = 8.0

#: The level of the overload test below the required field strength, in dB
#: (10.3.2 as amended: "7 dB less than the required value").
_OVERLOAD_TEST_OFFSET_DB = -7.0

#: The highest frequency the overload test sweeps to looking for the doubling
#: of the loop voltage, in hertz: the top of the audio band.
_OVERLOAD_SWEEP_LIMIT_HZ = 20000.0

#: The frequency the overload test starts from, in hertz (10.3.2).
_OVERLOAD_START_HZ = 1000.0

#: How much the loop voltage rises before the sweep of 10.3.2 may stop.
_OVERLOAD_VOLTAGE_FACTOR = 2.0

#: Points on the overload sweep between 1 kHz and its end, for the curve.
_OVERLOAD_POINTS = 241

#: The band-limiting filters of the pink noise of 6.4 (and of IEC 62489-1
#: 5.4.8.2 b): third-order Butterworth, -3 dB at 75 Hz and 6,5 kHz.
_BAND_LIMIT_ORDER = 3
_BAND_LIMIT_HZ = (75.0, 6500.0)

#: The crest factor of the pink noise, peak over RMS (6.4: a peak-to-peak to
#: RMS ratio "of at least 18 dB (crest factor = 4)").
_CREST_FACTOR = 4.0

#: Settling time discarded at the start of the band-limited noise, in seconds:
#: the 75 Hz high-pass has rung down to far below the noise within it.
_NOISE_SETTLING_S = 0.25

#: The combi signal of 6.6 and Table 2: a 1 kHz sine at 0 dB, rise and fall
#: times of 5 ms, pink noise 6 dB lower, at least 1 s of sine and at least 4 s
#: of noise, in the ratio of at least 4 to 1.
_COMBI_FREQUENCY_HZ = 1000.0
_COMBI_RAMP_S = 0.005
_COMBI_NOISE_RELATIVE_DB = -6.0
_COMBI_MIN_SINE_S = 1.0
_COMBI_MIN_NOISE_S = 4.0
_COMBI_MIN_RATIO = 4.0

#: The measurement heights of the small-volume layouts of clause 9 as
#: amended, in metres: 1,2 m and 1,7 m for a refuge (9.2), and 1,2 m, 1,45 m
#: and 1,7 m for a counter (9.3, Figure 3 b).
_REFUGE_HEIGHTS_M = (1.2, 1.7)
_COUNTER_HEIGHTS_M = (1.2, 1.45, 1.7)

#: The plan positions of the measurement points, in metres, with the reference
#: point (or the middle of the reference line) at the origin, x across and y
#: away from the call point or counter into the area where people stand.
#: Figure 2 a): along 0 and plus or minus 45 degrees at the inner radius l2 of
#: 300 mm and the outer radius l2 + l3 of 500 mm (as amended). Figure 2 b): a
#: row 424 mm wide at 300 mm and a row 700 mm wide 200 mm further. Figure 3 a):
#: on the semicircle of radius 300 mm, at its bottom and 150 mm either side.
_SIN45 = math.sqrt(0.5)
_PLAN_POINTS_M: Mapping[str, tuple[tuple[float, float], ...]] = MappingProxyType(
    {
        "refuge_small": (
            (-0.3 * _SIN45, 0.3 * _SIN45),
            (0.0, 0.3),
            (0.3 * _SIN45, 0.3 * _SIN45),
            (-0.5 * _SIN45, 0.5 * _SIN45),
            (0.0, 0.5),
            (0.5 * _SIN45, 0.5 * _SIN45),
        ),
        "refuge_large": (
            (-0.212, 0.3),
            (0.0, 0.3),
            (0.212, 0.3),
            (-0.35, 0.5),
            (0.0, 0.5),
            (0.35, 0.5),
        ),
        "counter": (
            (-0.15, math.sqrt(0.3**2 - 0.15**2)),
            (0.0, 0.3),
            (0.15, math.sqrt(0.3**2 - 0.15**2)),
        ),
    }
)

#: The layouts of clause 9, with the heights their points are taken at.
_LAYOUT_HEIGHTS: Mapping[str, tuple[float, ...]] = MappingProxyType(
    {
        "refuge_small": _REFUGE_HEIGHTS_M,
        "refuge_large": _REFUGE_HEIGHTS_M,
        "counter": _COUNTER_HEIGHTS_M,
    }
)

#: The useful magnetic field volume of 9.4, which replaces the points of 9.2
#: (a refuge) or of 9.3 (a counter) by contract and has to cover, at the
#: minimum, the heights of the clause it replaces.
_USEFUL_VOLUME_HEIGHTS: Mapping[str, tuple[float, ...]] = MappingProxyType(
    {
        "refuge_useful_volume": _REFUGE_HEIGHTS_M,
        "counter_useful_volume": _COUNTER_HEIGHTS_M,
    }
)

#: The layouts :func:`verify_small_volume_system` accepts: the three of
#: Figures 2 and 3, and the useful magnetic field volume of 9.4 in place of a
#: refuge's points or a counter's.
_SMALL_VOLUME_LAYOUTS = (*_LAYOUT_HEIGHTS, *_USEFUL_VOLUME_HEIGHTS)


# ---------------------------------------------------------------------------
# Levels, units and the telecoil
# ---------------------------------------------------------------------------


def field_strength_level(field_strength_a_per_m: ArrayLike) -> np.ndarray:
    r"""The magnetic field strength level, in dB re 400 mA/m (IEC 60118-4:2014 3.1).

    .. math::

       L = 20\lg\frac{H}{0{,}4\ \mathrm{A/m}}

    :param field_strength_a_per_m: RMS magnetic field strength, in A/m.
    :return: The level, in dB re 400 mA/m.
    """
    h = _as_float64(field_strength_a_per_m, "field_strength_a_per_m")
    if not np.all(np.isfinite(h)) or np.any(h <= 0.0):
        msg = "'field_strength_a_per_m' must be positive and finite."
        raise ValueError(msg)
    return 20.0 * np.log10(h / REFERENCE_FIELD_STRENGTH_A_PER_M)


def field_strength(level_db: ArrayLike) -> np.ndarray:
    r"""The magnetic field strength of a level in dB re 400 mA/m, in A/m.

    The inverse of :func:`field_strength_level`: -12 dB is the 100 mA/m of
    4.3, and plus or minus 3 dB span 283 mA/m to 565 mA/m (10.2 as amended
    prints 566 mA/m, which is :math:`400\sqrt{2}`).

    :param level_db: Level, in dB re 400 mA/m.
    :return: The RMS field strength, in A/m.
    """
    level = _as_float64(level_db, "level_db")
    if not np.all(np.isfinite(level)):
        msg = "'level_db' must be finite."
        raise ValueError(msg)
    return REFERENCE_FIELD_STRENGTH_A_PER_M * 10.0 ** (level / 20.0)


def magnetic_flux_density(field_strength_a_per_m: ArrayLike) -> np.ndarray:
    r"""The magnetic flux density in air of a field strength (IEC 60118-4:2014 E.6).

    :math:`B = \mu_0 \mu_\mathrm{r} H` with :math:`\mu_\mathrm{r} = 1` in air,
    so 1 A/m is :math:`1{,}2566\ \mu\mathrm{T}` and 400 mA/m about
    :math:`0{,}503\ \mu\mathrm{T}`. E.6 prints 1,256; the last digit rounds to
    7 (see ``docs/ERRATA.md``).

    :param field_strength_a_per_m: Magnetic field strength, in A/m.
    :return: The flux density, in tesla.
    """
    h = _as_float64(field_strength_a_per_m, "field_strength_a_per_m")
    if not np.all(np.isfinite(h)):
        msg = "'field_strength_a_per_m' must be finite."
        raise ValueError(msg)
    return _MU_0 * h


def telecoil_response(angle_deg: ArrayLike) -> np.ndarray:
    r"""The relative response of a telecoil off its axis, in dB (IEC 60118-4:2014 E.2).

    A telecoil follows a cosine law, :math:`20\lg|\cos\theta|`: 3 dB down at
    45 degrees off its magnetic axis and 9,3 dB down at 70 degrees
    (Figure E.6). A telecoil at right angles to the field picks up nothing,
    which is why the measurements of 8.1 are made with the coil vertical
    unless the users kneel or lie.

    The cosine is taken as the sine of the angle from the nearest null,
    :math:`|\cos\theta| = \sin|90^\circ - (\theta \bmod 180^\circ)|`, so a
    right angle gives exactly zero: :math:`\cos(\pi/2)` in floating point is
    :math:`6 \times 10^{-17}`, which would read as about -324 dB instead.

    :param angle_deg: Angle between the telecoil's axis and the field, in
        degrees.
    :return: The response relative to the one on axis, in dB; minus infinity
        at 90 and 270 degrees.
    """
    angle = _as_float64(angle_deg, "angle_deg")
    if not np.all(np.isfinite(angle)):
        msg = "'angle_deg' must be finite."
        raise ValueError(msg)
    from_null = np.abs(90.0 - np.mod(angle, 180.0))
    with np.errstate(divide="ignore"):
        response: np.ndarray = 20.0 * np.log10(np.sin(np.radians(from_null)))
    return response


# ---------------------------------------------------------------------------
# The meter
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FieldStrengthReading(OwnsArrays):
    """What the true-RMS field strength meter of IEC 60118-4:2014 6.1.3 reads.

    :ivar fs: Sample rate of the record, in hertz.
    :ivar weighting: ``"Z"`` (flat, 6.1.2) or ``"A"`` (the noise measurements
        of clause 7 and 10.4).
    :ivar times_s: The time of each reading, in seconds.
    :ivar levels_db: The time-weighted level, 125 ms exponential averaging, in
        dB re 400 mA/m.
    :ivar maximum_db: The maximum indication over the record, the "maximum
        value of the magnetic field" that 8.2.7 sets to 400 mA/m, in dB re
        400 mA/m.
    :ivar equivalent_db: The level of the mean square over the whole record,
        in dB re 400 mA/m.
    """

    fs: int
    weighting: str
    times_s: np.ndarray
    levels_db: np.ndarray
    maximum_db: float
    equivalent_db: float

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the meter reading against time, with the 0 dB reference.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the level curve's ``Axes.plot``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_field_strength_reading

        check_language(language)
        return plot_field_strength_reading(self, ax, language=language, **kwargs)


def field_strength_meter(
    x: ArrayLike, fs: int, *, weighting: str = "Z"
) -> FieldStrengthReading:
    """Read a magnetic field strength record like the true-RMS meter of 6.1.3.

    The meter of IEC 60118-4:2014 6.1.3 is a sound level meter with a
    magnetic pick-up coil in place of the microphone, equalized flat within
    plus or minus 1 dB from 50 Hz to 10 kHz, with a true-RMS detector and the
    125 ms averaging of its "F" mode. The A-weighting of IEC 61672-1 is what
    clause 7 and 10.4 measure noise with. In case of doubt this meter, not the
    peak programme meter of 6.1.4, is definitive (6.1.1).

    :param x: The field strength record, in A/m, as the calibrated pick-up
        gives it.
    :param fs: Sample rate, in hertz.
    :param weighting: ``"Z"`` for the flat response of 6.1.2, ``"A"`` for the
        A-weighted noise measurements of 7.1 and 10.4.6.
    :return: A :class:`FieldStrengthReading`.
    """
    from ..filters.weighting import time_weighting, weighting_filter

    record = require_finite_array(x, "x")
    rate = require_count(fs, "fs")
    curve = require_choice(weighting, "weighting", ("Z", "A"))
    weighted = (
        record if curve == "Z" else np.asarray(weighting_filter(record, rate, "A"))
    )
    mean_square = np.asarray(time_weighting(weighted, rate, "fast"))
    reference_square = REFERENCE_FIELD_STRENGTH_A_PER_M**2
    with np.errstate(divide="ignore"):
        levels = 10.0 * np.log10(mean_square / reference_square)
    equivalent = float(np.mean(weighted * weighted))
    if equivalent <= 0.0:
        msg = "'x' is silent: a meter reads no level from an all-zero record."
        raise ValueError(msg)
    return FieldStrengthReading(
        fs=rate,
        weighting=curve,
        times_s=read_only(np.arange(record.size, dtype=np.float64) / rate),
        levels_db=read_only(levels),
        maximum_db=float(np.max(levels)),
        equivalent_db=10.0 * math.log10(equivalent / reference_square),
    )


# ---------------------------------------------------------------------------
# Test signals
# ---------------------------------------------------------------------------


def band_limit_response(frequencies_hz: ArrayLike) -> np.ndarray:
    r"""The theoretical response of the band limiting of the pink noise, in dB.

    6.4 band-limits the pink noise with third-order Butterworth high-pass and
    low-pass filters, -3 dB at 75 Hz and 6,5 kHz, whose combined response is

    .. math::

       |H|^2 = \frac{1}{1 + (75/f)^6}\,\frac{1}{1 + (f/6500)^6}.

    At 100 Hz it is -0,71 dB and at 5 kHz -0,82 dB. 6.4 NOTE 2, and NOTE 3 to
    5.4.8.2 of IEC 62489-1:2010, print -0,8 dB at 100 Hz and -0,7 dB at 5 kHz,
    the two exchanged (see ``docs/ERRATA.md``). The plus or minus 1 dB flatness
    6.4 requires from 100 Hz to 5 kHz holds either way.

    :param frequencies_hz: Frequencies, in hertz.
    :return: The response, in dB.
    """
    f = require_positive_array(frequencies_hz, "frequencies_hz")
    low, high = _BAND_LIMIT_HZ
    n2 = 2 * _BAND_LIMIT_ORDER
    power = 1.0 / ((1.0 + (low / f) ** n2) * (1.0 + (f / high) ** n2))
    return 10.0 * np.log10(power)


def _band_limited_noise(fs: int, n: int, rms: float, seed: int | None) -> np.ndarray:
    """``n`` samples of the pink noise of 6.4 at an RMS of ``rms``."""
    from ..signals.test_signals import noise_signal

    settle = round(_NOISE_SETTLING_S * fs)
    raw = noise_signal(float(fs), (n + settle) / fs, color="pink", seed=seed)
    high = signal.butter(
        _BAND_LIMIT_ORDER, _BAND_LIMIT_HZ[0], "highpass", fs=fs, output="sos"
    )
    low = signal.butter(
        _BAND_LIMIT_ORDER, _BAND_LIMIT_HZ[1], "lowpass", fs=fs, output="sos"
    )
    shaped = signal.sosfilt(low, signal.sosfilt(high, raw))[settle : settle + n]
    shaped = shaped / math.sqrt(float(np.mean(shaped * shaped)))
    clipped = np.clip(shaped, -_CREST_FACTOR, _CREST_FACTOR)
    return np.asarray(clipped * (rms / math.sqrt(float(np.mean(clipped * clipped)))))


def loop_test_noise(
    fs: int, seconds: float, *, rms: float = 1.0, seed: int | None = None
) -> np.ndarray:
    r"""The pink noise test signal of IEC 60118-4:2014 6.4.

    Pink noise band-limited by third-order Butterworth high-pass and low-pass
    filters, -3 dB at 75 Hz and 6,5 kHz, with "a peak-to-peak voltage (as
    measured with an oscilloscope) to true r.m.s. voltage ratio of at least
    18 dB (crest factor = 4)". The same
    signal drives the compliance voltage measurement of IEC 62489-1:2010
    5.4.8.2 b), which asks for 18 dB plus or minus 2 dB.

    Gaussian noise has no crest factor of its own: in 60 s at 48 kHz it
    reaches about 5,5 times its RMS, a ratio of 21 dB, which meets 6.4 and
    fails 5.4.8.2 b). The noise is therefore clipped at 4 times its RMS and
    rescaled, which gives a peak-to-peak ratio of 18,1 dB and meets both, once
    the record is long enough to reach 4 times its RMS both ways: some tens of
    seconds make that certain, which is the length both measurements run for.
    The filters are the bilinear transforms of the Butterworth prototypes at
    ``fs``, so the response at 5 kHz differs from the analog one of
    :func:`band_limit_response` by a tenth of a decibel at 48 kHz; 6.4
    allows plus or minus 1 dB for exactly that.

    :param fs: Sample rate, in hertz.
    :param seconds: Duration, in seconds.
    :param rms: RMS value of the signal, in whatever unit it is scaled to.
    :param seed: Seed for the noise generator; the same seed reproduces the
        same record.
    :return: The signal.
    """
    rate = require_count(fs, "fs")
    duration = require_positive(seconds, "seconds")
    level = require_positive(rms, "rms")
    if rate <= 2 * _BAND_LIMIT_HZ[1]:
        msg = f"'fs' must exceed {2 * _BAND_LIMIT_HZ[1]:g} Hz for the 6.5 kHz low-pass."
        raise ValueError(msg)
    n = round(duration * rate)
    if n < 1:
        msg = f"'seconds' of {duration:g} s is shorter than one sample at {rate} Hz."
        raise ValueError(msg)
    return _band_limited_noise(rate, n, level, seed)


def _zero_crossings(x: np.ndarray) -> np.ndarray:
    """Indices ``k`` where the record changes sign between ``k`` and ``k + 1``."""
    return np.flatnonzero((x[:-1] < 0.0) != (x[1:] < 0.0))


def _nearer_zero(x: np.ndarray, k: int) -> int:
    """Of the two samples either side of the crossing at ``k``, the smaller one."""
    return k + 1 if abs(float(x[k + 1])) < abs(float(x[k])) else k


def combi_signal(
    fs: int,
    *,
    sine_seconds: float = _COMBI_MIN_SINE_S,
    noise_seconds: float = _COMBI_MIN_NOISE_S,
    cycles: int = 1,
    seed: int | None = None,
) -> np.ndarray:
    r"""The combi signal of IEC 60118-4:2014 6.6 and Table 2.

    Bursts of a 1 kHz sine at an RMS of 1, with 5 ms rise and fall times,
    interleaved with the pink noise of 6.4 at an RMS 6 dB lower: the sine's
    peaks sit 3 dB below the maximum peak of noise of crest factor 4, as
    Table 2 notes (:math:`\sqrt{2}` against :math:`4 \times 10^{-6/20}`,
    -3,03 dB). Each burst lasts at least 1 s so that either meter settles,
    and the noise at least four times as long, so the amplifier runs cooler
    than on a steady sine while the level of the sine can still be read.
    Every transition is at a zero crossing: the bursts start and end on the
    sine's zeros, under their ramps, and each stretch of noise is cut at its
    own zero crossings.

    :param fs: Sample rate, in hertz.
    :param sine_seconds: Duration of each sine burst, at least 1 s; rounded to
        a whole number of periods.
    :param noise_seconds: Duration of each stretch of noise, at least 4 s and
        at least four times ``sine_seconds``. It grows to four times the
        sine burst when rounding the burst to whole periods has lengthened
        it, so the ratio of 4:1 is never reduced, and by the few samples it
        takes to end on a zero crossing.
    :param cycles: Number of burst-and-noise cycles.
    :param seed: Seed for the noise generator.
    :return: The signal, starting with a sine burst.
    """
    rate = require_count(fs, "fs")
    if rate <= 2 * _BAND_LIMIT_HZ[1]:
        msg = f"'fs' must exceed {2 * _BAND_LIMIT_HZ[1]:g} Hz for the 6.5 kHz low-pass."
        raise ValueError(msg)
    sine_s = require_finite(sine_seconds, "sine_seconds")
    noise_s = require_finite(noise_seconds, "noise_seconds")
    n_cycles = require_count(cycles, "cycles")
    if sine_s < _COMBI_MIN_SINE_S or noise_s < _COMBI_MIN_NOISE_S:
        msg = (
            "Table 2 sets at least 1 s of sine and at least 4 s of noise; got "
            f"{sine_s:g} s and {noise_s:g} s."
        )
        raise ValueError(msg)
    if noise_s < _COMBI_MIN_RATIO * sine_s:
        msg = (
            f"the noise has to last at least {_COMBI_MIN_RATIO:g} times the sine "
            f"(Table 2); got {noise_s:g} s against {sine_s:g} s."
        )
        raise ValueError(msg)
    periods = round(sine_s * _COMBI_FREQUENCY_HZ)
    n_sine = round(periods * rate / _COMBI_FREQUENCY_HZ)
    t = np.arange(n_sine, dtype=np.float64) / rate
    ramp = round(_COMBI_RAMP_S * rate)
    envelope = np.ones(n_sine)
    rise = 0.5 * (1.0 - np.cos(np.pi * np.arange(ramp) / ramp))
    envelope[:ramp] = rise
    envelope[n_sine - ramp :] = rise[::-1]
    burst = math.sqrt(2.0) * np.sin(2.0 * np.pi * _COMBI_FREQUENCY_HZ * t) * envelope

    # Table 2: "the ratio of 4:1 shall not be reduced", also once the sine has
    # been rounded to whole periods, which can lengthen it.
    n_noise = max(round(noise_s * rate), math.ceil(_COMBI_MIN_RATIO * n_sine))
    spare = round(0.02 * rate)
    noise_rms = 10.0 ** (_COMBI_NOISE_RELATIVE_DB / 20.0)
    noise = _band_limited_noise(rate, n_cycles * (n_noise + 2 * spare), noise_rms, seed)
    pieces: list[np.ndarray] = []
    for k in range(n_cycles):
        stretch = noise[k * (n_noise + 2 * spare) : (k + 1) * (n_noise + 2 * spare)]
        crossings = _zero_crossings(stretch)
        start = _nearer_zero(stretch, int(crossings[0]))
        after = crossings[crossings >= start + n_noise]
        stop = _nearer_zero(stretch, int(after[0])) + 1 if after.size else stretch.size
        pieces.extend((burst, stretch[start:stop]))
    return np.concatenate(pieces)


# ---------------------------------------------------------------------------
# Measurement points of small-volume systems
# ---------------------------------------------------------------------------


def small_volume_measurement_points(layout: str) -> np.ndarray:
    """The measurement points of a disabled refuge or a counter (clause 9 as amended).

    ``"refuge_small"`` is Figure 2 a), for a magnetic field source of small
    dimensions: along the perpendicular and plus or minus 45 degrees from it,
    at 300 mm and 500 mm from the reference point. ``"refuge_large"`` is
    Figure 2 b), for a larger source such as a vertical loop: three points on
    a row 424 mm wide at 300 mm from the reference line and three on a row
    700 mm wide 200 mm further. Both are taken at 1,2 m and 1,7 m (9.2).
    ``"counter"`` is Figure 3: on the semicircle of 300 mm radius around the
    reference point, at its bottom and 150 mm to either side, at 1,2 m,
    1,45 m and 1,7 m (9.3).

    Amendment 1 corrects the key of Figure 2 a): the outer radius is
    :math:`l_2 + l_3` = 500 mm, where the 2014 key printed ":math:`l_3` outer
    radius 200", smaller than the inner one (see ``docs/ERRATA.md``). The offset
    :math:`l_1` between the source and the reference is the installer's
    choice and is not part of the points.

    :param layout: ``"refuge_small"``, ``"refuge_large"`` or ``"counter"``.
    :return: The points, shape ``(heights, points, 3)``: :math:`x` across,
        :math:`y` away from the reference into the area where people stand,
        :math:`z` the height above the floor, all in metres.
    """
    name = require_choice(layout, "layout", tuple(_LAYOUT_HEIGHTS))
    plan = np.array(_PLAN_POINTS_M[name], dtype=np.float64)
    heights = _LAYOUT_HEIGHTS[name]
    points = np.empty((len(heights), plan.shape[0], 3), dtype=np.float64)
    for k, height in enumerate(heights):
        points[k, :, :2] = plan
        points[k, :, 2] = height
    return read_only(points)


# ---------------------------------------------------------------------------
# The magnetic background noise
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BackgroundNoiseAssessment(OwnsArrays):
    """The magnetic background noise of a site against 7.2 of IEC 60118-4:2014.

    The ratio, the category and the reporting duty are read from the noise
    levels and the 47 dB, 32 dB and 22 dB that 7.2 prints, so they are not
    fields: an assessment cannot be built to place a site in a class its
    noise does not reach.

    :ivar noise_levels_db: The A-weighted noise level at each point with the
        loop switched off, in dB re 400 mA/m.
    :ivar noise_is_tonal: Whether the noise was declared tonal and not mostly
        at low frequencies, which withholds the 22 dB relaxation.
    """

    noise_levels_db: np.ndarray
    noise_is_tonal: bool

    @property
    def reference_signal_to_noise_ratio_db(self) -> float:
        """The reference level less the noisiest point, in dB.

        The "reference signal-to-noise ratio" of 7.2: the levels are in dB re
        400 mA/m, the reference level, so the ratio is the loudest level with
        its sign changed.
        """
        return -float(np.max(self.noise_levels_db))

    @property
    def category(self) -> str:
        """The class 7.2 puts the site in.

        ``"ideal"`` (above 47 dB), ``"acceptable"`` (32 dB to 47 dB),
        ``"tolerable_for_short_periods"`` (22 dB to 32 dB, only for noise
        without an undesirable tonal quality or mostly at low frequencies) or
        ``"below_tolerable"``.
        """
        snr = self.reference_signal_to_noise_ratio_db
        if snr > _SNR_IDEAL_DB:
            return _NOISE_CATEGORIES[0]
        if snr >= _SNR_MINIMUM_DB:
            return _NOISE_CATEGORIES[1]
        if snr >= _SNR_SHORT_PERIODS_DB and not self.noise_is_tonal:
            return _NOISE_CATEGORIES[2]
        return _NOISE_CATEGORIES[3]

    @property
    def report_required(self) -> bool:
        """Whether the ratio is below 32 dB.

        7.2: such a ratio "shall be reported and agreed with the system
        operator".
        """
        return self.reference_signal_to_noise_ratio_db < _SNR_MINIMUM_DB

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the noise at each point against the 47, 32 and 22 dB lines.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the noise levels' ``Axes.plot``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_background_noise

        check_language(language)
        return plot_background_noise(self, ax, language=language, **kwargs)


def assess_background_noise(
    noise_levels_db: ArrayLike, *, noise_is_tonal: bool = False
) -> BackgroundNoiseAssessment:
    """How quiet is the site magnetically? (IEC 60118-4:2014 7.2).

    The magnetic background noise is measured A-weighted with the loop
    switched off, everything else normally in use on and dimmable lighting
    half-dimmed, at enough points of the intended volume, normally at 1,2 m
    for seated and 1,7 m for standing listeners (7.1). Its difference from the
    reference level, the reference signal-to-noise ratio, is taken at the
    noisiest point, because that is where a listener hears the most of it.

    7.2 sets no requirement, only recommendations: above 47 dB is the ideal for
    theatres and places where the aesthetic value of speech matters, 32 dB is
    the recommended minimum, and below it the ratio "shall be reported and
    agreed with the system operator". As low as 22 dB may be tolerable for
    short periods when the noise "has no significant undesirable tonal quality
    or is mostly at low frequencies"; ``noise_is_tonal=True`` declares that it
    does not, and withholds that relaxation.

    :param noise_levels_db: A-weighted noise level at each point, in dB re
        400 mA/m.
    :param noise_is_tonal: The noise has a significant undesirable tonal
        quality and is not mostly at low frequencies.
    :return: A :class:`BackgroundNoiseAssessment`.
    """
    levels = require_finite_array(noise_levels_db, "noise_levels_db")
    return BackgroundNoiseAssessment(
        noise_levels_db=levels, noise_is_tonal=bool(noise_is_tonal)
    )


# ---------------------------------------------------------------------------
# The verdicts on an installed system
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LoopRequirement(RichDisplay):
    """One requirement of IEC 60118-4:2014, judged on every value it covers.

    Each judged value has its own lower and upper limit (minus or plus
    infinity where the requirement sets none), because the system-noise limit
    of 10.4.7 can differ from point to point.

    :ivar name: ``"field_strength"`` (8.4.3), ``"field_strength_reached"``
        (8.2.7, or 9.5 for a small volume), ``"frequency_response"``
        (8.3.7), ``"system_noise"`` (10.4.7), ``"field_strength_range"`` or
        ``"standing_area"`` (9.5).
    :ivar clause: The subclause that states it, as amended.
    :ivar values_db: The judged values, in dB.
    :ivar lower_db: The lower limit of each, in dB.
    :ivar upper_db: The upper limit of each, in dB.
    """

    name: str
    clause: str
    values_db: tuple[float, ...]
    lower_db: tuple[float, ...]
    upper_db: tuple[float, ...]

    @property
    def margins_db(self) -> tuple[float, ...]:
        """How far inside its limits each value lies, in dB (negative outside).

        Each margin is settled to nine decimal places, a nanodecibel, so that a
        value on a limit reached through floating-point arithmetic is on it: a
        response of -18,6 dB against -15,6 dB at 1 kHz has a margin of 0 dB,
        not -0,000 000 000 000 001 8 dB.
        """
        # Adding 0.0 turns the -0.0 a settled rounding error leaves into 0.0.
        return tuple(
            float(settled(min(value - low, high - value))) + 0.0
            for value, low, high in zip(
                self.values_db, self.lower_db, self.upper_db, strict=True
            )
        )

    @property
    def worst_margin_db(self) -> float:
        """The smallest margin, in dB: negative when the requirement fails."""
        return min(self.margins_db)

    @property
    def passes(self) -> bool:
        """Whether every value lies within its limits, both inclusive.

        Judged on the settled :attr:`margins_db`, so an edge reached from
        decimal readings passes.
        """
        return bool(self.values_db) and all(
            is_at_most(0.0, margin) for margin in self.margins_db
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a LoopRequirement has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw each judged value against its limits.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the values' ``Axes.plot``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_loop_requirement

        check_language(language)
        return plot_loop_requirement(self, ax, language=language, **kwargs)


@dataclass(frozen=True)
class InductionLoopVerification(RichDisplay):
    """The IEC 60118-4:2014 verdict on an installed induction-loop system.

    :ivar clause: ``"8"`` for a system judged on its useful magnetic field
        volume, ``"9"`` for a small-volume system as amended.
    :ivar layout: ``"useful_volume"`` for clause 8, or the small-volume
        layout (``"refuge_small"``, ``"refuge_large"``, ``"counter"``,
        ``"refuge_useful_volume"``, ``"counter_useful_volume"``).
    :ivar requirements: One :class:`LoopRequirement` per requirement
        measured.
    :ivar background_noise: The 7.2 assessment of the site, when the noise
        with the loop off was given; a recommendation, so not part of
        :attr:`passes`.
    """

    clause: str
    layout: str
    requirements: tuple[LoopRequirement, ...]
    background_noise: BackgroundNoiseAssessment | None = None

    @property
    def passes(self) -> bool:
        """Whether every requirement measured is met; ``False`` when none was."""
        return bool(self.requirements) and all(r.passes for r in self.requirements)

    @property
    def failed(self) -> tuple[str, ...]:
        """The names of the requirements that are not met."""
        return tuple(r.name for r in self.requirements if not r.passes)

    def requirement(self, name: str) -> LoopRequirement:
        """The verdict on one requirement.

        :param name: Its :attr:`LoopRequirement.name`.
        :return: The :class:`LoopRequirement`.
        :raises KeyError: when that requirement was not judged.
        """
        for requirement in self.requirements:
            if requirement.name == name:
                return requirement
        msg = f"'{name}' was not judged; judged: {[r.name for r in self.requirements]}"
        raise KeyError(msg)

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "an InductionLoopVerification has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the worst margin of every requirement as a bar.

        A requirement is met when its bar stands at or above zero.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the bars' ``Axes.bar``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_induction_loop_verification

        check_language(language)
        return plot_induction_loop_verification(self, ax, language=language, **kwargs)


def _levels(values: ArrayLike, name: str) -> np.ndarray:
    """A non-empty array of finite, real levels, of any shape."""
    arr = _as_float64(values, name)
    if arr.size == 0 or not np.all(np.isfinite(arr)):
        msg = f"'{name}' must be a non-empty array of finite levels."
        raise ValueError(msg)
    return arr


def _band_requirement(
    name: str, clause: str, values: np.ndarray, low: float, high: float
) -> LoopRequirement:
    """A requirement with the same limits for every value."""
    flat = tuple(float(v) for v in values.ravel())
    return LoopRequirement(
        name=name,
        clause=clause,
        values_db=flat,
        lower_db=(low,) * len(flat),
        upper_db=(high,) * len(flat),
    )


def _frequency_response_requirement(
    frequencies_hz: ArrayLike, response_db: ArrayLike
) -> LoopRequirement:
    """The 8.3.7 requirement on responses measured at one or more points."""
    f = require_positive_array(frequencies_hz, "frequencies_hz")
    response = np.atleast_2d(_levels(response_db, "response_db"))
    if response.ndim != _POINTS_BY_FREQUENCIES or response.shape[1] != f.size:
        msg = (
            "'response_db' must hold one value per frequency, for one point or "
            "for each point (shape (points, frequencies))."
        )
        raise ValueError(msg)
    for required in _REQUIRED_RESPONSE_FREQUENCIES_HZ:
        if not np.any(np.isclose(f, required, rtol=_FREQUENCY_MATCH_RTOL, atol=0.0)):
            msg = (
                f"the frequency response has to be measured at least at 100 Hz, "
                f"1 kHz and 5 kHz (8.3.3, 8.3.4); {required:g} Hz is missing."
            )
            raise ValueError(msg)
    ref = _reference_index(f, "frequencies_hz")
    low, high = _RESPONSE_BAND_HZ
    inside = (f >= low * (1.0 - _FREQUENCY_MATCH_RTOL)) & (
        f <= high * (1.0 + _FREQUENCY_MATCH_RTOL)
    )
    relative = response - response[:, [ref]]
    return _band_requirement(
        "frequency_response",
        "8.3.7",
        relative[:, inside],
        -_RESPONSE_TOLERANCE_DB,
        _RESPONSE_TOLERANCE_DB,
    )


def verify_induction_loop_system(
    field_strength_levels_db: ArrayLike,
    *,
    specified_level_db: float = 0.0,
    frequencies_hz: ArrayLike | None = None,
    response_db: ArrayLike | None = None,
    background_noise_levels_db: ArrayLike | None = None,
    system_noise_levels_db: ArrayLike | None = None,
    noise_is_tonal: bool = False,
) -> InductionLoopVerification:
    """Does an installed loop meet IEC 60118-4:2014 over its useful volume?

    The requirements of clause 8 and of 10.4 as amended, on the measurements an
    installer makes at the selected points of the useful magnetic field volume,
    normally at 1,2 m for seated and 1,7 m for standing listeners (8.4.2):

    * ``"field_strength"`` (8.4.3): every level within plus or minus 3 dB of
      the level specified according to 8.2.7, which is 400 mA/m, 0 dB, with a
      1 kHz sine or the combi signal and the true-RMS meter. Measured with
      another signal or meter, the specified level is the reading the
      manufacturer states for 400 mA/m (Table 3 gives -6 dB for pink noise on
      the RMS meter), passed as ``specified_level_db``;
    * ``"field_strength_reached"`` (8.2.7): the maximum value of the field is
      400 mA/m "at one point, at least, within the useful magnetic field
      volume" (8.2.1), so the highest level reaches the specified one. A
      spread that sits within its window but wholly below the reference, set
      too low, fails here;
    * ``"frequency_response"`` (8.3.7): at every point, within plus or minus
      3 dB of the response at 1 kHz from 100 Hz to 5 000 Hz, measured at least
      at 100 Hz, 1 kHz and 5 kHz. The response is the field spectrum less the
      source spectrum (8.3.2 d), or the field at each sine frequency;
    * ``"system_noise"`` (10.4.7, which was 10.2.7 before Amendment 1): the
      A-weighted level with the system on and every input muted. The site's
      reference signal-to-noise ratio is taken at the noisiest point with the
      system off. Above 47 dB, no point may exceed -47 dB; otherwise no point
      may exceed its own level with the system off by more than 1 dB, so the
      two sets of levels are paired point by point. 10.4.7 prints "greater
      than 47 dB" and "less than 47 dB", so a ratio of exactly 47 dB falls in
      neither sentence; the 1 dB rule is applied there, since 7.2 calls only
      a ratio above 47 dB ideal (see ``docs/ERRATA.md``).

    Every requirement is judged on what was given; one not measured is not
    judged, and a verdict with none fails. The background noise with the loop
    off is also assessed against the recommendations of 7.2
    (:func:`assess_background_noise`), which are not requirements.

    :param field_strength_levels_db: The field strength level at each
        selected point, in dB re 400 mA/m.
    :param specified_level_db: The level specified according to 8.2.7 for the
        signal and meter used, in dB re 400 mA/m.
    :param frequencies_hz: The frequencies of the response, in hertz,
        including 100 Hz, 1 kHz and 5 kHz.
    :param response_db: The response at each frequency, in dB on any fixed
        reference, for one point or one row per point.
    :param background_noise_levels_db: The A-weighted level at each point with
        the loop switched off, in dB re 400 mA/m.
    :param system_noise_levels_db: The A-weighted level at the same points
        with the system on and every input muted, in dB re 400 mA/m.
    :param noise_is_tonal: The background noise has a significant undesirable
        tonal quality and is not mostly at low frequencies, which withholds
        the 22 dB relaxation of 7.2 (:func:`assess_background_noise`).
    :return: An :class:`InductionLoopVerification`.
    """
    levels = _levels(field_strength_levels_db, "field_strength_levels_db")
    specified = require_finite(specified_level_db, "specified_level_db")
    requirements = [
        _band_requirement(
            "field_strength",
            "8.4.3",
            levels,
            specified - _FIELD_TOLERANCE_DB,
            specified + _FIELD_TOLERANCE_DB,
        ),
        _band_requirement(
            "field_strength_reached",
            "8.2.7",
            np.array([np.max(levels)]),
            specified,
            math.inf,
        ),
    ]
    if (frequencies_hz is None) != (response_db is None):
        msg = "'frequencies_hz' and 'response_db' go together."
        raise ValueError(msg)
    if frequencies_hz is not None and response_db is not None:
        requirements.append(
            _frequency_response_requirement(frequencies_hz, response_db)
        )
    background = None
    if background_noise_levels_db is not None:
        background = assess_background_noise(
            background_noise_levels_db, noise_is_tonal=noise_is_tonal
        )
    if system_noise_levels_db is not None:
        if background is None:
            msg = (
                "'system_noise_levels_db' is judged against the noise with the "
                "system off (10.4.7); give 'background_noise_levels_db' too."
            )
            raise ValueError(msg)
        on = require_finite_array(system_noise_levels_db, "system_noise_levels_db")
        off = background.noise_levels_db
        if on.size != off.size:
            msg = (
                "'system_noise_levels_db' and 'background_noise_levels_db' are "
                "paired point by point and must have the same length."
            )
            raise ValueError(msg)
        if background.reference_signal_to_noise_ratio_db > _SNR_IDEAL_DB:
            upper = (_SYSTEM_NOISE_CEILING_DB,) * on.size
        else:
            upper = tuple(float(v) + _SYSTEM_NOISE_RISE_DB for v in off)
        requirements.append(
            LoopRequirement(
                name="system_noise",
                clause="10.4.7",
                values_db=tuple(float(v) for v in on),
                lower_db=(-math.inf,) * on.size,
                upper_db=upper,
            )
        )
    return InductionLoopVerification(
        clause="8",
        layout="useful_volume",
        requirements=tuple(requirements),
        background_noise=background,
    )


def _height_coverage(
    levels: np.ndarray, heights_m: ArrayLike | None, name: str
) -> None:
    """Refuse a useful volume of 9.4 that leaves out a height of 9.2 or 9.3.

    9.4 as amended asks, as a minimum, for the requirements to be met at one
    position at least at each of the heights defined in 9.2 and 9.3. Every
    point is judged against 9.5 anyway, so the minimum is that the
    representative points include one at each of those heights.
    """
    if heights_m is None:
        msg = (
            f"the '{name}' layout needs 'heights_m', the height of each point: "
            "9.4 asks for one position at least at each height of 9.2 or 9.3."
        )
        raise ValueError(msg)
    heights = _as_float64(heights_m, "heights_m")
    if not np.all(np.isfinite(heights)):
        msg = "'heights_m' must hold finite heights."
        raise ValueError(msg)
    if heights.shape != levels.shape:
        msg = (
            f"'heights_m' holds the height of each point and must have the shape "
            f"of 'field_strength_levels_db', {levels.shape}; got {heights.shape}."
        )
        raise ValueError(msg)
    required = _USEFUL_VOLUME_HEIGHTS[name]
    missing = [
        h for h in required if not np.any(np.abs(heights - h) <= _HEIGHT_MATCH_M)
    ]
    if missing:
        clause = "9.2" if name == "refuge_useful_volume" else "9.3"
        msg = (
            f"9.4 needs one position at least at each height of {clause} "
            f"({', '.join(f'{h:g} m' for h in required)}); none is at "
            f"{', '.join(f'{h:g} m' for h in missing)}."
        )
        raise ValueError(msg)


def verify_small_volume_system(
    field_strength_levels_db: ArrayLike,
    *,
    layout: str,
    heights_m: ArrayLike | None = None,
    standing_area_levels_db: ArrayLike | None = None,
    frequencies_hz: ArrayLike | None = None,
    response_db: ArrayLike | None = None,
) -> InductionLoopVerification:
    """Does a refuge, call-point or counter loop meet clause 9 as amended?

    The requirements of 9.5 as Amendment 1 writes them, at the measurement
    points of Figure 2 (a refuge) or Figure 3 (a counter), or at the
    representative points of a useful magnetic field volume agreed by contract
    in their place (9.4):

    * ``"field_strength_range"``: at every point within plus or minus 6 dB of
      400 mA/m, measured according to 8.2;
    * ``"field_strength_reached"``: at one point at least, 0 dB or more;
    * ``"standing_area"``: nowhere in the area where people are expected to
      stand above +8 dB, judged on the measurement points and on any survey
      of that area given as ``standing_area_levels_db``;
    * ``"frequency_response"``: 8.3.7 at every point.

    A useful volume replaces the points of 9.2 (``"refuge_useful_volume"``)
    or of 9.3 (``"counter_useful_volume"``), and 9.4 asks it, as a minimum, to
    meet the requirements at one position at least at each height of the
    clause it replaces: 1,2 m and 1,7 m for a refuge, and 1,2 m, 1,45 m and
    1,7 m for a counter. Every point is held to 9.5 all the same, so the
    minimum comes down to the points including each of those heights, and
    ``heights_m`` says which height each point was taken at.

    The informative Annex A.4 allows up to +12 dB at 1,45 m for a counter;
    9.5 does not, and 9.5 is what is applied (see ``docs/ERRATA.md``).

    :param field_strength_levels_db: The level at each measurement point, in
        dB re 400 mA/m: shape ``(heights, points)`` for a layout of Figures 2
        and 3, ``(2, 6)`` for a refuge and ``(3, 3)`` for a counter, in the
        order of :func:`small_volume_measurement_points`; any shape for a
        useful volume.
    :param layout: ``"refuge_small"``, ``"refuge_large"`` or ``"counter"``
        for the points of Figures 2 and 3; ``"refuge_useful_volume"`` or
        ``"counter_useful_volume"`` for a useful volume of 9.4 in their place.
    :param heights_m: The height of each point of a useful volume above the
        floor, in metres, in the shape of ``field_strength_levels_db``;
        required for a useful volume, and refused for the fixed layouts,
        whose heights are those of Figures 2 and 3.
    :param standing_area_levels_db: Levels surveyed elsewhere in the area
        where people are expected to stand, in dB re 400 mA/m.
    :param frequencies_hz: The frequencies of the response, in hertz,
        including 100 Hz, 1 kHz and 5 kHz.
    :param response_db: The response at each frequency, one row per point.
    :return: An :class:`InductionLoopVerification`.
    :raises ValueError: for a fixed layout's levels of the wrong shape, or a
        useful volume without a point at a height of 9.2 or 9.3.
    """
    name = require_choice(layout, "layout", _SMALL_VOLUME_LAYOUTS)
    levels = _levels(field_strength_levels_db, "field_strength_levels_db")
    if name in _LAYOUT_HEIGHTS:
        if heights_m is not None:
            msg = (
                f"the '{name}' layout is measured at the heights of Figures 2 and 3; "
                "'heights_m' belongs to a useful volume."
            )
            raise ValueError(msg)
        expected = (len(_LAYOUT_HEIGHTS[name]), len(_PLAN_POINTS_M[name]))
        if levels.shape != expected:
            msg = (
                f"the '{name}' layout is measured at {expected[1]} points at each of "
                f"{expected[0]} heights: 'field_strength_levels_db' must have shape "
                f"{expected}, got {levels.shape}."
            )
            raise ValueError(msg)
    else:
        _height_coverage(levels, heights_m, name)
    requirements = [
        _band_requirement(
            "field_strength_range",
            "9.5",
            levels,
            -_SMALL_VOLUME_RANGE_DB,
            _SMALL_VOLUME_RANGE_DB,
        ),
        _band_requirement(
            "field_strength_reached", "9.5", np.array([np.max(levels)]), 0.0, math.inf
        ),
    ]
    standing = levels.ravel()
    if standing_area_levels_db is not None:
        standing = np.concatenate(
            [
                standing,
                _levels(standing_area_levels_db, "standing_area_levels_db").ravel(),
            ]
        )
    requirements.append(
        _band_requirement(
            "standing_area", "9.5", standing, -math.inf, _STANDING_AREA_MAX_DB
        )
    )
    if (frequencies_hz is None) != (response_db is None):
        msg = "'frequencies_hz' and 'response_db' go together."
        raise ValueError(msg)
    if frequencies_hz is not None and response_db is not None:
        requirements.append(
            _frequency_response_requirement(frequencies_hz, response_db)
        )
    return InductionLoopVerification(
        clause="9", layout=name, requirements=tuple(requirements)
    )


# ---------------------------------------------------------------------------
# The overload test of 10.3 as amended
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OverloadTestFrequency(RichDisplay):
    """One row of Table 4 of IEC 60118-4:2014/A1:2017.

    :ivar programme: The typical programme material of the system.
    :ivar power_bandwidth_limit_hz: The upper limit of the maximum power
        bandwidth it needs, in hertz.
    :ivar test_frequency_hz: The frequency the overload test is run to, about
        twice that limit, in hertz.
    """

    programme: str
    power_bandwidth_limit_hz: float
    test_frequency_hz: float


#: Table 4 of IEC 60118-4:2014/A1:2017, "Programme material and test
#: frequency": speech for transient use such as small-volume systems, speech
#: (the default) and music. The test runs at about twice the upper limit of the
#: maximum power bandwidth, with the level 7 dB down, which loads the power
#: supply the way real programme does (10.3.1).
OVERLOAD_TEST_FREQUENCIES: Mapping[str, OverloadTestFrequency] = MappingProxyType(
    {
        "transient_speech": OverloadTestFrequency(
            programme="speech for transient use, for example small-volume systems",
            power_bandwidth_limit_hz=1250.0,
            test_frequency_hz=2500.0,
        ),
        "speech": OverloadTestFrequency(
            programme="speech (default)",
            power_bandwidth_limit_hz=1600.0,
            test_frequency_hz=3150.0,
        ),
        "music": OverloadTestFrequency(
            programme="music",
            power_bandwidth_limit_hz=2000.0,
            test_frequency_hz=4000.0,
        ),
    }
)


@dataclass(frozen=True)
class AmplifierOverloadVerification(OwnsArrays):
    """The overload test of 10.3 as amended, judged on the compliance voltage.

    10.3.3 as amended asks for no clipping "a la frecuencia de ensayo
    especificada en la tabla 4 y al nivel especificado en el apartado 10.3.2",
    so the verdict is taken at the Table 4 frequency, which the sweep always
    reaches. Where the voltage doubles above that frequency, 10.3.2 carries the
    sweep on to the doubling; the voltage there is drawn and kept in
    :attr:`max_voltage_v`, and 10.3.3 does not judge it.

    :ivar programme: The row of Table 4 the test used.
    :ivar test_current_a: The loop current at 1 kHz, 7 dB below the one that
        gives the required field, in amperes.
    :ivar doubling_frequency_hz: Where the loop voltage first reaches twice
        its value at 1 kHz, in hertz; infinite when it does not double below
        20 kHz (or below the top of the given current response).
    :ivar end_frequency_hz: Where the sweep ends: the higher of the doubling
        frequency and the Table 4 frequency, in hertz.
    :ivar frequencies_hz: The sweep from 1 kHz to its end, in hertz.
    :ivar voltage_v: The RMS loop voltage along it, in volts.
    :ivar test_frequency_voltage_v: The RMS loop voltage at the frequency of
        Table 4, where 10.3.3 judges the test, in volts.
    :ivar compliance_voltage_v: The amplifier's compliance voltage (IEC
        62489-1:2010 5.4.8), in volts.
    """

    programme: OverloadTestFrequency
    test_current_a: float
    doubling_frequency_hz: float
    end_frequency_hz: float
    frequencies_hz: np.ndarray
    voltage_v: np.ndarray
    test_frequency_voltage_v: float
    compliance_voltage_v: float

    @property
    def max_voltage_v(self) -> float:
        """The highest loop voltage of the whole sweep, in volts.

        Higher than :attr:`test_frequency_voltage_v` when the sweep runs on
        past the Table 4 frequency to the doubling; 10.3.3 does not judge it.
        """
        return float(np.max(self.voltage_v))

    @property
    def headroom_db(self) -> float:
        """The compliance voltage over the voltage at the Table 4 frequency, in dB."""
        return 20.0 * math.log10(
            self.compliance_voltage_v / self.test_frequency_voltage_v
        )

    @property
    def passes(self) -> bool:
        """Whether the voltage at the Table 4 frequency is within compliance (10.3.3)."""
        return is_at_most(self.test_frequency_voltage_v, self.compliance_voltage_v)

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "an AmplifierOverloadVerification has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the loop voltage along the sweep against the compliance voltage.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the voltage curve's ``Axes.plot``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_amplifier_overload

        check_language(language)
        return plot_amplifier_overload(self, ax, language=language, **kwargs)


def verify_amplifier_overload(
    required_current_a: float,
    impedance: LoopImpedance,
    compliance_voltage_v: float,
    *,
    programme: str = "speech",
    current_response: AmplifierFrequencyResponse | None = None,
) -> AmplifierOverloadVerification:
    r"""Does the amplifier clip in the overload test of 10.3 as amended?

    10.3.2 as amended: a 1 kHz sine is set 7 dB below the field required at a
    point, the voltage across the loop is measured, and the frequency is
    raised at the same input until that voltage doubles or the frequency of
    Table 4 is reached, whichever is the higher frequency. No clipping may
    appear at the frequency of Table 4 and the level of 10.3.2 (10.3.3), and
    that is where the verdict is taken; the rest of the sweep is drawn and
    its highest voltage kept, but not judged. Of the three ways to detect
    clipping the amendment lists,
    the second compares the loop voltage with the amplifier's compliance
    voltage of IEC 62489-1, and that is the one computed here: the loop is a
    series resistance and inductance, and the current follows the amplifier's
    frequency response into it, which is where a correction for metal loss
    shows (10.3.1).

    The sweep looks for the first frequency where the voltage doubles, up to
    20 kHz, the top of the audio band, or up to the highest frequency of the
    given current response; a loop that is mostly resistive and flat may not
    double at all, and then the test ends at the Table 4 frequency. A current
    response that peaks and falls again, as a correction for metal loss can,
    may double the voltage and then bring it back below twice its start; the
    sweep stops at that first doubling. It is found exactly: the response is
    read log-linearly between its measured frequencies, and between two of
    them the logarithm of the voltage, a straight line in the logarithm of
    frequency plus :math:`\tfrac{1}{2}\ln(R^2 + (2\pi f L)^2)`, is convex in
    it, so the voltage crosses twice its start at most once going up in each
    interval, and the first interval whose upper end has doubled holds the
    first doubling.

    :param required_current_a: The RMS loop current at 1 kHz that gives the
        required field strength at the chosen point, in amperes.
    :param impedance: The loop's :class:`LoopImpedance`
        (:func:`~phonometry.electroacoustics.induction_loop_components.loop_impedance`).
    :param compliance_voltage_v: The amplifier's compliance voltage, in
        volts (:func:`~phonometry.electroacoustics.induction_loop_components.compliance_voltage`).
    :param programme: The row of :data:`OVERLOAD_TEST_FREQUENCIES`:
        ``"transient_speech"``, ``"speech"`` (the default of Table 4) or
        ``"music"``.
    :param current_response: The amplifier's current response into the loop,
        relative to 1 kHz (:func:`~phonometry.electroacoustics.induction_loop_components.amplifier_frequency_response`);
        ``None`` for a flat current, which is what a current-drive amplifier
        delivers (E.3).
    :return: An :class:`AmplifierOverloadVerification`.
    """
    required = require_positive(required_current_a, "required_current_a")
    compliance = require_positive(compliance_voltage_v, "compliance_voltage_v")
    row = OVERLOAD_TEST_FREQUENCIES[
        require_choice(programme, "programme", tuple(OVERLOAD_TEST_FREQUENCIES))
    ]
    test_current = required * 10.0 ** (_OVERLOAD_TEST_OFFSET_DB / 20.0)
    top = _OVERLOAD_SWEEP_LIMIT_HZ
    if current_response is not None:
        top = float(current_response.frequencies_hz[-1])
        if top < row.test_frequency_hz:
            msg = (
                f"the current response stops at {top:g} Hz, below the "
                f"{row.test_frequency_hz:g} Hz of Table 4."
            )
            raise ValueError(msg)

    def voltage(f: float | np.ndarray) -> np.ndarray:
        gain = (
            np.ones_like(np.asarray(f, dtype=np.float64))
            if current_response is None
            else 10.0 ** (current_response.at(f) / 20.0)
        )
        return np.asarray(test_current * gain * impedance.at(f))

    start = float(voltage(_OVERLOAD_START_HZ))
    target = _OVERLOAD_VOLTAGE_FACTOR * start
    breaks = [_OVERLOAD_START_HZ, top]
    if current_response is not None:
        breaks[1:1] = [
            float(f)
            for f in current_response.frequencies_hz
            if _OVERLOAD_START_HZ < f < top
        ]
    doubling = math.inf
    for low, high in itertools.pairwise(breaks):
        if float(voltage(high)) >= target:
            doubling = float(
                optimize.brentq(
                    lambda f: float(voltage(f)) - target,
                    low,
                    high,
                    xtol=1e-9,
                    rtol=1e-12,
                )
            )
            break
    end = (
        max(row.test_frequency_hz, doubling)
        if math.isfinite(doubling)
        else row.test_frequency_hz
    )
    grid = np.exp(
        np.linspace(math.log(_OVERLOAD_START_HZ), math.log(end), _OVERLOAD_POINTS)
    )
    return AmplifierOverloadVerification(
        programme=row,
        test_current_a=test_current,
        doubling_frequency_hz=doubling,
        end_frequency_hz=end,
        frequencies_hz=read_only(grid),
        voltage_v=read_only(np.asarray(voltage(grid), dtype=np.float64)),
        test_frequency_voltage_v=float(voltage(row.test_frequency_hz)),
        compliance_voltage_v=compliance,
    )
