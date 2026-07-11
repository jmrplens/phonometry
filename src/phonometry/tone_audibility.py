#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Objective audibility of tones in noise -- engineering method (ISO/PAS 20065:2016).

ISO/PAS 20065 is the detailed engineering method that ISO 1996-2:2017 defers to
for the audibility of prominent tones; the simplified 2007/2009 Annex C method
lives in :mod:`phonometry.environmental_measurement`. The audibility of a tone
is the amount, in decibels, by which its tone level rises above the masking
threshold of the surrounding noise.

**Critical band about the tone (Clause 5.2).** The width of the critical band
around a tone of frequency ``fT`` is
``Δfc = 25.0 + 75.0·(1.0 + 1.4·(fT/1000)²)^0.69`` Hz (Formula (2)). Assuming a
geometric placement of the corner frequencies, ``fT = √(f1·f2)`` (Formula (3)),
``f1 = −Δfc/2 + √(Δfc² + 4·fT²)/2`` (Formula (4)) and ``f2 = f1 + Δfc``
(Formula (5)).

**Audibility of a single tone (Clause 5.3).** From the mean narrow-band level
``LS`` of the masking noise (Formula (6)) the critical-band level of the masking
noise is ``LG = LS + 10·lg(Δfc/Δf)`` (Formula (12), ``Δf`` the line spacing).
The masking index is ``av = −2 − lg[1 + (f/502)²·⁵]`` dB (Formula (13)) and the
audibility of a tone of level ``LT`` (Formula (8)) is
``ΔL = LT − LG − av`` dB (Formula (14)). A tone is present when ``ΔL > 0``.

**Decisive and mean audibility (Clauses 5.3.8/5.3.9).** The decisive audibility
of one narrow-band spectrum is the largest tone audibility in it (Step 4). Over
``J`` staggered spectra the mean audibility is the energy mean
``ΔL = 10·lg[(1/J)·Σ 10^(ΔLj/10)]`` dB (Formula (20)); a spectrum in which no
tone is found contributes ``ΔLj = −10 dB`` (Formula (21)).

**From a critical-band spectrum.** :func:`mean_narrowband_level` determines
``LS`` from the lines of the critical band by the iterative procedure of
Formula (6)/Annex D (energy average, dropping any line more than 6 dB above the
running mean, with the −1.76 dB Hanning bandwidth correction), and
:func:`tone_level` sums the tonal lines contiguous with the peak for ``LT``
(Formula (8)). Both reproduce the ISO/PAS 20065 Annex E worked example
(``LS = 49.22 dB``, ``LT = 67.96 dB`` for the 137.3 Hz tone) and are confirmed
against the parent standard DIN 45681:2005-03.

**Whole-spectrum detection.** :func:`analyze_spectrum` runs the full front-end
over a spectrum — mean narrow-band level per line, peak detection (Clause 5.3.8
Step 1), tone level, the distinctness test (Clause 5.3.4) and audibility — and
returns the distinct, audible tones. :func:`combined_tone_level` performs the
multi-tone "FG" combination (Formula (17)) for tones sharing a critical band.
On the Annex E example these recover the three tones and their combined tone
level ``LT = 72.15 dB``. A decisive audibility reproduced exactly needs the
*complete* narrow-band spectrum: a spectrum truncated to one critical band
mis-estimates the mean narrow-band level of tones near its edges.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

#: Constant term of the critical bandwidth Δfc (Formula (2)), in Hz.
_DFC_CONSTANT = 25.0
#: Frequency-dependent scale of the critical bandwidth (Formula (2)), in Hz.
_DFC_SCALE = 75.0
#: Inner coefficient of the critical bandwidth (Formula (2)).
_DFC_INNER = 1.4
#: Exponent of the critical bandwidth (Formula (2)).
_DFC_EXPONENT = 0.69
#: Reference frequency of the critical bandwidth (Formula (2)), in Hz.
_DFC_REFERENCE = 1000.0

#: Reference frequency of the masking index av (Formula (13)), in Hz.
_MASKING_REFERENCE_FREQUENCY = 502.0
#: Exponent of the masking index av (Formula (13)).
_MASKING_EXPONENT = 2.5
#: Constant offset (dB) of the masking index av (Formula (13)).
_MASKING_OFFSET = 2.0

#: Effective-bandwidth factor Δfe/Δf for a Hanning window (Annex A): 1.5.
HANNING_BANDWIDTH_FACTOR = 1.5

#: Audibility (dB) assigned to a spectrum with no tone found (Formula (21)).
NO_TONE_AUDIBILITY = -10.0


def _positive(value: float, name: str) -> float:
    scalar = float(value)
    if not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"'{name}' must be a positive, finite number.")
    return scalar


def _finite(value: float, name: str) -> float:
    scalar = float(value)
    if not np.isfinite(scalar):
        raise ValueError(f"'{name}' must be finite.")
    return scalar


# --------------------------------------------------------------------------- #
# Critical band about the tone (Clause 5.2)
# --------------------------------------------------------------------------- #
def critical_bandwidth_engineering(tone_frequency: float) -> float:
    """Width ``Δfc`` of the critical band about a tone (Formula (2)).

    ``Δfc = 25.0 + 75.0·(1.0 + 1.4·(fT/1000)²)^0.69`` Hz. This is the
    continuous ISO/PAS 20065 engineering-method bandwidth, distinct from the
    stepped ISO 1996-2 Annex C :func:`~phonometry.environmental_measurement.
    critical_bandwidth` (100 Hz / 20 %).

    :param tone_frequency: Tone frequency ``fT``, in Hz.
    :return: Critical bandwidth ``Δfc``, in Hz.
    :raises ValueError: If ``tone_frequency`` is not positive/finite.
    """
    ft = _positive(tone_frequency, "tone_frequency")
    inner = 1.0 + _DFC_INNER * (ft / _DFC_REFERENCE) ** 2
    return float(_DFC_CONSTANT + _DFC_SCALE * inner**_DFC_EXPONENT)


def critical_band_corners(tone_frequency: float) -> tuple[float, float]:
    """Lower/upper corner frequencies of the critical band (Formulae (3)-(5)).

    With a geometric placement of the corners about the tone,
    ``f1 = −Δfc/2 + √(Δfc² + 4·fT²)/2`` and ``f2 = f1 + Δfc``, so that
    ``√(f1·f2) = fT`` and ``f2 − f1 = Δfc``.

    :param tone_frequency: Tone frequency ``fT``, in Hz.
    :return: ``(f1, f2)`` corner frequencies, in Hz.
    :raises ValueError: If ``tone_frequency`` is not positive/finite.
    """
    ft = _positive(tone_frequency, "tone_frequency")
    dfc = critical_bandwidth_engineering(ft)
    # Rationalised form of f1 = −Δfc/2 + √(Δfc²+4·fT²)/2: numerically stable at
    # low frequencies where Δfc ≫ fT and the direct form loses precision to the
    # subtraction of two nearly equal terms.
    f1 = 2.0 * ft**2 / (np.sqrt(dfc**2 + 4.0 * ft**2) + dfc)
    return float(f1), float(f1 + dfc)


# --------------------------------------------------------------------------- #
# Audibility of a single tone (Clause 5.3)
# --------------------------------------------------------------------------- #
def masking_index(frequency: float) -> float:
    """Masking index ``av`` of the auditory system (Formula (13)).

    ``av = −2 − lg[1 + (f/502)²·⁵]`` dB. The value is negative and grows more
    negative with frequency (see Annex C).

    :param frequency: Frequency ``f``, in Hz.
    :return: Masking index ``av``, in dB.
    :raises ValueError: If ``frequency`` is not positive/finite.
    """
    f = _positive(frequency, "frequency")
    return float(
        -_MASKING_OFFSET
        - np.log10(1.0 + (f / _MASKING_REFERENCE_FREQUENCY) ** _MASKING_EXPONENT)
    )


def critical_band_level(
    mean_narrowband_level: float, tone_frequency: float, line_spacing: float
) -> float:
    """Critical-band level ``LG`` of the masking noise (Formula (12)).

    ``LG = LS + 10·lg(Δfc/Δf)`` dB, spreading the mean narrow-band level ``LS``
    over the critical bandwidth ``Δfc`` relative to the line spacing ``Δf``.

    :param mean_narrowband_level: Mean narrow-band level ``LS``, in dB
        (Formula (6)).
    :param tone_frequency: Tone frequency ``fT``, in Hz.
    :param line_spacing: Line spacing (frequency resolution) ``Δf``, in Hz.
    :return: Critical-band level ``LG``, in dB.
    :raises ValueError: If the level is not finite or a frequency is not
        positive/finite.
    """
    ls = _finite(mean_narrowband_level, "mean_narrowband_level")
    df = _positive(line_spacing, "line_spacing")
    dfc = critical_bandwidth_engineering(tone_frequency)
    return float(ls + 10.0 * np.log10(dfc / df))


def audibility_from_levels(
    tone_level: float, critical_band_level: float, masking_index: float
) -> float:
    """Audibility ``ΔL`` from the levels and masking index (Formula (14)).

    ``ΔL = LT − LG − av`` dB.

    :param tone_level: Tone level ``LT``, in dB (Formula (8)).
    :param critical_band_level: Critical-band level ``LG`` of the masking
        noise, in dB (Formula (12)).
    :param masking_index: Masking index ``av``, in dB (Formula (13)).
    :return: Audibility ``ΔL``, in dB (dB above the masking threshold).
    :raises ValueError: If any argument is not finite.
    """
    lt = _finite(tone_level, "tone_level")
    lg = _finite(critical_band_level, "critical_band_level")
    av = _finite(masking_index, "masking_index")
    return float(lt - lg - av)


def energy_sum_level(
    line_levels: "ArrayLike",
    *,
    effective_bandwidth_factor: float = HANNING_BANDWIDTH_FACTOR,
) -> float:
    """Energy sum of the tonal spectral lines with window correction (Formula (8)).

    ``LT = 10·lg(Σ 10^(Li/10)) + 10·lg(Δf/Δfe)`` dB, the tone level from the
    ``K`` lines carrying tone energy. The window correction ``10·lg(Δf/Δfe)`` is
    ``−1.76 dB`` for a Hanning window (``Δfe = 1.5·Δf``, Annex A) and ``0 dB``
    for a rectangular window (``Δfe = Δf``). (The mean narrow-band level ``LS``
    of Formula (6) is the analogous *energy average*; :func:`mean_narrowband_level`
    and :func:`tone_level` derive ``LS`` and ``LT`` from a critical-band spectrum.)

    :param line_levels: Narrow-band levels ``Li`` of the tonal lines to sum,
        in dB.
    :param effective_bandwidth_factor: ``Δfe/Δf``; 1.5 for a Hanning window
        (the default), 1.0 for a rectangular window.
    :return: Corrected energy-sum level, in dB.
    :raises ValueError: If ``line_levels`` is empty/non-finite or the factor is
        not positive/finite.
    """
    levels = np.asarray(line_levels, dtype=np.float64)
    if levels.size == 0:
        raise ValueError("'line_levels' must contain at least one line.")
    if not np.all(np.isfinite(levels)):
        raise ValueError("'line_levels' must be finite.")
    factor = _positive(effective_bandwidth_factor, "effective_bandwidth_factor")
    total = np.sum(10.0 ** (levels / 10.0))
    return float(10.0 * np.log10(total) - 10.0 * np.log10(factor))


# --------------------------------------------------------------------------- #
# Narrow-band front-end: LS and LT from a critical-band spectrum
# (Clauses 5.3.2/5.3.3, Annex D)
# --------------------------------------------------------------------------- #
def _validate_spectrum(
    levels: "ArrayLike", frequencies: "ArrayLike"
) -> tuple["NDArray[np.float64]", "NDArray[np.float64]"]:
    """Coerce and validate a narrow-band ``(levels, frequencies)`` spectrum."""
    lev = np.asarray(levels, dtype=np.float64)
    freq = np.asarray(frequencies, dtype=np.float64)
    if lev.ndim != 1 or freq.ndim != 1:
        raise ValueError("'levels' and 'frequencies' must be one-dimensional.")
    if lev.size != freq.size:
        raise ValueError("'levels' and 'frequencies' must share their length.")
    if lev.size == 0:
        raise ValueError("'levels' and 'frequencies' must not be empty.")
    if not (np.all(np.isfinite(lev)) and np.all(np.isfinite(freq))):
        raise ValueError("'levels' and 'frequencies' must be finite.")
    if not np.all(np.diff(freq) > 0.0):
        raise ValueError("'frequencies' must be strictly increasing.")
    if freq[0] <= 0.0:
        raise ValueError("'frequencies' must be positive.")
    return lev, freq


#: Line-exclusion / tone-energy margin above the mean narrow-band level (dB).
_TONE_MARGIN = 6.0
#: Convergence tolerance of the iterative mean narrow-band level (dB).
_LS_TOLERANCE = 0.005
#: Minimum lines each side of the tone required to keep iterating (Annex D).
_LS_MIN_SIDE = 5
#: Level drop (dB) below the tone peak that bounds its tonal lines (Clause 5.3.3).
_TONE_PEAK_DROP = 10.0


def mean_narrowband_level(
    levels: "ArrayLike",
    frequencies: "ArrayLike",
    tone_frequency: float,
    *,
    effective_bandwidth_factor: float = HANNING_BANDWIDTH_FACTOR,
) -> float:
    """Mean narrow-band level ``LS`` of the masking noise (Formula (6), Annex D).

    ``LS = 10·lg[(1/M)·Σ 10^(Li/10)] + 10·lg(Δf/Δfe)`` dB, determined iteratively
    over the lines of the critical band about ``tone_frequency`` (Formulae (2)-(5)
    give the band). The line at the tone frequency is excluded; the average then
    drops any line more than ``6 dB`` above the current ``LS`` and repeats until
    ``LS`` is stable within ``±0.005 dB`` or fewer than five lines remain on
    either side of the tone (Annex D). The window correction ``10·lg(Δf/Δfe)`` is
    ``−1.76 dB`` for the recommended Hanning window (``Δfe = 1.5·Δf``).

    :param levels: Narrow-band levels ``Li`` of the spectrum, in dB.
    :param frequencies: The line frequencies, in Hz (strictly increasing).
    :param tone_frequency: Tone frequency ``fT``, in Hz.
    :param effective_bandwidth_factor: ``Δfe/Δf``; 1.5 for a Hanning window
        (the default), 1.0 for a rectangular window.
    :return: Mean narrow-band level ``LS``, in dB.
    :raises ValueError: If the spectrum is invalid, the factor is not
        positive/finite, or no lines fall in the critical band.
    """
    lev, freq = _validate_spectrum(levels, frequencies)
    ft = _positive(tone_frequency, "tone_frequency")
    factor = _positive(effective_bandwidth_factor, "effective_bandwidth_factor")
    correction = 10.0 * np.log10(factor)

    f1, f2 = critical_band_corners(ft)
    under = int(np.argmin(np.abs(freq - ft)))
    band = [
        i for i in range(lev.size) if f1 <= freq[i] <= f2 and i != under
    ]
    if not band:
        raise ValueError("No spectral lines fall in the critical band.")

    def _ls(indices: list[int]) -> float:
        return float(
            10.0 * np.log10(np.mean(10.0 ** (lev[indices] / 10.0))) - correction
        )

    kept = band
    ls = _ls(kept)
    for _ in range(200):
        pruned = [i for i in kept if lev[i] <= ls + _TONE_MARGIN]
        left = sum(1 for i in pruned if i < under)
        right = sum(1 for i in pruned if i > under)
        if left < _LS_MIN_SIDE or right < _LS_MIN_SIDE or pruned == kept:
            break
        kept = pruned
        new_ls = _ls(kept)
        if abs(new_ls - ls) <= _LS_TOLERANCE:
            ls = new_ls
            break
        ls = new_ls
    return ls


def tone_level(
    levels: "ArrayLike",
    frequencies: "ArrayLike",
    tone_frequency: float,
    mean_narrowband_level: float,
    *,
    effective_bandwidth_factor: float = HANNING_BANDWIDTH_FACTOR,
) -> float:
    """Tone level ``LT`` from the tonal lines about a tone (Formula (8)).

    The tone energy is carried by the run of lines contiguous with the peak at
    ``tone_frequency`` whose level stays above both ``LS + 6 dB`` and
    ``L_peak − 10 dB`` (Clause 5.3.3); their energy sum with the window
    correction is ``LT`` (via :func:`energy_sum_level`).

    :param levels: Narrow-band levels ``Li`` of the spectrum, in dB.
    :param frequencies: The line frequencies, in Hz (strictly increasing).
    :param tone_frequency: Tone frequency ``fT`` (the peak), in Hz.
    :param mean_narrowband_level: Mean narrow-band level ``LS`` of the masking
        noise, in dB (see :func:`mean_narrowband_level`).
    :param effective_bandwidth_factor: ``Δfe/Δf``; 1.5 for a Hanning window
        (the default), 1.0 for a rectangular window.
    :return: Tone level ``LT``, in dB.
    :raises ValueError: If the spectrum is invalid or the levels are not finite.
    """
    lev, freq = _validate_spectrum(levels, frequencies)
    ft = _positive(tone_frequency, "tone_frequency")
    ls = _finite(mean_narrowband_level, "mean_narrowband_level")
    peak = int(np.argmin(np.abs(freq - ft)))
    threshold = max(ls + _TONE_MARGIN, lev[peak] - _TONE_PEAK_DROP)

    low = peak
    while low - 1 >= 0 and lev[low - 1] > threshold:
        low -= 1
    high = peak
    while high + 1 < lev.size and lev[high + 1] > threshold:
        high += 1
    return energy_sum_level(
        lev[low : high + 1], effective_bandwidth_factor=effective_bandwidth_factor
    )


# --------------------------------------------------------------------------- #
# Full-spectrum tone detection (Clause 5.3.8 Steps 1-3, distinctness 5.3.4)
# --------------------------------------------------------------------------- #
#: Max tone bandwidth ΔfR = 26·(1 + 0.001·fT) Hz for distinctness (Formula (9)).
_DISTINCT_BW_CONSTANT = 26.0
_DISTINCT_BW_SLOPE = 0.001
#: Minimum edge steepness of a distinct tone, in dB/octave (Formulae (10)/(11)).
_DISTINCT_EDGE_STEEPNESS = 24.0


def _tone_line_span(lev: "NDArray[np.float64]", peak: int, ls: float) -> tuple[int, int]:
    """Contiguous run of tonal lines about ``peak`` (levels above LS+6, peak−10)."""
    threshold = max(ls + _TONE_MARGIN, lev[peak] - _TONE_PEAK_DROP)
    low = peak
    while low - 1 >= 0 and lev[low - 1] > threshold:
        low -= 1
    high = peak
    while high + 1 < lev.size and lev[high + 1] > threshold:
        high += 1
    return low, high


def _is_distinct(
    lev: "NDArray[np.float64]",
    freq: "NDArray[np.float64]",
    peak: int,
    low: int,
    high: int,
    line_spacing: float,
) -> bool:
    """Distinctness test: bandwidth (Formula (9)) and edge steepness (10)/(11)."""
    n_lines = high - low + 1
    max_bandwidth = _DISTINCT_BW_CONSTANT * (1.0 + _DISTINCT_BW_SLOPE * freq[peak])
    if n_lines * line_spacing > max_bandwidth:
        return False
    ft = freq[peak]
    if low - 1 >= 0:
        lower = ft * (lev[peak] - lev[low - 1]) / (
            np.sqrt(2.0) * (ft - freq[low - 1])
        )
        if lower < _DISTINCT_EDGE_STEEPNESS:
            return False
    if high + 1 < lev.size:
        upper = ft * (lev[peak] - lev[high + 1]) / (
            np.sqrt(2.0) * (freq[high + 1] - ft)
        )
        if upper < _DISTINCT_EDGE_STEEPNESS:
            return False
    return True


def _detect_tones(
    lev: "NDArray[np.float64]",
    freq: "NDArray[np.float64]",
    line_spacing: float,
    factor: float,
) -> list[tuple[int, int, int, float]]:
    """Detect distinct tone peaks (Clause 5.3.8 Steps 1-2, 5.3.4).

    Returns ``(peak, low, high, LS)`` records: a local maximum that rises more
    than 6 dB above its mean narrow-band level, whose tonal-line run passes the
    distinctness criteria. The search resumes past each tone's line run so that
    secondary maxima inside a tone are absorbed, not double-counted.
    """
    n = lev.size
    tones: list[tuple[int, int, int, float]] = []

    def _ls_at(index: int) -> float | None:
        """LS at a line, or None if its critical band holds no other line."""
        try:
            return mean_narrowband_level(
                lev, freq, float(freq[index]), effective_bandwidth_factor=factor
            )
        except ValueError:
            return None

    i = 0
    while i < n - 1:
        # Advance off any flank to a local maximum (a tone cannot sit on a slope).
        # ``i > 0`` guards the left neighbour so line 0 is not compared against
        # the wrapped-around last line of the spectrum.
        while i < n - 1 and (
            lev[i + 1] > lev[i] or (i > 0 and lev[i - 1] > lev[i])
        ):
            i += 1
        peak = i
        ls = _ls_at(peak)
        if ls is None:
            i += 1
            continue
        # Extend over the run above LS+6, tracking the strongest line as the peak.
        j = i
        while j < n and lev[j] > ls + _TONE_MARGIN:
            if lev[j] > lev[peak]:
                peak = j
            j += 1
        resume = j
        if lev[peak] > ls + _TONE_MARGIN:
            if peak != i:
                recomputed = _ls_at(peak)
                if recomputed is None:
                    i = max(resume, i + 1)
                    continue
                ls = recomputed
            low, high = _tone_line_span(lev, peak, ls)
            if _is_distinct(lev, freq, peak, low, high, line_spacing):
                tones.append((peak, low, high, ls))
        i = max(resume, i + 1)
    return tones


def analyze_spectrum(
    levels: "ArrayLike",
    frequencies: "ArrayLike",
    line_spacing: float,
    *,
    effective_bandwidth_factor: float = HANNING_BANDWIDTH_FACTOR,
) -> ToneAudibilityResult:
    """Detect and rate the audible tones of a narrow-band spectrum (Clause 5.3.8).

    Runs the full front-end: the mean narrow-band level (Formula (6)) per line,
    peak detection (Step 1), the tone level (Formula (8)), the distinctness test
    (Clause 5.3.4) and the audibility (Formula (14)). Only distinct tones with a
    positive audibility are returned, bundled by :func:`assess_tones`.

    The multi-tone "FG" combination (Formula (17)) is provided separately by
    :func:`combined_tone_level`. Reproducing a decisive audibility exactly
    requires the *complete* narrow-band spectrum — a spectrum truncated to a
    single critical band gives the wrong mean narrow-band level for tones near
    its edges.

    :param levels: Narrow-band levels ``Li`` of the spectrum, in dB.
    :param frequencies: The line frequencies, in Hz (strictly increasing).
    :param line_spacing: Line spacing (frequency resolution) ``Δf``, in Hz.
    :param effective_bandwidth_factor: ``Δfe/Δf``; 1.5 for a Hanning window
        (the default), 1.0 for a rectangular window.
    :return: A :class:`ToneAudibilityResult` of the detected audible tones.
    :raises ValueError: If the spectrum is invalid or no audible tone is found.
    """
    lev, freq = _validate_spectrum(levels, frequencies)
    df = _positive(line_spacing, "line_spacing")
    factor = _positive(effective_bandwidth_factor, "effective_bandwidth_factor")
    detected = _detect_tones(lev, freq, df, factor)

    tones = []
    for peak, low, high, ls in detected:
        lt = energy_sum_level(
            lev[low : high + 1], effective_bandwidth_factor=factor
        )
        if tone_audibility(lt, ls, float(freq[peak]), df) > 0.0:
            tones.append((float(freq[peak]), lt, ls))
    if not tones:
        raise ValueError("No audible tone was detected in the spectrum.")
    return assess_tones(
        [t[0] for t in tones],
        [t[1] for t in tones],
        [t[2] for t in tones],
        df,
    )


def combined_tone_level(
    levels: "ArrayLike",
    frequencies: "ArrayLike",
    tone_frequencies: "ArrayLike",
    mean_narrowband_levels: "ArrayLike",
    *,
    effective_bandwidth_factor: float = HANNING_BANDWIDTH_FACTOR,
) -> float:
    """Combined tone level ``LT`` of several tones in one critical band (Formula (17)).

    ``LTm = 10·lg(Σ 10^(LTm,n/10))`` — the energy sum of the tonal lines of all
    the tones, each spectral line counted at most once. Use it when more than one
    audible tone falls in a critical band (Clause 5.3.8 Step 3); the group is
    then rated at the frequency of its most audible tone.

    :param levels: Narrow-band levels ``Li`` of the spectrum, in dB.
    :param frequencies: The line frequencies, in Hz (strictly increasing).
    :param tone_frequencies: The tone frequencies sharing the critical band, Hz.
    :param mean_narrowband_levels: Each tone's mean narrow-band level ``LS``, dB
        (same length as ``tone_frequencies``).
    :param effective_bandwidth_factor: ``Δfe/Δf``; 1.5 for a Hanning window.
    :return: Combined tone level ``LT``, in dB.
    :raises ValueError: If the inputs are invalid or differ in length.
    """
    lev, freq = _validate_spectrum(levels, frequencies)
    fts = np.asarray(tone_frequencies, dtype=np.float64)
    lss = np.asarray(mean_narrowband_levels, dtype=np.float64)
    if fts.ndim != 1 or lss.ndim != 1 or fts.size != lss.size:
        raise ValueError(
            "'tone_frequencies' and 'mean_narrowband_levels' must be "
            "one-dimensional and share their length."
        )
    if fts.size == 0:
        raise ValueError("At least one tone is required.")
    marked: set[int] = set()
    for ft, ls in zip(fts, lss):
        peak = int(np.argmin(np.abs(freq - ft)))
        low, high = _tone_line_span(lev, peak, float(ls))
        marked.update(range(low, high + 1))
    return energy_sum_level(
        lev[sorted(marked)], effective_bandwidth_factor=effective_bandwidth_factor
    )


# --------------------------------------------------------------------------- #
# Decisive and mean audibility (Clauses 5.3.8/5.3.9)
# --------------------------------------------------------------------------- #
def mean_audibility(decisive_audibilities: "ArrayLike") -> float:
    """Mean audibility ``ΔL`` over a number of spectra (Formula (20)).

    ``ΔL = 10·lg[(1/J)·Σ 10^(ΔLj/10)]`` dB, the energy mean of the decisive
    audibilities ``ΔLj`` of the ``J`` staggered narrow-band spectra. A spectrum
    with no tone found contributes ``ΔLj = −10 dB`` (Formula (21)); pass that
    value explicitly for such spectra.

    :param decisive_audibilities: Decisive audibilities ``ΔLj`` of the spectra,
        in dB.
    :return: Mean audibility ``ΔL``, in dB.
    :raises ValueError: If the input is empty or non-finite.
    """
    deltas = np.asarray(decisive_audibilities, dtype=np.float64)
    if deltas.size == 0:
        raise ValueError("'decisive_audibilities' must not be empty.")
    if not np.all(np.isfinite(deltas)):
        raise ValueError("'decisive_audibilities' must be finite.")
    return float(10.0 * np.log10(np.mean(10.0 ** (deltas / 10.0))))


# --------------------------------------------------------------------------- #
# Result
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ToneAudibilityResult:
    """Audibility of the tones of a narrow-band spectrum (ISO/PAS 20065).

    :ivar tone_frequencies: Tone frequencies ``fT``, in Hz.
    :ivar tone_levels: Tone levels ``LT``, in dB (Formula (8)).
    :ivar mean_narrowband_levels: Mean narrow-band levels ``LS`` of the masking
        noise, in dB (Formula (6)).
    :ivar line_spacing: Line spacing (frequency resolution) ``Δf``, in Hz.
    :ivar critical_bandwidths: Critical bandwidths ``Δfc``, in Hz (Formula (2)).
    :ivar lower_corners: Lower corner frequencies ``f1``, in Hz (Formula (4)).
    :ivar upper_corners: Upper corner frequencies ``f2``, in Hz (Formula (5)).
    :ivar critical_band_levels: Critical-band levels ``LG`` of the masking
        noise, in dB (Formula (12)).
    :ivar masking_indices: Masking indices ``av``, in dB (Formula (13)).
    :ivar audibilities: Audibilities ``ΔL``, in dB (Formula (14)).
    """

    tone_frequencies: "NDArray[np.float64]"
    tone_levels: "NDArray[np.float64]"
    mean_narrowband_levels: "NDArray[np.float64]"
    line_spacing: float
    critical_bandwidths: "NDArray[np.float64]"
    lower_corners: "NDArray[np.float64]"
    upper_corners: "NDArray[np.float64]"
    critical_band_levels: "NDArray[np.float64]"
    masking_indices: "NDArray[np.float64]"
    audibilities: "NDArray[np.float64]"

    @property
    def audible(self) -> "NDArray[np.bool_]":
        """Boolean mask of tones that are present, i.e. ``ΔL > 0`` (Step 2)."""
        return self.audibilities > 0.0

    @property
    def decisive_audibility(self) -> float:
        """Decisive audibility ``ΔLj`` of the spectrum: the largest ``ΔL`` (Step 4)."""
        return float(np.max(self.audibilities))

    @property
    def decisive_frequency(self) -> float:
        """Tone frequency of the decisive (most audible) tone, in Hz."""
        return float(self.tone_frequencies[int(np.argmax(self.audibilities))])

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the per-tone audibility ``ΔL`` against tone frequency."""
        from ._plotting import plot_tone_audibility

        return plot_tone_audibility(self, ax=ax, **kwargs)


# Module named ``tone_audibility`` (distinct from the ISO 1996-2 Annex C
# ``tonal_audibility`` in :mod:`phonometry.environmental_measurement`).


def tone_audibility(
    tone_level: float,
    mean_narrowband_level: float,
    tone_frequency: float,
    line_spacing: float,
) -> float:
    """Audibility ``ΔL`` of one tone from its levels (Formulae (12)-(14)).

    Chains the critical-band level ``LG`` (Formula (12)), the masking index
    ``av`` (Formula (13)) and the audibility ``ΔL = LT − LG − av``
    (Formula (14)) for a single tone.

    :param tone_level: Tone level ``LT``, in dB (Formula (8)).
    :param mean_narrowband_level: Mean narrow-band level ``LS`` of the masking
        noise, in dB (Formula (6)).
    :param tone_frequency: Tone frequency ``fT``, in Hz.
    :param line_spacing: Line spacing (frequency resolution) ``Δf``, in Hz.
    :return: Audibility ``ΔL``, in dB.
    :raises ValueError: If the levels are not finite or a frequency/spacing is
        not positive/finite.
    """
    lg = critical_band_level(mean_narrowband_level, tone_frequency, line_spacing)
    av = masking_index(tone_frequency)
    return audibility_from_levels(tone_level, lg, av)


def assess_tones(
    tone_frequencies: "ArrayLike",
    tone_levels: "ArrayLike",
    mean_narrowband_levels: "ArrayLike",
    line_spacing: float,
) -> ToneAudibilityResult:
    """Assess the audibility of the tones of a narrow-band spectrum.

    Applies the critical band (Formulae (2)-(5)), critical-band level
    (Formula (12)), masking index (Formula (13)) and audibility (Formula (14))
    to every tone and bundles them into a plottable :class:`ToneAudibilityResult`.

    :param tone_frequencies: Tone frequencies ``fT``, in Hz.
    :param tone_levels: Tone levels ``LT``, in dB (Formula (8)).
    :param mean_narrowband_levels: Mean narrow-band levels ``LS`` of the masking
        noise, in dB (Formula (6)).
    :param line_spacing: Line spacing (frequency resolution) ``Δf``, in Hz.
    :return: A :class:`ToneAudibilityResult`.
    :raises ValueError: If the arrays are empty, differ in length, or contain
        non-finite/non-positive values.
    """
    freqs = np.asarray(tone_frequencies, dtype=np.float64)
    lt = np.asarray(tone_levels, dtype=np.float64)
    ls = np.asarray(mean_narrowband_levels, dtype=np.float64)
    df = _positive(line_spacing, "line_spacing")
    if freqs.ndim != 1 or lt.ndim != 1 or ls.ndim != 1:
        raise ValueError(
            "'tone_frequencies', 'tone_levels' and 'mean_narrowband_levels' "
            "must be one-dimensional."
        )
    if not (freqs.size == lt.size == ls.size):
        raise ValueError(
            "'tone_frequencies', 'tone_levels' and 'mean_narrowband_levels' "
            "must share their length."
        )
    if freqs.size == 0:
        raise ValueError("At least one tone is required.")
    if not (np.all(np.isfinite(freqs)) and np.all(freqs > 0.0)):
        raise ValueError("'tone_frequencies' must be positive and finite.")
    if not (np.all(np.isfinite(lt)) and np.all(np.isfinite(ls))):
        raise ValueError(
            "'tone_levels' and 'mean_narrowband_levels' must be finite."
        )

    dfc = np.array([critical_bandwidth_engineering(f) for f in freqs])
    # Corner frequencies (Formulae 4/5) from the already-computed Δfc, in the
    # numerically stable form (see critical_band_corners).
    f1 = 2.0 * freqs**2 / (np.sqrt(dfc**2 + 4.0 * freqs**2) + dfc)
    f2 = f1 + dfc
    lg = ls + 10.0 * np.log10(dfc / df)
    av = np.array([masking_index(f) for f in freqs])
    delta = lt - lg - av
    return ToneAudibilityResult(
        tone_frequencies=freqs,
        tone_levels=lt,
        mean_narrowband_levels=ls,
        line_spacing=df,
        critical_bandwidths=dfc,
        lower_corners=f1,
        upper_corners=f2,
        critical_band_levels=lg,
        masking_indices=av,
        audibilities=delta,
    )
