#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""IEC 61260-1:2014 band-filter class verification.

Acceptance limits on relative attenuation transcribed from the
official text (BS EN 61260-1:2014, **Table 1**, standard pages 15-16):
octave-band breakpoint frequencies with class 1 and class 2 minimum/maximum
limits. Fractional-octave-band breakpoints are derived with Formulas (9) and
(10) (subclauses 5.10.3-5.10.4) and limits between breakpoints are interpolated
linearly in :math:`\log_{10} \Omega` per Formula (11) (subclause 5.10.6).
Relative attenuation is
:math:`\Delta A(\Omega) = A(\Omega) - A_{\mathrm{ref}}` (Formula 8) with
:math:`A = L_{\mathrm{in}} - L_{\mathrm{out}}`
(Formula 7); here :math:`A_{\mathrm{ref}}` is the attenuation at the exact
mid-band frequency
(subclause 5.9: the pass-band reference attenuation).

IEC 61260-1:2014 defines only classes 1 and 2. **Class 0** (the tightest,
laboratory-grade class) lives only in the withdrawn **IEC 61260:1995 /
EN 61260:1995 Table 1** and its US twin **ANSI S1.11-2004 Table 1**, whose
class 1/2 masks differ numerically from the 2014 edition (e.g. the 2014
pass-band reference tolerance is ±0.4 dB for class 1 vs ±0.3 dB in 1995, and
the 2014 stop-band edge minimum is +1.2 dB vs +2.0 dB in 1995). The two editions
are therefore kept as separate mask tables selected by the ``edition`` argument
(``"2014"`` default -> classes 1/2; ``"1995"`` -> classes 0/1/2). The 1995 /
ANSI-2004 octave-band table was transcribed digit-for-digit and cross-checked
between the two standards (they agree exactly).

One subject: the class of a band-filter design, graded against what IEC
61260-1:2014 requires of the transfer function of a set of filters, with the
effective bandwidth and the summation run the way IEC 61260-2:2016 (pattern
evaluation) tests them, or against what IEC 61260:1995 requires and run the
way its clause 5 tests it. The relative attenuation is graded further than
IEC 61260-2:2016 7.2.2.2 measures it, which is from 0.5 times the lowest to
1.5 times the highest mid-band frequency of the set: every band is read up to
:math:`f_\mathrm{s}/2`, on the requirement of IEC 61260-1:2014 5.15 and
Table 1 themselves.

The transfer function graded is the one the bank has at its input rate. A
band the bank decimates by :math:`M` runs its input through a linear-phase
anti-aliasing filter, keeps one sample in :math:`M` and filters at
:math:`f_\mathrm{s}/M`; a tone of frequency :math:`f` therefore comes out at
:math:`f` folded about the multiples of :math:`f_\mathrm{s}/M`, scaled by the
anti-aliasing filter at :math:`f` and the band's sections at the folded
frequency. Every frequency below :math:`f_\mathrm{s}/2` is graded that way,
the images the decimation folds onto the band included. IEC 61260-1:2014
5.15 asks the anti-aliasing filters to keep the aliased components inside the
Table 1 limits, and Table 1 covers every frequency. IEC 61260:1995 4.8 asks
them to keep the relative attenuation from exceeding the greatest of the
applicable minimum limits of Table 1, and 5.7 tests it with a tone at the
decimated sampling frequency minus the mid-band frequency. The images are
graded against the Table 1 corridor at their input frequency in both
editions, which for the 1995 edition is the same floor: a decimated band
keeps :math:`f_\mathrm{s}/(2M)` at least sixteen times its upper band-edge
frequency, so every image lies past the last breakpoint of the mask, where
the minimum limit is the greatest one.

Besides the Table 1 mask there are two more requirements, both computed from
the same response:

* **Effective bandwidth deviation** (61260-1 5.11 and 5.12). The normalized
  effective bandwidth :math:`B_\mathrm{e}` is the integral of Formula (13),
  :math:`\int (1/\Omega)\,10^{-0.1\,\Delta A(\Omega)}\,\mathrm{d}\Omega`,
  evaluated as IEC 61260-2 7.2.3.2 recommends: by the trapezoidal rule of its
  Formula (2) over the test frequencies of its Formula (1),
  :math:`\Omega_i = G^{i/(bS)}`, with :math:`S \ge 24` frequencies per
  bandwidth (7.2.1.4). Its deviation from the reference
  :math:`B_\mathrm{r} = (1/b)\ln G` (Formula (15)) is
  :math:`\Delta B = 10\lg(B_\mathrm{e}/B_\mathrm{r})` (Formula (16)), within
  :math:`\pm 0.4` dB for class 1 and :math:`\pm 0.6` dB for class 2 (5.12.2).
  The 1995 edition calls the same quotient the **filter integrated
  response** (4.5) and builds it differently: its equation (14) integrates
  :math:`10^{-0.1\,\Delta A}` over :math:`f/f_\mathrm{m}` with no
  :math:`1/\Omega` weight, by the trapezoidal rule of equation (16) with
  :math:`N \ge 5S` (5.4.2), against
  :math:`B_\mathrm{r} = G^{1/(2b)} - G^{-1/(2b)}` (equation (9)), within
  :math:`\pm 0.15`, :math:`\pm 0.3` and :math:`\pm 0.5` dB for classes 0, 1
  and 2 (4.5.3). Its :math:`S` is raised in steps of 12 until the integrated
  response of every band is independent of it to the nearest tenth of a
  decibel (5.3.3), and the summation runs at the same :math:`S`.
* **Summation of output signals** (61260-1 5.16). At the test frequencies
  :math:`\Omega_i`, :math:`|i| \le \lfloor S/2 \rfloor`, inside a band, the
  outputs of that band and of its two neighbours are summed on an energy
  basis, IEC 61260-2 Formula (3):
  :math:`\Delta P_j = 10\lg\left[10^{-0.1\,\Delta A_{j-1}} +
  10^{-0.1\,\Delta A_j} + 10^{-0.1\,\Delta A_{j+1}}\right]`, for every band
  that has a neighbour on both sides (7.2.4.4). The limits are
  :math:`+0.8` dB and :math:`-1.8` dB for class 1 and :math:`+1.8` dB and
  :math:`-3.8` dB for class 2. They are applied to Formula (3) as printed,
  as 7.2.4.5 instructs; the words of 7.2.4.3 and of 5.16 name the difference
  the other way round, "input minus reference attenuation, and the summed
  output", which with limits this asymmetric is not the same test (see the
  errata registry). The 1995 edition prints the same sum as equation (19)
  (5.8.3), with the same conflict between its words and the formula, and
  runs it "from the lowest midband frequency to the highest midband
  frequency of the filter set" (5.8.4): its end bands are read on the half
  facing the set, where the neighbour the set lacks adds nothing. Its limits
  are :math:`\pm 1.0` dB for class 0, :math:`+1.0` dB and :math:`-2.0` dB for
  class 1 and :math:`+2.0` dB and :math:`-4.0` dB for class 2 (4.9).

The time-invariant operation of 5.14, tested with an exponential sweep
(IEC 61260-2 7.4), is :func:`phonometry.filters.verify_time_invariance`: it
runs the bank itself, decimation included, rather than reading its transfer
functions.

The acceptance limits of the A/B/C/AU/Z frequency weightings, which qualify a
network applied to the whole signal against a design-goal response, live in
:mod:`phonometry.filters.weighting_compliance`.
"""

from __future__ import annotations

import math
from dataclasses import KW_ONLY, dataclass
from functools import cached_property
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy import signal

from .._internal.frozen import (
    OwnsArrays,
    frozen_rows,
    read_only,
    reduce_with_plain_rows,
)
from .._internal.validation import (
    check_engine,
    require_choice,
    require_count,
    require_ranks,
    require_same_length,
)
from .core import _multirate_lowpass

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from matplotlib.axes import Axes

    from .._report.metadata import ReportMetadata
    from .core import OctaveFilterBank

__all__ = [
    "FilterComplianceResult",
    "class_limits",
    "verify_filter_class",
]

_G = 10 ** (3 / 10)

# Fewest per-band frequency-grid points the class verification accepts.
_MIN_GRID_POINTS = 16

#: IEC 61260-2:2016 7.2.1.4: the number S of test frequencies per filter
#: bandwidth "shall be not less than 24".
_MIN_POINTS_PER_BANDWIDTH = 24

#: IEC 61260:1995 5.3.3: S is raised "in steps of 12 until the calculated
#: filter integrated response is independent of S to the nearest tenth of a
#: decibel".
_POINTS_PER_BANDWIDTH_STEP_1995 = 12

#: The largest S the raise of IEC 61260:1995 5.3.3 is carried to. A response
#: whose limit sits on a rounding boundary of a tenth of a decibel need never
#: read the same tenth twice running; it is taken at this S, sixteen times
#: the least, where the trapezoidal sum of equation (16) of an octave,
#: one-third-octave or one-twenty-fourth-octave band of any of the library's
#: designs, of order 2 to 12, is within 0.0001 dB of its value at four times
#: that S.
_MAX_POINTS_PER_BANDWIDTH_1995 = 16 * _MIN_POINTS_PER_BANDWIDTH

#: The acceptance limits, +/- dB per class, on the deviation of a band's
#: effective bandwidth from its reference bandwidth: IEC 61260-1:2014 5.12.2
#: (the effective bandwidth deviation) and IEC 61260:1995 4.5.3 (the filter
#: integrated response), by edition.
_BANDWIDTH_LIMITS_DB: Mapping[str, Mapping[int, float]] = MappingProxyType(
    {
        "2014": MappingProxyType({1: 0.4, 2: 0.6}),
        "1995": MappingProxyType({0: 0.15, 1: 0.3, 2: 0.5}),
    }
)

#: The acceptance limits (lower, upper), dB per class, on the summation of the
#: output signals: IEC 61260-1:2014 5.16 and IEC 61260:1995 4.9, by edition.
_SUMMATION_LIMITS_DB: Mapping[str, Mapping[int, tuple[float, float]]] = (
    MappingProxyType(
        {
            "2014": MappingProxyType({1: (-1.8, 0.8), 2: (-3.8, 1.8)}),
            "1995": MappingProxyType({0: (-1.0, 1.0), 1: (-2.0, 1.0), 2: (-4.0, 2.0)}),
        }
    )
)

#: The least half-width of the trapezoidal integration of the effective
#: bandwidth, in filter bandwidths: :math:`N \ge 2S` test frequencies on each
#: side in IEC 61260-2:2016 7.2.3.2, :math:`N \ge 5S` in IEC 61260:1995 5.4.2.
_INTEGRATION_BANDWIDTHS: Mapping[str, int] = MappingProxyType({"2014": 2, "1995": 5})

#: The names of the requirements a design verdict can carry, with the key
#: template their per-band margins are stored under.
_REQUIREMENTS: Mapping[str, str] = MappingProxyType(
    {
        "relative_attenuation": "margin_class{c}_db",
        "effective_bandwidth": "bandwidth_margin_class{c}_db",
        "summation": "summation_margin_class{c}_db",
    }
)

# BS EN 61260-1:2014 Table 1, high side (Omega >= 1), as exponents x of the
# octave-band normalized frequency G**x with (min, max) limits per class.
# The low side mirrors these at 1/Omega (Formula 10). The band-edge rows
# G**(1/2 - epsilon) and G**(1/2 + epsilon) encode the discontinuity at the
# edge: the pass-band segment carries the max limits, the stop-band segment
# the min limits.
#
# Pass-band max limits (min is constant -0.4 dB class 1 / -0.6 dB class 2):
_PASSBAND_MAX: list[tuple[float, float, float]] = [
    # (exponent, class 1 max, class 2 max)
    (0.0, 0.4, 0.6),  # band centre (Omega of 1)
    (1 / 8, 0.5, 0.7),
    (1 / 4, 0.7, 0.9),
    (3 / 8, 1.4, 1.7),
    (1 / 2, 5.3, 5.8),  # G**(1/2) - epsilon
]
_PASSBAND_MIN = {1: -0.4, 2: -0.6}

# Stop-band min limits (max is +inf):
_STOPBAND_MIN: list[tuple[float, float, float]] = [
    # (exponent, class 1 min, class 2 min)
    (1 / 2, 1.2, 0.8),  # G**(1/2) + epsilon
    (1.0, 16.6, 15.6),
    (2.0, 40.5, 39.5),
    (3.0, 60.0, 54.0),
    (4.0, 70.0, 60.0),  # and >= G**4: constant
]

# EN 61260:1995 / IEC 61260:1995 Table 1 == ANSI S1.11-2004 Table 1 (verified
# identical digit-for-digit between both standards). Same layout as the 2014
# tables above, plus a class-0 column. Pass-band min is constant per class. The
# fractional-octave breakpoint mapping is the same as the 2014 edition: 1995
# Annex B equation (10) is identical to 2014 Formula (9), so _map_breakpoint is
# reused unchanged for both editions.
_PASSBAND_MAX_1995: list[tuple[float, float, float, float]] = [
    # (exponent, class 0 max, class 1 max, class 2 max)
    (0.0, 0.15, 0.3, 0.5),  # band centre (Omega of 1)
    (1 / 8, 0.2, 0.4, 0.6),
    (1 / 4, 0.4, 0.6, 0.8),
    (3 / 8, 1.1, 1.3, 1.6),
    (1 / 2, 4.5, 5.0, 5.5),  # G**(1/2) - epsilon
]
_PASSBAND_MIN_1995 = {0: -0.15, 1: -0.3, 2: -0.5}
_STOPBAND_MIN_1995: list[tuple[float, float, float, float]] = [
    # (exponent, class 0 min, class 1 min, class 2 min)
    (1 / 2, 2.3, 2.0, 1.6),  # G**(1/2) + epsilon
    (1.0, 18.0, 17.5, 16.5),
    (2.0, 42.5, 42.0, 41.0),
    (3.0, 62.0, 61.0, 55.0),
    (4.0, 75.0, 70.0, 60.0),  # and >= G**4: constant
]

# Per-edition mask spec: ordered classes (best -> worst), the three limit tables
# and the column index of each class within the (exponent, ...) rows.
_FILTER_EDITIONS: dict[str, dict[str, Any]] = {
    "2014": {
        "classes": (1, 2),
        "passband_max": _PASSBAND_MAX,
        "passband_min": _PASSBAND_MIN,
        "stopband_min": _STOPBAND_MIN,
        "col": {1: 1, 2: 2},
    },
    "1995": {
        "classes": (0, 1, 2),
        "passband_max": _PASSBAND_MAX_1995,
        "passband_min": _PASSBAND_MIN_1995,
        "stopband_min": _STOPBAND_MIN_1995,
        "col": {0: 1, 1: 2, 2: 3},
    },
}


def _map_breakpoint(exponent: float, fraction: float) -> float:
    r"""Map an octave-band breakpoint :math:`G^x` to a fractional-octave one.

    BS EN 61260-1:2014 Formula (9): the high-frequency breakpoint for
    bandwidth designator 1/b is

    .. math::

       1 + \frac{G^{1/(2b)} - 1}{G^{1/2} - 1}
       \left( \Omega_\mathrm{h}(1/1) - 1 \right)
    """
    omega_octave = _G**exponent
    scale = (_G ** (1 / (2 * fraction)) - 1) / (_G**0.5 - 1)
    return float(1 + scale * (omega_octave - 1))


def class_limits(
    fraction: float, filter_class: int, omega: np.ndarray, *, edition: str = "2014"
) -> tuple[np.ndarray, np.ndarray]:
    r"""Acceptance limits on relative attenuation at normalized frequencies.

    :param fraction: Bandwidth designator denominator b (1 for octave,
        3 for one-third octave, ...).
    :param filter_class: Performance class: 1 or 2 for ``edition="2014"``;
        0, 1 or 2 for ``edition="1995"``.
    :param omega: Normalized frequencies :math:`f/f_\mathrm{m}` (> 0).
    :param edition: ``"2014"`` (IEC 61260-1:2014, classes 1/2) or ``"1995"``
        (IEC 61260:1995 / ANSI S1.11-2004, classes 0/1/2).
    :return: Tuple (minimum, maximum) relative attenuation in dB per point;
        the maximum is ``+inf`` outside the pass-band.

    .. note::
        The exact band-edge point :math:`\Omega = G^{1/2}` is treated as
        pass-band.
        The 1995 edition's Table 1 prints a dedicated minimum (+2.3/+2.0/
        +1.6 dB) *at* that single frequency, which this convention relaxes to
        the pass-band minimum; the discrepancy has measure zero -- any
        continuous response violating the edge row is caught at
        :math:`\text{edge} + \epsilon`
        by the interpolated stop-band mask. The 2014 edition defines only
        the :math:`G^{1/2} - \epsilon` and :math:`G^{1/2} + \epsilon`
        rows, which the masks match
        exactly.
    """
    spec = _FILTER_EDITIONS.get(edition)
    if spec is None:
        msg = "edition must be '2014' or '1995'."
        raise ValueError(msg)
    if filter_class not in spec["classes"]:
        msg = f"filter_class must be one of {spec['classes']} for edition '{edition}'."
        raise ValueError(msg)
    if fraction <= 0:
        msg = "'fraction' must be positive."
        raise ValueError(msg)
    col = spec["col"][filter_class]
    passband_max = spec["passband_max"]
    stopband_min = spec["stopband_min"]

    omega_arr = np.asarray(omega, dtype=np.float64)
    if np.any(omega_arr <= 0):
        msg = "Normalized frequencies must be positive."
        raise ValueError(msg)
    # Formula (10): low side mirrors the high side.
    omega_h = np.where(omega_arr < 1.0, 1.0 / omega_arr, omega_arr)

    pass_x = np.array([_map_breakpoint(row[0], fraction) for row in passband_max])
    pass_y = np.array([row[col] for row in passband_max])
    stop_x = np.array([_map_breakpoint(row[0], fraction) for row in stopband_min])
    stop_y = np.array([row[col] for row in stopband_min])

    edge = pass_x[-1]  # mapped G**(1/2): the band-edge frequency ratio
    in_pass = omega_h <= edge

    minimum = np.empty_like(omega_h)
    maximum = np.empty_like(omega_h)

    # Pass-band: constant min, interpolated max (linear in lg(Omega), Formula 11).
    minimum[in_pass] = spec["passband_min"][filter_class]
    maximum[in_pass] = np.interp(np.log10(omega_h[in_pass]), np.log10(pass_x), pass_y)

    # Stop-band: interpolated min (constant beyond the last breakpoint), max +inf.
    lg = np.log10(omega_h[~in_pass])
    minimum[~in_pass] = np.interp(lg, np.log10(stop_x), stop_y)
    maximum[~in_pass] = np.inf

    return minimum, maximum


def _test_frequencies(
    fraction: float, points_per_bandwidth: int, first: int, last: int
) -> np.ndarray:
    r"""IEC 61260-2:2016 Formula (1): :math:`\Omega_i = G^{i/(bS)}`, ``first..last``.

    :param fraction: The bandwidth designator denominator ``b``.
    :param points_per_bandwidth: ``S``, the test frequencies per bandwidth.
    :param first: The first index ``i`` (negative below the mid-band).
    :param last: The last index ``i``, included.
    :return: The normalized test frequencies, in ascending order.
    """
    i = np.arange(first, last + 1, dtype=np.float64)
    return np.asarray(_G ** (i / (fraction * points_per_bandwidth)))


#: The machine epsilon, the spacing of doubles at 1: added to a gain, it keeps
#: the logarithm of a zero gain finite.
_EPS = float(np.finfo(float).eps)

#: How many alias images of a decimated band are read in one batch: each is a
#: zoom transform of the band's anti-aliasing filter, and a batch holds that
#: many of them in memory at once.
_IMAGE_BATCH = 16


def _anti_alias_gain(
    factor: int, fs_hz: float, frequencies_hz: np.ndarray
) -> np.ndarray:
    r"""The magnitude of a band's anti-aliasing filter at the bank's input rate.

    :param factor: The band's decimation factor; 1 has no such filter.
    :param fs_hz: The bank's input sampling rate.
    :param frequencies_hz: Where to evaluate it.
    :return: :math:`|H_\mathrm{aa}(f)|`, one per frequency.
    """
    freqs = np.asarray(frequencies_hz, dtype=np.float64)
    if factor == 1:
        return np.ones(freqs.shape)
    _, h = signal.freqz(_multirate_lowpass(factor), worN=freqs, fs=fs_hz)
    return np.asarray(np.abs(h))


def _band_gain(
    sos: np.ndarray, factor: int, fs_hz: float, frequencies_hz: np.ndarray
) -> np.ndarray:
    r"""The magnitude response of one band, decimation included, at the input rate.

    A tone of frequency :math:`f` at the input of the bank goes through the
    band's anti-aliasing filter at the input rate and is then sampled at
    :math:`f_\mathrm{s}/M`, where the band's sections see it folded about
    multiples of that rate. :func:`scipy.signal.sosfreqz` at that rate is
    periodic in it, so the sections evaluated at :math:`f` itself read the
    folded frequency, and the band's output is the product of the two.

    :param sos: The band's second-order sections, designed at ``fs / factor``.
    :param factor: The band's decimation factor :math:`M`.
    :param fs_hz: The bank's input sampling rate.
    :param frequencies_hz: Input frequencies.
    :return: :math:`|H_\mathrm{aa}(f)\,H_\mathrm{b}(f)|`.
    """
    freqs = np.asarray(frequencies_hz, dtype=np.float64)
    _, h = signal.sosfreqz(sos, worN=freqs, fs=fs_hz / factor)
    return np.asarray(_anti_alias_gain(factor, fs_hz, freqs) * np.abs(h))


def _reference_attenuation_db(
    sos: np.ndarray, factor: int, fs_hz: float, mid_hz: float
) -> float:
    """The attenuation of one band at its exact mid-band frequency, dB.

    The reference attenuation of Formula (8) of IEC 61260-1:2014 and of
    equation (8) of IEC 61260:1995, as :func:`verify_filter_class` takes it.
    """
    gain = float(_band_gain(sos, factor, fs_hz, np.array([mid_hz]))[0])
    return -20.0 * math.log10(gain + _EPS)


def _band_relative_attenuation(
    sos: np.ndarray,
    factor: int,
    fs_hz: float,
    mid_hz: float,
    frequencies_hz: np.ndarray,
) -> np.ndarray:
    """Relative attenuation of one designed band at arbitrary frequencies, dB.

    Formula (8) of IEC 61260-1:2014 with the attenuation at the exact
    mid-band frequency as reference, read off the response the band has at
    the bank's input rate (:func:`_band_gain`), the alias images its
    decimation folds onto it included. A frequency at or above half the
    input rate is one no input of the bank can hold, and reads as infinite
    attenuation.

    :param sos: The band's second-order sections.
    :param factor: The band's decimation factor.
    :param fs_hz: The bank's input sampling rate.
    :param mid_hz: Its exact mid-band frequency.
    :param frequencies_hz: Where to evaluate it.
    :return: The relative attenuation, ``+inf`` where no input reaches.
    """
    freqs = np.asarray(frequencies_hz, dtype=np.float64)
    out = np.full(freqs.shape, np.inf)
    reachable = (freqs > 0.0) & (freqs < fs_hz / 2.0)
    if np.any(reachable):
        # The mid-band frequency rides along, so the reference costs no
        # second pass over the taps of the anti-aliasing filter.
        gain = _band_gain(sos, factor, fs_hz, np.append(freqs[reachable], mid_hz))
        a_ref = -20.0 * np.log10(gain[-1] + _EPS)
        out[reachable] = -20.0 * np.log10(gain[:-1] + _EPS) - a_ref
    return out


@dataclass(frozen=True)
class _BandGrid:
    r"""One band read on the frequency grid of :func:`verify_filter_class`.

    ``num_points`` frequencies cover the band's decimated half-band,
    :math:`[0, f_\mathrm{s}/(2M))`, at the spacing
    :math:`f_\mathrm{s}/(2M\,\mathrm{num\_points})`; the alias images
    above it are read at the same spacing, on the frequencies that fold onto
    the same points.

    :ivar sos: The band's second-order sections.
    :ivar factor: Its decimation factor :math:`M`.
    :ivar fs_hz: The bank's input sampling rate.
    :ivar mid_hz: Its exact mid-band frequency.
    :ivar num_points: Points per decimated half-band.
    """

    sos: np.ndarray
    factor: int
    fs_hz: float
    mid_hz: float
    num_points: int

    @property
    def rate_hz(self) -> float:
        """The band's decimated sampling rate."""
        return self.fs_hz / self.factor

    @property
    def spacing_hz(self) -> float:
        """The grid spacing, the same in the half-band and in every image."""
        return self.rate_hz / (2.0 * self.num_points)

    @cached_property
    def reference_db(self) -> float:
        """The attenuation at the exact mid-band frequency."""
        return _reference_attenuation_db(self.sos, self.factor, self.fs_hz, self.mid_hz)

    @cached_property
    def folded_gain(self) -> np.ndarray:
        """The sections' magnitude at the folded points ``0 .. num_points``.

        Point ``j`` is the frequency ``j * spacing`` of the decimated
        half-band, its Nyquist frequency included; every image frequency
        folds onto one of them. The anti-aliasing filter is not in it.
        """
        g = np.arange(self.num_points + 1) * self.spacing_hz
        _, h = signal.sosfreqz(self.sos, worN=g, fs=self.rate_hz)
        return read_only(np.abs(h))

    def baseband(self) -> tuple[np.ndarray, np.ndarray]:
        """The band below its decimated Nyquist frequency, anti-aliasing included.

        :return: ``(frequencies_hz, relative_attenuation_db)`` on the grid
            points of ``(0, fs / (2 M))``.
        """
        g = np.arange(1, self.num_points) * self.spacing_hz
        gain = self.folded_gain[1 : self.num_points]
        if self.factor > 1:
            taps = _multirate_lowpass(self.factor)
            zoom = signal.ZoomFFT(
                taps.size,
                [self.spacing_hz, self.num_points * self.spacing_hz],
                m=self.num_points - 1,
                fs=self.fs_hz,
            )
            gain = gain * np.abs(zoom(taps))
        return g, -20.0 * np.log10(gain + _EPS) - self.reference_db

    def images(self, first: int, last: int) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        r"""The alias images, on the frequencies that fold onto points ``first .. last``.

        Image ``k`` is the input band around :math:`k f_\mathrm{s}/M`: an
        input at :math:`k f_\mathrm{s}/M \pm g` is sampled onto :math:`g`.
        Read are the frequencies on either side of every
        :math:`k f_\mathrm{s}/M` below half the input rate whose :math:`g`
        is ``first .. last`` grid steps. The anti-aliasing filter is read
        there exactly, with one zoom transform of its taps shifted by
        :math:`k f_\mathrm{s}/M` per image and side.

        :param first: The first folded point (>= 0).
        :param last: The last folded point (<= ``num_points``).
        :return: One ``(frequencies_hz, relative_attenuation_db)`` per image
            and side.
        """
        if self.factor == 1 or last < first:
            return
        taps = _multirate_lowpass(self.factor)
        spacing = self.spacing_hz
        steps = np.arange(first, last + 1, dtype=np.float64)
        folded = self.folded_gain[first : last + 1]
        a_ref = self.reference_db
        size = steps.size
        sides = (
            (
                signal.ZoomFFT(
                    taps.size,
                    [first * spacing, (last + 1) * spacing],
                    m=size,
                    fs=self.fs_hz,
                ),
                1.0,
            ),
            (
                signal.ZoomFFT(
                    taps.size,
                    [-last * spacing, (1 - first) * spacing],
                    m=size,
                    fs=self.fs_hz,
                ),
                -1.0,
            ),
        )
        t = np.arange(taps.size)
        nyquist = self.fs_hz / 2.0
        shifts = np.arange(1, self.factor // 2 + 1)
        for start in range(0, shifts.size, _IMAGE_BATCH):
            batch = shifts[start : start + _IMAGE_BATCH]
            shifted = taps * np.exp(-2j * np.pi * np.outer(batch, t) / self.factor)
            for zoom, sign in sides:
                gain = np.abs(zoom(shifted, axis=-1))
                if sign < 0:
                    # The zoom runs from -last to -first steps: reverse it
                    # to line it up with the folded points first .. last.
                    gain = gain[:, ::-1]
                for row, k in zip(gain, batch, strict=True):
                    freqs = k * self.rate_hz + sign * steps * spacing
                    keep = freqs < nyquist
                    attenuation = -20.0 * np.log10(row * folded + _EPS) - a_ref
                    yield freqs[keep], attenuation[keep]


def _mask_margin(
    fraction: float,
    filter_class: int,
    omega: np.ndarray,
    delta_a: np.ndarray,
    edition: str,
) -> float:
    """The smallest distance, dB, of a relative attenuation to the Table 1 corridor.

    Negative where the attenuation leaves it, on either side.
    """
    if omega.size == 0:
        return math.inf
    minimum, maximum = class_limits(fraction, filter_class, omega, edition=edition)
    low = float(np.min(delta_a - minimum))
    finite = np.isfinite(maximum)
    high = (
        float(np.min(maximum[finite] - delta_a[finite])) if np.any(finite) else math.inf
    )
    return min(low, high)


def _image_window(
    grid: _BandGrid,
    margins: dict[int, float],
    spec: Mapping[str, Any],
    fraction: float,
) -> tuple[int, int]:
    r"""The folded points whose images can still bind a band's verdict.

    An image point folds onto a point :math:`g` of the half-band, where the
    band's sections alone attenuate by :math:`A_\mathrm{b}(g)` relative to
    the mid-band; the anti-aliasing filter can add gain to that by no more
    than the sum of the magnitudes of its taps, and the limit an image point
    is held to is no more than the class's largest minimum of Table 1 (the
    one at and beyond :math:`G^{\pm 4}`). An image point whose
    :math:`A_\mathrm{b}(g)` clears that limit by more than the margin the
    band already has, after that gain, therefore cannot lower the margin,
    and is not read. The rest are, every one, so the margin is the exact
    minimum over the whole grid. A band whose pass band reaches its
    decimated Nyquist frequency has image points the bound does not cover,
    and all of them are read.

    :return: ``(first, last)`` folded points to read; ``last < first`` when
        none can bind.
    """
    if grid.factor == 1:
        return 0, -1
    edge = _map_breakpoint(spec["passband_max"][-1][0], fraction)
    if grid.rate_hz / 2.0 <= edge * grid.mid_hz:
        return 0, grid.num_points
    taps = _multirate_lowpass(grid.factor)
    gain_db = 20.0 * math.log10(float(np.sum(np.abs(taps))))
    threshold = gain_db + max(
        spec["stopband_min"][-1][spec["col"][cls]] + margin
        for cls, margin in margins.items()
    )
    folded = -20.0 * np.log10(grid.folded_gain + _EPS) - grid.reference_db
    alive = np.nonzero(folded < threshold)[0]
    if alive.size == 0:
        return 0, -1
    return int(alive[0]), int(alive[-1])


def _effective_bandwidth(
    omega: np.ndarray, relative_attenuation_db: np.ndarray
) -> float:
    r"""IEC 61260-2:2016 Formula (2): the trapezoidal :math:`B_\mathrm{e}`.

    .. math::

       B_\mathrm{e} = \sum_i \frac{2}{\Omega_i + \Omega_{i+1}}\,
       \frac{1}{2}\left[10^{-0.1\,\Delta A(\Omega_i)} +
       10^{-0.1\,\Delta A(\Omega_{i+1})}\right]
       \left[\Omega_{i+1} - \Omega_i\right]

    which is Formula (14) of IEC 61260-1:2014, the integral of
    :math:`(1/\Omega)\,10^{-0.1\,\Delta A}`, with the weight
    :math:`1/\Omega` taken at the arithmetic mean of each interval. An
    infinite attenuation contributes nothing.

    :param omega: The ascending normalized test frequencies.
    :param relative_attenuation_db: :math:`\Delta A` at each of them.
    :return: The normalized effective bandwidth.
    """
    power = 10.0 ** (-0.1 * np.asarray(relative_attenuation_db, dtype=np.float64))
    lo, hi = omega[:-1], omega[1:]
    return float(np.sum(2.0 / (lo + hi) * 0.5 * (power[:-1] + power[1:]) * (hi - lo)))


def _effective_bandwidth_1995(
    omega: np.ndarray, relative_attenuation_db: np.ndarray
) -> float:
    r"""IEC 61260:1995 equation (16): the trapezoidal :math:`B_\mathrm{e}`.

    .. math::

       B_\mathrm{e} = \sum_{i=-N}^{N} \frac{1}{2}
       \left\{10^{-0.1\,\Delta A(f_i/f_\mathrm{m})} +
       10^{-0.1\,\Delta A(f_{i+1}/f_\mathrm{m})}\right\}
       \left[(f_{i+1}/f_\mathrm{m}) - (f_i/f_\mathrm{m})\right]

    the integral of equation (14),
    :math:`\int_0^\infty 10^{-0.1\,\Delta A(f/f_\mathrm{m})}\,
    \mathrm{d}(f/f_\mathrm{m})`, which, unlike Formula (14) of the 2014
    edition, carries no :math:`1/\Omega` weight. An infinite attenuation
    contributes nothing.

    :param omega: The ascending normalized test frequencies :math:`f_i/f_\mathrm{m}`.
    :param relative_attenuation_db: :math:`\Delta A` at each of them.
    :return: The normalized effective bandwidth.
    """
    power = 10.0 ** (-0.1 * np.asarray(relative_attenuation_db, dtype=np.float64))
    return float(np.sum(0.5 * (power[:-1] + power[1:]) * np.diff(omega)))


def _reference_bandwidth(fraction: float) -> float:
    r"""IEC 61260-1:2014 Formula (15): :math:`B_\mathrm{r} = (1/b)\ln G`."""
    return math.log(_G) / fraction


def _reference_bandwidth_1995(fraction: float) -> float:
    r"""IEC 61260:1995 equation (9): :math:`B_\mathrm{r} = G^{1/(2b)} - G^{-1/(2b)}`.

    The bandwidth between the band-edge frequencies over the exact mid-band
    frequency, :math:`(f_2 - f_1)/f_\mathrm{m}`.
    """
    return float(_G ** (1.0 / (2.0 * fraction)) - _G ** (-1.0 / (2.0 * fraction)))


#: Per edition: the trapezoidal integration of the effective bandwidth and the
#: reference bandwidth its deviation is taken against.
_BANDWIDTH_INTEGRALS: Mapping[str, tuple[Any, Any]] = MappingProxyType(
    {
        "2014": (_effective_bandwidth, _reference_bandwidth),
        "1995": (_effective_bandwidth_1995, _reference_bandwidth_1995),
    }
)


def _summation_deviation(relative_attenuations_db: np.ndarray) -> np.ndarray:
    r"""IEC 61260-2:2016 Formula (3) and IEC 61260:1995 equation (19), point by point.

    :math:`\Delta P_j = 10\lg\left[\sum 10^{-0.1\,\Delta A}\right]` over the
    filters :math:`j-1`, :math:`j`, :math:`j+1` at one frequency.

    :param relative_attenuations_db: Shape ``(n_filters, n)``: the relative
        attenuation of each filter summed at the same ``n`` frequencies.
    :return: :math:`\Delta P_j` at each frequency, dB.
    """
    power = 10.0 ** (-0.1 * np.asarray(relative_attenuations_db, dtype=np.float64))
    return np.asarray(10.0 * np.log10(np.sum(power, axis=0)))


def _bank_bandwidth_deviation(
    sos: np.ndarray,
    factor: int,
    fs_hz: float,
    mid_hz: float,
    fraction: float,
    points_per_bandwidth: int,
    edition: str = "2014",
) -> float:
    r"""The deviation :math:`\Delta B` of one designed band's effective bandwidth.

    The effective bandwidth deviation of IEC 61260-1:2014 5.12 or the filter
    integrated response of IEC 61260:1995 4.5, both
    :math:`10\lg(B_\mathrm{e}/B_\mathrm{r})` but with the effective and the
    reference bandwidths of their own edition. The test frequencies
    :math:`\Omega_i = G^{i/(bS)}` run from :math:`-N` to :math:`N + 1`,
    :math:`N` at least :math:`2S` (IEC 61260-2:2016 7.2.3.2) or :math:`5S`
    (IEC 61260:1995 5.4.2) and wide enough to reach the outermost breakpoint
    of Table 1 (:math:`G^{\pm 4}` carried to the bandwidth), past which a
    band that meets any class attenuates by 60 dB or more and the integrand
    is at most :math:`10^{-6}` of its pass-band value.
    """
    outermost = _map_breakpoint(_STOPBAND_MIN[-1][0], fraction)
    reach = math.ceil(fraction * points_per_bandwidth * math.log(outermost, _G))
    n = max(_INTEGRATION_BANDWIDTHS[edition] * points_per_bandwidth, reach)
    omega = _test_frequencies(fraction, points_per_bandwidth, -n, n + 1)
    delta_a = _band_relative_attenuation(sos, factor, fs_hz, mid_hz, omega * mid_hz)
    effective, reference = _BANDWIDTH_INTEGRALS[edition]
    return 10.0 * math.log10(effective(omega, delta_a) / reference(fraction))


def _settled_points_per_bandwidth(
    bank: OctaveFilterBank, points_per_bandwidth: int
) -> int:
    r"""IEC 61260:1995 5.3.3: the S at which every band's integrated response has settled.

    S starts at *points_per_bandwidth* and is raised in steps of 12 while the
    filter integrated response of any band, :math:`\Delta B` of 4.5.1, read
    to the nearest tenth of a decibel, changes from S to S + 12. The S
    returned is the first at which none does, and the summation runs at it
    too: 5.8.2 takes its S "from the relative attenuation tests", which
    5.3.3 has raised. It stops at :data:`_MAX_POINTS_PER_BANDWIDTH_1995`.

    :param bank: The filter bank graded.
    :param points_per_bandwidth: The S to start from, at least 24.
    :return: The S the 1995 tests run at.
    """
    factors = tuple(int(f) for f in bank.factor)
    fs = float(bank.fs)
    mids = np.asarray(bank.freq, dtype=np.float64)

    def tenths(s: int) -> list[int]:
        return [
            round(
                10.0
                * _bank_bandwidth_deviation(
                    bank.sos[idx],
                    factors[idx],
                    fs,
                    float(mids[idx]),
                    bank.fraction,
                    s,
                    "1995",
                )
            )
            for idx in range(bank.num_bands)
        ]

    s = points_per_bandwidth
    current = tenths(s)
    while s < _MAX_POINTS_PER_BANDWIDTH_1995:
        following = tenths(s + _POINTS_PER_BANDWIDTH_STEP_1995)
        if following == current:
            break
        s += _POINTS_PER_BANDWIDTH_STEP_1995
        current = following
    return s


def _summation_span(
    band: int, num_bands: int, points_per_bandwidth: int, edition: str
) -> tuple[int, int]:
    r"""The indices :math:`i` of the summation test frequencies of one band.

    :math:`i` runs from :math:`-M` to :math:`M`, :math:`M = \lfloor S/2
    \rfloor` (IEC 61260-2:2016 7.2.4.2, IEC 61260:1995 5.8.2), the
    frequencies between the band edges. IEC 61260:1995 5.8.4 runs the test
    "from the lowest midband frequency to the highest midband frequency of
    the filter set", so the lowest band is read from its mid-band frequency
    up and the highest from its mid-band frequency down; IEC 61260-2:2016
    7.2.4.4 leaves both out.
    """
    half = points_per_bandwidth // 2
    first = 0 if edition == "1995" and band == 0 else -half
    last = 0 if edition == "1995" and band == num_bands - 1 else half
    return first, last


def _bank_summation(
    sos: tuple[np.ndarray, ...] | list[np.ndarray],
    factors: tuple[int, ...] | list[int] | np.ndarray,
    fs_hz: float,
    mids_hz: np.ndarray,
    fraction: float,
    points_per_bandwidth: int,
    band: int,
    edition: str = "2014",
) -> tuple[np.ndarray, np.ndarray]:
    r"""The summation curve of one band: :math:`\Omega_i` and :math:`\Delta P_j`.

    Formula (3) of IEC 61260-2:2016, equation (19) of IEC 61260:1995, over
    the test frequencies of :func:`_summation_span`. Each filter is
    evaluated at the same frequency in hertz, which is the normalized
    frequency :math:`G^{i/(bS) \pm 1/b}` the two standards give for the
    neighbours of a set whose mid-band frequencies step by :math:`G^{1/b}`.
    A neighbour the set does not have (below the lowest band or above the
    highest) adds nothing.

    :return: ``(omega, delta_p_db)`` for the band.
    """
    count = len(mids_hz)
    first, last = _summation_span(band, count, points_per_bandwidth, edition)
    omega = _test_frequencies(fraction, points_per_bandwidth, first, last)
    freqs = omega * float(mids_hz[band])
    rows = np.vstack(
        [
            _band_relative_attenuation(
                sos[k], int(factors[k]), fs_hz, float(mids_hz[k]), freqs
            )
            for k in (band - 1, band, band + 1)
            if 0 <= k < count
        ]
    )
    return omega, _summation_deviation(rows)


def _summation_graded(band: int, num_bands: int, edition: str) -> bool:
    """Whether one band carries the summation requirement in its edition.

    IEC 61260-2:2016 7.2.4.4 grades the bands with a neighbour on each side;
    IEC 61260:1995 5.8.4 every band of a set of two or more, between the
    lowest and the highest mid-band frequency.
    """
    if edition == "1995":
        return num_bands > 1
    return 0 < band < num_bands - 1


def _verify_band(
    bank: OctaveFilterBank,
    idx: int,
    classes_ordered: tuple[int, ...],
    breakpoint_omegas: np.ndarray,
    edition: str,
    num_points: int,
) -> dict[str, Any]:
    """Grade one band on Table 1 at the full input rate; return its entry.

    The relative attenuation is read on the band's decimated half-band, on
    the Table 1 breakpoints exactly and on the alias images of the half-band
    up to half the input rate (:class:`_BandGrid`, :func:`_image_window`).
    """
    fm = float(bank.freq[idx])
    fs = float(bank.fs)
    grid = _BandGrid(
        np.asarray(bank.sos[idx], dtype=np.float64),
        int(bank.factor[idx]),
        fs,
        fm,
        num_points,
    )
    nyquist = fs / 2.0
    freqs, delta_a = grid.baseband()
    # The Table 1 breakpoints (pass-band included) are read exactly, not off
    # the grid, so a coarse grid cannot smooth a dip across them.
    extra = breakpoint_omegas * fm
    extra = extra[(extra > 0.0) & (extra < nyquist)]
    if extra.size:
        freqs = np.concatenate([freqs, extra])
        delta_a = np.concatenate(
            [delta_a, _band_relative_attenuation(grid.sos, grid.factor, fs, fm, extra)]
        )
    margins = {
        cls: _mask_margin(bank.fraction, cls, freqs / fm, delta_a, edition)
        for cls in classes_ordered
    }
    spec = _FILTER_EDITIONS[edition]
    first, last = _image_window(grid, margins, spec, bank.fraction)
    for image_freqs, image_delta in grid.images(first, last):
        for cls in classes_ordered:
            margins[cls] = min(
                margins[cls],
                _mask_margin(
                    bank.fraction, cls, image_freqs / fm, image_delta, edition
                ),
            )

    band_entry: dict[str, Any] = {"freq": fm, "checked_to_omega": nyquist / fm}
    for cls in classes_ordered:
        band_entry[f"margin_class{cls}_db"] = margins[cls]
    return band_entry


def _grade_pattern_requirements(
    bank: OctaveFilterBank,
    bands: list[dict[str, Any]],
    classes_ordered: tuple[int, ...],
    points_per_bandwidth: int,
    edition: str,
) -> None:
    """Add the effective bandwidth and the summation to every band entry, in place.

    Each band gets the deviation of its effective bandwidth and its margin
    to each class's limits; each band the summation applies to
    (:func:`_summation_graded`) gets the range of its summation curve and
    its margins too, and the others carry ``None``. The band's class, the
    strictest class it meets on every requirement graded, is read from these
    margins by :attr:`FilterComplianceResult.bands`.
    """
    factors = tuple(int(f) for f in bank.factor)
    fs = float(bank.fs)
    mids = np.asarray(bank.freq, dtype=np.float64)
    bandwidth_limits = _BANDWIDTH_LIMITS_DB[edition]
    summation_limits = _SUMMATION_LIMITS_DB[edition]
    for idx, band in enumerate(bands):
        deviation = _bank_bandwidth_deviation(
            bank.sos[idx],
            factors[idx],
            fs,
            float(mids[idx]),
            bank.fraction,
            points_per_bandwidth,
            edition,
        )
        band["bandwidth_deviation_db"] = deviation
        for cls in classes_ordered:
            band[f"bandwidth_margin_class{cls}_db"] = bandwidth_limits[cls] - abs(
                deviation
            )
        if _summation_graded(idx, len(bands), edition):
            _, curve = _bank_summation(
                bank.sos,
                factors,
                fs,
                mids,
                bank.fraction,
                points_per_bandwidth,
                idx,
                edition,
            )
            low, high = float(np.min(curve)), float(np.max(curve))
            band["summation_min_db"] = low
            band["summation_max_db"] = high
            for cls in classes_ordered:
                lower, upper = summation_limits[cls]
                band[f"summation_margin_class{cls}_db"] = min(low - lower, upper - high)
        else:
            band["summation_min_db"] = None
            band["summation_max_db"] = None
            for cls in classes_ordered:
                band[f"summation_margin_class{cls}_db"] = None


def _band_class(
    band: Mapping[str, Any], classes_ordered: tuple[int, ...]
) -> int | None:
    """The strictest class one band meets on every requirement it carries."""
    for cls in classes_ordered:
        margins = [
            band.get(template.format(c=cls)) for template in _REQUIREMENTS.values()
        ]
        if all(m is None or m >= 0.0 for m in margins):
            return cls
    return None


def verify_filter_class(
    bank: OctaveFilterBank,
    *,
    num_points: int = 2**15,
    edition: str = "2014",
    points_per_bandwidth: int = _MIN_POINTS_PER_BANDWIDTH,
) -> FilterComplianceResult:
    r"""Verify a filter bank against the IEC 61260 class limits.

    Each band's relative attenuation (referenced to the attenuation at its
    exact mid-band frequency) is checked against every acceptance-limit
    class of the selected edition's Table 1, on the response the band has
    at the bank's input rate: its anti-aliasing filter, the decimation and
    its sections, so that every alias image the decimation folds onto the
    band is graded where the input carries it. Table 1 covers every
    frequency (its last rows read :math:`\le G^{-4}` and :math:`\ge G^{+4}`),
    and a sampled input holds every frequency below half its sampling rate,
    so that is the range graded: ``num_points`` frequencies cover the
    band's decimated half-band and the images above it are read at the same
    spacing, up to half the input rate. The Table 1 breakpoint frequencies
    in that range are always evaluated exactly, so the pass-band
    constraints are checked even on a coarse grid. Above half the input
    rate no input of the bank has a frequency, and the Table 1 limits there
    are not demonstrated: the returned ``range_limited`` flag is set
    whenever a band's outermost breakpoint (:math:`G^{4}`, carried to the
    bandwidth) lies beyond half the input rate, and the per-band
    ``checked_to_omega`` records how far the check reached.

    Two more requirements are graded on the same sections, the effective
    bandwidth and the summation of the output signals, each in its edition's
    own form (see the module docstring): for ``edition="2014"`` the
    effective bandwidth deviation of IEC 61260-1:2014 5.12 of every band and
    the summation of 5.16 of every band with a neighbour on each side, the
    way IEC 61260-2:2016 tests them; for ``edition="1995"`` the filter
    integrated response of IEC 61260:1995 4.5.3 of every band and the
    summation of 4.9 from the lowest to the highest mid-band frequency, the
    way its clauses 5.4 and 5.8 test them. A band's class, and so the
    bank's, is the strictest class met on every requirement graded;
    :meth:`FilterComplianceResult.requirement_class` gives the class of each
    requirement on its own.

    :param bank: The filter bank to verify (its designed SOS are analyzed;
        works for stateful and stateless banks alike).
    :param num_points: Number of frequency grid points per band on its
        decimated half-band (>= 16); the alias images are read at the same
        spacing.
    :param edition: ``"2014"`` (IEC 61260-1:2014, classes 1/2) or ``"1995"``
        (IEC 61260:1995, adds the stricter class 0).
    :param points_per_bandwidth: ``S``, the test frequencies per filter
        bandwidth of IEC 61260-2:2016 Formula (1) and IEC 61260:1995
        equation (15), at least 24 (7.2.1.4 and 5.3.3). For
        ``edition="1995"`` it is where S starts: 5.3.3 raises it in steps of
        12 until the filter integrated response of every band reads the same
        to the nearest tenth of a decibel at S and at S + 12, and the
        result's ``points_per_bandwidth`` says where it stopped.
    :return: A :class:`FilterComplianceResult`, which carries the verdict
        together with the sections, mid-band frequencies, decimation factors
        and sampling rate it was measured through, so it can redraw the
        relative attenuation and render an accredited ``.report()`` fiche
        without keeping a reference to the (possibly stateful) bank.
    """
    if num_points < _MIN_GRID_POINTS:
        msg = "'num_points' must be at least 16."
        raise ValueError(msg)
    points_per_bandwidth = require_count(
        points_per_bandwidth, "points_per_bandwidth", minimum=_MIN_POINTS_PER_BANDWIDTH
    )
    spec = _FILTER_EDITIONS.get(edition)
    if spec is None:
        msg = "edition must be '2014' or '1995'."
        raise ValueError(msg)
    classes_ordered: tuple[int, ...] = spec["classes"]  # best -> worst

    # Table 1 breakpoints (both sides) that must always be evaluated.
    rows = list(spec["passband_max"]) + list(spec["stopband_min"])
    breakpoint_omegas = np.array(
        [_map_breakpoint(row[0], bank.fraction) for row in rows]
    )
    breakpoint_omegas = np.concatenate([1.0 / breakpoint_omegas, breakpoint_omegas])

    bands = [
        _verify_band(bank, idx, classes_ordered, breakpoint_omegas, edition, num_points)
        for idx in range(bank.num_bands)
    ]
    if edition == "1995":
        points_per_bandwidth = _settled_points_per_bandwidth(bank, points_per_bandwidth)
    _grade_pattern_requirements(
        bank, bands, classes_ordered, points_per_bandwidth, edition
    )

    return FilterComplianceResult(
        band_margins=tuple(bands),
        fraction=int(bank.fraction),
        edition=edition,
        sos=tuple(np.asarray(s, dtype=np.float64) for s in bank.sos),
        band_frequencies=np.asarray(bank.freq, dtype=np.float64),
        factors=tuple(int(f) for f in bank.factor),
        fs=float(bank.fs),
        num_points=int(num_points),
        points_per_bandwidth=points_per_bandwidth,
    )


def _margin_classes(band: Mapping[str, Any]) -> list[int]:
    """The classes one band verdict carries margins for, read off its keys."""
    prefix, suffix = "margin_class", "_db"
    return sorted(
        int(key[len(prefix) : -len(suffix)])
        for key in band
        if key.startswith(prefix) and key.endswith(suffix)
    )


def _require_margin_classes(
    bands: tuple[Mapping[str, Any], ...], edition: str, expected: list[int]
) -> None:
    """Pin the margin keys of every band to the classes the edition defines.

    Two things reach here. A verdict verified against the other edition: its
    bands carry that edition's margin keys, so the corridor would be drawn
    from the wrong table under this edition's title. And a band list whose
    entries disagree among themselves, which reading only the first band let
    through: :meth:`FilterComplianceResult.plot` and the ``.report()`` fiche
    read ``margin_class<c>_db`` out of *every* band, so one later band short
    of the key dies in a bare ``KeyError`` halfway through the figure.

    :raises ValueError: if a band carries margins for other classes than
        ``expected`` (in any order).
    """
    wanted = sorted(expected)
    for band in bands:
        carried = _margin_classes(band)
        if carried != wanted:
            msg = (
                f"'edition' ({edition!r}) defines classes {expected}, but the "
                f"{band.get('freq', math.nan):g} Hz entry of 'band_margins' carries "
                f"margins for classes {carried}."
            )
            raise ValueError(msg)


def _require_requirement_keys(
    bands: tuple[Mapping[str, Any], ...], classes: list[int]
) -> None:
    """Every band carries the same requirements, or none of them does.

    A requirement is graded for the whole set or not at all:
    :attr:`FilterComplianceResult.requirements` reads the first band, and a
    later band short of one of its margins would die in a bare ``KeyError``
    in the fiche.

    :raises ValueError: if the bands disagree on which requirements they
        carry.
    """
    if not bands or not classes:
        return
    for name, template in _REQUIREMENTS.items():
        key = template.format(c=classes[0])
        carried = [key in band for band in bands]
        if any(carried) and not all(carried):
            missing = next(b for b, has in zip(bands, carried, strict=True) if not has)
            msg = (
                f"'band_margins' must carry the {name!r} requirement in every band or "
                f"in none; the {missing.get('freq', math.nan):g} Hz entry has "
                f"no {key!r}."
            )
            raise ValueError(msg)


@dataclass(frozen=True)
class FilterComplianceResult(OwnsArrays):
    r"""IEC 61260-1 class-compliance verdict of an :class:`OctaveFilterBank`.

    What :func:`verify_filter_class` returns: the verdict together with the
    minimal filter-bank data needed to redraw the measured relative-attenuation
    curve, so the result exposes the standard ``plot`` / ``report`` pair without
    holding a reference to the (possibly stateful) bank.

    The classes and the range are read from the per-band margins and the
    edition's Table 1, so they are not fields: a verdict cannot be built to
    state a class its margins do not reach.

    :ivar band_margins: What each band was measured to, without its class:
        one ``{"freq", "checked_to_omega", "margin_class<c>_db", ...}`` per
        band, as an immutable tuple of read-only rows, copied at construction
        so a write into a caller's dictionary cannot move the verdict;
        :attr:`bands` adds the class each band reaches.
    :ivar fraction: Bandwidth designator ``b`` (1 for octave, 3 for
        one-third-octave).
    :ivar edition: ``"2014"`` (IEC 61260-1:2014, classes 1/2) or ``"1995"``
        (IEC 61260:1995 / ANSI S1.11-2004, classes 0/1/2).
    :ivar sos: Per-band second-order sections of the analysed bank (one array
        per band), kept so the relative attenuation can be recomputed
        exactly as the verifier does.
    :ivar band_frequencies: The exact mid-band frequencies ``f_m`` in Hz.
    :ivar factors: Per-band decimation factor; the band's processing sample
        rate is ``fs / factor`` (the multirate rate the SOS were designed at)
        and the factor fixes its anti-aliasing filter. Stored because the
        response is evaluated through both, which the verifier's public
        return does not otherwise expose.
    :ivar fs: The bank's full sampling rate in Hz.
    :ivar num_points: Frequency grid points per band used by the verification,
        retained so the redrawn curve matches the analysed grid.
    :ivar points_per_bandwidth: ``S``, the test frequencies per bandwidth of
        IEC 61260-2:2016 Formula (1) (IEC 61260:1995 equation (15)) the
        effective bandwidth and the summation were evaluated on; in the 1995
        edition, the S that 5.3.3 raised the one asked for to.

    Every band entry carries, besides its Table 1 margins
    ``margin_class<c>_db``, the two requirements its edition tests on the
    same measurements:

    * ``bandwidth_deviation_db``, the effective bandwidth deviation
      :math:`\Delta B` of 5.12 (the filter integrated response of 4.5 in the
      1995 edition), and ``bandwidth_margin_class<c>_db``, its distance to
      each class's limit;
    * ``summation_min_db`` and ``summation_max_db``, the range of the
      summation :math:`\Delta P_j` of 5.16 (4.9 in the 1995 edition) across
      the band, and ``summation_margin_class<c>_db``, the nearer of its
      distances to each class's two limits; all three are ``None`` on a band
      the summation does not apply to: in the 2014 edition the first and the
      last band, which have a neighbour on one side only (IEC 61260-2
      7.2.4.4), in the 1995 edition the one band of a single-band bank.

    A band's ``class`` is then the strictest class it meets on all of them.
    """

    band_margins: tuple[Mapping[str, Any], ...]
    fraction: int
    edition: str
    sos: tuple[np.ndarray, ...]
    band_frequencies: np.ndarray
    factors: tuple[int, ...]
    fs: float
    num_points: int
    _: KW_ONLY
    points_per_bandwidth: int = _MIN_POINTS_PER_BANDWIDTH

    def __post_init__(self) -> None:
        """Reject a verdict whose per-band entries disagree.

        The fiche prints one row per band and, in its box, the overall class
        of the whole bank, so a band list short of an entry gives a sheet
        whose verdict covers a band that is nowhere in its table.

        The edition is pinned against the margins the bands carry, because
        the two travel together: the plot and the fiche pick the corridor
        from :attr:`edition` and read ``margin_class<c>_db`` out of every
        band. A verdict whose edition disagrees with its margin keys would
        draw the other edition's corridor under this edition's title. Every
        band is checked, not just the first: :func:`verify_filter_class`
        fills each entry from the same list of classes, so a band list whose
        entries disagree among themselves is one no bank produced.

        A band carries no class of its own: the class is read from its
        margins (:attr:`bands`), so a row that states one is refused rather
        than believed or silently replaced.

        The per-band numbers are pinned finite. Every margin comes from a
        ``min`` over the measured relative attenuation against the Table 1
        mask, so no bank emits a NaN here; one smuggled in through
        :func:`dataclasses.replace` would print ``Class 1 (+nan dB)`` in the
        per-band table.

        :raises ValueError: if the per-band entries disagree, the edition is
            unknown or does not match the per-band margin keys, a band states
            a class, or a per-band value is not finite.
        """
        object.__setattr__(self, "band_margins", frozen_rows(self.band_margins))
        require_ranks(self, band_frequencies=1)
        require_same_length(self, "band_margins", "sos", "band_frequencies", "factors")
        require_choice(self.edition, "edition", tuple(_FILTER_EDITIONS))
        expected = list(_FILTER_EDITIONS[self.edition]["classes"])
        _require_margin_classes(self.band_margins, self.edition, expected)
        for band in self.band_margins:
            if "class" in band:
                msg = (
                    "'band_margins' must not state a class: the class of a band "
                    "is read from its margins. The "
                    f"{band.get('freq', math.nan):g} Hz entry states "
                    f"{band['class']!r}."
                )
                raise ValueError(msg)
        _require_requirement_keys(self.band_margins, expected)
        for band in self.band_margins:
            for key, value in band.items():
                if isinstance(value, float) and not math.isfinite(value):
                    msg = (
                        "'band_margins' must carry finite per-band values; the "
                        f"{band.get('freq', math.nan):g} Hz entry has "
                        f"{key}={value!r}."
                    )
                    raise ValueError(msg)

    @property
    def bands(self) -> tuple[dict[str, Any], ...]:
        """The per-band verdicts, each margin row with the class it reaches.

        One ``{"freq", "class", "checked_to_omega", "margin_class<c>_db",
        ...}`` per band: the ``class`` is the strictest class of the edition
        the band meets on every requirement graded, or ``None``. A fresh copy
        at every read.
        """
        classes = tuple(_FILTER_EDITIONS[self.edition]["classes"])
        return tuple(
            {
                "freq": band["freq"],
                "class": _band_class(band, classes),
                **{key: value for key, value in band.items() if key != "class"},
            }
            for band in self.band_margins
        )

    def __reduce__(self) -> tuple[Any, tuple[type, dict[str, Any]]]:
        """Travel with plain rows, which pickle; they are frozen again on arrival."""
        return reduce_with_plain_rows(self)

    @property
    def overall_class(self) -> int | None:
        """The strictest class every band meets (0/1/2), or ``None``.

        ``None`` when at least one band meets no class of the edition, and
        for a bank with no bands in range, so nothing is attested vacuously.
        The strictest class every band meets is the worst (largest) per-band
        class.
        """
        classes = [band["class"] for band in self.bands]
        if not classes or None in classes:
            return None
        return int(max(classes))

    @property
    def range_limited(self) -> bool:
        """Whether a band's Table 1 mask reaches beyond half the input rate.

        ``True`` when at least one band's outermost Table 1 breakpoint
        (:math:`G^{4}`, carried to the bandwidth) lies beyond half the input
        sampling rate, so the verification could not exercise the full
        Table 1 mask there (no input of a digital bank has a frequency beyond
        it, but the limits are not demonstrated); the stated class then
        attests the verified frequency range and the ``.report()`` fiche
        prints a qualifying note.
        """
        spec = _FILTER_EDITIONS[self.edition]
        mask_top_omega = _map_breakpoint(spec["stopband_min"][-1][0], self.fraction)
        return any(
            band["checked_to_omega"] < mask_top_omega for band in self.band_margins
        )

    def available_classes(self) -> list[int]:
        """The performance classes carried by the per-band verdict dictionaries.

        Reads the ``margin_class<n>_db`` keys of a band verdict, so it reflects
        the edition (the 1995 edition adds class 0; the 2014 edition keeps only
        classes 1 and 2). An empty result (a bank with no bands in range)
        carries no verdicts, so this returns an empty list.

        The first band answers for all of them: construction pins every band
        to the same margin classes.
        """
        if not self.bands:
            return []
        return _margin_classes(self.bands[0])

    @property
    def requirements(self) -> tuple[str, ...]:
        """The requirements of its edition this verdict graded.

        ``"relative_attenuation"`` (Table 1: 5.10 of IEC 61260-1:2014, 4.4 of
        IEC 61260:1995) and ``"effective_bandwidth"`` (5.12; the filter
        integrated response of 4.5 in 1995) always, and ``"summation"``
        (5.16; 4.9 in 1995) when the bank has a band it applies to: a band
        with a neighbour on each side in the 2014 edition, which
        IEC 61260-2:2016 7.2.4.4 grades on those bands only, and two bands or
        more in the 1995 edition. Empty for a bank with no bands.
        """
        if not self.bands:
            return ()
        classes = self.available_classes()
        return tuple(
            name
            for name, template in _REQUIREMENTS.items()
            if any(
                band.get(template.format(c=classes[0])) is not None
                for band in self.bands
            )
        )

    def requirement_class(self, requirement: str) -> int | None:
        """The strictest class every band meets on one requirement alone.

        :param requirement: One of :attr:`requirements`.
        :return: The class, or ``None`` when a band meets none. The bands a
            requirement does not apply to (the end bands of the summation)
            do not constrain it.
        :raises KeyError: for a requirement this verdict did not grade.
        """
        template = self._requirement_template(requirement)
        for cls in self.available_classes():
            margins = [band[template.format(c=cls)] for band in self.bands]
            if all(m is None or m >= 0.0 for m in margins):
                return cls
        return None

    def binding_margin_db(self, requirement: str, filter_class: int) -> float:
        """The smallest margin, in dB, of any band to one class on one requirement.

        :param requirement: One of :attr:`requirements`.
        :param filter_class: One of :meth:`available_classes`.
        :return: The binding margin; negative when a band misses the class.
        :raises KeyError: for a requirement this verdict did not grade, or a
            class it carries no margins for.
        """
        template = self._requirement_template(requirement)
        if filter_class not in self.available_classes():
            msg = (
                f"class {filter_class!r} is not one of {self.available_classes()} "
                f"for edition {self.edition!r}"
            )
            raise KeyError(msg)
        key = template.format(c=filter_class)
        return float(min(band[key] for band in self.bands if band[key] is not None))

    def _requirement_template(self, requirement: str) -> str:
        """The per-band margin key template of a graded requirement."""
        if requirement not in self.requirements:
            msg = f"{requirement!r} was not graded; graded: {list(self.requirements)}"
            raise KeyError(msg)
        return _REQUIREMENTS[requirement]

    def reference_class(self) -> int:
        """The class whose corridor the fiche/plot overlays.

        The achieved overall class when the bank complies, else the loosest
        class of the edition (the one it comes closest to meeting).

        :raises ValueError: If the result carries no bands, so there is no
            reference class to report.
        """
        if self.overall_class is not None:
            return self.overall_class
        classes = self.available_classes()
        if not classes:
            msg = (
                "This filter-compliance result has no bands, so it has no "
                "reference class; check the bank's frequency limits."
            )
            raise ValueError(msg)
        return max(classes)

    def plot(
        self,
        ax: Axes | None = None,
        *,
        requirement: str = "relative_attenuation",
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        r"""Plot one graded requirement.

        ``"relative_attenuation"`` (the default) draws the measured relative
        attenuation of the binding band over the acceptance corridor of the
        achieved (or, when non-compliant, the loosest) class; see
        :func:`phonometry._plot.filters.plot_filter_class`.
        ``"effective_bandwidth"`` draws :math:`\Delta B` of every band between
        the limits of 5.12.2, and ``"summation"`` the Formula (3) curve of
        every inner band between the limits of 5.16. Requires matplotlib
        (``pip install phonometry[plot]``) and returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param requirement: One of :attr:`requirements`.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the renderer's measured curve.
        :raises ValueError: for a requirement this verdict did not grade.
        """
        from .._i18n import check_language
        from .._plot.filters import (
            plot_filter_bandwidth,
            plot_filter_class,
            plot_filter_summation,
        )

        check_language(language)
        require_choice(requirement, "requirement", self.requirements)
        renderers = {
            "relative_attenuation": plot_filter_class,
            "effective_bandwidth": plot_filter_bandwidth,
            "summation": plot_filter_summation,
        }
        return renderers[requirement](self, ax=ax, language=language, **kwargs)

    def report(
        self,
        path: str,
        *,
        metadata: ReportMetadata | None = None,
        engine: str = "reportlab",
        verbose: bool = False,
        language: str = "en",
    ) -> str:
        """Render an IEC 61260-1 filter-class-compliance fiche to a PDF.

        Writes a one-page accredited report: the standard-basis line, an
        optional metadata header block, a per-band classification table beside
        the mask-overlay plot (the result's own :meth:`plot`), the boxed
        class-compliance result, an optional verdict row against a supplied
        ``required_class`` and a footer with the fixed disclaimer.

        :param path: Destination path of the PDF file.
        :param metadata: Optional
            :class:`~phonometry.ReportMetadata`; ``None`` produces a
            prediction fiche (body, result and disclaimer only). A supplied
            ``required_class`` drives the verdict row.
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: Accepted for a uniform signature; it has no effect on
            the single-layout filter-compliance fiche.
        :param language: Fiche language: ``"en"`` (default, English) or
            ``"es"`` (Spanish, with a comma decimal separator).
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` is not ``"reportlab"``.
        :raises ImportError: If reportlab is not installed
            (``pip install phonometry[report]``), or matplotlib is missing for
            the embedded figure (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language

        check_language(language)
        check_engine(engine)
        from .._report.iec61260 import render_iec61260_report

        return render_iec61260_report(
            self, path, metadata=metadata, verbose=verbose, language=language
        )


#: The frequency-weighting transcriptions this module used to carry went to
#: :mod:`phonometry.filters.weighting_compliance` with their subject. The
#: clean-room oracles pin the tables by this path, so the reads still resolve
#: to the module that holds them now.
_WEIGHTING_TRANSCRIPTIONS = frozenset(
    {
        "_ANSI_S14_TABLE4_B",
        "_ANSI_S14_TABLE5_12",
        "_IEC61012_AU_HF",
        "_IEC61012_TABLE1",
        "_U_POLES_HZ",
        "_WEIGHTING_TABLE3",
        "_analytic_weighting_db",
    }
)


def __getattr__(name: str) -> object:
    """Serve the transcriptions this module used to carry from their module."""
    if name in _WEIGHTING_TRANSCRIPTIONS:
        from . import weighting_compliance

        return getattr(weighting_compliance, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
