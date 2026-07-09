#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Speech Intelligibility Index (SII) per ANSI S3.5-1997 (R2017).

Implements the one-third-octave-band method (18 bands, 160 Hz - 8000 Hz) of
ANSI S3.5-1997, *American National Standard Methods for the Calculation of the
Speech Intelligibility Index*. From an equivalent speech spectrum level, an
equivalent noise spectrum level and an equivalent hearing threshold, the
procedure forms the self-speech masking, the upward spread of masking, the
equivalent internal noise and disturbance, the level-distortion factor and the
band-audibility function, and weights the latter by the band-importance function
of Table 3 to give the index ``SII`` in [0, 1] (clause 6).

The band-importance function (Table 3, average speech material), the standard
speech spectrum levels by vocal effort (Table 3) and the reference internal
noise spectrum level (Table 3) are the standard's own tabulated constants.
Spectrum levels are as defined in clauses 3.11 and 3.55.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

from numpy.typing import ArrayLike

# ---------------------------------------------------------------------------
# Normative constants - ANSI S3.5-1997, one-third-octave-band method (Table 3).
# ---------------------------------------------------------------------------

#: One-third-octave band centre frequencies, in hertz (18 bands, Table 3).
BAND_CENTRES: np.ndarray = np.array(
    [160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0,
     1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0],
    dtype=np.float64,
)

#: Band-importance function ``Ii`` (Table 3, average speech material); sums to 1.
BAND_IMPORTANCE: np.ndarray = np.array(
    [0.0083, 0.0095, 0.0150, 0.0289, 0.0440, 0.0578, 0.0653, 0.0711, 0.0818,
     0.0844, 0.0882, 0.0898, 0.0868, 0.0844, 0.0771, 0.0527, 0.0364, 0.0185],
    dtype=np.float64,
)

#: Standard speech spectrum level ``Ui``, normal vocal effort (Table 3), dB SPL.
_SPEECH_NORMAL: np.ndarray = np.array(
    [32.41, 34.48, 34.75, 33.98, 34.59, 34.27, 32.06, 28.30, 25.01, 23.00,
     20.15, 17.32, 13.18, 11.55, 9.33, 5.31, 2.59, 1.13],
    dtype=np.float64,
)

#: Standard speech spectra by vocal effort (Table 3). Only the normal-effort
#: spectrum is currently included; the raised/loud/shout spectra are pending
#: transcription against a verified copy of Table 3.
_SPEECH_SPECTRA: dict[str, np.ndarray] = {
    "normal": _SPEECH_NORMAL,
}

#: Reference internal noise spectrum level ``Xi`` (Table 3), dB SPL.
REFERENCE_INTERNAL_NOISE: np.ndarray = np.array(
    [0.6, -1.7, -3.9, -6.1, -8.2, -9.7, -10.8, -11.9, -12.5, -13.5, -15.4,
     -17.7, -21.2, -24.2, -25.9, -23.6, -15.8, -7.1],
    dtype=np.float64,
)

_N_BANDS = BAND_CENTRES.size
VOCAL_EFFORTS: tuple[str, ...] = ("normal",)


@dataclass(frozen=True)
class SIIResult:
    """Result of a Speech Intelligibility Index computation (ANSI S3.5-1997).

    :ivar sii: The overall Speech Intelligibility Index in [0, 1] (clause 6).
    :ivar band_audibility: Per-band audibility function ``Ai`` (clause 5.8).
    :ivar band_importance: Per-band importance function ``Ii`` used (Table 3).
    :ivar frequencies: One-third-octave band centre frequencies, in hertz.
    :ivar speech_spectrum: Equivalent speech spectrum level ``Ei'`` per band.
    :ivar disturbance: Equivalent disturbance spectrum level ``Di`` (clause 5.6).
    :ivar masking: Equivalent masking spectrum level ``Zi`` (clause 5.4).
    """

    sii: float
    band_audibility: np.ndarray
    band_importance: np.ndarray
    frequencies: np.ndarray
    speech_spectrum: np.ndarray
    disturbance: np.ndarray
    masking: np.ndarray

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the per-band audibility weighted by importance, with the SII.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ._plotting import plot_sii

        return plot_sii(self, ax=ax, **kwargs)


def standard_speech_spectrum(vocal_effort: str = "normal") -> np.ndarray:
    """Standard speech spectrum level by vocal effort (ANSI S3.5-1997 Table 3).

    :param vocal_effort: One of ``"normal"``, ``"raised"``, ``"loud"``,
        ``"shout"``.
    :return: The 18-band equivalent speech spectrum level ``Ui``, in dB SPL.
    :raises ValueError: for an unknown vocal effort.
    """
    try:
        return _SPEECH_SPECTRA[vocal_effort].copy()
    except KeyError:
        raise ValueError(
            f"Unknown vocal_effort {vocal_effort!r}; choose from "
            f"{', '.join(VOCAL_EFFORTS)}."
        ) from None


def _as_band_vector(values: ArrayLike, name: str) -> np.ndarray:
    """Validate and return a length-18 one-third-octave band vector."""
    arr = np.atleast_1d(np.asarray(values, dtype=np.float64))
    if arr.ndim != 1 or arr.size != _N_BANDS:
        raise ValueError(
            f"{name!r} must be a 1-D vector of {_N_BANDS} one-third-octave "
            f"band values (160 Hz - 8000 Hz); got shape {arr.shape}."
        )
    return arr


def speech_intelligibility_index(
    speech_spectrum: ArrayLike,
    noise_spectrum: ArrayLike | None = None,
    *,
    threshold: ArrayLike | None = None,
) -> SIIResult:
    """Speech Intelligibility Index (ANSI S3.5-1997, one-third-octave method).

    All spectra are equivalent spectrum levels (clauses 3.11/3.55) sampled at
    the 18 one-third-octave band centres from 160 Hz to 8000 Hz.

    :param speech_spectrum: Equivalent speech spectrum level ``Ei'``, in dB SPL.
        The vocal-effort name ``"normal"`` selects the standard normal-effort
        spectrum (Table 3).
    :param noise_spectrum: Equivalent noise spectrum level ``Ni'``, in dB SPL;
        ``None`` uses a quiet field (``-80`` dB in every band).
    :param threshold: Equivalent hearing threshold ``Ti'``, in dB HL; ``None``
        uses normal hearing (``0`` in every band).
    :return: An :class:`SIIResult` with the overall index and its ``.plot()``.
    :raises ValueError: if a spectrum has the wrong length or effort name.
    """
    if isinstance(speech_spectrum, str):
        e = standard_speech_spectrum(speech_spectrum)
    else:
        e = _as_band_vector(speech_spectrum, "speech_spectrum")
    n = (
        np.full(_N_BANDS, -80.0)
        if noise_spectrum is None
        else _as_band_vector(noise_spectrum, "noise_spectrum")
    )
    t = (
        np.zeros(_N_BANDS)
        if threshold is None
        else _as_band_vector(threshold, "threshold")
    )
    f = BAND_CENTRES

    # Clause 5.4 - self-speech masking and the upward spread of masking.
    v = e - 24.0
    b = np.maximum(n, v)
    c = -80.0 + 0.6 * (b + 10.0 * np.log10(f) - 6.353)
    z = np.empty(_N_BANDS)
    z[0] = b[0]
    for i in range(1, _N_BANDS):
        contrib = 10.0 ** (0.1 * (b[:i] + 3.32 * c[:i] * np.log10(0.89 * f[i] / f[:i])))
        z[i] = 10.0 * np.log10(10.0 ** (0.1 * n[i]) + np.sum(contrib))

    # Clause 5.5/5.6 - equivalent internal noise and disturbance.
    xp = REFERENCE_INTERNAL_NOISE + t
    d = 10.0 * np.log10(10.0 ** (0.1 * z) + 10.0 ** (0.1 * xp))

    # Clause 5.7/5.8 - level distortion, band audibility and the index.
    level_factor = np.clip(1.0 - (e - _SPEECH_NORMAL - 10.0) / 160.0, 0.0, 1.0)
    audibility = np.clip((e - d + 15.0) / 30.0, 0.0, 1.0)
    a = level_factor * audibility
    sii = float(np.sum(BAND_IMPORTANCE * a))

    return SIIResult(
        sii=sii,
        band_audibility=a,
        band_importance=BAND_IMPORTANCE.copy(),
        frequencies=f.copy(),
        speech_spectrum=e,
        disturbance=d,
        masking=z,
    )
