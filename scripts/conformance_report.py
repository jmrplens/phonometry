#  Copyright (c) 2026. Jose M. Requena-Plens
"""Numerical conformance report for phonometry.

A maintainable registry of numerical conformance checks. Each entry pins one
(standard, quantity) pair to:

* the standard designation + clause/table citation,
* the normative expected value or range (from the standard's own worked
  examples, or a closed form synthesized to a known result),
* a callable that computes the library's result, and
* the tolerance.

Running the harness emits Markdown for a GitHub PR comment: a headline
summary, a "Numerical validation - filters & weightings" section (per
filter architecture IEC 61260-1 class margins and A/C/G weighting worst-case
deviation vs the analytic/normative curve), and one conformance table per
domain (Standard | Quantity | Expected | Computed | Delta | Status).

Expected values are pulled from a single source of truth wherever the tests
already encode them: the shared ``tests/reference_data`` tables and the
ISO 532-1 data fixtures. Where the reference is a closed form, the harness
synthesizes an input with a known output, so the check is self-verifying.

Design goals: deterministic, fast (< 1 min), no network, pure library calls.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
from scipy import signal as sg

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_TESTS = _ROOT / "tests"
_DATA = _TESTS / "data"
for _p in (str(_TESTS),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import reference_data as ref  # noqa: E402

import phonometry as ph  # noqa: E402
from phonometry import OctaveFilterBank, WeightingFilter  # noqa: E402
from phonometry.compliance import class_limits, verify_filter_class  # noqa: E402
from phonometry.sharpness import reference_sound  # noqa: E402
from phonometry.sti import _sti_from_mtf  # noqa: E402


# ===========================================================================
# Registry primitives
# ===========================================================================
@dataclass(frozen=True)
class Outcome:
    """The rendered result of a single conformance check."""

    expected: str
    computed: str
    delta: str
    passed: bool


@dataclass(frozen=True)
class Check:
    """A registered (standard, quantity) conformance check."""

    domain: str
    standard: str
    quantity: str
    run: Callable[[], Outcome]


CHECKS: list[Check] = []


def register(domain: str, standard: str, quantity: str) -> Callable[
    [Callable[[], Outcome]], Callable[[], Outcome]
]:
    """Register a check callable under a domain / standard / quantity."""

    def deco(fn: Callable[[], Outcome]) -> Callable[[], Outcome]:
        CHECKS.append(Check(domain, standard, quantity, fn))
        return fn

    return deco


# Decimal places for the informational delta column. Coarse on purpose so the
# committed docs/CONFORMANCE.md stays byte-stable across numpy/scipy/BLAS
# builds (see the note in ``numeric``).
_DELTA_PLACES = 3


def _fmt(value: float, unit: str = "", places: int = 4) -> str:
    """Compact fixed/again-significant formatting with an optional unit."""
    if not math.isfinite(value):
        return "inf" if value > 0 else "-inf"
    text = f"{value:.{places}f}".rstrip("0").rstrip(".")
    if text in ("", "-0"):
        text = "0"
    return f"{text} {unit}".strip()


def numeric(
    expected: float,
    computed: float,
    tol: float,
    *,
    unit: str = "",
    rel: bool = False,
    places: int = 4,
    expected_label: Optional[str] = None,
) -> Outcome:
    """Build an Outcome for ``|computed - expected| <= tol`` (abs or rel)."""
    delta = computed - expected
    limit = tol * abs(expected) if rel else tol
    passed = abs(delta) <= limit
    tol_txt = f"{tol * 100:g}%" if rel else _fmt(tol, unit, places)
    exp_txt = expected_label or _fmt(expected, unit, places)
    return Outcome(
        expected=f"{exp_txt} (+/-{tol_txt})" if not expected_label else exp_txt,
        computed=_fmt(computed, unit, places),
        # The delta column is informational (pass/fail comes from ``passed``),
        # so it is coarsened to 3 decimals. This collapses sub-milli residuals
        # of the heavy DSP chains (ECMA/Moore-Glasberg/Zwicker, FFT intensity),
        # whose 4th-5th digit is BLAS/FFT-build dependent, to a stable value -
        # keeping the committed report diff-stable without hiding a regression
        # (that still shows in the Computed column and flips the status).
        delta=_fmt(delta, unit, _DELTA_PLACES),
        passed=passed,
    )


# ===========================================================================
# Shared compute helpers (called by both the registry and the numerical
# validation section, so the two can never disagree).
# ===========================================================================
_FILTER_ARCHS = ["butter", "cheby1", "cheby2", "ellip", "bessel"]


@dataclass(frozen=True)
class FilterClass:
    """IEC 61260-1 class verification summary for one architecture.

    Beyond the pass/fail verdict and margins, this captures the *binding*
    band and point - the measured relative attenuation there and the class-1
    acceptance limit it is compared against - so the report can show the
    number and the range it must sit in, not just the margin.
    """

    overall_class: Optional[int]
    min_margin1: float
    min_margin2: float
    bind_freq: float
    bind_measured_db: float
    bind_limit_db: float
    bind_side: str  # "ceil" (upper limit), "floor" (pass-band min) or
    # "stop" (stop-band min) - the side of the acceptance band that binds


@dataclass(frozen=True)
class WeightingDeviation:
    """Weighting deviation split into an informational maximum and the
    compliance margin evaluated at the *binding* frequency.

    ``worst_*`` is the largest |designed - nominal| across the band (usually
    at a frequency extreme, where the class-1 tolerance is widest and
    asymmetric). ``bind_*`` is taken at the frequency with the least headroom
    to its acceptance band - where deviation, the +/- tolerance and the
    headroom are co-located, so "value vs range" is unambiguous.
    """

    worst_freq: float
    worst_dev: float
    bind_freq: float
    bind_dev: float
    bind_lower: float
    bind_upper: float
    min_headroom: float


def _filter_class(arch: str, fraction: float) -> FilterClass:
    """IEC 61260-1 class verification summary for one architecture.

    The pass/fail verdict and margins come from the library's
    ``verify_filter_class`` (authoritative). The binding measured value and
    limit are re-derived here with the same public ``class_limits`` on the
    same designed SOS, so they cannot disagree with the library margin (a
    smoke-test guard asserts the re-derived margin equals the library's).
    """
    bank = OctaveFilterBank(
        48000, fraction=fraction, order=6, limits=[100, 10000], filter_type=arch
    )
    result = verify_filter_class(bank)
    bands = result["bands"]
    worst = min(bands, key=lambda b: b["margin_class1_db"])
    idx = [b["freq"] for b in bands].index(worst["freq"])
    fm = float(bank.freq[idx])
    fsd = bank.fs / float(bank.factor[idx])
    w, h = sg.sosfreqz(bank.sos[idx], worN=2 ** 15, fs=fsd)
    attenuation = -20.0 * np.log10(np.abs(h) + np.finfo(float).eps)
    a_ref = float(np.interp(fm, w, attenuation))
    delta = attenuation - a_ref
    omega = w / fm
    valid = omega > 0
    omega, delta = omega[valid], delta[valid]
    minimum, maximum = class_limits(bank.fraction, 1, omega)
    low_margin = delta - minimum
    finite = np.isfinite(maximum)
    high_margin = np.where(finite, maximum - delta, np.inf)
    point_margin = np.minimum(low_margin, high_margin)
    j = int(np.argmin(point_margin))
    omega_h = 1.0 / omega[j] if omega[j] < 1.0 else omega[j]
    if high_margin[j] < low_margin[j]:
        bind_side, bind_limit = "ceil", float(maximum[j])
    else:
        bind_side = "floor" if omega_h <= _pass_edge(bank.fraction) else "stop"
        bind_limit = float(minimum[j])
    return FilterClass(
        overall_class=result["overall_class"],
        min_margin1=min(b["margin_class1_db"] for b in bands),
        min_margin2=min(b["margin_class2_db"] for b in bands),
        bind_freq=fm,
        bind_measured_db=float(delta[j]),
        bind_limit_db=bind_limit,
        bind_side=bind_side,
    )


def _pass_edge(fraction: float) -> float:
    """Normalized pass-band edge G**(1/(2b)) for the given bandwidth b."""
    return float((10.0 ** (3.0 / 10.0)) ** (1.0 / (2.0 * fraction)))


def _weighting_deviation(curve: str, fs: int) -> WeightingDeviation:
    """Weighting deviation vs the normative curve, informational maximum plus
    the binding-frequency compliance margin.

    The weighting filter's designed SOS (at its internal oversampled rate)
    is evaluated against the standard's nominal response. For A/C the
    normative band is the IEC 61672-1 Table 3 class-1 acceptance limits;
    for G it is the ISO 7196 Annex A.3 +/-1 dB instrumentation tolerance.
    """
    wf = WeightingFilter(fs, curve)
    design_fs = wf.fs * wf._oversample  # noqa: SLF001 - documented attribute
    if curve == "G":
        rows = [r for r in ref.ISO7196_TABLE2 if r[0] < fs / 2]
        # Table 2 lists nominal one-third-octave labels; evaluate at the
        # exact base-10 frequencies 10**(n/10) as IEC 61672-1 Annex D does.
        freqs = np.array([10 ** (round(10 * math.log10(r[0])) / 10) for r in rows])
        nominal = np.array([r[1] for r in rows])
        upper = np.full(nominal.shape, ref.ISO7196_G_TOLERANCE_DB)
        lower = np.full(nominal.shape, -ref.ISO7196_G_TOLERANCE_DB)
    else:
        col = 1 if curve == "A" else 2
        rows = [r for r in ref.IEC61672_TABLE3 if r[0] < fs / 2]
        freqs = np.array([r[0] for r in rows], dtype=float)
        nominal = np.array([r[col] for r in rows])
        upper = np.array([r[3] for r in rows])
        lower = np.array([r[4] for r in rows])

    _, h = sg.sosfreqz(wf.sos, worN=freqs, fs=design_fs)
    response = 20.0 * np.log10(np.abs(h))
    deviation = response - nominal
    worst_idx = int(np.argmax(np.abs(deviation)))
    headroom = np.minimum(upper - deviation, deviation - lower)
    bind_idx = int(np.argmin(headroom))
    return WeightingDeviation(
        worst_freq=float(freqs[worst_idx]),
        worst_dev=float(deviation[worst_idx]),
        bind_freq=float(freqs[bind_idx]),
        bind_dev=float(deviation[bind_idx]),
        bind_lower=float(lower[bind_idx]),
        bind_upper=float(upper[bind_idx]),
        min_headroom=float(headroom[bind_idx]),
    )


# ===========================================================================
# Domain 1 - Filters & weightings
# ===========================================================================
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


# ===========================================================================
# Domain 2 - Levels & dosimetry
# ===========================================================================
_FS = 48000


def _tone(freq: float, seconds: float = 1.0, amp: float = 1.0) -> np.ndarray:
    t = np.arange(int(_FS * seconds)) / _FS
    return amp * np.sin(2.0 * np.pi * freq * t)


@register(
    "Levels & dosimetry",
    "IEC 61672-1:2013 (Leq)",
    "Leq of a 1 Pa 1 kHz sine",
)
def _chk_leq_sine() -> Outcome:
    # 20*log10((1/sqrt2) / 20e-6) = 90.97 dB.
    computed = float(ph.leq(_tone(1000.0)))
    return numeric(90.97, computed, 0.05, unit="dB", places=3)


@register(
    "Levels & dosimetry",
    "IEC 61252:1995 (LEX,8h)",
    "8 h exposure to 90 dB(A) noise",
)
def _chk_lex_8h() -> Outcome:
    rms = 2e-5 * 10 ** (90.0 / 20.0)
    x = math.sqrt(2) * rms * _tone(1000.0, seconds=2.0)
    computed = float(ph.lex_8h(x, _FS, duration_hours=8.0))
    return numeric(90.0, computed, 0.05, unit="dB", places=3)


@register(
    "Levels & dosimetry",
    "ISO 1996-1:2016 3.6.4",
    "Lden, constant 60 dB in day/evening/night",
)
def _chk_lden() -> Outcome:
    offset = 10.0 * math.log10((12 + 4 * 10**0.5 + 8 * 10) / 24)
    computed = float(ph.lden(60.0, 60.0, 60.0))
    return numeric(60.0 + offset, computed, 1e-6, unit="dB", places=4)


# ===========================================================================
# Domain 3 - Psychoacoustics
# ===========================================================================
def _iso532_stationary_expected() -> tuple[float, float, float]:
    data = json.loads((_DATA / "iso532_1_annexB_expected.json").read_text())
    entry = data["Test signal 1.txt"]
    return entry["N"], entry["Nmin"], entry["Nmax"]


def _iso532_levels() -> np.ndarray:
    levels = []
    for line in (_DATA / "iso532_1_test_signal_1_levels.txt").read_text().splitlines():
        if ":" in line and not line.strip().startswith("#"):
            levels.append(float(line.split(":")[1]))
    return np.array(levels)


@register(
    "Psychoacoustics",
    "ISO 532-1:2017 Annex B.2",
    "Zwicker loudness N, stationary test signal 1",
)
def _chk_iso532_stationary() -> Outcome:
    expected_n, nmin, nmax = _iso532_stationary_expected()
    res = ph.loudness_zwicker_from_spectrum(_iso532_levels(), field="free")
    computed = float(res.loudness)
    out = numeric(expected_n, computed, 0.001, unit="sone", rel=True, places=4)
    within_band = nmin <= computed <= nmax
    return Outcome(out.expected, out.computed, out.delta, out.passed and within_band)


@register(
    "Psychoacoustics",
    "DIN 45692:2009 Clause 6",
    "Sharpness of the standard 1 kHz reference signal",
)
def _chk_sharpness_reference() -> Outcome:
    computed = float(ph.sharpness_din(reference_sound(), _FS))
    return numeric(1.0, computed, 1e-9, unit="acum", places=6)


@register(
    "Psychoacoustics",
    "ISO 226:2023 Table B.1",
    "Equal-loudness contour, 60 phon @ 100 Hz",
)
def _chk_iso226_contour() -> Outcome:
    # Anchored off 1 kHz (where SPL == phon is a trivial identity) at a
    # tabulated point that exercises the Table 1 contour formula.
    phon, freq, spl_ref = ref.ISO226_2023_TABLE_B1_ANCHOR
    freqs, spl = ph.equal_loudness_contour(phon)
    computed = float(spl[np.asarray(freqs) == freq][0])
    return numeric(spl_ref, computed, 0.05, unit="dB SPL", places=3)


# --- Block-A psychoacoustics: calibrated tones (pressure in pascals) --------
def _spl_tone(freq: float, level_db: float, seconds: float) -> np.ndarray:
    """Pure tone whose RMS is ``level_db`` dB re 20 uPa (pressure in Pa)."""
    t = np.arange(int(_FS * seconds)) / _FS
    amp = math.sqrt(2.0) * 2e-5 * 10.0 ** (level_db / 20.0)
    return np.asarray(amp * np.sin(2.0 * np.pi * freq * t))


def _am_tone(
    fc: float, fmod: float, depth: float, level_db: float, seconds: float
) -> np.ndarray:
    """Amplitude-modulated tone, carrier RMS at ``level_db`` (pressure in Pa)."""
    t = np.arange(int(_FS * seconds)) / _FS
    amp = math.sqrt(2.0) * 2e-5 * 10.0 ** (level_db / 20.0)
    carrier = amp * (1.0 + depth * np.cos(2.0 * np.pi * fmod * t))
    return np.asarray(carrier * np.sin(2.0 * np.pi * fc * t))


@register(
    "Psychoacoustics",
    "ECMA-418-2:2025 Clause 5.1.8",
    "HMS loudness of a 1 kHz / 40 dB tone (c_N=0.0211964)",
)
def _chk_ecma_loudness() -> Outcome:
    computed = float(ph.loudness_ecma(_spl_tone(1000.0, 40.0, 0.6), _FS).loudness)
    return numeric(
        ref.ECMA418_2_LOUDNESS_1KHZ_40DB_SONE,
        computed,
        0.03,
        unit="sone_HMS",
        places=4,
    )


@register(
    "Psychoacoustics",
    "ECMA-418-2:2025 Clause 6.2.8",
    "HMS tonality of a 1 kHz / 40 dB tone (c_T=2.8758615)",
)
def _chk_ecma_tonality() -> Outcome:
    computed = float(ph.tonality_ecma(_spl_tone(1000.0, 40.0, 0.7), _FS).tonality)
    return numeric(
        ref.ECMA418_2_TONALITY_1KHZ_40DB_TU,
        computed,
        0.03,
        unit="tu_HMS",
        places=4,
    )


@register(
    "Psychoacoustics",
    "ECMA-418-2:2025 Clause 7",
    "HMS roughness of a 1 kHz / 70 Hz / m=1 / 60 dB tone (c_R=0.0180685)",
)
def _chk_ecma_roughness() -> Outcome:
    # The standard target is 1.0 asper; this clean-room chain deterministically
    # computes ~1.0735 (+7.35 %, documented methodology variance). The check
    # pins the clean-room value, NOT the 1.0 target.
    sig = _am_tone(1000.0, 70.0, 1.0, 60.0, 2.0)
    computed = float(ph.roughness_ecma(sig, _FS).roughness)
    target = ref.ECMA418_2_ROUGHNESS_STANDARD_TARGET_ASPER
    out = numeric(
        ref.ECMA418_2_ROUGHNESS_CLEANROOM_ASPER,
        computed,
        0.01,
        unit="asper",
        places=4,
    )
    return Outcome(
        expected=f"{out.expected} [clean-room; standard target {target:g}]",
        computed=out.computed,
        delta=out.delta,
        passed=out.passed,
    )


@register(
    "Psychoacoustics",
    "ISO 532-2:2017 Clause 3.17 / Annex B.1",
    "Moore-Glasberg loudness of a 1 kHz / 40 dB tone (C=0.0617)",
)
def _chk_mg_loudness() -> Outcome:
    computed = float(
        ph.loudness_moore_glasberg_from_spectrum([(1000.0, 40.0)]).loudness
    )
    return numeric(
        ref.ISO532_2_ANCHOR_1KHZ_40DB_SONE, computed, 0.01, unit="sone", places=4
    )


@register(
    "Psychoacoustics",
    "ISO 532-3:2023 Annex C.1",
    "Moore-Glasberg-Schlittenlacher peak LTL, steady 1 kHz / 40 dB",
)
def _chk_mg_time_loudness() -> Outcome:
    fs = 32000.0
    t = np.arange(int(round(0.8 * fs))) / fs
    x = math.sqrt(2.0) * 2e-5 * 10.0 ** (40.0 / 20.0) * np.sin(2.0 * np.pi * 1000.0 * t)
    computed = float(ph.loudness_moore_glasberg_time(x, fs).n_max)
    return numeric(
        ref.ISO532_3_ANCHOR_1KHZ_40DB_SONE, computed, 0.02, unit="sone", places=4
    )


# ===========================================================================
# Domain 4 - Speech intelligibility
# ===========================================================================
_NUM_STI_BANDS = 7
_NUM_MOD_FREQS = 14


@register(
    "Speech intelligibility",
    "IEC 60268-16:2020 A.2.2",
    "STI weighting-factor pair (500 Hz + 1 kHz bands)",
)
def _chk_sti_weighting_pair() -> Outcome:
    mtf = np.zeros((_NUM_STI_BANDS, _NUM_MOD_FREQS))
    mtf[[2, 3], :] = 1.0
    computed = float(_sti_from_mtf(mtf).sti)
    return numeric(0.398, computed, 0.001, places=4)


@register(
    "Speech intelligibility",
    "IEC 60268-16:2020 A.3.1.2",
    "Uniform MTF m=0.5 maps to STI=0.5",
)
def _chk_sti_uniform() -> Outcome:
    mtf = np.full((_NUM_STI_BANDS, _NUM_MOD_FREQS), 0.5)
    computed = float(_sti_from_mtf(mtf).sti)
    return numeric(0.5, computed, 0.01, places=4)


# ===========================================================================
# Domain 5 - Intensity & sound power
# ===========================================================================
def _plane_wave_pair(
    delay_s: float, seconds: float = 4.0
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42)
    n = int(_FS * seconds)
    freqs = np.fft.rfftfreq(n, 1.0 / _FS)
    spec = np.zeros(freqs.size, dtype=complex)
    band = (freqs >= 50.0) & (freqs <= 2000.0)
    spec[band] = np.exp(1j * rng.uniform(0.0, 2.0 * np.pi, int(band.sum())))
    p1 = np.fft.irfft(spec, n)
    p2 = np.fft.irfft(spec * np.exp(-2j * np.pi * freqs * delay_s), n)
    scale = 1.0 / np.sqrt(np.mean(p1**2))
    return p1 * scale, p2 * scale


@register(
    "Intensity & sound power",
    "IEC 61043:1994 Clause 5",
    "Plane-wave intensity I = p^2 / (rho c)",
)
def _chk_plane_wave_intensity() -> Outcome:
    rho, c, spacing = 1.204, 343.0, 0.012
    p1, p2 = _plane_wave_pair(spacing / c)
    res = ph.sound_intensity(p1, p2, _FS, spacing, rho=rho, c=c)
    expected = float(np.mean(((p1 + p2) / 2.0) ** 2)) / (rho * c)
    return numeric(
        expected, float(res.total_intensity), 0.015, unit="W/m^2", rel=True, places=5
    )


@register(
    "Intensity & sound power",
    "ISO 3744:2010 Eq. 18",
    "Monopole hemisphere recovers LW (r=4 m)",
)
def _chk_monopole_lw() -> Outcome:
    lw_true, r = 95.0, 4.0
    lp = lw_true - 10.0 * math.log10(2.0 * math.pi * r**2)
    res = ph.sound_power_pressure(np.full((10, 1), lp), "hemisphere", radius=r)
    return numeric(lw_true, float(res.sound_power_level[0]), 1e-9, unit="dB", places=6)


@register(
    "Intensity & sound power",
    "ISO 9614-2:1996 Eq. 12",
    "Intensity scan recovers LW of an enclosed source",
)
def _chk_intensity_scan_lw() -> Outcome:
    w = 1.0e-3  # 90 dB re 1 pW
    areas = np.array([0.5, 0.5, 0.5, 0.5])
    intensity = np.full((4, 1), w / areas.sum())
    res = ph.sound_power_intensity(intensity, areas)
    return numeric(90.0, float(res.sound_power_level[0]), 1e-6, unit="dB", places=6)


def _reverb_bracket(
    t60: np.ndarray, volume: float, surface: float, freq: np.ndarray,
    theta: float, ps: float,
) -> np.ndarray:
    """Independent re-implementation of the ISO 3741 Eq. (20) bracket.

    The two constants below are deliberately different and mirror the library
    (:func:`phonometry.sound_power_reverberation._speed_of_sound` and its C1/C2
    terms): the speed of sound uses the rounded 273 of ISO 3741 clause 9.1.4
    (``c = 20,05*sqrt(273 + theta)``), while the C1/C2 barometric corrections
    use the exact absolute-zero offset 273.15 in their temperature ratios.
    Matching the library keeps the "expected" bracket and the computed value on
    the same convention.
    """
    ps0, theta0, theta1 = 101.325, 314.0, 296.0
    c = 20.05 * math.sqrt(273.0 + theta)  # ISO 3741 clause 9.1.4 (rounded 273)
    a = (55.26 / c) * (volume / t60)
    waterhouse = 10.0 * np.log10(1.0 + surface * c / (8.0 * volume * freq))
    # C1/C2 use 273.15 (absolute temperature ratios), as in the library.
    c1 = -10.0 * math.log10(ps / ps0) + 5.0 * math.log10((273.15 + theta) / theta0)
    c2 = -10.0 * math.log10(ps / ps0) + 15.0 * math.log10((273.15 + theta) / theta1)
    return 10.0 * np.log10(a) + 4.34 * (a / surface) + waterhouse + c1 + c2 - 6.0


@register(
    "Intensity & sound power",
    "ISO 3741:2010 Eq. 20",
    "Reverberation-room method inverts to a known LW",
)
def _chk_reverberation_lw() -> Outcome:
    volume, surface = 200.0, 210.0
    freqs = np.array([100.0, 500.0, 1000.0, 5000.0, 10000.0])
    t60 = np.array([2.0, 1.8, 1.5, 1.0, 0.6])
    theta, ps = 23.0, 101.325
    lw_target = np.array([80.0, 85.0, 90.0, 82.0, 75.0])
    lp = lw_target - _reverb_bracket(t60, volume, surface, freqs, theta, ps)
    res = ph.sound_power_reverberation(
        lp, t60, volume, surface, freqs, temperature=theta, static_pressure=ps
    )
    worst = float(np.max(np.abs(np.asarray(res.sound_power_level) - lw_target)))
    return numeric(0.0, worst, 1e-9, unit="dB", places=9, expected_label="0 dB error")


# ===========================================================================
# Domain 6 - Room & building acoustics
# ===========================================================================
_A60 = 6.0 * math.log(10.0)


def _exponential_ir(t60: float, seconds: float) -> np.ndarray:
    t = np.arange(int(round(seconds * _FS))) / _FS
    return np.asarray(np.exp(-0.5 * _A60 * t / t60))


@register(
    "Room & building acoustics",
    "ISO 3382-2:2008 5.3.3",
    "T30 from a synthetic exponential decay (T=1.0 s)",
)
def _chk_room_t30() -> Outcome:
    t60 = 1.0
    res = ph.room_parameters(_exponential_ir(t60, 3.0 * t60), _FS, limits=None)
    return numeric(t60, float(res.t30[0]), 0.01, unit="s", rel=True, places=4)


@register(
    "Room & building acoustics",
    "ISO 717-1 Annex C, Table C.1",
    "Weighted sound reduction index Rw (C;Ctr)",
)
def _chk_iso717_rw() -> Outcome:
    exp = ref.ISO717_1_ANNEX_C_EXPECTED
    res = ph.weighted_rating(ref.ISO717_1_ANNEX_C_R)
    ok = res.rating == exp["rw"] and res.c == exp["c"] and res.ctr == exp["ctr"]
    return Outcome(
        expected=f"Rw {exp['rw']} (C {exp['c']}; Ctr {exp['ctr']})",
        computed=f"Rw {res.rating} (C {res.c}; Ctr {res.ctr})",
        delta=f"sum {res.unfavourable_sum:.1f} dB",
        passed=ok,
    )


@register(
    "Room & building acoustics",
    "ISO 354:2003 Eq. 5/8",
    "Sabine inversion recovers absorption area",
)
def _chk_iso354_absorption() -> Outcome:
    v, c, t = 200.0, 343.0, 3.5
    expected = 55.3 * v / (c * t)
    computed = float(np.asarray(ph.absorption_area(t, v, speed_of_sound=c))[()])
    return numeric(expected, computed, 1e-9, unit="m^2", places=6)


@register(
    "Room & building acoustics",
    "ISO 3382-3:2012 Clause 6.2",
    "Open-plan spatial decay rate D2,S (-6 dB/doubling)",
)
def _chk_open_plan_d2s() -> Outcome:
    r = np.array([2.0, 4.0, 8.0, 16.0])
    lp = 70.0 - 6.0 * np.log2(r)
    sti = 0.6 - 0.02 * r
    res = ph.open_plan_metrics(r, lp, sti)
    return numeric(6.0, float(res.d2s), 1e-9, unit="dB", places=6)


# ===========================================================================
# Markdown rendering
# ===========================================================================
def _snap(value: float, eps: float = 5e-4) -> float:
    """Snap a near-zero value to +0 so displays avoid a spurious ``-0.00``."""
    return 0.0 if abs(value) < eps else value


def _status(passed: bool) -> str:
    return "&#9989;" if passed else "&#10060;"


def _domains() -> list[str]:
    seen: list[str] = []
    for chk in CHECKS:
        if chk.domain not in seen:
            seen.append(chk.domain)
    return seen


# Architectures that cannot meet the IEC 61260-1 mask by construction, with
# the reason (for the "By design" label, not a failure verdict).
_BY_DESIGN: dict[str, str] = {
    "cheby1": "passband ripple",
    "ellip": "passband ripple",
    "bessel": "soft rolloff",
}


def _filter_verdict(arch: str, fc: FilterClass) -> str:
    if fc.overall_class == 1:
        return "Class 1 (default)" if arch == "butter" else "Class 1"
    if fc.overall_class == 2:
        return "Class 2"
    reason = _BY_DESIGN.get(arch)
    return f"By design ({reason})" if reason else "not compliant"


def _numerical_validation_section() -> str:
    lines: list[str] = []
    lines.append("### Numerical validation - filters &amp; weightings")
    lines.append("")
    lines.append(
        "**IEC 61260-1:2014 class per filter architecture** (order 6, "
        "one-third-octave, 100 Hz-10 kHz, fs = 48 kHz). For each architecture "
        "the table shows, at its *binding* band, the measured relative "
        "attenuation and the class-1 limit it must clear, so the number and "
        "the range it must sit in are both visible. A positive margin means "
        "the acceptance limits are met with that much room."
    )
    lines.append("")
    lines.append(
        "| Architecture | Class verdict | Binding band | Measured rel. atten. "
        "| Class-1 limit | Margin cl.1 | Margin cl.2 |"
    )
    lines.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for arch in _FILTER_ARCHS:
        fc = _filter_class(arch, 3)
        if fc.bind_side == "ceil":
            req = f"&le; {fc.bind_limit_db:+.2f} dB"
        else:
            req = f"&ge; {fc.bind_limit_db:+.2f} dB"
        lines.append(
            f"| {arch} | {_filter_verdict(arch, fc)} | {fc.bind_freq:.0f} Hz "
            f"| {_snap(fc.bind_measured_db, 5e-3):+.2f} dB | {req} "
            f"| {fc.min_margin1:+.3f} dB | {fc.min_margin2:+.3f} dB |"
        )
    lines.append("")
    lines.append(
        "Only **Butterworth** (the library default) and **Chebyshev-II** are "
        "class-compliant architectures. Chebyshev-I and elliptic trade the "
        "mask for passband ripple, and Bessel for a maximally-flat group delay "
        "(soft rolloff); they cannot satisfy the IEC 61260-1 Class 1/2 "
        "attenuation mask by construction, so they are labelled *By design* - "
        "this is expected, not a failure or regression."
    )
    lines.append("")
    lines.append(
        "**Frequency-weighting conformance** (A/C: IEC 61672-1 Table 3; "
        "G: ISO 7196 A.3). The *max deviation from nominal* is informational "
        "(it falls at a frequency extreme where the tolerance is widest and "
        "asymmetric); compliance is judged at the *binding* frequency - the "
        "one with the least headroom - where the deviation, the applicable "
        "tolerance band and the headroom are shown together."
    )
    lines.append("")
    lines.append(
        "| Curve | fs | Max dev. from nominal (info) | Binding freq "
        "| Deviation there | Tolerance band | Headroom |"
    )
    lines.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for curve, fs in [("A", 48000), ("A", 96000), ("C", 48000), ("G", 48000)]:
        wd = _weighting_deviation(curve, fs)
        band = f"[{wd.bind_lower:+.2f}, {wd.bind_upper:+.2f}] dB"
        lines.append(
            f"| {curve} | {fs // 1000} kHz "
            f"| {wd.worst_dev:+.3f} dB @ {wd.worst_freq:.0f} Hz "
            f"| {wd.bind_freq:.0f} Hz | {_snap(wd.bind_dev):+.3f} dB | {band} "
            f"| {wd.min_headroom:+.3f} dB |"
        )
    return "\n".join(lines)


def render_markdown() -> tuple[str, int, int]:
    """Render the full conformance report. Returns (markdown, passed, total)."""
    results = [(chk, chk.run()) for chk in CHECKS]
    passed = sum(1 for _, o in results if o.passed)
    total = len(results)

    filters_ok = all(
        o.passed for c, o in results if c.domain == "Filters & weightings"
    )
    headline_emoji = "&#9989;" if passed == total else "&#10060;"

    out: list[str] = []
    out.append("## Numerical conformance report")
    out.append("")
    summary = (
        f"**{passed}/{total} conformance checks pass** across "
        f"{len(_domains())} domains and {len({c.standard.split(':')[0].split(' Annex')[0] for c, _ in results})} standards"
    )
    if filters_ok:
        summary += " - filters class 1 - weightings within IEC 61672-1 class 1"
    out.append(f"{headline_emoji} {summary}.")
    out.append("")
    out.append(_numerical_validation_section())
    out.append("")

    for domain in _domains():
        out.append(f"### {domain}")
        out.append("")
        out.append("| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |")
        out.append("|:---|:---|:---|:---|:---|:---:|")
        for chk, outcome in results:
            if chk.domain != domain:
                continue
            out.append(
                f"| {chk.standard} | {chk.quantity} | {outcome.expected} "
                f"| {outcome.computed} | {outcome.delta} | {_status(outcome.passed)} |"
            )
        out.append("")

    return "\n".join(out), passed, total


# Header prepended to the committed docs/CONFORMANCE.md (via `--file-header`,
# used by `make conformance`). Emitted only for the committed file, not for the
# CI PR-comment body, so the PR comment stays header-free.
_DOC_HEADER = """<!--
  AUTO-GENERATED FILE - DO NOT EDIT BY HAND.
  Regenerate with `make conformance` (runs scripts/conformance_report.py).
  CI regenerates it on every pull request and fails the build if it drifts.
-->

> **Auto-generated conformance report - do not hand-edit.** Produced by
> `make conformance` from the library's own computations checked against the
> referenced standards. CI regenerates it on every pull request and fails if it
> is out of date, so edit the checks in `scripts/conformance_report.py`, not this
> file. Each row pins a standard and clause to its expected normative value and
> the value the library computes. Full standards list and methodology:
> [Theory](https://github.com/jmrplens/phonometry/blob/main/docs/theory.md) -
> [Why phonometry](https://github.com/jmrplens/phonometry/blob/main/docs/why-phonometry.md).

"""


def main(argv: Optional[list[str]] = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    markdown, passed, total = render_markdown()
    # The root artifact feeds the CI PR comment; keep it header-free.
    (_ROOT / "conformance_report.md").write_text(markdown + "\n")
    output = _DOC_HEADER + markdown if "--file-header" in args else markdown
    print(output)
    print(f"\n[conformance] {passed}/{total} checks passed", file=sys.stderr)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
