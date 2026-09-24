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
61260-1:2014 requires of the transfer function of a set of filters and run the
way IEC 61260-2:2016 (pattern evaluation) says the requirement is tested.
Besides the Table 1 mask there are two more requirements, both computed from
the same designed sections:

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
  errata registry).

Both are graded for ``edition="2014"`` only, whose Part 2 prescribes them; a
1995-edition verdict remains the Table 1 mask.

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
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy import signal

from .._internal.validation import (
    check_engine,
    is_class_designation,
    require_choice,
    require_count,
    require_ranks,
    require_same_length,
    require_summary_class,
)

if TYPE_CHECKING:
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

#: IEC 61260-1:2014 5.12.2: acceptance limits on the effective bandwidth
#: deviation, +/- dB, per class.
_BANDWIDTH_LIMITS_DB: dict[int, float] = {1: 0.4, 2: 0.6}

#: IEC 61260-1:2014 5.16: acceptance limits (lower, upper) on the summation of
#: output signals, dB, per class.
_SUMMATION_LIMITS_DB: dict[int, tuple[float, float]] = {1: (-1.8, 0.8), 2: (-3.8, 1.8)}

#: The names of the requirements a design verdict can carry, with the key
#: template their per-band margins are stored under and the clause of IEC
#: 61260-1:2014 that states them.
_REQUIREMENTS: dict[str, tuple[str, str]] = {
    "relative_attenuation": ("margin_class{c}_db", "5.10"),
    "effective_bandwidth": ("bandwidth_margin_class{c}_db", "5.12"),
    "summation": ("summation_margin_class{c}_db", "5.16"),
}

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


def _band_relative_attenuation(
    sos: np.ndarray, mid_hz: float, rate_hz: float, frequencies_hz: np.ndarray
) -> np.ndarray:
    """Relative attenuation of one designed band at arbitrary frequencies, dB.

    Formula (8) of IEC 61260-1:2014 with the attenuation at the exact mid-band
    frequency as reference, as :func:`verify_filter_class` reads the mask.
    A frequency at or beyond the band's processing Nyquist frequency carries
    no signal at the band's decimated rate (the multirate anti-aliasing
    removes it), so it reads as infinite attenuation: its output is nothing.

    :param sos: The band's second-order sections.
    :param mid_hz: Its exact mid-band frequency.
    :param rate_hz: The rate its sections run at, ``fs / factor``.
    :param frequencies_hz: Where to evaluate it.
    :return: The relative attenuation, ``+inf`` where no signal reaches.
    """
    eps = np.finfo(float).eps
    freqs = np.asarray(frequencies_hz, dtype=np.float64)
    out = np.full(freqs.shape, np.inf)
    reachable = (freqs > 0.0) & (freqs < rate_hz / 2.0)
    _, h_ref = signal.sosfreqz(sos, worN=np.array([mid_hz]), fs=rate_hz)
    a_ref = -20.0 * np.log10(np.abs(h_ref[0]) + eps)
    if np.any(reachable):
        _, h = signal.sosfreqz(sos, worN=freqs[reachable], fs=rate_hz)
        out[reachable] = -20.0 * np.log10(np.abs(h) + eps) - a_ref
    return out


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


def _reference_bandwidth(fraction: float) -> float:
    r"""IEC 61260-1:2014 Formula (15): :math:`B_\mathrm{r} = (1/b)\ln G`."""
    return math.log(_G) / fraction


def _summation_deviation(relative_attenuations_db: np.ndarray) -> np.ndarray:
    r"""IEC 61260-2:2016 Formula (3), point by point.

    :math:`\Delta P_j = 10\lg\left[\sum 10^{-0.1\,\Delta A}\right]` over the
    three filters :math:`j-1`, :math:`j`, :math:`j+1` at one frequency.

    :param relative_attenuations_db: Shape ``(3, n)``: the relative
        attenuation of the lower neighbour, the band and the upper neighbour
        at the same ``n`` frequencies.
    :return: :math:`\Delta P_j` at each frequency, dB.
    """
    power = 10.0 ** (-0.1 * np.asarray(relative_attenuations_db, dtype=np.float64))
    return np.asarray(10.0 * np.log10(np.sum(power, axis=0)))


def _bank_bandwidth_deviation(
    sos: np.ndarray,
    mid_hz: float,
    rate_hz: float,
    fraction: float,
    points_per_bandwidth: int,
) -> float:
    r"""The effective bandwidth deviation :math:`\Delta B` of one designed band.

    The Formula (1) grid runs from :math:`-N` to :math:`N + 1` with :math:`N`
    at least :math:`2S` (7.2.3.2) and wide enough to reach the outermost
    breakpoint of Table 1 (:math:`G^{\pm 4}` carried to the bandwidth), past
    which the class 1 relative attenuation is at least 70 dB and leaves less
    than one part in :math:`10^7` of the integral.
    """
    outermost = _map_breakpoint(_STOPBAND_MIN[-1][0], fraction)
    reach = math.ceil(fraction * points_per_bandwidth * math.log(outermost, _G))
    n = max(2 * points_per_bandwidth, reach)
    omega = _test_frequencies(fraction, points_per_bandwidth, -n, n + 1)
    delta_a = _band_relative_attenuation(sos, mid_hz, rate_hz, omega * mid_hz)
    return 10.0 * math.log10(
        _effective_bandwidth(omega, delta_a) / _reference_bandwidth(fraction)
    )


def _bank_summation(
    sos: tuple[np.ndarray, ...] | list[np.ndarray],
    mids_hz: np.ndarray,
    rates_hz: np.ndarray,
    fraction: float,
    points_per_bandwidth: int,
    band: int,
) -> tuple[np.ndarray, np.ndarray]:
    r"""The Formula (3) curve of one band: :math:`\Omega_i` and :math:`\Delta P_j`.

    :math:`i` runs from :math:`-M` to :math:`M`, :math:`M = \lfloor S/2
    \rfloor` (7.2.4.2), the frequencies between the band edges of the band.
    Each of the three filters is evaluated at the same frequency in hertz,
    which is the normalized frequency :math:`G^{i/(bS) \pm 1/b}` of 7.2.4.3
    for the neighbours of a set whose mid-band frequencies step by
    :math:`G^{1/b}`.

    :return: ``(omega, delta_p_db)`` for the band.
    """
    half = points_per_bandwidth // 2
    omega = _test_frequencies(fraction, points_per_bandwidth, -half, half)
    freqs = omega * float(mids_hz[band])
    rows = np.vstack(
        [
            _band_relative_attenuation(
                sos[k], float(mids_hz[k]), float(rates_hz[k]), freqs
            )
            for k in (band - 1, band, band + 1)
        ]
    )
    return omega, _summation_deviation(rows)


def _verify_band(
    bank: OctaveFilterBank,
    idx: int,
    classes_ordered: tuple[int, ...],
    breakpoint_omegas: np.ndarray,
    edition: str,
    num_points: int,
) -> tuple[dict[str, Any], float]:
    """Evaluate one band against every class; return its entry and Nyquist."""
    fm = float(bank.freq[idx])
    fsd = bank.fs / float(bank.factor[idx])
    w, h = signal.sosfreqz(bank.sos[idx], worN=num_points, fs=fsd)

    # Attenuation relative to the mid-band attenuation (Formulas 7-8),
    # with the reference evaluated exactly at the mid-band frequency.
    attenuation = -20.0 * np.log10(np.abs(h) + np.finfo(float).eps)
    _, h_ref = signal.sosfreqz(bank.sos[idx], worN=np.array([fm]), fs=fsd)
    a_ref = float(-20.0 * np.log10(np.abs(h_ref[0]) + np.finfo(float).eps))
    delta_all = attenuation - a_ref

    omega = w / fm
    valid = omega > 0
    omega, delta_a = omega[valid], delta_all[valid]

    # Guarantee the Table 1 breakpoints (pass-band included) are evaluated,
    # exactly (sosfreqz at the breakpoint frequencies, not interpolated
    # off the grid, so a coarse grid cannot smooth a dip across them).
    # Cut at the processing Nyquist, not omega.max(): the sosfreqz grid
    # stops short of Nyquist and must not exclude checkable breakpoints.
    omega_nyq = fsd / 2.0 / fm
    extra = breakpoint_omegas[
        (breakpoint_omegas > 0) & (breakpoint_omegas <= omega_nyq)
    ]
    if extra.size:
        _, h_extra = signal.sosfreqz(bank.sos[idx], worN=extra * fm, fs=fsd)
        att_extra = -20.0 * np.log10(np.abs(h_extra) + np.finfo(float).eps)
        omega = np.concatenate([omega, extra])
        delta_a = np.concatenate([delta_a, att_extra - a_ref])

    margins: dict[int, float] = {}
    for cls in classes_ordered:
        minimum, maximum = class_limits(bank.fraction, cls, omega, edition=edition)
        low_margin = float(np.min(delta_a - minimum))
        finite = np.isfinite(maximum)
        high_margin = (
            float(np.min(maximum[finite] - delta_a[finite]))
            if np.any(finite)
            else np.inf
        )
        margins[cls] = min(low_margin, high_margin)

    band_class: int | None = next(
        (cls for cls in classes_ordered if margins[cls] >= 0), None
    )
    band_entry: dict[str, Any] = {
        "freq": fm,
        "class": band_class,
        "checked_to_omega": float(omega_nyq),
    }
    for cls in classes_ordered:
        band_entry[f"margin_class{cls}_db"] = margins[cls]
    return band_entry, omega_nyq


def _grade_pattern_requirements(
    bank: OctaveFilterBank,
    bands: list[dict[str, Any]],
    classes_ordered: tuple[int, ...],
    points_per_bandwidth: int,
) -> None:
    """Add the 5.12 and 5.16 requirements to every band entry, in place.

    Each band gets its effective bandwidth deviation and its margin to each
    class's limits; each band with a neighbour on both sides gets the range
    of its Formula (3) curve and its margins too (7.2.4.4 leaves the two end
    bands out, and they carry ``None``). The band's class is then the
    strictest class it meets on every requirement graded.
    """
    rates = np.asarray([bank.fs / float(f) for f in bank.factor], dtype=np.float64)
    mids = np.asarray(bank.freq, dtype=np.float64)
    last = len(bands) - 1
    for idx, band in enumerate(bands):
        deviation = _bank_bandwidth_deviation(
            bank.sos[idx],
            float(mids[idx]),
            float(rates[idx]),
            bank.fraction,
            points_per_bandwidth,
        )
        band["bandwidth_deviation_db"] = deviation
        for cls in classes_ordered:
            band[f"bandwidth_margin_class{cls}_db"] = _BANDWIDTH_LIMITS_DB[cls] - abs(
                deviation
            )
        if 0 < idx < last:
            _, curve = _bank_summation(
                bank.sos, mids, rates, bank.fraction, points_per_bandwidth, idx
            )
            low, high = float(np.min(curve)), float(np.max(curve))
            band["summation_min_db"] = low
            band["summation_max_db"] = high
            for cls in classes_ordered:
                lower, upper = _SUMMATION_LIMITS_DB[cls]
                band[f"summation_margin_class{cls}_db"] = min(low - lower, upper - high)
        else:
            band["summation_min_db"] = None
            band["summation_max_db"] = None
            for cls in classes_ordered:
                band[f"summation_margin_class{cls}_db"] = None
        band["class"] = _band_class(band, classes_ordered)


def _band_class(band: dict[str, Any], classes_ordered: tuple[int, ...]) -> int | None:
    """The strictest class one band meets on every requirement it carries."""
    for cls in classes_ordered:
        margins = [
            band.get(template.format(c=cls)) for template, _ in _REQUIREMENTS.values()
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
    """Verify a filter bank against the IEC 61260 class limits.

    Each band's relative attenuation (referenced to the attenuation at its
    exact mid-band frequency) is checked against every acceptance-limit class of
    the selected edition's Table 1, evaluated on a dense frequency grid up to
    the band's processing Nyquist. The Table 1 breakpoint frequencies inside
    that range are always included in the evaluation, so the pass-band
    constraints are checked even if the grid were coarse. Frequencies beyond
    the processing Nyquist cannot carry signal energy at the band's decimated
    rate (the multirate anti-aliasing filter removes them), so they are
    treated as compliant; because the Table 1 limits there are nevertheless
    not demonstrated, the returned ``range_limited`` flag is set whenever a
    band's stop-band mask extends beyond its processing Nyquist, and the
    per-band ``checked_to_omega`` records how far the check reached.

    For ``edition="2014"`` two more requirements of IEC 61260-1:2014 are
    graded on the same sections, the way IEC 61260-2:2016 tests them (see
    the module docstring): the effective bandwidth deviation of every band
    (5.12, Formulas (1) and (2) of Part 2) and the summation of the output
    signals of every band that has a neighbour on each side (5.16, Formula
    (3) of Part 2). A band's class, and so the bank's, is the strictest class
    met on every requirement graded; :meth:`FilterComplianceResult.requirement_class`
    gives the class of each requirement on its own.

    :param bank: The filter bank to verify (its designed SOS are analyzed;
        works for stateful and stateless banks alike).
    :param num_points: Number of frequency grid points per band (>= 16).
    :param edition: ``"2014"`` (IEC 61260-1:2014, classes 1/2) or ``"1995"``
        (IEC 61260:1995 / ANSI S1.11-2004, adds the stricter class 0; the
        verdict is its Table 1 mask alone).
    :param points_per_bandwidth: ``S``, the test frequencies per filter
        bandwidth of IEC 61260-2:2016 Formula (1), at least 24 (7.2.1.4).
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

    bands: list[dict[str, Any]] = []

    # Table 1 breakpoints (both sides) that must always be evaluated.
    rows = list(spec["passband_max"]) + list(spec["stopband_min"])
    breakpoint_omegas = np.array(
        [_map_breakpoint(row[0], bank.fraction) for row in rows]
    )
    breakpoint_omegas = np.concatenate([1.0 / breakpoint_omegas, breakpoint_omegas])

    # The outermost stop-band breakpoint (G**4 mapped to the bandwidth
    # designator): a band whose processing Nyquist lies below it cannot have
    # its full high-side stop-band mask demonstrated, so the verdict is then
    # range-limited (the multirate anti-aliasing justifies treating the
    # unreachable region as compliant, but it is not verified).
    mask_top_omega = _map_breakpoint(spec["stopband_min"][-1][0], bank.fraction)
    range_limited = False

    for idx in range(bank.num_bands):
        band_entry, omega_nyq = _verify_band(
            bank, idx, classes_ordered, breakpoint_omegas, edition, num_points
        )
        if omega_nyq < mask_top_omega:
            range_limited = True
        bands.append(band_entry)
    if edition == "2014":
        _grade_pattern_requirements(bank, bands, classes_ordered, points_per_bandwidth)

    if not bands:
        # No bands to verify: never report compliance vacuously.
        overall: int | None = None
        range_limited = False
    else:
        classes = [band["class"] for band in bands]
        # The strictest class every band meets is the worst (largest) per-band
        # class; None if any band meets no class.
        overall = None if None in classes else max(classes)

    return FilterComplianceResult(
        overall_class=overall,
        bands=tuple(bands),
        fraction=int(bank.fraction),
        edition=edition,
        sos=tuple(np.asarray(s, dtype=np.float64) for s in bank.sos),
        band_frequencies=np.asarray(bank.freq, dtype=np.float64),
        factors=tuple(int(f) for f in bank.factor),
        fs=float(bank.fs),
        num_points=int(num_points),
        range_limited=range_limited,
        points_per_bandwidth=points_per_bandwidth,
    )


def _margin_classes(band: dict[str, Any]) -> list[int]:
    """The classes one band verdict carries margins for, read off its keys."""
    prefix, suffix = "margin_class", "_db"
    return sorted(
        int(key[len(prefix) : -len(suffix)])
        for key in band
        if key.startswith(prefix) and key.endswith(suffix)
    )


def _require_margin_classes(
    bands: tuple[dict[str, Any], ...], edition: str, expected: list[int]
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
                f"{band.get('freq', math.nan):g} Hz entry of 'bands' carries "
                f"margins for classes {carried}."
            )
            raise ValueError(msg)


def _require_requirement_keys(
    bands: tuple[dict[str, Any], ...], classes: list[int]
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
    for name, (template, _) in _REQUIREMENTS.items():
        key = template.format(c=classes[0])
        carried = [key in band for band in bands]
        if any(carried) and not all(carried):
            missing = next(b for b, has in zip(bands, carried, strict=True) if not has)
            msg = (
                f"'bands' must carry the {name!r} requirement in every band or "
                f"in none; the {missing.get('freq', math.nan):g} Hz entry has "
                f"no {key!r}."
            )
            raise ValueError(msg)


@dataclass(frozen=True)
class FilterComplianceResult:
    r"""IEC 61260-1 class-compliance verdict of an :class:`OctaveFilterBank`.

    What :func:`verify_filter_class` returns: the verdict together with the
    minimal filter-bank data needed to redraw the measured relative-attenuation
    curve, so the result exposes the standard ``plot`` / ``report`` pair without
    holding a reference to the (possibly stateful) bank.

    :ivar overall_class: The strictest class every band meets (0/1/2), or
        ``None`` when at least one band meets no class of the edition.
    :ivar bands: The per-band verdicts (one ``{"freq", "class",
        "margin_class<c>_db", ...}`` per band), as an immutable tuple.
    :ivar fraction: Bandwidth designator ``b`` (1 for octave, 3 for
        one-third-octave).
    :ivar edition: ``"2014"`` (IEC 61260-1:2014, classes 1/2) or ``"1995"``
        (IEC 61260:1995 / ANSI S1.11-2004, classes 0/1/2).
    :ivar sos: Per-band second-order sections of the analysed bank (one array
        per band), kept so the relative attenuation can be recomputed with
        :func:`scipy.signal.sosfreqz` exactly as the verifier does.
    :ivar band_frequencies: The exact mid-band frequencies ``f_m`` in Hz.
    :ivar factors: Per-band decimation factor; the band's processing sample
        rate is ``fs / factor`` (the multirate rate the SOS were designed at).
        Stored because the response must be evaluated at that decimated rate,
        which the verifier's public return does not expose.
    :ivar fs: The bank's full sampling rate in Hz.
    :ivar num_points: Frequency grid points per band used by the verification,
        retained so the redrawn curve matches the analysed grid.
    :ivar range_limited: ``True`` when at least one band's stop-band mask
        extends beyond its processing Nyquist frequency, so the verification
        could not exercise the full Table 1 mask there (the multirate
        anti-aliasing removes signal energy beyond it, but the limits are not
        demonstrated); the stated class then attests the verified frequency
        range and the ``.report()`` fiche prints a qualifying note.
    :ivar points_per_bandwidth: ``S``, the test frequencies per bandwidth of
        IEC 61260-2:2016 Formula (1) the effective bandwidth and the summation
        were evaluated on.

    For ``edition="2014"`` every band entry carries, besides its Table 1
    margins ``margin_class<c>_db``, the two requirements IEC 61260-2 tests on
    the same measurements:

    * ``bandwidth_deviation_db``, the effective bandwidth deviation
      :math:`\Delta B` of 5.12, and ``bandwidth_margin_class<c>_db``, its
      distance to each class's limit;
    * ``summation_min_db`` and ``summation_max_db``, the range of the
      summation :math:`\Delta P_j` of 5.16 across the band, and
      ``summation_margin_class<c>_db``, the nearer of its distances to each
      class's two limits; all three are ``None`` on the first and the last
      band, which have a neighbour on one side only (IEC 61260-2 7.2.4.4).

    A band's ``class`` is then the strictest class it meets on all of them.
    """

    overall_class: int | None
    bands: tuple[dict[str, Any], ...]
    fraction: int
    edition: str
    sos: tuple[np.ndarray, ...]
    band_frequencies: np.ndarray
    factors: tuple[int, ...]
    fs: float
    num_points: int
    _: KW_ONLY
    range_limited: bool = False
    points_per_bandwidth: int = _MIN_POINTS_PER_BANDWIDTH

    def __post_init__(self) -> None:
        """Reject a verdict whose per-band entries disagree.

        The fiche prints one row per band and, in its box, the overall class
        of the whole bank, so a band list short of an entry gives a sheet
        whose verdict covers a band that is nowhere in its table.

        The edition and the class are pinned against the band verdicts they
        summarise, because the three travel together: the plot and the fiche
        pick the corridor from :attr:`edition` and read
        ``margin_class<overall_class>_db`` out of :attr:`bands`. A verdict
        whose edition disagrees with its margin keys would draw the other
        edition's corridor under this edition's title, and an overall class
        the bands carry no margins for dies in a bare ``KeyError`` halfway
        through the figure. The class is pinned as a designation, not merely
        as a value equal to one: ``1.0`` and ``True`` compare equal to class 1
        yet build ``margin_class1.0_db`` and print ``Class True``. Being one
        of the edition's classes is not enough either, so the class is pinned
        against the per-band classes it summarises as well; see
        :func:`~.._internal.validation.require_summary_class`. Every band is checked, not just the
        first:
        :func:`verify_filter_class` fills each entry from the same list of
        classes, so a band list whose entries disagree among themselves is
        one no bank produced, and it is the later band that the fiche's
        per-band table and the plot's worst-band search die on.

        A bank with no bands in range is an outcome
        :func:`verify_filter_class` does produce, and it always pairs it with
        ``overall_class = None`` so nothing is attested vacuously; the class
        is therefore pinned against the emptiness too, because a stated class
        over zero bands prints an accredited verdict box above a table that
        reportlab then refuses to build, complaining about a table with no
        rows and naming neither the bands nor the bank.

        The per-band numbers are pinned finite. Every margin comes from a
        ``min`` over the measured relative attenuation against the Table 1
        mask, so no bank emits a NaN here; one smuggled in through
        :func:`dataclasses.replace` prints ``Class 1 (+nan dB)`` in the
        per-band table under a boxed verdict that still reads COMPLIES,
        because the binding margin reads whichever band is untouched.

        :raises ValueError: if the per-band entries disagree, the edition is
            unknown or does not match the per-band margin keys, the overall
            class is not one the bands carry margins for or not the one the
            per-band classes derive, a band carries no class of the edition,
            a class is stated over no bands at all, or a per-band value is not
            finite.
        """
        require_ranks(self, band_frequencies=1)
        require_same_length(self, "bands", "sos", "band_frequencies", "factors")
        require_choice(self.edition, "edition", tuple(_FILTER_EDITIONS))
        expected = list(_FILTER_EDITIONS[self.edition]["classes"])
        _require_margin_classes(self.bands, self.edition, expected)
        if self.overall_class is not None and not is_class_designation(
            self.overall_class, expected
        ):
            msg = (
                f"'overall_class' must be one of {expected} for edition "
                f"{self.edition!r} (or None); got {self.overall_class!r}."
            )
            raise ValueError(msg)
        if self.overall_class is not None and not self.bands:
            msg = (
                f"'overall_class' is {self.overall_class!r} but 'bands' is "
                "empty: a class cannot be attested over no verified band. A "
                "bank with no bands in range carries 'overall_class' None."
            )
            raise ValueError(msg)
        require_summary_class(self, self.bands, self.overall_class, expected)
        _require_requirement_keys(self.bands, expected)
        for band in self.bands:
            for key, value in band.items():
                if isinstance(value, float) and not math.isfinite(value):
                    msg = (
                        "'bands' must carry finite per-band values; the "
                        f"{band.get('freq', math.nan):g} Hz entry has "
                        f"{key}={value!r}."
                    )
                    raise ValueError(msg)

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
        """The requirements of IEC 61260-1:2014 this verdict graded.

        ``"relative_attenuation"`` (5.10, Table 1) always; for the 2014
        edition also ``"effective_bandwidth"`` (5.12) and, when the bank has
        a band with a neighbour on each side, ``"summation"`` (5.16), which
        IEC 61260-2:2016 7.2.4.4 grades on those bands only. Empty for a bank
        with no bands.
        """
        if not self.bands:
            return ()
        classes = self.available_classes()
        return tuple(
            name
            for name, (template, _) in _REQUIREMENTS.items()
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
        return _REQUIREMENTS[requirement][0]

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
