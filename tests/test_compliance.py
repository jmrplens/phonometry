#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for the IEC 61260-1:2014 filter class verifier.
"""

import numpy as np
import pytest

from phonometry import OctaveFilterBank, verify_filter_class
from phonometry.compliance import class_limits


def test_class_limits_table1_anchor_values() -> None:
    """Spot-check the transcription against BS EN 61260-1:2014 Table 1 (b=1)."""
    G = 10 ** (3 / 10)
    # Passband center: class 1 in [-0.4, +0.4]
    lo, hi = class_limits(1.0, 1, np.array([1.0]))
    assert lo[0] == pytest.approx(-0.4) and hi[0] == pytest.approx(0.4)
    # Band edge (inside): max +5.3 (class 1)
    lo, hi = class_limits(1.0, 1, np.array([G ** 0.5 * 0.999999]))
    assert hi[0] == pytest.approx(5.3, abs=0.05)
    # Just outside the edge: minimum attenuation +1.2 (class 1)
    lo, hi = class_limits(1.0, 1, np.array([G ** 0.5 * 1.000001]))
    assert lo[0] == pytest.approx(1.2, abs=0.05)
    assert np.isinf(hi[0])
    # One octave out: minimum +16.6 (class 1) / +15.6 (class 2)
    lo1, _ = class_limits(1.0, 1, np.array([G]))
    lo2, _ = class_limits(1.0, 2, np.array([G]))
    assert lo1[0] == pytest.approx(16.6)
    assert lo2[0] == pytest.approx(15.6)
    # Far stopband: minimum +70 (class 1) / +60 (class 2)
    lo1, _ = class_limits(1.0, 1, np.array([G ** 5]))
    lo2, _ = class_limits(1.0, 2, np.array([G ** 5]))
    assert lo1[0] == pytest.approx(70.0)
    assert lo2[0] == pytest.approx(60.0)


def test_class_limits_low_side_is_reciprocal() -> None:
    """Formula (10): the low side mirrors the high side at 1/Omega."""
    omega = np.array([1.3, 2.0, 4.0])
    lo_h, hi_h = class_limits(3.0, 1, omega)
    lo_l, hi_l = class_limits(3.0, 1, 1.0 / omega)
    np.testing.assert_allclose(lo_l, lo_h)
    np.testing.assert_allclose(hi_l, hi_h, equal_nan=False)


def test_butter_order6_third_octave_meets_class1() -> None:
    bank = OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[100, 5000])
    result = verify_filter_class(bank)
    assert result["overall_class"] == 1, result


def test_butter_order6_octave_meets_class1() -> None:
    bank = OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[125, 4000])
    result = verify_filter_class(bank)
    assert result["overall_class"] == 1, result


def test_low_order_fails_class1() -> None:
    """A 1st-order bank cannot reach the class stopband attenuations."""
    bank = OctaveFilterBank(fs=48000, fraction=1, order=1, limits=[500, 2000])
    result = verify_filter_class(bank)
    assert result["overall_class"] is None


def test_result_has_per_band_details() -> None:
    bank = OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[500, 2000])
    result = verify_filter_class(bank)
    assert len(result["bands"]) == bank.num_bands
    for band in result["bands"]:
        assert set(band) >= {"freq", "class", "margin_class1_db", "margin_class2_db"}
    # margins must be finite floats
    assert all(np.isfinite(b["margin_class1_db"]) for b in result["bands"])


def test_stateful_bank_matches_stateless_design() -> None:
    """Stateful banks share the SOS design: verification must agree exactly."""
    stateful = OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[500, 2000],
                                stateful=True, resample=False)
    stateless = OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[500, 2000],
                                 resample=False)
    r_stateful = verify_filter_class(stateful)
    r_stateless = verify_filter_class(stateless)
    assert r_stateful["overall_class"] == r_stateless["overall_class"]
    for a, b in zip(r_stateful["bands"], r_stateless["bands"], strict=True):
        assert a["margin_class1_db"] == pytest.approx(b["margin_class1_db"])


def test_invalid_inputs_raise() -> None:
    bank = OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[500, 2000])
    with pytest.raises(ValueError, match="num_points"):
        verify_filter_class(bank, num_points=4)
    with pytest.raises(ValueError, match="filter_class"):
        class_limits(1.0, 3, np.array([1.0]))
    with pytest.raises(ValueError, match="fraction"):
        class_limits(-1.0, 1, np.array([1.0]))
