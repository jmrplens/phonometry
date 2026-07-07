#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Guards for the measurement methods used by generate_graphs.py.

The published weighting-curves figure once showed A/C ~2.4 dB low (never
crossing 0 dB) because the impulse sat at sample 0 and the high-accuracy
resampling path truncated the interpolation kernel at the array edge.
These tests call the ACTUAL graph measurement helper, so CI breaks if the
figures would ship distorted curves again.
"""

import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import generate_graphs  # noqa: E402

FS = 48000


def _analytic_a_db(f: np.ndarray) -> np.ndarray:
    """IEC 61672-1 analytic A-weighting curve."""
    f2 = np.asarray(f, dtype=float) ** 2
    ra = (12194**2 * f2**2) / (
        (f2 + 20.6**2)
        * np.sqrt((f2 + 107.7**2) * (f2 + 737.9**2))
        * (f2 + 12194**2)
    )
    return 20 * np.log10(ra) + 2.0


def _analytic_c_db(f: np.ndarray) -> np.ndarray:
    """IEC 61672-1 analytic C-weighting curve."""
    f2 = np.asarray(f, dtype=float) ** 2
    rc = (12194**2 * f2) / ((f2 + 20.6**2) * (f2 + 12194**2))
    return 20 * np.log10(rc) + 0.06


def test_graph_a_curve_matches_analytic() -> None:
    """The figure's A curve must match the IEC analytic curve, LF to HF."""
    freqs = np.array([16.0, 31.5, 100.0, 1000.0, 2500.0, 4000.0, 8000.0])
    _, mag = generate_graphs.measure_weighting_response(FS, "A", freqs)
    np.testing.assert_allclose(mag, _analytic_a_db(freqs), atol=0.3)


def test_graph_c_curve_matches_analytic() -> None:
    """The figure's C curve must match the IEC analytic curve, LF to HF."""
    freqs = np.array([16.0, 31.5, 100.0, 1000.0, 4000.0, 8000.0])
    _, mag = generate_graphs.measure_weighting_response(FS, "C", freqs)
    np.testing.assert_allclose(mag, _analytic_c_db(freqs), atol=0.3)


def test_graph_a_curve_shows_positive_bump() -> None:
    """
    The exact failure mode that shipped: an A curve that never crosses 0 dB.

    The A-weighting is positive between ~1.1 and ~6.2 kHz with a maximum of
    +1.27 dB at ~2.5 kHz (IEC 61672-1 Table 2). The plotted curve must show it.
    """
    w, mag = generate_graphs.measure_weighting_response(FS, "A")
    assert mag.max() == pytest.approx(1.27, abs=0.15), (
        f"A-curve max is {mag.max():+.2f} dB; the +1.27 dB bump is missing"
    )
    f_max = w[mag.argmax()]
    assert 2000 < f_max < 3200, f"A-curve peak at {f_max:.0f} Hz, expected ~2.5 kHz"


def test_graph_curves_anchor_at_1khz() -> None:
    """Both weightings are normalized to 0 dB at 1 kHz; the figure must agree."""
    for curve in ("A", "C"):
        _, mag = generate_graphs.measure_weighting_response(FS, curve, np.array([1000.0]))
        assert mag[0] == pytest.approx(0.0, abs=0.1), f"{curve} at 1 kHz: {mag[0]:+.2f} dB"
