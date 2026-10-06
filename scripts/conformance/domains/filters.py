#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Domain 1 - Filters & weightings.

The fractional-octave bank against the IEC 61260-1 class masks, and the
frequency weightings (A and C of IEC 61672-1, G of ISO 7196, B of
ANSI S1.4-1983, AU of IEC 61012, D of IEC 537) against the design-goal tables
and tolerance masks they are defined by.

The class verdicts and the weighting deviations are not computed here: they
come from :mod:`conformance.shared`, which the showcase table at the head of
the report also calls, so a row below and the table above can never disagree
about the same filter.
"""

from __future__ import annotations

import math

import numpy as np
import reference_data as ref

import phonometry as ph
from phonometry import filters
from phonometry.filters.compliance import (
    _effective_bandwidth_1995,
    _reference_bandwidth_1995,
    _test_frequencies,
)
from phonometry.filters.core import _decimate_and_filter
from phonometry.filters.weighting import _runtime_frequency_response

from ..registry import Outcome, count, numeric, register
from ..render import _snap
from ..shared import _filter_class, _weighting_deviation

#: IEC 61260:1995 Table 1: the greatest value of the minimum relative
#: attenuation of class 0, the limit 5.7.3 holds an alias tone to, dB.
_CLASS_0_GREATEST_MINIMUM_DB = 75.0


def _filter_class_check(arch: str, fraction: float, label: str) -> Outcome:
    res = _filter_class(arch, fraction)
    margin = res.min_margin1
    ok = res.overall_class == 1
    return Outcome(
        expected="class 1",
        computed=(f"class {res.overall_class}" if res.overall_class else "none")
        + f" (margin {margin:+.3f} dB)",
        delta=f"{margin:+.3f} dB",
        passed=ok,
    )


@register(
    "Filters & weightings",
    "IEC 61260-1:2014 Table 1",
    "Octave-band filter class (butterworth, fs=48 kHz)",
)
def _chk_butter_octave() -> Outcome:
    return _filter_class_check("butter", 1, "octave")


@register(
    "Filters & weightings",
    "IEC 61260-1:2014 Table 1",
    "One-third-octave filter class (butterworth, fs=48 kHz)",
)
def _chk_butter_third() -> Outcome:
    return _filter_class_check("butter", 3, "third")


@register(
    "Filters & weightings",
    "IEC 61260:1995 / ANSI S1.11-2004 Table 1",
    "Class 0 (strictest) octave-band filter (butterworth, fs=48 kHz)",
)
def _chk_butter_class0_1995() -> Outcome:
    bank = filters.OctaveFilterBank(
        48000,
        fraction=1,
        order=6,
        limits=[100, 10000],
        design=filters.FilterDesign(filter_type="butter"),
    )
    result = ph.filters.verify_filter_class(bank, edition="1995")
    margin = min(b["margin_class0_db"] for b in result.bands)
    achieved = result.requirement_class("relative_attenuation")
    return Outcome(
        expected="class 0",
        computed=(f"class {achieved}" if achieved is not None else "none")
        + f" (margin {margin:+.3f} dB)",
        delta=f"{margin:+.3f} dB",
        passed=achieved == 0,
    )


def _bank_1995(fraction: int) -> ph.filters.OctaveFilterBank:
    """The default Butterworth bank at 48 kHz, 125 Hz to 4 kHz."""
    return ph.filters.OctaveFilterBank(
        48000, fraction=fraction, order=6, limits=[125, 4000]
    )


def _integrated_response_check(fraction: int) -> Outcome:
    result = ph.filters.verify_filter_class(_bank_1995(fraction), edition="1995")
    worst = max(abs(b["bandwidth_deviation_db"]) for b in result.bands)
    achieved = result.requirement_class("effective_bandwidth")
    margin = result.binding_margin_db("effective_bandwidth", 0)
    return Outcome(
        expected="class 0 (|Delta B| <= 0.15 dB)",
        computed=f"class {achieved} (|Delta B| <= {worst:.3f} dB)",
        delta=f"{margin:+.3f} dB",
        passed=achieved == 0,
    )


@register(
    "Filters & weightings",
    "IEC 61260:1995 4.5.3 and 5.4",
    "Octave Butterworth bank (fs=48 kHz, 125 Hz to 4 kHz): largest |Delta B| "
    "of equations (13), (14) and (16) within the class 0 +/-0.15 dB",
)
def _chk_integrated_response_octave_1995() -> Outcome:
    return _integrated_response_check(1)


@register(
    "Filters & weightings",
    "IEC 61260:1995 4.5.3 and 5.4",
    "One-third-octave Butterworth bank (fs=48 kHz, 125 Hz to 4 kHz): largest "
    "|Delta B| of equations (13), (14) and (16) within the class 0 +/-0.15 dB",
)
def _chk_integrated_response_third_1995() -> Outcome:
    return _integrated_response_check(3)


def _summation_check(fraction: int) -> Outcome:
    result = ph.filters.verify_filter_class(_bank_1995(fraction), edition="1995")
    # Rounded before printing, plus zero, so a sum a hair under the input does
    # not print as -0.000.
    low = round(min(b["summation_min_db"] for b in result.bands), 3) + 0.0
    high = round(max(b["summation_max_db"] for b in result.bands), 3) + 0.0
    achieved = result.requirement_class("summation")
    margin = result.binding_margin_db("summation", 0)
    return Outcome(
        expected="class 0 (-1.0 dB <= Delta P <= +1.0 dB)",
        computed=f"class {achieved} ({low:+.3f} dB to {high:+.3f} dB)",
        delta=f"{margin:+.3f} dB",
        passed=achieved == 0,
    )


@register(
    "Filters & weightings",
    "IEC 61260:1995 4.9 and 5.8",
    "Octave Butterworth bank (fs=48 kHz, 125 Hz to 4 kHz): summed outputs of "
    "equation (19), lowest to highest mid-band frequency, within the class 0 "
    "+/-1.0 dB",
)
def _chk_summation_octave_1995() -> Outcome:
    return _summation_check(1)


@register(
    "Filters & weightings",
    "IEC 61260:1995 4.9 and 5.8",
    "One-third-octave Butterworth bank (fs=48 kHz, 125 Hz to 4 kHz): summed "
    "outputs of equation (19), lowest to highest mid-band frequency, within "
    "the class 0 +/-1.0 dB",
)
def _chk_summation_third_1995() -> Outcome:
    return _summation_check(3)


@register(
    "Filters & weightings",
    "IEC 61260:1995 equations (9) and (16)",
    "Ideal octave band, S = 24, N = 5S: filter integrated response of the "
    "trapezoidal sum equals its hand sum interval by interval (closed form)",
)
def _chk_ideal_integrated_response_1995() -> Outcome:
    points = 24
    half = points // 2
    n = 5 * points
    omega = _test_frequencies(1, points, -n, n + 1)
    i = np.arange(-n, n + 2)
    half_power = 10.0 * math.log10(2.0)
    delta_a = np.where(
        np.abs(i) < half, 0.0, np.where(np.abs(i) == half, half_power, np.inf)
    )
    # The base-ten octave ratio of equation (1), and from it the reference
    # bandwidth of equation (9) for b = 1, both written out here so that the
    # row holds the library's equation (9) as well as its equation (16).
    g = 10.0 ** (3.0 / 10.0)
    reference_by_hand = g ** (1.0 / 2.0) - g ** (-1.0 / 2.0)
    r = g ** (1.0 / points)
    by_hand = (
        (r ** (half - 1) - r ** -(half - 1))
        + 0.75 * (r ** -(half - 1) - r**-half)
        + 0.75 * (r**half - r ** (half - 1))
        + 0.25 * (r**-half - r ** -(half + 1))
        + 0.25 * (r ** (half + 1) - r**half)
    )
    computed = 10.0 * math.log10(
        _effective_bandwidth_1995(omega, delta_a) / _reference_bandwidth_1995(1)
    )
    return numeric(
        10.0 * math.log10(by_hand / reference_by_hand),
        computed,
        1e-12,
        unit="dB",
        places=6,
    )


@register(
    "Filters & weightings",
    "IEC 61260:1995 4.8 and 5.7",
    "Tones at the decimated sampling frequency minus the nominal mid-band "
    "frequency of the 20 Hz and 200 Hz bands of the default one-third-octave "
    "bank (fs=48 kHz), run through the bank: band output at least the +75 dB "
    "of class 0 below the input",
)
def _chk_anti_alias_tones_1995() -> Outcome:
    fs = 48000
    bank = ph.filters.OctaveFilterBank(fs, fraction=3)
    t = np.arange(4 * fs) / fs
    nominal = list(bank.nominal_freq)
    held = 0
    picks = (20.0, 200.0)
    for target in picks:
        index = nominal.index(f"{target:g}")
        factor = int(bank.factor[index])
        tone_hz = fs / factor - target
        x = np.sqrt(2.0) * np.sin(2.0 * np.pi * tone_hz * t)
        y = _decimate_and_filter(x, bank.sos[index], factor)
        settled = y[y.size // 2 :]
        below = -10.0 * math.log10(float(np.mean(settled**2)))
        held += int(factor > 1 and below >= _CLASS_0_GREATEST_MINIMUM_DB)
    return count(held, len(picks), subject="band outputs")


@register(
    "Filters & weightings",
    "IEC 61260-1:2014 5.15 and Table 1",
    "Default octave bank at fs=16 kHz graded at its input rate, alias images "
    "of the decimated bands included: class 1 on Table 1",
)
def _chk_alias_images_2014() -> Outcome:
    # The default bank at 16 kHz keeps the bands up to 4 kHz; asking for
    # them spares the warning about the ones above the Nyquist frequency.
    bank = ph.filters.OctaveFilterBank(16000, 1, limits=[12, 5000])
    result = ph.filters.verify_filter_class(bank)
    margin = min(b["margin_class1_db"] for b in result.bands)
    achieved = result.requirement_class("relative_attenuation")
    return Outcome(
        expected="class 1",
        computed=(f"class {achieved}" if achieved is not None else "none")
        + f" (margin {margin:+.3f} dB)",
        delta=f"{margin:+.3f} dB",
        passed=achieved == 1,
    )


def _weighting_type0_check(curve: str, fs: int) -> Outcome:
    """Grade one weighting against the IEC 651:1979 Table V Type 0 mask.

    Type 0 is the tightest of the four instrument types of subclause 1.2 and
    has no equivalent in IEC 61672-1:2013, whose class 1 opens to +2.5/-16 dB
    at 16 kHz and +3/-inf at 20 kHz where Type 0 holds +2/-3 at both.
    """
    wf = filters.WeightingFilter(fs, curve)
    result = ph.filters.verify_weighting_class(wf, edition="1979")
    margin = min(b["margin_class0_db"] for b in result.bands)
    ok = result.overall_class == 0
    return Outcome(
        expected="Type 0",
        computed=(
            f"Type {result.overall_class}"
            if result.overall_class is not None
            else "none"
        )
        + f" (margin {margin:+.3f} dB)",
        delta=f"{margin:+.3f} dB",
        passed=ok,
    )


@register(
    "Filters & weightings",
    "IEC 651:1979 Table V (via BS 5969:1981)",
    "Type 0 (strictest) A-weighting tolerance mask (fs=48 kHz)",
)
def _chk_a_weighting_type0_1979() -> Outcome:
    return _weighting_type0_check("A", 48000)


@register(
    "Filters & weightings",
    "IEC 651:1979 Table V (via BS 5969:1981)",
    "Type 0 (strictest) C-weighting tolerance mask (fs=48 kHz)",
)
def _chk_c_weighting_type0_1979() -> Outcome:
    return _weighting_type0_check("C", 48000)


@register(
    "Filters & weightings",
    "IEC 61260-1:2014 Table F.1",
    "Formula (9) breakpoint mapping, b=3, Omega at G**(1/2)",
)
def _chk_map_breakpoint_table_f1() -> Outcome:
    from phonometry.filters.compliance import _map_breakpoint

    return numeric(
        ref.IEC61260_TABLE_F1[0.5][0], _map_breakpoint(0.5, 3), 5e-6, places=5
    )


def _weighting_check(curve: str, fs: int) -> Outcome:
    res = _weighting_deviation(curve, fs)
    headroom = res.min_headroom
    band = f"[{res.bind_lower:+.2f}, {res.bind_upper:+.2f}] dB"
    return Outcome(
        expected=f"deviation within limits @ {res.bind_freq:.0f} Hz",
        computed=f"{_snap(res.bind_dev):+.3f} dB in {band}",
        delta=f"headroom {headroom:+.3f} dB",
        passed=headroom >= 0.0,
    )


@register(
    "Filters & weightings",
    "IEC 61672-1:2013 Table 3",
    "A-weighting deviation vs class-1 limits (fs=48 kHz)",
)
def _chk_a_weighting() -> Outcome:
    return _weighting_check("A", 48000)


@register(
    "Filters & weightings",
    "IEC 61672-1:2013 Table 3",
    "C-weighting deviation vs class-1 limits (fs=48 kHz)",
)
def _chk_c_weighting() -> Outcome:
    return _weighting_check("C", 48000)


@register(
    "Filters & weightings",
    "ISO 7196:1995 Table 2 / A.3",
    "G-weighting deviation vs +/-1 dB tolerance (fs=48 kHz)",
)
def _chk_g_weighting() -> Outcome:
    return _weighting_check("G", 48000)


@register(
    "Filters & weightings",
    "ANSI S1.4-1983 Tables IV/V",
    "B-weighting (historical) deviation vs Type 0 limits (fs=48 kHz)",
)
def _chk_b_weighting() -> Outcome:
    return _weighting_check("B", 48000)


@register(
    "Filters & weightings",
    "IEC 61012:1990 Table 1 / 2.2",
    "AU-weighting deviation vs separate-unit tolerances (fs=96 kHz)",
)
def _chk_au_weighting() -> Outcome:
    # 96 kHz so the 25/31.5/40 kHz rows (exact base-10 frequencies up to
    # 39 811 Hz) fall below Nyquist and the full Table 1 range is checked.
    return _weighting_check("AU", 96000)


@register(
    "Filters & weightings",
    "IEC 537:1976 (withdrawn) via NASA CR-3406 Table SLD-I",
    "D-weighting response vs the published tabulated curve (fs=48 kHz)",
)
def _chk_d_weighting() -> Outcome:
    # IEC 537 is withdrawn and published no surviving tolerance table, so the
    # D response is pinned against the tabulated curve republished in the
    # NASA Handbook of Aircraft Noise Metrics (Table SLD-I, printed at the
    # integer nominal frequencies to 0.1 dB). The rational transfer function
    # reproduces every row within 0.1 dB except 1600/2500 Hz, which appear to
    # round a different source curve; the realized filter adds bilinear
    # residuals below 0.1 dB, so the acceptance bound is 0.2 dB (0.45 dB at
    # the two outlier cells).
    wf = filters.WeightingFilter(48000, "D")
    freqs = np.array([r[0] for r in ref.IEC537_NASA_TABLE_SLD1], dtype=float)
    table = np.array([r[1] for r in ref.IEC537_NASA_TABLE_SLD1], dtype=float)
    h = _runtime_frequency_response(wf, np.concatenate([freqs, [1000.0]]))
    gain = 20.0 * np.log10(np.abs(h))
    dev = (gain[:-1] - gain[-1]) - table
    bound = np.where(np.isin(freqs, (1600.0, 2500.0)), 0.45, 0.2)
    worst = int(np.argmax(np.abs(dev) / bound))
    ok = bool(np.all(np.abs(dev) <= bound))
    return Outcome(
        expected="abs(response - table) <= 0.2 dB (0.45 dB at 1600/2500 Hz)",
        computed=(
            f"{dev[worst]:+.3f} dB @ {freqs[worst]:.0f} Hz "
            f"(bound {bound[worst]:.2f} dB)"
        ),
        delta=f"headroom {bound[worst] - abs(dev[worst]):+.3f} dB",
        passed=ok,
    )
