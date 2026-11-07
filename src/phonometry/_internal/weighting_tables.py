#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The frequency weightings as their standards print and define them.

IEC 61672-1:2013 Table 3 (the A and C design goals and the class 1 and
class 2 limits at the 34 nominal frequencies), and the analytic design goals
of Annex E, with the B weighting of ANSI S1.4-1983 and the AU weighting of
IEC 61012:1990 beside them. The weighting-class verifier of
:mod:`phonometry.filters`, the aircraft noise of Doc 29 and the headphone
levels of EN 50332 all read this one transcription, so they cannot drift
apart.
"""

from __future__ import annotations

import numpy as np

from .validation import real_array

__all__ = ["WEIGHTING_TABLE3", "exact_base10"]

_INF = float("inf")

# BS EN 61672-1:2013 Table 3 (standard page 22): design-goal frequency
# weightings and class 1 / class 2 acceptance limits at the 34 nominal
# frequencies. Columns: (nominal Hz, A dB, C dB, class1 upper, class1 lower,
# class2 upper, class2 lower); Z is 0.0 dB at every frequency. A lower limit
# of -inf means only the upper limit applies.
WEIGHTING_TABLE3: tuple[tuple[float, float, float, float, float, float, float], ...] = (
    (10.0, -70.4, -14.3, 3.0, -_INF, 5.0, -_INF),
    (12.5, -63.4, -11.2, 2.5, -_INF, 5.0, -_INF),
    (16.0, -56.7, -8.5, 2.0, -4.0, 5.0, -_INF),
    (20.0, -50.5, -6.2, 2.0, -2.0, 3.0, -3.0),
    (25.0, -44.7, -4.4, 2.0, -1.5, 3.0, -3.0),
    (31.5, -39.4, -3.0, 1.5, -1.5, 3.0, -3.0),
    (40.0, -34.6, -2.0, 1.0, -1.0, 2.0, -2.0),
    (50.0, -30.2, -1.3, 1.0, -1.0, 2.0, -2.0),
    (63.0, -26.2, -0.8, 1.0, -1.0, 2.0, -2.0),
    (80.0, -22.5, -0.5, 1.0, -1.0, 2.0, -2.0),
    (100.0, -19.1, -0.3, 1.0, -1.0, 1.5, -1.5),
    (125.0, -16.1, -0.2, 1.0, -1.0, 1.5, -1.5),
    (160.0, -13.4, -0.1, 1.0, -1.0, 1.5, -1.5),
    (200.0, -10.9, 0.0, 1.0, -1.0, 1.5, -1.5),
    (250.0, -8.6, 0.0, 1.0, -1.0, 1.5, -1.5),
    (315.0, -6.6, 0.0, 1.0, -1.0, 1.5, -1.5),
    (400.0, -4.8, 0.0, 1.0, -1.0, 1.5, -1.5),
    (500.0, -3.2, 0.0, 1.0, -1.0, 1.5, -1.5),
    (630.0, -1.9, 0.0, 1.0, -1.0, 1.5, -1.5),
    (800.0, -0.8, 0.0, 1.0, -1.0, 1.5, -1.5),
    (1000.0, 0.0, 0.0, 0.7, -0.7, 1.0, -1.0),
    (1250.0, 0.6, 0.0, 1.0, -1.0, 1.5, -1.5),
    (1600.0, 1.0, -0.1, 1.0, -1.0, 2.0, -2.0),
    (2000.0, 1.2, -0.2, 1.0, -1.0, 2.0, -2.0),
    (2500.0, 1.3, -0.3, 1.0, -1.0, 2.5, -2.5),
    (3150.0, 1.2, -0.5, 1.0, -1.0, 2.5, -2.5),
    (4000.0, 1.0, -0.8, 1.0, -1.0, 3.0, -3.0),
    (5000.0, 0.5, -1.3, 1.5, -1.5, 3.5, -3.5),
    (6300.0, -0.1, -2.0, 1.5, -2.0, 4.5, -4.5),
    (8000.0, -1.1, -3.0, 1.5, -2.5, 5.0, -5.0),
    (10000.0, -2.5, -4.4, 2.0, -3.0, 5.0, -_INF),
    (12500.0, -4.3, -6.2, 2.0, -5.0, 5.0, -_INF),
    (16000.0, -6.6, -8.5, 2.5, -16.0, 5.0, -_INF),
    (20000.0, -9.3, -11.2, 3.0, -_INF, 5.0, -_INF),
)

# ANSI S1.4-1983 Appendix C: the B weighting is the C weighting with one
# extra zero at the origin and one extra real pole at f5 (Formula C2).
_F5 = 158.48932

# IEC 61012:1990 Table 2: pole locations of the U weighting (Hz).
_U_POLES_HZ = np.array(
    [
        -12200.0,
        -12200.0,
        -7850.0 + 8800.0j,
        -7850.0 - 8800.0j,
        -2900.0 + 12150.0j,
        -2900.0 - 12150.0j,
    ]
)

# IEC 61672-1:2013 Annex E pole frequencies of the analytic A/C design goals
# (E.4.1-E.4.8); identical to the constants the WeightingFilter design uses.
_F1 = 20.598997
_F2 = 107.65265
_F3 = 737.86223
_F4 = 12194.217


def exact_base10(frequencies: np.ndarray) -> np.ndarray:
    r"""Exact base-10 frequencies :math:`1000 \cdot 10^{n/10}`.

    IEC 61672-1:2013 Table 3 NOTE: the tabulated weightings are computed
    at the exact frequencies
    :math:`f = 1000 \cdot 10^{0.1 (n - 30)}`, not at the nominal
    labels (e.g. 15 848.9 Hz behind "16 kHz").
    """
    return np.asarray(
        10.0 ** (np.round(10.0 * np.log10(frequencies)) / 10.0), dtype=np.float64
    )


def _analytic_weighting_db(curve: str, frequencies: np.ndarray) -> np.ndarray:
    """Analytic design-goal weighting, re 1 kHz.

    For A/C(/Z) this evaluates the exact transfer-function magnitudes of IEC
    61672-1:2013 Annex E (E.4.1/E.4.2) at ``frequencies`` and normalizes to
    the 1 kHz value, reproducing every Table 3 design goal after 0.1 dB
    rounding. ``B`` adds the ANSI S1.4-1983 Appendix C Formula (C2) factor to
    the C response, and ``AU`` cascades the A response with the U low-pass
    built from the IEC 61012:1990 Table 2 poles (which reproduces every
    Table 1 nominal value within 0.05 dB).
    """
    f = real_array(frequencies, "frequencies")
    if curve == "Z":
        return np.zeros_like(f)

    def _c_gain(x: np.ndarray) -> np.ndarray:
        x2 = x**2
        return np.asarray(
            (_F4**2 * x2) / ((x2 + _F1**2) * (x2 + _F4**2)), dtype=np.float64
        )

    def _a_gain(x: np.ndarray) -> np.ndarray:
        x2 = x**2
        return np.asarray(
            _c_gain(x) * x2 / np.sqrt((x2 + _F2**2) * (x2 + _F3**2)),
            dtype=np.float64,
        )

    def _b_gain(x: np.ndarray) -> np.ndarray:
        # ANSI S1.4-1983 Formula (C2): W_B = 10 lg(K2 f^2/(f^2 + f5^2)) + W_C
        # (the constant K2 cancels in the 1 kHz normalization below).
        return np.asarray(_c_gain(x) * x / np.sqrt(x**2 + _F5**2), dtype=np.float64)

    def _u_gain(x: np.ndarray) -> np.ndarray:
        # Magnitude of the all-pole U weighting from the Table 2 pole
        # coordinates in Hz (the 2*pi scale cancels in the normalization).
        den = np.prod(1j * x[:, None] - _U_POLES_HZ[None, :], axis=1)
        return np.asarray(1.0 / np.abs(den), dtype=np.float64)

    def _au_gain(x: np.ndarray) -> np.ndarray:
        return np.asarray(_a_gain(x) * _u_gain(x), dtype=np.float64)

    gain = {"A": _a_gain, "B": _b_gain, "C": _c_gain, "AU": _au_gain}[curve]
    ref = gain(np.asarray([1000.0]))[0]
    return np.asarray(20.0 * np.log10(gain(f) / ref), dtype=np.float64)
