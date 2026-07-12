#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Wind-turbine acoustic noise (IEC 61400-11:2012+A1:2018).

Two closed-form quantities of the standard:

* :func:`apparent_sound_power_level` -- the A-weighted apparent sound power
  level ``L_WA`` referred to the equivalent point source at the rotor centre,
  from the ground-board sound pressure level and the slant distance
  (:func:`slant_distance`), ``L_WA = L_p − 6 + 10·lg(4π R1²/S0)`` (Formula 26).
* :func:`wind_turbine_tonality` -- the tonal-audibility chain (Formulae 30-34):
  the critical bandwidth (:func:`critical_bandwidth`), the masking-noise level,
  the tonality and the audibility criterion, giving the tonal audibility
  ``ΔL_a`` that decides whether a tone is audible.

The tonal-audibility formula itself is the ISO 1996-2 Annex C one already in
:mod:`phonometry.environmental_measurement`; what is specific to IEC 61400-11 is
how the tone and masking-noise levels and the (Zwicker) critical band are
determined from the narrowband spectrum. The rating adjustment ``K_T`` is the
ISO 1996-2 :func:`~phonometry.environmental_measurement.tonal_adjustment`. The
full measurement pipeline (binning, regression to standardised wind speeds,
uncertainty budgets) is out of scope; these are the underlying closed forms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import NDArray

#: Reference area ``S0`` for the apparent sound power level (m²).
_REFERENCE_AREA = 1.0
#: The apparent-sound-power ground-board pressure-doubling term (dB).
_BOARD_TERM = 6.0
#: Effective-noise-bandwidth Hanning factor (× frequency resolution).
_HANNING_ENBW_FACTOR = 1.5
#: Low-frequency band where the critical band is fixed to 20-120 Hz.
_LOW_FREQ_MIN, _LOW_FREQ_MAX = 20.0, 70.0
_LOW_FREQ_BANDWIDTH = 100.0


def _positive(value: float, name: str) -> float:
    scalar = float(value)
    if not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"'{name}' must be a positive, finite number.")
    return scalar


def slant_distance(hub_height: float, rotor_diameter: float) -> float:
    """Slant distance ``R1`` from the rotor centre to the ground microphone.

    With the reference microphone on the ground at the horizontal distance
    ``R0 = H + D/2`` (IEC 61400-11 Formula 1) and the rotor centre at height
    ``H``, the slant distance is ``R1 = sqrt(H² + R0²)``.

    :param hub_height: Hub height ``H`` (ground to rotor centre), in m.
    :param rotor_diameter: Rotor diameter ``D``, in m.
    :return: The slant distance ``R1``, in m.
    :raises ValueError: If a dimension is not positive.
    """
    h = _positive(hub_height, "hub_height")
    d = _positive(rotor_diameter, "rotor_diameter")
    r0 = h + d / 2.0
    return float(np.hypot(h, r0))


def apparent_sound_power_level(
    band_levels: "float | NDArray[np.float64] | list[float]", r1: float
) -> float:
    """A-weighted apparent sound power level ``L_WA`` (IEC 61400-11 Formula 26).

    ``L_WA,i = L_p,i − 6 + 10·lg(4π R1²/S0)`` per one-third-octave band, energy
    summed over bands (Formula 27). The ``−6 dB`` accounts for the ground-board
    pressure doubling; ``S0 = 1 m²``.

    :param band_levels: Background-corrected A-weighted band sound pressure
        levels ``L_p,i``, in dB (scalar or per band).
    :param r1: Slant distance ``R1`` to the rotor centre, in m.
    :return: The apparent sound power level ``L_WA``, in dB re 1 pW.
    :raises ValueError: If the inputs are invalid.
    """
    levels = np.atleast_1d(np.asarray(band_levels, dtype=np.float64))
    if levels.size == 0 or not np.all(np.isfinite(levels)):
        raise ValueError("'band_levels' must be finite and non-empty.")
    r = _positive(r1, "r1")
    geometry = 10.0 * np.log10(4.0 * np.pi * r**2 / _REFERENCE_AREA)
    lwa_bands = levels - _BOARD_TERM + geometry
    return float(10.0 * np.log10(np.sum(10.0 ** (lwa_bands / 10.0))))


def critical_bandwidth(fc: float) -> float:
    """Critical bandwidth about a tone (IEC 61400-11 Formula 30), in Hz.

    ``CBW = 25 + 75·[1 + 1.4·(fc/1000)²]^0.69``. For a candidate tone in the
    20-70 Hz range the critical band is fixed to 20-120 Hz (100 Hz wide),
    per subclause 9.5.3.

    :param fc: Tone (local-maximum) frequency, in Hz.
    :return: The critical bandwidth, in Hz.
    :raises ValueError: If the frequency is not positive.
    """
    f = _positive(fc, "fc")
    if _LOW_FREQ_MIN <= f <= _LOW_FREQ_MAX:
        return _LOW_FREQ_BANDWIDTH
    return float(25.0 + 75.0 * (1.0 + 1.4 * (f / 1000.0) ** 2) ** 0.69)


def _critical_band_edges(fc: float) -> "tuple[float, float]":
    """Lower and upper edges of the critical band about a tone (Hz).

    For a candidate tone in the 20-70 Hz range the band is the fixed absolute
    20-120 Hz band (subclause 9.5.3), not one centred on ``fc``; otherwise it is
    the Zwicker critical band ``fc ± CBW/2``.
    """
    f = _positive(fc, "fc")
    if _LOW_FREQ_MIN <= f <= _LOW_FREQ_MAX:
        return _LOW_FREQ_MIN, _LOW_FREQ_MIN + _LOW_FREQ_BANDWIDTH
    cbw = critical_bandwidth(f)
    return f - cbw / 2.0, f + cbw / 2.0


def _energy_mean(levels_db: "NDArray[np.float64]") -> float:
    return float(10.0 * np.log10(np.mean(10.0 ** (levels_db / 10.0))))


#: Tone-classification margins (dB): masking-line criterion and tone criterion.
_MASKING_MARGIN = 6.0
_TONE_MARGIN = 6.0
#: A tone line stays grouped with the peak while within this level of it (dB).
_TONE_GROUP_DROP = 10.0
#: Audibility criterion constants of Formula 34.
_LA_OFFSET, _LA_PIVOT, _LA_EXP = -2.0, 502.0, 2.5


@dataclass(frozen=True)
class WindTurbineTonalityResult:
    """Tonal audibility of a narrowband spectrum (IEC 61400-11).

    :ivar tone_frequency: The candidate tone frequency, in Hz.
    :ivar critical_bandwidth: The critical bandwidth about the tone, in Hz.
    :ivar tone_level: Tone level ``L_pt`` (energy sum of the tone lines), in dB.
    :ivar masking_level: Masking-noise level ``L_pn``, in dB.
    :ivar tonality: Tonality ``ΔL_tn = L_pt − L_pn``, in dB.
    :ivar audibility_criterion: The criterion ``L_a`` (Formula 34), in dB.
    :ivar tonal_audibility: Tonal audibility ``ΔL_a = ΔL_tn − L_a``, in dB.
    :ivar is_audible: Whether the tone is audible (``ΔL_a > 0``).
    :ivar frequencies: The narrowband line frequencies, in Hz.
    :ivar levels: The narrowband line levels, in dB.
    """

    tone_frequency: float
    critical_bandwidth: float
    tone_level: float
    masking_level: float
    tonality: float
    audibility_criterion: float
    tonal_audibility: float
    is_audible: bool
    frequencies: "NDArray[np.float64]"
    levels: "NDArray[np.float64]"

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the narrowband spectrum with the critical band and masking level."""
        from ._plotting import plot_wind_turbine_tonality

        return plot_wind_turbine_tonality(self, ax=ax, **kwargs)


def wind_turbine_tonality(
    levels: "NDArray[np.float64] | list[float]",
    frequencies: "NDArray[np.float64] | list[float]",
    *,
    tone_frequency: "float | None" = None,
) -> WindTurbineTonalityResult:
    """Tonal audibility of a narrowband spectrum (IEC 61400-11 Formulae 30-34).

    From a uniformly-spaced narrowband spectrum, classifies the lines in the
    critical band about the candidate tone into masking noise and tone lines,
    forms the masking-noise level ``L_pn`` (Formula 31), the tonality
    ``ΔL_tn = L_pt − L_pn`` (Formula 32), the audibility criterion ``L_a``
    (Formula 34) and the tonal audibility ``ΔL_a = ΔL_tn − L_a`` (Formula 33).

    :param levels: Narrowband line levels, in dB (A-weighted, 1-2 Hz resolution).
    :param frequencies: Line frequencies, in Hz (uniform spacing).
    :param tone_frequency: Candidate tone frequency, in Hz; if ``None`` the
        highest-level line is used.
    :return: A :class:`WindTurbineTonalityResult`.
    :raises ValueError: If the inputs are invalid.
    """
    lv = np.asarray(levels, dtype=np.float64)
    fr = np.asarray(frequencies, dtype=np.float64)
    if lv.ndim != 1 or lv.shape != fr.shape or lv.size < 3:
        raise ValueError("'levels' and 'frequencies' must be 1-D and the same length (>= 3).")
    if not (np.all(np.isfinite(lv)) and np.all(np.isfinite(fr))):
        raise ValueError("'levels' and 'frequencies' must be finite.")
    diffs = np.diff(fr)
    if np.any(diffs <= 0.0):
        raise ValueError("'frequencies' must be strictly increasing.")
    df = float(np.median(diffs))
    if np.any(np.abs(diffs - df) > 1e-3 * df):
        raise ValueError("'frequencies' must be uniformly spaced (a narrowband spectrum).")

    peak = int(np.argmax(lv)) if tone_frequency is None else int(np.argmin(np.abs(fr - tone_frequency)))
    fc = float(fr[peak])
    cbw = critical_bandwidth(fc)
    lo, hi = _critical_band_edges(fc)
    in_band = (fr >= lo) & (fr <= hi)
    band = lv[in_band]

    # L_70%: energy mean of the 70 % lowest-level lines in the critical band.
    n_low = max(1, int(round(0.7 * band.size)))
    l70 = _energy_mean(np.sort(band)[:n_low])
    masking = band[band < l70 + _MASKING_MARGIN]
    l_pn_avg = _energy_mean(masking) if masking.size else l70
    tone_threshold = l_pn_avg + _TONE_MARGIN

    # Tone lines (9.5.3, "adjacent" struck out by A1:2018): every line in the
    # critical band above the tone threshold and within 10 dB of the peak,
    # whether or not contiguous with it.
    peak_level = float(lv[peak])
    is_tone = in_band & (lv > tone_threshold) & (peak_level - lv <= _TONE_GROUP_DROP)
    tone_positions = np.nonzero(is_tone)[0]
    if tone_positions.size == 0:
        tone_positions = np.array([peak])
    # Energy-sum the tone lines per contiguous run (9.5.5), applying the Hanning
    # ÷1.5 correction to any run that spans two or more adjacent lines.
    runs = np.split(tone_positions, np.nonzero(np.diff(tone_positions) != 1)[0] + 1)
    tone_energy = 0.0
    for run in runs:
        run_energy = float(np.sum(10.0 ** (lv[run] / 10.0)))
        if run.size >= 2:
            run_energy /= _HANNING_ENBW_FACTOR
        tone_energy += run_energy
    l_pt = 10.0 * np.log10(tone_energy)

    enbw = _HANNING_ENBW_FACTOR * df
    l_pn = l_pn_avg + 10.0 * np.log10(cbw / enbw)
    tonality = l_pt - l_pn
    l_a = _LA_OFFSET - np.log10(1.0 + (fc / _LA_PIVOT) ** _LA_EXP)
    delta_la = float(tonality - l_a)

    return WindTurbineTonalityResult(
        tone_frequency=fc,
        critical_bandwidth=cbw,
        tone_level=float(l_pt),
        masking_level=float(l_pn),
        tonality=float(tonality),
        audibility_criterion=float(l_a),
        tonal_audibility=delta_la,
        is_audible=bool(delta_la > 0.0),
        frequencies=fr,
        levels=lv,
    )
