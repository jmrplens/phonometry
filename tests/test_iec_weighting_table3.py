#  Copyright (c) 2026. Jose M. Requena-Plens
"""
IEC 61672-1:2013 frequency weighting compliance (Table 3).

Nominal A/C/Z weightings and class 1 acceptance limits transcribed from the
official text: BS EN 61672-1:2013, **Table 3** ("Frequency weightings and
acceptance limits", standard page 22). Lower limits of ``-inf`` in the
standard are represented as ``-math.inf`` (only the upper limit applies).

The measured gain is the steady-state RMS ratio of a pure tone through the
real filter path (default ``high_accuracy``), at 48 kHz and 96 kHz.
"""

import math

import numpy as np
import pytest

from phonometry import WeightingFilter

INF = math.inf

# (nominal_freq_Hz, A_dB, C_dB, class1_upper_dB, class1_lower_dB)
# BS EN 61672-1:2013 Table 3 (Z weighting is 0.0 dB at every frequency).
TABLE3 = [
    (10, -70.4, -14.3, 3.0, -INF),
    (12.5, -63.4, -11.2, 2.5, -INF),
    (16, -56.7, -8.5, 2.0, -4.0),
    (20, -50.5, -6.2, 2.0, -2.0),
    (25, -44.7, -4.4, 2.0, -1.5),
    (31.5, -39.4, -3.0, 1.5, -1.5),
    (40, -34.6, -2.0, 1.0, -1.0),
    (50, -30.2, -1.3, 1.0, -1.0),
    (63, -26.2, -0.8, 1.0, -1.0),
    (80, -22.5, -0.5, 1.0, -1.0),
    (100, -19.1, -0.3, 1.0, -1.0),
    (125, -16.1, -0.2, 1.0, -1.0),
    (160, -13.4, -0.1, 1.0, -1.0),
    (200, -10.9, 0.0, 1.0, -1.0),
    (250, -8.6, 0.0, 1.0, -1.0),
    (315, -6.6, 0.0, 1.0, -1.0),
    (400, -4.8, 0.0, 1.0, -1.0),
    (500, -3.2, 0.0, 1.0, -1.0),
    (630, -1.9, 0.0, 1.0, -1.0),
    (800, -0.8, 0.0, 1.0, -1.0),
    (1000, 0.0, 0.0, 0.7, -0.7),
    (1250, 0.6, 0.0, 1.0, -1.0),
    (1600, 1.0, -0.1, 1.0, -1.0),
    (2000, 1.2, -0.2, 1.0, -1.0),
    (2500, 1.3, -0.3, 1.0, -1.0),
    (3150, 1.2, -0.5, 1.0, -1.0),
    (4000, 1.0, -0.8, 1.0, -1.0),
    (5000, 0.5, -1.3, 1.5, -1.5),
    (6300, -0.1, -2.0, 1.5, -2.0),
    (8000, -1.1, -3.0, 1.5, -2.5),
    (10000, -2.5, -4.4, 2.0, -3.0),
    (12500, -4.3, -6.2, 2.0, -5.0),
    (16000, -6.6, -8.5, 2.5, -16.0),
    (20000, -9.3, -11.2, 3.0, -INF),
]


def _measured_gain_db(wf: WeightingFilter, fs: int, f0: float) -> float:
    """Steady-state RMS gain of the weighting filter at a single frequency."""
    # Longer windows at low frequencies keep the partial-cycle RMS error tiny.
    duration = max(0.5, 12 / f0)
    t = np.arange(int(fs * duration)) / fs
    x = np.sin(2 * np.pi * f0 * t)
    y = wf.filter(x)
    n0 = int(0.2 * fs)  # skip the filter transient
    return float(20 * np.log10(np.std(y[n0:]) / np.std(x[n0:])))


@pytest.mark.parametrize("fs", [48000, 96000])
@pytest.mark.parametrize("curve,column", [("A", 1), ("C", 2)])
def test_weighting_within_class1_limits_table3(fs: int, curve: str, column: int) -> None:
    wf = WeightingFilter(fs, curve)
    failures = []
    for row in TABLE3:
        f0 = row[0]
        if f0 >= fs / 2:
            continue
        nominal, upper, lower = row[column], row[3], row[4]
        deviation = _measured_gain_db(wf, fs, f0) - nominal
        if not (lower <= deviation <= upper):
            failures.append(f"{f0} Hz: deviation {deviation:+.2f} dB (limits {upper:+}/{lower:+})")
    assert not failures, f"{curve} @ fs={fs}: " + "; ".join(failures)


def test_z_weighting_is_flat() -> None:
    """Z weighting is 0.0 dB at every Table 3 frequency (bypass)."""
    wf = WeightingFilter(48000, "Z")
    x = np.random.default_rng(0).standard_normal(4800)
    np.testing.assert_array_equal(wf.filter(x), x)
