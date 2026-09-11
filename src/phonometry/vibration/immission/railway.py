#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Evaluating the vibration of a passing train (DIN 45672-2:1995-07).

A train passing a building puts vibration into the ground for twenty seconds
and then leaves, and DIN 45672-2 is the procedure that turns those twenty
seconds into numbers that can be compared: between two measuring points on the
way from the track to the building, between two dates either side of a
mitigation measure, and between one train and the next. It is measured with
the meter of DIN 45669-1 in its railway working range, 4 Hz to 315 Hz, and it
is an evaluation standard rather than an assessment one: it says how to reduce
a record, not what the result may be.

**Three stretches of one record** (Clause 5). :math:`T_1` is about four
seconds with the largest vibration in its middle, where the characteristic
values of the passage are read. :math:`T_2` is the passage itself, from where
the amplitude first reaches about a quarter of its usual maxima to where it
falls back to it. :math:`T_3` is the whole event, and it is the one an event
value is formed over. Every quantity below carries the index of the stretch it
came from.

**The quantities** (Clause 6). The running r.m.s. :math:`\tilde v_F(t)` with
:math:`\tau = 125` ms (Formula (1)) and its level against
:math:`v_0 = 5 \cdot 10^{-8}` m/s (Formula (2)); the interval r.m.s.
:math:`\tilde v_j` of Formula (4), or the approximation of Formula (5) formed
from the running r.m.s.; and the **event value** of Formula (8), the interval
r.m.s. of :math:`T_3` referred to one hour, :math:`v_E = \tilde v_3
\sqrt{T_3/3600\,\mathrm{s}}`, whose square adds across the passages of an hour
(Formula (10)). The same quantities in third-octave bands from 4 Hz to 315 Hz
give the interval and maximum third-octave levels of Formulae (6) and (7).

**Narrow band** (Clause 7.3). The one-sided power spectral density of Formula
(12), blockwise with a Hanning window and at least half a block of overlap, at
the resolution of 1,25 Hz the standard recommends because it resolves the
resonance of an ordinary floor. Adding its lines back into third octaves is
Formula (23), and Table 1 fixes how many lines each band takes: a number
recommended for comparability rather than derived, which is why it is a
table here.

**What this does not do.** The standard is a method of reduction, so there is
no verdict anywhere in it, and none here: what the numbers mean for people and
buildings is DIN 4150-2 and DIN 4150-3. The calibration checks of Clause 7.3.3
test an analyser, which this module is not.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import scipy.signal as sig

from ..._internal.levels_math import energy_mean, energy_sum
from ..._internal.validation import (
    _as_float64,
    require_finite_array,
    require_positive,
)
from .vibration_meter import (
    KB_TIME_CONSTANT_S,
    _exponential_running_rms,
    _record,
    _sample_rate,
    _sos,
    kbf_signal,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

    from ...signals.spectra import SpectralDensityResult

__all__ = [
    "EVENT_REFERENCE_DURATION_S",
    "NARROWBAND_RESOLUTION_HZ",
    "PASSAGE_BANDS_HZ",
    "T1_DURATION_S",
    "THIRD_OCTAVE_LINES",
    "VELOCITY_LEVEL_REFERENCE_MM_S",
    "AmplitudeDistribution",
    "TrainPassage",
    "amplitude_distribution",
    "band_sum_level",
    "centred_interval",
    "combined_event_velocity",
    "elastic_insertion_loss",
    "evaluate_train_passage",
    "event_velocity",
    "event_velocity_level",
    "interval_rms",
    "narrowband_psd",
    "passage_average_level",
    "passage_average_velocity",
    "passage_energy_spectral_density",
    "running_acceleration_level",
    "running_velocity_level",
    "running_velocity_rms",
    "spectral_density_level",
    "third_octaves_from_narrowband",
    "velocity_psd_from_voltage",
]

#: The reference acceleration of Formula (3), in metres per second squared:
#: the :math:`10^{-6}` m/s² of DIN EN 21683, the same number
#: ``vibration.REFERENCE_ACCELERATION`` publishes for human exposure.
_ACCELERATION_REFERENCE_M_S2 = 1.0e-6

#: The reference velocity of Formula (2), in millimetres per second: the
#: :math:`5 \cdot 10^{-8}` m/s the standard takes from DIN EN 21683
#: (ISO 1683:1983). ISO 1683:2015 changed it to 1 nm/s, so a level quoted
#: against the other reference is 34 dB different for the same vibration.
VELOCITY_LEVEL_REFERENCE_MM_S: float = 5.0e-5

#: The hour an event value is referred to (Formulae (8) and (9)), in seconds.
EVENT_REFERENCE_DURATION_S: float = 3600.0

#: The duration Clause 5 a) recommends for the stretch around the largest
#: vibration, in seconds. A short or fast train often needs less, and then
#: :math:`T_1` may be as long as :math:`T_2` and no longer.
T1_DURATION_S: float = 4.0

#: The third-octave range of Clause 7.2, in hertz: 4 Hz to at least 315 Hz,
#: the railway working range of the DIN 45669-1 meter. DIN 45672-1 allows a
#: special case that stops at 80 Hz.
PASSAGE_BANDS_HZ: tuple[float, float] = (4.0, 315.0)

#: The narrow-band resolution Clause 7.3.2 recommends, in hertz. It resolves
#: the resonance of an ordinary floor, and it is the one the line counts of
#: :data:`THIRD_OCTAVE_LINES` are written for.
NARROWBAND_RESOLUTION_HZ: float = 1.25

#: Table 1: how many narrow-band lines of 1,25 Hz each third octave takes when
#: a narrow-band spectrum is added back into bands (Formula (23)), keyed by the
#: nominal centre frequency in hertz. The counts are recommended "for
#: comparability" and are not derived in the standard. They are what a sixth
#: of an octave either side of the nominal centre holds, except at 10 Hz and
#: 12,5 Hz, where the table gives each band two lines and those edges give one
#: and three.
THIRD_OCTAVE_LINES: dict[float, int] = {
    4.0: 1,
    5.0: 1,
    6.3: 1,
    8.0: 2,
    10.0: 2,
    12.5: 2,
    16.0: 3,
    20.0: 3,
    25.0: 5,
    31.5: 6,
    40.0: 7,
    50.0: 9,
    63.0: 12,
    80.0: 14,
    100.0: 18,
    125.0: 23,
    160.0: 29,
    200.0: 37,
    250.0: 46,
    315.0: 58,
    400.0: 74,
    500.0: 92,
}

#: How far the line spacing may stray from 1,25 Hz before Table 1 stops
#: describing the spectrum it is handed. The counts are counts of lines of that
#: spacing: at 0,1 % the lines up to 560 Hz drift by less than half a line, and
#: every sampling rate in common use lands well inside it.
_RESOLUTION_TOLERANCE = 1e-3

#: The fewest bins an amplitude distribution can have a shape with.
_MIN_BINS = 2

#: The upper band limits Clause 7.2 allows, in hertz.
_UPPER_BAND_RANGE_HZ: tuple[float, float] = (80.0, 315.0)


def running_velocity_rms(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    time_constant_s: float = KB_TIME_CONSTANT_S,
) -> NDArray[np.float64]:
    r"""The running r.m.s. :math:`\tilde v_F(t)` of Formula (1), in mm/s.

    The exponential average the formula integrates, started from rest. Clause
    4 says what that costs at the start of a record and so why the averaging
    has to be running before the train arrives. It puts the cost at 14 % after
    :math:`2\tau` and 2 % after :math:`4\tau`, which are the shortfalls of the
    mean square, :math:`e^{-2}` and :math:`e^{-4}`; the running r.m.s. itself,
    which is what Figure 3 draws, is 7 % and 0,9 % short.

    :param velocity_mm_s: The velocity, in millimetres per second (1-D), as
        measured or in one third-octave band of it.
    :param fs_hz: Sampling frequency, in hertz.
    :param time_constant_s: The time constant, in seconds (default 0,125 s,
        "Fast").
    :return: :math:`\tilde v_F(t)`, one value per sample, in mm/s.
    :raises ValueError: For a bad record or a non-positive rate or constant.
    """
    return _exponential_running_rms(
        velocity_mm_s, fs_hz, time_constant_s=time_constant_s, name="velocity_mm_s"
    )


def _level(values: NDArray[np.float64], reference: float) -> NDArray[np.float64]:
    """``20 lg(values / reference)``, with ``-inf`` for an exact zero."""
    with np.errstate(divide="ignore"):
        return np.asarray(20.0 * np.log10(values / reference), dtype=np.float64)


def running_velocity_level(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    time_constant_s: float = KB_TIME_CONSTANT_S,
) -> NDArray[np.float64]:
    r"""The running velocity level :math:`L_{vF}(t)` of Formula (2), in dB.

    :param velocity_mm_s: The velocity, in millimetres per second (1-D).
    :param fs_hz: Sampling frequency, in hertz.
    :param time_constant_s: See :func:`running_velocity_rms`.
    :return: :math:`20 \lg(\tilde v_F / v_0)` with :math:`v_0` =
        :data:`VELOCITY_LEVEL_REFERENCE_MM_S`, one value per sample. A sample
        whose running r.m.s. is still exactly zero, before the first nonzero
        sample, is ``-inf``.
    :raises ValueError: For a bad record or a non-positive rate or constant.
    """
    rms = running_velocity_rms(velocity_mm_s, fs_hz, time_constant_s=time_constant_s)
    return _level(rms, VELOCITY_LEVEL_REFERENCE_MM_S)


def running_acceleration_level(
    acceleration_m_s2: ArrayLike,
    fs_hz: float,
    *,
    time_constant_s: float = KB_TIME_CONSTANT_S,
) -> NDArray[np.float64]:
    r"""The running acceleration level :math:`L_{aF}(t)` of Formula (3), in dB.

    :param acceleration_m_s2: The acceleration, in metres per second squared
        (1-D).
    :param fs_hz: Sampling frequency, in hertz.
    :param time_constant_s: See :func:`running_velocity_rms`.
    :return: :math:`20 \lg(\tilde a_F / a_0)` with :math:`a_0 = 10^{-6}`
        m/s², the reference DIN EN 21683 gives and the one the rest of this
        package's acceleration levels use.
    :raises ValueError: For a bad record or a non-positive rate or constant.
    """
    rms = _exponential_running_rms(
        acceleration_m_s2,
        fs_hz,
        time_constant_s=time_constant_s,
        name="acceleration_m_s2",
    )
    return _level(rms, _ACCELERATION_REFERENCE_M_S2)


def _slice(size: int, fs_hz: float, interval_s: tuple[float, float]) -> slice:
    """The samples of a ``(start, end)`` stretch of a record, in seconds."""
    start_s, end_s = (float(bound) for bound in interval_s)
    if not (math.isfinite(start_s) and math.isfinite(end_s)) or end_s <= start_s:
        msg = (
            "an interval must be a finite (start, end) with end > start; "
            f"got {interval_s!r}."
        )
        raise ValueError(msg)
    first = round(start_s * fs_hz)
    last = round(end_s * fs_hz)
    if first < 0 or last > size:
        msg = (
            f"the interval {interval_s!r} runs outside the record, which is "
            f"{size / fs_hz:g} s long."
        )
        raise ValueError(msg)
    if last <= first:
        msg = f"the interval {interval_s!r} holds no sample of the record."
        raise ValueError(msg)
    return slice(first, last)


def interval_rms(
    values: ArrayLike, fs_hz: float, *, interval_s: tuple[float, float]
) -> float:
    r"""The interval r.m.s. of Formula (4), or of Formula (5).

    Formula (4) averages the square of the velocity over the stretch. Handed
    the running r.m.s. of :func:`running_velocity_rms` instead, the same
    average is Formula (5), which Clause 6.1 calls a good approximation of
    Formula (4) and which is what a meter reading its display produces.

    :param values: The velocity or its running r.m.s., in any unit (1-D).
    :param fs_hz: Sampling frequency, in hertz.
    :param interval_s: The stretch ``(start, end)``, in seconds from the start
        of the record.
    :return: :math:`\tilde v_j`, in the unit of *values*.
    :raises ValueError: For a bad record, a non-positive rate, or an interval
        that is empty or runs outside the record.
    """
    x = _record(values, "values")
    fs = require_positive(fs_hz, "fs_hz")
    stretch = x[_slice(x.size, fs, interval_s)]
    return float(np.sqrt(np.mean(stretch**2)))


def event_velocity(interval_rms_mm_s: float, duration_s: float) -> float:
    r"""The event value :math:`v_E` of Formula (8), in mm/s.

    The interval r.m.s. of the whole event referred to one hour,
    :math:`v_E = \tilde v_3 \sqrt{T_3 / 3600\,\mathrm{s}}`: the constant
    velocity that, held for an hour, carries the energy the passage carried.

    :param interval_rms_mm_s: :math:`\tilde v_3`, in millimetres per second.
        Clause 6.2 allows :math:`\tilde v_{F3}` of Formula (5) in its place.
    :param duration_s: :math:`T_3`, in seconds.
    :return: :math:`v_E`, in millimetres per second.
    :raises ValueError: For a negative velocity or a non-positive duration.
    """
    v = float(interval_rms_mm_s)
    if not math.isfinite(v) or v < 0.0:
        msg = f"'interval_rms_mm_s' must be finite and non-negative; got {v!r}."
        raise ValueError(msg)
    duration = require_positive(duration_s, "duration_s")
    return v * math.sqrt(duration / EVENT_REFERENCE_DURATION_S)


def event_velocity_level(interval_rms_mm_s: float, duration_s: float) -> float:
    r"""The event level :math:`L_{vE}` of Formula (9), in dB.

    :math:`20 \lg(\tilde v_3 / v_0) + 10 \lg(T_3 / 3600\,\mathrm{s})`, which
    is :func:`event_velocity` as a level against
    :data:`VELOCITY_LEVEL_REFERENCE_MM_S`.

    :param interval_rms_mm_s: :math:`\tilde v_3`, in millimetres per second,
        positive.
    :param duration_s: :math:`T_3`, in seconds.
    :return: :math:`L_{vE}`, in decibels.
    :raises ValueError: For a non-positive velocity or duration.
    """
    v = require_positive(interval_rms_mm_s, "interval_rms_mm_s")
    duration = require_positive(duration_s, "duration_s")
    return 20.0 * math.log10(v / VELOCITY_LEVEL_REFERENCE_MM_S) + 10.0 * math.log10(
        duration / EVENT_REFERENCE_DURATION_S
    )


def _non_negative(values: ArrayLike, name: str) -> NDArray[np.float64]:
    """A finite, non-empty array with no negative entry."""
    x = require_finite_array(values, name)
    if x.size == 0 or np.any(x < 0.0):
        msg = f"{name!r} must be non-empty and not negative."
        raise ValueError(msg)
    return x


def combined_event_velocity(event_velocities_mm_s: ArrayLike) -> float:
    r"""The event value of every passage in one hour, Formula (10), in mm/s.

    Event values add in square, because each is already the energy of its
    passage spread over the same hour: :math:`v_{E,\mathrm{ges}} =
    \sqrt{\sum v_{En}^2}`.

    :param event_velocities_mm_s: The event values of the passages, in
        millimetres per second.
    :return: :math:`v_{E,\mathrm{ges}}`, in millimetres per second.
    :raises ValueError: For an empty, non-finite or negative input.
    """
    values = _non_negative(event_velocities_mm_s, "event_velocities_mm_s")
    return float(np.sqrt(np.sum(values**2)))


def passage_average_velocity(interval_rms_mm_s: ArrayLike) -> float:
    r"""The energy average of r.m.s. values over repeated passages (Clause 9).

    Clause 9 averages the results of a class of trains energetically, which
    for r.m.s. values is the root of the mean square, :math:`\sqrt{\langle
    \tilde v^2 \rangle}`. The same holds for narrow-band spectra, whose power
    spectral densities average arithmetically line by line.

    :param interval_rms_mm_s: One r.m.s. value per passage, in millimetres per
        second.
    :return: The energy average, in millimetres per second.
    :raises ValueError: For an empty, non-finite or negative input.
    """
    values = _non_negative(interval_rms_mm_s, "interval_rms_mm_s")
    return float(np.sqrt(np.mean(values**2)))


def passage_average_level(
    levels_db: ArrayLike, *, axis: int | None = None
) -> float | NDArray[np.float64]:
    r"""The energy average of levels over repeated passages (Clause 9), in dB.

    :math:`10 \lg \langle 10^{L/10} \rangle`, the level of
    :func:`passage_average_velocity`.

    :param levels_db: The levels of the passages, in decibels. A 2-D array of
        third-octave spectra, one row per passage, averages band by band with
        ``axis=0``.
    :param axis: The axis the passages run along; ``None`` (default) averages
        every value.
    :return: The average level: a float, or one level per band.
    :raises ValueError: For an empty or non-finite input.
    """
    levels = _as_float64(levels_db, "levels_db")
    if levels.size == 0 or not np.all(np.isfinite(levels)):
        msg = "'levels_db' must be non-empty and finite."
        raise ValueError(msg)
    if axis is None:
        return float(energy_mean(levels))
    return np.asarray(energy_mean(levels, axis=int(axis)), dtype=np.float64)


@dataclass(frozen=True)
class AmplitudeDistribution:
    r"""How often each velocity occurred in a stretch, Formula (11).

    :ivar edges_mm_s: The bin edges, in millimetres per second.
    :ivar density_per_mm_s: :math:`p_2(v)`, the amplitude distribution density,
        one value per bin, in 1/(mm/s); it integrates to one.
    :ivar cumulative: :math:`P_2(v)`, its integral up to the upper edge of each
        bin, rising from zero to one.
    """

    edges_mm_s: NDArray[np.float64]
    density_per_mm_s: NDArray[np.float64]
    cumulative: NDArray[np.float64]


def amplitude_distribution(
    velocity_mm_s: ArrayLike, *, bins: int = 101
) -> AmplitudeDistribution:
    """The amplitude distribution of a stretch of velocity (Clause 6.3).

    Clause 6.3 forms it over :math:`T_2` by DIN 55350-23, which is a histogram
    normalised to unit area: equal bins across the range of the stretch.

    :param velocity_mm_s: The velocity of the stretch, in millimetres per
        second (1-D).
    :param bins: How many equal bins span the range of the stretch (default
        101, odd so that zero sits in the middle of one).
    :return: The density and its cumulative function, as an
        :class:`AmplitudeDistribution`.
    :raises ValueError: For a bad record or fewer than two bins.
    """
    x = _record(velocity_mm_s)
    count = int(bins)
    if count < _MIN_BINS:
        msg = f"'bins' must be at least 2; got {bins!r}."
        raise ValueError(msg)
    extent = float(np.max(np.abs(x)))
    if extent <= 0.0:
        extent = 1.0
    density, edges = np.histogram(x, bins=count, range=(-extent, extent), density=True)
    cumulative = np.cumsum(density * np.diff(edges))
    return AmplitudeDistribution(
        edges_mm_s=np.asarray(edges, dtype=np.float64),
        density_per_mm_s=np.asarray(density, dtype=np.float64),
        cumulative=np.asarray(cumulative, dtype=np.float64),
    )


def narrowband_psd(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    resolution_hz: float = NARROWBAND_RESOLUTION_HZ,
) -> SpectralDensityResult:
    r"""The one-sided power spectral density of Formula (12), in (mm/s)²/Hz.

    Clause 7.3.1 asks for blocks of :math:`1/\Delta f`, a Hanning window
    (Formula (18)), at least half a block of overlap and a linear average of
    the blocks, which is the Welch estimate
    :func:`~phonometry.signals.power_spectral_density` makes. Its lines add
    back to the mean square of the stretch, which is Formula (14).

    :param velocity_mm_s: The velocity of the stretch, in millimetres per
        second (1-D).
    :param fs_hz: Sampling frequency, in hertz.
    :param resolution_hz: The line spacing :math:`\Delta f`, in hertz (default
        1,25 Hz). The block holds ``round(fs / resolution)`` samples, so the
        spacing actually used is ``fs`` over that count.
    :return: The spectrum, as a
        :class:`~phonometry.signals.SpectralDensityResult`.
    :raises ValueError: For a bad record, a non-positive rate or resolution, or
        a stretch shorter than one block.
    """
    from ...signals import power_spectral_density

    x = _record(velocity_mm_s)
    fs = require_positive(fs_hz, "fs_hz")
    resolution = require_positive(resolution_hz, "resolution_hz")
    block = round(fs / resolution)
    if block > x.size:
        msg = (
            f"the stretch holds {x.size} samples and one block of "
            f"{resolution:g} Hz resolution needs {block}."
        )
        raise ValueError(msg)
    try:
        return power_spectral_density(x, fs, window="hann", nperseg=block, overlap=0.5)
    except ValueError as exc:
        msg = (
            f"a {resolution:g} Hz resolution at {fs:g} Hz makes a block of "
            f"{block} samples, which the Welch estimate cannot use ({exc})"
        )
        raise ValueError(msg) from exc


def passage_energy_spectral_density(
    psd: ArrayLike, duration_s: float
) -> NDArray[np.float64]:
    r"""The energy spectral density of :math:`T_2`, Formula (13), in (mm/s)²/Hz².

    Formula (13) writes :math:`e_2 = |V_2|^2/4` with the one-sided Fourier
    spectrum :math:`V = 2X` of Formula (16), which is :math:`|X|^2`, the
    two-sided density. Set beside Formula (12) that is :math:`e_2 = G_2 T_2 /
    2`, and it means the lines of :math:`e_2` over positive frequencies add up
    to half the energy of the stretch where the lines of :math:`G_2` add up to
    all of its mean square. This returns the formula as printed.

    :param psd: :math:`G_2`, the power spectral density of the stretch, in
        (mm/s)²/Hz, as :func:`narrowband_psd` gives it.
    :param duration_s: :math:`T_2`, in seconds.
    :return: :math:`e_2` at the same lines, in (mm/s)²/Hz².
    :raises ValueError: For a negative or non-finite density or a non-positive
        duration.
    """
    g = _non_negative(psd, "psd")
    duration = require_positive(duration_s, "duration_s")
    return np.asarray(0.5 * g * duration, dtype=np.float64)


def spectral_density_level(psd: ArrayLike) -> NDArray[np.float64]:
    r"""The level of a power spectral density, as Figure 7 draws it, in dB.

    :math:`10 \lg(G / G_0)` with :math:`G_0 = (5 \cdot 10^{-8}\,\mathrm{m/s})^2
    /\mathrm{Hz}`, the square of :data:`VELOCITY_LEVEL_REFERENCE_MM_S` per
    hertz.

    :param psd: The density, in (mm/s)²/Hz.
    :return: The level at each line, in decibels; ``-inf`` where the density is
        exactly zero.
    :raises ValueError: For a negative or non-finite density.
    """
    g = _non_negative(psd, "psd")
    with np.errstate(divide="ignore"):
        return np.asarray(
            10.0 * np.log10(g / VELOCITY_LEVEL_REFERENCE_MM_S**2), dtype=np.float64
        )


def velocity_psd_from_voltage(
    psd_v2_per_hz: ArrayLike, *, sensitivity_v_per_mm_s: float, gain: float
) -> NDArray[np.float64]:
    r"""A density measured in volts, in the unit of the velocity (Annex A).

    The transducer's transfer coefficient :math:`\kappa_A` and the amplifier's
    gain :math:`\kappa_V` multiply the velocity, so they divide its density in
    square: :math:`G_{vv} = G_{\mathrm{V}} / (\kappa_A^2 \kappa_V^2)`.

    :param psd_v2_per_hz: The density the analyser shows, in V²/Hz.
    :param sensitivity_v_per_mm_s: :math:`\kappa_A`, in volts per millimetre
        per second (Annex A uses 0,030).
    :param gain: :math:`\kappa_V`, the amplifier gain, in volts per volt
        (Annex A uses 10).
    :return: The density of the velocity, in (mm/s)²/Hz.
    :raises ValueError: For a negative or non-finite density or a non-positive
        coefficient.
    """
    g = _non_negative(psd_v2_per_hz, "psd_v2_per_hz")
    kappa_a = require_positive(sensitivity_v_per_mm_s, "sensitivity_v_per_mm_s")
    kappa_v = require_positive(gain, "gain")
    return np.asarray(g / (kappa_a**2 * kappa_v**2), dtype=np.float64)


def _check_resolution(frequencies: NDArray[np.float64]) -> float:
    """The line spacing of a narrow-band axis, held to the one Table 1 is for."""
    steps = np.diff(frequencies)
    if steps.size == 0 or not np.allclose(steps, steps[0], rtol=1e-6, atol=0.0):
        msg = "'frequencies_hz' must be evenly spaced, as a narrow-band spectrum is."
        raise ValueError(msg)
    spacing = float(steps[0])
    if abs(spacing / NARROWBAND_RESOLUTION_HZ - 1.0) > _RESOLUTION_TOLERANCE:
        msg = (
            f"Table 1 counts lines of {NARROWBAND_RESOLUTION_HZ:g} Hz and this "
            f"spectrum is spaced {spacing:g} Hz; form it with "
            "narrowband_psd(..., resolution_hz=1.25)."
        )
        raise ValueError(msg)
    return spacing


def third_octaves_from_narrowband(
    frequencies_hz: ArrayLike, psd: ArrayLike
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    r"""Add a narrow-band spectrum back into third octaves, Formula (23).

    Each band takes the number of lines Table 1 gives it, and the band r.m.s.
    is the square root of their summed power, :math:`\sqrt{\sum G(f_k)\,
    \Delta f}`. The table gives the counts and not the lines, so the choice is
    stated here: the lines nearest the nominal centre on a logarithmic axis.
    Wherever the count is what a sixth of an octave either side of the centre
    holds, which is every band but two, those are exactly the lines inside the
    band's nominal edges; at 10 Hz and 12,5 Hz, where the table departs from
    the edges, they are 10 and 11,25 Hz, then 12,5 and 13,75 Hz.

    It is a rule of nominal bands and it behaves like one. Nominal edges do
    not meet: six lines fall between two bands and are in neither (71,25 Hz,
    141,25 Hz and 142,5 Hz, and 353,75 Hz to 356,25 Hz), and five are in two
    (178,75 Hz, 223,75 Hz, and 446,25 Hz to 448,75 Hz). The bands therefore
    do not add up to the spectrum exactly, and a tone that sits in one of the
    gaps is in no band at all; that is the comparability the table buys.

    A band is returned only if the spectrum holds all its lines: a spectrum
    that starts above the lowest bands or stops inside a band leaves those
    bands out rather than filling them with the lines of a neighbour.

    :param frequencies_hz: The line frequencies of the spectrum, in hertz,
        evenly spaced at 1,25 Hz.
    :param psd: The one-sided power spectral density at those lines, in
        (mm/s)²/Hz.
    :return: ``(centres, rms)``: the nominal centres of the bands the spectrum
        holds whole, from :data:`THIRD_OCTAVE_LINES`, in hertz, and the band
        r.m.s. in each, in mm/s.
    :raises ValueError: For mismatched or non-finite inputs, a negative
        density, uneven spacing, or a spacing Table 1 is not written for.
    """
    f = require_finite_array(frequencies_hz, "frequencies_hz")
    g = require_finite_array(psd, "psd")
    if f.ndim != 1 or f.shape != g.shape:
        msg = "'frequencies_hz' and 'psd' must be 1-D with one value per line."
        raise ValueError(msg)
    if np.any(g < 0.0):
        msg = "'psd' must not be negative; a power spectral density never is."
        raise ValueError(msg)
    spacing = _check_resolution(f)
    # The selection is made on the spectrum's own grid extended by the widest
    # band either way, so a band that would reach for a line the spectrum does
    # not hold is seen to, and left out, instead of borrowing a neighbour's.
    margin = max(THIRD_OCTAVE_LINES.values())
    below = f[0] - spacing * np.arange(margin, 0, -1)
    below = below[below > 0.0]
    above = f[-1] + spacing * np.arange(1, margin + 1)
    grid = np.concatenate([below, f, above])
    log_grid = np.log(np.where(grid > 0.0, grid, np.inf))
    first = below.size
    centres: list[float] = []
    rms: list[float] = []
    for nominal, lines in THIRD_OCTAVE_LINES.items():
        distance = np.abs(log_grid - math.log(nominal))
        chosen = np.argsort(distance, kind="stable")[:lines]
        if np.min(chosen) < first or np.max(chosen) >= first + f.size:
            continue
        centres.append(nominal)
        rms.append(float(np.sqrt(np.sum(g[chosen - first]) * spacing)))
    return np.asarray(centres, dtype=np.float64), np.asarray(rms, dtype=np.float64)


def elastic_insertion_loss(
    levels_before_db: ArrayLike, levels_after_db: ArrayLike
) -> NDArray[np.float64]:
    r"""The insertion loss :math:`D_e(f_{Tn})` of Annex B, Formula (B.1), in dB.

    The drop in the third-octave structure-borne level at one point of a
    transmission path when an elastic element is built in. Annex B says it and
    it bears repeating: the value belongs to the point it was measured at. The
    difference spectrum of Formula (B.2) is the same subtraction between any
    two spectra.

    :param levels_before_db: The third-octave levels before, in decibels.
    :param levels_after_db: The levels after, at the same point, in decibels.
    :return: :math:`L_1 - L_2` per band, positive where the element reduces
        the level.
    :raises ValueError: If the two do not match band for band.
    """
    before = require_finite_array(levels_before_db, "levels_before_db")
    after = require_finite_array(levels_after_db, "levels_after_db")
    if before.shape != after.shape:
        msg = "'levels_before_db' and 'levels_after_db' must match band for band."
        raise ValueError(msg)
    return np.asarray(before - after, dtype=np.float64)


def band_sum_level(levels_db: ArrayLike) -> float:
    r"""The sum level :math:`\Sigma L` of a spectrum, Annex B, Formula (B.3).

    :math:`10 \lg \sum 10^{0,1 L(f_{Tn})}`, the energy sum of the bands.

    :param levels_db: The band levels, in decibels.
    :return: :math:`\Sigma L`, in decibels.
    :raises ValueError: For an empty or non-finite input.
    """
    levels = require_finite_array(levels_db, "levels_db")
    if levels.size == 0:
        msg = "'levels_db' must not be empty."
        raise ValueError(msg)
    return float(energy_sum(levels))


def centred_interval(
    velocity_mm_s: ArrayLike, fs_hz: float, *, duration_s: float = T1_DURATION_S
) -> tuple[float, float]:
    """The stretch :math:`T_1` of Clause 5 a), centred on the largest amplitude.

    Clause 5 a) asks for the largest vibration to sit about in the middle of
    :math:`T_1`, and this puts it exactly there, or as near as the record
    allows: a stretch that would run off either end is moved back inside it
    rather than cut, so it keeps its length.

    :param velocity_mm_s: The velocity, in millimetres per second (1-D).
    :param fs_hz: Sampling frequency, in hertz.
    :param duration_s: The length of the stretch, in seconds (default 4 s).
    :return: ``(start, end)``, in seconds from the start of the record. A
        record shorter than *duration_s* is returned whole.
    :raises ValueError: For a bad record or a non-positive rate or duration.
    """
    x = _record(velocity_mm_s)
    fs = require_positive(fs_hz, "fs_hz")
    record_s = x.size / fs
    duration = min(require_positive(duration_s, "duration_s"), record_s)
    peak_s = float(np.argmax(np.abs(x))) / fs
    start = min(max(0.0, peak_s - 0.5 * duration), record_s - duration)
    return start, start + duration


@dataclass(frozen=True)
class TrainPassage:
    r"""One passage reduced the way Clauses 5 to 7 reduce it.

    :ivar velocity_mm_s: The velocity the meter's railway band limitation
        leaves, one value per sample.
    :ivar running_rms_mm_s: :math:`\tilde v_F(t)` of it.
    :ivar peak_velocity_mm_s: :math:`v_\mathrm{max}`, the largest absolute
        velocity of the passage (Clause 6.3).
    :ivar running_rms_max_mm_s: :math:`\tilde v_{F\mathrm{max}}`, the maximum
        of the running r.m.s.
    :ivar kbf_max: :math:`KB_{F\mathrm{max}}`, the maximum of the weighted
        severity of DIN 45669-1 over the same stretch, which DIN 4150-2 reads.
    :ivar interval_rms_mm_s: :math:`\tilde v_1`, :math:`\tilde v_2` and
        :math:`\tilde v_3` of Formula (4), in that order.
    :ivar intervals_s: The three stretches ``(start, end)``, in seconds.
    :ivar event_velocity_mm_s: :math:`v_E` of Formula (8), from :math:`T_3`.
    :ivar event_level_db: :math:`L_{vE}` of Formula (9).
    :ivar band_centres_hz: The nominal third-octave centres analysed.
    :ivar band_interval_levels_db: :math:`L_{vFj}(f_{Tn})` of Formula (6), one
        row per stretch, :math:`T_1` to :math:`T_3`.
    :ivar band_max_levels_db: :math:`L_{vF\mathrm{max}}(f_{Tn})` of Formula
        (7), over :math:`T_3`.
    :ivar fs_hz: The sampling frequency of the record.
    """

    velocity_mm_s: NDArray[np.float64]
    running_rms_mm_s: NDArray[np.float64]
    peak_velocity_mm_s: float
    running_rms_max_mm_s: float
    kbf_max: float
    interval_rms_mm_s: tuple[float, float, float]
    intervals_s: tuple[tuple[float, float], ...]
    event_velocity_mm_s: float
    event_level_db: float
    band_centres_hz: NDArray[np.float64]
    band_interval_levels_db: NDArray[np.float64]
    band_max_levels_db: NDArray[np.float64]
    fs_hz: float

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the running level with the three stretches marked on it.

        Requires matplotlib (``pip install phonometry[plot]``). The spectra of
        Figure 6 are :meth:`plot_spectrum`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_train_passage`.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_train_passage

        check_language(language)
        return plot_train_passage(self, ax=ax, language=language, **kwargs)

    def plot_spectrum(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the interval and maximum third-octave levels, as Figure 6 does.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_train_passage_spectrum`.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_train_passage_spectrum

        check_language(language)
        return plot_train_passage_spectrum(self, ax=ax, language=language, **kwargs)


def _band_running_rms(
    x: NDArray[np.float64], fs: float, upper_band_hz: float
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The third octaves of Clause 7.2 and the running r.m.s. in each."""
    from ...filters import OctaveFilterBank

    rate = round(fs)
    if not math.isclose(rate, fs, rel_tol=0.0, abs_tol=1e-9):
        msg = (
            f"the third-octave bank needs an integer sampling frequency; got {fs!r} Hz."
        )
        raise ValueError(msg)
    with warnings.catch_warnings():
        # A band the rate cannot carry is dropped by the bank with a warning,
        # and the check below turns that into the error it is here.
        warnings.simplefilter("ignore", UserWarning)
        bank = OctaveFilterBank(
            rate, fraction=3, limits=[PASSAGE_BANDS_HZ[0], upper_band_hz]
        )
    if not math.isclose(float(bank.nominal_freq[-1]), upper_band_hz):
        msg = (
            f"a sampling frequency of {fs:g} Hz cannot carry the "
            f"{upper_band_hz:g} Hz third octave; raise it above twice the "
            "band's upper edge."
        )
        raise ValueError(msg)
    _levels, _centres, bands = bank.filter(
        x, sigbands=True, calculate_level=False, detrend=False
    )
    band_rms = np.vstack(
        [_exponential_running_rms(np.asarray(band), fs) for band in bands]
    )
    nominal = np.asarray(
        [float(label) for label in bank.nominal_freq], dtype=np.float64
    )
    return nominal, band_rms


def _stretch_bounds(
    x: NDArray[np.float64],
    fs: float,
    t1_s: tuple[float, float] | None,
    t2_s: tuple[float, float],
    t3_s: tuple[float, float] | None,
) -> tuple[slice, slice, slice]:
    """The samples of :math:`T_1`, :math:`T_2` and :math:`T_3`, checked."""
    t2 = _slice(x.size, fs, t2_s)
    if t1_s is None:
        t2_duration = (t2.stop - t2.start) / fs
        start, end = centred_interval(
            x[t2], fs, duration_s=min(T1_DURATION_S, t2_duration)
        )
        offset = t2.start / fs
        t1 = _slice(x.size, fs, (start + offset, end + offset))
    else:
        t1 = _slice(x.size, fs, t1_s)
    if t1.stop - t1.start > t2.stop - t2.start:
        msg = "T1 may be as long as T2 and no longer (Clause 5 a))."
        raise ValueError(msg)
    t3 = _slice(x.size, fs, (0.0, x.size / fs) if t3_s is None else t3_s)
    if not (t3.start <= t2.start <= t1.start and t1.stop <= t2.stop <= t3.stop):
        msg = (
            "the stretches nest as Figure 2 draws them: T1 inside T2 and T2 inside T3."
        )
        raise ValueError(msg)
    return t1, t2, t3


def evaluate_train_passage(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    t2_s: tuple[float, float],
    t1_s: tuple[float, float] | None = None,
    t3_s: tuple[float, float] | None = None,
    upper_band_hz: float = PASSAGE_BANDS_HZ[1],
) -> TrainPassage:
    r"""Reduce one passage to the quantities of Clauses 5 to 7.

    The record goes through the band limitation of the DIN 45669-1 railway
    working range first, as it does inside the meter, and every quantity is
    read from what is left: the running r.m.s. and its maximum, the peak, the
    interval r.m.s. of the three stretches, the event value, the weighted
    severity DIN 4150-2 reads, and the third-octave levels of Figure 6.

    :param velocity_mm_s: The velocity of the passage as the transducer gives
        it, in millimetres per second (1-D).
    :param fs_hz: Sampling frequency, in hertz: an integer, for the
        third-octave bank, and high enough to carry the 315 Hz range.
    :param t2_s: :math:`T_2`, the passage itself, ``(start, end)`` in seconds.
        Clause 5 b) reads it off the record, from about a quarter of the most
        frequent maxima back down to the same amplitude, which is a judgement
        about the record, so it is asked for rather than guessed.
    :param t1_s: :math:`T_1`; ``None`` (default) centres four seconds on the
        largest amplitude inside :math:`T_2`, or all of :math:`T_2` when that
        is shorter. An explicit one may not be longer than :math:`T_2`.
    :param t3_s: :math:`T_3`; ``None`` (default) takes the whole record.
    :param upper_band_hz: The highest third octave, a nominal centre in hertz:
        315 (default) or down to 80, the special case of DIN 45672-1.
    :return: The reduced passage, as a :class:`TrainPassage`.
    :raises ValueError: For a bad record, a rate the chain or the upper band
        cannot take, a stretch outside the record, stretches that do not nest
        or a :math:`T_1` longer than :math:`T_2`, or an upper band that is not
        a nominal centre from 80 Hz to 315 Hz.
    """
    raw = _record(velocity_mm_s)
    fs = _sample_rate(fs_hz, "railway")
    upper = float(upper_band_hz)
    allowed = [
        nominal
        for nominal in THIRD_OCTAVE_LINES
        if _UPPER_BAND_RANGE_HZ[0] <= nominal <= _UPPER_BAND_RANGE_HZ[1]
    ]
    if not any(math.isclose(upper, nominal) for nominal in allowed):
        msg = (
            "'upper_band_hz' must be a nominal third-octave centre from 80 Hz "
            f"to 315 Hz; got {upper_band_hz!r}."
        )
        raise ValueError(msg)
    x = np.asarray(
        sig.sosfilt(_sos("railway", fs, weighted=False), raw), dtype=np.float64
    )
    stretches = _stretch_bounds(x, fs, t1_s, t2_s, t3_s)
    t3 = stretches[2]

    running = running_velocity_rms(x, fs)
    rms = tuple(float(np.sqrt(np.mean(x[s] ** 2))) for s in stretches)
    duration_3 = (t3.stop - t3.start) / fs
    centres, band_rms = _band_running_rms(x, fs, upper)
    interval_levels = np.vstack(
        [
            _level(
                np.sqrt(np.mean(band_rms[:, s] ** 2, axis=1)),
                VELOCITY_LEVEL_REFERENCE_MM_S,
            )
            for s in stretches
        ]
    )
    kbf = kbf_signal(raw, fs, working_range="railway")
    return TrainPassage(
        velocity_mm_s=x,
        running_rms_mm_s=running,
        peak_velocity_mm_s=float(np.max(np.abs(x[t3]))),
        running_rms_max_mm_s=float(np.max(running[t3])),
        kbf_max=float(np.max(kbf[t3])),
        interval_rms_mm_s=(rms[0], rms[1], rms[2]),
        intervals_s=tuple((s.start / fs, s.stop / fs) for s in stretches),
        event_velocity_mm_s=event_velocity(rms[2], duration_3),
        event_level_db=(
            event_velocity_level(rms[2], duration_3) if rms[2] > 0.0 else -math.inf
        ),
        band_centres_hz=centres,
        band_interval_levels_db=interval_levels,
        band_max_levels_db=_level(
            np.max(band_rms[:, t3], axis=1), VELOCITY_LEVEL_REFERENCE_MM_S
        ),
        fs_hz=fs,
    )
