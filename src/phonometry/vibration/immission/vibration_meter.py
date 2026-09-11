#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The vibration meter of DIN 45669-1:2010-09 (with Corrigendum 1:2012-12).

German immission control judges vibration in buildings with two standards that
print thresholds and say almost nothing about how the number reaching them was
formed: DIN 4150-2 for people in buildings and DIN 4150-3 for the buildings
themselves. DIN 45669-1 is the missing half. It defines the instrument, and
with it the quantities those thresholds are compared against, as exact
transfer functions and exact time weightings, then grades a real meter against
them.

**The chain.** A velocity signal is band-limited (5.2.3.2, Formula (3)), which
is two Butterworth pairs: a two-pole high pass at :math:`0{,}8 f_u` and a
two-pole low pass at :math:`f_o / 0{,}8`. The working range is
:math:`f_u = 1` Hz to :math:`f_o = 80` Hz for buildings, and 4 Hz to 315 Hz
next to a railway, which is where DIN 45672-1 works. Frequency weighting
(Formula (4)) divides that by :math:`1 - \mathrm{j}\,5{,}6\,\mathrm{Hz}/f`,
one more pole and one more zero, and normalising by 1 mm/s turns the result
into the dimensionless **KB signal**. Its running r.m.s. with
:math:`\tau = 0{,}125` s (Formula (1)) is :math:`KB_F(t)`, the *weighted
vibration severity*, and the quantities a meter displays are its maximum
:math:`KB_{F\mathrm{max}}`, the maximum within each 30 s clock interval
(*Takt*) and the r.m.s. of those clock maxima :math:`KB_{FTm}` (Formula (2)).

**Two rules of Formula (2) that are easy to miss.** A clock maximum at or
below 0,1 enters the sum as zero but still counts in :math:`N`, so a quiet
interval lowers the average rather than being dropped from it; and a clock
interval that the measurement did not fill does not count at all (5.1.6.4), so
the averaging time is always a whole number of clock intervals.

**What Annex E adds.** DIN 4150-3 compares a peak velocity with a guideline
value that depends on frequency, so it needs a dominant frequency, and Annex D
shows two ways of finding one that do not agree. Annex E removes the question:
three weighting filters, one per building class of DIN 4150-3:1999-02 Table 1,
each the inverse of that class's guideline curve normalised to its 1 Hz to
10 Hz value. Filter the velocity with one of them and the peak of what comes
out, the *assessment velocity* :math:`v_{Bn}`, is compared with a single
number that no longer depends on frequency: 20, 5 or 3 mm/s (Table E.2). The
filters are specified as a target magnitude with a :math:`\pm 5` % band and a
linear phase, which is why this module designs them as symmetric FIRs.

**Where the printed check values come from, and where one of them does not.**
Table 9 (folio 35) prints what a meter must display for a 1 mm/s sine at five
frequencies, and its :math:`KB_F`, :math:`KB_{F\mathrm{max}}` and
:math:`KB_{FTm}` rows are reproduced by this module to the three decimals they
are printed with, ripple and all. Its :math:`|v|_\mathrm{max}` row is not, and
cannot be: at 31,5 Hz it prints 1,000 where Formula (5) gives 0,995, and at
315 Hz it prints 0,249 where Formula (5) gives 0,100, while the
:math:`KB_F` row of the same column follows Formula (5) at both. The table
contradicts itself rather than the formula, so :data:`KB_TEST_INDICATIONS`
carries the rows that agree with it and the other row is left to
``docs/ERRATA.md``.

**What a verdict here is and is not.** :func:`verify_vibration_meter` grades
one thing, the amplitude response against Tables 2 and 3, which is Clause
5.2.3.3 of a standard whose Clause 6 also asks for linearity, overload,
crest-factor handling, temperature, humidity and electromagnetic tests on
hardware. Passing here is necessary for conformity and is not conformity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
from scipy import signal as sig

from ..._internal.validation import (
    require_choice,
    require_equal_shapes,
    require_finite_array,
    require_positive,
    require_positive_array,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "ASSESSMENT_GUIDE_VALUES_MM_S",
    "ASSESSMENT_WEIGHTING_TOLERANCE",
    "BAND_LIMIT_CORNER_FACTOR",
    "KB_DETECTION_LIMIT",
    "VELOCITY_DETECTION_LIMIT_MM_S",
    "KB_INDICATION_TOLERANCE_PERCENT",
    "KB_CORNER_HZ",
    "KB_TIME_CONSTANT_S",
    "RESPONSE_TOLERANCE_LOWER_PERCENT",
    "KB_PULSE_RESPONSE_PERCENT",
    "KB_REFERENCE_FREQUENCY_HZ",
    "KB_REFERENCE_INDICATIONS",
    "TAKT_DURATION_S",
    "TAKT_SUPPRESSION_THRESHOLD",
    "KB_TEST_INDICATIONS",
    "RESPONSE_TOLERANCE_UPPER_PERCENT",
    "WORKING_RANGES_HZ",
    "AssessmentVelocity",
    "DominantFrequency",
    "VibrationMeterReading",
    "VibrationMeterVerification",
    "assess_short_term_vibration",
    "assessment_velocity",
    "assessment_weighting_response",
    "assessment_weighting_taps",
    "band_limitation_response",
    "dominant_frequency",
    "kb_signal",
    "kbf_signal",
    "kb_weighting_response",
    "measure_vibration_immission",
    "response_tolerance_percent",
    "takt_maxima",
    "takt_maximum_rms",
    "verify_vibration_meter",
]

#: The corner of the frequency weighting, in hertz: Formula (4) divides the
#: band-limited response by ``1 - j 5,6 Hz / f``, which is the pole that turns
#: a velocity signal into the KB signal.
KB_CORNER_HZ: float = 5.6

#: The time constant of the running r.m.s. of Formula (1), in seconds. It is
#: the "Fast" of a sound level meter, and 3.10.1.2 says why it is the one:
#: DIN 4150-2 judges the effect on people with it, and the fluctuating
#: indication it gives below 5 Hz was taken into account when those judging
#: criteria were set.
KB_TIME_CONSTANT_S: float = 0.125

#: The clock interval (*Takt*) of the clock maximum, in seconds (5.1.6.4,
#: following DIN 4150-2).
TAKT_DURATION_S: float = 30.0

#: Formula (2): a clock maximum at or below this value enters the sum as zero,
#: and its interval still counts in ``N``.
TAKT_SUPPRESSION_THRESHOLD: float = 0.1

#: The factor between a band limit of the working range and the corner of the
#: filter that makes it (5.2.3.2): the high pass sits at ``0,8 f_u`` and the
#: low pass at ``f_o / 0,8``, so 1 Hz to 80 Hz is made by corners at 0,8 Hz
#: and 100 Hz.
BAND_LIMIT_CORNER_FACTOR: float = 0.8

#: The two working ranges of 5.2.3.1, as ``(f_u, f_o)`` in hertz.
#: ``"building"`` is the range the standard is written for and ``"railway"``
#: the one 5.2.3.1 sends to DIN 45672-1, which blasting work and structure-borne
#: sound also need.
WORKING_RANGES_HZ: dict[str, tuple[float, float]] = {
    "building": (1.0, 80.0),
    "railway": (4.0, 315.0),
}

#: The reference frequency of the reference conditions (5.2.10), in hertz. The
#: input there is a 1 mm/s sine with at most 2 % distortion.
KB_REFERENCE_FREQUENCY_HZ: float = 16.0

#: What a meter must display under the reference conditions (6.2.3.12). The
#: peak is the amplitude of the input, the r.m.s. quantities are the KB signal
#: at 16 Hz, and ``kbf_max`` is higher than ``kbf`` because the running r.m.s.
#: of a sine ripples (Annex B).
KB_REFERENCE_INDICATIONS: dict[str, float] = {
    "peak_velocity_mm_s": 1.00,
    "kbf": 0.667,
    "kbf_max": 0.680,
    "kbf_takt_rms": 0.680,
}

#: The largest deviation allowed from :data:`KB_REFERENCE_INDICATIONS`, in per
#: cent (6.2.3.12).
KB_INDICATION_TOLERANCE_PERCENT: float = 4.0

#: The detection limit of 5.2.2: a meter resolves a peak velocity at least
#: this small, in millimetres per second.
VELOCITY_DETECTION_LIMIT_MM_S: float = 0.05

#: The detection limit of 5.2.2 for the weighted vibration severity, which is
#: dimensionless.
KB_DETECTION_LIMIT: float = 0.02

#: Table 2, the lower limit of the amplitude response deviation ``F(f)`` of
#: Formula (7), in per cent, as ``(lower factor, upper factor, limit)`` bands
#: of the working range. A band is entered as ``lower * f_u <= f`` and
#: ``f <= upper * f_o`` where the factor applies to the limit it is written
#: against; outside all of them the standard stops constraining the response
#: from below, which is what 100 % means.
RESPONSE_TOLERANCE_LOWER_PERCENT: tuple[tuple[float, float, float], ...] = (
    (1.25, 0.8, 10.0),
    (0.5, 2.0, 20.0),
)

#: Table 3, the upper limit of ``F(f)``, in per cent. The central band is the
#: same 10 %; outside it the limit is 20 % and applies only where the measured
#: response is above 0,01.
RESPONSE_TOLERANCE_UPPER_PERCENT: tuple[tuple[float, float, float], ...] = (
    (1.25, 0.8, 10.0),
    (0.0, math.inf, 20.0),
)

#: Above this response the upper limit of Table 3 applies at all (footnote a).
_UPPER_TOLERANCE_FLOOR: float = 0.01

#: Table 8 as Corrigendum 1:2012-12 rewrites it: bursts of an 80 Hz sine
#: repeated once a second, and the ``KB_Fmax`` each must show as a percentage
#: of the display for the continuous signal of the same amplitude. The rows
#: are ``(burst duration in milliseconds, whole sine cycles per second,
#: percentage)``; ``math.inf`` is the continuous signal, whose 100,4 % is the
#: ripple of the running r.m.s. rather than a gain.
KB_PULSE_RESPONSE_PERCENT: tuple[tuple[float, int, float], ...] = (
    (math.inf, 80, 100.4),
    (800.0, 64, 100.3),
    (400.0, 32, 98.3),
    (200.0, 16, 89.7),
    (100.0, 8, 74.5),
    (50.0, 4, 57.6),
    (25.0, 2, 42.7),
    (12.5, 1, 30.9),
)

#: The rows of Table 9 that follow the formulas of 5.2.3: for a 1 mm/s sine at
#: each test frequency, the ``KB_F(t)``, ``KB_Fmax`` and ``KB_FTm`` a meter of
#: the building working range must display. The ``|v|max`` row of the same
#: table is not here; see the module docstring and ``docs/ERRATA.md``.
KB_TEST_INDICATIONS: dict[float, tuple[float, float, float]] = {
    1.0: (0.103, 0.130, 0.130),
    5.6: (0.500, 0.528, 0.528),
    31.5: (0.693, 0.700, 0.700),
    80.0: (0.594, 0.597, 0.597),
    315.0: (0.071, 0.071, 0.071),
}

#: Table E.2: the frequency-independent guideline value each assessment
#: velocity is compared with, in millimetres per second, keyed by the building
#: class of DIN 4150-3:1999-02 Table 1 as
#: :data:`~phonometry.vibration.BUILDING_CLASSES` spells it.
ASSESSMENT_GUIDE_VALUES_MM_S: dict[str, float] = {
    "commercial": 20.0,
    "residential": 5.0,
    "sensitive": 3.0,
}

#: Table E.1: how far a realised assessment weighting may sit from its target
#: magnitude, as a fraction.
ASSESSMENT_WEIGHTING_TOLERANCE: float = 0.05

#: Table E.1, the guideline curve each assessment weighting inverts, as
#: ``(slope in mm/(s Hz), intercept in mm/s)`` over 10 Hz to 50 Hz and over
#: 50 Hz to 100 Hz. Below 10 Hz and above 100 Hz the curve is flat, at the
#: guideline value of :data:`ASSESSMENT_GUIDE_VALUES_MM_S` and at the value
#: the second segment reaches at 100 Hz.
_ASSESSMENT_SEGMENTS: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {
    "commercial": ((0.5, 15.0), (0.2, 30.0)),
    "residential": ((0.25, 2.5), (0.1, 10.0)),
    "sensitive": ((0.125, 1.75), (0.04, 6.0)),
}

#: Where Table E.1 changes segment, in hertz. They are also the corners of the
#: DIN 4150-3 Table 1 curve the weighting inverts, and the test suite asserts
#: the whole curve against the module that implements that table rather than
#: importing three numbers from it.
_SEGMENT_EDGES_HZ: tuple[float, float, float] = (10.0, 50.0, 100.0)

_WORKING_RANGES = tuple(WORKING_RANGES_HZ)
_WEIGHTINGS = ("kb", "unweighted")
_DOMINANT_METHODS = ("zero_crossing", "fourier")
_SQRT2 = math.sqrt(2.0)


def _range_limits(working_range: str) -> tuple[float, float]:
    """The ``(f_u, f_o)`` of a named working range, in hertz."""
    name = require_choice(str(working_range), "working_range", _WORKING_RANGES)
    return WORKING_RANGES_HZ[name]


def _frequencies(frequencies_hz: ArrayLike) -> NDArray[np.float64]:
    """Positive, finite frequencies as a float array."""
    return require_positive_array(frequencies_hz, "frequencies_hz")


def _velocity(
    velocity_mm_s: ArrayLike, name: str = "velocity_mm_s"
) -> NDArray[np.float64]:
    """A finite one-dimensional record as a float array, reported as *name*."""
    x = require_finite_array(velocity_mm_s, name)
    if x.ndim != 1 or x.size == 0:
        msg = f"{name!r} must be a non-empty 1-D array."
        raise ValueError(msg)
    return x


def _analog_zpk(
    working_range: str, *, weighted: bool
) -> tuple[NDArray[np.float64], NDArray[np.complex128], float]:
    """Formula (3), and Formula (4) when *weighted*, as zeros, poles and gain.

    Writing the printed expressions with ``s = j 2 pi f`` turns each bracket
    into a Butterworth pair: the first is ``s^2 / (s^2 + sqrt(2) w s + w^2)``
    with ``w`` the high-pass corner, the second the low pass with the same
    damping, and the weighting factor of Formula (4) is one more real pole at
    5,6 Hz with its zero at the origin.
    """
    lower_hz, upper_hz = _range_limits(working_range)
    w_high = 2.0 * math.pi * BAND_LIMIT_CORNER_FACTOR * lower_hz
    w_low = 2.0 * math.pi * upper_hz / BAND_LIMIT_CORNER_FACTOR
    poles = np.concatenate(
        (
            np.roots([1.0, _SQRT2 * w_high, w_high**2]),
            np.roots([1.0, _SQRT2 * w_low, w_low**2]),
        )
    ).astype(np.complex128)
    zeros = np.zeros(2, dtype=np.float64)
    if weighted:
        w_kb = 2.0 * math.pi * KB_CORNER_HZ
        poles = np.concatenate((poles, np.array([-w_kb], dtype=np.complex128)))
        zeros = np.zeros(3, dtype=np.float64)
    return zeros, poles, float(w_low**2)


@lru_cache(maxsize=16)
def _cached_sos(
    working_range: str, fs_hz: float, *, weighted: bool
) -> NDArray[np.float64]:
    """The shared, read-only digital design behind :func:`_sos`."""
    zeros, poles, gain = _analog_zpk(working_range, weighted=weighted)
    sos = sig.zpk2sos(*sig.bilinear_zpk(zeros, poles, gain, fs_hz))
    shared = np.asarray(sos, dtype=np.float64)
    shared.setflags(write=False)
    return shared


def _sos(working_range: str, fs_hz: float, *, weighted: bool) -> NDArray[np.float64]:
    """A writable copy of the cached second-order sections."""
    return np.array(_cached_sos(working_range, fs_hz, weighted=weighted))


def _sample_rate(fs_hz: float, working_range: str) -> float:
    """A sampling frequency that can carry the working range it is asked for.

    The upper band limit has to be inside the digital band, and comfortably:
    a bilinear design at a rate that puts ``f_o`` near Nyquist warps the very
    corner the response is graded at. Refused rather than warned about,
    because the numbers that come out of an aliased record look ordinary.
    """
    fs = require_positive(fs_hz, "fs_hz")
    upper_hz = _range_limits(working_range)[1]
    if fs <= 2.0 * upper_hz:
        msg = (
            f"'fs_hz' must be above twice the upper band limit of the "
            f"{working_range!r} working range ({upper_hz:g} Hz); got {fs:g} Hz."
        )
        raise ValueError(msg)
    return fs


def band_limitation_response(
    frequencies_hz: ArrayLike, *, working_range: str = "building"
) -> NDArray[np.complex128]:
    r"""The band limitation of the unweighted signal, Formula (3).

    :param frequencies_hz: Frequencies, in hertz.
    :param working_range: ``"building"`` (1 Hz to 80 Hz, the default) or
        ``"railway"`` (4 Hz to 315 Hz); see :data:`WORKING_RANGES_HZ`.
    :return: The complex response :math:`H_{u\mathrm{Soll}}`, whose magnitude
        is Formula (5).
    :raises ValueError: For a non-positive frequency or an unknown range.
    """
    f = _frequencies(frequencies_hz)
    lower_hz, upper_hz = _range_limits(working_range)
    high = 1.0 - 1j * _SQRT2 * (BAND_LIMIT_CORNER_FACTOR * lower_hz / f)
    high = high - (BAND_LIMIT_CORNER_FACTOR * lower_hz / f) ** 2
    low = 1.0 + 1j * _SQRT2 * (BAND_LIMIT_CORNER_FACTOR * f / upper_hz)
    low = low - (BAND_LIMIT_CORNER_FACTOR * f / upper_hz) ** 2
    return np.asarray(1.0 / (high * low), dtype=np.complex128)


def kb_weighting_response(
    frequencies_hz: ArrayLike, *, working_range: str = "building"
) -> NDArray[np.complex128]:
    r"""The KB frequency weighting, Formula (4).

    :param frequencies_hz: Frequencies, in hertz.
    :param working_range: See :func:`band_limitation_response`.
    :return: The complex response :math:`H_{B\mathrm{Soll}}`, whose magnitude
        is Formula (6).
    :raises ValueError: For a non-positive frequency or an unknown range.
    """
    f = _frequencies(frequencies_hz)
    band = band_limitation_response(f, working_range=working_range)
    return np.asarray(band / (1.0 - 1j * KB_CORNER_HZ / f), dtype=np.complex128)


def response_tolerance_percent(
    frequencies_hz: ArrayLike, *, working_range: str = "building"
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The limits of Tables 2 and 3 at each frequency, in per cent.

    :param frequencies_hz: Frequencies, in hertz.
    :param working_range: See :func:`band_limitation_response`.
    :return: ``(lower, upper)``: the largest deviation allowed below and above
        the design response, both as positive percentages. A lower limit of
        100 % is the standard declining to constrain the response from below
        outside the working range.
    :raises ValueError: For a non-positive frequency or an unknown range.
    """
    f = _frequencies(frequencies_hz)
    lower_hz, upper_hz = _range_limits(working_range)
    central = (f >= 1.25 * lower_hz) & (f <= BAND_LIMIT_CORNER_FACTOR * upper_hz)
    skirt = (f > 0.5 * lower_hz) & (f < 2.0 * upper_hz)
    lower = np.full(f.shape, 100.0)
    lower[skirt] = 20.0
    lower[central] = 10.0
    upper = np.full(f.shape, 20.0)
    upper[central] = 10.0
    return lower, upper


@dataclass(frozen=True)
class VibrationMeterVerification:
    """One measured amplitude response against Tables 2 and 3.

    :ivar frequencies_hz: The frequencies the response was measured at.
    :ivar deviation_percent: ``F(f)`` of Formula (7) at each of them: the
        measured response over the design response, both normalised at the
        reference frequency, as a percentage departure from unity.
    :ivar lower_percent: The Table 2 limit at each frequency.
    :ivar upper_percent: The Table 3 limit at each frequency.
    :ivar within_tolerance: Whether each frequency keeps to both limits.
    :ivar weighting: ``"kb"`` or ``"unweighted"``, which design response the
        deviation is against.
    :ivar working_range: The working range the limits were read for.
    :ivar reference_frequency_hz: The frequency both responses were
        normalised at.
    """

    frequencies_hz: NDArray[np.float64]
    deviation_percent: NDArray[np.float64]
    lower_percent: NDArray[np.float64]
    upper_percent: NDArray[np.float64]
    within_tolerance: NDArray[np.bool_]
    weighting: str
    working_range: str
    reference_frequency_hz: float

    @property
    def passes(self) -> bool:
        """Whether every graded frequency keeps to its limits."""
        return bool(np.all(self.within_tolerance))

    @property
    def worst_frequency_hz(self) -> float:
        """The frequency that uses the largest share of its allowance."""
        allowance = np.where(
            self.deviation_percent >= 0.0, self.upper_percent, self.lower_percent
        )
        used = np.abs(self.deviation_percent) / allowance
        return float(self.frequencies_hz[int(np.argmax(used))])

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the deviation against the tolerance band it is judged by.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_vibration_meter_verification`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_vibration_meter_verification

        check_language(language)
        return plot_vibration_meter_verification(
            self, ax=ax, language=language, **kwargs
        )


def verify_vibration_meter(
    frequencies_hz: ArrayLike,
    measured_response: ArrayLike,
    *,
    weighting: Literal["kb", "unweighted"] | str = "kb",
    working_range: str = "building",
    reference_frequency_hz: float = KB_REFERENCE_FREQUENCY_HZ,
) -> VibrationMeterVerification:
    """Check a measured amplitude response against Tables 2 and 3.

    Formula (7) is a ratio of ratios: the measured response over the design
    response, each divided by its own value at the reference frequency, so a
    meter is graded on the shape of its response and not on the gain that a
    calibration sets. The reference frequency itself carries no requirement,
    the standard writing every limit "for all f not equal to f_r", and it is
    dropped from the verdict rather than passed for free.

    :param frequencies_hz: The frequencies the response was measured at, in
        hertz. The reference frequency has to be among them.
    :param measured_response: The measured amplitude response at those
        frequencies, in any consistent unit: only its shape is graded.
    :param weighting: ``"kb"`` for the weighted response of Formula (4), the
        default, or ``"unweighted"`` for the band limitation of Formula (3).
    :param working_range: See :func:`band_limitation_response`.
    :param reference_frequency_hz: The reference frequency of 5.2.10, in
        hertz (default 16 Hz).
    :return: The comparison, as a :class:`VibrationMeterVerification`.
    :raises ValueError: If the two arrays disagree in shape, if a frequency or
        a response is not positive and finite, or if the reference frequency
        is not one of the measured frequencies.
    """
    f = _frequencies(frequencies_hz)
    measured = require_positive_array(measured_response, "measured_response")
    require_equal_shapes(
        "verify_vibration_meter",
        {"frequencies_hz": f.shape, "measured_response": measured.shape},
        quantity="frequency",
    )
    which = require_choice(str(weighting), "weighting", _WEIGHTINGS)
    reference_hz = require_positive(reference_frequency_hz, "reference_frequency_hz")
    at_reference = np.isclose(f, reference_hz, rtol=1e-9, atol=0.0)
    if not np.any(at_reference):
        msg = (
            f"'reference_frequency_hz' ({reference_hz:g} Hz) must be one of the "
            f"measured frequencies, because Formula (7) normalises both "
            f"responses there."
        )
        raise ValueError(msg)
    design_call = kb_weighting_response if which == "kb" else band_limitation_response
    design = np.abs(design_call(f, working_range=working_range))
    graded = ~at_reference
    ratio = (measured[graded] / design[graded]) * (
        float(design[at_reference][0]) / float(measured[at_reference][0])
    )
    deviation = (ratio - 1.0) * 100.0
    lower, upper = response_tolerance_percent(f[graded], working_range=working_range)
    upper = np.where(measured[graded] > _UPPER_TOLERANCE_FLOOR, upper, math.inf)
    within = (deviation >= -lower) & (deviation <= upper)
    return VibrationMeterVerification(
        frequencies_hz=f[graded],
        deviation_percent=deviation,
        lower_percent=lower,
        upper_percent=upper,
        within_tolerance=within,
        weighting=which,
        working_range=str(working_range),
        reference_frequency_hz=reference_hz,
    )


def kb_signal(
    velocity_mm_s: ArrayLike, fs_hz: float, *, working_range: str = "building"
) -> NDArray[np.float64]:
    """The KB signal ``KB(t)`` of 3.10.1.1, which is dimensionless.

    The velocity is band-limited and frequency-weighted by Formula (4) and
    normalised by 1 mm/s, which is the normalisation that makes the KB signal
    a number rather than a velocity, so the record has to be in millimetres
    per second for the result to mean what the standard says.

    :param velocity_mm_s: The measured velocity, in millimetres per second
        (1-D).
    :param fs_hz: Sampling frequency, in hertz.
    :param working_range: See :func:`band_limitation_response`.
    :return: ``KB(t)``, one value per sample.
    :raises ValueError: For a bad record, a rate that cannot carry the working
        range, or an unknown range.
    """
    x = _velocity(velocity_mm_s)
    name = require_choice(str(working_range), "working_range", _WORKING_RANGES)
    fs = _sample_rate(fs_hz, name)
    return np.asarray(sig.sosfilt(_sos(name, fs, weighted=True), x), dtype=np.float64)


def kbf_signal(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    working_range: str = "building",
    time_constant_s: float = KB_TIME_CONSTANT_S,
) -> NDArray[np.float64]:
    """The weighted vibration severity ``KB_F(t)``, Formula (1).

    The running r.m.s. is the exponential average the formula integrates, as
    the single-pole recursion Annex A draws: ``y[i] = (1 - a) y[i-1] + a x[i]``
    with ``a = 1 - exp(-1 / (tau fs))``. It starts from zero, so the first
    samples ramp up like a meter switched on with the signal already present;
    2 tau of record is 14 % low in mean square and 4 tau is 2 % low, which is
    why a measurement is started before the event it is about.

    :param velocity_mm_s: The measured velocity, in millimetres per second
        (1-D).
    :param fs_hz: Sampling frequency, in hertz.
    :param working_range: See :func:`band_limitation_response`.
    :param time_constant_s: The averaging time constant, in seconds. The
        standard fixes it at 0,125 s and the parameter exists so a comparison
        with another time weighting can be written down, not so a meter can
        use one.
    :return: ``KB_F(t)``, one value per sample.
    :raises ValueError: For a bad record, a non-positive time constant, or a
        rate that cannot carry the working range.
    """
    kb = kb_signal(velocity_mm_s, fs_hz, working_range=working_range)
    tau = require_positive(time_constant_s, "time_constant_s")
    alpha = 1.0 - math.exp(-1.0 / (tau * float(fs_hz)))
    mean_square = np.asarray(
        sig.lfilter([alpha], [1.0, -(1.0 - alpha)], kb**2), dtype=np.float64
    )
    return np.sqrt(np.maximum(mean_square, 0.0))


def takt_maxima(
    kbf: ArrayLike, fs_hz: float, *, takt_duration_s: float = TAKT_DURATION_S
) -> NDArray[np.float64]:
    """The clock maxima ``KB_FTi`` of 3.10.1.4, one per whole clock interval.

    A clock interval the record did not fill is not a clock interval: 5.1.6.4
    says the averaging time always spans a whole number of them, so a trailing
    part-interval is dropped rather than scaled up.

    :param kbf: The ``KB_F(t)`` signal (1-D).
    :param fs_hz: Sampling frequency, in hertz.
    :param takt_duration_s: The clock interval, in seconds (default 30 s).
    :return: One maximum per whole clock interval, in order. Empty when the
        record is shorter than one interval.
    :raises ValueError: For a bad signal or a non-positive rate or interval.
    """
    y = _velocity(kbf, "kbf")
    fs = require_positive(fs_hz, "fs_hz")
    duration_s = require_positive(takt_duration_s, "takt_duration_s")
    per_takt = int(round(duration_s * fs))
    if per_takt <= 0:
        msg = "'takt_duration_s' is shorter than one sample."
        raise ValueError(msg)
    count = y.size // per_takt
    if count == 0:
        return np.empty(0, dtype=np.float64)
    blocks = y[: count * per_takt].reshape(count, per_takt)
    return np.asarray(blocks.max(axis=1), dtype=np.float64)


def takt_maximum_rms(maxima: ArrayLike) -> float:
    """The clock maximum r.m.s. ``KB_FTm``, Formula (2).

    Both rules of the formula are here: a clock maximum at or below
    :data:`TAKT_SUPPRESSION_THRESHOLD` enters the sum as zero, and the
    interval it came from still counts in ``N``, so a run of quiet intervals
    pulls the result down instead of leaving it unchanged.

    :param maxima: The clock maxima of :func:`takt_maxima`.
    :return: ``KB_FTm``, dimensionless. Zero for an empty input, which is the
        answer for a record with no whole clock interval in it.
    :raises ValueError: If a maximum is negative or not finite.
    """
    values = np.atleast_1d(np.asarray(maxima, dtype=np.float64))
    if values.size == 0:
        # A record with no whole clock interval in it: Formula (2) averages
        # over N of them and there are none, which is nothing rather than an
        # error. The empty case is settled before the validator, which refuses
        # an empty array everywhere else in this tree for good reason.
        return 0.0
    values = require_finite_array(values, "maxima")
    if np.any(values < 0.0):
        msg = "'maxima' must not be negative; a KB_F signal never is."
        raise ValueError(msg)
    counted = np.where(values <= TAKT_SUPPRESSION_THRESHOLD, 0.0, values)
    return float(np.sqrt(np.mean(counted**2)))


@dataclass(frozen=True)
class VibrationMeterReading:
    r"""What a meter displays for one record (5.1.6.1).

    :ivar peak_velocity_mm_s: :math:`|v|_\mathrm{max}`, the largest absolute
        value of the band-limited velocity over the measuring time.
    :ivar kbf: The ``KB_F(t)`` signal, one value per sample.
    :ivar kbf_max: :math:`KB_{F\mathrm{max}}`, its maximum.
    :ivar takt_maxima: The clock maxima, one per whole clock interval.
    :ivar kbf_takt_rms: :math:`KB_{FTm}` of Formula (2).
    :ivar fs_hz: The sampling frequency the record was read at.
    :ivar measuring_time_s: :math:`T_M`, the length of the record.
    :ivar averaging_time_s: :math:`T_m`, the whole clock intervals in it.
    :ivar working_range: The working range the chain was built for.
    """

    peak_velocity_mm_s: float
    kbf: NDArray[np.float64]
    kbf_max: float
    takt_maxima: NDArray[np.float64]
    kbf_takt_rms: float
    fs_hz: float
    measuring_time_s: float
    averaging_time_s: float
    working_range: str

    @property
    def above_detection_limit(self) -> bool:
        """Whether the reading is above the detection limits of 5.2.2.

        Below them a meter is not required to resolve anything, so a smaller
        reading is not a measurement of a smaller vibration.
        """
        return bool(
            self.peak_velocity_mm_s > VELOCITY_DETECTION_LIMIT_MM_S
            or self.kbf_max > KB_DETECTION_LIMIT
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw ``KB_F(t)`` with its maximum and the clock maxima on it.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_vibration_meter_reading`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_vibration_meter_reading

        check_language(language)
        return plot_vibration_meter_reading(self, ax=ax, language=language, **kwargs)


def measure_vibration_immission(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    working_range: str = "building",
    takt_duration_s: float = TAKT_DURATION_S,
) -> VibrationMeterReading:
    """Run one velocity record through the whole chain of 5.1.6.

    **Start the record before the event.** Every filter here begins at rest,
    so a record that begins with the signal already at full amplitude carries
    the filter's own switch-on transient, and the peak is a max-hold that
    keeps it: a 1 mm/s sine started at a zero crossing reads 1,06 mm/s rather
    than the 1,00 mm/s of 6.2.3.12, and at 315 Hz outside the building range
    it reads 0,25 mm/s where the steady response is 0,10 mm/s. That is an
    artefact of the record, not of the chain, and a lead-in of a second or two
    of quiet removes it, which is also how a real measurement is made.

    :param velocity_mm_s: The measured velocity, in millimetres per second
        (1-D).
    :param fs_hz: Sampling frequency, in hertz.
    :param working_range: See :func:`band_limitation_response`.
    :param takt_duration_s: The clock interval, in seconds (default 30 s).
    :return: The displayed quantities, as a :class:`VibrationMeterReading`.
    :raises ValueError: For a bad record, a rate that cannot carry the working
        range, or a non-positive clock interval.
    """
    x = _velocity(velocity_mm_s)
    name = require_choice(str(working_range), "working_range", _WORKING_RANGES)
    fs = _sample_rate(fs_hz, name)
    band_limited = sig.sosfilt(_sos(name, fs, weighted=False), x)
    kbf = kbf_signal(x, fs, working_range=name)
    maxima = takt_maxima(kbf, fs, takt_duration_s=takt_duration_s)
    return VibrationMeterReading(
        peak_velocity_mm_s=float(np.max(np.abs(band_limited))),
        kbf=kbf,
        kbf_max=float(np.max(kbf)),
        takt_maxima=maxima,
        kbf_takt_rms=takt_maximum_rms(maxima),
        fs_hz=fs,
        measuring_time_s=float(x.size / fs),
        averaging_time_s=float(maxima.size * takt_duration_s),
        working_range=name,
    )


def assessment_weighting_response(
    frequencies_hz: ArrayLike, *, building_class: str
) -> NDArray[np.float64]:
    """The target magnitude of an Annex E weighting filter, Table E.1.

    Each filter is the guideline curve of its building class inverted and
    normalised to the value that curve holds from 1 Hz to 10 Hz, so filtering
    with it turns a frequency-dependent comparison into a comparison with one
    number. The curve is flat below 10 Hz, rises along two straight segments
    to 100 Hz and is flat above it, and Table E.1 carries that last segment
    up to the Nyquist frequency rather than stopping at 100 Hz.

    :param frequencies_hz: Frequencies, in hertz.
    :param building_class: The row of DIN 4150-3:1999-02 Table 1, as
        :data:`ASSESSMENT_GUIDE_VALUES_MM_S` keys it.
    :return: The target magnitude, dimensionless, 1 below 10 Hz.
    :raises ValueError: For a non-positive frequency or an unknown class.
    """
    f = _frequencies(frequencies_hz)
    name = require_choice(
        str(building_class), "building_class", tuple(ASSESSMENT_GUIDE_VALUES_MM_S)
    )
    guide = ASSESSMENT_GUIDE_VALUES_MM_S[name]
    (slope_low, intercept_low), (slope_high, intercept_high) = _ASSESSMENT_SEGMENTS[
        name
    ]
    flat_hz, knee_hz, top_hz = _SEGMENT_EDGES_HZ
    curve = np.full(f.shape, guide, dtype=np.float64)
    mid = (f > flat_hz) & (f <= knee_hz)
    upper = (f > knee_hz) & (f <= top_hz)
    above = f > top_hz
    curve[mid] = slope_low * f[mid] + intercept_low
    curve[upper] = slope_high * f[upper] + intercept_high
    curve[above] = slope_high * top_hz + intercept_high
    return np.asarray(guide / curve, dtype=np.float64)


def assessment_weighting_taps(
    fs_hz: float, *, building_class: str, numtaps: int | None = None
) -> NDArray[np.float64]:
    """A linear-phase FIR that realises an Annex E weighting.

    Annex E asks for a linear phase and says why: a weighting filter that
    delays different frequencies differently changes the peak it is there to
    measure. A symmetric FIR is the type the annex names, and its only cost is
    a constant delay of half its length, which :func:`assessment_velocity`
    removes.

    :param fs_hz: Sampling frequency, in hertz. Table E.1 requires the Nyquist
        frequency to be above 315 Hz where the meter reaches that far, and
        this refuses a rate below 630 Hz for the same reason.
    :param building_class: See :func:`assessment_weighting_response`.
    :param numtaps: Length of the filter, odd. The default resolves the 10 Hz
        corner of the target with room to spare, at half a second of taps.
    :return: The filter coefficients.
    :raises ValueError: For a rate below 630 Hz, an even or non-positive
        length, or an unknown class.
    """
    fs = require_positive(fs_hz, "fs_hz")
    minimum_hz = 2.0 * WORKING_RANGES_HZ["railway"][1]
    if fs <= minimum_hz:
        msg = (
            f"'fs_hz' must be above {minimum_hz:g} Hz: Table E.1 defines the "
            f"weighting up to the Nyquist frequency and requires it above "
            f"315 Hz; got {fs:g} Hz."
        )
        raise ValueError(msg)
    name = require_choice(
        str(building_class), "building_class", tuple(ASSESSMENT_GUIDE_VALUES_MM_S)
    )
    if numtaps is None:
        taps = int(round(fs / 2.0))
        taps += 1 - taps % 2
    else:
        taps = int(numtaps)
        if taps <= 0 or taps % 2 == 0:
            msg = f"'numtaps' must be a positive odd number; got {numtaps!r}."
            raise ValueError(msg)
    grid_hz = np.linspace(0.0, fs / 2.0, 512)
    gains = np.empty_like(grid_hz)
    gains[0] = 1.0
    gains[1:] = assessment_weighting_response(grid_hz[1:], building_class=name)
    coefficients: NDArray[np.float64] = np.asarray(
        sig.firwin2(taps, grid_hz, gains, fs=fs), dtype=np.float64
    )
    return coefficients


def assessment_velocity(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    building_class: str,
    numtaps: int | None = None,
) -> NDArray[np.float64]:
    """The assessment velocity ``v_Bn(t)`` of Annex E, in mm/s.

    The velocity is filtered with the weighting of its building class and the
    constant delay of the symmetric filter is removed, so the result lines up
    in time with the record it came from.

    :param velocity_mm_s: The measured velocity, in millimetres per second
        (1-D). Annex E filters the unweighted signal, which has already been
        band-limited by 5.2.3.
    :param fs_hz: Sampling frequency, in hertz.
    :param building_class: See :func:`assessment_weighting_response`.
    :param numtaps: See :func:`assessment_weighting_taps`.
    :return: ``v_Bn(t)``, one value per sample.
    :raises ValueError: For a bad record, a rate below 630 Hz, or an unknown
        class.
    """
    x = _velocity(velocity_mm_s)
    taps = assessment_weighting_taps(
        fs_hz, building_class=building_class, numtaps=numtaps
    )
    delay = (taps.size - 1) // 2
    padded = np.concatenate((x, np.zeros(delay, dtype=np.float64)))
    return np.asarray(sig.lfilter(taps, [1.0], padded)[delay:], dtype=np.float64)


@dataclass(frozen=True)
class AssessmentVelocity:
    r"""One record judged by Annex E, without a dominant frequency.

    :ivar assessment_velocity_mm_s: :math:`|v_{Bn}|_\mathrm{max}`, the peak
        of the weighted velocity, in millimetres per second.
    :ivar guide_value_mm_s: The Table E.2 value it is compared with.
    :ivar building_class: The row of DIN 4150-3 Table 1 that was used.
    :ivar velocity_mm_s: The weighted velocity itself, one value per sample.
    :ivar fs_hz: The sampling frequency the record was read at.
    """

    assessment_velocity_mm_s: float
    guide_value_mm_s: float
    building_class: str
    velocity_mm_s: NDArray[np.float64]
    fs_hz: float

    @property
    def ratio(self) -> float:
        """The peak as a fraction of the guideline value."""
        return float(self.assessment_velocity_mm_s / self.guide_value_mm_s)

    @property
    def within_guideline(self) -> bool:
        """Whether the record keeps to the guideline value of Table E.2.

        The same reading as DIN 4150-3 gives it: keeping to the value is what
        the standard promises about, exceeding it means the question moves to
        Clauses 4.2 to 4.4 rather than that damage has occurred.
        """
        return bool(self.assessment_velocity_mm_s <= self.guide_value_mm_s)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the weighted velocity against its guideline value.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_assessment_velocity`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_assessment_velocity

        check_language(language)
        return plot_assessment_velocity(self, ax=ax, language=language, **kwargs)


def assess_short_term_vibration(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    building_class: str,
    numtaps: int | None = None,
) -> AssessmentVelocity:
    """Judge short-term vibration on a building by Annex E.

    :param velocity_mm_s: The measured velocity at the foundation, in
        millimetres per second (1-D).
    :param fs_hz: Sampling frequency, in hertz.
    :param building_class: See :func:`assessment_weighting_response`.
    :param numtaps: See :func:`assessment_weighting_taps`.
    :return: The comparison, as an :class:`AssessmentVelocity`.
    :raises ValueError: For a bad record, a rate below 630 Hz, or an unknown
        class.
    """
    name = require_choice(
        str(building_class), "building_class", tuple(ASSESSMENT_GUIDE_VALUES_MM_S)
    )
    weighted = assessment_velocity(
        velocity_mm_s, fs_hz, building_class=name, numtaps=numtaps
    )
    return AssessmentVelocity(
        assessment_velocity_mm_s=float(np.max(np.abs(weighted))),
        guide_value_mm_s=ASSESSMENT_GUIDE_VALUES_MM_S[name],
        building_class=name,
        velocity_mm_s=weighted,
        fs_hz=float(fs_hz),
    )


@dataclass(frozen=True)
class DominantFrequency:
    """The dominant frequency of one event, and how it was found (Annex D).

    :ivar frequency_hz: The dominant frequency, in hertz.
    :ivar method: ``"zero_crossing"`` or ``"fourier"``.
    :ivar candidates: For the Fourier method, the two largest spectral values
        as ``(frequency in hertz, magnitude)`` pairs, largest first, which is
        what D b) asks a meter to report so the choice between them is made
        rather than assumed. Empty for the zero-crossing method.
    """

    frequency_hz: float
    method: str
    candidates: tuple[tuple[float, float], ...]


def dominant_frequency(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    method: Literal["zero_crossing", "fourier"] | str = "zero_crossing",
) -> DominantFrequency:
    """The dominant frequency of a short-term event, by one of Annex D's ways.

    A short-term vibration has no frequency in the physical sense, and Annex D
    says so before giving two ways of naming one anyway. They can disagree,
    and the disagreement matters: the frequency picks the guideline value in
    DIN 4150-3, so it can change the verdict. That is the ambiguity Annex E
    removes, and this function is here for the case where the frequency itself
    has to be reported.

    :param velocity_mm_s: The measured velocity, in millimetres per second
        (1-D).
    :param fs_hz: Sampling frequency, in hertz.
    :param method: ``"zero_crossing"`` (D a), the default: the two zero
        crossings around the largest amplitude are half a period apart) or
        ``"fourier"`` (D b): the largest value of the spectrum of the whole
        event, with the runner-up reported beside it.
    :return: The frequency and how it was found, as a
        :class:`DominantFrequency`.
    :raises ValueError: For a bad record, a non-positive rate, an unknown
        method, or a record whose largest amplitude has no zero crossing on
        both sides of it.
    """
    x = _velocity(velocity_mm_s)
    fs = require_positive(fs_hz, "fs_hz")
    how = require_choice(str(method), "method", _DOMINANT_METHODS)
    if how == "fourier":
        window = np.hanning(x.size)
        spectrum = np.abs(np.fft.rfft(x * window))
        freqs = np.fft.rfftfreq(x.size, 1.0 / fs)
        order = np.argsort(spectrum)[::-1]
        best = [(float(freqs[i]), float(spectrum[i])) for i in order[:2]]
        return DominantFrequency(
            frequency_hz=best[0][0], method=how, candidates=tuple(best)
        )
    peak = int(np.argmax(np.abs(x)))
    signs = np.signbit(x)
    crossings = np.flatnonzero(signs[1:] != signs[:-1])
    before = crossings[crossings < peak]
    after = crossings[crossings >= peak]
    if before.size == 0 or after.size == 0:
        msg = (
            "the largest amplitude has no zero crossing on both sides of it, "
            "so no half period can be read; use method='fourier'."
        )
        raise ValueError(msg)
    half_period_s = float(after[0] - before[-1]) / fs
    return DominantFrequency(
        frequency_hz=1.0 / (2.0 * half_period_s), method=how, candidates=()
    )
