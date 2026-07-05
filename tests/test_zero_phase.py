#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for zero-phase (sosfiltfilt) filtering in OctaveFilterBank.
"""

import numpy as np
import pytest

from pyoctaveband import OctaveFilterBank

FS = 48000


def test_zero_phase_no_group_delay() -> None:
    """A pulse filtered zero-phase keeps its energy centered at the pulse time."""
    bank = OctaveFilterBank(fs=FS, fraction=1, limits=[800, 1200])
    x = np.zeros(FS)
    center = FS // 2
    x[center] = 1.0

    _, _, bands_zp = bank.filter(x, sigbands=True, zero_phase=True, calculate_level=False)
    yb = bands_zp[0]
    centroid = int(np.sum(np.arange(len(yb)) * yb**2) / np.sum(yb**2))
    assert abs(centroid - center) < FS // 1000  # within 1 ms


def test_zero_phase_doubles_attenuation() -> None:
    """filtfilt applies the filter twice: stopband attenuation doubles.

    Measured on the steady-state middle segment: the whole-signal RMS is
    dominated by the filter onset transient, which masks the difference.
    """
    bank = OctaveFilterBank(fs=FS, fraction=1, limits=[800, 1200])
    t = np.arange(FS) / FS
    x = np.sin(2 * np.pi * 4000 * t)  # far out of band

    _, _, bands_fwd = bank.filter(x, sigbands=True, calculate_level=False)
    _, _, bands_zp = bank.filter(x, sigbands=True, calculate_level=False, zero_phase=True)
    mid = slice(FS // 4, 3 * FS // 4)
    rms_fwd = np.sqrt(np.mean(bands_fwd[0][mid] ** 2))
    rms_zp = np.sqrt(np.mean(bands_zp[0][mid] ** 2))
    assert 20 * np.log10(rms_zp / rms_fwd) < -20


def test_zero_phase_rejects_stateful() -> None:
    bank = OctaveFilterBank(fs=FS, stateful=True, resample=False)
    with pytest.raises(ValueError, match="zero_phase"):
        bank.filter(np.zeros(FS), zero_phase=True)


def test_zero_phase_passband_level_matches() -> None:
    """In-band level must match forward filtering (0 dB passband both ways)."""
    bank = OctaveFilterBank(fs=FS, fraction=1, limits=[800, 1200])
    t = np.arange(FS * 2) / FS
    x = np.sin(2 * np.pi * 1000 * t)
    spl_fwd, _ = bank.filter(x)
    spl_zp, _ = bank.filter(x, zero_phase=True)
    assert spl_zp[0] == pytest.approx(spl_fwd[0], abs=0.1)
