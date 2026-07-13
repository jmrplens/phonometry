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
from typing import Callable, Literal, Optional, cast

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
from phonometry.metrology.compliance import class_limits, verify_filter_class  # noqa: E402
from phonometry.psychoacoustics.sharpness import reference_sound  # noqa: E402
from phonometry.hearing.sti import _sti_from_mtf  # noqa: E402


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


@register(
    "Filters & weightings",
    "IEC 61260:1995 / ANSI S1.11-2004 Table 1",
    "Class 0 (strictest) octave-band filter (butterworth, fs=48 kHz)",
)
def _chk_butter_class0_1995() -> Outcome:
    bank = OctaveFilterBank(48000, fraction=1, order=6, limits=[100, 10000], filter_type="butter")
    result = ph.verify_filter_class(bank, edition="1995")
    margin = min(b["margin_class0_db"] for b in result["bands"])
    ok = result["overall_class"] == 0
    return Outcome(
        expected="class 0",
        computed=(f"class {result['overall_class']}" if result["overall_class"] is not None
                  else "none") + f" (margin {margin:+.3f} dB)",
        delta=f"{margin:+.3f} dB",
        passed=ok,
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


@register(
    "Levels & dosimetry",
    "ISO 1996-2:2007 Annex C.5 Example 1",
    "Tonal audibility ΔLta (Formula C.3), 4 kHz tone",
)
def _chk_iso1996_2_tonal_audibility() -> Outcome:
    lpt, lpn, fc, delta_expected, _kt = ref.ISO1996_2_TONAL_EXAMPLES[0]
    computed = ph.tonal_audibility(lpt, lpn, fc)
    return numeric(delta_expected, computed, 0.05, unit="dB", places=2)


@register(
    "Levels & dosimetry",
    "ISO 1996-2:2007 Annex C.5 Example 1",
    "Tonal adjustment Kt (Formulae C.4-C.6)",
)
def _chk_iso1996_2_tonal_adjustment() -> Outcome:
    lpt, lpn, fc, _delta, kt_expected = ref.ISO1996_2_TONAL_EXAMPLES[0]
    computed = ph.tonal_adjustment(ph.tonal_audibility(lpt, lpn, fc))
    return numeric(kt_expected, computed, 1e-9, unit="dB", places=2)


@register(
    "Levels & dosimetry",
    "ISO 1996-2:2017 Annex G.2",
    "Combined measurement uncertainty u = √(Σ(cj·uj)²)",
)
def _chk_iso1996_2_uncertainty() -> Outcome:
    computed = ph.combined_standard_uncertainty(ref.ISO1996_2_G2_CONTRIBUTIONS)
    return numeric(ref.ISO1996_2_G2_COMBINED, computed, 0.01, unit="dB", places=2)


# ---------------------------------------------------------------------------
# Reverberation-time prediction (Sabine / Eyring / Millington / Fitzroy /
# Arau-Puchades). No source carries a machine-readable worked example, so the
# checks anchor on hand-computed closed-form values and the model identities.
# ---------------------------------------------------------------------------
# Shoebox 8x5x3 m: V = 120 m3, S = 158 m2. Values hand-derived with the default
# c0 = 343 m/s (Sabine constant k = 24 ln10 / c0 = 0.161113...).
_RT_DIMS = (8.0, 5.0, 3.0)
_RT_VOLUME = 120.0
_RT_SURFACES = [
    (40.0, 0.2), (40.0, 0.2), (24.0, 0.2), (24.0, 0.2), (15.0, 0.2), (15.0, 0.2)
]


@register(
    "Room acoustics",
    "Sabine (W. C. Sabine, 1922)",
    "Reverberation time T = k·V/A  (V=120 m³, S=158 m², α=0.2)",
)
def _chk_sabine_rt() -> Outcome:
    computed = float(ph.sabine_reverberation_time(_RT_VOLUME, _RT_SURFACES))
    return numeric(0.6118246547, computed, 1e-6, unit="s", places=6)


@register(
    "Room acoustics",
    "Everest, Master Handbook of Acoustics 4th ed, Fig. 7-22",
    "Sabine RT, worked Example 1 @ 1 kHz (untreated 23.3×16×10 ft room, SI)",
)
def _chk_sabine_everest() -> Outcome:
    surfaces = [
        (ref.EVEREST_EX1_FLOOR_AREA, ref.EVEREST_EX1_FLOOR_ALPHA[3]),
        (ref.EVEREST_EX1_SHELL_AREA, ref.EVEREST_EX1_SHELL_ALPHA[3]),
    ]
    computed = float(ph.sabine_reverberation_time(ref.EVEREST_EX1_VOLUME, surfaces))
    return numeric(ref.EVEREST_EX1_RT[3], computed, 0.02, unit="s", places=3)


@register(
    "Room acoustics",
    "Eyring (Norris-Eyring, 1930)",
    "Reverberation time T = k·V/(-S·ln(1-ᾱ))  (α=0.2)",
)
def _chk_eyring_rt() -> Outcome:
    computed = float(ph.eyring_reverberation_time(_RT_VOLUME, _RT_SURFACES))
    return numeric(0.5483686633, computed, 1e-6, unit="s", places=6)


@register(
    "Room acoustics",
    "Arau-Puchades (Acustica 65, 1988, Formula 18)",
    "T (α=0.5/0.1/0.1 per wall pair, dims 8×5×3 m)",
)
def _chk_arau_rt() -> Outcome:
    computed = float(ph.arau_puchades_reverberation_time(_RT_DIMS, (0.5, 0.1, 0.1)))
    return numeric(0.8121469281, computed, 1e-6, unit="s", places=6)


@register(
    "Room acoustics",
    "Model identity (uniform absorption)",
    "Arau-Puchades ≡ Eyring when ᾱ is uniform",
)
def _chk_arau_eyring_identity() -> Outcome:
    eyring = float(ph.eyring_reverberation_time(_RT_VOLUME, _RT_SURFACES))
    arau = float(ph.arau_puchades_reverberation_time(_RT_DIMS, (0.2, 0.2, 0.2)))
    return numeric(eyring, arau, 1e-9, unit="s", places=6,
                   expected_label=f"{eyring:.6f} s (= Eyring)")


# ===========================================================================
# Domain 3 - Psychoacoustics
# ===========================================================================
def _iso532_stationary_expected() -> tuple[float, float, float]:
    data = json.loads((_DATA / "iso532_1" / "iso532_1_annexB_expected.json").read_text())
    entry = data["Test signal 1.txt"]
    return entry["N"], entry["Nmin"], entry["Nmax"]


def _iso532_levels() -> np.ndarray:
    levels = []
    for line in (_DATA / "iso532_1" / "iso532_1_test_signal_1_levels.txt").read_text().splitlines():
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


def _iso532_b5_signal(
    num: int,
) -> tuple[np.ndarray, int, float, Literal["free", "diffuse"]]:
    """Load a recorded ISO 532-1 Annex B.5 technical signal and its expected values.

    Returns the pressure signal, its sample rate, the expected maximum loudness
    Nmax (sone) and the sound field the ISO results workbook was computed in.
    The 16-bit WAV is scaled per Annex B.1 (full scale = 100 dB SPL, so one
    full-scale unit is 2*sqrt(2) Pa peak).
    """
    import glob
    import wave

    data = json.loads((_DATA / "iso532_1" / "iso532_1_annexB_expected.json").read_text())
    entry = data[f"Test signal {num}"]
    matches = glob.glob(str(_DATA / "iso532_1" / "Annex B.5" / f"Test signal {num} *.wav"))
    if not matches:
        raise FileNotFoundError(
            f"No ISO 532-1 Annex B.5 WAV found for Test signal {num} "
            "(see tests/data/iso532_1/README.md)."
        )
    # WAV/RIFF is little-endian, so the dtype is fixed to '<i2'; a multi-channel
    # file keeps only channel 0.
    with wave.open(matches[0]) as handle:
        fs = handle.getframerate()
        n_channels = handle.getnchannels()
        raw = np.frombuffer(handle.readframes(handle.getnframes()), dtype="<i2")
    if n_channels > 1:
        raw = raw.reshape(-1, n_channels)[:, 0]
    signal = raw.astype(np.float64) / 32768.0 * (2.0 * math.sqrt(2.0))
    field = str(entry["field"])
    if field not in ("free", "diffuse"):
        raise ValueError(f"unexpected sound field {field!r} in the workbook")
    return signal, int(fs), float(entry["Nmax"]), cast(Literal["free", "diffuse"], field)


@register(
    "Psychoacoustics",
    "ISO 532-1:2017 Annex B.5",
    "Time-varying loudness Nmax, technical signal 14 (aircraft, free field)",
)
def _chk_iso532_b5_free() -> Outcome:
    signal, fs, nmax, field = _iso532_b5_signal(14)
    res = ph.loudness_zwicker(signal, fs, field=field)
    return numeric(nmax, float(res.loudness), 0.001, unit="sone", rel=True, places=4)


@register(
    "Psychoacoustics",
    "ISO 532-1:2017 Annex B.5",
    "Time-varying loudness Nmax, technical signal 15 (vehicle interior, diffuse field)",
)
def _chk_iso532_b5_diffuse() -> Outcome:
    signal, fs, nmax, field = _iso532_b5_signal(15)
    res = ph.loudness_zwicker(signal, fs, field=field)
    return numeric(nmax, float(res.loudness), 0.001, unit="sone", rel=True, places=4)


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
# Domain 4 - Speech transmission (IEC 60268-16)
# ===========================================================================
_NUM_STI_BANDS = 7
_NUM_MOD_FREQS = 14


@register(
    "Speech transmission (IEC 60268-16)",
    "IEC 60268-16:2020 A.2.2",
    "STI weighting-factor pair (500 Hz + 1 kHz bands)",
)
def _chk_sti_weighting_pair() -> Outcome:
    mtf = np.zeros((_NUM_STI_BANDS, _NUM_MOD_FREQS))
    mtf[[2, 3], :] = 1.0
    computed = float(_sti_from_mtf(mtf).sti)
    return numeric(0.398, computed, 0.001, places=4)


@register(
    "Speech transmission (IEC 60268-16)",
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
    (:func:`phonometry.emission.sound_power_reverberation._speed_of_sound` and its C1/C2
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
    "ISO 18233:2006 (swept-sine method)",
    "Sweep deconvolution recovers a known IIR response",
)
def _chk_iso18233_sweep_deconvolution() -> Outcome:
    # Closed-form identity: an exponential sweep through a known Butterworth
    # band-pass, deconvolved back, must reproduce the filter's freqz response.
    b, a = sg.butter(4, [200.0, 2000.0], btype="band", fs=_FS)
    x = ph.sweep_signal(_FS, 20.0, 20000.0, 2.0)
    y = sg.lfilter(b, a, x)
    ir = np.asarray(ph.impulse_response(y, x, _FS, length=16384))
    freqs = np.fft.rfftfreq(ir.size, d=1.0 / _FS)
    h_est = np.fft.rfft(ir)
    _, h_true = sg.freqz(b, a, worN=freqs, fs=_FS)
    mask = (freqs >= 300.0) & (freqs <= 1500.0)
    worst = float(np.max(np.abs(
        20.0 * np.log10(np.abs(h_est[mask])) - 20.0 * np.log10(np.abs(h_true[mask]))
    )))
    # Linear deconvolution is exact in-band up to windowing/regularisation
    # leakage; 0.1 dB is the demonstrated in-band bound (tests/test_room_ir.py)
    # with the same 300-1500 Hz evaluation band, well inside the sweep edges.
    return numeric(0.0, worst, 0.1, unit="dB", places=4,
                   expected_label="0 dB in-band error (+/-0.1 dB)")


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
    "ISO 717-2 Annex C, Table C.1",
    "Weighted impact sound pressure level Ln,w (CI)",
)
def _chk_iso717_2_lnw() -> Outcome:
    # Worked example: Ln,w = 79 dB, CI = -11 dB, unfavourable sum 28,0 dB.
    # Integer ratings and CI must match exactly; the unfavourable sum is a
    # one-decimal tabulated intermediate, so 1e-9 = exact up to float noise.
    exp = ref.ISO717_2_ANNEX_C1_EXPECTED
    res = ph.weighted_impact_rating(ref.ISO717_2_ANNEX_C1_LN)
    sum_ok = abs(res.unfavourable_sum - exp["unfavourable_sum"]) <= 1e-9
    ok = res.rating == exp["ln_w"] and res.ci == exp["ci"] and sum_ok
    return Outcome(
        expected=f"Ln,w {exp['ln_w']} (CI {exp['ci']}; sum {exp['unfavourable_sum']:.1f} dB)",
        computed=f"Ln,w {res.rating} (CI {res.ci}; sum {res.unfavourable_sum:.1f} dB)",
        delta=f"{res.rating - exp['ln_w']:+d} dB",
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


@register(
    "Room & building acoustics",
    "ISO 16283-3:2016 Clause 3.12",
    "Facade R'45 isolates the -1.5 dB incidence correction (S=A)",
)
def _chk_facade_r45() -> Outcome:
    # With S = A the 10 lg(S/A) coupling term vanishes, so R' = L1,s - L2 - 1,5.
    n = 3
    res = ph.facade_insulation(
        np.full(n, 55.0),
        np.full(n, ref.ISO16283_3_R45_RECEIVE_LEVEL_DB),
        np.full(n, ref.ISO16283_3_R45_REVERB_TIME_S),
        area=ref.ISO16283_3_R45_AREA_M2,
        volume=ref.ISO16283_3_R45_VOLUME_M3,
        surface_level=np.full(n, ref.ISO16283_3_R45_SURFACE_LEVEL_DB),
    )
    assert res.r_prime is not None
    # The expected value is rebuilt from its components, so the -1,5 dB
    # oblique-incidence correction constant is exercised explicitly.
    expected = (
        ref.ISO16283_3_R45_SURFACE_LEVEL_DB
        - ref.ISO16283_3_R45_RECEIVE_LEVEL_DB
        - ref.ISO16283_3_R45_LOUDSPEAKER_CORRECTION_DB
    )
    assert expected == ref.ISO16283_3_R45_EXPECTED_DB
    computed = float(np.asarray(res.r_prime)[0])
    return numeric(expected, computed, 1e-9, unit="dB", places=6)


@register(
    "Room & building acoustics",
    "ISO 10140-2:2010 Formula (2)",
    "Lab airborne R on the ISO 717-1 reference shape -> Rw = 54",
)
def _chk_lab_airborne_rw() -> Outcome:
    # S = A (A = 0,16*50/0,8 = 10 = area) => R = L1 - L2 = the reference curve.
    ref_r = np.asarray(ref.ISO10140_2_REF_AIRBORNE_R, dtype=float)
    res = ph.lab_airborne_insulation(
        np.full(16, 90.0), 90.0 - ref_r, np.full(16, 0.8), area=10.0, volume=50.0
    )
    assert res.rating is not None
    # R lands exactly on the reference; guard that before reading the rating.
    on_curve = bool(np.allclose(np.asarray(res.r), ref_r))
    expected = ref.ISO10140_2_REF_AIRBORNE_RW
    return Outcome(
        expected=f"Rw {expected} dB",
        computed=f"Rw {res.rating.rating} dB",
        delta=f"{res.rating.rating - expected:+d} dB",
        passed=on_curve and res.rating.rating == expected,
    )


@register(
    "Room & building acoustics",
    "ISO 15186-1:2000 Formula (7)",
    "Intensity RI on the ISO 717-1 reference shape -> RI,w = 30",
)
def _chk_intensity_ri_rw() -> Outcome:
    # Choose LIn so that RI = Lp1 - 6 - [LIn + 10 lg(Sm/S)] lands exactly on
    # the ISO 717-1 Annex C curve; the rating engine must then return Rw = 30.
    ref_ri = np.asarray(ref.ISO15186_1_REF_RI, dtype=float)
    lp1, sm, s = ref.ISO15186_1_REF_LP1, ref.ISO15186_1_REF_SM, ref.ISO15186_1_REF_S
    lin = lp1 - 6.0 - 10.0 * np.log10(sm / s) - ref_ri
    res = ph.intensity_sound_reduction(
        np.full(16, lp1), lin, measurement_area=sm, area=s
    )
    assert res.rating is not None
    on_curve = bool(np.allclose(np.asarray(res.r_i), ref_ri))
    expected = ref.ISO15186_1_REF_RIW
    return Outcome(
        expected=f"RI,w {expected} dB",
        computed=f"RI,w {res.rating.rating} dB",
        delta=f"{res.rating.rating - expected:+d} dB",
        passed=on_curve and res.rating.rating == expected,
    )


@register(
    "Room & building acoustics",
    "ISO 15186-1:2000 Annex B",
    "Adaptation term Kc: reference-room (B.1) reduces to (B.2)",
)
def _chk_intensity_kc_annexb() -> Outcome:
    # Formula (B.1) with Sb2 = 117 m², V2 = 81 m³, c = 340 m/s must reproduce
    # the room-independent approximation Kc = 10 lg(1 + 61,4/f) of (B.2).
    b2 = ph.adaptation_term_kc(ref.ISO15186_1_KC_BANDS)
    b1 = ph.adaptation_term_kc(
        ref.ISO15186_1_KC_BANDS, boundary_area=117.0, volume=81.0
    )
    tab = np.asarray(ref.ISO15186_1_KC_B2, dtype=float)
    delta = float(np.max(np.abs(b1 - b2)))
    passed = bool(np.allclose(b2, tab, atol=5e-4)) and delta <= 1e-3
    return Outcome(
        expected="max abs(B.1 - B.2) <= 0,001 dB",
        computed=f"{delta:.2e} dB (Kc@1k = {b2[3]:.3f} dB)",
        delta=f"{delta:.2e} dB",
        passed=passed,
    )


@register(
    "Room & building acoustics",
    "ISO 10052:2021 Clause 3.6",
    "Survey R' applies the V/7,5 minimum-area rule",
)
def _chk_survey_rprime_area_rule() -> Outcome:
    # V/7,5 = 120/7,5 = 16 m^2 > S = 5 m^2, so the larger value replaces S.
    # With k = 0 (T = T0), R' = D + 10 lg(16 * T0 / (0,16 V)).
    v, s, d = 120.0, 5.0, 30.0
    res = ph.survey_airborne_insulation(
        np.full(5, 70.0), np.full(5, 40.0), np.zeros(5), volume=v, area=s
    )
    assert res.r_prime is not None
    s_eff = v / 7.5
    expected = d + 10.0 * np.log10(s_eff * 0.5 / (0.16 * v))
    return numeric(expected, float(res.r_prime[0]), 1e-9, unit="dB", places=6)


@register(
    "Room & building acoustics",
    "ISO 10052:2021 Clause 3.16",
    "Service-equipment LXY is the 3-position energy average",
)
def _chk_survey_service_equipment() -> Outcome:
    # Energy average of 35 / 30 / 32 dB(A), then standardized by k.
    levels = [35.0, 30.0, 32.0]
    res = ph.survey_service_equipment_level(levels, 3.0, volume=50.0)
    expected = 10.0 * np.log10(sum(10.0 ** (0.1 * x) for x in levels) / 3.0)
    return numeric(expected, float(np.asarray(res.l_xy)[()]), 1e-9, unit="dB", places=6)


@register(
    "Room & building acoustics",
    "ISO 10052:2021 Table 4",
    "Reverberation-index estimate (35 <= V < 60, type g)",
)
def _chk_survey_reverberation_estimate() -> Outcome:
    # Table 4 row 'g' for 35 <= V < 60: 4,5 / 5 / 5,5 / 5,5 / 5,5 dB.
    expected = [4.5, 5.0, 5.5, 5.5, 5.5]
    got = np.asarray(ph.estimate_reverberation_index(50.0, "g"), dtype=float)
    ok = bool(np.array_equal(got, expected))
    return Outcome(
        expected=f"k = {expected} dB",
        computed=f"k = {got.tolist()} dB",
        delta="exact",
        passed=ok,
    )


@register(
    "Room & building acoustics",
    "ISO 717-2:2020 Table 4 / Clause 5.2",
    "Reference-floor weighted level Ln,r,0,w and CI (ISO 16251-1 ΔLw anchor)",
)
def _chk_iso717_2_reference_floor() -> Outcome:
    res = ph.weighted_impact_rating(ref.ISO717_2_REFERENCE_FLOOR_LN_R0)
    ok = (
        res.rating == ref.ISO717_2_REFERENCE_FLOOR_LN_R0_W
        and res.ci == ref.ISO717_2_REFERENCE_FLOOR_CI
    )
    return Outcome(
        expected=f"Ln,r,0,w = {ref.ISO717_2_REFERENCE_FLOOR_LN_R0_W} dB, "
        f"CI = {ref.ISO717_2_REFERENCE_FLOOR_CI} dB",
        computed=f"Ln,r,0,w = {res.rating} dB, CI = {res.ci} dB",
        delta="exact",
        passed=ok,
    )


@register(
    "Room & building acoustics",
    "ISO 16251-1:2014 / ISO 717-2 Formula (2)",
    "Floor-covering ΔLw: zero improvement gives ΔLw = 0",
)
def _chk_iso16251_zero_improvement() -> Outcome:
    import numpy as _np

    dlw = ph.weighted_impact_improvement(_np.zeros(16))
    return Outcome(
        expected="ΔLw = 0 dB (ΔL = 0 -> Ln,r = Ln,r,0)",
        computed=f"ΔLw = {dlw} dB",
        delta="exact",
        passed=(dlw == 0),
    )


@register(
    "Room & building acoustics",
    "ISO 10848-1:2006 Formula (14)",
    "Flanking Kij (simplified) matches closed form",
)
def _chk_iso10848_kij_simplified() -> Outcome:
    # No worked example in the standard; anchor on the closed form recomputed
    # independently here (delta is "exact" to keep the report byte-stable).
    res = ph.vibration_reduction_index(
        [ref.ISO10848_KIJ_DBAR],
        ref.ISO10848_KIJ_LIJ,
        ref.ISO10848_KIJ_AREA,
        ref.ISO10848_KIJ_AREA,
    )
    computed = float(res.k_ij[0])
    expected = ref.ISO10848_KIJ_DBAR + 10.0 * math.log10(
        ref.ISO10848_KIJ_LIJ / math.sqrt(ref.ISO10848_KIJ_AREA**2)
    )
    return Outcome(
        expected=f"Kij = {expected:.4f} dB",
        computed=f"Kij = {computed:.4f} dB",
        delta="exact",
        passed=abs(computed - expected) < 1e-9,
    )


@register(
    "Room & building acoustics",
    "ISO 10848-1:2006 Formula (12)",
    "Flanking equivalent absorption length aj at f_ref",
)
def _chk_iso10848_absorption_length() -> Outcome:
    a = ph.equivalent_absorption_length(
        ref.ISO10848_ABS_AREA,
        ref.ISO10848_ABS_TS,
        [1000.0],
        speed_of_sound=ref.ISO10848_ABS_C0,
    )
    computed = float(a[0])
    # aj at f = f_ref (sqrt(f_ref/f) = 1): aj = 2,2·π²·S/(Ts·c0).
    expected = (
        2.2 * math.pi**2 * ref.ISO10848_ABS_AREA
        / (ref.ISO10848_ABS_TS * ref.ISO10848_ABS_C0)
    )
    return Outcome(
        expected=f"aj = {expected:.4f} m",
        computed=f"aj = {computed:.4f} m",
        delta="exact",
        passed=abs(computed - expected) < 1e-9,
    )


@register(
    "Room & building acoustics",
    "ISO 10848-1:2006 Clause 7.3.1",
    "Flanking total loss factor η = 2,2/(f·Ts)",
)
def _chk_iso10848_loss_factor() -> Outcome:
    eta = ph.total_loss_factor([1000.0], [0.5])
    computed = float(eta[0])
    expected = 2.2 / (1000.0 * 0.5)
    return Outcome(
        expected=f"η = {expected:.4f}",
        computed=f"η = {computed:.4f}",
        delta="exact",
        passed=abs(computed - expected) < 1e-12,
    )


# --- Dynamic stiffness of resilient materials (EN 29052-1:1992) ---
@register(
    "Room & building acoustics",
    "EN 29052-1:1992 Formula 4",
    "Apparent dynamic stiffness s't = 4π²·m't·fr²  (m't=200 kg/m², fr=25 Hz)",
)
def _chk_en29052_apparent() -> Outcome:
    computed = float(ph.apparent_dynamic_stiffness(25.0, 200.0)) / 1e6
    expected = 4.0 * math.pi**2 * 200.0 * 25.0**2 / 1e6
    return numeric(expected, computed, 1e-6, unit="MN/m³", places=6)


@register(
    "Room & building acoustics",
    "EN 29052-1:1992 clause 8.2 NOTE",
    "Enclosed-gas stiffness s'a·d = 111 MN·mm/m³ (p₀=0,1 MPa, ε=0,9)",
)
def _chk_en29052_enclosed_gas() -> Outcome:
    # NOTE: s'a = 111/d MN/m3 for d in mm; the closed form gives 100/0,9 = 111.11.
    sa_mn = float(ph.enclosed_gas_stiffness(0.020, 0.9)) / 1e6   # d = 20 mm
    return numeric(111.111111 / 20.0, sa_mn, 1e-4, unit="MN/m³", places=5)


@register(
    "Room & building acoustics",
    "EN 29052-1:1992 Formula 2",
    "Floating-floor natural frequency f0 = (1/2π)√(s'/m')  (s'=10 MN/m³, m'=100 kg/m²)",
)
def _chk_en29052_resonance() -> Outcome:
    computed = float(ph.natural_frequency(10.0e6, 100.0))
    expected = math.sqrt(10.0e6 / 100.0) / (2.0 * math.pi)
    return numeric(expected, computed, 1e-6, unit="Hz", places=5)


# --- Mechanical mobility (ISO 7626-1:2011) ---
# SDOF resonator m=2 kg, k=8000 N/m, c=5 N.s/m; f0 = sqrt(k/m)/(2pi).
_MOB_M, _MOB_K, _MOB_C = 2.0, 8000.0, 5.0
_MOB_F0 = math.sqrt(_MOB_K / _MOB_M) / (2.0 * math.pi)


@register(
    "Room & building acoustics",
    "ISO 7626-1:2011 Annex A",
    "SDOF driving-point mobility peak |Y(f0)| = 1/c  (c=5 N·s/m)",
)
def _chk_iso7626_mobility_peak() -> Outcome:
    y0 = complex(ph.sdof_mobility(_MOB_F0, _MOB_M, _MOB_K, _MOB_C))
    return numeric(1.0 / _MOB_C, abs(y0), 1e-6, unit="m/(N·s)", places=6)


@register(
    "Room & building acoustics",
    "ISO 7626-1:2011 Annex A",
    "SDOF static receptance H(0) = 1/k  (k=8000 N/m)",
)
def _chk_iso7626_static_receptance() -> Outcome:
    h = complex(ph.sdof_receptance(1e-6, _MOB_M, _MOB_K, _MOB_C))
    return numeric(1.0 / _MOB_K, h.real, 1e-6, unit="m/N", rel=True, places=8)


@register(
    "Room & building acoustics",
    "ISO 7626-1:2011 Table 1",
    "FRF reciprocity: impedance × mobility = 1  (at 37 Hz)",
)
def _chk_iso7626_reciprocity() -> Outcome:
    y = complex(ph.sdof_mobility(37.0, _MOB_M, _MOB_K, _MOB_C))
    z = complex(ph.convert_frf(y, 37.0, "mobility", "impedance"))
    return numeric(1.0, abs(z * y), 1e-9, expected_label="1 (= Z·Y)")


# --- Dynamic transfer stiffness of resilient elements (ISO 10846) ---
@register(
    "Room & building acoustics",
    "ISO 10846-2:2008 3.17",
    "Transfer-stiffness level Lk = 20 lg(|k|/k0), k0 = 1 N/m  (|k| = 1 MN/m)",
)
def _chk_iso10846_level() -> Outcome:
    lk = float(ph.transfer_stiffness_level(1.0e6))
    return numeric(120.0, lk, 1e-6, unit="dB")


@register(
    "Room & building acoustics",
    "ISO 10846-3:2002 Formula (1)",
    "Indirect method k2,1 = -(2πf)²·m2·T  (f=500 Hz, m2=10 kg, T=0,01)",
)
def _chk_iso10846_indirect() -> Outcome:
    f, m2, t = 500.0, 10.0, 0.01
    expected = -((2.0 * math.pi * f) ** 2) * m2 * t
    computed = complex(ph.transfer_stiffness_indirect(f, t + 0j, m2)).real
    return numeric(expected, computed, 1e-3, rel=True, unit="N/m", places=1)


@register(
    "Room & building acoustics",
    "ISO 10846-1:2008 Table A.2",
    "FRF relation k = jω·Z at 250 Hz  (|k| recovered from impedance)",
)
def _chk_iso10846_stiffness_impedance() -> Outcome:
    f = 250.0
    w = 2.0 * math.pi * f
    k = 1.0e6 + 1j * 5.0e4
    z = complex(ph.convert_frf(k, f, "dynamic_stiffness", "impedance"))
    return numeric(abs(k), abs(1j * w * z), 1e-6, rel=True, unit="N/m", places=1)


# --- Sound power from surface vibration (ISO/TS 7849-1/-2) ---
@register(
    "Room & building acoustics",
    "ISO/TS 7849-1:2009 Formula (8)",
    "Calibration L_v from â = 9,81 m/s² at 100 Hz  (standard's EXAMPLE)",
)
def _chk_iso7849_calibration() -> Outcome:
    lv = float(ph.velocity_level_from_acceleration(9.81, 100.0))
    return numeric(106.9, lv, 0.05, unit="dB", places=1)


@register(
    "Room & building acoustics",
    "ISO/TS 7849-2:2009 Formula (15)",
    "L_W from L_v via measured radiation factor = 10 lg(P/P0)  (round-trip)",
)
def _chk_iso7849_power_round_trip() -> Outcome:
    p, s, v2 = 3.0e-4, 2.0, (1.0e-3) ** 2
    eps = float(ph.radiation_factor(p, s, v2))
    lv = float(ph.velocity_level(math.sqrt(v2)))
    lw = float(ph.radiated_sound_power_level(lv, s, radiation_factor=eps))
    return numeric(10.0 * math.log10(p / 1e-12), lw, 1e-6, unit="dB", places=3)


@register(
    "Room & building acoustics",
    "ISO/TS 7849-1:2009 Formula (12)",
    "Impedance term: L_W − L_v = 10 lg(411/400) at ε = 1, S = S0",
)
def _chk_iso7849_impedance_term() -> Outcome:
    lw = float(ph.radiated_sound_power_level(80.0, 1.0))
    return numeric(10.0 * math.log10(411.0 / 400.0), lw - 80.0, 1e-9, unit="dB")


# --- Structure-borne sound power of building equipment (EN 15657) ---
@register(
    "Room & building acoustics",
    "EN 15657:2018 Formula (14)",
    "Reception-plate L_Ws = resonant-plate power P = ωη(mS)⟨v²⟩  (round-trip)",
)
def _chk_en15657_power_balance() -> Outcome:
    lv, f, m, s, eta = 82.0, 800.0, 15.0, 1.5, 0.02
    lw = float(ph.structure_borne_power_level(lv, f, m, s, eta))
    v2 = (1e-9) ** 2 * 10.0 ** (0.1 * lv)
    p = 2.0 * math.pi * f * eta * (m * s) * v2
    return numeric(10.0 * math.log10(p / 1e-12), lw, 1e-6, unit="dB", places=3)


@register(
    "Room & building acoustics",
    "EN 15657:2018 Formula (13)",
    "Plate loss factor η = 2,2/(f·Ts) at 1 kHz, Ts = 0,3 s",
)
def _chk_en15657_loss_factor() -> Outcome:
    eta = float(ph.plate_loss_factor([1000.0], 0.3)[0])
    return numeric(2.2 / (1000.0 * 0.3), eta, 1e-9)


# --- Installed structure-borne sound from equipment (EN 12354-5) ---
@register(
    "Room & building acoustics",
    "EN 12354-5:2009 Formula (19b/19c)",
    "Coupling term → force-source limit 10 lg(|Ys|/Re{Yi}) as |Ys|≫|Yi|",
)
def _chk_en12354_5_coupling_limit() -> Outcome:
    ys, yi = 1e-3 + 0j, 1e-7 + 0j
    dc = float(ph.coupling_term(ys, yi))
    limit = float(ph.coupling_term_force_source(ys, yi))
    return numeric(limit, dc, 1e-2, unit="dB", places=3)


@register(
    "Room & building acoustics",
    "EN 12354-5:2009 Formula (18b)",
    "Installed power L_Ws,inst = L_Ws,c − D_C  (80 − 10,828 dB)",
)
def _chk_en12354_5_installed_power() -> Outcome:
    lw = float(ph.installed_structure_borne_power_level(80.0, 10.828))
    return numeric(69.172, lw, 1e-6, unit="dB", places=3)


@register(
    "Room & building acoustics",
    "EN 12354-5:2009 Formula (18a)",
    "Path SPL area/absorption terms −10 lg(S/S0) − 10 lg(A0/4), S0=A0=10 m²",
)
def _chk_en12354_5_path_terms() -> Outcome:
    # With S = S0 the area term is 0, leaving −10 lg(10/4) = −3,979 dB.
    lp = float(ph.structure_borne_pressure_level_path(0.0, 0.0, 0.0, 10.0))
    return numeric(-10.0 * math.log10(10.0 / 4.0), lp, 1e-9, unit="dB", places=3)


# ===========================================================================
# Domain 7 - Building prediction & uncertainty
# ===========================================================================
def _annex_h3_paths() -> list[ph.FlankingPath]:
    """The EN 12354-1 Annex H.3 flanking paths from the shared input table."""
    ss = ref.EN12354_1_ANNEX_H3_SEPARATING_AREA
    paths: list[ph.FlankingPath] = []
    for label, rw, kff, kfd, lf in ref.EN12354_1_ANNEX_H3_ELEMENTS:
        ff, df, fd = ph.flanking_element(
            label=label, r_flanking=rw, r_separating=ref.EN12354_1_ANNEX_H3_R_DIRECT,
            k_ff=kff, k_fd=kfd, k_df=kfd, separating_area=ss, coupling_length=lf,
        )
        paths += [ff, df, fd]
    return paths


@register(
    "Building prediction & uncertainty",
    "EN 12354-1:2000 Annex H.3",
    "Airborne prediction R'w (direct + 12 flanking paths)",
)
def _chk_en12354_1_airborne() -> Outcome:
    res = ph.predicted_airborne_insulation(
        r_direct=ref.EN12354_1_ANNEX_H3_R_DIRECT, flanking_paths=_annex_h3_paths()
    )
    expected = ref.EN12354_1_ANNEX_H3_RPRIME_W
    computed = float(res.r_prime_w)
    paths_ok = len(res.paths) == ref.EN12354_1_ANNEX_H3_NUM_PATHS
    return Outcome(
        expected=f"R'w {expected} dB ({ref.EN12354_1_ANNEX_H3_NUM_PATHS} paths)",
        computed=f"R'w {round(computed)} dB ({len(res.paths)} paths, {computed:.2f})",
        delta=f"{computed - expected:+.2f} dB",
        passed=paths_ok and round(computed) == expected,
    )


@register(
    "Building prediction & uncertainty",
    "EN 12354-2:2000 Annex E.3",
    "Impact prediction L'n,w = Ln,w,eq - dLw + K",
)
def _chk_en12354_2_impact() -> Outcome:
    ln_eq = ph.equivalent_impact_level(ref.EN12354_2_ANNEX_E3_MASS)
    k = ph.impact_flanking_correction(
        ref.EN12354_2_ANNEX_E3_MASS, ref.EN12354_2_ANNEX_E3_FLANKING_MEAN_MASS
    )
    res = ph.predicted_impact_insulation(
        ln_w_eq=round(ln_eq), delta_l_w=ref.EN12354_2_ANNEX_E3_DELTA_LW,
        k_correction=k,
    )
    k_ok = int(k) == ref.EN12354_2_ANNEX_E3_K
    computed = float(res.l_prime_n_w)
    out = numeric(
        ref.EN12354_2_ANNEX_E3_LPRIME_N_W, computed, 1e-9, unit="dB", places=6
    )
    return Outcome(out.expected, out.computed, out.delta, out.passed and k_ok)


def _en12354_3_annex_f() -> "ph.FacadePredictionResult":
    """The EN 12354-3 Annex F facade prediction from the shared input table."""
    elements = [
        ph.FacadeElement(name=name, area=area, r=r)
        for name, area, r in ref.EN12354_3_ANNEX_F_ELEMENTS
    ]
    elements.append(ph.FacadeElement(name="inlet", dn_e=ref.EN12354_3_ANNEX_F_INLET_DNE))
    return ph.facade_sound_reduction(
        elements,
        area=ref.EN12354_3_ANNEX_F_AREA,
        volume=ref.EN12354_3_ANNEX_F_VOLUME,
        frequencies=ref.EN12354_3_ANNEX_F_BANDS,
        bands="octave",
    )


@register(
    "Building prediction & uncertainty",
    "EN 12354-3:2000 Annex F",
    "Facade airborne prediction (R'tr,s,w / D2m,nT,w single numbers)",
)
def _chk_en12354_3_facade() -> Outcome:
    res = _en12354_3_annex_f()
    # Anchor on the digit-exact low bands and the single-number ratings.
    low_ok = np.allclose(
        np.asarray(res.r_prime)[:3], ref.EN12354_3_ANNEX_F_RPRIME_LOW, atol=0.05
    )
    nums_ok = (
        res.r_tr_s_w == ref.EN12354_3_ANNEX_F_RTRS_W
        and res.c_tr == ref.EN12354_3_ANNEX_F_CTR
        and res.d_2m_nt_w == ref.EN12354_3_ANNEX_F_D2MNT_W
    )
    return Outcome(
        expected=(
            f"R'tr,s,w {ref.EN12354_3_ANNEX_F_RTRS_W} "
            f"(Ctr {ref.EN12354_3_ANNEX_F_CTR}); D2m,nT,w {ref.EN12354_3_ANNEX_F_D2MNT_W} dB"
        ),
        computed=f"R'tr,s,w {res.r_tr_s_w} (Ctr {res.c_tr}); D2m,nT,w {res.d_2m_nt_w} dB",
        delta="0",
        passed=bool(low_ok and nums_ok),
    )


@register(
    "Building prediction & uncertainty",
    "EN 12354-4:2000 Annex G / Formula (2)",
    "Radiated LW of a wall+door segment (side 1, low bands)",
)
def _chk_en12354_4_radiated() -> Outcome:
    res = ph.radiated_sound_power(
        [
            ph.FacadeElement(
                name="wall",
                area=ref.EN12354_4_ANNEX_G_SEGMENT_AREA - ref.EN12354_4_ANNEX_G_DOOR_AREA,
                r=ref.EN12354_4_ANNEX_G_CONCRETE_R,
            ),
            ph.FacadeElement(
                name="door", area=ref.EN12354_4_ANNEX_G_DOOR_AREA,
                r=ref.EN12354_4_ANNEX_G_DOOR_R,
            ),
        ],
        lp_in=ref.EN12354_4_ANNEX_G_LP_IN,
        area=ref.EN12354_4_ANNEX_G_SEGMENT_AREA,
        c_d=ref.EN12354_4_ANNEX_G_CD,
        r_prime_cap=ref.EN12354_4_ANNEX_G_RPRIME_CAP,
        octave_bands=[int(f) for f in ref.EN12354_4_ANNEX_G_BANDS],
    )
    rp_ok = np.allclose(
        np.asarray(res.r_prime)[:3], ref.EN12354_4_ANNEX_G_SIDE1_RPRIME_LOW, atol=0.05
    )
    lw = np.asarray(res.l_w)[:2]
    exp = np.asarray(ref.EN12354_4_ANNEX_G_SIDE1_LW_LOW)
    out = numeric(0.0, float(np.max(np.abs(lw - exp))), 0.1, unit="dB", places=3)
    return Outcome(
        expected=f"LW 63/125 Hz {ref.EN12354_4_ANNEX_G_SIDE1_LW_LOW} dB (+/-0.1)",
        computed=f"LW {np.round(lw, 1).tolist()} dB",
        delta=out.delta,
        passed=bool(rp_ok and out.passed),
    )


@register(
    "Building prediction & uncertainty",
    "EN 12354-4:2000 Annex E / Table G.9",
    "Exterior level from a finite radiating side (side 1, d = 5 m)",
)
def _chk_en12354_4_propagation() -> Outcome:
    w, h, d, a_tot = ref.EN12354_4_ANNEX_G_ATTENUATION[0]
    att = ph.outdoor_attenuation(w, h, d)
    lp = ph.outdoor_level(ref.EN12354_4_ANNEX_G_SIDE1_LWA, att)
    att_ok = abs(att - a_tot) <= 0.05
    return numeric(
        ref.EN12354_4_ANNEX_G_LP_SIDE1_D5, lp, 0.05, unit="dB", places=3
    ) if att_ok else Outcome(
        expected=f"A'tot {a_tot} dB", computed=f"A'tot {att:.2f} dB",
        delta=f"{att - a_tot:+.2f} dB", passed=False,
    )


@register(
    "Building prediction & uncertainty",
    "ISO 12999-1:2020 Table 2",
    "Airborne band uncertainty, situation A @ 1 kHz",
)
def _chk_iso12999_table2_band() -> Outcome:
    res = ph.band_uncertainty("airborne", "A")
    idx = list(res.frequencies).index(1000)
    computed = float(res.uncertainties[idx])
    return numeric(
        ref.ISO12999_1_TABLE2_AIRBORNE_A_1000HZ, computed, 1e-9, unit="dB", places=3
    )


@register(
    "Building prediction & uncertainty",
    "ISO 12999-1:2020 Clause 8 / Table 8",
    "Expanded uncertainty U = 1.96 u (95 % two-sided, Rw sit. A)",
)
def _chk_iso12999_expanded() -> Outcome:
    u = ref.ISO12999_1_RW_A_STANDARD_UNCERTAINTY
    expected = ref.ISO12999_1_COVERAGE_K_95 * u
    computed = float(ph.insulation_expanded_uncertainty(u, coverage=0.95))
    return numeric(expected, computed, 1e-9, unit="dB", places=6)


@register(
    "Building prediction & uncertainty",
    "ISO 12999-2:2020 Table 4 / Formula (1)",
    "Absorption coefficient +/-U (k=2), reproducibility, 20 x 1/3-oct bands",
)
def _chk_iso12999_2_table4() -> Outcome:
    res = ph.sound_absorption_coefficient_uncertainty(
        ref.ISO12999_2_TABLE4_ALPHA_S, ref.ISO12999_2_TABLE4_FREQ, confidence=0.95
    )
    got = res.reported_expanded_uncertainty
    expected = np.asarray(ref.ISO12999_2_TABLE4_U_K2, dtype=float)
    ok = bool(np.array_equal(got, expected))
    return Outcome(
        expected=f"U(k=2) = {expected.tolist()}",
        computed=f"U(k=2) = {got.tolist()}",
        delta="exact",
        passed=ok,
    )


@register(
    "Building prediction & uncertainty",
    "ISO 12999-2:2020 Table 5 / Formula (4)",
    "Practical coefficient +/-U (k=2), reproducibility, 5 octave bands",
)
def _chk_iso12999_2_table5() -> Outcome:
    res = ph.practical_coefficient_uncertainty(
        ref.ISO12999_2_TABLE5_ALPHA_P, ref.ISO12999_2_TABLE5_FREQ
    )
    got = res.reported_expanded_uncertainty
    expected = np.asarray(ref.ISO12999_2_TABLE5_U_K2, dtype=float)
    ok = bool(np.array_equal(got, expected))
    return Outcome(
        expected=f"U(k=2) = {expected.tolist()}",
        computed=f"U(k=2) = {got.tolist()}",
        delta="exact",
        passed=ok,
    )


@register(
    "Building prediction & uncertainty",
    "ISO 12999-2:2020 Clause 7, Examples 1/2",
    "Single-number U (k=2): alpha_w and DLalpha,NRD",
)
def _chk_iso12999_2_single_numbers() -> Outcome:
    u_aw = float(
        ph.weighted_coefficient_uncertainty(
            ref.ISO12999_2_ALPHA_W_EXAMPLE
        ).reported_expanded_uncertainty[0]
    )
    u_dl = float(
        ph.single_number_rating_uncertainty(
            ref.ISO12999_2_DLALPHA_EXAMPLE
        ).reported_expanded_uncertainty[0]
    )
    ok = (
        u_aw == ref.ISO12999_2_ALPHA_W_U_K2 and u_dl == ref.ISO12999_2_DLALPHA_U_K2
    )
    return Outcome(
        expected=f"alpha_w +/-{ref.ISO12999_2_ALPHA_W_U_K2}, "
        f"DLalpha +/-{ref.ISO12999_2_DLALPHA_U_K2} dB",
        computed=f"alpha_w +/-{u_aw}, DLalpha +/-{u_dl} dB",
        delta="exact",
        passed=ok,
    )


# ===========================================================================
# Domain 8 - Outdoor propagation & occupational exposure
# ===========================================================================
def _iso9613_table1(point: tuple[float, float, float, float]) -> Outcome:
    """Compare air_attenuation against an ISO 9613-1 Table 1 grid point (dB/km)."""
    temp, rh, freq, alpha_km = point
    computed = float(
        ph.air_attenuation(freq, temp, rh, exact_midband=True)[()]
    ) * 1000.0  # dB/m -> dB/km
    # Tolerance = 1 in the last printed (3-significant-figure) digit.
    tol = 10.0 ** (math.floor(math.log10(alpha_km)) - 2)
    return numeric(alpha_km, computed, tol, unit="dB/km", places=3)


@register(
    "Outdoor propagation & occupational exposure",
    "ISO 9613-1:1993 Table 1",
    "Air attenuation @ 10 degC, 70 %, 1 kHz",
)
def _chk_iso9613_table1_mid() -> Outcome:
    return _iso9613_table1(ref.ISO9613_1_TABLE1_MID)


@register(
    "Outdoor propagation & occupational exposure",
    "ISO 9613-1:1993 Table 1",
    "Air attenuation @ 0 degC, 20 %, 2 kHz",
)
def _chk_iso9613_table1_corner() -> Outcome:
    return _iso9613_table1(ref.ISO9613_1_TABLE1_CORNER)



@register(
    "Outdoor propagation & occupational exposure",
    "ISO 9613-2:1996 Eq. (7)",
    "Geometrical divergence Adiv = 20 lg(d/d0) + 11 at 100 m",
)
def _chk_iso9613_2_adiv() -> Outcome:
    computed = ph.geometric_divergence(100.0)
    return numeric(ref.ISO9613_2_ADIV_100M, computed, 1e-9, unit="dB", places=6)


@register(
    "Outdoor propagation & occupational exposure",
    "ISO 9613-2:1996 Table 3",
    "Ground b'(0) porous limit -> Agr(250 Hz) = 2(-1.5 + 10.1)",
)
def _chk_iso9613_2_ground_limit() -> Outcome:
    # Porous ground both sides (Gs = Gr = 1), source and receiver on the ground
    # (hs = hr = 0), fully-developed path (dp -> inf): the 250 Hz band isolates
    # the Table 3 limit b'(0) = 1,5 + 8,6 = 10,1, so Agr = 2(-1,5 + 10,1) = 17,2.
    big = 1.0e7
    agr = ph.ground_attenuation(big, 0.0, 0.0, [250.0], 1.0, 1.0, 1.0,
                                projected_distance=big)
    return numeric(
        ref.ISO9613_2_GROUND_AGR_250_POROUS, float(agr[0]), 1e-6, unit="dB",
        places=4,
    )


@register(
    "Outdoor propagation & occupational exposure",
    "ISO 9613-2:1996 clause 7.4",
    "Single-edge diffraction saturates at the 20 dB cap",
)
def _chk_iso9613_2_barrier_single_cap() -> Outcome:
    b = ph.Barrier(source_to_edge=50.0, edge_to_receiver=50.0)
    dz = ph.barrier_attenuation(b, 60.0, ph.DEFAULT_FREQUENCIES)
    return numeric(
        ref.ISO9613_2_BARRIER_CAP_SINGLE, float(np.max(dz)), 1e-9, unit="dB",
        places=6,
    )


@register(
    "Outdoor propagation & occupational exposure",
    "ISO 9613-2:1996 clause 7.4",
    "Double-edge diffraction saturates at the 25 dB cap",
)
def _chk_iso9613_2_barrier_double_cap() -> Outcome:
    b = ph.Barrier(source_to_edge=50.0, edge_to_receiver=50.0, edge_separation=5.0)
    dz = ph.barrier_attenuation(b, 60.0, ph.DEFAULT_FREQUENCIES)
    return numeric(
        ref.ISO9613_2_BARRIER_CAP_DOUBLE, float(np.max(dz)), 1e-9, unit="dB",
        places=6,
    )


def _iso9612_annex_d_tasks() -> list[ph.Task]:
    """Rebuild the ISO 9612 Annex D Task objects from the shared input table."""
    from phonometry.hearing.occupational_exposure import Task

    tasks = []
    for samples, duration, drange in ref.ISO9612_ANNEX_D_TASKS:
        tasks.append(Task(samples=samples, duration_hours=duration,
                          duration_range=drange))
    return tasks


def _lex_and_u(lex: float, u: float, exp_lex: float, exp_u: float,
               tol_lex: float, tol_u: float) -> Outcome:
    """Combined LEX,8h + expanded-uncertainty outcome for one ISO 9612 example."""
    ok = abs(lex - exp_lex) <= tol_lex and abs(u - exp_u) <= tol_u
    return Outcome(
        expected=f"LEX,8h {exp_lex:.1f}; U {exp_u:.1f} dB",
        computed=f"LEX,8h {lex:.1f}; U {u:.1f} dB",
        delta=f"{lex - exp_lex:+.2f}; {u - exp_u:+.2f} dB",
        passed=ok,
    )


@register(
    "Outdoor propagation & occupational exposure",
    "ISO 9612:2009 Annex D",
    "Task-based LEX,8h + U (welder day, case a)",
)
def _chk_iso9612_annex_d() -> Outcome:
    res = ph.task_based_exposure(
        _iso9612_annex_d_tasks(), include_duration_uncertainty=False, warn=False
    )
    return _lex_and_u(
        res.lex_8h, res.expanded_uncertainty,
        ref.ISO9612_ANNEX_D_LEX_8H, ref.ISO9612_ANNEX_D_U, 0.05, 0.1,
    )


@register(
    "Outdoor propagation & occupational exposure",
    "ISO 9612:2009 Annex E",
    "Job-based LEX,8h + U (production line, 18 workers)",
)
def _chk_iso9612_annex_e() -> Outcome:
    res = ph.job_based_exposure(
        list(ref.ISO9612_ANNEX_E_SAMPLES), ref.ISO9612_ANNEX_E_TE_HOURS
    )
    return _lex_and_u(
        res.lex_8h, res.expanded_uncertainty,
        ref.ISO9612_ANNEX_E_LEX_8H, ref.ISO9612_ANNEX_E_U, 0.1, 0.05,
    )


@register(
    "Outdoor propagation & occupational exposure",
    "ISO 9612:2009 Annex F",
    "Full-day LEX,8h + U (forklift drivers)",
)
def _chk_iso9612_annex_f() -> Outcome:
    res = ph.full_day_exposure(
        list(ref.ISO9612_ANNEX_F_SAMPLES), ref.ISO9612_ANNEX_F_TE_HOURS
    )
    return _lex_and_u(
        res.lex_8h, res.expanded_uncertainty,
        ref.ISO9612_ANNEX_F_LEX_8H, ref.ISO9612_ANNEX_F_U, 0.05, 0.05,
    )


# ---------------------------------------------------------------------------
# Materials: absorption rating, airflow resistance & impedance tube
# ---------------------------------------------------------------------------
_MATERIALS = "Materials: absorption, airflow & impedance"


@register(_MATERIALS, "ISO 11654:1997 Annex A.1", "Weighted absorption alpha_w (no indicator)")
def _chk_iso11654_a1() -> Outcome:
    res = ph.weighted_absorption(list(ref.ISO11654_ANNEX_A1_ALPHA_P))
    out = numeric(ref.ISO11654_ANNEX_A1_ALPHA_W, res.alpha_w, 5e-4, places=2)
    # alpha_w matches AND no shape indicator applies AND class is C.
    ok = (
        out.passed
        and res.shape_indicator == ref.ISO11654_ANNEX_A1_INDICATOR
        and res.absorption_class == ref.ISO11654_ANNEX_A1_CLASS
    )
    return Outcome(
        expected=f"{ref.ISO11654_ANNEX_A1_ALPHA_W:.2f} (class C, no indic.)",
        computed=f"{res.alpha_w:.2f} (class {res.absorption_class}, '{res.shape_indicator}')",
        delta=out.delta,
        passed=ok,
    )


@register(_MATERIALS, "ISO 11654:1997 Annex A.2", "Weighted absorption alpha_w with M indicator")
def _chk_iso11654_a2() -> Outcome:
    res = ph.weighted_absorption(list(ref.ISO11654_ANNEX_A2_ALPHA_P))
    out = numeric(ref.ISO11654_ANNEX_A2_ALPHA_W, res.alpha_w, 5e-4, places=2)
    ok = out.passed and res.shape_indicator == ref.ISO11654_ANNEX_A2_INDICATOR
    return Outcome(
        expected=f"{ref.ISO11654_ANNEX_A2_ALPHA_W:.2f}(M)",
        computed=res.rating_label,
        delta=out.delta,
        passed=ok,
    )


@register(_MATERIALS, "ISO 9053-2:2020 Annex A.3", "Thermal boundary-layer thickness b")
def _chk_iso9053_2_boundary() -> Outcome:
    b = ph.thermal_boundary_layer_thickness(frequency=ref.ISO9053_2_ANNEX_A_FREQUENCY)
    return numeric(
        ref.ISO9053_2_ANNEX_A_BOUNDARY_LAYER, b, 5e-6, unit="m", places=5,
    )


@register(_MATERIALS, "ISO 9053-2:2020 Annex A.3", "Effective ratio of specific heats kappa'")
def _chk_iso9053_2_kappa() -> Outcome:
    kp = ph.effective_kappa(
        cavity_surface=ref.ISO9053_2_ANNEX_A_SURFACE,
        cavity_volume=ref.ISO9053_2_ANNEX_A_VOLUME,
        frequency=ref.ISO9053_2_ANNEX_A_FREQUENCY,
    )
    return numeric(ref.ISO9053_2_ANNEX_A_KAPPA_PRIME, kp, 5e-4, places=3)


@register(_MATERIALS, "ISO 10534-1:1996 Eqs (9)/(13)/(14)", "Absorption from standing-wave ratio s=3")
def _chk_iso10534_1_swr() -> Outcome:
    alpha = float(ph.standing_wave_absorption(ref.ISO10534_1_SWR))
    # The intermediate |r| = (s-1)/(s+1) (Eq. (13)) must match its shared
    # oracle too, so both steps of the chain are pinned.
    from phonometry.materials.impedance_tube import standing_wave_reflection_magnitude

    r_mag = float(standing_wave_reflection_magnitude(ref.ISO10534_1_SWR))
    out = numeric(ref.ISO10534_1_ABSORPTION, alpha, 1e-9, places=4)
    r_ok = abs(r_mag - ref.ISO10534_1_REFLECTION_MAGNITUDE) <= 1e-9
    # Show both chained values so a |r| failure is visible in the report.
    expected = (
        f"alpha {out.expected}, \\|r\\| {ref.ISO10534_1_REFLECTION_MAGNITUDE:g}"
    )
    computed = f"alpha {out.computed}, \\|r\\| {r_mag:.4f}"
    return Outcome(expected, computed, out.delta, out.passed and r_ok)


@register(
    _MATERIALS,
    "ISO 10534-2 Eq. (17) / Annex D",
    "Two-microphone round trip recovers a known reflection factor",
)
def _chk_iso10534_2_roundtrip() -> Outcome:
    # Synthesise the transfer function H12 of a known complex r via the
    # Annex D field equations (Eq. (D.7)), then recover r with the library's
    # Eq. (17) reduction. Synthesis and reduction share only the plane-wave
    # field model, so this is an algebraic identity: the only residual is
    # float rounding, hence the 1e-9 tolerance.
    from phonometry.materials.impedance_tube import reflection_factor, tube_wavenumber

    f = np.array([500.0, 1000.0, 1800.0])
    x1, spacing, c0 = 0.12, 0.03, 343.2
    r_true = 0.3 - 0.4j
    k0 = np.asarray(tube_wavenumber(f, c0))
    x2 = x1 - spacing
    h12 = (
        (np.exp(1j * k0 * x2) + r_true * np.exp(-1j * k0 * x2))
        / (np.exp(1j * k0 * x1) + r_true * np.exp(-1j * k0 * x1))
    )
    r = reflection_factor(h12, spacing=spacing, x1=x1, wavenumber=k0)
    err = float(np.max(np.abs(np.asarray(r) - r_true)))
    # NOTE: no pipe characters in the label (it lands in a Markdown table cell).
    return numeric(0.0, err, 1e-9, places=9,
                   expected_label="abs(r - (0.3-0.4j)) = 0 (identity, +/-1e-9)")


# ---------------------------------------------------------------------------
# Scattering & diffusion (ISO 17497-1/-2)
# ---------------------------------------------------------------------------
_SCATTERING = "Scattering & diffusion (ISO 17497)"


@register(_SCATTERING, "ISO 17497-1:2004 Eq (2)", "Reference speed of sound at 20 C")
def _chk_iso17497_1_speed() -> Outcome:
    c = float(ph.speed_of_sound(20.0))
    return numeric(ref.ISO17497_1_SPEED_OF_SOUND_20C, c, 1e-6, unit="m/s", places=4)


@register(_SCATTERING, "ISO 17497-1:2004 Eqs (1)/(4)/(5)", "Scattering coefficient (synthetic chain)")
def _chk_iso17497_1_scattering() -> Outcome:
    t1, t2, t3, t4 = ref.ISO17497_1_CHAIN_T
    c = ref.ISO17497_1_CHAIN_C
    alpha_s = ph.random_incidence_absorption(
        ref.ISO17497_1_CHAIN_V, ref.ISO17497_1_CHAIN_S, c1=c, T1=t1, c2=c, T2=t2
    )
    alpha_spec = ph.specular_absorption_coefficient(
        ref.ISO17497_1_CHAIN_V, ref.ISO17497_1_CHAIN_S, c3=c, T3=t3, c4=c, T4=t4
    )
    s = float(ph.scattering_coefficient(alpha_spec, alpha_s))
    return numeric(ref.ISO17497_1_CHAIN_SCATTERING, s, 1e-9, places=4)


@register(_SCATTERING, "ISO 17497-1:2004 Annex A.5", "Expanded uncertainty of scattering coefficient")
def _chk_iso17497_1_uncertainty() -> Outcome:
    u = float(ph.scattering_coefficient_uncertainty(
        ref.ISO17497_1_A5_ALPHA_SPEC,
        ref.ISO17497_1_A5_ALPHA_S,
        ref.ISO17497_1_A5_U_ALPHA_SPEC,
        ref.ISO17497_1_A5_U_ALPHA_S,
    ).u_scattering)
    return numeric(ref.ISO17497_1_A5_U_SCATTERING, u, 1e-6, places=5)


@register(_SCATTERING, "ISO 17497-2:2012 Formula (5)", "Diffusion coefficient (autocorrelation)")
def _chk_iso17497_2_diffusion() -> Outcome:
    d = float(ph.directional_diffusion_coefficient(list(ref.ISO17497_2_DIFFUSION_LEVELS)))
    return numeric(ref.ISO17497_2_DIFFUSION_COEFF, d, 1e-9, places=4)


@register(_SCATTERING, "ISO 17497-2:2012 Formula (8)", "Zenith area factor (radians convention)")
def _chk_iso17497_2_area_factor() -> Outcome:
    n = ph.area_factors([0.0, 30.0, 60.0, 90.0], delta_theta=5.0)
    return numeric(ref.ISO17497_2_AREA_FACTOR_ZENITH, float(n[0]), 1e-6, places=5)


# ---------------------------------------------------------------------------
# In-situ road-surface absorption (ISO 13472-1/-2)
# ---------------------------------------------------------------------------
_ROAD = "In-situ road absorption (ISO 13472)"


@register(_ROAD, "ISO 13472-1:2002 Clause 4.2", "Geometrical-spreading factor Kr")
def _chk_iso13472_1_kr() -> Outcome:
    kr = ph.geometric_spreading_factor()
    return numeric(ref.ISO13472_1_KR, kr, 1e-12, places=4)


@register(_ROAD, "ISO 13472-1:2002 Annex A", "Maximum-sampled-area radius")
def _chk_iso13472_1_msa() -> Outcome:
    r = ph.max_sampled_area_radius(ref.ISO13472_1_MSA_WINDOW)
    return numeric(ref.ISO13472_1_MSA_RADIUS, r, 1e-6, unit="m", places=4)


@register(_ROAD, "ISO 13472-2:2010 Clause 5.4.1", "Spot-tube upper usable frequency f_u")
def _chk_iso13472_2_fu() -> Outcome:
    fu = ph.spot_tube_upper_frequency(
        ref.ISO13472_2_SPOT_DIAMETER, ref.ISO13472_2_SPOT_SPEED
    )
    return numeric(ref.ISO13472_2_SPOT_FU, fu, 0.1, unit="Hz", places=1)


# ---------------------------------------------------------------------------
# Precision sound power (ISO 3745 / ISO 9614-3)
# ---------------------------------------------------------------------------
_PRECISION_POWER = "Precision sound power (ISO 3745 / 9614-3)"


@register(_PRECISION_POWER, "ISO 3745:2012 Clause 10.5 EXAMPLE", "Expanded uncertainty U (k=2)")
def _chk_iso3745_uncertainty() -> Outcome:
    u = float(ph.precision_uncertainty(
        ref.ISO3745_U_SIGMA_R0, ref.ISO3745_U_SIGMA_OMC, ref.ISO3745_U_COVERAGE
    ))
    return numeric(ref.ISO3745_U_EXPANDED, u, 1e-3, unit="dB", places=3)


@register(_PRECISION_POWER, "ISO 3745:2012 Eq (11)", "K1 background floor (6 dB edge band)")
def _chk_iso3745_k1_floor() -> Outcome:
    k1 = ph.precision_background_correction(
        np.array([[ref.ISO3745_K1_EDGE_LEVEL]]),
        np.array([[ref.ISO3745_K1_EDGE_BACKGROUND]]),
        np.array([ref.ISO3745_K1_EDGE_FREQUENCY]),
    )
    return numeric(ref.ISO3745_K1_EDGE_FLOOR, float(k1[0, 0]), 1e-4, unit="dB", places=4)


@register(_PRECISION_POWER, "ISO 3745:2012 Eq (16)", "Meteorological C1 at 23 C reference")
def _chk_iso3745_c1() -> Outcome:
    c1 = ph.meteorological_corrections(23.0, 101.325).c1
    return numeric(ref.ISO3745_C1_REFERENCE, c1, 1e-4, unit="dB", places=4)


@register(_PRECISION_POWER, "ISO 9614-3:2002 Eqs (5)/(8)/(9)", "Uniform-intensity LW recovery")
def _chk_iso9614_3_uniform() -> Outcome:
    areas = np.array(ref.ISO9614_3_UNIFORM_AREAS, dtype=float)
    i_n = np.full(areas.shape, ref.ISO9614_3_UNIFORM_POWER / float(areas.sum()))
    res = ph.sound_power_intensity_precision(i_n, areas)
    return numeric(ref.ISO9614_3_UNIFORM_LW, float(res.sound_power_level[0]), 1e-9, unit="dB", places=4)


# ===========================================================================
# Human vibration (ISO 8041-1 / ISO 2631 / ISO 5349 / Directive 2002/44/EC)
# ===========================================================================
_HUMAN_VIB = "Human vibration (ISO 8041 / 2631 / 5349)"


def _true_centre(n: int) -> float:
    """True IEC 61260 one-third-octave centre ``10^(n/10)`` Hz."""
    return float(10.0 ** (n / 10.0))


@register(_HUMAN_VIB, "ISO 8041-1:2017 Table B.8", "Wk design-goal factor at 6,31 Hz")
def _chk_iso8041_wk_annex_b() -> Outcome:
    factor = float(ph.weighting_factors("Wk", _true_centre(8))[0])
    return numeric(ref.ISO8041_1_WK_FACTOR_6P31HZ, factor, 1e-3, rel=True, places=4)


@register(_HUMAN_VIB, "ISO 8041-1:2017 Table B.9", "Wm design-goal factor at 1,585 Hz")
def _chk_iso8041_wm_annex_b() -> Outcome:
    factor = float(ph.weighting_factors("Wm", _true_centre(2))[0])
    return numeric(ref.ISO8041_1_WM_FACTOR_1P585HZ, factor, 1e-3, rel=True, places=4)


@register(_HUMAN_VIB, "ISO 8041-1:2017 Table 1", "Wh factor at the 500 rad/s reference")
def _chk_iso8041_wh_reference() -> Outcome:
    factor = float(ph.weighting_factors("Wh", ref.ISO8041_1_WH_REF_FREQ_HZ)[0])
    return numeric(ref.ISO8041_1_WH_REF_FACTOR, factor, 1.5e-3, rel=True, places=4)


@register(_HUMAN_VIB, "ISO 5349-2:2001 Example E.2.1", "Single-tool daily exposure A(8)")
def _chk_iso5349_e21() -> Outcome:
    a8 = ph.daily_exposure(7.4, 2.5 * 3600.0)
    return numeric(ref.ISO5349_2_E21_A8, a8, 0.05, unit="m/s^2", places=2)


@register(_HUMAN_VIB, "ISO 5349-2:2001 Example E.3", "Forestry three-task A(8)")
def _chk_iso5349_e3() -> Outcome:
    a8 = ph.hav_daily_exposure(
        [4.6, 6.0, 3.6], [2 * 3600.0, 1 * 3600.0, 2 * 3600.0]
    )
    return numeric(ref.ISO5349_2_E3_A8, a8, 0.05, unit="m/s^2", places=2)


@register(_HUMAN_VIB, "ISO 5349-1:2001 Eq. (C.1)", "VWF 10 % lifetime Dy at A(8)=7")
def _chk_iso5349_vwf() -> Outcome:
    dy = ph.hav_vwf_lifetime_years(ref.ISO5349_1_VWF_A8)
    return numeric(ref.ISO5349_1_VWF_DY_YEARS, dy, 0.1, unit="yr", places=2)


@register(_HUMAN_VIB, "Directive 2002/44/EC Art. 3", "HAV/WBV action & limit values")
def _chk_directive_2002_44() -> Outcome:
    hav = ph.exposure_assessment(1.0, kind="hav")
    wbv = ph.exposure_assessment(0.1, kind="wbv")
    ok = (
        hav.action_value == ref.DIRECTIVE_2002_44_HAV_EAV
        and hav.limit_value == ref.DIRECTIVE_2002_44_HAV_ELV
        and wbv.action_value == ref.DIRECTIVE_2002_44_WBV_EAV
        and wbv.limit_value == ref.DIRECTIVE_2002_44_WBV_ELV
    )
    exp = (
        f"HAV {ref.DIRECTIVE_2002_44_HAV_EAV}/{ref.DIRECTIVE_2002_44_HAV_ELV}, "
        f"WBV {ref.DIRECTIVE_2002_44_WBV_EAV}/{ref.DIRECTIVE_2002_44_WBV_ELV} m/s^2"
    )
    got = (
        f"HAV {hav.action_value}/{hav.limit_value}, "
        f"WBV {wbv.action_value}/{wbv.limit_value} m/s^2"
    )
    return Outcome(expected=exp, computed=got, delta="0", passed=ok)


# ---------------------------------------------------------------------------
# Speech Intelligibility Index (ANSI S3.5-1997)
# ---------------------------------------------------------------------------
_SII = "Speech intelligibility (ANSI S3.5-1997)"


@register(_SII, "ANSI S3.5-1997 Table 3", "Band-importance function normalisation")
def _chk_sii_band_importance_sum() -> Outcome:
    total = float(ph.sii.BAND_IMPORTANCE.sum())
    return numeric(ref.ANSIS3_5_BAND_IMPORTANCE_SUM, total, 1e-9, places=6)


@register(_SII, "ANSI S3.5-1997 clause 5.4", "Equivalent masking spectrum level at 200 Hz")
def _chk_sii_masking() -> Outcome:
    result = ph.speech_intelligibility_index("normal")
    return numeric(ref.ANSIS3_5_MASKING_Z_200HZ, float(result.masking[1]), 1e-3, places=3)


@register(_SII, "ANSI S3.5-1997 clause 6", "SII, standard speech in quiet, normal hearing")
def _chk_sii_standard_quiet() -> Outcome:
    result = ph.speech_intelligibility_index("normal")
    return numeric(ref.ANSIS3_5_STANDARD_QUIET, result.sii, 5e-4, places=4)


@register(_SII, "ANSI S3.5-1997 Table 3", "Loud-effort speech spectrum level at 1 kHz")
def _chk_sii_loud_spectrum() -> Outcome:
    from phonometry.hearing.sii import standard_speech_spectrum

    value = float(standard_speech_spectrum("loud")[8])
    return numeric(ref.ANSIS3_5_LOUD_1KHZ, value, 1e-9, unit="dB", places=2)


_NTA = "Impulsive-sound prominence (NT ACOU 112)"


@register(_NTA, "NT ACOU 112:2002 Formula 1", "Predicted prominence, OR=1000 dB/s, LD=30 dB")
def _chk_impulse_prominence() -> Outcome:
    value = float(ph.predicted_prominence(1000.0, 30.0))
    return numeric(ref.NTACOU112_PROMINENCE, value, 1e-4, places=4)


@register(_NTA, "NT ACOU 112:2002 Formula 2", "Adjustment KI to LAeq at prominence P=10")
def _chk_impulse_adjustment() -> Outcome:
    value = float(ph.impulse_adjustment(10.0))
    return numeric(ref.NTACOU112_ADJUSTMENT_P10, value, 1e-9, unit="dB", places=3)


_RN = "Room noise (ANSI S12.2-2019)"


@register(_RN, "ANSI S12.2-2019 Table 1", "NC-40 curve, tangency self-consistency")
def _chk_rn_nc_self() -> Outcome:
    rating = ph.noise_criterion(ph.nc_curve(40.0)).rating
    return numeric(ref.ANSIS12_2_NC40_SELF, rating, 1e-9, places=3)


@register(_RN, "ANSI S12.2-2019 Table D.1", "RC-31 Mark II curve, 63 Hz level")
def _chk_rn_rc_curve() -> Outcome:
    return numeric(ref.ANSIS12_2_RC31_63HZ, float(ph.rc_curve(31.0)[2]), 1e-9, places=3)


@register(_RN, "ANSI S12.2-2019 clause D.4", "RC-35 curve, mid-frequency average LMF")
def _chk_rn_rc_lmf() -> Outcome:
    return numeric(ref.ANSIS12_2_RC35_LMF, ph.room_criterion(ph.rc_curve(35.0)).lmf, 1e-9, places=3)


_HEAR = "Hearing threshold (ISO 7029 / ISO 389-7)"


@register(_HEAR, "ISO 7029:2017 Table 1", "Median threshold, male age 60 at 4 kHz")
def _chk_hearing_median() -> Outcome:
    value = float(ph.age_threshold(60, "male", 0.5).median[8])
    return numeric(ref.ISO7029_MEDIAN_MALE_60_4KHZ, value, 1e-3, unit="dB", places=3)


@register(_HEAR, "ISO 7029:2017 Table 2", "Upper spread su, male age 60 at 1 kHz")
def _chk_hearing_spread() -> Outcome:
    value = float(ph.age_threshold(60, "male", 0.5).spread_upper[4])
    return numeric(ref.ISO7029_SU_MALE_60_1KHZ, value, 1e-3, unit="dB", places=3)


@register(_HEAR, "ISO 389-7:2006 Table 1", "Free-field reference threshold at 1 kHz")
def _chk_hearing_reference() -> Outcome:
    value = float(ph.reference_threshold("free-field")[4])
    return numeric(ref.ISO389_7_REF_FREE_1KHZ, value, 1e-9, unit="dB", places=3)


_GUM = "Measurement uncertainty (GUM / Supplement 1)"


@register(_GUM, "ISO/IEC Guide 98-3-1 clause 9.2", "Combined uncertainty, additive model")
def _chk_gum_additive() -> Outcome:
    quantities = [ph.Quantity(0.0, 1.0) for _ in range(4)]
    result = ph.combine_uncertainty(lambda a, b, c, d: a + b + c + d, quantities)
    return numeric(ref.GUM_ADDITIVE_UC, result.combined_uncertainty, 1e-9, places=4)


@register(_GUM, "ISO/IEC Guide 98-3 Table G.2", "Coverage factor, p=0.99, v=16")
def _chk_gum_coverage() -> Outcome:
    from phonometry.metrology.uncertainty import coverage_factor

    return numeric(ref.GUM_COVERAGE_K99_16, coverage_factor(0.99, 16), 5e-3, places=3)


@register(_GUM, "ISO/IEC Guide 98-3 Annex G.4", "Welch-Satterthwaite effective dof")
def _chk_gum_welch() -> Outcome:
    quantities = [ph.Quantity(0.0, 1.0, dof=10) for _ in range(4)]
    result = ph.combine_uncertainty(lambda a, b, c, d: a + b + c + d, quantities)
    return numeric(ref.GUM_WELCH_VEFF, result.effective_dof, 1e-6, places=3)


_NIHL = "Noise-induced hearing loss (ISO 1999)"


@register(_NIHL, "ISO 1999:2013 Table D.2", "Median NIPTS, 4 kHz, 90 dB, 20 yr")
def _chk_nihl_median() -> Outcome:
    value = float(ph.nipts(90.0, 20.0, 0.5).value[4])
    return numeric(ref.ISO1999_N50_4K_90_20, value, 0.5, unit="dB", places=1)


@register(_NIHL, "ISO 1999:2013 Table D.2", "Worst-10 % NIPTS, 4 kHz, 90 dB, 20 yr")
def _chk_nihl_fractile() -> Outcome:
    value = float(ph.nipts(90.0, 20.0, 0.9).value[4])
    return numeric(ref.ISO1999_N10_4K_90_20, value, 0.5, unit="dB", places=1)


@register(_NIHL, "ISO 1999:2013 Table D.4", "Worst-10 % NIPTS, 3 kHz, 100 dB, 40 yr")
def _chk_nihl_high() -> Outcome:
    value = float(ph.nipts(100.0, 40.0, 0.9).value[3])
    return numeric(ref.ISO1999_N10_3K_100_40, value, 0.5, unit="dB", places=1)


_MSV = "Multiple-shock whole-body vibration (ISO 2631-5)"


@register(_MSV, "ISO 2631-5:2018 Formula 3", "Daily acceleration dose, 5 x 40 m/s2 peaks")
def _chk_multiple_shock_dose() -> Outcome:
    value = ph.dose_from_peaks([40.0] * 5)
    return numeric(ref.ISO2631_5_DZD_MALE, value, 0.01, unit="m/s2", places=2)


@register(_MSV, "ISO 2631-5:2018 Formula C.3", "Stress variable R, Annex C male example")
def _chk_multiple_shock_risk() -> Outcome:
    sd = ph.compression_dose(ph.dose_from_peaks([40.0] * 5))
    value = ph.injury_risk(sd, start_age=20, years=20, days_per_year=120, sex="male")
    return numeric(ref.ISO2631_5_R_MALE, value, 0.01, places=2)


@register(_MSV, "ISO 2631-5:2018 Formula C.5", "Injury probability, Annex C male example")
def _chk_multiple_shock_probability() -> Outcome:
    sd = ph.compression_dose(ph.dose_from_peaks([40.0] * 5))
    r = ph.injury_risk(sd, start_age=20, years=20, days_per_year=120, sex="male")
    return numeric(ref.ISO2631_5_PI_MALE, float(ph.injury_probability(r)), 0.01, places=2)


_ABS = "Sound absorption in enclosed spaces (EN 12354-6)"


@register(_ABS, "EN 12354-6:2003 Formula 1", "Equivalent absorption area, Annex E bare room")
def _chk_enclosed_space_area() -> Outcome:
    value = float(ph.equivalent_absorption_area(ref.EN12354_6_ANNEX_E_BARE_SURFACES))
    return numeric(ref.EN12354_6_A_BARE, value, 0.01, unit="m2", places=2)


@register(_ABS, "EN 12354-6:2003 Formula 5", "Reverberation time, Annex E bare room")
def _chk_enclosed_space_rt() -> Outcome:
    area = ph.equivalent_absorption_area(ref.EN12354_6_ANNEX_E_BARE_SURFACES)
    value = float(ph.reverberation_time(area, ref.EN12354_6_ANNEX_E_VOLUME))
    return numeric(ref.EN12354_6_T_BARE, value, 0.05, unit="s", places=1)


_TONES = "Prominent discrete tones (ECMA-418-1)"


@register(_TONES, "ECMA-418-1:2024 Clause 10 Formula (2)", "Critical band at 1 kHz (f1,c / f2,c / dfc)")
def _chk_ecma418_1_critical_band() -> Outcome:
    from phonometry.psychoacoustics.tonality import _critical_band

    f1, f2, dfc = _critical_band(1000.0)
    # 0.05 Hz = half a unit in the last printed digit (the clause EXAMPLE
    # values are given to one decimal: 922,2 / 1084,4 / 162,2 Hz).
    out = numeric(ref.ECMA418_1_DFC_1KHZ, float(dfc), 0.05, unit="Hz", places=2)
    edges_ok = (
        abs(float(f1) - ref.ECMA418_1_F1_1KHZ) <= 0.05
        and abs(float(f2) - ref.ECMA418_1_F2_1KHZ) <= 0.05
    )
    return Outcome(
        expected=(
            f"dfc {out.expected}; edges {ref.ECMA418_1_F1_1KHZ:g}"
            f"-{ref.ECMA418_1_F2_1KHZ:g} Hz"
        ),
        computed=f"dfc {out.computed}; edges {float(f1):.1f}-{float(f2):.1f} Hz",
        delta=out.delta,
        passed=out.passed and edges_ok,
    )


@register(_TONES, "ECMA-418-1:2024 Clause 11.6 Formula (14)", "Proximity spacing dfprox at 150 / 850 Hz")
def _chk_ecma418_1_proximity_spacing() -> Outcome:
    from phonometry.psychoacoustics.tonality import _proximity_spacing

    v150 = float(_proximity_spacing(150.0))
    v850 = float(_proximity_spacing(850.0))
    # 0.5 Hz = half a unit in the last printed digit of the coarser EXAMPLE
    # value (the standard prints 23 Hz with no decimals; 63,8 Hz with one).
    ok = (
        abs(v150 - ref.ECMA418_1_PROX_150HZ) <= 0.5
        and abs(v850 - ref.ECMA418_1_PROX_850HZ) <= 0.5
    )
    return Outcome(
        expected=(
            f"{ref.ECMA418_1_PROX_150HZ:g} Hz @ 150 Hz; "
            f"{ref.ECMA418_1_PROX_850HZ:g} Hz @ 850 Hz (+/-0.5 Hz)"
        ),
        computed=f"{v150:.1f} Hz; {v850:.1f} Hz",
        delta=(
            f"{v150 - ref.ECMA418_1_PROX_150HZ:+.3f}; "
            f"{v850 - ref.ECMA418_1_PROX_850HZ:+.3f} Hz"
        ),
        passed=ok,
    )


_TONE_AUD = "Tonal audibility (ISO/PAS 20065)"


@register(_TONE_AUD, "ISO/PAS 20065:2016 Formulae (12)-(14)", "Audibility at 137.3 Hz, Annex E spectrum 1")
def _chk_iso20065_audibility() -> Outcome:
    fT, ls, lt, expected = ref.ISO20065_ANNEX_E_TONES[1]  # 137.3 Hz tone
    value = ph.tone_audibility(lt, ls, fT, ref.ISO20065_LINE_SPACING)
    # 0.05 dB absorbs the standard's 2-decimal table rounding of LS/LT/LG/av.
    return numeric(expected, value, 0.05, unit="dB", places=2)


@register(_TONE_AUD, "ISO/PAS 20065:2016 Formula (13)", "Masking index av at 137.3 / 592.2 Hz")
def _chk_iso20065_masking_index() -> Outcome:
    av137 = ph.masking_index(137.3)
    av592 = ph.masking_index(592.2)
    ok = (
        abs(av137 - ref.ISO20065_AV_137) <= 0.005
        and abs(av592 - ref.ISO20065_AV_592) <= 0.005
    )
    return Outcome(
        expected=f"{ref.ISO20065_AV_137:g} dB @ 137.3 Hz; "
        f"{ref.ISO20065_AV_592:g} dB @ 592.2 Hz (+/-0.005 dB)",
        computed=f"{av137:.3f} dB; {av592:.3f} dB",
        delta=f"{av137 - ref.ISO20065_AV_137:+.3f}; "
        f"{av592 - ref.ISO20065_AV_592:+.3f} dB",
        passed=ok,
    )


@register(_TONE_AUD, "ISO/PAS 20065:2016 Formula (20)", "Mean audibility of the five spectra, Annex E")
def _chk_iso20065_mean_audibility() -> Outcome:
    value = ph.mean_audibility(ref.ISO20065_DECISIVE_AUDIBILITIES)
    # 0.05 dB absorbs the 2-decimal rounding of the tabulated decisive values.
    return numeric(ref.ISO20065_MEAN_AUDIBILITY, value, 0.05, unit="dB", places=2)


@register(_TONE_AUD, "ISO/PAS 20065:2016 Formula (6)", "Mean narrow-band level LS from spectrum, Table E.1")
def _chk_iso20065_mean_narrowband_level() -> Outcome:
    value = ph.mean_narrowband_level(
        ref.ISO20065_E1_LEVELS, ref.ISO20065_E1_FREQUENCIES, 137.3
    )
    # Iterative Formula (6) with Hanning correction; 0.02 dB absorbs rounding.
    return numeric(ref.ISO20065_E1_LS, value, 0.02, unit="dB", places=2)


@register(_TONE_AUD, "ISO/PAS 20065:2016 Formula (8)", "Tone level LT from spectrum, Table E.1")
def _chk_iso20065_tone_level() -> Outcome:
    ls = ph.mean_narrowband_level(
        ref.ISO20065_E1_LEVELS, ref.ISO20065_E1_FREQUENCIES, 137.3
    )
    value = ph.tone_level(
        ref.ISO20065_E1_LEVELS, ref.ISO20065_E1_FREQUENCIES, 137.3, ls
    )
    return numeric(ref.ISO20065_E1_LT, value, 0.02, unit="dB", places=2)


@register(_TONE_AUD, "ISO/PAS 20065:2016 Clause 5.3.8", "Tone detection over the spectrum, Table E.1")
def _chk_iso20065_peak_detection() -> Outcome:
    result = ph.analyze_spectrum(
        ref.ISO20065_E1_LEVELS, ref.ISO20065_E1_FREQUENCIES, ref.ISO20065_LINE_SPACING
    )
    found = sorted(round(float(f), 1) for f in result.tone_frequencies)
    expected = sorted(ref.ISO20065_E1_TONE_FREQUENCIES)
    ok = found == expected
    return Outcome(
        expected=f"tones at {expected} Hz",
        computed=f"tones at {found} Hz",
        delta="exact" if ok else "mismatch",
        passed=ok,
    )


@register(_TONE_AUD, "ISO/PAS 20065:2016 Formula (17)", "Multi-tone FG combination, Table E.1")
def _chk_iso20065_fg_combination() -> Outcome:
    value = ph.combined_tone_level(
        ref.ISO20065_E1_LEVELS,
        ref.ISO20065_E1_FREQUENCIES,
        ref.ISO20065_E1_TONE_FREQUENCIES,
        ref.ISO20065_E1_TONE_LS,
    )
    return numeric(ref.ISO20065_E1_LT_FG, value, 0.02, unit="dB", places=2)


@register(
    _TONE_AUD,
    "ISO/PAS 20065:2016 Formulae (18)/(19)",
    "Two-tone separation fD (DIN 45681 Annex J), 137.3 / 212 Hz",
)
def _chk_iso20065_two_tone_separation() -> Outcome:
    fd_137 = ph.two_tone_separation_frequency(137.3)
    fd_212 = ph.two_tone_separation_frequency(212.0)
    # Annex E consistency: the 118.4/137.3 Hz pair is combined, not separated
    # (|Δf| = 18.9 Hz < fD ≈ 24 Hz at the more prominent tone).
    annex_e_combined = not ph.resolve_tones_separately(118.4, 137.3, 4.0, 5.0)
    ok = (
        round(fd_137, 2) == ref.ISO20065_FD_137
        and round(fd_212, 2) == ref.ISO20065_FD_212
        and annex_e_combined
    )
    return Outcome(
        expected=(
            f"fD(137.3)={ref.ISO20065_FD_137}, fD(212)={ref.ISO20065_FD_212} Hz; "
            "Annex E pair combined"
        ),
        computed=(
            f"fD(137.3)={fd_137:.2f}, fD(212)={fd_212:.2f} Hz; "
            f"Annex E pair {'combined' if annex_e_combined else 'separated'}"
        ),
        delta="exact" if ok else "mismatch",
        passed=ok,
    )


# ===========================================================================
# Psychoacoustic annoyance & fluctuation strength (Fastl & Zwicker)
# ===========================================================================
_PA_FS = "Psychoacoustic annoyance & fluctuation strength (Fastl & Zwicker)"


@register(
    _PA_FS,
    "Fastl & Zwicker Eqs (16.2)-(16.4)",
    "Psychoacoustic annoyance, worked (N5,S,F,R) tuple",
)
def _chk_psychoacoustic_annoyance() -> Outcome:
    n5, s, f, r = ref.PA_WORKED_INPUT
    value = ph.psychoacoustic_annoyance(n5, s, f, r).annoyance
    return numeric(ref.PA_WORKED_VALUE, value, 1e-3, places=4)


@register(
    _PA_FS,
    "Fastl & Zwicker Eq (10.2)",
    "Fluctuation strength of AM broadband noise (60 dB, m=1, 4 Hz)",
)
def _chk_fluctuation_strength_am_noise() -> Outcome:
    value = ph.fluctuation_strength_am_noise(60.0, 1.0, 4.0)
    return numeric(ref.FS_BBN_60_1_4, value, 1e-3, unit="vacil", places=4)


@register(
    _PA_FS,
    "Fastl & Zwicker Ch. 10 / Osses et al. 2016",
    "Fluctuation-strength calibration: 1 kHz / 60 dB / m=1 / 4 Hz AM tone",
)
def _chk_fluctuation_strength_calibration() -> Outcome:
    # The signal model is anchored (clean-room) so the 1-vacil reference tone
    # returns 1.00 vacil through its own front-end. No numeric standard exists.
    fs = 48000
    t = np.arange(int(fs * 2.0)) / fs
    tone = (1.0 + np.sin(2.0 * np.pi * 4.0 * t)) * np.sin(2.0 * np.pi * 1000.0 * t)
    tone = tone / np.sqrt(np.mean(tone**2)) * 2e-5 * 10.0 ** (60.0 / 20.0)
    value = ph.fluctuation_strength(tone, fs).fluctuation_strength
    return numeric(
        ref.FS_CALIBRATION_VACIL, value, 0.05, unit="vacil", places=3
    )


# ===========================================================================
# Electroacoustics: distortion & frequency response (IEC 60268-3 / Bendat)
# ===========================================================================
_ELECTRO = "Electroacoustics: distortion & frequency response"


def _electro_fs() -> int:
    return 48000


def _electro_tone(t: np.ndarray, freq: float, amp: float) -> np.ndarray:
    """A single sine of amplitude ``amp`` at ``freq`` over the time base ``t``."""
    return amp * np.sin(2.0 * np.pi * freq * t)


def _electro_harmonic_signal() -> np.ndarray:
    fs = _electro_fs()
    t = np.arange(fs) / fs  # 1 s, tones on integer bins
    a1, a2, a3, a4 = ref.DISTORTION_HARMONICS
    sig = (
        _electro_tone(t, 1000.0, a1)
        + _electro_tone(t, 2000.0, a2)
        + _electro_tone(t, 3000.0, a3)
        + _electro_tone(t, 4000.0, a4)
    )
    return np.asarray(sig, dtype=np.float64)


@register(
    _ELECTRO,
    "IEC 60268-3:2013 (14.12.2-3)",
    "THD (rel. fundamental) of a synthetic 4-harmonic signal",
)
def _chk_thd_f() -> Outcome:
    value = ph.thd(_electro_harmonic_signal(), _electro_fs(), 1000.0, kind="F")
    return numeric(ref.DISTORTION_THD_F, value, 1e-4, places=6)


@register(
    _ELECTRO,
    "IEC 60268-3:2013 (14.12.5)",
    "2nd-order harmonic distortion d2 (rel. total)",
)
def _chk_harmonic_d2() -> Outcome:
    value = ph.harmonic_distortion(_electro_harmonic_signal(), _electro_fs(), 1000.0, 2)
    return numeric(ref.DISTORTION_D2, value, 1e-4, places=6)


@register(
    _ELECTRO,
    "IEC 60268-3:2013 (14.12.7)",
    "SMPTE modulation distortion of a known two-tone signal",
)
def _chk_smpte() -> Outcome:
    fs = _electro_fs()
    t = np.arange(fs) / fs
    fl, fh, ah = 250.0, 8000.0, 0.25
    x = (
        _electro_tone(t, fl, 1.0)
        + _electro_tone(t, fh, ah)
        + _electro_tone(t, fh + fl, 0.02)
        + _electro_tone(t, fh - fl, 0.02)
        + _electro_tone(t, fh + 2 * fl, 0.01)
        + _electro_tone(t, fh - 2 * fl, 0.01)
    )
    expected = math.sqrt(0.02**2 + 0.02**2 + 0.01**2 + 0.01**2) / ah
    return numeric(expected, ph.modulation_distortion(x, fs, fl, fh), 1e-4, places=6)


@register(
    _ELECTRO,
    "IEC 60268-3:2013 (14.12.8)",
    "CCIF difference-frequency distortion (2nd order) of a two-tone signal",
)
def _chk_ccif() -> Outcome:
    fs = _electro_fs()
    t = np.arange(fs) / fs
    f1, f2 = 13000.0, 14000.0
    x = (
        _electro_tone(t, f1, 0.5)
        + _electro_tone(t, f2, 0.5)
        + _electro_tone(t, f2 - f1, 0.03)
    )
    return numeric(
        0.03 / 0.5,
        ph.difference_frequency_distortion(x, fs, f1, f2, order=2),
        1e-4,
        places=6,
    )


@register(
    _ELECTRO,
    "IEC 60268-3:2013 (14.12.9)",
    "DIM of the 15 kHz / 3.15 kHz signal (Table 2, 9 products)",
)
def _chk_dim() -> Outcome:
    fs = _electro_fs()
    t = np.arange(fs) / fs
    fsine, fsq = 15000.0, 3150.0
    comps = sorted(
        round(abs(k * fsq - fsine), 6) for k in range(1, 10) if abs(k * fsq - fsine) < fsine
    )
    amps = [0.01 * (i + 1) for i in range(len(comps))]
    # 15 kHz sine + the strong 3.15 kHz fundamental + the nine products.
    x = _electro_tone(t, fsine, 1.0) + _electro_tone(t, fsq, 0.8)
    for c, a in zip(comps, amps):
        x = x + _electro_tone(t, c, a)
    expected = math.sqrt(sum(a**2 for a in amps))
    return numeric(expected, ph.dynamic_intermodulation_distortion(x, fs), 1e-4, places=6)


@register(
    _ELECTRO,
    "Bendat & Piersol, Random Data 4e",
    "H1 recovers a known first-order IIR gain at 1 kHz",
)
def _chk_h1_gain() -> Outcome:
    fs = _electro_fs()
    rng = np.random.default_rng(1)
    x = rng.standard_normal(200000)
    b, a = sg.butter(1, 2000.0 / (fs / 2.0), btype="low")
    y = sg.lfilter(b, a, x)
    res = ph.transfer_function(x, y, fs, estimator="H1")
    _, h = sg.freqz(b, a, worN=res.frequencies, fs=fs)
    idx = int(np.argmin(np.abs(res.frequencies - 1000.0)))
    return numeric(
        float(np.abs(h[idx])), float(np.abs(res.response[idx])), 0.02, rel=True, places=4
    )


@register(
    _ELECTRO,
    "Bendat & Piersol, Random Data 4e",
    "Ordinary coherence = 1 for a noiseless LTI path",
)
def _chk_coherence_unity() -> Outcome:
    fs = _electro_fs()
    rng = np.random.default_rng(1)
    x = rng.standard_normal(200000)
    b, a = sg.butter(1, 2000.0 / (fs / 2.0), btype="low")
    y = sg.lfilter(b, a, x)
    f, g = ph.coherence(x, y, fs)
    band = (f > 100.0) & (f < 5000.0)
    return numeric(1.0, float(np.mean(g[band])), 1e-3, places=6)


# ===========================================================================
# Underwater acoustics (ISO 18405 / 17208 / 18406)
# ===========================================================================
_UNDERWATER = "Underwater acoustics (ISO 18405/17208/18406)"


@register(
    _UNDERWATER,
    "ISO 18405:2017 / ISO 18406 Formula 7",
    "Sound pressure level of a synthetic tone, dB re 1 µPa",
)
def _chk_uw_spl() -> Outcome:
    fs = 48000
    t = np.arange(fs) / fs
    amp = 2.0  # Pa
    x = amp * np.sin(2.0 * np.pi * 500.0 * t)
    expected = 20.0 * math.log10((amp / math.sqrt(2.0)) / 1e-6)
    return numeric(expected, ph.sound_pressure_level(x), 1e-4, places=4)


@register(
    _UNDERWATER,
    "ISO 18405:2017 / ISO 18406 Formulae 3-4",
    "Sound exposure level of a 2 s tone, dB re 1 µPa²·s",
)
def _chk_uw_sel() -> Outcome:
    fs = 48000
    t = np.arange(2 * fs) / fs
    amp = 1.0
    x = amp * np.sin(2.0 * np.pi * 500.0 * t)
    spl = 20.0 * math.log10((amp / math.sqrt(2.0)) / 1e-6)
    expected = spl + 10.0 * math.log10(2.0)
    return numeric(expected, ph.sound_exposure_level(x, fs), 1e-3, places=4)


@register(
    _UNDERWATER,
    "ISO 18406:2017 (6.4.2.1.3)",
    "Peak sound pressure level of a known waveform, dB re 1 µPa",
)
def _chk_uw_peak() -> Outcome:
    fs = 48000
    t = np.arange(fs) / fs
    amp = 3.0
    x = amp * np.sin(2.0 * np.pi * 500.0 * t)
    expected = 20.0 * math.log10(amp / 1e-6)
    return numeric(expected, ph.peak_sound_pressure_level(x), 1e-4, places=4)


@register(
    _UNDERWATER,
    "ISO 17208-1:2016",
    "Radiated noise level from RMS pressure and distance, dB re 1 µPa·m",
)
def _chk_uw_rnl() -> Outcome:
    expected = 20.0 * math.log10(2.0) + 40.0  # p = 2 µPa, r = 100 m
    return numeric(expected, ph.radiated_noise_level(2e-6, 100.0), 1e-4, places=4)


@register(
    _UNDERWATER,
    "ISO 17208-2:2019 (Formula 3)",
    "Lloyd's-mirror surface correction ΔL at a known k·d_s",
)
def _chk_uw_delta_l() -> Outcome:
    draught, c, f = 10.0, 1500.0, 200.0
    ds = 0.7 * draught
    u = 2.0 * math.pi * f / c * ds
    expected = -10.0 * math.log10((2 * u**4 + 14 * u**2) / (14 + 2 * u**2 + u**4))
    res = ph.monopole_source_level(120.0, f, draught, c=c)
    return numeric(expected, float(res.surface_correction[0]), 1e-4, places=4)


@register(
    _UNDERWATER,
    "ISO 18406:2017 (Formulae 8-9)",
    "Cumulative SEL of N identical strikes = SEL_ss + 10·lg(N)",
)
def _chk_uw_cumulative_sel() -> Outcome:
    return numeric(
        180.0 + 10.0 * math.log10(50),
        ph.cumulative_sel_identical(180.0, 50),
        1e-6,
        places=4,
    )


# ===========================================================================
# Underwater sound propagation (transmission loss, closed-form)
# ===========================================================================
_UW_PROP = "Underwater sound propagation (transmission loss)"


@register(
    _UW_PROP,
    "Mackenzie (1981) nine-term equation",
    "Speed of sound at 25 °C, 35 ‰, 1000 m (canonical check value), m/s",
)
def _chk_uwp_mackenzie() -> Outcome:
    return numeric(
        1550.744,
        ph.sea_water_sound_speed(25.0, 35.0, 1000.0, model="mackenzie"),
        1e-2,
        unit="m/s",
        places=3,
    )


@register(
    _UW_PROP,
    "UNESCO/Chen-Millero vs Mackenzie",
    "Sound-speed agreement at 10 °C, 35 ‰, 1000 m (cross-model), m/s",
)
def _chk_uwp_unesco() -> Outcome:
    expected = ph.sea_water_sound_speed(10.0, 35.0, 1000.0, model="mackenzie")
    got = ph.sea_water_sound_speed(10.0, 35.0, 1000.0, model="unesco")
    return numeric(expected, got, 1.0, unit="m/s", places=3)


@register(
    _UW_PROP,
    "Del Grosso (1974) vs Mackenzie",
    "Sound-speed agreement at 10 °C, 35 ‰, 1000 m (cross-model), m/s",
)
def _chk_uwp_del_grosso() -> Outcome:
    expected = ph.sea_water_sound_speed(10.0, 35.0, 1000.0, model="mackenzie")
    got = ph.sea_water_sound_speed(10.0, 35.0, 1000.0, model="del_grosso")
    return numeric(expected, got, 1.0, unit="m/s", places=3)


@register(
    _UW_PROP,
    "Spherical spreading 20·lg(R)",
    "Geometrical spreading loss at R = 1000 m, dB",
)
def _chk_uwp_spreading() -> Outcome:
    return numeric(
        20.0 * math.log10(1000.0),
        float(ph.spreading_loss([1000.0], law="spherical")[0]),
        1e-9,
        unit="dB",
        places=4,
    )


@register(
    _UW_PROP,
    "Thorp (1967) absorption",
    "Volume absorption α at 10 kHz (cold deep water), dB/km",
)
def _chk_uwp_thorp() -> Outcome:
    f = 10.0  # kHz
    expected = 1.0936 * (0.1 * f**2 / (1 + f**2) + 40 * f**2 / (4100 + f**2))
    got = float(ph.seawater_absorption(10_000.0, model="thorp")[0])
    return numeric(expected, got, 1e-6, unit="dB/km", places=4)


@register(
    _UW_PROP,
    "Ainslie-McColm (1998) vs Francois-Garrison (1982)",
    "Absorption agreement at 10 kHz, 10 °C, 35 ‰, 0 m, pH 8, dB/km",
)
def _chk_uwp_absorption_agreement() -> Outcome:
    kw = dict(temperature=10.0, salinity=35.0, depth=0.0, ph=8.0)
    fg = float(ph.seawater_absorption(10_000.0, model="francois-garrison", **kw)[0])
    am = float(ph.seawater_absorption(10_000.0, model="ainslie-mccolm", **kw)[0])
    return numeric(fg, am, 0.1 * fg, unit="dB/km", places=4)


@register(
    _UW_PROP,
    "Passive sonar equation (Urick/Etter)",
    "Figure of merit SL − (NL − DI) − DT, dB",
)
def _chk_uwp_sonar() -> Outcome:
    res = ph.passive_sonar_equation(140.0, 80.0, 60.0, directivity_index=10.0, detection_threshold=5.0)
    return numeric(85.0, res.figure_of_merit, 1e-9, unit="dB", places=4)


@register(
    _UW_PROP,
    "Seabed reflection (Rayleigh, normal incidence)",
    "Bottom loss at 90° grazing, sand ρ=1900 c=1650 over water, dB",
)
def _chk_uwp_seabed() -> Outcome:
    # Normal-incidence oracle: R = (Z2 − Z1)/(Z2 + Z1), BL = −20·lg|R|.
    z1, z2 = 1000.0 * 1500.0, 1900.0 * 1650.0
    expected = -20.0 * math.log10(abs((z2 - z1) / (z2 + z1)))
    res = ph.bottom_reflection_loss(90.0, rho1=1000.0, c1=1500.0, rho2=1900.0, c2=1650.0)
    return numeric(expected, float(res.reflection_loss[0]), 1e-6, unit="dB", places=4)


@register(
    _UW_PROP,
    "Wenz wind noise (rule of fives)",
    "Wind spectrum level at 1 kHz, 5 kn (canonical anchor), dB re 1 µPa²/Hz",
)
def _chk_uwp_wind_noise() -> Outcome:
    got = float(ph.wind_noise_spectrum(1000.0, 5.0)[0])
    return numeric(25.0, got, 1e-9, unit="dB", places=4)


@register(
    _UW_PROP,
    "Mellen thermal noise",
    "Thermal spectrum level at 50 kHz, 16.85 °C (physical), dB re 1 µPa²/Hz",
)
def _chk_uwp_thermal_noise() -> Outcome:
    f, t, rho, c = 5.0e4, 16.85, 1025.0, 1500.0
    p2 = 4.0 * math.pi * 1.380649e-23 * (t + 273.15) * rho * f**2 / c
    expected = 10.0 * math.log10(p2 / (1e-6) ** 2)
    got = float(ph.thermal_noise_spectrum(f, temperature=t, density=rho, sound_speed=c)[0])
    return numeric(expected, got, 1e-6, unit="dB", places=4)


@register(
    _UW_PROP,
    "JOMOPANS-ECHO ship source level",
    "Bulker V=13.5 kn L=211 m band level at 1 kHz (File S1 oracle), dB re 1 µPa m",
)
def _chk_uwp_ship_traffic() -> Outcome:
    # Oracle: authors' Excel reference calculator (File S1), decidecade band.
    s = ph.ship_source_spectrum(13.5, 211.0, vessel_class="bulker", model="jomopans-echo")
    idx = int(min(range(len(s.frequency)), key=lambda i: abs(s.frequency[i] - 1000.0)))
    return numeric(161.394, float(s.band_level[idx]), 1e-2, unit="dB", places=3)


# ===========================================================================
# Underwater numerical propagation (Jensen et al., modes / rays / PE)
# ===========================================================================
_UW_NUM = "Underwater numerical propagation (modes / rays / PE)"


@register(
    _UW_NUM,
    "Normal modes vs ideal waveguide",
    "Fundamental horizontal wavenumber kr1 at 20 Hz, 100 m (analytic), rad/m",
)
def _chk_uwn_modes() -> Outcome:
    d, c, f = 100.0, 1500.0, 20.0
    k = 2.0 * math.pi * f / c
    kr1 = math.sqrt(k**2 - (math.pi / d) ** 2)
    res = ph.normal_modes(f, [0.0, d], [c, c], source_depth=36.0, receiver_depth=46.0,
                          bottom="pressure-release", n_depth_points=800)
    return numeric(kr1, float(res.wavenumbers[0]), 1e-4, unit="rad/m", places=6)


@register(
    _UW_NUM,
    "Ray tracing vs linear gradient",
    "Turning depth of a 10° ray, c = 1500 + 0.05z (circular arc), m",
)
def _chk_uwn_rays() -> Outcome:
    c0, g = 1500.0, 0.05
    xi = math.cos(math.radians(10.0)) / c0
    z_turn = (1.0 / xi - c0) / g
    res = ph.ray_trace([0.0, 2000.0], [c0, c0 + g * 2000.0], source_depth=0.0,
                       launch_angles_deg=[10.0], max_range=10_500.0, n_steps=20_000)
    return numeric(z_turn, float(res.depths[0].max()), 1.0, unit="m", places=2)


@register(
    _UW_NUM,
    "Parabolic equation vs free field",
    "PE transmission loss at 2 km, homogeneous medium (spherical spreading), dB",
)
def _chk_uwn_pe() -> Outcome:
    res = ph.parabolic_equation(50.0, [0.0, 20_000.0], [1500.0, 1500.0],
                                source_depth=10_000.0, max_range=3000.0,
                                range_step=2.0, n_depth_points=8192)
    zi = int(min(range(res.depths.size), key=lambda i: abs(res.depths[i] - 10_000.0)))
    ri = int(min(range(res.ranges.size), key=lambda i: abs(res.ranges[i] - 2000.0)))
    return numeric(20.0 * math.log10(2000.0), float(res.transmission_loss[zi][ri]),
                   0.1, unit="dB", places=3)


# ===========================================================================
# Aircraft noise (ICAO Annex 16 EPNL / IEC 61265)
# ===========================================================================
_AIRCRAFT = "Aircraft noise (ICAO Annex 16 / IEC 61265)"


@register(
    _AIRCRAFT,
    "ECAC Doc 29 noise fraction (half path)",
    "Finite-segment correction ΔF for a perpendicular foot at the segment start, dB",
)
def _chk_ecac_noise_fraction() -> Outcome:
    # A half-infinite segment (Sp at the start) receives half the energy: −3.01 dB.
    got = float(ph.noise_fraction(0.0, 10_000.0, 100.0))
    return numeric(-10.0 * math.log10(2.0), got, 1e-3, unit="dB", places=4)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 single-event chain",
    "SEL of a long level flyover vs the infinite-path limit LE∞ + ΔI − Λ, dB",
)
def _chk_ecac_event_level() -> Outcome:
    # A long straight level segment through the CPA reduces to the infinite-path
    # baseline plus the geometry corrections (ΔF → 0, ΔV = 0 at Vref).
    npd_p = [8000.0, 12000.0]
    npd_d = [60.0, 120.0, 240.0, 480.0, 960.0, 1920.0, 3840.0]
    sel = [[98.0, 92.0, 86.0, 80.0, 74.0, 68.0, 62.0], [102.0, 96.0, 90.0, 84.0, 78.0, 72.0, 66.0]]
    lmax = [[94.0, 88.0, 82.0, 76.0, 70.0, 64.0, 58.0], [98.0, 92.0, 86.0, 80.0, 74.0, 68.0, 62.0]]
    vref = 160.0 * 0.514444
    import numpy as _np

    xs = _np.linspace(-40000.0, 40000.0, 801)
    path = _np.column_stack([xs, _np.zeros_like(xs), _np.full_like(xs, 300.0),
                             _np.full_like(xs, 10000.0), _np.full_like(xs, vref)])
    got = ph.event_level(path, [0.0, 300.0, 0.0], npd_p, npd_d, sel, lmax, metric="exposure").level
    dp = math.hypot(300.0, 300.0)
    beta = math.degrees(math.acos(300.0 / dp))
    expected = (float(ph.npd_level(npd_p, npd_d, sel, 10000.0, dp)[0])
                + ph.impedance_adjustment()
                + ph.engine_installation_correction(beta, "wing")
                - ph.lateral_attenuation(beta, 300.0))
    return numeric(expected, float(got), 1e-2, unit="dB", places=3)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 impedance adjustment (standard atmosphere)",
    "Acoustic-impedance adjustment of NPD data at 15 °C / 101.325 kPa (Eq. 4-6/4-7), dB",
)
def _chk_ecac_impedance() -> Outcome:
    # ECAC Doc 29 Vol 2 §4.2.1 states the standard-atmosphere adjustment is
    # +0.074 dB (ρc = 416.86, reference impedance 409.81 N·s/m³).
    return numeric(0.074, float(ph.impedance_adjustment()), 5e-4, unit="dB", places=4)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 reference workbook (segment Λ)",
    "Lateral attenuation of a climbing segment vs the ECAC Vol 3 Part 1 workbook, dB",
)
def _chk_ecac_workbook_segment() -> Outcome:
    # ECAC Doc 29 5th ed. Vol 3 Part 1 reference workbook, sheet
    # B-2_Segment_Results, case JETFAC receptor R02 segment 1 (climbing): the
    # workbook lists β = 4.2226°, lateral displacement 81363.28 ft (24799.6 m)
    # and Λ = 6.3769 dB. Here we anchor the Λ(β, ℓ) formula to those reference
    # values (the β/φ geometry itself is validated in tests/test_airport_noise).
    beta_ref, lateral_m = 4.2225708673, 81363.2829 * 0.3048
    got = float(ph.lateral_attenuation(beta_ref, lateral_m))
    return numeric(6.3768594165, got, 1e-2, unit="dB", places=4)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 start-of-roll directivity (jet)",
    "ΔSOR behind a takeoff ground-roll segment vs the Vol 3 Part 1 workbook, dB",
)
def _chk_ecac_start_of_roll() -> Outcome:
    # ECAC Doc 29 5th ed. Vol 3 Part 1 workbook, case JETFDC: at ψ = 112.8895°,
    # dSOR = 217.09 m the turbofan directivity (Eq. 4-24a) is +0.3196 dB.
    got = float(ph.start_of_roll_directivity(112.889545, 217.0934, "jet"))
    return numeric(0.31961, got, 1e-2, unit="dB", places=4)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 start-of-roll directivity (turboprop)",
    "ΔSOR behind a takeoff ground-roll segment (turboprop, Eq. 4-24b), dB",
)
def _chk_ecac_start_of_roll_prop() -> Outcome:
    # Same workbook, case PROPDC: at ψ = 128.1824°, dSOR = 254.44 m the turboprop
    # directivity (Eq. 4-24b) is +1.0943 dB.
    got = float(ph.start_of_roll_directivity(128.182381, 254.4361, "turboprop"))
    return numeric(1.09434, got, 1e-2, unit="dB", places=4)


@register(
    _AIRCRAFT,
    "SAE ARP 5534 band-attenuation continuity",
    "SAE-Method δ_B at the 150 dB branch split (Eq. 7 vs Eq. 8), dB",
)
def _chk_arp5534_continuity() -> Outcome:
    # The two SAE-Method branches meet at δ_t = 150 dB (Eqs. 7-8).
    a, b, c, d, e = 0.867942, 0.111761, 0.95824, 0.008191, 1.6
    eq7 = a * 150.0 * (1.0 + b * (c - d * 150.0)) ** e
    eq8 = 9.2 + 0.765 * 150.0
    return numeric(eq8, eq7, 0.01, unit="dB", places=3)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 NPD interpolation",
    "Log-linear NPD level at the log-midpoint distance (Eq. 4-4), dB",
)
def _chk_ecac_npd() -> Outcome:
    # Log-midpoint distance -> arithmetic mean of the bracketing node levels.
    p, d = [1000.0, 2000.0], [200.0, 400.0, 800.0, 1600.0]
    lv = [[100.0, 94.0, 88.0, 82.0], [110.0, 104.0, 98.0, 92.0]]
    got = float(ph.npd_level(p, d, lv, 1000.0, math.sqrt(200.0 * 400.0))[0])
    return numeric(97.0, got, 1e-9, unit="dB", places=4)


_ROTORCRAFT = "Rotorcraft noise (ECAC Doc 32 / NORAH2)"


@register(
    _ROTORCRAFT,
    "ECAC Doc 32 atmospheric attenuation (Table 4)",
    "ΔLa over a 1 km excess path at 1 kHz vs the NORAH2 guidance Table 4, dB",
)
def _chk_doc32_atmospheric() -> Outcome:
    # NORAH2 guidance Table 4: 6.3 dB/km at 1 kHz (ICAO reference conditions).
    got = -float(ph.atmospheric_adjustment([1000.0], 1000.0 + 60.0)[0])
    return numeric(6.3, got, 0.2, unit="dB", places=3)


@register(
    _ROTORCRAFT,
    "ECAC Doc 32 spherical spreading",
    "ΔLs at ten times the 60 m hemisphere reference distance (Eq. 24), dB",
)
def _chk_doc32_spreading() -> Outcome:
    return numeric(-20.0, float(ph.spherical_spreading_adjustment(600.0)), 1e-9,
                   unit="dB", places=3)


@register(
    _ROTORCRAFT,
    "ECAC Doc 32 ground effect (rigid limit)",
    "ΔLg over a rigid surface at grazing incidence tends to +6 dB (Eq. 29), dB",
)
def _chk_doc32_ground() -> Outcome:
    # Over a near-rigid surface (Zs -> inf), coherent reflection at a small path
    # difference reinforces the direct ray towards the +6.02 dB pressure-doubling
    # limit. A low frequency and near-grazing geometry approaches it.
    got = float(ph.ground_effect_adjustment([20.0], 50.0, 1.2, 400.0, flow_resistivity="H")[0])
    return numeric(6.0, got, 1.0, unit="dB", places=2)


@register(
    _AIRCRAFT,
    "SAE ARP 5534 pure-tone coefficient (ISO 9613-1)",
    "Mid-band α at 1 kHz, 25 °C, 70 % RH, 101.325 kPa, dB/m",
)
def _chk_arp5534_coefficient() -> Outcome:
    # ARP 5534 §3.1: the pure-tone coefficient is the ISO 9613-1 one.
    expected = float(ph.air_attenuation(1000.0, 25.0, 70.0, 101.325, exact_midband=True))
    res = ph.sae_band_attenuation([1000.0], 1000.0, temperature=25.0, relative_humidity=70.0)
    return numeric(expected, float(res.coefficient[0]), 1e-9, unit="dB/m", places=6)

# ICAO Doc 9501 ETM Vol. I (2018) Table 3-7 turbofan spectrum (bands 1-2 blank).
_ETM_SPL_37 = [
    -999.0, -999.0, 70.0, 62.0, 70.0, 80.0, 82.0, 83.0, 76.0, 80.0,
    80.0, 79.0, 78.0, 80.0, 78.0, 76.0, 79.0, 85.0, 79.0, 78.0, 71.0, 60.0, 54.0, 45.0,
]
# ICAO Doc 9501 ETM Vol. I (2018) Table 4-4 integrated-method EPNL example.
_ETM_PNLTR_44 = [
    84.62, 85.84, 85.37, 88.57, 88.82, 88.03, 88.76, 87.06, 86.92, 90.39, 89.89,
    91.00, 90.08, 89.71, 89.61, 90.21, 91.14, 92.10, 93.68, 94.89, 95.87, 97.06,
    97.40, 96.23, 94.73, 92.30, 88.75, 86.96, 85.41, 83.88, 83.01,
]
_ETM_DTR_44 = [
    0.3950, 0.3950, 0.3951, 0.3951, 0.3952, 0.3953, 0.3954, 0.3956, 0.3957, 0.3960,
    0.3963, 0.3967, 0.3973, 0.3981, 0.3992, 0.4009, 0.4033, 0.4066, 0.4108, 0.4153,
    0.4196, 0.4231, 0.4256, 0.4273, 0.4285, 0.4294, 0.4299, 0.4304, 0.4307, 0.4309,
    0.4311,
]


@register(
    _AIRCRAFT,
    "ICAO Annex 16 Vol. I App. 2 Table A2-3",
    "Perceived noisiness at SPL(b), 1 kHz band, in noys",
)
def _chk_ac_noy() -> Outcome:
    spl = np.full(24, -999.0)
    spl[13] = 40.0  # 1000 Hz, SPL(b) -> n = 1
    return numeric(1.0, float(ph.perceived_noisiness(spl)[13]), 1e-6, places=4)


@register(
    _AIRCRAFT,
    "ICAO Doc 9501 ETM Vol. I Table 3-7",
    "Tone correction of the turbofan example, dB",
)
def _chk_ac_tone() -> Outcome:
    return numeric(2.0, ph.tone_correction(_ETM_SPL_37), 1e-6, places=4)


@register(
    _AIRCRAFT,
    "ICAO Doc 9501 ETM Vol. I Table 4-4",
    "Integrated-method reference EPNL, EPNdB",
)
def _chk_ac_epnl() -> Outcome:
    epnl, _, _, _ = ph.epnl_from_pnlt(np.array(_ETM_PNLTR_44), np.array(_ETM_DTR_44))
    return numeric(92.61892, epnl, 1e-2, unit="EPNdB", places=3)


@register(
    _AIRCRAFT,
    "IEC 61265:1995 Table 1",
    "Directional-response tolerance at 4 kHz / 90°, dB",
)
def _chk_ac_iec61265() -> Outcome:
    from phonometry.metrology.compliance import _iec61265_directional_limit

    return numeric(2.0, _iec61265_directional_limit(4000.0, 90.0), 1e-9, unit="dB", places=1)


# ===========================================================================
# Wind-turbine noise (IEC 61400-11)
# ===========================================================================
_WIND_TURBINE = "Wind-turbine noise (IEC 61400-11)"


@register(
    _WIND_TURBINE,
    "IEC 61400-11:2012 Formula 30",
    "Critical bandwidth about a 500 Hz tone, Hz",
)
def _chk_wt_critical_bandwidth() -> Outcome:
    from phonometry.environmental.wind_turbine_noise import critical_bandwidth

    expected = 25.0 + 75.0 * (1.0 + 1.4 * (500.0 / 1000.0) ** 2) ** 0.69
    return numeric(expected, critical_bandwidth(500.0), 1e-6, unit="Hz", places=3)


@register(
    _WIND_TURBINE,
    "IEC 61400-11:2012 Formula 26",
    "Apparent sound power level of a single band, dB re 1 pW",
)
def _chk_wt_apparent_power() -> Outcome:
    r1 = 150.0
    expected = 100.0 - 6.0 + 10.0 * math.log10(4.0 * math.pi * r1**2)
    return numeric(expected, ph.apparent_sound_power_level([100.0], r1), 1e-4, unit="dB", places=4)


@register(
    _WIND_TURBINE,
    "IEC 61400-11:2012 Formulae 31-34",
    "Tonal audibility of a synthetic clean tone, dB",
)
def _chk_wt_tonal_audibility() -> Outcome:
    df = 2.0
    freqs = np.arange(440.0, 560.0 + df, df)
    levels = np.full(freqs.size, 30.0)
    levels[int(np.argmin(np.abs(freqs - 500.0)))] = 60.0
    res = ph.wind_turbine_tonality(levels, freqs)
    return numeric(16.38, res.tonal_audibility, 6e-2, unit="dB", places=2)


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
        rows = [(chk, o) for chk, o in results if chk.domain == domain]
        passed_d = sum(1 for _, o in rows if o.passed)
        total_d = len(rows)
        pct = 100.0 * passed_d / total_d if total_d else 100.0
        emoji = "&#9989;" if passed_d == total_d else "&#10060;"
        # Each domain is a collapsible group labelled with its compliance
        # percentage (100 % = every row passes). Groups with any failing row are
        # opened by default so regressions stay visible.
        opened = " open" if passed_d != total_d else ""
        domain_html = domain.replace("&", "&amp;")
        out.append(f"<details{opened}>")
        out.append(
            f"<summary>{emoji} <b>{domain_html}</b> — {pct:.0f}% "
            f"({passed_d}/{total_d})</summary>"
        )
        out.append("")
        out.append("| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |")
        out.append("|:---|:---|:---|:---|:---|:---:|")
        for chk, outcome in rows:
            out.append(
                f"| {chk.standard} | {chk.quantity} | {outcome.expected} "
                f"| {outcome.computed} | {outcome.delta} | {_status(outcome.passed)} |"
            )
        out.append("")
        out.append("</details>")
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
