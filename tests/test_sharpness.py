#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Sharpness (DIN 45692:2009-08) conformance tests.

Clause 6: the standard test signal is critical-band-wide narrowband noise
at 1 kHz (920-1080 Hz) with 60 dB overall level -> S = 1.00 acum, and every
other test signal carries the same loudness (4 sone). Targets from
Table A.2 (p. 11) with critical-band edges from Tabelle A.1 (p. 10);
permitted deviation 5 % or 0.05 acum.
"""

import numpy as np
import pytest
from scipy import signal as sp_signal

from phonometry import loudness_zwicker, sharpness_din, sharpness_din_from_specific
from phonometry.sharpness import reference_sound

FS = 48000

# DIN 45692 Tabelle A.1 critical-band edges for the Table A.2 subset used
# here: centre frequency -> (lower edge, upper edge) Hz, target acum.
A2_CASES = [
    (250.0, 200.0, 300.0, 0.38),
    (1000.0, 920.0, 1080.0, 1.00),
    (2500.0, 2320.0, 2700.0, 1.78),
    (4000.0, 3700.0, 4400.0, 2.82),
]


def _narrowband(f_lo: float, f_hi: float, level_db: float, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(FS * 2)
    sos = sp_signal.butter(8, [f_lo, f_hi], btype="band", fs=FS, output="sos")
    nb = sp_signal.sosfilt(sos, white)
    return np.asarray(nb / np.sqrt(np.mean(nb**2)) * 2e-5 * 10 ** (level_db / 20))


def _level_for_4_sone(f_lo: float, f_hi: float) -> float:
    lo, hi = 40.0, 85.0
    for _ in range(20):
        mid = (lo + hi) / 2
        n = loudness_zwicker(_narrowband(f_lo, f_hi, mid), FS, stationary=True).loudness
        if n < 4.0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def test_reference_signal_is_one_acum() -> None:
    """Clause 6: the standard test signal gives exactly 1.00 acum."""
    s = sharpness_din(reference_sound(), FS)
    assert s == pytest.approx(1.00, abs=1e-9)


def test_k_in_normative_range() -> None:
    """Clause 5.2: the normalization constant satisfies 0.105 <= k < 0.115."""
    from phonometry.sharpness import _k_din

    assert 0.105 <= _k_din() < 0.115


@pytest.mark.parametrize(("fc", "f_lo", "f_hi", "target"), A2_CASES)
def test_table_a2_targets(fc: float, f_lo: float, f_hi: float, target: float) -> None:
    """Table A.2 target sharpness for critical-band-wide noises at 4 sone,
    within the clause 6 tolerance (5 % or 0.05 acum)."""
    level = _level_for_4_sone(f_lo, f_hi)
    s = sharpness_din(_narrowband(f_lo, f_hi, level), FS)
    tol = max(0.05, 0.05 * target)
    assert abs(s - target) <= tol, f"{fc} Hz: S={s:.3f} vs {target} (tol {tol:.3f})"


def test_higher_frequency_is_sharper() -> None:
    lo = sharpness_din(_narrowband(400.0, 510.0, 60.0), FS)
    hi = sharpness_din(_narrowband(7700.0, 9500.0, 60.0), FS)
    assert hi > lo


def test_annex_b_variants() -> None:
    """The Aures and von Bismarck scales anchor the same 1 kHz
    critical-band reference at 1 acum (DIN 45692 Annex B); hold them to
    the clause 6 tolerance (0.05 acum) on the clause 6 reference sound."""
    spec = loudness_zwicker(reference_sound(), FS, stationary=True).specific
    for method in ("aures", "bismarck"):
        s = sharpness_din_from_specific(spec, method=method)
        assert abs(s - 1.0) < 0.05
    with pytest.raises(ValueError, match="method"):
        sharpness_din_from_specific(spec, method="zwicker")


def test_silence_is_zero() -> None:
    assert sharpness_din_from_specific(np.zeros(240)) == 0.0
