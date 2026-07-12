#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Aircraft noise certification: Effective Perceived Noise Level (ICAO Annex 16).

The EPNL is the noise-certification metric for transport-category aircraft. It
is built from a half-second spectral time history (24 one-third-octave bands,
50 Hz-10 kHz) in five steps, implementing **ICAO Annex 16 Vol. I, Appendix 2**
(the analytic formulation):

* :func:`perceived_noisiness` -- per-band perceived noisiness ``n`` (noys),
  the analytic piecewise noy law with the Table A2-3 constants.
* :func:`perceived_noise_level` -- ``PNL = 40 + (10/lg2)·lg N`` from the total
  noisiness ``N = 0.85·n_max + 0.15·Σn``.
* :func:`tone_correction` -- the tone-correction factor ``C`` (the slope /
  "encircling" method) that penalises spectral irregularities.
* :func:`effective_perceived_noise_level` -- the end-to-end metric: per-record
  ``PNLT = PNL + C``, the maximum ``PNLTM``, the 10 dB-down integration limits
  and the duration correction, giving ``EPNL = PNLTM + D``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import NDArray

#: The 24 one-third-octave band centre frequencies (Hz) used by PNL/EPNL.
NOY_BANDS: "NDArray[np.float64]" = np.array(
    [
        50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0, 250.0,
        315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0,
        2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0, 10000.0,
    ],
    dtype=np.float64,
)

_INF = np.inf
_NAN = np.nan
#: ICAO Annex 16 Vol. I Appendix 2 Table A2-3: analytic noy constants per band.
#: Columns: SPL(a), SPL(b), SPL(c), SPL(d), SPL(e), M(b), M(c), M(d), M(e).
_A2_3: "NDArray[np.float64]" = np.array(
    [
        [91.0, 64, 52, 49, 55, 0.043478, 0.030103, 0.079520, 0.058098],
        [85.9, 60, 51, 44, 51, 0.040570, 0.030103, 0.068160, 0.058098],
        [87.3, 56, 49, 39, 46, 0.036831, 0.030103, 0.068160, 0.052288],
        [79.0, 53, 47, 34, 42, 0.036831, 0.030103, 0.059640, 0.047534],
        [79.8, 51, 46, 30, 39, 0.035336, 0.030103, 0.053013, 0.043573],
        [76.0, 48, 45, 27, 36, 0.033333, 0.030103, 0.053013, 0.043573],
        [74.0, 46, 43, 24, 33, 0.033333, 0.030103, 0.053013, 0.040221],
        [74.9, 44, 42, 21, 30, 0.032051, 0.030103, 0.053013, 0.037349],
        [94.6, 42, 41, 18, 27, 0.030675, 0.030103, 0.053013, 0.034859],
        [_INF, 40, 40, 16, 25, 0.030103, _NAN, 0.053013, 0.034859],
        [_INF, 40, 40, 16, 25, 0.030103, _NAN, 0.053013, 0.034859],
        [_INF, 40, 40, 16, 25, 0.030103, _NAN, 0.053013, 0.034859],
        [_INF, 40, 40, 16, 25, 0.030103, _NAN, 0.053013, 0.034859],
        [_INF, 40, 40, 16, 25, 0.030103, _NAN, 0.053013, 0.034859],
        [_INF, 38, 38, 15, 23, 0.030103, _NAN, 0.059640, 0.034859],
        [_INF, 34, 34, 12, 21, 0.029960, _NAN, 0.053013, 0.040221],
        [_INF, 32, 32, 9, 18, 0.029960, _NAN, 0.053013, 0.037349],
        [_INF, 30, 30, 5, 15, 0.029960, _NAN, 0.047712, 0.034859],
        [_INF, 29, 29, 4, 14, 0.029960, _NAN, 0.047712, 0.034859],
        [_INF, 29, 29, 5, 14, 0.029960, _NAN, 0.053013, 0.034859],
        [_INF, 30, 30, 6, 15, 0.029960, _NAN, 0.053013, 0.034859],
        [_INF, 31, 31, 10, 17, 0.029960, 0.029960, 0.068160, 0.037349],
        [44.3, 37, 34, 17, 23, 0.042285, 0.029960, 0.079520, 0.037349],
        [50.7, 41, 37, 21, 29, 0.042285, 0.029960, 0.059640, 0.043573],
    ],
    dtype=np.float64,
)

#: Perceived-noise-level scale factor 10/log10(2).
_PNL_FACTOR = 10.0 / np.log10(2.0)


def _validate_spectrum(spl: "NDArray[np.float64] | list[float]") -> "NDArray[np.float64]":
    sig = np.asarray(spl, dtype=np.float64)
    if sig.shape != (24,):
        raise ValueError("'spl' must contain the 24 one-third-octave-band levels.")
    if not np.all(np.isfinite(sig)):
        raise ValueError("'spl' must be finite.")
    return sig


def perceived_noisiness(spl: "NDArray[np.float64] | list[float]") -> "NDArray[np.float64]":
    """Per-band perceived noisiness ``n`` in noys (ICAO Annex 16 App. 2 §4.7).

    The analytic piecewise noy law, using the Table A2-3 constants:

    * ``SPL ≥ SPL(a)``: ``n = 10^{M(c)·(SPL − SPL(c))}``
    * ``SPL(b) ≤ SPL < SPL(a)``: ``n = 10^{M(b)·(SPL − SPL(b))}``
    * ``SPL(e) ≤ SPL < SPL(b)``: ``n = 0.3·10^{M(e)·(SPL − SPL(e))}``
    * ``SPL(d) ≤ SPL < SPL(e)``: ``n = 0.1·10^{M(d)·(SPL − SPL(d))}``
    * ``SPL < SPL(d)``: ``n = 0`` (below the noy floor)

    :param spl: The 24 one-third-octave-band sound pressure levels, in dB.
    :return: The per-band perceived noisiness, in noys.
    :raises ValueError: If the spectrum is not 24 finite levels.
    """
    sig = _validate_spectrum(spl)
    spl_a, spl_b, spl_c, spl_d, spl_e = _A2_3[:, 0], _A2_3[:, 1], _A2_3[:, 2], _A2_3[:, 3], _A2_3[:, 4]
    m_b, m_c, m_d, m_e = _A2_3[:, 5], _A2_3[:, 6], _A2_3[:, 7], _A2_3[:, 8]

    # Guard the "not applicable" M(c) (NaN) so it never feeds a live branch:
    # branch (a) is only selected where SPL ≥ SPL(a), which never holds when
    # SPL(a) = inf, so replacing NaN with 0 here is inert.
    m_c_safe = np.where(np.isnan(m_c), 0.0, m_c)

    n_a = 10.0 ** (m_c_safe * (sig - spl_c))
    n_b = 10.0 ** (m_b * (sig - spl_b))
    n_e = 0.3 * 10.0 ** (m_e * (sig - spl_e))
    n_d = 0.1 * 10.0 ** (m_d * (sig - spl_d))

    conditions = [
        sig >= spl_a,
        sig >= spl_b,
        sig >= spl_e,
        sig >= spl_d,
    ]
    choices = [n_a, n_b, n_e, n_d]
    return np.asarray(np.select(conditions, choices, default=0.0), dtype=np.float64)


def perceived_noise_level(spl: "NDArray[np.float64] | list[float]") -> float:
    """Perceived noise level ``PNL`` (ICAO Annex 16 App. 2 §4.2), in PNdB.

    ``N = 0.85·n_max + 0.15·Σn`` and ``PNL = 40 + (10/lg2)·lg N``. If the total
    noisiness is not positive the PNL is defined as 0.

    :param spl: The 24 one-third-octave-band sound pressure levels, in dB.
    :return: The perceived noise level, in PNdB.
    :raises ValueError: If the spectrum is not 24 finite levels.
    """
    noys = perceived_noisiness(spl)
    total = float(0.85 * np.max(noys) + 0.15 * np.sum(noys))
    if total <= 0.0:
        return 0.0
    return float(40.0 + _PNL_FACTOR * np.log10(total))
